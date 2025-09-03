"""
ステージ・マップチップシステム
レトロゲーム風のドット絵背景と障害物を管理
"""

import pygame
import random
import math
from constants import *

# マップチップサイズ
TILE_SIZE = 32

# マップチップの種類
TILE_GRASS = 0
TILE_DIRT = 1
TILE_STONE = 2
TILE_WATER = 3
TILE_TREE = 4
TILE_ROCK = 5
TILE_FLOWER = 6
TILE_BUSH = 7

# 障害物タイル（プレイヤーが通れない）
OBSTACLE_TILES = {TILE_WATER, TILE_TREE, TILE_ROCK}

class TileRenderer:
    """ドット絵風のマップチップを描画するクラス"""
    
    def __init__(self):
        self.tile_cache = {}
        self._create_tile_sprites()
    
    def _create_tile_sprites(self):
        """各マップチップのスプライトを生成"""
        
        # 草地タイル
        self.tile_cache[TILE_GRASS] = self._create_grass_tile()
        
        # 土タイル
        self.tile_cache[TILE_DIRT] = self._create_dirt_tile()
        
        # 石畳タイル
        self.tile_cache[TILE_STONE] = self._create_stone_tile()
        
        # 水タイル（障害物）
        self.tile_cache[TILE_WATER] = self._create_water_tile()
        
        # 木タイル（障害物）
        self.tile_cache[TILE_TREE] = self._create_tree_tile()
        
        # 岩タイル（障害物）
        self.tile_cache[TILE_ROCK] = self._create_rock_tile()
        
        # 花タイル
        self.tile_cache[TILE_FLOWER] = self._create_flower_tile()
        
        # 茂みタイル
        self.tile_cache[TILE_BUSH] = self._create_bush_tile()
    
    def _create_grass_tile(self):
        """草地タイルを作成"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # ベース色（緑）
        base_colors = [(34, 139, 34), (50, 205, 50), (46, 125, 50)]
        base_color = random.choice(base_colors)
        surface.fill(base_color)
        
        # 草のドット
        for _ in range(8):
            x = random.randint(2, TILE_SIZE-3)
            y = random.randint(2, TILE_SIZE-3)
            grass_color = (random.randint(40, 60), random.randint(150, 200), random.randint(40, 60))
            pygame.draw.rect(surface, grass_color, (x, y, 2, 1))
        
        return surface
    
    def _create_dirt_tile(self):
        """土タイルを作成"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # ベース色（茶色）
        base_color = (139, 69, 19)
        surface.fill(base_color)
        
        # 土の質感
        for _ in range(12):
            x = random.randint(0, TILE_SIZE-2)
            y = random.randint(0, TILE_SIZE-2)
            dirt_color = (random.randint(100, 160), random.randint(50, 90), random.randint(10, 30))
            pygame.draw.rect(surface, dirt_color, (x, y, 2, 2))
        
        return surface
    
    def _create_stone_tile(self):
        """石畳タイルを作成"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # ベース色（グレー）
        base_color = (105, 105, 105)
        surface.fill(base_color)
        
        # 石の境界線
        border_color = (70, 70, 70)
        pygame.draw.rect(surface, border_color, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        
        # 内部の質感
        for _ in range(6):
            x = random.randint(4, TILE_SIZE-6)
            y = random.randint(4, TILE_SIZE-6)
            stone_color = (random.randint(90, 120), random.randint(90, 120), random.randint(90, 120))
            pygame.draw.rect(surface, stone_color, (x, y, 3, 3))
        
        return surface
    
    def _create_water_tile(self):
        """水タイルを作成（障害物）"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # ベース色（青）
        base_color = (30, 144, 255)
        surface.fill(base_color)
        
        # 水の波紋効果
        for _ in range(4):
            x = random.randint(4, TILE_SIZE-8)
            y = random.randint(4, TILE_SIZE-8)
            wave_color = (random.randint(50, 100), random.randint(160, 200), 255)
            pygame.draw.circle(surface, wave_color, (x, y), 3)
        
        return surface
    
    def _create_tree_tile(self):
        """木タイルを作成（障害物）"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill((34, 139, 34))  # 草地ベース
        
        # 木の幹
        trunk_color = (101, 67, 33)
        trunk_x = TILE_SIZE // 2 - 3
        pygame.draw.rect(surface, trunk_color, (trunk_x, TILE_SIZE-12, 6, 12))
        
        # 木の葉（円形）
        leaf_color = (34, 139, 34)
        pygame.draw.circle(surface, leaf_color, (TILE_SIZE // 2, TILE_SIZE // 2), 12)
        
        # 葉の詳細
        detail_color = (46, 125, 50)
        pygame.draw.circle(surface, detail_color, (TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4), 6)
        pygame.draw.circle(surface, detail_color, (TILE_SIZE // 2 + 4, TILE_SIZE // 2 - 2), 4)
        
        return surface
    
    def _create_rock_tile(self):
        """岩タイルを作成（障害物）"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill((34, 139, 34))  # 草地ベース
        
        # 岩の本体
        rock_color = (128, 128, 128)
        points = [
            (8, TILE_SIZE-4),
            (12, TILE_SIZE-12),
            (20, TILE_SIZE-14),
            (24, TILE_SIZE-8),
            (20, TILE_SIZE-4)
        ]
        pygame.draw.polygon(surface, rock_color, points)
        
        # 岩の影
        shadow_color = (64, 64, 64)
        shadow_points = [(p[0]+2, p[1]+2) for p in points]
        pygame.draw.polygon(surface, shadow_color, shadow_points)
        
        return surface
    
    def _create_flower_tile(self):
        """花タイルを作成"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill((34, 139, 34))  # 草地ベース
        
        # 花を数個配置
        flower_colors = [(255, 192, 203), (255, 255, 0), (255, 165, 0), (138, 43, 226)]
        
        for _ in range(3):
            x = random.randint(4, TILE_SIZE-6)
            y = random.randint(4, TILE_SIZE-6)
            color = random.choice(flower_colors)
            pygame.draw.circle(surface, color, (x, y), 2)
        
        return surface
    
    def _create_bush_tile(self):
        """茂みタイルを作成"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill((34, 139, 34))  # 草地ベース
        
        # 茂みの塊
        bush_colors = [(34, 139, 34), (46, 125, 50), (50, 205, 50)]
        
        for _ in range(6):
            x = random.randint(2, TILE_SIZE-4)
            y = random.randint(2, TILE_SIZE-4)
            color = random.choice(bush_colors)
            size = random.randint(3, 6)
            pygame.draw.circle(surface, color, (x, y), size)
        
        return surface
    
    def get_tile(self, tile_type):
        """指定されたタイプのマップチップを取得"""
        return self.tile_cache.get(tile_type, self.tile_cache[TILE_GRASS])


