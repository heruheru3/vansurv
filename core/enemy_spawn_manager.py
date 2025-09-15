import csv
import random
import os
from typing import List, Dict, Optional, Tuple

class EnemySpawnManager:
    """エネミー出現ルールを管理するクラス"""
    
    def __init__(self, csv_path: str = "data/enemy_spawn_rules.csv"):
        self.csv_path = csv_path
        self.spawn_rules: List[Dict] = []
        self.use_csv_rules = True  # CSVルールを使用するかのフラグ
        self.load_spawn_rules()
    
    def load_spawn_rules(self):
        """CSV ファイルからスポーンルールを読み込み"""
        try:
            if not os.path.exists(self.csv_path):
                print(f"Warning: Spawn rules CSV not found at {self.csv_path}")
                print("Falling back to hardcoded rules")
                self.use_csv_rules = False
                return
            
            self.spawn_rules = []
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # データ型変換
                    rule = {
                        'rule_id': int(row['rule_id']),
                        'start_time': int(row['start_time']),
                        'end_time': int(row['end_time']) if row['end_time'] != '-1' else -1,
                        'enemy_no_list': [int(x.strip()) for x in row['enemy_no_list'].split(',')],
                        'spawn_weight': float(row['spawn_weight']),
                        'spawn_frequency': float(row['spawn_frequency']),
                        'strength_multiplier': float(row['strength_multiplier']),
                        'size_multiplier': float(row['size_multiplier']),
                        'enabled': row['enabled'].lower() == 'true',
                        'description': row['description']
                    }
                    self.spawn_rules.append(rule)
            
            print(f"Loaded {len(self.spawn_rules)} spawn rules from {self.csv_path}")
            self.use_csv_rules = True
            
        except Exception as e:
            print(f"Error loading spawn rules: {e}")
            print("Falling back to hardcoded rules")
            self.use_csv_rules = False
    
    def get_active_rules(self, game_time: int) -> List[Dict]:
        """現在の時刻で有効なルールを取得"""
        if not self.use_csv_rules:
            return []
        
        active_rules = []
        for rule in self.spawn_rules:
            if not rule['enabled']:
                continue
            
            # 時間範囲チェック
            if rule['start_time'] <= game_time:
                if rule['end_time'] == -1 or game_time <= rule['end_time']:
                    active_rules.append(rule)
        
        return active_rules
    
    def select_enemy_no(self, game_time: int) -> Tuple[int, Optional[Dict]]:
        """
        時間に応じてenemy_noを選択
        
        Returns:
            tuple: (enemy_no, rule_dict or None)
        """
        if not self.use_csv_rules:
            print("ERROR: CSV spawn rules are required but not available!")
            return 1, None  # 最低限のフォールバック
        
        active_rules = self.get_active_rules(game_time)
        if not active_rules:
            print(f"WARNING: No active spawn rules found for game_time {game_time}")
            return 1, None
        
        # 各ルールから候補を収集
        candidates = []
        weights = []
        
        for rule in active_rules:
            for enemy_no in rule['enemy_no_list']:
                candidates.append({
                    'enemy_no': enemy_no,
                    'rule': rule
                })
                weights.append(rule['spawn_weight'])
        
        if not candidates:
            print(f"WARNING: No enemy candidates found for game_time {game_time}")
            return 1, None
        
        # 重み付き選択
        selected = random.choices(candidates, weights=weights)[0]
        return selected['enemy_no'], selected['rule']
    
    def get_enemy_modifiers(self, rule: Optional[Dict]) -> Tuple[float, float]:
        """
        ルールから倍率情報を取得
        
        Returns:
            tuple: (strength_multiplier, size_multiplier)
        """
        if rule is None:
            return 1.0, 1.0
        
        return rule['strength_multiplier'], rule['size_multiplier']
    
    def get_spawn_frequency_multiplier(self, rule: Optional[Dict]) -> float:
        """出現頻度倍率を取得"""
        if rule is None:
            return 1.0
        
        return rule['spawn_frequency']
    
    def get_average_spawn_frequency(self, game_time: int) -> float:
        """
        現在の時刻でアクティブなルールの平均spawn_frequency倍率を取得
        
        Returns:
            float: 平均spawn_frequency倍率（重み付き平均）
        """
        if not self.use_csv_rules:
            return 1.0
        
        active_rules = self.get_active_rules(game_time)
        if not active_rules:
            return 1.0
        
        # 重み付き平均を計算
        total_weighted_frequency = 0.0
        total_weight = 0.0
        
        for rule in active_rules:
            # enemy_no_listの数だけ重みを倍増（敵の数に比例）
            rule_weight = rule['spawn_weight'] * len(rule['enemy_no_list'])
            total_weighted_frequency += rule['spawn_frequency'] * rule_weight
            total_weight += rule_weight
        
        if total_weight == 0:
            return 1.0
        
        return total_weighted_frequency / total_weight
    
    def reload_rules(self):
        """ルールを再読み込み（デバッグ・調整用）"""
        self.load_spawn_rules()
    
    def get_debug_info(self, game_time: int) -> Dict:
        """デバッグ情報を取得"""
        active_rules = self.get_active_rules(game_time)
        
        return {
            'use_csv_rules': self.use_csv_rules,
            'total_rules': len(self.spawn_rules),
            'active_rules_count': len(active_rules),
            'active_rules': [
                {
                    'rule_id': rule['rule_id'],
                    'description': rule['description'],
                    'enemy_nos': rule['enemy_no_list'],
                    'weight': rule['spawn_weight']
                }
                for rule in active_rules
            ]
        }