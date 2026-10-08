import bpy
import bmesh
import json
import math
import os
import random
import struct
import sys
import time
import zlib
import numpy
from mathutils import Matrix, Vector, geometry

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gunkit as g
import turntable
from gunkit import v

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(here))
models_root = os.path.join(root, "assets", "raw", "models")
previews_root = os.path.join(root, "assets", "previews")
source_root = os.path.join(root, "assets", "source")
source_textures = os.path.join(root, "assets", "source", "textures")
raw_textures = os.path.join(root, "assets", "raw", "textures")
acg_textures = os.path.join(root, "assets", "raw", "textures_acg")
hdri_path = os.path.join(root, "assets", "raw", "hdri", "kloofendal_overcast_puresky_4k.hdr")
fonts_root = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
tau = math.pi * 2.0
X = v(1.0, 0.0, 0.0)
Y = v(0.0, 1.0, 0.0)
Z = v(0.0, 0.0, 1.0)
g.roots["source"] = source_root
g.roots["raw"] = os.path.join(root, "assets", "raw")
materials_cache = {}
labels = {}
specs = {}
templates = {}
settings = {"bake_size": 2048, "output_size": 1024, "samples": 24, "ao_samples": 32, "margin": 16, "ao_distance": 0.45, "band": 0.12}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials_cache.clear()
    labels.clear()
    templates.clear()


def log(*items):
    print(*items, flush=True)


def rgba(color):
    return (color[0], color[1], color[2], 1.0) if len(color) == 3 else tuple(color)


def scaled(color, factor):
    return (color[0] * factor, color[1] * factor, color[2] * factor)


def blend(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def frame(position, forward, up=None):
    x_axis = Vector(forward).normalized()
    hint = Vector(up).normalized() if up is not None else Z
    if abs(x_axis.dot(hint)) > 0.985:
        hint = X if abs(x_axis.x) < 0.9 else Y
    z_axis = (hint - x_axis * hint.dot(x_axis)).normalized()
    y_axis = z_axis.cross(x_axis)
    matrix = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
    matrix.translation = position
    return matrix


def at(position, yaw=0.0, pitch=0.0, roll=0.0):
    return Matrix.Translation(position) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'Y') @ Matrix.Rotation(roll, 4, 'X')


def about(point, axis, angle):
    return Matrix.Translation(point) @ Matrix.Rotation(angle, 4, Vector(axis).normalized()) @ Matrix.Translation(-Vector(point))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def cube(sx, sy, sz):
    return g.box(sx, sy, sz)


def block(low, high):
    low = Vector(low)
    high = Vector(high)
    size = high - low
    return g.shifted(g.box(abs(size.x), abs(size.y), abs(size.z)), (low.x + high.x) * 0.5, (low.y + high.y) * 0.5, (low.z + high.z) * 0.5)


def cylinder(radius, length, sides=16, caps=True, start=0.0):
    if caps:
        return g.revolve([(0.0, 0.0), (radius, 0.0), (radius, length), (0.0, length)], sides, start)
    return g.revolve([(radius, 0.0), (radius, length)], sides, start, False)


def lathe(profile, sides=16, start=0.0, closed=True):
    bm = g.revolve([(r, z) for r, z in profile], sides, start, closed)
    bmesh.ops.transform(bm, matrix=Matrix.Rotation(-math.pi * 0.5, 4, 'Y'), verts=bm.verts)
    return bm


def tube(points, radius, sides=8, caps=True, up=None, scales=None):
    return g.sweep([Vector(p) for p in points], g.circle(radius, sides), up=up if up is not None else Z, caps=caps, scales=scales)


def sweep(points, profile, caps=True, up=None, closed=False, scales=None):
    return g.sweep([Vector(p) for p in points], profile, closed=closed, up=up if up is not None else Z, caps=caps, scales=scales)


def rod(a, b, radius, sides=8, caps=True):
    a = Vector(a)
    b = Vector(b)
    return g.transformed(cylinder(radius, (b - a).length, sides, caps), frame(a, b - a))


def bar(a, b, width, height, up=None):
    a = Vector(a)
    b = Vector(b)
    return g.transformed(g.box((b - a).length, width, height), frame((a + b) * 0.5, b - a, up))


def cone(base, tip, radius, sides=6):
    base = Vector(base)
    tip = Vector(tip)
    return g.transformed(g.revolve([(0.0, 0.0), (radius, 0.0), (0.0, (tip - base).length)], sides), frame(base, tip - base))


def slab(outline, thickness, holes=()):
    bm = bmesh.new()
    loops = [list(outline)] + [list(hole) for hole in holes]
    flat = [p for loop in loops for p in loop]
    triangles = geometry.tessellate_polygon([[Vector((x, y, 0.0)) for x, y in loop] for loop in loops])
    low = [bm.verts.new((x, y, -thickness * 0.5)) for x, y in flat]
    high = [bm.verts.new((x, y, thickness * 0.5)) for x, y in flat]
    for a, b, c in triangles:
        for face in ((high[a], high[b], high[c]), (low[c], low[b], low[a])):
            try:
                bm.faces.new(face)
            except ValueError:
                pass
    start = 0
    for loop in loops:
        count = len(loop)
        for i in range(count):
            j = (i + 1) % count
            try:
                bm.faces.new((low[start + i], low[start + j], high[start + j], high[start + i]))
            except ValueError:
                pass
        start += count
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def prism(outline, y0, y1):
    bm = slab(outline, abs(y1 - y0))
    bmesh.ops.transform(bm, matrix=Matrix.Translation((0.0, (y0 + y1) * 0.5, 0.0)) @ Matrix.Rotation(math.pi * 0.5, 4, 'X'), verts=bm.verts)
    return bm


def rubble(sx, sy, sz, rng, jitter=0.16, bevel=0.025):
    bm = g.box(sx, sy, sz)
    for vert in bm.verts:
        vert.co.x += rng.uniform(-jitter, jitter) * sx * 0.5
        vert.co.z += rng.uniform(-jitter, jitter) * sz * 0.5
        if vert.co.y < 0.0:
            vert.co.y -= rng.uniform(0.0, 0.25) * sy
    bmesh.ops.subdivide_edges(bm, edges=[edge for edge in bm.edges if (edge.verts[0].co.y < 0.0 and edge.verts[1].co.y < 0.0)], cuts=1, use_grid_fill=True)
    for vert in bm.verts:
        if vert.co.y < -sy * 0.3 and abs(vert.co.x) < sx * 0.3 and abs(vert.co.z) < sz * 0.3:
            vert.co.y -= rng.uniform(0.005, 0.03)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bevelled(bm, min(bevel, sx * 0.18, sz * 0.18), 1, 25.0)


def rounded(width, height, radius, steps=3):
    return g.fillet([(-width * 0.5, -height * 0.5), (width * 0.5, -height * 0.5), (width * 0.5, height * 0.5), (-width * 0.5, height * 0.5)], radius, steps)


def grid_sheet(width, height, nx, ny, lift=None):
    bm = bmesh.new()
    rows = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = -width * 0.5 + width * i / nx
            y = -height * 0.5 + height * j / ny
            row.append(bm.verts.new((x, y, lift(x, y) if lift else 0.0)))
        rows.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    return bm


