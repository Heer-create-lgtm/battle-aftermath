import pygame
import random
from settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK
from zombie import Zombie
from special_zombies import random_zombie
from levels.dialogue import show_dialogue
import math

def show_scientist_revival_scene():
    """Show the lab scene where the scientist revives the player."""
    from levels.lab_scene import show_lab_scene, create_outside_environment, draw_outside_environment
    
    # Show the lab scene with dialogue
    show_lab_scene()
    
    # Create the outside environment
    outside_map = create_outside_environment()
    
    # Initialize player in the outside area
    from player import Player
    player = Player()
    player.x = 8 * TILE_SIZE  # Start near the lab entrance
    player.y = 14 * TILE_SIZE
    player.angle = -math.pi / 2
    
    # Spawn zombies in the outside area
    zombies = []
    for _ in range(8):
        while True:
            x = random.randint(2, len(outside_map[0]) - 3) * TILE_SIZE
            y = random.randint(2, len(outside_map) - 3) * TILE_SIZE
            
            # Make sure we don't spawn on walls or the player
            map_x, map_y = int(x / TILE_SIZE), int(y / TILE_SIZE)
            if (outside_map[map_y][map_x] == ' ' and 
                abs(x - player.x) > 100 and abs(y - player.y) > 100):
                zombies.append(random_zombie(x, y))
                break
    
    # Return the game objects
    return {
        'player': player,
        'zombies': zombies,
        'map': outside_map,
        'draw_environment': draw_outside_environment
    }

def show_scientist_after_blood():
    """Display post-blood-quest cutscene with smooth fades without flicker.

    Returns:
        str: "BLOOD_QUEST_COMPLETE" to inform the main loop.
    """
    screen = pygame.display.get_surface()

    # Import shared fade helpers locally to avoid circular import at top level
    from main import fade_to_black as main_fade_to_black, fade_in_from_black as main_fade_in_from_black

    # Fade out, show dialogue, fade back in
    main_fade_to_black(screen)

    scientist_lines = [
        "Amazing! You've collected enough samples.",
        "With this, I can start working on a cure.",
        "But there's something you should know...",
        "The infection is spreading faster than we anticipated.",
        "We need to find the source and stop it before it's too late.",
        "I'll analyze these samples. Be careful out there..."
    ]

    show_dialogue(scientist_lines)

    main_fade_in_from_black(screen)

    return "BLOOD_QUEST_COMPLETE"



def check_zombie_blood_quest(player):
    """Check if player has collected enough zombie blood."""
    if hasattr(player, 'zombie_blood_collected') and player.zombie_blood_collected >= 5:
        next_state = show_scientist_after_blood()
        player.zombie_blood_collected = 0  # Reset the counter
        return next_state  # This will be "MAIN_MENU"
    return None
