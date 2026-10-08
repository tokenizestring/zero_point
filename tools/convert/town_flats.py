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
hy = 5.5
wall_t = 0.3
ix = hx - wall_t
fy = -hy + wall_t
by = hy - wall_t
levels = (0.0, 3.0, 6.0)
room_h = 2.75
roof_low = 8.75
roof_top = 9.0
parapet = 9.6
plinth_top = 0.42
stone = "granite_rubble"
render = "render_white"
trim = "town_paint_green"
frames = "painted_wood_white"
stair_x = 1.4
side_wall = (1.4, 1.52)
landing_y = -2.85
half_y = (-0.6, 0.6)
split = (0.6, 0.72)
flight_a = (-1.3, -0.15)
flight_b = (0.15, 1.3)
rise = 1.5
steps = 9
landing_door = (-4.6, -3.7)
bath_door = (1.1, 1.9)
kitchen_door = (2.5, 3.4)
bed_door = (4.7, 5.6)
bed_wall = (4.0, 4.12)
breast_y = (-1.4, 0.0)
entrance = (-0.6, 0.6, 0.0, 2.2)
front_windows = [(-6.6, -5.0), (-4.0, -2.4), (2.4, 4.0), (5.0, 6.6)]
bed_windows = [(4.8, 6.4), (-6.4, -4.8)]
kitchen_windows = [(2.2, 3.4), (-3.4, -2.2)]
bath_windows = [(0.5, 1.1), (-1.1, -0.5)]
yard_doors = [(1.7, 2.6), (-2.6, -1.7)]
yard_windows = [(2.9, 3.8), (-3.8, -2.9)]
side_living = (-3.4, -2.2)
side_bed = (2.2, 3.4)


def span(s, a, c):
    return (a, c) if s > 0 else (-c, -a)


def front_openings():
    result = []
    for f in levels:
        for a0, a1 in front_windows:
            result.append((a0, a1, f + 0.9, f + 2.4))
        if f > 0.0:
            result.append((-0.55, 0.55, f + 1.0, f + 2.4))
    result.append(entrance)
    return result


def back_openings():
    result = []
    for f in levels:
        for a0, a1 in bed_windows:
            result.append((-a1, -a0, f + 0.9, f + 2.4))
        for a0, a1 in bath_windows:
            result.append((-a1, -a0, f + 1.5, f + 2.2))
        if f > 0.0:
            for a0, a1 in kitchen_windows:
                result.append((-a1, -a0, f + 1.0, f + 2.2))
    for a0, a1 in yard_doors:
        result.append((-a1, -a0, 0.0, 2.1))
    for a0, a1 in yard_windows:
        result.append((-a1, -a0, 1.0, 2.2))
    return result


def side_openings(s):
    result = []
    for f in levels:
        for a0, a1 in (side_living, side_bed):
            a = (a0, a1) if s > 0 else (-a1, -a0)
            result.append((a[0], a[1], f + 0.9, f + 2.4))
    return result


def plinth(shell, frame, a0, a1, gaps):
    edges = [a0]
    for g0, g1 in sorted(gaps):
        edges += [g0 - 0.02, g1 + 0.02]
    edges.append(a1)
    for s0, s1 in zip(edges[0::2], edges[1::2]):
        if s1 - s0 > 0.05:
            frame_block(shell, "town_paint_black", frame, s0, s1, -0.45, plinth_top, -0.025, 0.0)


def window(b, parts, frame, opening, rng, boarded=False, rows=2):
    joinery = parts["joinery"]
    a0, a1, z0, z1 = opening
    depth = 0.07
    fw = 0.04
    frame_block(joinery, frames, frame, a0, a1, z0, z0 + fw, depth, depth + 0.05)
    frame_block(joinery, frames, frame, a0, a1, z1 - fw, z1, depth, depth + 0.05)
    frame_block(joinery, frames, frame, a0, a0 + fw, z0 + fw, z1 - fw, depth, depth + 0.05)
    frame_block(joinery, frames, frame, a1 - fw, a1, z0 + fw, z1 - fw, depth, depth + 0.05)
    cols = 2 if a1 - a0 > 0.9 else 1
    width = (a1 - a0 - 2.0 * fw) / cols
    height = (z1 - z0 - 2.0 * fw) / rows
    for c in range(1, cols):
        a = a0 + fw + width * c
        frame_block(joinery, frames, frame, a - 0.016, a + 0.016, z0 + fw, z1 - fw, depth + 0.005, depth + 0.045)
    for r in range(1, rows):
        z = z0 + fw + height * r
        frame_block(joinery, frames, frame, a0 + fw, a1 - fw, z - 0.01, z + 0.01, depth + 0.012, depth + 0.038)
    matrix = kit.frame_matrix(frame)
    choose = kit.glass_chooser(rng, 0.35, 0.3)
    for c in range(cols):
        for r in range(rows):
            kit.pane(joinery, matrix, a0 + fw + width * c + 0.012, a0 + fw + width * (c + 1) - 0.012, z0 + fw + height * r + 0.008, z0 + fw + height * (r + 1) - 0.008, depth + 0.024, choose(), rng)
    if boarded:
        tk.boards_over(joinery, frame, opening, rng)
    tk.opening_block(b, "wood" if boarded else "glass", "window", frame, opening, wall_t)
    frame_block(parts["shell"], "concrete", frame, a0 - 0.06, a1 + 0.06, z0 - 0.07, z0, -0.06, 0.1)


