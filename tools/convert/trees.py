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
mode = arguments[3] if len(arguments) > 3 else "atlas"
atlas_directory = os.path.join(source_root, "trees", "conifer_spray")
bark_directory = os.path.join(source_root, "trees", "fir_tree_01")
impostor_directory = os.path.join(source_root, "trees", "conifer_impostor")
atlas_size = 2048
cell_world = 0.62
impostor_frames = 8
impostor_columns = 4
impostor_cell = (256, 512)


def v(x, y, z):
    return Vector((x, y, z))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def emission_material(name, color_node_builder):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    emission = tree.nodes.new('ShaderNodeEmission')
    tree.links.new(color_node_builder(tree), emission.inputs['Color'])
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return material


def needle_color(tree):
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_name = "tint"
    attribute.attribute_type = 'GEOMETRY'
    return attribute.outputs['Color']


def normal_color(tree):
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    scale = tree.nodes.new('ShaderNodeVectorMath')
    scale.operation = 'MULTIPLY_ADD'
    tree.links.new(geometry.outputs['Normal'], scale.inputs[0])
    scale.inputs[1].default_value = (0.5, 0.5, 0.5)
    scale.inputs[2].default_value = (0.5, 0.5, 0.5)
    return scale.outputs['Vector']


def occlusion_color(tree):
    occlusion = tree.nodes.new('ShaderNodeAmbientOcclusion')
    occlusion.inputs['Distance'].default_value = 0.035
    occlusion.samples = 16
    return occlusion.outputs['AO']


def add_needle(bm, tint_layer, base, direction, up, length, width, tint_base, tint_tip):
    side = direction.cross(up).normalized() * width * 0.5
    lift = up.normalized() * width * 0.18
    bend = up.normalized() * length * 0.06
    points = [base - side, base + side, base + direction * length * 0.5 + side * 0.9 + bend + lift, base + direction * length + bend * 1.6, base + direction * length * 0.5 - side * 0.9 + bend + lift]
    verts = [bm.verts.new(point) for point in points]
    faces = [bm.faces.new((verts[0], verts[1], verts[2], verts[4])), bm.faces.new((verts[4], verts[2], verts[3]))]
    for face in faces:
        for loop in face.loops:
            t = (loop.vert.co - base).dot(direction) / max(length, 1e-6)
            tint = tint_base.lerp(tint_tip, max(0.0, min(1.0, t)) ** 1.6)
            loop[tint_layer] = (tint.x, tint.y, tint.z, 1.0)


def add_twig(bm, tint_layer, points, radius_start, radius_end, color):
    rings = []
    count = len(points)
    for index, point in enumerate(points):
        ahead = points[min(index + 1, count - 1)]
        behind = points[max(index - 1, 0)]
        tangent = (ahead - behind).normalized()
        side = tangent.cross(v(0.0, 0.0, 1.0))
        if side.length < 1e-4:
            side = v(1.0, 0.0, 0.0)
        side.normalize()
        normal = side.cross(tangent).normalized()
        radius = radius_start + (radius_end - radius_start) * index / max(count - 1, 1)
        rings.append([bm.verts.new(point + (side * math.cos(a) + normal * math.sin(a)) * radius) for a in (0.0, math.pi * 0.5, math.pi, math.pi * 1.5)])
    for index in range(count - 1):
        for corner in range(4):
            face = bm.faces.new((rings[index][corner], rings[index][(corner + 1) % 4], rings[index + 1][(corner + 1) % 4], rings[index + 1][corner]))
            for loop in face.loops:
                loop[tint_layer] = (color.x, color.y, color.z, 1.0)


def curve_points(start, direction, length, curl, steps):
    points = []
    heading = direction.normalized()
    position = start.copy()
    step = length / steps
    for index in range(steps + 1):
        points.append(position.copy())
        heading = (Matrix.Rotation(curl * step, 3, 'Z') @ heading).normalized()
        position = position + heading * step
    return points


