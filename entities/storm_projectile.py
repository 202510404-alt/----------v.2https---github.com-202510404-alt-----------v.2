import pygame
import math
import config
import utils
from core.grid import enemy_grid

class StormProjectile:
    def __init__(self, world_x, world_y, move_angle, damage, radius):
        # 위치 및 각도 초기화 (맵 래핑 적용)
        self.world_x = float(world_x % config.MAP_WIDTH)
        self.world_y = float(world_y % config.MAP_HEIGHT)
        self.move_angle = move_angle
        self.rotation_angle = 0.0
        self.rotation_speed = 0.15
        
        # 스킬로부터 전달받은 현재 강화 수치 적용
        self.damage = damage 
        self.radius = radius
        
        # config 상수를 이용한 기본 설정
        self.speed = config.STORM_PROJECTILE_SPEED
        self.color = config.STORM_COLOR
        self.lifespan = config.STORM_PROJECTILE_LIFESPAN_SECONDS * config.FPS
        
        # 타격 타이머 (다단 히트 방지)
        self.enemy_hit_timers = {} 
        self.hit_interval = config.FPS // 4 # 0.25초 주기
        
        # 그리드 탐색 범위 자동 계산
        self.search_cells = math.ceil(self.radius / 250) + 1

    def update(self, all_slimes_list):
        self.lifespan -= 1
        if self.lifespan <= 0: return False

        # 이동 및 회전
        self.world_x = (self.world_x + math.cos(self.move_angle) * self.speed) % config.MAP_WIDTH
        self.world_y = (self.world_y + math.sin(self.move_angle) * self.speed) % config.MAP_HEIGHT
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
        # 맵 래핑을 고려한 9방향 그리기
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                screen_x = (self.world_x + dx_offset) - camera_offset_x
                screen_y = (self.world_y + dy_offset) - camera_offset_y

                # 화면 안에 있을 때만 그리기
                if -self.radius < screen_x < config.SCREEN_WIDTH + self.radius and \
                   -self.radius < screen_y < config.SCREEN_HEIGHT + self.radius:
                    
                    points = []
                    for i in range(3):
                        angle = self.rotation_angle + (i * (2 * math.pi / 3))
                        px = screen_x + self.radius * math.cos(angle)
                        py = screen_y + self.radius * math.sin(angle)
                        points.append((px, py))
                    
                    # 투명도가 적용된 삼각형 그리기
                    temp_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.polygon(temp_surface, self.color, points)
                    surface.blit(temp_surface, (0, 0))
                    return # 최적화: 하나 그렸으면 탈출