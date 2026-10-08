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
from buildkit import V, Geo, emit
from oilrig_kit import box, col, tube, up

FZ = ok.drill_z
HEIGHT = 30.0
TOP = FZ + HEIGHT
CXD = (ok.drill[0] + ok.drill[1]) * 0.5
CYD = (ok.drill[2] + ok.drill[3]) * 0.5
BASE_HALF = 4.2
TOP_HALF = 1.35
GIRTS = [0.0, 4.2, 8.2, 12.0, 15.6, 19.0, 22.2, 25.2, 28.0, 30.0]
VDOOR = (-1.5, 1.5)
paint = "rig_paint_white"
accent = "rig_paint_orange"
boom_angle = math.radians(20.0)
boom_length = 40.0
walk_y = (ok.flare_root[1] - 0.5, ok.flare_root[1] + 0.5)


def half_at(h):
    return BASE_HALF + (TOP_HALF - BASE_HALF) * (h / HEIGHT)


def leg_at(sx, sy, h):
    r = half_at(h)
    return V(CXD + sx * r, CYD + sy * r, FZ + h)


def legs(b, parts, rng):
    part = parts["lattice"]
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            a = leg_at(sx, sy, 0.0)
            c = leg_at(sx, sy, HEIGHT)
            ok.angle_bar(part, paint, a, c, 0.26, 0.022, V(-sx, -sy, 0.0).normalized(), 0.0, 1.4)
            box(part, accent, a.x - 0.35, a.x + 0.35, a.y - 0.35, a.y + 0.35, FZ, FZ + 0.25, "box", 0.02)
            col(b, "metal", "derrick_leg", a.x - 0.3, a.x + 0.3, a.y - 0.3, a.y + 0.3, FZ, FZ + 3.0)


def faces(b, parts, rng):
    part = parts["lattice"]
    sides = [((-1.0, -1.0), (1.0, -1.0), "south"), ((1.0, -1.0), (1.0, 1.0), "east"), ((1.0, 1.0), (-1.0, 1.0), "north"), ((-1.0, 1.0), (-1.0, -1.0), "west")]
    for index in range(len(GIRTS) - 1):
        h0 = GIRTS[index]
        h1 = GIRTS[index + 1]
        for (ax, ay), (cx, cy), name in sides:
            a0 = leg_at(ax, ay, h0)
            c0 = leg_at(cx, cy, h0)
            a1 = leg_at(ax, ay, h1)
            c1 = leg_at(cx, cy, h1)
            vdoor = name == "north" and h1 <= 8.2
            if index > 0 and not (name == "north" and h0 < 8.0):
                ok.angle_bar(part, paint, a0, c0, 0.12, 0.012, None, 0.0, 2.0)
            if vdoor:
                if index == 0:
                    top_mid = (leg_at(ax, ay, 8.2) + leg_at(cx, cy, 8.2)) * 0.5
                    tube(part, paint, a0, top_mid + (a0 - c0).normalized() * 1.2, 0.07, 6, True, 2.0)
                    tube(part, paint, c0, top_mid + (c0 - a0).normalized() * 1.2, 0.07, 6, True, 2.0)
                continue
            tube(part, paint, a0, c1, 0.055, 6, True, 2.0)
            tube(part, paint, c0, a1, 0.055, 6, True, 2.0)
    for h in (GIRTS[3], GIRTS[6]):
        for sx in (-1.0, 1.0):
            a = leg_at(sx, -1.0, h)
            c = leg_at(-sx, 1.0, h)
            tube(part, paint, a, c, 0.05, 6, True, 2.0)


