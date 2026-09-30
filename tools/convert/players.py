import bpy
import bmesh
import math
import os
import sys
import time
import numpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import anatomy
import bodies
import turntable
import texels
import faces
import headtex
import eyetex
import bodytex
import grooming
import garments

roots = {"rocketbox": "", "output": "", "previews": ""}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def select(objects, active):
    bpy.context.view_layer.update()
    for other in bpy.context.scene.objects:
        other.select_set(other in objects)
    bpy.context.view_layer.objects.active = active


def avatar_path():
    return os.path.join(roots["rocketbox"], "Avatars", "Adults", "Male_Adult_01", "Export", "Male_Adult_01.fbx")


def load_rig(keep_mesh=False):
    bpy.ops.import_scene.fbx(filepath=avatar_path(), use_anim=False)
    for obj in list(bpy.data.objects):
        if obj.type == 'EMPTY':
            bpy.data.objects.remove(obj, do_unlink=True)
    armature = next(obj for obj in bpy.data.objects if obj.type == 'ARMATURE')
    source = next((obj for obj in bpy.data.objects if obj.type == 'MESH'), None)
    if source is not None and not keep_mesh:
        bpy.data.objects.remove(source, do_unlink=True)
        source = None
    return armature, source


def skeleton_of(armature):
    joints = {}
    frames = {}
    world = armature.matrix_world
    for bone in armature.data.bones:
        matrix = world @ bone.matrix_local
        joints[bone.name] = numpy.array(matrix.translation)
        rotation = matrix.to_3x3().normalized()
        frames[bone.name] = numpy.array([list(rotation.col[0]), list(rotation.col[1]), list(rotation.col[2])])
    return {"joints": joints, "axes": frames}


def neck_cut(front_y, front_z, back_y, back_z, power=0.8):
    def cut(query):
        t = numpy.clip((query[:, 1] - front_y) / (back_y - front_y), 0.0, 1.0) ** power
        return front_z + (back_z - front_z) * t - query[:, 2]

    return cut


def mesh_object(name, points, quads, triangles=None, collection=None):
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(points))
    mesh.vertices.foreach_set("co", numpy.asarray(points, dtype=numpy.float32).ravel())
    faces = [numpy.asarray(quads, dtype=numpy.int32)]
    sizes = [numpy.full(len(quads), 4, dtype=numpy.int32)]
    if triangles is not None and len(triangles):
        faces.append(numpy.asarray(triangles, dtype=numpy.int32))
        sizes.append(numpy.full(len(triangles), 3, dtype=numpy.int32))
    loops = numpy.concatenate([f.ravel() for f in faces])
    counts = numpy.concatenate(sizes)
    mesh.loops.add(len(loops))
    mesh.loops.foreach_set("vertex_index", loops)
    mesh.polygons.add(len(counts))
    mesh.polygons.foreach_set("loop_start", numpy.r_[0, numpy.cumsum(counts)[:-1]].astype(numpy.int32))
    mesh.update(calc_edges=True)
    mesh.validate()
    mesh.polygons.foreach_set("use_smooth", numpy.ones(len(mesh.polygons), dtype=bool))
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def clay(name="clay", color=(0.62, 0.6, 0.58)):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    shader.inputs['Roughness'].default_value = 0.55
    return material


def setup_render(samples=48, resolution=(900, 1400)):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    turntable.accelerate(scene)
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    return scene


def shoot(scene, path, target, direction, distance, lens=50.0, ortho=0.0, resolution=None, up=None):
    data = bpy.data.cameras.new("view")
    data.clip_start = 0.005
    data.clip_end = 100.0
    if ortho > 0.0:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    else:
        data.lens = lens
    camera = bpy.data.objects.new("view", data)
    scene.collection.objects.link(camera)
    camera.location = Vector(target) + Vector(direction).normalized() * distance
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = camera
    if resolution is not None:
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)
    print("RENDERED", path)


characters = {
    "male": {"folder": "survivor_male", "figure": "male", "cut": (-0.07, 1.508, 0.07, 1.613, 1.0), "head_box": ((-0.11, -0.18, 1.44), (0.11, 0.14, 1.86))},
    "female": {"folder": "survivor_female", "figure": "female", "cut": (-0.0638, 1.5302, 0.0622, 1.612, 1.0), "head_box": ((-0.099, -0.1628, 1.4547), (0.099, 0.1252, 1.8327))},
}


def character_setup(name, with_head=True):
    reset()
    spec = characters[name]
    armature, source = load_rig(keep_mesh=True)
    figure = getattr(bodies, spec["figure"])
    deform = None
    if name == "female":
        world = source.matrix_world.copy()
        source.parent = None
        source.matrix_world = world
        reshape_rig(armature, figure)
        deform = feminize(armature, figure)
    skeleton = skeleton_of(armature)
    setup = {"name": name, "spec": spec, "armature": armature, "source": source, "skeleton": skeleton, "figure": figure, "deform": deform}
    if "rig" in figure:
        setup["root_scale"] = figure["rig"]["root_height"] / 0.8952
        skeleton["finger_scale"] = float(rig_factor("Bip01 L Finger01", figure["rig"])[0])
        skeleton["foot_scale"] = float(rig_factor("Bip01 L Toe0", figure["rig"])[0])
        skeleton["scale"] = figure["rig"]["head"]
    setup["placement"] = (numpy.array(skeleton["joints"]["Bip01 Head"]), figure["rig"]["head"] if "rig" in figure else 1.0)
    if with_head:
        low, high = head_box(name, skeleton)
        smooth_head = faces.build_head(roots["rocketbox"], name, levels=2, placement=setup["placement"])
        point, normal = neck_frame(setup)
        setup["head"] = faces.head_graft(smooth_head, low, high, point, normal, setup["placement"][1])
    source.hide_render = True
    armature.hide_render = True
    return setup


def neck_frame(setup):
    front_y, front_z, back_y, back_z, power = cut_of(setup["name"], setup["skeleton"])
    return faces.neck_plane((front_y, front_z), (back_y, back_z))


def weight_table(indices, values, count):
    table = numpy.zeros((len(indices), count))
    for slot in range(indices.shape[1]):
        numpy.add.at(table, (numpy.arange(len(indices)), indices[:, slot]), values[:, slot])
    return table


def stage_assemble(setup, cache, gap=0.005, band=0.035):
    low = numpy.load(os.path.join(cache, "low.npz"))
    stored = numpy.load(os.path.join(cache, "weights.npz"))
    names = [str(n) for n in stored["names"]]
    points = low["points"].astype(numpy.float64)
    triangles = low["triangles"].astype(numpy.int64)
    table = weight_table(stored["indices"], stored["values"], len(names))
    point, normal = neck_frame(setup)
    head = faces.clear_eyes(faces.build_head(roots["rocketbox"], setup["name"], levels=1, placement=setup["placement"]))
    head_cut = faces.cut_above(head, point, normal)
    body = {"points": points, "sizes": numpy.full(len(triangles), 3, dtype=numpy.int32), "corners": triangles.ravel(), "uv": numpy.zeros((len(triangles) * 3, 2)), "weights": table, "names": names}
    body_cut = faces.cut_below(body, point - normal * gap, normal)
    from mathutils.bvhtree import BVHTree
    whole_head = BVHTree.FromPolygons(head["points"].tolist(), faces.triangulate(head["sizes"], head["corners"])[0].tolist(), all_triangles=True)
    top = numpy.flatnonzero((body_cut["points"] - point) @ normal > -gap - 0.004)
    step = [whole_head.find_nearest(Vector(body_cut["points"][index]))[3] for index in top]
    print("ASSEMBLE body rim to head surface mm mean", round(float(numpy.mean(step)) * 1000.0, 2), "max", round(float(numpy.max(step)) * 1000.0, 2))
    data = faces.bridge(body_cut, head_cut)
    seam_triangles = faces.triangulate(data["sizes"], data["corners"])[0]
    seam_edges = numpy.unique(numpy.sort(numpy.concatenate([seam_triangles[:, [0, 1]], seam_triangles[:, [1, 2]], seam_triangles[:, [2, 0]]]), axis=1), axis=0)
    relaxed = data["points"].copy()
    pull = texels.smoothstep(0.014, 0.004, numpy.abs((relaxed - point) @ normal + gap * 0.5))
    for iteration in range(16):
        total = numpy.zeros_like(relaxed)
        count = numpy.zeros(len(relaxed))
        numpy.add.at(total, seam_edges[:, 0], relaxed[seam_edges[:, 1]])
        numpy.add.at(total, seam_edges[:, 1], relaxed[seam_edges[:, 0]])
        numpy.add.at(count, seam_edges[:, 0], 1.0)
        numpy.add.at(count, seam_edges[:, 1], 1.0)
        relaxed = relaxed + (total / numpy.maximum(count, 1.0)[:, None] - relaxed) * ((0.5 if iteration % 2 == 0 else -0.52) * pull)[:, None]
    print("ASSEMBLE seam relaxed vertices", int((pull > 0.0).sum()), "largest move", round(float(numpy.linalg.norm(relaxed - data["points"], axis=1).max()) * 1000.0, 2), "mm")
    data["points"] = relaxed
    names_final = data["names"]
    weights = data["weights"]
    head_vertices = numpy.zeros(len(data["points"]), dtype=bool)
    starts = faces.corner_starts(data["sizes"])
    for face in numpy.flatnonzero(data["material"] == 1):
        head_vertices[data["corners"][starts[face]:starts[face] + data["sizes"][face]]] = True
    height = (data["points"] - point) @ normal
    border = head_vertices & (height < 0.003)
    from mathutils.kdtree import KDTree
    tree = KDTree(int(border.sum()))
    border_index = numpy.flatnonzero(border)
    for slot, index in enumerate(border_index):
        tree.insert(data["points"][index].tolist(), slot)
    tree.balance()
    blend_region = (~head_vertices) & (height > -band)
    for index in numpy.flatnonzero(blend_region):
        location, slot, distance = tree.find(data["points"][index].tolist())
        t = numpy.clip(1.0 + height[index] / band, 0.0, 1.0)
        t = t * t * (3.0 - 2.0 * t)
        weights[index] = weights[index] * (1.0 - t) + weights[border_index[slot]] * t
    order = numpy.argsort(-weights, axis=1)[:, :4]
    top = numpy.take_along_axis(weights, order, axis=1)
    top = numpy.maximum(top, 0.0)
    total = top.sum(axis=1)
    empty = total < 1e-6
    top = top / numpy.maximum(total, 1e-9)[:, None]
    if empty.any():
        print("ASSEMBLE vertices without weights", int(empty.sum()))
    bone_order = [str(n) for n in stored["names"]]
    remap = numpy.array([bone_order.index(n) for n in names_final])
    triangles_final, corner_triangles, face_of_triangle = faces.triangulate(data["sizes"], data["corners"], True)
    numpy.savez(os.path.join(cache, "final.npz"), points=data["points"].astype(numpy.float32), triangles=triangles_final.astype(numpy.int32), material=data["material"][face_of_triangle].astype(numpy.int32), head_uv=data["uv"][corner_triangles].astype(numpy.float32), indices=remap[order].astype(numpy.int32), values=top.astype(numpy.float32), names=numpy.array(bone_order), eyes=numpy.asarray(head["eyes"]), eye_radius=numpy.array([head["eye_radius"]]))
    counts = numpy.bincount(data["material"][face_of_triangle], minlength=2)
    print("ASSEMBLE vertices", len(data["points"]), "triangles body/head", counts.tolist())


def rig_factor(name, rig):
    for key, value in rig["bones"]:
        if key in name:
            return numpy.asarray(value, dtype=numpy.float64)
    return numpy.full(3, rig["default"])


