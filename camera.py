# camera.py
import config

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.world_x = 0
        self.world_y = 0

    def update(self, target_player):
        self.world_x = (target_player.world_x - config.SCREEN_WIDTH // 2)
        self.world_y = (target_player.world_y - config.SCREEN_HEIGHT // 2)