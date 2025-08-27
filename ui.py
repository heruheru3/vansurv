import pygame
from constants import *

# 軽量キャッシュ: サーフェスとフォントを使い回す
_font_cache = {}
_surf_cache = {}

def get_font(size):
    key = f"font_{size}"
    f = _font_cache.get(key)
    if f is None:
        try:
            f = pygame.font.Font(None, size)
        except Exception:
            f = pygame.font.SysFont(None, size)
        _font_cache[key] = f
    return f

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

def draw_ui(screen, player, game_time, game_over, game_clear, damage_stats=None, icons=None, show_status=True):
    font = get_font(36)
    
    # HP/EXPをメーターバー形式で表示（画面上部にまとめて表示）
    meter_w = 300
    meter_h = 18
    pad = 12
    panel_w = meter_w + pad * 2
    panel_h = meter_h * 2 + pad * 3
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
    pygame.draw.rect(screen, CYAN, (bar_x, exp_y, int(meter_w * exp_ratio), meter_h), border_radius=6)
    exp_text = font.render(f"LV{getattr(player,'level',1)} EXP {getattr(player,'exp',0)}/{exp_to}", True, WHITE)
    exp_rect = exp_text.get_rect(midleft=(bar_x + 8, exp_y + meter_h // 2))
    screen.blit(exp_text, exp_rect.topleft)

    # 時間表示
    time_text = font.render(f"Time: {int(game_time)}s", True, WHITE)
    screen.blit(time_text, (16, 76))

    # ゲームクリア/オーバー表示を修正
    if game_clear:
        # タイトル／時間／再開テキストを、リザルト表と重ならないように配置
        big_font = get_font(72)
        final_time_font = get_font(40)
        restart_font = get_font(28)

        if damage_stats:
            # リザルト表の開始位置を再計算して、その上に収まるようにする
            table_h = 320
            table_y = max(20, (SCREEN_HEIGHT - table_h) // 2 - 20)
            title_y = table_y - 80
            time_y = table_y - 32
            restart_y = table_y - 8
        else:
            title_y = SCREEN_HEIGHT // 2 - 80
            time_y = SCREEN_HEIGHT // 2 - 20
            restart_y = SCREEN_HEIGHT // 2 + 20

        clear_surf = big_font.render("GAME CLEAR!", True, GREEN)
        clear_rect = clear_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(clear_surf, clear_rect)

        final_time = final_time_font.render(f"Survival Time: {int(game_time)}s", True, GREEN)
        final_time_rect = final_time.get_rect(center=(SCREEN_WIDTH // 2, time_y))
        screen.blit(final_time, final_time_rect)

        restart_text = restart_font.render("Press ENTER to restart", True, GREEN)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, restart_y))
        screen.blit(restart_text, restart_rect)

        # リザルト表示: 半透明の白背景に変更し、垂直方向は中央よりやや上に配置
        if damage_stats:
            # テーブル領域を調整
            table_w = min(880, SCREEN_WIDTH - 80)
            table_h = 320
            # 垂直方向の中央にして少し上に寄せる
            table_x = (SCREEN_WIDTH - table_w) // 2
            table_y = max(20, (SCREEN_HEIGHT - table_h) // 2 - 20)

            # 半透明の白背景をサーフェスで取得（キャッシュ）
            result_surf = get_result_surf(table_w, table_h, alpha=128)
            screen.blit(result_surf, (table_x, table_y))

            header_font = get_font(34)
            row_font = get_font(30)
            # ヘッダ（サーフェス上に描画する代わりに直接座標で描画）
            screen.blit(header_font.render("Weapon", True, BLACK), (table_x + 24, table_y + 8))
            screen.blit(header_font.render("Total Damage", True, BLACK), (table_x + 280, table_y + 8))
            screen.blit(header_font.render("DPS", True, BLACK), (table_x + 560, table_y + 8))

            total_time = max(1.0, game_time)
            # ソートして表示（ダメージ降順）
            items = sorted(damage_stats.items(), key=lambda kv: kv[1], reverse=True)
            row_y = table_y + 56
            row_height = 40
            for wname, dmg in items:
                dps = dmg / total_time
                screen.blit(row_font.render(str(wname), True, BLACK), (table_x + 24, row_y))
                screen.blit(row_font.render(str(int(dmg)), True, BLACK), (table_x + 320, row_y))
                screen.blit(row_font.render(f"{dps:.1f}", True, BLACK), (table_x + 580, row_y))
                row_y += row_height
                # テーブルが溢れたら停止
                if row_y + row_height > table_y + table_h - 40:
                    break

            # 合計行
            total_dmg = sum(damage_stats.values())
            row_y = table_y + table_h - 40
            screen.blit(row_font.render("Total", True, BLACK), (table_x + 24, row_y))
            screen.blit(row_font.render(str(int(total_dmg)), True, BLACK), (table_x + 320, row_y))
            screen.blit(row_font.render(f"{(total_dmg/total_time):.1f}", True, BLACK), (table_x + 580, row_y))

    elif game_over:
        # タイトル／時間／再開テキストを、リザルト表と重ならないように配置
        big_font = get_font(72)
        final_time_font = get_font(40)
        restart_font = get_font(28)

        if damage_stats:
            table_h = 320
            table_y = max(20, (SCREEN_HEIGHT - table_h) // 2 - 20)
            title_y = table_y - 80
            time_y = table_y - 32
            restart_y = table_y - 8
        else:
            title_y = SCREEN_HEIGHT // 2 - 80
            time_y = SCREEN_HEIGHT // 2 - 20
            restart_y = SCREEN_HEIGHT // 2 + 20

        over_surf = big_font.render("GAME OVER", True, RED)
        over_rect = over_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(over_surf, over_rect)

        final_time = final_time_font.render(f"Survival Time: {int(game_time)}s", True, RED)
        final_time_rect = final_time.get_rect(center=(SCREEN_WIDTH // 2, time_y))
        screen.blit(final_time, final_time_rect)

        restart_text = restart_font.render("Press ENTER to restart", True, RED)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, restart_y))
        screen.blit(restart_text, restart_rect)

    # 結果パネル: ゲーム終了時に damage_stats があれば表示（GAME CLEAR / GAME OVER 共通）
    try:
        if (game_over or game_clear) and damage_stats:
            table_w = min(880, SCREEN_WIDTH - 80)
            table_h = 320
            table_x = (SCREEN_WIDTH - table_w) // 2
            table_y = max(20, (SCREEN_HEIGHT - table_h) // 2 - 20)

            result_surf = get_result_surf(table_w, table_h, alpha=128)
            screen.blit(result_surf, (table_x, table_y))

            header_font = get_font(34)
            row_font = get_font(30)
            screen.blit(header_font.render("Weapon", True, BLACK), (table_x + 24, table_y + 8))
            screen.blit(header_font.render("Total Damage", True, BLACK), (table_x + 280, table_y + 8))
            screen.blit(header_font.render("DPS", True, BLACK), (table_x + 560, table_y + 8))

            total_time = max(1.0, game_time)
            items = sorted(damage_stats.items(), key=lambda kv: kv[1], reverse=True)
            row_y = table_y + 56
            row_height = 40
            for wname, dmg in items:
                dps = dmg / total_time
                screen.blit(row_font.render(str(wname), True, BLACK), (table_x + 24, row_y))
                screen.blit(row_font.render(str(int(dmg)), True, BLACK), (table_x + 320, row_y))
                screen.blit(row_font.render(f"{dps:.1f}", True, BLACK), (table_x + 580, row_y))
                row_y += row_height
                if row_y + row_height > table_y + table_h - 40:
                    break

            total_dmg = sum(damage_stats.values())
            row_y = table_y + table_h - 40
            screen.blit(row_font.render("Total", True, BLACK), (table_x + 24, row_y))
            screen.blit(row_font.render(str(int(total_dmg)), True, BLACK), (table_x + 320, row_y))
            screen.blit(row_font.render(f"{(total_dmg/total_time):.1f}", True, BLACK), (table_x + 580, row_y))
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
    small_font = get_font(20)
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

                # レベルは 'Lv.' を付けず数値のみをアイコンの下にセンタリングして表示
                lvl = str(getattr(weapon, 'level', 1))
                lvl_text = small_font.render(lvl, True, WHITE)
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
                    lvl = str(getattr(inst, 'level', 1))
                    lvl_text = small_font.render(lvl, True, WHITE)
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
            s_font = get_font(18)
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
            # 画面外の大きなワールドでは重なるので小さく点で描く
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
        font = pygame.font.Font(None, 18)
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

def draw_level_choice(screen, player, icons):
    """レベルアップ（または開始時）の3択オーバーレイを描画する関数。
    main.py の描画ブロックをここに移動して再利用性を高めます。
    icons: dict mapping weapon name -> Surface
    """
    try:
        if not getattr(player, 'last_level_choices', None):
            return

        # 半透明の暗いオーバーレイ
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        choices = player.last_level_choices
        cw = min(880, SCREEN_WIDTH - 160)
        ch = 220
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)

        # ベースパネル
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((18, 18, 20, 230))
        # アクセントバー
        accent_h = 54
        accent_color = (36, 200, 185, 230)
        pygame.draw.rect(panel_surf, accent_color, (0, 0, panel_rect.width, accent_h), border_radius=12)
        # 枠線
        pygame.draw.rect(panel_surf, (10, 10, 10), (0, 0, panel_rect.width, panel_rect.height), 3, border_radius=12)

        # 光彩（簡易）
        pygame.draw.line(panel_surf, (255,255,255,28), (12, accent_h-8), (panel_rect.width-12, accent_h-8), 2)
        screen.blit(panel_surf, panel_rect.topleft)

        # タイトル
        title_font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 22)
        title_bg = title_font.render('Choose Your Reward', True, WHITE)
        screen.blit(title_bg, (panel_rect.x + 24, panel_rect.y + 10))

        # 各選択肢を描画
        option_w = (cw - 40) // max(1, len(choices))
        option_h = ch - 78
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for i, choice in enumerate(choices):
            # choice may be prefixed like 'weapon:magic_wand' or 'sub:hp'
            typ = 'weapon'
            key = choice
            if isinstance(choice, str) and ':' in choice:
                parts = choice.split(':', 1)
                if len(parts) == 2:
                    typ, key = parts[0], parts[1]

            ox = panel_rect.x + 20 + i * option_w
            oy = panel_rect.y + accent_h + 12
            rect = pygame.Rect(ox, oy, option_w - 8, option_h)

            # 背景
            pygame.draw.rect(screen, (28,28,30), rect, border_radius=10)

            # ホバー時の強調
            if rect.collidepoint((mouse_x, mouse_y)):
                hl = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                hl.fill((50, 230, 200, 28))
                screen.blit(hl, rect.topleft)
                pygame.draw.rect(screen, (36,200,185), rect, 3, border_radius=10)
            else:
                pygame.draw.rect(screen, (60,60,60), rect, 2, border_radius=10)

            # タイプバッジを左下に表示（武器 / サブ）
            try:
                # 動的幅計算: テキストに合わせて幅を決定し、オプションボックスを超えないように制限
                if typ == 'weapon':
                    badge_label = 'WEAPON'
                    badge_bg = (255,160,60)
                else:
                    badge_label = 'SUB'
                    badge_bg = (80,200,140)
                text_color = (0,0,0)
                # small_font は上部で定義済み
                try:
                    badge_surf = small_font.render(badge_label, True, text_color)
                except Exception:
                    badge_surf = pygame.font.Font(None, 18).render(badge_label, True, text_color)
                padding_x = 10
                padding_y = 6
                bw = badge_surf.get_width() + padding_x
                bh = badge_surf.get_height() + padding_y
                # オプションボックス内に収まる最大幅を計算して制限
                max_bw = max(44, rect.width - 16)
                if bw > max_bw:
                    bw = max_bw
                bh = max(bh, 16)
                # 左下に配置（左端からはみ出さないようにクランプ）
                bx = rect.x + 8
                by = rect.bottom - bh - 8
                pygame.draw.rect(screen, badge_bg, (bx, by, bw, bh), border_radius=6)
                # テキストを中央寄せ
                tx = bx + max(4, (bw - badge_surf.get_width()) // 2)
                ty = by + max(1, (bh - badge_surf.get_height()) // 2)
                screen.blit(badge_surf, (tx, ty))
            except Exception:
                pass

            # アイコン（武器ならアイコン辞書から取得、サブアイテムは汎用アイコン）
            icon_x = rect.x + 12
            icon_y = rect.y + 12
            icon_size = 32
            icon_surf = None
            try:
                # 武器・サブアイテムの両方について icons 辞書から探す
                if icons and isinstance(icons, dict):
                    icon_surf = icons.get(key)
            except Exception:
                icon_surf = None

            if icon_surf:
                try:
                    icon_draw = pygame.transform.scale(icon_surf, (icon_size, icon_size))
                    screen.blit(icon_draw, (icon_x, icon_y))
                except Exception:
                    pygame.draw.circle(screen, (120,120,120), (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2)
                    pygame.draw.circle(screen, BLACK, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2, 2)
            else:
                # サブアイテムは葉っぱアイコン的な円を表示、武器が無ければグレー四角
                if typ == 'sub':
                    pygame.draw.circle(screen, (120,200,140), (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2)
                    pygame.draw.circle(screen, BLACK, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2, 2)
                else:
                    pygame.draw.rect(screen, (120,120,120), (icon_x, icon_y, icon_size, icon_size))

            # 名前と説明
            name = key.replace('_', ' ').title()
            lbl = title_font.render(name, True, WHITE)
            screen.blit(lbl, (rect.x + 16 + 32, rect.y + 8))

            if typ == 'weapon':
                desc = 'New Weapon' if key in getattr(player, 'available_weapons', {}) else 'Upgrade'
                # レベル表示
                try:
                    w = player.weapons.get(key)
                    if w is not None:
                        level_s = small_font.render(f"Lv.{w.level}", True, (220,220,220))
                        screen.blit(level_s, (rect.x + 16 + 32, rect.y + 72))
                except Exception:
                    pass
                # 新規バッジ
                if key in getattr(player, 'available_weapons', {}):
                    # NEW バッジの幅をテキスト幅に合わせて調整（はみ出し防止）
                    try:
                        badge_text = 'NEW'
                        b_surf = small_font.render(badge_text, True, (8,8,8))
                        padding_x = 10
                        padding_y = 6
                        bw = b_surf.get_width() + padding_x
                        bh = b_surf.get_height() + padding_y
                        # オプションボックス内に収まる最大幅を計算して制限
                        max_bw = max(44, rect.width - 24)
                        if bw > max_bw:
                            bw = max_bw
                        # バッジの高さは最低限確保
                        bh = max(bh, 18)
                        # 右端に寄せるが、左にはみ出さないようにクランプ
                        bx = rect.x + rect.width - bw - 12
                        bx = max(rect.x + 8, bx)
                        by = rect.y + 10
                        pygame.draw.rect(screen, (255,200,60), (bx, by, bw, bh), border_radius=6)
                        # テキストを中央に描画（幅が狭い場合は左寄せの余白を確保）
                        tx = bx + max(4, (bw - b_surf.get_width()) // 2)
                        ty = by + max(1, (bh - b_surf.get_height()) // 2)
                        screen.blit(b_surf, (tx, ty))
                    except Exception:
                        # フォールバック: 既存の固定サイズで描画
                        try:
                            badge = small_font.render('NEW', True, (8,8,8))
                            bx = rect.x + rect.width - 60
                            by = rect.y + 10
                            pygame.draw.rect(screen, (255,200,60), (bx+4, by, 44, 20), border_radius=6)
                            screen.blit(badge, (bx + 8, by + 2))
                        except Exception:
                            pass
            else:
                # サブアイテムの説明をテンプレートから取得
                tmpl = player.subitem_templates.get(key)
                if tmpl is not None:
                    desc = f"+{tmpl.per_level}{('%' if getattr(tmpl, 'is_percent', False) else '')} per level"
                else:
                    desc = 'Subitem'
                dsurf = small_font.render(desc, True, (200,200,200))
                screen.blit(dsurf, (rect.x + 16 + 32, rect.y + 44))
                # 所持中ならレベル表示
                if key in player.subitems:
                    try:
                        lvl = player.subitems[key].level
                        screen.blit(small_font.render(f"Lv {lvl}", True, (220,220,220)), (rect.x + 16 + 32, rect.y + 72))
                    except Exception:
                        pass

    except Exception:
        # レンダリング中の例外は無視して描画を中断
        pass

def draw_subitem_choice(screen, player, icons=None):
    """サブアイテム選択 UI を描画する。player.last_subitem_choices を参照する。
    icons はオプションで渡すとサブアイテムアイコンが表示される。
    """
    try:
        if not getattr(player, 'last_subitem_choices', None):
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        screen.blit(overlay, (0,0))

        choices = player.last_subitem_choices
        cw = min(700, SCREEN_WIDTH - 200)
        ch = 180
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)

        panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel.fill((22,22,26,230))
        pygame.draw.rect(panel, (12,12,12), (0,0,panel_rect.width, panel_rect.height), 3, border_radius=10)
        screen.blit(panel, panel_rect.topleft)

        title_font = pygame.font.Font(None, 34)
        small = pygame.font.Font(None, 20)
        screen.blit(title_font.render('Choose a Subitem', True, WHITE), (panel_rect.x + 18, panel_rect.y + 10))

        option_w = (cw - 40) // max(1, len(choices))
        option_h = ch - 60
        mx, my = pygame.mouse.get_pos()
        for i, key in enumerate(choices):
            ox = panel_rect.x + 20 + i * option_w
            oy = panel_rect.y + 48
            rect = pygame.Rect(ox, oy, option_w - 8, option_h)
            pygame.draw.rect(screen, (30,30,34), rect, border_radius=8)

            if rect.collidepoint((mx,my)):
                hl = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                hl.fill((80,200,120,28))
                screen.blit(hl, rect.topleft)
                pygame.draw.rect(screen, (80,200,120), rect, 3, border_radius=8)
            else:
                pygame.draw.rect(screen, (60,60,60), rect, 2, border_radius=8)

            # タイプバッジを左下に表示
            try:
                badge_w, badge_h = 56, 18
                # 枠の左下に表示
                badge_x = rect.x + 8
                badge_y = rect.bottom - badge_h - 8
                badge_color = (80,200,140)  # sub default
                badge_label = 'SUB'
                text_color = (0,0,0)
                pygame.draw.rect(screen, badge_color, (badge_x, badge_y, badge_w, badge_h), border_radius=6)
                try:
                    blt = small.render(badge_label, True, text_color)
                    bx = badge_x + (badge_w - blt.get_width()) // 2
                    by = badge_y + (badge_h - blt.get_height()) // 2
                    screen.blit(blt, (bx, by))
                except Exception:
                    pass
            except Exception:
                pass

            # アイコン表示: icons が渡されていれば利用する
            try:
                icon_size = 28
                icon_x = rect.x + 12
                icon_y = rect.y + 12
                icon_surf = None
                if icons and isinstance(icons, dict):
                    icon_surf = icons.get(key)
                if icon_surf:
                    try:
                        icon_draw = pygame.transform.scale(icon_surf, (icon_size, icon_size))
                        screen.blit(icon_draw, (icon_x, icon_y))
                    except Exception:
                        pygame.draw.circle(screen, (120,120,120), (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2)
                        pygame.draw.circle(screen, BLACK, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2, 2)
                else:
                    pygame.draw.circle(screen, (120,200,140), (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2)
                    pygame.draw.circle(screen, BLACK, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2, 2)
            except Exception:
                pass

            name = key.replace('_',' ').title()
            screen.blit(title_font.render(name, True, WHITE), (rect.x + 12 + 36, rect.y + 8))
            # 説明はテンプレートの per_level を使って簡単に表示
            tmpl = player.subitem_templates.get(key)
            if tmpl is not None:
                desc = f"+{tmpl.per_level}{('%' if tmpl.is_percent else '')} per level"
            else:
                desc = ''
            screen.blit(small.render(desc, True, (200,200,200)), (rect.x + 12 + 36, rect.y + 40))
            # 所持状態表示
            if key in player.subitems:
                lvl = player.subitems[key].level
                screen.blit(small.render(f"Lv {lvl}", True, (220,220,220)), (rect.x + 12 + 36, rect.y + 64))

    except Exception:
        pass
