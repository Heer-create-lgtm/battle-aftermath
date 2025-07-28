import pygame
import math
import sys
import random
import traceback
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, GOD_GOLD, AURA_COLOR_GOLD,
    GOD_SILVER, AURA_COLOR_SILVER, GOD_BRONZE, AURA_COLOR_BRONZE,
    CARPET_COLOR, MAP_HEIGHT, WHITE, DIALOGUE_TEXT_COLOR, WALL_COLOR,
    PILLAR_COLOR, GOD_EYE_COLOR, STAFF_COLOR, BULLET_COLOR, BULLET_RADIUS,
    UI_PANEL_BG, PLAYER_MAX_SHIELD_ENERGY, SHIELD_BAR_BG, SHIELD_BAR_FG,
    MAX_HEALTH, HEALTH_BAR_BG, HEALTH_BAR_FG, MAX_STAMINA, STAMINA_BAR_BG,
    STAMINA_BAR_FG, PLAYER_MAX_AMMO, BG_COLOR, BLACK, GREY, ZOMBIE_DAMAGE,
    BULLET_SPEED, MAP_WIDTH, PYTHON_DAMAGE, PYTHON_CHARGE_DAMAGE,
    PLAYER_BULLET_DAMAGE, PYTHON_HEALTH, BOSS_HEALTH_BAR_BG,
    BOSS_HEALTH_BAR_FG, THRONE_ROOM_END_POS, END_LEVEL_RADIUS
)
from player import Player
from zombie import Zombie
from human import Human
from python_boss import PythonBoss
from levels.outside_area import run_outside_area
from levels.lab_scene import show_lab_scene
from ui import draw_ui
from levels.endless_mode import run_endless_mode

from mechanics import handle_player_input, update_player_state

# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.mixer.set_reserved(1)  
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Aftermath")
clock = pygame.time.Clock()

# --- Revival & progression flags ---
# Set to True once the 5-blood quest is finished
blood_quest_completed = False
# Stores last position before death so player can be restored
last_checkpoint = None  # dict with keys: level, x, y, angle
# Counts how many times scientist has revived the hero (for varied dialogue)
revival_count = 0

# --- Scene state management ---
game_state = "START"

throne_room_end_triggered = False

try:
    from settings import PELLET_SPRITE_SIZE
    pellet_img = pygame.image.load('assets/sprites/shotgun_pellet.png').convert_alpha()
    pellet_img = pygame.transform.scale(pellet_img, (PELLET_SPRITE_SIZE, PELLET_SPRITE_SIZE))
except Exception:
    pellet_img = None

try:
    game_over_sound = pygame.mixer.Sound("assets/music/game_over.ogg")
    collect_sound = pygame.mixer.Sound("assets/music/reload.ogg")
except Exception:
    print("An unexpected error occurred:")
    traceback.print_exc()
    game_over_sound = None
    collect_sound = None


particles = []


COLLECTIBLE_SIZE = 20
collectibles = []
collectible_images = {}

