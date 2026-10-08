import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import town_kit as tk
import oilrig_library as lib
import oilrig_kit as ok
import oilrig_jacket as oj
from buildkit import V, Geo, emit
from oilrig_kit import box, col, tube, up

z = ok.cellar
top = ok.main - 2.0
frame_paint = "rig_paint_white"
truss_y = [(-15.0, -7.5, 0.0, 7.5, 15.0), (-1.0, 1.0)]
truss_x = [(-12.0, -4.0, 4.0, 12.0), (-1.0, 1.0)]
plate_zones = [(-24.6, -2.6, 12.6, 19.6), (3.6, 13.0, -6.6, 1.6), (15.6, 24.6, 0.6, 9.4)]
collapse = (20.6, 23.6, 16.4, 19.4)
scrubber = (1.6, 16.6, 0.9, 4.6)
exchanger = (-22.2, -17.4, 9.6, 0.45)
injection = (-21.2, 3.2)
mcc = (16.0, 24.4, 1.0, 9.0)
separator_a = (-22.6, -13.6, 16.0, 1.5)
separator_b = (-10.4, -4.8, 16.2, 1.0)
tanks = [(18.4, -16.0, 1.1, 4.2), (21.6, -16.0, 1.1, 3.6)]


def framing(b, parts, rng):
    structure = parts["structure"]
    for sy in (-1.0, 1.0):
        ok.ibeam(structure, frame_paint, V(-ok.deck_x, sy * ok.leg_y, z - 0.5), V(ok.deck_x, sy * ok.leg_y, z - 0.5), 1.0, 0.45, None, 0.02, 0.035, 1.0)
    for sx in (-1.0, 1.0):
        ok.ibeam(structure, frame_paint, V(sx * ok.leg_x, -ok.deck_y, z - 0.5), V(sx * ok.leg_x, ok.deck_y, z - 0.5), 1.0, 0.45, None, 0.02, 0.035, 1.0)
    for sx in (-1.0, 1.0):
        ok.ibeam(structure, frame_paint, V(sx * ok.deck_x, -ok.deck_y, z - 0.3), V(sx * ok.deck_x, ok.deck_y, z - 0.3), 0.6, 0.3)
    for sy in (-1.0, 1.0):
        ok.ibeam(structure, frame_paint, V(-ok.deck_x, sy * ok.deck_y, z - 0.3), V(ok.deck_x, sy * ok.deck_y, z - 0.3), 0.6, 0.3)
    y = -ok.deck_y + 2.5
    while y < ok.deck_y - 1.0:
        if abs(abs(y) - ok.leg_y) > 0.6:
            x0 = -ok.deck_x
            pieces = [(x0, ok.deck_x)]
            if ok.tower[2] - 0.2 < y < ok.tower[3] + 0.2:
                pieces = [(x0, ok.tower[0] - 0.1), (ok.tower_runs[1] + 0.1, ok.deck_x)]
            for a, c in pieces:
                ok.ibeam(structure, frame_paint, V(a, y, z - 0.22), V(c, y, z - 0.22), 0.4, 0.18)
        y += 2.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            center = V(sx * ok.leg_x, sy * ok.leg_y, 0.0)
            tube(structure, frame_paint, V(center.x, center.y, z - 0.6), V(center.x, center.y, top + 0.05), 0.8, 20, False)
            ok.ring(structure, frame_paint, V(center.x, center.y, z + 0.4), up, 0.8, 0.05, 0.3, 20)
            col(b, "metal", "deck_leg", center.x - 0.8, center.x + 0.8, center.y - 0.8, center.y + 0.8, z, top)
    for sy in (-1.0, 1.0):
        xs = truss_y[0]
        for x in xs:
            if abs(x) < 14.0:
                column(b, structure, V(x, sy * ok.leg_y, 0.0), True)
        for index in range(len(xs) - 1):
            a = xs[index]
            c = xs[index + 1]
            rising = (index % 2 == 0) == (sy > 0)
            diagonal(b, structure, V(a if rising else c, sy * ok.leg_y, z + 0.1), V(c if rising else a, sy * ok.leg_y, top - 0.1))
        for x in (-25.0, 25.0):
            column(b, structure, V(x, sy * ok.leg_y, 0.0), True)
    for sx in (-1.0, 1.0):
        ys = truss_x[0]
        for y in ys:
            if abs(y) < 11.0:
                column(b, structure, V(sx * ok.leg_x, y, 0.0), True)
        for index in range(len(ys) - 1):
            a = ys[index]
            c = ys[index + 1]
            rising = (index % 2 == 0) == (sx > 0)
            diagonal(b, structure, V(sx * ok.leg_x, a if rising else c, z + 0.1), V(sx * ok.leg_x, c if rising else a, top - 0.1))
        for y in (-20.0, 20.0):
            column(b, structure, V(sx * ok.leg_x, y, 0.0), True)
    for x in (-25.0, -5.0, 5.0, 25.0):
        for y in (-20.0, 20.0):
            column(b, structure, V(x, y, 0.0), True)
    for y in (0.0,):
        for x in (-25.0, 25.0):
            column(b, structure, V(x, y, 0.0), True)


def column(b, part, base, collide):
    ok.ibeam(part, frame_paint, V(base.x, base.y, z), V(base.x, base.y, top), 0.36, 0.36, V(1.0, 0.0, 0.0), 0.016, 0.026, 1.4)
    box(part, frame_paint, base.x - 0.3, base.x + 0.3, base.y - 0.3, base.y + 0.3, z, z + 0.03)
    if collide:
        col(b, "metal", "column", base.x - 0.19, base.x + 0.19, base.y - 0.19, base.y + 0.19, z, top)


def diagonal(b, part, a, c):
    tube(part, frame_paint, a, c, 0.22, 10, True, 1.2)
    steps = 5
    for k in range(steps):
        p = a.lerp(c, k / steps)
        q = a.lerp(c, (k + 1) / steps)
        if min(p.z, q.z) > z + 2.6:
            continue
        col(b, "metal", "diagonal", min(p.x, q.x) - 0.23, max(p.x, q.x) + 0.23, min(p.y, q.y) - 0.23, max(p.y, q.y) + 0.23, min(p.z, q.z) - 0.2, max(p.z, q.z) + 0.2)


def floors(b, parts, rng):
    holes = [(ok.tower[0], ok.tower_runs[1], ok.tower[2], ok.tower[3]), collapse]
    for zone in plate_zones:
        holes.append(zone)
    ok.grating_floor(b, parts, -ok.deck_x, ok.deck_x, -ok.deck_y, ok.deck_y, z, frame_paint, True, "cellar", holes, 1.0, False)
    for x0, x1, y0, y1 in plate_zones:
        ok.plate_floor(b, parts["deck"], x0, x1, y0, y1, z, "rig_deck_green", (), 0.03, "metal", "pan")
        for a, c in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
            box(parts["deck"], "rig_paint_yellow", min(a[0], c[0]) - 0.04, max(a[0], c[0]) + 0.04, min(a[1], c[1]) - 0.04, max(a[1], c[1]) + 0.04, z, z + 0.12, "box", 0.0, ok.fine)


def railings(b, parts, rng):
    rails = parts["rails"]
    x0, x1, y0, y1 = -ok.deck_x + 0.1, ok.deck_x - 0.1, -ok.deck_y + 0.1, ok.deck_y - 0.1
    sx0, sx1, sy0, sy1 = ok.cellar_stair
    ok.railing(b, rails, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], z, rng, 1.1, "rig_paint_yellow", True, False, "edge", 0.0, 0.1)
    tx0, tx1, ty0, ty1 = ok.tower
    run0, run1 = ok.tower_runs
    ok.railing(b, rails, [(run1, ty0), (tx0, ty0), (tx0, ty1), (run1, ty1)], z, rng, 1.1, "rig_paint_yellow", True, False, "tower_hole")
    ok.railing(b, rails, [(run1, ty0), (run1, ok.tower_split)], z, rng, 1.1, "rig_paint_yellow", True, False, "tower_hole")


