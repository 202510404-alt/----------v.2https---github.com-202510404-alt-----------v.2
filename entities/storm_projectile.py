import pygame
import math
import config
import utils
from core.grid import enemy_grid

class StormProjectile:
    def __init__(self, world_x, world_y, move_angle, damage, radius):
        # 1. 위치 및 각도 초기화
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
        
        # 🚩 [최적화] 이동 벡터 및 충돌 범위 미리 계산
        self.vx = math.cos(self.move_angle) * self.speed
        self.vy = math.sin(self.move_angle) * self.speed
        self.hit_radius_sq = (self.radius + 15)**2
        
        self.enemy_hit_timers = {} 
        self.hit_interval = config.FPS // 4 
        self.search_cells = math.ceil(self.radius / 250) + 1

        # 🚩 [최적화] 드로잉용 전용 서피스 생성 (회전 연산 대용)
        # 반지름의 2배 크기보다 약간 크게 설정
        self.surf_size = int(self.radius * 2) + 4
        self.proj_surface = pygame.Surface((self.surf_size, self.surf_size), pygame.SRCALPHA)
        self.center_pos = self.surf_size // 2

    def update(self, all_slimes_list):
        self.lifespan -= 1
        if self.lifespan <= 0: return False

        # 🚩 [최적화] 미리 계산된 벡터로 이동
        self.world_x = (self.world_x + self.vx) % config.MAP_WIDTH
        self.world_y = (self.world_y + self.vy) % config.MAP_HEIGHT
        
        # 회전 각도 업데이트
        self.rotation_angle += self.rotation_speed

        # 히트 타이머 업데이트
        if self.enemy_hit_timers:
            for enemy in list(self.enemy_hit_timers.keys()):
                self.enemy_hit_timers[enemy] -= 1
                if self.enemy_hit_timers[enemy] <= 0:
                    del self.enemy_hit_timers[enemy]

        # 주변 적 탐색 및 데미지 처리
        nearby_enemies = enemy_grid.get_nearby_enemies(self.world_x, self.world_y, self.search_cells)
        
        for slime in nearby_enemies:
            if slime.hp > 0 and slime not in self.enemy_hit_timers:
                dist_sq = utils.distance_sq_wrapped(self.world_x, self.world_y, slime.world_x, slime.world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
                if dist_sq < self.hit_radius_sq:
                    slime.take_damage(self.damage)
                    self.enemy_hit_timers[slime] = self.hit_interval
        return True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        # 🚩 [최적화] rotate 함수 대신 직접 폴리곤 좌표 계산하여 그리기
        self.proj_surface.fill((0, 0, 0, 0)) # 서피스 초기화
        
        points = []
        for i in range(3):
            # 현재 회전각(self.rotation_angle)을 적용하여 3개의 점 계산
            angle = self.rotation_angle + (i * (2 * math.pi / 3))
            px = self.center_pos + self.radius * math.cos(angle)
            py = self.center_pos + self.radius * math.sin(angle)
            points.append((px, py))
        
        # 작은 전용 서피스에 삼각형 그리기
        pygame.draw.polygon(self.proj_surface, self.color, points)

        # 9방향 그리기 로직 (최적화된 이미지 사용)
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                screen_x = (self.world_x + dx_offset) - camera_offset_x
                screen_y = (self.world_y + dy_offset) - camera_offset_y

                # 화면 범위 체크
                if -self.radius < screen_x < config.SCREEN_WIDTH + self.radius and \
                   -self.radius < screen_y < config.SCREEN_HEIGHT + self.radius:
                    
                    # 미리 그려둔 서피스를 화면에 blit
                    surface.blit(self.proj_surface, (screen_x - self.center_pos, screen_y - self.center_pos))
                    
                    # 화면 중앙에 그려졌다면 나머지 8방향 체크 생략하고 리턴
                    if (self.radius < screen_x < config.SCREEN_WIDTH - self.radius and 
                        self.radius < screen_y < config.SCREEN_HEIGHT - self.radius):
                        return