import math
import pygame
from settings import TILE_SIZE, SHIELD_TRAIL_COLOR, SHIELD_MAX_TRAIL_POINTS


def update_shield_bullet(bullet: dict, bullets: list, dt: float, game_map, owner_player, zombies=None):
    """Update physics & boomerang behaviour for a shield projectile.
    Removes the bullet from list when it is caught. Expects keys created in Player.throw_shield().
    `game_map` 2-D tile list, `owner_player` is the player object.
    `zombies` optional list to apply bounce & damage.
    """
    # ----- Trail -----
    trail = bullet['trail']
    trail.append((bullet['x'], bullet['y']))
    try:
        from settings import SHIELD_TRAIL_MAX_POINTS as _MAX
    except ImportError:
        from settings import SHIELD_MAX_TRAIL_POINTS as _MAX
    if len(trail) > _MAX:
        trail.pop(0)

    # ----- Wall bounce with bounds check (only while heading out) -----
    if not bullet.get('returning'):
        map_x = int(bullet['x'] / TILE_SIZE)
        map_y = int(bullet['y'] / TILE_SIZE)
        if 0 <= map_y < len(game_map) and 0 <= map_x < len(game_map[0]):
            tile = game_map[map_y][map_x]
            if tile in ['W', 'P']:
                bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                bullet['bounces'] = bullet.get('bounces',0)+1
                bullet['returning'] = True
        else:
            # Went off-map: trigger immediate return instead of deleting.
            bullet['returning'] = True
            # Recompute angle toward player so it heads back.
            dx = owner_player.x - bullet['x']
            dy = owner_player.y - bullet['y']
            bullet['angle'] = math.atan2(dy, dx)

    # ----- Zombie bounce + damage -----
    if zombies is not None:
        for z in zombies:
            if getattr(z, 'is_alive', True) and math.hypot(z.x - bullet['x'], z.y - bullet['y']) < z.radius:
                bullet['angle'] = math.atan2(-math.sin(bullet['angle']), -math.cos(bullet['angle']))
                bullet['bounces'] = bullet.get('bounces',0)+1
                if hasattr(z, 'take_damage'):
                    died = z.take_damage(bullet.get('damage', 20))
                    if died and hasattr(owner_player, 'zombie_blood_collected'):
                        owner_player.zombie_blood_collected += 1
                break

    # ----- Turn back after distance -----
    # Auto-return if bounce count exceeded
    if bullet.get('bounces',0) >= 4:
        bullet['returning'] = True
    # Return after max distance
    if (not bullet.get('returning') and math.hypot(bullet['x'] - bullet['start_x'], bullet['y'] - bullet['start_y']) >= bullet['max_distance']):
        bullet['returning'] = True

    # ----- Returning behaviour -----
    if bullet.get('returning'):
        dx = owner_player.x - bullet['x']
        dy = owner_player.y - bullet['y']
        bullet['angle'] = math.atan2(dy, dx)
        # Expanded catch radius to compensate for per–frame movement (prevents bounce when player is idle)
        catch_radius = owner_player.radius + bullet.get('radius', 10) + bullet.get('speed', 300) * dt
        if math.hypot(dx, dy) < catch_radius:
            owner_player.active_shield_throw = False
            if bullet in bullets:
                bullets.remove(bullet)
            return True

    return False


def draw_shield_bullet(screen, bullet):
    """Render the shield bullet with trail and sprite fallback."""
    # Draw trail
    for i in range(len(bullet['trail']) - 1):
        pygame.draw.line(screen, SHIELD_TRAIL_COLOR[:3], bullet['trail'][i], bullet['trail'][i + 1], 3)

    owner = bullet.get('owner')
    img = getattr(owner, 'shield_image', None) if owner else None
    if img:
        rect = img.get_rect(center=(bullet['x'], bullet['y']))
        screen.blit(img, rect)
    else:
        pygame.draw.circle(screen, (0, 180, 255), (int(bullet['x']), int(bullet['y'])), bullet.get('radius', 12))