def reshape_rig(armature, figure):
    rig = figure["rig"]
    world = armature.matrix_world.copy()
    old = {bone.name: numpy.array(world @ bone.head_local) for bone in armature.data.bones}
    new = {}
    order = []
    stack = [bone for bone in armature.data.bones if bone.parent is None]
    while stack:
        bone = stack.pop(0)
        order.append(bone)
        stack += list(bone.children)
    for bone in order:
        if bone.parent is None:
            new[bone.name] = numpy.array([old[bone.name][0], old[bone.name][1], rig["root_height"]])
        else:
            offset = old[bone.name] - old[bone.parent.name]
            factor = rig_factor(bone.name, rig) if not is_facial(bone.name) else numpy.full(3, rig["head"])
            new[bone.name] = new[bone.parent.name] + offset * factor
    armature.location.z = rig["root_height"]
    bpy.context.view_layer.update()
    inverse = armature.matrix_world.inverted()
    select([armature], armature)
    bpy.ops.object.mode_set(mode='EDIT')
    for edit in armature.data.edit_bones:
        direction = edit.tail - edit.head
        head = inverse @ Vector(new[edit.name])
        edit.head = head
        edit.tail = head + direction
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    print("RESHAPED rig root", rig["root_height"], "head", new["Bip01 Head"].round(4), "hand", new["Bip01 L Hand"].round(4), "toe", new["Bip01 L Toe0"].round(4))


def feminize(armature, figure):
    rig = figure["rig"]
    male_head = numpy.array([0.0, -0.0081, 1.5871])

    def deform(mesh, matrix):
        points = mesh_points(mesh)
        world = numpy.asarray(matrix)
        points = points @ world[:3, :3].T + world[:3, 3]
        head_now = numpy.array(armature.matrix_world @ armature.data.bones["Bip01 Head"].head_local)
        moved = head_now + (points - male_head) * rig["head"]
        inverse = numpy.linalg.inv(world)
        moved = moved @ inverse[:3, :3].T + inverse[:3, 3]
        mesh.vertices.foreach_set("co", moved.astype(numpy.float32).ravel())
        mesh.update()

    return deform


def head_box(name, skeleton):
    low, high = characters[name]["head_box"]
    offset = skeleton["joints"]["Bip01 Head"] - numpy.array([0.0, -0.0081, 1.5871])
    return tuple(numpy.asarray(low) + offset), tuple(numpy.asarray(high) + offset)


def cut_of(name, skeleton):
    front_y, front_z, back_y, back_z, power = characters[name]["cut"]
    offset = skeleton["joints"]["Bip01 Head"] - numpy.array([0.0, -0.0081, 1.5871])
    return front_y + offset[1], front_z + offset[2], back_y + offset[1], back_z + offset[2], power


def detail_boxes(setup):
    skeleton = setup["skeleton"]
    boxes = {}
    for side, flip in (("L", 1.0), ("R", -1.0)):
        points = [skeleton["joints"]["Bip01 L Hand"]]
        for index in range(5):
            names, chain_points = bodies.finger_points(skeleton, index)
            points += chain_points
        wrist = skeleton["joints"]["Bip01 L Hand"]
        points.append(wrist + (skeleton["joints"]["Bip01 L Forearm"] - wrist) * 0.12)
        points = numpy.array(points) * numpy.array([flip, 1.0, 1.0])
        boxes["hand_" + side.lower()] = (points.min(axis=0) - 0.022, points.max(axis=0) + 0.022, 0.0003)
        ankle = skeleton["joints"]["Bip01 L Foot"] * numpy.array([flip, 1.0, 1.0])
        ball = skeleton["joints"]["Bip01 L Toe0"] * numpy.array([flip, 1.0, 1.0])
        low = numpy.array([min(ankle[0], ball[0]) - 0.075, ball[1] - 0.12, -0.012])
        high = numpy.array([max(ankle[0], ball[0]) + 0.075, ankle[1] + 0.09, ankle[2] + 0.045])
        boxes["foot_" + side.lower()] = (low, high, 0.0004)
    return boxes


def body_bounds(skeleton):
    points = numpy.array(list(skeleton["joints"].values()))
    return tuple(points.min(axis=0) - numpy.array([0.12, 0.25, 0.02])), tuple(points.max(axis=0) + numpy.array([0.12, 0.25, 0.25]))


def save_level_set(shapes, low, high, voxel, path):
    start = time.time()
    grid = anatomy.level_set(shapes, low, high, voxel)
    points, triangles, quads = anatomy.mesh_of(grid)
    numpy.savez(path, points=points.astype(numpy.float32), quads=quads.astype(numpy.int32))
    print("SAVED", path, len(points), "points", len(quads), "quads", round(time.time() - start, 1), "s")


def load_mesh(path, name):
    data = numpy.load(path)
    return mesh_object(name, data["points"], data["quads"])


def stage_sculpt(setup, cache):
    shapes = bodies.build(setup["skeleton"], setup["figure"], setup["head"])
    low, high = body_bounds(setup["skeleton"])
    save_level_set(shapes, low, high, 0.0015, os.path.join(cache, "source.npz"))


def region_of(points, setup):
    regions = numpy.zeros(len(points), dtype=numpy.int32)
    for key, (low, high, voxel) in detail_boxes(setup).items():
        inside = numpy.all((points >= low + 0.012) & (points <= high - 0.012), axis=1)
        regions[inside] = 1 if key.startswith("hand") else 2
    head = setup["skeleton"]["joints"]["Bip01 Head"]
    cut = neck_cut(*cut_of(setup["name"], setup["skeleton"]))
    above = cut(points) < -0.01
    face = above & (points[:, 1] < head[1] - 0.035)
    regions[above] = 3
    regions[face] = 4
    landmarks = setup["figure"].get("landmarks", {})
    reach = setup["figure"].get("nipples", {}).get("areola", 0.0) * 1.6
    for key in ("nipple_l", "nipple_r"):
        if key in landmarks:
            regions[numpy.linalg.norm(points - landmarks[key], axis=1) < reach] = 5
    return regions


def mesh_points(mesh):
    points = numpy.empty(len(mesh.vertices) * 3, dtype=numpy.float32)
    mesh.vertices.foreach_get("co", points)
    return points.reshape(-1, 3).astype(numpy.float64)


def mesh_triangles(mesh):
    mesh.calc_loop_triangles()
    triangles = numpy.empty(len(mesh.loop_triangles) * 3, dtype=numpy.int32)
    mesh.loop_triangles.foreach_get("vertices", triangles)
    return triangles.reshape(-1, 3)


def vertex_normals(points, triangles):
    a = points[triangles[:, 0]]
    b = points[triangles[:, 1]]
    c = points[triangles[:, 2]]
    face = numpy.cross(b - a, c - a)
    normals = numpy.zeros_like(points)
    for corner in range(3):
        numpy.add.at(normals, triangles[:, corner], face)
    return normals / numpy.maximum(numpy.linalg.norm(normals, axis=1), 1e-12)[:, None]


def relax(points, triangles, shapes, iterations, amount=0.5):
    edges = numpy.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    edges = numpy.unique(numpy.sort(edges, axis=1), axis=0)
    for iteration in range(iterations):
        total = numpy.zeros_like(points)
        count = numpy.zeros(len(points))
        numpy.add.at(total, edges[:, 0], points[edges[:, 1]])
        numpy.add.at(total, edges[:, 1], points[edges[:, 0]])
        numpy.add.at(count, edges[:, 0], 1.0)
        numpy.add.at(count, edges[:, 1], 1.0)
        delta = total / numpy.maximum(count, 1.0)[:, None] - points
        normals = vertex_normals(points, triangles)
        delta -= normals * numpy.sum(delta * normals, axis=1)[:, None]
        points = points + delta * amount
        points = anatomy.project(shapes, points, 2, 0.003)
    return points


def folded(points, triangles):
    normals = vertex_normals(points, triangles)
    faces = numpy.cross(points[triangles[:, 1]] - points[triangles[:, 0]], points[triangles[:, 2]] - points[triangles[:, 0]])
    return numpy.sum(faces * normals[triangles].mean(axis=1), axis=1) < 0.0


def unfold(points, triangles, shapes, attempts=8):
    edges = numpy.unique(numpy.sort(numpy.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]]), axis=1), axis=0)
    points = points.copy()
    for attempt in range(attempts):
        bad = folded(points, triangles)
        print("LOWPOLY folded triangles", int(bad.sum()))
        if not bad.any():
            break
        chosen = numpy.zeros(len(points), dtype=bool)
        chosen[triangles[bad].ravel()] = True
        total = numpy.zeros_like(points)
        count = numpy.zeros(len(points))
        numpy.add.at(total, edges[:, 0], points[edges[:, 1]])
        numpy.add.at(total, edges[:, 1], points[edges[:, 0]])
        numpy.add.at(count, edges[:, 0], 1.0)
        numpy.add.at(count, edges[:, 1], 1.0)
        average = total / numpy.maximum(count, 1.0)[:, None]
        points[chosen] = average[chosen]
        points[chosen] = anatomy.project(shapes, points[chosen], 2, 0.002)
    return points


def collapse_folds(points, triangles):
    points = points.copy()
    for attempt in range(4):
        bad = numpy.flatnonzero(folded(points, triangles))
        if not len(bad):
            break
        remap = numpy.arange(len(points))
        touched = numpy.zeros(len(points), dtype=bool)
        for face in bad:
            corners = triangles[face]
            if touched[corners].any():
                continue
            pairs = ((corners[0], corners[1]), (corners[1], corners[2]), (corners[2], corners[0]))
            lengths = [float(numpy.linalg.norm(points[a] - points[b])) for a, b in pairs]
            a, b = pairs[int(numpy.argmin(lengths))]
            points[a] = (points[a] + points[b]) * 0.5
            remap[b] = a
            touched[corners] = True
        triangles = remap[triangles]
        keep = (triangles[:, 0] != triangles[:, 1]) & (triangles[:, 1] != triangles[:, 2]) & (triangles[:, 2] != triangles[:, 0])
        triangles = triangles[keep]
        keys = numpy.sort(triangles, axis=1)
        unique_keys, inverse, counts = numpy.unique(keys, axis=0, return_inverse=True, return_counts=True)
        triangles = triangles[counts[inverse.ravel()] == 1]
        used, compact = numpy.unique(triangles, return_inverse=True)
        points = points[used]
        triangles = compact.reshape(-1, 3)
    edges = numpy.sort(numpy.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]]), axis=1)
    unique_edges, edge_counts = numpy.unique(edges, axis=0, return_counts=True)
    print("LOWPOLY after collapse folded", int(folded(points, triangles).sum()), "open edges", int((edge_counts == 1).sum()), "nonmanifold edges", int((edge_counts > 2).sum()))
    return points, triangles


def stage_lowpoly(setup, cache, target=62000):
    shapes = bodies.build(setup["skeleton"], setup["figure"], setup["head"])
    obj = load_mesh(os.path.join(cache, "source.npz"), "lowpoly")
    source_triangles = len(mesh_triangles(obj.data))
    modifier = obj.modifiers.new("decimate", 'DECIMATE')
    modifier.decimate_type = 'COLLAPSE'
    modifier.ratio = target / source_triangles
    modifier.use_collapse_triangulate = True
    bpy.context.view_layer.update()
    decimated = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    obj.modifiers.clear()
    points = mesh_points(decimated)
    triangles = mesh_triangles(decimated)
    counts = numpy.bincount(region_of(points, setup)[triangles[:, 0]], minlength=6)
    print("DECIMATED", len(triangles), "triangles per region body/hands/feet/head/face/nipples", counts.tolist())
    bm = bmesh.new()
    bm.from_mesh(decimated)
    for region, cuts, rule in ((5, 2, any),):
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        regions = region_of(numpy.array([list(v.co) for v in bm.verts]), setup)
        chosen = [face for face in bm.faces if rule(regions[v.index] == region for v in face.verts)]
        edges = list({edge for face in chosen for edge in face.edges})
        if edges:
            bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True, use_single_edge=False, use_only_quads=False)
            bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    subdivided = bpy.data.meshes.new("subdivided")
    bm.to_mesh(subdivided)
    bm.free()
    points = mesh_points(subdivided)
    triangles = mesh_triangles(subdivided)
    points = anatomy.project(shapes, points, 3, 0.003)
    points = relax(points, triangles, shapes, 4)
    points = unfold(points, triangles, shapes)
    points, triangles = collapse_folds(points, triangles)
    counts = numpy.bincount(region_of(points, setup)[triangles[:, 0]], minlength=6)
    numpy.savez(os.path.join(cache, "low.npz"), points=points.astype(numpy.float32), triangles=triangles.astype(numpy.int32))
    print("LOWPOLY", len(points), "points", len(triangles), "triangles per region", counts.tolist())
    return points, triangles


