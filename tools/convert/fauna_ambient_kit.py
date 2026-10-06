import bpy
import json
import math
import os
import numpy
from mathutils import bvhtree
import fauna_hoofed_build as build
import fauna_hoofed_check as check
import fauna_hoofed_field as fields
import fauna_hoofed_paint as paint
import fauna_hoofed_render as render

unit = fields.unit
smooth = fields.smoothstep
flip = numpy.array([-1.0, 1.0, 1.0])


class mesh:
    def __init__(self):
        self.points = []
        self.faces = []
        self.tags = []
        self.part = []
        self.coord = []
        self.cuts = []
        self.normal = []

    def vertex(self, point, part, coord=(0.0, 0.0), normal=None):
        self.points.append(numpy.asarray(point, dtype=numpy.float64))
        self.part.append(part)
        self.coord.append(tuple(float(v) for v in coord))
        self.normal.append(numpy.full(3, numpy.nan) if normal is None else unit(normal))
        return len(self.points) - 1

    def face(self, ids, tag):
        clean = []
        for index in ids:
            if not clean or clean[-1] != index:
                clean.append(int(index))
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        if len(clean) >= 3:
            self.faces.append(tuple(clean))
            self.tags.append(tag)

    def strip(self, first, second, tag, closed=False):
        count = len(first)
        for index in range(count if closed else count - 1):
            following = (index + 1) % count
            self.face((first[index], first[following], second[following], second[index]), tag)

    def fan(self, ring, center, tag, closed=True):
        count = len(ring)
        for index in range(count if closed else count - 1):
            self.face((ring[index], ring[(index + 1) % count], center), tag)

    def seam(self, chain):
        for index in range(len(chain) - 1):
            self.cuts.append((int(chain[index]), int(chain[index + 1])))

    def model(self):
        points = numpy.array(self.points)
        return {"points": points, "faces": list(self.faces), "tags": list(self.tags), "part": list(self.part), "coord": numpy.array(self.coord, dtype=numpy.float64), "cuts": list(self.cuts), "detail": numpy.zeros(len(points), dtype=bool), "normal": numpy.array(self.normal), "scale": 1.0}


def superellipse(angle, wide, up, down, n_up, n_down):
    c = math.cos(angle)
    s = math.sin(angle)
    n = n_up if c >= 0.0 else n_down
    reach = up if c >= 0.0 else down
    x = wide * math.copysign(abs(s) ** (2.0 / n), s)
    z = reach * math.copysign(abs(c) ** (2.0 / n), c)
    return x, z


def table(stations, count):
    stations = sorted(stations, key=lambda s: s[0])
    knots = numpy.array([s[0] for s in stations])
    values = numpy.array([s[1:] for s in stations])
    return fields.monotone_table(knots, values, count), numpy.linspace(knots[0], knots[-1], count)


def body(m, stations, rings, around, part, tag, tip_front=None, tip_back=None, tagger=None, spacing=None):
    profile, along = table(stations, 256)
    picks = numpy.linspace(0.0, 1.0, rings) if spacing is None else numpy.asarray(spacing)
    ids = []
    for t in picks:
        index = min(int(round(t * 255)), 255)
        y = along[index]
        zc, wide, up, down, n_up, n_down = profile[index]
        ring = []
        arc = 0.0
        previous = None
        for step in range(around):
            angle = 2.0 * math.pi * step / around
            x, z = superellipse(angle, wide, up, down, n_up, n_down)
            p = numpy.array([x, y, zc + z])
            if previous is not None:
                arc += float(numpy.linalg.norm(p - previous))
            previous = p
            ring.append(m.vertex(p, part, (y, arc)))
        ids.append(ring)
    half = around // 2
    for ring in ids:
        top = m.points[ring[0]]
        for step, vid in enumerate(ring):
            p = m.points[vid]
            m.coord[vid] = (float(p[1]), float(numpy.linalg.norm(p[[0, 2]] - top[[0, 2]])) if step <= half else -float(numpy.linalg.norm(p[[0, 2]] - top[[0, 2]])))
    for level in range(len(ids) - 1):
        name = tagger(along[min(int(round(picks[level] * 255)), 255)]) if tagger else tag
        m.strip(ids[level], ids[level + 1], name, closed=True)
    m.seam([ring[half] for ring in ids])
    if tip_back is not None:
        center = m.vertex(tip_back, part, (float(tip_back[1]), 0.0))
        m.fan(ids[0][::-1], center, tagger(along[0]) if tagger else tag)
        m.cuts.append((ids[0][half], center))
    if tip_front is not None:
        center = m.vertex(tip_front, part, (float(tip_front[1]), 0.0))
        m.fan(ids[-1], center, tagger(along[-1]) if tagger else tag)
        m.cuts.append((ids[-1][half], center))
    return ids


