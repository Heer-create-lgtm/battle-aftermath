import pygame
import random
import math
from shield_bullet import update_shield_bullet, draw_shield_bullet
import sys
from settings import (
    TILE_SIZE, PLAYER_MAX_AMMO, MAX_HEALTH, PLAYER_BULLET_DAMAGE, HEALTH_BAR_FG, HEALTH_BAR_BG,
    STAMINA_BAR_FG, STAMINA_BAR_BG, MAX_STAMINA, SHIELD_BAR_FG, SHIELD_BAR_BG,
    PLAYER_MAX_SHIELD_ENERGY, UI_PANEL_BG, WHITE, SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, ZOMBIE_DAMAGE, BULLET_COLOR, BULLET_RADIUS, BULLET_SPEED
)
from zombie import Zombie
from special_zombies import random_zombie
from player import Player, shield_hit_sound
from levels.dialogue import show_dialogue
from levels.scientist_scenes import check_zombie_blood_quest
from ui import draw_ui
from levels.failure_ending import show_failure_ending
from mechanics import handle_player_input, update_player_state

def run_outside_area(game_objects):
    """Run the outside area where the player fights zombies."""
    player = game_objects['player']
    zombies = game_objects['zombies']
    game_map = game_objects['map']
    
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    bullets = []
    shake_timer = 0.0
    flash_timer = 0.0  # white flash duration
    # ---------- ENVIRONMENT SETUP ----------
    # Load collect sound with channel management
    collect_sound = None
    try:
        from main import play_sound_effect
        collect_sound = lambda: play_sound_effect('reload.ogg', volume=0.7)
    except Exception as e:
        print(f"Could not load collect sound: {e}")
    # Load hidden collectible image & crate
    try:
        collection_img = pygame.image.load('assets/sprites/collection4.png').convert_alpha()
    except pygame.error:
        collection_img = None
    try:
        crate_img = pygame.image.load('assets/sprites/crate.png').convert_alpha()
    except pygame.error:
        crate_img = None

    crate = {
        'x': SCREEN_WIDTH//2 + 120,
        'y': SCREEN_HEIGHT//2 - 80,
        'radius': 20,
        'health': 60,
        'destroyed': False
    }
    collectible = None  # Will appear after crate destroyed
    door_open = False  # Will become True after collecting 5 zombie blood samples
    door_rect = pygame.Rect(SCREEN_WIDTH//2 - 40, SCREEN_HEIGHT - 120, 80, 40)
    # Pre-generate decorative tree positions so they stay consistent each frame
    tree_positions = [
        (random.randint(40, SCREEN_WIDTH - 40), random.randint(40, SCREEN_HEIGHT - 160))
        for _ in range(25)
    ]
    
    # Initialize player stats if not already set
    if not hasattr(player, 'zombie_blood_collected'):
        player.zombie_blood_collected = 0
    
    # Show initial objective
    show_dialogue(["Objective: Collect 5 zombie blood samples.", "Return to the lab entrance when the quest is complete."])
    
    # Helper to spawn particle effect like other collectibles
    def create_collect_effect(x, y):
        for _ in range(20):
            particles.append({
                'x': x,
                'y': y,
                'vx': random.uniform(-150, 150),
                'vy': random.uniform(-150, 150),
                'timer': random.uniform(0.2, 0.5),
                'color': random.choice([WHITE, (255,215,0), (200,200,200)])
            })

    def update_and_draw_particles(dt):
        for p in particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['timer'] -= dt
            if p['timer'] <= 0:
                particles.remove(p)
            else:
                pygame.draw.rect(screen, p['color'], (p['x'], p['y'], 3, 3))

    # Initialize particles list
    particles = []
    
    # Game loop for the outside area
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        handle_player_input(player, bullets, events)
        
        # Update player
        keys = pygame.key.get_pressed()
        update_player_state(player, keys, game_map, dt)

        # ---- Ground Pound impact ----
        if player.gp_triggered:
            player.gp_triggered = False
            # stun zombies for 2 seconds
            GP_RADIUS = 250  # pixels
            for zb in zombies:
                dist = math.hypot(zb.x - player.x, zb.y - player.y)
                if dist <= GP_RADIUS:
                    zb.stun_timer = 2.0
                    # Knockback 60 pixels proportionally
                    if dist>0:
                        kx = (zb.x - player.x)/dist * 60
                        ky = (zb.y - player.y)/dist * 60
                        zb.x += kx
                        zb.y += ky
            shake_timer = 0.4
            flash_timer = 0.15
        
        # Update zombies
        for zombie in zombies[:]:
            info = zombie.update(player.x, player.y, game_map, dt)
            if info:
                if isinstance(info, dict) and info.get('quake'):
                    shake_timer = info.get('duration',500)/1000.0
                else:
                    bullets.append(info)
            
            # Check for zombie attack with damage over time
            if zombie.is_alive:
                dist = math.hypot(player.x - zombie.x, player.y - zombie.y)
                if dist < player.radius + zombie.radius:
                    current_time = pygame.time.get_ticks()
                    attack_cooldown = 1000  # 1 second between damage ticks
                    
                    if player.is_shielding and player.shield_energy > 0:
                        # Shield blocks damage but drains energy
                        if current_time - zombie.last_attack_time > attack_cooldown:
                            player.shield_energy = max(0, player.shield_energy - 2)
                            if shield_hit_sound:
                                shield_hit_sound.play()
                            zombie.last_attack_time = current_time
                    elif current_time - zombie.last_attack_time > attack_cooldown:
                        # Deal damage over time when not shielding
                        player.take_damage(1)  # Small amount of damage per tick
                        zombie.last_attack_time = current_time
                        if player.health <= 0:
                            player.health = 0

            # Remove dead zombies from the list
            if not zombie.is_alive:
                zombies.remove(zombie)
        
        # Check for player death after handling all zombies
        if player.health <= 0:
            # Play alternate failure ending and propagate player's choice
            result = show_failure_ending()
            if result == "MAIN_MENU":
                return "MAIN_MENU"
            # Fallback
            return "MAIN_MENU"

        # Spawn new zombies if needed
        if len(zombies) < 5:  # Keep 5 zombies in the area
            spawn_zombie(game_map, zombies, player)
        
        # Draw everything
        screen.fill((0, 0, 0))  # Clear screen
        
        # Update shake / flash timers
        if shake_timer>0:
            shake_timer -= dt
        if flash_timer>0:
            flash_timer -= dt
        
        # White flash overlay
        if flash_timer>0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surf.fill(WHITE)
            alpha = int(255 * (flash_timer/0.15))
            flash_surf.set_alpha(alpha)
            screen.blit(flash_surf,(0,0))
        
        # Draw environment (road, grass, decorations)
        draw_outside_environment(screen, game_map)
        # ---------- Decorative elements ----------
        TREE_COLOR = (0, 100, 0)
        for tx, ty in tree_positions:
            pygame.draw.circle(screen, TREE_COLOR, (tx, ty), 10)
        
        # ---------- Lab door rendering & interaction ----------
        if door_open:
            # Door body and frame
            pygame.draw.rect(screen, (120, 80, 40), door_rect)
            pygame.draw.rect(screen, (180, 150, 90), door_rect, 3)
            # Highlight door when player is nearby
            if math.hypot(player.x - door_rect.centerx, player.y - door_rect.centery) < 100:
                pygame.draw.rect(screen, (255, 255, 100), door_rect.inflate(10, 10), 2)
        
        # Check if the player enters the open door
        if door_open:
            player_rect = pygame.Rect(player.x - player.radius, player.y - player.radius, player.radius * 2, player.radius * 2)
            if player_rect.colliderect(door_rect) and keys[pygame.K_e]:
                # Check if player has collected enough zombie blood
                if hasattr(player, 'zombie_blood_collected') and player.zombie_blood_collected >= 5:
                    # Complete the blood quest and show scientist dialogue
                    next_state = check_zombie_blood_quest(player)
                    if next_state == "BLOOD_QUEST_COMPLETE":
                        return next_state
                # If not enough blood, just return to throne room
                return "THRONE_ROOM"
        
        # Draw crate or collectible
        if not crate['destroyed']:
            # Draw crate box
            if crate_img:
                rect = crate_img.get_rect(center=(crate['x'], crate['y']))
                screen.blit(crate_img, rect)
            else:
                pygame.draw.rect(screen, (120,90,60), (crate['x']-20, crate['y']-20, 40,40))
        elif collectible and not collectible.get('collected'):
            if collection_img:
                rect = collection_img.get_rect(center=(collectible['x'], collectible['y']))
                screen.blit(collection_img, rect)
            else:
                pygame.draw.circle(screen, (255,215,0), (collectible['x'], collectible['y']), 14)

        # Draw player, zombies, and bullets
        player.draw(screen)
        for z in zombies:
            z.draw(screen)
        
        # ---- Update and draw bullets ----
        for bullet in bullets[:]:
            # Move projectile
            speed = bullet.get('speed', BULLET_SPEED)
            bullet['x'] += math.cos(bullet['angle']) * speed * dt
            bullet['y'] += math.sin(bullet['angle']) * speed * dt

            # Special shield boomerang behaviour
            if bullet.get('type') == 'shield':
                update_shield_bullet(bullet, bullets, dt, game_map, player, zombies)

            
            # Remove bullets that go off screen or hit walls
            if (bullet['x'] < 0 or bullet['x'] > SCREEN_WIDTH or
                bullet['y'] < 0 or bullet['y'] > SCREEN_HEIGHT or
                game_map[int(bullet['y'] / TILE_SIZE)][int(bullet['x'] / TILE_SIZE)] in ['W', 'P']):
                if bullet.get('type') == 'shield' and bullet.get('owner'):
                    bullet['owner'].active_shield_throw = False
                if bullet in bullets:
                    bullets.remove(bullet)
                continue
                
            # Get bullet radius before any checks
            radius = bullet.get('radius', BULLET_RADIUS)
            
            # Draw bullet / shield
            if bullet.get('type') == 'shield':
                draw_shield_bullet(screen, bullet)
            else:
                color = (0,255,0) if bullet.get('acid') else BULLET_COLOR
                pygame.draw.circle(screen, color, (int(bullet['x']), int(bullet['y'])), radius)
            
            # Check bullet hit crate (skip for shield)
            if not crate['destroyed'] and bullet.get('type') != 'shield':
                dist_crate = math.hypot(crate['x'] - bullet['x'], crate['y'] - bullet['y'])
                if dist_crate < crate['radius'] + radius:
                    crate['health'] -= bullet.get('damage', PLAYER_BULLET_DAMAGE)
                    if bullet in bullets:
                        bullets.remove(bullet)
                    if crate['health'] <= 0:
                        crate['destroyed'] = True
                        # spawn collectible
                        collectible = {'x': crate['x'], 'y': crate['y'], 'collected': False}
                    continue

            # Check for zombie hits
            for zombie in zombies[:]:
                if zombie.is_alive:
                    dist = math.hypot(zombie.x - bullet['x'], zombie.y - bullet['y'])
                    if dist < zombie.radius:
                        dmg = bullet.get('damage', PLAYER_BULLET_DAMAGE) if isinstance(bullet, dict) else PLAYER_BULLET_DAMAGE
                        zombie_died = zombie.take_damage(dmg)
                        if zombie_died:
                            if hasattr(player, 'zombie_blood_collected'):
                                player.zombie_blood_collected += 1
                            # Open lab door after collecting 5 zombie blood samples
                            if player.zombie_blood_collected >= 5 and not door_open:
                                door_open = True
                                show_dialogue(["The lab door has opened!", "Return to the entrance to head back inside."])
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break
        
        # Check player pick up collectible
        if collectible and not collectible['collected']:
            dist_pick = math.hypot(player.x - collectible['x'], player.y - collectible['y'])
            if dist_pick < player.radius + 20:
                collectible['collected'] = True
                create_collect_effect(collectible['x'], collectible['y'])
                if collect_sound:
                    collect_sound()  # Call the function to play the sound
                # Further benefits/stat boosts can be added here

        # Update & draw particles
        update_and_draw_particles(dt)

        # Draw UI
        draw_ui(screen, player, show_blood_counter=True)
        
        # Apply screen shake by offsetting the final frame
        if shake_timer > 0:
            offset = (random.randint(-6,6), random.randint(-6,6))
            frame_copy = screen.copy()
            screen.fill((0,0,0))
            screen.blit(frame_copy, offset)
        pygame.display.flip()
    
    return "MAIN_MENU"

def spawn_zombie(map_data, zombies, player):
    """Spawn a new zombie at a valid position."""
    while True:
        x = random.randint(2, len(map_data[0]) - 3) * TILE_SIZE
        y = random.randint(2, len(map_data) - 3) * TILE_SIZE
        
        # Check if position is walkable and far enough from player
        map_x, map_y = int(x / TILE_SIZE), int(y / TILE_SIZE)
        if (map_data[map_y][map_x] == ' ' and 
            abs(x - player.x) > 100 and abs(y - player.y) > 100):
            zombies.append(random_zombie(x, y))
            break

from levels.lab_scene import draw_outside_environment as detailed_draw_env

def draw_outside_environment(screen, map_data):
    """Draw the richer outside environment reused from lab_scene."""
    detailed_draw_env(screen, map_data)
