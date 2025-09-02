"""
CSVマップ読み込みシステム
80x45マスのマップデータを読み込み、描画する
"""

import pygame
import csv
import os
from constants import *

class MapLoader:
    def __init__(self):
        self.map_data = []
        self.tile_size = TEST_TILE_SIZE
        self.map_width = 0
        self.map_height = 0
        
        # タイル定義（数字 -> 色のマッピング）
        self.tile_colors = {
            0: MOREDARK_GRAY,    # 暗いグレー（デフォルト）
            1: DARK_GRAY,        # 濃いグレー
            2: GRAY,             # 通常グレー  
            3: LIGHT_GRAY,       # 薄いグレー
            4: (64, 32, 16),     # 茶色（土）
            5: (32, 64, 32),     # 濃い緑（森）
            6: (64, 64, 32),     # 黄土色（道）
            7: (32, 32, 64),     # 青系（水）
            8: (64, 16, 16),     # 赤系（危険地帯）
            9: (48, 48, 48),     # 中間グレー
        }
    
    def load_csv_map(self, csv_file_path):
        """CSVファイルからマップデータを読み込む"""
        try:
            if not os.path.exists(csv_file_path):
                print(f"[WARNING] Map file not found: {csv_file_path}")
                return self.generate_default_map()
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.map_data = []
                for row in reader:
                    # 各要素を整数に変換
                    int_row = []
                    for cell in row:
                        try:
                            int_row.append(int(cell.strip()))
                        except ValueError:
                            int_row.append(0)  # 変換できない場合は0
                    self.map_data.append(int_row)
            
            if self.map_data:
                self.map_height = len(self.map_data)
                self.map_width = len(self.map_data[0]) if self.map_data[0] else 0
                print(f"[INFO] Map loaded: {self.map_width}x{self.map_height} tiles")
                return True
            else:
                print("[WARNING] Empty map data, using default")
                return self.generate_default_map()
                
        except Exception as e:
            print(f"[ERROR] Failed to load map: {e}")
            return self.generate_default_map()
    
    def generate_default_map(self):
        """デフォルトマップ（市松模様）を生成"""
        expected_width = WORLD_WIDTH // self.tile_size  # 80
        expected_height = WORLD_HEIGHT // self.tile_size  # 45
        
        self.map_data = []
        for y in range(expected_height):
            row = []
            for x in range(expected_width):
                # 市松模様パターン
                if (x + y) % 2 == 0:
                    row.append(1)  # DARK_GRAY
                else:
                    row.append(0)  # MOREDARK_GRAY
            self.map_data.append(row)
        
        self.map_width = expected_width
        self.map_height = expected_height
        print(f"[INFO] Generated default map: {self.map_width}x{self.map_height} tiles")
        return True
    
    def get_tile_at(self, world_x, world_y):
        """ワールド座標からタイル番号を取得"""
        tile_x = int(world_x // self.tile_size)
        tile_y = int(world_y // self.tile_size)
        
        if (0 <= tile_y < self.map_height and 
            0 <= tile_x < len(self.map_data[tile_y])):
            return self.map_data[tile_y][tile_x]
        else:
            return 0  # 範囲外はデフォルトタイル
    
    def draw_map(self, screen, camera_x, camera_y):
        """マップを描画"""
        if not self.map_data:
            return
        
        # 描画範囲を計算
        start_tile_x = max(0, int(camera_x // self.tile_size))
        end_tile_x = min(self.map_width, int((camera_x + SCREEN_WIDTH) // self.tile_size) + 1)
        start_tile_y = max(0, int(camera_y // self.tile_size))
        end_tile_y = min(self.map_height, int((camera_y + SCREEN_HEIGHT) // self.tile_size) + 1)
        
        # タイルを描画
        for tile_y in range(start_tile_y, end_tile_y):
            if tile_y >= len(self.map_data):
                continue
            row = self.map_data[tile_y]
            
            for tile_x in range(start_tile_x, end_tile_x):
                if tile_x >= len(row):
                    continue
                
                tile_id = row[tile_x]
                color = self.tile_colors.get(tile_id, self.tile_colors[0])
                
                # スクリーン座標を計算
                screen_x = tile_x * self.tile_size - camera_x
                screen_y = tile_y * self.tile_size - camera_y
                
                # タイルを描画
                pygame.draw.rect(screen, color, 
                               (screen_x, screen_y, self.tile_size, self.tile_size))
    
    def create_sample_csv(self, output_path):
        """サンプルCSVファイルを作成"""
        expected_width = WORLD_WIDTH // self.tile_size  # 80
        expected_height = WORLD_HEIGHT // self.tile_size  # 45
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                for y in range(expected_height):
                    row = []
                    for x in range(expected_width):
                        # サンプルパターン：境界線、中央部、角にアクセント
                        if (x == 0 or x == expected_width-1 or 
                            y == 0 or y == expected_height-1):
                            row.append(8)  # 境界は赤系
                        elif (x % 10 == 0 or y % 10 == 0):
                            row.append(6)  # グリッド線は黄土色
                        elif (abs(x - expected_width//2) < 3 and 
                              abs(y - expected_height//2) < 3):
                            row.append(5)  # 中央は緑系
                        elif (x + y) % 2 == 0:
                            row.append(1)  # 市松模様
                        else:
                            row.append(0)
                    writer.writerow(row)
                    
            print(f"[INFO] Sample CSV created: {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to create sample CSV: {e}")
            return False