def shell(b, parts, rng):
    shell_part = parts["shell"]
    joinery = parts["joinery"]
    sides = (("front", hx, front_openings()), ("back", hx, back_openings()), ("left", hy, side_openings(-1.0)), ("right", hy, side_openings(1.0)))
    for side, reach, openings in sides:
        frame = kit.facade(side, hx, hy)
        a0, a1 = (-reach, reach) if side in ("front", "back") else (-by, by)
        cut = [kit.rect(o[0], o[1], -0.05, o[3]) if o[2] <= 0.01 else kit.rect(*o) for o in openings]
        kit.wall(shell_part, stone, frame, kit.rect(a0, a1, -1.5, parapet), cut, wall_t)
        kit.wall_boxes(b, "rock", side, frame, a0, a1, -1.5, parapet, wall_t, openings)
        tk.render_skin(shell_part, frame, -reach, reach, parapet - 0.07, openings, rng, 3, render, 0.02, 1, (plinth_top, plinth_top))
        plinth(shell_part, frame, -reach, reach, [(o[0], o[1]) for o in openings if o[2] <= 0.01])
        for z in (levels[1], levels[2], roof_top):
            for c0, c1, b0, b1 in tk.bands(-reach - 0.03, reach + 0.03, z - 0.06, z + 0.06, openings, 0.02):
                frame_block(shell_part, render, frame, c0, c1, b0, b1, -0.05, 0.0)
        frame_block(shell_part, "concrete", frame, -reach - 0.05, reach + 0.05, parapet, parapet + 0.06, -0.05, wall_t + 0.04)
        inner = reach - wall_t
        frame_block(shell_part, render, frame, -inner, inner, roof_top, parapet, wall_t, wall_t + 0.015)
    block(shell_part, "concrete", V(-hx, -hy, roof_low + 0.03), V(hx, hy, roof_top))
    block(shell_part, "soot", V(-ix, fy, roof_top), V(ix, by, roof_top + 0.012), 0.0, "world")
    tk.col(b, "concrete", "roof", -ix, ix, fy, by, roof_low, roof_top)
    for s in (-1.0, 1.0):
        tk.stack(b, shell_part, s * (hx - 0.3), (breast_y[0] + breast_y[1]) * 0.5, 0.8, 1.5, roof_top, roof_top + 1.3, rng, 3, render)
    for x, y in ((-5.0, 2.5), (4.2, -3.0)):
        lump(shell_part, "dirt_debris", V(x, y, roof_top + 0.01), (0.5, 0.35, 0.04), rng, 0.3, 1)
        kit.grass_tuft(parts["plants"], V(x, y, roof_top + 0.03), rng, (0.12, 0.3), (5, 9), 0.08)
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    for index, (a0, a1) in enumerate(front_windows):
        for f in levels:
            window(b, parts, front, (a0, a1, f + 0.9, f + 2.4), rng, f == 0.0 and index in (0, 3), 2)
    for f in levels[1:]:
        window(b, parts, front, (-0.55, 0.55, f + 1.0, f + 2.4), rng, False, 4)
    for f in levels:
        for a0, a1 in bed_windows:
            window(b, parts, back, (-a1, -a0, f + 0.9, f + 2.4), rng, f == 0.0 and rng.random() < 0.5)
        for a0, a1 in bath_windows:
            window(b, parts, back, (-a1, -a0, f + 1.5, f + 2.2), rng, False, 1)
        if f > 0.0:
            for a0, a1 in kitchen_windows:
                window(b, parts, back, (-a1, -a0, f + 1.0, f + 2.2), rng, False, 2)
        for frame, s in ((left, -1.0), (right, 1.0)):
            for a0, a1 in (side_living, side_bed):
                a = (a0, a1) if s > 0 else (-a1, -a0)
                window(b, parts, frame, (a[0], a[1], f + 0.9, f + 2.4), rng, f == 0.0 and rng.random() < 0.4)
    for a0, a1 in yard_windows:
        window(b, parts, back, (-a1, -a0, 1.0, 2.2), rng, False, 2)
    for index, (a0, a1) in enumerate(yard_doors):
        tk.door_unit(joinery, back, -a1, -a0, 0.0, 2.1, wall_t, trim, rng, "low" if index == 0 else "high", 80.0 + index * 25.0, "ledged", index == 0, 0.0, 0.06, 2.0, trim)
        block(shell_part, "concrete", V(a0 - 0.12, hy - 0.02, -0.4), V(a1 + 0.12, hy + 0.4, -0.06), 0.01)
        tk.col(b, "concrete", "step", a0 - 0.12, a1 + 0.12, hy, hy + 0.4, -1.5, -0.06)
        tk.col(b, "concrete", "threshold", a0, a1, by, hy, -1.5, 0.0)
    a0, a1, z0, z1 = entrance
    tk.door_unit(joinery, front, a0, a1, 0.0, z1, wall_t, trim, rng, "low", 70.0, "panel", True, 0.0, 0.07, 1.5, trim)
    block(shell_part, "concrete", V(a0 - 0.5, -hy - 0.75, z1 + 0.12), V(a1 + 0.5, -hy, z1 + 0.24), 0.01)
    tk.col(b, "concrete", "canopy", a0 - 0.5, a1 + 0.5, -hy - 0.75, -hy, z1 + 0.12, z1 + 0.24)
    frame_block(shell_part, "granite_ashlar", front, -0.52, 0.52, 2.53, 2.93, -0.02, 0.0)
    tk.atlas_panel(shell_part, "town_signs", kit.frame_point(front, 0.0, 2.73, 0.021), V(0.0, -1.0, 0.0), 0.95, 0.38, tp.sg("flats_plaque"), 0.0, 0.0)
    block(shell_part, "concrete", V(a0 - 0.25, -hy - 0.45, -0.4), V(a1 + 0.25, -hy + 0.02, -0.06), 0.01)
    tk.col(b, "concrete", "step", a0 - 0.25, a1 + 0.25, -hy - 0.45, -hy, -1.5, -0.06)
    tk.col(b, "concrete", "threshold", a0, a1, -hy, fy, -1.5, 0.0)
    for x, y, z_top in ((-hx - 0.07, hy - 0.12, roof_top + 0.3), (hx + 0.07, hy - 0.12, roof_top + 0.3)):
        rod(shell_part, "rusty_metal", V(x, y, z_top), V(x, y, -0.1), 0.04, 6)
        block(shell_part, "rusty_metal", V(x - 0.08, y - 0.08, z_top - 0.12), V(x + 0.08, y + 0.08, z_top))


