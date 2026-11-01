"""Pygame drawing and mouse interaction for the game."""

from collections import OrderedDict
import math
from pathlib import Path

import pygame

import config as C
import terrain
from entities import Building, Tank


class UI:
    _terrain_cache = None
    _menu_cache = None

    # Initialize interface state, fonts, cached backgrounds, and unit sprites.
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 19)
        self.small = pygame.font.SysFont("arial", 15)
        self.large = pygame.font.SysFont("arial", 42, bold=True)
        self.title = pygame.font.SysFont("arial", 27, bold=True)
        self.selected = []
        self.build_kind = None
        self.console_open = False
        self.console_text = ""
        self.drag_start = None
        self.buttons = []
        self.rotated_sprites = OrderedDict()
        self.minimap_rect = pygame.Rect(C.MAP_WIDTH + 18, 83, 264, 194)
        self.camera_x = 0
        self.camera_y = 0
        icon = pygame.image.load(str(Path(__file__).parent / "assets" / "power_icon.png")).convert()
        icon.set_colorkey((255, 255, 255))
        self.power_icon = icon
        assets = Path(__file__).parent / "assets"
        if UI._menu_cache is None:
            UI._menu_cache = self.make_menu_background(assets)
        self.menu_background = UI._menu_cache
        model_assets = assets / "models"
        icon_files = {("A", "tank1"): "guardian.png", ("A", "tank2"): "mirage.png",
                      ("B", "tank1"): "hammer.png", ("B", "tank2"): "apocalypse.png"}
        self.unit_icons = {}
        self.disabled_unit_icons = {}
        for key, filename in icon_files.items():
            original = pygame.image.load(str(assets / "unit_icons" / filename)).convert_alpha()
            for size in (48, 64, 96):
                self.unit_icons[(*key, size)] = pygame.transform.smoothscale(original, (size, size))
            disabled = self.unit_icons[(*key, 48)].copy()
            disabled.set_alpha(140)
            self.disabled_unit_icons[key] = disabled
        if UI._terrain_cache is None:
            UI._terrain_cache = self.make_terrain_surfaces(assets)
        self.terrain_surface, self.minimap_terrain = UI._terrain_cache
        hull = pygame.image.load(str(model_assets / "guardian_hull.png")).convert_alpha()
        turret = pygame.image.load(str(model_assets / "guardian_turret.png")).convert_alpha()
        # Both source canvases are 32x32, so scaling them equally preserves the pivot.
        self.guardian_body = pygame.transform.scale(hull, C.GUARDIAN_SPRITE_SIZE)
        self.guardian_turret = pygame.transform.scale(turret, C.GUARDIAN_SPRITE_SIZE)
        mirage = pygame.image.load(str(model_assets / "mirage.png")).convert_alpha()
        self.mirage_body = pygame.transform.scale(mirage, C.MIRAGE_SPRITE_SIZE)
        hammer_body = pygame.image.load(str(model_assets / "hammer_hull.png")).convert_alpha()
        hammer_turret = pygame.image.load(str(model_assets / "hammer_turret.png")).convert_alpha()
        self.hammer_body = pygame.transform.scale(hammer_body, C.HAMMER_SPRITE_SIZE)
        turret_art = pygame.transform.scale(hammer_turret, C.HAMMER_SPRITE_SIZE)
        width, height = C.HAMMER_SPRITE_SIZE
        source_w, source_h = C.HAMMER_SOURCE_SIZE
        pivot_x = round(C.HAMMER_TURRET_PIVOT[0] * width / source_w)
        pivot_y = round(C.HAMMER_TURRET_PIVOT[1] * height / source_h)
        side = 2 * max(pivot_x, width - pivot_x, pivot_y, height - pivot_y)
        self.hammer_turret = pygame.Surface((side, side), pygame.SRCALPHA)
        self.hammer_turret.blit(turret_art, (side // 2 - pivot_x, side // 2 - pivot_y))
        apocalypse_body = pygame.image.load(str(model_assets / "apocalypse_hull.png")).convert_alpha()
        apocalypse_turret = pygame.image.load(str(model_assets / "apocalypse_turret.png")).convert_alpha()
        self.apocalypse_body = pygame.transform.scale(apocalypse_body, C.APOCALYPSE_SPRITE_SIZE)
        turret_art = pygame.transform.scale(apocalypse_turret, C.APOCALYPSE_SPRITE_SIZE)
        width, height = C.APOCALYPSE_SPRITE_SIZE
        source_w, source_h = C.APOCALYPSE_SOURCE_SIZE
        pivot_x = round(C.APOCALYPSE_TURRET_PIVOT[0] * width / source_w)
        pivot_y = round(C.APOCALYPSE_TURRET_PIVOT[1] * height / source_h)
        side = 2 * max(pivot_x, width - pivot_x, pivot_y, height - pivot_y)
        self.apocalypse_turret = pygame.Surface((side, side), pygame.SRCALPHA)
        self.apocalypse_turret.blit(turret_art, (side // 2 - pivot_x, side // 2 - pivot_y))

    # Scale and center the menu artwork, extending its edges for widescreen.
    @staticmethod
    def make_menu_background(assets):
        original = pygame.image.load(str(assets / "menu_background_centered.png")).convert()
        scale = min(C.WIDTH / original.get_width(), C.HEIGHT / original.get_height())
        size = (round(original.get_width() * scale), round(original.get_height() * scale))
        image = pygame.transform.smoothscale(original, size)
        x = (C.WIDTH - size[0]) // 2
        y = (C.HEIGHT - size[1]) // 2
        background = pygame.Surface((C.WIDTH, C.HEIGHT)).convert()
        background.fill((0, 0, 0))
        # Extend the dark edges into a widescreen window without stretching the artwork.
        left_width, right_width = x, C.WIDTH - x - size[0]
        if left_width:
            edge = image.subsurface((0, 0, 1, size[1]))
            background.blit(pygame.transform.scale(edge, (left_width, size[1])), (0, y))
        if right_width:
            edge = image.subsurface((size[0] - 1, 0, 1, size[1]))
            background.blit(pygame.transform.scale(edge, (right_width, size[1])), (x + size[0], y))
        shade = pygame.Surface((C.WIDTH, C.HEIGHT), pygame.SRCALPHA)
        for i in range(left_width):
            alpha = round(255 * (1 - (i + 1) / left_width))
            pygame.draw.line(shade, (0, 0, 0, alpha), (i, y), (i, y + size[1] - 1))
        for i in range(right_width):
            alpha = round(255 * (1 - (i + 1) / right_width))
            column = C.WIDTH - 1 - i
            pygame.draw.line(shade, (0, 0, 0, alpha), (column, y), (column, y + size[1] - 1))
        background.blit(shade, (0, 0))
        background.blit(image, (x, y))
        return background

    # Build the world terrain image and matching minimap background.
    @staticmethod
    def make_terrain_surfaces(assets):
        tile_dir = assets / "terrain"
        size = (terrain.TILE_SIZE, terrain.TILE_SIZE)
        land_tiles = [pygame.transform.scale(
            pygame.image.load(str(tile_dir / f"terr_{index}.png")).convert(), size)
            for index in range(1, 5)]
        water = pygame.transform.scale(pygame.image.load(str(tile_dir / "water_1.png")).convert(), size)
        mountain = pygame.transform.scale(pygame.image.load(str(tile_dir / "mount_1.png")).convert(), size)
        world = pygame.Surface((C.WORLD_WIDTH, C.WORLD_HEIGHT)).convert()
        minimap_size = pygame.Rect(C.MAP_WIDTH + 18, 83, 264, 194).inflate(-8, -8).size
        overview = pygame.Surface(minimap_size).convert()
        x_edges = [round(min(col * terrain.TILE_SIZE, C.WORLD_WIDTH) * minimap_size[0] / C.WORLD_WIDTH)
                   for col in range(terrain.COLS + 1)]
        y_edges = [round(min(row * terrain.TILE_SIZE, C.WORLD_HEIGHT) * minimap_size[1] / C.WORLD_HEIGHT)
                   for row in range(terrain.ROWS + 1)]
        overview_colors = {terrain.GROUND: (224, 181, 138),
                           terrain.WATER: (78, 100, 192),
                           terrain.MOUNTAIN: (126, 80, 42)}
        for row, tiles in enumerate(terrain.TILES):
            for col, kind in enumerate(tiles):
                if kind == terrain.GROUND:
                    value = (col * 73856093) ^ (row * 19349663)
                    value ^= value >> 13
                    value *= 0x5BD1E995
                    value ^= value >> 15
                    tile = land_tiles[value % len(land_tiles)]
                else:
                    tile = water if kind == terrain.WATER else mountain
                world.blit(tile, (col * terrain.TILE_SIZE, row * terrain.TILE_SIZE))
                pygame.draw.rect(overview, overview_colors[kind],
                                 (x_edges[col], y_edges[row],
                                  x_edges[col + 1] - x_edges[col], y_edges[row + 1] - y_edges[row]))
        return world, overview

    # Center the camera on a world position while respecting map bounds.
    def center_on(self, x, y):
        self.camera_x = max(0, min(C.WORLD_WIDTH - C.MAP_WIDTH, x - C.MAP_WIDTH / 2))
        self.camera_y = max(0, min(C.WORLD_HEIGHT - C.HEIGHT, y - C.HEIGHT / 2))

    # Move the camera by a relative offset.
    def pan(self, dx, dy):
        self.center_on(self.camera_x + C.MAP_WIDTH / 2 + dx,
                       self.camera_y + C.HEIGHT / 2 + dy)

    # Convert world coordinates into camera-relative screen coordinates.
    def to_screen(self, x, y):
        return round(x - self.camera_x), round(y - self.camera_y)

    # Convert screen coordinates into world coordinates.
    def to_world(self, x, y):
        return x + self.camera_x, y + self.camera_y

    # Render and draw a text value with the selected font and color.
    def text(self, screen, value, x, y, color=None, font=None):
        image = (font or self.font).render(str(value), True, color or C.COLORS["text"])
        screen.blit(image, (x, y))

    # Return a cached sprite rotated to the nearest degree.
    def rotated(self, name, sprite, angle):
        key = (name, round(angle) % 360)
        cached = self.rotated_sprites.get(key)
        if cached is None:
            cached = pygame.transform.rotate(sprite, key[1])
            self.rotated_sprites[key] = cached
            if len(self.rotated_sprites) > C.ROTATION_CACHE_SIZE:
                self.rotated_sprites.popitem(last=False)
        else:
            self.rotated_sprites.move_to_end(key)
        return cached

    # Draw a button and register its action and enabled state.
    def button(self, screen, rect, label, enabled=True, active=False, action=None):
        color = (51, 88, 104) if active else ((58, 72, 83) if enabled else (42, 49, 56))
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (112, 150, 163) if enabled else (65, 75, 81), rect, 1, border_radius=5)
        self.text(screen, label, rect.x + 10, rect.y + 8, C.COLORS["text"] if enabled else C.COLORS["muted"], self.small)
        if action:
            self.buttons.append((rect, action, enabled))

    # Draw and register a unit-production button with its portrait and cost.
    def unit_training_button(self, screen, rect, team, kind, game, enabled):
        self.button(screen, rect, "", enabled, False, ("train", kind))
        icon = (self.unit_icons[team, kind, 48] if enabled else self.disabled_unit_icons[team, kind])
        screen.blit(icon, (rect.x + 4, rect.y + 4))
        color = C.COLORS["text"] if enabled else C.COLORS["muted"]
        self.text(screen, C.FACTIONS[team][kind]["name"], rect.x + 56, rect.y + 7, color, self.small)
        self.text(screen, f"${game.cost(team, kind)}", rect.x + 56, rect.y + 29, color, self.small)

    # Display portraits and counts for selected tank types.
    def draw_selected_unit_icons(self, screen, selected, panel_x):
        counts = {}
        for unit in selected:
            if isinstance(unit, Tank):
                key = (unit.team, unit.kind)
                if (*key, 48) in self.unit_icons:
                    counts[key] = counts.get(key, 0) + 1
        if len(counts) == 1:
            key = next(iter(counts))
            screen.blit(self.unit_icons[(*key, 96)], (panel_x + 168, 552))
        elif len(counts) == 2:
            for index, (key, count) in enumerate(counts.items()):
                x = panel_x + 136 + index * 68
                screen.blit(self.unit_icons[(*key, 64)], (x, 554))
                label = self.small.render(f"x{count}", True, C.COLORS["text"])
                screen.blit(label, label.get_rect(center=(x + 32, 628)))
        else:
            for index, key in enumerate(counts):
                if index >= 4:
                    break
                screen.blit(self.unit_icons[(*key, 48)],
                            (panel_x + 168 + index % 2 * 48, 552 + index // 2 * 48))

    # Interpolate between two angles along the shortest rotation.
    @staticmethod
    def interpolate_angle(previous, current, alpha):
        difference = (current - previous + 180) % 360 - 180
        return (previous + difference * alpha) % 360

    # Draw active movement or attack routes and return their destination markers.
    def draw_order_lines(self, screen, game, alpha):
        markers = set()
        for tank in game.tanks:
            if tank.hp <= 0:
                continue
            x = tank.previous_x + (tank.x - tank.previous_x) * alpha
            y = tank.previous_y + (tank.y - tank.previous_y) * alpha
            points = [(x, y)]
            target = tank.target
            if target is not None and target.hp > 0 and target.team != tank.team:
                color = C.COLORS["bad"]
                if isinstance(target, Tank):
                    goal = (target.previous_x + (target.x - target.previous_x) * alpha,
                            target.previous_y + (target.y - target.previous_y) * alpha)
                else:
                    goal = (target.x, target.y)
                if math.dist((tank.x, tank.y), (target.x, target.y)) > tank.stats["range"] * 0.88:
                    points.extend(tank.waypoints)
                points.append(goal)
            elif tank.destination is not None:
                color = C.COLORS["good"]
                goal = tank.destination
                points.extend(tank.waypoints)
                if not tank.waypoints and tank.path_goal is None:
                    points.append(goal)
            else:
                continue
            screen_points = [self.to_screen(px, py) for px, py in points]
            if len(screen_points) > 1:
                pygame.draw.lines(screen, color, False, screen_points, 2)
            markers.add((self.to_screen(*goal), color))
        return markers

    # Render terrain, objects, effects, orders, and placement previews.
    def draw_map(self, screen, game, alpha=1.0):
        screen.blit(self.terrain_surface, (0, 0),
                    (round(self.camera_x), round(self.camera_y), C.MAP_WIDTH, C.HEIGHT))
        pygame.draw.rect(screen, C.COLORS["outline"], (0, 0, C.MAP_WIDTH, C.HEIGHT), 4)
        for index, (x, y) in enumerate(C.VEINS):
            sx, sy = self.to_screen(x, y)
            if not (-35 <= sx <= C.MAP_WIDTH + 35 and -35 <= sy <= C.HEIGHT + 35):
                continue
            occupied = any(b.vein == index for b in game.buildings)
            pygame.draw.circle(screen, (118, 105, 70), (sx, sy), 30)
            for dx, dy in ((-13, -5), (5, -13), (12, 9), (-4, 13)):
                pygame.draw.circle(screen, C.COLORS["ore"] if not occupied else (134, 117, 78), (sx + dx, sy + dy), 8)
        for particle in game.dust_particles:
            sx, sy = self.to_screen(particle.x, particle.y)
            radius = round(particle.radius * (1 - particle.age / particle.lifetime))
            if radius > 0 and -radius <= sx <= C.MAP_WIDTH + radius and -radius <= sy <= C.HEIGHT + radius:
                pygame.draw.circle(screen, C.COLORS["dust"], (sx, sy), radius)
        order_markers = self.draw_order_lines(screen, game, alpha)
        for b in game.buildings:
            sx, sy = self.to_screen(b.x, b.y)
            if not (-85 <= sx <= C.MAP_WIDTH + 85 and -85 <= sy <= C.HEIGHT + 85):
                continue
            size = b.stats["size"]
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (round(sx), round(sy))
            team_color = C.FACTIONS[b.team]["color"]
            sprite = pygame.Surface((size, size), pygame.SRCALPHA)
            fill = tuple(int(v * 0.75) for v in team_color)
            local = sprite.get_rect()
            pygame.draw.rect(sprite, fill, local, border_radius=7)
            pygame.draw.rect(sprite, team_color, local, 3, border_radius=7)
            if b.kind.startswith("tower"):
                pygame.draw.circle(sprite, team_color, local.center, 10)
            elif b.kind == "factory":
                pygame.draw.rect(sprite, team_color, local.inflate(-23, -23), 2)
            elif b.kind == "power":
                icon = pygame.transform.smoothscale(self.power_icon, (size - 12, size - 12))
                icon.set_colorkey((255, 255, 255))
                sprite.blit(icon, ((size - icon.get_width()) // 2, (size - icon.get_height()) // 2))
            elif b.kind == "mine":
                pygame.draw.circle(sprite, C.COLORS["ore"], local.center, 11)
            elif b.kind == "tech":
                pygame.draw.circle(sprite, (220, 220, 250), local.center, 12, 2)
            else:
                pygame.draw.circle(sprite, (230, 235, 240), local.center, 14, 2)
            opacity = 255 if b.complete else round(25.5 + 229.5 * b.progress / b.stats["time"])
            sprite.set_alpha(opacity)
            screen.blit(sprite, rect)
            if not b.complete:
                self.progress(screen, rect.left, rect.bottom + 4, rect.width, b.progress / b.stats["time"], C.COLORS["ore"])
            self.health(screen, sx, rect.top - 9, rect.width, b.hp / b.stats["hp"])
            if b in self.selected:
                self.diamond(screen, sx, sy, size + 12)
        for tank in game.tanks:
            render_x = tank.previous_x + (tank.x - tank.previous_x) * alpha
            render_y = tank.previous_y + (tank.y - tank.previous_y) * alpha
            body_angle = self.interpolate_angle(tank.previous_body_angle, tank.body_angle, alpha)
            turret_angle = self.interpolate_angle(tank.previous_turret_angle, tank.turret_angle, alpha)
            visual_body_angle = round(body_angle) % 360
            visual_turret_angle = round(turret_angle) % 360
            sx, sy = self.to_screen(render_x, render_y)
            if not (-50 <= sx <= C.MAP_WIDTH + 50 and -50 <= sy <= C.HEIGHT + 50):
                continue
            color = C.FACTIONS[tank.team]["color"]
            guardian = tank.team == "A" and tank.kind == "tank1"
            mirage = tank.team == "A" and tank.kind == "tank2"
            hammer = tank.team == "B" and tank.kind == "tank1"
            apocalypse = tank.team == "B" and tank.kind == "tank2"
            modeled = guardian or mirage or hammer or apocalypse
            if guardian:
                body = self.rotated("guardian_body", self.guardian_body, visual_body_angle)
                turret = self.rotated("guardian_turret", self.guardian_turret, visual_turret_angle)
                screen.blit(body, body.get_rect(center=(sx, sy)))
                screen.blit(turret, turret.get_rect(center=(sx, sy)))
            elif mirage:
                body = self.rotated("mirage_body", self.mirage_body, visual_body_angle + C.MIRAGE_ART_ROTATION)
                screen.blit(body, body.get_rect(center=(sx, sy)))
            elif hammer or apocalypse:
                rotation = C.HAMMER_ART_ROTATION if hammer else C.APOCALYPSE_ART_ROTATION
                body_art = self.hammer_body if hammer else self.apocalypse_body
                turret_art = self.hammer_turret if hammer else self.apocalypse_turret
                name = "hammer" if hammer else "apocalypse"
                body = self.rotated(name + "_body", body_art, visual_body_angle + rotation)
                turret = self.rotated(name + "_turret", turret_art, visual_turret_angle + rotation)
                mount_x, mount_y = tank.turret_mount_offset(visual_body_angle)
                screen.blit(body, body.get_rect(center=(sx, sy)))
                screen.blit(turret, turret.get_rect(center=(round(sx + mount_x), round(sy + mount_y))))
            else:
                pygame.draw.circle(screen, C.COLORS["outline"], (sx, sy), 14)
                pygame.draw.circle(screen, color, (sx, sy), 11)
                if tank.kind == "tank2":
                    pygame.draw.circle(screen, (240, 235, 219), (sx, sy), 5)
            if tank in self.selected:
                self.diamond(screen, sx, sy, 44 if modeled else 25)
            self.health(screen, sx, sy - (48 if modeled else 22),
                        38 if modeled else 30, tank.hp / tank.stats["hp"])
        for particle in game.damage_particles:
            owner = particle.owner
            if isinstance(owner, Tank):
                x = owner.previous_x + (owner.x - owner.previous_x) * alpha
                y = owner.previous_y + (owner.y - owner.previous_y) * alpha
            else:
                x, y = owner.x, owner.y
            sx, sy = self.to_screen(x + particle.velocity_x * particle.age,
                                    y + particle.velocity_y * particle.age)
            radius = round(particle.radius * (1 - particle.age / particle.lifetime))
            if radius > 0 and -radius <= sx <= C.MAP_WIDTH + radius and -radius <= sy <= C.HEIGHT + radius:
                pygame.draw.circle(screen, C.COLORS["damage_particle"], (sx, sy), radius)
        for position, color in order_markers:
            pygame.draw.circle(screen, color, position, 10, 2)
        for shot in game.shots:
            pygame.draw.line(screen, shot.color, self.to_screen(shot.x, shot.y),
                             self.to_screen(shot.end_x, shot.end_y), 3)
        if self.drag_start and pygame.mouse.get_pressed()[0]:
            mouse = pygame.mouse.get_pos()
            box = pygame.Rect(min(self.drag_start[0], mouse[0]), min(self.drag_start[1], mouse[1]),
                              abs(mouse[0] - self.drag_start[0]), abs(mouse[1] - self.drag_start[1]))
            pygame.draw.rect(screen, (218, 230, 173), box, 1)
        if self.build_kind:
            mx, my = pygame.mouse.get_pos()
            if mx < C.MAP_WIDTH:
                wx, wy = self.to_world(mx, my)
                if self.build_kind == "mine":
                    nearest = min(C.VEINS, key=lambda v: math.dist(v, (wx, wy)))
                    if math.dist(nearest, (wx, wy)) <= 34:
                        wx, wy = nearest
                        mx, my = self.to_screen(wx, wy)
                reason = game.can_place(game.player, self.build_kind, wx, wy)
                color = C.COLORS["good"] if reason is None else C.COLORS["bad"]
                size = C.BUILDINGS[self.build_kind]["size"]
                preview = pygame.Surface((size, size), pygame.SRCALPHA)
                preview.fill((*color, 105))
                screen.blit(preview, (mx - size/2, my - size/2))
                pygame.draw.rect(screen, color, (mx - size/2, my - size/2, size, size), 2)
                if reason:
                    self.text(screen, reason, max(8, min(mx + 18, C.MAP_WIDTH - 220)), min(my + 20, C.HEIGHT - 22), color, self.small)

    # Draw the diamond outline around a selected object.
    def diamond(self, screen, x, y, radius):
        points = [(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)]
        pygame.draw.polygon(screen, (247, 235, 138), points, 2)

    # Draw a horizontal progress bar for a fractional value.
    def progress(self, screen, x, y, width, fraction, color):
        pygame.draw.rect(screen, (25, 32, 38), (x, y, width, 5))
        pygame.draw.rect(screen, color, (x, y, max(0, width * min(1, fraction)), 5))

    # Draw a health bar with a color based on the remaining health.
    def health(self, screen, x, y, width, fraction):
        self.progress(screen, x - width/2, y, width, fraction,
                      C.COLORS["good"] if fraction > C.LOW_HEALTH_THRESHOLD else C.COLORS["bad"])

    # Draw the terrain overview, object markers, and camera viewport.
    def draw_minimap(self, screen, game):
        outer = self.minimap_rect
        inner = outer.inflate(-8, -8)
        pygame.draw.rect(screen, C.COLORS["outline"], outer, border_radius=4)
        screen.blit(self.minimap_terrain, inner.topleft)

        # Convert a world position into a point on the minimap.
        def point(x, y):
            return (round(inner.left + x * inner.width / C.WORLD_WIDTH),
                    round(inner.top + y * inner.height / C.WORLD_HEIGHT))

        for x, y in C.VEINS:
            pygame.draw.circle(screen, C.COLORS["ore"], point(x, y), 3)
        for building in game.buildings:
            color = C.FACTIONS[building.team]["color"]
            marker = pygame.Rect(0, 0, 6 if building.kind == "hq" else 4,
                                 6 if building.kind == "hq" else 4)
            marker.center = point(building.x, building.y)
            pygame.draw.rect(screen, color, marker)
        for tank in game.tanks:
            pygame.draw.circle(screen, C.FACTIONS[tank.team]["color"], point(tank.x, tank.y), 2)

        viewport = pygame.Rect(
            round(inner.left + self.camera_x * inner.width / C.WORLD_WIDTH),
            round(inner.top + self.camera_y * inner.height / C.WORLD_HEIGHT),
            round(C.MAP_WIDTH * inner.width / C.WORLD_WIDTH),
            round(C.HEIGHT * inner.height / C.WORLD_HEIGHT),
        )
        pygame.draw.rect(screen, (250, 238, 145), viewport, 2)
        pygame.draw.rect(screen, (112, 150, 163), outer, 1, border_radius=4)

    # Draw the side panel, minimap, building controls, and selection details.
    def draw_panel(self, screen, game):
        self.buttons.clear()
        self.selected = [o for o in self.selected if o in game.buildings or o in game.tanks]
        building = next((o for o in self.selected if isinstance(o, Building)), None)
        pygame.draw.rect(screen, C.COLORS["panel"], (C.MAP_WIDTH, 0, C.WIDTH - C.MAP_WIDTH, C.HEIGHT))
        px = C.MAP_WIDTH + 18
        credits = "INF" if game.god_mode else str(int(game.money[game.player]))
        self.text(screen, f"Faction {game.player}   Credits {credits}", px, 16)
        supply, demand = game.power(game.player)
        power_color = C.COLORS["good"] if supply >= demand else C.COLORS["bad"]
        self.text(screen, f"Power {supply} / {demand}", px, 44, power_color)
        if game.god_mode:
            self.text(screen, "GOD MODE", px + 164, 44, C.COLORS["ore"], self.small)
        if supply < demand:
            self.text(screen, "BLACKOUT: build a Power Plant", px, 65, C.COLORS["bad"], self.small)
        self.draw_minimap(screen, game)
        repair_enabled = bool(building and building.complete and
                              (building.hp < building.stats["hp"] or building in game.repairing))
        repair_label = "Stop Repair" if building in game.repairing else "Repair"
        sell_enabled = bool(building and building.kind != "hq")
        refund = 0 if not sell_enabled else int(game.cost(game.player, building.kind) *
                                               C.SELL_REFUND_RATIO * building.hp / building.stats["hp"])
        self.button(screen, pygame.Rect(px, 286, 128, 31), repair_label, repair_enabled,
                    bool(building and building in game.repairing), ("repair", None))
        self.button(screen, pygame.Rect(px + 136, 286, 128, 31), f"Sell +${refund}", sell_enabled,
                    False, ("sell", None))
        self.text(screen, "BUILD", px, 321, font=self.font)
        kinds = ("mine", "power", "factory", "tech", "tower1", "tower2")
        for index, kind in enumerate(kinds):
            name = C.FACTIONS[game.player].get(kind, C.BUILDINGS[kind])["name"]
            label = f"{name}  ${game.cost(game.player, kind)}"
            enabled = (game.god_mode or game.money[game.player] >= game.cost(game.player, kind)) and (kind != "tower2" or game.has_tech(game.player))
            self.button(screen, pygame.Rect(px, 345 + index*31, 264, 27), label, enabled,
                        self.build_kind == kind, ("build", kind))
        self.text(screen, "SELECTION", px, 530)
        if self.selected:
            obj = self.selected[0]
            label = obj.name + (f" +{len(self.selected)-1}" if len(self.selected) > 1 else "")
            self.text(screen, label, px, 554, font=self.small)
            self.text(screen, f"HP {max(0, int(obj.hp))}/{int(obj.stats['hp'])}", px, 574, font=self.small)
            if isinstance(obj, Tank):
                self.draw_selected_unit_icons(screen, self.selected, px)
            if isinstance(obj, Building):
                if not obj.complete:
                    self.text(screen, f"Building {int(obj.progress / obj.stats['time'] * 100)}%", px, 592, font=self.small)
                elif obj.kind == "factory":
                    if obj.queue:
                        active = obj.queue[0]
                        total = C.FACTIONS[obj.team][active]["time"]
                        self.text(screen, f"Queue {len(obj.queue)}: {int(obj.production / total * 100)}%", px, 592, font=self.small)
                    if obj.team == game.player:
                        for index, kind in enumerate(("tank1", "tank2")):
                            enabled = (game.god_mode or game.money[obj.team] >= game.cost(obj.team, kind)) and (kind != "tank2" or game.has_tech(obj.team))
                            rect = pygame.Rect(px + 136 * index, 610, 128, 56)
                            self.unit_training_button(screen, rect, obj.team, kind, game, enabled)
        if game.message_time > 0:
            self.text(screen, game.message[:35], px, 676, C.COLORS["ore"], self.small)
        self.text(screen, "Enter: console  |  WASD: pan", px, 699, C.COLORS["muted"], self.small)

    # Draw the command console and its input hint.
    def draw_console(self, screen):
        bar = pygame.Surface((C.WIDTH, 76), pygame.SRCALPHA)
        bar.fill((9, 15, 22, 235))
        screen.blit(bar, (0, C.HEIGHT - 76))
        self.text(screen, "CONSOLE  > " + self.console_text + "_", 20, C.HEIGHT - 64,
                  C.COLORS["text"])
        self.text(screen, "Enter to run  |  Esc to close  |  god / god off", 20,
                  C.HEIGHT - 32, C.COLORS["muted"], self.small)

    # Edit console input or run a god-mode command.
    def handle_console_key(self, event, game):
        if event.key == pygame.K_ESCAPE:
            self.console_open = False
            self.console_text = ""
        elif event.key == pygame.K_BACKSPACE:
            self.console_text = self.console_text[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            command = self.console_text.strip().lower()
            self.console_open = False
            self.console_text = ""
            if command in ("god", "god on"):
                game.set_god_mode(True)
            elif command == "god off":
                game.set_god_mode(False)
            elif command:
                game.notify("Unknown command: " + command[:20])
        elif event.unicode and event.unicode.isprintable() and len(self.console_text) < 48:
            self.console_text += event.unicode

    # Draw the game view, side panel, and any result or console overlays.
    def draw(self, screen, game, alpha=1.0):
        self.draw_map(screen, game, alpha)
        self.draw_panel(screen, game)
        if game.winner is not None:
            overlay = pygame.Surface((C.WIDTH, C.HEIGHT), pygame.SRCALPHA)
            overlay.fill((9, 15, 22, 195))
            screen.blit(overlay, (0, 0))
            verdict = "DRAW" if game.winner == "draw" else ("VICTORY" if game.winner == game.player else "DEFEAT")
            image = self.large.render(verdict, True, C.COLORS["text"])
            screen.blit(image, image.get_rect(center=(C.WIDTH/2, C.HEIGHT/2 - 30)))
            image = self.font.render("Press R for a new game, or Esc to quit", True, C.COLORS["text"])
            screen.blit(image, image.get_rect(center=(C.WIDTH/2, C.HEIGHT/2 + 28)))
        if self.console_open:
            self.draw_console(screen)

    # Handle movement, attacks, minimap, building, and panel clicks.
    def handle_mouse_down(self, event, game):
        pos = event.pos
        if event.button == 3:
            if self.build_kind:
                self.build_kind = None
                return
            if pos[0] < C.MAP_WIDTH:
                tanks = [o for o in self.selected if isinstance(o, Tank) and o.team == game.player]
                if tanks:
                    world_pos = self.to_world(*pos)
                    target = game.object_at(*world_pos)
                    if target and target.team != game.player:
                        game.issue_attack(tanks, target)
                    else:
                        game.issue_move(tanks, world_pos)
            return
        if event.button != 1 or game.winner is not None:
            return
        if self.minimap_rect.collidepoint(pos):
            inner = self.minimap_rect.inflate(-8, -8)
            world_x = max(0, min(C.WORLD_WIDTH, (pos[0] - inner.left) * C.WORLD_WIDTH / inner.width))
            world_y = max(0, min(C.WORLD_HEIGHT, (pos[1] - inner.top) * C.WORLD_HEIGHT / inner.height))
            self.center_on(world_x, world_y)
            return
        if pos[0] >= C.MAP_WIDTH:
            for rect, action, enabled in self.buttons:
                if rect.collidepoint(pos):
                    mode, kind = action
                    if mode == "repair":
                        building = next((o for o in self.selected if isinstance(o, Building)), None)
                        reason = game.toggle_repair(game.player, building)
                        if reason:
                            game.notify(reason)
                    elif mode == "sell":
                        building = next((o for o in self.selected if isinstance(o, Building)), None)
                        reason = game.sell(game.player, building)
                        if reason:
                            game.notify(reason)
                        else:
                            self.selected = []
                    elif mode == "build":
                        self.build_kind = kind
                        if kind == "tower2" and not game.has_tech(game.player):
                            game.notify("Tech Center required")
                        elif not game.god_mode and game.money[game.player] < game.cost(game.player, kind):
                            game.notify("Insufficient funds")
                    else:
                        factory = next((o for o in self.selected if isinstance(o, Building) and o.kind == "factory"), None)
                        reason = game.train(game.player, factory, kind)
                        if reason:
                            game.notify(reason)
                    break
        elif self.build_kind:
            reason = game.place(game.player, self.build_kind, *self.to_world(*pos))
            if reason:
                game.notify(reason)
            else:
                self.build_kind = None
        else:
            self.drag_start = pos

    # Finish click or drag selection of player objects.
    def handle_mouse_up(self, event, game):
        if event.button != 1 or not self.drag_start or game.winner is not None:
            return
        start = self.drag_start
        self.drag_start = None
        end = event.pos
        if math.dist(start, end) < 7:
            obj = game.object_at(*self.to_world(*end))
            self.selected = [obj] if obj is not None and obj.team == game.player else []
        else:
            box = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                              abs(start[0] - end[0]), abs(start[1] - end[1]))
            self.selected = [t for t in game.tanks if t.team == game.player and box.collidepoint(*self.to_screen(t.x, t.y))]


# Identify which faction button contains a title-screen click.
def start_choice_at(pos):
    for team, bounds in C.START_BUTTONS.items():
        if pygame.Rect(bounds).collidepoint(pos):
            return team
    return None


# Draw the title background, caption, and faction selection buttons.
def draw_start(screen, ui):
    screen.blit(ui.menu_background, (0, 0))
    caption = ui.font.render("choose your fraction", True, (240, 220, 195))
    caption_rect = caption.get_rect(center=(C.WIDTH // 2, 472))
    shadow = ui.font.render("choose your fraction", True, (15, 5, 5))
    screen.blit(shadow, caption_rect.move(1, 2))
    screen.blit(caption, caption_rect)
    labels = {"A": "A  Guardian / Mirage", "B": "B  Hammer / Apocalypse"}
    mouse = pygame.mouse.get_pos()
    for team, bounds in C.START_BUTTONS.items():
        rect = pygame.Rect(bounds)
        hover = rect.collidepoint(mouse)
        fill = (62, 22, 20) if hover else (31, 12, 14)
        border = (242, 179, 92) if hover else (169, 98, 55)
        pygame.draw.rect(screen, fill, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)
        pygame.draw.line(screen, (106, 41, 33), (rect.left + 8, rect.top + 5), (rect.right - 9, rect.top + 5), 1)
        label = ui.font.render(labels[team], True, (250, 232, 211))
        screen.blit(label, label.get_rect(center=rect.center))
