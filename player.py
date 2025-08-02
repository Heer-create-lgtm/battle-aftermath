import pygame
import math
import random

# Initialize mixer with more channels for simultaneous sounds
pygame.mixer.init(frequency=44100, size=-16, channels=8)  # Increased channels from default 2 to 8

# Load sounds (safe load)
try:
    hurt_sound = pygame.mixer.Sound("assets/music/player_hurt.ogg")
    hurt_sound.set_volume(0.7)  # Adjust volume as needed
except Exception:
    hurt_sound = None
try:
    shield_hit_sound = pygame.mixer.Sound("assets/music/shield_hit.ogg")
    shield_hit_sound.set_volume(0.7)  # Adjust volume as needed
except Exception:
    shield_hit_sound = None
from settings import (
    PLAYER_START_X, PLAYER_START_Y, PLAYER_START_ANGLE, PLAYER_SPEED,
    PLAYER_SPRINT_SPEED, PLAYER_ROT_SPEED, MAX_HEALTH, MAX_STAMINA,
    PLAYER_RADIUS, PLAYER_MAX_AMMO, PLAYER_MAX_SHIELD_ENERGY, PLAYER_IMAGE_SIZE,
    PLAYER_RELOAD_TIME, PLAYER_SHIELD_DEPLETION_RATE, PLAYER_SHIELD_REGEN_RATE, PLAYER_BULLET_DAMAGE,
    STAMINA_DEPLETION_RATE, STAMINA_SPRINT_PENALTY_DURATION, STAMINA_REGEN_RATE,
    TILE_SIZE, PLAYER_INVINCIBILITY_DURATION, HERO_BLOOD_COLOR
)

