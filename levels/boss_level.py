import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, WHITE, BOSS_HEALTH_BAR_BG, BOSS_HEALTH_BAR_FG, MAX_HEALTH, BULLET_SPEED, PLAYER_BULLET_DAMAGE, PYTHON_DAMAGE, PYTHON_HEALTH
from levels.death_endings import show_python_boss_death_ending
from player import Player
from python_boss import PythonBoss
from mechanics import handle_player_input, update_player_state
from ui import draw_ui
from levels.dialogue import show_dialogue

def run_boss_level():
    """Run the boss level with the Python boss."""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    bullets = []

    # Set up boss level map
    boss_room_map = [
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
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
        "W                              W",
        "W                              W",
        "W                              W",
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    ]
    
    # Create player and boss
    player = Player()
    player.x = SCREEN_WIDTH // 2
    player.y = SCREEN_HEIGHT - 100
    player.angle = -math.pi / 2
    
    boss = PythonBoss()
    
    # Game state
    game_state = "BOSS_INTRO"
    boss_intro_timer = 180  # 3 seconds at 60 FPS
    
    # Game loop
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Event handling
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return "QUIT"
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                elif event.key == pygame.K_SPACE:
                        # SPACE handled in handle_player_input too, but keep for responsiveness
                    bullet = player.shoot()
                    if bullet:
                        bullets.append(bullet)
        
        # Update game state
        if game_state == "BOSS_INTRO":
            boss_intro_timer -= 1
            if boss_intro_timer <= 0:
                game_state = "BOSS_FIGHT"
                show_dialogue([
                    "Python Boss: You dare challenge me, mortal?",
                    "Python Boss: Let me show you the power of clean code!"
                ])
        
        elif game_state == "BOSS_FIGHT":
                        # Handle input and update player consistently
            handle_player_input(player, bullets, events)
            keys = pygame.key.get_pressed()
            update_player_state(player, keys, boss_room_map, dt)
            
            # Update boss
            boss.update(player.x, player.y, boss_room_map, dt)

            # Update bullets and check for hits on boss
            for bullet in bullets[:]:
                bullet['x'] += math.cos(bullet['angle']) * BULLET_SPEED * dt
                bullet['y'] += math.sin(bullet['angle']) * BULLET_SPEED * dt
                
                # Check for collision with walls
                if (bullet['x'] < 0 or bullet['x'] > SCREEN_WIDTH or
                    bullet['y'] < 0 or bullet['y'] > SCREEN_HEIGHT or
                    boss_room_map[int(bullet['y'] / TILE_SIZE)][int(bullet['x'] / TILE_SIZE)] in ['W', 'P']):
                    bullets.remove(bullet)
                    continue

                # Check for collision with boss
                if boss.state in ['EMERGING', 'ATTACKING', 'ROAMING', 'TELEGRAPHING_CHARGE', 'CHARGING']:
                    dist_to_head = math.hypot(boss.segments[0]['x'] - bullet['x'], boss.segments[0]['y'] - bullet['y'])
                    if dist_to_head < TILE_SIZE // 2:
                        boss.take_damage(PLAYER_BULLET_DAMAGE)
                        bullets.remove(bullet)
                        if not boss.is_alive:
                            game_state = "BOSS_DEFEATED"
                            show_dialogue([
                                "Python Boss: Nooo! My beautiful indentation!",
                                "Python Boss: You... you've won this time..."
                            ])
                            return "VICTORY"

            # Check for boss attacks
            if boss.state in ['ATTACKING', 'ROAMING', 'CHARGING']:
                dist_to_player = math.hypot(player.x - boss.segments[0]['x'], player.y - boss.segments[0]['y'])
                if dist_to_player < player.radius + (TILE_SIZE // 2):
                    player.take_damage(PYTHON_DAMAGE)
                    if player.health <= 0:
                        # Show special ending when player dies to Python boss
                        show_python_boss_death_ending()
                        # Standard Game Over screen afterwards
                        from main import show_game_over_screen
                        result = show_game_over_screen(show_restart_level=False)
                        if result == "MAIN_MENU":
                            return "MAIN_MENU"
                        return "GAME_OVER"
        
        # Draw everything
        draw_boss_level(screen, boss_room_map, player, boss, game_state, bullets)
        
        pygame.display.flip()
    
    return "MENU"  # Shouldn't reach here



def draw_boss_level(screen, map_data, player, boss, game_state, bullets):
    """Draw the boss level scene."""
    # Clear screen
    screen.fill((0, 0, 0))  # Black background for boss level
    
    # Draw floor pattern
    for y in range(0, SCREEN_HEIGHT, 40):
        for x in range(0, SCREEN_WIDTH, 40):
            if (x // 40 + y // 40) % 2 == 0:
                pygame.draw.rect(screen, (20, 20, 20), (x, y, 40, 40))
    
    # Draw walls
    for y, row in enumerate(map_data):
        for x, tile in enumerate(row):
            if tile == 'W':  # Wall
                pygame.draw.rect(screen, (50, 50, 50), 
                               (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    
    # Draw boss
    if game_state != "BOSS_INTRO" or pygame.time.get_ticks() % 1000 < 500:  # Flash during intro
        boss.draw(screen)
    
    # Draw player
    player.draw(screen)

    # Draw bullets
    for bullet in bullets:
        pygame.draw.circle(screen, (255, 255, 0), (int(bullet['x']), int(bullet['y'])), 5)
    
    # Draw UI
    draw_ui(screen, player, boss)