def floors(b, parts, rng):
    floor = parts["floors"]
    hole = (-stair_x, stair_x, landing_y, split[0])
    for f in levels:
        if f == 0.0:
            block(floor, "concrete", V(-ix, fy, -0.3), V(ix, by, -0.03))
            tk.col(b, "concrete", "ground", -ix, ix, fy, by, -0.3, 0.0)
        else:
            inside = (side_wall[0] + side_wall[1]) * 0.5
            for x0, x1, y0, y1 in ((-ix, -inside, fy, by), (inside, ix, fy, by), (-inside, inside, fy, landing_y), (-inside, inside, (split[0] + split[1]) * 0.5, by)):
                block(floor, "concrete", V(x0, y0, f - 0.22), V(x1, y1, f - 0.03))
            tk.floor_cols(b, "wood", "floor", -ix, ix, fy, by, f - 0.25, f, [hole])
        block(floor, "town_quarry", V(-1.46, fy - 0.05, f - 0.03), V(1.46, landing_y, f), 0.0, "world")
        for s in (-1.0, 1.0):
            x0, x1 = span(s, side_wall[1], ix)
            tk.tile_floor(floor, "floorboards", x0, x1, fy, split[0], f, 0.03)
            x0, x1 = span(s, bed_wall[1], ix)
            tk.tile_floor(floor, "floorboards", x0, x1, split[1], by, f, 0.03)
            x0, x1 = span(s, side_wall[1], bed_wall[0])
            tk.tile_floor(floor, "town_lino", x0, x1, split[1], by, f, 0.03)
            x0, x1 = span(s, 0.06, side_wall[0])
            tk.tile_floor(floor, "town_tiles", x0, x1, split[1], by, f, 0.03)


