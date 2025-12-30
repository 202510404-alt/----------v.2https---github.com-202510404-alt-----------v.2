import config
from enemies.shooter_slime import ShooterSlime
from enemies.boss_minion_slime import BossMinionSlime

class BossGunnerSlime(ShooterSlime, BossMinionSlime):
    def __init__(self, world_x, world_y, current_total_max_hp):
        # 1. ShooterSlime의 __init__을 호출하여 
        #    거너 전용 크기(radius)와 속도(speed)를 상속받아 초기화합니다.
        ShooterSlime.__init__(self, world_x, world_y, current_total_max_hp)
        
        # 2. 외형은 보스 미니언들과 통일하기 위해 보스 미니언 색상을 적용합니다.
        self.color = config.BOSS_MINION_SLIME_COLOR

    # update 로직은 ShooterSlime의 것을 그대로 상속받아 사용하므로 
    # 별도로 작성하지 않아도 사격 패턴이 자동으로 적용됩니다.