import pygame
import sys
import math
import random
import os
from constants import *
from player import Player
from enemy import Enemy
from effects.items import ExperienceGem, GameItem
from effects.particles import DeathParticle, PlayerHurtParticle, HurtFlash, LevelUpEffect, SpawnParticle, DamageNumber, AvoidanceParticle
from ui import draw_ui, draw_minimap, draw_background, draw_level_choice, draw_end_buttons, get_end_button_rects
import resources

# パーティクル関連の制限（パフォーマンス改善用）
PARTICLE_LIMIT = 300        # これ以上は古いパーティクルから切る
PARTICLE_TRIM_TO = 220      # 切るときに残す数
# 画面上に存在可能な経験値ジェムの上限
MAX_GEMS_ON_SCREEN = 200

# ランタイムで切り替え可能なデバッグフラグ（F3でトグル）
DEBUG_MODE = DEBUG


def init_game(screen):
    """ゲームの初期状態を設定する関数"""
    player = Player(screen)
    # 初期開始時は必ず「武器のみ」の3択ダイアログを表示する
    #（サブアイテム混在ではなく起動直後は武器だけを選ばせる）
    player.awaiting_subitem_choice = False
    player.last_subitem_choices = []
    try:
        pool = list(getattr(player, 'available_weapons', {}).keys())
        if pool:
            num = min(3, len(pool))
            sampled = random.sample(pool, num)
            player.last_level_choices = [f"weapon:{k}" for k in sampled]
            player.awaiting_weapon_choice = True
            try:
                player.selected_weapon_choice_index = 0
            except Exception:
                pass
        else:
            # 万が一 available_weapons が空なら従来の混合候補生成を試みる
            try:
                player.upgrade_weapons()
                if getattr(player, 'last_level_choices', None):
                    player.awaiting_weapon_choice = True
            except Exception:
                pass
    except Exception:
        # 失敗してもゲーム開始は続行
        pass
    enemies = []
    experience_gems = []
    items = []
    game_over = False
    game_clear = False
    spawn_timer = 0
    spawn_interval = 60
    game_time = 0
    last_difficulty_increase = 0
    particles = []  # パーティクルリストを追加
    # ダメージ記録: { weapon_type: total_damage }
    damage_stats = {}
    # 無敵タイマー初期化（ミリ秒タイムスタンプ）
    try:
        player.last_hit_time = -999999
    except Exception:
        pass
    return player, enemies, experience_gems, items, game_over, game_clear, spawn_timer, spawn_interval, game_time, last_difficulty_increase, particles, damage_stats