def stairs(b, parts, rng):
    joinery = parts["joinery"]
    floor = parts["floors"]
    run = half_y[0] - landing_y
    for f in levels[:-1]:
        tk.stair_flight(b, parts, flight_a[0], flight_a[1], landing_y, f, run, rise, steps, rng, 1.0, "concrete", "concrete", None, None, "rock", "stair")
        tk.stair_flight(b, parts, flight_b[0], flight_b[1], half_y[0], f + rise, run, rise, steps, rng, -1.0, "concrete", "concrete", None, None, "rock", "stair")
        for x0, x1, y_low, z_low, direction in ((flight_a[0], flight_a[1], landing_y, f, 1.0), (flight_b[0], flight_b[1], half_y[0], f + rise, -1.0)):
            a = V((x0 + x1) * 0.5, y_low, z_low - 0.12)
            c = V((x0 + x1) * 0.5, y_low + direction * run, z_low + rise - 0.12)
            kit.member(floor, "concrete", a, c, x1 - x0 - 0.04, 0.14, V(1.0, 0.0, 0.0).cross((c - a).normalized()), 0.0, "box")
        block(floor, "concrete", V(-1.46, half_y[0], f + rise - 0.2), V(1.46, 0.66, f + rise - 0.03))
        block(floor, "town_quarry", V(-1.46, half_y[0], f + rise - 0.03), V(1.46, 0.66, f + rise), 0.0, "world")
        tk.col(b, "concrete", "landing", -stair_x, stair_x, half_y[0], half_y[1], f + rise - 0.2, f + rise)
        bd.balustrade(b, joinery, V(flight_a[1] + 0.03, landing_y + 0.05, f + 0.02), V(flight_a[1] + 0.03, half_y[0] - 0.02, f + rise + 0.02), rng, 0.9, 0.15, "timber_beam", "town_paint_black", 0.08, (True, False), False)
        bd.balustrade(b, joinery, V(flight_b[0] - 0.03, half_y[0] - 0.02, f + rise + 0.02), V(flight_b[0] - 0.03, landing_y + 0.05, f + 3.0 + 0.02), rng, 0.9, 0.15, "timber_beam", "town_paint_black", 0.08, (False, True), False)
    top = levels[-1]
    bd.balustrade(b, joinery, V(-stair_x + 0.04, landing_y - 0.03, top + 0.02), V(flight_b[0] - 0.03, landing_y - 0.03, top + 0.02), rng, 0.92, 0.15, "timber_beam", "town_paint_black", 0.06, (False, True), True, "landing")
    for f in levels:
        tp.bulb(b, parts["interior"], V(0.0, -4.0, f + room_h), rng, 0.4, "warm")


def walls(b, parts, rng):
    joinery = parts["joinery"]
    for f in levels:
        z1 = f + (3.02 if f < levels[-1] else room_h)
        doors = [(-bed_door[1], -bed_door[0], f, f + 2.1), (-kitchen_door[1], -kitchen_door[0], f, f + 2.1), (kitchen_door[0], kitchen_door[1], f, f + 2.1), (bed_door[0], bed_door[1], f, f + 2.1)]
        p3 = tk.partition(b, parts, V(0.0, split[0], 0.0), V(0.0, -1.0, 0.0), -ix, ix, f, z1, split[1] - split[0], doors, "partition", "rock")
        for d0, d1, z0, dz in doors:
            hinge = "low" if (d0 + d1) < 0.0 else "high"
            if rng.random() < 0.6:
                tk.door_unit(joinery, p3, d0, d1, f, 2.1, split[1] - split[0], frames, rng, hinge, rng.uniform(70.0, 100.0), "panel", True, 0.0, 0.05, rng.uniform(0.0, 3.0))
            else:
                tk.door_unit(joinery, p3, d0, d1, f, 2.1, split[1] - split[0], frames, rng, hinge, 0.0, "panel", False, 0.0, 0.05)
        for s in (-1.0, 1.0):
            normal = V(s, 0.0, 0.0)
            if s > 0:
                landing = (landing_door[0], landing_door[1], f, f + 2.1)
                bath = (bath_door[0], bath_door[1], f, f + 2.1)
            else:
                landing = (-landing_door[1], -landing_door[0], f, f + 2.1)
                bath = (-bath_door[1], -bath_door[0], f, f + 2.1)
            frame = tk.partition(b, parts, V(s * side_wall[1], 0.0, 0.0), normal, -by, by, f, z1, side_wall[1] - side_wall[0], [landing, bath], "stairwall", "rock")
            tk.door_unit(joinery, frame, landing[0], landing[1], f, 2.1, side_wall[1] - side_wall[0], trim, rng, "low" if s > 0 else "high", -rng.uniform(70.0, 100.0), "panel", rng.random() < 0.85, 0.0, 0.06, rng.uniform(0.0, 2.5))
            tk.door_unit(joinery, frame, bath[0], bath[1], f, 2.1, side_wall[1] - side_wall[0], frames, rng, "high" if s > 0 else "low", 95.0, "panel", rng.random() < 0.45, 0.0, 0.05)
            plane = kit.plane(V(s * bed_wall[1], 0.0, 0.0), normal)
            a_lo, a_hi = sorted((kit.along_of(plane, V(0.0, split[1], 0.0)), kit.along_of(plane, V(0.0, by, 0.0))))
            tk.partition(b, parts, V(s * bed_wall[1], 0.0, 0.0), normal, a_lo, a_hi, f, z1, bed_wall[1] - bed_wall[0], [], "partition", "rock")
        tk.partition(b, parts, V(0.06, 0.0, 0.0), V(1.0, 0.0, 0.0), split[1], by, f, z1, 0.12, [], "partition", "rock")


