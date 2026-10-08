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

CX, CY = ok.heli_center
H = ok.heli_half
TAN = math.tan(math.radians(22.5)) * H
Z = ok.heli_z
DEPTH = 0.6
NET = 1.5
STAIR_X = (17.2, 18.4)
STAIR_FOOT = -9.36
ROOF = ok.roof


def outline(inset=0.0):
    h = H - inset
    t = TAN - inset * math.tan(math.radians(22.5))
    return [(CX + h, CY - t), (CX + h, CY + t), (CX + t, CY + h), (CX - t, CY + h), (CX - h, CY + t), (CX - h, CY - t), (CX - t, CY - h), (CX + t, CY - h)]


def y_extent(x):
    dx = abs(x - CX)
    if dx <= TAN:
        reach = H
    else:
        reach = H + TAN - dx
    return CY - reach, CY + reach


def x_extent(y):
    dy = abs(y - CY)
    if dy <= TAN:
        reach = H
    else:
        reach = H + TAN - dy
    return CX - reach, CX + reach


def flat_polygon(part, name, points, z, lift=0.003):
    pts = [V(x, y, z + lift) for x, y in points]
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), points, [], z + lift - 0.002, z + lift, False)
    geo.faces = [face for face in geo.faces if kit.newell([geo.points[i] for i in face]).z > 0.0]
    emit(part, geo, name, None, "world")


def ring_polygons(part, name, cx, cy, r0, r1, z, segments=48):
    for k in range(segments):
        a0 = math.pi * 2.0 * k / segments
        a1 = math.pi * 2.0 * (k + 1) / segments
        quad = [(cx + math.cos(a0) * r0, cy + math.sin(a0) * r0), (cx + math.cos(a0) * r1, cy + math.sin(a0) * r1), (cx + math.cos(a1) * r1, cy + math.sin(a1) * r1), (cx + math.cos(a1) * r0, cy + math.sin(a1) * r0)]
        flat_polygon(part, name, quad, z)


def text_geometry(body, size, font_file="STENCIL.TTF", resolution=12):
    bpy = kit.bpy
    curve = bpy.data.curves.new("deck_text", 'FONT')
    curve.body = body
    curve.size = size
    curve.resolution_u = resolution
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.fill_mode = 'FRONT'
    folder = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    for candidate in (font_file, "arialbd.ttf"):
        path = os.path.join(folder, candidate)
        if os.path.exists(path):
            curve.font = bpy.data.fonts.load(path, check_existing=True)
            break
    obj = bpy.data.objects.new("deck_text", curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [V(v.co.x, v.co.y, 0.0) for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    evaluated.to_mesh_clear()
    bpy.data.objects.remove(obj)
    bpy.data.curves.remove(curve)
    return points, faces


def painted_text(part, name, body, center, height, max_width, z, rotation=0.0, resolution=12):
    points, faces = text_geometry(body, height, "STENCIL.TTF", resolution)
    if not points:
        return
    width = max(p.x for p in points) - min(p.x for p in points)
    scale = min(1.0, max_width / max(width, 1e-3))
    c = math.cos(rotation)
    s = math.sin(rotation)
    placed = [V(center.x + (p.x * c - p.y * s) * scale, center.y + (p.x * s + p.y * c) * scale, z + 0.004) for p in points]
    oriented = []
    for face in faces:
        oriented.append(kit.orient(face, placed, up))
    emit(part, Geo(placed, oriented), name, None, "world")


def deck(b, parts, rng):
    part = parts["deck"]
    pts = outline()
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), pts, [], Z - 0.06, Z)
    emit(part, geo, "rig_deck_green", None, "world")
    marks = parts["marks"]
    outer = outline(0.08)
    inner = outline(0.42)
    for k in range(8):
        a = outer[k]
        c = outer[(k + 1) % 8]
        d = inner[(k + 1) % 8]
        e = inner[k]
        flat_polygon(marks, "rig_mark_white", [a, c, d, e], Z)
    ring_polygons(marks, "rig_paint_yellow", CX, CY, 4.6, 5.6, Z, 56)
    hx0, hx1 = CX - 1.5, CX + 1.5
    hy0, hy1 = CY - 2.0, CY + 2.0
    stroke = 0.75
    flat_polygon(marks, "rig_mark_white", [(hx0, hy0), (hx0 + stroke, hy0), (hx0 + stroke, hy1), (hx0, hy1)], Z)
    flat_polygon(marks, "rig_mark_white", [(hx1 - stroke, hy0), (hx1, hy0), (hx1, hy1), (hx1 - stroke, hy1)], Z)
    flat_polygon(marks, "rig_mark_white", [(hx0 + stroke, CY - stroke * 0.5), (hx1 - stroke, CY - stroke * 0.5), (hx1 - stroke, CY + stroke * 0.5), (hx0 + stroke, CY + stroke * 0.5)], Z)
    painted_text(marks, "rig_mark_white", "ECREHOU A", V(CX, CY - 7.6, 0.0), 1.5, 8.6, Z)
    painted_text(marks, "rig_mark_white", "12.8", V(CX - 6.6, CY, 0.0), 1.1, 3.0, Z, -math.pi * 0.5)
    for x0, x1, y0, y1 in ((CX - H, CX + H, CY - TAN, CY + TAN), (CX - TAN, CX + TAN, CY - H, CY + H)):
        col(b, "metal", "helideck", x0, x1, y0, y1, Z - DEPTH, Z)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            corner_boxes(b, sx, sy)
    for k in range(10):
        ok.floor_decal(parts["decals"], rng.choice(["guano_a", "guano_b", "oil_b", "guano_a"]), rng.uniform(CX - 7.0, CX + 7.0), rng.uniform(CY - 7.0, CY + 7.0), Z + 0.007, rng.uniform(0.8, 1.8), rng.uniform(0.8, 1.8), rng.uniform(0.0, 6.0))
    for k in range(2):
        ok.floor_decal(parts["decals"], "oil_a", CX + rng.uniform(-2.0, 2.0), CY + rng.uniform(-2.0, 2.0), Z + 0.008, 2.4, 2.4, rng.uniform(0.0, 6.0))


