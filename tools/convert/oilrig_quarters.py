import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import buildings as bd
import railkit as rk
import town_kit as tk
import town_props as tp
import oilrig_library as lib
import oilrig_kit as ok
from buildkit import V, Geo, emit
from oilrig_kit import box, col, tube, up

X0, X1, Y0, Y1 = ok.quarters
T = 0.2
IX0, IX1, IY0, IY1 = X0 + T, X1 - T, Y0 + T, Y1 - T
CX0, CX1 = 17.9, 19.3
PT = 0.1
FLOORS = ok.floors
ROOF = ok.roof
STAIR = (19.3, 24.8, -11.8, -9.2)
LAND = 20.7
RUN1 = 23.0
LANE1 = (-11.75, -10.55)
LANE2 = (-10.45, -9.25)
DOOR_H = 2.15
WIN = (1.0, 2.05)
VOID = (LAND, IX1, IY0, STAIR[3])
face_east = math.pi * 0.5
face_west = -math.pi * 0.5
face_north = math.pi
face_south = 0.0

plans = [
    {
        "west": [("lobby", -11.8, -7.0, (-11.0, -9.8)), ("locker", -7.0, -1.0, (-4.6, -3.4)), ("galley", -1.0, 5.0, (0.2, 1.4)), ("mess", 5.0, 11.8, (8.4, 9.6))],
        "east": [("wc", -9.2, -7.0, (-8.7, -7.6)), ("laundry", -7.0, -2.0, (-5.6, -4.5)), ("recreation", -2.0, 5.0, (0.0, 1.2)), ("provisions", 5.0, 11.8, (6.0, 7.2))],
        "west_windows": [(-8.6, -7.4), (2.0, 3.2), (6.4, 7.8), (9.6, 11.0)],
        "east_windows": [(0.2, 1.6), (2.8, 4.2)],
        "north_windows": [(13.6, 15.0)],
        "south_windows": [],
    },
    {
        "west": [("medical", -11.8, -7.0, (-9.1, -8.0)), ("cabin", -7.0, -2.5, (-3.7, -2.6)), ("cabin", -2.5, 2.0, (0.8, 1.9)), ("cabin", 2.0, 6.5, (5.3, 6.4)), ("cabin", 6.5, 11.8, (10.5, 11.6))],
        "east": [("wc", -9.2, -7.0, (-8.7, -7.6)), ("showers", -7.0, -2.5, (-5.0, -3.9)), ("cabin", -2.5, 2.0, (-2.3, -1.2)), ("cabin", 2.0, 6.5, (2.2, 3.3)), ("cabin", 6.5, 11.8, (6.7, 7.8))],
        "west_windows": [(-10.4, -9.0), (-5.4, -4.2), (-0.9, 0.3), (3.6, 4.8), (8.4, 9.8)],
        "east_windows": [(-0.6, 0.6), (3.8, 5.0), (8.6, 9.8)],
        "north_windows": [(13.6, 15.0), (21.2, 22.6)],
        "south_windows": [(13.8, 15.2)],
    },
    {
        "west": [("oim", -11.8, -7.0, (-9.1, -8.0)), ("office", -7.0, -1.0, (-2.4, -1.3)), ("control", -1.0, 11.8, (0.0, 1.1))],
        "east": [("wc", -9.2, -7.0, (-8.7, -7.6)), ("radio", -7.0, -2.5, (-3.7, -2.6)), ("meeting", -2.5, 5.0, (-2.3, -1.2)), ("archive", 5.0, 11.8, (5.3, 6.4))],
        "west_windows": [(-10.4, -9.0), (-5.0, -3.6), (0.6, 2.2), (3.6, 5.2), (6.6, 8.2), (9.6, 11.2)],
        "east_windows": [(-5.4, -4.0), (-0.4, 1.0), (2.6, 4.0), (8.0, 9.4)],
        "north_windows": [(13.6, 15.0), (21.2, 22.6)],
        "south_windows": [(13.8, 15.2)],
    },
]


def segments(a0, a1, z0, z1, openings):
    cuts = sorted(set([a0, a1] + [c for o in openings for c in (o[0], o[1]) if a0 < c < a1]))
    out = []
    for c0, c1 in zip(cuts[:-1], cuts[1:]):
        middle = (c0 + c1) * 0.5
        blocked = sorted((o[2], o[3]) for o in openings if o[0] <= middle <= o[1])
        start = z0
        for lo, hi in blocked:
            if lo > start + 0.01:
                out.append((c0, c1, start, min(lo, z1)))
            start = max(start, hi)
        if start < z1 - 0.01:
            out.append((c0, c1, start, z1))
    return out


def wall_line(b, parts, axis, fixed, a0, a1, z0, z1, openings, thickness, outer=None, outer_sign=0.0, tag="wall", collide=True, inner_name="rig_wall"):
    for s, e, zs, ze in segments(a0, a1, z0, z1, openings):
        if axis == "x":
            lo = V(s, fixed - thickness * 0.5, zs)
            hi = V(e, fixed + thickness * 0.5, ze)
        else:
            lo = V(fixed - thickness * 0.5, s, zs)
            hi = V(fixed + thickness * 0.5, e, ze)
        if outer is None:
            box(parts["walls"], inner_name, lo.x, hi.x, lo.y, hi.y, zs, ze, "world")
        else:
            split = fixed + outer_sign * (thickness * 0.5 - 0.11)
            if axis == "x":
                ylo, yhi = (split, hi.y) if outer_sign > 0 else (lo.y, split)
                yli, yhi2 = (lo.y, split) if outer_sign > 0 else (split, hi.y)
                box(parts["shell"], outer, lo.x, hi.x, ylo, yhi, zs, ze, "world")
                box(parts["walls"], inner_name, lo.x, hi.x, yli, yhi2, zs, ze, "world")
            else:
                xlo, xhi = (split, hi.x) if outer_sign > 0 else (lo.x, split)
                xli, xhi2 = (lo.x, split) if outer_sign > 0 else (split, hi.x)
                box(parts["shell"], outer, xlo, xhi, lo.y, hi.y, zs, ze, "world")
                box(parts["walls"], inner_name, xli, xhi2, lo.y, hi.y, zs, ze, "world")
        if collide:
            col(b, "metal", tag, lo.x, hi.x, lo.y, hi.y, zs, ze)


def window_unit(b, parts, axis, fixed, a0, a1, z0, outward, rng, broken=False):
    sill = z0 + WIN[0]
    head = z0 + WIN[1]
    frame = parts["joinery"]
    if axis == "x":
        for a in (a0, a1 - 0.06):
            box(frame, "rig_paint_grey", a, a + 0.06, fixed - 0.1, fixed + 0.1, sill, head)
        for zz in (sill, head - 0.06):
            box(frame, "rig_paint_grey", a0, a1, fixed - 0.1, fixed + 0.1, zz, zz + 0.06)
        box(frame, "rig_paint_grey", (a0 + a1) * 0.5 - 0.025, (a0 + a1) * 0.5 + 0.025, fixed - 0.03, fixed + 0.03, sill, head)
        if not broken:
            box(frame, "glass_dirty", a0 + 0.06, a1 - 0.06, fixed - 0.012, fixed + 0.012, sill + 0.06, head - 0.06)
        box(frame, "rig_paint_white", a0 - 0.05, a1 + 0.05, fixed + outward * 0.1, fixed + outward * 0.18, sill - 0.06, sill)
        col(b, "glass", "window", a0, a1, fixed - 0.06, fixed + 0.06, sill, head)
    else:
        for a in (a0, a1 - 0.06):
            box(frame, "rig_paint_grey", fixed - 0.1, fixed + 0.1, a, a + 0.06, sill, head)
        for zz in (sill, head - 0.06):
            box(frame, "rig_paint_grey", fixed - 0.1, fixed + 0.1, a0, a1, zz, zz + 0.06)
        box(frame, "rig_paint_grey", fixed - 0.03, fixed + 0.03, (a0 + a1) * 0.5 - 0.025, (a0 + a1) * 0.5 + 0.025, sill, head)
        if not broken:
            box(frame, "glass_dirty", fixed - 0.012, fixed + 0.012, a0 + 0.06, a1 - 0.06, sill + 0.06, head - 0.06)
        box(frame, "rig_paint_white", fixed + outward * 0.1, fixed + outward * 0.18, a0 - 0.05, a1 + 0.05, sill - 0.06, sill)
        col(b, "glass", "window", fixed - 0.06, fixed + 0.06, a0, a1, sill, head)


def door_frame(parts, axis, fixed, a0, a1, z0, thickness, rng, leaf=True, paint="rig_paint_grey"):
    frame = parts["joinery"]
    if axis == "x":
        for a in (a0 - 0.05, a1):
            box(frame, paint, a, a + 0.05, fixed - thickness * 0.5 - 0.02, fixed + thickness * 0.5 + 0.02, z0, z0 + DOOR_H)
        box(frame, paint, a0 - 0.05, a1 + 0.05, fixed - thickness * 0.5 - 0.02, fixed + thickness * 0.5 + 0.02, z0 + DOOR_H, z0 + DOOR_H + 0.05)
    else:
        for a in (a0 - 0.05, a1):
            box(frame, paint, fixed - thickness * 0.5 - 0.02, fixed + thickness * 0.5 + 0.02, a, a + 0.05, z0, z0 + DOOR_H)
        box(frame, paint, fixed - thickness * 0.5 - 0.02, fixed + thickness * 0.5 + 0.02, a0 - 0.05, a1 + 0.05, z0 + DOOR_H, z0 + DOOR_H + 0.05)
    if leaf and rng.random() < 0.7:
        width = a1 - a0
        side = rng.choice([-1.0, 1.0])
        angle = rng.uniform(1.4, 1.75)
        if axis == "x":
            hinge = V(a0, fixed + side * thickness * 0.5, z0 + 0.02)
            direction = V(math.cos(angle) * 1.0, side * math.sin(angle), 0.0)
        else:
            hinge = V(fixed + side * thickness * 0.5, a0, z0 + 0.02)
            direction = V(side * math.sin(angle), math.cos(angle), 0.0)
        direction.normalize()
        center = hinge + direction * (width * 0.5) + V(0.0, 0.0, (DOOR_H - 0.04) * 0.5)
        emit(frame, kit.geo_box(width - 0.02, 0.045, DOOR_H - 0.05), "rig_wall", kit.place(center, direction, up), "box")


def pilaster_spots(a0, a1, step, gaps):
    spots = []
    a = a0 + step
    while a < a1 - 0.3:
        if not any(g0 - 0.2 < a < g1 + 0.2 for g0, g1 in gaps):
            spots.append(a)
        a += step
    return spots


