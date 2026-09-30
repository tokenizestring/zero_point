import bpy
import bmesh
import math
import os
import numpy
from mathutils import Vector

import texels

avatars = {"sm005": ("Professions", "Military_Male_04"), "m002": ("Adults", "Male_Adult_01")}
rocketbox_head = numpy.array([0.0, -0.0081, 1.5871])
rocketbox_eyes = numpy.array([[0.032, -0.0941, 1.6861], [-0.032, -0.0941, 1.6861]])
rocketbox_eye_radius = 0.018
cache = {}


def avatar_folder(root, key):
    group, name = avatars[key]
    return os.path.join(root, "Avatars", group, name)


def texture_path(root, key, kind):
    return os.path.join(avatar_folder(root, key), "Textures", "%s_head_%s.tga" % (key, kind))


def load_avatar(root, key):
    if key in cache:
        return cache[key]
    group, name = avatars[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(avatar_folder(root, key), "Export", name + ".fbx"), use_anim=False)
    imported = [obj for obj in bpy.data.objects if obj not in before]
    source = next(obj for obj in imported if obj.type == 'MESH')
    world = numpy.array(source.matrix_world)
    mesh = source.data
    count = len(mesh.vertices)
    points = numpy.empty(count * 3, dtype=numpy.float64)
    mesh.vertices.foreach_get("co", points)
    points = points.reshape(-1, 3) @ world[:3, :3].T + world[:3, 3]
    sizes = numpy.empty(len(mesh.polygons), dtype=numpy.int32)
    mesh.polygons.foreach_get("loop_total", sizes)
    materials = numpy.empty(len(mesh.polygons), dtype=numpy.int32)
    mesh.polygons.foreach_get("material_index", materials)
    loops = numpy.empty(len(mesh.loops), dtype=numpy.int32)
    mesh.loops.foreach_get("vertex_index", loops)
    uv = numpy.empty(len(mesh.loops) * 2, dtype=numpy.float64)
    mesh.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    names = [group.name for group in source.vertex_groups]
    weights = numpy.zeros((count, len(names)), dtype=numpy.float64)
    for vertex in mesh.vertices:
        for entry in vertex.groups:
            weights[vertex.index, entry.group] = entry.weight
    head_material = next(index for index, slot in enumerate(source.material_slots) if slot.material and slot.material.name.split(".")[0].endswith("_head"))
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    starts = numpy.r_[0, numpy.cumsum(sizes)[:-1]]
    keys = numpy.round(points / 1e-5).astype(numpy.int64)
    unique, merged = numpy.unique(keys, axis=0, return_inverse=True)
    merged = merged.ravel()
    parent = numpy.arange(len(sizes))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner = {}
    for face in range(len(sizes)):
        for corner in loops[starts[face]:starts[face] + sizes[face]]:
            slot = merged[corner]
            if slot in owner:
                a = find(face)
                b = find(owner[slot])
                if a != b:
                    parent[a] = b
            else:
                owner[slot] = face
    component = numpy.array([find(face) for face in range(len(sizes))])
    head_faces = materials == head_material
    counts = numpy.bincount(component[head_faces], minlength=len(sizes))
    largest = counts.argmax()
    keep = head_faces & (component == largest)
    print("AVATAR head material components", sorted([int(c) for c in counts[counts > 0]], reverse=True)[:8])
    faces = numpy.flatnonzero(keep)
    corner_index = numpy.concatenate([numpy.arange(starts[face], starts[face] + sizes[face]) for face in faces])
    corner_vertex = merged[loops[corner_index]]
    used, compact = numpy.unique(corner_vertex, return_inverse=True)
    first = numpy.zeros(len(unique), dtype=numpy.int64)
    first[merged[::-1]] = numpy.arange(len(merged))[::-1]
    head_points = points[first[used]]
    head_weights = weights[first[used]]
    result = {"points": head_points, "sizes": sizes[faces], "corners": compact.ravel().astype(numpy.int64), "uv": uv[corner_index], "weights": head_weights, "names": names}
    cache[key] = result
    print("AVATAR", key, "head vertices", len(head_points), "faces", len(faces))
    return result


def select_only(obj):
    bpy.context.view_layer.update()
    for other in bpy.context.scene.objects:
        other.select_set(other == obj)
    bpy.context.view_layer.objects.active = obj