def crown(b, parts, rng):
    part = parts["lattice"]
    r = TOP_HALF + 0.9
    z = TOP
    box(part, accent, CXD - r, CXD + r, CYD - r, CYD + r, z, z + 0.25, "box", 0.0, 1.2)
    ok.grating(parts["grating"], CXD - r, CXD + r, CYD - r, CYD + r, z + 0.26)
    ok.railing(b, parts["rails"], [(CXD - r, CYD - r), (CXD + r, CYD - r), (CXD + r, CYD + r), (CXD - r, CYD + r), (CXD - r, CYD - r)], z + 0.26, rng, 1.0, "rig_paint_yellow", False, False, "crown")
    block = (CXD - 0.9, CXD + 0.9, CYD - 0.6, CYD + 0.6)
    box(part, accent, block[0], block[1], block[2], block[3], z + 0.26, z + 0.7)
    for k in range(5):
        x = block[0] + 0.25 + k * 0.33
        ok.lathe(part, "rig_paint_grey", V(x, CYD, z + 1.25), V(1.0, 0.0, 0.0), [(0.0, 0.0), (0.62, 0.0), (0.62, 0.06), (0.52, 0.12), (0.62, 0.18), (0.62, 0.24), (0.0, 0.24)], 16)
    tube(part, "rig_steel", V(block[0] - 0.1, CYD, z + 1.25), V(block[1] + 0.1, CYD, z + 1.25), 0.08, 8)
    for sx in (-1.0, 1.0):
        box(part, accent, CXD + sx * 0.95 - 0.06, CXD + sx * 0.95 + 0.06, CYD - 0.6, CYD + 0.6, z + 0.7, z + 1.95)
    for sy in (-1.0, 1.0):
        tube(part, accent, V(CXD - 1.4, CYD + sy * 1.2, z + 0.3), V(CXD, CYD + sy * 0.5, z + 4.2), 0.07, 6)
        tube(part, accent, V(CXD + 1.4, CYD + sy * 1.2, z + 0.3), V(CXD, CYD + sy * 0.5, z + 4.2), 0.07, 6)
    tube(part, accent, V(CXD, CYD - 0.5, z + 4.2), V(CXD, CYD + 0.5, z + 4.2), 0.08, 6)
    ok.lathe(part, "rig_lamp_warm", V(CXD, CYD, z + 4.3), up, [(0.0, 0.0), (0.09, 0.0), (0.09, 0.14), (0.0, 0.18)], 8)
    b.light("warm", V(CXD, CYD, z + 4.7))


def monkey_board(b, parts, rng):
    h = 21.0
    z = FZ + h
    r = half_at(h)
    part = parts["lattice"]
    y_edge = CYD + r
    ok.grating(parts["grating"], CXD - 1.4, CXD + 1.4, y_edge - 0.2, y_edge + 1.2, z)
    box(part, "rig_paint_yellow", CXD - 1.45, CXD + 1.45, y_edge - 0.25, y_edge + 1.25, z - 0.12, z - 0.02, "box", 0.0, 1.6)
    ok.railing(b, parts["rails"], [(CXD - 1.4, y_edge - 0.2), (CXD - 1.4, y_edge + 1.2), (CXD + 1.4, y_edge + 1.2), (CXD + 1.4, y_edge - 0.2)], z, rng, 1.0, "rig_paint_yellow", False, False, "monkey")
    for k in range(7):
        x = CXD - 1.5 + k * 0.5
        ok.bar(part, "rig_paint_yellow", V(x, y_edge - 1.2, z - 0.05), V(0.0, 1.0, 0.0), 2.0, 0.06, 0.08, up, 2.0)
    for k in range(4):
        base = V(CXD - 1.2 + k * 0.32, CYD + 2.4, FZ + 0.05)
        top = V(CXD - 1.25 + k * 0.32, y_edge - 0.9, z - 0.1)
        tube(parts["equipment"], "rig_steel", base, top, 0.065, 8)


