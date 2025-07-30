import pygame
import sys
from settings import TILE_SIZE, BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, WHITE
from player import Player
from mechanics import handle_player_input, update_player_state
from ui import draw_ui
from levels.dialogue import show_dialogue

def run_tutorial():
    """Run the tutorial level."""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # Set up tutorial map
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
    
    # Create player
    player = Player()
    player.x = 2 * TILE_SIZE
    player.y = 2 * TILE_SIZE
    
    # Tutorial state
    tutorial_state = "movement"
    tutorial_complete = False
    
    # Tutorial messages
    movement_messages = [
        "Use WASD or Arrow Keys to move.",
        "Move around to get a feel for the controls.",
        "Try moving to the next area when you're ready."
    ]
    
    # Game loop
    running = True
    while running and not tutorial_complete:
        dt = clock.tick(60) / 1000.0
        
        events = pygame.event.get()
        # Event handling
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
        
        # Handle input consistently
        handle_player_input(player, [], events)  # tutorial currently has no bullets list
        keys = pygame.key.get_pressed()
        update_player_state(player, keys, tutorial_map, dt)
        
        # Check tutorial state
        if tutorial_state == "movement":
            if player.x > 10 * TILE_SIZE:
                tutorial_state = "complete"
        
        # Draw
        screen.fill(BG_COLOR)
        
        # Draw map
        for y, row in enumerate(tutorial_map):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if tile == 'W':
                    pygame.draw.rect(screen, (100, 100, 100), rect)
                elif tile == '1':
                    pygame.draw.rect(screen, (0, 255, 0), rect)
        
                # Draw player
        player.draw(screen)

        # Draw UI using shared HUD
        draw_ui(screen, player)
        
        # Draw tutorial messages
        if tutorial_state == "movement":
            show_tutorial_message(screen, movement_messages[0])
        
        pygame.display.flip()
        
        # Check for tutorial completion
        if tutorial_state == "complete":
            tutorial_complete = True
    
    # Show completion message
    show_dialogue(["Tutorial complete! You're ready to face the apocalypse."])

def show_tutorial_message(screen, message):
    """Display a tutorial message on screen."""
    font = pygame.font.Font(None, 36)
    text = font.render(message, True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    
    # Semi-transparent background
    s = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    screen.blit(s, (0, SCREEN_HEIGHT - 80))
    
    screen.blit(text, text_rect)
