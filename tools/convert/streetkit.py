import bpy
import bmesh
import math
import os
import random
import sys
import time
import numpy
from mathutils import Matrix, Vector, geometry

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gunkit as g
import vehiclekit as vk
from vehiclekit import v, X, Y, Z, tau

arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = arguments[0] if arguments else "look"
wanted = [name for name in (arguments[1].split(",") if len(arguments) > 1 else []) if name]
samples = int(arguments[2]) if len(arguments) > 2 else 48
preview_root = os.path.join(vk.previews_root, "street")
manifest_path = os.path.join(vk.source_root, "street", "street.json")


class model:
    def __init__(self, name, seed=1):
        self.name = name
        self.rng = random.Random(seed)
        self.parts = {}
        self.far_parts = {}
        self.sets = []
        self.markers = []
        self.closeups = []
        self.info = {}
        self.counters = {}
        self.band = None
        self.boost = 2.6
        self.library_parts = []

    def part(self, key, sharp=38.0, origin=None):
        if key not in self.parts:
            self.parts[key] = vk.part(key, sharp, origin)
        return self.parts[key]

    def far(self, key, sharp=40.0, origin=None):
        if key not in self.far_parts:
            self.far_parts[key] = vk.part(key, sharp, origin)
        return self.far_parts[key]

    def col(self, surface, low, high):
        self.counters[surface] = self.counters.get(surface, 0) + 1
        self.markers.append(("col_" + surface + "_" + str(self.counters[surface]), Vector(low), Vector(high)))

    def loot(self, kind, position):
        self.counters["loot_" + kind] = self.counters.get("loot_" + kind, 0) + 1
        position = Vector(position)
        self.markers.append(("loot_" + kind + "_" + str(self.counters["loot_" + kind]), position + Vector((-0.05, -0.05, 0.0)), position + Vector((0.05, 0.05, 0.1))))

    def close(self, position, target, lens=50.0):
        self.closeups.append((Vector(position), Vector(target), lens))


def looks():
    vk.standard_looks()
    vk.register("iron_black", "paint", color=(0.012, 0.012, 0.013), under=(0.07, 0.068, 0.062), primer=(0.11, 0.05, 0.03), chips=0.5, fade=0.35, chalk=0.12, bleed=0.45, streaks=0.5, gloss=0.6, dirt=0.5, bare=0.5)
    vk.register("iron_green", "paint", color=(0.018, 0.05, 0.03), under=(0.02, 0.02, 0.02), primer=(0.12, 0.05, 0.03), chips=0.5, fade=0.45, chalk=0.25, bleed=0.4, streaks=0.5, gloss=0.6, dirt=0.5)
    vk.register("paint_white", "paint", color=(0.46, 0.45, 0.41), under=(0.03, 0.03, 0.03), primer=(0.12, 0.05, 0.03), chips=0.5, fade=0.2, chalk=0.05, bleed=0.4, streaks=0.55, gloss=0.62, dirt=0.6)
    vk.register("post_red", "paint", color=(0.25, 0.011, 0.008), under=(0.1, 0.01, 0.008), primer=(0.05, 0.045, 0.04), chips=0.45, fade=0.45, chalk=0.12, bleed=0.45, streaks=0.55, gloss=0.55, dirt=0.5)
    vk.register("litter_paper", "organic", kind="paper", tint=(0.38, 0.36, 0.3), dirt=0.6, creases=0.8)
    vk.register("granite", "stone", kind="granite", lichen=0.5, moss=0.25, dirt=0.4, streaks=0.35)
    vk.register("granite_grey", "stone", kind="granite", tint=(0.27, 0.26, 0.25), minerals=[(0.0, (0.26, 0.25, 0.24)), (0.35, (0.36, 0.35, 0.33)), (0.6, (0.48, 0.47, 0.45)), (0.82, (0.14, 0.135, 0.13)), (0.94, (0.025, 0.024, 0.024))], lichen=0.6, moss=0.3, dirt=0.4, streaks=0.4)
    vk.register("rubble_wall", "stone", kind="wall", lichen=0.5, moss=0.45, dirt=0.4, streaks=0.3, stones=5.0)
    vk.register("concrete", "stone", kind="concrete", lichen=0.3, moss=0.3, dirt=0.5, streaks=0.4)
    vk.register("teak", "wood", along="X", light=(0.2, 0.15, 0.1), dark=(0.08, 0.06, 0.045), silver=0.75, cracks=0.6, moss=0.15, lichen=0.3, dirt=0.4)
    vk.register("pine_white", "wood", along="Z", light=(0.26, 0.21, 0.15), dark=(0.11, 0.09, 0.07), silver=0.8, cracks=0.5, paint=(0.45, 0.44, 0.4), peel=0.85, moss=0.3, dirt=0.65, lichen=0.2)
    vk.register("canvas_red", "fabric", kind="stripes", a=(0.22, 0.026, 0.02), b=(0.34, 0.32, 0.27), axis="X", width=0.13, fade=0.5, stains=0.9, mildew=0.75, dirt=0.8, moss=0.15)
    vk.register("canvas_green", "fabric", kind="stripes", a=(0.025, 0.08, 0.045), b=(0.34, 0.32, 0.27), axis="X", width=0.13, fade=0.55, stains=0.9, mildew=0.8, dirt=0.8, moss=0.2)
    vk.register("cone_orange", "plastic", color=(0.62, 0.12, 0.02), fade=0.5, gloss=0.5, dirt=0.6)
    vk.register("vinyl_brown", "fabric", kind="vinyl", tint=(0.09, 0.05, 0.03), dirt=0.5, moss=0.2)
    vk.register("bronze", "bronze", verdigris=0.7)


def swatches():
    m = model("prop_swatches", 3)
    names = ["iron_black", "iron_green", "paint_white", "post_red", "steel", "iron", "rust", "zinc", "chrome", "granite", "granite_grey", "rubble_wall", "concrete", "teak", "pine_white", "canvas_red", "canvas_green", "hessian", "cone_orange", "glass", "glass_cracked", "rubber", "vinyl_brown", "bronze", "moss", "leaves", "dirt", "water", "weld", "chain"]
    columns = 6
    for index, look in enumerate(names):
        x = (index % columns - (columns - 1) * 0.5) * 0.85
        y = (index // columns) * 0.85
        piece = m.part("swatch_" + look)
        piece.add(vk.cube(0.42, 0.42, 0.42), look, Matrix.Translation((x - 0.12, y, 0.21)), 0.012, 2)
        piece.add(vk.cylinder(0.12, 0.6, 24), look, vk.frame(v(x + 0.24, y - 0.12, 0.0), Z))
    for row in range(5):
        for half in (-1.0, 1.0):
            m.close(v(half * 1.27, row * 0.85 - 1.5, 1.75), v(half * 1.27, row * 0.85, 0.2), 36.0)
    return m


def plane_points(points, x):
    return [v(x, a, b) for a, b in points]


def spiral(center, r0, r1, a0, turns, steps=14):
    return [(center[0] + (r0 + (r1 - r0) * s / steps) * math.cos(a0 + tau * turns * s / steps), center[1] + (r0 + (r1 - r0) * s / steps) * math.sin(a0 + tau * turns * s / steps)) for s in range(steps + 1)]


def frame_bar(target, look, x, points, width, depth, steps=8):
    path = g.spline([v(x, a, b) for a, b in points], steps) if len(points) > 2 else [v(x, a, b) for a, b in points]
    target.add(g.sweep(path, g.rectangle(width, depth), planar=X), look)


def leaf_litter(target, rng, center, radius, count, z=0.003, look="leaves"):
    for index in range(count):
        angle = rng.uniform(0.0, tau)
        spread = radius * math.sqrt(rng.random())
        size = rng.uniform(0.035, 0.07)
        outline = [(size * math.cos(a) * (1.0 if a < math.pi else 0.55), size * 0.45 * math.sin(a)) for a in [tau * k / 7 for k in range(7)]]
        target.add(vk.slab(outline, 0.002), look, vk.at(Vector(center) + v(math.cos(angle) * spread, math.sin(angle) * spread, z + index * 0.0004), rng.uniform(0.0, tau), rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15)))


def shards(target, rng, center, radius, count, z=0.004, look="glass"):
    for index in range(count):
        angle = rng.uniform(0.0, tau)
        spread = radius * math.sqrt(rng.random())
        size = rng.uniform(0.02, 0.07)
        outline = [(rng.uniform(-size, size), rng.uniform(-size, 0.0)), (rng.uniform(0.0, size), rng.uniform(-size * 0.5, size)), (rng.uniform(-size, 0.0), rng.uniform(0.0, size))]
        if (outline[1][0] - outline[0][0]) * (outline[2][1] - outline[0][1]) - (outline[1][1] - outline[0][1]) * (outline[2][0] - outline[0][0]) < 0.0:
            outline.reverse()
        target.add(vk.slab(outline, 0.005), look, vk.at(Vector(center) + v(math.cos(angle) * spread, math.sin(angle) * spread, z), rng.uniform(0.0, tau), rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1)))


def crumple(rng, size, flat=1.0):
    bm = vk.lump(size, size * rng.uniform(0.8, 1.1), size * 0.85 * flat, rng, 0.0, 2)
    for vert in bm.verts:
        n = vert.co.normalized()
        vert.co *= 1.0 + 0.32 * math.sin(n.x * 9.0 + n.y * 5.0) * math.cos(n.z * 7.0 - n.x * 3.0) + rng.uniform(-0.12, 0.12)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def jagged_pane(rng, width, height, keep=0.22):
    points = []
    steps = 9
    for side in range(4):
        for s in range(steps):
            t = s / steps
            if side == 0:
                base = (-width * 0.5 + width * t, -height * 0.5)
                inward = (0.0, 1.0)
            elif side == 1:
                base = (width * 0.5, -height * 0.5 + height * t)
                inward = (-1.0, 0.0)
            elif side == 2:
                base = (width * 0.5 - width * t, height * 0.5)
                inward = (0.0, -1.0)
            else:
                base = (-width * 0.5, height * 0.5 - height * t)
                inward = (1.0, 0.0)
            depth = rng.uniform(0.01, min(width, height) * keep) * (1.0 if s % 2 else 0.25)
            points.append((base[0] + inward[0] * depth, base[1] + inward[1] * depth))
    outer = [(-width * 0.5, -height * 0.5), (width * 0.5, -height * 0.5), (width * 0.5, height * 0.5), (-width * 0.5, height * 0.5)]
    return outer, [list(reversed(points))]


def pane(target, rng, matrix, width, height, state, thickness=0.006):
    if state == "missing":
        return
    if state == "broken":
        outer, holes = jagged_pane(rng, width, height)
        target.add(vk.slab(outer, thickness, holes), "glass_cracked", matrix @ Matrix.Rotation(math.pi * 0.5, 4, 'X'))
        return
    target.add(vk.cube(width, thickness, height), "glass_cracked" if state == "cracked" else "glass", matrix)


def bench():
    m = model("prop_bench", 21)
    body = m.part("prop_bench", 40.0)
    rng = m.rng
    for side in (-1.0, 1.0):
        x = side * 0.84
        frame_bar(body, "iron_black", x, [(-0.245, 0.02), (-0.258, 0.12), (-0.25, 0.26), (-0.236, 0.36), (-0.25, 0.44)], 0.04, 0.034)
        frame_bar(body, "iron_black", x, [(0.27, 0.02), (0.245, 0.13), (0.195, 0.28), (0.165, 0.4), (0.18, 0.52), (0.215, 0.66), (0.255, 0.8), (0.29, 0.885)], 0.042, 0.034)
        frame_bar(body, "iron_black", x, [(-0.275, 0.435), (-0.05, 0.418), (0.18, 0.392)], 0.04, 0.03)
        frame_bar(body, "iron_black", x, [(0.235, 0.69), (0.05, 0.672), (-0.17, 0.664), (-0.27, 0.652)], 0.034, 0.04)
        frame_bar(body, "iron_black", x, [(-0.25, 0.44), (-0.243, 0.55), (-0.25, 0.66)], 0.028, 0.03)
        frame_bar(body, "iron_black", x, spiral((-0.27, 0.605), 0.05, 0.012, math.pi * 0.5, 0.85, 12), 0.026, 0.038)
        frame_bar(body, "iron_black", x, spiral((-0.17, 0.2), 0.075, 0.02, math.pi, 1.0, 14), 0.022, 0.026)
        frame_bar(body, "iron_black", x, spiral((0.12, 0.2), 0.07, 0.02, 0.0, -1.0, 14), 0.022, 0.026)
        frame_bar(body, "iron_black", x, [(-0.2, 0.27), (-0.03, 0.31), (0.13, 0.27)], 0.022, 0.026)
        frame_bar(body, "iron_black", x, spiral((0.27, 0.86), 0.04, 0.01, -math.pi * 0.5, 0.8, 10), 0.028, 0.034)
        for y in (-0.245, 0.27):
            body.add(vk.cube(0.06, 0.09, 0.025), "iron_black", Matrix.Translation((x, y, 0.0125)), 0.006)
    seat_ys = [-0.24, -0.155, -0.07, 0.015, 0.1]
    for index, y in enumerate(seat_ys):
        z = 0.435 - (y + 0.275) / 0.455 * 0.043 + 0.034
        pitch = math.atan2(-0.043, 0.455)
        tone = (rng.uniform(0.85, 1.12), rng.uniform(0.85, 1.08), rng.uniform(0.82, 1.05))
        if index == 2:
            body.add(vk.cube(1.0, 0.066, 0.03), "teak", about(v(-0.84, y, z), Y, 0.06) @ Matrix.Translation((-0.43, y, z)) @ Matrix.Rotation(pitch, 4, 'X'), 0.004, tint=tone)
            body.add(vk.cube(0.76, 0.066, 0.03), "teak", about(v(0.84, y, z), Y, -0.075) @ Matrix.Translation((0.55, y, z)) @ Matrix.Rotation(pitch, 4, 'X'), 0.004, tint=tone)
            for k in range(3):
                body.add(vk.cube(0.09 + k * 0.03, 0.012, 0.008), "teak", about(v(-0.84, y, z), Y, 0.06) @ Matrix.Translation((0.1 + k * 0.012, y - 0.022 + k * 0.022, z + 0.006 - k * 0.006)), 0.0, tint=tone)
                body.add(vk.cube(0.08 + k * 0.02, 0.012, 0.008), "teak", about(v(0.84, y, z), Y, -0.075) @ Matrix.Translation((0.16 - k * 0.012, y - 0.02 + k * 0.02, z + 0.004 - k * 0.005)), 0.0, tint=tone)
        else:
            body.add(vk.cube(1.86 + rng.uniform(-0.01, 0.01), 0.066, 0.03), "teak", Matrix.Translation((rng.uniform(-0.01, 0.01), y, z)) @ Matrix.Rotation(pitch, 4, 'X') @ Matrix.Rotation(rng.uniform(-0.004, 0.004), 4, 'Z'), 0.004, tint=tone)
        for x in (-0.84, 0.84):
            for dy in (-0.017, 0.017):
                vk.rivet(body, v(x, y + dy, z + 0.015), Z, 0.008, "iron")
    back_path = [v(0.0, 0.18, 0.52), v(0.0, 0.29, 0.885)]
    direction = (back_path[1] - back_path[0]).normalized()
    normal = v(0.0, -direction.z, direction.y)
    tilt = math.atan2(direction.y, direction.z)
    for index, t in enumerate((0.16, 0.42, 0.66, 0.9)):
        if index == 1:
            for x in (-0.84, 0.84):
                center = back_path[0].lerp(back_path[1], t) + normal * 0.036
                body.add(vk.cylinder(0.006, 0.02, 6), "iron", vk.frame(v(x, center.y, center.z), normal))
            continue
        center = back_path[0].lerp(back_path[1], t) + normal * 0.034
        tone = (rng.uniform(0.85, 1.12), rng.uniform(0.85, 1.08), rng.uniform(0.82, 1.05))
        body.add(vk.cube(1.86, 0.03, 0.066), "teak", Matrix.Translation((rng.uniform(-0.008, 0.008), center.y, center.z)) @ Matrix.Rotation(-tilt, 4, 'X'), 0.004, tint=tone)
        for x in (-0.84, 0.84):
            for dz in (-0.017, 0.017):
                vk.rivet(body, v(x, center.y, center.z) + normal * 0.016 + v(0.0, direction.y, direction.z) * dz, normal, 0.008, "iron")
    vk.text_mask("bench_plaque", 3.6, [("IN LOVING MEMORY OF", 0.18, 0.78, "timesbd.ttf", 1.8, 3.2), ("ALICE LE CORNU", 0.3, 0.5, "timesbd.ttf", 1.8, 3.2), ("WHO LOVED THIS VIEW", 0.18, 0.2, "timesbd.ttf", 1.8, 3.2)], 1024, [(0.04, 0.035)])
    vk.register("bench_plaque", "bronze", verdigris=0.9, tone=(0.13, 0.085, 0.04), text=("bench_plaque", (0.0, 0.0, 0.0), 3.0))
    top = back_path[0].lerp(back_path[1], 0.9) + normal * 0.0505
    plaque = Matrix.Translation(top) @ Matrix.Rotation(-tilt, 4, 'X')
    body.add(vk.cube(0.216, 0.004, 0.06), "bench_plaque", plaque, 0.0012, label=vk.label(top - normal * 0.002, X, v(0.0, direction.y, direction.z), 0.216, 0.06, 0.8))
    for dx in (-0.098, 0.098):
        vk.rivet(body, top + v(dx, 0.0, 0.0) + normal * 0.002, normal, 0.004, "bench_plaque")
    leaf_litter(body, rng, v(0.3, -0.05, 0.0), 0.5, 18)
    far = m.far("prop_bench_far")
    far.add(vk.cube(1.86, 0.43, 0.03), "steel", Matrix.Translation((0.0, -0.07, 0.448)) @ Matrix.Rotation(math.atan2(-0.043, 0.455), 4, 'X'))
    far.add(vk.cube(1.86, 0.03, 0.37), "steel", Matrix.Translation((0.0, 0.25, 0.71)) @ Matrix.Rotation(-tilt, 4, 'X'))
    for side in (-1.0, 1.0):
        far.add(vk.slab([(-0.26, 0.0), (0.28, 0.0), (0.2, 0.4), (0.3, 0.89), (0.24, 0.7), (-0.27, 0.68), (-0.25, 0.44)], 0.03), "steel", Matrix(((0.0, 0.0, 1.0, side * 0.84), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))))
    m.col("wood", (-0.93, -0.29, 0.38), (0.93, 0.17, 0.47))
    m.col("wood", (-0.93, 0.16, 0.47), (0.93, 0.33, 0.9))
    for side in (-1.0, 1.0):
        m.col("metal", (side * 0.82, -0.29, 0.0), (side * 0.865, 0.31, 0.7))
    m.close(v(-0.55, -1.05, 0.95), v(-0.6, 0.0, 0.45), 40.0)
    m.close(v(0.05, -0.45, 0.95), v(0.0, 0.27, 0.8), 45.0)
    m.info = {"kind": "point", "front": "-Y (seat faces -Y)", "length": 1.86}
    return m


def about(point, axis, angle):
    return vk.about(point, axis, angle)


def side_matrix(normal, offset):
    normal = Vector(normal)
    u = Z.cross(normal).normalized()
    matrix = Matrix((u, -normal, Z)).transposed().to_4x4()
    matrix.translation = normal * offset
    return matrix


def face_matrix(normal, offset):
    normal = Vector(normal)
    u = Z.cross(normal).normalized()
    matrix = Matrix((u, Z, normal)).transposed().to_4x4()
    matrix.translation = normal * offset
    return matrix


def crown_outline(width, height):
    w = width * 0.5
    h = height
    points = [(-w * 0.86, 0.0), (w * 0.86, 0.0), (w * 0.86, h * 0.2), (w, h * 0.26), (w * 0.94, h * 0.34)]
    for step in range(1, 8):
        t = step / 8.0 * math.pi * 0.5
        points.append((w * 0.94 * math.cos(t), h * 0.34 + h * 0.36 * math.sin(t)))
    points += [(w * 0.07, h * 0.7), (w * 0.07, h * 0.78), (w * 0.2, h * 0.78), (w * 0.2, h * 0.86), (w * 0.07, h * 0.86), (w * 0.07, h)]
    mirrored = [(-x, y) for x, y in reversed(points[2:])]
    return points + mirrored


def outline_triangles(points, offset=(0.0, 0.0)):
    triangles = geometry.tessellate_polygon([[Vector((x, y, 0.0)) for x, y in points]])
    return [tuple((points[i][0] + offset[0], points[i][1] + offset[1]) for i in tri) for tri in triangles]


