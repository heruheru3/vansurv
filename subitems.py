import random

class SubItem:
    """単純なサブアイテム (ステータスの強化) を表現するクラス

    name: キー名
    level: 現在のレベル
    base: レベル0時の基本値
    per_level: レベル1ごとの成長量
    is_percent: True の場合は割合として扱う (値は 0.0 = 0%)
    """
    def __init__(self, name, base=0.0, per_level=1.0, is_percent=False):
        self.name = name
        self.level = 0
        self.base = base
        self.per_level = per_level
        self.is_percent = is_percent

    def value(self):
        """現在の効果量を返す。is_percent が True の場合は 0.10 が "+10%" を意味する."""
        return self.base + (self.level * self.per_level)

    def __repr__(self):
        return f"SubItem(name={self.name}, level={self.level}, value={self.value()})"

    def copy(self, level=0):
        """テンプレートから新しい SubItem インスタンスを作るユーティリティ（テンプレートを壊さない）

        level: 新しいインスタンスの初期レベル
        """
        s = SubItem(self.name, base=self.base, per_level=self.per_level, is_percent=self.is_percent)
        s.level = level
        return s


def get_default_subitems():
    """プロジェクトで使うデフォルトのサブアイテム定義を辞書で返す。

    キー一覧:
      - hp: 最大HPに加算される（flat）
      - base_damage: 基礎攻撃力に加算される（flat）
      - defense: 受けるダメージを軽減する（flat、将来的に%化可能）
      - speed: プレイヤー移動速度に加算される（flat）
      - effect_range: 武器の効果範囲に対する倍率（is_percent=True）
      - effect_time: 武器の効果時間に対する倍率（is_percent=True）
      - extra_projectiles: 武器の発射数に追加される量（小数で蓄積し、実際の追加は int() で扱う）
      - projectile_speed: 発射物（弾）の速度に対する倍率（is_percent=True）
      - gem_pickup_range: ジェムの取得範囲に対する倍率（is_percent=True）
    """
    return {
        'hp': SubItem('hp', base=0.0, per_level=20.0, is_percent=True),
        'base_damage': SubItem('base_damage', base=0.0, per_level=0.20, is_percent=True),
        'defense': SubItem('defense', base=0.0, per_level=2.0, is_percent=False),
        'speed': SubItem('speed', base=0.0, per_level=0.2, is_percent=False),
        'effect_range': SubItem('effect_range', base=0.0, per_level=0.25, is_percent=True),
        'effect_time': SubItem('effect_time', base=0.0, per_level=0.25, is_percent=True),
        'extra_projectiles': SubItem('extra_projectiles', base=0.0, per_level=1, is_percent=False),
        'projectile_speed': SubItem('projectile_speed', base=0.0, per_level=0.2, is_percent=True),
        'gem_pickup_range': SubItem('gem_pickup_range', base=0.0, per_level=16.0, is_percent=False),
    }


def random_upgrade(subitems_dict, count=1):
    """ランダムに1つ以上のサブアイテムのレベルを増やし、増やしたキーのリストを返す."""
    keys = list(subitems_dict.keys())
    chosen = []
    for _ in range(count):
        k = random.choice(keys)
        subitems_dict[k].level += 1
        chosen.append(k)
    return chosen
