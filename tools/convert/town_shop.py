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
hx = 3.5
hy = 5.0
ix = 3.25
front_t = 0.4
back_t = 0.4
fy = -hy + front_t
by = hy - back_t
glass_y = -4.92
c1 = 3.35
f1 = 3.6
c2 = 6.1
head = 3.05
paint = "painted_wood_green"
window_paint = "painted_wood_white"
stone = "granite_rubble"
dressed = "granite_ashlar"
render = "render_white"
windows = [(-3.22, -0.66), (0.66, 3.22)]
lobby = (-0.66, 0.66, -4.2)
shop_door = (-0.575, 0.575, 0.0, 2.3)
upper_windows = [(-2.75, -1.7, 4.4, 5.85), (-0.52, 0.52, 4.4, 5.85), (1.7, 2.75, 4.4, 5.85)]
back_door = (-2.65, -1.5, 0.0, 2.22)
back_windows = [(0.0, 1.0, 1.0, 2.2), (0.5, 1.6, 4.4, 5.6), (-2.5, -1.4, 4.4, 5.8)]
partition = (1.0, 1.1)
store_door = (-3.1, -1.95, 0.0, 2.22)
stair_x = (-3.25, -2.25)
stair_foot = 3.9
stair_top = 0.0
stair_run = stair_foot - stair_top
well = (-3.25, -2.25, 0.0, 2.4)
lounge_wall = (-1.1, -1.0)
hall_wall = (0.0, 0.1)
split_x = (0.5, 0.6)


def gable_of():
    return kit.Gable(-hx, hx, hy, 0.3, 6.26, 30.0)