facial = ("Eye", "Jaw", "Lip", "lip", "Tongue", "Mouth", "Masseter", "Caninus", "Cheek", "Brow", "brow", "Nose")


def is_facial(name):
    return any(key in name for key in facial)


def bone_tail(armature, skeleton, name):
    joints = skeleton["joints"]
    follow = {"Bip01 Pelvis": "Bip01 Spine", "Bip01 Spine": "Bip01 Spine1", "Bip01 Spine1": "Bip01 Spine2", "Bip01 Spine2": "Bip01 Neck", "Bip01 Neck": "Bip01 Head"}
    for side in ("L", "R"):
        follow["Bip01 %s Clavicle" % side] = "Bip01 %s UpperArm" % side
        follow["Bip01 %s UpperArm" % side] = "Bip01 %s Forearm" % side
        follow["Bip01 %s Forearm" % side] = "Bip01 %s Hand" % side
        follow["Bip01 %s Hand" % side] = "Bip01 %s Finger2" % side
        follow["Bip01 %s Thigh" % side] = "Bip01 %s Calf" % side
        follow["Bip01 %s Calf" % side] = "Bip01 %s Foot" % side
        follow["Bip01 %s Foot" % side] = "Bip01 %s Toe0" % side
        for finger in range(5):
            follow["Bip01 %s Finger%d" % (side, finger)] = "Bip01 %s Finger%d1" % (side, finger)
            follow["Bip01 %s Finger%d1" % (side, finger)] = "Bip01 %s Finger%d2" % (side, finger)
    if name in follow:
        return joints[follow[name]]
    x_axis = skeleton["axes"][name][0]
    if name == "Bip01 Head":
        return joints[name] + x_axis * bodies.nubs["Head"] * skeleton.get("scale", 1.0)
    if "Toe0" in name:
        return joints[name] + x_axis * bodies.nubs["Toe0"] * skeleton.get("foot_scale", 1.0)
    finger = name.split("Finger")[-1][0]
    return joints[name] + x_axis * bodies.nubs["Finger" + finger] * skeleton.get("finger_scale", 1.0)


def heat_weights(obj, armature, skeleton):
    data = bpy.data.armatures.new("heat")
    heat = bpy.data.objects.new("heat", data)
    bpy.context.scene.collection.objects.link(heat)
    bpy.context.view_layer.objects.active = heat
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.bones:
        if is_facial(bone.name):
            continue
        edit = data.edit_bones.new(bone.name)
        edit.head = Vector(skeleton["joints"][bone.name])
        edit.tail = Vector(bone_tail(armature, skeleton, bone.name))
    bpy.ops.object.mode_set(mode='OBJECT')
    select([obj, heat], heat)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    weights = group_weights(obj)
    obj.parent = None
    obj.modifiers.clear()
    bpy.data.objects.remove(heat)
    return weights


def group_weights(obj):
    names = [group.name for group in obj.vertex_groups]
    table = numpy.zeros((len(obj.data.vertices), len(names)), dtype=numpy.float32)
    for vertex in obj.data.vertices:
        for entry in vertex.groups:
            table[vertex.index, entry.group] = entry.weight
    return {name: table[:, index] for index, name in enumerate(names)}


def transfer_source(setup):
    source = setup["source"]
    if setup.get("deform") is None:
        return source
    mesh = source.data.copy()
    setup["deform"](mesh, source.matrix_world)
    copy = bpy.data.objects.new("source_deformed", mesh)
    bpy.context.scene.collection.objects.link(copy)
    copy.matrix_world = source.matrix_world
    for group in source.vertex_groups:
        copy.vertex_groups.new(name=group.name)
    return copy


def transferred_weights(obj, source):
    copy = bpy.data.objects.new("transfer", obj.data.copy())
    bpy.context.scene.collection.objects.link(copy)
    for group in source.vertex_groups:
        copy.vertex_groups.new(name=group.name)
    modifier = copy.modifiers.new("transfer", 'DATA_TRANSFER')
    modifier.object = source
    modifier.use_vert_data = True
    modifier.data_types_verts = {'VGROUP_WEIGHTS'}
    modifier.vert_mapping = 'POLYINTERP_NEAREST'
    modifier.layers_vgroup_select_src = 'ALL'
    modifier.layers_vgroup_select_dst = 'NAME'
    select([copy], copy)
    bpy.ops.object.modifier_apply(modifier="transfer")
    weights = group_weights(copy)
    mesh = copy.data
    bpy.data.objects.remove(copy)
    bpy.data.meshes.remove(mesh)
    return weights


def pack_weights(weights, names, count=4):
    table = numpy.stack([weights.get(name, numpy.zeros_like(next(iter(weights.values())))) for name in names], axis=1)
    order = numpy.argsort(-table, axis=1)[:, :count]
    values = numpy.take_along_axis(table, order, axis=1)
    values = numpy.maximum(values, 0.0)
    total = values.sum(axis=1)
    values = values / numpy.maximum(total, 1e-9)[:, None]
    return order.astype(numpy.int32), values.astype(numpy.float32), total


def stage_rig(setup, cache):
    data = numpy.load(os.path.join(cache, "low.npz"))
    points = data["points"].astype(numpy.float64)
    obj = mesh_object("rig", points, numpy.zeros((0, 4), dtype=numpy.int32), data["triangles"])
    armature = setup["armature"]
    names = [bone.name for bone in armature.data.bones]
    heat = heat_weights(obj, armature, setup["skeleton"])
    transfer = transferred_weights(obj, transfer_source(setup))
    cut = neck_cut(*cut_of(setup["name"], setup["skeleton"]))
    blend = numpy.clip((-cut(points) + 0.004) / 0.03, 0.0, 1.0)
    blend = blend * blend * (3.0 - 2.0 * blend)
    merged = {}
    for name in names:
        a = heat.get(name, numpy.zeros(len(points), dtype=numpy.float32))
        b = transfer.get(name, numpy.zeros(len(points), dtype=numpy.float32))
        merged[name] = a * (1.0 - blend) + b * blend
    shapes = bodies.build(setup["skeleton"], setup["figure"], None)
    landmarks = setup["figure"].get("landmarks", {})
    if "groin" in landmarks:
        center, radii = landmarks["groin"]
        near = numpy.flatnonzero(numpy.linalg.norm((points - center) / (numpy.asarray(radii) * 1.7), axis=1) < 1.0)
        hold = numpy.zeros(len(points))
        if "shaft" in setup["figure"]["groin"]:
            hold[near] = texels.smoothstep(0.002, 0.009, bodies.protrusion(shapes, points[near]))
        else:
            hold[near] = texels.smoothstep(1.0, 0.4, numpy.linalg.norm((points[near] - center) / numpy.asarray(radii), axis=1)) * 0.65
        everything = sum(merged[name] for name in names)
        for name in names:
            merged[name] = merged[name] * (1.0 - hold) + (everything if name == "Bip01 Pelvis" else 0.0) * hold
        print("RIG groin vertices held to the pelvis", int((hold > 0.5).sum()))
    if "breast" in setup["figure"]:
        chest = ("Bip01 Spine", "Bip01 Spine1", "Bip01 Spine2")
        hold = numpy.zeros(len(points))
        for key in ("breast_l", "breast_r"):
            center, outward, radii = setup["figure"]["landmarks"][key]
            reach = numpy.linalg.norm((points - center) / (numpy.asarray(radii) * 1.35), axis=1)
            hold = numpy.maximum(hold, texels.smoothstep(1.0, 0.55, reach))
        spine_total = sum(merged[name] for name in chest)
        everything = sum(merged[name] for name in names)
        for name in names:
            if name in chest:
                target = numpy.where(spine_total > 1e-4, merged[name] / numpy.maximum(spine_total, 1e-6), 1.0 if name == "Bip01 Spine2" else 0.0) * everything
            else:
                target = 0.0
            merged[name] = merged[name] * (1.0 - hold) + target * hold
        print("RIG breast vertices held to the chest", int((hold > 0.5).sum()))
    indices, values, total = pack_weights(merged, names)
    empty = total < 1e-4
    if empty.any():
        joints = numpy.array([setup["skeleton"]["joints"][name] for name in names])
        usable = numpy.array([not is_facial(name) for name in names])
        distances = numpy.linalg.norm(points[empty][:, None, :] - joints[None, :, :], axis=2)
        distances[:, ~usable] = numpy.inf
        indices[empty, 0] = numpy.argmin(distances, axis=1)
        values[empty] = numpy.array([1.0, 0.0, 0.0, 0.0])
    print("RIG vertices", len(points), "unweighted", int(empty.sum()), "bones used", len(numpy.unique(indices[values > 0.01])))
    numpy.savez(os.path.join(cache, "weights.npz"), indices=indices, values=values, names=numpy.array(names))


def bone_part(name):
    if is_facial(name) or name == "Bip01 Head":
        return "torso"
    side = "l" if " L " in name else "r"
    if "Finger" in name or "Hand" in name:
        return "hand_" + side
    if "UpperArm" in name or "Forearm" in name:
        return "arm_" + side
    if "Thigh" in name or "Calf" in name:
        return "leg_" + side
    if "Foot" in name or "Toe" in name:
        return "foot_" + side
    return "torso"


part_names = ["torso", "arm_l", "arm_r", "hand_l", "hand_r", "leg_l", "leg_r", "foot_l", "foot_r"]


def face_adjacency(triangles):
    edges = numpy.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    owners = numpy.tile(numpy.arange(len(triangles)), 3)
    keys = numpy.sort(edges, axis=1)
    order = numpy.lexsort((keys[:, 1], keys[:, 0]))
    keys = keys[order]
    owners = owners[order]
    same = numpy.all(keys[1:] == keys[:-1], axis=1)
    pairs = numpy.stack([owners[:-1][same], owners[1:][same]], axis=1)
    return pairs, keys[:-1][same]


def majority(labels, pairs, iterations=4):
    count = labels.max() + 1
    for iteration in range(iterations):
        votes = numpy.zeros((len(labels), count), dtype=numpy.int32)
        numpy.add.at(votes, (pairs[:, 0], labels[pairs[:, 1]]), 1)
        numpy.add.at(votes, (pairs[:, 1], labels[pairs[:, 0]]), 1)
        numpy.add.at(votes, (numpy.arange(len(labels)), labels), 1)
        labels = numpy.argmax(votes, axis=1)
    return labels


def limb_angle(points, chain, medial):
    best = numpy.full(len(points), numpy.inf)
    angle = numpy.zeros(len(points))
    for start, end in zip(chain[:-1], chain[1:]):
        axis = anatomy.unit(end - start)
        length = float(numpy.linalg.norm(end - start))
        inward = anatomy.unit(medial - axis * numpy.dot(medial, axis))
        other = numpy.cross(axis, inward)
        q = points - start
        along = q @ axis
        nearest = start + numpy.outer(numpy.clip(along, 0.0, length), axis)
        distance = numpy.linalg.norm(points - nearest, axis=1)
        closer = distance < best
        best = numpy.where(closer, distance, best)
        angle = numpy.where(closer, numpy.arctan2(q @ other, -(q @ inward)), angle)
    return angle


def surface_side(points, setup, names, dominant):
    skeleton = setup["skeleton"]
    joints = skeleton["joints"]
    side = numpy.zeros(len(points))
    for index, name in enumerate(names):
        chosen = dominant == index
        if not chosen.any():
            continue
        part = bone_part(name)
        axes = skeleton["axes"][name]
        if part.startswith("hand"):
            q = points[chosen] - joints[name]
            if "Finger" in name:
                tail = bone_tail(setup["armature"], skeleton, name)
                length = numpy.linalg.norm(tail - joints[name])
                t = numpy.clip(q @ anatomy.unit(tail - joints[name]), 0.0, length)
                q = points[chosen] - (joints[name] + numpy.outer(t, anatomy.unit(tail - joints[name])))
                side[chosen] = -(q @ axes[1]) + 0.0017
            else:
                side[chosen] = -(q @ axes[1]) + 0.0017
        elif part.startswith("foot"):
            side[chosen] = 1.0
    return side