def cellar_stairs(b, parts, rng):
    sx0, sx1, sy0, sy1 = ok.cellar_stair
    split = ok.cellar_stair_split
    run0, run1 = ok.cellar_stair_runs
    lane_a = (sy0 + 0.05, split - 0.05)
    lane_b = (split + 0.05, sy1 - 0.05)
    mid = (z + ok.main) * 0.5
    ok.stair_flight(b, parts, run0, run1, lane_a[0], lane_a[1], z, mid, "px", rng, "rig_paint_yellow", "rig_paint_yellow", (True, True), (False, False), "cellar_stair")
    ok.stair_flight(b, parts, run0, run1, lane_b[0], lane_b[1], mid, ok.main, "nx", rng, "rig_paint_yellow", "rig_paint_yellow", (True, True), (False, True), "cellar_stair")
    ok.grating_floor(b, parts, run1, sx1, sy0, sy1, mid, "rig_paint_grey", True, "half_landing")
    structure = parts["structure"]
    for cx in (run1, sx1):
        for cy in (sy0, sy1):
            ok.ibeam(structure, "rig_paint_grey", V(cx, cy, z), V(cx, cy, mid), 0.18, 0.18, V(1.0, 0.0, 0.0))
    ok.channel(structure, "rig_paint_grey", V(run1, sy0, mid - 0.12), V(sx1, sy0, mid - 0.12), 0.18, 0.06, up)
    ok.channel(structure, "rig_paint_grey", V(run1, sy1, mid - 0.12), V(sx1, sy1, mid - 0.12), 0.18, 0.06, up)
    rails = parts["rails"]
    ok.railing(b, rails, [(sx1, sy0), (sx1, sy1), (run1, sy1)], mid, rng, 1.1, "rig_paint_yellow", True, False, "half_landing")
    col(b, "metal", "stair_divider", run0, run1, split - 0.05, split + 0.05, z, ok.main + 1.1)
    col(b, "metal", "stair_outer", run0, sx1, sy0 - 0.1, sy0, z, ok.main + 1.1)
    ok.sign(parts["fittings"], "main_level", V(run1, sy1 + 0.12, z + 1.6), V(0.0, 1.0, 0.0), 0.75, 0.15)


def xmas_tree(b, parts, center, rng, wing_dir):
    part = parts["equipment"]
    paint = "rig_paint_orange"
    base = V(center.x, center.y, z)
    ok.lathe(part, "rig_paint_grey", base, up, [(0.0, 0.0), (0.42, 0.0), (0.42, 0.18), (0.36, 0.2), (0.36, 0.55), (0.46, 0.57), (0.46, 0.68), (0.0, 0.68)], 14)
    stack = [(0.68, 1.12, 0.3), (1.16, 1.6, 0.3)]
    for z0, z1, half in stack:
        box(part, paint, base.x - half, base.x + half, base.y - half, base.y + half, base.z + z0, base.z + z1, "box", 0.03)
        ok.handwheel(part, "rig_paint_yellow", V(base.x - half - 0.35, base.y, base.z + (z0 + z1) * 0.5), V(1.0, 0.0, 0.0), 0.22)
        tube(part, paint, V(base.x - half, base.y, base.z + (z0 + z1) * 0.5), V(base.x - half - 0.33, base.y, base.z + (z0 + z1) * 0.5), 0.05, 6)
    cross_z = base.z + 1.86
    box(part, paint, base.x - 0.24, base.x + 0.24, base.y - 0.24, base.y + 0.24, cross_z - 0.24, cross_z + 0.24, "box", 0.02)
    wing = V(wing_dir, 0.0, 0.0)
    a = V(base.x, base.y, cross_z) + wing * 0.24
    c = a + wing * 0.55
    tube(part, paint, a, c, 0.12, 10)
    box(part, paint, c.x - 0.18 if wing_dir > 0 else c.x - 0.18, c.x + 0.18, c.y - 0.2, c.y + 0.2, cross_z - 0.22, cross_z + 0.22, "box", 0.02)
    ok.lathe(part, "rig_paint_grey", V(c.x, c.y, cross_z + 0.22), up, [(0.0, 0.0), (0.14, 0.0), (0.14, 0.5), (0.2, 0.52), (0.2, 0.62), (0.0, 0.62)], 10)
    tube(part, paint, c + wing * 0.18, c + wing * 0.6, 0.09, 8)
    ok.flange(part, paint, c + wing * 0.6, wing, 0.09, 10)
    tube(part, paint, V(base.x, base.y, cross_z + 0.24), V(base.x, base.y, cross_z + 0.7), 0.14, 10)
    box(part, paint, base.x - 0.22, base.x + 0.22, base.y - 0.22, base.y + 0.22, cross_z + 0.7, cross_z + 1.1, "box", 0.02)
    ok.handwheel(part, "rig_paint_yellow", V(base.x, base.y + 0.5, cross_z + 0.9), V(0.0, 1.0, 0.0), 0.2)
    tube(part, paint, V(base.x, base.y + 0.22, cross_z + 0.9), V(base.x, base.y + 0.48, cross_z + 0.9), 0.04, 6)
    ok.lathe(part, "rig_paint_grey", V(base.x, base.y, cross_z + 1.1), up, [(0.0, 0.0), (0.16, 0.0), (0.16, 0.2), (0.08, 0.3), (0.0, 0.3)], 10)
    gauge = V(base.x + 0.2, base.y - 0.25, cross_z + 1.0)
    tube(part, "rig_steel", V(base.x, base.y - 0.22, cross_z + 1.0), gauge, 0.015, 5)
    ok.lathe(part, "rig_steel", gauge, V(0.0, -1.0, 0.0), [(0.0, 0.0), (0.06, 0.0), (0.06, 0.04), (0.0, 0.04)], 10, False)
    col(b, "metal", "tree", base.x - 0.45, base.x + 0.45, base.y - 0.45, base.y + 0.45, z, cross_z + 1.4)
    return c + wing * 0.66


def wellbay(b, parts, rng):
    part = parts["equipment"]
    outlets = []
    for index, (x, y) in enumerate(ok.wells):
        outlets.append(xmas_tree(b, parts, V(x, y, z), rng, 1.0))
    header_x = -1.4
    header_y0 = 1.6
    header_y1 = 8.2
    hz = z + 1.05
    tube(part, "rig_paint_grey", V(header_x, header_y0, hz), V(header_x, header_y1, hz), 0.2, 12)
    for y in (header_y0, header_y1):
        ok.lathe(part, "rig_paint_grey", V(header_x, y, hz), V(0.0, 1.0 if y == header_y1 else -1.0, 0.0), [(0.0, 0.0), (0.2, 0.0), (0.12, 0.18), (0.0, 0.2)], 12)
    for y in (header_y0 + 0.4, header_y1 - 0.4):
        box(part, "rig_paint_grey", header_x - 0.25, header_x + 0.25, y - 0.12, y + 0.12, z, hz - 0.2)
    col(b, "metal", "manifold", header_x - 0.25, header_x + 0.25, header_y0, header_y1, z, hz + 0.25)
    for index, outlet in enumerate(outlets):
        target_y = header_y0 + 0.6 + index * ((header_y1 - header_y0 - 1.2) / max(len(outlets) - 1, 1))
        route = [outlet, V(outlet.x + 0.4, outlet.y, outlet.z), V(outlet.x + 0.4, outlet.y, hz + 0.7 + index * 0.05), V(header_x - 1.5, target_y, hz + 0.7 + index * 0.05), V(header_x - 0.9, target_y, hz + 0.7 + index * 0.05), V(header_x - 0.2, target_y, hz + 0.1)]
        ok.pipe(part, "rig_paint_grey", route, 0.07, 8, 0.2)
        ok.gate_valve(part, "rig_paint_grey", V(header_x - 0.9, target_y, hz + 0.7 + index * 0.05), V(1.0, 0.0, 0.0), 0.08)
    out = [V(header_x, header_y1 + 0.2, hz), V(header_x, 10.6, hz), V(header_x, 10.6, z + 4.6), V(-4.0, 10.6, z + 4.6), V(-7.6, 14.4, z + 4.6), V(-7.6, 16.2, z + 3.2)]
    ok.pipe(part, "rig_paint_grey", out, 0.16, 10, 0.5)
    ok.gate_valve(part, "rig_paint_grey", V(header_x, 9.6, hz), V(0.0, 1.0, 0.0), 0.16, True, V(-1.0, 0.0, 0.0))
    ok.sign(parts["fittings"], "h2s", V(-9.2, 1.6, z + 1.8), V(0.0, -1.0, 0.0), 0.6, 0.22)
    for x in (-8.6, -3.4):
        for y in (2.0, 7.0):
            box(part, "rig_paint_yellow", x - 0.04, x + 0.04, y - 0.04, y + 0.04, z, z + 1.0, "box", 0.0, ok.fine)
    ok.railing(b, parts["rails"], [(-8.6, 2.0), (-3.4, 2.0)], z, rng, 1.0, "rig_paint_yellow", False, False, "wellbay", 0.0, 0.0, True, False)


