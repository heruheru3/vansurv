import pygame
import math
import os
import sys
from constants import *
from utils.file_paths import get_resource_path

class Attack:
    # 武器画像のキャッシュ
    _weapon_image_cache = {}
    
    def __init__(self, x, y, size_x, size_y, type_, duration=1000, target=None, 
                 speed=0, bounces=0, follow_player=None, direction=None, 
                 velocity_x=None, velocity_y=None, rotation_speed=None, damage=0,
                 stage=None):
        self.x = x
        self.y = y
        self.size_x = size_x
        self.size_y = size_y
        self.size = max(size_x, size_y) // 2  # 当たり判定用
        self.type = type_
        self.creation_time = pygame.time.get_ticks()
        self.duration = duration
        self.target = target
        self.speed = speed
        self.angle = 0
        self.bounces_remaining = bounces
        self.follow_player = follow_player
        self.direction = direction
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.rotation_speed = rotation_speed if rotation_speed is not None else 0
        self.damage = damage  # 攻撃のダメージ量
        self.stage = stage  # 不可侵領域チェック用のステージ参照

        # 武器画像を読み込み（存在すれば）
        self.weapon_image = self._load_weapon_image(type_)

        # spawn_delay を外部から設定できるようにする（ms）。設定されると開始を遅らせる。
        self.spawn_delay = 0
        self._pending = False

        # 同一攻撃が同じ敵を繰り返しヒットするのを防ぐための記録（id(enemy)を格納）
        self.hit_targets = set()

        # 魔法の杖の場合、ターゲットへの移動方向を設定
        if target and type_ == "magic_wand":
            angle = math.atan2(target.y - y, target.x - x)
            self.dx = math.cos(angle) * speed
            self.dy = math.sin(angle) * speed
        elif type_ == "stone":
            self.dx = speed
            self.dy = -speed

        self.original_size = max(size_x, size_y)  # パルスエフェクト用に元のサイズを保存
        self.pulse_timer = 0  # パルスのタイミング用

        # holy_water 用の描画キャッシュサーフェス
        if self.type == "holy_water":
            self.holy_surf = None
            self.holy_surf_size = 0

    @classmethod
    def _load_weapon_image(cls, weapon_type):
        """武器の画像を読み込む（キャッシュ機能付き）"""
        if weapon_type in cls._weapon_image_cache:
            return cls._weapon_image_cache[weapon_type]
        
        # 画像ファイルパスを構築
        image_path = get_resource_path(os.path.join("assets", "weapons", f"{weapon_type}.png"))
        
        try:
            if os.path.exists(image_path):
                image = pygame.image.load(image_path).convert_alpha()
                cls._weapon_image_cache[weapon_type] = image
                return image
            else:
                cls._weapon_image_cache[weapon_type] = None
                return None
        except Exception as e:
            cls._weapon_image_cache[weapon_type] = None
            return None

    def update(self, camera_x=None, camera_y=None):
        # spawn_delay が設定されている場合は開始まで待機する
        if getattr(self, '_pending', False) and getattr(self, 'spawn_delay', 0) > 0:
            now = pygame.time.get_ticks()
            if now - self.creation_time < self.spawn_delay:
                # まだ待機中: 何もせず早期リターン
                return
            else:
                # 待機終了: 開始時刻を現在にリセットして通常処理へ
                self.creation_time = now
                self._pending = False
        elif getattr(self, '_pending', False) and getattr(self, 'spawn_delay', 0) <= 0:
            # 安全策: 遅延なしで pending になっていたら即時有効化
            self._pending = False

        if self.follow_player:
            # follow_player の共通処理（位置追従）
            origin_x = self.follow_player.x
            origin_y = self.follow_player.y
            if self.type == "garlic":
                # パルスエフェクトの更新
                # 中心をプレイヤー位置に追従させる
                self.x = origin_x
                self.y = origin_y
                self.pulse_timer += 1
                pulse_period = 60  # パルスの周期（フレーム数）
                pulse_ratio = abs(math.sin(self.pulse_timer * math.pi / pulse_period))
                self.size_x = self.original_size * (0.5 + 0.5 * pulse_ratio)
                self.size_y = self.size_x
                self.size = self.size_x // 2
            elif self.type == "whip":
                # プレイヤーからシュッと一直線に伸び縮みするムチ表現
                elapsed = pygame.time.get_ticks() - self.creation_time
                t = min(max(elapsed / max(1, self.duration), 0.0), 1.0)
                extend = math.sin(math.pi * t) ** 2

                # 長さ・角度を direction から決定（常にプレイヤー基点から計算）
                length = getattr(self, 'length', max(self.size_x, self.size_y))
                dir_name = getattr(self, 'direction', 'right')
                angle_lookup = {
                    'right': 0.0,
                    'left': math.pi,
                    'up': -math.pi/2,
                    'down': math.pi/2
                }
                angle = angle_lookup.get(dir_name, 0.0)

                # 少数のセグメントで直線を作る（滑らかさはセグメント数で調整）
                segments = max(2, int(getattr(self, 'segments', 4)))
                points = []
                for i in range(segments + 1):
                    frac = i / segments
                    px = origin_x + math.cos(angle) * (length * extend * frac)
                    py = origin_y + math.sin(angle) * (length * extend * frac)
                    points.append((px, py))
                self.whip_points = points
                # 当たり判定用の中心座標はムチの全長の中央に固定（描画の伸縮に依らない）
                self.x = origin_x + math.cos(angle) * (length * 0.5)
                self.y = origin_y + math.sin(angle) * (length * 0.5)
            elif self.type == "book":
                # 回転する本: orbit_angle を進め、プレイヤー周囲に配置
                try:
                    self.orbit_angle = getattr(self, 'orbit_angle', 0.0) + getattr(self, 'rotation_speed', 0.08)
                    r = getattr(self, 'orbit_radius', 40)
                    self.x = origin_x + math.cos(self.orbit_angle) * r
                    self.y = origin_y + math.sin(self.orbit_angle) * r
                except Exception:
                    pass
        elif self.type == "axe":
            # 不可侵領域チェック（axe は影響を受ける武器）
            if self.stage and hasattr(self.stage, 'is_weapon_blocked_at_pos'):
                # 次の位置をチェック
                next_x = self.x + (self.velocity_x if self.velocity_x is not None else 0)
                next_y = self.y + (self.velocity_y if self.velocity_y is not None else -self.speed)
                if self.stage.is_weapon_blocked_at_pos(next_x, next_y, "axe"):
                    # 不可侵領域に衝突する場合、攻撃を削除
                    self.duration = 0
                    return
            
            # 回転速度が指定されていればそれを使用
            self.angle += self.rotation_speed
            # 速度ベクトルがあればそれで移動（投げる軌道）
            if self.velocity_x is not None and self.velocity_y is not None:
                self.x += self.velocity_x
                self.y += self.velocity_y
            else:
                self.y -= self.speed  # 上方向に移動
                self.x += math.sin(self.angle) * 3  # 横方向に揺れる動き
        elif self.type == "magic_wand":
            # 不可侵領域チェック（magic_wand は影響を受ける武器）
            if self.stage and hasattr(self.stage, 'is_weapon_blocked_at_pos'):
                next_x = self.x + getattr(self, 'dx', 0)
                next_y = self.y + getattr(self, 'dy', 0)
                if self.stage.is_weapon_blocked_at_pos(next_x, next_y, "magic_wand"):
                    # 不可侵領域に衝突する場合、攻撃を削除
                    self.duration = 0
                    return
            
            # 移動と軌跡記録
            self.x += getattr(self, 'dx', 0)
            self.y += getattr(self, 'dy', 0)
            try:
                if getattr(self, 'trail', None) is None:
                    self.trail = []
                self.trail.append((self.x, self.y))
                max_trail = 6
                if len(self.trail) > max_trail:
                    self.trail = self.trail[-max_trail:]
            except Exception:
                pass
        elif self.type == "thunder":
            # 上空から落ちてきて目標地点でストップする表現
            try:
                # ターゲット参照があれば、目標Y座標は常にターゲットの頭上に追従させる
                if getattr(self, 'target', None) is not None:
                    target_y = getattr(self.target, 'y', self.y) - getattr(self, 'head_offset', 0)
                else:
                    target_y = getattr(self, 'y', self.y)

                # 初期化: y を strike_from_y にセット
                if not getattr(self, 'thunder_started', False) and hasattr(self, 'strike_from_y'):
                    self.y = getattr(self, 'strike_from_y')
                    self.thunder_started = True
                    # 落下速度を設定（目標との差分に基づく）
                    self.fall_speed = max(8, int((target_y - self.y) / 6))
                    if self.fall_speed <= 0:
                        self.fall_speed = 12
                    # mark when reached
                    self.struck = False

                if not getattr(self, 'struck', False):
                    # 毎フレーム、ターゲットが動いていれば目標位置を更新する
                    if getattr(self, 'target', None) is not None:
                        target_y = getattr(self.target, 'y', target_y) - getattr(self, 'head_offset', 0)
                    # 落下
                    self.y += getattr(self, 'fall_speed', 12)
                    if self.y >= target_y:
                        self.y = target_y
                        self.struck = True
                        # 小さなウェーブ/エフェクトが出るように duration を短く保つ
                        self.creation_time = pygame.time.get_ticks()
                        self.duration = 300
                else:
                    # 既に着地後は短時間その場に留まる（is_expired によって消える）
                    pass
            except Exception:
                pass
        elif (getattr(self, 'velocity_x', None) is not None and getattr(self, 'velocity_y', None) is not None) and self.type not in ("stone", "axe", "magic_wand"):
            # 一般的な速度ベースの移動（ナイフ等）
            try:
                # 不可侵領域チェック（knife は影響を受ける武器）
                if self.type == "knife" and self.stage and hasattr(self.stage, 'is_weapon_blocked_at_pos'):
                    # 次の位置をチェック
                    next_x = self.x + self.velocity_x
                    next_y = self.y + self.velocity_y
                    if self.stage.is_weapon_blocked_at_pos(next_x, next_y, "knife"):
                        # 不可侵領域に衝突する場合、攻撃を削除（消去）
                        self.duration = 0
                        return
                
                self.x += self.velocity_x
                self.y += self.velocity_y
            except Exception:
                pass
        elif self.type == "stone":
            # 次の移動先を計算
            next_x = self.x + self.velocity_x
            next_y = self.y + self.velocity_y
            
            # 不可侵領域チェック（stone は影響を受ける武器）
            if self.stage and hasattr(self.stage, 'is_weapon_blocked_at_pos'):
                if self.stage.is_weapon_blocked_at_pos(next_x, next_y, "stone"):
                    # 不可侵領域に衝突する場合、バウンド処理（移動前に方向転換）
                    self.velocity_x *= -1
                    self.velocity_y *= -1
                    self.bounces_remaining -= 1  # 不可侵領域でのバウンドもバウンド回数を消費
                    # 新しい方向で移動先を再計算
                    next_x = self.x + self.velocity_x
                    next_y = self.y + self.velocity_y
            
            # 速度に基づいて位置を更新
            self.x = next_x
            self.y = next_y

            # 画面端での跳ね返り処理（カメラ範囲の境界で判定するように変更）
            if camera_x is not None and camera_y is not None:
                left = camera_x
                right = camera_x + SCREEN_WIDTH
                top = camera_y
                bottom = camera_y + SCREEN_HEIGHT
            else:
                left = 0
                right = WORLD_WIDTH
                top = 0
                bottom = WORLD_HEIGHT

            bounced = False
            if self.x <= left or self.x >= right:
                self.velocity_x *= -1
                self.bounces_remaining -= 1
                # 反射後に画面外に留まらないように座標を内側に補正
                self.x = max(left + 1, min(self.x, right - 1))
                bounced = True
            if self.y <= top or self.y >= bottom:
                self.velocity_y *= -1
                self.bounces_remaining -= 1
                self.y = max(top + 1, min(self.y, bottom - 1))
                bounced = True

            # 短い軌跡用の履歴を保持（毎フレーム現在座標を追加し、古いものを切る）
            try:
                if getattr(self, 'trail', None) is None:
                    self.trail = []
                # 座標はワールド座標で保存
                self.trail.append((self.x, self.y))
                # サイズに応じて軌跡長を決める（最大8）
                trail_len = max(3, min(8, int(self.size // 2) + 3))
                if len(self.trail) > trail_len:
                    self.trail = self.trail[-trail_len:]
                # 反射時にはわずかに軌跡を切る（視覚的に区切りを作る）
                if bounced and len(self.trail) > 2:
                    self.trail = self.trail[-2:]
            except Exception:
                # 軌跡管理が失敗してもゲーム継続
                pass

    def is_expired(self):
        return (pygame.time.get_ticks() - self.creation_time >= self.duration or 
                (self.type == "stone" and self.bounces_remaining < 0))

    def draw(self, screen, camera_x=0, camera_y=0):
        # ワールド座標をスクリーン座標に変換
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)

        # spawn_delay によってまだ発生していない攻撃は描画しない
        if getattr(self, '_pending', False) and getattr(self, 'spawn_delay', 0) > 0:
            return

        # 画面外の攻撃は描画をスキップ（軽量化）
        margin = 100  # 少しマージンを持たせる
        if (sx < -margin or sx > SCREEN_WIDTH + margin or 
            sy < -margin or sy > SCREEN_HEIGHT + margin):
            return

        if self.type == "whip":
            # ムチは follow_player と whip_points を使ってシュッと伸び縮みする直線で描画
            pts = getattr(self, 'whip_points', None)
            # フォールバック: update() が未実行でもここでポイントを計算
            if not pts:
                elapsed = pygame.time.get_ticks() - self.creation_time
                t = min(max(elapsed / max(1, self.duration), 0.0), 1.0)
                extend = math.sin(math.pi * t) ** 2
                length = getattr(self, 'length', max(self.size_x, self.size_y))
                dir_name = getattr(self, 'direction', 'right')
                angle_lookup = {
                    'right': 0.0,
                    'left': math.pi,
                    'up': -math.pi/2,
                    'down': math.pi/2
                }
                angle = angle_lookup.get(dir_name, 0.0)
                segments = max(2, int(getattr(self, 'segments', 4)))
                pts = []
                for i in range(segments + 1):
                    frac = i / segments
                    px = self.x + math.cos(angle) * (length * extend * frac)
                    py = self.y + math.sin(angle) * (length * extend * frac)
                    pts.append((px, py))

            if pts and len(pts) > 1:
                int_pts = [(int(x - camera_x), int(y - camera_y)) for x, y in pts]
                # 細めの茶色ベースのムチライン（素早い見た目のため幅は控えめ）
                w = max(2, int(getattr(self, 'width', 6)))
                try:
                    BROWN = (139, 69, 19)
                    BEIGE = (222, 184, 135)
                    # ベースラインと細いハイライト
                    pygame.draw.lines(screen, BROWN, False, int_pts, w)
                    pygame.draw.lines(screen, BEIGE, False, int_pts, max(1, w // 3))
                except Exception:
                    pass

                # 先端の光はユーザー要望により削除（ラインのみで表現する）

            else:
                pygame.draw.rect(screen, WHITE, 
                               (sx - self.size_x/2, 
                                sy - self.size_y/2, 
                                self.size_x, self.size_y))
        elif self.type == "holy_water":
            # 半透明の水面を描画（塗り + リップル）
            try:
                r = max(2, int(self.size))
                surf_size = r * 2 + 8
                # キャッシュサーフェスをサイズ変化時に生成
                if getattr(self, 'holy_surf', None) is None or self.holy_surf_size != surf_size:
                    self.holy_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                    self.holy_surf_size = surf_size

                s = self.holy_surf
                s.fill((0, 0, 0, 0))

                # ベースの半透明フィル
                base_alpha = 110
                pygame.draw.circle(s, (30, 140, 200, base_alpha), (surf_size//2, surf_size//2), r)

                # 時間に応じて動くリップル（同心円）を数本描く
                elapsed = pygame.time.get_ticks() - self.creation_time
                # 周期を200msに設定して滑らかに動かす
                for i in range(3):
                    phase = (elapsed / 200.0 + i * 0.6)
                    frac = (math.sin(phase) * 0.5 + 0.5)
                    rr = int(r * (0.6 + 0.6 * frac))
                    alpha = int(80 * (1.0 - i * 0.25) * (0.4 + 0.6 * (1 - frac)))
                    if alpha > 0:
                        pygame.draw.circle(s, (80, 180, 230, max(10, alpha)), (surf_size//2, surf_size//2), rr, 2)

                # 軽いノイズのストロークを追加（薄め）
                try:
                    pygame.draw.circle(s, (20, 100, 160, 24), (surf_size//2, surf_size//2), int(r*0.9), 1)
                except Exception:
                    pass

                # ブリット（カメラオフセットを考慮）
                screen.blit(s, (sx - surf_size//2, sy - surf_size//2))
            except Exception:
                # フォールバック: 輪郭のみ
                pygame.draw.circle(screen, CYAN, (int(sx), int(sy)), self.size, 2)
        elif self.type == "garlic":
            try:
                # 中心から透過した赤で拡散する見た目を作る
                r = max(2, int(self.size_x/2))
                surf_size = r * 2 + 12
                # サイズが変わったらキャッシュサーフェスを再生成
                if getattr(self, 'garlic_surf', None) is None or getattr(self, 'garlic_surf_size', 0) != surf_size:
                    self.garlic_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                    self.garlic_surf_size = surf_size

                gs = self.garlic_surf
                gs.fill((0, 0, 0, 0))

                # 中心の半透明フィルでソフトな光を作る
                base_alpha = 90
                pygame.draw.circle(gs, (200, 40, 40, base_alpha), (surf_size//2, surf_size//2), r)

                # 時間経過で動く薄いリップル（同心円）を数本描画して拡散感を演出
                elapsed = pygame.time.get_ticks() - self.creation_time
                for i in range(3):
                    phase = (elapsed / 180.0 + i * 0.6)
                    frac = (math.sin(phase) * 0.5 + 0.5)
                    rr = int(r * (0.7 + 0.8 * frac))
                    alpha = int(100 * (1.0 - i * 0.25) * (0.4 + 0.6 * (1 - frac)))
                    if alpha > 0:
                        pygame.draw.circle(gs, (255, 80, 80, max(8, alpha)), (surf_size//2, surf_size//2), rr, 2)

                # 内側の柔らかいグローを追加
                try:
                    pygame.draw.circle(gs, (255, 120, 120, 40), (surf_size//2, surf_size//2), int(r*0.6))
                except Exception:
                    pass

                # ブリット（カメラオフセットを考慮）
                screen.blit(gs, (sx - surf_size//2, sy - surf_size//2))
            except Exception:
                # フォールバック: 薄い赤の円で描画
                pygame.draw.circle(screen, (200, 50, 50), (int(sx), int(sy)), int(self.size_x/2))
        elif self.type == "magic_wand":
            try:
                # 半透明ライン軌跡（見やすく調整）
                trail = getattr(self, 'trail', [])
                if trail and len(trail) > 1:
                    pts = [(int(x - camera_x), int(y - camera_y)) for x, y in trail]
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    minx = min(xs) - 6
                    miny = min(ys) - 6
                    maxx = max(xs) + 6
                    maxy = max(ys) + 6
                    w = max(1, maxx - minx)
                    h = max(1, maxy - miny)
                    surf = pygame.Surface((w, h), pygame.SRCALPHA)
                    # 新しいほど濃く太く、古いほど薄く細く描画
                    n = len(pts)
                    base_col = (150, 80, 220)
                    for i in range(n - 1):
                        p0 = pts[i]
                        p1 = pts[i + 1]
                        rel0 = (p0[0] - minx, p0[1] - miny)
                        rel1 = (p1[0] - minx, p1[1] - miny)
                        frac = (i + 1) / float(n)
                        alpha = int(60 + 180 * frac)  # 目立つように下限を引き上げ
                        line_w = max(1, int(self.size * (0.6 + 0.8 * frac)))
                        try:
                            pygame.draw.line(surf, (base_col[0], base_col[1], base_col[2], alpha), rel0, rel1, line_w)
                        except Exception:
                            pass
                        # 点で強調（新しい点ほど明るく）
                        try:
                            dot_alpha = int(80 + 175 * frac)
                            dr = max(1, int(self.size * (0.4 + 0.6 * frac)))
                            pygame.draw.circle(surf, (220, 140, 250, dot_alpha), rel1, dr)
                        except Exception:
                            pass
                    try:
                        screen.blit(surf, (minx, miny))
                    except Exception:
                        pass

                # グロー（中央）を残すがやや抑えめに
                glow_layers = [ (self.size+6, (200,120,255,20)), (self.size+3, (210,140,255,60)), (self.size, (255,200,255,200)) ]
                for radius, col in glow_layers:
                    rr = int(radius)
                    gs = pygame.Surface((rr*2+2, rr*2+2), pygame.SRCALPHA)
                    try:
                        pygame.draw.circle(gs, col, (rr+1, rr+1), rr)
                        screen.blit(gs, (sx - rr - 1, sy - rr - 1))
                    except Exception:
                        pass

                # 中心の明るい点
                try:
                    pygame.draw.circle(screen, MAGENTA, (int(sx), int(sy)), max(1, int(self.size)))
                except Exception:
                    pass
            except Exception:
                pygame.draw.circle(screen, MAGENTA, (int(sx), int(sy)), self.size)
        elif self.type == "axe":
            # 画像がある場合は画像を描画、ない場合は従来の四角形を描画（軽量化版）
            if self.weapon_image is not None:
                try:
                    # 画像サイズを90%に縮小（当たり判定とのバランス調整）
                    w, h = int(self.size_x * 0.8), int(self.size_y * 0.8)
                    angle_degrees = math.degrees(self.angle)
                    
                    # 回転角度を30度刻みに丸めてキャッシュ効率をさらに改善
                    angle_rounded = round(angle_degrees / 30) * 30
                    
                    # 統合キャッシュを使用
                    if not hasattr(Attack, '_axe_unified_cache'):
                        Attack._axe_unified_cache = {}
                    
                    cache_key = f"axe_{w}x{h}_r{angle_rounded}"
                    
                    if cache_key not in Attack._axe_unified_cache:
                        # 一度に全ての変換を適用
                        scaled_image = pygame.transform.scale(self.weapon_image, (w, h))
                        if angle_rounded != 0:
                            rotated_image = pygame.transform.rotate(scaled_image, -angle_rounded)
                        else:
                            rotated_image = scaled_image
                        Attack._axe_unified_cache[cache_key] = rotated_image
                        
                        # キャッシュサイズ制限を強化
                        if len(Attack._axe_unified_cache) > 48:  # 360/30 = 12方向 × 4サイズ程度
                            keys = list(Attack._axe_unified_cache.keys())
                            for old_key in keys[:12]:
                                del Attack._axe_unified_cache[old_key]
                    
                    cached_image = Attack._axe_unified_cache[cache_key]
                    rotated_rect = cached_image.get_rect()
                    rotated_rect.center = (sx, sy)
                    screen.blit(cached_image, rotated_rect.topleft)
                    
                except Exception as e:
                    print(f"[WARNING] Failed to draw axe image: {e}")
                    # フォールバック：従来の四角形描画
                    self._draw_axe_fallback(screen, sx, sy, camera_x, camera_y)
            else:
                # 画像がない場合は従来の四角形を描画
                self._draw_axe_fallback(screen, sx, sy, camera_x, camera_y)
        elif self.type == "stone":
            try:
                r = max(2, int(self.size))
                surf_size = r * 4 + 10
                if getattr(self, 'stone_surf', None) is None or getattr(self, 'stone_surf_size', 0) != surf_size:
                    ss = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                    ss.fill((0, 0, 0, 0))
                    cx = surf_size // 2
                    cy = surf_size // 2
                    # 白ベースの岩テクスチャ
                    pygame.draw.circle(ss, (230, 230, 235, 255), (cx, cy), r)
                    try:
                        pygame.draw.circle(ss, (255, 255, 255, 180), (cx - int(r*0.3), cy - int(r*0.4)), int(r*0.5))
                        pygame.draw.circle(ss, (200, 200, 205, 160), (cx + int(r*0.4), cy + int(r*0.3)), int(r*0.6))
                        pygame.draw.line(ss, (180,180,190,200), (cx - int(r*0.2), cy), (cx + int(r*0.5), cy - int(r*0.4)), 2)
                    except Exception:
                        pass
                    self.stone_surf = ss
                    self.stone_surf_size = surf_size

                # 軌跡を描画（ワールド座標の履歴から、古いものほど薄く、小さく描く）
                try:
                    trail = getattr(self, 'trail', [])
                    if trail and len(trail) > 1:
                        n = len(trail)
                        # 古いものから順に描画していく（古いほど小さく透明）
                        for i, (tx, ty) in enumerate(trail[:-1]):
                            frac = (i + 1) / float(n)
                            alpha = int(40 + 200 * frac)  # 古いほど小さい alpha -> newer もっと濃い
                            tr = int(max(1, r * (0.35 + 0.65 * frac)))
                            color = (245, 245, 250, max(8, min(255, alpha)))
                            try:
                                pygame.draw.circle(screen, color, (int(tx - camera_x), int(ty - camera_y)), tr)
                            except Exception:
                                pass
                except Exception:
                    pass

                rot = self.stone_surf
                rw, rh = rot.get_size()
                screen.blit(rot, (sx - rw//2, sy - rh//2))
            except Exception:
                pygame.draw.circle(screen, WHITE, (int(sx), int(sy)), self.size)
        elif self.type == "book":
            # 回転する本のテクスチャを描画（プレイヤーを中心に外向き）- 軽量化版
            try:
                # フレームスキップによる軽量化（2フレームに1回だけ角度更新）
                current_frame = pygame.time.get_ticks() // 16  # 約60FPS基準
                if not hasattr(self, '_last_rotation_frame'):
                    self._last_rotation_frame = -1
                    self._cached_rotation = 0
                
                # 表示サイズは Attack に渡された size_x/size_y を使う
                w = int(getattr(self, 'size_x', 18))
                h = int(getattr(self, 'size_y', 18))
                
                # 角度計算を2フレームに1回に削減
                if current_frame != self._last_rotation_frame:
                    if self.follow_player:
                        dx = self.x - self.follow_player.x
                        dy = self.y - self.follow_player.y
                        outward_angle = math.atan2(dy, dx)
                        self._cached_rotation = math.degrees(outward_angle + math.pi/2)
                    else:
                        self._cached_rotation = 0
                    self._last_rotation_frame = current_frame
                
                # 回転角度を30度刻みに丸めてキャッシュ効率をさらに改善
                book_rotation_rounded = round(self._cached_rotation / 30) * 30
                
                # フェード計算を簡略化
                elapsed = pygame.time.get_ticks() - getattr(self, 'creation_time', 0)
                dur = max(1, int(getattr(self, 'duration', 1000)))
                
                # 簡単なフェード計算（計算量削減）
                if elapsed < 200:  # フェードイン期間短縮
                    alpha_ratio = elapsed / 200.0
                elif elapsed > dur - 200:  # フェードアウト期間短縮
                    alpha_ratio = (dur - elapsed) / 200.0
                else:
                    alpha_ratio = 1.0
                
                alpha_ratio = max(0.0, min(1.0, alpha_ratio))
                alpha_level = int(alpha_ratio * 4) * 25  # 5段階に削減: 0, 25, 50, 75, 100
                alpha = int(255 * alpha_level / 100)
                
                # キャッシュキーを簡略化
                cache_key = f"book_{w}x{h}_r{book_rotation_rounded}_a{alpha_level}"
                
                # 統合キャッシュ（1段階キャッシュに簡略化）
                if not hasattr(Attack, '_book_unified_cache'):
                    Attack._book_unified_cache = {}
                
                if cache_key not in Attack._book_unified_cache:
                    try:
                        book_image = Attack._load_weapon_image("rotating_book")
                        if book_image:
                            # 一度に全ての変換を適用
                            book_scaled = pygame.transform.scale(book_image, (w, h))
                            if book_rotation_rounded != 0:
                                book_scaled = pygame.transform.rotate(book_scaled, -book_rotation_rounded)
                            if alpha < 255:
                                book_scaled = book_scaled.copy()
                                book_scaled.set_alpha(alpha)
                            Attack._book_unified_cache[cache_key] = book_scaled
                        else:
                            Attack._book_unified_cache[cache_key] = None
                    except Exception:
                        Attack._book_unified_cache[cache_key] = None
                    
                    # キャッシュサイズ制限を強化
                    if len(Attack._book_unified_cache) > 60:  # 制限をより厳しく
                        keys = list(Attack._book_unified_cache.keys())
                        for old_key in keys[:15]:
                            del Attack._book_unified_cache[old_key]
                
                final_texture = Attack._book_unified_cache[cache_key]
                if final_texture:
                    tw, th = final_texture.get_size()
                    screen.blit(final_texture, (sx - tw//2, sy - th//2))
                else:
                    # 最軽量フォールバック
                    pygame.draw.rect(screen, (200,180,80), (sx - w//2, sy - h//2, w, h))
            except Exception:
                # 最終フォールバック
                pygame.draw.rect(screen, (200,180,80), (sx - 9, sy - 6, 18, 12))
            except Exception:
                pygame.draw.rect(screen, (200,180,80), (sx - 9, sy - 6, 18, 12))
        elif self.type == "knife":
            # ナイフは小さな三角形で高速に移動するため短い尾を描画
            try:
                vx = getattr(self, 'velocity_x', 0)
                vy = getattr(self, 'velocity_y', 0)
                ang = math.atan2(vy, vx) if vx != 0 or vy != 0 else 0

                # 表示サイズは size_x / size を基準にスケーリング
                base_size = max(2, int(getattr(self, 'size_x', getattr(self, 'size', 4))))
                tip_dist = max(4, int(base_size * 1.6))
                side_dist = max(3, int(base_size * 1.2))

                # 三角形の先端と基底を計算（サイズに応じてスケール）
                tip = (int(self.x - camera_x + math.cos(ang) * tip_dist), int(self.y - camera_y + math.sin(ang) * tip_dist))
                left = (int(self.x - camera_x + math.cos(ang + 2.5) * side_dist), int(self.y - camera_y + math.sin(ang + 2.5) * side_dist))
                right = (int(self.x - camera_x + math.cos(ang - 2.5) * side_dist), int(self.y - camera_y + math.sin(ang - 2.5) * side_dist))

                pygame.draw.polygon(screen, (220,220,220), [tip, left, right])
                pygame.draw.polygon(screen, BLACK, [tip, left, right], 1)
            except Exception:
                # フォールバック: サイズに応じた小さな円を描画
                try:
                    r = max(1, int(getattr(self, 'size_x', getattr(self, 'size', 4)) / 2))
                    pygame.draw.circle(screen, (220,220,220), (int(sx), int(sy)), r)
                except Exception:
                    pygame.draw.circle(screen, (220,220,220), (int(sx), int(sy)), 3)
        elif self.type == "thunder":
            # サンダー: 着地前は細長い光、着地時は衝撃波的に描画
            try:
                if not getattr(self, 'struck', False):
                    # 落下中は線を描く
                    x0 = int(self.x - camera_x)
                    y0 = int(getattr(self, 'strike_from_y', self.y) - camera_y)
                    x1 = int(self.x - camera_x)
                    y1 = int(self.y - camera_y)
                    pygame.draw.line(screen, (240,240,80), (x0, y0), (x1, y1), 3)
                else:
                    # 着地時の短い閃光と円
                    cx = int(self.x - camera_x)
                    cy = int(self.y - camera_y)
                    r = max(6, int(self.size))
                    s = pygame.Surface((r*4+4, r*4+4), pygame.SRCALPHA)
                    pygame.draw.circle(s, (255, 255, 200, 180), (r*2+2, r*2+2), r)
                    try:
                        screen.blit(s, (cx - (r*2+2), cy - (r*2+2)))
                    except Exception:
                        pass
                    pygame.draw.circle(screen, (255, 230, 120), (cx, cy), r, 2)
            except Exception:
                pygame.draw.circle(screen, (255, 230, 120), (int(sx), int(sy)), max(2, int(self.size)))

    def _draw_axe_fallback(self, screen, sx, sy, camera_x, camera_y):
        """斧の画像がない場合のフォールバック描画（従来の四角形）"""
        points = [
            (self.x - self.size_x/2, self.y),
            (self.x, self.y - self.size_y/2),
            (self.x + self.size_x/2, self.y),
            (self.x, self.y + self.size_y/2)
        ]
        # 点を回転
        rotated_points = []
        for px, py in points:
            dx = px - self.x
            dy = py - self.y
            rx = dx * math.cos(self.angle) - dy * math.sin(self.angle)
            ry = dx * math.sin(self.angle) + dy * math.cos(self.angle)
            rotated_points.append((int(self.x + rx - camera_x), int(self.y + ry - camera_y)))
        
        pygame.draw.polygon(screen, GRAY, rotated_points)