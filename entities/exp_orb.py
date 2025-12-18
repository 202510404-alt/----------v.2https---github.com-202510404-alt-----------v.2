# entities/exp_orb.py
import pygame
import math
import config
import utils

class ExpOrb:
    def __init__(self, world_x, world_y):
        self.world_x = float(world_x % config.MAP_WIDTH)
        self.world_y = float(world_y % config.MAP_HEIGHT)
        self.radius = config.EXP_ORB_RADIUS
        self.color = config.EXP_ORB_COLOR
        self.speed = config.EXP_ORB_SPEED
        self.rect = pygame.Rect(0,0, self.radius*2, self.radius*2)
        self.rect.center = (self.world_x, self.world_y)
        self.value = config.EXP_ORB_VALUE

    def update(self, target_player_world_x, target_player_world_y):
        dist_sq = utils.distance_sq_wrapped(self.world_x, self.world_y, target_player_world_x, target_player_world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
        dist = math.sqrt(dist_sq)
        if dist < self.speed:
            self.world_x = target_player_world_x
            self.world_y = target_player_world_y
            return True
        elif dist > 0:
            dx_move = utils.get_wrapped_delta(self.world_x, target_player_world_x, config.MAP_WIDTH)
            dy_move = utils.get_wrapped_delta(self.world_y, target_player_world_y, config.MAP_HEIGHT)
            self.world_x += (dx_move / dist) * self.speed
            self.world_y += (dy_move / dist) * self.speed
        self.world_x %= config.MAP_WIDTH
        self.world_y %= config.MAP_HEIGHT
        return False

    def draw(self, surface, camera_offset_x, camera_offset_y):
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                obj_world_x = self.world_x + dx_offset
                obj_world_y = self.world_y + dy_offset
                screen_x = obj_world_x - camera_offset_x
                screen_y = obj_world_y - camera_offset_y
                if -self.radius < screen_x < config.SCREEN_WIDTH + self.radius and \
                   -self.radius < screen_y < config.SCREEN_HEIGHT + self.radius:
                    pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), self.radius)
                    return