def stage_uv(setup, cache):
    final = numpy.load(os.path.join(cache, "final.npz"))
    all_points = final["points"].astype(numpy.float64)
    all_triangles = final["triangles"].astype(numpy.int64)
    material = final["material"]
    names = [str(n) for n in final["names"]]
    body_faces = numpy.flatnonzero(material == 0)
    used, remap = numpy.unique(all_triangles[body_faces], return_inverse=True)
    points = all_points[used]
    triangles = remap.reshape(-1, 3)
    dominant = final["indices"][used, 0]
    skeleton = setup["skeleton"]
    joints = skeleton["joints"]
    vertex_part = numpy.array([part_names.index(bone_part(names[i])) for i in dominant])
    pairs, shared = face_adjacency(triangles)
    labels = numpy.array([numpy.bincount(vertex_part[t], minlength=len(part_names)).argmax() for t in triangles])
    labels = majority(labels, pairs, 6)
    centers = points[triangles].mean(axis=1)
    sub = numpy.zeros(len(triangles), dtype=numpy.int32)
    normals = vertex_normals(points, triangles)
    face_normals = normals[triangles].mean(axis=1)
    torso = labels == part_names.index("torso")
    spine_y = numpy.interp(centers[:, 2], [joints["Bip01 Pelvis"][2], joints["Bip01 Spine1"][2], joints["Bip01 Neck"][2]], [joints["Bip01 Pelvis"][1], joints["Bip01 Spine1"][1], joints["Bip01 Neck"][1]])
    sub[torso] = (centers[torso, 1] > spine_y[torso] + 0.01).astype(numpy.int32)
    vertex_side = surface_side(points, setup, names, dominant)
    for part in ("hand_l", "hand_r"):
        chosen = labels == part_names.index(part)
        sub[chosen] = (vertex_side[triangles[chosen]].mean(axis=1) > 0.0).astype(numpy.int32)
    for part in ("foot_l", "foot_r"):
        chosen = labels == part_names.index(part)
        sub[chosen] = (face_normals[chosen, 2] < -0.3).astype(numpy.int32)
    combined = absorb_small(majority(labels * 2 + sub, pairs, 3), pairs, triangles, 80)
    labels = combined // 2
    sub = combined % 2
    seam = (labels[pairs[:, 0]] != labels[pairs[:, 1]]) | (sub[pairs[:, 0]] != sub[pairs[:, 1]])
    for side, flip in (("l", 1.0), ("r", -1.0)):
        s = "L" if side == "l" else "R"
        arm_medial = numpy.array([-flip, 0.0, -0.8])
        leg_medial = numpy.array([-flip, 0.0, 0.0])
        limbs = (("arm_" + side, [joints["Bip01 %s UpperArm" % s], joints["Bip01 %s Forearm" % s], joints["Bip01 %s Hand" % s]], arm_medial), ("leg_" + side, [joints["Bip01 %s Thigh" % s], joints["Bip01 %s Calf" % s], joints["Bip01 %s Foot" % s]], leg_medial))
        for part, chain, medial in limbs:
            index = part_names.index(part)
            angle = limb_angle(points, chain, medial)
            a = angle[shared[:, 0]]
            b = angle[shared[:, 1]]
            inside = (labels[pairs[:, 0]] == index) & (labels[pairs[:, 1]] == index)
            seam |= inside & (numpy.abs(a - b) > numpy.pi)
    edge_keys = {tuple(key) for key in shared[seam].tolist()}
    obj = mesh_object("uv", points, numpy.zeros((0, 4), dtype=numpy.int32), triangles)
    mesh = obj.data
    for edge in mesh.edges:
        key = tuple(sorted(edge.vertices))
        edge.use_seam = key in edge_keys
    mesh.uv_layers.new(name="UVMap")
    select([obj], obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', iterations=40, margin=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')
    loops = numpy.empty(len(mesh.loops) * 2, dtype=numpy.float32)
    mesh.uv_layers["UVMap"].data.foreach_get("uv", loops)
    uv = loops.reshape(len(triangles), 3, 2).astype(numpy.float64)
    islands = island_ids(triangles, pairs, seam)
    factors = {"hand_l": 1.8, "hand_r": 1.8, "foot_l": 1.25, "foot_r": 1.25}
    for island in numpy.unique(islands):
        chosen = islands == island
        area3 = triangle_areas(points[triangles[chosen]]).sum()
        flat = triangle_areas(numpy.concatenate([uv[chosen], numpy.zeros((chosen.sum(), 3, 1))], axis=2))
        area2 = flat.sum()
        scale = math.sqrt(area3 / max(area2, 1e-12)) * factors.get(part_names[labels[chosen][0]], 1.0)
        center = uv[chosen].reshape(-1, 2).mean(axis=0)
        uv[chosen] = (uv[chosen] - center) * scale + center
        print("UV island", part_names[labels[chosen][0]], "sub", int(sub[chosen][0]), "triangles", int(chosen.sum()), "area3", round(float(area3), 4), "collapsed", int((flat < 1e-12).sum()))
    mesh.uv_layers["UVMap"].data.foreach_set("uv", uv.astype(numpy.float32).ravel())
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, rotate_method='ANY', scale=True, margin_method='SCALED', margin=0.0025, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.uv_layers["UVMap"].data.foreach_get("uv", loops)
    uv = loops.reshape(len(triangles), 3, 2).astype(numpy.float64)
    result = final["head_uv"].astype(numpy.float64).copy()
    result[body_faces] = uv
    flat = triangle_areas(numpy.concatenate([uv, numpy.zeros((len(uv), 3, 1))], axis=2))
    stretch = flat / numpy.maximum(triangle_areas(points[triangles]), 1e-12)
    squeezed = stretch < numpy.median(stretch) * 0.05
    print("UV squeezed triangles", int(squeezed.sum()))
    coverage = flat.sum()
    numpy.savez(os.path.join(cache, "uv.npz"), uv=result.astype(numpy.float32), material=material.astype(numpy.int32), parts=labels.astype(numpy.int32))
    print("UV islands", len(numpy.unique(islands)), "body faces", len(triangles), "head faces", int((material == 1).sum()), "body coverage", round(float(coverage), 3))


def absorb_small(combined, pairs, triangles, minimum):
    combined = combined.copy()
    for iteration in range(6):
        islands = island_ids(triangles, pairs, combined[pairs[:, 0]] != combined[pairs[:, 1]])
        sizes = numpy.bincount(islands, minlength=len(triangles))
        small = sizes[islands] < minimum
        if not small.any():
            break
        votes = numpy.zeros((len(triangles), combined.max() + 1), dtype=numpy.int32)
        crossing = islands[pairs[:, 0]] != islands[pairs[:, 1]]
        numpy.add.at(votes, (pairs[crossing, 0], combined[pairs[crossing, 1]]), 1)
        numpy.add.at(votes, (pairs[crossing, 1], combined[pairs[crossing, 0]]), 1)
        for island in numpy.unique(islands[small]):
            faces = numpy.flatnonzero(islands == island)
            tally = votes[faces].sum(axis=0)
            if tally.sum() > 0:
                combined[faces] = int(numpy.argmax(tally))
    return combined


def triangle_areas(corners):
    return 0.5 * numpy.linalg.norm(numpy.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]), axis=1)


def island_ids(triangles, pairs, seam):
    parent = numpy.arange(len(triangles))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs[~seam]:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[ra] = rb
    return numpy.array([find(i) for i in range(len(triangles))])


palettes = {
    "male": {"base": (0.505, 0.282, 0.182), "red": (0.56, 0.22, 0.16), "palm": (0.6, 0.38, 0.28), "nail": (0.64, 0.37, 0.33), "lunula": (0.74, 0.58, 0.54), "edge": (0.76, 0.69, 0.6), "roughness": 0.62, "hair": 1.0, "freckles": 0.8, "moles": 1.0, "veins": 1.0, "variation": 1.25, "sun": 1.0, "dirt": 0.22, "grit": 0.35, "tan": (0.93, 0.915, 0.9), "areola": (0.6, 0.47, 0.46), "nipple": (0.86, 0.78, 0.78)},
    "female": {"base": (0.52, 0.292, 0.19), "red": (0.58, 0.24, 0.18), "palm": (0.62, 0.4, 0.3), "nail": (0.66, 0.39, 0.35), "lunula": (0.76, 0.6, 0.56), "edge": (0.78, 0.71, 0.62), "roughness": 0.6, "freckles": 0.95, "moles": 0.85, "veins": 0.8, "variation": 1.45, "sun": 0.9, "dirt": 0.14, "grit": 0.2, "tan": (1.0, 0.985, 0.97), "areola": (0.74, 0.55, 0.55), "nipple": (0.88, 0.8, 0.8)},
}


