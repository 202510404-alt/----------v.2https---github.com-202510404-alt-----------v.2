import pygame
import math
import config
import utils
from core.grid import enemy_grid

class StormProjectile:
    def __init__(self, world_x, world_y, move_angle, damage):
        self.world_x = float(world_x % config.MAP_WIDTH)
        self.world_y = float(world_y % config.MAP_HEIGHT)
        self.move_angle = move_angle # 날아가는 방향
        self.rotation_angle = 0.0    # 빙글빙글 도는 각도
        self.rotation_speed = 0.15   # 회전 속도 (취향에 따라 조절)
        
        self.damage = 20 # 0.25초마다 줄 고정 대미지
        self.speed = config.STORM_PROJECTILE_SPEED
        self.radius = config.STORM_PROJECTILE_RADIUS
        self.color = config.STORM_COLOR
        self.lifespan = config.STORM_PROJECTILE_LIFESPAN_SECONDS * config.FPS
        
        # 🚩 0.25초(15프레임) 타격 주기를 위한 쿨타임 관리
        self.enemy_hit_timers = {} # {슬라임객체: 남은_쿨타임_프레임}
        self.hit_interval = config.FPS // 4 # 60FPS 기준 15프레임 (0.25초)
        
        # 그리드 탐색 범위 (반지름 기반)
        self.search_cells = math.ceil(self.radius / 250) + 1

    def update(self, all_slimes_list):
        self.lifespan -= 1
        if self.lifespan <= 0:
            return False

        # 1. 위치 이동 및 회전
        self.world_x = (self.world_x + math.cos(self.move_angle) * self.speed) % config.MAP_WIDTH
        self.world_y = (self.world_y + math.sin(self.move_angle) * self.speed) % config.MAP_HEIGHT
        self.rotation_angle += self.rotation_speed

        # 2. 개별 적 대미지 쿨타임 감소 루프
        # 리스트 복사본으로 루프 돌려서 안전하게 삭제
        for enemy in list(self.enemy_hit_timers.keys()):
            self.enemy_hit_timers[enemy] -= 1
            if self.enemy_hit_timers[enemy] <= 0:
                del self.enemy_hit_timers[enemy]

        # 3. 그리드에서 주변 적만 가져오기
        nearby_enemies = enemy_grid.get_nearby_enemies(self.world_x, self.world_y, self.search_cells)
        rad_sq = (self.radius + 15)**2 # 판정 범위 약간 보정
        
        for slime in nearby_enemies:
            if slime.hp > 0:
                # 🚩 이미 0.25초 안에 맞았다면 무시
                if slime in self.enemy_hit_timers:
                    continue
                
                # 거리 계산
                dist_sq = utils.distance_sq_wrapped(
                    self.world_x, self.world_y, 
                    slime.world_x, slime.world_y, 
                    config.MAP_WIDTH, config.MAP_HEIGHT
                )
                
                # 🚩 범위 안이면 대미지 주고 0.25초 쿨타임 등록
                if dist_sq < rad_sq:
                    slime.take_damage(self.damage)
                    self.enemy_hit_timers[slime] = self.hit_interval
                    
        return True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        # 맵 래핑 대응 그리기
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                screen_x = (self.world_x + dx_offset) - camera_offset_x
                screen_y = (self.world_y + dy_offset) - camera_offset_y

                # 화면 안에 있을 때만 그리기 연산 수행
                if -self.radius < screen_x < config.SCREEN_WIDTH + self.radius and \
                   -self.radius < screen_y < config.SCREEN_HEIGHT + self.radius:
                    
                    # 🚩 삼각형의 3개 꼭짓점 좌표 계산
                    points = []
                    for i in range(3):
                        # 120도(2*pi/3) 간격으로 점을 찍음
                        angle = self.rotation_angle + (i * (2 * math.pi / 3))
                        px = screen_x + self.radius * math.cos(angle)
                        py = screen_y + self.radius * math.sin(angle)
                        points.append((px, py))
                    
                    # 투명도가 포함된 삼각형 그리기 (Surface 매번 생성 대신 바로 그리기 시도)
                    # 성능을 위해 화면 전체 Surface가 아닌 최소 범위만 그려도 되지만 일단 로직 우선
                    temp_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.polygon(temp_surface, self.color, points)
                    surface.blit(temp_surface, (0, 0))
                    return # 중복 그리기 방지