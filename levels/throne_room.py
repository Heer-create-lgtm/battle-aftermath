import pygame
import math
from settings import (
    TILE_SIZE, BG_COLOR
)
from ui import draw_ui
from player import Player
from zombie import Zombie
from levels.dialogue import show_god_dialogue

import random

def run_throne_room():
    """Run the main throne room level."""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # Set up throne room map
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
    
    # Create player
    player = Player()
    player.x = 16 * TILE_SIZE
    player.y = 15 * TILE_SIZE
    player.angle = -math.pi / 2
    
    # Initialize game state
    game_state = "GAME"
    zombies = []
    
    # Game loop
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
        
        # Update game state
        if game_state == "GAME":
            # Update player
            keys = pygame.key.get_pressed()
            player.update(keys, throne_room_map, True, dt)
            
            # Update zombies
            for zombie in zombies[:]:
                zombie_died = zombie.update(player.x, player.y, throne_room_map, dt)
                if not zombie.is_alive:
                    if zombie_died and hasattr(player, 'zombie_blood_collected'):
                        player.zombie_blood_collected += 1
                    zombies.remove(zombie)
            
            # Spawn new zombies if needed
            if len(zombies) < 5:  # Keep 5 zombies in the level
                spawn_zombie(throne_room_map, zombies)
            
            # Check for interactions with gods
            check_god_interaction(player, throne_room_map)
            

        
        # Draw everything
        draw_throne_room(screen, throne_room_map, player, zombies, game_state)
        
        # Check for game over
        if player.health <= 0:
            return "GAME_OVER"
        
        pygame.display.flip()
    
    return "MENU"  # Default return

def spawn_zombie(map_data, zombies):
    """Spawn a new zombie at a valid position."""
    while True:
        x = random.randint(1, len(map_data[0]) - 2)
        y = random.randint(1, len(map_data) - 2)
        
        # Check if position is walkable
        if map_data[y][x] == ' ':
            zombies.append(Zombie(x * TILE_SIZE, y * TILE_SIZE))
            break

def check_god_interaction(player, map_data):
    """Check if player is interacting with any of the gods."""
    # Define god positions (center of their thrones)
    god_positions = [
        (14 * TILE_SIZE, 2.5 * TILE_SIZE),  # Left god
        (16 * TILE_SIZE, 2.5 * TILE_SIZE),  # Middle god
        (18 * TILE_SIZE, 2.5 * TILE_SIZE),  # Right god
    ]
    
    # Check distance to each god
    for god_x, god_y in god_positions:
        distance = math.hypot(player.x - god_x, player.y - god_y)
        if distance < 50:  # Interaction range
            show_god_dialogue(["Approach, mortal..."])
            break

def draw_throne_room(screen, map_data, player, zombies, game_state):
    """Draw the entire throne room scene."""
    # Clear screen
    screen.fill(BG_COLOR)
    
    # Draw floor
    for y, row in enumerate(map_data):
        for x, tile in enumerate(row):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if tile == 'W':  # Wall
                pygame.draw.rect(screen, (100, 100, 100), rect)
            elif tile == 'P':  # Pillar
                pygame.draw.rect(screen, (150, 150, 150), rect)
    
    # Draw thrones
    thrones = [
        (14 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE, 3 * TILE_SIZE),  # Left throne
        (16 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE, 3 * TILE_SIZE),  # Middle throne
        (18 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE, 3 * TILE_SIZE),  # Right throne
    ]
    
    for x, y, w, h in thrones:
        pygame.draw.rect(screen, (139, 69, 19), (x, y, w, h))  # Brown thrones
    
    # Draw player and zombies
    player.draw(screen)
    for zombie in zombies:
        zombie.draw(screen)
    
    # Draw UI using shared HUD
    draw_ui(screen, player)
    

