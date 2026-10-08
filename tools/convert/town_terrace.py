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
hx = 2.75
hy = 4.5
ix = 2.5
front_t = 0.4
back_t = 0.35
party_t = 0.25
fy = -hy + front_t
by = hy - back_t
c1 = 2.85
f1 = 3.1
c2 = 5.65
door = (0.9, 2.05, 0.0, 2.65)
door_top = 2.22
bay_open = (-2.15, -0.05, 0.0, 2.6)
bay_outer = [V(-2.15, -hy, 0.0), V(-1.6, -5.05, 0.0), V(-0.6, -5.05, 0.0), V(-0.05, -hy, 0.0)]
front_upper = [(-1.65, -0.55, 3.85, 5.35), (1.0, 1.9, 3.9, 5.3)]
back_door = (-2.45, -1.3, 0.0, 2.22)
back_windows = [(0.05, 1.25, 1.0, 2.3), (0.5, 1.6, 3.9, 5.3), (-2.0, -1.35, 4.15, 5.15)]
stair_x = (1.5, 2.5)
stair_foot = -2.9
stair_run = 3.4
well = (1.5, 2.5, -2.0, 0.5)
spine = (0.5, 0.62)
yard_end = 7.4
gate = (-2.4, -1.1)
paint = "painted_wood_white"
door_paint = "painted_wood_bauxite"
render = "render_pink"
stone = "granite_rubble"
dressed = "granite_ashlar"


def gable_of():
    return kit.Gable(-hx, hx, hy, 0.3, 5.79, 33.0)


def intersect(p, d, q, e):
    denom = d.x * e.y - d.y * e.x
    s = ((q.x - p.x) * e.y - (q.y - p.y) * e.x) / denom
    return p + d * s


def bay_inner(points, t):
    lines = []
    for index in range(len(points) - 1):
        d = (points[index + 1] - points[index]).normalized()
        lines.append((points[index] + V(-d.y, d.x, 0.0) * t, d))
    wall_point = V(0.0, -hy, 0.0)
    wall_dir = V(1.0, 0.0, 0.0)
    inner = [intersect(lines[0][0], lines[0][1], wall_point, wall_dir)]
    for index in range(len(lines) - 1):
        inner.append(intersect(lines[index][0], lines[index][1], lines[index + 1][0], lines[index + 1][1]))
    inner.append(intersect(lines[-1][0], lines[-1][1], wall_point, wall_dir))
    return inner


def bay_outset(points, t):
    return bay_inner(points, -t)


def prism(part, name, polygon, z0, z1, mapping="world"):
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), [(p.x, p.y) for p in polygon], [], z0, z1)
    emit(part, geo, name, None, mapping)


def ring(outer, inner):
    return list(outer) + list(reversed(inner))


