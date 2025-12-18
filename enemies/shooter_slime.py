# enemies/shooter_slime.py (수정됨)
import random
import math
import pygame
import config
import utils
from enemies.slime import Slime
from entities.slime_bullet import SlimeBullet # 슬라임 총알을 발사하기 위해

class ShooterSlime(Slime):
    # 슈터 슬라임도 current_total_max_hp를 받아서 계산
    def __init__(self, world_x, world_y, current_total_max_hp):
        radius = config.SLIME_RADIUS
        speed = config.SLIME_SPEED * config.SHOOTER_SLIME_SPEED_FACTOR
        # ShooterSlime은 기본 슬라임과 동일한 HP를 가지므로, hp_multiplier를 1.0으로 전달
        super().__init__(world_x, world_y, radius, config.SHOOTER_SLIME_COLOR, speed, current_total_max_hp, hp_multiplier=1.0)
        self.shoot_cooldown_timer = random.randint(0, config.SHOOTER_SLIME_SHOOT_COOLDOWN)

    def update(self, target_player_world_x, target_player_world_y, game_entities_lists):
        if not super().update(target_player_world_x, target_player_world_y, game_entities_lists):
            return False

        self.shoot_cooldown_timer -= 1
        if self.shoot_cooldown_timer <= 0:
            self.shoot_cooldown_timer = config.SHOOTER_SLIME_SHOOT_COOLDOWN

            slime_bullets_list_ref = game_entities_lists.get('slime_bullets')
            if slime_bullets_list_ref is not None:
                dx_to_player = utils.get_wrapped_delta(self.world_x, target_player_world_x, config.MAP_WIDTH)
                dy_to_player = utils.get_wrapped_delta(self.world_y, target_player_world_y, config.MAP_HEIGHT)
                angle = math.atan2(dy_to_player, dx_to_player)

                bullet_spawn_x = self.world_x + math.cos(angle) * (self.radius + config.SLIME_BULLET_SIZE)
                bullet_spawn_y = self.world_y + math.sin(angle) * (self.radius + config.SLIME_BULLET_SIZE)

                slime_bullets_list_ref.append(SlimeBullet(bullet_spawn_x, bullet_spawn_y, angle))
        return True