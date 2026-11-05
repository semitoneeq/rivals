"""Dependency-free map, geometry, and navigation for Arena Duel."""
from collections import deque
from math import floor, hypot

LEVEL = (
    "####################",
    "#..................#",
    "#..................#",
    "#.....##....##.....#",
    "#.....##....##.....#",
    "#..................#",
    "#..................#",
    "#..................#",
    "#.....##....##.....#",
    "#.....##....##.....#",
    "#..................#",
    "#..................#",
    "####################",
)


def is_wall(level, x, y):
    ix, iy = floor(x), floor(y)
    return iy < 0 or iy >= len(level) or ix < 0 or ix >= len(level[0]) or level[iy][ix] == "#"


def can_stand(level, x, y, radius=0.21):
    # Four corner checks model a compact player/robot collision box.
    return all(not is_wall(level, x + sx * radius, y + sy * radius)
               for sx in (-1, 1) for sy in (-1, 1))


def move_colliding(level, x, y, dx, dy, radius=0.21):
    if can_stand(level, x + dx, y, radius):
        x += dx
    if can_stand(level, x, y + dy, radius):
        y += dy
    return x, y


def line_of_sight(level, x1, y1, x2, y2):
    dist = hypot(x2 - x1, y2 - y1)
    if dist < 1e-8:
        return True
    steps = max(1, int(dist / 0.05))
    for i in range(1, steps):
        t = i / steps
        if is_wall(level, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t):
            return False
    return True


def nav_direction(level, x1, y1, x2, y2):
    """BFS through floor cells; allows the bot to get around pillars."""
    start = (int(x1), int(y1))
    goal = (int(x2), int(y2))
    if start == goal or line_of_sight(level, x1, y1, x2, y2):
        vx, vy = x2 - x1, y2 - y1
        dist = hypot(vx, vy) or 1.0
        return vx / dist, vy / dist
    q = deque([start])
    parents = {start: None}
    while q:
        node = q.popleft()
        if node == goal:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (node[0] + dx, node[1] + dy)
            if neighbor not in parents and not is_wall(level, neighbor[0] + .5, neighbor[1] + .5):
                parents[neighbor] = node
                q.append(neighbor)
    if goal not in parents:
        return 0.0, 0.0
    node = goal
    while parents[node] not in (start, None):
        node = parents[node]
    target_x, target_y = node[0] + .5, node[1] + .5
    vx, vy = target_x - x1, target_y - y1
    dist = hypot(vx, vy) or 1.0
    return vx / dist, vy / dist


def cast_ray(level, pos_x, pos_y, ray_x, ray_y):
    """Grid DDA raycast: perpendicular wall distance, hit orientation, wall texture U."""
    map_x, map_y = int(pos_x), int(pos_y)
    delta_x = abs(1.0 / ray_x) if abs(ray_x) > 1e-10 else 1e30
    delta_y = abs(1.0 / ray_y) if abs(ray_y) > 1e-10 else 1e30
    if ray_x < 0:
        step_x, side_x = -1, (pos_x - map_x) * delta_x
    else:
        step_x, side_x = 1, (map_x + 1 - pos_x) * delta_x
    if ray_y < 0:
        step_y, side_y = -1, (pos_y - map_y) * delta_y
    else:
        step_y, side_y = 1, (map_y + 1 - pos_y) * delta_y
    side = 0
    for _ in range(70):
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
        else:
            side_y += delta_y
            map_y += step_y
            side = 1
        if is_wall(level, map_x + .5, map_y + .5):
            break
    if side == 0:
        distance = side_x - delta_x
        texture_x = pos_y + distance * ray_y
    else:
        distance = side_y - delta_y
        texture_x = pos_x + distance * ray_x
    return max(0.01, distance), side, texture_x % 1.0
