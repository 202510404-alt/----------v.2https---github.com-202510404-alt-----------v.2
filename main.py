import pygame
import random
import math
import os
import asyncio  # 웹 실행 필수

# 커스텀 모듈 import
import config
import utils
from camera import Camera
from player import Player
import ui 

# 엔티티 및 적 클래스 import
from entities.exp_orb import ExpOrb
from entities.slime_bullet import SlimeBullet
from entities.dagger import Dagger
from entities.bat_minion import BatMinion
from entities.storm_projectile import StormProjectile
from enemies.slime import Slime
from enemies.mint_slime import MintSlime
from enemies.shooter_slime import ShooterSlime
from enemies.boss_slime import BossSlime 
from enemies.boss_minion_slime import BossMinionSlime
from weapons.bat_controller import BatController 

# --- 전역 변수 설정 ---
GAME_STATE_MENU = "MENU"
GAME_STATE_PLAYING = "PLAYING"
GAME_STATE_RANKING = "RANKING"

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
current_slime_max_hp = config.SLIME_INITIAL_BASE_HP
slime_hp_increase_timer = 0
game_state = GAME_STATE_MENU
is_game_over_for_menu = False
input_box = None        
is_name_entered = False 

# 랭킹 관련 전역 변수
online_rankings = None
current_rank_category_index = 0
RANK_CATEGORIES = ["DifficultyScore", "Level", "Kills", "Bosses", "SurvivalTime"]

