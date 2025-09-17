import pygame
import sys
from constants import *
import json
import os
from systems.resources import get_font
from core.audio import audio
from utils.file_paths import get_resource_path

# 軽量キャッシュ: サーフェスを使い回す（フォントは resources.get_font に一本化）
_surf_cache = {}


def render_wrapped_jp(text, font, color, max_width, max_lines=None):
    """
    日本語を含むテキストの折り返し: 英単語は単語単位で、その他は文字単位で分割して幅に合わせる。
    戻り値はレンダリング済みサーフェスのリスト。
    """
    if not text:
        return []
    # まず英単語とその他の文字を混ぜてトークン化
    tokens = []
    cur = ''
    for ch in text:
        # ASCII の英数字と一部記号は単語を作る
        if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9'):
            cur += ch
        else:
            if cur:
                tokens.append(cur)
                cur = ''
            tokens.append(ch)
    if cur:
        tokens.append(cur)

    lines = []
    cur_line = ''
    for tok in tokens:
        trial = cur_line + tok
        try:
            w = font.size(trial)[0]
        except Exception:
            w = 0
        if w <= max_width:
            cur_line = trial
        else:
            if cur_line:
                lines.append(cur_line)
            # tok が単独で幅を超える場合は文字ごとに分割
            try:
                if font.size(tok)[0] > max_width:
                    # 詳細分割
                    for c in tok:
                        if not cur_line:
                            cur_line = c
                        else:
                            if font.size(cur_line + c)[0] <= max_width:
                                cur_line += c
                            else:
                                lines.append(cur_line)
                                cur_line = c
                else:
                    cur_line = tok
            except Exception:
                cur_line = tok
        if max_lines and len(lines) >= max_lines:
            break
    if cur_line and (not max_lines or len(lines) < max_lines):
        lines.append(cur_line)
    # レンダリング
    rendered = [font.render(l, True, color) for l in lines[:max_lines] if l]
    return rendered

def get_panel_surf(panel_w, panel_h, radius=8, alpha=160):
    key = f"panel_{panel_w}x{panel_h}_{radius}_{alpha}"
    s = _surf_cache.get(key)
    if s is None:
        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, alpha), (0, 0, panel_w, panel_h), border_radius=radius)
        # convert_alpha() を呼べるなら呼んでおく（表示フォーマットに合わせて最適化）
        try:
            s = s.convert_alpha()
        except Exception:
            pass
        _surf_cache[key] = s
    return s

def get_result_surf(table_w, table_h, alpha=128):
    key = f"result_{table_w}x{table_h}_{alpha}"
    s = _surf_cache.get(key)
    if s is None:
        s = pygame.Surface((table_w, table_h), pygame.SRCALPHA)
        s.fill((255, 255, 255, alpha))
        try:
            pygame.draw.rect(s, BLACK, (0, 0, table_w, table_h), 3)
        except Exception:
            pass
        try:
            s = s.convert_alpha()
        except Exception:
            pass
        _surf_cache[key] = s
    return s

def get_minimap_surf(map_w, map_h, alpha=128, bg=(20,20,20)):
    key = f"minimap_{map_w}x{map_h}_{alpha}"
    s = _surf_cache.get(key)
    if s is None:
        s = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        s.fill((bg[0], bg[1], bg[2], alpha))
        try:
            s = s.convert_alpha()
        except Exception:
            pass
        _surf_cache[key] = s
    return s

