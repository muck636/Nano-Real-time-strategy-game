"""Resources, construction, movement, combat and victory rules."""

import math
import random

import config as C
from entities import Building, DamageParticle, DustParticle, Shot, Tank
from pathing import blocked, clear_segment, nearest_open, route
import terrain


class Game:
    # Initialize match state, resources, and the starting buildings for both teams.
    def __init__(self, player_team):
        self.player = player_team
        self.enemy = "B" if player_team == "A" else "A"
        self.money = {"A": float(C.START_MONEY), "B": float(C.START_MONEY)}
        self.god_mode = False
        self.buildings = []
        self.tanks = []
        self.shots = []
        self.dust_particles = []
        self.damage_particles = []
        self._dust_random = random.Random()
        self._damage_random = random.Random()
        self.repairing = set()
        self._paths_remaining = None
        self.winner = None
        self.combat_event_serial = 0
        self.message = "Build a mine on a gold deposit."
        self.message_time = 6.0
        for team in ("A", "B"):
            hq, plant = C.STARTS[team]
            self.buildings.append(Building(team, "hq", *hq))
            p = Building(team, "power", *plant)
            p.progress = p.stats["time"]
            self.buildings.append(p)

    # Display a temporary in-game message.
    def notify(self, message):
        self.message = message
        self.message_time = 3.2

    # Return living team buildings that match the requested filters.
    def team_buildings(self, team, kind=None, complete_only=False):
        return [b for b in self.buildings if b.hp > 0 and b.team == team and
                (kind is None or b.kind == kind) and (not complete_only or b.complete)]

    # Sum living tanks' battle scores weighted by their remaining health.
    def unit_battle_score(self, team):
        return sum(
            tank.stats.get("battle_score", tank.stats["cost"]) * min(1.0, tank.hp / tank.stats["hp"])
            for tank in self.tanks if tank.team == team and tank.hp > 0
        )

    # Check whether the team has a completed Tech Center.
    def has_tech(self, team):
        return bool(self.team_buildings(team, "tech", True))

    # Calculate power supply and demand from completed team buildings.
    def power(self, team):
        ready = self.team_buildings(team, complete_only=True)
        return (sum(b.stats["supply"] for b in ready), sum(b.stats["power"] for b in ready))

    # Check whether the team's power supply meets its demand.
    def powered(self, team):
        supply, demand = self.power(team)
        return supply >= demand

    # Look up the team's cost for a building or unit.
    def cost(self, team, kind):
        if kind in ("tower1", "tower2", "tank1", "tank2"):
            return C.FACTIONS[team][kind]["cost"]
        return C.BUILDINGS[kind]["cost"]

    # Check whether god mode grants this team unlimited funds.
    def unlimited_funds(self, team):
        return self.god_mode and team == self.player

    # Toggle god mode and finish eligible player construction and queued units.
    def set_god_mode(self, enabled):
        self.god_mode = enabled
        if enabled:
            for building in self.team_buildings(self.player):
                building.progress = building.stats["time"]
            for factory in self.team_buildings(self.player, "factory", True):
                while factory.queue and self._spawn(factory, factory.queue[0]):
                    factory.queue.pop(0)
                    factory.production = 0
        self.notify("God mode ON: instant construction and units" if enabled else "God mode OFF")

    # Return a placement error, or None if the building can be placed.
    def can_place(self, team, kind, x, y, check_money=True):
        if kind not in C.BUILDINGS or kind == "hq":
            return "Unavailable building"
        if not self.team_buildings(team, "hq", True):
            return "Construction Yard required"
        if kind == "tower2" and not self.has_tech(team):
            return "Tech Center required"
        if check_money and not self.unlimited_funds(team) and self.money[team] < self.cost(team, kind):
            return "Insufficient funds"
        size = C.BUILDINGS[kind]["size"] / 2
        if x - size < 8 or x + size > C.WORLD_WIDTH - 8 or y - size < 8 or y + size > C.WORLD_HEIGHT - 8:
            return "Outside map"
        if terrain.rect_blocked(x - size, y - size, x + size, y + size):
            return "Cannot build on water or mountains"
        vein_id = next((i for i, v in enumerate(C.VEINS) if math.dist(v, (x, y)) <= 8), None)
        if kind == "mine" and vein_id is None:
            return "Place on a gold deposit"
        if kind != "mine" and any(abs(x-v[0]) < size+24 and abs(y-v[1]) < size+24 for v in C.VEINS):
            return "Gold deposit blocked"
        if any(math.dist((x, y), (b.x, b.y)) < size + b.radius + 10 for b in self.buildings if b.hp > 0):
            return "Building overlap"
        if kind == "mine" and any(b.vein == vein_id for b in self.buildings if b.hp > 0):
            return "Deposit occupied"
        if not any(math.dist((x, y), (b.x, b.y)) <= C.BUILD_RADIUS for b in self.team_buildings(team, complete_only=True)):
            return "Outside build range"
        return None

    # Snap mines to deposits, validate placement, and create the building.
    def place(self, team, kind, x, y):
        if kind == "mine":
            nearest = min(C.VEINS, key=lambda v: math.dist(v, (x, y)))
            if math.dist(nearest, (x, y)) > 34:
                return "Place on a gold deposit"
            x, y = nearest
        reason = self.can_place(team, kind, x, y)
        if reason:
            return reason
        if not self.unlimited_funds(team):
            self.money[team] -= self.cost(team, kind)
        b = Building(team, kind, x, y)
        if self.unlimited_funds(team):
            b.progress = b.stats["time"]
        if kind == "mine":
            b.vein = C.VEINS.index((x, y))
        self.buildings.append(b)
        return None

    # Validate a factory order and queue or instantly spawn the requested tank.
    def train(self, team, factory, kind):
        if factory not in self.buildings or factory.team != team or factory.kind != "factory" or not factory.complete:
            return "Select a completed War Factory"
        if kind not in ("tank1", "tank2"):
            return "Unavailable unit"
        if kind == "tank2" and not self.has_tech(team):
            return "Tech Center required"
        if not self.unlimited_funds(team) and self.money[team] < self.cost(team, kind):
            return "Insufficient funds"
        if self.unlimited_funds(team):
            return None if self._spawn(factory, kind) else "No open spawn point"
        self.money[team] -= self.cost(team, kind)
        factory.queue.append(kind)
        return None

    # Start or stop repairing an eligible building.
    def toggle_repair(self, team, building):
        if building not in self.buildings or building.team != team or not building.complete:
            return "Select a completed building"
        if building in self.repairing:
            self.repairing.remove(building)
        elif building.hp < building.stats["hp"]:
            self.repairing.add(building)
        else:
            return "Building is at full health"
        return None

    # Remove an eligible building and refund its health-adjusted value.
    def sell(self, team, building):
        if building not in self.buildings or building.team != team:
            return "Select your building"
        if building.kind == "hq":
            return "Construction Yard cannot be sold"
        refund = self.cost(team, building.kind) * C.SELL_REFUND_RATIO
        refund *= max(0, building.hp) / building.stats["hp"]
        self.money[team] += refund
        self.repairing.discard(building)
        building.hp = 0
        self.buildings.remove(building)
        self._resolve_winner()
        self.notify(f"Sold {building.name} for ${int(refund)}")
        return None

    # Update the winner when a team has no remaining buildings.
    def _resolve_winner(self):
        lost = {team: not self.team_buildings(team) for team in ("A", "B")}
        if lost["A"] and lost["B"]:
            self.winner = "draw"
        elif lost["A"]:
            self.winner = "B"
        elif lost["B"]:
            self.winner = "A"

    # Assign formation destinations and reset paths for the selected tanks.
    def issue_move(self, tanks, point):
        columns = max(1, math.ceil(math.sqrt(len(tanks))))
        rows = max(1, math.ceil(len(tanks) / columns))
        spacing = 2 * C.UNIT_RADIUS + 8
        for index, tank in enumerate(tanks):
            offset = ((index % columns) - (columns - 1) / 2) * spacing, \
                     ((index // columns) - (rows - 1) / 2) * spacing
            destination = (max(16, min(C.WORLD_WIDTH - 16, point[0] + offset[0])),
                           max(16, min(C.WORLD_HEIGHT - 16, point[1] + offset[1])))
            tank.destination = nearest_open(destination, self.buildings) or (tank.x, tank.y)
            tank.target = None
            tank.waypoints.clear()
            tank.path_goal = None
            tank.repath = 0

    # Assign an enemy target and clear movement orders for selected tanks.
    def issue_attack(self, tanks, target):
        for tank in tanks:
            tank.target = target
            tank.destination = None
            tank.waypoints.clear()
            tank.path_goal = None
            tank.repath = 0

    # Find a selectable tank or building at a world position.
    def object_at(self, x, y):
        for tank in reversed(self.tanks):
            guardian = tank.team == "A" and tank.kind == "tank1"
            mirage = tank.team == "A" and tank.kind == "tank2"
            hammer = tank.team == "B" and tank.kind == "tank1"
            apocalypse = tank.team == "B" and tank.kind == "tank2"
            hit_radius = 30 if mirage else (23 if guardian or hammer or apocalypse else C.UNIT_RADIUS + 5)
            dx, dy = x - tank.x, y - tank.y
            if math.hypot(dx, dy) < hit_radius:
                return tank
            if guardian:
                angle = math.radians(tank.turret_angle)
                forward_x, forward_y = -math.sin(angle), -math.cos(angle)
                along = dx * forward_x + dy * forward_y
                sideways = abs(dx * forward_y - dy * forward_x)
                if 0 <= along <= 32 and sideways <= 7:
                    return tank
            elif hammer or apocalypse:
                mount_x, mount_y = tank.turret_mount_offset()
                pivot_x, pivot_y = tank.x + mount_x, tank.y + mount_y
                for muzzle_x, muzzle_y in tank.muzzle_positions():
                    vx, vy = muzzle_x - pivot_x, muzzle_y - pivot_y
                    length = math.hypot(vx, vy)
                    if length:
                        ax, ay = x - pivot_x, y - pivot_y
                        along = (ax * vx + ay * vy) / length
                        sideways = abs(ax * vy - ay * vx) / length
                        if 0 <= along <= length + 3 and sideways <= 8:
                            return tank
        for b in reversed(self.buildings):
            if abs(x - b.x) <= b.radius and abs(y - b.y) <= b.radius:
                return b
        return None

    # Place a newly produced tank at a free position near its factory.
    def _spawn(self, factory, kind):
        for radius in (factory.radius + 28, factory.radius + 48, factory.radius + 72, factory.radius + 100):
            for angle in range(0, 360, 30):
                theta = math.radians(angle)
                x = factory.x + math.cos(theta) * radius
                y = factory.y + math.sin(theta) * radius
                if not blocked(x, y, self.buildings) and all(math.dist((x, y), (t.x, t.y)) > 2*C.UNIT_RADIUS for t in self.tanks):
                    self.tanks.append(Tank(factory.team, kind, x, y))
                    return True
        return False

    # Advance a tank along a collision-checked route toward its goal.
    def _move_tank(self, tank, goal, dt):
        tank.repath = max(0, tank.repath - dt)
        changed_goal = tank.path_goal is not None and math.dist(goal, tank.path_goal) > 25
        if tank.path_goal is None or (tank.repath == 0 and (changed_goal or not tank.waypoints)):
            if self._paths_remaining is not None:
                if self._paths_remaining <= 0:
                    return False
                self._paths_remaining -= 1
            tank.waypoints = route((tank.x, tank.y), goal, self.buildings)
            tank.path_goal = goal
            tank.repath = 0.5
        if not tank.waypoints:
            return False
        for index in range(len(tank.waypoints) - 1, 0, -1):
            if clear_segment((tank.x, tank.y), tank.waypoints[index], self.buildings):
                del tank.waypoints[:index]
                break
        remaining = tank.stats["speed"] * dt
        moved = False
        while tank.waypoints and remaining > 0:
            waypoint = tank.waypoints[0]
            dx, dy = waypoint[0] - tank.x, waypoint[1] - tank.y
            distance = math.hypot(dx, dy)
            if distance < 0.01:
                tank.waypoints.pop(0)
                continue
            travel = min(distance, remaining)
            nx, ny = tank.x + dx / distance * travel, tank.y + dy / distance * travel
            if blocked(nx, ny, self.buildings):
                tank.repath = 0
                tank.waypoints.clear()
                break
            facing = self._angle_to(tank.x, tank.y, nx, ny)
            tank.body_angle = self._turn_toward(
                tank.body_angle, facing, C.TANK_BODY_TURN_SPEED * travel / tank.stats["speed"])
            tank.x, tank.y = nx, ny
            moved = True
            remaining -= travel
            if travel >= distance - 0.01:
                tank.waypoints.pop(0)
        return moved

    # Choose an approach point near an attack target.
    def _attack_goal(self, tank, target):
        dx, dy = tank.x - target.x, tank.y - target.y
        distance = max(0.001, math.hypot(dx, dy))
        radius = target.radius if isinstance(target, Building) else C.UNIT_RADIUS
        stop = min(tank.stats["range"] * 0.75, radius + C.UNIT_RADIUS + 22)
        return (target.x + dx / distance * stop, target.y + dy / distance * stop)

    # Find the nearest living enemy within the attack radius.
    def _acquire(self, attacker, radius):
        enemies = [t for t in self.tanks if t.team != attacker.team and t.hp > 0]
        enemies += [b for b in self.buildings if b.team != attacker.team and b.hp > 0]
        nearby = [obj for obj in enemies if math.dist((attacker.x, attacker.y), (obj.x, obj.y)) <= radius]
        return min(nearby, key=lambda obj: math.dist((attacker.x, attacker.y), (obj.x, obj.y))) if nearby else None

    # Compute a facing angle between two world positions.
    @staticmethod
    def _angle_to(x, y, target_x, target_y):
        return -math.degrees(math.atan2(target_x - x, y - target_y))

    # Turn toward a target angle by no more than the allowed step.
    @staticmethod
    def _turn_toward(current, desired, max_step):
        difference = (desired - current + 180) % 360 - 180
        return (current + max(-max_step, min(max_step, difference))) % 360

    # Resolve overlapping tanks without moving them into blocked terrain.
    def _separate_tanks(self):
        for _ in range(2):
            for index, first in enumerate(self.tanks):
                for second in self.tanks[index + 1:]:
                    dx, dy = second.x - first.x, second.y - first.y
                    distance = math.hypot(dx, dy)
                    overlap = 2 * C.UNIT_RADIUS - distance
                    if overlap <= 0.5:
                        continue
                    if distance < 0.001:
                        dx, dy, distance = 1, 0, 1
                    ux, uy = dx / distance, dy / distance
                    first_pos = (first.x - ux * overlap / 2, first.y - uy * overlap / 2)
                    second_pos = (second.x + ux * overlap / 2, second.y + uy * overlap / 2)
                    first_free = not blocked(*first_pos, self.buildings)
                    second_free = not blocked(*second_pos, self.buildings)
                    if first_free and second_free:
                        first.x, first.y = first_pos
                        second.x, second.y = second_pos
                    elif first_free:
                        candidate = (first.x - ux * overlap, first.y - uy * overlap)
                        if not blocked(*candidate, self.buildings):
                            first.x, first.y = candidate
                    elif second_free:
                        candidate = (second.x + ux * overlap, second.y + uy * overlap)
                        if not blocked(*candidate, self.buildings):
                            second.x, second.y = candidate

    # Advance the economy, construction, movement, combat, effects, and victory state.
    def update(self, dt):
        if self.winner is not None:
            return
        dt = min(dt, 0.08)
        self._paths_remaining = C.PATHS_PER_TICK
        for tank in self.tanks:
            tank.snapshot_render_state()
        self.message_time = max(0, self.message_time - dt)
        self.shots = [s for s in self.shots if s.age > dt]
        for shot in self.shots:
            shot.age -= dt
        for particle in self.dust_particles:
            particle.age += dt
        self.dust_particles = [particle for particle in self.dust_particles if particle.age < particle.lifetime]
        for particle in self.damage_particles:
            particle.age += dt
        self.damage_particles = [particle for particle in self.damage_particles if particle.age < particle.lifetime]

        power_ok = {team: self.powered(team) for team in ("A", "B")}
        damage = []
        dust_emitters = []
        for b in list(self.buildings):
            b.cooldown = max(0, b.cooldown - dt)
            if not b.complete:
                if self.unlimited_funds(b.team):
                    b.progress = b.stats["time"]
                elif power_ok[b.team] or b.kind == "power":
                    b.progress = min(b.stats["time"], b.progress + dt)
                continue
            if b.kind == "mine" and power_ok[b.team]:
                self.money[b.team] += b.stats["income"] * dt
            if b.kind == "factory" and b.queue and self.unlimited_funds(b.team):
                while b.queue and self._spawn(b, b.queue[0]):
                    b.queue.pop(0)
                    b.production = 0
            elif b.kind == "factory" and b.queue and power_ok[b.team]:
                kind = b.queue[0]
                # Losing the Tech Center blocks starting a new T2 item.
                if b.production > 0 or kind != "tank2" or self.has_tech(b.team):
                    b.production += dt
                    if b.production >= C.FACTIONS[b.team][kind]["time"] and self._spawn(b, kind):
                        b.queue.pop(0)
                        b.production = 0
            if b.kind.startswith("tower") and power_ok[b.team] and b.cooldown <= 0:
                target = self._acquire(b, b.stats["range"])
                if target:
                    weapon = C.FACTIONS[b.team][b.kind]
                    damage.append((target, weapon["damage"]))
                    b.cooldown = weapon["cooldown"]
                    self.shots.append(Shot(b.x, b.y, target.x, target.y, C.FACTIONS[b.team]["color"]))

        for tank in list(self.tanks):
            tank.cooldown = max(0, tank.cooldown - dt)
            if tank.target is not None and (tank.target.hp <= 0 or tank.target.team == tank.team):
                tank.target = None
            moving = False
            explicit = tank.target
            if explicit:
                distance = math.dist((tank.x, tank.y), (explicit.x, explicit.y))
                if distance > tank.stats["range"] * 0.88:
                    moving = self._move_tank(tank, self._attack_goal(tank, explicit), dt)
            elif tank.destination:
                distance_to_destination = math.dist((tank.x, tank.y), tank.destination)
                occupied_destination = (distance_to_destination <= 2 * C.UNIT_RADIUS + 4 and
                                        any(other is not tank and
                                            math.dist((other.x, other.y), tank.destination) < 2 * C.UNIT_RADIUS
                                            for other in self.tanks))
                if distance_to_destination > 4 and not occupied_destination:
                    moving = self._move_tank(tank, tank.destination, dt)
                else:
                    tank.destination = None
                    tank.waypoints.clear()
                    tank.path_goal = None
            target = explicit if explicit and math.dist((tank.x, tank.y), (explicit.x, explicit.y)) <= tank.stats["range"] else None
            if target is None:
                target = self._acquire(tank, tank.stats["range"])
            mirage = tank.team == "A" and tank.kind == "tank2"
            apocalypse = tank.team == "B" and tank.kind == "tank2"
            tank.dust_cooldown = max(0, tank.dust_cooldown - dt)
            if moving and tank.dust_cooldown <= 0:
                dust_emitters.append(tank)
                tank.dust_cooldown = C.TANK_DUST_INTERVAL
            aim = (target or explicit) if apocalypse or mirage else (explicit or target)
            mount_x, mount_y = tank.turret_mount_offset() if apocalypse else (0, 0)
            desired_angle = (self._angle_to(tank.x + mount_x, tank.y + mount_y, aim.x, aim.y)
                             if aim else tank.body_angle)
            if mirage:
                if aim and not moving and tank.destination is None:
                    tank.body_angle = self._turn_toward(
                        tank.body_angle, desired_angle, C.TANK_BODY_TURN_SPEED * dt)
                tank.turret_angle = tank.body_angle
            else:
                turn_speed = C.APOCALYPSE_TURRET_TURN_SPEED if apocalypse else C.TANK_TURRET_TURN_SPEED
                tank.turret_angle = self._turn_toward(
                    tank.turret_angle, desired_angle, turn_speed * dt)
            if tank.destination is not None and not tank.stats["moving_fire"]:
                continue
            if moving and not tank.stats["moving_fire"]:
                continue
            angle_error = abs((desired_angle - tank.turret_angle + 180) % 360 - 180)
            requires_aim = apocalypse or mirage
            tolerance = C.APOCALYPSE_AIM_TOLERANCE if apocalypse else C.MIRAGE_AIM_TOLERANCE
            if target and tank.cooldown <= 0 and (not requires_aim or angle_error <= tolerance):
                damage.append((target, tank.stats["damage"]))
                tank.cooldown = tank.stats["cooldown"]
                for muzzle_x, muzzle_y in tank.muzzle_positions():
                    self.shots.append(Shot(muzzle_x, muzzle_y, target.x, target.y, C.FACTIONS[tank.team]["color"]))

        for building in tuple(self.repairing):
            if building not in self.buildings or building.hp <= 0 or not building.complete:
                self.repairing.discard(building)
                continue
            missing = building.stats["hp"] - building.hp
            if missing <= 0:
                self.repairing.discard(building)
                continue
            affordable = (float("inf") if self.unlimited_funds(building.team)
                          else self.money[building.team] / C.REPAIR_COST_PER_HP)
            restored = min(missing, C.REPAIR_HP_PER_SECOND * dt, affordable)
            if restored > 0:
                building.hp += restored
                if not self.unlimited_funds(building.team):
                    self.money[building.team] -= restored * C.REPAIR_COST_PER_HP

        if damage:
            self.combat_event_serial += 1
        for target, amount in damage:
            target.hp -= amount
        self._separate_tanks()
        for tank in dust_emitters:
            if tank.hp > 0:
                for side in (-1, 1):
                    jitter = self._dust_random.uniform(-C.TANK_DUST_POSITION_JITTER, C.TANK_DUST_POSITION_JITTER)
                    dx, dy = tank._rotate_offset(side * C.TANK_DUST_TRACK_OFFSET + jitter,
                                                 C.TANK_DUST_REAR_OFFSET, tank.body_angle)
                    self.dust_particles.append(DustParticle(
                        tank.x + dx, tank.y + dy,
                        self._dust_random.uniform(*C.TANK_DUST_RADIUS_RANGE),
                        self._dust_random.uniform(*C.TANK_DUST_LIFETIME_RANGE)))
        for obj in (*self.buildings, *self.tanks):
            obj.damage_effect_cooldown = max(0, obj.damage_effect_cooldown - dt)
            if obj.hp > 0 and obj.hp / obj.stats["hp"] <= C.LOW_HEALTH_THRESHOLD:
                if obj.damage_effect_cooldown <= 0:
                    angle = self._damage_random.uniform(0, math.tau)
                    speed = self._damage_random.uniform(*C.DAMAGE_PARTICLE_DRIFT_RANGE)
                    self.damage_particles.append(DamageParticle(
                        obj, math.cos(angle) * speed, math.sin(angle) * speed,
                        self._damage_random.uniform(*C.DAMAGE_PARTICLE_RADIUS_RANGE),
                        self._damage_random.uniform(*C.DAMAGE_PARTICLE_LIFETIME_RANGE)))
                    obj.damage_effect_cooldown = C.DAMAGE_PARTICLE_INTERVAL
            else:
                obj.damage_effect_cooldown = 0
        self.buildings = [b for b in self.buildings if b.hp > 0]
        self.tanks = [t for t in self.tanks if t.hp > 0]
        self.repairing.intersection_update(self.buildings)
        self._resolve_winner()
        self._paths_remaining = None
