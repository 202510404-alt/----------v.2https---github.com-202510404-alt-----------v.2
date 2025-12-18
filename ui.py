# ui.py
import pygame
import math
import config
from weapons.dagger_launcher import DaggerLauncher
from weapons.flail_weapon import FlailWeapon
from weapons.whip_weapon import WhipWeapon
from weapons.bat_controller import BatController
from entities.bat_minion import BatMinion

# Pygame 폰트 모듈 초기화
pygame.font.init()

# 폰트 로딩
FONT_FILE_NAME = 'D2Coding.ttf' 

font = None
small_font = None
large_font = None
medium_font = None

# --- Custom font loading attempt (D2Coding.ttf) ---
try:
    font = pygame.font.Font(FONT_FILE_NAME, 30)
    small_font = pygame.font.Font(FONT_FILE_NAME, 24)
    large_font = pygame.font.Font(FONT_FILE_NAME, 74)
    medium_font = pygame.font.Font(FONT_FILE_NAME, 36)
    print(f"정보: 폰트 파일 '{FONT_FILE_NAME}'을(를) 성공적으로 로드했습니다.")
    print(f"DEBUG: 로드된 'font' 객체 타입: {type(font)}, 값: {font}")
except pygame.error as e: 
    print(f"경고: 폰트 파일 '{FONT_FILE_NAME}'을(를) 로드할 수 없습니다: {e}. 시스템 폰트 (SysFont)로 대체 시도합니다.")
    
    # --- Fallback to SysFont (시스템 내 한글 폰트 찾기) ---
    fallback_font_names = ["Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "Arial", "sans", "korean"] # 추가적인 시스템 폰트 이름 후보
    for fname in fallback_font_names:
        try:
            # SysFont는 파일 경로 대신 폰트 이름을 받음
            # bold=False, italic=False (기본값)
            temp_font = pygame.font.SysFont(fname, 30) # SysFont는 TrueType 폰트 이름으로 작동.
            if temp_font and temp_font.get_height() > 0: # 유효한 폰트 객체인지 확인
                font = temp_font
                small_font = pygame.font.SysFont(fname, 24)
                large_font = pygame.font.SysFont(fname, 74)
                medium_font = pygame.font.SysFont(fname, 36)
                print(f"정보: 시스템 폰트 '{fname}'을(를) 성공적으로 로드했습니다.")
                print(f"DEBUG: 로드된 'font' 객체 타입 (fallback SysFont): {type(font)}, 값: {font}")
                break # 성공했으니 루프 종료
        except pygame.error:
            # print(f"DEBUG: 시스템 폰트 '{fname}' 로드 실패: {pygame.error}") # 디버깅용
            continue # 다음 폰트 시도
    
    if font is None: # 모든 SysFont 시도 실패
        print("심각 경고: 모든 시스템 폰트 로드마저 실패했습니다. Pygame 기본 폰트 (Font(None))로 최종 시도합니다.")
        try:
            font = pygame.font.Font(None, 30)
            small_font = pygame.font.Font(None, 24)
            large_font = pygame.font.Font(None, 74)
            medium_font = pygame.font.Font(None, 36)
            print("정보: 최종적으로 Pygame 기본 폰트 (Font(None))를 로드했습니다.")
            print(f"DEBUG: 로드된 'font' 객체 타입 (final fallback Font(None)): {type(font)}, 값: {font}")
        except pygame.error as e_final_fallback:
            print(f"치명적 오류: 최종 기본 폰트 로드마저 실패했습니다: {e_final_fallback}. 텍스트 표시가 불가능하며, 게임이 불안정할 수 있습니다.")
            font = None # 모든 폰트 로드 실패
            small_font = None
            large_font = None
            medium_font = None
except Exception as e_general: # SysFont 자체에서 예상치 못한 다른 오류 발생 시
    print(f"치명적 오류: 폰트 로딩 중 예상치 못한 일반 오류 발생: {e_general}. 텍스트 표시가 불가능할 수 있습니다.")
    font = None
    small_font = None
    large_font = None
    medium_font = None


def draw_grass(surface, cam_wx, cam_wy):
    step = config.GRASS_TILE_SIZE * config.GRASS_SPACING_FACTOR
    start_tile_ix = math.floor(cam_wx / step)
    start_tile_iy = math.floor(cam_wy / step)
    end_tile_ix = math.ceil((cam_wx + config.SCREEN_WIDTH) / step)
    end_tile_iy = math.ceil((cam_wy + config.SCREEN_HEIGHT) / step)
    for i in range(start_tile_ix, end_tile_ix + 1):
        for j in range(start_tile_iy, end_tile_iy + 1):
            patch_world_x = i * step
            patch_world_y = j * step
            screen_x = patch_world_x - cam_wx
            screen_y = patch_world_y - cam_wy
            pygame.draw.rect(surface, config.DARK_GREEN, (screen_x, screen_y, config.GRASS_PATCH_SIZE, config.GRASS_PATCH_SIZE))

def draw_main_menu(surface, start_button_rect, exit_button_rect, is_game_over):
    """메인 메뉴 화면을 그립니다."""
    if font is None or not isinstance(font, pygame.font.Font):
        return

    # 반투명 오버레이
    overlay_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay_surface.fill((0, 0, 0, 180))
    surface.blit(overlay_surface, (0, 0))

    # 게임 오버 메시지 (해당하는 경우)
    if is_game_over:
        try:
            go_s = large_font.render("게임 오버", True, config.RED)
            surface.blit(go_s, go_s.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 100)))
        except pygame.error as e:
            print(f"ERROR: 게임 오버 타이틀 렌더링 실패: {e}.")
    else:
        # 게임 시작 화면 제목
        try:
            title_s = large_font.render("게임 시작하기", True, config.BLUE) # 파란색 제목
            surface.blit(title_s, title_s.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 100)))
        except pygame.error as e:
            print(f"ERROR: 게임 시작 타이틀 렌더링 실패: {e}.")

    # 게임 시작 버튼
    pygame.draw.rect(surface, config.UI_OPTION_BOX_BG_COLOR, start_button_rect, border_radius=15)
    pygame.draw.rect(surface, config.UI_OPTION_BOX_BORDER_COLOR, start_button_rect, 3, border_radius=15)
    try:
        start_text = medium_font.render("게임 시작", True, config.WHITE)
        surface.blit(start_text, start_text.get_rect(center=start_button_rect.center))
    except pygame.error as e:
        print(f"ERROR: 시작 버튼 텍스트 렌더링 실패: {e}.")

    # 게임 종료 버튼 (빨간 X)
    pygame.draw.rect(surface, config.RED, exit_button_rect, border_radius=5)
    try:
        exit_text = medium_font.render("X", True, config.WHITE)
        surface.blit(exit_text, exit_text.get_rect(center=exit_button_rect.center))
    except pygame.error as e:
        print(f"ERROR: 종료 버튼 텍스트 렌더링 실패: {e}.")


