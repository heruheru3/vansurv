#!/usr/bin/env python3
"""
セーブデータを初期化するスクリプト
"""

from save_system import SaveSystem

def create_initial_save():
    """初期セーブデータを作成"""
    print("[INFO] Creating initial save data...")
    
    # SaveSystemを初期化（自動でデフォルトデータが作成される）
    save_system = SaveSystem()
    
    # 初期データを保存
    success = save_system.save()
    
    if success:
        print(f"[SUCCESS] Save data created successfully!")
        print(f"[INFO] Save location: {save_system.save_path}")
        print(f"[INFO] Current money: {save_system.get_money()}G")
        
        # 統計情報も表示
        player_stats = save_system.get_player_stats()
        print(f"[INFO] Games played: {player_stats['games_played']}")
        print(f"[INFO] Total playtime: {player_stats['total_playtime']}s")
        
        # 武器統計も表示
        weapon_stats = save_system.get_weapon_stats()
        print(f"[INFO] Weapon selection stats: {weapon_stats}")
        
        return True
    else:
        print("[ERROR] Failed to create save data!")
        return False

if __name__ == "__main__":
    create_initial_save()