def enforce_experience_gems_limit(gems, max_gems=MAX_GEMS_ON_SCREEN, player_x=None, player_y=None):
    """上限を超えた場合、プレイヤーから遠いジェムから順に削除して
    その value を残った（近い）ジェムに加算して総EXPを維持する。
    player_x, player_yが指定されていない場合は従来通り古い順で削除。
    """
    try:
        while len(gems) > max_gems:
            if player_x is not None and player_y is not None:
                # プレイヤーから最も遠いジェムを見つける
                farthest_gem = None
                max_distance = -1
                farthest_index = 0
                
                for i, gem in enumerate(gems):
                    distance = ((gem.x - player_x) ** 2 + (gem.y - player_y) ** 2) ** 0.5
                    if distance > max_distance:
                        max_distance = distance
                        farthest_gem = gem
                        farthest_index = i
                
                # 最も遠いジェムを削除
                removed_gem = gems.pop(farthest_index)
            else:
                # プレイヤー位置が不明な場合は従来通り古い順
                removed_gem = gems.pop(0)
            
            if not gems:
                # もし残ったジェムがなければ、削除したジェムの価値を新しいまとまりとして
                # 末尾に再配置する（ほとんど発生しないが保険）
                gems.append(ExperienceGem(removed_gem.x, removed_gem.y, value=removed_gem.value))
            else:
                # プレイヤーから最も近いジェムに価値を集約
                if player_x is not None and player_y is not None:
                    closest_gem = None
                    min_distance = float('inf')
                    
                    for gem in gems:
                        distance = ((gem.x - player_x) ** 2 + (gem.y - player_y) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            closest_gem = gem
                    
                    if closest_gem:
                        closest_gem.value = getattr(closest_gem, 'value', 1) + getattr(removed_gem, 'value', 1)
                    else:
                        # 最寄りが見つからない場合は最新のジェムに集約
                        gems[-1].value = getattr(gems[-1], 'value', 1) + getattr(removed_gem, 'value', 1)
                else:
                    # プレイヤー位置が不明な場合は従来通り最新のジェムに集約
                    gems[-1].value = getattr(gems[-1], 'value', 1) + getattr(removed_gem, 'value', 1)
    except Exception:
        # 失敗してもゲームは続行
        pass

def main():
    global DEBUG_MODE
    # 初期化
    pygame.init()
    # ディスプレイ情報取得（フルスクリーン切替に使用）
    try:
        display_info = pygame.display.Info()
    except Exception:
        display_info = None

    # ウィンドウサイズ（通常モード）
    windowed_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    # フルスクリーンフラグ（ウィンドウフルスクリーンタイプのトグルに使用）
    is_fullscreen = False

    # 初期はウィンドウモードで開始
    screen = pygame.display.set_mode(windowed_size)
    pygame.display.set_caption("Van Survivor Clone")

    # リソースをプリロード（アイコン・フォント・サウンド等）
    preload_res = resources.preload_all(icon_size=16)
    ICONS = preload_res.get('icons', {})

    clock = pygame.time.Clock()
    # 画面右下に小さなプレイヤーステータスを表示するかどうかのフラグ（F4でトグル）
    show_status = True
    # 攻撃範囲の可視化フラグ（F5でトグル）
    show_hitboxes = False
    try:
        debug_font = pygame.font.SysFont(None, 14)
    except Exception:
        debug_font = None

    # カメラ初期値とスムージング係数（0.0: 固定、1.0: 即時追従）
    camera_x = 0.0
    camera_y = 0.0
    CAMERA_LERP = 0.18

    # ゲーム状態の初期化
    player, enemies, experience_gems, items, game_over, game_clear, spawn_timer, spawn_interval, game_time, last_difficulty_increase, particles, damage_stats = init_game(screen)

    # デバッグ: 初期状態の選択フラグ確認
    try:
        print(f"[DEBUG] initial awaiting_weapon_choice={getattr(player,'awaiting_weapon_choice', False)} last_level_choices={getattr(player,'last_level_choices', [])}")
    except Exception:
        pass

    # メインゲームループ
    running = True
    print("[INFO] Entering main loop")
    while running:
        try:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    # デバッグログのオン/オフ切り替え（F3）
                    if event.key == pygame.K_F3:
                        DEBUG_MODE = not DEBUG_MODE
                        # 他モジュールで直接 DEBUG を参照している箇所があるため、読み込まれているモジュール内の DEBUG 変数を一括更新する
                        try:
                            for m in list(sys.modules.values()):
                                try:
                                    setattr(m, 'DEBUG', DEBUG_MODE)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        print(f"[INFO] DEBUG_MODE set to {DEBUG_MODE}")
                        continue

                    # プレイヤーステータス表示のオン/オフ切り替え（F4）
                    if event.key == pygame.K_F4:
                        show_status = not show_status
                        print(f"[INFO] show_status set to {show_status}")
                        continue

                    # 攻撃範囲表示のトグル（F5）
                    if event.key == pygame.K_F5:
                        show_hitboxes = not show_hitboxes
                        print(f"[INFO] show_hitboxes set to {show_hitboxes}")
                        continue

                    # フルスクリーン切替（F11） -- 元の変更を取り消して一旦無効化
                    if event.key == pygame.K_F11:
                        # フルスクリーン系の変更は一旦戻しました。必要なら再度実装してください。
                        try:
                            print("[INFO] F11 fullscreen toggle is disabled (reverted).")
                        except Exception:
                            pass
                        continue

                    # 武器/サブアイテム選択のキー処理は下側の統合ブロックで処理する
                    # （ここで処理: 1押下=1移動に変更）
                    try:
                        if getattr(player, 'awaiting_weapon_choice', False) and getattr(player, 'last_level_choices', None):
                            n = len(player.last_level_choices)
                            if n > 0:
                                if event.key in (pygame.K_LEFT, pygame.K_a):
                                    player.selected_weapon_choice_index = (player.selected_weapon_choice_index - 1) % n
                                    try:
                                        particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                    player.selected_weapon_choice_index = (player.selected_weapon_choice_index + 1) % n
                                    try:
                                        particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                    idx = max(0, min(player.selected_weapon_choice_index, n - 1))
                                    choice = player.last_level_choices[idx]
                                    player.apply_level_choice(choice)
                                    try:
                                        for _ in range(8):
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                        elif getattr(player, 'awaiting_subitem_choice', False) and getattr(player, 'last_subitem_choices', None):
                            n = len(player.last_subitem_choices)
                            if n > 0:
                                if event.key in (pygame.K_LEFT, pygame.K_a):
                                    player.selected_subitem_choice_index = (player.selected_subitem_choice_index - 1) % n
                                    try:
                                        particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                    player.selected_subitem_choice_index = (player.selected_subitem_choice_index + 1) % n
                                    try:
                                        particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                    idx = max(0, min(player.selected_subitem_choice_index, n - 1))
                                    key = player.last_subitem_choices[idx]
                                    player.apply_subitem_choice(key)
                                    try:
                                        for _ in range(8):
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                    except Exception:
                        pass

                    if event.key == pygame.K_RETURN and (game_over or game_clear):
                        # ゲームクリア後は（規定時間生存）プレイヤー状態を保持して続行する
                        if game_clear:
                            print("[INFO] Survived required time - continuing without resetting player/weapons.")
                            enemies = []
                            experience_gems = []
                            items = []
                            particles = []
                            spawn_timer = 0
                            spawn_interval = 60
                            game_time = 0
                            last_difficulty_increase = 0
                            game_clear = False
                        else:
                            # 通常のリスタート（全て再初期化）
                            player, enemies, experience_gems, items, game_over, game_clear, spawn_timer, spawn_interval, game_time, last_difficulty_increase, particles, damage_stats = init_game(screen)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # マウスで選択可能ならクリック位置を判定
                    if getattr(player, 'awaiting_weapon_choice', False) and event.button == 1:
                        mx, my = event.pos
                        # レイアウトを再現して当たり判定
                        choices = getattr(player, 'last_level_choices', [])
                        if choices:
                            # 中央パネルに3分割で表示するレイアウト
                            cw = min(880, SCREEN_WIDTH - 160)
                            ch = 180
                            cx = SCREEN_WIDTH // 2
                            cy = SCREEN_HEIGHT // 2
                            panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
                            option_w = (cw - 40) // len(choices)
                            option_h = ch - 60
                            hit = False
                            for i, choice in enumerate(choices):
                                ox = panel_rect.x + 20 + i * option_w
                                oy = panel_rect.y + 40
                                rect = pygame.Rect(ox, oy, option_w - 8, option_h)
                                if rect.collidepoint(mx, my):
                                    player.apply_level_choice(choice)
                                    try:
                                        for _ in range(8):
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    hit = True
                                    break
                            if hit:
                                continue
                    # サブアイテム選択のマウスクリック判定
                    if getattr(player, 'awaiting_subitem_choice', False) and event.button == 1:
                        mx, my = event.pos
                        choices = getattr(player, 'last_subitem_choices', [])
                        if choices:
                            cw = min(700, SCREEN_WIDTH - 200)
                            ch = 180
                            cx = SCREEN_WIDTH // 2
                            cy = SCREEN_HEIGHT // 2
                            panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
                            option_w = (cw - 40) // len(choices)
                            option_h = ch - 60
                            hit = False
                            for i, key in enumerate(choices):
                                ox = panel_rect.x + 20 + i * option_w
                                oy = panel_rect.y + 48
                                rect = pygame.Rect(ox, oy, option_w - 8, option_h)
                                if rect.collidepoint(mx, my):
                                    player.apply_subitem_choice(key)
                                    try:
                                        for _ in range(8):
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    hit = True
                                    break
                            if hit:
                                continue

                    # エンド画面のボタン処理（GAME OVER / CLEAR）
                    if (game_over or game_clear) and event.button == 1:
                        mx, my = event.pos
                        try:
                            rects = get_end_button_rects()
                            # Continue はゲームオーバー時のみ有効
                            if game_over and rects.get('continue') and rects['continue'].collidepoint(mx, my):
                                try:
                                    player.hp = player.get_max_hp()
                                except Exception:
                                    player.hp = getattr(player, 'max_hp', 100)
                                game_over = False
                                for _ in range(8):
                                    particles.append(DeathParticle(player.x, player.y, CYAN))
                                continue
                            # GAME CLEAR の Continue: 残り時間を規定値に戻して続行
                            if game_clear and rects.get('continue') and rects['continue'].collidepoint(mx, my):
                                try:
                                    # reset game_time to 0 on continue from game clear
                                    game_time = 0
                                except Exception:
                                    game_time = 0
                                game_clear = False
                                # 画面エフェクト
                                for _ in range(8):
                                    particles.append(DeathParticle(player.x, player.y, CYAN))
                                continue
                            # Restart
                            if rects.get('restart') and rects['restart'].collidepoint(mx, my):
                                player, enemies, experience_gems, items, game_over, game_clear, spawn_timer, spawn_interval, game_time, last_difficulty_increase, particles, damage_stats = init_game(screen)
                                continue
                        except Exception:
                            pass

            # キーボードでのレベルアップ選択処理は KEYDOWN イベントで単発処理に変更済み

            # ループ冒頭でプレイヤー位置からターゲットカメラを算出（まだスムーズは適用しない）
            target_cam_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, int(player.x - SCREEN_WIDTH // 2)))
            target_cam_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, int(player.y - SCREEN_HEIGHT // 2)))

            # ゲームの更新処理。武器/サブアイテム選択UIが開いている間はゲームを一時停止する
            # UI が表示されてゲームを停止すべきかを判定する。
            # フラグだけでなく、実際に候補リストが存在するかもチェックする（フラグが残留していると攻撃できなくなる不具合対策）。
            awaiting_weapon_active = bool(getattr(player, 'awaiting_weapon_choice', False) and getattr(player, 'last_level_choices', None))
            awaiting_subitem_active = bool(getattr(player, 'awaiting_subitem_choice', False) and getattr(player, 'last_subitem_choices', None))
            if not game_over and not game_clear and not (awaiting_weapon_active or awaiting_subitem_active):
                # プレイヤーの移動（現在のカメラ位置を渡してマウス座標をワールド座標に変換）
                player.move(int(camera_x), int(camera_y))

                # 自動攻撃の更新
                player.update_attacks(enemies, camera_x=int(camera_x), camera_y=int(camera_y))

                # 自然回復（HPサブアイテム所持時のみ、5秒で1回復）
                try:
                    player.update_regen()
                except Exception:
                    pass

                # 攻撃と敵の当たり判定
                for attack in player.active_attacks[:]:
                    # spawn_delay によってまだ発生していない攻撃は無視する
                    if getattr(attack, '_pending', False):
                        continue
                    for enemy in enemies[:]:
                        # sqrt を避けて二乗距離で比較（高速化）
                        dx = enemy.x - attack.x
                        dy = enemy.y - attack.y
                        r = (getattr(attack, 'size', 0) + getattr(enemy, 'size', 0))
                        if dx*dx + dy*dy < (r * r):
                            # 持続系攻撃は0.2秒ごとにダメージ再発生
                            persistent_types = {"garlic", "holy_water"}
                            is_persistent = getattr(attack, 'type', '') in persistent_types

                            # attack に必要な構造を初期化（動的に追加）
                            if not hasattr(attack, 'hit_targets'):
                                attack.hit_targets = set()
                            if not hasattr(attack, 'last_hit_times'):
                                attack.last_hit_times = {}

                            # 非持続系は一度ヒットしたら再ヒットさせない
                            if not is_persistent:
                                if id(enemy) in attack.hit_targets:
                                    continue
                            else:
                                # 持続系は最後にダメージを与えた時刻から0.2秒以上経過していれば再ダメージ
                                last = attack.last_hit_times.get(id(enemy), -999)
                                if game_time - last < 0.2:
                                    continue

                            # 攻撃のダメージを適用
                            dmg = getattr(attack, 'damage', 0) or 0
                            try:
                                dmg = float(dmg)
                            except Exception:
                                dmg = 0.0
                            # ダメージにランダム性を追加（±10%の範囲）
                            variance = random.uniform(-0.1, 0.1)
                            dmg = max(0.0, dmg * (1.0 + variance))
                            hp_before = enemy.hp
                            enemy.hp -= dmg
                            # デバッグ出力（DEBUG フラグが有効な場合）
                            if DEBUG_MODE:
                                print(f"[DEBUG] attack_type={getattr(attack,'type','?')} damage={dmg} enemy_type={getattr(enemy,'enemy_type','?')} hp: {hp_before} -> {enemy.hp}")

                            # ヒット時の記録: 非持続系は hit_targets に追加、持続系は last_hit_times を更新
                            if is_persistent:
                                attack.last_hit_times[id(enemy)] = game_time
                            else:
                                attack.hit_targets.add(id(enemy))

                            # ダメージ集計: 武器(type)ごとに合計ダメージを記録
                            try:
                                atk_type = getattr(attack, 'type', 'unknown') or 'unknown'
                                damage_stats[atk_type] = damage_stats.get(atk_type, 0) + dmg
                            except Exception:
                                pass

                            # Garlic がヒットしたらプレイヤーを1回復する（クールダウン: 500ms）
                            try:
                                if getattr(attack, 'type', '') == 'garlic':
                                    now = pygame.time.get_ticks()
                                    # attack にクールダウン時刻を保持
                                    if not hasattr(attack, 'last_garlic_heal_time'):
                                        attack.last_garlic_heal_time = -999999
                                    COOLDOWN_MS = 500
                                    if now - attack.last_garlic_heal_time >= COOLDOWN_MS:
                                        try:
                                            prev_hp = int(getattr(player, 'hp', 0))
                                            # ここはハードコードの100ではなくプレイヤーの最大HPを使う
                                            new_hp = min(player.get_max_hp(), prev_hp + 1)
                                            healed = new_hp - prev_hp
                                            if healed > 0:
                                                player.hp = new_hp
                                                # プレイヤー上に緑色で回復量を表示
                                                particles.append(DamageNumber(player.x, player.y - getattr(player, 'size', 32) - 6, f"+{int(healed)}", color=GREEN))
                                        except Exception:
                                            # 万が一何か問題があってもHPは最低限設定
                                            try:
                                                player.hp = min(player.get_max_hp(), getattr(player, 'hp', 0) + 1)
                                            except Exception:
                                                # 最終フォールバック
                                                player.hp = min(100, getattr(player, 'hp', 0) + 1)
                                        attack.last_garlic_heal_time = now
                            except Exception:
                                pass

                            # ヒット時の小エフェクト
                            try:
                                if hasattr(enemy, 'on_hit') and callable(enemy.on_hit):
                                    enemy.on_hit()
                            except Exception:
                                pass

                            for _ in range(4):
                                particles.append(DeathParticle(enemy.x, enemy.y, enemy.color))

                            # ダメージ数表示を追加（敵の上部に素早くフェードイン・アウト）
                            try:
                                dval = float(dmg)
                                if dval <= 10.0:
                                    color = WHITE
                                else:
                                    t = min(1.0, max(0.0, (dval - 10.0) / 40.0))
                                    r = 255
                                    g = int(255 - (215 * t))
                                    b = int(255 - (215 * t))
                                    color = (r, g, b)
                                particles.append(DamageNumber(enemy.x, enemy.y - enemy.size - 6, int(dmg), color=color))
                            except Exception:
                                pass

                            # 敵のHPが0以下なら死亡処理
                            if enemy.hp <= 0:
                                for _ in range(8):
                                    particles.append(DeathParticle(enemy.x, enemy.y, enemy.color))

                                rand = random.random()
                                if rand < HEAL_ITEM_DROP_RATE:
                                    items.append(GameItem(enemy.x, enemy.y, "heal"))
                                elif rand < BOMB_ITEM_DROP_RATE:
                                    items.append(GameItem(enemy.x, enemy.y, "bomb"))
                                else:
                                    experience_gems.append(ExperienceGem(enemy.x, enemy.y))
                                    enforce_experience_gems_limit(experience_gems, player_x=player.x, player_y=player.y)

                                if enemy in enemies:
                                    enemies.remove(enemy)

                            # ヒット時に消費する攻撃（弾丸系など）のみ削除する
                            consumable_on_hit = {"magic_wand"}
                            if getattr(attack, 'type', '') in consumable_on_hit:
                                if attack in player.active_attacks:
                                    player.active_attacks.remove(attack)

                            # stone は貫通させるため、貫通攻撃の一覧を定義
                            penetrating_types = {"stone"}
                            if getattr(attack, 'type', '') not in penetrating_types:
                                break

                # ゲーム時間の更新（60FPSを想定）
                game_time += 1/60

                # クリア判定
                if game_time >= SURVIVAL_TIME:
                    game_clear = True

                # 15秒ごとに難易度アップ（間隔を短縮）
                if game_time - last_difficulty_increase >= 15:
                    spawn_interval = max(10, spawn_interval - 5)
                    last_difficulty_increase = game_time

                # 敵の生成を爆発的に
                spawn_timer += 1
                if spawn_timer >= spawn_interval:
                    if game_time <= 30:
                        num_enemies = 1 + int(game_time // 10)
                    else:
                        base_enemies = 1 + int((game_time - 30) // 20)
                        num_enemies = base_enemies + int((game_time ** 1.2) / 15)

                    if game_time > SURVIVAL_TIME * 0.7:
                        num_enemies = int(num_enemies * 1.3)

                    num_enemies = min(num_enemies, 12)

                    for _ in range(num_enemies):
                        cam_vx = int(camera_x)
                        cam_vy = int(camera_y)
                        margin = 32
                        side = random.randint(0, 3)
                        if side == 0:
                            sx = random.randint(cam_vx - margin, cam_vx + SCREEN_WIDTH + margin)
                            sy = cam_vy - margin
                        elif side == 1:
                            sx = cam_vx + SCREEN_WIDTH + margin
                            sy = random.randint(cam_vy - margin, cam_vy + SCREEN_HEIGHT + margin)
                        elif side == 2:
                            sx = random.randint(cam_vx - margin, cam_vx + SCREEN_WIDTH + margin)
                            sy = cam_vy + SCREEN_HEIGHT + margin
                        else:
                            sx = cam_vx - margin
                            sy = random.randint(cam_vy - margin, cam_vy + SCREEN_HEIGHT + margin)

                        sx = max(-margin, min(WORLD_WIDTH + margin, sx))
                        sy = max(-margin, min(WORLD_HEIGHT + margin, sy))

                        enemy = Enemy(screen, game_time, spawn_x=sx, spawn_y=sy, spawn_side=side)
                        enemies.append(enemy)
                        particles.append(SpawnParticle(enemy.x, enemy.y, enemy.color))
                    spawn_timer = 0

                for enemy in enemies[:]:
                    enemy.move(player)
                    # プレイヤーとの当たり判定も二乗距離で比較
                    dx = player.x - enemy.x
                    dy = player.y - enemy.y
                    r = (getattr(player, 'size', 0) + getattr(enemy, 'size', 0))
                    if dx*dx + dy*dy < (r * r):
                        if random.random() < player.get_avoidance():
                            # サブアイテムスピードアップ効果で攻撃を回避
                            particles.append(AvoidanceParticle(player.x, player.y))
                            try:
                                from effects.particles import LuckyText
                                particles.append(LuckyText(player.x, player.y - getattr(player, 'size', 32) - 6, "Lukey!", color=CYAN))
                            except Exception:
                                pass
                        else:
                            # 無敵時間チェック
                            now_ms = pygame.time.get_ticks()
                            last_hit = getattr(player, 'last_hit_time', -999999)
                            if now_ms - last_hit >= INVINCIBLE_MS:
                                particles.append(HurtFlash(player.x, player.y, size=player.size))

                                # サブアイテムアーマーの効果でダメージを軽減
                                try:
                                    player.hp -= max(1, int(enemy.damage - player.get_defense()))
                                except Exception:
                                    player.hp -= enemy.damage

                                # 被弾時刻を更新
                                try:
                                    player.last_hit_time = now_ms
                                except Exception:
                                    pass

                                # この敵は処理済み
                                enemies.remove(enemy)
                                if player.hp <= 0:
                                    game_over = True
                            else:
                                # 無敵中はノーダメージ、敵だけ消す（多段ヒット防止）
                                try:
                                    enemies.remove(enemy)
                                except Exception:
                                    pass

                for gem in experience_gems[:]:
                    gem.move_to_player(player)
                    # 経験値ジェムの取得判定も二乗距離で比較
                    dx = player.x - gem.x
                    dy = player.y - gem.y
                    # プレイヤーの基準取得半径は player.size + gem.size
                    base_r = (getattr(player, 'size', 0) + getattr(gem, 'size', 0))
                    # サブアイテムから追加されるピクセル半径を取得
                    try:
                        extra = float(getattr(player, 'get_gem_pickup_range', lambda: 0.0)())
                    except Exception:
                        extra = 0.0
                    r = base_r + extra
                    if dx*dx + dy*dy < (r * r):
                        prev_level = player.level
                        # ジェムごとの価値を付与
                        player.add_exp(getattr(gem, 'value', 1))
                        experience_gems.remove(gem)
                        if player.level > prev_level:
                            particles.append(LevelUpEffect(player.x, player.y))
                            for _ in range(12):
                                particles.append(DeathParticle(player.x, player.y, CYAN))

                for item in items[:]:
                    item.move_to_player(player)
                    # アイテム取得判定も二乗距離比較に変更
                    dx = player.x - item.x
                    dy = player.y - item.y
                    r = (getattr(player, 'size', 0) + getattr(item, 'size', 0))
                    if dx*dx + dy*dy < (r * r):
                        if item.type == "heal":
                            try:
                                prev_hp = int(getattr(player, 'hp', 0))
                                # 最大HPの30%を回復（最低1）
                                heal_amount = max(1, int(player.get_max_hp() * 0.3))
                                new_hp = min(player.get_max_hp(), prev_hp + heal_amount)
                                healed = new_hp - prev_hp
                                if healed > 0:
                                    player.hp = new_hp
                                    particles.append(DamageNumber(player.x, player.y - getattr(player, 'size', 32) - 6, f"+{int(healed)}", color=GREEN))
                            except Exception:
                                try:
                                    try:
                                        max_hp = player.get_max_hp()
                                    except Exception:
                                        max_hp = 100
                                    heal_amount = max(1, int(max_hp * 0.3))
                                    player.hp = min(max_hp, getattr(player, 'hp', 0) + heal_amount)
                                except Exception:
                                    player.hp = min(100, getattr(player, 'hp', 0) + 30)
                        elif item.type == "bomb":
                            for enemy in enemies[:]:
                                experience_gems.append(ExperienceGem(enemy.x, enemy.y))
                                # 各追加ごとに上限をチェックしてプレイヤーから遠いものを削除しつつ価値を集約
                                enforce_experience_gems_limit(experience_gems, player_x=player.x, player_y=player.y)
                            enemies.clear()
                        items.remove(item)

            # パーティクルの更新と描画
            # パーティクルはカメラに依存しないため従来通り呼び出す
            # パーティクル数が多すぎる場合は古いものから削減して負荷を抑える
            if len(particles) > PARTICLE_LIMIT:
                # 最も新しいものを残す（古いものは削除）
                particles = particles[-PARTICLE_TRIM_TO:]

            # 安全に順次更新して生存するものだけ残す
            new_particles = []
            for p in particles:
                try:
                    if p.update():
                        new_particles.append(p)
                except Exception:
                    # エフェクトの update で例外が出てもゲームを継続する
                    pass
            particles = new_particles

            # カメラ目標を現在のプレイヤー位置から再計算（プレイヤー移動後）
            desired_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, player.x - SCREEN_WIDTH // 2))
            desired_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, player.y - SCREEN_HEIGHT // 2))
            # 補間（スムージング）
            camera_x += (desired_x - camera_x) * CAMERA_LERP
            camera_y += (desired_y - camera_y) * CAMERA_LERP
            # 描画で使用する整数カメラ座標
            int_cam_x = int(camera_x)
            int_cam_y = int(camera_y)

            # ワールド用サーフェスに描画してからスクリーンにブリットする
            world_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

            # 背景をワールド全体のタイルで描画（オフセット適用）
            draw_background(world_surf, int_cam_x, int_cam_y)
            
            # 敵の描画（プレイヤーより背後に表示）
            for enemy in enemies:
                enemy.draw(world_surf, int_cam_x, int_cam_y)

            # パーティクル（ワールド座標）の描画（エネミーの後、攻撃エフェクトの前に追加）
            # HurtFlash, LevelUpEffect は画面オーバーレイなので別途画面に描画する
            world_particles = [p for p in particles if not isinstance(p, (HurtFlash, LevelUpEffect))]
            overlay_particles = [p for p in particles if isinstance(p, (HurtFlash, LevelUpEffect))]
            for particle in world_particles:
                # 各パーティクルは world_surf 上に描画する（カメラオフセットを渡す）
                try:
                    particle.draw(world_surf, int_cam_x, int_cam_y)
                except TypeError:
                    # 古いインターフェースのままなら位置をオフセットして描画
                    particle.draw(world_surf)

            # 経験値ジェムの描画
            for gem in experience_gems:
                gem.draw(world_surf, int_cam_x, int_cam_y)

            # アイテムの描画
            for item in items:
                item.draw(world_surf, int_cam_x, int_cam_y)

            # まず武器のエフェクトを描画（プレイヤーより後ろに表示されるべきなので先に描く）
            player.draw_attacks(world_surf, int_cam_x, int_cam_y)

            # プレイヤー本体は武器エフェクトより手前に表示する
            player.draw(world_surf, int_cam_x, int_cam_y)

            # デバッグ: 攻撃範囲の可視化（world_surf に描画）
            if show_hitboxes:
                try:
                    # 攻撃エフェクトの範囲を例示
                    for atk in player.active_attacks:
                        try:
                            ax = int(atk.x - int_cam_x)
                            ay = int(atk.y - int_cam_y)
                            w = int(getattr(atk, 'size_x', getattr(atk, 'size', 16) * 2))
                            h = int(getattr(atk, 'size_y', getattr(atk, 'size', 16) * 2))
                            tx = ax - w // 2
                            ty = ay - h // 2
                            s = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
                            s.fill((255, 255, 0, 40))
                            try:
                                pygame.draw.rect(s, (255, 200, 0, 180), (0, 0, w, h), 2)
                            except Exception:
                                pass
                            world_surf.blit(s, (tx, ty))
                            if debug_font:
                                t = str(getattr(atk, 'type', '?'))
                                try:
                                    txt = debug_font.render(t, True, (220, 220, 60))
                                    world_surf.blit(txt, (ax + 6, ay - 6))
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    # 敵の当たり判定も表示
                    for e in enemies:
                        try:
                            ex = int(e.x - int_cam_x)
                            ey = int(e.y - int_cam_y)
                            rs = int(getattr(e, 'size', 12))
                            try:
                                pygame.draw.circle(world_surf, (255, 80, 80, 160), (ex, ey), rs, 2)
                            except Exception:
                                pygame.draw.circle(world_surf, (255, 80, 80), (ex, ey), rs, 2)
                        except Exception:
                            pass
                except Exception:
                    pass

            # ワールドをスクリーンにブリット
            screen.blit(world_surf, (0, 0))

            # オーバーレイ系パーティクルを画面に直接描画（全画面フラッシュ等）
            for particle in overlay_particles:
                # overlay パーティクルはワールド座標を保持しているためカメラオフセットを渡す
                try:
                    particle.draw(screen, int_cam_x, int_cam_y)
                except TypeError:
                    particle.draw(screen)

            # 右上にミニマップを描画
            try:
                draw_minimap(screen, player, enemies, experience_gems, items, int_cam_x, int_cam_y)
            except Exception:
                pass

            # デバッグ: ゲーム終了時に damage_stats の中身をログ出力 (表が出ない原因調査用)
            try:
                if (game_over or game_clear) and DEBUG_MODE:
                    if not damage_stats:
                        print("[DEBUG] damage_stats is empty at game end")
                    else:
                        print(f"[DEBUG] damage_stats keys={list(damage_stats.items())[:8]}")
            except Exception:
                pass
            # UI描画を修正（プレイヤーステータス表示のON/OFFを渡す）
            draw_ui(screen, player, game_time, game_over, game_clear, damage_stats, ICONS, show_status=show_status)
            # エンド画面のボタンを描画（描画だけでクリックはイベントハンドラで処理）
            if game_over or game_clear:
                from ui import draw_end_buttons
                draw_end_buttons(screen, game_over, game_clear)
            
            # レベルアップ候補がある場合はポップアップを ui.draw_level_choice に任せる
            # サブアイテム選択 UI を優先して表示
            if getattr(player, 'awaiting_subitem_choice', False) and getattr(player, 'last_subitem_choices', None):
                # サブアイテム選択は ui.draw_subitem_choice を使う
                from ui import draw_subitem_choice
                draw_subitem_choice(screen, player, ICONS)
            elif getattr(player, 'awaiting_weapon_choice', False) and getattr(player, 'last_level_choices', None):
                draw_level_choice(screen, player, ICONS)

            pygame.display.flip()
            clock.tick(FPS)

        except Exception as e:
            # 例外が発生したら詳細をログ出力してループを抜ける
            import traceback
            print("[ERROR] Exception in main loop:", e)
            traceback.print_exc()
            running = False

    print("[INFO] Exited main loop")
    pygame.quit()

if __name__ == "__main__":
    main()
    sys.exit(0)