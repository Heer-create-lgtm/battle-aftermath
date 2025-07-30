import pygame
import math
from settings import ZOMBIE_HEALTH, ZOMBIE_SPEED, ZOMBIE_IMAGE_SIZE, TILE_SIZE, ZOMBIE_COLOR, ZOMBIE_BLOOD_COLOR

class Zombie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0 # Will be updated to face the player
        self.health = ZOMBIE_HEALTH
        self.speed = ZOMBIE_SPEED
        self.radius = ZOMBIE_IMAGE_SIZE // 2
        self.is_alive = True
        self.last_attack_time = 0
        
        # Initialize attack sound (can be overridden by subclasses)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/music/zombie.ogg")
        except Exception:
            self.attack_sound = None

        # Sounds
        try:
            self.damage_sound = pygame.mixer.Sound("assets/music/zombie.ogg")
        except Exception:
            self.damage_sound = None

        # Blood splat effect as [{'x': int, 'y': int, 'r': int, 'timer': float}]
        self.blood_splatters = []   # Each fades out over time

        try:
            self.image = pygame.image.load('assets/sprites/zombies.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (ZOMBIE_IMAGE_SIZE, ZOMBIE_IMAGE_SIZE))
        except pygame.error:
            self.image = None

    def update(self, player_x, player_y, game_map, dt):
        if not self.is_alive:
            return False
            
        # Call attack sound if available when in range
        if hasattr(self, 'attack_sound') and self.attack_sound:
            dist_to_player = math.hypot(player_x - self.x, player_y - self.y)
            if dist_to_player < self.radius * 2:  # If in attack range
                self.attack()

        # Fade splatters
        for splat in self.blood_splatters:
            splat['timer'] -= dt
        # Clean up expired
        self.blood_splatters = [s for s in self.blood_splatters if s['timer'] > 0]

        # Move towards player
        self.angle = math.atan2(player_y - self.y, player_x - self.x)
        dx = math.cos(self.angle) * self.speed * dt
        dy = math.sin(self.angle) * self.speed * dt

        # Get map dimensions
        map_height = len(game_map)
        if map_height == 0:
            return
        map_width = len(game_map[0])

        # Calculate potential new positions
        new_x = self.x + dx
        new_y = self.y + dy

        # Check x movement
        if 0 <= new_x < map_width * TILE_SIZE:
            target_col = int(new_x / TILE_SIZE)
            row = int(self.y / TILE_SIZE)
            if 0 <= row < map_height and 0 <= target_col < map_width:
                if game_map[row][target_col] not in ['W', 'P']:
                    self.x = new_x
            else:
                # If we're at the map edge, stop horizontal movement
                pass

        # Check y movement
        if 0 <= new_y < map_height * TILE_SIZE:
            target_row = int(new_y / TILE_SIZE)
            col = int(self.x / TILE_SIZE)
            if 0 <= target_row < map_height and 0 <= col < map_width:
                if game_map[target_row][col] not in ['W', 'P']:
                    self.y = new_y
            else:
                # If we're at the map edge, stop vertical movement
                pass
        return False

    def attack(self):
        """Play attack sound if available. Can be overridden by subclasses."""
        if hasattr(self, 'attack_sound') and self.attack_sound:
            try:
                self.attack_sound.play()
            except Exception:
                pass
                
    def take_damage(self, amount):
        self.health -= amount
        # Play sound if available
        if hasattr(self, 'damage_sound') and self.damage_sound:
            try:
                self.damage_sound.play()
            except Exception:
                pass
        import random
        # Add blood splatter with small random offset
        offset_angle = random.uniform(0, 2 * math.pi)
        offset_dist = random.uniform(self.radius // 4, self.radius // 2)
        bx = self.x + math.cos(offset_angle) * offset_dist
        by = self.y + math.sin(offset_angle) * offset_dist
        rad = random.randint(self.radius // 5, self.radius // 2)
        self.blood_splatters.append({
            'x': bx,
            'y': by,
            'r': rad,
            'timer': 0.4
        })

        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            return True  # Return True to indicate this zombie just died
        return False  # Return False if zombie is still alive
            
    def check_collision(self, x, y, radius):
        """Check if a point (x,y) with given radius collides with the zombie."""
        if not self.is_alive:
            return False
        distance = math.sqrt((self.x - x)**2 + (self.y - y)**2)
        return distance < (self.radius + radius)

    def draw(self, screen):
        if not self.is_alive:
            return

        # Draw green blood splatters beneath zombie (with fade)
        for splat in self.blood_splatters:
            blood_surf = pygame.Surface((splat['r']*2, splat['r']*2), pygame.SRCALPHA)
            color = ZOMBIE_BLOOD_COLOR[:3] + (int(ZOMBIE_BLOOD_COLOR[3] * (splat['timer'] / 0.4)),) # fade alpha
            pygame.draw.circle(blood_surf, color, (splat['r'], splat['r']), splat['r'])
            screen.blit(blood_surf, (splat['x']-splat['r'], splat['y']-splat['r']))

        if self.image:
            # The angle needs to be converted to degrees and inverted for pygame's rotation system
            # We also add 90 degrees because the sprite might be facing upwards by default.
            rotated_image = pygame.transform.rotate(self.image, -math.degrees(self.angle) - 90)
            rotated_rect = rotated_image.get_rect(center=(self.x, self.y))
            screen.blit(rotated_image, rotated_rect)
        else:
            # Fallback to drawing a circle if image failed to load
            pygame.draw.circle(screen, ZOMBIE_COLOR, (int(self.x), int(self.y)), self.radius)