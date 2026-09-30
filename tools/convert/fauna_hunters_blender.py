import math
import os
import bpy
import bmesh
import numpy as np
from mathutils import Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def select(objects, active):
    bpy.context.view_layer.update()
    for other in bpy.context.scene.objects:
        other.select_set(other in objects)
    bpy.context.view_layer.objects.active = active


def mesh_object(name, positions, faces, smooth=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(p) for p in positions], [], [tuple(f) for f in faces])
    mesh.update()
    if smooth:
        mesh.polygons.foreach_set("use_smooth", np.ones(len(mesh.polygons), dtype=bool))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def recalc_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def read_faces(obj):
    return [tuple(polygon.vertices) for polygon in obj.data.polygons]


def mark_seams(obj, seams):
    mesh = obj.data
    lookup = {}
    for edge in mesh.edges:
        a, b = edge.vertices
        lookup[(min(a, b), max(a, b))] = edge.index
    flags = np.zeros(len(mesh.edges), dtype=bool)
    missing = 0
    for a, b in seams:
        index = lookup.get((min(a, b), max(a, b)))
        if index is None:
            missing += 1
        else:
            flags[index] = True
    mesh.edges.foreach_set("use_seam", flags)
    return missing


def mark_sharp(obj, sharp):
    mesh = obj.data
    lookup = {}
    for edge in mesh.edges:
        a, b = edge.vertices
        lookup[(min(a, b), max(a, b))] = edge.index
    flags = np.zeros(len(mesh.edges), dtype=bool)
    for a, b in sharp:
        index = lookup.get((min(a, b), max(a, b)))
        if index is not None:
            flags[index] = True
    mesh.edges.foreach_set("use_edge_sharp", flags)
    mesh.update()


