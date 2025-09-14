"""
PyInstaller対応のファイルパス管理ユーティリティ
macでのビルド時の権限問題を解決するため、適切な書き込み可能ディレクトリを取得
"""

import os
import sys
import platform
from pathlib import Path


def get_app_data_dir():
    """OSごとに適切なアプリケーションデータディレクトリを取得"""
    app_name = "VanSurv"
    
    system = platform.system()
    
    if system == "Windows":
        base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base_dir, app_name)
    elif system == "Darwin":  # macOS
        home = os.path.expanduser('~')
        return os.path.join(home, 'Library', 'Application Support', app_name)
    else:  # Linux and others
        xdg_data_home = os.environ.get('XDG_DATA_HOME')
        if xdg_data_home:
            return os.path.join(xdg_data_home, app_name)
        else:
            home = os.path.expanduser('~')
            return os.path.join(home, '.local', 'share', app_name)


def get_user_documents_dir():
    """ユーザーのドキュメントフォルダ内にゲーム用ディレクトリを取得"""
    app_name = "VanSurv"
    
    system = platform.system()
    
    if system == "Windows":
        documents = os.path.join(os.path.expanduser('~'), 'Documents')
        return os.path.join(documents, app_name)
    elif system == "Darwin":  # macOS
        documents = os.path.join(os.path.expanduser('~'), 'Documents')
        return os.path.join(documents, app_name)
    else:  # Linux
        documents = os.path.join(os.path.expanduser('~'), 'Documents')
        if os.path.exists(documents):
            return os.path.join(documents, app_name)
        else:
            return os.path.join(os.path.expanduser('~'), app_name)


def ensure_directory_exists(directory_path):
    """ディレクトリが存在しない場合は作成し、書き込み権限があるかチェック"""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        
        # 書き込み権限をテスト
        test_file = os.path.join(directory_path, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except Exception:
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to create directory {directory_path}: {e}")
        return False


def get_safe_file_path(relative_path, use_documents=False):
    """PyInstaller対応の安全なファイルパスを取得"""
    if getattr(sys, 'frozen', False):
        # PyInstallerでバンドルされている場合
        if use_documents:
            base_dir = get_user_documents_dir()
        else:
            base_dir = get_app_data_dir()
    else:
        # 開発環境の場合は元の相対パスを維持
        current_dir = os.path.dirname(os.path.abspath(__file__))
        game_root = os.path.dirname(current_dir)  # utils の親ディレクトリ
        base_dir = game_root
    
    # パスを結合
    full_path = os.path.join(base_dir, relative_path)
    
    # ディレクトリ部分を確保
    directory = os.path.dirname(full_path)
    if directory:
        ensure_directory_exists(directory)
    
    return full_path


def get_log_file_path(filename="performance_log.csv"):
    """ログファイルの絶対パスを取得"""
    return get_safe_file_path(f"logs/{filename}", use_documents=False)


def get_save_file_path(filename="savedata.json"):
    """セーブファイルの絶対パスを取得"""
    return get_safe_file_path(f"save/{filename}", use_documents=True)