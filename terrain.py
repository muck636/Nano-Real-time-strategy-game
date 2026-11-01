"""Static island terrain and obstacle geometry shared by drawing and gameplay."""

import math

import config as C

GROUND = 0
WATER = 1
MOUNTAIN = 2
TILE_SIZE = 32
COLS = math.ceil(C.WORLD_WIDTH / TILE_SIZE)
ROWS = math.ceil(C.WORLD_HEIGHT / TILE_SIZE)


# Classify a world position as ground, water, or mountain.
def _terrain_at(x, y):
    # Two coastal bases meet at a broad pass, with mountains closing its sides.
    center_y = C.WORLD_HEIGHT / 2
    left_x, right_x = 350, C.WORLD_WIDTH - 350
    base_land = any(((x - cx) / 300) ** 2 + ((y - center_y) / 330) ** 2 <= 1
                    for cx in (left_x, right_x))
    middle = C.WORLD_WIDTH / 2
    pass_half_length = middle - 580
    if abs(x - middle) <= pass_half_length:
        road_y = center_y + 55 * math.cos((x - middle) * math.pi / (2 * pass_half_length))
        distance = abs(y - road_y)
        if distance <= 224:
            return GROUND if distance <= 112 else MOUNTAIN
    return GROUND if base_land else WATER


TILES = tuple(tuple(_terrain_at((col + 0.5) * TILE_SIZE, (row + 0.5) * TILE_SIZE)
                    for col in range(COLS)) for row in range(ROWS))


# Check whether any part of a rectangle overlaps blocked terrain.
def rect_blocked(left, top, right, bottom):
    """Check the entire rectangle, with edge-only contact allowed."""
    if left < 0 or top < 0 or right > C.WORLD_WIDTH or bottom > C.WORLD_HEIGHT:
        return True
    epsilon = 1e-7
    first_col = max(0, int(left // TILE_SIZE))
    last_col = min(COLS - 1, int((right - epsilon) // TILE_SIZE))
    first_row = max(0, int(top // TILE_SIZE))
    last_row = min(ROWS - 1, int((bottom - epsilon) // TILE_SIZE))
    for row in range(first_row, last_row + 1):
        for col in range(first_col, last_col + 1):
            if TILES[row][col] != GROUND:
                return True
    return False


# Merge neighboring blocked terrain tiles into larger rectangles.
def _obstacle_rectangles():
    """Merge neighbouring blocked tiles into rectangles for segment checks."""
    active = {}
    merged = []
    for row in range(ROWS + 1):
        runs = []
        if row < ROWS:
            start = None
            for col in range(COLS + 1):
                blocked = col < COLS and TILES[row][col] != GROUND
                if blocked and start is None:
                    start = col
                elif not blocked and start is not None:
                    runs.append((start, col))
                    start = None
        for run, first_row in active.items():
            if run not in runs:
                merged.append((run[0] * TILE_SIZE, first_row * TILE_SIZE,
                               run[1] * TILE_SIZE, row * TILE_SIZE))
        active = {run: active.get(run, row) for run in runs}
    return tuple(merged)


OBSTACLE_RECTS = _obstacle_rectangles()


# Test whether a swept unit footprint crosses blocked terrain.
def segment_blocked(a, b, radius):
    """Check a swept square against impassable tiles without skipping corners."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    min_x, max_x = sorted((a[0], b[0]))
    min_y, max_y = sorted((a[1], b[1]))
    epsilon = 1e-7
    for left, top, right, bottom in OBSTACLE_RECTS:
        left, top = left - radius + epsilon, top - radius + epsilon
        right, bottom = right + radius - epsilon, bottom + radius - epsilon
        if max_x < left or min_x > right or max_y < top or min_y > bottom:
            continue
        enter, leave = 0.0, 1.0
        for low, high, start, delta in ((left, right, a[0], dx), (top, bottom, a[1], dy)):
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
            return True
    return False


# Convert a navigation-grid cell to its world-space center.
def _grid_center(cell):
    return ((cell[0] + 0.5) * C.GRID, (cell[1] + 0.5) * C.GRID)


# Precompute terrain-safe navigation cells and edges.
def _navigation_grid():
    """Prepare terrain-only cell and edge collision once before a match."""
    columns, rows = C.WORLD_WIDTH // C.GRID, C.WORLD_HEIGHT // C.GRID
    free_cells = set()
    for row in range(rows):
        for col in range(columns):
            x, y = _grid_center((col, row))
            radius = C.UNIT_RADIUS
            if not rect_blocked(x - radius, y - radius, x + radius, y + radius):
                free_cells.add((col, row))
    edges = set()
    for col, row in free_cells:
        first = (col, row)
        for dx, dy in ((1, 0), (0, 1), (1, 1), (-1, 1)):
            second = (col + dx, row + dy)
            if second in free_cells and not segment_blocked(_grid_center(first), _grid_center(second), C.UNIT_RADIUS):
                edges.add(tuple(sorted((first, second))))
    return frozenset(free_cells), frozenset(edges)


GRID_OPEN, GRID_EDGES = _navigation_grid()


# Check whether a navigation cell is blocked by terrain.
def grid_cell_blocked(cell):
    return cell not in GRID_OPEN


# Check whether a precomputed edge between cells is blocked.
def grid_segment_blocked(first, second):
    return tuple(sorted((first, second))) not in GRID_EDGES
