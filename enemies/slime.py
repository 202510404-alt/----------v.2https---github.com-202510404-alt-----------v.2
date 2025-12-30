import pygame
import math
import os
import config
import utils

class Slime:
    _animation_cache = {}

    def __init__(self, world_x, world_y, radius, color, speed, current_total_max_hp, hp_multiplier=1.0):
        self.world_x = float(world_x % config.MAP_WIDTH)
        self.world_y = float(world_y % config.MAP_HEIGHT)
        self.radius = radius
        self.color = color
        self.speed = speed
        
        # 난이도에 따른 HP 설정
        self.max_hp = math.ceil(current_total_max_hp * hp_multiplier)
        self.hp = self.max_hp

        # 피격 이펙트 타이머
        self.hit_flash_timer = 0
        self.flash_duration = 5 
        
        self.rect = pygame.Rect(0,0,radius*2,radius*2)
        self.rect.center = (self.world_x,self.world_y)
        self.lifespan = config.SLIME_LIFESPAN_SECONDS * config.FPS
        
        # 🟢 [수정] 공격력 계산 로직: 기본 데미지 + 최대 체력의 1%
        # 보스 등의 급격한 데미지 상승을 방지하려면 math.ceil이나 int로 정수화하는 것이 좋습니다.
        self.base_damage = config.SLIME_DAMAGE_TO_PLAYER
        self.damage_to_player = self.base_damage + (self.max_hp * 0.01)

        self.animation_images = self._load_animation_images()
        self.animation_sequence = [0, 1, 2, 3, 2, 1, 4, 0] 
        self.current_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.1 

    def _get_image_filename_prefix(self):
        class_name = self.__class__.__name__
        if class_name == "Slime": return "slime"
        if class_name == "MintSlime": return "mintslime"
        if class_name == "ShooterSlime": return "shooterslime"
        if class_name == "BossSlime": return "slimeboss"
        if class_name == "BossMinionSlime": return "minislime"
        return "slime"

    def _load_animation_images(self):
        prefix = self._get_image_filename_prefix()
        if prefix in Slime._animation_cache:
            return Slime._animation_cache[prefix]

        images = []
        try:
            path = os.path.join('image', 'slimes')
            for i in range(1, 6):
                img_path = os.path.join(path, f"{prefix}{i}.png")
                original_image = pygame.image.load(img_path).convert_alpha()
                scaled_image = pygame.transform.scale(original_image, (self.radius * 2, self.radius * 2))
                images.append(scaled_image)
            Slime._animation_cache[prefix] = images
        except Exception as e:
            Slime._animation_cache[prefix] = [] 
        return Slime._animation_cache[prefix]

    def update(self, target_player_world_x, target_player_world_y, game_entities_lists=None):
        if self.hp <= 0: return False

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        self.lifespan -= 1
        if self.lifespan <= 0: self.hp = 0; return False

        dist_sq = utils.distance_sq_wrapped(self.world_x, self.world_y, target_player_world_x, target_player_world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
        dist = math.sqrt(dist_sq)
        stop_distance = config.PLAYER_SIZE / 2 + self.radius

        # 플레이어 방향으로 이동
        if dist > stop_distance:
            dx = utils.get_wrapped_delta(self.world_x, target_player_world_x, config.MAP_WIDTH)
            dy = utils.get_wrapped_delta(self.world_y, target_player_world_y, config.MAP_HEIGHT)
            self.world_x = (self.world_x + (dx / dist) * self.speed) % config.MAP_WIDTH
            self.world_y = (self.world_y + (dy / dist) * self.speed) % config.MAP_HEIGHT

        # 애니메이션 업데이트
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed * config.FPS:
            self.animation_timer = 0
            self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_sequence)

        self.rect.center = (int(self.world_x), int(self.world_y))
        
        # 🟢 [추가 로직] 플레이어와 충돌 시 데미지 주기 (main.py에서 처리하지만, 값 확인용)
        # 이 슬라임의 self.damage_to_player 값이 플레이어의 take_damage로 전달됩니다.
        
        return True

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash_timer = self.flash_duration 
        if self.hp <= 0: self.hp = 0; return True
        return False
    
    def draw(self, surface, camera_offset_x, camera_offset_y):
        # 맵 래핑 그리기 최적화 (가장 가까운 위치 하나만 그리기 위해 return 활용 가능하지만 기존 구조 유지)
        for dx_off in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_off in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                obj_wx_render, obj_wy_render = self.world_x+dx_off, self.world_y+dy_off
                scr_x, scr_y = obj_wx_render-camera_offset_x, obj_wy_render-camera_offset_y

                if -self.radius < scr_x < config.SCREEN_WIDTH+self.radius and \
                   -self.radius < scr_y < config.SCREEN_HEIGHT+self.radius:

                    if self.animation_images:
                        frame_index = self.animation_sequence[self.current_frame_index]
                        original_image = self.animation_images[frame_index]
                        
                        render_image = original_image
                        if self.hit_flash_timer > 0:
                            # 피격 시 빨간색 효과
                            render_image = original_image.copy()
                            flash_surf = pygame.Surface(render_image.get_size(), pygame.SRCALPHA)
                            flash_surf.fill((255, 50, 50, 180)) # 불투명도를 약간 조절하여 피격 느낌 강조
                            render_image.blit(flash_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        
                        surface.blit(render_image, render_image.get_rect(center=(int(scr_x), int(scr_y))))
                    else: 
                        draw_color = (255, 0, 0) if self.hit_flash_timer > 0 else self.color
                        pygame.draw.circle(surface, draw_color, (int(scr_x), int(scr_y)), self.radius)

                    # HP 바 그리기
                    if self.hp < self.max_hp and self.hp > 0:
                        bar_width = self.radius * 2
                        bar_height = config.SLIME_HP_BAR_HEIGHT
                        bar_screen_x = scr_x - bar_width//2
                        bar_screen_y = scr_y - self.radius - bar_height - 5
                        pygame.draw.rect(surface, config.DARK_RED, (bar_screen_x, bar_screen_y, bar_width, bar_height))
                        current_hp_bar_width = int(bar_width*(self.hp/self.max_hp)) if self.max_hp>0 else 0
                        if current_hp_bar_width > 0: 
                            pygame.draw.rect(surface, config.HP_BAR_GREEN, (bar_screen_x, bar_screen_y, current_hp_bar_width, bar_height))
                    return # 최적화: 9개 중 하나 그렸으면 탈출