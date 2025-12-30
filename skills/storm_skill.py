import math
import config
import utils
from entities.storm_projectile import StormProjectile

class StormSkill:
    def __init__(self, player_ref):
        self.player = player_ref
        self.name = "태풍"
        self.level = 1
        
        # config의 최신 수치로 초기 상태 설정
        self.current_damage = config.STORM_SKILL_BASE_DAMAGE
        self.current_radius = config.STORM_PROJECTILE_RADIUS
        self.cooldown = config.STORM_SKILL_COOLDOWN_SECONDS * config.FPS
        self.cooldown_timer = self.cooldown
        self.num_projectiles = config.STORM_SKILL_INITIAL_NUM

    def update(self):
        if self.cooldown_timer < self.cooldown:
            self.cooldown_timer += 1

    def activate(self, game_entities_lists):
        if self.cooldown_timer >= self.cooldown:
            self.cooldown_timer = 0
            storm_list = game_entities_lists.get('storm_projectiles')
            if storm_list is None: return

            center_angle = self.player.facing_angle
            
            # 발사 각도 계산 (부채꼴 형태)
            if self.num_projectiles == 1:
                angles = [center_angle]
            else:
                total_spread = math.radians(120)
                angle_step = total_spread / (self.num_projectiles - 1)
                start_angle = center_angle - total_spread / 2
                angles = [start_angle + i * angle_step for i in range(self.num_projectiles)]

            for angle in angles:
                # 강화된 수치를 적용하여 투사체 생성
                storm_list.append(StormProjectile(
                    self.player.world_x, self.player.world_y, 
                    angle, self.current_damage, self.current_radius
                ))

    def generate_upgrade_options(self):
        pool = []
        
        # 1. 폭풍 개수 증가 (최대치 제한)
        if self.num_projectiles < config.STORM_SKILL_MAX_NUM:
            pool.append({
                "text": f"폭풍 개수 증가 ({self.num_projectiles} -> {self.num_projectiles + 1})", 
                "type": "num_projectiles", 
                "value": self.num_projectiles + 1
            })

        # 2. 데미지 증가 (제한 없음)
        pool.append({
            "text": f"데미지 증가 ({self.current_damage} -> {self.current_damage + config.STORM_SKILL_DAMAGE_UPGRADE})", 
            "type": "damage", 
            "value": self.current_damage + config.STORM_SKILL_DAMAGE_UPGRADE
        })

        # 3. 범위 증가 (제한 없음)
        pool.append({
            "text": f"범위 증가 ({int(self.current_radius)} -> {int(self.current_radius * config.STORM_SKILL_RADIUS_UPGRADE_MULT)})", 
            "type": "range", 
            "value": self.current_radius * config.STORM_SKILL_RADIUS_UPGRADE_MULT
        })

        # 4. 쿨타임 감소 (최소치 제한: 10초)
        min_cooldown_frames = config.STORM_SKILL_MIN_COOLDOWN_SECONDS * config.FPS
        if self.cooldown > min_cooldown_frames:
            pool.append({
                "text": "쿨타임 감소", 
                "type": "cooldown", 
                "value": max(min_cooldown_frames, 
                             self.cooldown - config.STORM_SKILL_COOLDOWN_DECREASE_SECONDS * config.FPS)
            })
        
        return pool

    def apply_upgrade(self, upgrade_info):
        # 업그레이드 선택 결과 반영
        if upgrade_info["type"] == "num_projectiles": 
            self.num_projectiles = upgrade_info["value"]
        elif upgrade_info["type"] == "damage":
            self.current_damage = upgrade_info["value"]
        elif upgrade_info["type"] == "range":
            self.current_radius = upgrade_info["value"]
        elif upgrade_info["type"] == "cooldown":
            self.cooldown = upgrade_info["value"]
        self.level += 1