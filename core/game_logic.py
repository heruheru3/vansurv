"""
ゲームロジック処理
敵の生成、アイテムドロップ、レベルアップ処理などを管理
"""

import random
import pygame
from constants import *
from core.enemy import Enemy
from effects.items import ExperienceGem, GameItem
from effects.particles import DeathParticle, SpawnParticle
from core.game_utils import enforce_experience_gems_limit


def spawn_enemies(enemies, particles, game_time, spawn_timer, spawn_interval, 
                 player_x, player_y, camera_x, camera_y, boss_spawn_timer=0, stage=None):
    """敵の生成処理"""
    new_spawn_timer = spawn_timer + 1
    new_boss_spawn_timer = boss_spawn_timer + 1
    
    # ボス出現チェック（1分=3600フレーム間隔）
    boss_spawn_interval = 3600  # 60秒 * 60FPS
    if new_boss_spawn_timer >= boss_spawn_interval and game_time >= 60:
        new_boss_spawn_timer = 0
        
        # ボスを画面中央付近にスポーン
        boss_x = camera_x + SCREEN_WIDTH // 2 + random.randint(-100, 100)
        boss_y = camera_y + SCREEN_HEIGHT // 2 + random.randint(-100, 100)
        
        # ワールド境界をクランプ
        boss_x = max(100, min(WORLD_WIDTH - 100, boss_x))
        boss_y = max(100, min(WORLD_HEIGHT - 100, boss_y))
        
        # ステージが利用可能な場合、安全な位置を探す
        if stage:
            boss_x, boss_y = stage.find_safe_spawn_position(boss_x, boss_y, 50)
        
        # ボス生成
        boss = Enemy(None, game_time, spawn_x=boss_x, spawn_y=boss_y, is_boss=True)
        enemies.append(boss)
        
        # ボススポーンエフェクト（大きめ）
        if len(particles) < 300:
            for _ in range(15):  # 通常より多めのエフェクト
                particles.append(SpawnParticle(boss_x, boss_y, size=3))
    
    # 通常の敵スポーン処理
    if new_spawn_timer >= spawn_interval:
        new_spawn_timer = 0
        
        # 敵の生成数を時間に応じて増加
        num_enemies = 1
        if game_time > 60:  # 1分後から2体ずつ
            num_enemies = 2
        if game_time > 120:  # 2分後から3体ずつ
            num_enemies = 3
            
        for _ in range(num_enemies):
            # カメラ外の位置に敵を生成
            spawn_margin = 100
            side = random.choice(['top', 'bottom', 'left', 'right'])
            
            if side == 'top':
                x = random.randint(int(camera_x) - spawn_margin, 
                                 int(camera_x) + SCREEN_WIDTH + spawn_margin)
                y = int(camera_y) - spawn_margin
            elif side == 'bottom':
                x = random.randint(int(camera_x) - spawn_margin, 
                                 int(camera_x) + SCREEN_WIDTH + spawn_margin)
                y = int(camera_y) + SCREEN_HEIGHT + spawn_margin
            elif side == 'left':
                x = int(camera_x) - spawn_margin
                y = random.randint(int(camera_y) - spawn_margin, 
                                 int(camera_y) + SCREEN_HEIGHT + spawn_margin)
            else:  # right
                x = int(camera_x) + SCREEN_WIDTH + spawn_margin
                y = random.randint(int(camera_y) - spawn_margin, 
                                 int(camera_y) + SCREEN_HEIGHT + spawn_margin)
            
            # ワールド境界をクランプ
            x = max(50, min(WORLD_WIDTH - 50, x))
            y = max(50, min(WORLD_HEIGHT - 50, y))
            
            # ステージが利用可能な場合、安全な位置を探す
            if stage:
                x, y = stage.find_safe_spawn_position(x, y, 32)
            
            enemy = Enemy(None, game_time, spawn_x=x, spawn_y=y)
            enemies.append(enemy)
            
            # スポーンエフェクト
            if len(particles) < 300:  # パーティクル制限
                particles.append(SpawnParticle(x, y))
    
    return new_spawn_timer, new_boss_spawn_timer