def draw_game_ui(surface, player_obj, game_entities, current_slime_max_hp_val, boss_defeat_count_val, slime_kill_count_val, boss_spawn_threshold_val):
    """게임 플레이 중의 UI를 그립니다."""
    if font is None or not isinstance(font, pygame.font.Font):
        return
    if small_font is None or not isinstance(small_font, pygame.font.Font) or \
       large_font is None or not isinstance(large_font, pygame.font.Font) or \
       medium_font is None or not isinstance(medium_font, pygame.font.Font):
        return


    # 🚩🚩 닉네임 표시 로직 추가 🚩🚩
    try:
        # 닉네임 텍스트 생성
        name_text = font.render(f"id: {player_obj.name}", True, config.WHITE)
        
        # 화면 오른쪽 위 (HP 바와 대칭되는 위치)
        name_text_x = config.SCREEN_WIDTH - name_text.get_width() - 10 
        name_text_y = 10 
        
        surface.blit(name_text, (name_text_x, name_text_y))
    except pygame.error as e:
        print(f"ERROR: 닉네임 텍스트 렌더링 실패: {e}.")
        pass
    # 🚩🚩 닉네임 표시 로직 추가 완료 🚩🚩

    # --- HP 게이지 바 ---
    hp_bar_x, hp_bar_y = 10, 10
    hp_bar_width, hp_bar_height = 150, 20
    hp_ratio = player_obj.hp / player_obj.max_hp if player_obj.max_hp > 0 else 0

    try:
        pygame.draw.rect(surface, config.DARK_RED, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), border_radius=3) # 배경 바
        current_hp_bar_width = int(hp_bar_width * hp_ratio)
        if current_hp_bar_width > 0:
            pygame.draw.rect(surface, config.HP_BAR_GREEN, (hp_bar_x, hp_bar_y, current_hp_bar_width, hp_bar_height), border_radius=3) # 현재 HP 바
        
        hp_text_surface = small_font.render(f"HP: {player_obj.hp}/{player_obj.max_hp}", True, config.WHITE)
        hp_text_rect = hp_text_surface.get_rect(center=(hp_bar_x + hp_bar_width/2, hp_bar_y + hp_bar_height/2))
        surface.blit(hp_text_surface, hp_text_rect)
    except pygame.error as e:
        print(f"ERROR: HP 게이지 렌더링 실패: {e}.")
        pass
    
    # --- 레벨 표시 ---
    try:
        level_text = font.render(f"레벨: {player_obj.level}", True, config.WHITE)
        surface.blit(level_text, (hp_bar_x, hp_bar_y + hp_bar_height + 5)) # HP 바 아래에
    except pygame.error as e:
        print(f"ERROR: 레벨 텍스트 렌더링 실패: {e}.")
        pass

    # --- 경험치 바 ---
    exp_bar_x, exp_bar_y = hp_bar_x, hp_bar_y + hp_bar_height + 5 + 30 # 레벨 텍스트 아래에
    exp_bar_width, exp_bar_height = hp_bar_width, 15
    exp_ratio = player_obj.exp / player_obj.exp_to_level_up if player_obj.exp_to_level_up > 0 else 0

    try:
        pygame.draw.rect(surface, config.DARK_RED, (exp_bar_x, exp_bar_y, exp_bar_width, exp_bar_height), border_radius=3) # 배경 바
        current_exp_width = int(exp_bar_width * exp_ratio)
        if current_exp_width > 0: pygame.draw.rect(surface, config.EXP_BAR_COLOR, (exp_bar_x, exp_bar_y, current_exp_width, exp_bar_height), border_radius=3) # 현재 EXP 바
        
        exp_text_surface = small_font.render(f"EXP: {player_obj.exp}/{player_obj.exp_to_level_up}", True, config.WHITE)
        exp_text_rect = exp_text_surface.get_rect(center=(exp_bar_x + exp_bar_width/2, exp_bar_y + exp_bar_height/2))
        surface.blit(exp_text_surface, exp_text_rect)
    except pygame.error as e:
        print(f"ERROR: EXP 게이지 렌더링 실패: {e}.")
        pass

    y_offset = exp_bar_y + exp_bar_height + 15 # 다음 UI 요소 시작 위치

    # --- 무기 정보 ---
    for wpn in player_obj.active_weapons:
        extra_info = ""
        if isinstance(wpn, BatController):
            my_bats_count = 0
            for bat_minion_obj in game_entities.get('bats', []):
                if isinstance(bat_minion_obj, BatMinion) and bat_minion_obj.controller == wpn:
                    my_bats_count += 1
            extra_info = f" (활성:{my_bats_count}/{wpn.max_bats} 흡혈:{(wpn.lifesteal_percentage*100):.0f}%)"
        elif isinstance(wpn, DaggerLauncher):
             extra_info = f" (샷:{wpn.num_daggers_per_shot})" # 샷당으로 변경
        elif isinstance(wpn, FlailWeapon):
            extra_info = f" (길이:{wpn.chain_length})"
        elif isinstance(wpn, WhipWeapon):
            extra_info = f" (범위:{wpn.attack_reach})"

        try:
            weapon_text = small_font.render(f"{wpn.name} L{wpn.level} (데미지:{wpn.damage}){extra_info}", True, config.WHITE)
            surface.blit(weapon_text, (10, y_offset)); y_offset += 20
        except pygame.error as e:
            print(f"ERROR: Weapon 텍스트 렌더링 실패: {e}.")
            y_offset += 20 
            pass

    # --- 특수 스킬 (폭풍) 정보 ---
    if player_obj.special_skill:
        sk = player_obj.special_skill
        cooldown_ratio = sk.cooldown_timer / sk.cooldown
        skill_color = (0, 255, 100) if cooldown_ratio >= 1.0 else (150, 150, 150)

        try:
            skill_text = small_font.render(
                f"{sk.name} L{sk.level} (데미지:{sk.get_current_projectile_damage()} x{sk.num_projectiles})", # 데미지로 변경
                True, skill_color
            )
            surface.blit(skill_text, (10, y_offset))
        except pygame.error as e:
            print(f"ERROR: Skill 텍스트 렌더링 실패: {e}.")
            pass
        y_offset += 20

        # 스킬 쿨다운 바
        cd_bar_width, cd_bar_height = 150, 10
        pygame.draw.rect(surface, (50,50,50), (10, y_offset, cd_bar_width, cd_bar_height))
        current_cd_width = int(cd_bar_width * cooldown_ratio)
        if current_cd_width > 0:
            pygame.draw.rect(surface, skill_color, (10, y_offset, current_cd_width, cd_bar_height))
        y_offset += 15

    # --- 난이도 표시 (원래 Slime BaseMaxHP) ---
    info_y_start = config.SCREEN_HEIGHT - 90 # 아래쪽으로 이동 및 공간 확보
    try:
        difficulty_level = current_slime_max_hp_val / config.SLIME_INITIAL_BASE_HP # 기본 HP 대비 몇 배인지
        difficulty_text = font.render(f"난이도: {difficulty_level:.1f}x", True, config.WHITE) # .1f는 소수점 첫째자리까지
        surface.blit(difficulty_text, (10, info_y_start))
    except pygame.error as e: print(f"ERROR: 난이도 렌더링 실패: {e}."); pass

    # --- 보스 처치 수 표시 (원래 Kills) ---
    try:
        boss_kill_text = font.render(f"보스 처치: {boss_defeat_count_val}", True, config.YELLOW)
        surface.blit(boss_kill_text, (10, info_y_start + 30))
    except pygame.error as e: print(f"ERROR: 보스 처치 수 렌더링 실패: {e}."); pass


    # --- 보스 소환 게이지 바 (화면 맨 위 중앙) ---
    boss_gauge_width, boss_gauge_height = 400, 25
    boss_gauge_x = (config.SCREEN_WIDTH - boss_gauge_width) // 2
    boss_gauge_y = 10 # 화면 맨 위
    
    # 다음 보스 소환까지 필요한 킬 수를 현재 킬 수와 임계값을 이용하여 계산
    progress_in_current_cycle = slime_kill_count_val % boss_spawn_threshold_val
    boss_gauge_ratio = progress_in_current_cycle / boss_spawn_threshold_val if boss_spawn_threshold_val > 0 else 0

    try:
        # 배경 바
        pygame.draw.rect(surface, (100, 50, 0), (boss_gauge_x, boss_gauge_y, boss_gauge_width, boss_gauge_height), border_radius=5) 
        # 현재 진행 바 (주황색 계열)
        if boss_gauge_ratio > 0:
            pygame.draw.rect(surface, (255, 140, 0), (boss_gauge_x, boss_gauge_y, int(boss_gauge_width * boss_gauge_ratio), boss_gauge_height), border_radius=5)
        
        # 텍스트
        boss_gauge_text = medium_font.render(f"다음 보스: {progress_in_current_cycle}/{boss_spawn_threshold_val}", True, config.WHITE)
        boss_gauge_text_rect = boss_gauge_text.get_rect(center=(boss_gauge_x + boss_gauge_width // 2, boss_gauge_y + boss_gauge_height // 2))
        surface.blit(boss_gauge_text, boss_gauge_text_rect)
    except pygame.error as e:
        print(f"ERROR: 보스 소환 게이지 렌더링 실패: {e}.")
        pass


    # --- 레벨업 및 보상 선택 UI (기존 로직 유지) ---
    if player_obj.is_selecting_upgrade:
        overlay_surface = pygame.Surface((config.SCREEN_WIDTH,config.SCREEN_HEIGHT),pygame.SRCALPHA); overlay_surface.fill((0,0,0,180)); surface.blit(overlay_surface,(0,0))
        try:
            title_s = large_font.render("레벨업!",True,config.WHITE); surface.blit(title_s,title_s.get_rect(center=(config.SCREEN_WIDTH//2,config.SCREEN_HEIGHT//4))) # 한글 변경
        except pygame.error as e: print(f"ERROR: 레벨업 타이틀 렌더링 실패: {e}."); pass
        try:
            instr_s = font.render("선택 (키보드 1, 2 또는 3):",True,config.WHITE); surface.blit(instr_s,instr_s.get_rect(center=(config.SCREEN_WIDTH//2,config.SCREEN_HEIGHT//4+60))) # 한글 변경
        except pygame.error as e: print(f"ERROR: 레벨업 안내 렌더링 실패: {e}."); pass
        
        opt_y, box_w, box_h, spacing = config.SCREEN_HEIGHT//2-100, config.SCREEN_WIDTH*0.8, 60, 15
        for i, opt_data in enumerate(player_obj.upgrade_options_to_display):
            b_y = opt_y + i*(box_h+spacing); b_x = (config.SCREEN_WIDTH-box_w)/2
            opt_r = pygame.Rect(b_x,b_y,box_w,box_h)
            pygame.draw.rect(surface,config.UI_OPTION_BOX_BG_COLOR,opt_r,border_radius=10)
            pygame.draw.rect(surface,config.UI_OPTION_BOX_BORDER_COLOR,opt_r,2,border_radius=10)
            try:
                txt_s = small_font.render(f"[{i+1}] {opt_data['text']}",True,config.WHITE)
                surface.blit(txt_s,txt_s.get_rect(center=opt_r.center))
            except pygame.error as e: print(f"ERROR: 업그레이드 옵션 {i+1} 렌더링 실패: {e}."); pass

# ui.py (맨 아래에 추가)
class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = config.RED 
        self.text = text
        self.font = medium_font # ui.py 상단에서 로드된 폰트 사용
        self.active = False # 현재 입력이 활성화되었는지 여부
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 사용자가 상자를 클릭했는지 확인
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = config.RED if self.active else config.UI_OPTION_BOX_BORDER_COLOR # 활성화 시 빨간색 표시
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN: # 엔터 키를 누르면 입력 종료
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode:
                    # 텍스트가 너무 길어지지 않도록 제한
                    if len(self.text) < 15:
                        self.text += event.unicode # 입력된 문자를 추가
                self.color = config.RED if self.active else config.UI_OPTION_BOX_BORDER_COLOR # 엔터 입력 후 색상 복구
        return not self.active and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN

    def draw(self, screen):
        # 텍스트 상자 그리기
        pygame.draw.rect(screen, config.UI_OPTION_BOX_BG_COLOR, self.rect, border_radius=5)
        pygame.draw.rect(screen, self.color, self.rect, 3, border_radius=5)
        
        # 입력된 텍스트 그리기
        if self.font:
            try:
                text_surface = self.font.render(self.text if self.text else "닉네임을 입력하세요", True, config.WHITE)
                # 텍스트를 상자 중앙에 위치
                text_rect = text_surface.get_rect(center=self.rect.center)
                screen.blit(text_surface, text_rect)
            except pygame.error as e:
                print(f"ERROR: InputBox 텍스트 렌더링 실패: {e}.")