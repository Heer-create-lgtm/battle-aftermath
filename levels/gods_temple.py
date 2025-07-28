import pygame
import math
import random
from settings import *
from zombie import Zombie
from special_zombies import random_zombie
from levels.dialogue import show_dialogue
from mechanics import handle_player_input

class CorruptedGod:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 500
        self.max_health = 500
        self.radius = 40
        self.attack_cooldown = 0
        self.attack_delay = 2000  # 2 seconds between attacks
        self.last_attack = 0
        self.is_alive = True
        self.phase = 1
        
        # Load assets
        try:
            self.image = pygame.image.load('assets/sprites/corrupted_god.png').convert_alpha()
            # Scale to 240x240 pixels (120 radius) for better visibility
            self.radius = 120
            self.image = pygame.transform.scale(self.image, (self.radius*2, self.radius*2))
        except Exception as e:
            print(f"Error loading corrupted god sprite: {e}")
            self.image = None
            
    def update(self, player, current_time, dt):
        """Update god's state and attacks."""
        if self.health <= self.max_health // 2 and self.phase == 1:
            self.phase = 2
            return "PHASE_CHANGE"
            
        if current_time - self.last_attack > self.attack_delay:
            self.last_attack = current_time
            return self.attack(player)
        return None
        
    def attack(self, player):
        """Execute attack pattern based on current phase."""
        if self.phase == 1:
            return self._phase_one_attack(player)
        else:
            return self._phase_two_attack(player)
    
    def _phase_one_attack(self, player):
        """First phase: Basic projectile attacks."""
        angle = math.atan2(player.y - self.y, player.x - self.x)
        return {
            'type': 'projectile',
            'x': self.x,
            'y': self.y,
            'angle': angle,
            'speed': 200,
            'damage': 20,
            'radius': 10
        }
        
    def _phase_two_attack(self, player):
        """Second phase: Summon corrupted minions."""
        summoned = []
        for _ in range(3):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(120, 180)
            x = self.x + math.cos(angle) * dist
            y = self.y + math.sin(angle) * dist
            # Create a random zombie instance directly so we don't need extra handling later
            summoned.append(random_zombie(x, y))
        return {'type': 'summon', 'minions': summoned}
    
    def take_damage(self, amount):
        """Handle damage taken."""
        self.health -= amount
        if self.health <= 0:
            self.is_alive = False
            return True
        return False
    
    def draw(self, screen):
        """Draw the corrupted god."""
        if self.image:
            screen.blit(self.image, (int(self.x - self.radius), int(self.y - self.radius)))
        else:
            # Fallback drawing
            pygame.draw.circle(screen, (150, 0, 150), (int(self.x), int(self.y)), self.radius)
            
        # Draw health bar
        health_ratio = self.health / self.max_health
        bar_width = 100
        bar_height = 10
        pygame.draw.rect(screen, (255, 0, 0), (self.x - bar_width//2, self.y - 50, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (self.x - bar_width//2, self.y - 50, bar_width * health_ratio, bar_height))

def run_gods_temple():
    """Run the gods' temple level."""
    from player import Player
    
    # Initialize player
    player = Player()
    player.x = SCREEN_WIDTH // 4
    player.y = SCREEN_HEIGHT // 2
    
    # Initialize corrupted god
    god = CorruptedGod(SCREEN_WIDTH * 3//4, SCREEN_HEIGHT // 2)
    
    # Initialize level state
    bullets = []  # God projectiles
    player_bullets = []  # Hero projectiles
    minions = []
    level_complete = False
    
    # Show intro dialogue
    show_dialogue([
        "You stand before the corrupted temple of the gods...",
        "The air crackles with dark energy.",
        "A familiar presence calls out to you...",
        "'I was wrong to cast you out... but now it's too late.'",
        "The lesser god appears, twisted by corruption!"
    ])
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    while running and not level_complete:
        dt = clock.tick(60) / 1000.0
        current_time = pygame.time.get_ticks()
        
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return "QUIT"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "PAUSE"
        
        # ---- Handle player input (movement & shooting) ----
        # movement keys
        keys = pygame.key.get_pressed()
        player.update(keys, [], False, dt)  # No walls, not throne room
        # shooting / reload etc
        handle_player_input(player, player_bullets, events)
        
        # Update god
        god_action = god.update(player, current_time, dt)
        if god_action == "PHASE_CHANGE":
            show_dialogue(["The god's form shifts as corruption takes hold!", "'I can't hold it back much longer!'"])
        elif god_action and god_action.get('type') == 'projectile':
            bullets.append(god_action)
        elif god_action and god_action.get('type') == 'summon':
            minions.extend(god_action['minions'])
        
        # -------- Update god projectiles --------
        for b in bullets[:]:
            b['x'] += math.cos(b['angle']) * b['speed'] * dt
            b['y'] += math.sin(b['angle']) * b['speed'] * dt
            # out of bounds
            if b['x'] < 0 or b['x'] > SCREEN_WIDTH or b['y'] < 0 or b['y'] > SCREEN_HEIGHT:
                bullets.remove(b)
                continue
            # collision with player
            if math.hypot(player.x - b['x'], player.y - b['y']) < b['radius'] + getattr(player, 'radius', 15):
                player.health -= b['damage']
                bullets.remove(b)
                if player.health <= 0:
                    return "GAME_OVER"

        # -------- Update player bullets --------
        for pb in player_bullets[:]:
            pb_speed = 350
            pb['x'] += math.cos(pb['angle']) * pb_speed * dt
            pb['y'] += math.sin(pb['angle']) * pb_speed * dt
            if pb['x'] < 0 or pb['x'] > SCREEN_WIDTH or pb['y'] < 0 or pb['y'] > SCREEN_HEIGHT:
                player_bullets.remove(pb)
                continue
            # collision with god
            if math.hypot(god.x - pb['x'], god.y - pb['y']) < god.radius + 5:
                god.take_damage(pb.get('damage', 20))
                if pb in player_bullets:
                    player_bullets.remove(pb)

        
        # Check for player victory
        if not god.is_alive:
            show_dialogue([
                "The corrupted god falls to their knees...",
                "'Thank you... for freeing me...'",
                "As the corruption fades, you feel a new power awakening within you..."
            ])
            level_complete = True
            return "VICTORY"
            
        # Draw everything
        screen = pygame.display.get_surface()
        screen.fill((20, 10, 30))  # Dark purple background
        
        # Draw temple environment
        # (Add temple drawing code here)
        
        # Draw entities
        god.draw(screen)
        for m in minions:
            m.update(player.x, player.y, [], dt)
            m.draw(screen)
        for b in bullets:
            pygame.draw.circle(screen, (255, 50, 50), (int(b['x']), int(b['y'])), b['radius'])
        for pb in player_bullets:
            pygame.draw.circle(screen, (255, 255, 0), (int(pb['x']), int(pb['y'])), 4)
        player.draw(screen)
        
        pygame.display.flip()
    
    return "MAIN_MENU"  # Fallback return