def handle_enemy_death(enemy, enemies, experience_gems, items, particles, damage_stats, 
                      player_x, player_y, player=None):
    """敵死亡時の処理"""
    if enemy.hp <= 0:
        # 死亡エフェクト
        for _ in range(8):
            particles.append(DeathParticle(enemy.x, enemy.y, enemy.color))
        
        # アイテムドロップ判定
        rand = random.random()
        if rand < HEAL_ITEM_DROP_RATE:
            items.append(GameItem(enemy.x, enemy.y, "heal"))
            try:
                from core.audio import audio
                audio.play_sound('item_drop')
            except Exception:
                pass
        elif rand < HEAL_ITEM_DROP_RATE + BOMB_ITEM_DROP_RATE:
            items.append(GameItem(enemy.x, enemy.y, "bomb"))
        elif rand < HEAL_ITEM_DROP_RATE + BOMB_ITEM_DROP_RATE + (player.get_magnet_drop_rate() if player else MAGNET_ITEM_DROP_RATE):
            items.append(GameItem(enemy.x, enemy.y, "magnet"))
        else:
            experience_gems.append(ExperienceGem(enemy.x, enemy.y))
            enforce_experience_gems_limit(experience_gems, player_x=player_x, player_y=player_y)
        
        # 敵を削除
        if enemy in enemies:
            enemies.remove(enemy)
        
        return True
    return False


def handle_bomb_item_effect(enemies, experience_gems, particles, player_x, player_y, player=None):
    """ボムアイテム使用時の処理"""
    # 画面揺れエフェクトを発生させる
    if player and hasattr(player, 'activate_screen_shake'):
        player.activate_screen_shake()
    
    # 全敵に100ダメージを与える
    bomb_damage = 100
    enemies_to_remove = []
    
    for enemy in enemies:
        enemy.hp -= bomb_damage
        
        # HPが0以下になった敵を処理
        if enemy.hp <= 0:
            # 経験値ジェムを生成
            experience_gems.append(ExperienceGem(enemy.x, enemy.y))
            # 各追加ごとに上限をチェックしてプレイヤーから遠いものを削除しつつ価値を集約
            enforce_experience_gems_limit(experience_gems, player_x=player_x, player_y=player_y)
            enemies_to_remove.append(enemy)
    
    # 死亡した敵を削除
    for enemy in enemies_to_remove:
        enemies.remove(enemy)
    # ボム発動のサウンド
    try:
        from core.audio import audio
        audio.play_sound('bomb')
    except Exception:
        pass


def update_difficulty(game_time, last_difficulty_increase, spawn_interval):
    """難易度調整処理"""
    new_last_difficulty_increase = last_difficulty_increase
    new_spawn_interval = spawn_interval
    
    # 30秒ごとに難易度を上げる
    if game_time - last_difficulty_increase >= 30:
        new_last_difficulty_increase = game_time
        if new_spawn_interval > 20:  # 最小スポーン間隔を20フレームに制限
            new_spawn_interval = max(20, new_spawn_interval - 5)
    
    return new_last_difficulty_increase, new_spawn_interval


def handle_player_level_up(player):
    """プレイヤーのレベルアップ処理"""
    if player.exp >= player.exp_to_next:
        player.level += 1
        player.exp -= player.exp_to_next
        player.exp_to_next = int(player.exp_to_next * 1.2)
        
        # レベルアップエフェクトを追加する場合はここで
        # particles.append(LevelUpEffect(player.x, player.y))
        
        # 武器選択UIを表示
        try:
            player.upgrade_weapons()
            if getattr(player, 'last_level_choices', None):
                player.awaiting_weapon_choice = True
                player.selected_weapon_choice_index = 0
        except Exception:
            pass
        
        return True
    return False


def collect_experience_gems(player, experience_gems, particles):
    """経験値ジェムの収集処理"""
    collection_range = 30  # 収集範囲
    
    for gem in experience_gems[:]:
        distance = ((gem.x - player.x) ** 2 + (gem.y - player.y) ** 2) ** 0.5
        if distance <= collection_range:
            # 経験値を加算
            gem_value = getattr(gem, 'value', 1)
            player.exp += gem_value
            
            # 収集エフェクト（必要に応じて）
            # particles.append(CollectEffect(gem.x, gem.y))
            
            experience_gems.remove(gem)


def collect_items(player, items, enemies, experience_gems, particles):
    """アイテムの収集処理"""
    collection_range = 25  # アイテム収集範囲
    
    for item in items[:]:
        distance = ((item.x - player.x) ** 2 + (item.y - player.y) ** 2) ** 0.5
        if distance <= collection_range:
            if item.type == "heal":
                # 体力回復（割合回復）
                healed = player.heal(HEAL_ITEM_AMOUNT, "item")
                try:
                    if healed > 0:
                        from core.audio import audio
                        audio.play_sound('heal')
                except Exception:
                    pass
                        
            elif item.type == "bomb":
                # ボム効果（画面揺れも含む）
                handle_bomb_item_effect(enemies, experience_gems, particles, 
                                      player.x, player.y, player)
            
            elif item.type == "magnet":
                # マグネット効果を有効化
                player.activate_magnet()
            
            items.remove(item)
