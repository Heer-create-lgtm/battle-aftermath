import math

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Game settings
TILE_SIZE = 40
MAP_WIDTH = SCREEN_WIDTH // TILE_SIZE
MAP_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

# Level specific settings
THRONE_ROOM_END_POS = (MAP_WIDTH / 2 * TILE_SIZE, 8 * TILE_SIZE)
END_LEVEL_RADIUS = TILE_SIZE

# Player initial settings for Throne Room
PLAYER_START_X = 16 * TILE_SIZE
PLAYER_START_Y = 15 * TILE_SIZE
PLAYER_START_ANGLE = -math.pi / 2
PLAYER_IMAGE_SIZE = 30 # pixels

# Player attributes
PLAYER_RADIUS = 10
PLAYER_SPEED = 200 # pixels per second
PLAYER_SPRINT_SPEED = 350 # pixels per second
PLAYER_ROT_SPEED = 3 # radians per second
MAX_HEALTH = 100
MAX_STAMINA = 100
STAMINA_DEPLETION_RATE = 25 # per second
STAMINA_REGEN_RATE = 15 # per second
STAMINA_SPRINT_PENALTY_DURATION = 2 # seconds

# Bullet settings
BULLET_SPEED = 700 # pixels per second
BULLET_RADIUS = 5
BULLET_COLOR = (255, 255, 0)  # Yellow

# Colors
UI_PANEL_BG = (10, 10, 30, 200)
HEALTH_BAR_BG = (80, 0, 0)
HEALTH_BAR_FG = (255, 0, 0)
STAMINA_BAR_BG = (0, 0, 80)
STAMINA_BAR_FG = (0, 0, 255)
GOD_GOLD = (255, 215, 0)
GOD_SILVER = (192, 192, 192)
GOD_BRONZE = (205, 127, 50)
WALL_COLOR = (200, 200, 200)
BG_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (150, 150, 150)
DARK_GRAY = (50, 50, 50)
DIALOGUE_TEXT_COLOR = (200, 200, 255)
STAFF_COLOR = (139, 69, 19) # A woody brown
CARPET_COLOR = (139, 0, 0) # Dark red
PILLAR_COLOR = (105, 105, 105) # Dim grey
GOD_EYE_COLOR = (255, 255, 255)
AURA_COLOR_GOLD = (255, 215, 0, 50)
AURA_COLOR_SILVER = (192, 192, 192, 50)
AURA_COLOR_BRONZE = (205, 127, 50, 50)

# Shield settings
SHIELD_COLOR = (0, 191, 255)

# Zombie settings
ZOMBIE_COLOR = (0, 100, 0) # Dark green
ZOMBIE_IMAGE_SIZE = 30 # pixels
ZOMBIE_HEALTH = 100
ZOMBIE_SPEED = 90 # pixels per second
ZOMBIE_DAMAGE = 10

# Human NPC settings
HUMAN_COLOR = (230, 230, 250) # Lavender
HUMAN_SPEED = 0.05
HUMAN_SCARED_DISTANCE = TILE_SIZE * 3

# Player Weapon Settings
SHOTGUN_PELLETS = 5           # Number of pellets fired per shot
SHOTGUN_SPREAD_DEGREES = 10   # Half-angle spread (degrees) for pellets
SHOTGUN_PELLET_DAMAGE = 12    # Damage per pellet
PELLET_SPRITE_SIZE = 10       # pixels
PLAYER_MAX_AMMO = 10
PLAYER_RELOAD_TIME = 1.5 # seconds
PLAYER_INVINCIBILITY_DURATION = 1.5 # seconds
PLAYER_BULLET_DAMAGE = 50
PLAYER_MAX_SHIELD_ENERGY = 100
PLAYER_SHIELD_DEPLETION_RATE = 40 # Energy per second
PLAYER_SHIELD_REGEN_RATE = 20 # Energy per second