def curved_panel(r0, r1, a0, a1, z0, z1, steps=10):
    bm = bmesh.new()
    rings = []
    for radius in (r0, r1):
        ring = []
        for s in range(steps + 1):
            angle = a0 + (a1 - a0) * s / steps
            ring.append((bm.verts.new((radius * math.cos(angle), radius * math.sin(angle), z0)), bm.verts.new((radius * math.cos(angle), radius * math.sin(angle), z1))))
        rings.append(ring)
    inner, outer = rings
    for s in range(steps):
        bm.faces.new((outer[s][0], outer[s + 1][0], outer[s + 1][1], outer[s][1]))
        bm.faces.new((inner[s][1], inner[s + 1][1], inner[s + 1][0], inner[s][0]))
        bm.faces.new((inner[s][1], outer[s][1], outer[s + 1][1], inner[s + 1][1]))
        bm.faces.new((inner[s + 1][0], outer[s + 1][0], outer[s][0], inner[s][0]))
    for s, flip in ((0, False), (steps, True)):
        quad = (inner[s][0], outer[s][0], outer[s][1], inner[s][1])
        bm.faces.new(tuple(reversed(quad)) if flip else quad)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def phone_box():
    m = model("prop_phone_box", 41)
    body = m.part("prop_phone_box", 40.0)
    rng = m.rng
    half = 0.4575
    post = 0.085
    base_top = 0.18
    eaves = 2.17
    inner = half - post
    body.add(vk.block(v(-0.53, -0.53, -0.06), v(0.53, 0.53, 0.06)), "concrete", None, 0.012)
    body.add(vk.block(v(-0.478, -0.478, 0.06), v(0.478, 0.478, 0.1)), "post_red", None, 0.008)
    body.add(vk.block(v(-half, -half, 0.1), v(half, half, base_top)), "post_red", None, 0.006)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            cx = sx * (half - post * 0.5)
            cy = sy * (half - post * 0.5)
            body.add(vk.block(v(cx - post * 0.5, cy - post * 0.5, base_top), v(cx + post * 0.5, cy + post * 0.5, eaves)), "post_red", None, 0.012, 2)
    vk.text_mask("telephone", 6.0, [("TELEPHONE", 0.62, 0.5, "GILB____.TTF", 3.0, 5.2, 1.0, 1.15)])
    vk.register("phone_sign", "plastic", color=(0.46, 0.45, 0.4), fade=0.3, gloss=0.35, dirt=0.65, text=("telephone", (0.015, 0.015, 0.015), 0.0))
    door = vk.part("door")
    hinge = v(-inner, -half, 0.0)
    for normal in (v(0.0, -1.0, 0.0), v(1.0, 0.0, 0.0), v(0.0, 1.0, 0.0), v(-1.0, 0.0, 0.0)):
        front = normal.y < -0.5
        target = door if front else body
        frame = side_matrix(normal, half)
        target.add(vk.block(v(-inner, 0.02, base_top), v(inner, 0.05, 0.44)), "post_red", frame, 0.005)
        target.add(vk.block(v(-0.3, 0.012, 0.21), v(0.3, 0.02, 0.41)), "post_red", frame, 0.004)
        for a0, a1 in ((-inner, -0.33), (0.33, inner)):
            target.add(vk.block(v(a0, 0.012, 0.44), v(a1, 0.06, 2.0)), "post_red", frame, 0.005)
        for b0, b1 in ((0.44, 0.48), (1.96, 2.0)):
            target.add(vk.block(v(-0.33, 0.012, b0), v(0.33, 0.06, b1)), "post_red", frame, 0.005)
        rows = [0.48 + (1.96 - 0.48) * k / 8 for k in range(9)]
        for b in rows[1:-1]:
            target.add(vk.block(v(-0.33, 0.02, b - 0.011), v(0.33, 0.05, b + 0.011)), "post_red", frame, 0.004)
        for a in (-0.15, 0.15):
            target.add(vk.block(v(a - 0.011, 0.02, 0.48), v(a + 0.011, 0.05, 1.96)), "post_red", frame, 0.004)
        columns = [(-0.33, -0.15), (-0.15, 0.15), (0.15, 0.33)]
        for row in range(8):
            for a0, a1 in columns:
                roll = rng.random()
                state = "missing" if roll < 0.14 else ("broken" if roll < 0.22 else ("cracked" if roll < 0.45 else "glass"))
                pane(target, rng, frame @ Matrix.Translation(((a0 + a1) * 0.5, 0.036, (rows[row] + rows[row + 1]) * 0.5)), a1 - a0 - 0.012, rows[row + 1] - rows[row] - 0.012, state, 0.005)
        if front:
            door.add(vk.block(v(0.3, -0.03, 1.02), v(0.318, 0.012, 1.18)), "zinc", frame, 0.003)
            door.add(vk.block(v(0.29, -0.012, 1.06), v(0.33, 0.0, 1.14)), "zinc", frame, 0.002)
        body.add(vk.block(v(-0.33, -0.032, 2.01), v(0.33, 0.04, 2.15)), "post_red", frame, 0.006)
        sign_center = frame @ v(0.0, -0.033, 2.08)
        body.add(vk.block(v(-0.3, -0.035, 2.03), v(0.3, -0.031, 2.13)), "phone_sign", frame, 0.0, label=vk.label(sign_center, Z.cross(normal), Z, 0.6, 0.1, 0.8))
        arc = []
        radius = (0.47 ** 2 + 0.16 ** 2) / 0.32
        for s in range(13):
            a = 0.47 - 0.94 * s / 12
            arc.append((a, 2.2 + math.sqrt(radius * radius - a * a) - (radius - 0.16)))
        body.add(vk.slab([(-0.47, 2.2), (0.47, 2.2)] + arc[1:-1], 0.05), "post_red", face_matrix(normal, 0.455), 0.006)
        crown = crown_outline(0.16, 0.13)
        body.add(vk.slab(crown, 0.02), "post_red", face_matrix(normal, 0.485) @ Matrix.Translation((0.0, 2.215, 0.0)), 0.003)
    body.add(vk.block(v(-0.49, -0.49, 2.15), v(0.49, 0.49, 2.2)), "post_red", None, 0.01, 2)
    radius = (0.47 ** 2 + 0.16 ** 2) / 0.32

    def vault(x, y):
        return min(math.sqrt(max(radius * radius - x * x, 0.0)), math.sqrt(max(radius * radius - y * y, 0.0))) - (radius - 0.16)

    roof = vk.grid_sheet(0.95, 0.95, 16, 16, vault)
    vk.thicken(roof, 0.03)
    body.add(roof, "post_red", Matrix.Translation((0.0, 0.0, 2.205)))
    body.add(vk.lathe([(0.0, 0.0), (0.05, 0.0), (0.045, 0.03), (0.02, 0.05), (0.0, 0.06)], 12), "post_red", Matrix.Translation((0.0, 0.0, 2.355)))
    door_matrix = vk.about(hinge, Z, -0.46)
    for coord_index in range(len(door.coords)):
        door.coords[coord_index] = tuple(door_matrix @ Vector(door.coords[coord_index]))
    merge(body, door)
    phone = v(0.0, 0.335, 1.3)
    body.add(vk.block(phone + v(-0.1, -0.06, -0.13), phone + v(0.1, 0.06, 0.13)), "iron_black", None, 0.012)
    body.add(vk.block(phone + v(-0.08, -0.05, -0.33), phone + v(0.08, 0.05, -0.15)), "zinc", None, 0.01)
    body.add(vk.block(phone + v(0.04, -0.064, 0.0), phone + v(0.075, -0.06, 0.08)), "zinc", None, 0.002)
    for k in range(3):
        body.add(vk.cylinder(0.011, 0.01, 10), "zinc", vk.frame(phone + v(-0.05 + k * 0.025, -0.06, 0.08), v(0.0, -1.0, 0.0)))
    cord = [phone + v(-0.09, -0.065, -0.05)] + [phone + v(-0.11 + 0.015 * math.cos(k * 1.4), -0.07 + 0.015 * math.sin(k * 1.4), -0.12 - k * 0.035) for k in range(14)]
    body.add(vk.tube(cord, 0.004, 5), "rubber")
    handset = cord[-1] + v(0.0, 0.0, -0.02)
    body.add(vk.rod(handset, handset + v(0.03, -0.02, -0.2), 0.016, 8), "iron_black")
    for end in (handset, handset + v(0.03, -0.02, -0.2)):
        body.add(g.sphere(0.028, 10, 6), "iron_black", Matrix.Translation(end))
    body.add(vk.block(v(-0.36, 0.12, 0.92), v(-0.12, 0.37, 0.945)), "post_red", None, 0.004)
    vk.register("directory", "organic", kind="paper", tint=(0.42, 0.36, 0.12), dirt=0.6)
    body.add(vk.block(v(-0.33, 0.16, 0.945), v(-0.15, 0.36, 1.01)), "directory", None, 0.005)
    leaf_litter(body, rng, v(0.0, 0.0, base_top), 0.3, 18)
    shards(body, rng, v(0.0, -0.75, 0.0), 0.45, 16)
    far = m.far("prop_phone_box_far")
    far.add(vk.block(v(-0.53, -0.53, -0.04), v(0.53, 0.53, 0.06)), "steel")
    far.add(vk.block(v(-half, -half + 0.03, 0.06), v(half, half, 2.2)), "steel")
    far.add(vk.block(v(-0.49, -0.49, 2.15), v(0.49, 0.49, 2.22)), "steel")
    far.add(vk.lathe([(0.0, 0.0), (0.67, 0.0), (0.0, 0.16)], 4, math.pi * 0.25), "steel", Matrix.Translation((0.0, 0.0, 2.22)))
    far.add(vk.block(v(-inner, -0.03, 0.18), v(inner, 0.0, 2.0)), "steel", vk.about(hinge, Z, -0.46) @ Matrix.Translation((0.0, -half, 0.0)))
    m.col("metal", (-0.48, -0.48, 0.0), (0.48, 0.48, 2.4))
    m.close(v(0.75, -1.25, 1.9), v(0.0, -0.3, 1.6), 40.0)
    m.close(v(-0.25, -1.25, 1.35), v(0.05, 0.3, 1.25), 38.0)
    m.close(v(0.6, -0.9, 2.65), v(0.0, -0.4, 2.15), 45.0)
    m.info = {"kind": "point", "front": "-Y (door, hinged on -X side, ajar)", "footprint": [0.915, 0.915]}
    return m


def merge(target, other):
    base = len(target.coords)
    target.coords.extend(other.coords)
    target.colors.extend(other.colors)
    for face, slot, uvs, box, flag in zip(other.faces, other.face_slot, other.face_label, other.face_uv, other.face_boost):
        target.faces.append(tuple(base + index for index in face))
        target.face_slot.append(target.slot(other.slots[slot]))
        target.face_label.append(uvs)
        target.face_uv.append(box)
        target.face_boost.append(flag)


def post_box():
    m = model("prop_post_box", 51)
    body = m.part("prop_post_box", 40.0)
    rng = m.rng
    lean = vk.about(v(0.0, 0.0, 0.0), X, -0.022)
    body.add(vk.lathe([(0.0, -0.06), (0.3, -0.06), (0.3, 0.03), (0.288, 0.05), (0.288, 0.11), (0.268, 0.13), (0.0, 0.13)], 40), "iron_black", lean)
    profile = [(0.0, 0.12), (0.264, 0.12), (0.264, 1.2), (0.27, 1.21), (0.273, 1.225), (0.27, 1.24), (0.263, 1.25), (0.263, 1.33), (0.276, 1.34), (0.3, 1.356), (0.308, 1.37), (0.308, 1.396), (0.298, 1.41), (0.283, 1.42), (0.27, 1.432), (0.255, 1.47), (0.222, 1.52), (0.165, 1.563), (0.09, 1.59), (0.0, 1.6)]
    vk.text_mask("post_office", 5.0, [("POST  OFFICE", 0.62, 0.5, "timesbd.ttf", 2.5, 4.6, 1.0, 1.25)])
    vk.register("post_band", "paint", color=(0.25, 0.011, 0.008), under=(0.1, 0.01, 0.008), primer=(0.05, 0.045, 0.04), chips=0.45, fade=0.45, chalk=0.12, bleed=0.45, streaks=0.55, gloss=0.55, dirt=0.5, text=("post_office", (0.3, 0.014, 0.01), 7.0))
    body.add(vk.lathe(profile, 40), "post_band", lean, label=vk.label(v(0.0, -0.27, 1.225), X, Z, 0.24, 0.048, 0.86))
    body.add(vk.block(v(-0.13, -0.27, 1.272), v(0.13, -0.258, 1.304)), "iron_black", lean, 0.003)
    body.add(vk.block(v(-0.148, -0.296, 1.306), v(0.148, -0.255, 1.322)), "post_red", lean, 0.004)
    door = curved_panel(0.263, 0.271, -math.pi * 0.5 - 0.6, -math.pi * 0.5 + 0.6, 0.46, 1.1, 14)
    shapes = outline_triangles([(x * 1.0, y) for x, y in crown_outline(0.36, 0.3)], (0.5, 0.58))
    vk.text_mask("cypher", 1.0, [("G  R", 0.34, 0.33, "timesbd.ttf", 0.5, 0.86, 1.0, 1.0)], 1024, (), [shapes])
    vk.register("post_door", "paint", color=(0.25, 0.011, 0.008), under=(0.1, 0.01, 0.008), primer=(0.05, 0.045, 0.04), chips=0.45, fade=0.45, chalk=0.12, bleed=0.45, streaks=0.55, gloss=0.55, dirt=0.5, text=("cypher", (0.32, 0.015, 0.011), 8.0))
    body.add(door, "post_door", lean, label=vk.label(v(0.0, -0.271, 0.95), X, Z, 0.2, 0.2, 0.86))
    for z in (0.46, 1.1):
        body.add(curved_panel(0.27, 0.276, -math.pi * 0.5 - 0.62, -math.pi * 0.5 + 0.62, z - 0.012, z + 0.012, 14), "post_red", lean)
    vk.text_mask("collection", 1.4, [("COLLECTIONS", 0.12, 0.84, "arialbd.ttf", 0.7, 1.2), ("MONDAY - FRIDAY", 0.085, 0.68, "arial.ttf", 0.7, 1.2), ("9.00 AM   5.30 PM", 0.12, 0.54, "arialbd.ttf", 0.7, 1.2), ("SATURDAY", 0.085, 0.38, "arial.ttf", 0.7, 1.2), ("11.45 AM", 0.12, 0.24, "arialbd.ttf", 0.7, 1.2)], 1024, [(0.03, 0.02)])
    vk.register("enamel", "paint", color=(0.48, 0.47, 0.43), under=(0.02, 0.02, 0.025), primer=(0.02, 0.02, 0.025), chips=0.4, fade=0.15, chalk=0.0, bleed=0.5, streaks=0.4, gloss=0.25, dirt=0.4, text=("collection", (0.02, 0.02, 0.025), 0.0))
    body.add(curved_panel(0.2705, 0.2745, -math.pi * 0.5 - 0.26, -math.pi * 0.5 + 0.26, 0.6, 0.7, 6), "enamel", lean, label=vk.label(v(0.0, -0.275, 0.65), X, Z, 0.14, 0.1, 0.8))
    body.add(vk.block(v(0.09, -0.276, 0.82), v(0.11, -0.27, 0.86)), "zinc", lean, 0.002)
    for angle in (-0.75, 0.75):
        hinge_point = v(math.sin(angle) * 0.272, -math.cos(angle) * 0.272, 0.0)
        for z in (0.58, 0.98):
            body.add(vk.cylinder(0.008, 0.045, 8), "post_red", lean @ vk.frame(hinge_point + v(0.0, 0.0, z), Z))
    leaf_litter(body, rng, v(0.15, -0.3, 0.0), 0.35, 12)
    far = m.far("prop_post_box_far")
    far.add(vk.lathe([(0.0, -0.04), (0.29, -0.04), (0.29, 0.12), (0.264, 0.13), (0.264, 1.33), (0.308, 1.37), (0.3, 1.42), (0.2, 1.53), (0.0, 1.6)], 10), "steel", lean)
    m.col("metal", (-0.31, -0.31, 0.0), (0.31, 0.31, 1.6))
    m.close(v(0.35, -0.95, 1.25), v(0.0, -0.2, 1.05), 45.0)
    m.close(v(-0.25, -0.75, 0.85), v(0.0, -0.2, 0.75), 50.0)
    m.info = {"kind": "point", "front": "-Y (aperture and door)", "footprint_radius": 0.31}
    return m


def finger(target, rng, base, yaw, droop, key, words, length=0.92, height=0.155, thickness=0.03):
    outline = [(0.0, -height * 0.5), (length - 0.13, -height * 0.5), (length, 0.0), (length - 0.13, height * 0.5), (0.0, height * 0.5)]
    aspect = (length - 0.06) / height
    vk.text_mask(key, aspect, [(words, 0.56, 0.5, "GILB____.TTF", (length - 0.13) * 0.5 / height + 0.25, aspect - 1.3, 0.92, 1.08)], 1024)
    vk.register(key, "paint", color=(0.46, 0.45, 0.41), under=(0.02, 0.02, 0.02), primer=(0.12, 0.05, 0.03), chips=0.45, fade=0.2, chalk=0.05, bleed=0.4, streaks=0.55, gloss=0.6, dirt=0.55, text=(key, (0.02, 0.02, 0.022), 1.2))
    matrix = Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(droop, 4, 'Y') @ Matrix.Rotation(math.pi * 0.5, 4, 'X')
    direction = matrix.to_3x3() @ X
    side = matrix.to_3x3() @ Z
    upward = matrix.to_3x3() @ Y
    center = base + direction * (length - 0.06) * 0.5
    labels = [vk.label(center + side * thickness * 0.5, direction, upward, length - 0.06, height, 0.8), vk.label(center - side * thickness * 0.5, -direction, upward, length - 0.06, height, 0.8)]
    target.add(vk.slab(outline, thickness), key, matrix, 0.004, label=labels)
    target.add(vk.block(v(-0.07, -0.05, -height * 0.5 - 0.01), v(0.02, 0.05, height * 0.5 + 0.01)), "iron_black", Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(droop, 4, 'Y'), 0.008)