def load_collectible_images():
    global collectible_images
    collectible_images = {
        '1': pygame.transform.scale(pygame.image.load('assets/sprites/collection1.png').convert_alpha(), (COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
        '2': pygame.transform.scale(pygame.image.load('assets/sprites/collection2.png').convert_alpha(), (COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
        '3': pygame.transform.scale(pygame.image.load('assets/sprites/collection3.png').convert_alpha(), (COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
    }
    # Try loading medkit sprite
    try:
        med_img = pygame.image.load('assets/sprites/medkit.png').convert_alpha()
        med_img = pygame.transform.scale(med_img, (COLLECTIBLE_SIZE, COLLECTIBLE_SIZE))
    except FileNotFoundError:
        med_img = pygame.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE))
        med_img.fill((200, 0, 0))
        pygame.draw.rect(med_img, (255, 255, 255), med_img.get_rect(), 2)
    collectible_images['medkit'] = med_img
load_collectible_images()


is_throne_room_level = True

player = Player()

# God settings
gods = [
    {'x': 14 * TILE_SIZE, 'y': 2.5 * TILE_SIZE, 'color': GOD_GOLD, 'radius': TILE_SIZE, 'aura_color': AURA_COLOR_GOLD}, 
    {'x': 16 * TILE_SIZE, 'y': 2.5 * TILE_SIZE, 'color': GOD_SILVER, 'radius': TILE_SIZE, 'aura_color': AURA_COLOR_SILVER},
    {'x': 18 * TILE_SIZE, 'y': 2.5 * TILE_SIZE, 'color': GOD_BRONZE, 'radius': TILE_SIZE, 'aura_color': AURA_COLOR_BRONZE}
]

bullets = []

throne_room_map = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W                              W",
    "W        WWWWWWWWWWWWWW        W",
    "W        W            W        W",
    "W                              W",
    "W   P                      P   W",
    "W                              W",
    "W                              W",
    "W   P                      P   W",
    "W                              W",
    "W                              W",
    "W   P                      P   W",
    "W                              W",
    "WWWWWWWWWWWW          WWWWWWWWWW",
    "W                              W",
    "W                              W",
    "W                              W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

tutorial_map = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W                              W",
    "W                              W",
    "W    1                         W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

post_tutorial_map = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W    WWWW                WWWW  W",
    "W    W                      W  W",
    "W    W                      W  W",
    "W    WWWW                WWWW  W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

boss_level_map = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W                              W",
    "W                              W",
    "W                              W",
    "W   P                      P   W",
    "W                              W",
    "W                              W",
    "W     2                        W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W   P                      P   W",
    "W                              W",
    "W                              W",
    "W                              W",
    "W                              W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

game_map = throne_room_map

def spawn_collectibles(current_map):
    collectibles.clear()
    for y, row in enumerate(current_map):
        for x, tile in enumerate(row):
            if tile in collectible_images:
                collectibles.append({
                    'x': x * TILE_SIZE + TILE_SIZE // 2,
                    'y': y * TILE_SIZE + TILE_SIZE // 2,
                    'type': tile,
                    'image': collectible_images[tile]
                })


def maybe_spawn_medkit(zx, zy):
    """Spawn a medkit collectible at given position if player low on health."""
    if player.health <= player.max_health * 0.2:
        collectibles.append({
            'x': zx,
            'y': zy,
            'type': 'medkit',
            'image': collectible_images['medkit']
        })

background_music = {}

def play_sound_effect(sound_name, volume=1.0):
    """Play a sound effect with proper channel management.
    
    Args:
        sound_name (str): Name of the sound file in assets/music/
        volume (float): Volume level (0.0 to 1.0)
    """
    try:
        # Find an available channel
        channel = pygame.mixer.find_channel(True)
        if channel:
            sound = pygame.mixer.Sound(f"assets/music/{sound_name}")
            sound.set_volume(volume)
            channel.play(sound)
            return channel
    except Exception as e:
        print(f"Error playing sound effect {sound_name}: {e}")
    return None

def play_music(track_name, channel=0, volume=0.5, loop=True):
    """Play a music track on a specific channel with volume control.
    
    Args:
        track_name (str): Name of the music file in assets/music/
        channel (int): Channel number to play on (0-7)
        volume (float): Volume level (0.0 to 1.0)
        loop (bool): Whether to loop the track
    """
    try:
        # Stop any existing music on this channel
        if channel in background_music:
            background_music[channel].stop()
            
        # Load and play the new track
        sound = pygame.mixer.Sound(f"assets/music/{track_name}")
        sound.set_volume(volume)
        if loop:
            loops = -1  # Loop indefinitely
        else:
            loops = 0   # Play once
            
        channel_obj = pygame.mixer.Channel(channel)
        channel_obj.play(sound, loops=loops, fade_ms=500)
        background_music[channel] = channel_obj
        return channel_obj
    except pygame.error as e:
        print(f"Warning: Could not play music file 'assets/music/{track_name}'. Error: {e}")
        return None

def stop_music(channel=None, fade_out=500):
    """Stop music on a specific channel or all channels.
    
    Args:
        channel (int, optional): Channel number to stop. If None, stops all channels.
        fade_out (int): Fade out duration in milliseconds.
    """
    if channel is not None and channel in background_music:
        background_music[channel].fadeout(fade_out)
        del background_music[channel]
    elif channel is None:
        for ch in list(background_music.keys()):
            background_music[ch].fadeout(fade_out)
            del background_music[ch]

def draw_floor_details():
    # Draw red carpet
    if is_throne_room_level:
        carpet_width = 3 * TILE_SIZE
        carpet_x = SCREEN_WIDTH / 2 - carpet_width / 2
        carpet_y_start = 4 * TILE_SIZE
        carpet_y_end = (MAP_HEIGHT - 3) * TILE_SIZE
        pygame.draw.rect(screen, CARPET_COLOR, (carpet_x, carpet_y_start, carpet_width, carpet_y_end))

def create_collect_effect(x, y):
    for _ in range(20):  # Number of particles
        particles.append({
            'x': x,
            'y': y,
            'vx': random.uniform(-150, 150),
            'vy': random.uniform(-150, 150),
            'timer': random.uniform(0.2, 0.5),  # Lifetime in seconds
            'color': random.choice([WHITE, GOD_GOLD, DIALOGUE_TEXT_COLOR])
        })

def update_and_draw_particles(dt):
    for p in particles[:]:
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt
        p['timer'] -= dt
        if p['timer'] <= 0:
            particles.remove(p)
        else:
            # Simple square particle
            pygame.draw.rect(screen, p['color'], (p['x'], p['y'], 3, 3))

def draw_collectibles():
    for collectible in collectibles:
        screen.blit(collectible['image'], (collectible['x'] - COLLECTIBLE_SIZE // 2, collectible['y'] - COLLECTIBLE_SIZE // 2))

def draw_map():
    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            if tile == 'W':
                pygame.draw.rect(screen, WALL_COLOR, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            elif tile == 'P':
                pygame.draw.circle(screen, PILLAR_COLOR, (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2), TILE_SIZE // 2)

def draw_gods():
    current_time = pygame.time.get_ticks()
    for god in gods:
        # Calculate pulsing effect
        pulse = (math.sin(current_time * 0.001) * 0.1) + 1.0
        
        # Draw outer glow
        glow_radius = int(god['radius'] * 2.5 * pulse)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        
        # Create gradient glow
        for i in range(glow_radius, 0, -1):
            alpha = int(100 * (i / glow_radius))
            color = (*god['aura_color'][:3], alpha)
            pygame.draw.circle(glow_surface, color, (glow_radius, glow_radius), i)
            
        screen.blit(glow_surface, (god['x'] - glow_radius, god['y'] - glow_radius), special_flags=pygame.BLEND_ADD)
        
        # Draw main body with inner glow
        body_surface = pygame.Surface((god['radius'] * 2, god['radius'] * 2), pygame.SRCALPHA)
        pygame.draw.circle(body_surface, (*god['color'], 200), (god['radius'], god['radius']), god['radius'])
        
        # Add subtle inner glow
        for i in range(god['radius'], god['radius']//2, -1):
            # Reduced alpha for a more subtle effect
            alpha = int(1.25 * (1 - (i / god['radius'])))
            color = (*WHITE, alpha)
            pygame.draw.circle(body_surface, color, (god['radius'], god['radius']), i)
            
        screen.blit(body_surface, (god['x'] - god['radius'], god['y'] - god['radius']))
        
        # Draw divine symbols or patterns
        symbol_points = []
        for i in range(8):
            angle = (i / 8) * (2 * math.pi) + (current_time * 0.001)
            x = god['x'] + math.cos(angle) * (god['radius'] * 0.8)
            y = god['y'] + math.sin(angle) * (god['radius'] * 0.8)
            symbol_points.append((x, y))
            
        if len(symbol_points) > 1:
            pygame.draw.lines(screen, (255, 255, 255, 150), True, symbol_points, 2)
        
        # Draw eyes with glow
        eye_glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(eye_glow, (*GOD_EYE_COLOR, 150), (10, 10), 10)
        screen.blit(eye_glow, (int(god['x']) - 10, int(god['y']) - god['radius'] // 2 - 10), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(screen, GOD_EYE_COLOR, (int(god['x']), int(god['y']) - god['radius'] // 2), 4)
        
        # Draw ornate staff
        staff_x = int(god['x']) + god['radius'] - 5
        staff_y_start = int(god['y']) - god['radius']
        staff_y_end = int(god['y']) + god['radius'] * 2
        
        # Staff glow
        staff_glow = pygame.Surface((20, staff_y_end - staff_y_start + 20), pygame.SRCALPHA)
        pygame.draw.line(staff_glow, (*STAFF_COLOR, 100), (10, 10), (10, staff_y_end - staff_y_start + 10), 20)
        screen.blit(staff_glow, (staff_x - 10, staff_y_start - 10), special_flags=pygame.BLEND_ADD)
        
        # Staff body
        pygame.draw.line(screen, STAFF_COLOR, (staff_x, staff_y_start), (staff_x, staff_y_end), 8)
        
        # Staff orb
        pygame.draw.circle(screen, (255, 200, 100), (staff_x, staff_y_start - 10), 12)
        pygame.draw.circle(screen, (255, 255, 200), (staff_x, staff_y_start - 10), 6)

def draw_bullets():
    for bullet in bullets:
        if bullet.get('type') == 'shield':
            # Draw trail
            from settings import SHIELD_TRAIL_COLOR
            for i in range(len(bullet['trail'])-1):
                start = bullet['trail'][i]
                end = bullet['trail'][i+1]
                pygame.draw.line(screen, SHIELD_TRAIL_COLOR[:3], start, end, 3)
            img = None
            if bullet.get('owner'):
                img = getattr(bullet['owner'], 'shield_image', None)
            if img:
                rect = img.get_rect(center=(bullet['x'], bullet['y']))
                screen.blit(img, rect)
            else:
                # fallback circle if sprite missing
                pygame.draw.circle(screen, (0, 180, 255), (int(bullet['x']), int(bullet['y'])), bullet.get('radius',12))
        else:
            if bullet.get('sprite') == 'pellet' and pellet_img:
                rect = pellet_img.get_rect(center=(bullet['x'], bullet['y']))
                screen.blit(pellet_img, rect)
            else:
                pygame.draw.circle(screen, BULLET_COLOR, (int(bullet['x']), int(bullet['y'])), BULLET_RADIUS)

def draw_ui_if_needed():
    if not is_throne_room_level:
        draw_ui(screen, player)

def show_dialogue(lines):
    dialogue_font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    # Calculate dialogue box dimensions
    dialogue_box_height = 150  # Increased height for better text display
    dialogue_box_y = SCREEN_HEIGHT - dialogue_box_height - 20
    dialogue_box_width = SCREEN_WIDTH - 40
    dialogue_box_x = 20
    
    # Create a semi-transparent overlay for the entire screen
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # Semi-transparent black
    
    for line in lines:
        # Redraw the scene behind the dialogue
        screen.fill(BG_COLOR)
        draw_floor_details()
        draw_map()
        draw_gods()
        player.draw(screen)
        
        # Draw the overlay
        screen.blit(overlay, (0, 0))
        
        # Draw dialogue box with border and shadow
        pygame.draw.rect(screen, (0, 0, 0, 200), 
                        (dialogue_box_x-2, dialogue_box_y-2, 
                         dialogue_box_width+4, dialogue_box_height+4), 
                        border_radius=10)
        pygame.draw.rect(screen, (100, 100, 150), 
                        (dialogue_box_x, dialogue_box_y, 
                         dialogue_box_width, dialogue_box_height),
                        border_radius=8)
        
        # Render wrapped text
        words = line.split(' ')
        wrapped_lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if dialogue_font.size(test_line)[0] < dialogue_box_width - 40:  # Padding of 20px each side
                current_line.append(word)
            else:
                wrapped_lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            wrapped_lines.append(' '.join(current_line))
        
        # Draw each line of text
        for i, text in enumerate(wrapped_lines):
            text_surface = dialogue_font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(
                x=dialogue_box_x + 20,
                y=dialogue_box_y + 20 + i * (dialogue_font.get_height() + 5)
            )
            screen.blit(text_surface, text_rect)
        
        # Draw continue prompt at the bottom of the box
        continue_text = small_font.render("Press ENTER to continue...", True, (200, 200, 255))
        continue_rect = continue_text.get_rect(
            centerx=SCREEN_WIDTH // 2,
            y=dialogue_box_y + dialogue_box_height - 40
        )
        screen.blit(continue_text, continue_rect)
        
        pygame.display.flip()

        # Wait for player to continue
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        waiting = False
    
def power_up_effect():
    start_time = pygame.time.get_ticks()
    duration = 2000 # 2 seconds
    flash_interval = 100 # milliseconds

    while pygame.time.get_ticks() - start_time < duration:
        # Redraw the scene
        screen.fill(BG_COLOR)
        draw_floor_details()
        draw_map()
        draw_gods()
        player.draw(screen)
        
        # Flash effect
        if (pygame.time.get_ticks() // flash_interval) % 2 == 0:
             pygame.draw.circle(screen, WHITE, (int(player.x), int(player.y)), 12)
        else:
             pygame.draw.circle(screen, GOD_GOLD, (int(player.x), int(player.y)), 10)

        pygame.display.flip()

        # Keep event loop responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

def fade_to_black(surface, duration=2000):
    """Fade the screen to black over the given duration in milliseconds."""
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill(BLACK)
    steps = 30
    delay = max(10, duration // steps)
    
    for alpha in range(0, 256, 256 // steps):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        fade.set_alpha(alpha)
        temp_surface = surface.copy()
        temp_surface.blit(fade, (0, 0), special_flags=pygame.BLEND_MULT)
        screen.blit(temp_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(delay)
    
    # Ensure final state is fully black
    surface.fill(BLACK)
    pygame.display.flip()
    return fade

def fade_in_from_black(surface, duration=2000):
    """Fade in from black over the given duration in milliseconds."""
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill(BLACK)
    for alpha in range(300, 0, -5):  # Fade in from black
        fade.set_alpha(alpha)
        surface.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)

def show_scientist_revival_scene():
    """Show the lab scene where the scientist revives the player."""
    from levels.revive_lab_scene import show_lab_scene
    
    # Show the dedicated revival lab scene with new dialogue and receive game objects
    return show_lab_scene()

def show_scientist_after_blood():
    """ Show the scene after player collects enough zombie blood. """
    
    # Fade to black
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill(BLACK)
    for alpha in range(0, 256, 5):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)
    
    # Show dialogue
    show_dialogue([
        "Scientist: Excellent work! With this blood sample, I can create a cure.",
        "The scientist works frantically at his lab bench...",
        "Scientist: It's ready! This serum will make you immune to the zombie virus.",
        "You feel a surge of energy as the serum takes effect!"
    ])
    
    # Get player from globals if it exists
    player_obj = globals().get('player')
    if player_obj:
        player_obj.max_health = 150  # Increased from 100
        player_obj.health = player_obj.max_health
        player_obj.max_stamina = 150  # Increased from 100
        player_obj.stamina = player_obj.max_stamina
        player_obj.max_shield_energy = 150  # Increased from 100
        player_obj.shield_energy = player_obj.max_shield_energy
    
    # Mark quest complete so future revivals skip the blood requirement
    globals()['blood_quest_completed'] = True
    # Fade back in
    fade_in_from_black(screen)
    
    # Update game state
    if 'game_state' in globals():
        globals()['game_state'] = "GAME"

def check_zombie_blood_quest():
    """ Check if player has collected enough zombie blood. """
    player_obj = globals().get('player')
    if (player_obj and hasattr(player_obj, 'zombie_blood_collected') and 
        player_obj.zombie_blood_collected >= 5):
        # Player has collected enough blood, show completion scene
        show_scientist_after_blood()
        player_obj.zombie_blood_collected = 0  # Reset counter
        return True
    return False

def show_game_over_screen(show_revival=False, allow_revival=False, show_restart_level=True):
    # These are used in the function
    global current_level_runner  # noqa: F821
    
    # Play background music if not already playing
    if not background_music:  # If no music is playing
        play_music("bgm.ogg")
    
    # Play sound
    if game_over_sound:
        game_over_sound.play()
        
    # Rest of the function...

    # Create a semi-transparent surface for the overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    title_font = pygame.font.Font(None, 82)
    button_font = pygame.font.Font(None, 52)
    small_font = pygame.font.Font(None, 36)
    
    title_text = title_font.render("YOU HAVE FALLEN", True, (220, 0, 0))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 200))
    
    # Add dramatic text
    sub_text = small_font.render("The darkness consumes you...", True, (200, 200, 200))
    sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 130))

    # Button settings
    button_width, button_height = 350, 60
    button_y_start = SCREEN_HEIGHT / 2 - 50
    button_spacing = 80
    button_x = SCREEN_WIDTH / 2 - button_width / 2

    # Initialize button rects
    revival_rect = None
    restart_level_rect = None
    
    # Position buttons based on the options requested
    if show_revival:
        revival_rect = pygame.Rect(button_x, button_y_start, button_width, button_height)
        restart_game_rect = pygame.Rect(button_x, button_y_start + button_spacing, button_width, button_height)
    else:
        if show_restart_level:
            restart_level_rect = pygame.Rect(button_x, button_y_start, button_width, button_height)
            restart_game_rect = pygame.Rect(button_x, button_y_start + button_spacing, button_width, button_height)
        else:
            restart_level_rect = None
            restart_game_rect = pygame.Rect(button_x, button_y_start, button_width, button_height)
    
    # Create button texts
    revival_text = button_font.render("Seek Revival", True, (200, 255, 200))
    revival_text_rect = revival_text.get_rect(center=revival_rect.center if revival_rect else (0, 0))
    
    if restart_level_rect:
        restart_level_text = button_font.render("Restart Level", True, WHITE)
        restart_level_text_rect = restart_level_text.get_rect(center=restart_level_rect.center)
    else:
        restart_level_text = None
    
    restart_game_text = button_font.render("Main Menu", True, WHITE)
    restart_game_text_rect = restart_game_text.get_rect(center=restart_game_rect.center if restart_game_rect else (0, 0))
    
    # Add subtle particle effects only if the revival button is present
    revival_particles = []
    if show_revival and revival_rect:
        for _ in range(20):
            revival_particles.append({
                'x': random.randint(revival_rect.left, revival_rect.right),
                'y': random.randint(revival_rect.top, revival_rect.bottom),
                'size': random.randint(2, 5),
                'alpha': random.randint(100, 200),
                'speed': random.uniform(0.5, 2)
            })

    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        
        # Update revival button particles (only if they exist)
        if revival_particles:
            for p in revival_particles:
                p['y'] -= p['speed']
                p['alpha'] -= 1
                if p['alpha'] <= 0 and revival_rect:
                    p['y'] = random.randint(revival_rect.bottom - 10, revival_rect.bottom)
                    p['x'] = random.randint(revival_rect.left, revival_rect.right)
                    p['alpha'] = random.randint(100, 200)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if show_revival and revival_rect and revival_rect.collidepoint(mouse_pos):
                    return "REVIVE"
                elif restart_level_rect and restart_level_rect.collidepoint(mouse_pos):
                    # Restart the current level
                    # Let main loop handle level restart logic
                    return "RESTART_LEVEL"
                elif restart_game_rect and restart_game_rect.collidepoint(mouse_pos):
                    # Return to main menu
                    return "MAIN_MENU"

        # Drawing
        screen.fill(BG_COLOR)
        
        # Draw map in background (semi-visible)
        draw_map()
        
        # Draw overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        # Draw title and subtitle
        screen.blit(title_text, title_rect)
        screen.blit(sub_text, sub_rect)

        # Draw revival button with particles if shown
        if show_revival and revival_rect:
            # Draw button background
            is_hovered = revival_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (0, 80, 0, 200) if not is_hovered else (0, 120, 0, 230), revival_rect, 0, 10)
            pygame.draw.rect(screen, (0, 255, 0, 200) if is_hovered else (0, 200, 0, 200), revival_rect, 3, 10)
            
            # Draw particles for revival button
            for p in revival_particles:
                if p['alpha'] > 0:
                    s = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
                    pygame.draw.circle(s, (100, 255, 100, p['alpha']), (p['size']//2, p['size']//2), p['size']//2)
                    screen.blit(s, (p['x'], p['y']))
            
            # Draw button text
            screen.blit(revival_text, revival_text_rect)
            
            # Add hint text
            hint_text = small_font.render("Seek the scientist's help for another chance...", True, (200, 200, 200))
            # Position the hint text ABOVE the Seek Revival button to ensure it isn't obscured.
            hint_y = revival_rect.top - hint_text.get_height() - 10
            screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, hint_y))

        # Button colors
        button_color = (80, 0, 0, 200)  # Darker red
        button_hover = (120, 0, 0, 230)  # Brighter red
        border_color = (200, 0, 0, 200)  # Red border
        
        # Draw Restart Level button if shown
        if restart_level_rect:
            is_hovered = restart_level_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, button_hover if is_hovered else button_color, restart_level_rect, 0, 10)
            pygame.draw.rect(screen, border_color, restart_level_rect, 3, 10)
            screen.blit(restart_level_text, restart_level_text_rect)
        
        # Draw Main Menu button
        if restart_game_rect:
            is_hovered = restart_game_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, button_hover if is_hovered else button_color, restart_game_rect, 0, 10)
            pygame.draw.rect(screen, border_color, restart_game_rect, 3, 10)
            screen.blit(restart_game_text, restart_game_text_rect)

        pygame.display.flip()
    
    return False
        
# -------------------------------------------------------
# Fake death cut-scene shown after the gods strike you down
# -------------------------------------------------------

def show_fake_death_screen():
    """Display a realistic fake death screen matching the real one, then overlay the hero’s quip."""
    title_font = pygame.font.Font(None, 82)
    small_font = pygame.font.Font(None, 36)

    # Play the existing game-over sound
    if game_over_sound:
        game_over_sound.play()

    start_time = pygame.time.get_ticks()
    phase = 0  # 0 = show death for 3s, 1 = overlay quip for 2s
    local_clock = pygame.time.Clock()

    while True:
        now = pygame.time.get_ticks()
        elapsed = now - start_time
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

        # Base: replicate original death screen visuals (static)
        screen.fill(BG_COLOR)
        draw_map()  # faint backdrop like original
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        title_text = title_font.render("YOU HAVE FALLEN", True, (220, 0, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 200))
        screen.blit(title_text, title_rect)

        sub_text = small_font.render("The darkness consumes you...", True, (200, 200, 200))
        sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 130))
        screen.blit(sub_text, sub_rect)

        # After 3 seconds, switch to overlay quip
        if elapsed >= 3000:
            phase = 1
        if phase == 1:
            quip_font = pygame.font.Font(None, 48)
            quip_text = quip_font.render("You thought it was over, mate.", True, (255, 255, 255))
            quip_rect = quip_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100))
            screen.blit(quip_text, quip_rect)

        pygame.display.flip()
        local_clock.tick(60)

        # Exit after total of 5 seconds (3s death + 2s quip)
        if elapsed >= 5000:
            break


def show_teleport_and_vision_scene():
    # Teleport fade effect
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for alpha in range(0, 256, 4):
        # Redraw the scene to avoid artifacts from dialogue boxes
        screen.fill(BG_COLOR)
        draw_floor_details()
        draw_map()
        draw_gods()
        player.draw(screen)
        
        fade_surface.set_alpha(alpha)
        fade_surface.fill(WHITE)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(15)

    # Vision scene
    screen.fill(BG_COLOR)
    vision_font = pygame.font.Font(None, 48)
    god_font = pygame.font.Font(None, 36)
    
    vision_line = "A vision... he is back on Earth."
    vision_line_2 = "Before him lies his daughter... still and silent."
    god_line = '"This power... it is fueled by your RAGE."'

    # Display text
    text_surface1 = vision_font.render(vision_line, True, GREY)
    text_rect1 = text_surface1.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))
    screen.blit(text_surface1, text_rect1)
    
    text_surface2 = vision_font.render(vision_line_2, True, GREY)
    text_rect2 = text_surface2.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(text_surface2, text_rect2)
    
    god_surface = god_font.render(god_line, True, DIALOGUE_TEXT_COLOR)
    god_rect = god_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150))
    screen.blit(god_surface, god_rect)
    
    pygame.display.flip()
    
    # Wait for key press to end
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

