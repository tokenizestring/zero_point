import bpy
import bmesh
import math
import os
import numpy
from mathutils import Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def pixels_of(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    data = numpy.empty(width * height * 4, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(height, width, 4)[::-1].copy()


def save_pixels(path, data):
    height, width = data.shape[:2]
    image = bpy.data.images.new("sheet", width, height, alpha=False)
    image.pixels.foreach_set(numpy.ascontiguousarray(data[::-1], dtype=numpy.float32).ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)


def compose(rows, path, gap=6, shade=(0.12, 0.12, 0.13, 1.0)):
    strips = []
    for row in rows:
        height = max(tile.shape[0] for tile in row)
        width = sum(tile.shape[1] for tile in row) + gap * (len(row) - 1)
        strip = numpy.empty((height, width, 4), dtype=numpy.float32)
        strip[:] = shade
        cursor = 0
        for tile in row:
            strip[:tile.shape[0], cursor:cursor + tile.shape[1]] = tile
            cursor += tile.shape[1] + gap
        strips.append(strip)
    width = max(strip.shape[1] for strip in strips)
    height = sum(strip.shape[0] for strip in strips) + gap * (len(strips) - 1)
    sheet = numpy.empty((height, width, 4), dtype=numpy.float32)
    sheet[:] = shade
    cursor = 0
    for strip in strips:
        sheet[cursor:cursor + strip.shape[0], :strip.shape[1]] = strip
        cursor += strip.shape[0] + gap
    save_pixels(path, sheet)


def plain(name, color, roughness=0.6):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    shader.inputs['Roughness'].default_value = roughness
    return material


def studio(samples=32, ground=True, sun_direction=(0.6, -0.5, 0.62)):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = samples
    scene.eevee.use_raytracing = True
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Base Contrast'
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.7, 0.82, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    scene.world = world
    data = bpy.data.lights.new("sun", 'SUN')
    data.energy = 3.4
    data.angle = math.radians(9.0)
    data.color = (1.0, 0.96, 0.9)
    sun = bpy.data.objects.new("sun", data)
    sun.rotation_euler = Vector(sun_direction).normalized().to_track_quat('Z', 'Y').to_euler()
    scene.collection.objects.link(sun)
    if ground:
        mesh = bpy.data.meshes.new("ground")
        mesh.from_pydata([(-30.0, -30.0, 0.0), (30.0, -30.0, 0.0), (30.0, 30.0, 0.0), (-30.0, 30.0, 0.0)], [], [(0, 1, 2, 3)])
        floor = bpy.data.objects.new("ground", mesh)
        material = plain("ground", (0.2, 0.2, 0.2), 0.9)
        material.use_backface_culling = True
        mesh.materials.append(material)
        scene.collection.objects.link(floor)
    return scene


def oriented(points, faces):
    mesh = bpy.data.meshes.new("orient")
    mesh.from_pydata(numpy.asarray(points).tolist(), [], [list(face) for face in faces])
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    result = [tuple(v.index for v in face.verts) for face in bm.faces]
    bm.free()
    bpy.data.meshes.remove(mesh)
    return result


def shoot(path, target, direction, distance, ortho=0.0, lens=50.0, resolution=(1200, 800)):
    scene = bpy.context.scene
    data = bpy.data.cameras.new("view")
    data.clip_start = 0.02
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
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)
    bpy.data.cameras.remove(data)


def mesh_object(name, points, faces, smooth=True):
    mesh = bpy.data.meshes.new(name)
    points = numpy.asarray(points, dtype=numpy.float32)
    mesh.vertices.add(len(points))
    mesh.vertices.foreach_set("co", points.ravel())
    sizes = numpy.array([len(face) for face in faces], dtype=numpy.int32)
    loops = numpy.fromiter((index for face in faces for index in face), dtype=numpy.int32, count=int(sizes.sum()))
    mesh.loops.add(len(loops))
    mesh.loops.foreach_set("vertex_index", loops)
    mesh.polygons.add(len(sizes))
    mesh.polygons.foreach_set("loop_start", numpy.r_[0, numpy.cumsum(sizes)[:-1]].astype(numpy.int32))
    mesh.update(calc_edges=True)
    mesh.validate()
    if smooth:
        mesh.polygons.foreach_set("use_smooth", numpy.ones(len(mesh.polygons), dtype=bool))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def wire(obj, thickness=0.0012):
    copy = bpy.data.objects.new(obj.name + "_wire", obj.data)
    bpy.context.scene.collection.objects.link(copy)
    copy.matrix_world = obj.matrix_world
    modifier = copy.modifiers.new("wire", 'WIREFRAME')
    modifier.thickness = thickness
    modifier.use_even_offset = False
    modifier.offset = 1.0
    modifier.material_offset = len(obj.data.materials)
    material = plain("wire", (0.01, 0.01, 0.012), 0.9)
    obj.data.materials.append(material)
    return copy


def fit(span_x, span_y, resolution, margin=1.08):
    if resolution[0] >= resolution[1]:
        return max(span_x, span_y * resolution[0] / resolution[1]) * margin
    return max(span_y, span_x * resolution[1] / resolution[0]) * margin


def shots(prefix, path, rows):
    tiles = []
    for row in rows:
        strip = []
        for index, view in enumerate(row):
            file = "%s_%d_%d.png" % (prefix, len(tiles), index)
            if view.get("top"):
                shoot_top(file, view["target"], 8.0, view["ortho"], view["resolution"])
            else:
                shoot(file, view["target"], view["direction"], view.get("distance", 8.0), ortho=view.get("ortho", 0.0), lens=view.get("lens", 50.0), resolution=view["resolution"])
            strip.append(pixels_of(file))
            os.remove(file)
        tiles.append(strip)
    compose(tiles, path)


def sheet_rows(extent, head, scale=1.0, zoom=1.0):
    length = extent["length"]
    height = extent["height"]
    center = extent["center"]
    body = extent.get("body", height)
    side = {"target": (0.0, center, height * 0.5), "direction": (1.0, 0.0, 0.0), "ortho": fit(length, height, (1500, 1100)), "resolution": (1500, 1100)}
    close = {"target": head, "direction": (0.8, -0.62, 0.12), "distance": 1.75 * scale * zoom, "lens": 70.0, "resolution": (900, 1100)}
    front = {"target": (0.0, center, height * 0.5), "direction": (0.0, -1.0, 0.0), "ortho": fit(1.2 * scale * zoom, height, (640, 900)), "resolution": (640, 900)}
    rear = {"target": (0.0, center * 0.4, body * 0.5), "direction": (0.72, 0.62, 0.3), "distance": 4.6 * scale * zoom, "resolution": (900, 900)}
    top = {"target": (0.0, center, 0.0), "top": True, "ortho": fit(length, 1.2 * scale * zoom, (860, 900)), "resolution": (860, 900)}
    return [[side, close], [front, rear, top]]


def detail_rows(marks, scale=1.0, zoom=1.0):
    head = marks["eye"] * numpy.array([0.0, 1.0, 1.0]) * scale + numpy.array([0.0, -0.06, -0.04]) * scale * zoom
    wide = scale * zoom
    profile = {"target": tuple(head), "direction": (1.0, 0.0, 0.0), "ortho": 0.62 * wide, "resolution": (1100, 900)}
    face = {"target": tuple(head), "direction": (0.35, -1.0, 0.1), "ortho": 0.5 * wide, "resolution": (800, 900)}
    above = {"target": tuple(head), "direction": (0.0, -1.0, 0.0), "ortho": 0.5 * wide, "resolution": (500, 900)}
    fore = {"target": (0.0, float(marks["carpus"][1]) * scale, 0.42 * wide), "direction": (1.0, 0.0, 0.0), "ortho": 0.98 * wide, "resolution": (560, 900)}
    fore_front = {"target": (0.0, float(marks["carpus"][1]) * scale, 0.42 * wide), "direction": (0.0, -1.0, 0.0), "ortho": 0.98 * wide, "resolution": (560, 900)}
    hind = {"target": (0.0, float(marks["hock"][1]) * scale - 0.08 * wide, 0.52 * wide), "direction": (1.0, 0.0, 0.0), "ortho": 1.15 * wide, "resolution": (640, 900)}
    hind_rear = {"target": (0.0, float(marks["hock"][1]) * scale, 0.52 * wide), "direction": (0.0, 1.0, 0.0), "ortho": 1.15 * wide, "resolution": (540, 900)}
    return [[profile, face, above], [fore, fore_front, hind, hind_rear]]


def shoot_top(path, target, distance, ortho, resolution):
    scene = bpy.context.scene
    data = bpy.data.cameras.new("view")
    data.type = 'ORTHO'
    data.ortho_scale = ortho
    data.clip_end = 200.0
    camera = bpy.data.objects.new("view", data)
    scene.collection.objects.link(camera)
    camera.location = Vector(target) + Vector((0.0, 0.0, distance))
    camera.rotation_euler = (0.0, 0.0, math.radians(90.0))
    scene.camera = camera
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)
    bpy.data.cameras.remove(data)
