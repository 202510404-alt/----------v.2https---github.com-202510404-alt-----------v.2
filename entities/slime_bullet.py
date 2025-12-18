# entities/slime_bullet.py
import pygame
import math
import config
import utils

class SlimeBullet:
    def __init__(self, world_x, world_y, angle_to_player, color=config.SLIME_BULLET_COLOR):
        self.world_x = float(world_x % config.MAP_WIDTH)
        self.world_y = float(world_y % config.MAP_HEIGHT)
        self.angle = angle_to_player
        self.speed = config.SLIME_BULLET_SPEED
        self.size = config.SLIME_BULLET_SIZE
        self.color = color
        self.lifespan = config.SLIME_BULLET_LIFESPAN_SECONDS * config.FPS
        self.is_hit_by_player_attack = False

    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0 or self.is_hit_by_player_attack:
            return False

        self.world_x = (self.world_x + math.cos(self.angle) * self.speed) % config.MAP_WIDTH
        self.world_y = (self.world_y + math.sin(self.angle) * self.speed) % config.MAP_HEIGHT
        return True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                obj_world_x_render = self.world_x + dx_offset
                obj_world_y_render = self.world_y + dy_offset
                screen_x = obj_world_x_render - camera_offset_x
                screen_y = obj_world_y_render - camera_offset_y
                if -self.size < screen_x < config.SCREEN_WIDTH + self.size and \
                   -self.size < screen_y < config.SCREEN_HEIGHT + self.size:
                    pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), self.size)
                    return

    def get_world_rect_for_collision(self):
        return pygame.Rect(self.world_x - self.size // 2, self.world_y - self.size // 2, self.size, self.size)