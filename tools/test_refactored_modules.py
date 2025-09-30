"""
リファクタリングされた新モジュールのテストスクリプト
EventHandler, GameInitializer, DebugManagerの基本動作を確認
"""

import pygame
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.event_handler import EventHandler
from core.game_initializer import GameInitializer
from core.debug_manager import DebugManager
from constants import *

def test_event_handler():
    """EventHandlerクラスのテスト"""
    print("\n=== EventHandler Test ===")
    
    try:
        # 初期化
        event_handler = EventHandler()
        print("✅ EventHandler初期化成功")
        
        # メソッドの存在確認
        assert hasattr(event_handler, 'handle_window_events')
        print("✅ handle_window_events メソッド存在確認")
        
        assert hasattr(event_handler, 'handle_keyboard_navigation')
        print("✅ handle_keyboard_navigation メソッド存在確認")
        
        assert hasattr(event_handler, 'handle_mouse_selection')
        print("✅ handle_mouse_selection メソッド存在確認")
        
        assert hasattr(event_handler, '_handle_grid_navigation')
        print("✅ _handle_grid_navigation メソッド存在確認")
        
        assert hasattr(event_handler, '_handle_linear_navigation')
        print("✅ _handle_linear_navigation メソッド存在確認")
        
        return True
    except Exception as e:
        print(f"❌ EventHandler Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_initializer():
    """GameInitializerクラスのテスト"""
    print("\n=== GameInitializer Test ===")
    
    try:
        # Pygame初期化が必要
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        
        initializer = GameInitializer()
        print("✅ GameInitializer初期化成功")
        
        # メソッドの存在確認
        assert hasattr(initializer, 'initialize_pygame')
        print("✅ initialize_pygame メソッド存在確認")
        
        assert hasattr(initializer, 'create_display')
        print("✅ create_display メソッド存在確認")
        
        assert hasattr(initializer, 'load_resources')
        print("✅ load_resources メソッド存在確認")
        
        assert hasattr(initializer, 'initialize_audio')
        print("✅ initialize_audio メソッド存在確認")
        
        assert hasattr(initializer, 'initialize_map')
        print("✅ initialize_map メソッド存在確認")
        
        assert hasattr(initializer, 'initialize_spawn_manager')
        print("✅ initialize_spawn_manager メソッド存在確認")
        
        assert hasattr(initializer, 'full_initialization')
        print("✅ full_initialization メソッド存在確認")
        
        pygame.quit()
        return True
    except Exception as e:
        print(f"❌ GameInitializer Test Failed: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        return False


def test_debug_manager():
    """DebugManagerクラスのテスト"""
    print("\n=== DebugManager Test ===")
    
    try:
        # Pygame初期化が必要
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        
        debug_manager = DebugManager()
        print("✅ DebugManager初期化成功")
        
        # デバッグモードの切り替えテスト
        initial_debug_mode = debug_manager.debug_mode
        debug_manager.toggle_debug_mode()
        print(f"✅ デバッグモード切り替え: {initial_debug_mode} -> {debug_manager.debug_mode}")
        
        # メソッドの存在確認
        assert hasattr(debug_manager, 'handle_debug_keys')
        print("✅ handle_debug_keys メソッド存在確認")
        
        assert hasattr(debug_manager, 'toggle_debug_mode')
        print("✅ toggle_debug_mode メソッド存在確認")
        
        assert hasattr(debug_manager, 'toggle_fps_display')
        print("✅ toggle_fps_display メソッド存在確認")
        
        assert hasattr(debug_manager, 'draw_fps')
        print("✅ draw_fps メソッド存在確認")
        
        assert hasattr(debug_manager, 'draw_debug_info')
        print("✅ draw_debug_info メソッド存在確認")
        
        assert hasattr(debug_manager, 'should_show_debug_visuals')
        print("✅ should_show_debug_visuals メソッド存在確認")
        
        pygame.quit()
        return True
    except Exception as e:
        print(f"❌ DebugManager Test Failed: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        return False


def main():
    """テストの実行"""
    print("=" * 60)
    print("リファクタリングされたモジュールのテスト")
    print("=" * 60)
    
    results = []
    
    # 各テストを実行
    results.append(("EventHandler", test_event_handler()))
    results.append(("GameInitializer", test_game_initializer()))
    results.append(("DebugManager", test_debug_manager()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20s} : {status}")
    
    # 総合結果
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 すべてのテストが成功しました！")
        print("新しいモジュールは正常に動作しています。")
    else:
        print("⚠️ 一部のテストが失敗しました。")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
