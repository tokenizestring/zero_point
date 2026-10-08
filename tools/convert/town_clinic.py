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
hx = 5.0
hy = 6.0
wall_t = 0.4
ix = hx - wall_t
fy = -hy + wall_t
by = hy - wall_t
c1 = 3.0
render = "render_white"
stone = "granite_rubble"
dressed = "granite_ashlar"
trim = "town_paint_cream"
green = "painted_wood_green"
door = (-0.55, 0.55, 0.0, 2.7)
door_top = 2.2
windows = [(-3.75, -2.55, 0.85, 2.45), (2.55, 3.75, 0.85, 2.45)]
vent = (-0.32, 0.32, 4.55, 5.25)
left_windows = [(3.0, 4.3, 0.85, 2.45), (-0.8, 0.5, 0.85, 2.45), (-4.6, -3.4, 0.85, 2.45)]
right_windows = [(-4.3, -3.0, 0.85, 2.45), (-0.5, 0.8, 0.85, 2.45), (3.4, 4.6, 0.95, 2.35)]
back_door = (-0.5, 0.5, 0.0, 2.15)
back_windows = [(2.2, 3.4, 0.9, 2.3)]
partition = (-1.6, -1.48)
west = (-0.72, -0.6)
east = (0.6, 0.72)
reception_wall = (1.6, 1.72)
split = (2.3, 2.42)
corridor_door = (-0.55, 0.55, 0.0, 2.15)
reception_door = (-2.75, -1.75, 0.0, 2.15)
hatch = (-4.6, -3.4, 0.95, 1.85)
consult1_door = (-0.9, 0.15, 0.0, 2.15)
treatment_door = (3.0, 4.05, 0.0, 2.15)
consult2_door = (-0.9, 0.15, 0.0, 2.15)
pharmacy_door = (3.0, 4.05, 0.0, 2.15)
dispense = (4.4, 5.2, 0.95, 1.75)
breast_x = (-2.85, -1.45)
plinth_top = 0.42


def gable_of():
    return tk.YGable(-hy, hy, hx, 0.3, 3.45, 35.0, 0.0)


def flip(o):
    return (-o[1], -o[0], o[2], o[3])


def gable_skin(part, frame, gable, z_low, openings, rng, patches=4, name=render, thickness=0.02, depth=0.08):
    doors = sorted(o for o in openings if o[2] <= z_low + 0.05)
    holes = [kit.rect(*o) for o in openings if o[2] > z_low + 0.05]
    outline = [(-hx, z_low)]
    for d in doors:
        outline += [(d[0], z_low), (d[0], d[3]), (d[1], d[3]), (d[1], z_low)]
    outline += [(hx, z_low), (hx, gable.height(hx, depth)), (0.0, gable.height(0.0, depth)), (-hx, gable.height(-hx, depth))]
    blocked = holes + [kit.rect(d[0] - 0.08, d[1] + 0.08, z_low, d[3] + 0.08) for d in doors]
    blobs = tk.scatter_light((-hx + 0.1, hx - 0.1, z_low + 0.2, gable.height(hx, depth) - 0.1), blocked, patches, (0.12, 0.42), rng, (0.5, 1.3), None, 11)
    kit.skin(part, name, frame, outline, holes + blobs, thickness)


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    wall_top = gable.height(hx, 0.03)
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    front_open = [door] + windows + [vent]
    holes = [kit.rect(door[0], door[1], -0.05, door[3])] + [kit.rect(*w) for w in windows + [vent]]
    kit.wall(shell, stone, front, tk.gable_wall_y(gable, hx), holes, wall_t)
    kit.wall_boxes(b, "rock", "front", front, -hx, hx, -1.5, wall_top, wall_t, front_open)
    tk.gable_cols_y(b, "gable", -hy, -hy + wall_t, gable, wall_top)
    back_open = [back_door] + back_windows
    holes = [kit.rect(back_door[0], back_door[1], -0.05, back_door[3])] + [kit.rect(*w) for w in back_windows]
    kit.wall(shell, stone, back, tk.gable_wall_y(gable, hx), holes, wall_t)
    kit.wall_boxes(b, "rock", "back", back, -hx, hx, -1.5, wall_top, wall_t, back_open)
    tk.gable_cols_y(b, "gable", hy - wall_t, hy, gable, wall_top)
    for frame, openings_list, tag in ((left, left_windows, "left"), (right, right_windows, "right")):
        kit.wall(shell, stone, frame, kit.rect(-by, by, -1.5, wall_top), [kit.rect(*w) for w in openings_list], wall_t)
        kit.wall_boxes(b, "rock", tag, frame, -by, by, -1.5, wall_top, wall_t, openings_list)
    gable_skin(shell, front, gable, plinth_top, front_open, rng, 4)
    for a0, a1 in ((-hx, door[0] - 0.02), (door[1] + 0.02, hx)):
        frame_block(shell, "town_paint_black", front, a0, a1, -0.45, plinth_top, -0.025, 0.0)
    for corner, ua, ub in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0))):
        tk.quoins_light(shell, dressed, corner, ua, ub, -0.3, wall_top - 0.05, rng, 0.045)
    for frame in (front, back):
        for side in (-1.0, 1.0):
            a = side * hx
            frame_block(shell, dressed, frame, min(a, a - side * 0.5), max(a, a - side * 0.5), wall_top - 0.02, wall_top + 0.2, -0.06, 0.0)
    gable_skin(shell, back, gable, 1.2, [(o[0], o[1], max(o[2], 1.2), o[3]) for o in back_open], rng, 5)
    bd.damp_band(shell, back, -hx, hx, rng, 0.35, 1.0, "granite_rubble_damp", -0.2, 0.003, [(back_door[0] - 0.05, back_door[1] + 0.05)])
    for side in ("left", "right"):
        bd.damp_band(shell, kit.facade(side, hx, hy), -hy, hy, rng, 0.3, 0.9, "granite_rubble_damp", -0.2, 0.003)
    return wall_top