def carve(target, cutters, operation='DIFFERENCE'):
    target_mesh = bpy.data.meshes.new("carve_target")
    target.to_mesh(target_mesh)
    target.free()
    subject = bpy.data.objects.new("carve_target", target_mesh)
    bpy.context.scene.collection.objects.link(subject)
    tools = []
    for index, cutter in enumerate(cutters):
        cutter_mesh = bpy.data.meshes.new("carve_tool")
        cutter.to_mesh(cutter_mesh)
        cutter.free()
        tool = bpy.data.objects.new("carve_tool", cutter_mesh)
        bpy.context.scene.collection.objects.link(tool)
        tools.append(tool)
        modifier = subject.modifiers.new("carve%d" % index, 'BOOLEAN')
        modifier.operation = operation
        modifier.solver = 'EXACT'
        modifier.object = tool
    bpy.context.view_layer.update()
    result = bpy.data.meshes.new_from_object(subject.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(subject)
    bpy.data.meshes.remove(target_mesh)
    for tool in tools:
        mesh = tool.data
        bpy.data.objects.remove(tool)
        bpy.data.meshes.remove(mesh)
    bm = bmesh.new()
    bm.from_mesh(result)
    bpy.data.meshes.remove(result)
    return bm


def thicken(bm, thickness):
    bm.normal_update()
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thickness)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def lump(rx, ry, rz, rng, rough=0.25, subdivisions=2, floor=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    waves = []
    for index in range(7):
        direction = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
        waves.append((direction * rng.uniform(1.0, 3.5), rng.uniform(0.0, tau), rng.uniform(0.4, 1.0) / (index + 1) ** 0.5))
    total = sum(w for d, p, w in waves)
    for vert in bm.verts:
        n = vert.co.normalized()
        bump = sum(math.sin(d.dot(n) + p) * w for d, p, w in waves) / total
        s = 1.0 + rough * bump
        vert.co = Vector((n.x * rx * s, n.y * ry * s, n.z * rz * s))
        if floor is not None and vert.co.z < floor:
            vert.co.z = floor
    return bm


def pillow(sx, sy, sz, rng, squash=0.35, sag=0.0, bulge=0.12, u=14, w=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=w, radius=1.0)
    for vert in bm.verts:
        n = vert.co
        px = math.copysign(abs(n.x) ** squash, n.x)
        py = math.copysign(abs(n.y) ** squash, n.y)
        pz = math.copysign(abs(n.z) ** (squash + 0.25), n.z)
        swell = 1.0 + bulge * (1.0 - abs(px)) * (1.0 - abs(py))
        z = pz * sz * 0.5 * swell
        if sag:
            z -= sag * (1.0 - px * px) * (1.0 - py * py) * (0.5 + 0.5 * pz)
        vert.co = Vector((px * sx * 0.5 * (1.0 + rng.uniform(-0.02, 0.02)), py * sy * 0.5, z))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def superellipse(width, height, exponent=4.0, count=24):
    points = []
    for s in range(count):
        angle = tau * s / count
        c = math.cos(angle)
        sn = math.sin(angle)
        points.append((math.copysign(abs(c) ** (2.0 / exponent), c) * width * 0.5, math.copysign(abs(sn) ** (2.0 / exponent), sn) * height * 0.5))
    return points


def template(key, builder):
    if key not in templates:
        templates[key] = builder()
    return templates[key].copy()


def hex_head(across, height):
    return g.shifted(g.hexagon(across, height, "x"), height * 0.5)


def bolt(target, position, normal, across=0.022, look="zinc", washer=True, spin=0.0):
    height = across * 0.42
    matrix = frame(Vector(position), Vector(normal)) @ Matrix.Rotation(spin, 4, 'X')
    if washer:
        target.add(template(("washer", round(across, 4)), lambda: cylinder(across * 0.82, across * 0.1, 10)), look, matrix)
        matrix = matrix @ Matrix.Translation((across * 0.1, 0.0, 0.0))
    target.add(template(("hex", round(across, 4)), lambda: hex_head(across, height)), look, matrix)


def rivet(target, position, normal, radius=0.008, look="steel"):
    target.add(template(("rivet", round(radius, 4)), lambda: g.revolve([(0.0, -radius * 0.2), (radius, -radius * 0.2), (radius * 0.9, radius * 0.25), (radius * 0.55, radius * 0.55), (0.0, radius * 0.62)], 7)), look, frame(Vector(position), Vector(normal)))


def rivets(target, a, b, spacing, normal, radius=0.008, look="steel", ends=True):
    a = Vector(a)
    b = Vector(b)
    count = max(int((b - a).length / spacing), 1)
    for index in range(count + 1):
        if not ends and index in (0, count):
            continue
        rivet(target, a.lerp(b, index / count), normal, radius, look)


def weld(target, points, normal, radius=0.005, seed=0, look="weld"):
    path = [Vector(p) for p in points]
    dense, length = g.resample(g.spline(path, 6) if len(path) > 2 else path, max(radius * 2.4, 0.01))
    wobble = g.smooth_noise(len(dense), seed, 3)
    normal = Vector(normal).normalized()
    bm = bmesh.new()
    rings = []
    profile = [(-1.0, -0.4), (-0.7, 0.35), (0.0, 0.62), (0.7, 0.35), (1.0, -0.4)]
    for i, point in enumerate(dense):
        ahead = dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]
        side = ahead.cross(normal).normalized() if ahead.length > 1e-9 else normal.orthogonal().normalized()
        along = length * i / max(len(dense) - 1, 1)
        taper = math.sqrt(max(min(1.0, along / (radius * 1.5), (length - along) / (radius * 1.5)), 0.05))
        r = radius * taper * (1.0 + 0.12 * wobble[i])
        rings.append([bm.verts.new(point + side * x * r + normal * y * r) for x, y in profile])
    for i in range(len(rings) - 1):
        for j in range(len(profile) - 1):
            bm.faces.new((rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    target.add(bm, look)


def mesh_panel(target, matrix, width, height, pitch, wire, look="mesh", border=0.0, skip=None):
    columns = max(int(width / pitch), 1)
    rows = max(int(height / pitch), 1)
    for i in range(columns + 1):
        x = -width * 0.5 + width * i / columns
        if skip and skip(x, None):
            continue
        target.add(g.transformed(g.box(wire, wire, height), Matrix.Translation((x, wire * 0.5, 0.0))), look, matrix)
    for j in range(rows + 1):
        z = -height * 0.5 + height * j / rows
        if skip and skip(None, z):
            continue
        target.add(g.transformed(g.box(width, wire, wire), Matrix.Translation((0.0, -wire * 0.5, z))), look, matrix)
    if border > 0.0:
        for x in (-width * 0.5 - border * 0.5, width * 0.5 + border * 0.5):
            target.add(g.transformed(g.box(border, border, height + border * 2.0), Matrix.Translation((x, 0.0, 0.0))), look, matrix)
        for z in (-height * 0.5 - border * 0.5, height * 0.5 + border * 0.5):
            target.add(g.transformed(g.box(width, border, border), Matrix.Translation((0.0, 0.0, z))), look, matrix)


def link_geometry(length, width, wire, sides=4, steps=4):
    straight = max(length - width, 0.0) * 0.5
    radius = (width - wire) * 0.5
    path = []
    for end, sign in ((straight, 1.0), (-straight, -1.0)):
        for s in range(steps + 1):
            angle = -math.pi * 0.5 + math.pi * s / steps
            path.append(Vector((end + sign * math.cos(angle) * radius, sign * math.sin(angle) * radius, 0.0)))
    return g.sweep(path, g.circle(wire * 0.5, sides), closed=True, planar=Z)


def chain(target, points, link=0.05, wire=0.008, look="chain", seed=0):
    path = [Vector(p) for p in points]
    dense, length = g.resample(g.spline(path, 8), link * 0.78)
    for i in range(len(dense) - 1):
        a = dense[i]
        b = dense[i + 1]
        middle = (a + b) * 0.5
        direction = b - a
        if direction.length < 1e-6:
            continue
        twist = math.pi * 0.5 * (i % 2) + 0.15 * math.sin(i * 1.7 + seed)
        matrix = frame(middle, direction) @ Matrix.Rotation(twist, 4, 'X')
        target.add(template(("link", round(link, 4), round(wire, 4)), lambda: link_geometry(link, link * 0.62, wire)), look, matrix)


def sag(a, b, depth, steps=10):
    a = Vector(a)
    b = Vector(b)
    return [a.lerp(b, s / steps) - Z * depth * math.sin(math.pi * s / steps) for s in range(steps + 1)]


def spike(target, base, direction, length=0.12, radius=0.022, look="spike"):
    base = Vector(base)
    tip = base + Vector(direction).normalized() * length
    target.add(cone(base, tip, radius, 6), look)


def strap(target, path, width, thickness, look="strap", up=None):
    profile = [(-width * 0.5, -thickness * 0.5), (width * 0.5, -thickness * 0.5), (width * 0.5, thickness * 0.5), (-width * 0.5, thickness * 0.5)]
    target.add(sweep(path, profile, True, up), look)


def rope_line(target, points, radius=0.009, look="rope", spacing=None):
    target.add_many(g.rope([Vector(p) for p in points], radius, 2, 3.0, 5, spacing if spacing is not None else radius * 1.6), look)


def hose_clamp(target, center, axis, radius, look="zinc", width=0.012):
    axis = Vector(axis).normalized()
    side = axis.orthogonal().normalized()
    other = axis.cross(side)
    path = [Vector(center) + (side * math.cos(tau * s / 16) + other * math.sin(tau * s / 16)) * (radius + 0.0015) for s in range(16)]
    profile = [(0.0, -width * 0.5), (0.0, width * 0.5), (-0.0015, width * 0.5), (-0.0015, -width * 0.5)]
    target.add(g.sweep(path, profile, closed=True, planar=axis), look)
    lug = Vector(center) + side * (radius + 0.008)
    target.add(g.transformed(g.box(0.018, 0.014, width), frame(lug, side, axis)), look)


class part:
    def __init__(self, name, sharp=38.0, origin=None):
        self.name = name
        self.sharp = sharp
        self.origin = Vector(origin) if origin is not None else None
        self.coords = []
        self.colors = []
        self.faces = []
        self.face_slot = []
        self.face_label = []
        self.slots = []
        self.lookup = {}

    def slot(self, look):
        if look not in self.lookup:
            self.lookup[look] = len(self.slots)
            self.slots.append(look)
        return self.lookup[look]

    def add(self, bm, look, matrix=None, bevel=0.0, segments=1, angle=30.0, label=None, profile=0.5, tint=None, chooser=None):
        if bevel > 0.0:
            bevelled(bm, bevel, segments, angle, profile)
        if matrix is not None:
            bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
        bm.verts.index_update()
        bm.normal_update()
        base = len(self.coords)
        self.coords.extend(tuple(vert.co) for vert in bm.verts)
        shade = tuple(tint) if tint is not None else (1.0, 1.0, 1.0)
        self.colors.extend([shade] * len(bm.verts))
        index = self.slot(look)
        for face in bm.faces:
            self.faces.append(tuple(base + vert.index for vert in face.verts))
            chosen = chooser(face) if chooser is not None else None
            self.face_slot.append(self.slot(chosen) if chosen else index)
            uvs = None
            if label is not None:
                for projection in (label if isinstance(label, list) else [label]):
                    if face.normal.dot(projection["facing"]) > projection["limit"]:
                        uvs = [((vert.co - projection["origin"]).dot(projection["u"]) / projection["width"] + 0.5, (vert.co - projection["origin"]).dot(projection["v"]) / projection["height"] + 0.5) for vert in face.verts]
                        break
            self.face_label.append(uvs)
        bm.free()

    def add_many(self, pieces, look, matrix=None):
        for piece in pieces:
            self.add(piece, look, matrix)

    def triangles(self):
        return sum(len(face) - 2 for face in self.faces)

    def build(self):
        mesh = bpy.data.meshes.new(self.name)
        shift = self.origin if self.origin is not None else Vector((0.0, 0.0, 0.0))
        mesh.from_pydata([(x - shift.x, y - shift.y, z - shift.z) for x, y, z in self.coords], [], self.faces)
        mesh.polygons.foreach_set("material_index", self.face_slot)
        layer = mesh.uv_layers.new(name="UVMap")
        if any(uvs is not None for uvs in self.face_label):
            text_layer = mesh.uv_layers.new(name="TextMap")
            flat = []
            for face, uvs in zip(self.faces, self.face_label):
                if uvs is None:
                    flat.extend((-4.0, -4.0) * len(face))
                else:
                    for u, w in uvs:
                        flat.extend((u, w))
            text_layer.data.foreach_set("uv", flat)
        mesh.uv_layers.active = layer
        layer.active_render = True
        attribute = mesh.color_attributes.new("tint", 'FLOAT_COLOR', 'POINT')
        attribute.data.foreach_set("color", [value for r, g_value, b in self.colors for value in (r, g_value, b, 1.0)])
        boost = [1 if uvs is not None and any(-0.05 <= u <= 1.05 and -0.05 <= w <= 1.05 for u, w in uvs) else 0 for uvs in self.face_label]
        if any(boost):
            mesh.attributes.new("boost", 'INT', 'FACE').data.foreach_set("value", boost)
        mesh.validate(clean_customdata=False)
        for look in self.slots:
            mesh.materials.append(material(look))
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.set_sharp_from_angle(angle=math.radians(self.sharp))
        mesh.update()
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        modifier = obj.modifiers.new("weighted", 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
        modifier.weight = 50
        modifier.mode = 'FACE_AREA'
        bpy.context.view_layer.update()
        final = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        obj.modifiers.clear()
        obj.data = final
        bpy.data.meshes.remove(mesh)
        final.name = self.name
        if self.origin is not None:
            obj.location = self.origin
        return obj


def bevelled(bm, width, segments=1, angle=30.0, profile=0.5):
    if width <= 0.0:
        return bm
    bm.normal_update()
    limit = math.radians(angle)
    edges = [edge for edge in bm.edges if edge.is_manifold and edge.calc_face_angle(0.0) > limit]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type='OFFSET', profile_type='SUPERELLIPSE', segments=segments, profile=profile, affect='EDGES', clamp_overlap=True)
    return bm


def marker(name, low, high, look=None):
    low = Vector(low)
    high = Vector(high)
    lo = Vector((min(low.x, high.x), min(low.y, high.y), min(low.z, high.z)))
    hi = Vector((max(low.x, high.x), max(low.y, high.y), max(low.z, high.z)))
    points = [(lo.x, lo.y, lo.z), (hi.x, lo.y, lo.z), (hi.x, hi.y, lo.z), (lo.x, hi.y, lo.z), (lo.x, lo.y, hi.z), (hi.x, lo.y, hi.z), (hi.x, hi.y, hi.z), (lo.x, hi.y, hi.z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (0, 4, 7, 3), (1, 2, 6, 5)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0] * 6)
    if look is not None:
        mesh.materials.append(look)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def point_marker(name, position, size=0.03, look=None):
    position = Vector(position)
    half = Vector((size, size, size)) * 0.5
    return marker(name, position - half, position + half, look)


def is_marker(name):
    return name.split("_")[0] in ("col", "ramp", "loot", "light", "seat") or name == "exhaust"


def font_path(name):
    for path in (name, os.path.join(source_root, "fonts", name), os.path.join(fonts_root, name)):
        if os.path.isabs(path) and os.path.exists(path):
            return path
    return os.path.join(fonts_root, "arialbd.ttf")


def mask_image(key, data):
    height, width = data.shape[:2]
    image = bpy.data.images.new("label_" + key, width, height, alpha=False, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    pixels = numpy.ones((height, width, 4), dtype=numpy.float32)
    for channel in range(3):
        pixels[:, :, channel] = numpy.clip(data, 0.0, 1.0)
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    labels[key] = image
    return image


def text_in_cell(text, font, height_m, center, max_width_m, px_u, px_v):
    triangles = text_triangles(text, font, height_m / 0.7, 0.0, 0.0, max_width_m)
    return [tuple((x * px_u + center[0], y * px_v + center[1]) for x, y in tri) for tri in triangles]


def rasterize(triangles, width, height, supersample=4):
    W = width * supersample
    H = height * supersample
    canvas = numpy.zeros((H, W), dtype=numpy.float32)
    for a, b, c in triangles:
        ax, ay = a[0] * supersample, a[1] * supersample
        bx, by = b[0] * supersample, b[1] * supersample
        cx, cy = c[0] * supersample, c[1] * supersample
        x0 = max(int(math.floor(min(ax, bx, cx))), 0)
        x1 = min(int(math.ceil(max(ax, bx, cx))), W - 1)
        y0 = max(int(math.floor(min(ay, by, cy))), 0)
        y1 = min(int(math.ceil(max(ay, by, cy))), H - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = numpy.meshgrid(numpy.arange(x0, x1 + 1) + 0.5, numpy.arange(y0, y1 + 1) + 0.5)
        area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        if abs(area) < 1e-9:
            continue
        sign = 1.0 if area > 0.0 else -1.0
        e0 = ((bx - ax) * (ys - ay) - (by - ay) * (xs - ax)) * sign
        e1 = ((cx - bx) * (ys - by) - (cy - by) * (xs - bx)) * sign
        e2 = ((ax - cx) * (ys - cy) - (ay - cy) * (xs - cx)) * sign
        inside = (e0 >= 0.0) & (e1 >= 0.0) & (e2 >= 0.0)
        region = canvas[y0:y1 + 1, x0:x1 + 1]
        region[inside] = 1.0
    return canvas.reshape(height, supersample, width, supersample).mean(axis=(1, 3))


def text_triangles(text, font, size, center_x, center_y, max_width, spacing=1.0, squash=1.0):
    curve = bpy.data.curves.new("label_text", 'FONT')
    curve.body = text
    curve.font = bpy.data.fonts.load(font_path(font), check_existing=True)
    curve.size = size
    curve.space_character = spacing
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.fill_mode = 'BOTH'
    obj = bpy.data.objects.new("label_text", curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    points = [vert.co.copy() for vert in mesh.vertices]
    tris = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    bpy.data.objects.remove(obj)
    bpy.data.curves.remove(curve)
    if not points:
        return []
    low_x = min(p.x for p in points)
    high_x = max(p.x for p in points)
    low_y = min(p.y for p in points)
    high_y = max(p.y for p in points)
    fit = min(1.0, max_width / max((high_x - low_x) * squash, 1e-6))
    sx = fit * squash
    sy = fit
    mid_x = (low_x + high_x) * 0.5
    mid_y = (low_y + high_y) * 0.5
    return [tuple(((points[i].x - mid_x) * sx + center_x, (points[i].y - mid_y) * sy + center_y) for i in tri) for tri in tris]


def text_mask(key, aspect, lines, resolution=1024, borders=(), shapes=()):
    width = resolution
    height = max(16, int(round(resolution / aspect)))
    scale = height
    triangles = []
    for line in lines:
        text, size, y = line[0], line[1], line[2]
        font = line[3] if len(line) > 3 else "arialbd.ttf"
        x = line[4] if len(line) > 4 else aspect * 0.5
        max_width = line[5] if len(line) > 5 else aspect * 0.9
        squash = line[6] if len(line) > 6 else 1.0
        spacing = line[7] if len(line) > 7 else 1.0
        for tri in text_triangles(text, font, size, x, y, max_width, spacing, squash):
            triangles.append(tuple((px * scale, py * scale) for px, py in tri))
    for shape in shapes:
        for tri in shape:
            triangles.append(tuple((px * scale, py * scale) for px, py in tri))
    mask = rasterize(triangles, width, height)
    ys, xs = numpy.meshgrid((numpy.arange(height) + 0.5) / scale, (numpy.arange(width) + 0.5) / scale, indexing="ij")
    for inset, thickness in borders:
        outer = (xs > inset) & (xs < aspect - inset) & (ys > inset) & (ys < 1.0 - inset)
        inner = (xs > inset + thickness) & (xs < aspect - inset - thickness) & (ys > inset + thickness) & (ys < 1.0 - inset - thickness)
        mask = numpy.maximum(mask, (outer & ~inner).astype(numpy.float32))
    image = bpy.data.images.new("label_" + key, width, height, alpha=False, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    pixels = numpy.ones((height, width, 4), dtype=numpy.float32)
    pixels[:, :, 0] = mask
    pixels[:, :, 1] = mask
    pixels[:, :, 2] = mask
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    labels[key] = image
    return image


def label(origin, u_axis, v_axis, width, height, limit=0.55, facing=None):
    u_axis = Vector(u_axis).normalized()
    v_axis = Vector(v_axis).normalized()
    return {"origin": Vector(origin), "u": u_axis, "v": v_axis, "width": width, "height": height, "facing": Vector(facing).normalized() if facing is not None else u_axis.cross(v_axis).normalized(), "limit": limit}


def atlas_label(center, u_axis, v_axis, width, height, cell, limit=0.35, facing=None):
    u0, u1, v0, v1 = cell
    u_axis = Vector(u_axis).normalized()
    v_axis = Vector(v_axis).normalized()
    width_label = width / (u1 - u0)
    height_label = height / (v1 - v0)
    origin = Vector(center) - u_axis * width_label * ((u0 + u1) * 0.5 - 0.5) - v_axis * height_label * ((v0 + v1) * 0.5 - 0.5)
    return label(origin, u_axis, v_axis, width_label, height_label, limit, facing)


def line_mask(key, size, strokes, rects=(), extra=None):
    canvas = numpy.zeros((size, size), dtype=numpy.float32) if extra is None else extra.astype(numpy.float32)
    ys, xs = numpy.meshgrid((numpy.arange(size) + 0.5) / size, (numpy.arange(size) + 0.5) / size, indexing="ij")
    for points, width in strokes:
        for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
            x0 = max(int((min(ax, bx) - width) * size) - 2, 0)
            x1 = min(int((max(ax, bx) + width) * size) + 3, size)
            y0 = max(int((min(ay, by) - width) * size) - 2, 0)
            y1 = min(int((max(ay, by) + width) * size) + 3, size)
            if x1 <= x0 or y1 <= y0:
                continue
            px = xs[y0:y1, x0:x1]
            py = ys[y0:y1, x0:x1]
            dx = bx - ax
            dy = by - ay
            length = max(dx * dx + dy * dy, 1e-12)
            t = numpy.clip(((px - ax) * dx + (py - ay) * dy) / length, 0.0, 1.0)
            distance = numpy.hypot(px - (ax + t * dx), py - (ay + t * dy))
            value = numpy.clip(1.0 - (distance - width * 0.5) * size, 0.0, 1.0)
            canvas[y0:y1, x0:x1] = numpy.maximum(canvas[y0:y1, x0:x1], value)
    for x0, y0, x1, y1, value in rects:
        mask = (xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1)
        canvas[mask] = numpy.maximum(canvas[mask], value)
    return mask_image(key, canvas)


def register(name, builder, **params):
    specs[name] = (builder, params)


def material(look):
    cached = materials_cache.get(look)
    if cached is not None:
        try:
            cached.name
            return cached
        except ReferenceError:
            pass
    result = bpy.data.materials.new(look)
    result.use_nodes = True
    kind, params = specs.get(look, (look, {}))
    gr = graph(result)
    builders[kind](gr, params)
    materials_cache[look] = result
    return result


class graph:
    def __init__(self, result):
        self.material = result
        self.tree = result.node_tree
        self.shader = next(node for node in self.tree.nodes if node.type == 'BSDF_PRINCIPLED')
        coordinates = self.tree.nodes.new('ShaderNodeTexCoord')
        self.object = coordinates.outputs['Object']
        info = self.tree.nodes.new('ShaderNodeNewGeometry')
        self.normal = info.outputs['Normal']
        self.position = info.outputs['Position']
        split = self.tree.nodes.new('ShaderNodeSeparateXYZ')
        self.tree.links.new(self.normal, split.inputs['Vector'])
        self.nz = split.outputs['Z']
        self.nx = split.outputs['X']
        self.ny = split.outputs['Y']
        where = self.tree.nodes.new('ShaderNodeSeparateXYZ')
        self.tree.links.new(self.position, where.inputs['Vector'])
        self.wz = where.outputs['Z']
        local = self.tree.nodes.new('ShaderNodeSeparateXYZ')
        self.tree.links.new(self.object, local.inputs['Vector'])
        self.ox = local.outputs['X']
        self.oy = local.outputs['Y']
        self.oz = local.outputs['Z']
        self.cache = {}

    def m(self, op, a, b=None, clamp=False):
        return g.math_node(self.tree, op, a, b, clamp)

    def mul(self, a, b, clamp=False):
        return self.m('MULTIPLY', a, b, clamp)

    def add(self, a, b, clamp=False):
        return self.m('ADD', a, b, clamp)

    def sub(self, a, b, clamp=False):
        return self.m('SUBTRACT', a, b, clamp)

    def most(self, a, b):
        return self.m('MAXIMUM', a, b)

    def least(self, a, b):
        return self.m('MINIMUM', a, b)

    def clamp(self, a):
        return self.m('MULTIPLY', a, 1.0, True)

    def ramp(self, x, low, high):
        return g.ramp(self.tree, x, low, high)

    def mix(self, factor, a, b, blend_type='MIX'):
        return g.mix_color(self.tree, factor, rgba(a) if isinstance(a, tuple) else a, rgba(b) if isinstance(b, tuple) else b, blend_type)

    def lerp(self, factor, a, b):
        return g.mix_value(self.tree, factor, a, b)

    def mapping(self, scale=(1.0, 1.0, 1.0), offset=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), source=None):
        node = self.tree.nodes.new('ShaderNodeMapping')
        node.inputs['Location'].default_value = offset
        node.inputs['Rotation'].default_value = rotation
        node.inputs['Scale'].default_value = scale
        self.tree.links.new(source if source is not None else self.object, node.inputs['Vector'])
        return node.outputs['Vector']

    def noise(self, scale, detail=4.0, rough=0.55, stretch=None, offset=None, distortion=0.0, source=None, rotation=None, output='Fac'):
        node = self.tree.nodes.new('ShaderNodeTexNoise')
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = rough
        node.inputs['Distortion'].default_value = distortion
        vector = source if source is not None else self.object
        if stretch is not None or offset is not None or rotation is not None:
            vector = self.mapping(stretch or (1.0, 1.0, 1.0), offset or (0.0, 0.0, 0.0), rotation or (0.0, 0.0, 0.0), vector)
        self.tree.links.new(vector, node.inputs['Vector'])
        return node.outputs[output]

    def voronoi(self, scale, feature='F1', output='Distance', stretch=None, offset=None, randomness=1.0, source=None):
        node = self.tree.nodes.new('ShaderNodeTexVoronoi')
        node.feature = feature
        node.inputs['Scale'].default_value = scale
        node.inputs['Randomness'].default_value = randomness
        vector = source if source is not None else self.object
        if stretch is not None or offset is not None:
            vector = self.mapping(stretch or (1.0, 1.0, 1.0), offset or (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), vector)
        self.tree.links.new(vector, node.inputs['Vector'])
        return node.outputs[output]

    def vector(self, operation, a, b=None, scale=None):
        node = self.tree.nodes.new('ShaderNodeVectorMath')
        node.operation = operation
        g_link(self.tree, a, node.inputs[0])
        if b is not None:
            g_link(self.tree, b, node.inputs[1])
        if scale is not None:
            node.inputs['Scale'].default_value = scale
        return node.outputs['Vector'] if operation not in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else node.outputs['Value']

    def warped(self, amount, scale=3.0, source=None):
        node = self.tree.nodes.new('ShaderNodeTexNoise')
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = 3.0
        self.tree.links.new(source if source is not None else self.object, node.inputs['Vector'])
        offset = self.vector('SUBTRACT', node.outputs['Color'], (0.5, 0.5, 0.5))
        return self.vector('ADD', source if source is not None else self.object, self.vector('SCALE', offset, scale=amount))

    def photo(self, path, scale, colorspace='sRGB', source=None):
        return g.photo(self.tree, source if source is not None else self.object, path, scale, colorspace)

    def chan(self, color, which='Red'):
        return g.channel(self.tree, color, which)

    def palette(self, factor, stops, constant=False):
        node = self.tree.nodes.new('ShaderNodeValToRGB')
        ramp_data = node.color_ramp
        ramp_data.interpolation = 'CONSTANT' if constant else 'LINEAR'
        while len(ramp_data.elements) > 1:
            ramp_data.elements.remove(ramp_data.elements[-1])
        ramp_data.elements[0].position = stops[0][0]
        ramp_data.elements[0].color = rgba(stops[0][1])
        for position, color in stops[1:]:
            element = ramp_data.elements.new(position)
            element.color = rgba(color)
        self.tree.links.new(factor, node.inputs['Fac'])
        return node.outputs['Color']

    def edge(self, radius=0.006):
        key = ("edge", radius)
        if key not in self.cache:
            bevel = self.tree.nodes.new('ShaderNodeBevel')
            bevel.samples = 6
            bevel.inputs['Radius'].default_value = radius
            dot = self.tree.nodes.new('ShaderNodeVectorMath')
            dot.operation = 'DOT_PRODUCT'
            self.tree.links.new(bevel.outputs['Normal'], dot.inputs[0])
            self.tree.links.new(self.normal, dot.inputs[1])
            self.cache[key] = self.ramp(self.sub(1.0, dot.outputs['Value']), 0.004, 0.07)
        return self.cache[key]

    def cavity(self, distance=0.06):
        key = ("cavity", distance)
        if key not in self.cache:
            occlusion = self.tree.nodes.new('ShaderNodeAmbientOcclusion')
            occlusion.samples = 12
            occlusion.only_local = True
            occlusion.inputs['Distance'].default_value = distance
            self.cache[key] = self.ramp(self.sub(1.0, occlusion.outputs['AO']), 0.12, 0.75)
        return self.cache[key]

    def tint(self, color):
        if "tint" not in self.cache:
            node = self.tree.nodes.new('ShaderNodeAttribute')
            node.attribute_type = 'GEOMETRY'
            node.attribute_name = "tint"
            self.cache["tint"] = node.outputs['Color']
        return self.mix(1.0, color, self.cache["tint"], 'MULTIPLY')

    def up(self, low=0.3, high=0.9):
        return self.ramp(self.nz, low, high)

    def ground(self, height=0.5):
        return self.ramp(self.wz, height, 0.0)

    def text(self, key):
        node = self.tree.nodes.new('ShaderNodeUVMap')
        node.uv_map = "TextMap"
        texture = self.tree.nodes.new('ShaderNodeTexImage')
        texture.image = labels[key]
        texture.extension = 'CLIP'
        texture.interpolation = 'Cubic'
        self.tree.links.new(node.outputs['UV'], texture.inputs['Vector'])
        return self.chan(texture.outputs['Color'], 'Red')

    def finish(self, color, rough, metal, height=None, strength=0.35, distance=0.002, round_radius=0.003):
        g_link(self.tree, color, self.shader.inputs['Base Color'])
        g_link(self.tree, rough, self.shader.inputs['Roughness'])
        g_link(self.tree, metal, self.shader.inputs['Metallic'])
        bump = self.tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = strength
        bump.inputs['Distance'].default_value = distance
        if height is not None:
            g_link(self.tree, height, bump.inputs['Height'])
        rounder = self.tree.nodes.new('ShaderNodeBevel')
        rounder.samples = 6
        rounder.inputs['Radius'].default_value = round_radius
        self.tree.links.new(bump.outputs['Normal'], rounder.inputs['Normal'])
        self.tree.links.new(rounder.outputs['Normal'], self.shader.inputs['Normal'])


def g_link(tree, value, socket):
    if isinstance(value, (int, float)):
        socket.default_value = value
    elif isinstance(value, tuple):
        socket.default_value = rgba(value) if len(socket.default_value) == 4 else value
    else:
        tree.links.new(value, socket)


def rust_color(gr, s=1.0, dark=0.0):
    photo = gr.photo(os.path.join(source_textures, "rusty_metal_04", "rusty_metal_04_diff_2k.jpg"), 1.4 / s)
    mottle = gr.ramp(gr.noise(4.0 / s, 5.0, 0.6), 0.3, 0.75)
    deep = gr.mix(mottle, (0.09, 0.035, 0.016), (0.2, 0.075, 0.028))
    result = gr.mix(0.55, deep, photo)
    if dark > 0.0:
        result = gr.mix(dark, result, (0.035, 0.018, 0.01))
    return result


def weather(gr, color, rough, p, s, height=None):
    cavity = gr.cavity(p.get("cavity", 0.07) * s)
    up = gr.up()
    side = gr.sub(1.0, gr.up(0.2, 0.75))
    dirt = p.get("dirt", 0.4)
    grime_tone = p.get("grime_color", (0.06, 0.05, 0.038))
    if dirt > 0.0:
        color = gr.mix(dirt * 0.3, color, scaled(grime_tone, 1.6))
        stains = gr.mul(gr.ramp(gr.noise(1.7 / s, 5.0, 0.62, offset=(4.0, 1.0, 6.0)), 0.42, 0.74), dirt * 0.85, True)
        color = gr.mix(gr.mul(stains, 0.7), color, scaled(grime_tone, 1.25))
        runs = gr.ramp(gr.noise(1.0, 4.0, 0.55, stretch=(18.0 / s, 18.0 / s, 0.8 / s), offset=(1.0, 3.0, 0.0)), 0.5, 0.74)
        runs = gr.mul(gr.mul(runs, side), gr.mul(gr.ramp(gr.noise(0.9 / s, 2.0, 0.5, offset=(9.0, 2.0, 7.0)), 0.35, 0.65), dirt * 1.2), True)
        color = gr.mix(gr.mul(runs, 0.6), color, scaled(grime_tone, 0.9))
        splash = gr.mul(gr.ground(p.get("splash", 0.45)), gr.ramp(gr.noise(4.0 / s, 5.0, 0.62, offset=(2.0, 9.0, 4.0)), 0.25, 0.6))
        grime = gr.mul(gr.add(gr.mul(cavity, 1.4), gr.mul(splash, 1.5)), dirt, True)
        color = gr.mix(gr.mul(grime, 0.92), color, grime_tone)
        rough = gr.lerp(gr.most(grime, stains), rough, 0.93)
        sooty = gr.mul(gr.mul(cavity, gr.ramp(gr.noise(9.0 / s, 4.0, 0.6), 0.35, 0.7)), dirt, True)
        color = gr.mix(sooty, color, (0.018, 0.016, 0.013))
        dust = gr.mul(gr.mul(gr.add(up, 0.15), gr.ramp(gr.noise(2.6 / s, 5.0, 0.6), 0.3, 0.7)), dirt * 0.75, True)
        color = gr.mix(dust, color, p.get("dust_color", (0.2, 0.18, 0.15)))
        rough = gr.lerp(dust, rough, 0.95)
    moss = p.get("moss", 0.0)
    if moss > 0.0:
        patches = gr.ramp(gr.noise(2.0 / s, 5.0, 0.64, offset=(3.0, 3.0, 8.0)), 0.6 - moss * 0.22, 0.66 - moss * 0.22)
        where = gr.mul(gr.add(gr.mul(up, 0.7), gr.add(gr.mul(cavity, 1.0), gr.mul(gr.ground(0.35), 0.6))), patches, True)
        where = gr.mul(where, gr.ramp(gr.noise(45.0 / s, 4.0, 0.7), 0.28, 0.5), True)
        tone = gr.mix(gr.ramp(gr.noise(12.0 / s, 3.0, 0.5), 0.3, 0.7), (0.03, 0.042, 0.01), (0.075, 0.09, 0.02))
        color = gr.mix(where, color, tone)
        rough = gr.lerp(where, rough, 0.96)
        if height is not None:
            height = gr.add(height, gr.mul(where, 0.6))
    lichen = p.get("lichen", 0.0)
    if lichen > 0.0:
        crust = gr.ramp(gr.noise(5.5 / s, 6.0, 0.7, offset=(5.0, 2.0, 1.0), distortion=0.4), 0.66 - lichen * 0.12, 0.69 - lichen * 0.12)
        crust = gr.mul(crust, gr.ramp(gr.noise(1.2 / s, 3.0, 0.5), 0.4, 0.6), True)
        rim = gr.sub(gr.ramp(gr.noise(5.5 / s, 6.0, 0.7, offset=(5.0, 2.0, 1.0), distortion=0.4), 0.63 - lichen * 0.12, 0.66 - lichen * 0.12), crust, True)
        pale = gr.mix(gr.ramp(gr.noise(20.0 / s, 3.0, 0.6), 0.3, 0.7), (0.2, 0.215, 0.18), (0.29, 0.3, 0.25))
        color = gr.mix(gr.mul(crust, 0.8), color, pale)
        color = gr.mix(gr.mul(gr.mul(rim, gr.ramp(gr.noise(1.2 / s, 3.0, 0.5), 0.4, 0.6)), 0.5), color, (0.06, 0.06, 0.05))
        yellow = gr.mul(gr.mul(gr.ramp(gr.noise(9.0 / s, 5.0, 0.68, offset=(1.0, 8.0, 3.0)), 0.7, 0.73), up), lichen, True)
        color = gr.mix(gr.mul(yellow, 0.85), color, (0.4, 0.22, 0.04))
        rough = gr.lerp(gr.most(crust, yellow), rough, 0.92)
        if height is not None:
            height = gr.add(height, gr.mul(gr.most(crust, yellow), 0.3))
    return color, rough, height


def look_paint(gr, p):
    s = p.get("scale", 1.0)
    base = p["color"]
    chalk = blend(base, (0.62, 0.6, 0.57), p.get("chalk", 0.35))
    under = p.get("under", (0.42, 0.41, 0.38))
    primer = p.get("primer", (0.14, 0.055, 0.035))
    edge = gr.edge(p.get("edge", 0.006) * s)
    cavity = gr.cavity(p.get("cavity", 0.07) * s)
    up = gr.up()
    mottle = gr.ramp(gr.noise(1.4 / s, 3.0, 0.5), 0.3, 0.7)
    color = gr.tint(gr.mix(mottle, scaled(base, 0.82), scaled(base, 1.1)))
    height = gr.mul(gr.noise(160.0 / s, 3.0, 0.55), 0.12)
    if "text" in p:
        key, ink, relief = p["text"]
        letters = gr.text(key)
        color = gr.mix(letters, color, ink)
        height = gr.add(height, gr.mul(letters, relief))
    fade = gr.mul(gr.mul(gr.ramp(gr.noise(0.6 / s, 3.0, 0.5), 0.25, 0.7), p.get("fade", 0.4) * 1.4), gr.add(0.45, gr.mul(up, 0.55)), True)
    color = gr.mix(fade, color, chalk)
    bleed_amount = p.get("bleed", 0.35)
    if bleed_amount > 0.0:
        bleed = gr.mul(gr.ramp(gr.noise(2.4 / s, 6.0, 0.62, offset=(8.0, 3.0, 5.0)), 0.5, 0.78), bleed_amount * 1.3, True)
        bleed = gr.mul(bleed, gr.ramp(gr.noise(18.0 / s, 4.0, 0.6), 0.25, 0.6), True)
        color = gr.mix(gr.mul(bleed, 0.75), color, p.get("bleed_color", (0.11, 0.045, 0.02)))
    chips = p.get("chips", 0.4)
    blotch = gr.ramp(gr.noise(2.2 / s, 6.0, 0.65, offset=(3.1, 1.7, 0.4)), 0.4, 0.76)
    coverage = gr.add(gr.add(gr.mul(edge, 1.6 * min(1.0, chips * 2.2)), gr.mul(blotch, chips * 2.1)), gr.mul(cavity, 0.45 * chips))
    if p.get("rot", 0.0) > 0.0:
        coverage = gr.add(coverage, gr.mul(gr.mul(gr.ground(p.get("rot_height", 0.5)), gr.ramp(gr.noise(3.0 / s, 5.0, 0.6, offset=(6.0, 4.0, 2.0)), 0.3, 0.65)), p["rot"] * 1.5))
    jag = gr.add(coverage, gr.mul(gr.sub(gr.noise(44.0 / s, 6.0, 0.72), 0.5), 0.95))
    halo = gr.ramp(jag, 0.46, 0.6)
    layer_a = gr.ramp(jag, 0.58, 0.61)
    layer_b = gr.ramp(jag, 0.7, 0.73)
    layer_c = gr.ramp(jag, 0.82, 0.86)
    color = gr.mix(gr.mul(halo, 0.35), color, scaled(primer, 0.7))
    color = gr.mix(layer_a, color, under)
    color = gr.mix(layer_b, color, primer)
    rust = rust_color(gr, s, 0.15)
    color = gr.mix(layer_c, color, rust)
    streaks = p.get("streaks", 0.35)
    if streaks > 0.0:
        runs = gr.ramp(gr.noise(1.0, 3.0, 0.5, stretch=(26.0 / s, 26.0 / s, 1.2 / s)), 0.52, 0.76)
        runs = gr.mul(gr.mul(runs, gr.ramp(gr.noise(1.1 / s, 3.0, 0.5, offset=(7.0, 2.0, 1.0)), 0.38, 0.66)), streaks * 1.6, True)
        runs = gr.mul(runs, gr.sub(1.0, gr.mul(up, 0.8)), True)
        color = gr.mix(gr.mul(runs, 0.8), color, p.get("streak_color", (0.12, 0.05, 0.022)))
    gloss = p.get("gloss", 0.45)
    rough = gr.lerp(fade, gloss, 0.82)
    rough = gr.lerp(layer_a, rough, 0.6)
    rough = gr.lerp(layer_b, rough, 0.72)
    rough = gr.lerp(layer_c, rough, 0.88)
    bright = gr.mul(gr.mul(edge, layer_c), gr.ramp(gr.noise(30.0 / s, 3.0, 0.6), 0.55, 0.62), True)
    color = gr.mix(gr.mul(bright, p.get("bare", 0.6)), color, (0.36, 0.35, 0.33))
    rough = gr.lerp(gr.mul(bright, p.get("bare", 0.6)), rough, 0.35)
    metal = gr.mul(bright, p.get("bare", 0.6))
    color, rough, height = weather(gr, color, rough, p, s, height)
    dents = p.get("dents", 0.0)
    relief = gr.sub(height, gr.add(gr.mul(layer_a, 0.25), gr.add(gr.mul(layer_b, 0.25), gr.mul(layer_c, 0.3))))
    relief = gr.add(relief, gr.mul(gr.mul(layer_c, gr.noise(90.0 / s, 4.0, 0.7)), 0.5))
    if dents > 0.0:
        relief = gr.add(relief, gr.mul(gr.noise(1.8 / s, 3.0, 0.5, offset=(5.0, 5.0, 5.0)), dents * 40.0))
    gr.finish(color, rough, metal, relief, p.get("bump", 0.35), 0.0004 * s, p.get("round", 0.003) * s)


def look_metal(gr, p):
    s = p.get("scale", 1.0)
    kind = p.get("kind", "steel")
    edge = gr.edge(p.get("edge", 0.005) * s)
    cavity = gr.cavity(p.get("cavity", 0.06) * s)
    grain = gr.photo(os.path.join(acg_textures, "Metal027", "Metal027_2K-JPG_Roughness.jpg"), 1.6 / s, 'Non-Color')
    tone = {"steel": (0.2, 0.2, 0.2), "iron": (0.06, 0.055, 0.05), "galvanised": (0.33, 0.34, 0.34), "chrome": (0.62, 0.62, 0.6), "blackened": (0.035, 0.034, 0.033), "aluminium": (0.5, 0.5, 0.49), "weld": (0.07, 0.065, 0.06), "rust": (0.1, 0.05, 0.03)}[kind]
    tone = p.get("tone", tone)
    mottle = gr.ramp(gr.noise(3.0 / s, 4.0, 0.55), 0.3, 0.75)
    color = gr.tint(gr.mix(mottle, scaled(tone, 0.75), scaled(tone, 1.2)))
    color = gr.mix(gr.mul(gr.ramp(gr.chan(grain), 0.3, 0.8), 0.4), color, scaled(tone, 0.65))
    metal = {"steel": 0.85, "iron": 0.6, "galvanised": 0.9, "chrome": 1.0, "blackened": 0.45, "aluminium": 0.9, "weld": 0.6, "rust": 0.3}[kind]
    rough = gr.lerp(gr.chan(grain), {"steel": 0.42, "iron": 0.62, "galvanised": 0.4, "chrome": 0.12, "blackened": 0.6, "aluminium": 0.35, "weld": 0.5, "rust": 0.8}[kind], {"steel": 0.62, "iron": 0.8, "galvanised": 0.6, "chrome": 0.3, "blackened": 0.75, "aluminium": 0.55, "weld": 0.7, "rust": 0.95}[kind])
    height = gr.mul(gr.chan(grain), 0.3)
    if kind == "galvanised":
        crystals = gr.chan(gr.voronoi(55.0 / s, 'F1', 'Color'), 'Red')
        color = gr.mix(gr.mul(crystals, 0.5), color, scaled(tone, 1.25))
        white = gr.mul(gr.ramp(gr.noise(9.0 / s, 5.0, 0.6), 0.55, 0.7), 0.7, True)
        color = gr.mix(white, color, (0.46, 0.46, 0.43))
        rough = gr.lerp(white, rough, 0.8)
        metal = gr.lerp(white, metal, 0.3)
    if kind == "weld":
        ripple = gr.voronoi(260.0 / s, 'F1', 'Distance', randomness=0.6)
        height = gr.add(height, gr.mul(gr.ramp(ripple, 0.0, 0.6), 0.6))
        heat = gr.mul(gr.ramp(gr.noise(25.0 / s, 3.0, 0.5), 0.45, 0.7), 0.6)
        color = gr.mix(heat, color, (0.09, 0.07, 0.1))
    rust_amount = p.get("rust", 0.4)
    patches = gr.mul(gr.ramp(gr.noise(2.2 / s, 6.0, 0.62, offset=(1.3, 4.1, 2.2)), 0.6 - rust_amount * 0.3, 0.72 - rust_amount * 0.3), gr.ramp(gr.noise(22.0 / s, 5.0, 0.6), 0.32, 0.6), True)
    rusty = gr.mul(gr.add(gr.add(gr.mul(cavity, 1.2 * rust_amount), patches), gr.mul(edge, 0.3 * rust_amount)), gr.ramp(gr.noise(70.0 / s, 5.0, 0.7), 0.3, 0.6), True)
    if kind == "rust":
        rusty = gr.add(0.75, gr.mul(rusty, 0.25))
    pits = gr.mul(gr.ramp(gr.noise(160.0 / s, 2.0, 0.5), 0.66, 0.74), rust_amount * 0.8, True)
    rust = rust_color(gr, s)
    color = gr.mix(rusty, color, rust)
    color = gr.mix(pits, color, (0.04, 0.02, 0.01))
    rough = gr.lerp(gr.most(rusty, pits), rough, 0.9)
    metal = gr.lerp(gr.most(rusty, pits), metal, 0.05)
    height = gr.add(gr.sub(height, gr.mul(pits, 0.5)), gr.mul(rusty, gr.mul(gr.noise(120.0 / s, 4.0, 0.7), 0.6)))
    wear = gr.mul(edge, gr.ramp(gr.noise(40.0 / s, 4.0, 0.6), 0.45, 0.6), True)
    wear = gr.mul(wear, gr.sub(1.0, rusty), True)
    color = gr.mix(gr.mul(wear, 0.7), color, (0.42, 0.41, 0.39))
    rough = gr.lerp(wear, rough, 0.3)
    metal = gr.lerp(wear, metal, 1.0)
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, metal, height, p.get("bump", 0.3), 0.0004 * s, p.get("round", 0.002) * s)


def look_stone(gr, p):
    s = p.get("scale", 1.0)
    kind = p.get("kind", "granite")
    cavity = gr.cavity(p.get("cavity", 0.08) * s)
    edge = gr.edge(p.get("edge", 0.008) * s)
    if kind == "granite":
        tint = p.get("tint", (0.21, 0.18, 0.165))
        cells = gr.chan(gr.voronoi(230.0 / s, 'F1', 'Color', randomness=1.0), 'Red')
        minerals = gr.palette(cells, p.get("minerals", [(0.0, (0.27, 0.195, 0.175)), (0.3, (0.2, 0.19, 0.18)), (0.58, (0.31, 0.27, 0.255)), (0.83, (0.13, 0.12, 0.112)), (0.93, (0.03, 0.029, 0.028))]), True)
        color = gr.mix(p.get("blend", 0.4), minerals, tint)
        coarse = gr.chan(gr.voronoi(60.0 / s, 'F1', 'Color', randomness=1.0, offset=(3.0, 1.0, 2.0)), 'Green')
        color = gr.mix(gr.mul(gr.ramp(coarse, 0.55, 0.95), 0.3), color, scaled(tint, 1.18))
        color = gr.mix(gr.mul(gr.ramp(gr.noise(1.2 / s, 4.0, 0.55), 0.3, 0.75), 0.4), color, scaled(tint, 0.72))
        patina = gr.mul(gr.ramp(gr.noise(1.6 / s, 5.0, 0.6, offset=(1.0, 2.0, 3.0)), 0.3, 0.72), p.get("patina", 0.55), True)
        color = gr.tint(gr.mix(patina, color, p.get("patina_color", (0.125, 0.13, 0.115))))
        rough = gr.lerp(gr.ramp(cells, 0.2, 0.8), 0.62, 0.86)
        height = gr.add(gr.mul(gr.noise(70.0 / s, 4.0, 0.65), 0.5), gr.mul(gr.ramp(cells, 0.85, 0.95), -0.25))
        tool = p.get("tooled", 0.0)
        if tool > 0.0:
            height = gr.add(height, gr.mul(gr.noise(1.0, 2.0, 0.5, stretch=(160.0 / s, 9.0 / s, 160.0 / s)), tool))
    elif kind == "concrete":
        photo = gr.photo(os.path.join(acg_textures, "Concrete046", "Concrete046_2K-JPG_Color.jpg"), 0.8 / s)
        color = gr.mix(1.0, photo, scaled(p.get("tint", (0.34, 0.33, 0.3)), 2.2), 'MULTIPLY')
        rough = 0.88
        height = gr.chan(gr.photo(os.path.join(acg_textures, "Concrete046", "Concrete046_2K-JPG_Displacement.jpg"), 0.8 / s, 'Non-Color'))
    else:
        id_color = gr.voronoi(p.get("stones", 5.5) / s, 'F1', 'Color', stretch=(1.0, 1.0, 1.6), randomness=0.9)
        joint = gr.voronoi(p.get("stones", 5.5) / s, 'DISTANCE_TO_EDGE', 'Distance', stretch=(1.0, 1.0, 1.6), randomness=0.9)
        pick = gr.chan(id_color, 'Red')
        stone = gr.palette(pick, [(0.0, (0.27, 0.2, 0.18)), (0.2, (0.21, 0.2, 0.19)), (0.4, (0.3, 0.255, 0.235)), (0.6, (0.16, 0.145, 0.135)), (0.8, (0.33, 0.29, 0.26)), (0.92, (0.24, 0.17, 0.14))], True)
        grains = gr.chan(gr.voronoi(200.0 / s, 'F1', 'Color'), 'Red')
        stone = gr.mix(gr.mul(gr.ramp(grains, 0.75, 0.95), 0.5), stone, (0.05, 0.045, 0.04))
        stone = gr.mix(gr.mul(gr.ramp(grains, 0.0, 0.3), 0.25), stone, (0.42, 0.39, 0.36))
        stone = gr.mix(gr.mul(gr.ramp(gr.noise(1.6 / s, 5.0, 0.6, offset=(1.0, 2.0, 3.0)), 0.3, 0.72), 0.5), stone, (0.16, 0.165, 0.145))
        stone = gr.tint(stone)
        mortar = gr.ramp(joint, p.get("joint", 0.05), 0.0)
        mortar_color = gr.mix(gr.ramp(gr.noise(8.0 / s), 0.3, 0.7), (0.3, 0.28, 0.24), (0.2, 0.19, 0.16))
        color = gr.mix(mortar, stone, mortar_color)
        rough = gr.lerp(mortar, 0.75, 0.93)
        bulge = gr.ramp(joint, 0.0, 0.28)
        height = gr.add(gr.mul(bulge, 3.0), gr.mul(gr.noise(25.0 / s, 5.0, 0.65), 0.8))
        cavity = gr.most(cavity, gr.mul(mortar, 0.7))
    streaks = p.get("streaks", 0.3)
    if streaks > 0.0:
        runs = gr.mul(gr.ramp(gr.noise(1.0, 3.0, 0.5, stretch=(14.0 / s, 14.0 / s, 0.9 / s)), 0.55, 0.78), streaks, True)
        color = gr.mix(gr.mul(runs, 0.5), color, p.get("streak_color", (0.05, 0.05, 0.045)))
    color = gr.mix(gr.mul(edge, 0.25), color, scaled(p.get("tint", (0.36, 0.28, 0.25)), 1.3))
    if "text" in p:
        key, ink, relief = p["text"]
        letters = gr.text(key)
        if relief < 0.0:
            letters = gr.mul(letters, gr.ramp(gr.noise(30.0 / s, 4.0, 0.6), 0.25, 0.4), True)
        color = gr.mix(gr.mul(letters, 0.85), color, ink)
        height = gr.add(height, gr.mul(letters, relief))
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, 0.0, height, p.get("bump", 0.4), 0.0008 * s, p.get("round", 0.006) * s)


def look_wood(gr, p):
    s = p.get("scale", 1.0)
    along = p.get("along", "X")
    edge = gr.edge(p.get("edge", 0.004) * s)
    cavity = gr.cavity(p.get("cavity", 0.05) * s)
    stretch = {"X": (1.0, 26.0, 26.0), "Y": (26.0, 1.0, 26.0), "Z": (26.0, 26.0, 1.0)}[along]
    grain = gr.noise(3.5 / s, 6.0, 0.62, stretch=stretch, distortion=0.6)
    fibres = gr.noise(4.0 / s, 3.0, 0.55, stretch=tuple(value * 6.0 if value > 1.0 else value * 2.0 for value in stretch))
    light = p.get("light", (0.24, 0.2, 0.15))
    dark = p.get("dark", (0.1, 0.08, 0.06))
    color = gr.tint(gr.mix(gr.ramp(grain, 0.35, 0.68), light, dark))
    color = gr.mix(gr.mul(gr.ramp(fibres, 0.55, 0.75), 0.45), color, scaled(dark, 0.6))
    silver = p.get("silver", 0.6)
    weathered = gr.mul(gr.ramp(gr.noise(1.4 / s, 3.0, 0.5), 0.25, 0.7), silver, True)
    color = gr.mix(weathered, color, gr.mix(gr.ramp(fibres, 0.4, 0.7), (0.33, 0.32, 0.3), (0.2, 0.19, 0.18)))
    cracks = gr.ramp(gr.noise(1.0, 2.0, 0.5, stretch=tuple(value * 9.0 / s if value > 1.0 else value * 0.6 / s for value in stretch)), 0.69, 0.73)
    cracks = gr.mul(cracks, p.get("cracks", 0.5), True)
    color = gr.mix(cracks, color, (0.02, 0.016, 0.012))
    rough = gr.lerp(cracks, 0.78, 0.95)
    height = gr.sub(gr.mul(gr.ramp(fibres, 0.3, 0.8), 0.4), gr.mul(cracks, 1.0))
    paint = p.get("paint")
    if paint is not None:
        peel = gr.add(gr.mul(edge, 1.6), gr.mul(gr.ramp(gr.noise(3.0 / s, 6.0, 0.62), 0.45, 0.72), p.get("peel", 0.6)))
        peel = gr.add(peel, gr.mul(gr.sub(gr.noise(40.0 / s, 5.0, 0.7), 0.5), 0.8))
        bare = gr.ramp(peel, 0.62, 0.68)
        coat = gr.mix(gr.ramp(gr.noise(1.5 / s, 3.0, 0.5), 0.3, 0.7), scaled(paint, 0.9), blend(paint, (0.6, 0.6, 0.58), 0.3))
        coat = gr.mix(gr.mul(gr.ramp(fibres, 0.5, 0.8), 0.25), coat, scaled(paint, 0.75))
        color = gr.mix(bare, coat, color)
        rough = gr.lerp(bare, 0.7, rough)
        height = gr.add(height, gr.mul(gr.sub(1.0, bare), 0.6))
    if "text" in p:
        key, ink, relief = p["text"]
        letters = gr.text(key)
        color = gr.mix(letters, color, ink)
        height = gr.add(height, gr.mul(letters, relief))
    color = gr.mix(gr.mul(edge, 0.3), color, scaled(light, 1.25))
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, 0.0, height, p.get("bump", 0.4), 0.0006 * s, p.get("round", 0.003) * s)


def look_fabric(gr, p):
    s = p.get("scale", 1.0)
    kind = p.get("kind", "canvas")
    cavity = gr.cavity(p.get("cavity", 0.08) * s)
    weave = gr.photo(os.path.join(raw_textures, "hessian_230", "hessian_230_disp_2k.jpg"), p.get("weave", 6.0) / s, 'Non-Color')
    if kind == "hessian":
        photo = gr.photo(os.path.join(raw_textures, "hessian_230", "hessian_230_diff_2k.jpg"), p.get("weave", 6.0) / s)
        color = gr.mix(1.0, photo, p.get("tint", (0.62, 0.52, 0.38)), 'MULTIPLY')
        color = gr.mix(gr.ramp(gr.noise(2.0 / s, 3.0, 0.5), 0.3, 0.75), gr.mix(1.0, color, (0.7, 0.7, 0.7), 'MULTIPLY'), color)
        rough = 0.95
    elif kind == "stripes":
        axis = {"X": gr.ox, "Y": gr.oy, "Z": gr.oz}[p.get("axis", "X")]
        width = p.get("width", 0.14)
        phase = gr.m('FRACT', gr.add(gr.mul(axis, 1.0 / (2.0 * width)), p.get("phase", 0.0)))
        stripe = gr.mul(gr.ramp(phase, 0.47, 0.53), gr.ramp(phase, 1.0, 0.97), True)
        color = gr.mix(stripe, p.get("a", (0.45, 0.03, 0.025)), p.get("b", (0.62, 0.6, 0.55)))
        fade = gr.mul(gr.ramp(gr.noise(0.8 / s, 3.0, 0.5), 0.3, 0.7), p.get("fade", 0.5), True)
        color = gr.mix(fade, color, gr.mix(stripe, blend(p.get("a", (0.45, 0.03, 0.025)), (0.6, 0.55, 0.5), 0.5), (0.58, 0.56, 0.52)))
        rough = 0.9
    elif kind == "vinyl":
        crackle = gr.voronoi(34.0 / s, 'DISTANCE_TO_EDGE', 'Distance', randomness=1.0)
        lines = gr.mul(gr.ramp(crackle, 0.03, 0.0), gr.ramp(gr.noise(2.5 / s, 4.0, 0.6), 0.5, 0.68), True)
        tone = p.get("tint", (0.08, 0.05, 0.035))
        color = gr.mix(gr.ramp(gr.noise(3.0 / s, 4.0, 0.55), 0.3, 0.7), scaled(tone, 0.8), scaled(tone, 1.25))
        worn = gr.mul(gr.ramp(gr.noise(4.0 / s, 5.0, 0.6, offset=(3.0, 3.0, 3.0)), 0.55, 0.7), 0.6, True)
        color = gr.mix(worn, color, scaled(tone, 1.8))
        color = gr.mix(gr.mul(lines, 0.6), color, (0.13, 0.115, 0.095))
        rough = gr.lerp(gr.most(lines, worn), 0.5, 0.85)
        weave = gr.add(gr.mul(lines, -1.0), gr.mul(gr.noise(120.0 / s, 3.0, 0.6), 0.15))
    else:
        tone = p.get("tint", (0.18, 0.16, 0.13))
        color = gr.mix(gr.ramp(gr.noise(2.5 / s, 4.0, 0.55), 0.3, 0.7), scaled(tone, 0.75), scaled(tone, 1.15))
        color = gr.mix(gr.mul(gr.ramp(gr.chan(weave), 0.3, 0.7), 0.3), color, scaled(tone, 0.6))
        rough = 0.93
    stains = gr.mul(gr.ramp(gr.noise(1.6 / s, 4.0, 0.6, offset=(2.0, 7.0, 1.0)), 0.58, 0.72), p.get("stains", 0.5), True)
    color = gr.mix(gr.mul(stains, 0.55), color, (0.12, 0.1, 0.06))
    mildew = gr.mul(gr.ramp(gr.voronoi(55.0 / s, 'F1', 'Distance'), 0.16, 0.05), gr.mul(gr.ramp(gr.noise(2.0 / s, 3.0, 0.5), 0.55, 0.7), p.get("mildew", 0.4)), True)
    color = gr.mix(mildew, color, (0.03, 0.035, 0.025))
    height = gr.chan(weave) if not isinstance(weave, tuple) and kind != "vinyl" else weave
    if "text" in p:
        key, ink, relief = p["text"]
        letters = gr.text(key)
        color = gr.mix(letters, color, ink)
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, 0.0, height, p.get("bump", 0.3), 0.0005 * s, p.get("round", 0.003) * s)


def look_rubber(gr, p):
    s = p.get("scale", 1.0)
    edge = gr.edge(0.004 * s)
    cavity = gr.cavity(0.04 * s)
    tone = p.get("tint", (0.022, 0.021, 0.02))
    grain = gr.photo(os.path.join(acg_textures, "Rubber004", "Rubber004_2K-JPG_Roughness.jpg"), 3.0 / s, 'Non-Color')
    color = gr.mix(gr.ramp(gr.noise(4.0 / s, 4.0, 0.55), 0.3, 0.7), scaled(tone, 0.8), scaled(tone, 1.5))
    perished = gr.mul(gr.ramp(gr.noise(2.0 / s, 4.0, 0.6), 0.45, 0.75), p.get("perished", 0.5), True)
    color = gr.mix(perished, color, (0.065, 0.062, 0.058))
    cracks = gr.mul(gr.ramp(gr.voronoi(70.0 / s, 'DISTANCE_TO_EDGE', 'Distance', stretch=(1.0, 1.0, 3.0)), 0.03, 0.0), perished, True)
    color = gr.mix(cracks, color, (0.008, 0.008, 0.008))
    color = gr.mix(gr.mul(edge, 0.4), color, (0.08, 0.075, 0.07))
    rough = gr.lerp(gr.chan(grain), 0.7, 0.92)
    height = gr.sub(gr.mul(gr.chan(grain), 0.2), gr.mul(cracks, 1.0))
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, 0.0, height, p.get("bump", 0.3), 0.0004 * s, 0.002 * s)


