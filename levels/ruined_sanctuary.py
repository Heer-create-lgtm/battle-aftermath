import pygame
import math
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, WHITE, MAX_HEALTH, BULLET_COLOR
from ui import draw_ui
from levels.dialogue import show_dialogue
from player import Player, shield_hit_sound
from shield_bullet import update_shield_bullet, draw_shield_bullet


class DragonBoss:
    """Ancient Dragon – breathes corruption flames, orbs, and executes swift dives."""
    def __init__(self, x, y):
        import random
        import math
        self.x, self.y = x, y
        self.health = 10  # increased for tougher fight
        self.max_health = 10
        self.radius = 70
        self.image = None
        try:
            img = pygame.image.load('assets/sprites/dragon.png').convert_alpha()
            self.image = pygame.transform.scale(img, (self.radius*2, self.radius*2))
        except Exception:
             pass
        
        # Phases: 1 (>=50%), 2 (>=20%), 3 (<20%)
        self.phase = 1
        
        # Load core sounds with channel management
        def _load(name, volume=0.7):
            try:
                sound = pygame.mixer.Sound(f"assets/music/{name}.ogg")
                sound.set_volume(volume)
                return sound
            except Exception as e:
                print(f"Could not load sound {name}: {e}")
                return None
                
        self.sfx = {
            "roar": _load("dragon_roar", 0.8),
            "fire": _load("fire_sweep", 0.6),
            "wing": _load("wing_flap", 0.5),
            "impact": _load("impact_hit", 0.7),
            "explode": _load("explosion_big", 0.8)
        }
        self.sound_channels = {}  # To track active sound channels
        self.last_attack = 0
        self.attack_delay = 850  # tightened attack cadence
        # Internal state for variable attacks
        self._flame_end = 0
        self._last_flame_emit = 0
        self.projectile_speed = 320  # phase 1 projectile speed
        self.move_speed = 80        # phase 1 glide speed
        # Dashing parameters
        self.is_dashing = False
        self._dash_vec = (0, 0)
        self._dash_time = 0
        self._last_pursuit_dash = 0  # cooldown timer
        # Play intro roar
        if self.sfx["roar"]: self.sfx["roar"].play()

    def _play_sound(self, sound_name):
        """Play a sound with channel management to prevent cutoff"""
        if sound_name in self.sfx and self.sfx[sound_name]:
            try:
                # Find an available channel
                channel = pygame.mixer.find_channel(True)
                if channel:
                    channel.play(self.sfx[sound_name])
                    # Store the channel if we need to reference it later
                    self.sound_channels[sound_name] = channel
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")

    def _update_phase(self, current_time):
        # Update phase based on health percentage
        health_pct = self.health / self.max_health
        new_phase = 3 if health_pct < 0.2 else (2 if health_pct < 0.5 else 1)
        if new_phase != self.phase:
            self.phase = new_phase
            # Phase-based scaling
            if self.phase == 1:
                self.attack_delay = 850
                self.projectile_speed = 320
                self.move_speed = 80
            elif self.phase == 2:
                self.attack_delay = 650
                self.projectile_speed = 360
                self.move_speed = 120
            else:
                self.attack_delay = 500
                self.projectile_speed = 400
                self.move_speed = 150
            self._play_sound("roar")

    def update(self, player, current_time, dt):
        import math, random
        self._update_phase(current_time)
        # Handle dash movement if active
        if self.is_dashing:
            # Leave flame trail during dash for area denial
            trail_interval = 0.12
            if not hasattr(self, '_last_trail_emit'):
                self._last_trail_emit = 0
            if current_time - self._last_trail_emit > trail_interval*1000:
                self._last_trail_emit = current_time
                if 'flame_trail' not in globals():
                    globals()['flame_trail'] = []
                globals()['flame_trail'].append({'x': self.x, 'y': self.y, 'timer': 2})
            self.x += self._dash_vec[0] * dt
            self.y += self._dash_vec[1] * dt
            self._dash_time -= dt
            if self._dash_time <= 0:
                self.is_dashing = False
        else:
            # Continuous glide toward player
            vec_x = player.x - self.x
            vec_y = player.y - self.y
            dist = math.hypot(vec_x, vec_y) or 1
            self.x += (vec_x/dist) * self.move_speed * dt
            self.y += (vec_y/dist) * self.move_speed * dt
            # Subtle vertical bob for life-like motion
            self.y += math.sin(current_time/500) * 15 * dt

            # Reactive dash to prevent easy circling
            if current_time - self._last_pursuit_dash > 2500 and dist < 300:
                self._last_pursuit_dash = current_time
                self.is_dashing = True
                dash_speed = self.move_speed * 4  # fast burst
                self._dash_vec = (vec_x/dist * dash_speed, vec_y/dist * dash_speed)
                self._dash_time = min(0.6, dist / dash_speed)
                # Start dash sound
                if self.sfx.get("wing"):
                    self.sfx["wing"].play()

        actions = None
        if not self.is_dashing and current_time - self.last_attack > self.attack_delay:
            self.last_attack = current_time
            # Different weightings by phase
            roll = random.random()
            # Phase-specific choices
            if self.phase == 1:
                table = [0.35,0.55,0.7,0.9,1.0]
            elif self.phase == 2:
                table = [0.20,0.40,0.60,0.80,1.0]
            else:
                table = [0.15,0.35,0.55,0.75,1.0]
            # Map roll to attack index simplifying branching below
            idx = next(i for i,v in enumerate(table) if roll<=v)
            # 0-radial,1-spread,2-flame,3-meteor,4-dash
            if idx==0:
                # Radial/Claw Slam analogue
                if self.sfx["impact"]: self.sfx["impact"].play()
                actions = []
                for i in range(12):
                    ang = i*(2*math.pi/12)
                    actions.append({'type':'projectile','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed*0.8,
                                     'radius':6,'damage':14,'color':(230,60,230)})
            elif idx==1:
                # Spread / Tail Whip
                if self.sfx["impact"]: self.sfx["impact"].play()
                actions = []
                base = math.atan2(player.y - self.y, player.x - self.x)
                for offset in (-0.30,0,0.30):
                    ang = base + offset
                    actions.append({'type':'projectile','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed,
                                     'radius':7,'damage':16,'color':(200,80,240)})
            elif idx==2:
                # Flame Breath sweep
                if self.sfx["fire"]: self.sfx["fire"].play()
                actions = []
                base = math.atan2(player.y - self.y, player.x - self.x)
                for i in range(-4,5):
                    ang = base + i*0.1
                    actions.append({'type':'flame','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed*0.9,
                                     'radius':5,'damage':10,'color':(255,120,40)})
            elif idx==3:
                # Meteor / Aerial firebomb
                summon = random.random() < (0.4 if self.phase==1 else 0.7)
                if self.sfx["wing"]: self.sfx["wing"].play()
                actions = []
                for i in range(6):
                    px = player.x + random.randint(-120,120)
                    actions.append({'type':'meteor','x':px,'y':-50,'angle':math.pi/2,'speed':self.projectile_speed*1.2,
                                     'radius':8,'damage':22,'color':(255,80,0)})
                if summon:
                    actions.append({'type':'spawn_minion','count':random.randint(2,3)})
            else:
                # Dash / Inferno dash
                if self.sfx["wing"]: self.sfx["wing"].play()
                self.is_dashing = True
                dest_x = random.randint(100, SCREEN_WIDTH-100)
                dest_y = random.randint(100, SCREEN_HEIGHT-100)
                vec_x = dest_x - self.x
                vec_y = dest_y - self.y
                length = math.hypot(vec_x, vec_y) or 1
                speed = 450 if self.phase==3 else 400
                self._dash_vec = (vec_x/length*speed, vec_y/length*speed)
                self._dash_time = length / speed
            if roll < 0.25:
                if actions is None:
                    actions = []
                for i in range(12):
                    ang = i * (2*math.pi/12)
                    actions.append({'type':'projectile','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed*0.8,
                                    'radius':6,'damage':14,'color':(230,60,230)})
            elif roll < 0.5:
                # 3-shot spread towards player
                actions = []
                base = math.atan2(player.y - self.y, player.x - self.x)
                for offset in (-0.30, 0, 0.30):
                    ang = base + offset
                    actions.append({'type':'projectile','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed,
                                    'radius':7,'damage':16,'color':(200,80,240)})
            elif roll < 0.65:
                # Slow tracking orb (larger, slower)
                angle = math.atan2(player.y - self.y, player.x - self.x)
                actions = {'type':'projectile','x':self.x,'y':self.y,'angle':angle,'speed':self.projectile_speed*0.6,
                           'radius':10,'damage':24,'color':(160,30,200)}
            elif roll < 0.8:
                # Flame-breath: spray 9 small fireballs in a narrow cone
                actions = []
                base = math.atan2(player.y - self.y, player.x - self.x)
                for i in range(-4,5):
                    ang = base + i*0.1
                    actions.append({'type':'flame','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed*0.9,
                                     'radius':5,'damage':10,'color':(255,120,40)})
            elif roll < 0.9:
                # Meteor rain: spawn 6 downward fireballs around player
                actions = []
                for i in range(6):
                    px = player.x + random.randint(-160, 160)
                    actions.append({'type':'meteor','x':px,'y':-60,'angle':math.pi/2,'speed':self.projectile_speed*1.25,
                                     'radius':9,'damage':26,'color':(255,80,0)})
            elif roll < 0.97:
                # Ring of Fire – full 24-shot flame circle around the boss
                actions = []
                if self.sfx.get("fire"):
                    self.sfx["fire"].play()
                for i in range(24):
                    ang = i * (2*math.pi/24)
                    actions.append({'type':'flame','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed*0.8,
                                     'radius':6,'damage':15,'color':(255,120,40)})
            elif roll < 0.985:
                # Tail swipe – semicircle 18-shot arc
                actions = []
                base = math.atan2(player.y - self.y, player.x - self.x)
                start = base - math.pi/2
                for i in range(18):
                    ang = start + i*(math.pi/18)
                    actions.append({'type':'tail','x':self.x,'y':self.y,'angle':ang,'speed':self.projectile_speed*0.7,
                                     'radius':6,'damage':14,'color':(200,200,60)})
            elif roll < 0.995:
                # Corner blast – punish campers by firing a wall of projectiles from a screen edge
                actions = []
                edge = random.choice(['left','right','top','bottom'])
                step = 40
                if edge in ('left','right'):
                    x = 0 if edge=='left' else SCREEN_WIDTH
                    ang = 0 if edge=='left' else math.pi
                    for y in range(0, SCREEN_HEIGHT+step, step):
                        actions.append({'type':'wall','x':x,'y':y,'angle':ang,'speed':self.projectile_speed*0.9,
                                         'radius':8,'damage':18,'color':(255,90,90)})
                else:
                    y = 0 if edge=='top' else SCREEN_HEIGHT
                    ang = math.pi/2 if edge=='top' else -math.pi/2
                    for x in range(0, SCREEN_WIDTH+step, step):
                        actions.append({'type':'wall','x':x,'y':y,'angle':ang,'speed':self.projectile_speed*0.9,
                                         'radius':8,'damage':18,'color':(255,90,90)})
            else:
                # Dive dash to new random location (no bullets)
                self.is_dashing = True
                dest_x = random.randint(100, SCREEN_WIDTH-100)
                dest_y = random.randint(100, SCREEN_HEIGHT-100)
                vec_x = dest_x - self.x
                vec_y = dest_y - self.y
                length = math.hypot(vec_x, vec_y)
                if length == 0:
                    length = 1
                speed = 400
                self._dash_vec = (vec_x/length * speed, vec_y/length * speed)
                self._dash_time = length / speed
        return actions

    def take_damage(self, dmg):
        self.health -= dmg
        if self.health<=0 and self.sfx["explode"]:
            self.sfx["explode"].play()
        return self.health <= 0

    def draw(self, screen):

        if self.image:
            screen.blit(self.image, (self.x - self.radius, self.y - self.radius))
        else:
            pygame.draw.circle(screen, (180, 40, 180), (int(self.x), int(self.y)), self.radius)
        # Health bar
        bar_w = 120
        pygame.draw.rect(screen, (100,0,0), (self.x-bar_w//2, self.y-self.radius-20, bar_w, 8))
        pygame.draw.rect(screen, (0,200,0), (self.x-bar_w//2, self.y-self.radius-20, bar_w*(self.health/self.max_health), 8))


def run_ruined_sanctuary(game_objects=None):
    import random
    """Level 3 – Ruined Sanctuary.
    A placeholder implementation that lets you test the level flow.
    Returns "VICTORY" when the lesser god is defeated or the choice is made,
    "GAME_OVER" if the player dies, and "MAIN_MENU" if they quit.
    """
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()

    # Use existing player or create a new one
    player = game_objects.get("player") if isinstance(game_objects, dict) else Player()
    player.x, player.y = SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2

    # --- Audio: play BGM ---
    try:
        pygame.mixer.music.load('assets/music/bgm.ogg')
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
    except Exception:
        pass  # file missing

    # Real boss
    boss = DragonBoss(SCREEN_WIDTH*0.75, SCREEN_HEIGHT//2)
    bullets = []  # boss bullets
    minions = []
    player_bullets = []
    # Visual effect timers (ground-pound)
    shake_timer = 0.0
    flash_timer = 0.0

    # Intro dialogue
    show_dialogue([
        "You step into the once-holy sanctuary, now rotten with decay…",
        "The ground trembles as an Ancient Dragon emerges from the shadows…",
        "Dragon: 'Intruder… my flames will test your worth.'",
        "Dragon: 'Survive my fury if you can!'",
    ])

    running = True
    while running:
        dt = clock.tick(60)/1000.0
        current_time = pygame.time.get_ticks()
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return "MAIN_MENU"
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "MAIN_MENU"
        # Player input
        keys = pygame.key.get_pressed()
        from mechanics import update_player_state, handle_player_input
        # Ruined sanctuary uses an open area; create a dummy empty map for collisions
        if 'game_map' not in locals():
            game_map = [[' ' for _ in range(SCREEN_WIDTH // TILE_SIZE + 1)] for _ in range(SCREEN_HEIGHT // TILE_SIZE + 1)]
        update_player_state(player, keys, game_map, dt)
        handle_player_input(player, player_bullets, events)

        # --- Decay visual timers ---
        if shake_timer > 0:
            shake_timer -= dt
        if flash_timer > 0:
            flash_timer -= dt

        # ---- Ground Pound impact (no damage to Dragon) ----
        if player.gp_triggered:
            player.gp_triggered = False
            GP_RADIUS = 250
            for m in minions:
                dist = math.hypot(m.x - player.x, m.y - player.y)
                if dist <= GP_RADIUS:
                    m.stun_timer = 2.0
                    if dist > 0:
                        kx = (m.x - player.x)/dist * 60
                        ky = (m.y - player.y)/dist * 60
                        m.x += kx
                        m.y += ky
            shake_timer = 0.4
            flash_timer = 0.15

        # Boss update
        act = boss.update(player, current_time, dt)
        if act:
            if isinstance(act, list):
                for a in act:
                    if a.get('type') == 'spawn_minion':
                        # Minion spawning disabled for Dragon boss per updated design
                        continue
                    bullets.append(a)
            else:
                bullets.append(act)

        # Update player bullets
        for pb in player_bullets[:]:
            speed = pb.get('speed', 350)
            pb['x'] += math.cos(pb['angle'])*speed*dt
            pb['y'] += math.sin(pb['angle'])*speed*dt
            if pb.get('type') == 'shield':
                update_shield_bullet(pb, player_bullets, dt, game_map, player, zombies=minions)
            if pb['x']<0 or pb['x']>SCREEN_WIDTH or pb['y']<0 or pb['y']>SCREEN_HEIGHT:
                player_bullets.remove(pb); continue
            # hit boss

            if math.hypot(boss.x-pb['x'], boss.y-pb['y']) < boss.radius+4:
                if boss.take_damage(pb.get('damage',20)):
                    show_dialogue([
                        "The dragon collapses, smoke billowing from its scales…",
                        "Dragon: 'You… are stronger than the flames.'",
                    ])
                    return "VICTORY"
                if pb.get('type') == 'shield':
                    pb['returning'] = True
                    pb['damage'] = 0
                else:
                    player_bullets.remove(pb)
        # Update minions
        for m in minions[:]:
            m.update(player.x, player.y, game_map, dt)
            if not m.is_alive:
                minions.remove(m)
            else:
                # minion attacks (simple contact damage)
                if math.hypot(player.x-m.x, player.y-m.y) < m.radius+player.radius:
                    player.take_damage(8*dt)  # Respect shield and play sound
                    if player.health<=0:
                        return "GAME_OVER"
        # Update boss bullets
        for b in bullets[:]:
            b['x'] += math.cos(b['angle'])*b['speed']*dt
            b['y'] += math.sin(b['angle'])*b['speed']*dt
            if b['x']<0 or b['x']>SCREEN_WIDTH or b['y']<0 or b['y']>SCREEN_HEIGHT:
                bullets.remove(b); continue
            if math.hypot(player.x-b['x'], player.y-b['y']) < b['radius']+player.radius:
                if player.is_shielding and player.shield_energy>0:
                    player.shield_energy = max(0, player.shield_energy - 4)
                    if shield_hit_sound:
                        shield_hit_sound.play()
                else:
                    player.health -= b['damage']
                    if player.health<=0:
                        return "GAME_OVER"
                bullets.remove(b)


        # Background ruined tiles
        screen.fill((40, 30, 40))
        for i in range(0, SCREEN_WIDTH, 60):
            pygame.draw.rect(screen, (60,50,60), (i,0,4,SCREEN_HEIGHT))
        for j in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.rect(screen, (60,50,60), (0,j,SCREEN_WIDTH,4))
        # Debris
        for _ in range(6):
            pygame.draw.rect(screen,(70,60,70), (random.randint(0,SCREEN_WIDTH-20), random.randint(0,SCREEN_HEIGHT-20), random.randint(10,25),4))
        # Draw minions
        for m in minions:
            m.draw(screen)
        # Draw boss
        boss.draw(screen)
        # Draw enemy projectiles
        for b in bullets:
            pygame.draw.circle(screen, b.get('color',(200,50,200)), (int(b['x']), int(b['y'])), b['radius'])

        # Draw player bullets (normal and shield)
        for pb in player_bullets:
            if pb.get('type') == 'shield':
                draw_shield_bullet(screen, pb)
            else:
                pygame.draw.circle(screen, BULLET_COLOR, (int(pb['x']), int(pb['y'])), pb.get('radius', 4))
        # Draw player & UI
        player.draw(screen)
        draw_ui(screen, player)

        # ---- Flash overlay ----
        if flash_timer > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surf.fill((255, 255, 255))
            alpha = int(255 * (flash_timer / 0.15))
            flash_surf.set_alpha(alpha)
            screen.blit(flash_surf, (0, 0))

        # ---- Apply screen shake ----
        if shake_timer > 0:
            offset = (random.randint(-6, 6), random.randint(-6, 6))
            shake_frame = screen.copy()
            screen.fill((0, 0, 0))
            screen.blit(shake_frame, offset)
        pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    run_ruined_sanctuary()
