# main.py
import pygame
import random
import math

import os # 파일 경로를 위해 os 모듈 import
# 커스텀 모듈 import
import config
import utils
from camera import Camera
from player import Player
import ui # ui.py 전체 모듈을 import

# 엔티티 클래스 import
from entities.exp_orb import ExpOrb
from entities.slime_bullet import SlimeBullet
from entities.dagger import Dagger
from entities.bat_minion import BatMinion
from entities.storm_projectile import StormProjectile

# 적 클래스 import
from enemies.slime import Slime
from enemies.mint_slime import MintSlime
from enemies.shooter_slime import ShooterSlime
from enemies.boss_slime import BossSlime
from enemies.boss_minion_slime import BossMinionSlime

# 무기 클래스 import (main.py에서 직접 참조할 때 필요)
from weapons.bat_controller import BatController 


# --- 게임 상태 정의 ---
GAME_STATE_MENU = "MENU"
GAME_STATE_PLAYING = "PLAYING"

# --- 게임 상태 변수 ---
player = None
camera_obj = None
slimes = []
daggers = []
exp_orbs = []
bats = []
slime_bullets = []
boss_slimes = []
storm_projectiles = []

slime_spawn_timer = 0
game_over = False
boss_active = False
slime_kill_count = 0
boss_defeat_count = 0 
current_slime_max_hp = config.SLIME_INITIAL_BASE_HP # 이 변수는 main.py에서 관리
slime_hp_increase_timer = 0


game_state = GAME_STATE_MENU
is_game_over_for_menu = False # 게임오버 후 메뉴로 돌아왔는지 여부