def look_plastic(gr, p):
    s = p.get("scale", 1.0)
    edge = gr.edge(0.004 * s)
    tone = p["color"]
    color = gr.mix(gr.ramp(gr.noise(2.0 / s, 4.0, 0.55), 0.3, 0.7), scaled(tone, 0.85), scaled(tone, 1.08))
    fade = gr.mul(gr.mul(gr.ramp(gr.noise(0.9 / s, 3.0, 0.5), 0.3, 0.7), p.get("fade", 0.4)), gr.add(0.4, gr.mul(gr.up(), 0.6)), True)
    color = gr.mix(fade, color, blend(tone, (0.62, 0.6, 0.56), 0.45))
    scuffs = gr.mul(gr.mul(edge, gr.ramp(gr.noise(30.0 / s, 4.0, 0.6), 0.45, 0.62)), 1.0, True)
    color = gr.mix(gr.mul(scuffs, 0.6), color, blend(tone, (0.5, 0.48, 0.45), 0.6))
    if "text" in p:
        key, ink, relief = p["text"]
        letters = gr.text(key)
        color = gr.mix(letters, color, ink)
    rough = gr.lerp(fade, p.get("gloss", 0.45), 0.8)
    height = gr.mul(gr.noise(60.0 / s, 3.0, 0.6), 0.2)
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, 0.0, height, 0.2, 0.0004 * s, 0.003 * s)


