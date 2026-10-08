import bpy
import bmesh
import json
import math
import os
import random
import sys
import time
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gunkit as g
import vehiclekit as vk
from vehiclekit import v, X, Y, Z, tau

arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = arguments[0] if arguments else "look"
wanted = [name for name in (arguments[1].split(",") if len(arguments) > 1 else []) if name]
samples = int(arguments[2]) if len(arguments) > 2 else 48
preview_root = os.path.join(vk.previews_root, "vehicles")


class model:
    def __init__(self, name, seed):
        self.name = name
        self.rng = random.Random(seed)
        self.parts = {}
        self.far_parts = {}
        self.sets = []
        self.markers = []
        self.points = []
        self.closeups = []
        self.manifest = {}
        self.objects = {}

    def part(self, key, sharp=38.0, origin=None):
        if key not in self.parts:
            self.parts[key] = vk.part(key, sharp, origin)
        return self.parts[key]

    def far(self, key, sharp=40.0, origin=None):
        if key not in self.far_parts:
            self.far_parts[key] = vk.part("far_" + key, sharp, origin)
        return self.far_parts[key]

    def col(self, low, high, surface="metal"):
        index = len([marker for marker in self.markers if marker[0].startswith("col_" + surface)]) + 1
        self.markers.append(("col_" + surface + "_" + str(index), Vector(low), Vector(high)))

    def point(self, name, position, size=0.03):
        self.points.append((name, Vector(position), size))

    def close(self, position, target, lens=45.0):
        self.closeups.append((Vector(position), Vector(target), lens))


def looks():
    vk.standard_looks()
    vk.register("sand", "paint", color=(0.27, 0.2, 0.115), under=(0.06, 0.07, 0.035), primer=(0.14, 0.05, 0.03), chips=0.5, fade=0.5, chalk=0.25, bleed=0.55, streaks=0.65, gloss=0.65, dirt=0.75, rot=0.8, rot_height=0.8, dents=0.8)
    vk.register("olive", "paint", color=(0.045, 0.055, 0.028), under=(0.25, 0.19, 0.11), primer=(0.14, 0.05, 0.03), chips=0.55, fade=0.45, chalk=0.25, bleed=0.55, streaks=0.65, gloss=0.65, dirt=0.75, rot=0.8, rot_height=0.8, dents=0.9)
    vk.register("primer_red", "paint", color=(0.12, 0.04, 0.022), under=(0.1, 0.1, 0.1), primer=(0.08, 0.08, 0.08), chips=0.45, fade=0.3, chalk=0.15, bleed=0.6, streaks=0.6, gloss=0.85, dirt=0.75, rot=0.8, dents=0.9)
    vk.register("roof_white", "paint", color=(0.36, 0.35, 0.32), under=(0.27, 0.2, 0.115), primer=(0.14, 0.05, 0.03), chips=0.5, fade=0.3, chalk=0.1, bleed=0.6, streaks=0.7, gloss=0.65, dirt=0.8, moss=0.35)
    vk.register("blue_panel", "paint", color=(0.035, 0.065, 0.11), under=(0.12, 0.12, 0.11), primer=(0.14, 0.05, 0.03), chips=0.55, fade=0.55, chalk=0.35, bleed=0.6, streaks=0.65, gloss=0.6, dirt=0.75, dents=0.9)
    vk.register("chassis_black", "paint", color=(0.018, 0.018, 0.018), under=(0.1, 0.04, 0.025), primer=(0.1, 0.04, 0.025), chips=0.55, fade=0.3, chalk=0.1, bleed=0.6, streaks=0.5, gloss=0.6, dirt=0.95, rot=1.0, rot_height=0.9)
    vk.register("plate_steel", "metal", kind="steel", rust=0.55, dirt=0.7)
    vk.register("plate_rust", "metal", kind="rust", rust=1.0, dirt=0.6)
    vk.register("plate_dark", "metal", kind="blackened", rust=0.5, dirt=0.7)
    vk.register("tube_steel", "metal", kind="steel", rust=0.6, dirt=0.6)
    vk.register("tyre", "rubber", perished=0.55, dirt=0.95, splash=0.9)
    vk.register("rim_paint", "paint", color=(0.3, 0.3, 0.28), under=(0.1, 0.1, 0.1), primer=(0.14, 0.05, 0.03), chips=0.55, fade=0.3, chalk=0.1, bleed=0.65, streaks=0.5, gloss=0.6, dirt=0.9, splash=0.9, rot=0.8)
    vk.register("can_olive", "paint", color=(0.04, 0.05, 0.025), under=(0.1, 0.04, 0.025), primer=(0.1, 0.04, 0.025), chips=0.5, fade=0.4, chalk=0.2, bleed=0.5, gloss=0.6, dirt=0.65)
    vk.register("can_red", "paint", color=(0.22, 0.02, 0.012), under=(0.1, 0.04, 0.025), primer=(0.1, 0.04, 0.025), chips=0.5, fade=0.45, chalk=0.2, bleed=0.5, gloss=0.6, dirt=0.65)
    vk.register("lens", "glass", tint=(0.08, 0.08, 0.075), cracked=0.4)
    vk.register("lens_red", "plastic", color=(0.2, 0.012, 0.01), fade=0.3, gloss=0.25, dirt=0.6)
    vk.register("lens_amber", "plastic", color=(0.4, 0.15, 0.02), fade=0.4, gloss=0.25, dirt=0.6)
    vk.register("lens_green", "plastic", color=(0.02, 0.2, 0.05), fade=0.3, gloss=0.25, dirt=0.6)
    vk.register("seat_canvas", "fabric", kind="canvas", tint=(0.09, 0.09, 0.06), weave=12.0, stains=0.7, mildew=0.4, dirt=0.75)
    vk.register("seat_vinyl", "fabric", kind="vinyl", tint=(0.05, 0.045, 0.04), dirt=0.6)
    vk.register("floor_plate", "metal", kind="steel", rust=0.55, dirt=0.85)
    vk.register("dash_paint", "paint", color=(0.03, 0.035, 0.03), under=(0.1, 0.04, 0.025), primer=(0.1, 0.04, 0.025), chips=0.5, fade=0.3, chalk=0.1, bleed=0.4, gloss=0.65, dirt=0.65)
    vk.register("mud_rubber", "rubber", perished=0.4, dirt=1.0, splash=1.2)
    vk.register("wood_handle", "wood", along="Z", light=(0.2, 0.15, 0.1), dark=(0.08, 0.06, 0.04), silver=0.5, cracks=0.4, dirt=0.5)
    vk.register("heat_blue", "metal", kind="steel", rust=0.45, dirt=0.4, tone=(0.12, 0.1, 0.14))
    vk.register("engine_alloy", "metal", kind="aluminium", rust=0.25, dirt=0.85)
    vk.register("engine_black", "paint", color=(0.025, 0.025, 0.025), under=(0.2, 0.2, 0.19), primer=(0.2, 0.2, 0.19), chips=0.5, fade=0.2, chalk=0.05, bleed=0.4, gloss=0.5, dirt=0.9)
    vk.register("blade_paint", "paint", color=(0.04, 0.045, 0.04), under=(0.2, 0.2, 0.19), primer=(0.3, 0.3, 0.29), chips=0.35, fade=0.3, chalk=0.15, bleed=0.3, streaks=0.4, gloss=0.55, dirt=0.4)
    vk.register("blade_tip", "paint", color=(0.42, 0.3, 0.02), under=(0.2, 0.2, 0.19), primer=(0.3, 0.3, 0.29), chips=0.45, fade=0.45, chalk=0.25, bleed=0.3, gloss=0.55, dirt=0.4)
    vk.register("gauge", "glass", tint=(0.03, 0.03, 0.028), cracked=0.5)
    vk.register("rope_old", "fabric", kind="hessian", tint=(0.4, 0.32, 0.21), weave=18.0, stains=0.75, mildew=0.35, dirt=0.75)


def helix(start, end, coil, wire, turns, sides=5, steps=10):
    start = Vector(start)
    end = Vector(end)
    axis = end - start
    forward = axis.normalized()
    side = forward.orthogonal().normalized()
    other = forward.cross(side)
    count = int(turns * steps)
    path = [start + axis * s / count + (side * math.cos(tau * turns * s / count) + other * math.sin(tau * turns * s / count)) * coil for s in range(count + 1)]
    return g.sweep(path, g.circle(wire, sides), up=forward)


def tube_frame(target, look, points, radius=0.03, sides=8, welds=True, seed=0):
    points = [Vector(p) for p in points]
    for a, b in zip(points[:-1], points[1:]):
        target.add(vk.rod(a, b, radius, sides), look)
    if welds:
        for index, p in enumerate(points[1:-1]):
            weld_ring(target, p, points[index + 2] - points[index], radius, seed + index)


def weld_ring(target, center, axis, radius, seed=0):
    axis = Vector(axis).normalized()
    side = axis.orthogonal().normalized()
    other = axis.cross(side)
    steps = 12
    path = [Vector(center) + (side * math.cos(tau * s / steps) + other * math.sin(tau * s / steps)) * (radius + 0.002) for s in range(steps + 1)]
    vk.weld(target, path, axis, 0.006, seed, "weld")


def stitch_welds(target, frame_matrix, width, height, thickness, edges, seed=0, pitch=0.16, length=0.07):
    normal = frame_matrix.to_3x3() @ v(0.0, -1.0, 0.0)
    for edge in edges:
        if edge in ("top", "bottom"):
            z = height * 0.5 if edge == "top" else -height * 0.5
            count = max(int(width / pitch), 1)
            for k in range(count):
                x = -width * 0.5 + (k + 0.5) * width / count
                a = frame_matrix @ v(x - length * 0.5, -thickness * 0.5, z)
                b = frame_matrix @ v(x + length * 0.5, -thickness * 0.5, z)
                vk.weld(target, [a, b], normal, 0.006, seed + k, "weld")
        else:
            x = width * 0.5 if edge == "right" else -width * 0.5
            count = max(int(height / pitch), 1)
            for k in range(count):
                z = -height * 0.5 + (k + 0.5) * height / count
                a = frame_matrix @ v(x, -thickness * 0.5, z - length * 0.5)
                b = frame_matrix @ v(x, -thickness * 0.5, z + length * 0.5)
                vk.weld(target, [a, b], normal, 0.006, seed + 31 + k, "weld")


def plate(target, look, frame_matrix, width, height, thickness=0.008, slits=(), bolts=True, bolt_look="zinc", rng=None, bevel=0.003, label=None, tint=None):
    outline = [(-width * 0.5, -height * 0.5), (width * 0.5, -height * 0.5), (width * 0.5, height * 0.5), (-width * 0.5, height * 0.5)]
    holes = []
    for cx, cz, sw, sh in slits:
        holes.append([(cx - sw * 0.5, cz - sh * 0.5), (cx - sw * 0.5, cz + sh * 0.5), (cx + sw * 0.5, cz + sh * 0.5), (cx + sw * 0.5, cz - sh * 0.5)])
    piece = vk.slab(outline, thickness, holes)
    matrix = frame_matrix @ Matrix.Rotation(math.pi * 0.5, 4, 'X')
    target.add(piece, look, matrix, bevel, 1, label=label, tint=tint)
    if bolts:
        spacing = 0.16
        for edge in range(4):
            if edge in (0, 2):
                count = max(int(width / spacing), 1)
                for k in range(count + 1):
                    x = -width * 0.5 + 0.025 + (width - 0.05) * k / count
                    z = (-height * 0.5 + 0.025) if edge == 0 else (height * 0.5 - 0.025)
                    vk.bolt(target, frame_matrix @ v(x, -thickness * 0.5, z), frame_matrix.to_3x3() @ v(0.0, -1.0, 0.0), 0.02, bolt_look, False)
            else:
                count = max(int((height - 0.05) / spacing), 1)
                for k in range(1, count):
                    z = -height * 0.5 + 0.025 + (height - 0.05) * k / count
                    x = (-width * 0.5 + 0.025) if edge == 3 else (width * 0.5 - 0.025)
                    vk.bolt(target, frame_matrix @ v(x, -thickness * 0.5, z), frame_matrix.to_3x3() @ v(0.0, -1.0, 0.0), 0.02, bolt_look, False)


def face_frame(origin, normal, up=Z):
    normal = Vector(normal).normalized()
    u = Vector(up).cross(normal).normalized()
    w = normal.cross(u).normalized()
    matrix = Matrix((u, -normal, w)).transposed().to_4x4()
    matrix.translation = origin
    return matrix