def ladder(b, parts, rng):
    part = parts["lattice"]
    sx, sy = -1.0, -1.0
    foot = leg_at(sx, sy, 0.0) + V(1.0, -0.25, 0.0)
    head = leg_at(sx, sy, HEIGHT) + V(1.0, -0.25, 0.0)
    direction = (head - foot).normalized()
    rest_levels = [9.5, 19.0]
    pts = [foot, head]
    for s in (-0.22, 0.22):
        tube(part, "rig_paint_yellow", foot + V(s, 0.0, 0.0), head + V(s, 0.0, 1.0), 0.022, 6, True, ok.fine)
    steps = int((head - foot).length / 0.3)
    for k in range(1, steps):
        p = foot.lerp(head, k / steps)
        tube(part, "rig_paint_yellow", p + V(-0.22, 0.0, 0.0), p + V(0.22, 0.0, 0.0), 0.012, 4, False, ok.fine)
    hoop_count = int((HEIGHT - 2.4) / 0.9)
    for k in range(hoop_count):
        t = (2.4 + k * 0.9) / HEIGHT
        p = foot.lerp(head, t)
        points = []
        for j in range(9):
            angle = math.pi * j / 8.0
            points.append(p + V(math.cos(angle) * 0.38, -0.38 - math.sin(angle) * 0.38 + 0.0, 0.0))
        ok.path_tube(part, "rig_paint_yellow", points, 0.012, 4, False, ok.fine, up)
    for j in range(5):
        angle = math.pi * (0.1 + 0.8 * j / 4.0)
        offset = V(math.cos(angle) * 0.38, -0.38 - math.sin(angle) * 0.38, 0.0)
        tube(part, "rig_paint_yellow", foot.lerp(head, 2.4 / HEIGHT) + offset, head + offset, 0.01, 4, False, ok.fine)
    for h in rest_levels:
        p = foot.lerp(head, h / HEIGHT)
        ok.grating(parts["grating"], p.x - 0.9, p.x + 0.9, p.y - 1.0, p.y + 0.1, p.z)
        box(part, "rig_paint_yellow", p.x - 0.92, p.x + 0.92, p.y - 1.02, p.y + 0.12, p.z - 0.1, p.z - 0.02, "box", 0.0, 1.6)
        ok.railing(b, parts["rails"], [(p.x - 0.9, p.y + 0.1), (p.x - 0.9, p.y - 1.0), (p.x + 0.9, p.y - 1.0), (p.x + 0.9, p.y + 0.1)], p.z, rng, 1.0, "rig_paint_yellow", False, False, "rest")
    col(b, "metal", "ladder_cage", foot.x - 0.45, foot.x + 0.45, foot.y - 0.8, foot.y + 0.05, FZ, FZ + 2.4)


def travelling_block(b, parts, rng):
    part = parts["equipment"]
    block = V(CXD, CYD, FZ + 13.5)
    box(part, accent, block.x - 0.55, block.x + 0.55, block.y - 0.35, block.y + 0.35, block.z, block.z + 1.6, "box", 0.06)
    for k in range(4):
        ok.lathe(part, "rig_paint_grey", V(block.x - 0.45 + k * 0.3, block.y, block.z + 1.15), V(1.0, 0.0, 0.0), [(0.0, 0.0), (0.42, 0.0), (0.42, 0.18), (0.0, 0.18)], 12)
    for k in range(8):
        x = block.x - 0.5 + k * 0.14
        tube(part, "rig_steel", V(x, block.y + (0.12 if k % 2 else -0.12), block.z + 1.5), V(CXD - 0.6 + k * 0.17, CYD + (0.15 if k % 2 else -0.15), TOP + 1.2), 0.012, 4, False)
    hook = [block - V(0.0, 0.0, 0.05), block - V(0.0, 0.0, 0.9), block + V(0.0, 0.35, -1.25), block + V(0.0, 0.45, -0.85)]
    ok.path_tube(part, "rig_rust", hook, 0.07, 8, True, 1.0)
    swivel = block - V(0.0, 0.0, 1.0)
    ok.lathe(part, "rig_paint_grey", swivel - V(0.0, 0.0, 1.2), up, [(0.0, 0.0), (0.25, 0.0), (0.3, 0.3), (0.3, 0.9), (0.15, 1.2), (0.0, 1.2)], 12)
    standpipe = leg_at(1.0, -1.0, 0.0) + V(-0.6, 0.3, 0.0)
    top = leg_at(1.0, -1.0, 14.0) + V(-0.6, 0.3, 0.0)
    tube(part, "rig_paint_grey", standpipe, top, 0.07, 8)
    goose = [top, top + V(0.0, 0.0, 0.5), top + V(-0.3, 0.3, 0.7)]
    ok.path_tube(part, "rig_paint_grey", goose, 0.07, 8, True, 1.0)
    hose = [goose[-1]] + [goose[-1].lerp(swivel - V(0.0, 0.0, 0.6), t) - V(0.0, 0.0, 2.6 * math.sin(math.pi * t)) for t in (0.2, 0.4, 0.6, 0.8, 1.0)]
    ok.path_tube(part, "rig_rubber", hose, 0.08, 8, True, 1.0)
    for k in range(3):
        start = leg_at(-1.0, 1.0, rng.uniform(6.0, 18.0))
        ok.hanging_cable(part, start + V(0.4, -0.4, 0.0), rng.uniform(2.0, 6.0), rng, 0.02)