def shopfront(b, parts, rng):
    joinery = parts["joinery"]
    shell = parts["shell"]
    clutter = parts["clutter"]
    front = kit.facade("front", hx, hy)
    for edge, sign in ((-hx, 1.0), (hx, -1.0)):
        a0 = min(edge, edge + sign * 0.28)
        a1 = max(edge, edge + sign * 0.28)
        frame_block(joinery, paint, front, a0, a1, 0.45, head + 0.05, -0.08, 0.02, 0.0, "board")
        frame_block(joinery, paint, front, a0 + 0.04, a1 - 0.04, 0.6, head - 0.1, -0.1, -0.08, 0.0, "board")
        frame_block(shell, dressed, front, max(a0 - 0.01, -hx), min(a1 + 0.01, hx), -0.4, 0.45, -0.11, 0.02, 0.01)
        frame_block(joinery, paint, front, a0 + 0.02, a1 - 0.02, head + 0.05, 3.75, -0.24, 0.02, 0.0, "board")
        frame_block(joinery, paint, front, a0, a1, 3.75, 3.82, -0.27, 0.02, 0.0, "board")
    frame_block(joinery, paint, front, -3.22, 3.22, 3.1, 3.7, -0.1, 0.02, 0.0, "board")
    tk.atlas_quad(joinery, "town_signs", [kit.frame_point(front, -3.2, 3.11, 0.101), kit.frame_point(front, 3.2, 3.11, 0.101), kit.frame_point(front, 3.2, 3.69, 0.101), kit.frame_point(front, -3.2, 3.69, 0.101)], tp.sg("shop_fascia"))
    frame_block(joinery, paint, front, -3.3, 3.3, 3.7, 3.8, -0.2, 0.02, 0.0, "board")
    frame_block(joinery, paint, front, -3.36, 3.36, 3.8, 3.86, -0.25, 0.02, 0.0, "board")
    frame_block(joinery, "rusty_metal", front, -3.36, 3.36, 3.86, 3.88, -0.27, 0.05)
    frame_block(joinery, paint, front, -3.1, 3.1, 2.97, 3.1, -0.26, -0.1, 0.0, "board")
    tp.curtain_light(clutter, kit.frame_point(front, -3.0, 2.97, 0.25), kit.frame_point(front, -0.9, 2.97, 0.25), 0.95, rng, "mattress", 1.0, True, 9, 5, False)
    tp.curtain_light(clutter, kit.frame_point(front, 1.5, 2.97, 0.25), kit.frame_point(front, 2.3, 2.97, 0.25), 0.55, rng, "mattress", 1.0, True, 4, 4, False)
    matrix = kit.frame_matrix(front)
    states = {0: ("missing", "shard"), 1: ("whole", "shard")}
    for index, (a0, a1) in enumerate(windows):
        frame_block(joinery, paint, front, a0, a1, 0.0, 0.7, 0.02, 0.14, 0.0, "board")
        for p0, p1 in ((a0 + 0.1, (a0 + a1) * 0.5 - 0.05), ((a0 + a1) * 0.5 + 0.05, a1 - 0.1)):
            frame_block(joinery, paint, front, p0, p1, 0.12, 0.58, 0.0, 0.02, 0.0, "board")
        frame_block(joinery, paint, front, a0 - 0.02, a1 + 0.02, 0.7, 0.77, -0.04, 0.16, 0.0, "board")
        middle = (a0 + a1) * 0.5
        for x0, x1 in ((a0, a0 + 0.07), (a1 - 0.07, a1), (middle - 0.035, middle + 0.035)):
            frame_block(joinery, paint, front, x0, x1, 0.77, head, 0.02, 0.12, 0.0, "board")
        frame_block(joinery, paint, front, a0, a1, 2.55, 2.63, 0.02, 0.12, 0.0, "board")
        frame_block(joinery, paint, front, a0, a1, head - 0.05, head + 0.05, 0.0, 0.12, 0.0, "board")
        lower = states[index]
        kit.pane(joinery, matrix, a0 + 0.07, middle - 0.035, 0.77, 2.55, 0.07, lower[0], rng)
        kit.pane(joinery, matrix, middle + 0.035, a1 - 0.07, 0.77, 2.55, 0.07, lower[1], rng)
        if index == 0:
            for shard in range(3):
                x = rng.uniform(a0 + 0.1, middle - 0.1)
                kit.pane(joinery, matrix, x - 0.12, x + 0.12, 0.77, 0.77 + rng.uniform(0.15, 0.35), 0.07, "shard", rng)
        lights = 4
        for light in range(lights):
            l0 = a0 + 0.07 + (a1 - a0 - 0.14) * light / lights
            l1 = a0 + 0.07 + (a1 - a0 - 0.14) * (light + 1) / lights
            kit.pane(joinery, matrix, l0 + 0.012, l1 - 0.012, 2.63, head - 0.05, 0.07, rng.choice(("whole", "whole", "shard")), rng)
            if light:
                frame_block(joinery, paint, front, l0 - 0.012, l0 + 0.012, 2.63, head - 0.05, 0.04, 0.1)
        tk.col(b, "wood", "stall", a0, a1, -hy, -hy + 0.16, -1.5, 0.77)
        tk.col(b, "glass", "shopfront", a0, a1, -hy, -hy + 0.12, 2.55 if index == 0 else 0.77, head + 0.05)
    tk.atlas_panel(joinery, "town_signs", kit.frame_point(front, 1.4, 2.1, -0.067), V(0.0, -1.0, 0.0), 1.0, 0.5, tp.sg("shop_window"), 0.0, 0.0)
    tk.atlas_panel(joinery, "town_signs", kit.frame_point(front, 2.75, 1.55, -0.064), V(0.0, -1.0, 0.0), 0.36, 0.12, tp.sg("open_sign"), 0.06, 0.0)
    x0, x1, y_door = lobby
    for x, normal in ((x0, 1.0), (x1, -1.0)):
        side = kit.plane(V(x, 0.0, 0.0), V(normal, 0.0, 0.0))
        along = side[1]
        a_front = V(0.0, -hy + 0.02, 0.0).dot(along)
        a_back = V(0.0, y_door, 0.0).dot(along)
        s0, s1 = min(a_front, a_back), max(a_front, a_back)
        frame_block(joinery, paint, side, s0, s1, 0.0, 0.7, -0.06, 0.06, 0.0, "board")
        frame_block(joinery, paint, side, s0, s1, 0.7, 0.77, -0.08, 0.08, 0.0, "board")
        kit.pane(joinery, kit.frame_matrix(side), s0 + 0.06, s1 - 0.06, 0.77, 2.55, -0.002, "whole" if normal > 0 else "shard", rng)
        frame_block(joinery, paint, side, s0, s1, 2.55, 2.63, -0.05, 0.05, 0.0, "board")
        frame_block(joinery, paint, side, s0, s0 + 0.06, 0.77, head, -0.05, 0.05, 0.0, "board")
        frame_block(joinery, paint, side, s1 - 0.06, s1, 0.77, head, -0.05, 0.05, 0.0, "board")
        tk.col(b, "glass", "lobby", x - 0.06, x + 0.06, -hy, y_door, 0.0, head + 0.05)
    block(joinery, paint, V(x0, -hy, head), V(x1, y_door, head + 0.06), 0.0, "board")
    block(parts["floors"], "town_tiles", V(x0, -hy, -0.03), V(x1, y_door + 0.05, 0.0), 0.0, "world")
    block(parts["shell"], dressed, V(x0 - 0.1, -hy - 0.3, -0.45), V(x1 + 0.1, -hy + 0.02, -0.06), 0.015)
    tk.col(b, "rock", "lobby_floor", x0, x1, -hy - 0.3, y_door, -1.5, 0.0)
    door_frame = kit.plane(V(0.0, y_door, 0.0), V(0.0, -1.0, 0.0))
    tk.door_unit(joinery, door_frame, shop_door[0], shop_door[1], 0.0, shop_door[3], 0.1, paint, rng, "high", 96.0, "panel")
    for index in range(3):
        p0 = shop_door[0] + 0.04 + (shop_door[1] - shop_door[0] - 0.08) * index / 3
        p1 = shop_door[0] + 0.04 + (shop_door[1] - shop_door[0] - 0.08) * (index + 1) / 3
        kit.pane(joinery, kit.frame_matrix(door_frame), p0 + 0.01, p1 - 0.01, shop_door[3] + 0.05, head - 0.04, 0.04, rng.choice(("whole", "shard", "missing")), rng)
    frame_block(joinery, paint, door_frame, shop_door[0], shop_door[1], shop_door[3], shop_door[3] + 0.05, 0.0, 0.1, 0.0, "board")
    for x_post in (shop_door[0] - 0.05, shop_door[1]):
        block(joinery, paint, V(x_post, y_door - 0.02, 0.0), V(x_post + 0.05, y_door + 0.1, head), 0.0, "board")
    for x_a, x_b in ((x0, shop_door[0] - 0.05), (shop_door[1] + 0.05, x1)):
        block(joinery, paint, V(x_a, y_door, 0.0), V(x_b, y_door + 0.1, head), 0.0, "board")
        tk.col(b, "wood", "door_screen", x_a, x_b, y_door, y_door + 0.1, 0.0, head)
    tk.col(b, "glass", "fanlight", shop_door[0], shop_door[1], y_door, y_door + 0.1, shop_door[3], head)


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    kit.wall(shell, stone, front, kit.rect(-ix, ix, head, wall_top), [kit.rect(*w) for w in upper_windows], front_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, head, wall_top, front_t, upper_windows)
    back_holes = [kit.rect(back_door[0], back_door[1], -0.05, back_door[3])] + [kit.rect(*w) for w in back_windows]
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), back_holes, back_t)
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, -1.5, wall_top, back_t, [back_door] + back_windows)
    for frame in (left, right):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
        kit.wall(shell, stone, frame, outline, [], 0.25)
        kit.wall_boxes(b, "rock", "party", frame, -hy, hy, -1.5, wall_top, 0.25, [])
    bd.gable_cols(b, "party_gable", -hx, -ix, gable, wall_top, 0.0)
    bd.gable_cols(b, "party_gable", ix, hx, gable, wall_top, 0.0)
    block(shell, stone, V(-ix, -hy, -1.5), V(ix, fy, -0.05), 0.0, "world")
    wide_front = kit.facade("front", hx, hy)
    tk.render_skin(shell, wide_front, -hx, hx, wall_top - 0.02, upper_windows, rng, 6, render, 0.02, 2, (3.88, 3.9), 0.0)
    for w in upper_windows:
        kit.sill_stone(shell, dressed, front, w[0], w[1], w[2], 0.16, 0.06, 0.08, 0.07)
        kit.lintel_stone(shell, dressed, front, w[0], w[1], w[3], 0.22, 0.25, 0.03, 0.14)
    frame_block(shell, "render_white", wide_front, -hx, hx, wall_top - 0.32, wall_top - 0.18, -0.06, 0.0, 0.006)
    frame_block(shell, "render_white", wide_front, -hx, hx, wall_top - 0.18, wall_top - 0.02, -0.03, 0.0, 0.004)
    wide_back = kit.facade("back", hx, hy)
    tk.render_skin(shell, wide_back, -hx, hx, wall_top - 0.4, [back_door] + back_windows, rng, 6, "render_white", 0.018, 2, (0.5, 1.2), 0.7)
    bd.damp_band(shell, wide_back, -hx, hx, rng, 0.4, 1.2, "granite_rubble_damp", -0.2, 0.003, [(back_door[0] - 0.05, back_door[1] + 0.05)])
    return wall_top


