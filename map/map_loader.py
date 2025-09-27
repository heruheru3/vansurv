"""
CSVマップ読み込みシステム
80x45マスのマップデータを読み込み、描画する
"""

import pygame
import csv
import os
import sys
from constants import *
from utils.file_paths import get_resource_path

class MapLoader:
    def __init__(self):
        self.map_data = []
        self.tile_size = TEST_TILE_SIZE
        self.map_width = 0
        self.map_height = 0
        
        # タイル定義（数字 -> 色のマッピング）
        self.tile_colors = {
            0: MOREDARK_GRAY,    # 暗いグレー（デフォルト）
            1: DARK_GRAY,        # 濃いグレー
            2: GRAY,             # 通常グレー  
            3: LIGHT_GRAY,       # 薄いグレー
            4: (64, 32, 16),     # 茶色（土）
            5: (32, 64, 32),     # 濃い緑（森）
            6: (64, 64, 32),     # 黄土色（道）
            7: (32, 32, 64),     # 青系（水）
            8: (64, 16, 16),     # 赤系（危険地帯）
            9: (48, 48, 48),     # 中間グレー
        }
        
        # ブロッカータイル用の縁色定義（基本色より濃い同系色）
        self.border_colors = {
            5: (16, 32, 16),     # 森：より濃い緑
            7: (16, 16, 32),     # 水：より濃い青
            8: (32, 8, 8),       # 危険地帯：より濃い赤
            9: (24, 24, 24),     # 石/岩：より濃いグレー
        }
    
    def load_csv_map(self, csv_file_path):
        """CSVファイルからマップデータを読み込む"""
        try:
            # PyInstaller対応のリソースパスを取得
            full_path = get_resource_path(csv_file_path)
            
            if not os.path.exists(full_path):
                return False
            
            with open(full_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.map_data = []
                for row in reader:
                    # 各要素を整数に変換
                    int_row = []
                    for cell in row:
                        try:
                            int_row.append(int(cell.strip()))
                        except ValueError:
                            int_row.append(0)  # 変換できない場合は0
                    self.map_data.append(int_row)
            
            if self.map_data:
                self.map_height = len(self.map_data)
                self.map_width = len(self.map_data[0]) if self.map_data[0] else 0
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def generate_default_map(self):
        """デフォルトマップ（市松模様）を生成"""
        expected_width = WORLD_WIDTH // self.tile_size  # 80
        expected_height = WORLD_HEIGHT // self.tile_size  # 45
        
        self.map_data = []
        for y in range(expected_height):
            row = []
            for x in range(expected_width):
                # 市松模様パターン
                if (x + y) % 2 == 0:
                    row.append(1)  # DARK_GRAY
                else:
                    row.append(0)  # MOREDARK_GRAY
            self.map_data.append(row)
        
        self.map_width = expected_width
        self.map_height = expected_height
        print(f"[INFO] Generated default map: {self.map_width}x{self.map_height} tiles")
        return True
    
    def get_tile_at(self, world_x, world_y):
        """ワールド座標からタイル番号を取得"""
        tile_x = int(world_x // self.tile_size)
        tile_y = int(world_y // self.tile_size)
        
        if (0 <= tile_y < self.map_height and 
            0 <= tile_x < len(self.map_data[tile_y])):
            return self.map_data[tile_y][tile_x]
        else:
            return 0  # 範囲外はデフォルトタイル
    
    def draw_map(self, screen, camera_x, camera_y):
        """マップを描画"""
        if not self.map_data:
            return
        
        # 描画範囲を計算
        start_tile_x = max(0, int(camera_x // self.tile_size))
        end_tile_x = min(self.map_width, int((camera_x + SCREEN_WIDTH) // self.tile_size) + 1)
        start_tile_y = max(0, int(camera_y // self.tile_size))
        end_tile_y = min(self.map_height, int((camera_y + SCREEN_HEIGHT) // self.tile_size) + 1)
        
        # タイルを描画
        for tile_y in range(start_tile_y, end_tile_y):
            if tile_y >= len(self.map_data):
                continue
            row = self.map_data[tile_y]
            
            for tile_x in range(start_tile_x, end_tile_x):
                if tile_x >= len(row):
                    continue
                
                tile_id = row[tile_x]
                color = self.tile_colors.get(tile_id, self.tile_colors[0])
                
                # スクリーン座標を計算
                screen_x = tile_x * self.tile_size - camera_x
                screen_y = tile_y * self.tile_size - camera_y
                
                # タイルを描画
                pygame.draw.rect(screen, color, 
                               (screen_x, screen_y, self.tile_size, self.tile_size))
        
        # ブロッカータイルの縁を描画
        self._draw_blocker_borders(screen, camera_x, camera_y, start_tile_x, end_tile_x, start_tile_y, end_tile_y)
    
    def _draw_blocker_borders(self, screen, camera_x, camera_y, start_tile_x, end_tile_x, start_tile_y, end_tile_y):
        """ブロッカータイル（障害物）の縁を描画"""
        # ブロッカータイル: 5(森), 7(水), 8(危険地帯), 9(石/岩)
        blocker_tiles = {5, 7, 8, 9}
        
        # 画面内のブロッカータイルを収集
        screen_blockers = set()
        for tile_y in range(start_tile_y, end_tile_y):
            if tile_y >= len(self.map_data):
                continue
            row = self.map_data[tile_y]
            
            for tile_x in range(start_tile_x, end_tile_x):
                if tile_x >= len(row):
                    continue
                
                tile_id = row[tile_x]
                if tile_id in blocker_tiles:
                    screen_blockers.add((tile_x, tile_y))
        
        if screen_blockers:
            # 画面内のブロッカーエリアを検出して縁を描画
            visited = set()
            for tile_pos in screen_blockers:
                if tile_pos not in visited:
                    # このブロッカーから連続するエリアを検出
                    region = self._flood_fill_blocker_region(tile_pos[0], tile_pos[1], visited, blocker_tiles)
                    if region:
                        self._draw_blocker_region_border(screen, region, camera_x, camera_y)
    
    def _flood_fill_blocker_region(self, start_x, start_y, visited, blocker_tiles):
        """指定座標から連続するブロッカーエリアを検出"""
        if (start_x, start_y) in visited:
            return set()
        
        # 開始位置がブロッカータイルかチェック
        if (start_y >= len(self.map_data) or 
            start_x >= len(self.map_data[start_y]) or 
            self.map_data[start_y][start_x] not in blocker_tiles):
            return set()
            
        stack = [(start_x, start_y)]
        region = set()
        
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or (x, y) in region:
                continue
            
            # 境界チェック
            if (y < 0 or y >= len(self.map_data) or 
                x < 0 or x >= len(self.map_data[y])):
                continue
            
            # ブロッカータイルかチェック
            if self.map_data[y][x] not in blocker_tiles:
                continue
                
            region.add((x, y))
            visited.add((x, y))
            
            # 4方向の隣接タイルを探索
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    stack.append((nx, ny))
        
        return region
    
    def _draw_blocker_region_border(self, screen, region, camera_x, camera_y):
        """ブロッカーエリアの内側縁を描画"""
        if not region:
            return
            
        blocker_tiles = {5, 7, 8, 9}
        
        # このエリアの代表的なタイル種類を決定（最も多いタイル種類を使用）
        tile_type_count = {}
        for tile_x, tile_y in region:
            if (tile_y < len(self.map_data) and tile_x < len(self.map_data[tile_y])):
                tile_id = self.map_data[tile_y][tile_x]
                tile_type_count[tile_id] = tile_type_count.get(tile_id, 0) + 1
        
        # 最も多いタイル種類の縁色を使用
        dominant_tile_id = max(tile_type_count.keys()) if tile_type_count else 9
        border_color = self.border_colors.get(dominant_tile_id, (24, 24, 24))
        
        # 明るい色を作成（左と上の線用）
        def make_lighter_color(color, factor=1.5):
            return tuple(min(255, int(c * factor)) for c in color)
        
        # 暗い色を作成（凹効果用）
        def make_darker_color(color, factor=0.6):
            return tuple(int(c * factor) for c in color)
        
        # タイルIDに応じて明暗を決定
        # エリア5,9: 凸効果（上・左が明るい）
        # エリア7,8: 凹効果（上・左が暗い）
        if dominant_tile_id in [7, 8]:
            # 凹効果：上・左が暗い、下・右が明るい
            top_left_color = make_darker_color(border_color)
            bottom_right_color = make_lighter_color(border_color)
        else:
            # 凸効果：上・左が明るい、下・右が暗い（デフォルト）
            top_left_color = make_lighter_color(border_color)
            bottom_right_color = border_color
        
        border_thickness = BORDER_THICKNESS  # 縁の厚さ
        
        for tile_x, tile_y in region:
            # スクリーン座標でのタイル位置
            screen_x = tile_x * self.tile_size - camera_x
            screen_y = tile_y * self.tile_size - camera_y
            
            # 画面外の場合はスキップ
            if (screen_x < -self.tile_size or screen_x > SCREEN_WIDTH or 
                screen_y < -self.tile_size or screen_y > SCREEN_HEIGHT):
                continue
            
            # このタイルの4辺について、隣接タイルがこのエリア内にない辺に内側縁を描画
            directions = [
                (0, -1, 'top'),     # 上
                (0, 1, 'bottom'),   # 下
                (-1, 0, 'left'),    # 左
                (1, 0, 'right')     # 右
            ]
            
            # 境界辺を記録
            border_sides = []
            
            for dx, dy, side in directions:
                neighbor_x = tile_x + dx
                neighbor_y = tile_y + dy
                
                # 隣接タイルがこのエリア内にない場合、この辺は境界
                if (neighbor_x, neighbor_y) not in region:
                    border_sides.append(side)
            
            for side in border_sides:
                if side == 'top':
                    # 上辺の内側縁
                    pygame.draw.rect(screen, top_left_color, 
                                   (screen_x, screen_y, 
                                    self.tile_size, border_thickness))
                elif side == 'bottom':
                    # 下辺の内側縁
                    pygame.draw.rect(screen, bottom_right_color, 
                                   (screen_x, screen_y + self.tile_size - border_thickness, 
                                    self.tile_size, border_thickness))
                elif side == 'left':
                    # 左辺の内側縁
                    pygame.draw.rect(screen, top_left_color, 
                                   (screen_x, screen_y, 
                                    border_thickness, self.tile_size))
                elif side == 'right':
                    # 右辺の内側縁
                    pygame.draw.rect(screen, bottom_right_color, 
                                   (screen_x + self.tile_size - border_thickness, screen_y, 
                                    border_thickness, self.tile_size))
            
            # 角部分の処理：2つの境界辺が交わる角に矩形を描画
            corner_combinations = [
                (['top', 'left'], (screen_x, screen_y), top_left_color),  # 左上
                (['bottom', 'right'], (screen_x + self.tile_size - border_thickness, screen_y + self.tile_size - border_thickness), bottom_right_color)  # 右下
            ]
            
            for corner_sides, corner_pos, corner_color in corner_combinations:
                if all(side in border_sides for side in corner_sides):
                    # 角の矩形を描画
                    pygame.draw.rect(screen, corner_color, 
                                   (corner_pos[0], corner_pos[1], border_thickness, border_thickness))
            
            # 右上と左下の角は斜めカット処理
            if all(side in border_sides for side in ['top', 'right']):
                # 右上角：斜めカット
                corner_x = screen_x + self.tile_size - border_thickness
                corner_y = screen_y
                # 斜め分割：三角形で描画
                for i in range(border_thickness):
                    for j in range(border_thickness):
                        if i + j < border_thickness:
                            # 左上三角形部分（上辺の色）
                            pygame.draw.rect(screen, top_left_color, (corner_x + j, corner_y + i, 1, 1))
                        else:
                            # 右下三角形部分（右辺の色）
                            pygame.draw.rect(screen, bottom_right_color, (corner_x + j, corner_y + i, 1, 1))
            
            if all(side in border_sides for side in ['bottom', 'left']):
                # 左下角：斜めカット
                corner_x = screen_x
                corner_y = screen_y + self.tile_size - border_thickness
                # 斜め分割：三角形で描画
                for i in range(border_thickness):
                    for j in range(border_thickness):
                        if i + j >= border_thickness:
                            # 右下三角形部分（下辺の色）
                            pygame.draw.rect(screen, bottom_right_color, (corner_x + j, corner_y + i, 1, 1))
                        else:
                            # 左上三角形部分（左辺の色）
                            pygame.draw.rect(screen, top_left_color, (corner_x + j, corner_y + i, 1, 1))
    
    def create_sample_csv(self, output_path):
        """サンプルCSVファイルを作成"""
        expected_width = WORLD_WIDTH // self.tile_size  # 80
        expected_height = WORLD_HEIGHT // self.tile_size  # 45
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                for y in range(expected_height):
                    row = []
                    for x in range(expected_width):
                        # サンプルパターン：境界線、中央部、角にアクセント
                        if (x == 0 or x == expected_width-1 or 
                            y == 0 or y == expected_height-1):
                            row.append(8)  # 境界は赤系
                        elif (x % 10 == 0 or y % 10 == 0):
                            row.append(6)  # グリッド線は黄土色
                        elif (abs(x - expected_width//2) < 3 and 
                              abs(y - expected_height//2) < 3):
                            row.append(5)  # 中央は緑系
                        elif (x + y) % 2 == 0:
                            row.append(1)  # 市松模様
                        else:
                            row.append(0)
                    writer.writerow(row)
                    
            print(f"[INFO] Sample CSV created: {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to create sample CSV: {e}")
            return False
