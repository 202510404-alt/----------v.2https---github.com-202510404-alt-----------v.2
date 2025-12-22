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

# 랭킹 항목 정보 (버튼 텍스트와 내부 키 매핑)
CATEGORY_INFO = [
    {"name": "난이도 배율", "key": "DifficultyScore"},
    {"name": "최고 레벨", "key": "Level"},
    {"name": "총 킬 수", "key": "Kills"},
    {"name": "보스 처치", "key": "Bosses"},
    {"name": "생존 시간", "key": "SurvivalTime"}
]
# 랭킹 버튼 Rect를 저장할 전역 리스트 (main.py에서도 사용)
RANKING_BUTTONS = []
BUTTON_W, BUTTON_H = 150, 40 # 버튼 크기

# --- Custom font loading attempt (D2Coding.ttf) ---
try:
    font = pygame.font.Font(FONT_FILE_NAME, 30)
    small_font = pygame.font.Font(FONT_FILE_NAME, 24)
    large_font = pygame.font.Font(FONT_FILE_NAME, 74)
    medium_font = pygame.font.Font(FONT_FILE_NAME, 36)
    print(f"정보: 폰트 파일 '{FONT_FILE_NAME}'을(를) 성공적으로 로드했습니다.")
    # ... (생략: DEBUG 출력)