def corner_starts(sizes):
    return numpy.r_[0, numpy.cumsum(sizes)[:-1]]


def triangulate(sizes, corners, with_faces=False):
    starts = corner_starts(sizes)
    corner_triangles = []
    owners = []
    for size in numpy.unique(sizes):
        chosen = numpy.flatnonzero(sizes == size)
        for k in range(1, size - 1):
            ids = numpy.stack([starts[chosen], starts[chosen] + k, starts[chosen] + k + 1], axis=1)
            corner_triangles.append(ids)
            owners.append(chosen)
    corner_triangles = numpy.concatenate(corner_triangles)
    owners = numpy.concatenate(owners)
    order = numpy.argsort(owners, kind='stable')
    corner_triangles = corner_triangles[order]
    if with_faces:
        return corners[corner_triangles], corner_triangles, owners[order]
    return corners[corner_triangles], corner_triangles


def kernel(points, center, radii):
    q = (points - numpy.asarray(center)) / numpy.asarray(radii)
    t = numpy.clip(1.0 - numpy.sum(q * q, axis=1), 0.0, 1.0)
    return t * t


def mirrored_centers(center):
    center = numpy.asarray(center, dtype=numpy.float64)
    if abs(center[0]) < 1e-9:
        return [(center, 1.0)]
    return [(center, 1.0), (center * numpy.array([-1.0, 1.0, 1.0]), -1.0)]


def eye_guard(points, origin):
    guard = numpy.zeros(len(points))
    for eye in rocketbox_eyes:
        distance = numpy.linalg.norm(points - (eye - rocketbox_head + origin), axis=1)
        guard = numpy.maximum(guard, texels.smoothstep(0.03, 0.02, distance))
    return guard


def apply_morphs(points, normals, morphs, origin):
    moved = points.copy()
    guard = eye_guard(points, origin)
    for entry in morphs:
        kind = entry[0]
        if kind == "lid":
            for center, sign in mirrored_centers(numpy.asarray(entry[1]) + origin * numpy.array([0.0, 1.0, 1.0])):
                weight = kernel(points, center, entry[2])[:, None]
                moved += weight * numpy.asarray(entry[3]) * numpy.array([sign, 1.0, 1.0])
            continue
        free = 1.0 - guard
        if kind == "taper":
            z_top, z_full, amount, y_limit = entry[1:5]
            q = points - origin
            weight = texels.smoothstep(z_top, z_full, q[:, 2]) * texels.smoothstep(y_limit + 0.02, y_limit - 0.02, q[:, 1]) * free
            moved[:, 0] -= q[:, 0] * amount * weight
            continue
        if kind == "neck":
            z_chin, slope, top, full, factors, y_center = entry[1:7]
            q = points - origin
            below = q[:, 2] - (z_chin + (q[:, 1] + 0.11) * slope)
            weight = texels.smoothstep(top, full, below)
            moved[:, 0] -= q[:, 0] * (1.0 - factors[0]) * weight
            moved[:, 1] -= (q[:, 1] - y_center) * (1.0 - factors[1]) * weight
            continue
        if kind == "squash":
            z_pivot, z_fade, factor, y_limit = entry[1:5]
            q = points - origin
            front = texels.smoothstep(y_limit + 0.02, y_limit - 0.02, q[:, 1])
            base = numpy.clip(q[:, 2], z_fade, z_pivot) - z_pivot
            decay = texels.smoothstep(z_fade - 0.04, z_fade, q[:, 2])
            moved[:, 2] += base * (factor - 1.0) * decay * front * free
            continue
        for center, sign in mirrored_centers(numpy.asarray(entry[1]) + origin * numpy.array([0.0, 1.0, 1.0])):
            weight = kernel(points, center, entry[2])[:, None] * free[:, None]
            if kind == "move":
                delta = numpy.asarray(entry[3], dtype=numpy.float64) * numpy.array([sign, 1.0, 1.0])
                moved += weight * delta
            elif kind == "scale":
                pivot = numpy.asarray(entry[4], dtype=numpy.float64) + origin * numpy.array([0.0, 1.0, 1.0]) if len(entry) > 4 else center
                pivot = pivot * numpy.array([sign, 1.0, 1.0]) if len(entry) > 4 else pivot
                moved += weight * (points - pivot) * (numpy.asarray(entry[3]) - 1.0)
            elif kind == "inflate":
                moved += weight * normals * entry[3]
    return moved