# Python Boss settings
PYTHON_HEAD_COLOR = (85, 107, 47) # Dark Olive Green
PYTHON_BODY_COLOR = (107, 142, 35) # Olive Drab
PYTHON_EYE_COLOR = (255, 0, 0) # Red eyes
PYTHON_HEALTH = 30 #change this to 3000
PYTHON_SPEED = 120 # pixels per second
PYTHON_TURN_SPEED = 1.8 # radians per second
PYTHON_BODY_SEGMENTS = 20
PYTHON_BURROW_TIME = 4 # seconds
PYTHON_ATTACK_TIME = 3 # seconds
PYTHON_TELEGRAPH_TIME = 1.5 # seconds
PYTHON_TELEGRAPH_COLOR = (255, 165, 0, 100)
PYTHON_CHARGE_SPEED_MULTIPLIER = 4
PYTHON_CHARGE_TELEGRAPH_TIME = 0.75 # seconds
PYTHON_CHARGE_COLOR = (255, 0, 0, 100)
PYTHON_CHARGE_DAMAGE = 25
PYTHON_ENRAGE_HEALTH_THRESHOLD = 0.5
PYTHON_ENRAGE_SPEED_MULTIPLIER = 1.5
PYTHON_STUN_DURATION = 3 # seconds
PYTHON_STUN_EYE_COLOR = (255, 255, 0) # Yellow
PYTHON_ROAMING_TIME_MIN = 4 # seconds
PYTHON_ROAMING_TIME_MAX = 6 # seconds
PYTHON_RETREAT_DURATION = 0.5 # seconds
PYTHON_RETREAT_SPEED_MULTIPLIER = 1.5
PYTHON_DAMAGE = 25
CHANCE_TO_BURROW = 0.2
CHANCE_TO_CHARGE = 0.3

# UI Settings
BOSS_HEALTH_BAR_BG = (50, 0, 0)
BOSS_HEALTH_BAR_FG = (180, 0, 0)
SHIELD_BAR_BG = (0, 30, 50)
ZOMBIE_BLOOD_COLOR = (30, 220, 60, 180) # Green blood (RGBA) for zombies
HERO_BLOOD_COLOR = (200, 22, 22, 190) # Red blood (RGBA) for hero/player
# --- Extra Python Boss Visuals ---
POISON_TRAIL_COLOR = (0, 200, 70, 150)      # Green translucent
PYTHON_STRIPE_COLOR = (180, 210, 80)        # Lighter olive drab
PYTHON_SHADOW_COLOR = (0, 0, 0, 80)         # Soft shadow
PYTHON_ENRAGED_HEAD_COLOR = (220, 60, 60)   # Red-tinted for enraged head
DUST_COLOR = (160, 140, 50, 128)            # Brownish dust circle
SHIELD_BAR_FG = (0, 191, 255)

# --- Shield Boomerang (Q ability) ---
# Size (pixels) to scale the shield sprite to when rendered
SHIELD_IMAGE_SIZE = 40
# Speed of the flying shield in pixels per second
SHIELD_SPEED = 300
# Maximum one-way distance before the shield turns back (pixels)
SHIELD_MAX_DISTANCE = 350
# Damage dealt to enemies on hit
SHIELD_DAMAGE = 100
# Cooldown between throws (seconds)
SHIELD_COOLDOWN_TIME = 10
# Trail visuals (points = length of trail)
SHIELD_TRAIL_COLOR = (0, 180, 255, 180)  # bright blue with alpha
SHIELD_MAX_TRAIL_POINTS = 20  # number of points in the trail
SHIELD_TRAIL_MAX_POINTS = 15
# Shield energy ratio needed/consumed per throw
SHIELD_ENERGY_THROW_RATIO = 0.5

# New constants
SPRINT_SPEED = 350
STAMINA_COST = 30  # per second
STAMINA_REGEN = 15  # per second
SHIELD_DRAIN = 40  # per second
SHIELD_REGEN = 20  # per second 