def corner_boxes(b, sx, sy, depth=DEPTH, z_top=Z, tag="helideck", surface="metal", reach=H, cut=TAN, steps=7):
    span = reach - cut
    for k in range(steps):
        a0 = cut + span * k / steps
        a1 = cut + span * (k + 1) / steps
        limit = reach + cut - a1
        x0 = CX + sx * a0
        x1 = CX + sx * a1
        y0 = CY + sy * cut
        y1 = CY + sy * limit
        col(b, surface, tag, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z_top - depth, z_top)


def net(b, parts, rng):
    pts = outline()
    outer = outline(-NET)
    netpart = parts["net"]
    frame = parts["structure"]
    for k in range(8):
        a = pts[k]
        c = pts[(k + 1) % 8]
        d = outer[(k + 1) % 8]
        e = outer[k]
        segments = [(0.0, 1.0)]
        if k == 6:
            length = math.hypot(c[0] - a[0], c[1] - a[1])
            g0 = (STAIR_X[0] - 0.2 - a[0]) / (c[0] - a[0])
            g1 = (STAIR_X[1] + 0.2 - a[0]) / (c[0] - a[0])
            lo, hi = min(g0, g1), max(g0, g1)
            segments = [(0.0, lo), (hi, 1.0)]
        for t0, t1 in segments:
            p0 = (a[0] + (c[0] - a[0]) * t0, a[1] + (c[1] - a[1]) * t0)
            p1 = (a[0] + (c[0] - a[0]) * t1, a[1] + (c[1] - a[1]) * t1)
            q1 = (e[0] + (d[0] - e[0]) * t1, e[1] + (d[1] - e[1]) * t1)
            q0 = (e[0] + (d[0] - e[0]) * t0, e[1] + (d[1] - e[1]) * t0)
            quad = [V(p0[0], p0[1], Z - 0.06), V(p1[0], p1[1], Z - 0.06), V(q1[0], q1[1], Z + 0.08), V(q0[0], q0[1], Z + 0.08)]
            emit(netpart, Geo(quad, [kit.orient((0, 1, 2, 3), quad, up)]), "rig_net", None, "world")
            tube(frame, "rig_paint_grey", V(q0[0], q0[1], Z + 0.08), V(q1[0], q1[1], Z + 0.08), 0.03, 6, True, ok.fine)
            length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            count = max(1, int(length / 2.4))
            for j in range(count + 1):
                t = j / count
                inner = V(p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, Z - 0.1)
                outer_point = V(q0[0] + (q1[0] - q0[0]) * t, q0[1] + (q1[1] - q0[1]) * t, Z + 0.06)
                tube(frame, "rig_paint_grey", inner - V(0.0, 0.0, 0.35), outer_point, 0.025, 6, True, ok.fine)
    ot = TAN + NET * math.tan(math.radians(22.5))
    for x0, x1 in ((CX - ot, STAIR_X[0] - 0.1), (STAIR_X[1] + 0.1, CX + ot)):
        col(b, "grate", "net", x0, x1, CY - H - NET, CY - H, Z - 0.1, Z)
        col(b, "metal", "net_edge", x0, x1, CY - H - NET - 0.1, CY - H - NET, Z - 0.1, Z + 1.1)
    col(b, "grate", "net", CX - ot, CX + ot, CY + H, CY + H + NET, Z - 0.1, Z)
    col(b, "metal", "net_edge", CX - ot, CX + ot, CY + H + NET, CY + H + NET + 0.1, Z - 0.1, Z + 1.1)
    col(b, "grate", "net", CX - H - NET, CX - H, CY - ot, CY + ot, Z - 0.1, Z)
    col(b, "metal", "net_edge", CX - H - NET - 0.1, CX - H - NET, CY - ot, CY + ot, Z - 0.1, Z + 1.1)
    col(b, "grate", "net", CX + H, CX + H + NET, CY - ot, CY + ot, Z - 0.1, Z)
    col(b, "metal", "net_edge", CX + H + NET, CX + H + NET + 0.1, CY - ot, CY + ot, Z - 0.1, Z + 1.1)
    diagonal_ring(b)


