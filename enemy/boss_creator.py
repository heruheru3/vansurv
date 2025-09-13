"""
ボスキャラ作成・管理ツール
ボスの画像生成、ステータス設定、出現条件設定を行う
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont
import colorsys
import random
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

@dataclass
class BossStats:
    """ボスのステータス情報"""
    name: str
    hp: int
    damage: int
    speed: float
    size: int
    special_abilities: List[str]
    attack_patterns: List[str]
    
@dataclass
class BossSpawnCondition:
    """ボス出現条件"""
    time_threshold: int  # 経過時間（秒）
    player_level_threshold: int  # プレイヤーレベル
    enemies_killed_threshold: int  # 撃破敵数
    spawn_message: str  # 出現時メッセージ

@dataclass
class BossData:
    """ボス全体データ"""
    id: str
    image_file: str
    stats: BossStats
    spawn_condition: BossSpawnCondition
    color_scheme: Dict[str, Any]

class BossCreator:
    """ボス作成・管理クラス"""
    
    def __init__(self):
        self.output_dir = "enemy"
        self.bosses_dir = os.path.join(self.output_dir, "bosses")
        self.config_file = os.path.join(self.output_dir, "boss_config.json")
        
        # ディレクトリ作成
        os.makedirs(self.bosses_dir, exist_ok=True)
    
    def generate_boss_image(self, boss_id: str, size: int = 128, color_scheme: Dict[str, Any] = None):
        """ボス画像を生成する"""
        if color_scheme is None:
            color_scheme = self._generate_boss_colors()
        
        # キャンバス作成
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        center = size // 2
        
        # ボスの基本形状を描画（より大きく威圧的に）
        # 外側のオーラ
        aura_radius = size // 2 - 5
        for i in range(5):
            alpha = 50 - i * 8
            aura_color = (*color_scheme['aura'], alpha)
            draw.ellipse([
                center - aura_radius + i, center - aura_radius + i,
                center + aura_radius - i, center + aura_radius - i
            ], fill=aura_color)
        
        # メイン本体（六角形っぽい形状で威圧感）
        body_radius = size // 3
        body_points = []
        for i in range(8):  # 8角形
            angle = i * 45  # 45度刻み
            x = center + int(body_radius * 0.8 * cos_deg(angle))
            y = center + int(body_radius * 0.8 * sin_deg(angle))
            body_points.extend([x, y])
        
        draw.polygon(body_points, fill=color_scheme['body'], outline=color_scheme['outline'], width=3)
        
        # 中央のコア
        core_radius = body_radius // 2
        draw.ellipse([
            center - core_radius, center - core_radius,
            center + core_radius, center + core_radius
        ], fill=color_scheme['core'], outline=color_scheme['core_outline'], width=2)
        
        # 触手・攻撃部位
        tentacle_count = 6
        for i in range(tentacle_count):
            angle = i * 60  # 60度刻み
            start_x = center + int((body_radius - 5) * cos_deg(angle))
            start_y = center + int((body_radius - 5) * sin_deg(angle))
            end_x = center + int((size // 2 - 10) * cos_deg(angle))
            end_y = center + int((size // 2 - 10) * sin_deg(angle))
            
            draw.line([start_x, start_y, end_x, end_y], 
                     fill=color_scheme['tentacle'], width=4)
            
            # 触手先端
            draw.ellipse([
                end_x - 3, end_y - 3, end_x + 3, end_y + 3
            ], fill=color_scheme['tentacle_tip'])
        
        # 威圧的な目（複数）
        eye_positions = [
            (center - 15, center - 10),
            (center + 15, center - 10),
            (center, center + 5)
        ]
        
        for eye_x, eye_y in eye_positions:
            # 目の背景
            draw.ellipse([eye_x - 8, eye_y - 5, eye_x + 8, eye_y + 5], 
                        fill=color_scheme['eye_bg'])
            # 瞳
            draw.ellipse([eye_x - 4, eye_y - 3, eye_x + 4, eye_y + 3], 
                        fill=color_scheme['pupil'])
            # 光彩効果
            draw.ellipse([eye_x - 2, eye_y - 2, eye_x + 2, eye_y + 2], 
                        fill=color_scheme['eye_glow'])
        
        # ファイル保存
        filename = f"{boss_id}.png"
        filepath = os.path.join(self.bosses_dir, filename)
        image.save(filepath)
        print(f"ボス画像を生成しました: {filepath}")
        
        return filename, color_scheme
    
    def _generate_boss_colors(self) -> Dict[str, Any]:
        """ボス用カラースキームを生成"""
        # ベース色相（赤系、紫系、暗色系）
        base_hues = [0, 0.8, 0.9, 0.1]  # 赤、紫、マゼンタ、オレンジ系
        base_hue = random.choice(base_hues)
        
        def hue_to_rgb(h, s, v, alpha=255):
            rgb = colorsys.hsv_to_rgb(h, s, v)
            return tuple(int(c * 255) for c in rgb) + (alpha,)
        
        return {
            'aura': hue_to_rgb(base_hue, 0.6, 0.3)[:3],  # オーラ（暗め）
            'body': hue_to_rgb(base_hue, 0.8, 0.6),      # 本体
            'outline': hue_to_rgb(base_hue, 0.9, 0.3),   # アウトライン
            'core': hue_to_rgb((base_hue + 0.1) % 1.0, 0.9, 0.8),  # コア（明るめ）
            'core_outline': hue_to_rgb(base_hue, 1.0, 0.4),
            'tentacle': hue_to_rgb(base_hue, 0.7, 0.5),
            'tentacle_tip': hue_to_rgb((base_hue + 0.05) % 1.0, 0.9, 0.7),
            'eye_bg': (220, 220, 220),  # 目の背景（白系）
            'pupil': (20, 20, 20),      # 瞳（黒）
            'eye_glow': hue_to_rgb((base_hue + 0.2) % 1.0, 0.8, 1.0),  # 目の光彩
        }
    
    def create_boss(self, boss_id: str, **kwargs) -> BossData:
        """新しいボスを作成"""
        # デフォルト値
        defaults = {
            'name': f'Boss {boss_id.upper()}',
            'hp': 5000,
            'damage': 50,
            'speed': 1.5,
            'size': 128,
            'special_abilities': ['charge_attack', 'area_damage'],
            'attack_patterns': ['melee', 'ranged_burst'],
            'time_threshold': 120,  # 2分後
            'player_level_threshold': 10,
            'enemies_killed_threshold': 100,
            'spawn_message': f'{boss_id.upper()}が出現した！'
        }
        
        # カスタム値でデフォルトを上書き
        config = {**defaults, **kwargs}
        
        # 画像生成
        image_file, color_scheme = self.generate_boss_image(
            boss_id, 
            size=config['size']
        )
        
        # データ構造作成
        stats = BossStats(
            name=config['name'],
            hp=config['hp'],
            damage=config['damage'],
            speed=config['speed'],
            size=config['size'],
            special_abilities=config['special_abilities'],
            attack_patterns=config['attack_patterns']
        )
        
        spawn_condition = BossSpawnCondition(
            time_threshold=config['time_threshold'],
            player_level_threshold=config['player_level_threshold'],
            enemies_killed_threshold=config['enemies_killed_threshold'],
            spawn_message=config['spawn_message']
        )
        
        boss_data = BossData(
            id=boss_id,
            image_file=image_file,
            stats=stats,
            spawn_condition=spawn_condition,
            color_scheme=color_scheme
        )
        
        return boss_data
    
    def save_boss_config(self, bosses: List[BossData]):
        """ボス設定をJSONファイルに保存"""
        config_data = {
            "bosses": [asdict(boss) for boss in bosses],
            "version": "1.0"
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"ボス設定を保存しました: {self.config_file}")
    
    def load_boss_config(self) -> List[BossData]:
        """ボス設定をJSONファイルから読み込み"""
        if not os.path.exists(self.config_file):
            return []
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        bosses = []
        for boss_dict in config_data.get("bosses", []):
            stats = BossStats(**boss_dict["stats"])
            spawn_condition = BossSpawnCondition(**boss_dict["spawn_condition"])
            boss = BossData(
                id=boss_dict["id"],
                image_file=boss_dict["image_file"],
                stats=stats,
                spawn_condition=spawn_condition,
                color_scheme=boss_dict["color_scheme"]
            )
            bosses.append(boss)
        
        return bosses

def cos_deg(degrees):
    """度数法でcosを計算"""
    import math
    return math.cos(math.radians(degrees))

def sin_deg(degrees):
    """度数法でsinを計算"""
    import math
    return math.sin(math.radians(degrees))

def main():
    """メイン実行関数"""
    creator = BossCreator()
    
    # ボス01を作成
    boss_01 = creator.create_boss(
        "boss-01",
        name="デストロイヤー",
        hp=8000,
        damage=75,
        speed=2.0,
        size=128,
        special_abilities=["charge_attack", "area_damage", "summon_minions"],
        attack_patterns=["melee", "ranged_burst", "spin_attack"],
        time_threshold=90,  # 1分30秒後
        player_level_threshold=8,
        enemies_killed_threshold=80,
        spawn_message="強大なる破壊者が現れた！"
    )
    
    # 設定保存
    creator.save_boss_config([boss_01])
    
    print("ボス01の作成が完了しました！")
    print(f"名前: {boss_01.stats.name}")
    print(f"HP: {boss_01.stats.hp}")
    print(f"攻撃力: {boss_01.stats.damage}")
    print(f"速度: {boss_01.stats.speed}")
    print(f"特殊能力: {', '.join(boss_01.stats.special_abilities)}")
    print(f"出現条件: 時間{boss_01.spawn_condition.time_threshold}秒, レベル{boss_01.spawn_condition.player_level_threshold}, 撃破数{boss_01.spawn_condition.enemies_killed_threshold}")

if __name__ == "__main__":
    main()