# --- 게임 상태 리셋 함수 ---
def reset_game_state():
    global player, camera_obj, slimes, daggers, exp_orbs, bats, slime_bullets, boss_slimes, storm_projectiles
    global slime_spawn_timer, current_slime_max_hp, slime_hp_increase_timer
    global boss_active, slime_kill_count, boss_defeat_count, is_game_over_for_menu
    
    player = Player(config.MAP_WIDTH/2, config.MAP_HEIGHT/2)
    camera_obj = Camera(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

    slimes.clear()
    daggers.clear()
    exp_orbs.clear()
    bats.clear()
    slime_bullets.clear()
    boss_slimes.clear()
    storm_projectiles.clear()

    slime_spawn_timer = 0
    current_slime_max_hp = config.SLIME_INITIAL_BASE_HP
    slime_hp_increase_timer = 0
    
    player.is_selecting_upgrade = False
    player.is_selecting_boss_reward = False

    boss_active = False
    slime_kill_count = 0
    boss_defeat_count = 0
    is_game_over_for_menu = False

# --- Pygame 초기화 ---
pygame.init()
# 화면 크기 자동 조절 (전체 화면)
try:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    config.SCREEN_WIDTH, config.SCREEN_HEIGHT = screen.get_size()
    print(f"전체 화면 모드 시작: {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
except pygame.error as e:
    print(f"전체 화면 모드 실패: {e}. 기본 설정({config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT})으로 실행합니다.")
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("뱀파이어 서바이벌 v.2")
clock = pygame.time.Clock()

# --- 배경 이미지 로드 ---
background_image = None
bg_width, bg_height = 0, 0
try:
    bg_path = os.path.join('image', 'background', 'background.png')
    # background.png 파일을 로드하고, 화면에 더 빨리 그릴 수 있도록 convert() 합니다.
    background_image = pygame.image.load(bg_path).convert()
    bg_width, bg_height = background_image.get_size()
    print(f"정보: '{bg_path}'를 배경 이미지로 로드했습니다.")
except pygame.error as e:
    print(f"경고: 배경 이미지 '{bg_path}'를 로드할 수 없습니다: {e}. 기본 배경색으로 대체됩니다.")

# --- 게임 루프 ---
running = True

# 메뉴 버튼 Rect 정의
start_button_rect = pygame.Rect(0, 0, 200, 80)
exit_button_rect = pygame.Rect(config.SCREEN_WIDTH - 50, 10, 40, 40)

while running:
    dt = clock.tick(config.FPS) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        if game_state == GAME_STATE_MENU:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button_rect.collidepoint(mouse_pos):
                    reset_game_state()
                    game_state = GAME_STATE_PLAYING
                elif exit_button_rect.collidepoint(mouse_pos):
                    running = False

        elif game_state == GAME_STATE_PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = GAME_STATE_MENU
                    is_game_over_for_menu = False # 일시정지 개념이므로 게임오버는 아님
                elif player and player.is_selecting_upgrade:
                    removed_weapon_instance = None
                    if event.key == pygame.K_1: removed_weapon_instance = player.apply_chosen_upgrade(0)
                    elif event.key == pygame.K_2 and len(player.upgrade_options_to_display)>1: removed_weapon_instance = player.apply_chosen_upgrade(1)
                    elif event.key == pygame.K_3 and len(player.upgrade_options_to_display)>2: removed_weapon_instance = player.apply_chosen_upgrade(2)
                    
                    if removed_weapon_instance is not None:
                        if isinstance(removed_weapon_instance, BatController):
                            bats[:] = [bat for bat in bats if not (isinstance(bat, BatMinion) and bat.controller == removed_weapon_instance)]

                elif player and player.is_selecting_boss_reward:
                    if event.key == pygame.K_1: player.apply_chosen_boss_reward(0)
                    elif event.key == pygame.K_2 and len(player.boss_reward_options_to_display)>1: player.apply_chosen_boss_reward(1)
                    elif event.key == pygame.K_3 and len(player.boss_reward_options_to_display)>2: player.apply_chosen_boss_reward(2)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # 3은 우클릭
                if player and player.special_skill:
                    mouse_screen_x, mouse_screen_y = event.pos
                    mouse_world_x = camera_obj.world_x + mouse_screen_x
                    mouse_world_y = camera_obj.world_y + mouse_screen_y
                    game_entities_for_skill = {'storm_projectiles': storm_projectiles}
                    player.special_skill.activate(mouse_world_x, mouse_world_y, game_entities_for_skill)

    # --- 업데이트 ---
    if game_state == GAME_STATE_PLAYING and player:
        game_entities = {
            'slimes': slimes, 'daggers': daggers, 'exp_orbs': exp_orbs, 'bats': bats,
            'slime_bullets': slime_bullets, 'boss_slimes': boss_slimes, 'storm_projectiles': storm_projectiles
        }

        is_player_paused = player.is_selecting_upgrade or player.is_selecting_boss_reward
        if not is_player_paused:
            player.update(slimes, game_entities)
            if player.hp <= 0:
                game_state = GAME_STATE_MENU
                is_game_over_for_menu = True

            if game_state == GAME_STATE_PLAYING: # player.update 후 상태가 바뀔 수 있으므로 재확인
                camera_obj.update(player)

                if not boss_active:
                    slime_hp_increase_timer += 1
                    if slime_hp_increase_timer >= config.FPS * config.SLIME_HP_INCREASE_INTERVAL_SECONDS:
                        slime_hp_increase_timer = 0; current_slime_max_hp += 1

                    slime_spawn_timer += 1
                    if slime_spawn_timer >= config.SLIME_SPAWN_INTERVAL:
                        slime_spawn_timer = 0
                        edge=random.randint(0,3); cam_l,cam_t=camera_obj.world_x,camera_obj.world_y; cam_r,cam_b=cam_l+config.SCREEN_WIDTH,cam_t+config.SCREEN_HEIGHT
                        if edge==0: sx,sy=random.uniform(cam_l-config.SPAWN_EDGE_OFFSET,cam_r+config.SPAWN_EDGE_OFFSET),cam_t-config.SPAWN_EDGE_OFFSET
                        elif edge==1: sx,sy=random.uniform(cam_l-config.SPAWN_EDGE_OFFSET,cam_r+config.SPAWN_EDGE_OFFSET),cam_b+config.SPAWN_EDGE_OFFSET
                        elif edge==2: sx,sy=cam_l-config.SPAWN_EDGE_OFFSET,random.uniform(cam_t-config.SPAWN_EDGE_OFFSET,cam_b+config.SPAWN_EDGE_OFFSET)
                        else: sx,sy=cam_r+config.SPAWN_EDGE_OFFSET,random.uniform(cam_t-config.SPAWN_EDGE_OFFSET,cam_b+config.SPAWN_EDGE_OFFSET)

                        spawn_roll = random.randint(0, 9)
                        if spawn_roll < 2: slimes.append(ShooterSlime(sx % config.MAP_WIDTH, sy % config.MAP_HEIGHT, current_slime_max_hp))
                        elif spawn_roll < 4: slimes.append(MintSlime(sx % config.MAP_WIDTH, sy % config.MAP_HEIGHT, current_slime_max_hp))
                        else: slimes.append(Slime(sx % config.MAP_WIDTH, sy % config.MAP_HEIGHT, config.SLIME_RADIUS, config.SLIME_GREEN, config.SLIME_SPEED, current_slime_max_hp))

                slimes_to_remove = [s for s in slimes if not s.update(player.world_x, player.world_y, game_entities)]
                for s_inst in slimes_to_remove:
                    if s_inst.hp <= 0 and not isinstance(s_inst, BossMinionSlime):
                        slime_kill_count += 1
                        if not any(utils.distance_sq_wrapped(o.world_x,o.world_y,s_inst.world_x,s_inst.world_y,config.MAP_WIDTH,config.MAP_HEIGHT)<config.EXP_ORB_EXIST_CHECK_RADIUS**2 for o in exp_orbs):
                            exp_orbs.append(ExpOrb(s_inst.world_x,s_inst.world_y))
                slimes[:] = [s for s in slimes if s not in slimes_to_remove]

                if not boss_active and slime_kill_count > 0 and slime_kill_count % config.BOSS_SLIME_SPAWN_KILL_THRESHOLD == 0 and not boss_slimes:
                    print("보스 슬라임 출현!"); boss_active = True
                    edge=random.randint(0,3); cam_l,cam_t=camera_obj.world_x,camera_obj.world_y; cam_r,cam_b=cam_l+config.SCREEN_WIDTH,cam_t+config.SCREEN_HEIGHT
                    if edge==0: sx,sy=random.uniform(cam_l-config.SPAWN_EDGE_OFFSET,cam_r+config.SPAWN_EDGE_OFFSET),cam_t-config.SPAWN_EDGE_OFFSET
                    elif edge==1: sx,sy=random.uniform(cam_l-config.SPAWN_EDGE_OFFSET,cam_r+config.SPAWN_EDGE_OFFSET),cam_b+config.SPAWN_EDGE_OFFSET
                    elif edge==2: sx,sy=cam_l-config.SPAWN_EDGE_OFFSET,random.uniform(cam_t-config.SPAWN_EDGE_OFFSET,cam_b+config.SPAWN_EDGE_OFFSET)
                    else: sx,sy=cam_r+config.SPAWN_EDGE_OFFSET,random.uniform(cam_t-config.SPAWN_EDGE_OFFSET,cam_b+config.SPAWN_EDGE_OFFSET)
                    boss_slimes.append(BossSlime(sx % config.MAP_WIDTH, sy % config.MAP_HEIGHT, current_slime_max_hp))

                bosses_to_remove = [b for b in boss_slimes if not b.update(player.world_x, player.world_y, game_entities)]
                for boss in bosses_to_remove:
                    boss_active = False; print("보스 처치! 일반 슬라임이 다시 나타납니다."); boss_defeat_count += 1; player.trigger_boss_reward_selection()
                    for _ in range(30): exp_orbs.append(ExpOrb(boss.world_x + random.randint(-boss.radius, boss.radius), boss.world_y + random.randint(-boss.radius, boss.radius)))
                boss_slimes[:] = [b for b in boss_slimes if b not in bosses_to_remove]

                storm_projectiles[:] = [p for p in storm_projectiles if p.update(slimes + boss_slimes)]
                daggers[:] = [d for d in daggers if d.update(game_entities)]
                bats[:] = [b for b in bats if b.update(slimes, game_entities)]

                slime_bullets_to_keep = []
                for sb in slime_bullets:
                    if sb.update():
                        if utils.distance_sq_wrapped(player.world_x, player.world_y, sb.world_x, sb.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < (config.PLAYER_SIZE/2 + sb.size/2)**2:
                            player.take_damage(config.SLIME_BULLET_DAMAGE)
                            if player.hp <= 0: game_state = GAME_STATE_MENU; is_game_over_for_menu = True; break
                        else: slime_bullets_to_keep.append(sb)
                slime_bullets[:] = slime_bullets_to_keep
                if game_state != GAME_STATE_PLAYING: continue

                daggers_hit_this_frame = set()
                for d in daggers:
                    for s in slimes + boss_slimes:
                        if s.hp > 0 and utils.distance_sq_wrapped(d.world_x,d.world_y,s.world_x,s.world_y,config.MAP_WIDTH,config.MAP_HEIGHT) < (d.size/2+s.radius)**2:
                            s.take_damage(d.damage); daggers_hit_this_frame.add(d); break
                daggers[:]=[d for d in daggers if d not in daggers_hit_this_frame]

                orbs_to_remove = [o for o in exp_orbs if o.update(player.world_x,player.world_y) or utils.distance_sq_wrapped(o.world_x,o.world_y,player.world_x,player.world_y,config.MAP_WIDTH,config.MAP_HEIGHT) < (config.EXP_ORB_RADIUS+config.PLAYER_SIZE/2)**2]
                for o in orbs_to_remove: player.gain_exp(o.value)
                exp_orbs[:]=[o for o in exp_orbs if o not in orbs_to_remove]
                for s in slimes + boss_slimes:
                    if s.hp > 0 and utils.distance_sq_wrapped(player.world_x, player.world_y, s.world_x, s.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < ((config.PLAYER_SIZE/2)*config.PLAYER_DAMAGE_HITBOX_MULTIPLIER + s.radius)**2:
                        player.take_damage(s.damage_to_player)
                        if player.hp <= 0: game_state = GAME_STATE_MENU; is_game_over_for_menu = True; break

    # --- 그리기 ---
    if game_state == GAME_STATE_PLAYING and player and camera_obj:
        # 배경 그리기
        if background_image:
            # 카메라의 월드 좌표 (화면의 왼쪽 상단)
            camera_x = camera_obj.world_x
            camera_y = camera_obj.world_y

            # 타일링(Tiling)을 위한 시작 오프셋 계산
            start_x = - (camera_x % bg_width)
            start_y = - (camera_y % bg_height)

            # 화면을 채우기 위해 필요한 타일 개수 계산
            num_tiles_x = (config.SCREEN_WIDTH // bg_width) + 2
            num_tiles_y = (config.SCREEN_HEIGHT // bg_height) + 2

            # 배경 이미지 타일링
            for y in range(num_tiles_y):
                for x in range(num_tiles_x):
                    screen.blit(background_image, (start_x + x * bg_width, start_y + y * bg_height))
        else:
            screen.fill(config.GREEN) # 배경 이미지가 없을 경우 기본 녹색 배경

        # --- 그리기 순서 변경 ---
        # 1. 플레이어와 무기를 먼저 그립니다.
        for wpn_obj in player.active_weapons:
            wpn_obj.draw(screen, camera_obj.world_x, camera_obj.world_y)

        if not (player.invincible_timer > 0 and player.invincible_timer % 10 < 5):
            screen.blit(player.image, player.rect)

        # 2. 나머지 모든 엔티티(슬라임, 발사체 등)를 그립니다.
        all_other_entities = exp_orbs + daggers + bats + slime_bullets + storm_projectiles + slimes + boss_slimes
        for entity in all_other_entities:
            entity.draw(screen, camera_obj.world_x, camera_obj.world_y)

        # 게임 UI 그리기 (레벨업 창 포함)
        ui.draw_game_ui(screen, player, game_entities, current_slime_max_hp, boss_defeat_count, slime_kill_count, config.BOSS_SLIME_SPAWN_KILL_THRESHOLD)

    elif game_state == GAME_STATE_MENU:
        # 메뉴 화면에서도 배경을 어둡게 표시하기 위해 기본 배경색을 채웁니다.
        screen.fill(config.GREEN)
        # 메뉴 UI 그리기
        start_button_rect.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        exit_button_rect.topright = (config.SCREEN_WIDTH - 10, 10)
        ui.draw_main_menu(screen, start_button_rect, exit_button_rect, is_game_over_for_menu)

    pygame.display.flip()

pygame.quit()