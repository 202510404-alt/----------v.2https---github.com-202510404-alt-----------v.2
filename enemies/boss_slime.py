import random
import math
import pygame
import config
import utils
from enemies.slime import Slime
from entities.slime_bullet import SlimeBullet
from enemies.boss_minion_slime import BossMinionSlime
from enemies.shooter_slime import ShooterSlime # 슈터 소환용

class BossSlime(Slime):
    def __init__(self, world_x, world_y, current_total_max_hp, boss_index): 
        # 1. 보스 기본 스펙 (체력 20배)
        radius = config.SLIME_RADIUS * config.BOSS_SLIME_RADIUS_MULTIPLIER
        speed = config.SLIME_SPEED * config.BOSS_SLIME_SPEED_MULTIPLIER
        
        # 부모 클래스(Slime) 초기화 - HP 배율 20배 적용
        super().__init__(world_x, world_y, radius, config.BOSS_SLIME_COLOR, speed, current_total_max_hp, hp_multiplier=config.BOSS_SLIME_HP_MULTIPLIER) 

        # 2. 보스 상태 관리
        self.boss_index = boss_index    # 몇 번째 보스인지 (0부터 시작)
        self.is_phase2 = False          # 각성 여부
        self.stop_timer = 0             # 각성 시 멈춤 연출 타이머
        
        # 3. 🚩 [수정 핵심] 모든 타이머 변수 초기화 (에러 방지)
        self.shoot_cooldown_timer = config.BOSS_SLIME_SHOOT_COOLDOWN
        self.shooter_summon_timer = config.BOSS_SHOOTER_SUMMON_INTERVAL
        self.big_bullet_timer = config.BOSS_BIG_BULLET_INTERVAL
        self.minion_spawn_timer = config.BOSS_MINION_SPAWN_COOLDOWN
        
        self.damage_to_player = config.BOSS_SLIME_CONTACT_DAMAGE
        self.initial_spawn_hp_for_minions = current_total_max_hp 

    def update(self, target_player_world_x, target_player_world_y, game_entities_lists):
        if self.hp <= 0: return False

        # --- 🚩 3번째 보스부터 각성 패턴 (피 20% 이하일 때) ---
        if self.boss_index >= config.BOSS_AWAKEN_COUNT and not self.is_phase2:
            if self.hp < (self.max_hp * 0.2):
                print("!!! 보스 각성: 진정한 힘을 개방합니다 !!!")
                self.is_phase2 = True
                self.stop_timer = config.FPS * 1.5 # 1.5초간 기 모으기 (멈춤)
                self.hp = self.max_hp * 0.7        # 체력 70%까지 즉시 회복
                self.speed *= config.BOSS_PHASE2_SPEED_MULT # 속도 1.2배 증가

        # 각성 연출 중에는 이동/공격 정지
        if self.stop_timer > 0:
            self.stop_timer -= 1
            return True

        # --- 회복 로직 (초당 0.4% 회복) ---
        regen_rate = config.BOSS_SLIME_REGEN_RATE_PER_SEC
        if self.is_phase2:
            regen_rate *= config.BOSS_PHASE2_REGEN_MULT # 각성 시 회복량 1.5배
        
        regen_per_frame = (self.max_hp * regen_rate) / config.FPS
        self.hp = min(self.max_hp, self.hp + regen_per_frame)

        # --- 이동 로직 ---
        dist_sq = utils.distance_sq_wrapped(self.world_x, self.world_y, target_player_world_x, target_player_world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
        dist = math.sqrt(dist_sq)
        stop_distance = config.PLAYER_SIZE / 2 + self.radius

        if dist > self.speed + stop_distance:
            dx = utils.get_wrapped_delta(self.world_x, target_player_world_x, config.MAP_WIDTH)
            dy = utils.get_wrapped_delta(self.world_y, target_player_world_y, config.MAP_HEIGHT)
            self.world_x = (self.world_x + (dx / dist) * self.speed) % config.MAP_WIDTH
            self.world_y = (self.world_y + (dy / dist) * self.speed) % config.MAP_HEIGHT
        self.rect.center = (int(self.world_x), int(self.world_y))

        # --- 공격 패턴 1: 샷건 (일반 3발 / 각성 5발) ---
        self.shoot_cooldown_timer -= 1
        if self.shoot_cooldown_timer <= 0:
            self.shoot_cooldown_timer = config.BOSS_SLIME_SHOOT_COOLDOWN
            bullets = game_entities_lists.get('slime_bullets')
            if bullets is not None:
                dx = utils.get_wrapped_delta(self.world_x, target_player_world_x, config.MAP_WIDTH)
                dy = utils.get_wrapped_delta(self.world_y, target_player_world_y, config.MAP_HEIGHT)
                angle = math.atan2(dy, dx)
                
                count = 5 if self.is_phase2 else 3
                spread = math.radians(6) # 발사 간격 각도
                for i in range(count):
                    bullet_angle = angle + (i - count // 2) * spread
                    bullets.append(SlimeBullet(self.world_x, self.world_y, bullet_angle, color=config.BOSS_BULLET_COLOR))

        # --- 🚩 패턴 2: 7초마다 슈터 슬라임 5마리 소환 (각성 전용) ---
        if self.is_phase2:
            self.shooter_summon_timer -= 1
            if self.shooter_summon_timer <= 0:
                self.shooter_summon_timer = config.BOSS_SHOOTER_SUMMON_INTERVAL
                slimes = game_entities_lists.get('slimes')
                if slimes is not None:
                    print("보스가 슈터 부대를 소환합니다!")
                    for _ in range(5):
                        s_angle = random.uniform(0, 2 * math.pi)
                        s_dist = random.uniform(300, 500)
                        sx = (target_player_world_x + math.cos(s_angle) * s_dist) % config.MAP_WIDTH
                        sy = (target_player_world_y + math.sin(s_angle) * s_dist) % config.MAP_HEIGHT
                        slimes.append(ShooterSlime(sx, sy, self.initial_spawn_hp_for_minions))

        # --- 🚩 패턴 3: 4초마다 동서남북 거대 탄환 (각성 전용) ---
        if self.is_phase2:
            self.big_bullet_timer -= 1
            if self.big_bullet_timer <= 0:
                self.big_bullet_timer = config.BOSS_BIG_BULLET_INTERVAL
                bullets = game_entities_lists.get('slime_bullets')
                if bullets is not None:
                    # 동서남북 중 랜덤 한 곳에서 플레이어를 향해 발사
                    offset = random.choice([(-300, 0), (300, 0), (0, -300), (0, 300)])
                    bx = (target_player_world_x + offset[0]) % config.MAP_WIDTH
                    by = (target_player_world_y + offset[1]) % config.MAP_HEIGHT
                    
                    b_angle = math.atan2(utils.get_wrapped_delta(by, target_player_world_y, config.MAP_HEIGHT),
                                         utils.get_wrapped_delta(bx, target_player_world_x, config.MAP_WIDTH))
                    
                    big_b = SlimeBullet(bx, by, b_angle, color=config.RED)
                    big_b.size = config.SLIME_BULLET_SIZE * 3 # 3배 크기
                    big_b.lifespan = config.FPS * 5 # 넉넉한 수명
                    bullets.append(big_b)

        # --- 미니언 소환 (기존 패턴 유지) ---
        self.minion_spawn_timer -= 1
        if self.minion_spawn_timer <= 0:
            self.minion_spawn_timer = config.BOSS_MINION_SPAWN_COOLDOWN
            slimes = game_entities_lists.get('slimes')
            if slimes is not None:
                for _ in range(config.BOSS_MINION_SPAWN_COUNT):
                    m_angle = random.uniform(0, 2 * math.pi)
                    mx = (self.world_x + math.cos(m_angle) * 50) % config.MAP_WIDTH
                    my = (self.world_y + math.sin(m_angle) * 50) % config.MAP_HEIGHT
                    slimes.append(BossMinionSlime(mx, my, self.initial_spawn_hp_for_minions))

        return True