def flare(b, parts, rng):
    part = parts["flare"]
    root = V(ok.flare_root[0], ok.flare_root[1], ok.main)
    forward = V(-math.cos(boom_angle), 0.0, math.sin(boom_angle))
    side = V(0.0, 1.0, 0.0)
    normal = forward.cross(side) * -1.0
    if normal.z < 0.0:
        normal = -normal
    sections = 20

    def width(t):
        return 3.0

    def frame(t, offset_side, offset_up):
        return root + forward * (boom_length * t) + side * offset_side + normal * offset_up

    chords = []
    for s in (-1.0, 1.0):
        chords.append([frame(k / sections, s * width(k / sections) * 0.5, -0.05) for k in range(sections + 1)])
    chords.append([frame(k / sections, 0.0, 3.2) for k in range(sections + 1)])
    for points in chords:
        ok.path_tube(part, "rig_paint_orange", points, 0.08, 6, True, 1.4, normal)
    for k in range(sections):
        t0 = k / sections
        t1 = (k + 1) / sections
        for a, c in ((chords[0][k], chords[2][k + 1]), (chords[1][k], chords[2][k + 1]), (chords[0][k + 1], chords[2][k]), (chords[1][k + 1], chords[2][k])):
            if (k % 2 == 0) == (a == chords[0][k] or a == chords[1][k]):
                tube(part, "rig_paint_orange" if k % 4 < 2 else "rig_paint_white", a, c, 0.045, 5, False, 2.0)
        tube(part, "rig_paint_orange", chords[0][k], chords[1][k], 0.04, 5, False, 2.0)
        tube(part, "rig_paint_orange", chords[0][k], chords[2][k], 0.04, 5, False, 2.0)
        tube(part, "rig_paint_orange", chords[1][k], chords[2][k], 0.04, 5, False, 2.0)
    walk = []
    for k in range(sections):
        t0 = k / sections
        t1 = (k + 1) / sections
        corners = [frame(t0, -0.5, 0.02), frame(t1, -0.5, 0.02), frame(t1, 0.5, 0.02), frame(t0, 0.5, 0.02)]
        emit(parts["grating"], Geo(corners, [kit.orient((0, 1, 2, 3), corners, normal)]), "rig_grating", None, "world")
    for s in (-1.0, 1.0):
        rail = [frame(k / 4.0, s * 0.62, 1.05) for k in range(5)]
        ok.path_tube(part, "rig_paint_yellow", rail, 0.025, 6, True, ok.fine, normal)
        mid_rail = [frame(k / 4.0, s * 0.62, 0.55) for k in range(5)]
        ok.path_tube(part, "rig_paint_yellow", mid_rail, 0.02, 6, True, ok.fine, normal)
        for k in range(int(boom_length / 1.8)):
            p = frame(k * 1.8 / boom_length, s * 0.62, 0.0)
            tube(part, "rig_paint_yellow", p, p + normal * 1.05, 0.02, 5, False, ok.fine)
    pipe_points = [frame(k / 4.0, 1.25, 2.3) for k in range(4)]
    tip = frame(1.0, 0.0, 0.0)
    pipe_points.append(V(tip.x - 1.0, tip.y + 1.25, tip.z + 2.0))
    pipe_points.append(V(tip.x - 1.0, tip.y, tip.z + 1.6))
    ok.path_tube(part, "rig_paint_grey", [V(root.x + 0.3, root.y + 1.25, ok.main - 1.6), V(root.x + 0.3, root.y + 1.25, ok.main + 1.6)] + pipe_points, 0.3, 10, True, 1.0, up)
    for k in range(1, 4):
        ok.ring(part, "rig_paint_grey", frame(k / 4.0, 1.25, 2.3), forward, 0.3, 0.03, 0.12, 10)
        tube(part, "rig_paint_orange", frame(k / 4.0, 1.25, 2.0), frame(k / 4.0, 1.5, -0.05), 0.05, 5, False, 2.0)
    stack_base = V(tip.x - 1.0, tip.y, tip.z + 0.1)
    platform = (stack_base.x - 1.6, stack_base.x + 1.6, stack_base.y - 1.6, stack_base.y + 1.6)
    ok.grating(parts["grating"], platform[0], platform[1], platform[2], platform[3], stack_base.z)
    box(part, "rig_paint_orange", platform[0], platform[1], platform[2], platform[3], stack_base.z - 0.2, stack_base.z - 0.03, "box", 0.0, 1.2)
    ok.railing(b, parts["rails"], [(platform[1], platform[3]), (platform[0], platform[3]), (platform[0], platform[2]), (platform[1], platform[2])], stack_base.z, rng, 1.1, "rig_paint_yellow", True, False, "flare_tip", 0.0, 0.25)
    col(b, "grate", "flare_tip", platform[0], platform[1], platform[2], platform[3], stack_base.z - 0.3, stack_base.z)
    ok.lathe(part, "rig_rust", stack_base, up, [(0.0, 0.0), (0.45, 0.0), (0.45, 2.4), (0.55, 2.5), (0.55, 3.2), (0.0, 3.2)], 14)
    for k in range(10):
        angle = math.pi * 2.0 * k / 10.0
        if rng.random() < 0.3:
            continue
        p = stack_base + V(math.cos(angle) * 0.75, math.sin(angle) * 0.75, 2.7)
        tilt = V(math.cos(angle), math.sin(angle), 0.0) * rng.uniform(0.0, 0.25)
        emit(part, kit.geo_box(0.04, 0.5, 1.2), "rig_rust", kit.place(p + tilt * 0.5, V(math.cos(angle), math.sin(angle), 0.0), up), "box")
    col(b, "metal", "flare_stack", stack_base.x - 0.55, stack_base.x + 0.55, stack_base.y - 0.55, stack_base.y + 0.55, stack_base.z, stack_base.z + 3.2)
    ok.decal(parts["decals"], "scorch", stack_base + V(0.0, -0.58, 2.3), V(0.0, -1.0, 0.0), 1.4, 1.6)
    ok.decal(parts["decals"], "scorch", stack_base + V(0.0, 0.58, 2.3), V(0.0, 1.0, 0.0), 1.4, 1.6)
    ok.decal(parts["decals"], "scorch", stack_base + V(0.58, 0.0, 2.3), V(1.0, 0.0, 0.0), 1.4, 1.6)
    pilot = [V(stack_base.x + 0.3, stack_base.y + 0.5, stack_base.z + 3.0)] + [frame(t, 0.4, 0.8) for t in (0.95, 0.6, 0.3, 0.0)]
    ok.path_tube(part, "rig_steel", pilot, 0.02, 5, True, 2.0)
    strut_foot = V(root.x, root.y, ok.cellar + 0.4)
    strut_head = frame(0.32, 0.0, -0.1)
    tube(part, "rig_paint_orange", strut_foot, strut_head, 0.22, 10, True, 1.2)
    for s in (-1.0, 1.0):
        tube(part, "rig_paint_orange", strut_foot + V(0.0, s * 0.4, 0.0), frame(0.32, s * width(0.32) * 0.5, -0.05), 0.08, 6, True, 1.6)
    ok.lathe(part, "rig_paint_grey", root + V(0.0, -1.1, -0.45), V(0.0, 1.0, 0.0), [(0.0, 0.0), (0.25, 0.0), (0.25, 2.2), (0.0, 2.2)], 10)
    for s in (-1.0, 1.0):
        box(part, "rig_paint_orange", root.x - 0.3, root.x + 0.3, root.y + s * 1.0 - 0.1, root.y + s * 1.0 + 0.1, ok.main - 1.2, ok.main + 0.35)
    tip_z = frame(1.0, 0.0, 0.0).z
    low = V(stack_base.x - 0.6, walk_y[0], ok.main)
    high = V(root.x, walk_y[1], tip_z)
    b.ramp("nx", "grate", "flare_walk", V(frame(1.0, 0.0, 0.0).x, walk_y[0], ok.main), V(root.x, walk_y[1], tip_z))
    for y in (walk_y[0] - 0.12, walk_y[1] + 0.12):
        col(b, "metal", "flare_side", frame(1.0, 0.0, 0.0).x, root.x, y - 0.05, y + 0.05, ok.main, tip_z + 1.1)
    ok.floodlight(b, part, parts["lamps"], frame(0.5, 0.0, 2.0), V(-0.4, 0.0, -1.0), "cold", False, True, rng)