def sides_of(s):
    return ("right", "left") if s > 0 else ("left", "right")


def room_finishes(parts, rng, f, s, index):
    outer, inner = sides_of(s)
    worn = index in (1, 4)
    paper = ("paper", rng.choice(("wallpaper_faded", "town_stripe")), 1 if worn else 0, 1 if worn else 0)
    floral = ("paper", "wallpaper_faded", 0, 0)
    kitchen = ("tiles", 1.3, "kitchen_tiles", ("plaster", 1 if worn else 0))
    kitchen_inner = ("tiles", 1.3, "kitchen_tiles", ("bare",))
    bath = ("tiles", 1.5, "kitchen_tiles", ("plaster", 0))
    bath_inner = ("tiles", 1.5, "kitchen_tiles", ("bare",))
    x0, x1 = span(s, side_wall[1], ix)
    openings = {"front": [span(s, a0, a1) + (f + 0.9, f + 2.4) for a0, a1 in ((2.4, 4.0), (5.0, 6.6))], "back": [span(s, a0, a1) + (f, f + 2.1) for a0, a1 in (kitchen_door, bed_door)], outer: [(side_living[0], side_living[1], f + 0.9, f + 2.4)], inner: [(landing_door[0], landing_door[1], f, f + 2.1)]}
    tk.room(parts, rng, x0, x1, fy, split[0], f, f + room_h, {"front": paper, "back": paper, outer: paper, inner: paper}, openings, frames, None, True, 1 if worn else 0, (), {outer: [(breast_y[0] - 0.05, breast_y[1] + 0.05, f, f + room_h)]}, 2, 0.0)
    x0, x1 = span(s, bed_wall[1], ix)
    openings = {"front": [span(s, bed_door[0], bed_door[1]) + (f, f + 2.1)], "back": [span(s, 4.8, 6.4) + (f + 0.9, f + 2.4)], outer: [(side_bed[0], side_bed[1], f + 0.9, f + 2.4)]}
    tk.room(parts, rng, x0, x1, split[1], by, f, f + room_h, {"front": floral, "back": floral, outer: floral, inner: floral}, openings, frames, None, True, 0, (), None, 2, 0.0)
    x0, x1 = span(s, side_wall[1], bed_wall[0])
    if f == 0.0:
        back = [span(s, 1.7, 2.6) + (0.0, 2.1), span(s, 2.9, 3.8) + (1.0, 2.2)]
    else:
        back = [span(s, 2.2, 3.4) + (f + 1.0, f + 2.2)]
    openings = {"front": [span(s, kitchen_door[0], kitchen_door[1]) + (f, f + 2.1)], "back": back, inner: [(bath_door[0], bath_door[1], f, f + 2.1)]}
    tk.room(parts, rng, x0, x1, split[1], by, f, f + room_h, {"front": kitchen_inner, "back": kitchen, outer: kitchen_inner, inner: kitchen_inner}, openings, None, None, True, 0, (), None, 1, 0.0)
    x0, x1 = span(s, 0.06, side_wall[0])
    openings = {"back": [span(s, 0.5, 1.1) + (f + 1.5, f + 2.2)], outer: [(bath_door[0], bath_door[1], f, f + 2.1)]}
    tk.room(parts, rng, x0, x1, split[1], by, f, f + room_h, {"front": bath_inner, "back": bath, outer: bath_inner, inner: bath_inner}, openings, None, None, True, 0, (), None, 0, 0.0)


def stairwell_finishes(parts, rng):
    interior = parts["interior"]
    dado = ("tiles", 1.2, "kitchen_tiles", ("plaster", 1))
    inner = ("tiles", 1.2, "kitchen_tiles", ("bare",))
    for index, f in enumerate(levels):
        z1 = f + (3.0 if index < len(levels) - 1 else room_h)
        front = [entrance] if f == 0.0 else [(-0.55, 0.55, f + 1.0, f + 2.4)]
        tk.wall_finish(interior, "front", dado, -stair_x, stair_x, fy, split[0], f, z1, front, rng)
        tk.wall_finish(interior, "left", inner, -stair_x, stair_x, fy, split[0], f, z1, [(landing_door[0], landing_door[1], f, f + 2.1)], rng)
        tk.wall_finish(interior, "right", inner, -stair_x, stair_x, fy, split[0], f, z1, [(landing_door[0], landing_door[1], f, f + 2.1)], rng)
    tk.ceiling_skin(interior, roof_low + 0.02, -stair_x, stair_x, fy, split[0], rng, 1)
    for f in levels[1:]:
        tk.ceiling_skin(interior, f - 0.225, -stair_x, stair_x, fy, landing_y, rng, 0)