def crack_lines(gr, s, impacts, reach, amount, spokes=11.0, width=0.0016):
    k = impacts / s
    scaled = gr.mapping((k, k, k), (4.0, 2.0, 7.0))
    node = gr.tree.nodes.new('ShaderNodeTexVoronoi')
    node.feature = 'F1'
    node.inputs['Scale'].default_value = 1.0
    node.inputs['Randomness'].default_value = 1.0
    gr.tree.links.new(scaled, node.inputs['Vector'])
    offset = gr.vector('SUBTRACT', scaled, node.outputs['Position'])
    split = gr.tree.nodes.new('ShaderNodeSeparateXYZ')
    gr.tree.links.new(offset, split.inputs['Vector'])
    distance = gr.mul(gr.vector('LENGTH', offset), 1.0 / k)
    across = gr.ramp(gr.m('ABSOLUTE', gr.nx), 0.4, 0.7)
    angle = gr.lerp(across, gr.m('ARCTAN2', split.outputs['Z'], split.outputs['X']), gr.m('ARCTAN2', split.outputs['Z'], split.outputs['Y']))
    warp = gr.sub(gr.noise(5.0 / s, 3.0, 0.6), 0.5)
    phase = gr.m('FRACT', gr.add(gr.mul(angle, spokes / tau), gr.mul(warp, 0.7)))
    arc = gr.mul(gr.mul(gr.m('ABSOLUTE', gr.sub(phase, 0.5)), tau / spokes), distance)
    radial = gr.mul(gr.ramp(arc, width, 0.0), gr.ramp(gr.add(distance, gr.mul(warp, 0.2)), reach, 0.03), True)
    ring_phase = gr.m('FRACT', gr.add(gr.mul(distance, 16.0), gr.mul(warp, 1.4)))
    ring = gr.ramp(gr.mul(gr.m('ABSOLUTE', gr.sub(ring_phase, 0.5)), 1.0 / 16.0), width, 0.0)
    ring = gr.mul(gr.mul(ring, gr.ramp(distance, reach * 0.6, 0.05)), gr.ramp(gr.noise(9.0 / s, 2.0, 0.5, offset=(1.0, 5.0, 2.0)), 0.48, 0.56), True)
    crush = gr.mul(gr.ramp(gr.voronoi(60.0 / s, 'DISTANCE_TO_EDGE', 'Distance'), 0.06, 0.0), gr.ramp(distance, 0.05, 0.01), True)
    return gr.mul(gr.most(gr.most(radial, ring), crush), amount * 1.2, True)


