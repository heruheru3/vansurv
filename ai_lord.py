import pygame
import random
import math
from constants import *

class AILord:
    """AI勢力を表現するクラス"""
    
    PERSONALITIES = {
        'aggressive': {'attack_weight': 0.7, 'defense_weight': 0.2, 'expand_weight': 0.1, 'attack_threshold': 0.6},
        'defensive': {'attack_weight': 0.2, 'defense_weight': 0.6, 'expand_weight': 0.2, 'attack_threshold': 1.2},
        'expansionist': {'attack_weight': 0.3, 'defense_weight': 0.1, 'expand_weight': 0.6, 'attack_threshold': 0.8},
        'balanced': {'attack_weight': 0.4, 'defense_weight': 0.3, 'expand_weight': 0.3, 'attack_threshold': 1.0}
    }
    
    def __init__(self, faction_name, color, personality='balanced'):
        self.faction_name = faction_name
        self.color = color
        self.personality = personality
        self.personality_data = self.PERSONALITIES[personality]
        
        # AI状態
        self.territories = []
        self.resources = {'gold': 100, 'troops': 50}
        self.last_action_time = 0
        self.action_interval = 3.0  # 3秒ごとに行動判定
        self.current_target = None
        self.attack_in_progress = False
        
        # AI思考記録
        self.threat_assessment = {}  # 脅威度評価
        self.strategic_priorities = []
        
        # 外交関係（他のAI勢力との関係）
        self.diplomacy = {}  # 'faction_name': relationship_value (-1.0 ~ 1.0)
        self.alliance_proposals = {}  # 同盟提案
        self.war_declarations = set()  # 宣戦布告された相手
        
    def update(self, dt, territory_manager, all_lords):
        """AI勢力の更新"""
        current_time = pygame.time.get_ticks() / 1000.0
        
        # 資源の更新
        self.update_resources(territory_manager)
        
        # 定期的な戦略判定
        if current_time - self.last_action_time >= self.action_interval:
            self.last_action_time = current_time
            self.make_strategic_decision(territory_manager, all_lords)
            
    def update_resources(self, territory_manager):
        """所有拠点から資源を獲得"""
        self.territories = [t for t in territory_manager.territories if t.owner == self.faction_name]
        total_income = sum(t.income for t in self.territories)
        self.resources['gold'] += total_income
        self.resources['troops'] = min(200, self.resources['troops'] + len(self.territories))  # 拠点数に応じて兵力回復
        
    def make_strategic_decision(self, territory_manager, all_lords):
        """戦略的判定を行う"""
        if not self.territories:
            return
            
        # 脅威度評価の更新
        self.assess_threats(territory_manager, all_lords)
        
        # 戦略優先度の決定
        self.determine_priorities(territory_manager)
        
        # 行動の実行
        self.execute_action(territory_manager)
        
    def assess_threats(self, territory_manager, all_lords):
        """脅威度評価"""
        self.threat_assessment = {}
        
        for lord in all_lords:
            if lord.faction_name == self.faction_name:
                continue
                
            # 相手の拠点数と距離から脅威度を計算
            enemy_territories = len(lord.territories)
            min_distance = float('inf')
            
            for my_territory in self.territories:
                for enemy_territory in lord.territories:
                    distance = math.sqrt((my_territory.x - enemy_territory.x)**2 + 
                                       (my_territory.y - enemy_territory.y)**2)
                    min_distance = min(min_distance, distance)
                    
            if min_distance == float('inf'):
                min_distance = 1000
                
            # 脅威度 = 敵の勢力 / 距離
            threat_level = enemy_territories / (min_distance / 100 + 1)
            self.threat_assessment[lord.faction_name] = threat_level
            
            # 外交関係の更新
            self.update_diplomacy(lord.faction_name, threat_level, enemy_territories)
            
        # プレイヤーの脅威度も評価
        player_territories = territory_manager.get_player_territories()
        if player_territories > 0:
            player_threat = self.calculate_player_threat(territory_manager)
            self.threat_assessment['player'] = player_threat
            
    def calculate_player_threat(self, territory_manager):
        """プレイヤーの脅威度を計算"""
        player_territories = [t for t in territory_manager.territories if t.owner == 'player']
        if not player_territories:
            return 0
            
        # プレイヤーの拠点数と最近接距離から脅威度を計算
        min_distance = float('inf')
        for my_territory in self.territories:
            for player_territory in player_territories:
                distance = math.sqrt((my_territory.x - player_territory.x)**2 + 
                                   (my_territory.y - player_territory.y)**2)
                min_distance = min(min_distance, distance)
                
        if min_distance == float('inf'):
            return 0
            
        return len(player_territories) / (min_distance / 100 + 1) * 1.5  # プレイヤーは特に警戒
        
    def determine_priorities(self, territory_manager):
        """戦略優先度の決定"""
        self.strategic_priorities = []
        
        # 1. 攻撃可能な敵拠点を検索
        attack_targets = self.find_attack_targets(territory_manager)
        
        # 2. 防御が必要な自拠点を検索  
        defense_targets = self.find_defense_targets(territory_manager)
        
        # 3. 拡張可能な中立拠点を検索
        expansion_targets = self.find_expansion_targets(territory_manager)
        
        # 性格に基づいて優先度を設定
        personality = self.personality_data
        
        for target in attack_targets:
            priority = personality['attack_weight'] * target['strategic_value']
            self.strategic_priorities.append({
                'type': 'attack',
                'target': target['territory'],
                'priority': priority,
                'data': target
            })
            
        for target in defense_targets:
            priority = personality['defense_weight'] * target['urgency']
            self.strategic_priorities.append({
                'type': 'defense', 
                'target': target['territory'],
                'priority': priority,
                'data': target
            })
            
        for target in expansion_targets:
            priority = personality['expand_weight'] * target['value']
            self.strategic_priorities.append({
                'type': 'expand',
                'target': target['territory'], 
                'priority': priority,
                'data': target
            })
            
        # 優先度でソート
        self.strategic_priorities.sort(key=lambda x: x['priority'], reverse=True)
        
    def find_attack_targets(self, territory_manager):
        """攻撃可能な敵拠点を検索"""
        targets = []
        
        for territory in territory_manager.territories:
            if territory.owner == self.faction_name or territory.owner is None:
                continue
                
            # 自拠点からの最短距離を計算
            min_distance = self.get_min_distance_to_territory(territory)
            
            if min_distance <= 300:  # 攻撃圏内
                # 戦略的価値を計算
                strategic_value = self.calculate_strategic_value(territory, territory_manager)
                
                # 戦争状態の相手は優先度を上げる
                if territory.owner in self.war_declarations:
                    strategic_value *= 2.0
                
                targets.append({
                    'territory': territory,
                    'distance': min_distance,
                    'strategic_value': strategic_value,
                    'estimated_difficulty': territory.current_defense / self.resources['troops']
                })
                
        return targets
        
    def find_defense_targets(self, territory_manager):
        """防御が必要な自拠点を検索"""
        targets = []
        
        for territory in self.territories:
            # 敵拠点との距離を確認
            enemy_proximity = self.get_enemy_proximity(territory, territory_manager)
            
            if enemy_proximity < 250:  # 敵が接近している
                urgency = (250 - enemy_proximity) / 250
                targets.append({
                    'territory': territory,
                    'urgency': urgency,
                    'enemy_proximity': enemy_proximity
                })
                
        return targets
        
    def find_expansion_targets(self, territory_manager):
        """拡張可能な中立拠点を検索"""
        targets = []
        
        for territory in territory_manager.territories:
            if territory.owner is not None:
                continue
                
            # 自拠点からの距離
            min_distance = self.get_min_distance_to_territory(territory)
            
            if min_distance <= 200:  # 拡張圏内
                # 拡張価値を計算（収入、戦略位置など）
                value = territory.income / (min_distance / 50 + 1)
                
                targets.append({
                    'territory': territory,
                    'distance': min_distance,
                    'value': value
                })
                
        return targets
        
    def execute_action(self, territory_manager):
        """最優先行動を実行"""
        if not self.strategic_priorities:
            return
            
        top_priority = self.strategic_priorities[0]
        action_type = top_priority['type']
        target = top_priority['target']
        
        if action_type == 'attack':
            self.execute_attack(target, territory_manager)
        elif action_type == 'defense':
            self.execute_defense(target, territory_manager)
        elif action_type == 'expand':
            self.execute_expansion(target, territory_manager)
            
    def execute_attack(self, target_territory, territory_manager):
        """攻撃の実行"""
        if self.resources['troops'] < 20:
            return
            
        # 攻撃力と防御力の比較
        attack_power = self.resources['troops'] * 0.8
        defense_power = target_territory.current_defense
        
        if attack_power >= defense_power * self.personality_data['attack_threshold']:
            # 攻撃元の拠点を取得（一番近い自拠点）
            attacker_territory = min(self.territories, 
                                   key=lambda t: math.sqrt((t.x - target_territory.x)**2 + (t.y - target_territory.y)**2))
            
            # 戦闘エフェクトを追加
            if hasattr(territory_manager, 'battle_effects'):
                from battle_effects import BattleEffect
                effect = BattleEffect(attacker_territory.x, attacker_territory.y,
                                    target_territory.x, target_territory.y,
                                    self.color)
                territory_manager.battle_effects.append(effect)
            
            # 攻撃実行
            damage = min(attack_power * 0.3, target_territory.current_defense)
            target_territory.current_defense -= damage
            self.resources['troops'] -= int(attack_power * 0.1)  # 攻撃側も損失
            
            # 制圧成功
            if target_territory.current_defense <= 0:
                old_owner = target_territory.owner
                target_territory.owner = self.faction_name
                target_territory.current_defense = target_territory.max_defense * 0.5  # 半分で制圧
                print(f"[AI] {self.faction_name}が{target_territory.territory_type}を{old_owner}から奪取！")
                
            self.attack_in_progress = True
            
    def execute_defense(self, target_territory, territory_manager):
        """防御の実行"""
        if self.resources['gold'] >= 50:
            # 防御力強化
            target_territory.current_defense = min(
                target_territory.max_defense,
                target_territory.current_defense + 30
            )
            self.resources['gold'] -= 50
            
    def execute_expansion(self, target_territory, territory_manager):
        """拡張の実行"""
        if self.resources['troops'] >= 15:
            # 中立拠点の制圧
            target_territory.owner = self.faction_name
            target_territory.current_defense = target_territory.max_defense * 0.7
            self.resources['troops'] -= 15
            print(f"[AI] {self.faction_name}が中立の{target_territory.territory_type}を制圧！")
            
    def get_min_distance_to_territory(self, target_territory):
        """自拠点から指定拠点への最短距離"""
        if not self.territories:
            return float('inf')
            
        return min(
            math.sqrt((t.x - target_territory.x)**2 + (t.y - target_territory.y)**2)
            for t in self.territories
        )
        
    def get_enemy_proximity(self, my_territory, territory_manager):
        """指定拠点への敵の最接近距離"""
        min_distance = float('inf')
        
        for territory in territory_manager.territories:
            if territory.owner == self.faction_name or territory.owner is None:
                continue
                
            distance = math.sqrt((my_territory.x - territory.x)**2 + (my_territory.y - territory.y)**2)
            min_distance = min(min_distance, distance)
            
        return min_distance
        
    def calculate_strategic_value(self, territory, territory_manager):
        """拠点の戦略的価値を計算"""
        base_value = territory.income
        
        # 敵勢力の拠点なら価値が高い
        if territory.owner == 'player':
            base_value *= 1.5
        elif territory.owner != self.faction_name and territory.owner is not None:
            base_value *= 1.3
            
        # 拠点の種類による価値補正
        if territory.territory_type == 'castle':
            base_value *= 1.4
        elif territory.territory_type == 'town':
            base_value *= 1.2
            
        return base_value


    def update_diplomacy(self, other_faction, threat_level, their_territory_count):
        """外交関係の更新"""
        if other_faction not in self.diplomacy:
            self.diplomacy[other_faction] = 0.0
            
        current_relation = self.diplomacy[other_faction]
        
        # 脅威度が高いと関係悪化、低いと改善の可能性
        if threat_level > 2.0:
            # 高脅威：関係悪化
            self.diplomacy[other_faction] = max(-1.0, current_relation - 0.1)
            if current_relation < -0.7:
                self.war_declarations.add(other_faction)
        elif threat_level < 0.5 and their_territory_count < len(self.territories):
            # 低脅威で弱い相手：関係改善の余地
            self.diplomacy[other_faction] = min(1.0, current_relation + 0.05)
            
    def consider_alliance(self, other_lord):
        """同盟の検討"""
        if other_lord.faction_name in self.diplomacy:
            relation = self.diplomacy[other_lord.faction_name]
            
            # 好関係かつ共通の脅威がある場合は同盟提案
            if relation > 0.3:
                common_threats = self.find_common_threats(other_lord)
                if common_threats:
                    self.alliance_proposals[other_lord.faction_name] = True
                    return True
        return False
        
    def find_common_threats(self, other_lord):
        """共通の脅威を見つける"""
        common_threats = []
        
        for faction, my_threat in self.threat_assessment.items():
            if faction in other_lord.threat_assessment:
                other_threat = other_lord.threat_assessment[faction]
                if my_threat > 1.5 and other_threat > 1.5:
                    common_threats.append(faction)
                    
        return common_threats