def diagonal_ring(b, steps=12):
    inner = H + TAN
    outer_h = H + NET
    outer_t = TAN + NET * math.tan(math.radians(22.5))
    outer = outer_h + outer_t
    span = outer_h - outer_t
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            for k in range(steps):
                a0 = TAN + (outer_h - TAN) * k / steps
                a1 = TAN + (outer_h - TAN) * (k + 1) / steps
                y_lo = max(TAN, inner - a1 - 0.05)
                y_hi = min(outer_h, outer - a0)
                if y_hi <= y_lo:
                    continue
                col(b, "grate", "net", min(CX + sx * a0, CX + sx * a1), max(CX + sx * a0, CX + sx * a1), min(CY + sy * y_lo, CY + sy * y_hi), max(CY + sy * y_lo, CY + sy * y_hi), Z - 0.1, Z)
            for k in range(steps):
                t = (k + 0.5) / steps
                ex = outer_t + span * t
                ey = outer - ex + 0.08
                half = span / steps * 0.5 + 0.06
                px = CX + sx * (ex + 0.06)
                py = CY + sy * ey
                col(b, "metal", "net_edge", px - half, px + half, py - half, py + half, Z - 0.1, Z + 1.1)


def structure(b, parts, rng):
    part = parts["structure"]
    pts = outline()
    for k in range(8):
        a = pts[k]
        c = pts[(k + 1) % 8]
        ok.channel(part, "rig_paint_white", V(a[0], a[1], Z - 0.25), V(c[0], c[1], Z - 0.25), 0.4, 0.1, up)
    for x in (12.6, 18.5, 24.4, 29.4):
        y0, y1 = y_extent(x)
        ok.ibeam(part, "rig_paint_white", V(x, y0 + 0.2, Z - DEPTH * 0.5 - 0.06), V(x, y1 - 0.2, Z - DEPTH * 0.5 - 0.06), DEPTH - 0.06, 0.25)
    for y in (-4.0, 0.0, 4.0, 8.0, 12.0):
        x0, x1 = x_extent(y)
        ok.ibeam(part, "rig_paint_white", V(x0 + 0.2, y, Z - 0.26), V(x1 - 0.2, y, Z - 0.26), 0.38, 0.16)
    base = ROOF
    for x in (12.6, 18.5, 24.4):
        for y in (-4.0, 4.0, 11.4):
            ok.ibeam(part, "rig_paint_white", V(x, y, base), V(x, y, Z - DEPTH), 0.3, 0.3, V(1.0, 0.0, 0.0))
            box(part, "rig_paint_white", x - 0.3, x + 0.3, y - 0.3, y + 0.3, base, base + 0.03)
            col(b, "metal", "heli_column", x - 0.16, x + 0.16, y - 0.16, y + 0.16, base, Z - DEPTH)
    for y in (-2.0, 4.0, 10.0):
        tube(part, "rig_paint_white", V(ok.quarters[1] + 0.05, y, ROOF - 3.4), V(29.4, y, Z - DEPTH), 0.16, 10, True, 1.4)
        box(part, "rig_paint_white", ok.quarters[1], ok.quarters[1] + 0.12, y - 0.3, y + 0.3, ROOF - 3.7, ROOF - 3.1)
    for x, y in ((12.6, -4.0), (24.4, 11.4)):
        tube(part, "rig_paint_white", V(x, y, base + 0.1), V(x + (3.0 if x < CX else -3.0), y + (3.0 if y < CY else -3.0), Z - DEPTH), 0.08, 8, True, 1.4)


