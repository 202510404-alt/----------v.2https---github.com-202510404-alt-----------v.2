import pygame
import math
import config
import utils
from core.grid import enemy_grid

class StormProjectile:
    def __init__(self, world_x, world_y, move_angle, damage, radius):
        # 위치 및 각도 초기화
        self.world_x = float(world_x % config.MAP_WIDTH)
        self.world_y = float(world_y % config.MAP_HEIGHT)
        self.move_angle = move_angle
        self.rotation_angle = 0.0
        self.rotation_speed = 0.15
        
        self.damage = damage 
        self.radius = radius
        self.speed = config.STORM_PROJECTILE_SPEED
        self.color = config.STORM_COLOR
        self.lifespan = config.STORM_PROJECTILE_LIFESPAN_SECONDS * config.FPS
        
        self.enemy_hit_timers = {} 
        self.hit_interval = config.FPS // 4 
        self.search_cells = math.ceil(self.radius / 250) + 1

        # 🚩 캐싱 로직: 미리 그리기 (Pre-rendering)
        self._cache_image()

    def _cache_image(self):
        """태풍 이미지를 별도의 Surface에 미리 그립니다."""
        # 반지름의 2배 크기로 충분한 공간 확보
        diameter = int(self.radius * 2)
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        
        # 중심점 기준으로 삼각형 생성
        center = (self.radius, self.radius)
        points = []
        for i in range(3):
            # 초기 회전각 0을 기준으로 그림
            angle = i * (2 * math.pi / 3)
            px = center[0] + self.radius * math.cos(angle)
            py = center[1] + self.radius * math.sin(angle)
            points.append((px, py))
        
        pygame.draw.polygon(self.image, self.color, points)

    def update(self, all_slimes_list):
        self.lifespan -= 1
        if self.lifespan <= 0: return False

        # 이동
        self.world_x = (self.world_x + math.cos(self.move_angle) * self.speed) % config.MAP_WIDTH
        self.world_y = (self.world_y + math.sin(self.move_angle) * self.speed) % config.MAP_HEIGHT
        
        # 🚩 회전 처리: 이미지를 회전시키는 대신 rotation_angle만 업데이트
        self.rotation_angle += self.rotation_speed

        # 히트 타이머 업데이트
        for enemy in list(self.enemy_hit_timers.keys()):
            self.enemy_hit_timers[enemy] -= 1
            if self.enemy_hit_timers[enemy] <= 0:
                del self.enemy_hit_timers[enemy]

        # 주변 적 탐색 및 데미지 처리
        nearby_enemies = enemy_grid.get_nearby_enemies(self.world_x, self.world_y, self.search_cells)
        rad_sq = (self.radius + 15)**2 
        
        for slime in nearby_enemies:
            if slime.hp > 0 and slime not in self.enemy_hit_timers:
                dist_sq = utils.distance_sq_wrapped(self.world_x, self.world_y, slime.world_x, slime.world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
                if dist_sq < rad_sq:
                    slime.take_damage(self.damage)
                    self.enemy_hit_timers[slime] = self.hit_interval
        return True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        # 🚩 실시간 회전 적용
        rotated_image = pygame.transform.rotate(self.image, math.degrees(-self.rotation_angle))
        rotated_rect = rotated_image.get_rect()

        # 9방향 그리기 로직 (캐싱된 이미지 사용)
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                screen_x = (self.world_x + dx_offset) - camera_offset_x
                screen_y = (self.world_y + dy_offset) - camera_offset_y

                # 화면 범위 체크
                if -self.radius < screen_x < config.SCREEN_WIDTH + self.radius and \
                   -self.radius < screen_y < config.SCREEN_HEIGHT + self.radius:
                    
                    # 회전된 이미지의 중심을 이동 위치에 맞춤
                    rotated_rect.center = (screen_x, screen_y)
                    surface.blit(rotated_image, rotated_rect)
                    return # 최적화: 한 번 그렸으면 종료