def separator(b, parts, x0, x1, y, radius, rng, label=None):
    part = parts["equipment"]
    cz = z + 0.7 + radius
    a = V(x0, y, cz)
    c = V(x1, y, cz)
    ok.vessel(part, "rig_paint_white", a, c, radius, 28, 0.5)
    for t in (0.15, 0.85):
        ok.saddle(part, "rig_paint_grey", V(x0 + (x1 - x0) * t, y, cz), V(1.0, 0.0, 0.0), radius, 0.3, 0.7)
    for t in (0.35, 0.65):
        ok.ring(part, "rig_paint_white", V(x0 + (x1 - x0) * t, y, cz), V(1.0, 0.0, 0.0), radius, 0.012, 0.1, 28)
    manway = V(x0 - radius * 0.5, y, cz)
    ok.lathe(part, "rig_paint_white", manway, V(-1.0, 0.0, 0.0), [(0.0, 0.0), (0.35, 0.0), (0.35, 0.3), (0.5, 0.3), (0.5, 0.42), (0.0, 0.42)], 16)
    for k in range(12):
        angle = math.pi * 2.0 * k / 12.0
        p = manway + V(-0.42, math.cos(angle) * 0.44, math.sin(angle) * 0.44)
        tube(part, "rig_steel", p + V(0.03, 0.0, 0.0), p - V(0.04, 0.0, 0.0), 0.022, 6)
    tube(part, "rig_steel", manway + V(-0.42, -0.4, 0.0), manway + V(-0.42, 0.55, 0.3), 0.02, 5)
    top_nozzles = [x0 + (x1 - x0) * t for t in (0.2, 0.5, 0.8)]
    for index, nx in enumerate(top_nozzles):
        base = V(nx, y, cz + radius * 0.98)
        tube(part, "rig_paint_white", base, base + V(0.0, 0.0, 0.45), 0.14 if index != 1 else 0.2, 10)
        ok.flange(part, "rig_paint_white", base + V(0.0, 0.0, 0.45), up, 0.14 if index != 1 else 0.2, 12)
    psv = V(top_nozzles[0], y, cz + radius + 0.55)
    box(part, "rig_paint_orange", psv.x - 0.15, psv.x + 0.15, psv.y - 0.15, psv.y + 0.15, psv.z, psv.z + 0.4, "box", 0.02)
    tube(part, "rig_paint_orange", psv + V(0.0, 0.0, 0.4), psv + V(0.0, 0.0, 0.85), 0.05, 8)
    ok.pipe(part, "rig_paint_grey", [psv + V(0.15, 0.0, 0.2), psv + V(0.8, 0.0, 0.2), V(psv.x + 0.8, y, top - 0.9), V(x1 + 2.0, y, top - 0.9)], 0.1, 8, 0.3)
    for nx in (x0 + 1.0, x1 - 1.0):
        base = V(nx, y, cz - radius * 0.98)
        tube(part, "rig_paint_white", base, base - V(0.0, 0.0, 0.35), 0.12, 10)
        ok.gate_valve(part, "rig_paint_grey", base - V(0.0, 0.0, 0.5), V(0.0, 1.0, 0.0), 0.11, True, V(-1.0, 0.0, 0.0))
    gauge_x = x0 + (x1 - x0) * 0.42
    side = y - radius - 0.2
    tube(part, "rig_steel", V(gauge_x, side, cz - radius * 0.6), V(gauge_x, side, cz + radius * 0.6), 0.04, 6)
    for zz in (cz - radius * 0.6, cz + radius * 0.6):
        tube(part, "rig_steel", V(gauge_x, side, zz), V(gauge_x, y - radius * 0.8, zz), 0.03, 6)
    box(part, "glass_dirty", gauge_x - 0.03, gauge_x + 0.03, side - 0.05, side - 0.035, cz - radius * 0.5, cz + radius * 0.5)
    col(b, "metal", "vessel", x0 - radius * 0.5 - 0.4, x1 + radius * 0.5, y - radius, y + radius, z, cz + radius)
    ladder_x = x1 - 0.6
    ok.ladder(part, V(ladder_x, y - radius - 0.45, z), cz + radius - 0.2, V(0.0, 1.0, 0.0), 0.45, "rig_paint_yellow", True, 2.4)
    if label:
        ok.sign(parts["fittings"], label, V((x0 + x1) * 0.5, y - radius * 0.72 - 0.05, cz - radius * 0.68), V(0.0, -1.0, 0.0), 1.0, 0.22)
    return cz


