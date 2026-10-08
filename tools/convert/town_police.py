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
hy = 7.0
wall_t = 0.45
ix = hx - wall_t
fy = -hy + wall_t
by = hy - wall_t
c1 = 3.2
f1 = 3.45
c2 = 6.25
navy = "town_paint_navy"
trim = "painted_wood_white"
green = "painted_wood_green"
stone = "granite_rubble"
dressed = "granite_ashlar"
render = "render_white"
door = (-0.68, 0.68, 0.0, 2.85)
door_top = 2.32
windows = [(-4.8, -3.5, 0.85, 2.55), (-2.7, -1.4, 0.85, 2.55), (1.4, 2.7, 0.85, 2.55), (3.5, 4.8, 0.85, 2.55)]
upper_windows = [(-4.7, -3.6, 4.05, 5.75), (-2.6, -1.5, 4.05, 5.75), (1.5, 2.6, 4.05, 5.75), (3.6, 4.7, 4.05, 5.75)]
lamp_window = (-0.35, 0.35, 4.95, 5.85)
left_windows = [(4.9, 6.1, 0.85, 2.55), (-0.55, 0.55, 0.95, 2.45), (-5.2, -4.4, 1.85, 2.55), (0.7, 1.8, 4.05, 5.75), (-5.1, -4.3, 4.6, 5.75)]
right_windows = [(-6.1, -4.9, 0.85, 2.55), (-1.1, -0.45, 1.95, 2.5), (1.78, 2.43, 1.95, 2.5), (4.78, 5.43, 1.95, 2.5), (-1.0, 0.1, 4.05, 5.75), (2.5, 3.6, 4.05, 5.75), (4.7, 5.8, 4.05, 5.75)]
back_door = (-0.55, 0.55, 0.0, 2.25)
back_windows = [(-2.45, -1.5, 1.0, 2.3), (3.0, 3.9, 1.85, 2.55), (-0.5, 0.5, 4.05, 5.75), (2.2, 3.1, 4.6, 5.75), (-3.7, -2.6, 4.45, 5.75)]
partition = (-2.3, -2.18)
west = (-1.24, -1.12)
east = (1.08, 1.2)
cell_x = 2.75
cells = [(-2.18, 0.62), (0.74, 3.54), (3.66, 6.55)]
interview_split = (2.0, 2.12)
locker_split = (2.9, 3.02)
records_split = (1.48, 1.6)
stair_x = (-1.12, -0.07)
stair_foot = -1.0
stair_run = 4.9
stair_steps = 17
well = (-1.12, -0.02, -0.3, 3.9)
counter = (0.9, ix, -4.5, -3.9)
interview_door = (-3.0, -1.95, 0.0, 2.2)
hall_door = (-0.5, 0.55, 0.0, 2.2)
cells_door = (1.45, 2.5, 0.0, 2.2)
armoury_door = (4.4, 5.45, 0.0, 2.2)
cell_back_door = (4.4, 5.45, 0.0, 2.2)
inspector_door = (-3.6, -2.55, f1, f1 + 2.2)
locker_door = (-1.5, -0.45, f1, f1 + 2.2)
washroom_door = (4.5, 5.5, f1, f1 + 2.2)
cid_door = (-3.6, -2.55, f1, f1 + 2.2)
records_door = (-1.5, -0.45, f1, f1 + 2.2)
mess_door = (4.5, 5.5, f1, f1 + 2.2)
breast_y = (-5.4, -3.8)


def gable_of():
    return kit.Gable(-hx, hx, hy, 0.3, 6.62, 30.0)


def flip(o):
    return (-o[1], -o[0], o[2], o[3])


def plinth(shell, frame, a_low, a_high, gaps, rng, top=0.42):
    edges = [a_low]
    for g0, g1 in sorted(gaps):
        edges += [g0, g1]
    edges.append(a_high)
    for s0, s1 in zip(edges[0::2], edges[1::2]):
        count = max(1, int(round((s1 - s0) / 0.6)))
        for index in range(count):
            a = s0 + (s1 - s0) * index / count
            c = s0 + (s1 - s0) * (index + 1) / count
            frame_block(shell, dressed, frame, a + 0.006, c - 0.006, -0.5, top + rng.uniform(-0.02, 0.02), -0.045, 0.0)


def plain_dressings(shell, frame, w, lintel=True):
    frame_block(shell, dressed, frame, w[0] - 0.07, w[1] + 0.07, w[2] - 0.09, w[2], -0.06, 0.2)
    if lintel:
        frame_block(shell, dressed, frame, w[0] - 0.16, w[1] + 0.16, w[3], w[3] + 0.26, -0.02, 0.3)


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    front_open = [door] + windows + upper_windows + [lamp_window]
    holes = [kit.rect(door[0], door[1], -0.05, door[3])] + [kit.rect(*w) for w in windows + upper_windows + [lamp_window]]
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), holes, wall_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, -1.5, wall_top, wall_t, front_open)
    back_open = [back_door] + back_windows
    holes = [kit.rect(back_door[0], back_door[1], -0.05, back_door[3])] + [kit.rect(*w) for w in back_windows]
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), holes, wall_t)
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, -1.5, wall_top, wall_t, back_open)
    outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
    for frame, openings_list, tag in ((left, left_windows, "left"), (right, right_windows, "right")):
        kit.wall(shell, stone, frame, outline, [kit.rect(*w) for w in openings_list], wall_t)
        kit.wall_boxes(b, "rock", tag, frame, -hy, hy, -1.5, wall_top, wall_t, openings_list)
    bd.gable_cols(b, "gable", -hx, -ix, gable, wall_top, 0.0)
    bd.gable_cols(b, "gable", ix, hx, gable, wall_top, 0.0)
    wide_front = kit.facade("front", hx, hy)
    tk.render_skin(shell, wide_front, -hx, hx, wall_top - 0.02, upper_windows + [lamp_window], rng, 3, render, 0.02, 1, (3.52, 3.54), 0.0)
    plinth(shell, wide_front, -hx, hx, [(door[0] - 0.34, door[1] + 0.34)], rng)
    frame_block(shell, dressed, wide_front, -hx - 0.05, hx + 0.05, 3.3, 3.52, -0.08, 0.0, 0.01)
    frame_block(shell, render, wide_front, -hx, hx, wall_top - 0.36, wall_top - 0.22, -0.06, 0.0, 0.006)
    frame_block(shell, render, wide_front, -hx - 0.04, hx + 0.04, wall_top - 0.22, wall_top - 0.02, -0.13, 0.0, 0.008)
    for w in upper_windows + [lamp_window]:
        a0, a1, z0, z1 = w
        frame_block(shell, render, front, a0 - 0.1, a0, z0, z1 + 0.15, -0.03, 0.0)
        frame_block(shell, render, front, a1, a1 + 0.1, z0, z1 + 0.15, -0.03, 0.0)
        frame_block(shell, render, front, a0 - 0.14, a1 + 0.14, z1 + 0.15, z1 + 0.21, -0.07, 0.0)
        frame_block(shell, dressed, front, (a0 + a1) * 0.5 - 0.07, (a0 + a1) * 0.5 + 0.07, z1 - 0.02, z1 + 0.17, -0.05, 0.0)
    for corner, ua, ub in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0))):
        tk.quoins_light(shell, dressed, corner, ua, ub, -0.3, wall_top - 0.05, rng, 0.045)
    wide_back = kit.facade("back", hx, hy)
    tk.render_skin(shell, wide_back, -hx, hx, wall_top - 0.4, back_open, rng, 4, render, 0.018, 1, (0.6, 1.3), 0.8)
    bd.damp_band(shell, wide_back, -hx, hx, rng, 0.35, 1.1, "granite_rubble_damp", -0.2, 0.003, [(back_door[0] - 0.05, back_door[1] + 0.05)])
    for side in ("left", "right"):
        bd.damp_band(shell, kit.facade(side, hx, hy), -hy, hy, rng, 0.3, 0.9, "granite_rubble_damp", -0.2, 0.003)
    return wall_top


