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
stone = "granite_rubble"
dressed = "granite_ashlar"
oak = "timber_beam"
board = "timber_planks_weathered"
tower_x = 3.2
tower_y = (-13.0, -6.6)
tower_t = 0.85
tix = 2.35
tiy = (-12.15, -7.45)
tower_top = 19.2
tower_roof = 17.6
levels = (4.4, 8.8, 13.2)
nave_x = 6.0
nave_y = (-6.6, 8.4)
nave_t = 0.75
nix = 5.25
niy = (-5.85, 7.65)
chancel_x = 3.6
chancel_y = (8.4, 13.0)
chancel_t = 0.6
cix = 3.0
ciy = (8.4, 12.4)
chancel_floor = 0.3
vestry_x = (3.6, 6.0)
vestry_y = (8.4, 11.6)
vestry_t = 0.45
vix = (3.6, 5.55)
viy = (8.4, 11.15)
west_door = (-0.75, 0.75, -0.05, 2.8, 3.45)
west_window = (-0.45, 0.45, 5.2, 6.9, 7.5)
belfry_light = (14.0, 16.0, 16.75)
tower_arch = (-1.4, 1.4, -0.05, 3.3, 4.1)
chancel_arch = (-2.6, 2.6, -0.05, 4.2, 5.8)
nave_windows = (-3.0, 1.0, 5.0)
lancet_z = (2.4, 4.8, 5.7)
chancel_window = (10.4, 11.2, 2.2, 3.9, 4.6)
east_window = (-1.3, 1.3, 1.8, 5.0, 6.4)
vestry_door = (9.55, 10.7, chancel_floor, 2.55)
vestry_out = (-5.35, -4.2, chancel_floor, 2.55)
vestry_window = (9.6, 10.4, 1.4, 2.4)
stair_slits = ((-1.0, 2.0, 2.9), (1.0, 6.4, 7.3), (-1.0, 10.8, 11.7))
collar_z = 9.8
truss_y = (-4.1, -0.6, 2.9, 6.3)
roof_holes = [(0.4, 1.8, 2.8, 4.4, -1.0), (4.6, 5.6, 5.0, 6.2, 1.0)]


def nave_gable():
    return tk.YGable(nave_y[0], nave_y[1], nave_x, 0.3, 6.35, 45.0, 0.0)


def chancel_gable():
    return tk.YGable(chancel_y[0], chancel_y[1], chancel_x, 0.3, 4.75, 45.0, 0.0)


def vestry_gable():
    return tk.YGable(vestry_y[0], vestry_y[1], vestry_x[1] - vestry_x[0], 0.25, 3.35, 30.0, vestry_x[0])


def gable_outline(gable, inner, outer, top, depth=0.05):
    return [(-inner, -1.5), (inner, -1.5), (inner, top), (outer, gable.height(outer, depth)), (0.0, gable.height(0.0, depth)), (-outer, gable.height(-outer, depth)), (-inner, top)]


def inner_gable(gable, inner, z0, depth=0.06):
    return [(-inner, z0), (inner, z0), (inner, gable.height(inner, depth)), (0.0, gable.height(0.0, depth)), (-inner, gable.height(inner, depth))]


def gable_cols_y(b, tag, y0, y1, gable, base, steps=4, surface="rock"):
    for index in range(steps):
        z0 = base + (gable.ridge_top - base) * index / steps
        z1 = base + (gable.ridge_top - base) * (index + 1) / steps
        half = (gable.ridge_top - z1 - 0.05) / gable.tan
        if half > 0.05:
            b.col(surface, tag, V(gable.origin_x - half, y0, z0), V(gable.origin_x + half, y1, z1))


def rect_of(shape):
    a0, a1, z0, spring, apex = shape
    return (a0, a1, max(z0, 0.0), apex)


def surround(shell, frame, shape, pad=0.12, proud=0.03):
    a0, a1, z0, spring, apex = shape
    outer = tk.lancet(a0 - pad, a1 + pad, z0, spring, apex + pad * 1.4)
    inner = tk.lancet(a0, a1, z0, spring, apex)
    kit.skin(shell, dressed, frame, outer, [inner], proud)


def buttress(shell, b, foot, outward, width, steps):
    n = outward.normalized()
    matrix = kit.place(foot, n, up)
    profile = [(0.0, -0.45), (steps[0][1], -0.45)]
    for index, (z_top, depth) in enumerate(steps):
        profile.append((depth, z_top))
        if index + 1 < len(steps):
            following = steps[index + 1][1]
            profile.append((following, z_top + (depth - following)))
        else:
            profile.append((0.0, z_top + depth))
    kit.prism(shell, dressed, matrix, profile, -width * 0.5, width * 0.5)
    side = up.cross(n).normalized()
    lo, hi = kit.box_between(foot - side * (width * 0.5) - V(0.0, 0.0, 0.45), foot + side * (width * 0.5) + n * steps[0][1] + V(0.0, 0.0, steps[0][0]))
    b.col("rock", "buttress", lo, hi)


def glazing(joinery, frame, shape, depth, rng, broken=0.3, bars=0.45):
    a0, a1, z0, spring, apex = shape
    polygon = tk.lancet(a0 + 0.02, a1 - 0.02, z0 + 0.02, spring, apex - 0.03)
    holes = []
    if rng.random() < broken:
        holes = tk.scatter_light((a0 + 0.1, a1 - 0.1, z0 + 0.3, spring - 0.2), [], rng.randint(1, 2), (0.12, 0.3), rng, (0.6, 1.4), None, 7)
    kit.skin(joinery, "glass_dirty", frame, polygon, holes, 0.006, -depth)
    z = z0 + bars
    while z < spring:
        rod(joinery, "rusty_metal", kit.frame_point(frame, a0 + 0.01, z, -depth + 0.012), kit.frame_point(frame, a1 - 0.01, z, -depth + 0.012), 0.008, 4)
        z += bars


