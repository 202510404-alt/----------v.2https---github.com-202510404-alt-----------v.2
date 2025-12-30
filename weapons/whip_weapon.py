import random
import math
import pygame
import config
import utils
from weapons.base_weapon import Weapon
from core.grid import enemy_grid

class WhipWeapon(Weapon):
    def __init__(self, player_ref):
        super().__init__(player_ref)
        self.name = "채찍"
        self.damage = 5
        self.knockback_strength = 50
        self.attack_reach = 140
        self.attack_angle_range = math.pi # 180도 (반원)
        self.cooldown = config.FPS * 0.7 # 공격 주기
        self.attack_timer = self.cooldown
        
        self.is_attacking = False
        self.attack_animation_duration = 10 # 휘두르는 시간 (프레임 단위, 낮을수록 빠름)
        self.animation_frame = 0
        
        self.start_angle = 0 # 이번 공격의 시작 각도
        self.hit_slimes_this_attack = set() # 이번 휘두르기에 이미 맞은 적들 목록
        self.target_search_radius_cells = 1 

    def update(self, slimes_list, game_entities_lists):
        self.attack_timer += 1
        
        # 1. 공격 시작 판단 (쿨타임 끝났을 때)
        if self.attack_timer >= self.cooldown and not self.is_attacking:
            player_wx, player_wy = self.player.world_x, self.player.world_y
            nearby = enemy_grid.get_nearby_enemies(player_wx, player_wy, self.target_search_radius_cells)
            
            # 조준 로직: 가장 가까운 적 방향으로 휘두르기 시작
            closest_s, min_d2 = None, float('inf')
            for s in nearby:
                if s.hp <= 0: continue
                d2 = utils.distance_sq_wrapped(player_wx, player_wy, s.world_x, s.world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
                if d2 < min_d2: min_d2 = d2; closest_s = s
            
            if closest_s:
                dx = utils.get_wrapped_delta(player_wx, closest_s.world_x, config.MAP_WIDTH)
                dy = utils.get_wrapped_delta(player_wy, closest_s.world_y, config.MAP_HEIGHT)
                target_mid_angle = math.atan2(dy, dx)
            else:
                # 적이 없으면 플레이어가 움직이는 방향, 그것도 없으면 마지막 각도 유지
                p_dx = utils.get_wrapped_delta(self.player.prev_world_x, self.player.world_x, config.MAP_WIDTH)
                p_dy = utils.get_wrapped_delta(self.player.prev_world_y, self.player.world_y, config.MAP_HEIGHT)
                if p_dx != 0 or p_dy != 0:
                    target_mid_angle = math.atan2(p_dy, p_dx)
                else:
                    target_mid_angle = self.start_angle + (self.attack_angle_range / 2)
            
            # 공격 상태로 전환
            self.is_attacking = True
            self.animation_frame = 0
            self.attack_timer = 0
            # 반원의 시작 각도 설정 (시계 반대 방향으로 휘두름)
            self.start_angle = target_mid_angle - (self.attack_angle_range / 2)
            self.hit_slimes_this_attack.clear()

        # 2. 휘두르는 중 (선과 적의 충돌 판정)
        if self.is_attacking:
            self.animation_frame += 1
            progress = self.animation_frame / self.attack_animation_duration # 0.0 ~ 1.0
            
            if progress > 1.0:
                self.is_attacking = False
                return

            # 🚩 [핵심] 현재 프레임에서 채찍 선의 각도
            current_line_angle = self.start_angle + (self.attack_angle_range * progress)
            
            player_wx, player_wy = self.player.world_x, self.player.world_y
            nearby = enemy_grid.get_nearby_enemies(player_wx, player_wy, self.target_search_radius_cells)
            
            # 현재 채찍 선의 방향 벡터 (길이 1인 단위 벡터)
            line_vec_x = math.cos(current_line_angle)
            line_vec_y = math.sin(current_line_angle)

            reach_sq = (self.attack_reach + 20)**2 # 충돌 반경 보정
            
            for s in nearby:
                if s.hp <= 0 or s in self.hit_slimes_this_attack: continue
                
                # 래핑 맵 거리 계산
                dx = utils.get_wrapped_delta(player_wx, s.world_x, config.MAP_WIDTH)
                dy = utils.get_wrapped_delta(player_wy, s.world_y, config.MAP_HEIGHT)
                dist_sq = dx*dx + dy*dy
                
                if dist_sq <= reach_sq:
                    # 🚩 [벡터 내적 판정] 적이 현재 채찍 선 위에 있는지 확인
                    # dist_sq가 0인 경우(플레이어와 겹침) 예외 처리
                    dist = math.sqrt(dist_sq) if dist_sq > 0 else 1
                    
                    # 적의 방향 벡터와 채찍 선의 방향 벡터의 내적
                    # 두 벡터가 거의 일치하면(1.0에 가까우면) 선 위에 있는 것임
                    dot = (dx/dist) * line_vec_x + (dy/dist) * line_vec_y
                    
                    # 0.98 이상이면 약 11도 이내의 오차 (선 두께 역할)
                    if dot > 0.98: 
                        s.take_damage(self.damage)
                        self.hit_slimes_this_attack.add(s)
                        # 넉백 처리
                        s.world_x = (s.world_x + line_vec_x * self.knockback_strength) % config.MAP_WIDTH
                        s.world_y = (s.world_y + line_vec_y * self.knockback_strength) % config.MAP_HEIGHT

            # 적 발사체도 선에 닿으면 지워버리기
            bullets = game_entities_lists.get('slime_bullets', [])
            for sb in bullets:
                if sb.is_hit_by_player_attack: continue
                bdx = utils.get_wrapped_delta(player_wx, sb.world_x, config.MAP_WIDTH)
                bdy = utils.get_wrapped_delta(player_wy, sb.world_y, config.MAP_HEIGHT)
                b_dist_sq = bdx*bdx + bdy*bdy
                if b_dist_sq <= reach_sq:
                    b_dist = math.sqrt(b_dist_sq) if b_dist_sq > 0 else 1
                    if ((bdx/b_dist) * line_vec_x + (bdy/b_dist) * line_vec_y) > 0.98:
                        sb.is_hit_by_player_attack = True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        if self.is_attacking:
            # 현재 진행도에 따른 각도 계산
            progress = self.animation_frame / self.attack_animation_duration
            current_line_angle = self.start_angle + (self.attack_angle_range * progress)
            
            # 화면 중심(플레이어 위치)
            px, py = config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2
            
            # 채찍 선의 끝점 계산
            ex = px + self.attack_reach * math.cos(current_line_angle)
            ey = py + self.attack_reach * math.sin(current_line_angle)
            
            # 1. 메인 채찍 선 (하얀색)
            pygame.draw.line(surface, config.WHITE, (px, py), (ex, ey), 4)
            
            # 2. 끝부분 강조 (강렬한 노란색 원)
            pygame.draw.circle(surface, config.YELLOW, (int(ex), int(ey)), 6)
            
            # 3. 아주 얇은 잔상 (선택 사항: 시각적 부드러움 추가)
            prev_angle = self.start_angle + (self.attack_angle_range * (max(0, self.animation_frame - 1) / self.attack_animation_duration))
            px2, py2 = px + self.attack_reach * math.cos(prev_angle), py + self.attack_reach * math.sin(prev_angle)
            pygame.draw.line(surface, (200, 200, 0), (px, py), (px2, py2), 2)

    def get_level_up_options(self):
        options = [
            {"text": f"데미지 ({self.damage} -> {self.damage+3})", "type": "damage", "value": self.damage+3},
            {"text": f"넉백 ({self.knockback_strength} -> {self.knockback_strength+15})", "type": "knockback", "value": self.knockback_strength+15},
            {"text": f"사거리 ({self.attack_reach} -> {self.attack_reach+20})", "type": "reach", "value": self.attack_reach+20},
            {"text": f"공속 (쿨다운 줄임)", "type": "cooldown", "value": max(config.FPS*0.1, self.cooldown - 5)}
        ]
        return random.sample(options, min(len(options), 2))

    def apply_upgrade(self, upgrade_info):
        if upgrade_info["type"] == "damage": self.damage = upgrade_info["value"]
        elif upgrade_info["type"] == "knockback": self.knockback_strength = upgrade_info["value"]
        elif upgrade_info["type"] == "reach": self.attack_reach = upgrade_info["value"]
        elif upgrade_info["type"] == "cooldown": self.cooldown = upgrade_info["value"]
        self.level += 1