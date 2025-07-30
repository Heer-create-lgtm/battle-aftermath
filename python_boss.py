import pygame
import math
import random
from settings import (
    PYTHON_HEALTH, PYTHON_SPEED, PYTHON_TURN_SPEED, PYTHON_BURROW_TIME,
    PYTHON_BODY_SEGMENTS, PYTHON_ENRAGE_HEALTH_THRESHOLD,
    PYTHON_ENRAGE_SPEED_MULTIPLIER, TILE_SIZE, PYTHON_TELEGRAPH_TIME,
    PYTHON_ATTACK_TIME, CHANCE_TO_CHARGE, CHANCE_TO_BURROW,
    PYTHON_ROAMING_TIME_MIN, PYTHON_ROAMING_TIME_MAX,
    PYTHON_CHARGE_SPEED_MULTIPLIER, PYTHON_STUN_DURATION,
    PYTHON_RETREAT_SPEED_MULTIPLIER, POISON_TRAIL_COLOR, DUST_COLOR,
    PYTHON_TELEGRAPH_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, PYTHON_CHARGE_COLOR,
    PYTHON_SHADOW_COLOR, PYTHON_STRIPE_COLOR, PYTHON_BODY_COLOR,
    PYTHON_HEAD_COLOR, PYTHON_ENRAGED_HEAD_COLOR, PYTHON_STUN_EYE_COLOR,
    PYTHON_EYE_COLOR, PYTHON_RETREAT_DURATION, PYTHON_CHARGE_TELEGRAPH_TIME
)