except pygame.error as e: 
    print(f"경고: 폰트 파일 '{FONT_FILE_NAME}'을(를) 로드할 수 없습니다: {e}. 시스템 폰트 (SysFont)로 대체 시도합니다.")
    
    # --- Fallback to SysFont (시스템 내 한글 폰트 찾기) ---
    fallback_font_names = ["Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "Arial", "sans", "korean"] 
    for fname in fallback_font_names:
        try:
            temp_font = pygame.font.SysFont(fname, 30)
            if temp_font and temp_font.get_height() > 0: 
                font = temp_font
                small_font = pygame.font.SysFont(fname, 24)
                large_font = pygame.font.SysFont(fname, 74)
                medium_font = pygame.font.SysFont(fname, 36)
                print(f"정보: 시스템 폰트 '{fname}'을(를) 성공적으로 로드했습니다.")
                break
        except pygame.error:
            continue
    
    if font is None:
        print("심각 경고: 모든 시스템 폰트 로드마저 실패했습니다. Pygame 기본 폰트 (Font(None))로 최종 시도합니다.")
        try:
            font = pygame.font.Font(None, 30)
            small_font = pygame.font.Font(None, 24)
            large_font = pygame.font.Font(None, 74)
            medium_font = pygame.font.Font(None, 36)
            print("정보: 최종적으로 Pygame 기본 폰트 (Font(None))를 로드했습니다.")
        except pygame.error as e_final_fallback:
            print(f"치명적 오류: 최종 기본 폰트 로드마저 실패했습니다: {e_final_fallback}. 텍스트 표시가 불가능하며, 게임이 불안정할 수 있습니다.")
            font = small_font = large_font = medium_font = None
except Exception as e_general:
    print(f"치명적 오류: 폰트 로딩 중 예상치 못한 일반 오류 발생: {e_general}. 텍스트 표시가 불가능할 수 있습니다.")
    font = small_font = large_font = medium_font = None

# 🚩 랭킹 버튼 위치 미리 계산 함수
def setup_ranking_buttons():
    global RANKING_BUTTONS
    total_w = len(CATEGORY_INFO) * BUTTON_W + (len(CATEGORY_INFO) - 1) * 10 # 총 가로 길이
    start_x = (config.SCREEN_WIDTH - total_w) // 2 
    start_y = config.SCREEN_HEIGHT - 60 # 화면 아래쪽
    
    RANKING_BUTTONS.clear()
    for i, info in enumerate(CATEGORY_INFO):
        rect = pygame.Rect(start_x + i * (BUTTON_W + 10), start_y, BUTTON_W, BUTTON_H)
        RANKING_BUTTONS.append({"rect": rect, "key": info['key'], "name": info['name']})
    return RANKING_BUTTONS


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

def draw_main_menu(surface, start_button_rect, exit_button_rect, is_game_over, ranking_button_rect):
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
            title_s = large_font.render("게임 시작하기", True, config.BLUE)
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

    # 🚩 랭킹 버튼
    pygame.draw.rect(surface, config.UI_OPTION_BOX_BG_COLOR, ranking_button_rect, border_radius=15)
    pygame.draw.rect(surface, config.UI_OPTION_BOX_BORDER_COLOR, ranking_button_rect, 3, border_radius=15)
    try:
        ranking_text = medium_font.render("랭킹 보기", True, config.WHITE)
        surface.blit(ranking_text, ranking_text.get_rect(center=ranking_button_rect.center))
    except pygame.error as e:
        print(f"ERROR: 랭킹 버튼 텍스트 렌더링 실패: {e}.")


    # 게임 종료 버튼 (빨간 X)
    pygame.draw.rect(surface, config.RED, exit_button_rect, border_radius=5)
    try:
        exit_text = medium_font.render("X", True, config.WHITE)
        surface.blit(exit_text, exit_button_rect.center) # 텍스트 중앙 위치 수정
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

    # 🚩 닉네임 표시 로직 추가
    try:
        name_text = font.render(f"ID: {player_obj.name}", True, config.WHITE)
        name_text_x = config.SCREEN_WIDTH - name_text.get_width() - 10 
        name_text_y = 10 
        surface.blit(name_text, (name_text_x, name_text_y))
    except pygame.error as e:
        print(f"ERROR: 닉네임 텍스트 렌더링 실패: {e}.")
        pass

    # --- HP 게이지 바 ---
    hp_bar_x, hp_bar_y = 10, 10
    hp_bar_width, hp_bar_height = 150, 20
    hp_ratio = player_obj.hp / player_obj.max_hp if player_obj.max_hp > 0 else 0

    try:
        pygame.draw.rect(surface, config.DARK_RED, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), border_radius=3) 
        current_hp_bar_width = int(hp_bar_width * hp_ratio)
        if current_hp_bar_width > 0:
            pygame.draw.rect(surface, config.HP_BAR_GREEN, (hp_bar_x, hp_bar_y, current_hp_bar_width, hp_bar_height), border_radius=3)
        
        hp_text_surface = small_font.render(f"HP: {player_obj.hp}/{player_obj.max_hp}", True, config.WHITE)
        hp_text_rect = hp_text_surface.get_rect(center=(hp_bar_x + hp_bar_width/2, hp_bar_y + hp_bar_height/2))
        surface.blit(hp_text_surface, hp_text_rect)
    except pygame.error as e:
        print(f"ERROR: HP 게이지 렌더링 실패: {e}.")
        pass
    
    # --- 레벨 표시 ---
    try:
        level_text = font.render(f"레벨: {player_obj.level}", True, config.WHITE)
        surface.blit(level_text, (hp_bar_x, hp_bar_y + hp_bar_height + 5))
    except pygame.error as e:
        print(f"ERROR: 레벨 텍스트 렌더링 실패: {e}.")
        pass

    # --- 경험치 바 ---
    exp_bar_x, exp_bar_y = hp_bar_x, hp_bar_y + hp_bar_height + 5 + 30 
    exp_bar_width, exp_bar_height = hp_bar_width, 15
    exp_ratio = player_obj.exp / player_obj.exp_to_level_up if player_obj.exp_to_level_up > 0 else 0

    try:
        pygame.draw.rect(surface, config.DARK_RED, (exp_bar_x, exp_bar_y, exp_bar_width, exp_bar_height), border_radius=3)
        current_exp_width = int(exp_bar_width * exp_ratio)
        if current_exp_width > 0: pygame.draw.rect(surface, config.EXP_BAR_COLOR, (exp_bar_x, exp_bar_y, current_exp_width, exp_bar_height), border_radius=3)
        
        exp_text_surface = small_font.render(f"EXP: {player_obj.exp}/{player_obj.exp_to_level_up}", True, config.WHITE)
        exp_text_rect = exp_text_surface.get_rect(center=(exp_bar_x + exp_bar_width/2, exp_bar_y + exp_bar_height/2))
        surface.blit(exp_text_surface, exp_text_rect)
    except pygame.error as e:
        print(f"ERROR: EXP 게이지 렌더링 실패: {e}.")
        pass

    y_offset = exp_bar_y + exp_bar_height + 15

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
             extra_info = f" (샷:{wpn.num_daggers_per_shot})"
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
                f"{sk.name} L{sk.level} (데미지:{sk.get_current_projectile_damage()} x{sk.num_projectiles})", 
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
    info_y_start = config.SCREEN_HEIGHT - 90
    try:
        difficulty_level = current_slime_max_hp_val / config.SLIME_INITIAL_BASE_HP
        difficulty_text = font.render(f"난이도: {difficulty_level:.1f}x", True, config.WHITE)
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
    boss_gauge_y = 10
    
    progress_in_current_cycle = slime_kill_count_val % boss_spawn_threshold_val
    boss_gauge_ratio = progress_in_current_cycle / boss_spawn_threshold_val if boss_spawn_threshold_val > 0 else 0

    try:
        pygame.draw.rect(surface, (100, 50, 0), (boss_gauge_x, boss_gauge_y, boss_gauge_width, boss_gauge_height), border_radius=5) 
        if boss_gauge_ratio > 0:
            pygame.draw.rect(surface, (255, 140, 0), (boss_gauge_x, boss_gauge_y, int(boss_gauge_width * boss_gauge_ratio), boss_gauge_height), border_radius=5)
        
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
            title_s = large_font.render("레벨업!",True,config.WHITE); surface.blit(title_s,title_s.get_rect(center=(config.SCREEN_WIDTH//2,config.SCREEN_HEIGHT//4))) 
        except pygame.error as e: print(f"ERROR: 레벨업 타이틀 렌더링 실패: {e}."); pass
        try:
            instr_s = font.render("선택 (키보드 1, 2 또는 3):",True,config.WHITE); surface.blit(instr_s,instr_s.get_rect(center=(config.SCREEN_WIDTH//2,config.SCREEN_HEIGHT//4+60)))
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


# 🚩🚩 랭킹 화면 그리기 함수 추가 🚩🚩
def draw_ranking_screen(surface, filtered_rankings, current_category_key):
    """랭킹 화면 및 데이터를 그립니다."""
    surface.fill(config.DARK_GREEN) 
    
    # 제목
    try:
        title_s = large_font.render("온라인 랭킹", True, config.WHITE)
        surface.blit(title_s, title_s.get_rect(center=(config.SCREEN_WIDTH // 2, 50)))
        
        # ESC 안내
        esc_s = small_font.render("ESC: 메뉴로 복귀", True, config.WHITE)
        surface.blit(esc_s, esc_s.get_rect(topright=(config.SCREEN_WIDTH - 10, 10)))
        
    except pygame.error as e:
        print(f"ERROR: 랭킹 타이틀 렌더링 실패: {e}.")

    # 🚩 카테고리 표시 (현재 어떤 랭킹을 보는지)
    current_category_name = next((info['name'] for info in CATEGORY_INFO if info['key'] == current_category_key), "Unknown")
    try:
        category_s = medium_font.render(f"--- {current_category_name} ---", True, config.YELLOW)
        surface.blit(category_s, category_s.get_rect(center=(config.SCREEN_WIDTH // 2, 110)))
    except pygame.error as e:
        print(f"ERROR: 카테고리 텍스트 렌더링 실패: {e}.")


    # 랭킹 데이터 표시 (테이블)
    start_y = 150
    row_height = 30
    
    # 🚩 헤더
    header_format = "{:<5} {:<15} {:>10} {:>10} {:>10}"
    try:
        header_text = small_font.render(header_format.format("순위", "ID", current_category_name, "LV", "Kills"), True, config.YELLOW)
        surface.blit(header_text, (30, start_y))
    except pygame.error as e: print(f"ERROR: 랭킹 헤더 렌더링 실패: {e}.")

    start_y += row_height + 5

    # 데이터 표시
    if filtered_rankings is None: # 로딩 중
        try:
            loading_text = font.render("로딩 중...", True, config.YELLOW)
            surface.blit(loading_text, loading_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)))
        except pygame.error as e: pass
    elif not filtered_rankings: # 데이터 없음
        try:
            no_data_text = font.render("아직 기록이 없습니다.", True, config.WHITE)
            surface.blit(no_data_text, no_data_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)))
        except pygame.error as e: pass
    else:
        for i, record in enumerate(filtered_rankings):
            rank = i + 1
            
            # 기록 값 포맷팅
            rank_value = record.get('RankValue', 0)
            score_key = current_category_key
            
            if score_key in ["DifficultyScore", "SurvivalTime"]:
                score_str = f"{float(rank_value):.2f}"
            else:
                score_str = str(int(rank_value))
            
            # 최종 표시 문자열
            display_str = header_format.format(
                f"#{rank}", 
                str(record.get('ID', 'N/A')), 
                score_str,
                str(record.get('Level', 0)),
                str(record.get('Kills', 0))
            )
            
            try:
                rank_color = config.YELLOW if rank <= 3 else config.WHITE
                rank_text = small_font.render(display_str, True, rank_color)
                surface.blit(rank_text, (30, start_y + i * row_height))
            except pygame.error as e:
                print(f"ERROR: 랭킹 항목 렌더링 실패: {e}.")

    # 🚩 랭킹 카테고리 버튼 그리기
    for button_info in RANKING_BUTTONS:
        rect = button_info['rect']
        text_name = button_info['name']
        is_active = button_info['key'] == current_category_key

        bg_color = config.RED if is_active else config.UI_OPTION_BOX_BG_COLOR
        border_color = config.YELLOW if is_active else config.UI_OPTION_BOX_BORDER_COLOR

        pygame.draw.rect(surface, bg_color, rect, border_radius=5)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=5)
        
        try:
            btn_text = small_font.render(text_name, True, config.WHITE)
            surface.blit(btn_text, btn_text.get_rect(center=rect.center))
        except pygame.error:
            pass


# 🚩🚩 InputBox 클래스 추가 (ui.py에 필수) 🚩🚩
class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = config.RED
        self.text = text
        self.font = medium_font 
        self.active = True
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = config.RED if self.active else config.UI_OPTION_BOX_BORDER_COLOR
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN: 
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode: 
                    if len(self.text) < 15:
                        self.text += event.unicode
                
                self.color = config.RED if self.active else config.UI_OPTION_BOX_BORDER_COLOR
        
        return not self.active and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN

    def draw(self, screen):
        pygame.draw.rect(screen, config.UI_OPTION_BOX_BG_COLOR, self.rect, border_radius=5)
        pygame.draw.rect(screen, self.color, self.rect, 3, border_radius=5)
        
        if self.font:
            try:
                # 닉네임을 입력하세요 텍스트를 그릴 때, 텍스트가 비어있지 않은지 확인
                display_text = self.text if self.text else "닉네임을 입력하세요"
                text_surface = self.font.render(display_text, True, config.WHITE)
                
                # 텍스트 중앙 위치 수정
                text_rect = text_surface.get_rect(center=self.rect.center)
                screen.blit(text_surface, text_rect)
            except pygame.error as e:
                print(f"ERROR: InputBox 텍스트 렌더링 실패: {e}.")