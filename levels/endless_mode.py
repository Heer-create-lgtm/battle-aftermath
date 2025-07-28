import pygame
import random
import math
from shield_bullet import update_shield_bullet, draw_shield_bullet
import os
import sys
from settings import (
    TILE_SIZE, PLAYER_MAX_AMMO, MAX_HEALTH, PLAYER_BULLET_DAMAGE, HEALTH_BAR_FG, HEALTH_BAR_BG,
    STAMINA_BAR_FG, STAMINA_BAR_BG, MAX_STAMINA, SHIELD_BAR_FG, SHIELD_BAR_BG,
    PLAYER_MAX_SHIELD_ENERGY, UI_PANEL_BG, WHITE, SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, ZOMBIE_DAMAGE, BULLET_COLOR, BULLET_RADIUS, BULLET_SPEED, BLACK
)
from zombie import Zombie
from special_zombies import random_zombie
from ui import draw_ui
from mechanics import handle_player_input, update_player_state
from levels.outside_area import spawn_zombie as spawn_zombie_out


# ---------- HELPERS ----------
ENDLESS_MAP_WIDTH = 32  # should match other maps
ENDLESS_MAP_HEIGHT = 18

def _generate_empty_map():
    """Generate a walled empty map suitable for free movement"""
    top_bottom = "W" * ENDLESS_MAP_WIDTH
    middle = "W" + " " * (ENDLESS_MAP_WIDTH - 2) + "W"
    return [top_bottom] + [middle for _ in range(ENDLESS_MAP_HEIGHT - 2)] + [top_bottom]


def _load_highscore(path: str) -> int:
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def _save_highscore(path: str, score: int):
    try:
        with open(path, "w") as f:
            f.write(str(score))
    except Exception:
        pass


# ---------- HELL VISUALS HELPERS ----------
EMBER_COLOR_RANGE = [(255, 120, 0), (255, 180, 50), (255, 80, 0)]
embers = []

# Collectible particles/effects
particles = []


def _create_lava_surface():
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill((40, 0, 0))  # dark red base
    # random glowing cracks
    for _ in range(250):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        length = random.randint(20, 120)
        angle = random.uniform(0, math.pi * 2)
        end_x = x + math.cos(angle) * length
        end_y = y + math.sin(angle) * length
        color = random.choice([(200, 40, 0), (255, 90, 0), (255, 60, 20)])
        pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)
    return surface.convert()


lava_surface = None  # will be generated on first run
# Scrolling parameters for animated lava
LAVA_SCROLL_SPEED = 30  # pixels per second
lava_scroll = 0

# Load collect sound once
try:
    collect_sound = pygame.mixer.Sound('assets/music/reload.ogg')
except Exception:
    collect_sound = None


def _spawn_ember():
    return {
        'x': random.uniform(0, SCREEN_WIDTH),
        'y': SCREEN_HEIGHT + 10,
        'vy': random.uniform(-50, -120),
        'radius': random.randint(1, 3),
        'color': random.choice(EMBER_COLOR_RANGE),
        'life': random.uniform(1.5, 3.0)
    }


def _update_and_draw_embers(screen, dt):
    # spawn
    if random.random() < 0.6:  # increased density for fiery atmosphere
        embers.append(_spawn_ember())

    for ember in embers[:]:
        ember['y'] += ember['vy'] * dt
        ember['life'] -= dt
        if ember['life'] <= 0 or ember['y'] < -10:
            embers.remove(ember)
            continue
        pygame.draw.circle(screen, ember['color'], (int(ember['x']), int(ember['y'])), ember['radius'])


# Music helper

def _play_hell_music():
    """Play looping hell track using pygame.mixer.music so it is isolated
    from the normal sound-effect channels."""
    try:
        import pygame
        pygame.mixer.music.load('assets/music/doom.ogg')
        pygame.mixer.music.set_volume(0.7)
        pygame.mixer.music.play(-1)  # loop indefinitely
    except Exception as e:
        print(f"Could not play hell music: {e}")


# Helper functions for collectible particle effect
COLLECTIBLE_SIZE = 20

def _create_collect_effect(x, y):
    for _ in range(20):
        particles.append({
            'x': x,
            'y': y,
            'vx': random.uniform(-150, 150),
            'vy': random.uniform(-150, 150),
            'timer': random.uniform(0.2, 0.5),
            'color': random.choice([(255,255,255), (255,215,0), (180,180,180)])
        })

def _update_and_draw_particles(screen, dt):
    for p in particles[:]:
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt
        p['timer'] -= dt
        if p['timer'] <= 0:
            particles.remove(p)
        else:
            pygame.draw.rect(screen, p['color'], (p['x'], p['y'], 3, 3))

# ---------- MAIN LOOP ----------