def build_spray(rng, origin, scale, lush):
    bm = bmesh.new()
    tint_layer = bm.loops.layers.float_color.new("tint")
    dark = v(0.018, 0.05, 0.018)
    mid = v(0.035, 0.082, 0.026)
    fresh = v(0.12, 0.2, 0.045)
    twig_color = v(0.06, 0.036, 0.02)
    length = 0.5 * scale
    main = curve_points(origin, v(rng.uniform(-0.06, 0.06), 1.0, 0.0), length, rng.uniform(-0.25, 0.25), 24)
    add_twig(bm, tint_layer, main, 0.0035 * scale, 0.0012 * scale, twig_color)
    twigs = [(main, 1.0)]
    side_count = int(13 * lush)
    for index in range(side_count):
        t = 0.08 + 0.84 * index / max(side_count - 1, 1)
        anchor = main[int(t * (len(main) - 1))]
        ahead = main[min(int(t * (len(main) - 1)) + 1, len(main) - 1)]
        axis = (ahead - anchor).normalized()
        side = 1.0 if index % 2 == 0 else -1.0
        angle = math.radians(rng.uniform(50.0, 64.0)) * side
        direction = Matrix.Rotation(angle, 3, 'Z') @ axis
        twig_length = length * (0.52 - 0.36 * t) * rng.uniform(0.85, 1.15)
        points = curve_points(anchor, direction, twig_length, -side * rng.uniform(0.4, 1.2), 12)
        add_twig(bm, tint_layer, points, 0.0022 * scale, 0.001 * scale, twig_color)
        twigs.append((points, 0.85))
        if twig_length > length * 0.16:
            for sub in range(3):
                st = 0.28 + 0.24 * sub
                sub_anchor = points[int(st * (len(points) - 1))]
                sub_axis = (points[min(int(st * (len(points) - 1)) + 1, len(points) - 1)] - sub_anchor).normalized()
                sub_side = side if sub != 1 else -side
                sub_direction = Matrix.Rotation(math.radians(48.0) * sub_side, 3, 'Z') @ sub_axis
                sub_points = curve_points(sub_anchor, sub_direction, twig_length * 0.38, 0.0, 6)
                add_twig(bm, tint_layer, sub_points, 0.0014 * scale, 0.0008 * scale, twig_color)
                twigs.append((sub_points, 0.7))
    for points, weight in twigs:
        total = sum((points[index + 1] - points[index]).length for index in range(len(points) - 1))
        spacing = 0.0021 * scale
        walked = 0.0
        index = 0
        while index < len(points) - 1:
            segment = points[index + 1] - points[index]
            if walked > segment.length:
                walked -= segment.length
                index += 1
                continue
            base = points[index] + segment.normalized() * walked
            along = segment.normalized()
            t = (sum((points[i + 1] - points[i]).length for i in range(index)) + walked) / max(total, 1e-6)
            needle_length = 0.021 * scale * weight * (0.7 + 0.3 * math.sin(math.pi * min(1.0, t * 1.3))) * rng.uniform(0.85, 1.15)
            tip_fresh = t > 0.72 and rng.random() < 0.9
            for side in (-1.0, 1.0):
                sideways = along.cross(v(0.0, 0.0, 1.0)).normalized() * side
                forward = rng.uniform(0.35, 0.65)
                direction = (sideways + along * forward + v(0.0, 0.0, rng.uniform(0.05, 0.35))).normalized()
                tint_base = dark.lerp(mid, rng.uniform(0.0, 0.7))
                tint_tip = fresh.lerp(mid, rng.uniform(0.2, 0.6)) if tip_fresh else mid.lerp(fresh, rng.uniform(0.0, 0.35))
                add_needle(bm, tint_layer, base, direction, v(0.0, 0.0, 1.0), needle_length, 0.0017 * scale, tint_base, tint_tip)
            if rng.random() < 0.55:
                direction = (along * rng.uniform(0.3, 0.6) + v(rng.uniform(-0.3, 0.3), 0.0, 1.0)).normalized()
                add_needle(bm, tint_layer, base + v(0.0, 0.0, 0.001), direction, along.cross(v(0.0, 0.0, 1.0)), needle_length * 0.8, 0.0016 * scale, dark.lerp(mid, 0.6), fresh.lerp(mid, 0.5) if tip_fresh else mid)
            walked += spacing
    mesh = bpy.data.meshes.new("spray")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("spray", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def render_pass(scene, objects, material, path, transform, samples):
    for obj in objects:
        obj.data.materials.clear()
        obj.data.materials.append(material)
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


def make_atlas():
    reset()
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    turntable.accelerate(scene)
    scene.render.resolution_x = atlas_size
    scene.render.resolution_y = atlas_size
    scene.render.film_transparent = True
    scene.cycles.use_denoising = False
    scene.cycles.filter_width = 1.0
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.look = 'None'
    world = bpy.data.worlds.new("black")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.0
    scene.world = world
    rng = random.Random(907)
    sprays = []
    for cell in range(4):
        column = cell % 2
        row = cell // 2
        center = v((column - 0.5) * cell_world, (row - 0.5) * cell_world, 0.0)
        origin = center + v(0.0, -cell_world * 0.46, 0.0)
        sprays.append(build_spray(rng, origin, 1.12 if cell < 2 else 0.95, 1.0 if cell % 2 == 0 else 0.8))
    camera_data = bpy.data.cameras.new("atlas")
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = cell_world * 2.0
    camera = bpy.data.objects.new("atlas", camera_data)
    camera.location = v(0.0, 0.0, 2.0)
    scene.collection.objects.link(camera)
    scene.camera = camera
    os.makedirs(atlas_directory, exist_ok=True)
    albedo_path = os.path.join(atlas_directory, "render_albedo.png")
    normal_path = os.path.join(atlas_directory, "render_normal.png")
    occlusion_path = os.path.join(atlas_directory, "render_occlusion.png")
    scene.render.image_settings.color_mode = 'RGBA'
    render_pass(scene, sprays, emission_material("albedo", needle_color), albedo_path, 'Standard', 32)
    render_pass(scene, sprays, emission_material("normal", normal_color), normal_path, 'Raw', 32)
    render_pass(scene, sprays, emission_material("occlusion", occlusion_color), occlusion_path, 'Raw', 96)
    albedo = load_pixels(albedo_path)
    normal = load_pixels(normal_path)
    occlusion = load_pixels(occlusion_path)
    alpha = albedo[:, :, 3]
    shade = numpy.clip(occlusion[:, :, 0] * 0.8 + 0.2, 0.0, 1.0)
    color = dilate(albedo, alpha, 24)
    color = color * shade[:, :, None] ** 0.5
    normals = dilate(normal, alpha, 24)
    arm = numpy.stack([shade, numpy.full_like(shade, 0.62), numpy.zeros_like(shade)], axis=2)
    save_pixels(os.path.join(atlas_directory, "conifer_spray_diff_2k.png"), color, 3)
    save_pixels(os.path.join(atlas_directory, "conifer_spray_alpha_2k.png"), numpy.repeat(alpha[:, :, None], 3, axis=2), 3)
    save_pixels(os.path.join(atlas_directory, "conifer_spray_nor_gl_2k.png"), normals, 3)
    save_pixels(os.path.join(atlas_directory, "conifer_spray_arm_2k.png"), arm, 3)
    preview = numpy.concatenate([color * alpha[:, :, None] + 0.15 * (1.0 - alpha[:, :, None]), numpy.ones_like(alpha)[:, :, None]], axis=2)
    save_pixels(os.path.join(preview_root, "conifer_spray_preview.png"), preview, 4)
    for path in (albedo_path, normal_path, occlusion_path):
        os.remove(path)
    print("ATLAS", atlas_directory, float(alpha.mean()))


def cell_rect(cell):
    column = cell % 2
    row = cell // 2
    return column * 0.5, row * 0.5


def add_card(bm, uv_layer, frame, width, cell, droop, normal_bias, crown_axis, detail=True):
    base, forward, right, up = frame
    u0, v0 = cell_rect(cell)
    rows = []
    levels = (-0.04, 0.46, 0.96) if detail else (-0.04, 0.96)
    for row, local_y in enumerate(levels):
        sag = droop * (local_y + 0.04) ** 1.7
        row_verts = []
        for local_x in (-0.5, 0.5):
            point = base + forward * (local_y * width) + right * (local_x * width) - up * (sag * width)
            row_verts.append((bm.verts.new(point), (u0 + (local_x + 0.5) * 0.5, v0 + (local_y + 0.04) * 0.5)))
        rows.append(row_verts)
    faces = []
    for row in range(len(levels) - 1):
        a, auv = rows[row][0]
        b, buv = rows[row][1]
        c, cuv = rows[row + 1][1]
        d, duv = rows[row + 1][0]
        face = bm.faces.new((a, b, c, d))
        for loop, uv in zip(face.loops, (auv, buv, cuv, duv)):
            loop[uv_layer].uv = uv
        faces.append(face)
    for face in faces:
        for vert in face.verts:
            radial = vert.co - crown_axis(vert.co.z)
            radial.z = 0.0
            outward = radial.normalized() if radial.length > 1e-4 else Vector((0.0, 0.0, 1.0))
            normal_bias[vert] = (outward * 0.62 + up * 0.38 + Vector((0.0, 0.0, 0.25))).normalized()
    return faces


def add_tube(bm, uv_layer, points, radii, sides, tile):
    rings = []
    along = 0.0
    for index, point in enumerate(points):
        if index:
            along += (point - points[index - 1]).length
        ahead = points[min(index + 1, len(points) - 1)]
        behind = points[max(index - 1, 0)]
        tangent = (ahead - behind).normalized()
        reference = Vector((0.0, 0.0, 1.0)) if abs(tangent.z) < 0.95 else Vector((1.0, 0.0, 0.0))
        side = tangent.cross(reference).normalized()
        normal = side.cross(tangent).normalized()
        ring = []
        for step in range(sides + 1):
            angle = math.tau * step / sides
            offset = (side * math.cos(angle) + normal * math.sin(angle)) * radii[index]
            ring.append((bm.verts.new(point + offset), (step / sides, along / tile)))
        rings.append(ring)
    for index in range(len(rings) - 1):
        for step in range(sides):
            a, auv = rings[index][step]
            b, buv = rings[index][step + 1]
            c, cuv = rings[index + 1][step + 1]
            d, duv = rings[index + 1][step]
            face = bm.faces.new((a, b, c, d))
            for loop, uv in zip(face.loops, (auv, buv, cuv, duv)):
                loop[uv_layer].uv = uv


def card_frame(base, direction, roll, pitch):
    forward = direction.normalized()
    forward = (forward + Vector((0.0, 0.0, -math.sin(pitch)))).normalized()
    right = forward.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-4:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(forward).normalized()
    rotation = Matrix.Rotation(roll, 3, forward)
    return base, forward, rotation @ right, rotation @ up


def point_on(points, s):
    index = min(int(s * (len(points) - 1)), len(points) - 2)
    local = s * (len(points) - 1) - index
    return points[index].lerp(points[index + 1], local), (points[index + 1] - points[index]).normalized()


def add_sprays(foliage, uv, normals, axis, points, length, t, begin, spacing, size_scale, rng, tip, lod=0):
    walked = begin
    while walked <= 1.0:
        base, along = point_on(points, walked)
        for side in (-1.0, 1.0):
            spread = math.radians(rng.uniform(35.0, 70.0)) * side
            direction = Matrix.Rotation(spread, 3, 'Z') @ along
            frame = card_frame(base, direction, rng.uniform(-0.95, 0.95), rng.uniform(-0.1, 0.35))
            size = rng.uniform(0.42, 0.66) * size_scale * (0.75 + 0.35 * (1.0 - t))
            add_card(foliage, uv, frame, size, rng.randint(0, 3), rng.uniform(0.05, 0.3), normals, axis, lod == 0)
        if rng.random() < 0.45 and lod < 2:
            frame = card_frame(base, along, rng.uniform(-1.3, 1.3), rng.uniform(-0.4, 0.2))
            add_card(foliage, uv, frame, rng.uniform(0.35, 0.55) * size_scale, rng.randint(0, 3), rng.uniform(0.1, 0.35), normals, axis, lod == 0)
        walked += spacing / max(length, 0.5)
    if tip:
        base, along = point_on(points, 0.97)
        frame = card_frame(base - along * 0.1, along, rng.uniform(-0.6, 0.6), rng.uniform(-0.2, 0.1))
        add_card(foliage, uv, frame, rng.uniform(0.45, 0.6) * size_scale, rng.randint(0, 3), 0.1, normals, axis, lod == 0)


def fir(seed, lod):
    far = lod > 0
    rng = random.Random(seed)
    height = rng.uniform(13.0, 20.0)
    base_radius = 0.14 + height * 0.011
    crown_base = height * rng.uniform(0.1, 0.22)
    lean = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3))
    phase_seed = rng.uniform(0.0, 10.0)

    def axis(h):
        t = max(h, 0.0) / height
        return Vector((lean[0] * t * t + 0.05 * math.sin(h * 0.9 + phase_seed), lean[1] * t * t + 0.05 * math.cos(h * 0.7 + phase_seed), h))

    def radius(h):
        t = max(h, 0.0) / height
        flare = max(0.0, 1.0 - max(h, 0.0) / 1.1) ** 2
        return (base_radius + (0.018 - base_radius) * t ** 0.8) * (1.0 + flare * 0.85)

    bark = bmesh.new()
    bark_uv = bark.loops.layers.uv.new("UVMap")
    foliage = bmesh.new()
    foliage_uv = foliage.loops.layers.uv.new("UVMap")
    normals = {}
    sides = (16, 7, 5)[lod]
    rings = (34, 8, 5)[lod]
    heights = [-0.6] + [height * (index / rings) ** 1.15 for index in range(0, rings + 1)]
    trunk_rings = []
    for index, h in enumerate(heights):
        center = axis(h)
        flare = max(0.0, 1.0 - max(h, 0.0) / 1.1) ** 2
        ring = []
        for step in range(sides + 1):
            angle = math.tau * step / sides
            lobes = 1.0 + flare * 0.32 * (0.5 + 0.5 * math.cos(angle * 5.0 + phase_seed)) - flare * 0.12
            r = radius(h) * lobes
            ring.append((bark.verts.new(center + Vector((math.cos(angle) * r, math.sin(angle) * r, 0.0))), (step / sides * 2.0, h / 1.6)))
        trunk_rings.append(ring)
    for index in range(len(trunk_rings) - 1):
        for step in range(sides):
            a, auv = trunk_rings[index][step]
            b, buv = trunk_rings[index][step + 1]
            c, cuv = trunk_rings[index + 1][step + 1]
            d, duv = trunk_rings[index + 1][step]
            face = bark.faces.new((a, b, c, d))
            for loop, uv in zip(face.loops, (auv, buv, cuv, duv)):
                loop[bark_uv].uv = uv
    stub = 0.6
    while stub < crown_base and far is False:
        for count in range(rng.randint(2, 4)):
            yaw = rng.uniform(0.0, math.tau)
            direction = Vector((math.cos(yaw), math.sin(yaw), rng.uniform(-0.5, 0.1))).normalized()
            start = axis(stub) + Vector((math.cos(yaw), math.sin(yaw), 0.0)) * radius(stub) * 0.8
            length = rng.uniform(0.2, 0.7)
            add_tube(bark, bark_uv, [start, start + direction * length * 0.5, start + direction * length + Vector((0.0, 0.0, -0.05))], [0.02, 0.012, 0.004], 4, 1.2)
        stub += rng.uniform(0.35, 0.7)
    whorl = crown_base
    phase = rng.uniform(0.0, math.tau)
    spacing = (0.14, 0.3, 0.72)[lod]
    size_scale = (1.0, 2.05, 4.2)[lod]
    while whorl < height - 0.35:
        t = (whorl - crown_base) / (height - crown_base)
        count = rng.randint(5, 7) if far is False else 5
        for branch in range(count):
            yaw = phase + math.tau * branch / count + rng.uniform(-0.25, 0.25)
            horizontal = Vector((math.cos(yaw), math.sin(yaw), 0.0))
            length = (1.0 - t) ** 0.92 * height * 0.2 + 0.35
            length *= rng.uniform(0.85, 1.12)
            pitch = -0.35 + 0.75 * t + rng.uniform(-0.08, 0.08)
            droop = (0.35 - 0.3 * t) * rng.uniform(0.8, 1.2)
            start = axis(whorl) + horizontal * radius(whorl) * 0.7
            points = []
            for step in range(7):
                s = step / 6.0
                points.append(start + horizontal * length * s + Vector((0.0, 0.0, length * (math.sin(pitch) * s - droop * s * s + 0.18 * s ** 3))))
            if far is False or (t < 0.4 and lod == 1):
                add_tube(bark, bark_uv, points, [0.012 + length * 0.011 - (0.012 + length * 0.011 - 0.004) * s for s in (0.0, 0.17, 0.33, 0.5, 0.67, 0.83, 1.0)], 4 if far is False else 3, 1.4)
            begin = 0.18 if t > 0.3 else 0.4
            add_sprays(foliage, foliage_uv, normals, axis, points, length, t, begin, spacing, size_scale, rng, lod < 2, lod)
            if length > 1.3 and far is False:
                for sub in range(rng.randint(2, 4)):
                    s0 = rng.uniform(0.3, 0.75)
                    base, along = point_on(points, s0)
                    side = 1.0 if sub % 2 == 0 else -1.0
                    direction = Matrix.Rotation(math.radians(rng.uniform(38.0, 60.0)) * side, 3, 'Z') @ along
                    sub_length = length * rng.uniform(0.25, 0.4) * (1.0 - s0 * 0.5)
                    sub_points = [base + direction * sub_length * (step / 4.0) + Vector((0.0, 0.0, -sub_length * 0.12 * (step / 4.0) ** 2)) for step in range(5)]
                    add_tube(bark, bark_uv, sub_points, [0.008, 0.006, 0.005, 0.004, 0.003], 3, 1.0)
                    add_sprays(foliage, foliage_uv, normals, axis, sub_points, sub_length, t, 0.2, spacing * 1.1, size_scale * 0.9, rng, True)
        phase += 0.9 + rng.uniform(0.0, 0.4)
        whorl += rng.uniform(*((0.42, 0.62), (0.55, 0.7), (0.9, 1.15))[lod])
    top = axis(height - 0.2)
    for index in range((3, 2, 1)[lod]):
        yaw = math.tau * index / 3.0
        frame = card_frame(top - Vector((0.0, 0.0, 0.5)), Vector((math.cos(yaw) * 0.25, math.sin(yaw) * 0.25, 1.0)), rng.uniform(-0.5, 0.5), 0.0)
        add_card(foliage, foliage_uv, frame, 0.8 * min(size_scale, 2.0), rng.randint(0, 3), 0.0, normals, axis, lod == 0)
    return bark, foliage, normals, height


