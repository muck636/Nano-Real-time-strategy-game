"""First-version balance and layout values."""

WIDTH, HEIGHT = 1280, 720
START_BUTTONS = {"A": (378, 524, 240, 62), "B": (662, 524, 240, 62)}
MAP_WIDTH = 980
WORLD_WIDTH, WORLD_HEIGHT = 3920, 1440
FPS = 60
RENDER_FPS = 240
GRID = 28
PATHS_PER_TICK = 2
ROTATION_CACHE_SIZE = 720
BUILD_RADIUS = 225
UNIT_RADIUS = 15
START_MONEY = 2500
BASE_VEINS = ((225, 610), (385, 585), (445, 810))
VEINS = BASE_VEINS + tuple((WORLD_WIDTH - x, y) for x, y in BASE_VEINS)
STARTS = {"A": ((330, 720), (300, 850)), "B": ((WORLD_WIDTH - 330, 720), (WORLD_WIDTH - 300, 850))}
CAMERA_SPEED = 540
CAMERA_EDGE_SCROLL_MARGIN = 32
MUSIC_DIRECTORY = "assets/music"
MUSIC_TRACK_NAMES = {
    "menu": "Soviet March",
    "bgm1": "1_(beginning)",
    "bgm2": "Combat_2_(triumphal)",
    "bgm3": "Combat_1_(Losing)",
    "combat3": "Combat_3_(triumphal)",
    "balance": "ExploringinHavana(balance)",
}
MUSIC_EXTENSIONS = (".ogg", ".mp3", ".wav")
MUSIC_BALANCE_DELAY = 5.0
MUSIC_VOLUME = 0.5
MUSIC_FADE_IN_MS = 300
REPAIR_HP_PER_SECOND = 45
REPAIR_COST_PER_HP = 0.4
SELL_REFUND_RATIO = 0.5
LOW_HEALTH_THRESHOLD = 0.35
DAMAGE_PARTICLE_INTERVAL = 0.15
DAMAGE_PARTICLE_RADIUS_RANGE = (4.0, 7.5)
DAMAGE_PARTICLE_LIFETIME_RANGE = (0.55, 0.85)
DAMAGE_PARTICLE_DRIFT_RANGE = (18, 32)
GUARDIAN_SPRITE_SIZE = (64, 64)
MIRAGE_SPRITE_SIZE = (64, 64)
MIRAGE_SOURCE_SIZE = (32, 32)
MIRAGE_BARREL_TIP = (16, 5)
MIRAGE_ART_ROTATION = 0
MIRAGE_AIM_TOLERANCE = 1.0
HAMMER_SPRITE_SIZE = (64, 64)
HAMMER_SOURCE_SIZE = (32, 32)
HAMMER_TURRET_PIVOT = (16, 10)
HAMMER_BARREL_TIP = (10, 29)
HAMMER_ART_ROTATION = 180
APOCALYPSE_SPRITE_SIZE = (64, 64)
APOCALYPSE_SOURCE_SIZE = (32, 32)
APOCALYPSE_TURRET_PIVOT = (16, 14)
APOCALYPSE_BARREL_TIPS = ((11.5, 32), (19.5, 32))
APOCALYPSE_ART_ROTATION = 180
TANK_DUST_INTERVAL = 0.09
TANK_DUST_REAR_OFFSET = 19
TANK_DUST_TRACK_OFFSET = 10
TANK_DUST_POSITION_JITTER = 1.5
TANK_DUST_RADIUS_RANGE = (3.5, 6.5)
TANK_DUST_LIFETIME_RANGE = (0.55, 0.9)
TANK_BODY_TURN_SPEED = 320
TANK_TURRET_TURN_SPEED = 420
APOCALYPSE_TURRET_TURN_SPEED = TANK_TURRET_TURN_SPEED / 2
APOCALYPSE_AIM_TOLERANCE = 0.01

BUILDINGS = {
    "hq": dict(name="Construction Yard", cost=0, hp=1100, size=66, time=0, power=0, supply=0),
    "power": dict(name="Power Plant", cost=500, hp=520, size=54, time=7, power=0, supply=100),
    "mine": dict(name="Mine", cost=600, hp=460, size=54, time=8, power=10, supply=0, income=30),
    "factory": dict(name="War Factory", cost=900, hp=760, size=66, time=11, power=20, supply=0),
    "tech": dict(name="Tech Center", cost=1200, hp=650, size=60, time=12, power=20, supply=0),
    "tower1": dict(name="T1 Tower", cost=500, hp=350, size=42, time=7, power=10, supply=0, range=190),
    "tower2": dict(name="T2 Tower", cost=900, hp=450, size=48, time=10, power=20, supply=0, range=220),
}

FACTIONS = {
    "A": {
        "color": (66, 173, 237),
        "tank1": dict(name="Guardian", cost=850, hp=300, damage=30, cooldown=1.0, speed=105, time=7, range=135, moving_fire=True),
        "tank2": dict(name="Mirage", cost=1600, hp=320, damage=60, cooldown=1.0, speed=90, time=12, range=270, moving_fire=False),
        "tower1": dict(name="Missile Tower", cost=500, damage=40, cooldown=1.0),
        "tower2": dict(name="Prism Tower", cost=900, damage=90, cooldown=1.5),
    },
    "B": {
        "color": (232, 99, 88),
        "tank1": dict(name="Hammer", cost=1000, hp=360, damage=34, cooldown=1.0, speed=85, time=8, range=135, moving_fire=True),
        "tank2": dict(name="Apocalypse", cost=2000, hp=650, damage=62, cooldown=1.0, speed=65, time=13, range=135, moving_fire=False),
        "tower1": dict(name="Sentry Gun", cost=500, damage=10, cooldown=0.25),
        "tower2": dict(name="Tesla Coil", cost=1000, damage=100, cooldown=1.5),
    },
}

COLORS = {
    "ground": (57, 83, 70), "grid": (65, 94, 78), "panel": (28, 37, 48),
    "text": (235, 242, 244), "muted": (165, 180, 188), "good": (108, 214, 135),
    "bad": (242, 110, 99), "ore": (220, 182, 91), "outline": (12, 20, 26),
    "dust": (212, 190, 157),
    "damage_particle": (232, 80, 59),
}