def stair(b, parts, rng):
    ok.stair_flight(b, parts, STAIR_X[0], STAIR_X[1], STAIR_FOOT, CY - H, ROOF, Z, "py", rng, "rig_paint_yellow", "rig_paint_yellow", (True, True), (True, True), "heli_stair")
    part = parts["structure"]
    for x in STAIR_X:
        box(part, "rig_paint_grey", x - 0.05, x + 0.05, STAIR_FOOT + 0.9, STAIR_FOOT + 1.0, ROOF, ROOF + 0.6)
    ok.sign(parts["fittings"], "helideck", V(STAIR_X[0] - 0.1, STAIR_FOOT + 0.3, ROOF + 1.3), V(-1.0, 0.0, 0.0), 0.7, 0.18)


def lights(b, parts, rng):
    part = parts["fittings"]
    lamps = parts["lamps"]
    pts = outline(-0.08)
    for k in range(8):
        a = pts[k]
        c = pts[(k + 1) % 8]
        length = math.hypot(c[0] - a[0], c[1] - a[1])
        count = max(1, int(length / 2.6))
        for j in range(count):
            t = (j + 0.5) / count
            x = a[0] + (c[0] - a[0]) * t
            y = a[1] + (c[1] - a[1]) * t
            if k == 6 and STAIR_X[0] - 0.4 < x < STAIR_X[1] + 0.4:
                continue
            box(part, "rig_paint_grey", x - 0.09, x + 0.09, y - 0.09, y + 0.09, Z - 0.05, Z + 0.06)
            lit = rng.random() < 0.55
            ok.lathe(lamps, "rig_lamp_green" if lit else "glass_dirty", V(x, y, Z + 0.06), up, [(0.0, 0.0), (0.07, 0.0), (0.06, 0.06), (0.0, 0.08)], 8, True)
    for (x, y), aim in (((CX + H + 0.6, CY - TAN - 0.6), V(-1.0, 0.6, -0.25)), ((CX - H - 0.6, CY + TAN + 0.6), V(1.0, -0.6, -0.25))):
        base = V(x, y, Z - 0.5)
        tube(part, "rig_paint_grey", base, base + V(0.0, 0.0, 0.85), 0.04, 6)
        ok.floodlight(b, part, lamps, base + V(0.0, 0.0, 0.85) + aim.normalized() * 0.2, aim, "cold", True, False, rng)
    pole = V(12.3, 11.7, ROOF)
    tube(part, "rig_paint_white", pole, pole + V(0.0, 0.0, 5.6), 0.05, 8, True, 1.6)
    ok.ring(part, "rig_paint_grey", pole + V(0.0, 0.0, 5.4), up, 0.05, 0.02, 0.08, 8)
    sock_axis = V(0.7, -0.35, -0.62).normalized()
    hoop = pole + V(0.0, 0.0, 5.45) + V(0.25, 0.0, 0.0)
    tube(part, "rig_paint_grey", pole + V(0.0, 0.0, 5.45), hoop, 0.015, 4)
    profile = [(0.32, 0.0), (0.3, 0.5), (0.26, 1.0), (0.2, 1.5), (0.13, 2.0), (0.06, 2.4)]
    for k in range(len(profile) - 1):
        r0, z0 = profile[k]
        r1, z1 = profile[k + 1]
        name = "rig_lifeboat" if k % 2 == 0 else "rig_mark_white"
        geo = kit.geo_lathe([(r0, z0), (r1, z1)], 10)
        geo_inner = kit.geo_lathe([(r1 - 0.01, z1), (r0 - 0.01, z0)], 10)
        matrix = rk.axis_matrix(hoop, sock_axis)
        emit(parts["sock"], geo, name, matrix, "given", True)
        emit(parts["sock"], geo_inner, name, matrix, "given", True)
    col(b, "metal", "sock_pole", pole.x - 0.08, pole.x + 0.08, pole.y - 0.08, pole.y + 0.08, ROOF, ROOF + 5.6)