def shadow_fir(seed):
    rng = random.Random(seed)
    height = rng.uniform(13.0, 20.0)
    base_radius = 0.14 + height * 0.011
    crown_base = height * rng.uniform(0.1, 0.22)
    lean = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3))
    phase_seed = rng.uniform(0.0, 10.0)

    def axis(h):
        t = max(h, 0.0) / height
        return Vector((lean[0] * t * t + 0.05 * math.sin(h * 0.9 + phase_seed), lean[1] * t * t + 0.05 * math.cos(h * 0.7 + phase_seed), h))

    def crown(h):
        t = max(0.0, min(1.0, (h - crown_base) / (height - crown_base)))
        return (0.22 * height + 0.75) * (1.0 - t) ** 0.92 + 0.3

    bark = bmesh.new()
    bark_uv = bark.loops.layers.uv.new("UVMap")
    foliage = bmesh.new()
    foliage_uv = foliage.loops.layers.uv.new("UVMap")
    normals = {}
    add_tube(bark, bark_uv, [axis(-0.6), axis(crown_base), axis(height * 0.6)], [base_radius * 1.3, base_radius * 0.8, base_radius * 0.4], 5, 1.6)
    for layer, (inset, card) in enumerate(((0.92, 2.4), (0.55, 2.0))):
        h = crown_base + 0.4
        ring = 0
        while h < height - 0.6:
            radius = crown(h) * inset
            count = max(3, int(math.ceil(math.tau * radius / (card * 0.8))))
            below = crown(h - 1.0) * inset
            for index in range(count):
                angle = math.tau * (index + 0.5 * (ring % 2)) / count + layer * 0.4
                outward = Vector((math.cos(angle), math.sin(angle), 0.0))
                tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
                slant = (outward * (below - radius) - Vector((0.0, 0.0, 1.0))).normalized()
                center = axis(h) + outward * radius
                forward = -slant
                up = forward.cross(tangent).normalized()
                frame = (center - forward * (card * 0.5), forward, tangent, up)
                add_card(foliage, foliage_uv, frame, card * rng.uniform(0.9, 1.1), rng.randint(0, 3), 0.0, normals, axis, False)
            h += card * 0.62
            ring += 1
    return bark, foliage, normals, height


