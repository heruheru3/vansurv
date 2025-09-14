import json
import os
from datetime import datetime
from utils.file_paths import get_save_file_path, ensure_directory_exists

class SaveSystem:
    """ゲームの永続データ（お金、統計など）を管理するクラス"""
    
    def __init__(self, save_file="savedata.json"):
        self.save_path = get_save_file_path(save_file)
        self.save_dir = os.path.dirname(self.save_path)
        self.save_file = save_file
        self.data = self._load_or_create_default()
    
    def _get_default_data(self):
        """デフォルトのセーブデータを返す"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "player_stats": {
                "total_money": 0,  # 総所持金
                "money_earned_total": 0,  # 累計獲得金額
                "games_played": 0,  # プレイ回数
                "total_playtime": 0,  # 総プレイ時間（秒）
                "best_survival_time": 0,  # 最長生存時間
                "total_enemies_killed": 0,  # 累計撃破数
                "total_experience_gained": 0,  # 累計経験値
                "max_level_reached": 1  # 到達最高レベル
            },
            "weapon_stats": {
                # 武器ごとの選択回数
                "whip": 0,
                "holy_water": 0,
                "garlic": 0,
                "magic_wand": 0,
                "axe": 0,
                "stone": 0,
                "rotating_book": 0,
                "knife": 0,
                "thunder": 0
            },
            "subitem_stats": {
                # サブアイテムごとの選択回数
                "hp": 0,
                "speed": 0,
                "base_damage": 0,
                "effect_range": 0,
                "effect_time": 0,
                "extra_projectiles": 0,
                "projectile_speed": 0,
                "defense": 0
            },
            "weapon_usage_stats": {
                # 武器使用統計（ダメージベース）
            },
            "achievements": {
                # 実績システム用（将来拡張）
                "first_clear": False,
                "weapon_master": False,  # 全武器を一定回数使用
                "millionaire": False,    # 100万ゴールド達成
                "survivor": False        # 一定時間生存
            }
        }
    
    def _load_or_create_default(self):
        """セーブファイルを読み込み、存在しない場合はデフォルトデータを作成"""
        if not ensure_directory_exists(self.save_dir):
            print(f"[ERROR] Failed to create save directory: {self.save_dir}")
        
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    default_data = self._get_default_data()
                    self._merge_data(default_data, data)
                    print(f"[INFO] Save data loaded from: {self.save_path}")
                    return data
            except (json.JSONDecodeError, FileNotFoundError, KeyError, PermissionError) as e:
                print(f"[WARNING] Save file corrupted or inaccessible: {e}")
                print("[INFO] Creating new save file with default data")
        
        print(f"[INFO] Using default save data. Will save to: {self.save_path}")
        return self._get_default_data()
    
    def _merge_data(self, default, loaded):
        """デフォルトデータと読み込んだデータをマージ（新しいフィールドの追加対応）"""
        for key, value in default.items():
            if key not in loaded:
                loaded[key] = value
            elif isinstance(value, dict) and isinstance(loaded[key], dict):
                self._merge_data(value, loaded[key])
    
    def save(self):
        """データをファイルに保存"""
        try:
            if not ensure_directory_exists(self.save_dir):
                print(f"[ERROR] Cannot create save directory: {self.save_dir}")
                return False
            
            self.data["last_updated"] = datetime.now().isoformat()
            
            # 一時ファイルに書き込んでから置き換え（原子的操作）
            temp_path = self.save_path + '.tmp'
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
                
                if os.path.exists(self.save_path):
                    os.remove(self.save_path)
                os.rename(temp_path, self.save_path)
                
                print(f"[INFO] Save data written to: {self.save_path}")
                return True
                
            except (PermissionError, OSError) as e:
                print(f"[ERROR] Failed to write save file: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to save data: {e}")
            return False
    
    # お金関連のメソッド
    def get_money(self):
        """現在の所持金を取得"""
        return self.data["player_stats"]["total_money"]
    
    def add_money(self, amount):
        """お金を追加"""
        if amount > 0:
            self.data["player_stats"]["total_money"] += amount
            self.data["player_stats"]["money_earned_total"] += amount
    
    def spend_money(self, amount):
        """お金を使用（足りない場合はFalseを返す）"""
        if self.data["player_stats"]["total_money"] >= amount:
            self.data["player_stats"]["total_money"] -= amount
            return True
        return False
    
    # 統計更新メソッド
    def record_game_end(self, survival_time, level, enemies_killed, exp_gained):
        """ゲーム終了時の統計を記録"""
        stats = self.data["player_stats"]
        stats["games_played"] += 1
        stats["total_playtime"] += survival_time
        stats["best_survival_time"] = max(stats["best_survival_time"], survival_time)
        stats["total_enemies_killed"] += enemies_killed
        stats["total_experience_gained"] += exp_gained
        stats["max_level_reached"] = max(stats["max_level_reached"], level)
    
    def record_weapon_selection(self, weapon_name):
        """武器選択回数を記録"""
        if weapon_name in self.data["weapon_stats"]:
            self.data["weapon_stats"][weapon_name] += 1
    
    def record_subitem_selection(self, subitem_name):
        """サブアイテム選択回数を記録"""
        if subitem_name in self.data["subitem_stats"]:
            self.data["subitem_stats"][subitem_name] += 1
    
    def record_weapon_usage(self, weapon_damage_stats):
        """武器使用統計をダメージベースで記録"""
        if "weapon_usage_stats" not in self.data:
            self.data["weapon_usage_stats"] = {}
        
        for weapon_name, damage in weapon_damage_stats.items():
            if weapon_name not in self.data["weapon_usage_stats"]:
                self.data["weapon_usage_stats"][weapon_name] = {
                    "total_damage": 0,
                    "games_used": 0
                }
            self.data["weapon_usage_stats"][weapon_name]["total_damage"] += damage
            self.data["weapon_usage_stats"][weapon_name]["games_used"] += 1
    
    # 統計取得メソッド
    def get_weapon_stats(self):
        """武器統計を取得"""
        return self.data["weapon_stats"].copy()
    
    def get_subitem_stats(self):
        """サブアイテム統計を取得"""
        return self.data["subitem_stats"].copy()
    
    def get_player_stats(self):
        """プレイヤー統計を取得"""
        return self.data["player_stats"].copy()
    
    def get_weapon_usage_stats(self):
        """武器使用統計を取得"""
        return self.data.get("weapon_usage_stats", {}).copy()
    
    # 実績関連メソッド
    def unlock_achievement(self, achievement_name):
        """実績を解除"""
        if achievement_name in self.data["achievements"]:
            if not self.data["achievements"][achievement_name]:
                self.data["achievements"][achievement_name] = True
                print(f"[ACHIEVEMENT] {achievement_name} unlocked!")
                return True
        return False
    
    def check_achievements(self):
        """実績条件をチェック"""
        stats = self.data["player_stats"]
        
        # 初回クリア
        if stats["best_survival_time"] >= 900:  # 15分生存
            self.unlock_achievement("first_clear")
        
        # 大富豪（100万ゴールド）
        if stats["total_money"] >= 1000000:
            self.unlock_achievement("millionaire")
        
        # 武器マスター（全武器を5回以上使用）
        if all(count >= 5 for count in self.data["weapon_stats"].values()):
            self.unlock_achievement("weapon_master")
        
        # サバイバー（30分生存）
        if stats["best_survival_time"] >= 1800:
            self.unlock_achievement("survivor")