def living(b, parts, rng, f, s, look):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    P = lambda x, y, z=0.0: V(s * x, y, f + z)
    face = tk.chimney_breast(b, interior, s * ix, -s, breast_y[0], breast_y[1], f, f + room_h, 0.46, 0.66, rng)
    tk.fireplace_light(b, interior, V(face, (breast_y[0] + breast_y[1]) * 0.5, f), V(-s, 0.0, 0.0), rng, 1.2, frames, "kitchen_tiles")
    tp.mantel_clock(clutter, V(face - s * 0.09, -0.7, f + 1.16), -s * math.pi * 0.5, rng)
    if look > 0.5:
        tp.wall_mirror(interior, V(face - s * 0.01, -0.7, f + 1.75), V(-s, 0.0, 0.0), 0.7, 0.55, rng)
    if look > 0.2:
        tp.sofa_light(b, furniture, P(5.3, -0.7), s * math.pi * 0.5, rng, 1.6, rng.choice(("fabric_worn", "leather_brown")))
    if look > 0.35 or look < 0.2:
        tp.armchair_light(b, furniture, P(6.4, -2.3), tk.facing(P(6.4, -2.3), V(face, -0.7, f)), rng)
    if look > 0.3:
        bd.rug(clutter, P(6.3, -0.7), 1.4, 1.1, 0.0, rng, rng.choice(("fabric_tartan", "fabric_worn")))
    tp.table_light(furniture, s * 3.3, -3.4, f, 1.1, 0.8, 0.75, rng)
    tk.col(b, "wood", "table", min(s * 2.75, s * 3.85), max(s * 2.75, s * 3.85), -3.8, -3.0, f, f + 0.75)
    tp.chair_light(furniture, P(2.7, -3.4), s * math.pi * 0.5, rng)
    tp.chair_light(furniture, P(4.0, -3.2), s * math.pi * 0.5 - s * 2.6, rng, "timber_beam", "timber_planks_weathered", look < 0.5)
    if look > 0.55:
        tp.sideboard(b, furniture, clutter, P(6.4, split[0] - 0.27), 0.0, rng, 1.3)
        if look > 0.6:
            tp.wireless(clutter, P(6.0, split[0] - 0.24, 0.9), rng.uniform(-0.2, 0.2), rng)
    if look > 0.5:
        for a0, a1 in ((2.3, 4.1), (4.9, 6.7)):
            tp.curtain_light(clutter, P(a0, fy + 0.06, 2.48), P(a1, fy + 0.06, 2.48), 1.9, rng, rng.choice(("fabric_worn", "fabric_tartan")), 0.5, True, 5, 4)
    tp.wall_sheet(interior, P(1.54, -1.5, 1.6), V(s, 0.0, 0.0), "calendar", rng, 1.0, 0.04)
    tk.pendant(b, interior, P(4.6, -2.3, room_h), rng, "town_metal", 0.5, "warm", 8)
    tp.papers(parts["debris"], s * 2.0 if s > 0 else s * 7.4, s * 7.4 if s > 0 else s * 2.0, -5.0, 0.3, f, 4, rng, ("newspaper", "letter", "card", "envelope"))
    tp.debris_field(parts, min(s * 1.7, s * 7.5), max(s * 1.7, s * 7.5), -5.0, 0.4, f, rng, 3, 3 if f == 0.0 else 0, 0, 2)


def bedroom(b, parts, rng, f, s, look):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    P = lambda x, y, z=0.0: V(s * x, y, f + z)
    if look > 0.15:
        tp.iron_bed_light(b, furniture, clutter, P(5.15, 3.65), 0.0 if s > 0 else math.pi, rng, 1.95, 1.25, "rusty_metal", look > 0.4, rng.choice(("fabric_tartan", "fabric_worn")))
    else:
        emit(clutter, bd.cushion_geo(1.9, 0.9, 0.16, rng, 0.02, 0.05, 5, 3), "mattress", kit.turned(P(5.4, 3.7, 0.08), rng.uniform(-0.3, 0.3)), "box", True)
    tp.wardrobe_light(b, furniture, clutter, P(6.95, split[1] + 0.32), math.pi, rng)
    tp.chest_light(b, furniture, P(ix - 0.25, 4.55), -s * math.pi * 0.5, rng, 0.85, 0.46, 0.92)
    if look < 0.5:
        tp.chair_light(furniture, P(6.3, 2.0), rng.uniform(0.0, tau), rng, "timber_beam", "timber_planks_weathered", look < 0.35)
    b.loot("box", P(4.5, 1.25))
    tp.bulb(b, interior, P(5.9, 2.9, room_h), rng, 0.45, "warm")
    tp.papers(parts["debris"], min(s * 4.3, s * 7.5), max(s * 4.3, s * 7.5), 1.0, 5.0, f, 2, rng, ("letter", "card"))
    tp.debris_field(parts, min(s * 4.3, s * 7.5), max(s * 4.3, s * 7.5), 1.0, 5.0, f, rng, 2, 0, 0, 1)