def snag(seed):
    rng = random.Random(seed)
    height = rng.uniform(8.0, 13.0)
    base_radius = 0.19 + height * 0.015
    lean = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3))
    phase_seed = rng.uniform(0.0, 10.0)
    top = height * rng.uniform(0.8, 0.97)

    def axis(h):
        t = max(h, 0.0) / height
        return Vector((lean[0] * t * t + 0.09 * math.sin(h * 0.7 + phase_seed), lean[1] * t * t + 0.09 * math.cos(h * 0.55 + phase_seed), h))

    def radius(h):
        t = max(h, 0.0) / height
        flare = max(0.0, 1.0 - max(h, 0.0) / 1.7) ** 2.5
        return (base_radius + (0.06 - base_radius) * t ** 0.8) * (1.0 + flare * 0.55)

    bark = bmesh.new()
    bark_uv = bark.loops.layers.uv.new("UVMap")
    sides = 12
    count = 26
    heights = [-0.6] + [top * (index / count) ** 1.1 for index in range(count + 1)]
    lifts = [rng.uniform(-0.12, 0.5) for step in range(sides)]
    rings = []
    for index, h in enumerate(heights):
        center = axis(h)
        flare = max(0.0, 1.0 - max(h, 0.0) / 1.2) ** 2
        ring = []
        for step in range(sides + 1):
            angle = math.tau * step / sides
            lobes = 1.0 + flare * 0.35 * (0.5 + 0.5 * math.cos(angle * 5.0 + phase_seed)) - flare * 0.12
            gnarl = 1.0 + 0.05 * math.sin(angle * 3.0 + h * 1.7 + phase_seed)
            r = radius(h) * lobes * gnarl
            lift = lifts[step % sides] if index == len(heights) - 1 else 0.0
            ring.append((bark.verts.new(center + Vector((math.cos(angle) * r, math.sin(angle) * r, lift))), (step / sides * 2.0, (h + lift) / 1.6)))
        rings.append(ring)
    for index in range(len(rings) - 1):
        for step in range(sides):
            a, auv = rings[index][step]
            b, buv = rings[index][step + 1]
            c, cuv = rings[index + 1][step + 1]
            d, duv = rings[index + 1][step]
            face = bark.faces.new((a, b, c, d))
            for loop, coordinate in zip(face.loops, (auv, buv, cuv, duv)):
                loop[bark_uv].uv = coordinate
    rim = rings[-1]
    hollow = bark.verts.new(axis(top) + Vector((0.0, 0.0, 0.05)))
    for step in range(sides):
        a, auv = rim[step]
        b, buv = rim[step + 1]
        face = bark.faces.new((a, b, hollow))
        for loop, coordinate in zip(face.loops, (auv, buv, (auv[0], auv[1] + 0.1))):
            loop[bark_uv].uv = coordinate
    whorl = top * rng.uniform(0.14, 0.24)
    phase = rng.uniform(0.0, math.tau)
    while whorl < top - 0.3:
        t = whorl / top
        count = rng.randint(3, 5)
        for branch in range(count):
            yaw = phase + math.tau * branch / count + rng.uniform(-0.35, 0.35)
            horizontal = Vector((math.cos(yaw), math.sin(yaw), 0.0))
            side = Vector((-horizontal.y, horizontal.x, 0.0))
            length = rng.uniform(0.9, 3.1) * (1.0 - t * 0.6)
            if rng.random() < 0.25:
                length *= rng.uniform(0.12, 0.3)
            rise = rng.uniform(-0.15, 0.25) + 0.5 * t
            droop = rng.uniform(0.25, 0.6) * (1.0 - t)
            wiggle = rng.uniform(-0.12, 0.12)
            start = axis(whorl) + horizontal * radius(whorl) * 0.75
            points = []
            for step in range(8):
                s = step / 7.0
                points.append(start + horizontal * length * s + side * wiggle * length * math.sin(s * math.pi) + Vector((0.0, 0.0, length * (rise * s - droop * s * s))))
            thick = 0.028 + length * 0.014
            add_tube(bark, bark_uv, points, [thick - (thick - 0.005) * (step / 7.0) ** 0.8 for step in range(8)], 5, 1.2)
            if length > 0.8:
                for twig in range(rng.randint(3, 6)):
                    s0 = rng.uniform(0.25, 0.9)
                    base, along = point_on(points, s0)
                    direction = (Matrix.Rotation(rng.uniform(0.45, 1.1) * (1 if twig % 2 else -1), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.35, 0.45)))).normalized()
                    twig_length = length * rng.uniform(0.18, 0.38) * (1.0 - s0 * 0.4)
                    tip = base + direction * twig_length + Vector((0.0, 0.0, -0.08 * twig_length))
                    add_tube(bark, bark_uv, [base, base + direction * twig_length * 0.5, tip], [0.011, 0.007, 0.0025], 4, 1.0)
                    if twig_length > 0.3:
                        for fork in range(2):
                            fork_base = base.lerp(tip, rng.uniform(0.4, 0.8))
                            fork_direction = (Matrix.Rotation(rng.uniform(0.5, 0.9) * (1 if fork else -1), 3, 'Z') @ direction).normalized()
                            add_tube(bark, bark_uv, [fork_base, fork_base + fork_direction * twig_length * 0.35], [0.005, 0.002], 3, 1.0)
        phase += 0.9 + rng.uniform(0.0, 0.5)
        whorl += rng.uniform(0.35, 0.7)
    stub = 0.7
    while stub < top * 0.25:
        yaw = rng.uniform(0.0, math.tau)
        direction = Vector((math.cos(yaw), math.sin(yaw), rng.uniform(-0.4, 0.2))).normalized()
        start = axis(stub) + Vector((math.cos(yaw), math.sin(yaw), 0.0)) * radius(stub) * 0.8
        length = rng.uniform(0.15, 0.5)
        add_tube(bark, bark_uv, [start, start + direction * length * 0.5, start + direction * length], [0.035, 0.022, 0.008], 5, 1.2)
        stub += rng.uniform(0.4, 0.9)
    return bark


