import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from levels.lab_scene import create_outside_environment  # Re-use the outdoor map generator

# We import show_dialogue from main at runtime to avoid circular imports.

def _show_simple_dialogue(lines):
    """Fallback dialogue renderer if main.show_dialogue is not ready."""
    screen = pygame.display.get_surface()
    if screen is None:
        return

    font = pygame.font.Font(None, 42)
    clock = pygame.time.Clock()
    for line in lines:
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    waiting = False
            screen.fill((20, 30, 40))
            text = font.render(line, True, (255, 255, 255))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, rect)
            prompt = font.render("Press ENTER…", True, (180, 180, 200))
            p_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
            screen.blit(prompt, p_rect)
            pygame.display.flip()
            clock.tick(60)


def show_lab_scene():
    """Light-weight revival lab scene with fresh dialogue instructing the blood quest."""
    screen = pygame.display.get_surface()
    if screen is None:
        return {}

    # Draw a simple dim laboratory background
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg.fill((30, 40, 55))
    pygame.draw.rect(bg, (45, 55, 70), (0, SCREEN_HEIGHT - 150, SCREEN_WIDTH, 150))  # floor area
    screen.blit(bg, (0, 0))
    pygame.display.flip()

    # Dialogue lines distinct from the first visit to the lab.
    lines = [
        "Scientist: You made it back alive, barely…",
        "Scientist: My med-kits are spent. We'll need fresh zombie blood to patch you up.",
        "Scientist: Bring me samples from 5 of the cursed outside these walls.",
        "Scientist: Hurry—each minute you stay hurt, the infection grows…"
    ]

    # Always use local simple dialogue to keep lab background.
    _show_simple_dialogue(lines)

    # After dialogue, fade out quickly
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(0, 256, 12):
        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(15)

    # ------- Build outside quest objects -------
    from player import Player
    from zombie import Zombie
    import random
    outside_map = create_outside_environment()
    player = Player()
    # Spawn player near lab entrance (center bottom)
    player.x = SCREEN_WIDTH // 2
    player.y = SCREEN_HEIGHT - 120

    zombies = []
    # Spawn a few starter zombies randomly
    for _ in range(6):
        zx = random.randint(2, len(outside_map[0])-3) * 16
        zy = random.randint(2, len(outside_map)-5) * 16
        zombies.append(Zombie(zx, zy))

    return {
        'player': player,
        'zombies': zombies,
        'map': outside_map
    }


def create_outside_environment_wrapper():
    """Expose create_outside_environment with the same signature."""
    return create_outside_environment()