def face_islands(faces, seams):
    parent = list(range(len(faces)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner = {}
    for index, face in enumerate(faces):
        for k in range(len(face)):
            a = face[k]
            b = face[(k + 1) % len(face)]
            key = (min(a, b), max(a, b))
            if key in seams:
                continue
            if key in owner:
                ra = find(owner[key])
                rb = find(index)
                if ra != rb:
                    parent[ra] = rb
            else:
                owner[key] = index
    roots = [find(i) for i in range(len(faces))]
    names = {root: k for k, root in enumerate(sorted(set(roots)))}
    return np.array([names[root] for root in roots], dtype=np.int64)


def polygon_area(points):
    total = 0.0
    for k in range(1, len(points) - 1):
        a = points[k] - points[0]
        b = points[k + 1] - points[0]
        if points.shape[1] == 2:
            total += 0.5 * abs(a[0] * b[1] - a[1] * b[0])
        else:
            total += 0.5 * float(np.linalg.norm(np.cross(a, b)))
    return total


def unwrap(obj, seams, factor, margin=0.003, method='ANGLE_BASED'):
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    select([obj], obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method=method, margin=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')
    faces = read_faces(obj)
    positions = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)
    raw =np.empty(len(mesh.loops) * 2, dtype=np.float32)
    mesh.uv_layers[0].data.foreach_get("uv", raw)
    loops = raw.reshape(-1, 2).astype(np.float64)
    starts = np.empty(len(mesh.polygons), dtype=np.int32)
    mesh.polygons.foreach_get("loop_start", starts)
    positions = positions.astype(np.float64)
    islands = face_islands(faces, seams)
    for island in range(int(islands.max()) + 1):
        chosen = np.nonzero(islands == island)[0]
        area3 = 0.0
        area2 = 0.0
        rows = []
        for index in chosen:
            face = faces[index]
            span = list(range(starts[index], starts[index] + len(face)))
            rows.extend(span)
            area3 += polygon_area(positions[list(face)])
            area2 += polygon_area(loops[span])
        rows = np.array(rows, dtype=np.int64)
        scale = math.sqrt(area3 / max(area2, 1e-14)) * factor(chosen)
        center = loops[rows].mean(axis=0)
        loops[rows] = (loops[rows] - center) * scale + center
    mesh.uv_layers[0].data.foreach_set("uv", loops.astype(np.float32).ravel())
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, rotate_method='ANY', scale=True, margin_method='FRACTION', margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    packed = np.empty(len(mesh.loops) * 2, dtype=np.float32)
    mesh.uv_layers[0].data.foreach_get("uv", packed)
    loops = packed.reshape(-1, 2).astype(np.float64)
    face_uvs =[loops[starts[index]:starts[index] + len(faces[index])].copy() for index in range(len(faces))]
    return faces, face_uvs, islands


def clay(name="clay", color=(0.62, 0.6, 0.57), roughness=0.6):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    shader.inputs['Roughness'].default_value = roughness
    return material


def studio(scene, ground=True, sun_energy=3.4, sky=0.55, sun_from=(0.55, -0.6, 0.75)):
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = 32
    try:
        scene.eevee.use_shadows = True
        scene.eevee.use_raytracing = True
        scene.eevee.use_gtao = True
    except Exception:
        pass
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs[0].default_value = (0.72, 0.8, 0.95, 1.0)
    background.inputs[1].default_value = sky
    scene.world = world
    data = bpy.data.lights.new("sun", 'SUN')
    data.energy = sun_energy
    data.angle = math.radians(6.0)
    sun = bpy.data.objects.new("sun", data)
    sun.rotation_euler = (-Vector(sun_from)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(sun)
    if ground:
        mesh = bpy.data.meshes.new("ground")
        mesh.from_pydata([(-30.0, -30.0, 0.0), (30.0, -30.0, 0.0), (30.0, 30.0, 0.0), (-30.0, 30.0, 0.0)], [], [(0, 1, 2, 3)])
        floor = bpy.data.objects.new("ground", mesh)
        mesh.materials.append(clay("ground", (0.42, 0.42, 0.42), 0.9))
        scene.collection.objects.link(floor)
    return sun


def shoot(scene, path, target, direction, distance, ortho=0.0, lens=70.0, resolution=(1200, 800)):
    data = bpy.data.cameras.new("view")
    data.clip_start = 0.01
    data.clip_end = 200.0
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
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)
    bpy.data.cameras.remove(data)


def wire_copy(obj, thickness=0.0012, color=(0.02, 0.02, 0.02)):
    copy = obj.copy()
    copy.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(copy)
    modifier = copy.modifiers.new("wire", 'WIREFRAME')
    modifier.thickness = thickness
    modifier.use_replace = True
    material = bpy.data.materials.new("wire")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    shader.inputs['Roughness'].default_value = 1.0
    copy.data.materials.clear()
    copy.data.materials.append(material)
    return copy


def load_pixels(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    data = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(height, width, 4)


def save_pixels(path, data, colorspace='sRGB'):
    height, width = data.shape[:2]
    if data.shape[2] == 3:
        data = np.concatenate([data, np.ones((height, width, 1), dtype=data.dtype)], axis=2)
    image = bpy.data.images.new("out", width, height, alpha=True)
    image.colorspace_settings.name = colorspace
    image.pixels.foreach_set(np.ascontiguousarray(data, dtype=np.float32).ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)


def contact_sheet(rows, path, gap=6, shade=(0.12, 0.12, 0.13, 1.0)):
    loaded = [[load_pixels(p) for p in row] for row in rows]
    heights = [max(image.shape[0] for image in row) for row in loaded]
    widths = [sum(image.shape[1] for image in row) + gap * (len(row) - 1) for row in loaded]
    total_width = max(widths)
    total_height = sum(heights) + gap * (len(rows) - 1)
    sheet = np.empty((total_height, total_width, 4), dtype=np.float32)
    sheet[:] = np.array(shade, dtype=np.float32)
    y = total_height
    for row, height in zip(loaded, heights):
        x = 0
        for image in row:
            h, w = image.shape[:2]
            sheet[y - h:y, x:x + w] = image
            x += w + gap
        y -= height + gap
    save_pixels(path, sheet)