def make_snags(count, preview):
    for variant in range(count):
        reset()
        name = "tree_dead_%d" % variant
        bark = snag(7717 + variant * 104729)
        mesh = bpy.data.meshes.new(name)
        bark.to_mesh(mesh)
        bark.free()
        mesh.materials.append(bark_material())
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new("trunk", mesh)
        bpy.context.scene.collection.objects.link(obj)
        if preview:
            turntable.render_views([obj], preview_root, name, ["side"], 24, os.path.join(os.path.dirname(output_root), "hdri", "kloofendal_overcast_puresky_4k.hdr"), (900, 1400))
        export_tree(name, [obj])


def bark_material():
    material = bpy.data.materials.new("bark")
    material.use_nodes = True
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = bpy.data.images.load(os.path.join(bark_directory, "fir_tree_01_bark_diff_2k.jpg"), check_existing=True)
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    normal_image = tree.nodes.new('ShaderNodeTexImage')
    normal_image.image = bpy.data.images.load(os.path.join(bark_directory, "fir_tree_01_bark_nor_gl_2k.jpg"), check_existing=True)
    normal_image.image.colorspace_settings.name = 'Non-Color'
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(normal_image.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    shader.inputs['Roughness'].default_value = 0.85
    return material


def spray_material():
    material = bpy.data.materials.new("spray")
    material.use_nodes = True
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = bpy.data.images.load(os.path.join(atlas_directory, "conifer_spray_diff_2k.png"), check_existing=True)
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    alpha = tree.nodes.new('ShaderNodeTexImage')
    alpha.image = bpy.data.images.load(os.path.join(atlas_directory, "conifer_spray_alpha_2k.png"), check_existing=True)
    alpha.image.colorspace_settings.name = 'Non-Color'
    tree.links.new(alpha.outputs['Color'], shader.inputs['Alpha'])
    normal_image = tree.nodes.new('ShaderNodeTexImage')
    normal_image.image = bpy.data.images.load(os.path.join(atlas_directory, "conifer_spray_nor_gl_2k.png"), check_existing=True)
    normal_image.image.colorspace_settings.name = 'Non-Color'
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(normal_image.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    shader.inputs['Roughness'].default_value = 0.62
    return material


def finish_tree(name, bark, foliage, normals):
    materials = [bark_material(), spray_material()]
    bark_mesh = bpy.data.meshes.new(name + "_bark")
    bark.to_mesh(bark_mesh)
    bark.free()
    foliage.verts.index_update()
    foliage_normals = [normals.get(vert, Vector((0.0, 0.0, 1.0))) for vert in foliage.verts]
    foliage_mesh = bpy.data.meshes.new(name + "_foliage")
    foliage.to_mesh(foliage_mesh)
    foliage.free()
    bark_mesh.materials.append(materials[0])
    foliage_mesh.materials.append(materials[1])
    for polygon in bark_mesh.polygons:
        polygon.use_smooth = True
    for polygon in foliage_mesh.polygons:
        polygon.use_smooth = True
    foliage_mesh.normals_split_custom_set_from_vertices(foliage_normals)
    objects = []
    for mesh, part in ((bark_mesh, "trunk"), (foliage_mesh, "foliage")):
        obj = bpy.data.objects.new(part, mesh)
        bpy.context.scene.collection.objects.link(obj)
        objects.append(obj)
    return objects


def export_tree(name, objects):
    directory = os.path.join(output_root, name)
    os.makedirs(directory, exist_ok=True)
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in objects)
    for material in bpy.data.materials:
        if material.node_tree:
            shader = next((node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
            if shader:
                for link in list(shader.inputs['Alpha'].links):
                    material.node_tree.links.remove(link)
    path = os.path.join(directory, name + ".gltf")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_keep_originals=True, export_yup=True, export_apply=True, export_skins=False, export_animations=False, export_morph=False, export_cameras=False, export_lights=False, export_extras=False)
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    for material in document.get("materials", []):
        if material.get("name") == "spray":
            material["alphaMode"] = "MASK"
            material["alphaCutoff"] = 0.5
            material["doubleSided"] = True
    for image in document.get("images", []):
        if "uri" in image:
            source = image["uri"]
            if os.path.isabs(source) is False:
                source = os.path.normpath(os.path.join(directory, source))
            image["uri"] = os.path.relpath(source, directory).replace("\\", "/")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    print("EXPORTED", name, sum(len(o.data.polygons) for o in objects))


def pass_material(name, kind, image_path, alpha_path):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    if kind == "albedo":
        color = tree.nodes.new('ShaderNodeTexImage')
        color.image = bpy.data.images.load(image_path, check_existing=True)
        surface = tree.nodes.new('ShaderNodeEmission')
        tree.links.new(color.outputs['Color'], surface.inputs['Color'])
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
        combine = tree.nodes.new('ShaderNodeCombineXYZ')
        for axis in ("X", "Y", "Z"):
            dot = tree.nodes.new('ShaderNodeVectorMath')
            dot.operation = 'DOT_PRODUCT'
            dot.name = "axis_" + axis
            tree.links.new(flip.outputs['Vector'], dot.inputs[0])
            tree.links.new(dot.outputs['Value'], combine.inputs[axis])
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
    if alpha_path:
        alpha = tree.nodes.new('ShaderNodeTexImage')
        alpha.image = bpy.data.images.load(alpha_path, check_existing=True)
        alpha.image.colorspace_settings.name = 'Non-Color'
        cut = tree.nodes.new('ShaderNodeMath')
        cut.operation = 'GREATER_THAN'
        cut.inputs[1].default_value = 0.5
        tree.links.new(alpha.outputs['Color'], cut.inputs[0])
        hole = tree.nodes.new('ShaderNodeBsdfTransparent')
        mix = tree.nodes.new('ShaderNodeMixShader')
        tree.links.new(cut.outputs['Value'], mix.inputs['Fac'])
        tree.links.new(hole.outputs['BSDF'], mix.inputs[1])
        tree.links.new(shader, mix.inputs[2])
        shader = mix.outputs['Shader']
    tree.links.new(shader, output.inputs['Surface'])
    return material


def tree_bounds(objects):
    radius = 0.0
    low = 1e9
    high = -1e9
    for obj in objects:
        for vert in obj.data.vertices:
            radius = max(radius, math.hypot(vert.co.x, vert.co.y))
            low = min(low, vert.co.z)
            high = max(high, vert.co.z)
    return radius, low, high


def write_quad(name, stem, width, bottom, top):
    directory = os.path.join(output_root, name)
    os.makedirs(directory, exist_ok=True)
    half = width * 0.5
    positions = [(-half, bottom, 0.0), (half, bottom, 0.0), (half, top, 0.0), (-half, top, 0.0)]
    normals = [(0.0, 0.0, -1.0)] * 4
    uvs = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    blob = struct.pack("<12f", *[c for p in positions for c in p]) + struct.pack("<12f", *[c for n in normals for c in n]) + struct.pack("<8f", *[c for u in uvs for c in u]) + struct.pack("<6I", 0, 1, 2, 0, 2, 3)
    with open(os.path.join(directory, name + ".bin"), "wb") as handle:
        handle.write(blob)
    relative = os.path.relpath(impostor_directory, directory).replace("\\", "/")
    document = {
        "asset": {"version": "2.0", "generator": "zero point impostor"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "impostor", "mesh": 0}],
        "meshes": [{"name": "impostor", "primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]}],
        "materials": [{"name": "impostor", "alphaMode": "MASK", "alphaCutoff": 0.5, "doubleSided": True, "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicRoughnessTexture": {"index": 2}, "metallicFactor": 0.0, "roughnessFactor": 1.0}, "normalTexture": {"index": 1}, "occlusionTexture": {"index": 2}}],
        "textures": [{"source": 0}, {"source": 1}, {"source": 2}],
        "images": [{"uri": relative + "/" + stem + "_diff_1k.png"}, {"uri": relative + "/" + stem + "_nor_gl_1k.png"}, {"uri": relative + "/" + stem + "_arm_1k.png"}],
        "buffers": [{"uri": name + ".bin", "byteLength": len(blob)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 48}, {"buffer": 0, "byteOffset": 96, "byteLength": 32}, {"buffer": 0, "byteOffset": 128, "byteLength": 24}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-half, bottom, 0.0], "max": [half, top, 0.0]}, {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"}, {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC2"}, {"bufferView": 3, "componentType": 5125, "count": 6, "type": "SCALAR"}],
    }
    with open(os.path.join(directory, name + ".gltf"), "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)


def make_impostor(variant):
    reset()
    bark, foliage, normals, height = fir(1301 + variant * 7919, 0)
    objects = finish_tree("impostor", bark, foliage, normals)
    radius, low, high = tree_bounds(objects)
    width = radius * 2.0 * 1.05
    tall = (high - low) * 1.03
    if tall < width * 2.0:
        tall = width * 2.0
    width = tall * 0.5
    bottom = (low + high) * 0.5 - tall * 0.5
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    turntable.accelerate(scene)
    scene.render.resolution_x = impostor_cell[0]
    scene.render.resolution_y = impostor_cell[1]
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
    scene.cycles.use_denoising = False
    scene.cycles.transparent_max_bounces = 96
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.look = 'None'
    world = bpy.data.worlds.new("impostor")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    scene.world = world
    spray_diffuse = os.path.join(atlas_directory, "conifer_spray_diff_2k.png")
    spray_alpha = os.path.join(atlas_directory, "conifer_spray_alpha_2k.png")
    bark_diffuse = os.path.join(bark_directory, "fir_tree_01_bark_diff_2k.jpg")
    passes = [
        ("albedo", pass_material("albedo_bark", "albedo", bark_diffuse, None), pass_material("albedo_leaf", "albedo", spray_diffuse, spray_alpha), 'Standard', 24, 0.0),
        ("normal", pass_material("normal_bark", "normal", None, None), pass_material("normal_leaf", "normal", None, spray_alpha), 'Raw', 24, 0.0),
        ("occlusion", pass_material("occlusion_bark", "occlusion", None, None), pass_material("occlusion_leaf", "occlusion", None, spray_alpha), 'Raw', 160, 1.0),
    ]
    camera_data = bpy.data.cameras.new("impostor")
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = tall
    camera_data.clip_start = 0.1
    camera_data.clip_end = 400.0
    camera = bpy.data.objects.new("impostor", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    size = (impostor_cell[1] * 2, impostor_cell[0] * impostor_columns)
    color_atlas = numpy.zeros((size[0], size[1], 3), dtype=numpy.float32)
    normal_atlas = numpy.zeros((size[0], size[1], 3), dtype=numpy.float32)
    occlusion_atlas = numpy.ones((size[0], size[1], 3), dtype=numpy.float32)
    alpha_atlas = numpy.zeros((size[0], size[1]), dtype=numpy.float32)
    center = Vector((0.0, 0.0, bottom + tall * 0.5))
    scratch = os.path.join(preview_root, "impostor_frame.png")
    for frame in range(impostor_frames):
        angle = math.tau * frame / impostor_frames
        toward = Vector((math.sin(angle), math.cos(angle), 0.0))
        right = Vector((-math.cos(angle), math.sin(angle), 0.0))
        up = Vector((0.0, 0.0, 1.0))
        camera.location = center + toward * 150.0
        camera.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
        results = {}
        for name, bark_pass, leaf_pass, transform, samples, strength in passes:
            for axis_name, axis in (("axis_X", right), ("axis_Y", up), ("axis_Z", toward)):
                for material in (bark_pass, leaf_pass):
                    if axis_name in material.node_tree.nodes:
                        material.node_tree.nodes[axis_name].inputs[1].default_value = axis
            objects[0].data.materials.clear()
            objects[0].data.materials.append(bark_pass)
            objects[1].data.materials.clear()
            objects[1].data.materials.append(leaf_pass)
            background.inputs['Strength'].default_value = strength
            scene.view_settings.view_transform = transform
            scene.cycles.samples = samples
            scene.render.filepath = scratch
            bpy.ops.render.render(write_still=True)
            results[name] = load_pixels(scratch)
        alpha = results["albedo"][:, :, 3]
        column = frame % impostor_columns
        row = 1 - frame // impostor_columns
        rows = slice(row * impostor_cell[1], (row + 1) * impostor_cell[1])
        columns = slice(column * impostor_cell[0], (column + 1) * impostor_cell[0])
        color_atlas[rows, columns] = dilate(results["albedo"], alpha, 20)
        normal_atlas[rows, columns] = dilate(results["normal"], alpha, 20)
        occlusion_atlas[rows, columns] = dilate(results["occlusion"], alpha, 20)
        alpha_atlas[rows, columns] = alpha
        print("FRAME", variant, frame)
    os.remove(scratch)
    shade = numpy.clip(occlusion_atlas[:, :, 0], 0.0, 1.0)
    arm = numpy.stack([0.3 + 0.7 * shade, numpy.full_like(shade, 0.78), numpy.zeros_like(shade)], axis=2)
    stem = "conifer_fir_%d_impostor" % variant
    os.makedirs(impostor_directory, exist_ok=True)
    save_pixels(os.path.join(impostor_directory, stem + "_diff_1k.png"), color_atlas, 3)
    save_pixels(os.path.join(impostor_directory, stem + "_alpha_1k.png"), numpy.repeat(alpha_atlas[:, :, None], 3, axis=2), 3)
    save_pixels(os.path.join(impostor_directory, stem + "_nor_gl_1k.png"), normal_atlas, 3)
    save_pixels(os.path.join(impostor_directory, stem + "_arm_1k.png"), arm, 3)
    preview = numpy.concatenate([color_atlas * shade[:, :, None] * alpha_atlas[:, :, None] + 0.2 * (1.0 - alpha_atlas[:, :, None]), numpy.ones_like(alpha_atlas)[:, :, None]], axis=2)
    save_pixels(os.path.join(preview_root, stem + "_preview.png"), preview, 4)
    save_pixels(os.path.join(preview_root, stem + "_normals.png"), numpy.concatenate([normal_atlas * alpha_atlas[:, :, None], numpy.ones_like(alpha_atlas)[:, :, None]], axis=2), 4)
    write_quad(stem, stem, width, bottom, bottom + tall)
    print("IMPOSTOR", stem, round(width, 3), round(bottom, 3), round(bottom + tall, 3), float(alpha_atlas.mean()))


def make_trees(count, preview):
    for variant in range(count):
        for lod in (0, 1, 2):
            reset()
            name = "conifer_fir_%d%s" % (variant, ("", "_far", "_shadow")[lod])
            bark, foliage, normals, height = fir(1301 + variant * 7919, lod) if lod < 2 else shadow_fir(1301 + variant * 7919)
            objects = finish_tree(name, bark, foliage, normals)
            if preview and variant < 1:
                turntable.render_views(objects, preview_root, name, ["side", "wide"], 24, os.path.join(os.path.dirname(output_root), "hdri", "kloofendal_overcast_puresky_4k.hdr"), (1200, 1600))
            export_tree(name, objects)


if mode == "atlas":
    make_atlas()

elif mode == "trees":
    make_trees(int(arguments[4]) if len(arguments) > 4 else 6, True)

elif mode == "impostors":
    for variant in range(int(arguments[4]) if len(arguments) > 4 else 6):
        make_impostor(variant)

elif mode == "snags":
    make_snags(int(arguments[4]) if len(arguments) > 4 else 3, True)
