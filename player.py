import pygame
import math
import random
import config
import utils

# 무기 및 스킬 임포트
from weapons.dagger_launcher import DaggerLauncher
from weapons.flail_weapon import FlailWeapon
from weapons.whip_weapon import WhipWeapon
from weapons.bat_controller import BatController
from skills.storm_skill import StormSkill

class Player(pygame.sprite.Sprite):
    def __init__(self, initial_world_x, initial_world_y, name="Player"):
        super().__init__()
        self.image = pygame.Surface([config.PLAYER_SIZE, config.PLAYER_SIZE])
        self.image.fill(config.BLUE)
        self.rect = self.image.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2))
        
        self.world_x = float(initial_world_x)
        self.world_y = float(initial_world_y)
        self.prev_world_x = self.world_x
        self.prev_world_y = self.world_y
        
        self.name = name
        self.max_hp = config.PLAYER_INITIAL_HP
        self.hp = config.PLAYER_INITIAL_HP
        self.invincible_timer = 0
        self.level = config.PLAYER_INITIAL_LEVEL
        self.exp = 0
        self.exp_to_level_up = config.PLAYER_INITIAL_EXP_TO_LEVEL_UP
        
        # 플레이어가 마지막으로 바라본 각도 (기본은 오른쪽: 0도)
        self.facing_angle = 0.0
        
        # 경험치 배수 초기화 (1.0배로 시작)
        self.exp_multiplier = 1.0
        
        self.active_weapons = []
        self.shake_intensity = 0.0
        self.available_new_weapons = [DaggerLauncher, FlailWeapon, WhipWeapon, BatController]
        self.acquire_new_weapon(DaggerLauncher)
        
        self.is_selecting_upgrade = False
        self.upgrade_options_to_display = []
        self.special_skill = None
        self.is_selecting_boss_reward = False
        self.boss_reward_options_to_display = []
        self.total_enemies_killed = 0
        self.total_bosses_killed = 0

    def acquire_new_weapon(self, weapon_class_to_acquire):
        MAX_WEAPON_SLOTS = 10
        if any(isinstance(w, weapon_class_to_acquire) for w in self.active_weapons):
            return None
        if len(self.active_weapons) >= MAX_WEAPON_SLOTS:
            return None
        new_weapon = weapon_class_to_acquire(self)
        self.active_weapons.append(new_weapon)
        return None

    def update(self, slimes_list, game_entities_lists):
        if self.hp <= 0 or self.is_selecting_upgrade or self.is_selecting_boss_reward:
             return

        self.prev_world_x = self.world_x
        self.prev_world_y = self.world_y

        if self.invincible_timer > 0: self.invincible_timer -= 1
        if self.shake_intensity > 0:
            self.shake_intensity -= 1.5
            if self.shake_intensity < 0: self.shake_intensity = 0

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -config.PLAYER_SPEED
        if keys[pygame.K_RIGHT]: dx = config.PLAYER_SPEED
        if keys[pygame.K_UP]: dy = -config.PLAYER_SPEED
        if keys[pygame.K_DOWN]: dy = config.PLAYER_SPEED

        # 움직임이 있을 때만 보는 방향 업데이트
        if dx != 0 or dy != 0:
            self.facing_angle = math.atan2(dy, dx)

        self.world_x = (self.world_x + dx) % config.MAP_WIDTH
        self.world_y = (self.world_y + dy) % config.MAP_HEIGHT

        for weapon in self.active_weapons: 
            weapon.update(slimes_list, game_entities_lists)
        if self.special_skill:
            self.special_skill.update()

    def take_damage(self, amount):
        if self.invincible_timer > 0: return
        self.shake_intensity = min(amount / 3.0, 20.0)
        self.hp = max(0, self.hp - amount)
        self.invincible_timer = config.PLAYER_INVINCIBILITY_DURATION

    def heal(self, amount):
        if amount <= 0: return
        self.hp = min(self.max_hp, self.hp + math.ceil(amount))

    def gain_exp(self, amount):
        if self.hp <= 0 or self.is_selecting_upgrade or self.is_selecting_boss_reward: return
        
        # 경험치 획득 시 배수 적용
        self.exp += amount * self.exp_multiplier
        self.check_level_up()

    def check_level_up(self):
        while self.exp >= self.exp_to_level_up: # 연속 레벨업 가능하도록 while 사용
            self.exp -= self.exp_to_level_up
            self.level += 1
            self.exp_to_level_up = math.ceil(self.exp_to_level_up * 1.5)
            self.max_hp += 10
            self.hp = self.max_hp
            self.is_selecting_upgrade = True
            self.generate_upgrade_options()

    def generate_upgrade_options(self):
        self.upgrade_options_to_display = []
        pool = []
        
        # 새로운 무기 획득 옵션
        available_for_new = [wt for wt in self.available_new_weapons if not any(isinstance(aw, wt) for aw in self.active_weapons)]
        if available_for_new:
            chosen = random.choice(available_for_new)
            pool.append({"text": f"새 무기: {chosen(self).name}", "type": "new_weapon", "weapon_class": chosen})
        
        # 기존 무기 강화 옵션
        for wpn in self.active_weapons:
            opts = wpn.get_level_up_options()
            for o in opts:
                pool.append({"text": f"{wpn.name} 업그레이드: {o['text']}", "type": "existing_weapon_upgrade", "weapon_instance": wpn, "upgrade_details": o})
        
        # 옵션이 부족할 경우 스탯 강화
        if not pool: 
            pool.append({"text": "최대 HP +20 증가", "type": "stat_hp", "value": 20})
            
        self.upgrade_options_to_display = random.sample(pool, min(len(pool), 3))

    def apply_chosen_upgrade(self, option_index):
        if not (self.is_selecting_upgrade and 0 <= option_index < len(self.upgrade_options_to_display)): return None
        chosen = self.upgrade_options_to_display[option_index]
        removed = None
        if chosen["type"] == "new_weapon": removed = self.acquire_new_weapon(chosen["weapon_class"])
        elif chosen["type"] == "existing_weapon_upgrade": chosen["weapon_instance"].apply_upgrade(chosen["upgrade_details"])
        elif chosen["type"] == "stat_hp":
            self.max_hp += chosen["value"]; self.hp = self.max_hp
        self.is_selecting_upgrade = False
        self.upgrade_options_to_display = []
        return removed

    def trigger_boss_reward_selection(self):
        # 보스 처치 시 경험치 배수 1.5배 영구 증가
        self.exp_multiplier *= 1.5
        utils.browser_debug(f"보스 처치! 현재 경험치 배수: {self.exp_multiplier:.2f}배")
        
        if not self.special_skill:
             self.special_skill = StormSkill(self)
             print("태풍 획득! Z키로 발사!")
        else:
            self.is_selecting_boss_reward = True
            self.boss_reward_options_to_display = self.special_skill.generate_upgrade_options()

    def apply_chosen_boss_reward(self, option_index):
        # 🚩 4번째 선택지(index 3)를 포함하여 선택 가능하도록 수정
        if self.is_selecting_boss_reward and 0 <= option_index < len(self.boss_reward_options_to_display):
            opt = self.boss_reward_options_to_display[option_index]
            self.special_skill.apply_upgrade(opt)
            self.is_selecting_boss_reward = False

    def get_world_rect(self):
        return pygame.Rect(self.world_x-config.PLAYER_SIZE//2, self.world_y-config.PLAYER_SIZE//2, config.PLAYER_SIZE,config.PLAYER_SIZE)