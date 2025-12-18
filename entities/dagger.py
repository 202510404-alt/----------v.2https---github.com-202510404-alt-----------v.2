# entities/dagger.py
import pygame
import math
import config
import utils

class Dagger:
    def __init__(self, start_world_x, start_world_y, target_slime, damage):
        self.world_x = float(start_world_x % config.MAP_WIDTH)
        self.world_y = float(start_world_y % config.MAP_HEIGHT)
        self.target_slime = target_slime
        self.speed = config.DAGGER_SPEED
        self.damage = damage
        self.size = config.DAGGER_SIZE
        self.angle = 0
        self.lifespan = config.DAGGER_LIFESPAN
        self.rect = pygame.Rect(0,0, self.size, self.size)
        self.rect.center = (int(self.world_x), int(self.world_y))
        self.is_hit_slime_bullet = False

        if self.target_slime:
            dx_init = utils.get_wrapped_delta(self.world_x, self.target_slime.world_x, config.MAP_WIDTH)
            dy_init = utils.get_wrapped_delta(self.world_y, self.target_slime.world_y, config.MAP_HEIGHT)
            if dx_init != 0 or dy_init != 0: self.angle = math.atan2(dy_init, dx_init)

    def update(self, game_entities_lists):
        self.lifespan -=1
        if self.lifespan <= 0 or self.is_hit_slime_bullet:
            return False 

        slime_bullets_list_ref = game_entities_lists.get('slime_bullets')
        if slime_bullets_list_ref:
            for sb in slime_bullets_list_ref:
                if sb.is_hit_by_player_attack: continue
                required_dist_sq_bullet = (self.size/2 + sb.size/2)**2
                if utils.distance_sq_wrapped(self.world_x, self.world_y, sb.world_x, sb.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < required_dist_sq_bullet:
                    sb.is_hit_by_player_attack = True
                    self.is_hit_slime_bullet = True
                    return False

        if not self.target_slime or self.target_slime.hp <= 0:
            self.target_slime = None

        if self.target_slime:
            dist_sq = utils.distance_sq_wrapped(self.world_x, self.world_y, self.target_slime.world_x, self.target_slime.world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
            dist = math.sqrt(dist_sq)
            if dist < self.speed:
                self.world_x = self.target_slime.world_x
                self.world_y = self.target_slime.world_y
            elif dist > 0:
                dx_move = utils.get_wrapped_delta(self.world_x, self.target_slime.world_x, config.MAP_WIDTH)
                dy_move = utils.get_wrapped_delta(self.world_y, self.target_slime.world_y, config.MAP_HEIGHT)
                self.angle = math.atan2(dy_move, dx_move)
                self.world_x += math.cos(self.angle) * self.speed
                self.world_y += math.sin(self.angle) * self.speed
        else:
            self.world_x += math.cos(self.angle) * self.speed
            self.world_y += math.sin(self.angle) * self.speed

        self.world_x %= config.MAP_WIDTH
        self.world_y %= config.MAP_HEIGHT
        self.rect.center = (int(self.world_x), int(self.world_y))
        return True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                obj_world_x_render = self.world_x + dx_offset
                obj_world_y_render = self.world_y + dy_offset
                screen_x = obj_world_x_render - camera_offset_x
                screen_y = obj_world_y_render - camera_offset_y
                if -self.size*2 < screen_x < config.SCREEN_WIDTH + self.size*2 and \
                   -self.size*2 < screen_y < config.SCREEN_HEIGHT + self.size*2:
                    tip_length = self.size * 0.7
                    base_width_half = self.size * 0.4 / 2 
                    tip_x = screen_x + math.cos(self.angle) * tip_length
                    tip_y = screen_y + math.sin(self.angle) * tip_length
                    base_center_offset = -self.size * 0.2
                    base_center_x = screen_x + math.cos(self.angle) * base_center_offset
                    base_center_y = screen_y + math.sin(self.angle) * base_center_offset
                    left_base_x = base_center_x + math.cos(self.angle-math.pi/2)*base_width_half
                    left_base_y = base_center_y + math.sin(self.angle-math.pi/2)*base_width_half
                    right_base_x = base_center_x + math.cos(self.angle+math.pi/2)*base_width_half
                    right_base_y = base_center_y + math.sin(self.angle+math.pi/2)*base_width_half
                    points = [(tip_x, tip_y), (left_base_x, left_base_y), (right_base_x, right_base_y)]
                    try: pygame.draw.polygon(surface, config.DAGGER_COLOR, points)
                    except TypeError: pygame.draw.polygon(surface, config.DAGGER_COLOR, [(int(p[0]), int(p[1])) for p in points])
                    return