import bpy
import bmesh
import json
import math
import os
import random
import struct
import sys
import numpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import turntable

arguments = sys.argv[sys.argv.index("--") + 1:]
source_root = arguments[0]
output_root = arguments[1]
preview_root = arguments[2]
atlas_directory = os.path.join(source_root, "grass", "grass_clumps")
cell_size = 1024
cell_world = 1.0
base_margin = 0.015

palettes = {
    "lush": [((0.050, 0.070, 0.020), (0.110, 0.190, 0.040), (0.220, 0.320, 0.070)), ((0.055, 0.072, 0.022), (0.130, 0.205, 0.045), (0.270, 0.340, 0.085)), ((0.045, 0.065, 0.020), (0.090, 0.170, 0.045), (0.180, 0.290, 0.075))],
    "dry": [((0.110, 0.090, 0.040), (0.340, 0.270, 0.120), (0.560, 0.460, 0.240)), ((0.080, 0.080, 0.030), (0.260, 0.240, 0.100), (0.470, 0.400, 0.190)), ((0.060, 0.075, 0.025), (0.160, 0.190, 0.055), (0.400, 0.360, 0.160))],
    "dead": [((0.080, 0.060, 0.030), (0.200, 0.140, 0.065), (0.330, 0.240, 0.120))],
    "seed": [((0.220, 0.180, 0.090), (0.400, 0.320, 0.160), (0.560, 0.470, 0.260))],
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mix(a, b, t):
    return tuple(a[index] + (b[index] - a[index]) * t for index in range(3))


def gradient(colors, t):
    if t < 0.45:
        return mix(colors[0], colors[1], (t / 0.45) ** 0.8)
    return mix(colors[1], colors[2], ((t - 0.45) / 0.55) ** 1.3)


def add_blade(bm, tint, base, yaw, lean, length, width, bend, twist, colors, shade):
    segments = 11
    heading = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    axis = Vector((-heading.y, heading.x, 0.0))
    rows = []
    position = base.copy()
    step = length / segments
    for index in range(segments + 1):
        t = index / segments
        pitch = lean + bend * t ** 1.8
        direction = (Matrix.Rotation(pitch, 3, axis) @ Vector((0.0, 0.0, 1.0))).normalized()
        side = (Matrix.Rotation(twist * t, 3, direction) @ axis).normalized()
        front = direction.cross(side).normalized()
        half = width * 0.5 * (1.0 - t ** 2.4) * (0.82 + 0.18 * math.sin(math.pi * min(1.0, t * 1.4)))
        fold = half * 0.45
        color = gradient(colors, t)
        color = (color[0] * shade, color[1] * shade, color[2] * shade)
        if index == segments:
            rows.append([(bm.verts.new(position), color)])
        else:
            rows.append([(bm.verts.new(position - side * half), color), (bm.verts.new(position + front * fold), color), (bm.verts.new(position + side * half), color)])
        position = position + direction * step
    for index in range(segments):
        lower = rows[index]
        upper = rows[index + 1]
        if len(upper) == 1:
            faces = [bm.faces.new((lower[0][0], lower[1][0], upper[0][0])), bm.faces.new((lower[1][0], lower[2][0], upper[0][0]))]
            colors_used = [(lower[0][1], lower[1][1], upper[0][1]), (lower[1][1], lower[2][1], upper[0][1])]
        else:
            faces = [bm.faces.new((lower[0][0], lower[1][0], upper[1][0], upper[0][0])), bm.faces.new((lower[1][0], lower[2][0], upper[2][0], upper[1][0]))]
            colors_used = [(lower[0][1], lower[1][1], upper[1][1], upper[0][1]), (lower[1][1], lower[2][1], upper[2][1], upper[1][1])]
        for face, face_colors in zip(faces, colors_used):
            face.smooth = True
            for loop, color in zip(face.loops, face_colors):
                loop[tint] = (color[0], color[1], color[2], 1.0)


def add_stem(bm, tint, base, yaw, lean, length, radius, colors):
    heading = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    axis = Vector((-heading.y, heading.x, 0.0))
    points = []
    position = base.copy()
    segments = 14
    for index in range(segments + 1):
        t = index / segments
        points.append(position.copy())
        direction = (Matrix.Rotation(lean + 0.35 * t ** 2, 3, axis) @ Vector((0.0, 0.0, 1.0))).normalized()
        position = position + direction * (length / segments)
    rings = []
    for index, point in enumerate(points):
        ahead = points[min(index + 1, segments)]
        behind = points[max(index - 1, 0)]
        tangent = (ahead - behind).normalized()
        side = tangent.cross(Vector((0.0, 0.0, 1.0)) if abs(tangent.z) < 0.95 else Vector((1.0, 0.0, 0.0))).normalized()
        normal = side.cross(tangent).normalized()
        color = gradient(colors, index / segments)
        rings.append([(bm.verts.new(point + (side * math.cos(a) + normal * math.sin(a)) * radius * (1.0 - 0.5 * index / segments)), color) for a in (0.0, math.tau / 3.0, math.tau * 2.0 / 3.0)])
    for index in range(segments):
        for corner in range(3):
            a = rings[index][corner]
            b = rings[index][(corner + 1) % 3]
            c = rings[index + 1][(corner + 1) % 3]
            d = rings[index + 1][corner]
            face = bm.faces.new((a[0], b[0], c[0], d[0]))
            face.smooth = True
            for loop, color in zip(face.loops, (a[1], b[1], c[1], d[1])):
                loop[tint] = (color[0], color[1], color[2], 1.0)
    return points


def add_spikelet(bm, tint, base, direction, length, width, color):
    side = direction.cross(Vector((0.0, 0.0, 1.0)))
    if side.length < 1e-4:
        side = Vector((1.0, 0.0, 0.0))
    side.normalize()
    front = direction.cross(side).normalized()
    ring = []
    for step in range(6):
        angle = math.tau * step / 6.0
        ring.append(base + direction * (length * 0.45) + (side * math.cos(angle) + front * math.sin(angle)) * width)
    tip = bm.verts.new(base + direction * length)
    root = bm.verts.new(base)
    verts = [bm.verts.new(point) for point in ring]
    for step in range(6):
        for face in (bm.faces.new((root, verts[(step + 1) % 6], verts[step])), bm.faces.new((verts[step], verts[(step + 1) % 6], tip))):
            face.smooth = True
            for loop in face.loops:
                loop[tint] = (color[0], color[1], color[2], 1.0)


def build_clump(kind, rng, origin):
    bm = bmesh.new()
    tint = bm.loops.layers.float_color.new("tint")
    settings = {
        "lush": (230, 0.24, 0.62, 0.0105, 0.34, 0.07),
        "meadow": (170, 0.26, 0.58, 0.0095, 0.30, 0.09),
        "dry": (190, 0.2, 0.55, 0.0095, 0.32, 0.12),
        "short": (280, 0.1, 0.3, 0.0105, 0.36, 0.05),
    }
    count, low, high, width, spread, dead = settings[kind]
    for blade in range(count):
        offset = rng.uniform(-1.0, 1.0)
        across = offset * abs(offset) ** 0.35
        base = origin + Vector((across * spread, rng.uniform(-0.09, 0.09), 0.0))
        outward = rng.uniform(0.0, math.tau)
        edge = abs(across)
        length = rng.uniform(low, high) * (1.0 - 0.45 * edge ** 2)
        lean = rng.uniform(0.02, 0.32) + 0.25 * edge
        if across * math.cos(outward) < 0.0 and edge > 0.6:
            outward += math.pi
        bend = rng.uniform(0.1, 0.9) if rng.random() < 0.75 else rng.uniform(0.9, 1.8)
        if bend > 0.9:
            length *= 0.7
        if rng.random() < dead:
            colors = palettes["dead"][0]
        elif kind == "dry":
            colors = rng.choice(palettes["dry"])
        elif kind == "meadow" and rng.random() < 0.3:
            colors = palettes["dry"][2]
        else:
            colors = rng.choice(palettes["lush"])
        shade = rng.uniform(0.8, 1.15)
        add_blade(bm, tint, base, outward, lean, length, width * rng.uniform(0.75, 1.3), bend, rng.uniform(-1.4, 1.4), colors, shade)
    if kind in ("meadow", "dry"):
        for stem in range(10 if kind == "meadow" else 6):
            angle = rng.uniform(0.0, math.tau)
            base = origin + Vector((rng.uniform(-0.7, 0.7) * spread, rng.uniform(-0.06, 0.06), 0.0))
            length = rng.uniform(0.66, 0.92) if kind == "meadow" else rng.uniform(0.5, 0.74)
            points = add_stem(bm, tint, base, angle, rng.uniform(0.05, 0.3), length, 0.0024, palettes["dry"][2] if kind == "meadow" else palettes["dry"][0])
            head = points[-4:]
            for spike in range(16):
                t = spike / 15.0
                anchor = head[0].lerp(head[-1], t)
                along = (head[-1] - head[0]).normalized()
                droop = Matrix.Rotation(rng.uniform(0.3, 0.9) * (1 if spike % 2 else -1), 3, Vector((0.0, 0.0, 1.0)).cross(along).normalized() if abs(along.z) < 0.99 else Vector((1.0, 0.0, 0.0)))
                direction = (droop @ along).normalized()
                direction = (direction + Vector((0.0, 0.0, -0.35))).normalized()
                add_spikelet(bm, tint, anchor, direction, rng.uniform(0.018, 0.03), 0.0038, gradient(palettes["seed"][0], rng.uniform(0.4, 1.0)))
    mesh = bpy.data.meshes.new(kind)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(kind, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def pass_material(kind):
    material = bpy.data.materials.new(kind)
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    if kind == "albedo":
        attribute = tree.nodes.new('ShaderNodeAttribute')
        attribute.attribute_name = "tint"
        attribute.attribute_type = 'GEOMETRY'
        surface = tree.nodes.new('ShaderNodeEmission')
        tree.links.new(attribute.outputs['Color'], surface.inputs['Color'])
        shader = surface.outputs['Emission']
    elif kind == "normal":
        geometry = tree.nodes.new('ShaderNodeNewGeometry')
        sign = tree.nodes.new('ShaderNodeMath')
        sign.operation = 'MULTIPLY_ADD'
        tree.links.new(geometry.outputs['Backfacing'], sign.inputs[0])
        sign.inputs[1].default_value = -2.0
        sign.inputs[2].default_value = 1.0
        flip = tree.nodes.new('ShaderNodeVectorMath')
        flip.operation = 'SCALE'
        tree.links.new(geometry.outputs['Normal'], flip.inputs[0])
        tree.links.new(sign.outputs['Value'], flip.inputs['Scale'])
        facing = tree.nodes.new('ShaderNodeVectorMath')
        facing.operation = 'DOT_PRODUCT'
        tree.links.new(flip.outputs['Vector'], facing.inputs[0])
        facing.inputs[1].default_value = (0.0, -1.0, 0.0)
        toward = tree.nodes.new('ShaderNodeMath')
        toward.operation = 'SIGN'
        tree.links.new(facing.outputs['Value'], toward.inputs[0])
        oriented = tree.nodes.new('ShaderNodeVectorMath')
        oriented.operation = 'SCALE'
        tree.links.new(flip.outputs['Vector'], oriented.inputs[0])
        tree.links.new(toward.outputs['Value'], oriented.inputs['Scale'])
        separate = tree.nodes.new('ShaderNodeSeparateXYZ')
        tree.links.new(oriented.outputs['Vector'], separate.inputs['Vector'])
        combine = tree.nodes.new('ShaderNodeCombineXYZ')
        tree.links.new(separate.outputs['X'], combine.inputs['X'])
        tree.links.new(separate.outputs['Z'], combine.inputs['Y'])
        negate = tree.nodes.new('ShaderNodeMath')
        negate.operation = 'MULTIPLY'
        negate.inputs[1].default_value = -1.0
        tree.links.new(separate.outputs['Y'], negate.inputs[0])
        tree.links.new(negate.outputs['Value'], combine.inputs['Z'])
        encode = tree.nodes.new('ShaderNodeVectorMath')
        encode.operation = 'MULTIPLY_ADD'
        tree.links.new(combine.outputs['Vector'], encode.inputs[0])
        encode.inputs[1].default_value = (0.5, 0.5, 0.5)
        encode.inputs[2].default_value = (0.5, 0.5, 0.5)
        surface = tree.nodes.new('ShaderNodeEmission')
        tree.links.new(encode.outputs['Vector'], surface.inputs['Color'])
        shader = surface.outputs['Emission']
    else:
        surface = tree.nodes.new('ShaderNodeBsdfDiffuse')
        surface.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        shader = surface.outputs['BSDF']
    tree.links.new(shader, output.inputs['Surface'])
    return material


def render_pass(scene, clump, material, path, transform, samples):
    clump.data.materials.clear()
    clump.data.materials.append(material)
    scene.view_settings.view_transform = transform
    scene.cycles.samples = samples
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def dilate(pixels, alpha, passes):
    color = pixels[:, :, :3].copy()
    known = alpha > 0.02
    for index in range(passes):
        grown = known.copy()
        total = numpy.zeros_like(color)
        count = numpy.zeros(alpha.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            shifted_known = numpy.roll(numpy.roll(known, dy, 0), dx, 1)
            shifted_color = numpy.roll(numpy.roll(color, dy, 0), dx, 1)
            total += shifted_color * shifted_known[:, :, None]
            count += shifted_known
        fill = (known == False) & (count > 0)
        color[fill] = total[fill] / count[fill][:, None]
        grown |= fill
        known = grown
    return color


def load_pixels(path):
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = 'Non-Color'
    data = numpy.array(image.pixels[:], dtype=numpy.float32).reshape(image.size[1], image.size[0], 4)
    bpy.data.images.remove(image)
    return data


def save_pixels(path, data, channels):
    height, width = data.shape[:2]
    image = bpy.data.images.new(os.path.basename(path), width, height, alpha=channels == 4)
    image.colorspace_settings.name = 'Non-Color'
    full = numpy.ones((height, width, 4), dtype=numpy.float32)
    full[:, :, :data.shape[2]] = data
    image.pixels.foreach_set(full.ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)


def write_quad(name, stem):
    directory = os.path.join(output_root, name)
    os.makedirs(directory, exist_ok=True)
    positions = [(-0.5, 0.0, 0.0), (0.5, 0.0, 0.0), (0.5, 1.0, 0.0), (-0.5, 1.0, 0.0)]
    normals = [(0.0, 0.0, -1.0)] * 4
    uvs = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    blob = struct.pack("<12f", *[c for p in positions for c in p]) + struct.pack("<12f", *[c for n in normals for c in n]) + struct.pack("<8f", *[c for u in uvs for c in u]) + struct.pack("<6I", 0, 1, 2, 0, 2, 3)
    with open(os.path.join(directory, name + ".bin"), "wb") as handle:
        handle.write(blob)
    relative = os.path.relpath(atlas_directory, directory).replace("\\", "/")
    document = {
        "asset": {"version": "2.0", "generator": "zero point grass"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "grass", "mesh": 0}],
        "meshes": [{"name": "grass", "primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]}],
        "materials": [{"name": "grass", "alphaMode": "MASK", "alphaCutoff": 0.5, "doubleSided": True, "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicRoughnessTexture": {"index": 2}, "metallicFactor": 0.0, "roughnessFactor": 1.0}, "normalTexture": {"index": 1}, "occlusionTexture": {"index": 2}}],
        "textures": [{"source": 0}, {"source": 1}, {"source": 2}],
        "images": [{"uri": relative + "/" + stem + "_diff_2k.png"}, {"uri": relative + "/" + stem + "_nor_gl_2k.png"}, {"uri": relative + "/" + stem + "_arm_2k.png"}],
        "buffers": [{"uri": name + ".bin", "byteLength": len(blob)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 48}, {"buffer": 0, "byteOffset": 96, "byteLength": 32}, {"buffer": 0, "byteOffset": 128, "byteLength": 24}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-0.5, 0.0, 0.0], "max": [0.5, 1.0, 0.0]}, {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"}, {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC2"}, {"bufferView": 3, "componentType": 5125, "count": 6, "type": "SCALAR"}],
    }
    with open(os.path.join(directory, name + ".gltf"), "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)


def make_atlas():
    reset()
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    turntable.accelerate(scene)
    scene.render.resolution_x = cell_size
    scene.render.resolution_y = cell_size
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.cycles.transparent_max_bounces = 16
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.look = 'None'
    world = bpy.data.worlds.new("grass")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    scene.world = world
    ground_data = bpy.data.meshes.new("ground")
    ground_data.from_pydata([(-3.0, -3.0, 0.0), (3.0, -3.0, 0.0), (3.0, 3.0, 0.0), (-3.0, 3.0, 0.0)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("ground", ground_data)
    ground.visible_camera = False
    scene.collection.objects.link(ground)
    ground_material = bpy.data.materials.new("ground")
    ground_material.use_nodes = True
    next(node for node in ground_material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.08, 0.07, 0.05, 1.0)
    ground_data.materials.append(ground_material)
    camera_data = bpy.data.cameras.new("grass")
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = cell_world
    camera = bpy.data.objects.new("grass", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = Vector((0.0, -6.0, cell_world * 0.5 - base_margin))
    camera.rotation_euler = Vector((0.0, 1.0, 0.0)).to_track_quat('-Z', 'Y').to_euler()
    materials = {name: pass_material(name) for name in ("albedo", "normal", "occlusion")}
    size = cell_size * 2
    color_atlas = numpy.zeros((size, size, 3), dtype=numpy.float32)
    normal_atlas = numpy.zeros((size, size, 3), dtype=numpy.float32)
    shade_atlas = numpy.ones((size, size), dtype=numpy.float32)
    alpha_atlas = numpy.zeros((size, size), dtype=numpy.float32)
    rng = random.Random(4217)
    scratch = os.path.join(preview_root, "grass_cell.png")
    os.makedirs(preview_root, exist_ok=True)
    for cell, kind in enumerate(("lush", "meadow", "dry", "short")):
        clump = build_clump(kind, rng, Vector((0.0, 0.0, 0.0)))
        results = {}
        for name, transform, samples, strength in (("albedo", 'Standard', 32, 0.0), ("normal", 'Raw', 32, 0.0), ("occlusion", 'Raw', 192, 1.0)):
            ground.hide_render = name != "occlusion"
            background.inputs['Strength'].default_value = strength
            render_pass(scene, clump, materials[name], scratch, transform, samples)
            results[name] = load_pixels(scratch)
        bpy.data.objects.remove(clump)
        alpha = results["albedo"][:, :, 3]
        shade = numpy.clip(results["occlusion"][:, :, 0], 0.0, 1.0)
        column = cell % 2
        row = 1 - cell // 2
        rows = slice(row * cell_size, (row + 1) * cell_size)
        columns = slice(column * cell_size, (column + 1) * cell_size)
        color_atlas[rows, columns] = dilate(results["albedo"], alpha, 24)
        normal_atlas[rows, columns] = dilate(results["normal"], alpha, 24)
        shade_atlas[rows, columns] = dilate(numpy.repeat(shade[:, :, None], 3, axis=2), alpha, 24)[:, :, 0]
        alpha_atlas[rows, columns] = alpha
        covered = numpy.argwhere(alpha > 0.05)
        top = cell_size - 1 - int(covered[:, 0].max())
        left = int(covered[:, 1].min())
        right = int(covered[:, 1].max()) + 1
        pad = 6
        u0 = (column * cell_size + max(left - pad, 0)) / size
        u1 = (column * cell_size + min(right + pad, cell_size)) / size
        v0 = ((1 - row) * cell_size + max(top - pad, 0)) / size
        v1 = ((1 - row) * cell_size + cell_size) / size
        print("CELL", cell, kind, round(float(alpha.mean()), 4), "RECT { %.4ff, %.4ff, %.4ff, %.4ff }" % (u0, v0, u1, v1))
    os.remove(scratch)
    shade = numpy.clip(shade_atlas * 0.75 + 0.25, 0.0, 1.0)
    color = color_atlas * shade[:, :, None] ** 0.6
    arm = numpy.stack([shade, numpy.full_like(shade, 0.72), numpy.zeros_like(shade)], axis=2)
    stem = "grass_clumps"
    os.makedirs(atlas_directory, exist_ok=True)
    save_pixels(os.path.join(atlas_directory, stem + "_diff_2k.png"), color, 3)
    save_pixels(os.path.join(atlas_directory, stem + "_alpha_2k.png"), numpy.repeat(alpha_atlas[:, :, None], 3, axis=2), 3)
    save_pixels(os.path.join(atlas_directory, stem + "_nor_gl_2k.png"), normal_atlas, 3)
    save_pixels(os.path.join(atlas_directory, stem + "_arm_2k.png"), arm, 3)
    preview = numpy.concatenate([color * alpha_atlas[:, :, None] + numpy.array([0.55, 0.62, 0.7]) * (1.0 - alpha_atlas[:, :, None]), numpy.ones_like(alpha_atlas)[:, :, None]], axis=2)
    save_pixels(os.path.join(preview_root, stem + "_preview.png"), preview, 4)
    save_pixels(os.path.join(preview_root, stem + "_normals.png"), numpy.concatenate([normal_atlas * alpha_atlas[:, :, None], numpy.ones_like(alpha_atlas)[:, :, None]], axis=2), 4)
    write_quad(stem, stem)
    print("ATLAS", stem, float(alpha_atlas.mean()))


make_atlas()