def kitchen(b, parts, rng, f, s, look, index):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    P = lambda x, y, z=0.0: V(s * x, y, f + z)
    if f == 0.0:
        tp.sink_light(b, furniture, clutter, P(3.2, by - 0.25), 0.0, rng, 0.7, 0.48, 0.25)
    else:
        tp.sink_light(b, furniture, clutter, P(2.55, by - 0.25), 0.0, rng, 0.76, 0.48, 0.4)
    tp.cooker_light(b, furniture, P(bed_wall[0] - 0.3, 3.0), -s * math.pi * 0.5, rng, rng.choice(("cream", "green")))
    if index in (0, 3):
        tp.dresser_light(b, furniture, clutter, P(side_wall[1] + 0.24, 3.25), s * math.pi * 0.5, rng, rng.choice(("painted_wood_green", "painted_wood_blue", frames)), 1.3)
    else:
        bd.cabinet(furniture, P(side_wall[1] + 0.24, 3.25), 1.1, 0.46, 0.0, 0.9, s * math.pi * 0.5, rng, "timber_planks_weathered", rng.choice(("painted_wood_green", frames)), 2, 0, 1 if look < 0.5 else None)
        tk.col(b, "wood", "cupboard", min(s * side_wall[1], s * (side_wall[1] + 0.48)), max(s * side_wall[1], s * (side_wall[1] + 0.48)), 2.7, 3.8, f, f + 0.9)
    tp.table_light(furniture, s * 2.8, 1.75, f, 0.9, 0.6, 0.75, rng, "floorboards", "timber_beam", 0.0)
    tk.col(b, "wood", "table", min(s * 2.35, s * 3.25), max(s * 2.35, s * 3.25), 1.45, 2.05, f, f + 0.75)
    b.loot("food", P(2.8, 1.75, 0.75))
    tp.chair_light(furniture, P(2.8, 1.12), math.pi, rng, "timber_beam", "timber_planks_weathered", look < 0.3)
    if look < 0.5:
        tp.bucket_light(clutter, P(3.7, 4.6), rng, "rusty_metal", True)
    tp.bulb(b, interior, P(2.8, 3.0, room_h), rng, 0.4, "warm")
    tp.debris_field(parts, min(s * 1.6, s * 3.9), max(s * 1.6, s * 3.9), 0.8, 5.0, f, rng, 2, 0, 1, 0)


def bathroom(b, parts, rng, f, s, look, medical):
    furniture = parts["furniture"]
    interior = parts["interior"]
    P = lambda x, y, z=0.0: V(s * x, y, f + z)
    tp.bath(b, furniture, P(0.5, 4.3), math.pi * 0.5, rng, 1.5, 0.7, 0.6, "town_brass", 8)
    tp.toilet(b, furniture, P(1.1, by - 0.42), 0.0, rng, 1.0, rng.random() < 0.4, 8, False)
    tp.basin(b, furniture, P(side_wall[0] - 0.22, 2.6), -s * math.pi * 0.5, rng, 8)
    tp.wall_mirror(interior, P(side_wall[0] - 0.01, 2.6, 1.45), V(-s, 0.0, 0.0), 0.42, 0.5, rng)
    if medical:
        b.loot("medical", P(0.7, 1.3))


def flat(b, parts, rng, f, s, index):
    look = rng.random()
    room_finishes(parts, rng, f, s, index)
    living(b, parts, rng, f, s, look)
    bedroom(b, parts, rng, f, s, look)
    kitchen(b, parts, rng, f, s, look, index)
    bathroom(b, parts, rng, f, s, look, index in (1, 4))


