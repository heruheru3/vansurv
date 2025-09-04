"""
ステージ・CSVマップシステム
CSVマップによる障害物と背景を管理
"""

import pygame
import math
from constants import *

class StageMap:
    """CSVマップベースのステージマップ管理クラス"""
    
    def __init__(self):
        # CSVマップキャッシュ
        self._csv_map_cache = None
        self._csv_map_loaded = False
        
        # CSVマップを読み込み
        self._load_csv_map_cache()
    
    def _load_csv_map_cache(self):
        """CSVマップをキャッシュに読み込む（一度だけ実行）"""
        if self._csv_map_loaded:
            return
        
        try:
            from constants import CSV_MAP_FILE
            from map.map_loader import MapLoader
            self._csv_map_cache = MapLoader()
            if self._csv_map_cache.load_csv_map(CSV_MAP_FILE):
                print(f"[DEBUG] CSV map cached successfully")
            else:
                print(f"[DEBUG] Failed to load CSV map, using default")
                self._csv_map_cache.generate_default_map()
        except Exception as e:
            print(f"[DEBUG] Failed to load CSV map cache: {e}")
            from map.map_loader import MapLoader
            self._csv_map_cache = MapLoader()
            self._csv_map_cache.generate_default_map()
            
        self._csv_map_loaded = True
    
    def get_tile_at_world_pos(self, world_x, world_y):
        """ワールド座標からタイル種類を取得"""
        self._load_csv_map_cache()
        if self._csv_map_cache:
            try:
                return self._csv_map_cache.get_tile_at(world_x, world_y)
            except Exception as e:
                print(f"[DEBUG] CSV tile lookup failed: {e}")
        return 0  # デフォルトタイル
    
    def is_weapon_blocked_at_pos(self, world_x, world_y, weapon_name):
        """指定座標で武器がブロックされるかチェック
        
        Args:
            world_x, world_y: ワールド座標
            weapon_name: 武器名（"stone", "knife", "axe", "magic_wand" など）
            
        Returns:
            bool: ブロックされる場合True
        """
        # 武器が不可侵領域の影響を受けない場合は常にFalse
        if weapon_name not in WEAPONS_AFFECTED_BY_BLOCKERS:
            return False
        
        tile_id = self.get_tile_at_world_pos(world_x, world_y)
        
        # エリア5,9: ソリッドブロッカー（武器をブロック）
        if tile_id in BLOCKER_AREAS_SOLID:
            return True
            
        # エリア6,7: パススルーブロッカー（武器は貫通可能）
        if tile_id in BLOCKER_AREAS_PASSTHROUGH:
            return False
        
        # その他のタイル（通常エリア）: ブロックされない
        return False
    
    def get_weapon_collision_line(self, start_x, start_y, end_x, end_y, weapon_name, step_size=8):
        """武器の軌道上で最初にブロックされる座標を取得
        
        Args:
            start_x, start_y: 開始座標
            end_x, end_y: 終了座標
            weapon_name: 武器名
            step_size: チェック間隔（ピクセル）
            
        Returns:
            tuple: (collision_x, collision_y) ブロックされた座標、None if no collision
        """
        if weapon_name not in WEAPONS_AFFECTED_BY_BLOCKERS:
            return None  # この武器は不可侵領域の影響を受けない
        
        # 軌道をステップごとにチェック
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return None
            
        # 正規化された方向ベクトル
        step_x = (dx / distance) * step_size
        step_y = (dy / distance) * step_size
        
        # 軌道をチェック
        current_x = start_x
        current_y = start_y
        steps = int(distance / step_size)
        
        for i in range(steps + 1):
            if self.is_weapon_blocked_at_pos(current_x, current_y, weapon_name):
                return (current_x, current_y)
            current_x += step_x
            current_y += step_y
            
        return None  # 衝突なし
    
    def is_obstacle_at_world_pos(self, world_x, world_y):
        """ワールド座標が障害物かどうかチェック"""
        self._load_csv_map_cache()
        if self._csv_map_cache:
            try:
                tile_id = self._csv_map_cache.get_tile_at(world_x, world_y)
                # ブロッカータイル: 5(森), 7(水), 8(危険地帯), 9(石/岩)
                return tile_id in [5, 7, 8, 9]
            except Exception as e:
                print(f"[DEBUG] CSV collision check failed: {e}")
        return False
    
    def find_safe_spawn_position(self, preferred_x, preferred_y, entity_size):
        """障害物のない安全な開始位置を見つける"""
        # まず希望位置をチェック
        if self.is_position_safe(preferred_x, preferred_y, entity_size):
            return preferred_x, preferred_y
        
        # 希望位置から螺旋状に安全な場所を探索
        max_radius = 10  # 最大10タイル分探索
        tile_size = self._csv_map_cache.tile_size if self._csv_map_cache else 32
        
        for radius in range(1, max_radius + 1):
            for angle_step in range(0, 360, 15):  # 15度刻み
                angle = math.radians(angle_step)
                test_x = preferred_x + radius * tile_size * math.cos(angle)
                test_y = preferred_y + radius * tile_size * math.sin(angle)
                
                # ワールド境界内かチェック
                if (entity_size <= test_x <= WORLD_WIDTH - entity_size and 
                    entity_size <= test_y <= WORLD_HEIGHT - entity_size):
                    if self.is_position_safe(test_x, test_y, entity_size):
                        return test_x, test_y
        
        # どうしても見つからない場合は左上の安全な場所を返す
        for y in range(entity_size, WORLD_HEIGHT - entity_size, tile_size):
            for x in range(entity_size, WORLD_WIDTH - entity_size, tile_size):
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
        self._load_csv_map_cache()
        if self._csv_map_cache:
            try:
                self._csv_map_cache.draw_map(screen, camera_x, camera_y)
                return
            except Exception as e:
                print(f"[DEBUG] CSV map draw failed: {e}")
        
        # フォールバック：黒い画面を表示
        screen.fill((0, 0, 0))


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
