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
hx = 10.0
hy = 7.0
fz = -0.08
wall_t = 0.3
kx0 = 2.4
kx1 = 9.6
khx = (kx1 - kx0) * 0.5
khy = 3.4
kcx = (kx0 + kx1) * 0.5
ix0 = kx0 + wall_t
ix1 = kx1 - wall_t
iy0 = -khy + wall_t
iy1 = khy - wall_t
ceiling = 3.0
roof_top = 3.3
parapet = 3.75
plinth_top = 0.42
stone = "granite_rubble"
render = "render_white"
trim = "town_paint_green"
shop_door = (-3.0, -2.0, 0.0, 2.2)
shop_window = (-1.4, 2.9, 0.55, 2.45)
side_window = (0.9, 2.7, 0.9, 2.3)
store_window = (-2.4, -1.5, 1.2, 2.2)
office_window = (1.0, 1.8, 1.2, 2.2)
back_door = (1.9, 2.8, 0.0, 2.1)
wc_window = (-3.05, -2.55, 1.6, 2.2)
split_y = (0.6, 0.72)
store_door = (3.3, 4.2, 0.0, 2.1)
office_door = (8.2, 9.1, 0.0, 2.1)
office_x = (6.0, 6.12)
canopy = (-9.4, 0.4, -5.4, 1.0)
deck_low = 4.4
deck_top = 4.62
posts = [(-7.5, -3.75), (-7.5, -0.65), (-1.5, -3.75), (-1.5, -0.65)]
islands = [-7.5, -1.5]
island_y = (-4.1, -0.3)
island_top = 0.1
pumps = [(-7.5, -2.85), (-7.5, -1.55), (-1.5, -2.85), (-1.5, -1.55)]


def kframe(side):
    return kit.shifted(kit.facade(side, khx, khy), V(kcx, 0.0, 0.0))


def world_front(o):
    return (o[0] + kcx, o[1] + kcx, o[2], o[3])


def world_back(o):
    return (kcx - o[1], kcx - o[0], o[2], o[3])


def world_left(o):
    return (-o[1], -o[0], o[2], o[3])


def plinth(shell, frame, a0, a1, gaps):
    edges = [a0]
    for g0, g1 in sorted(gaps):
        edges += [g0 - 0.02, g1 + 0.02]
    edges.append(a1)
    for s0, s1 in zip(edges[0::2], edges[1::2]):
        if s1 - s0 > 0.05:
            frame_block(shell, "town_paint_black", frame, s0, s1, -0.45, plinth_top, -0.025, 0.0)


def forecourt(b, parts, rng):
    floor = parts["floors"]
    block(floor, "concrete", V(-hx, -hy, -1.2), V(hx, hy, fz - 0.3), 0.0, "world")
    block(floor, "soot", V(-hx + 0.01, -hy + 0.01, fz - 0.3), V(hx - 0.01, hy - 0.01, fz - 0.02), 0.0, "world")
    xs = [-hx + 4.0 * k for k in range(6)]
    ys = [-hy + 3.5 * k for k in range(5)]
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for y0, y1 in zip(ys[:-1], ys[1:]):
            if x0 >= kx0 and x1 <= kx1 + 0.5 and y0 >= -khy - 0.2 and y1 <= khy + 0.2:
                continue
            drop = rng.uniform(0.0, 0.012) if rng.random() < 0.3 else 0.0
            block(floor, "concrete", V(x0 + 0.012, y0 + 0.012, fz - 0.3), V(x1 - 0.012, y1 - 0.012, fz - drop), 0.0, "world")
    tk.col(b, "concrete", "forecourt", -hx, hx, -hy, hy, -1.2, fz)
    for center, size in ((V(-7.5, -2.2, fz), 0.5), (V(-1.5, -2.2, fz), 0.45), (V(-4.6, -1.0, fz), 0.6), (V(-4.2, -3.6, fz), 0.35), (V(5.0, -5.2, fz), 0.4)):
        shape = kit.blob(0.0, 0.0, size, size * rng.uniform(0.5, 0.9), rng, 12, 0.3)
        emit(floor, kit.geo_slab(center + V(0.0, 0.0, 0.003), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), shape, [], 0.0, 0.001, False), "soot", None, "world")
    for x in (-6.0, -4.5, -3.0):
        emit(floor, kit.geo_lathe([(0.0, 0.0), (0.3, 0.0), (0.3, 0.012), (0.0, 0.018)], 12), "rusty_metal", kit.Matrix.Translation(V(x, -6.1, fz)), "given", True)
    for center, size in ((V(-8.6, 5.6, fz), 1.3), (V(-3.0, 6.2, fz), 1.0), (V(1.8, 6.3, fz), 0.9), (V(9.0, 6.1, fz), 1.1), (V(-9.3, 0.8, fz), 0.8), (V(9.2, -5.9, fz), 0.9), (V(-9.0, -5.2, fz), 0.7), (V(4.6, -6.4, fz), 0.6), (V(-5.4, 2.6, fz), 0.9)):
        shape = kit.blob(0.0, 0.0, size, size * rng.uniform(0.4, 0.8), rng, 14, 0.4)
        emit(floor, kit.geo_slab(center + V(0.0, 0.0, 0.002), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), shape, [], 0.0, 0.004, False), "dirt_debris", None, "world")
    for start, end in ((V(-8.2, -1.2, fz), V(-6.4, -0.1, fz)), (V(3.0, -6.6, fz), V(4.1, -4.4, fz)), (V(-2.8, 4.2, fz), V(-0.6, 5.5, fz))):
        points = [start.lerp(end, t / 5.0) + V(rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), 0.002) for t in range(6)]
        for p, q in zip(points[:-1], points[1:]):
            kit.member(floor, "soot", p, q, 0.015, 0.002, up, 0.0, "box")
    plants = parts["plants"]
    for x in (-6.0, -2.0, 2.0):
        tk.weeds_line(plants, V(x, -hy + 0.2, fz), V(x, -hy + 3.4, fz), rng, 3, (0.08, 0.25))
    for y in (-3.5, 3.5):
        tk.weeds_line(plants, V(-hx + 0.2, y, fz), V(1.5, y, fz), rng, 4, (0.08, 0.25))
    tk.weeds_line(plants, V(-hx + 0.2, hy - 0.15, fz), V(hx - 0.2, hy - 0.15, fz), rng, 8)
    tk.weeds_line(plants, V(-hx + 0.15, -hy + 0.2, fz), V(-hx + 0.15, hy - 0.2, fz), rng, 6)
    tk.weeds_line(plants, V(hx - 0.15, -hy + 0.2, fz), V(hx - 0.15, hy - 0.2, fz), rng, 6)


