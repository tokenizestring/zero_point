import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import buildings as bd
import town_kit as tk
import town_props as tp
from buildkit import V, block, emit, rod, lump, local_block, frame_block

tau = math.pi * 2.0
up = V(0.0, 0.0, 1.0)
hx = 8.0
hy = 5.0
wall_t = 0.45
ix = hx - wall_t
fy = -hy + wall_t
by = hy - wall_t
ceiling = 4.0
stone = "granite_rubble"
dressed = "granite_ashlar"
trim = "painted_wood_white"
door_paint = "painted_wood_bauxite"
door = (-0.6, 0.6, 0.0, 2.5)
front_windows = [(-6.6, -5.4), (-4.4, -3.2), (3.2, 4.4), (5.4, 6.6)]
hall_windows = [(-1.55, -1.05, 1.4, 2.8), (1.05, 1.55, 1.4, 2.8)]
staff_window = (-1.6, -0.8, 1.0, 2.8)
back_door = (-0.35, 0.55, 0.0, 2.2)
end_lights = [(-1.6, -0.62), (-0.5, 0.5), (0.62, 1.6)]
vent = (-0.3, 0.3, 6.2, 6.8)
west_wall = (-2.0, -1.88)
east_wall = (1.88, 2.0)
hall_wall = (-1.2, -1.08)
staff_wall = (1.2, 1.32)
side_doors = [(-3.4, -2.4), (2.4, 3.4)]
middle_door = (-0.45, 0.45)


def gable_of():
    return kit.Gable(-hx, hx, hy, 0.35, 4.6, 38.0)


def window_z(w):
    return (w[0], w[1], 1.0, 3.4)


def back_windows():
    return [(-a1, -a0, 1.0, 3.4) for a0, a1 in front_windows]


def end_windows():
    return [(a0, a1, 1.0, 3.4) for a0, a1 in end_lights]


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    front_open = [door] + [window_z(w) for w in front_windows] + hall_windows
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [kit.rect(door[0], door[1], -0.05, door[3])] + [kit.rect(*o) for o in front_open[1:]], wall_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, -1.5, wall_top, wall_t, front_open)
    back_open = [back_door] + back_windows() + [staff_window]
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [kit.rect(back_door[0], back_door[1], -0.05, back_door[3])] + [kit.rect(*o) for o in back_open[1:]], wall_t)
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, -1.5, wall_top, wall_t, back_open)
    outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
    for frame, tag in ((left, "left"), (right, "right")):
        kit.wall(shell, stone, frame, outline, [kit.rect(*w) for w in end_windows()] + [kit.rect(*vent)], wall_t)
        kit.wall_boxes(b, "rock", tag, frame, -hy, hy, -1.5, wall_top, wall_t, end_windows())
        tk.opening_block(b, "wood", "vent", frame, vent, wall_t)
    bd.gable_cols(b, "gable", -hx, -ix, gable, wall_top, 0.0)
    bd.gable_cols(b, "gable", ix, hx, gable, wall_top, 0.0)
    for side, reach, gaps in (("front", hx, [(door[0] - 0.3, door[1] + 0.3)]), ("back", hx, [(back_door[0] - 0.05, back_door[1] + 0.05)]), ("left", hy, []), ("right", hy, [])):
        frame = kit.facade(side, hx, hy)
        edges = [-reach]
        for g0, g1 in gaps:
            edges += [g0, g1]
        edges.append(reach)
        for s0, s1 in zip(edges[0::2], edges[1::2]):
            count = max(1, int(round((s1 - s0) / 0.7)))
            for index in range(count):
                a = s0 + (s1 - s0) * index / count
                c = s0 + (s1 - s0) * (index + 1) / count
                frame_block(shell, dressed, frame, a + 0.006, c - 0.006, -0.5, 0.45 + rng.uniform(-0.02, 0.02), -0.05, 0.0)
        bd.damp_band(shell, frame, -reach, reach, rng, 0.5, 1.0, "granite_rubble_damp", -0.2, 0.003, gaps)
    for corner, ua, ub in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0))):
        tk.quoins_light(shell, dressed, corner, ua, ub, 0.45, wall_top - 0.05, rng, 0.045)
    for x_center in (-hx + wall_t * 0.5, hx - wall_t * 0.5):
        kit.gable_coping(shell, dressed, gable, x_center, wall_t + 0.04, rng, 0.12, 0.05, 0.02)
    return wall_top


