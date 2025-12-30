import math
import config
import utils
from entities.storm_projectile import StormProjectile

class StormSkill:
    def __init__(self, player_ref):
        self.player = player_ref
        self.name = "태풍"
        self.level = 1
        self.base_damage = config.STORM_SKILL_BASE_DAMAGE
        self.cooldown = config.STORM_SKILL_COOLDOWN_SECONDS * config.FPS
        self.cooldown_timer = self.cooldown
        self.num_projectiles = 1

    def update(self):
        if self.cooldown_timer < self.cooldown:
            self.cooldown_timer += 1

    def activate(self, game_entities_lists):
        if self.cooldown_timer >= self.cooldown:
            self.cooldown_timer = 0
            storm_list = game_entities_lists.get('storm_projectiles')
            if storm_list is None: return

            # 플레이어가 현재 보고 있는 방향을 기준으로 발사
            center_angle = self.player.facing_angle
            
            if self.num_projectiles == 1:
                angles = [center_angle]
            else:
                total_spread = math.radians(120) # 120도 부채꼴 범위로 발사
                angle_step = total_spread / (self.num_projectiles - 1)
                start_angle = center_angle - total_spread / 2
                angles = [start_angle + i * angle_step for i in range(self.num_projectiles)]

            for angle in angles:
                # 🚩 투사체 생성 (데미지는 투사체 내부에서 20으로 처리하지만 인자로도 전달)
                storm_list.append(StormProjectile(self.player.world_x, self.player.world_y, angle, 20))

    def generate_upgrade_options(self):
        options = [
            {"text": f"폭풍 개수 증가 ({self.num_projectiles} -> {self.num_projectiles+1})", "type": "num_projectiles", "value": self.num_projectiles+1},
            {"text": f"범위 증가 (반지름 {int(config.STORM_PROJECTILE_RADIUS)} -> {int(config.STORM_PROJECTILE_RADIUS*1.2)})", "type": "range", "value": 1.2},
            {"text": "쿨타임 감소", "type": "cooldown", "value": max(config.FPS*5, self.cooldown - config.STORM_SKILL_COOLDOWN_DECREASE_SECONDS*config.FPS)}
        ]
        return options

    def apply_upgrade(self, upgrade_info):
        if upgrade_info["type"] == "num_projectiles": self.num_projectiles = upgrade_info["value"]
        elif upgrade_info["type"] == "range": pass # config 상수를 직접 건드리거나 projectile에서 배율 적용 필요
        elif upgrade_info["type"] == "cooldown": self.cooldown = upgrade_info["value"]
        self.level += 1