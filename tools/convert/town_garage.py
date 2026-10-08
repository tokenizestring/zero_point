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
hy = 6.0
wall_t = 0.3
shop_x = (-7.0, 3.0)
ix0 = shop_x[0] + wall_t
ix1 = shop_x[1] - wall_t
wx1 = hx - wall_t
fy = -hy + wall_t
by = hy - wall_t
lean_hi = 3.75
lean_lo = 3.15
wing_ceiling = 2.8
plinth_top = 0.42
stone = "granite_rubble"
dressed = "granite_ashlar"
render = "render_white"
trim = "town_paint_green"
roller = (-5.3, 0.3, 0.0, 4.0)
shutter_bottom = 2.65
torn_x = -0.95
gable_vent = (-2.45, -1.55, 5.45, 6.15)
office_window = (3.45, 5.25, 0.8, 2.45)
office_door = (5.55, 6.45, 0.0, 2.2)
west_windows = [(2.7, 4.5, 2.6, 3.7), (-0.8, 1.0, 2.6, 3.7), (-4.3, -2.5, 2.6, 3.7)]
east_windows = [(2.9, 3.9, 1.0, 2.3)]
back_shop = [(-0.1, 1.0, 0.0, 2.2), (4.0, 5.6, 2.6, 3.6)]
back_vent = (1.55, 2.45, 5.45, 6.15)
back_wing = [(-4.5, -3.6, 0.0, 2.1), (-6.3, -5.7, 1.6, 2.2)]
office_split = (-2.0, -1.88)
office_link = (-3.6, -2.6, 0.0, 2.1)
store_link = (0.3, 1.3, 0.0, 2.1)
store_door = (5.5, 6.4, 0.0, 2.1)
lift_center = V(-2.5, 1.2, 0.0)


def gable_of():
    return tk.YGable(-hy - 0.2, hy + 0.2, 5.0, 0.3, 4.3, 28.0, -2.0)


def lean(x):
    return lean_hi - (x - shop_x[1]) * (lean_hi - lean_lo) / (hx + 0.3 - shop_x[1])


def flip(o):
    return (-o[1], -o[0], o[2], o[3])


def gable_outline(gable, a0, a1, flipped=False, depth=0.05):
    top = lambda a: gable.height(-a if flipped else a, depth)
    apex = -gable.origin_x if flipped else gable.origin_x
    return [(a0, -1.5), (a1, -1.5), (a1, top(a1)), (apex, top(apex)), (a0, top(a0))]


def plinth(shell, frame, a0, a1, gaps):
    edges = [a0]
    for g0, g1 in sorted(gaps):
        edges += [g0 - 0.02, g1 + 0.02]
    edges.append(a1)
    for s0, s1 in zip(edges[0::2], edges[1::2]):
        if s1 - s0 > 0.05:
            frame_block(shell, "town_paint_black", frame, s0, s1, -0.45, plinth_top, -0.025, 0.0)


def louvres(joinery, frame, opening):
    a0, a1, z0, z1 = opening
    count = int((z1 - z0) / 0.13)
    for index in range(count):
        center = kit.frame_point(frame, (a0 + a1) * 0.5, z0 + 0.08 + index * 0.13, -wall_t * 0.5)
        slope = (frame[3] * 0.6 - up).normalized()
        emit(joinery, kit.geo_box(a1 - a0 + 0.02, 0.2, 0.02), "timber_planks_weathered", kit.place(center, frame[1], slope.cross(frame[1]).normalized()), "board")


def sign_lamp(b, part, x, z, rng):
    wall = V(x, -hy - 0.02, z)
    elbow = V(x, -hy - 0.2, z + 0.1)
    head = V(x, -hy - 0.3, z + 0.02)
    emit(part, kit.geo_tube([wall, elbow, head], kit.circle(0.012, 5), True), "town_paint_black", None, "given", True)
    local_block(part, "town_paint_black", kit.Matrix.Translation(wall), -0.05, 0.05, -0.015, 0.02, -0.06, 0.06)
    geo = tk.region_geo(kit.geo_lathe([(0.02, 0.05), (0.04, 0.04), (0.12, -0.04), (0.11, -0.045), (0.035, 0.035)], 10), "town_metal", "green", 0.4)
    emit(part, geo, "town_metal", kit.Matrix.Translation(head) @ kit.Matrix.Rotation(0.5, 4, 'X'), "texture", True)
    b.light("warm", head + V(0.0, 0.04, -0.1))


