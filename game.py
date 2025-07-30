import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from player import Player

# Initialize Pygame
pygame.init()

# Screen dimensions
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Shooter")

# Game clock
clock = pygame.time.Clock()

# Player
player = None

def start_game():
    """Initializes and runs the main game loop."""
    global player
    
    # Initialize player
    player = Player()
    
    # Game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Player movement
        keys = pygame.key.get_pressed()
        
        # Update player
        player.update(keys, [], False, 1/60)
        
        # Drawing
        screen.fill((0, 0, 0))
        player.draw(screen)
        pygame.display.flip()
        
        # Tick the clock
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    start_game()