def smooth_normals(points, sizes, corners):
    triangles, corner_triangles = triangulate(sizes, corners)
    a = points[triangles[:, 0]]
    b = points[triangles[:, 1]]
    c = points[triangles[:, 2]]
    face = numpy.cross(b - a, c - a)
    normals = numpy.zeros_like(points)
    for k in range(3):
        numpy.add.at(normals, triangles[:, k], face)
    return normals / numpy.maximum(numpy.linalg.norm(normals, axis=1), 1e-12)[:, None]


def skull_weight(points, spec):
    q = points - rocketbox_head
    lateral = numpy.abs(q[:, 0])
    back = texels.smoothstep(spec["back_low"], spec["back_high"], q[:, 1])
    front = texels.smoothstep(-0.02, -0.07, q[:, 1]) * texels.smoothstep(0.05, 0.02, lateral)
    top = texels.smoothstep(spec["top_low"] + spec.get("top_front", 0.0) * front, spec["top_high"] + spec.get("top_front", 0.0) * front * 0.5, q[:, 2])
    temple = texels.smoothstep(0.052, 0.066, lateral) * texels.smoothstep(0.1, 0.125, q[:, 2])
    ear = numpy.exp(-numpy.sum(((numpy.stack([lateral, q[:, 1], q[:, 2]], axis=1) - numpy.array([0.078, 0.004, 0.08])) / numpy.array([0.022, 0.03, 0.036])) ** 2, axis=1))
    return numpy.clip(numpy.maximum(numpy.maximum(back, top), temple) * (1.0 - ear), 0.0, 1.0)


def blend_skull(face, skull, spec):
    from mathutils.bvhtree import BVHTree
    triangles, corner_triangles = triangulate(skull["sizes"], skull["corners"])
    tree = BVHTree.FromPolygons(skull["points"].tolist(), triangles.tolist(), all_triangles=True)
    points = face["points"]
    target = numpy.array([list(tree.find_nearest(Vector(p))[0]) for p in points])
    weight = skull_weight(points, spec)
    distance = numpy.linalg.norm(target - points, axis=1)
    blended = points + (target - points) * weight[:, None]
    result = dict(face)
    result["points"] = blended
    print("SKULL blend vertices", int((weight > 0.5).sum()), "max shift", round(float((distance * weight).max()), 4))
    return result


def build_mesh(name, points, sizes, corners, uv, weights, names, collection=None):
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(points))
    mesh.vertices.foreach_set("co", numpy.asarray(points, dtype=numpy.float32).ravel())
    mesh.loops.add(len(corners))
    mesh.loops.foreach_set("vertex_index", numpy.asarray(corners, dtype=numpy.int32))
    mesh.polygons.add(len(sizes))
    mesh.polygons.foreach_set("loop_start", corner_starts(sizes).astype(numpy.int32))
    mesh.update(calc_edges=True)
    mesh.validate()
    mesh.polygons.foreach_set("use_smooth", numpy.ones(len(sizes), dtype=bool))
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", numpy.asarray(uv, dtype=numpy.float32).ravel())
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    if weights is not None:
        set_weights(obj, weights, names)
    return obj


def set_weights(obj, weights, names):
    used = [index for index in range(len(names)) if (weights[:, index] > 1e-5).any()]
    for index in used:
        if names[index] not in obj.vertex_groups:
            obj.vertex_groups.new(name=names[index])
    group_index = {index: obj.vertex_groups[names[index]].index for index in used}
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    layer = bm.verts.layers.deform.verify()
    bm.verts.ensure_lookup_table()
    rows, columns = numpy.nonzero(weights[:, used] > 1e-5)
    for row, column in zip(rows.tolist(), columns.tolist()):
        bm.verts[row][layer][group_index[used[column]]] = float(weights[row, used[column]])
    bm.to_mesh(obj.data)
    bm.free()