def plate(m, base, tips, normal, thickness, rows, part, tags, coord=None, bulge=None):
    base = numpy.asarray(base, dtype=numpy.float64)
    tips = numpy.asarray(tips, dtype=numpy.float64)
    columns = len(tips)
    normal = unit(normal)
    upper = []
    lower = []
    for j in range(columns):
        t = j / (columns - 1.0)
        root = base[0] + (base[1] - base[0]) * t if len(base) == 2 else base[j]
        up_col = []
        low_col = []
        for i in range(rows + 1):
            s = i / float(rows)
            p = root + (tips[j] - root) * s
            if bulge is not None:
                p = p + bulge(s, t)
            half = 0.5 * thickness * (1.0 - s) ** 0.7 + 0.0004
            uv = (s, t) if coord is None else coord(s, t)
            if i == rows:
                shared = m.vertex(p, part, uv)
                up_col.append(shared)
                low_col.append(shared)
            else:
                up_col.append(m.vertex(p + normal * half, part, uv))
                low_col.append(m.vertex(p - normal * half, part, uv))
        upper.append(up_col)
        lower.append(low_col)
    for j in range(columns - 1):
        for i in range(rows):
            m.face((upper[j][i], upper[j + 1][i], upper[j + 1][i + 1], upper[j][i + 1]), tags[0])
            m.face((lower[j][i + 1], lower[j + 1][i + 1], lower[j + 1][i], lower[j][i]), tags[1])
    for i in range(rows):
        m.face((upper[0][i + 1], lower[0][i + 1], lower[0][i], upper[0][i]), tags[1])
        m.face((upper[-1][i], lower[-1][i], lower[-1][i + 1], upper[-1][i + 1]), tags[1])
    m.seam([column[0] for column in upper])
    m.seam([upper[0][i] for i in range(rows + 1)])
    m.seam([upper[-1][i] for i in range(rows + 1)])
    return upper, lower


def eyeball(m, center, axis, radius, part="eyeball", tag="eyeball", segments=8):
    axis = unit(axis)
    side = unit(numpy.cross(axis, numpy.array([0.0, 0.0, 1.0])) if abs(axis[2]) < 0.9 else numpy.cross(axis, numpy.array([0.0, 1.0, 0.0])))
    up = numpy.cross(side, axis)
    tip = m.vertex(center + axis * radius, part, (0.0, 0.0), axis)
    rings = []
    for level, angle in enumerate((30.0, 62.0, 95.0)):
        a = math.radians(angle)
        ring = []
        for index in range(segments):
            psi = 2.0 * math.pi * index / segments
            direction = math.cos(a) * axis + math.sin(a) * (math.cos(psi) * side + math.sin(psi) * up)
            ring.append(m.vertex(center + radius * direction, part, (angle / 95.0, index / segments), direction))
        rings.append(ring)
    m.fan(rings[0], tip, tag)
    for level in range(len(rings) - 1):
        m.strip(rings[level], rings[level + 1], tag, closed=True)
    return rings


def mirror(m, start):
    count = len(m.points)
    faces = len(m.faces)
    mapping = {}
    for index in range(start, count):
        p = m.points[index]
        mapping[index] = m.vertex(p * flip, m.part[index], m.coord[index], None if numpy.isnan(m.normal[index][0]) else m.normal[index] * flip)
    for index in range(faces):
        face = m.faces[index]
        if all(v >= start for v in face):
            m.faces.append(tuple(mapping[v] for v in reversed(face)))
            m.tags.append(m.tags[index])
    for a, c in list(m.cuts):
        if a >= start and c >= start:
            m.cuts.append((mapping[a], mapping[c]))


