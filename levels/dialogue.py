import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE

def show_dialogue(lines, font_size=36, text_color=WHITE, bg_color=(0, 0, 0, 200)):
    """
    Display dialogue text on screen with word wrapping and click-to-continue.
    
    Args:
        lines: List of strings, each representing a line of dialogue
        font_size: Size of the font to use
        text_color: RGB tuple for text color
        bg_color: RGBA tuple for background color (includes alpha)
    """
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # Set up font
    try:
        font = pygame.font.Font("assets/fonts/arial.ttf", font_size)
    except:
        font = pygame.font.SysFont("Arial", font_size)
    
    # Calculate text dimensions
    padding = 20
    
    # Process each line of dialogue
    current_line = 0
    while current_line < len(lines):
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_e):
                    current_line += 1
                    if current_line >= len(lines):
                        return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                current_line += 1
                if current_line >= len(lines):
                    return
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw current line
        text = font.render(lines[current_line], True, text_color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        # Draw background
        bg_rect = pygame.Rect(
            text_rect.left - padding,
            text_rect.top - padding,
            text_rect.width + 2 * padding,
            text_rect.height + 2 * padding
        )
        
        # Create a surface with per-pixel alpha for the background
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, bg_color, (0, 0, bg_rect.width, bg_rect.height), border_radius=10)
        
        # Blit the background and text
        screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
        screen.blit(text, text_rect)
        
        # Draw "Press any key to continue" prompt
        if current_line < len(lines) - 1:
            prompt_font = pygame.font.Font(None, 24)
            prompt = prompt_font.render("Press any key to continue...", True, (200, 200, 200))
            prompt_rect = prompt.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
            screen.blit(prompt, prompt_rect)
        
        pygame.display.flip()
        clock.tick(60)

def show_god_dialogue(lines):
    """Special dialogue function for god dialogues with different styling."""
    return show_dialogue(
        lines,
        font_size=32,
        text_color=(220, 220, 255),
        bg_color=(20, 20, 40, 220)
    )