def bridge(body, head, gap_material=0):
    names = list(dict.fromkeys(list(body["names"]) + list(head["names"])))
    def expand(part):
        table = numpy.zeros((len(part["points"]), len(names)))
        for index, bone in enumerate(part["names"]):
            table[:, names.index(bone)] = part["weights"][:, index]
        return table
    points = numpy.vstack([body["points"], head["points"]])
    sizes = numpy.concatenate([body["sizes"], head["sizes"]])
    corners = numpy.concatenate([body["corners"], head["corners"] + len(body["points"])])
    uv = numpy.vstack([body["uv"], head["uv"]])
    weights = numpy.vstack([expand(body), expand(head)])
    obj = build_mesh("assembled", points, sizes, corners, uv, weights, names)
    materials = numpy.concatenate([numpy.zeros(len(body["sizes"]), dtype=numpy.int32), numpy.ones(len(head["sizes"]), dtype=numpy.int32)])
    obj.data.polygons.foreach_set("material_index", materials)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    border = [edge for edge in bm.edges if edge.is_boundary]
    result = bmesh.ops.bridge_loops(bm, edges=border)
    for face in result["faces"]:
        face.material_index = gap_material
        face.smooth = True
    bm.to_mesh(obj.data)
    bm.free()
    data = read_mesh(obj)
    material = numpy.empty(len(obj.data.polygons), dtype=numpy.int32)
    obj.data.polygons.foreach_get("material_index", material)
    data["material"] = material
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    print("BRIDGE border edges", len(border), "new faces", len(result["faces"]))
    return data


def read_mesh(obj):
    mesh = obj.data
    count = len(mesh.vertices)
    points = numpy.empty(count * 3, dtype=numpy.float64)
    mesh.vertices.foreach_get("co", points)
    sizes = numpy.empty(len(mesh.polygons), dtype=numpy.int32)
    mesh.polygons.foreach_get("loop_total", sizes)
    corners = numpy.empty(len(mesh.loops), dtype=numpy.int32)
    mesh.loops.foreach_get("vertex_index", corners)
    uv = numpy.empty(len(mesh.loops) * 2, dtype=numpy.float64)
    mesh.uv_layers[0].data.foreach_get("uv", uv)
    names = [group.name for group in obj.vertex_groups]
    weights = numpy.zeros((count, len(names)))
    for vertex in mesh.vertices:
        for entry in vertex.groups:
            weights[vertex.index, entry.group] = entry.weight
    return {"points": points.reshape(-1, 3), "sizes": sizes, "corners": corners.astype(numpy.int64), "uv": uv.reshape(-1, 2), "weights": weights, "names": names}


def subdivide(data, levels, name="head_subdivided"):
    obj = build_mesh(name, data["points"], data["sizes"], data["corners"], data["uv"], data["weights"], data["names"])
    modifier = obj.modifiers.new("subdivide", 'SUBSURF')
    modifier.levels = levels
    modifier.render_levels = levels
    modifier.uv_smooth = 'PRESERVE_BOUNDARIES'
    modifier.boundary_smooth = 'PRESERVE_CORNERS'
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier="subdivide")
    result = read_mesh(obj)
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return result


male_morphs = [
    ("lid", (0.032, -0.105, 0.1068), (0.018, 0.012, 0.0062), (0.0, 0.0, -0.0009)),
    ("move", (0.03, -0.11, 0.125), (0.03, 0.018, 0.016), (0.0, -0.0012, 0.0)),
    ("move", (0.0, -0.119, 0.12), (0.02, 0.016, 0.014), (0.0, -0.0008, 0.0)),
    ("move", (0.055, -0.035, 0.0), (0.03, 0.04, 0.03), (0.0015, 0.0, 0.0)),
]

