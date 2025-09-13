"""
衝突判定処理
プレイヤー、敵、攻撃の衝突判定を管理
"""

import pygame
from constants import INVINCIBLE_MS
from effects.particles import PlayerHurtParticle, HurtFlash, DamageNumber, AvoidanceParticle
from core.game_logic import handle_enemy_death
from core.game_utils import calculate_distance


def check_player_enemy_collision(player, enemies, particles, current_time):
    """プレイヤーと敵の衝突判定"""
    player_hit = False
    
    # 無敵時間チェック
    if current_time - getattr(player, 'last_hit_time', -999999) < INVINCIBLE_MS:
        return player_hit
    
    collision_range = 25  # プレイヤーと敵の衝突範囲
    
    for enemy in enemies:
        distance = calculate_distance(player.x, player.y, enemy.x, enemy.y)
        if distance <= collision_range:
            # ダメージ処理
            damage = getattr(enemy, 'damage', 10)
            player.hp -= damage
            player.last_hit_time = current_time
            player_hit = True
            
            # ヒットエフェクト
            particles.append(PlayerHurtParticle(player.x, player.y))
            particles.append(HurtFlash())
            # サウンド再生（プレイヤー被弾）
            try:
                from core.audio import audio
                audio.play_sound('player_hurt')
            except Exception:
                pass
            
            break  # 1フレームに1回だけダメージ
    
    return player_hit


def check_attack_enemy_collision(attacks, enemies, particles, damage_stats, player):
    """攻撃と敵の衝突判定"""
    hits_processed = []
    
    for attack in attacks[:]:
        if not hasattr(attack, 'x') or not hasattr(attack, 'y'):
            continue
            
        # 攻撃範囲の設定
        attack_range = getattr(attack, 'range', 30)
        
        for enemy in enemies[:]:
            distance = calculate_distance(attack.x, attack.y, enemy.x, enemy.y)
            
            if distance <= attack_range:
                # 同じ攻撃で同じ敵への重複ヒットを防ぐ
                hit_key = (id(attack), id(enemy))
                if hit_key in hits_processed:
                    continue
                hits_processed.append(hit_key)
                
                # ダメージ計算
                damage = getattr(attack, 'damage', 10)
                
                # 回避判定（敵が回避スキルを持つ場合）
                if hasattr(enemy, 'avoidance') and enemy.avoidance > 0:
                    import random
                    if random.random() < enemy.avoidance:
                        # 回避エフェクト
                        particles.append(AvoidanceParticle(enemy.x, enemy.y))
                        continue
                
                # ダメージ適用
                enemy.hp -= damage
                # サウンド再生（エネミー被弾）
                try:
                    from core.audio import audio
                    audio.play_sound('enemy_hurt')
                except Exception:
                    pass
                
                # ダメージ統計更新
                attack_type = getattr(attack, 'type', 'unknown')
                if attack_type not in damage_stats:
                    damage_stats[attack_type] = 0
                damage_stats[attack_type] += damage
                
                # ダメージエフェクト
                particles.append(DamageNumber(enemy.x, enemy.y, damage))
                
                # ガーリック効果の回復処理
                try:
                    if attack_type == "garlic":
                        current_time = pygame.time.get_ticks()
                        if not hasattr(attack, 'last_garlic_heal_time'):
                            attack.last_garlic_heal_time = 0
                        
                        if current_time - attack.last_garlic_heal_time > 3000:  # 3秒間隔
                            # Try to use player.heal if available so we get actual healed amount
                            try:
                                healed = player.heal(1, "garlic")
                            except Exception:
                                # Fallback: direct increment
                                try:
                                    old = getattr(player, 'hp', 0)
                                    player.hp = min(100, old + 1)
                                    healed = player.hp - old
                                except Exception:
                                    healed = 0

                            attack.last_garlic_heal_time = current_time
                            # サウンド再生（回復が発生した場合のみ）
                            try:
                                if healed > 0:
                                    from core.audio import audio
                                    audio.play_sound('heal')
                            except Exception:
                                pass
                except Exception:
                    pass
                
                # ヒット時の小エフェクト
                try:
                    if hasattr(enemy, 'on_hit') and callable(enemy.on_hit):
                        enemy.on_hit()
                except Exception:
                    pass
                
                # 敵死亡チェック
                handle_enemy_death(enemy, enemies, [], [], particles, damage_stats,
                                 player.x, player.y, player)
                
                # ヒット時に消費する攻撃の処理
                consumable_on_hit = {"magic_wand"}
                if attack_type in consumable_on_hit:
                    if attack in attacks:
                        attacks.remove(attack)
                    break


def check_circle_rect_collision(circle_x, circle_y, radius, rect_x, rect_y, rect_width, rect_height):
    """円と矩形の衝突判定"""
    # 矩形の最も近い点を求める
    closest_x = max(rect_x, min(circle_x, rect_x + rect_width))
    closest_y = max(rect_y, min(circle_y, rect_y + rect_height))
    
    # 距離を計算
    distance = calculate_distance(circle_x, circle_y, closest_x, closest_y)
    
    return distance <= radius


def check_rect_collision(x1, y1, w1, h1, x2, y2, w2, h2):
    """矩形同士の衝突判定"""
    return (x1 < x2 + w2 and
            x1 + w1 > x2 and
            y1 < y2 + h2 and
            y1 + h1 > y2)


def get_collision_bounds(obj):
    """オブジェクトの衝突判定用境界を取得"""
    x = getattr(obj, 'x', 0)
    y = getattr(obj, 'y', 0)
    width = getattr(obj, 'width', 20)
    height = getattr(obj, 'height', 20)
    
    return x - width // 2, y - height // 2, width, height