def common(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.pigeonholes(interior, clutter, V(-1.0, fy + 0.03, 1.5), V(0.0, 1.0, 0.0), 2, 2, rng)
    tp.wall_sheet(interior, V(1.0, fy + 0.03, 1.55), V(0.0, 1.0, 0.0), "notice", rng, 1.0, 0.05)
    tp.crate_light(clutter, V(0.8, -1.6, 0.0), (0.6, 0.45, 0.4), 0.3, rng)
    tk.col(b, "wood", "crate", 0.45, 1.15, -1.9, -1.3, 0.0, 0.4)
    tp.papers(parts["debris"], -1.2, 1.2, -5.0, -3.0, 0.0, 6, rng, ("letter", "envelope", "newspaper", "card"))
    for f in levels[1:]:
        tp.papers(parts["debris"], -1.2, 1.2, -5.0, -3.0, f, 2, rng, ("letter", "newspaper"))
        tp.debris_field(parts, -1.2, 1.2, -5.0, -3.0, f, rng, 4, 0, 0, 1)


def yard(b, parts, rng):
    clutter = parts["clutter"]
    plants = parts["plants"]
    for x in (-5.4, 4.9):
        bd.dustbin(clutter, V(x, hy + 0.45, -0.15), rng)
        tk.col(b, "metal", "bin", x - 0.25, x + 0.25, hy + 0.2, hy + 0.7, -0.15, 0.6)
    tp.washing_line(plants, clutter, V(-7.0, hy + 1.2, 1.8), V(-1.0, hy + 1.3, 1.75), rng, 4)
    for x in (-7.0, -1.0):
        rod(clutter, "timber_beam", V(x, hy + 1.2 + (0.1 if x > -2 else 0.0), -0.15), V(x, hy + 1.2 + (0.1 if x > -2 else 0.0), 1.85), 0.035, 6)
    tk.ivy_light(plants, V(-hx - 0.02, 3.8, -0.15), V(-1.0, 0.0, 0.0), rng, 4.5, 1.0, 3, 8.0)
    tk.ivy_light(plants, V(5.2, hy + 0.02, -0.15), V(0.0, 1.0, 0.0), rng, 3.0, 0.8, 3, 8.0)
    tk.weeds_line(plants, V(-hx + 0.3, hy + 0.12, -0.15), V(hx - 0.3, hy + 0.12, -0.15), rng, 7)
    tk.weeds_line(plants, V(-hx - 0.12, -hy + 0.3, -0.15), V(-hx - 0.12, hy - 0.3, -0.15), rng, 5)
    tk.weeds_line(plants, V(hx + 0.12, -hy + 0.3, -0.15), V(hx + 0.12, hy - 0.3, -0.15), rng, 5)
    tk.chips(parts["debris"], "concrete", -6.0, 6.0, hy + 0.2, hy + 1.2, -0.15, 6, rng, (0.06, 0.16), (0.01, 0.03))


def flats():
    b = kit.Build("flats", 1901)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    shell(b, parts, rng)
    floors(b, parts, rng)
    stairs(b, parts, rng)
    walls(b, parts, rng)
    stairwell_finishes(parts, rng)
    index = 0
    for f in levels:
        for s in (-1.0, 1.0):
            flat(b, parts, rng, f, s, index)
            index += 1
    common(b, parts, rng)
    yard(b, parts, rng)
    return b


def flats_far():
    b = kit.Build("flats_far", 1902)
    shell_part = b.part("shell", 30.0)
    sides = (("front", hx, front_openings()), ("back", hx, back_openings()), ("left", hy, side_openings(-1.0)), ("right", hy, side_openings(1.0)))
    for side, reach, openings in sides:
        frame = kit.facade(side, hx, hy)
        a0, a1 = (-reach, reach) if side in ("front", "back") else (-by, by)
        kit.wall(shell_part, stone, frame, kit.rect(a0, a1, -1.5, parapet + 0.06), [], wall_t)
        kit.skin(shell_part, render, frame, kit.rect(-reach, reach, plinth_top, parapet + 0.06), [], 0.02, 0.0, False)
        frame_block(shell_part, "town_paint_black", frame, -reach, reach, -0.45, plinth_top, -0.025, 0.0)
        frame_block(shell_part, render, frame, -reach + wall_t, reach - wall_t, roof_top, parapet, wall_t, wall_t + 0.015)
        for o in openings:
            kit.skin(shell_part, "glass_dirty" if o[2] > 0.3 else "soot", frame, kit.rect(*o), [], 0.004, 0.03, False)
    block(shell_part, "soot", V(-ix, fy, roof_top - 0.2), V(ix, by, roof_top + 0.012), 0.0, "world")
    block(shell_part, "concrete", V(-1.1, -hy - 0.75, 2.32), V(1.1, -hy, 2.44))
    for s in (-1.0, 1.0):
        block(shell_part, render, V(s * (hx - 0.3) - 0.4, -1.45, roof_top), V(s * (hx - 0.3) + 0.4, 0.05, roof_top + 1.3))
    return b