def bay(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    roof = parts["roof"]
    interior = parts["interior"]
    clutter = parts["clutter"]
    inner = bay_inner(bay_outer, 0.18)
    prism(shell, dressed, bay_outer, -1.5, 0.0)
    prism(shell, dressed, ring(bay_outer, inner), 0.0, 0.72)
    prism(shell, dressed, ring(bay_outset(bay_outer, 0.05), bay_inner(bay_outer, 0.2)), 0.72, 0.8)
    prism(joinery, paint, ring(bay_outset(bay_outer, 0.01), bay_inner(bay_outer, 0.12)), 2.4, 2.62)
    prism(joinery, paint, ring(bay_outset(bay_outer, 0.07), bay_inner(bay_outer, 0.05)), 2.62, 2.7)
    prism(interior, "plaster_interior", inner, 2.56, 2.6)
    for index in range(3):
        p0 = bay_outer[index]
        p1 = bay_outer[index + 1]
        d = (p1 - p0).normalized()
        n = V(d.y, -d.x, 0.0)
        frame = kit.plane((p0 + p1) * 0.5, n)
        half = (p1 - p0).length * 0.5
        tk.sash_light(joinery, paint, frame, -half + 0.06, half - 0.06, 0.8, 2.4, 0.03, rng, 0.0 if index != 1 else 0.22, 0.4 if index != 1 else 0.15, 0.3, 2 if index != 1 else 3, 2)
        tk.slanted_cols(b, "rock", "bay", p0 - n * 0.09, p1 - n * 0.09, 0.18, -1.5, 0.8, 1 if index == 1 else 3)
        tk.slanted_cols(b, "glass", "bay", p0 - n * 0.09, p1 - n * 0.09, 0.18, 0.8, 2.7, 1 if index == 1 else 3)
        rail_a = (p0 + p1) * 0.5 - d * (half - 0.15) - n * 0.22 + V(0.0, 0.0, 2.3)
        rail_b = (p0 + p1) * 0.5 + d * (half - 0.15) - n * 0.22 + V(0.0, 0.0, 2.3)
        tp.curtain_light(clutter, rail_a, rail_b, rng.uniform(1.0, 1.45), rng, "fabric_worn", 0.45 if index != 1 else 0.3)
    for corner in bay_outer:
        kit.member(joinery, paint, corner + V(0.0, 0.03, 0.8), corner + V(0.0, 0.03, 2.4), 0.11, 0.11, V(1.0, 0.0, 0.0), 0.006, "box")
    z_top = 3.0
    w1 = V(bay_outer[1].x, -hy + 0.02, z_top)
    w2 = V(bay_outer[2].x, -hy + 0.02, z_top)
    outer_raised = [p + V(0.0, 0.0, 2.7) for p in bay_outset(bay_outer, 0.09)]
    for facet in ([outer_raised[1], outer_raised[2], w2, w1], [outer_raised[0], outer_raised[1], w1], [outer_raised[2], outer_raised[3], w2]):
        emit(roof, kit.Geo(facet, [kit.orient(tuple(range(len(facet))), facet, up)]), "slate_roof", None, "world")
        under = [p - V(0.0, 0.0, 0.04) for p in facet]
        emit(roof, kit.Geo(under, [kit.orient(tuple(range(len(under))), under, -up)]), "timber_planks_weathered", None, "world")
    kit.member(roof, "rusty_metal", V(bay_outer[0].x - 0.1, -hy - 0.03, z_top - 0.02), V(bay_outer[3].x + 0.1, -hy - 0.03, z_top - 0.02), 0.06, 0.05, up, 0.0, "box")
    tk.col(b, "rock", "bay_roof", bay_outer[0].x - 0.08, bay_outer[3].x + 0.08, -5.15, -hy, 2.7, z_top + 0.05)
    tk.col(b, "wood", "bay_floor", bay_open[0], bay_open[1], -5.05, fy, -0.3, 0.0)


def doorcase(b, parts, front, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    a0, a1, z0, z1 = door
    for edge, sign in ((a0, -1.0), (a1, 1.0)):
        frame_block(shell, "render_white", front, edge + sign * 0.04, edge + sign * 0.2, -0.05, 2.75, -0.05, 0.0, 0.006)
        frame_block(shell, "render_white", front, edge + sign * 0.03, edge + sign * 0.21, 2.75, 3.02, -0.14, 0.0, 0.01)
        frame_block(shell, dressed, front, edge + sign * 0.02, edge + sign * 0.22, -0.4, -0.05, -0.08, 0.0, 0.008)
        frame_block(joinery, paint, front, min(edge, edge - sign * 0.06), max(edge, edge - sign * 0.06), door_top, z1, 0.0, front_t, 0.003, "board")
    frame_block(shell, "render_white", front, a0 - 0.28, a1 + 0.28, 3.02, 3.12, -0.2, 0.0, 0.012)
    frame_block(shell, "render_white", front, a0 - 0.22, a1 + 0.22, 2.7, 2.78, -0.08, 0.0, 0.006)
    frame_block(joinery, paint, front, a0, a1, door_top, door_top + 0.07, 0.05, 0.16, 0.004, "board")
    frame_block(joinery, paint, front, a0, a1, z1 - 0.05, z1, 0.05, 0.16, 0.004, "board")
    matrix = kit.frame_matrix(front)
    bars = 4
    for index in range(bars):
        p0 = a0 + 0.06 + (a1 - a0 - 0.12) * index / bars
        p1 = a0 + 0.06 + (a1 - a0 - 0.12) * (index + 1) / bars
        kit.pane(joinery, matrix, p0 + 0.01, p1 - 0.01, door_top + 0.08, z1 - 0.06, 0.1, rng.choice(["whole", "whole", "shard", "missing"]), rng)
        if index:
            frame_block(joinery, paint, front, p0 - 0.012, p0 + 0.012, door_top + 0.07, z1 - 0.05, 0.08, 0.14)
    tk.opening_block(b, "glass", "fanlight", front, (a0, a1, door_top, z1), front_t)
    block(shell, dressed, V(a0 - 0.12, -hy - 0.38, -0.45), V(a1 + 0.12, -hy + 0.02, -0.04), 0.015)
    tk.col(b, "rock", "step", a0 - 0.12, a1 + 0.12, -hy - 0.38, -hy, -1.5, -0.04)
    tk.col(b, "rock", "threshold", a0, a1, -hy, fy, -1.5, 0.0)
    block(shell, dressed, V(a0, -hy, -0.08), V(a1, fy + 0.05, 0.0), 0.004)
    scraper = V(a1 + 0.3, -hy - 0.12, -0.04)
    for dx in (-0.1, 0.1):
        rod(joinery, "rusty_metal", scraper + V(dx, 0.0, 0.0), scraper + V(dx, 0.0, 0.18), 0.008, 5)
    local_block(joinery, "rusty_metal", kit.Matrix.Translation(scraper), -0.1, 0.1, -0.006, 0.006, 0.12, 0.16)
    tk.door_unit(joinery, front, a0, a1, 0.0, door_top, front_t, door_paint, rng, "high", 100.0, "panel", True, 0.0, 0.06, 0.0, paint)


def plinth(shell, frame, a_low, a_high, gaps, rng, top=0.42):
    edges = [a_low]
    for g0, g1 in sorted(gaps):
        edges += [g0, g1]
    edges.append(a_high)
    for s0, s1 in zip(edges[0::2], edges[1::2]):
        count = max(1, int(round((s1 - s0) / 0.55)))
        for index in range(count):
            a = s0 + (s1 - s0) * index / count
            c = s0 + (s1 - s0) * (index + 1) / count
            frame_block(shell, dressed, frame, a + 0.006, c - 0.006, -0.5, top + rng.uniform(-0.02, 0.02), -0.035, 0.0, 0.012)


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    front_holes = [kit.rect(door[0], door[1], -0.05, door[3]), kit.rect(bay_open[0], bay_open[1], -0.02, bay_open[3])] + [kit.rect(*w) for w in front_upper]
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), front_holes, front_t)
    back_holes = [kit.rect(back_door[0], back_door[1], -0.05, back_door[3])] + [kit.rect(*w) for w in back_windows]
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), back_holes, back_t)
    for frame in (left, right):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
        kit.wall(shell, stone, frame, outline, [], party_t)
    front_open = [door, bay_open] + front_upper
    back_open = [back_door] + back_windows
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, -1.5, wall_top, front_t, front_open)
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, -1.5, wall_top, back_t, back_open)
    kit.wall_boxes(b, "rock", "party", left, -hy, hy, -1.5, wall_top, party_t, [])
    kit.wall_boxes(b, "rock", "party", right, -hy, hy, -1.5, wall_top, party_t, [])
    bd.gable_cols(b, "party_gable", -hx, -ix, gable, wall_top, 0.0)
    bd.gable_cols(b, "party_gable", ix, hx, gable, wall_top, 0.0)
    wide_front = kit.facade("front", hx, hy)
    tk.render_skin(shell, wide_front, -hx, hx, wall_top - 0.02, front_open, rng, 6, render, 0.02, 2, (0.42, 0.55), 0.0)
    plinth(shell, wide_front, -hx, hx, [(door[0] - 0.24, door[1] + 0.24), (bay_open[0] - 0.02, bay_open[1] + 0.02)], rng)
    frame_block(shell, "render_white", wide_front, -hx, hx, 2.98, 3.1, -0.035, 0.0, 0.006)
    frame_block(shell, "render_white", wide_front, -hx, hx, wall_top - 0.32, wall_top - 0.18, -0.06, 0.0, 0.006)
    frame_block(shell, "render_white", wide_front, -hx, hx, wall_top - 0.18, wall_top - 0.02, -0.03, 0.0, 0.004)
    for w in front_upper:
        tk.architrave(shell, front, w, "render_white", 0.1, 0.025, 0.14, True)
    wide_back = kit.facade("back", hx, hy)
    tk.render_skin(shell, wide_back, -hx, hx, wall_top - 0.25, back_open, rng, 7, "render_white", 0.018, 2, (0.4, 0.8), 0.6)
    bd.damp_band(shell, wide_back, -hx, hx, rng, 0.35, 1.1, "granite_rubble_damp", -0.2, 0.003, [(back_door[0] - 0.05, back_door[1] + 0.05)])
    return wall_top


def front_windows(b, parts, rng):
    front = kit.facade("front", ix, hy)
    tk.sash(b, parts, front, front_upper[0], front_t, rng, paint, 0.1, 0.25, 0.4, 0.3, 2, 2, render, dressed)
    tk.sash(b, parts, front, front_upper[1], front_t, rng, paint, 0.1, 0.0, 0.2, 0.4, 2, 2, render, dressed, None, False, True)


