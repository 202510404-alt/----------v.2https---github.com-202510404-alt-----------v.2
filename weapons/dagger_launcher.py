# weapons/dagger_launcher.py
import random
import math
import pygame
import config
import utils
from weapons.base_weapon import Weapon
from entities.dagger import Dagger # 단검을 생성하기 위해

class DaggerLauncher(Weapon):
    def __init__(self, player_ref):
        super().__init__(player_ref)
        self.name = "단검"
        self.damage = config.PLAYER_DAGGER_DAMAGE_BASE
        self.cooldown = config.PLAYER_ATTACK_COOLDOWN
        self.attack_timer = 0
        self.num_daggers_per_shot = 1

    def update(self, slimes_list, game_entities_lists):
        daggers_list_ref = game_entities_lists.get('daggers')
        if daggers_list_ref is None: return

        self.attack_timer += 1
        if self.attack_timer >= self.cooldown:
            all_slimes = slimes_list + game_entities_lists.get('boss_slimes', [])
            living_slimes = [s for s in all_slimes if s.hp > 0]
            if not living_slimes: return

            self.attack_timer = 0
            player_wx,player_wy = self.player.world_x,self.player.world_y
            targets_to_shoot = []
            if len(living_slimes) <= self.num_daggers_per_shot:
                targets_to_shoot.extend(living_slimes)
            else:
                sorted_slimes = sorted(living_slimes,key=lambda s:utils.distance_sq_wrapped(player_wx,player_wy,s.world_x,s.world_y,config.MAP_WIDTH,config.MAP_HEIGHT))
                targets_to_shoot.extend(sorted_slimes[:self.num_daggers_per_shot])
            for target_slime_for_dagger in targets_to_shoot:
                if target_slime_for_dagger:
                    daggers_list_ref.append(Dagger(player_wx,player_wy,target_slime_for_dagger,self.damage))

    def get_level_up_options(self):
        options=[{"text":f"데미지 ({self.damage} -> {math.ceil(self.damage*config.PLAYER_DAGGER_DAMAGE_MULTIPLIER_PER_LEVEL)})","type":"damage","value":math.ceil(self.damage*config.PLAYER_DAGGER_DAMAGE_MULTIPLIER_PER_LEVEL)},
                 {"text":f"공속 (쿨다운 {self.cooldown} -> {max(10,self.cooldown-5)})","type":"cooldown","value":max(10,self.cooldown-5)},
                 {"text":f"발사 수 ({self.num_daggers_per_shot} -> {self.num_daggers_per_shot+1})","type":"num_daggers","value":self.num_daggers_per_shot+1}]
        return random.sample(options,min(len(options),2))

    def apply_upgrade(self, upgrade_info):
        if upgrade_info["type"]=="damage":self.damage=upgrade_info["value"]
        elif upgrade_info["type"]=="cooldown":self.cooldown=upgrade_info["value"]
        elif upgrade_info["type"]=="num_daggers":self.num_daggers_per_shot=upgrade_info["value"]
        self.level+=1