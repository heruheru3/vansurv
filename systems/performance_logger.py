"""
パフォーマンス測定用ログシステム
FPS、エンティティ数、処理時間などを定期的にCSVファイルに記録
PyInstaller対応（macでの権限問題解決）
"""

import os
import csv
import time
from datetime import datetime
from collections import deque
from constants import *
from utils.file_paths import get_log_file_path, ensure_directory_exists

# psutilの安全なインポート
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[WARNING] psutil not available - CPU usage will be 0")


class PerformanceLogger:
    """パフォーマンス測定データをCSVファイルに記録するクラス"""
    
    def __init__(self, log_file=None, max_entries=PERFORMANCE_LOG_MAX_ENTRIES):
        self.log_file = get_log_file_path("performance_log.csv") if log_file is None else log_file
        self.max_entries = max_entries
        self.enabled = ENABLE_PERFORMANCE_LOG
        self.last_log_time = 0.0
        self.log_interval = PERFORMANCE_LOG_INTERVAL
        
        # ログデータのバッファ（メモリ効率のため）
        self.log_buffer = deque(maxlen=max_entries)
        
        # CSV列の定義
        self.csv_headers = [
            'timestamp',           # タイムスタンプ
            'game_time',          # ゲーム内時間
            'fps',                # FPS
            'frame_time_ms',      # フレーム時間(ms)
            'enemies_count',      # 敵の数
            'particles_count',    # パーティクル数
            'gems_count',         # ジェム数
            'projectiles_count',  # 弾丸数
            'particle_update_ms', # パーティクル更新時間(ms)
            'enemy_update_ms',    # 敵更新時間(ms)
            'collision_check_ms', # 衝突判定時間(ms)
            'render_time_ms',     # 描画時間(ms)
            'parallel_enabled',   # 並列処理有効フラグ
            'parallel_threads',   # 並列処理スレッド数
            'cpu_usage_percent',  # CPU使用率(%)
            'cpu_cores_used',     # 使用中CPUコア数
            'cpu_efficiency',     # CPU効率(%)
            'memory_usage_mb',    # メモリ使用量(MB)概算
            'total_processing_ms' # 総処理時間(ms)
        ]
        
        # ログファイルの初期化
        self._initialize_log_file()

    def _initialize_log_file(self):
        """ログファイルとディレクトリを初期化"""
        try:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not ensure_directory_exists(log_dir):
                print(f"[ERROR] Failed to create log directory: {log_dir}")
                self.enabled = False
                return

            # 古いログファイルは削除
            if os.path.exists(self.log_file):
                try:
                    os.remove(self.log_file)
                except PermissionError as e:
                    print(f"[WARNING] Cannot remove existing log file: {e}")

            # ログファイル初期化
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.csv_headers)
                
                session_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([f'# New session started at {session_start}'] + [''] * (len(self.csv_headers) - 1))
            
            print(f"[INFO] Performance log initialized: {self.log_file}")
                
        except (PermissionError, OSError) as e:
            print(f"[ERROR] Cannot write to log file {self.log_file}: {e}")
            print("[INFO] Performance logging will be disabled")
            self.enabled = False
    
    def toggle_logging(self):
        """ログ記録のON/OFF切り替え"""
        self.enabled = not self.enabled
        status = "enabled" if self.enabled else "disabled"
        print(f"[INFO] Performance logging {status}")
        return self.enabled
    
    def should_log(self, current_time):
        """ログを記録すべきかどうかを判定"""
        if not self.enabled:
            return False
        
        if current_time - self.last_log_time >= self.log_interval:
            self.last_log_time = current_time
            return True
        
        return False
    
    def log_performance(self, performance_data, game_data, fps_data):
        """パフォーマンスデータをログに記録"""
        if not self.enabled:
            return
        
        try:
            # 現在時刻の取得
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # ミリ秒まで
            
            # CPU使用率の取得
            cpu_usage = self._get_cpu_usage()
            
            # メモリ使用量の概算（エンティティ数から推定）
            memory_estimate = self._estimate_memory_usage(performance_data)
            
            # 総処理時間の計算
            total_processing = (
                performance_data.get('particle_update_time', 0) +
                performance_data.get('enemy_update_time', 0) +
                performance_data.get('collision_check_time', 0) +
                performance_data.get('render_time', 0)
            )
            
            # ログエントリの作成
            log_entry = [
                timestamp,
                round(game_data.get('game_time', 0), 2),
                round(fps_data.get('fps', 0), 1),
                round(performance_data.get('frame_time', 0), 1),
                performance_data['entities_count'].get('enemies', 0),
                performance_data['entities_count'].get('particles', 0),
                performance_data['entities_count'].get('gems', 0),
                performance_data['entities_count'].get('projectiles', 0),
                round(performance_data.get('particle_update_time', 0), 1),
                round(performance_data.get('enemy_update_time', 0), 1),
                round(performance_data.get('collision_check_time', 0), 1),
                round(performance_data.get('render_time', 0), 1),
                1 if performance_data.get('parallel_enabled', False) else 0,
                performance_data.get('parallel_threads', 0),
                round(cpu_usage, 1),
                performance_data.get('cpu_cores_used', 0),
                round(performance_data.get('cpu_efficiency', 0), 1),
                round(memory_estimate, 1),
                round(total_processing, 1)
            ]
            
            # バッファに追加
            self.log_buffer.append(log_entry)
            
            # ファイルに書き込み（バッファリング）
            self._write_to_file(log_entry)
            
        except Exception as e:
            print(f"[ERROR] Failed to log performance data: {e}")
    
    def _get_cpu_usage(self):
        """現在のCPU使用率を取得"""
        if not PSUTIL_AVAILABLE:
            return 0.0
        try:
            # 短時間での測定（非ブロッキング）
            cpu_percent = psutil.cpu_percent(interval=None)
            return cpu_percent
        except Exception as e:
            # psutilエラー時は0を返す
            return 0.0
    
    def _estimate_memory_usage(self, performance_data):
        """エンティティ数からメモリ使用量を概算（MB）"""
        try:
            entities = performance_data['entities_count']
            
            # 各エンティティの概算メモリ使用量（KB）
            enemy_size = 2.0      # 敵1体あたり約2KB
            particle_size = 0.5   # パーティクル1個あたり約0.5KB
            gem_size = 1.0        # ジェム1個あたり約1KB
            projectile_size = 0.3 # 弾丸1個あたり約0.3KB
            
            total_kb = (
                entities.get('enemies', 0) * enemy_size +
                entities.get('particles', 0) * particle_size +
                entities.get('gems', 0) * gem_size +
                entities.get('projectiles', 0) * projectile_size
            )
            
            # 基本メモリ使用量（ゲーム本体など）を加算
            base_memory = 50.0  # 基本50MB
            
            return base_memory + (total_kb / 1024.0)  # MBに変換
            
        except Exception:
            return 0.0
    
    def _write_to_file(self, log_entry):
        """ログエントリをファイルに書き込み"""
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(log_entry)
                
        except Exception as e:
            print(f"[WARNING] Failed to write log entry: {e}")
    
    def flush_buffer(self):
        """バッファの内容を全てファイルに書き込み"""
        if not self.log_buffer:
            return
        
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for entry in self.log_buffer:
                    writer.writerow(entry)
            
            print(f"[INFO] Flushed {len(self.log_buffer)} log entries to file")
            self.log_buffer.clear()
            
        except Exception as e:
            print(f"[ERROR] Failed to flush log buffer: {e}")
    
    def get_log_summary(self):
        """ログの概要情報を取得"""
        if not self.log_buffer:
            return "No log data available"
        
        try:
            # 最新のエントリ
            latest = self.log_buffer[-1]
            
            # 平均FPS計算（最近10エントリ）
            recent_entries = list(self.log_buffer)[-10:]
            avg_fps = sum(float(entry[2]) for entry in recent_entries) / len(recent_entries)
            
            summary = f"""Performance Log Summary:
- Total entries: {len(self.log_buffer)}
- Latest FPS: {latest[2]}
- Average FPS (last 10): {avg_fps:.1f}
- Latest entities: E:{latest[4]} P:{latest[5]} G:{latest[6]} B:{latest[7]}
- Memory estimate: {latest[13]}MB
- Log file: {self.log_file}"""
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {e}"
    
    def close(self):
        """ログシステムを終了（バッファをフラッシュ）"""
        if self.enabled and self.log_buffer:
            self.flush_buffer()
            
            # セッション終了の記録
            try:
                with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    session_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    writer.writerow([f'# Session ended at {session_end}'] + [''] * (len(self.csv_headers) - 1))
                    
                print(f"[INFO] Performance logging session ended")
                
            except Exception as e:
                print(f"[ERROR] Failed to close performance log: {e}")