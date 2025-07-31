import pygame
import math
from settings import (
    PLAYER_SPEED, SPRINT_SPEED, STAMINA_COST, STAMINA_REGEN,
    SHIELD_DRAIN, SHIELD_REGEN, TILE_SIZE, PLAYER_RADIUS
)

def handle_player_input(player, bullets_list, events):
    """Handles player-specific input events like shooting and reloading."""
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not player.is_reloading:
                new_bullet = player.shoot()
                if new_bullet:
                    if isinstance(new_bullet, list):
                        bullets_list.extend(new_bullet)
                    else:
                        bullets_list.append(new_bullet)
            elif event.key == pygame.K_q:
                from settings import SHIELD_COOLDOWN_TIME
                from settings import SHIELD_COOLDOWN_TIME, SHIELD_ENERGY_THROW_RATIO
                if player.shield_cooldown == 0 and player.shield_energy >= player.max_shield_energy * SHIELD_ENERGY_THROW_RATIO:
                    proj = player.throw_shield()
                    if proj:
                        player.shield_cooldown = SHIELD_COOLDOWN_TIME
                        # Consume shield energy
                        player.shield_energy = max(0, player.shield_energy - player.max_shield_energy * SHIELD_ENERGY_THROW_RATIO)
                        bullets_list.append(proj)
                else:
                    proj = None
                if proj:
                    bullets_list.append(proj)
            elif event.key == pygame.K_r and not player.is_shielding:
                player.start_reload()

def update_player_state(player, keys, game_map, dt):
    """Updates the player's state, including movement, stamina, and shield."""
    # --- Shield cooldown timer ---
    # --- Cooldowns ---
    if player.shield_cooldown > 0:
        player.shield_cooldown = max(0, player.shield_cooldown - dt)
    # Shotgun cooldown
    if hasattr(player, 'shotgun_cooldown') and player.shotgun_cooldown > 0:
        player.shotgun_cooldown = max(0, player.shotgun_cooldown - dt)

    # Movement
    dx, dy = 0, 0
    is_sprinting = keys[pygame.K_LSHIFT] and player.stamina > 0
    speed = SPRINT_SPEED if is_sprinting else PLAYER_SPEED

    if keys[pygame.K_w]:
        dy -= 1
    if keys[pygame.K_s]:
        dy += 1
    if keys[pygame.K_a]:
        dx -= 1
    if keys[pygame.K_d]:
        dx += 1

    if dx != 0 or dy != 0:
        angle = math.atan2(dy, dx)
        # Normalize vector
        length = math.sqrt(dx*dx + dy*dy)
        dx /= length
        dy /= length

        new_x = player.x + speed * dx * dt
        new_y = player.y + speed * dy * dt
        
        # ------- Safe collision handling with bounds checks -------
        map_h = len(game_map)
        map_w = len(game_map[0]) if map_h else 0

        # Check X movement
        col = int(new_x / TILE_SIZE)
        row = int(player.y / TILE_SIZE)
        if 0 <= row < map_h and 0 <= col < map_w:
            if game_map[row][col] not in ['W', 'P', 'T', 'R']:
                player.x = new_x
        # Prevent moving beyond map borders horizontally
        player.x = max(player.radius, min(player.x, (map_w - 1) * TILE_SIZE))

        # Check Y movement
        col = int(player.x / TILE_SIZE)
        row = int(new_y / TILE_SIZE)
        if 0 <= row < map_h and 0 <= col < map_w:
            if game_map[row][col] not in ['W', 'P', 'T', 'R']:
                player.y = new_y
        # Prevent moving beyond map borders vertically
        player.y = max(player.radius, min(player.y, (map_h - 1) * TILE_SIZE))

    # Update angle to face mouse
    mouse_x, mouse_y = pygame.mouse.get_pos()
    player.angle = math.atan2(mouse_y - player.y, mouse_x - player.x)

    # Stamina management
    if is_sprinting and (dx != 0 or dy != 0):
        player.stamina -= STAMINA_COST * dt
        if player.stamina < 0:
            player.stamina = 0
    elif player.stamina < player.max_stamina:
        player.stamina += STAMINA_REGEN * dt
        if player.stamina > player.max_stamina:
            player.stamina = player.max_stamina

    # ----- Ground Pound ability processing -----
    if player.gp_charging:
        player.gp_charge += dt
        if player.gp_charge >= 1.0:
            player.gp_charging = False
            player.gp_triggered = True
            player.gp_cooldown = 10.0
            player.gp_msg_timer = 1.5
    elif keys[pygame.K_f] and player.gp_cooldown <= 0 and not player.gp_charging:
        player.gp_charging = True
        player.gp_charge = 0.0
    # Cooldown timer
    if player.gp_cooldown > 0:
        player.gp_cooldown = max(0, player.gp_cooldown - dt)

    # Message timer decay
    if hasattr(player, 'gp_msg_timer') and player.gp_msg_timer > 0:
        player.gp_msg_timer = max(0, player.gp_msg_timer - dt)

    # Shield toggle and energy management (hold 'E' to shield)
    if keys[pygame.K_e] and player.shield_energy > 0 and not player.is_reloading:
        player.is_shielding = True
    else:
        player.is_shielding = False

    if player.is_shielding:
        player.shield_energy -= SHIELD_DRAIN * dt
        if player.shield_energy < 0:
            player.shield_energy = 0
            player.is_shielding = False
    elif player.shield_energy < player.max_shield_energy:
        player.shield_energy += SHIELD_REGEN * dt
        if player.shield_energy > player.max_shield_energy:
            player.shield_energy = player.max_shield_energy

    # Reloading
    if player.is_reloading:
        player.reload_timer -= dt
        if player.reload_timer <= 0:
            player.finish_reload() 