def dressing(b, parts, rng):
    part = parts["clutter"]
    for k in range(4):
        x = CX + rng.uniform(-7.0, 7.0)
        y = CY + rng.uniform(-6.0, 6.0)
        ok.path_tube(part, "rig_rust", [V(x, y, Z + 0.02), V(x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.6, 0.6), Z + 0.03), V(x + rng.uniform(-1.2, 1.2), y + rng.uniform(-1.2, 1.2), Z + 0.02)], 0.02, 5, True, 2.0)
    heap = V(CX + 6.4, CY + 3.2, Z)
    for k in range(5):
        ok.lump(part, "rope_net", heap + V(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0.08), (rng.uniform(0.3, 0.6), rng.uniform(0.3, 0.6), 0.12), rng, 0.3, 1)
    monitor = V(16.2, -8.6, ROOF)
    tube(part, "rig_paint_orange", monitor, monitor + V(0.0, 0.0, 1.5), 0.08, 8)
    ok.pipe(part, "rig_paint_orange", [monitor + V(0.0, 0.0, 1.5), monitor + V(0.0, 0.0, 1.7), monitor + V(0.35, 0.35, 1.85), monitor + V(0.7, 0.7, 1.9)], 0.06, 8, 0.15)
    ok.handwheel(part, "rig_paint_yellow", monitor + V(0.0, -0.15, 1.2), V(0.0, -1.0, 0.0), 0.16)
    b.loot("medical", V(CX + 5.8, CY - 4.6, Z))
    b.loot("box", V(CX - 7.0, CY + 1.2, Z))


def helideck():
    b = kit.Build("rig_helideck", 7501)
    rng = b.rng
    parts = ok.setup(b, (("deck", 40.0), ("marks", 30.0), ("structure", 50.0), ("fittings", 45.0), ("clutter", 45.0), ("sock", 70.0), ("lamps", 30.0), ("grating", 30.0), ("net", 30.0), ("decals", 30.0)))
    deck(b, parts, rng)
    net(b, parts, rng)
    structure(b, parts, rng)
    stair(b, parts, rng)
    lights(b, parts, rng)
    dressing(b, parts, rng)
    return b


