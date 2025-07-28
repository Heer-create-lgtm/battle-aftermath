import pygame
import random
import math
from shield_bullet import update_shield_bullet, draw_shield_bullet
import sys
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, WHITE, MAX_HEALTH, MAX_STAMINA,
    PLAYER_MAX_AMMO, PLAYER_MAX_SHIELD_ENERGY, HEALTH_BAR_BG, HEALTH_BAR_FG,
    STAMINA_BAR_BG, STAMINA_BAR_FG, SHIELD_BAR_BG, SHIELD_BAR_FG, UI_PANEL_BG,
    BULLET_SPEED, ZOMBIE_DAMAGE, BULLET_COLOR, BULLET_RADIUS
)
from zombie import Zombie
from player import Player
from levels.dialogue import show_dialogue
from ui import draw_ui
from mechanics import handle_player_input, update_player_state

# These will be set when the function is called
fade_to_black = None
fade_in_from_black = None

def show_lab_scene(revival_mode=False, revival_count=0):
    """Show the lab scene where the scientist revives the player."""
    global fade_to_black, fade_in_from_black
    
    # Initialize bullets list for this scene
    bullets = []
    
    # Import these here to avoid circular imports
    from main import fade_to_black as main_fade_to_black, fade_in_from_black as main_fade_in_from_black
    fade_to_black = main_fade_to_black
    fade_in_from_black = main_fade_in_from_black
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # Initialize a new player instance for this scene
    player = Player()

    # If in revival mode, we skip collectible/pillar logic
    if revival_mode:
        pillars = []
        broken_pillars = []
        collectible_img = collectible_rect = None
        collectible_collected = collectible_visible = False
    
    # Load and resize sprites
    try:
        # Load and resize scientist
        scientist_img = pygame.image.load('assets/sprites/scientist.png').convert_alpha()
        scientist_img = pygame.transform.scale(scientist_img, (20, 20))
        scientist_rect = scientist_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        
        # Load and resize collectible (initially hidden)
        collectible_img = pygame.image.load('assets/sprites/collection3.png').convert_alpha()
        collectible_img = pygame.transform.scale(collectible_img, (20, 20))
        collectible_rect = collectible_img.get_rect(center=(0, 0))  # Start hidden
        collectible_collected = False
        collectible_visible = False  # Will be set to True when pillar is broken
        
        # Pillar positions (x, y, width, height, is_breakable, has_collectible)
        pillars = [
            (100, 100, 30, 30, False, False),  # Top-left pillar (unbreakable)
            (SCREEN_WIDTH - 130, 100, 30, 30, True, False),  # Top-right pillar (breakable)
            (100, SCREEN_HEIGHT - 130, 30, 30, True, True),  # Bottom-left pillar (hides collectible)
            (SCREEN_WIDTH - 130, SCREEN_HEIGHT - 130, 30, 30, False, False)  # Bottom-right pillar (unbreakable)
        ]
        
        # Track which pillars are broken
        broken_pillars = [False] * len(pillars)
        
    except Exception as e:
        print(f"Error loading assets: {e}")
        scientist_img = None
        scientist_rect = None
        collectible_img = None
        collectible_rect = None
        collectible_collected = True
        collectible_visible = False
        pillars = []
        broken_pillars = []
    
    # Create a more detailed lab background
    lab_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    # Draw lab background - dark blue-gray
    lab_bg.fill((30, 30, 40, 255))
    
    # Draw floor tiles
    for y in range(0, SCREEN_HEIGHT, 40):
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.rect(lab_bg, (40, 40, 50, 255), (x, y, 40, 40), 1)
    
    # Draw lab exit door at bottom center with more detail
    exit_door_rect = pygame.Rect(SCREEN_WIDTH//2 - 40, SCREEN_HEIGHT - 120, 80, 40)
    pygame.draw.rect(lab_bg, (100, 60, 30, 255), exit_door_rect)  # Brown door
    pygame.draw.rect(lab_bg, (120, 80, 40, 255), exit_door_rect, 2)  # Door frame
    
    # Draw lab equipment and pillars
    for i, (x, y, w, h, _, _) in enumerate(pillars):
        if not broken_pillars[i]:
            # Draw bullet / shield
            pygame.draw.rect(lab_bg, (100, 100, 120), (x, y, w, h))
            # Draw pillar details
            pygame.draw.rect(lab_bg, (70, 70, 90), (x, y, w, h), 2)
            pygame.draw.rect(lab_bg, (90, 90, 110), (x + 5, y + 5, w - 10, h - 10))
    
    # Position the scientist in the lab - no name tag needed
    pygame.draw.rect(lab_bg, (70, 70, 80, 255), (100, 200, 300, 200))  # Main table
    pygame.draw.rect(lab_bg, (120, 120, 130, 255), (100, 200, 300, 20))  # Table edge
    
    # Draw computer setup
    pygame.draw.rect(lab_bg, (150, 150, 170, 255), (150, 150, 100, 50))  # Monitor
    pygame.draw.rect(lab_bg, (180, 180, 200, 255), (160, 160, 80, 30))  # Screen
    pygame.draw.rect(lab_bg, (100, 100, 120, 255), (180, 200, 40, 30))  # Keyboard
    
    # Draw cabinet with details
    pygame.draw.rect(lab_bg, (200, 200, 200, 255), (350, 250, 100, 200))  # Cabinet
    pygame.draw.rect(lab_bg, (180, 180, 180, 255), (350, 250, 100, 15))  # Top shelf
    pygame.draw.rect(lab_bg, (180, 180, 180, 255), (350, 350, 100, 15))  # Middle shelf
    
    # ----------------- Interactive surprise objects -----------------
    cabinet_rect = pygame.Rect(350, 250, 100, 200)
    cabinet_broken = False  # Will turn True when player shoots the cabinet
    healthpack_rect = pygame.Rect(cabinet_rect.centerx - 10, cabinet_rect.bottom - 30, 20, 20)
    healthpack_visible = False
    healthpack_collected = False
    
    # Draw lab equipment on the table
    pygame.draw.rect(lab_bg, (180, 180, 200, 255), (120, 220, 40, 40))  # Microscope
    pygame.draw.ellipse(lab_bg, (200, 200, 220, 255), (130, 220, 20, 15))  # Microscope head
    
    # Draw test tubes in a rack
    for i in range(3):
        tube_rect = pygame.Rect(220 + i*30, 230, 15, 30)
        pygame.draw.rect(lab_bg, (200, 200, 255, 150), tube_rect)
        pygame.draw.rect(lab_bg, (180, 180, 200, 200), tube_rect, 1)  # Outline
    
    if not revival_mode:
        # Add collectible to the global collectibles list
        from main import collectibles, COLLECTIBLE_SIZE, collect_sound, create_collect_effect, update_and_draw_particles
    
    # Clear any existing collectibles
    collectibles.clear()
    
    # Add the lab collectible (collection3)
    collectible = {
        'x': SCREEN_WIDTH - 100,
        'y': 300,
        'type': '3',  # Use collection3.png
        'collected': False
    }
    collectibles.append(collectible)
    
    # Fade in
    for alpha in range(0, 256, 5):
        temp_surface = lab_bg.copy()
        temp_surface.set_alpha(alpha)
        screen.blit(temp_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(15)

    # Initialize player with normal stats
    player.x = SCREEN_WIDTH // 2
    player.y = SCREEN_HEIGHT // 2 + 100  # Start lower on the screen
    player.angle = -math.pi / 2  # Face up
    
    # Reset player stats after revival - set health to minimum (one hit from death)
    player.health = ZOMBIE_DAMAGE  # Set health to be exactly one hit from death
    player.ammo = PLAYER_MAX_AMMO
    player.is_reloading = False
    player.is_shielding = False
    player.stamina = 100
    player.is_invincible = False
    
    # Reset any power-ups or temporary effects
    # if hasattr(player, 'power_up_timer'):
    #     player.power_up_timer = 0
    # if hasattr(player, 'speed_boost'):
    #     player.speed_boost = 1.0
    # if hasattr(player, 'damage_boost'):
    #     player.damage_boost = 1.0
    
    # Scientist position (top center of the screen)
    if scientist_rect:
        scientist_rect.topleft = (SCREEN_WIDTH//2 - 40, 50)

    # Scientist dialogue with the scientist visible
    if revival_mode:
        # Simple variation depending on revival_count
        variant = revival_count % 3
        if variant == 0:
            scientist_lines = [
                ("Scientist: You're back. Let's stabilize you quickly.", True),
                ("Scientist: Step through the door once the dizziness fades.", True)
            ]
        elif variant == 1:
            scientist_lines = [
                ("Scientist: Hold still… administering serum.", True),
                ("Scientist: All set. Return to the field when ready.", True)
            ]
        else:
            scientist_lines = [
                ("Scientist: Another close call. Your resilience is astounding.", True),
                ("Scientist: The cure holds—exit when you feel strong enough.", True)
            ]
    else:
        scientist_lines = [
        ("Scientist: Ah, you're finally awake! I found you near the battlefield.", True),
        ("Scientist: I've stabilized your condition, but we're in grave danger.", True),
        ("Scientist: The infection is spreading rapidly. We need a cure, and fast.", True),
        ("Scientist: I need you to collect blood samples from 5 infected.", True),
        ("Scientist: The door behind you leads outside where they roam.", True),
        ("Scientist: Walk to the door at the bottom to exit the lab.", True),
        ("Scientist: Be extremely careful - they're more aggressive than before.", True),
        ("Scientist: I'll be monitoring from here. Good luck!", True)
    ]
    
    # Show the lab background, scientist, and player
    screen.blit(lab_bg, (0, 0))
    if scientist_img and scientist_rect:
        screen.blit(scientist_img, scientist_rect.topleft)
    else:
        # Fallback if no scientist image
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(SCREEN_WIDTH//2 - 40, 50, 80, 100))
    
    # Draw a name tag
    font = pygame.font.Font(None, 24)
    name_text = font.render("Dr. Aldric", True, (255, 255, 255))
    if scientist_rect:
        name_rect = name_text.get_rect(center=(scientist_rect.centerx, scientist_rect.bottom + 15))
        screen.blit(name_text, name_rect)
    
    player.draw(screen)
    pygame.display.flip()
    
    # Show dialogue in god dialogue style
    for line, _ in scientist_lines:
        # Create a dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        
        # Draw the lab scene in the background
        screen.blit(lab_bg, (0, 0))
        if not collectible_collected and collectible_rect and collectible_img:
            screen.blit(collectible_img, collectible_rect.topleft)
        if scientist_img and scientist_rect:
            screen.blit(scientist_img, scientist_rect.topleft)
        player.draw(screen)
        
        # Apply the overlay
        screen.blit(overlay, (0, 0))
        
        # Setup fonts and dialogue box
        intro_font = pygame.font.Font(None, 42)
        small_font = pygame.font.Font(None, 28)
        
        # Draw dialogue box at bottom (like throne room)
        box_height = 120
        box_y = SCREEN_HEIGHT - box_height - 20
        box_x = 100
        box_width = SCREEN_WIDTH - 200
        
        # Draw box with border
        pygame.draw.rect(screen, (30, 30, 60), (box_x-2, box_y-2, box_width+4, box_height+4), border_radius=8)
        pygame.draw.rect(screen, (30, 30, 60, 220), (box_x, box_y, box_width, box_height), border_radius=6)
        pygame.draw.rect(screen, (80, 80, 120), (box_x, box_y, box_width, box_height), 2, border_radius=6)
        
        # Draw speaker name (Scientist:) at top left
        speaker = "Dr. Aldric:" if line.startswith("Scientist:") else ""
        speaker_text = intro_font.render(speaker, True, (200, 200, 255))
        screen.blit(speaker_text, (box_x + 30, box_y + 20))
        
        # Draw the actual dialogue text with word wrap
        display_text = line.replace("Scientist: ", "") if line.startswith("Scientist:") else line
        words = display_text.split(' ')
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
                x=box_x + 30,
                y=box_y + 60 + j * (intro_font.get_height() + 5)
            )
            screen.blit(text_surface, text_rect)
        
        # Draw continue prompt at bottom right
        continue_text = small_font.render("Press ENTER to continue...", True, (200, 200, 255))
        continue_rect = continue_text.get_rect(bottomright=(box_x + box_width - 20, box_y + box_height - 20))
        screen.blit(continue_text, continue_rect)
        
        pygame.display.flip()
        
        # Wait for player to continue
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        waiting = False
                        break
            clock.tick(60)

    # Main lab loop - wait for player to reach exit
    running = True
    
    # Flicker effect variables removed
    game_map = [[' ' for _ in range(SCREEN_WIDTH // TILE_SIZE + 1)] for _ in range(SCREEN_HEIGHT // TILE_SIZE + 1)]

    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        keys = pygame.key.get_pressed()
        
        # Handle shooting and other input events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        handle_player_input(player, bullets, events)
        update_player_state(player, keys, game_map, dt)

        # Keep player in bounds
        player.x = max(player.radius, min(SCREEN_WIDTH - player.radius, player.x))
        player.y = max(player.radius, min(SCREEN_HEIGHT - player.radius, player.y))

        # Update bullets
        for bullet in bullets[:]:
            bullet['x'] += math.cos(bullet['angle']) * BULLET_SPEED * dt
            bullet['y'] += math.sin(bullet['angle']) * BULLET_SPEED * dt
            if bullet.get('type') == 'shield':
                update_shield_bullet(bullet, bullets, dt, game_map, player, zombies=None)
            
            if not (0 < bullet['x'] < SCREEN_WIDTH and 0 < bullet['y'] < SCREEN_HEIGHT):
                if bullet.get('type') == 'shield' and bullet.get('owner'):
                    bullet['owner'].active_shield_throw = False
                bullets.remove(bullet)
                continue
            
            bullet_rect = pygame.Rect(bullet['x'] - 2, bullet['y'] - 2, 4, 4)
            
            # Check for pillar collisions
            for i, (x, y, w, h, is_breakable, has_collectible) in enumerate(pillars):
                if not broken_pillars[i] and is_breakable and bullet_rect.colliderect(pygame.Rect(x, y, w, h)):
                    if bullet in bullets:
                        if bullet.get('type') == 'shield' and bullet.get('owner'):
                            bullet['owner'].active_shield_throw = False
                    bullets.remove(bullet)
                    broken_pillars[i] = True
                    if has_collectible and not collectible_collected and not collectible_visible:
                        collectible_visible = True
                        if collectible_rect:
                            collectible_rect.center = (x + w//2, y + h//2)
                    break
            
            # Check for cabinet collision (hidden surprise)
            if not cabinet_broken and bullet_rect.colliderect(cabinet_rect):
                if bullet in bullets:
                    if bullet.get('type') == 'shield' and bullet.get('owner'):
                        bullet['owner'].active_shield_throw = False
                bullets.remove(bullet)
                cabinet_broken = True
                healthpack_visible = True
                create_collect_effect(cabinet_rect.centerx, cabinet_rect.centery)
                continue
        
        # Check collectible collision if visible
        if collectible_visible and not collectible_collected and collectible_rect:
            player_rect = pygame.Rect(player.x - player.radius, player.y - player.radius, player.radius * 2, player.radius * 2)
            if player_rect.colliderect(collectible_rect):
                collectible_collected = True
                if collect_sound:
                    collect_sound.play()
                if collectible_rect:
                    create_collect_effect(collectible_rect.centerx, collectible_rect.centery)
        
        # ---------- Healthpack pickup ----------
        if healthpack_visible and not healthpack_collected:
            player_rect_hp = pygame.Rect(player.x - player.radius, player.y - player.radius, player.radius * 2, player.radius * 2)
            if player_rect_hp.colliderect(healthpack_rect):
                healthpack_collected = True
                healthpack_visible = False
                player.health = min(MAX_HEALTH, player.health + 20)
                create_collect_effect(healthpack_rect.centerx, healthpack_rect.centery)
                if collect_sound:
                    collect_sound.play()
        
        # Check if player reached the exit
        player_rect = pygame.Rect(player.x - 10, player.y - 10, 20, 20)
        if player_rect.colliderect(exit_door_rect):
            try:
                door_sound = pygame.mixer.Sound('assets/music/door.ogg')
                door_sound.play()
            except Exception as e:
                print(f"Could not play door sound: {e}")
            pygame.time.delay(500)
            running = False

        # Drawing
        screen.blit(lab_bg, (0, 0))
        
        # Flicker effect removed as requested
        pass
        
        # Draw broken cabinet overlay and healthpack if required
        if cabinet_broken:
            pygame.draw.rect(screen, (120, 120, 120), cabinet_rect)
            pygame.draw.line(screen, WHITE, cabinet_rect.topleft, cabinet_rect.bottomright, 2)
            pygame.draw.line(screen, WHITE, cabinet_rect.topright, cabinet_rect.bottomleft, 2)
        if healthpack_visible and not healthpack_collected:
            pygame.draw.rect(screen, (200, 50, 50), healthpack_rect)
            pygame.draw.rect(screen, WHITE, healthpack_rect, 2)
        draw_ui(screen, player)
        update_and_draw_particles(dt)

        if collectible_visible and not collectible_collected and collectible_rect and collectible_img:
            screen.blit(collectible_img, collectible_rect.topleft)
        
        if scientist_img and scientist_rect:
            screen.blit(scientist_img, scientist_rect.topleft)
            
        for bullet in bullets:
            draw_shield_bullet(screen, bullet) if bullet.get('type') == 'shield' else pygame.draw.circle(screen, BULLET_COLOR, (int(bullet['x']), int(bullet['y'])), BULLET_RADIUS)
            
        player.draw(screen)
        
        if abs(player.x - exit_door_rect.centerx) < 100 and abs(player.y - exit_door_rect.centery) < 100:
            pygame.draw.rect(screen, (255, 255, 100, 100), exit_door_rect.inflate(10, 10), 3)
        
        font = pygame.font.Font(None, 24)
        if not revival_mode:
            instructions = font.render("Walk to the door at the bottom to exit the lab", True, (255, 255, 255))
            screen.blit(instructions, (SCREEN_WIDTH//2 - instructions.get_width()//2, 20))
        
        pygame.display.flip()
    
    # Fade to black when exiting lab
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill((0, 0, 0))
    for alpha in range(0, 256, 10):
        fade_surface.set_alpha(alpha)
        screen.blit(lab_bg, (0, 0))
        player.draw(screen)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)
    
    # Create the outside environment
    outside_map = create_outside_environment()
    
    # Initialize player in the outside area - position at the lab entrance
    # Position player at the center of the screen
    player.x = SCREEN_WIDTH // 2
    player.y = SCREEN_HEIGHT - 100  # Near bottom of the screen with some margin
    player.angle = -math.pi / 2  # Facing up (towards the lab)
    player.zombie_blood_collected = 0
    
    # Spawn zombies
    zombies = []
    max_attempts = 50
    for _ in range(8):
        spawned = False
        attempts = 0
        while not spawned and attempts < max_attempts:
            x = random.randint(2, len(outside_map[0]) - 3) * TILE_SIZE
            y = random.randint(2, len(outside_map) - 3) * TILE_SIZE
            map_x, map_y = int(x / TILE_SIZE), int(y / TILE_SIZE)
            
            valid_position = True
            if not (outside_map[map_y][map_x] in [' ', 'p'] and abs(x - player.x) > 100 and abs(y - player.y) > 100):
                valid_position = False
            
            if valid_position:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if not (0 <= map_x + dx < len(outside_map[0]) and 0 <= map_y + dy < len(outside_map) and outside_map[map_y + dy][map_x + dx] in [' ', 'p']):
                            valid_position = False
                            break
                    if not valid_position:
                        break
            
            if valid_position:
                zombies.append(Zombie(x, y))
                spawned = True
            attempts += 1
    
    # Fade in from black
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill((0, 0, 0))
    for alpha in range(255, -1, -10):
        fade_surface.set_alpha(alpha)
        draw_outside_environment(screen, outside_map)
        player.draw(screen)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)
    
    show_dialogue(["Objective: Collect 5 zombie blood samples by defeating zombies.", "Return to the lab entrance when done."])
    
    return {
        'player': player,
        'zombies': zombies,
        'map': outside_map,
        'map_data': outside_map,
        'game_state': 'ZOMBIE_BLOOD_QUEST',
        'draw_environment': lambda: draw_outside_environment(screen, outside_map)
    }

def show_outside_scene():
    """Show the outside area where the zombie fight happens."""
    # This will be used to set up the outside environment
    pass

def create_outside_environment():
    """Create the outside environment with roads, flowers, and bushes."""
    # Create a new map for the outside area (40x30 tiles)
    map_width, map_height = 40, 30
    outside_map = [[' ' for _ in range(map_width)] for _ in range(map_height)]
    
    # Draw boundary walls
    for x in range(map_width):
        outside_map[0][x] = 'W'  # Top wall
        outside_map[map_height-1][x] = 'W'  # Bottom wall
    for y in range(map_height):
        outside_map[y][0] = 'W'  # Left wall
        outside_map[y][map_width-1] = 'W'  # Right wall
    
    # Add some paths (p = path)
    path_width = 4
    # Main horizontal path
    for x in range(5, map_width - 5):
        for w in range(path_width):
            outside_map[map_height//2 + w - path_width//2][x] = 'p'
    # Vertical path to lab
    for y in range(map_height//2, map_height - 5):
        for w in range(path_width):
            outside_map[y][map_width//2 + w - path_width//2] = 'p'
    
    # Add some obstacles (trees, rocks, etc.)
    def place_obstacle(x, y, width, height, char='T'):
        for dy in range(height):
            for dx in range(width):
                if 0 <= y+dy < map_height and 0 <= x+dx < map_width:
                    if outside_map[y+dy][x+dx] == ' ':
                        outside_map[y+dy][x+dx] = char
    
    # Place some trees (T)
    for _ in range(15):
        x = random.randint(2, map_width-4)
        y = random.randint(2, map_height-4)
        if outside_map[y][x] == ' ' and not any(cell != ' ' for row in outside_map[y-1:y+2] for cell in row[x-1:x+2]):
            outside_map[y][x] = 'T'
    
    # Place some rocks (R)
    for _ in range(10):
        x = random.randint(2, map_width-3)
        y = random.randint(2, map_height-3)
        if outside_map[y][x] == ' ' and not any(cell != ' ' for row in outside_map[y-1:y+2] for cell in row[x-1:x+2]):
            outside_map[y][x] = 'R'
    
    # Place some bushes (B) - zombies can walk through these but players can't
    for _ in range(20):
        x = random.randint(2, map_width-3)
        y = random.randint(2, map_height-3)
        if outside_map[y][x] == ' ' and not any(cell != ' ' for row in outside_map[y-1:y+2] for cell in row[x-1:x+2]):
            outside_map[y][x] = 'B'
    
    # Ensure lab entrance is clear (where player spawns)
    lab_entrance_x, lab_entrance_y = map_width//2, map_height - 5
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if 0 <= lab_entrance_y+dy < map_height and 0 <= lab_entrance_x+dx < map_width:
                outside_map[lab_entrance_y+dy][lab_entrance_x+dx] = 'p'
    
    return outside_map

def draw_outside_environment(screen, map_data):
    """Draw the outside environment with proper visuals for paths, walls, and obstacles."""
    # Draw base grass first
    grass_color = (50, 120, 50)
    screen.fill(grass_color)
    
    # Draw a grid pattern for the grass
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(screen, (60, 110, 40), (0, y), (SCREEN_WIDTH, y), 1)
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(screen, (60, 110, 40), (x, 0), (x, SCREEN_HEIGHT), 1)
    
    # Draw map elements
    for y, row in enumerate(map_data):
        for x, cell in enumerate(row):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            
            if cell == 'W':  # Wall (stone wall)
                pygame.draw.rect(screen, (100, 100, 100), rect)
                # Add some texture to the wall
                pygame.draw.rect(screen, (80, 80, 80), rect.inflate(-4, -4), 1)
                
            elif cell == 'p':  # Path (dirt)
                path_color = (139, 119, 101)  # Dirt color
                pygame.draw.rect(screen, path_color, rect)
                # Add some texture to the path
                if (x + y) % 2 == 0:
                    pygame.draw.rect(screen, (129, 109, 91), rect.inflate(-2, -2))
                
            elif cell == 'T':  # Tree
                # Tree trunk
                trunk_rect = pygame.Rect(rect.centerx - 5, rect.centery - 5, 10, 20)
                pygame.draw.rect(screen, (101, 67, 33), trunk_rect)
                # Tree leaves (top part)
                leaf_radius = TILE_SIZE
                leaf_rect = pygame.Rect(rect.centerx - leaf_radius//2, rect.centery - leaf_radius + 10, 
                                      leaf_radius, leaf_radius)
                pygame.draw.ellipse(screen, (34, 139, 34), leaf_rect)
                
            elif cell == 'R':  # Rock
                pygame.draw.ellipse(screen, (100, 100, 100), rect.inflate(-5, -5))
                # Add some highlights
                highlight = pygame.Rect(rect.left + 5, rect.top + 5, 
                                      rect.width // 2, rect.height // 2)
                pygame.draw.ellipse(screen, (150, 150, 150), highlight.inflate(-5, -5))
                
            elif cell == 'B':  # Bush
                # Draw a simple bush shape
                pygame.draw.ellipse(screen, (0, 100, 0), rect.inflate(-5, -5))
                # Add some highlights
                highlight = pygame.Rect(rect.left + 5, rect.top + 5, 
                                     rect.width // 2, rect.height // 2)
                pygame.draw.ellipse(screen, (0, 150, 0), highlight.inflate(-5, -5))