def openings(b, parts, rng):
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    for index, w in enumerate(upper_windows):
        tk.sash(b, parts, front, w, front_t, rng, window_paint, 0.1, (0.0, 0.3, 0.0)[index], (0.4, 0.2, 0.3)[index], 0.3, 2, 2, render, None, None, False, index == 2)
    tk.sash(b, parts, back, back_windows[0], back_t, rng, window_paint, 0.1, 0.0, 0.1, 0.3, 2, 2, None, dressed, None, False, True)
    tk.sash(b, parts, back, back_windows[1], back_t, rng, window_paint, 0.1, 0.2, 0.3, 0.3, 2, 2, None, dressed)
    tk.sash(b, parts, back, back_windows[2], back_t, rng, window_paint, 0.1, 0.0, 0.4, 0.3, 2, 2, None, dressed)
    a0, a1, z0, z1 = back_door
    tk.door_unit(parts["joinery"], back, a0, a1, 0.0, z1, back_t, "painted_wood_bauxite", rng, "low", 100.0, "ledged", True, 0.0, 0.06, 4.0, paint)
    block(parts["shell"], dressed, V(-a1 - 0.08, hy - 0.04, -0.3), V(-a0 + 0.08, hy + 0.34, -0.06), 0.012)
    tk.col(b, "rock", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
    tk.col(b, "rock", "step", -a1 - 0.08, -a0 + 0.08, hy, hy + 0.34, -0.6, -0.06)


def interior_walls(b, parts, rng):
    interior = parts["interior"]
    joinery = parts["joinery"]
    floors = parts["floors"]
    tk.board_floor(floors, -ix, ix, fy - 0.3, partition[0], 0.0, rng, "y", [(lobby[0], lobby[1], fy - 0.3, lobby[2])])
    block(floors, "concrete", V(-2.25, partition[0], -0.1), V(ix, by, 0.0), 0.0, "world")
    tk.col(b, "wood", "ground", -ix, ix, fy - 0.35, by, -0.3, 0.0)
    block(floors, "timber_beam", V(1.95, partition[0], -0.02), V(3.1, partition[1], 0.005), 0.003)
    tk.board_floor(floors, -ix, ix, fy, by, f1, rng, "y", [well])
    tk.tile_floor(floors, "town_lino", -2.25, ix, lounge_wall[1], hall_wall[0], f1 + 0.004, 0.006)
    tk.floor_cols(b, "wood", "upper", -ix, ix, fy, by, c1, f1, [well])
    tk.col(b, "wood", "attic", -ix, ix, fy, by, c2, c2 + 0.25)
    kit.joists(floors, "timber_beam", -2.25, ix, partition[1], by, f1 - 0.025, "x", 0.45, 0.08, 0.2)
    block(floors, "painted_wood_white", V(well[1], well[2], c1 - 0.01), V(well[1] + 0.03, well[3], f1 + 0.012), 0.0, "board")
    block(floors, "painted_wood_white", V(well[0], well[3], c1 - 0.01), V(well[1], well[3] + 0.03, f1 + 0.012), 0.0, "board")
    block(joinery, paint, V(-ix, fy, head), V(ix, fy + 0.12, c1), 0.0, "board")
    wall = kit.plane(V(0.0, partition[1], 0.0), V(0.0, 1.0, 0.0))
    kit.wall(interior, "plaster_interior", wall, kit.notched(-ix, 2.25, 0.0, c1, [(store_door[0], store_door[1], store_door[3])]), [], partition[1] - partition[0])
    kit.wall_boxes(b, "wood", "partition", wall, -ix, 2.25, 0.0, c1, partition[1] - partition[0], [store_door])
    tk.door_unit(joinery, wall, store_door[0], store_door[1], 0.0, store_door[3], partition[1] - partition[0], paint, rng, "high", -100.0, "ledged")
    enclosure = kit.plane(V(stair_x[1], 0.0, 0.0), V(1.0, 0.0, 0.0))
    kit.wall(interior, "plaster_interior", enclosure, kit.rect(stair_top, partition[1], 0.0, c1), [], 0.08)
    tk.col(b, "wood", "enclosure", stair_x[1] - 0.08, stair_x[1], stair_top, partition[1], 0.0, c1)
    face = kit.plane(V(0.0, stair_top, 0.0), V(0.0, -1.0, 0.0))
    kit.wall(interior, "plaster_interior", face, kit.rect(stair_x[0], stair_x[1], 0.0, c1), [], 0.08)
    tk.col(b, "wood", "enclosure", stair_x[0], stair_x[1], stair_top, stair_top + 0.08, 0.0, c1)
    frame_block(joinery, paint, face, -3.0, -2.45, 0.05, 1.85, -0.015, 0.0, 0.0, "board")
    frame_block(joinery, "town_brass", face, -2.55, -2.52, 0.95, 1.0, -0.03, -0.015)
    tk.under_stair_panel(joinery, stair_x[1], stair_foot, 0.0, stair_foot - partition[1], (stair_foot - partition[1]) * f1 / stair_run, -1.0, rng, paint, None, 0.03, 1.0)
    tk.stair_flight(b, parts, stair_x[0], stair_x[1], stair_foot, 0.0, stair_run, f1, 16, rng, -1.0, "floorboards", "painted_wood_white", "town_carpet", "town_brass")
    hall = kit.plane(V(0.0, lounge_wall[0], 0.0), V(0.0, -1.0, 0.0))
    lounge_door = (-0.575, 0.575, f1, f1 + 2.2)
    kit.wall(interior, "plaster_interior", hall, kit.notched(-ix, ix, f1, c2, [(lounge_door[0], lounge_door[1], lounge_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "lounge_wall", hall, -ix, ix, f1, c2, 0.1, [lounge_door])
    tk.door_unit(joinery, hall, lounge_door[0], lounge_door[1], f1, 2.2, 0.1, "painted_wood_white", rng, "high", -92.0, "panel")
    back_rooms = kit.plane(V(0.0, hall_wall[1], 0.0), V(0.0, 1.0, 0.0))
    kitchen_door = (0.45, 1.6, f1, f1 + 2.2)
    bed_door = (-2.45, -1.3, f1, f1 + 2.2)
    kit.wall(interior, "plaster_interior", back_rooms, kit.notched(-ix, 2.25, f1, c2, [(bed_door[0], bed_door[1], bed_door[3]), (kitchen_door[0], kitchen_door[1], kitchen_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "back_rooms", back_rooms, -ix, 2.25, f1, c2, 0.1, [bed_door, kitchen_door])
    tk.door_unit(joinery, back_rooms, kitchen_door[0], kitchen_door[1], f1, 2.2, 0.1, "painted_wood_white", rng, "high", -88.0, "panel")
    tk.door_unit(joinery, back_rooms, bed_door[0], bed_door[1], f1, 2.2, 0.1, "painted_wood_white", rng, "high", -90.0, "panel")
    split = kit.plane(V(split_x[1], 0.0, 0.0), V(1.0, 0.0, 0.0))
    kit.wall(interior, "plaster_interior", split, kit.rect(hall_wall[1], by, f1, c2), [], 0.1)
    kit.wall_boxes(b, "wood", "split", split, hall_wall[1], by, f1, c2, 0.1, [])
    bd.balustrade(b, joinery, V(well[1] + 0.02, well[2] + 0.12, f1), V(well[1] + 0.02, well[3], f1), rng, 0.92, 0.12, "timber_beam", "painted_wood_white", 0.1, (True, True), True, "well")
    bd.balustrade(b, joinery, V(well[0], well[3] + 0.02, f1), V(well[1] + 0.02, well[3] + 0.02, f1), rng, 0.92, 0.12, "timber_beam", "painted_wood_white", 0.1, (False, False), True, "well")
    return (-0.575, 0.575, f1, f1 + 2.2), (-1.6, -0.45, f1, f1 + 2.2), (1.3, 2.45, f1, f1 + 2.2)


def breasts(b, parts, rng):
    interior = parts["interior"]
    lounge = tk.chimney_breast(b, interior, ix, -1.0, -3.6, -2.2, f1, c2, 0.62, 0.66, rng, depth=0.38)
    tk.fireplace_light(b, interior, V(lounge, -2.9, f1), V(-1.0, 0.0, 0.0), rng, 1.25, "painted_wood_white", "kitchen_tiles", False)
    bedroom = tk.chimney_breast(b, interior, ix, -1.0, 1.9, 3.2, f1, c2, 0.56, 0.6, rng, depth=0.34)
    tk.fireplace_light(b, interior, V(bedroom, 2.55, f1), V(-1.0, 0.0, 0.0), rng, 1.0, "timber_beam", "kitchen_tiles", False, False)
    return lounge, bedroom


def finishes(parts, rng, doors, breast_faces):
    lounge_door, kitchen_door, bed_door = doors
    lounge, bedroom = breast_faces
    interior = parts["interior"]
    plaster = ("plaster", 3)
    floral = ("paper", "wallpaper_faded", 2, 1)
    stripe = ("paper", "town_stripe", 2, 1)
    boarded = ("panel", 1.25, "painted_wood_green", ("plaster", 2))
    tiled = ("tiles", 1.3, "kitchen_tiles", ("plaster", 2))
    store_door_world = (1.95, 3.1, 0.0, 2.22)
    tk.room(parts, rng, -ix, ix, fy, partition[0], 0.0, c1, {"right": boarded}, {}, "painted_wood_green", None, True, 2, (), None, 14)
    tk.wall_finish(interior, "left", boarded, -ix, ix, fy, stair_top, 0.0, c1, [], rng)
    tk.skirting(interior, "left", -ix, ix, fy, stair_top, 0.0, [], "painted_wood_green")
    tk.wall_finish(interior, "back", boarded, stair_x[1], ix, fy, partition[0], 0.0, c1, [store_door_world], rng)
    tk.skirting(interior, "back", stair_x[1], ix, fy, partition[0], 0.0, [store_door_world], "painted_wood_green")
    tk.wall_finish(interior, "left", boarded, stair_x[1], ix, stair_top, partition[0], 0.0, c1, [], rng)
    tk.wall_finish(interior, "back", boarded, stair_x[0], stair_x[1], fy, stair_top, 0.0, c1, [(-3.0, -2.45, 0.0, 1.85)], rng)
    store_back = [(-back_door[1], -back_door[0], 0.0, back_door[3]), (-back_windows[0][1], -back_windows[0][0], back_windows[0][2], back_windows[0][3])]
    tk.room(parts, rng, stair_x[1], ix, partition[1], by, 0.0, c1, {"front": ("plaster", 4), "right": ("plaster", 5), "back": ("plaster", 5)}, {"front": [store_door_world], "back": store_back}, None, None, False, 0, (), None, 16)
    tk.wall_finish(interior, "left", ("plaster", 4), -ix, ix, stair_top, stair_foot, 0.0, c2, [], rng)
    tk.room(parts, rng, -ix, ix, fy, lounge_wall[0], f1, c2, {"front": floral, "left": floral, "right": floral, "back": floral}, {"front": list(upper_windows), "back": [lounge_door]}, "painted_wood_white", f1 + 2.15, True, 2, (), {"right": [(-3.6, -2.2, f1, c2)]}, 12)
    tk.wall_finish(interior, "right", floral, 0.0, lounge, -3.6, -2.2, f1, c2, [(-3.53, -2.27, f1, f1 + 1.2)], rng)
    tk.room(parts, rng, -ix, ix, lounge_wall[1], hall_wall[0], f1, c2, {"front": stripe, "left": stripe, "right": stripe}, {"front": [lounge_door]}, "painted_wood_white", None, True, 1, (), None, 4)
    tk.wall_finish(interior, "back", stripe, stair_x[1], ix, lounge_wall[1], hall_wall[0], f1, c2, [kitchen_door, bed_door], rng)
    tk.skirting(interior, "back", stair_x[1], ix, lounge_wall[1], hall_wall[0], f1, [kitchen_door, bed_door], "painted_wood_white")
    kitchen_back = [(-back_windows[1][1], -back_windows[1][0], back_windows[1][2], back_windows[1][3])]
    tk.room(parts, rng, -ix, split_x[0], hall_wall[1], by, f1, c2, {"back": tiled, "right": tiled}, {"back": kitchen_back}, "painted_wood_green", None, True, 2, (), None, 8)
    tk.wall_finish(interior, "front", tiled, stair_x[1], split_x[0], hall_wall[1], by, f1, c2, [kitchen_door], rng)
    tk.skirting(interior, "front", stair_x[1], split_x[0], hall_wall[1], by, f1, [kitchen_door], "painted_wood_green")
    tk.wall_finish(interior, "left", ("plaster", 2), -ix, split_x[0], well[3] + 0.03, by, f1, c2, [], rng)
    bed_back = [(-back_windows[2][1], -back_windows[2][0], back_windows[2][2], back_windows[2][3])]
    tk.room(parts, rng, split_x[1], ix, hall_wall[1], by, f1, c2, {"front": stripe, "back": stripe, "left": stripe, "right": stripe}, {"front": [bed_door], "back": bed_back}, "painted_wood_white", f1 + 2.15, True, 2, (), {"right": [(1.9, 3.2, f1, c2)]}, 10)
    tk.wall_finish(interior, "right", stripe, 0.0, bedroom, 1.9, 3.2, f1, c2, [(2.05, 3.05, f1, f1 + 1.2)], rng)


def shop_room(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.wall_shelves(b, furniture, clutter, V(ix - 0.01, -4.4, 0.0), V(ix - 0.01, 0.9, 0.0), V(-1.0, 0.0, 0.0), [0.12, 0.6, 1.05, 1.5, 1.95, 2.4], rng)
    tp.wall_shelves(b, furniture, clutter, V(-ix + 0.01, 0.0, 0.0), V(-ix + 0.01, -4.2, 0.0), V(1.0, 0.0, 0.0), [0.5, 0.95, 1.4, 1.85, 2.3], rng, ("can", "jar", "box", "bottle", "gap", "gap"))
    tp.shop_counter(b, furniture, clutter, 1.45, 2.0, -3.6, 0.0, rng)
    tp.till(clutter, V(1.72, -1.6, 0.92), -math.pi * 0.5, rng)
    tp.scales(clutter, V(1.72, -2.6, 0.92), -math.pi * 0.5, rng)
    tp.slicer(clutter, V(1.75, -0.63, 0.92), -math.pi * 0.5, rng)
    for index, y in enumerate((-3.4, -3.15, -2.95)):
        tp.tin_box(clutter, V(1.72, y, 0.92), rng.uniform(-0.2, 0.2), rng, ("cocoa", "beef", "peaches")[index])
    tp.glass_case(furniture, clutter, V(1.7, -0.2, 0.92), math.pi * 0.5, rng)
    b.loot("food", V(1.72, -2.1, 0.92))
    tp.tier_stand(b, furniture, clutter, V(-0.7, -2.0, 0.0), 0.0, rng)
    for x0, x1 in windows:
        x_a = x0 + 0.08 if x0 < 0 else x0 + 0.06
        x_b = x1 - 0.06 if x0 < 0 else x1 - 0.08
        block(furniture, "timber_planks_weathered", V(x_a, -4.82, 0.0), V(x_b, -4.28, 0.5), 0.0, "board")
        block(clutter, "fabric_worn", V(x_a, -4.82, 0.5), V(x_b, -4.28, 0.52), 0.0, "world")
        tk.col(b, "wood", "display", x_a, x_b, -4.82, -4.28, 0.0, 0.52)
        tp.stock_row(clutter, V(x_a + 0.05, -4.6, 0.52), V(1.0, 0.0, 0.0), x_b - x_a - 0.1, rng, ("can", "can", "jar", "box", "gap"), 0.4, 0.0)
        if x0 > 0:
            for level in range(3):
                for index in range(4 - level):
                    tp.label_can(clutter, V(2.0 + index * 0.09 + level * 0.045, -4.42, 0.52 + level * 0.11), rng, "peas", 0.04, 0.11)
    for index in range(7):
        tp.label_can(clutter, V(rng.uniform(-2.2, -0.9), rng.uniform(-4.2, -3.4), 0.0), rng, rng.choice(("peas", "beans", "soup")), lying=True)
    tk.chips(parts["debris"], "glass_dirty", -3.0, -0.8, -4.25, -3.4, 0.0, 14, rng, (0.02, 0.07), (0.003, 0.004))
    tk.chips(parts["debris"], "glass_dirty", -3.1, -0.7, -5.6, -5.05, -0.15, 10, rng, (0.02, 0.07), (0.003, 0.004))
    tp.sack_row(clutter, V(-2.75, -3.7, 0.0), V(0.0, 1.0, 0.0), 4, rng)
    tp.sack_row(clutter, V(-2.35, -3.5, 0.0), V(0.0, 1.0, 0.0), 2, rng)
    tk.col(b, "fabric", "sacks", -2.95, -2.1, -3.95, -2.3, 0.0, 0.5)
    bd.barrel(b, furniture, V(-2.65, -0.65, 0.0), rng, 0.28, 0.85, "timber_planks_weathered", "rusty_metal", False)
    tp.chair_light(furniture, V(0.4, -3.3, 0.0), 2.6, rng)
    tp.chair_light(furniture, V(0.9, -0.7, 0.0), 0.4, rng, fallen=True)
    tp.enamel_sign(interior, V(-ix + 0.02, -3.2, 2.95), V(1.0, 0.0, 0.0), 0.9, 0.34, "enamel_tea", rng, 0.03)
    tp.enamel_sign(interior, V(-ix + 0.02, -1.8, 2.95), V(1.0, 0.0, 0.0), 0.9, 0.34, "enamel_smoke", rng, -0.02)
    tp.enamel_sign(interior, V(-ix + 0.02, -0.6, 2.95), V(1.0, 0.0, 0.0), 0.9, 0.34, "enamel_soap", rng, 0.0)
    tp.wall_clock(interior, V(0.3, partition[0] - 0.015, 2.5), V(0.0, -1.0, 0.0), rng, 0.2)
    tp.wall_sheet(interior, V(-1.2, partition[0] - 0.012, 1.6), V(0.0, -1.0, 0.0), "police_notice", rng, 1.0, 0.02)
    tp.wall_sheet(interior, V(1.0, partition[0] - 0.012, 1.55), V(0.0, -1.0, 0.0), "calendar", rng, 1.0, -0.04)
    for x, y in ((-0.6, -2.6), (-0.6, -0.4), (2.3, -1.8)):
        tk.pendant(b, interior, V(x, y, c1), rng, "town_metal", 0.75)
    tp.papers(parts["debris"], -2.4, 1.2, -4.0, 0.6, 0.0, 8, rng, ("newspaper", "letter", "card", "envelope"))
    tp.bucket_light(clutter, V(-1.9, 0.5, 0.0), rng, "rusty_metal", True)
    bd.long_tool(clutter, V(-1.6, 0.85, 0.0), V(-1.55, 0.95, 1.45), "broom", rng)
    tp.debris_field(parts, -2.2, 1.2, -3.8, 0.7, 0.0, rng, 16, 0, 0, 6)


def store_room(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.wall_shelves(b, furniture, clutter, V(ix - 0.01, 1.35, 0.0), V(ix - 0.01, 3.3, 0.0), V(-1.0, 0.0, 0.0), [0.25, 0.8, 1.35, 1.9], rng, ("box", "box", "jar", "can", "gap"))
    crates = [(V(-1.55, 4.25, 0.0), (0.6, 0.45, 0.45), 0.1), (V(-1.5, 4.25, 0.45), (0.5, 0.4, 0.36), -0.15), (V(-0.85, 4.28, 0.0), (0.55, 0.45, 0.4), 0.05), (V(-0.3, 2.45, 0.0), (0.6, 0.5, 0.42), 0.4), (V(0.3, 2.4, 0.0), (0.5, 0.4, 0.35), -0.2)]
    for center, size3, yaw in crates:
        bd.crate(clutter, center, size3, yaw, rng)
    tk.col(b, "wood", "crates", -1.9, -0.55, 3.98, by, 0.0, 0.8)
    tk.col(b, "wood", "crates", -0.65, 0.6, 2.1, 2.75, 0.0, 0.42)
    b.loot("box", V(-0.3, 2.45, 0.42))
    tp.sack_row(clutter, V(-1.85, 1.45, 0.0), V(0.0, 1.0, 0.0), 2, rng)
    tp.sack_row(clutter, V(-1.45, 1.4, 0.0), V(0.0, 1.0, 0.0), 2, rng, "fabric_tartan")
    tk.col(b, "fabric", "sacks", -2.2, -1.15, 1.15, 2.1, 0.0, 0.45)
    bd.barrel(b, furniture, V(2.95, 4.25, 0.0), rng, 0.28, 0.85, "timber_planks_weathered", "rusty_metal", False)
    bd.barrel(b, furniture, V(-1.75, 2.75, 0.0), rng, 0.28, 0.85, "timber_planks_weathered", "rusty_metal", False)
    tp.table_light(furniture, 0.6, 1.6, 0.0, 1.2, 0.6, 0.85, rng, "timber_planks_weathered")
    tk.col(b, "wood", "table", 0.0, 1.2, 1.3, 1.9, 0.0, 0.85)
    tp.papers(clutter, 0.1, 1.1, 1.4, 1.8, 0.85, 3, rng, ("newspaper",))
    bd.rope_coil(clutter, V(0.9, 1.65, 0.85), rng, 0.12, 3, "hay")
    bd.coat_rail(interior, clutter, V(-1.0, partition[1], 1.65), V(-0.3, partition[1], 1.65), V(0.0, 1.0, 0.0), rng, 2)
    tp.sack_truck(furniture, V(-0.62, partition[1] + 0.31, 0.0), math.pi, rng)
    tk.col(b, "metal", "truck", -0.9, -0.34, partition[1], partition[1] + 0.42, 0.0, 1.3)
    tp.wall_sheet(interior, V(0.6, partition[1] + 0.012, 1.55), V(0.0, 1.0, 0.0), "calendar", rng, 1.0, 0.03)
    tp.wall_sheet(interior, V(0.95, partition[1] + 0.012, 1.45), V(0.0, 1.0, 0.0), "letter", rng, 1.0, -0.05)
    tk.pendant(b, interior, V(0.6, 2.6, f1 - 0.2), rng, "glass_dirty", 0.4)
    tk.chips(parts["debris"], "plaster_interior", -2.0, 3.0, 1.2, 4.5, 0.0, 14, rng)
    tp.papers(parts["debris"], -1.5, 2.5, 1.3, 3.5, 0.0, 4, rng, ("newspaper", "card"))


def lounge_room(b, parts, rng, lounge):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    hearth = V(lounge - 0.3, -2.9, f1)
    tp.mantel_set(clutter, V(lounge - 0.06, -3.4, f1 + 1.16), V(0.0, 1.0, 0.0), V(-1.0, 0.0, 0.0), 1.0, rng)
    tp.wall_mirror(interior, V(lounge - 0.006, -2.9, f1 + 1.75), V(-1.0, 0.0, 0.0), 0.9, 0.7, rng, "town_brass", True)
    tp.fender(clutter, V(lounge - 0.42, -3.45, f1 + 0.02), V(lounge - 0.42, -2.35, f1 + 0.02), rng)
    for position in (V(1.6, -3.9, f1), V(1.75, -1.7, f1)):
        tp.armchair_light(b, furniture, position, tk.facing(position, hearth), rng)
    tp.sofa_light(b, furniture, V(-0.2, -2.9, f1), math.pi * 0.5, rng, 1.6)
    bd.rug(clutter, V(1.2, -2.9, f1), 2.2, 1.7, 0.02, rng, "town_carpet")
    tp.table_light(furniture, -2.2, -2.6, f1, 1.1, 0.8, 0.74, rng)
    tk.col(b, "wood", "table", -2.75, -1.65, -3.0, -2.2, f1, f1 + 0.74)
    for position in (V(-2.2, -3.25, f1), V(-2.2, -1.9, f1), V(-1.4, -2.6, f1)):
        tp.chair_light(furniture, position, tk.facing(position, V(-2.2, -2.6, f1)), rng)
    tp.plate_light(clutter, V(-2.4, -2.5, f1 + 0.74), rng)
    tp.cup_light(clutter, V(-2.0, -2.75, f1 + 0.74), rng)
    tp.sheet(clutter, V(-2.1, -2.4, f1 + 0.745), 0.4, 0.36, 0.48, tp.pr("newspaper"), rng, 0.0)
    tp.sideboard(b, furniture, clutter, V(-0.9, lounge_wall[0] - 0.28, f1), 0.0, rng, 1.4)
    tp.wireless(clutter, V(-0.55, lounge_wall[0] - 0.3, f1 + 0.9), 0.0, rng)
    tp.vase(clutter, V(-1.2, lounge_wall[0] - 0.25, f1 + 0.9), rng)
    tp.bookcase(b, furniture, clutter, V(-ix + 0.16, -1.65, f1), math.pi * 0.5, rng, 0.85, 1.7, 0.3)
    tp.framed(interior, V(-1.0, lounge_wall[0] - 0.006, f1 + 1.8), V(0.0, -1.0, 0.0), 0.7, 0.5, tp.pr("harbour"), rng, "town_brass")
    tp.framed(interior, V(-ix + 0.006, -3.3, f1 + 1.7), V(1.0, 0.0, 0.0), 0.5, 0.36, tp.pr("ship"), rng, "timber_beam", 0.04)
    tp.framed(interior, V(ix - 0.006, -1.5, f1 + 1.6), V(-1.0, 0.0, 0.0), 0.3, 0.4, tp.pr("portrait_a"), rng, "timber_beam", -0.05)
    for w in upper_windows:
        tp.curtain_light(clutter, V(w[0] - 0.1, fy + 0.08, w[3] + 0.12), V(w[1] + 0.1, fy + 0.08, w[3] + 0.12), 1.6, rng, "fabric_tartan" if w[0] > 0 else "fabric_worn", 0.4)
    tk.pendant(b, interior, V(0.4, -2.9, c2), rng, "town_metal", 0.5)
    tp.papers(parts["debris"], -2.5, 2.0, -4.3, -1.4, f1, 5, rng)
    tp.debris_field(parts, -2.8, 2.6, -4.4, -1.3, f1, rng, 10, 8, 0, 6)


def flat_rooms(b, parts, rng, bedroom):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.gas_cooker(b, furniture, clutter, V(-2.75, by - 0.3, f1), 0.0, rng)
    bd.belfast_sink(b, furniture, clutter, V(-1.05, by - 0.27, f1), 0.0, rng)
    tp.table_light(furniture, -0.9, 2.3, f1, 0.9, 0.7, 0.76, rng)
    tk.col(b, "wood", "table", -1.35, -0.45, 1.95, 2.65, f1, f1 + 0.76)
    tp.chair_light(furniture, V(-0.9, 1.75, f1), math.pi + 0.2, rng)
    tp.chair_light(furniture, V(-1.6, 2.6, f1), 1.3, rng, fallen=True)
    tp.label_jar(clutter, V(-0.7, 2.4, f1 + 0.76), rng, "marmalade")
    tp.label_can(clutter, V(-1.05, 2.15, f1 + 0.76), rng, "milk")
    tp.plate_light(clutter, V(-1.0, 2.45, f1 + 0.76), rng)
    b.loot("food", V(-0.85, 2.3, f1 + 0.76))
    for z in (f1 + 1.4, f1 + 1.8):
        bd.shelf(interior, V(split_x[0], 1.6, z), V(split_x[0], 3.2, z), 0.22, V(-1.0, 0.0, 0.0), rng)
        y = 1.7
        while y < 3.1:
            if rng.random() < 0.5:
                tp.label_jar(clutter, V(split_x[0] - 0.11, y, z), rng, rng.choice(("jam", "pickles", "honey")))
            else:
                tp.label_can(clutter, V(split_x[0] - 0.11, y, z), rng, rng.choice(("peas", "soup", "cocoa")))
            y += rng.uniform(0.13, 0.22)
    bd.cabinet(furniture, V(0.2, 3.7, f1), 0.5, 0.5, 0.0, 1.9, -math.pi * 0.5, rng, "timber_planks_weathered", "painted_wood_green", 1, 0, 0)
    tk.col(b, "wood", "larder", -0.05, split_x[0], 3.45, 3.95, f1, f1 + 1.9)
    tp.wall_clock(interior, V(-1.8, hall_wall[1] + 0.015, f1 + 2.0), V(0.0, 1.0, 0.0), rng, 0.15)
    tk.pendant(b, interior, V(-1.1, 2.6, c2), rng, "town_metal", 0.5)
    tp.debris_field(parts, -2.2, 0.3, 2.5, 4.3, f1, rng, 8, 6, 2, 0)
    bd.iron_bed(b, furniture, clutter, V(1.6, 3.55, f1), 0.0, rng, 1.95, 1.3)
    bd.suitcase(clutter, V(1.8, 3.4, f1 + 0.62), 0.25, rng, True)
    tp.wardrobe_light(b, furniture, clutter, V(0.92, 1.0, f1), math.pi * 0.5, rng, 1.0, 0.56)
    tp.chest_light(b, furniture, V(2.8, 0.36, f1), math.pi, rng, 0.8, 0.44, 0.9, "timber_beam", 4)
    b.loot("box", V(2.8, 0.36, f1 + 0.95))
    tp.chair_light(furniture, V(2.2, 1.5, f1), 2.2, rng)
    bd.rug(clutter, V(1.9, 2.3, f1), 1.3, 1.0, 0.1, rng, "fabric_tartan")
    tp.mantel_set(clutter, V(bedroom - 0.05, 2.1, f1 + 1.16), V(0.0, 1.0, 0.0), V(-1.0, 0.0, 0.0), 0.9, rng, False)
    tp.framed(interior, V(split_x[1] + 0.006, 2.6, f1 + 1.6), V(1.0, 0.0, 0.0), 0.36, 0.46, tp.pr("portrait_b"), rng, "timber_beam", 0.05)
    tp.curtain_light(clutter, V(1.3, by - 0.08, f1 + 2.35), V(2.6, by - 0.08, f1 + 2.35), 1.4, rng, "fabric_worn", 0.4)
    tk.pendant(b, interior, V(1.9, 2.3, c2), rng, "glass_dirty", 0.45)
    tp.papers(parts["debris"], 0.8, 3.0, 0.4, 2.8, f1, 4, rng, ("letter", "envelope"))
    block(clutter, "town_carpet", V(-2.0, lounge_wall[1] + 0.12, f1 + 0.004), V(2.8, hall_wall[0] - 0.12, f1 + 0.012), 0.0, "world")
    tp.framed(interior, V(0.9, hall_wall[0] - 0.006, f1 + 1.6), V(0.0, -1.0, 0.0), 0.32, 0.24, tp.pr("seascape"), rng, "timber_beam", 0.05)
    tk.pendant(b, interior, V(-1.2, -0.5, c2), rng, "glass_dirty", 0.35)


def exterior(b, parts, gable, rng):
    roof = parts["roof"]
    clutter = parts["clutter"]
    plants = parts["plants"]
    gutter_z = gable.eave_top - 0.05 - 0.06
    tk.downpipe_light(roof, ix + 0.1, -gable.edge - 0.04, -hy, gutter_z - 0.03, 3.9, rng)
    tk.downpipe_light(roof, -ix - 0.1, gable.edge + 0.04, hy, gutter_z - 0.03, -0.15, rng, broken=1.1, lean=0.05)
    tk.terrace_roof(b, parts, -hx, hx, gable, rng, 0.3, 0.015, [(-1.6, -0.6, 1.6, 2.6, -1.0)], 0.03, True, "rock", True, None, True)
    tk.stack(b, roof, hx - 0.42, 0.0, 0.7, 1.2, gable.top(0.6) - 0.3, gable.ridge_top + 0.95, rng, 3)
    tk.ivy_light(plants, V(-2.2, hy + 0.02, -0.15), V(0.0, 1.0, 0.0), rng, 3.2, 0.8, 3, 16.0)
    bd.dustbin(clutter, V(1.0, hy + 0.4, -0.15), rng)
    bd.crate(clutter, V(-0.2, hy + 0.35, -0.15), (0.55, 0.45, 0.4), 0.3, rng, broken=True)
    tk.col(b, "wood", "crate", -0.5, 0.1, hy + 0.1, hy + 0.6, -0.15, 0.25)
    tk.weeds_line(plants, V(-ix + 0.3, hy + 0.12, -0.15), V(ix - 0.3, hy + 0.12, -0.15), rng, 5)
    tk.weeds_line(plants, V(-ix + 0.3, -hy - 0.1, -0.15), V(windows[0][1] - 0.1, -hy - 0.1, -0.15), rng, 3)
    tk.weeds_line(plants, V(windows[1][0] + 0.1, -hy - 0.1, -0.15), V(ix - 0.3, -hy - 0.1, -0.15), rng, 3)
    for index in range(6):
        kit.grass_tuft(plants, V(rng.uniform(-ix, ix), -gable.edge - 0.06, gutter_z + 0.02), rng, (0.06, 0.2), (3, 5), 0.03)
    tp.papers(parts["debris"], -2.6, 2.6, -5.7, -5.1, -0.15, 6, rng, ("newspaper", "notice", "card"))
    tk.chips(parts["debris"], "slate_roof", -2.5, 2.5, -5.6, -5.1, -0.15, 6, rng, (0.08, 0.17), (0.006, 0.008))


def shop():
    b = kit.Build("shop", 1201)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    shell_walls(b, parts, gable, rng)
    shopfront(b, parts, rng)
    openings(b, parts, rng)
    doors = interior_walls(b, parts, rng)
    breast_faces = breasts(b, parts, rng)
    finishes(parts, rng, doors, breast_faces)
    shop_room(b, parts, rng)
    store_room(b, parts, rng)
    lounge_room(b, parts, rng, breast_faces[0])
    flat_rooms(b, parts, rng, breast_faces[1])
    exterior(b, parts, gable, rng)
    return b


def shop_far():
    b = kit.Build("shop_far", 1202)
    shell = b.part("shell", 30.0)
    gable = gable_of()
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    wide_front = kit.facade("front", hx, hy)
    back = kit.facade("back", ix, hy)
    kit.wall(shell, stone, front, kit.rect(-ix, ix, head, wall_top), [], front_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [], back_t)
    for side in ("left", "right"):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.under(hy, 0.05)), (0.0, gable.under(0.0, 0.05)), (-hy, gable.under(-hy, 0.05))]
        kit.wall(shell, stone, kit.facade(side, hx, hy), outline, [], 0.25)
    kit.skin(shell, render, wide_front, kit.rect(-hx, hx, 3.88, wall_top - 0.02), [kit.rect(*w) for w in upper_windows], 0.02, 0.0, False)
    for w in upper_windows:
        kit.skin(shell, "glass_dirty", wide_front, kit.rect(*w), [], 0.004, 0.001, False)
    kit.skin(shell, "render_white", kit.facade("back", hx, hy), kit.rect(-hx, hx, 1.2, wall_top - 0.4), [kit.rect(*w) for w in back_windows] + [kit.rect(back_door[0], back_door[1], 1.21, back_door[3])], 0.018, 0.0, False)
    for w in back_windows + [back_door]:
        kit.skin(shell, "glass_dirty" if w[2] > 0.5 else "soot", kit.facade("back", hx, hy), kit.rect(*w), [], 0.004, 0.001, False)
    block(shell, "glass_dirty", V(-ix, -hy + 0.04, 0.7), V(ix, -hy + 0.08, head))
    block(shell, paint, V(-ix, -hy, 0.0), V(ix, -hy + 0.12, 0.7))
    block(shell, paint, V(-hx, -hy - 0.1, head), V(hx, -hy + 0.02, 3.85))
    tk.atlas_quad(shell, "town_signs", [kit.frame_point(front, -3.2, 3.11, 0.101), kit.frame_point(front, 3.2, 3.11, 0.101), kit.frame_point(front, 3.2, 3.69, 0.101), kit.frame_point(front, -3.2, 3.69, 0.101)], tp.sg("shop_fascia"))
    for edge in (-hx, hx - 0.28):
        block(shell, paint, V(edge, -hy - 0.08, 0.0), V(edge + 0.28, -hy, head))
    kit.roof_slab(shell, gable, -1.0, -hx, hx, "slate_roof", 0.2)
    kit.roof_slab(shell, gable, 1.0, -hx, hx, "roof_moss", 0.2)
    block(shell, "terracotta", V(-hx, -0.13, gable.ridge_top - 0.04), V(hx, 0.13, gable.ridge_top + 0.09))
    block(shell, dressed, V(hx - 0.77, -0.6, gable.top(0.6) - 0.3), V(hx - 0.07, 0.6, gable.ridge_top + 1.07))
    for dy in (-0.36, 0.0, 0.36):
        block(shell, "terracotta", V(hx - 0.5, dy - 0.09, gable.ridge_top + 1.07), V(hx - 0.34, dy + 0.09, gable.ridge_top + 1.45))
    return b