def tower_walls(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    west = kit.plane(V(0.0, tower_y[0], 0.0), V(0.0, -1.0, 0.0))
    east = kit.plane(V(0.0, tower_y[1], 0.0), V(0.0, 1.0, 0.0))
    left = kit.plane(V(-tower_x, 0.0, 0.0), V(-1.0, 0.0, 0.0))
    right = kit.plane(V(tower_x, 0.0, 0.0), V(1.0, 0.0, 0.0))
    belfry_face = (-0.5, 0.5) + belfry_light
    west_shapes = [west_door, west_window, belfry_face]
    kit.wall(shell, stone, west, kit.rect(-tower_x, tower_x, -1.5, tower_top), [tk.lancet(*s) for s in west_shapes], tower_t)
    kit.wall_boxes(b, "rock", "tower", west, -tower_x, tower_x, -1.5, tower_top, tower_t, [rect_of(s) for s in west_shapes])
    east_shapes = [tower_arch, belfry_face]
    kit.wall(shell, stone, east, kit.rect(-tower_x, tower_x, -1.5, tower_top), [tk.lancet(*s) for s in east_shapes], tower_t)
    kit.wall_boxes(b, "rock", "tower", east, -tower_x, tower_x, -1.5, tower_top, tower_t, [rect_of(s) for s in east_shapes])
    louvred = [(west, belfry_face), (east, belfry_face)]
    for frame, sign in ((left, -1.0), (right, 1.0)):
        center = -9.8 if sign > 0 else 9.8
        shape = (center - 0.5, center + 0.5) + belfry_light
        holes = [tk.lancet(*shape)]
        rects = [rect_of(shape)]
        for slit_side, z0, z1 in stair_slits:
            if slit_side == sign:
                a = -10.6 if sign > 0 else 10.6
                holes.append(kit.rect(a - 0.12, a + 0.12, z0, z1))
                rects.append((a - 0.12, a + 0.12, z0, z1))
        a_low, a_high = (tiy[0], tiy[1]) if sign > 0 else (-tiy[1], -tiy[0])
        kit.wall(shell, stone, frame, kit.rect(a_low, a_high, -1.5, tower_top), holes, tower_t)
        kit.wall_boxes(b, "rock", "tower", frame, a_low, a_high, -1.5, tower_top, tower_t, rects)
        louvred.append((frame, shape))
    for frame, shape in [(west, west_door), (west, west_window)] + louvred:
        surround(shell, frame, shape)
    tk.opening_block(b, "glass", "tower_window", west, rect_of(west_window), tower_t)
    glazing(joinery, west, west_window, 0.3, rng, 0.6)
    for frame, shape in louvred:
        a0, a1, z0, spring, apex = shape
        for index in range(6):
            if rng.random() < 0.15:
                continue
            center = kit.frame_point(frame, (a0 + a1) * 0.5, z0 + 0.2 + index * 0.36, -tower_t * 0.5)
            slope = (frame[3] * 0.6 - up).normalized()
            emit(joinery, kit.geo_box(a1 - a0 + 0.04, 0.3, 0.025), board, kit.place(center, frame[1], slope.cross(frame[1]).normalized()), "board")
        tk.opening_block(b, "wood", "louvre", frame, (a0, a1, z0, apex), tower_t)
    for frame, a0, a1 in ((west, -tower_x, tower_x), (east, -tower_x, tower_x), (left, 6.6, 13.0), (right, -13.0, -6.6)):
        frame_block(shell, dressed, frame, a0, a1, -0.45, 0.35, -0.08, 0.0, 0.0)
        for z in levels:
            frame_block(shell, dressed, frame, a0, a1, z - 0.08, z + 0.08, -0.07, 0.0, 0.0)
        frame_block(shell, dressed, frame, a0 - 0.08, a1 + 0.08, tower_top - 0.02, tower_top + 0.1, -0.1, tower_t + 0.05, 0.0)
        a = a0 + 0.35
        merlon = True
        while a < a1 - 0.3:
            width = min(0.55, a1 - 0.35 - a)
            if merlon and width > 0.2:
                frame_block(shell, dressed, frame, a, a + width, tower_top + 0.1, tower_top + 0.65, 0.0, tower_t, 0.01)
            a += width + 0.02
            merlon = not merlon
    emit(shell, kit.geo_lathe([(0.66, 0.0), (0.84, 0.0), (0.84, 0.05), (0.66, 0.05)], 20), dressed, kit.place(V(0.0, tower_y[0], 10.7), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), "given", True)
    tp.disc(shell, "town_print", V(0.0, tower_y[0] - 0.035, 10.7), V(0.0, -1.0, 0.0), 0.68, tp.pr("clock", 2.0), 20)
    block(shell, "concrete", V(-tix, tiy[0], tower_roof - 0.12), V(tix, tiy[1], tower_roof), 0.0, "world")
    block(parts["floors"], board, V(-tix, tiy[0], tower_roof - 0.15), V(tix, tiy[1], tower_roof - 0.12), 0.0, "world")
    tk.col(b, "rock", "tower_roof", -tix, tix, tiy[0], tiy[1], tower_roof - 0.15, tower_roof)
    for cx in (-tower_x + 0.25, tower_x - 0.25):
        for cy in (tower_y[0] + 0.25, tower_y[1] - 0.25):
            block(shell, dressed, V(cx - 0.25, cy - 0.25, tower_top + 0.1), V(cx + 0.25, cy + 0.25, tower_top + 0.95), 0.01)
            emit(shell, kit.geo_frustum(0.27, 0.27, 0.0, 0.0, 0.7), dressed, kit.Matrix.Translation(V(cx, cy, tower_top + 0.95)), "box")
    for sx in (-1.0, 1.0):
        buttress(shell, b, V(sx * (tower_x - 0.45), tower_y[0], 0.0), V(0.0, -1.0, 0.0), 0.8, [(5.0, 0.95), (10.0, 0.65), (14.2, 0.35)])
        buttress(shell, b, V(sx * tower_x, tower_y[0] + 0.45, 0.0), V(sx, 0.0, 0.0), 0.8, [(5.0, 0.95), (10.0, 0.65), (14.2, 0.35)])
    return west


def west_doors(b, parts, rng, west):
    joinery = parts["joinery"]
    shell = parts["shell"]
    a0, a1, z0, spring, apex = west_door
    ja0, ja1, jtop = tk.door_frame_light(joinery, oak, west, a0, a1, 0.0, spring, 0.25, 0.08, 0.2)
    head = tk.lancet(a0, a1, spring, spring, apex)
    kit.skin(joinery, board, west, head[:2] + head[3:-1], [], 0.05, -0.3)
    width = (ja1 - ja0) * 0.5 - 0.01
    d_axis = 0.25 + 0.1 - 0.0225
    tk.door_leaf_light(joinery, board, west, ja0 + 0.005, 1.0, d_axis, 0.01, jtop - 0.02, width, 104.0, rng, "ledged", 2.0)
    tk.door_leaf_light(joinery, board, west, ja1 - 0.005, -1.0, d_axis, 0.01, jtop - 0.02, width, 88.0, rng, "ledged", 1.0)
    block(shell, dressed, V(a0 - 0.2, tower_y[0] - 0.55, -0.45), V(a1 + 0.2, tower_y[0] + 0.02, -0.07), 0.015)
    block(shell, dressed, V(a0 - 0.35, tower_y[0] - 0.95, -0.6), V(a1 + 0.35, tower_y[0] - 0.5, -0.12), 0.015)
    tk.col(b, "rock", "step", a0 - 0.2, a1 + 0.2, tower_y[0] - 0.55, tower_y[0], -1.5, -0.07)
    tk.col(b, "rock", "step", a0 - 0.35, a1 + 0.35, tower_y[0] - 0.95, tower_y[0] - 0.55, -1.5, -0.12)
    tk.col(b, "rock", "threshold", a0, a1, tower_y[0], tiy[0], -1.5, 0.0)
    block(shell, dressed, V(a0, tower_y[0], -0.08), V(a1, tiy[0] + 0.03, 0.0), 0.004)
    block(joinery, "town_paint_navy", V(1.05, tower_y[0] - 0.06, 1.25), V(2.15, tower_y[0], 2.15), 0.004, "board")
    tk.atlas_panel(joinery, "town_signs", V(1.6, tower_y[0] - 0.061, 1.7), V(0.0, -1.0, 0.0), 1.0, 0.8, tp.sg("church_board"), 0.0, 0.0)


def tower_inside(b, parts, rng):
    floors = parts["floors"]
    joinery = parts["joinery"]
    tk.tile_floor(floors, dressed, -tix, tix, tiy[0], tiy[1], 0.0, 0.03)
    tk.col(b, "rock", "floor", -tix, tix, tiy[0], tiy[1], -0.3, 0.0)
    for z, (hx0, hx1) in zip(levels, ((-tix, -1.5), (1.5, tix), (-tix, -1.5))):
        hole = (hx0, hx1, tiy[0], -9.35)
        tk.board_floor(floors, -tix, tix, tiy[0], tiy[1], z, rng, "x", [hole], "floorboards", 0.02, 0.05, (0.2, 0.28), ())
        tk.floor_cols(b, "wood", "tower_floor", -tix, tix, tiy[0], tiy[1], z - 0.2, z, [hole])
        for x in (-1.0, 0.9):
            block(floors, oak, V(x - 0.09, tiy[0], z - 0.3), V(x + 0.09, tiy[1], z - 0.03), 0.004)
        inner = hx1 if hx0 < 0 else hx0
        bd.balustrade(b, joinery, V(inner, -11.3, z), V(inner, -9.37, z), rng, 0.9, 0.16, oak, oak, 0.12, (True, True), True, "rail")
        bd.balustrade(b, joinery, V(hx0, -9.33, z), V(hx1, -9.33, z), rng, 0.9, 0.16, oak, oak, 0.12, (False, False), True, "rail")
    for z0, sx in ((0.0, -1.0), (levels[0], 1.0), (levels[1], -1.0)):
        inner = (0.65, 1.5) if sx > 0 else (-1.5, -0.65)
        outer = (1.5, tix) if sx > 0 else (-tix, -1.5)
        tk.stair_flight(b, parts, inner[0], inner[1], -11.95, z0, 2.6, 2.2, 10, rng, 1.0, board, oak, None, None, "wood", "tower_stair")
        lx0 = min(inner[0], outer[0])
        lx1 = max(inner[1], outer[1])
        block(floors, board, V(lx0, -9.35, z0 + 2.12), V(lx1, -8.45, z0 + 2.2), 0.0, "board")
        block(floors, oak, V(lx0, -8.55, z0 + 1.98), V(lx1, -8.45, z0 + 2.12), 0.004)
        for x in (lx0 + 0.06, lx1 - 0.06):
            block(floors, oak, V(x - 0.05, -8.6, z0), V(x + 0.05, -8.5, z0 + 1.98), 0.004)
        tk.col(b, "wood", "landing", lx0, lx1, -9.35, -8.45, z0, z0 + 2.2)
        tk.stair_flight(b, parts, outer[0], outer[1], -9.35, z0 + 2.2, 2.6, 2.2, 10, rng, -1.0, board, oak, None, None, "wood", "tower_stair")


def bell_frame(b, parts, rng):
    joinery = parts["joinery"]
    furniture = parts["furniture"]
    z = levels[2]
    cx = 0.65
    cy = -9.8
    for x in (cx - 0.95, cx + 0.95):
        for y in (cy - 1.1, cy + 1.1):
            top_y = cy - 0.12 if y < cy else cy + 0.12
            kit.member(joinery, oak, V(x, y, z), V(x, top_y, z + 2.3), 0.16, 0.16, V(1.0, 0.0, 0.0), 0.0, "box")
        kit.member(joinery, oak, V(x, cy - 1.25, z + 0.08), V(x, cy + 1.25, z + 0.08), 0.2, 0.16, up, 0.0, "box")
        kit.member(joinery, oak, V(x, cy - 0.35, z + 2.3), V(x, cy + 0.35, z + 2.3), 0.2, 0.2, up, 0.0, "box")
    kit.member(joinery, oak, V(cx - 1.05, cy, z + 2.42), V(cx + 1.05, cy, z + 2.42), 0.22, 0.2, up, 0.0, "box")
    for y in (cy - 1.15, cy + 1.15):
        kit.member(joinery, oak, V(cx - 0.95, y, z + 0.08), V(cx + 0.95, y, z + 0.08), 0.16, 0.16, up, 0.0, "box")
    crown = V(cx, cy, z + 2.3)
    r = 0.52
    h = 0.98
    profile = [(0.0, 0.0), (0.42 * r, 0.0), (0.55 * r, -0.08 * h), (0.58 * r, -0.3 * h), (0.66 * r, -0.6 * h), (0.85 * r, -0.85 * h), (1.0 * r, -0.97 * h), (0.98 * r, -1.0 * h), (0.9 * r, -0.96 * h), (0.78 * r, -0.85 * h), (0.6 * r, -0.6 * h), (0.5 * r, -0.3 * h), (0.0, -0.25 * h)]
    emit(furniture, kit.geo_lathe(profile, 14), "town_brass", kit.Matrix.Translation(crown) @ kit.Matrix.Rotation(0.18, 4, 'Y'), "given", True)
    rod(furniture, "rusty_metal", crown - V(0.0, 0.0, 0.25), crown - V(0.05, 0.0, 0.85), 0.025, 5)
    emit(furniture, kit.geo_lathe([(0.0, -0.06), (0.06, 0.0), (0.0, 0.06)], 6), "rusty_metal", kit.Matrix.Translation(crown - V(0.05, 0.0, 0.88)), "given", True)
    hub = V(cx - 0.62, cy, z + 2.42)
    emit(joinery, kit.geo_lathe([(0.66, -0.03), (0.72, -0.03), (0.72, 0.03), (0.66, 0.03)], 16), oak, kit.place(hub, V(0.0, 1.0, 0.0), V(1.0, 0.0, 0.0)), "given", True)
    for k in range(4):
        angle = tau * k / 4 + 0.4
        rod(joinery, oak, hub, hub + V(0.0, math.cos(angle) * 0.68, math.sin(angle) * 0.68), 0.02, 4)
    rope_top = hub + V(0.0, 0.7, -0.1)
    rope_bottom = V(rope_top.x, rope_top.y, levels[0] + 1.25)
    rod(furniture, "hay", rope_top, rope_bottom, 0.014, 4)
    emit(furniture, kit.geo_lathe([(0.0, 0.0), (0.045, 0.02), (0.05, 0.3), (0.045, 0.58), (0.0, 0.6)], 6), "town_paint_red", kit.Matrix.Translation(rope_bottom + V(0.0, 0.0, 0.25)), "given", True)
    rod(furniture, "hay", rope_bottom, rope_bottom - V(0.0, 0.0, 0.35), 0.014, 4)
    for level in levels[1:]:
        emit(furniture, kit.geo_lathe([(0.03, -0.02), (0.08, -0.02), (0.08, 0.02), (0.03, 0.02)], 8), oak, kit.Matrix.Translation(V(rope_top.x, rope_top.y, level + 0.02)), "given", True)
    tk.col(b, "wood", "bell_frame", cx - 1.1, cx + 1.1, cy - 1.3, cy + 1.3, z, z + 2.55)
    tk.chips(parts["debris"], "plaster_interior", -2.0, 2.0, -11.8, -7.8, z, 10, rng, (0.01, 0.04), (0.004, 0.008))
    tk.chips(parts["debris"], "plaster_interior", -0.5, 2.0, -11.8, -7.8, levels[1], 6, rng, (0.01, 0.03), (0.004, 0.006))


def tower_rooms(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.bench_light(b, furniture, V(tix - 0.25, -10.4, 0.0), math.pi * 0.5, rng, 1.6, board, oak)
    tp.wall_sheet(interior, V(tix - 0.012, -8.9, 1.6), V(-1.0, 0.0, 0.0), "notice", rng, 1.0, 0.02)
    tp.wall_sheet(interior, V(tix - 0.012, -11.65, 1.5), V(-1.0, 0.0, 0.0), "poster", rng, 1.0, -0.03)
    tk.pendant(b, interior, V(0.4, -9.8, levels[0] - 0.2), rng, "glass_dirty", 0.6, "warm", 8)
    tp.papers(parts["debris"], -0.6, 1.8, -11.9, -8.0, 0.0, 4, rng, ("notice", "card", "newspaper"))
    tk.chips(parts["debris"], "foliage", -0.6, 1.8, -12.0, -10.5, 0.0, 10, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    tp.bench_light(b, furniture, V(-0.4, tiy[1] - 0.25, levels[0]), 0.0, rng, 1.4, board, oak)
    b.loot("box", V(-0.4, tiy[1] - 0.25, levels[0] + 0.45))
    tp.crate_light(clutter, V(-1.25, tiy[1] - 0.3, levels[0]), (0.5, 0.4, 0.36), 0.2, rng)
    tp.framed(interior, V(-tix + 0.006, -8.3, levels[0] + 1.6), V(1.0, 0.0, 0.0), 0.42, 0.56, tp.pr("notice"), rng, oak, 0.02)
    tp.framed(interior, V(0.0, tiy[1] - 0.006, levels[0] + 1.75), V(0.0, -1.0, 0.0), 0.4, 0.5, tp.pr("calendar"), rng, oak, -0.03)
    tk.pendant(b, interior, V(-0.2, -10.6, levels[1] - 0.2), rng, "glass_dirty", 0.5, "warm", 8)
    frame = kit.turned(V(0.4, -11.3, levels[1]), 0.0)
    for sx in (-0.45, 0.45):
        for sy in (-0.25, 0.25):
            local_block(furniture, "rusty_metal", frame, sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.95)
    local_block(furniture, "rusty_metal", frame, -0.5, 0.5, -0.3, 0.3, 0.92, 0.98)
    local_block(furniture, "rusty_metal", frame, -0.5, 0.5, -0.3, 0.3, 0.3, 0.34)
    for x, radius in ((-0.2, 0.22), (0.15, 0.16), (0.32, 0.1)):
        emit(furniture, kit.geo_lathe([(0.0, -0.015), (radius, -0.015), (radius, 0.015), (0.0, 0.015)], 12), "town_brass", frame @ kit.Matrix.Translation(V(x, 0.0, 0.62)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)
    rod(furniture, "rusty_metal", frame @ V(0.0, -0.3, 0.62), V(0.0, tiy[0] + 0.02, 10.7), 0.012, 5)
    tk.col(b, "metal", "clock", -0.15, 0.95, -11.65, -10.95, levels[1], levels[1] + 1.0)


def nave_walls(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    interior = parts["interior"]
    g = nave_gable()
    wall_top = g.height(nave_x, 0.03)
    frames = {}
    for sign in (-1.0, 1.0):
        frame = kit.plane(V(sign * nave_x, 0.0, 0.0), V(sign, 0.0, 0.0))
        a_low, a_high = nave_y if sign > 0 else (-nave_y[1], -nave_y[0])
        shapes = [(sign * y - 0.5, sign * y + 0.5) + lancet_z for y in nave_windows]
        kit.wall(shell, stone, frame, kit.rect(a_low, a_high, -1.5, wall_top), [tk.lancet(*s) for s in shapes], nave_t)
        kit.wall_boxes(b, "rock", "nave", frame, a_low, a_high, -1.5, wall_top, nave_t, [rect_of(s) for s in shapes])
        for shape in shapes:
            surround(shell, frame, shape)
            glazing(joinery, frame, shape, 0.3, rng, 0.45)
            tk.opening_block(b, "glass", "window", frame, rect_of(shape), nave_t)
            kit.sill_stone(shell, dressed, frame, shape[0], shape[1], shape[2], 0.3, 0.06, 0.08, 0.1)
        inner_low, inner_high = niy if sign > 0 else (-niy[1], -niy[0])
        tk.inner_skin(interior, frame, nave_t, kit.rect(inner_low, inner_high, 0.0, wall_top - 0.04), [tk.lancet(*s) for s in shapes], rng, 4)
        x_in = sign * nix
        x_out = sign * nave_x
        if sign > 0:
            points = [(x_in, wall_top - 0.02), (x_out, wall_top - 0.02), (x_in, g.height(nix, 0.06))]
        else:
            points = [(x_out, wall_top - 0.02), (x_in, wall_top - 0.02), (x_in, g.height(nix, 0.06))]
        kit.prism(shell, stone, kit.Matrix.Identity(4), points, niy[0], niy[1])
        kit.member(joinery, oak, V(sign * (nix - 0.1), niy[0], wall_top + 0.05), V(sign * (nix - 0.1), niy[1], wall_top + 0.05), 0.2, 0.18, up, 0.0, "box")
        frame_block(shell, dressed, frame, a_low, a_high, -0.45, 0.3, -0.07, 0.0, 0.0)
        frames[sign] = frame
    west = kit.plane(V(0.0, nave_y[0], 0.0), V(0.0, -1.0, 0.0))
    kit.wall(shell, stone, west, gable_outline(g, nix, nave_x, wall_top), [tk.lancet(*tower_arch)], nave_t)
    kit.wall_boxes(b, "rock", "nave_west", west, -nix, nix, -1.5, wall_top, nave_t, [rect_of(tower_arch)])
    gable_cols_y(b, "nave_gable", nave_y[0], nave_y[0] + nave_t, g, wall_top)
    tk.inner_skin(interior, west, nave_t, inner_gable(g, nix, 0.0), [tk.lancet(*tower_arch)], rng, 3)
    east = kit.plane(V(0.0, nave_y[1], 0.0), V(0.0, 1.0, 0.0))
    kit.wall(shell, stone, east, gable_outline(g, nix, nave_x, wall_top), [tk.lancet(*chancel_arch)], nave_t)
    kit.wall_boxes(b, "rock", "nave_east", east, -nix, nix, -1.5, wall_top, nave_t, [rect_of(chancel_arch)])
    gable_cols_y(b, "nave_gable", nave_y[1] - nave_t, nave_y[1], g, wall_top)
    tk.inner_skin(interior, east, nave_t, inner_gable(g, nix, 0.0), [tk.lancet(*chancel_arch)], rng, 3)
    inner_east = kit.plane(V(0.0, niy[1], 0.0), V(0.0, -1.0, 0.0))
    surround(shell, inner_east, chancel_arch, 0.18, 0.03)
    inner_west = kit.plane(V(0.0, niy[0], 0.0), V(0.0, 1.0, 0.0))
    surround(shell, inner_west, (-tower_arch[1], -tower_arch[0]) + tower_arch[2:], 0.15, 0.03)
    for sign in (-1.0, 1.0):
        buttress(shell, b, V(sign * nave_x, nave_y[1] - 0.45, 0.0), V(sign, 0.0, 0.0), 0.75, [(3.0, 0.8), (5.2, 0.45)])
        buttress(shell, b, V(sign * nave_x, -1.0, 0.0), V(sign, 0.0, 0.0), 0.7, [(2.6, 0.7), (4.8, 0.4)])
        buttress(shell, b, V(sign * nave_x, 3.0, 0.0), V(sign, 0.0, 0.0), 0.7, [(2.6, 0.7), (4.8, 0.4)])
        buttress(shell, b, V(sign * (nave_x - 0.4), nave_y[0], 0.0), V(0.0, -1.0, 0.0), 0.75, [(3.0, 0.8), (5.2, 0.45)])
    return g, wall_top, east


def trusses(parts, g, wall_top):
    joinery = parts["joinery"]
    shell = parts["shell"]
    reach = g.ridge_top - 0.3 - collar_z
    for y in truss_y:
        for sx in (-1.0, 1.0):
            foot = V(sx * (nix - 0.15), y, wall_top + 0.12)
            top = V(0.0, y, g.height(0.0, 0.3))
            kit.member(joinery, oak, foot, top, 0.14, 0.22, V(sx * g.sin, 0.0, g.cos), 0.0, "box")
            collar_end = V(sx * (reach + 0.05), y, collar_z)
            knee = V(sx * (nix - 0.95), y, collar_z - 2.0)
            post_top = V(sx * (nix - 0.12), y, wall_top - 0.2)
            post_foot = V(sx * (nix - 0.12), y, wall_top - 2.2)
            kit.member(joinery, oak, post_foot, post_top, 0.14, 0.18, V(0.0, 1.0, 0.0), 0.0, "box")
            for a, c in ((post_foot + V(0.0, 0.0, 0.3), knee), (knee, collar_end)):
                kit.member(joinery, oak, a, c, 0.12, 0.16, V(0.0, 1.0, 0.0).cross((c - a).normalized()), 0.0, "box")
            lo, hi = kit.box_between(V(sx * nix, y - 0.15, wall_top - 2.45), V(sx * (nix - 0.25), y + 0.15, wall_top - 2.2))
            block(shell, dressed, lo, hi, 0.01)
        kit.member(joinery, oak, V(-reach, y, collar_z), V(reach, y, collar_z), 0.14, 0.2, up, 0.0, "box")
    kit.member(joinery, oak, V(0.0, niy[0], g.height(0.0, 0.28)), V(0.0, niy[1], g.height(0.0, 0.28)), 0.16, 0.22, up, 0.0, "box")
    for sx in (-1.0, 1.0):
        x = sx * 2.9
        kit.member(joinery, oak, V(x, niy[0], g.height(x, 0.2)), V(x, niy[1], g.height(x, 0.2)), 0.14, 0.18, V(sx * g.sin, 0.0, g.cos), 0.0, "box")


def chancel_walls(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    interior = parts["interior"]
    g = chancel_gable()
    top = g.height(chancel_x, 0.03)
    left = kit.plane(V(-chancel_x, 0.0, 0.0), V(-1.0, 0.0, 0.0))
    kit.wall(shell, stone, left, kit.rect(-chancel_y[1], -chancel_y[0], -1.5, top), [tk.lancet(*chancel_window)], chancel_t)
    kit.wall_boxes(b, "rock", "chancel", left, -chancel_y[1], -chancel_y[0], -1.5, top, chancel_t, [rect_of(chancel_window)])
    surround(shell, left, chancel_window)
    glazing(joinery, left, chancel_window, 0.25, rng, 0.5)
    tk.opening_block(b, "glass", "window", left, rect_of(chancel_window), chancel_t)
    kit.sill_stone(shell, dressed, left, chancel_window[0], chancel_window[1], chancel_window[2], 0.25, 0.06, 0.08, 0.1)
    tk.inner_skin(interior, left, chancel_t, kit.rect(-ciy[1], -ciy[0], chancel_floor, top - 0.04), [tk.lancet(*chancel_window)], rng, 2)
    right = kit.plane(V(chancel_x, 0.0, 0.0), V(1.0, 0.0, 0.0))
    door_hole = kit.rect(vestry_door[0], vestry_door[1], vestry_door[2] - 0.05, vestry_door[3])
    kit.wall(shell, stone, right, kit.rect(chancel_y[0], chancel_y[1], -1.5, top), [door_hole], chancel_t)
    kit.wall_boxes(b, "rock", "chancel", right, chancel_y[0], chancel_y[1], -1.5, top, chancel_t, [vestry_door])
    tk.door_unit(joinery, right, vestry_door[0], vestry_door[1], vestry_door[2], vestry_door[3] - vestry_door[2], chancel_t, oak, rng, "high", -95.0, "ledged")
    tk.inner_skin(interior, right, chancel_t, kit.rect(ciy[0], ciy[1], chancel_floor, top - 0.04), [kit.rect(vestry_door[0], vestry_door[1], vestry_door[2], vestry_door[3])], rng, 2)
    east = kit.plane(V(0.0, chancel_y[1], 0.0), V(0.0, 1.0, 0.0))
    kit.wall(shell, stone, east, gable_outline(g, cix, chancel_x, top), [tk.lancet(*east_window)], chancel_t)
    kit.wall_boxes(b, "rock", "chancel_east", east, -cix, cix, -1.5, top, chancel_t, [rect_of(east_window)])
    gable_cols_y(b, "chancel_gable", chancel_y[1] - chancel_t, chancel_y[1], g, top)
    surround(shell, east, east_window, 0.15)
    glazing(joinery, east, east_window, 0.25, rng, 0.35)
    for a in (-0.43, 0.43):
        frame_block(shell, dressed, east, a - 0.06, a + 0.06, east_window[2], east_window[3] + 0.6, 0.05, 0.42, 0.0)
    tk.opening_block(b, "glass", "window", east, rect_of(east_window), chancel_t)
    kit.sill_stone(shell, dressed, east, east_window[0], east_window[1], east_window[2], 0.25, 0.06, 0.08, 0.1)
    tk.inner_skin(interior, east, chancel_t, inner_gable(g, cix, chancel_floor), [tk.lancet(*east_window)], rng, 2)
    for sign in (-1.0, 1.0):
        x_in = sign * cix
        x_out = sign * chancel_x
        if sign > 0:
            points = [(x_in, top - 0.02), (x_out, top - 0.02), (x_in, g.height(cix, 0.06))]
        else:
            points = [(x_out, top - 0.02), (x_in, top - 0.02), (x_in, g.height(cix, 0.06))]
        kit.prism(shell, stone, kit.Matrix.Identity(4), points, ciy[0], ciy[1])
        kit.member(joinery, oak, V(sign * (cix - 0.1), ciy[0], top + 0.05), V(sign * (cix - 0.1), ciy[1], top + 0.05), 0.18, 0.16, up, 0.0, "box")
        buttress(shell, b, V(sign * (chancel_x - 0.35), chancel_y[1], 0.0), V(0.0, 1.0, 0.0), 0.6, [(2.6, 0.6), (4.2, 0.35)])
    buttress(shell, b, V(-chancel_x, chancel_y[1] - 0.35, 0.0), V(-1.0, 0.0, 0.0), 0.6, [(2.6, 0.6), (4.2, 0.35)])
    kit.member(joinery, oak, V(0.0, ciy[0], g.height(0.0, 0.26)), V(0.0, ciy[1], g.height(0.0, 0.26)), 0.14, 0.2, up, 0.0, "box")
    for y in (9.6, 11.2):
        for sx in (-1.0, 1.0):
            kit.member(joinery, oak, V(sx * (cix - 0.1), y, top + 0.1), V(0.0, y, g.height(0.0, 0.26)), 0.12, 0.18, V(sx * g.sin, 0.0, g.cos), 0.0, "box")
    return g, top, right


def vestry_walls(b, parts, rng, nave_east, chancel_right):
    shell = parts["shell"]
    joinery = parts["joinery"]
    interior = parts["interior"]
    g = vestry_gable()
    top = g.height(vestry_x[1], 0.03)
    north = kit.plane(V(vestry_x[1], 0.0, 0.0), V(1.0, 0.0, 0.0))
    kit.wall(shell, stone, north, kit.rect(vestry_y[0], vestry_y[1], -1.5, top), [kit.rect(*vestry_window)], vestry_t)
    kit.wall_boxes(b, "rock", "vestry", north, vestry_y[0], vestry_y[1], -1.5, top, vestry_t, [vestry_window])
    tk.casement(b, parts, north, vestry_window, vestry_t, rng, "painted_wood_white", 0.1, [25.0], 0.3, 0.3, 2, dressed)
    tk.inner_skin(interior, north, vestry_t, kit.rect(viy[0], viy[1], chancel_floor, top - 0.03), [kit.rect(*vestry_window)], rng, 1)
    east = kit.plane(V(0.0, vestry_y[1], 0.0), V(0.0, 1.0, 0.0))
    outline = [(-vix[1], -1.5), (-vix[0], -1.5), (-vix[0], g.height(vix[0], 0.06)), (-vix[1], g.height(vix[1], 0.06))]
    door_hole = kit.rect(vestry_out[0], vestry_out[1], vestry_out[2] - 0.05, vestry_out[3])
    kit.wall(shell, stone, east, outline, [door_hole], vestry_t)
    kit.wall_boxes(b, "rock", "vestry", east, -vix[1], -vix[0], -1.5, g.height(vix[1], 0.06), vestry_t, [vestry_out])
    tk.door_unit(joinery, east, vestry_out[0], vestry_out[1], vestry_out[2], vestry_out[3] - vestry_out[2], vestry_t, "town_paint_red", rng, "low", 82.0, "ledged")
    tk.inner_skin(interior, east, vestry_t, [(-vix[1], chancel_floor), (-vix[0], chancel_floor), (-vix[0], g.height(vix[0], 0.08)), (-vix[1], g.height(vix[1], 0.08))], [kit.rect(vestry_out[0], vestry_out[1], vestry_out[2], vestry_out[3])], rng, 1)
    block(shell, dressed, V(-vestry_out[1] - 0.1, vestry_y[1] - 0.02, -0.45), V(-vestry_out[0] + 0.1, vestry_y[1] + 0.45, 0.1), 0.012)
    tk.col(b, "rock", "step", -vestry_out[1] - 0.1, -vestry_out[0] + 0.1, vestry_y[1] - 0.02, vestry_y[1] + 0.45, -1.5, 0.1)
    tk.col(b, "rock", "threshold", -vestry_out[1], -vestry_out[0], viy[1], vestry_y[1], -1.5, chancel_floor)
    kit.skin(interior, "plaster_interior", nave_east, kit.rect(-vix[1], -vix[0], chancel_floor, 3.75), [], 0.015, 0.0)
    kit.skin(interior, "plaster_interior", chancel_right, kit.rect(viy[0], viy[1], chancel_floor, g.height(vix[0], 0.1)), [kit.rect(vestry_door[0], vestry_door[1], vestry_door[2], vestry_door[3])], 0.015, 0.0)
    block(shell, "rusty_metal", V(vestry_x[0], vestry_y[0], g.ridge_top - 0.06), V(vestry_x[0] + 0.14, vestry_y[1], g.ridge_top + 0.06), 0.004)
    return g


def floors(b, parts, rng):
    floor = parts["floors"]
    tk.tile_floor(floor, dressed, -tower_arch[1], tower_arch[1], tiy[1], niy[0], 0.0, 0.03)
    tk.tile_floor(floor, dressed, -nix, nix, niy[0], niy[1], 0.0, 0.03)
    tk.tile_floor(floor, "town_tiles", -0.85, 0.85, niy[0] + 0.3, niy[1] - 0.1, 0.006, 0.006)
    block(floor, dressed, V(-chancel_arch[1], niy[1], 0.0), V(chancel_arch[1], ciy[0], chancel_floor), 0.0, "world")
    tk.tile_floor(floor, "town_tiles", -cix, cix, ciy[0], ciy[1], chancel_floor, 0.03)
    block(floor, dressed, V(-cix, 11.0, chancel_floor), V(cix, ciy[1], chancel_floor + 0.15), 0.004, "world")
    tk.board_floor(floor, vix[0], vix[1], viy[0], viy[1], chancel_floor, rng, "y", (), "floorboards", 0.02, 0.05, (0.16, 0.22), ())
    tk.col(b, "rock", "floor", -tower_arch[1], tower_arch[1], tiy[1], niy[0], -0.3, 0.0)
    tk.col(b, "rock", "floor", -nix, nix, niy[0], niy[1], -0.3, 0.0)
    tk.col(b, "rock", "chancel", -chancel_arch[1], chancel_arch[1], niy[1], ciy[0], -0.3, chancel_floor)
    tk.col(b, "rock", "chancel", -cix, cix, ciy[0], ciy[1], -0.3, chancel_floor)
    tk.col(b, "rock", "sanctuary", -cix, cix, 11.0, ciy[1], chancel_floor, chancel_floor + 0.15)
    tk.col(b, "wood", "vestry", vix[0], vix[1], viy[0], viy[1], -0.3, chancel_floor)
    tk.col(b, "rock", "threshold", cix, chancel_x, vestry_door[0], vestry_door[1], -0.3, chancel_floor)


def nave_furniture(b, parts, rng, g):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    debris = parts["debris"]
    rows = [-3.0 + index for index in range(9)]
    missing = {(-1.0, 3), (1.0, 6), (1.0, 0)}
    toppled = {(-1.0, 4), (1.0, 7)}
    for index, y in enumerate(rows):
        for sx in (-1.0, 1.0):
            if (sx, index) in missing:
                continue
            center = V(sx * 2.7, y, 0.0)
            if (sx, index) in toppled:
                tp.pew_light(b, furniture, center + V(rng.uniform(-0.2, 0.2), 0.0, 0.0), math.pi + rng.uniform(-0.12, 0.12), rng, 3.4, -math.pi * 0.5)
                continue
            twist = rng.uniform(-0.25, 0.25) if rng.random() < 0.18 else rng.uniform(-0.02, 0.02)
            shift = V(rng.uniform(-0.15, 0.15), rng.uniform(-0.08, 0.08), 0.0) if abs(twist) > 0.05 else V(0.0, 0.0, 0.0)
            base = tp.pew_light(b, furniture, center + shift, math.pi + twist, rng, 3.4)
            if rng.random() < 0.3:
                start = base @ V(rng.uniform(-1.3, 0.6), 0.33, 0.785)
                tp.book_row(clutter, start, (base @ V(1.0, 0.33, 0.785)) - (base @ V(0.0, 0.33, 0.785)), rng.uniform(0.15, 0.4), rng, (0.1, 0.13), (0.14, 0.18), False, 0.3)
            if rng.random() < 0.25:
                lump(clutter, "fabric_tartan", base @ V(rng.uniform(-1.2, 1.2), -0.45, 0.05), (0.18, 0.12, 0.05), rng, 0.2, 1)
    tp.font_light(b, furniture, V(-3.3, -4.7, 0.0), rng)
    tp.pulpit_light(b, furniture, V(-4.45, 6.7, 0.0), rng)
    tp.lectern_light(b, furniture, clutter, V(1.5, 6.9, 0.0), math.pi, rng)
    tp.organ_light(b, furniture, clutter, V(4.75, 6.6, 0.0), -math.pi * 0.5, rng)
    tp.framed(interior, V(-nix + 0.006, -1.0, 2.1), V(1.0, 0.0, 0.0), 0.5, 0.5, tp.pr("hymns"), rng, oak)
    tp.framed(interior, V(nix - 0.006, 3.0, 2.1), V(-1.0, 0.0, 0.0), 0.5, 0.5, tp.pr("hymns"), rng, oak, 0.02)
    for x_wall, normal, y, z in ((-nix, 1.0, 3.0, 1.9), (-nix, 1.0, -5.0, 2.0), (nix, -1.0, -1.0, 1.85), (nix, -1.0, -4.8, 2.2)):
        lo, hi = kit.box_between(V(x_wall, y - 0.32, z - 0.42), V(x_wall + normal * 0.05, y + 0.32, z + 0.42))
        block(interior, dressed, lo, hi, 0.01)
        lo, hi = kit.box_between(V(x_wall + normal * 0.05, y - 0.26, z - 0.34), V(x_wall + normal * 0.07, y + 0.26, z + 0.34))
        block(interior, "ceramic", lo, hi, 0.004)
    for y in truss_y[:3]:
        tk.pendant(b, interior, V(0.0, y, collar_z - 0.1), rng, "town_brass", collar_z - 0.1 - 3.6, "warm", 8)
    kit.member(furniture, oak, V(2.3, 0.15, 0.95), V(4.6, 2.1, 0.08), 0.12, 0.18, None, 0.0, "box")
    tk.chips(debris, "slate_roof", 2.6, 4.6, 0.0, 2.2, 0.0, 12, rng, (0.08, 0.17), (0.006, 0.008))
    tk.chips(debris, "slate_roof", -3.0, -1.6, 4.4, 5.8, 0.0, 8, rng, (0.08, 0.17), (0.006, 0.008))
    tk.chips(debris, "foliage", -1.0, 1.0, -5.8, -2.0, 0.0, 16, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    tk.chips(debris, "plaster_interior", -5.0, 5.0, -5.6, 7.4, 0.0, 18, rng)
    tp.papers(debris, -1.0, 1.0, -5.5, 6.5, 0.0, 6, rng, ("music", "notice", "letter", "card"))
    for index in range(4):
        tp.book_row(clutter, V(rng.uniform(-0.8, 0.6), rng.uniform(-4.0, 6.0), 0.0), V(math.cos(rng.uniform(0.0, tau)), math.sin(rng.uniform(0.0, tau)), 0.0), 0.12, rng, (0.1, 0.13), (0.14, 0.18), False, 1.0)


def chancel_furniture(b, parts, rng, g, top):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.choir_stall(b, furniture, V(-2.45, 9.6, chancel_floor), math.pi * 0.5, rng, 1.8)
    tp.chair_light(furniture, V(2.55, 8.95, chancel_floor), -math.pi * 0.5 + 0.3, rng)
    tp.altar_rail(b, furniture, -cix + 0.05, -0.5, 10.9, chancel_floor, rng)
    tp.altar_rail(b, furniture, 0.5, cix - 0.05, 10.9, chancel_floor, rng)
    tp.altar_light(b, furniture, clutter, V(0.0, 11.95, chancel_floor + 0.15), 0.0, rng)
    tk.pendant(b, interior, V(0.0, 10.4, g.height(0.0, 0.4)), rng, "town_brass", g.height(0.0, 0.4) - 3.5, "warm", 8)
    tp.framed(interior, V(-cix + 0.006, 9.4, 2.4), V(1.0, 0.0, 0.0), 0.36, 0.46, tp.pr("portrait_a"), rng, "town_brass")
    tp.candlestick(clutter, V(0.9, 10.6, chancel_floor), rng)
    tp.papers(parts["debris"], -2.0, 2.0, 8.6, 10.6, chancel_floor, 3, rng, ("music", "letter"))
    tk.chips(parts["debris"], "plaster_interior", -2.6, 2.6, 8.6, 12.2, chancel_floor, 8, rng)


def vestry_furniture(b, parts, rng, g):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.wardrobe_light(b, furniture, clutter, V(vix[1] - 0.3, 8.95, chancel_floor), -math.pi * 0.5, rng, 1.0, 0.56, oak, oak)
    tp.chest_light(b, furniture, V(4.3, viy[0] + 0.24, chancel_floor), math.pi, rng, 0.8, 0.44, 0.75, oak, 3)
    b.loot("box", V(4.3, viy[0] + 0.24, chancel_floor + 0.8))
    tp.table_light(furniture, 4.65, 9.45, chancel_floor, 0.8, 0.5, 0.74, rng)
    tk.col(b, "wood", "table", 4.25, 5.05, 9.2, 9.7, chancel_floor, chancel_floor + 0.74)
    tp.chair_light(furniture, V(4.05, 9.55, chancel_floor), -math.pi * 0.5 - 0.2, rng)
    tp.book_row(clutter, V(4.4, 9.35, chancel_floor + 0.74), V(1.0, 0.0, 0.0), 0.4, rng, (0.2, 0.26), (0.03, 0.05), False, 1.0)
    tp.papers(clutter, 4.3, 5.0, 9.25, 9.65, chancel_floor + 0.745, 3, rng, ("letter", "notice", "envelope"))
    bd.coat_rail(interior, clutter, V(vix[0], 10.85, 1.95), V(vix[0], 11.05, 1.95), V(1.0, 0.0, 0.0), rng, 1)
    tp.framed(interior, V(4.0, viy[0] + 0.02, 2.0), V(0.0, 1.0, 0.0), 0.36, 0.46, tp.pr("portrait_b"), rng, oak, 0.03)
    tk.pendant(b, interior, V(4.55, 10.0, g.height(4.55, 0.1)), rng, "glass_dirty", g.height(4.55, 0.1) - 2.7, "warm", 8)
    tp.papers(parts["debris"], 3.8, 5.3, 9.8, 11.0, chancel_floor, 3, rng, ("letter", "envelope"))


def exterior(b, parts, rng, nave_g, chancel_g, vestry_g):
    roof = parts["roof"]
    plants = parts["plants"]
    tk.ygable_roof(b, parts, nave_g, rng, (-1.0, 1.0), 0.4, 0.012, roof_holes, 0.03, 0.33, 0.7, 0.48, True, (True, True), "rock", True)
    tk.ygable_roof(b, parts, chancel_g, rng, (-1.0, 1.0), 0.4, 0.01, (), 0.03, 0.33, 0.7, 0.48, True, (False, True), "rock", True)
    tk.ygable_roof(b, parts, vestry_g, rng, (-1.0,), 0.3, 0.01, (), 0.02, 0.3, 0.64, 0.44, False, (False, True), "rock", True)
    gutter_z = nave_g.eave_top - 0.11
    for sx in (-1.0, 1.0):
        x_gutter = sx * (nave_g.edge - 0.02 + 0.06)
        for y in (nave_y[0] + 0.5, nave_y[1] - 1.2):
            rod(roof, "rusty_metal", V(x_gutter, y, gutter_z), V(sx * (nave_x + 0.06), y, gutter_z - 0.45), 0.035, 6)
            rod(roof, "rusty_metal", V(sx * (nave_x + 0.06), y, gutter_z - 0.45), V(sx * (nave_x + 0.06), y, -0.1), 0.035, 6)
            z = gutter_z - 1.2
            while z > 0.4:
                lo, hi = kit.box_between(V(sx * nave_x, y - 0.04, z), V(sx * (nave_x + 0.1), y + 0.04, z + 0.03))
                block(roof, "rusty_metal", lo, hi)
                z -= 1.7
    tk.ivy_light(plants, V(-1.6, tower_y[0] - 0.02, -0.15), V(0.0, -1.0, 0.0), rng, 7.5, 1.2, 4, 10.0)
    tk.ivy_light(plants, V(-nave_x - 0.02, 4.2, -0.15), V(-1.0, 0.0, 0.0), rng, 4.5, 1.0, 3, 10.0)
    tk.ivy_light(plants, V(tower_x + 0.02, -8.0, -0.15), V(1.0, 0.0, 0.0), rng, 5.0, 0.8, 3, 10.0)
    tk.weeds_line(plants, V(-tower_x + 0.4, tower_y[0] - 0.15, -0.15), V(west_door[0] - 0.3, tower_y[0] - 0.15, -0.15), rng, 3)
    tk.weeds_line(plants, V(west_door[1] + 0.3, tower_y[0] - 0.15, -0.15), V(tower_x - 0.4, tower_y[0] - 0.15, -0.15), rng, 3)
    for sx in (-1.0, 1.0):
        tk.weeds_line(plants, V(sx * (nave_x + 0.15), nave_y[0] + 0.5, -0.15), V(sx * (nave_x + 0.15), nave_y[1] - 0.5, -0.15), rng, 6)
        tk.weeds_line(plants, V(sx * (tower_x + 0.15), tower_y[0] + 1.0, -0.15), V(sx * (tower_x + 0.15), tower_y[1] - 0.2, -0.15), rng, 2)
    tk.weeds_line(plants, V(-chancel_x + 0.3, chancel_y[1] + 0.15, -0.15), V(chancel_x - 0.3, chancel_y[1] + 0.15, -0.15), rng, 3)
    tk.chips(parts["debris"], "slate_roof", -6.4, -6.05, -5.0, 7.5, -0.15, 6, rng, (0.08, 0.17), (0.006, 0.008))
    tk.chips(parts["debris"], "slate_roof", 6.05, 6.4, -5.0, 7.5, -0.15, 6, rng, (0.08, 0.17), (0.006, 0.008))
    tp.papers(parts["debris"], -1.5, 1.5, -14.2, -13.4, -0.15, 4, rng, ("notice", "newspaper", "card"))


def church():
    b = kit.Build("church", 1401)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    west = tower_walls(b, parts, rng)
    west_doors(b, parts, rng, west)
    tower_inside(b, parts, rng)
    bell_frame(b, parts, rng)
    tower_rooms(b, parts, rng)
    nave_g, wall_top, nave_east = nave_walls(b, parts, rng)
    trusses(parts, nave_g, wall_top)
    chancel_g, chancel_top, chancel_right = chancel_walls(b, parts, rng)
    vestry_g = vestry_walls(b, parts, rng, nave_east, chancel_right)
    floors(b, parts, rng)
    nave_furniture(b, parts, rng, nave_g)
    chancel_furniture(b, parts, rng, chancel_g, chancel_top)
    vestry_furniture(b, parts, rng, vestry_g)
    exterior(b, parts, rng, nave_g, chancel_g, vestry_g)
    return b


def church_far():
    b = kit.Build("church_far", 1402)
    shell = b.part("shell", 30.0)
    nave_g = nave_gable()
    chancel_g = chancel_gable()
    vestry_g = vestry_gable()
    west = kit.plane(V(0.0, tower_y[0], 0.0), V(0.0, -1.0, 0.0))
    east = kit.plane(V(0.0, tower_y[1], 0.0), V(0.0, 1.0, 0.0))
    left = kit.plane(V(-tower_x, 0.0, 0.0), V(-1.0, 0.0, 0.0))
    right = kit.plane(V(tower_x, 0.0, 0.0), V(1.0, 0.0, 0.0))
    for frame, a0, a1 in ((west, -tower_x, tower_x), (east, -tower_x, tower_x), (left, -tiy[1], -tiy[0]), (right, tiy[0], tiy[1])):
        kit.wall(shell, stone, frame, kit.rect(a0, a1, -1.5, tower_top + 0.6), [], tower_t)
    for frame, shape in ((west, west_door), (west, west_window), (west, (-0.5, 0.5) + belfry_light), (east, (-0.5, 0.5) + belfry_light), (left, (9.3, 10.3) + belfry_light), (right, (-10.3, -9.3) + belfry_light)):
        kit.skin(shell, "soot", frame, tk.lancet(*shape), [], 0.004, 0.001, False)
    tp.disc(shell, "town_print", V(0.0, tower_y[0] - 0.01, 10.7), V(0.0, -1.0, 0.0), 0.68, tp.pr("clock", 2.0), 12)
    block(shell, "concrete", V(-tix, tiy[0], tower_roof - 0.1), V(tix, tiy[1], tower_roof), 0.0, "world")
    for cx in (-tower_x + 0.25, tower_x - 0.25):
        for cy in (tower_y[0] + 0.25, tower_y[1] - 0.25):
            emit(shell, kit.geo_frustum(0.27, 0.27, 0.0, 0.0, 1.4), dressed, kit.Matrix.Translation(V(cx, cy, tower_top + 0.6)), "box")
    wall_top = nave_g.height(nave_x, 0.03)
    for sign in (-1.0, 1.0):
        frame = kit.plane(V(sign * nave_x, 0.0, 0.0), V(sign, 0.0, 0.0))
        a_low, a_high = nave_y if sign > 0 else (-nave_y[1], -nave_y[0])
        kit.wall(shell, stone, frame, kit.rect(a_low, a_high, -1.5, wall_top), [], nave_t)
        for y in nave_windows:
            kit.skin(shell, "glass_dirty", frame, tk.lancet(sign * y - 0.5, sign * y + 0.5, *lancet_z), [], 0.004, 0.001, False)
    for y, normal in ((nave_y[0], -1.0), (nave_y[1], 1.0)):
        kit.wall(shell, stone, kit.plane(V(0.0, y, 0.0), V(0.0, normal, 0.0)), gable_outline(nave_g, nix, nave_x, wall_top), [], nave_t)
    top = chancel_g.height(chancel_x, 0.03)
    for sign in (-1.0, 1.0):
        frame = kit.plane(V(sign * chancel_x, 0.0, 0.0), V(sign, 0.0, 0.0))
        a_low, a_high = chancel_y if sign > 0 else (-chancel_y[1], -chancel_y[0])
        kit.wall(shell, stone, frame, kit.rect(a_low, a_high, -1.5, top), [], chancel_t)
    chancel_east = kit.plane(V(0.0, chancel_y[1], 0.0), V(0.0, 1.0, 0.0))
    kit.wall(shell, stone, chancel_east, gable_outline(chancel_g, cix, chancel_x, top), [], chancel_t)
    kit.skin(shell, "glass_dirty", chancel_east, tk.lancet(*east_window), [], 0.004, 0.001, False)
    vtop = vestry_g.height(vestry_x[1], 0.03)
    kit.wall(shell, stone, kit.plane(V(vestry_x[1], 0.0, 0.0), V(1.0, 0.0, 0.0)), kit.rect(vestry_y[0], vestry_y[1], -1.5, vtop), [], vestry_t)
    kit.wall(shell, stone, kit.plane(V(0.0, vestry_y[1], 0.0), V(0.0, 1.0, 0.0)), [(-vix[1], -1.5), (-vix[0], -1.5), (-vix[0], vestry_g.height(vix[0], 0.06)), (-vix[1], vestry_g.height(vix[1], 0.06))], [], vestry_t)
    for gable, sides, name in ((nave_g, (-1.0, 1.0), "slate_roof"), (chancel_g, (-1.0, 1.0), "slate_roof"), (vestry_g, (-1.0,), "slate_roof")):
        for side in sides:
            tk.roof_slab_y(shell, gable, side, gable.x0, gable.x1, name if side < 0 else "roof_moss", 0.15)
    for gable in (nave_g, chancel_g):
        block(shell, "terracotta", V(gable.origin_x - 0.13, gable.x0, gable.ridge_top - 0.04), V(gable.origin_x + 0.13, gable.x1, gable.ridge_top + 0.09))
    return b