def pumps(b, parts, rng):
    part = parts["equipment"]
    for index in range(3):
        x = 4.6 + index * 2.9
        y0 = -5.6
        y1 = -0.4
        box(part, "rig_paint_grey", x - 0.5, x + 0.5, y0, y1, z, z + 0.2)
        motor = V(x, y0 + 1.2, z + 0.75)
        ok.lathe(part, "rig_paint_grey" if index != 1 else "rig_paint_orange", motor - V(0.0, 0.6, 0.0), V(0.0, 1.0, 0.0), [(0.0, 0.0), (0.38, 0.0), (0.42, 0.05), (0.42, 1.15), (0.36, 1.25), (0.0, 1.25)], 14)
        for k in range(12):
            angle = math.pi * 2.0 * k / 12.0
            offset = V(math.cos(angle) * 0.44, 0.0, math.sin(angle) * 0.44)
            if offset.z < -0.3:
                continue
            ok.bar(part, "rig_paint_grey", motor + offset + V(0.0, 0.05, 0.0), V(0.0, 1.0, 0.0), 1.0, 0.04, 0.012, V(math.cos(angle), 0.0, math.sin(angle)), ok.fine)
        box(part, "rig_paint_grey", x - 0.3, x + 0.3, y0 + 0.4, y0 + 0.65, z + 0.2, z + 0.4)
        box(part, "rig_paint_grey", x - 0.25, x + 0.25, y0 + 2.4, y0 + 2.9, z + 0.2, z + 0.7)
        tube(part, "rig_steel", motor + V(0.0, 0.65, 0.0), motor + V(0.0, 1.2, 0.0), 0.06, 8)
        casing = V(x, y0 + 3.4, z + 0.75)
        ok.lathe(part, "rig_paint_grey", casing - V(0.0, 0.25, 0.0), V(0.0, 1.0, 0.0), [(0.0, 0.0), (0.42, 0.0), (0.48, 0.12), (0.48, 0.38), (0.42, 0.5), (0.0, 0.5)], 14)
        ok.pipe(part, "rig_paint_grey", [casing + V(0.0, 0.25, 0.0), casing + V(0.0, 1.0, 0.0), casing + V(0.0, 1.0, -0.4), V(x, y1 + 0.6, z + 0.35)], 0.14, 10, 0.3)
        ok.pipe(part, "rig_paint_grey", [casing + V(0.0, 0.0, 0.48), casing + V(0.0, 0.0, 1.4), casing + V(0.0, -2.2, 1.4), V(x, -6.6, top - 1.2), V(x, -9.0, top - 1.2)], 0.12, 10, 0.3)
        ok.gate_valve(part, "rig_paint_grey", casing + V(0.0, -0.9, 1.4), V(0.0, 1.0, 0.0), 0.12, True, up)
        col(b, "metal", "pump", x - 0.5, x + 0.5, y0, y1 + 0.6, z, z + 1.3)
        ok.decal(parts["decals"], "oil_a" if index % 2 == 0 else "oil_b", V(x + 0.2, y0 + 2.6, z + 0.205), up, 1.6, 1.6, rng.uniform(0.0, 6.0))
    b.loot("toolbox", V(4.0, 0.9, z))
    toolbox_shelf(parts, V(13.4, -2.0, z), rng)
    for k in range(4):
        ok.drum(part, V(12.6 + (k % 2) * 0.62, 1.2 + (k // 2) * 0.62, z), rng, "rig_paint_grey" if k % 2 else "rig_paint_orange")
    col(b, "metal", "drums", 12.3, 13.9, 0.9, 2.5, z, z + 0.9)


def toolbox_shelf(parts, base, rng):
    part = parts["equipment"]
    for zz in (0.0, 0.6, 1.2, 1.8):
        box(part, "rig_paint_grey", base.x - 0.25, base.x + 0.25, base.y - 0.9, base.y + 0.9, base.z + zz + 0.05, base.z + zz + 0.08)
    for dy in (-0.88, 0.88):
        for dx in (-0.23, 0.23):
            box(part, "rig_paint_grey", base.x + dx - 0.02, base.x + dx + 0.02, base.y + dy - 0.02, base.y + dy + 0.02, base.z, base.z + 1.95)
    ok.gas_cylinder(part, base + V(0.0, -0.4, 0.08), rng, "rig_paint_grey", True, 1.57, 0.6, 0.08)
    ok.hose(part, base + V(0.0, 0.4, 0.68), rng, 0.22, 2, 0.018)


def caisson_pumps(b, parts, rng):
    part = parts["equipment"]
    for x, y in oj.caissons:
        base = V(x, y, z)
        ok.lathe(part, "rig_paint_grey", base - V(0.0, 0.0, 0.2), up, [(0.0, 0.0), (0.62, 0.0), (0.62, 0.35), (0.48, 0.38), (0.48, 0.6), (0.0, 0.6)], 16)
        ok.lathe(part, "rig_paint_orange", base + V(0.0, 0.0, 0.4), up, [(0.0, 0.0), (0.42, 0.0), (0.46, 0.06), (0.46, 1.3), (0.38, 1.42), (0.18, 1.48), (0.18, 1.62), (0.0, 1.62)], 14)
        ok.pipe(part, "rig_paint_grey", [base + V(0.5, 0.0, 0.2), base + V(1.4, 0.0, 0.2), base + V(1.4, 0.0, 3.6), base + V(4.0, 0.0, 3.6)], 0.14, 10, 0.3)
        ok.gate_valve(part, "rig_paint_grey", base + V(1.4, 0.0, 1.4), up, 0.14, True, V(-1.0, 0.0, 0.0))
        col(b, "metal", "caisson_pump", x - 0.62, x + 1.6, y - 0.62, y + 0.62, z, z + 2.1)
    ok.sign(parts["fittings"], "fire_point", V(-14.2, -6.0, z + 1.7), V(1.0, 0.0, 0.0), 0.55, 0.2)


def pig_traps(b, parts, rng):
    part = parts["equipment"]
    for index, x in enumerate(oj.riser_xs):
        riser_top = V(x, oj.face_y(oj.top_z + 0.6) + 0.9, oj.top_z + 0.6)
        barrel_z = z + 1.1
        ok.pipe(part, "rig_paint_grey", [riser_top, riser_top + V(0.0, 0.0, 0.5), V(x, riser_top.y, barrel_z), V(x, riser_top.y + 1.2, barrel_z)], 0.25, 12, 0.5)
        ok.gate_valve(part, "rig_paint_grey", V(x, riser_top.y + 0.8, barrel_z), V(0.0, 1.0, 0.0), 0.25, True, up)
        a = V(x, riser_top.y + 1.4, barrel_z)
        c = V(x, 18.6, barrel_z)
        tube(part, "rig_paint_orange", a, a + V(0.0, 0.5, 0.0), 0.25, 14)
        ok.lathe(part, "rig_paint_orange", a + V(0.0, 0.5, 0.0), V(0.0, 1.0, 0.0), [(0.0, 0.0), (0.25, 0.0), (0.4, 0.4), (0.4, 0.0 + (c.y - a.y) - 0.5), (0.0, (c.y - a.y) - 0.5)], 16)
        door = c + V(0.0, 0.05, 0.0)
        ok.lathe(part, "rig_paint_orange", door, V(0.0, 1.0, 0.0), [(0.0, 0.0), (0.56, 0.0), (0.56, 0.16), (0.42, 0.2), (0.0, 0.22)], 16)
        box(part, "rig_steel", x + 0.5, x + 0.62, door.y + 0.02, door.y + 0.14, barrel_z - 0.1, barrel_z + 0.1)
        ok.handwheel(part, "rig_paint_yellow", door + V(0.0, 0.3, 0.0), V(0.0, 1.0, 0.0), 0.25)
        for t in (0.3, 0.75):
            p = a.lerp(c, t)
            ok.saddle(part, "rig_paint_grey", p + V(0.0, 0.0, 0.0), V(0.0, 1.0, 0.0), 0.4, 0.25, barrel_z - 0.4 - z)
        ok.pipe(part, "rig_paint_grey", [a.lerp(c, 0.2) + V(0.0, 0.0, 0.4), a.lerp(c, 0.2) + V(0.0, 0.0, 1.4), V(x - 1.2, a.lerp(c, 0.2).y, barrel_z + 1.4), V(x - 1.2, 11.0, barrel_z + 1.4), V(x - 1.2, 11.0, top - 1.6)], 0.1, 8, 0.3)
        gauge = a.lerp(c, 0.55) + V(0.0, 0.0, 0.42)
        tube(part, "rig_steel", gauge, gauge + V(0.0, 0.0, 0.25), 0.015, 5)
        ok.lathe(part, "rig_steel", gauge + V(0.0, 0.0, 0.25), V(0.0, -1.0, 0.0), [(0.0, 0.0), (0.07, 0.0), (0.07, 0.05), (0.0, 0.05)], 10, False)
        col(b, "metal", "pig", x - 0.45, x + 0.45, riser_top.y, c.y + 0.3, z, barrel_z + 0.6)
    ok.sign(parts["fittings"], "danger", V(7.8, 19.85, z + 1.6), V(0.0, -1.0, 0.0), 1.2, 0.2)


def tanks_and_room(b, parts, rng):
    part = parts["equipment"]
    for x, y, r, h in tanks:
        ok.lathe(part, "rig_paint_white", V(x, y, z + 0.25), up, [(0.0, 0.0), (r, 0.0), (r, h), (r * 0.6, h + 0.25), (0.0, h + 0.3)], 22)
        for k in range(4):
            angle = math.pi * 0.5 * k + 0.4
            p = V(x + math.cos(angle) * (r - 0.1), y + math.sin(angle) * (r - 0.1), z)
            box(part, "rig_paint_grey", p.x - 0.08, p.x + 0.08, p.y - 0.08, p.y + 0.08, z, z + 0.4)
        ok.ladder(part, V(x + r + 0.45, y, z), z + 0.25 + h, V(-1.0, 0.0, 0.0), 0.45, "rig_paint_yellow", True, 2.4)
        col(b, "metal", "tank", x - r, x + r, y - r, y + r, z, z + h + 0.5)
        tube(part, "rig_paint_grey", V(x, y + r * 0.7, z + h + 0.5), V(x, y + r * 0.7, top - 0.3), 0.06, 8)
    ok.sign(parts["fittings"], "no_smoking", V(tanks[0][0], tanks[0][1] - tanks[0][2] - 0.02, z + 1.8), V(0.0, -1.0, 0.0), 0.55, 0.2)
    x0, x1, y0, y1 = mcc
    h = 3.4
    shell = parts["deck"]
    t = 0.08
    door = (19.0, 20.2)
    vents = []
    walls = [("y0", x0, x1, y0), ("y1", x0, x1, y1)]
    for key, a, c, yy in walls:
        holes = [(door[0], door[1])] if key == "y1" else []
        cuts = sorted(set([a, c] + [p for hole in holes for p in hole]))
        for s, e in zip(cuts[:-1], cuts[1:]):
            inside = any(hs <= (s + e) * 0.5 <= he for hs, he in holes)
            if inside:
                box(shell, "rig_paint_white", s, e, yy - t * 0.5, yy + t * 0.5, z + 2.15, z + h)
                continue
            box(shell, "rig_paint_white", s, e, yy - t * 0.5, yy + t * 0.5, z, z + h)
            col(b, "metal", "room", s, e, yy - t * 0.5, yy + t * 0.5, z, z + h)
    for xx in (x0, x1):
        box(shell, "rig_paint_white", xx - t * 0.5, xx + t * 0.5, y0, y1, z, z + h)
        col(b, "metal", "room", xx - t * 0.5, xx + t * 0.5, y0, y1, z, z + h)
    box(shell, "rig_paint_white", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z + h, z + h + 0.12)
    ok.plate_floor(b, shell, x0, x1, y0, y1, z + 0.02, "rig_vinyl", (), 0.02, "metal", "room_floor", False)
    box(shell, "rig_ceiling", x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, z + h - 0.05, z + h - 0.02, "world")
    for k in range(4):
        cx = x0 + 1.5 + k * 1.9
        box(part, "rig_paint_grey", cx - 0.8, cx + 0.8, y0 + 0.08, y0 + 0.68, z, z + 2.1)
        tk_panel(part, V(cx, y0 + 0.69, z + 1.3), V(0.0, 1.0, 0.0), 1.4, 1.0, "console" if k % 2 == 0 else "mimic")
        col(b, "metal", "cabinet", cx - 0.8, cx + 0.8, y0 + 0.08, y0 + 0.68, z, z + 2.1)
    for cx in (17.2, 22.8):
        box(part, "rig_paint_grey", cx - 1.0, cx + 1.0, y1 - 0.68, y1 - 0.08, z, z + 2.1)
        col(b, "metal", "cabinet", cx - 1.0, cx + 1.0, y1 - 0.68, y1 - 0.08, z, z + 2.1)
    ok.sign(parts["fittings"], "danger", V((door[0] + door[1]) * 0.5, y1 + 0.06, z + 2.5), V(0.0, 1.0, 0.0), 1.2, 0.2)
    ok.strip_light(b, part, V((x0 + x1) * 0.5, (y0 + y1) * 0.5, z + h - 0.06), 1.2, True, "cold", True)
    b.loot("box", V(x1 - 0.8, (y0 + y1) * 0.5, z + 0.04))
    for yy in (y0 + 1.5, y1 - 1.5):
        box(shell, "rig_steel", x1 + 0.04, x1 + 0.08, yy - 0.5, yy + 0.5, z + 2.2, z + 2.9)


def tk_panel(part, center, normal, width, height, key):
    tk.atlas_panel(part, "rig_signs", center, normal, width, height, lib.region_uv(lib.signs, key), 0.0, 0.003)


def overhead(b, parts, rng):
    services = parts["services"]
    for y in (-8.0, 7.0):
        a = V(-23.5, y, top - 0.6)
        c = V(23.5, y, top - 0.6)
        ok.cable_tray(services, a, c, 0.6, rng, "rig_paint_grey", 6, 2.2)
        for x in range(-22, 24, 4):
            tube(services, "rig_paint_grey", V(x, y - 0.3, top - 0.6), V(x, y - 0.3, top), 0.025, 5)
            tube(services, "rig_paint_grey", V(x, y + 0.3, top - 0.6), V(x, y + 0.3, top), 0.025, 5)
    for k in range(9):
        x = rng.uniform(-22.0, 22.0)
        y = rng.choice([-8.0, 7.0])
        ok.hanging_cable(services, V(x, y + rng.uniform(-0.25, 0.25), top - 0.66), rng.uniform(1.2, 4.6), rng, 0.016 + rng.uniform(0.0, 0.01))
    for y, radius in ((-10.6, 0.16), (-11.1, 0.12), (10.0, 0.2), (9.4, 0.14), (8.9, 0.1)):
        a = V(-24.0, y, top - 1.1)
        c = V(24.0, y, top - 1.1)
        tube(services, "rig_paint_grey", a, c, radius, 10)
        for x in range(-22, 24, 6):
            tube(services, "rig_paint_grey", V(x, y, top - 1.1 + radius), V(x, y, top), 0.02, 5)
            ok.ring(services, "rig_paint_grey", V(x, y, top - 1.1), V(1.0, 0.0, 0.0), radius, 0.01, 0.05, 10)
    lights = [(-18.0, -15.0, True), (-6.0, -15.5, False), (8.0, -14.0, True), (18.0, -6.0, True), (-18.0, 4.0, True), (-2.0, 12.0, False), (10.0, 6.0, True), (20.0, 14.0, False), (-12.0, -8.0, True), (2.0, -4.0, True), (-20.0, 17.5, True), (14.0, 17.5, True)]
    for x, y, lit in lights:
        ok.floodlight(b, services, parts["lamps"], V(x, y, top - 0.45), V(0.0, 0.2, -1.0), "cold", lit, not lit, rng, V(x, y, top))
        if not lit:
            ok.hanging_cable(services, V(x, y, top - 0.5), rng.uniform(0.5, 1.4), rng)


def dressing(b, parts, rng):
    part = parts["clutter"]
    decals = parts["decals"]
    spots = [(-21.0, -16.0), (-16.0, -6.5), (-0.5, -10.0), (20.5, -10.0), (2.0, 10.5), (-23.0, 10.6), (18.6, 18.6), (-3.0, 18.5)]
    kinds = ["box", "box", "box", "box", "box", "box", "box", "box"]
    for (x, y), kind in zip(spots, kinds):
        b.loot(kind, V(x, y, z))
    for x, y in ((-19.0, -12.6), (-8.0, -13.0), (13.0, -8.5), (-11.0, 9.0), (10.5, 9.5), (23.0, -3.0)):
        lying = rng.random() < 0.3
        ok.drum(part, V(x, y, z), rng, rng.choice(["rig_paint_grey", "rig_paint_orange", "rig_rust"]), lying, rng.uniform(0.0, 6.0))
        if not lying:
            col(b, "metal", "drum", x - 0.3, x + 0.3, y - 0.3, y + 0.3, z, z + 0.88)
    for x, y, yaw in ((-19.5, -17.6, 0.3), (17.0, 11.0, 1.2), (-1.5, 15.5, 0.0)):
        ok.pallet(part, V(x, y, z), yaw, rng)
        col(b, "wood", "pallet", x - 0.7, x + 0.7, y - 0.7, y + 0.7, z, z + 0.14)
    ok.crate(part, V(-19.5, -17.6, z + 0.14), (1.0, 0.8, 0.7), 0.3, rng)
    col(b, "wood", "crate", -20.1, -18.9, -18.2, -17.0, z, z + 0.85)
    for k in range(5):
        x = rng.uniform(-22.0, -16.0)
        y = rng.uniform(-10.0, -7.0)
        ok.gas_cylinder(part, V(x, y, z), rng, rng.choice(["rig_paint_grey", "rig_paint_orange", "rig_deck_green"]), k % 3 == 0, rng.uniform(0.0, 6.0))
    for k in range(4):
        ok.sack(part, V(16.6 + rng.uniform(-0.3, 0.3), 12.8 + k * 0.5, z), rng)
    for k in range(18):
        x = rng.uniform(-24.0, 24.0)
        y = rng.uniform(-19.0, 19.0)
        ok.floor_decal(decals, rng.choice(["guano_a", "guano_b", "oil_a", "salt"]), x, y, z + 0.008, rng.uniform(0.8, 1.6), rng.uniform(0.8, 1.6), rng.uniform(0.0, 6.0))
    for k in range(5):
        x = rng.uniform(-22.0, 22.0)
        y = rng.choice([-8.0, 7.0])
        ok.nest(part, V(x, y + rng.uniform(-0.1, 0.1), top - 0.6 + 0.02), rng)
    for x0, x1, y, r in ((separator_a[0], separator_a[1], separator_a[2], separator_a[3]), (separator_b[0], separator_b[1], separator_b[2], separator_b[3])):
        cz = z + 0.7 + r
        for k in range(3):
            xx = rng.uniform(x0 + 0.5, x1 - 0.5)
            ok.decal(decals, rng.choice(["run_a", "run_b", "run_c"]), V(xx, y - r * 0.92 - 0.02, cz - r * 0.35), V(0.0, -1.0, 0.0), 0.3, 1.2)
    ok.sign(parts["fittings"], "muster", V(-24.85, -12.5, z + 1.7), V(1.0, 0.0, 0.0), 1.2, 0.22)
    ok.sign(parts["fittings"], "escape", V(1.0, -19.85, z + 1.6), V(0.0, 1.0, 0.0), 0.6, 0.22)


def damage(b, parts, rng):
    x0, x1, y0, y1 = collapse
    rails = parts["rails"]
    grate = parts["grating"]
    for k in range(3):
        hinge_y = y0 + 0.3 + k * 1.0
        corners = [V(x0, hinge_y, z - 0.02), V(x0, hinge_y + 0.9, z - 0.02), V(x0 + 0.9 * math.cos(1.2 + k * 0.15), hinge_y + 0.9, z - 0.02 - 0.9 * math.sin(1.2 + k * 0.15)), V(x0 + 0.9 * math.cos(1.2 + k * 0.15), hinge_y, z - 0.02 - 0.9 * math.sin(1.2 + k * 0.15))]
        if k != 1:
            emit(grate, Geo(corners, [(0, 1, 2, 3)]), "rig_grating", None, "world")
    hanging = [V(x1, y0 + 0.6, z - 0.03), V(x1, y0 + 1.6, z - 0.03), V(x1 - 0.4, y0 + 1.6, z - 1.0), V(x1 - 0.35, y0 + 0.6, z - 1.05)]
    emit(grate, Geo(hanging, [(0, 1, 2, 3)]), "rig_grating", None, "world")
    for px, py, lean in ((x0, y0, V(0.3, 0.4, -0.2)), (x0 + 1.5, y0, V(0.1, 0.6, -0.5)), (x1, y0, V(-0.2, 0.3, 0.0))):
        tube(rails, "rig_paint_yellow", V(px, py, z), V(px, py, z) + (V(0.0, 0.0, 1.0) + lean).normalized() * 1.1, 0.024, 6, True, ok.fine)
    ok.path_tube(rails, "rig_paint_yellow", [V(x0, y0, z + 1.05), V(x0 + 1.4, y0 + 0.5, z + 0.7), V(x1 - 0.2, y0 + 0.3, z + 1.0)], 0.025, 6, True, ok.fine)
    ok.path_tube(rails, "rig_paint_yellow", [V(x0, y0, z + 0.6), V(x0 + 0.8, y0 + 0.9, z - 0.2), V(x0 + 1.2, y0 + 1.6, z - 1.4)], 0.02, 6, True, ok.fine)
    col(b, "metal", "collapse_rail", x0 - 0.05, x1, y0 - 0.05, y0 + 0.05, z, z + 1.1)
    col(b, "metal", "collapse_rail", x0 - 0.05, x0 + 0.05, y0, y1, z, z + 1.1)
    ok.sign(parts["fittings"], "danger", V(x0 - 0.1, (y0 + y1) * 0.5, z + 1.0), V(-1.0, 0.0, 0.0), 1.0, 0.17)
    decals = parts["decals"]
    for side, fixed, lo, hi, normal in (("s", -20.18, -24.0, 24.0, V(0.0, -1.0, 0.0)), ("n", 20.18, -24.0, 24.0, V(0.0, 1.0, 0.0)), ("w", -25.18, -19.0, 19.0, V(-1.0, 0.0, 0.0)), ("e", 25.18, -19.0, 19.0, V(1.0, 0.0, 0.0))):
        a = lo
        while a < hi:
            if rng.random() < 0.7:
                center = V(a, fixed, z - 0.55) if side in ("s", "n") else V(fixed, a, z - 0.55)
                ok.decal(decals, rng.choice(["runs_wide", "runs_wide", "run_c", "run_a"]), center, normal, rng.uniform(1.2, 2.2), rng.uniform(0.8, 1.1))
            a += rng.uniform(2.5, 4.5)


def process_extras(b, parts, rng):
    part = parts["equipment"]
    sx, sy, r, h = scrubber
    ok.vessel(part, "rig_paint_white", V(sx, sy, z + 1.0), V(sx, sy, z + 1.0 + h - 1.6), r, 20, 0.5)
    for k in range(4):
        angle = math.pi * 0.5 * k + 0.785
        foot = V(sx + math.cos(angle) * r * 0.8, sy + math.sin(angle) * r * 0.8, z)
        tube(part, "rig_paint_grey", foot, foot + V(0.0, 0.0, 1.3), 0.06, 6)
    ok.ladder(part, V(sx - r - 0.45, sy, z), z + h - 0.4, V(1.0, 0.0, 0.0), 0.45, "rig_paint_yellow", True, 2.4)
    tube(part, "rig_paint_white", V(sx, sy, z + h), V(sx, sy, top - 0.4), 0.15, 10)
    ok.pipe(part, "rig_paint_grey", [V(sx + r, sy, z + 2.2), V(sx + r + 0.8, sy, z + 2.2), V(sx + r + 0.8, sy, top - 1.6), V(sx + r + 0.8, 12.6, top - 1.6)], 0.12, 10, 0.3)
    gauge_x = sx - r - 0.15
    tube(part, "rig_steel", V(gauge_x, sy + 0.3, z + 1.6), V(gauge_x, sy + 0.3, z + 3.2), 0.035, 6)
    col(b, "metal", "scrubber", sx - r, sx + r, sy - r, sy + r, z, z + h)
    x0, x1, y, er = exchanger
    cz = z + 1.1
    tube(part, "rig_paint_grey", V(x0 + 0.6, y, cz), V(x1, y, cz), er, 18)
    ok.lathe(part, "rig_paint_grey", V(x0 + 0.6, y, cz), V(-1.0, 0.0, 0.0), [(0.0, 0.0), (er + 0.08, 0.0), (er + 0.08, 0.06), (er, 0.08), (er, 0.5), (er + 0.08, 0.52), (er + 0.08, 0.6), (0.0, 0.62)], 18)
    ok.lathe(part, "rig_paint_grey", V(x1, y, cz), V(1.0, 0.0, 0.0), [(0.0, 0.0), (er + 0.06, 0.0), (er + 0.06, 0.05), (0.0, 0.25)], 18)
    for t in (0.25, 0.8):
        ok.saddle(part, "rig_paint_grey", V(x0 + (x1 - x0) * t, y, cz), V(1.0, 0.0, 0.0), er, 0.25, cz - er - z)
    for nx in (x0 + 0.9, x1 - 0.6):
        tube(part, "rig_paint_grey", V(nx, y, cz + er), V(nx, y, cz + er + 0.45), 0.1, 8)
        ok.flange(part, "rig_paint_grey", V(nx, y, cz + er + 0.45), up, 0.1, 10)
    ok.pipe(part, "rig_paint_grey", [V(x0 + 0.9, y, cz + er + 0.5), V(x0 + 0.9, y, top - 1.1), V(x0 + 0.9, 10.0, top - 1.1)], 0.1, 8, 0.3)
    col(b, "metal", "exchanger", x0, x1 + 0.3, y - er - 0.1, y + er + 0.1, z, cz + er)
    ix, iy = injection
    box(part, "rig_paint_grey", ix - 1.0, ix + 1.0, iy - 0.75, iy + 0.75, z, z + 0.15)
    ok.lathe(part, "rig_paint_white", V(ix - 0.45, iy, z + 0.15), up, [(0.0, 0.0), (0.5, 0.0), (0.5, 1.3), (0.35, 1.45), (0.0, 1.45)], 14)
    for k in range(2):
        px = ix + 0.35 + k * 0.45
        box(part, "rig_paint_orange", px - 0.15, px + 0.15, iy - 0.35, iy + 0.05, z + 0.15, z + 0.55, "box", 0.02)
        ok.lathe(part, "rig_paint_grey", V(px, iy + 0.05, z + 0.35), V(0.0, 1.0, 0.0), [(0.0, 0.0), (0.12, 0.0), (0.12, 0.35), (0.0, 0.35)], 10)
        ok.pipe(part, "rig_steel", [V(px, iy - 0.35, z + 0.45), V(px, iy - 0.6, z + 0.45), V(px, iy - 0.6, z + 2.2)], 0.02, 6, 0.08)
    col(b, "metal", "injection", ix - 1.0, ix + 1.0, iy - 0.75, iy + 0.75, z, z + 1.6)


def cellar():
    b = kit.Build("rig_cellar", 7201)
    rng = b.rng
    parts = ok.setup(b, (("structure", 50.0), ("deck", 40.0), ("equipment", 45.0), ("services", 50.0), ("clutter", 45.0), ("fittings", 40.0), ("rails", 50.0), ("lamps", 30.0), ("grating", 30.0), ("decals", 30.0)))
    framing(b, parts, rng)
    floors(b, parts, rng)
    railings(b, parts, rng)
    cellar_stairs(b, parts, rng)
    wellbay(b, parts, rng)
    separator(b, parts, separator_a[0], separator_a[1], separator_a[2], separator_a[3], rng, None)
    separator(b, parts, separator_b[0], separator_b[1], separator_b[2], separator_b[3], rng, None)
    pumps(b, parts, rng)
    caisson_pumps(b, parts, rng)
    pig_traps(b, parts, rng)
    tanks_and_room(b, parts, rng)
    overhead(b, parts, rng)
    dressing(b, parts, rng)
    damage(b, parts, rng)
    process_extras(b, parts, rng)
    return b


def cellar_far():
    b = kit.Build("rig_cellar_far", 7202)
    part = b.part("shell", 40.0)
    grate = b.part("grating", 30.0)
    dx, dy = ok.deck_x, ok.deck_y
    holes = [(ok.tower[0], ok.tower_runs[1], ok.tower[2], ok.tower[3]), collapse] + plate_zones
    outline = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
    loops = [[(h[0], h[2]), (h[1], h[2]), (h[1], h[3]), (h[0], h[3])] for h in holes]
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), outline, loops, z - 0.002, z, False)
    geo.faces = [face for face in geo.faces if kit.newell([geo.points[i] for i in face]).z > 0.0]
    emit(grate, geo, "rig_grating", None, "world")
    x0, x1, y0, y1 = collapse
    hanging = [V(x1, y0 + 0.6, z - 0.03), V(x1, y0 + 1.6, z - 0.03), V(x1 - 0.4, y0 + 1.6, z - 1.0), V(x1 - 0.35, y0 + 0.6, z - 1.05)]
    emit(grate, Geo(hanging, [(0, 1, 2, 3)]), "rig_grating", None, "world")
    for px0, px1, py0, py1 in plate_zones:
        ok.far_box(part, "rig_deck_green", px0, px1, py0, py1, z - 0.03, z, (), 1.0, "world")
    for sy in (-1.0, 1.0):
        ok.far_box(part, frame_paint, -dx, dx, sy * ok.leg_y - 0.22, sy * ok.leg_y + 0.22, z - 1.0, z - 0.01)
        ok.far_box(part, frame_paint, -dx, dx, sy * dy - 0.15, sy * dy + 0.15, z - 0.6, z - 0.01)
    for sx in (-1.0, 1.0):
        ok.far_box(part, frame_paint, sx * ok.leg_x - 0.22, sx * ok.leg_x + 0.22, -dy, dy, z - 1.0, z - 0.01)
        ok.far_box(part, frame_paint, sx * dx - 0.15, sx * dx + 0.15, -dy, dy, z - 0.6, z - 0.01)
    y = -dy + 2.5
    while y < dy - 1.0:
        if abs(abs(y) - ok.leg_y) > 0.6:
            pieces = [(-dx, dx)]
            if ok.tower[2] - 0.2 < y < ok.tower[3] + 0.2:
                pieces = [(-dx, ok.tower[0] - 0.1), (ok.tower_runs[1] + 0.1, dx)]
            for a, c in pieces:
                ok.far_box(part, frame_paint, a, c, y - 0.09, y + 0.09, z - 0.42, z - 0.02, ("left", "right"))
        y += 2.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            ok.far_tube(part, frame_paint, V(sx * ok.leg_x, sy * ok.leg_y, z - 0.6), V(sx * ok.leg_x, sy * ok.leg_y, top + 0.05), 0.8, 10)
    columns = []
    for sy in (-1.0, 1.0):
        xs = truss_y[0]
        columns += [(x, sy * ok.leg_y) for x in xs if abs(x) < 14.0] + [(-25.0, sy * ok.leg_y), (25.0, sy * ok.leg_y)]
        for index in range(len(xs) - 1):
            a = xs[index]
            c = xs[index + 1]
            rising = (index % 2 == 0) == (sy > 0)
            ok.far_tube(part, frame_paint, V(a if rising else c, sy * ok.leg_y, z + 0.1), V(c if rising else a, sy * ok.leg_y, top - 0.1), 0.22, 6)
    for sx in (-1.0, 1.0):
        ys = truss_x[0]
        columns += [(sx * ok.leg_x, y) for y in ys if abs(y) < 11.0] + [(sx * ok.leg_x, -20.0), (sx * ok.leg_x, 20.0)]
        for index in range(len(ys) - 1):
            a = ys[index]
            c = ys[index + 1]
            rising = (index % 2 == 0) == (sx > 0)
            ok.far_tube(part, frame_paint, V(sx * ok.leg_x, a if rising else c, z + 0.1), V(sx * ok.leg_x, c if rising else a, top - 0.1), 0.22, 6)
    columns += [(x, y) for x in (-25.0, -5.0, 5.0, 25.0) for y in (-20.0, 20.0)] + [(-25.0, 0.0), (25.0, 0.0)]
    for x, y in columns:
        ok.far_post(part, frame_paint, x, y, z, top, 0.18, 1.4)
    e = 0.1
    ok.far_rail(part, [(-dx + e, -dy + e), (dx - e, -dy + e), (dx - e, dy - e), (-dx + e, dy - e), (-dx + e, -dy + e)], z)
    tx0, tx1, ty0, ty1 = ok.tower
    ok.far_rail(part, [(ok.tower_runs[1], ty0), (tx0, ty0), (tx0, ty1), (ok.tower_runs[1], ty1)], z, 1.1, "rig_paint_yellow", 3.2)
    cellar_stairs_far(part, grate)
    equipment_far(part)
    return b


def cellar_stairs_far(part, grate):
    sx0, sx1, sy0, sy1 = ok.cellar_stair
    split = ok.cellar_stair_split
    run0, run1 = ok.cellar_stair_runs
    mid = (z + ok.main) * 0.5
    ok.far_stair(part, grate, run0, run1, sy0 + 0.05, split - 0.05, z, mid, "px")
    ok.far_stair(part, grate, run0, run1, split + 0.05, sy1 - 0.05, mid, ok.main, "nx")
    ok.flat_quad(grate, "rig_grating", run1, sx1, sy0, sy1, mid)
    for cx in (run1, sx1):
        for cy in (sy0, sy1):
            ok.far_post(part, "rig_paint_grey", cx, cy, z, mid, 0.09)
    ok.far_rail(part, [(sx1, sy0), (sx1, sy1), (run1, sy1)], mid, 1.1, "rig_paint_yellow", 2.4)


def equipment_far(part):
    for x, y in ok.wells:
        ok.far_box(part, "rig_paint_grey", x - 0.42, x + 0.42, y - 0.42, y + 0.42, z, z + 0.68, ("bottom",))
        ok.far_box(part, "rig_paint_orange", x - 0.3, x + 0.3, y - 0.3, y + 0.3, z + 0.68, z + 2.96, ("bottom",))
        ok.far_box(part, "rig_paint_orange", x + 0.24, x + 1.1, y - 0.15, y + 0.15, z + 1.7, z + 2.0, ("left",))
    hz = z + 1.05
    ok.far_tube(part, "rig_paint_grey", V(-1.4, 1.6, hz), V(-1.4, 8.2, hz), 0.2, 6)
    ok.far_path(part, "rig_paint_grey", [V(-1.4, 8.2, hz), V(-1.4, 10.6, hz), V(-1.4, 10.6, z + 4.6), V(-4.0, 10.6, z + 4.6), V(-7.6, 14.4, z + 4.6), V(-7.6, 16.2, z + 3.2)], 0.16, 6, 1.0)
    for x0, x1, y, r in (separator_a, separator_b):
        cz = z + 0.7 + r
        length = x1 - x0
        profile = [(0.0, -r * 0.5), (r * 0.72, -r * 0.36), (r, 0.0), (r, length), (r * 0.72, length + r * 0.36), (0.0, length + r * 0.5)]
        ok.lathe(part, "rig_paint_white", V(x0, y, cz), V(1.0, 0.0, 0.0), profile, 10, True)
        for t in (0.15, 0.85):
            sx = x0 + length * t
            ok.far_box(part, "rig_paint_grey", sx - 0.15, sx + 0.15, y - r * 0.85, y + r * 0.85, z, cz - r * 0.55, ("bottom",))
        for t in (0.2, 0.5, 0.8):
            nx = x0 + length * t
            ok.far_tube(part, "rig_paint_white", V(nx, y, cz + r * 0.9), V(nx, y, cz + r + 0.45), 0.17, 4)
    sx, sy, r, h = scrubber
    ok.lathe(part, "rig_paint_white", V(sx, sy, z + 1.0), up, [(0.0, -r * 0.5), (r * 0.72, -r * 0.36), (r, 0.0), (r, h - 1.6), (r * 0.72, h - 1.6 + r * 0.36), (0.0, h - 1.6 + r * 0.5)], 10, True)
    ok.far_tube(part, "rig_paint_white", V(sx, sy, z + h), V(sx, sy, top - 0.4), 0.15, 4)
    for index in range(3):
        x = 4.6 + index * 2.9
        ok.far_box(part, "rig_paint_grey", x - 0.5, x + 0.5, -5.6, -0.4, z, z + 0.2, ("bottom",))
        ok.far_tube(part, "rig_paint_grey" if index != 1 else "rig_paint_orange", V(x, -5.0, z + 0.75), V(x, -3.75, z + 0.75), 0.42, 8)
        ok.far_tube(part, "rig_paint_grey", V(x, -2.45, z + 0.75), V(x, -1.95, z + 0.75), 0.48, 8)
        ok.far_path(part, "rig_paint_grey", [V(x, -2.2, z + 1.2), V(x, -2.2, z + 2.15), V(x, -4.4, z + 2.15), V(x, -6.6, top - 1.2), V(x, -9.0, top - 1.2)], 0.12, 4, 1.0)
    for x, y in oj.caissons:
        ok.far_tube(part, "rig_paint_grey", V(x, y, z - 0.2), V(x, y, z + 0.4), 0.62, 8)
        ok.lathe(part, "rig_paint_orange", V(x, y, z + 0.4), up, [(0.46, 0.0), (0.46, 1.3), (0.18, 1.48), (0.0, 1.62)], 8, True)
        ok.far_path(part, "rig_paint_grey", [V(x + 0.5, y, z + 0.2), V(x + 1.4, y, z + 0.2), V(x + 1.4, y, z + 3.6), V(x + 4.0, y, z + 3.6)], 0.14, 4, 1.0)
    for x in oj.riser_xs:
        riser_top = V(x, oj.face_y(oj.top_z + 0.6) + 0.9, oj.top_z + 0.6)
        barrel_z = z + 1.1
        ok.far_path(part, "rig_paint_grey", [riser_top, V(x, riser_top.y, barrel_z), V(x, riser_top.y + 1.4, barrel_z)], 0.25, 6, 1.0)
        ok.far_tube(part, "rig_paint_orange", V(x, riser_top.y + 1.4, barrel_z), V(x, riser_top.y + 1.9, barrel_z), 0.25, 6)
        tube(part, "rig_paint_orange", V(x, riser_top.y + 1.9, barrel_z), V(x, 18.65, barrel_z), 0.4, 8, True)
        ok.far_box(part, "rig_paint_grey", x - 0.38, x + 0.38, 17.0, 17.25, z, barrel_z - 0.3, ("bottom",))
    for x, y, r, h in tanks:
        ok.lathe(part, "rig_paint_white", V(x, y, z + 0.25), up, [(r, 0.0), (r, h), (r * 0.6, h + 0.25), (0.0, h + 0.3)], 10, True)
        ok.far_tube(part, "rig_paint_grey", V(x, y, z), V(x, y, z + 0.25), r * 0.8, 4)
    x0, x1, y0, y1 = mcc
    ok.far_box(part, "rig_paint_white", x0, x1, y0, y1, z, z + 3.4, ("bottom",))
    ok.far_box(part, "rig_paint_white", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z + 3.4, z + 3.52)
    ok.far_panel(part, "soot", (19.0, y1 + 0.01), (20.2, y1 + 0.01), z, z + 2.15, V(0.0, 1.0, 0.0))
    ex0, ex1, ey, er = exchanger
    tube(part, "rig_paint_grey", V(ex0, ey, z + 1.1), V(ex1 + 0.2, ey, z + 1.1), er, 8, True)
    ix, iy = injection
    ok.far_box(part, "rig_paint_grey", ix - 1.0, ix + 1.0, iy - 0.75, iy + 0.75, z, z + 0.15, ("bottom",))
    ok.far_tube(part, "rig_paint_white", V(ix - 0.45, iy, z + 0.15), V(ix - 0.45, iy, z + 1.45), 0.5, 6)
    for y in (-8.0, 7.0):
        ok.far_box(part, "rig_paint_grey", -23.5, 23.5, y - 0.3, y + 0.3, top - 0.66, top - 0.56, ("left", "right"))
    for y, radius in ((-10.6, 0.16), (-11.1, 0.12), (10.0, 0.2), (9.4, 0.14), (8.9, 0.1)):
        ok.far_tube(part, "rig_paint_grey", V(-24.0, y, top - 1.1), V(24.0, y, top - 1.1), radius, 6 if radius > 0.13 else 4)
