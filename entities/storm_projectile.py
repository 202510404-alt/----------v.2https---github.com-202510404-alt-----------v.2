# entities/storm_projectile.py
import pygame
import math
import config
import utils

class StormProjectile:
    def __init__(self, world_x, world_y, angle, damage):
        self.world_x = float(world_x % config.MAP_WIDTH)
        self.world_y = float(world_y % config.MAP_HEIGHT)
        self.angle = angle
        self.damage = damage
        self.speed = config.STORM_PROJECTILE_SPEED
        self.radius = config.STORM_PROJECTILE_RADIUS
        self.color = config.STORM_COLOR
        self.lifespan = config.STORM_PROJECTILE_LIFESPAN_SECONDS * config.FPS
        self.hit_slimes = set()

    def update(self, all_slimes_list):
        self.lifespan -= 1
        if self.lifespan <= 0:
            return False

        self.world_x = (self.world_x + math.cos(self.angle) * self.speed) % config.MAP_WIDTH
        self.world_y = (self.world_y + math.sin(self.angle) * self.speed) % config.MAP_HEIGHT

        for slime in all_slimes_list:
            if slime.hp > 0 and slime not in self.hit_slimes:
                required_dist_sq = (self.radius + slime.radius)**2
                if utils.distance_sq_wrapped(self.world_x, self.world_y, slime.world_x, slime.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < required_dist_sq:
                    slime.take_damage(self.damage)
                    self.hit_slimes.add(slime)
        return True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        for dx_offset in [-config.MAP_WIDTH, 0, config.MAP_WIDTH]:
            for dy_offset in [-config.MAP_HEIGHT, 0, config.MAP_HEIGHT]:
                obj_world_x = self.world_x + dx_offset
                obj_world_y = self.world_y + dy_offset
                screen_x = obj_world_x - camera_offset_x
                screen_y = obj_world_y - camera_offset_y

                if -self.radius < screen_x < config.SCREEN_WIDTH + self.radius and \
                   -self.radius < screen_y < config.SCREEN_HEIGHT + self.radius:

                    temp_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(temp_surface, self.color, (self.radius, self.radius), self.radius)
                    surface.blit(temp_surface, (int(screen_x - self.radius), int(screen_y - self.radius)))
                    return