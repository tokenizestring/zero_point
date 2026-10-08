import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import town_kit as tk
import town_props as tp
import oilrig_library as lib
import oilrig_kit as ok
from buildkit import V, Geo, emit
from oilrig_kit import box, col, tube, up

z = ok.main
frame_paint = "rig_paint_white"
void = (6.7, 13.6, -19.6, -17.2)
containers = [(15.0, -19.4, True, "rig_paint_orange"), (15.0, -16.6, True, "rig_paint_white")]
laydown = (22.0, 24.6, -19.2, -15.4)
dropped = (-16.8, -10.4)
scaffold = (-16.9, -14.7, 11.5, 14.0)


def deck(b, parts, rng):
    structure = parts["structure"]
    ok.plate_floor(b, parts["deck"], -ok.deck_x, ok.deck_x, -ok.deck_y, ok.deck_y, z, "rig_deck_green", [void], 0.03, "metal", "deck")
    for sy in (-1.0, 1.0):
        ok.ibeam(structure, frame_paint, V(-ok.deck_x, sy * ok.leg_y, z - 1.0), V(ok.deck_x, sy * ok.leg_y, z - 1.0), 2.0, 0.6, None, 0.025, 0.04, 1.0)
    for sx in (-1.0, 1.0):
        ok.ibeam(structure, frame_paint, V(sx * ok.leg_x, -ok.deck_y, z - 1.0), V(sx * ok.leg_x, ok.deck_y, z - 1.0), 2.0, 0.6, None, 0.025, 0.04, 1.0)
        ok.ibeam(structure, frame_paint, V(sx * ok.deck_x, -ok.deck_y, z - 0.6), V(sx * ok.deck_x, ok.deck_y, z - 0.6), 1.2, 0.4)
    for sy in (-1.0, 1.0):
        ok.ibeam(structure, frame_paint, V(-ok.deck_x, sy * ok.deck_y, z - 0.6), V(ok.deck_x, sy * ok.deck_y, z - 0.6), 1.2, 0.4)
    y = -17.5
    while y < 18.0:
        if abs(abs(y) - ok.leg_y) > 0.8:
            pieces = [(-ok.deck_x, ok.deck_x)]
            if void[2] < y < void[3]:
                pieces = [(-ok.deck_x, void[0] - 0.1), (void[1] + 0.1, ok.deck_x)]
            for a, c in pieces:
                ok.ibeam(structure, frame_paint, V(a, y, z - 0.42), V(c, y, z - 0.42), 0.8, 0.25)
        y += 2.5
    for x0, x1 in ((-ok.deck_x, ok.deck_x),):
        for yy in (-ok.deck_y, ok.deck_y):
            box(structure, "rig_paint_yellow", x0, x1, yy - 0.02 if yy > 0 else yy, yy if yy > 0 else yy + 0.02, z, z + 0.15, "box", 0.0, ok.fine)
    for xx in (-ok.deck_x, ok.deck_x):
        box(structure, "rig_paint_yellow", xx - 0.02 if xx > 0 else xx, xx if xx > 0 else xx + 0.02, -ok.deck_y, ok.deck_y, z, z + 0.15, "box", 0.0, ok.fine)


def railings(b, parts, rng):
    rails = parts["rails"]
    e = 0.1
    x0, x1, y0, y1 = -ok.deck_x + e, ok.deck_x - e, -ok.deck_y + e, ok.deck_y - e
    fy0 = ok.flare_root[1] - 0.6
    fy1 = ok.flare_root[1] + 0.6
    ok.railing(b, rails, [(x0, fy0), (x0, y0), (dropped[0], y0)], z, rng, 1.1, "rig_paint_yellow", True, False, "edge", 0.0, 0.12)
    ok.railing(b, rails, [(dropped[1], y0), (x1, y0), (x1, ok.quarters[2])], z, rng, 1.1, "rig_paint_yellow", True, False, "edge", 0.0, 0.12)
    ok.railing(b, rails, [(x1, ok.quarters[3]), (x1, y1), (ok.davits[1] + 1.0, y1)], z, rng, 1.1, "rig_paint_yellow", True, False, "edge", 0.0, 0.12)
    ok.railing(b, rails, [(ok.davits[1] - 1.0, y1), (ok.davits[0] + 1.0, y1)], z, rng, 1.1, "rig_paint_yellow", True, False, "edge")
    ok.railing(b, rails, [(ok.davits[0] - 1.0, y1), (x0, y1), (x0, fy1)], z, rng, 1.1, "rig_paint_yellow", True, False, "edge", 0.0, 0.08)
    for dx in ok.davits:
        a = V(dx - 1.0, y1, z + 0.9)
        c = V(dx + 1.0, y1, z + 0.9)
        rk.chain(parts["fittings"], "rig_rust", ok.catenary(a, c, 0.22, 6), 0.13, 0.06, 0.01, rng, 4, 2)
        for px in (dx - 1.0, dx + 1.0):
            tube(rails, "rig_paint_yellow", V(px, y1, z), V(px, y1, z + 1.15), 0.03, 6, True, ok.fine)
        col(b, "metal", "gate", dx - 1.0, dx + 1.0, y1 - 0.05, y1 + 0.05, z, z + 1.1)
    vx0, vx1, vy0, vy1 = void
    ok.railing(b, rails, [(vx0, vy1), (vx1, vy1), (vx1, vy0)], z, rng, 1.1, "rig_paint_yellow", True, False, "void")
    ok.railing(b, rails, [(vx0, vy0), (vx0, ok.cellar_stair_split)], z, rng, 1.1, "rig_paint_yellow", True, False, "void")


