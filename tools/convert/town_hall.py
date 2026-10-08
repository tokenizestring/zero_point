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
hx = 7.0
hy = 10.0
wall_t = 0.45
ix = hx - wall_t
fy = -hy + wall_t
by = hy - wall_t
gallery_z = 3.0
gallery_y = -5.0
front_wall = (-5.12, -5.0)
lobby_w = (-1.62, -1.5)
lobby_e = (1.5, 1.62)
proscenium = (6.0, 6.2)
stage_x = 4.5
stage_wall = 0.15
stage_top = 0.9
toilet_top = 3.0
hall_top = 5.6
stone = "granite_rubble"
dressed = "granite_ashlar"
trim = "painted_wood_white"
paint = "painted_wood_green"
door = (-0.85, 0.85, 0.0, 2.6)
door_top = 2.25
front_windows = [(-5.2, -3.8, 0.9, 2.4), (3.8, 5.2, 0.9, 2.4)]
lancets = [(-1.75, -0.8, 3.5, 5.6, 6.2), (-0.45, 0.45, 3.5, 5.9, 6.7), (0.8, 1.75, 3.5, 5.6, 6.2)]
clock_z = 8.4
plaque_z = 7.15
west_windows = [(7.0, 8.4, 0.9, 2.4), (7.2, 8.0, 3.6, 4.7), (2.2, 3.4, 1.6, 4.6), (-1.2, 0.0, 1.6, 4.6), (-4.2, -3.0, 1.6, 4.6), (-8.1, -7.3, 1.6, 2.3)]
east_windows = [(-8.4, -7.0, 0.9, 2.4), (-8.0, -7.2, 3.6, 4.7), (-3.4, -2.2, 1.6, 4.6), (0.0, 1.2, 1.6, 4.6), (7.3, 8.1, 1.6, 2.3)]
side_door = (3.6, 4.5, 0.0, 2.3)
back_vent = (-0.35, 0.35, 8.0, 8.6)
inner_doors = (-0.9, 0.9, 0.0, 2.3)
hatch = (3.0, 4.2, 0.95, 1.85)
side_room_door = (-6.6, -5.7)
gents_door = (-6.25, -5.45)
ladies_door = (5.45, 6.25)
stair = (-6.5, -5.45)
stair_foot = -0.6
steps_x = [(-4.3, -3.3), (3.3, 4.3)]


def gable_of():
    return tk.YGable(-hy - 0.3, hy + 0.3, hx, 0.35, 5.6, 35.0, 0.0)


def lancet_outline(l, pad=0.0):
    a0, a1, z0, spring, apex = l
    return tk.lancet(a0 - pad, a1 + pad, z0 - pad, spring, apex + pad * 1.6, 4)


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    wall_top = gable.height(hx, 0.03)
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    lancet_boxes = [(l[0], l[1], l[2], l[4]) for l in lancets]
    front_open = [door] + front_windows + lancet_boxes
    holes = [kit.rect(door[0], door[1], -0.05, door[3])] + [kit.rect(*w) for w in front_windows] + [lancet_outline(l) for l in lancets]
    kit.wall(shell, stone, front, tk.gable_wall_y(gable, hx), holes, wall_t)
    kit.wall_boxes(b, "rock", "front", front, -hx, hx, -1.5, wall_top, wall_t, front_open)
    tk.gable_cols_y(b, "gable", -hy, fy, gable, wall_top)
    kit.wall(shell, stone, back, tk.gable_wall_y(gable, hx), [kit.rect(*back_vent)], wall_t)
    kit.wall_boxes(b, "rock", "back", back, -hx, hx, -1.5, wall_top, wall_t, [])
    tk.gable_cols_y(b, "gable", by, hy, gable, wall_top)
    for frame, openings_list, tag in ((left, west_windows, "left"), (right, east_windows + [(-side_door[1], -side_door[0], 0.0, side_door[3])], "right")):
        cut = [kit.rect(o[0], o[1], -0.05, o[3]) if o[2] <= 0.01 else kit.rect(*o) for o in openings_list]
        kit.wall(shell, stone, frame, kit.rect(-by, by, -1.5, wall_top), cut, wall_t)
        kit.wall_boxes(b, "rock", tag, frame, -by, by, -1.5, wall_top, wall_t, openings_list)
    for side, reach, gaps in (("front", hx, [(door[0] - 0.35, door[1] + 0.35)]), ("back", hx, []), ("left", hy, []), ("right", hy, [(-side_door[1] - 0.05, -side_door[0] + 0.05)])):
        frame = kit.facade(side, hx, hy)
        edges = [-reach]
        for g0, g1 in gaps:
            edges += [g0, g1]
        edges.append(reach)
        for s0, s1 in zip(edges[0::2], edges[1::2]):
            count = max(1, int(round((s1 - s0) / 0.75)))
            for index in range(count):
                a = s0 + (s1 - s0) * index / count
                c = s0 + (s1 - s0) * (index + 1) / count
                frame_block(shell, dressed, frame, a + 0.006, c - 0.006, -0.5, 0.5 + rng.uniform(-0.02, 0.02), -0.05, 0.0)
        bd.damp_band(shell, frame, -reach, reach, rng, 0.55, 1.1, "granite_rubble_damp", -0.2, 0.003, gaps)
    for corner, ua, ub in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0))):
        tk.quoins_light(shell, dressed, corner, ua, ub, 0.5, wall_top - 0.05, rng, 0.045)
    for frame in (front, back):
        for side in (-1.0, 1.0):
            a = side * hx
            frame_block(shell, dressed, frame, min(a, a - side * 0.6), max(a, a - side * 0.6), wall_top - 0.02, wall_top + 0.22, -0.06, 0.0)
    louvres = kit.facade("back", hx, hy)
    a0, a1, z0, z1 = back_vent
    for index in range(4):
        center = kit.frame_point(louvres, 0.0, z0 + 0.09 + index * 0.13, -wall_t * 0.5)
        slope = (louvres[3] * 0.6 - up).normalized()
        emit(parts["joinery"], kit.geo_box(a1 - a0 + 0.02, 0.2, 0.02), "timber_planks_weathered", kit.place(center, louvres[1], slope.cross(louvres[1]).normalized()), "board")
    tk.opening_block(b, "wood", "vent", back, back_vent, wall_t)
    return wall_top