female_morphs = [
    ("squash", 0.047, -0.035, 0.9, -0.02),
    ("taper", 0.09, -0.02, 0.13, 0.01),
    ("scale", (0.0, -0.09, 0.06), (0.1, 0.09, 0.11), (0.945, 1.0, 1.0), (0.0, -0.09, 0.06)),
    ("move", (0.055, -0.035, 0.0), (0.035, 0.045, 0.035), (-0.0042, 0.0, 0.003)),
    ("move", (0.0, -0.128, 0.096), (0.009, 0.012, 0.02), (0.0, -0.0013, 0.0)),
    ("move", (0.0135, -0.115, 0.09), (0.008, 0.012, 0.018), (-0.0012, 0.0012, 0.0)),
    ("inflate", (0.0, -0.127, 0.0335), (0.02, 0.012, 0.0075), 0.0012),
    ("inflate", (0.0, -0.125, 0.0205), (0.02, 0.012, 0.0085), 0.0014),
    ("scale", (0.0, -0.115, -0.005), (0.035, 0.035, 0.035), (0.88, 1.0, 1.0), (0.0, -0.115, 0.0)),
    ("move", (0.03, -0.11, 0.125), (0.035, 0.022, 0.02), (0.0, 0.003, 0.0006)),
    ("move", (0.0, -0.119, 0.12), (0.022, 0.018, 0.016), (0.0, 0.0028, 0.0)),
    ("move", (0.0, -0.1, 0.17), (0.07, 0.04, 0.045), (0.0, -0.003, 0.0)),
    ("scale", (0.0, -0.13, 0.075), (0.03, 0.05, 0.055), (0.78, 0.9, 0.88), (0.0, -0.119, 0.105)),
    ("move", (0.0, -0.146, 0.062), (0.016, 0.02, 0.016), (0.0, 0.0025, 0.0022)),
    ("move", (0.0, -0.136, 0.082), (0.012, 0.015, 0.016), (0.0, 0.0012, 0.0)),
    ("move", (0.016, -0.125, 0.05), (0.012, 0.015, 0.012), (-0.002, 0.0, 0.0)),
    ("move", (0.0, -0.127, 0.034), (0.024, 0.016, 0.01), (0.0, -0.0016, 0.001)),
    ("move", (0.0, -0.124, 0.02), (0.024, 0.016, 0.01), (0.0, -0.0014, -0.0005)),
    ("move", (0.05, -0.085, 0.08), (0.034, 0.034, 0.03), (0.002, -0.0028, 0.0016)),
    ("move", (0.048, -0.078, 0.035), (0.028, 0.028, 0.022), (-0.0012, 0.0008, 0.0)),
    ("inflate", (0.04, -0.1, 0.058), (0.028, 0.03, 0.028), 0.0012),
    ("lid", (0.032, -0.105, 0.104), (0.017, 0.012, 0.007), (0.0, 0.0, -0.0009)),
    ("neck", -0.022, 0.33, -0.004, -0.034, (0.86, 0.91), -0.012),
    ("move", (0.0, -0.065, -0.05), (0.025, 0.03, 0.03), (0.0, 0.004, 0.0)),
    ("scale", (0.075, 0.0, 0.08), (0.025, 0.03, 0.035), (0.9, 0.9, 0.9), (0.075, 0.0, 0.08)),
]

specs = {
    "male": {"face": "sm005", "skull": None, "morphs": male_morphs, "iris": "hazel"},
    "female": {"face": "m002", "skull": "sm005", "back_low": -0.03, "back_high": 0.005, "top_low": 0.15, "top_high": 0.2, "top_front": 0.035, "morphs": female_morphs, "iris": "green"},
}


def head_source(root, name):
    spec = specs[name]
    face = load_avatar(root, spec["face"])
    if spec["skull"]:
        face = blend_skull(face, load_avatar(root, spec["skull"]), spec)
    return face


def neck_plane(front, back):
    point = numpy.array([0.0, front[0], front[1]])
    along = numpy.array([0.0, back[0] - front[0], back[1] - front[1]])
    normal = numpy.cross(numpy.array([1.0, 0.0, 0.0]), along)
    normal /= numpy.linalg.norm(normal)
    if normal[2] < 0.0:
        normal = -normal
    return point, normal


def cut_above(data, point, normal):
    obj = build_mesh("head_cut", data["points"], data["sizes"], data["corners"], data["uv"], data["weights"], data["names"])
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=Vector(point), plane_no=Vector(normal), clear_inner=True)
    bm.to_mesh(obj.data)
    bm.free()
    result = read_mesh(obj)
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return result


lower_lip = ("Bip01 MBottomLip", "Bip01 LMouthBottom", "Bip01 RMouthBottom")
upper_lip = ("Bip01 MUpperLip", "Bip01 LUpperlip", "Bip01 RUpperlip")


def bone_weight(data, bones):
    total = numpy.zeros(len(data["points"]))
    for index, bone in enumerate(data["names"]):
        if bone in bones:
            total += data["weights"][:, index]
    return total