def occlusion(model, rays=64, reach=0.12, strength=0.9):
    points = model["points"]
    triangles, loops, owner = paint.triangulate(model)
    normals = paint.model_normals(model, triangles)
    tree = bvhtree.BVHTree.FromPolygons(points.tolist(), [list(face) for face in model["faces"]])
    golden = math.pi * (3.0 - math.sqrt(5.0))
    samples = []
    for index in range(rays):
        z = 1.0 - (index + 0.5) / rays
        r = math.sqrt(max(1.0 - z * z, 0.0))
        samples.append((math.cos(golden * index) * r, math.sin(golden * index) * r, z))
    samples = numpy.array(samples)
    result = numpy.ones(len(points))
    for vertex in range(len(points)):
        n = normals[vertex]
        a = unit(numpy.cross(n, numpy.array([0.0, 0.0, 1.0])) if abs(n[2]) < 0.9 else numpy.cross(n, numpy.array([1.0, 0.0, 0.0])))
        b = numpy.cross(n, a)
        directions = samples[:, 0:1] * a[None, :] + samples[:, 1:2] * b[None, :] + samples[:, 2:3] * n[None, :]
        origin = points[vertex] + n * 0.0015
        blocked = 0.0
        for d in directions:
            hit = tree.ray_cast(origin.tolist(), d.tolist(), reach)
            if hit[0] is not None:
                blocked += 1.0 - hit[3] / reach
        result[vertex] = 1.0 - strength * blocked / rays
    return numpy.clip(result, 0.0, 1.0)


def tiles(u, v, size, aspect=0.8, reach=0.78, seed=0, wobble=0.18):
    across = size * aspect
    rows = numpy.floor(v / across).astype(numpy.int64)
    best = numpy.full(len(u), numpy.inf)
    du = numpy.zeros(len(u))
    dv = numpy.zeros(len(u))
    distance = numpy.ones(len(u))
    cell = numpy.zeros(len(u))
    for dr in (-1, 0, 1):
        r = rows + dr
        shift = (r % 2) * 0.5
        columns = numpy.floor(u / size - shift).astype(numpy.int64)
        for dc in (-1, 0, 1):
            c = columns + dc
            jitter_u = (paint.hashed(c, r, numpy.zeros_like(c), seed) - 0.5) * wobble
            jitter_v = (paint.hashed(c, r, numpy.ones_like(c), seed) - 0.5) * wobble
            cu = (c + shift + 0.5 + jitter_u) * size
            cv = (r + 0.5 + jitter_v) * across
            pu = (u - cu) / size
            pv = (v - cv) / across
            d = numpy.sqrt(pu * pu + pv * pv)
            take = (d < reach) & (cu < best)
            best = numpy.where(take, cu, best)
            du = numpy.where(take, pu, du)
            dv = numpy.where(take, pv, dv)
            distance = numpy.where(take, d / reach, distance)
            cell = numpy.where(take, paint.hashed(c, r, numpy.full_like(c, 2), seed), cell)
    return du, dv, distance, cell


def canvas(model, size):
    return paint.canvas(model, {"field": None, "cage": {"skin": ()}}, size)


def write_textures(c, color, rough, height, relief, occlusion, folder, name):
    slope = c.relief(height, 1.0) * relief[:, None]
    albedo, normal_path, orm = [os.path.join(folder, name + suffix) for suffix in ("_albedo.png", "_normal.png", "_orm.png")]
    paint.write(c, numpy.clip(color, 0.0, 1.0), albedo)
    paint.write(c, c.encode_normal(c.normal, slope), normal_path, fill=(0.5, 0.5, 1.0))
    paint.write(c, numpy.column_stack([occlusion, numpy.clip(rough, 0.04, 1.0), numpy.zeros(len(occlusion))]), orm, fill=(1.0, 0.8, 0.0))
    return albedo, normal_path, orm


def mesh_object(model, name):
    obj, triangles, owner = build.mesh_from_model(model, name)
    return obj