def draw_ui(screen, player, game_time, game_over, game_clear, damage_stats=None, icons=None, show_status=True, money=0, game_money=0, enemy_kill_stats=None, boss_kill_stats=None, force_ended=False, save_system=None):
    # メイン画面のフォントをやや小さく（約70%）にする
    font = get_font(18)
    
    # HP/EXPをメーターバー形式で表示（画面上部にまとめて表示）
    meter_w = 300
    meter_h = 24
    pad = 12
    panel_w = meter_w + pad * 2
    panel_h = meter_h * 2 + pad * 3  # 元の2バー分に戻す
    # パネル背景（半透明）
    panel_surf = get_panel_surf(panel_w, panel_h, radius=8, alpha=160)
    screen.blit(panel_surf, (8, 8))

    bar_x = 8 + pad
    bar_y = 8 + pad
    # HPバー背景
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, meter_w, meter_h), border_radius=6)
    try:
        max_hp = max(1, int(player.get_max_hp()))
    except Exception:
        max_hp = 100
    hp_ratio = max(0.0, min(1.0, float(getattr(player, 'hp', 0)) / float(max_hp)))
    pygame.draw.rect(screen, RED, (bar_x, bar_y, int(meter_w * hp_ratio), meter_h), border_radius=6)
    # HPテキスト
    hp_text = font.render(f"HP {int(getattr(player,'hp',0))}/{max_hp}", True, WHITE)
    hp_rect = hp_text.get_rect(midleft=(bar_x + 8, bar_y + meter_h // 2))
    screen.blit(hp_text, hp_rect.topleft)

    # EXPバー
    exp_y = bar_y + meter_h + pad
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, exp_y, meter_w, meter_h), border_radius=6)
    exp_to = max(1, getattr(player, 'exp_to_next_level', 1))
    exp_ratio = max(0.0, min(1.0, getattr(player, 'exp', 0) / exp_to))
    pygame.draw.rect(screen, (40, 200, 250), (bar_x, exp_y, int(meter_w * exp_ratio), meter_h), border_radius=6)
    exp_text = font.render(f"LV{getattr(player,'level',1)} EXP {getattr(player,'exp',0)}/{exp_to}", True, WHITE)
    exp_rect = exp_text.get_rect(midleft=(bar_x + 8, exp_y + meter_h // 2))
    screen.blit(exp_text, exp_rect.topleft)

    # 獲得金額をHPパネルの右側に表示（パネルの外側）
    panel_right = 8 + panel_w  # パネルの右端
    money_text = font.render(f"Money: {game_money}G", True, YELLOW)
    money_x = panel_right + 20  # パネルから20px右
    money_y = 8 + pad + meter_h // 2  # HPバーと同じ高さ
    money_rect = money_text.get_rect(midleft=(money_x, money_y))
    screen.blit(money_text, money_rect.topleft)

    # 難易度表示（画面右上、ミニマップの左側）
    if save_system:
        try:
            from constants import DIFFICULTY_NAMES
            current_difficulty = save_system.get_difficulty()
            difficulty_name = DIFFICULTY_NAMES.get(current_difficulty, "不明")
            difficulty_font = get_font(16)  # 小さめのフォント
            difficulty_text = difficulty_font.render(f"難易度: {difficulty_name}", True, WHITE)
            
            # ミニマップの位置を参考にして、その左側に配置
            # ミニマップは右上 margin=10 で配置される
            minimap_w = 220  # draw_minimapと同じ値
            difficulty_x = SCREEN_WIDTH - minimap_w - 10 - difficulty_text.get_width() - 20  # ミニマップの左20px
            difficulty_y = 15  # 上端から15px
            
            # 背景パネル（小さめ、半透明）
            diff_bg_w = difficulty_text.get_width() + 12
            diff_bg_h = difficulty_text.get_height() + 8
            diff_panel = get_panel_surf(diff_bg_w, diff_bg_h, radius=4, alpha=140)
            screen.blit(diff_panel, (difficulty_x - 6, difficulty_y - 4))
            
            screen.blit(difficulty_text, (difficulty_x, difficulty_y))
        except Exception:
            pass  # エラーが発生した場合は表示しない

    # # 時間表示
    # time_text = font.render(f"Time: {int(game_time)}s", True, WHITE)
    # screen.blit(time_text, (16, 76))

    # ゲームクリア/オーバー表示を修正
    if game_clear:
        # タイトル／時間のみ表示（レザルト表は共通処理で表示）
        big_font = get_font(34)
        final_time_font = get_font(20)

        if damage_stats:
            # リザルト表の開始位置を共通処理と合わせる
            table_h = 280  # 共通処理と同じ高さ
            table_y = max(10, (SCREEN_HEIGHT - table_h) // 2 - 80)  # 共通処理と同じ位置計算（上に移動）
            title_y = 40  # 上部に20pxの余裕を確保
            time_y = title_y + 40  # タイトルの下に配置
        else:
            title_y = 40  # 上部に20pxの余裕を確保
            time_y = 60   # タイトルの下に配置

        clear_surf = big_font.render("GAME CLEAR!", True, GREEN)
        clear_rect = clear_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(clear_surf, clear_rect)

        final_time = final_time_font.render(f"Survival Time: {int(game_time)}s", True, GREEN)
        final_time_rect = final_time.get_rect(center=(SCREEN_WIDTH // 2, time_y))
        screen.blit(final_time, final_time_rect)

    elif game_over:
        # タイトル／時間／再開テキストを、リザルト表と重ならないように配置
        big_font = get_font(34)
        final_time_font = get_font(20)
        restart_font = get_font(14)

        if damage_stats:
            table_h = 280  # 共通処理と同じ高さに統一
            table_y = max(10, (SCREEN_HEIGHT - table_h) // 2 - 80)  # 共通処理と同じ位置計算（上に移動）
            title_y = 20  # 上部に20pxの余裕を確保
            time_y = title_y + 40  # タイトルの下に配置
            restart_y = time_y + 30  # 時間の下に配置
        else:
            title_y = 40  # 上部に20pxの余裕を確保
            time_y = title_y + 40   # タイトルの下に配置
            restart_y = 100 # 時間の下に配置

        if force_ended:
            # ESCキーによる強制終了の場合は途中経過画面として表示
            over_surf = big_font.render("GAME PAUSED", True, YELLOW)
        else:
            # 通常のゲームオーバー
            over_surf = big_font.render("GAME OVER", True, RED)
        over_rect = over_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(over_surf, over_rect)

        if force_ended:
            final_time = final_time_font.render(f"Current Time: {int(game_time)}s", True, YELLOW)
        else:
            final_time = final_time_font.render(f"Survival Time: {int(game_time)}s", True, RED)
        final_time_rect = final_time.get_rect(center=(SCREEN_WIDTH // 2, time_y))
        screen.blit(final_time, final_time_rect)

        # if force_ended:
        #     restart_text = restart_font.render("Press ENTER to continue or restart", True, YELLOW)
        # else:
        #     restart_text = restart_font.render("Press ENTER to restart", True, RED)
        # restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, restart_y))
        # screen.blit(restart_text, restart_rect)

    # 結果パネル: ゲーム終了時に武器統計を常に表示（GAME CLEAR / GAME OVER 共通）
    try:
        if game_over or game_clear:
            table_w = min(880, SCREEN_WIDTH - 80)
            table_h = 250  # さらに縮小（280から250に、30px短縮）
            table_x = (SCREEN_WIDTH - table_w) // 2
            table_y = 110  # 全体的に20px下げる（90→110に調整）

            result_surf = get_result_surf(table_w, table_h, alpha=128)
            screen.blit(result_surf, (table_x, table_y))

            header_font = get_font(20)
            row_font = get_font(16)
            screen.blit(header_font.render("Weapon", True, BLACK), (table_x + 24, table_y + 8))
            screen.blit(header_font.render("Total Damage", True, BLACK), (table_x + 280, table_y + 8))
            screen.blit(header_font.render("DPS", True, BLACK), (table_x + 560, table_y + 8))

            total_time = max(1.0, game_time)
            
            # damage_statsがない場合は空の辞書として扱う
            stats_to_show = damage_stats if damage_stats else {}
            items = sorted(stats_to_show.items(), key=lambda kv: kv[1], reverse=True)
            row_y = table_y + 50  # ヘッダーとの間隔を短縮（56から50に）
            row_height = 30  # 行間をさらに短縮（36から30に）
            
            for wname, dmg in items:
                dps = dmg / total_time
                screen.blit(row_font.render(str(wname), True, BLACK), (table_x + 24, row_y))
                screen.blit(row_font.render(str(int(dmg)), True, BLACK), (table_x + 320, row_y))
                screen.blit(row_font.render(f"{dps:.1f}", True, BLACK), (table_x + 580, row_y))
                row_y += row_height
                if row_y + row_height > table_y + table_h - 40:  # Totalエリア確保マージンを短縮（50から40に）
                    break

            total_dmg = sum(stats_to_show.values()) if stats_to_show else 0
            row_y = table_y + table_h - 25  # マージンをさらに短縮（30から25に）
            screen.blit(row_font.render("Total", True, BLACK), (table_x + 24, row_y))
            screen.blit(row_font.render(str(int(total_dmg)), True, BLACK), (table_x + 320, row_y))
            screen.blit(row_font.render(f"{(total_dmg/total_time):.1f}", True, BLACK), (table_x + 580, row_y))
    except Exception:
        pass

    # エネミー撃破統計の表示（レザルト画面のみ、撃破数0でも枠を表示）
    try:
        if (game_over or game_clear) and enemy_kill_stats is not None:
            # 武器統計テーブルの下に配置（武器統計は常に表示される）
            weapon_table_w = min(880, SCREEN_WIDTH - 80)
            weapon_table_h = 250  # 武器統計と同じ高さ
            weapon_table_x = (SCREEN_WIDTH - weapon_table_w) // 2
            weapon_table_y = 110  # 武器統計と同じ位置計算（20px下げる）
            
            # 武器統計テーブルの下に10px間隔で配置
            enemy_table_start_y = weapon_table_y + weapon_table_h + 10
            
            # エネミー撃破統計パネルの設定
            enemy_table_w = min(560, SCREEN_WIDTH - 80)  # 武器統計より小さく
            enemy_table_h = 130  # さらに縮小（140から130に）
            enemy_table_x = (SCREEN_WIDTH - enemy_table_w) // 2
            enemy_table_y = enemy_table_start_y
            
            # ボタンとの重複チェック（ボタンが最下部にあるので大丈夫だが念のため）
            button_y = SCREEN_HEIGHT - 48 - 20  # ボタンの位置
            if enemy_table_y + enemy_table_h > button_y - 20:
                # もし重複するなら、エネミー統計テーブルをさらに上に移動
                enemy_table_y = button_y - enemy_table_h - 20

            enemy_result_surf = get_result_surf(enemy_table_w, enemy_table_h, alpha=128)
            screen.blit(enemy_result_surf, (enemy_table_x, enemy_table_y))

            # タイトル
            header_font = get_font(16)
            screen.blit(header_font.render("Enemies Defeated", True, BLACK), (enemy_table_x + 20, enemy_table_y + 8))

            # エネミー撃破数をアイコンと数字で表示（10個×2段）
            draw_enemy_kill_stats(screen, enemy_kill_stats, enemy_table_x + 20, enemy_table_y + 35, enemy_table_w - 40, 90)
    except Exception:
        pass

    # ボス撃破統計の表示（レザルト画面のみ、撃破数0でも枠を表示）
    try:
        if (game_over or game_clear) and boss_kill_stats is not None:
            # ボス統計テーブルの配置
            boss_table_w = 700
            boss_table_h = 110  # さらに縮小（100から90に）
            boss_table_x = (SCREEN_WIDTH - boss_table_w) // 2
            boss_table_y = enemy_table_y + enemy_table_h + 10  # エネミー統計の下（15pxから10pxに短縮）
            
            # 背景
            boss_result_surf = get_result_surf(boss_table_w, boss_table_h, alpha=128)
            screen.blit(boss_result_surf, (boss_table_x, boss_table_y))

            # タイトル
            header_font = get_font(16)
            screen.blit(header_font.render("Boss Defeated", True, BLACK), (boss_table_x + 20, boss_table_y + 8))

            # ボス撃破状況をアイコンとチェックマークで表示
            draw_boss_kill_stats(screen, boss_kill_stats, boss_table_x + 20, boss_table_y + 35, boss_table_w - 40, 60)
    except Exception:
        pass

    # 残り時間の表示
    if not game_over and not game_clear:
        remaining_time = SURVIVAL_TIME - game_time
        remaining_text = font.render(f"Remaining: {int(remaining_time)}s", True, 
                                   YELLOW if remaining_time <= 30 else WHITE)
        screen.blit(remaining_text, (600, 10))

    # 武器情報の表示
    # 横並びで表示（アイコンの下にレベル数のみを表示）
    start_x = 10
    start_y = 100
    # 画面上の表示サイズを2倍に変更（16pxアセットを2倍表示して32pxに）
    icon_display_size = 32
    gap = 12
    small_font = get_font(12)
    try:
        for i, (weapon_name, weapon) in enumerate(player.weapons.items()):
            x = start_x + i * (icon_display_size + gap)
            y = start_y
            try:
                icon_surf = None
                if icons and isinstance(icons, dict):
                    icon_surf = icons.get(weapon_name)
                if icon_surf:
                    try:
                        # ピクセルアートをシャープに拡大するため nearest-neighbor の pygame.transform.scale を使う
                        icon_draw = pygame.transform.scale(icon_surf, (icon_display_size, icon_display_size))
                    except Exception:
                        icon_draw = icon_surf
                    screen.blit(icon_draw, (x, y))
                else:
                    pygame.draw.rect(screen, (120,120,120), (x, y, icon_display_size, icon_display_size))

                # レベル表示（上限到達なら MAX バッジを表示）
                try:
                    level_val = int(getattr(weapon, 'level', 1))
                except Exception:
                    level_val = int(getattr(weapon, 'level', 1) if hasattr(weapon, 'level') else 1)
                if level_val >= MAX_WEAPON_LEVEL:
                    try:
                        badge_text = 'MAX'
                        b_surf = small_font.render(badge_text, True, WHITE)
                        bw = b_surf.get_width() + 8
                        bh = b_surf.get_height() + 4
                        bx = x + (icon_display_size - bw) // 2
                        by = y + icon_display_size + 4
                        pygame.draw.rect(screen, (200,60,60), (bx, by, bw, bh), border_radius=4)
                        screen.blit(b_surf, (bx + (bw - b_surf.get_width())//2, by + (bh - b_surf.get_height())//2))
                    except Exception:
                        screen.blit(small_font.render('MAX', True, WHITE), (x, y + icon_display_size + 4))
                else:
                    lvl_text = small_font.render(str(level_val), True, WHITE)
                    tx = x + (icon_display_size - lvl_text.get_width()) // 2
                    ty = y + icon_display_size + 4
                    screen.blit(lvl_text, (tx, ty))
            except Exception:
                # 個別描画エラーは無視して次の武器へ
                continue
    except Exception:
        pass

    # --- 所持サブアイテムを武器表示と同じスタイルのアイコン並びに統一 ---
    try:
        sub_start_x = start_x
        sub_start_y = start_y + icon_display_size + 40  # 武器表示の下に余白を取って表示
        sub_icon_size = icon_display_size  # 武器と同じサイズに統一
        sub_gap = gap
        # 小フォントは武器表示と同じ small_font を流用
        sub_items = list(getattr(player, 'subitems', {}).items())
        if sub_items:
            max_per_row = max(1, (SCREEN_WIDTH - sub_start_x - 20) // (sub_icon_size + sub_gap))
            for idx, (key, inst) in enumerate(sub_items):
                row = idx // max_per_row
                col = idx % max_per_row
                x = sub_start_x + col * (sub_icon_size + sub_gap)
                y = sub_start_y + row * (sub_icon_size + 36)

                # アイコン表示（武器と同じnearest-neighbor拡大を試みる）
                icon_surf = None
                try:
                    if icons and isinstance(icons, dict):
                        icon_surf = icons.get(key)
                except Exception:
                    icon_surf = None

                if icon_surf:
                    try:
                        icon_draw = pygame.transform.scale(icon_surf, (sub_icon_size, sub_icon_size))
                        screen.blit(icon_draw, (x, y))
                    except Exception:
                        pygame.draw.rect(screen, (120,200,140), (x, y, sub_icon_size, sub_icon_size))
                else:
                    pygame.draw.rect(screen, (120,200,140), (x, y, sub_icon_size, sub_icon_size))

                # レベル表示は武器と同様に数値のみをアイコンの下にセンタリングして表示
                try:
                    lvl_val = int(getattr(inst, 'level', 1))
                except Exception:
                    lvl_val = int(getattr(inst, 'level', 1) if hasattr(inst, 'level') else 1)
                try:
                    if lvl_val >= MAX_SUBITEM_LEVEL:
                        badge_text = 'MAX'
                        b_surf = small_font.render(badge_text, True, WHITE)
                        bw = b_surf.get_width() + 8
                        bh = b_surf.get_height() + 4
                        bx = x + (sub_icon_size - bw) // 2
                        by = y + sub_icon_size + 4
                        pygame.draw.rect(screen, (200,60,60), (bx, by, bw, bh), border_radius=4)
                        screen.blit(b_surf, (bx + (bw - b_surf.get_width())//2, by + (bh - b_surf.get_height())//2))
                    else:
                        lvl_text = small_font.render(str(lvl_val), True, WHITE)
                        tx = x + (sub_icon_size - lvl_text.get_width()) // 2
                        ty = y + sub_icon_size + 4
                        screen.blit(lvl_text, (tx, ty))
                except Exception:
                    pass
    except Exception:
        pass

    # 右下に小さなプレイヤーステータス表示（ON/OFF）
    try:
        if show_status:
            s_font = get_font(14)
            # 値を安全に取得
            try:
                lvl = getattr(player, 'level', 1)
            except Exception:
                lvl = 1
            try:
                cur_hp = int(getattr(player, 'hp', 0))
            except Exception:
                cur_hp = 0
            try:
                max_hp = int(player.get_max_hp())
            except Exception:
                max_hp = getattr(player, 'max_hp', 100)
            try:
                sp = float(player.get_speed())
            except Exception:
                sp = float(getattr(player, 'base_speed', 3))
            try:
                bd = float(player.get_base_damage_bonus())
            except Exception:
                bd = 0.0
            try:
                df = float(player.get_defense())
            except Exception:
                df = 0.0
            try:
                range_mult = float(player.get_effect_range_multiplier())
            except Exception:
                range_mult = 1.0
            try:
                time_mult = float(player.get_effect_time_multiplier())
            except Exception:
                time_mult = 1.0
            try:
                extra_proj = int(player.get_extra_projectiles())
            except Exception:
                extra_proj = 0

            # 表示行を組み立て
            lines = [
                f"LV {lvl}",
                f"HP {cur_hp}/{max_hp}",
                f"Speed {sp:.1f}",
                f"Damage+ {bd:+.1f}",
                f"Defense {df:.1f}",
                f"Range {((range_mult-1.0)*100):+.0f}%",  # +8%
                f"Duration {((time_mult-1.0)*100):+.0f}%",  # +8%
                f"ExtraProj {extra_proj}",
                f"Weapons {len(getattr(player, 'weapons', {}))}",
            ]

            # パネル作成（幅は固定だがテキスト長に応じて余裕を持たせる）
            pad = 8
            w = 220
            h = 18 * len(lines) + pad * 2
            x = SCREEN_WIDTH - w - 12
            y = SCREEN_HEIGHT - h - 12
            panel = get_panel_surf(w, h, radius=8, alpha=180)
            screen.blit(panel, (x, y))
            for i, ln in enumerate(lines):
                try:
                    txt = s_font.render(ln, True, WHITE)
                    screen.blit(txt, (x + pad, y + pad + i * 18))
                except Exception:
                    continue
    except Exception:
        pass

# --- ミニマップ機能を追加 ---
def draw_minimap(screen, player, enemies, gems, items, camera_x=0, camera_y=0):
    """右上にミニマップを描画する。プレイヤー・敵・ジェム・アイテム、カメラ範囲を表示する。
    """
    # ミニマップの最大サイズ
    max_w = 220
    max_h = 140
    margin = 10

    # スケールをワールドサイズに合わせて計算
    scale_x = max_w / float(max(1, WORLD_WIDTH))
    scale_y = max_h / float(max(1, WORLD_HEIGHT))
    scale = min(scale_x, scale_y)
    if scale <= 0:
        return

    map_w = int(WORLD_WIDTH * scale)
    map_h = int(WORLD_HEIGHT * scale)
    # 右上に配置
    map_x = SCREEN_WIDTH - map_w - margin
    map_y = margin

    # 背景パネル（半透明）とマップ本体をキャッシュして再利用
    panel_surf = get_panel_surf(map_w + 6, map_h + 6, radius=0, alpha=180)
    # (panel_surf は黒ベースなのでブリット位置を微調整)
    screen.blit(panel_surf, (map_x - 3, map_y - 3))
    map_surf = get_minimap_surf(map_w, map_h, alpha=128)
    screen.blit(map_surf, (map_x, map_y))
    pygame.draw.rect(screen, WHITE, (map_x, map_y, map_w, map_h), 2)

    def world_to_map(wx, wy):
        mx = map_x + int(wx * scale)
        my = map_y + int(wy * scale)
        return mx, my

    # 敵を点で描画（赤）
    for e in enemies:
        try:
            ex, ey = world_to_map(e.x, e.y)
            if hasattr(e, 'is_boss') and e.is_boss:
                pygame.draw.rect(screen, PINK, (ex, ey, 4, 4))  # ボスは大きめ&ピンク
            else:
                pygame.draw.rect(screen, (200, 60, 60), (ex, ey, 3, 3))
        except Exception:
            pass

    # 経験値ジェム（シアン）
    for g in gems:
        try:
            gx, gy = world_to_map(g.x, g.y)
            pygame.draw.rect(screen, CYAN, (gx, gy, 3, 3))
        except Exception:
            pass

    # アイテム（黄色）"
    for it in items:
        try:
            ix, iy = world_to_map(it.x, it.y)
            pygame.draw.rect(screen, YELLOW, (ix, iy, 3, 3))
        except Exception:
            pass

    # プレイヤー（緑）を大きめの円で描画
    try:
        px, py = world_to_map(player.x, player.y)
        pygame.draw.circle(screen, GREEN, (px, py), 5)
        pygame.draw.circle(screen, BLACK, (px, py), 6, 1)
    except Exception:
        pass

    # カメラの表示領域を矩形で描画（白の半透明枠）
    try:
        vx = int(camera_x * scale)
        vy = int(camera_y * scale)
        vw = max(1, int(SCREEN_WIDTH * scale))
        vh = max(1, int(SCREEN_HEIGHT * scale))
        cam_rect = pygame.Rect(map_x + vx, map_y + vy, vw, vh)
        # 半透明の塗りで視認性を上げる
        s = pygame.Surface((cam_rect.width, cam_rect.height), pygame.SRCALPHA)
        s.fill((255, 255, 255, 32))
        screen.blit(s, (cam_rect.x, cam_rect.y))
        pygame.draw.rect(screen, WHITE, cam_rect, 1)
    except Exception:
        pass

    # 小さな凡例を追加
    try:
        legend_x = map_x
        legend_y = map_y + map_h + 6
        font = get_font(14)
        screen.blit(font.render('P: Player', True, WHITE), (legend_x, legend_y))
        screen.blit(font.render('E: Enemy', True, (200,60,60)), (legend_x + 80, legend_y))
    except Exception:
        pass

def draw_background(screen, camera_x=0, camera_y=0):
    """暗めのグレーのタイル状背景を描画する簡易グリッド（ワールド座標に対応）。
    main.py の同名関数から移動してここで再利用します。
    """
    tile = 64
    light = (50, 50, 50)
    dark = (40, 40, 40)
    # ワールド全体をタイル描画し、カメラオフセットを適用してスクリーンに描画
    for y in range(0, WORLD_HEIGHT, tile):
        for x in range(0, WORLD_WIDTH, tile):
            sx = x - camera_x
            sy = y - camera_y
            # 画面外はスキップ
            if sx + tile < 0 or sy + tile < 0 or sx > SCREEN_WIDTH or sy > SCREEN_HEIGHT:
                continue
            rect = (sx, sy, tile, tile)
            if (x // tile + y // tile) % 2 == 0:
                pygame.draw.rect(screen, light, rect)
            else:
                pygame.draw.rect(screen, dark, rect)
    # ビネットなどの余計な効果はここでは付けない（シンプルに）

def draw_initial_weapon_grid(screen, player, icons, virtual_mouse_pos=None):
    """初期武器選択用の3x3グリッドUIを描画する"""
    try:
        choices = getattr(player, 'last_level_choices', None)
        # reset flag if no choices
        if not choices:
            try:
                player._powerup_played_for_level_choice = False
            except Exception:
                pass
            return

        # Play powerup sound once when the level-up UI is first opened
        try:
            if not getattr(player, '_powerup_played_for_level_choice', False):
                audio.play_sound('powerup')
                player._powerup_played_for_level_choice = True
        except Exception:
            pass

        # 説明データの読み込み
        try:
            data_path = get_resource_path(os.path.join('data', 'descriptions.json'))
            with open(data_path, 'r', encoding='utf-8') as f:
                desc_data = json.load(f)
        except Exception:
            desc_data = {'weapons': {}, 'subitems': {}}

        # 背景オーバーレイ
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # グリッド設定（レベルアップと同じ幅を3x3に分割）
        grid_size = 3
        cw = min(880, SCREEN_WIDTH - 160)  # レベルアップと同じパネル幅
        option_w = (cw - 40) // grid_size  # 3分割
        cell_margin = 8
        option_h = 142  # レベルアップと同じ高さ
        panel_w = cw
        panel_h = grid_size * (option_h + cell_margin) + 100  # 縦方向のスペース確保（タイトル+余白）

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        # パネルが画面からはみ出ないように調整
        panel_y = max(20, cy - panel_h // 2)  # 上端から最低20pxの余白を確保
        if panel_y + panel_h > SCREEN_HEIGHT - 20:  # 下端からも20pxの余白を確保
            panel_y = SCREEN_HEIGHT - panel_h - 20
        panel_rect = pygame.Rect(cx - panel_w // 2, panel_y, panel_w, panel_h)

        # パネル背景
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((18, 18, 20, 230))
        accent_h = 54
        pygame.draw.rect(panel_surf, (36, 200, 185, 230), (0, 0, panel_rect.width, accent_h), border_radius=12)
        pygame.draw.rect(panel_surf, (10, 10, 10), (0, 0, panel_rect.width, panel_rect.height), 3, border_radius=12)
        pygame.draw.line(panel_surf, (255, 255, 255, 28), (12, accent_h - 8), (panel_rect.width - 12, accent_h - 8), 2)
        screen.blit(panel_surf, panel_rect.topleft)

        # タイトル
        title_font = get_font(24)
        screen.blit(title_font.render('最初の武器を選ぼう！', True, WHITE), (panel_rect.x + 24, panel_rect.y + 10))

        # グリッドセル描画（レベルアップと同じレイアウト）
        # 仮想マウス座標を使用（全画面対応）
        if virtual_mouse_pos:
            mouse_x, mouse_y = virtual_mouse_pos
        else:
            mouse_x, mouse_y = pygame.mouse.get_pos()
        selected_index = getattr(player, 'selected_weapon_choice_index', 0)
        
        title_font = get_font(24)
        small_font = get_font(14)
        option_h = 142  # レベルアップと同じ高さ

        for i, weapon_key in enumerate(choices[:9]):  # 最大9個まで
            if weapon_key.startswith('weapon:'):
                key = weapon_key.split(':', 1)[1]
            else:
                key = weapon_key

            row = i // grid_size
            col = i % grid_size
            
            # レベルアップと同じ配置計算
            rect_x = panel_rect.x + 20 + col * option_w
            rect_y = panel_rect.y + accent_h + 12 + row * (option_h + cell_margin)
            rect = pygame.Rect(rect_x, rect_y, option_w - 8, option_h)

            # セル背景（レベルアップと同じスタイル）
            pygame.draw.rect(screen, (28, 28, 30), rect, border_radius=10)

            # 選択状態の表示
            is_selected = (i == selected_index)
            is_mouse_hover = rect.collidepoint((mouse_x, mouse_y))
            show_keyboard_cursor = getattr(player, 'should_show_keyboard_cursor', lambda: True)()
            
            if (is_selected and show_keyboard_cursor) or is_mouse_hover:
                hl = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                if is_selected and show_keyboard_cursor:
                    hl.fill((50, 230, 200, 48))
                    pygame.draw.rect(screen, (36, 200, 185), rect, 4, border_radius=10)
                else:
                    hl.fill((50, 230, 200, 28))
                    pygame.draw.rect(screen, (36, 200, 185), rect, 3, border_radius=10)
                screen.blit(hl, rect.topleft)
            else:
                pygame.draw.rect(screen, (60, 60, 60), rect, 2, border_radius=10)

            # バッジ（レベルアップと同じスタイル）
            try:
                badge_surf = small_font.render('WEAPON', True, (0, 0, 0))
                bw = badge_surf.get_width() + 10
                bh = badge_surf.get_height() + 6
                bx = rect.x + 8
                by = rect.bottom - bh - 8
                pygame.draw.rect(screen, (255, 160, 60), (bx, by, bw, bh), border_radius=6)
                screen.blit(badge_surf, (bx + (bw - badge_surf.get_width()) // 2, by + (bh - badge_surf.get_height()) // 2))
            except Exception:
                pass

            # アイコン描画（レベルアップと同じ位置とサイズ）
            icon_x, icon_y, icon_size = rect.x + 12, rect.y + 12, 32
            icon_surf = None
            try:
                if icons and isinstance(icons, dict):
                    icon_surf = icons.get(key)
            except Exception:
                icon_surf = None

            if icon_surf:
                try:
                    screen.blit(pygame.transform.scale(icon_surf, (icon_size, icon_size)), (icon_x, icon_y))
                except Exception:
                    pygame.draw.rect(screen, (120, 120, 120), (icon_x, icon_y, icon_size, icon_size))
            else:
                pygame.draw.rect(screen, (120, 120, 120), (icon_x, icon_y, icon_size, icon_size))

            # テキスト（レベルアップと同じレイアウト）
            try:
                weapon_data = desc_data.get('weapons', {}).get(key, {})
                display_name = weapon_data.get('name', key.replace('_', ' ').title())
                long_desc = weapon_data.get('description', 'New weapon')

                # 武器名（レベルアップと同じ位置）
                screen.blit(title_font.render(display_name, True, WHITE), (rect.x + 16 + 32, rect.y + 8))
                
                # 説明文（レベルアップと同じレイアウト）
                desc_x, desc_y, desc_w = rect.x + 16 + 32, rect.y + 44, rect.width - (16 + 32 + 24)
                if long_desc:
                    for li, surf in enumerate(render_wrapped_jp(long_desc, small_font, (200, 200, 200), desc_w, max_lines=4)):
                        screen.blit(surf, (desc_x, desc_y + li * (small_font.get_height() - 3)))

            except Exception:
                # フォールバック：キー名のみ表示
                fallback_name = key.replace('_', ' ').title()
                screen.blit(title_font.render(fallback_name, True, WHITE), (rect.x + 16 + 32, rect.y + 8))

            # 右上のNEWバッジ（レベルアップと同じスタイル）
            try:
                if key in getattr(player, 'available_weapons', {}):
                    new_surf = small_font.render('NEW', True, (8, 8, 8))
                    new_w, new_h = new_surf.get_width() + 10, new_surf.get_height() + 6
                    new_x = max(rect.x + 8, rect.x + rect.width - new_w - 12)
                    new_y = rect.y + 10
                    pygame.draw.rect(screen, (255, 200, 60), (new_x, new_y, new_w, new_h), border_radius=6)
                    screen.blit(new_surf, (new_x + (new_w - new_surf.get_width()) // 2, new_y + (new_h - new_surf.get_height()) // 2))
            except Exception:
                pass

        # 操作説明
        try:
            help_font = get_font(14)
            help_text = "Use arrow keys or 1-9 keys to select, ENTER to confirm"
            help_surf = help_font.render(help_text, True, (180, 180, 180))
            help_x = panel_rect.x + (panel_rect.width - help_surf.get_width()) // 2
            help_y = panel_rect.y + panel_rect.height - 30
            screen.blit(help_surf, (help_x, help_y))
        except Exception:
            pass

    except Exception:
        pass

def draw_level_choice(screen, player, icons, virtual_mouse_pos=None):
    """レベルアップ（または開始時）の3択オーバーレイを描画する。"""
    try:
        # 初期武器選択の場合はグリッドUIを使用
        if getattr(player, 'is_initial_weapon_selection', False):
            draw_initial_weapon_grid(screen, player, icons, virtual_mouse_pos)
            return

        choices = getattr(player, 'last_level_choices', None)
        if not choices:
            return

        # Play powerup sound once when the level-up UI is first opened (normal 3-choice UI)
        try:
            if not getattr(player, '_powerup_played_for_level_choice', False):
                audio.play_sound('powerup')
                player._powerup_played_for_level_choice = True
        except Exception:
            pass

        # 説明データの読み込み
        try:
            data_path = get_resource_path(os.path.join('data', 'descriptions.json'))
            with open(data_path, 'r', encoding='utf-8') as f:
                desc_data = json.load(f)
        except Exception:
            desc_data = {'weapons': {}, 'subitems': {}}

        # 背景オーバーレイ
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        # パネル
        cw = min(880, SCREEN_WIDTH - 160)
        ch = 220
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        panel_rect = pygame.Rect(cx - cw // 2, cy - ch // 2, cw, ch)
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((18, 18, 20, 230))
        accent_h = 54
        pygame.draw.rect(panel_surf, (36, 200, 185, 230), (0, 0, panel_rect.width, accent_h), border_radius=12)
        pygame.draw.rect(panel_surf, (10, 10, 10), (0, 0, panel_rect.width, panel_rect.height), 3, border_radius=12)
        pygame.draw.line(panel_surf, (255, 255, 255, 28), (12, accent_h - 8), (panel_rect.width - 12, accent_h - 8), 2)
        screen.blit(panel_surf, panel_rect.topleft)

        title_font = get_font(24)
        middle_font = get_font(18)
        small_font = get_font(14)
        screen.blit(title_font.render('Choose Your Reward', True, WHITE), (panel_rect.x + 24, panel_rect.y + 10))

        option_w = (cw - 40) // max(1, len(choices))
        option_h = ch - 78
        
        # 仮想マウス座標を使用（全画面対応）
        if virtual_mouse_pos:
            mouse_x, mouse_y = virtual_mouse_pos
        else:
            mouse_x, mouse_y = pygame.mouse.get_pos()

        for i, raw in enumerate(choices):
            typ, key = ('weapon', raw)
            if isinstance(raw, str) and ':' in raw:
                parts = raw.split(':', 1)
                if len(parts) == 2:
                    typ, key = parts[0], parts[1]

            rect = pygame.Rect(panel_rect.x + 20 + i * option_w, panel_rect.y + accent_h + 12, option_w - 8, option_h)
            pygame.draw.rect(screen, (28, 28, 30), rect, border_radius=10)

            # 強調
            is_selected = (i == getattr(player, 'selected_weapon_choice_index', -1))
            is_mouse_hover = rect.collidepoint((mouse_x, mouse_y))
            show_keyboard_cursor = getattr(player, 'should_show_keyboard_cursor', lambda: True)()
            
            # キーボード使用時のみ選択カーソルを表示、マウス使用時はホバーのみ
            if (is_selected and show_keyboard_cursor) or is_mouse_hover:
                hl = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                if is_selected and show_keyboard_cursor:
                    # キーボード選択時：より強い強調
                    hl.fill((50, 230, 200, 48))
                    pygame.draw.rect(screen, (36, 200, 185), rect, 4, border_radius=10)
                else:
                    # マウスホバー時：弱い強調
                    hl.fill((50, 230, 200, 28))
                    pygame.draw.rect(screen, (36, 200, 185), rect, 3, border_radius=10)
                screen.blit(hl, rect.topleft)
            else:
                pygame.draw.rect(screen, (60, 60, 60), rect, 2, border_radius=10)

            # バッジ
            try:
                badge_label = 'WEAPON' if typ == 'weapon' else 'SUB'
                badge_bg = (255, 160, 60) if typ == 'weapon' else (80, 200, 140)
                badge_surf = small_font.render(badge_label, True, (0, 0, 0))
                bw = badge_surf.get_width() + 10
                bh = badge_surf.get_height() + 6
                bx = rect.x + 8
                by = rect.bottom - bh - 8
                pygame.draw.rect(screen, badge_bg, (bx, by, bw, bh), border_radius=6)
                screen.blit(badge_surf, (bx + (bw - badge_surf.get_width()) // 2, by + (bh - badge_surf.get_height()) // 2))
            except Exception:
                pass

            # アイコン
            icon_x, icon_y, icon_size = rect.x + 12, rect.y + 12, 32
            icon_surf = None
            try:
                if icons and isinstance(icons, dict):
                    icon_surf = icons.get(key)
            except Exception:
                icon_surf = None
            if icon_surf:
                try:
                    screen.blit(pygame.transform.scale(icon_surf, (icon_size, icon_size)), (icon_x, icon_y))
                except Exception:
                    pygame.draw.rect(screen, (120, 120, 120), (icon_x, icon_y, icon_size, icon_size))
            else:
                if typ == 'sub':
                    pygame.draw.circle(screen, (120, 200, 140), (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2)
                    pygame.draw.circle(screen, BLACK, (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2, 2)
                else:
                    pygame.draw.rect(screen, (120, 120, 120), (icon_x, icon_y, icon_size, icon_size))

            # テキスト
            # 新しい形式の名前と説明を取得
            display_name = key.replace('_', ' ').title()  # デフォルト名
            long_desc = ''
            try:
                category_data = desc_data['weapons' if typ == 'weapon' else 'subitems']
                item_data = category_data.get(key, {})
                if isinstance(item_data, dict):
                    display_name = item_data.get('name', display_name)
                    long_desc = item_data.get('description', '')
            except Exception:
                pass
            
            screen.blit(title_font.render(display_name, True, WHITE), (rect.x + 16 + 32, rect.y + 8))
            desc_x, desc_y, desc_w = rect.x + 16 + 32, rect.y + 44, rect.width - (16 + 32 + 24)
            if long_desc:
                for li, surf in enumerate(render_wrapped_jp(long_desc, small_font, (200, 200, 200), desc_w, max_lines=4)):
                    screen.blit(surf, (desc_x, desc_y + li * (small_font.get_height() - 3)))
            else:
                if typ == 'weapon':
                    desc = 'New Weapon' if key in getattr(player, 'available_weapons', {}) else 'Upgrade'
                else:
                    tmpl = getattr(player, 'subitem_templates', {}).get(key)
                    desc = f"+{tmpl.per_level}{('%' if getattr(tmpl, 'is_percent', False) else '')} per level" if tmpl else 'Subitem'
                screen.blit(small_font.render(desc, True, (200, 200, 200)), (desc_x, desc_y))

            # 右上のレベル/NEW表示
            if typ == 'weapon':
                w = None
                try:
                    w = player.weapons.get(key)
                except Exception:
                    w = None
                if w is not None:
                    try:
                        lvl_val = int(getattr(w, 'level', 1))
                    except Exception:
                        lvl_val = 1
                    if lvl_val >= MAX_WEAPON_LEVEL:
                        try:
                            b = small_font.render('MAX', True, WHITE)
                            bw, bh = b.get_width() + 8, b.get_height() + 4
                            bx, by = rect.x + rect.width - bw - 12, rect.y + 10
                            pygame.draw.rect(screen, (200, 60, 60), (bx, by, bw, bh), border_radius=4)
                            screen.blit(b, (bx + (bw - b.get_width()) // 2, by + (bh - b.get_height()) // 2))
                        except Exception:
                            pass
                    else:
                        try:
                            level_s = middle_font.render(f"Lv.{lvl_val + 1}", True, (50, 220, 220))
                            screen.blit(level_s, (rect.x + rect.width - level_s.get_width() - 12, rect.y + 12))
                        except Exception:
                            pass
                else:
                    try:
                        if key in getattr(player, 'available_weapons', {}):
                            b = small_font.render('NEW', True, (8, 8, 8))
                            bw, bh = b.get_width() + 10, b.get_height() + 6
                            bx = max(rect.x + 8, rect.x + rect.width - bw - 12)
                            by = rect.y + 10
                            pygame.draw.rect(screen, (255, 200, 60), (bx, by, bw, bh), border_radius=6)
                            screen.blit(b, (bx + (bw - b.get_width()) // 2, by + (bh - b.get_height()) // 2))
                    except Exception:
                        pass
            else:
                owned = key in getattr(player, 'subitems', {})
                if owned:
                    try:
                        lvl = int(getattr(player.subitems.get(key), 'level', 1))
                    except Exception:
                        lvl = 1
                    if lvl >= MAX_SUBITEM_LEVEL:
                        try:
                            b = small_font.render('MAX', True, WHITE)
                            bw, bh = b.get_width() + 8, b.get_height() + 4
                            bx, by = rect.x + rect.width - bw - 12, rect.y + 10
                            pygame.draw.rect(screen, (200, 60, 60), (bx, by, bw, bh), border_radius=4)
                            screen.blit(b, (bx + (bw - b.get_width()) // 2, by + (bh - b.get_height()) // 2))
                        except Exception:
                            pass
                    else:
                        try:
                            level_s = middle_font.render(f"Lv {lvl + 1}", True, (50, 220, 220))
                            screen.blit(level_s, (rect.x + rect.width - level_s.get_width() - 12, rect.y + 12))
                        except Exception:
                            pass
                else:
                    try:
                        b = small_font.render('NEW', True, (8, 8, 8))
                        bw, bh = b.get_width() + 10, b.get_height() + 6
                        bx = max(rect.x + 8, rect.x + rect.width - bw - 12)
                        by = rect.y + 10
                        pygame.draw.rect(screen, (255, 200, 60), (bx, by, bw, bh), border_radius=6)
                        screen.blit(b, (bx + (bw - b.get_width()) // 2, by + (bh - b.get_height()) // 2))
                    except Exception:
                        pass
    except Exception:
        pass

def get_end_button_rects(is_game_clear=False):
    """GAME OVER / CLEAR 時に表示するボタンの矩形を返す。描画は行わない。
    戻り値: {'restart': Rect, 'continue': Rect or None, 'settings': Rect}
    """
    try:
        button_w = 220
        button_h = 48
        gap = 24
        
        # 設定ボタン（小さめ、右上に配置）
        settings_w = 100
        settings_h = 40
        settings_x = SCREEN_WIDTH - settings_w - 20
        settings_y = 20
        settings_rect = pygame.Rect(settings_x, settings_y, settings_w, settings_h)
        
        if is_game_clear:
            # GameClear時はRestartボタンのみ（中央配置）
            cx = SCREEN_WIDTH // 2
            by = SCREEN_HEIGHT - button_h - 40  # 画面最下部から40px上
            restart_rect = pygame.Rect(cx - button_w // 2, by, button_w, button_h)
            return {'restart': restart_rect, 'continue': None, 'settings': settings_rect}
        else:
            # GameOver時は両方のボタン
            total_w = button_w * 2 + gap
            cx = SCREEN_WIDTH // 2
            by = SCREEN_HEIGHT - button_h - 40  # 画面最下部から40px上
            left_x = cx - total_w // 2
            restart_rect = pygame.Rect(left_x, by, button_w, button_h)
            continue_rect = pygame.Rect(left_x + button_w + gap, by, button_w, button_h)
            return {'restart': restart_rect, 'continue': continue_rect, 'settings': settings_rect}
    except Exception:
        return {'restart': None, 'continue': None, 'settings': None}


def draw_end_buttons(screen, is_game_over, is_game_clear, selected_option=0):
    """エンド画面用のボタンを描画し、矩形を返す。主に main.py 側でクリック判定に使う。
    
    Args:
        screen: 描画対象のスクリーン
        is_game_over: ゲームオーバー状態
        is_game_clear: ゲームクリア状態
        selected_option: 選択されたオプション (0: Restart (left), 1: Continue (right), 2: Settings)
    """
    rects = get_end_button_rects(is_game_clear)
    restart_rect = rects.get('restart')
    continue_rect = rects.get('continue')
    settings_rect = rects.get('settings')
    
    try:
        font = get_font(18)
        
        # 設定ボタンを常に描画
        if settings_rect:
            try:
                if selected_option == 2:  # Settings選択中
                    pygame.draw.rect(screen, (80, 80, 120), settings_rect, border_radius=6)  # 明るい青系
                    pygame.draw.rect(screen, (255, 255, 255), settings_rect, width=2, border_radius=6)
                else:
                    pygame.draw.rect(screen, (50, 50, 70), settings_rect, border_radius=6)  # 通常の青系
                
                # テキスト描画
                settings_font = get_font(16)
                settings_txt = settings_font.render('設定', True, WHITE)
                screen.blit(settings_txt, (settings_rect.centerx - settings_txt.get_width()//2, 
                                         settings_rect.centery - settings_txt.get_height()//2))
            except Exception:
                pass
        
        if is_game_clear:
            # GameClear時はRestartボタンのみ
            try:
                if selected_option == 0:  # Restart選択中
                    pygame.draw.rect(screen, (80, 80, 80), restart_rect, border_radius=8)  # 明るい灰色
                    # 選択中の枠線を描画（白い太枠）
                    pygame.draw.rect(screen, (255, 255, 255), restart_rect, width=3, border_radius=8)
                    # 影のような効果を追加
                    shadow_rect = pygame.Rect(restart_rect.x + 2, restart_rect.y + 2, restart_rect.width, restart_rect.height)
                    pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, width=1, border_radius=8)
                else:
                    pygame.draw.rect(screen, (40, 40, 40), restart_rect, border_radius=8)  # 通常の灰色
                
                # テキスト描画
                txt_font = get_font(20) if selected_option == 0 else font
                txt = txt_font.render('Restart', True, WHITE)
                screen.blit(txt, (restart_rect.centerx - txt.get_width()//2, restart_rect.centery - txt.get_height()//2))
            except Exception:
                pass
        
        elif is_game_over:
            # GameOver時はContinueとRestartの両方
            # Continue - 選択状態に応じて色を変更
            try:
                if selected_option == 1:  # Continue選択中 (right)
                    pygame.draw.rect(screen, (60, 200, 60), continue_rect, border_radius=8)  # 明るい緑
                    # 選択中の枠線を描画（白い太枠）
                    pygame.draw.rect(screen, (255, 255, 255), continue_rect, width=3, border_radius=8)
                    # 影のような効果を追加
                    shadow_rect = pygame.Rect(continue_rect.x + 2, continue_rect.y + 2, continue_rect.width, continue_rect.height)
                    pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, width=1, border_radius=8)
                else:
                    pygame.draw.rect(screen, (40, 160, 40), continue_rect, border_radius=8)  # 通常の緑
            except Exception:
                pass
            # Restart - 選択状態に応じて色を変更
            try:
                if selected_option == 0:  # Restart選択中 (left)
                    pygame.draw.rect(screen, (80, 80, 80), restart_rect, border_radius=8)  # 明るい灰色
                    # 選択中の枠線を描画（白い太枠）
                    pygame.draw.rect(screen, (255, 255, 255), restart_rect, width=3, border_radius=8)
                    # 影のような効果を追加
                    shadow_rect = pygame.Rect(restart_rect.x + 2, restart_rect.y + 2, restart_rect.width, restart_rect.height)
                    pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, width=1, border_radius=8)
                else:
                    pygame.draw.rect(screen, (40, 40, 40), restart_rect, border_radius=8)  # 通常の灰色
            except Exception:
                pass

            try:
                # 選択中のボタンのテキストは少し大きく表示
                if selected_option == 0:  # Restart選択中 (left)
                    txt_font = get_font(20)  # 少し大きなフォント
                    txt = txt_font.render('Restart', True, WHITE)
                else:
                    txt = font.render('Restart', True, WHITE)
                screen.blit(txt, (restart_rect.centerx - txt.get_width()//2, restart_rect.centery - txt.get_height()//2))
            except Exception:
                pass
            try:
                # 選択中のボタンのテキストは少し大きく表示
                if selected_option == 1:  # Continue選択中 (right)
                    txt_font = get_font(20)  # 少し大きなフォント
                    txt = txt_font.render('Continue', True, WHITE)
                else:
                    txt = font.render('Continue', True, WHITE)
                screen.blit(txt, (continue_rect.centerx - txt.get_width()//2, continue_rect.centery - txt.get_height()//2))
            except Exception:
                pass
        # （どちらの終了状態でも上で Continue / Restart を描画しているため、ここでは追加の分岐は不要）
    except Exception:
        pass
    return rects

def draw_subitem_choice(screen, player, icons=None, virtual_mouse_pos=None):
    """サブアイテム選択 UI を描画する。player.last_subitem_choices を参照。"""
    try:
        choices = getattr(player, 'last_subitem_choices', None)
        # reset flag if no choices
        if not choices:
            try:
                player._powerup_played_for_subitem_choice = False
            except Exception:
                pass
            return

        # Play powerup sound once when the subitem selection UI is first opened
        try:
            if not getattr(player, '_powerup_played_for_subitem_choice', False):
                audio.play_sound('powerup')
                player._powerup_played_for_subitem_choice = True
        except Exception:
            pass

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        cw = min(700, SCREEN_WIDTH - 200)
        ch = 180
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        panel_rect = pygame.Rect(cx - cw // 2, cy - ch // 2, cw, ch)

        panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel.fill((22, 22, 26, 230))
        pygame.draw.rect(panel, (12, 12, 12), (0, 0, panel_rect.width, panel_rect.height), 3, border_radius=10)
        screen.blit(panel, panel_rect.topleft)

        title_font = get_font(22)
        small = get_font(14)
        screen.blit(title_font.render('Choose a Subitem', True, WHITE), (panel_rect.x + 18, panel_rect.y + 10))

        option_w = (cw - 40) // max(1, len(choices))
        option_h = ch - 60
        
        # 仮想マウス座標を使用（全画面対応）
        if virtual_mouse_pos:
            mx, my = virtual_mouse_pos
        else:
            mx, my = pygame.mouse.get_pos()

        for i, key in enumerate(choices):
            rect = pygame.Rect(panel_rect.x + 20 + i * option_w, panel_rect.y + 48, option_w - 8, option_h)
            pygame.draw.rect(screen, (30, 30, 34), rect, border_radius=8)

            is_selected = (i == getattr(player, 'selected_subitem_choice_index', -1))
            is_mouse_hover = rect.collidepoint((mx, my))
            show_keyboard_cursor = getattr(player, 'should_show_keyboard_cursor', lambda: True)()
            
            # キーボード使用時のみ選択カーソルを表示、マウス使用時はホバーのみ
            if (is_selected and show_keyboard_cursor) or is_mouse_hover:
                hl = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                if is_selected and show_keyboard_cursor:
                    # キーボード選択時：より強い強調
                    hl.fill((80, 200, 120, 48))
                    pygame.draw.rect(screen, (80, 200, 120), rect, 4, border_radius=8)
                else:
                    # マウスホバー時：弱い強調
                    hl.fill((80, 200, 120, 28))
                    pygame.draw.rect(screen, (80, 200, 120), rect, 3, border_radius=8)
                screen.blit(hl, rect.topleft)
            else:
                pygame.draw.rect(screen, (60, 60, 60), rect, 2, border_radius=8)

            # バッジ
            try:
                badge_w, badge_h = 56, 18
                badge_x = rect.x + 8
                badge_y = rect.bottom - badge_h - 8
                pygame.draw.rect(screen, (80, 200, 140), (badge_x, badge_y, badge_w, badge_h), border_radius=6)
                blt = small.render('SUB', True, (0, 0, 0))
                screen.blit(blt, (badge_x + (badge_w - blt.get_width()) // 2, badge_y + (badge_h - blt.get_height()) // 2))
            except Exception:
                pass

            # アイコン
            try:
                icon_size = 28
                icon_x = rect.x + 12
                icon_y = rect.y + 12
                icon_surf = icons.get(key) if (icons and isinstance(icons, dict)) else None
                if icon_surf:
                    try:
                        screen.blit(pygame.transform.scale(icon_surf, (icon_size, icon_size)), (icon_x, icon_y))
                    except Exception:
                        pygame.draw.circle(screen, (120, 120, 120), (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2)
                        pygame.draw.circle(screen, BLACK, (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2, 2)
                else:
                    pygame.draw.circle(screen, (120, 200, 140), (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2)
                    pygame.draw.circle(screen, BLACK, (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2, 2)
            except Exception:
                pass

            # テキスト
            # 新しい形式の名前と説明を取得
            display_name = key.replace('_', ' ').title()  # デフォルト名
            long_desc = ''
            try:
                data_path = get_resource_path(os.path.join('data', 'descriptions.json'))
                with open(data_path, 'r', encoding='utf-8') as f:
                    sub_desc_data = json.load(f).get('subitems', {})
                item_data = sub_desc_data.get(key, {})
                if isinstance(item_data, dict):
                    display_name = item_data.get('name', display_name)
                    long_desc = item_data.get('description', '')
            except Exception:
                pass
            
            screen.blit(title_font.render(display_name, True, WHITE), (rect.x + 12 + 36, rect.y + 8))
            if long_desc:
                desc_x, desc_y, desc_w = rect.x + 12 + 36, rect.y + 40, rect.width - (12 + 36 + 20)
                lines = render_wrapped_jp(long_desc, small, (200, 200, 200), desc_w, max_lines=3)
                for li, surf in enumerate(lines):
                    screen.blit(surf, (desc_x, desc_y + li * (small.get_height() - 3)))
            else:
                tmpl = getattr(player, 'subitem_templates', {}).get(key)
                desc = f"+{tmpl.per_level}{('%' if getattr(tmpl, 'is_percent', False) else '')} per level" if tmpl else ''
                screen.blit(small.render(desc, True, (200, 200, 200)), (rect.x + 12 + 36, rect.y + 40))

            if key in getattr(player, 'subitems', {}):
                lvl = getattr(player.subitems.get(key), 'level', 1)
                screen.blit(small.render(f"Lv {lvl}", True, (220, 220, 220)), (rect.x + 12 + 36, rect.y + 64))
                try:
                    if lvl >= MAX_SUBITEM_LEVEL:
                        b_surf = small.render('MAX', True, WHITE)
                        bw, bh = b_surf.get_width() + 8, b_surf.get_height() + 4
                        bx, by = rect.x + 12 + 36, rect.y + 64
                        pygame.draw.rect(screen, (200, 60, 60), (bx, by, bw, bh), border_radius=4)
                        screen.blit(b_surf, (bx + (bw - b_surf.get_width()) // 2, by + (bh - b_surf.get_height()) // 2))
                except Exception:
                    pass
    except Exception:
        pass

def get_enemy_info():
    """エネミー情報を読み込んで返す"""
    try:
        import os
        import csv
        # 直接ファイルパスを構築
        base_dir = os.path.dirname(os.path.dirname(__file__))
        csv_path = os.path.join(base_dir, 'data', 'enemy_stats.csv')
        
        enemy_info = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enemy_no = int(row['enemy_no'])
                enemy_info[enemy_no] = {
                    'type': int(row['type']),
                    'level': int(row['level']),
                    'image_file': row['image_file'],
                    'image_size': int(row['image_size'])
                }
        return enemy_info
    except Exception:
        return {}

def get_boss_info():
    """ボス情報を読み込んで返す"""
    try:
        import os
        import csv
        # 直接ファイルパスを構築
        base_dir = os.path.dirname(os.path.dirname(__file__))
        csv_path = os.path.join(base_dir, 'data', 'boss_stats.csv')
        
        boss_info = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                boss_no = int(row['No'])
                boss_info[boss_no] = {
                    'image_file': row['image_file']
                }
        return boss_info
    except Exception:
        return {}

def draw_enemy_kill_stats(screen, enemy_kill_stats, start_x, start_y, area_width, area_height):
    """エネミー撃破統計をアイコンと数字で表示"""
    try:
        import pygame
        import os
        
        # 直接ファイルパスを構築
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # エネミー情報を取得
        enemy_info = get_enemy_info()
        if not enemy_info:
            return
        
        # 表示用フォント（小さめ）
        small_font = get_font(12)
        
        # アイコンサイズとレイアウト設定
        icon_size = 24  # 小さめのアイコン
        cols = 10  # 横10個
        rows = 2   # 2段
        col_width = area_width // cols
        row_height = area_height // rows
        
        # 全20体のエネミーを順番に表示
        for enemy_no in range(1, 21):  # enemy_no 1-20
            if enemy_no not in enemy_info:
                continue
                
            # 行・列の計算
            col = (enemy_no - 1) % cols
            row = (enemy_no - 1) // cols
            if row >= rows:  # 2段を超える場合はスキップ
                break
                
            # 描画位置
            x = start_x + col * col_width + (col_width - icon_size) // 2
            y = start_y + row * row_height
            
            # 撃破数取得
            kill_count = enemy_kill_stats.get(enemy_no, 0)
            
            # エネミーアイコンを描画
            try:
                info = enemy_info[enemy_no]
                image_file = info['image_file']
                # 直接ファイルパスを構築（enemyサブフォルダを含む）
                assets_dir = os.path.join(base_dir, 'assets', 'character', 'enemy')
                image_path = os.path.join(assets_dir, f'{image_file}.png')
                
                if os.path.exists(image_path):
                    # 画像をロードしてリサイズ
                    enemy_image = pygame.image.load(image_path)
                    enemy_image = pygame.transform.scale(enemy_image, (icon_size, icon_size))
                    
                    # 撃破数が0の場合は半透明に
                    if kill_count == 0:
                        enemy_image.set_alpha(100)
                    
                    screen.blit(enemy_image, (x, y))
                else:
                    # 画像がない場合は色付きの四角で代用
                    type_colors = {1: (255, 100, 100), 2: (100, 255, 100), 3: (100, 100, 255), 4: (255, 255, 100)}
                    color = type_colors.get(info['type'], (150, 150, 150))
                    if kill_count == 0:
                        color = tuple(c // 3 for c in color)  # 暗くする
                    pygame.draw.rect(screen, color, (x, y, icon_size, icon_size))
                    pygame.draw.rect(screen, BLACK, (x, y, icon_size, icon_size), 1)
            except Exception:
                # 描画に失敗した場合はグレーの四角
                color = (50, 50, 50) if kill_count == 0 else (150, 150, 150)
                pygame.draw.rect(screen, color, (x, y, icon_size, icon_size))
                pygame.draw.rect(screen, BLACK, (x, y, icon_size, icon_size), 1)
            
            # 撃破数をアイコンの下に表示
            count_text = small_font.render(str(kill_count), True, BLACK if kill_count > 0 else (100, 100, 100))
            text_x = x + (icon_size - count_text.get_width()) // 2
            text_y = y + icon_size + 2
            screen.blit(count_text, (text_x, text_y))
            
    except Exception:
        pass

def draw_boss_kill_stats(screen, boss_kill_stats, start_x, start_y, area_width, area_height):
    """ボス撃破統計をアイコンと撃破マークで表示"""
    try:
        import pygame
        import os
        
        # ボス情報取得
        boss_info = get_boss_info()
        if not boss_info:
            return
        
        # 固定設定
        icon_size = 60
        check_size = 20  # チェックマークサイズ
        
        # フォント設定
        small_font = get_font(16)
        medium_font = get_font(20)
        
        # カラー定義
        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        GREEN = (0, 255, 0)
        
        # 基本ディレクトリ取得
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # ボス数を取得してアイコンの配置を計算
        boss_count = len(boss_info)
        if boss_count == 0:
            return
            
        # 横並びで配置
        total_width = boss_count * icon_size + (boss_count - 1) * 10  # アイコン間隔10px
        start_icon_x = start_x + (area_width - total_width) // 2
        
        # ボスアイコンを横並びで表示
        for i, boss_no in enumerate(sorted(boss_info.keys())):
            info = boss_info[boss_no]
            
            # 描画位置
            x = start_icon_x + i * (icon_size + 10)
            y = start_y
            
            # 撃破状況取得
            is_defeated = boss_kill_stats.get(boss_no, 0) > 0
            
            # ボスアイコンを描画
            try:
                image_file = info['image_file']
                # 直接ファイルパスを構築（enemyサブフォルダを含む）
                assets_dir = os.path.join(base_dir, 'assets', 'character', 'enemy')
                image_path = os.path.join(assets_dir, f'{image_file}.png')
                
                if os.path.exists(image_path):
                    # 画像をロードしてリサイズ
                    boss_image = pygame.image.load(image_path)
                    boss_image = pygame.transform.scale(boss_image, (icon_size, icon_size))
                    
                    # 未撃破の場合は半透明に
                    if not is_defeated:
                        boss_image.set_alpha(100)
                    
                    screen.blit(boss_image, (x, y))
                else:
                    # 画像がない場合は色付きの四角で代用（ボスは赤系）
                    color = (200, 50, 50) if is_defeated else (100, 25, 25)
                    pygame.draw.rect(screen, color, (x, y, icon_size, icon_size))
                    pygame.draw.rect(screen, BLACK, (x, y, icon_size, icon_size), 2)
            except Exception:
                # 描画に失敗した場合はグレーの四角
                color = (150, 150, 150) if is_defeated else (75, 75, 75)
                pygame.draw.rect(screen, color, (x, y, icon_size, icon_size))
                pygame.draw.rect(screen, BLACK, (x, y, icon_size, icon_size), 2)
            
            # 撃破済みの場合はチェックマークを重ねて表示
            if is_defeated:
                check_x = x + icon_size - check_size - 5
                check_y = y + 5
                
                # チェックマーク背景（白い円）
                pygame.draw.circle(screen, WHITE, (check_x + check_size // 2, check_y + check_size // 2), check_size // 2 + 2)
                pygame.draw.circle(screen, BLACK, (check_x + check_size // 2, check_y + check_size // 2), check_size // 2 + 2, 2)
                
                # チェックマーク（緑の✓）
                pygame.draw.circle(screen, GREEN, (check_x + check_size // 2, check_y + check_size // 2), check_size // 2)
                
                # ✓マークを線で描画
                check_points = [
                    (check_x + check_size // 4, check_y + check_size // 2),
                    (check_x + check_size // 2, check_y + check_size * 3 // 4),
                    (check_x + check_size * 3 // 4, check_y + check_size // 4)
                ]
                pygame.draw.lines(screen, WHITE, False, check_points, 3)
            
    except Exception:
        pass


def draw_settings_screen(screen, save_system, selected_difficulty=None, virtual_mouse_pos=None):
    """設定画面を描画する"""
    try:
        from constants import (DIFFICULTY_NAMES, DIFFICULTY_MULTIPLIERS, 
                              DIFFICULTY_VERY_EASY, DIFFICULTY_VERY_HARD)
        
        # 現在の難易度を取得
        current_difficulty = save_system.get_difficulty() if save_system else 3
        if selected_difficulty is not None:
            current_difficulty = selected_difficulty
        
        # 背景オーバーレイ
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # メインパネル
        panel_w = min(800, SCREEN_WIDTH - 100)
        panel_h = min(650, SCREEN_HEIGHT - 100)  # 600から650に変更（50px増加）
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        
        panel_surf = get_panel_surf(panel_w, panel_h, 12, 200)
        screen.blit(panel_surf, (panel_x, panel_y))
        
        # フォント
        title_font = get_font(48)
        subtitle_font = get_font(32)
        text_font = get_font(24)
        small_font = get_font(20)
        
        # タイトル
        title_surf = title_font.render("設定", True, WHITE)
        title_x = panel_x + (panel_w - title_surf.get_width()) // 2
        title_y = panel_y + 30
        screen.blit(title_surf, (title_x, title_y))
        
        # 難易度セクション
        subtitle_surf = subtitle_font.render("難易度選択", True, WHITE)
        subtitle_x = panel_x + 40
        subtitle_y = title_y + 80
        screen.blit(subtitle_surf, (subtitle_x, subtitle_y))
        
        # 難易度選択肢
        difficulty_buttons = []
        button_width = panel_w - 80
        button_height = 70  # 60から70に変更（10px増加）
        button_spacing = 80  # 70から80に変更（10px増加）
        
        start_y = subtitle_y + 60
        
        for i in range(DIFFICULTY_VERY_EASY, DIFFICULTY_VERY_HARD + 1):
            button_x = panel_x + 40
            button_y = start_y + (i - 1) * button_spacing
            
            # ボタンの当たり判定領域
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            difficulty_buttons.append((i, button_rect))
            
            # ボタンの背景色（選択中は明るく、ホバー時は中間色）
            is_selected = (i == current_difficulty)
            is_hovered = False
            
            if virtual_mouse_pos:
                mx, my = virtual_mouse_pos
                is_hovered = button_rect.collidepoint(mx, my)
            
            if is_selected:
                bg_color = (70, 140, 70)  # 選択中は緑系
                border_color = (100, 200, 100)
            elif is_hovered:
                bg_color = (60, 60, 80)   # ホバー時は青系
                border_color = (100, 100, 150)
            else:
                bg_color = (40, 40, 50)   # 通常は暗い
                border_color = (80, 80, 100)
            
            # ボタン描画
            pygame.draw.rect(screen, bg_color, button_rect, border_radius=8)
            pygame.draw.rect(screen, border_color, button_rect, 3, border_radius=8)
            
            # 難易度名
            diff_name = DIFFICULTY_NAMES.get(i, f"難易度{i}")
            name_surf = text_font.render(diff_name, True, WHITE)
            name_x = button_x + 20
            name_y = button_y + 8
            screen.blit(name_surf, (name_x, name_y))
            
            # 係数情報
            multipliers = DIFFICULTY_MULTIPLIERS.get(i, {"hp": 1.0, "damage": 1.0, "speed": 1.0})
            info_text = f"HP:{multipliers['hp']:.1f}倍 攻撃:{multipliers['damage']:.1f}倍 速度:{multipliers['speed']:.1f}倍"
            info_surf = small_font.render(info_text, True, (200, 200, 200))
            info_x = button_x + 20
            info_y = button_y + 35
            screen.blit(info_surf, (info_x, info_y))
        
        # 閉じるボタン
        close_button_w = 120
        close_button_h = 40
        close_button_x = panel_x + panel_w - close_button_w - 20
        # 最後のボタン（5番目）の下に30pxの間隔を空けて配置
        last_button_y = start_y + (5 - 1) * button_spacing + button_height
        close_button_y = last_button_y + 30
        close_button_rect = pygame.Rect(close_button_x, close_button_y, close_button_w, close_button_h)
        
        # 閉じるボタンのホバー判定
        close_hovered = False
        if virtual_mouse_pos:
            mx, my = virtual_mouse_pos
            close_hovered = close_button_rect.collidepoint(mx, my)
        
        close_bg = (80, 50, 50) if close_hovered else (50, 30, 30)
        close_border = (150, 80, 80) if close_hovered else (100, 60, 60)
        
        pygame.draw.rect(screen, close_bg, close_button_rect, border_radius=6)
        pygame.draw.rect(screen, close_border, close_button_rect, 2, border_radius=6)
        
        close_surf = text_font.render("閉じる", True, WHITE)
        close_text_x = close_button_x + (close_button_w - close_surf.get_width()) // 2
        close_text_y = close_button_y + (close_button_h - close_surf.get_height()) // 2
        screen.blit(close_surf, (close_text_x, close_text_y))
        
        # 戻り値として、ボタンの当たり判定情報を返す
        return {
            'difficulty_buttons': difficulty_buttons,
            'close_button': close_button_rect
        }
        
    except Exception as e:
        print(f"[ERROR] Settings screen drawing failed: {e}")
        return {'difficulty_buttons': [], 'close_button': None}