def shell_walls(b, parts, gable, rng):
    shell = parts["shell"]
    eave = gable.height(shop_x[0], 0.03)
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    wing_top = lambda x: lean(x) - 0.05
    kit.wall(shell, stone, front, gable_outline(gable, shop_x[0], shop_x[1]), [kit.rect(roller[0], roller[1], -0.05, roller[3]), kit.rect(*gable_vent)], wall_t)
    kit.wall_boxes(b, "rock", "front", front, shop_x[0], shop_x[1], -1.5, eave, wall_t, [roller, gable_vent])
    tk.gable_cols_y(b, "gable", -hy, fy, gable, eave)
    kit.wall(shell, stone, front, [(shop_x[1], -1.5), (hx, -1.5), (hx, wing_top(hx)), (shop_x[1], wing_top(shop_x[1]))], [kit.rect(*office_window), kit.rect(office_door[0], office_door[1], -0.05, office_door[3])], wall_t)
    kit.wall_boxes(b, "rock", "front", front, shop_x[1], hx, -1.5, wing_top(hx), wall_t, [office_window, office_door])
    kit.wall(shell, stone, back, gable_outline(gable, -shop_x[1], -shop_x[0], True), [kit.rect(back_shop[0][0], back_shop[0][1], -0.05, back_shop[0][3]), kit.rect(*back_shop[1]), kit.rect(*back_vent)], wall_t)
    kit.wall_boxes(b, "rock", "back", back, -shop_x[1], -shop_x[0], -1.5, eave, wall_t, back_shop + [back_vent])
    tk.gable_cols_y(b, "gable", by, hy, gable, eave)
    kit.wall(shell, stone, back, [(-hx, -1.5), (-shop_x[1], -1.5), (-shop_x[1], wing_top(shop_x[1])), (-hx, wing_top(hx))], [kit.rect(back_wing[0][0], back_wing[0][1], -0.05, back_wing[0][3]), kit.rect(*back_wing[1])], wall_t)
    kit.wall_boxes(b, "rock", "back", back, -hx, -shop_x[1], -1.5, wing_top(hx), wall_t, back_wing)
    kit.wall(shell, stone, left, kit.rect(-by, by, -1.5, eave), [kit.rect(*w) for w in west_windows], wall_t)
    kit.wall_boxes(b, "rock", "left", left, -by, by, -1.5, eave, wall_t, west_windows)
    kit.wall(shell, stone, right, kit.rect(-by, by, -1.5, wing_top(hx)), [kit.rect(*w) for w in east_windows], wall_t)
    kit.wall_boxes(b, "rock", "right", right, -by, by, -1.5, wing_top(hx), wall_t, east_windows)
    tk.partition(b, parts, V(shop_x[1], 0.0, 0.0), V(1.0, 0.0, 0.0), fy, by, 0.0, eave, wall_t, [office_link, store_link], "shared", "rock", stone)
    for x0, x1 in ((shop_x[0], ix0), (ix1, shop_x[1])):
        outline = [(x0, eave - 0.02), (x1, eave - 0.02), (x1, gable.height(x1, -0.004)), (x0, gable.height(x0, -0.004))]
        emit(shell, kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), up, V(0.0, -1.0, 0.0), outline, [], -by, by), "timber_beam", None, "box")
    tk.gable_skin_y(shell, front, gable, shop_x[0], shop_x[1], plinth_top, [roller, gable_vent], rng, 4, render, 0.02)
    wing = [(shop_x[1], plinth_top), (office_door[0], plinth_top), (office_door[0], office_door[3]), (office_door[1], office_door[3]), (office_door[1], plinth_top), (hx, plinth_top), (hx, lean(hx) - 0.08), (shop_x[1], lean(shop_x[1]) - 0.08)]
    kit.skin(shell, render, front, wing, [kit.rect(*office_window)], 0.02)
    plinth(shell, front, shop_x[0], hx, [(roller[0], roller[1]), (office_door[0], office_door[1])])
    tk.quoins_light(shell, dressed, V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), plinth_top, eave - 0.12, rng, 0.035)
    tk.quoins_light(shell, dressed, V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), plinth_top, lean(hx) - 0.12, rng, 0.035)
    bd.damp_band(shell, back, -hx, hx, rng, 0.35, 1.0, "granite_rubble_damp", -0.2, 0.003, [(back_shop[0][0] - 0.05, back_shop[0][1] + 0.05), (back_wing[0][0] - 0.05, back_wing[0][1] + 0.05)])
    for frame in (left, right):
        bd.damp_band(shell, frame, -hy, hy, rng, 0.3, 0.9, "granite_rubble_damp", -0.2, 0.003)
    return eave