def close_lips(data, origin, overlap=0.0004, width=0.028, reach=0.009):
    points = data["points"].copy()
    local = points - origin
    lower = bone_weight(data, lower_lip)
    upper = bone_weight(data, upper_lip)
    middle = numpy.abs(local[:, 0]) < 0.006
    low_members = middle & (lower > 0.5)
    high_members = middle & (upper > 0.5)
    low_edge = float(local[low_members, 2].max())
    high_edge = float(local[high_members, 2].min())
    gap = high_edge - low_edge + overlap
    if gap <= 0.0:
        return data
    low_peak = float(lower[low_members & (local[:, 2] > low_edge - 0.0015)].mean())
    high_peak = float(upper[high_members & (local[:, 2] < high_edge + 0.0015)].mean())
    span = numpy.clip(1.0 - (local[:, 0] / width) ** 2, 0.0, 1.0)
    rise = lower / low_peak * span * texels.smoothstep(low_edge - reach, low_edge, local[:, 2]) * gap * 0.48
    drop = upper / high_peak * span * texels.smoothstep(high_edge + reach, high_edge, local[:, 2]) * gap * 0.52
    points[:, 2] += numpy.minimum(rise, gap * 0.6) - numpy.minimum(drop, gap * 0.6)
    data["points"] = points
    print("LIPS closed gap", round(gap * 1000.0, 2), "mm between", round(low_edge, 4), round(high_edge, 4))
    return data


def build_head(root, name, levels=1, placement=None):
    spec = specs[name]
    source = head_source(root, name)
    data = subdivide(source, levels)
    normals = smooth_normals(data["points"], data["sizes"], data["corners"])
    data["points"] = apply_morphs(data["points"], normals, spec["morphs"], rocketbox_head)
    data = close_lips(data, rocketbox_head)
    eyes = rocketbox_eyes.copy()
    radius = rocketbox_eye_radius
    if placement is not None:
        head_now, scale = placement
        data["points"] = head_now + (data["points"] - rocketbox_head) * scale
        eyes = head_now + (eyes - rocketbox_head) * scale
        radius = radius * scale
    data["eyes"] = eyes
    data["eye_radius"] = radius
    return data


def boundary_loops(sizes, corners):
    starts = corner_starts(sizes)
    edges = {}
    for face, (start, size) in enumerate(zip(starts, sizes)):
        ring = corners[start:start + size]
        for k in range(size):
            a = int(ring[k])
            b = int(ring[(k + 1) % size])
            key = (min(a, b), max(a, b))
            edges[key] = edges.get(key, 0) + 1
    border = [key for key, count in edges.items() if count == 1]
    neighbours = {}
    for a, b in border:
        neighbours.setdefault(a, []).append(b)
        neighbours.setdefault(b, []).append(a)
    loops = []
    seen = set()
    for start in neighbours:
        if start in seen:
            continue
        loop = [start]
        seen.add(start)
        previous = None
        current = start
        while True:
            options = [n for n in neighbours[current] if n != previous and n not in seen]
            if not options:
                break
            previous = current
            current = options[0]
            loop.append(current)
            seen.add(current)
        loops.append(loop)
    return loops


def rim_directions(data, loops, fallback, passes=6):
    starts = corner_starts(data["sizes"])
    rim = set(vertex for loop in loops for vertex in loop)
    neighbours = {}
    for start, size in zip(starts, data["sizes"]):
        ring = data["corners"][start:start + size]
        for k in range(size):
            a = int(ring[k])
            b = int(ring[(k + 1) % size])
            if a in rim:
                neighbours.setdefault(a, set()).add(b)
            if b in rim:
                neighbours.setdefault(b, set()).add(a)
    points = data["points"]
    result = {}
    for loop in loops:
        raw = []
        for vertex in loop:
            inner = [n for n in neighbours.get(vertex, ()) if n not in rim]
            direction = points[vertex] - numpy.mean(points[inner], axis=0) if inner else fallback
            length = float(numpy.linalg.norm(direction))
            direction = direction / length if length > 1e-9 else fallback
            if direction @ fallback < 0.25:
                direction = direction + fallback * (0.25 - direction @ fallback)
                direction = direction / numpy.linalg.norm(direction)
            raw.append(direction)
        smooth = numpy.array(raw)
        for iteration in range(passes):
            smooth = (numpy.roll(smooth, 1, axis=0) + smooth * 2.0 + numpy.roll(smooth, -1, axis=0)) * 0.25
        smooth = smooth / numpy.maximum(numpy.linalg.norm(smooth, axis=1), 1e-9)[:, None]
        for vertex, direction in zip(loop, smooth):
            result[vertex] = direction
    return result