def frontage(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    front = kit.facade("front", hx, hy)
    a0, a1, z0, z1 = door
    for edge, sign in ((a0, -1.0), (a1, 1.0)):
        lo, hi = sorted((edge, edge + sign * 0.3))
        frame_block(shell, dressed, front, lo, hi, 0.5, z1, -0.08, 0.0, 0.008)
    kit.wall(shell, dressed, front, tk.lancet(a0 - 0.3, a1 + 0.3, z1, z1 + 0.05, z1 + 0.62, 4), [], 0.08, 0.08)
    frame_block(shell, dressed, front, a0 - 0.45, a1 + 0.45, z1 + 0.62, z1 + 0.72, -0.14, 0.0, 0.008)
    ja0, ja1, jtop = tk.door_frame_light(joinery, paint, front, a0, a1, 0.0, door_top, 0.12, 0.07, 0.2)
    width = (ja1 - ja0) * 0.5 - 0.01
    d_axis = 0.12 + 0.1 - 0.0225
    tk.door_leaf_light(joinery, paint, front, ja0 + 0.005, 1.0, d_axis, 0.012, jtop - 0.02, width, 98.0, rng, "panel", 1.0)
    tk.door_leaf_light(joinery, paint, front, ja1 - 0.005, -1.0, d_axis, 0.012, jtop - 0.02, width, 24.0, rng, "panel", 0.0)
    frame_block(joinery, paint, front, a0, a1, door_top, door_top + 0.07, 0.12, 0.32, 0.0, "board")
    matrix = kit.frame_matrix(front)
    for index in range(3):
        p0 = a0 + 0.06 + (a1 - a0 - 0.12) * index / 3
        p1 = a0 + 0.06 + (a1 - a0 - 0.12) * (index + 1) / 3
        kit.pane(joinery, matrix, p0 + 0.01, p1 - 0.01, door_top + 0.07, z1 - 0.05, 0.2, rng.choice(("whole", "shard", "missing")), rng)
        if index:
            frame_block(joinery, paint, front, p0 - 0.012, p0 + 0.012, door_top + 0.07, z1, 0.17, 0.25)
    tk.opening_block(b, "glass", "fanlight", front, (a0, a1, door_top, z1), wall_t)
    frame_block(shell, dressed, front, -0.75, 0.75, 3.42, 3.5, -0.04, 0.0)
    block(shell, dressed, V(a0 - 0.35, -hy - 0.5, -0.45), V(a1 + 0.35, -hy + 0.02, -0.05), 0.015)
    block(shell, dressed, V(a0 - 0.6, -hy - 0.9, -0.5), V(a1 + 0.6, -hy - 0.45, -0.18), 0.015)
    tk.col(b, "rock", "step", a0 - 0.35, a1 + 0.35, -hy - 0.5, -hy, -1.5, -0.05)
    tk.col(b, "rock", "step", a0 - 0.6, a1 + 0.6, -hy - 0.9, -hy - 0.5, -1.5, -0.18)
    tk.col(b, "rock", "threshold", a0, a1, -hy, fy, -1.5, 0.0)
    block(shell, dressed, V(a0, -hy, -0.08), V(a1, fy + 0.04, 0.0), 0.004)
    tk.atlas_panel(shell, "town_signs", kit.frame_point(front, 0.0, plaque_z, 0.021), V(0.0, -1.0, 0.0), 0.9, 0.45, tp.sg("hall_plaque"), 0.0, 0.0)
    frame_block(shell, dressed, front, -0.5, 0.5, plaque_z - 0.28, plaque_z + 0.28, -0.02, 0.0)
    tp.lantern(b, joinery, kit.frame_point(front, 1.45, 2.55, 0.0), V(0.0, -1.0, 0.0), rng)
    tp.notice_board(shell, kit.frame_point(front, 2.4, 1.55, 0.0), V(0.0, -1.0, 0.0), 0.9, 0.7, rng, ("notice", "poster", "card", "letter"))
    center = kit.frame_point(front, 0.0, clock_z, 0.0)
    emit(shell, kit.geo_lathe([(0.0, 0.0), (0.72, 0.0), (0.72, 0.05), (0.62, 0.09), (0.6, 0.06), (0.0, 0.06)], 20), dressed, kit.place(center, V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), "given", True)
    tp.disc(shell, "town_signs", center + V(0.0, -0.065, 0.0), V(0.0, -1.0, 0.0), 0.6, tp.sg("hall_clock"), 20)
    for hand, length in ((0.9, 0.42), (2.6, 0.3)):
        tip = center + V(math.cos(hand) * length, -0.075, math.sin(hand) * length)
        rod(shell, "town_paint_black", center + V(0.0, -0.075, 0.0), tip, 0.012, 3)
    matrix = kit.frame_matrix(front)
    for l in lancets:
        a0, a1, z0, spring, apex = l
        kit.wall(shell, dressed, front, lancet_outline(l, 0.14), [lancet_outline(l)], 0.06, 0.06)
        frame_block(shell, dressed, front, a0 - 0.12, a1 + 0.12, z0 - 0.1, z0, -0.08, wall_t)
        outline = tk.lancet(a0 + 0.03, a1 - 0.03, z0, spring, apex - 0.05, 4)
        lower = [(x, z) for x, z in outline if z <= spring + 1e-6]
        state = rng.random()
        if state < 0.65:
            kit.prism(joinery, "glass_dirty", matrix, outline if state < 0.3 else lower, wall_t * 0.5, wall_t * 0.5 + 0.006)
        for z in (z0 + (spring - z0) * 0.35, z0 + (spring - z0) * 0.7, spring):
            frame_block(joinery, "rusty_metal", front, a0, a1, z - 0.01, z + 0.01, wall_t * 0.5 - 0.01, wall_t * 0.5 + 0.016)
        frame_block(joinery, "rusty_metal", front, (a0 + a1) * 0.5 - 0.01, (a0 + a1) * 0.5 + 0.01, z0, apex - 0.1, wall_t * 0.5 - 0.01, wall_t * 0.5 + 0.016)
        tk.opening_block(b, "glass", "window", front, (a0, a1, z0, apex), wall_t)


def windows(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    front = kit.facade("front", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    for w, lift, boarded in zip(front_windows, (0.0, 0.2), (False, True)):
        tk.sash(b, parts, front, w, wall_t, rng, trim, 0.12, lift, 0.3, 0.3, 2, 1, None, dressed, None, False, boarded, "glass", "window", dressed, trim)
    for frame, openings_list in ((left, west_windows), (right, east_windows)):
        for index, w in enumerate(openings_list):
            if w[3] - w[2] > 2.5:
                tk.sash(b, parts, frame, w, wall_t, rng, trim, 0.12, rng.choice((0.0, 0.0, 0.3)), 0.25, 0.35, 2, 3, None, dressed, None, False, rng.random() < 0.15, "glass", "window", dressed, None)
                frame_block(shell, dressed, frame, w[0] - 0.15, w[1] + 0.15, w[3], w[3] + 0.28, -0.03, wall_t, 0.01)
            elif w[3] - w[2] > 1.0:
                tk.sash(b, parts, frame, w, wall_t, rng, trim, 0.12, 0.0, 0.3, 0.3, 2, 1, None, dressed, None, False, False, "glass", "window", dressed, trim)
            else:
                tk.casement(b, parts, frame, w, wall_t, rng, trim, 0.1, [rng.choice((0.0, 35.0))], 0.3, 0.3, 1, dressed)
    a0, a1, z0, z1 = side_door
    tk.door_unit(joinery, right, -a1, -a0, 0.0, z1, wall_t, paint, rng, "low", 70.0, "ledged", True, 0.0, 0.06, 3.0, trim)
    frame_block(shell, dressed, right, -a1 - 0.15, -a0 + 0.15, z1, z1 + 0.25, -0.03, wall_t)
    block(shell, dressed, V(hx - 0.02, a0 - 0.12, -0.4), V(hx + 0.4, a1 + 0.12, -0.06), 0.012)
    tk.col(b, "rock", "step", hx, hx + 0.4, a0 - 0.12, a1 + 0.12, -0.6, -0.06)
    tk.col(b, "rock", "threshold", ix, hx, a0, a1, -1.5, 0.0)


def floors(b, parts, rng):
    floor = parts["floors"]
    tk.tile_floor(floor, "floorboards", -ix, ix, front_wall[0], proscenium[1], 0.0, 0.05)
    tk.tile_floor(floor, "floorboards", -ix, lobby_w[0], fy, front_wall[0], 0.0, 0.05)
    tk.tile_floor(floor, "town_quarry", lobby_w[0], lobby_e[1], fy, front_wall[0], 0.0, 0.05)
    tk.tile_floor(floor, "town_lino", lobby_e[1], ix, fy, front_wall[0], 0.0, 0.05)
    for s in (-1.0, 1.0):
        x0, x1 = sorted((s * (stage_x + stage_wall), s * ix))
        tk.tile_floor(floor, "town_tiles", x0, x1, proscenium[1], by, 0.0, 0.05)
    tk.col(b, "wood", "ground", -ix, ix, fy, by, -0.3, 0.0)
    block(floor, "floorboards", V(-stage_x, proscenium[1], 0.0), V(stage_x, by, stage_top), 0.0, "world")
    tk.col(b, "wood", "stage", -stage_x, stage_x, proscenium[1], by, 0.0, stage_top)
    for x0, x1 in steps_x:
        tk.stair_flight(b, parts, x0, x1, 4.75, 0.0, proscenium[0] - 4.75, stage_top, 5, rng, 1.0, "floorboards", "timber_beam", None, None, "wood", "steps")
    block(floor, "floorboards", V(-ix, fy, gallery_z - 0.22), V(ix, gallery_y, gallery_z))
    frame_block(floor, "timber_beam", kit.plane(V(0.0, gallery_y, 0.0), V(0.0, 1.0, 0.0)), -ix, ix, gallery_z - 0.3, gallery_z, -0.06, 0.0)
    tk.col(b, "wood", "gallery", -ix, ix, fy, gallery_y, gallery_z - 0.22, gallery_z)
    for s in (-1.0, 1.0):
        x0, x1 = sorted((s * stage_x, s * ix))
        block(floor, "plaster_interior", V(x0, proscenium[1], toilet_top), V(x1, by, toilet_top + 0.12))
        tk.col(b, "wood", "loft", x0, x1, proscenium[1], by, toilet_top, toilet_top + 0.12)


def interior_walls(b, parts, gable, rng):
    joinery = parts["joinery"]
    interior = parts["interior"]
    frame = kit.plane(V(0.0, front_wall[0], 0.0), V(0.0, -1.0, 0.0))
    kit.wall(interior, "plaster_interior", frame, kit.notched(-ix, ix, 0.0, gallery_z - 0.22, [(inner_doors[0], inner_doors[1], inner_doors[3])]), [kit.rect(*hatch)], front_wall[1] - front_wall[0])
    kit.wall_boxes(b, "wood", "front_wall", frame, -ix, ix, 0.0, gallery_z - 0.22, front_wall[1] - front_wall[0], [inner_doors, hatch])
    ja0, ja1, jtop = tk.door_frame_light(joinery, paint, frame, inner_doors[0], inner_doors[1], 0.0, inner_doors[3], 0.0, 0.07, 0.12)
    width = (ja1 - ja0) * 0.5 - 0.01
    tk.door_leaf_light(joinery, paint, frame, ja0 + 0.005, 1.0, 0.06 - 0.0225, 0.012, jtop - 0.02, width, -88.0, rng, "panel", 0.5)
    tk.door_leaf_light(joinery, paint, frame, ja1 - 0.005, -1.0, 0.06 - 0.0225, 0.012, jtop - 0.02, width, -12.0, rng, "panel", 0.0)
    frame_block(joinery, "timber_beam", frame, hatch[0] - 0.06, hatch[1] + 0.06, hatch[2] - 0.04, hatch[2], -0.22, 0.34, 0.0, "board")
    for a in (hatch[0], hatch[1] - 0.05):
        frame_block(joinery, paint, frame, a, a + 0.05, hatch[2], hatch[3], -0.02, 0.14, 0.0, "board")
    frame_block(joinery, paint, frame, hatch[0], hatch[1], hatch[3] - 0.05, hatch[3], -0.02, 0.14, 0.0, "board")
    shutter = kit.frame_matrix(frame) @ kit.Matrix.Translation(V(hatch[0], 0.12, hatch[3])) @ kit.Matrix.Rotation(-1.3, 4, 'X')
    local_block(joinery, paint, shutter, 0.0, hatch[1] - hatch[0], 0.0, 0.025, 0.0, hatch[3] - hatch[2], 0.0, "board")
    for wall, s in ((lobby_w, -1.0), (lobby_e, 1.0)):
        normal = V(-1.0, 0.0, 0.0) if s < 0 else V(1.0, 0.0, 0.0)
        origin_x = wall[0] if s < 0 else wall[1]
        plane = kit.plane(V(origin_x, 0.0, 0.0), normal)
        d0, d1 = sorted((kit.along_of(plane, V(0.0, side_room_door[0], 0.0)), kit.along_of(plane, V(0.0, side_room_door[1], 0.0))))
        a_lo, a_hi = sorted((kit.along_of(plane, V(0.0, fy, 0.0)), kit.along_of(plane, V(0.0, front_wall[0], 0.0))))
        tk.partition(b, parts, V(origin_x, 0.0, 0.0), normal, a_lo, a_hi, 0.0, gallery_z - 0.22, wall[1] - wall[0], [(d0, d1, 0.0, 2.15)], "lobby")
        tk.door_unit(joinery, plane, d0, d1, 0.0, 2.15, wall[1] - wall[0], paint, rng, "high" if s < 0 else "low", -rng.uniform(80.0, 100.0), "panel", True, 0.0, 0.06, rng.uniform(0.0, 2.0), trim)
    frame = kit.plane(V(0.0, proscenium[0], 0.0), V(0.0, -1.0, 0.0))
    top = lambda x: gable.height(x, 0.3)
    outline = kit.notched(-ix, ix, 0.0, 1.0, [(gents_door[0], gents_door[1], 2.15), (ladies_door[0], ladies_door[1], 2.15)])
    outline = outline[:-2] + [(ix, top(ix)), (0.0, top(0.0)), (-ix, top(-ix))]
    opening = (-stage_x, stage_x, stage_top, 4.0)
    kit.wall(interior, "plaster_interior", frame, outline, [kit.rect(*opening)], proscenium[1] - proscenium[0])
    kit.wall_boxes(b, "rock", "proscenium", frame, -ix, ix, 0.0, hall_top, proscenium[1] - proscenium[0], [opening, (gents_door[0], gents_door[1], 0.0, 2.15), (ladies_door[0], ladies_door[1], 0.0, 2.15)])
    for d0, d1 in (gents_door, ladies_door):
        tk.door_unit(joinery, frame, d0, d1, 0.0, 2.15, proscenium[1] - proscenium[0], paint, rng, "low" if d0 < 0 else "high", rng.uniform(60.0, 95.0), "panel", True, 0.0, 0.06, 1.0, trim)
    frame_block(joinery, "timber_beam", frame, -stage_x - 0.2, stage_x + 0.2, 4.0, 4.3, -0.08, 0.0, 0.006)
    for x in (-stage_x - 0.2, stage_x):
        frame_block(joinery, "timber_beam", frame, x, x + 0.2, stage_top, 4.0, -0.06, 0.0, 0.006)
    frame_block(joinery, paint, frame, -stage_x, stage_x, 0.05, stage_top - 0.05, -0.02, 0.0, 0.0, "board")
    for s in (-1.0, 1.0):
        x_face = s * stage_x
        normal = V(-s, 0.0, 0.0)
        plane = kit.plane(V(x_face, 0.0, 0.0), normal)
        a_lo, a_hi = sorted((kit.along_of(plane, V(0.0, proscenium[1], 0.0)), kit.along_of(plane, V(0.0, by, 0.0))))
        tk.partition(b, parts, V(x_face, 0.0, 0.0), normal, a_lo, a_hi, 0.0, gable.height(stage_x, 0.25), stage_wall, [], "wing")


def stair_and_gallery(b, parts, rng):
    joinery = parts["joinery"]
    interior = parts["interior"]
    run = stair_foot - gallery_y
    tk.stair_flight(b, parts, stair[0], stair[1], stair_foot, 0.0, run, gallery_z, 17, rng, -1.0, "floorboards", "timber_beam", "town_carpet", "town_brass", "wood", "stair")
    tk.under_stair_panel(interior, stair[1] + 0.02, stair_foot, 0.0, run, gallery_z, -1.0, rng, paint, None, 0.03, 1.0)
    bd.balustrade(b, joinery, V(stair[1] + 0.03, stair_foot - 0.05, 0.02), V(stair[1] + 0.03, gallery_y + 0.02, gallery_z + 0.02), rng, 0.9, 0.15, "timber_beam", paint, 0.08, (True, False), False)
    bd.balustrade(b, joinery, V(stair[1] + 0.03, gallery_y + 0.04, gallery_z), V(ix - 0.04, gallery_y + 0.04, gallery_z), rng, 0.95, 0.14, "timber_beam", paint, 0.1, (True, True), True, "gallery")


def finishes(parts, rng):
    dado = ("panel", 1.2, paint, ("plaster", 2))
    plain = ("plaster", 1)
    tiles = ("tiles", 1.3, "kitchen_tiles", ("plaster", 1))
    paper = ("paper", "town_stripe", 1, 1)
    hall_left = [(-w[1], -w[0], w[2], w[3]) for w in west_windows if -w[0] > gallery_y and -w[1] < proscenium[0]]
    hall_right = [w for w in east_windows if w[0] > gallery_y and w[1] < proscenium[0]] + [side_door]
    tk.room(parts, rng, -ix, ix, gallery_y, proscenium[0], 0.0, hall_top, {"left": dado, "right": dado}, {"left": hall_left, "right": hall_right}, paint, None, False, 0, (), None, 10, 0.0)
    gal_left = [(-w[1], -w[0], w[2], w[3]) for w in west_windows if -w[1] < gallery_y and w[2] > 3.0]
    gal_right = [w for w in east_windows if w[1] < gallery_y and w[2] > 3.0]
    tk.room(parts, rng, -ix, ix, fy, gallery_y, gallery_z, hall_top, {"left": plain, "right": plain}, {"left": gal_left, "right": gal_right}, None, None, False, 0, (), None, 4, 0.0)
    off_left = [(-w[1], -w[0], w[2], w[3]) for w in west_windows if -w[1] < gallery_y and w[3] < 3.0]
    tk.room(parts, rng, -ix, lobby_w[0], fy, front_wall[0], 0.0, gallery_z - 0.22, {"front": paper, "back": paper, "left": paper, "right": paper}, {"front": [front_windows[0]], "left": off_left, "right": [(side_room_door[0], side_room_door[1], 0.0, 2.15)]}, trim, None, True, 1, (), None, 3, 0.0)
    kit_right = [w for w in east_windows if w[1] < gallery_y and w[3] < 3.0]
    tk.room(parts, rng, lobby_e[1], ix, fy, front_wall[0], 0.0, gallery_z - 0.22, {"front": tiles, "back": tiles, "left": tiles, "right": tiles}, {"front": [front_windows[1]], "back": [hatch], "left": [(side_room_door[0], side_room_door[1], 0.0, 2.15)], "right": kit_right}, None, None, True, 1, (), None, 3, 0.0)
    tk.room(parts, rng, lobby_w[1], lobby_e[0], fy, front_wall[0], 0.0, gallery_z - 0.22, {"front": tiles, "back": tiles, "left": tiles, "right": tiles}, {"front": [door], "back": [inner_doors], "left": [(side_room_door[0], side_room_door[1], 0.0, 2.15)], "right": [(side_room_door[0], side_room_door[1], 0.0, 2.15)]}, None, None, True, 0, (), None, 3, 0.0)
    loo = ("tiles", 1.5, "kitchen_tiles", ("plaster", 0))
    for s in (-1.0, 1.0):
        x0, x1 = sorted((s * (stage_x + stage_wall), s * ix))
        outer = "right" if s > 0 else "left"
        door_x = ladies_door if s > 0 else gents_door
        tk.room(parts, rng, x0, x1, proscenium[1], by, 0.0, toilet_top, {"front": loo, "back": loo, outer: loo}, {"front": [(door_x[0], door_x[1], 0.0, 2.15)], outer: [(7.3, 8.1, 1.6, 2.3)]}, None, None, False, 0, (), None, 2, 0.0)
    tk.wall_finish(parts["interior"], "back", ("plaster", 2), -stage_x, stage_x, proscenium[1], by, stage_top, 5.6, [], rng)


def trusses(parts, gable):
    joinery = parts["joinery"]
    wall_top = gable.height(hx, 0.03)
    for y in (-2.4, 1.0, 4.4):
        left = V(-ix - 0.1, y, wall_top - 0.1)
        right = V(ix + 0.1, y, wall_top - 0.1)
        apex = V(0.0, y, gable.height(0.0, 0.22))
        foot = V(0.0, y, wall_top - 0.1)
        kit.member(joinery, "timber_beam", left, right, 0.16, 0.24, up, 0.0, "board")
        for a in (left, right):
            kit.member(joinery, "timber_beam", a, apex, 0.16, 0.2, V(0.0, 1.0, 0.0).cross((apex - a).normalized()), 0.0, "board")
            kit.member(joinery, "timber_beam", foot + V(0.0, 0.0, 0.4), a.lerp(apex, 0.55), 0.12, 0.12, V(0.0, 1.0, 0.0), 0.0, "board")
        kit.member(joinery, "timber_beam", foot, apex, 0.16, 0.16, V(1.0, 0.0, 0.0), 0.0, "board")
        for side in (-1.0, 1.0):
            block(joinery, "rusty_metal", V(side * ix - 0.16, y - 0.1, wall_top - 0.3), V(side * ix + 0.16, y + 0.1, wall_top - 0.22))


def hall(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    for row, y in enumerate((-2.3, -1.2, -0.1, 1.0)):
        for column in range(7):
            x = -3.3 + column * 1.0 + rng.uniform(-0.05, 0.05)
            roll = rng.random()
            if roll < 0.12:
                continue
            fallen = roll < 0.3
            tp.chair_light(furniture, V(x, y + rng.uniform(-0.05, 0.05), 0.0), math.pi + rng.uniform(-0.12, 0.12) + (rng.uniform(-1.2, 1.2) if fallen else 0.0), rng, "timber_beam", "timber_planks_weathered", fallen)
    for position in (V(6.15, -4.4, 0.0), V(6.15, -3.75, 0.0), V(6.15, 2.1, 0.0)):
        tp.chair_stack(b, furniture, position, -math.pi * 0.5, rng, rng.randint(4, 6))
    for y in (1.4, 2.45):
        tp.trestle_leaning(furniture, V(-ix + 0.3, y, 0.0), V(0.0, 1.0, 0.0), rng, 1.0, 1.4, 0.22)
    tk.col(b, "wood", "tables", -ix, -ix + 0.45, 1.4, 3.45, 0.0, 1.4)
    tp.table_light(furniture, 3.6, -4.3, 0.0, 1.8, 0.7, 0.76, rng, "timber_planks_weathered", "timber_beam")
    tk.col(b, "wood", "table", 2.7, 4.5, -4.65, -3.95, 0.0, 0.76)
    tp.tea_urn(clutter, V(3.2, -4.3, 0.76), rng)
    for k in range(4):
        tp.cup_light(clutter, V(3.7 + k * 0.17 + rng.uniform(-0.03, 0.03), -4.4 + rng.uniform(-0.1, 0.1), 0.76), rng)
    bd.piano(b, furniture, clutter, V(-ix + 0.33, 4.25, 0.0), math.pi * 0.5, rng)
    tp.stove_light(b, furniture, V(ix - 0.55, -0.9, 0.0), rng, V(ix, -0.9, 3.2))
    tp.framed(interior, V(0.0, proscenium[0] - 0.02, 4.75), V(0.0, -1.0, 0.0), 0.62, 0.8, tp.pr("portrait_a"), rng, "timber_beam", 0.03)
    tp.framed(interior, V(ix - 0.02, -1.5, 2.2), V(-1.0, 0.0, 0.0), 0.9, 0.5, tp.pr("hymns"), rng, "timber_beam", -0.02)
    tp.notice_board(interior, V(-ix + 0.02, 1.3 + 0.95, 1.7), V(1.0, 0.0, 0.0), 0.8, 0.6, rng, ("notice", "poster", "card", "letter", "calendar"))
    tie = gable_of().height(hx, 0.03) - 0.22
    for x, y in ((-2.6, -2.4), (2.6, -2.4), (-2.6, 1.0), (2.6, 1.0)):
        tk.pendant(b, interior, V(x, y, tie), rng, "town_metal", 1.6, "warm", 8)
    tp.papers(parts["debris"], -6.0, 6.0, -4.8, 5.8, 0.0, 12, rng, ("newspaper", "notice", "poster", "card", "letter", "music"))
    tp.debris_field(parts, -6.3, 6.3, -4.8, 5.8, 0.0, rng, 14, 4, 0, 10)
    tk.chips(parts["debris"], "slate_roof", -5.2, -3.9, 0.0, 2.2, 0.0, 12, rng, (0.1, 0.2), (0.006, 0.008))
    tk.chips(parts["debris"], "foliage", -5.4, -3.7, -0.2, 2.4, 0.0, 10, rng, (0.02, 0.05), (0.002, 0.003), 0.5)


def stage(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tk.atlas_panel(interior, "town_print", V(0.0, by - 0.03, 2.95), V(0.0, -1.0, 0.0), 5.6, 3.2, tp.pr("seascape"), 0.0, 0.0)
    for x0, x1 in ((-stage_x, -stage_x + 1.9), (stage_x, stage_x - 1.9)):
        tp.curtain_light(clutter, V(x0, proscenium[1] + 0.12, 3.95), V(x1, proscenium[1] + 0.12, 3.95), 3.0, rng, "fabric_worn", 0.6, True, 6, 5)
    tp.lectern_light(b, furniture, clutter, V(1.6, 7.1, stage_top), math.pi, rng)
    tp.table_light(furniture, -1.0, 8.3, stage_top, 1.6, 0.7, 0.76, rng, "floorboards", "timber_beam")
    tk.col(b, "wood", "table", -1.8, -0.2, 7.95, 8.65, stage_top, stage_top + 0.76)
    tp.drape_light(clutter, V(-1.0, 8.3, stage_top + 0.77), 1.66, 0.76, 0.35, 0.0, rng, "fabric_worn", 5, (True, True))
    for x, yaw, fallen in ((-1.6, 0.2, False), (-0.4, -0.1, False), (2.8, 1.4, True)):
        tp.chair_light(furniture, V(x, 7.55, stage_top), math.pi + yaw, rng, "timber_beam", "timber_planks_weathered", fallen)
    tp.crate_light(clutter, V(3.6, 8.9, stage_top), (0.7, 0.5, 0.45), 0.2, rng)
    tk.col(b, "wood", "crate", 3.2, 4.0, 8.6, 9.2, stage_top, stage_top + 0.45)
    b.loot("box", V(-3.6, 9.0, stage_top))
    kit.member(interior, "rusty_metal", V(-4.2, 6.9, 4.6), V(4.2, 6.9, 4.6), 0.05, 0.05, up, 0.0, "box")
    for x in (-4.2, 4.2):
        rod(interior, "rusty_metal", V(x, 6.9, 4.6), V(x, 6.9, gable_of().height(x, 0.4)), 0.008, 3)
    for x in (-2.5, 0.0, 2.5):
        tp.cage_lamp(b, interior, V(x, 6.9, 4.57), rng, "warm")
    tp.debris_field(parts, -4.2, 4.2, 6.4, 9.3, stage_top, rng, 6, 0, 3, 6)


def side_rooms(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.desk_light(b, furniture, clutter, V(-4.5, fy + 0.4, 0.0), math.pi, rng, 1.3, 0.7, 0.76, "timber_beam", "floorboards", ("papers", "files", "phone"))
    tp.chair_light(furniture, V(-4.5, -8.4, 0.0), 0.15, rng)
    tp.table_light(furniture, -3.7, -6.9, 0.0, 1.6, 0.9, 0.75, rng)
    tk.col(b, "wood", "table", -4.5, -2.9, -7.35, -6.45, 0.0, 0.75)
    for position, yaw, fallen in ((V(-4.85, -6.9, 0.0), math.pi * 0.5, False), (V(-2.55, -6.8, 0.0), -math.pi * 0.5, True), (V(-3.7, -6.1, 0.0), math.pi, False)):
        tp.chair_light(furniture, position, yaw, rng, "timber_beam", "timber_planks_weathered", fallen)
    tp.filing_cabinet(b, furniture, V(-6.05, front_wall[0] - 0.35, 0.0), 0.0, rng, 4, "green")
    tp.safe_light(b, furniture, V(-5.25, front_wall[0] - 0.3, 0.0), 0.0, rng, 1.2)
    b.loot("box", V(-2.2, -8.9, 0.0))
    tp.framed(interior, V(-ix + 0.02, -6.2, 1.7), V(1.0, 0.0, 0.0), 1.2, 0.7, tp.pr("map"), rng, "timber_beam", 0.01)
    tp.pigeonholes(interior, clutter, V(lobby_w[0] - 0.02, -8.3, 1.65), V(-1.0, 0.0, 0.0), 3, 2, rng)
    tk.pendant(b, interior, V(-4.0, -7.3, gallery_z - 0.22), rng, "town_metal", 0.45, "warm", 8)
    tp.papers(parts["debris"], -6.3, -1.9, -9.3, -5.4, 0.0, 6, rng, ("letter", "envelope", "notice", "card"))
    tp.sink_light(b, furniture, clutter, V(4.5, fy + 0.25, 0.0), math.pi, rng, 0.76, 0.48, 0.4)
    tp.cooker_light(b, furniture, V(ix - 0.29, -6.2, 0.0), -math.pi * 0.5, rng, "cream")
    tp.dresser_light(b, furniture, clutter, V(lobby_e[1] + 0.24, -8.2, 0.0), math.pi * 0.5, rng, paint, 1.3)
    tp.table_light(furniture, 3.9, -7.1, 0.0, 1.2, 0.7, 0.76, rng)
    tk.col(b, "wood", "table", 3.3, 4.5, -7.45, -6.75, 0.0, 0.76)
    tp.tea_urn(clutter, V(3.6, -7.1, 0.76), rng)
    b.loot("food", V(4.2, -7.1, 0.76))
    tp.wall_shelves(b, furniture, clutter, V(4.5, front_wall[0] - 0.01, 0.0), V(6.45, front_wall[0] - 0.01, 0.0), V(0.0, -1.0, 0.0), [0.35, 0.9, 1.45, 2.0], rng, ("can", "jar", "box", "gap"), 0.32)
    b.loot("food", V(5.3, front_wall[0] - 0.55, 0.0))
    tp.bulb(b, interior, V(4.0, -7.3, gallery_z - 0.22), rng, 0.45, "warm")
    tp.debris_field(parts, 1.9, 6.3, -9.3, -5.5, 0.0, rng, 4, 2, 1, 0)
    bd.coat_rail(interior, clutter, V(lobby_w[1] + 0.01, -8.9, 1.6), V(lobby_w[1] + 0.01, -7.6, 1.6), V(1.0, 0.0, 0.0), rng, 2)
    tp.bench_light(b, furniture, V(lobby_w[1] + 0.25, -8.25, 0.0), math.pi * 0.5, rng, 1.2)
    tp.aid_cabinet(interior, clutter, V(lobby_e[0] - 0.02, -7.6, 1.55), V(-1.0, 0.0, 0.0), rng)
    b.loot("medical", V(1.2, -8.2, 0.0))
    tp.notice_board(interior, V(lobby_e[0] - 0.02, -8.9, 1.6), V(-1.0, 0.0, 0.0), 0.7, 0.55, rng, ("notice", "card", "letter"))
    tk.pendant(b, interior, V(0.0, -7.3, gallery_z - 0.22), rng, "ceramic", 0.45, "warm", 8)
    tp.papers(parts["debris"], -1.2, 1.2, -9.3, -5.4, 0.0, 5, rng, ("notice", "poster", "card"))
    tp.urinal_trough(b, furniture, -ix + 0.05, -5.85, by, -1.0, rng)
    tp.cubicles(b, furniture, -5.75, -stage_x - stage_wall, by, 8.3, 0.0, 1, rng, paint, (True, False))
    tp.basin(b, furniture, V(-ix + 0.25, 7.7, 0.0), math.pi * 0.5, rng, 10)
    tp.cubicles(b, furniture, stage_x + stage_wall, ix, by, 8.3, 0.0, 2, rng, paint, (False, False))
    tp.basin(b, furniture, V(ix - 0.25, 7.7, 0.0), -math.pi * 0.5, rng, 10)
    for x in (-5.6, 5.6):
        tp.bulb(b, interior, V(x, 7.2, toilet_top), rng, 0.4, "cold")


def gallery(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    z = gallery_z
    for position in (V(-3.6, -9.05, z), V(-2.95, -9.1, z), V(4.6, -9.05, z), V(5.3, -9.0, z)):
        tp.chair_stack(b, furniture, position, 0.0, rng, rng.randint(3, 5))
    tp.crate_light(clutter, V(2.8, -8.9, z), (0.7, 0.5, 0.45), 0.15, rng)
    tp.crate_light(clutter, V(2.9, -8.85, z + 0.45), (0.55, 0.42, 0.38), -0.2, rng)
    tk.col(b, "wood", "crates", 2.4, 3.2, -9.2, -8.6, z, z + 0.83)
    b.loot("box", V(-5.6, -8.6, z))
    tp.trestle_leaning(furniture, V(-6.2, -9.3, z), V(1.0, 0.0, 0.0), rng, 1.6, 0.7, -0.3)
    tp.chair_light(furniture, V(0.9, -6.0, z), 2.4, rng, "timber_beam", "timber_planks_weathered", True)
    tp.bulb(b, interior, V(-3.0, -7.3, gable_of().height(-3.0, 0.4)), rng, 3.0, "warm")
    tp.papers(parts["debris"], -5.0, 6.0, -9.2, -5.4, z, 5, rng, ("music", "notice", "poster"))
    tp.debris_field(parts, -6.2, 6.2, -9.3, -5.3, z, rng, 6, 2, 0, 4)


def exterior(b, parts, gable, rng):
    plants = parts["plants"]
    tk.ygable_roof(b, parts, gable, rng, (-1.0, 1.0), 0.35, 0.012, [(0.0, 2.2, 2.6, 4.2, 1.0)], 0.03, 0.36, 0.76, 0.52, True, (True, True), "rock", True)
    tk.ivy_light(plants, V(-hx - 0.02, 6.5, -0.15), V(-1.0, 0.0, 0.0), rng, 4.0, 1.0, 3, 8.0)
    tk.ivy_light(plants, V(3.5, hy + 0.02, -0.15), V(0.0, 1.0, 0.0), rng, 3.4, 0.8, 3, 8.0)
    tk.weeds_line(plants, V(-hx + 0.3, -hy - 0.12, -0.15), V(door[0] - 0.7, -hy - 0.12, -0.15), rng, 4)
    tk.weeds_line(plants, V(door[1] + 0.7, -hy - 0.12, -0.15), V(hx - 0.3, -hy - 0.12, -0.15), rng, 4)
    tk.weeds_line(plants, V(-hx + 0.3, hy + 0.12, -0.15), V(hx - 0.3, hy + 0.12, -0.15), rng, 6)
    tk.weeds_line(plants, V(-hx - 0.12, -hy + 0.3, -0.15), V(-hx - 0.12, hy - 0.3, -0.15), rng, 7)
    tk.weeds_line(plants, V(hx + 0.12, -hy + 0.3, -0.15), V(hx + 0.12, hy - 0.3, -0.15), rng, 7)
    for k in range(6):
        lump(plants, "roof_moss", V(0.0 + rng.uniform(-0.05, 0.05), rng.uniform(-hy + 1.0, hy - 1.0), gable.ridge_top + 0.09), (0.08, rng.uniform(0.06, 0.14), 0.03), rng, 0.3, 1)


def hall_building():
    b = kit.Build("hall", 2101)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    shell_walls(b, parts, gable, rng)
    frontage(b, parts, rng)
    windows(b, parts, rng)
    floors(b, parts, rng)
    interior_walls(b, parts, gable, rng)
    stair_and_gallery(b, parts, rng)
    finishes(parts, rng)
    trusses(parts, gable)
    hall(b, parts, rng)
    stage(b, parts, rng)
    side_rooms(b, parts, rng)
    gallery(b, parts, rng)
    exterior(b, parts, gable, rng)
    return b


def hall_far():
    b = kit.Build("hall_far", 2102)
    shell = b.part("shell", 30.0)
    gable = gable_of()
    wall_top = gable.height(hx, 0.03)
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    kit.wall(shell, stone, front, tk.gable_wall_y(gable, hx), [], wall_t)
    kit.wall(shell, stone, back, tk.gable_wall_y(gable, hx), [], wall_t)
    for frame in (left, right):
        kit.wall(shell, stone, frame, kit.rect(-by, by, -1.5, wall_top), [], wall_t)
    for o in [door] + front_windows:
        kit.skin(shell, "glass_dirty" if o[2] > 0.3 else "soot", front, kit.rect(*o), [], 0.004, 0.02, False)
    for l in lancets:
        kit.skin(shell, "glass_dirty", front, lancet_outline(l), [], 0.004, 0.02, False)
    for frame, openings_list in ((left, west_windows), (right, east_windows + [(-side_door[1], -side_door[0], 0.0, side_door[3])])):
        for o in openings_list:
            kit.skin(shell, "glass_dirty" if o[2] > 0.3 else "soot", frame, kit.rect(*o), [], 0.004, 0.02, False)
    for side in (-1.0, 1.0):
        tk.roof_slab_y(shell, gable, side, gable.x0, gable.x1, "slate_roof", 0.2)
    block(shell, "terracotta", V(-0.13, gable.x0, gable.ridge_top - 0.04), V(0.13, gable.x1, gable.ridge_top + 0.09))
    tp.disc(shell, "town_signs", V(0.0, -hy - 0.03, clock_z), V(0.0, -1.0, 0.0), 0.6, tp.sg("hall_clock"), 16)
    tk.atlas_panel(shell, "town_signs", V(0.0, -hy - 0.021, plaque_z), V(0.0, -1.0, 0.0), 0.9, 0.45, tp.sg("hall_plaque"), 0.0, 0.0)
    return b