def islands_and_pumps(b, parts, rng):
    floor = parts["floors"]
    furniture = parts["furniture"]
    for x in islands:
        block(floor, "concrete", V(x - 0.4, island_y[0], fz - 0.05), V(x + 0.4, island_y[1], island_top), 0.006)
        for y0, y1 in ((island_y[0] - 0.01, island_y[0] + 0.25), (island_y[1] - 0.25, island_y[1] + 0.01)):
            block(floor, "town_paint_cream", V(x - 0.41, y0, fz + 0.03), V(x + 0.41, y1, island_top - 0.02), 0.0, "board")
        tk.col(b, "concrete", "island", x - 0.4, x + 0.4, island_y[0], island_y[1], fz, island_top)
    for index, (x, y) in enumerate(pumps):
        tp.petrol_pump(b, furniture, V(x, y, island_top), math.pi * 0.5, rng, ("red", "red", "green", "red")[index])
    tp.oil_rack(b, furniture, parts["clutter"], V(kx0 - 0.15, 0.0, fz), -math.pi * 0.5, rng)
    tp.air_tower(b, furniture, V(1.3, -4.6, fz), 0.0, rng)


def canopy_roof(b, parts, rng):
    roof = parts["roof"]
    cx0, cx1, cy0, cy1 = canopy
    block(roof, "concrete", V(cx0, cy0, deck_low), V(cx1, cy1, deck_top), 0.0, "world")
    block(roof, "soot", V(cx0 + 0.02, cy0 + 0.02, deck_top), V(cx1 - 0.02, cy1 - 0.02, deck_top + 0.012), 0.0, "world")
    for x0, x1, y0, y1 in ((cx0 - 0.06, cx1 + 0.06, cy0 - 0.06, cy0), (cx0 - 0.06, cx1 + 0.06, cy1, cy1 + 0.06), (cx0 - 0.06, cx0, cy0, cy1), (cx1, cx1 + 0.06, cy0, cy1)):
        block(roof, "town_paint_cream", V(x0, y0, deck_low - 0.15), V(x1, y1, deck_top + 0.23), 0.0, "board")
        tk.col(b, "metal", "fascia", x0, x1, y0, y1, deck_low - 0.15, deck_top + 0.23)
    for x0, x1, y0, y1 in ((cx0 - 0.075, cx1 + 0.075, cy0 - 0.075, cy0 - 0.06), (cx0 - 0.075, cx1 + 0.075, cy1 + 0.06, cy1 + 0.075), (cx0 - 0.075, cx0 - 0.06, cy0 - 0.06, cy1 + 0.06), (cx1 + 0.06, cx1 + 0.075, cy0 - 0.06, cy1 + 0.06)):
        block(roof, "town_paint_red", V(x0, y0, deck_low - 0.15), V(x1, y1, deck_low - 0.05), 0.0, "board")
    tk.col(b, "concrete", "canopy", cx0, cx1, cy0, cy1, deck_low, deck_top)
    middle = (cx0 + cx1) * 0.5
    tk.atlas_quad(roof, "town_signs", [V(middle - 2.5, cy0 - 0.062, 4.36), V(middle + 2.5, cy0 - 0.062, 4.36), V(middle + 2.5, cy0 - 0.062, 4.83), V(middle - 2.5, cy0 - 0.062, 4.83)], tp.sg("fuel_fascia"))
    tk.atlas_quad(roof, "town_signs", [V(middle + 2.5, cy1 + 0.062, 4.36), V(middle - 2.5, cy1 + 0.062, 4.36), V(middle - 2.5, cy1 + 0.062, 4.83), V(middle + 2.5, cy1 + 0.062, 4.83)], tp.sg("fuel_fascia"))
    for x, y in posts:
        base = kit.turned(V(x, y, island_top), 0.0)
        local_block(roof, "rusty_metal", base, -0.17, 0.17, -0.17, 0.17, 0.0, 0.025)
        tp.painted_long(roof, "cream", base, -0.09, 0.09, -0.09, 0.09, 0.025, deck_low - island_top, 0.75)
        local_block(roof, "rusty_metal", base, -0.2, 0.2, -0.2, 0.2, deck_low - island_top - 0.03, deck_low - island_top)
        tk.col(b, "metal", "post", x - 0.1, x + 0.1, y - 0.1, y + 0.1, island_top, deck_low)
    for x, y in ((-4.5, -3.75), (-4.5, -0.65), (-8.6, -2.2), (-0.4, -2.2)):
        tp.cage_lamp(b, roof, V(x, y, deck_low), rng, "cold")