def closed_triangles(data, drop=None, follow=False):
    triangles, corner_triangles = triangulate(data["sizes"], data["corners"])
    points = [p for p in data["points"]]
    added = []
    loops = boundary_loops(data["sizes"], data["corners"])
    directions = {}
    if drop is not None and follow:
        reach = float(numpy.linalg.norm(drop))
        directions = rim_directions(data, loops, numpy.asarray(drop, dtype=numpy.float64) / reach)
    for loop in loops:
        ring = list(loop)
        if drop is not None:
            lower = []
            for vertex in ring:
                lower.append(len(points))
                points.append(points[vertex] + (directions[vertex] * reach if vertex in directions else drop))
            for k in range(len(ring)):
                a = ring[k]
                b = ring[(k + 1) % len(ring)]
                c = lower[(k + 1) % len(ring)]
                d = lower[k]
                added.append((b, a, d))
                added.append((b, d, c))
            ring = lower
        center = numpy.mean([points[vertex] for vertex in ring], axis=0)
        index = len(points)
        points.append(center)
        for k in range(len(ring)):
            added.append((ring[(k + 1) % len(ring)], ring[k], index))
    if added:
        triangles = numpy.vstack([triangles, numpy.array(added, dtype=triangles.dtype)])
    return numpy.array(points), triangles


def head_graft(data, low, high, point, normal, scale, voxel=0.001, reach=0.06):
    import anatomy
    point = numpy.asarray(point, dtype=numpy.float64)
    normal = numpy.asarray(normal, dtype=numpy.float64)
    low = numpy.asarray(low, dtype=numpy.float64) - numpy.array([0.0, 0.0, reach])
    high = numpy.asarray(high, dtype=numpy.float64)
    points, triangles = closed_triangles(data, -normal * reach, True)
    grid = anatomy.openvdb.FloatGrid.createLevelSetFromPolygons(points.astype(numpy.float32), triangles=triangles.astype(numpy.uint32), transform=anatomy.openvdb.createLinearTransform(voxelSize=voxel), halfWidth=24.0)
    sampler = anatomy.dense_sampler(grid, low, high, voxel)
    rim = numpy.concatenate([data["points"][loop] for loop in boundary_loops(data["sizes"], data["corners"])])
    center = rim.mean(axis=0)

    def weight(query):
        height = (query - point) @ normal
        radial = query - center - numpy.outer((query - center) @ normal, normal)
        near = texels.smoothstep(0.105 * scale, 0.08 * scale, numpy.linalg.norm(radial, axis=1))
        rise = texels.smoothstep(-0.04 * scale, -0.0075 * scale, height)
        return rise * (near + (1.0 - near) * texels.smoothstep(-0.0075 * scale, 0.015 * scale, height))

    result = anatomy.shape("custom", "Bip01 Head", 0.0, "graft", function=sampler, low=low, high=high, weight=weight)
    result.data["sampler"] = sampler
    print("HEAD graft rim height mm", numpy.round(numpy.percentile((rim - point) @ normal, [0, 50, 100]) * 1000.0, 1))
    return result


def cut_below(data, point, normal):
    return cut_above(data, point, -numpy.asarray(normal))


def cornea_profile(rho, radius):
    limbus = radius * 0.395
    return 0.058 * radius * numpy.clip(1.0 - (rho / limbus) ** 2, 0.0, 1.0) ** 2


def clear_eyes(data):
    points = data["points"].copy()
    for center in data["eyes"]:
        radius = data["eye_radius"]
        q = points - center
        r = numpy.linalg.norm(q, axis=1)
        forward = -q[:, 1] / numpy.maximum(r, 1e-9)
        rho = numpy.linalg.norm(q[:, [0, 2]], axis=1)
        bulge = numpy.where(forward > 0.0, cornea_profile(rho, radius), 0.0)
        limit = radius + bulge + 0.00012
        near = (r > radius - 0.0004) & (r < limit) & (forward > 0.2)
        points[near] = center + q[near] / r[near][:, None] * limit[near][:, None]
    data["points"] = points
    return data


