"""
ゲーム用ユーティリティ関数群
主にmain.pyから切り出した汎用的な処理を管理
"""

import random
from constants import MAX_GEMS_ON_SCREEN
from effects.items import ExperienceGem


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


def init_game_state(screen, save_system=None):
    """ゲームの初期状態を設定する関数"""
    from player import Player
    
    player = Player(screen)
    # セーブシステムへの参照を設定
    if save_system:
        player.save_system = save_system
    # 初期武器選択：すべての武器を3x3グリッドで表示
    player.awaiting_subitem_choice = False
    player.last_subitem_choices = []
    
    try:
        # すべての利用可能な武器を取得（最大9個）
        all_weapons = list(getattr(player, 'available_weapons', {}).keys())
        if all_weapons:
            # 武器を9個に制限（3x3グリッド用）
            selected_weapons = all_weapons[:9]
            player.last_level_choices = [f"weapon:{k}" for k in selected_weapons]
            player.awaiting_weapon_choice = True
            player.is_initial_weapon_selection = True  # 初期武器選択フラグ
            player.selected_weapon_choice_index = 0
        else:
            # 万が一 available_weapons が空なら従来の混合候補生成を試みる
            try:
                player.upgrade_weapons()
                if getattr(player, 'last_level_choices', None):
                    player.awaiting_weapon_choice = True
                    player.is_initial_weapon_selection = False
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


def clamp_to_world(x, y, world_width, world_height, margin=50):
    """座標をワールド境界内にクランプする"""
    x = max(margin, min(world_width - margin, x))
    y = max(margin, min(world_height - margin, y))
    return x, y


def calculate_distance(x1, y1, x2, y2):
    """2点間の距離を計算"""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def is_point_in_rect(point_x, point_y, rect_x, rect_y, rect_width, rect_height):
    """点が矩形内にあるかチェック"""
    return (rect_x <= point_x <= rect_x + rect_width and 
            rect_y <= point_y <= rect_y + rect_height)


def limit_particles(particles, max_particles=300, trim_to=220):
    """パーティクル数を制限して古いものから削除"""
    if len(particles) > max_particles:
        particles[:] = particles[-trim_to:]