def exterior(b, parts, rng):
    shell = parts["shell"]
    bases = [FLOORS[0] - 0.05, FLOORS[1] - 0.3, FLOORS[2] - 0.3]
    tops = [FLOORS[1] - 0.3, FLOORS[2] - 0.3, ROOF]
    for level, z in enumerate(FLOORS):
        plan = plans[level]
        west_open = [(a0, a1, z + WIN[0], z + WIN[1]) for a0, a1 in plan["west_windows"]]
        east_open = [(a0, a1, z + WIN[0], z + WIN[1]) for a0, a1 in plan["east_windows"]]
        north_open = [(a0, a1, z + WIN[0], z + WIN[1]) for a0, a1 in plan["north_windows"]]
        south_open = [(a0, a1, z + WIN[0], z + WIN[1]) for a0, a1 in plan["south_windows"]]
        if level == 0:
            west_open.append((-11.2, -10.0, z, z + DOOR_H))
            north_open.append((18.0, 19.2, z, z + DOOR_H))
        base = bases[level]
        z1 = tops[level]
        wall_line(b, parts, "y", X0 + T * 0.5, Y0, Y1, base, z1, west_open, T, "rig_paint_white", -1.0, "facade")
        wall_line(b, parts, "y", X1 - T * 0.5, Y0, Y1, base, z1, east_open, T, "rig_paint_white", 1.0, "facade")
        wall_line(b, parts, "x", Y0 + T * 0.5, X0 + T, X1 - T, base, z1, south_open, T, "rig_paint_white", -1.0, "facade")
        wall_line(b, parts, "x", Y1 - T * 0.5, X0 + T, X1 - T, base, z1, north_open, T, "rig_paint_white", 1.0, "facade")
        for a0, a1 in plan["west_windows"]:
            window_unit(b, parts, "y", X0 + T * 0.5, a0, a1, z, -1.0, rng)
        for a0, a1 in plan["east_windows"]:
            window_unit(b, parts, "y", X1 - T * 0.5, a0, a1, z, 1.0, rng, rng.random() < 0.15)
        for a0, a1 in plan["north_windows"]:
            window_unit(b, parts, "x", Y1 - T * 0.5, a0, a1, z, 1.0, rng)
        for a0, a1 in plan["south_windows"]:
            window_unit(b, parts, "x", Y0 + T * 0.5, a0, a1, z, -1.0, rng)
        if level > 0:
            band = z - 0.25
            for x0, x1, y0, y1 in ((X0 - 0.06, X0, Y0 - 0.06, Y1 + 0.06), (X1, X1 + 0.06, Y0 - 0.06, Y1 + 0.06), (X0, X1, Y0 - 0.06, Y0), (X0, X1, Y1, Y1 + 0.06)):
                box(shell, "rig_paint_orange", x0, x1, y0, y1, band, band + 0.22, "world")
    door_frame(parts, "y", X0 + T * 0.5, -11.2, -10.0, FLOORS[0], T, rng, False, "rig_paint_grey")
    door_frame(parts, "x", Y1 - T * 0.5, 18.0, 19.2, FLOORS[0], T, rng, False, "rig_paint_grey")
    facades = {"west": [], "east": [], "north": [], "south": []}
    for plan in plans:
        for key in facades:
            facades[key].extend(plan[key + "_windows"])
    facades["west"].append((-11.2, -10.0))
    facades["north"].append((18.0, 19.2))
    for x in pilaster_spots(X0, X1, 1.3, facades["south"]):
        box(shell, "rig_paint_white", x - 0.04, x + 0.04, Y0 - 0.05, Y0, FLOORS[0], ROOF, "world")
    for x in pilaster_spots(X0, X1, 1.3, facades["north"]):
        box(shell, "rig_paint_white", x - 0.04, x + 0.04, Y1, Y1 + 0.05, FLOORS[0], ROOF, "world")
    for y in pilaster_spots(Y0, Y1, 1.5, facades["west"]):
        box(shell, "rig_paint_white", X0 - 0.05, X0, y - 0.04, y + 0.04, FLOORS[0], ROOF, "world")
    for y in pilaster_spots(Y0, Y1, 1.5, facades["east"]):
        box(shell, "rig_paint_white", X1, X1 + 0.05, y - 0.04, y + 0.04, FLOORS[0], ROOF, "world")
    box(shell, "rig_paint_grey", X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y1 + 0.1, ROOF, ROOF + 0.08, "world")
    for x0, x1, y0, y1 in ((X0 - 0.1, X0 + 0.05, Y0 - 0.1, Y1 + 0.1), (X1 - 0.05, X1 + 0.1, Y0 - 0.1, Y1 + 0.1), (X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y0 + 0.05), (X0 - 0.1, X1 + 0.1, Y1 - 0.05, Y1 + 0.1)):
        box(shell, "rig_paint_white", x0, x1, y0, y1, ROOF, ROOF + 0.35, "world")
    ok.sign(parts["fittings"], "name_board", V((X0 + X1) * 0.5 + 0.6, Y0 - 0.08, FLOORS[2] + 2.65), V(0.0, -1.0, 0.0), 7.6, 0.9, 0.0, "rig_paint_white", 0.02)
    ok.sign(parts["fittings"], "name_board", V(X0 - 0.08, 0.0, FLOORS[2] + 2.6), V(-1.0, 0.0, 0.0), 6.0, 0.75, 0.0, "rig_paint_white", 0.02)
    ok.sign(parts["fittings"], "escape", V(X0 - 0.05, -9.4, FLOORS[0] + 1.7), V(-1.0, 0.0, 0.0), 0.6, 0.22)
    ok.sign(parts["fittings"], "muster", V(X0 - 0.05, -6.4, FLOORS[0] + 1.9), V(-1.0, 0.0, 0.0), 1.1, 0.21)
    for y, kind, lit in ((-10.6, "warm", True), (18.6, "cold", True)):
        if y < 0:
            ok.bulkhead_light(b, parts["fittings"], V(X0 - 0.02, y, FLOORS[0] + 2.45), V(-1.0, 0.0, 0.0), kind, lit)
        else:
            ok.bulkhead_light(b, parts["fittings"], V(y, Y1 + 0.02, FLOORS[0] + 2.45), V(0.0, 1.0, 0.0), kind, lit)
    decals = parts["decals"]
    for level, z in enumerate(FLOORS):
        plan = plans[level]
        for a0, a1 in plan["west_windows"]:
            ok.decal(decals, rng.choice(["run_a", "run_b", "run_d"]), V(X0 - 0.03, rng.uniform(a0, a1), z + WIN[0] - 0.6), V(-1.0, 0.0, 0.0), rng.uniform(0.3, 0.6), 1.2)
        for a0, a1 in plan["east_windows"]:
            ok.decal(decals, rng.choice(["run_a", "run_c", "run_d"]), V(X1 + 0.03, rng.uniform(a0, a1), z + WIN[0] - 0.6), V(1.0, 0.0, 0.0), rng.uniform(0.3, 0.6), 1.2)
    for k in range(10):
        side = rng.choice(["w", "e", "s", "n"])
        zz = rng.uniform(FLOORS[0] + 0.5, ROOF - 0.6)
        if side == "w":
            ok.decal(decals, "runs_wide", V(X0 - 0.03, rng.uniform(Y0 + 1.0, Y1 - 1.0), zz), V(-1.0, 0.0, 0.0), 1.6, 1.0)
        elif side == "e":
            ok.decal(decals, "runs_wide", V(X1 + 0.03, rng.uniform(Y0 + 1.0, Y1 - 1.0), zz), V(1.0, 0.0, 0.0), 1.6, 1.0)
        elif side == "s":
            ok.decal(decals, "runs_wide", V(rng.uniform(X0 + 1.0, X1 - 1.0), Y0 - 0.03, zz), V(0.0, -1.0, 0.0), 1.6, 1.0)
        else:
            ok.decal(decals, "runs_wide", V(rng.uniform(X0 + 1.0, X1 - 1.0), Y1 + 0.03, zz), V(0.0, 1.0, 0.0), 1.6, 1.0)
    for k in range(6):
        ok.decal(decals, "guano_runs", V(X0 - 0.03, rng.uniform(Y0 + 1.0, Y1 - 1.0), ROOF - 0.5), V(-1.0, 0.0, 0.0), 0.6, 0.9)
    ok.pipe(parts["services"], "rig_paint_grey", [V(X1 + 0.25, -11.0, FLOORS[0] + 0.3), V(X1 + 0.25, -11.0, ROOF + 0.5), V(X1 - 1.0, -11.0, ROOF + 0.5)], 0.08, 8, 0.3)
    ok.cable_tray(parts["services"], V(X0 - 0.35, -11.5, FLOORS[1] - 0.6), V(X0 - 0.35, 11.5, FLOORS[1] - 0.6), 0.4, rng, "rig_paint_grey", 4, 1.2)


def floors_and_ceilings(b, parts, rng):
    floor = parts["floors"]
    for level, z in enumerate(FLOORS):
        holes = [VOID] if level > 0 else []
        outline = [(IX0, IY0), (IX1, IY0), (IX1, IY1), (IX0, IY1)]
        loops = [[(h[0], h[2]), (h[1], h[2]), (h[1], h[3]), (h[0], h[3])] for h in holes]
        thickness = 0.3 if level > 0 else 0.05
        geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), outline, loops, z - thickness, z)
        emit(floor, geo, "rig_vinyl", None, "world")
        tk.floor_cols(b, "metal", "floor", IX0, IX1, IY0, IY1, z - 0.3, z, holes)
    outline = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), outline, [[(VOID[0], VOID[2]), (VOID[1], VOID[2]), (VOID[1], VOID[3]), (VOID[0], VOID[3])]], ROOF - 0.3, ROOF)
    emit(floor, geo, "rig_paint_grey", None, "world")
    tk.floor_cols(b, "metal", "roof", X0, X1, Y0, Y1, ROOF - 0.3, ROOF, [VOID])


def ceiling(parts, x0, x1, y0, y1, z, rng, missing=0.08):
    part = parts["ceilings"]
    nx = max(1, int((x1 - x0) / 0.6))
    ny = max(1, int((y1 - y0) / 0.6))
    holes = []
    for i in range(nx):
        for j in range(ny):
            if rng.random() < missing:
                holes.append((x0 + (x1 - x0) * i / nx + 0.02, x0 + (x1 - x0) * (i + 1) / nx - 0.02, y0 + (y1 - y0) * j / ny + 0.02, y0 + (y1 - y0) * (j + 1) / ny - 0.02))
    holes = holes[:3]
    outline = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    loops = [[(h[0], h[2]), (h[1], h[2]), (h[1], h[3]), (h[0], h[3])] for h in holes]
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), outline, loops, z, z + 0.02, False)
    geo.faces = [face for face in geo.faces if kit.newell([geo.points[i] for i in face]).z < 0.0]
    emit(part, geo, "rig_ceiling", None, "world")
    for h in holes:
        box(part, "soot", h[0], h[1], h[2], h[3], z + 0.25, z + 0.27, "world")
    for index, h in enumerate(holes[:1]):
        cx = (h[0] + h[1]) * 0.5
        cy = (h[2] + h[3]) * 0.5
        matrix = kit.turned(V(cx + 0.15, cy, z - 0.25), rng.uniform(0.0, 0.5), rng.uniform(0.6, 1.0), rng.uniform(-0.3, 0.3))
        emit(part, kit.geo_box(0.58, 0.58, 0.015), "rig_ceiling", matrix, "world")
    for index, h in enumerate(holes[1:2]):
        cx = (h[0] + h[1]) * 0.5
        cy = (h[2] + h[3]) * 0.5
        ok.hanging_cable(part, V(cx, cy, z + 0.02), rng.uniform(0.3, 0.9), rng, 0.008)
    return holes


def skirting(parts, x0, x1, y0, y1, z, doors):
    part = parts["joinery"]
    for a0, a1, y, axis in ((x0, x1, y0 + 0.012, "x"), (x0, x1, y1 - 0.012, "x"), (y0, y1, x0 + 0.012, "y"), (y0, y1, x1 - 0.012, "y")):
        spans = [(a0, a1)]
        for d in doors:
            if d[0] == axis and abs(d[1] - y) < 0.2:
                new = []
                for s, e in spans:
                    if d[3] <= s or d[2] >= e:
                        new.append((s, e))
                        continue
                    if d[2] > s:
                        new.append((s, d[2]))
                    if d[3] < e:
                        new.append((d[3], e))
                spans = new
        for s, e in spans:
            if axis == "x":
                box(part, "rig_paint_grey", s, e, y - 0.012, y + 0.012, z, z + 0.1)
            else:
                box(part, "rig_paint_grey", y - 0.012, y + 0.012, s, e, z, z + 0.1)