class StageMap:
    """ステージマップの管理クラス"""
    
    def __init__(self):
        self.tile_renderer = TileRenderer()
        self.tiles = {}
        self.obstacles = set()
        
        # CSVマップキャッシュ
        self._csv_map_cache = None
        self._csv_map_loaded = False
        
        self._generate_map()
    
    def _load_csv_map_cache(self):
        """CSVマップをキャッシュに読み込む（一度だけ実行）"""
        if self._csv_map_loaded:
            return
        
        try:
            from constants import USE_CSV_MAP, CSV_MAP_FILE
            if USE_CSV_MAP:
                from map.map_loader import MapLoader
                temp_loader = MapLoader()
                if temp_loader.load_csv_map(CSV_MAP_FILE):
                    self._csv_map_cache = temp_loader
                    print(f"[DEBUG] CSV map cached successfully")
        except Exception as e:
            print(f"[DEBUG] Failed to load CSV map cache: {e}")
            
        self._csv_map_loaded = True
    
    def _generate_map(self):
        """プロシージャル生成でマップを作成"""
        
        # ワールドサイズをタイル数に変換
        tiles_x = WORLD_WIDTH // TILE_SIZE
        tiles_y = WORLD_HEIGHT // TILE_SIZE
        
        # ベースタイルを生成（主に草地）
        for y in range(tiles_y):
            for x in range(tiles_x):
                # 基本は草地
                tile_type = TILE_GRASS
                
                # 確率的に他のタイルを配置（密度を下げて移動しやすく）
                rand = random.random()
                
                # 周辺の障害物密度をチェック（障害物が集中しすぎるのを避ける）
                nearby_obstacles = self._count_nearby_obstacles(x, y, 2)
                obstacle_penalty = nearby_obstacles * 0.01  # 近くに障害物があると生成確率を下げる
                
                if rand < max(0.001, 0.008 - obstacle_penalty):  # 0.8% の確率で水（周辺調整）
                    tile_type = TILE_WATER
                    self.obstacles.add((x, y))
                elif rand < max(0.003, 0.025 - obstacle_penalty):  # 1.7% の確率で木（周辺調整）
                    tile_type = TILE_TREE
                    self.obstacles.add((x, y))
                elif rand < max(0.005, 0.035 - obstacle_penalty):  # 1% の確率で岩（周辺調整）
                    tile_type = TILE_ROCK
                    self.obstacles.add((x, y))
                elif rand < 0.12:  # 8.5% の確率で土
                    tile_type = TILE_DIRT
                elif rand < 0.22:  # 10% の確率で花
                    tile_type = TILE_FLOWER
                elif rand < 0.32:  # 10% の確率で茂み
                    tile_type = TILE_BUSH
                
                self.tiles[(x, y)] = tile_type
        
        # 石畳の道を追加
        self._add_stone_paths(tiles_x, tiles_y)
    
    def _count_nearby_obstacles(self, x, y, radius):
        """指定位置の周辺の障害物数をカウント"""
        count = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                check_x, check_y = x + dx, y + dy
                if (check_x, check_y) in self.obstacles:
                    count += 1
        return count
    
    def _add_stone_paths(self, tiles_x, tiles_y):
        """石畳の道を追加"""
        
        # 縦の道
        road_x = tiles_x // 2
        for y in range(tiles_y):
            if (road_x, y) not in self.obstacles:
                self.tiles[(road_x, y)] = TILE_STONE
        
        # 横の道
        road_y = tiles_y // 2
        for x in range(tiles_x):
            if (x, road_y) not in self.obstacles:
                self.tiles[(x, road_y)] = TILE_STONE
    
    def get_tile_at_world_pos(self, world_x, world_y):
        """ワールド座標からタイル種類を取得"""
        # CSVマップが有効な場合はCSVマップのタイルを取得
        from constants import USE_CSV_MAP
        if USE_CSV_MAP:
            # キャッシュからCSVマップを取得
            self._load_csv_map_cache()
            if self._csv_map_cache:
                try:
                    return self._csv_map_cache.get_tile_at(world_x, world_y)
                except Exception as e:
                    print(f"[DEBUG] CSV tile lookup failed: {e}")
        
        # 従来のプロシージャル生成マップのタイル取得
        tile_x = int(world_x // TILE_SIZE)
        tile_y = int(world_y // TILE_SIZE)
        return self.tiles.get((tile_x, tile_y), TILE_GRASS)
    
    def is_obstacle_at_world_pos(self, world_x, world_y):
        """ワールド座標が障害物かどうかチェック"""
        # CSVマップが有効な場合はCSVマップのブロッカータイルをチェック
        from constants import USE_CSV_MAP
        if USE_CSV_MAP:
            # キャッシュからCSVマップを取得
            self._load_csv_map_cache()
            if self._csv_map_cache:
                try:
                    tile_id = self._csv_map_cache.get_tile_at(world_x, world_y)
                    # ブロッカータイル: 5(森), 7(水), 8(危険地帯), 9(石/岩)
                    return tile_id in [5, 7, 8, 9]
                except Exception as e:
                    print(f"[DEBUG] CSV collision check failed: {e}")
        
        # 従来のプロシージャル生成マップの障害物チェック
        tile_x = int(world_x // TILE_SIZE)
        tile_y = int(world_y // TILE_SIZE)
        return (tile_x, tile_y) in self.obstacles
    
    def find_safe_spawn_position(self, preferred_x, preferred_y, entity_size):
        """障害物のない安全な開始位置を見つける"""
        # まず希望位置をチェック
        if self.is_position_safe(preferred_x, preferred_y, entity_size):
            return preferred_x, preferred_y
        
        # 希望位置から螺旋状に安全な場所を探索
        max_radius = 10  # 最大10タイル分探索
        for radius in range(1, max_radius + 1):
            for angle_step in range(0, 360, 15):  # 15度刻み
                angle = math.radians(angle_step)
                test_x = preferred_x + radius * TILE_SIZE * math.cos(angle)
                test_y = preferred_y + radius * TILE_SIZE * math.sin(angle)
                
                # ワールド境界内かチェック
                if (entity_size <= test_x <= WORLD_WIDTH - entity_size and 
                    entity_size <= test_y <= WORLD_HEIGHT - entity_size):
                    if self.is_position_safe(test_x, test_y, entity_size):
                        return test_x, test_y
        
        # どうしても見つからない場合は左上の安全な場所を返す
        for y in range(entity_size, WORLD_HEIGHT - entity_size, TILE_SIZE):
            for x in range(entity_size, WORLD_WIDTH - entity_size, TILE_SIZE):
                if self.is_position_safe(x, y, entity_size):
                    return x, y
        
        # 最後の手段：希望位置をそのまま返す
        return preferred_x, preferred_y
    
    def is_position_safe(self, world_x, world_y, entity_size):
        """指定位置がエンティティにとって安全かチェック（障害物と重ならない）"""
        # エンティティの四隅をチェック
        half_size = entity_size // 2
        corners = [
            (world_x - half_size, world_y - half_size),
            (world_x + half_size, world_y - half_size),
            (world_x - half_size, world_y + half_size),
            (world_x + half_size, world_y + half_size),
        ]
        
        for corner_x, corner_y in corners:
            if self.is_obstacle_at_world_pos(corner_x, corner_y):
                return False
        return True
    
    def draw(self, screen, camera_x, camera_y):
        """ステージを描画"""
        
        # 描画範囲を計算
        start_tile_x = max(0, int(camera_x // TILE_SIZE))
        end_tile_x = min(WORLD_WIDTH // TILE_SIZE, int((camera_x + SCREEN_WIDTH) // TILE_SIZE) + 1)
        start_tile_y = max(0, int(camera_y // TILE_SIZE))
        end_tile_y = min(WORLD_HEIGHT // TILE_SIZE, int((camera_y + SCREEN_HEIGHT) // TILE_SIZE) + 1)
        
        # タイルを描画
        for tile_y in range(start_tile_y, end_tile_y):
            for tile_x in range(start_tile_x, end_tile_x):
                
                # ワールド座標
                world_x = tile_x * TILE_SIZE
                world_y = tile_y * TILE_SIZE
                
                # 画面座標
                screen_x = world_x - camera_x
                screen_y = world_y - camera_y
                
                # タイル種類を取得して描画
                tile_type = self.tiles.get((tile_x, tile_y), TILE_GRASS)
                tile_surface = self.tile_renderer.get_tile(tile_type)
                screen.blit(tile_surface, (screen_x, screen_y))


# グローバルなステージマップインスタンス
_stage_map = None

def get_stage_map():
    """ステージマップのシングルトンインスタンスを取得"""
    global _stage_map
    if _stage_map is None:
        _stage_map = StageMap()
    return _stage_map

def init_stage():
    """ステージを明示的に初期化（プレイヤー初期化前に呼び出す）"""
    get_stage_map()  # シングルトンインスタンスを作成

def draw_stage_background(screen, camera_x=0, camera_y=0):
    """ステージ背景を描画（ui.pyのdraw_backgroundの置き換え）"""
    stage_map = get_stage_map()
    stage_map.draw(screen, camera_x, camera_y)