def oriented_face(bm, verts, outward):
    face = bm.faces.new(verts)
    face.normal_update()
    if face.normal.dot(outward) < 0.0:
        face.normal_flip()
    return face


def tread_lug(path, widths, depths, mirror, sink=0.006, draft=0.007):
    bm = bmesh.new()
    rings = []
    count = len(path)
    for i, (x, r, angle) in enumerate(path):
        before = path[max(i - 1, 0)]
        after = path[min(i + 1, count - 1)]
        dx = after[0] - before[0]
        dr = after[1] - before[1]
        length = math.hypot(dx, dr)
        radial = v(0.0, math.cos(angle), math.sin(angle))
        tangent = v(0.0, -math.sin(angle), math.cos(angle))
        normal = (X * -dr + radial * dx) / length
        point = X * x + radial * r
        half = widths[i] * 0.5
        ring = [point - normal * sink - tangent * half, point - normal * sink + tangent * half, point + normal * depths[i] + tangent * (half - draft), point + normal * depths[i] - tangent * (half - draft)]
        if mirror:
            ring = [v(-p.x, p.y, p.z) for p in ring]
        rings.append([bm.verts.new(p) for p in ring])
    centers = [sum((vert.co for vert in ring), Vector()) / 4.0 for ring in rings]
    for i in range(count - 1):
        a = rings[i]
        b = rings[i + 1]
        middle = (centers[i] + centers[i + 1]) * 0.5
        for quad in ((a[3], a[2], b[2], b[3]), (a[1], b[1], b[2], a[2]), (a[0], a[3], b[3], b[0])):
            oriented_face(bm, quad, sum((vert.co for vert in quad), Vector()) / 4.0 - middle)
    oriented_face(bm, rings[0], centers[0] - centers[1])
    oriented_face(bm, rings[-1], centers[-1] - centers[-2])
    return bm


def offroad_tyre(radius, width, rim, lugs=18):
    pieces = []
    base = radius - 0.021
    half = width * 0.5
    profile = [(rim + 0.01, -width * 0.42), (rim + 0.03, -width * 0.47), (radius - 0.09, -width * 0.52), (radius - 0.045, -width * 0.5), (base - 0.004, -width * 0.44), (base, -width * 0.3), (base + 0.001, 0.0), (base, width * 0.3), (base - 0.004, width * 0.44), (radius - 0.045, width * 0.5), (radius - 0.09, width * 0.52), (rim + 0.03, width * 0.47), (rim + 0.01, width * 0.42)]
    pieces.append(g.revolve(profile, 48))
    pitch = tau / lugs
    track = [(0.012, base), (0.06, base), (half * 0.74, base - 0.001), (half * 0.9, base - 0.007), (half * 0.99, radius - 0.047), (half * 1.035, radius - 0.075)]
    widths = [0.06, 0.068, 0.074, 0.078, 0.08, 0.07]
    depths = [0.019, 0.021, 0.021, 0.019, 0.015, 0.009]
    for side in (1.0, -1.0):
        for index in range(lugs):
            count = 6 if index % 2 == 0 else 5
            start = (index + (0.0 if side > 0 else 0.5)) * pitch
            path = [(x, r, start + side * 0.1 * x / half) for x, r in track[:count]]
            pieces.append(tread_lug(path, widths[:count], depths[:count], side < 0))
    return pieces


def steel_wheel(target, rim, width, look="rim_paint", hub_look="steel", holes=5, studs=5, disc_offset=0.035):
    w = width * 0.44
    profile = [(0.0, disc_offset + 0.045), (0.06, disc_offset + 0.045), (0.075, disc_offset + 0.03), (0.095, disc_offset + 0.022), (0.16, disc_offset), (rim - 0.025, disc_offset - 0.012), (rim - 0.008, disc_offset + 0.01), (rim - 0.004, w - 0.01), (rim + 0.014, w + 0.002), (rim + 0.014, w + 0.012), (rim - 0.006, w + 0.012), (rim - 0.014, w - 0.006), (rim - 0.014, -w + 0.006), (rim - 0.006, -w - 0.012), (rim + 0.014, -w - 0.012), (rim + 0.014, -w - 0.002), (rim - 0.004, -w + 0.01), (rim - 0.025, -w * 0.5), (0.0, -w * 0.5)]
    disc = g.revolve(profile, 32)
    cutters = []
    for k in range(holes):
        angle = tau * (k + 0.5) / holes
        cutters.append(g.transformed(vk.cylinder(0.026, 0.2, 10), Matrix.Translation((0.012, math.cos(angle) * (rim * 0.66), math.sin(angle) * (rim * 0.66)))))
    target.add(vk.carve(disc, cutters), look)
    for k in range(studs):
        angle = tau * k / studs
        center = v(disc_offset + 0.045, math.cos(angle) * 0.072, math.sin(angle) * 0.072)
        target.add(g.shifted(g.hexagon(0.026, 0.018, "x"), center.x + 0.009, center.y, center.z), hub_look)
        target.add(vk.cylinder(0.008, 0.03, 6), hub_look, Matrix.Translation(center + v(0.018, 0.0, 0.0)))
    target.add(g.revolve([(0.0, 0.0), (0.042, 0.0), (0.045, 0.02), (0.03, 0.04), (0.0, 0.045)], 16), hub_look, Matrix.Translation((disc_offset + 0.04, 0.0, 0.0)))


def rover_wheel(m, key, center, side):
    radius = 0.4
    width = 0.27
    rim = 0.203
    wheel = m.part(key, 42.0, center)
    turn = Matrix.Translation(center) @ (Matrix.Identity(4) if side > 0 else Matrix.Rotation(math.pi, 4, 'Z'))
    for piece in offroad_tyre(radius, width, rim):
        wheel.add(piece, "tyre", turn)
    sub = vk.part("staging")
    steel_wheel(sub, rim, width)
    merge_into(wheel, sub, turn)
    return wheel


def merge_into(target, other, matrix=None):
    base = len(target.coords)
    for coord in other.coords:
        target.coords.append(tuple(matrix @ Vector(coord)) if matrix is not None else coord)
    target.colors.extend(other.colors)
    for face, slot, uvs, box, flag in zip(other.faces, other.face_slot, other.face_label, other.face_uv, other.face_boost):
        target.faces.append(tuple(base + index for index in face))
        target.face_slot.append(target.slot(other.slots[slot]))
        target.face_label.append(uvs)
        target.face_uv.append(box)
        target.face_boost.append(flag)


def jerrycan(target, center, yaw, look, rng):
    matrix = Matrix.Translation(center) @ Matrix.Rotation(yaw, 4, 'Z')
    target.add(vk.cube(0.165, 0.345, 0.43), look, matrix @ Matrix.Translation((0.0, 0.0, 0.215)), 0.012, 2)
    for side in (-1.0, 1.0):
        for a, b in ((v(side * 0.084, -0.14, 0.05), v(side * 0.084, 0.14, 0.38)), (v(side * 0.084, -0.14, 0.38), v(side * 0.084, 0.14, 0.05))):
            target.add(vk.bar(a, b, 0.006, 0.022, v(side, 0.0, 0.0)), look, matrix, 0.002)
    for x in (-0.05, 0.0, 0.05):
        target.add(vk.bar(v(x, -0.07, 0.45), v(x, 0.07, 0.45), 0.014, 0.04, X), look, matrix, 0.004)
    target.add(vk.cylinder(0.025, 0.05, 10), look, matrix @ vk.frame(v(0.0, 0.13, 0.42), v(0.0, 0.5, 1.0)))


def shattered_glass(target, rng, corners, reach=(0.1, 0.24), look="glass_cracked"):
    corners = [Vector(p) for p in corners]
    center = sum(corners, Vector()) / len(corners)
    for index in range(len(corners)):
        a = corners[index]
        b = corners[(index + 1) % len(corners)]
        steps = max(int((b - a).length / 0.11), 2)
        for k in range(steps):
            t0 = k / steps
            t1 = (k + 1) / steps
            tip = a.lerp(b, (t0 + t1) * 0.5 + rng.uniform(-0.35, 0.35) / steps).lerp(center, rng.uniform(reach[0], reach[1]))
            shard = bmesh.new()
            shard.faces.new([shard.verts.new(p) for p in (a.lerp(b, t0), a.lerp(b, t1), tip)])
            vk.thicken(shard, 0.004)
            target.add(shard, look)


def rope_coil(target, center, radius, wire, loops, rng, look="rope_old"):
    center = Vector(center)
    phase = rng.uniform(0.0, tau)
    steps = 12
    count = int(loops * steps)
    points = []
    for s in range(count + 1):
        t = s / steps
        angle = phase + tau * t
        r = radius * (1.0 - 0.05 * t + 0.05 * math.sin(angle * 2.0 + phase))
        drift = v(0.012 * math.sin(t * 2.1 + phase), 0.012 * math.cos(t * 1.7), 0.0)
        points.append(center + drift + v(math.cos(angle) * r, math.sin(angle) * r, wire * (1.0 + 1.3 * t)))
    end = points[-1]
    outward = v(end.x - center.x, end.y - center.y, 0.0).normalized()
    points.append(end + outward * 0.1 - v(0.0, 0.0, wire * 1.5))
    points.append(v(end.x, end.y, center.z + wire) + outward * 0.2 + v(0.02, 0.03, 0.0))
    vk.rope_line(target, points, wire, look, wire * 1.8)


def caged_lamp(frame_part, kit_part, center, direction, radius=0.09):
    direction = Vector(direction).normalized()
    matrix = vk.frame(Vector(center), direction)
    kit_part.add(g.revolve([(0.0, -0.1), (radius * 0.7, -0.1), (radius + 0.012, -0.03), (radius + 0.012, 0.01), (radius + 0.004, 0.02)], 18), "chassis_black", matrix)
    kit_part.add(g.revolve([(0.0, 0.03), (radius * 0.6, 0.026), (radius, 0.016), (radius, 0.008), (0.0, 0.008)], 18), "lens", matrix)
    outer = radius + 0.016
    inner = radius * 0.78
    reach = radius * 1.1
    for x, r in ((0.004, outer), (reach, inner)):
        ring = [v(x, math.cos(tau * s / 16) * r, math.sin(tau * s / 16) * r) for s in range(16)]
        frame_part.add(g.sweep([matrix @ p for p in ring], g.circle(0.0045, 5), closed=True, planar=direction), "mesh")
    for k in range(6):
        angle = tau * (k + 0.5) / 6
        frame_part.add(vk.rod(matrix @ v(0.004, math.cos(angle) * outer, math.sin(angle) * outer), matrix @ v(reach, math.cos(angle) * inner, math.sin(angle) * inner), 0.004, 5), "mesh")
    for a, b in ((v(reach, -inner, 0.0), v(reach, inner, 0.0)), (v(reach, 0.0, -inner), v(reach, 0.0, inner))):
        frame_part.add(vk.rod(matrix @ a, matrix @ b, 0.0045, 5), "mesh")


def arch_cutter(side, y, z, radius=0.49):
    start = 0.35 if side > 0 else -1.05
    return g.transformed(vk.cylinder(radius, 0.7, 24), Matrix.Translation((start, y, z)))