class Player:
    def __init__(self):
        from settings import SHOTGUN_PELLETS, SHOTGUN_SPREAD_DEGREES
        self.shotgun_pellets = SHOTGUN_PELLETS
        self.shotgun_spread = math.radians(SHOTGUN_SPREAD_DEGREES)
        # Minimum delay between shotgun shots (seconds)
        self.shotgun_cooldown_time = 0.6  # Doom-like fire rate
        self.shotgun_cooldown = 0
        self.x = PLAYER_START_X
        self.y = PLAYER_START_Y
        self.angle = PLAYER_START_ANGLE
        self.base_speed = PLAYER_SPEED
        self.speed = self.base_speed
        self.zombie_blood_collected = 0  # Track zombie blood collected
        self.base_sprint_speed = PLAYER_SPRINT_SPEED
        self.sprint_speed = self.base_sprint_speed
        self.rot_speed = PLAYER_ROT_SPEED
        # Calm Fury mode
        self.calm_fury_active = False
        self.base_bullet_damage = PLAYER_BULLET_DAMAGE
        self.current_bullet_damage = PLAYER_BULLET_DAMAGE
        self.health = MAX_HEALTH
        self.max_health = MAX_HEALTH
        self.stamina = MAX_STAMINA
        self.max_stamina = MAX_STAMINA
        self.shield_energy = PLAYER_MAX_SHIELD_ENERGY
        self.max_shield_energy = PLAYER_MAX_SHIELD_ENERGY
        self.ammo = PLAYER_MAX_AMMO
        self.sprint_allowed = True
        self.is_shielding = False
        self.radius = PLAYER_RADIUS
        self.is_reloading = False
        self.reload_timer = 0
        self.is_invincible = False
        self.invincibility_timer = 0
        self.sprint_penalty_timer = 0

        # Shield throw (boomerang) ability state
        self.active_shield_throw = False  # True while a thrown shield is airborne
        self.shield_cooldown = 0  # seconds remaining
        self.trail_points = []  # stores past positions for trail
        import os
        try:
            img_path = os.path.join(os.path.dirname(__file__), 'assets', 'sprites', 'shield.png')
            shield_img = pygame.image.load(img_path).convert_alpha()
            from settings import SHIELD_IMAGE_SIZE
            self.shield_image = pygame.transform.scale(shield_img, (SHIELD_IMAGE_SIZE, SHIELD_IMAGE_SIZE))
        except Exception as e:
            print(f"[Shield] Failed to load shield image: {e}")
            self.shield_image = None

        # Sound FX
        try:
            self.shotgun_sound = pygame.mixer.Sound("assets/music/shotgun.ogg")
            self.shotgun_sound.set_volume(0.9)  # Louder for impact
        except pygame.error as e:
            print(f"Warning: Could not load shotgun sound. Error: {e}")
            self.shotgun_sound = None
        try:
            self.reload_sound = pygame.mixer.Sound("assets/music/reload.ogg")
            self.reload_sound.set_volume(0.6)  # Slightly quieter
        except pygame.error as e:
            print(f"Warning: Could not load reload sound. Error: {e}")
            self.reload_sound = None

        # Chainsaw sound for shield throw
        try:
            self.chainsaw_sound = pygame.mixer.Sound("assets/music/chainsaw.ogg")
            self.chainsaw_sound.set_volume(0.8)
        except pygame.error as e:
            print(f"Warning: Could not load chainsaw sound. Error: {e}")
            self.chainsaw_sound = None

        # Blood splatters (for visual effects when player is hit)
        self.blood_splatters = []   # Each is {'x', 'y', 'r', 'timer'}

        try:
            self.original_image = pygame.image.load('assets/sprites/hero.png').convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (PLAYER_IMAGE_SIZE, PLAYER_IMAGE_SIZE))
        except pygame.error as e:
            print(f"Warning: Could not load player image. Error: {e}")
            self.original_image = None

        # Ground Pound attributes
        self.gp_cooldown = 0
        self.gp_charging = False
        self.gp_charge = 0.0
        self.gp_triggered = False
        self.gp_msg_timer = 0.0
        self.gp_disabled = False

    def reset(self):
        self.health = MAX_HEALTH
        self.stamina = MAX_STAMINA
        self.shield_energy = PLAYER_MAX_SHIELD_ENERGY
        self.ammo = PLAYER_MAX_AMMO
        self.zombie_blood_collected = 0
        self.sprint_penalty_timer = 0
        self.is_reloading = False
        self.reload_timer = 0
        self.is_invincible = False
        self.invincibility_timer = 0

    def decrease_power(self):
        print("You feel your power draining...")
        self.health *= 0.75
        self.stamina *= 0.75
        self.speed *= 0.75
        self.sprint_speed *= 0.75

    def shoot(self):
        """Fire the shotgun. Returns a list of pellet dictionaries or None if unable."""
        from settings import SHOTGUN_PELLETS, SHOTGUN_SPREAD_DEGREES, SHOTGUN_PELLET_DAMAGE, BULLET_SPEED
        if self.shotgun_cooldown > 0:
            return None
        if self.ammo > 0 and not self.is_reloading:
            self.ammo -= 1
            self.shotgun_cooldown = self.shotgun_cooldown_time
            # Play sound
            if self.shotgun_sound:
                try:
                    channel = pygame.mixer.find_channel(True)
                    if channel:
                        channel.play(self.shotgun_sound)
                    else:
                        self.shotgun_sound.stop(); self.shotgun_sound.play()
                except Exception:
                    pass
            pellets = []
            spread_rad = math.radians(SHOTGUN_SPREAD_DEGREES)
            for _ in range(SHOTGUN_PELLETS):
                offset = random.uniform(-spread_rad, spread_rad)
                pellets.append({
                    'x': self.x,
                    'y': self.y,
                    'angle': self.angle + offset,
                    'damage': SHOTGUN_PELLET_DAMAGE,
                    'speed': BULLET_SPEED,
                    'sprite': 'pellet',
                })
            return pellets
        elif self.ammo == 0 and not self.is_reloading:
            self.start_reload()
        return None
        if self.ammo > 0 and not self.is_reloading:
            self.ammo -= 1
            if self.shotgun_sound:
                try:
                    # Find an available channel to play the sound
                    channel = pygame.mixer.find_channel(True)  # Force find a channel
                    if channel:
                        channel.play(self.shotgun_sound)
                    else:
                        # If no channel is available, play and stop any existing sound
                        self.shotgun_sound.stop()
                        self.shotgun_sound.play()
                except Exception as e:
                    print(f"Error playing shotgun sound: {e}")
            # Return bullet properties including damage
            return {'x': self.x, 'y': self.y, 'angle': self.angle, 'damage': self.current_bullet_damage}
        elif self.ammo == 0 and not self.is_reloading:
            self.start_reload()
        return None

    def start_reload(self):
        if not self.is_reloading and self.ammo < PLAYER_MAX_AMMO:
            self.is_reloading = True
            self.reload_timer = PLAYER_RELOAD_TIME
            if self.reload_sound:
                self.reload_sound.play()

    def finish_reload(self):
        self.is_reloading = False
        self.ammo = PLAYER_MAX_AMMO

    # ---------------- Shield Throw Ability -----------------
    def throw_shield(self):
        """Launch the shield as a boomerang projectile. Returns dict or None if already active."""
        if self.active_shield_throw or self.is_reloading:
            return None
        from settings import SHIELD_SPEED, SHIELD_MAX_DISTANCE, SHIELD_DAMAGE
        # Mark shield as active
        self.active_shield_throw = True

        # Play chainsaw sound effect on shield throw
        if hasattr(self, 'chainsaw_sound') and self.chainsaw_sound:
            try:
                channel = pygame.mixer.find_channel(True)
                if channel:
                    channel.play(self.chainsaw_sound)
                else:
                    # Fallback – stop and replay on existing channel
                    self.chainsaw_sound.stop()
                    self.chainsaw_sound.play()
            except Exception as e:
                print(f"Error playing chainsaw sound: {e}")
        return {
            'type': 'shield',
            'x': self.x,
            'y': self.y,
            'start_x': self.x,
            'start_y': self.y,
            'angle': self.angle,
            'speed': SHIELD_SPEED,
            'radius': self.radius + 6,
            'damage': SHIELD_DAMAGE,
            'boomerang': True,
            'returning': False,
            'max_distance': SHIELD_MAX_DISTANCE,
            'owner': self,
            'trail': [],
            'bounces': 0
        }

        self.is_reloading = False
        self.ammo = PLAYER_MAX_AMMO

    def toggle_shield(self, activate):
        """Toggle shield on/off. Returns True if state changed, False otherwise."""
        if activate and not self.is_shielding and self.shield_energy > 0 and not self.is_reloading:
            self.is_shielding = True
            return True
        elif not activate and self.is_shielding:
            self.is_shielding = False

    def handle_input_and_movement(self, keys, game_map, is_throne_room, dt):
        # Reloading - can't reload while shielding
        if keys[pygame.K_r] and not is_throne_room and not self.is_shielding and not self.is_reloading:
            self.start_reload()

        # Determine player state for movement (arrow keys or W/S)
        is_trying_to_move = keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_w] or keys[pygame.K_s]
        is_sprinting = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.stamina > 0 and not is_throne_room and self.sprint_penalty_timer <= 0
        
        current_speed = 0
        if is_trying_to_move:
            if is_sprinting:
                current_speed = self.sprint_speed
                self.stamina -= STAMINA_DEPLETION_RATE * dt
                if self.stamina <= 0:
                    self.stamina = 0
                    self.sprint_penalty_timer = STAMINA_SPRINT_PENALTY_DURATION # Penalize
            else:
                current_speed = self.speed
        
        # Regenerate stamina only when Shift is NOT held
        if not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.stamina < MAX_STAMINA:
            self.stamina += STAMINA_REGEN_RATE * dt
            if self.stamina > MAX_STAMINA:
                self.stamina = MAX_STAMINA

        # Movement with slide-based collision
        if keys[pygame.K_UP]:
            self.move_with_collision(current_speed * dt, game_map)
        if keys[pygame.K_DOWN]:
            self.move_with_collision(-current_speed * dt, game_map)

    def move_with_collision(self, speed, game_map):
        dx = math.cos(self.angle) * speed
        dy = math.sin(self.angle) * speed

        # Check y movement
        new_y = self.y + dy
        if 0 <= new_y < len(game_map) * TILE_SIZE:
            target_row = int(new_y / TILE_SIZE)
            col = int(self.x / TILE_SIZE)
            if game_map[target_row][col] not in ['W', 'P']:
                self.y += dy
        # Check x movement
        new_x = self.x + dx
        if 0 <= new_x < len(game_map[0]) * TILE_SIZE:
            target_col = int(new_x / TILE_SIZE)
            row = int(self.y / TILE_SIZE)
            if game_map[row][target_col] not in ['W', 'P']:
                self.x += dx

    def take_damage(self, amount):
        if self.is_invincible:
            return
        if self.is_shielding:
            if shield_hit_sound:
                shield_hit_sound.play()
            self.shield_energy -= amount * 2  # Shield takes more damage
            if self.shield_energy < 0:
                self.health += self.shield_energy  # Overflow damage
                self.shield_energy = 0
        else:
            if hurt_sound:
                hurt_sound.play()
            self.health -= amount
        if self.health <= 0:
            self.health = 0
            # Player death is handled in the main game loop

    def draw(self, screen):
        # Draw hero blood splatters first
        for splat in self.blood_splatters[:]:
            blood_surf = pygame.Surface((splat['r']*2, splat['r']*2), pygame.SRCALPHA)
            color = HERO_BLOOD_COLOR[:3] + (int(HERO_BLOOD_COLOR[3] * (splat['timer']/0.5)),)
            pygame.draw.circle(blood_surf, color, (splat['r'], splat['r']), splat['r'])
            screen.blit(blood_surf, (splat['x']-splat['r'], splat['y']-splat['r']))
            
            # Update and remove old splatters
            splat['timer'] -= 0.02
            if splat['timer'] <= 0:
                self.blood_splatters.remove(splat)

        # Draw player image if it exists
        if self.original_image:
            # The angle needs to be converted to degrees and inverted for pygame's rotation system
            rotated_image = pygame.transform.rotate(self.original_image, -math.degrees(self.angle))
            rotated_rect = rotated_image.get_rect(center=(self.x, self.y))
            screen.blit(rotated_image, rotated_rect)
            
            # Draw shield icon when active
            if self.is_shielding:
                shield_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(shield_icon, (0, 100, 255, 200), (15, 15), 12, 2)
                pygame.draw.polygon(shield_icon, (0, 150, 255, 200), [(15, 8), (20, 15), (15, 22), (10, 15)])
                screen.blit(shield_icon, (self.x - 15, self.y - 40))
        else:
            # Fallback to drawing a circle if image failed to load
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)

        # Draw shield effect
        if self.is_shielding:
            # Pulsing shield effect
            shield_alpha = 100 + int(50 * math.sin(pygame.time.get_ticks() * 0.01))
            shield_surface = pygame.Surface((self.radius * 2.5, self.radius * 2.5), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (0, 191, 255, shield_alpha), 
                             (int(self.radius * 1.25), int(self.radius * 1.25)), 
                             int(self.radius * 1.25), 3)
            screen.blit(shield_surface, (self.x - self.radius * 1.25, self.y - self.radius * 1.25))
            
            # Shield energy indicator
            energy_ratio = self.shield_energy / PLAYER_MAX_SHIELD_ENERGY
            bar_width = 40
            bar_height = 4
            pygame.draw.rect(screen, (0, 0, 0, 200), 
                           (self.x - bar_width//2, self.y + self.radius + 5, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 200, 255, 200), 
                           (self.x - bar_width//2, self.y + self.radius + 5, 
                            int(bar_width * energy_ratio), bar_height))

        # Draw invincibility flash or low shield warning
        if self.is_invincible:
            # Flash white every 100ms during invincibility
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                flash_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surface, (255, 255, 255, 100), 
                                 (self.radius, self.radius), self.radius)
                screen.blit(flash_surface, (self.x - self.radius, self.y - self.radius))
        elif self.is_shielding and self.shield_energy < PLAYER_MAX_SHIELD_ENERGY * 0.3:
            # Flash red when shield is low
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                warning_surface = pygame.Surface((self.radius * 2.2, self.radius * 2.2), pygame.SRCALPHA)
                pygame.draw.circle(warning_surface, (255, 100, 100, 80), 
                                 (int(self.radius * 1.1), int(self.radius * 1.1)), 
                                 int(self.radius * 1.1))
                screen.blit(warning_surface, (self.x - self.radius * 1.1, self.y - self.radius * 1.1)) 