def show_level_complete():
    font = pygame.font.Font(None, 72)
    small_font = pygame.font.Font(None, 28)
    text_surface = font.render("To be continued...", True, (200, 200, 200))
    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(text_surface, text_rect)

    continue_text = small_font.render("Press ENTER to continue...", True, GREY)
    continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
    screen.blit(continue_text, continue_rect)
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

def show_intro():
    intro_font = pygame.font.Font(None, 42)
    small_font = pygame.font.Font(None, 28)
    title_font = pygame.font.Font(None, 72)
    
    # Split the story into two parts: backstory and god dialogue
    backstory_lines = [
        "He was a marine, a husband, and a father.",
        "Then the world ended.",
        "Amidst the zombie apocalypse, his wife was bitten.",
        "To save their daughter, he made an impossible choice...",
        "He had to leave the woman he loved the most.",
        "In his darkest hour, a new calling emerged..."
    ]
    
    god_dialogue = [
        "The gods spoke as one:",
        "'Mortal, your suffering has not gone unnoticed.'",
        "'We have witnessed your sacrifice and your strength.'",
        "'The world has fallen to darkness, but you...'",
        "'...you have been chosen.'",
        "'We grant you power beyond mortal means.'",
        "'Use it to cleanse this world of the undead plague.'",
        "'But beware - the greatest test is yet to come...'"
    ]
    
    # Show backstory first
    screen.fill(BG_COLOR)
    
    # Draw title
    title_text = title_font.render("THE CHOSEN", True, (200, 50, 50))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, 80))
    screen.blit(title_text, title_rect)
    
    # Display backstory lines with fade-in effect
    for i, line in enumerate(backstory_lines):
        for alpha in range(0, 256, 10):
            screen.fill(BG_COLOR)
            screen.blit(title_text, title_rect)
            
            # Draw previous lines
            for j in range(i):
                prev_text = intro_font.render(backstory_lines[j], True, (200, 200, 200))
                prev_rect = prev_text.get_rect(center=(SCREEN_WIDTH / 2, 180 + j * 50))
                screen.blit(prev_text, prev_rect)
            
            # Draw current line with fade in
            text_surface = intro_font.render(line, True, (200, 200, 200))
            text_surface.set_alpha(alpha)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, 180 + i * 50))
            screen.blit(text_surface, text_rect)
            
            # Draw continue prompt
            if i == len(backstory_lines) - 1 and alpha > 150:  # Only show on last line
                continue_text = small_font.render("Press ENTER to continue...", True, (150, 150, 150))
                continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
                screen.blit(continue_text, continue_rect)
            
            pygame.display.flip()
            pygame.time.delay(20)
            
            # Check for skip
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    # Skip to god dialogue
                    return show_god_dialogue(god_dialogue)
    
    # Wait for player to continue to god dialogue
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
    
    # Show god dialogue
    show_god_dialogue(god_dialogue)