class PythonBoss:
    def __init__(self):
        self.segments = []
        self.health = PYTHON_HEALTH
        self.speed = PYTHON_SPEED
        self.turn_speed = PYTHON_TURN_SPEED
        self.state = 'BURROWED' # BURROWED, TELEGRAPHING, EMERGING, ATTACKING, ROAMING, TELEGRAPHING_CHARGE, CHARGING, STUNNED, RETREATING
        self.timer = PYTHON_BURROW_TIME
        self.is_alive = True
        self.death_scene_triggered = False
        self.angle = 0
        self.telegraph_pos = (0, 0)
        self.charge_target_angle = 0
        self.is_enraged = False

        self.poison_trail = []   # List of dicts {x, y, timer}
        self.dust_effects = []   # List of dicts {x, y, timer}
        self.max_trail_duration = 2.5 # seconds poison puddle lasts
        self.max_dust_duration = 0.6  # seconds
        self.consecutive_charges = 0  # For multi-charge
        self.max_consecutive_charges = 1  # Start with 1, increase if enraged

        # Initialize body segments
        self.segments.append({'x': -100, 'y': -100}) # Head
        for _ in range(PYTHON_BODY_SEGMENTS):
            self.segments.append({'x': -100, 'y': -100})

        # Check for enrage state
        if not self.is_enraged and self.health < PYTHON_HEALTH * PYTHON_ENRAGE_HEALTH_THRESHOLD:
            self.is_enraged = True
            self.speed *= PYTHON_ENRAGE_SPEED_MULTIPLIER
            self.max_consecutive_charges = 3
    def update(self, player_x, player_y, game_map, dt):
        if not self.is_alive:
            if self.state != 'DEFEATED':
                self.state = 'DEFEATED'
                # Clear any active effects when defeated
                self.poison_trail = []
                self.dust_effects = []
            return  # Don't update anything if not alive

        self.timer -= dt

        # ENRAGE mechanic: check on every update
        if not self.is_enraged and self.health < PYTHON_HEALTH * PYTHON_ENRAGE_HEALTH_THRESHOLD:
            self.is_enraged = True
            self.speed *= PYTHON_ENRAGE_SPEED_MULTIPLIER
            self.max_consecutive_charges = 3

        # Clean old poison puddles
        self.poison_trail = [p for p in self.poison_trail if p['timer'] > 0]
        # Decay their timers
        for p in self.poison_trail:
            p['timer'] -= dt

        # Clean dust effects
        self.dust_effects = [d for d in self.dust_effects if d['timer'] > 0]
        for d in self.dust_effects:
            d['timer'] -= dt

        if self.state == 'BURROWED':
            if self.timer <= 0:
                self.state = 'TELEGRAPHING'
                # Pick a valid spot to emerge (inside map and not into a wall)
                max_attempts = 15
                for _ in range(max_attempts):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(TILE_SIZE * 3, TILE_SIZE * 5)
                    cand_x = player_x + math.cos(angle) * distance
                    cand_y = player_y + math.sin(angle) * distance
                    map_x = int(cand_x / TILE_SIZE)
                    map_y = int(cand_y / TILE_SIZE)
                    if 0 <= map_y < len(game_map) and 0 <= map_x < len(game_map[0]) and game_map[map_y][map_x] != 'W':
                        self.telegraph_pos = (cand_x, cand_y)
                        break
                else:
                    # Fallback to player's position if no valid spot found
                    self.telegraph_pos = (player_x, player_y)
                self.timer = PYTHON_TELEGRAPH_TIME

        elif self.state == 'TELEGRAPHING':
            if self.timer <= 0:
                self.state = 'EMERGING'
                self.segments[0]['x'] = self.telegraph_pos[0]
                self.segments[0]['y'] = self.telegraph_pos[1]
                # Reset body segments to the head's new position
                for i in range(1, len(self.segments)):
                    self.segments[i]['x'] = self.segments[0]['x']
                    self.segments[i]['y'] = self.segments[0]['y']
                # Emerge dust
                self.dust_effects.append({'x': self.segments[0]['x'], 'y': self.segments[0]['y'], 'timer': self.max_dust_duration})

        elif self.state == 'EMERGING':
            # Short pause to telegraph; instantly add dust
            self.state = 'ATTACKING'
            self.timer = PYTHON_ATTACK_TIME

        elif self.state in ['ATTACKING', 'ROAMING']:
            if self.timer <= 0:
                # Decide what to do next
                rand_action = random.random()
                if rand_action < CHANCE_TO_CHARGE:
                    self.state = 'TELEGRAPHING_CHARGE'
                    self.timer = PYTHON_CHARGE_TELEGRAPH_TIME
                    self.charge_target_angle = math.atan2(player_y - self.segments[0]['y'], player_x - self.segments[0]['x'])
                elif rand_action < CHANCE_TO_CHARGE + CHANCE_TO_BURROW:
                    self.state = 'BURROWED'
                    self.timer = PYTHON_BURROW_TIME
                else:  # Continue roaming
                    self.state = 'ROAMING'
                    self.timer = random.uniform(PYTHON_ROAMING_TIME_MIN, PYTHON_ROAMING_TIME_MAX)
            # More stable turning logic
            target_angle = math.atan2(player_y - self.segments[0]['y'], player_x - self.segments[0]['x'])
            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            if angle_diff > self.turn_speed * dt:
                self.angle += self.turn_speed * dt
            elif angle_diff < -self.turn_speed * dt:
                self.angle -= self.turn_speed * dt
            else:
                self.angle = target_angle

            next_x = self.segments[0]['x'] + math.cos(self.angle) * self.speed * dt
            next_y = self.segments[0]['y'] + math.sin(self.angle) * self.speed * dt

            # Check for collision with walls
            map_x = int(next_x / TILE_SIZE)
            map_y = int(next_y / TILE_SIZE)
            if (map_y < 0 or map_y >= len(game_map) or map_x < 0 or map_x >= len(game_map[0])) or game_map[map_y][map_x] == 'W':
                self.angle += math.pi
            else:
                self.segments[0]['x'] = next_x
                self.segments[0]['y'] = next_y

        elif self.state == 'TELEGRAPHING_CHARGE':
            if self.timer <= 0:
                self.state = 'CHARGING'
                self.timer = 0.5  # Charge duration
                # Start charge: set number of consecutive charges allowed
                if self.is_enraged:
                    self.consecutive_charges = self.max_consecutive_charges
                else:
                    self.consecutive_charges = 1
                # Dust effect at charge start
                self.dust_effects.append({'x': self.segments[0]['x'], 'y': self.segments[0]['y'], 'timer': self.max_dust_duration})
            self.angle = self.charge_target_angle  # Lock angle

        elif self.state == 'CHARGING':
            if self.timer <= 0:
                if self.consecutive_charges > 1:
                    self.consecutive_charges -= 1
                    # Begin another charge at same angle
                    self.state = 'TELEGRAPHING_CHARGE'
                    self.timer = 0.28  # shorter telegraph for combos
                else:
                    self.state = 'ROAMING'  # Cooldown
                    self.timer = random.uniform(2, 4)
            else:
                # Move forward at high speed
                charge_speed = self.speed * PYTHON_CHARGE_SPEED_MULTIPLIER
                next_x = self.segments[0]['x'] + math.cos(self.angle) * charge_speed * dt
                next_y = self.segments[0]['y'] + math.sin(self.angle) * charge_speed * dt

                # Drop poison trail while charging (if enraged)
                if self.is_enraged:
                    self.poison_trail.append({
                        'x': self.segments[0]['x'],
                        'y': self.segments[0]['y'],
                        'timer': self.max_trail_duration
                    })

                # Check for collision with pillars and walls
                map_x = int(next_x / TILE_SIZE)
                map_y = int(next_y / TILE_SIZE)

                if map_y < 0 or map_y >= len(game_map) or map_x < 0 or map_x >= len(game_map[0]):
                    self.state = 'ROAMING'
                    self.timer = random.uniform(1, 2)
                elif game_map[map_y][map_x] == 'P':
                    self.state = 'STUNNED'
                    self.timer = PYTHON_STUN_DURATION
                elif game_map[map_y][map_x] == 'W':
                    self.state = 'ROAMING'
                    self.timer = random.uniform(1, 2)
                else:
                    self.segments[0]['x'] = next_x
                    self.segments[0]['y'] = next_y

        elif self.state == 'STUNNED':
            if self.timer <= 0:
                self.state = 'ROAMING'
                self.timer = random.uniform(1, 2)

        elif self.state == 'RETREATING':
            if self.timer <= 0:
                self.state = 'ROAMING'
                self.timer = random.uniform(1, 2)
            # Move away from player
            retreat_speed = self.speed * PYTHON_RETREAT_SPEED_MULTIPLIER
            next_x = self.segments[0]['x'] + math.cos(self.angle) * retreat_speed * dt
            next_y = self.segments[0]['y'] + math.sin(self.angle) * retreat_speed * dt
            map_x = int(next_x / TILE_SIZE)
            map_y = int(next_y / TILE_SIZE)
            if (map_y < 0 or map_y >= len(game_map) or map_x < 0 or map_x >= len(game_map[0])) or game_map[map_y][map_x] == 'W':
                self.state = 'ROAMING'
                self.timer = random.uniform(1, 2)
            else:
                self.segments[0]['x'] = next_x
                self.segments[0]['y'] = next_y

        # Update body segments to follow the head
        for i in range(1, len(self.segments)):
            leader = self.segments[i-1]
            follower = self.segments[i]
            dx = leader['x'] - follower['x']
            dy = leader['y'] - follower['y']
            distance = math.hypot(dx, dy)
            if distance > TILE_SIZE / 2:
                angle = math.atan2(dy, dx)
                follower['x'] += math.cos(angle) * self.speed * dt
                follower['y'] += math.sin(angle) * self.speed * dt

    def take_damage(self, amount):
        # Only process damage if boss is alive
        if not self.is_alive:
            return False
            
        # Calculate new health, ensuring it doesn't go below 0
        new_health = max(0, self.health - amount)
        
        # Check if this damage will kill the boss
        will_die = new_health <= 0
        
        # Update health
        self.health = new_health
        
        # Handle death if needed
        if will_die and self.is_alive:
            self.health = 0
            self.is_alive = False
            self.death_scene_triggered = True
            # Stop any ongoing actions
            self.state = 'DEFEATED'
            # Clear any active effects
            self.poison_trail = []
            self.dust_effects = []
            return True  # Return True if this damage killed the boss
            
        return False  # Return False if boss is still alive
            
    def draw(self, screen):
        if not self.is_alive:
            return

        # Draw poison trail
        for p in self.poison_trail:
            surf = pygame.Surface((TILE_SIZE*1.1, TILE_SIZE*1.1), pygame.SRCALPHA)
            pygame.draw.circle(surf, POISON_TRAIL_COLOR,
                (int(TILE_SIZE*1.1/2), int(TILE_SIZE*1.1/2)), int(TILE_SIZE*0.55))
            alpha = max(20, int(180 * (p['timer'] / self.max_trail_duration)))
            surf.set_alpha(alpha)
            screen.blit(surf, (p['x']-TILE_SIZE*0.55, p['y']-TILE_SIZE*0.55))

        # Draw dust effects
        for d in self.dust_effects:
            surf = pygame.Surface((TILE_SIZE*1.3, TILE_SIZE*1.3), pygame.SRCALPHA)
            pygame.draw.circle(surf, DUST_COLOR, (int(TILE_SIZE*0.65),int(TILE_SIZE*0.65)), int(TILE_SIZE*0.65))
            alpha = int(255 * (d['timer'] / self.max_dust_duration))
            surf.set_alpha(alpha)
            screen.blit(surf, (d['x']-TILE_SIZE*0.65,d['y']-TILE_SIZE*0.65))

        if self.state == 'TELEGRAPHING':
            telegraph_surface = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
            pygame.draw.circle(telegraph_surface, PYTHON_TELEGRAPH_COLOR, (TILE_SIZE, TILE_SIZE), TILE_SIZE)
            screen.blit(telegraph_surface, (self.telegraph_pos[0] - TILE_SIZE, self.telegraph_pos[1] - TILE_SIZE))

        if self.state == 'TELEGRAPHING_CHARGE':
            line_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            end_x = self.segments[0]['x'] + math.cos(self.angle) * SCREEN_WIDTH
            end_y = self.segments[0]['y'] + math.sin(self.angle) * SCREEN_HEIGHT
            pygame.draw.line(line_surface, PYTHON_CHARGE_COLOR,
                             (self.segments[0]['x'], self.segments[0]['y']), (end_x, end_y), 30)
            screen.blit(line_surface, (0, 0))

        if self.state in ['EMERGING', 'ATTACKING', 'ROAMING', 'TELEGRAPHING_CHARGE', 'CHARGING', 'STUNNED', 'RETREATING']:
            # Draw shadow under each segment for depth
            for i in range(len(self.segments)):
                seg = self.segments[i]
                shadow_surf = pygame.Surface((TILE_SIZE, TILE_SIZE//2), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, PYTHON_SHADOW_COLOR, (0, 0, TILE_SIZE, TILE_SIZE//2))
                # Lower the shadow a bit under the segment
                screen.blit(shadow_surf, (seg['x']-TILE_SIZE//2, seg['y']-TILE_SIZE//4 + TILE_SIZE//2))

            # Draw body with stripes effect
            for i in range(len(self.segments) - 1, 0, -1):
                seg = self.segments[i]
                color = PYTHON_STRIPE_COLOR if (i % 2 == 0) else PYTHON_BODY_COLOR
                pygame.draw.circle(screen, color, (int(seg['x']), int(seg['y'])), TILE_SIZE // 3)

            # Draw head (flashing red if enraged and not stunned)
            head_x = int(self.segments[0]['x'])
            head_y = int(self.segments[0]['y'])

            head_color = PYTHON_HEAD_COLOR
            anim_flash = False
            if self.is_enraged and self.state != 'STUNNED':
                anim_flash = (pygame.time.get_ticks() // 120) % 2 == 0
                if anim_flash:
                    head_color = PYTHON_ENRAGED_HEAD_COLOR
            if self.state == 'STUNNED':
                head_color = (220, 180, 20)  # strong yellow-stun color

            pygame.draw.circle(screen, head_color, (head_x, head_y), TILE_SIZE // 2)

            # Draw Eyes (bigger/brighter when stunned/enraged)
            if self.state == 'STUNNED':
                eye_color = PYTHON_STUN_EYE_COLOR
                eye_radius = 8
                glow_surf = pygame.Surface((24,24), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, PYTHON_STUN_EYE_COLOR, (12,12), 12)
                glow_surf.set_alpha(120)
            elif self.is_enraged:
                eye_color = (255,32,32)
                eye_radius = 7
                glow_surf = pygame.Surface((22,22), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255,42,42), (11,11), 11)
                glow_surf.set_alpha(110)
            else:
                eye_color = PYTHON_EYE_COLOR
                eye_radius = 4
                glow_surf = None

            # Eyes offset from head (same as before)
            offset1_x = math.cos(self.angle + math.pi/4) * 10
            offset1_y = math.sin(self.angle + math.pi/4) * 10
            offset2_x = math.cos(self.angle - math.pi/4) * 10
            offset2_y = math.sin(self.angle - math.pi/4) * 10

            if glow_surf:
                screen.blit(glow_surf, (head_x+offset1_x-12, head_y+offset1_y-12))
                screen.blit(glow_surf, (head_x+offset2_x-12, head_y+offset2_y-12))
            pygame.draw.circle(screen, eye_color, (int(head_x+offset1_x), int(head_y+offset1_y)), eye_radius)
            pygame.draw.circle(screen, eye_color, (int(head_x+offset2_x), int(head_y+offset2_y)), eye_radius)

    def trigger_retreat(self, player_x, player_y):
        self.state = 'RETREATING'
        self.timer = PYTHON_RETREAT_DURATION
        # Calculate angle away from player and set that as the current angle
        angle_to_player = math.atan2(player_y - self.segments[0]['y'], player_x - self.segments[0]['x'])
        self.angle = angle_to_player + math.pi 