def pole_sign(b, parts, rng):
    roof = parts["roof"]
    x = -9.25
    y = -6.35
    top = 5.05
    base = kit.turned(V(x, y, fz), 0.0)
    local_block(roof, "concrete", base, -0.26, 0.26, -0.26, 0.26, -0.03, 0.12, 0.006)
    tp.painted_long(roof, "red", base, -0.07, 0.07, -0.07, 0.07, 0.12, top - 0.95 - fz, 0.8)
    local_block(roof, "town_paint_black", kit.turned(V(x, y, top - 0.95), 0.0), -0.73, 0.73, -0.07, 0.07, 0.0, 0.95)
    for side in (-1.0, 1.0):
        tk.atlas_panel(roof, "town_signs", V(x, y + side * 0.07, top - 0.475), V(0.0, side, 0.0), 1.36, 0.88, tp.sg("fuel_globe"), 0.0, 0.002)
    local_block(roof, "town_paint_black", kit.turned(V(x, y, top), 0.0), -0.78, 0.78, -0.1, 0.1, 0.0, 0.05)
    tk.col(b, "metal", "sign", x - 0.08, x + 0.08, y - 0.08, y + 0.08, fz, top)
    tk.col(b, "metal", "sign", x - 0.73, x + 0.73, y - 0.07, y + 0.07, top - 0.95, top)
    lamp = V(x + 0.45, y - 0.42, top + 0.02)
    emit(roof, kit.geo_tube([V(x + 0.45, y - 0.08, top + 0.04), V(x + 0.45, y - 0.32, top + 0.16), lamp], kit.circle(0.012, 5), True), "town_paint_black", None, "given", True)
    geo = tk.region_geo(kit.geo_lathe([(0.02, 0.05), (0.04, 0.04), (0.11, -0.04), (0.1, -0.045), (0.035, 0.035)], 10), "town_metal", "green", 0.4)
    emit(roof, geo, "town_metal", kit.Matrix.Translation(lamp) @ kit.Matrix.Rotation(0.6, 4, 'X'), "texture", True)
    b.light("warm", lamp + V(0.0, 0.05, -0.12))


