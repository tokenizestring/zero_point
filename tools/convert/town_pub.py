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
hx = 6.0
hy = 5.5
wall_t = 0.45
ix = hx - wall_t
fy = -hy + wall_t
by = hy - wall_t
c1 = 3.1
f1 = 3.35
c2 = 5.85
paint = "town_paint_green"
trim = "painted_wood_white"
stone = "granite_rubble"
dressed = "granite_ashlar"
render = "render_white"
door = (-0.6, 0.6, 0.0, 2.62)
door_top = 2.28
windows = [(-5.0, -3.5, 0.75, 2.45), (-2.6, -1.1, 0.75, 2.45), (1.1, 2.6, 0.75, 2.45), (3.5, 5.0, 0.75, 2.45)]
upper_windows = [(-4.7, -3.7, 4.0, 5.45), (-2.55, -1.55, 4.0, 5.45), (-0.5, 0.5, 4.0, 5.45), (1.55, 2.55, 4.0, 5.45), (3.7, 4.7, 4.0, 5.45)]
pilasters = [(-5.98, -5.55), (-3.25, -2.85), (-1.0, -0.66), (0.66, 1.0), (2.85, 3.25), (5.55, 5.98)]
left_windows = [(3.65, 4.65, 0.85, 2.45)]
right_windows = [(-4.65, -3.65, 0.85, 2.45), (2.0, 3.0, 1.0, 2.2)]
back_door = (3.08, 4.22, 0.0, 2.25)
store_door = (-4.75, -3.6, 0.0, 2.3)
back_windows = [(1.1, 2.0, 1.7, 2.5), (-1.9, -0.9, 1.0, 2.2), (3.4, 4.1, 4.0, 5.3), (1.4, 2.3, 4.3, 5.3), (-1.4, -0.4, 4.0, 5.45), (-4.5, -3.5, 4.0, 5.4)]
partition = (1.0, 1.12)
stair_x = (-5.55, -4.35)
stair_foot = 1.3
stair_run = 3.6
stair_steps = 15
well = (-5.55, -4.35, 1.3, 4.9)
enclosure = (-4.35, -4.25)
toilet_wall = (-3.05, -2.95)
toilet_split = (2.95, 3.05)
store_wall = (0.2, 0.3)
front_rooms = (-0.1, 0.0)
back_rooms = (1.3, 1.4)
landing_wall = (-3.15, -3.05)
living_split = (0.55, 0.65)
bath_split = (-0.7, -0.6)
kitchen_split = (2.4, 2.5)
stair_door = (-5.5, -4.38, 0.0, 2.2)
passage_door = (-4.22, -3.08, 0.0, 2.2)
servery_door = (1.75, 2.9, 0.0, 2.2)
ladies_door = (1.45, 2.6, 0.0, 2.2)
gents_door = (3.45, 4.6, 0.0, 2.2)
living_door = (-2.25, -1.1, f1, f1 + 2.2)
bedroom_door = (1.3, 2.45, f1, f1 + 2.2)
bath_door = (-2.35, -1.2, f1, f1 + 2.2)
bed2_door = (0.15, 1.3, f1, f1 + 2.2)
kitchen_door = (2.95, 4.1, f1, f1 + 2.2)


def gable_of():
    return kit.Gable(-hx, hx, hy, 0.3, 6.05, 35.0)


def flip(o):
    return (-o[1], -o[0], o[2], o[3])


def interior_wall(b, parts, origin, normal, a0, a1, z0, z1, thickness, doors, tag):
    frame = kit.plane(origin, normal)
    notches = sorted((d[0], d[1], d[3]) for d in doors)
    kit.wall(parts["interior"], "plaster_interior", frame, kit.notched(a0, a1, z0, z1, notches) if notches else kit.rect(a0, a1, z0, z1), [], thickness)
    kit.wall_boxes(b, "wood", tag, frame, a0, a1, z0, z1, thickness, doors)
    return frame


def frontage(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    front = kit.facade("front", hx, hy)
    holes = [kit.rect(w[0], w[1], w[2], w[3]) for w in windows]
    kit.skin(joinery, paint, front, kit.notched(-5.95, 5.95, 0.16, 2.74, [(door[0], door[1], door[3])]), holes, 0.03)
    for a0, a1 in ((-5.98, door[0]), (door[1], 5.98)):
        frame_block(shell, dressed, front, a0, a1, -0.45, 0.16, -0.06, 0.0, 0.008)
    for p0, p1 in pilasters:
        frame_block(joinery, paint, front, p0, p1, 0.16, 2.6, -0.11, -0.03, 0.0, "board")
        frame_block(joinery, paint, front, p0 - 0.03, p1 + 0.03, 2.6, 2.74, -0.15, -0.03, 0.0, "board")
        frame_block(shell, dressed, front, p0 - 0.02, p1 + 0.02, -0.45, 0.16, -0.14, 0.0, 0.008)
    for w0, w1, z0, z1 in windows:
        frame_block(joinery, paint, front, w0 + 0.08, w1 - 0.08, 0.26, z0 - 0.1, -0.048, -0.03, 0.004, "board")
        frame_block(joinery, paint, front, w0 - 0.06, w1 + 0.06, z0 - 0.06, z0, -0.12, 0.05, 0.004, "board")
        frame_block(joinery, paint, front, w0 - 0.02, w1 + 0.02, z1, z1 + 0.08, -0.08, 0.0, 0.0, "board")
    frame_block(joinery, paint, front, -5.95, 5.95, 2.74, 3.68, -0.12, -0.03, 0.0, "board")
    tk.atlas_quad(joinery, "town_signs", [kit.frame_point(front, -4.8, 2.76, 0.121), kit.frame_point(front, 4.8, 2.76, 0.121), kit.frame_point(front, 4.8, 3.66, 0.121), kit.frame_point(front, -4.8, 3.66, 0.121)], tp.sg("pub_fascia"))
    for sign in (-1.0, 1.0):
        frame_block(joinery, paint, front, min(sign * 5.6, sign * 5.98), max(sign * 5.6, sign * 5.98), 2.7, 3.68, -0.18, -0.03, 0.0, "board")
    frame_block(joinery, paint, front, -6.0, 6.0, 3.68, 3.78, -0.22, -0.03, 0.0, "board")
    frame_block(joinery, "rusty_metal", front, -6.0, 6.0, 3.78, 3.8, -0.24, 0.0)
    tk.door_unit(joinery, front, door[0], door[1], 0.0, door_top, wall_t, paint, rng, "high", 84.0, "panel", True, 0.0, 0.06, 0.0, paint)
    frame_block(joinery, paint, front, door[0], door[1], door_top, door_top + 0.06, 0.04, 0.16, 0.0, "board")
    matrix = kit.frame_matrix(front)
    for index in range(3):
        p0 = door[0] + 0.06 + (door[1] - door[0] - 0.12) * index / 3
        p1 = door[0] + 0.06 + (door[1] - door[0] - 0.12) * (index + 1) / 3
        kit.pane(joinery, matrix, p0 + 0.01, p1 - 0.01, door_top + 0.06, door[3] - 0.04, 0.1, rng.choice(("whole", "shard", "missing")), rng)
        if index:
            frame_block(joinery, paint, front, p0 - 0.015, p0 + 0.015, door_top + 0.06, door[3], 0.08, 0.14)
    frame_block(joinery, paint, front, door[0], door[1], door[3] - 0.04, door[3], 0.04, 0.16, 0.0, "board")
    tk.opening_block(b, "glass", "fanlight", front, (door[0], door[1], door_top, door[3]), wall_t)
    block(shell, dressed, V(door[0] - 0.15, -hy - 0.4, -0.45), V(door[1] + 0.15, -hy + 0.02, -0.06), 0.015)
    tk.col(b, "rock", "step", door[0] - 0.15, door[1] + 0.15, -hy - 0.4, -hy, -1.5, -0.06)
    tk.col(b, "rock", "threshold", door[0], door[1], -hy, fy, -1.5, 0.0)
    block(shell, dressed, V(door[0], -hy, -0.08), V(door[1], fy + 0.04, 0.0), 0.004)


def quoins(shell, rng, wall_top):
    z = -0.1
    course = 0
    while z < wall_top - 0.2:
        h = min(rng.uniform(0.26, 0.32), wall_top - z)
        long_face = course % 2 == 0
        for sx in (-1.0, 1.0):
            face_len = 0.5 if long_face else 0.3
            side_len = 0.3 if long_face else 0.5
            if z > 3.78:
                lo, hi = kit.box_between(V(sx * (hx + 0.025), -hy - 0.025, z + 0.006), V(sx * (hx - face_len), -hy, z + h - 0.006))
                block(shell, dressed, lo, hi)
            lo, hi = kit.box_between(V(sx * hx, -hy - 0.025, z + 0.006), V(sx * (hx + 0.025), -hy + side_len, z + h - 0.006))
            block(shell, dressed, lo, hi)
        z += h
        course += 1


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    front_holes = [kit.rect(door[0], door[1], -0.05, door[3])] + [kit.rect(*w) for w in windows + upper_windows]
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), front_holes, wall_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, -1.5, wall_top, wall_t, [door] + windows + upper_windows)
    back_open = [back_door, store_door] + back_windows
    back_holes = [kit.rect(o[0], o[1], -0.05 if o[2] < 0.1 else o[2], o[3]) for o in back_open]
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), back_holes, wall_t)
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, -1.5, wall_top, wall_t, back_open)
    outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
    for frame, openings, tag in ((left, left_windows, "left"), (right, right_windows, "right")):
        kit.wall(shell, stone, frame, outline, [kit.rect(*w) for w in openings], wall_t)
        kit.wall_boxes(b, "rock", tag, frame, -hy, hy, -1.5, wall_top, wall_t, openings)
    bd.gable_cols(b, "gable", -hx, -ix, gable, wall_top, 0.0)
    bd.gable_cols(b, "gable", ix, hx, gable, wall_top, 0.0)
    wide_front = kit.facade("front", hx, hy)
    tk.render_skin(shell, wide_front, -hx, hx, wall_top - 0.02, upper_windows, rng, 5, render, 0.02, 1, (3.79, 3.8), 0.0)
    frame_block(shell, render, wide_front, -hx, hx, wall_top - 0.32, wall_top - 0.18, -0.06, 0.0, 0.006)
    frame_block(shell, render, wide_front, -hx, hx, wall_top - 0.18, wall_top - 0.02, -0.03, 0.0, 0.004)
    for w in upper_windows:
        tk.architrave(shell, front, w, render, 0.1, 0.025, 0.14, False)
    wide_back = kit.facade("back", hx, hy)
    tk.render_skin(shell, wide_back, -hx, hx, wall_top - 0.35, back_open, rng, 7, render, 0.018, 2, (0.45, 1.0), 0.6)
    bd.damp_band(shell, wide_back, -hx, hx, rng, 0.4, 1.1, "granite_rubble_damp", -0.2, 0.003, [(o[0] - 0.05, o[1] + 0.05) for o in (back_door, store_door)])
    block(shell, stone, V(-ix, -hy, -1.5), V(ix, fy, -0.05), 0.0, "world")
    quoins(shell, rng, wall_top)
    return wall_top


