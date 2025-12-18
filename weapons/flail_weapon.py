# weapons/flail_weapon.py
import random
import math
import pygame
import config
import utils
from weapons.base_weapon import Weapon

class FlailWeapon(Weapon):
    def __init__(self, player_ref):
        super().__init__(player_ref)
        self.name = "철퇴"
        self.chain_length = config.FLAIL_INITIAL_CHAIN_LENGTH
        self.head_radius = config.FLAIL_HEAD_RADIUS
        self.angle = 0
        self.rotation_speed = config.FLAIL_ROTATION_SPEED
        self.current_rotation_speed = self.rotation_speed
        self.damage = config.FLAIL_DAMAGE_BASE
        self.head_world_x = self.player.world_x + self.chain_length*math.cos(self.angle)
        self.head_world_y = self.player.world_y + self.chain_length*math.sin(self.angle)
        self.hit_cooldowns = {}
        self.hit_cooldown_duration = config.FPS//3

    def update(self, slimes_list, game_entities_lists):
        player_moved_dx=utils.get_wrapped_delta(self.player.prev_world_x,self.player.world_x,config.MAP_WIDTH)
        player_moved_dy=utils.get_wrapped_delta(self.player.prev_world_y,self.player.world_y,config.MAP_HEIGHT)
        if player_moved_dx!=0 or player_moved_dy!=0: self.current_rotation_speed=self.rotation_speed+abs(player_moved_dx+player_moved_dy)*0.005
        else: self.current_rotation_speed=self.rotation_speed
        self.angle=(self.angle+self.current_rotation_speed)%(2*math.pi)
        self.head_world_x=(self.player.world_x+self.chain_length*math.cos(self.angle))%config.MAP_WIDTH
        self.head_world_y=(self.player.world_y+self.chain_length*math.sin(self.angle))%config.MAP_HEIGHT

        slimes_to_remove_from_cooldown=[]
        for slime_in_cooldown,cd_timer in list(self.hit_cooldowns.items()):
            self.hit_cooldowns[slime_in_cooldown]-=1
            if self.hit_cooldowns[slime_in_cooldown]<=0: slimes_to_remove_from_cooldown.append(slime_in_cooldown)
        for s_rem in slimes_to_remove_from_cooldown:
            if s_rem in self.hit_cooldowns: del self.hit_cooldowns[s_rem]

        all_slimes = slimes_list + game_entities_lists.get('boss_slimes', [])
        for slime in all_slimes:
            if slime.hp<=0:
                if slime in self.hit_cooldowns: del self.hit_cooldowns[slime]
                continue
            if slime in self.hit_cooldowns: continue
            dist_sq=utils.distance_sq_wrapped(self.head_world_x,self.head_world_y,slime.world_x,slime.world_y,config.MAP_WIDTH,config.MAP_HEIGHT)
            if dist_sq<(self.head_radius+slime.radius)**2:
                if slime.take_damage(self.damage):
                    if slime in self.hit_cooldowns: del self.hit_cooldowns[slime]
                self.hit_cooldowns[slime]=config.FPS//3
                impact_angle=math.atan2(utils.get_wrapped_delta(self.head_world_y,slime.world_y,config.MAP_HEIGHT),utils.get_wrapped_delta(self.head_world_x,slime.world_x,config.MAP_WIDTH))
                self.angle=impact_angle+math.pi; self.current_rotation_speed*=-0.7; break

        slime_bullets_list_ref = game_entities_lists.get('slime_bullets')
        if slime_bullets_list_ref:
            for sb in slime_bullets_list_ref:
                if sb.is_hit_by_player_attack: continue
                dist_sq_bullet = utils.distance_sq_wrapped(self.head_world_x, self.head_world_y, sb.world_x, sb.world_y, config.MAP_WIDTH, config.MAP_HEIGHT)
                if dist_sq_bullet < (self.head_radius + sb.size)**2:
                    sb.is_hit_by_player_attack = True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        player_screen_x,player_screen_y=config.SCREEN_WIDTH//2,config.SCREEN_HEIGHT//2
        min_dist_sq,closest_head_sx,closest_head_sy=float('inf'),0,0
        for dx_off in [-config.MAP_WIDTH,0,config.MAP_WIDTH]:
            for dy_off in [-config.MAP_HEIGHT,0,config.MAP_HEIGHT]:
                h_wx_cand,h_wy_cand=self.head_world_x+dx_off,self.head_world_y+dy_off
                h_sx_cand,h_sy_cand=h_wx_cand-camera_offset_x,h_wy_cand-camera_offset_y
                cur_d_sq=(h_sx_cand-player_screen_x)**2+(h_sy_cand-player_screen_y)**2
                if cur_d_sq<min_dist_sq: min_dist_sq=cur_d_sq; closest_head_sx,closest_head_sy=h_sx_cand,h_sy_cand
        pygame.draw.line(surface,config.FLAIL_CHAIN_COLOR,(player_screen_x,player_screen_y),(int(closest_head_sx),int(closest_head_sy)),2)
        for dx_off in [-config.MAP_WIDTH,0,config.MAP_WIDTH]:
            for dy_off in [-config.MAP_HEIGHT,0,config.MAP_HEIGHT]:
                obj_wx_render,obj_wy_render=self.head_world_x+dx_off,self.head_world_y+dy_off
                sx_render,sy_render=obj_wx_render-camera_offset_x,obj_wy_render-camera_offset_y
                if -self.head_radius*2<sx_render<config.SCREEN_WIDTH+self.head_radius*2 and \
                   -self.head_radius*2<sy_render<config.SCREEN_HEIGHT+self.head_radius*2:
                    pygame.draw.circle(surface,config.FLAIL_HEAD_COLOR,(int(sx_render),int(sy_render)),self.head_radius)
    def get_level_up_options(self):
        options=[{"text":f"데미지 ({self.damage} -> {math.ceil(self.damage*config.FLAIL_DAMAGE_MULTIPLIER_PER_LEVEL)})","type":"damage","value":math.ceil(self.damage*config.FLAIL_DAMAGE_MULTIPLIER_PER_LEVEL)},
                 {"text":f"길이 ({self.chain_length} -> {self.chain_length+10})","type":"chain_length","value":self.chain_length+10},
                 {"text":f"속도 ({self.rotation_speed:.2f} -> {self.rotation_speed+0.01:.2f})","type":"rotation_speed","value":self.rotation_speed+0.01}]
        return random.sample(options,min(len(options),2))
    def apply_upgrade(self, upgrade_info):
        if upgrade_info["type"]=="damage":self.damage=upgrade_info["value"]
        elif upgrade_info["type"]=="chain_length":self.chain_length=upgrade_info["value"]
        elif upgrade_info["type"]=="rotation_speed":self.rotation_speed=upgrade_info["value"]
        self.level+=1