def shop_front(b, parts, rng):
    joinery = parts["joinery"]
    front = kframe("front")
    a0, a1, z0, z1 = shop_window
    bays = 4
    width = (a1 - a0) / bays
    transom = z1 - 0.42
    frame_block(joinery, trim, front, a0 - 0.04, a1 + 0.04, z0 - 0.06, z0, -0.05, 0.16, 0.0, "board")
    frame_block(joinery, trim, front, a0, a1, z1 - 0.07, z1, 0.02, 0.14, 0.0, "board")
    frame_block(joinery, trim, front, a0, a1, transom - 0.035, transom + 0.035, 0.02, 0.14, 0.0, "board")
    for k in range(bays + 1):
        a = a0 + width * k
        frame_block(joinery, trim, front, max(a0, a - 0.035), min(a1, a + 0.035), z0, z1 - 0.07, 0.02, 0.14, 0.0, "board")
    matrix = kit.frame_matrix(front)
    lows = ["shard", "missing", "whole", "shard"]
    rng.shuffle(lows)
    for k in range(bays):
        p0 = a0 + width * k + 0.035
        p1 = a0 + width * (k + 1) - 0.035
        kit.pane(joinery, matrix, p0, p1, z0, transom - 0.035, 0.08, lows[k], rng)
        kit.pane(joinery, matrix, p0, p1, transom + 0.035, z1 - 0.07, 0.08, rng.choice(("whole", "shard", "missing")), rng)
        if lows[k] == "missing":
            tk.boards_over(joinery, front, (a0 + width * k, a0 + width * (k + 1), z0, transom), rng, "timber_planks_weathered", 4, 0.025, 0.3)
    frame_block(joinery, trim, front, a0 + 0.05, a1 - 0.05, z0 - 0.03, z0, 0.16, 0.5, 0.0, "board")
    tk.opening_block(b, "glass", "window", front, shop_window, wall_t)
    a0, a1, z0, z1 = shop_door
    tk.door_unit(joinery, front, a0, a1, 0.0, z1, wall_t, trim, rng, "low", 78.0, "panel", True, 0.0, 0.06, 1.5, trim)
    tk.atlas_panel(joinery, "town_signs", kit.frame_point(front, shop_window[0] + 0.45, 1.15, -0.11), V(0.0, -1.0, 0.0), 0.3, 0.1, tp.sg("open_sign"), 0.05, 0.0)
    block(parts["shell"], "concrete", V(a0 + kcx - 0.15, -khy - 0.45, fz - 0.2), V(a1 + kcx + 0.15, -khy + 0.02, -0.02), 0.01)
    tk.col(b, "concrete", "step", a0 + kcx - 0.15, a1 + kcx + 0.15, -khy - 0.45, -khy, fz, -0.02)


def kiosk_shell(b, parts, rng):
    shell = parts["shell"]
    joinery = parts["joinery"]
    front = kframe("front")
    back = kframe("back")
    left = kframe("left")
    right = kframe("right")
    walls = ((front, -khx, khx, [shop_door, shop_window]), (back, -khx, khx, [back_door, wc_window]), (left, -iy1, iy1, [side_window, store_window]), (right, -iy1, iy1, [office_window]))
    for frame, a0, a1, holes in walls:
        cut = [kit.rect(o[0], o[1], -0.05, o[3]) if o[2] <= 0.01 else kit.rect(*o) for o in holes]
        kit.wall(shell, stone, frame, kit.rect(a0, a1, -1.2, parapet), cut, wall_t)
        kit.wall_boxes(b, "rock", "wall", frame, a0, a1, -1.2, parapet, wall_t, holes)
        reach = khx if frame is front or frame is back else khy
        tk.render_skin(shell, frame, -reach, reach, parapet - 0.07, holes, rng, 3, render, 0.02, 1 if frame is not front else 0, (plinth_top, plinth_top))
        plinth(shell, frame, -reach, reach, [(o[0], o[1]) for o in holes if o[2] <= 0.01])
        frame_block(shell, "concrete", frame, -reach - 0.04, reach + 0.04, parapet, parapet + 0.06, -0.04, wall_t + 0.04)
        inner = reach - wall_t
        frame_block(shell, render, frame, -inner, inner, roof_top, parapet, wall_t, wall_t + 0.015)
    block(shell, "concrete", V(kx0, -khy, ceiling + 0.02), V(kx1, khy, roof_top))
    block(shell, "soot", V(ix0, iy0, roof_top), V(ix1, iy1, roof_top + 0.012), 0.0, "world")
    tk.col(b, "concrete", "roof", ix0, ix1, iy0, iy1, ceiling, roof_top)
    for k in range(2):
        x = ix1 - 0.4 - k * 0.6
        lump(shell, "dirt_debris", V(x, iy1 - 0.3, roof_top), (0.25, 0.15, 0.04), rng, 0.3, 1)
    frame_block(joinery, "town_paint_cream", front, -1.6, 1.6, 2.72, 3.54, -0.06, 0.0, 0.0, "board")
    tk.atlas_panel(joinery, "town_signs", kit.frame_point(front, 0.0, 3.13, 0.061), V(0.0, -1.0, 0.0), 3.1, 0.775, tp.sg("fuel_board"), 0.0, 0.0)
    tp.enamel_sign(shell, kit.frame_point(front, 3.25, 1.7, 0.025), V(0.0, -1.0, 0.0), 0.5, 0.32, "enamel_oil", rng, -0.02)
    tp.enamel_sign(shell, kframe("left")[0] + V(-0.025, 0.4, 1.9), V(-1.0, 0.0, 0.0), 0.6, 0.23, "enamel_smoke", rng, 0.03)
    tk.casement(b, parts, left, side_window, wall_t, rng, "painted_wood_white", 0.08, [0.0, 0.0], 0.2, 0.4, 2, "concrete")
    tk.casement(b, parts, left, store_window, wall_t, rng, "painted_wood_white", 0.08, [0.0, 30.0], 0.3, 0.3, 2, "concrete")
    tk.casement(b, parts, right, office_window, wall_t, rng, "painted_wood_white", 0.08, [0.0, 0.0], 0.3, 0.3, 2, "concrete")
    tk.casement(b, parts, back, wc_window, wall_t, rng, "painted_wood_white", 0.08, [35.0], 0.3, 0.3, 1, "concrete")
    a0, a1, z0, z1 = back_door
    tk.door_unit(joinery, back, a0, a1, 0.0, z1, wall_t, trim, rng, "high", 88.0, "ledged", True, 0.0, 0.06, 2.0, trim)
    x0, x1 = world_back(back_door)[:2]
    block(shell, "concrete", V(x0 - 0.12, khy - 0.02, fz - 0.2), V(x1 + 0.12, khy + 0.4, -0.02), 0.01)
    tk.col(b, "concrete", "step", x0 - 0.12, x1 + 0.12, khy, khy + 0.4, fz, -0.02)
    for x0, x1 in ((world_front(shop_door)[0], world_front(shop_door)[1]),):
        tk.col(b, "concrete", "threshold", x0, x1, -khy, iy0, fz, 0.0)
    tk.col(b, "concrete", "threshold", world_back(back_door)[0], world_back(back_door)[1], iy1, khy, fz, 0.0)
    shop_front(b, parts, rng)


