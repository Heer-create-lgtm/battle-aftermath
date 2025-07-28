import math
import random
import pygame

from zombie import Zombie
from settings import TILE_SIZE, ZOMBIE_HEALTH, ZOMBIE_SPEED

# Default pixel sizes for special zombies (recommendation for sprite designers)
ACID_SPITTER_SIZE = 24  # 24x24 sprite
JUGGERNAUT_SIZE = 32    # 32x32 sprite

class AcidSpitter(Zombie):
    """Ranged zombie that spits acid projectiles."""
    spit_cooldown_ms = 1500
    spit_cooldown_ms = 1500
    """A ranged zombie that could spit acid (placeholder behaviour)."""
    def __init__(self, x, y):
        super().__init__(x, y)
        # Override stats
        self.health = int(ZOMBIE_HEALTH * 0.8)
        self.speed = ZOMBIE_SPEED * 1.1
        self.radius = ACID_SPITTER_SIZE // 2
        
        # Load sound effect
        try:
            self.attack_sound = pygame.mixer.Sound('assets/music/acid.ogg')
        except Exception:
            self.attack_sound = None
            
        # Load dedicated sprite if available
        try:
            img = pygame.image.load('assets/sprites/acid_spitter.png').convert_alpha()
            self.image = pygame.transform.scale(img, (ACID_SPITTER_SIZE, ACID_SPITTER_SIZE))
        except Exception:
            # Fallback to existing zombie sprite size change handled in parent
            pass
            
    def attack(self):
        """Play attack sound if available."""
        if hasattr(self, 'attack_sound') and self.attack_sound:
            try:
                self.attack_sound.play()
            except Exception:
                pass

    def update(self, player_x, player_y, game_map, dt):
        """Move like normal zombie and occasionally spit acid projectile."""
        super().update(player_x, player_y, game_map, dt)
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_next_spit'):
            self._next_spit = current_time + self.spit_cooldown_ms
        if current_time >= self._next_spit and self.is_alive:
            angle = math.atan2(player_y - self.y, player_x - self.x)
            speed = 300
            proj = {'x': self.x, 'y': self.y, 'angle': angle, 'speed': speed, 'damage': 10, 'acid': True, 'radius': 4}
            self._next_spit = current_time + self.spit_cooldown_ms
            return proj
        return None

class Juggernaut(Zombie):
    """Tanky melee zombie that causes screen quake when it slams."""
    quake_cooldown_ms = 2000
    quake_cooldown_ms = 2000
    """A tanky slow zombie."""
    def __init__(self, x, y):
        super().__init__(x, y)
        # Override stats
        self.health = int(ZOMBIE_HEALTH * 3)
        self.speed = ZOMBIE_SPEED * 0.6
        self.radius = JUGGERNAUT_SIZE // 2
        
        # Load sound effect
        try:
            self.attack_sound = pygame.mixer.Sound('assets/music/juggernaut.ogg')
        except Exception:
            self.attack_sound = None
            
        try:
            img = pygame.image.load('assets/sprites/juggernaut.png').convert_alpha()
            self.image = pygame.transform.scale(img, (JUGGERNAUT_SIZE, JUGGERNAUT_SIZE))
        except Exception:
            pass
            
    def attack(self):
        """Play attack sound if available."""
        if hasattr(self, 'attack_sound') and self.attack_sound:
            try:
                self.attack_sound.play()
            except Exception:
                pass

    def update(self, player_x, player_y, game_map, dt):
        """Move and trigger quake when near player."""
        super().update(player_x, player_y, game_map, dt)
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_next_quake'):
            self._next_quake = current_time + self.quake_cooldown_ms
        dist = math.hypot(player_x - self.x, player_y - self.y)
        if dist < self.radius * 2 and current_time >= self._next_quake and self.is_alive:
            self.attack()
            self._next_quake = current_time + self.quake_cooldown_ms
            return {'quake': True, 'duration': 500}
        return None

# Helper to randomly create a zombie instance given coordinates
SPECIAL_ZOMBIE_CLASSES = [AcidSpitter, Juggernaut]

def random_zombie(x: int, y: int):
    # 70% chance normal zombie, 20% acid spitter, 10% juggernaut
    from zombie import Zombie  # local import to avoid circular
    # Adjusted probabilities to see specials earlier: 50% normal, 30% AcidSpitter, 20% Juggernaut
    choice = random.choices(
        population=[Zombie, AcidSpitter, Juggernaut],
        weights=[50, 30, 20],
        k=1
    )[0]
    return choice(x, y)
