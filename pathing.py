"""Small grid A* for tank movement around terrain and buildings."""

import heapq
import math
from functools import lru_cache

import config as C
import terrain


# Check whether a tank-sized area overlaps a living building.
def _building_blocked(x, y, buildings, extra=0):
    return any(abs(x - b.x) < b.radius + C.UNIT_RADIUS + extra and
               abs(y - b.y) < b.radius + C.UNIT_RADIUS + extra for b in buildings if b.hp > 0)


# Check whether a tank-sized area intersects terrain or buildings.
def blocked(x, y, buildings, extra=0):
    radius = C.UNIT_RADIUS + extra
    return (terrain.rect_blocked(x - radius, y - radius, x + radius, y + radius)
            or _building_blocked(x, y, buildings, extra))


# Check whether a tank can travel a straight segment without a collision.
def clear_segment(a, b, buildings):
    if blocked(*a, buildings) or blocked(*b, buildings):
        return False
    if terrain.segment_blocked(a, b, C.UNIT_RADIUS):
        return False
    dx, dy = b[0] - a[0], b[1] - a[1]
    for building in buildings:
        if building.hp <= 0:
            continue
        radius = building.radius + C.UNIT_RADIUS
        # Shrink by an epsilon: touching an obstacle edge is allowed by blocked().
        bounds = ((building.x - radius + 1e-6, building.x + radius - 1e-6, a[0], dx),
                  (building.y - radius + 1e-6, building.y + radius - 1e-6, a[1], dy))
        enter, leave = 0.0, 1.0
        for low, high, start, delta in bounds:
            if abs(delta) < 1e-12:
                if start < low or start > high:
                    break
            else:
                first, last = (low - start) / delta, (high - start) / delta
                enter = max(enter, min(first, last))
                leave = min(leave, max(first, last))
                if enter > leave:
                    break
        else:
            return False
    return True


# Find a nearby grid position with enough clearance for a tank.
def nearest_open(goal, buildings):
    """Snap an obstructed order to a nearby position with room for a tank."""
    if not blocked(*goal, buildings):
        return goal
    step = C.GRID
    cols, rows = C.WORLD_WIDTH // step, C.WORLD_HEIGHT // step
    cx = max(0, min(cols - 1, int(goal[0] // step)))
    cy = max(0, min(rows - 1, int(goal[1] // step)))
    best = None
    best_distance = float("inf")
    for ring in range(max(cols, rows)):
        if ring == 0:
            cells = [(cx, cy)]
        else:
            cells = [(cx + dx, cy - ring) for dx in range(-ring, ring + 1)]
            cells += [(cx + dx, cy + ring) for dx in range(-ring, ring + 1)]
            cells += [(cx - ring, cy + dy) for dy in range(-ring + 1, ring)]
            cells += [(cx + ring, cy + dy) for dy in range(-ring + 1, ring)]
        for x, y in cells:
            if not (0 <= x < cols and 0 <= y < rows):
                continue
            point = ((x + 0.5) * step, (y + 0.5) * step)
            distance = math.dist(point, goal)
            if distance < best_distance and not blocked(*point, buildings):
                best, best_distance = point, distance
        if best is not None:
            next_edges = []
            for x in (cx - ring - 1, cx + ring + 1):
                if 0 <= x < cols:
                    next_edges.append(abs((x + 0.5) * step - goal[0]))
            for y in (cy - ring - 1, cy + ring + 1):
                if 0 <= y < rows:
                    next_edges.append(abs((y + 0.5) * step - goal[1]))
            if not next_edges or min(next_edges) >= best_distance:
                return best
    return best


# Plan a route using direct paths, corridor shortcuts, or grid A*.
def route(start, goal, buildings):
    """Find a reachable cell nearest goal, with a direct final segment when possible."""
    step = C.GRID
    cols = C.WORLD_WIDTH // step
    rows = C.WORLD_HEIGHT // step

    # Map a world position to a navigation-grid cell within the map.
    def cell(p):
        return (max(0, min(cols - 1, int(p[0] // step))),
                max(0, min(rows - 1, int(p[1] // step))))

    # Convert a navigation-grid cell to its world-space center.
    def center(c):
        return ((c[0] + 0.5) * step, (c[1] + 0.5) * step)

    # Cache whether a navigation cell is blocked by terrain or buildings.
    @lru_cache(maxsize=None)
    def cell_blocked(c):
        return terrain.grid_cell_blocked(c) or _building_blocked(*center(c), buildings)

    origin = cell(start)
    goal = nearest_open(goal, buildings)
    if goal is None:
        return []
    if clear_segment(start, goal, buildings):
        return [goal]
    # Try a few fully checked corridor routes before searching a long map-wide grid.
    dx = goal[0] - start[0]
    if abs(dx) >= C.WORLD_WIDTH / 2:
        direction = 1 if dx > 0 else -1
        approach = min(140, abs(dx) / 4)
        for offset in (40, 0, 70, -40):
            lane_y = C.WORLD_HEIGHT / 2 + offset
            first = (start[0] + direction * approach, lane_y)
            second = (goal[0] - direction * approach, lane_y)
            if (clear_segment(start, first, buildings)
                    and clear_segment(first, second, buildings)
                    and clear_segment(second, goal, buildings)):
                if clear_segment(start, second, buildings):
                    return [second, goal]
                if clear_segment(first, goal, buildings):
                    return [first, goal]
                return [first, second, goal]
    frontier = [(0, origin)]
    distance = {origin: 0}
    previous = {}
    seen = set()
    best = origin
    best_h = math.dist(center(origin), goal)
    while frontier:
        _, here = heapq.heappop(frontier)
        if here in seen:
            continue
        seen.add(here)
        h = math.dist(center(here), goal)
        if h < best_h:
            best, best_h = here, h
        if (here != origin and math.dist(center(here), goal) <= step * 1.5
                and clear_segment(center(here), goal, buildings)):
            best = here
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nxt = (here[0] + dx, here[1] + dy)
            if not (0 <= nxt[0] < cols and 0 <= nxt[1] < rows):
                continue
            if cell_blocked(nxt):
                continue
            if here == origin and not clear_segment(start, center(nxt), buildings):
                continue
            if here != origin and terrain.grid_segment_blocked(here, nxt):
                continue
            if dx and dy and (cell_blocked((here[0] + dx, here[1])) or
                              cell_blocked((here[0], here[1] + dy))):
                continue
            cost = distance[here] + (1.414 if dx and dy else 1)
            if cost < distance.get(nxt, float("inf")):
                distance[nxt] = cost
                previous[nxt] = here
                heapq.heappush(frontier, (cost + math.dist(center(nxt), goal) / step, nxt))
    if best == origin:
        return []
    result = []
    while best != origin:
        result.append(center(best))
        best = previous[best]
    result.reverse()
    if clear_segment(result[-1], goal, buildings):
        result.append(goal)
    # Skip intermediate grid centers whenever the tank can move straight to a later point.
    smoothed = []
    anchor = start
    while result:
        index = len(result) - 1
        while index > 0 and not clear_segment(anchor, result[index], buildings):
            index -= 1
        if not clear_segment(anchor, result[index], buildings):
            return []
        anchor = result[index]
        smoothed.append(anchor)
        result = result[index + 1:]
    return smoothed