def look_glass(gr, p):
    s = p.get("scale", 1.0)
    dirt = gr.ramp(gr.noise(2.5 / s, 5.0, 0.6), 0.3, 0.75)
    color = gr.mix(dirt, p.get("tint", (0.012, 0.016, 0.018)), p.get("grime", (0.08, 0.075, 0.065)))
    rough = gr.lerp(dirt, 0.05, 0.6)
    height = 0.0
    cracked = p.get("cracked", 0.0)
    if cracked > 0.0:
        lines = crack_lines(gr, s, p.get("impacts", 1.7), p.get("reach", 0.32), cracked)
        color = gr.mix(lines, color, (0.3, 0.31, 0.3))
        rough = gr.lerp(lines, rough, 0.45)
        height = gr.mul(lines, -1.0)
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, 0.0, height, 0.3, 0.0004 * s, 0.002 * s)


def look_organic(gr, p):
    s = p.get("scale", 1.0)
    kind = p.get("kind", "moss")
    if kind == "moss":
        blades = gr.noise(90.0 / s, 5.0, 0.7)
        color = gr.mix(gr.ramp(gr.noise(6.0 / s, 4.0, 0.55), 0.3, 0.7), (0.03, 0.045, 0.01), (0.1, 0.12, 0.03))
        color = gr.mix(gr.mul(gr.ramp(blades, 0.55, 0.75), 0.5), color, (0.15, 0.16, 0.05))
        rough = 0.95
        height = blades
    elif kind == "leaves":
        cells = gr.voronoi(30.0 / s, 'F1', 'Color')
        pick = gr.chan(cells, 'Red')
        color = gr.palette(pick, [(0.0, (0.16, 0.07, 0.02)), (0.3, (0.09, 0.05, 0.02)), (0.55, (0.24, 0.12, 0.03)), (0.8, (0.05, 0.035, 0.02))], False)
        edge_lines = gr.ramp(gr.voronoi(30.0 / s, 'DISTANCE_TO_EDGE', 'Distance'), 0.03, 0.0)
        color = gr.mix(gr.mul(edge_lines, 0.8), color, (0.02, 0.015, 0.01))
        rough = 0.85
        height = gr.sub(gr.mul(gr.chan(cells, 'Green'), 0.5), edge_lines)
    elif kind == "dirt":
        color = gr.mix(gr.ramp(gr.noise(5.0 / s, 5.0, 0.6), 0.3, 0.7), (0.05, 0.04, 0.03), (0.12, 0.1, 0.075))
        stones = gr.ramp(gr.voronoi(60.0 / s, 'F1', 'Distance'), 0.25, 0.1)
        color = gr.mix(gr.mul(stones, 0.5), color, (0.2, 0.19, 0.17))
        rough = 0.95
        height = gr.add(gr.noise(30.0 / s, 5.0, 0.65), gr.mul(stones, 0.5))
    elif kind == "water":
        color = gr.mix(gr.ramp(gr.noise(3.0 / s, 4.0, 0.5), 0.3, 0.7), (0.008, 0.012, 0.008), (0.03, 0.04, 0.015))
        scum = gr.ramp(gr.noise(5.0 / s, 5.0, 0.6), 0.6, 0.7)
        color = gr.mix(gr.mul(scum, 0.8), color, (0.07, 0.09, 0.025))
        rough = gr.lerp(scum, 0.04, 0.7)
        height = gr.mul(gr.noise(8.0 / s, 3.0, 0.5), 0.1)
    else:
        color = gr.mix(gr.ramp(gr.noise(4.0 / s, 4.0, 0.6), 0.3, 0.7), p.get("tint", (0.4, 0.38, 0.33)), scaled(p.get("tint", (0.4, 0.38, 0.33)), 0.6))
        rough = 0.9
        height = gr.noise(40.0 / s, 4.0, 0.6)
        creases = p.get("creases", 0.0)
        if creases > 0.0:
            folds = gr.ramp(gr.voronoi(26.0 / s, 'DISTANCE_TO_EDGE', 'Distance', source=gr.warped(0.04 * s, 6.0 / s)), 0.05, 0.0)
            color = gr.mix(gr.mul(folds, creases * 0.6), color, scaled(p.get("tint", (0.4, 0.38, 0.33)), 0.45))
            height = gr.sub(height, gr.mul(folds, creases * 2.0))
        if "text" in p:
            key, ink, relief = p["text"]
            letters = gr.text(key)
            color = gr.mix(letters, color, ink)
    color, rough, height = weather(gr, color, rough, p, s, height)
    gr.finish(color, rough, 0.0, height, p.get("bump", 0.4), 0.001 * s, 0.003 * s)