def partitions(b, parts, rng):
    for level, z in enumerate(FLOORS):
        top = (FLOORS[level + 1] - 0.3) if level < 2 else ROOF - 0.3
        plan = plans[level]
        west_doors = [(d[0], d[1], z, z + DOOR_H) for name, y0, y1, d in plan["west"]]
        east_doors = [(d[0], d[1], z, z + DOOR_H) for name, y0, y1, d in plan["east"]]
        stair_door = (-11.2, -10.0, z, z + DOOR_H)
        inner_doors = {(0, 5.0): (13.0, 14.2)}
        wall_line(b, parts, "y", CX0, IY0, IY1, z, top, west_doors, PT, None, 0.0, "partition")
        wall_line(b, parts, "y", CX1, STAIR[3], IY1, z, top, east_doors, PT, None, 0.0, "partition")
        wall_line(b, parts, "y", CX1, IY0, STAIR[3], z, top, [stair_door], PT, None, 0.0, "partition")
        for name, y0, y1, d in plan["west"]:
            door_frame(parts, "y", CX0, d[0], d[1], z, PT, rng, name not in ("lobby",))
            if y0 > IY0 + 0.1:
                extra = inner_doors.get((level, y0))
                openings = [(extra[0], extra[1], z, z + DOOR_H)] if extra else []
                wall_line(b, parts, "x", y0, IX0, CX0 - PT * 0.5, z, top, openings, PT, None, 0.0, "partition")
                if extra:
                    door_frame(parts, "x", y0, extra[0], extra[1], z, PT, rng, False)
        for name, y0, y1, d in plan["east"]:
            door_frame(parts, "y", CX1, d[0], d[1], z, PT, rng, True)
            if y0 > STAIR[3] + 0.05:
                wall_line(b, parts, "x", y0, CX1 + PT * 0.5, IX1, z, top, [], PT, None, 0.0, "partition")
        wall_line(b, parts, "x", STAIR[3], CX1 + PT * 0.5, IX1, z, top, [], PT, None, 0.0, "partition")
        door_frame(parts, "y", CX1, -11.2, -10.0, z, PT, rng, False)
    stair_walls(b, parts, rng)


def stair_walls(b, parts, rng):
    top = ROOF + 2.6
    wall_line(b, parts, "x", (LANE1[1] + LANE2[0]) * 0.5, LAND, RUN1, FLOORS[0], ROOF + 1.2, [], 0.1, None, 0.0, "stair_spine", True, "rig_paint_grey")


def stairs(b, parts, rng):
    for level, z in enumerate(FLOORS):
        mid = z + 1.6
        nxt = z + 3.2
        ok.stair_flight(b, parts, LAND, RUN1, LANE1[0], LANE1[1], z, mid, "px", rng, "rig_paint_grey", "rig_paint_yellow", (True, False), (False, False), "q_stair", "rig_grating", 0.95)
        ok.stair_flight(b, parts, LAND, RUN1, LANE2[0], LANE2[1], mid, nxt, "nx", rng, "rig_paint_grey", "rig_paint_yellow", (False, True), (False, False), "q_stair", "rig_grating", 0.95)
        geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), [(RUN1, IY0), (IX1, IY0), (IX1, STAIR[3] - PT * 0.5), (RUN1, STAIR[3] - PT * 0.5)], [], mid - 0.2, mid)
        emit(parts["floors"], geo, "chequer_plate", None, "world")
        col(b, "metal", "half_landing", RUN1, IX1, IY0, STAIR[3], mid - 0.3, mid)
        ok.strip_light(b, parts["fixtures"], V((LAND + RUN1) * 0.5, (STAIR[2] + STAIR[3]) * 0.5, nxt - 0.35), 1.0, True, "cold", level != 1)
        ok.sign(parts["fittings"], ["main_level", "escape", "escape"][level], V(CX1 + 0.06, -9.6, z + 1.7), V(-1.0, 0.0, 0.0), 0.6, 0.15)


def doghouse(b, parts, rng):
    x0, x1, y0, y1 = STAIR[0] - 0.1, IX1 + 0.2, Y0, STAIR[3] + 0.1
    z0 = ROOF
    h = 2.6
    shell = parts["shell"]
    door = (-11.4, -10.2)
    wall_line(b, parts, "y", x0 + 0.06, y0, y1, z0, z0 + h, [(door[0], door[1], z0, z0 + DOOR_H)], 0.12, "rig_paint_white", -1.0, "doghouse", True, "rig_paint_grey")
    wall_line(b, parts, "y", x1 - 0.06, y0, y1, z0, z0 + h, [], 0.12, "rig_paint_white", 1.0, "doghouse", True, "rig_paint_grey")
    wall_line(b, parts, "x", y0 + 0.06, x0 + 0.12, x1 - 0.12, z0, z0 + h, [], 0.12, "rig_paint_white", -1.0, "doghouse", True, "rig_paint_grey")
    wall_line(b, parts, "x", y1 - 0.06, x0 + 0.12, x1 - 0.12, z0, z0 + h, [], 0.12, "rig_paint_white", 1.0, "doghouse", True, "rig_paint_grey")
    box(shell, "rig_paint_grey", x0 - 0.08, x1 + 0.08, y0 - 0.08, y1 + 0.08, z0 + h, z0 + h + 0.12, "world")
    col(b, "metal", "doghouse_roof", x0, x1, y0, y1, z0 + h, z0 + h + 0.12)
    door_frame(parts, "y", x0 + 0.06, door[0], door[1], z0, 0.12, rng, False)
    hinge = V(x0 - 0.02, door[0], z0 + 0.02)
    direction = V(-0.75, 0.66, 0.0).normalized()
    emit(parts["joinery"], kit.geo_box(1.18, 0.05, 2.1), "rig_paint_grey", kit.place(hinge + direction * 0.59 + V(0.0, 0.0, 1.05), direction, up), "box")
    ok.sign(parts["fittings"], "helideck", V(x0 - 0.02, -9.7, z0 + 1.7), V(-1.0, 0.0, 0.0), 0.8, 0.2)
    ok.bulkhead_light(b, parts["fittings"], V(x0 - 0.02, -10.8, z0 + 2.35), V(-1.0, 0.0, 0.0), "cold", True)


def roof_dressing(b, parts, rng):
    rails = parts["rails"]
    z = ROOF
    e = 0.15
    ok.railing(b, rails, [(X1 - e, STAIR[3] + 0.2), (X1 - e, Y1 - e), (X0 + e, Y1 - e), (X0 + e, Y0 + e), (STAIR[0] - 0.15, Y0 + e)], z, rng, 1.1, "rig_paint_yellow", True, False, "roof_rail")
    part = parts["services"]
    for cx, cy in ((14.6, -4.0), (14.6, 1.5)):
        box(part, "rig_paint_grey", cx - 1.2, cx + 1.2, cy - 1.5, cy + 1.5, z, z + 1.25, "box", 0.04)
        ok.lathe(part, "rig_paint_grey", V(cx, cy, z + 1.25), up, [(0.0, 0.0), (0.7, 0.0), (0.7, 0.18), (0.0, 0.18)], 16, False)
        for k in range(5):
            angle = k * math.pi * 2.0 / 5.0
            ok.bar(part, "rig_steel", V(cx + math.cos(angle) * 0.32, cy + math.sin(angle) * 0.32, z + 1.36), V(math.cos(angle), math.sin(angle), 0.0), 0.55, 0.12, 0.012, up, 2.0)
        col(b, "metal", "hvac", cx - 1.2, cx + 1.2, cy - 1.5, cy + 1.5, z, z + 1.45)
        ok.pipe(part, "rig_paint_grey", [V(cx + 1.2, cy, z + 0.6), V(cx + 2.0, cy, z + 0.6), V(cx + 2.0, cy, z - 0.2)], 0.25, 4, 0.0)
    mast = V(13.3, -11.0, z)
    for k in range(3):
        angle = k * math.pi * 2.0 / 3.0
        tube(part, "rig_paint_white", mast + V(math.cos(angle) * 0.6, math.sin(angle) * 0.6, 0.0), mast + V(math.cos(angle) * 0.18, math.sin(angle) * 0.18, 7.5), 0.04, 6, True, 2.0)
    for hz in (1.5, 3.0, 4.5, 6.0):
        rad = 0.6 - (hz / 7.5) * 0.42
        pts = [mast + V(math.cos(a) * rad, math.sin(a) * rad, hz) for a in [k * math.pi * 2.0 / 3.0 for k in range(4)]]
        ok.path_tube(part, "rig_paint_white", pts, 0.02, 4, False, 2.0)
    tube(part, "rig_steel", mast + V(0.0, 0.0, 7.3), mast + V(0.0, 0.0, 10.2), 0.025, 6)
    for hz, length in ((8.2, 1.2), (9.0, 0.9)):
        tube(part, "rig_steel", mast + V(-length, 0.0, hz), mast + V(length, 0.0, hz), 0.012, 4)
    col(b, "metal", "mast", mast.x - 0.6, mast.x + 0.6, mast.y - 0.6, mast.y + 0.6, z, z + 2.0)
    dish = V(15.4, -11.0, z)
    tube(part, "rig_paint_grey", dish, dish + V(0.0, 0.0, 1.1), 0.06, 8)
    matrix = kit.Matrix.Translation(dish + V(0.0, 0.0, 1.3)) @ kit.Matrix.Rotation(0.9, 4, 'X') @ kit.Matrix.Rotation(-0.6, 4, 'Z')
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.45, 0.08), (0.6, 0.18), (0.58, 0.19), (0.0, 0.02)], 16), "rig_paint_white", matrix, "given", True)
    for k in range(8):
        ok.floor_decal(parts["decals"], rng.choice(["guano_a", "guano_b", "guano_a"]), rng.uniform(X0 + 1.0, X1 - 1.0), rng.uniform(Y0 + 1.0, Y1 - 1.0), z + 0.01, rng.uniform(1.0, 2.0), rng.uniform(1.0, 2.0), rng.uniform(0.0, 6.0))
    for k in range(3):
        ok.nest(part, V(rng.uniform(X0 + 1.0, X1 - 1.0), rng.uniform(-8.0, 9.0), z), rng)
    b.loot("box", V(16.4, -10.6, z))


def bunk(b, part, x, y, z, yaw, rng, length=2.0, width=0.85):
    base = kit.turned(V(x, y, z), yaw)
    for sx in (-length * 0.5 + 0.03, length * 0.5 - 0.03):
        for sy in (-width * 0.5 + 0.03, width * 0.5 - 0.03):
            emit(part, kit.geo_box(0.05, 0.05, 1.75), "rig_paint_grey", base @ kit.Matrix.Translation(V(sx, sy, 0.875)), "box", False, None, 2.0)
    for hz in (0.38, 1.38):
        for sy in (-width * 0.5 + 0.03, width * 0.5 - 0.03):
            emit(part, kit.geo_box(length - 0.06, 0.04, 0.12), "rig_paint_grey", base @ kit.Matrix.Translation(V(0.0, sy, hz)), "box", False, None, 2.0)
        emit(part, kit.geo_box(length - 0.08, width - 0.08, 0.025), "rig_paint_grey", base @ kit.Matrix.Translation(V(0.0, 0.0, hz + 0.02)), "box")
        if rng.random() < 0.85:
            geo = bd.cushion_geo(length - 0.12, width - 0.12, 0.13, rng, 0.02, 0.02, 4, 2)
            emit(part, geo, "mattress", base @ kit.Matrix.Translation(V(0.0, 0.0, hz + 0.035)), "box", True)
            if rng.random() < 0.6:
                cover = base @ kit.Matrix.Translation(V(rng.uniform(0.1, 0.4), 0.0, hz + 0.17)) @ kit.Matrix.Rotation(rng.uniform(-0.2, 0.2), 4, 'Z')
                emit(part, bd.cushion_geo(rng.uniform(0.8, 1.2), width - 0.06, 0.05, rng, 0.03, 0.0, 3, 2), rng.choice(["fabric_tartan", "fabric_worn"]), cover, "box", True)
            pillow = base @ kit.Matrix.Translation(V(-length * 0.5 + 0.3, 0.0, hz + 0.19))
            emit(part, kit.geo_cbox(0.34, 0.5, 0.1, 0.04), "fabric_worn", pillow, "box", True)
    for hz in (0.7, 1.0, 1.3):
        emit(part, kit.geo_box(0.03, 0.4, 0.03), "rig_paint_grey", base @ kit.Matrix.Translation(V(length * 0.5 - 0.03, 0.0, hz)), "box")
    corners = [base @ V(sx, sy, 0.0) for sx in (-length * 0.5, length * 0.5) for sy in (-width * 0.5, width * 0.5)]
    xs = [p.x for p in corners]
    ys = [p.y for p in corners]
    col(b, "metal", "bunk", min(xs), max(xs), min(ys), max(ys), z, z + 1.75)