# reset_game_state 함수 (게임 초기화)
def reset_game_state():
    global player, camera_obj, slimes, daggers, exp_orbs, bats, slime_bullets, boss_slimes, storm_projectiles
    global slime_spawn_timer, current_slime_max_hp, slime_hp_increase_timer
    global boss_active, is_game_over_for_menu, input_box, is_name_entered, online_rankings
    
    # 1. 닉네임 가져오기
    player_name_to_use = input_box.text if input_box and input_box.text else "익명 개발자" 
    
    # 2. Player 객체 생성 시 닉네임 전달
    player = Player(config.MAP_WIDTH/2, config.MAP_HEIGHT/2, player_name_to_use)
    
    # 3. 나머지 초기화 로직
    camera_obj = Camera(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    slimes.clear(); daggers.clear(); exp_orbs.clear(); bats.clear(); slime_bullets.clear(); boss_slimes.clear(); storm_projectiles.clear()
    slime_spawn_timer = 0; current_slime_max_hp = config.SLIME_INITIAL_BASE_HP; slime_hp_increase_timer = 0
    player.is_selecting_upgrade = False; player.is_selecting_boss_reward = False
    boss_active = False; is_game_over_for_menu = False
    
    # 4. InputBox 초기화
    if input_box:
        input_box.text = ""
        is_name_entered = False
    
    # 5. 랭킹 데이터 초기화
    online_rankings = None

# 랭킹 데이터 로드 함수
async def load_rankings_data():
    """랭킹 데이터를 비동기적으로 로드합니다."""
    global online_rankings
    online_rankings = None # 로딩 중 상태로 설정
    online_rankings = utils.load_rankings_online()
    print(f"랭킹 데이터 로드 완료. 항목 수: {len(online_rankings)}")


async def main():
    global game_state, is_game_over_for_menu, slime_spawn_timer
    global current_slime_max_hp, slime_hp_increase_timer, boss_active
    global player, camera_obj, slimes, daggers, exp_orbs, bats, slime_bullets, boss_slimes, storm_projectiles
    global input_box, is_name_entered
    global online_rankings, current_rank_category_index, RANK_CATEGORIES

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("뱀파이어 서바이벌 v.2")
    clock = pygame.time.Clock()

    # InputBox 생성
    input_box = ui.InputBox(
        (config.SCREEN_WIDTH // 2) - 150, 
        (config.SCREEN_HEIGHT // 2) + 100, 
        300, 
        50, 
        text=''
    )

    # 배경 이미지 로드
    background_image = None
    bg_width, bg_height = 0, 0
    try:
        bg_path = "image/background/background.png" 
        background_image = pygame.image.load(bg_path).convert()
        bg_width, bg_height = background_image.get_size()
    except:
        print("배경 이미지 로드 실패")

    running = True
    start_button_rect = pygame.Rect(0, 0, 200, 80)
    exit_button_rect = pygame.Rect(config.SCREEN_WIDTH - 50, 10, 40, 40)
    ranking_button_rect = pygame.Rect(0, 0, 150, 60) 

    ui.setup_ranking_buttons() # 랭킹 카테고리 버튼 위치 설정

    while running:
        dt = clock.tick(config.FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if game_state == GAME_STATE_MENU:
                
                # 닉네임 입력 처리
                if not is_name_entered and input_box:
                    enter_pressed = input_box.handle_event(event)
                    
                    if enter_pressed: 
                        if input_box.text:
                            is_name_entered = True
                            print(f"닉네임 설정 완료: {input_box.text}")
                        else:
                            input_box.text = "익명 개발자"
                            is_name_entered = True
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 게임 시작 버튼
                    if start_button_rect.collidepoint(mouse_pos) and is_name_entered:
                        reset_game_state()
                        game_state = GAME_STATE_PLAYING
                    
                    # 랭킹 버튼
                    elif ranking_button_rect.collidepoint(mouse_pos):
                        game_state = GAME_STATE_RANKING 
                        await load_rankings_data()
            
            elif game_state == GAME_STATE_RANKING:
                
                # 랭킹 카테고리 전환 처리 (마우스)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for button_info in ui.RANKING_BUTTONS:
                        if button_info['rect'].collidepoint(mouse_pos):
                            try:
                                # ui.RANKING_BUTTONS의 key를 사용하여 인덱스를 찾습니다.
                                new_index = RANK_CATEGORIES.index(button_info['key']) 
                                current_rank_category_index = new_index
                                print(f"랭킹 카테고리 변경: {button_info['key']}")
                            except ValueError:
                                pass
                
                # 랭킹 카테고리 전환 처리 (키보드)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GAME_STATE_MENU
                    
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        current_rank_category_index = (current_rank_category_index - 1) % len(RANK_CATEGORIES)
                        print(f"랭킹 카테고리 변경: {RANK_CATEGORIES[current_rank_category_index]}")
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        current_rank_category_index = (current_rank_category_index + 1) % len(RANK_CATEGORIES)
                        print(f"랭킹 카테고리 변경: {RANK_CATEGORIES[current_rank_category_index]}")

            elif game_state == GAME_STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GAME_STATE_MENU
                    elif player and player.is_selecting_upgrade:
                        removed_weapon_instance = None
                        if event.key == pygame.K_1: removed_weapon_instance = player.apply_chosen_upgrade(0)
                        elif event.key == pygame.K_2 and len(player.upgrade_options_to_display)>1: removed_weapon_instance = player.apply_chosen_upgrade(1)
                        elif event.key == pygame.K_3 and len(player.upgrade_options_to_display)>2: removed_weapon_instance = player.apply_chosen_upgrade(2)
                        if removed_weapon_instance:
                            bats[:] = [bat for bat in bats if not (isinstance(bat, BatMinion) and bat.controller == removed_weapon_instance)]
                    elif player and player.is_selecting_boss_reward:
                        if event.key == pygame.K_1: removed_weapon_instance = player.apply_chosen_upgrade(0)
                        elif event.key == pygame.K_2 and len(player.boss_reward_options_to_display)>1: removed_weapon_instance = player.apply_chosen_upgrade(1)
                        elif event.key == pygame.K_3 and len(player.boss_reward_options_to_display)>2: removed_weapon_instance = player.apply_chosen_upgrade(2)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    if player and player.special_skill:
                        mouse_world_x = camera_obj.world_x + event.pos[0]
                        mouse_world_y = camera_obj.world_y + event.pos[1]
                        player.special_skill.activate(mouse_world_x, mouse_world_y, {'storm_projectiles': storm_projectiles})

        if game_state == GAME_STATE_PLAYING and player:
            game_entities = {'slimes': slimes, 'daggers': daggers, 'exp_orbs': exp_orbs, 'bats': bats, 'slime_bullets': slime_bullets, 'boss_slimes': boss_slimes, 'storm_projectiles': storm_projectiles}
            
            if not (player.is_selecting_upgrade or player.is_selecting_boss_reward):
                player.update(slimes, game_entities)

                if player.hp <= 0:
                    
                    # 랭킹 저장 로직 
                    game_time_in_seconds = slime_hp_increase_timer / config.FPS 
                    current_difficulty_factor = current_slime_max_hp / config.SLIME_INITIAL_BASE_HP

                    score_data = {
                        "level": player.level,
                        "kills": player.total_enemies_killed,
                        "bosses": player.total_bosses_killed,
                        "difficulty_score": current_difficulty_factor,
                        "survival_time": game_time_in_seconds
                    }
                    
                    utils.save_new_ranking_online(player.name, score_data)

                    game_state = GAME_STATE_MENU; is_game_over_for_menu = True
                
                if game_state == GAME_STATE_PLAYING:
                    camera_obj.update(player)
                    if not boss_active:
                        slime_hp_increase_timer += 1
                        if slime_hp_increase_timer >= config.FPS * config.SLIME_HP_INCREASE_INTERVAL_SECONDS:
                            slime_hp_increase_timer = 0; current_slime_max_hp += 1
                        slime_spawn_timer += 1
                        if slime_spawn_timer >= config.SLIME_SPAWN_INTERVAL:
                            slime_spawn_timer = 0
                            edge=random.randint(0,3); cam_l,cam_t=camera_obj.world_x,camera_obj.world_y; cam_r,cam_b=cam_l+config.SCREEN_WIDTH,cam_t+config.SCREEN_HEIGHT
                            if edge==0: sx,sy=random.uniform(cam_l-100,cam_r+100),cam_t-100
                            elif edge==1: sx,sy=random.uniform(cam_l-100,cam_r+100),cam_b+100
                            elif edge==2: sx,sy=cam_l-100,random.uniform(cam_t-100,cam_b+100)
                            else: sx,sy=cam_r+100,random.uniform(cam_t-100,cam_b+100)
                            spawn_roll = random.randint(0, 9)
                            if spawn_roll < 2: slimes.append(ShooterSlime(sx % config.MAP_WIDTH, sy % config.MAP_HEIGHT, current_slime_max_hp))
                            elif spawn_roll < 4: slimes.append(MintSlime(sx % config.MAP_WIDTH, sy % config.MAP_HEIGHT, current_slime_max_hp))
                            else: slimes.append(Slime(sx % config.MAP_WIDTH, sy % config.MAP_HEIGHT, config.SLIME_RADIUS, config.SLIME_GREEN, config.SLIME_SPEED, current_slime_max_hp))

                    # 1. 적 업데이트 및 사망 처리
                    slimes_to_remove = [s for s in slimes if not s.update(player.world_x, player.world_y, game_entities)]
                    for s_inst in slimes_to_remove:
                        if s_inst.hp <= 0 and not isinstance(s_inst, BossMinionSlime):
                            player.total_enemies_killed += 1
                            exp_orbs.append(ExpOrb(s_inst.world_x, s_inst.world_y))
                    slimes[:] = [s for s in slimes if s not in slimes_to_remove]

                    # 2. 보스 처리
                    if not boss_active and player.total_enemies_killed > 0 and player.total_enemies_killed % config.BOSS_SLIME_SPAWN_KILL_THRESHOLD == 0 and not boss_slimes:
                        boss_active = True
                        boss_slimes.append(BossSlime((player.world_x + 300)%config.MAP_WIDTH, (player.world_y + 300)%config.MAP_HEIGHT, current_slime_max_hp))

                    bosses_to_remove = [b for b in boss_slimes if not b.update(player.world_x, player.world_y, game_entities)]
                    for boss in bosses_to_remove:
                        boss_active = False; player.total_bosses_killed += 1; player.trigger_boss_reward_selection()
                        for _ in range(20): exp_orbs.append(ExpOrb(boss.world_x + random.randint(-50,50), boss.world_y + random.randint(-50,50)))
                    boss_slimes[:] = [b for b in boss_slimes if b not in bosses_to_remove]

                    # 3. 무기 및 발사체 로직 (충돌 복구)
                    storm_projectiles[:] = [p for p in storm_projectiles if p.update(slimes + boss_slimes)]
                    daggers[:] = [d for d in daggers if d.update(game_entities)]
                    bats[:] = [b for b in bats if b.update(slimes, game_entities)]
                    
                    # 단검 적 충돌
                    d_hit = set()
                    for d in daggers:
                        for s in slimes + boss_slimes:
                            if s.hp > 0 and utils.distance_sq_wrapped(d.world_x, d.world_y, s.world_x, s.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < (d.size/2 + s.radius)**2:
                                s.take_damage(d.damage); d_hit.add(d); break
                    daggers[:] = [d for d in daggers if d not in d_hit]

                    # 4. 플레이어 데미지 로직 (충돌 복구)
                    # 적 발사체 충돌
                    sb_keep = []
                    for sb in slime_bullets:
                        if sb.update():
                            if utils.distance_sq_wrapped(player.world_x, player.world_y, sb.world_x, sb.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < (config.PLAYER_SIZE/2 + sb.size/2)**2:
                                player.take_damage(config.SLIME_BULLET_DAMAGE)
                            else: sb_keep.append(sb)
                    slime_bullets[:] = sb_keep

                    # 적 접촉 데미지
                    for s in slimes + boss_slimes:
                        if s.hp > 0 and utils.distance_sq_wrapped(player.world_x, player.world_y, s.world_x, s.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < ((config.PLAYER_SIZE/2)*config.PLAYER_DAMAGE_HITBOX_MULTIPLIER + s.radius)**2:
                            player.take_damage(s.damage_to_player)

                    # 5. 경험치 획득 로직 (복구)
                    o_rem = [o for o in exp_orbs if o.update(player.world_x, player.world_y) or utils.distance_sq_wrapped(o.world_x, o.world_y, player.world_x, player.world_y, config.MAP_WIDTH, config.MAP_HEIGHT) < (config.EXP_ORB_RADIUS + config.PLAYER_SIZE/2)**2]
                    for o in o_rem: player.gain_exp(o.value)
                    exp_orbs[:] = [o for o in exp_orbs if o not in o_rem]

        # --- 그리기 ---
        if game_state == GAME_STATE_PLAYING and player and camera_obj:
            if background_image:
                sx, sy = -(camera_obj.world_x % bg_width), -(camera_obj.world_y % bg_height)
                for y in range((config.SCREEN_HEIGHT // bg_height) + 2):
                    for x in range((config.SCREEN_WIDTH // bg_width) + 2):
                        screen.blit(background_image, (sx + x * bg_width, sy + y * bg_height))
            else: screen.fill(config.GREEN)

            for wpn in player.active_weapons: wpn.draw(screen, camera_obj.world_x, camera_obj.world_y)
            if not (player.invincible_timer > 0 and player.invincible_timer % 10 < 5): screen.blit(player.image, player.rect)
            for e in exp_orbs + daggers + bats + slime_bullets + storm_projectiles + slimes + boss_slimes:
                e.draw(screen, camera_obj.world_x, camera_obj.world_y)
            ui.draw_game_ui(screen, player, game_entities, current_slime_max_hp, player.total_bosses_killed, player.total_enemies_killed, config.BOSS_SLIME_SPAWN_KILL_THRESHOLD)

        elif game_state == GAME_STATE_MENU:
            screen.fill(config.GREEN)
            
            # 버튼 위치 설정
            start_button_rect.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
            ranking_button_rect.bottomleft = (10, config.SCREEN_HEIGHT - 10) # 🚩 왼쪽 아래 구석에 배치

            ui.draw_main_menu(screen, start_button_rect, exit_button_rect, is_game_over_for_menu, ranking_button_rect) # 🚩 인자 추가
            
            # 닉네임 입력 상자 그리기
            if not is_name_entered and input_box:
                input_box.draw(screen)

       # main.py (Line 325 근처 - 랭킹 화면 그리기 블록)
        elif game_state == GAME_STATE_RANKING: 
            current_category = RANK_CATEGORIES[current_rank_category_index]
            
            # 랭킹 데이터를 로드합니다 (데이터가 None이 아니면 로딩 완료)
            filtered_rankings = []
            if online_rankings and isinstance(online_rankings, list):
                filtered_rankings = [
                    r for r in online_rankings 
                    if isinstance(r, dict) and 'RankCategory' in r and r['RankCategory'] == current_category
                ]
            
            ui.draw_ranking_screen(screen, filtered_rankings, current_category)
        pygame.display.flip()
        await asyncio.sleep(0) # 웹 브라우저를 위해 제어권 양보

if __name__ == "__main__":
    asyncio.run(main())