def derrick():
    b = kit.Build("rig_derrick", 7601)
    rng = b.rng
    parts = ok.setup(b, (("lattice", 50.0), ("equipment", 45.0), ("flare", 50.0), ("rails", 50.0), ("lamps", 30.0), ("grating", 30.0), ("decals", 30.0)))
    legs(b, parts, rng)
    faces(b, parts, rng)
    crown(b, parts, rng)
    monkey_board(b, parts, rng)
    ladder(b, parts, rng)
    travelling_block(b, parts, rng)
    flare(b, parts, rng)
    return b


def derrick_far():
    b = kit.Build("rig_derrick_far", 7602)
    part = b.part("shell", 50.0)
    grate = b.part("grating", 30.0)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            ok.far_tube(part, paint, leg_at(sx, sy, 0.0), leg_at(sx, sy, HEIGHT), 0.2, 4, 1.4)
    sides = [((-1.0, -1.0), (1.0, -1.0), "south"), ((1.0, -1.0), (1.0, 1.0), "east"), ((1.0, 1.0), (-1.0, 1.0), "north"), ((-1.0, 1.0), (-1.0, -1.0), "west")]
    for index in range(len(GIRTS) - 1):
        h0 = GIRTS[index]
        h1 = GIRTS[index + 1]
        for (ax, ay), (cx, cy), name in sides:
            a0 = leg_at(ax, ay, h0)
            c0 = leg_at(cx, cy, h0)
            a1 = leg_at(ax, ay, h1)
            c1 = leg_at(cx, cy, h1)
            if index > 0 and not (name == "north" and h0 < 8.0):
                ok.far_bar(part, paint, a0, c0, 0.12, 0.12, None, 2.0)
            if name == "north" and h1 <= 8.2:
                if index == 0:
                    top_mid = (leg_at(ax, ay, 8.2) + leg_at(cx, cy, 8.2)) * 0.5
                    ok.far_tube(part, paint, a0, top_mid + (a0 - c0).normalized() * 1.2, 0.08, 3, 2.0)
                    ok.far_tube(part, paint, c0, top_mid + (c0 - a0).normalized() * 1.2, 0.08, 3, 2.0)
                continue
            ok.far_tube(part, paint, a0, c1, 0.07, 3, 2.0)
            ok.far_tube(part, paint, c0, a1, 0.07, 3, 2.0)
    for h in (GIRTS[3], GIRTS[6]):
        for sx in (-1.0, 1.0):
            ok.far_tube(part, paint, leg_at(sx, -1.0, h), leg_at(-sx, 1.0, h), 0.06, 3, 2.0)
    r = TOP_HALF + 0.9
    ok.far_box(part, accent, CXD - r, CXD + r, CYD - r, CYD + r, TOP, TOP + 0.25, (), 1.2)
    ok.flat_quad(grate, "rig_grating", CXD - r, CXD + r, CYD - r, CYD + r, TOP + 0.26)
    ok.far_rail(part, [(CXD - r, CYD - r), (CXD + r, CYD - r), (CXD + r, CYD + r), (CXD - r, CYD + r), (CXD - r, CYD - r)], TOP + 0.26, 1.0, "rig_paint_yellow", 2.4)
    ok.far_box(part, accent, CXD - 0.9, CXD + 0.9, CYD - 0.6, CYD + 0.6, TOP + 0.26, TOP + 0.7, ("bottom",))
    tube(part, "rig_paint_grey", V(CXD - 0.9, CYD, TOP + 1.25), V(CXD + 0.9, CYD, TOP + 1.25), 0.62, 8, True)
    for sy in (-1.0, 1.0):
        ok.far_tube(part, accent, V(CXD - 1.4, CYD + sy * 1.2, TOP + 0.3), V(CXD, CYD + sy * 0.5, TOP + 4.2), 0.07, 3)
        ok.far_tube(part, accent, V(CXD + 1.4, CYD + sy * 1.2, TOP + 0.3), V(CXD, CYD + sy * 0.5, TOP + 4.2), 0.07, 3)
    ok.far_tube(part, accent, V(CXD, CYD - 0.5, TOP + 4.2), V(CXD, CYD + 0.5, TOP + 4.2), 0.08, 3)
    hm = 21.0
    zm = FZ + hm
    y_edge = CYD + half_at(hm)
    ok.flat_quad(grate, "rig_grating", CXD - 1.4, CXD + 1.4, y_edge - 0.2, y_edge + 1.2, zm)
    ok.far_box(part, "rig_paint_yellow", CXD - 1.45, CXD + 1.45, y_edge - 0.25, y_edge + 1.25, zm - 0.12, zm - 0.02, (), 1.6)
    ok.far_rail(part, [(CXD - 1.4, y_edge - 0.2), (CXD - 1.4, y_edge + 1.2), (CXD + 1.4, y_edge + 1.2), (CXD + 1.4, y_edge - 0.2)], zm, 1.0, "rig_paint_yellow", 1.5)
    foot = leg_at(-1.0, -1.0, 0.0) + V(1.0, -0.25, 0.0)
    head = leg_at(-1.0, -1.0, HEIGHT) + V(1.0, -0.25, 0.0)
    for s in (-0.22, 0.22):
        ok.far_tube(part, "rig_paint_yellow", foot + V(s, 0.0, 0.0), head + V(s, 0.0, 1.0), 0.03, 3, ok.fine)
    for h in (9.5, 19.0):
        p = foot.lerp(head, h / HEIGHT)
        ok.far_box(part, "rig_paint_yellow", p.x - 0.92, p.x + 0.92, p.y - 1.02, p.y + 0.12, p.z - 0.1, p.z, (), 1.6)
        ok.far_rail(part, [(p.x - 0.9, p.y + 0.1), (p.x - 0.9, p.y - 1.0), (p.x + 0.9, p.y - 1.0), (p.x + 0.9, p.y + 0.1)], p.z, 1.0, "rig_paint_yellow", 2.0)
    block = V(CXD, CYD, FZ + 13.5)
    ok.far_box(part, accent, block.x - 0.55, block.x + 0.55, block.y - 0.35, block.y + 0.35, block.z, block.z + 1.6)
    for dx in (-0.3, 0.3):
        ok.far_tube(part, "rig_steel", V(block.x + dx, block.y, block.z + 1.5), V(CXD + dx, CYD, TOP + 1.2), 0.04, 3)
    ok.far_path(part, "rig_rust", [block - V(0.0, 0.0, 0.05), block - V(0.0, 0.0, 0.9), block + V(0.0, 0.35, -1.25), block + V(0.0, 0.45, -0.85)], 0.07, 4, 1.0)
    standpipe = leg_at(1.0, -1.0, 0.0) + V(-0.6, 0.3, 0.0)
    pipe_top = leg_at(1.0, -1.0, 14.0) + V(-0.6, 0.3, 0.0)
    ok.far_tube(part, "rig_paint_grey", standpipe, pipe_top, 0.07, 4)
    swivel = block - V(0.0, 0.0, 1.0)
    goose_end = pipe_top + V(-0.3, 0.3, 0.7)
    ok.far_path(part, "rig_rubber", [goose_end] + [goose_end.lerp(swivel - V(0.0, 0.0, 0.6), t) - V(0.0, 0.0, 2.6 * math.sin(math.pi * t)) for t in (0.25, 0.5, 0.75, 1.0)], 0.08, 4, 1.0)
    flare_far(part, grate)
    return b


