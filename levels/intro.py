import pygame
import sys
from settings import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE

def show_intro():
    """Show the game's introduction sequence."""
    title_font = pygame.font.Font(None, 100)
    font = pygame.font.Font(None, 36)
    
    backstory_lines = [
        "A man lost everything...",
        "His family, his home, his world.",
        "Then the world ended.",
        "Amidst the zombie apocalypse, his wife was bitten.",
        "To save their daughter, he made an impossible choice...",
        "He had to leave the woman he loved the most.",
        "In his darkest hour, a new calling emerged..."
    ]
    
    god_dialogue = [
        "The gods spoke as one:",
        "'Mortal, your suffering has not gone unnoticed.'",
        "'We have witnessed your sacrifice and your strength.'",
        "'The world has fallen to darkness, but you...'",
        "'...you have been chosen.'",
        "'We grant you power beyond mortal means.'",
        "'Use it to cleanse this world of the undead plague.'",
        "'But beware - the greatest test is yet to come...'"
    ]

    # Show backstory first
    screen = pygame.display.get_surface()
    screen.fill(BG_COLOR)
    
    # Draw title
    title_text = title_font.render("THE CHOSEN", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, 80))
    screen.blit(title_text, title_rect)
    
    # Display backstory lines with fade-in effect
    for i, line in enumerate(backstory_lines):
        text = font.render(line, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, 200 + i * 40))
        
        # Fade in effect
        for alpha in range(0, 256, 5):
            screen.fill(BG_COLOR)
            screen.blit(title_text, title_rect)
            
            # Draw previous lines
            for j in range(i):
                prev_text = font.render(backstory_lines[j], True, WHITE)
                screen.blit(prev_text, 
                           (SCREEN_WIDTH // 2 - prev_text.get_width() // 2, 
                            200 + j * 40))
            
            # Draw current line with fading
            text.set_alpha(alpha)
            screen.blit(text, text_rect)
            
            pygame.display.flip()
            pygame.time.delay(30)
            
            # Check for quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
    
    # Pause before showing god dialogue
    pygame.time.delay(1000)
    
    # Show god dialogue
    for i, line in enumerate(god_dialogue):
        text = font.render(line, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, 200 + i * 40))
        
        # Fade in effect
        for alpha in range(0, 256, 10):
            screen.fill(BG_COLOR)
            screen.blit(title_text, title_rect)
            
            # Draw current line with fading
            text.set_alpha(alpha)
            screen.blit(text, text_rect)
            
            pygame.display.flip()
            pygame.time.delay(10)
            
            # Check for quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
        
        pygame.time.delay(1000) if i < len(god_dialogue) - 1 else pygame.time.delay(2000)
    
    # Fade to black
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill(BLACK)
    for alpha in range(0, 256, 5):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(10)
    
    pygame.time.delay(1000)