def street_sign():
    m = model("prop_street_sign", 61)
    body = m.part("prop_street_sign", 40.0)
    rng = m.rng
    lean = vk.about(v(0.0, 0.0, 0.0), Y, 0.025)
    profile = [(0.0, -0.08), (0.13, -0.08), (0.13, 0.0), (0.125, 0.03), (0.1, 0.06), (0.085, 0.12), (0.076, 0.22), (0.072, 0.26), (0.08, 0.27), (0.08, 0.3), (0.066, 0.31), (0.06, 1.2), (0.054, 2.5), (0.062, 2.51), (0.062, 2.54), (0.05, 2.55), (0.04, 2.57), (0.046, 2.6), (0.05, 2.63)]
    for step in range(1, 7):
        angle = -math.pi * 0.5 + math.pi * step / 6
        profile.append((max(0.05 * math.cos(angle), 0.0), 2.68 + 0.05 * math.sin(angle)))
    body.add(vk.lathe(profile, 18), "iron_black", lean)
    for z in (2.38, 2.17, 1.96):
        body.add(vk.lathe([(0.054, -0.05), (0.068, -0.045), (0.068, 0.045), (0.054, 0.05)], 18, closed=False), "iron_black", lean @ Matrix.Translation((0.0, 0.0, z)))
    finger(body, rng, lean @ v(0.062, 0.0, 2.38), 0.15, 0.0, "finger_halt", "ST AUBIN HALT  1/4")
    finger(body, rng, lean @ v(-0.03, 0.054, 2.17), 2.2, 0.0, "finger_gorey", "GOREY HARBOUR  7")
    finger(body, rng, lean @ v(-0.035, -0.05, 1.96), 4.1, 0.42, "finger_noirmont", "NOIRMONT  1")
    far = m.far("prop_street_sign_far")
    far.add(vk.lathe([(0.0, -0.02), (0.12, -0.02), (0.1, 0.06), (0.07, 0.3), (0.054, 2.55), (0.05, 2.73), (0.0, 2.74)], 6), "steel", lean)
    for z, yaw, droop in ((2.38, 0.15, 0.0), (2.17, 2.2, 0.0), (1.96, 4.1, 0.42)):
        far.add(vk.block(v(0.0, -0.015, -0.077), v(0.92, 0.015, 0.077)), "steel", Matrix.Translation(lean @ v(0.0, 0.0, z)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(droop, 4, 'Y'))
    m.col("metal", (-0.12, -0.12, 0.0), (0.12, 0.12, 2.75))
    m.close(v(0.9, -1.4, 2.3), v(0.4, 0.0, 2.25), 40.0)
    m.close(v(-1.0, 1.2, 2.2), v(-0.4, 0.0, 2.05), 40.0)
    m.info = {"kind": "point", "front": "-Y"}
    return m


def litter_bin():
    m = model("prop_litter_bin", 71)
    body = m.part("prop_litter_bin", 40.0)
    rng = m.rng
    profile = [(0.0, 0.0), (0.25, 0.0), (0.25, 0.05), (0.236, 0.07), (0.228, 0.1), (0.228, 0.24), (0.236, 0.25), (0.236, 0.27), (0.228, 0.28), (0.232, 0.66), (0.24, 0.67), (0.24, 0.69), (0.232, 0.7), (0.236, 0.74), (0.25, 0.75), (0.25, 0.775), (0.2, 0.775), (0.2, 0.15), (0.0, 0.15)]
    vk.text_mask("litter", 4.2, [("LITTER", 0.6, 0.5, "timesbd.ttf", 2.1, 3.6, 1.0, 1.3)])
    vk.register("bin_iron", "paint", color=(0.012, 0.012, 0.013), under=(0.07, 0.068, 0.062), primer=(0.11, 0.05, 0.03), chips=0.5, fade=0.35, chalk=0.12, bleed=0.45, streaks=0.5, gloss=0.6, dirt=0.55, bare=0.5, text=("litter", (0.36, 0.25, 0.07), 6.0))
    dent = v(0.17, -0.17, 0.45)
    shell = vk.lathe(profile, 36)
    for vert in shell.verts:
        offset = vert.co - dent
        if offset.length < 0.18 and vert.co.xy.length > 0.21:
            push = (1.0 - offset.length / 0.18) ** 2 * 0.035
            vert.co -= Vector((vert.co.x, vert.co.y, 0.0)).normalized() * push
    body.add(shell, "bin_iron", None, label=vk.label(v(0.0, -0.236, 0.47), X, Z, 0.42, 0.1, 0.82))
    for k in range(10):
        angle = tau * k / 10
        body.add(vk.block(v(-0.012, -0.006, 0.28), v(0.012, 0.006, 0.66)), "bin_iron", Matrix.Rotation(angle, 4, 'Z') @ Matrix.Translation((0.0, -0.234, 0.0)), 0.003)
    for k in range(4):
        angle = tau * k / 4 + 0.4
        body.add(vk.block(v(-0.018, -0.01, 0.77), v(0.018, 0.01, 0.9)), "bin_iron", Matrix.Rotation(angle, 4, 'Z') @ Matrix.Translation((0.0, -0.232, 0.0)), 0.004)
    body.add(vk.lathe([(0.0, 0.0), (0.262, 0.0), (0.262, 0.03), (0.25, 0.045), (0.215, 0.085), (0.15, 0.12), (0.07, 0.137), (0.0, 0.14)], 36), "bin_iron", Matrix.Translation((0.0, 0.0, 0.89)))
    body.add(g.sphere(0.03, 12, 8), "bin_iron", Matrix.Translation((0.0, 0.0, 1.05)))
    body.add(vk.lathe([(0.19, 0.16), (0.196, 0.16), (0.196, 0.82), (0.19, 0.82)], 24), "zinc")
    for k in range(9):
        angle = rng.uniform(0.0, tau)
        spread = rng.uniform(0.0, 0.12)
        body.add(crumple(rng, rng.uniform(0.04, 0.07)), "litter_paper", Matrix.Translation((math.cos(angle) * spread, math.sin(angle) * spread, 0.74 + rng.uniform(0.0, 0.08))))
    can = vk.lathe([(0.0, 0.0), (0.033, 0.0), (0.033, 0.115), (0.027, 0.122), (0.0, 0.122)], 14)
    vk.register("can", "paint", color=(0.3, 0.05, 0.02), under=(0.35, 0.35, 0.34), primer=(0.35, 0.35, 0.34), chips=0.5, fade=0.6, chalk=0.4, bleed=0.6, gloss=0.4, dirt=0.6)
    body.add(can, "can", vk.at(v(0.07, 0.02, 0.8), 0.4, 0.9, 0.2))
    body.add(vk.lathe([(0.0, 0.0), (0.033, 0.0), (0.033, 0.115), (0.027, 0.122), (0.0, 0.122)], 14), "can", vk.at(v(0.38, -0.25, 0.033), 1.1, math.pi * 0.5, 0.0))
    for k in range(3):
        body.add(crumple(rng, rng.uniform(0.04, 0.06), 0.55), "litter_paper", Matrix.Translation((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, -0.3), 0.02)))
    leaf_litter(body, rng, v(0.0, -0.1, 0.0), 0.55, 20)
    far = m.far("prop_litter_bin_far")
    far.add(vk.lathe([(0.0, 0.0), (0.25, 0.0), (0.232, 0.08), (0.232, 0.75), (0.25, 0.77), (0.24, 0.9), (0.26, 0.92), (0.15, 1.0), (0.0, 1.04)], 8), "steel")
    m.col("metal", (-0.26, -0.26, 0.0), (0.26, 0.26, 1.05))
    m.close(v(0.45, -0.85, 1.05), v(0.0, 0.0, 0.7), 45.0)
    m.info = {"kind": "point", "front": "-Y", "footprint_radius": 0.26}
    return m