def doorcase(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    front = kit.facade("front", ix, hy)
    a0, a1, z0, z1 = door
    for edge, sign in ((a0, -1.0), (a1, 1.0)):
        lo, hi = sorted((edge, edge + sign * 0.3))
        frame_block(shell, dressed, front, lo - 0.02, hi + 0.02, -0.45, 0.34, -0.15, 0.0, 0.012)
        frame_block(shell, dressed, front, lo, hi, 0.34, 2.95, -0.1, 0.0, 0.01)
        frame_block(shell, dressed, front, lo - 0.02, hi + 0.02, 2.95, 3.06, -0.13, 0.0, 0.01)
    frame_block(shell, dressed, front, a0 - 0.34, a1 + 0.34, 3.06, 3.36, -0.12, 0.0, 0.01)
    frame_block(shell, dressed, front, a0 - 0.44, a1 + 0.44, 3.36, 3.5, -0.26, 0.0, 0.015)
    frame_block(joinery, navy, front, -0.9, 0.9, 3.1, 3.32, -0.135, -0.12, 0.0, "board")
    tk.atlas_panel(joinery, "town_signs", kit.frame_point(front, 0.0, 3.21, 0.137), V(0.0, -1.0, 0.0), 1.74, 0.2, tp.sg("police_board"), 0.0, 0.0)
    ja0, ja1, jtop = tk.door_frame_light(joinery, navy, front, a0, a1, 0.0, door_top, 0.2, 0.07, 0.2)
    width = (ja1 - ja0) * 0.5 - 0.01
    d_axis = 0.2 + 0.1 - 0.0225
    tk.door_leaf_light(joinery, navy, front, ja0 + 0.005, 1.0, d_axis, 0.012, jtop - 0.02, width, 97.0, rng, "panel", 1.0)
    tk.door_leaf_light(joinery, navy, front, ja1 - 0.005, -1.0, d_axis, 0.012, jtop - 0.02, width, 82.0, rng, "panel", 0.0)
    frame_block(joinery, navy, front, a0, a1, door_top, door_top + 0.07, 0.2, 0.4, 0.004, "board")
    frame_block(joinery, navy, front, a0, a1, z1 - 0.06, z1, 0.2, 0.4, 0.004, "board")
    for edge in (a0, a1 - 0.06):
        frame_block(joinery, navy, front, edge, edge + 0.06, door_top, z1, 0.2, 0.4, 0.004, "board")
    matrix = kit.frame_matrix(front)
    bars = 4
    for index in range(bars):
        p0 = a0 + 0.06 + (a1 - a0 - 0.12) * index / bars
        p1 = a0 + 0.06 + (a1 - a0 - 0.12) * (index + 1) / bars
        kit.pane(joinery, matrix, p0 + 0.01, p1 - 0.01, door_top + 0.07, z1 - 0.06, 0.28, rng.choice(("whole", "shard", "missing", "whole")), rng)
        if index:
            frame_block(joinery, navy, front, p0 - 0.012, p0 + 0.012, door_top + 0.07, z1 - 0.06, 0.25, 0.32)
    tk.opening_block(b, "glass", "fanlight", front, (a0, a1, door_top, z1), wall_t)
    block(shell, dressed, V(a0 - 0.22, -hy - 0.42, -0.45), V(a1 + 0.22, -hy + 0.02, -0.05), 0.015)
    tk.col(b, "rock", "step", a0 - 0.22, a1 + 0.22, -hy - 0.42, -hy, -1.5, -0.05)
    tk.col(b, "rock", "threshold", a0, a1, -hy, fy, -1.5, 0.0)
    block(shell, dressed, V(a0, -hy, -0.08), V(a1, fy + 0.04, 0.0), 0.004)
    scraper = V(a1 + 0.45, -hy - 0.13, -0.05)
    for dx in (-0.1, 0.1):
        rod(joinery, "rusty_metal", scraper + V(dx, 0.0, 0.0), scraper + V(dx, 0.0, 0.18), 0.008, 5)
    local_block(joinery, "rusty_metal", kit.Matrix.Translation(scraper), -0.1, 0.1, -0.006, 0.006, 0.12, 0.16)
    tp.blue_lamp(b, joinery, V(0.0, -hy - 0.02, 4.45), V(0.0, -1.0, 0.0), rng)


def openings(b, parts, rng):
    joinery = parts["joinery"]
    shell = parts["shell"]
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    states = [(0.0, 0.35, 0.3, False, False), (0.25, 0.15, 0.35, False, True), (0.0, 0.4, 0.3, False, False), (0.0, 0.0, 0.2, True, False)]
    for w, (lift, whole, shard, climb, boarded) in zip(windows, states):
        tk.sash(b, parts, front, w, wall_t, rng, trim, 0.12, lift, whole, shard, 2, 1, None, dressed, None, climb, boarded, "glass", "window", dressed, "painted_wood_white")
        frame_block(shell, dressed, front, (w[0] + w[1]) * 0.5 - 0.08, (w[0] + w[1]) * 0.5 + 0.08, w[3] - 0.02, w[3] + 0.24, -0.04, 0.0, 0.008)
    upper_states = [(0.0, 0.4, False), (0.2, 0.25, False), (0.0, 0.3, True), (0.1, 0.35, False)]
    for w, (lift, whole, boarded) in zip(upper_windows, upper_states):
        tk.sash(b, parts, front, w, wall_t, rng, trim, 0.12, lift, whole, 0.3, 2, 1, render, dressed, None, False, boarded)
    tk.sash(b, parts, front, lamp_window, wall_t, rng, trim, 0.12, 0.0, 0.3, 0.3, 1, 1, render, dressed)
    for frame, w, lift, whole, shard, cols, boarded in ((left, left_windows[0], 0.0, 0.3, 0.3, 2, False), (left, left_windows[1], 0.0, 0.2, 0.4, 1, False), (left, left_windows[3], 0.15, 0.3, 0.3, 1, False), (right, right_windows[0], 0.0, 0.2, 0.3, 1, True), (right, right_windows[4], 0.0, 0.3, 0.3, 1, False), (right, right_windows[5], 0.2, 0.3, 0.3, 1, False), (right, right_windows[6], 0.0, 0.3, 0.3, 1, False), (back, back_windows[0], 0.0, 0.2, 0.3, 1, False), (back, back_windows[2], 0.0, 0.25, 0.35, 1, False), (back, back_windows[4], 0.3, 0.2, 0.3, 1, False)):
        tk.sash(b, parts, frame, w, wall_t, rng, trim, 0.12, lift, whole, shard, cols, 1, None, None, None, False, boarded, "glass", "window", None, None)
        plain_dressings(shell, frame, w)
    for frame, w, leaves, rows in ((left, left_windows[2], [0.0], 1), (left, left_windows[4], [35.0], 2), (right, right_windows[1], [0.0], 1), (right, right_windows[2], [0.0], 1), (right, right_windows[3], [0.0], 1), (back, back_windows[1], [0.0], 1), (back, back_windows[3], [50.0], 2)):
        tk.casement(b, parts, frame, w, wall_t, rng, trim, 0.1, leaves, 0.2, 0.4, rows, None)
        plain_dressings(shell, frame, w, False)
    for frame, w in ((left, left_windows[1]), (left, left_windows[2]), (right, right_windows[1]), (right, right_windows[2]), (right, right_windows[3]), (back, back_windows[0]), (back, back_windows[1])):
        tp.window_bars(joinery, frame, w, 0.05)
    a0, a1, z0, z1 = back_door
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, navy, rng, "high", 96.0, "ledged", True, 0.0, 0.06, 3.0, trim)
    block(shell, dressed, V(-a1 - 0.1, hy - 0.04, -0.35), V(-a0 + 0.1, hy + 0.36, -0.06), 0.012)
    tk.col(b, "rock", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
    tk.col(b, "rock", "step", -a1 - 0.1, -a0 + 0.1, hy, hy + 0.36, -0.6, -0.06)


def floors(b, parts, rng):
    floor = parts["floors"]
    tk.tile_floor(floor, "town_quarry", -ix, ix, fy, partition[0], 0.0, 0.02)
    tk.tile_floor(floor, "town_quarry", west[1], east[0], partition[1], by, 0.0, 0.02)
    tk.board_floor(floor, -ix, west[0], partition[1], interview_split[0], 0.0, rng, "x", (), "floorboards", 0.03, 0.0, (0.15, 0.2), (0.5,))
    tk.tile_floor(floor, "concrete", -ix, west[0], interview_split[1], by, 0.0, 0.04)
    tk.tile_floor(floor, "concrete", east[1], ix, partition[1], by, 0.0, 0.04)
    for d in (interview_door, hall_door, cells_door):
        block(floor, "timber_beam", V(d[0], partition[0], -0.02), V(d[1], partition[1], 0.006), 0.003)
    for x0, x1, d in ((west[0], west[1], armoury_door), (east[0], east[1], cell_back_door)):
        block(floor, "timber_beam", V(x0, d[0], -0.02), V(x1, d[1], 0.006), 0.003)
    block(floor, "concrete", V(-ix, interview_split[0], -0.02), V(west[0], interview_split[1], 0.004))
    tk.col(b, "rock", "ground", -ix, ix, fy, partition[1], -0.3, 0.0)
    tk.col(b, "wood", "ground", -ix, west[0], partition[1], interview_split[0], -0.3, 0.0)
    tk.col(b, "concrete", "ground", -ix, west[0], interview_split[0], by, -0.3, 0.0)
    tk.col(b, "rock", "ground", west[0], east[1], partition[1], by, -0.3, 0.0)
    tk.col(b, "concrete", "ground", east[1], ix, partition[1], by, -0.3, 0.0)
    lino = [(west[0] - 0.06, east[1] + 0.06, fy, by), (east[1], ix, records_split[0], by), (-ix, west[0], locker_split[0], by)]
    tk.board_floor(floor, -ix, ix, fy, by, f1, rng, "y", [well] + lino, "floorboards", 0.03, 0.0, (0.15, 0.21), (0.4,))
    for x0, x1, y0, y1 in ((west[0], east[1], fy, well[2]), (well[1], east[1], well[2], well[3]), (west[0], east[1], well[3], by)):
        tk.tile_floor(floor, "town_lino", x0, x1, y0, y1, f1, 0.04)
    tk.tile_floor(floor, "town_lino", east[1], ix, records_split[0], by, f1, 0.04)
    tk.tile_floor(floor, "town_tiles", -ix, west[0], locker_split[0], by, f1, 0.04)
    tk.floor_cols(b, "wood", "upper", -ix, ix, fy, by, c1, f1, [well])
    tk.col(b, "wood", "attic", -ix, ix, fy, by, c2, c2 + 0.25)
    block(floor, trim, V(well[1], well[2], c1 - 0.01), V(well[1] + 0.03, well[3], f1 + 0.014), 0.002, "board")
    block(floor, trim, V(well[0], well[2] - 0.03, c1 - 0.01), V(well[1] + 0.03, well[2], f1 + 0.014), 0.002, "board")


def ground_walls(b, parts, rng):
    joinery = parts["joinery"]
    interior = parts["interior"]
    front_plane = tk.partition(b, parts, V(0.0, partition[0], 0.0), V(0.0, -1.0, 0.0), -ix, ix, 0.0, c1, partition[1] - partition[0], [interview_door, hall_door, cells_door], "partition")
    tk.door_unit(joinery, front_plane, interview_door[0], interview_door[1], 0.0, 2.2, 0.12, trim, rng, "low", 94.0, "panel")
    tk.door_unit(joinery, front_plane, hall_door[0], hall_door[1], 0.0, 2.2, 0.12, navy, rng, "high", -92.0, "panel")
    tk.door_unit(joinery, front_plane, cells_door[0], cells_door[1], 0.0, 2.2, 0.12, "town_paint_black", rng, "low", 101.0, "ledged")
    west_plane = tk.partition(b, parts, V(west[1], 0.0, 0.0), V(1.0, 0.0, 0.0), partition[1], by, 0.0, f1, west[1] - west[0], [armoury_door], "corridor")
    tk.door_unit(joinery, west_plane, armoury_door[0], armoury_door[1], 0.0, 2.2, 0.12, "town_paint_black", rng, "low", 98.0, "ledged")
    east_plane = tk.partition(b, parts, V(east[1], 0.0, 0.0), V(1.0, 0.0, 0.0), partition[1], by, 0.0, c1, east[1] - east[0], [cell_back_door], "corridor")
    tk.door_unit(joinery, east_plane, cell_back_door[0], cell_back_door[1], 0.0, 2.2, 0.12, "town_paint_black", rng, "high", -96.0, "ledged")
    tk.partition(b, parts, V(0.0, interview_split[0], 0.0), V(0.0, -1.0, 0.0), -ix, west[0], 0.0, c1, interview_split[1] - interview_split[0], [], "interview")
    for y0, y1 in ((cells[0][1], cells[1][0]), (cells[1][1], cells[2][0])):
        tk.partition(b, parts, V(0.0, y0, 0.0), V(0.0, -1.0, 0.0), cell_x, ix, 0.0, c1, y1 - y0, [], "cell", "rock")
    bars = kit.plane(V(cell_x, 0.0, 0.0), V(-1.0, 0.0, 0.0))
    for (y0, y1), angle in zip(cells, (1.45, 0.0, 1.25)):
        yc = (y0 + y1) * 0.5
        tp.cell_front(b, joinery, bars, -y1, -y0, (-yc - 0.42, -yc + 0.42), rng, angle, 2.45, 0.0, "rusty_metal", 0.16)
    kit.wall(interior, "plaster_interior", bars, kit.rect(-by, -partition[1], 2.45, c1), [], 0.2)
    tk.col(b, "rock", "bulkhead", cell_x, cell_x + 0.2, partition[1], by, 2.45, c1)
    tk.stair_flight(b, parts, stair_x[0], stair_x[1], stair_foot, 0.0, stair_run, f1, stair_steps, rng, 1.0, "floorboards", green, None, None, "wood", "stair")
    top_y = stair_foot + stair_run
    bd.balustrade(b, joinery, V(stair_x[1] - 0.03, stair_foot + 0.05, 0.02), V(stair_x[1] - 0.03, top_y - 0.04, f1 + 0.02), rng, 0.88, 0.14, "timber_beam", green, 0.1, (True, False), False)
    tk.under_stair_panel(joinery, stair_x[1], stair_foot, 0.0, stair_run, f1, 1.0, rng, green, (2.35, 3.05, 1.85), 0.03, 1.0)


def upper_walls(b, parts, rng):
    joinery = parts["joinery"]
    tk.partition(b, parts, V(0.0, partition[0], 0.0), V(0.0, -1.0, 0.0), -ix, west[0], f1, c2, partition[1] - partition[0], [], "front_rooms")
    tk.partition(b, parts, V(0.0, partition[0], 0.0), V(0.0, -1.0, 0.0), east[1], ix, f1, c2, partition[1] - partition[0], [], "front_rooms")
    west_plane = tk.partition(b, parts, V(west[1], 0.0, 0.0), V(1.0, 0.0, 0.0), fy, by, f1, c2, west[1] - west[0], [inspector_door, locker_door, washroom_door], "corridor_up")
    for d, hinge, angle in ((inspector_door, "high", 92.0), (locker_door, "high", 88.0), (washroom_door, "low", 100.0)):
        tk.door_unit(joinery, west_plane, d[0], d[1], f1, 2.2, 0.12, trim, rng, hinge, angle, "panel")
    east_plane = tk.partition(b, parts, V(east[1], 0.0, 0.0), V(1.0, 0.0, 0.0), fy, by, f1, c2, east[1] - east[0], [cid_door, records_door, mess_door], "corridor_up")
    for d, hinge, angle in ((cid_door, "high", -95.0), (records_door, "high", -86.0), (mess_door, "low", -98.0)):
        tk.door_unit(joinery, east_plane, d[0], d[1], f1, 2.2, 0.12, trim, rng, hinge, angle, "panel")
    tk.partition(b, parts, V(0.0, locker_split[0], 0.0), V(0.0, -1.0, 0.0), -ix, west[0], f1, c2, locker_split[1] - locker_split[0], [], "locker_split")
    tk.partition(b, parts, V(0.0, records_split[0], 0.0), V(0.0, -1.0, 0.0), east[1], ix, f1, c2, records_split[1] - records_split[0], [], "records_split")
    tk.well_rail(b, joinery, well, f1, rng, ("right", "front"), "timber_beam", green, 0.92, 0.15)


def breasts(b, parts, rng):
    interior = parts["interior"]
    inspector = tk.chimney_breast(b, interior, -ix, 1.0, breast_y[0], breast_y[1], f1, c2, 0.62, 0.66, rng, depth=0.38)
    tk.fireplace_light(b, interior, V(inspector, (breast_y[0] + breast_y[1]) * 0.5, f1), V(1.0, 0.0, 0.0), rng, 1.25, "timber_beam", "kitchen_tiles", False)
    cid = tk.chimney_breast(b, interior, ix, -1.0, breast_y[0], breast_y[1], f1, c2, 0.58, 0.62, rng, depth=0.36)
    tk.fireplace_light(b, interior, V(cid, (breast_y[0] + breast_y[1]) * 0.5, f1), V(-1.0, 0.0, 0.0), rng, 1.05, trim, "kitchen_tiles", False, False)
    return inspector, cid


def finishes(parts, rng, faces):
    inspector, cid = faces
    interior = parts["interior"]
    tiled = ("tiles", 1.25, "kitchen_tiles", ("plaster", 1))
    dado = ("panel", 1.1, green, ("plaster", 0))
    plaster = ("plaster", 1)
    clean = ("plaster", 0)
    bare = ("plaster", 1)
    floral = ("paper", "wallpaper_faded", 1, 1)
    stripe = ("paper", "town_stripe", 1, 1)
    wash = ("tiles", 1.5, "kitchen_tiles", ("plaster", 0))
    mess = ("tiles", 1.25, "kitchen_tiles", ("plaster", 0))
    tk.room(parts, rng, -ix, ix, fy, partition[0], 0.0, c1, {"front": tiled, "left": tiled, "right": tiled, "back": tiled}, {"front": [door] + windows, "left": [flip(left_windows[0])], "right": [right_windows[0]], "back": [interview_door, hall_door, cells_door]}, "timber_beam", None, True, 1, (), None, 4, 0.0)
    tk.room(parts, rng, -ix, west[0], partition[1], interview_split[0], 0.0, c1, {"front": plaster, "left": plaster, "right": plaster, "back": plaster}, {"front": [interview_door], "left": [flip(left_windows[1])]}, "timber_beam", None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, -ix, west[0], interview_split[1], by, 0.0, c1, {"front": bare, "left": bare, "right": bare, "back": bare}, {"left": [flip(left_windows[2])], "right": [armoury_door], "back": [flip(back_windows[1])]}, "timber_beam", None, True, 1, (), None, 4, 0.0)
    tk.room(parts, rng, west[1], east[0], partition[1], by, 0.0, c1, {"front": dado, "left": dado, "right": dado, "back": dado}, {"front": [hall_door], "left": [armoury_door], "right": [cell_back_door], "back": [flip(back_door)]}, "timber_beam", None, True, 0, [well], None, 2, 0.0)
    tk.room(parts, rng, east[1], cell_x, partition[1], by, 0.0, c1, {"front": clean, "left": mess, "back": clean}, {"front": [cells_door], "left": [cell_back_door], "back": [flip(back_windows[0])]}, "timber_beam", None, True, 0, (), None, 2, 0.0)
    for (y0, y1), w in zip(cells, right_windows[1:4]):
        tk.room(parts, rng, cell_x + 0.2, ix, y0, y1, 0.0, c1, {"front": clean, "back": plaster, "right": clean}, {"right": [w]}, None, None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, -ix, west[0], fy, partition[0], f1, c2, {"front": floral, "left": floral, "right": floral, "back": floral}, {"front": upper_windows[:2], "right": [inspector_door]}, trim, f1 + 2.2, True, 1, (), {"left": [(breast_y[0], breast_y[1], f1, c2)]}, 4, 0.0)
    tk.wall_finish(interior, "left", floral, inspector, 0.0, breast_y[0], breast_y[1], f1, c2, [(breast_y[0] + 0.17, breast_y[1] - 0.17, f1, f1 + 1.16)], rng)
    tk.room(parts, rng, east[1], ix, fy, partition[0], f1, c2, {"front": stripe, "left": stripe, "right": stripe, "back": stripe}, {"front": upper_windows[2:], "left": [cid_door]}, trim, f1 + 2.2, True, 1, (), {"right": [(breast_y[0], breast_y[1], f1, c2)]}, 4, 0.0)
    tk.wall_finish(interior, "right", stripe, 0.0, cid, breast_y[0], breast_y[1], f1, c2, [(breast_y[0] + 0.27, breast_y[1] - 0.27, f1, f1 + 1.16)], rng)
    tk.room(parts, rng, west[1], east[0], fy, by, f1, c2, {"front": clean, "left": clean, "right": clean, "back": clean}, {"front": [lamp_window], "left": [inspector_door, locker_door, washroom_door], "right": [cid_door, records_door, mess_door], "back": [flip(back_windows[2])]}, "timber_beam", None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, -ix, west[0], partition[1], locker_split[0], f1, c2, {"front": clean, "left": clean, "right": clean, "back": clean}, {"left": [flip(left_windows[3])], "right": [locker_door]}, "timber_beam", None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, -ix, west[0], locker_split[1], by, f1, c2, {"front": wash, "left": wash, "right": wash, "back": wash}, {"left": [flip(left_windows[4])], "right": [washroom_door], "back": [flip(back_windows[3])]}, None, None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, east[1], ix, partition[1], records_split[0], f1, c2, {"front": plaster, "left": clean, "right": clean, "back": plaster}, {"left": [records_door], "right": [right_windows[4]]}, "timber_beam", None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, east[1], ix, records_split[1], by, f1, c2, {"front": mess, "left": mess, "right": mess, "back": mess}, {"left": [mess_door], "right": right_windows[5:7], "back": [flip(back_windows[4])]}, green, None, True, 0, (), None, 2, 0.0)


def front_office(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    length = counter[1] - counter[0]
    tp.pub_counter(b, furniture, V((counter[0] + counter[1]) * 0.5, (counter[2] + counter[3]) * 0.5, 0.0), 0.0, length, rng, counter[3] - counter[2], 1.05, "timber_beam", navy, (True, False), "counter", False)
    tp.desk_bell(clutter, V(1.25, -4.32, 1.05), rng)
    tp.ledger(clutter, V(2.1, -4.18, 1.05), 0.12, rng, True)
    tp.telephone(clutter, V(4.85, -4.05, 1.05), math.pi + 0.3, rng)
    tp.papers(clutter, 2.7, 4.2, -4.4, -4.0, 1.05, 3, rng, ("police_notice", "letter", "notice"))
    tp.ledger(clutter, V(3.5, -4.15, 1.05), -0.3, rng, False)
    tp.desk_light(b, furniture, clutter, V(5.15, -3.0, 0.0), -math.pi * 0.5, rng, 1.3, 0.7, 0.76, "timber_beam", "floorboards", ("papers", "typewriter"))
    tp.chair_light(furniture, V(4.4, -3.05, 0.0), tk.facing(V(4.4, -3.05, 0.0), V(5.15, -3.05, 0.0)) + 0.2, rng)
    tp.filing_cabinet(b, furniture, V(2.85, partition[0] - 0.36, 0.0), 0.0, rng)
    tp.filing_cabinet(b, furniture, V(3.37, partition[0] - 0.36, 0.0), 0.0, rng, 3, "green", 1.05)
    tp.helmet(clutter, V(2.88, partition[0] - 0.4, 1.32), rng)
    tp.ledger(clutter, V(3.37, partition[0] - 0.36, 1.05), 0.2, rng, False)
    tp.key_cabinet(interior, V(4.05, partition[0] - 0.002, 1.75), V(0.0, -1.0, 0.0), rng)
    tp.pigeonholes(interior, clutter, V(ix - 0.002, -3.0, 1.75), V(-1.0, 0.0, 0.0), 4, 3, rng)
    tp.framed(interior, V(ix - 0.006, -4.15, 1.85), V(-1.0, 0.0, 0.0), 0.62, 0.42, tp.pr("map"), rng, "timber_beam", 0.02)
    b.loot("box", V(2.0, -3.55, 0.0))
    tp.stove_light(b, furniture, V(-3.1, -3.85, 0.0), rng, V(-ix, -3.85, 2.45))
    tp.coal_scuttle(clutter, V(-2.55, -3.45, 0.0), rng, True)
    tp.settle_light(b, furniture, V(-4.45, partition[0] - 0.26, 0.0), 0.0, rng, 1.7)
    tp.bench_light(b, furniture, V(-5.27, -5.5, 0.0), math.pi * 0.5, rng, 1.3)
    tp.bench_light(b, furniture, V(-2.05, fy + 0.25, 0.0), 0.0, rng, 1.35)
    tp.notice_board(interior, V(-ix + 0.002, -3.0, 1.55), V(1.0, 0.0, 0.0), 0.95, 0.72, rng)
    tp.wall_sheet(interior, V(-1.45, partition[0] - 0.006, 1.6), V(0.0, -1.0, 0.0), "poster", rng, 1.0, 0.03)
    tp.wall_sheet(interior, V(-3.65, partition[0] - 0.006, 2.05), V(0.0, -1.0, 0.0), "police_notice", rng, 1.0, -0.02)
    tp.wall_sheet(interior, V(-0.95, fy + 0.006, 1.5), V(0.0, 1.0, 0.0), "notice", rng, 1.0, 0.04)
    tp.framed(interior, V(-3.15, fy + 0.006, 2.0), V(0.0, 1.0, 0.0), 0.34, 0.44, tp.pr("portrait_a"), rng, "town_brass")
    tp.wall_clock(interior, V((hall_door[0] + hall_door[1]) * 0.5, partition[0] - 0.015, 2.62), V(0.0, -1.0, 0.0), rng, 0.18)
    bd.coat_rail(interior, clutter, V(0.68, partition[0], 1.75), V(1.36, partition[0], 1.75), V(0.0, -1.0, 0.0), rng, 1)
    tp.chair_light(furniture, V(-1.1, -3.5, 0.0), 1.1, rng, fallen=True)
    tp.chair_light(furniture, V(-4.0, -4.6, 0.0), 0.3, rng)
    tk.pendant(b, interior, V(-2.9, -4.4, c1), rng, "town_metal", 0.75, "warm", 8)
    tk.pendant(b, interior, V(3.1, -3.4, c1), rng, "town_metal", 0.75, "warm", 8)
    tp.papers(parts["debris"], -4.5, 0.5, -6.2, -2.7, 0.0, 9, rng, ("newspaper", "police_notice", "letter", "envelope", "notice"))
    tp.debris_field(parts, -5.2, 0.6, -6.3, -4.0, 0.0, rng, 4, 4, 0, 5)
    tp.debris_field(parts, 1.0, 5.2, -3.8, -2.5, 0.0, rng, 4, 0, 4, 0)
    tk.chips(parts["debris"], "glass_dirty", 3.4, 4.9, -6.4, -5.9, 0.0, 6, rng, (0.02, 0.06), (0.003, 0.004))


def interview_room(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    table = V(-3.4, 0.0, 0.0)
    tp.table_light(furniture, table.x, table.y, 0.0, 1.2, 0.8, 0.76, rng, "floorboards")
    tk.col(b, "wood", "table", table.x - 0.6, table.x + 0.6, -0.4, 0.4, 0.0, 0.76)
    for position in (V(-3.4, -0.72, 0.0), V(-3.8, 0.74, 0.0)):
        tp.chair_light(furniture, position, tk.facing(position, table) + rng.uniform(-0.2, 0.2), rng)
    tp.chair_light(furniture, V(-2.3, 1.15, 0.0), 2.2, rng, fallen=True)
    tp.desk_lamp(clutter, V(-3.9, 0.18, 0.76), 0.4, rng)
    tp.ashtray(clutter, V(-3.15, 0.08, 0.76), rng)
    tp.cup_light(clutter, V(-2.95, -0.22, 0.76), rng)
    tp.papers(clutter, -3.7, -3.1, -0.3, 0.25, 0.76, 3, rng, ("letter", "police_notice", "notice"))
    tp.filing_cabinet(b, furniture, V(-ix + 0.35, 1.6, 0.0), math.pi * 0.5, rng, 3, "green", 1.05)
    tp.wall_clock(interior, V(west[0] - 0.015, 0.2, 2.3), V(-1.0, 0.0, 0.0), rng, 0.16)
    tp.framed(interior, V(-4.3, partition[1] + 0.006, 1.7), V(0.0, 1.0, 0.0), 0.3, 0.4, tp.pr("notice"), rng, "timber_beam", 0.03)
    tp.bulb(b, interior, V(table.x, table.y, c1), rng, 0.95, "warm")
    tp.debris_field(parts, -5.2, -1.5, -1.9, 1.7, 0.0, rng, 6, 3, 3, 0)


def armoury(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.gun_rack(b, furniture, clutter, V(-3.4, by - 0.2, 0.0), 0.0, rng, 6, 1.5, 0.9)
    tp.gun_rack(b, furniture, clutter, V(-ix + 0.2, 3.3, 0.0), math.pi * 0.5, rng, 5, 1.3, 0.9)
    tp.wall_shelves(b, furniture, clutter, V(-4.3, interview_split[1] + 0.01, 0.0), V(-1.5, interview_split[1] + 0.01, 0.0), V(0.0, 1.0, 0.0), [0.35, 0.85, 1.35, 1.85], rng, ("gap",), 0.38)
    for z in (0.35, 0.85, 1.35):
        x = -4.05
        while x < -1.8:
            if rng.random() < 0.75:
                tp.ammo_box(clutter, V(x, interview_split[1] + 0.2, z), rng.uniform(-0.12, 0.12), rng, "green" if rng.random() < 0.7 else "cream", (0.36, 0.2, 0.2), rng.random() < 0.2)
            x += rng.uniform(0.42, 0.55)
    tp.rifle(clutter, V(-1.62, 2.55, 0.02), V(-1.28, 2.6, 1.12), rng)
    tp.wall_sheet(interior, V(west[0] - 0.006, 4.0, 1.6), V(-1.0, 0.0, 0.0), "police_notice", rng, 1.0, 0.02)
    tp.wall_sheet(interior, V(west[0] - 0.006, 3.95, 1.25), V(-1.0, 0.0, 0.0), "notice", rng, 0.8, -0.03)
    tp.locker_row(b, furniture, V(west[0] - 0.25, 3.2, 0.0), -math.pi * 0.5, 2, rng, "green", 1.85, 0.5, 0.42)
    for center, yaw in ((V(-4.85, 5.75, 0.0), 0.2), (V(-4.75, 5.75, 0.38), -0.25)):
        tp.ammo_box(clutter, center, yaw, rng, "green", (0.6, 0.38, 0.38))
    tk.col(b, "metal", "ammo", -5.25, -4.4, 5.45, 6.05, 0.0, 0.76)
    tp.crate_light(clutter, V(-1.75, by - 0.35, 0.0), (0.6, 0.48, 0.45), 0.15, rng)
    tp.crate_light(clutter, V(-1.8, by - 0.35, 0.45), (0.5, 0.4, 0.36), -0.2, rng)
    tk.col(b, "wood", "crates", -2.1, -1.45, by - 0.65, by - 0.05, 0.0, 0.81)
    tp.sack_row(clutter, V(-5.0, 4.6, 0.0), V(0.0, 1.0, 0.0), 1, rng)
    tk.col(b, "fabric", "sack", -5.3, -4.7, 4.3, 4.9, 0.0, 0.45)
    b.loot("military", V(-3.35, 5.2, 0.0))
    b.loot("military", V(-3.0, 3.25, 0.0))
    b.loot("box", V(-4.55, 2.95, 0.0))
    for butt, muzzle in (((-3.1, 4.05), (-2.05, 4.32)), ((-2.75, 3.92), (-1.75, 3.72))):
        tp.rifle(clutter, V(butt[0], butt[1], 0.02), V(muzzle[0], muzzle[1], 0.02), rng, "timber_beam", "rusty_metal", True)
    tp.bulb(b, interior, V(-3.4, 4.3, c1), rng, 0.5, "cold")
    tp.debris_field(parts, -5.2, -1.6, 2.6, 6.2, 0.0, rng, 6, 0, 4, 0)


def cell_block(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    for index, (y0, y1) in enumerate(cells):
        tp.plank_bed(b, furniture, ix, y0 + 0.22, y1 - 0.45, -1.0, rng, 0.45, 0.7)
        tp.bucket_light(clutter, V(cell_x + 0.5, y1 - 0.32, 0.0), rng, "rusty_metal", index == 2)
        for k in range(rng.randint(5, 11)):
            x = ix - 0.018
            y = y1 - 0.4 - k * 0.035
            block(interior, "soot", V(x - 0.003, y - 0.004, 1.35 + rng.uniform(-0.02, 0.02)), V(x, y + 0.004, 1.55 + rng.uniform(-0.02, 0.02)))
        tp.cage_lamp(b, interior, V((cell_x + ix) * 0.5 + 0.1, (y0 + y1) * 0.5, c1), rng, "cold")
        tk.chips(parts["debris"], "plaster_interior", cell_x + 0.3, ix - 0.8, y0 + 0.2, y1 - 0.2, 0.0, 4, rng)
    tp.chamber_pot(clutter, V(4.3, cells[0][0] + 0.35, 0.0), rng)
    lump(clutter, "fabric_worn", V(5.15, cells[2][0] + 0.9, 0.48), (0.28, 0.2, 0.06), rng, 0.3, 1)
    lump(clutter, "fabric_tartan", V(4.0, cells[1][0] + 1.5, 0.03), (0.35, 0.25, 0.04), rng, 0.35, 1)
    b.loot("box", V(3.85, cells[0][0] + 0.55, 0.0))
    tp.papers(parts["debris"], 3.2, 4.6, cells[2][0] + 0.3, cells[2][1] - 0.6, 0.0, 3, rng, ("letter", "envelope"))


def corridors(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.bench_light(b, furniture, V(east[1] + 0.22, 1.6, 0.0), math.pi * 0.5, rng, 1.6)
    tp.notice_board(interior, V(east[1] + 0.002, 0.9, 1.55), V(1.0, 0.0, 0.0), 0.8, 0.6, rng, ("police_notice", "notice", "letter", "calendar"))
    tp.bucket_light(clutter, V(2.45, by - 0.35, 0.0), rng, "rusty_metal", False)
    bd.long_tool(clutter, V(2.55, by - 0.2, 0.0), V(2.45, by - 0.05, 1.4), "broom", rng)
    tp.bulb(b, interior, V((east[1] + cell_x) * 0.5, 2.0, c1), rng, 0.5, "cold")
    for y in (5.75, 6.15):
        rod(interior, "rusty_metal", V(east[0] - 0.002, y, 1.55), V(east[0] - 0.05, y, 1.58), 0.006, 4)
        tp.bucket_light(clutter, V(east[0] - 0.13, y, 1.32), rng, "town_paint_red", False)
    tp.wall_sheet(interior, V(east[0] - 0.006, -0.5, 1.75), V(-1.0, 0.0, 0.0), "police_notice", rng, 1.0, 0.0)
    tp.bulb(b, interior, V(0.5, -1.6, c1), rng, 0.55, "warm")
    tp.bulb(b, interior, V(0.0, 5.2, c1), rng, 0.55, "warm")
    tp.bucket_light(clutter, V(0.55, 4.6, 0.0), rng, "rusty_metal", True)
    bd.long_tool(clutter, V(-0.95, by - 0.12, 0.0), V(-0.85, by - 0.05, 1.45), "broom", rng)
    for k in range(2):
        p = V(0.68 + k * 0.22, by - 0.3, 0.0)
        emit(clutter, kit.geo_lathe([(0.0, 0.0), (0.05, 0.0), (0.055, 0.12), (0.05, 0.32), (0.0, 0.33)], 7), "leather_brown", kit.turned(p, rng.uniform(0.0, tau)) @ kit.Matrix.Scale(1.8, 4, V(1.0, 0.0, 0.0)), "given", True)
    tp.debris_field(parts, -0.05, 1.0, -2.0, 6.3, 0.0, rng, 4, 0, 4, 6)
    tp.debris_field(parts, east[1] + 0.1, cell_x - 0.1, -2.0, 6.3, 0.0, rng, 4, 0, 3, 0)
    tp.bench_light(b, furniture, V(0.55, by - 0.25, f1), 0.0, rng, 1.0)
    tp.framed(interior, V(west[1] + 0.006, 6.0, f1 + 1.65), V(1.0, 0.0, 0.0), 0.3, 0.4, tp.pr("portrait_b"), rng, "timber_beam", 0.02)
    tp.notice_board(interior, V(east[0] - 0.002, 2.2, f1 + 1.5), V(-1.0, 0.0, 0.0), 1.0, 0.7, rng)
    tp.framed(interior, V(east[0] - 0.006, -5.0, f1 + 1.6), V(-1.0, 0.0, 0.0), 0.5, 0.36, tp.pr("seascape"), rng, "timber_beam", 0.02)
    for x, y in ((0.0, -4.5), (0.5, 0.9), (0.0, 5.2)):
        tp.bulb(b, interior, V(x, y, c2), rng, 0.45, "warm")
    tp.papers(parts["debris"], -1.0, 1.0, -6.3, -0.4, f1, 4, rng, ("police_notice", "letter", "newspaper"))
    tp.debris_field(parts, -0.1, 1.0, -0.2, 6.3, f1, rng, 3, 0, 2, 0)


def offices(b, parts, rng, faces):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    inspector, cid = faces
    middle = (breast_y[0] + breast_y[1]) * 0.5
    hearth = V(inspector + 0.4, middle, f1)
    tp.mantel_set(clutter, V(inspector + 0.06, middle - 0.5, f1 + 1.16), V(0.0, 1.0, 0.0), V(1.0, 0.0, 0.0), 1.0, rng)
    tp.framed(interior, V(inspector + 0.006, middle, f1 + 1.75), V(1.0, 0.0, 0.0), 0.42, 0.55, tp.pr("portrait_a"), rng, "town_brass", 0.02)
    tp.fender(clutter, V(inspector + 0.42, middle - 0.55, f1 + 0.02), V(inspector + 0.42, middle + 0.55, f1 + 0.02), rng)
    tp.coal_scuttle(clutter, V(inspector + 0.3, breast_y[0] - 0.35, f1), rng)
    desk = V(-3.0, -4.65, f1)
    tp.desk_light(b, furniture, clutter, desk, 0.0, rng, 1.5, 0.8, 0.76, "timber_beam", "floorboards", ("papers", "phone", "lamp", "files"))
    tp.chair_light(furniture, V(-3.0, -5.4, f1), tk.facing(V(-3.0, -5.4, 0.0), V(-3.0, -4.0, 0.0)), rng, "timber_beam", "leather_brown")
    for position in (V(-3.45, -3.7, f1), V(-2.5, -3.75, f1)):
        tp.chair_light(furniture, position, tk.facing(position, desk) + rng.uniform(-0.25, 0.25), rng)
    tp.bookcase(b, furniture, clutter, V(-4.05, partition[0] - 0.17, f1), 0.0, rng, 1.0, 2.0, 0.32, "timber_beam", 0.6, 4)
    tp.filing_cabinet(b, furniture, V(-ix + 0.35, partition[0] - 0.3, f1), math.pi * 0.5, rng)
    tp.safe_light(b, furniture, V(-ix + 0.34, fy + 0.36, f1), math.pi * 0.5, rng, 1.4)
    b.loot("box", V(-4.6, -3.2, f1))
    bd.rug(clutter, V(-3.1, -4.4, f1), 2.4, 1.8, 0.02, rng, "town_carpet")
    tp.framed(interior, V(-2.0, partition[0] - 0.006, f1 + 1.75), V(0.0, -1.0, 0.0), 0.72, 0.5, tp.pr("map"), rng, "timber_beam", -0.02)
    for w in upper_windows[:2]:
        tp.curtain_light(clutter, V(w[0] - 0.1, fy + 0.08, w[3] + 0.12), V(w[1] + 0.1, fy + 0.08, w[3] + 0.12), 1.7, rng, "fabric_worn", 0.4)
    tk.pendant(b, interior, V(-3.1, -4.4, c2), rng, "town_brass", 0.6, "warm", 8)
    tp.papers(parts["debris"], -4.8, -1.6, -6.2, -2.6, f1, 6, rng, ("letter", "police_notice", "envelope", "newspaper"))
    tp.debris_field(parts, -4.9, -1.5, -6.2, -2.6, f1, rng, 4, 0, 0, 0)
    for position, yaw in ((V(2.6, -4.75, f1), -math.pi * 0.5), (V(3.35, -4.75, f1), math.pi * 0.5)):
        tp.desk_light(b, furniture, clutter, position, yaw, rng, 1.3, 0.75, 0.76, "timber_beam", "floorboards", ("papers", "typewriter") if yaw < 0.0 else ("phone", "lamp", "files"))
    tp.chair_light(furniture, V(1.82, -4.75, f1), tk.facing(V(1.82, -4.75, 0.0), V(2.6, -4.75, 0.0)) + 0.15, rng)
    tp.chair_light(furniture, V(4.25, -4.3, f1), 1.9, rng, fallen=True)
    for x in (2.5, 3.02, 3.54):
        tp.filing_cabinet(b, furniture, V(x, partition[0] - 0.36, f1), 0.0, rng, 4, "green" if x < 3.0 else "cream")
    tp.notice_board(interior, V(east[1] + 0.002, -5.0, f1 + 1.55), V(1.0, 0.0, 0.0), 1.3, 0.85, rng, ("notice", "letter", "poster", "card", "police_notice"))
    tp.framed(interior, V(4.4, partition[0] - 0.006, f1 + 1.7), V(0.0, -1.0, 0.0), 0.72, 0.5, tp.pr("map"), rng, "timber_beam", 0.02)
    tp.mantel_clock(clutter, V(cid - 0.12, middle, f1 + 1.16), -math.pi * 0.5, rng)
    bd.coat_rail(interior, clutter, V(ix, -3.4, f1 + 1.75), V(ix, -2.55, f1 + 1.75), V(-1.0, 0.0, 0.0), rng, 1)
    tp.helmet(clutter, V(4.9, -6.15, f1), rng, None, True)
    for w in upper_windows[2:]:
        tp.curtain_light(clutter, V(w[0] - 0.1, fy + 0.08, w[3] + 0.12), V(w[1] + 0.1, fy + 0.08, w[3] + 0.12), 1.6, rng, "fabric_tartan", 0.45)
    tk.pendant(b, interior, V(2.95, -4.75, c2), rng, "town_metal", 0.6, "warm", 8)
    tp.papers(parts["debris"], 1.5, 5.0, -6.2, -2.7, f1, 12, rng, ("letter", "police_notice", "notice", "envelope", "newspaper", "card"))
    tp.debris_field(parts, 1.5, 5.0, -6.2, -2.7, f1, rng, 4, 0, 0, 0)


def back_rooms(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.bookcase(b, furniture, clutter, V(3.0, partition[1] + 0.2, f1), math.pi, rng, 1.2, 2.1, 0.36, "timber_beam", 0.45, 4)
    tp.bookcase(b, furniture, clutter, V(4.5, partition[1] + 0.2, f1), math.pi, rng, 1.2, 2.1, 0.36, "timber_beam", 0.4, 4)
    tp.table_light(furniture, 3.5, -0.4, f1, 1.2, 0.7, 0.76, rng)
    tk.col(b, "wood", "table", 2.9, 4.1, -0.75, -0.05, f1, f1 + 0.76)
    tp.desk_lamp(clutter, V(3.1, -0.25, f1 + 0.76), 2.6, rng)
    tp.papers(clutter, 3.2, 4.0, -0.7, -0.1, f1 + 0.76, 4, rng, ("letter", "notice", "police_notice"))
    tp.chair_light(furniture, V(3.5, 0.2, f1), math.pi + 0.2, rng)
    for center, yaw in ((V(1.65, 0.85, f1), 0.3), (V(1.8, 0.2, f1), -0.1)):
        tp.crate_light(clutter, center, (0.45, 0.4, 0.32), yaw, rng)
    tk.col(b, "wood", "crates", 1.35, 2.1, -0.05, 1.1, f1, f1 + 0.32)
    b.loot("box", V(5.0, -0.4, f1))
    tp.bulb(b, interior, V(3.5, -0.3, c2), rng, 0.5, "warm")
    tp.papers(parts["debris"], 1.4, 5.3, -2.0, 1.3, f1, 16, rng, ("letter", "police_notice", "notice", "envelope", "card"))
    tp.debris_field(parts, 1.4, 5.3, -2.0, 1.3, f1, rng, 5, 0, 0, 0)
    tp.gas_cooker(b, furniture, clutter, V(4.85, by - 0.3, f1), 0.0, rng)
    tp.sink_light(b, furniture, clutter, V(2.65, by - 0.25, f1), 0.0, rng)
    bd.cabinet(furniture, V(2.6, records_split[1] + 0.26, f1), 1.3, 0.5, 0.0, 0.88, math.pi, rng, "timber_planks_weathered", green, 2, 2, 1)
    local_block(furniture, "floorboards", kit.turned(V(2.6, records_split[1] + 0.26, f1), math.pi), -0.68, 0.68, -0.28, 0.25, 0.88, 0.92, 0.0, "board")
    tk.col(b, "wood", "cupboard", 1.92, 3.28, records_split[1], records_split[1] + 0.54, f1, f1 + 0.92)
    tp.wireless(clutter, V(2.25, records_split[1] + 0.3, f1 + 0.92), math.pi, rng)
    tp.cup_light(clutter, V(2.75, records_split[1] + 0.3, f1 + 0.92), rng)
    tp.label_jar(clutter, V(3.0, records_split[1] + 0.25, f1 + 0.92), rng, "jam")
    bd.shelf(interior, V(2.0, records_split[1], f1 + 1.6), V(3.2, records_split[1], f1 + 1.6), 0.22, V(0.0, 1.0, 0.0), rng)
    for k, label in enumerate(("cocoa", "milk", "soup", "beans")):
        tp.label_can(clutter, V(2.15 + k * 0.28, records_split[1] + 0.11, f1 + 1.6), rng, label)
    table = V(3.6, 3.75, f1)
    tp.table_light(furniture, table.x, table.y, f1, 1.5, 0.85, 0.76, rng)
    tk.col(b, "wood", "table", table.x - 0.75, table.x + 0.75, table.y - 0.43, table.y + 0.43, f1, f1 + 0.76)
    for position in (V(2.75, 3.45, f1), V(4.45, 4.05, f1), V(3.3, 4.55, f1)):
        tp.chair_light(furniture, position, tk.facing(position, table) + rng.uniform(-0.3, 0.3), rng)
    tp.chair_light(furniture, V(4.1, 2.75, f1), 0.8, rng, fallen=True)
    tp.cup_light(clutter, V(3.3, 3.6, f1 + 0.76), rng)
    tp.cup_light(clutter, V(3.95, 3.95, f1 + 0.76), rng)
    tp.plate_light(clutter, V(3.65, 3.55, f1 + 0.76), rng)
    tp.label_can(clutter, V(3.85, 3.6, f1 + 0.76), rng, "beans", lying=True)
    b.loot("food", V(3.75, 3.85, f1 + 0.76))
    b.loot("food", V(1.75, 6.15, f1))
    tp.dartboard(interior, V(4.5, records_split[1] + 0.002, f1 + 1.73), V(0.0, 1.0, 0.0), rng)
    tp.wall_sheet(interior, V(east[1] + 0.006, 2.6, f1 + 1.6), V(1.0, 0.0, 0.0), "calendar", rng, 1.0, 0.03)
    tp.wall_clock(interior, V(east[1] + 0.015, 3.6, f1 + 2.1), V(1.0, 0.0, 0.0), rng, 0.16)
    tk.pendant(b, interior, V(3.6, 3.75, c2), rng, "town_metal", 0.55, "warm", 8)
    tp.debris_field(parts, 1.5, 5.2, 2.0, 6.2, f1, rng, 4, 0, 3, 0)
    tp.locker_row(b, furniture, V(-ix + 0.25, 1.2, f1), math.pi * 0.5, 7, rng, "blue")
    tp.locker_row(b, furniture, V(-3.4, locker_split[0] - 0.25, f1), 0.0, 5, rng, "blue")
    for k in (0, 3):
        tp.helmet(clutter, V(-ix + 0.25, -0.1 + k * 0.62, f1 + 1.85), rng)
    tp.bench_light(b, furniture, V(-3.3, 0.35, f1), math.pi * 0.5, rng, 2.0)
    b.loot("box", V(-3.3, -0.15, f1 + 0.45))
    bd.coat_rail(interior, clutter, V(-4.6, partition[1], f1 + 1.7), V(-2.0, partition[1], f1 + 1.7), V(0.0, 1.0, 0.0), rng, 1)
    tp.wall_mirror(interior, V(west[0] - 0.005, 1.6, f1 + 1.55), V(-1.0, 0.0, 0.0), 0.45, 0.6, rng)
    for k in range(3):
        p = V(-2.4 + k * 0.25, -1.75 + rng.uniform(-0.1, 0.1), f1)
        emit(clutter, kit.geo_lathe([(0.0, 0.0), (0.05, 0.0), (0.055, 0.12), (0.05, 0.32), (0.0, 0.33)], 7), "leather_brown", kit.turned(p, rng.uniform(0.0, tau)) @ kit.Matrix.Scale(1.8, 4, V(1.0, 0.0, 0.0)), "given", True)
    tp.bulb(b, interior, V(-3.4, 0.4, c2), rng, 0.5, "warm")
    tp.debris_field(parts, -5.0, -1.5, -2.0, 2.6, f1, rng, 4, 0, 3, 0)
    tp.cubicles(b, furniture, -ix, -3.55, by, 5.3, f1, 2, rng, green, (False, True))
    for x in (-4.95, -4.2):
        tp.basin(b, furniture, V(x, locker_split[1] + 0.24, f1), math.pi, rng, 8)
        tp.wall_mirror(interior, V(x, locker_split[1] + 0.006, f1 + 1.55), V(0.0, 1.0, 0.0), 0.4, 0.5, rng)
    tp.aid_cabinet(interior, clutter, V(west[0] - 0.002, 3.75, f1 + 1.45), V(-1.0, 0.0, 0.0), rng, 2.6)
    b.loot("medical", V(west[0] - 0.4, 3.75, f1))
    tp.bulb(b, interior, V(-3.3, 4.7, c2), rng, 0.45, "cold")
    tk.chips(parts["debris"], "kitchen_tiles", -4.8, -2.0, 3.3, 5.0, f1, 8, rng, (0.03, 0.07), (0.006, 0.008))
    tp.papers(parts["debris"], -4.6, -2.0, 3.4, 5.0, f1, 2, rng, ("newspaper",))


def exterior(b, parts, gable, rng):
    roof = parts["roof"]
    clutter = parts["clutter"]
    plants = parts["plants"]
    gutter_z = gable.eave_top - 0.05 - 0.06
    tk.terrace_roof(b, parts, -hx, hx, gable, rng, 0.35, 0.012, [(2.0, 3.2, 2.6, 3.8, 1.0)], 0.03, True, "rock", True, 1.4, True, (-1.0, 1.0), 0.36, 0.76, 0.52)
    tk.stack(b, roof, -hx + 0.42, 0.0, 0.75, 1.2, gable.top(0.6) - 0.3, gable.ridge_top + 1.0, rng, 3)
    tk.stack(b, roof, hx - 0.42, 0.0, 0.75, 1.2, gable.top(0.6) - 0.3, gable.ridge_top + 0.85, rng, 2)
    tk.downpipe_light(roof, hx - 0.3, -gable.edge - 0.04, -hy, gutter_z - 0.03, -0.15, rng)
    tk.downpipe_light(roof, -hx + 0.3, -gable.edge - 0.04, -hy, gutter_z - 0.03, -0.15, rng, broken=1.2, lean=0.05)
    tk.downpipe_light(roof, hx - 0.3, gable.edge + 0.04, hy, gutter_z - 0.03, -0.15, rng)
    tk.ivy_light(plants, V(-hx - 0.02, 3.2, -0.15), V(-1.0, 0.0, 0.0), rng, 4.6, 1.2, 4, 8.0)
    tk.ivy_light(plants, V(2.6, hy + 0.02, -0.15), V(0.0, 1.0, 0.0), rng, 3.8, 0.9, 3, 8.0)
    bd.dustbin(clutter, V(-2.2, hy + 0.45, -0.15), rng)
    tk.col(b, "metal", "bin", -2.45, -1.95, hy + 0.2, hy + 0.7, -0.15, 0.5)
    tk.weeds_line(plants, V(-hx + 0.4, -hy - 0.12, -0.15), V(door[0] - 0.5, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(door[1] + 0.5, -hy - 0.12, -0.15), V(hx - 0.4, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(-hx + 0.3, hy + 0.12, -0.15), V(hx - 0.3, hy + 0.12, -0.15), rng, 4)
    tk.weeds_line(plants, V(-hx - 0.12, -hy + 0.3, -0.15), V(-hx - 0.12, hy - 0.3, -0.15), rng, 4)
    tk.weeds_line(plants, V(hx + 0.12, -hy + 0.3, -0.15), V(hx + 0.12, hy - 0.3, -0.15), rng, 3)
    for index in range(6):
        kit.grass_tuft(plants, V(rng.uniform(-hx, hx), rng.choice((-1.0, 1.0)) * (gable.edge + 0.06), gutter_z + 0.02), rng, (0.06, 0.2), (3, 5), 0.03)
    for index in range(3):
        lump(plants, "roof_moss", V(rng.uniform(-hx + 1.0, hx - 1.0), rng.uniform(-0.05, 0.05), gable.ridge_top + 0.09), (rng.uniform(0.06, 0.14), 0.08, 0.03), rng, 0.3, 1)
    tp.papers(parts["debris"], -5.0, 5.0, -7.45, -7.12, -0.15, 6, rng, ("newspaper", "police_notice", "card", "notice"))
    tk.chips(parts["debris"], "slate_roof", -5.0, 5.0, -7.45, -7.15, -0.15, 6, rng, (0.08, 0.17), (0.006, 0.008))
    tk.chips(parts["debris"], "glass_dirty", 3.3, 5.0, -7.45, -7.12, -0.15, 6, rng, (0.02, 0.06), (0.003, 0.004))
    tk.chips(parts["debris"], "slate_roof", -4.0, 4.0, hy + 0.3, hy + 0.9, -0.15, 8, rng, (0.08, 0.17), (0.006, 0.008))


def police():
    b = kit.Build("police", 1501)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    shell_walls(b, parts, gable, rng)
    doorcase(b, parts, rng)
    openings(b, parts, rng)
    floors(b, parts, rng)
    ground_walls(b, parts, rng)
    upper_walls(b, parts, rng)
    faces = breasts(b, parts, rng)
    finishes(parts, rng, faces)
    front_office(b, parts, rng)
    interview_room(b, parts, rng)
    armoury(b, parts, rng)
    cell_block(b, parts, rng)
    corridors(b, parts, rng)
    offices(b, parts, rng, faces)
    back_rooms(b, parts, rng)
    exterior(b, parts, gable, rng)
    return b


def police_far():
    b = kit.Build("police_far", 1502)
    shell = b.part("shell", 30.0)
    gable = gable_of()
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    wide_front = kit.facade("front", hx, hy)
    wide_back = kit.facade("back", hx, hy)
    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [], wall_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [], wall_t)
    outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
    for side, openings_list in (("left", left_windows), ("right", right_windows)):
        frame = kit.facade(side, hx, hy)
        kit.wall(shell, stone, frame, outline, [], wall_t)
        for w in openings_list:
            kit.skin(shell, "glass_dirty", frame, kit.rect(*w), [], 0.004, 0.001, False)
    kit.skin(shell, render, wide_front, kit.rect(-hx, hx, 3.52, wall_top - 0.02), [kit.rect(*w) for w in upper_windows + [lamp_window]], 0.02, 0.0, False)
    for w in windows + upper_windows + [lamp_window]:
        kit.skin(shell, "glass_dirty", wide_front, kit.rect(*w), [], 0.004, 0.001, False)
    kit.skin(shell, "soot", wide_front, kit.rect(door[0], door[1], 0.0, door[3]), [], 0.004, 0.001, False)
    kit.skin(shell, render, wide_back, kit.rect(-hx, hx, 1.3, wall_top - 0.4), [kit.rect(o[0], o[1], max(o[2], 1.31), o[3]) for o in back_windows + [back_door]], 0.018, 0.0, False)
    for o in back_windows + [back_door]:
        kit.skin(shell, "glass_dirty" if o[2] > 0.5 else "soot", wide_back, kit.rect(*o), [], 0.004, 0.001, False)
    frame_block(shell, dressed, wide_front, -hx - 0.05, hx + 0.05, 3.3, 3.52, -0.08, 0.0)
    frame_block(shell, render, wide_front, -hx - 0.04, hx + 0.04, wall_top - 0.36, wall_top - 0.02, -0.13, 0.0)
    frame_block(shell, dressed, wide_front, -hx, hx, -0.5, 0.42, -0.045, 0.0)
    frame_block(shell, dressed, front, door[0] - 0.44, door[1] + 0.44, 3.06, 3.5, -0.2, 0.0)
    frame_block(shell, navy, front, -0.9, 0.9, 3.1, 3.32, -0.21, -0.2)
    tk.atlas_panel(shell, "town_signs", kit.frame_point(front, 0.0, 3.21, 0.212), V(0.0, -1.0, 0.0), 1.74, 0.2, tp.sg("police_board"), 0.0, 0.0)
    lamp = V(0.0, -hy - 0.5, 4.17)
    for direction in (V(0.0, -1.0, 0.0), V(1.0, 0.0, 0.0), V(-1.0, 0.0, 0.0)):
        tk.atlas_panel(shell, "town_signs", lamp + direction * 0.15, direction, 0.27, 0.36, tp.sg("police_lamp"), 0.0, 0.0)
    block(shell, "town_paint_black", lamp + V(-0.17, -0.17, 0.2), lamp + V(0.17, 0.17, 0.26))
    kit.roof_slab(shell, gable, -1.0, -hx, hx, "slate_roof", 0.2)
    kit.roof_slab(shell, gable, 1.0, -hx, hx, "roof_moss", 0.2)
    block(shell, "terracotta", V(-hx, -0.13, gable.ridge_top - 0.04), V(hx, 0.13, gable.ridge_top + 0.09))
    for cx, top, pots in ((-hx + 0.42, gable.ridge_top + 1.0, (-0.3, 0.0, 0.3)), (hx - 0.42, gable.ridge_top + 0.85, (-0.2, 0.2))):
        block(shell, dressed, V(cx - 0.375, -0.6, gable.top(0.6) - 0.3), V(cx + 0.375, 0.6, top + 0.12))
        for dy in pots:
            block(shell, "terracotta", V(cx - 0.08, dy - 0.08, top + 0.12), V(cx + 0.08, dy + 0.08, top + 0.5))
    return b