def doorcase(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    front = kit.facade("front", ix, hy)
    a0, a1, z0, z1 = door
    for edge, sign in ((a0, -1.0), (a1, 1.0)):
        lo, hi = sorted((edge, edge + sign * 0.28))
        frame_block(shell, dressed, front, lo, hi, 0.45, z1, -0.08, 0.0, 0.008)
    outline = tk.lancet(a0 - 0.28, a1 + 0.28, z1, z1 + 0.05, z1 + 0.65, 4)
    kit.wall(shell, dressed, front, outline, [], 0.08, 0.08)
    tk.atlas_panel(shell, "town_signs", kit.frame_point(front, 0.0, 3.62, 0.021), V(0.0, -1.0, 0.0), 1.2, 0.48, tp.sg("school_plaque"), 0.0, 0.0)
    frame_block(shell, dressed, front, -0.68, 0.68, 3.34, 3.9, -0.02, 0.0)
    tk.door_unit(joinery, front, a0, a1, 0.0, 2.2, wall_t, door_paint, rng, "low", 76.0, "ledged", True, 0.0, 0.07, 2.0, trim)
    frame_block(joinery, trim, front, a0, a1, 2.2, z1, 0.06, 0.2, 0.0, "board")
    block(shell, dressed, V(a0 - 0.3, -hy - 0.45, -0.45), V(a1 + 0.3, -hy + 0.02, -0.05), 0.015)
    tk.col(b, "rock", "step", a0 - 0.3, a1 + 0.3, -hy - 0.45, -hy, -1.5, -0.05)
    tk.col(b, "rock", "threshold", a0, a1, -hy, fy, -1.5, 0.0)
    block(shell, dressed, V(a0, -hy, -0.08), V(a1, fy + 0.04, 0.0), 0.004)
    tk.opening_block(b, "wood", "transom", front, (a0, a1, 2.2, z1), wall_t)


def bell_cote(parts, gable, rng):
    shell = parts["shell"]
    x = -hx + wall_t * 0.5
    z0 = gable.under(0.45, 0.0) + 0.05
    for y in (-0.42, 0.42):
        block(shell, dressed, V(x - 0.2, y - 0.12, z0 - 0.4), V(x + 0.2, y + 0.12, z0 + 0.95), 0.012)
    cap = kit.Matrix.Translation(V(x, 0.0, z0 + 0.95)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Z')
    kit.prism(shell, dressed, cap, [(-0.64, 0.0), (0.64, 0.0), (0.0, 0.42)], -0.27, 0.27)
    kit.member(shell, "timber_beam", V(x, -0.32, z0 + 0.85), V(x, 0.32, z0 + 0.85), 0.1, 0.1, up, 0.0, "box")
    bell = kit.Matrix.Translation(V(x, 0.0, z0 + 0.38)) @ kit.Matrix.Rotation(rng.uniform(-0.25, 0.25), 4, 'X')
    emit(shell, kit.geo_lathe([(0.0, 0.0), (0.2, 0.0), (0.19, 0.04), (0.13, 0.14), (0.11, 0.3), (0.07, 0.38), (0.0, 0.4)], 12), "town_brass", bell, "given", True)
    rod(shell, "rusty_metal", bell @ V(0.0, 0.0, 0.4), V(x, 0.0, z0 + 0.8), 0.012, 4)
    rod(shell, "rusty_metal", bell @ V(0.0, 0.0, 0.05), bell @ V(0.0, 0.0, -0.08), 0.02, 5)


def windows(b, parts, rng):
    joinery = parts["joinery"]
    shell = parts["shell"]
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    states = [(0.0, 0.3, 0.3, False), (0.3, 0.2, 0.4, False), (0.0, 0.25, 0.3, True), (0.0, 0.35, 0.3, False)]
    for w, (lift, whole, shard, boarded) in zip(front_windows, states):
        tk.sash(b, parts, front, window_z(w), wall_t, rng, trim, 0.12, lift, whole, shard, 2, 2, None, dressed, None, False, boarded, "glass", "window", dressed, trim)
    for w in hall_windows:
        tk.sash(b, parts, front, w, wall_t, rng, trim, 0.12, 0.0, 0.3, 0.3, 1, 2, None, dressed, None, False, False, "glass", "window", dressed, trim)
    for index, w in enumerate(back_windows()):
        tk.sash(b, parts, back, w, wall_t, rng, trim, 0.12, 0.2 if index == 1 else 0.0, 0.25, 0.35, 2, 2, None, dressed, None, False, index == 3, "glass", "window", dressed, trim)
    tk.sash(b, parts, back, staff_window, wall_t, rng, trim, 0.12, 0.0, 0.3, 0.3, 1, 2, None, dressed, None, False, False, "glass", "window", dressed, trim)
    for frame in (left, right):
        for index, w in enumerate(end_windows()):
            tk.sash(b, parts, frame, w, wall_t, rng, trim, 0.12, 0.0, 0.3, 0.35, 1, 2, None, dressed, None, False, False, "glass", "window", None, trim)
        frame_block(shell, dressed, frame, end_lights[0][0] - 0.2, end_lights[-1][1] + 0.2, 3.4, 3.7, -0.03, wall_t, 0.01)
        for a0, a1, z0, z1 in [vent]:
            for index in range(4):
                center = kit.frame_point(frame, 0.0, z0 + 0.09 + index * 0.13, -wall_t * 0.5)
                slope = (frame[3] * 0.6 - up).normalized()
                emit(joinery, kit.geo_box(a1 - a0 + 0.02, 0.2, 0.02), "timber_planks_weathered", kit.place(center, frame[1], slope.cross(frame[1]).normalized()), "board")
            frame_block(shell, dressed, frame, a0 - 0.12, a1 + 0.12, z1, z1 + 0.18, -0.03, wall_t)
            frame_block(shell, dressed, frame, a0 - 0.1, a1 + 0.1, z0 - 0.1, z0, -0.05, wall_t)
    a0, a1, z0, z1 = back_door
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, door_paint, rng, "high", 95.0, "ledged", True, 0.0, 0.06, 2.0, trim)
    frame_block(shell, dressed, back, a0 - 0.15, a1 + 0.15, z1, z1 + 0.25, -0.02, wall_t)
    block(shell, dressed, V(-a1 - 0.12, hy - 0.04, -0.4), V(-a0 + 0.12, hy + 0.38, -0.06), 0.012)
    tk.col(b, "rock", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
    tk.col(b, "rock", "step", -a1 - 0.12, -a0 + 0.12, hy, hy + 0.38, -0.6, -0.06)


def floors(b, parts, rng):
    floor = parts["floors"]
    tk.tile_floor(floor, "floorboards", -ix, west_wall[0], fy, by, 0.0, 0.05)
    tk.tile_floor(floor, "floorboards", east_wall[1], ix, fy, by, 0.0, 0.05)
    tk.tile_floor(floor, "town_quarry", west_wall[0], east_wall[1], fy, hall_wall[1], 0.0, 0.05)
    tk.tile_floor(floor, "floorboards", west_wall[0], east_wall[1], hall_wall[1], by, 0.0, 0.05)
    tk.col(b, "wood", "ground", -ix, ix, fy, by, -0.3, 0.0)
    for s in (-1.0, 1.0):
        x0, x1 = sorted((s * 2.0, s * 3.3))
        block(floor, "floorboards", V(x0, -1.5, 0.0), V(x1, 2.5, 0.18), 0.0, "world")
        frame_block(floor, "timber_beam", kit.plane(V(s * 3.3, 0.0, 0.0), V(s, 0.0, 0.0)), -1.5 if s > 0 else -2.5, 2.5 if s > 0 else 1.5, 0.0, 0.18, -0.01, 0.0)
        tk.col(b, "wood", "dais", x0, x1, -1.5, 2.5, 0.0, 0.18)


def walls(b, parts, rng):
    joinery = parts["joinery"]
    z1 = ceiling
    for s, wall in ((-1.0, west_wall), (1.0, east_wall)):
        normal = V(-1.0, 0.0, 0.0) if s < 0 else V(1.0, 0.0, 0.0)
        origin_x = wall[0] if s < 0 else wall[1]
        frame = kit.plane(V(origin_x, 0.0, 0.0), normal)
        doors = []
        for d0, d1 in side_doors:
            a0, a1 = sorted((kit.along_of(frame, V(0.0, d0, 0.0)), kit.along_of(frame, V(0.0, d1, 0.0))))
            doors.append((a0, a1, 0.0, 2.2))
        a_lo, a_hi = sorted((kit.along_of(frame, V(0.0, fy, 0.0)), kit.along_of(frame, V(0.0, by, 0.0))))
        tk.partition(b, parts, V(origin_x, 0.0, 0.0), normal, a_lo, a_hi, 0.0, z1, wall[1] - wall[0], doors, "partition", "rock")
        for index, d in enumerate(doors):
            tk.door_unit(joinery, frame, d[0], d[1], 0.0, 2.2, wall[1] - wall[0], door_paint, rng, "low" if index == 0 else "high", -rng.uniform(70.0, 100.0), "panel", rng.random() < 0.75, 0.0, 0.06, rng.uniform(0.0, 2.0), trim)
    for wall in (hall_wall, staff_wall):
        frame = kit.plane(V(0.0, wall[0], 0.0), V(0.0, -1.0, 0.0))
        doors = [(middle_door[0], middle_door[1], 0.0, 2.1)]
        tk.partition(b, parts, V(0.0, wall[0], 0.0), V(0.0, -1.0, 0.0), west_wall[1], east_wall[0], 0.0, z1, wall[1] - wall[0], doors, "partition", "rock")
        tk.door_unit(joinery, frame, middle_door[0], middle_door[1], 0.0, 2.1, wall[1] - wall[0], door_paint, rng, "high", 85.0, "panel", True, 0.0, 0.06)


def finishes(parts, rng):
    dado = ("panel", 1.2, "painted_wood_green", ("plaster", 1))
    tiles = ("tiles", 1.3, "kitchen_tiles", ("plaster", 1))
    paper = ("paper", "town_stripe", 1, 1)
    for s in (-1.0, 1.0):
        x0, x1 = sorted((s * ix, s * 2.0))
        outer, inner = ("left", "right") if s < 0 else ("right", "left")
        windows_front = [(min(s * a0, s * a1), max(s * a0, s * a1), 1.0, 3.4) for a0, a1 in ((3.2, 4.4), (5.4, 6.6))]
        openings = {"front": windows_front, "back": windows_front, outer: end_windows(), inner: [(d0, d1, 0.0, 2.2) for d0, d1 in side_doors]}
        if s < 0:
            openings[outer] = [(-w[1], -w[0], w[2], w[3]) for w in end_windows()]
        tk.room(parts, rng, x0, x1, fy, by, 0.0, ceiling, {"front": dado, "back": dado, outer: dado, inner: dado}, openings, None, None, True, 1, (), None, 4, 0.0)
    tk.room(parts, rng, west_wall[1], east_wall[0], fy, hall_wall[0], 0.0, ceiling, {"front": tiles, "back": tiles, "left": tiles, "right": tiles}, {"front": [door] + hall_windows, "back": [(middle_door[0], middle_door[1], 0.0, 2.1)], "left": [(d0, d1, 0.0, 2.2) for d0, d1 in side_doors[:1]], "right": [(d0, d1, 0.0, 2.2) for d0, d1 in side_doors[:1]]}, None, None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, west_wall[1], east_wall[0], hall_wall[1], staff_wall[0], 0.0, ceiling, {"front": paper, "back": paper, "left": paper, "right": paper}, {"front": [(middle_door[0], middle_door[1], 0.0, 2.1)], "back": [(middle_door[0], middle_door[1], 0.0, 2.1)]}, trim, None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, west_wall[1], east_wall[0], staff_wall[1], by, 0.0, ceiling, {"front": paper, "back": paper, "left": paper, "right": paper}, {"front": [(middle_door[0], middle_door[1], 0.0, 2.1)], "back": [(-back_door[1], -back_door[0], 0.0, 2.2), (-staff_window[1], -staff_window[0], 1.0, 2.8)], "left": [(d0, d1, 0.0, 2.2) for d0, d1 in side_doors[1:]], "right": [(d0, d1, 0.0, 2.2) for d0, d1 in side_doors[1:]]}, trim, None, True, 1, (), None, 2, 0.0)


def classroom(b, parts, rng, s):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    P = lambda x, y, z=0.0: V(s * x, y, z)
    tp.blackboard(interior, P(2.02, 0.5, 1.95), V(s, 0.0, 0.0), 2.4, 1.2, rng)
    tp.desk_light(b, furniture, clutter, P(2.85, 0.5, 0.18), -s * math.pi * 0.5, rng, 1.2, 0.65, 0.76, "timber_beam", "floorboards", ("papers",))
    tp.chair_light(furniture, P(2.35, 0.5, 0.18), s * math.pi * 0.5, rng)
    for row, x in enumerate((4.2, 5.4, 6.6)):
        for column, y in enumerate((-2.0, 0.5, 3.0)):
            fallen = rng.random() < 0.12
            jitter = rng.uniform(-0.12, 0.12) if rng.random() < 0.5 else 0.0
            if rng.random() < 0.06:
                continue
            base = tp.school_desk(b, furniture, P(x + rng.uniform(-0.05, 0.05), y + jitter), -s * math.pi * 0.5 + rng.uniform(-0.08, 0.08) + (rng.uniform(-0.6, 0.6) if fallen else 0.0), rng, fallen)
            if rng.random() < 0.3:
                tp.papers(parts["debris"], s * x - 0.4, s * x + 0.4, y - 0.4, y + 0.4, 0.0, 1, rng, ("notice", "letter"))
    tp.stove_light(b, furniture, P(7.0, -3.7), rng, P(ix, -3.7, 3.0))
    tp.framed(interior, P(ix - 0.02, 3.0, 2.1), V(-s, 0.0, 0.0), 1.6, 0.8, tp.pr("map"), rng, "timber_beam", 0.02)
    tp.framed(interior, P(2.6, fy + 0.02, 2.2), V(0.0, 1.0, 0.0), 0.7, 0.45, tp.pr("harbour"), rng, "timber_beam", -0.03)
    bd.cabinet(furniture, P(7.0, by - 0.26), 0.9, 0.46, 0.0, 0.9, 0.0, rng, "timber_planks_weathered", "painted_wood_green", 2, 0, 0 if rng.random() < 0.5 else None)
    tk.col(b, "wood", "cupboard", min(s * 6.55, s * 7.45), max(s * 6.55, s * 7.45), by - 0.49, by, 0.0, 0.9)
    if s < 0:
        b.loot("box", P(2.55, -0.95, 0.18))
    else:
        b.loot("food", P(7.0, by - 0.26, 0.9))
    for x in (3.8, 6.0):
        tk.pendant(b, interior, P(x, 0.5, ceiling), rng, "ceramic", 0.6, "warm", 8)
    tp.papers(parts["debris"], min(s * 2.4, s * 7.2), max(s * 2.4, s * 7.2), -4.2, 4.2, 0.0, 8, rng, ("notice", "letter", "card", "newspaper"))
    tp.debris_field(parts, min(s * 2.4, s * 7.2), max(s * 2.4, s * 7.2), -4.2, 4.2, 0.0, rng, 6, 4, 0, 6)


def hall(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    for s in (-1.0, 1.0):
        x = s * (east_wall[0] - 0.01)
        inward = V(-s, 0.0, 0.0)
        for y0, y1 in ((-4.4, -3.5), (-2.3, -1.4)):
            bd.coat_rail(interior, clutter, V(x, y0, 1.55), V(x, y1, 1.55), inward, rng, rng.randint(0, 2))
        tp.bench_light(b, furniture, V(s * 1.6, -1.85, 0.0), math.pi * 0.5, rng, 0.8)
    tp.notice_board(interior, V(1.15, hall_wall[0] - 0.02, 1.6), V(0.0, -1.0, 0.0), 0.8, 0.6, rng, ("notice", "letter", "card", "calendar"))
    tk.pendant(b, interior, V(0.0, -2.9, ceiling), rng, "ceramic", 0.5, "warm", 8)
    tp.papers(parts["debris"], -1.6, 1.6, -4.3, -1.5, 0.0, 5, rng, ("notice", "letter", "card"))
    tp.debris_field(parts, -1.6, 1.6, -4.3, -1.5, 0.0, rng, 4, 2, 0, 4)


def office(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.desk_light(b, furniture, clutter, V(-1.05, 0.05, 0.0), math.pi * 0.5, rng, 1.1, 0.62, 0.76, "timber_beam", "floorboards", ("papers", "files", "lamp"))
    tp.chair_light(furniture, V(-0.35, 0.0, 0.0), -math.pi * 0.5 + 0.3, rng)
    tp.filing_cabinet(b, furniture, V(1.5, 0.75, 0.0), -math.pi * 0.5, rng, 4, "green")
    tp.safe_light(b, furniture, V(1.5, -0.6, 0.0), -math.pi * 0.5, rng, 1.0, (0.5, 0.46, 0.66))
    tp.aid_cabinet(interior, clutter, V(-0.9, staff_wall[0] - 0.02, 1.55), V(0.0, -1.0, 0.0), rng)
    b.loot("medical", V(-1.3, 0.85, 0.0))
    tp.wall_clock(interior, V(1.0, hall_wall[1] + 0.02, 2.5), V(0.0, 1.0, 0.0), rng, 0.15)
    tp.bulb(b, interior, V(0.0, 0.05, ceiling), rng, 0.6, "warm")
    tp.papers(parts["debris"], -1.6, 1.6, -0.9, 1.0, 0.0, 6, rng, ("letter", "envelope", "notice", "card"))


def staff(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.table_light(furniture, 0.0, 2.75, 0.0, 1.2, 0.75, 0.75, rng)
    tk.col(b, "wood", "table", -0.6, 0.6, 2.38, 3.12, 0.0, 0.75)
    b.loot("food", V(0.25, 2.75, 0.75))
    for position, yaw, fallen in ((V(-0.85, 2.75, 0.0), math.pi * 0.5, False), (V(0.85, 2.6, 0.0), -math.pi * 0.5, False), (V(0.1, 3.5, 0.0), 0.0, True)):
        tp.chair_light(furniture, position, yaw, rng, "timber_beam", "timber_planks_weathered", fallen)
    tp.armchair_light(b, furniture, V(1.25, 4.0, 0.0), 3.6, rng, "leather_brown")
    tp.stove_light(b, furniture, V(-1.45, 4.05, 0.0), rng, V(-1.45, by, 2.4))
    bd.kettle(clutter, V(-1.45, 4.05, 0.86), rng)
    bd.cabinet(furniture, V(-1.6, 1.85, 0.0), 0.8, 0.44, 0.0, 0.9, math.pi * 0.5, rng, "timber_planks_weathered", "painted_wood_green", 2, 0)
    tk.col(b, "wood", "cupboard", -1.88, -1.4, 1.45, 2.25, 0.0, 0.9)
    b.loot("box", V(1.35, 1.75, 0.0))
    tp.bulb(b, interior, V(0.0, 2.9, ceiling), rng, 0.6, "warm")
    tp.debris_field(parts, -1.6, 1.6, 1.6, 4.3, 0.0, rng, 3, 0, 2, 2)


def exterior(b, parts, gable, rng):
    roof = parts["roof"]
    plants = parts["plants"]
    tk.terrace_roof(b, parts, -hx, hx, gable, rng, 0.35, 0.012, [(-5.2, -4.2, 2.4, 3.4, 1.0)], 0.03, True, "rock", True, 2.0, False, (-1.0, 1.0), 0.36, 0.76, 0.52)
    tk.stack(b, roof, 0.0, 0.0, 0.7, 0.9, gable.top(0.45) - 0.3, gable.ridge_top + 1.0, rng, 2, dressed)
    gutter_z = gable.eave_top - 0.11
    tk.downpipe_light(roof, -hx + 0.35, -gable.edge - 0.04, -hy, gutter_z - 0.03, -0.15, rng)
    tk.downpipe_light(roof, hx - 0.35, gable.edge + 0.04, hy, gutter_z - 0.03, -0.15, rng, broken=1.4, lean=0.05)
    bell_cote(parts, gable, rng)
    tk.ivy_light(plants, V(-hx - 0.02, -3.0, -0.15), V(-1.0, 0.0, 0.0), rng, 3.6, 1.0, 3, 8.0)
    tk.ivy_light(plants, V(5.0, hy + 0.02, -0.15), V(0.0, 1.0, 0.0), rng, 3.0, 0.8, 3, 8.0)
    tk.weeds_line(plants, V(-hx + 0.3, -hy - 0.12, -0.15), V(door[0] - 0.5, -hy - 0.12, -0.15), rng, 5)
    tk.weeds_line(plants, V(door[1] + 0.5, -hy - 0.12, -0.15), V(hx - 0.3, -hy - 0.12, -0.15), rng, 5)
    tk.weeds_line(plants, V(-hx + 0.3, hy + 0.12, -0.15), V(hx - 0.3, hy + 0.12, -0.15), rng, 6)
    tk.weeds_line(plants, V(-hx - 0.12, -hy + 0.3, -0.15), V(-hx - 0.12, hy - 0.3, -0.15), rng, 4)
    tk.weeds_line(plants, V(hx + 0.12, -hy + 0.3, -0.15), V(hx + 0.12, hy - 0.3, -0.15), rng, 4)
    for k in range(6):
        kit.grass_tuft(plants, V(rng.uniform(-hx, hx), rng.choice((-1.0, 1.0)) * (gable.edge + 0.06), gutter_z + 0.02), rng, (0.06, 0.2), (3, 5), 0.03)
    for k in range(5):
        lump(plants, "roof_moss", V(rng.uniform(-hx + 1.0, hx - 1.0), rng.uniform(-0.05, 0.05), gable.ridge_top + 0.09), (rng.uniform(0.06, 0.14), 0.08, 0.03), rng, 0.3, 1)


def school():
    b = kit.Build("school", 2001)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    shell_walls(b, parts, gable, rng)
    doorcase(b, parts, rng)
    windows(b, parts, rng)
    floors(b, parts, rng)
    walls(b, parts, rng)
    finishes(parts, rng)
    for s in (-1.0, 1.0):
        classroom(b, parts, rng, s)
    hall(b, parts, rng)
    office(b, parts, rng)
    staff(b, parts, rng)
    exterior(b, parts, gable, rng)
    return b


def school_far():
    b = kit.Build("school_far", 2002)
    shell = b.part("shell", 30.0)
    gable = gable_of()
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [], wall_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [], wall_t)
    outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
    for side in ("left", "right"):
        frame = kit.facade(side, hx, hy)
        kit.wall(shell, stone, frame, outline, [], wall_t)
        for w in end_windows():
            kit.skin(shell, "glass_dirty", frame, kit.rect(*w), [], 0.004, 0.02, False)
    for o in [door] + [window_z(w) for w in front_windows] + hall_windows:
        kit.skin(shell, "glass_dirty" if o[2] > 0.3 else "soot", front, kit.rect(*o), [], 0.004, 0.02, False)
    for o in [back_door] + back_windows() + [staff_window]:
        kit.skin(shell, "glass_dirty" if o[2] > 0.3 else "soot", back, kit.rect(*o), [], 0.004, 0.02, False)
    kit.roof_slab(shell, gable, -1.0, -hx, hx, "slate_roof", 0.2)
    kit.roof_slab(shell, gable, 1.0, -hx, hx, "slate_roof", 0.2)
    block(shell, "terracotta", V(-hx, -0.13, gable.ridge_top - 0.04), V(hx, 0.13, gable.ridge_top + 0.09))
    block(shell, dressed, V(-0.35, -0.45, gable.top(0.45) - 0.3), V(0.35, 0.45, gable.ridge_top + 1.0))
    x = -hx + wall_t * 0.5
    z0 = gable.under(0.45, 0.0) + 0.05
    block(shell, dressed, V(x - 0.2, -0.54, z0 - 0.4), V(x + 0.2, 0.54, z0 + 1.2))
    tk.atlas_panel(shell, "town_signs", kit.frame_point(kit.facade("front", ix, hy), 0.0, 3.62, 0.021), V(0.0, -1.0, 0.0), 1.2, 0.48, tp.sg("school_plaque"), 0.0, 0.0)
    return b
