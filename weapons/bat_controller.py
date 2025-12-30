import random
import math
import pygame
import config
import utils
from weapons.base_weapon import Weapon
from entities.bat_minion import BatMinion

class BatController(Weapon):
    def __init__(self, player_ref):
        super().__init__(player_ref)
        self.name = "박쥐 소환"
        self.damage = config.BAT_BASE_DAMAGE
        self.lifesteal_percentage = config.BAT_LIFESTEAL_PERCENTAGE # config에서 0.05로 너프된 값 사용
        self.max_bats = config.BAT_MAX_COUNT_INITIAL
        self.spawn_cooldown = config.FPS * 1 
        self.spawn_timer = 0

    def update(self, slimes_list, game_entities_lists):
        bats_list_ref = game_entities_lists.get('bats')
        if bats_list_ref is None: return

        # 1. 현재 이 컨트롤러가 소환한 살아있는 박쥐 수 체크
        current_bat_count = sum(1 for b in bats_list_ref if isinstance(b, BatMinion) and b.controller == self)

        # 2. 부족하면 즉시 보충 (최대 max_bats까지만)
        while current_bat_count < self.max_bats:
            spawn_angle = random.uniform(0, 2 * math.pi)
            spawn_dist = random.uniform(config.PLAYER_SIZE, config.PLAYER_SIZE + 20)
            spawn_x = (self.player.world_x + spawn_dist * math.cos(spawn_angle)) % config.MAP_WIDTH
            spawn_y = (self.player.world_y + spawn_dist * math.sin(spawn_angle)) % config.MAP_HEIGHT
            
            new_bat = BatMinion(self, spawn_x, spawn_y)
            bats_list_ref.append(new_bat)
            
            current_bat_count += 1
            # print(f"DEBUG: 박쥐 충원 ({current_bat_count}/{self.max_bats})")

    def draw(self, surface, camera_offset_x, camera_offset_y):
        pass 

    def get_level_up_options(self):
        """레벨업 시 제공할 옵션들 (박쥐 수 제한 로직 포함)"""
        options = []
        
        # 1. 데미지 강화 옵션
        options.append({
            "text": f"박쥐 데미지 ({self.damage} -> {math.ceil(self.damage * config.BAT_DAMAGE_MULTIPLIER_PER_LEVEL)})", 
            "type": "damage", 
            "value": math.ceil(self.damage * config.BAT_DAMAGE_MULTIPLIER_PER_LEVEL)
        })

        # 2. 흡혈량 강화 옵션
        options.append({
            "text": f"박쥐 흡혈량 ({(self.lifesteal_percentage*100):.0f}% -> {((self.lifesteal_percentage+0.02)*100):.0f}%)", 
            "type": "lifesteal", 
            "value": min(1.0, self.lifesteal_percentage + 0.02)
        })

        # 3. 🟢 [핵심] 최대 박쥐 수 제한 (5마리 미만일 때만 옵션 등장)
        if self.max_bats < 5: # config.BAT_MAX_COUNT_LIMIT 대신 직접 5로 제한하거나 config 연결
            options.append({
                "text": f"최대 박쥐 수 ({self.max_bats} -> {self.max_bats + 1})", 
                "type": "max_bats", 
                "value": self.max_bats + 1
            })

        # 사용 가능한 옵션 중 무작위로 최대 2개 선택하여 반환
        return random.sample(options, min(len(options), 2))

    def apply_upgrade(self, upgrade_info):
        """선택한 업그레이드 적용"""
        if upgrade_info["type"] == "damage": 
            self.damage = upgrade_info["value"]
        elif upgrade_info["type"] == "max_bats": 
            self.max_bats = upgrade_info["value"]
        elif upgrade_info["type"] == "lifesteal": 
            self.lifesteal_percentage = upgrade_info["value"]
        self.level += 1
    
    def on_remove(self):
        pass