def kiosk_floor(b, parts, rng):
    floor = parts["floors"]
    block(floor, "concrete", V(ix0, iy0, fz - 0.05), V(ix1, iy1, -0.03))
    tk.tile_floor(floor, "town_quarry", ix0, ix1, iy0, split_y[1], 0.0, 0.03)
    tk.tile_floor(floor, "concrete", ix0, office_x[1], split_y[1], iy1, 0.0, 0.03)
    tk.tile_floor(floor, "town_lino", office_x[1], ix1, split_y[1], iy1, 0.0, 0.03)
    for x0, x1 in (world_front(shop_door)[:2], world_back(back_door)[:2]):
        y0, y1 = (-khy, iy0) if x0 == world_front(shop_door)[0] else (iy1, khy)
        block(floor, "concrete", V(x0, y0, -0.05), V(x1, y1, 0.0))
    tk.col(b, "concrete", "ground", ix0, ix1, iy0, iy1, -0.3, 0.0)


def partitions(b, parts, rng):
    joinery = parts["joinery"]
    split = tk.partition(b, parts, V(0.0, split_y[0], 0.0), V(0.0, -1.0, 0.0), ix0, ix1, 0.0, ceiling, split_y[1] - split_y[0], [store_door, office_door], "split")
    tk.door_unit(joinery, split, store_door[0], store_door[1], 0.0, store_door[3], split_y[1] - split_y[0], trim, rng, "low", 95.0, "panel")
    tk.door_unit(joinery, split, office_door[0], office_door[1], 0.0, office_door[3], split_y[1] - split_y[0], trim, rng, "high", 85.0, "panel")
    tk.partition(b, parts, V(office_x[0], 0.0, 0.0), V(-1.0, 0.0, 0.0), -iy1, -split_y[1], 0.0, ceiling, office_x[1] - office_x[0], [], "split")


def finishes(parts, rng):
    tiles = ("tiles", 1.1, "kitchen_tiles", ("plaster", 1))
    plain = ("plaster", 2)
    paper = ("paper", "wallpaper_faded", 1, 1)
    tk.room(parts, rng, ix0, ix1, iy0, split_y[0], 0.0, ceiling, {"front": tiles, "back": tiles, "left": tiles, "right": tiles}, {"front": [world_front(shop_door), world_front(shop_window)], "back": [store_door, office_door], "left": [world_left(side_window)]}, None, None, True, 1, (), None, 4, 0.0)
    tk.room(parts, rng, ix0, office_x[0], split_y[1], iy1, 0.0, ceiling, {"front": plain, "back": plain, "left": plain, "right": plain}, {"front": [store_door], "back": [world_back(back_door)], "left": [world_left(store_window)]}, None, None, True, 1, (), None, 4, 0.0)
    tk.room(parts, rng, office_x[1], ix1, split_y[1], iy1, 0.0, ceiling, {"front": paper, "back": paper, "left": paper, "right": paper}, {"front": [office_door], "back": [world_back(wc_window)], "right": [office_window]}, "painted_wood_white", None, True, 1, (), None, 2, 0.0)


