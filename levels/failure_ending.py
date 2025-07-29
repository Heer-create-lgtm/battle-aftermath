import pygame
import sys

from settings import SCREEN_WIDTH, SCREEN_HEIGHT

def show_failure_ending():
    """Display the bad ending where Doom falls to the zombie horde.

    The function shows `assets/sprites/ending2.png` centred on-screen with a
    subtle fade-in.  The image stays until the player presses any key,
    clicks the mouse, or closes the window, after which control returns to
    the caller so they can continue (typically back to the main menu).
    """

    screen = pygame.display.get_surface()
    if screen is None:
        # If called before a display is initialised, create one.
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()

    # ---- Load image ----
    try:
        ending_img = pygame.image.load('assets/sprites/ending2.png').convert_alpha()
    except pygame.error as e:
        # If the graphic is missing, fall back to a simple text message.
        print(f"[failure_ending] Could not load ending2.png: {e}")
        _fallback_dialogue(screen, clock)
        return

    # Scale the image to at most screen size while maintaining aspect ratio.
    img_rect = ending_img.get_rect()
    scale_ratio = min(SCREEN_WIDTH / img_rect.width, SCREEN_HEIGHT / img_rect.height)
    if scale_ratio < 1:
        new_size = (int(img_rect.width * scale_ratio), int(img_rect.height * scale_ratio))
        ending_img = pygame.transform.smoothscale(ending_img, new_size)
        img_rect = ending_img.get_rect()
    img_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    # ---- Fade-in variables ----
    fade_alpha = 0
    fade_speed = 4  # larger -> quicker fade (≈1 s)
    fade_full_time = None  # timestamp when image is fully opaque

    running = True
    while running:
        elapsed_ms = clock.tick(60)  # milliseconds since last frame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False

        # Increase alpha until fully opaque
        if fade_alpha < 255:
            fade_alpha = min(fade_alpha + fade_speed, 255)
            if fade_alpha == 255:
                fade_full_time = pygame.time.get_ticks()

        # Draw background and image
        screen.fill((0, 0, 0))
        ending_img.set_alpha(fade_alpha)
        screen.blit(ending_img, img_rect)
        pygame.display.flip()

        # After the image is fully opaque, auto-advance after ~6 seconds
        if fade_full_time is not None and pygame.time.get_ticks() - fade_full_time > 6000:
            running = False


    # After showing the failure ending image, display the simplified Game Over screen (Main Menu only)
    from main import show_game_over_screen  # Local import to avoid circular dependency
    result = show_game_over_screen(show_restart_level=False)
    return result


def _fallback_dialogue(screen, clock):
    """Fallback simple text-only ending if image cannot be displayed."""
    font = pygame.font.Font(None, 48)
    line = "The world succumbs to the undead…"
    text = font.render(line, True, (255, 255, 255))
    rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
        screen.fill((0, 0, 0))
        screen.blit(text, rect)
        pygame.display.flip()
        clock.tick(60)
