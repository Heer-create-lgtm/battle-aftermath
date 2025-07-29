import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, UI_PANEL_BG, PLAYER_MAX_SHIELD_ENERGY,
    SHIELD_BAR_BG, SHIELD_BAR_FG, MAX_HEALTH, HEALTH_BAR_BG, HEALTH_BAR_FG,
    MAX_STAMINA, STAMINA_BAR_BG, STAMINA_BAR_FG, PLAYER_MAX_AMMO, WHITE, BOSS_HEALTH_BAR_BG, BOSS_HEALTH_BAR_FG, PYTHON_HEALTH
)

def draw_ui(screen, player, boss=None, show_blood_counter=False):
    """Draws the game UI."""
    # UI Panel background
    ui_panel_height = 70
    ui_panel_y = SCREEN_HEIGHT - ui_panel_height
    panel_surface = pygame.Surface((SCREEN_WIDTH, ui_panel_height), pygame.SRCALPHA)
    panel_surface.fill(UI_PANEL_BG)
    screen.blit(panel_surface, (0, ui_panel_y))

    # Shield Energy Bar
    shield_bar_width = 200
    shield_bar_height = 10
    shield_bar_x = 220 # To the right of health/stamina
    shield_bar_y = SCREEN_HEIGHT - 65
    shield_ratio = player.shield_energy / PLAYER_MAX_SHIELD_ENERGY
    pygame.draw.rect(screen, SHIELD_BAR_BG, (shield_bar_x, shield_bar_y, shield_bar_width, shield_bar_height))
    pygame.draw.rect(screen, SHIELD_BAR_FG, (shield_bar_x, shield_bar_y, shield_bar_width * shield_ratio, shield_bar_height))

    # Health bar
    health_bar_width = 200
    health_bar_height = 20
    health_bar_x = 10
    health_bar_y = SCREEN_HEIGHT - 50 # Positioned inside the panel
    health_ratio = player.health / MAX_HEALTH
    pygame.draw.rect(screen, HEALTH_BAR_BG, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
    pygame.draw.rect(screen, HEALTH_BAR_FG, (health_bar_x, health_bar_y, health_bar_width * health_ratio, health_bar_height))

    # Stamina bar
    stamina_bar_width = 200
    stamina_bar_height = 20
    stamina_bar_x = 10
    stamina_bar_y = SCREEN_HEIGHT - 25 # Below health bar
    stamina_ratio = player.stamina / MAX_STAMINA
    pygame.draw.rect(screen, STAMINA_BAR_BG, (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height))
    pygame.draw.rect(screen, STAMINA_BAR_FG, (stamina_bar_x, stamina_bar_y, stamina_bar_width * stamina_ratio, stamina_bar_height))

    # Ammo display
    ammo_font = pygame.font.Font(None, 28)
    ammo_text = f"AMMO: {player.ammo} / {PLAYER_MAX_AMMO}"
    if player.is_reloading:
        ammo_text = "RELOADING..."
    text_surface = ammo_font.render(ammo_text, True, WHITE)
    screen.blit(text_surface, (220, SCREEN_HEIGHT - 40))

    # Zombie blood counter (if the player has this attribute)
    if show_blood_counter and hasattr(player, 'zombie_blood_collected'):
        blood_font = pygame.font.Font(None, 24)
        blood_text = f"BLOOD: {player.zombie_blood_collected}/5"
        blood_surface = blood_font.render(blood_text, True, WHITE)
        screen.blit(blood_surface, (SCREEN_WIDTH - blood_surface.get_width() - 20, SCREEN_HEIGHT - 40))

    # Boss health bar (optional)
    if boss is not None:
        boss_bar_width = SCREEN_WIDTH - 40
        boss_bar_height = 20
        boss_bar_x = 20
        boss_bar_y = 20
        # Fall back to PYTHON_HEALTH if the boss lacks max_health attribute
        max_boss_health = getattr(boss, 'max_health', PYTHON_HEALTH)
        boss_ratio = max(0, boss.health) / max_boss_health
        pygame.draw.rect(screen, BOSS_HEALTH_BAR_BG, (boss_bar_x, boss_bar_y, boss_bar_width, boss_bar_height))
        pygame.draw.rect(screen, BOSS_HEALTH_BAR_FG, (boss_bar_x, boss_bar_y, boss_bar_width * boss_ratio, boss_bar_height)) 