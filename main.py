import pygame
import asyncio
import random
import config
import utils
import ui.ui as ui
import core.state as state
import core.physics as physics
import core.logic as logic
from core.grid import enemy_grid 
from enemies.boss_minion_slime import BossMinionSlime
from entities.exp_orb import ExpOrb
from entities.bat_minion import BatMinion

# ----------------------------------------------------
# 1. 비동기 통신 래퍼 함수 (게임 루프 정지 방지)
# ----------------------------------------------------
async def load_rankings_data():
    """백그라운드에서 랭킹 데이터를 로드합니다."""
    utils.browser_debug("서버 데이터 요청 중...")
    state.online_rankings = None  # 로딩 중 표시
    try:
        data = await utils.load_rankings_online()
        state.online_rankings = data if data is not None else []
        utils.browser_debug(f"데이터 수신 성공: {len(state.online_rankings)}개")
    except Exception as e:
        utils.browser_debug(f"데이터 로드 실패: {e}", True)
        state.online_rankings = []

async def save_ranking_task(name, score):
    """백그라운드에서 점수를 저장합니다."""
    try:
        utils.browser_debug(f"점수 저장 시작: {name}")
        success = await utils.save_new_ranking_online(name, score)
        if success:
            utils.browser_debug("서버 저장 완료!")
    except Exception as e:
        utils.browser_debug(f"저장 중 오류 발생: {e}", True)

