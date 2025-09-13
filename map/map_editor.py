"""
VanSurv マップエディタ
CSVマップファイルをGUIで編集できるツール
"""

import pygame
import csv
import os
import sys
from typing import Optional

# プロジェクトルートの constants.py を読み込み
try:
    from constants import *
    print(f"[DEBUG] Using CSV_MAP_FILE from constants: {CSV_MAP_FILE}")
except ImportError:
    # デフォルト設定
    SCREEN_WIDTH = 1440
    SCREEN_HEIGHT = 810
    MAP_TILES_WIDTH = 80
    MAP_TILES_HEIGHT = 45
    TEST_TILE_SIZE = 64
    CSV_MAP_FILE = "map/stage_map.csv"  # 正しいパスに修正
    print(f"[DEBUG] Using fallback CSV_MAP_FILE: {CSV_MAP_FILE}")

class MapEditor:
    def __init__(self):
        pygame.init()
        
        # 画面設定（さらに大きな画面サイズ）
        self.screen_width = min(1920, SCREEN_WIDTH * 1.5)  # さらに大きく
        self.screen_height = min(1200, SCREEN_HEIGHT * 1.5)  # さらに大きく
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("VanSurv Map Editor")
        
        # マップ設定
        self.map_width = MAP_TILES_WIDTH
        self.map_height = MAP_TILES_HEIGHT
        self.tile_size = 20  # 大きなタイルサイズ（12 → 20）
        
        # マップデータ
        self.map_data = []
        self.init_empty_map()
        
        # 履歴の初期状態を保存は __init__の最後で行う
        
        # カメラ・表示設定
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # 編集設定
        self.current_tile = 0
        self.is_painting = False
        self.is_erasing = False
        self.brush_size = 1  # ブラシサイズ
        
        # UI設定（さらに広いUI領域）
        self.ui_width = 320  # さらに広いUI領域（280 → 320）
        self.map_area_width = self.screen_width - self.ui_width
        
        # ツールモード
        self.tool_mode = "paint"  # "paint", "fill", "line", "rect"
        self.fill_start_pos = None
        self.line_start_pos = None
        
        # アンドゥ・リドゥ
        self.history = []
        self.history_index = -1
        self.max_history = 50
        
        # 色定義
        self.tile_colors = {
            0: (32, 32, 32),     # 暗いグレー（デフォルト）
            1: (64, 64, 64),     # 濃いグレー
            2: (128, 128, 128),  # 通常グレー  
            3: (192, 192, 192),  # 薄いグレー
            4: (139, 69, 19),    # 茶色（土）
            5: (34, 139, 34),    # 緑（森）
            6: (218, 165, 32),   # 黄土色（道）
            7: (30, 144, 255),   # 青（水）
            8: (220, 20, 60),    # 赤（危険地帯）
            9: (105, 105, 105),  # 中間グレー
        }
        
        # タイル説明（ツールチップ用）
        self.tile_descriptions = {
            0: "Empty Ground - Passable",
            1: "Dark Ground - Passable",
            2: "Normal Ground - Passable", 
            3: "Light Ground - Passable",
            4: "Dirt/Soil - Passable",
            5: "Forest/Trees - Blocked",
            6: "Path/Road - Passable", 
            7: "Water/Lake - Blocked",
            8: "Danger/Lava - Blocked",
            9: "Stone/Rock - Blocked"
        }
        
        # フォント（文字化け対策でシステムフォントを使用）
        try:
            # Windowsの場合、日本語対応フォントを試す
            self.font = pygame.font.SysFont('msgothic', 28)        # メイリオやMSゴシック
            self.small_font = pygame.font.SysFont('msgothic', 22)  
            self.tiny_font = pygame.font.SysFont('msgothic', 18)   
        except:
            # フォールバック：デフォルトフォント
            self.font = pygame.font.Font(None, 32)        
            self.small_font = pygame.font.Font(None, 24)  
            self.tiny_font = pygame.font.Font(None, 20)   
        
        # 状態
        self.running = True
        self.clock = pygame.time.Clock()
        
        # マウス関連
        self.mouse_pos = (0, 0)
        self.hovered_tile = None  # マウスオーバー中のタイルID
        
        # 起動時にマップファイルを読み込み
        self.load_existing_map()
        
        # 履歴の初期状態を保存
        self.save_to_history()
        
    def save_to_history(self):
        """現在のマップ状態を履歴に保存"""
        if self.history_index < len(self.history) - 1:
            # リドゥ履歴があったら削除
            self.history = self.history[:self.history_index + 1]
        
        # マップデータのディープコピーを保存
        map_copy = [row[:] for row in self.map_data]
        self.history.append(map_copy)
        
        # 最大履歴数を超えた場合、古いものを削除
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1
    
    def undo(self):
        """アンドゥ"""
        if self.history_index > 0:
            self.history_index -= 1
            self.map_data = [row[:] for row in self.history[self.history_index]]
    
    def redo(self):
        """リドゥ"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.map_data = [row[:] for row in self.history[self.history_index]]
    
    def flood_fill(self, x: int, y: int, new_tile: int):
        """塗りつぶしツール"""
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return
        
        original_tile = self.map_data[y][x]
        if original_tile == new_tile:
            return
        
        # BFS で塗りつぶし
        queue = [(x, y)]
        visited = set()
        
        while queue:
            cx, cy = queue.pop(0)
            if (cx, cy) in visited:
                continue
            if cx < 0 or cx >= self.map_width or cy < 0 or cy >= self.map_height:
                continue
            if self.map_data[cy][cx] != original_tile:
                continue
            
            visited.add((cx, cy))
            self.map_data[cy][cx] = new_tile
            
            # 隣接する4方向をキューに追加
            queue.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int, tile: int):
        """直線描画"""
        # Bresenhamアルゴリズムで直線を描画
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                self.map_data[y][x] = tile
            
            if x == x2 and y == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def draw_rect(self, x1: int, y1: int, x2: int, y2: int, tile: int, filled: bool = False):
        """矩形描画"""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if 0 <= x < self.map_width and 0 <= y < self.map_height:
                    if filled or x == min_x or x == max_x or y == min_y or y == max_y:
                        self.map_data[y][x] = tile

    def init_empty_map(self):
        """空のマップを初期化"""
        self.map_data = []
        for y in range(self.map_height):
            row = [0] * self.map_width
            self.map_data.append(row)
    
    def load_existing_map(self):
        """起動時に既存のマップファイルを読み込む"""
        import os
        
        # 複数のパスを試す
        possible_paths = [
            CSV_MAP_FILE,                    # "map/stage_map.csv"
            "stage_map.csv",                 # カレントディレクトリ内
            os.path.join("..", CSV_MAP_FILE), # 上位ディレクトリから
        ]
        
        for map_path in possible_paths:
            try:
                if os.path.exists(map_path) and self.load_csv_map(map_path):
                    print(f"[INFO] Loaded existing map from: {map_path}")
                    return
            except Exception as e:
                print(f"[DEBUG] Could not load {map_path}: {e}")
        
        # どのパスも失敗した場合は空のマップで開始
        print("[INFO] No existing map found, starting with empty map")
        print(f"[DEBUG] Searched paths: {possible_paths}")
        print(f"[DEBUG] Current working directory: {os.getcwd()}")
        self.init_empty_map()
    
    def load_csv_map(self, filename: str) -> bool:
        """CSVファイルからマップを読み込み"""
        import os
        
        # ファイルの存在確認
        if not os.path.exists(filename):
            print(f"[WARNING] Map file not found: {filename}")
            return False
            
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.map_data = []
                for row in reader:
                    int_row = []
                    for cell in row:
                        try:
                            int_row.append(int(cell.strip()))
                        except ValueError:
                            int_row.append(0)
                    # 幅を調整
                    while len(int_row) < self.map_width:
                        int_row.append(0)
                    int_row = int_row[:self.map_width]
                    self.map_data.append(int_row)
                
                # 高さを調整
                while len(self.map_data) < self.map_height:
                    self.map_data.append([0] * self.map_width)
                self.map_data = self.map_data[:self.map_height]
                
            print(f"[INFO] Map loaded successfully: {filename} ({len(self.map_data)}x{len(self.map_data[0]) if self.map_data else 0})")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load map: {e}")
            return False
    
    def save_csv_map(self, filename: str) -> bool:
        """CSVファイルにマップを保存"""
        try:
            import os
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                for row in self.map_data:
                    writer.writerow(row)
            print(f"[INFO] Map saved successfully: {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save map: {e}")
            return False
    
    def save_as_dialog(self):
        """名前を付けて保存のダイアログ（簡易版）"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"map/backup_map_{timestamp}.csv"
        
        if self.save_csv_map(backup_filename):
            print(f"[INFO] Backup saved as: {backup_filename}")
        
        # メインファイルも保存
        self.save_csv_map(CSV_MAP_FILE)
    
    def get_tile_at_screen(self, screen_x: int, screen_y: int) -> Optional[tuple]:
        """スクリーン座標からタイル座標を取得"""
        if screen_x >= self.map_area_width:
            return None
            
        # マップ座標に変換
        map_x = int((screen_x + self.camera_x) / self.tile_size)
        map_y = int((screen_y + self.camera_y) / self.tile_size)
        
        if 0 <= map_x < self.map_width and 0 <= map_y < self.map_height:
            return (map_x, map_y)
        return None
    
    def paint_tile(self, tile_x: int, tile_y: int, tile_id: int):
        """指定座標にタイルをペイント"""
        if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
            self.map_data[tile_y][tile_x] = tile_id
    
    def paint_tile_with_brush(self, tile_x: int, tile_y: int, tile_id: int):
        """ブラシサイズを考慮してタイルを塗る"""
        half_brush = self.brush_size // 2
        for dy in range(-half_brush, half_brush + 1):
            for dx in range(-half_brush, half_brush + 1):
                # 円形ブラシにする場合
                if dx*dx + dy*dy <= half_brush*half_brush + half_brush:
                    self.paint_tile(tile_x + dx, tile_y + dy, tile_id)
    
    def check_palette_click(self, mouse_pos):
        """パレットがクリックされたかチェックし、該当するタイルIDを返す"""
        if not hasattr(self, 'palette_rects'):
            return None
            
        for tile_id, rect in self.palette_rects.items():
            if rect.collidepoint(mouse_pos):
                return tile_id
        return None
    
    def check_palette_hover(self, mouse_pos):
        """パレットにマウスがホバーしているかチェックし、該当するタイルIDを返す"""
        if not hasattr(self, 'palette_rects'):
            return None
            
        for tile_id, rect in self.palette_rects.items():
            if rect.collidepoint(mouse_pos):
                return tile_id
        return None
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # アンドゥ・リドゥ
                elif event.key == pygame.K_z and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.redo()
                    else:
                        self.undo()
                elif event.key == pygame.K_y and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.redo()
                
                # 数字キーでタイル選択
                elif pygame.K_0 <= event.key <= pygame.K_9:
                    self.current_tile = event.key - pygame.K_0
                
                # ツールモード選択
                elif event.key == pygame.K_p:
                    self.tool_mode = "paint"
                elif event.key == pygame.K_f:
                    self.tool_mode = "fill"
                elif event.key == pygame.K_l:
                    self.tool_mode = "line"
                elif event.key == pygame.K_r:
                    self.tool_mode = "rect"
                
                # ブラシサイズ変更
                elif event.key == pygame.K_MINUS:
                    self.brush_size = max(1, self.brush_size - 1)
                elif event.key == pygame.K_EQUALS:  # プラスキー
                    self.brush_size = min(5, self.brush_size + 1)
                
                # セーブ・ロード
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        # Ctrl+Shift+S: 名前を付けて保存
                        self.save_as_dialog()
                    else:
                        # Ctrl+S: 通常の保存
                        self.save_csv_map(CSV_MAP_FILE)
                elif event.key == pygame.K_o and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.load_csv_map(CSV_MAP_FILE)
                
                # 全クリア
                elif event.key == pygame.K_c and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.init_empty_map()
                    self.save_to_history()
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    # まずパレットクリックをチェック
                    clicked_tile = self.check_palette_click(event.pos)
                    if clicked_tile is not None:
                        self.current_tile = clicked_tile
                        print(f"[INFO] Selected tile: {clicked_tile}")
                    else:
                        # マップエリアのクリック処理
                        pos = self.get_tile_at_screen(event.pos[0], event.pos[1])
                        if pos:
                            tile_x, tile_y = pos
                            
                            if self.tool_mode == "paint":
                                self.is_painting = True
                                self.paint_tile_with_brush(tile_x, tile_y, self.current_tile)
                            elif self.tool_mode == "fill":
                                self.flood_fill(tile_x, tile_y, self.current_tile)
                                self.save_to_history()
                            elif self.tool_mode == "line":
                                if self.line_start_pos is None:
                                    self.line_start_pos = (tile_x, tile_y)
                                else:
                                    self.draw_line(self.line_start_pos[0], self.line_start_pos[1], 
                                                 tile_x, tile_y, self.current_tile)
                                    self.line_start_pos = None
                                    self.save_to_history()
                            elif self.tool_mode == "rect":
                                if self.fill_start_pos is None:
                                    self.fill_start_pos = (tile_x, tile_y)
                                else:
                                    keys = pygame.key.get_pressed()
                                    filled = keys[pygame.K_LSHIFT]
                                    self.draw_rect(self.fill_start_pos[0], self.fill_start_pos[1], 
                                                 tile_x, tile_y, self.current_tile, filled)
                                    self.fill_start_pos = None
                                    self.save_to_history()
                
                elif event.button == 3:  # 右クリック
                    pos = self.get_tile_at_screen(event.pos[0], event.pos[1])
                    if pos:
                        self.is_erasing = True
                        self.paint_tile_with_brush(pos[0], pos[1], 0)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.is_painting:
                        self.save_to_history()
                    self.is_painting = False
                elif event.button == 3:
                    if self.is_erasing:
                        self.save_to_history()
                    self.is_erasing = False
            
            elif event.type == pygame.MOUSEMOTION:
                # マウス位置を更新
                self.mouse_pos = event.pos
                
                # パレットホバー状態を更新
                self.hovered_tile = self.check_palette_hover(event.pos)
                
                # ドラッグ中の描画
                if self.is_painting or self.is_erasing:
                    pos = self.get_tile_at_screen(event.pos[0], event.pos[1])
                    if pos:
                        tile_id = self.current_tile if self.is_painting else 0
                        self.paint_tile_with_brush(pos[0], pos[1], tile_id)
            
            elif event.type == pygame.MOUSEWHEEL:
                # カメラ移動（上下）
                self.camera_y -= event.y * 20
                self.camera_y = max(0, min(self.camera_y, 
                                          max(0, self.map_height * self.tile_size - self.screen_height)))
        
        # キーボード入力（カメラ移動）
        keys = pygame.key.get_pressed()
        move_speed = 5
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.camera_x -= move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.camera_x += move_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.camera_y -= move_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.camera_y += move_speed
        
        # カメラ位置制限
        self.camera_x = max(0, min(self.camera_x, 
                                  max(0, self.map_width * self.tile_size - self.map_area_width)))
        self.camera_y = max(0, min(self.camera_y, 
                                  max(0, self.map_height * self.tile_size - self.screen_height)))
    
    def draw_map(self):
        """マップを描画"""
        # 描画範囲を計算
        start_x = max(0, int(self.camera_x / self.tile_size))
        end_x = min(self.map_width, int((self.camera_x + self.map_area_width) / self.tile_size) + 1)
        start_y = max(0, int(self.camera_y / self.tile_size))
        end_y = min(self.map_height, int((self.camera_y + self.screen_height) / self.tile_size) + 1)
        
        # タイルを描画
        for tile_y in range(start_y, end_y):
            for tile_x in range(start_x, end_x):
                if tile_y < len(self.map_data) and tile_x < len(self.map_data[tile_y]):
                    tile_id = self.map_data[tile_y][tile_x]
                    color = self.tile_colors.get(tile_id, self.tile_colors[0])
                    
                    screen_x = tile_x * self.tile_size - self.camera_x
                    screen_y = tile_y * self.tile_size - self.camera_y
                    
                    rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                    if rect.right > 0 and rect.bottom > 0 and rect.left < self.map_area_width:
                        pygame.draw.rect(self.screen, color, rect)
        
        # マウスプレビューを描画
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] < self.map_area_width:
            tile_pos = self.get_tile_at_screen(mouse_pos[0], mouse_pos[1])
            if tile_pos:
                self.draw_preview(tile_pos[0], tile_pos[1])
    
    def draw_preview(self, tile_x: int, tile_y: int):
        """マウス位置のプレビューを描画"""
        if self.tool_mode == "paint":
            # ブラシプレビュー
            half_brush = self.brush_size // 2
            for dy in range(-half_brush, half_brush + 1):
                for dx in range(-half_brush, half_brush + 1):
                    if dx*dx + dy*dy <= half_brush*half_brush + half_brush:
                        px, py = tile_x + dx, tile_y + dy
                        if 0 <= px < self.map_width and 0 <= py < self.map_height:
                            screen_x = px * self.tile_size - self.camera_x
                            screen_y = py * self.tile_size - self.camera_y
                            rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                            pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)
        
        elif self.tool_mode == "line" and self.line_start_pos:
            # 線のプレビュー
            start_x, start_y = self.line_start_pos
            self.draw_line_preview(start_x, start_y, tile_x, tile_y)
        
        elif self.tool_mode == "rect" and self.fill_start_pos:
            # 矩形のプレビュー
            start_x, start_y = self.fill_start_pos
            self.draw_rect_preview(start_x, start_y, tile_x, tile_y)
    
    def draw_line_preview(self, x1: int, y1: int, x2: int, y2: int):
        """直線プレビューを描画"""
        points = self.get_line_points(x1, y1, x2, y2)
        for px, py in points:
            if 0 <= px < self.map_width and 0 <= py < self.map_height:
                screen_x = px * self.tile_size - self.camera_x
                screen_y = py * self.tile_size - self.camera_y
                rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)
    
    def draw_rect_preview(self, x1: int, y1: int, x2: int, y2: int):
        """矩形プレビューを描画"""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if 0 <= x < self.map_width and 0 <= y < self.map_height:
                    # 枠線のみ、または塗りつぶし（Shiftキーで判定）
                    keys = pygame.key.get_pressed()
                    filled = keys[pygame.K_LSHIFT]
                    if filled or x == min_x or x == max_x or y == min_y or y == max_y:
                        screen_x = x * self.tile_size - self.camera_x
                        screen_y = y * self.tile_size - self.camera_y
                        rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                        color = (0, 255, 0) if filled else (255, 255, 0)
                        pygame.draw.rect(self.screen, color, rect, 2)
    
    def get_line_points(self, x1: int, y1: int, x2: int, y2: int):
        """直線上の点を取得（Bresenhamアルゴリズム）"""
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            points.append((x, y))
            if x == x2 and y == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return points
    
    def draw_tooltip(self):
        """ツールチップを描画"""
        if self.hovered_tile is not None and self.hovered_tile in self.tile_descriptions:
            description = self.tile_descriptions[self.hovered_tile]
            tile_id = self.hovered_tile
            
            # ツールチップテキストを2行に分ける
            line1 = f"Tile {tile_id}: {description.split(' - ')[0]}"
            line2 = f"Movement: {description.split(' - ')[1]}"
            
            # 各行のテキストレンダリング
            text1 = self.tiny_font.render(line1, True, (255, 255, 255))
            text2 = self.tiny_font.render(line2, True, (200, 255, 200))  # 薄緑で移動情報
            
            # 最大幅を計算
            max_width = max(text1.get_width(), text2.get_width())
            total_height = text1.get_height() + text2.get_height() + 4  # 行間
            
            # ツールチップの背景サイズ（余白を付ける）
            bg_width = max_width + 16
            bg_height = total_height + 12
            
            # マウス位置からオフセット
            tooltip_x = self.mouse_pos[0] + 15
            tooltip_y = self.mouse_pos[1] - 40
            
            # 画面外に出ないよう調整
            if tooltip_x + bg_width > self.screen_width:
                tooltip_x = self.mouse_pos[0] - bg_width - 5
            if tooltip_y < 0:
                tooltip_y = self.mouse_pos[1] + 25
            
            # 背景描画（黒背景 + 黄色枠 + 影）
            shadow_rect = pygame.Rect(tooltip_x + 2, tooltip_y + 2, bg_width, bg_height)
            bg_rect = pygame.Rect(tooltip_x, tooltip_y, bg_width, bg_height)
            
            pygame.draw.rect(self.screen, (50, 50, 50), shadow_rect)  # 影
            pygame.draw.rect(self.screen, (30, 30, 30), bg_rect)      # 背景
            pygame.draw.rect(self.screen, (255, 200, 0), bg_rect, 2)  # 枠
            
            # テキスト描画
            text_x = tooltip_x + 8
            text_y = tooltip_y + 6
            self.screen.blit(text1, (text_x, text_y))
            self.screen.blit(text2, (text_x, text_y + text1.get_height() + 2))
    
    def draw_ui(self):
        """UIを描画"""
        # UI背景
        ui_rect = pygame.Rect(self.map_area_width, 0, self.ui_width, self.screen_height)
        pygame.draw.rect(self.screen, (40, 40, 40), ui_rect)
        
        y_offset = 10
        
        # タイトル
        title_text = self.font.render("Map Editor", True, (255, 255, 255))
        self.screen.blit(title_text, (self.map_area_width + 10, y_offset))
        y_offset += 35
        
        # ツールモード
        tool_text = self.small_font.render(f"Tool: {self.tool_mode.upper()}", True, (255, 255, 0))
        self.screen.blit(tool_text, (self.map_area_width + 10, y_offset))
        y_offset += 25
        
        # ブラシサイズ
        brush_text = self.small_font.render(f"Brush Size: {self.brush_size}", True, (255, 255, 255))
        self.screen.blit(brush_text, (self.map_area_width + 10, y_offset))
        y_offset += 25
        
        # 現在のタイル
        current_text = self.small_font.render(f"Current Tile: {self.current_tile}", True, (255, 255, 255))
        self.screen.blit(current_text, (self.map_area_width + 10, y_offset))
        y_offset += 30
        
        # タイルパレット（5個ずつ横並び）
        palette_text = self.small_font.render("Tile Palette (Click to select):", True, (255, 255, 255))
        self.screen.blit(palette_text, (self.map_area_width + 10, y_offset))
        y_offset += 30
        
        # パレット配置用の座標を保存（マウスクリック判定で使用）
        self.palette_rects = {}
        
        for row in range(2):  # 2行
            for col in range(5):  # 5列
                i = row * 5 + col
                if i >= 10:  # タイルは0-9の10種類
                    break
                    
                color = self.tile_colors.get(i, (255, 255, 255))
                x = self.map_area_width + 10 + col * 55  # 55px間隔で横並び
                y = y_offset + row * 45  # 45px間隔で縦並び
                
                rect = pygame.Rect(x, y, 45, 35)  # 少し大きなパレット
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 3 if i == self.current_tile else 1)
                
                # パレット矩形を保存（クリック判定用）
                self.palette_rects[i] = rect
                
                # タイル番号を中央に表示
                num_text = self.small_font.render(str(i), True, (0, 0, 0) if sum(color) > 400 else (255, 255, 255))
                text_rect = num_text.get_rect(center=rect.center)
                self.screen.blit(num_text, text_rect)
        
        y_offset += 90 + 20  # パレット分の高さ + 余白
        
        # 操作説明（コンパクトに整理）
        instructions = [
            "=== CONTROLS ===",
            "Tiles: 0-9 keys / Click palette",
            "Hover: Show tile info",
            "Paint: Left click",  
            "Erase: Right click",
            "Move: WASD/Arrows",
            "Scroll: Mouse wheel",
            "Brush: +/- keys",
            "",
            "=== TOOLS ===", 
            "P: Paint  F: Fill",
            "L: Line   R: Rect",
            "",
            "=== SHORTCUTS ===",
            "Ctrl+Z: Undo",
            "Ctrl+Y: Redo", 
            "Ctrl+S: Save",
            "Ctrl+Shift+S: Backup",
            "Ctrl+O: Load",
            "Ctrl+C: Clear all",
            "ESC: Exit editor",
            "",
            "=== STATUS ===",
            f"History: {self.history_index + 1}/{len(self.history)}",
            f"Map: {len(self.map_data[0]) if self.map_data else 0}x{len(self.map_data)}",
            "",
            "=== TIPS ===",
            "Shift+Rect: Fill mode",
            "Right-click: Quick erase",
            "Hover palette: Show info",
            "",
            "Green = Passable",
            "Red = Blocked terrain"
        ]
        
        for instruction in instructions:
            if instruction:
                # セクションヘッダーは目立たせる
                if instruction.startswith("==="):
                    text = self.small_font.render(instruction, True, (255, 255, 0))  # 黄色
                    self.screen.blit(text, (self.map_area_width + 10, y_offset))
                    y_offset += 28  # 行間を広げる（22 → 28）
                else:
                    # 通常のテキストは小さめのフォント
                    text = self.tiny_font.render(instruction, True, (200, 200, 200))
                    self.screen.blit(text, (self.map_area_width + 15, y_offset))  # 少しインデント
                    y_offset += 22  # 行間を広げる（18 → 22）
            else:
                y_offset += 12  # 空行のスペースも広げる（8 → 12）
        
        # カメラ情報
        y_offset += 20
        camera_info = f"Camera: ({self.camera_x}, {self.camera_y})"
        info_text = self.small_font.render(camera_info, True, (150, 150, 150))
        self.screen.blit(info_text, (self.map_area_width + 10, y_offset))
    
    def run(self):
        """メインループ"""
        # 既存のマップがあれば読み込み
        if os.path.exists(CSV_MAP_FILE):
            self.load_csv_map(CSV_MAP_FILE)
        
        print("[INFO] Map Editor started")
        print("[INFO] Controls:")
        print("  0-9: Select tile type")
        print("  Left click: Paint")
        print("  Right click: Erase")
        print("  WASD/Arrow keys: Move camera")
        print("  Mouse wheel: Scroll")
        print("  Ctrl+S: Save map")
        print("  Ctrl+O: Load map")
        print("  Ctrl+C: Clear map")
        print("  ESC: Exit")
        
        while self.running:
            self.handle_events()
            
            # 描画
            self.screen.fill((0, 0, 0))
            self.draw_map()
            self.draw_ui()
            self.draw_tooltip()  # ツールチップを最後に描画
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        print("[INFO] Map Editor closed")

def main():
    """メイン関数"""
    # 作業ディレクトリをプロジェクトルートに変更
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # mapフォルダの親ディレクトリ
    os.chdir(project_root)
    
    editor = MapEditor()
    editor.run()

if __name__ == "__main__":
    main()