def shelter():
    m = model("prop_bus_shelter", 31)
    body = m.part("prop_bus_shelter", 40.0)
    rng = m.rng
    hx = 1.47
    hy = 0.67
    top = 2.22
    posts = [(-hx, hy), (hx, hy), (-hx, -hy), (hx, -hy), (-0.49, hy), (0.49, hy), (-hx, -0.22), (hx, -0.22)]
    for x, y in posts:
        body.add(vk.block(v(x - 0.035, y - 0.035, -0.08), v(x + 0.035, y + 0.035, top)), "iron_green", None, 0.006)
        body.add(vk.block(v(x - 0.06, y - 0.06, -0.02), v(x + 0.06, y + 0.06, 0.012)), "iron_green", None, 0.004)
        for dx, dy in ((-0.04, -0.04), (0.04, 0.04)):
            vk.bolt(body, v(x + dx, y + dy, 0.012), Z, 0.018, "zinc", False)
    for y in (-hy, hy):
        body.add(vk.block(v(-hx - 0.035, y - 0.04, top - 0.1), v(hx + 0.035, y + 0.04, top)), "iron_green", None, 0.006)
    for x in (-hx, hx):
        body.add(vk.block(v(x - 0.04, -hy, top - 0.1), v(x + 0.04, hy, top)), "iron_green", None, 0.006)
    roof = vk.grid_sheet(3.24, 1.62, 18, 9, lambda x, y: 0.003 * math.sin(x * 40.0))
    vk.thicken(roof, 0.012)
    vk.register("roof_felt", "fabric", kind="canvas", tint=(0.05, 0.05, 0.046), weave=3.0, stains=0.6, mildew=0.4, dirt=0.6, moss=0.7)
    body.add(roof, "roof_felt", Matrix.Translation((0.0, 0.0, top + 0.05)))
    for y, normal in ((-hy - 0.12, -1.0), (hy + 0.12, 1.0)):
        body.add(vk.block(v(-hx - 0.15, y - 0.012, top - 0.06), v(hx + 0.15, y + 0.012, top + 0.1)), "paint_white" if normal < 0 else "iron_green", None, 0.004)
    for x in (-hx - 0.14, hx + 0.14):
        body.add(vk.block(v(x - 0.012, -hy - 0.13, top - 0.06), v(x + 0.012, hy + 0.13, top + 0.1)), "iron_green", None, 0.004)
    for x in (-hx, -0.49, 0.49, hx):
        body.add(vk.block(v(x - 0.02, -hy - 0.12, top - 0.02), v(x + 0.02, hy + 0.12, top + 0.04)), "iron_green", None, 0.003)
    vk.text_mask("shelter_name", 15.0, [("THE BULWARKS", 0.62, 0.5, "GILB____.TTF", 7.5, 13.0, 1.0, 1.2)])
    vk.register("shelter_fascia", "paint", color=(0.4, 0.39, 0.35), under=(0.03, 0.06, 0.04), primer=(0.12, 0.05, 0.03), chips=0.5, fade=0.2, chalk=0.05, bleed=0.45, streaks=0.6, gloss=0.6, dirt=0.65, text=("shelter_name", (0.02, 0.05, 0.03), 0.3))
    body.add(vk.block(v(-1.1, -hy - 0.135, top - 0.045), v(1.1, -hy - 0.13, top + 0.085)), "shelter_fascia", None, 0.0, label=vk.label(v(0.0, -hy - 0.136, top + 0.02), X, Z, 2.2, 0.13, 0.8))
    states = {(-1, 0): "glass", (0, 0): "glass", (1, 0): "broken", ("left", 0): "missing", ("right", 0): "cracked"}
    bays = [(-hx, -0.49, -1), (-0.49, 0.49, 0), (0.49, hx, 1)]
    for x0, x1, key in bays:
        width = x1 - x0 - 0.07
        middle = (x0 + x1) * 0.5
        for z in (0.16, 2.06):
            body.add(vk.block(v(x0 + 0.035, hy - 0.025, z - 0.025), v(x1 - 0.035, hy + 0.025, z + 0.025)), "iron_green", None, 0.004)
        pane(body, rng, Matrix.Translation((middle, hy, 1.11)), width, 1.86, states[(key, 0)])
        if states[(key, 0)] == "broken":
            shards(body, rng, v(middle, hy - 0.35, 0.0), 0.45, 22)
    for side, x in (("left", -hx), ("right", hx)):
        for z in (0.16, 2.06):
            body.add(vk.block(v(x - 0.025, -0.22 + 0.035, z - 0.025), v(x + 0.025, hy - 0.035, z + 0.025)), "iron_green", None, 0.004)
        state = states[(side, 0)]
        pane(body, rng, Matrix.Translation((x, (hy - 0.22) * 0.5, 1.11)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Z'), hy + 0.22 - 0.07, 1.86, state)
        if state == "missing":
            for k in range(5):
                piece = [(rng.uniform(-0.05, 0.0), 0.0), (rng.uniform(0.02, 0.08), 0.0), (rng.uniform(-0.02, 0.03), rng.uniform(0.06, 0.18))]
                body.add(vk.slab(piece, 0.006), "glass_cracked", Matrix.Translation((x, -0.1 + k * 0.17, 0.185)) @ Matrix.Rotation(math.pi * 0.5, 4, 'X') @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
            shards(body, rng, v(x + 0.35, 0.2, 0.0), 0.4, 18)
    for x in (-1.25, 0.0, 1.25):
        body.add(vk.block(v(x - 0.02, hy - 0.3, 0.6), v(x + 0.02, hy - 0.02, 0.63)), "iron_green", None, 0.003)
        body.add(vk.block(v(x - 0.02, hy - 0.04, 0.45), v(x + 0.02, hy - 0.02, 0.63)), "iron_green", None, 0.003)
    for index, y in enumerate((hy - 0.24, hy - 0.12)):
        body.add(vk.cube(2.7, 0.1, 0.035), "teak", Matrix.Translation((0.0, y + 0.02, 0.648)) @ Matrix.Rotation(rng.uniform(-0.01, 0.01), 4, 'Y'), 0.004, tint=(rng.uniform(0.85, 1.1), rng.uniform(0.85, 1.05), rng.uniform(0.8, 1.0)))
    vk.text_mask("timetable", 0.75, [("J.M.T.", 0.09, 0.9, "GILB____.TTF", 0.375, 0.6), ("ROUTE 12", 0.07, 0.8, "GILB____.TTF", 0.375, 0.6), ("ST AUBIN - ST HELIER", 0.045, 0.72, "GIL_____.TTF", 0.375, 0.66)] + [("06 15   07 40   09 05   10 30   11 55   13 20", 0.03, 0.62 - k * 0.055, "GIL_____.TTF", 0.375, 0.66) for k in range(9)], 1024, [(0.03, 0.006)])
    vk.register("timetable", "organic", kind="paper", tint=(0.5, 0.48, 0.4), dirt=0.6, text=("timetable", (0.03, 0.03, 0.035), 0.0))
    case = v(0.0, hy - 0.06, 1.38)
    body.add(vk.block(case + v(-0.33, -0.03, -0.42), case + v(0.33, 0.03, 0.42)), "iron_green", None, 0.006)
    body.add(vk.block(case + v(-0.29, -0.034, -0.38), case + v(0.29, -0.03, 0.38)), "timetable", None, 0.0, label=vk.label(case + v(0.0, -0.035, 0.0), X, Z, 0.58, 0.76, 0.8))
    body.add(vk.block(case + v(-0.29, -0.038, -0.38), case + v(-0.05, -0.034, 0.12)), "glass_cracked", None)
    pole = v(-hx - 0.06, -hy - 0.06, 0.0)
    body.add(vk.cylinder(0.03, 3.0, 12), "zinc", vk.frame(pole, Z))
    for z in (1.0, 2.0):
        body.add(vk.block(pole + v(0.0, 0.0, z - 0.02) - v(0.035, 0.035, 0.0), pole + v(0.07, 0.035, z + 0.02)), "zinc", None, 0.003)
    vk.text_mask("bus_flag", 1.5, [("BUS", 0.42, 0.62, "GILB____.TTF", 0.75, 1.3), ("STOP", 0.42, 0.25, "GILB____.TTF", 0.75, 1.3)], 1024, [(0.03, 0.02)])
    vk.register("bus_flag", "paint", color=(0.48, 0.47, 0.43), under=(0.1, 0.1, 0.1), primer=(0.3, 0.3, 0.29), chips=0.35, fade=0.3, chalk=0.05, bleed=0.3, streaks=0.5, gloss=0.55, dirt=0.5, text=("bus_flag", (0.12, 0.02, 0.015), 0.3))
    flag = pole + v(0.0, 0.0, 2.7) + v(0.0, -0.26, 0.0)
    body.add(vk.cube(0.012, 0.45, 0.3), "bus_flag", Matrix.Translation(flag) @ Matrix.Rotation(0.05, 4, 'X'), 0.002, label=[vk.label(flag + v(-0.007, 0.0, 0.0), v(0.0, 1.0, 0.0), Z, 0.45, 0.3, 0.8), vk.label(flag + v(0.007, 0.0, 0.0), v(0.0, -1.0, 0.0), Z, 0.45, 0.3, 0.8)])
    leaf_litter(body, rng, v(-1.0, 0.35, 0.0), 0.35, 26)
    leaf_litter(body, rng, v(1.1, 0.45, 0.0), 0.25, 14)
    leaf_litter(body, rng, v(0.3, 0.2, top + 0.056), 0.6, 30, 0.0)
    paper = vk.grid_sheet(0.42, 0.3, 4, 3, lambda x, y: 0.015 * math.sin(x * 14.0) + 0.01 * math.cos(y * 20.0))
    vk.thicken(paper, 0.002)
    vk.register("newspaper", "organic", kind="paper", tint=(0.42, 0.41, 0.37), dirt=0.6)
    body.add(paper, "newspaper", vk.at(v(0.4, 0.15, 0.018), 0.6))
    far = m.far("prop_bus_shelter_far")
    far.add(vk.block(v(-hx - 0.15, -hy - 0.13, top - 0.06), v(hx + 0.15, hy + 0.13, top + 0.1)), "steel")
    far.add(vk.block(v(-hx, hy - 0.02, 0.0), v(hx, hy + 0.02, top - 0.06)), "steel")
    for x in (-hx, hx):
        far.add(vk.block(v(x - 0.02, -0.25, 0.0), v(x + 0.02, hy, top - 0.06)), "steel")
    for x, y in posts[2:4]:
        far.add(vk.block(v(x - 0.035, y - 0.035, 0.0), v(x + 0.035, y + 0.035, top - 0.06)), "steel")
    far.add(vk.block(v(-1.35, hy - 0.26, 0.6), v(1.35, hy - 0.02, 0.67)), "steel")
    far.add(vk.block(pole + v(-0.03, -0.03, 0.0), pole + v(0.03, 0.03, 3.0)), "steel")
    far.add(vk.block(flag + v(-0.006, -0.225, -0.15), flag + v(0.006, 0.225, 0.15)), "steel")
    m.col("glass", (-hx - 0.04, hy - 0.04, 0.0), (hx + 0.04, hy + 0.04, top))
    for x in (-hx, hx):
        m.col("glass", (x - 0.04, -0.26, 0.0), (x + 0.04, hy, top))
    m.col("metal", (-hx - 0.16, -hy - 0.14, top - 0.06), (hx + 0.16, hy + 0.14, top + 0.12))
    m.col("wood", (-1.35, hy - 0.3, 0.45), (1.35, hy - 0.02, 0.67))
    m.col("metal", pole + v(-0.04, -0.04, 0.0), pole + v(0.04, 0.04, 3.0))
    m.close(v(0.9, -1.7, 1.6), v(0.6, 0.6, 1.1), 35.0)
    m.close(v(-0.6, -0.9, 1.5), v(0.0, 0.6, 1.3), 40.0)
    m.close(v(-2.3, -2.2, 2.6), v(-1.53, -0.73, 2.55), 50.0)
    m.info = {"kind": "point", "front": "-Y (open side)", "length": 3.24}
    return m


def bollard():
    m = model("prop_bollard", 11)
    body = m.part("prop_bollard", 40.0)
    profile = [(0.0, -0.06), (0.126, -0.06), (0.126, 0.0), (0.134, 0.01), (0.134, 0.032), (0.12, 0.05), (0.106, 0.072), (0.1, 0.1), (0.097, 0.42), (0.093, 0.69), (0.091, 0.775), (0.099, 0.785), (0.109, 0.8), (0.109, 0.842), (0.099, 0.856), (0.086, 0.87), (0.07, 0.884), (0.06, 0.9)]
    center = 0.952
    radius = 0.07
    for step in range(1, 9):
        angle = -math.radians(48.0) + (math.pi * 0.5 + math.radians(48.0)) * step / 8
        profile.append((max(radius * math.cos(angle), 0.0), center + radius * math.sin(angle)))
    lean = vk.about(v(0.0, 0.0, 0.0), X, 0.03) @ vk.about(v(0.0, 0.0, 0.0), Y, -0.012)
    vk.text_mask("bollard", 1.4, [("ST BRELADE", 0.5, 0.5, "GILB____.TTF", 0.7, 1.3, 1.0, 1.05)])
    vk.register("bollard_iron", "paint", color=(0.012, 0.012, 0.013), under=(0.07, 0.068, 0.062), primer=(0.11, 0.05, 0.03), chips=0.5, fade=0.35, chalk=0.12, bleed=0.45, streaks=0.5, gloss=0.6, dirt=0.5, bare=0.5, text=("bollard", (0.07, 0.066, 0.06), 7.0))
    tag = vk.label(v(0.0, -0.095, 0.5), X, Z, 0.17, 0.12, 0.6)
    body.add(vk.lathe(profile, 28), "bollard_iron", lean, label=tag)
    body.add(vk.lathe([(0.0955, 0.598), (0.0995, 0.602), (0.0995, 0.678), (0.0955, 0.682)], 28), "paint_white", lean)
    for index in range(4):
        angle = tau * index / 4 + 0.4
        body.add(vk.cube(0.016, 0.03, 0.022), "bollard_iron", lean @ vk.at(v(math.cos(angle) * 0.13, math.sin(angle) * 0.13, 0.03), angle), 0.003)
    far = m.far("prop_bollard_far")
    far.add(vk.lathe([(0.0, -0.02), (0.13, -0.02), (0.13, 0.03), (0.1, 0.08), (0.093, 0.78), (0.108, 0.8), (0.108, 0.85), (0.06, 0.9), (0.065, 0.97), (0.0, 1.02)], 8), "steel", lean)
    m.col("metal", (-0.11, -0.11, 0.0), (0.11, 0.11, 1.0))
    m.close(v(0.32, -0.55, 0.78), v(0.0, 0.0, 0.62), 50.0)
    m.info = {"footprint_radius": 0.134, "kind": "point"}
    return m


def produce_looks():
    vk.register("timber", "wood", along="Z", light=(0.2, 0.16, 0.11), dark=(0.08, 0.065, 0.05), silver=0.7, cracks=0.55, moss=0.2, lichen=0.2, dirt=0.5)
    vk.register("timber_x", "wood", along="X", light=(0.2, 0.16, 0.11), dark=(0.08, 0.065, 0.05), silver=0.7, cracks=0.55, moss=0.15, dirt=0.5)
    vk.register("timber_y", "wood", along="Y", light=(0.2, 0.16, 0.11), dark=(0.08, 0.065, 0.05), silver=0.7, cracks=0.55, moss=0.15, dirt=0.5)
    vk.register("crate_wood", "wood", along="X", light=(0.26, 0.21, 0.15), dark=(0.12, 0.1, 0.075), silver=0.55, cracks=0.4, moss=0.1, dirt=0.55)
    vk.register("apple", "organic", kind="paper", tint=(0.13, 0.025, 0.015), dirt=0.6, moss=0.4)
    vk.register("cabbage", "organic", kind="paper", tint=(0.07, 0.085, 0.025), dirt=0.6, moss=0.3, creases=0.6)
    vk.register("potato", "organic", kind="paper", tint=(0.16, 0.11, 0.06), dirt=0.8, moss=0.2)


def crate(target, rng, center, size, yaw=0.0, produce=None, roll=0.0, pitch=0.0):
    sx, sy, sz = size
    base = Matrix.Translation(center) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'Y') @ Matrix.Rotation(roll, 4, 'X')
    tone = (rng.uniform(0.82, 1.15), rng.uniform(0.82, 1.1), rng.uniform(0.8, 1.05))
    for side in (-1.0, 1.0):
        for k, z in enumerate((sz * 0.25, sz * 0.72)):
            target.add(vk.cube(sx, 0.012, sz * 0.36), "crate_wood", base @ Matrix.Translation((0.0, side * (sy * 0.5 - 0.006), z)), 0.002, tint=tone)
            target.add(vk.cube(0.012, sy - 0.024, sz * 0.36), "crate_wood", base @ Matrix.Translation((side * (sx * 0.5 - 0.006), 0.0, z)), 0.002, tint=tone)
        for other in (-1.0, 1.0):
            target.add(vk.cube(0.03, 0.03, sz), "crate_wood", base @ Matrix.Translation((side * (sx * 0.5 - 0.02), other * (sy * 0.5 - 0.02), sz * 0.5)), 0.003, tint=tone)
    target.add(vk.cube(sx - 0.02, sy - 0.02, 0.012), "crate_wood", base @ Matrix.Translation((0.0, 0.0, 0.01)), 0.002, tint=tone)
    if produce:
        look, radius, count = produce
        for index in range(count):
            px = rng.uniform(-sx * 0.5 + radius, sx * 0.5 - radius)
            py = rng.uniform(-sy * 0.5 + radius, sy * 0.5 - radius)
            pz = sz * rng.uniform(0.55, 0.85)
            target.add(vk.lump(radius * rng.uniform(0.85, 1.15), radius * rng.uniform(0.85, 1.15), radius * rng.uniform(0.7, 1.0), rng, 0.25, 1), look, base @ Matrix.Translation((px, py, pz)))


def canvas_sheet(xs, ys, height, holes=()):
    bm = bmesh.new()
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            row.append(bm.verts.new((x, y, height(x, y))))
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            cx = (xs[i] + xs[i + 1]) * 0.5
            cy = (ys[j] + ys[j + 1]) * 0.5
            if any(hole(cx, cy) for hole in holes):
                continue
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    loose = [vert for vert in bm.verts if not vert.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    return vk.thicken(bm, 0.004)


def scallop_strip(xs, top, depth, width=0.24):
    bm = bmesh.new()
    upper = []
    lower = []
    for x in xs:
        phase = ((x / width) % 1.0)
        drop = depth - 0.045 * (1.0 - math.sin(math.pi * phase))
        upper.append(bm.verts.new(top(x)))
        lower.append(bm.verts.new(top(x) - Vector((0.0, 0.0, drop))))
    for i in range(len(xs) - 1):
        bm.faces.new((lower[i], lower[i + 1], upper[i + 1], upper[i]))
    return vk.thicken(bm, 0.004)


def market_stall(variant):
    broken = variant == "b"
    name = "prop_market_stall_" + variant
    m = model(name, 82 if broken else 81)
    body = m.part(name, 52.0)
    rng = m.rng
    produce_looks()
    canvas = "canvas_green" if broken else "canvas_red"
    hx = 1.2
    hy = 0.6
    front_h = 2.05
    back_h = 2.32
    snap = 0.95

    def front_z(x):
        return front_h - (front_h - snap - 0.03) * smooth_ramp(x, 0.0, hx) if broken else front_h

    def roof(x, y):
        t = (y + hy) / (2.0 * hy)
        edge = front_z(min(max(x, -hx), hx))
        z = edge + (back_h - edge) * t
        bay = ((x + hx) / 0.6) % 1.0
        sag = 0.028 * math.sin(math.pi * bay) * (1.0 - abs(t - 0.5) * 0.6)
        if y < -hy:
            z -= (-hy - y) * 0.35
        return z + 0.03 - sag

    for x in (-hx, hx):
        for y in (-hy, hy):
            top = front_z(x) if y < 0 else back_h
            if broken and x > 0 and y < 0:
                body.add(vk.block(v(x - 0.035, y - 0.035, -0.05), v(x + 0.035, y + 0.035, snap)), "timber", None, 0.004)
                for k in range(4):
                    body.add(vk.cone(v(x - 0.025 + k * 0.016, y + rng.uniform(-0.02, 0.02), snap - 0.01), v(x - 0.025 + k * 0.016 + rng.uniform(-0.01, 0.01), y + rng.uniform(-0.02, 0.02), snap + rng.uniform(0.04, 0.12)), 0.012, 4), "timber")
                fallen = vk.block(v(-0.035, -0.035, 0.0), v(0.035, 0.035, front_h - snap))
                body.add(fallen, "timber", vk.at(v(x + 0.35, y - 0.55, 0.036), 0.5, math.pi * 0.5, 0.0), 0.004)
                continue
            body.add(vk.block(v(x - 0.035, y - 0.035, -0.05), v(x + 0.035, y + 0.035, top)), "timber", None, 0.004)
            m.col("wood", (x - 0.04, y - 0.04, 0.0), (x + 0.04, y + 0.04, top))
    body.add(vk.bar(v(-hx, -hy, front_z(-hx) - 0.02), v(hx, -hy, front_z(hx) - 0.02), 0.05, 0.06), "timber_x", None, 0.004)
    body.add(vk.bar(v(-hx, hy, back_h - 0.02), v(hx, hy, back_h - 0.02), 0.05, 0.06), "timber_x", None, 0.004)
    for x in (-hx, -0.6, 0.0, 0.6, hx):
        body.add(vk.bar(v(x, -hy - 0.12, front_z(x) - 0.04 + 0.12 * 0.35 * 0.0), v(x, hy, back_h + 0.0), 0.045, 0.05), "timber_y", None, 0.004)
    holes = []
    if broken:
        holes = [lambda x, y: (x - 0.35) ** 2 / 0.09 + (y + 0.1) ** 2 / 0.02 < 1.0 + 0.4 * math.sin(x * 23.0) * math.cos(y * 17.0), lambda x, y: (x + 0.75) ** 2 / 0.02 + (y - 0.25) ** 2 / 0.05 < 1.0 + 0.4 * math.sin(x * 29.0 + y * 13.0)]
    xs = [-hx - 0.1 + (2.0 * hx + 0.2) * i / 32 for i in range(33)]
    ys = [-hy - 0.22 + (2.0 * hy + 0.3) * j / 18 for j in range(19)]
    body.add(canvas_sheet(xs, ys, roof, holes), canvas)
    body.add(scallop_strip(xs, lambda x: v(x, -hy - 0.22, roof(x, -hy - 0.22)), 0.2), canvas)
    if broken:
        flap = vk.grid_sheet(0.32, 0.6, 3, 6, lambda x, y: 0.03 * math.sin(y * 8.0))
        vk.thicken(flap, 0.004)
        body.add(flap, canvas, Matrix.Translation((0.35, -0.1, roof(0.35, -0.1) - 0.3)) @ Matrix.Rotation(1.45, 4, 'X') @ Matrix.Rotation(0.2, 4, 'Z'))
    table_z = 0.86
    tilt = math.atan2(table_z - 0.06, 1.75) if broken else 0.0
    table = vk.about(v(-0.85, -0.3, table_z), Y, tilt) if broken else Matrix.Identity(4)
    for k, y in enumerate((-0.47, -0.3, -0.13)):
        body.add(vk.cube(2.3, 0.165, 0.03), "timber_x", table @ Matrix.Translation((rng.uniform(-0.01, 0.01), y, table_z + 0.015)), 0.003, tint=(rng.uniform(0.85, 1.1), rng.uniform(0.85, 1.05), rng.uniform(0.8, 1.0)))
    for x in (-0.85, 0.85):
        legs = Matrix.Identity(4) if not (broken and x > 0) else vk.about(v(x, -0.3, 0.0), Y, -1.35)
        for y0, y1 in ((-0.56, -0.38), (-0.04, -0.22)):
            body.add(vk.bar(v(x, y0, 0.0), v(x, y1, table_z - 0.01), 0.045, 0.035, X), "timber", legs, 0.003)
        body.add(vk.cube(0.04, 0.5, 0.05), "timber_y", legs @ Matrix.Translation((x, -0.3, table_z - 0.03)), 0.003)
    if broken:
        crate(body, rng, v(0.45, -0.85, 0.0), (0.5, 0.34, 0.24), 0.7, ("apple", 0.04, 8), 0.0, 0.0)
        crate(body, rng, v(-0.2, -0.95, 0.17), (0.5, 0.34, 0.24), 1.9, None, 1.7, 0.0)
        crate(body, rng, v(-0.75, -0.25, table_z + 0.03), (0.5, 0.34, 0.24), 0.1, ("potato", 0.035, 8))
        for k in range(14):
            body.add(vk.lump(0.04, 0.04, 0.034, rng, 0.25, 1), "apple", Matrix.Translation((rng.uniform(-0.1, 1.2), rng.uniform(-1.3, -0.6), 0.032)))
        m.loot("food", v(0.5, -0.85, 0.0))
        m.col("wood", (-1.15, -0.56, 0.0), (1.15, -0.04, 0.6))
    else:
        crate(body, rng, v(-0.7, -0.3, table_z + 0.03), (0.5, 0.34, 0.24), 0.05, ("apple", 0.04, 10))
        crate(body, rng, v(-0.15, -0.32, table_z + 0.03), (0.5, 0.34, 0.24), -0.08, ("potato", 0.035, 10))
        crate(body, rng, v(0.45, -0.28, table_z + 0.03), (0.5, 0.34, 0.24), 0.12, ("cabbage", 0.07, 5))
        crate(body, rng, v(0.75, 0.25, 0.0), (0.5, 0.34, 0.24), 0.3, None)
        crate(body, rng, v(0.72, 0.22, 0.25), (0.5, 0.34, 0.24), 0.45, ("potato", 0.035, 6))
        m.loot("food", v(0.2, -0.3, table_z + 0.03))
        m.col("wood", (-1.15, -0.56, 0.0), (1.15, -0.04, table_z + 0.03))
        m.col("wood", (0.45, 0.0, 0.0), (1.05, 0.5, 0.5))
    vk.text_mask("chalk_" + variant, 0.7, [("JERSEY", 0.16, 0.8, "Kalam-Bold.ttf", 0.35, 0.62), ("ROYALS", 0.16, 0.6, "Kalam-Bold.ttf", 0.35, 0.62), ("50p lb", 0.13, 0.35, "Kalam-Bold.ttf", 0.35, 0.6)], 1024, [(0.02, 0.012)])
    vk.register("chalkboard_" + variant, "organic", kind="paper", tint=(0.035, 0.04, 0.036), dirt=0.4, text=("chalk_" + variant, (0.36, 0.36, 0.33), 0.0))
    board = v(-hx + 0.05, -hy - 0.28, 0.0)
    lean = Matrix.Translation(board) @ Matrix.Rotation(0.3, 4, 'Z') @ Matrix.Rotation(-0.28, 4, 'X')
    body.add(vk.cube(0.42, 0.02, 0.6), "chalkboard_" + variant, lean @ Matrix.Translation((0.0, 0.0, 0.32)), 0.003, label=vk.label(lean @ v(0.0, -0.011, 0.32), (lean.to_3x3() @ X), (lean.to_3x3() @ Z), 0.42, 0.6, 0.8))
    body.add(vk.lump(0.22, 0.17, 0.3, rng, 0.12, 2, 0.0), "hessian", Matrix.Translation((hx + 0.25, 0.2, 0.0)))
    leaf_litter(body, rng, v(0.0, -0.2, 0.0), 1.1, 30)
    far = m.far(name + "_far")
    far.add(canvas_sheet([xs[0], xs[16], xs[-1]], [ys[0], ys[9], ys[-1]], roof), "steel")
    far.add(vk.block(v(-1.15, -0.56, 0.0), v(1.15, -0.04, 0.89)), "steel", table if not broken else None)
    for x in (-hx, hx):
        for y in (-hy, hy):
            if broken and x > 0 and y < 0:
                continue
            far.add(vk.block(v(x - 0.035, y - 0.035, 0.0), v(x + 0.035, y + 0.035, front_z(x) if y < 0 else back_h)), "steel")
    m.close(v(1.6, -2.1, 1.7), v(0.0, -0.3, 1.0), 38.0)
    m.close(v(-0.2, -1.5, 1.35), v(-0.3, -0.3, 0.9), 45.0)
    m.info = {"kind": "point", "front": "-Y (counter side)", "variant": variant}
    return m


def smooth_ramp(x, low, high):
    t = min(max((x - low) / (high - low), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def verdigris_mask(width=256, height=512, seed=3):
    rng = numpy.random.default_rng(seed)
    columns = numpy.zeros(width)
    for index in range(14):
        center = rng.uniform(0.15, 0.85) * width
        spread = rng.uniform(3.0, 14.0)
        columns += rng.uniform(0.4, 1.0) * numpy.exp(-((numpy.arange(width) - center) / spread) ** 2)
    columns = numpy.clip(columns, 0.0, 1.0)
    ys = numpy.arange(height) / height
    length = rng.uniform(0.35, 1.0, width)
    length = numpy.convolve(length, numpy.ones(9) / 9.0, mode="same")
    fade = numpy.clip((ys[:, None] - (1.0 - length[None, :])) / 0.25, 0.0, 1.0)
    edge = numpy.clip(numpy.minimum(numpy.arange(width), width - 1 - numpy.arange(width)) / (width * 0.1), 0.0, 1.0)
    noise = rng.uniform(0.7, 1.0, (height, width))
    return columns[None, :] * fade * edge[None, :] * noise


def war_memorial():
    m = model("prop_war_memorial", 91)
    body = m.part("prop_war_memorial", 35.0)
    rng = m.rng
    vk.register("memorial_granite", "stone", kind="library", library="granite_ashlar", tint=(0.92, 0.92, 0.92), lichen=0.55, moss=0.35, dirt=0.45, streaks=0.4, tooled=0.2)
    vk.mask_image("verdigris", verdigris_mask())
    vk.register("memorial_die", "stone", kind="library", library="granite_ashlar", tint=(0.92, 0.92, 0.92), lichen=0.45, moss=0.25, dirt=0.45, streaks=0.4, tooled=0.2, text=("verdigris", (0.07, 0.15, 0.11), 0.0))
    vk.text_mask("lest", 0.62, [("LEST", 0.14, 0.8, "timesbd.ttf", 0.31, 0.55, 1.0, 1.2), ("WE", 0.14, 0.55, "timesbd.ttf", 0.31, 0.55, 1.0, 1.2), ("FORGET", 0.14, 0.3, "timesbd.ttf", 0.31, 0.57, 1.0, 1.1)])
    vk.register("memorial_shaft", "stone", kind="library", library="granite_ashlar", tint=(0.92, 0.92, 0.92), lichen=0.6, moss=0.2, dirt=0.4, streaks=0.5, tooled=0.15, text=("lest", (0.045, 0.04, 0.035), -4.0))
    for width, z0, z1 in ((2.6, -0.08, 0.22), (2.1, 0.22, 0.44), (1.6, 0.44, 0.66)):
        w = width * 0.5
        d = 0.38
        slabs = [(v(-w, -w, z0), v(w, -w + d, z1)), (v(-w, w - d, z0), v(w, w, z1)), (v(-w, -w + d + 0.004, z0), v(-w + d, w - d - 0.004, z1)), (v(w - d, -w + d + 0.004, z0), v(w, w - d - 0.004, z1))]
        for low, high in slabs:
            body.add(vk.block(low, high), "memorial_granite", None, 0.012, 1, tint=(rng.uniform(0.9, 1.1),) * 3)
        body.add(vk.block(v(-w + d + 0.004, -w + d + 0.004, z0), v(w - d - 0.004, w - d - 0.004, z1 - 0.004)), "memorial_granite", None)
    body.add(vk.block(v(-0.6, -0.6, 0.66), v(0.6, 0.6, 0.8)), "memorial_granite", None, 0.02, 2)
    body.add(vk.block(v(-0.54, -0.54, 0.8), v(0.54, 0.54, 0.86)), "memorial_granite", None, 0.015, 1)
    half = 0.475
    die_labels = [vk.label(v(0.0, -half - 0.001, 0.95), X, Z, 0.7, 0.62, 0.8), vk.label(v(half + 0.001, 0.0, 0.95), Y, Z, 0.7, 0.62, 0.8), vk.label(v(0.0, half + 0.001, 0.95), -X, Z, 0.7, 0.62, 0.8), vk.label(v(-half - 0.001, 0.0, 0.95), -Y, Z, 0.7, 0.62, 0.8)]
    body.add(vk.block(v(-half, -half, 0.86), v(half, half, 2.05)), "memorial_die", None, 0.012, 1, label=die_labels)
    body.add(vk.block(v(-0.56, -0.56, 2.05), v(0.56, 0.56, 2.15)), "memorial_granite", None, 0.02, 2)
    body.add(vk.block(v(-0.5, -0.5, 2.15), v(0.5, 0.5, 2.21)), "memorial_granite", None, 0.012, 1)
    shaft = bmesh.new()
    low = [shaft.verts.new((x * 0.31, y * 0.31, 2.21)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    high = [shaft.verts.new((x * 0.2, y * 0.2, 5.3)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    apex = shaft.verts.new((0.0, 0.0, 5.72))
    shaft.faces.new(list(reversed(low)))
    for i in range(4):
        j = (i + 1) % 4
        shaft.faces.new((low[i], low[j], high[j], high[i]))
        shaft.faces.new((high[i], high[j], apex))
    bmesh.ops.recalc_face_normals(shaft, faces=shaft.faces)
    lean_face = math.atan2(0.11, 3.09)
    shaft_label = vk.label(v(0.0, -0.31 + (0.11 * (2.9 - 2.21) / 3.09), 2.9), X, v(0.0, 0.11 / 3.09, 1.0), 0.36, 0.58, 0.8)
    body.add(shaft, "memorial_shaft", None, 0.01, 1, label=shaft_label)
    cross = [(-0.03, 0.0), (0.03, 0.0), (0.03, 0.42), (0.13, 0.42), (0.13, 0.48), (0.03, 0.48), (0.03, 0.6), (-0.03, 0.6), (-0.03, 0.48), (-0.13, 0.48), (-0.13, 0.42), (-0.03, 0.42)]
    z_cross = 4.15
    y_face = -0.31 + 0.11 * (z_cross - 2.21) / 3.09
    body.add(vk.slab(cross, 0.04), "memorial_granite", Matrix.Translation((0.0, y_face, z_cross)) @ Matrix.Rotation(-lean_face, 4, 'X') @ Matrix.Rotation(math.pi * 0.5, 4, 'X'), 0.006)
    vk.text_mask("memorial_front", 0.82, [("TO THE GLORIOUS MEMORY", 0.07, 0.88, "timesbd.ttf", 0.41, 0.74), ("OF THE MEN OF", 0.06, 0.79, "timesbd.ttf", 0.41, 0.74), ("ST AUBIN", 0.11, 0.67, "timesbd.ttf", 0.41, 0.74), ("WHO GAVE THEIR LIVES", 0.06, 0.55, "timesbd.ttf", 0.41, 0.74), ("FOR KING AND COUNTRY", 0.06, 0.47, "timesbd.ttf", 0.41, 0.74), ("1914 - 1918", 0.09, 0.33, "timesbd.ttf", 0.41, 0.74), ("1939 - 1945", 0.09, 0.2, "timesbd.ttf", 0.41, 0.74)], 1024, [(0.03, 0.012)])
    surnames = ["LE BRUN", "DE GRUCHY", "VIBERT", "LE QUESNE", "RENOUF", "AHIER", "LE CORNU", "PALLOT", "LE SUEUR", "MAUGER", "BISSON", "GALLICHAN", "LE FEUVRE", "DU FEU", "LE MAISTRE", "QUERIPEL", "LE GALLAIS", "BOUCHARD", "AMY", "LE MARQUAND", "HAMON", "LE CAPELAIN", "NICOLLE", "FALLE", "GRUCHY", "DE LA HAYE", "LE BOUTILLIER", "MALZARD", "PICOT", "SIMON"]
    for face, key in ((1, "memorial_names_a"), (2, "memorial_names_b"), (3, "memorial_names_c")):
        chosen = rng.sample(surnames, 16)
        initials = ["%s.%s." % (rng.choice("AJHPWGECRT"), rng.choice("ABCDEFGHJLMNPRSTW")) for name in chosen]
        lines = [("1914 - 1918" if face != 3 else "1939 - 1945", 0.07, 0.9, "timesbd.ttf", 0.41, 0.74)]
        for row in range(8):
            for column in range(2):
                index = row * 2 + column
                lines.append((initials[index] + " " + chosen[index], 0.045, 0.78 - row * 0.085, "timesbd.ttf", 0.22 + column * 0.38, 0.36))
        vk.text_mask(key, 0.82, lines, 1024, [(0.03, 0.012)])
    plaque_keys = ["memorial_front", "memorial_names_a", "memorial_names_b", "memorial_names_c"]
    normals = [v(0.0, -1.0, 0.0), v(1.0, 0.0, 0.0), v(0.0, 1.0, 0.0), v(-1.0, 0.0, 0.0)]
    for key, normal in zip(plaque_keys, normals):
        vk.register("plaque_" + key, "bronze", verdigris=0.8, tone=(0.12, 0.08, 0.04), text=(key, (0.0, 0.0, 0.0), 3.0))
        u = Z.cross(normal)
        center = normal * (half + 0.009) + v(0.0, 0.0, 1.5)
        frame = Matrix((u, -normal, Z)).transposed().to_4x4()
        frame.translation = center
        body.add(vk.cube(0.62, 0.016, 0.76), "plaque_" + key, frame, 0.004, label=vk.label(center + normal * 0.009, u, Z, 0.62, 0.76, 0.8))
        for du, dz in ((-0.27, -0.34), (0.27, -0.34), (-0.27, 0.34), (0.27, 0.34)):
            vk.rivet(body, center + u * du + Z * dz + normal * 0.009, normal, 0.009, "plaque_" + key)
    vk.register("poppy", "organic", kind="paper", tint=(0.2, 0.02, 0.015), dirt=0.6, moss=0.2)
    vk.register("wreath_leaf", "organic", kind="paper", tint=(0.04, 0.05, 0.025), dirt=0.6)
    wreath = Matrix.Translation((0.25, -0.66, 0.66 + 0.2)) @ Matrix.Rotation(-1.25, 4, 'X')
    path = [v(0.2 * math.cos(tau * k / 20), 0.2 * math.sin(tau * k / 20), 0.0) for k in range(20)]
    body.add(g.sweep(path, g.circle(0.035, 6), closed=True, planar=Z), "wreath_leaf", wreath)
    for k in range(16):
        angle = tau * k / 16 + rng.uniform(-0.1, 0.1)
        body.add(vk.cylinder(0.028, 0.012, 7), "poppy", wreath @ vk.frame(v(0.2 * math.cos(angle), 0.2 * math.sin(angle), 0.025), Z))
    leaf_litter(body, rng, v(0.0, -1.0, 0.0), 0.6, 20)
    leaf_litter(body, rng, v(-0.5, -0.7, 0.665), 0.15, 8, 0.0)
    far = m.far("prop_war_memorial_far")
    for width, z0, z1 in ((2.6, -0.04, 0.22), (2.1, 0.22, 0.44), (1.6, 0.44, 0.66)):
        far.add(vk.block(v(-width * 0.5, -width * 0.5, z0), v(width * 0.5, width * 0.5, z1)), "steel")
    far.add(vk.block(v(-0.6, -0.6, 0.66), v(0.6, 0.6, 0.86)), "steel")
    far.add(vk.block(v(-half, -half, 0.86), v(half, half, 2.05)), "steel")
    far.add(vk.block(v(-0.56, -0.56, 2.05), v(0.56, 0.56, 2.21)), "steel")
    far_shaft = bmesh.new()
    low = [far_shaft.verts.new((x * 0.31, y * 0.31, 2.21)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    high = [far_shaft.verts.new((x * 0.2, y * 0.2, 5.3)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    apex = far_shaft.verts.new((0.0, 0.0, 5.72))
    for i in range(4):
        j = (i + 1) % 4
        far_shaft.faces.new((low[i], low[j], high[j], high[i]))
        far_shaft.faces.new((high[i], high[j], apex))
    bmesh.ops.recalc_face_normals(far_shaft, faces=far_shaft.faces)
    far.add(far_shaft, "steel")
    m.col("rock", (-1.3, -1.3, 0.0), (1.3, 1.3, 0.22))
    m.col("rock", (-1.05, -1.05, 0.22), (1.05, 1.05, 0.44))
    m.col("rock", (-0.8, -0.8, 0.44), (0.8, 0.8, 0.66))
    m.col("rock", (-0.6, -0.6, 0.66), (0.6, 0.6, 2.21))
    m.col("rock", (-0.31, -0.31, 2.21), (0.31, 0.31, 5.72))
    m.close(v(0.9, -2.2, 1.7), v(0.0, -0.5, 1.4), 35.0)
    m.close(v(0.35, -1.05, 1.6), v(0.0, -0.48, 1.45), 40.0)
    m.close(v(-1.5, -2.6, 5.0), v(0.0, 0.0, 4.2), 35.0)
    m.info = {"kind": "point", "front": "-Y (main inscription)", "footprint": [2.6, 2.6]}
    return m


def horse_trough():
    m = model("prop_horse_trough", 111)
    body = m.part("prop_horse_trough", 35.0)
    rng = m.rng
    vk.text_mask("trough", 7.0, [("ST BRELADE 1894", 0.52, 0.5, "timesbd.ttf", 3.5, 6.0, 1.0, 1.25)])
    vk.register("trough_granite", "stone", kind="library", library="granite_ashlar", tint=(0.8, 0.82, 0.84), tile_scale=0.8, lichen=0.6, moss=0.45, dirt=0.5, streaks=0.4, tooled=0.25, text=("trough", (0.04, 0.04, 0.035), -4.0))
    outer = vk.slab(vk.rounded(2.2, 0.72, 0.09, 3), 0.74)
    vk.bevelled(outer, 0.025, 1, 30.0)
    g.shifted(outer, 0.0, 0.0, 0.32)
    basin = g.shifted(vk.slab(vk.rounded(1.96, 0.5, 0.08, 3), 0.6), 0.0, 0.0, 0.69)
    chip = g.shifted(vk.lump(0.16, 0.12, 0.1, rng, 0.35, 2), 1.08, -0.36, 0.69)
    body.add(g.cut(outer, [basin, chip]), "trough_granite", None, label=vk.label(v(0.0, -0.361, 0.42), X, Z, 1.4, 0.2, 0.8))
    body.add(vk.slab(vk.rounded(1.95, 0.49, 0.075, 3), 0.01), "water", Matrix.Translation((0.0, 0.0, 0.56)))
    leaf_litter(body, rng, v(0.2, 0.0, 0.566), 0.25, 14, 0.0)
    for x in (-0.6, 0.6):
        body.add(vk.block(v(x - 0.3, -0.38, -0.06), v(x + 0.3, 0.38, 0.0)), "trough_granite", None, 0.01)
    leaf_litter(body, rng, v(-0.4, -0.7, 0.0), 0.5, 16)
    far = m.far("prop_horse_trough_far")
    far.add(vk.block(v(-1.1, -0.36, -0.05), v(1.1, 0.36, 0.69)), "steel")
    m.col("rock", (-1.1, -0.36, 0.0), (1.1, 0.36, 0.69))
    m.close(v(0.8, -1.4, 1.2), v(0.2, 0.0, 0.5), 40.0)
    m.close(v(-0.2, -1.0, 0.7), v(-0.1, -0.36, 0.42), 45.0)
    m.info = {"kind": "point", "front": "-Y (inscription)", "footprint": [2.2, 0.72]}
    return m


def garden_wall():
    m = model("prop_garden_wall", 121)
    body = m.part("prop_garden_wall", 30.0)
    m.library_parts = ["prop_garden_wall"]
    rng = m.rng
    half = 2.0
    top = 0.97
    body.add(vk.block(v(-half, -0.2, -0.06), v(half, 0.2, top)), "lib_concrete", None)
    for side in (-1.0, 1.0):
        z = -0.06
        while z < top - 0.06:
            course = min(rng.uniform(0.17, 0.3), top - z)
            x = -half
            first = True
            while x < half - 0.02:
                length = rng.uniform(0.18, 0.48) * (rng.uniform(0.4, 1.0) if first else 1.0)
                first = False
                x1 = min(x + length, half)
                gap = rng.uniform(0.018, 0.035)
                sx = x1 - x - (0.0 if x1 >= half - 1e-6 else gap)
                sz = course - gap - rng.uniform(0.0, course * 0.25)
                depth = rng.uniform(0.11, 0.16)
                bulge = rng.uniform(0.005, 0.025)
                lift = rng.uniform(0.0, course - gap - sz)
                tone = rng.uniform(0.65, 1.3)
                hue = (tone * rng.uniform(0.95, 1.12), tone, tone * rng.uniform(0.88, 1.02))
                stone = vk.rubble(sx, depth, sz, rng)
                if side > 0.0:
                    bmesh.ops.transform(stone, matrix=Matrix.Rotation(math.pi, 4, 'Z'), verts=stone.verts)
                body.add(stone, "lib_granite_ashlar", Matrix.Translation((x + sx * 0.5, side * (0.2 + bulge - depth * 0.5), z + gap * 0.5 + lift + sz * 0.5)) @ Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, 'Y'), tint=hue)
                if course - gap - sz > 0.07 and rng.random() < 0.7:
                    pin = vk.rubble(min(sx * 0.6, 0.18), depth * 0.7, (course - gap - sz) * 0.7, rng, 0.25, 0.012)
                    if side > 0.0:
                        bmesh.ops.transform(pin, matrix=Matrix.Rotation(math.pi, 4, 'Z'), verts=pin.verts)
                    body.add(pin, "lib_granite_ashlar", Matrix.Translation((x + sx * rng.uniform(0.3, 0.7), side * (0.2 + bulge * 0.5 - depth * 0.35), z + gap * 0.5 + (lift + sz + (course - gap)) * 0.5 if lift < (course - gap - sz) * 0.5 else z + gap * 0.5 + lift * 0.5)), tint=(tone * 0.9,) * 3)
                x = x1
            z += course
    x = -half
    while x < half - 0.02:
        length = min(rng.uniform(0.45, 0.62), half - x)
        outline = [(-0.235, 0.0), (0.235, 0.0)] + [(0.235 * math.cos(a), 0.13 * math.sin(a)) for a in [math.pi * k / 10 for k in range(1, 10)]]
        coping = vk.prism(outline, -length * 0.5 + 0.004, length * 0.5 - 0.004)
        bmesh.ops.transform(coping, matrix=Matrix.Rotation(math.pi * 0.5, 4, 'Z'), verts=coping.verts)
        tone = rng.uniform(0.75, 1.2)
        body.add(coping, "lib_granite_ashlar", Matrix.Translation((x + length * 0.5, 0.0, top)) @ Matrix.Rotation(rng.uniform(-0.01, 0.01), 4, 'X'), tint=(tone, tone, tone))
        x += length
    far = m.far("prop_garden_wall_far")
    far.add(vk.block(v(-half, -0.23, -0.04), v(half, 0.23, top)), "lib_granite_rubble")
    far.add(vk.prism([(-0.235, 0.0), (0.235, 0.0), (0.17, 0.09), (0.0, 0.13), (-0.17, 0.09)], -half, half), "lib_granite_ashlar", Matrix.Translation((0.0, 0.0, top)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Z'))
    m.col("rock", (-half, -0.24, 0.0), (half, 0.24, top + 0.13))
    m.close(v(0.6, -1.6, 1.3), v(-0.2, 0.0, 0.6), 40.0)
    m.close(v(-1.4, -0.9, 1.4), v(-1.9, 0.0, 0.95), 45.0)
    m.info = {"kind": "tile", "tile_axis": "X", "tile_length": 4.0, "height": 1.1, "front": "both faces dressed"}
    return m


def railing():
    m = model("prop_railing", 131)
    body = m.part("prop_railing", 40.0)
    kerb = m.part("prop_railing_kerb", 30.0)
    m.library_parts = ["prop_railing_kerb"]
    rng = m.rng
    half = 1.5
    x = -half
    while x < half - 0.01:
        length = min(rng.uniform(0.9, 1.1), half - x)
        kerb.add(vk.block(v(x + 0.003, -0.13, -0.08), v(x + length - 0.003, 0.13, 0.14)), "lib_granite_ashlar", None, 0.015, 1)
        x += length
    rail_low = 0.24
    rail_high = 1.05
    body.add(vk.block(v(-half, -0.012, rail_low - 0.02), v(half, 0.012, rail_low + 0.02)), "iron_black", None, 0.003)
    body.add(vk.block(v(-half, -0.016, rail_high - 0.025), v(half, 0.016, rail_high + 0.025)), "iron_black", None, 0.003)
    for index in range(25):
        x = -half + 0.12 * (index + 0.5)
        if index == 13:
            body.add(vk.cylinder(0.009, 0.05, 8), "iron_black", vk.frame(v(x, 0.0, rail_high + 0.025), Z))
            body.add(vk.cylinder(0.009, 0.07, 8), "iron_black", vk.frame(v(x, 0.0, 0.14), Z))
            continue
        bend = 0.0
        if index in (6, 7):
            bend = 0.07 if index == 6 else 0.05
        path = [v(x, 0.0, 0.1), v(x, -bend * 0.4, 0.4), v(x + bend * 0.3, -bend, 0.62), v(x, -bend * 0.3, 0.85), v(x, 0.0, rail_high + 0.02), v(x, 0.0, 1.13)]
        body.add(vk.tube(g.spline(path, 4) if bend else [v(x, 0.0, 0.1), v(x, 0.0, 1.13)], 0.009, 8), "iron_black")
        if index != 19:
            body.add(vk.lathe([(0.0, 0.0), (0.011, 0.0), (0.02, 0.025), (0.016, 0.04), (0.006, 0.07), (0.0, 0.085)], 8), "iron_black", Matrix.Translation((x, 0.0, 1.12)))
            body.add(vk.lathe([(0.012, 0.0), (0.016, 0.006), (0.012, 0.012)], 8, closed=False), "iron_black", Matrix.Translation((x, 0.0, rail_low - 0.026)))
    post = v(-half, 0.0, 0.0)
    body.add(vk.block(post + v(-0.022, -0.022, 0.1), post + v(0.022, 0.022, 1.22)), "iron_black", None, 0.004)
    body.add(vk.lathe([(0.0, 0.0), (0.03, 0.0), (0.03, 0.02), (0.018, 0.04), (0.03, 0.07), (0.022, 0.1), (0.0, 0.11)], 10), "iron_black", Matrix.Translation(post + v(0.0, 0.0, 1.22)))
    body.add(vk.bar(post + v(0.0, 0.02, 0.85), post + v(0.0, 0.55, 0.0), 0.02, 0.02), "iron_black", None, 0.003)
    body.add(vk.block(post + v(-0.05, -0.05, 0.1), post + v(0.05, 0.05, 0.16)), "iron_black", None, 0.005)
    leaf_litter(body, rng, v(0.4, 0.0, 0.142), 0.12, 10, 0.0)
    far = m.far("prop_railing_far")
    far_kerb = m.far("prop_railing_far_kerb", 30.0)
    m.library_parts.append("prop_railing_far_kerb")
    far_kerb.add(vk.block(v(-half, -0.13, -0.04), v(half, 0.13, 0.14)), "lib_granite_ashlar")
    for z, h in ((rail_low, 0.04), (rail_high, 0.05)):
        far.add(vk.block(v(-half, -0.014, z - h * 0.5), v(half, 0.014, z + h * 0.5)), "steel")
    for index in range(25):
        if index == 13:
            continue
        x = -half + 0.12 * (index + 0.5)
        far.add(vk.cube(0.018, 0.018, 1.06), "steel", Matrix.Translation((x, 0.0, 0.67)))
    far.add(vk.block(post + v(-0.022, -0.022, 0.1), post + v(0.022, 0.022, 1.3)), "steel")
    m.col("rock", (-half, -0.13, 0.0), (half, 0.13, 0.14))
    m.col("metal", (-half, -0.04, 0.14), (half, 0.04, 1.2))
    m.close(v(0.4, -1.3, 1.25), v(-0.3, 0.0, 0.8), 40.0)
    m.close(v(-1.0, -0.8, 1.4), v(-1.45, 0.0, 1.1), 45.0)
    m.info = {"kind": "tile", "tile_axis": "X", "tile_length": 3.0, "height": 1.33, "post": "single standard at x = -1.5; tile at 3.0 m pitch"}
    return m


def picket_fence():
    m = model("prop_picket_fence", 141)
    body = m.part("prop_picket_fence", 40.0)
    rng = m.rng
    half = 1.5
    post = v(-half, 0.03, 0.0)
    body.add(vk.block(post + v(-0.04, -0.04, -0.08), post + v(0.04, 0.04, 1.1)), "pine_white", None, 0.005)
    body.add(vk.lathe([(0.0, 0.0), (0.06, 0.0), (0.0, 0.07)], 4, math.pi * 0.25), "pine_white", Matrix.Translation(post + v(0.0, 0.0, 1.1)))
    for z in (0.26, 0.78):
        body.add(vk.block(v(-half, 0.018, z - 0.035), v(half, 0.043, z + 0.035)), "pine_white", None, 0.003, tint=(rng.uniform(0.9, 1.05),) * 3)
    for index in range(1, 25):
        x = -half + 0.12 * (index + 0.5) - 0.06
        if index in (9, 17):
            continue
        height = rng.uniform(0.94, 0.99)
        if index == 12:
            height = 0.55
        outline = [(-0.035, 0.0), (0.035, 0.0), (0.035, height - 0.05), (0.0, height), (-0.035, height - 0.05)]
        if index == 12:
            outline = [(-0.035, 0.0), (0.035, 0.0), (0.035, height + 0.03), (0.01, height - 0.02), (-0.012, height + 0.05), (-0.035, height)]
        lean = 0.0
        if index in (4, 5):
            lean = 0.08 if index == 4 else 0.05
        matrix = Matrix.Translation((x, 0.0, 0.03)) @ Matrix.Rotation(lean, 4, 'Y') @ Matrix.Rotation(math.pi * 0.5, 4, 'X')
        body.add(vk.slab(outline, 0.018), "pine_white", matrix, 0.002, tint=(rng.uniform(0.88, 1.08), rng.uniform(0.9, 1.05), rng.uniform(0.88, 1.05)))
        for z in (0.26, 0.78):
            if z > height:
                continue
            vk.rivet(body, v(x + math.sin(lean) * z, -0.009, z + 0.03), v(0.0, -1.0, 0.0), 0.005, "iron")
    body.add(vk.slab([(-0.035, 0.0), (0.035, 0.0), (0.035, 0.9), (0.0, 0.95), (-0.035, 0.9)], 0.018), "pine_white", vk.at(v(0.1, -0.5, 0.01), 1.2))
    leaf_litter(body, rng, v(0.2, -0.25, 0.0), 0.8, 16)
    far = m.far("prop_picket_fence_far")
    for z in (0.26, 0.78):
        far.add(vk.block(v(-half, 0.018, z - 0.035), v(half, 0.043, z + 0.035)), "steel")
    for index in range(1, 25):
        if index in (9, 17):
            continue
        x = -half + 0.12 * index
        top = 0.58 if index == 12 else 0.97
        far.add(vk.slab([(-0.035, 0.0), (0.035, 0.0), (0.035, top - 0.05), (0.0, top), (-0.035, top - 0.05)], 0.018), "steel", Matrix.Translation((x, 0.0, 0.03)) @ Matrix.Rotation(math.pi * 0.5, 4, 'X'))
    far.add(vk.block(post + v(-0.04, -0.04, 0.0), post + v(0.04, 0.04, 1.15)), "steel")
    m.col("wood", (-half, -0.03, 0.0), (half, 0.07, 1.0))
    m.close(v(0.3, -1.2, 1.2), v(-0.2, 0.0, 0.6), 40.0)
    m.info = {"kind": "tile", "tile_axis": "X", "tile_length": 3.0, "height": 1.17, "post": "single post at x = -1.5; tile at 3.0 m pitch", "front": "-Y (pickets), rails on +Y"}
    return m


def traffic_cone():
    m = model("prop_traffic_cone", 151)
    body = m.part("prop_traffic_cone", 40.0)
    rng = m.rng
    vk.register("reflective", "plastic", color=(0.42, 0.42, 0.4), fade=0.2, gloss=0.35, dirt=0.7)
    vk.register("cone_black", "plastic", color=(0.02, 0.02, 0.02), fade=0.4, gloss=0.6, dirt=0.7)
    base = vk.slab(vk.rounded(0.38, 0.38, 0.06, 4), 0.035, [list(reversed([(0.16 * math.cos(tau * k / 24), 0.16 * math.sin(tau * k / 24)) for k in range(24)]))])
    body.add(base, "cone_black", Matrix.Translation((0.0, 0.0, 0.0175)), 0.006)
    def radius(z):
        return 0.15 - (z - 0.08) / 0.64 * 0.11

    segments = [([(0.165, 0.0), (0.16, 0.035), (0.15, 0.08), (radius(0.3), 0.3)], "cone_orange"), ([(radius(0.3), 0.3), (radius(0.36), 0.36), (radius(0.42), 0.42)], "reflective"), ([(radius(0.42), 0.42), (radius(0.5), 0.5)], "cone_orange"), ([(radius(0.5), 0.5), (radius(0.56), 0.56)], "reflective"), ([(radius(0.56), 0.56), (0.04, 0.72), (0.03, 0.745), (0.0, 0.75)], "cone_orange")]
    for profile, look in segments:
        body.add(vk.lathe(profile, 28, 0.0, False), look)
    far = m.far("prop_traffic_cone_far")
    far.add(vk.block(v(-0.19, -0.19, 0.0), v(0.19, 0.19, 0.035)), "steel")
    far.add(vk.lathe([(0.0, 0.0), (0.16, 0.0), (0.035, 0.75), (0.0, 0.75)], 8), "steel")
    m.col("fabric", (-0.19, -0.19, 0.0), (0.19, 0.19, 0.75))
    m.close(v(0.45, -0.75, 0.75), v(0.0, 0.0, 0.4), 45.0)
    m.info = {"kind": "point", "footprint": [0.38, 0.38]}
    return m


def sandbags():
    m = model("prop_sandbags", 161)
    body = m.part("prop_sandbags", 40.0)
    rng = m.rng
    vk.register("sandbag", "fabric", kind="hessian", tint=(0.5, 0.42, 0.3), weave=11.0, stains=0.8, mildew=0.55, dirt=0.75, moss=0.3)
    vk.register("sand", "organic", kind="paper", tint=(0.2, 0.16, 0.11), dirt=0.5)
    half = 1.5
    courses = [(0.0, 2, 0.0), (0.13, 2, 0.5), (0.26, 2, 0.0), (0.39, 1, 0.5), (0.52, 1, 0.0), (0.65, 1, 0.5), (0.78, 1, 0.0)]
    length = 0.6
    for level, (z, rows, offset) in enumerate(courses):
        ys = [-0.17, 0.17] if rows == 2 else [rng.uniform(-0.03, 0.03)]
        for y in ys:
            x = -half + offset * length * 0.5 + length * 0.5 - (length * 0.5 if offset else 0.0)
            count = 0
            while x - length * 0.5 < half - 0.12:
                cx = min(x, half - length * 0.5 + 0.02)
                squash = 0.15 if level < 6 else 0.17
                bag = vk.pillow(length - 0.02, 0.34, squash, rng, rng.uniform(0.26, 0.38), 0.015, 0.14, 16, 9)
                twist = rng.uniform(-0.04, 0.04)
                slump = rng.uniform(0.0, 0.03)
                for vert in bag.verts:
                    vert.co.y += twist * vert.co.x
                    vert.co.z -= slump * (1.0 - (2.0 * vert.co.x / length) ** 2) * (0.5 + vert.co.z / squash)
                    vert.co.y += 0.012 * math.sin(vert.co.x * 23.0 + level) * (0.5 + vert.co.z / squash)
                burst = level == 6 and count == 2
                if burst:
                    for vert in bag.verts:
                        if vert.co.z > 0.0:
                            vert.co.z -= 0.022 * max(0.0, 1.0 - abs(vert.co.x) / 0.25) * (vert.co.z / (squash * 0.5))
                tone = rng.uniform(0.8, 1.15)
                body.add(bag, "sandbag", Matrix.Translation((cx + rng.uniform(-0.02, 0.02), y + rng.uniform(-0.02, 0.02), z + squash * 0.5)) @ Matrix.Rotation(rng.uniform(-0.05, 0.05), 4, 'Z') @ Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, 'X'), tint=(tone, tone * rng.uniform(0.95, 1.02), tone * rng.uniform(0.9, 1.0)))
                neck = v(cx + length * 0.5 - 0.025, y, z + squash * 0.5)
                body.add(vk.lathe([(0.0, -0.035), (0.03, -0.03), (0.018, 0.0), (0.028, 0.03), (0.0, 0.045)], 7), "sandbag", vk.frame(neck, X) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
                if burst:
                    body.add(vk.lump(0.28, 0.34, 0.1, rng, 0.2, 2, 0.0), "sand", Matrix.Translation((cx + 0.1, -0.45, 0.0)))
                    body.add(vk.lump(0.12, 0.08, 0.04, rng, 0.2, 2), "sand", Matrix.Translation((cx, y, z + squash * 0.8)))
                x += length
                count += 1
    m.loot("military", v(0.4, 0.62, 0.0))
    leaf_litter(body, rng, v(0.0, -0.5, 0.0), 0.8, 14)
    far = m.far("prop_sandbags_far")
    far.add(vk.prism([(-0.36, 0.0), (0.36, 0.0), (0.3, 0.39), (0.2, 0.39), (0.18, 0.93), (-0.18, 0.93), (-0.2, 0.39), (-0.3, 0.39)], -half, half), "steel", Matrix.Rotation(math.pi * 0.5, 4, 'Z'))
    m.col("fabric", (-half, -0.36, 0.0), (half, 0.36, 0.39))
    m.col("fabric", (-half, -0.2, 0.39), (half, 0.2, 0.95))
    m.close(v(0.8, -1.5, 1.2), v(0.2, 0.0, 0.5), 40.0)
    m.close(v(-0.2, -0.9, 1.1), v(0.0, 0.0, 0.85), 45.0)
    m.info = {"kind": "tile", "tile_axis": "X", "tile_length": 3.0, "height": 0.95, "front": "-Y (enemy side); loot behind on +Y"}
    return m


car_specs = {
    "hatch": {
        "seed": 171, "length": 3.73, "axles": (-1.2, 1.2), "tyre": 0.285, "rim": 0.165, "tyre_width": 0.165, "track": 0.69, "sink": 0.055,
        "exponent": 5.0, "egg": 0.07, "belt": 0.92, "roof": 1.37, "w_belt": 0.785, "w_roof": 0.625,
        "stations": [(-1.865, 0.34, 0.75, 0.75), (-1.845, 0.3, 0.785, 0.775), (-1.76, 0.25, 0.805, 0.79), (-1.5, 0.23, 0.82, 0.8), (-1.0, 0.21, 0.86, 0.805), (-0.6, 0.2, 0.9, 0.805), (0.0, 0.2, 0.92, 0.805), (0.6, 0.2, 0.93, 0.805), (1.2, 0.22, 0.94, 0.8), (1.6, 0.25, 0.94, 0.787), (1.79, 0.3, 0.93, 0.765), (1.865, 0.38, 0.9, 0.74)],
        "a": (-0.6, -0.08), "pillars": [(0.44, 0.42)], "c": (1.2, 1.12), "roof_y": (-0.08, 1.3), "rear": "hatch", "tail": (1.77, 0.98),
        "doors": [(-0.56, 0.44)], "open": (1.0, 0, 1.05), "dash": -0.52, "front_seat": -0.05, "rear_seat": 0.62, "cabin_end": 1.62, "floor": 0.3,
        "paint": ("car_blue", (0.06, 0.12, 0.21)), "odd": None, "plate": "J 48213", "headlights": "round", "loot": ("box", (0.15, 0.62, 0.45)),
    },
    "saloon": {
        "seed": 181, "length": 4.45, "axles": (-1.37, 1.21), "tyre": 0.3, "rim": 0.178, "tyre_width": 0.175, "track": 0.71, "sink": 0.06,
        "exponent": 5.5, "egg": 0.06, "belt": 0.9, "roof": 1.38, "w_belt": 0.835, "w_roof": 0.655,
        "stations": [(-2.225, 0.34, 0.77, 0.8), (-2.205, 0.3, 0.8, 0.83), (-2.1, 0.25, 0.815, 0.845), (-1.7, 0.23, 0.81, 0.85), (-1.0, 0.21, 0.85, 0.85), (-0.7, 0.2, 0.88, 0.85), (0.0, 0.2, 0.9, 0.85), (0.8, 0.2, 0.91, 0.85), (1.4, 0.22, 0.92, 0.85), (1.9, 0.25, 0.92, 0.84), (2.15, 0.3, 0.9, 0.82), (2.225, 0.38, 0.86, 0.79)],
        "a": (-0.72, -0.2), "pillars": [(0.25, 0.22)], "c": (1.36, 0.86), "roof_y": (-0.2, 0.88), "rear": "saloon", "tail": (2.2, 0.9),
        "doors": [(-0.68, 0.24), (0.26, 1.12)], "open": (-1.0, 1, 1.15), "dash": -0.62, "front_seat": -0.12, "rear_seat": 0.72, "cabin_end": 1.1, "floor": 0.3,
        "paint": ("car_beige", (0.26, 0.19, 0.1)), "odd": ("primer_door", 0), "plate": "J 27694", "headlights": "square", "loot": ("box", (-0.2, 0.74, 0.45)),
    },
    "van": {
        "seed": 191, "length": 4.6, "axles": (-1.55, 1.14), "tyre": 0.315, "rim": 0.18, "tyre_width": 0.185, "track": 0.82, "sink": 0.06,
        "exponent": 7.0, "egg": 0.03, "belt": 1.15, "roof": 2.02, "w_belt": 0.97, "w_roof": 0.95,
        "stations": [(-2.3, 0.42, 0.88, 0.9), (-2.27, 0.36, 0.95, 0.93), (-2.15, 0.33, 0.99, 0.95), (-1.7, 0.32, 1.04, 0.97), (-1.28, 0.32, 1.12, 0.975), (-1.1, 0.32, 1.45, 0.975), (-0.9, 0.32, 1.85, 0.975), (-0.72, 0.32, 2.0, 0.975), (0.0, 0.32, 2.02, 0.975), (1.6, 0.33, 2.02, 0.975), (2.2, 0.36, 2.0, 0.97), (2.3, 0.4, 1.98, 0.96)],
        "rear": "van", "doors": [(-1.25, -0.3)], "open": (1.0, None, 0.0), "dash": -1.15, "front_seat": -0.62, "cabin_end": 2.24, "floor": 0.45,
        "paint": ("van_white", (0.4, 0.4, 0.37)), "odd": None, "plate": "J 9152", "headlights": "round_van", "loot": ("toolbox", (0.3, 1.7, 0.5)),
    },
}


def car_mask(spec, key, kind, widest):
    length = spec["length"]
    half = length * 0.5
    side_height = spec["roof"] + 0.1
    size = 2048
    cells = {1.0: (0.0, 0.32), -1.0: (0.34, 0.66)}
    strokes = []
    triangles = []

    def side_uv(side, y, z):
        v0, v1 = cells[side]
        u = (y + half) / length if side > 0 else (half - y) / length
        return (u, v0 + (z / side_height) * (v1 - v0))

    def top_uv(y, x):
        return ((y + half) / length, 0.68 + (x + widest) / (2.0 * widest) * 0.32)

    stroke = 0.0011
    front_y = spec["stations"][0][0]
    for side in (-1.0, 1.0):
        for y0, y1 in spec["doors"]:
            top_z = spec["belt"] if kind != "van" else spec["belt"] + 0.7
            strokes.append(([side_uv(side, y0, 0.27), side_uv(side, y0, top_z)], stroke))
            strokes.append(([side_uv(side, y1, 0.27), side_uv(side, y1, top_z)], stroke))
            strokes.append(([side_uv(side, y0, 0.27), side_uv(side, y1, 0.27)], stroke))
            if kind == "van":
                strokes.append(([side_uv(side, y0, top_z), side_uv(side, y1, top_z)], stroke))
            handle_y = y1 - 0.13
            strokes.append(([side_uv(side, handle_y - 0.05, spec["belt"] - 0.07), side_uv(side, handle_y + 0.05, spec["belt"] - 0.07)], stroke * 5.0))
        if kind != "van":
            bonnet_end = spec["a"][0] - 0.05
            strokes.append(([side_uv(side, bonnet_end, spec["belt"] - 0.03), side_uv(side, front_y + 0.05, section_at(spec, front_y + 0.05)[1] - 0.04)], stroke))
        else:
            strokes.append(([side_uv(side, -0.05, 0.36), side_uv(side, -0.05, 1.9), side_uv(side, 1.0, 1.9), side_uv(side, 1.0, 0.36), side_uv(side, -0.05, 0.36)], stroke))
            strokes.append(([side_uv(side, -0.05, 1.02), side_uv(side, 1.0, 1.02)], stroke * 0.7))
        fuel = (half * 0.62, spec["belt"] - 0.13)
        if side > 0:
            strokes.append(([side_uv(side, fuel[0] + 0.045 * math.cos(tau * k / 16), fuel[1] + 0.045 * math.sin(tau * k / 16)) for k in range(17)], stroke))
    if kind != "van":
        bonnet_end = spec["a"][0] - 0.05
        strokes.append(([top_uv(bonnet_end, -widest * 0.9), top_uv(bonnet_end, widest * 0.9)], stroke))
        for side in (-1.0, 1.0):
            strokes.append(([top_uv(bonnet_end, side * widest * 0.9), top_uv(front_y + 0.04, side * widest * 0.88)], stroke))
    else:
        strokes.append(([top_uv(-1.3, -widest * 0.85), top_uv(-1.3, widest * 0.85)], stroke))
    if spec["rear"] == "saloon":
        boot = spec["c"][0] + 0.05
        strokes.append(([top_uv(boot, -widest * 0.88), top_uv(boot, widest * 0.88)], stroke))
        for side in (-1.0, 1.0):
            strokes.append(([top_uv(boot, side * widest * 0.88), top_uv(half - 0.03, side * widest * 0.85)], stroke))
    if spec["rear"] == "hatch":
        strokes.append(([top_uv(spec["roof_y"][1] + 0.02, -0.6), top_uv(spec["roof_y"][1] + 0.02, 0.6)], stroke))
    if kind == "van":
        for side in (-1.0, 1.0):
            v0, v1 = cells[side]
            for text, height, y, z in (("LE BRUN & SONS", 0.15, 0.5, 1.62), ("BUILDERS  -  ST AUBIN", 0.075, 0.5, 1.42), ("TEL  41290", 0.07, 0.5, 1.26)):
                u, w = side_uv(side, y, z)
                triangles.extend(vk.text_in_cell(text, "GILB____.TTF", height, (u * size, w * size), 2.4, size / length, size * (v1 - v0) / side_height))
    extra = vk.rasterize(triangles, size, size, 2) * 0.8 if triangles else None
    vk.line_mask(key + "_seams", size, strokes, (), extra)
    labels = [vk.atlas_label(v(0.0, 0.0, spec["roof"] * 0.5), Y, X, length, 2.0 * widest, (0.0, 1.0, 0.68, 1.0), 0.6, Z), vk.atlas_label(v(widest, 0.0, side_height * 0.5), Y, Z, length, side_height, (0.0, 1.0) + cells[1.0], 0.3, X), vk.atlas_label(v(-widest, 0.0, side_height * 0.5), -Y, Z, length, side_height, (0.0, 1.0) + cells[-1.0], 0.3, -X)]
    return labels


def car_looks(spec, key):
    name, color = spec["paint"]
    produce_looks()
    vk.register("tyre", "rubber", perished=0.75, dirt=0.8)
    vk.register("trim_black", "plastic", color=(0.025, 0.025, 0.025), fade=0.6, gloss=0.55, dirt=0.75)
    vk.register("lens_red", "plastic", color=(0.22, 0.015, 0.012), fade=0.3, gloss=0.2, dirt=0.65)
    vk.register("lens_amber", "plastic", color=(0.42, 0.15, 0.02), fade=0.4, gloss=0.2, dirt=0.65)
    vk.register("lens_clear", "glass", cracked=0.5, tint=(0.05, 0.055, 0.055))
    vk.register("seat_vinyl", "fabric", kind="vinyl", tint=(0.06, 0.04, 0.03), dirt=0.6, moss=0.35)
    vk.register("carpet", "fabric", kind="canvas", tint=(0.06, 0.05, 0.04), weave=20.0, dirt=0.8, moss=0.4)
    vk.register("dash", "plastic", color=(0.03, 0.03, 0.03), fade=0.5, gloss=0.6, dirt=0.75, moss=0.25)
    vk.register("trim_dark", "paint", color=(0.05, 0.05, 0.048), under=(0.12, 0.05, 0.03), primer=(0.12, 0.05, 0.03), chips=0.6, rot=1.0, bleed=0.6, gloss=0.7, dirt=0.8)
    vk.register("underbody", "metal", kind="rust", rust=1.0, dirt=0.8)
    vk.register("wheel_steel", "paint", color=(0.2, 0.2, 0.19), under=(0.12, 0.05, 0.03), primer=(0.12, 0.05, 0.03), chips=0.6, bleed=0.7, gloss=0.55, dirt=0.8, rot=0.8)
    vk.register("primer_door", "paint", color=(0.12, 0.12, 0.115), under=(0.1, 0.04, 0.03), primer=(0.1, 0.04, 0.03), chips=0.45, fade=0.2, chalk=0.0, bleed=0.6, streaks=0.5, gloss=0.85, dirt=0.75, rot=0.9, text=(key + "_seams", (0.02, 0.02, 0.02), -3.0))
    vk.register(name, "paint", color=color, under=(0.13, 0.13, 0.125), primer=(0.12, 0.05, 0.03), chips=0.45, fade=0.6, chalk=0.42, bleed=0.55, streaks=0.65, gloss=0.6, dirt=0.75, moss=0.3, rot=1.0, rot_height=0.55, dents=0.6, text=(key + "_seams", (0.02, 0.02, 0.02), -3.0))
    vk.register("plate_" + key, "paint", color=(0.02, 0.02, 0.022), under=(0.3, 0.3, 0.3), primer=(0.12, 0.05, 0.03), chips=0.3, fade=0.3, chalk=0.2, gloss=0.5, dirt=0.6, text=("plate_" + key, (0.4, 0.4, 0.38), 2.0))
    return name


def section_at(spec, y):
    rows = spec["stations"]
    if y <= rows[0][0]:
        return rows[0][1:]
    for a, b in zip(rows[:-1], rows[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 4))
    return rows[-1][1:]


def body_x(spec, y, z):
    zb, zt, hw = section_at(spec, y)
    zc = (zb + zt) * 0.5
    hu = (zt - zb) * 0.5
    yn = max(min((z - zc) / hu, 0.999), -0.999)
    xn = (1.0 - abs(yn) ** spec["exponent"]) ** (1.0 / spec["exponent"])
    return xn * hw * (1.0 - spec["egg"] * yn)


def lower_body(spec, segments=36):
    stations = [(v(0.0, y, (zb + zt) * 0.5), hw, (zt - zb) * 0.5, 1.0, 1.0, spec["egg"]) for y, zb, zt, hw in spec["stations"]]
    return g.loft(stations, segments, spec["exponent"], Z)


def side_point(spec, side, y, z):
    t = (z - spec["belt"]) / (spec["roof"] - spec["belt"])
    return v(side * (spec["w_belt"] + (spec["w_roof"] - spec["w_belt"]) * t), y, z)


def car_wheel(target, spec, center, side, rng, cap=True):
    tyre = spec["tyre"]
    rim = spec["rim"]
    width = spec["tyre_width"]
    sink = spec["sink"]
    profile = [(rim + 0.004, -width * 0.44), (rim + 0.025, -width * 0.5), (tyre - 0.045, -width * 0.53), (tyre - 0.012, -width * 0.46), (tyre, -width * 0.3), (tyre + 0.002, 0.0), (tyre, width * 0.3), (tyre - 0.012, width * 0.46), (tyre - 0.045, width * 0.53), (rim + 0.025, width * 0.5), (rim + 0.004, width * 0.44)]
    shell = g.revolve(profile, 36)
    ground = -(tyre - sink)
    for vert in shell.verts:
        if vert.co.z < ground + 0.012:
            squeeze = (ground + 0.012 - vert.co.z)
            vert.co.z = ground + 0.012 - squeeze * 0.15
            vert.co.x *= 1.0 + squeeze * 2.2
        elif vert.co.z < ground + 0.12:
            closeness = 1.0 - (vert.co.z - ground - 0.012) / 0.108
            vert.co.x *= 1.0 + 0.09 * closeness * closeness
    spin = Matrix.Rotation(rng.uniform(0.0, tau), 4, 'X')
    turn = Matrix.Identity(4) if side > 0 else Matrix.Rotation(math.pi, 4, 'Z')
    place = Matrix.Translation(center) @ turn
    target.add(shell, "tyre", place)
    disc = g.revolve([(0.0, width * 0.3), (0.07, width * 0.3), (0.09, width * 0.22), (rim - 0.025, width * 0.18), (rim - 0.005, width * 0.32), (rim + 0.008, width * 0.42), (rim + 0.008, width * 0.46), (rim, width * 0.46), (rim - 0.008, width * 0.3), (rim - 0.008, -width * 0.42), (rim + 0.006, -width * 0.44), (rim + 0.006, -width * 0.47), (rim - 0.012, -width * 0.47), (rim - 0.02, -width * 0.3), (0.0, -width * 0.3)], 28)
    holes = []
    for k in range(6):
        angle = tau * k / 6
        holes.append(g.transformed(g.box(0.2, 0.026, 0.05), Matrix.Translation((width * 0.2, math.cos(angle) * (rim * 0.62), math.sin(angle) * (rim * 0.62))) @ Matrix.Rotation(angle, 4, 'X')))
    target.add(vk.carve(disc, holes), "wheel_steel", place @ spin)
    for k in range(4):
        angle = tau * k / 4
        target.add(g.hexagon(0.022, 0.014, "x"), "steel", place @ spin @ Matrix.Translation((width * 0.3 + 0.007, math.cos(angle) * 0.05, math.sin(angle) * 0.05)))
    if cap:
        target.add(g.revolve([(0.0, width * 0.43), (0.05, width * 0.43), (0.11, width * 0.4), (rim - 0.012, width * 0.36), (rim - 0.012, width * 0.3), (0.0, width * 0.3)], 28), "chrome", place)


def glass_panel(target, rng, points, state, inward=None):
    points = [Vector(p) for p in points]
    if state == "missing":
        return
    center = sum(points, Vector()) / len(points)
    normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
    shift = normal * 0.0 if inward is None else Vector(inward) * 0.012
    if state == "broken":
        for index in range(len(points)):
            a = points[index]
            b = points[(index + 1) % len(points)]
            if rng.random() < 0.55:
                continue
            for k in range(3):
                t0 = rng.uniform(0.0, 0.7)
                t1 = t0 + rng.uniform(0.1, 0.3)
                tip = a.lerp(b, (t0 + t1) * 0.5).lerp(center, rng.uniform(0.12, 0.35))
                shard = bmesh.new()
                verts = [shard.verts.new(a.lerp(b, t0) + shift), shard.verts.new(a.lerp(b, min(t1, 1.0)) + shift), shard.verts.new(tip + shift)]
                shard.faces.new(verts)
                vk.thicken(shard, 0.004)
                target.add(shard, "glass_cracked")
        return
    bm = bmesh.new()
    verts = [bm.verts.new(p + shift) for p in points]
    bm.faces.new(verts)
    vk.thicken(bm, 0.005)
    target.add(bm, "glass_cracked" if state == "cracked" else "glass")


def van_openings(spec):
    slope = math.atan2(2.0 - 1.12, -0.72 + 1.28)
    screen = g.transformed(g.box(1.62, 0.3, 0.84), Matrix.Translation((0.0, -1.0, 1.56)) @ Matrix.Rotation(-(math.pi * 0.5 - slope), 4, 'X'))
    result = [screen]
    for side in (-1.0, 1.0):
        result.append(vk.block(v(side * 0.86, -1.13, spec["belt"] + 0.04), v(side * 1.15, -0.38, 1.86)))
    return result


def side_slab(target, look, spec, side, points, thickness=0.04, label=None, matrix=None):
    bm = bmesh.new()
    outer = [bm.verts.new(side_point(spec, side, y, z)) for y, z in points]
    normal = v(side, 0.0, (spec["w_belt"] - spec["w_roof"]) / (spec["roof"] - spec["belt"])).normalized()
    inner = [bm.verts.new(vert.co - normal * thickness) for vert in outer]
    bm.faces.new(outer)
    bm.faces.new(list(reversed(inner)))
    count = len(points)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((outer[i], inner[i], inner[j], outer[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    target.add(bm, look, matrix, label=label)


def greenhouse(m, spec, shell, cabin, rng, paint, drop, labels, door_parts, open_side, open_index):
    belt = spec["belt"]
    roof = spec["roof"]
    a0, a1 = spec["a"]
    c0, c1 = spec["c"]
    r0, r1 = spec["roof_y"]
    pillars = spec["pillars"]
    for side in (-1.0, 1.0):
        shell.add(vk.bar(side_point(spec, side, a0, belt - 0.02), side_point(spec, side, a1, roof + 0.01), 0.075, 0.05, v(side, 0.0, 0.3)), paint, drop, 0.008, label=labels)
        for b0, b1 in pillars:
            shell.add(vk.bar(side_point(spec, side, b0, belt - 0.02), side_point(spec, side, b1, roof + 0.01), 0.075, 0.05, v(side, 0.0, 0.3)), paint, drop, 0.008, label=labels)
        if spec["rear"] == "hatch":
            tail_y, tail_z = spec["tail"]
            side_slab(shell, paint, spec, side, [(c0 - 0.04, belt - 0.01), (tail_y - 0.04, belt - 0.01), (tail_y - 0.01, tail_z), (r1 + 0.03, roof - 0.01), (c1, roof - 0.01)], 0.045, labels, drop)
        else:
            side_slab(shell, paint, spec, side, [(c0 - 0.14, belt - 0.01), (c0 + 0.06, belt - 0.01), (c1 + 0.04, roof - 0.01), (c1 - 0.08, roof - 0.01)], 0.045, labels, drop)
        gutter = [side_point(spec, side, a1 + 0.01, roof + 0.012), side_point(spec, side, r1 + 0.02, roof + 0.012)]
        shell.add(vk.bar(gutter[0], gutter[1], 0.022, 0.02), paint, drop, 0.004)
    def roof_lift(x, y):
        edge = min(1.0, (abs(x) / (spec["w_roof"] + 0.02)) ** 4 + 0.0)
        ends = min(1.0, max(0.0, (abs(y - (r0 + r1) * 0.5) - (r1 - r0) * 0.5 + 0.05) / 0.05))
        return 0.025 * (1.0 - edge) - 0.012 * ends
    sheet = vk.grid_sheet(2.0 * spec["w_roof"] + 0.04, r1 - r0 + 0.06, 10, 10, roof_lift)
    vk.thicken(sheet, 0.03)
    shell.add(sheet, paint, drop @ Matrix.Translation((0.0, (r0 + r1) * 0.5, roof + 0.012)), label=labels)
    screen = [v(-spec["w_belt"] + 0.08, a0 + 0.06, belt + 0.015), v(spec["w_belt"] - 0.08, a0 + 0.06, belt + 0.015), v(spec["w_roof"] - 0.05, a1 + 0.03, roof - 0.025), v(-spec["w_roof"] + 0.05, a1 + 0.03, roof - 0.025)]
    glass_panel(shell, rng, [drop @ p for p in screen], "cracked" if spec["rear"] == "saloon" else "broken")
    if spec["rear"] == "hatch":
        tail_y, tail_z = spec["tail"]
        rear = [v(-0.6, tail_y - 0.05, tail_z + 0.04), v(0.6, tail_y - 0.05, tail_z + 0.04), v(spec["w_roof"] - 0.07, r1 + 0.05, roof - 0.03), v(-spec["w_roof"] + 0.07, r1 + 0.05, roof - 0.03)]
        shell.add(vk.bar(v(-0.66, tail_y - 0.02, tail_z), v(0.66, tail_y - 0.02, tail_z), 0.06, 0.04), paint, drop, 0.006, label=labels)
    else:
        rear = [v(-spec["w_belt"] + 0.14, c0 - 0.04, belt + 0.02), v(spec["w_belt"] - 0.14, c0 - 0.04, belt + 0.02), v(spec["w_roof"] - 0.07, r1 + 0.02, roof - 0.03), v(-spec["w_roof"] + 0.07, r1 + 0.02, roof - 0.03)]
    glass_panel(shell, rng, [drop @ p for p in rear], window_state(rng, 0.3))
    edges = [a0] + [b for b, top in pillars] + [c0]
    tops = [a1] + [top for b, top in pillars] + [c1]
    for side in (-1.0, 1.0):
        for index in range(len(edges) - 1):
            y0 = edges[index] + (0.05 if index == 0 else 0.04)
            y1 = edges[index + 1] - (0.04 if index + 1 < len(edges) - 1 else (0.06 if spec["rear"] == "hatch" else 0.1))
            t0 = tops[index] + (0.04 if index == 0 else 0.04)
            t1 = tops[index + 1] - (0.04 if index + 1 < len(edges) - 1 else 0.02)
            corners = [side_point(spec, side, y0, belt + 0.025), side_point(spec, side, y1, belt + 0.025), side_point(spec, side, t1, roof - 0.035), side_point(spec, side, t0, roof - 0.035)]
            inward = v(-side, 0.0, 0.0)
            matrix = drop
            moving = door_parts is not None and side == open_side and index == open_index
            if moving:
                swing, door_y0, door_y1 = door_parts
                matrix = drop @ swing
                frame_points = corners + [corners[0]]
                for p, q in zip(frame_points[:-1], frame_points[1:]):
                    shell.add(vk.bar(p, q, 0.03, 0.03), paint, matrix, 0.004)
            state = window_state(rng, -0.1 if index == 0 else 0.1)
            glass_panel(shell, rng, [matrix @ p for p in corners], state, (matrix.to_3x3() @ inward))
            if state in ("missing", "broken") and not moving:
                shards(cabin, rng, drop @ v(side * 0.35, (y0 + y1) * 0.5, spec["floor"] + 0.1), 0.25, 8)
    for side in (-1.0, 1.0):
        y = a0 + 0.12
        base = side_point(spec, side, y, belt - 0.03)
        matrix = drop
        if door_parts is not None and side == open_side and open_index == 0:
            matrix = drop @ door_parts[0]
        if side < 0 or rng.random() < 0.5:
            shell.add(vk.bar(base, base + v(side * 0.1, 0.02, 0.06), 0.025, 0.02), "trim_black", matrix, 0.003)
            shell.add(vk.block(v(-0.06, -0.045, -0.04), v(0.06, 0.045, 0.04)), "trim_black", matrix @ Matrix.Translation(base + v(side * 0.15, 0.03, 0.08)), 0.012)
        else:
            shell.add(vk.bar(base, base + v(side * 0.05, 0.01, 0.03), 0.025, 0.02), "trim_black", matrix, 0.003)
    for x in (-0.32, 0.18):
        shell.add(vk.bar(v(x, a0 + 0.1, belt + 0.03), v(x + 0.35, a0 + 0.2, belt + 0.12), 0.012, 0.008), "trim_black", drop, 0.002)
    shell.add(vk.rod(v(0.55, a0 - 0.6, section_at(spec, a0 - 0.6)[1] - 0.01), v(0.62, a0 - 0.45, section_at(spec, a0 - 0.6)[1] + 0.75), 0.003, 5), "chrome", drop)


def van_body(m, spec, shell, cabin, rng, paint, drop, labels):
    belt = spec["belt"]
    slope = math.atan2(2.0 - 1.12, -0.72 + 1.28)
    screen = [v(-0.78, -1.21, 1.2), v(0.78, -1.21, 1.2), v(0.78, -0.8, 1.9), v(-0.78, -0.8, 1.9)]
    glass_panel(shell, rng, [drop @ p for p in screen], "broken")
    for side in (-1.0, 1.0):
        state = window_state(rng, 0.0)
        corners = [v(side * 0.955, -1.1, belt + 0.07), v(side * 0.955, -0.41, belt + 0.07), v(side * 0.955, -0.41, 1.83), v(side * 0.955, -1.1, 1.83)]
        glass_panel(shell, rng, [drop @ p for p in corners], state, v(-side, 0.0, 0.0))
        for z in (0.62, 1.32):
            shell.add(vk.block(v(side * 0.975, -0.04, z), v(side * 0.99, 1.02, z + 0.02)), "trim_black", drop, 0.004)
    half = spec["length"] * 0.5
    inner = 0.915
    hinge_left = v(-inner - 0.01, half, 0.0)
    hinge_right = v(inner + 0.01, half, 0.0)
    for side, hinge, angle in ((-1.0, hinge_left, 0.0), (1.0, hinge_right, -1.75)):
        swing = vk.about(hinge, Z, angle)
        door = vk.block(v(min(side * inner, 0.0) + (0.006 if side > 0 else 0.0), half - 0.045, spec["floor"] + 0.01), v(max(side * inner, 0.0) - (0.006 if side < 0 else 0.0), half + 0.01, 1.93))
        shell.add(door, paint, drop @ swing, 0.008, label=labels, chooser=lambda face: "trim_dark" if face.normal.y < -0.5 else None)
        window = [v(side * 0.12, half + 0.012, 1.25), v(side * 0.78, half + 0.012, 1.25), v(side * 0.78, half + 0.012, 1.8), v(side * 0.12, half + 0.012, 1.8)]
        glass_panel(shell, rng, [drop @ swing @ p for p in window], window_state(rng, 0.2))
        shell.add(vk.block(v(side * 0.86 - 0.04, half + 0.01, 0.62), v(side * 0.86 + 0.04, half + 0.035, 0.78)), "lens_red", drop @ swing, 0.008)
        shell.add(vk.block(v(side * 0.1 - 0.015, half + 0.01, 1.0), v(side * 0.1 + 0.015, half + 0.03, 1.1)), "chrome", drop @ swing, 0.004)
    rack_z = spec["roof"] + 0.12
    for x in (-0.82, 0.82):
        shell.add(vk.bar(v(x, -0.6, rack_z), v(x, 2.1, rack_z), 0.035, 0.035), "zinc", drop, 0.004)
    for y in (-0.5, 0.4, 1.3, 2.0):
        shell.add(vk.bar(v(-0.86, y, rack_z), v(0.86, y, rack_z), 0.03, 0.03), "zinc", drop, 0.004)
        for x in (-0.82, 0.82):
            shell.add(vk.bar(v(x, y, spec["roof"] - 0.01), v(x, y, rack_z - 0.015), 0.03, 0.03), "zinc", drop, 0.003)
    vk.register("ladder_alloy", "metal", kind="aluminium", rust=0.25, dirt=0.6)
    for x in (-0.25, 0.25):
        shell.add(vk.bar(v(x, -0.4, rack_z + 0.04), v(x, 1.9, rack_z + 0.04), 0.05, 0.025), "ladder_alloy", drop, 0.003)
    for k in range(8):
        y = -0.3 + k * 0.29
        shell.add(vk.rod(v(-0.25, y, rack_z + 0.04), v(0.25, y, rack_z + 0.04), 0.012, 6), "ladder_alloy", drop)


def car_front(m, spec, shell, rng, drop, key):
    kind = key
    front = spec["stations"][0][0]
    back = spec["stations"][-1][0]
    zb_front, zt_front, w_front = spec["stations"][0][1:]
    zb_back, zt_back, w_back = spec["stations"][-1][1:]
    plate_text = spec["plate"]
    vk.text_mask("plate_" + key, 4.7, [(plate_text, 0.68, 0.5, "arialbd.ttf", 2.35, 4.2, 1.0, 1.1)], 1024, [(0.04, 0.03)])
    if kind == "hatch":
        grille_z = (0.52, 0.66)
        shell.add(vk.block(v(-0.62, front - 0.025, grille_z[0]), v(0.62, front + 0.02, grille_z[1])), "trim_black", drop, 0.006)
        for k in range(4):
            z = grille_z[0] + 0.02 + k * 0.032
            shell.add(vk.block(v(-0.36, front - 0.035, z), v(0.36, front - 0.025, z + 0.012)), "trim_black", drop, 0.002)
        lights = [(-0.5, 0.59, "round"), (0.5, 0.59, "round")]
        bumper = (0.36, 0.46, 0.06)
        tails = [(-0.6, 0.64, 0.17, 0.15), (0.6, 0.64, 0.17, 0.15)]
    elif kind == "saloon":
        grille_z = (0.52, 0.68)
        shell.add(vk.block(v(-0.44, front - 0.025, grille_z[0]), v(0.44, front + 0.02, grille_z[1])), "chrome", drop, 0.006)
        for k in range(6):
            z = grille_z[0] + 0.015 + k * 0.026
            shell.add(vk.block(v(-0.42, front - 0.035, z), v(0.42, front - 0.025, z + 0.01)), "trim_black", drop, 0.002)
        lights = [(-0.6, 0.61, "square"), (0.6, 0.61, "square")]
        bumper = (0.38, 0.47, 0.07)
        tails = [(-0.55, 0.72, 0.38, 0.11), (0.55, 0.72, 0.38, 0.11)]
    else:
        grille_z = (0.62, 0.86)
        shell.add(vk.block(v(-0.58, front - 0.03, grille_z[0]), v(0.58, front + 0.02, grille_z[1])), "trim_black", drop, 0.008)
        for k in range(7):
            z = grille_z[0] + 0.02 + k * 0.03
            shell.add(vk.block(v(-0.55, front - 0.04, z), v(0.55, front - 0.03, z + 0.014)), "trim_black", drop, 0.002)
        lights = [(-0.75, 0.74, "round"), (0.75, 0.74, "round")]
        bumper = (0.4, 0.56, 0.1)
        tails = []
    broken = rng.choice((0, 1))
    for index, (x, z, shape) in enumerate(lights):
        center = v(x, front - 0.01, z)
        if shape == "round":
            radius = 0.085 if kind == "hatch" else 0.09
            shell.add(vk.lathe([(0.0, 0.0), (radius + 0.018, 0.0), (radius + 0.018, 0.02), (radius + 0.008, 0.035), (radius, 0.03)], 20), "chrome", drop @ vk.frame(center, v(0.0, -1.0, 0.0)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
            if index != broken:
                shell.add(vk.lathe([(0.0, 0.04), (radius * 0.6, 0.038), (radius, 0.03), (radius, 0.022), (0.0, 0.022)], 20), "lens_clear", drop @ vk.frame(center, v(0.0, -1.0, 0.0)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
            else:
                shell.add(vk.lathe([(0.0, 0.0), (radius, 0.0), (radius, 0.004), (0.0, 0.004)], 20), "trim_dark", drop @ vk.frame(center + v(0.0, 0.015, 0.0), v(0.0, -1.0, 0.0)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
        else:
            shell.add(vk.block(center + v(-0.11, -0.025, -0.07), center + v(0.11, 0.01, 0.07)), "chrome", drop, 0.008)
            if index != broken:
                shell.add(vk.block(center + v(-0.095, -0.035, -0.055), center + v(0.095, -0.02, 0.055)), "lens_clear", drop, 0.006)
        shell.add(vk.block(v(x * 1.12 - 0.04, front - 0.02, bumper[0] + 0.12), v(x * 1.12 + 0.04, front + 0.01, bumper[0] + 0.18)), "lens_amber", drop, 0.004)
    for end, y, direction in ((front, front - 0.035, -1.0), (back, back + 0.035, 1.0)):
        low, high, depth = bumper
        droop = 0.0
        if end == back and kind != "van":
            droop = 0.12
        width = (w_front if end == front else w_back) + 0.02
        piece = vk.block(v(-width, -depth * 0.5, 0.0), v(width, depth * 0.5, high - low))
        matrix = drop @ Matrix.Translation((0.0, y + direction * depth * 0.2, low)) @ vk.about(v(-width, 0.0, 0.0), Y, droop)
        shell.add(piece, "chrome" if kind == "saloon" else "trim_black", matrix, 0.012, 2)
        plate_center = v(0.0, y + direction * (depth * 0.7 + 0.004), low + (high - low) * 0.5 + (0.12 if end == front else 0.14))
        plate_matrix = drop @ Matrix.Translation(plate_center)
        normal = v(0.0, direction, 0.0)
        u = Z.cross(normal)
        shell.add(vk.cube(0.5, 0.008, 0.11), "plate_" + key, plate_matrix, 0.002, label=vk.label(drop @ (plate_center + normal * 0.005), u, Z, 0.5, 0.106, 0.8))
    for x, z, w, h in tails:
        center = v(x, back + 0.01, z)
        shell.add(vk.block(center + v(-w * 0.5, -0.02, -h * 0.5), center + v(w * 0.5, 0.012, h * 0.5)), "lens_red", drop, 0.008)
        shell.add(vk.block(center + v(-w * 0.5 - 0.012, -0.02, -h * 0.5 - 0.012), center + v(w * 0.5 + 0.012, 0.004, h * 0.5 + 0.012)), "trim_black", drop, 0.004)
    shell.add(vk.tube([v(0.42, back - 0.6, 0.2), v(0.44, back - 0.1, 0.21), v(0.45, back + 0.06, 0.2)], 0.024, 8, False), "underbody", drop)


def car_interior(m, spec, cabin, rng, drop):
    floor = spec["floor"]
    dash = spec["dash"]
    van = spec["rear"] == "van"
    widest = max(row[3] for row in spec["stations"])
    seat_y = spec["front_seat"]
    width = widest - 0.08
    cabin.add(vk.block(v(-width, dash, floor), v(width, spec["cabin_end"] - 0.02 if not van else -0.3, floor + 0.015)), "carpet", drop)
    cabin.add(vk.block(v(-width, dash, floor + 0.38), v(width, dash + 0.32, floor + 0.62 if not van else floor + 0.55)), "dash", drop, 0.03, 2)
    cabin.add(vk.block(v(-width, dash + 0.22, floor + 0.62 if not van else floor + 0.55), v(width, dash + 0.4, floor + 0.67 if not van else floor + 0.6)), "dash", drop, 0.02, 2)
    wheel_x = -0.38 if not van else -0.45
    binnacle = v(wheel_x, dash + 0.36, floor + 0.7 if not van else floor + 0.64)
    cabin.add(vk.block(binnacle + v(-0.16, -0.06, -0.05), binnacle + v(0.16, 0.06, 0.06)), "dash", drop, 0.02, 2)
    hub = binnacle + v(0.0, 0.22, -0.12)
    tilt = vk.frame(hub, v(0.0, 1.0, 0.45))
    ring = [v(0.0, 0.19 * math.cos(tau * k / 20), 0.19 * math.sin(tau * k / 20)) for k in range(20)]
    cabin.add(g.sweep(ring, g.circle(0.015, 6), closed=True, planar=X), "dash", drop @ tilt)
    for angle in (0.0, math.pi * 0.8, -math.pi * 0.8):
        cabin.add(vk.bar(v(0.0, 0.0, 0.0), v(0.0, 0.18 * math.cos(angle), 0.18 * math.sin(angle)), 0.02, 0.012), "dash", drop @ tilt)
    cabin.add(vk.rod(hub - v(0.0, 0.22, -0.1), hub, 0.025, 8), "dash", drop)
    for x in ((-0.38, 0.38) if not van else (-0.5, 0.0, 0.5)):
        sx = 0.46 if not van else 0.42
        if van or rng.random() < 0.85:
            cabin.add(vk.pillow(sx, 0.48, 0.13, rng, 0.35, 0.02, 0.1), "seat_vinyl", drop @ Matrix.Translation((x, seat_y, floor + 0.27)) @ Matrix.Rotation(0.06, 4, 'X'))
            back = drop @ Matrix.Translation((x, seat_y + 0.27, floor + 0.62)) @ Matrix.Rotation(-0.25, 4, 'X')
            cabin.add(vk.pillow(sx, 0.12, 0.58, rng, 0.35, 0.0, 0.08), "seat_vinyl", back)
            if not van:
                cabin.add(vk.pillow(0.26, 0.1, 0.2, rng, 0.4, 0.0, 0.06), "seat_vinyl", back @ Matrix.Translation((0.0, 0.0, 0.42)))
            cabin.add(vk.block(v(x - sx * 0.45, seat_y - 0.2, floor), v(x + sx * 0.45, seat_y + 0.2, floor + 0.2)), "trim_dark", drop, 0.01)
    if not van:
        rear = spec["rear_seat"]
        cabin.add(vk.pillow(1.25, 0.45, 0.13, rng, 0.3, 0.03, 0.08), "seat_vinyl", drop @ Matrix.Translation((0.0, rear - 0.08, floor + 0.25)))
        cabin.add(vk.pillow(1.25, 0.12, 0.52, rng, 0.3, 0.0, 0.06), "seat_vinyl", drop @ Matrix.Translation((0.0, rear + 0.2, floor + 0.55)) @ Matrix.Rotation(-0.3, 4, 'X'))
        cabin.add(vk.block(v(-0.62, rear - 0.3, floor), v(0.62, rear + 0.15, floor + 0.18)), "trim_dark", drop, 0.01)
        if spec["rear"] == "hatch":
            cabin.add(vk.block(v(-width, rear + 0.32, spec["belt"] - 0.05), v(width, spec["cabin_end"] - 0.02, spec["belt"] - 0.03)), "dash", drop)
            for side in (-1.0, 1.0):
                axle = spec["axles"][1]
                cabin.add(vk.block(v(side * 0.49 if side > 0 else -width, axle - 0.36, floor), v(width if side > 0 else -0.49, axle + 0.36, spec["tyre"] + 0.37)), "trim_dark", drop, 0.02)
        else:
            cabin.add(vk.block(v(-width, spec["cabin_end"] - 0.06, spec["belt"] - 0.04), v(width, spec["cabin_end"] + 0.15, spec["belt"] - 0.02)), "dash", drop)
        cabin.add(vk.rod(v(0.0, seat_y - 0.2, floor + 0.02), v(0.0, seat_y - 0.28, floor + 0.32), 0.008, 6), "steel", drop)
        cabin.add(g.sphere(0.025, 10, 6), "dash", drop @ Matrix.Translation((0.0, seat_y - 0.28, floor + 0.33)))
    else:
        cabin.add(vk.block(v(-0.92, -0.32, floor), v(0.92, -0.28, 1.95)), "trim_dark", drop, 0.004)
        for side in (-1.0, 1.0):
            for axle in spec["axles"][1:]:
                cabin.add(vk.block(v(side * 0.64 if side > 0 else -0.915, axle - 0.4, floor), v(0.915 if side > 0 else -0.64, axle + 0.4, floor + 0.3)), "trim_dark", drop, 0.02)
        vk.register("ply_floor", "wood", along="Y", light=(0.22, 0.17, 0.11), dark=(0.1, 0.08, 0.06), silver=0.4, cracks=0.4, moss=0.25, dirt=0.75)
        cabin.add(vk.block(v(-0.9, -0.27, floor + 0.015), v(0.9, spec["length"] * 0.5 - 0.06, floor + 0.035)), "ply_floor", drop)
        for k in range(3):
            crate(cabin, rng, drop @ v(rng.uniform(-0.5, 0.3), rng.uniform(0.1, 0.9), floor + 0.035), (0.5, 0.34, 0.24), rng.uniform(0.0, tau), None)
        cabin.add(vk.cylinder(0.29, 0.86, 18), "rust", drop @ vk.frame(v(-0.55, 0.4, floor + 0.32), v(0.0, 1.0, 0.1)))
    vk.register("bottle_glass", "glass", tint=(0.02, 0.05, 0.02), cracked=0.0)
    for k in range(3):
        bottle = vk.lathe([(0.0, 0.0), (0.035, 0.0), (0.036, 0.16), (0.014, 0.21), (0.012, 0.26), (0.0, 0.26)], 10)
        cabin.add(bottle, "bottle_glass", drop @ vk.at(v(rng.uniform(-0.5, 0.5), rng.uniform(seat_y - 0.1, seat_y + 0.3), floor + 0.05), rng.uniform(0.0, tau), math.pi * 0.5, 0.0))
    for k in range(4):
        cabin.add(crumple(rng, rng.uniform(0.03, 0.05), 0.4), "litter_paper", drop @ Matrix.Translation((rng.uniform(-0.5, 0.5), rng.uniform(dash + 0.4, seat_y + 0.6), floor + 0.03)))
    leaf_litter(cabin, rng, drop @ v(0.0, seat_y, floor + 0.02), 0.5, 18)
    exhaust_y = spec["stations"][-1][0]
    cabin.add(vk.tube([v(0.38, -0.8, 0.17), v(0.4, exhaust_y - 0.65, 0.18)], 0.022, 8), "underbody", drop)
    cabin.add(vk.block(v(0.25, exhaust_y - 1.2, 0.15), v(0.55, exhaust_y - 0.75, 0.25)), "underbody", drop, 0.03)
    cabin.add(vk.block(v(-0.55, exhaust_y - 1.1, 0.18), v(0.15, exhaust_y - 0.6, 0.32)), "underbody", drop, 0.03)
    for axle in spec["axles"]:
        cabin.add(vk.bar(v(-spec["track"] + 0.1, axle, spec["tyre"]), v(spec["track"] - 0.1, axle, spec["tyre"]), 0.07, 0.07), "underbody", drop, 0.008)


def car_far(m, spec, name):
    far = m.far(name + "_far", 40.0)
    rows = spec["stations"]
    picks = [rows[0], rows[2], rows[len(rows) // 2 - 1], rows[len(rows) // 2 + 1], rows[-3], rows[-1]]
    stations = [(v(0.0, y, (zb + zt) * 0.5), hw, (zt - zb) * 0.5, 1.0, 1.0, spec["egg"]) for y, zb, zt, hw in picks]
    drop = Matrix.Translation((0.0, 0.0, -spec["sink"]))
    far.add(g.loft(stations, 12, spec["exponent"], Z), "steel", drop)
    if spec["rear"] != "van":
        belt = spec["belt"]
        roof = spec["roof"]
        a0, a1 = spec["a"]
        c0, c1 = spec["c"]
        r0, r1 = spec["roof_y"]
        tail_y, tail_z = spec["tail"] if spec["rear"] == "hatch" else (c0, belt)
        outline = [(a0, belt), (tail_y, tail_z if spec["rear"] == "hatch" else belt), (r1 + 0.02, roof), (a1, roof)]
        bm = bmesh.new()
        ring = []
        for side in (-1.0, 1.0):
            ring.append([bm.verts.new(side_point(spec, side, y, z)) for y, z in outline])
        left, right = ring
        bm.faces.new(right)
        bm.faces.new(list(reversed(left)))
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((left[i], left[j], right[j], right[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        far.add(bm, "steel", drop)
    for axle in spec["axles"]:
        for side in (-1.0, 1.0):
            far.add(vk.cylinder(spec["tyre"] - 0.01, spec["tyre_width"], 10), "steel", drop @ Matrix.Translation((side * spec["track"] - spec["tyre_width"] * 0.5, axle, spec["tyre"] - 0.03)))


def window_state(rng, bias=0.0):
    roll = rng.random() + bias
    return "missing" if roll < 0.25 else ("broken" if roll < 0.45 else ("cracked" if roll < 0.75 else "glass"))


def car_wreck(kind):
    spec = car_specs[kind]
    name = "prop_wreck_" + kind
    m = model(name, spec["seed"])
    rng = m.rng
    key = kind
    shell_part = m.part(name + "_body", 38.0)
    cabin_part = m.part(name + "_cabin", 45.0)
    m.sets = [(name + "_body", [name + "_body"]), (name + "_cabin", [name + "_cabin"])]
    m.band = 0.11
    m.boost = 4.5
    length = spec["length"]
    half = length * 0.5
    widest = max(row[3] for row in spec["stations"])
    roof = spec["roof"]
    sink = spec["sink"]
    drop = Matrix.Translation((0.0, 0.0, -sink))
    labels_body = car_mask(spec, key, kind, widest)
    paint = car_looks(spec, key)
    labels_low = [dict(item, origin=item["origin"] - Z * sink) for item in labels_body]
    floor = spec["floor"]
    inner = widest - 0.06
    cavity_low = v(-inner, spec["dash"], floor)
    cavity_high = v(inner, spec["cabin_end"], roof + 0.5)
    body = lower_body(spec)
    door_cut = None
    door_piece = None
    open_side, open_index, open_angle = spec["open"]
    if open_index is not None:
        y0, y1 = spec["doors"][open_index]
        top_cut = spec["belt"] + 0.6 if kind != "van" else roof - 0.25
        door_box = vk.block(v(open_side * (widest - 0.11), y0, floor + 0.02), v(open_side * (widest + 0.2), y1, top_cut))
        door_piece = vk.carve(body.copy(), [door_box.copy()], 'INTERSECT')
        door_cut = door_box
    cutters = [vk.block(cavity_low, cavity_high)]
    if kind == "van":
        cutters[0] = vk.block(v(-inner, spec["dash"], floor), v(inner, half + 0.3, roof - 0.14))
    wells = []
    for axle in spec["axles"]:
        for side in (-1.0, 1.0):
            radius = spec["tyre"] + 0.05
            x0 = side * (widest - 0.3)
            well = g.transformed(vk.cylinder(radius, 0.55, 24), Matrix.Translation((x0, axle, spec["tyre"])) @ Matrix.Rotation(0.0 if side > 0 else math.pi, 4, 'Z'))
            cutters.append(well)
            wells.append((axle, side, radius))
    if door_cut is not None:
        cutters.append(door_cut)
    for index in range(7):
        y = rng.uniform(-half + 0.3, half - 0.3)
        side = rng.choice((-1.0, 1.0))
        z = rng.uniform(0.22, 0.42)
        cutters.append(g.shifted(vk.lump(rng.uniform(0.03, 0.07), rng.uniform(0.05, 0.1), rng.uniform(0.025, 0.05), rng, 0.4, 1), side * body_x(spec, y, z), y, z))
    if kind == "van":
        cutters.extend(van_openings(spec))
    body = vk.carve(body, cutters)
    cabin_x = inner + 0.002

    def chooser(face):
        c = face.calc_center_median()
        if kind == "van" and face.normal.z > 0.45 and c.z > roof - 0.2:
            return None
        if abs(c.x) < cabin_x and cavity_low.y - 0.002 < c.y < (cavity_high.y + 0.002 if kind != "van" else half + 0.4) and c.z > floor - 0.002:
            return "trim_dark"
        for axle, side, radius in wells:
            if side * c.x > widest - 0.302 and math.hypot(c.y - axle, c.z - spec["tyre"]) < radius + 0.004:
                radial = v(0.0, c.y - axle, c.z - spec["tyre"])
                if (radial.length > 1e-6 and face.normal.dot(radial.normalized()) < -0.5) or (face.normal.x * side > 0.5 and side * c.x < widest - 0.25):
                    return "underbody"
        if face.normal.z < -0.6 and c.z < 0.4:
            return "underbody"
        return None

    shell_part.add(body, paint, drop, label=labels_low, chooser=chooser)
    if door_piece is not None:
        y0, y1 = spec["doors"][open_index]
        hinge = v(open_side * (body_x(spec, y0, spec["belt"] - 0.1) - 0.02), y0, 0.0)
        swing = vk.about(hinge, Z, -open_side * open_angle)
        door_look = "primer_door" if spec["odd"] == ("primer_door", open_index) else paint
        closed_space = drop @ swing.inverted() @ drop.inverted()
        shell_part.add(door_piece, door_look, drop @ swing, label=labels_low, chooser=lambda face: "trim_dark" if (closed_space.to_3x3() @ face.normal).x * open_side < -0.5 else None, label_space=closed_space)
        door_parts = (swing, y0, y1)
    else:
        door_parts = None
    if kind != "van":
        greenhouse(m, spec, shell_part, cabin_part, rng, paint, drop, labels_low, door_parts, open_side, open_index)
    else:
        van_body(m, spec, shell_part, cabin_part, rng, paint, drop, labels_low)
    car_front(m, spec, shell_part, rng, drop, key)
    car_interior(m, spec, cabin_part, rng, drop)
    for axle in spec["axles"]:
        for side in (-1.0, 1.0):
            center = v(side * spec["track"], axle, spec["tyre"] - sink)
            car_wheel(cabin_part, spec, center, side, rng, cap=(rng.random() < 0.5 and kind != "van"))
    leaf_litter(shell_part, rng, v(0.0, (spec["roof_y"][0] + spec["roof_y"][1]) * 0.5 if kind != "van" else 0.5, roof + 0.02 - sink), 0.5, 26, 0.0)
    leaf_litter(cabin_part, rng, v(0.0, 0.0, 0.0), 1.25, 34)
    car_far(m, spec, name)
    loot_kind, spot = spec["loot"]
    m.loot(loot_kind, v(spot[0], spot[1], spot[2] - sink))
    belt = spec["belt"] - sink
    m.col("metal", (-widest, -half, 0.1), (widest, half, belt))
    if kind == "van":
        m.col("metal", (-widest, -1.1, belt), (widest, half, roof - sink))
    else:
        m.col("metal", (-spec["w_roof"] - 0.05, spec["a"][0], belt), (spec["w_roof"] + 0.05, spec["c"][0], roof - sink))
    m.close(v(2.6, -half - 1.6, 1.6), v(0.0, -half * 0.4, 0.7), 35.0)
    m.close(v(open_side * 2.2, -0.6 if kind != "van" else half + 1.6, 1.4), v(0.0, 0.3 if kind != "van" else half - 0.5, 0.6), 38.0)
    m.close(v(-1.4, -half - 0.9, 0.9), v(-0.5, -half, 0.5), 45.0)
    m.info = {"kind": "point", "front": "-Y (car nose)", "wheelbase": round(spec["axles"][1] - spec["axles"][0], 3)}
    return m


builders = {
    "prop_swatches": swatches,
    "prop_bollard": bollard,
    "prop_bench": bench,
    "prop_bus_shelter": shelter,
    "prop_phone_box": phone_box,
    "prop_post_box": post_box,
    "prop_street_sign": street_sign,
    "prop_litter_bin": litter_bin,
    "prop_market_stall_a": lambda: market_stall("a"),
    "prop_market_stall_b": lambda: market_stall("b"),
    "prop_war_memorial": war_memorial,
    "prop_horse_trough": horse_trough,
    "prop_garden_wall": garden_wall,
    "prop_railing": railing,
    "prop_picket_fence": picket_fence,
    "prop_traffic_cone": traffic_cone,
    "prop_sandbags": sandbags,
    "prop_wreck_hatch": lambda: car_wreck("hatch"),
    "prop_wreck_saloon": lambda: car_wreck("saloon"),
    "prop_wreck_van": lambda: car_wreck("van"),
}

directions = {
    "three": (0.8, -1.0, 0.5),
    "back": (-0.9, 0.85, 0.42),
    "front": (0.12, -1.0, 0.16),
    "side": (1.0, -0.1, 0.14),
    "top": (0.25, -0.45, 1.0),
}


def render_set(name, objects, views, prefix, closeups, far_objects=None, markers=None):
    vk.render_settings(samples, (1280, 720))
    sun = vk.daylight()
    ground = vk.ground_plane(0.0)
    paths = []
    for view in views:
        path = prefix + "_" + view + ".png"
        vk.view_shot(path, objects, directions[view], 40.0, None, 0.07)
        paths.append(path)
    for index, (position, target, lens) in enumerate(closeups):
        path = prefix + "_close" + str(index) + ".png"
        vk.close_shot(path, position, target, lens)
        paths.append(path)
    if markers:
        for obj in markers:
            obj.hide_render = False
            obj.data.materials.clear()
            obj.data.materials.append(vk.overlay_material((1.0, 0.25, 0.1) if obj.name.startswith("col_") else (0.2, 1.0, 0.3), 1.2, 0.4))
        path = prefix + "_collision.png"
        vk.view_shot(path, objects, directions["three"], 40.0, None, 0.07)
        paths.append(path)
        for obj in markers:
            obj.hide_render = True
    if far_objects:
        for obj in objects:
            obj.hide_render = True
        for obj in far_objects:
            obj.hide_render = False
        path = prefix + "_far.png"
        vk.view_shot(path, objects, directions["three"], 40.0, None, 0.07)
        paths.append(path)
        for obj in objects:
            obj.hide_render = False
        for obj in far_objects:
            obj.hide_render = True
    vk.contact_sheet(paths, prefix + "_sheet.png", 3, (640, 360))
    return paths


def look(name):
    vk.reset()
    looks()
    m = builders[name]()
    objects = [p.build() for p in m.parts.values()]
    far_objects = [p.build() for p in m.far_parts.values()]
    for obj in far_objects:
        obj.location.x += 0.0
        obj.hide_render = True
    vk.log("LOOK", name, "near tris", vk.triangles_of(objects), "far tris", vk.triangles_of(far_objects))
    os.makedirs(preview_root, exist_ok=True)
    render_set(name, objects, [] if name == "prop_swatches" else ["three", "back", "front"], os.path.join(preview_root, name + "_look"), m.closeups, far_objects)


def bake(name):
    vk.reset()
    looks()
    started = time.time()
    m = builders[name]()
    built = {key: p.build() for key, p in m.parts.items()}
    objects = list(built.values())
    far_built = {key: p.build() for key, p in m.far_parts.items()}
    far_objects = list(far_built.values())
    far_baked = [obj for key, obj in far_built.items() if key not in m.library_parts]
    bake_keys = [key for key in built if key not in m.library_parts]
    sets = m.sets if m.sets else ([(name, bake_keys)] if bake_keys else [])
    texture_sets = []
    for index, (key, members) in enumerate(sets):
        tset = vk.texture_set(key, name, band=m.band, boost=m.boost)
        tset.bake_near([built[member] for member in members], with_far=(index == 0 and bool(far_baked)))
        texture_sets.append(tset)
    if far_baked and texture_sets:
        texture_sets[0].bake_far(far_baked, objects)
    for obj in objects + far_objects:
        vk.clean(obj)
    marker_look = texture_sets[0].material if texture_sets else objects[0].data.materials[0]
    markers = [vk.marker(marker_name, low, high, marker_look) for marker_name, low, high in m.markers]
    path, document = vk.export(name, objects + markers)
    near = vk.audit(path, document)
    far = None
    if far_objects:
        path, document = vk.export(name + "_far", far_objects)
        far = vk.audit(path, document)
    record(name, m, near, far)
    vk.log("BAKE DONE", name, round(time.time() - started, 1), "s")


def record(name, m, near, far):
    document = {}
    if os.path.exists(manifest_path):
        import json
        with open(manifest_path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    document["space"] = "Blender model space in metres: X right, Y back (front faces -Y), Z up; origin at ground contact, bottom centre"
    entry = {"model": name, "far_model": name + "_far" if far else None, "size": [round(near["high"][i] - near["low"][i], 3) for i in range(3)], "bounds_min": list(near["low"]), "bounds_max": list(near["high"]), "triangles": near["triangles"], "triangles_far": far["triangles"] if far else 0, "markers": near["markers"]}
    boxes = [(low, high) for marker_name, low, high in m.markers if marker_name.startswith("col_")]
    if boxes:
        low = [round(min(box[0][i] for box in boxes), 3) for i in range(3)]
        high = [round(max(box[1][i] for box in boxes), 3) for i in range(3)]
        entry["footprint_min"] = low
        entry["footprint_max"] = high
        entry["footprint_size"] = [round(high[i] - low[i], 3) for i in range(3)]
    entry.update(m.info)
    document.setdefault("props", {})[name] = entry
    vk.write_json(manifest_path, document)


def preview(name):
    vk.reset()
    objects = vk.import_model(name)
    visual = [obj for obj in objects if obj.type == 'MESH' and not vk.is_marker(obj.name)]
    markers = [obj for obj in objects if obj.type == 'MESH' and vk.is_marker(obj.name)]
    for obj in markers:
        obj.hide_render = True
    far_objects = []
    if os.path.exists(os.path.join(vk.models_root, name + "_far", name + "_far.gltf")):
        far_objects = [obj for obj in vk.import_model(name + "_far") if obj.type == 'MESH']
        for obj in far_objects:
            obj.hide_render = True
    m = builders[name]()
    os.makedirs(preview_root, exist_ok=True)
    render_set(name, visual, ["three", "back", "front", "side", "top"], os.path.join(preview_root, name), m.closeups, far_objects, markers)


def main():
    started = time.time()
    names = wanted or [name for name in builders if name != "prop_swatches"]
    for name in names:
        if mode == "look":
            look(name)
        elif mode == "bake":
            bake(name)
        elif mode == "preview":
            preview(name)
        elif mode == "all":
            bake(name)
            preview(name)
    vk.log("DONE", mode, names, round(time.time() - started, 1), "s")


if __name__ == "__main__":
    main()