def export(model, name, folder, textures):
    render.reset()
    os.makedirs(folder, exist_ok=True)
    obj = mesh_object(model, name)
    obj.data.materials.append(build.material(name, *textures))
    for other in bpy.context.scene.objects:
        other.select_set(other is obj)
    bpy.context.view_layer.objects.active = obj
    path = os.path.join(folder, name + ".gltf")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_keep_originals=True, export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_yup=True, export_apply=True, export_skins=False, export_animations=False, export_morph=False, export_cameras=False, export_lights=False, export_extras=False)
    build.patch_material(path)
    return path


def inspect(path, budget, size):
    document, buffers = check.load(path)
    name = os.path.splitext(os.path.basename(path))[0]
    errors = []
    report = {"name": name}
    if os.path.basename(os.path.dirname(path)) != name:
        errors.append("file name differs from the folder name")
    meshes = [node for node in document["nodes"] if "mesh" in node]
    if len(meshes) != 1 or len(document.get("meshes", [])) != 1:
        errors.append("expected exactly one mesh")
    if len(document.get("materials", [])) != 1:
        errors.append("expected one material")
    if document.get("extensionsUsed"):
        errors.append("extensions in use: %s" % document["extensionsUsed"])
    triangles = 0
    low = numpy.full(3, numpy.inf)
    high = numpy.full(3, -numpy.inf)
    for node in meshes:
        t, r, s = check.node_trs(node)
        if numpy.abs(t).max() > 1e-6 or numpy.abs(r - numpy.array([0.0, 0.0, 0.0, 1.0])).max() > 1e-6 or numpy.abs(s - 1.0).max() > 1e-6:
            errors.append("mesh node is not at identity")
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            attributes = primitive["attributes"]
            for key in ("POSITION", "NORMAL", "TEXCOORD_0"):
                if key not in attributes:
                    errors.append("primitive lacks " + key)
            indices = check.accessor(document, buffers, primitive["indices"])
            triangles += len(indices) // 3
            positions = check.accessor(document, buffers, attributes["POSITION"])
            low = numpy.minimum(low, positions.min(axis=0))
            high = numpy.maximum(high, positions.max(axis=0))
            uv = check.accessor(document, buffers, attributes["TEXCOORD_0"])
            if uv.min() < -1e-4 or uv.max() > 1.0001:
                errors.append("uv outside the unit square")
            normals = check.accessor(document, buffers, attributes["NORMAL"])
            if numpy.abs(numpy.linalg.norm(normals, axis=1) - 1.0).max() > 1e-2:
                errors.append("normals are not unit length")
    engine_low = numpy.array([low[0], low[1], -high[2]])
    engine_high = numpy.array([high[0], high[1], -low[2]])
    report["triangles"] = triangles
    report["engine_bounds"] = [engine_low.round(4).tolist(), engine_high.round(4).tolist()]
    if triangles < budget[0] or triangles > budget[1]:
        errors.append("%d triangles outside the budget %d-%d" % (triangles, budget[0], budget[1]))
    material = document["materials"][0]
    pbr = material.get("pbrMetallicRoughness", {})
    slots = {"base": pbr.get("baseColorTexture"), "surface": pbr.get("metallicRoughnessTexture"), "normal": material.get("normalTexture"), "occlusion": material.get("occlusionTexture")}
    files = {}
    for label, slot in slots.items():
        if slot is None:
            errors.append("material lacks the %s texture" % label)
            continue
        files[label] = document["images"][document["textures"][slot["index"]]["source"]]["uri"]
    report["images"] = files
    for label, uri in files.items():
        file = os.path.join(os.path.dirname(path), uri)
        if not os.path.isfile(file):
            errors.append("missing image " + uri)
            continue
        pixels, color = check.png_pixels(file)
        if pixels.shape[0] != size or pixels.shape[1] != size:
            errors.append("%s is %dx%d" % (uri, pixels.shape[1], pixels.shape[0]))
        if label == "surface" and int(pixels[:, :, 2].max()) != 0:
            errors.append("metallic channel is not zero")
    if pbr.get("metallicFactor", 1.0) != 0.0 or pbr.get("roughnessFactor", 1.0) != 1.0:
        errors.append("material factors are not metallic 0, roughness 1")
    if material.get("alphaMode", "OPAQUE") != "OPAQUE":
        errors.append("material is not opaque")
    report["errors"] = errors
    return report