def pixels_of(image):
    data = numpy.empty(image.size[0] * image.size[1] * 4, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    return data.reshape(image.size[1], image.size[0], 4)


def output_directory(setup):
    directory = os.path.join(roots["output"], characters[setup["name"]]["folder"])
    os.makedirs(directory, exist_ok=True)
    return directory


def final_object(cache, name="final"):
    final = numpy.load(os.path.join(cache, "final.npz"))
    uvdata = numpy.load(os.path.join(cache, "uv.npz"))
    obj = mesh_object(name, final["points"], numpy.zeros((0, 4), dtype=numpy.int32), final["triangles"])
    layer = obj.data.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", uvdata["uv"].astype(numpy.float32).ravel())
    for key in ("body", "head"):
        material = bpy.data.materials.new(key)
        material.use_nodes = True
        obj.data.materials.append(material)
    obj.data.polygons.foreach_set("material_index", final["material"].astype(numpy.int32))
    return obj, final, uvdata


def bake_occlusion(obj, size, samples=64, distance=0.12):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    turntable.accelerate(scene)
    scene.cycles.samples = samples
    if scene.world is None:
        scene.world = bpy.data.worlds.new("occlusion")
    scene.world.light_settings.distance = distance
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.margin = 16
    scene.render.bake.margin_type = 'EXTEND'
    images = {}
    for material in obj.data.materials:
        image = bpy.data.images.new(material.name + "_ao", size, size, alpha=False, float_buffer=True)
        image.colorspace_settings.name = 'Non-Color'
        node = material.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        material.node_tree.nodes.active = node
        images[material.name] = image
    select([obj], obj)
    started = time.time()
    bpy.ops.object.bake(type='AO', margin=16)
    print("BAKED occlusion", size, round(time.time() - started, 1), "s")
    return {key: pixels_of(image)[:, :, 0].copy() for key, image in images.items()}


def skin_base(setup, head_page, directory, prefix):
    point, normal = neck_frame(setup)
    albedo = headtex.load_image(os.path.join(directory, prefix + "_head_albedo.png"), 'sRGB')[:, :, :3]
    colors = texels.to_linear(head_page.sample(albedo))
    positions = head_page.position.astype(numpy.float64)
    height = (positions - point) @ normal
    head_now, scale = setup["placement"]
    near = (height > 0.03 * scale) & (height < 0.065 * scale) & (positions[:, 1] - head_now[1] < 0.03 * scale)
    cheeks = headtex.soft((positions - head_now) / scale, (0.047, -0.092, 0.06), (0.026, 0.03, 0.026), True) > 0.5
    base = numpy.median(colors[near], axis=0) * 0.3 + numpy.median(colors[cheeks], axis=0) * 0.7
    print("SKIN base color", texels.to_srgb(base).round(3), "neck", texels.to_srgb(numpy.median(colors[near], axis=0)).round(3), "cheek", texels.to_srgb(numpy.median(colors[cheeks], axis=0)).round(3))
    return base


def stage_bake(setup, cache, size=4096):
    name = setup["name"]
    folder = characters[name]["folder"]
    directory = output_directory(setup)
    obj, final, uvdata = final_object(cache)
    eyes = faces.eye_object({"eyes": final["eyes"], "eye_radius": float(final["eye_radius"][0])}, "eyes_occluder")
    occlusion = bake_occlusion(obj, size // 2)
    occlusion = {key: numpy.clip(texels.upscale(value[:, :, None], 2)[:, :, 0], 0.0, 1.0) for key, value in occlusion.items()}
    bpy.data.objects.remove(eyes, do_unlink=True)
    triangles = final["triangles"].astype(numpy.int64)
    material = final["material"]
    points = final["points"].astype(numpy.float64)
    head_faces = numpy.flatnonzero(material == 1)
    head_data = {"points": points, "sizes": numpy.full(len(head_faces), 3, dtype=numpy.int32), "corners": triangles[head_faces].ravel(), "uv": uvdata["uv"][head_faces].reshape(-1, 2).astype(numpy.float64)}
    head_now, scale = setup["placement"]
    head_page = headtex.head_maps(roots["rocketbox"], name, head_data, head_now, scale, directory, folder, size, occlusion["head"], neck=neck_frame(setup))
    base = skin_base(setup, head_page, directory, folder)
    head_mask = head_page.mask
    del head_page
    palette = dict(palettes[name])
    base = base * numpy.asarray(palette.get("tan", (1.0, 1.0, 1.0)))
    ratio = base / numpy.asarray(palettes[name]["base"])
    palette["base"] = tuple(base)
    for key in ("red", "palm"):
        palette[key] = tuple(numpy.asarray(palette[key]) * (0.25 + 0.75 * ratio))
    palette["edge"] = tuple(numpy.asarray(palette["edge"]) * (0.55 + 0.45 * ratio))
    for key, factor in (("nail", (1.2, 1.0, 1.06)), ("lunula", (1.42, 1.38, 1.44))):
        palette[key] = tuple(numpy.clip(base * numpy.asarray(factor), 0.0, 1.0))
    shapes = bodies.build(setup["skeleton"], setup["figure"], setup["head"])
    tangent, sign, normal = bodytex.corner_frames(obj)
    body_faces = numpy.flatnonzero(material == 0)
    if options.get("part") != "head":
        bodytex.body_maps(setup, shapes, (tangent[body_faces], sign[body_faces], normal[body_faces]), uvdata["uv"][body_faces].astype(numpy.float64), points[triangles[body_faces]], triangles[body_faces], occlusion["body"], palette, directory, folder, size)
    bodytex.collar_maps(setup, shapes, (tangent[head_faces], sign[head_faces], normal[head_faces]), uvdata["uv"][head_faces].astype(numpy.float64), points[triangles[head_faces]], triangles[head_faces], occlusion["head"], palette, head_mask, neck_frame(setup), directory, folder, size)
    eyetex.eye_maps(faces.specs[name]["iris"], directory, folder, 1024)


def gltf_group():
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
        group.interface.new_socket(name="Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
        group.interface.new_socket(name="Thickness", in_out='INPUT', socket_type='NodeSocketFloat')
    return group


def export_material(name, albedo, orm=None, normal=None, alpha=None, roughness=0.5, double=False):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.use_backface_culling = not double
    tree = material.node_tree
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = albedo
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    if alpha:
        cutoff = tree.nodes.new('ShaderNodeMath')
        cutoff.operation = 'ROUND'
        tree.links.new(color.outputs['Alpha'], cutoff.inputs[0])
        tree.links.new(cutoff.outputs[0], shader.inputs['Alpha'])
        material.surface_render_method = 'DITHERED'
    shader.inputs['Metallic'].default_value = 0.0
    shader.inputs['Roughness'].default_value = roughness
    if orm is not None:
        packed = tree.nodes.new('ShaderNodeTexImage')
        packed.image = orm
        split = tree.nodes.new('ShaderNodeSeparateColor')
        tree.links.new(packed.outputs['Color'], split.inputs['Color'])
        tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
        tree.links.new(split.outputs['Blue'], shader.inputs['Metallic'])
        settings = tree.nodes.new('ShaderNodeGroup')
        settings.node_tree = gltf_group()
        tree.links.new(split.outputs['Red'], settings.inputs['Occlusion'])
    if normal is not None:
        bumps = tree.nodes.new('ShaderNodeTexImage')
        bumps.image = normal
        mapping = tree.nodes.new('ShaderNodeNormalMap')
        tree.links.new(bumps.outputs['Color'], mapping.inputs['Color'])
        tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    return material


def load_png(path, colorspace):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = colorspace
    return image


def assign_weights(obj, indices, values, names):
    for name in names:
        if name not in obj.vertex_groups:
            obj.vertex_groups.new(name=name)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    deform = bm.verts.layers.deform.verify()
    group_index = {name: obj.vertex_groups[name].index for name in names}
    bm.verts.ensure_lookup_table()
    for vertex in bm.verts:
        slots = vertex[deform]
        for slot in range(indices.shape[1]):
            weight = float(values[vertex.index, slot])
            if weight > 0.0:
                slots[group_index[names[indices[vertex.index, slot]]]] = weight
    bm.to_mesh(obj.data)
    bm.free()


def limit_weights(obj, count=4):
    for vertex in obj.data.vertices:
        entries = sorted(((g.weight, g.group) for g in vertex.groups), reverse=True)
        total = sum(weight for weight, group in entries[:count])
        for index, (weight, group) in enumerate(entries):
            if index >= count or total <= 0.0:
                obj.vertex_groups[group].remove([vertex.index])
            else:
                obj.vertex_groups[group].add([vertex.index], weight / total, 'REPLACE')


def material_maps(directory, prefix, key):
    maps = []
    for suffix, space in (("albedo", 'sRGB'), ("orm", 'Non-Color'), ("nor_gl", 'Non-Color')):
        path = os.path.join(directory, "%s_%s_%s.png" % (prefix, key, suffix))
        maps.append(load_png(path, space) if os.path.exists(path) else None)
    return maps


def save_part(cache, order, key, points, triangles, uv, indices, values, double=True, alpha=True, separate=False, maps=None):
    directory = os.path.join(cache, "parts")
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "%02d_%s.npz" % (order, key))
    if not len(triangles):
        if os.path.exists(path):
            os.remove(path)
        return
    numpy.savez(path, points=numpy.asarray(points, dtype=numpy.float32), triangles=numpy.asarray(triangles, dtype=numpy.int32), uv=numpy.asarray(uv, dtype=numpy.float32), indices=numpy.asarray(indices, dtype=numpy.int32), values=numpy.asarray(values, dtype=numpy.float32), material=numpy.array(key), double=numpy.array(double), alpha=numpy.array(alpha), separate=numpy.array(separate), maps=numpy.array(maps or key))


def part_objects(cache, directory, prefix, names):
    folder = os.path.join(cache, "parts")
    joined = []
    separate = []
    materials = {}
    if not os.path.isdir(folder):
        return joined, separate
    for entry in sorted(os.listdir(folder)):
        if not entry.endswith(".npz"):
            continue
        data = numpy.load(os.path.join(folder, entry))
        key = str(data["material"])
        obj = mesh_object(entry[:-4], data["points"], numpy.zeros((0, 4), dtype=numpy.int32), data["triangles"])
        layer = obj.data.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", data["uv"].astype(numpy.float32).ravel())
        assign_weights(obj, data["indices"], data["values"], names)
        if key not in materials:
            albedo, orm, normal = material_maps(directory, prefix, str(data["maps"]) if "maps" in data else key)
            materials[key] = export_material(prefix + "_" + key, albedo, orm, normal, alpha=bool(data["alpha"]), roughness=0.6, double=bool(data["double"]))
        obj.data.materials.append(materials[key])
        (separate if bool(data["separate"]) else joined).append(obj)
    return joined, separate


def stage_groom(setup, cache):
    name = setup["name"]
    folder = characters[name]["folder"]
    directory = output_directory(setup)
    final = numpy.load(os.path.join(cache, "final.npz"))
    names = [str(n) for n in final["names"]]
    points = final["points"].astype(numpy.float64)
    triangles = final["triangles"].astype(numpy.int64)
    material = final["material"]
    head_now, scale = setup["placement"]
    space = grooming.head_space(points, triangles[material == 1], head_now, scale, name, triangles)
    rng = numpy.random.default_rng(7 if name == "male" else 11)
    grooming.hair_atlas(name, directory, folder)
    grooming.lash_atlas(name, directory, folder)
    stored = (final["indices"], final["values"])
    hair = grooming.cards()
    if name == "female":
        grooming.female_hair(hair, space, rng)
    else:
        grooming.male_hair(hair, space, rng)
        print("GROOM stubble shell triangles", grooming.stubble_shell(hair, space, stored, names))
    scalp_triangles = len(hair.triangles)
    body = grooming.surface(points, triangles[material == 0])
    fur = grooming.cards()
    shapes = bodies.build(setup["skeleton"], setup["figure"], None)
    bare = (lambda centers: bodies.protrusion(shapes, centers) > 0.003) if "shaft" in setup["figure"].get("groin", {}) else None
    grooming.body_hair(fur, body, grooming.nearest_weights(body, stored, names), setup["skeleton"], setup["figure"]["scale"], name, rng, bare)
    fur_arrays = fur.arrays(names)
    hidden = garments.edge_distance(fur_arrays[0][fur_arrays[1]].mean(axis=1), setup) > -0.006 if len(fur_arrays[1]) else numpy.zeros(0, dtype=bool)
    save_part(cache, 10, "hair", *grooming.merged(hair.arrays(names), grooming.subset(fur_arrays, ~hidden)))
    save_part(cache, 12, "pubic_hair", *grooming.subset(fur_arrays, hidden), maps="hair")
    face = grooming.cards()
    lookup = grooming.nearest_weights(space.skin, stored, names)
    line = None
    albedo_path = os.path.join(directory, folder + "_head_albedo.png")
    if name == "male" and os.path.exists(albedo_path):
        uvdata = numpy.load(os.path.join(cache, "uv.npz"))
        line = grooming.detect_brows(space, uvdata["uv"][material == 1].astype(numpy.float64), headtex.load_image(albedo_path, 'sRGB'), grooming.brow_lines[name])
    grooming.brows(face, space, lookup, rng, line)
    grooming.lashes(face, space, final["eyes"], float(final["eye_radius"][0]), lookup, rng)
    save_part(cache, 11, "lashes", *face.arrays(names))
    print("GROOM", name, "scalp triangles", scalp_triangles, "body hair triangles", len(fur.triangles), "of which under the underwear", int(hidden.sum()), "lashes and brows", len(face.triangles))


def stage_garments(setup, cache, size=2048):
    name = setup["name"]
    folder = characters[name]["folder"]
    directory = output_directory(setup)
    final = numpy.load(os.path.join(cache, "final.npz"))
    uvdata = numpy.load(os.path.join(cache, "uv.npz"))
    names = [str(n) for n in final["names"]]
    points = final["points"].astype(numpy.float64)
    triangles = final["triangles"].astype(numpy.int64)
    body_faces = numpy.flatnonzero(final["material"] == 0)
    shapes = bodies.build(setup["skeleton"], setup["figure"], None)
    lifted, faces_, face_uv, weights, covered = garments.build(setup, shapes, points, triangles[body_faces], uvdata["uv"][body_faces].astype(numpy.float64), final["indices"], final["values"], names)
    obj = mesh_object("underwear", lifted, numpy.zeros((0, 4), dtype=numpy.int32), faces_)
    if len(obj.data.polygons) != len(faces_):
        raise RuntimeError("garment faces changed during validation")
    layer = obj.data.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", face_uv.astype(numpy.float32).ravel())
    select([obj], obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, rotate_method='ANY', scale=True, margin_method='SCALED', margin=0.004, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    loops = numpy.empty(len(obj.data.loops) * 2, dtype=numpy.float32)
    obj.data.uv_layers["UVMap"].data.foreach_get("uv", loops)
    uv = loops.reshape(len(faces_), 3, 2).astype(numpy.float64)
    tangent, sign, normal = bodytex.corner_frames(obj)
    page = bodytex.sheet(uv, lifted[faces_], (tangent, sign, normal), size, faces_)
    garments.fabric_maps(setup, page, directory, folder)
    save_part(cache, 20, "underwear", lifted, faces_, uv, weights[0], weights[1], double=False, alpha=False, separate=True)
    numpy.save(os.path.join(cache, "covered.npy"), covered)
    print("GARMENTS", name, "triangles", len(faces_), "uv coverage", round(float(triangle_areas(numpy.concatenate([uv, numpy.zeros((len(uv), 3, 1))], axis=2)).sum()), 3))


def stage_export(setup, cache):
    name = setup["name"]
    folder = characters[name]["folder"]
    directory = output_directory(setup)
    body, final, uvdata = final_object(cache, folder)
    names = [str(n) for n in final["names"]]
    assign_weights(body, final["indices"], final["values"], names)
    for index, key in enumerate(("body", "head")):
        body.data.materials[index] = export_material(folder + "_" + key, *material_maps(directory, folder, key))
    covered_path = os.path.join(cache, "covered.npy")
    if os.path.exists(covered_path):
        covered = numpy.load(covered_path)
        slots = final["material"].astype(numpy.int32).copy()
        body_faces = numpy.flatnonzero(slots == 0)
        if len(covered) == len(body_faces) and covered.any():
            slots[body_faces[covered]] = 2
            body.data.materials.append(export_material(folder + "_covered_body", *material_maps(directory, folder, "body")))
            body.data.polygons.foreach_set("material_index", slots)
    eyes = faces.eye_object({"eyes": final["eyes"], "eye_radius": float(final["eye_radius"][0])}, "eyes")
    eyes.data.materials.append(export_material(folder + "_eye", *material_maps(directory, folder, "eye"), roughness=0.06))
    joined, separate = part_objects(cache, directory, folder, names)
    parts = [body, eyes] + joined
    select(parts, body)
    bpy.ops.object.join()
    armature = setup["armature"]
    exported = [body] + separate
    for obj in exported:
        while len(obj.data.uv_layers) > 1:
            obj.data.uv_layers.remove(obj.data.uv_layers[-1])
        limit_weights(obj)
        obj.parent = armature
        obj.matrix_parent_inverse = armature.matrix_world.inverted()
        modifier = obj.modifiers.new(armature.name, 'ARMATURE')
        modifier.object = armature
    for index, obj in enumerate(separate):
        obj.name = "%s_%s" % (folder, obj.data.materials[0].name.split("_")[-1])
    for obj in list(bpy.data.objects):
        if obj.type == 'MESH' and obj not in exported:
            bpy.data.objects.remove(obj, do_unlink=True)
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)
    bpy.ops.export_scene.gltf(filepath=os.path.join(directory, folder + ".gltf"), export_format='GLTF_SEPARATE', export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT', export_skins=True, export_animations=False, export_force_sampling=False, export_optimize_animation_size=False, export_anim_single_armature=True, export_morph=False, export_yup=True, export_apply=False, use_selection=False, export_extras=False, export_cameras=False, export_lights=False)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(directory, folder + ".blend"))
    for obj in exported:
        counts = {}
        indices = numpy.empty(len(obj.data.polygons), dtype=numpy.int32)
        obj.data.polygons.foreach_get("material_index", indices)
        sizes = numpy.empty(len(obj.data.polygons), dtype=numpy.int32)
        obj.data.polygons.foreach_get("loop_total", sizes)
        for slot, material in enumerate(obj.data.materials):
            counts[material.name] = int((sizes[indices == slot] - 2).sum())
        print("EXPORTED", obj.name, "vertices", len(obj.data.vertices), "triangles", counts)


component_types = {5126: numpy.float32, 5125: numpy.uint32, 5123: numpy.uint16, 5121: numpy.uint8, 5122: numpy.int16, 5120: numpy.int8}
component_counts = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_gltf(path):
    import json
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    buffers = []
    for entry in document["buffers"]:
        with open(os.path.join(os.path.dirname(path), entry["uri"]), "rb") as handle:
            buffers.append(handle.read())

    def accessor(index):
        item = document["accessors"][index]
        view = document["bufferViews"][item["bufferView"]]
        dtype = numpy.dtype(component_types[item["componentType"]])
        components = component_counts[item["type"]]
        offset = view.get("byteOffset", 0) + item.get("byteOffset", 0)
        stride = view.get("byteStride", dtype.itemsize * components)
        raw = numpy.frombuffer(buffers[view["buffer"]], dtype=numpy.uint8, count=stride * (item["count"] - 1) + dtype.itemsize * components, offset=offset)
        rows = numpy.lib.stride_tricks.as_strided(raw, shape=(item["count"], dtype.itemsize * components), strides=(stride, 1))
        values = numpy.ascontiguousarray(rows).view(dtype).reshape(item["count"], components).astype(numpy.float64)
        if item.get("normalized"):
            values /= float(numpy.iinfo(dtype).max)
        return values

    document["accessor"] = accessor
    return document


def quaternion_matrix(q):
    x, y, z, w = q
    return numpy.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def compose(t, r, s):
    matrix = numpy.eye(4)
    matrix[:3, :3] = quaternion_matrix(r) * numpy.asarray(s)[None, :]
    matrix[:3, 3] = t
    return matrix


def node_trs(node):
    return numpy.array(node.get("translation", [0.0, 0.0, 0.0])), numpy.array(node.get("rotation", [0.0, 0.0, 0.0, 1.0])), numpy.array(node.get("scale", [1.0, 1.0, 1.0]))


def clip_sampler(path):
    document = read_gltf(path)
    animation = document["animations"][0]
    tracks = {}
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        name = document["nodes"][channel["target"]["node"]]["name"]
        tracks.setdefault(name, {})[channel["target"]["path"]] = (document["accessor"](sampler["input"])[:, 0], document["accessor"](sampler["output"]))
    duration = max(times[-1] for track in tracks.values() for times, values in track.values())

    def sample(name, path, time):
        track = tracks.get(name, {}).get(path)
        if track is None:
            return None
        times, values = track
        index = int(numpy.clip(numpy.searchsorted(times, time) - 1, 0, len(times) - 2))
        fraction = float(numpy.clip((time - times[index]) / max(times[index + 1] - times[index], 1e-6), 0.0, 1.0))
        a = values[index]
        b = values[index + 1]
        if path == "rotation":
            if numpy.dot(a, b) < 0.0:
                b = -b
            q = a + (b - a) * fraction
            return q / numpy.linalg.norm(q)
        return a + (b - a) * fraction

    return sample, duration


posed_joints = {}


def axis_rotation(axis, degrees):
    return anatomy.rotation(numpy.asarray(axis, dtype=numpy.float64), degrees)


def skinned_mesh(document, sample=None, time=0.0, rotation_only=False, root_height=1.0, adjust=None, skip=()):
    nodes = document["nodes"]
    parents = {}
    for index, node in enumerate(nodes):
        for child in node.get("children", []):
            parents[child] = index
    locals_ = []
    for index, node in enumerate(nodes):
        t, r, s = node_trs(node)
        if sample is not None:
            rotation = sample(node.get("name", ""), "rotation", time)
            translation = sample(node.get("name", ""), "translation", time)
            if rotation is not None:
                r = rotation
            if translation is not None:
                if node.get("name") == "Bip01":
                    t = numpy.array([0.0, translation[1] * root_height, 0.0])
                elif not rotation_only:
                    t = translation
        locals_.append(compose(t, r, s))
    globals_ = [None] * len(nodes)

    def world(index):
        if globals_[index] is None:
            local = locals_[index]
            above = numpy.eye(4) if index not in parents else world(parents[index])
            name = nodes[index].get("name", "")
            if adjust and name in adjust:
                turn = above[:3, :3]
                local = local.copy()
                local[:3, :3] = numpy.linalg.inv(turn) @ adjust[name] @ turn @ local[:3, :3]
            globals_[index] = above @ local
        return globals_[index]

    binding = document["skins"][0]
    inverse = document["accessor"](binding["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    palette = numpy.array([world(joint) @ inverse[index] for index, joint in enumerate(binding["joints"])])
    posed_joints.clear()
    for joint in binding["joints"]:
        place = world(joint)[:3, 3]
        posed_joints[nodes[joint].get("name", "")] = numpy.array([place[0], -place[2], place[1]])
    primitives = []
    names = [entry["name"] for entry in document["materials"]]
    for node in nodes:
        if "mesh" not in node:
            continue
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            if any(names[primitive.get("material", 0)].endswith(suffix) for suffix in skip):
                continue
            attributes = primitive["attributes"]
            positions = document["accessor"](attributes["POSITION"])
            normals = document["accessor"](attributes["NORMAL"])
            joints = document["accessor"](attributes["JOINTS_0"]).astype(numpy.int64)
            weights = document["accessor"](attributes["WEIGHTS_0"])
            weights = weights / numpy.maximum(weights.sum(axis=1), 1e-9)[:, None]
            blended = numpy.einsum('nk,nkij->nij', weights, palette[joints])
            posed = numpy.einsum('nij,nj->ni', blended[:, :3, :3], positions) + blended[:, :3, 3]
            turned = numpy.einsum('nij,nj->ni', blended[:, :3, :3], normals)
            turned /= numpy.maximum(numpy.linalg.norm(turned, axis=1), 1e-9)[:, None]
            uvs = document["accessor"](attributes["TEXCOORD_0"])
            indices = document["accessor"](primitive["indices"]).astype(numpy.int64).reshape(-1, 3)
            primitives.append((posed, turned, uvs, indices, primitive.get("material", 0)))
    return primitives


def gltf_to_blender(points):
    return numpy.stack([points[:, 0], -points[:, 2], points[:, 1]], axis=1)


def posed_object(name, primitives, materials, offset=(0.0, 0.0, 0.0)):
    all_points = []
    all_uv = []
    all_faces = []
    all_normals = []
    material_index = []
    base = 0
    for posed, normals, uvs, indices, material in primitives:
        all_points.append(gltf_to_blender(posed) + numpy.asarray(offset))
        all_normals.append(gltf_to_blender(normals))
        all_uv.append(uvs)
        all_faces.append(indices + base)
        material_index.append(numpy.full(len(indices), material))
        base += len(posed)
    points = numpy.concatenate(all_points)
    faces = numpy.concatenate(all_faces)
    obj = mesh_object(name, points, numpy.zeros((0, 4), dtype=numpy.int32), faces)
    mesh = obj.data
    uv = numpy.concatenate(all_uv)
    uv[:, 1] = 1.0 - uv[:, 1]
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", uv[faces.ravel()].astype(numpy.float32).ravel())
    for material in materials:
        mesh.materials.append(material)
    mesh.polygons.foreach_set("material_index", numpy.concatenate(material_index).astype(numpy.int32))
    normals = numpy.concatenate(all_normals)
    mesh.normals_split_custom_set_from_vertices(normals.astype(numpy.float32).tolist())
    return obj


def preview_materials(path):
    before = set(bpy.data.materials)
    bpy.ops.import_scene.gltf(filepath=path)
    imported = [obj for obj in bpy.context.scene.objects if obj.select_get()]
    document = read_gltf(path)
    names = [entry["name"] for entry in document["materials"]]
    materials = [bpy.data.materials[name] for name in names]
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    for material in materials:
        tree = material.node_tree
        shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
        if material.name.endswith("_body") or material.name.endswith("_head"):
            shader.inputs['Subsurface Weight'].default_value = 0.1
            shader.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2)
            shader.inputs['Subsurface Scale'].default_value = 0.004
            shader.inputs['Specular IOR Level'].default_value = 0.35
        if material.name.endswith("_hair") or material.name.endswith("_lashes"):
            shader.inputs['Specular IOR Level'].default_value = 0.12
            output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
            glow = tree.nodes.new('ShaderNodeBsdfTranslucent')
            if shader.inputs['Base Color'].links:
                tree.links.new(shader.inputs['Base Color'].links[0].from_socket, glow.inputs['Color'])
            clear = tree.nodes.new('ShaderNodeBsdfTransparent')
            body_mix = tree.nodes.new('ShaderNodeMixShader')
            body_mix.inputs[0].default_value = 0.35
            cut_mix = tree.nodes.new('ShaderNodeMixShader')
            cut_mix.inputs[0].default_value = 1.0
            if shader.inputs['Alpha'].links:
                source = shader.inputs['Alpha'].links[0].from_socket
                tree.links.remove(shader.inputs['Alpha'].links[0])
                crisp = tree.nodes.new('ShaderNodeMapRange')
                crisp.inputs['From Min'].default_value = 0.35
                crisp.inputs['From Max'].default_value = 0.65
                tree.links.new(source, crisp.inputs['Value'])
                tree.links.new(crisp.outputs['Result'], cut_mix.inputs[0])
            shader.inputs['Alpha'].default_value = 1.0
            tree.links.new(shader.outputs['BSDF'], body_mix.inputs[1])
            tree.links.new(glow.outputs['BSDF'], body_mix.inputs[2])
            tree.links.new(clear.outputs['BSDF'], cut_mix.inputs[1])
            tree.links.new(body_mix.outputs['Shader'], cut_mix.inputs[2])
            tree.links.new(cut_mix.outputs['Shader'], output.inputs['Surface'])
    return document, materials


def hdri_path():
    return os.path.join(os.path.dirname(os.path.dirname(roots["rocketbox"])), "raw", "hdri", "kloofendal_overcast_puresky_4k.hdr")


def stage_lights(scene, mode):
    for obj in [o for o in scene.objects if o.get("stage")]:
        bpy.data.objects.remove(obj, do_unlink=True)
    world = bpy.data.worlds.new("stage_" + mode)
    world.use_nodes = True
    tree = world.node_tree
    output = tree.nodes["World Output"]
    background = tree.nodes["Background"]
    environment = tree.nodes.new('ShaderNodeTexEnvironment')
    environment.image = bpy.data.images.load(hdri_path(), check_existing=True)
    tree.links.new(environment.outputs['Color'], background.inputs['Color'])
    plain = tree.nodes.new('ShaderNodeBackground')
    path = tree.nodes.new('ShaderNodeLightPath')
    mixer = tree.nodes.new('ShaderNodeMixShader')
    tree.links.new(path.outputs['Is Camera Ray'], mixer.inputs['Fac'])
    tree.links.new(background.outputs['Background'], mixer.inputs[1])
    tree.links.new(plain.outputs['Background'], mixer.inputs[2])
    tree.links.new(mixer.outputs['Shader'], output.inputs['Surface'])
    scene.world = world
    created = []
    if mode == "studio":
        background.inputs['Strength'].default_value = 0.3
        plain.inputs['Color'].default_value = (0.22, 0.22, 0.225, 1.0)
        plain.inputs['Strength'].default_value = 1.0
        specs = (("key", (-2.0, -2.8, 2.7), 520.0, 2.0, (1.0, 0.97, 0.93)), ("fill", (2.4, -2.4, 1.3), 120.0, 2.4, (0.95, 0.97, 1.0)), ("rim", (1.6, 2.6, 2.5), 330.0, 1.4, (0.9, 0.94, 1.0)), ("kick", (-2.4, 2.0, 1.2), 90.0, 1.6, (1.0, 0.98, 0.95)))
        scene.view_settings.exposure = -0.45
        for name, location, energy, size, color in specs:
            data = bpy.data.lights.new(name, 'AREA')
            data.energy = energy
            data.size = size
            data.color = color
            light = bpy.data.objects.new(name, data)
            light.location = Vector(location)
            light.rotation_euler = (Vector((0.0, 0.0, 1.0)) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
            scene.collection.objects.link(light)
            created.append(light)
        floor_color = (0.2, 0.2, 0.205, 1.0)
    else:
        background.inputs['Strength'].default_value = 1.15
        plain.inputs['Color'].default_value = (0.5, 0.54, 0.6, 1.0)
        plain.inputs['Strength'].default_value = 1.0
        floor_color = (0.16, 0.15, 0.13, 1.0)
        scene.view_settings.exposure = 0.0
    floor_data = bpy.data.meshes.new("floor")
    floor_data.from_pydata([(-30.0, -30.0, 0.0), (30.0, -30.0, 0.0), (30.0, 30.0, 0.0), (-30.0, 30.0, 0.0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("floor", floor_data)
    material = bpy.data.materials.new("floor_" + mode)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = floor_color
    shader.inputs['Roughness'].default_value = 0.85
    floor_data.materials.append(material)
    scene.collection.objects.link(floor)
    created.append(floor)
    for obj in created:
        obj["stage"] = True


def close_light(scene, target, direction, distance):
    data = bpy.data.lights.new("close", 'AREA')
    data.energy = 7.0 * distance * distance
    data.size = distance * 0.8
    data.color = (1.0, 0.98, 0.95)
    light = bpy.data.objects.new("close", data)
    offset = Vector(direction).normalized() * distance + Vector((-distance * 0.35, 0.0, distance * 0.45))
    light.location = Vector(target) + offset
    light.rotation_euler = (-offset).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(light)
    return light


def preview_views(setup):
    name = setup["name"]
    skeleton = setup["skeleton"]
    joints = skeleton["joints"]
    head = joints["Bip01 Head"]
    height = head[2] + 0.22
    middle = (0.0, 0.0, height * 0.5)
    tall = (900, 1500)
    square = (1100, 1100)
    views = []

    def add(label, target, direction, distance, lens=50.0, ortho=0.0, resolution=tall, mode="studio", pose="rest", variant="nude", anchor=None):
        views.append({"label": label, "target": tuple(target), "direction": tuple(direction), "distance": distance, "lens": lens, "ortho": ortho, "resolution": resolution, "mode": mode, "pose": pose, "variant": variant, "anchor": anchor})

    add("full_front", middle, (0.0, -1.0, 0.02), 5.5, ortho=height * 1.12)
    add("full_back", middle, (0.0, 1.0, 0.02), 5.5, ortho=height * 1.12)
    add("full_left", middle, (1.0, 0.0, 0.02), 5.5, ortho=height * 1.12)
    add("full_three", middle, (0.75, -1.0, 0.12), 4.6)
    face = head + numpy.array([0.0, -0.06, 0.07]) * setup["placement"][1]
    add("face_front", face, (0.0, -1.0, 0.0), 0.75, 85.0, resolution=square)
    add("face_three", face, (0.8, -1.0, 0.05), 0.75, 85.0, resolution=square)
    eye = head + numpy.array([0.032, -0.1, 0.099]) * setup["placement"][1]
    add("eye_close", eye, (0.25, -1.0, 0.04), 0.2, 105.0, resolution=(1200, 800))
    wrist = joints["Bip01 L Hand"]
    axes = skeleton["axes"]["Bip01 L Hand"]
    center = wrist + axes[0] * 0.075
    add("hand_back", center, -axes[1] - axes[2] * 0.25, 0.42, 60.0, resolution=square)
    add("hand_palm", center, axes[1] - axes[2] * 0.35 - axes[0] * 0.15, 0.42, 60.0, resolution=square)
    ankle = joints["Bip01 L Foot"]
    add("feet", (0.0, ankle[1] - 0.05, 0.05), (0.35, -1.0, 0.75), 0.85, 60.0, resolution=square)
    add("foot_side", (ankle[0], ankle[1] - 0.05, 0.04), (1.0, -0.15, 0.12), 0.55, 60.0, resolution=square)
    chest = joints["Bip01 Spine2"] + numpy.array([0.0, -0.06, 0.05])
    add("torso_front", chest, (0.12, -1.0, 0.04), 1.35, 70.0, resolution=square)
    add("torso_side", chest, (1.0, -0.35, 0.04), 1.35, 70.0, resolution=square)
    add("torso_back", joints["Bip01 Spine2"] + numpy.array([0.0, 0.06, 0.0]), (-0.2, 1.0, 0.08), 1.6, 70.0, resolution=square)
    crown = head + numpy.array([0.0, 0.0, 0.1]) * setup["placement"][1]
    add("hair_back", crown, (0.25, 1.0, 0.12), 0.9, 85.0, resolution=square)
    add("hair_side", crown, (1.0, 0.12, 0.08), 0.9, 85.0, resolution=square)
    add("hair_top", crown, (0.45, -0.75, 0.75), 0.85, 85.0, resolution=square)
    add("hair_front", head + numpy.array([0.0, -0.07, 0.15]) * setup["placement"][1], (0.3, -1.0, 0.22), 0.5, 85.0, resolution=square)
    for pose in ("walk", "run", "crouch", "arms"):
        add("pose_" + pose, middle, (0.8, -1.0, 0.12), 4.6, pose=pose)
    add("pose_run_side", middle, (1.0, -0.2, 0.06), 4.6, pose="run")
    add("pose_arms_back", middle, (-0.6, 1.0, 0.15), 4.6, pose="arms")
    add("pose_arms_shoulder", joints["Bip01 L UpperArm"] + numpy.array([0.0, 0.0, 0.1]), (0.55, -1.0, 0.2), 1.3, 60.0, resolution=square, pose="arms")
    add("underwear_front", middle, (0.0, -1.0, 0.02), 5.5, ortho=height * 1.12, variant="underwear")
    add("underwear_back", middle, (0.0, 1.0, 0.02), 5.5, ortho=height * 1.12, variant="underwear")
    add("underwear_crouch", middle, (0.8, -1.0, 0.12), 4.6, pose="crouch", variant="underwear")
    add("overcast_front", middle, (0.0, -1.0, 0.02), 5.5, ortho=height * 1.12, mode="overcast")
    add("overcast_three", middle, (0.75, -1.0, 0.12), 4.6, mode="overcast")
    add("overcast_face", face, (0.8, -1.0, 0.05), 0.75, 85.0, resolution=square, mode="overcast")
    s = setup["figure"]["scale"]
    pelvis = joints["Bip01 Pelvis"]
    navel = pelvis[2] + setup["figure"]["navel"][0] * (joints["Bip01 Neck"][2] - pelvis[2])
    add("chest_close", joints["Bip01 Spine2"] + numpy.array([0.05, -0.1, -0.025]) * s, (0.4, -1.0, 0.06), 0.62, 70.0, resolution=square)
    add("navel_close", (0.0, -0.1 * s, navel), (0.25, -1.0, 0.02), 0.55, 70.0, resolution=square)
    add("back_close", joints["Bip01 Spine2"] + numpy.array([0.04, 0.1, 0.02]) * s, (-0.35, 1.0, 0.1), 0.8, 70.0, resolution=square)
    add("knee_close", joints["Bip01 L Calf"] + numpy.array([0.0, -0.04, 0.0]) * s, (0.45, -1.0, 0.08), 0.62, 70.0, resolution=square)
    front_y, front_z, back_y, back_z, power = cut_of(name, skeleton)
    collar = (0.0, (front_y + back_y) * 0.5, (front_z + back_z) * 0.5)
    add("neck_front", collar, (0.3, -1.0, -0.05), 0.62, 85.0, resolution=square)
    add("neck_side", collar, (1.0, -0.15, 0.0), 0.62, 85.0, resolution=square)
    add("neck_back", collar, (-0.35, 1.0, 0.1), 0.62, 85.0, resolution=square)
    add("overcast_neck", collar, (0.85, -1.0, 0.0), 0.62, 85.0, resolution=square, mode="overcast")
    hips = (0.0, -0.05 * s, -0.075 * s)
    add("pelvis_front", middle, (0.3, -1.0, -0.02), 0.85, 70.0, resolution=square, anchor=("Bip01 Pelvis", hips))
    add("pelvis_run", middle, (0.55, -1.0, 0.0), 0.95, 70.0, resolution=square, pose="run", anchor=("Bip01 Pelvis", hips))
    add("pelvis_crouch", middle, (0.2, -1.0, -0.12), 1.05, 70.0, resolution=square, pose="crouch", anchor=("Bip01 Pelvis", hips))
    return views


pose_clips = {"walk": ("m_walk_neutral_01", 0.35), "run": ("m_run_neutral", 0.2), "crouch": ("m_crouch_idle", 0.5)}


def pose_primitives(setup, document, pose, variant):
    skip = ("_pubic_hair", "_covered_body") if variant == "underwear" else ("_underwear",)
    rotation_only = setup["name"] == "female"
    scale = setup.get("root_scale", 1.0)
    if pose == "rest":
        return skinned_mesh(document, skip=skip)
    if pose == "arms":
        adjust = {"Bip01 L Clavicle": axis_rotation((0.0, 0.0, 1.0), 22.0), "Bip01 R Clavicle": axis_rotation((0.0, 0.0, 1.0), -22.0), "Bip01 L UpperArm": axis_rotation((0.0, 0.0, 1.0), 95.0) @ axis_rotation((0.0, 1.0, 0.0), -12.0), "Bip01 R UpperArm": axis_rotation((0.0, 0.0, 1.0), -95.0) @ axis_rotation((0.0, 1.0, 0.0), 12.0), "Bip01 L Forearm": axis_rotation((0.0, 0.0, 1.0), 25.0), "Bip01 R Forearm": axis_rotation((0.0, 0.0, 1.0), -25.0)}
        return skinned_mesh(document, adjust=adjust, skip=skip)
    clip, fraction = pose_clips[pose]
    animations = os.path.join(os.path.dirname(os.path.dirname(roots["rocketbox"])), "raw", "animations")
    sample, duration = clip_sampler(os.path.join(animations, clip + ".gltf"))
    return skinned_mesh(document, sample, duration * fraction, rotation_only, scale, skip=skip)


def stage_preview(setup, cache, only=None, samples=96):
    folder = characters[setup["name"]]["folder"]
    path = os.path.join(roots["output"], folder, folder + ".gltf")
    views = [view for view in preview_views(setup) if only is None or any(view["label"].startswith(prefix) for prefix in only)]
    reset()
    document, materials = preview_materials(path)
    if options.get("debug") == "albedo":
        for material in materials:
            tree = material.node_tree
            shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
            output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
            emission = tree.nodes.new('ShaderNodeEmission')
            if shader.inputs['Base Color'].links:
                tree.links.new(shader.inputs['Base Color'].links[0].from_socket, emission.inputs['Color'])
            tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    has_underwear = any(entry["name"].endswith("_underwear") for entry in document["materials"])
    scene = setup_render(samples, (900, 1500))
    directory = roots["previews"]
    os.makedirs(directory, exist_ok=True)
    built = {}
    anchors = {}
    current_mode = None
    for view in sorted(views, key=lambda v: (v["mode"], v["pose"], v["variant"])):
        if view["variant"] == "underwear" and not has_underwear:
            continue
        if view["mode"] != current_mode:
            stage_lights(scene, view["mode"])
            current_mode = view["mode"]
        key = (view["pose"], view["variant"])
        if key not in built:
            built[key] = posed_object("%s_%s_%s" % (folder, view["pose"], view["variant"]), pose_primitives(setup, document, view["pose"], view["variant"]), materials)
            anchors[key] = dict(posed_joints)
        for other_key, obj in built.items():
            obj.hide_render = other_key != key
        target = view["target"]
        if view["anchor"] is not None:
            target = tuple(anchors[key][view["anchor"][0]] + numpy.asarray(view["anchor"][1]))
        fill = close_light(scene, target, view["direction"], view["distance"]) if view["distance"] < 1.7 and view["mode"] == "studio" else None
        shoot(scene, os.path.join(directory, "%s_%s.png" % (folder, view["label"])), target, view["direction"], view["distance"], view["lens"], view["ortho"], view["resolution"])
        if fill is not None:
            bpy.data.objects.remove(fill)


def load_pixels(path):
    image = bpy.data.images.load(path, check_existing=False)
    data = pixels_of(image).copy()
    bpy.data.images.remove(image)
    return data


def resized(data, height):
    rows, columns = data.shape[:2]
    width = max(1, int(round(columns * height / rows)))
    image = bpy.data.images.new("resize", columns, rows, alpha=True)
    image.pixels.foreach_set(numpy.ascontiguousarray(data, dtype=numpy.float32).ravel())
    image.scale(width, height)
    result = pixels_of(image).copy()
    bpy.data.images.remove(image)
    return result


def contact_sheet(rows, path, gap=10, shade=(0.16, 0.16, 0.17, 1.0)):
    strips = []
    for names, height in rows:
        tiles = [resized(load_pixels(name), height) for name in names if os.path.exists(name)]
        if not tiles:
            continue
        width = sum(tile.shape[1] for tile in tiles) + gap * (len(tiles) - 1)
        strip = numpy.tile(numpy.array(shade, dtype=numpy.float32), (height, width, 1))
        x = 0
        for tile in tiles:
            strip[:, x:x + tile.shape[1]] = tile
            x += tile.shape[1] + gap
        strips.append(strip)
    width = max(strip.shape[1] for strip in strips) + gap * 2
    total = sum(strip.shape[0] for strip in strips) + gap * (len(strips) + 1)
    sheet = numpy.tile(numpy.array(shade, dtype=numpy.float32), (total, width, 1))
    y = total - gap
    for strip in strips:
        y -= strip.shape[0]
        x = (width - strip.shape[1]) // 2
        sheet[y:y + strip.shape[0], x:x + strip.shape[1]] = strip
        y -= gap
    image = bpy.data.images.new(os.path.basename(path), width, total, alpha=True)
    image.pixels.foreach_set(sheet.ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    print("SHEET", path, width, total)


def stage_sheet(setup, cache):
    directory = roots["previews"]

    def named(folder, views):
        return [os.path.join(directory, "%s_%s.png" % (folder, view)) for view in views]

    folder = characters[setup["name"]]["folder"]
    rows = [
        (named(folder, ["full_front", "full_back", "full_left", "full_three"]), 900),
        (named(folder, ["face_front", "face_three", "eye_close", "overcast_face"]), 560),
        (named(folder, ["neck_front", "neck_side", "neck_back", "overcast_neck", "hair_top"]), 470),
        (named(folder, ["torso_front", "torso_side", "torso_back", "chest_close", "navel_close"]), 470),
        (named(folder, ["hand_back", "hand_palm", "feet", "foot_side", "knee_close", "back_close"]), 400),
        (named(folder, ["hair_back", "hair_side", "hair_front", "pelvis_front", "pelvis_run", "pelvis_crouch"]), 400),
        (named(folder, ["pose_walk", "pose_run", "pose_run_side", "pose_crouch", "pose_arms", "pose_arms_back"]), 640),
        (named(folder, ["underwear_front", "underwear_back", "underwear_crouch", "overcast_front", "overcast_three", "pose_arms_shoulder"]), 640),
    ]
    contact_sheet(rows, os.path.join(directory, folder + "_sheet_v2.png"))
    folders = [characters[name]["folder"] for name in ("male", "female")]
    if all(os.path.exists(os.path.join(directory, other + "_full_front.png")) for other in folders):
        rows = [(sum((named(other, ["full_front", "full_three"]) for other in folders), []), 900), (sum((named(other, ["face_front", "face_three"]) for other in folders), []), 540), (sum((named(other, ["pose_walk", "pose_run"]) for other in folders), []), 900)]
        contact_sheet(rows, os.path.join(directory, "survivors_sheet_v2.png"))


clay_views = {
    "front": ((0.0, 0.0, 0.0), (0.0, -1.0, 0.03), 4.4, 50.0, (700, 1200), "full"),
    "back": ((0.0, 0.0, 0.0), (0.0, 1.0, 0.03), 4.4, 50.0, (700, 1200), "full"),
    "side": ((0.0, 0.0, 0.0), (1.0, 0.0, 0.03), 4.4, 50.0, (700, 1200), "full"),
    "three": ((0.0, 0.0, 0.0), (0.8, -1.0, 0.15), 4.4, 50.0, (700, 1200), "full"),
    "rear": ((0.0, 0.0, 0.0), (-0.8, 1.0, 0.15), 4.4, 50.0, (700, 1200), "full"),
    "chest": ((0.0, -0.05, 0.4), (0.3, -1.0, 0.08), 1.3, 60.0, (900, 900), "torso"),
    "chest_side": ((0.0, -0.05, 0.4), (1.0, -0.3, 0.05), 1.3, 60.0, (900, 900), "torso"),
    "upper_back": ((0.0, 0.05, 0.4), (-0.3, 1.0, 0.1), 1.3, 60.0, (900, 900), "torso"),
    "belly": ((0.0, -0.05, 0.12), (0.25, -1.0, 0.05), 1.1, 60.0, (900, 900), "torso"),
    "hips": ((0.0, 0.0, -0.02), (0.5, -1.0, 0.05), 1.2, 60.0, (900, 900), "torso"),
    "glutes": ((0.0, 0.05, -0.02), (-0.4, 1.0, 0.05), 1.2, 60.0, (900, 900), "torso"),
    "shoulder": ((0.2, 0.0, 0.47), (0.9, -0.7, 0.35), 0.9, 60.0, (900, 900), "torso"),
    "arm": ((0.42, 0.0, 0.3), (0.3, -1.0, 0.2), 1.2, 60.0, (900, 900), "full"),
    "arm_back": ((0.42, 0.0, 0.3), (0.3, 1.0, 0.2), 1.2, 60.0, (900, 900), "full"),
    "legs": ((0.0, 0.0, -0.5), (0.5, -1.0, 0.05), 1.9, 60.0, (900, 900), "full"),
    "legs_back": ((0.0, 0.0, -0.5), (-0.5, 1.0, 0.05), 1.9, 60.0, (900, 900), "full"),
    "knee": ((0.1, -0.03, -0.42), (0.4, -1.0, 0.1), 0.8, 60.0, (900, 900), "full"),
    "neck": ((0.0, -0.02, 0.64), (0.55, -1.0, 0.05), 0.75, 60.0, (900, 900), "torso"),
    "neck_side": ((0.0, 0.0, 0.66), (1.0, 0.1, 0.05), 0.75, 60.0, (900, 900), "torso"),
    "neck_back": ((0.0, 0.02, 0.66), (-0.45, 1.0, 0.12), 0.75, 60.0, (900, 900), "torso"),
    "pelvis": ((0.0, -0.05, -0.085), (0.4, -1.0, -0.05), 0.62, 60.0, (900, 900), "torso"),
    "pelvis_side": ((0.0, -0.05, -0.085), (1.0, -0.55, -0.1), 0.62, 60.0, (900, 900), "torso"),
    "pelvis_low": ((0.0, -0.03, -0.1), (0.15, -1.0, -0.75), 0.6, 60.0, (900, 900), "torso"),
}


def stage_clay(setup, cache, voxel=0.002, only=None, tag=""):
    shapes = bodies.build(setup["skeleton"], setup["figure"], setup["head"])
    low, high = body_bounds(setup["skeleton"])
    if options.get("box"):
        values = [float(value) for value in options["box"].split(":")]
        origin = numpy.array(setup["skeleton"]["joints"]["Bip01 Pelvis"]) * numpy.array([0.0, 1.0, 1.0])
        low = tuple(origin + numpy.array(values[:3]) * setup["figure"]["scale"])
        high = tuple(origin + numpy.array(values[3:]) * setup["figure"]["scale"])
    started = time.time()
    grid = anatomy.level_set(shapes, low, high, voxel)
    points, triangles, quads = anatomy.mesh_of(grid)
    print("CLAY mesh", len(points), round(time.time() - started, 1), "s")
    obj = mesh_object("clay", points, quads)
    obj.data.materials.append(clay("clay", (0.3, 0.28, 0.27)))
    setup["source"].hide_render = True
    scene = setup_render(24, (700, 1200))
    stage_lights(scene, "studio")
    scene.view_settings.exposure = -0.9
    for light in [o for o in scene.objects if o.type == 'LIGHT']:
        if light.name.startswith("fill") or light.name.startswith("kick"):
            light.data.energy *= 0.35
    pelvis = numpy.array(setup["skeleton"]["joints"]["Bip01 Pelvis"])
    scale = setup["figure"]["scale"]
    directory = os.path.join(roots["previews"], "clay")
    os.makedirs(directory, exist_ok=True)
    for label, (target, direction, distance, lens, resolution, group) in clay_views.items():
        if only is not None and label not in only:
            continue
        center = pelvis * numpy.array([0.0, 1.0, 1.0]) + numpy.asarray(target) * scale
        shoot(scene, os.path.join(directory, "%s_%s%s.png" % (setup["name"], label, tag)), tuple(center), direction, distance * scale, lens, 0.0, resolution)


options = {}
sculpted = ("sculpt", "lowpoly", "bake", "clay")


def run(name, stage):
    cache = os.path.join(roots["output"], characters[name]["folder"], "cache")
    os.makedirs(cache, exist_ok=True)
    started = time.time()
    setup = character_setup(name, with_head=stage in sculpted)
    function = globals()["stage_" + stage]
    if stage == "preview":
        function(setup, cache, options.get("only"), int(options.get("samples", 96)))
    elif stage == "bake":
        function(setup, cache, int(options.get("size", 4096)))
    elif stage == "garments":
        function(setup, cache, int(options.get("cloth", 2048)))
    elif stage == "clay":
        function(setup, cache, float(options.get("voxel", 0.002)), options.get("only"), options.get("tag", ""))
    else:
        function(setup, cache)
    print("STAGE", name, stage, "done in", round(time.time() - started, 1), "s")


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:]
    roots["rocketbox"] = arguments[0]
    roots["output"] = arguments[1]
    roots["previews"] = arguments[2]
    for entry in arguments[5:]:
        key, value = entry.split("=", 1)
        options[key] = value.split(",") if key == "only" else value
    for name in arguments[3].split(","):
        for stage in arguments[4].split(","):
            run(name, stage)