def desk(b, part, clutter, x, y, z, yaw, rng, width=1.2, depth=0.6, items=True):
    base = kit.turned(V(x, y, z), yaw)
    emit(part, kit.geo_box(width, depth, 0.03), "timber_beam", base @ kit.Matrix.Translation(V(0.0, 0.0, 0.73)), "board")
    for sx in (-1.0, 1.0):
        emit(part, kit.geo_box(0.03, depth - 0.04, 0.72), "rig_paint_grey", base @ kit.Matrix.Translation(V(sx * (width * 0.5 - 0.03), 0.0, 0.36)), "box")
    emit(part, kit.geo_box(0.4, depth - 0.06, 0.55), "rig_paint_grey", base @ kit.Matrix.Translation(V(width * 0.5 - 0.25, 0.0, 0.4)), "box")
    for k in range(3):
        emit(part, kit.geo_box(0.36, 0.01, 0.16), "rig_paint_grey", base @ kit.Matrix.Translation(V(width * 0.5 - 0.25, -depth * 0.5 + 0.02, 0.2 + k * 0.18)), "box")
    if items:
        tp.papers(clutter, x - 0.3, x + 0.3, y - 0.15, y + 0.15, z + 0.75, 3, rng, ("letter", "notice", "envelope"))
        if rng.random() < 0.5:
            tp.cup_light(clutter, base @ V(-width * 0.3, 0.1, 0.75), rng)
    corners = [base @ V(sx, sy, 0.0) for sx in (-width * 0.5, width * 0.5) for sy in (-depth * 0.5, depth * 0.5)]
    col(b, "wood", "desk", min(p.x for p in corners), max(p.x for p in corners), min(p.y for p in corners), max(p.y for p in corners), z, z + 0.76)


def office_chair(part, position, yaw, rng, fallen=False):
    if fallen:
        base = kit.Matrix.Translation(position + V(0.0, 0.0, 0.32)) @ kit.Matrix.Rotation(yaw, 4, 'Z') @ kit.Matrix.Rotation(1.45, 4, 'Y')
    else:
        base = kit.turned(position, yaw)
    for k in range(5):
        angle = k * math.pi * 2.0 / 5.0
        emit(part, kit.geo_box(0.3, 0.035, 0.03), "rig_paint_grey", base @ kit.Matrix.Translation(V(math.cos(angle) * 0.15, math.sin(angle) * 0.15, 0.06)) @ kit.Matrix.Rotation(angle, 4, 'Z'), "box")
    emit(part, kit.geo_tube([V(0.0, 0.0, 0.06), V(0.0, 0.0, 0.42)], kit.circle(0.025, 6), True), "rig_steel", base, "given", True)
    emit(part, kit.geo_cbox(0.46, 0.46, 0.08, 0.03), "fabric_worn", base @ kit.Matrix.Translation(V(0.0, 0.0, 0.46)), "box")
    emit(part, kit.geo_cbox(0.44, 0.07, 0.5, 0.03), "fabric_worn", base @ kit.Matrix.Translation(V(0.0, 0.24, 0.78)) @ kit.Matrix.Rotation(-0.12, 4, 'X'), "box")


def plastic_chair(part, position, yaw, rng, name="rig_paint_orange", fallen=False):
    if fallen:
        base = kit.Matrix.Translation(position + V(0.0, 0.0, 0.22)) @ kit.Matrix.Rotation(yaw, 4, 'Z') @ kit.Matrix.Rotation(1.57, 4, 'X')
    else:
        base = kit.turned(position, yaw)
    for sx in (-0.19, 0.19):
        for sy in (-0.19, 0.19):
            emit(part, kit.geo_tube([V(sx, sy, 0.0), V(sx * 0.95, sy * 0.95, 0.44)], kit.circle(0.012, 4), True), "rig_steel", base, "given", True)
    emit(part, kit.geo_cbox(0.44, 0.42, 0.03, 0.01), name, base @ kit.Matrix.Translation(V(0.0, 0.0, 0.455)), "box")
    emit(part, kit.geo_cbox(0.42, 0.03, 0.34, 0.01), name, base @ kit.Matrix.Translation(V(0.0, 0.22, 0.68)) @ kit.Matrix.Rotation(-0.15, 4, 'X'), "box")


def table(b, part, x, y, z, width, depth, rng, top="rig_steel", legs="rig_paint_grey", tag="table"):
    box(part, top, x - width * 0.5, x + width * 0.5, y - depth * 0.5, y + depth * 0.5, z + 0.72, z + 0.75, "box")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            px = x + sx * (width * 0.5 - 0.06)
            py = y + sy * (depth * 0.5 - 0.06)
            box(part, legs, px - 0.02, px + 0.02, py - 0.02, py + 0.02, z, z + 0.72)
    col(b, "wood", tag, x - width * 0.5, x + width * 0.5, y - depth * 0.5, y + depth * 0.5, z, z + 0.75)


def screen(part, center, yaw, rng, size=0.42, key=None):
    base = kit.turned(center, yaw)
    emit(part, kit.geo_cbox(size + 0.06, 0.36, size * 0.85, 0.03), "rig_paint_white", base @ kit.Matrix.Translation(V(0.0, 0.12, size * 0.45)), "box")
    face = base @ V(0.0, -0.065, size * 0.45)
    normal = (base.to_3x3() @ V(0.0, -1.0, 0.0)).normalized()
    tk.atlas_panel(part, "rig_signs", face, normal, size, size * 0.7, lib.region_uv(lib.signs, key or rng.choice(["screen_a", "screen_b"])), 0.0, 0.004)


def console_run(b, part, clutter, x0, x1, y, z, facing, rng, depth=0.9):
    sign = 1.0 if facing > 0 else -1.0
    y_back = y
    y_front = y + sign * depth
    box(part, "rig_paint_grey", x0, x1, min(y_back, y_front), max(y_back, y_front), z, z + 0.72, "box")
    length = x1 - x0
    count = max(1, int(length / 1.3))
    for k in range(count):
        cx = x0 + length * (k + 0.5) / count
        tk.atlas_panel(part, "rig_signs", V(cx, y + sign * depth * 0.55, z + 0.735), up, length / count - 0.12, depth * 0.55, lib.region_uv(lib.signs, "console"), 0.0 if sign > 0 else math.pi, 0.002)
        screen(clutter, V(cx + rng.uniform(-0.15, 0.15), y + sign * 0.28, z + 0.75), (0.0 if sign > 0 else math.pi) + rng.uniform(-0.2, 0.2), rng)
        if rng.random() < 0.6:
            box(clutter, "rig_paint_grey", cx - 0.22, cx + 0.22, y + sign * 0.6 - 0.08, y + sign * 0.6 + 0.08, z + 0.75, z + 0.77)
    col(b, "metal", "console", x0, x1, min(y_back, y_front), max(y_back, y_front), z, z + 0.75)


def console_column(b, part, clutter, y0, y1, x, z, rng, depth=0.85):
    box(part, "rig_paint_grey", x, x + depth, y0, y1, z, z + 0.72, "box")
    length = y1 - y0
    count = max(1, int(length / 1.3))
    for k in range(count):
        cy = y0 + length * (k + 0.5) / count
        tk.atlas_panel(part, "rig_signs", V(x + depth * 0.55, cy, z + 0.735), up, depth * 0.55, length / count - 0.12, lib.region_uv(lib.signs, "console"), math.pi * 0.5, 0.002)
        screen(clutter, V(x + 0.28, cy + rng.uniform(-0.15, 0.15), z + 0.75), face_east + rng.uniform(-0.2, 0.2), rng)
    col(b, "metal", "console", x, x + depth, y0, y1, z, z + 0.75)


def counter_run(b, part, x0, x1, y0, y1, z, rng, top="rig_steel", body="rig_steel", sink=None, hob=None):
    box(part, body, x0, x1, y0, y1, z, z + 0.86, "box")
    box(part, top, x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 + 0.01, z + 0.86, z + 0.9, "box")
    if sink:
        sx, sy = sink
        box(part, "soot", sx - 0.25, sx + 0.25, sy - 0.2, sy + 0.2, z + 0.9, z + 0.902)
        tube(part, "rig_steel", V(sx, sy + 0.25, z + 0.9), V(sx, sy + 0.25, z + 1.2), 0.012, 6)
        tube(part, "rig_steel", V(sx, sy + 0.25, z + 1.2), V(sx, sy + 0.08, z + 1.16), 0.012, 6)
    if hob:
        hx, hy = hob
        for dx in (-0.2, 0.2):
            for dy in (-0.15, 0.15):
                ok.lathe(part, "soot", V(hx + dx, hy + dy, z + 0.9), up, [(0.0, 0.0), (0.09, 0.0), (0.09, 0.012), (0.0, 0.012)], 10, False)
    col(b, "metal", "counter", x0, x1, y0, y1, z, z + 0.9)


def tall_unit(b, part, x0, x1, y0, y1, z, height, name="rig_steel", tag="unit"):
    box(part, name, x0, x1, y0, y1, z, z + height, "box", 0.01)
    col(b, "metal", tag, x0, x1, y0, y1, z, z + height)


def shelves(b, part, x0, x1, y0, y1, z, rng, levels=4, height=1.9, stock=True):
    for k in range(levels):
        zz = z + 0.15 + (height - 0.2) * k / max(levels - 1, 1)
        box(part, "rig_paint_grey", x0, x1, y0, y1, zz, zz + 0.025)
        if stock:
            cursor = x0 + 0.05 if (x1 - x0) > (y1 - y0) else y0 + 0.05
            limit = x1 - 0.05 if (x1 - x0) > (y1 - y0) else y1 - 0.05
            while cursor < limit - 0.2:
                w = rng.uniform(0.15, 0.4)
                if rng.random() < 0.25:
                    cursor += w
                    continue
                h = rng.uniform(0.12, 0.32)
                name = rng.choice(["rig_cardboard", "rig_cardboard", "rig_cardboard", "timber_planks_weathered", "fabric_worn"])
                if (x1 - x0) > (y1 - y0):
                    box(part, name, cursor, min(cursor + w, limit), y0 + 0.03, y1 - 0.03, zz + 0.025, zz + 0.025 + h)
                else:
                    box(part, name, x0 + 0.03, x1 - 0.03, cursor, min(cursor + w, limit), zz + 0.025, zz + 0.025 + h)
                cursor += w + 0.02
    for px in (x0, x1 - 0.03):
        for py in (y0, y1 - 0.03):
            box(part, "rig_paint_grey", px, px + 0.03, py, py + 0.03, z, z + height)
    col(b, "metal", "shelves", x0, x1, y0, y1, z, z + height)