def run_endless_mode(game_objects):
    """Endless survival mode. The player fights never-ending hordes of zombies.
    Returns "MAIN_MENU" when the player dies or quits."""
    player = game_objects.get("player")
    # Reset player stats
    player.health = MAX_HEALTH
    player.stamina = MAX_STAMINA
    player.ammo = PLAYER_MAX_AMMO
    player.shield_energy = PLAYER_MAX_SHIELD_ENERGY
    player.x, player.y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    # Ensure shotgun volume consistent
    if getattr(player, 'shotgun_sound', None):
        player.shotgun_sound.set_volume(0.6)

    # Game specific vars
    zombies = []
    bullets = []
    kill_count = 0
    game_map = _generate_empty_map()

    # Spawn collectible 5 somewhere random but open
    try:
        collect5_img_raw = pygame.image.load('assets/sprites/collection5.png').convert_alpha()
        collect5_img = pygame.transform.scale(collect5_img_raw, (COLLECTIBLE_SIZE, COLLECTIBLE_SIZE))
    except pygame.error:
        collect5_img = None
    collectible = {
        'x': random.randint(2 * TILE_SIZE, SCREEN_WIDTH - 2 * TILE_SIZE),
        'y': random.randint(2 * TILE_SIZE, SCREEN_HEIGHT - 2 * TILE_SIZE),
        'image': collect5_img,
        'collected': False
    }

    # High-score persistence
    HS_PATH = os.path.join(os.path.dirname(__file__), "..", "endless_highscore.txt")
    high_score = _load_highscore(HS_PATH)

    # Pygame handles
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()

    # Load sounds
    try:
        game_over_sfx = pygame.mixer.Sound("assets/music/game_over.ogg")
        hurt_sfx = pygame.mixer.Sound("assets/music/player_hurt.ogg")
        shield_hit_sfx = pygame.mixer.Sound("assets/music/shield_hit.ogg")
    except Exception:
        game_over_sfx = hurt_sfx = shield_hit_sfx = None

    # Start hell background music
    _play_hell_music()

    # Reference to main's background_music dict for checking music state
    try:
        from main import background_music, play_music as _play_music_main
    except Exception:
        background_music = {}
        _play_music_main = None

    # Dark DOOM-like colours
    BACKGROUND = (20, 0, 0)  # slightly brighter base red

    # Timer to avoid checking music every single frame
    music_check_timer = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        # Ensure background music keeps playing (check every 3 seconds)
        if _play_music_main:
            music_check_timer += dt
            if music_check_timer >= 3.0:
                music_check_timer = 0.0
                if 0 not in background_music:
                    _play_music_main("doom.ogg", channel=0, volume=0.7, loop=True)

        # Draw collectible if not collected
        if not collectible['collected'] and collectible['image']:
            screen.blit(collectible['image'], (collectible['x'] - COLLECTIBLE_SIZE // 2, collectible['y'] - COLLECTIBLE_SIZE // 2))

        # Particle updates
        _update_and_draw_particles(screen, dt)

        # -------- Event handling --------
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Handle player input (movement, shooting etc.)
        handle_player_input(player, bullets, events)

        # Update player physics/state
        keys = pygame.key.get_pressed()
        update_player_state(player, keys, game_map, dt)

        # -------- Update zombies --------
        for zombie in zombies[:]:
            info = zombie.update(player.x, player.y, game_map, dt)
            if info:
                bullets.append(info)
                
            # Damage to player when close
            if zombie.is_alive:
                dist = math.hypot(player.x - zombie.x, player.y - zombie.y)
                if dist < player.radius + zombie.radius:
                    current_time = pygame.time.get_ticks()
                    attack_cooldown = 1000
                    if current_time - zombie.last_attack_time > attack_cooldown:
                        player.take_damage(ZOMBIE_DAMAGE)
                        if hurt_sfx: hurt_sfx.play()
                        zombie.last_attack_time = current_time

            # Zombie death check
            if not zombie.is_alive:
                zombies.remove(zombie)
                kill_count += 1
        
        # -------- Collectible pickup check --------
        if not collectible['collected']:
            dist_c = math.hypot(player.x - collectible['x'], player.y - collectible['y'])
            if dist_c < player.radius + COLLECTIBLE_SIZE/2:
                collectible['collected'] = True
                _create_collect_effect(collectible['x'], collectible['y'])
                if collect_sound:
                    collect_sound.play()

        # Player death check
        if player.health <= 0:
            running = False
            break

        # -------- Spawn new zombies --------
        # Dynamic difficulty scaling: more zombies as kill count rises
        desired = min(50, 8 + kill_count // 2)  # cap at 50, ramp quicker
        while len(zombies) < desired:
            prev_len = len(zombies)
            spawn_zombie_out(game_map, zombies, player)
            if len(zombies) > prev_len:
                # scale the newly added zombie(s)
                level = kill_count // 20  # every 20 kills raise level
                for nz in zombies[prev_len:]:
                    if not hasattr(nz, 'scaled_level') or nz.scaled_level < level:
                        nz.health = int(nz.health * (1 + 0.3 * level))
                        nz.speed *= (1 + 0.1 * level)
                        nz.scaled_level = level

        # -------- Update bullets --------
        for bullet in bullets[:]:
            # Skip or remove bullets that don't conform to expected dict structure
            if not isinstance(bullet, dict) or 'x' not in bullet or 'y' not in bullet:
                bullets.remove(bullet)
                continue

            # Standard bullet dict processing
            bullet['x'] += math.cos(bullet['angle']) * BULLET_SPEED * dt
            bullet['y'] += math.sin(bullet['angle']) * BULLET_SPEED * dt

            # Shield boomerang behaviour
            if bullet.get('type') == 'shield':
                update_shield_bullet(bullet, bullets, dt, game_map, player, zombies)

            off_screen = (bullet['x'] < 0 or bullet['x'] > SCREEN_WIDTH or
                          bullet['y'] < 0 or bullet['y'] > SCREEN_HEIGHT)
            if off_screen:
                if bullet.get('type') == 'shield' and bullet.get('owner'):
                    bullet['owner'].active_shield_throw = False
                bullets.remove(bullet)
                continue

            # Collision with zombies
            for zombie in zombies[:]:
                if zombie.is_alive:
                    dist = math.hypot(zombie.x - bullet['x'], zombie.y - bullet['y'])
                    if dist < zombie.radius:
                        if bullet.get('type') == 'shield':
                            # bounce instead of disappearing
                            bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                            bullet['bounces'] = bullet.get('bounces', 0) + 1
                            if bullet['bounces'] >= 4:
                                bullet['returning'] = True
                            zombie.take_damage(bullet.get('damage', PLAYER_BULLET_DAMAGE))
                        else:
                            zombie.take_damage(bullet.get('damage', PLAYER_BULLET_DAMAGE))
                            if bullet in bullets:
                                bullets.remove(bullet)
                        break

        # --- After bullet loop: reset shield flag if no projectile owned by player ---
        if player.active_shield_throw and not any(b.get('type')=='shield' and b.get('owner')==player for b in bullets):
            player.active_shield_throw = False

        # -------- Drawing --------
        global lava_surface, lava_scroll
        if lava_surface is None:
            lava_surface = _create_lava_surface()

        # Animate scrolling lava by vertical offset
        lava_scroll = (lava_scroll + LAVA_SCROLL_SPEED * dt) % SCREEN_HEIGHT
        screen.blit(lava_surface, (0, -lava_scroll))
        screen.blit(lava_surface, (0, SCREEN_HEIGHT - lava_scroll))

        # Dynamic red fog overlay with subtle flicker
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        flicker_alpha = random.randint(100, 140)
        overlay.set_alpha(flicker_alpha)
        overlay.fill((80, 0, 0))
        screen.blit(overlay, (0, 0))

        # Embers / fire sparks
        _update_and_draw_embers(screen, dt)

        # Draw player and entities
        # Draw bullets
        for bullet in bullets:
            if bullet.get('type') == 'shield':
                draw_shield_bullet(screen, bullet)
            else:
                pygame.draw.circle(screen, BULLET_COLOR, (int(bullet['x']), int(bullet['y'])), bullet.get('radius', BULLET_RADIUS))
        player.draw(screen)
        for z in zombies:
            z.draw(screen)
        for bullet in bullets:
            pygame.draw.circle(screen, BULLET_COLOR, (int(bullet['x']), int(bullet['y'])), BULLET_RADIUS)

        # Draw UI + kill counters
        draw_ui(screen, player)
        font = pygame.font.Font(None, 36)
        kills_surf = font.render(f"Kills: {kill_count}", True, WHITE)
        hs_surf = font.render(f"High Score: {high_score}", True, WHITE)
        screen.blit(kills_surf, (20, 20))
        screen.blit(hs_surf, (20, 60))

        pygame.display.flip()

    # ----- Exit sequence -----
    # Fade out background music when mode ends
    try:
        pygame.mixer.music.fadeout(1000)
    except Exception:
        pass

    if game_over_sfx:
        game_over_sfx.play()
        # Wait for the sound to play before showing the game over screen
        pygame.time.wait(1000)  # 1 second delay to hear the sound

    if kill_count > high_score:
        high_score = kill_count
        _save_highscore(HS_PATH, high_score)

    # Interactive game-over screen that mirrors main story mode
    _show_endless_game_over(screen, kill_count, high_score)
    return "MAIN_MENU"


def _show_endless_game_over(screen, kills: int, record: int):
    """Display an interactive game-over overlay for Endless Mode."""
    title_font = pygame.font.Font(None, 82)
    mid_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 32)

    # Button settings
    button_width, button_height = 300, 70
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT//2 + 100, button_width, button_height)

    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_m):
                return  # back to caller
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button_rect.collidepoint(mouse_pos):
                return

        # Background dim
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))

        # Texts
        title = title_font.render("YOU HAVE FALLEN", True, (220, 0, 0))
        kills_txt = mid_font.render(f"Kills: {kills}", True, WHITE)
        record_txt = mid_font.render(f"High Score: {record}", True, WHITE)

        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 120)))
        screen.blit(kills_txt, kills_txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20)))
        screen.blit(record_txt, record_txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40)))

        # Button
        is_hover = button_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (120,0,0) if is_hover else (80,0,0), button_rect, 0, 10)
        pygame.draw.rect(screen, (200,0,0), button_rect, 3, 10)
        btn_text = small_font.render("MAIN MENU", True, WHITE)
        screen.blit(btn_text, btn_text.get_rect(center=button_rect.center))

        pygame.display.flip()
