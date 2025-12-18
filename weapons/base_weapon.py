# weapons/base_weapon.py

class Weapon:
    def __init__(self, player_ref):
        self.player = player_ref
        self.level = 1
        self.damage = 0
        self.name = "기본 무기"
    def update(self, slimes_list, game_entities_lists): pass
    def draw(self, surface, camera_offset_x, camera_offset_y): pass
    def get_level_up_options(self): return []
    def apply_upgrade(self, upgrade_info): pass
    def on_remove(self): pass # 이 메소드는 main.py에서 해당 무기 관련 엔티티를 정리하도록 신호 역할만