def room_light(b, parts, x, y, z_ceiling, kind, lit=True, length=1.2, along_x=False, hanging=0.0):
    ok.strip_light(b, parts["fixtures"], V(x, y, z_ceiling), length, along_x, kind, lit, hanging)


def notice(part, center, normal, rng, kind=None, scale=1.0):
    tp.wall_sheet(part, center, normal, kind or rng.choice(["notice", "poster", "calendar", "letter"]), rng, scale, rng.uniform(-0.08, 0.08))


def finish_room(b, parts, x0, x1, y0, y1, z, rng, floor_name=None, missing=0.08, doors=()):
    top = z + 3.2 - 0.55 if z < ROOF - 0.1 else z + 2.6
    holes = ceiling(parts, x0, x1, y0, y1, top, rng, missing)
    if floor_name:
        box(parts["floors"], floor_name, x0, x1, y0, y1, z, z + 0.008, "world")
    skirting(parts, x0, x1, y0, y1, z, doors)
    clutter = parts["clutter"]
    for h in holes[:2]:
        cx = (h[0] + h[1]) * 0.5
        cy = (h[2] + h[3]) * 0.5
        for k in range(rng.randint(1, 3)):
            piece = kit.turned(V(cx + rng.uniform(-0.4, 0.4), cy + rng.uniform(-0.4, 0.4), z + 0.012 + k * 0.016), rng.uniform(0.0, 6.0), rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05))
            emit(clutter, kit.geo_box(rng.uniform(0.15, 0.35), rng.uniform(0.12, 0.3), 0.015), "rig_ceiling", piece, "box")
    if rng.random() < 0.6 and (x1 - x0) > 1.5:
        tp.papers(clutter, x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, z + 0.01, rng.randint(2, 5), rng, ("letter", "notice", "envelope", "newspaper"))
    return top


def furnish(b, parts, rng):
    for level, z in enumerate(FLOORS):
        plan = plans[level]
        for side in ("west", "east"):
            for name, y0, y1, d in plan[side]:
                if side == "west":
                    x0, x1 = IX0, CX0 - PT * 0.5
                    door_wall = ("y", x1, d[0], d[1])
                else:
                    x0, x1 = CX1 + PT * 0.5, IX1
                    door_wall = ("y", x0, d[0], d[1])
                ry0 = y0 + (PT * 0.5 if y0 > IY0 + 0.1 else 0.0)
                ry1 = y1 - (PT * 0.5 if y1 < IY1 - 0.1 else 0.0)
                if side == "east" and name == "wc":
                    ry0 = y0 + PT * 0.5
                handler = rooms.get(name)
                floor_name = {"galley": "kitchen_tiles", "wc": "kitchen_tiles", "showers": "kitchen_tiles", "mess": "town_lino", "medical": None}.get(name)
                top = finish_room(b, parts, x0, x1, ry0, ry1, z, rng, floor_name, 0.12 if level == 1 else 0.07, [door_wall])
                if handler:
                    handler(b, parts, x0, x1, ry0, ry1, z, top, side, d, rng)
        corridor(b, parts, level, z, rng)


def corridor(b, parts, level, z, rng):
    top = finish_room(b, parts, CX0 + PT * 0.5, CX1 - PT * 0.5, IY0, IY1, z, rng, None, 0.1, [])
    for k, y in enumerate((-6.0, 0.5, 7.0)):
        room_light(b, parts, (CX0 + CX1) * 0.5, y, top, "cold", (k + level) % 3 != 2, 1.2, False)
    fittings = parts["fittings"]
    notice(fittings, V(CX0 + 0.06, -5.5, z + 1.5), V(1.0, 0.0, 0.0), rng, "notice")
    notice(fittings, V(CX1 - 0.06, 3.6, z + 1.45), V(-1.0, 0.0, 0.0), rng, "poster")
    ok.sign(fittings, "escape", V((CX0 + CX1) * 0.5, IY1 - 0.05, z + 2.35), V(0.0, -1.0, 0.0), 0.5, 0.18, 0.0, "rig_paint_grey", 0.01)
    extinguisher(parts["clutter"], V(CX1 - 0.12, -0.6, z), rng)
    if level == 1:
        bd.drape(parts["clutter"], V((CX0 + CX1) * 0.5, 4.2, z + 0.02), 0.8, 1.3, 0.02, 0.3, rng, "fabric_worn")
    for k in range(3):
        ok.floor_decal(parts["decals"], rng.choice(["oil_b", "salt"]), (CX0 + CX1) * 0.5, rng.uniform(-8.0, 10.0), z + 0.012, 0.9, 0.9, rng.uniform(0.0, 6.0))


def extinguisher(part, base, rng, lying=False):
    ok.gas_cylinder(part, base, rng, "rig_paint_orange", lying, rng.uniform(0.0, 6.0), 0.55, 0.08, "rig_rubber")


def lobby(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    for k in range(3):
        bx = x0 + 0.5 + k * 0.7
        box(part, "rig_paint_grey", bx - 0.3, bx + 0.3, y1 - 0.42, y1 - 0.08, z, z + 0.05)
        box(part, "rig_paint_grey", bx - 0.3, bx + 0.3, y1 - 0.42, y1 - 0.08, z + 0.35, z + 0.38)
        for s in (-0.12, 0.12):
            lump(part, "rig_rubber", V(bx + s, y1 - 0.25, z + 0.12), (0.06, 0.15, 0.12), rng)
    col(b, "metal", "boots", x0 + 0.2, x0 + 2.4, y1 - 0.42, y1 - 0.08, z, z + 0.4)
    for k in range(6):
        hy = y0 + 0.6 + k * 0.55
        tube(part, "rig_steel", V(x0 + 0.02, hy, z + 1.75), V(x0 + 0.14, hy, z + 1.8), 0.01, 4)
        if rng.random() < 0.7:
            suit = kit.turned(V(x0 + 0.18, hy, z + 1.2), face_east)
            emit(part, bd.cushion_geo(0.5, 0.18, 1.1, rng, 0.04, 0.0, 4, 6), rng.choice(["rig_lifeboat", "rig_paint_orange", "fabric_worn"]), suit, "box", True)
    col(b, "fabric", "suits", x0, x0 + 0.4, y0 + 0.3, y0 + 3.8, z, z + 1.8)
    box(part, "timber_beam", x1 - 2.8, x1 - 0.6, y0 + 0.08, y0 + 0.45, z + 0.42, z + 0.47)
    for px in (x1 - 2.6, x1 - 0.8):
        box(part, "rig_paint_grey", px - 0.03, px + 0.03, y0 + 0.1, y0 + 0.43, z, z + 0.42)
    col(b, "wood", "bench", x1 - 2.8, x1 - 0.6, y0 + 0.08, y0 + 0.45, z, z + 0.47)
    ok.sign(parts["fittings"], "muster", V((x0 + x1) * 0.5, y0 + 0.02, z + 1.9), V(0.0, 1.0, 0.0), 1.2, 0.23, 0.0, "rig_paint_grey", 0.01)
    notice(parts["fittings"], V(x1 - 1.4, y0 + 0.02, z + 1.45), V(0.0, 1.0, 0.0), rng, "notice", 1.2)
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "warm", True)


def lump(part, name, center, radii, rng):
    kit.lump(part, name, center, radii, rng, 0.2, 1)


