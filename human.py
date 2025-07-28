import pygame
import math
from settings import TILE_SIZE, HUMAN_SPEED, HUMAN_SCARED_DISTANCE, HUMAN_COLOR

class Human:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = TILE_SIZE // 2 - 4
        self.speed = HUMAN_SPEED
        self.state = 'WALKING' # 'WALKING' or 'SCARED'
        
        # Load human image
        try:
            self.image = pygame.image.load('assets/sprites/human.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
            self.rect = self.image.get_rect(center=(self.x, self.y))
        except pygame.error as e:
            print(f"Warning: Could not load human image. Error: {e}")
            self.image = None

    def update(self, player_x, player_y):
        if self.state == 'WALKING':
            # Check distance to player
            dist_to_player = math.hypot(player_x - self.x, player_y - self.y)
            if dist_to_player < HUMAN_SCARED_DISTANCE:
                self.state = 'SCARED'
                return # Stop moving

            # Move towards player
            angle_to_player = math.atan2(player_y - self.y, player_x - self.x)
            self.x += math.cos(angle_to_player) * self.speed
            self.y += math.sin(angle_to_player) * self.speed

    def draw(self, screen):
        if hasattr(self, 'image') and self.image:
            self.rect.center = (int(self.x), int(self.y))
            screen.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.circle(screen, HUMAN_COLOR, (int(self.x), int(self.y)), self.radius)