def rover():
    m = model("veh_rover", 501)
    rng = m.rng
    hull = m.part("rover_hull", 36.0)
    frame = m.part("rover_frame", 40.0)
    cab = m.part("rover_cab", 40.0)
    kit = m.part("rover_kit", 42.0)
    wheelbase = 2.794
    yf = -wheelbase * 0.5
    yr = wheelbase * 0.5
    track = 0.775
    radius = 0.4
    axle_z = 0.4
    floor = 0.74
    belt = 1.32
    roof = 1.98
    half = 0.84
    front = -2.0
    back = 2.06
    for x in (-0.43, 0.43):
        frame.add(vk.block(v(x - 0.035, -2.12, 0.47), v(x + 0.035, 2.14, 0.62)), "chassis_black", None, 0.006)
    for y in (-2.08, -0.95, 0.4, 1.55, 2.1):
        frame.add(vk.block(v(-0.43, y - 0.04, 0.49), v(0.43, y + 0.04, 0.6)), "chassis_black", None, 0.005)
    for y, diff in ((yf, 0.16), (yr, -0.08)):
        frame.add(vk.rod(v(-0.63, y, axle_z), v(0.63, y, axle_z), 0.055, 10), "chassis_black")
        frame.add(g.sphere(0.15, 14, 8), "chassis_black", Matrix.Translation((diff, y, axle_z - 0.02)) @ Matrix.Scale(0.85, 4, Y))
        frame.add(vk.rod(v(diff, y - 0.1, axle_z), v(diff * 0.4, y - 0.6 if y < 0 else y - 0.5, 0.5), 0.035, 8), "chassis_black")
        for side in (-1.0, 1.0):
            frame.add(g.sphere(0.1, 12, 8), "chassis_black", Matrix.Translation((side * 0.64, y, axle_z)))
            frame.add(helix(v(side * 0.5, y, axle_z + 0.06), v(side * 0.5, y, 0.68), 0.075, 0.011, 5.5), "chassis_black")
            frame.add(vk.rod(v(side * 0.36, y + 0.14, axle_z + 0.02), v(side * 0.4, y + 0.1, 0.66), 0.022, 8), "plate_steel")
            frame.add(vk.bar(v(side * 0.43, y + (0.15 if y < 0 else -0.15), axle_z - 0.03), v(side * 0.43, y + (0.95 if y < 0 else -0.95), 0.52), 0.05, 0.06), "chassis_black", None, 0.004)
    frame.add(vk.rod(v(-0.6, yf + 0.18, axle_z - 0.05), v(0.6, yf + 0.18, axle_z - 0.05), 0.016, 8), "plate_steel")
    frame.add(vk.block(v(-0.3, 1.6, 0.5), v(0.25, 1.95, 0.72)), "chassis_black", None, 0.02, 2)
    frame.add(vk.block(v(-0.32, -1.7, 0.55), v(0.32, -0.9, 1.05)), "engine_black", None, 0.03, 2)
    for side in (-1.0, 1.0):
        for k in range(4):
            frame.add(vk.rod(v(side * 0.33, -1.55 + k * 0.18, 0.95), v(side * 0.45, -1.55 + k * 0.18, 0.85), 0.018, 6), "heat_blue")
    hull_looks = {"wing": "sand", "bonnet": "primer_red", "door_l": "olive", "door_r": "sand", "side": "sand", "roof": "roof_white", "rear": "blue_panel"}
    for side in (-1.0, 1.0):
        wing = vk.block(v(side * 0.52, front, 0.82), v(side * half, -0.9, 1.2))
        hull.add(vk.carve(wing, [arch_cutter(side, yf, axle_z)]), hull_looks["wing"], None, 0.006, 1, tint=(1.0, 1.0, 1.0) if side > 0 else (0.92, 0.95, 0.9))
        hull.add(vk.block(v(side * 0.5, front + 0.02, 0.75), v(side * 0.53, -0.92, 1.2)), "chassis_black")
        flare = [v(side * (half + 0.02), yf + 0.52 * math.cos(a), axle_z + 0.52 * math.sin(a)) for a in [math.pi * k / 12 for k in range(13)]]
        hull.add(vk.sweep(flare, [(-0.035, -0.012), (0.035, -0.012), (0.035, 0.012), (-0.035, 0.012)], True, v(side, 0.0, 0.0)), "mud_rubber", None, 0.004)
    bonnet = vk.grid_sheet(1.04, 1.06, 8, 8, lambda x, y: 0.03 * (1.0 - (x / 0.52) ** 2) - 0.01 * max(0.0, (abs(y) - 0.45) / 0.08))
    vk.thicken(bonnet, 0.02)
    hull.add(bonnet, hull_looks["bonnet"], Matrix.Translation((0.0, -1.45, 1.2)))
    hull.add(vk.block(v(-0.52, front, 0.75), v(0.52, front + 0.04, 1.2)), "chassis_black", None, 0.005)
    vk.mesh_panel(frame, face_frame(v(0.0, front - 0.012, 0.97), v(0.0, -1.0, 0.0)), 0.92, 0.36, 0.03, 0.006, "mesh", 0.02)
    hull.add(vk.block(v(-half, -0.92, 1.18), v(half, -0.8, 1.34)), hull_looks["wing"], None, 0.008)
    for k in range(6):
        hull.add(vk.block(v(-0.5 + k * 0.2, -0.925, 1.24), v(-0.42 + k * 0.2, -0.915, 1.3)), "chassis_black")
    screen_frame = vk.about(v(0.0, -0.85, belt), X, -0.12)
    for x in (-half + 0.03, 0.0, half - 0.03):
        hull.add(vk.block(v(x - 0.03, -0.875, belt), v(x + 0.03, -0.825, roof - 0.02)), hull_looks["wing"], screen_frame, 0.006)
    for z in (belt + 0.01, roof - 0.05):
        hull.add(vk.block(v(-half, -0.875, z), v(half, -0.825, z + 0.05)), hull_looks["wing"], screen_frame, 0.006)
    for x0, x1, reach in ((-half + 0.06, -0.03, (0.08, 0.2)), (0.03, half - 0.06, (0.1, 0.3))):
        shattered_glass(hull, rng, [screen_frame @ v(x0, -0.849, belt + 0.06), screen_frame @ v(x1, -0.849, belt + 0.06), screen_frame @ v(x1, -0.849, roof - 0.05), screen_frame @ v(x0, -0.849, roof - 0.05)], reach)
    vk.mesh_panel(frame, screen_frame @ face_frame(v(0.0, -0.9, (belt + roof) * 0.5 - 0.01), v(0.0, -1.0, 0.0)), 1.66, 0.64, 0.045, 0.007, "mesh", 0.025)
    for x in (-0.7, 0.7):
        for z in (belt + 0.04, roof - 0.06):
            frame.add(vk.block(v(x - 0.03, -0.93, z - 0.02), v(x + 0.03, -0.86, z + 0.02)), "tube_steel", screen_frame, 0.003)
            vk.weld(frame, [screen_frame @ v(x - 0.03, -0.9, z + 0.025), screen_frame @ v(x + 0.03, -0.9, z + 0.025)], v(0.0, 0.0, 1.0), 0.006, int(x * 10 + z * 7), "weld")
    vk.text_mask("rover_number", 1.0, [("13", 0.62, 0.5, "STENCIL.TTF", 0.5, 0.9, 1.0, 1.05)])
    vk.register("armour_number", "metal", kind="steel", rust=0.6, dirt=0.7, text=("rover_number", (0.4, 0.39, 0.36), 0.0))
    vk.register("armour_plain", "metal", kind="steel", rust=0.65, dirt=0.7)
    for side in (-1.0, 1.0):
        door_look = hull_looks["door_l"] if side > 0 else hull_looks["door_r"]
        hull.add(vk.block(v(side * (half - 0.05), -0.8, floor + 0.02), v(side * half, 0.3, belt)), door_look, None, 0.006)
        hull.add(vk.block(v(side * (half - 0.04), -0.78, belt), v(side * half, -0.74, roof - 0.04)), door_look, None, 0.004)
        hull.add(vk.block(v(side * (half - 0.04), 0.26, belt), v(side * half, 0.3, roof - 0.04)), door_look, None, 0.004)
        hull.add(vk.block(v(side * (half - 0.04), -0.78, roof - 0.08), v(side * half, 0.3, roof - 0.04)), door_look, None, 0.004)
        normal = v(side, 0.0, 0.0)
        door_window = face_frame(v(side * (half + 0.006), -0.24, (belt + roof) * 0.5 - 0.02), normal)
        number = vk.label(v(side * (half + 0.012), -0.24, 0.98), Z.cross(normal), Z, 0.36, 0.36, 0.8)
        plate(hull, "armour_plain", door_window, 1.12, 0.66, 0.01, [(-0.1 if side > 0 else 0.1, 0.06, 0.34, 0.045)], True, "zinc", rng)
        plate(hull, "armour_number", face_frame(v(side * (half + 0.006), -0.24, 0.97), normal), 1.1, 0.42, 0.008, [], True, "zinc", rng, label=number)
        rear_window = face_frame(v(side * (half + 0.006), 1.18, (belt + roof) * 0.5 - 0.02), normal)
        plate(hull, "plate_rust" if side > 0 else "plate_steel", rear_window, 1.62, 0.64, 0.01, [(-0.45, 0.08, 0.28, 0.04), (0.35, 0.08, 0.28, 0.04)], False, "zinc", rng)
        stitch_welds(hull, rear_window, 1.62, 0.64, 0.01, ("top", "bottom", "left", "right"), 70 + int(side * 5))
        hull.add(vk.block(v(side * (half - 0.04), 0.3, roof - 0.08), v(side * half, back, roof - 0.04)), hull_looks["side"], None, 0.004)
        for y in (0.3, back - 0.02):
            hull.add(vk.block(v(side * (half - 0.04), y - 0.02, belt), v(side * half, y + 0.02, roof - 0.04)), hull_looks["side"], None, 0.004)
        body_side = vk.block(v(side * (half - 0.05), 0.3, floor + 0.02), v(side * half, back, belt))
        hull.add(vk.carve(body_side, [arch_cutter(side, yr, axle_z)]), hull_looks["side"], None, 0.006)
        skirt = vk.block(v(side * half, -0.8, 0.6), v(side * (half + 0.012), 2.0, 0.86))
        hull.add(vk.carve(skirt, [arch_cutter(side, yr, axle_z, 0.5), arch_cutter(side, yf, axle_z, 0.5)]), "plate_dark", None, 0.003)
        for y in [-0.7 + 0.2 * k for k in range(14)]:
            if abs(y - yr) > 0.56:
                vk.bolt(hull, v(side * (half + 0.012), y, 0.83), normal, 0.018, "zinc", False)
        rear_arch = [v(side * (half + 0.02), yr + 0.52 * math.cos(a), axle_z + 0.52 * math.sin(a)) for a in [math.pi * k / 12 for k in range(13)]]
        hull.add(vk.sweep(rear_arch, [(-0.035, -0.012), (0.035, -0.012), (0.035, 0.012), (-0.035, 0.012)], True, v(side, 0.0, 0.0)), "mud_rubber", None, 0.004)
        hull.add(vk.block(v(side * (half + 0.01), 0.1, belt - 0.13), v(side * (half + 0.03), 0.22, belt - 0.1)), "zinc", None, 0.003)
    for index in range(3):
        y = rng.uniform(0.6, 1.8)
        z = rng.uniform(0.9, 1.15)
        side = rng.choice((-1.0, 1.0))
        patch = face_frame(v(side * (half + 0.004), y, z), v(side, 0.0, 0.0))
        size = (rng.uniform(0.18, 0.32), rng.uniform(0.14, 0.24))
        hull.add(vk.cube(size[0], 0.004, size[1]), rng.choice(("primer_red", "plate_steel", "blue_panel")), patch, 0.002)
        for corner in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            vk.rivet(hull, patch @ v(corner[0] * (size[0] * 0.5 - 0.02), -0.002, corner[1] * (size[1] * 0.5 - 0.02)), v(side, 0.0, 0.0), 0.007, "steel")
    hull.add(vk.block(v(-half, -0.84, roof - 0.04), v(half, back, roof + 0.02)), hull_looks["roof"], None, 0.012, 2)
    hull.add(vk.block(v(-half + 0.02, -0.8, floor - 0.02), v(half - 0.02, back - 0.02, floor + 0.01)), "floor_plate")
    rear_door = face_frame(v(0.0, back + 0.006, 1.32), v(0.0, 1.0, 0.0))
    hull.add(vk.block(v(-half, back - 0.04, floor), v(half, back, roof - 0.03)), hull_looks["rear"], None, 0.006)
    plate(hull, "plate_steel", face_frame(v(0.0, back + 0.006, 1.62), v(0.0, 1.0, 0.0)), 1.0, 0.5, 0.01, [(-0.2, 0.05, 0.3, 0.04)], True, "zinc", rng)
    for x in (-0.72, 0.72):
        kit.add(vk.block(v(x - 0.05, back, 0.8), v(x + 0.05, back + 0.04, 1.0)), "lens_red", None, 0.008)
        kit.add(vk.block(v(x - 0.05, back, 1.0), v(x + 0.05, back + 0.04, 1.08)), "lens_amber", None, 0.006)
    for side in (-1.0, 1.0):
        hull.add(vk.block(v(side * 0.42, back - 0.02, 1.1), v(side * 0.44, back + 0.04, 1.4)), "zinc", None, 0.003)
    bar_y = -2.2
    for side in (-1.0, 1.0):
        tube_frame(frame, "tube_steel", [v(side * 0.42, -2.1, 0.5), v(side * 0.42, bar_y, 0.62), v(side * 0.42, bar_y - 0.02, 1.0), v(side * 0.4, bar_y + 0.02, 1.26)], 0.045, 10, True, 11 + int(side))
        tube_frame(frame, "tube_steel", [v(side * 0.42, bar_y - 0.012, 0.84), v(side * 0.68, bar_y + 0.05, 0.84), v(side * 0.82, -2.04, 0.84)], 0.035, 10, True, 21 + int(side))
        tube_frame(frame, "tube_steel", [v(side * 0.4, bar_y + 0.02, 1.26), v(side * 0.55, -2.04, 1.22), v(side * 0.62, -1.9, 1.21)], 0.035, 10, True, 31 + int(side))
    tube_frame(frame, "tube_steel", [v(-0.82, bar_y + 0.04, 0.62), v(0.82, bar_y + 0.04, 0.62)], 0.045, 10, False)
    tube_frame(frame, "tube_steel", [v(-0.42, bar_y, 1.0), v(0.42, bar_y, 1.0)], 0.04, 10, False)
    tube_frame(frame, "tube_steel", [v(-0.4, bar_y + 0.02, 1.26), v(0.4, bar_y + 0.02, 1.26)], 0.04, 10, False)
    ram = face_frame(v(0.0, bar_y - 0.05, 0.8), v(0.0, -1.0, 0.0))
    plate(frame, "plate_rust", ram, 0.8, 0.32, 0.012, [], True, "zinc", rng)
    stitch_welds(frame, ram, 0.8, 0.32, 0.012, ("top", "bottom"), 90)
    for k in range(7):
        x = -0.6 + k * 0.2
        vk.spike(frame, v(x, bar_y - 0.04, 0.62), v(0.0, -1.0, 0.15), 0.16, 0.026, "spike")
        vk.weld(frame, [v(x - 0.025, bar_y - 0.035, 0.6), v(x, bar_y - 0.04, 0.585), v(x + 0.025, bar_y - 0.035, 0.6)], v(0.0, -1.0, 0.0), 0.006, k, "weld")
    for k in range(5):
        x = -0.3 + k * 0.15
        vk.spike(frame, v(x, bar_y - 0.02, 1.27), v(0.0, -1.0, 0.45), 0.13, 0.022, "spike")
    frame.add(vk.block(v(-0.22, bar_y + 0.05, 0.7), v(0.22, -2.06, 0.9)), "chassis_black", None, 0.01)
    frame.add(vk.rod(v(-0.16, bar_y + 0.05, 0.8), v(0.16, bar_y + 0.05, 0.8), 0.07, 14), "chassis_black")
    vk.chain(kit, vk.sag(v(-0.5, bar_y - 0.05, 0.98), v(0.3, bar_y - 0.05, 0.98), 0.22, 12), 0.05, 0.008, "chain", 3)
    for side in (-1.0, 1.0):
        caged_lamp(frame, kit, v(side * 0.68, front - 0.02, 1.0), v(0.0, -1.0, 0.0), 0.085)
        kit.add(vk.block(v(side * 0.68 - 0.045, front - 0.02, 1.115), v(side * 0.68 + 0.045, front + 0.01, 1.165)), "lens_amber", None, 0.005)
    cage = 0.03
    for y, z_base in ((-0.78, 1.22), (0.33, 0.85), (1.95, 0.85)):
        for side in (-1.0, 1.0):
            tube_frame(frame, "tube_steel", [v(side * (half + 0.06), y, z_base), v(side * (half + 0.06), y, roof - 0.1), v(side * (half - 0.02), y, roof + 0.09)], cage, 8, True, int(y * 10) + int(side))
        tube_frame(frame, "tube_steel", [v(-half + 0.02, y, roof + 0.09), v(half - 0.02, y, roof + 0.09)], cage, 8, False)
    for side in (-1.0, 1.0):
        tube_frame(frame, "tube_steel", [v(side * (half - 0.02), -0.78, roof + 0.09), v(side * (half - 0.02), 1.95, roof + 0.09)], cage, 8, False)
        tube_frame(frame, "tube_steel", [v(side * (half + 0.06), -0.78, 1.22), v(side * 0.62, -1.75, 1.22), v(side * 0.42, bar_y + 0.04, 1.26)], cage, 8, True, 40 + int(side))
        tube_frame(frame, "tube_steel", [v(side * (half + 0.06), 0.33, 1.0), v(side * (half + 0.06), 1.95, 1.6)], cage, 8, False)
    tube_frame(frame, "tube_steel", [v(-half + 0.02, 1.95, roof + 0.09), v(half - 0.04, 1.95, 0.95)], cage, 8, False)
    rack_z = roof + 0.15
    for side in (-1.0, 1.0):
        frame.add(vk.block(v(side * 0.86 - 0.02, -0.7, rack_z - 0.02), v(side * 0.86 + 0.02, 1.88, rack_z + 0.02)), "tube_steel", None, 0.003)
        frame.add(vk.block(v(side * 0.86 - 0.015, -0.7, rack_z + 0.17), v(side * 0.86 + 0.015, 1.88, rack_z + 0.2)), "tube_steel", None, 0.003)
        for y in (-0.6, 0.0, 0.6, 1.2, 1.8):
            frame.add(vk.block(v(side * 0.86 - 0.012, y - 0.012, rack_z), v(side * 0.86 + 0.012, y + 0.012, rack_z + 0.18)), "tube_steel", None, 0.002)
    for y in (-0.7, -0.35, 0.0, 0.35, 0.7, 1.05, 1.4, 1.88):
        frame.add(vk.block(v(-0.86, y - 0.018, rack_z - 0.018), v(0.86, y + 0.018, rack_z + 0.018)), "tube_steel", None, 0.003)
    for y in (-0.78, 0.33, 1.95):
        for x in (-0.6, 0.6):
            frame.add(vk.block(v(x - 0.015, y - 0.015, roof + 0.09), v(x + 0.015, y + 0.015, rack_z - 0.018)), "tube_steel", None, 0.002)
    vk.mesh_panel(frame, Matrix.Translation((0.0, 0.59, rack_z + 0.02)) @ Matrix.Rotation(-math.pi * 0.5, 4, 'X'), 1.7, 2.56, 0.08, 0.006, "mesh")
    for index, (x, look) in enumerate(((-0.62, "can_olive"), (-0.42, "can_red"), (-0.22, "can_olive"))):
        jerrycan(kit, v(x, 1.55, rack_z + 0.025), 0.0 + rng.uniform(-0.05, 0.05), look, rng)
    vk.strap(kit, [v(-0.75, 1.36, rack_z + 0.02), v(-0.75, 1.36, rack_z + 0.47), v(-0.12, 1.36, rack_z + 0.47), v(-0.12, 1.36, rack_z + 0.02)], 0.04, 0.004, "strap", v(0.0, 1.0, 0.0))
    vk.register("ammo_can", "paint", color=(0.035, 0.045, 0.025), under=(0.1, 0.04, 0.025), primer=(0.1, 0.04, 0.025), chips=0.5, fade=0.4, chalk=0.2, bleed=0.5, gloss=0.6, dirt=0.65)
    for k, (x, y) in enumerate(((0.35, 1.6), (0.62, 1.55))):
        kit.add(vk.block(v(x - 0.14, y - 0.075, rack_z + 0.025), v(x + 0.14, y + 0.075, rack_z + 0.21)), "ammo_can", None, 0.01, 2)
        kit.add(vk.block(v(x - 0.06, y - 0.012, rack_z + 0.21), v(x + 0.06, y + 0.012, rack_z + 0.235)), "chassis_black", None, 0.004)
    rope_coil(kit, v(0.45, 1.02, rack_z + 0.026), 0.15, 0.012, 3.5, rng)
    vk.rope_line(kit, [v(-0.86, 1.25, rack_z + 0.2), v(-0.4, 1.3, rack_z + 0.5), v(0.2, 1.3, rack_z + 0.48), v(0.86, 1.25, rack_z + 0.2)], 0.01, "rope_old")
    vk.chain(kit, [v(0.86, -0.4, rack_z + 0.18), v(0.4, -0.1, rack_z + 0.42), v(-0.3, -0.05, rack_z + 0.42), v(-0.86, -0.4, rack_z + 0.18)], 0.05, 0.008, "chain", 9)
    stack_x = half + 0.11
    stack = [v(0.5, 0.42, 0.62), v(0.78, 0.42, 0.66), v(stack_x, 0.42, 0.8), v(stack_x, 0.42, 1.4), v(stack_x, 0.42, 2.45)]
    frame.add(vk.tube(g.spline(stack, 6), 0.045, 12, False), "heat_blue")
    tip = v(stack_x, 0.42, 2.56)
    frame.add(vk.cylinder(0.045, 0.11, 12, False), "heat_blue", vk.frame(v(stack_x, 0.42, 2.45), Z))
    flap = vk.lathe([(0.0, 0.0), (0.052, 0.0), (0.052, 0.006), (0.0, 0.006)], 12)
    kit.add(flap, "rust", Matrix.Translation(tip + v(0.0, -0.05, 0.0)) @ Matrix.Rotation(-0.7, 4, 'X') @ Matrix.Translation((0.0, 0.05, 0.0)))
    shield = g.revolve([(0.061, 0.0), (0.067, 0.0), (0.067, 0.55), (0.061, 0.55)], 16)
    slots = [g.transformed(g.box(0.05, 0.016, 0.04), Matrix.Rotation(tau * j / 6 + (0.5 if k % 2 else 0.0), 4, 'X') @ Matrix.Translation((0.08 + 0.09 * k, 0.0, 0.064))) for k in range(5) for j in range(6)]
    frame.add(vk.carve(shield, slots), "zinc", vk.frame(v(stack_x, 0.42, 1.45), Z))
    for z in (1.42, 2.02):
        vk.hose_clamp(frame, v(stack_x, 0.42, z), Z, 0.065, "zinc")
    for z in (1.3, 2.1):
        frame.add(vk.bar(v(half + 0.06, 0.42, z), v(stack_x, 0.42, z), 0.03, 0.012), "tube_steel", None, 0.002)
    m.point("exhaust", tip)
    for side in (-1.0, 1.0):
        for y in (yf + 0.55, yr + 0.55):
            frame.add(vk.block(v(side * 0.62, y - 0.02, 0.6), v(side * 0.9, y + 0.02, 0.64)), "plate_steel", None, 0.003)
            flap_matrix = Matrix.Translation((side * 0.76, y + 0.012, 0.42)) @ Matrix.Rotation(rng.uniform(-0.06, 0.06), 4, 'Y')
            kit.add(vk.cube(0.3, 0.012, 0.4), "mud_rubber", flap_matrix, 0.004)
            for x in (-0.1, 0.0, 0.1):
                vk.bolt(kit, flap_matrix @ v(x, -0.006, 0.17), v(0.0, -1.0, 0.0), 0.016, "zinc", False)
        frame.add(vk.block(v(side * 0.86, -0.72, 0.56), v(side * 0.96, 0.22, 0.58)), "floor_plate", None, 0.003)
        for y in (-0.6, 0.1):
            frame.add(vk.block(v(side * 0.6, y - 0.02, 0.5), v(side * 0.9, y + 0.02, 0.57)), "chassis_black", None, 0.003)
    frame.add(vk.block(v(-0.82, 2.1, 0.47), v(0.82, 2.24, 0.62)), "plate_steel", None, 0.01)
    frame.add(vk.block(v(-0.1, 2.24, 0.42), v(0.1, 2.28, 0.62)), "plate_steel", None, 0.006)
    hook = [v(0.0, 2.28, 0.5), v(0.0, 2.36, 0.5), v(0.0, 2.39, 0.47), v(0.0, 2.37, 0.43), v(0.0, 2.33, 0.44)]
    frame.add(vk.tube(g.spline(hook, 5), 0.022, 8), "chassis_black")
    frame.add(vk.block(v(-0.04, 2.28, 0.51), v(0.04, 2.36, 0.53)), "chassis_black", None, 0.004)
    for side in (-1.0, 1.0):
        vk.chain(kit, vk.sag(v(side * 0.12, 2.26, 0.5), v(side * 0.05, 2.33, 0.45), 0.08, 6), 0.04, 0.007, "chain", 5)
        frame.add(vk.lathe([(0.03, -0.02), (0.045, -0.02), (0.045, 0.02), (0.03, 0.02)], 10, closed=True), "chassis_black", vk.frame(v(side * 0.6, 2.25, 0.55), Y))
    seat_y = -0.08
    for side in (-1.0, 1.0):
        x = side * 0.42
        cab.add(vk.block(v(x - 0.22, seat_y - 0.24, floor), v(x + 0.22, seat_y + 0.24, floor + 0.24)), "dash_paint", None, 0.01)
        cab.add(vk.pillow(0.48, 0.5, 0.12, rng, 0.35, 0.02, 0.1), "seat_canvas", Matrix.Translation((x, seat_y, floor + 0.3)))
        cab.add(vk.pillow(0.48, 0.13, 0.62, rng, 0.35, 0.0, 0.06), "seat_canvas", Matrix.Translation((x, seat_y + 0.28, floor + 0.66)) @ Matrix.Rotation(-0.18, 4, 'X'))
    eye = 1.76
    m.point("seat_driver", v(-0.42, seat_y - 0.05, eye))
    m.point("seat_passenger", v(0.42, seat_y - 0.05, eye))
    cab.add(vk.block(v(-half + 0.04, -0.82, 1.0), v(half - 0.04, -0.62, 1.2)), "dash_paint", None, 0.012, 2)
    cab.add(vk.block(v(-0.62, -0.68, 1.12), v(-0.2, -0.6, 1.28)), "dash_paint", None, 0.01)
    for k, x in enumerate((-0.52, -0.42, -0.32)):
        cab.add(vk.lathe([(0.0, 0.0), (0.04, 0.0), (0.04, 0.012), (0.0, 0.012)], 14), "gauge", vk.frame(v(x, -0.598, 1.2), v(0.0, 1.0, 0.0)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
    hub = v(-0.42, -0.42, 1.42)
    axis = v(0.0, 0.8, 0.6).normalized()
    cab.add(vk.rod(hub - axis * 0.4, hub - axis * 0.05, 0.03, 10), "dash_paint")
    steering = m.part("steering", 40.0, hub)
    wheel_frame = vk.frame(hub, axis)
    ring = [v(0.0, 0.2 * math.cos(tau * k / 24), 0.2 * math.sin(tau * k / 24)) for k in range(24)]
    steering.add(g.sweep([wheel_frame @ p for p in ring], g.circle(0.016, 7), closed=True, planar=axis), "seat_vinyl")
    for angle in (math.pi * 0.5, math.pi * 0.5 + tau / 3.0, math.pi * 0.5 + 2.0 * tau / 3.0):
        steering.add(vk.bar(wheel_frame @ v(-0.01, 0.0, 0.0), wheel_frame @ v(-0.01, 0.19 * math.cos(angle), 0.19 * math.sin(angle)), 0.03, 0.01, axis), "dash_paint", None, 0.002)
    steering.add(vk.cylinder(0.05, 0.06, 14), "dash_paint", wheel_frame @ Matrix.Translation((-0.04, 0.0, 0.0)))
    m.manifest["steering"] = {"part": "steering", "hub": vk.triple(hub), "axis_toward_driver": vk.triple(axis), "rim_radius": 0.2}
    for x, length in ((0.0, 0.45), (0.12, 0.35)):
        cab.add(vk.rod(v(x, -0.45, floor + 0.04), v(x - 0.03, -0.38, floor + length), 0.01, 6), "steel")
        cab.add(g.sphere(0.025, 10, 6), "dash_paint", Matrix.Translation((x - 0.03, -0.38, floor + length)))
    cab.add(vk.block(v(-0.18, -0.85, floor), v(0.18, 0.6, floor + 0.18)), "floor_plate", None, 0.02)
    for x in (-0.5, -0.38, -0.26):
        cab.add(vk.block(v(x - 0.04, -0.72, floor + 0.05), v(x + 0.04, -0.66, floor + 0.12)), "steel", None, 0.004)
    for k in range(3):
        kit.add(vk.block(v(-0.6 + k * 0.4, 0.9, floor + 0.01), v(-0.3 + k * 0.4, 1.3, floor + 0.3)), "ammo_can", None, 0.01)
    vk.register("shovel_blade", "metal", kind="steel", rust=0.7, dirt=0.7)
    shovel = Matrix.Translation((-half - 0.015, 1.1, 1.05)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Z') @ Matrix.Rotation(-0.05, 4, 'Y')
    kit.add(vk.rod(v(-0.55, 0.0, 0.0), v(0.35, 0.0, 0.0), 0.018, 8), "wood_handle", shovel)
    kit.add(vk.cube(0.28, 0.008, 0.22), "shovel_blade", shovel @ Matrix.Translation((0.48, 0.0, 0.0)), 0.003)
    for y in (0.85, 1.35):
        kit.add(vk.block(v(-half - 0.03, y - 0.02, 1.0), v(-half, y + 0.02, 1.1)), "chassis_black", None, 0.002)
    kit.add(vk.rod(v(-half + 0.05, -0.75, roof + 0.02), v(-half + 0.1, -0.6, roof + 1.25), 0.004, 5), "steel")
    wheels = {}
    for key, y, side in (("wheel_fl", yf, 1.0), ("wheel_fr", yf, -1.0), ("wheel_rl", yr, 1.0), ("wheel_rr", yr, -1.0)):
        wheels[key] = (v(side * track, y, axle_z), side)
    rover_wheel(m, "wheel_fl", wheels["wheel_fl"][0], 1.0)
    m.wheels = wheels
    m.spare = Matrix.Translation((0.25, 0.25, rack_z + 0.17)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y')
    m.sets = [("veh_rover_hull", ["rover_hull"]), ("veh_rover_frame", ["rover_frame"]), ("veh_rover_cab", ["rover_cab", "steering"]), ("veh_rover_kit", ["rover_kit"]), ("veh_rover_wheel", ["wheel_fl"])]
    m.body_parts = ["rover_hull", "rover_frame", "rover_cab", "rover_kit"]
    m.wheel_set = "veh_rover_wheel"
    lamp_y = front - 0.02 - 0.03
    m.point("light_head_l", v(0.68, lamp_y, 1.0))
    m.point("light_head_r", v(-0.68, lamp_y, 1.0))
    m.col((-0.92, -2.0, 0.45), (0.92, back, roof + 0.02))
    m.col((-0.88, -0.78, roof + 0.02), (0.88, 1.95, rack_z + 0.5))
    m.col((-0.85, -2.36, 0.42), (0.85, -2.0, 1.3))
    m.col((-0.82, back, 0.42), (0.82, 2.4, 0.66))
    m.col((stack_x - 0.06, 0.36, 0.6), (stack_x + 0.07, 0.48, 2.56))
    m.manifest.update({
        "wheelbase": wheelbase, "track": track * 2.0, "wheel_radius": radius, "tyre_width": 0.27,
        "ride_height": {"wheel_centre": axle_z, "chassis_rail_bottom": 0.47, "floor": floor, "roof": roof, "rack_top": round(rack_z + 0.5, 3)},
        "mass_kg": 2850, "mass_note": "Land Rover 110 hardtop kerb weight about 1900 kg plus about 950 kg of armour plate, cage, bull bar, rack, spare wheel and cargo",
        "centre_of_mass": [0.0, 0.05, 0.95],
        "lights": {"light_head_l": {"position": vk.triple(v(0.68, lamp_y, 1.0)), "direction": [0.0, -1.0, 0.0], "kind": "headlight"}, "light_head_r": {"position": vk.triple(v(-0.68, lamp_y, 1.0)), "direction": [0.0, -1.0, 0.0], "kind": "headlight"}},
        "exhaust": {"position": vk.triple(tip), "direction": [0.0, 0.0, 1.0]},
        "seats": {"seat_driver": vk.triple(v(-0.42, seat_y - 0.05, eye)), "seat_passenger": vk.triple(v(0.42, seat_y - 0.05, eye))},
    })
    m.close(v(2.2, -4.4, 2.2), v(0.0, -1.6, 1.0), 40.0)
    m.close(v(1.3, -3.0, 1.3), v(0.4, -2.1, 0.85), 45.0)
    m.close(v(1.8, 0.9, 3.4), v(0.0, 1.2, 2.3), 40.0)
    m.close(v(2.0, -1.6, 0.7), v(track, yf, axle_z), 40.0)
    m.close(v(-1.6, -0.2, 1.75), v(-0.4, -0.4, 1.3), 50.0)
    m.close(v(1.2, 3.8, 1.0), v(0.0, 2.2, 0.6), 40.0)
    return m


def rover_far(m):
    body = m.far("body")
    body.add(vk.block(v(-0.84, -2.0, 0.74), v(0.84, -0.9, 1.22)), "steel")
    body.add(vk.block(v(-0.84, -0.9, 0.74), v(0.84, 2.06, 1.98)), "steel")
    body.add(vk.block(v(-0.86, -0.7, 2.1), v(0.86, 1.9, 2.32)), "steel")
    body.add(vk.block(v(-0.44, -2.14, 0.47), v(0.44, 2.2, 0.74)), "steel")
    body.add(vk.block(v(-0.8, -2.26, 0.58), v(0.8, -2.0, 1.28)), "steel")
    body.add(vk.block(v(0.9, 0.38, 0.8), v(1.0, 0.48, 2.56)), "steel")
    body.add(vk.lathe([(0.0, -0.13), (0.4, -0.13), (0.4, 0.13), (0.0, 0.13)], 10), "steel", m.spare)
    center, side = m.wheels["wheel_fl"]
    far_wheel = m.far("wheel_fl", 40.0, center)
    far_wheel.add(vk.cylinder(0.4, 0.27, 12), "steel", Matrix.Translation(center - X * 0.135))
    far_wheel.add(vk.cylinder(0.2, 0.02, 10), "steel", Matrix.Translation(center + X * 0.135))


def heli():
    m = model("veh_heli", 601)
    rng = m.rng
    hull = m.part("heli_hull", 36.0)
    frame = m.part("heli_frame", 40.0)
    engine = m.part("heli_engine", 40.0)
    mast_hub = v(0.0, 0.25, 2.62)
    tail_hub = v(0.33, 6.22, 1.93)
    blade_radius = 4.0
    tail_radius = 0.7
    floor = 0.66
    for side in (-1.0, 1.0):
        skid = [v(side * 1.0, -1.85, 0.32), v(side * 1.0, -1.72, 0.12), v(side * 1.0, -1.5, 0.045), v(side * 1.0, 1.95, 0.045), v(side * 1.0, 2.05, 0.06)]
        frame.add(vk.tube(g.spline(skid, 6), 0.042, 10), "tube_steel")
        for y in (-0.9, 1.15):
            cross = [v(side * 1.0, y, 0.06), v(side * 0.96, y, 0.36), v(side * 0.78, y, floor - 0.04), v(side * 0.55, y, floor - 0.02)]
            frame.add(vk.tube(g.spline(cross, 5), 0.045, 10), "tube_steel")
            weld_ring(frame, v(side * 1.0, y, 0.08), Z, 0.042, int(y * 10))
        for y in (-1.3, 1.6):
            frame.add(vk.block(v(side * 1.0 - 0.025, y - 0.04, 0.0), v(side * 1.0 + 0.025, y + 0.04, 0.012)), "plate_steel", None, 0.003)
    for y in (-0.9, 1.15):
        frame.add(vk.rod(v(-0.56, y, floor - 0.02), v(0.56, y, floor - 0.02), 0.045, 10), "tube_steel")
    pod = [(-2.55, 0.42, 0.95, 1.45), (-2.3, 0.6, 0.78, 1.75), (-1.8, 0.74, 0.68, 2.0), (-1.0, 0.76, 0.66, 2.05), (0.1, 0.74, 0.66, 2.0)]
    for side in (-1.0, 1.0):
        rail_low = [v(side * w, y, z0) for y, w, z0, z1 in pod]
        rail_mid = [v(side * w, y, z0 + (z1 - z0) * 0.45) for y, w, z0, z1 in pod]
        rail_top = [v(side * w * 0.88, y, z1) for y, w, z0, z1 in pod]
        for rail in (rail_low, rail_mid, rail_top):
            tube_frame(frame, "tube_steel", rail, 0.024, 8, True, 61)
        for y, w, z0, z1 in pod:
            tube_frame(frame, "tube_steel", [v(side * w, y, z0), v(side * w, y, z0 + (z1 - z0) * 0.45), v(side * w * 0.88, y, z1)], 0.022, 8, False)
    for y, w, z0, z1 in pod[1:]:
        tube_frame(frame, "tube_steel", [v(-w * 0.88, y, z1), v(w * 0.88, y, z1)], 0.022, 8, False)
        tube_frame(frame, "tube_steel", [v(-w, y, z0), v(w, y, z0)], 0.022, 8, False)
    looks = ["olive", "primer_red", "plate_steel", "blue_panel", "olive", "plate_rust"]
    for side in (-1.0, 1.0):
        for index in range(len(pod) - 1):
            y0, w0, b0, t0 = pod[index]
            y1, w1, b1, t1 = pod[index + 1]
            look = looks[(index + (1 if side > 0 else 3)) % len(looks)]
            mid0 = b0 + (t0 - b0) * 0.45
            mid1 = b1 + (t1 - b1) * 0.45
            quad = [v(side * (w0 + 0.012), y0, b0), v(side * (w1 + 0.012), y1, b1), v(side * (w1 + 0.012), y1, mid1), v(side * (w0 + 0.012), y0, mid0)]
            panel = bmesh.new()
            verts = [panel.verts.new(p) for p in quad]
            panel.faces.new(verts if side > 0 else list(reversed(verts)))
            vk.thicken(panel, 0.008)
            hull.add(panel, look, None, 0.002, tint=(rng.uniform(0.85, 1.1),) * 3)
            for t in (0.15, 0.5, 0.85):
                for p0, p1 in ((quad[0], quad[1]), (quad[3], quad[2])):
                    vk.rivet(hull, p0.lerp(p1, t) + v(side * 0.006, 0.0, 0.015 if p0 == quad[0] else -0.015), v(side, 0.0, 0.0), 0.007, "steel")
    belly = bmesh.new()
    ring = [belly.verts.new(v(w * s, y, z0 - 0.01)) for y, w, z0, z1 in pod for s in (-1.0, 1.0)]
    for index in range(len(pod) - 1):
        a, b = ring[index * 2], ring[index * 2 + 1]
        c, d = ring[index * 2 + 2], ring[index * 2 + 3]
        belly.faces.new((a, c, d, b))
    vk.thicken(belly, 0.01)
    hull.add(belly, "plate_dark", None, 0.002)
    nose = pod[0]
    vk.text_mask("heli_nose", 1.6, [("ZP-07", 0.5, 0.5, "STENCIL.TTF", 0.8, 1.45)])
    vk.register("nose_paint", "paint", color=(0.045, 0.055, 0.028), under=(0.25, 0.19, 0.11), primer=(0.14, 0.05, 0.03), chips=0.55, fade=0.45, chalk=0.25, bleed=0.55, streaks=0.65, gloss=0.65, dirt=0.7, dents=0.9, text=("heli_nose", (0.38, 0.37, 0.33), 0.0))
    nose_frame = face_frame(v(0.0, nose[0] - 0.012, (nose[2] + nose[3]) * 0.5 - 0.15), v(0.0, -1.0, 0.25))
    plate(hull, "nose_paint", nose_frame, 0.78, 0.42, 0.01, [(-0.18, 0.12, 0.26, 0.04), (0.18, 0.12, 0.26, 0.04)], True, "zinc", rng, label=vk.label(nose_frame @ v(0.0, -0.006, -0.05), X, (nose_frame.to_3x3() @ Z), 0.5, 0.31, 0.7))
    front_y, front_w, front_z0, front_z1 = pod[1]
    screen = [v(-0.66, -2.3, 1.35), v(0.66, -2.3, 1.35), v(0.6, -1.85, 1.98), v(-0.6, -1.85, 1.98)]
    for half_index, (x0, x1) in enumerate(((-0.66, 0.0), (0.0, 0.66))):
        corners = [screen[0].lerp(screen[1], (x0 + 0.66) / 1.32), screen[0].lerp(screen[1], (x1 + 0.66) / 1.32), screen[3].lerp(screen[2], (x1 + 0.66) / 1.32), screen[3].lerp(screen[2], (x0 + 0.66) / 1.32)]
        center = sum(corners, Vector()) / 4.0
        normal = (corners[1] - corners[0]).cross(corners[3] - corners[0]).normalized()
        if normal.y > 0.0:
            normal = -normal
        if half_index == 1:
            panel_frame = face_frame(center, normal, (corners[3] - corners[0]).normalized())
            plate(hull, "plate_steel", panel_frame, (corners[1] - corners[0]).length, (corners[3] - corners[0]).length, 0.01, [(0.0, 0.05, 0.38, 0.05)], False, "zinc", rng)
            stitch_welds(hull, panel_frame, (corners[1] - corners[0]).length, (corners[3] - corners[0]).length, 0.01, ("top", "bottom", "left", "right"), 120)
        else:
            shattered_glass(hull, rng, [p - normal * 0.01 for p in corners], (0.08, 0.22))
            vk.mesh_panel(frame, face_frame(center + normal * 0.03, normal, (corners[3] - corners[0]).normalized()), (corners[1] - corners[0]).length, (corners[3] - corners[0]).length, 0.05, 0.006, "mesh", 0.02)
    for side in (-1.0, 1.0):
        y0, w0, b0, t0 = pod[2]
        y1, w1, b1, t1 = pod[3]
        mid0 = b0 + (t0 - b0) * 0.45
        if side < 0:
            vk.mesh_panel(frame, face_frame(v(side * (w0 + 0.03), (y0 + y1) * 0.5, (mid0 + t0) * 0.5 + 0.02), v(side, 0.0, 0.12)), 0.72, 0.56, 0.06, 0.006, "mesh", 0.02)
    hull.add(vk.block(v(-0.66, -1.85, 2.0), v(0.66, 0.1, 2.04)), "olive", None, 0.006)
    hull.add(vk.block(v(-0.74, -1.85, floor - 0.02), v(0.74, 0.1, floor + 0.01)), "floor_plate")
    seat_y = -1.15
    eye = 1.74
    for side, name in ((-1.0, "seat_pilot"), (1.0, "seat_passenger")):
        x = side * 0.35
        engine.add(vk.block(v(x - 0.2, seat_y - 0.22, floor), v(x + 0.2, seat_y + 0.22, floor + 0.26)), "dash_paint", None, 0.01)
        engine.add(vk.pillow(0.44, 0.46, 0.11, rng, 0.35, 0.02, 0.1), "seat_canvas", Matrix.Translation((x, seat_y, floor + 0.31)))
        engine.add(vk.pillow(0.44, 0.12, 0.6, rng, 0.35, 0.0, 0.06), "seat_canvas", Matrix.Translation((x, seat_y + 0.26, floor + 0.66)) @ Matrix.Rotation(-0.15, 4, 'X'))
        vk.strap(engine, [v(x - 0.15, seat_y + 0.3, floor + 0.95), v(x - 0.1, seat_y + 0.05, floor + 0.55), v(x, seat_y - 0.1, floor + 0.36)], 0.045, 0.004, "strap", v(0.0, 1.0, 0.0))
        m.point(name, v(x, seat_y - 0.05, eye))
        engine.add(vk.rod(v(x, seat_y - 0.35, floor + 0.02), v(x, seat_y - 0.45, floor + 0.62), 0.014, 8), "dash_paint")
        engine.add(g.sphere(0.03, 10, 6), "engine_black", Matrix.Translation((x, seat_y - 0.45, floor + 0.63)))
        for dx in (-0.1, 0.1):
            engine.add(vk.block(v(x + dx - 0.04, -1.85, floor + 0.02), v(x + dx + 0.04, -1.72, floor + 0.06)), "steel", None, 0.004)
    engine.add(vk.rod(v(-0.12, seat_y + 0.0, floor + 0.05), v(-0.12, seat_y - 0.45, floor + 0.42), 0.014, 8), "dash_paint")
    engine.add(vk.block(v(-0.6, -1.95, 1.18), v(0.6, -1.78, 1.38)), "dash_paint", None, 0.012, 2)
    for k, x in enumerate((-0.45, -0.3, -0.15, 0.15, 0.3)):
        engine.add(vk.lathe([(0.0, 0.0), (0.045, 0.0), (0.045, 0.012), (0.0, 0.012)], 14), "gauge", vk.frame(v(x, -1.775, 1.29), v(0.0, 1.0, 0.0)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
    deck = (0.1, 1.7)
    engine.add(vk.block(v(-0.6, deck[0], floor + 0.02), v(0.6, deck[1], floor + 0.1)), "floor_plate", None, 0.008)
    for side in (-1.0, 1.0):
        tube_frame(frame, "tube_steel", [v(side * 0.74, 0.1, floor), v(side * 0.62, 1.7, floor + 0.1)], 0.03, 8, False)
        tube_frame(frame, "tube_steel", [v(side * 0.65, 0.1, 2.0), v(side * 0.4, 0.9, 2.15), v(side * 0.25, 1.7, 2.05)], 0.03, 8, True, 71)
        for y in (0.1, 0.9, 1.7):
            top = 2.0 if y < 0.5 else (2.15 if y < 1.2 else 2.05)
            tube_frame(frame, "tube_steel", [v(side * (0.74 if y < 0.5 else 0.62), y, floor), v(side * (0.65 if y < 0.5 else (0.4 if y < 1.2 else 0.25)), y, top)], 0.028, 8, False)
    block_center = v(0.0, 0.95, 1.05)
    engine.add(vk.block(block_center + v(-0.22, -0.4, -0.18), block_center + v(0.22, 0.4, 0.14)), "engine_alloy", None, 0.02, 2)
    for side in (-1.0, 1.0):
        for k in range(3):
            cylinder_center = block_center + v(side * 0.32, -0.28 + k * 0.28, 0.0)
            engine.add(vk.cylinder(0.075, 0.22, 14), "engine_black", vk.frame(block_center + v(side * 0.2, -0.28 + k * 0.28, 0.0), v(side, 0.0, 0.0)))
            for f in range(5):
                engine.add(vk.cylinder(0.095, 0.006, 14), "engine_black", vk.frame(block_center + v(side * (0.23 + f * 0.035), -0.28 + k * 0.28, 0.0), v(side, 0.0, 0.0)))
            engine.add(vk.block(cylinder_center + v(side * 0.06 - 0.05, -0.07, 0.05), cylinder_center + v(side * 0.06 + 0.05, 0.07, 0.13)), "engine_alloy", None, 0.01)
            pipe = [cylinder_center + v(side * 0.05, 0.0, -0.08), cylinder_center + v(side * 0.1, 0.05, -0.16), block_center + v(side * 0.38, 0.45, -0.12), block_center + v(side * 0.4, 0.62, 0.15), block_center + v(side * 0.42, 0.7, 0.62)]
            engine.add(vk.tube(g.spline(pipe, 4), 0.022, 8, False), "heat_blue")
        exhaust_tip = block_center + v(side * 0.42, 0.7, 0.62)
        engine.add(vk.cylinder(0.04, 0.2, 10, False), "heat_blue", vk.frame(exhaust_tip - v(0.0, 0.02, 0.18), v(0.0, 0.1, 1.0)))
        vk.hose_clamp(engine, exhaust_tip - v(0.0, 0.0, 0.12), Z, 0.04, "zinc")
    engine.add(vk.cylinder(0.12, 0.08, 18), "engine_black", vk.frame(block_center + v(0.0, -0.44, 0.0), v(0.0, -1.0, 0.0)))
    engine.add(vk.block(block_center + v(-0.1, 0.4, -0.1), block_center + v(0.1, 0.62, 0.1)), "engine_black", None, 0.012)
    gearbox = v(0.0, 0.25, 1.85)
    engine.add(vk.lathe([(0.0, -0.18), (0.16, -0.18), (0.2, -0.08), (0.2, 0.06), (0.14, 0.14), (0.07, 0.17), (0.0, 0.17)], 18), "engine_alloy", Matrix.Translation(gearbox))
    engine.add(vk.rod(gearbox + v(0.0, 0.0, 0.1), mast_hub - v(0.0, 0.0, 0.18), 0.055, 14), "steel")
    engine.add(vk.lathe([(0.06, 0.0), (0.2, 0.0), (0.2, 0.03), (0.06, 0.03)], 20), "zinc", Matrix.Translation(mast_hub - v(0.0, 0.0, 0.33)))
    for k in range(3):
        angle = tau * k / 3 + 0.5
        engine.add(vk.rod(gearbox + v(math.cos(angle) * 0.18, math.sin(angle) * 0.18, -0.15), v(math.cos(angle) * 0.6, 0.25 + math.sin(angle) * 0.6, floor + 0.1), 0.022, 8), "tube_steel")
    engine.add(vk.rod(block_center + v(0.0, -0.42, 0.0), gearbox + v(0.0, -0.05, -0.15), 0.03, 8), "steel")
    vk.register("tank_paint", "paint", color=(0.22, 0.02, 0.012), under=(0.12, 0.12, 0.11), primer=(0.12, 0.05, 0.03), chips=0.55, fade=0.5, chalk=0.25, bleed=0.6, streaks=0.6, gloss=0.6, dirt=0.75, dents=0.7)
    tank = vk.frame(v(-0.62, 0.55, floor + 0.36), v(0.0, 1.0, 0.0))
    engine.add(vk.lathe([(0.0, 0.0), (0.27, 0.0), (0.29, 0.02), (0.29, 0.1), (0.28, 0.12), (0.29, 0.14), (0.29, 0.72), (0.28, 0.74), (0.29, 0.76), (0.29, 0.84), (0.27, 0.86), (0.0, 0.86)], 20), "tank_paint", tank @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
    for y in (0.25, 0.7):
        vk.strap(engine, [v(-0.33, 0.55 + y, floor + 0.07), v(-0.33, 0.55 + y, floor + 0.66), v(-0.92, 0.55 + y, floor + 0.66), v(-0.92, 0.55 + y, floor + 0.07)], 0.04, 0.004, "strap", v(0.0, 1.0, 0.0))
    engine.add(vk.tube([v(-0.62, 0.55, floor + 0.62), v(-0.4, 0.8, floor + 0.7), block_center + v(-0.15, -0.2, 0.15)], 0.01, 6), "rubber")
    boom_start = 1.6
    boom_end = 6.3
    nodes = 7
    for k in range(nodes + 1):
        t = k / nodes
        y = boom_start + (boom_end - boom_start) * t
        width = 0.36 * (1.0 - t) + 0.12 * t
        top = 2.05 - 0.05 * t
        bottom = 1.5 + 0.28 * t
        points = [v(-width, y, bottom), v(width, y, bottom), v(0.0, y, top)]
        if k < nodes:
            t2 = (k + 1) / nodes
            y2 = boom_start + (boom_end - boom_start) * t2
            width2 = 0.36 * (1.0 - t2) + 0.12 * t2
            top2 = 2.05 - 0.05 * t2
            bottom2 = 1.5 + 0.28 * t2
            nxt = [v(-width2, y2, bottom2), v(width2, y2, bottom2), v(0.0, y2, top2)]
            for a, b in zip(points, nxt):
                frame.add(vk.rod(a, b, 0.026, 8), "tube_steel")
            frame.add(vk.rod(points[0], nxt[2], 0.016, 6), "tube_steel")
            frame.add(vk.rod(points[1], nxt[2], 0.016, 6), "tube_steel")
            frame.add(vk.rod(points[0], nxt[1], 0.016, 6), "tube_steel")
        for a, b in ((points[0], points[1]), (points[1], points[2]), (points[2], points[0])):
            frame.add(vk.rod(a, b, 0.018, 6), "tube_steel")
        for p in points:
            frame.add(g.sphere(0.034, 8, 6), "weld", Matrix.Translation(p))
    shaft = [v(0.0, 0.55, 1.85), v(0.0, boom_end - 0.05, 2.0)]
    frame.add(vk.rod(shaft[0], shaft[1], 0.02, 8), "steel")
    for k in range(5):
        y = 2.0 + k * 0.9
        frame.add(vk.block(v(-0.03, y - 0.03, 1.95), v(0.03, y + 0.03, 2.04)), "zinc", None, 0.003)
    tail_box = v(0.12, boom_end, 1.93)
    engine.add(vk.block(tail_box + v(-0.12, -0.12, -0.1), tail_box + v(0.12, 0.12, 0.1)), "engine_alloy", None, 0.02, 2)
    engine.add(vk.rod(tail_box + v(0.12, 0.0, 0.0), tail_hub - v(0.04, 0.0, 0.0), 0.025, 10), "steel")
    fin = [(boom_end - 0.35, 1.78), (boom_end + 0.25, 1.75), (boom_end + 0.42, 2.95), (boom_end + 0.15, 2.95), (boom_end - 0.3, 2.05)]
    vk.register("fin_paint", "paint", color=(0.22, 0.02, 0.012), under=(0.2, 0.2, 0.19), primer=(0.14, 0.05, 0.03), chips=0.55, fade=0.55, chalk=0.3, bleed=0.6, streaks=0.65, gloss=0.65, dirt=0.65, dents=0.7)
    fin_frame = Matrix(((0.0, 0.0, 1.0, -0.05), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
    hull.add(vk.slab(fin, 0.012), "fin_paint", fin_frame, 0.003)
    for k in range(6):
        y = boom_end - 0.25 + k * 0.12
        vk.rivet(hull, v(-0.058, y, 1.82 + k * 0.17), v(-1.0, 0.0, 0.0), 0.006, "steel")
    for side in (-1.0, 1.0):
        stab = [(side * x, y) for x, y in ((0.0, -0.18), (0.62, -0.12), (0.62, 0.06), (0.0, 0.12))]
        hull.add(vk.slab(stab if side > 0 else list(reversed(stab)), 0.01), "olive", Matrix.Translation((side * 0.12, boom_end - 1.1, 1.78)), 0.003)
    skid_guard = [v(0.0, boom_end - 0.4, 1.78), v(0.0, boom_end + 0.1, 1.15), v(0.0, boom_end + 0.4, 1.2), v(0.0, boom_end + 0.3, 1.76)]
    frame.add(vk.tube(g.spline(skid_guard, 5), 0.018, 8, True), "tube_steel")
    rotor = m.part("rotor_main", 40.0, mast_hub)
    rotor.add(vk.lathe([(0.0, -0.3), (0.09, -0.3), (0.09, -0.06), (0.14, -0.05), (0.14, 0.06), (0.08, 0.08), (0.0, 0.1)], 16), "engine_alloy", Matrix.Translation(mast_hub))
    rotor.add(vk.lathe([(0.07, 0.0), (0.21, 0.0), (0.21, 0.025), (0.07, 0.025)], 20), "engine_alloy", Matrix.Translation(mast_hub - v(0.0, 0.0, 0.28)))
    rotor.add(vk.block(v(-0.5, -0.06, -0.04), v(0.5, 0.06, 0.04)), "engine_alloy", Matrix.Translation(mast_hub), 0.01)
    airfoil = [(0.5, 0.0), (0.35, 0.012), (0.1, 0.022), (-0.15, 0.024), (-0.38, 0.016), (-0.5, 0.0), (-0.38, -0.01), (-0.15, -0.014), (0.1, -0.012), (0.35, -0.006)]
    for side in (-1.0, 1.0):
        rotor.add(vk.rod(mast_hub + v(side * 0.2, 0.05, -0.27), mast_hub + v(side * 0.28, 0.05, -0.02), 0.012, 6), "steel")
        rotor.add(vk.block(v(-0.08, -0.07, -0.05), v(0.08, 0.07, 0.05)), "engine_alloy", Matrix.Translation(mast_hub + v(side * 0.55, 0.0, 0.0)), 0.01)
        for k, (start, end, look) in enumerate(((0.62, blade_radius - 0.35, "blade_paint"), (blade_radius - 0.35, blade_radius, "blade_tip"))):
            stations = 10 if k == 0 else 3
            path = [mast_hub + v(side * (start + (end - start) * s / stations), 0.0, 0.0) for s in range(stations + 1)]
            chord = 0.26
            profile = [(px * chord, py) for px, py in airfoil]
            blade = g.sweep(path, profile, closed=False, planar=Z, caps=True)
            rotor.add(blade, look, None, 0.0)
        rotor.add(vk.block(v(-0.18, -0.13, -0.035), v(0.18, 0.13, 0.035)), "plate_steel", Matrix.Translation(mast_hub + v(side * 0.75, 0.0, 0.0)), 0.006)
        for dx in (-0.12, 0.0, 0.12):
            vk.bolt(rotor, mast_hub + v(side * 0.75 + dx, 0.08, 0.035), Z, 0.018, "zinc", False)
            vk.bolt(rotor, mast_hub + v(side * 0.75 + dx, -0.08, 0.035), Z, 0.018, "zinc", False)
    tail = m.part("rotor_tail", 40.0, tail_hub)
    tail.add(vk.lathe([(0.0, -0.06), (0.05, -0.06), (0.06, -0.03), (0.06, 0.04), (0.03, 0.07), (0.0, 0.08)], 14), "engine_alloy", vk.frame(tail_hub, X) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'))
    for side in (-1.0, 1.0):
        path = [tail_hub + v(0.0, 0.0, side * (0.08 + (tail_radius - 0.08) * s / 6)) for s in range(7)]
        profile = [(px * 0.12, -py * 1.2) for px, py in airfoil]
        tail.add(g.sweep(path, profile, closed=False, planar=X, caps=True), "blade_paint")
        tip_path = [tail_hub + v(0.0, 0.0, side * (tail_radius - 0.1)), tail_hub + v(0.0, 0.0, side * tail_radius)]
        tail.add(g.sweep(tip_path, [(px * 0.122, -py * 1.25) for px, py in airfoil], closed=False, planar=X, caps=True), "blade_tip")
    nav_l = v(0.81, -1.0, 0.96)
    nav_r = v(-0.81, -1.0, 0.96)
    land = v(0.0, -2.42, 0.86)
    tail_light = v(0.0, boom_end + 0.3, 2.9)
    frame.add(vk.block(v(-0.08, -2.48, 0.84), v(0.08, -2.36, 0.94)), "chassis_black", None, 0.01)
    caged_lamp(frame, frame, land + v(0.0, -0.02, 0.0), v(0.0, -1.0, -0.35), 0.06)
    hull.add(g.sphere(0.035, 12, 8), "lens_red", Matrix.Translation(nav_l))
    hull.add(g.sphere(0.035, 12, 8), "lens_green", Matrix.Translation(nav_r))
    hull.add(g.sphere(0.03, 12, 8), "lens", Matrix.Translation(tail_light))
    m.point("light_head", land + v(0.0, -0.1, -0.03))
    m.point("light_nav_l", nav_l)
    m.point("light_nav_r", nav_r)
    m.point("light_tail", tail_light)
    m.sets = [("veh_heli_hull", ["heli_hull"]), ("veh_heli_frame", ["heli_frame"]), ("veh_heli_engine", ["heli_engine"]), ("veh_heli_rotor", ["rotor_main", "rotor_tail"])]
    m.body_parts = ["heli_hull", "heli_frame", "heli_engine"]
    m.col((-0.8, -2.6, 0.6), (0.8, 0.12, 2.06))
    m.col((-0.76, 0.12, 0.6), (0.76, 1.7, 2.18))
    m.col((-0.38, 1.7, 1.45), (0.38, 6.45, 2.1))
    m.col((-0.07, 5.9, 1.7), (0.07, 6.75, 2.98))
    for side in (-1.0, 1.0):
        m.col((side * 1.0 - 0.05, -1.85, 0.0), (side * 1.0 + 0.05, 2.05, 0.1))
    m.manifest.update({
        "rotor_main": {"part": "rotor_main", "hub": vk.triple(mast_hub), "axis": [0.0, 0.0, 1.0], "radius": blade_radius, "blades": 2, "spin": "counter-clockwise seen from above"},
        "rotor_tail": {"part": "rotor_tail", "hub": vk.triple(tail_hub), "axis": [1.0, 0.0, 0.0], "radius": tail_radius, "blades": 2},
        "skid_contacts": [vk.triple(v(side * 1.0, y, 0.0)) for side in (-1.0, 1.0) for y in (-1.5, 1.95)],
        "mass_kg": 1150, "mass_note": "welded steel tube airframe, armour plate cockpit, flat-six engine, 80 l drum tank; between a two-seat light helicopter (about 650 kg empty) and a small utility type",
        "centre_of_mass": [0.0, 0.1, 1.25],
        "seats": {"seat_pilot": vk.triple(v(-0.35, seat_y - 0.05, eye)), "seat_passenger": vk.triple(v(0.35, seat_y - 0.05, eye))},
        "lights": {"light_head": {"position": vk.triple(land + v(0.0, -0.1, -0.03)), "direction": vk.triple(v(0.0, -1.0, -0.35).normalized()), "kind": "landing"}, "light_nav_l": {"position": vk.triple(nav_l), "direction": [1.0, 0.0, 0.0], "kind": "navigation red (port)"}, "light_nav_r": {"position": vk.triple(nav_r), "direction": [-1.0, 0.0, 0.0], "kind": "navigation green (starboard)"}, "light_tail": {"position": vk.triple(tail_light), "direction": [0.0, 1.0, 0.0], "kind": "tail white"}},
        "exhausts": [vk.triple(block_center + v(side * 0.42, 0.7, 0.62)) for side in (-1.0, 1.0)],
    })
    m.close(v(3.4, -5.2, 3.2), v(0.0, -0.5, 1.4), 35.0)
    m.close(v(1.8, -3.6, 1.7), v(0.0, -1.8, 1.3), 40.0)
    m.close(v(2.0, 0.4, 2.0), v(0.0, 1.0, 1.2), 45.0)
    m.close(v(1.6, 5.2, 2.6), v(0.2, 6.2, 2.0), 40.0)
    m.close(v(1.2, -0.6, 3.4), v(0.0, 0.25, 2.6), 40.0)
    return m


def heli_far(m):
    body = m.far("body")
    body.add(vk.block(v(-0.76, -2.4, 0.64), v(0.76, 0.1, 2.04)), "steel")
    body.add(vk.block(v(-0.62, 0.1, 0.66), v(0.62, 1.7, 2.1)), "steel")
    body.add(vk.prism([(-0.36, 1.5), (0.36, 1.5), (0.0, 2.05)], 1.6, 3.95), "steel")
    body.add(vk.prism([(-0.24, 1.64), (0.24, 1.64), (0.0, 2.02)], 3.95, 6.3), "steel")
    body.add(vk.slab([(6.0, 1.78), (6.55, 1.75), (6.72, 2.95), (6.45, 2.95), (6.0, 2.05)], 0.012), "steel", Matrix(((0.0, 0.0, 1.0, -0.05), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))))
    for side in (-1.0, 1.0):
        body.add(vk.block(v(side * 1.0 - 0.04, -1.6, 0.0), v(side * 1.0 + 0.04, 2.0, 0.08)), "steel")
        for y in (-0.9, 1.15):
            body.add(vk.block(v(min(side * 1.0, side * 0.55) - 0.03, y - 0.03, 0.05), v(max(side * 1.0, side * 0.55) + 0.03, y + 0.03, 0.62)), "steel")
    hub = m.manifest["rotor_main"]["hub"]
    rotor = m.far("rotor_main", 40.0, Vector(hub))
    rotor.add(vk.block(v(-4.0, -0.13, -0.015), v(4.0, 0.13, 0.015)), "steel", Matrix.Translation(Vector(hub)))
    rotor.add(vk.cylinder(0.12, 0.3, 8), "steel", vk.frame(Vector(hub) - v(0.0, 0.0, 0.25), Z))
    tail_hub = Vector(m.manifest["rotor_tail"]["hub"])
    tail = m.far("rotor_tail", 40.0, tail_hub)
    tail.add(vk.block(v(-0.01, -0.06, -0.7), v(0.01, 0.06, 0.7)), "steel", Matrix.Translation(tail_hub))


builders = {"veh_rover": (rover, rover_far), "veh_heli": (heli, heli_far)}


def build_objects(m):
    built = {}
    for key, part in m.parts.items():
        built[key] = part.build()
    return built


def rename(obj, name):
    obj.name = name
    obj.data.name = name


def bake(name):
    vk.reset()
    looks()
    started = time.time()
    maker, far_maker = builders[name]
    m = maker()
    built = build_objects(m)
    far_maker(m)
    far_built = {key: part.build() for key, part in m.far_parts.items()}
    sets = {}
    body_objects = [built[key] for key in m.body_parts]
    rotors = [obj for key, obj in built.items() if key.startswith("rotor")]
    far_sets = {m.sets[0][0], getattr(m, "wheel_set", ""), "veh_heli_rotor"}
    for key, members in m.sets:
        tset = vk.texture_set(key, name)
        objects = [built[member] for member in members]
        isolated = any(member.startswith(("wheel", "rotor")) for member in members)
        hide = [obj for obj in built.values() if obj not in objects] if isolated else [obj for obj in rotors if obj not in objects]
        tset.bake_near(objects, with_far=key in far_sets, hide=hide)
        sets[key] = tset
    first = sets[m.sets[0][0]]
    first.bake_far([far_built["body"]], body_objects, 0.1, 0.6)
    if "wheel_fl" in far_built:
        sets[m.wheel_set].bake_far([far_built["wheel_fl"]], [built["wheel_fl"]], 0.06, 0.3)
    if "rotor_main" in far_built:
        sets["veh_heli_rotor"].bake_far([far_built["rotor_main"], far_built["rotor_tail"]], [built["rotor_main"], built["rotor_tail"]], 0.06, 0.3)
    if name == "veh_rover":
        source = built["wheel_fl"]
        far_source = far_built["wheel_fl"]
        for key, (center, side) in m.wheels.items():
            if key == "wheel_fl":
                continue
            turn = Matrix.Identity(4) if side > 0 else Matrix.Rotation(math.pi, 4, 'Z')
            built[key] = vk.duplicate(source, key, turn, center)
            far_built[key] = vk.duplicate(far_source, "far_" + key, turn, center)
        spare = vk.duplicate(source, "spare", m.spare.to_3x3().to_4x4(), m.spare.translation.copy())
        body = vk.join(body_objects + [spare], "body")
        near_objects = [body, built["steering"]] + [built[key] for key in ("wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr")]
    else:
        body = vk.join(body_objects, "body")
        near_objects = [body, built["rotor_main"], built["rotor_tail"]]
    markers = [vk.marker(marker_name, low, high, first.material) for marker_name, low, high in m.markers]
    for point_name, position, size in m.points:
        markers.append(vk.point_marker(point_name, position, size, first.material))
    path, document = vk.export(name, near_objects + markers)
    near = vk.audit(path, document, 64000)
    for obj in near_objects + markers:
        rename(obj, "done_" + obj.name)
    far_objects = []
    for key, obj in far_built.items():
        rename(obj, key)
        far_objects.append(obj)
    path, document = vk.export(name + "_far", far_objects)
    far = vk.audit(path, document, 4500)
    write_manifest(name, m, near, far, near_objects)
    vk.log("BAKE DONE", name, round(time.time() - started, 1), "s", "problems", near["problems"] + far["problems"])


def write_manifest(name, m, near, far, objects):
    document = {
        "space": "Blender model space in metres. +X = vehicle left, -X = vehicle right, -Y = forward (nose / front bumper), +Z = up. Origin on the ground plane under the centre of the vehicle (between the axles for the rover, under the main rotor mast for the helicopter). The engine baker maps Blender (x, y, z) to engine (x, z, y), so engine forward is -Z.",
        "model": name,
        "far_model": name + "_far",
        "triangles": near["triangles"],
        "triangles_far": far["triangles"],
        "bounds_min": list(near["low"]),
        "bounds_max": list(near["high"]),
        "size": [round(near["high"][i] - near["low"][i], 3) for i in range(3)],
        "parts": {key: {"origin": value[1], "triangles": value[0]} for key, value in near["parts"].items()},
        "markers": near["markers"],
    }
    if name == "veh_rover":
        wheels = {}
        for key, (center, side) in m.wheels.items():
            wheels[key] = {"centre": vk.triple(center), "radius": 0.4, "width": 0.27, "axle": [1.0, 0.0, 0.0], "outer_face": "+X" if side > 0 else "-X", "steers": key in ("wheel_fl", "wheel_fr"), "driven": True}
        document["wheels"] = wheels
    document.update(m.manifest)
    vk.write_json(os.path.join(vk.models_root, name, name + ".json"), document)
    vk.log("MANIFEST", name, json.dumps(document)[:2000])


def look(name):
    vk.reset()
    looks()
    maker, far_maker = builders[name]
    m = maker()
    built = build_objects(m)
    if name == "veh_rover":
        source = built["wheel_fl"]
        for key, (center, side) in m.wheels.items():
            if key != "wheel_fl":
                vk.duplicate(source, key, Matrix.Identity(4) if side > 0 else Matrix.Rotation(math.pi, 4, 'Z'), center)
        vk.duplicate(source, "spare", m.spare.to_3x3().to_4x4(), m.spare.translation.copy())
    objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    vk.log("LOOK", name, "tris", vk.triangles_of(objects), [(obj.name, vk.triangles_of([obj])) for obj in objects])
    os.makedirs(preview_root, exist_ok=True)
    render(name, objects, m.closeups, os.path.join(preview_root, name + "_look"))


def render(name, objects, closeups, prefix, extra_paths=()):
    vk.render_settings(samples, (1280, 720))
    vk.daylight()
    vk.ground_plane(0.0, 80.0, "gravel")
    paths = []
    for view, direction in (("three", (0.8, -1.0, 0.45)), ("back", (-0.9, 0.85, 0.4)), ("side", (1.0, 0.0, 0.12)), ("front", (0.05, -1.0, 0.15)), ("top", (0.15, -0.3, 1.0))):
        path = prefix + "_" + view + ".png"
        vk.view_shot(path, objects, direction, 40.0, None, 0.05)
        paths.append(path)
    for index, (position, target, lens) in enumerate(closeups):
        path = prefix + "_close" + str(index) + ".png"
        vk.close_shot(path, position, target, lens)
        paths.append(path)
    vk.contact_sheet(list(paths) + list(extra_paths), prefix + "_sheet.png", 3, (640, 360))
    return paths


def preview(name):
    vk.reset()
    imported = vk.import_model(name)
    visual = [obj for obj in imported if obj.type == 'MESH' and not vk.is_marker(obj.name)]
    markers = [obj for obj in imported if obj.type == 'MESH' and vk.is_marker(obj.name)]
    for obj in markers:
        obj.hide_render = True
    maker, far_maker = builders[name]
    looks()
    m = maker()
    os.makedirs(preview_root, exist_ok=True)
    prefix = os.path.join(preview_root, name)
    paths = render(name, visual, m.closeups, prefix)
    extra = []
    shown = []
    for obj in markers:
        if obj.name.startswith("col_"):
            obj.hide_render = False
            obj.data.materials.clear()
            obj.data.materials.append(vk.overlay_material((1.0, 0.25, 0.1), 1.5, 0.3))
            shown.append(obj)
        else:
            low, high = vk.world_bounds([obj])
            color = (1.0, 0.9, 0.2) if obj.name.startswith("light") else ((0.2, 1.0, 0.3) if obj.name.startswith("seat") else (0.3, 0.6, 1.0))
            shown.append(vk.solid_object("marker_dot", g.shifted(g.sphere(0.07, 12, 8), *((low + high) * 0.5)), vk.overlay_material(color, 4.0, 1.0)))
    path = prefix + "_markers.png"
    vk.view_shot(path, visual, (0.8, -1.0, 0.45), 40.0, None, 0.05)
    extra.append(path)
    for obj in shown:
        obj.hide_render = True
    moving = [obj for obj in visual if obj.name.startswith(("wheel", "rotor", "steering"))]
    gizmos = []
    for obj in moving:
        if obj.name.startswith("wheel"):
            obj.location.x += 0.6 if obj.location.x > 0 else -0.6
        elif obj.name == "rotor_main":
            obj.location.z += 1.2
        elif obj.name == "rotor_tail":
            obj.location.x += 0.8
        elif obj.name == "steering":
            obj.location.x -= 1.4
        gizmos += vk.gizmo(obj.location, 0.5 if not obj.name.startswith("rotor_main") else 1.2)
    for obj in visual:
        if obj.name == "body":
            obj.hide_render = False
    path = prefix + "_exploded.png"
    vk.view_shot(path, visual + gizmos, (0.85, -1.0, 0.55), 40.0, None, 0.05)
    extra.append(path)
    for obj in visual:
        if obj.name == "body":
            obj.hide_render = True
    path = prefix + "_parts.png"
    vk.view_shot(path, [obj for obj in moving] + gizmos, (0.85, -1.0, 0.55), 40.0, None, 0.08)
    extra.append(path)
    for obj in visual:
        obj.hide_render = True
    for obj in gizmos:
        obj.hide_render = True
    far = [obj for obj in vk.import_model(name + "_far") if obj.type == 'MESH']
    path = prefix + "_far.png"
    vk.view_shot(path, far, (0.8, -1.0, 0.45), 40.0, None, 0.05)
    extra.append(path)
    vk.contact_sheet(paths + extra, prefix + "_sheet.png", 3, (640, 360))


def main():
    started = time.time()
    names = wanted or list(builders)
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