def locker(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    tp.locker_row(b, part, V(x0 + 0.27, (y0 + y1) * 0.5, z), face_east, 9, rng, "blue", 1.85, 0.5, 0.42)
    tp.locker_row(b, part, V((x0 + x1) * 0.5 - 0.2, y0 + 0.27, z), face_north, 6, rng, "green", 1.85, 0.5, 0.42)
    for k in range(2):
        by = y0 + 1.6 + k * 1.8
        box(part, "timber_beam", x0 + 1.4, x0 + 3.6, by - 0.18, by + 0.18, z + 0.42, z + 0.47)
        for px in (x0 + 1.6, x0 + 3.4):
            box(part, "rig_paint_grey", px - 0.03, px + 0.03, by - 0.16, by + 0.16, z, z + 0.42)
        col(b, "wood", "bench", x0 + 1.4, x0 + 3.6, by - 0.18, by + 0.18, z, z + 0.47)
    for k in range(3):
        bd.drape(parts["clutter"], V(x0 + rng.uniform(1.5, 3.4), y0 + rng.uniform(1.4, 3.6), z + 0.47), 0.5, 0.6, 0.15, rng.uniform(0.0, 6.0), rng, rng.choice(["fabric_worn", "rig_lifeboat"]))
    b.loot("box", V(x1 - 0.6, y1 - 0.6, z))
    b.loot("box", V(x0 + 2.5, y0 + 2.5, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", True)


def galley(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    counter_run(b, part, x0 + 0.05, x0 + 0.7, y0 + 0.2, y1 - 1.6, z, rng, "rig_steel", "rig_steel", (x0 + 0.38, y0 + 1.0), (x0 + 0.38, y0 + 3.0))
    hood = (x0 + 0.05, x0 + 0.9, y0 + 2.4, y0 + 3.6)
    box(part, "rig_steel", hood[0], hood[1], hood[2], hood[3], top - 0.5, top - 0.05, "box")
    counter_run(b, part, x0 + 1.6, x0 + 3.2, y0 + 1.8, y0 + 2.8, z, rng, "rig_steel", "rig_steel")
    tall_unit(b, part, x1 - 0.75, x1 - 0.05, y1 - 0.85, y1 - 0.1, z, 2.0, "rig_steel", "fridge")
    tall_unit(b, part, x1 - 0.75, x1 - 0.05, y1 - 1.65, y1 - 0.9, z, 2.0, "rig_steel", "fridge")
    box(part, "soot", x1 - 0.77, x1 - 0.75, y1 - 0.7, y1 - 0.3, z + 0.9, z + 1.9)
    shelves(b, part, x0 + 1.0, x0 + 2.8, y0 + 0.05, y0 + 0.45, z, rng, 4, 1.9)
    for k in range(4):
        cx = x0 + 1.8 + rng.uniform(-0.6, 0.8)
        cy = y0 + 2.3 + rng.uniform(-0.3, 0.3)
        if k % 2 == 0:
            bd.pot(parts["clutter"], V(cx, cy, z + 0.9), rng, 0.14, "rig_steel")
        else:
            tp.plate_light(parts["clutter"], V(cx, cy, z + 0.9), rng)
    for k in range(3):
        tp.label_can(parts["clutter"], V(x0 + 1.2 + k * 0.4, y0 + 0.25, z + 1.2), rng, rng.choice(["peas", "beans", "soup", "beef", "peaches"]))
    tp.plate_light(parts["clutter"], V(x0 + 2.6, y0 + 3.4, z + 0.01), rng, 0.13, 0.5)
    b.loot("food", V(x0 + 2.6, y1 - 0.9, z))
    b.loot("food", V(x1 - 0.5, y0 + 2.4, z))
    room_light(b, parts, (x0 + x1) * 0.5, y0 + 1.5, top, "cold", True)
    room_light(b, parts, (x0 + x1) * 0.5, y1 - 1.5, top, "cold", False)
    ok.floor_decal(parts["decals"], "oil_a", x0 + 1.0, y0 + 3.0, z + 0.012, 1.2, 1.2, 0.5)


def mess(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    clutter = parts["clutter"]
    spots = [(x0 + 1.4, y0 + 1.5), (x0 + 1.4, y0 + 4.2), (x0 + 3.9, y0 + 1.5), (x0 + 3.9, y0 + 4.2)]
    for index, (tx, ty) in enumerate(spots):
        table(b, part, tx, ty, z, 1.6, 0.85, rng, "rig_steel", "rig_paint_grey", "mess_table")
        for sx in (-0.45, 0.45):
            for sy, yaw in ((-0.7, face_north), (0.7, face_south)):
                fallen = rng.random() < 0.2
                plastic_chair(part, V(tx + sx, ty + sy, z), yaw + rng.uniform(-0.3, 0.3), rng, rng.choice(["rig_paint_orange", "rig_paint_grey"]), fallen)
        for k in range(rng.randint(1, 3)):
            if rng.random() < 0.5:
                tp.cup_light(clutter, V(tx + rng.uniform(-0.6, 0.6), ty + rng.uniform(-0.25, 0.25), z + 0.75), rng)
            else:
                tp.plate_light(clutter, V(tx + rng.uniform(-0.6, 0.6), ty + rng.uniform(-0.25, 0.25), z + 0.75), rng)
    box(part, "rig_steel", x0 + 0.4, x0 + 2.2, y1 - 0.65, y1 - 0.05, z, z + 1.0)
    col(b, "metal", "servery", x0 + 0.4, x0 + 2.2, y1 - 0.65, y1 - 0.05, z, z + 1.0)
    tv = V(x1 - 0.3, y1 - 0.6, z + 1.8)
    box(part, "rig_paint_grey", tv.x - 0.25, tv.x + 0.05, tv.y - 0.35, tv.y + 0.35, tv.z - 0.4, tv.z - 0.38)
    screen(part, tv - V(0.1, 0.0, 0.38), face_west, rng, 0.6, "screen_b")
    b.loot("food", V(x0 + 2.6, y1 - 0.5, z))
    notice(parts["fittings"], V(x1 - 0.06, y0 + 2.0, z + 1.5), V(-1.0, 0.0, 0.0), rng, "notice")
    tp.wall_clock(parts["fittings"], V(x0 + 0.06, y0 + 3.4, z + 2.1), V(1.0, 0.0, 0.0), rng)
    room_light(b, parts, x0 + 1.4, (y0 + y1) * 0.5, top, "warm", True, 1.2, True)
    room_light(b, parts, x0 + 3.9, (y0 + y1) * 0.5, top, "warm", True, 1.2, True)


def wc(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    for k in range(2):
        cx = x1 - 0.6 - k * 1.1
        tp.toilet(b, part, V(cx, y1 - 0.4, z), face_south, rng, 1.6, rng.random() < 0.5, 12, False)
        box(part, "rig_paint_grey", cx - 0.56, cx - 0.53, y0 + 0.9, y1, z + 0.1, z + 2.0)
    col(b, "metal", "cubicle", x1 - 1.69, x1 - 1.66, y0 + 0.9, y1, z, z + 2.0)
    tp.basin(b, part, V(x0 + 1.4, y0 + 0.28, z), face_north, rng, 12)
    tp.wall_mirror(parts["fittings"], V(x0 + 1.4, y0 + 0.02, z + 1.55), V(0.0, 1.0, 0.0), 0.5, 0.6, rng, "rig_steel", True)
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", rng.random() < 0.6, 0.6)


def laundry(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    for k in range(3):
        cy = y0 + 0.5 + k * 0.7
        box(part, "rig_paint_white", x1 - 0.65, x1 - 0.05, cy - 0.3, cy + 0.3, z, z + 0.85, "box", 0.02)
        ok.lathe(part, "glass_dirty", V(x1 - 0.66, cy, z + 0.48), V(-1.0, 0.0, 0.0), [(0.0, 0.0), (0.2, 0.0), (0.2, 0.02), (0.0, 0.03)], 12, False)
        ok.ring(part, "rig_steel", V(x1 - 0.67, cy, z + 0.48), V(1.0, 0.0, 0.0), 0.2, 0.03, 0.03, 12)
    col(b, "metal", "machines", x1 - 0.65, x1 - 0.05, y0 + 0.2, y0 + 2.2, z, z + 0.85)
    table(b, part, x0 + 1.2, (y0 + y1) * 0.5, z, 1.6, 0.8, rng, "timber_beam", "rig_paint_grey", "laundry_table")
    for k in range(3):
        bd.drape(parts["clutter"], V(x0 + 1.2 + rng.uniform(-0.5, 0.5), (y0 + y1) * 0.5 + rng.uniform(-0.2, 0.2), z + 0.75), 0.5, 0.5, 0.2, rng.uniform(0.0, 6.0), rng, rng.choice(["fabric_worn", "fabric_tartan", "rig_lifeboat"]))
    shelves(b, part, x0 + 0.05, x0 + 0.45, y1 - 2.0, y1 - 0.1, z, rng, 4, 1.8)
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", False)


def recreation(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    tp.sofa_light(b, part, V(x0 + 1.9, y0 + 0.55, z), face_north, rng, 2.0, "fabric_worn", "timber_beam")
    tp.sofa_light(b, part, V(x0 + 0.55, y0 + 2.6, z), face_east, rng, 1.8, "fabric_tartan", "timber_beam")
    table(b, part, x0 + 2.0, y0 + 2.2, z - 0.3, 1.0, 0.6, rng, "timber_beam", "timber_beam", "coffee")
    tv = V(x0 + 2.0, y1 - 0.3, z + 0.6)
    box(part, "timber_beam", tv.x - 0.7, tv.x + 0.7, tv.y - 0.25, tv.y + 0.25, z, z + 0.6)
    screen(part, tv + V(0.0, 0.0, 0.01), face_south, rng, 0.6)
    col(b, "wood", "tv", tv.x - 0.7, tv.x + 0.7, tv.y - 0.25, tv.y + 0.25, z, z + 1.2)
    tp.bookcase(b, part, parts["clutter"], V(x1 - 1.0, y0 + 0.2, z), face_north, rng, 1.0, 1.8, 0.3, "timber_beam", 0.6)
    tp.dartboard(parts["fittings"], V(x1 - 0.05, y0 + 1.4, z + 1.73), V(-1.0, 0.0, 0.0), rng)
    tp.papers(parts["clutter"], x0 + 1.6, x0 + 2.4, y0 + 2.0, y0 + 2.4, z + 0.46, 4, rng, ("newspaper", "card", "letter"))
    b.loot("box", V(x1 - 0.6, y0 + 3.0, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "warm", True)


def provisions(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    shelves(b, part, x1 - 0.5, x1 - 0.05, y0 + 0.2, y1 - 0.2, z, rng, 5, 2.0)
    shelves(b, part, x0 + 1.4, x1 - 1.4, y1 - 0.5, y1 - 0.05, z, rng, 5, 2.0)
    for k in range(2):
        cx = x0 + 1.6 + k * 1.3
        box(part, "rig_paint_white", cx - 0.55, cx + 0.55, y0 + 0.1, y0 + 0.8, z, z + 0.9, "box", 0.03)
        col(b, "metal", "freezer", cx - 0.55, cx + 0.55, y0 + 0.1, y0 + 0.8, z, z + 0.9)
    for k in range(5):
        ok.sack(parts["clutter"], V(x0 + 1.0 + rng.uniform(-0.3, 0.6), y0 + 2.5 + rng.uniform(-0.4, 1.4), z), rng, 0.9)
    for k in range(4):
        tp.label_can(parts["clutter"], V(x0 + rng.uniform(1.0, 3.5), y0 + rng.uniform(1.4, 4.0), z), rng, rng.choice(["beans", "peas", "soup", "milk", "cocoa"]), None, None, True)
    b.loot("food", V(x0 + 2.6, y0 + 3.0, z))
    b.loot("food", V(x0 + 1.2, y1 - 1.0, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", True)


def medical(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    couch = (x0 + 0.9, x0 + 2.9, y0 + 0.5, y0 + 1.2)
    box(part, "rig_steel", couch[0] + 0.1, couch[1] - 0.1, couch[2] + 0.1, couch[3] - 0.1, z + 0.15, z + 0.65)
    emit(part, bd.cushion_geo(couch[1] - couch[0], couch[3] - couch[2], 0.12, rng, 0.02, 0.02, 6, 3), "leather_brown", kit.Matrix.Translation(V((couch[0] + couch[1]) * 0.5, (couch[2] + couch[3]) * 0.5, z + 0.65)), "box", True)
    col(b, "fabric", "couch", couch[0], couch[1], couch[2], couch[3], z, z + 0.8)
    tall_unit(b, part, x1 - 0.5, x1 - 0.05, y0 + 0.3, y0 + 1.8, z, 1.9, "rig_paint_white", "cabinet")
    for k in range(6):
        tp.medicine_bottle(parts["clutter"], V(x1 - 0.7 + rng.uniform(-0.1, 0.1), y0 + 0.6 + k * 0.2, z + 0.9), rng)
    counter_run(b, part, x0 + 0.05, x0 + 0.65, y1 - 2.2, y1 - 0.2, z, rng, "rig_steel", "rig_paint_white", (x0 + 0.35, y1 - 0.8), None)
    aid = V(x0 + 3.4, y0 + 0.12, z + 1.5)
    box(parts["fittings"], "rig_paint_white", aid.x - 0.3, aid.x + 0.3, y0 + 0.02, y0 + 0.22, aid.z - 0.35, aid.z + 0.35, "box", 0.01)
    box(parts["fittings"], "town_paint_red", aid.x - 0.05, aid.x + 0.05, y0 + 0.22, y0 + 0.226, aid.z - 0.15, aid.z + 0.15)
    box(parts["fittings"], "town_paint_red", aid.x - 0.15, aid.x + 0.15, y0 + 0.22, y0 + 0.226, aid.z - 0.05, aid.z + 0.05)
    for k in range(2):
        ok.gas_cylinder(part, V(x1 - 0.25, y1 - 0.4 - k * 0.3, z), rng, "rig_paint_white", False, 0.0, 1.1, 0.1, "rig_deck_green")
    box(part, "rig_lifeboat", x0 + 1.6, x0 + 3.5, y1 - 0.08, y1 - 0.04, z + 1.0, z + 1.55)
    for px in (x0 + 1.7, x0 + 3.4):
        box(part, "rig_steel", px - 0.02, px + 0.02, y1 - 0.1, y1 - 0.02, z + 0.95, z + 1.6)
    rail_y = y0 + 2.2
    tube(part, "rig_steel", V(x0 + 0.6, rail_y, top - 0.1), V(x0 + 3.2, rail_y, top - 0.1), 0.012, 5)
    tp.curtain_light(parts["clutter"], V(x0 + 0.6, rail_y, top - 0.12), V(x0 + 2.0, rail_y, top - 0.12), 2.0, rng, "fabric_worn", 0.5, True, 6, 5, False)
    ok.sign(parts["fittings"], "medical", V(CX0 - 0.08, (d[0] + d[1]) * 0.5 + 1.0, z + 2.3), V(1.0, 0.0, 0.0), 0.7, 0.17, 0.0, "rig_paint_grey", 0.01)
    b.loot("medical", V(x0 + 1.6, y1 - 0.6, z))
    b.loot("medical", V(x1 - 0.6, y0 + 2.4, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", True)


def showers(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    for k in range(3):
        cy = y0 + 0.6 + k * 1.2
        box(part, "ceramic", x1 - 1.0, x1 - 0.05, cy - 0.5, cy + 0.5, z, z + 0.08)
        box(part, "rig_paint_grey", x1 - 1.0, x1 - 0.05, cy + 0.5, cy + 0.53, z, z + 2.0)
        tube(part, "rig_steel", V(x1 - 0.1, cy, z + 1.0), V(x1 - 0.1, cy, z + 2.0), 0.012, 5)
        tube(part, "rig_steel", V(x1 - 0.1, cy, z + 2.0), V(x1 - 0.35, cy, z + 1.95), 0.012, 5)
        col(b, "metal", "shower", x1 - 1.0, x1 - 0.05, cy + 0.48, cy + 0.55, z, z + 2.0)
    for y in (y1 - 0.45, y0 + 0.5):
        tp.basin(b, part, V(x0 + 0.28, y, z), face_east, rng, 12)
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", False)


def cabin(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    door_y = (d[0] + d[1]) * 0.5
    far_low = abs(door_y - y1) < abs(door_y - y0)
    far_y = y0 + 0.5 if far_low else y1 - 0.5
    near_y = y1 - 0.3 if far_low else y0 + 0.3
    outer = x0 if side == "west" else x1
    inward = 1.0 if side == "west" else -1.0
    bx = outer + inward * 1.05
    bunk(b, part, bx, far_y, z, 0.0, rng)
    bunk(b, part, bx + inward * 2.05, far_y, z, 0.0, rng)
    region = rng.choice(["blue", "green", "cream"])
    wall_facing = face_south if far_low else face_north
    chair_facing = face_north if far_low else face_south
    tp.locker_row(b, part, V(outer + inward * 0.9, near_y, z), wall_facing, 3, rng, region, 1.85, 0.5, 0.42)
    desk(b, part, parts["clutter"], outer + inward * 2.5, near_y, z, wall_facing, rng, 1.0, 0.55)
    office_chair(part, V(outer + inward * 2.5, near_y + (-0.65 if far_low else 0.65), z), chair_facing, rng, rng.random() < 0.25)
    if rng.random() < 0.6:
        bd.suitcase(parts["clutter"], V(outer + inward * 3.3, (y0 + y1) * 0.5, z), rng.uniform(0.0, 6.0), rng, rng.random() < 0.5)
    notice(parts["fittings"], V(outer + inward * 3.0, far_y + (-0.48 if far_low else 0.48), z + 1.5), V(0.0, 1.0 if far_low else -1.0, 0.0), rng, rng.choice(["poster", "calendar", "card"]), 0.8)
    if rng.random() < 0.5:
        b.loot("box", V(outer + inward * 3.6, (y0 + y1) * 0.5 + (0.6 if far_low else -0.6), z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "warm", rng.random() < 0.75, 0.8)


def oim(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    desk(b, part, parts["clutter"], x0 + 1.6, (y0 + y1) * 0.5, z, face_east, rng, 1.6, 0.8)
    office_chair(part, V(x0 + 0.95, (y0 + y1) * 0.5, z), face_east, rng)
    for k in range(2):
        plastic_chair(part, V(x0 + 2.6, (y0 + y1) * 0.5 - 0.5 + k, z), face_west, rng, "fabric_worn")
    for k in range(3):
        tp.filing_cabinet(b, part, V(x1 - 0.4, y0 + 0.5 + k * 0.6, z), face_west, rng, 4, "cream")
    tp.bookcase(b, part, parts["clutter"], V(x0 + 2.4, y1 - 0.2, z), face_south, rng, 1.0, 1.8, 0.3, "timber_beam", 0.7)
    notice(parts["fittings"], V(x0 + 0.03, y0 + 1.0, z + 1.6), V(1.0, 0.0, 0.0), rng, "calendar")
    tp.wall_clock(parts["fittings"], V(x0 + 0.04, y1 - 1.2, z + 2.2), V(1.0, 0.0, 0.0), rng)
    b.loot("box", V(x0 + 0.6, y1 - 0.6, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "warm", True)


def office(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    for k in range(2):
        cy = y0 + 1.2 + k * 2.4
        desk(b, part, parts["clutter"], x0 + 0.8, cy, z, face_east, rng, 1.2, 0.7)
        office_chair(part, V(x0 + 1.5, cy, z), face_west, rng, k == 1)
        screen(parts["clutter"], V(x0 + 0.65, cy + 0.2, z + 0.76), face_east, rng, 0.36)
    for k in range(2):
        tp.filing_cabinet(b, part, V(x1 - 0.4, y0 + 0.5 + k * 0.6, z), face_west, rng, 4, "green")
    tp.papers(parts["clutter"], x0 + 1.5, x0 + 3.5, y0 + 1.5, y0 + 3.5, z + 0.01, 6, rng, ("letter", "notice", "envelope", "newspaper"))
    b.loot("box", V(x0 + 2.4, y0 + 0.6, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", True)


def control(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    clutter = parts["clutter"]
    console_run(b, part, clutter, x0 + 0.6, x1 - 1.5, y0 + 2.3, z, 1.0, rng)
    console_run(b, part, clutter, x0 + 0.3, x0 + 1.2, y0 + 4.2, z, -1.0, rng, 0.8)
    for k in range(3):
        office_chair(part, V(x0 + 1.3 + k * 1.4, y0 + 3.6, z), face_south, rng, k == 2)
    console_column(b, part, clutter, y0 + 5.6, y1 - 2.6, x0 + 0.05, z, rng)
    for k in range(2):
        office_chair(part, V(x0 + 1.5, y0 + 6.4 + k * 1.6, z), face_west + rng.uniform(-0.4, 0.4), rng, k == 1)
    panel = V((x0 + x1) * 0.5 - 0.6, y1 - 0.06, z + 1.4)
    box(parts["fittings"], "rig_paint_grey", panel.x - 1.1, panel.x + 1.1, y1 - 0.35, y1 - 0.02, z, z + 2.1, "box", 0.02)
    tk.atlas_panel(parts["fittings"], "rig_signs", V(panel.x, y1 - 0.36, z + 1.35), V(0.0, -1.0, 0.0), 1.9, 0.95, lib.region_uv(lib.signs, "mimic"), 0.0, 0.004)
    ok.sign(parts["fittings"], "danger", V(panel.x, y1 - 0.37, z + 1.97), V(0.0, -1.0, 0.0), 1.3, 0.2, 0.0, "rig_paint_grey", 0.005)
    col(b, "metal", "fg_panel", panel.x - 1.1, panel.x + 1.1, y1 - 0.35, y1 - 0.02, z, z + 2.1)
    for k in range(3):
        cx = x0 + 1.0 + k * 1.2
        ok.path_tube(clutter, "rig_rubber", [V(cx, y0 + 2.4, z + 0.02), V(cx + 0.3, y0 + 3.5, z + 0.02), V(cx + 0.1, y0 + 5.0, z + 0.02), V(x0 + 0.5, y0 + 6.0 + k * 0.3, z + 0.02)], 0.015, 5, True, 2.0)
    wall_x = x1 - 0.08
    for k in range(3):
        cy = y0 + 5.2 + k * 2.2
        tk.atlas_panel(parts["fittings"], "rig_signs", V(wall_x, cy, z + 1.6), V(-1.0, 0.0, 0.0), 2.0, 1.0, lib.region_uv(lib.signs, "mimic"), 0.0, 0.01)
        box(parts["fittings"], "rig_paint_grey", wall_x, wall_x + 0.06, cy - 1.04, cy + 1.04, z + 1.06, z + 2.14)
    esd = V(x1 - 0.3, y0 + 4.2, z)
    box(part, "rig_paint_grey", esd.x - 0.25, esd.x + 0.25, esd.y - 0.6, esd.y + 0.6, z, z + 1.1)
    tk.atlas_panel(part, "rig_signs", V(esd.x - 0.26, esd.y, z + 1.35), V(-1.0, 0.0, 0.0), 0.9, 0.55, lib.region_uv(lib.signs, "esd"), 0.0, 0.004)
    box(part, "rig_paint_grey", esd.x - 0.25, esd.x + 0.25, esd.y - 0.6, esd.y + 0.6, z + 1.1, z + 1.65)
    col(b, "metal", "esd", esd.x - 0.25, esd.x + 0.25, esd.y - 0.6, esd.y + 0.6, z, z + 1.65)
    table(b, part, x0 + 2.4, y1 - 1.6, z, 2.2, 1.0, rng, "timber_beam", "rig_paint_grey", "plan_table")
    tp.papers(clutter, x0 + 1.5, x0 + 3.3, y1 - 2.0, y1 - 1.2, z + 0.75, 5, rng, ("newspaper", "notice", "letter", "card"))
    tk.atlas_panel(clutter, "rig_signs", V(x0 + 2.2, y1 - 1.5, z + 0.755), up, 1.1, 0.18, lib.region_uv(lib.signs, "chart"), 0.3, 0.001)
    for k in range(2):
        tp.cup_light(clutter, V(x0 + 1.0 + k * 2.0, y0 + 2.6, z + 0.75), rng)
    tp.telephone(clutter, V(x0 + 3.6, y0 + 2.5, z + 0.75), 0.0, rng)
    tp.papers(clutter, x0 + 1.0, x0 + 4.0, y0 + 0.5, y0 + 1.8, z + 0.01, 7, rng, ("letter", "notice", "envelope"))
    ok.sign(parts["fittings"], "control_room", V(CX0 - 0.08, 1.8, z + 2.3), V(1.0, 0.0, 0.0), 0.9, 0.22, 0.0, "rig_paint_grey", 0.01)
    b.loot("military", V(x1 - 0.6, y1 - 0.6, z))
    b.loot("military", V(x0 + 0.6, y0 + 0.6, z))
    room_light(b, parts, (x0 + x1) * 0.5, y0 + 2.6, top, "cold", True, 1.2, True)
    room_light(b, parts, (x0 + x1) * 0.5, y0 + 7.5, top, "cold", True, 1.2, True)
    room_light(b, parts, (x0 + x1) * 0.5, y1 - 1.6, top, "cold", False, 1.2, True, 0.4)


def radio(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    clutter = parts["clutter"]
    for k in range(3):
        cx = x0 + 0.75 + k * 0.75
        box(part, "rig_paint_grey", cx - 0.35, cx + 0.35, y0 + 0.05, y0 + 0.65, z, z + 2.0, "box", 0.02)
        for row in range(3):
            tk.atlas_panel(part, "rig_signs", V(cx, y0 + 0.66, z + 0.6 + row * 0.5), V(0.0, 1.0, 0.0), 0.6, 0.22, lib.region_uv(lib.signs, "radio_face"), 0.0, 0.003)
        col(b, "metal", "rack", cx - 0.35, cx + 0.35, y0 + 0.05, y0 + 0.65, z, z + 2.0)
    dx = x1 - 1.4
    desk(b, part, clutter, dx, y1 - 0.45, z, face_south, rng, 2.4, 0.7, False)
    for k in range(2):
        rig = V(dx - 0.6 + k * 1.1, y1 - 0.4, z + 0.76)
        box(clutter, "rig_paint_grey", rig.x - 0.25, rig.x + 0.25, rig.y - 0.15, rig.y + 0.15, rig.z, rig.z + 0.22)
        tk.atlas_panel(clutter, "rig_signs", V(rig.x, rig.y - 0.151, rig.z + 0.11), V(0.0, -1.0, 0.0), 0.48, 0.18, lib.region_uv(lib.signs, "radio_face"), 0.0, 0.002)
    tube(clutter, "rig_steel", V(dx + 0.9, y1 - 0.5, z + 0.76), V(dx + 0.9, y1 - 0.55, z + 1.0), 0.01, 5)
    ok.lathe(clutter, "rig_paint_grey", V(dx + 0.9, y1 - 0.55, z + 1.0), V(0.0, -1.0, 0.0), [(0.0, 0.0), (0.03, 0.0), (0.03, 0.06), (0.0, 0.06)], 8)
    office_chair(part, V(dx, y1 - 1.2, z), face_north, rng)
    tp.papers(clutter, dx - 0.8, dx + 0.6, y1 - 0.7, y1 - 0.25, z + 0.76, 3, rng, ("letter", "notice"))
    notice(parts["fittings"], V(x1 - 0.03, y0 + 1.6, z + 1.5), V(-1.0, 0.0, 0.0), rng, "notice")
    ok.sign(parts["fittings"], "radio_room", V(CX1 + 0.08, (d[0] + d[1]) * 0.5 - 1.0, z + 2.3), V(-1.0, 0.0, 0.0), 0.7, 0.17, 0.0, "rig_paint_grey", 0.01)
    b.loot("box", V(22.8, -5.2, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", True)


def meeting(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    tx = (x0 + x1) * 0.5
    ty = (y0 + y1) * 0.5 + 0.4
    table(b, part, tx, ty, z, 1.2, 3.6, rng, "timber_beam", "rig_paint_grey", "meeting_table")
    for k in range(4):
        for sx, yaw in ((-0.85, face_east), (0.85, face_west)):
            plastic_chair(part, V(tx + sx, ty - 1.4 + k * 0.95, z), yaw + rng.uniform(-0.3, 0.3), rng, "fabric_worn", rng.random() < 0.15)
    board = V(tx, y1 - 0.04, z + 1.5)
    box(parts["fittings"], "rig_paint_white", board.x - 1.0, board.x + 1.0, board.y - 0.02, board.y, board.z - 0.6, board.z + 0.6)
    tp.papers(parts["clutter"], tx - 0.4, tx + 0.4, ty - 1.4, ty + 1.4, z + 0.75, 5, rng, ("letter", "notice", "card"))
    room_light(b, parts, tx, ty, top, "cold", True, 1.2, False)


def archive(b, parts, x0, x1, y0, y1, z, top, side, d, rng):
    part = parts["furniture"]
    for k in range(4):
        tp.filing_cabinet(b, part, V(x1 - 0.4, y0 + 0.6 + k * 0.62, z), face_west, rng, 4, rng.choice(["green", "cream"]))
    shelves(b, part, x0 + 0.05, x0 + 0.45, y0 + 1.6, y1 - 0.3, z, rng, 5, 2.0)
    desk(b, part, parts["clutter"], (x0 + x1) * 0.5, y1 - 0.5, z, face_south, rng, 1.4, 0.7)
    office_chair(part, V((x0 + x1) * 0.5, y1 - 1.2, z), face_north, rng, True)
    tp.papers(parts["clutter"], x0 + 1.0, x1 - 1.0, y0 + 1.0, y1 - 1.5, z + 0.01, 8, rng, ("letter", "notice", "envelope", "newspaper"))
    b.loot("box", V(x0 + 1.4, y0 + 0.6, z))
    room_light(b, parts, (x0 + x1) * 0.5, (y0 + y1) * 0.5, top, "cold", False)


rooms = {
    "lobby": lobby,
    "locker": locker,
    "galley": galley,
    "mess": mess,
    "wc": wc,
    "laundry": laundry,
    "recreation": recreation,
    "provisions": provisions,
    "medical": medical,
    "showers": showers,
    "cabin": cabin,
    "oim": oim,
    "office": office,
    "control": control,
    "radio": radio,
    "meeting": meeting,
    "archive": archive,
}


def quarters():
    b = kit.Build("rig_quarters", 7401)
    rng = b.rng
    parts = ok.setup(b, (("shell", 40.0), ("structure", 50.0), ("walls", 30.0), ("floors", 30.0), ("ceilings", 30.0), ("joinery", 40.0), ("furniture", 45.0), ("clutter", 45.0), ("fixtures", 40.0), ("fittings", 40.0), ("services", 50.0), ("rails", 50.0), ("lamps", 30.0), ("grating", 30.0), ("decals", 30.0)))
    exterior(b, parts, rng)
    floors_and_ceilings(b, parts, rng)
    partitions(b, parts, rng)
    stairs(b, parts, rng)
    furnish(b, parts, rng)
    doghouse(b, parts, rng)
    roof_dressing(b, parts, rng)
    return b


def quarters_far():
    b = kit.Build("rig_quarters_far", 7402)
    part = b.part("shell", 40.0)
    ok.far_box(part, "rig_paint_white", X0, X1, Y0, Y1, FLOORS[0] - 0.05, ROOF, ("top",), 1.0, "world")
    lift = 0.015
    for level, z in enumerate(FLOORS):
        plan = plans[level]
        for a0, a1 in plan["west_windows"]:
            ok.far_panel(part, "glass_dirty", (X0 - lift, a1), (X0 - lift, a0), z + WIN[0], z + WIN[1], V(-1.0, 0.0, 0.0))
            ok.far_box(part, "rig_paint_white", X0 - 0.18, X0, a0 - 0.05, a1 + 0.05, z + WIN[0] - 0.06, z + WIN[0], ("bottom",))
        for a0, a1 in plan["east_windows"]:
            ok.far_panel(part, "glass_dirty", (X1 + lift, a0), (X1 + lift, a1), z + WIN[0], z + WIN[1], V(1.0, 0.0, 0.0))
            ok.far_box(part, "rig_paint_white", X1, X1 + 0.18, a0 - 0.05, a1 + 0.05, z + WIN[0] - 0.06, z + WIN[0], ("bottom",))
        for a0, a1 in plan["north_windows"]:
            ok.far_panel(part, "glass_dirty", (a1, Y1 + lift), (a0, Y1 + lift), z + WIN[0], z + WIN[1], V(0.0, 1.0, 0.0))
        for a0, a1 in plan["south_windows"]:
            ok.far_panel(part, "glass_dirty", (a0, Y0 - lift), (a1, Y0 - lift), z + WIN[0], z + WIN[1], V(0.0, -1.0, 0.0))
        if level > 0:
            ok.far_box(part, "rig_paint_orange", X0 - 0.06, X1 + 0.06, Y0 - 0.06, Y1 + 0.06, z - 0.25, z - 0.03, (), 1.0, "world")
    facades = {"west": [], "east": [], "north": [], "south": []}
    for plan in plans:
        for key in facades:
            facades[key].extend(plan[key + "_windows"])
    facades["west"].append((-11.2, -10.0))
    facades["north"].append((18.0, 19.2))
    for x in pilaster_spots(X0, X1, 1.3, facades["south"]):
        ok.far_box(part, "rig_paint_white", x - 0.04, x + 0.04, Y0 - 0.05, Y0, FLOORS[0], ROOF, ("top", "bottom", "back"), 1.0, "world")
    for x in pilaster_spots(X0, X1, 1.3, facades["north"]):
        ok.far_box(part, "rig_paint_white", x - 0.04, x + 0.04, Y1, Y1 + 0.05, FLOORS[0], ROOF, ("top", "bottom", "front"), 1.0, "world")
    for y in pilaster_spots(Y0, Y1, 1.5, facades["west"]):
        ok.far_box(part, "rig_paint_white", X0 - 0.05, X0, y - 0.04, y + 0.04, FLOORS[0], ROOF, ("top", "bottom", "right"), 1.0, "world")
    for y in pilaster_spots(Y0, Y1, 1.5, facades["east"]):
        ok.far_box(part, "rig_paint_white", X1, X1 + 0.05, y - 0.04, y + 0.04, FLOORS[0], ROOF, ("top", "bottom", "left"), 1.0, "world")
    ok.far_panel(part, "soot", (X0 - lift, -10.0), (X0 - lift, -11.2), FLOORS[0], FLOORS[0] + DOOR_H, V(-1.0, 0.0, 0.0))
    ok.far_panel(part, "soot", (19.2, Y1 + lift), (18.0, Y1 + lift), FLOORS[0], FLOORS[0] + DOOR_H, V(0.0, 1.0, 0.0))
    ok.far_box(part, "rig_paint_grey", X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y1 + 0.1, ROOF, ROOF + 0.08, ("bottom",), 1.0, "world")
    for x0, x1, y0, y1 in ((X0 - 0.1, X0 + 0.05, Y0 - 0.1, Y1 + 0.1), (X1 - 0.05, X1 + 0.1, Y0 - 0.1, Y1 + 0.1), (X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y0 + 0.05), (X0 - 0.1, X1 + 0.1, Y1 - 0.05, Y1 + 0.1)):
        ok.far_box(part, "rig_paint_white", x0, x1, y0, y1, ROOF + 0.08, ROOF + 0.35, ("bottom",), 1.0, "world")
    e = 0.15
    ok.far_rail(part, [(X1 - e, STAIR[3] + 0.2), (X1 - e, Y1 - e), (X0 + e, Y1 - e), (X0 + e, Y0 + e), (STAIR[0] - 0.15, Y0 + e)], ROOF)
    x0, x1, y0, y1 = STAIR[0] - 0.1, IX1 + 0.2, Y0, STAIR[3] + 0.1
    ok.far_box(part, "rig_paint_white", x0, x1, y0, y1, ROOF, ROOF + 2.6, ("bottom", "top"), 1.0, "world")
    ok.far_box(part, "rig_paint_grey", x0 - 0.08, x1 + 0.08, y0 - 0.08, y1 + 0.08, ROOF + 2.6, ROOF + 2.72, ("bottom",), 1.0, "world")
    ok.far_panel(part, "soot", (x0 - lift, -10.2), (x0 - lift, -11.4), ROOF, ROOF + DOOR_H, V(-1.0, 0.0, 0.0))
    for cx, cy in ((14.6, -4.0), (14.6, 1.5)):
        ok.far_box(part, "rig_paint_grey", cx - 1.2, cx + 1.2, cy - 1.5, cy + 1.5, ROOF, ROOF + 1.25, ("bottom",))
        ok.lathe(part, "rig_paint_grey", V(cx, cy, ROOF + 1.25), up, [(0.7, 0.0), (0.7, 0.18), (0.0, 0.18)], 8, False)
    mast = V(13.3, -11.0, ROOF)
    for k in range(3):
        angle = k * math.pi * 2.0 / 3.0
        ok.far_tube(part, "rig_paint_white", mast + V(math.cos(angle) * 0.6, math.sin(angle) * 0.6, 0.0), mast + V(math.cos(angle) * 0.18, math.sin(angle) * 0.18, 7.5), 0.05, 3, 2.0)
    ok.far_tube(part, "rig_steel", mast + V(0.0, 0.0, 7.3), mast + V(0.0, 0.0, 10.2), 0.04, 3)
    ok.far_tube(part, "rig_steel", mast + V(-1.2, 0.0, 8.2), mast + V(1.2, 0.0, 8.2), 0.03, 3)
    dish = V(15.4, -11.0, ROOF)
    ok.far_tube(part, "rig_paint_grey", dish, dish + V(0.0, 0.0, 1.1), 0.06, 4)
    matrix = kit.Matrix.Translation(dish + V(0.0, 0.0, 1.3)) @ kit.Matrix.Rotation(0.9, 4, 'X') @ kit.Matrix.Rotation(-0.6, 4, 'Z')
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.6, 0.18), (0.0, 0.02)], 8), "rig_paint_white", matrix, "given", True)
    ok.far_path(part, "rig_paint_grey", [V(X1 + 0.25, -11.0, FLOORS[0] + 0.3), V(X1 + 0.25, -11.0, ROOF + 0.5), V(X1 - 1.0, -11.0, ROOF + 0.5)], 0.08, 4, 1.0)
    ok.far_box(part, "rig_paint_grey", X0 - 0.55, X0 - 0.15, -11.5, 11.5, FLOORS[1] - 0.64, FLOORS[1] - 0.56, ("front", "back"))
    tk.atlas_panel(part, "rig_signs", V((X0 + X1) * 0.5 + 0.6, Y0 - 0.03, FLOORS[2] + 2.65), V(0.0, -1.0, 0.0), 7.6, 0.9, lib.region_uv(lib.signs, "name_board"), 0.0, 0.01)
    tk.atlas_panel(part, "rig_signs", V(X0 - 0.03, 0.0, FLOORS[2] + 2.6), V(-1.0, 0.0, 0.0), 6.0, 0.75, lib.region_uv(lib.signs, "name_board"), 0.0, 0.01)
    return b