def helideck_far():
    b = kit.Build("rig_helideck_far", 7502)
    part = b.part("shell", 40.0)
    marks = b.part("marks", 30.0)
    grate = b.part("grating", 30.0)
    netpart = b.part("net", 30.0)
    pts = outline()
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), pts, [], Z - 0.06, Z, False)
    emit(part, geo, "rig_deck_green", None, "world")
    for k in range(8):
        a = pts[k]
        c = pts[(k + 1) % 8]
        ok.far_bar(part, "rig_paint_white", V(a[0], a[1], Z - 0.26), V(c[0], c[1], Z - 0.26), 0.1, 0.4)
    for x in (12.6, 18.5, 24.4, 29.4):
        y0, y1 = y_extent(x)
        ok.far_bar(part, "rig_paint_white", V(x, y0 + 0.2, Z - DEPTH * 0.5 - 0.06), V(x, y1 - 0.2, Z - DEPTH * 0.5 - 0.06), 0.25, DEPTH - 0.06)
    for y in (-4.0, 4.0, 12.0):
        x0, x1 = x_extent(y)
        ok.far_bar(part, "rig_paint_white", V(x0 + 0.2, y, Z - 0.26), V(x1 - 0.2, y, Z - 0.26), 0.16, 0.38)
    outer = outline(0.08)
    inner = outline(0.42)
    for k in range(8):
        flat_polygon(marks, "rig_mark_white", [outer[k], outer[(k + 1) % 8], inner[(k + 1) % 8], inner[k]], Z)
    ring_polygons(marks, "rig_paint_yellow", CX, CY, 4.6, 5.6, Z, 24)
    hx0, hx1 = CX - 1.5, CX + 1.5
    hy0, hy1 = CY - 2.0, CY + 2.0
    stroke = 0.75
    flat_polygon(marks, "rig_mark_white", [(hx0, hy0), (hx0 + stroke, hy0), (hx0 + stroke, hy1), (hx0, hy1)], Z)
    flat_polygon(marks, "rig_mark_white", [(hx1 - stroke, hy0), (hx1, hy0), (hx1, hy1), (hx1 - stroke, hy1)], Z)
    flat_polygon(marks, "rig_mark_white", [(hx0 + stroke, CY - stroke * 0.5), (hx1 - stroke, CY - stroke * 0.5), (hx1 - stroke, CY + stroke * 0.5), (hx0 + stroke, CY + stroke * 0.5)], Z)
    painted_text(marks, "rig_mark_white", "ECREHOU A", V(CX, CY - 7.6, 0.0), 1.5, 8.6, Z, 0.0, 1)
    rim = outline(-NET)
    for k in range(8):
        a = pts[k]
        c = pts[(k + 1) % 8]
        d = rim[(k + 1) % 8]
        e = rim[k]
        segments = [(0.0, 1.0)]
        if k == 6:
            g0 = (STAIR_X[0] - 0.2 - a[0]) / (c[0] - a[0])
            g1 = (STAIR_X[1] + 0.2 - a[0]) / (c[0] - a[0])
            segments = [(0.0, min(g0, g1)), (max(g0, g1), 1.0)]
        for t0, t1 in segments:
            p0 = (a[0] + (c[0] - a[0]) * t0, a[1] + (c[1] - a[1]) * t0)
            p1 = (a[0] + (c[0] - a[0]) * t1, a[1] + (c[1] - a[1]) * t1)
            q1 = (e[0] + (d[0] - e[0]) * t1, e[1] + (d[1] - e[1]) * t1)
            q0 = (e[0] + (d[0] - e[0]) * t0, e[1] + (d[1] - e[1]) * t0)
            quad = [V(p0[0], p0[1], Z - 0.06), V(p1[0], p1[1], Z - 0.06), V(q1[0], q1[1], Z + 0.08), V(q0[0], q0[1], Z + 0.08)]
            emit(netpart, Geo(quad, [kit.orient((0, 1, 2, 3), quad, up)]), "rig_net", None, "world")
            ok.far_tube(part, "rig_paint_grey", V(q0[0], q0[1], Z + 0.08), V(q1[0], q1[1], Z + 0.08), 0.04, 3, ok.fine)
    for x in (12.6, 18.5, 24.4):
        for y in (-4.0, 4.0, 11.4):
            ok.far_post(part, "rig_paint_white", x, y, ROOF, Z - DEPTH, 0.15)
    for y in (-2.0, 4.0, 10.0):
        ok.far_tube(part, "rig_paint_white", V(ok.quarters[1] + 0.05, y, ROOF - 3.4), V(29.4, y, Z - DEPTH), 0.16, 4, 1.4)
    for x, y in ((12.6, -4.0), (24.4, 11.4)):
        ok.far_tube(part, "rig_paint_white", V(x, y, ROOF + 0.1), V(x + (3.0 if x < CX else -3.0), y + (3.0 if y < CY else -3.0), Z - DEPTH), 0.08, 3, 1.4)
    ok.far_stair(part, grate, STAIR_X[0], STAIR_X[1], STAIR_FOOT, CY - H, ROOF, Z, "py")
    pole = V(12.3, 11.7, ROOF)
    ok.far_post(part, "rig_paint_white", pole.x, pole.y, ROOF, ROOF + 5.6, 0.05, 1.6)
    sock_axis = V(0.7, -0.35, -0.62).normalized()
    hoop = pole + V(0.25, 0.0, 5.45)
    matrix = rk.axis_matrix(hoop, sock_axis)
    for k, (r0, z0, r1, z1) in enumerate(((0.32, 0.0, 0.26, 1.0), (0.26, 1.0, 0.13, 2.0), (0.13, 2.0, 0.06, 2.4))):
        emit(part, kit.geo_lathe([(r0, z0), (r1, z1)], 6), "rig_lifeboat" if k % 2 == 0 else "rig_mark_white", matrix, "given", True)
    return b