def openings(b, parts, rng):
    joinery = parts["joinery"]
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    states = [(0.45, 0.3, 0.0, False, False), (0.2, 0.35, 0.0, False, False), (0.0, 0.0, 0.8, True, False), (0.3, 0.3, 0.0, False, True)]
    for w, (whole, shard, lift, climb, boarded) in zip(windows, states):
        tk.sash(b, parts, front, w, wall_t, rng, trim, 0.1, lift, whole, shard, 2, 2, None, None, None, climb, boarded, "glass", "window", None, "timber_beam")
    upper_states = [(0.0, 0.4, False), (0.3, 0.2, False), (0.0, 0.3, True), (0.15, 0.4, False), (0.0, 0.25, False)]
    for w, (lift, whole, boarded) in zip(upper_windows, upper_states):
        tk.sash(b, parts, front, w, wall_t, rng, trim, 0.1, lift, whole, 0.3, 2, 1, render, dressed, None, False, boarded)
    for w in left_windows:
        tk.sash(b, parts, left, w, wall_t, rng, trim, 0.1, 0.0, 0.25, 0.35, 2, 1, None, dressed, None, False, False, "glass", "window", dressed, None)
    for index, w in enumerate(right_windows):
        tk.sash(b, parts, right, w, wall_t, rng, trim, 0.1, 0.0, 0.3, 0.3, 2, 1, None, dressed, None, False, index == 1, "glass", "window", dressed, None)
    back_states = [(0.0, 0.5, False), (0.0, 0.2, False), (0.2, 0.3, False), (0.0, 0.5, False), (0.1, 0.25, False), (0.0, 0.3, False)]
    for w, (lift, whole, boarded) in zip(back_windows, back_states):
        tk.sash(b, parts, back, w, wall_t, rng, trim, 0.1, lift, whole, 0.3, 2, 1, render, dressed, None, False, boarded, "glass", "window", None, None)
    a0, a1, z0, z1 = back_door
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, "painted_wood_bauxite", rng, "high", 98.0, "ledged", True, 0.0, 0.06, 3.0, trim)
    block(parts["shell"], dressed, V(-a1 - 0.08, hy - 0.04, -0.3), V(-a0 + 0.08, hy + 0.34, -0.06), 0.012)
    tk.col(b, "rock", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
    tk.col(b, "rock", "step", -a1 - 0.08, -a0 + 0.08, hy, hy + 0.34, -0.6, -0.06)
    a0, a1, z0, z1 = store_door
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, paint, rng, "high", 95.0, "ledged", True, 0.0, 0.06, 2.0, trim)
    block(parts["shell"], "concrete", V(-a1 - 0.1, hy - 0.04, -0.3), V(-a0 + 0.1, hy + 0.5, -0.1), 0.01)
    tk.col(b, "rock", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
    tk.col(b, "rock", "step", -a1 - 0.1, -a0 + 0.1, hy, hy + 0.5, -0.6, -0.1)


def ground_walls(b, parts, rng):
    joinery = parts["joinery"]
    floors = parts["floors"]
    servery_zone = (-0.6, 3.6, -0.85, partition[0])
    tk.board_floor(floors, -ix, ix, fy, partition[0], 0.0, rng, "x", [servery_zone], "floorboards", 0.03, 0.1, (0.16, 0.22), (0.45,))
    tk.tile_floor(floors, "town_quarry", -0.6, 3.6, -0.85, partition[0], 0.0, 0.02)
    tk.tile_floor(floors, "town_quarry", -ix, toilet_wall[0], partition[0], by, 0.0, 0.02)
    tk.tile_floor(floors, "town_tiles", toilet_wall[1], store_wall[0], partition[1], by, 0.0, 0.02)
    tk.tile_floor(floors, "concrete", store_wall[1], ix, partition[0], by, 0.0, 0.03)
    tk.col(b, "wood", "ground", -ix, ix, fy, partition[0], -0.3, 0.0)
    tk.col(b, "rock", "ground", -ix, ix, partition[0], by, -0.3, 0.0)
    thickness = partition[1] - partition[0]
    part_plane = interior_wall(b, parts, V(0.0, partition[1], 0.0), V(0.0, 1.0, 0.0), -ix, ix, 0.0, c1, thickness, [flip(stair_door), flip(passage_door), flip(servery_door)], "partition")
    a0, a1, z0, z1 = flip(stair_door)
    tk.door_unit(joinery, part_plane, a0, a1, 0.0, 2.2, thickness, paint, rng, "high", 96.0, "panel")
    a0, a1, z0, z1 = flip(passage_door)
    tk.door_unit(joinery, part_plane, a0, a1, 0.0, 2.2, thickness, paint, rng, "high", -95.0, "panel")
    a0, a1, z0, z1 = flip(servery_door)
    tk.door_unit(joinery, part_plane, a0, a1, 0.0, 2.2, thickness, paint, rng, "low", -97.0, "ledged")
    for d in (stair_door, passage_door, servery_door):
        block(floors, "timber_beam", V(d[0], partition[0], -0.02), V(d[1], partition[1], 0.005), 0.003)
    interior_wall(b, parts, V(enclosure[1], 0.0, 0.0), V(1.0, 0.0, 0.0), partition[1], by, 0.0, c1, enclosure[1] - enclosure[0], [], "enclosure")
    toilets = interior_wall(b, parts, V(toilet_wall[1], 0.0, 0.0), V(1.0, 0.0, 0.0), partition[1], by, 0.0, c1, 0.1, [ladies_door, gents_door], "toilet_wall")
    tk.door_unit(joinery, toilets, ladies_door[0], ladies_door[1], 0.0, 2.2, 0.1, trim, rng, "low", -100.0, "panel")
    tk.door_unit(joinery, toilets, gents_door[0], gents_door[1], 0.0, 2.2, 0.1, trim, rng, "high", -85.0, "panel")
    interior_wall(b, parts, V(0.0, toilet_split[1], 0.0), V(0.0, 1.0, 0.0), -store_wall[0], -toilet_wall[1], 0.0, c1, 0.1, [], "toilet_split")
    interior_wall(b, parts, V(store_wall[1], 0.0, 0.0), V(1.0, 0.0, 0.0), partition[1], by, 0.0, c1, 0.1, [], "store_wall")
    tk.stair_flight(b, parts, stair_x[0], stair_x[1], stair_foot, 0.0, stair_run, f1, stair_steps, rng, 1.0, "floorboards", trim, "town_carpet", "town_brass")
    block(floors, "floorboards", V(stair_x[0], partition[1], -0.01), V(stair_x[1], stair_foot, 0.012), 0.0, "board")


def upper_walls(b, parts, rng):
    joinery = parts["joinery"]
    floors = parts["floors"]
    tk.board_floor(floors, -ix, ix, fy, by, f1, rng, "x", [well, (landing_wall[1], bath_split[0], back_rooms[1], by), (kitchen_split[1], ix, back_rooms[1], by)], "floorboards", 0.03, 0.1, (0.16, 0.22), (0.52,))
    tk.tile_floor(floors, "town_lino", landing_wall[1], bath_split[0], back_rooms[1], by, f1 + 0.004, 0.02)
    tk.tile_floor(floors, "town_lino", kitchen_split[1], ix, back_rooms[1], by, f1 + 0.004, 0.02)
    block(floors, "town_carpet", V(-4.2, front_rooms[1] + 0.12, f1 + 0.004), V(5.3, back_rooms[0] - 0.12, f1 + 0.012), 0.0, "world")
    block(floors, "town_carpet", V(-4.15, back_rooms[0] - 0.12, f1 + 0.004), V(-3.35, 4.85, f1 + 0.012), 0.0, "world")
    tk.floor_cols(b, "wood", "upper", -ix, ix, fy, by, c1, f1, [well])
    tk.col(b, "wood", "attic", -ix, ix, fy, by, c2, c2 + 0.25)
    block(floors, trim, V(well[1], well[2], c1 - 0.01), V(well[1] + 0.03, well[3], f1 + 0.012), 0.002, "board")
    block(floors, trim, V(well[0], well[2] - 0.03, c1 - 0.01), V(well[1] + 0.03, well[2], f1 + 0.012), 0.002, "board")
    block(floors, trim, V(well[0], well[3], c1 - 0.01), V(well[1] + 0.03, well[3] + 0.03, f1 + 0.012), 0.002, "board")
    front_plane = interior_wall(b, parts, V(0.0, front_rooms[1], 0.0), V(0.0, 1.0, 0.0), -ix, ix, f1, c2, 0.1, [flip(living_door), flip(bedroom_door)], "front_rooms")
    a0, a1, z0, z1 = flip(living_door)
    tk.door_unit(joinery, front_plane, a0, a1, f1, 2.2, 0.1, trim, rng, "high", 92.0, "panel")
    a0, a1, z0, z1 = flip(bedroom_door)
    tk.door_unit(joinery, front_plane, a0, a1, f1, 2.2, 0.1, trim, rng, "low", 86.0, "panel")
    back_plane = interior_wall(b, parts, V(0.0, back_rooms[1], 0.0), V(0.0, 1.0, 0.0), -ix, -landing_wall[0], f1, c2, 0.1, [flip(bath_door), flip(bed2_door), flip(kitchen_door)], "back_rooms")
    for d, hinge, angle in ((bath_door, "high", -90.0), (bed2_door, "high", -84.0), (kitchen_door, "high", -95.0)):
        a0, a1, z0, z1 = flip(d)
        tk.door_unit(joinery, back_plane, a0, a1, f1, 2.2, 0.1, trim, rng, hinge, angle, "panel")
    interior_wall(b, parts, V(landing_wall[1], 0.0, 0.0), V(1.0, 0.0, 0.0), back_rooms[0], by, f1, c2, 0.1, [], "landing_wall")
    interior_wall(b, parts, V(living_split[1], 0.0, 0.0), V(1.0, 0.0, 0.0), fy, front_rooms[0], f1, c2, 0.1, [], "living_split")
    interior_wall(b, parts, V(bath_split[1], 0.0, 0.0), V(1.0, 0.0, 0.0), back_rooms[1], by, f1, c2, 0.1, [], "bath_split")
    interior_wall(b, parts, V(kitchen_split[1], 0.0, 0.0), V(1.0, 0.0, 0.0), back_rooms[1], by, f1, c2, 0.1, [], "kitchen_split")
    bd.balustrade(b, joinery, V(well[1] + 0.02, well[2] - 0.02, f1), V(well[1] + 0.02, 3.9, f1), rng, 0.92, 0.12, "timber_beam", trim, 0.1, (True, True), True, "well")
    bd.balustrade(b, joinery, V(well[0], well[2] - 0.02, f1), V(well[1] + 0.02, well[2] - 0.02, f1), rng, 0.92, 0.12, "timber_beam", trim, 0.1, (False, False), True, "well")


def breasts(b, parts, rng):
    interior = parts["interior"]
    left_bar = tk.chimney_breast(b, interior, -ix, 1.0, -3.4, -1.6, 0.0, c1, 0.9, 0.85, rng, depth=0.5)
    tk.fireplace_light(b, interior, V(left_bar, -2.5, 0.0), V(1.0, 0.0, 0.0), rng, 1.6, "timber_beam", "town_quarry", False)
    right_bar = tk.chimney_breast(b, interior, ix, -1.0, -3.4, -1.6, 0.0, c1, 0.7, 0.72, rng, depth=0.42)
    tk.fireplace_light(b, interior, V(right_bar, -2.5, 0.0), V(-1.0, 0.0, 0.0), rng, 1.3, "timber_beam", "kitchen_tiles", False)
    living = tk.chimney_breast(b, interior, -ix, 1.0, -3.3, -1.7, f1, c2, 0.6, 0.66, rng, depth=0.4)
    tk.fireplace_light(b, interior, V(living, -2.5, f1), V(1.0, 0.0, 0.0), rng, 1.25, trim, "kitchen_tiles", False)
    bedroom = tk.chimney_breast(b, interior, ix, -1.0, -3.2, -1.8, f1, c2, 0.56, 0.6, rng, depth=0.36)
    tk.fireplace_light(b, interior, V(bedroom, -2.5, f1), V(-1.0, 0.0, 0.0), rng, 1.0, trim, "kitchen_tiles", False, False)
    kitchen = tk.chimney_breast(b, interior, ix, -1.0, 2.5, 4.1, f1, c2, 1.32, 1.4, rng, depth=0.55)
    tp.gas_cooker(b, interior, parts["clutter"], V(ix - 0.34, 3.3, f1), -math.pi * 0.5, rng)
    block(interior, "timber_beam", V(kitchen - 0.2, 2.35, f1 + 1.62), V(kitchen + 0.02, 4.25, f1 + 1.68), 0.006)
    return left_bar, right_bar, living, bedroom, kitchen


def world_back(o):
    return (-o[1], -o[0], o[2], o[3])


def finishes(parts, rng, faces):
    left_bar, right_bar, living, bedroom, kitchen = faces
    interior = parts["interior"]
    stripe = ("paper", "town_stripe", 2, 1)
    floral = ("paper", "wallpaper_faded", 1, 1)
    plaster = ("plaster", 1)
    dado = ("panel", 1.15, paint, ("paper", "town_stripe", 1, 1))
    tiled = ("tiles", 1.3, "kitchen_tiles", plaster)
    left_ground = world_back(left_windows[0])
    tk.room(parts, rng, -ix, ix, fy, partition[0], 0.0, c1, {"front": dado, "left": dado, "right": dado, "back": dado}, {"front": [door] + windows, "left": [left_ground], "right": [right_windows[0]], "back": [stair_door, passage_door, servery_door]}, "timber_beam", None, True, 2, (), {"left": [(-3.4, -1.6, 0.0, c1)], "right": [(-3.4, -1.6, 0.0, c1)], "back": [(-0.65, 3.65, 0.0, c1)]}, 6, 0.0)
    tk.wall_finish(interior, "left", dado, left_bar, 0.0, -3.4, -1.6, 0.0, c1, [(-3.3, -1.7, 0.0, 1.16)], rng)
    tk.wall_finish(interior, "right", dado, 0.0, right_bar, -3.4, -1.6, 0.0, c1, [(-3.15, -1.85, 0.0, 1.16)], rng)
    for x in (-4.2, -1.4, 1.4, 4.2):
        block(interior, "timber_beam", V(x - 0.1, fy, c1 - 0.24), V(x + 0.1, partition[0], c1 + 0.015), 0.01)
    tk.wall_finish(interior, "left", plaster, -ix, enclosure[0], partition[1], well[2], 0.0, c1, [], rng)
    tk.wall_finish(interior, "left", plaster, -ix, enclosure[0], well[2], by, 0.0, c2, [], rng)
    tk.wall_finish(interior, "back", plaster, -ix, enclosure[0], partition[1], by, 0.0, f1, [], rng)
    tk.wall_finish(interior, "front", plaster, -ix, enclosure[0], partition[1], by, 0.0, c1, [stair_door], rng)
    tk.wall_finish(interior, "right", plaster, -ix, enclosure[0], partition[1], by, 0.0, c1, [], rng)
    tk.room(parts, rng, enclosure[1], toilet_wall[0], partition[1], by, 0.0, c1, {"front": plaster, "back": plaster, "left": plaster, "right": plaster}, {"front": [passage_door], "back": [world_back(back_door)], "right": [ladies_door, gents_door]}, paint, None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, toilet_wall[1], store_wall[0], partition[1], toilet_split[0], 0.0, c1, {"front": tiled, "back": tiled, "left": tiled, "right": tiled}, {"left": [ladies_door]}, None, None, True, 0, (), None, 2)
    tk.room(parts, rng, toilet_wall[1], store_wall[0], toilet_split[1], by, 0.0, c1, {"front": tiled, "back": tiled, "left": tiled, "right": tiled}, {"left": [gents_door], "back": [world_back(back_windows[0])]}, None, None, True, 0, (), None, 2)
    tk.room(parts, rng, store_wall[1], ix, partition[1], by, 0.0, c1, {"front": ("plaster", 2), "back": ("plaster", 2), "left": plaster, "right": ("plaster", 2)}, {"front": [servery_door], "back": [world_back(back_windows[1]), world_back(store_door)], "right": [right_windows[1]]}, None, None, True, 1, (), None, 4)
    tk.room(parts, rng, -ix, living_split[0], fy, front_rooms[0], f1, c2, {"front": floral, "left": floral, "right": floral, "back": floral}, {"front": upper_windows[:3], "back": [living_door]}, trim, f1 + 2.15, True, 1, (), {"left": [(-3.3, -1.7, f1, c2)]}, 4, 0.0)
    tk.wall_finish(interior, "left", floral, living, 0.0, -3.3, -1.7, f1, c2, [(-3.12, -1.88, f1, f1 + 1.16)], rng)
    tk.room(parts, rng, living_split[1], ix, fy, front_rooms[0], f1, c2, {"front": stripe, "left": stripe, "right": stripe, "back": stripe}, {"front": upper_windows[3:], "back": [bedroom_door]}, trim, f1 + 2.15, True, 0, (), {"right": [(-3.2, -1.8, f1, c2)]}, 2, 0.0)
    tk.wall_finish(interior, "right", stripe, 0.0, bedroom, -3.2, -1.8, f1, c2, [(-3.0, -2.0, f1, f1 + 1.16)], rng)
    tk.room(parts, rng, -ix, ix, front_rooms[1], back_rooms[0], f1, c2, {"front": stripe, "left": stripe, "right": stripe}, {"front": [living_door, bedroom_door]}, trim, None, True, 0, (), None, 2, 0.0)
    tk.wall_finish(interior, "back", stripe, landing_wall[0], ix, front_rooms[1], back_rooms[0], f1, c2, [bath_door, bed2_door, kitchen_door], rng)
    tk.skirting(interior, "back", landing_wall[0], ix, front_rooms[1], back_rooms[0], f1, [bath_door, bed2_door, kitchen_door], trim, 0.2, 0.022, 0.012, 0.0)
    tk.wall_finish(interior, "right", stripe, -ix, landing_wall[0], back_rooms[0], by, f1, c2, [], rng)
    tk.skirting(interior, "right", -ix, landing_wall[0], back_rooms[0], by, f1, [], trim, 0.2, 0.022, 0.012, 0.0)
    tk.wall_finish(interior, "back", stripe, -ix, landing_wall[0], back_rooms[0], by, f1, c2, [world_back(back_windows[2])], rng)
    tk.ceiling_skin(interior, c2 + 0.02, -ix, landing_wall[0], back_rooms[0], by, rng, 0)
    tk.room(parts, rng, landing_wall[1], bath_split[0], back_rooms[1], by, f1, c2, {"front": tiled, "back": tiled, "left": tiled, "right": tiled}, {"front": [bath_door], "back": [world_back(back_windows[3])]}, None, None, True, 0, (), None, 2)
    tk.room(parts, rng, bath_split[1], kitchen_split[0], back_rooms[1], by, f1, c2, {"front": floral, "back": floral, "left": floral, "right": floral}, {"front": [bed2_door], "back": [world_back(back_windows[4])]}, trim, None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, kitchen_split[1], ix, back_rooms[1], by, f1, c2, {"front": tiled, "back": tiled, "left": tiled, "right": tiled}, {"front": [kitchen_door], "back": [world_back(back_windows[5])]}, "painted_wood_green", None, True, 0, (), {"right": [(2.5, 4.1, f1, c2)]}, 2, 0.0)
    tk.wall_finish(interior, "right", ("tiles", 1.4, "kitchen_tiles", ("plaster", 1)), 0.0, kitchen, 2.5, 4.1, f1, c2, [(2.64, 3.96, f1, f1 + 1.4)], rng)


def bar_room(b, parts, rng, faces):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    left_bar, right_bar = faces[0], faces[1]
    tp.settle_light(b, furniture, V(-4.8, -3.8, 0.0), math.pi, rng, 1.4)
    tp.settle_light(b, furniture, V(-4.8, -1.2, 0.0), 0.0, rng, 1.4)
    tp.pub_table(b, furniture, V(-4.0, -2.5, 0.0), rng, 0.3, 0.62)
    tp.pint_glass(clutter, V(-3.95, -2.45, 0.62), rng)
    tp.fender(clutter, V(left_bar + 0.47, -3.25, 0.02), V(left_bar + 0.47, -1.75, 0.02), rng)
    tp.fire_irons(clutter, V(left_bar + 0.25, -3.4 + 0.12, 0.0), rng)
    tables = [(V(-2.6, -4.2, 0.0), 2), (V(-2.2, -2.0, 0.0), 2), (V(2.1, -4.15, 0.0), 3), (V(4.1, -2.65, 0.0), 2)]
    for center, seats in tables:
        tp.pub_table(b, furniture, center, rng)
        start = rng.uniform(0.0, tau)
        for k in range(seats):
            angle = start + tau * k / seats + rng.uniform(-0.3, 0.3)
            position = center + V(math.cos(angle), math.sin(angle), 0.0) * 0.62
            if rng.random() < 0.18:
                tp.chair_light(furniture, position, rng.uniform(0.0, tau), rng, fallen=True)
            elif rng.random() < 0.3:
                tp.stool_light(furniture, position, rng, False, 0.48)
            else:
                tp.chair_light(furniture, position, tk.facing(position, center) + rng.uniform(-0.3, 0.3), rng)
        for index in range(rng.randint(1, 2)):
            tp.pint_glass(clutter, center + V(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0.72), rng, rng.random() < 0.3)
    for index in range(4):
        p = V(-2.2, -2.0, 0.72) + V(rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.0)
        tp.sheet(clutter, p, rng.uniform(0.0, tau), 0.064, 0.09, tp.pr("card_" + str(index)), rng, 0.0, 0.002 + index * 0.0005)
    tp.table_light(furniture, 1.6, -2.35, 0.0, 1.1, 0.7, 0.74, rng, "timber_beam")
    tk.col(b, "wood", "table", 1.05, 2.15, -2.7, -2.0, 0.0, 0.74)
    for position in (V(0.75, -2.35, 0.0), V(2.45, -2.35, 0.0), V(1.6, -3.0, 0.0)):
        tp.chair_light(furniture, position, tk.facing(position, V(1.6, -2.35, 0.0)), rng)
    tp.sheet(clutter, V(1.5, -2.3, 0.745), 0.3, 0.36, 0.48, tp.pr("newspaper"), rng, 0.0)
    tp.pint_glass(clutter, V(1.9, -2.5, 0.74), rng)
    tp.cask_light(furniture, V(-1.3, -4.5, 0.0), rng, 0.3, 0.95, rng.uniform(0.0, tau), False)
    tk.col(b, "wood", "cask", -1.6, -1.0, -4.8, -4.2, 0.0, 0.95)
    tp.pint_glass(clutter, V(-1.25, -4.45, 0.95), rng)
    tp.pint_glass(clutter, V(-1.4, -4.6, 0.95), rng, True)
    for x, fallen in ((-0.15, False), (0.65, False), (1.45, True), (2.3, False)):
        tp.stool_light(furniture, V(x + rng.uniform(-0.08, 0.08), -1.27 + rng.uniform(-0.05, 0.05), 0.0), rng, fallen)
    tp.dartboard(interior, V(4.6, partition[0] - 0.002, 1.73), V(0.0, -1.0, 0.0), rng)
    block(clutter, "town_brass", V(4.3, -1.39, 0.0), V(4.9, -1.36, 0.008))
    block(interior, "soot", V(5.0, partition[0] - 0.02, 1.35), V(5.45, partition[0] - 0.002, 1.95), 0.004)
    tp.enamel_sign(interior, V(4.6, partition[0] - 0.02, 2.6), V(0.0, -1.0, 0.0), 0.9, 0.34, "enamel_smoke", rng, 0.02)
    tp.framed(interior, V(-2.25, partition[0] - 0.006, 1.6), V(0.0, -1.0, 0.0), 0.92, 0.36, tp.pr("menu"), rng, "timber_beam")
    tp.framed(interior, V(-1.25, partition[0] - 0.006, 1.75), V(0.0, -1.0, 0.0), 0.7, 0.36, tp.pr("harbour"), rng, "town_brass")
    tp.wall_clock(interior, V(-1.25, partition[0] - 0.015, 2.55), V(0.0, -1.0, 0.0), rng, 0.18)
    tp.framed(interior, V(-ix + 0.006, -0.45, 1.85), V(1.0, 0.0, 0.0), 0.56, 0.4, tp.pr("ship"), rng, "timber_beam", 0.03)
    tp.framed(interior, V(-3.05, fy + 0.006, 1.7), V(0.0, 1.0, 0.0), 0.32, 0.42, tp.pr("portrait_a"), rng, "timber_beam", -0.04)
    tp.framed(interior, V(3.05, fy + 0.006, 1.75), V(0.0, 1.0, 0.0), 0.5, 0.3, tp.pr("seascape"), rng, "timber_beam", 0.02)
    tp.framed(interior, V(ix - 0.006, -0.6, 1.7), V(-1.0, 0.0, 0.0), 0.3, 0.4, tp.pr("portrait_b"), rng, "timber_beam", 0.05)
    tp.enamel_sign(interior, V(ix - 0.02, -4.15, 2.75), V(-1.0, 0.0, 0.0), 0.8, 0.3, "enamel_tea", rng, -0.03)
    tp.wall_sheet(interior, V(-1.2, partition[0] - 0.014, 1.15), V(0.0, -1.0, 0.0), "police_notice", rng, 1.0, -0.02)
    for x, y in ((-3.0, -2.6), (0.0, -3.2), (3.0, -2.6)):
        tk.pendant(b, interior, V(x, y, c1), rng, "town_metal", 0.6, "warm", 8)
    for index in range(3):
        tp.label_bottle(clutter, V(rng.uniform(-4.0, 4.5), rng.uniform(-4.6, -1.6), 0.0), rng, rng.choice(("ale", "stout", "gin", "cider")), True, rng.random() < 0.4)
    for index in range(2):
        tp.pint_glass(clutter, V(rng.uniform(-3.5, 3.5), rng.uniform(-4.5, -1.6), 0.0), rng, True, rng.random() < 0.5)
    tk.chips(parts["debris"], "glass_dirty", 1.0, 2.8, -4.9, -4.2, 0.0, 6, rng, (0.02, 0.06), (0.003, 0.004))
    tp.papers(parts["debris"], -4.0, 4.5, -4.7, -1.6, 0.0, 5, rng)
    tp.debris_field(parts, -5.2, 5.2, -4.8, -1.5, 0.0, rng, 6, 0, 0, 6)


def servery(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.pub_counter(b, furniture, V(1.2, -0.55, 0.0), 0.0, 3.6, rng, 0.6, 1.05, "timber_beam", paint, (True, False))
    tp.pub_counter(b, furniture, V(3.3, 0.075, 0.0), math.pi * 0.5, 1.85, rng, 0.6, 1.05, "timber_beam", paint, (True, False))
    for index, x in enumerate((0.2, 0.5, 0.8, 1.1)):
        tp.beer_pump(clutter, V(x, -0.5, 1.05), 0.0, rng, ("ale", "stout", "ale", "cider")[index], rng.uniform(0.1, 0.3))
    tp.till(clutter, V(2.45, -0.42, 1.05), math.pi, rng)
    tp.label_jar(clutter, V(-0.35, -0.55, 1.05), rng, "pickles", 0.07, 0.24)
    for x, y, tipped in ((1.5, -0.68, False), (1.75, -0.6, True), (3.3, 0.3, True)):
        tp.pint_glass(clutter, V(x, y, 1.05), rng, tipped)
    for k in range(5):
        tp.pint_glass(clutter, V(-0.35 + k * 0.6 + rng.uniform(-0.05, 0.05), -0.42, 0.545), rng, rng.random() < 0.15)
    for k in range(3):
        tp.label_bottle(clutter, V(-0.3 + k * 0.9 + rng.uniform(-0.1, 0.1), -0.4, 0.145), rng, rng.choice(("ale", "stout")), rng.random() < 0.3)
    tp.wall_shelves(b, furniture, clutter, V(-0.55, partition[0] - 0.005, 0.0), V(1.65, partition[0] - 0.005, 0.0), V(0.0, -1.0, 0.0), [0.15, 0.95, 1.45, 1.95], rng, ("bottle", "bottle", "bottle", "box", "gap"), 0.32)
    tp.wall_mirror(interior, V(0.55, partition[0] - 0.002, 2.68), V(0.0, -1.0, 0.0), 1.9, 0.56, rng, "timber_beam", True)
    b.loot("food", V(0.2, 0.83, 0.95))
    tp.bucket_light(clutter, V(2.75, -0.02, 0.0), rng, "rusty_metal", False)
    bd.long_tool(clutter, V(2.55, 0.05, 0.0), V(2.62, 0.45, 1.35), "broom", rng)
    tp.bottle_crate(clutter, V(2.55, -0.42, 0.145), 0.05, rng, "ale")
    tk.pendant(b, interior, V(1.2, 0.35, c1), rng, "glass_dirty", 0.45, "warm", 8)
    tk.chips(parts["debris"], "glass_dirty", -0.4, 2.8, -0.2, 0.6, 0.0, 5, rng, (0.02, 0.06), (0.003, 0.004))


def back_zone(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.stillage(b, furniture, 4.62, 5.45, 1.6, 4.35, rng)
    for y in (1.95, 2.65, 3.35, 4.02):
        if rng.random() < 0.85:
            tp.cask_light(furniture, V(5.03, y, 0.3), rng, 0.28, 0.72)
            rod(clutter, "town_brass", V(4.67, y, 0.56), V(4.55, y, 0.56), 0.012, 6)
            rod(clutter, "town_brass", V(4.55, y, 0.56), V(4.55, y, 0.5), 0.01, 5)
    tk.col(b, "wood", "casks", 4.6, ix, 1.6, 4.35, 0.0, 0.88)
    for center, radius, height in ((V(3.15, 4.68, 0.0), 0.24, 0.6), (V(2.62, 4.72, 0.0), 0.24, 0.6)):
        tp.cask_light(furniture, center, rng, radius, height, rng.uniform(0.0, tau), False)
    tk.col(b, "wood", "kegs", 2.35, 3.4, 4.4, by, 0.0, 0.6)
    tp.crate_light(clutter, V(2.0, 3.0, 0.0), (0.62, 0.48, 0.42), 0.25, rng)
    local_block(clutter, "timber_planks_weathered", kit.turned(V(2.45, 3.35, 0.0), 0.6) @ kit.Matrix.Rotation(1.2, 4, 'X'), -0.31, 0.31, -0.24, 0.24, 0.0, 0.018, 0.0, "board")
    b.loot("box", V(2.0, 3.0, 0.42))
    tk.col(b, "wood", "crate", 1.65, 2.35, 2.7, 3.3, 0.0, 0.42)
    for center, yaw in ((V(0.75, 4.75, 0.0), 0.05), (V(0.75, 4.75, 0.28), -0.1), (V(1.3, 4.75, 0.0), -0.05)):
        tp.bottle_crate(clutter, center, yaw, rng, rng.choice(("ale", "stout")))
    tk.col(b, "wood", "crates", 0.5, 1.55, 4.55, by, 0.0, 0.56)
    tp.wall_sheet(interior, V(enclosure[1] + 0.012, 4.2, 1.55), V(1.0, 0.0, 0.0), "poster", rng, 1.0, 0.03)
    tp.crate_light(clutter, V(1.5, 1.6, 0.0), (0.55, 0.42, 0.38), 0.3, rng)
    tk.col(b, "wood", "crate", 1.22, 1.78, 1.38, 1.82, 0.0, 0.38)
    tp.wall_shelves(b, furniture, clutter, V(store_wall[1] + 0.01, 1.5, 0.0), V(store_wall[1] + 0.01, 3.4, 0.0), V(1.0, 0.0, 0.0), [0.3, 0.9, 1.5], rng, ("box", "box", "gap", "can"), 0.38)
    tp.sack_truck(furniture, V(2.1, by - 0.31, 0.0), 0.0, rng)
    tk.col(b, "metal", "truck", 1.82, 2.38, by - 0.42, by, 0.0, 1.3)
    block(parts["floors"], "timber_planks_weathered", V(3.4, 2.3, 0.0), V(4.3, 3.1, 0.014), 0.0, "board")
    emit(clutter, kit.geo_lathe([(0.035, -0.005), (0.045, 0.0), (0.035, 0.005)], 6), "rusty_metal", kit.Matrix.Translation(V(3.85, 2.45, 0.02)), "given", True)
    tk.pendant(b, interior, V(2.9, 3.0, c1), rng, "glass_dirty", 0.5, "cold", 8)
    tk.chips(parts["debris"], "plaster_interior", 0.5, 4.4, 1.3, 4.6, 0.0, 4, rng)
    tp.papers(parts["debris"], 0.6, 4.0, 1.3, 4.0, 0.0, 3, rng, ("newspaper", "card"))
    tp.urinal_trough(b, furniture, -2.8, -1.15, by, -1.0, rng)
    tp.toilet(b, furniture, V(-0.22, 4.35, 0.0), -math.pi * 0.5, rng, 2.0, False, 8, False)
    tp.basin(b, furniture, V(-1.75, toilet_split[1] + 0.22, 0.0), math.pi, rng, 8)
    tp.wall_mirror(interior, V(-1.75, toilet_split[1] + 0.005, 1.5), V(0.0, 1.0, 0.0), 0.42, 0.56, rng)
    tk.pendant(b, interior, V(-1.4, 4.05, c1), rng, "glass_dirty", 0.4, "cold", 8)
    tp.toilet(b, furniture, V(-0.22, 2.25, 0.0), -math.pi * 0.5, rng, 2.0, True, 8, False)
    tp.basin(b, furniture, V(-1.25, partition[1] + 0.22, 0.0), math.pi, rng, 8)
    tp.wall_mirror(interior, V(-1.25, partition[1] + 0.005, 1.5), V(0.0, 1.0, 0.0), 0.42, 0.56, rng)
    tk.pendant(b, interior, V(-1.4, 2.05, c1), rng, "glass_dirty", 0.4, "cold", 8)
    tk.chips(parts["debris"], "plaster_interior", -2.8, 0.0, 1.3, 4.7, 0.0, 4, rng)
    bd.coat_rail(interior, clutter, V(enclosure[1], 2.3, 1.7), V(enclosure[1], 3.1, 1.7), V(1.0, 0.0, 0.0), rng, 1)
    tp.bucket_light(clutter, V(-3.35, 4.7, 0.0), rng, "town_paint_red", False)
    tp.wall_sheet(interior, V(toilet_wall[0] - 0.012, 3.05, 1.6), V(-1.0, 0.0, 0.0), "notice", rng, 1.0, 0.02)
    tk.pendant(b, interior, V(-3.65, 3.0, c1), rng, "town_metal", 0.4, "warm", 8)
    tp.framed(interior, V(-ix + 0.006, 3.2, 2.7), V(1.0, 0.0, 0.0), 0.5, 0.36, tp.pr("ship"), rng, "timber_beam", -0.03)
    tp.papers(parts["debris"], -4.1, -3.2, 1.4, 4.8, 0.0, 3, rng, ("letter", "envelope", "newspaper"))


def upper_rooms(b, parts, rng, faces):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    living, bedroom = faces[2], faces[3]
    hearth = V(living + 0.3, -2.5, f1)
    tp.mantel_set(clutter, V(living + 0.06, -3.0, f1 + 1.16), V(0.0, 1.0, 0.0), V(1.0, 0.0, 0.0), 1.0, rng)
    tp.wall_mirror(interior, V(living + 0.006, -2.5, f1 + 1.75), V(1.0, 0.0, 0.0), 0.9, 0.66, rng, "town_brass", True)
    tp.fender(clutter, V(living + 0.42, -3.05, f1 + 0.02), V(living + 0.42, -1.95, f1 + 0.02), rng)
    tp.sofa_light(b, furniture, V(-3.3, -2.5, f1), -math.pi * 0.5, rng, 1.7)
    tp.armchair_light(b, furniture, V(-4.35, -3.95, f1), tk.facing(V(-4.35, -3.95, f1), hearth), rng)
    tp.chair_light(furniture, V(-4.4, -1.15, f1), tk.facing(V(-4.4, -1.15, f1), hearth), rng)
    bd.rug(clutter, V(-4.2, -2.5, f1), 1.8, 2.2, 0.0, rng, "town_carpet")
    tp.sideboard(b, furniture, clutter, V(-4.3, front_rooms[0] - 0.28, f1), 0.0, rng, 1.4)
    tp.wireless(clutter, V(-3.9, front_rooms[0] - 0.3, f1 + 0.9), 0.0, rng)
    tp.vase(clutter, V(-4.7, front_rooms[0] - 0.25, f1 + 0.9), rng)
    tp.framed(interior, V(-4.3, front_rooms[0] - 0.006, f1 + 1.75), V(0.0, -1.0, 0.0), 0.7, 0.35, tp.pr("harbour"), rng, "town_brass")
    tp.table_light(furniture, -1.1, -3.7, f1, 1.1, 0.8, 0.74, rng)
    tk.col(b, "wood", "table", -1.65, -0.55, -4.1, -3.3, f1, f1 + 0.74)
    for position in (V(-1.1, -3.05, f1), V(-1.95, -3.7, f1)):
        tp.chair_light(furniture, position, tk.facing(position, V(-1.1, -3.7, f1)), rng)
    tp.tray_items(clutter, V(-1.4, -3.6, f1 + 0.74), V(1.0, 0.0, 0.0), rng, 3)
    tp.bookcase(b, furniture, clutter, V(living_split[0] - 0.16, -1.3, f1), -math.pi * 0.5, rng, 0.85, 1.7, 0.3, "timber_beam", 0.55)
    tp.framed(interior, V(living_split[0] - 0.006, -3.2, f1 + 1.6), V(-1.0, 0.0, 0.0), 0.36, 0.46, tp.pr("portrait_a"), rng, "timber_beam", 0.04)
    for w in upper_windows[:3]:
        tp.curtain_light(clutter, V(w[0] - 0.1, fy + 0.08, w[3] + 0.12), V(w[1] + 0.1, fy + 0.08, w[3] + 0.12), 1.6, rng, "fabric_worn", 0.4)
    tk.pendant(b, interior, V(-2.5, -2.5, c2), rng, "town_metal", 0.5, "warm", 8)
    tp.debris_field(parts, -5.0, 0.2, -4.7, -0.5, f1, rng, 4, 2, 3, 0)
    tp.iron_bed_light(b, furniture, clutter, V(1.75, -2.5, f1), 0.0, rng, 1.95, 1.4)
    tp.wardrobe_light(b, furniture, clutter, V(4.3, front_rooms[0] - 0.3, f1), 0.0, rng, 1.1, 0.56, "timber_beam", "timber_beam")
    tp.washstand_light(b, furniture, clutter, V(4.2, fy + 0.25, f1), math.pi, rng)
    tp.chest_light(b, furniture, V(2.05, fy + 0.24, f1), math.pi, rng, 0.8, 0.44, 0.9, "timber_beam", 4)
    b.loot("box", V(2.05, fy + 0.24, f1 + 0.95))
    tp.chair_light(furniture, V(3.3, -3.6, f1), 2.4, rng)
    bd.rug(clutter, V(1.8, -3.65, f1), 1.4, 0.8, 0.05, rng, "fabric_tartan")
    for y in (-2.85, -2.15):
        tp.candlestick(clutter, V(bedroom - 0.07, y, f1 + 1.16), rng)
    tp.framed(interior, V(living_split[1] + 0.006, -2.5, f1 + 1.6), V(1.0, 0.0, 0.0), 0.5, 0.3, tp.pr("seascape"), rng, "timber_beam", 0.03)
    for w in upper_windows[3:]:
        tp.curtain_light(clutter, V(w[0] - 0.1, fy + 0.08, w[3] + 0.12), V(w[1] + 0.1, fy + 0.08, w[3] + 0.12), 1.6, rng, "fabric_tartan", 0.4)
    tk.pendant(b, interior, V(3.1, -2.5, c2), rng, "glass_dirty", 0.45, "warm", 8)
    tp.papers(parts["debris"], 1.0, 5.0, -4.5, -0.6, f1, 4, rng, ("letter", "envelope", "card"))
    tp.bath(b, furniture, V(-2.66, 3.95, f1), math.pi * 0.5, rng, 1.6, 0.72, 0.62, "town_brass", 16)
    tp.toilet(b, furniture, V(-1.0, by - 0.41, f1), 0.0, rng, 2.0, False, 8, False)
    tp.basin(b, furniture, V(bath_split[0] - 0.22, 2.4, f1), -math.pi * 0.5, rng, 8)
    tp.wall_mirror(interior, V(bath_split[0] - 0.005, 2.4, f1 + 1.5), V(-1.0, 0.0, 0.0), 0.45, 0.55, rng)
    tk.pendant(b, interior, V(-1.9, 3.0, c2), rng, "glass_dirty", 0.4, "warm", 8)
    tk.chips(parts["debris"], "kitchen_tiles", -2.9, -0.9, 1.6, 3.0, f1, 4, rng, (0.03, 0.07), (0.006, 0.008))
    tp.iron_bed_light(b, furniture, clutter, V(-0.08, 3.95, f1), -math.pi * 0.5, rng, 1.9, 0.95, "rusty_metal", True, "fabric_worn")
    tp.chest_light(b, furniture, V(2.0, by - 0.24, f1), 0.0, rng, 0.8, 0.44, 0.9, "timber_beam", 4)
    tp.chair_light(furniture, V(1.6, 2.3, f1), 3.6, rng)
    bd.suitcase(clutter, V(1.0, 2.7, f1), 0.4, rng, True)
    tp.framed(interior, V(kitchen_split[0] - 0.006, 3.2, f1 + 1.6), V(-1.0, 0.0, 0.0), 0.36, 0.46, tp.pr("portrait_b"), rng, "timber_beam", -0.03)
    w = world_back(back_windows[4])
    tp.curtain_light(clutter, V(w[0] - 0.1, by - 0.08, w[3] + 0.12), V(w[1] + 0.1, by - 0.08, w[3] + 0.12), 1.4, rng, "fabric_worn", 0.4)
    tk.pendant(b, interior, V(0.9, 3.2, c2), rng, "town_metal", 0.45, "warm", 8)
    tp.sink_light(b, furniture, clutter, V(3.85, by - 0.25, f1), 0.0, rng)
    tp.table_light(furniture, 3.55, 2.45, f1, 0.9, 0.7, 0.76, rng)
    tk.col(b, "wood", "table", 3.1, 4.0, 2.1, 2.8, f1, f1 + 0.76)
    tp.chair_light(furniture, V(3.55, 1.85, f1), math.pi + 0.15, rng)
    tp.chair_light(furniture, V(4.3, 2.5, f1), 1.2, rng, fallen=True)
    tp.label_jar(clutter, V(3.4, 2.55, f1 + 0.76), rng, "jam")
    tp.label_can(clutter, V(3.75, 2.3, f1 + 0.76), rng, "beans")
    tp.plate_light(clutter, V(3.5, 2.3, f1 + 0.76), rng)
    b.loot("food", V(3.6, 2.5, f1 + 0.76))
    tp.dresser_light(b, furniture, clutter, V(kitchen_split[1] + 0.25, 3.6, f1), math.pi * 0.5, rng, "painted_wood_green", 1.2)
    bd.shelf(interior, V(2.6, by, f1 + 1.6), V(3.35, by, f1 + 1.6), 0.22, V(0.0, -1.0, 0.0), rng)
    x = 2.7
    while x < 3.25:
        tp.label_jar(clutter, V(x, by - 0.11, f1 + 1.6), rng, rng.choice(("jam", "pickles", "honey", "marmalade")))
        x += rng.uniform(0.15, 0.22)
    tk.pendant(b, interior, V(4.0, 3.2, c2), rng, "town_metal", 0.45, "warm", 8)
    tp.debris_field(parts, 2.7, 5.0, 1.6, 4.6, f1, rng, 3, 0, 2, 0)
    tp.framed(interior, V(3.5, front_rooms[1] + 0.006, f1 + 1.6), V(0.0, 1.0, 0.0), 0.6, 0.3, tp.pr("map"), rng, "timber_beam", 0.02)
    tp.framed(interior, V(-3.9, front_rooms[1] + 0.006, f1 + 1.65), V(0.0, 1.0, 0.0), 0.3, 0.4, tp.pr("portrait_b"), rng, "timber_beam", -0.02)
    tk.pendant(b, interior, V(1.0, 0.65, c2), rng, "town_metal", 0.4, "warm", 8)
    tp.papers(parts["debris"], -4.0, 5.0, 0.2, 1.1, f1, 3, rng, ("letter", "newspaper"))


def exterior(b, parts, gable, rng):
    roof = parts["roof"]
    clutter = parts["clutter"]
    plants = parts["plants"]
    joinery = parts["joinery"]
    gutter_z = gable.eave_top - 0.05 - 0.06
    tk.terrace_roof(b, parts, -hx, hx, gable, rng, 0.35, 0.012, [(1.6, 2.6, 2.2, 3.4, 1.0)], 0.03, True, "rock", True, None, True, (-1.0, 1.0), 0.33, 0.7, 0.48)
    tk.stack(b, roof, -hx + 0.42, 0.0, 0.75, 1.2, gable.top(0.6) - 0.3, gable.ridge_top + 1.0, rng, 3)
    tk.stack(b, roof, hx - 0.42, 0.0, 0.75, 1.2, gable.top(0.6) - 0.3, gable.ridge_top + 0.9, rng, 4)
    tk.downpipe_light(roof, hx - 0.22, -gable.edge - 0.04, -hy, gutter_z - 0.03, 3.82, rng)
    tk.downpipe_light(roof, -hx + 0.22, gable.edge + 0.04, hy, gutter_z - 0.03, -0.15, rng, broken=0.9, lean=0.04)
    tp.hanging_sign(joinery, V(-5.3, -hy, 5.1), V(0.0, -1.0, 0.0), rng, tp.sg("pub_sign"))
    block(joinery, paint, V(-hx - 0.04, -2.8, 3.2), V(-hx, 0.4, 3.6), 0.004)
    tk.atlas_panel(joinery, "town_signs", V(-hx - 0.041, -1.2, 3.4), V(-1.0, 0.0, 0.0), 3.2, 0.4, tp.sg("pub_board"), 0.0, 0.0)
    tp.lantern(b, joinery, V(0.83, -hy - 0.11, 2.45), V(0.0, -1.0, 0.0), rng)
    tp.bench_light(b, clutter, V(-4.25, -hy - 0.45, -0.15), 0.0, rng, 1.4)
    tp.cask_light(clutter, V(-1.45, -hy - 0.42, -0.15), rng, 0.3, 0.42, 0.0, False)
    lump(plants, "dirt_debris", V(-1.45, -hy - 0.42, 0.24), (0.24, 0.24, 0.03), rng, 0.2, 1)
    kit.nettle(plants, V(-1.45, -hy - 0.42, 0.26), rng, (0.3, 0.6))
    tk.col(b, "wood", "planter", -1.75, -1.15, -hy - 0.72, -hy - 0.12, -0.15, 0.27)
    tp.cellar_flap(parts["shell"], 3.75, 4.75, -hy - 0.85, -hy - 0.12, -0.15, rng)
    for center, yaw in ((V(4.9, hy + 0.45, -0.15), 0.2), (V(5.45, hy + 0.5, -0.15), 0.4)):
        tp.bottle_crate(clutter, center, yaw, rng, "stout", 2, 3, 0.4)
    tk.col(b, "wood", "crates", 4.6, 5.7, hy + 0.25, hy + 0.7, -0.15, 0.25)
    bd.dustbin(clutter, V(-2.4, hy + 0.4, -0.15), rng)
    tk.ivy_light(plants, V(-hx - 0.02, 2.6, -0.15), V(-1.0, 0.0, 0.0), rng, 3.6, 0.9, 3, 14.0)
    tk.weeds_line(plants, V(-hx + 0.3, -hy - 0.12, -0.15), V(door[0] - 0.3, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(door[1] + 0.3, -hy - 0.12, -0.15), V(hx - 0.3, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(-hx + 0.3, hy + 0.12, -0.15), V(hx - 0.3, hy + 0.12, -0.15), rng, 4)
    tk.weeds_line(plants, V(-hx - 0.1, -hy + 0.3, -0.15), V(-hx - 0.1, hy - 0.3, -0.15), rng, 3)
    tk.weeds_line(plants, V(hx + 0.1, -hy + 0.3, -0.15), V(hx + 0.1, hy - 0.3, -0.15), rng, 3)
    for index in range(5):
        kit.grass_tuft(plants, V(rng.uniform(-hx, hx), rng.choice((-1.0, 1.0)) * (gable.edge + 0.06), gutter_z + 0.02), rng, (0.06, 0.2), (3, 5), 0.03)
    tp.papers(parts["debris"], -5.0, 5.0, -6.6, -5.7, -0.15, 5, rng, ("newspaper", "notice", "card", "poster"))
    tk.chips(parts["debris"], "slate_roof", -5.0, 5.0, -6.4, -5.7, -0.15, 4, rng, (0.08, 0.17), (0.006, 0.008))
    tk.chips(parts["debris"], "glass_dirty", 1.0, 2.8, -6.0, -5.6, -0.15, 4, rng, (0.02, 0.06), (0.003, 0.004))


def pub():
    b = kit.Build("pub", 1301)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    shell_walls(b, parts, gable, rng)
    frontage(b, parts, rng)
    openings(b, parts, rng)
    ground_walls(b, parts, rng)
    upper_walls(b, parts, rng)
    faces = breasts(b, parts, rng)
    finishes(parts, rng, faces)
    bar_room(b, parts, rng, faces)
    servery(b, parts, rng)
    back_zone(b, parts, rng)
    upper_rooms(b, parts, rng, faces)
    exterior(b, parts, gable, rng)
    return b


def pub_far():
    b = kit.Build("pub_far", 1302)
    shell = b.part("shell", 30.0)
    gable = gable_of()
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    wide_front = kit.facade("front", hx, hy)
    back = kit.facade("back", ix, hy)
    wide_back = kit.facade("back", hx, hy)
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [], wall_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [], wall_t)
    outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
    for side, openings_list in (("left", left_windows), ("right", right_windows)):
        frame = kit.facade(side, hx, hy)
        kit.wall(shell, stone, frame, outline, [], wall_t)
        for w in openings_list:
            kit.skin(shell, "glass_dirty", frame, kit.rect(*w), [], 0.004, 0.001, False)
    kit.skin(shell, render, wide_front, kit.rect(-hx, hx, 3.8, wall_top - 0.02), [kit.rect(*w) for w in upper_windows], 0.02, 0.0, False)
    for w in upper_windows:
        kit.skin(shell, "glass_dirty", wide_front, kit.rect(*w), [], 0.004, 0.001, False)
    kit.skin(shell, render, wide_back, kit.rect(-hx, hx, 1.0, wall_top - 0.35), [kit.rect(o[0], o[1], max(o[2], 1.01), o[3]) for o in back_windows + [back_door, store_door]], 0.018, 0.0, False)
    for o in back_windows + [back_door, store_door]:
        kit.skin(shell, "glass_dirty" if o[2] > 0.5 else "soot", wide_back, kit.rect(*o), [], 0.004, 0.001, False)
    kit.skin(shell, paint, wide_front, kit.rect(-hx, hx, 0.0, 3.8), [], 0.08, 0.0, False)
    for w in windows:
        kit.skin(shell, "glass_dirty", wide_front, kit.rect(*w), [], 0.004, 0.081, False)
    kit.skin(shell, "soot", wide_front, kit.rect(door[0], door[1], 0.0, door[3]), [], 0.004, 0.081, False)
    tk.atlas_quad(shell, "town_signs", [kit.frame_point(wide_front, -4.8, 2.76, 0.0855), kit.frame_point(wide_front, 4.8, 2.76, 0.0855), kit.frame_point(wide_front, 4.8, 3.66, 0.0855), kit.frame_point(wide_front, -4.8, 3.66, 0.0855)], tp.sg("pub_fascia"))
    kit.roof_slab(shell, gable, -1.0, -hx, hx, "slate_roof", 0.2)
    kit.roof_slab(shell, gable, 1.0, -hx, hx, "roof_moss", 0.2)
    block(shell, "terracotta", V(-hx, -0.13, gable.ridge_top - 0.04), V(hx, 0.13, gable.ridge_top + 0.09))
    for cx, top, pots in ((-hx + 0.42, gable.ridge_top + 1.0, (-0.3, 0.3, 0.0)), (hx - 0.42, gable.ridge_top + 0.9, (-0.36, -0.12, 0.12, 0.36))):
        block(shell, dressed, V(cx - 0.375, -0.6, gable.top(0.6) - 0.3), V(cx + 0.375, 0.6, top + 0.12))
        for dy in pots:
            block(shell, "terracotta", V(cx - 0.08, dy - 0.08, top + 0.12), V(cx + 0.08, dy + 0.08, top + 0.5))
    center = V(-5.3, -hy - 0.52, 5.1 - 0.66)
    tk.atlas_panel(shell, "town_signs", center + V(0.026, 0.0, 0.0), V(1.0, 0.0, 0.0), 0.8, 1.0, tp.sg("pub_sign"), 0.0, 0.0)
    tk.atlas_panel(shell, "town_signs", center - V(0.026, 0.0, 0.0), V(-1.0, 0.0, 0.0), 0.8, 1.0, tp.sg("pub_sign"), 0.0, 0.0)
    return b