class AIManager:
    """AI勢力全体を管理するクラス"""
    
    def __init__(self):
        self.ai_lords = [
            AILord('ai_red', (150, 50, 50), 'aggressive'),
            AILord('ai_blue', (50, 50, 150), 'defensive'),
            AILord('ai_green', (50, 150, 50), 'expansionist'),
        ]
        
    def update(self, dt, territory_manager):
        """全AI勢力の更新"""
        for lord in self.ai_lords:
            lord.update(dt, territory_manager, self.ai_lords)
            
        # 外交システムの処理
        self.process_diplomacy()
            
    def get_ai_lord_by_faction(self, faction_name):
        """派閥名からAI勢力を取得"""
        for lord in self.ai_lords:
            if lord.faction_name == faction_name:
                return lord
        return None
        
    def process_diplomacy(self):
        """AI勢力間の外交処理"""
        for i, lord1 in enumerate(self.ai_lords):
            for j, lord2 in enumerate(self.ai_lords[i+1:], i+1):
                # 同盟の検討
                if lord1.consider_alliance(lord2):
                    if lord2.faction_name in lord1.alliance_proposals:
                        print(f"[DIPLOMACY] {lord1.faction_name}と{lord2.faction_name}が同盟締結を検討中")
                        
                # 戦争状態のチェック
                if lord2.faction_name in lord1.war_declarations:
                    if lord1.faction_name not in lord2.war_declarations:
                        lord2.war_declarations.add(lord1.faction_name)
                        print(f"[DIPLOMACY] {lord1.faction_name}と{lord2.faction_name}が戦争状態！")
        
    def draw_ai_info(self, screen, territory_manager):
        """AI勢力の情報を画面に表示"""
        try:
            font = pygame.font.SysFont(None, 20)
            y_offset = 150
            
            for lord in self.ai_lords:
                if not lord.territories:
                    continue
                    
                # 勢力情報の表示
                color_text = f"{lord.faction_name}: {len(lord.territories)}領土"
                text_surf = font.render(color_text, True, lord.color)
                screen.blit(text_surf, (SCREEN_WIDTH - 200, y_offset))
                
                # 資源情報
                resource_text = f"兵力:{lord.resources['troops']}"
                resource_surf = font.render(resource_text, True, WHITE)
                screen.blit(resource_surf, (SCREEN_WIDTH - 200, y_offset + 20))
                
                # 外交状態の表示
                diplomacy_status = "中立"
                if lord.war_declarations:
                    diplomacy_status = f"交戦中({len(lord.war_declarations)})"
                elif lord.alliance_proposals:
                    diplomacy_status = f"同盟({len(lord.alliance_proposals)})"
                    
                diplomacy_surf = font.render(diplomacy_status, True, (200, 200, 200))
                screen.blit(diplomacy_surf, (SCREEN_WIDTH - 200, y_offset + 40))
                
                y_offset += 70
                
        except Exception:
            pass
