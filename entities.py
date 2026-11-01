from dataclasses import dataclass, field
import math
from typing import Optional

import config as C


@dataclass(eq=False)
class Building:
    team: str
    kind: str
    x: float
    y: float
    hp: float = 0
    progress: float = 0
    cooldown: float = 0
    queue: list = field(default_factory=list)
    production: float = 0
    vein: Optional[int] = None
    damage_effect_cooldown: float = 0

    # Initialize building health from its configured type when not provided.
    def __post_init__(self):
        if not self.hp:
            self.hp = C.BUILDINGS[self.kind]["hp"]

    # Return the configured statistics for this building type.
    @property
    def stats(self):
        return C.BUILDINGS[self.kind]

    # Check whether construction progress has reached the required time.
    @property
    def complete(self):
        return self.progress >= self.stats["time"]

    # Return half of the building's configured size.
    @property
    def radius(self):
        return self.stats["size"] / 2

    # Return the faction-specific building name when available.
    @property
    def name(self):
        return C.FACTIONS[self.team].get(self.kind, self.stats).get("name", self.stats["name"])


@dataclass(eq=False)
class Tank:
    team: str
    kind: str
    x: float
    y: float
    hp: float = 0
    cooldown: float = 0
    destination: Optional[tuple] = None
    target: Optional[object] = None
    waypoints: list = field(default_factory=list)
    path_goal: Optional[tuple] = None
    repath: float = 0
    body_angle: float = 0
    turret_angle: float = 0
    dust_cooldown: float = 0
    damage_effect_cooldown: float = 0
    previous_x: float = field(init=False, repr=False)
    previous_y: float = field(init=False, repr=False)
    previous_body_angle: float = field(init=False, repr=False)
    previous_turret_angle: float = field(init=False, repr=False)

    # Initialize tank health and the previous render state.
    def __post_init__(self):
        if not self.hp:
            self.hp = self.stats["hp"]
        self.snapshot_render_state()

    # Save the current position and angles for render interpolation.
    def snapshot_render_state(self):
        self.previous_x, self.previous_y = self.x, self.y
        self.previous_body_angle = self.body_angle
        self.previous_turret_angle = self.turret_angle

    # Return faction-specific statistics for this tank type.
    @property
    def stats(self):
        return C.FACTIONS[self.team][self.kind]

    # Return the tank's configured display name.
    @property
    def name(self):
        return self.stats["name"]

    # Rotate a local offset using the game's screen-coordinate convention.
    @staticmethod
    def _rotate_offset(x, y, angle):
        radians = math.radians(angle)
        cosine, sine = math.cos(radians), math.sin(radians)
        return x * cosine + y * sine, -x * sine + y * cosine

    # Return the sprite pivot and muzzle settings for Hammer or Apocalypse tanks.
    def _turret_profile(self):
        if self.team == "B" and self.kind == "tank1":
            return (C.HAMMER_SOURCE_SIZE, C.HAMMER_SPRITE_SIZE,
                    C.HAMMER_TURRET_PIVOT, C.HAMMER_ART_ROTATION, (C.HAMMER_BARREL_TIP,))
        if self.team == "B" and self.kind == "tank2":
            return (C.APOCALYPSE_SOURCE_SIZE, C.APOCALYPSE_SPRITE_SIZE,
                    C.APOCALYPSE_TURRET_PIVOT, C.APOCALYPSE_ART_ROTATION, C.APOCALYPSE_BARREL_TIPS)
        return None

    # Calculate the turret mount offset for the current or supplied body angle.
    def turret_mount_offset(self, body_angle=None):
        profile = self._turret_profile()
        if profile is None:
            return 0.0, 0.0
        (source_w, source_h), (width, height), (pivot_x, pivot_y), art_rotation, _ = profile
        x = (pivot_x - source_w / 2) * width / source_w
        y = (pivot_y - source_h / 2) * height / source_h
        angle = self.body_angle if body_angle is None else body_angle
        return self._rotate_offset(x, y, angle + art_rotation)

    # Compute the world-space firing points for the tank's cannons.
    def muzzle_positions(self):
        if self.team == "A" and self.kind == "tank2":
            source_w, source_h = C.MIRAGE_SOURCE_SIZE
            width, height = C.MIRAGE_SPRITE_SIZE
            tip_x, tip_y = C.MIRAGE_BARREL_TIP
            x = (tip_x - source_w / 2) * width / source_w
            y = (tip_y - source_h / 2) * height / source_h
            dx, dy = self._rotate_offset(x, y, self.body_angle + C.MIRAGE_ART_ROTATION)
            return ((self.x + dx, self.y + dy),)
        profile = self._turret_profile()
        if profile is None:
            return ((self.x, self.y),)
        mount_x, mount_y = self.turret_mount_offset()
        (source_w, source_h), (width, height), (pivot_x, pivot_y), art_rotation, tips = profile
        result = []
        for tip_x, tip_y in tips:
            x = (tip_x - pivot_x) * width / source_w
            y = (tip_y - pivot_y) * height / source_h
            offset_x, offset_y = self._rotate_offset(x, y, self.turret_angle + art_rotation)
            result.append((self.x + mount_x + offset_x, self.y + mount_y + offset_y))
        return tuple(result)

    # Return the first firing point for this tank.
    def muzzle_position(self):
        return self.muzzle_positions()[0]


@dataclass
class DustParticle:
    x: float
    y: float
    radius: float
    lifetime: float
    age: float = 0


@dataclass
class DamageParticle:
    owner: object
    velocity_x: float
    velocity_y: float
    radius: float
    lifetime: float
    age: float = 0


@dataclass
class Shot:
    x: float
    y: float
    end_x: float
    end_y: float
    color: tuple
    age: float = 0.15
