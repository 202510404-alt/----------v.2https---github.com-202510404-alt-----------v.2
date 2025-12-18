# enemies/mint_slime.py (수정됨)
import math
import pygame
import config
from enemies.slime import Slime # Slime 클래스 상속

class MintSlime(Slime):
    # 민트 슬라임도 current_total_max_hp를 받아서 계산
    def __init__(self, world_x, world_y, current_total_max_hp):
        radius = config.SLIME_RADIUS * config.MINT_SLIME_RADIUS_FACTOR
        speed = config.SLIME_SPEED * config.MINT_SLIME_SPEED_FACTOR
        # MintSlime은 기본 슬라임 HP의 50%를 가지므로, hp_multiplier를 0.5로 전달
        super().__init__(world_x, world_y, radius, config.MINT_SLIME_COLOR, speed, current_total_max_hp, hp_multiplier=0.5)