def show_god_dialogue(lines):
    intro_font = pygame.font.Font(None, 42)
    small_font = pygame.font.Font(None, 28)
    
    # Create a dark overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    
    for i, line in enumerate(lines):
        # Draw scene with overlay
        screen.fill(BG_COLOR)
        
        # Draw gods in the background (simplified for performance)
        for god in gods:
            pygame.draw.circle(screen, god['color'], (int(god['x']), int(god['y'])), god['radius'])
        
        screen.blit(overlay, (0, 0))
        
        # Draw dialogue box
        box_height = 200
        box_y = (SCREEN_HEIGHT - box_height) // 2
        pygame.draw.rect(screen, (30, 30, 60), (50, box_y, SCREEN_WIDTH - 100, box_height), border_radius=10)
        pygame.draw.rect(screen, (80, 80, 120), (50, box_y, SCREEN_WIDTH - 100, box_height), 2, border_radius=10)
        
        # Draw text with word wrap
        words = line.split(' ')
        wrapped_lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if intro_font.size(test_line)[0] < SCREEN_WIDTH - 200:  # Padding of 100px each side
                current_line.append(word)
            else:
                wrapped_lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            wrapped_lines.append(' '.join(current_line))
        
        # Draw each line of text
        for j, text in enumerate(wrapped_lines):
            text_surface = intro_font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(
                centerx=SCREEN_WIDTH // 2,
                y=box_y + 30 + j * (intro_font.get_height() + 10)
            )
            screen.blit(text_surface, text_rect)
        
        # Draw continue prompt
        if i == len(lines) - 1:
            continue_text = small_font.render("Press ENTER to begin your journey...", True, (200, 200, 255))
            continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + box_height - 40))
            screen.blit(continue_text, continue_rect)
        
        pygame.display.flip()
        
        # Wait for player to continue
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        waiting = False