def frontage(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    front = kit.facade("front", hx, hy)
    a0, a1, z0, z1 = roller
    frame_block(shell, "rusty_metal", front, a0 - 0.3, a1 + 0.3, z1, z1 + 0.28, -0.03, wall_t)
    for a in (a0, a1 - 0.07):
        frame_block(joinery, "rusty_metal", front, a, a + 0.07, 0.0, z1, 0.06, 0.18)
    block(joinery, "rusty_metal", V(a0 - 0.12, fy, z1 - 0.02), V(a1 + 0.12, fy + 0.45, z1 + 0.45))
    origin = kit.frame_point(front, a0 + 0.07, shutter_bottom, -0.12)
    kit.corrugated_sheet(joinery, origin, up, V(1.0, 0.0, 0.0), z1 - shutter_bottom, a1 - a0 - 0.14, rng, "corrugated_rusty", 0.014, 9.0, 3, 0.002, 0.0, 1, 0.0, 0.02)
    local_block(joinery, "rusty_metal", kit.frame_matrix(front), a0 + 0.07, torn_x, 0.1, 0.14, shutter_bottom - 0.06, shutter_bottom)
    tk.col(b, "metal", "shutter", a0, a1, -hy + 0.06, -hy + 0.18, shutter_bottom, z1)
    top = kit.frame_point(front, torn_x, shutter_bottom, -0.12)
    foot = kit.frame_point(front, torn_x, 1.2, -0.12) - V(0.0, 0.3, 0.0)
    slope = top - foot
    kit.corrugated_sheet(joinery, foot, slope, V(1.0, 0.0, 0.0), slope.length, a1 - 0.07 - torn_x, rng, "corrugated_rusty", 0.014, 9.0, 3, 0.002, 0.0, 1, 0.0, 0.08)
    local_block(joinery, "rusty_metal", kit.Matrix.Translation(foot), 0.0, a1 - 0.07 - torn_x, -0.02, 0.02, -0.05, 0.0)
    tk.col(b, "metal", "shutter", torn_x, a1, -hy - 0.22, -hy + 0.16, 1.2, shutter_bottom)
    frame_block(joinery, "town_paint_cream", front, -5.35, 1.35, 4.28, 4.92, -0.06, 0.0, 0.0, "board")
    tk.atlas_quad(joinery, "town_signs", [kit.frame_point(front, -5.3, 4.3, 0.061), kit.frame_point(front, 1.3, 4.3, 0.061), kit.frame_point(front, 1.3, 4.9, 0.061), kit.frame_point(front, -5.3, 4.9, 0.061)], tp.sg("garage_fascia"))
    for x in (-4.0, -0.4):
        sign_lamp(b, joinery, x, 5.15, rng)
    tp.enamel_sign(shell, kit.frame_point(front, 1.75, 2.15, 0.025), V(0.0, -1.0, 0.0), 0.5, 0.32, "enamel_oil", rng, 0.03)
    tk.atlas_panel(shell, "town_signs", kit.frame_point(front, -5.95, 2.0, 0.02), V(0.0, -1.0, 0.0), 0.5, 0.33, tp.sg("garage_door"), -0.05, 0.0)
    louvres(joinery, front, gable_vent)
    tk.opening_block(b, "wood", "vent", front, gable_vent, wall_t)
    a0, a1, z0, z1 = office_window
    middle = (a0 + a1) * 0.5
    frame_block(joinery, trim, front, a0 - 0.04, a1 + 0.04, z0 - 0.07, z0, -0.05, 0.12, 0.0, "board")
    frame_block(joinery, trim, front, a0, a1, z1 - 0.07, z1, 0.0, 0.12, 0.0, "board")
    for a in (a0, middle - 0.03, a1 - 0.06):
        frame_block(joinery, trim, front, a, a + 0.06, z0, z1 - 0.07, 0.0, 0.12, 0.0, "board")
    matrix = kit.frame_matrix(front)
    kit.pane(joinery, matrix, a0 + 0.06, middle - 0.03, z0, z1 - 0.07, 0.06, "shard", rng)
    kit.pane(joinery, matrix, middle + 0.03, a1 - 0.06, z0, z1 - 0.07, 0.06, "whole", rng)
    tk.opening_block(b, "glass", "window", front, (a0, middle, z0, z1), wall_t)
    tk.boards_over(joinery, front, (middle - 0.05, a1, z0, z1), rng, "timber_planks_weathered", 5, 0.025, 0.4)
    tk.opening_block(b, "wood", "boards", front, (middle, a1, z0, z1), wall_t)
    a0, a1, z0, z1 = office_door
    tk.door_unit(joinery, front, a0, a1, 0.0, z1, wall_t, trim, rng, "high", 92.0, "ledged", True, 0.0, 0.06, 2.0, trim)
    block(shell, "concrete", V(a0 - 0.1, -hy - 0.35, -0.4), V(a1 + 0.1, -hy + 0.02, -0.05), 0.01)
    tk.col(b, "concrete", "step", a0 - 0.1, a1 + 0.1, -hy - 0.35, -hy, -1.5, -0.05)
    tk.col(b, "concrete", "threshold", a0, a1, -hy, fy, -1.5, 0.0)
    block(shell, "concrete", V(roller[0], -hy - 0.3, -0.4), V(roller[1], fy, 0.0), 0.0, "world")
    tk.col(b, "concrete", "apron", roller[0], roller[1], -hy - 0.3, fy, -1.5, 0.0)


def openings(b, parts, rng):
    joinery = parts["joinery"]
    shell = parts["shell"]
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    for frame, w in ((left, west_windows[0]), (left, west_windows[1]), (left, west_windows[2]), (back, back_shop[1])):
        tk.casement(b, parts, frame, w, wall_t, rng, "painted_wood_white", 0.08, [0.0, 0.0], 0.25, 0.35, 2, "concrete")
    tk.casement(b, parts, right, east_windows[0], wall_t, rng, "painted_wood_white", 0.08, [0.0, 25.0], 0.3, 0.3, 2, "concrete")
    tk.casement(b, parts, back, back_wing[1], wall_t, rng, "painted_wood_white", 0.08, [40.0], 0.3, 0.3, 1, "concrete")
    a0, a1, z0, z1 = back_shop[0]
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, trim, rng, "low", 97.0, "ledged", True, 0.0, 0.06, 3.0, trim)
    a0, a1, z0, z1 = back_wing[0]
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, trim, rng, "high", 90.0, "ledged", True, 0.0, 0.06, 2.0, trim)
    for a0, a1 in ((back_shop[0][0], back_shop[0][1]), (back_wing[0][0], back_wing[0][1])):
        block(shell, "concrete", V(-a1 - 0.1, hy - 0.04, -0.35), V(-a0 + 0.1, hy + 0.36, -0.06), 0.01)
        tk.col(b, "concrete", "threshold", -a1, -a0, by, hy, -1.5, 0.0)
        tk.col(b, "concrete", "step", -a1 - 0.1, -a0 + 0.1, hy, hy + 0.36, -0.6, -0.06)
    louvres(joinery, back, back_vent)
    tk.opening_block(b, "wood", "vent", back, back_vent, wall_t)


