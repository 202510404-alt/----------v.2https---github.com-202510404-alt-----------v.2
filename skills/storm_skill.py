# skills/storm_skill.py
import math
import config
import utils
from entities.storm_projectile import StormProjectile # 폭풍 투사체를 생성하기 위해

class StormSkill:
    def __init__(self, player_ref):
        self.player = player_ref
        self.name = "폭풍"
        self.level = 1
        self.base_damage = config.STORM_SKILL_BASE_DAMAGE
        self.cooldown = config.STORM_SKILL_COOLDOWN_SECONDS * config.FPS
        self.cooldown_timer = self.cooldown # 처음엔 바로 사용 가능하도록
        self.num_projectiles = 1

    def update(self):
        if self.cooldown_timer < self.cooldown:
            self.cooldown_timer += 1

    def get_current_projectile_damage(self):
        if self.num_projectiles == 0: return 0
        return math.ceil(self.base_damage / self.num_projectiles)

    def activate(self, target_world_x, target_world_y, game_entities_lists):
        if self.cooldown_timer >= self.cooldown:
            self.cooldown_timer = 0

            storm_projectiles_list_ref = game_entities_lists.get('storm_projectiles')
            if storm_projectiles_list_ref is None: return

            player_wx = self.player.world_x
            player_wy = self.player.world_y

            dx_to_target = utils.get_wrapped_delta(player_wx, target_world_x, config.MAP_WIDTH)
            dy_to_target = utils.get_wrapped_delta(player_wy, target_world_y, config.MAP_HEIGHT)
            center_angle = math.atan2(dy_to_target, dx_to_target)

            if self.num_projectiles == 1:
                angles = [center_angle]
            else:
                total_spread = math.pi # 180도
                angle_step = total_spread / (self.num_projectiles -1)
                start_angle = center_angle - total_spread / 2
                angles = [start_angle + i * angle_step for i in range(self.num_projectiles)]

            damage_per_projectile = self.get_current_projectile_damage()
            for angle in angles:
                storm_projectiles_list_ref.append(StormProjectile(player_wx, player_wy, angle, damage_per_projectile))

    def generate_upgrade_options(self):
        options = []
        options.append({
            "text": f"폭풍 개수 증가 ({self.num_projectiles} -> {self.num_projectiles + 1}, 데미지 분산)",
            "type": "num_projectiles", "value": self.num_projectiles + 1
        })
        new_damage = self.base_damage + config.STORM_SKILL_DAMAGE_INCREASE
        options.append({
            "text": f"기본 데미지 증가 ({self.base_damage} -> {new_damage})",
            "type": "damage", "value": new_damage
        })
        new_cooldown = max(5 * config.FPS, self.cooldown - config.STORM_SKILL_COOLDOWN_DECREASE_SECONDS * config.FPS)
        options.append({
            "text": f"쿨타임 감소 ({self.cooldown/config.FPS:.1f}초 -> {new_cooldown/config.FPS:.1f}초)",
            "type": "cooldown", "value": new_cooldown
        })
        return options

    def apply_upgrade(self, upgrade_info):
        if upgrade_info["type"] == "num_projectiles":
            self.num_projectiles = upgrade_info["value"]
        elif upgrade_info["type"] == "damage":
            self.base_damage = upgrade_info["value"]
        elif upgrade_info["type"] == "cooldown":
            self.cooldown = upgrade_info["value"]
        self.level += 1
        print(f"폭풍 스킬 업그레이드! 레벨: {self.level}")