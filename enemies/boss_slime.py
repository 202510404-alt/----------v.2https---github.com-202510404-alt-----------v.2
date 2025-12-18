# enemies/boss_slime.py (수정됨 - Pylance 오류 해결)
import random
import math
import pygame
import config
import utils
from enemies.slime import Slime
from entities.slime_bullet import SlimeBullet
from enemies.boss_minion_slime import BossMinionSlime # 미니언 소환을 위해

class BossSlime(Slime):
    def __init__(self, world_x, world_y, current_total_max_hp): 
        radius = config.SLIME_RADIUS * config.BOSS_SLIME_RADIUS_MULTIPLIER
        speed = config.SLIME_SPEED * config.BOSS_SLIME_SPEED_MULTIPLIER
        # BossSlime은 base HP의 BOSS_SLIME_HP_MULTIPLIER 배를 가짐
        super().__init__(world_x, world_y, radius, config.BOSS_SLIME_COLOR, speed, current_total_max_hp, hp_multiplier=config.BOSS_SLIME_HP_MULTIPLIER) 

        self.damage_to_player = config.BOSS_SLIME_CONTACT_DAMAGE
        self.lifespan = float('inf') 
        self.shoot_cooldown_timer = config.BOSS_SLIME_SHOOT_COOLDOWN
        self.minion_spawn_timer = config.BOSS_MINION_SPAWN_COOLDOWN
        
        # <--- 추가: current_total_max_hp를 인스턴스 변수로 저장
        self.initial_spawn_hp_for_minions = current_total_max_hp 

    def update(self, target_player_world_x, target_player_world_y, game_entities_lists):
        if self.hp <= 0: return False

        self.hp = min(self.max_hp, self.hp + config.BOSS_SLIME_REGEN_PER_SECOND / config.FPS)

        dist_sq = utils.distance_sq_wrapped(self.world_x, self.world_y, target_player_world_x, target_player_world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
        dist = math.sqrt(dist_sq)
        stop_distance = config.PLAYER_SIZE / 2 + self.radius

        if dist > self.speed + stop_distance:
            dx = utils.get_wrapped_delta(self.world_x, target_player_world_x, config.MAP_WIDTH)
            dy = utils.get_wrapped_delta(self.world_y, target_player_world_y, config.MAP_HEIGHT)
            self.world_x = (self.world_x + (dx / dist) * self.speed) % config.MAP_WIDTH
            self.world_y = (self.world_y + (dy / dist) * self.speed) % config.MAP_HEIGHT

        self.rect.center = (int(self.world_x), int(self.world_y))

        # 샷건 발사 로직
        self.shoot_cooldown_timer -= 1
        if self.shoot_cooldown_timer <= 0:
            self.shoot_cooldown_timer = config.BOSS_SLIME_SHOOT_COOLDOWN

            slime_bullets_list_ref = game_entities_lists.get('slime_bullets')
            if slime_bullets_list_ref is not None:
                dx_to_player = utils.get_wrapped_delta(self.world_x, target_player_world_x, config.MAP_WIDTH)
                dy_to_player = utils.get_wrapped_delta(self.world_y, target_player_world_y, config.MAP_HEIGHT)
                center_angle = math.atan2(dy_to_player, dx_to_player)

                angle_spread = math.radians(4) 
                angles = [center_angle - angle_spread, center_angle, center_angle + angle_spread]

                for angle in angles:
                    bullet_spawn_x = self.world_x + math.cos(angle) * (self.radius + config.SLIME_BULLET_SIZE)
                    bullet_spawn_y = self.world_y + math.sin(angle) * (self.radius + config.SLIME_BULLET_SIZE)
                    slime_bullets_list_ref.append(SlimeBullet(bullet_spawn_x, bullet_spawn_y, angle, color=config.BOSS_BULLET_COLOR))

        # 미니언 소환 로직
        self.minion_spawn_timer -= 1
        if self.minion_spawn_timer <= 0:
            self.minion_spawn_timer = config.BOSS_MINION_SPAWN_COOLDOWN
            slimes_list_ref = game_entities_lists.get('slimes')
            if slimes_list_ref is not None:
                print("보스가 미니언을 소환합니다!")
                for _ in range(config.BOSS_MINION_SPAWN_COUNT):
                    spawn_angle = random.uniform(0, 2 * math.pi)
                    spawn_dist = self.radius * 0.5 
                    spawn_x = self.world_x + math.cos(spawn_angle) * spawn_dist
                    spawn_y = self.world_y + math.sin(spawn_angle) * spawn_dist
                    # <--- 수정: 인스턴스 변수 self.initial_spawn_hp_for_minions 사용
                    slimes_list_ref.append(BossMinionSlime(spawn_x % config.MAP_WIDTH, spawn_y % config.MAP_HEIGHT, self.initial_spawn_hp_for_minions)) 

        return True