def floors(b, parts, rng):
    floor = parts["floors"]
    tk.tile_floor(floor, "concrete", ix0, ix1, fy, by, 0.0, 0.06)
    tk.board_floor(floor, shop_x[1], wx1, fy, office_split[1], 0.0, rng, "y", (), "floorboards", 0.03, 0.0, (0.15, 0.2), (0.5,))
    tk.tile_floor(floor, "concrete", shop_x[1], wx1, office_split[1], by, 0.0, 0.06)
    for d in (office_link, store_link):
        block(floor, "concrete", V(ix1, d[0], -0.02), V(shop_x[1], d[1], 0.004))
    tk.col(b, "concrete", "ground", ix0, ix1, fy, by, -0.3, 0.0)
    tk.col(b, "wood", "ground", shop_x[1], wx1, fy, office_split[0], -0.3, 0.0)
    tk.col(b, "concrete", "ground", shop_x[1], wx1, office_split[0], by, -0.3, 0.0)
    for center, size in ((V(-2.3, 0.4, 0.0), 0.32), (V(-4.4, 4.1, 0.0), 0.26), (V(0.5, 4.3, 0.0), 0.3)):
        shape = kit.blob(0.0, 0.0, size, size * rng.uniform(0.5, 0.9), rng, 12, 0.3)
        emit(floor, kit.geo_slab(center + V(0.0, 0.0, 0.002), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), shape, [], 0.0, 0.001, False), "soot", None, "world")


def trusses(parts, gable, eave):
    joinery = parts["joinery"]
    ox = gable.origin_x
    for y in (-3.9, -1.3, 1.3, 3.9):
        left = V(ix0 - 0.1, y, eave - 0.035)
        right = V(ix1 + 0.1, y, eave - 0.035)
        apex = V(ox, y, gable.height(ox, 0.16))
        foot = V(ox, y, eave - 0.035)
        kit.member(joinery, "rusty_metal", left, right, 0.07, 0.07, up, 0.0, "box")
        for a in (left, right):
            kit.member(joinery, "rusty_metal", a, apex, 0.07, 0.07, V(0.0, 1.0, 0.0).cross((apex - a).normalized()), 0.0, "box")
            kit.member(joinery, "rusty_metal", foot, a.lerp(apex, 0.5), 0.045, 0.045, V(0.0, 1.0, 0.0), 0.0, "box")
        kit.member(joinery, "rusty_metal", foot, apex, 0.05, 0.05, V(1.0, 0.0, 0.0), 0.0, "box")


def lean_roof(b, parts, rng):
    roof = parts["roof"]
    x0 = shop_x[1]
    x1 = hx + 0.3
    along = (V(x0 - x1, 0.0, lean(x0) - lean(x1))).normalized()
    length = (V(x0 - x1, 0.0, lean(x0) - lean(x1))).length
    y = -hy - 0.25
    while y < hy + 0.2:
        w = min(0.9, hy + 0.25 - y)
        if rng.random() > 0.06:
            origin = V(x1, y, lean(x1) + 0.01 + rng.uniform(0.0, 0.005))
            kit.corrugated_sheet(roof, origin, V(0.0, 1.0, 0.0), along, w + 0.04, length, rng, "corrugated_rusty", 0.012, 6.0, 4, 0.0015, rng.uniform(0.0, 0.03), 1, rng.uniform(0.0, 0.1), rng.uniform(-0.02, 0.02))
        y += w
    for x in (x0 + 0.6, (x0 + x1) * 0.5, x1 - 0.6):
        kit.member(roof, "timber_beam", V(x, -hy, lean(x) - 0.06), V(x, hy, lean(x) - 0.06), 0.06, 0.1, up, 0.0, "box")
    rod(roof, "rusty_metal", V(x1 - 0.02, -hy - 0.25, lean(x1) - 0.08), V(x1 - 0.02, hy + 0.25, lean(x1) - 0.08), 0.06, 6)
    b.ramp("nx", "metal", "roof", V(x0, -hy - 0.25, lean(x1)), V(x1, hy + 0.25, lean(x0)))


