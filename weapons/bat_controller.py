# weapons/bat_controller.py
import random
import math
import pygame
import config
import utils
from weapons.base_weapon import Weapon
from entities.bat_minion import BatMinion # 박쥐 미니언을 생성하기 위해

class BatController(Weapon):
    def __init__(self, player_ref):
        super().__init__(player_ref)
        self.name = "박쥐 소환"
        self.damage = config.BAT_BASE_DAMAGE
        self.lifesteal_percentage = config.BAT_LIFESTEAL_PERCENTAGE
        self.max_bats = config.BAT_MAX_COUNT_INITIAL
        self.spawn_cooldown = config.FPS * 1
        self.spawn_timer = 0

    def update(self, slimes_list, game_entities_lists):
        bats_list_ref = game_entities_lists.get('bats')
        if bats_list_ref is None: return

        self.spawn_timer += 1
        current_bat_count = 0
        for bat_obj in bats_list_ref:
            if isinstance(bat_obj, BatMinion) and bat_obj.controller == self: # 이 컨트롤러가 소환한 박쥐만 카운트
                current_bat_count +=1

        if current_bat_count < self.max_bats and self.spawn_timer >= self.spawn_cooldown:
            self.spawn_timer = 0
            spawn_angle = random.uniform(0, 2 * math.pi)
            spawn_dist = random.uniform(config.PLAYER_SIZE, config.PLAYER_SIZE + 20)
            spawn_x = self.player.world_x + spawn_dist * math.cos(spawn_angle)
            spawn_y = self.player.world_y + spawn_dist * math.sin(spawn_angle)
            bats_list_ref.append(BatMinion(self, spawn_x, spawn_y))

    def draw(self, surface, camera_offset_x, camera_offset_y):
        pass # 박쥐 컨트롤러 자체는 화면에 그릴 것이 없음

    def get_level_up_options(self):
        options = [
            {"text": f"박쥐 데미지 ({self.damage} -> {math.ceil(self.damage*config.BAT_DAMAGE_MULTIPLIER_PER_LEVEL)})", "type": "damage", "value": math.ceil(self.damage*config.BAT_DAMAGE_MULTIPLIER_PER_LEVEL)},
            {"text": f"최대 박쥐 수 ({self.max_bats} -> {self.max_bats+config.BAT_MAX_COUNT_INCREASE_PER_LEVEL})", "type": "max_bats", "value": self.max_bats+config.BAT_MAX_COUNT_INCREASE_PER_LEVEL},
            {"text": f"박쥐 흡혈량 ({(self.lifesteal_percentage*100):.0f}% -> {((self.lifesteal_percentage+0.02)*100):.0f}%)", "type": "lifesteal", "value": min(1.0,self.lifesteal_percentage+0.02)}
        ]
        return random.sample(options, min(len(options), 2))

    def apply_upgrade(self, upgrade_info):
        if upgrade_info["type"] == "damage": self.damage = upgrade_info["value"]
        elif upgrade_info["type"] == "max_bats": self.max_bats = upgrade_info["value"]
        elif upgrade_info["type"] == "lifesteal": self.lifesteal_percentage = upgrade_info["value"]
        self.level += 1
    
    def on_remove(self):
        pass # 실제 제거 로직은 main.py에서 담당