def look_bronze(gr, p):
    s = p.get("scale", 1.0)
    edge = gr.edge(0.003 * s)
    cavity = gr.cavity(0.03 * s)
    base = p.get("tone", (0.2, 0.12, 0.05))
    color = gr.mix(gr.ramp(gr.noise(5.0 / s, 4.0, 0.55), 0.3, 0.7), scaled(base, 0.7), scaled(base, 1.1))
    verdigris = gr.mul(gr.add(gr.mul(cavity, 1.4), gr.ramp(gr.noise(3.0 / s, 5.0, 0.6), 0.5, 0.75)), p.get("verdigris", 0.7), True)
    green = gr.mix(gr.ramp(gr.noise(20.0 / s, 4.0, 0.6), 0.3, 0.7), (0.16, 0.3, 0.24), (0.1, 0.2, 0.15))
    color = gr.mix(verdigris, color, green)
    polish = gr.mul(edge, gr.sub(1.0, verdigris), True)
    height = 0.0
    if "text" in p:
        key, ink, relief = p["text"]
        letters = gr.text(key)
        polish = gr.most(polish, gr.mul(letters, gr.sub(1.0, gr.mul(verdigris, 0.8))))
        height = gr.mul(letters, relief)
    color = gr.mix(gr.mul(polish, 0.55), color, (0.26, 0.18, 0.08))
    grime = gr.mul(gr.add(gr.mul(cavity, 1.2), gr.ramp(gr.noise(4.0 / s, 4.0, 0.6, offset=(5.0, 1.0, 2.0)), 0.45, 0.7)), 0.6, True)
    color = gr.mix(grime, color, (0.03, 0.025, 0.018))
    rough = gr.lerp(verdigris, gr.lerp(polish, 0.62, 0.42), 0.88)
    metal = gr.lerp(gr.most(verdigris, grime), 0.85, 0.1)
    gr.finish(color, rough, metal, height, p.get("bump", 0.5), 0.0006 * s, 0.002 * s)


builders = {"paint": look_paint, "metal": look_metal, "stone": look_stone, "wood": look_wood, "fabric": look_fabric, "rubber": look_rubber, "plastic": look_plastic, "glass": look_glass, "organic": look_organic, "bronze": look_bronze}