def wing_walls(b, parts, rng):
    joinery = parts["joinery"]
    thickness = office_split[1] - office_split[0]
    split = tk.partition(b, parts, V(0.0, office_split[0], 0.0), V(0.0, -1.0, 0.0), shop_x[1], wx1, 0.0, wing_ceiling, thickness, [store_door], "split")
    tk.door_unit(joinery, split, store_door[0], store_door[1], 0.0, store_door[3], thickness, trim, rng, "low", 100.0, "ledged")


def finishes(parts, rng):
    interior = parts["interior"]
    wash = ("plaster", 2)
    clean = ("plaster", 0)
    dado = ("panel", 1.0, "painted_wood_green", clean)
    tk.wall_finish(interior, "left", wash, ix0, ix1, fy, by, 0.0, 2.3, [], rng)
    tk.wall_finish(interior, "front", wash, ix0, roller[0], fy, by, 0.0, 2.3, [], rng)
    tk.wall_finish(interior, "front", wash, roller[1], ix1, fy, by, 0.0, 2.3, [], rng)
    tk.wall_finish(interior, "back", wash, ix0, ix1, fy, by, 0.0, 2.3, [flip(back_shop[0])], rng)
    tk.wall_finish(interior, "right", wash, ix0, ix1, fy, by, 0.0, 2.3, [office_link, store_link], rng)
    tk.room(parts, rng, shop_x[1], wx1, fy, office_split[0], 0.0, wing_ceiling, {"front": ("panel", 1.0, "painted_wood_green", ("paper", "town_stripe", 1, 1)), "left": dado, "right": dado, "back": dado}, {"front": [office_window, office_door], "left": [office_link], "back": [store_door]}, None, None, True, 1, (), None, 2, 0.0)
    tk.room(parts, rng, shop_x[1], wx1, office_split[1], by, 0.0, wing_ceiling, {"front": wash, "left": wash, "right": wash, "back": wash}, {"front": [store_door], "left": [store_link], "right": east_windows, "back": [flip(back_wing[0]), flip(back_wing[1])]}, None, None, True, 0, (), None, 4, 0.0)


def workshop(b, parts, rng, eave):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    top = tp.four_post_lift(b, furniture, lift_center, math.pi * 0.5, rng)
    tp.vintage_car(b, furniture, V(lift_center.x, lift_center.y + 0.1, top.z), math.pi * 0.5, rng, "blue")
    tp.engine_hoist(b, furniture, clutter, V(-5.0, -2.6, 0.0), 0.35, rng)
    for position in (V(-1.95, -2.6, 0.0), V(-3.05, -2.75, 0.0)):
        tp.axle_stand(clutter, position, rng)
    tp.trolley_jack(clutter, V(-0.6, -1.4, 0.0), 2.2, rng)
    bd.workbench(b, furniture, clutter, V(ix0 + 0.29, 0.6, 0.0), math.pi * 0.5, rng, 2.8)
    tp.tool_board(interior, V(ix0 + 0.016, 0.6, 1.62), V(1.0, 0.0, 0.0), 2.4, 0.85, rng)
    for y in (-0.55, -0.38, 1.55, 1.72):
        bd.tin(clutter, V(ix0 + 0.2 + rng.uniform(-0.05, 0.05), y, 0.9), rng)
    bd.workbench(b, furniture, clutter, V(-4.5, by - 0.29, 0.0), 0.0, rng, 2.4)
    tp.tool_board(interior, V(-4.5, by - 0.016, 1.62), V(0.0, -1.0, 0.0), 2.0, 0.8, rng)
    tp.engine_block(clutter, V(-4.15, by - 0.27, 0.9), 0.08, rng, "green")
    b.loot("toolbox", V(-5.05, by - 0.29, 0.9))
    b.loot("toolbox", V(-0.85, 2.7, 0.0))
    tp.tyre_stack(b, clutter, V(-6.1, -5.0, 0.0), rng, 4)
    tp.tyre_stack(b, clutter, V(-5.75, -4.35, 0.0), rng, 3)
    for y in (-2.15, -1.45, -0.75):
        tp.tyre_light(clutter, kit.Matrix.Translation(V(ix1 - 0.17, y, 0.31)) @ kit.Matrix.Rotation(math.pi * 0.5 + rng.uniform(0.15, 0.25), 4, 'Y'), rng)
    tk.col(b, "fabric", "tyres", ix1 - 0.45, ix1, -2.5, -0.4, 0.0, 0.66)
    for position, region, tipped in ((V(2.15, 5.15, 0.0), "red", False), (V(1.5, 5.25, 0.0), "green", False), (V(2.2, 4.5, 0.0), "red", False), (V(0.95, 4.6, 0.0), "blue", True)):
        tp.oil_drum(b, furniture, position, rng, region, tipped)
    for position, yaw in ((V(1.3, 3.95, 0.0), 0.4), (V(1.65, 3.8, 0.0), -0.2)):
        bd.jerrycan(clutter, position, yaw, rng)
    tk.col(b, "metal", "cans", 1.1, 1.85, 3.65, 4.1, 0.0, 0.47)
    bd.bicycle(clutter, V(ix0 + 0.35, -3.4, 0.0), math.pi * 0.5, 0.25, rng)
    tk.col(b, "metal", "bicycle", ix0, ix0 + 0.55, -4.3, -2.5, 0.0, 1.0)
    bd.long_tool(clutter, V(ix1 - 0.12, 2.6, 0.0), V(ix1 - 0.04, 2.75, 1.4), "broom", rng)
    tp.bucket_light(clutter, V(-1.6, 5.2, 0.0), rng, "rusty_metal", True)
    tp.enamel_sign(interior, V(ix1 - 0.012, -0.8, 2.5), V(-1.0, 0.0, 0.0), 0.9, 0.34, "enamel_oil", rng, 0.02)
    tp.wall_sheet(interior, V(ix1 - 0.02, 3.2, 1.6), V(-1.0, 0.0, 0.0), "calendar", rng, 1.0, 0.04)
    for x, y in ((-4.6, -3.9), (-0.4, -3.9), (-4.6, 3.9), (-0.4, 3.9)):
        tp.workshop_shade(b, interior, V(x, y, eave - 0.07), rng, 1.3)
    tp.cage_lamp(b, interior, V(-2.5, 1.3, eave - 0.07), rng, "cold")
    tp.papers(parts["debris"], -6.0, 2.0, -5.3, 5.0, 0.0, 6, rng, ("newspaper", "notice", "card", "letter"))
    tp.papers(parts["debris"], -5.0, -1.2, -6.2, -5.8, 0.0, 3, rng, ("newspaper", "card"))
    tp.debris_field(parts, -6.4, 2.4, -5.4, 5.4, 0.0, rng, 6, 5, 0, 14, 0)
    tk.chips(parts["debris"], "corrugated_rusty", -3.5, -1.5, 2.6, 4.8, 0.0, 6, rng, (0.08, 0.2), (0.004, 0.006))


