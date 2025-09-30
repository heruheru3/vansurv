"""
イベント処理を集約するモジュール
main.pyから肥大化したイベント処理ロジックを分離
"""

import pygame
import sys
from constants import *
from effects.particles import DeathParticle

class EventHandler:
    """ゲームのイベント処理を管理するクラス"""
    
    def __init__(self):
        self.virtual_to_screen_converter = None
        
    def set_coordinate_converter(self, converter_func):
        """マウス座標変換関数を設定"""
        self.virtual_to_screen_converter = converter_func
    
    def handle_window_events(self, event, is_fullscreen, windowed_size, display_info):
        """ウィンドウ関連のイベント処理"""
        if event.type == pygame.VIDEORESIZE:
            # リサイズイベントの処理
            return {'action': 'resize', 'size': event.size}
        return None
    
    def handle_keyboard_navigation(self, event, player, particles):
        """キーボードによるUI navigation処理"""
        if not hasattr(player, 'awaiting_weapon_choice') or not player.awaiting_weapon_choice:
            return None
            
        choices = getattr(player, 'last_level_choices', [])
        if not choices:
            return None
            
        n = len(choices)
        
        # 初期武器選択（グリッド形式）
        if getattr(player, 'is_initial_weapon_selection', False):
            return self._handle_grid_navigation(event, player, n, particles)
        else:
            # 通常のレベルアップ選択（横並び3択）
            return self._handle_linear_navigation(event, player, n, particles)
    
    def _handle_grid_navigation(self, event, player, n, particles):
        """3x3グリッド形式のナビゲーション"""
        grid_size = 3
        current_index = getattr(player, 'selected_weapon_choice_index', 0)
        row = current_index // grid_size
        col = current_index % grid_size
        new_index = current_index
        
        if event.key in (pygame.K_LEFT, pygame.K_a):
            col = (col - 1) % grid_size
            new_index = row * grid_size + col
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            col = (col + 1) % grid_size
            new_index = row * grid_size + col
        elif event.key in (pygame.K_UP, pygame.K_w):
            row = (row - 1) % grid_size
            new_index = row * grid_size + col
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            row = (row + 1) % grid_size
            new_index = row * grid_size + col
        elif pygame.K_1 <= event.key <= pygame.K_9:
            digit = event.key - pygame.K_1
            if digit < n:
                new_index = digit
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._confirm_selection(player, current_index, n, particles)
        
        if new_index != current_index and new_index < n:
            player.set_input_method("keyboard")
            player.selected_weapon_choice_index = new_index
            self._add_feedback_particle(player, particles)
        
        return {'action': 'navigate'}
    
    def _handle_linear_navigation(self, event, player, n, particles):
        """横並び3択のナビゲーション"""
        if event.key in (pygame.K_LEFT, pygame.K_a):
            player.set_input_method("keyboard")
            player.selected_weapon_choice_index = (player.selected_weapon_choice_index - 1) % n
            self._add_feedback_particle(player, particles)
            return {'action': 'navigate'}
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            player.set_input_method("keyboard")
            player.selected_weapon_choice_index = (player.selected_weapon_choice_index + 1) % n
            self._add_feedback_particle(player, particles)
            return {'action': 'navigate'}
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._confirm_selection(player, player.selected_weapon_choice_index, n, particles)
        
        return None
    
    def _confirm_selection(self, player, index, n, particles):
        """選択の確定処理"""
        player.set_input_method("keyboard")
        idx = max(0, min(index, n - 1))
        choice = player.last_level_choices[idx]
        player.apply_level_choice(choice)
        
        if getattr(player, 'is_initial_weapon_selection', False):
            player.is_initial_weapon_selection = False
        
        self._add_feedback_particles(player, particles, count=8)
        return {'action': 'confirm'}
    
    def handle_mouse_selection(self, event, player, particles, scale_factor, offset_x, offset_y):
        """マウスによる選択処理"""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        
        # マウス座標を仮想画面座標に変換
        mouse_x, mouse_y = event.pos
        virtual_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
        virtual_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
        virtual_x = max(0, min(SCREEN_WIDTH, virtual_x))
        virtual_y = max(0, min(SCREEN_HEIGHT, virtual_y))
        mx, my = int(virtual_x), int(virtual_y)
        
        # 武器選択
        if getattr(player, 'awaiting_weapon_choice', False):
            return self._handle_weapon_mouse_click(player, mx, my, particles)
        
        # サブアイテム選択
        if getattr(player, 'awaiting_subitem_choice', False):
            return self._handle_subitem_mouse_click(player, mx, my, particles)
        
        return None
    
    def _handle_weapon_mouse_click(self, player, mx, my, particles):
        """武器選択のマウスクリック処理"""
        player.set_input_method("mouse")
        choices = getattr(player, 'last_level_choices', [])
        
        if not choices:
            return None
        
        # 初期武器選択（グリッド形式）
        if getattr(player, 'is_initial_weapon_selection', False):
            grid_size = 3
            cw = min(880, SCREEN_WIDTH - 160)
            option_w = (cw - 40) // grid_size
            option_h = 142
            cell_margin = 8
            panel_w = cw
            panel_h = grid_size * (option_h + cell_margin) + 100
            
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            panel_y = max(20, cy - panel_h // 2)
            if panel_y + panel_h > SCREEN_HEIGHT - 20:
                panel_y = SCREEN_HEIGHT - panel_h - 20
            panel_rect = pygame.Rect(cx - panel_w // 2, panel_y, panel_w, panel_h)
            
            accent_h = 54
            
            for i, weapon_key in enumerate(choices[:9]):
                row = i // grid_size
                col = i % grid_size
                
                rect_x = panel_rect.x + 20 + col * option_w
                rect_y = panel_rect.y + accent_h + 12 + row * (option_h + cell_margin)
                rect = pygame.Rect(rect_x, rect_y, option_w - 8, option_h)
                
                if rect.collidepoint(mx, my):
                    choice = choices[i]
                    player.apply_level_choice(choice)
                    player.is_initial_weapon_selection = False
                    self._add_feedback_particles(player, particles, count=8)
                    return {'action': 'select_weapon', 'choice': choice}
        else:
            # 通常のレベルアップ選択
            cw = min(880, SCREEN_WIDTH - 160)
            ch = 180
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
            option_w = (cw - 40) // len(choices)
            option_h = ch - 60
            
            for i, choice in enumerate(choices):
                ox = panel_rect.x + 20 + i * option_w
                oy = panel_rect.y + 40
                rect = pygame.Rect(ox, oy, option_w - 8, option_h)
                
                if rect.collidepoint(mx, my):
                    player.apply_level_choice(choice)
                    self._add_feedback_particles(player, particles, count=8)
                    return {'action': 'select_weapon', 'choice': choice}
        
        return None
    
    def _handle_subitem_mouse_click(self, player, mx, my, particles):
        """サブアイテム選択のマウスクリック処理"""
        player.set_input_method("mouse")
        choices = getattr(player, 'last_subitem_choices', [])
        
        if not choices:
            return None
        
        cw = min(700, SCREEN_WIDTH - 200)
        ch = 180
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
        option_w = (cw - 40) // len(choices)
        option_h = ch - 60
        
        for i, key in enumerate(choices):
            ox = panel_rect.x + 20 + i * option_w
            oy = panel_rect.y + 48
            rect = pygame.Rect(ox, oy, option_w - 8, option_h)
            
            if rect.collidepoint(mx, my):
                player.apply_subitem_choice(key)
                self._add_feedback_particles(player, particles, count=8)
                return {'action': 'select_subitem', 'choice': key}
        
        return None
    
    def _add_feedback_particle(self, player, particles):
        """フィードバック用パーティクルを1つ追加"""
        try:
            particles.append(DeathParticle(player.x, player.y, CYAN))
        except Exception:
            pass
    
    def _add_feedback_particles(self, player, particles, count=8):
        """フィードバック用パーティクルを複数追加"""
        try:
            for _ in range(count):
                particles.append(DeathParticle(player.x, player.y, CYAN))
        except Exception:
            pass
