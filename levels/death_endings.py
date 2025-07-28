import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

def _show_static_image(image_path: str):
    """Generic helper to display a full-screen static image until key/mouse or timeout."""
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()

    # Load image (fallback to text on failure)
    try:
        ending_img = pygame.image.load(image_path).convert_alpha()
    except pygame.error as e:
        print(f"[death_endings] Could not load {image_path}: {e}")
        font = pygame.font.Font(None, 48)
        text = font.render("THE END", True, (255, 255, 255))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        _wait_loop(screen, clock, text_surface=text, text_rect=rect)
        return

    # Scale if needed to fit screen
    img_rect = ending_img.get_rect()
    scale_ratio = min(SCREEN_WIDTH / img_rect.width, SCREEN_HEIGHT / img_rect.height)
    if scale_ratio < 1:
        new_size = (int(img_rect.width * scale_ratio), int(img_rect.height * scale_ratio))
        ending_img = pygame.transform.smoothscale(ending_img, new_size)
        img_rect = ending_img.get_rect()
    img_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    # Fade-in variables
    fade_alpha = 0
    fade_speed = 4
    fade_full_time = None

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False

        if fade_alpha < 255:
            fade_alpha = min(fade_alpha + fade_speed, 255)
            if fade_alpha == 255:
                fade_full_time = pygame.time.get_ticks()

        screen.fill((0, 0, 0))
        ending_img.set_alpha(fade_alpha)
        screen.blit(ending_img, img_rect)
        pygame.display.flip()

        if fade_full_time and pygame.time.get_ticks() - fade_full_time > 6000:
            running = False


def _wait_loop(screen, clock, text_surface=None, text_rect=None):
    """Simple loop displaying text until player input quits."""
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
        screen.fill((0, 0, 0))
        if text_surface and text_rect:
            screen.blit(text_surface, text_rect)
        pygame.display.flip()
        clock.tick(60)


def show_python_boss_death_ending():
    """Display ending3.png when player dies to Python boss."""
    _show_static_image('assets/sprites/ending3.png')


def show_tutorial_death_ending():
    """Display ending4.png when player dies to tutorial zombie."""
    _show_static_image('assets/sprites/ending4.png')