def module(b, parts, rect, height, rng, tag, door=None, blast=None):
    x0, x1, y0, y1 = rect
    shell = parts["shell"]
    t = 0.12
    walls = [("y0", (x0, y0), (x1, y0), V(0.0, -1.0, 0.0)), ("x1", (x1, y0), (x1, y1), V(1.0, 0.0, 0.0)), ("y1", (x1, y1), (x0, y1), V(0.0, 1.0, 0.0)), ("x0", (x0, y1), (x0, y0), V(-1.0, 0.0, 0.0))]
    for key, (ax, ay), (cx, cy), normal in walls:
        along_x = ay == cy
        lo = min(ax, cx) if along_x else min(ay, cy)
        hi = max(ax, cx) if along_x else max(ay, cy)
        openings = []
        if door and door[0] == key:
            openings.append((door[1], door[2], z, z + 2.2))
        if blast and blast[0] == key:
            openings.append((blast[1], blast[2], z, z + blast[3]))
        cuts = sorted(set([lo, hi] + [p for o in openings for p in (o[0], o[1])]))
        for s, e in zip(cuts[:-1], cuts[1:]):
            mid = (s + e) * 0.5
            covering = [o for o in openings if o[0] <= mid <= o[1]]
            z_low = max([o[3] for o in covering], default=z)
            if z_low >= z + height:
                continue
            if along_x:
                box(shell, "rig_paint_white", s, e, ay - t * 0.5, ay + t * 0.5, z_low, z + height, "box", 0.0, 0.8)
                col(b, "metal", tag, s, e, ay - t * 0.5, ay + t * 0.5, z_low, z + height)
            else:
                box(shell, "rig_paint_white", ax - t * 0.5, ax + t * 0.5, s, e, z_low, z + height, "box", 0.0, 0.8)
                col(b, "metal", tag, ax - t * 0.5, ax + t * 0.5, s, e, z_low, z + height)
        length = hi - lo
        count = int(length / 1.2)
        for k in range(1, count):
            p = lo + length * k / count
            if any(o[0] - 0.2 <= p <= o[1] + 0.2 for o in openings):
                continue
            if along_x:
                box(shell, "rig_paint_white", p - 0.04, p + 0.04, ay + normal.y * 0.06 - 0.03, ay + normal.y * 0.06 + 0.03, z + 0.1, z + height - 0.05, "box", 0.0, 1.6)
            else:
                box(shell, "rig_paint_white", ax + normal.x * 0.06 - 0.03, ax + normal.x * 0.06 + 0.03, p - 0.04, p + 0.04, z + 0.1, z + height - 0.05, "box", 0.0, 1.6)
        for k in range(max(1, count // 3)):
            p = lo + length * (k + 0.5) / max(1, count // 3)
            if any(o[0] - 1.0 <= p <= o[1] + 1.0 for o in openings):
                continue
            center = V(p, ay + normal.y * 0.07, z + height - 1.1) if along_x else V(ax + normal.x * 0.07, p, z + height - 1.1)
            louvre(shell, center, normal, 1.0, 0.8)
    box(shell, "rig_paint_grey", x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, z + height, z + height + 0.2, "box", 0.0, 0.8)
    col(b, "metal", tag + "_roof", x0, x1, y0, y1, z + height, z + height + 0.2)


def louvre(part, center, normal, width, height):
    emit(part, kit.geo_box(0.05, width + 0.08, height + 0.08), "rig_paint_grey", kit.place(center + normal * 0.0, normal, up), "box", False, None, 1.6)
    count = int(height / 0.1)
    for k in range(count):
        zz = center.z - height * 0.5 + (k + 0.5) * height / count
        p = V(center.x, center.y, zz) + normal * 0.05
        emit(part, kit.geo_box(0.08, width, 0.012), "rig_paint_grey", kit.place(p, normal, up) @ kit.Matrix.Rotation(math.radians(35.0), 4, 'Y'), "box", False, None, 2.0)


def compressor(b, parts, rng):
    x0, x1, y0, y1 = ok.compressor
    blast = ("x1", -6.6, -2.2, 3.6)
    module(b, parts, ok.compressor, 5.5, rng, "compressor", ("y0", -21.4, -20.2), blast)
    equipment = parts["equipment"]
    box(equipment, "rig_paint_grey", -23.4, -18.6, -7.6, -1.6, z, z + 0.35)
    ok.lathe(equipment, "rig_paint_grey", V(-21.0, -7.0, z + 1.3), V(0.0, 1.0, 0.0), [(0.0, 0.0), (0.7, 0.0), (0.75, 0.2), (0.75, 2.6), (0.7, 2.8), (0.0, 2.8)], 16)
    box(equipment, "rig_paint_orange", -22.2, -19.8, -3.9, -1.9, z + 0.35, z + 2.2, "box", 0.03)
    tube(equipment, "rig_steel", V(-21.0, -4.2, z + 1.3), V(-21.0, -3.9, z + 1.3), 0.12, 10)
    ok.pipe(equipment, "rig_paint_grey", [V(-21.0, -4.6, z + 2.0), V(-21.0, -4.6, z + 4.6), V(-17.6, -4.6, z + 4.6), V(-16.0, -4.6, z + 4.6)], 0.2, 10, 0.4)
    col(b, "metal", "compressor_skid", -23.4, -18.6, -7.6, -1.6, z, z + 2.2)
    soot = parts["decals"]
    ok.decal(soot, "scorch", V(x1 + 0.08, -4.4, z + 4.2), V(1.0, 0.0, 0.0), 6.0, 4.0)
    ok.decal(soot, "scorch", V(-21.0, y0 - 0.08, z + 3.2), V(0.0, -1.0, 0.0), 3.0, 3.0)
    ok.decal(soot, "scorch", V(-22.4, -4.4, z + 5.4), V(0.0, 0.0, -1.0), 4.0, 4.0)
    debris = parts["clutter"]
    for k in range(7):
        cx = rng.uniform(-16.0, -11.5)
        cy = rng.uniform(-7.5, -1.0)
        yaw = rng.uniform(0.0, math.pi)
        tilt = rng.uniform(-0.4, 0.4)
        matrix = kit.turned(V(cx, cy, z + 0.05 + abs(tilt) * 0.4), yaw, tilt, rng.uniform(-0.2, 0.2))
        emit(debris, kit.geo_box(rng.uniform(1.0, 1.9), rng.uniform(0.6, 1.2), 0.03), "rig_paint_white", matrix, "box", False, None, 0.8)
    for k in range(5):
        p = V(rng.uniform(-17.2, -16.6), rng.uniform(-6.4, -2.4), z + rng.uniform(0.6, 3.4))
        ok.bar(debris, "rig_paint_white", p, V(rng.uniform(-0.3, 0.3), rng.uniform(-1.0, 1.0), rng.uniform(-0.6, 0.6)).normalized(), rng.uniform(0.6, 1.4), 0.05, 0.04, up, 1.6)
    ok.decal(soot, "oil_a", V(-14.0, -4.0, z + 0.005), up, 3.0, 3.0, 0.5)
    b.loot("box", V(-22.8, -0.8, z))
    ok.sign(parts["fittings"], "no_smoking", V(-20.8, y0 - 0.1, z + 1.8), V(0.0, -1.0, 0.0), 0.55, 0.2)


def generator(b, parts, rng):
    x0, x1, y0, y1 = ok.generator
    module(b, parts, ok.generator, 5.0, rng, "generator", ("x1", 3.0, 4.2), None)
    equipment = parts["equipment"]
    roof = z + 5.2
    for cy in (6.0, 11.0):
        base = V(-20.7, cy, roof)
        box(equipment, "rig_paint_grey", base.x - 1.2, base.x + 1.2, cy - 1.0, cy + 1.0, roof, roof + 0.8)
        ok.pipe(equipment, "rig_rust", [base + V(0.0, 0.0, 0.8), base + V(0.0, 0.0, 5.5), base + V(0.0, 0.0, 6.6)], 0.55, 16, 0.6)
        ok.ring(equipment, "rig_rust", base + V(0.0, 0.0, 6.3), up, 0.55, 0.06, 0.2, 16)
        for k in range(3):
            tube(equipment, "rig_paint_grey", base + V(0.0, 0.0, 3.0 + k), base + V(1.6, 0.0, 3.0 + k - 1.2) if k == 0 else base + V(-1.6, 0.0, 3.0 + k - 1.2), 0.03, 5)
        ok.decal(parts["decals"], "scorch", base + V(0.0, -0.58, 5.6), V(0.0, -1.0, 0.0), 1.2, 1.4)
    for cy in (3.5, 13.5):
        louvre_box = V(-22.6, cy, roof)
        box(equipment, "rig_paint_white", louvre_box.x - 1.2, louvre_box.x + 1.2, cy - 0.9, cy + 0.9, roof, roof + 1.6)
        louvre(equipment, louvre_box + V(1.25, 0.0, 0.8), V(1.0, 0.0, 0.0), 1.6, 1.2)
    ok.ladder(parts["rails"], V(x1 + 0.45, 9.0, z), roof, V(-1.0, 0.0, 0.0), 0.45, "rig_paint_yellow", True, 2.4)
    ok.railing(b, parts["rails"], [(x0 + 0.1, y0 + 0.1), (x1 - 0.1, y0 + 0.1), (x1 - 0.1, y1 - 0.1), (x0 + 0.1, y1 - 0.1), (x0 + 0.1, y0 + 0.1)], roof, rng, 1.0, "rig_paint_yellow", False, False, "gen_roof")
    box(equipment, "rig_paint_grey", -23.6, -18.2, 5.0, 12.0, z, z + 0.3)
    box(equipment, "rig_paint_orange", -23.2, -19.4, 7.4, 11.4, z + 0.3, z + 2.3, "box", 0.05)
    ok.lathe(equipment, "rig_paint_grey", V(-21.3, 7.4, z + 1.25), V(0.0, -1.0, 0.0), [(0.0, 0.0), (0.85, 0.0), (0.9, 0.1), (0.9, 1.9), (0.8, 2.0), (0.0, 2.0)], 16)
    ok.pipe(equipment, "rig_rust", [V(-21.3, 9.0, z + 2.3), V(-21.3, 9.0, z + 3.6), V(-20.7, 9.6, z + 4.4), V(-20.7, 11.0, z + 4.4), V(-20.7, 11.0, z + 5.3)], 0.25, 10, 0.4)
    col(b, "metal", "genset", -23.6, -18.2, 5.0, 12.0, z, z + 2.3)
    ok.floodlight(b, parts["fittings"], parts["lamps"], V(x1 + 0.3, y0 + 0.4, z + 4.6), V(0.6, -0.6, -0.5), "cold", True, False, rng, V(x1, y0 + 0.4, z + 4.6))
    ok.sign(parts["fittings"], "danger", V(x1 + 0.08, 3.6, z + 2.6), V(1.0, 0.0, 0.0), 1.2, 0.2)


def drill_floor(b, parts, rng):
    x0, x1, y0, y1 = ok.drill
    fz = ok.drill_z
    structure = parts["structure"]
    for cx in (x0, (x0 + x1) * 0.5, x1):
        for cy in (y0, (y0 + y1) * 0.5, y1):
            if cx == (x0 + x1) * 0.5 and cy == (y0 + y1) * 0.5:
                continue
            box(structure, "rig_paint_orange", cx - 0.3, cx + 0.3, cy - 0.3, cy + 0.3, z, fz - 0.4, "box", 0.0, 1.2)
            col(b, "metal", "substructure", cx - 0.3, cx + 0.3, cy - 0.3, cy + 0.3, z, fz - 0.4)
    vx0, vx1 = ok.vdoor[0], ok.vdoor[1]
    shell = parts["shell"]
    door = (2.0, 3.2)
    clad_top = fz - 0.75
    box(shell, "rig_paint_orange", x0 + 0.3, x1 - 0.3, y0 - 0.04, y0 + 0.04, z, clad_top, "box", 0.0, 0.8)
    box(shell, "rig_paint_orange", x0 - 0.04, x0 + 0.04, y0 + 0.3, y1 - 0.3, z, clad_top, "box", 0.0, 0.8)
    box(shell, "rig_paint_orange", x1 - 0.04, x1 + 0.04, y0 + 0.3, door[0], z, clad_top, "box", 0.0, 0.8)
    box(shell, "rig_paint_orange", x1 - 0.04, x1 + 0.04, door[1], y1 - 0.3, z, clad_top, "box", 0.0, 0.8)
    box(shell, "rig_paint_orange", x1 - 0.04, x1 + 0.04, door[0], door[1], z + 2.2, clad_top, "box", 0.0, 0.8)
    col(b, "metal", "substructure_wall", x0, x1, y0 - 0.05, y0 + 0.05, z, fz - 0.4)
    col(b, "metal", "substructure_wall", x0 - 0.05, x0 + 0.05, y0, y1, z, fz - 0.4)
    col(b, "metal", "substructure_wall", x1 - 0.05, x1 + 0.05, y0, door[0], z, fz - 0.4)
    col(b, "metal", "substructure_wall", x1 - 0.05, x1 + 0.05, door[1], y1, z, fz - 0.4)
    col(b, "metal", "substructure_wall", x1 - 0.05, x1 + 0.05, door[0], door[1], z + 2.2, fz - 0.4)
    for k in range(1, 9):
        px = x0 + (x1 - x0) * k / 9.0
        box(shell, "rig_paint_orange", px - 0.05, px + 0.05, y0 - 0.09, y0 - 0.04, z + 0.1, clad_top, "box", 0.0, 1.6)
    for k in range(1, 9):
        py = y0 + (y1 - y0) * k / 9.0
        box(shell, "rig_paint_orange", x0 - 0.09, x0 - 0.04, py - 0.05, py + 0.05, z + 0.1, clad_top, "box", 0.0, 1.6)
    for s, e in ((V(x0, y1, z + 0.3), V(vx0 - 0.3, y1, fz - 0.8)), (V(x1, y1, z + 0.3), V(vx1 + 0.3, y1, fz - 0.8))):
        tube(structure, "rig_paint_orange", s, e, 0.1, 8, True, 1.4)
    for (ax, ay), (cx, cy) in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
        ok.ibeam(structure, "rig_paint_orange", V(ax, ay, fz - 0.4), V(cx, cy, fz - 0.4), 0.7, 0.3)
    inside = parts["equipment"]
    ok.lathe(inside, "rig_paint_orange", V(-6.0, 4.5, z), up, [(0.0, 0.0), (0.9, 0.0), (0.9, 0.4), (0.6, 0.5), (0.6, 3.6), (0.0, 3.6)], 14)
    for k in range(4):
        box(inside, "rig_paint_orange", -6.9, -5.1, 3.6, 5.4, z + 0.6 + k * 0.75, z + 1.15 + k * 0.75, "box", 0.04)
    col(b, "metal", "bop", -6.9, -5.1, 3.6, 5.4, z, fz - 0.45)
    ok.bulkhead_light(b, inside, V(x1 - 0.1, 6.0, z + 2.6), V(-1.0, 0.0, 0.0), "cold", False, True)
    floor = parts["deck"]
    hole = (-6.6, -5.4, 3.9, 5.1)
    outline = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), outline, [[(hole[0], hole[2]), (hole[1], hole[2]), (hole[1], hole[3]), (hole[0], hole[3])]], fz - 0.05, fz)
    emit(floor, geo, "chequer_plate", None, "world")
    tk.floor_cols(b, "metal", "drill_floor", x0, x1, y0, y1, fz - 0.4, fz, [hole])
    rails = parts["rails"]
    sx0, sx1, sy0, sy1 = ok.drill_stair
    ok.railing(b, rails, [(x1 - 0.05, sy0), (x1 - 0.05, y0 + 0.05), (x0 + 0.05, y0 + 0.05), (x0 + 0.05, dog[2])], fz, rng, 1.1, "rig_paint_yellow", True, False, "drill_rail")
    ok.railing(b, rails, [(x0 + 0.05, dog[3]), (x0 + 0.05, y1 - 0.05), (vx0, y1 - 0.05)], fz, rng, 1.1, "rig_paint_yellow", True, False, "drill_rail")
    ok.railing(b, rails, [(vx1, y1 - 0.05), (x1 - 0.05, y1 - 0.05), (x1 - 0.05, sy1)], fz, rng, 1.1, "rig_paint_yellow", True, False, "drill_rail")
    equipment = parts["equipment"]
    ok.lathe(equipment, "rig_paint_grey", V(-6.0, 4.5, fz), up, [(0.62, 0.0), (1.1, 0.0), (1.1, 0.32), (0.62, 0.32), (0.62, 0.0)], 20)
    box(equipment, "rig_paint_grey", -6.45, -5.55, 4.05, 4.95, fz + 0.02, fz + 0.36)
    tube(equipment, "rig_steel", V(-6.0, 4.5, fz - 2.0), V(-6.0, 4.5, fz + 1.3), 0.09, 10)
    ok.lathe(equipment, "rig_steel", V(-6.0, 4.5, fz + 1.3), up, [(0.0, 0.0), (0.13, 0.0), (0.13, 0.35), (0.0, 0.35)], 10)
    col(b, "metal", "rotary", -7.1, -4.9, 3.4, 5.6, fz, fz + 0.32)
    dw = (-7.9, -3.0, 0.2, 1.55)
    box(equipment, "rig_paint_orange", dw[0], dw[1], dw[2], dw[3], fz, fz + 1.2, "box", 0.05)
    ok.lathe(equipment, "rig_paint_grey", V(dw[0] + 0.6, (dw[2] + dw[3]) * 0.5, fz + 1.55), V(1.0, 0.0, 0.0), [(0.0, 0.0), (0.7, 0.0), (0.7, 0.12), (0.5, 0.14), (0.5, 3.6), (0.7, 3.62), (0.7, 3.76), (0.0, 3.76)], 18)
    ok.lathe(equipment, "rig_rust", V(dw[0] + 0.75, (dw[2] + dw[3]) * 0.5, fz + 1.55), V(1.0, 0.0, 0.0), [(0.5, 0.0), (0.58, 0.0), (0.58, 3.45), (0.5, 3.45)], 18)
    col(b, "metal", "drawworks", dw[0], dw[1], dw[2], dw[3], fz, fz + 2.3)
    doghouse(b, parts, rng)
    for k in range(5):
        p = V(-8.8 + k * 0.32, 7.9, fz)
        tube(equipment, "rig_steel", p, p + V(0.15, -0.1, 3.8 - k * 0.2), 0.06, 8)
    ok.floodlight(b, parts["fittings"], parts["lamps"], V(x0 + 0.3, y0 + 0.3, fz + 2.6), V(0.5, 0.5, -0.6), "cold", True, False, rng, V(x0, y0, fz + 2.6))
    ok.floor_decal(parts["decals"], "oil_b", -6.0, 3.0, fz + 0.006, 2.2, 2.2, 0.3)
    ok.floor_decal(parts["decals"], "oil_a", -4.0, 6.0, fz + 0.006, 1.6, 1.6, 1.3)


dog = (-12.8, -10.5, 2.9, 5.7)
dog_door = (3.7, 4.9)


def doghouse(b, parts, rng):
    x0, x1, y0, y1 = dog
    fz = ok.drill_z
    shell = parts["shell"]
    h = 2.6
    t = 0.08
    box(shell, "chequer_plate", x0, x1, y0, y1, fz - 0.06, fz, "world")
    col(b, "metal", "doghouse_floor", x0, x1, y0, y1, fz - 0.3, fz)
    for cx in (x0 + 0.15, x1 - 0.15):
        for cy in (y0 + 0.15, y1 - 0.15):
            box(shell, "rig_paint_orange", cx - 0.1, cx + 0.1, cy - 0.1, cy + 0.1, ok.main, fz - 0.06, "box", 0.0, 1.2)
            col(b, "metal", "doghouse_leg", cx - 0.1, cx + 0.1, cy - 0.1, cy + 0.1, ok.main, fz - 0.06)
    tube(shell, "rig_paint_orange", V(x0 + 0.15, y0 + 0.15, ok.main + 0.2), V(x0 + 0.15, y1 - 0.15, fz - 0.3), 0.06, 6, True, 1.4)
    tube(shell, "rig_paint_orange", V(x0 + 0.15, y0 + 0.15, fz - 0.3), V(x1 - 0.15, y0 + 0.15, ok.main + 0.2), 0.06, 6, True, 1.4)
    box(shell, "rig_paint_orange", x0, x1, y0, y0 + t, fz, fz + h, "box", 0.0, 1.2)
    box(shell, "rig_paint_orange", x0, x1, y1 - t, y1, fz, fz + h, "box", 0.0, 1.2)
    box(shell, "rig_paint_orange", x0, x0 + t, y0, y1, fz, fz + 0.9, "box", 0.0, 1.2)
    box(shell, "rig_paint_orange", x0, x0 + t, y0, y1, fz + 2.0, fz + h, "box", 0.0, 1.2)
    box(shell, "glass_dirty", x0 + t * 0.4, x0 + t * 0.6, y0 + 0.1, y1 - 0.1, fz + 0.9, fz + 2.0)
    box(shell, "rig_paint_orange", x1 - t, x1, y0, dog_door[0], fz, fz + h, "box", 0.0, 1.2)
    box(shell, "rig_paint_orange", x1 - t, x1, dog_door[1], y1, fz, fz + h, "box", 0.0, 1.2)
    box(shell, "rig_paint_orange", x1 - t, x1, dog_door[0], dog_door[1], fz + 2.15, fz + h, "box", 0.0, 1.2)
    box(shell, "glass_dirty", x1 - t * 0.6, x1 - t * 0.4, dog_door[1] + 0.1, y1 - 0.15, fz + 1.0, fz + 1.9)
    box(shell, "rig_paint_orange", x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, fz + h, fz + h + 0.1, "box", 0.0, 1.2)
    col(b, "metal", "doghouse", x0, x1, y0, y0 + t, fz, fz + h)
    col(b, "metal", "doghouse", x0, x1, y1 - t, y1, fz, fz + h)
    col(b, "metal", "doghouse", x0, x0 + t, y0, y1, fz, fz + h)
    col(b, "metal", "doghouse", x1 - t, x1, y0, dog_door[0], fz, fz + h)
    col(b, "metal", "doghouse", x1 - t, x1, dog_door[1], y1, fz, fz + h)
    col(b, "metal", "doghouse", x0, x1, y0, y1, fz + h, fz + h + 0.1)
    equipment = parts["equipment"]
    box(equipment, "rig_paint_grey", x0 + 0.1, x0 + 0.75, y0 + 0.3, y1 - 0.3, fz, fz + 0.85)
    tk.atlas_panel(equipment, "rig_signs", V(x0 + 0.42, (y0 + y1) * 0.5, fz + 0.86), up, 0.6, 1.6, lib.region_uv(lib.signs, "console"), math.pi * 0.5, 0.002)
    tp.chair_light(equipment, V(x0 + 1.25, (y0 + y1) * 0.5, fz), -math.pi * 0.5, rng, "rig_paint_grey", "rig_rubber")
    b.loot("toolbox", V(x1 - 0.5, y0 + 0.45, fz))
    ok.bulkhead_light(b, equipment, V((x0 + x1) * 0.5, y1 - 0.1, fz + 2.2), V(0.0, -1.0, 0.0), "warm", True)
    ok.sign(parts["fittings"], "no_smoking", V(x1 + 0.02, y0 + 0.4, fz + 1.7), V(1.0, 0.0, 0.0), 0.5, 0.18)


def drill_access(b, parts, rng):
    sx0, sx1, sy0, sy1 = ok.drill_stair
    ok.stair_flight(b, parts, sx0, sx1, sy0, sy1, z, ok.drill_z, "nx", rng, "rig_paint_yellow", "rig_paint_yellow", (True, True), (True, True), "drill_stair")
    structure = parts["structure"]
    for cx in (sx0 + 0.3, (sx0 + sx1) * 0.5):
        h = ok.drill_z - z - (cx - sx0) / (sx1 - sx0) * (ok.drill_z - z)
        for cy in (sy0, sy1):
            box(structure, "rig_paint_grey", cx - 0.08, cx + 0.08, cy - 0.08, cy + 0.08, z, z + h - 0.25, "box", 0.0, 1.6)
    vx0, vx1, vy0, vy1 = ok.vdoor
    fz = ok.drill_z
    length = vy1 - vy0
    rise = fz - z
    a = V((vx0 + vx1) * 0.5, vy1, z)
    c = V((vx0 + vx1) * 0.5, vy0, fz)
    forward = (c - a).normalized()
    normal = V(0.0, forward.z, -forward.y)
    if normal.z < 0.0:
        normal = -normal
    center = (a + c) * 0.5 - normal * 0.05
    emit(parts["deck"], kit.geo_box((c - a).length, vx1 - vx0, 0.1), "chequer_plate", kit.place(center, forward, normal), "box")
    for x in (vx0, vx1):
        side = 1.0 if x == vx1 else -1.0
        emit(structure, kit.geo_box((c - a).length, 0.06, 0.35), "rig_paint_orange", kit.place(center + V(side * 0.03, 0.0, 0.0) + normal * 0.2, forward, normal), "box", False, None, 1.4)
        col(b, "metal", "vdoor_side", x - 0.05 if side < 0 else x, x if side < 0 else x + 0.05, vy0, vy1, z, fz + 0.6)
    for k in range(4):
        t = (k + 0.5) / 4.0
        p = a.lerp(c, t)
        box(structure, "rig_paint_orange", vx0 + 0.1, vx1 - 0.1, p.y - 0.12, p.y + 0.12, z, p.z - 0.12, "box", 0.0, 1.4)
    b.ramp("ny", "metal", "vdoor", V(vx0, vy0, z), V(vx1, vy1, fz))


def crane(b, parts, rng):
    cx, cy = ok.crane_at
    part = parts["crane"]
    top = z + 6.6
    ok.lathe(part, "rig_paint_yellow", V(cx, cy, z), up, [(0.0, 0.0), (2.0, 0.0), (2.0, 0.3), (1.4, 0.9), (1.3, 1.2), (1.3, 6.3), (1.6, 6.4), (1.6, 6.6), (0.0, 6.6)], 24, True, 0.45)
    ok.ring(part, "rig_paint_grey", V(cx, cy, top - 0.05), up, 1.55, 0.08, 0.25, 24)
    col(b, "metal", "crane_pedestal", cx - 1.35, cx + 1.35, cy - 1.35, cy + 1.35, z, top)
    ok.ladder(part, V(cx - 1.75, cy, z), top - 0.4, V(1.0, 0.0, 0.0), 0.45, "rig_paint_yellow", True, 2.4)
    hz = top + 0.25
    hx0, hx1, hy0, hy1 = cx - 1.8, cx + 1.8, cy - 3.2, cy + 2.2
    box(part, "rig_paint_yellow", hx0, hx1, hy0, hy1, hz, hz + 2.6, "box", 0.05, 0.6)
    box(part, "rig_paint_grey", hx0 - 0.1, hx1 + 0.1, hy0 - 0.1, hy1 + 0.1, hz + 2.6, hz + 2.75)
    for k in range(3):
        louvre(part, V(hx1 + 0.02, hy0 + 1.0 + k * 1.6, hz + 1.4), V(1.0, 0.0, 0.0), 1.1, 0.9)
    cab = (hx0 - 1.6, hx0, hy1 - 2.2, hy1 + 0.2)
    box(part, "rig_paint_yellow", cab[0], cab[1], cab[2], cab[3], hz + 0.6, hz + 0.9, "box", 0.03)
    box(part, "rig_paint_yellow", cab[0], cab[1], cab[2], cab[3], hz + 2.55, hz + 2.75, "box", 0.03)
    for px, py in ((cab[0], cab[2]), (cab[0], cab[3]), (cab[1], cab[3])):
        box(part, "rig_paint_yellow", px - 0.06, px + 0.06, py - 0.06, py + 0.06, hz + 0.9, hz + 2.55)
    box(part, "glass_dirty", cab[0] + 0.02, cab[0] + 0.06, cab[2] + 0.1, cab[3] - 0.1, hz + 0.95, hz + 2.5)
    box(part, "glass_dirty", cab[0] + 0.1, cab[1] - 0.1, cab[3] - 0.06, cab[3] - 0.02, hz + 0.95, hz + 2.5)
    box(part, "rig_paint_yellow", cab[0], cab[1], cab[2], cab[2] + 0.06, hz + 0.9, hz + 2.55)
    tk.atlas_panel(part, "rig_signs", V((cab[0] + cab[1]) * 0.5, cab[3] - 0.4, hz + 1.25), V(0.0, 0.0, 1.0), 1.2, 0.5, lib.region_uv(lib.signs, "console"), 0.0, 0.003)
    box(part, "rig_paint_grey", cab[0] + 0.2, cab[1] - 0.2, cab[3] - 0.65, cab[3] - 0.15, hz + 0.9, hz + 1.24)
    foot = V(cx, hy1 + 0.2, hz + 0.9)
    tip = V(cx, 21.4, z + 6.9)
    gantry = V(cx, hy0 + 0.6, hz + 5.6)
    for sx in (-1.0, 1.0):
        tube(part, "rig_paint_yellow", V(cx + sx * 1.5, hy0 + 0.3, hz + 2.7), gantry + V(sx * 0.4, 0.0, 0.0), 0.12, 8)
        tube(part, "rig_paint_yellow", V(cx + sx * 1.5, hy1 - 1.2, hz + 2.7), gantry + V(sx * 0.4, 0.0, 0.0), 0.1, 8)
    tube(part, "rig_paint_yellow", gantry + V(-0.5, 0.0, 0.0), gantry + V(0.5, 0.0, 0.0), 0.14, 8)
    lattice_boom(part, foot, tip, rng)
    for sx in (-0.25, 0.25):
        ok.cable(part, gantry + V(sx, 0.0, 0.0), tip + V(sx * 0.6, -0.4, 0.5), 0.9, 0.018, "rig_rubber", 14)
    block = tip + V(0.0, 0.25, -6.5)
    tube(part, "rig_steel", tip + V(-0.1, 0.0, -0.3), block + V(-0.1, 0.0, 0.5), 0.015, 4, False)
    tube(part, "rig_steel", tip + V(0.1, 0.0, -0.3), block + V(0.1, 0.0, 0.5), 0.015, 4, False)
    box(part, "rig_paint_yellow", block.x - 0.3, block.x + 0.3, block.y - 0.18, block.y + 0.18, block.z - 0.1, block.z + 0.55, "box", 0.03)
    hook = [block + V(0.0, 0.0, -0.1), block + V(0.0, 0.0, -0.6), block + V(0.0, 0.25, -0.8), block + V(0.0, 0.32, -0.55)]
    ok.path_tube(part, "rig_rust", hook, 0.05, 6, True, 1.0)
    rx, ry = ok.boom_rest
    t = (ry - foot.y) / (tip.y - foot.y)
    rest_z = foot.z + (tip.z - foot.z) * t - (0.35 + 0.45 * math.sin(math.pi * t) ** 0.6) - 0.34
    for sx in (-1.0, 1.0):
        tube(part, "rig_paint_yellow", V(rx + sx * 1.2, ry - 0.6, z), V(rx + sx * 0.6, ry, rest_z), 0.12, 8)
        tube(part, "rig_paint_yellow", V(rx + sx * 1.2, ry + 0.6, z), V(rx + sx * 0.6, ry, rest_z), 0.12, 8)
    box(part, "rig_paint_yellow", rx - 0.9, rx + 0.9, ry - 0.25, ry + 0.25, rest_z, rest_z + 0.2)
    box(part, "rig_rubber", rx - 0.7, rx + 0.7, ry - 0.2, ry + 0.2, rest_z + 0.2, rest_z + 0.3)
    col(b, "metal", "boom_rest", rx - 1.3, rx + 1.3, ry - 0.7, ry + 0.7, z, z + 1.2)
    ok.sign(parts["fittings"], "danger", V(cx, cy - 1.32, z + 2.0), V(0.0, -1.0, 0.0), 1.1, 0.18)


def lattice_boom(part, foot, tip, rng):
    axis = tip - foot
    length = axis.length
    forward = axis.normalized()
    side = up.cross(forward).normalized()
    upward = forward.cross(side).normalized()
    bays = int(length / 1.6)

    def half(t):
        return 0.35 + 0.45 * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.6

    corners = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    for cs, cu in corners:
        points = [foot + forward * (length * k / bays) + side * (cs * half(k / bays)) + upward * (cu * half(k / bays)) for k in range(bays + 1)]
        ok.path_tube(part, "rig_paint_yellow", points, 0.07, 6, True, 1.6, upward)
    for k in range(bays):
        t0 = k / bays
        t1 = (k + 1) / bays
        p0 = foot + forward * (length * t0)
        p1 = foot + forward * (length * t1)
        h0 = half(t0)
        h1 = half(t1)
        faces = [((-1.0, -1.0), (1.0, -1.0)), ((1.0, -1.0), (1.0, 1.0)), ((1.0, 1.0), (-1.0, 1.0)), ((-1.0, 1.0), (-1.0, -1.0))]
        for (as_, au), (cs_, cu) in faces:
            a = p0 + side * (as_ * h0) + upward * (au * h0) if k % 2 == 0 else p0 + side * (cs_ * h0) + upward * (cu * h0)
            c = p1 + side * (cs_ * h1) + upward * (cu * h1) if k % 2 == 0 else p1 + side * (as_ * h1) + upward * (au * h1)
            tube(part, "rig_paint_yellow", a, c, 0.032, 4, False, 2.6)
        if k % 3 == 0:
            for (as_, au), (cs_, cu) in faces:
                tube(part, "rig_paint_yellow", p0 + side * (as_ * h0) + upward * (au * h0), p0 + side * (cs_ * h0) + upward * (cu * h0), 0.03, 4, False, 2.6)
    sheave = tip + forward * 0.2
    ok.lathe(part, "rig_paint_grey", sheave - side * 0.35, side, [(0.0, 0.0), (0.45, 0.0), (0.45, 0.7), (0.0, 0.7)], 14)


def pipe_rack(b, parts, rng):
    part = parts["services"]
    y = -2.0
    xs = [-16.0, -11.0, -6.0, -1.0, 4.0, 9.0]
    for x in xs:
        for dy in (-1.0, 1.0):
            ok.ibeam(part, "rig_paint_grey", V(x, y + dy, z), V(x, y + dy, z + 4.3), 0.25, 0.25, V(1.0, 0.0, 0.0))
            col(b, "metal", "rack_leg", x - 0.13, x + 0.13, y + dy - 0.13, y + dy + 0.13, z, z + 4.3)
        for hz in (z + 2.6, z + 4.2):
            ok.ibeam(part, "rig_paint_grey", V(x, y - 1.1, hz), V(x, y + 1.1, hz), 0.25, 0.2)
    lines = [(-0.7, z + 2.85, 0.22), (-0.15, z + 2.8, 0.16), (0.35, z + 2.78, 0.14), (0.75, z + 2.75, 0.1), (-0.6, z + 4.42, 0.18), (0.0, z + 4.36, 0.12), (0.5, z + 4.34, 0.1)]
    for dy, hz, radius in lines:
        tube(part, "rig_paint_grey" if radius > 0.13 else "rig_paint_white", V(xs[0] - 1.5, y + dy, hz), V(xs[-1] + 1.5, y + dy, hz), radius, 10)
        for x in xs:
            ok.ring(part, "rig_paint_grey", V(x, y + dy, hz), V(1.0, 0.0, 0.0), radius, 0.012, 0.06, 10)
    ok.cable_tray(part, V(xs[0] - 1.0, y + 0.2, z + 4.65), V(xs[-1] + 1.0, y + 0.2, z + 4.65), 0.7, rng, "rig_paint_grey", 5, 0.0)
    ok.pipe(part, "rig_paint_grey", [V(xs[-1] + 1.5, y - 0.7, z + 2.85), V(xs[-1] + 2.6, y - 0.7, z + 2.85), V(xs[-1] + 2.6, y - 0.7, z + 0.2), V(xs[-1] + 2.6, y - 0.7, z - 2.6)], 0.22, 10, 0.4)
    ok.gate_valve(part, "rig_paint_grey", V(xs[-1] + 2.6, y - 0.7, z + 1.1), up, 0.22, True, V(1.0, 0.0, 0.0))
    for k in range(3):
        x = rng.uniform(xs[0], xs[-1])
        ok.hanging_cable(part, V(x, y + rng.uniform(0.0, 0.4), z + 4.6), rng.uniform(1.0, 2.4), rng)


def containers_and_cargo(b, parts, rng):
    part = parts["cargo"]
    for x0, y0, along_x, paint in containers:
        ok.shipping_container(b, part, x0, y0, z, along_x, rng, paint)
    ok.shipping_container(b, part, 12.6, 13.6, z, True, rng, "rig_paint_grey", tag="container")
    door_x = 12.6
    for dy, angle in ((0.0, 1.9), (2.44, -2.2)):
        hinge = V(door_x, 13.6 + dy, z + 0.1)
        direction = V(math.cos(angle), math.sin(angle), 0.0)
        emit(part, kit.geo_box(1.2, 0.05, 2.35), "rig_paint_grey", kit.place(hinge + direction * 0.6 + V(0.0, 0.0, 1.2), direction, up), "box")
    x0, x1, y0, y1 = laydown
    box(part, "rig_paint_orange", x0, x1, y0, y0 + 0.08, z, z + 1.1)
    box(part, "rig_paint_orange", x0, x1, y1 - 0.08, y1, z, z + 1.1)
    box(part, "rig_paint_orange", x0, x0 + 0.08, y0, y1, z, z + 1.1)
    box(part, "rig_paint_orange", x1 - 0.08, x1, y0, y1, z, z + 1.1)
    box(part, "rig_paint_orange", x0, x1, y0, y1, z, z + 0.08)
    col(b, "metal", "basket", x0, x1, y0, y1, z, z + 1.1)
    for k in range(3):
        ok.gas_cylinder(part, V(x0 + 0.4 + k * 0.3, y0 + 0.5, z + 0.08), rng, rng.choice(["rig_paint_grey", "rig_paint_orange"]), True, 1.57)
    ok.hose(part, V((x0 + x1) * 0.5, y1 - 1.2, z + 0.08), rng, 0.4, 3, 0.03)
    ok.sack(part, V(x0 + 0.8, y1 - 0.5, z + 0.08), rng)
    b.loot("box", V(23.3, -14.6, z))
    ok.pallet(part, V(19.0, -13.4, z), 0.0, rng)
    ok.crate(part, V(19.0, -13.4, z + 0.13), (1.1, 1.0, 0.9), 0.0, rng)
    col(b, "wood", "crate", 18.4, 19.6, -14.0, -12.8, z, z + 1.05)


def room(b, parts, rect, height, rng, tag, door_side, door_span, paint="rig_paint_white", window=None):
    x0, x1, y0, y1 = rect
    shell = parts["shell"]
    t = 0.1
    sides = {"y0": (x0, x1, y0), "y1": (x0, x1, y1), "x0": (y0, y1, x0), "x1": (y0, y1, x1)}
    for key, (a, c, fixed) in sides.items():
        cuts = [a, c]
        hole = None
        if key == door_side:
            hole = door_span
            cuts += list(door_span)
        win = None
        if window and window[0] == key:
            win = window[1:]
            cuts += [win[0], win[1]]
        cuts = sorted(set(cuts))
        for s, e in zip(cuts[:-1], cuts[1:]):
            m = (s + e) * 0.5
            in_door = hole is not None and hole[0] <= m <= hole[1]
            in_window = win is not None and win[0] <= m <= win[1]
            spans = [(z, z + height)]
            if in_door:
                spans = [(z + 2.15, z + height)]
            elif in_window:
                spans = [(z, z + 1.0), (z + 2.0, z + height)]
            for zz0, zz1 in spans:
                if key in ("y0", "y1"):
                    box(shell, paint, s, e, fixed - t * 0.5, fixed + t * 0.5, zz0, zz1, "box", 0.0, 0.9)
                    col(b, "metal", tag, s, e, fixed - t * 0.5, fixed + t * 0.5, zz0, zz1)
                else:
                    box(shell, paint, fixed - t * 0.5, fixed + t * 0.5, s, e, zz0, zz1, "box", 0.0, 0.9)
                    col(b, "metal", tag, fixed - t * 0.5, fixed + t * 0.5, s, e, zz0, zz1)
            if in_window:
                if key in ("y0", "y1"):
                    box(shell, "glass_dirty", s, e, fixed - 0.01, fixed + 0.01, z + 1.0, z + 2.0)
                    col(b, "glass", tag + "_window", s, e, fixed - 0.03, fixed + 0.03, z + 1.0, z + 2.0)
                else:
                    box(shell, "glass_dirty", fixed - 0.01, fixed + 0.01, s, e, z + 1.0, z + 2.0)
                    col(b, "glass", tag + "_window", fixed - 0.03, fixed + 0.03, s, e, z + 1.0, z + 2.0)
    box(shell, "rig_paint_grey", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z + height, z + height + 0.12, "box", 0.0, 0.9)
    box(shell, "rig_ceiling", x0 + 0.06, x1 - 0.06, y0 + 0.06, y1 - 0.06, z + height - 0.04, z + height, "world")
    col(b, "metal", tag + "_roof", x0, x1, y0, y1, z + height, z + height + 0.12)


def workshop(b, parts, rng):
    rect = ok.workshop
    x0, x1, y0, y1 = rect
    room(b, parts, rect, 3.2, rng, "workshop", "y1", (-7.6, -6.4), "rig_paint_white", ("x1", -18.2, -16.0))
    inside = parts["interior"]
    box(inside, "rig_paint_grey", x0 + 0.2, x1 - 0.2, y0 + 0.08, y0 + 0.12, z, z + 3.1)
    bench_y = y0 + 0.1
    box(inside, "timber_planks_weathered", x0 + 0.3, x0 + 3.6, bench_y, bench_y + 0.75, z + 0.86, z + 0.92, "box")
    for px in (x0 + 0.4, x0 + 3.5):
        for py in (bench_y + 0.05, bench_y + 0.68):
            box(inside, "rig_paint_grey", px - 0.03, px + 0.03, py - 0.03, py + 0.03, z, z + 0.86)
    box(inside, "rig_paint_grey", x0 + 0.35, x0 + 3.55, bench_y + 0.05, bench_y + 0.72, z + 0.15, z + 0.18)
    col(b, "wood", "bench", x0 + 0.3, x0 + 3.6, bench_y, bench_y + 0.75, z, z + 0.92)
    vice = V(x0 + 3.3, bench_y + 0.62, z + 0.92)
    box(inside, "rig_paint_grey", vice.x - 0.1, vice.x + 0.1, vice.y - 0.12, vice.y + 0.08, vice.z, vice.z + 0.16)
    box(inside, "rig_paint_grey", vice.x - 0.1, vice.x + 0.1, vice.y + 0.12, vice.y + 0.2, vice.z + 0.02, vice.z + 0.16)
    tube(inside, "rig_steel", vice + V(0.0, 0.25, 0.08), vice + V(0.0, 0.42, 0.08), 0.012, 5)
    tube(inside, "rig_steel", vice + V(-0.12, 0.42, 0.08), vice + V(0.12, 0.42, 0.08), 0.01, 5)
    board = V(x0 + 1.9, y0 + 0.14, z + 1.65)
    box(inside, "timber_planks_weathered", board.x - 1.4, board.x + 1.4, board.y, board.y + 0.02, board.z - 0.5, board.z + 0.5)
    for k in range(9):
        p = V(board.x - 1.2 + k * 0.3, board.y + 0.04, board.z + rng.uniform(-0.3, 0.3))
        length = rng.uniform(0.18, 0.4)
        ok.bar(inside, rng.choice(["rig_steel", "rig_paint_orange", "rig_rubber"]), p, up, length, 0.03, 0.02, V(0.0, 1.0, 0.0), 2.0)
    drill = V(x0 + 4.6, bench_y + 0.45, z)
    box(inside, "rig_paint_grey", drill.x - 0.3, drill.x + 0.3, drill.y - 0.3, drill.y + 0.3, z, z + 0.08)
    tube(inside, "rig_steel", drill + V(0.0, 0.1, 0.08), drill + V(0.0, 0.1, 1.7), 0.05, 8)
    box(inside, "rig_paint_orange", drill.x - 0.16, drill.x + 0.16, drill.y - 0.25, drill.y + 0.2, z + 1.45, z + 1.85, "box", 0.03)
    box(inside, "rig_paint_grey", drill.x - 0.2, drill.x + 0.2, drill.y - 0.25, drill.y + 0.15, z + 0.9, z + 0.95)
    tube(inside, "rig_steel", drill + V(0.0, -0.15, 1.45), drill + V(0.0, -0.15, 1.2), 0.012, 5)
    col(b, "metal", "drill", drill.x - 0.3, drill.x + 0.3, drill.y - 0.3, drill.y + 0.3, z, z + 1.85)
    for k in range(3):
        sx = x1 - 0.5
        sy = y1 - 0.9 - k * 0.9
        rack_shelf(inside, V(sx, sy, z), rng)
    col(b, "metal", "shelf", x1 - 0.8, x1 - 0.1, y1 - 3.2, y1 - 0.4, z, z + 2.0)
    trolley = V(x0 + 0.6, y1 - 1.2, z)
    box(inside, "rig_paint_grey", trolley.x - 0.3, trolley.x + 0.3, trolley.y - 0.25, trolley.y + 0.25, z + 0.15, z + 0.2)
    ok.gas_cylinder(inside, trolley + V(-0.12, 0.0, 0.2), rng, "rig_rubber", False, 0.0, 1.35, 0.11, "rig_paint_grey")
    ok.gas_cylinder(inside, trolley + V(0.14, 0.0, 0.2), rng, "rig_paint_orange", False, 0.0, 1.2, 0.1, "rig_paint_grey")
    ok.hose(inside, trolley + V(0.0, 0.0, 1.0), rng, 0.15, 2, 0.012, "rig_paint_orange")
    b.loot("toolbox", V(x0 + 1.2, bench_y + 1.1, z))
    b.loot("toolbox", V(x1 - 1.6, y1 - 0.6, z))
    ok.strip_light(b, inside, V((x0 + x1) * 0.5, (y0 + y1) * 0.5, z + 3.14), 1.2, True, "cold", True)
    ok.plate_floor(b, inside, x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, z + 0.02, "rig_deck_green", (), 0.02, "metal", "workshop_floor", False)
    ok.sign(parts["fittings"], "workshop", V(-7.0, y1 + 0.07, z + 2.5), V(0.0, 1.0, 0.0), 0.8, 0.2)
    ok.floor_decal(parts["decals"], "oil_a", x0 + 2.0, y0 + 1.4, z + 0.03, 1.4, 1.4, 0.2)


def rack_shelf(part, base, rng):
    for zz in (0.25, 0.9, 1.55):
        box(part, "rig_paint_grey", base.x - 0.3, base.x + 0.3, base.y - 0.42, base.y + 0.42, base.z + zz, base.z + zz + 0.03)
        for k in range(rng.randint(1, 3)):
            w = rng.uniform(0.2, 0.36)
            d = rng.uniform(0.2, 0.3)
            hh = rng.uniform(0.15, 0.35)
            px = base.x + rng.uniform(-0.12, 0.12)
            py = base.y + rng.uniform(-0.25, 0.25)
            box(part, rng.choice(["rig_paint_orange", "rig_cardboard", "rig_cardboard", "timber_planks_weathered", "rig_paint_yellow"]), px - w * 0.5, px + w * 0.5, py - d * 0.5, py + d * 0.5, base.z + zz + 0.03, base.z + zz + 0.03 + hh)
    for dx in (-0.28, 0.28):
        for dy in (-0.4, 0.4):
            box(part, "rig_paint_grey", base.x + dx - 0.02, base.x + dx + 0.02, base.y + dy - 0.02, base.y + dy + 0.02, base.z, base.z + 2.0)


def store(b, parts, rng):
    rect = ok.store
    x0, x1, y0, y1 = rect
    door = (0.2, 1.4)
    room(b, parts, rect, 3.2, rng, "store", "y1", door, "rig_paint_grey")
    inside = parts["interior"]
    hinge = V(door[0], y1 + 0.06, z + 0.04)
    angle = 2.3
    direction = V(math.cos(angle), math.sin(angle), 0.0)
    matrix = kit.place(hinge + direction * 0.6 + V(0.0, 0.0, 1.05), direction, up) @ kit.Matrix.Rotation(0.06, 4, 'X')
    emit(inside, kit.geo_box(1.2, 0.06, 2.1), "rig_paint_grey", matrix, "box", False, None, 0.9)
    for dz in (0.4, 1.7):
        box(inside, "rig_steel", door[0] - 0.06, door[0] + 0.02, y1 + 0.05, y1 + 0.1, z + dz, z + dz + 0.15)
    box(inside, "rig_steel", door[1] + 0.02, door[1] + 0.14, y1 + 0.05, y1 + 0.08, z + 1.05, z + 1.2)
    box(inside, "rig_steel", door[1] + 0.1, door[1] + 0.13, y1 + 0.06, y1 + 0.16, z + 0.95, z + 1.08)
    ok.sign(parts["fittings"], "stores", V(-1.4, y1 + 0.07, z + 1.9), V(0.0, 1.0, 0.0), 0.9, 0.24)
    cage_x = x0 + 2.2
    for k in range(9):
        y = y0 + 0.2 + k * (y1 - y0 - 0.4) / 8.0
        if 0.9 < y - y0 < 2.1:
            continue
        tube(inside, "rig_steel", V(cage_x, y, z), V(cage_x, y, z + 3.1), 0.015, 4, False)
    for zz in (z + 0.1, z + 1.5, z + 3.0):
        tube(inside, "rig_steel", V(cage_x, y0 + 0.1, zz), V(cage_x, y1 - 0.1, zz), 0.02, 4, False)
    cage_door = V(cage_x, y0 + 0.9, z + 1.05)
    emit(inside, kit.geo_box(1.1, 0.03, 2.0), "rig_steel", kit.place(cage_door + V(-0.5, 0.35, 0.0), V(-0.8, 0.6, 0.0).normalized(), up), "box")
    col(b, "metal", "cage", cage_x - 0.05, cage_x + 0.05, y0, y0 + 0.9, z, z + 3.1)
    col(b, "metal", "cage", cage_x - 0.05, cage_x + 0.05, y0 + 2.1, y1, z, z + 3.1)
    for k in range(3):
        rack_shelf(inside, V(x0 + 0.45, y0 + 0.7 + k * 1.3, z), rng)
    col(b, "metal", "shelf", x0 + 0.1, x0 + 0.8, y0 + 0.2, y1 - 0.4, z, z + 2.0)
    tp.ammo_box(inside, V(x0 + 1.6, y0 + 0.6, z), 0.2, rng, "green")
    tp.ammo_box(inside, V(x0 + 1.4, y0 + 0.62, z + 0.2), 1.4, rng, "green")
    b.loot("military", V(x0 + 1.5, y1 - 0.8, z))
    b.loot("military", V(x0 + 1.7, y0 + 1.6, z))
    b.loot("box", V(x1 - 0.7, y0 + 0.7, z))
    ok.crate(inside, V(x1 - 0.8, y0 + 2.4, z), (0.9, 0.8, 0.7), 0.2, rng)
    col(b, "wood", "crate", x1 - 1.3, x1 - 0.3, y0 + 1.9, y0 + 2.9, z, z + 0.7)
    ok.strip_light(b, inside, V((x0 + x1) * 0.5, (y0 + y1) * 0.5, z + 3.14), 1.2, True, "warm", True)
    ok.plate_floor(b, inside, x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, z + 0.02, "rig_vinyl", (), 0.02, "metal", "store_floor", False)


def hull_section(t, half_beam, depth, canopy, steps=10):
    points = []
    for k in range(steps + 1):
        a = math.pi * 0.5 * k / steps
        points.append((half_beam * math.sin(a) ** 0.6, -depth * math.cos(a) ** 1.4))
    for k in range(1, steps + 1):
        a = math.pi * 0.5 * k / steps
        points.append((half_beam * 0.92 * math.cos(a) ** 0.55, canopy * math.sin(a) ** 0.8))
    return points


def lifeboat_geo(length=8.4, beam=3.0, depth=1.25, canopy=1.55, stations=14, steps=10):
    rings = []
    xs = []
    for i in range(stations + 1):
        t = i / stations
        x = -length * 0.5 + length * t
        s = 1.0 - abs(2.0 * t - 1.0) ** 2.6
        scale = max(s, 0.02) ** 0.55
        half = beam * 0.5 * scale
        d = depth * (0.55 + 0.45 * scale)
        c = canopy * (0.3 + 0.7 * max(s, 0.0) ** 0.4)
        profile = hull_section(t, half, d, c, steps)
        full = [(-p[0], p[1]) for p in reversed(profile[1:])] + profile
        rings.append([V(x, px, py) for px, py in full])
        xs.append(x)
    count = len(rings[0])
    points = []
    for ring in rings:
        points.extend(ring)
    faces = []
    for i in range(stations):
        for j in range(count - 1):
            a = i * count + j
            faces.append((a, a + count, a + count + 1, a + 1))
    for index, ring_start in ((0, 0), (stations, stations * count)):
        ring = rings[index]
        center = sum(ring, V(0.0, 0.0, 0.0)) / len(ring)
        center.x += -0.12 if index == 0 else 0.12
        points.append(center)
        tip = len(points) - 1
        for j in range(count - 1):
            faces.append((ring_start + j, ring_start + j + 1, tip))
    return Geo(points, faces)


def lifeboat(part, matrix, rng):
    geo = lifeboat_geo()
    geo = rk.away(geo, V(0.0, 0.0, 0.1))
    emit(part, geo, "rig_lifeboat", matrix, "box", True, None, 1.0)
    for sy in (-1.0, 1.0):
        points = [V(-4.0 + k * 0.5, sy * (1.5 * max(1.0 - abs((-4.0 + k * 0.5) / 4.2) ** 2.6, 0.02) ** 0.55 + 0.04), 0.0) for k in range(17)]
        emit(part, kit.geo_tube([matrix @ p for p in points], kit.circle(0.07, 6), True), "rig_rubber", None, "given", True)
    for x in (-2.4, -0.8, 0.8, 2.4):
        for sy in (-1.0, 1.0):
            center = V(x, sy * 1.3, 0.75)
            emit(part, kit.geo_box(0.5, 0.06, 0.28), "glass_dirty", matrix @ kit.Matrix.Translation(center) @ kit.Matrix.Rotation(sy * 0.45, 4, 'X'), "box")
    for x in (-3.2, 3.0):
        emit(part, kit.geo_cbox(0.9, 0.7, 0.12, 0.03), "rig_lifeboat", matrix @ kit.Matrix.Translation(V(x, 0.0, 1.5)), "box")
    emit(part, kit.geo_cbox(1.1, 0.12, 1.2, 0.03), "rig_lifeboat", matrix @ kit.Matrix.Translation(V(1.2, 1.38, 0.55)) @ kit.Matrix.Rotation(0.3, 4, 'X'), "box")
    emit(part, kit.geo_box(0.08, 0.06, 1.0), "rig_rubber", matrix @ kit.Matrix.Translation(V(4.15, 0.0, -0.75)), "box")
    emit(part, kit.geo_box(0.5, 0.05, 0.7), "rig_paint_orange", matrix @ kit.Matrix.Translation(V(4.35, 0.0, -0.9)), "box")
    for x in (-3.4, 3.4):
        emit(part, kit.geo_tube([matrix @ V(x, 0.0, 1.45), matrix @ V(x, 0.0, 1.85)], kit.circle(0.06, 6), True), "rig_steel", None, "given", True)
        emit(part, kit.geo_tube([matrix @ V(x, 0.0, 1.85), matrix @ V(x, 0.12, 2.05), matrix @ V(x, 0.0, 2.2)], kit.circle(0.045, 6), True), "rig_rust", None, "given", True)
    tk.atlas_panel(part, "rig_signs", matrix @ V(0.0, -1.42, 0.35), (matrix.to_3x3() @ V(0.0, -1.0, 0.25)).normalized(), 1.8, 0.4, lib.region_uv(lib.signs, "lifeboat_2"), 0.0, 0.02)


def davit(part, b, x, rng, empty, tilt=0.0):
    y_edge = ok.deck_y
    for sx in (-1.0, 1.0):
        px = x + sx * 3.2
        base = V(px, y_edge - 1.6, z)
        box(part, "rig_paint_orange", px - 0.25, px + 0.25, y_edge - 2.3, y_edge - 0.2, z, z + 0.5)
        ok.ibeam(part, "rig_paint_orange", V(px, y_edge - 2.0, z + 0.5), V(px, y_edge - 0.4, z + 2.6), 0.3, 0.2, V(1.0, 0.0, 0.0))
        arm_foot = V(px, y_edge - 0.4, z + 2.6)
        arm_head = V(px, y_edge + 1.7, z + 4.2)
        ok.ibeam(part, "rig_paint_orange", arm_foot, arm_head, 0.32, 0.2, V(1.0, 0.0, 0.0))
        ok.lathe(part, "rig_paint_grey", arm_head + V(-0.12, 0.0, 0.0), V(1.0, 0.0, 0.0), [(0.0, 0.0), (0.28, 0.0), (0.28, 0.24), (0.0, 0.24)], 12)
        col(b, "metal", "davit", px - 0.3, px + 0.3, y_edge - 2.3, y_edge - 0.15, z, z + 2.6)
    box(part, "rig_paint_orange", x - 3.4, x + 3.4, y_edge - 2.15, y_edge - 1.85, z + 0.4, z + 0.6)
    ok.lathe(part, "rig_paint_grey", V(x - 0.6, y_edge - 1.8, z + 0.9), V(1.0, 0.0, 0.0), [(0.0, 0.0), (0.38, 0.0), (0.38, 1.2), (0.0, 1.2)], 14)
    box(part, "rig_paint_orange", x - 0.9, x + 0.9, y_edge - 2.2, y_edge - 1.4, z, z + 0.55)
    col(b, "metal", "winch", x - 0.9, x + 0.9, y_edge - 2.3, y_edge - 1.3, z, z + 1.4)


def lifeboat_pose():
    stern_head = V(ok.davits[1] + 3.2, ok.deck_y + 1.7, z + 4.0)
    rotation = kit.Matrix.Rotation(math.radians(9.0), 4, 'X') @ kit.Matrix.Rotation(math.radians(-52.0), 4, 'Y')
    hook_world = stern_head - V(0.0, 0.0, 2.6) + V(-0.3, 0.2, 0.0)
    offset = hook_world - (rotation @ V(3.4, 0.0, 2.2))
    return kit.Matrix.Translation(offset) @ rotation, stern_head, hook_world


def lifeboat_station(b, parts, rng):
    part = parts["lifeboat"]
    empty_x, boat_x = ok.davits
    davit(part, b, empty_x, rng, True)
    davit(part, b, boat_x, rng, False)
    y_edge = ok.deck_y
    for sx in (-1.0, 1.0):
        head = V(empty_x + sx * 3.2, y_edge + 1.7, z + 4.0)
        hook = head - V(0.0, 0.0, 9.0 + sx * 1.5) + V(0.0, 0.3, 0.0)
        tube(part, "rig_steel", head, hook, 0.012, 4, False)
        ok.path_tube(part, "rig_rust", [hook, hook - V(0.0, 0.0, 0.5), hook + V(0.0, 0.25, -0.65), hook + V(0.0, 0.3, -0.4)], 0.04, 6, True, 1.0)
        box(part, "rig_paint_orange", hook.x - 0.15, hook.x + 0.15, hook.y - 0.12, hook.y + 0.12, hook.z, hook.z + 0.5, "box", 0.02)
    bow_head = V(boat_x - 3.2, y_edge + 1.7, z + 4.0)
    matrix, stern_head, hook_world = lifeboat_pose()
    lifeboat(part, matrix, rng)
    tube(part, "rig_steel", stern_head, hook_world, 0.014, 4, False)
    tube(part, "rig_steel", stern_head + V(0.05, 0.0, 0.0), hook_world + V(0.05, 0.0, 0.0), 0.014, 4, False)
    loose = [bow_head, bow_head - V(0.0, 0.0, 3.0), bow_head - V(-0.2, 0.0, 5.5) + V(0.0, 0.25, 0.0), bow_head - V(-0.6, 0.0, 6.4) + V(0.0, 0.5, 0.0)]
    ok.path_tube(part, "rig_steel", loose, 0.014, 4, True, 1.0)
    bow_hook = matrix @ V(-3.4, 0.0, 2.2)
    ok.path_tube(part, "rig_steel", [bow_hook, bow_hook + V(0.3, 0.2, -0.8), bow_hook + V(0.6, 0.4, -1.7)], 0.014, 4, True, 1.0)
    ok.sign(parts["fittings"], "muster", V((empty_x + boat_x) * 0.5, y_edge - 2.6, z + 1.9), V(0.0, -1.0, 0.0), 1.4, 0.26)
    post = V((empty_x + boat_x) * 0.5, y_edge - 2.5, z)
    box(part, "rig_paint_grey", post.x - 0.04, post.x + 0.04, post.y + 0.02, post.y + 0.1, z, z + 2.1)
    for x in (empty_x - 1.6, boat_x + 1.6):
        tp_lifebuoy(parts["fittings"], V(x, y_edge - 0.18, z + 0.8))
    b.loot("food", V(boat_x - 1.2, y_edge - 3.0, z))
    ok.floodlight(b, parts["fittings"], parts["lamps"], V(boat_x, y_edge - 0.3, z + 5.0), V(0.0, 0.7, -0.7), "cold", True, False, rng, V(boat_x, y_edge - 0.3, z + 2.6))
    tube(part, "rig_paint_grey", V(boat_x, y_edge - 0.3, z), V(boat_x, y_edge - 0.3, z + 5.0), 0.05, 8)


def tp_lifebuoy(part, center):
    profile = []
    for k in range(9):
        a = math.pi * 2.0 * k / 8.0
        profile.append((0.3 + 0.06 * math.cos(a), 0.06 * math.sin(a)))
    ok.lathe(part, "rig_lifeboat", center, V(0.0, -1.0, 0.0), profile, 16)


def deck_lights(b, parts, rng):
    fittings = parts["fittings"]
    poles = [(-24.4, -19.4, True), (24.4, -19.4, True), (24.4, 19.4, False), (-12.0, 19.4, True), (11.0, -9.0, True), (-12.0, -19.4, False)]
    for x, y, lit in poles:
        base = V(x, y, z)
        tube(fittings, "rig_paint_grey", base, base + V(0.0, 0.0, 6.0), 0.07, 8, True, 1.6)
        box(fittings, "rig_paint_grey", x - 0.2, x + 0.2, y - 0.2, y + 0.2, z, z + 0.04)
        aim = (V(0.0, 0.0, z) - V(x, y, z)).normalized() + V(0.0, 0.0, -0.7)
        ok.floodlight(b, fittings, parts["lamps"], base + V(0.0, 0.0, 6.0) + aim.normalized() * 0.35, aim, "cold", lit, not lit, rng)
        col(b, "metal", "pole", x - 0.08, x + 0.08, y - 0.08, y + 0.08, z, z + 6.0)
    fallen = V(-12.0, 15.5, z + 0.08)
    ok.bar(fittings, "rig_paint_grey", fallen + V(2.9, 0.3, 0.0), V(1.0, 0.1, 0.0).normalized(), 6.0, 0.14, 0.14, up, 1.6)


def dressing(b, parts, rng):
    clutter = parts["clutter"]
    decals = parts["decals"]
    for x, y in ((-12.5, -6.0), (9.5, 4.5), (-3.0, 13.0), (4.5, -6.0), (21.5, 16.5)):
        b.loot("box", V(x, y, z))
    for x, y in ((-13.5, -8.0), (-12.8, -8.6), (3.0, -12.5), (10.5, 0.5), (-1.0, 16.0), (-9.0, 15.5), (11.0, 16.0), (5.0, 12.0)):
        lying = rng.random() < 0.35
        ok.drum(clutter, V(x, y, z), rng, rng.choice(["rig_paint_grey", "rig_paint_orange", "rig_rust", "rig_paint_white"]), lying, rng.uniform(0.0, 6.0))
        if not lying:
            col(b, "metal", "drum", x - 0.3, x + 0.3, y - 0.3, y + 0.3, z, z + 0.88)
    for x, y, yaw in ((-1.5, 10.5, 0.4), (8.5, -4.5, 1.1), (-12.0, 9.0, 0.0)):
        ok.pallet(clutter, V(x, y, z), yaw, rng)
        col(b, "wood", "pallet", x - 0.7, x + 0.7, y - 0.7, y + 0.7, z, z + 0.14)
    for k in range(4):
        ok.sack(clutter, V(-1.5 + rng.uniform(-0.4, 0.4), 10.5 + rng.uniform(-0.4, 0.4), z + 0.13), rng)
    for k in range(6):
        ok.gas_cylinder(clutter, V(9.0 + (k % 3) * 0.28, -6.8 + (k // 3) * 0.3, z), rng, rng.choice(["rig_paint_grey", "rig_paint_orange", "rig_deck_green"]))
    box(clutter, "rig_paint_grey", 8.7, 9.9, -7.1, -6.0, z, z + 0.05)
    tube(clutter, "rig_paint_grey", V(8.7, -6.0, z + 1.2), V(9.9, -6.0, z + 1.2), 0.02, 5)
    col(b, "metal", "bottles", 8.7, 9.9, -7.1, -6.0, z, z + 1.4)
    for x, y in ((-10.5, 12.5), (2.5, 14.0), (-2.5, 11.0)):
        ok.hose(clutter, V(x, y, z), rng, rng.uniform(0.3, 0.5), 3, 0.03)
    for k in range(40):
        x = rng.uniform(-24.0, 24.0)
        y = rng.uniform(-19.0, 19.0)
        if ok.quarters[0] - 0.2 < x < ok.quarters[1] and ok.quarters[2] < y < ok.quarters[3]:
            continue
        if ok.drill[0] < x < ok.drill[1] and ok.drill[2] < y < ok.drill[3]:
            continue
        key = rng.choice(["guano_a", "guano_b", "guano_a", "oil_a", "oil_b", "salt"])
        ok.floor_decal(decals, key, x, y, z + 0.008, rng.uniform(0.8, 1.8), rng.uniform(0.8, 1.8), rng.uniform(0.0, 6.0))
    for x0, x1, y0, y1 in (ok.workshop, ok.store, ok.generator, ok.compressor):
        for k in range(4):
            if rng.random() < 0.5:
                xx = rng.uniform(x0 + 0.4, x1 - 0.4)
                yy = y0 - 0.07
                n = V(0.0, -1.0, 0.0)
            else:
                xx = x1 + 0.07
                yy = rng.uniform(y0 + 0.4, y1 - 0.4)
                n = V(1.0, 0.0, 0.0)
            ok.decal(decals, rng.choice(["run_a", "run_b", "run_c", "run_d", "runs_wide"]), V(xx, yy, z + rng.uniform(1.2, 2.4)), n, rng.uniform(0.3, 0.9), rng.uniform(1.2, 2.0))
    ok.sign(parts["fittings"], "escape", V(11.8, -12.4, z + 1.8), V(-1.0, 0.0, 0.0), 0.6, 0.22)
    ok.sign(parts["fittings"], "no_smoking", V(-16.9, -10.5, z + 1.8), V(1.0, 0.0, 0.0), 0.55, 0.2)
    fire_station(b, parts, V(4.0, -0.4, z), rng)
    fire_station(b, parts, V(-12.0, 1.2, z), rng)


def container_geo(part, matrix, paint, rng, length=6.06, width=2.44, height=2.59):
    hl = length * 0.5
    hw = width * 0.5
    emit(part, kit.geo_box(length - 0.08, width - 0.08, height - 0.18), paint, matrix @ kit.Matrix.Translation(V(0.0, 0.0, height * 0.5)), "box")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            emit(part, kit.geo_box(0.16, 0.16, height), "rig_rust", matrix @ kit.Matrix.Translation(V(sx * (hl - 0.08), sy * (hw - 0.08), height * 0.5)), "box")
    for zz in (0.06, height - 0.06):
        for sy in (-1.0, 1.0):
            emit(part, kit.geo_box(length, 0.12, 0.12), paint, matrix @ kit.Matrix.Translation(V(0.0, sy * (hw - 0.06), zz)), "box")
        for sx in (-1.0, 1.0):
            emit(part, kit.geo_box(0.12, width, 0.12), paint, matrix @ kit.Matrix.Translation(V(sx * (hl - 0.06), 0.0, zz)), "box")
    count = int((length - 0.4) / 0.28)
    for k in range(count):
        x = -hl + 0.3 + k * 0.28
        for sy in (-1.0, 1.0):
            emit(part, kit.geo_box(0.1, 0.035, height - 0.24), paint, matrix @ kit.Matrix.Translation(V(x, sy * (hw - 0.02), height * 0.5)), "box")


def storytelling(b, parts, rng):
    cargo = parts["cargo"]
    rails = parts["rails"]
    decals = parts["decals"]
    x0, x1 = dropped
    pivot = V((x0 + x1) * 0.5, -19.0, z)
    matrix = kit.Matrix.Translation(pivot) @ kit.Matrix.Rotation(0.06, 4, 'Z') @ kit.Matrix.Rotation(0.06, 4, 'X') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X') @ kit.Matrix.Translation(V(0.0, 1.22, 0.0))
    container_geo(cargo, matrix, "rig_paint_grey", rng)
    col(b, "metal", "dropped_container", x0, x1, -21.8, -18.9, z, z + 2.5)
    for k in range(4):
        px = x0 + 0.6 + k * 1.6
        bend = V(rng.uniform(-0.3, 0.3), -rng.uniform(0.5, 0.9), -rng.uniform(0.2, 0.6))
        tube(rails, "rig_paint_yellow", V(px, -19.9, z), V(px, -19.9, z) + bend.normalized() * 1.1, 0.024, 6, True, ok.fine)
    ok.path_tube(rails, "rig_paint_yellow", [V(x0 + 0.2, -19.9, z + 1.1), V(x0 + 2.0, -20.6, z + 0.5), V(x0 + 3.8, -20.9, z + 0.2), V(x1 - 0.4, -20.3, z + 0.7)], 0.025, 6, True, ok.fine)
    ok.decal(decals, "runs_wide", V((x0 + x1) * 0.5, -21.83, z + 1.2), V(0.0, -1.0, 0.0), 3.0, 2.0)
    sx0, sx1, sy0, sy1 = scaffold
    scaff = parts["clutter"]
    for px in (sx0, sx1):
        for py in (sy0, sy1):
            tube(scaff, "rig_steel", V(px, py, z), V(px, py, z + 4.6), 0.024, 6, True, 2.0)
            box(scaff, "timber_beam", px - 0.1, px + 0.1, py - 0.1, py + 0.1, z, z + 0.04)
            col(b, "metal", "scaffold", px - 0.05, px + 0.05, py - 0.05, py + 0.05, z, z + 4.6)
    for hz in (0.2, 2.0, 4.0):
        for a, c in ((V(sx0, sy0, z + hz), V(sx1, sy0, z + hz)), (V(sx0, sy1, z + hz), V(sx1, sy1, z + hz)), (V(sx0, sy0, z + hz), V(sx0, sy1, z + hz)), (V(sx1, sy0, z + hz), V(sx1, sy1, z + hz))):
            tube(scaff, "rig_steel", a, c, 0.024, 6, True, 2.0)
    for hz in (2.0, 4.0):
        for k in range(5):
            py = sy0 + 0.15 + k * (sy1 - sy0 - 0.3) / 4.0
            if hz == 4.0 and k == 2:
                continue
            box(scaff, "timber_planks_weathered", sx0 + 0.05, sx1 - 0.05, py - 0.11, py + 0.11, z + hz + 0.03, z + hz + 0.07, "board")
    tube(scaff, "rig_steel", V(sx0, sy0, z + 0.2), V(sx0, sy1, z + 2.0), 0.024, 6, True, 2.0)
    tube(scaff, "rig_steel", V(sx1, sy1, z + 2.0), V(sx1, sy0, z + 4.0), 0.024, 6, True, 2.0)
    fallen_board = kit.turned(V(sx1 + 1.3, sy0 + 0.8, z + 0.05), 0.7, 0.0, 0.04)
    emit(scaff, kit.geo_box(2.4, 0.22, 0.04), "timber_planks_weathered", fallen_board, "board")
    lines = [((-3.0, -16.4), (9.6, -16.4)), ((-3.0, -15.4), (9.6, -15.4)), ((9.6, -16.4), (9.6, -9.4)), ((10.6, -16.4), (10.6, -9.4)), ((-12.0, 16.4), (11.6, 16.4)), ((-12.0, 17.4), (11.6, 17.4)), ((-16.2, -9.0), (-16.2, 10.6)), ((-15.2, -9.0), (-15.2, 10.6))]
    for (ax, ay), (cx, cy) in lines:
        if ax == cx:
            box(parts["deck"], "rig_paint_yellow", ax - 0.05, ax + 0.05, min(ay, cy), max(ay, cy), z, z + 0.004, "box", 0.0, 0.6)
        else:
            box(parts["deck"], "rig_paint_yellow", min(ax, cx), max(ax, cx), ay - 0.05, ay + 0.05, z, z + 0.004, "box", 0.0, 0.6)
    for side, fixed, lo, hi, normal in (("s", -20.22, -24.0, 24.0, V(0.0, -1.0, 0.0)), ("n", 20.22, -24.0, 24.0, V(0.0, 1.0, 0.0)), ("w", -25.22, -19.0, 19.0, V(-1.0, 0.0, 0.0)), ("e", 25.22, -19.0, 19.0, V(1.0, 0.0, 0.0))):
        a = lo
        while a < hi:
            if rng.random() < 0.75:
                center = V(a, fixed, z - 0.75) if side in ("s", "n") else V(fixed, a, z - 0.75)
                ok.decal(decals, rng.choice(["runs_wide", "runs_wide", "run_c", "guano_runs"]), center, normal, rng.uniform(1.4, 2.4), rng.uniform(1.0, 1.4))
            a += rng.uniform(2.5, 4.5)
    equipment = parts["equipment"]
    for x, y in ((-11.0, -3.6), (-4.0, -3.6), (2.0, -3.6), (6.5, -0.2), (-9.0, 10.4), (3.0, 9.0)):
        tube(equipment, "rig_paint_grey", V(x, y, z), V(x, y, z + 1.2), 0.04, 6)
        box(equipment, "rig_paint_grey", x - 0.22, x + 0.22, y - 0.1, y + 0.1, z + 1.0, z + 1.5, "box", 0.02)
        if rng.random() < 0.5:
            ok.hanging_cable(equipment, V(x, y - 0.1, z + 1.0), rng.uniform(0.6, 0.9), rng, 0.012)
    clutter = parts["clutter"]
    ok.lump(clutter, "rig_paint_yellow", V(-6.4, -13.9, z + 0.08), (0.15, 0.13, 0.09), rng, 0.15, 1)
    ok.lump(clutter, "fabric_worn", V(-5.6, -13.6, z + 0.03), (0.09, 0.05, 0.03), rng, 0.3, 1)
    ok.hose(clutter, V(2.3, 6.8, z), rng, 0.32, 3, 0.015, "rope_net")
    ok.bar(clutter, "rig_steel", V(1.2, 6.2, z + 0.02), V(0.8, 0.6, 0.0).normalized(), 0.45, 0.04, 0.015, up, 2.0)


def fire_station(b, parts, base, rng):
    part = parts["fittings"]
    box(part, "rig_paint_orange", base.x - 0.45, base.x + 0.45, base.y - 0.2, base.y + 0.2, base.z, base.z + 1.6, "box", 0.03)
    ok.lathe(part, "rig_paint_orange", base + V(0.0, -0.22, 1.0), V(0.0, -1.0, 0.0), [(0.0, 0.0), (0.32, 0.0), (0.32, 0.18), (0.0, 0.18)], 14, False)
    ok.lathe(part, "rig_rubber", base + V(0.0, -0.25, 1.0), V(0.0, -1.0, 0.0), [(0.12, 0.0), (0.3, 0.0), (0.3, 0.14), (0.12, 0.14)], 14, False)
    col(b, "metal", "fire_station", base.x - 0.45, base.x + 0.45, base.y - 0.25, base.y + 0.2, base.z, base.z + 1.6)
    ok.sign(part, "fire_point", base + V(0.0, -0.22, 1.85), V(0.0, -1.0, 0.0), 0.5, 0.18)


def main():
    b = kit.Build("rig_main", 7301)
    rng = b.rng
    parts = ok.setup(b, (("structure", 50.0), ("deck", 40.0), ("shell", 40.0), ("equipment", 45.0), ("services", 50.0), ("crane", 50.0), ("cargo", 40.0), ("interior", 45.0), ("lifeboat", 50.0), ("clutter", 45.0), ("fittings", 45.0), ("rails", 50.0), ("lamps", 30.0), ("grating", 30.0), ("decals", 30.0)))
    deck(b, parts, rng)
    railings(b, parts, rng)
    compressor(b, parts, rng)
    generator(b, parts, rng)
    drill_floor(b, parts, rng)
    drill_access(b, parts, rng)
    crane(b, parts, rng)
    pipe_rack(b, parts, rng)
    containers_and_cargo(b, parts, rng)
    workshop(b, parts, rng)
    store(b, parts, rng)
    lifeboat_station(b, parts, rng)
    deck_lights(b, parts, rng)
    dressing(b, parts, rng)
    storytelling(b, parts, rng)
    return b


def main_far():
    b = kit.Build("rig_main_far", 7302)
    part = b.part("shell", 40.0)
    grate = b.part("grating", 30.0)
    decals = b.part("decals", 30.0)
    deck_far(part)
    rails_far(part)
    modules_far(part, decals)
    drill_far(part, grate)
    crane_far(part)
    rack_far(part)
    cargo_far(part)
    lifeboats_far(part)
    for x, y, lit in ((-24.4, -19.4, True), (24.4, -19.4, True), (24.4, 19.4, False), (-12.0, 19.4, True), (11.0, -9.0, True), (-12.0, -19.4, False)):
        ok.far_post(part, "rig_paint_grey", x, y, z, z + 6.0, 0.07, 1.6)
        ok.far_box(part, "rig_paint_grey", x - 0.18, x + 0.18, y - 0.18, y + 0.18, z + 5.75, z + 6.1)
    return b


def deck_far(part):
    dx, dy = ok.deck_x, ok.deck_y
    vx0, vx1, vy0, vy1 = void
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)], [[(vx0, vy0), (vx1, vy0), (vx1, vy1), (vx0, vy1)]], z - 0.03, z)
    emit(part, geo, "rig_deck_green", None, "world")
    for sy in (-1.0, 1.0):
        ok.far_box(part, frame_paint, -dx, dx, sy * ok.leg_y - 0.3, sy * ok.leg_y + 0.3, z - 2.0, z - 0.03)
        ok.far_box(part, frame_paint, -dx, dx, sy * dy - 0.2, sy * dy + 0.2, z - 1.2, z - 0.03)
    for sx in (-1.0, 1.0):
        ok.far_box(part, frame_paint, sx * ok.leg_x - 0.3, sx * ok.leg_x + 0.3, -dy, dy, z - 2.0, z - 0.03)
        ok.far_box(part, frame_paint, sx * dx - 0.2, sx * dx + 0.2, -dy, dy, z - 1.2, z - 0.03)
    y = -17.5
    while y < 18.0:
        if abs(abs(y) - ok.leg_y) > 0.8:
            pieces = [(-dx, dx)]
            if vy0 < y < vy1:
                pieces = [(-dx, vx0 - 0.1), (vx1 + 0.1, dx)]
            for a, c in pieces:
                ok.far_box(part, frame_paint, a, c, y - 0.125, y + 0.125, z - 0.82, z - 0.03, ("left", "right", "top"))
        y += 2.5
    for yy in (-dy, dy):
        ok.far_box(part, "rig_paint_yellow", -dx, dx, yy - 0.02 if yy > 0 else yy, yy if yy > 0 else yy + 0.02, z, z + 0.15, ("bottom",), ok.fine)
    for xx in (-dx, dx):
        ok.far_box(part, "rig_paint_yellow", xx - 0.02 if xx > 0 else xx, xx if xx > 0 else xx + 0.02, -dy, dy, z, z + 0.15, ("bottom",), ok.fine)
    lines = [((-3.0, -16.4), (9.6, -16.4)), ((-3.0, -15.4), (9.6, -15.4)), ((9.6, -16.4), (9.6, -9.4)), ((10.6, -16.4), (10.6, -9.4)), ((-12.0, 16.4), (11.6, 16.4)), ((-12.0, 17.4), (11.6, 17.4)), ((-16.2, -9.0), (-16.2, 10.6)), ((-15.2, -9.0), (-15.2, 10.6))]
    for (ax, ay), (cx, cy) in lines:
        if ax == cx:
            ok.flat_quad(part, "rig_paint_yellow", ax - 0.05, ax + 0.05, min(ay, cy), max(ay, cy), z + 0.004, "box")
        else:
            ok.flat_quad(part, "rig_paint_yellow", min(ax, cx), max(ax, cx), ay - 0.05, ay + 0.05, z + 0.004, "box")


def rails_far(part):
    e = 0.1
    x0, x1, y0, y1 = -ok.deck_x + e, ok.deck_x - e, -ok.deck_y + e, ok.deck_y - e
    fy0 = ok.flare_root[1] - 0.6
    fy1 = ok.flare_root[1] + 0.6
    for points in ([(x0, fy0), (x0, y0), (dropped[0], y0)], [(dropped[1], y0), (x1, y0), (x1, ok.quarters[2])], [(x1, ok.quarters[3]), (x1, y1), (ok.davits[1] + 1.0, y1)], [(ok.davits[1] - 1.0, y1), (ok.davits[0] + 1.0, y1)], [(ok.davits[0] - 1.0, y1), (x0, y1), (x0, fy1)]):
        ok.far_rail(part, points, z)
    vx0, vx1, vy0, vy1 = void
    ok.far_rail(part, [(vx0, vy1), (vx1, vy1), (vx1, vy0)], z, 1.1, "rig_paint_yellow", 3.6)
    ok.far_rail(part, [(vx0, vy0), (vx0, ok.cellar_stair_split)], z, 1.1, "rig_paint_yellow", 3.6)


def far_module(part, rect, height, openings, paint="rig_paint_white", roof="rig_paint_grey"):
    x0, x1, y0, y1 = rect
    t = 0.12
    walls = {"y0": (x0, x1, y0), "y1": (x0, x1, y1), "x0": (y0, y1, x0), "x1": (y0, y1, x1)}
    for key, (lo, hi, fixed) in walls.items():
        holes = [o[1:] for o in openings if o[0] == key]
        cuts = sorted(set([lo, hi] + [p for o in holes for p in (o[0], o[1])]))
        for s, e in zip(cuts[:-1], cuts[1:]):
            middle = (s + e) * 0.5
            z_low = z + max([o[2] for o in holes if o[0] <= middle <= o[1]], default=0.0)
            if z_low >= z + height:
                continue
            if key in ("y0", "y1"):
                ok.far_box(part, paint, s, e, fixed - t * 0.5, fixed + t * 0.5, z_low, z + height, ("top",), 0.8)
            else:
                ok.far_box(part, paint, fixed - t * 0.5, fixed + t * 0.5, s, e, z_low, z + height, ("top",), 0.8)
        length = hi - lo
        slots = max(1, int(length / 1.2) // 3)
        sign = 1.0 if key in ("y1", "x1") else -1.0
        for k in range(slots):
            p = lo + length * (k + 0.5) / slots
            if any(o[0] - 1.0 <= p <= o[1] + 1.0 for o in holes):
                continue
            zc = z + height - 1.1
            if key in ("y0", "y1"):
                ok.far_panel(part, "rig_rubber", (p - 0.5, fixed + sign * 0.08), (p + 0.5, fixed + sign * 0.08), zc - 0.4, zc + 0.4, V(0.0, sign, 0.0))
            else:
                ok.far_panel(part, "rig_rubber", (fixed + sign * 0.08, p - 0.5), (fixed + sign * 0.08, p + 0.5), zc - 0.4, zc + 0.4, V(sign, 0.0, 0.0))
    ok.far_box(part, roof, x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, z + height, z + height + 0.2, (), 0.8)


def modules_far(part, decals):
    x0, x1, y0, y1 = ok.compressor
    far_module(part, ok.compressor, 5.5, [("y0", -21.4, -20.2, 2.2), ("x1", -6.6, -2.2, 3.6)])
    ok.far_box(part, "rig_paint_grey", -23.4, -18.6, -7.6, -1.6, z, z + 0.35, ("bottom",))
    ok.far_tube(part, "rig_paint_grey", V(-21.0, -7.0, z + 1.3), V(-21.0, -4.2, z + 1.3), 0.75, 8)
    ok.far_box(part, "rig_paint_orange", -22.2, -19.8, -3.9, -1.9, z + 0.35, z + 2.2, ("bottom",))
    ok.decal(decals, "scorch", V(x1 + 0.08, -4.4, z + 4.2), V(1.0, 0.0, 0.0), 6.0, 4.0)
    ok.decal(decals, "scorch", V(-21.0, y0 - 0.08, z + 3.2), V(0.0, -1.0, 0.0), 3.0, 3.0)
    x0, x1, y0, y1 = ok.generator
    far_module(part, ok.generator, 5.0, [("x1", 3.0, 4.2, 2.2)])
    roof = z + 5.2
    for cy in (6.0, 11.0):
        ok.far_box(part, "rig_paint_grey", -21.9, -19.5, cy - 1.0, cy + 1.0, roof, roof + 0.8, ("bottom",))
        ok.far_tube(part, "rig_rust", V(-20.7, cy, roof + 0.8), V(-20.7, cy, roof + 6.6), 0.55, 8)
    for cy in (3.5, 13.5):
        ok.far_box(part, "rig_paint_white", -23.8, -21.4, cy - 0.9, cy + 0.9, roof, roof + 1.6, ("bottom",))
    ok.far_rail(part, [(x0 + 0.1, y0 + 0.1), (x1 - 0.1, y0 + 0.1), (x1 - 0.1, y1 - 0.1), (x0 + 0.1, y1 - 0.1), (x0 + 0.1, y0 + 0.1)], roof, 1.0, "rig_paint_yellow", 4.4, False)
    x0, x1, y0, y1 = ok.workshop
    ok.far_box(part, "rig_paint_white", x0, x1, y0, y1, z, z + 3.2, ("bottom", "top"))
    ok.far_box(part, "rig_paint_grey", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z + 3.2, z + 3.32)
    ok.far_panel(part, "soot", (-7.6, y1 + 0.01), (-6.4, y1 + 0.01), z, z + 2.15, V(0.0, 1.0, 0.0))
    ok.far_panel(part, "glass_dirty", (x1 + 0.01, -18.2), (x1 + 0.01, -16.0), z + 1.0, z + 2.0, V(1.0, 0.0, 0.0))
    x0, x1, y0, y1 = ok.store
    ok.far_box(part, "rig_paint_grey", x0, x1, y0, y1, z, z + 3.2, ("bottom", "top"))
    ok.far_box(part, "rig_paint_grey", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z + 3.2, z + 3.32)
    ok.far_panel(part, "soot", (0.2, y1 + 0.01), (1.4, y1 + 0.01), z, z + 2.15, V(0.0, 1.0, 0.0))
    direction = V(math.cos(2.3), math.sin(2.3), 0.0)
    emit(part, kit.geo_box(1.2, 0.06, 2.1), "rig_paint_grey", kit.place(V(0.2, y1 + 0.06, z + 1.09) + direction * 0.6, direction, up), "box")


def drill_far(part, grate):
    x0, x1, y0, y1 = ok.drill
    fz = ok.drill_z
    for cx in (x0, (x0 + x1) * 0.5, x1):
        for cy in (y0, (y0 + y1) * 0.5, y1):
            if cx == (x0 + x1) * 0.5 and cy == (y0 + y1) * 0.5:
                continue
            ok.far_post(part, "rig_paint_orange", cx, cy, z, fz - 0.4, 0.3, 1.2)
    clad = fz - 0.75
    ok.far_box(part, "rig_paint_orange", x0 + 0.3, x1 - 0.3, y0 - 0.04, y0 + 0.04, z, clad, ("top", "bottom"), 0.8)
    ok.far_box(part, "rig_paint_orange", x0 - 0.04, x0 + 0.04, y0 + 0.3, y1 - 0.3, z, clad, ("top", "bottom"), 0.8)
    ok.far_box(part, "rig_paint_orange", x1 - 0.04, x1 + 0.04, y0 + 0.3, 2.0, z, clad, ("top", "bottom"), 0.8)
    ok.far_box(part, "rig_paint_orange", x1 - 0.04, x1 + 0.04, 3.2, y1 - 0.3, z, clad, ("top", "bottom"), 0.8)
    ok.far_box(part, "rig_paint_orange", x1 - 0.04, x1 + 0.04, 2.0, 3.2, z + 2.2, clad, ("top",), 0.8)
    vx0, vx1 = ok.vdoor[0], ok.vdoor[1]
    ok.far_tube(part, "rig_paint_orange", V(x0, y1, z + 0.3), V(vx0 - 0.3, y1, fz - 0.8), 0.1, 4, 1.4)
    ok.far_tube(part, "rig_paint_orange", V(x1, y1, z + 0.3), V(vx1 + 0.3, y1, fz - 0.8), 0.1, 4, 1.4)
    ok.far_box(part, "rig_paint_orange", x0, x1, y0, y1, fz - 0.75, fz - 0.05, ("top",), 1.2)
    ok.far_box(part, "chequer_plate", x0, x1, y0, y1, fz - 0.05, fz, ("bottom",), 1.0, "world")
    ok.far_tube(part, "rig_paint_orange", V(-6.0, 4.5, z), V(-6.0, 4.5, z + 3.6), 0.75, 8)
    ok.far_box(part, "rig_paint_grey", -7.1, -4.9, 3.4, 5.6, fz, fz + 0.32, ("bottom",))
    dw = (-7.9, -3.0, 0.2, 1.55)
    ok.far_box(part, "rig_paint_orange", dw[0], dw[1], dw[2], dw[3], fz, fz + 1.2, ("bottom",))
    tube(part, "rig_paint_grey", V(dw[0] + 0.6, (dw[2] + dw[3]) * 0.5, fz + 1.55), V(dw[0] + 4.36, (dw[2] + dw[3]) * 0.5, fz + 1.55), 0.7, 8, True)
    sx0, sx1, sy0, sy1 = ok.drill_stair
    ok.far_rail(part, [(x1 - 0.05, sy0), (x1 - 0.05, y0 + 0.05), (x0 + 0.05, y0 + 0.05), (x0 + 0.05, dog[2])], fz)
    ok.far_rail(part, [(x0 + 0.05, dog[3]), (x0 + 0.05, y1 - 0.05), (vx0, y1 - 0.05)], fz)
    ok.far_rail(part, [(vx1, y1 - 0.05), (x1 - 0.05, y1 - 0.05), (x1 - 0.05, sy1)], fz)
    dx0, dx1, dy0, dy1 = dog
    ok.far_box(part, "rig_paint_orange", dx0, dx1, dy0, dy1, fz - 0.3, fz + 2.6)
    ok.far_box(part, "rig_paint_orange", dx0 - 0.05, dx1 + 0.05, dy0 - 0.05, dy1 + 0.05, fz + 2.6, fz + 2.7, ("bottom",))
    ok.far_panel(part, "glass_dirty", (dx0 - 0.01, dy1 - 0.1), (dx0 - 0.01, dy0 + 0.1), fz + 0.9, fz + 2.0, V(-1.0, 0.0, 0.0))
    ok.far_panel(part, "soot", (dx1 + 0.01, dog_door[0]), (dx1 + 0.01, dog_door[1]), fz, fz + 2.15, V(1.0, 0.0, 0.0))
    for cx in (dx0 + 0.15, dx1 - 0.15):
        for cy in (dy0 + 0.15, dy1 - 0.15):
            ok.far_post(part, "rig_paint_orange", cx, cy, z, fz - 0.3, 0.1, 1.2)
    ok.far_stair(part, grate, sx0, sx1, sy0, sy1, z, fz, "nx")
    for cx in (sx0 + 0.3, (sx0 + sx1) * 0.5):
        h = fz - z - (cx - sx0) / (sx1 - sx0) * (fz - z)
        for cy in (sy0, sy1):
            ok.far_post(part, "rig_paint_grey", cx, cy, z, z + h - 0.25, 0.08, 1.6)
    vy0, vy1 = ok.vdoor[2], ok.vdoor[3]
    ok.slope_box(part, "chequer_plate", vx0, vx1, vy0, vy1, z, fz, "ny", 0.1)
    for (a, c) in ok.slope_ends(vx0, vx1, vy0, vy1, z, fz, "ny"):
        ok.far_bar(part, "rig_paint_orange", a + V(0.0, 0.0, 0.15), c + V(0.0, 0.0, 0.15), 0.06, 0.35)
    for k in range(4):
        t = (k + 0.5) / 4.0
        py = vy1 + (vy0 - vy1) * t
        pz = z + (fz - z) * t
        ok.far_box(part, "rig_paint_orange", vx0 + 0.1, vx1 - 0.1, py - 0.12, py + 0.12, z, pz - 0.12, ("bottom",), 1.4)


def crane_far(part):
    cx, cy = ok.crane_at
    top = z + 6.6
    ok.lathe(part, "rig_paint_yellow", V(cx, cy, z), up, [(2.0, 0.0), (2.0, 0.3), (1.3, 1.2), (1.3, 6.3), (1.6, 6.4), (1.6, 6.6), (0.0, 6.6)], 10, True, 0.45)
    hz = top + 0.25
    hx0, hx1, hy0, hy1 = cx - 1.8, cx + 1.8, cy - 3.2, cy + 2.2
    ok.far_box(part, "rig_paint_yellow", hx0, hx1, hy0, hy1, hz, hz + 2.6, (), 0.6)
    ok.far_box(part, "rig_paint_grey", hx0 - 0.1, hx1 + 0.1, hy0 - 0.1, hy1 + 0.1, hz + 2.6, hz + 2.75, ("bottom",))
    cab = (hx0 - 1.6, hx0, hy1 - 2.2, hy1 + 0.2)
    ok.far_box(part, "rig_paint_yellow", cab[0], cab[1], cab[2], cab[3], hz + 0.6, hz + 2.75)
    ok.far_panel(part, "glass_dirty", (cab[0] - 0.01, cab[3] - 0.1), (cab[0] - 0.01, cab[2] + 0.1), hz + 0.95, hz + 2.5, V(-1.0, 0.0, 0.0))
    ok.far_panel(part, "glass_dirty", (cab[0] + 0.1, cab[3] + 0.01), (cab[1] - 0.1, cab[3] + 0.01), hz + 0.95, hz + 2.5, V(0.0, 1.0, 0.0))
    foot = V(cx, hy1 + 0.2, hz + 0.9)
    tip = V(cx, 21.4, z + 6.9)
    gantry = V(cx, hy0 + 0.6, hz + 5.6)
    for sx in (-1.0, 1.0):
        ok.far_tube(part, "rig_paint_yellow", V(cx + sx * 1.5, hy0 + 0.3, hz + 2.7), gantry + V(sx * 0.4, 0.0, 0.0), 0.12, 4)
        ok.far_tube(part, "rig_paint_yellow", V(cx + sx * 1.5, hy1 - 1.2, hz + 2.7), gantry + V(sx * 0.4, 0.0, 0.0), 0.1, 4)
    ok.far_tube(part, "rig_paint_yellow", gantry + V(-0.5, 0.0, 0.0), gantry + V(0.5, 0.0, 0.0), 0.14, 4)
    axis = tip - foot
    length = axis.length
    forward = axis.normalized()
    side = up.cross(forward).normalized()
    upward = forward.cross(side).normalized()

    def half(t):
        return 0.35 + 0.45 * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.6

    def corner(t, cs, cu):
        return foot + forward * (length * t) + side * (cs * half(t)) + upward * (cu * half(t))

    corners = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    for cs, cu in corners:
        ok.far_path(part, "rig_paint_yellow", [corner(k / 4.0, cs, cu) for k in range(5)], 0.08, 4, 1.6, upward)
    bays = 10
    for k in range(bays):
        t0 = k / bays
        t1 = (k + 1) / bays
        for index in range(4):
            a_corner = corners[index]
            c_corner = corners[(index + 1) % 4]
            if k % 2 == 0:
                a = corner(t0, a_corner[0], a_corner[1])
                c = corner(t1, c_corner[0], c_corner[1])
            else:
                a = corner(t0, c_corner[0], c_corner[1])
                c = corner(t1, a_corner[0], a_corner[1])
            ok.far_tube(part, "rig_paint_yellow", a, c, 0.04, 3, 2.6)
    tube(part, "rig_paint_grey", tip + forward * 0.2 - side * 0.35, tip + forward * 0.2 + side * 0.35, 0.45, 8, True)
    for sx in (-0.25, 0.25):
        ok.far_tube(part, "rig_rubber", gantry + V(sx, 0.0, 0.0), tip + V(sx * 0.6, -0.4, 0.5), 0.03, 3)
    block = tip + V(0.0, 0.25, -6.5)
    ok.far_tube(part, "rig_steel", tip + V(0.0, 0.0, -0.3), block + V(0.0, 0.0, 0.5), 0.03, 3)
    ok.far_box(part, "rig_paint_yellow", block.x - 0.3, block.x + 0.3, block.y - 0.18, block.y + 0.18, block.z - 0.1, block.z + 0.55)
    rx, ry = ok.boom_rest
    t = (ry - foot.y) / (tip.y - foot.y)
    rest_z = foot.z + (tip.z - foot.z) * t - half(t) - 0.34
    for sx in (-1.0, 1.0):
        ok.far_tube(part, "rig_paint_yellow", V(rx + sx * 1.2, ry - 0.6, z), V(rx + sx * 0.6, ry, rest_z), 0.12, 4)
        ok.far_tube(part, "rig_paint_yellow", V(rx + sx * 1.2, ry + 0.6, z), V(rx + sx * 0.6, ry, rest_z), 0.12, 4)
    ok.far_box(part, "rig_paint_yellow", rx - 0.9, rx + 0.9, ry - 0.25, ry + 0.25, rest_z, rest_z + 0.2)


def rack_far(part):
    y = -2.0
    xs = [-16.0, -11.0, -6.0, -1.0, 4.0, 9.0]
    for x in xs:
        for dy in (-1.0, 1.0):
            ok.far_post(part, "rig_paint_grey", x, y + dy, z, z + 4.3, 0.125)
        for hz in (z + 2.6, z + 4.2):
            ok.far_bar(part, "rig_paint_grey", V(x, y - 1.1, hz), V(x, y + 1.1, hz), 0.2, 0.25)
    lines = [(-0.7, z + 2.85, 0.22), (-0.15, z + 2.8, 0.16), (0.35, z + 2.78, 0.14), (0.75, z + 2.75, 0.1), (-0.6, z + 4.42, 0.18), (0.0, z + 4.36, 0.12), (0.5, z + 4.34, 0.1)]
    for dy, hz, radius in lines:
        ok.far_tube(part, "rig_paint_grey" if radius > 0.13 else "rig_paint_white", V(xs[0] - 1.5, y + dy, hz), V(xs[-1] + 1.5, y + dy, hz), radius, 6 if radius > 0.13 else 4)
    ok.far_box(part, "rig_paint_grey", xs[0] - 1.0, xs[-1] + 1.0, y + 0.2 - 0.35, y + 0.2 + 0.35, z + 4.6, z + 4.7, ("left", "right"))
    ok.far_path(part, "rig_paint_grey", [V(xs[-1] + 1.5, y - 0.7, z + 2.85), V(xs[-1] + 2.6, y - 0.7, z + 2.85), V(xs[-1] + 2.6, y - 0.7, z - 2.6)], 0.22, 6, 1.0)


def cargo_far(part):
    for x0, y0, along_x, paint in containers:
        ok.far_box(part, paint, x0, x0 + 6.06, y0, y0 + 2.44, z, z + 2.59, ("bottom",))
    ok.far_box(part, "rig_paint_grey", 12.6, 18.66, 13.6, 16.04, z, z + 2.59, ("bottom",))
    ok.far_panel(part, "soot", (12.59, 16.0), (12.59, 13.64), z + 0.1, z + 2.45, V(-1.0, 0.0, 0.0))
    for dy, angle in ((0.0, 1.9), (2.44, -2.2)):
        hinge = V(12.6, 13.6 + dy, z + 0.1)
        direction = V(math.cos(angle), math.sin(angle), 0.0)
        emit(part, kit.geo_box(1.2, 0.05, 2.35), "rig_paint_grey", kit.place(hinge + direction * 0.6 + V(0.0, 0.0, 1.2), direction, up), "box")
    x0, x1, y0, y1 = laydown
    for wx0, wx1, wy0, wy1 in ((x0, x1, y0, y0 + 0.08), (x0, x1, y1 - 0.08, y1), (x0, x0 + 0.08, y0, y1), (x1 - 0.08, x1, y0, y1)):
        ok.far_box(part, "rig_paint_orange", wx0, wx1, wy0, wy1, z, z + 1.1, ("bottom",))
    ok.far_box(part, "timber_planks_weathered", 18.45, 19.55, -13.95, -12.85, z, z + 1.05, ("bottom",))
    x0, x1 = dropped
    pivot = V((x0 + x1) * 0.5, -19.0, z)
    matrix = kit.Matrix.Translation(pivot) @ kit.Matrix.Rotation(0.06, 4, 'Z') @ kit.Matrix.Rotation(0.06, 4, 'X') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X') @ kit.Matrix.Translation(V(0.0, 1.22, 0.0))
    emit(part, kit.geo_box(6.06, 2.44, 2.59), "rig_paint_grey", matrix @ kit.Matrix.Translation(V(0.0, 0.0, 1.295)), "box")
    sx0, sx1, sy0, sy1 = scaffold
    for px in (sx0, sx1):
        for py in (sy0, sy1):
            ok.far_post(part, "rig_steel", px, py, z, z + 4.6, 0.03, 2.0)
    for hz in (2.0, 4.0):
        ok.far_box(part, "timber_planks_weathered", sx0 + 0.05, sx1 - 0.05, sy0 + 0.04, sy1 - 0.04, z + hz + 0.03, z + hz + 0.07, (), 1.0, "board")


def lifeboats_far(part):
    y_edge = ok.deck_y
    for x in ok.davits:
        for sx in (-1.0, 1.0):
            px = x + sx * 3.2
            ok.far_box(part, "rig_paint_orange", px - 0.25, px + 0.25, y_edge - 2.3, y_edge - 0.2, z, z + 0.5, ("bottom",))
            ok.far_bar(part, "rig_paint_orange", V(px, y_edge - 2.0, z + 0.5), V(px, y_edge - 0.4, z + 2.6), 0.2, 0.3)
            ok.far_bar(part, "rig_paint_orange", V(px, y_edge - 0.4, z + 2.6), V(px, y_edge + 1.7, z + 4.2), 0.2, 0.32)
        ok.far_box(part, "rig_paint_orange", x - 3.4, x + 3.4, y_edge - 2.15, y_edge - 1.85, z + 0.4, z + 0.6, ("bottom",))
        ok.far_box(part, "rig_paint_orange", x - 0.9, x + 0.9, y_edge - 2.2, y_edge - 1.4, z, z + 0.55, ("bottom",))
        ok.far_tube(part, "rig_paint_grey", V(x - 0.6, y_edge - 1.8, z + 0.9), V(x + 0.6, y_edge - 1.8, z + 0.9), 0.38, 6)
    for sx in (-1.0, 1.0):
        head = V(ok.davits[0] + sx * 3.2, y_edge + 1.7, z + 4.0)
        ok.far_tube(part, "rig_steel", head, head - V(0.0, 0.0, 9.0 + sx * 1.5) + V(0.0, 0.3, 0.0), 0.025, 3)
    matrix, stern_head, hook_world = lifeboat_pose()
    emit(part, rk.away(lifeboat_geo(8.4, 3.0, 1.25, 1.55, 6, 3), V(0.0, 0.0, 0.1)), "rig_lifeboat", matrix, "box", True, None, 1.0)
    ok.far_tube(part, "rig_steel", stern_head, hook_world, 0.03, 3)
    bow_head = V(ok.davits[1] - 3.2, y_edge + 1.7, z + 4.0)
    ok.far_path(part, "rig_steel", [bow_head, bow_head - V(0.0, 0.0, 3.0), bow_head - V(-0.6, 0.0, 6.4) + V(0.0, 0.5, 0.0)], 0.025, 3, 1.0)
