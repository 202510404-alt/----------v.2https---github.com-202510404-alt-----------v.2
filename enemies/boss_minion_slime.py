# enemies/boss_minion_slime.py (수정됨)
import config
from enemies.mint_slime import MintSlime # MintSlime 클래스 상속

class BossMinionSlime(MintSlime):
    # 보스 미니언 슬라임도 current_total_max_hp를 받아서 계산
    def __init__(self, world_x, world_y, current_total_max_hp):
        # MintSlime의 특성을 그대로 상속받되, 색상만 변경
        # MintSlime은 hp_multiplier가 0.5로 설정되어 있으므로, BossMinionSlime은 추가로 수정할 필요 없음
        super().__init__(world_x, world_y, current_total_max_hp) # MintSlime의 __init__에 current_total_max_hp 전달
        self.color = config.BOSS_MINION_SLIME_COLOR