def flare_far(part, grate):
    root = V(ok.flare_root[0], ok.flare_root[1], ok.main)
    forward = V(-math.cos(boom_angle), 0.0, math.sin(boom_angle))
    side = V(0.0, 1.0, 0.0)
    normal = forward.cross(side) * -1.0
    if normal.z < 0.0:
        normal = -normal

    def frame(t, offset_side, offset_up):
        return root + forward * (boom_length * t) + side * offset_side + normal * offset_up

    chords = [lambda t: frame(t, -1.5, -0.05), lambda t: frame(t, 1.5, -0.05), lambda t: frame(t, 0.0, 3.2)]
    for chord in chords:
        ok.far_tube(part, "rig_paint_orange", chord(0.0), chord(1.0), 0.1, 4, 1.4)
    sections = 10
    for k in range(sections):
        t0 = k / sections
        t1 = (k + 1) / sections
        for lower in (chords[0], chords[1]):
            ok.far_tube(part, "rig_paint_orange" if k % 2 == 0 else "rig_paint_white", lower(t0 if k % 2 == 0 else t1), chords[2](t1 if k % 2 == 0 else t0), 0.05, 3, 2.0)
            ok.far_tube(part, "rig_paint_orange", lower(t0), chords[2](t0), 0.045, 3, 2.0)
        ok.far_tube(part, "rig_paint_orange", chords[0](t0), chords[1](t0), 0.045, 3, 2.0)
    for lower in (chords[0], chords[1]):
        ok.far_tube(part, "rig_paint_orange", lower(1.0), chords[2](1.0), 0.045, 3, 2.0)
    corners = [frame(0.0, -0.5, 0.02), frame(1.0, -0.5, 0.02), frame(1.0, 0.5, 0.02), frame(0.0, 0.5, 0.02)]
    emit(grate, Geo(corners, [kit.orient((0, 1, 2, 3), corners, normal)]), "rig_grating", None, "world")
    for s in (-1.0, 1.0):
        ok.far_bar(part, "rig_paint_yellow", frame(0.0, s * 0.62, 1.05), frame(1.0, s * 0.62, 1.05), 0.05, 0.05, normal, ok.fine)
        for k in range(6):
            p = frame(k / 5.0, s * 0.62, 0.0)
            ok.far_bar(part, "rig_paint_yellow", p, p + normal * 1.05, 0.04, 0.04, forward, ok.fine)
    tip = frame(1.0, 0.0, 0.0)
    pipe_points = [V(root.x + 0.3, root.y + 1.25, ok.main - 1.6), V(root.x + 0.3, root.y + 1.25, ok.main + 1.6)] + [frame(k / 4.0, 1.25, 2.3) for k in range(4)]
    pipe_points += [V(tip.x - 1.0, tip.y + 1.25, tip.z + 2.0), V(tip.x - 1.0, tip.y, tip.z + 1.6)]
    ok.far_path(part, "rig_paint_grey", pipe_points, 0.3, 6, 1.0, up)
    stack_base = V(tip.x - 1.0, tip.y, tip.z + 0.1)
    platform = (stack_base.x - 1.6, stack_base.x + 1.6, stack_base.y - 1.6, stack_base.y + 1.6)
    ok.flat_quad(grate, "rig_grating", platform[0], platform[1], platform[2], platform[3], stack_base.z)
    ok.far_box(part, "rig_paint_orange", platform[0], platform[1], platform[2], platform[3], stack_base.z - 0.2, stack_base.z - 0.03, (), 1.2)
    ok.far_rail(part, [(platform[1], platform[3]), (platform[0], platform[3]), (platform[0], platform[2]), (platform[1], platform[2])], stack_base.z, 1.1, "rig_paint_yellow", 1.8)
    ok.lathe(part, "rig_rust", stack_base, up, [(0.45, 0.0), (0.45, 2.4), (0.55, 2.5), (0.55, 3.2), (0.0, 3.2)], 8)
    strut_foot = V(root.x, root.y, ok.cellar + 0.4)
    ok.far_tube(part, "rig_paint_orange", strut_foot, frame(0.32, 0.0, -0.1), 0.22, 6, 1.2)
    for s in (-1.0, 1.0):
        ok.far_tube(part, "rig_paint_orange", strut_foot + V(0.0, s * 0.4, 0.0), frame(0.32, s * 1.5, -0.05), 0.08, 4, 1.6)
        ok.far_box(part, "rig_paint_orange", root.x - 0.3, root.x + 0.3, root.y + s * 1.0 - 0.1, root.y + s * 1.0 + 0.1, ok.main - 1.2, ok.main + 0.35)
