# main.py
import pygame
import random
import math
import os
import asyncio  # 1. 웹 실행을 위해 반드시 추가

# 커스텀 모듈 import
import config
import utils
from camera import Camera
from player import Player
import ui 

# 엔티티 및 적 클래스 import (기존과 동일)
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

# --- 전역 변수 설정 (기존과 동일) ---
GAME_STATE_MENU = "MENU"
GAME_STATE_PLAYING = "PLAYING"

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
current_slime_max_hp = config.SLIME_INITIAL_BASE_HP
slime_hp_increase_timer = 0
game_state = GAME_STATE_MENU
is_game_over_for_menu = False

def reset_game_state():
    global player, camera_obj, slimes, daggers, exp_orbs, bats, slime_bullets, boss_slimes, storm_projectiles
    global slime_spawn_timer, current_slime_max_hp, slime_hp_increase_timer
    global boss_active, slime_kill_count, boss_defeat_count, is_game_over_for_menu
    
    player = Player(config.MAP_WIDTH/2, config.MAP_HEIGHT/2)
    camera_obj = Camera(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    slimes.clear(); daggers.clear(); exp_orbs.clear(); bats.clear(); slime_bullets.clear(); boss_slimes.clear(); storm_projectiles.clear()
    slime_spawn_timer = 0; current_slime_max_hp = config.SLIME_INITIAL_BASE_HP; slime_hp_increase_timer = 0
    player.is_selecting_upgrade = False; player.is_selecting_boss_reward = False
    boss_active = False; slime_kill_count = 0; boss_defeat_count = 0; is_game_over_for_menu = False

# 2. 메인 함수를 async로 선언
async def main():
    global game_state, is_game_over_for_menu, running, slime_spawn_timer
    global current_slime_max_hp, slime_hp_increase_timer, slime_kill_count, boss_active, boss_defeat_count

    pygame.init()
    
    # 웹 브라우저에서는 전체화면 설정이 다를 수 있으므로 예외처리
    try:
        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    except:
        screen = pygame.display.set_mode((800, 600))
        
    pygame.display.set_caption("뱀파이어 서바이벌 v.2")
    clock = pygame.time.Clock()

    # 배경 이미지 로드
    background_image = None
    bg_width, bg_height = 0, 0
    try:
        bg_path = os.path.join('image', 'background', 'background.png')
        background_image = pygame.image.load(bg_path).convert()
        bg_width, bg_height = background_image.get_size()
    except:
        print("배경 로드 실패")

    running = True
    start_button_rect = pygame.Rect(0, 0, 200, 80)
    exit_button_rect = pygame.Rect(config.SCREEN_WIDTH - 50, 10, 40, 40)

    # 3. 게임 루프 시작
    while running:
        dt = clock.tick(config.FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            
            # (기존 이벤트 처리 로직 동일하게 유지...)
            if game_state == GAME_STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button_rect.collidepoint(mouse_pos):
                        reset_game_state()
                        game_state = GAME_STATE_PLAYING
            elif game_state == GAME_STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GAME_STATE_MENU
                    # 업로드 선택 로직 등... (기존 코드 생략 없이 그대로 사용하세요)
                # ... (기존 마우스 이벤트 등 계속)

        # --- 업데이트 및 그리기 로직 (기존 코드 그대로 사용) ---
        # (생략: 위에서 보내주신 업데이트 및 그리기 코드가 이 자리에 들어옵니다.)
        if game_state == GAME_STATE_PLAYING:
            # ... (보내주신 플레이 로직 그대로 넣기)
            pass
        elif game_state == GAME_STATE_MENU:
            # ... (보내주신 메뉴 로직 그대로 넣기)
            pass

        pygame.display.flip()
        
        # 4. 가장 중요한 부분: 웹 브라우저에 제어권을 넘겨줌
        await asyncio.sleep(0)

# 5. 프로그램 시작 지점
if __name__ == "__main__":
    asyncio.run(main())