def standard_looks():
    register("steel", "metal", kind="steel", rust=0.45)
    register("iron", "metal", kind="iron", rust=0.6)
    register("rust", "metal", kind="rust", rust=1.0)
    register("zinc", "metal", kind="galvanised", rust=0.3)
    register("chrome", "metal", kind="chrome", rust=0.4)
    register("weld", "metal", kind="weld", rust=0.5, dirt=0.3)
    register("mesh", "metal", kind="steel", rust=0.7, dirt=0.3)
    register("chain", "metal", kind="iron", rust=0.85, dirt=0.3)
    register("spike", "metal", kind="steel", rust=0.5)
    register("rubber", "rubber", perished=0.5)
    register("glass", "glass", cracked=0.0)
    register("glass_cracked", "glass", cracked=0.8, impacts=2.4, reach=0.42)
    register("moss", "organic", kind="moss")
    register("leaves", "organic", kind="leaves")
    register("dirt", "organic", kind="dirt")
    register("water", "organic", kind="water")
    register("rope", "fabric", kind="canvas", tint=(0.32, 0.25, 0.14), weave=14.0, stains=0.6)
    register("strap", "fabric", kind="canvas", tint=(0.12, 0.12, 0.08), weave=14.0, stains=0.5)
    register("canvas_olive", "fabric", kind="canvas", tint=(0.11, 0.11, 0.065), stains=0.6, dirt=0.5)
    register("hessian", "fabric", kind="hessian", dirt=0.6)


def select_only(objects, active=None):
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj in objects)
    bpy.context.view_layer.objects.active = active if active is not None else (objects[0] if objects else None)


def uv_bounds(objects):
    low = [1e9, 1e9]
    high = [-1e9, -1e9]
    for obj in objects:
        layer = obj.data.uv_layers["UVMap"]
        data = numpy.empty(len(layer.data) * 2, dtype=numpy.float32)
        layer.data.foreach_get("uv", data)
        if data.size:
            data = data.reshape(-1, 2)
            low = [min(low[0], float(data[:, 0].min())), min(low[1], float(data[:, 1].min()))]
            high = [max(high[0], float(data[:, 0].max())), max(high[1], float(data[:, 1].max()))]
    return low, high


def fit_uvs(objects, region):
    low, high = uv_bounds(objects)
    x0, y0, x1, y1 = region
    for obj in objects:
        layer = obj.data.uv_layers["UVMap"]
        data = numpy.empty(len(layer.data) * 2, dtype=numpy.float32)
        layer.data.foreach_get("uv", data)
        data = data.reshape(-1, 2)
        data[:, 0] = x0 + (data[:, 0] - low[0]) / max(high[0] - low[0], 1e-6) * (x1 - x0)
        data[:, 1] = y0 + (data[:, 1] - low[1]) / max(high[1] - low[1], 1e-6) * (y1 - y0)
        layer.data.foreach_set("uv", data.ravel())