def shop(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.shop_counter(b, furniture, clutter, 7.3, 7.9, -2.3, 0.0, rng, 0.92, "painted_wood_green", "floorboards")
    tp.till(clutter, V(7.62, -1.0, 0.92), math.pi * 0.5, rng)
    b.loot("food", V(7.6, -1.9, 0.92))
    for k in range(3):
        bd.tin(clutter, V(7.5 + rng.uniform(-0.05, 0.1), -0.5 + k * 0.14, 0.92), rng)
    tp.wall_shelves(b, furniture, clutter, V(ix1 - 0.01, -2.9, 0.0), V(ix1 - 0.01, 0.4, 0.0), V(-1.0, 0.0, 0.0), [0.35, 0.85, 1.35, 1.85], rng, ("can", "box", "bottle", "jar", "gap"), 0.34)
    tp.wall_shelves(b, furniture, clutter, V(4.4, split_y[0] - 0.01, 0.0), V(7.1, split_y[0] - 0.01, 0.0), V(0.0, -1.0, 0.0), [0.3, 0.8, 1.3, 1.8], rng, ("can", "can", "box", "jar", "gap"), 0.34)
    tp.chest_freezer(b, furniture, V(ix0 + 0.33, -1.6, 0.0), math.pi * 0.5, rng)
    tp.tier_stand(b, furniture, clutter, V(5.3, -1.5, 0.0), 0.1, rng, 1.2, 0.7)
    tp.chair_light(furniture, V(3.5, -0.2, 0.0), 0.0, rng, "timber_beam", "timber_planks_weathered", True)
    tp.enamel_sign(interior, V(4.3, iy0 + 0.02, 1.7), V(0.0, 1.0, 0.0), 0.4, 0.27, "enamel_tea", rng, 0.03)
    tp.enamel_sign(interior, V(5.75, split_y[0] - 0.02, 2.3), V(0.0, -1.0, 0.0), 0.9, 0.34, "enamel_oil", rng, -0.02)
    tp.wall_sheet(interior, V(ix0 + 0.02, -0.3, 1.6), V(1.0, 0.0, 0.0), "calendar", rng, 1.0, 0.03)
    tp.wall_clock(interior, V(8.6, split_y[0] - 0.03, 2.4), V(0.0, -1.0, 0.0), rng, 0.15)
    for x in (4.6, 7.9):
        tk.pendant(b, interior, V(x, -1.3, ceiling), rng, "town_metal", 0.5, "warm", 8)
    tp.papers(parts["debris"], 2.9, 7.1, -2.9, 0.3, 0.0, 7, rng, ("newspaper", "notice", "card", "letter"))
    tp.debris_field(parts, 2.9, 9.1, -2.9, 0.3, 0.0, rng, 6, 10, 0, 4)


def store(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.wall_shelves(b, furniture, clutter, V(4.3, iy1 - 0.01, 0.0), V(5.9, iy1 - 0.01, 0.0), V(0.0, -1.0, 0.0), [0.25, 0.75, 1.25, 1.75], rng, ("box", "can", "jar", "box", "gap"), 0.4)
    tp.crate_light(clutter, V(3.05, 1.05, 0.0), (0.6, 0.5, 0.45), 0.1, rng)
    tp.crate_light(clutter, V(3.05, 1.7, 0.0), (0.55, 0.45, 0.4), -0.15, rng)
    tk.col(b, "wood", "crates", ix0, 3.4, 0.75, 2.0, 0.0, 0.45)
    tp.bottle_crate(clutter, V(3.05, 1.05, 0.45), 0.3, rng, "cider")
    tp.sack_row(clutter, V(4.5, split_y[1] + 0.3, 0.0), V(1.0, 0.0, 0.0), 3, rng)
    tk.col(b, "fabric", "sacks", 4.3, 5.7, split_y[1], split_y[1] + 0.6, 0.0, 0.5)
    b.loot("food", V(5.05, 2.4, 0.0))
    b.loot("box", V(5.55, 1.6, 0.0))
    tp.bulb(b, interior, V(4.4, 1.9, ceiling), rng, 0.45, "warm")
    tp.papers(parts["debris"], 2.9, 5.8, 0.9, 2.9, 0.0, 3, rng, ("newspaper", "card"))
    tp.debris_field(parts, 2.9, 5.8, 0.9, 2.9, 0.0, rng, 4, 0, 0, 3)


def office(b, parts, rng):
    furniture = parts["furniture"]
    clutter = parts["clutter"]
    interior = parts["interior"]
    tp.cubicles(b, furniture, 8.0, ix1, iy1, 2.0, 0.0, 1, rng, trim, (True, False))
    tp.desk_light(b, furniture, clutter, V(office_x[1] + 0.36, 1.55, 0.0), math.pi * 0.5, rng, 1.1, 0.68, 0.76, "timber_beam", "floorboards", ("papers", "phone", "files"))
    tp.chair_light(furniture, V(7.05, 1.5, 0.0), tk.facing(V(7.05, 1.5, 0.0), V(6.4, 1.5, 0.0)), rng)
    tp.safe_light(b, furniture, V(office_x[1] + 0.31, 2.78, 0.0), math.pi * 0.5, rng, 1.1)
    b.loot("box", V(7.45, 2.65, 0.0))
    tp.wall_sheet(interior, V(7.2, split_y[1] + 0.02, 1.6), V(0.0, 1.0, 0.0), "calendar", rng, 1.0, -0.03)
    tp.pigeonholes(interior, clutter, V(office_x[1] + 0.02, 1.55, 1.75), V(1.0, 0.0, 0.0), 3, 2, rng)
    tp.bulb(b, interior, V(7.4, 1.4, ceiling), rng, 0.4, "warm")
    tp.papers(parts["debris"], 6.3, 8.0, 0.9, 1.9, 0.0, 4, rng, ("letter", "envelope", "notice"))


def yard(b, parts, rng):
    clutter = parts["clutter"]
    furniture = parts["furniture"]
    plants = parts["plants"]
    tp.vintage_car(b, furniture, V(-4.4, -2.0, fz), math.pi * 0.5, rng, "green")
    tp.vintage_car(b, furniture, V(-6.6, 4.7, fz), 0.25, rng, "red", 3.6, 1.36, False)
    for position, region, tipped in ((V(8.7, 4.3, fz), "red", False), (V(9.3, 4.9, fz), "green", False), (V(8.2, 5.3, fz), "blue", True)):
        tp.oil_drum(b, clutter, position, rng, region, tipped)
    tp.tyre_stack(b, clutter, V(1.0, 4.6, fz), rng, 4)
    tp.tyre_stack(b, clutter, V(1.75, 5.3, fz), rng, 3)
    for k in range(3):
        tp.tyre_light(clutter, kit.Matrix.Translation(V(0.2 + k * 0.5, 6.2, fz + 0.09)) @ kit.Matrix.Rotation(rng.uniform(0.0, tau), 4, 'Z') @ kit.Matrix.Rotation(rng.uniform(-0.2, 0.2), 4, 'X'), rng)
    tk.col(b, "fabric", "tyres", -0.15, 1.6, 5.85, 6.55, fz, fz + 0.2)
    bd.dustbin(clutter, V(5.0, 4.0, fz), rng)
    tk.col(b, "metal", "bin", 4.75, 5.25, 3.75, 4.25, fz, fz + 0.75)
    for position in (V(6.5, 3.75, fz), V(6.8, 3.8, fz)):
        tp.gas_cylinder(clutter, position, rng, 1.2, 0.12, "town_metal", "cream")
    tk.col(b, "metal", "cylinders", 6.3, 7.0, 3.55, 4.0, fz, fz + 1.3)
    b.loot("toolbox", V(1.9, 3.0, fz))
    tk.ivy_light(plants, V(kx1 + 0.02, 2.0, fz), V(1.0, 0.0, 0.0), rng, 2.4, 0.9, 3, 8.0)
    tk.ivy_light(plants, V(4.0, khy + 0.02, fz), V(0.0, 1.0, 0.0), rng, 1.6, 0.6, 2, 8.0)
    tk.weeds_line(plants, V(kx0 + 0.3, khy + 0.12, fz), V(kx1 - 0.3, khy + 0.12, fz), rng, 5)
    tk.weeds_line(plants, V(kx1 + 0.12, -khy + 0.3, fz), V(kx1 + 0.12, khy - 0.3, fz), rng, 4)
    tk.weeds_line(plants, V(kx0 - 0.12, 1.0, fz), V(kx0 - 0.12, khy - 0.3, fz), rng, 3)
    for x0, x1, y0, y1, count in ((-9.5, 2.0, 2.0, 6.8, 8), (2.5, 9.5, 3.8, 6.8, 5)):
        for k in range(count):
            p = V(rng.uniform(x0, x1), rng.uniform(y0, y1), fz)
            kit.grass_tuft(plants, p, rng, (0.15, 0.5), (5, 10), 0.08)
    tp.papers(parts["debris"], -9.0, 9.0, -6.6, -4.0, fz, 8, rng, ("newspaper", "notice", "card", "letter"))
    tp.debris_field(parts, -9.5, 2.0, -6.5, 6.5, fz, rng, 0, 6, 0, 16)
    tk.chips(parts["debris"], "concrete", -9.0, 1.5, -5.0, 0.5, fz, 10, rng, (0.05, 0.14), (0.01, 0.025))


def fuel():
    b = kit.Build("fuel", 1801)
    rng = b.rng
    parts = {}
    for key, sharp in (("shell", 30.0), ("roof", 50.0), ("joinery", 30.0), ("floors", 30.0), ("interior", 40.0), ("furniture", 40.0), ("clutter", 45.0), ("debris", 40.0), ("plants", 70.0)):
        parts[key] = b.part(key, sharp)
    forecourt(b, parts, rng)
    islands_and_pumps(b, parts, rng)
    canopy_roof(b, parts, rng)
    pole_sign(b, parts, rng)
    kiosk_shell(b, parts, rng)
    kiosk_floor(b, parts, rng)
    partitions(b, parts, rng)
    finishes(parts, rng)
    shop(b, parts, rng)
    store(b, parts, rng)
    office(b, parts, rng)
    yard(b, parts, rng)
    return b


def fuel_far():
    b = kit.Build("fuel_far", 1802)
    shell = b.part("shell", 30.0)
    block(shell, "concrete", V(-hx, -hy, -1.2), V(hx, hy, fz), 0.0, "world")
    for side in ("front", "back", "left", "right"):
        frame = kframe(side)
        reach = khx if side in ("front", "back") else khy
        kit.wall(shell, stone, frame, kit.rect(-reach, reach, fz - 0.1, parapet + 0.06), [], wall_t)
        kit.skin(shell, render, frame, kit.rect(-reach, reach, plinth_top, parapet), [], 0.02, 0.0, False)
        frame_block(shell, "town_paint_black", frame, -reach, reach, fz, plinth_top, -0.025, 0.0)
        frame_block(shell, render, frame, -reach + wall_t, reach - wall_t, roof_top, parapet, wall_t, wall_t + 0.015)
    holes = {"front": [shop_door, shop_window], "back": [back_door, wc_window], "left": [side_window, store_window], "right": [office_window]}
    for side, openings_list in holes.items():
        frame = kframe(side)
        for o in openings_list:
            kit.skin(shell, "glass_dirty" if o[2] > 0.3 else "soot", frame, kit.rect(*o), [], 0.004, 0.03, False)
    block(shell, "soot", V(kx0 + 0.3, -khy + 0.3, roof_top), V(kx1 - 0.3, khy - 0.3, roof_top + 0.02), 0.0, "world")
    frame_block(shell, "town_paint_cream", kframe("front"), -1.6, 1.6, 2.72, 3.54, -0.07, 0.0)
    tk.atlas_panel(shell, "town_signs", kit.frame_point(kframe("front"), 0.0, 3.13, 0.071), V(0.0, -1.0, 0.0), 3.1, 0.775, tp.sg("fuel_board"), 0.0, 0.0)
    cx0, cx1, cy0, cy1 = canopy
    block(shell, "town_paint_cream", V(cx0 - 0.06, cy0 - 0.06, deck_low - 0.15), V(cx1 + 0.06, cy1 + 0.06, deck_top + 0.23), 0.0, "board")
    block(shell, "soot", V(cx0 + 0.02, cy0 + 0.02, deck_top + 0.23), V(cx1 - 0.02, cy1 - 0.02, deck_top + 0.24), 0.0, "world")
    middle = (cx0 + cx1) * 0.5
    tk.atlas_quad(shell, "town_signs", [V(middle - 2.5, cy0 - 0.072, 4.36), V(middle + 2.5, cy0 - 0.072, 4.36), V(middle + 2.5, cy0 - 0.072, 4.83), V(middle - 2.5, cy0 - 0.072, 4.83)], tp.sg("fuel_fascia"))
    tk.atlas_quad(shell, "town_signs", [V(middle + 2.5, cy1 + 0.072, 4.36), V(middle - 2.5, cy1 + 0.072, 4.36), V(middle - 2.5, cy1 + 0.072, 4.83), V(middle + 2.5, cy1 + 0.072, 4.83)], tp.sg("fuel_fascia"))
    for x0, x1, y0, y1 in ((cx0 - 0.08, cx1 + 0.08, cy0 - 0.08, cy0 - 0.06), (cx0 - 0.08, cx1 + 0.08, cy1 + 0.06, cy1 + 0.08)):
        block(shell, "town_paint_red", V(x0, y0, deck_low - 0.15), V(x1, y1, deck_low - 0.05), 0.0, "board")
    for x, y in posts:
        block(shell, "town_paint_cream", V(x - 0.09, y - 0.09, fz), V(x + 0.09, y + 0.09, deck_low))
    for x, y in pumps:
        block(shell, "town_paint_red", V(x - 0.2, y - 0.24, fz), V(x + 0.2, y + 0.24, 2.1))
    for x in islands:
        block(shell, "concrete", V(x - 0.4, island_y[0], fz), V(x + 0.4, island_y[1], island_top))
    block(shell, "town_paint_black", V(-9.98, -6.42, 4.1), V(-8.52, -6.28, 5.05))
    block(shell, "town_paint_red", V(-9.32, -6.42, fz), V(-9.18, -6.28, 4.1))
    for side in (-1.0, 1.0):
        tk.atlas_panel(shell, "town_signs", V(-9.25, -6.35 + side * 0.071, 4.575), V(0.0, side, 0.0), 1.36, 0.88, tp.sg("fuel_globe"), 0.0, 0.002)
    return b