def run_tutorial():
    # These are used in the function
    global bullets, player, game_map, current_level_runner, is_throne_room_level
    current_level_runner = run_tutorial
    
    # Initialize sounds with error handling
    try:
        shield_hit_sound = pygame.mixer.Sound("assets/music/shield_hit.ogg")
    except:
        shield_hit_sound = None
        print("Warning: Could not load shield_hit.ogg")
    
    try:
        damage_sound = pygame.mixer.Sound("assets/music/player_hurt.ogg")
    except:
        damage_sound = None
        print("Warning: Could not load player_hurt.ogg")

    player.reset()
    game_map = tutorial_map
    spawn_collectibles(game_map)
    is_throne_room_level = False
    
    player.x = MAP_WIDTH / 2 * TILE_SIZE
    player.y = (MAP_HEIGHT - 2) * TILE_SIZE
    player.angle = -math.pi / 2

    zombie = Zombie(MAP_WIDTH / 2 * TILE_SIZE, 2 * TILE_SIZE)
    # Wrap single tutorial zombie into a list so shared shield logic can damage it
    zombies = [zombie]

    tutorial_font = pygame.font.Font(None, 32)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                quit_game()
        
        handle_player_input(player, bullets, events)

        keys = pygame.key.get_pressed()
        update_player_state(player, keys, game_map, dt)
        
        # Check for collectible collision
        for collectible in collectibles[:]:
            dist_to_player = math.hypot(player.x - collectible['x'], player.y - collectible['y'])
            if dist_to_player < player.radius + COLLECTIBLE_SIZE / 2:
                create_collect_effect(collectible['x'], collectible['y'])
                if collect_sound:
                    collect_sound.play()
                collectibles.remove(collectible)

        # Update tutorial zombie
        for z in zombies[:]:
            if z.is_alive:
                z.update(player.x, player.y, game_map, dt)
            else:
                zombies.remove(z)
            
            # Zombie attacks player with damage over time
            dist_to_player = math.hypot(player.x - zombie.x, player.y - zombie.y)
            current_time = pygame.time.get_ticks()
            attack_cooldown = 1000  # 1 second between damage ticks
            
            if dist_to_player < player.radius + zombie.radius:
                if player.is_shielding and player.shield_energy > 0:
                    # Shield blocks damage but still drains energy
                    if current_time - zombie.last_attack_time > attack_cooldown:
                        player.shield_energy = max(0, player.shield_energy - 2)  # Reduced shield drain
                        zombie.last_attack_time = current_time
                        if shield_hit_sound is not None:
                            shield_hit_sound.play()
                elif current_time - zombie.last_attack_time > attack_cooldown:
                    # Deal damage over time when not shielding
                    player.take_damage(1)  # Small amount of damage per tick
                    zombie.last_attack_time = current_time
                    if damage_sound is not None:
                        damage_sound.play()

        # Update bullets and check for hits
        for bullet in bullets[:]:
            proj_speed = bullet.get('speed', BULLET_SPEED)
            bullet['x'] += math.cos(bullet['angle']) * proj_speed * dt
            # Use per-projectile speed
            proj_speed = bullet.get('speed', BULLET_SPEED)
            bullet['y'] += math.sin(bullet['angle']) * proj_speed * dt

            # Shield boomerang behaviour (delegated)
            if bullet.get('type') == 'shield':
                from shield_bullet import update_shield_bullet
                update_shield_bullet(bullet, bullets, dt, game_map, player, zombies if 'zombies' in locals() else None)
                continue
            # old shield logic below will be skipped for shield bullets
            if bullet.get('type') == 'shield':
                # Record trail
                trail = bullet['trail']
                trail.append((bullet['x'], bullet['y']))
                from settings import SHIELD_TRAIL_MAX_POINTS
                if len(trail) > SHIELD_TRAIL_MAX_POINTS:
                    trail.pop(0)

                # Bounce on wall (safe indexing)
                map_x = int(bullet['x'] / TILE_SIZE)
                map_y = int(bullet['y'] / TILE_SIZE)
                if 0 <= map_y < len(game_map) and 0 <= map_x < len(game_map[0]):
                    map_tile = game_map[map_y][map_x]
                    if map_tile in ['W', 'P']:
                        bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                else:
                    if bullet.get('type') == 'shield' and bullet.get('owner'):
                        bullet['owner'].active_shield_throw = False
                    if bullet in bullets:
                        bullets.remove(bullet)
                    continue

                # Bounce off zombies list if available
                if 'zombies' in locals():
                    for z in zombies:
                        if z.is_alive and math.hypot(z.x - bullet['x'], z.y - bullet['y']) < z.radius:
                            bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                            bullet['bounces'] = bullet.get('bounces', 0) + 1
                            if bullet['bounces'] >= 4:
                                bullet['returning'] = True
                            if z.take_damage(bullet['damage']):
                                if player.health <= player.max_health * 0.2:
                                    collectibles.append({'x': z.x, 'y': z.y, 'type': 'medkit', 'image': collectible_images['medkit']})
                            break
                owner = bullet.get('owner')
                if not owner:
                    bullets.remove(bullet)
                    continue
                if (not bullet.get('returning') and math.hypot(bullet['x'] - bullet['start_x'], bullet['y'] - bullet['start_y']) >= bullet['max_distance']):
                    bullet['returning'] = True
                if bullet.get('returning'):
                    dx = owner.x - bullet['x']
                    dy = owner.y - bullet['y']
                    bullet['angle'] = math.atan2(dy, dx)
                # Catch when close enough – expand radius by distance bullet can travel this frame to avoid tunnelling
                catch_radius = owner.radius + bullet.get('radius', 10) + bullet.get('speed', BULLET_SPEED) * dt
                if bullet.get('returning') and math.hypot(owner.x - bullet['x'], owner.y - bullet['y']) < catch_radius:
                    owner.active_shield_throw = False
                    bullets.remove(bullet)
                    continue

            if (bullet['x'] < 0 or bullet['x'] > SCREEN_WIDTH or
                    bullet['y'] < 0 or bullet['y'] > SCREEN_HEIGHT or
                    game_map[int(bullet['y'] / TILE_SIZE)][int(bullet['x'] / TILE_SIZE)] in ['W', 'P']):
                if bullet.get('type') == 'shield' and bullet.get('owner'):
                     bullet['owner'].active_shield_throw = False
                bullets.remove(bullet)
                continue

            if zombie.is_alive:
                dist_to_zombie = math.hypot(zombie.x - bullet['x'], zombie.y - bullet['y'])
                if dist_to_zombie < z.radius:
                    if bullet.get('type') == 'shield':
                        bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                    elif hasattr(zombie, 'take_damage'):
                        if zombie.take_damage(bullet.get('damage', 20)):
                            # Spawn medkit if player low health
                            if player.health <= player.max_health * 0.2:
                                collectibles.append({'x': z.x, 'y': z.y, 'type': 'medkit', 'image': collectible_images['medkit']})
                            zombie.is_alive = False
                        if bullet.get('type') == 'shield' and 'owner' in bullet and bullet['owner']:
                            bullet['owner'].active_shield_throw = False
                        bullets.remove(bullet)

        # Drawing
        screen.fill(BG_COLOR)
        draw_map()
        player.draw(screen)
        draw_collectibles()
        update_and_draw_particles(dt)
        if zombie.is_alive:
            zombie.draw(screen)
        draw_bullets()
        draw_ui_if_needed()

        # Tutorial Text
        tutorial_text_1 = tutorial_font.render("Use SPACE to SHOOT the zombie!", True, WHITE)
        tutorial_text_2 = tutorial_font.render("Use 'E' to RAISE your SHIELD!", True, WHITE)
        screen.blit(tutorial_text_1, (SCREEN_WIDTH / 2 - tutorial_text_1.get_width() / 2, 20))
        screen.blit(tutorial_text_2, (SCREEN_WIDTH / 2 - tutorial_text_2.get_width() / 2, 60))

        # Win/Loss Condition
        if not zombie.is_alive:
            run_post_tutorial_scene()
            running = False
        
        if player.health <= 0:
            stop_music(fade_out=500)
            # Special ending for dying to tutorial zombie
            from levels.death_endings import show_tutorial_death_ending
            show_tutorial_death_ending()
            # Show standard Game Over screen afterwards
            result = show_game_over_screen(show_restart_level=False)
            running = False
            if result == "MAIN_MENU":
                return "MAIN_MENU"

        pygame.display.flip()

    return "COMPLETE"

def run_post_tutorial_scene():
    global game_map
    game_map = post_tutorial_map
    spawn_collectibles(game_map)

    # Fade out the combat music for the cinematic
    stop_music(fade_out=1000)

    # Lock the player in the middle of the room, facing down
    player.x = MAP_WIDTH / 2 * TILE_SIZE
    player.y = (MAP_HEIGHT / 2) * TILE_SIZE
    player.angle = math.pi / 2
    
    # Phase 1: Human approaches
    human = Human(MAP_WIDTH / 2 * TILE_SIZE, (MAP_HEIGHT - 2) * TILE_SIZE)
    human_approaching = True
    while human_approaching:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

        human.update(player.x, player.y)

        if human.state == 'SCARED':
            human_approaching = False

        # Drawing
        screen.fill(BG_COLOR)
        draw_map()
        player.draw(screen)
        draw_collectibles()
        human.draw(screen)
        pygame.display.flip()

    # Phase 2: Gods appear and speak
    # A brief pause for effect as the human vanishes and gods appear
    screen.fill(BG_COLOR)
    draw_map()
    player.draw(screen)
    draw_collectibles()
    draw_gods() # The gods appear
    pygame.display.flip()
    pygame.time.delay(1000) # Pause for dramatic effect

    gods_dialogue = [
        "Gods: 'See how they look at you now, champion.'",
        "Gods: 'They do not see a savior. They see a MONSTER.'",
        "Gods: 'This is the price of your power. You walk a lonely path.'",
        "Gods: 'Now, your true test begins...'"
    ]
    show_dialogue(gods_dialogue)

    # Phase 3: Set game state to trigger boss fight through the main game loop
    global game_state
    game_state = "BOSS_FIGHT"

