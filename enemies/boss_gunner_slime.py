import random
import config
from enemies.slime import Slime
from enemies.shooter_slime import ShooterSlime
from enemies.boss_minion_slime import BossMinionSlime

class BossGunnerSlime(ShooterSlime, BossMinionSlime):
    def __init__(self, world_x, world_y, current_total_max_hp):
        # 1. ShooterSlime 스펙 설정 (반지름 및 속도)
        radius = config.SLIME_RADIUS
        speed = config.SLIME_SPEED * config.SHOOTER_SLIME_SPEED_FACTOR
        
        # 2. Slime 클래스의 생성자를 직접 호출하여 초기화 (MRO 에러 방지)
        # 색상은 보스 미니언 색상으로 설정
        Slime.__init__(self, world_x, world_y, radius, config.BOSS_MINION_SLIME_COLOR, speed, current_total_max_hp, hp_multiplier=1.0)
        
        # 3. ShooterSlime 사격 타이머 설정
        self.shoot_cooldown_timer = random.randint(0, config.SHOOTER_SLIME_SHOOT_COOLDOWN)

    def _get_image_filename_prefix(self):
        """
        🚩 보스 거너 슬라임이 보스 미니언 슬라임(minislime)의 이미지를 
        사용하도록 강제로 지정합니다.
        """
        return "minislime"

    # update 메서드는 ShooterSlime의 것을 그대로 사용하여 사격 패턴 수행