# ----------------------------------------------------
# 2. 메인 실행 함수
# ----------------------------------------------------
async def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("뱀파이어 서바이벌 v.3 (Final Fix)")
    clock = pygame.time.Clock()

    # UI 및 입력창 초기화
    state.input_box = ui.InputBox((config.SCREEN_WIDTH // 2) - 150, (config.SCREEN_HEIGHT // 2) + 100, 300, 50)
    ui.setup_ranking_buttons()

    # 배경 이미지 로드
    background_image = None
    bg_w, bg_h = 0, 0
    try:
        background_image = pygame.image.load("image/background/background.png").convert()
        bg_w, bg_h = background_image.get_size()
    except:
        print("배경 이미지 로드 실패 - 기본 배경 사용")

    running = True
    
    # 버튼 객체 정의
    start_btn = pygame.Rect(0, 0, 200, 80)
    rank_btn = pygame.Rect(0, 0, 150, 60)
    exit_btn = pygame.Rect(config.SCREEN_WIDTH - 50, 10, 40, 40)

    while running:
        dt = clock.tick(config.FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        # --- 이벤트 처리 섹션 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            
            # [메뉴 상태]
            if state.game_state == state.GAME_STATE_MENU:
                if not state.is_name_entered:
                    if state.input_box.handle_event(event): state.is_name_entered = True
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_btn.collidepoint(mouse_pos) and state.is_name_entered:
                        state.reset_game_state()
                        state.game_state = state.GAME_STATE_PLAYING
                    elif rank_btn.collidepoint(mouse_pos):
                        utils.browser_debug("랭킹 버튼 클릭됨")
                        state.game_state = state.GAME_STATE_RANKING
                        # 🚩 await 대신 task를 써야 게임이 안 멈춤
                        asyncio.create_task(load_rankings_data()) 
            
            # [랭킹 상태]
            elif state.game_state == state.GAME_STATE_RANKING:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in ui.RANKING_BUTTONS:
                        if btn['rect'].collidepoint(mouse_pos):
                            state.current_rank_category_index = state.RANK_CATEGORIES.index(btn['key'])
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state.game_state = state.GAME_STATE_MENU

            # [게임 플레이 상태]
            elif state.game_state == state.GAME_STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        if state.player and state.player.special_skill:
                            state.player.special_skill.activate(state.get_entities_dict())
                    
                    if event.key == pygame.K_m: state.game_state = state.GAME_STATE_INVENTORY
                    elif event.key == pygame.K_ESCAPE: state.game_state = state.GAME_STATE_MENU
                    
                    elif state.player.is_selecting_boss_reward or state.player.is_selecting_upgrade:
                        choice = -1
                        if event.key == pygame.K_1: choice = 0
                        elif event.key == pygame.K_2: choice = 1
                        elif event.key == pygame.K_3: choice = 2
                        
                        if choice != -1:
                            if state.player.is_selecting_boss_reward:
                                state.player.apply_chosen_boss_reward(choice)
                            else:
                                removed = state.player.apply_chosen_upgrade(choice)
                                if removed:
                                    state.bats[:] = [b for b in state.bats if not (isinstance(b, BatMinion) and b.controller == removed)]

            # [인벤토리 상태]
            elif state.game_state == state.GAME_STATE_INVENTORY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                        state.game_state = state.GAME_STATE_PLAYING

        # --- 게임 업데이트 로직 ---
        if state.game_state == state.GAME_STATE_PLAYING and state.player:
            if not (state.player.is_selecting_upgrade or state.player.is_selecting_boss_reward):
                
                # 그리드 시스템 갱신
                enemy_grid.clear()
                for s in state.slimes + state.boss_slimes:
                    if s.hp > 0: enemy_grid.register_enemy(s)

                state.player.update(state.slimes, state.get_entities_dict())
                
                # 사망 처리
                if state.player.hp <= 0:
                    score = {
                        "levels": state.player.level, "kills": state.player.total_enemies_killed,
                        "bosses": state.player.total_bosses_killed, 
                        "difficulty_score": state.current_slime_max_hp / config.SLIME_INITIAL_BASE_HP,
                        "survival_time": state.slime_hp_increase_timer / config.FPS
                    }
                    utils.browser_debug("💀 사망! 데이터 저장 태스크 생성")
                    # 🚩 중요: 저장을 태스크로 넘기고 바로 메뉴로 이동
                    asyncio.create_task(save_ranking_task(state.player.name, score))
                    
                    state.game_state = state.GAME_STATE_MENU
                    state.is_game_over_for_menu = True
                
                if state.game_state == state.GAME_STATE_PLAYING:
                    state.camera_obj.update(state.player)
                    logic.update_game_logic(state)
                    logic.handle_boss_logic(state)
                    
                    slimes_to_rem = [s for s in state.slimes if not s.update(state.player.world_x, state.player.world_y, state.get_entities_dict())]
                    for s in slimes_to_rem:
                        if s.hp <= 0 and not isinstance(s, BossMinionSlime):
                            state.player.total_enemies_killed += 1
                            state.exp_orbs.append(ExpOrb(s.world_x, s.world_y))
                    state.slimes[:] = [s for s in state.slimes if s not in slimes_to_rem]
                    
                    physics.handle_collisions(state)
                    state.daggers[:] = [d for d in state.daggers if d.update(state.get_entities_dict())]

        # --- 그리기 섹션 ---
        if state.game_state in [state.GAME_STATE_PLAYING, state.GAME_STATE_INVENTORY] and state.player:
            off_x, off_y = 0, 0
            if state.game_state == state.GAME_STATE_PLAYING and state.player.shake_intensity > 0:
                off_x = random.uniform(-state.player.shake_intensity, state.player.shake_intensity)
                off_y = random.uniform(-state.player.shake_intensity, state.player.shake_intensity)
            
            shake_cam_x = state.camera_obj.world_x + off_x
            shake_cam_y = state.camera_obj.world_y + off_y

            # 1. 배경
            if background_image:
                sx, sy = -(shake_cam_x % bg_w), -(shake_cam_y % bg_h)
                for y in range((config.SCREEN_HEIGHT // bg_h) + 2):
                    for x in range((config.SCREEN_WIDTH // bg_w) + 2):
                        screen.blit(background_image, (sx + x * bg_w, sy + y * bg_h))
            else: screen.fill(config.GREEN)

            # 2. 무기 및 플레이어
            for wpn in state.player.active_weapons: wpn.draw(screen, shake_cam_x, shake_cam_y)
            if not (state.player.invincible_timer > 0 and state.player.invincible_timer % 10 < 5):
                p_rect = state.player.rect.copy()
                p_rect.x -= off_x; p_rect.y -= off_y
                screen.blit(state.player.image, p_rect)
            
            # 3. 모든 엔티티
            for e in state.exp_orbs + state.daggers + state.bats + state.slime_bullets + state.storm_projectiles + state.slimes + state.boss_slimes:
                e.draw(screen, shake_cam_x, shake_cam_y)
            
            # 4. HUD
            ui.draw_game_ui(screen, state.player, state.get_entities_dict(), state.current_slime_max_hp, state.player.total_bosses_killed, state.player.total_enemies_killed, config.BOSS_SLIME_SPAWN_KILL_THRESHOLD)
            if state.game_state == state.GAME_STATE_INVENTORY:
                ui.draw_weapon_inventory(screen, state.player)

        elif state.game_state == state.GAME_STATE_MENU:
            screen.fill(config.DARK_GREEN)
            start_btn.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
            rank_btn.bottomleft = (10, config.SCREEN_HEIGHT - 10)
            ui.draw_main_menu(screen, start_btn, exit_btn, state.is_game_over_for_menu, rank_btn)
            if not state.is_name_entered: state.input_box.draw(screen)
            
        elif state.game_state == state.GAME_STATE_RANKING:
            cat = state.RANK_CATEGORIES[state.current_rank_category_index]
            # 1. 카테고리에 맞는 데이터 필터링
            filtered = [r for r in (state.online_rankings or []) if r.get('RankCategory') == cat]
            
            # 🚩 [이 줄을 추가하세요!] 점수(RankValue)가 높은 순서대로 줄 세우기
            filtered.sort(key=lambda x: x.get('RankValue', 0), reverse=True)
            
            # 2. 정렬된 데이터를 화면에 그리기
            ui.draw_ranking_screen(screen, filtered, cat)
        pygame.display.flip()
        # 🚩 웹에서 비동기 작업을 처리할 수 있게 하는 핵심 한 줄
        await asyncio.sleep(0) 

if __name__ == "__main__":
    asyncio.run(main())