def run_boss_level():
    # These are used in the function
    global bullets, player, game_map, current_level_runner, is_throne_room_level
    current_level_runner = run_boss_level

    player.reset()
    game_map = boss_level_map
    spawn_collectibles(game_map)
    is_throne_room_level = False

    player.x = MAP_WIDTH / 2 * TILE_SIZE
    player.y = MAP_HEIGHT / 2 * TILE_SIZE
    player.angle = 0

    boss = PythonBoss()
    boss.max_trail_duration = 20.0  # Poison puddles last 20 seconds

    # Lists & timers for new boss mechanics
    zombies = []  # snake minions summoned by boss
    poison_timer = 0.0  # time until next poison puddle

    # Show the boss tutorial dialogue
    boss_intro_dialogue = [
        "A monstrous python appears!",
        "Aim for its head! The body is too thick to damage."
    ]
    show_dialogue(boss_intro_dialogue)

    play_music("boss_fight.ogg")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                quit_game()
        
        handle_player_input(player, bullets, events)

        keys = pygame.key.get_pressed()
        update_player_state(player, keys, game_map, dt)
        boss.update(player.x, player.y, game_map, dt)

        # --- Boss poison trail mechanic ---
        poison_timer -= dt
        if poison_timer <= 0:
            boss.poison_trail.append({'x': boss.segments[0]['x'], 'y': boss.segments[0]['y'], 'timer': boss.max_trail_duration})
            poison_timer = 0.4  # spawn puddle every 0.4s

        # Damage player if standing in poison puddle
        for puddle in boss.poison_trail:
            if math.hypot(player.x - puddle['x'], player.y - puddle['y']) < TILE_SIZE:
                # Poison puddle inflicts 20 damage per second
                player.take_damage(20 * dt)



        # Check for collectible collision
        for collectible in collectibles[:]:
            dist_to_player = math.hypot(player.x - collectible['x'], player.y - collectible['y'])
            if dist_to_player < player.radius + COLLECTIBLE_SIZE / 2:
                create_collect_effect(collectible['x'], collectible['y'])
                if collect_sound:
                    collect_sound.play()
                collectibles.remove(collectible)

        # Boss attacks player
        if boss.state in ['ATTACKING', 'ROAMING']:
            dist_to_player = math.hypot(player.x - boss.segments[0]['x'], player.y - boss.segments[0]['y'])
            if dist_to_player < player.radius + (TILE_SIZE // 2):
                player.take_damage(PYTHON_DAMAGE)
                boss.trigger_retreat(player.x, player.y) # Trigger retreat after a successful bite
        elif boss.state == 'CHARGING':
            # Check collision with entire body during charge
            for segment in boss.segments:
                dist_to_player = math.hypot(player.x - segment['x'], player.y - segment['y'])
                if dist_to_player < player.radius + (TILE_SIZE // 3):
                    player.take_damage(PYTHON_CHARGE_DAMAGE)
                    boss.trigger_retreat(player.x, player.y) # Also retreat after a charge hit
                    break
        
        # Update bullets and check for hits on boss
        for bullet in bullets[:]:
            proj_speed = bullet.get('speed', BULLET_SPEED)
            bullet['x'] += math.cos(bullet['angle']) * proj_speed * dt
            # Use per-projectile speed
            proj_speed = bullet.get('speed', BULLET_SPEED)
            bullet['y'] += math.sin(bullet['angle']) * proj_speed * dt

            # Shield boomerang behaviour (delegated)
            if bullet.get('type') == 'shield':
                from shield_bullet import update_shield_bullet
                update_shield_bullet(bullet, bullets, dt, game_map, player, zombies if 'zombies' in locals() else None)
                continue
            # old shield logic below will be skipped for shield bullets
            if bullet.get('type') == 'shield':
                # Record trail
                trail = bullet['trail']
                trail.append((bullet['x'], bullet['y']))
                from settings import SHIELD_TRAIL_MAX_POINTS
                if len(trail) > SHIELD_TRAIL_MAX_POINTS:
                    trail.pop(0)

                # Bounce on wall (safe indexing)
                map_x = int(bullet['x'] / TILE_SIZE)
                map_y = int(bullet['y'] / TILE_SIZE)
                if 0 <= map_y < len(game_map) and 0 <= map_x < len(game_map[0]):
                    map_tile = game_map[map_y][map_x]
                    if map_tile in ['W', 'P']:
                        bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                else:
                    if bullet.get('type') == 'shield' and bullet.get('owner'):
                        bullet['owner'].active_shield_throw = False
                    if bullet in bullets:
                        bullets.remove(bullet)
                    continue

                # Bounce off zombies list if available
                if 'zombies' in locals():
                    for z in zombies:
                        if z.is_alive and math.hypot(z.x - bullet['x'], z.y - bullet['y']) < z.radius:
                            bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                            bullet['bounces'] = bullet.get('bounces', 0) + 1
                            if bullet['bounces'] >= 4:
                                bullet['returning'] = True
                            if z.take_damage(bullet['damage']):
                                if player.health <= player.max_health * 0.2:
                                    collectibles.append({'x': z.x, 'y': z.y, 'type': 'medkit', 'image': collectible_images['medkit']})
                            break
                owner = bullet.get('owner')
                if not owner:
                    bullets.remove(bullet)
                    continue
                if (not bullet.get('returning') and math.hypot(bullet['x'] - bullet['start_x'], bullet['y'] - bullet['start_y']) >= bullet['max_distance']):
                    bullet['returning'] = True
                if bullet.get('returning'):
                    dx = owner.x - bullet['x']
                    dy = owner.y - bullet['y']
                    bullet['angle'] = math.atan2(dy, dx)
                # Catch when close enough – expand radius by distance bullet can travel this frame to avoid tunnelling
                catch_radius = owner.radius + bullet.get('radius', 10) + bullet.get('speed', BULLET_SPEED) * dt
                if bullet.get('returning') and math.hypot(owner.x - bullet['x'], owner.y - bullet['y']) < catch_radius:
                    owner.active_shield_throw = False
                    bullets.remove(bullet)
                    continue
            
            # Check for collision with walls
            if (bullet['x'] < 0 or bullet['x'] > SCREEN_WIDTH or
                bullet['y'] < 0 or bullet['y'] > SCREEN_HEIGHT or
                game_map[int(bullet['y'] / TILE_SIZE)][int(bullet['x'] / TILE_SIZE)] in ['W', 'P']):
                if bullet.get('type') == 'shield' and bullet.get('owner'):
                     bullet['owner'].active_shield_throw = False
                bullets.remove(bullet)
                continue

        # --- After bullet loop: reset shield flag if no projectile owned by player ---
        if player.active_shield_throw and not any(b.get('type')=='shield' and b.get('owner')==player for b in bullets):
             player.active_shield_throw = False

        # Check for collision with boss
        # Boss collision with non-shield bullets
        for bullet in bullets[:]:
            if boss.state in ['EMERGING', 'ATTACKING', 'ROAMING', 'TELEGRAPHING_CHARGE', 'CHARGING']:
                 dist_to_head = math.hypot(boss.segments[0]['x'] - bullet['x'], boss.segments[0]['y'] - bullet['y'])
                 if dist_to_head < TILE_SIZE // 2:
                     # Non-shield bullets damage boss and disappear
                     boss.take_damage(PLAYER_BULLET_DAMAGE)
                     bullets.remove(bullet)

        # Drawing
        screen.fill(BG_COLOR)
        draw_map()
        player.draw(screen)
        draw_collectibles()
        update_and_draw_particles(dt)
        boss.draw(screen)
        draw_bullets()
        draw_ui_if_needed()

        # Boss Health Bar
        boss_health_bar_width = SCREEN_WIDTH - 40
        health_ratio = boss.health / PYTHON_HEALTH
        pygame.draw.rect(screen, BOSS_HEALTH_BAR_BG, (20, 20, boss_health_bar_width, 30))
        pygame.draw.rect(screen, BOSS_HEALTH_BAR_FG, (20, 20, boss_health_bar_width * health_ratio, 30))

        # Win/Loss Condition
        if not boss.is_alive:
            running = False
            return "VICTORY"

        if player.health <= 0:
            stop_music(fade_out=500)
            from levels.death_endings import show_python_boss_death_ending
            show_python_boss_death_ending()
            # Standard Game Over screen without restart-level
            result = show_game_over_screen(show_restart_level=False)
            if result == "MAIN_MENU":
                return "MAIN_MENU"
            running = False
            return "GAME_OVER"

        pygame.display.flip()

# State variable to track which level is active
# This is used in the main game loop
current_level_runner = None  # This will be assigned when levels are run

def main_game():
    global current_level_runner
    current_level_runner = None  # Track current level function
    global game_map, is_throne_room_level, game_state, zombies, player, throne_room_end_triggered
    
    # Initialize game state
    game_state = "MAIN_MENU"
    player = Player()
    zombies = []
    throne_room_end_triggered = False
    is_throne_room_level = True
    
    # Main game loop
    running = True
    prev_game_state = None
    while running:
        dt = clock.tick(60) / 1000.0
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state in ["GAME", "OUTSIDE"]:
                        game_state = "PAUSED"
                    elif game_state == "PAUSED":
                        game_state = "GAME"
        
        # Clear the screen
        screen.fill(BLACK)
        
        # Game state machine
        if game_state == "MAIN_MENU":
            menu_result = show_main_menu()
            if menu_result == "START":
                prev_game_state = game_state
                game_state = "FAMILY_STORY"
                throne_room_end_triggered = False
                is_throne_room_level = True
            elif menu_result == "ENDLESS":
                prev_game_state = game_state
                game_state = "ENDLESS"
            elif menu_result == "QUIT":
                running = False
        
        elif game_state == "ENDLESS":
            game_objects = {'player': player, 'zombies': zombies}
            result = run_endless_mode(game_objects)
            player = Player()
            zombies = []
            game_state = "MAIN_MENU" if result == "MAIN_MENU" else result
        
        elif game_state == "FAMILY_STORY":
            prev_game_state = game_state
            # Show family backstory
            family_dialogue = [
                "You were once a simple farmer, living with your family...",
                "Until the day the undead hordes attacked your village.",
                "You fought bravely, but it wasn't enough...",
                "Your family... they didn't make it.",
                "Consumed by rage, you fought until you could fight no more..."
            ]
            show_dialogue(family_dialogue)
            game_state = "GOD_SUMMON"
        
        elif game_state == "GOD_SUMMON":
            prev_game_state = game_state
            # Show god summoning scene
            god_dialogue = [
                "The Gods of War have taken notice of your fury.",
                "They offer you a chance for vengeance...",
                "Become their champion, and you shall have the power",
                "to destroy the undead scourge once and for all!"
            ]
            show_dialogue(god_dialogue)
            game_state = "TUTORIAL"
        
        elif game_state == "TUTORIAL":
            prev_game_state = game_state
            # Zombie tutorial
            result = run_tutorial()
            if result == "COMPLETE":
                game_state = "BOSS_FIGHT"
            elif result == "MAIN_MENU":
                game_state = "MAIN_MENU"
        
        elif game_state == "BOSS_FIGHT":
            prev_game_state = game_state
            # Save level runner for restart
            current_level_runner = run_boss_level
            # Python Boss fight
            result = run_boss_level()
            if result == "VICTORY":
                game_state = "FAKE_DEATH"
            elif result == "MAIN_MENU":
                game_state = "MAIN_MENU"
            elif result == "GAME_OVER":
                # Save checkpoint for potential revival
                last_checkpoint = {
                    "level": current_level_runner,
                    "x": player.x,
                    "y": player.y,
                    "angle": player.angle
                }
                game_state = "GAME_OVER"
        
        elif game_state == "FAKE_DEATH":
            prev_game_state = game_state
            # Show wife revelation/fake death dialogue here
            death_dialogue = [
                "As you stand over the defeated Python Boss...",
                "You see something in its eyes... pain, suffering...",
                "For the first time, you feel doubt...",
                "The gods sense your hesitation...",
                "'You have failed us, champion...'",
                "The gods turn their power against you..."
            ]
            show_dialogue(death_dialogue)
            show_fake_death_screen()
            game_state = "SCIENTIST_SAVES"
            
        elif game_state == "SCIENTIST_SAVES":
            # Scientist saves the player in the lab
            game_objects = show_lab_scene(revival_mode=False)
            if game_objects and isinstance(game_objects, dict):
                game_state = "ZOMBIE_BLOOD_QUEST"
            else:
                game_state = "MAIN_MENU"  # Fallback if something goes wrong
        
        elif game_state == "ZOMBIE_BLOOD_QUEST":
            # Run the outside area with zombies for blood collection
            # Save level runner & checkpoint for future revivals
            from levels.outside_area import run_outside_area as run_outside
            current_level_runner = lambda: run_outside(game_objects)
            last_checkpoint = {
                "level": current_level_runner,
                "x": player.x,
                "y": player.y,
                "angle": player.angle
            }
            result = run_outside(game_objects)
            if result == "BLOOD_QUEST_COMPLETE":
                # Scientist scene already shown inside outside_area.
                game_state = "RUINED_SANCTUARY"
            elif result == "MAIN_MENU":
                game_state = "MAIN_MENU"  # Player died, return to main menu
            elif result == "GAME_OVER":
                # Save checkpoint for potential revival
                last_checkpoint = {
                    "level": current_level_runner,
                    "x": player.x,
                    "y": player.y,
                    "angle": player.angle
                }
                game_state = "GAME_OVER"
        elif game_state == "RUINED_SANCTUARY":
            from levels.ruined_sanctuary import run_ruined_sanctuary
            # Save level runner & checkpoint for revival
            current_level_runner = run_ruined_sanctuary
            last_checkpoint = {
                "level": current_level_runner,
                "x": player.x,
                "y": player.y,
                "angle": player.angle
            }
            result = run_ruined_sanctuary()
            if result == "VICTORY":
                game_state = "DIVINE_ARENA"
            elif result == "GAME_OVER":
                game_state = "GAME_OVER"
        
        elif game_state == "DIVINE_ARENA":
            from levels.divine_arena import run_divine_arena
            current_level_runner = run_divine_arena
            last_checkpoint = {
                "level": current_level_runner,
                "x": player.x,
                "y": player.y,
                "angle": player.angle
            }
            result = run_divine_arena()
            if result == "VICTORY":
                game_state = "FINAL_SCENE"  # Skip red boss fight
            elif result == "GAME_OVER":
                game_state = "GAME_OVER"
        

                
        elif game_state == "FINAL_SCENE":
            # Add your final scene logic here
            show_dialogue([
                "With the corrupted god defeated, the curse is lifted...",
                "The land begins to heal, and the undead return to rest.",
                "Your journey is complete, but the world will remember your name..."
            ])
            game_state = "MAIN_MENU"
                
        elif game_state == "GAME_OVER":
            # Allow revival if the player has already completed the blood quest OR
            # if they died in late-game levels (Ruined Sanctuary / Divine Arena).
            allow_revival = False
            if last_checkpoint is not None:
                level_name = last_checkpoint["level"].__name__
                if blood_quest_completed or level_name in ("run_ruined_sanctuary", "run_divine_arena"):
                    allow_revival = True
            
            # Show game over screen with revival option if available
            result = show_game_over_screen(show_revival=allow_revival)
            
            if result == "REVIVE" and allow_revival:
                # Reset core player survival stats (low health to encourage quest)
                player.health = max(20, player.max_health // 4)
                player.shield_energy = player.max_shield_energy // 2
                player.is_invincible = True
                player.invincible_timer = 180  # 3 seconds of invincibility

                # ----------------------------------------------------
                # NEW: Dedicated revival flow – send player to scientist
                # ----------------------------------------------------
                from levels.outside_area import run_outside_area  # local import to avoid circular deps

                game_objects = show_scientist_revival_scene()
                if game_objects and isinstance(game_objects, dict):
                    # Update player reference to the revived player instance
                    player = game_objects.get('player', player)
                    # Ensure the newly spawned player starts in a weakened state
                    player.health = max(20, player.max_health // 4)

                    # Launch outside area quest immediately
                    current_level_runner = lambda: run_outside_area(game_objects)
                    last_checkpoint = {
                        "level": current_level_runner,
                        "x": player.x,
                        "y": player.y,
                        "angle": player.angle
                    }
                    game_state = "ZOMBIE_BLOOD_QUEST"
                else:
                    game_state = "MAIN_MENU"
                    
            elif result == "MAIN_MENU":
                # Player chose to abandon the run and return to the title screen
                game_state = "MAIN_MENU"
            elif result == "RESTART_LEVEL":
                # Restart the level fresh
                if current_level_runner:
                    player.health = player.max_health
                    player.shield_energy = player.max_shield_energy
                    player.is_invincible = True
                    player.invincibility_timer = 2.0  # 2 seconds grace
                    # Resume whatever state triggered the game-over (e.g. BOSS_FIGHT or LEVEL_RUN)
                    try:
                        game_state = prev_game_state
                    except NameError:
                        game_state = "MAIN_MENU"
                else:
                    game_state = "MAIN_MENU"
            elif pygame.key.get_pressed()[pygame.K_q]:
                running = False
                
        elif game_state == "PAUSED":
            # Show pause menu
            font = pygame.font.Font(None, 74)
            text = font.render('PAUSED', True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
            screen.blit(text, text_rect)
            
            font = pygame.font.Font(None, 36)
            text = font.render('Press ESC to resume', True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
            screen.blit(text, text_rect)
            
            # Check for resume
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                game_state = "GAME"
                
        elif game_state == "GAME":
            # Main game logic
            handle_player_input(player, bullets, events)
            keys = pygame.key.get_pressed()
            update_player_state(player, keys, game_map, dt)
            
            # Check for collectible collision
            for collectible in collectibles[:]:
                dist_to_player = math.hypot(player.x - collectible['x'], player.y - collectible['y'])
                if dist_to_player < player.radius + COLLECTIBLE_SIZE / 2:
                    create_collect_effect(collectible['x'], collectible['y'])
                    if collect_sound:
                        collect_sound.play()
                    collectibles.remove(collectible)
            
            # Drawing code
            screen.fill(BG_COLOR)
            draw_floor_details()
            draw_map()
            draw_collectibles()
            update_and_draw_particles(dt)
            draw_gods()
            player.draw(screen)
            draw_ui_if_needed()
            
            # Level end check
            dist_to_end = math.hypot(player.x - THRONE_ROOM_END_POS[0], player.y - THRONE_ROOM_END_POS[1])
            if not throne_room_end_triggered and dist_to_end < END_LEVEL_RADIUS:
                throne_room_end_triggered = True
                quest_dialogue = [
                    "Marine! You have been chosen.",
                    "You are Earth's champion, our last hope against the tide of darkness.",
                    "But you are not yet ready for the trials ahead.",
                    "The path forward is fraught with peril beyond your understanding.",
                    "Take this divine gun and shield. Be empowered.",
                    "Now go, and save humanity."
                ]
                show_dialogue(quest_dialogue)
                power_up_effect()
                show_teleport_and_vision_scene()
                game_state = "SCIENTIST_SAVES"  # Go to scientist lab, not tutorial
                is_throne_room_level = False  # Prevent throne room logic/UI
                # Move player far from the throne room end to prevent retrigger
                player.x = 2 * TILE_SIZE
                player.y = 2 * TILE_SIZE
        
        # Update display
        pygame.display.flip()
    
    # Clean up
    pygame.quit()
    sys.exit()

def quit_game():
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()

def show_main_menu():
    # Play background music
    play_music("bgm.ogg")
    
    # Load background image
    try:
        background_img = pygame.image.load('assets/sprites/background.png').convert()
        background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except pygame.error as e:
        print(f"Warning: Could not load background image. Error: {e}")
        background_img = None
    
    # Load fonts
    title_font = pygame.font.Font('assets/fonts/Bloody.otf', 100) if pygame.font.get_fonts().count('bloody') else pygame.font.Font(None, 100)
    button_font = pygame.font.Font('assets/fonts/Bloody.otf', 60) if pygame.font.get_fonts().count('bloody') else pygame.font.Font(None, 60)
    
    # Load skull image for selection indicator
    try:
        skull_img = pygame.image.load('assets/sprites/skull.png').convert_alpha()
        skull_img = pygame.transform.scale(skull_img, (40, 40))
    except:
        skull_img = None
        print("Warning: Could not load skull image")
    
    # Menu state
    selected_option = 0  # 0 = Start, 1 = Exit
    
    # Button settings
    button_width, button_height = 400, 80
    start_button_rect = pygame.Rect(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT / 2, button_width, button_height)
    endless_button_rect = pygame.Rect(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT / 2 + 120, button_width, button_height)
    exit_button_rect = pygame.Rect(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT / 2 + 240, button_width, button_height)
    
    # Colors with minimal transparency for better visibility
    BLOOD_RED = (136, 8, 8, 150)  # More transparent
    HIGHLIGHT = (200, 0, 0, 180)  # More transparent
    
    # Create a very light overlay just for text readability
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 50))  # Very transparent to maximize background visibility
    
    # Create a surface for the title with a blood effect
    def create_blood_text(text, font, color, shadow_color=(100, 0, 0)):
        text_surface = font.render(text, True, shadow_color)
        final_surface = pygame.Surface((text_surface.get_width() + 4, text_surface.get_height() + 4), pygame.SRCALPHA)
        
        # Draw shadow
        for x, y in [(0, 0), (4, 4), (0, 4), (4, 0)]:
            final_surface.blit(text_surface, (x, y))
            
        # Draw main text
        text_surface = font.render(text, True, color)
        final_surface.blit(text_surface, (2, 2))
        
        return final_surface
        
    # Main menu loop
    title_toggle = False
    last_toggle_time = pygame.time.get_ticks()
    toggle_interval = 3000  # 3 seconds
    while True:
        current_time = pygame.time.get_ticks()
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        # Toggle the title every 3 seconds
        if current_time - last_toggle_time > toggle_interval:
            title_toggle = not title_toggle
            last_toggle_time = current_time

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "QUIT"
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        return "START"
                    elif selected_option == 1:
                        return "ENDLESS"
                    else:
                        return "QUIT"
                elif event.key == pygame.K_DOWN or event.key == pygame.K_UP:
                    if event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % 3
                    else:
                        selected_option = (selected_option - 1) % 3
            
            # Mouse click handling
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button_rect.collidepoint(mouse_pos):
                    return "START"
                elif endless_button_rect.collidepoint(mouse_pos):
                    return "ENDLESS"
                elif exit_button_rect.collidepoint(mouse_pos):
                    return "QUIT"
        
        # Update mouse hover
        if start_button_rect.collidepoint(mouse_pos):
            selected_option = 0
        elif endless_button_rect.collidepoint(mouse_pos):
            selected_option = 1
        elif exit_button_rect.collidepoint(mouse_pos):
            selected_option = 2
        
        # Draw everything
        if background_img:
            screen.blit(background_img, (0, 0))
        screen.blit(overlay, (0, 0))

        # Draw title with blood effect
        if not title_toggle:
            title_text = create_blood_text("ZOMBIE APOCALYPSE", title_font, BLOOD_RED)
            screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, 100))
        else:
            title_text = create_blood_text("BATTLE AFTERMATH", title_font, (200, 0, 0))
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))
            pulse = math.sin(pygame.time.get_ticks() * 0.002) * 5
            title_rect.y += int(pulse)
            screen.blit(title_text, title_rect)
        
        # Draw buttons
        pygame.draw.rect(screen, HIGHLIGHT if selected_option == 0 else BLOOD_RED, start_button_rect, 0, 10)
        pygame.draw.rect(screen, HIGHLIGHT if selected_option == 1 else BLOOD_RED, endless_button_rect, 0, 10)
        pygame.draw.rect(screen, HIGHLIGHT if selected_option == 2 else BLOOD_RED, exit_button_rect, 0, 10)
        
        # Draw button text
        start_text = button_font.render("STORY MODE", True, WHITE)
        endless_text = button_font.render("ENDLESS MODE", True, WHITE)
        exit_text = button_font.render("EXIT", True, WHITE)
        
        screen.blit(start_text, (start_button_rect.centerx - start_text.get_width()/2, 
                                start_button_rect.centery - start_text.get_height()/2))
        screen.blit(endless_text, (endless_button_rect.centerx - endless_text.get_width()/2, 
                                  endless_button_rect.centery - endless_text.get_height()/2))
        screen.blit(exit_text, (exit_button_rect.centerx - exit_text.get_width()/2, 
                               exit_button_rect.centery - exit_text.get_height()/2))
        
        # Draw skull indicator if available
        if skull_img:
            if selected_option == 0:
                target_rect = start_button_rect
            elif selected_option == 1:
                target_rect = endless_button_rect
            else:
                target_rect = exit_button_rect
            screen.blit(skull_img, (target_rect.left - 50, target_rect.centery - 20))
            screen.blit(pygame.transform.flip(skull_img, True, False), (target_rect.right + 10, target_rect.centery - 20))
        
        pygame.display.flip()

if __name__ == '__main__':
    main_game()