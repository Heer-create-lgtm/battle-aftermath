import pygame, math, random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, WHITE, MAX_HEALTH, BULLET_COLOR, BULLET_RADIUS
from ui import draw_ui
from levels.dialogue import show_dialogue

from player import Player, shield_hit_sound
from zombie import Zombie
from special_zombies import random_zombie
from shield_bullet import update_shield_bullet, draw_shield_bullet

# ------------------------------------------------------------
#  Kratos Boss – multi-phase encounter following God-of-War vibe
# ------------------------------------------------------------

class KratosBoss:
    """Corrupted War God 3 phases with distinct behaviour.
    Phase 1  (>=50% HP) : Spartan Discipline (melee focus)
    Phase 2  (>=20% HP) : Spartan Rage      (rage buff)
    Phase 3  (<20%  HP) : Full Arsenal      (all weapons + ultimate)
    Shield: While any minion is alive, Kratos projects an invulnerable
             shield (light-blue semi-transparent ring). He can still
             attack the player.
    """

    def __init__(self, x: float, y: float):
        self.x, self.y = x, y
        self.radius = 80
        self.health = 1500
        self.max_health = 1500
        try:
            img = pygame.image.load('assets/sprites/corrupted_god.png').convert_alpha()
            self.image = pygame.transform.scale(img, (self.radius*2, self.radius*2))
        except Exception:
            self.image = None
        # Timers / state trackers
        self.last_attack = 0          # global attack cooldown (milliseconds)
        self.state = "idle"           # can be 'idle', 'rush', 'combo', etc.
        self.state_end = 0            # timestamp when current state ends
        self._combo_step = 0
        self._spin_last_emit = 0
        self._bash_cooldown = 0
        self._rage_end = 0           # rage duration timer (phase2)
        self._ultimate_used = False  # only once in phase3
        # Minion spawn timer
        self._next_zombie_time = 0
        # Projectile speed baseline
        self.projectile_speed = 300
        # Shield flag (set externally each frame by arena loop)
        self.shield_active = False

    # ---------------------- Utility helpers -------------------
    def _emit_weapon_arc(self, actions, weapon_type, count, speed_mul=1.0, damage=6):
        """Emit radial arc of projectiles around Kratos"""
        for i in range(count):
            ang = i * (2*math.pi / count)
            actions.append({
                'type': weapon_type,
                'x': self.x, 'y': self.y,
                'angle': ang,
                'speed': self.projectile_speed * speed_mul,
                'radius': 9,
                'damage': damage,
                'color': (255, 120, 0)
            })

    # --------------------------- Main AI ----------------------
    def update(self, player, current_time: int, dt: float):
        actions = []

        # Calculate current health percentage early for consistent reference
        hp_pct = self.health / self.max_health

        # --- Periodic zombie summoning independent of attack pattern ---
        if current_time >= self._next_zombie_time:
            spawn_count = 4 if hp_pct > 0.5 else 6 if hp_pct > 0.2 else 8
            actions.append({'type': 'spawn_zombie', 'count': spawn_count})
            interval = (
                random.randint(4000, 7000) if hp_pct > 0.5 else
                random.randint(3000, 5500) if hp_pct > 0.2 else
                random.randint(2500, 4500)
            )
            self._next_zombie_time = current_time + interval

        phase = 1 if hp_pct > 0.5 else 2 if hp_pct > 0.2 else 3

        # Handle current active states first (rush, combo, etc.)
        if self.state == 'rush':
            # Shoulder charge movement
            self.x += self._rush_vec[0] * dt
            self.y += self._rush_vec[1] * dt
            if current_time >= self.state_end:
                self.state = 'idle'
        elif self.state == 'slam':
            if current_time >= self.state_end:
                self.state = 'idle'
        # Phase transition handling
        if phase == 2 and self._rage_end == 0:
            # Enter Rage – buff for 15s
            self._rage_end = current_time + 15000
            self.last_attack = current_time  # brief pause then faster attacks
            show_dialogue(["Kratos roars in rage! His power surges…"])
        if self._rage_end and current_time > self._rage_end:
            self._rage_end = 0  # rage expired

        # -------- choose attack if idle & off cooldown ------------
        atk_delay = 800 if phase == 1 else 600 if phase == 2 else 500  # ms
        if current_time - self.last_attack > atk_delay and self.state == 'idle':
            self.last_attack = current_time
            roll = random.random()
            # ------------------ PHASE 1 ------------------
            if phase == 1:
                if roll < 0.4:  # Blades of Chaos 3-hit combo
                    base = math.atan2(player.y - self.y, player.x - self.x)
                    for step, offset in enumerate((-0.5, 0, 0.5)):
                        actions.append({'type': 'blade', 'x': self.x, 'y': self.y,
                                        'angle': base + offset,
                                        'speed': self.projectile_speed,
                                        'radius': 9, 'damage': 6,
                                        'color': (255, 100, 0)})
                elif roll < 0.65:  # Shield Bash counter window
                    if current_time - self._bash_cooldown > 2000:
                        self._bash_cooldown = current_time
                        actions.append({'type': 'bash', 'x': self.x, 'y': self.y,
                                         'radius': 60, 'damage': 8})
                else:  # Leviathan Axe throw (boomerang)
                    base = math.atan2(player.y - self.y, player.x - self.x)
                    actions.append({'type': 'axe', 'x': self.x, 'y': self.y,
                                    'angle': base, 'speed': self.projectile_speed,
                                    'radius': 12, 'damage': 8,
                                    'color': (200, 200, 255), 'boomerang': True})
            # ------------------ PHASE 2 ------------------
            elif phase == 2:
                if roll < 0.3:  # Ground Slam shockwaves
                    self._emit_weapon_arc(actions, 'shock', 12, 0.9)
                elif roll < 0.6:  # Spartan Rush
                    # Calculate dash vector
                    dx, dy = player.x - self.x, player.y - self.y
                    dist = max(1, math.hypot(dx, dy))
                    speed = 700
                    self._rush_vec = (dx/dist * speed, dy/dist * speed)
                    dash_time = dist / speed
                    self.state = 'rush'
                    self.state_end = current_time + int(dash_time*1000) + 400
                else:  # Faster blade combo
                    self._emit_weapon_arc(actions, 'blade', 5, 1.2)
            # ------------------ PHASE 3 ------------------
            else:
                if not self._ultimate_used and hp_pct < 0.2:
                    # Wrath of Olympus – one-time screen-wide lightning
                    for x in range(80, SCREEN_WIDTH, 120):
                        actions.append({'type': 'lightning', 'x': x, 'y': 0,
                                        'angle': math.pi/2, 'speed': 0,
                                        'radius': 14, 'damage': 10,
                                        'color': (230, 230, 255)})
                    self._ultimate_used = True
                if roll < 0.5:
                    # Weapon switch combo: choose random weapon
                    weapon = random.choice(['blade', 'axe', 'fist'])
                    count = 8 if weapon != 'fist' else 12
                    self._emit_weapon_arc(actions, weapon, count, 1.2)
                else:
                    # Rage rush again but quicker
                    dx, dy = player.x - self.x, player.y - self.y
                    dist = max(1, math.hypot(dx, dy))
                    speed = 800
                    self._rush_vec = (dx/dist * speed, dy/dist * speed)
                    self.state = 'rush'
                    self.state_end = current_time + int(dist/speed*1000) + 300

        # Ensure Kratos never leaves the visible arena bounds
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

        return actions

    # -------------------------- Damage & Draw ------------------
    def take_damage(self, d):
        if self.shield_active:
            return False  # invulnerable while shield up
        self.health -= d
        return self.health <= 0

    def draw(self, screen):
        # Shield visual
        if self.shield_active:
            shield = pygame.Surface((self.radius*2+20, self.radius*2+20), pygame.SRCALPHA)
            pygame.draw.circle(shield, (150, 200, 255, 120), (self.radius+10, self.radius+10), self.radius+10)
            screen.blit(shield, (self.x - self.radius - 10, self.y - self.radius - 10))
        # Boss sprite / placeholder circle
        if self.image:
            screen.blit(self.image, (self.x - self.radius, self.y - self.radius))
        else:
            pygame.draw.circle(screen, (220, 40, 40), (int(self.x), int(self.y)), self.radius)
        # Health bar
        bar = 160
        pygame.draw.rect(screen, (100, 0, 0), (self.x - bar//2, self.y - self.radius - 25, bar, 10))
        pygame.draw.rect(screen, (0, 200, 0), (self.x - bar//2, self.y - self.radius - 25, bar * (self.health / self.max_health), 10))

# ------------------------------------------------------------
#                 Level Runner – Divine Arena
# ------------------------------------------------------------

def show_ending():
    """Show the ending sequence with image and dialogue."""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    try:
        # Load and scale the ending image to fit the screen
        ending_img = pygame.image.load('assets/sprites/ending.png').convert_alpha()
        img_rect = ending_img.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        # Create a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 0))  # Start transparent
        
        # Fade in variables
        fade_alpha = 0
        fade_speed = 2
        text_alpha = 0
        text_delay = 120  # frames before text starts appearing
        current_delay = 0
        
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT or e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                    running = False
            
            # Fade in image
            if fade_alpha < 200:  # Slightly transparent
                fade_alpha = min(fade_alpha + fade_speed, 200)
                overlay.fill((0, 0, 0, 255 - fade_alpha))
            
            # Update text alpha after delay
            if fade_alpha >= 200:
                current_delay += 1
                if current_delay >= text_delay:
                    text_alpha = min(text_alpha + 2, 255)
            
            # Draw everything
            screen.fill((0, 0, 0))
            screen.blit(ending_img, img_rect)
            screen.blit(overlay, (0, 0))
            
            # Draw dialogue text
            if text_alpha > 0:
                font = pygame.font.Font(None, 36)
                text1 = font.render("Mama... who was he?", True, (255, 255, 255))
                text2 = font.render("Someone the gods couldn't control.", True, (255, 255, 255))
                
                # Center text at bottom of screen
                text1_rect = text1.get_rect(centerx=SCREEN_WIDTH//2, bottom=SCREEN_HEIGHT-60)
                text2_rect = text2.get_rect(centerx=SCREEN_WIDTH//2, bottom=SCREEN_HEIGHT-20)
                
                # Apply fade
                text1.set_alpha(text_alpha)
                text2.set_alpha(max(0, text_alpha - 60))  # Slight delay for second line
                
                screen.blit(text1, text1_rect)
                screen.blit(text2, text2_rect)
            
            pygame.display.flip()
            
            # Auto-advance after text is fully shown
            if text_alpha >= 255 and current_delay > text_delay + 180:  # 3 second delay
                running = False
        from main import show_game_over_screen  # local to avoid circular dependency
        show_game_over_screen()
    
    except Exception as e:
        print(f"Error loading ending image: {e}")
        show_dialogue([
            "The corrupted War God falls, his power siphoned into your soul…",
            "You have become something beyond the gods' control.",
            "The people remember you as their savior."
        ])

def run_divine_arena():
    """Level 4 – Divine Arena boss fight against Kratos."""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()

    # --- Audio: play arena BGM ---
    try:
        pygame.mixer.music.load('assets/music/bgm.ogg')
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
    except Exception:
        pass  # fallback silently if file missing

    # ---------------- Collectibles (medkits) -----------------
    COLLECTIBLE_SIZE = 20
    collectibles = []
    try:
        med_img_raw = pygame.image.load('assets/sprites/medkit.png').convert_alpha()
        med_img = pygame.transform.scale(med_img_raw, (COLLECTIBLE_SIZE, COLLECTIBLE_SIZE))
    except Exception:
        # Fallback: simple red square with white border
        med_img = pygame.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE))
        med_img.fill((200, 0, 0))
        pygame.draw.rect(med_img, (255, 255, 255), med_img.get_rect(), 2)

    def spawn_medkit(mx, my):
        """Spawn a medkit at given coords if player's HP <=20%."""
        if player.health <= player.max_health * 0.2:
            collectibles.append({'x': mx, 'y': my, 'image': med_img})

    player = Player()
    player.x, player.y = SCREEN_WIDTH//2, SCREEN_HEIGHT-120
    player.is_invincible = True  # spawn invuln
    invul_end = pygame.time.get_ticks() + 2000

    boss = KratosBoss(SCREEN_WIDTH//2, SCREEN_HEIGHT//3)
    bullets = []
    player_bullets = []
    zombies = []

    show_dialogue([
        "The arena quakes as the Corrupted War God descends…",
        "Kratos: 'Spartan discipline shall crush you!'"
    ])

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        t = pygame.time.get_ticks()
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return "MAIN_MENU"
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "MAIN_MENU"

        # ---------------- Player movement & shooting ----------------
        keys = pygame.key.get_pressed()
        from mechanics import update_player_state, handle_player_input
        if 'arena_map' not in locals():
            arena_map = [[' ' for _ in range(SCREEN_WIDTH // TILE_SIZE + 1)] for _ in range(SCREEN_HEIGHT // TILE_SIZE + 1)]
        update_player_state(player, keys, arena_map, dt)
        handle_player_input(player, player_bullets, events)

        # ---------------- Update existing zombies -------------------
        from special_zombies import random_zombie
        boss.shield_active = any(z.is_alive for z in zombies)

        # ---------------- Wave spawning logic -------------------
        if not hasattr(run_divine_arena, '_wave_cleared'):
            run_divine_arena._wave_cleared = True
        if not hasattr(run_divine_arena, '_next_wave'):
            run_divine_arena._next_wave = t + 3000  # first wave after 3s

        # If no zombies left and cooldown passed, spawn next wave
        if run_divine_arena._wave_cleared and not zombies and t >= run_divine_arena._next_wave:
            wave_size = 10
            for _ in range(wave_size):
                zx = random.randint(60, SCREEN_WIDTH-60)
                zy = random.randint(60, SCREEN_HEIGHT-160)
                zombies.append(random_zombie(zx, zy))
            run_divine_arena._wave_cleared = False
            # Shield becomes active automatically via shield_active update above
        # Mark wave cleared when last zombie dies
        if not zombies and not run_divine_arena._wave_cleared:
            run_divine_arena._wave_cleared = True
            # Next wave after delay depending on boss health (faster when low HP)
            delay = 5000 if boss.health > boss.max_health*0.5 else 4000 if boss.health > boss.max_health*0.2 else 3000
            run_divine_arena._next_wave = t + delay
        for z in zombies[:]:
            z_info = z.update(player.x, player.y, arena_map, dt)
            if isinstance(z_info, dict):
                bullets.append(z_info)
            if z.is_alive and math.hypot(player.x - z.x, player.y - z.y) < z.radius + player.radius:
                if not player.is_invincible:
                    player.take_damage(1)  # Use player method to apply shield logic and play sound
                if player.health <= 0:
                    return "GAME_OVER"
            if not z.is_alive:
                # Spawn medkit if hero is in critical HP (<20%)
                spawn_medkit(z.x, z.y)
                zombies.remove(z)

        # ---------------- Boss update ------------------------------
        act = boss.update(player, t, dt)
        if act:
            def process(a):
                if a.get('type') == 'bash':
                    if math.hypot(player.x - a['x'], player.y - a['y']) < a.get('radius', 50) + player.radius:
                        player.take_damage(6)  # Use player method to apply shield logic and play sound
                    return False
                # Ignore boss-triggered zombie spawns; waves handled separately
                if a.get('type') in ('spawn_zombie', 'spawn_minion'):
                    return False
                return True
            if isinstance(act, list):
                for a in act:
                    if process(a):
                        bullets.append(a)
            else:
                if process(act):
                    bullets.append(act)

        # Minion spawning removed as per request

        # turn off spawn invulnerability
        if player.is_invincible and t >= invul_end:
            player.is_invincible = False

        # ---------------- Update bullets ---------------------------
        for b in bullets[:]:
            # Skip if bullet doesn't have required position keys
            if 'x' not in b or 'y' not in b:
                bullets.remove(b)
                continue
                
            if 'angle' in b and 'speed' in b:
                b['x'] += math.cos(b['angle']) * b['speed'] * dt
                b['y'] += math.sin(b['angle']) * b['speed'] * dt
                
            # Clean up off-screen bullets
            if (b['y'] > SCREEN_HEIGHT+50 or b['x'] < -50 or b['x'] > SCREEN_WIDTH+50 or
                b['y'] < -50):  # Also check top of screen
                bullets.remove(b)
                continue

            # Collision with player
            if math.hypot(player.x - b.get('x',0), player.y - b.get('y',0)) < b.get('radius',0) + player.radius:
                if player.is_shielding and player.shield_energy > 0:
                    player.shield_energy = max(0, player.shield_energy - 5)
                    if shield_hit_sound:
                        shield_hit_sound.play()
                else:
                    player.health -= b.get('damage',5)
                    if player.health <= 0:
                        return "GAME_OVER"
                bullets.remove(b)
                continue

        # ---------------- Player bullets ---------------------------
        for pb in player_bullets[:]:
            speed = pb.get('speed', 350)
            pb['x'] += math.cos(pb['angle']) * speed * dt
            pb['y'] += math.sin(pb['angle']) * speed * dt
            
            # Handle shield boomerang behavior
            if pb.get('type') == 'shield':
                update_shield_bullet(pb, player_bullets, dt, arena_map, player, zombies=zombies)
            
            if pb['x'] < 0 or pb['x'] > SCREEN_WIDTH or pb['y'] < 0 or pb['y'] > SCREEN_HEIGHT:
                if pb.get('type') == 'shield' and pb.get('owner'):
                    pb['owner'].active_shield_throw = False
                player_bullets.remove(pb)
                continue

            # Collision with boss
            if math.hypot(boss.x - pb['x'], boss.y - pb['y']) < boss.radius + pb.get('radius', 4):
                if boss.take_damage(pb.get('damage', 20)):
                    show_ending()
                    return "VICTORY"
                if pb.get('type') == 'shield':
                    pb['returning'] = True
                    pb['damage'] = 0  # avoid repeated damage spam
                elif pb in player_bullets:
                    player_bullets.remove(pb)
                continue

            # Collision with zombies
            hit_any = False
            for z in zombies[:]:
                if not z.is_alive:
                    continue
                if math.hypot(z.x - pb['x'], z.y - pb['y']) < z.radius + pb.get('radius', 4):
                    if hasattr(z, 'take_damage'):
                        if z.take_damage(pb.get('damage', 20)):
                            # Spawn medkit when player in critical HP
                            spawn_medkit(z.x, z.y)
                            z.is_alive = False
                            zombies.remove(z)
                    hit_any = True
                    break
            if hit_any:
                if pb.get('type') == 'shield':
                    pb['returning'] = True
                    pb['damage'] = 0
                elif pb in player_bullets:
                    player_bullets.remove(pb)

        # ---------------- Collectible pickup ----------------
        for c in collectibles[:]:
            if math.hypot(player.x - c['x'], player.y - c['y']) < player.radius + COLLECTIBLE_SIZE//2:
                player.health = min(player.max_health, player.health + player.max_health)  # heal fully
                collectibles.remove(c)
                # TODO: optional collect sound

        # ---------------- Drawing ---------------------------
        screen.fill((20, 0, 0))
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(screen, (50, 0, 0), (0, y), (SCREEN_WIDTH, y))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(screen, (50, 0, 0), (x, 0), (x, SCREEN_HEIGHT))

        # Draw boss and enemy bullets
        boss.draw(screen)
        for b in bullets:
            if 'x' in b and 'y' in b:
                pygame.draw.circle(screen, b.get('color', (255, 50, 50)),
                                (int(b['x']), int(b['y'])),
                                b.get('radius', 5))
        
        # Draw player bullets and shield projectiles
        for pb in player_bullets:
            if pb.get('type') == 'shield':
                draw_shield_bullet(screen, pb)
            else:
                pygame.draw.circle(screen, BULLET_COLOR, (int(pb['x']), int(pb['y'])), pb.get('radius', 4))
        for z in zombies:
            z.draw(screen)
        # Draw collectibles
        for c in collectibles:
            screen.blit(c['image'], (c['x'] - COLLECTIBLE_SIZE//2, c['y'] - COLLECTIBLE_SIZE//2))

        player.draw(screen)
        draw_ui(screen, player)
        pygame.display.flip()

        # escape when boss dead handled in collision

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    run_divine_arena()