def wing_rooms(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.desk_light(b, furniture, clutter, V(4.35, fy + 0.39, 0.0), math.pi, rng, 1.3, 0.7, 0.76, "timber_beam", "floorboards", ("papers", "phone", "files"))
    tp.chair_light(furniture, V(4.35, -4.5, 0.0), tk.facing(V(4.35, -4.5, 0.0), V(4.35, -5.5, 0.0)), rng)
    tp.filing_cabinet(b, furniture, V(3.62, office_split[0] - 0.36, 0.0), 0.0, rng, 4, "green")
    tp.safe_light(b, furniture, V(4.95, office_split[0] - 0.31, 0.0), 0.0, rng, 1.3)
    b.loot("box", V(4.22, office_split[0] - 0.22, 0.0))
    bd.shelf(interior, V(wx1 - 0.02, -5.5, 1.6), V(wx1 - 0.02, -4.1, 1.6), 0.26, V(-1.0, 0.0, 0.0), rng)
    for k in range(4):
        y = -5.3 + k * 0.32
        tp.painted_box(clutter, rng.choice(("red", "green", "cream")), kit.turned(V(wx1 - 0.15, y, 1.6), rng.uniform(-0.1, 0.1)), -0.08, 0.08, -0.1, 0.1, 0.0, rng.uniform(0.14, 0.24))
    tp.wall_sheet(interior, V(shop_x[1] + 0.03, -4.6, 1.55), V(1.0, 0.0, 0.0), "calendar", rng, 1.0, 0.03)
    tp.wall_clock(interior, V(5.0, office_split[0] - 0.03, 2.25), V(0.0, -1.0, 0.0), rng, 0.15)
    tp.enamel_sign(interior, V(wx1 - 0.02, -2.6, 2.1), V(-1.0, 0.0, 0.0), 0.5, 0.19, "enamel_smoke", rng, -0.04)
    tp.pigeonholes(interior, clutter, V(4.0, office_split[0] - 0.02, 1.75), V(0.0, -1.0, 0.0), 3, 2, rng)
    tk.pendant(b, interior, V(4.8, -3.8, wing_ceiling), rng, "town_metal", 0.5, "warm", 8)
    tp.papers(parts["debris"], 3.3, 6.4, -5.4, -2.3, 0.0, 6, rng, ("letter", "envelope", "card", "notice"))
    tp.debris_field(parts, 3.3, 6.4, -5.4, -2.3, 0.0, rng, 3, 4, 0, 4)
    tp.wall_shelves(b, furniture, clutter, V(wx1 - 0.01, -1.6, 0.0), V(wx1 - 0.01, 2.6, 0.0), V(-1.0, 0.0, 0.0), [0.2, 0.86, 1.52, 2.18], rng, ("gap",), 0.6)
    for z in (0.2, 0.86, 1.52):
        y = -1.45
        while y < 2.3:
            roll = rng.random()
            if roll < 0.4:
                tp.tyre_light(clutter, kit.Matrix.Translation(V(wx1 - 0.32, y + 0.09, z + 0.29)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), rng, 0.28, 0.15)
                y += 0.2
            elif roll < 0.75:
                tp.painted_box(clutter, rng.choice(("red", "green", "cream", "blue")), kit.turned(V(wx1 - 0.3, y + 0.16, z), rng.uniform(-0.1, 0.1)), -0.2, 0.2, -0.14, 0.14, 0.0, rng.uniform(0.15, 0.4))
                y += 0.36
            else:
                y += 0.3
    for position, region in ((V(3.55, 3.4, 0.0), "red"), (V(3.6, 4.05, 0.0), "green")):
        tp.oil_drum(b, furniture, position, rng, region)
    tp.tyre_stack(b, clutter, V(4.3, 2.2, 0.0), rng, 5)
    for position, yaw in ((V(3.35, 2.4, 0.0), 0.2), (V(3.4, 2.85, 0.0), -0.1)):
        bd.jerrycan(clutter, position, yaw, rng)
    tk.col(b, "metal", "cans", 3.15, 3.6, 2.25, 2.98, 0.0, 0.47)
    tp.crate_light(clutter, V(3.6, -1.2, 0.0), (0.6, 0.45, 0.42), 0.2, rng)
    tk.col(b, "wood", "crate", 3.25, 3.95, -1.5, -0.9, 0.0, 0.42)
    b.loot("box", V(3.6, -1.2, 0.42))
    b.loot("toolbox", V(5.6, 0.4, 0.0))
    tp.cubicles(b, furniture, 5.45, wx1, by, 4.45, 0.0, 1, rng, trim, (True, False))
    tp.bulb(b, interior, V(4.6, 1.5, wing_ceiling), rng, 0.45, "warm")
    tp.bulb(b, interior, V(4.6, 4.6, wing_ceiling), rng, 0.4, "cold")
    tp.papers(parts["debris"], 3.3, 6.0, -1.6, 4.0, 0.0, 3, rng, ("newspaper", "card"))
    tp.debris_field(parts, 3.3, 6.0, -1.6, 4.3, 0.0, rng, 3, 0, 0, 4)


def exterior(b, parts, gable, rng):
    roof = parts["roof"]
    clutter = parts["clutter"]
    plants = parts["plants"]
    tk.corrugated_ygable(b, parts, gable, rng, (-1.0, 1.0), 0.9, 0.06, {1.0: [(-1.1, -0.2), (2.4, 3.3)], -1.0: [(0.5, 1.4)]}, "metal", 3)
    for y in (gable.x0, gable.x1):
        for side in (-1.0, 1.0):
            kit.member(roof, "timber_planks_weathered", gable.point(side, y, -0.1, -0.06), gable.point(side, y, gable.run, -0.06), 0.04, 0.22, gable.normal(side), 0.0, "board")
    gutter_x = gable.origin_x - gable.edge - 0.03
    rod(roof, "rusty_metal", V(gutter_x, gable.x0, gable.eave_top - 0.07), V(gutter_x, gable.x1, gable.eave_top - 0.07), 0.06, 6)
    lean_roof(b, parts, rng)
    for x, y, z_top, z_bottom, neck in ((shop_x[0], -hy + 0.1, gable.eave_top - 0.1, -0.1, gutter_x), (shop_x[0], hy - 0.1, gable.eave_top - 0.1, 1.15, gutter_x), (hx, hy - 0.1, lean_lo - 0.1, -0.1, hx + 0.28)):
        side = -1.0 if x < 0.0 else 1.0
        wall_x = x + side * 0.07
        rod(roof, "rusty_metal", V(neck, y, z_top), V(wall_x, y, z_top - 0.25), 0.035, 6)
        rod(roof, "rusty_metal", V(wall_x, y, z_top - 0.25), V(wall_x, y, z_bottom), 0.035, 6)
    for position, region in ((V(-2.6, hy + 0.6, -0.15), "red"), (V(-1.95, hy + 0.75, -0.15), "blue")):
        tp.oil_drum(b, clutter, position, rng, region)
    tp.oil_drum(b, clutter, V(-3.4, hy + 0.7, -0.15), rng, "green", True)
    tp.tyre_stack(b, clutter, V(5.4, hy + 0.65, -0.15), rng, 3)
    tk.ivy_light(plants, V(hx + 0.02, -2.5, -0.15), V(1.0, 0.0, 0.0), rng, 2.6, 1.0, 3, 8.0)
    tk.ivy_light(plants, V(-6.4, hy + 0.02, -0.15), V(0.0, 1.0, 0.0), rng, 3.2, 0.8, 3, 8.0)
    tk.weeds_line(plants, V(shop_x[0] + 0.3, -hy - 0.12, -0.15), V(roller[0] - 0.3, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(roller[1] + 0.3, -hy - 0.12, -0.15), V(office_door[0] - 0.3, -hy - 0.12, -0.15), rng, 3)
    tk.weeds_line(plants, V(-hx + 0.3, hy + 0.12, -0.15), V(hx - 0.3, hy + 0.12, -0.15), rng, 5)
    tk.weeds_line(plants, V(-hx - 0.12, -hy + 0.3, -0.15), V(-hx - 0.12, hy - 0.3, -0.15), rng, 4)
    tk.weeds_line(plants, V(hx + 0.12, -hy + 0.3, -0.15), V(hx + 0.12, hy - 0.3, -0.15), rng, 4)
    tk.weeds_line(plants, V(roller[0] + 0.2, -hy - 0.1, 0.0), V(roller[1] - 0.2, -hy - 0.1, 0.0), rng, 4)
    tk.chips(parts["debris"], "corrugated_rusty", -6.0, 6.0, hy + 0.2, hy + 0.9, -0.15, 6, rng, (0.08, 0.2), (0.004, 0.006))


def garage():
    b = kit.Build("garage", 1701)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    gable = gable_of()
    eave = shell_walls(b, parts, gable, rng)
    frontage(b, parts, rng)
    openings(b, parts, rng)
    floors(b, parts, rng)
    trusses(parts, gable, eave)
    wing_walls(b, parts, rng)
    finishes(parts, rng)
    workshop(b, parts, rng, eave)
    wing_rooms(b, parts, rng)
    exterior(b, parts, gable, rng)
    return b


def garage_far():
    b = kit.Build("garage_far", 1702)
    shell = b.part("shell", 30.0)
    gable = gable_of()
    eave = gable.height(shop_x[0], 0.03)
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    kit.wall(shell, stone, front, gable_outline(gable, shop_x[0], shop_x[1]), [], wall_t)
    kit.wall(shell, stone, front, [(shop_x[1], -1.5), (hx, -1.5), (hx, lean(hx) - 0.05), (shop_x[1], lean(shop_x[1]) - 0.05)], [], wall_t)
    kit.wall(shell, stone, back, gable_outline(gable, -shop_x[1], -shop_x[0], True), [], wall_t)
    kit.wall(shell, stone, back, [(-hx, -1.5), (-shop_x[1], -1.5), (-shop_x[1], lean(shop_x[1]) - 0.05), (-hx, lean(hx) - 0.05)], [], wall_t)
    kit.wall(shell, stone, left, kit.rect(-by, by, -1.5, eave), [], wall_t)
    kit.wall(shell, stone, right, kit.rect(-by, by, -1.5, lean(hx) - 0.05), [], wall_t)
    kit.wall(shell, stone, kit.plane(V(shop_x[1], 0.0, 0.0), V(1.0, 0.0, 0.0)), kit.rect(-by, by, lean(shop_x[1]) - 0.3, eave), [], wall_t)
    outline = [(shop_x[0], plinth_top), (hx, plinth_top), (hx, lean(hx) - 0.08), (shop_x[1], lean(shop_x[1]) - 0.08), (shop_x[1], gable.height(shop_x[1], 0.08)), (gable.origin_x, gable.height(gable.origin_x, 0.08)), (shop_x[0], gable.height(shop_x[0], 0.08))]
    kit.skin(shell, render, front, outline, [], 0.02, 0.0, False)
    frame_block(shell, "town_paint_black", front, shop_x[0], hx, -0.45, plinth_top, -0.025, 0.0)
    kit.skin(shell, "soot", front, kit.rect(roller[0], roller[1], -0.1, shutter_bottom), [], 0.004, 0.03, False)
    kit.skin(shell, "corrugated_rusty", front, kit.rect(roller[0], roller[1], shutter_bottom, roller[3]), [], 0.004, 0.03, False)
    kit.skin(shell, "rusty_metal", front, kit.rect(roller[0] - 0.3, roller[1] + 0.3, roller[3], roller[3] + 0.28), [], 0.004, 0.03, False)
    for w in (office_window, gable_vent, office_door):
        kit.skin(shell, "glass_dirty" if w[2] > 0.5 else "soot", front, kit.rect(*w), [], 0.004, 0.03, False)
    for frame, openings_list in ((left, west_windows), (right, east_windows), (back, back_shop + back_wing + [back_vent])):
        for w in openings_list:
            kit.skin(shell, "glass_dirty" if w[2] > 0.5 else "soot", frame, kit.rect(*w), [], 0.004, 0.02, False)
    frame_block(shell, "town_paint_cream", front, -5.35, 1.35, 4.28, 4.92, -0.07, 0.0)
    tk.atlas_quad(shell, "town_signs", [kit.frame_point(front, -5.3, 4.3, 0.071), kit.frame_point(front, 1.3, 4.3, 0.071), kit.frame_point(front, 1.3, 4.9, 0.071), kit.frame_point(front, -5.3, 4.9, 0.071)], tp.sg("garage_fascia"))
    for side in (-1.0, 1.0):
        tk.roof_slab_y(shell, gable, side, gable.x0, gable.x1, "corrugated_rusty", 0.06)
    x1 = hx + 0.3
    top = [V(shop_x[1], -hy - 0.25, lean(shop_x[1]) + 0.02), V(x1, -hy - 0.25, lean(x1) + 0.02), V(x1, hy + 0.25, lean(x1) + 0.02), V(shop_x[1], hy + 0.25, lean(shop_x[1]) + 0.02)]
    emit(shell, kit.Geo(top, [kit.orient((0, 1, 2, 3), top, up), kit.orient((0, 1, 2, 3), top, -up)]), "corrugated_rusty", None, "world")
    return b