def back_openings(b, parts, rng):
    back = kit.facade("back", ix, hy)
    joinery = parts["joinery"]
    tk.sash(b, parts, back, back_windows[0], back_t, rng, paint, 0.08, 0.0, 0.05, 0.45, 2, 2, "render_white", dressed)
    tk.sash(b, parts, back, back_windows[1], back_t, rng, paint, 0.08, 0.15, 0.4, 0.3, 2, 2, "render_white", dressed)
    tk.casement(b, parts, back, back_windows[2], back_t, rng, paint, 0.08, [0.0], 0.6, 0.2, 2, dressed)
    a0, a1, z0, z1 = back_door
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, back_t, "painted_wood_green", rng, "low", 96.0, "ledged", True, 0.0, 0.06, 3.0, paint)
    block(parts["shell"], dressed, V(-a1 - 0.08, hy - 0.04, -0.3), V(-a0 + 0.08, hy + 0.34, -0.06), 0.012)
    tk.col(b, "rock", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
    tk.col(b, "rock", "step", -a1 - 0.08, -a0 + 0.08, hy, hy + 0.34, -0.6, -0.06)


def floors_and_walls(b, parts, rng):
    floors = parts["floors"]
    interior = parts["interior"]
    joinery = parts["joinery"]
    tk.tile_floor(floors, "town_tiles", 0.4, ix, fy, spine[1], 0.0)
    tk.board_floor(floors, -ix, 0.3, fy, spine[0], 0.0, rng, "y")
    tk.board_floor(floors, -2.1, -0.1, -5.0, fy, 0.0, rng, "y", (), "floorboards", 0.02, 0.0)
    block(floors, "timber_beam", V(0.3, -3.37, -0.02), V(0.4, -2.22, 0.005), 0.003)
    tk.tile_floor(floors, "town_quarry", -ix, ix, spine[1], by, 0.0)
    tk.col(b, "wood", "ground", -ix, ix, fy, by, -0.3, 0.0)
    tk.board_floor(floors, -ix, 0.3, fy, by, f1, rng, "y", (), "floorboards", 0.04, 0.0)
    tk.board_floor(floors, 0.4, ix, fy, 1.5, f1, rng, "x", [well])
    tk.tile_floor(floors, "town_lino", 0.4, ix, 1.5, by, f1, 0.02)
    block(floors, "floorboards", V(0.3, -1.65, f1 - 0.02), V(0.4, -0.5, f1), 0.0, "board")
    block(floors, "floorboards", V(0.3, 0.38, f1 - 0.02), V(0.4, 1.5, f1), 0.0, "board")
    tk.floor_cols(b, "wood", "upper", -ix, ix, fy, by, c1, f1, [well])
    tk.col(b, "wood", "attic", -ix, ix, fy, by, c2, c2 + 0.25)
    block(floors, paint, V(well[0] - 0.03, well[2], c1 - 0.01), V(well[0], well[3], f1 + 0.012), 0.002, "board")
    block(floors, paint, V(well[0], well[2] - 0.03, c1 - 0.01), V(well[1], well[2], f1 + 0.012), 0.002, "board")
    hall_frame = kit.plane(V(0.4, 0.0, 0.0), V(1.0, 0.0, 0.0))
    parlour_door = (-3.37, -2.22, 0.0, 2.22)
    kit.wall(interior, "plaster_interior", hall_frame, kit.notched(fy, spine[0], 0.0, c1, [(parlour_door[0], parlour_door[1], parlour_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "partition", hall_frame, fy, spine[0], 0.0, c1, 0.1, [parlour_door])
    tk.door_unit(joinery, hall_frame, parlour_door[0], parlour_door[1], 0.0, parlour_door[3], 0.1, paint, rng, "low", 92.0, "panel")
    spine_frame = kit.plane(V(0.0, spine[1], 0.0), V(0.0, 1.0, 0.0))
    kitchen_door = (-1.5, -0.41, 0.0, 2.2)
    kit.wall(interior, "plaster_interior", spine_frame, kit.notched(-ix, ix, 0.0, c1, [(kitchen_door[0], kitchen_door[1], kitchen_door[3])]), [], spine[1] - spine[0])
    kit.wall_boxes(b, "wood", "spine", spine_frame, -ix, ix, 0.0, c1, spine[1] - spine[0], [kitchen_door])
    tk.door_unit(joinery, spine_frame, kitchen_door[0], kitchen_door[1], 0.0, kitchen_door[3], spine[1] - spine[0], paint, rng, "low", -98.0, "panel", True, 0.0, 0.04)
    stair_wall = kit.plane(V(stair_x[0], 0.0, 0.0), V(-1.0, 0.0, 0.0))
    kit.wall(interior, "plaster_interior", stair_wall, kit.rect(-spine[0], 0.9, 0.0, c1), [], 0.05)
    tk.col(b, "wood", "stair_wall", stair_x[0], stair_x[0] + 0.05, -0.9, spine[0], 0.0, c1)
    tk.under_stair_panel(joinery, stair_x[0], stair_foot, 0.0, 2.0, 2.0 * f1 / stair_run, 1.0, rng, paint, (-1.65, -1.05, 0.88))
    tk.stair_flight(b, parts, stair_x[0], stair_x[1], stair_foot, 0.0, stair_run, f1, 14, rng, 1.0, "floorboards", paint, "town_carpet", "town_brass")
    top = (-0.95 - stair_foot) / stair_run * f1
    bd.balustrade(b, joinery, V(stair_x[0] + 0.03, stair_foot + 0.05, 0.02), V(stair_x[0] + 0.03, -0.95, top + 0.02), rng, 0.86, 0.13, "timber_beam", paint, 0.12, (True, False), False)
    block(joinery, "timber_beam", V(stair_x[0] - 0.02, -1.0, 0.0), V(stair_x[0] + 0.08, -0.9, c1), 0.006)
    upper = kit.plane(V(0.4, 0.0, 0.0), V(1.0, 0.0, 0.0))
    front_bed_door = (-1.65, -0.5, f1, f1 + 2.2)
    back_bed_door = (0.38, 1.5, f1, f1 + 2.2)
    kit.wall(interior, "plaster_interior", upper, kit.notched(fy, by, f1, c2, [(front_bed_door[0], front_bed_door[1], front_bed_door[3]), (back_bed_door[0], back_bed_door[1], back_bed_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "partition_up", upper, fy, by, f1, c2, 0.1, [front_bed_door, back_bed_door])
    tk.door_unit(joinery, upper, front_bed_door[0], front_bed_door[1], f1, 2.2, 0.1, paint, rng, "high", 88.0, "panel")
    tk.door_unit(joinery, upper, back_bed_door[0], back_bed_door[1], f1, 2.2, 0.1, paint, rng, "high", 84.0, "panel", True, 0.0, 0.05)
    box_wall = kit.plane(V(0.0, -2.0, 0.0), V(0.0, 1.0, 0.0))
    box_door = (-1.49, -0.41, f1, f1 + 2.2)
    kit.wall(interior, "plaster_interior", box_wall, kit.notched(-ix, -0.4, f1, c2, [(box_door[0], box_door[1], box_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "box_wall", box_wall, -ix, -0.4, f1, c2, 0.1, [box_door])
    tk.door_unit(joinery, box_wall, box_door[0], box_door[1], f1, 2.2, 0.1, paint, rng, "high", 80.0, "panel", True, 0.0, 0.04)
    bath_wall = kit.plane(V(0.0, 1.52, 0.0), V(0.0, -1.0, 0.0))
    bath_door = (1.32, 2.47, f1, f1 + 2.2)
    kit.wall(interior, "plaster_interior", bath_wall, kit.notched(0.4, ix, f1, c2, [(bath_door[0], bath_door[1], bath_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "bath_wall", bath_wall, 0.4, ix, f1, c2, 0.1, [bath_door])
    tk.door_unit(joinery, bath_wall, bath_door[0], bath_door[1], f1, 2.2, 0.1, paint, rng, "high", 75.0, "panel")
    bed_wall = kit.plane(V(0.0, -0.35, 0.0), V(0.0, 1.0, 0.0))
    kit.wall(interior, "plaster_interior", bed_wall, kit.rect(-0.3, ix, f1, c2), [], 0.1)
    kit.wall_boxes(b, "wood", "bed_wall", bed_wall, -0.3, ix, f1, c2, 0.1, [])
    bd.balustrade(b, joinery, V(well[0] - 0.02, well[2], f1), V(well[0] - 0.02, well[3], f1), rng, 0.92, 0.12, "timber_beam", paint, 0.1, (False, True), True, "landing")
    return parlour_door, front_bed_door, back_bed_door, bath_door


def breasts(b, parts, rng):
    interior = parts["interior"]
    parlour = tk.chimney_breast(b, interior, -ix, 1.0, -2.6, -1.0, 0.0, c1, 0.75, 0.75, rng, depth=0.42)
    tk.fireplace_light(b, interior, V(parlour, -1.8, 0.0), V(1.0, 0.0, 0.0), rng, 1.3, paint, "kitchen_tiles", False)
    kitchen = tk.chimney_breast(b, interior, -ix, 1.0, 1.55, 3.25, 0.0, c1, 1.32, 1.4, rng, depth=0.55)
    bd.range_stove(b, interior, parts["clutter"], V(-ix + 0.06, 2.4, 0.0), 0.0, rng, 1.2, 0.48)
    block(interior, "timber_beam", V(kitchen - 0.02, 1.4, 1.62), V(kitchen + 0.2, 3.4, 1.68), 0.006)
    front_bed = tk.chimney_breast(b, interior, -ix, 1.0, -2.5, -1.1, f1, c2, 0.6, 0.66, rng, depth=0.36)
    tk.fireplace_light(b, interior, V(front_bed, -1.8, f1), V(1.0, 0.0, 0.0), rng, 1.0, paint, "kitchen_tiles", False, False)
    back_bed = tk.chimney_breast(b, interior, -ix, 1.0, 1.75, 3.05, f1, c2, 0.56, 0.6, rng, depth=0.32)
    tk.fireplace_light(b, interior, V(back_bed, 2.4, f1), V(1.0, 0.0, 0.0), rng, 0.95, "timber_beam", "kitchen_tiles", False, False)
    return parlour, kitchen, front_bed, back_bed


def finishes(parts, rng, doors, breast_faces):
    parlour_door, front_bed_door, back_bed_door, bath_door = doors
    parlour, kitchen, front_bed, back_bed = breast_faces
    interior = parts["interior"]
    stripe = ("paper", "town_stripe", 2, 1)
    floral = ("paper", "wallpaper_faded", 2, 1)
    plaster = ("plaster", 3)
    tiled = ("tiles", 1.2, "kitchen_tiles", plaster)
    dado = ("panel", 0.95, "painted_wood_green", stripe)
    kitchen_window = (-back_windows[0][1], -back_windows[0][0], back_windows[0][2], back_windows[0][3])
    bed_window = (-back_windows[1][1], -back_windows[1][0], back_windows[1][2], back_windows[1][3])
    bath_window = (-back_windows[2][1], -back_windows[2][0], back_windows[2][2], back_windows[2][3])
    back_door_world = (-back_door[1], -back_door[0], 0.0, back_door[3])
    upper_doors = [(front_bed_door[0], front_bed_door[1], f1, front_bed_door[3]), (back_bed_door[0], back_bed_door[1], f1, back_bed_door[3])]
    box_door_world = (0.41, 1.49, f1, f1 + 2.2)
    bath_door_world = (bath_door[0], bath_door[1], f1, bath_door[3])
    kitchen_door_world = (0.41, 1.5, 0.0, 2.2)
    tk.room(parts, rng, 0.4, ix, fy, spine[0], 0.0, c1, {"front": dado, "left": dado, "right": dado, "back": dado}, {"front": [door], "left": [parlour_door], "back": [kitchen_door_world]}, paint, 2.3, True, 2, [well], None, 10)
    tk.room(parts, rng, -ix, 0.3, fy, spine[0], 0.0, c1, {"front": floral, "left": floral, "right": floral, "back": floral}, {"front": [bay_open], "right": [parlour_door]}, paint, 2.3, True, 3, (), {"left": [(-2.6, -1.0, 0.0, c1)]}, 16)
    tk.wall_finish(interior, "left", ("paper", "wallpaper_faded", 1, 1), parlour, 0.0, -2.6, -1.0, 0.0, c1, [(-2.47, -1.13, 0.0, 1.2)], rng)
    tk.room(parts, rng, -ix, ix, spine[1], by, 0.0, c1, {"front": plaster, "left": plaster, "right": tiled, "back": ("tiles", 1.35, "kitchen_tiles", plaster)}, {"front": [kitchen_door_world], "back": [kitchen_window, back_door_world]}, "painted_wood_green", None, True, 3, [(-1.2, -0.4, 2.8, 3.6)], {"left": [(1.55, 3.25, 0.0, c1)]}, 18)
    tk.wall_finish(interior, "left", ("tiles", 1.4, "kitchen_tiles", ("plaster", 1)), kitchen, 0.0, 1.55, 3.25, 0.0, c1, [(1.74, 3.06, 0.0, 1.4)], rng)
    tk.room(parts, rng, -ix, 0.3, fy, -0.45, f1, c2, {"front": stripe, "left": stripe, "right": stripe, "back": stripe}, {"front": [front_upper[0]], "right": [upper_doors[0]]}, paint, f1 + 2.1, True, 2, (), {"left": [(-2.5, -1.1, f1, c2)]}, 12)
    tk.wall_finish(interior, "left", stripe, front_bed, 0.0, -2.5, -1.1, f1, c2, [(-2.32, -1.28, f1, f1 + 1.2)], rng)
    tk.room(parts, rng, -ix, 0.3, -0.35, by, f1, c2, {"front": floral, "left": floral, "right": floral, "back": floral}, {"back": [bed_window], "right": [upper_doors[1]]}, paint, f1 + 2.1, True, 2, [(-2.1, -1.4, 2.2, 3.1)], {"left": [(1.75, 3.05, f1, c2)]}, 12)
    tk.wall_finish(interior, "left", floral, back_bed, 0.0, 1.75, 3.05, f1, c2, [(1.9, 2.9, f1, f1 + 1.2)], rng)
    tk.room(parts, rng, 0.4, ix, fy, -2.1, f1, c2, {"front": plaster, "left": plaster, "right": plaster, "back": plaster}, {"front": [front_upper[1]], "back": [box_door_world]}, paint, None, True, 2, (), None, 10)
    tk.room(parts, rng, 0.4, ix, -2.0, 1.52, f1, c2, {"front": stripe, "left": stripe, "right": stripe, "back": stripe}, {"front": [box_door_world], "left": upper_doors, "back": [bath_door_world]}, paint, f1 + 2.1, True, 1, (), None, 6)
    tk.wall_finish(interior, "right", stripe, 0.4, ix, well[2], well[3], c1 - 0.02, f1 + 0.02, [], rng)
    tk.room(parts, rng, 0.4, ix, 1.62, by, f1, c2, {"front": tiled, "left": tiled, "right": tiled, "back": tiled}, {"front": [bath_door_world], "back": [bath_window]}, None, None, True, 2, (), None, 8)


def hall_room(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.hall_stand(b, furniture, clutter, V(ix - 0.035, -3.5, 0.0), -math.pi * 0.5, rng)
    tp.papers(parts["debris"], 0.6, 1.9, -4.05, -3.3, 0.0, 9, rng, ("envelope", "letter", "newspaper", "card"))
    block(clutter, "fabric_worn", V(1.0, -4.05, 0.0), V(1.85, -3.6, 0.012), 0.004)
    tp.wall_clock(interior, V(0.418, -3.75, 1.9), V(1.0, 0.0, 0.0), rng, 0.14)
    tp.framed(interior, V(0.41, -0.5, 1.65), V(1.0, 0.0, 0.0), 0.36, 0.3, tp.pr("harbour"), rng, "timber_beam", 0.1)
    tk.pendant(b, interior, V(1.0, -3.2, c1), rng, "glass_dirty", 0.55)
    tp.wall_sheet(interior, V(0.62, fy + 0.006, 1.55), V(0.0, 1.0, 0.0), "card", rng, 1.0, 0.05)
    tp.debris_field(parts, 0.45, 1.45, -2.9, 0.4, 0.0, rng, 10, 0, 2, 4)


def parlour_room(b, parts, rng, parlour):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    hearth = V(parlour + 0.3, -1.8, 0.0)
    tp.mantel_set(clutter, V(parlour + 0.06, -2.4, 1.16), V(0.0, 1.0, 0.0), V(1.0, 0.0, 0.0), 1.2, rng)
    tp.wall_mirror(interior, V(parlour + 0.005, -1.8, 1.75), V(1.0, 0.0, 0.0), 0.95, 0.75, rng, "town_brass", True)
    tp.fender(clutter, V(parlour + 0.42, -2.4, 0.02), V(parlour + 0.42, -1.2, 0.02), rng)
    tp.fire_irons(clutter, V(parlour + 0.15, -1.05, 0.02), rng)
    tp.coal_scuttle(clutter, V(parlour + 0.25, -2.75, 0.0), rng, True)
    chair_a = V(-1.3, -2.85, 0.0)
    chair_b = V(-1.4, -0.7, 0.0)
    tp.armchair_light(b, furniture, chair_a, tk.facing(chair_a, hearth), rng)
    tp.armchair_light(b, furniture, chair_b, tk.facing(chair_b, hearth), rng, "leather_brown")
    tp.sofa_light(b, furniture, V(-0.16, -1.15, 0.0), -math.pi * 0.5, rng, 1.55)
    bd.rug(clutter, V(-1.2, -1.8, 0.0), 1.8, 2.4, 0.04, rng, "town_carpet")
    tp.bookcase(b, furniture, clutter, V(-2.34, -3.45, 0.0), math.pi * 0.5, rng, 0.85, 1.75, 0.3)
    tp.table_light(furniture, -2.05, -0.3, 0.0, 0.5, 0.5, 0.62, rng)
    tk.col(b, "wood", "side_table", -2.3, -1.8, -0.55, -0.05, 0.0, 0.62)
    bd.oil_lamp(clutter, V(-2.05, -0.3, 0.62), rng)
    b.light("warm", V(-2.05, -0.3, 0.86))
    tp.sideboard(b, furniture, clutter, V(-0.95, spine[0] - 0.28, 0.0), 0.0, rng, 1.3)
    tp.wireless(clutter, V(-0.6, spine[0] - 0.3, 0.9), 0.0, rng)
    tp.vase(clutter, V(-1.05, spine[0] - 0.22, 0.9), rng)
    tp.birdcage(clutter, V(-1.38, spine[0] - 0.28, 0.9), rng)
    tp.label_bottle(clutter, V(-0.85, spine[0] - 0.4, 0.9), rng, "gin")
    tp.plant_stand(clutter, V(-1.1, -4.72, 0.0), rng)
    tp.framed(interior, V(-1.0, spine[0] - 0.006, 1.8), V(0.0, -1.0, 0.0), 0.72, 0.52, tp.pr("seascape"), rng, "town_brass")
    tp.framed(interior, V(0.294, -0.9, 1.65), V(-1.0, 0.0, 0.0), 0.5, 0.36, tp.pr("ship"), rng, "timber_beam", 0.03)
    tp.framed(interior, V(-ix + 0.006, -0.35, 1.72), V(1.0, 0.0, 0.0), 0.3, 0.4, tp.pr("portrait_a"), rng, "timber_beam", -0.06)
    tp.framed(interior, V(0.294, -3.65, 1.6), V(-1.0, 0.0, 0.0), 0.32, 0.42, tp.pr("portrait_b"), rng, "town_brass", 0.0)
    tp.chair_light(furniture, V(-0.9, -0.55, 0.0), 1.7, rng, fallen=True)
    tk.pendant(b, interior, V(-1.1, -1.8, c1), rng, "town_metal", 0.5)
    tp.papers(parts["debris"], -2.0, -0.4, -3.9, -0.6, 0.0, 5, rng)
    tp.book_row(parts["debris"], V(-1.95, -3.2, 0.0), V(0.4, -1.0, 0.0), 0.35, rng, flat_chance=1.0)
    tp.debris_field(parts, -1.95, -0.25, -4.95, -4.2, 0.0, rng, 6, 16, 0, 8)


def kitchen_room(b, parts, rng, kitchen):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    bd.belfast_sink(b, furniture, clutter, V(-0.65, by - 0.27, 0.0), 0.0, rng)
    tp.bucket_light(clutter, V(0.05, by - 0.3, 0.0), rng)
    tp.dresser_light(b, furniture, clutter, V(-0.9, spine[1] + 0.24, 0.0), math.pi, rng, "painted_wood_green", 1.35)
    b.loot("food", V(-0.9, spine[1] + 0.28, 0.9))
    table = V(0.75, 2.45, 0.0)
    tp.table_light(furniture, table.x, table.y, 0.0, 1.3, 0.85, 0.76, rng)
    tk.col(b, "wood", "table", 0.1, 1.4, 2.03, 2.87, 0.0, 0.76)
    for position in (V(0.4, 1.72, 0.0), V(1.1, 3.18, 0.0), V(1.7, 2.35, 0.0)):
        tp.chair_light(furniture, position, tk.facing(position, table) + rng.uniform(-0.25, 0.25), rng)
    tp.chair_light(furniture, V(-0.45, 2.95, 0.0), 2.4, rng, fallen=True)
    tp.plate_light(clutter, V(0.45, 2.3, 0.76), rng, 0.12, 0.0)
    tp.plate_light(clutter, V(1.0, 2.65, 0.76), rng, 0.11, 0.0)
    tp.cup_light(clutter, V(0.62, 2.72, 0.76), rng)
    tp.label_jar(clutter, V(1.15, 2.25, 0.76), rng, "jam")
    tp.label_bottle(clutter, V(0.8, 2.1, 0.76), rng, "ale", True)
    tp.label_can(clutter, V(0.3, 2.65, 0.76), rng, "beans", lying=True)
    b.loot("food", V(0.85, 2.5, 0.76))
    pantry = V(2.05, spine[1] + 0.3, 0.0)
    bd.cabinet(furniture, pantry, 0.85, 0.55, 0.0, 2.0, math.pi, rng, "timber_planks_weathered", "painted_wood_green", 2, 0, 0)
    for z in (0.75, 1.2, 1.6):
        local_block(furniture, "timber_planks_weathered", kit.turned(pantry, math.pi), -0.4, 0.4, -0.25, 0.25, z - 0.02, z)
        for index in range(4):
            if rng.random() < 0.75:
                tp.label_can(clutter, V(1.75 + index * 0.18 + rng.uniform(-0.02, 0.02), pantry.y + rng.uniform(-0.1, 0.1), z), rng, rng.choice(("peas", "beans", "peaches", "beef", "soup", "sardines", "milk", "cocoa")))
    tk.col(b, "wood", "pantry", 1.62, ix, spine[1], spine[1] + 0.6, 0.0, 2.0)
    for z in (1.45, 1.85):
        bd.shelf(interior, V(ix, 3.3, z), V(ix, 4.05, z), 0.24, V(-1.0, 0.0, 0.0), rng)
        y = 3.4
        while y < 3.95:
            if rng.random() < 0.45:
                tp.label_jar(clutter, V(ix - 0.12, y, z), rng, rng.choice(("jam", "marmalade", "pickles", "honey")))
            else:
                tp.label_can(clutter, V(ix - 0.12, y, z), rng, rng.choice(("peas", "soup", "cocoa", "milk")))
            y += rng.uniform(0.12, 0.2)
    tp.wall_clock(interior, V(ix - 0.013, 2.0, 2.0), V(-1.0, 0.0, 0.0), rng, 0.15)
    tp.airer(interior, clutter, V(-0.9, 2.4, 2.45), 0.1, 1.5, rng, c1)
    for y in (2.1, 2.7):
        bd.hanging_pot(clutter, V(kitchen + 0.12, y, 1.62), rng, 0.04)
    tp.label_jar(clutter, V(kitchen + 0.1, 1.6, 1.68), rng, "honey")
    tp.label_can(clutter, V(kitchen + 0.1, 3.2, 1.68), rng, "cocoa")
    tk.pendant(b, interior, V(0.75, 2.45, c1), rng, "town_metal", 0.6)
    tp.debris_field(parts, -1.6, 2.3, 0.75, 4.0, 0.0, rng, 18, 12, 2, 10)
    lump(parts["debris"], "dirt_debris", V(-0.8, 3.2, -0.01), (0.5, 0.35, 0.04), rng, 0.3, 2, 0.0)


def bedrooms(b, parts, rng, front_bed, back_bed):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    bd.iron_bed(b, furniture, clutter, V(-1.25, -1.5, f1), -math.pi * 0.5, rng, 1.95, 1.3)
    tp.sheet(clutter, V(-1.1, -1.9, f1 + 0.62), 0.5, 0.19, 0.28, tp.pr("letter"), rng, 0.2, 0.004, 0.02)
    bd.suitcase(clutter, V(-0.95, -2.15, f1 + 0.62), 0.3, rng, True)
    bd.suitcase(clutter, V(-0.2, -2.6, f1), 1.2, rng)
    tp.chamber_pot(clutter, V(-1.6, -1.1, f1), rng)
    tp.wardrobe_light(b, furniture, clutter, V(0.01, -3.45, f1), -math.pi * 0.5, rng, 1.0, 0.56)
    tp.washstand_light(b, furniture, clutter, V(-2.27, -3.45, f1), math.pi * 0.5, rng)
    tp.dressing_table(b, furniture, clutter, V(-1.1, fy + 0.24, f1), 0.0, rng)
    tp.chair_light(furniture, V(-0.45, -2.85, f1), 2.6, rng)
    bd.rug(clutter, V(-1.2, -2.6, f1), 1.2, 1.6, 0.0, rng, "fabric_tartan")
    tp.framed(interior, V(-1.2, -0.456, f1 + 1.6), V(0.0, -1.0, 0.0), 0.5, 0.36, tp.pr("harbour"), rng, "timber_beam", 0.05)
    tp.mantel_set(clutter, V(front_bed + 0.05, -2.2, f1 + 1.16), V(0.0, 1.0, 0.0), V(1.0, 0.0, 0.0), 0.8, rng, False)
    tk.pendant(b, interior, V(-1.1, -2.2, c2), rng, "town_metal", 0.45)
    tp.curtain_light(clutter, V(-1.75, fy + 0.08, f1 + 2.38), V(-0.45, fy + 0.08, f1 + 2.38), 1.5, rng, "fabric_tartan", 0.4)
    tp.papers(parts["debris"], -2.2, -0.3, -3.6, -0.7, f1, 4, rng, ("letter", "envelope", "newspaper"))
    bd.iron_bed(b, furniture, clutter, V(-0.6, 3.15, f1), -math.pi * 0.5, rng, 1.9, 0.95)
    tp.cot(b, furniture, clutter, V(-1.7, 0.4, f1), 0.0, rng)
    tp.chest_light(b, furniture, V(-0.3, -0.1, f1), math.pi, rng, 0.85, 0.44, 0.9, "timber_beam", 4)
    bd.sea_chest(b, furniture, V(-2.0, 3.65, f1), math.pi * 0.5, rng)
    b.loot("box", V(-2.0, 3.65, f1 + 0.5))
    tp.chair_light(furniture, V(-1.4, 1.5, f1), 0.9, rng, fallen=True)
    lump(clutter, "fabric_worn", V(-0.6, 2.55, f1 + 0.6), (0.11, 0.08, 0.12), rng, 0.3, 1)
    tp.bucket_light(clutter, V(-1.75, 2.65, f1), rng)
    tp.mantel_set(clutter, V(back_bed + 0.05, 2.0, f1 + 1.16), V(0.0, 1.0, 0.0), V(1.0, 0.0, 0.0), 0.75, rng, False)
    tk.pendant(b, interior, V(-1.1, 1.6, c2), rng, "glass_dirty", 0.45)
    bd.laths(interior, V(0.0, 0.0, c2 + 0.025), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), -2.1, -1.4, 2.2, 3.1, rng)
    tk.chips(parts["debris"], "plaster_interior", -2.2, -1.3, 2.1, 3.2, f1, 16, rng, (0.04, 0.14), (0.012, 0.02))
    lump(parts["debris"], "dirt_debris", V(-1.75, 2.65, f1 - 0.01), (0.4, 0.35, 0.03), rng, 0.3, 2, f1)
    tp.framed(interior, V(-ix + 0.006, 0.9, f1 + 1.55), V(1.0, 0.0, 0.0), 0.36, 0.46, tp.pr("portrait_b"), rng, "timber_beam", -0.08)


def upper_rooms(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    bd.sea_chest(b, furniture, V(2.2, -3.45, f1), math.pi * 0.5, rng)
    b.loot("box", V(2.2, -3.45, f1 + 0.5))
    tp.sewing_table(b, furniture, V(1.05, fy + 0.25, f1), 0.0, rng)
    bd.crate(clutter, V(2.15, -2.45, f1), (0.55, 0.45, 0.4), 0.1, rng)
    bd.crate(clutter, V(2.15, -2.45, f1 + 0.4), (0.45, 0.38, 0.32), -0.2, rng, broken=True)
    tk.col(b, "wood", "crates", 1.85, 2.45, -2.7, -2.2, f1, f1 + 0.72)
    bd.suitcase(clutter, V(1.3, -3.1, f1), 0.4, rng, True)
    tp.chair_light(furniture, V(0.95, -2.95, f1), 0.6, rng, fallen=True)
    tp.papers(parts["debris"], 0.6, 2.3, -3.9, -2.4, f1, 6, rng)
    tk.pendant(b, interior, V(1.45, -3.1, c2), rng, "glass_dirty", 0.35)
    tp.bath(b, furniture, V(0.82, 3.2, f1), math.pi * 0.5, rng)
    tp.toilet(b, furniture, V(2.15, 3.85, f1), 0.0, rng, 2.0)
    tp.basin(b, furniture, V(1.6, 3.92, f1), 0.0, rng)
    tp.wall_mirror(interior, V(ix - 0.014, 2.7, f1 + 1.55), V(-1.0, 0.0, 0.0), 0.4, 0.5, rng, "town_brass", True)
    bd.cabinet(furniture, V(0.49, 2.05, f1 + 1.4), 0.5, 0.16, 0.0, 0.6, math.pi * 0.5, rng, "timber_planks_weathered", paint, 1, 0, 0)
    b.loot("medical", V(1.5, 2.3, f1))
    tk.pendant(b, interior, V(1.45, 2.9, c2), rng, "glass_dirty", 0.3)
    tp.papers(parts["debris"], 0.5, 1.4, -1.9, 1.4, f1, 3, rng)
    block(clutter, "town_carpet", V(0.55, -1.9, f1), V(1.35, 1.4, f1 + 0.008), 0.003, "world")
    tp.framed(interior, V(0.41, -1.9, f1 + 1.6), V(1.0, 0.0, 0.0), 0.3, 0.24, tp.pr("seascape"), rng, "timber_beam", 0.0)
    tk.pendant(b, interior, V(0.95, 0.9, c2), rng, "town_metal", 0.4)


def yard(b, parts, rng):
    yard_part = parts["yard"]
    clutter = parts["clutter"]
    plants = parts["plants"]
    block(yard_part, "concrete", V(-hx, hy, -0.6), V(hx, yard_end, -0.15), 0.0, "world")
    tk.col(b, "concrete", "yard", -hx, hx, hy, yard_end, -0.6, -0.15)
    wall_h = 1.85
    for x0, x1, y0, y1 in ((-hx, -hx + 0.16, hy, yard_end), (hx - 0.16, hx, hy, yard_end), (-hx + 0.16, gate[0] - 0.1, yard_end - 0.16, yard_end), (gate[1] + 0.1, hx - 0.16, yard_end - 0.16, yard_end)):
        block(yard_part, stone, V(x0, y0, -0.6), V(x1, y1, wall_h), 0.0, "world")
        block(yard_part, dressed, V(x0, y0, wall_h), V(x1, y1, wall_h + 0.08), 0.01)
        tk.col(b, "rock", "yard_wall", x0, x1, y0, y1, -0.6, wall_h + 0.08)
    for x in gate:
        block(yard_part, dressed, V(x - 0.1, yard_end - 0.2, -0.6), V(x + 0.1, yard_end + 0.02, wall_h + 0.2), 0.012)
        tk.col(b, "rock", "gate_post", x - 0.1, x + 0.1, yard_end - 0.2, yard_end + 0.02, -0.6, wall_h + 0.2)
    gate_frame = (V(0.0, yard_end - 0.08, 0.0), V(-1.0, 0.0, 0.0), up, V(0.0, 1.0, 0.0))
    kit.door_leaf(yard_part, "timber_planks_weathered", gate_frame, -gate[1] + 0.1, 1.0, 0.0, -0.13, 1.7, gate[1] - gate[0] - 0.22, 104.0, rng, "ledged", 6.0)
    span = tp.privy(b, parts, 1.15, hx - 0.16, 5.9, yard_end - 0.16, -0.15, rng)
    kit.door_leaf(yard_part, "painted_wood_green", kit.plane(V(1.15, 0.0, 0.0), V(-1.0, 0.0, 0.0)), -span[1], 1.0, 0.0, -0.13, 1.95, span[1] - span[0] - 0.02, -105.0, rng, "ledged", 4.0)
    tp.coal_bunker(b, yard_part, V(-1.95, hy + 0.45, -0.15), math.pi, rng)
    bd.dustbin(clutter, V(-0.75, yard_end - 0.45, -0.15), rng)
    tp.tin_bath(clutter, V(-hx + 0.18, 5.55, 1.1), V(1.0, 0.0, 0.0), rng)
    rod(clutter, "rusty_metal", V(-hx + 0.16, 5.55, 1.4), V(-hx + 0.22, 5.55, 1.42), 0.006, 4)
    post = V(0.92, yard_end - 0.35, -0.15)
    rod(clutter, "timber_beam", post, post + V(0.02, 0.0, 2.3), 0.045, 6)
    tk.col(b, "wood", "post", post.x - 0.05, post.x + 0.05, post.y - 0.05, post.y + 0.05, -0.15, 2.15)
    hook = V(-0.6, hy + 0.04, 2.6)
    rod(clutter, "rusty_metal", hook - V(0.0, 0.04, 0.0), hook, 0.006, 4)
    tp.washing_line(clutter, clutter, hook, post + V(0.02, 0.0, 2.25), rng, 4)
    for position, tipped in ((V(0.2, 4.75, -0.15), False), (V(0.45, 4.7, -0.15), True), (V(-0.2, 7.0, -0.15), False)):
        tp.flowerpot(clutter, position, rng, tipped, rng.uniform(0.8, 1.3), not tipped)
    tp.bucket_light(clutter, V(-0.3, 6.1, -0.15), rng, "rusty_metal", True)
    tp.label_bottle(clutter, V(-1.2, 4.75, -0.15), rng, "stout", True)
    for a, c, count in ((V(-hx + 0.4, hy + 1.0, -0.15), V(-hx + 0.4, yard_end - 0.25, -0.15), 8), (V(hx - 0.4, hy + 0.1, -0.15), V(hx - 0.4, 5.7, -0.15), 6), (V(gate[1] + 0.12, yard_end - 0.4, -0.15), V(0.8, yard_end - 0.4, -0.15), 5), (V(-1.2, 5.2, -0.15), V(1.0, 6.6, -0.15), 6)):
        tk.weeds_line(plants, a, c, rng, count)
    tk.chips(parts["debris"], "slate_roof", -1.5, 2.0, hy + 0.2, hy + 1.6, -0.15, 10, rng, (0.08, 0.17), (0.006, 0.008))
    tk.ivy_light(plants, V(hx - 0.17, 4.9, -0.15), V(-1.0, 0.0, 0.0), rng, 1.9, 0.6, 3, 18.0)
    tk.ivy_light(plants, V(-1.6, hy + 0.02, -0.15), V(0.0, 1.0, 0.0), rng, 3.6, 0.9, 4, 18.0)


def exterior_details(b, parts, gable, rng):
    roof = parts["roof"]
    clutter = parts["clutter"]
    plants = parts["plants"]
    gutter_z = gable.eave_top - 0.05 - 0.06
    tk.downpipe_light(roof, ix + 0.1, -gable.edge - 0.04, -hy, gutter_z - 0.03, -0.15, rng)
    tk.downpipe_light(roof, -ix - 0.1, gable.edge + 0.04, hy, gutter_z - 0.03, -0.15, rng, broken=0.9, lean=0.04)
    tp.wall_sheet(parts["joinery"], V(0.33, -hy - 0.024, 1.5), V(0.0, -1.0, 0.0), "notice", rng, 1.0, 0.03)
    tp.label_bottle(clutter, V(door[1] + 0.12, -hy - 0.25, -0.15), rng, "stout")
    for index in range(7):
        kit.grass_tuft(plants, V(rng.uniform(-ix, ix), -gable.edge - 0.06, gutter_z + 0.02), rng, (0.06, 0.2), (3, 5), 0.03)
    for index in range(3):
        lump(plants, "roof_moss", V(rng.uniform(-hx + 0.8, hx - 0.2), rng.uniform(-0.05, 0.05), gable.ridge_top + 0.09), (rng.uniform(0.06, 0.14), 0.08, 0.03), rng, 0.3, 1)
    tk.weeds_line(plants, V(-hx + 0.4, -hy - 0.12, -0.15), V(bay_outer[0].x - 0.05, -hy - 0.12, -0.15), rng, 2)
    tk.weeds_line(plants, V(bay_outer[3].x + 0.05, -hy - 0.12, -0.15), V(door[0] - 0.25, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(door[1] + 0.4, -hy - 0.12, -0.15), V(hx - 0.4, -hy - 0.12, -0.15), rng, 2)
    tk.weeds_line(plants, bay_outer[1] + V(0.0, -0.1, -0.15), bay_outer[2] + V(0.0, -0.1, -0.15), rng, 3)
    tk.chips(parts["debris"], "glass_dirty", bay_outer[1].x, bay_outer[2].x, -5.6, -5.15, -0.15, 8, rng, (0.02, 0.05), (0.003, 0.004))
    tk.chips(parts["debris"], "slate_roof", -2.0, 2.0, -5.4, -4.7, -0.15, 6, rng, (0.08, 0.17), (0.006, 0.008))


def terrace():
    b = kit.Build("terrace", 1101)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0), ("yard", 35.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    shell_walls(b, parts, gable, rng)
    bay(b, parts, rng)
    doorcase(b, parts, kit.facade("front", ix, hy), rng)
    front_windows(b, parts, rng)
    back_openings(b, parts, rng)
    doors = floors_and_walls(b, parts, rng)
    breast_faces = breasts(b, parts, rng)
    finishes(parts, rng, doors, breast_faces)
    hall_room(b, parts, rng)
    parlour_room(b, parts, rng, breast_faces[0])
    kitchen_room(b, parts, rng, breast_faces[1])
    bedrooms(b, parts, rng, breast_faces[2], breast_faces[3])
    upper_rooms(b, parts, rng)
    tk.terrace_roof(b, parts, -hx, hx, gable, rng, 0.35, 0.012, [(0.7, 1.6, 2.2, 3.0, 1.0)], 0.025, True, "rock", True, 1.2, True)
    tk.stack(b, parts["roof"], -hx + 0.42, 0.0, 0.7, 1.1, gable.top(0.55) - 0.3, gable.ridge_top + 0.95, rng, 3)
    exterior_details(b, parts, gable, rng)
    yard(b, parts, rng)
    return b


def terrace_far():
    b = kit.Build("terrace_far", 1102)
    rng = b.rng
    shell = b.part("shell", 30.0)
    gable = gable_of()
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [], front_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [], back_t)
    for side in ("left", "right"):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
        kit.wall(shell, stone, kit.facade(side, hx, hy), outline, [], party_t)
    wide_front = kit.facade("front", hx, hy)
    wide_back = kit.facade("back", hx, hy)
    kit.skin(shell, render, wide_front, kit.rect(-hx, hx, 0.45, wall_top - 0.02), [kit.rect(*w) for w in front_upper] + [kit.rect(door[0], door[1], 0.46, door[3])], 0.02, 0.0, False)
    kit.skin(shell, "render_white", wide_back, kit.rect(-hx, hx, 0.7, wall_top - 0.3), [kit.rect(*w) for w in back_windows] + [kit.rect(back_door[0], back_door[1], 0.71, back_door[3])], 0.018, 0.0, False)
    for w in front_upper:
        kit.skin(shell, "glass_dirty", wide_front, kit.rect(*w), [], 0.004, 0.001, False)
    for w in back_windows:
        kit.skin(shell, "glass_dirty", wide_back, kit.rect(*w), [], 0.004, 0.001, False)
    kit.skin(shell, "soot", wide_front, kit.rect(*door), [], 0.004, 0.001, False)
    kit.skin(shell, "soot", wide_back, kit.rect(*back_door), [], 0.004, 0.001, False)
    frame_block(shell, "render_white", wide_front, -hx, hx, 2.98, 3.1, -0.035, 0.0)
    frame_block(shell, "render_white", wide_front, -hx, hx, wall_top - 0.32, wall_top - 0.02, -0.06, 0.0)
    frame_block(shell, dressed, wide_front, -hx, hx, -0.5, 0.42, -0.035, 0.0)
    prism(shell, dressed, bay_outer, -1.5, 0.8)
    prism(shell, "glass_dirty", bay_outer, 0.8, 2.4)
    prism(shell, paint, bay_outset(bay_outer, 0.05), 2.4, 2.7)
    outer_raised = [p + V(0.0, 0.0, 2.7) for p in bay_outset(bay_outer, 0.09)]
    w1 = V(bay_outer[1].x, -hy, 3.0)
    w2 = V(bay_outer[2].x, -hy, 3.0)
    for facet in ([outer_raised[1], outer_raised[2], w2, w1], [outer_raised[0], outer_raised[1], w1], [outer_raised[2], outer_raised[3], w2]):
        emit(shell, kit.Geo(facet, [kit.orient(tuple(range(len(facet))), facet, up)]), "slate_roof", None, "world")
    kit.roof_slab(shell, gable, -1.0, -hx, hx, "slate_roof", 0.2)
    kit.roof_slab(shell, gable, 1.0, -hx, hx, "roof_moss", 0.2)
    block(shell, "terracotta", V(-hx, -0.13, gable.ridge_top - 0.04), V(hx, 0.13, gable.ridge_top + 0.09))
    block(shell, dressed, V(-hx + 0.07, -0.55, gable.top(0.55) - 0.3), V(-hx + 0.77, 0.55, gable.ridge_top + 1.07))
    for dy in (-0.33, 0.0, 0.33):
        block(shell, "terracotta", V(-hx + 0.34, dy - 0.09, gable.ridge_top + 1.07), V(-hx + 0.5, dy + 0.09, gable.ridge_top + 1.45))
    for x0, x1, y0, y1 in ((-hx, -hx + 0.16, hy, yard_end), (hx - 0.16, hx, hy, yard_end), (-hx, gate[0] - 0.1, yard_end - 0.16, yard_end), (gate[1] + 0.1, hx, yard_end - 0.16, yard_end)):
        block(shell, stone, V(x0, y0, -0.6), V(x1, y1, 1.93), 0.0, "world")
    block(shell, stone, V(1.15, 5.9, -0.6), V(hx - 0.16, yard_end - 0.16, 2.25), 0.0, "world")
    block(shell, "concrete", V(-hx, hy, -0.6), V(hx, yard_end, -0.15), 0.0, "world")
    return b