def frontage(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    roof = parts["roof"]
    front = kit.facade("front", hx, hy)
    a0, a1, z0, z1 = door
    for edge, sign in ((a0, -1.0), (a1, 1.0)):
        lo, hi = sorted((edge, edge + sign * 0.16))
        frame_block(shell, dressed, front, lo, hi, -0.4, z1 + 0.05, -0.05, 0.0)
    frame_block(shell, dressed, front, a0 - 0.2, a1 + 0.2, z1 + 0.05, z1 + 0.3, -0.06, 0.0)
    tk.door_unit(joinery, front, a0, a1, 0.0, door_top, wall_t, green, rng, "low", 100.0, "panel", True, 0.0, 0.06, 0.0, trim)
    frame_block(joinery, trim, front, a0, a1, door_top, door_top + 0.06, 0.05, 0.15, 0.0, "board")
    matrix = kit.frame_matrix(front)
    for index in range(2):
        p0 = a0 + 0.06 + (a1 - a0 - 0.12) * index / 2
        p1 = a0 + 0.06 + (a1 - a0 - 0.12) * (index + 1) / 2
        kit.pane(joinery, matrix, p0 + 0.01, p1 - 0.01, door_top + 0.06, z1 - 0.04, 0.1, rng.choice(("whole", "shard")), rng)
    frame_block(joinery, trim, front, -0.012, 0.012, door_top + 0.06, z1, 0.06, 0.14)
    frame_block(joinery, trim, front, a0, a1, z1 - 0.04, z1, 0.05, 0.15, 0.0, "board")
    tk.opening_block(b, "glass", "fanlight", front, (a0, a1, door_top, z1), wall_t)
    frame_block(joinery, "timber_beam", front, -0.95, 0.95, 2.86, 2.98, -0.72, 0.0)
    frame_block(roof, "rusty_metal", front, -1.0, 1.0, 2.98, 3.01, -0.76, 0.0)
    for a in (-0.82, 0.82):
        kit.prism(joinery, "timber_beam", kit.frame_matrix(front) @ kit.Matrix.Translation(V(a, 0.0, 0.0)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Z'), [(0.0, 2.86), (-0.62, 2.86), (0.0, 2.3)], -0.04, 0.04)
    tk.col(b, "wood", "canopy", -1.0, 1.0, -hy - 0.76, -hy, 2.86, 3.01)
    frame_block(joinery, "town_paint_navy", front, -0.95, 0.95, 3.25, 3.72, -0.05, 0.0, 0.0, "board")
    tk.atlas_panel(joinery, "town_signs", kit.frame_point(front, 0.0, 3.485, 0.052), V(0.0, -1.0, 0.0), 1.8, 0.45, tp.sg("clinic_board"), 0.0, 0.0)
    local_block(joinery, "town_brass", matrix, a1 + 0.22, a1 + 0.52, -0.012, 0.0, 1.42, 1.62)
    tk.atlas_panel(joinery, "town_signs", kit.frame_point(front, a1 + 0.37, 1.52, 0.0125), V(0.0, -1.0, 0.0), 0.29, 0.19, tp.sg("clinic_plate"), 0.0, 0.0)
    emit(joinery, kit.geo_lathe([(0.0, 0.0), (0.035, 0.0), (0.03, 0.02), (0.012, 0.03), (0.0, 0.032)], 8), "town_brass", kit.frame_matrix(front) @ kit.Matrix.Translation(V(a0 - 0.32, 0.0, 1.3)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)
    block(shell, dressed, V(a0 - 0.2, -hy - 0.4, -0.45), V(a1 + 0.2, -hy + 0.02, -0.05), 0.015)
    tk.col(b, "rock", "step", a0 - 0.2, a1 + 0.2, -hy - 0.4, -hy, -1.5, -0.05)
    tk.col(b, "rock", "threshold", a0, a1, -hy, fy, -1.5, 0.0)
    block(shell, dressed, V(a0, -hy, -0.08), V(a1, fy + 0.04, 0.0), 0.004)
    a0, a1, z0, z1 = vent
    for index in range(5):
        center = kit.frame_point(front, 0.0, z0 + 0.1 + index * 0.13, -wall_t * 0.5)
        slope = (front[3] * 0.6 - up).normalized()
        emit(joinery, kit.geo_box(a1 - a0 + 0.02, 0.2, 0.02), "timber_planks_weathered", kit.place(center, front[1], slope.cross(front[1]).normalized()), "board")
    kit.sill_stone(shell, dressed, front, a0, a1, z0, 0.2, 0.05, 0.07, 0.05)
    kit.lintel_stone(shell, dressed, front, a0, a1, z1, 0.2, 0.25, 0.02, 0.08)
    tk.opening_block(b, "wood", "vent", front, vent, wall_t)


def openings(b, parts, rng):
    joinery = parts["joinery"]
    shell = parts["shell"]
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    for w, lift, whole, boarded in zip(windows, (0.0, 0.25), (0.4, 0.2), (False, True)):
        tk.sash(b, parts, front, w, wall_t, rng, trim, 0.12, lift, whole, 0.3, 2, 1, render, dressed, None, False, boarded)
        tk.architrave(shell, front, w, render, 0.1, 0.025, 0.14, False)
    for frame, w, lift, whole, climb, boarded in ((left, left_windows[0], 0.0, 0.3, False, False), (left, left_windows[1], 0.2, 0.25, False, False), (left, left_windows[2], 0.0, 0.0, True, False), (right, right_windows[0], 0.0, 0.3, False, True), (right, right_windows[1], 0.0, 0.35, False, False), (back, back_windows[0], 0.1, 0.25, False, False)):
        tk.sash(b, parts, frame, w, wall_t, rng, trim, 0.12, lift, whole, 0.35, 2, 1, None, dressed, None, climb, boarded, "glass", "window", dressed, None)
    tk.casement(b, parts, right, right_windows[2], wall_t, rng, trim, 0.1, [0.0], 0.3, 0.3, 2, dressed)
    tp.window_bars(joinery, right, right_windows[2], 0.05)
    a0, a1, z0, z1 = back_door
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, green, rng, "high", 94.0, "ledged", True, 0.0, 0.06, 3.0, trim)
    block(shell, dressed, V(-a1 - 0.1, hy - 0.04, -0.35), V(-a0 + 0.1, hy + 0.36, -0.06), 0.012)
    tk.col(b, "rock", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
    tk.col(b, "rock", "step", -a1 - 0.1, -a0 + 0.1, hy, hy + 0.36, -0.6, -0.06)


def floors(b, parts, rng):
    floor = parts["floors"]
    tk.board_floor(floor, -ix, ix, fy, partition[1], 0.0, rng, "x", (), "floorboards", 0.03, 0.0, (0.15, 0.2), (0.5,))
    tk.tile_floor(floor, "town_lino", -ix, ix, partition[1], split[0], 0.0, 0.03)
    tk.tile_floor(floor, "town_lino", west[0], ix, split[0], by, 0.0, 0.03)
    tk.tile_floor(floor, "town_tiles", -ix, west[0], split[0], by, 0.0, 0.03)
    tk.col(b, "wood", "ground", -ix, ix, fy, partition[1], -0.3, 0.0)
    tk.col(b, "concrete", "ground", -ix, ix, partition[1], by, -0.3, 0.0)
    tk.col(b, "wood", "attic", -ix, ix, fy, by, c1, c1 + 0.2)


def breast_y(b, part, y_wall, inward, x0, x1, z0, z1, width, height, rng, depth=0.4, name="plaster_interior"):
    y_face = y_wall + inward * depth
    ya = min(y_wall, y_face)
    yb = max(y_wall, y_face)
    middle = (x0 + x1) * 0.5
    half = width * 0.5
    block(part, name, V(x0, ya, z0), V(middle - half, yb, z1), 0.0, "world")
    block(part, name, V(middle + half, ya, z0), V(x1, yb, z1), 0.0, "world")
    block(part, name, V(middle - half, ya, z0 + height), V(middle + half, yb, z1), 0.0, "world")
    back = y_wall + inward * 0.06
    block(part, "soot", V(middle - half, min(back, y_wall), z0), V(middle + half, max(back, y_wall), z0 + height), 0.0, "world")
    block(part, "soot", V(middle - half - 0.01, ya, z0), V(middle - half, yb, z0 + height), 0.0, "world")
    block(part, "soot", V(middle + half, ya, z0), V(middle + half + 0.01, yb, z0 + height), 0.0, "world")
    tk.col(b, "rock", "breast", x0, x1, ya, yb, z0, z1)
    return y_face


def interior_walls(b, parts, rng):
    joinery = parts["joinery"]
    interior = parts["interior"]
    front_plane = tk.partition(b, parts, V(0.0, partition[0], 0.0), V(0.0, -1.0, 0.0), -ix, ix, 0.0, c1, partition[1] - partition[0], [corridor_door], "partition")
    tk.door_unit(joinery, front_plane, corridor_door[0], corridor_door[1], 0.0, 2.15, 0.12, green, rng, "low", -95.0, "panel")
    frame = kit.plane(V(reception_wall[1], 0.0, 0.0), V(1.0, 0.0, 0.0))
    kit.wall(interior, "plaster_interior", frame, kit.notched(fy, partition[0], 0.0, c1, [(reception_door[0], reception_door[1], reception_door[3])]), [kit.rect(*hatch)], reception_wall[1] - reception_wall[0])
    kit.wall_boxes(b, "wood", "reception", frame, fy, partition[0], 0.0, c1, reception_wall[1] - reception_wall[0], [reception_door, hatch])
    tk.door_unit(joinery, frame, reception_door[0], reception_door[1], 0.0, 2.15, 0.12, green, rng, "high", -96.0, "panel")
    frame_block(joinery, "timber_beam", frame, hatch[0] - 0.06, hatch[1] + 0.06, hatch[2] - 0.04, hatch[2], -0.22, 0.34, 0.0, "board")
    for a in (hatch[0], hatch[1] - 0.05):
        frame_block(joinery, green, frame, a, a + 0.05, hatch[2], hatch[3], -0.02, 0.14, 0.0, "board")
    frame_block(joinery, green, frame, hatch[0], hatch[1], hatch[3] - 0.05, hatch[3], -0.02, 0.14, 0.0, "board")
    pane = kit.frame_matrix(frame) @ kit.Matrix.Translation(V(hatch[0] + 0.05, 0.06, 0.0)) @ kit.Matrix.Rotation(-1.2, 4, 'Z')
    local_block(joinery, green, pane, 0.0, 0.55, -0.02, 0.0, hatch[2] + 0.01, hatch[3] - 0.06)
    kit.pane(joinery, pane, 0.05, 0.5, hatch[2] + 0.06, hatch[3] - 0.11, -0.012, "shard", rng)
    west_plane = tk.partition(b, parts, V(west[1], 0.0, 0.0), V(1.0, 0.0, 0.0), partition[1], by, 0.0, c1, west[1] - west[0], [consult1_door, treatment_door], "corridor")
    tk.door_unit(joinery, west_plane, consult1_door[0], consult1_door[1], 0.0, 2.15, 0.12, trim, rng, "high", 94.0, "panel")
    tk.door_unit(joinery, west_plane, treatment_door[0], treatment_door[1], 0.0, 2.15, 0.12, trim, rng, "low", 98.0, "panel")
    frame = kit.plane(V(east[1], 0.0, 0.0), V(1.0, 0.0, 0.0))
    notches = sorted((d[0], d[1], d[3]) for d in (consult2_door, pharmacy_door))
    kit.wall(interior, "plaster_interior", frame, kit.notched(partition[1], by, 0.0, c1, notches), [kit.rect(*dispense)], east[1] - east[0])
    kit.wall_boxes(b, "wood", "corridor", frame, partition[1], by, 0.0, c1, east[1] - east[0], [consult2_door, pharmacy_door, dispense])
    tk.door_unit(joinery, frame, consult2_door[0], consult2_door[1], 0.0, 2.15, 0.12, trim, rng, "high", -92.0, "panel")
    tk.door_unit(joinery, frame, pharmacy_door[0], pharmacy_door[1], 0.0, 2.15, 0.12, trim, rng, "low", -97.0, "panel")
    frame_block(joinery, "timber_beam", frame, dispense[0] - 0.05, dispense[1] + 0.05, dispense[2] - 0.04, dispense[2], -0.2, 0.3, 0.0, "board")
    frame_block(joinery, trim, frame, dispense[0], dispense[1], dispense[3] - 0.05, dispense[3], -0.02, 0.14, 0.0, "board")
    tk.partition(b, parts, V(0.0, split[0], 0.0), V(0.0, -1.0, 0.0), -ix, west[0], 0.0, c1, split[1] - split[0], [], "split")
    tk.partition(b, parts, V(0.0, split[0], 0.0), V(0.0, -1.0, 0.0), east[1], ix, 0.0, c1, split[1] - split[0], [], "split")
    face = breast_y(b, interior, partition[0], -1.0, breast_x[0], breast_x[1], 0.0, c1, 0.66, 0.7, rng)
    tk.fireplace_light(b, interior, V((breast_x[0] + breast_x[1]) * 0.5, face, 0.0), V(0.0, -1.0, 0.0), rng, 1.2, "timber_beam", "kitchen_tiles", False)
    return face


def finishes(parts, rng, face):
    interior = parts["interior"]
    dado = ("panel", 1.1, green, ("plaster", 1))
    plaster = ("plaster", 1)
    clean = ("plaster", 0)
    floral = ("paper", "wallpaper_faded", 1, 1)
    tiled = ("tiles", 1.2, "kitchen_tiles", clean)
    wash = ("tiles", 1.5, "kitchen_tiles", clean)
    tk.room(parts, rng, -ix, reception_wall[0], fy, partition[0], 0.0, c1, {"front": dado, "left": dado, "right": dado, "back": dado}, {"front": [door, windows[0]], "left": [flip(left_windows[0])], "right": [reception_door, hatch], "back": [corridor_door]}, "timber_beam", 2.3, True, 1, (), {"back": [(breast_x[0], breast_x[1], 0.0, c1)]}, 4, 0.0)
    middle = (breast_x[0] + breast_x[1]) * 0.5
    tk.wall_finish(interior, "front", ("panel", 1.1, green, clean), breast_x[0], breast_x[1], face, 0.0, 0.0, c1, [(middle - 0.6, middle + 0.6, 0.0, 1.18)], rng)
    tk.room(parts, rng, reception_wall[1], ix, fy, partition[0], 0.0, c1, {"front": plaster, "left": plaster, "right": plaster, "back": plaster}, {"front": [windows[1]], "left": [reception_door, hatch], "right": [right_windows[0]]}, "timber_beam", None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, west[1], east[0], partition[1], by, 0.0, c1, {"front": tiled, "left": tiled, "right": tiled, "back": tiled}, {"front": [corridor_door], "left": [consult1_door, treatment_door], "right": [consult2_door, pharmacy_door, dispense], "back": [flip(back_door)]}, "timber_beam", None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, -ix, west[0], partition[1], split[0], 0.0, c1, {"front": floral, "left": floral, "right": floral, "back": floral}, {"left": [flip(left_windows[1])], "right": [consult1_door]}, "timber_beam", 2.3, True, 1, (), None, 2, 0.0)
    tk.room(parts, rng, east[1], ix, partition[1], split[0], 0.0, c1, {"front": plaster, "left": plaster, "right": plaster, "back": plaster}, {"right": [right_windows[1]], "left": [consult2_door]}, "timber_beam", 2.3, True, 1, (), None, 2, 0.0)
    tk.room(parts, rng, -ix, west[0], split[1], by, 0.0, c1, {"front": wash, "left": wash, "right": wash, "back": wash}, {"left": [flip(left_windows[2])], "right": [treatment_door], "back": [flip(back_windows[0])]}, None, None, True, 0, (), None, 2, 0.0)
    tk.room(parts, rng, east[1], ix, split[1], by, 0.0, c1, {"front": clean, "left": clean, "right": clean, "back": clean}, {"left": [pharmacy_door, dispense], "right": [right_windows[2]]}, "timber_beam", None, True, 0, (), None, 2, 0.0)


def waiting_room(b, parts, rng, face):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    middle = (breast_x[0] + breast_x[1]) * 0.5
    tp.mantel_set(clutter, V(middle - 0.5, face - 0.06, 1.16), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0), 1.0, rng, False)
    tp.wall_mirror(interior, V(middle, face - 0.005, 1.75), V(0.0, -1.0, 0.0), 0.85, 0.65, rng, "town_brass", True)
    tp.fender(clutter, V(middle - 0.55, face - 0.42, 0.02), V(middle + 0.55, face - 0.42, 0.02), rng)
    for k in range(4):
        position = V(-ix + 0.32, -4.95 + k * 0.58, 0.0)
        if k == 2:
            tp.chair_light(furniture, position + V(0.3, 0.0, 0.0), 1.9, rng, fallen=True)
            continue
        tp.chair_light(furniture, position, tk.facing(position, position + V(1.0, 0.0, 0.0)) + rng.uniform(-0.15, 0.15), rng)
    for x in (-3.65, -3.15):
        position = V(x, partition[0] - 0.32, 0.0)
        tp.chair_light(furniture, position, tk.facing(position, position - V(0.0, 1.0, 0.0)) + rng.uniform(-0.15, 0.15), rng)
    tp.bench_light(b, furniture, V(-3.15, fy + 0.25, 0.0), 0.0, rng, 1.3)
    tp.table_light(furniture, -2.1, -3.7, 0.0, 0.9, 0.6, 0.72, rng)
    tk.col(b, "wood", "table", -2.55, -1.65, -4.0, -3.4, 0.0, 0.72)
    tp.papers(clutter, -2.45, -1.75, -3.95, -3.45, 0.72, 4, rng, ("newspaper", "notice", "card"))
    tp.vase(clutter, V(-1.85, -3.55, 0.72), rng)
    tp.hall_stand(b, furniture, clutter, V(1.05, fy + 0.08, 0.0), math.pi, rng)
    tp.wall_sheet(interior, V(reception_wall[0] - 0.006, -3.0, 1.4), V(-1.0, 0.0, 0.0), "notice", rng, 1.0, 0.02)
    tp.desk_bell(clutter, V(reception_wall[0] - 0.12, -4.25, hatch[2]), rng)
    tp.wall_sheet(interior, V(-0.95, partition[0] - 0.006, 1.6), V(0.0, -1.0, 0.0), "poster", rng, 1.0, 0.03)
    tp.wall_sheet(interior, V(1.05, partition[0] - 0.006, 1.7), V(0.0, -1.0, 0.0), "police_notice", rng, 1.0, -0.02)
    tp.framed(interior, V(-ix + 0.006, -2.2, 1.75), V(1.0, 0.0, 0.0), 0.5, 0.36, tp.pr("seascape"), rng, "timber_beam", 0.03)
    tp.framed(interior, V(-1.2, fy + 0.006, 1.8), V(0.0, 1.0, 0.0), 0.32, 0.42, tp.pr("portrait_b"), rng, "town_brass", -0.03)
    tp.wall_clock(interior, V(-ix + 0.015, -5.0, 2.2), V(1.0, 0.0, 0.0), rng, 0.17)
    tp.plant_stand(clutter, V(-4.2, -2.05, 0.0), rng)
    tp.curtain_light(clutter, V(windows[0][0] - 0.1, fy + 0.08, windows[0][3] + 0.12), V(windows[0][1] + 0.1, fy + 0.08, windows[0][3] + 0.12), 1.6, rng, "fabric_worn", 0.4)
    tk.pendant(b, interior, V(-2.1, -3.7, c1), rng, "town_metal", 0.6, "warm", 8)
    tp.papers(parts["debris"], -3.8, 1.0, -5.3, -2.2, 0.0, 6, rng, ("newspaper", "notice", "letter", "envelope", "card"))
    tp.debris_field(parts, -4.2, 1.2, -5.4, -2.3, 0.0, rng, 6, 4, 0, 10)


def reception(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.desk_light(b, furniture, clutter, V(reception_wall[1] + 0.36, -4.0, 0.0), math.pi * 0.5, rng, 1.3, 0.7, 0.76, "timber_beam", "floorboards", ("papers", "phone"))
    tp.chair_light(furniture, V(2.85, -4.0, 0.0), tk.facing(V(2.85, -4.0, 0.0), V(1.8, -4.0, 0.0)), rng)
    for x, drawers in ((3.4, 4), (3.92, 3)):
        tp.filing_cabinet(b, furniture, V(x, partition[0] - 0.35, 0.0), 0.0, rng, drawers, "cream", 1.32 if drawers == 4 else 1.05)
    tp.ledger(clutter, V(3.92, partition[0] - 0.36, 1.05), 0.3, rng, False)
    tp.pigeonholes(interior, clutter, V(3.66, partition[0] - 0.002, 2.08), V(0.0, -1.0, 0.0), 4, 2, rng)
    bd.shelf(interior, V(ix, -5.4, 1.75), V(ix, -4.45, 1.75), 0.24, V(-1.0, 0.0, 0.0), rng)
    tp.book_row(clutter, V(ix - 0.03, -5.35, 1.75), V(0.0, 1.0, 0.0), 0.8, rng, (0.16, 0.2), (0.24, 0.3), True, 0.1)
    tp.wall_sheet(interior, V(ix - 0.006, -2.3, 1.5), V(-1.0, 0.0, 0.0), "calendar", rng, 1.0, 0.03)
    tp.wall_clock(interior, V(reception_wall[1] + 0.015, -3.1, 2.3), V(1.0, 0.0, 0.0), rng, 0.15)
    b.loot("box", V(3.85, -4.85, 0.0))
    tk.pendant(b, interior, V(3.1, -3.6, c1), rng, "glass_dirty", 0.5, "warm", 8)
    tp.papers(parts["debris"], 2.0, 4.3, -5.3, -2.0, 0.0, 7, rng, ("letter", "envelope", "notice", "card"))


def consulting_rooms(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.examination_couch(b, furniture, V(-3.35, split[0] - 0.36, 0.0), 0.0, rng)
    b.loot("medical", V(-2.95, split[0] - 0.36, 0.72))
    tp.folding_screen(furniture, V(-2.3, 2.25, 0.0), -1.2, rng)
    tp.desk_light(b, furniture, clutter, V(-3.2, partition[1] + 0.38, 0.0), math.pi, rng, 1.3, 0.7, 0.76, "timber_beam", "floorboards", ("papers", "lamp", "files"))
    tp.chair_light(furniture, V(-3.2, -0.35, 0.0), tk.facing(V(-3.2, -0.35, 0.0), V(-3.2, -1.2, 0.0)), rng, "timber_beam", "leather_brown")
    tp.chair_light(furniture, V(-2.25, -0.75, 0.0), tk.facing(V(-2.25, -0.75, 0.0), V(-3.2, -0.6, 0.0)), rng)
    tp.basin(b, furniture, V(-ix + 0.24, -1.0, 0.0), math.pi * 0.5, rng, 8)
    tp.wall_mirror(interior, V(-ix + 0.006, -1.0, 1.55), V(1.0, 0.0, 0.0), 0.36, 0.48, rng)
    tp.medicine_cabinet(b, furniture, clutter, V(west[0] - 0.19, 1.2, 0.0), -math.pi * 0.5, rng)
    tp.column_scale(b, furniture, V(-1.3, -1.12, 0.0), math.pi * 0.5, rng)
    tp.framed(interior, V(west[0] - 0.006, 2.0, 1.7), V(-1.0, 0.0, 0.0), 0.26, 0.36, tp.pr("notice"), rng, "timber_beam", 0.0)
    tp.framed(interior, V(-3.4, partition[1] + 0.006, 1.75), V(0.0, 1.0, 0.0), 0.5, 0.4, tp.pr("portrait_a"), rng, "town_brass", 0.02)
    tp.curtain_light(clutter, V(-ix + 0.08, 0.9, 2.57), V(-ix + 0.08, -0.6, 2.57), 1.5, rng, "fabric_worn", 0.4)
    tk.pendant(b, interior, V(-2.7, 0.4, c1), rng, "town_metal", 0.55, "warm", 8)
    tp.papers(parts["debris"], -4.2, -1.2, -1.2, 1.4, 0.0, 6, rng, ("letter", "notice", "envelope"))
    tp.debris_field(parts, -4.2, -1.2, -1.2, 1.9, 0.0, rng, 6, 3, 0, 0)
    tp.examination_couch(b, furniture, V(2.95, split[0] - 0.36, 0.0), 0.0, rng, 1.85, 0.62, 0.72, "leather_brown", "timber_beam", 0.25)
    tp.folding_screen(furniture, V(1.32, 0.15, 0.0), 1.2, rng, 3)
    tp.desk_light(b, furniture, clutter, V(3.0, partition[1] + 0.38, 0.0), math.pi, rng, 1.3, 0.7, 0.76, "timber_beam", "floorboards", ("papers", "phone"))
    tp.chair_light(furniture, V(3.0, -0.3, 0.0), 2.6, rng, "timber_beam", "leather_brown", True)
    tp.basin(b, furniture, V(ix - 0.24, -1.0, 0.0), -math.pi * 0.5, rng, 8)
    tp.drawer_bank(b, furniture, V(east[1] + 0.24, 1.25, 0.0), math.pi * 0.5, rng, 3, 4, 0.9, 0.45, 1.0)
    tp.painted_box(clutter, "cream", kit.turned(V(1.0, 1.45, 1.035), 0.2), -0.18, 0.18, -0.11, 0.11, 0.0, 0.18)
    tp.cup_light(clutter, V(0.98, 0.95, 1.035), rng)
    tp.medicine_bottle(clutter, V(1.05, 1.05, 1.035), rng)
    tp.gas_cylinder(clutter, V(ix - 0.22, 1.85, 0.0), rng, 1.25, 0.1, "town_metal", "green")
    tp.framed(interior, V(ix - 0.006, 1.2, 1.7), V(-1.0, 0.0, 0.0), 0.32, 0.42, tp.pr("calendar"), rng, "timber_beam", 0.03)
    tp.curtain_light(clutter, V(ix - 0.08, -0.6, 2.57), V(ix - 0.08, 0.9, 2.57), 1.5, rng, "fabric_tartan", 0.4)
    tk.pendant(b, interior, V(2.6, 0.4, c1), rng, "town_metal", 0.55, "warm", 8)
    tp.papers(parts["debris"], 1.2, 4.2, -1.2, 1.4, 0.0, 5, rng, ("letter", "notice", "card"))
    tp.debris_field(parts, 1.2, 4.2, -1.2, 1.9, 0.0, rng, 6, 0, 0, 0)


def back_rooms(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.stretcher(b, furniture, V(-3.05, 3.3, 0.0), 0.04, rng, True)
    lump(clutter, "fabric_worn", V(-2.6, 3.32, 0.68), (0.32, 0.22, 0.05), rng, 0.3, 1)
    tp.stretcher(b, furniture, V(-3.0, 5.1, 0.0), 0.08, rng, False)
    tp.medicine_cabinet(b, furniture, clutter, V(-1.3, split[1] + 0.19, 0.0), math.pi, rng, 0.9, 0.36, 1.85, "painted_wood_white", 2.1, 0.5)
    tp.gas_cylinder(clutter, V(-ix + 0.2, by - 0.25, 0.0), rng, 1.3, 0.11, "town_metal", "blue")
    tp.gas_cylinder(clutter, V(-ix + 0.48, by - 0.2, 0.0), rng, 1.3, 0.11, "town_metal", "cream", True)
    tk.col(b, "metal", "cylinders", -ix, -ix + 0.4, by - 0.45, by, 0.0, 1.35)
    tp.table_light(furniture, -1.55, 4.75, 0.0, 0.7, 0.5, 0.82, rng, "floorboards", "rusty_metal")
    tk.col(b, "metal", "trolley", -1.9, -1.2, 4.5, 5.0, 0.0, 0.82)
    for k in range(3):
        tp.medicine_bottle(clutter, V(-1.75 + k * 0.12, 4.68, 0.82), rng)
    emit(clutter, bd.plain(kit.geo_lathe([(0.0, 0.0), (0.12, 0.0), (0.16, 0.05), (0.15, 0.06), (0.0, 0.012)], 10)), "ceramic", kit.Matrix.Translation(V(-1.4, 4.85, 0.82)), "texture", True)
    b.loot("medical", V(-3.6, 4.25, 0.0))
    tp.bucket_light(clutter, V(-3.9, 2.75, 0.0), rng, "rusty_metal", True)
    bd.long_tool(clutter, V(-ix + 0.12, 2.7, 0.0), V(-ix + 0.05, 2.75, 1.4), "broom", rng)
    tp.bulb(b, interior, V(-2.7, 4.0, c1), rng, 0.45, "cold")
    tk.chips(parts["debris"], "kitchen_tiles", -4.2, -1.2, 2.6, 5.3, 0.0, 6, rng, (0.03, 0.07), (0.006, 0.008))
    tp.papers(parts["debris"], -4.0, -1.3, 2.7, 5.2, 0.0, 3, rng, ("letter", "notice"))
    tp.wall_shelves(b, furniture, clutter, V(1.0, by - 0.01, 0.0), V(4.45, by - 0.01, 0.0), V(0.0, -1.0, 0.0), [0.45, 0.95, 1.45, 1.95], rng, ("gap",), 0.3)
    for z in (0.45, 0.95, 1.45):
        x = 1.12
        while x < 4.35:
            if rng.random() < 0.7:
                tp.medicine_bottle(clutter, V(x, by - 0.15 + rng.uniform(-0.04, 0.04), z), rng)
            x += rng.uniform(0.1, 0.2)
    tp.drawer_bank(b, furniture, V(ix - 0.24, 2.95, 0.0), -math.pi * 0.5, rng, 2, 5, 0.9, 0.45, 1.0)
    tp.drawer_bank(b, furniture, V(2.55, split[1] + 0.24, 0.0), math.pi, rng, 5, 3, 2.0, 0.45, 0.92)
    tp.scales(clutter, V(2.0, split[1] + 0.26, 0.955), 0.0, rng)
    tp.mortar(clutter, V(2.55, split[1] + 0.22, 0.955), rng)
    tp.papers(clutter, 1.7, 2.4, split[1] + 0.12, split[1] + 0.38, 0.955, 2, rng, ("letter",))
    b.loot("medical", V(3.15, 4.55, 0.0))
    b.loot("medical", V(3.2, split[1] + 0.24, 0.955))
    tp.label_bottle(clutter, V(1.6, 4.9, 0.0), rng, "gin", True, True)
    tp.bulb(b, interior, V(2.6, 3.9, c1), rng, 0.45, "warm")
    tk.chips(parts["debris"], "glass_dirty", 1.1, 4.3, 4.6, 5.4, 0.0, 10, rng, (0.02, 0.05), (0.003, 0.004))
    tp.papers(parts["debris"], 1.0, 4.3, 2.8, 5.2, 0.0, 4, rng, ("letter", "envelope", "card"))
    tp.chair_light(furniture, V(0.32, -0.85, 0.0), -math.pi * 0.5 + 0.2, rng)
    bd.coat_rail(interior, clutter, V(west[1], 1.0, 1.75), V(west[1], 1.8, 1.75), V(1.0, 0.0, 0.0), rng, 1)
    tk.pendant(b, interior, V(0.0, -0.4, c1), rng, "glass_dirty", 0.5, "warm", 8)
    tp.bulb(b, interior, V(0.0, 4.4, c1), rng, 0.5, "warm")
    tp.wall_sheet(interior, V(west[1] + 0.006, 1.6, 1.6), V(1.0, 0.0, 0.0), "notice", rng, 1.0, 0.02)
    tp.papers(parts["debris"], -0.5, 0.5, -1.3, 5.3, 0.0, 4, rng, ("letter", "notice", "card"))
    tp.debris_field(parts, -0.5, 0.5, -1.3, 5.3, 0.0, rng, 4, 0, 0, 6)


def exterior(b, parts, gable, rng):
    roof = parts["roof"]
    clutter = parts["clutter"]
    plants = parts["plants"]
    tk.ygable_roof(b, parts, gable, rng, (-1.0, 1.0), 0.38, 0.012, [(0.6, 1.4, 2.0, 3.0, 1.0)], 0.03, 0.34, 0.72, 0.5, True, (True, True), "rock", True)
    tk.stack(b, roof, 0.0, partition[0], 1.0, 0.6, gable.ridge_top - 0.6, gable.ridge_top + 0.85, rng, 2)
    gutter_z = gable.eave_top - 0.11
    for sx, y, broken in ((-1.0, -hy + 0.25, 0.0), (1.0, -hy + 0.25, 0.0), (1.0, hy - 0.25, 1.1)):
        x_gutter = sx * (gable.edge - 0.02 + 0.06)
        rod(roof, "rusty_metal", V(x_gutter, y, gutter_z), V(sx * (hx + 0.06), y, gutter_z - 0.4), 0.035, 6)
        rod(roof, "rusty_metal", V(sx * (hx + 0.06), y, gutter_z - 0.4), V(sx * (hx + 0.06), y, -0.1 + broken), 0.035, 6)
    tk.ivy_light(plants, V(hx + 0.02, 1.5, -0.15), V(1.0, 0.0, 0.0), rng, 2.8, 1.0, 3, 8.0)
    tk.ivy_light(plants, V(-3.0, -hy - 0.02, -0.15), V(0.0, -1.0, 0.0), rng, 2.2, 0.7, 2, 8.0)
    bd.dustbin(clutter, V(2.0, hy + 0.45, -0.15), rng)
    tk.col(b, "metal", "bin", 1.75, 2.25, hy + 0.2, hy + 0.7, -0.15, 0.5)
    tk.weeds_line(plants, V(-hx + 0.4, -hy - 0.12, -0.15), V(door[0] - 0.4, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(door[1] + 0.4, -hy - 0.12, -0.15), V(hx - 0.4, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(-hx + 0.3, hy + 0.12, -0.15), V(hx - 0.3, hy + 0.12, -0.15), rng, 4)
    tk.weeds_line(plants, V(-hx - 0.12, -hy + 0.3, -0.15), V(-hx - 0.12, hy - 0.3, -0.15), rng, 3)
    tk.weeds_line(plants, V(hx + 0.12, -hy + 0.3, -0.15), V(hx + 0.12, hy - 0.3, -0.15), rng, 4)
    for index in range(4):
        kit.grass_tuft(plants, V(rng.choice((-1.0, 1.0)) * (gable.edge + 0.06), rng.uniform(-hy, hy), gutter_z + 0.02), rng, (0.06, 0.2), (3, 5), 0.03)
    tp.papers(parts["debris"], -3.5, 3.5, -6.4, -6.1, -0.15, 4, rng, ("newspaper", "notice", "card"))
    tk.chips(parts["debris"], "slate_roof", -4.0, 4.0, -6.4, -6.1, -0.15, 4, rng, (0.08, 0.17), (0.006, 0.008))
    tk.chips(parts["debris"], "slate_roof", hx + 0.1, hx + 0.6, -3.0, 3.0, -0.15, 6, rng, (0.08, 0.17), (0.006, 0.008))


def clinic():
    b = kit.Build("clinic", 1601)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    shell_walls(b, parts, gable, rng)
    frontage(b, parts, rng)
    openings(b, parts, rng)
    floors(b, parts, rng)
    face = interior_walls(b, parts, rng)
    finishes(parts, rng, face)
    waiting_room(b, parts, rng, face)
    reception(b, parts, rng)
    consulting_rooms(b, parts, rng)
    back_rooms(b, parts, rng)
    exterior(b, parts, gable, rng)
    return b


def clinic_far():
    b = kit.Build("clinic_far", 1602)
    shell = b.part("shell", 30.0)
    gable = gable_of()
    wall_top = gable.height(hx, 0.03)
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    kit.wall(shell, stone, front, tk.gable_wall_y(gable, hx), [], wall_t)
    kit.wall(shell, stone, back, tk.gable_wall_y(gable, hx), [], wall_t)
    for side, openings_list in (("left", left_windows), ("right", right_windows)):
        frame = kit.facade(side, hx, hy)
        kit.wall(shell, stone, frame, kit.rect(-by, by, -1.5, wall_top), [], wall_t)
        for w in openings_list:
            kit.skin(shell, "glass_dirty", frame, kit.rect(*w), [], 0.004, 0.001, False)
    outline = [(-hx, plinth_top), (hx, plinth_top), (hx, gable.height(hx, 0.08)), (0.0, gable.height(0.0, 0.08)), (-hx, gable.height(-hx, 0.08))]
    kit.skin(shell, render, front, outline, [kit.rect(*w) for w in windows + [vent]] + [kit.rect(door[0], door[1], plinth_top + 0.01, door[3])], 0.02, 0.0, False)
    frame_block(shell, "town_paint_black", front, -hx, hx, -0.45, plinth_top, -0.025, 0.0)
    for w in windows:
        kit.skin(shell, "glass_dirty", front, kit.rect(*w), [], 0.004, 0.001, False)
    kit.skin(shell, "soot", front, kit.rect(*vent), [], 0.004, 0.001, False)
    kit.skin(shell, "soot", front, kit.rect(door[0], door[1], 0.0, door[3]), [], 0.004, 0.026, False)
    for o in back_windows + [back_door]:
        kit.skin(shell, "glass_dirty" if o[2] > 0.5 else "soot", back, kit.rect(*o), [], 0.004, 0.001, False)
    frame_block(shell, "timber_beam", front, -0.95, 0.95, 2.86, 3.01, -0.72, 0.0)
    frame_block(shell, "town_paint_navy", front, -0.95, 0.95, 3.25, 3.72, -0.05, 0.0)
    tk.atlas_panel(shell, "town_signs", kit.frame_point(front, 0.0, 3.485, 0.052), V(0.0, -1.0, 0.0), 1.8, 0.45, tp.sg("clinic_board"), 0.0, 0.0)
    for side in (-1.0, 1.0):
        tk.roof_slab_y(shell, gable, side, gable.x0, gable.x1, "slate_roof" if side < 0 else "roof_moss", 0.15)
    block(shell, "terracotta", V(-0.13, gable.x0, gable.ridge_top - 0.04), V(0.13, gable.x1, gable.ridge_top + 0.09))
    block(shell, dressed, V(-0.5, partition[0] - 0.3, gable.ridge_top - 0.6), V(0.5, partition[0] + 0.3, gable.ridge_top + 0.97))
    for dx in (-0.22, 0.22):
        block(shell, "terracotta", V(dx - 0.08, partition[0] - 0.08, gable.ridge_top + 0.97), V(dx + 0.08, partition[0] + 0.08, gable.ridge_top + 1.35))
    return b
