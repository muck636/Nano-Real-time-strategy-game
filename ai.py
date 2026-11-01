"""Economy, tech and attack priorities for the opposing side."""

import math

import config as C


class SimpleAI:
    # Initialize the AI team, action timer, and unit-production state.
    def __init__(self, team):
        self.team = team
        self.timer = 0
        self.first_tank_ordered = False

    # Mirror candidate building positions for the opposing side.
    def _positions(self, positions):
        if self.team == "A":
            return positions
        return [(C.WORLD_WIDTH - x, y) for x, y in positions]

    # Try candidate locations and place the first valid building.
    def _build(self, game, kind, positions):
        for x, y in self._positions(positions):
            if game.can_place(self.team, kind, x, y) is None:
                game.place(self.team, kind, x, y)
                return True
        return False

    # Periodically build structures, train units, and issue attack orders.
    def update(self, game, dt):
        self.timer -= dt
        if self.timer > 0 or game.winner is not None:
            return
        self.timer = 1.0
        team = self.team
        mine_count = len(game.team_buildings(team, "mine"))
        factory_count = len(game.team_buildings(team, "factory"))
        tech_count = len(game.team_buildings(team, "tech"))
        tower_count = len(game.team_buildings(team, "tower1"))
        t2_tower_count = len(game.team_buildings(team, "tower2"))

        if mine_count == 0:
            self._build(game, "mine", [C.BASE_VEINS[0]])
        elif factory_count == 0:
            self._build(game, "factory", [(435, 690), (390, 930), (530, 750)])
        elif tech_count == 0:
            self._build(game, "tech", [(305, 560), (340, 960), (190, 780)])
        elif tower_count < 2:
            sites = [(535, 700), (500, 610)] if tower_count == 0 else [(620, 720), (590, 790)]
            self._build(game, "tower1", sites)
        elif mine_count < 3:
            self._build(game, "mine", list(C.BASE_VEINS[1:]))
        elif t2_tower_count == 0:
            self._build(game, "tower2", [(700, 720), (650, 650), (650, 790)])

        supply, demand = game.power(team)
        if supply - demand < 20 and game.money[team] >= C.BUILDINGS["power"]["cost"]:
            self._build(game, "power", [(300, 940), (200, 780), (420, 950), (500, 860)])

        factories = game.team_buildings(team, "factory", True)
        if factories:
            factory = min(factories, key=lambda f: len(f.queue))
            if len(factory.queue) < 2:
                active_army = [t for t in game.tanks if t.team == team]
                first_tank = not self.first_tank_ordered
                development_done = bool(tech_count and tower_count and mine_count >= 2 and t2_tower_count)
                if first_tank or development_done:
                    t2_count = sum(t.kind == "tank2" for t in active_army)
                    kind = "tank2" if game.has_tech(team) and t2_count < max(1, len(active_army) // 3) else "tank1"
                    if game.money[team] >= game.cost(team, kind):
                        if game.train(team, factory, kind) is None:
                            self.first_tank_ordered = True

        targets = game.team_buildings(game.player)
        if targets:
            for tank in [t for t in game.tanks if t.team == team]:
                if tank.target not in game.buildings and tank.target not in game.tanks:
                    target = min(targets, key=lambda b: math.dist((b.x, b.y), (tank.x, tank.y)))
                    game.issue_attack([tank], target)