def eyeball(center, radius, rings=22, segments=32, limit=2.05):
    rows = [math.pi * ((ring / rings) ** 1.35) for ring in range(1, rings)]
    rows = [theta for theta in rows if theta <= limit]
    points = [numpy.array([0.0, -radius, 0.0])]
    for theta in rows:
        for segment in range(segments):
            phi = 2.0 * math.pi * segment / segments
            points.append(numpy.array([math.sin(theta) * math.cos(phi) * radius, -math.cos(theta) * radius, math.sin(theta) * math.sin(phi) * radius]))
    points = numpy.array(points)
    rho = numpy.linalg.norm(points[:, [0, 2]], axis=1)
    front = points[:, 1] < 0.0
    points[:, 1] -= numpy.where(front, cornea_profile(rho, radius), 0.0)
    faces = []
    for segment in range(segments):
        faces.append((0, 1 + (segment + 1) % segments, 1 + segment))
    for ring in range(len(rows) - 1):
        for segment in range(segments):
            a = 1 + ring * segments + segment
            b = 1 + ring * segments + (segment + 1) % segments
            c = 1 + (ring + 1) * segments + (segment + 1) % segments
            d = 1 + (ring + 1) * segments + segment
            faces.append((a, b, c, d))
    uv = 0.5 + numpy.stack([points[:, 0], points[:, 2]], axis=1) / (2.0 * radius) * 0.94
    back = points[:, 1] > 0.0
    uv[back] = 0.5 + (uv[back] - 0.5) / numpy.maximum(numpy.linalg.norm(uv[back] - 0.5, axis=1), 1e-9)[:, None] * 0.47
    return points + center, faces, uv


def caruncle(center, radius, side):
    medial = numpy.array([-side, 0.0, 0.0])
    anchor = center + numpy.array([-side * radius * 0.86, -radius * 0.42, -radius * 0.05])
    shape = numpy.array([radius * 0.1, radius * 0.1, radius * 0.13])
    points = []
    faces = []
    rings = 6
    segments = 10
    points.append(anchor + numpy.array([0.0, 0.0, shape[2]]))
    for ring in range(1, rings):
        theta = math.pi * ring / rings
        for segment in range(segments):
            phi = 2.0 * math.pi * segment / segments
            points.append(anchor + numpy.array([math.sin(theta) * math.cos(phi) * shape[0], math.sin(theta) * math.sin(phi) * shape[1], math.cos(theta) * shape[2]]))
    points.append(anchor - numpy.array([0.0, 0.0, shape[2]]))
    for segment in range(segments):
        faces.append((0, 1 + segment, 1 + (segment + 1) % segments))
    for ring in range(rings - 2):
        for segment in range(segments):
            a = 1 + ring * segments + segment
            b = 1 + ring * segments + (segment + 1) % segments
            faces.append((a, a + segments, b + segments, b))
    last = len(points) - 1
    base = 1 + (rings - 2) * segments
    for segment in range(segments):
        faces.append((base + segment, last, base + (segment + 1) % segments))
    return numpy.array(points), faces


def eye_object(data, name):
    points = []
    faces = []
    uvs = []
    groups = []
    for index, center in enumerate(data["eyes"]):
        side = 1.0 if center[0] > 0.0 else -1.0
        bone = "Bip01 LEye" if side > 0.0 else "Bip01 REye"
        ball, ball_faces, ball_uv = eyeball(center, data["eye_radius"])
        base = sum(len(p) for p in points)
        points.append(ball)
        faces += [tuple(v + base for v in face) for face in ball_faces]
        uvs.append(ball_uv)
        groups.append((bone, numpy.arange(base, base + len(ball))))
        lump, lump_faces = caruncle(center, data["eye_radius"], side)
        base = sum(len(p) for p in points)
        points.append(lump)
        faces += [tuple(v + base for v in face) for face in lump_faces]
        uvs.append(numpy.tile(numpy.array([[0.04, 0.04]]), (len(lump), 1)))
        groups.append(("Bip01 Head", numpy.arange(base, base + len(lump))))
    points = numpy.concatenate(points)
    uvs = numpy.concatenate(uvs)
    sizes = numpy.array([len(face) for face in faces])
    corners = numpy.array([v for face in faces for v in face])
    obj = build_mesh(name, points, sizes, corners, uvs[corners], None, None)
    for bone, members in groups:
        group = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
        group.add([int(v) for v in members], 1.0, 'REPLACE')
    return obj