def boost_islands(obj, factor):
    attribute = obj.data.attributes.get("boost")
    if attribute is None or factor == 1.0:
        return
    flags = [0] * len(obj.data.polygons)
    attribute.data.foreach_get("value", flags)
    if not any(flags):
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    uv = bm.loops.layers.uv["UVMap"]
    parent = list(range(len(bm.faces)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        first, second = edge.link_faces
        loops_a = {loop.vert.index: loop[uv].uv.copy() for loop in first.loops if loop.vert in edge.verts}
        loops_b = {loop.vert.index: loop[uv].uv.copy() for loop in second.loops if loop.vert in edge.verts}
        if all((loops_a[key] - loops_b[key]).length < 1e-5 for key in loops_a):
            a = find(first.index)
            b = find(second.index)
            if a != b:
                parent[a] = b
    islands = {}
    for face in bm.faces:
        islands.setdefault(find(face.index), []).append(face)
    for members in islands.values():
        if not any(flags[face.index] for face in members):
            continue
        points = [loop[uv].uv for face in members for loop in face.loops]
        center = sum(points, Vector((0.0, 0.0))) / len(points)
        for face in members:
            for loop in face.loops:
                loop[uv].uv = center + (loop[uv].uv - center) * factor
    bm.to_mesh(obj.data)
    bm.free()


def unwrap(objects, region, margin=0.004, angle=52.0, boost=2.6):
    for obj in objects:
        obj.data.uv_layers.active = obj.data.uv_layers["UVMap"]
    select_only(objects)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in objects:
        boost_islands(obj, boost)
    fit_uvs(objects, region)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(udim_source='ORIGINAL_AABB', rotate=True, rotate_method='ANY', scale=True, merge_overlap=False, margin_method='FRACTION', margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    low, high = uv_bounds(objects)
    x0, y0, x1, y1 = region
    if low[0] < x0 - 1e-3 or low[1] < y0 - 1e-3 or high[0] > x1 + 1e-3 or high[1] > y1 + 1e-3:
        span = max((high[0] - low[0]) / (x1 - x0), (high[1] - low[1]) / (y1 - y0))
        log("UV REFIT", [round(value, 3) for value in low + high], region)
        fit_uvs(objects, (x0, y0, x0 + (high[0] - low[0]) / span, y0 + (high[1] - low[1]) / span))


def bake_scene(samples):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    turntable.accelerate(scene)
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("bake")
    scene.world.light_settings.distance = settings["ao_distance"]
    scene.render.bake.margin = settings["margin"]
    scene.render.bake.margin_type = 'EXTEND'
    scene.render.bake.use_clear = False
    return scene


def target_image(name, size):
    image = bpy.data.images.new(name, size, size, alpha=True, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    image.pixels.foreach_set(numpy.zeros(size * size * 4, dtype=numpy.float32))
    return image


def aim(materials, image):
    for slot in materials:
        tree = slot.node_tree
        holder = tree.nodes.get("bake_target")
        if holder is None:
            holder = tree.nodes.new('ShaderNodeTexImage')
            holder.name = "bake_target"
        holder.image = image
        tree.nodes.active = holder


def emission_swap(materials, input_name):
    saved = []
    for slot in materials:
        tree = slot.node_tree
        shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
        output = next(node for node in tree.nodes if node.type == 'OUTPUT_MATERIAL')
        emission = tree.nodes.new('ShaderNodeEmission')
        emission.name = "bake_emit"
        socket = shader.inputs[input_name]
        if socket.links:
            tree.links.new(socket.links[0].from_socket, emission.inputs['Color'])
        else:
            value = socket.default_value
            emission.inputs['Color'].default_value = tuple(value) if hasattr(value, '__len__') else (value, value, value, 1.0)
        saved.append((slot, output.inputs['Surface'].links[0].from_socket))
        tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return saved


def emission_restore(saved):
    for slot, socket in saved:
        tree = slot.node_tree
        output = next(node for node in tree.nodes if node.type == 'OUTPUT_MATERIAL')
        tree.links.new(socket, output.inputs['Surface'])
        tree.nodes.remove(tree.nodes["bake_emit"])


def materials_of(objects):
    result = []
    for obj in objects:
        for slot in obj.data.materials:
            if slot is not None and slot not in result:
                result.append(slot)
    return result


def pixels(image):
    data = numpy.empty(image.size[0] * image.size[1] * 4, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    return data.reshape(image.size[1], image.size[0], 4)


passes = [("color", 'EMIT', 'Base Color'), ("metal", 'EMIT', 'Metallic'), ("rough", 'ROUGHNESS', None), ("normal", 'NORMAL', None), ("ao", 'AO', None)]


def run_bake(kind, selected, active, to_active=False, extrusion=0.06, reach=0.4):
    select_only(selected, active)
    started = time.time()
    if to_active:
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=extrusion, max_ray_distance=reach, margin=settings["margin"], use_clear=False, normal_space='TANGENT', uv_layer="UVMap")
    else:
        bpy.ops.object.bake(type=kind, margin=settings["margin"], use_clear=False, normal_space='TANGENT', uv_layer="UVMap")
    return time.time() - started


def bake_maps(objects, size, sources=None, far=None, extrusion=0.06, reach=0.4, hide=()):
    scene = bake_scene(settings["samples"])
    hidden = []
    for obj in bpy.context.view_layer.objects:
        if obj in hide and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj)
    result = {}
    targets = objects if far is None else [far]
    source_list = objects if far is None else (sources if sources is not None else objects)
    target_materials = materials_of(targets)
    source_materials = materials_of(source_list)
    for key, kind, socket in passes:
        image = target_image("bake_" + key, size)
        aim(target_materials, image)
        scene.cycles.samples = settings["ao_samples"] if key == "ao" else settings["samples"]
        saved = emission_swap(source_materials, socket) if socket else []
        if far is None:
            spent = run_bake(kind, objects, objects[0])
        else:
            spent = run_bake(kind, list(source_list) + [far], far, True, extrusion, reach)
        emission_restore(saved)
        result[key] = pixels(image).copy()
        bpy.data.images.remove(image)
        log("BAKED", key, "far" if far is not None else ",".join(obj.name for obj in objects), round(spent, 1), "s")
    for obj in hidden:
        obj.hide_render = False
    return result


def push_pull(data, coverage):
    levels = [(data * coverage[:, :, None], coverage)]
    current_data, current_cover = levels[0]
    while current_data.shape[0] > 4:
        h, w = current_data.shape[:2]
        summed = current_data.reshape(h // 2, 2, w // 2, 2, -1).sum(axis=(1, 3))
        weight = current_cover.reshape(h // 2, 2, w // 2, 2).sum(axis=(1, 3))
        current_data = summed
        current_cover = weight
        levels.append((current_data, current_cover))
    filled = None
    for data_level, cover_level in reversed(levels):
        average = data_level / numpy.maximum(cover_level, 1e-6)[:, :, None]
        if filled is None:
            filled = numpy.where(cover_level[:, :, None] > 0.0, average, average.mean(axis=(0, 1)))
        else:
            up = numpy.repeat(numpy.repeat(filled, 2, axis=0), 2, axis=1)
            filled = numpy.where(cover_level[:, :, None] > 0.0, average, up)
    return filled


def save_png(path, data, colorspace):
    height, width = data.shape[:2]
    image = bpy.data.images.new(os.path.splitext(os.path.basename(path))[0], width, height, alpha=False)
    rgba_data = numpy.ones((height, width, 4), dtype=numpy.float32)
    rgba_data[:, :, :3] = numpy.clip(data[:, :, :3], 0.0, 1.0)
    image.pixels.foreach_set(rgba_data.ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    image.colorspace_settings.name = colorspace
    return image


def to_srgb(linear):
    linear = numpy.clip(linear, 0.0, 1.0)
    return numpy.where(linear <= 0.0031308, linear * 12.92, 1.055 * numpy.power(numpy.maximum(linear, 0.0031308), 1.0 / 2.4) - 0.055)


def shrink(data, factor):
    if factor <= 1:
        return data
    h, w = data.shape[:2]
    return data.reshape(h // factor, factor, w // factor, factor, -1).mean(axis=(1, 3))


class texture_set:
    def __init__(self, key, folder, size=None, band=None):
        self.key = key
        self.folder = folder
        self.size = size if size is not None else settings["bake_size"]
        self.band = band if band is not None else settings["band"]
        self.maps = None
        self.images = None
        self.material = None

    def region_near(self, with_far):
        return (0.0, 0.0, 1.0, 1.0 - self.band) if with_far else (0.0, 0.0, 1.0, 1.0)

    def region_far(self):
        return (0.0, 1.0 - self.band + 0.012, 1.0, 1.0)

    def split_row(self):
        return int((1.0 - self.band + 0.006) * self.size)

    def bake_near(self, objects, with_far=False, hide=()):
        unwrap(objects, self.region_near(with_far))
        self.maps = bake_maps(objects, self.size, hide=hide)
        self.write()
        self.apply(objects)

    def bake_far(self, far_objects, sources, extrusion=0.06, reach=0.4):
        unwrap(far_objects, self.region_far(), 0.01)
        result = None
        for far in far_objects:
            holder = bpy.data.materials.new(self.key + "_far_target")
            holder.use_nodes = True
            far.data.materials.clear()
            far.data.materials.append(holder)
            maps = bake_maps([far], self.size, sources, far, extrusion, reach)
            if result is None:
                result = maps
            else:
                for key in result:
                    covered = maps[key][:, :, 3:4] > 0.5
                    result[key] = numpy.where(covered, maps[key], result[key])
        row = self.split_row()
        for key in self.maps:
            self.maps[key][row:] = result[key][row:]
        self.write()
        for far in far_objects:
            far.data.materials.clear()
            far.data.materials.append(self.material)
            tint = far.data.color_attributes.get("tint")
            if tint is not None:
                far.data.color_attributes.remove(tint)

    def write(self):
        factor = max(self.size // settings["output_size"], 1)
        directory = os.path.join(models_root, self.folder)
        os.makedirs(directory, exist_ok=True)
        coverage = (self.maps["color"][:, :, 3] > 0.5).astype(numpy.float32)
        filled = {key: push_pull(self.maps[key][:, :, :3], coverage) for key in self.maps}
        color = shrink(filled["color"], factor)
        orm = numpy.stack([numpy.clip(shrink(filled["ao"], factor)[:, :, 0] * 0.7 + 0.3, 0.0, 1.0), numpy.clip(shrink(filled["rough"], factor)[:, :, 0], 0.04, 1.0), numpy.clip(shrink(filled["metal"], factor)[:, :, 0], 0.0, 1.0)], -1)
        normal = shrink(filled["normal"], factor) * 2.0 - 1.0
        normal /= numpy.maximum(numpy.linalg.norm(normal, axis=-1, keepdims=True), 1e-6)
        normal = normal * 0.5 + 0.5
        names = [self.key + "_albedo", self.key + "_orm", self.key + "_normal"]
        paths = [os.path.join(directory, name + ".png") for name in names]
        if self.images is None:
            self.images = [save_png(paths[0], to_srgb(color), 'sRGB'), save_png(paths[1], orm, 'Non-Color'), save_png(paths[2], normal, 'Non-Color')]
            self.material = baked_material(self.key, self.images)
        else:
            for image, data, path, colorspace in zip(self.images, (to_srgb(color), orm, normal), paths, ('sRGB', 'Non-Color', 'Non-Color')):
                rgba_data = numpy.ones((data.shape[0], data.shape[1], 4), dtype=numpy.float32)
                rgba_data[:, :, :3] = numpy.clip(data[:, :, :3], 0.0, 1.0)
                image.pixels.foreach_set(rgba_data.ravel())
                image.filepath_raw = path
                image.save()
                image.colorspace_settings.name = colorspace
        log("WROTE", self.key, [os.path.basename(path) for path in paths])

    def apply(self, objects):
        for obj in objects:
            obj.data.materials.clear()
            obj.data.materials.append(self.material)
            obj.data.polygons.foreach_set("material_index", [0] * len(obj.data.polygons))
            text_layer = obj.data.uv_layers.get("TextMap")
            if text_layer is not None:
                obj.data.uv_layers.remove(text_layer)
            tint = obj.data.color_attributes.get("tint")
            if tint is not None:
                obj.data.color_attributes.remove(tint)
            boost = obj.data.attributes.get("boost")
            if boost is not None:
                obj.data.attributes.remove(boost)


def baked_material(name, images):
    albedo, orm, normal = images
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    tree = result.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = albedo
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    packed = tree.nodes.new('ShaderNodeTexImage')
    packed.image = orm
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(packed.outputs['Color'], split.inputs['Color'])
    tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
    tree.links.new(split.outputs['Blue'], shader.inputs['Metallic'])
    settings_node = tree.nodes.new('ShaderNodeGroup')
    settings_node.node_tree = g.gltf_group()
    tree.links.new(split.outputs['Red'], settings_node.inputs['Occlusion'])
    bumps = tree.nodes.new('ShaderNodeTexImage')
    bumps.image = normal
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(bumps.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    return result


def join(objects, name):
    objects = [obj for obj in objects if obj is not None]
    select_only(objects, objects[0])
    bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    result.data.name = name
    return result


def duplicate(obj, name, matrix=None, location=None):
    mesh = obj.data.copy()
    mesh.name = name
    if matrix is not None:
        mesh.transform(matrix)
    copy = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(copy)
    copy.location = location if location is not None else obj.location.copy()
    return copy


def bake_into(target, obj):
    mesh = obj.data
    mesh.transform(Matrix.Translation(obj.location - target.location))
    obj.location = target.location.copy()
    return join([target, obj], target.name)


def export(folder, objects):
    directory = os.path.join(models_root, folder)
    os.makedirs(directory, exist_ok=True)
    for entry in os.listdir(directory):
        if entry.endswith((".gltf", ".bin")):
            os.remove(os.path.join(directory, entry))
    path = os.path.join(directory, folder + ".gltf")
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj in objects)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_keep_originals=True, export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_yup=True, export_apply=True, export_skins=False, export_animations=False, export_morph=False, export_cameras=False, export_lights=False, export_extras=False)
    from urllib.parse import unquote
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    for image in document.get("images", []):
        if "uri" in image:
            uri = unquote(image["uri"])
            absolute = uri if os.path.isabs(uri) else os.path.normpath(os.path.join(directory, uri))
            image["uri"] = os.path.relpath(absolute, directory).replace("\\", "/")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    return path, document


def audit(path, document, budget=None):
    from urllib.parse import unquote
    directory = os.path.dirname(path)
    names = [node.get("name", "") for node in document.get("nodes", [])]
    problems = []
    if len(set(names)) != len(names):
        problems.append("duplicate node names")
    for name in names:
        if not name.isascii() or len(name) > 41 or "." in name:
            problems.append("bad name " + name)
    triangles = 0
    markers = []
    parts = {}
    accessors = document.get("accessors", [])
    low = [1e9, 1e9, 1e9]
    high = [-1e9, -1e9, -1e9]
    for node in document.get("nodes", []):
        if "mesh" not in node:
            continue
        name = node.get("name", "")
        mesh = document["meshes"][node["mesh"]]
        shift = node.get("translation", [0.0, 0.0, 0.0])
        count = 0
        for primitive in mesh["primitives"]:
            if "TEXCOORD_0" not in primitive["attributes"]:
                problems.append("no uv " + name)
            count += accessors[primitive["indices"]]["count"] // 3
            position = accessors[primitive["attributes"]["POSITION"]]
            if not is_marker(name):
                for axis in range(3):
                    low[axis] = min(low[axis], position["min"][axis] + shift[axis])
                    high[axis] = max(high[axis], position["max"][axis] + shift[axis])
        if is_marker(name):
            markers.append(name)
        else:
            triangles += count
            parts[name] = (count, [round(value, 4) for value in (shift[0], -shift[2], shift[1])])
        if "scale" in node or "rotation" in node:
            problems.append("transform on " + name)
    for image in document.get("images", []):
        uri = unquote(image.get("uri", ""))
        if not os.path.exists(os.path.normpath(os.path.join(directory, uri))):
            problems.append("missing image " + uri)
    if budget is not None and triangles > budget:
        problems.append("over budget %d > %d" % (triangles, budget))
    blender_low = (round(low[0], 3), round(-high[2], 3), round(low[1], 3))
    blender_high = (round(high[0], 3), round(-low[2], 3), round(high[1], 3))
    log("AUDIT", os.path.basename(path), "tris", triangles, "markers", len(markers), "materials", len(document.get("materials", [])), "bounds", blender_low, blender_high, "problems", problems if problems else "none")
    for name, (count, origin) in parts.items():
        log("  PART", name, count, "origin", origin)
    return {"triangles": triangles, "markers": markers, "parts": parts, "problems": problems, "low": blender_low, "high": blender_high}


def triangles_of(objects):
    total = 0
    for obj in objects:
        if obj.type == 'MESH' and not is_marker(obj.name):
            total += sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons)
    return total


def write_png(path, data):
    array = numpy.clip(numpy.rint(numpy.asarray(data, dtype=numpy.float64) * 255.0), 0, 255).astype(numpy.uint8)[::-1]
    height, width = array.shape[:2]
    channels = 1 if array.ndim == 2 else array.shape[2]
    raw = numpy.empty((height, width * channels + 1), numpy.uint8)
    raw[:, 0] = 0
    raw[:, 1:] = array.reshape(height, width * channels)

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    kind = {1: 0, 3: 2, 4: 6}[channels]
    header = struct.pack(">IIBBBBB", width, height, 8, kind, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw.tobytes(), 6)) + chunk(b"IEND", b""))


def read_image(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    data = numpy.empty(width * height * 4, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(height, width, 4)[:, :, :3]


def contact_sheet(paths, out_path, columns=3, thumb=(800, 450)):
    images = [read_image(path) for path in paths if os.path.exists(path)]
    if not images:
        return
    rows = (len(images) + columns - 1) // columns
    sheet = numpy.full((rows * (thumb[1] + 6) + 6, columns * (thumb[0] + 6) + 6, 3), 0.05, dtype=numpy.float32)
    for index, image in enumerate(images):
        h, w = image.shape[:2]
        ys = (numpy.arange(thumb[1]) + 0.5) * h / thumb[1]
        xs = (numpy.arange(thumb[0]) + 0.5) * w / thumb[0]
        small = image[numpy.clip(ys.astype(int), 0, h - 1)][:, numpy.clip(xs.astype(int), 0, w - 1)]
        r = rows - 1 - index // columns
        c = index % columns
        sheet[6 + r * (thumb[1] + 6):6 + r * (thumb[1] + 6) + thumb[1], 6 + c * (thumb[0] + 6):6 + c * (thumb[0] + 6) + thumb[0]] = small
    write_png(out_path, sheet)


def render_settings(samples, resolution=(1600, 900), exposure=0.0):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 3
    turntable.accelerate(scene)
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = exposure
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False


def daylight(strength=0.9, sun=3.2, direction=(0.5, 0.62, -0.6), angle=12.0):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("daylight")
    world.use_nodes = True
    tree = world.node_tree
    background = tree.nodes["Background"]
    environment = tree.nodes.new('ShaderNodeTexEnvironment')
    environment.image = bpy.data.images.load(hdri_path, check_existing=True)
    tree.links.new(environment.outputs['Color'], background.inputs['Color'])
    background.inputs['Strength'].default_value = strength
    scene.world = world
    data = bpy.data.lights.new("preview_sun", 'SUN')
    data.energy = sun
    data.angle = math.radians(angle)
    data.color = (1.0, 0.96, 0.9)
    obj = bpy.data.objects.new("preview_sun", data)
    scene.collection.objects.link(obj)
    obj.rotation_euler = Vector(direction).normalized().to_track_quat('-Z', 'Y').to_euler()
    return obj


def ground_plane(z=0.0, extent=60.0, kind="asphalt"):
    mesh = bpy.data.meshes.new("preview_ground")
    mesh.from_pydata([(-extent, -extent, z), (extent, -extent, z), (extent, extent, z), (-extent, extent, z)], [], [(0, 1, 2, 3)])
    layer = mesh.uv_layers.new(name="UVMap")
    tile = 2.5
    layer.data.foreach_set("uv", [-extent / tile, -extent / tile, extent / tile, -extent / tile, extent / tile, extent / tile, -extent / tile, extent / tile])
    result = bpy.data.materials.new("preview_ground")
    result.use_nodes = True
    tree = result.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    folder = os.path.join(raw_textures, "asphalt_03" if kind == "asphalt" else "gravelly_sand")
    stem = os.path.basename(folder)
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = bpy.data.images.load(os.path.join(folder, stem + "_diff_2k.jpg"), check_existing=True)
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = 0.85
    mesh.materials.append(result)
    obj = bpy.data.objects.new("preview_ground", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def camera(position, target, lens=35.0, ortho=None, clip_start=0.02):
    data = bpy.data.cameras.new("preview_camera")
    data.lens = lens
    data.clip_start = clip_start
    data.clip_end = 600.0
    if ortho is not None:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    obj = bpy.data.objects.new("preview_camera", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = Vector(position)
    obj.rotation_euler = (Vector(target) - Vector(position)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = obj
    return obj


def fit_camera(cam, points, focus, margin=0.06):
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    focus = Vector(focus)
    for iteration in range(400):
        bpy.context.view_layer.update()
        coords = [world_to_camera_view(scene, cam, p) for p in points]
        if all(margin < c.x < 1.0 - margin and margin < c.y < 1.0 - margin and c.z > 0.0 for c in coords):
            break
        cam.location = focus + (cam.location - focus) * 1.025
    bpy.context.view_layer.update()


def shoot(path):
    scene = bpy.context.scene
    scene.render.filepath = path
    started = time.time()
    bpy.ops.render.render(write_still=True)
    log("RENDERED", os.path.basename(path), round(time.time() - started, 1), "s")


def import_model(folder):
    path = os.path.join(models_root, folder, folder + ".gltf")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [obj for obj in bpy.data.objects if obj not in before]


def world_bounds(objects):
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            low = Vector((min(low.x, p.x), min(low.y, p.y), min(low.z, p.z)))
            high = Vector((max(high.x, p.x), max(high.y, p.y), max(high.z, p.z)))
    return low, high


def overlay_material(color, strength=1.5, opacity=0.35):
    result = bpy.data.materials.new("overlay")
    result.use_nodes = True
    tree = result.node_tree
    output = next(node for node in tree.nodes if node.type == 'OUTPUT_MATERIAL')
    for node in list(tree.nodes):
        if node != output:
            tree.nodes.remove(node)
    emission = tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = rgba(color)
    emission.inputs['Strength'].default_value = strength
    clear = tree.nodes.new('ShaderNodeBsdfTransparent')
    mixer = tree.nodes.new('ShaderNodeMixShader')
    mixer.inputs['Fac'].default_value = opacity
    tree.links.new(clear.outputs['BSDF'], mixer.inputs[1])
    tree.links.new(emission.outputs['Emission'], mixer.inputs[2])
    tree.links.new(mixer.outputs['Shader'], output.inputs['Surface'])
    return result


def solid_object(name, bm, look):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(look)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def gizmo(position, size=0.25):
    created = []
    position = Vector(position)
    for axis, color in ((X, (1.0, 0.1, 0.1)), (Y, (0.1, 1.0, 0.1)), (Z, (0.2, 0.4, 1.0))):
        created.append(solid_object("gizmo", rod(position, position + axis * size, size * 0.045, 8), overlay_material(color, 4.0, 1.0)))
    created.append(solid_object("gizmo", g.shifted(g.sphere(size * 0.09, 12, 8), position.x, position.y, position.z), overlay_material((1.0, 1.0, 0.2), 4.0, 1.0)))
    return created


def view_shot(path, objects, direction, lens=40.0, focus=None, margin=0.06, points=None):
    low, high = world_bounds(objects)
    center = (low + high) * 0.5 if focus is None else Vector(focus)
    span = max((high - low).length, 0.3)
    corners = points if points is not None else [Vector((x, y, z)) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
    cam = camera(center + Vector(direction).normalized() * span * 0.5, center, lens)
    fit_camera(cam, corners, center, margin)
    shoot(path)
    bpy.data.objects.remove(cam)


def close_shot(path, position, target, lens=50.0):
    cam = camera(Vector(position), Vector(target), lens)
    shoot(path)
    bpy.data.objects.remove(cam)


def write_json(path, document):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)


def triple(vector):
    return [round(vector[0], 4), round(vector[1], 4), round(vector[2], 4)]
