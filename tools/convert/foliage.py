import bpy
import bmesh
import math
import os
import sys
import numpy
from mathutils import Vector, Matrix

arguments = sys.argv[sys.argv.index("--") + 1:]
source_root = arguments[0]
output_root = arguments[1]
preview_root = arguments[2] if len(arguments) > 2 else ""

atlas_size = 2048
cell_size = atlas_size // 2
sprites = [(0.31, 0.41, 0.638, 0.77), (0.64, 0.456, 0.952, 0.826), (0.655, 0.046, 0.933, 0.366), (0.192, 0.05, 0.425, 0.309), (0.497, 0.265, 0.628, 0.397)]
stick = (0.29, 0.86, 0.96, 0.975)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path, colorspace):
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = colorspace
    return image


def twig_material(textures):
    material = bpy.data.materials.new("twig")
    material.use_nodes = True
    tree = material.node_tree
    nodes = tree.nodes
    for node in list(nodes):
        nodes.remove(node)
    output = nodes.new('ShaderNodeOutputMaterial')
    coordinate = nodes.new('ShaderNodeUVMap')
    color = nodes.new('ShaderNodeTexImage')
    color.image = textures["diff"]
    alpha = nodes.new('ShaderNodeTexImage')
    alpha.image = textures["alpha"]
    normal_texture = nodes.new('ShaderNodeTexImage')
    normal_texture.image = textures["nor"]
    for node in (color, alpha, normal_texture):
        node.interpolation = 'Cubic'
        tree.links.new(coordinate.outputs['UV'], node.inputs['Vector'])
    normal_map = nodes.new('ShaderNodeNormalMap')
    tree.links.new(normal_texture.outputs['Color'], normal_map.inputs['Color'])
    back = nodes.new('ShaderNodeNewGeometry')
    flip = nodes.new('ShaderNodeVectorMath')
    flip.operation = 'MULTIPLY'
    tree.links.new(normal_map.outputs['Normal'], flip.inputs[0])
    side = nodes.new('ShaderNodeMath')
    side.operation = 'MULTIPLY_ADD'
    side.inputs[1].default_value = -2.0
    side.inputs[2].default_value = 1.0
    tree.links.new(back.outputs['Backfacing'], side.inputs[0])
    combine = nodes.new('ShaderNodeCombineXYZ')
    for axis in ('X', 'Y', 'Z'):
        tree.links.new(side.outputs['Value'], combine.inputs[axis])
    tree.links.new(combine.outputs['Vector'], flip.inputs[1])
    encode = nodes.new('ShaderNodeVectorMath')
    encode.operation = 'MULTIPLY_ADD'
    encode.inputs[1].default_value = (0.5, 0.5, 0.5)
    encode.inputs[2].default_value = (0.5, 0.5, 0.5)
    tree.links.new(flip.outputs['Vector'], encode.inputs[0])
    occlusion = nodes.new('ShaderNodeAmbientOcclusion')
    occlusion.samples = 24
    occlusion.inputs['Distance'].default_value = 0.09
    shade = nodes.new('ShaderNodeMix')
    shade.data_type = 'RGBA'
    shade.blend_type = 'MULTIPLY'
    tree.links.new(color.outputs['Color'], shade.inputs[6])
    tree.links.new(occlusion.outputs['AO'], shade.inputs[0])
    shade.inputs[7].default_value = (0.5, 0.5, 0.5, 1.0)
    emission = nodes.new('ShaderNodeEmission')
    emission.name = "emission"
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    cutoff = nodes.new('ShaderNodeMath')
    cutoff.operation = 'GREATER_THAN'
    cutoff.inputs[1].default_value = 0.5
    tree.links.new(alpha.outputs['Color'], cutoff.inputs[0])
    blend = nodes.new('ShaderNodeMixShader')
    tree.links.new(cutoff.outputs['Value'], blend.inputs['Fac'])
    tree.links.new(transparent.outputs['BSDF'], blend.inputs[1])
    tree.links.new(emission.outputs['Emission'], blend.inputs[2])
    tree.links.new(blend.outputs['Shader'], output.inputs['Surface'])
    material["color"] = color.name
    material["encode"] = encode.name
    material["shade"] = shade.name
    material["occlusion"] = occlusion.name
    return material


def set_pass(material, name):
    tree = material.node_tree
    emission = tree.nodes["emission"]
    for link in list(emission.inputs['Color'].links):
        tree.links.remove(link)
    if name == "color":
        tree.links.new(tree.nodes[material["color"]].outputs['Color'], emission.inputs['Color'])
    elif name == "normal":
        tree.links.new(tree.nodes[material["encode"]].outputs['Vector'], emission.inputs['Color'])
    else:
        tree.links.new(tree.nodes[material["occlusion"]].outputs['AO'], emission.inputs['Color'])


def add_card(mesh, layer, base, direction, side, length, width, rect):
    tip = base + direction * length
    half = side * (width * 0.5)
    corners = [base - half, base + half, tip + half, tip - half]
    u0, v0, u1, v1 = rect
    coordinates = [(u0, 1.0 - v1), (u1, 1.0 - v1), (u1, 1.0 - v0), (u0, 1.0 - v0)]
    verts = [mesh.verts.new(corner) for corner in corners]
    face = mesh.faces.new(verts)
    for loop, value in zip(face.loops, coordinates):
        loop[layer].uv = value


def build_spray(seed, length, spread, droop, twigs, tip_style):
    rng = numpy.random.default_rng(seed)
    mesh = bmesh.new()
    layer = mesh.loops.layers.uv.new("UVMap")

    def stem(t):
        return Vector((math.sin(t * 2.2 + seed) * 0.03 * length, t * length, -droop * t * t * length))

    count = int(twigs * length / 0.9)
    for index in range(count):
        t = 0.06 + 0.9 * (index + rng.uniform(-0.3, 0.3)) / count
        t = min(max(t, 0.04), 0.97)
        point = stem(t)
        ahead = (stem(min(t + 0.02, 1.0)) - stem(max(t - 0.02, 0.0))).normalized()
        side = -1.0 if index % 2 else 1.0
        angle = math.radians(rng.uniform(38.0, 62.0) - 18.0 * t)
        outward = Vector((side, 0.0, 0.0))
        direction = (ahead * math.cos(angle) + outward * math.sin(angle)).normalized()
        direction.z -= rng.uniform(0.02, 0.18)
        direction.normalize()
        taper = 1.0 - t * 0.55
        size = spread * rng.uniform(0.7, 1.05) * taper
        flat = Vector((0.0, 0.0, 1.0)).cross(direction).normalized()
        roll = math.radians(rng.uniform(-28.0, 28.0))
        width_axis = (flat * math.cos(roll) + Vector((0.0, 0.0, 1.0)) * math.sin(roll)).normalized()
        rect = sprites[int(rng.integers(0, 4))]
        aspect = (rect[2] - rect[0]) / (rect[3] - rect[1])
        add_card(mesh, layer, point - direction * size * 0.08 + Vector((0.0, 0.0, rng.uniform(-0.015, 0.02))), direction, width_axis, size, size * aspect, rect)
        if rng.random() < 0.45:
            rect = sprites[int(rng.integers(0, 5))]
            aspect = (rect[2] - rect[0]) / (rect[3] - rect[1])
            small = size * rng.uniform(0.45, 0.7)
            lift = Vector((0.0, 0.0, rng.uniform(0.01, 0.04)))
            add_card(mesh, layer, point + lift, (ahead + outward * 0.2 * side).normalized(), Vector((0.0, 0.0, 1.0)).cross(ahead).normalized(), small, small * aspect, rect)

    for index in range(int(count * 0.35)):
        t = rng.uniform(0.15, 0.95)
        point = stem(t) + Vector((rng.uniform(-0.18, 0.18) * spread / 0.3 * (1.0 - t * 0.5), 0.0, rng.uniform(0.01, 0.05)))
        yaw = rng.uniform(-0.9, 0.9)
        direction = Vector((math.sin(yaw), math.cos(yaw), rng.uniform(-0.15, 0.05))).normalized()
        flat = Vector((0.0, 0.0, 1.0)).cross(direction).normalized()
        rect = sprites[int(rng.integers(0, 5))]
        aspect = (rect[2] - rect[0]) / (rect[3] - rect[1])
        size = spread * rng.uniform(0.5, 0.8)
        add_card(mesh, layer, point, direction, flat, size, size * aspect, rect)

    rect = sprites[2 if tip_style else 0]
    aspect = (rect[2] - rect[0]) / (rect[3] - rect[1])
    top = stem(0.97)
    add_card(mesh, layer, top - Vector((0.0, spread * 0.1, 0.0)), (stem(1.0) - stem(0.9)).normalized(), Vector((1.0, 0.0, 0.0)), spread * 0.8, spread * 0.8 * aspect, rect)

    u0, v0, u1, v1 = stick
    segments = 12
    for index in range(segments):
        a = index / segments
        b = (index + 1) / segments
        p = stem(a)
        q = stem(b)
        axis = (q - p).normalized()
        across = Vector((0.0, 0.0, 1.0)).cross(axis).normalized()
        radius_a = 0.012 * (1.0 - a * 0.75) * length
        radius_b = 0.012 * (1.0 - b * 0.75) * length
        verts = [mesh.verts.new(p - across * radius_a), mesh.verts.new(p + across * radius_a), mesh.verts.new(q + across * radius_b), mesh.verts.new(q - across * radius_b)]
        face = mesh.faces.new(verts)
        for loop, value in zip(face.loops, [(u0 + (u1 - u0) * a, 1.0 - v1), (u0 + (u1 - u0) * a, 1.0 - v0), (u0 + (u1 - u0) * b, 1.0 - v0), (u0 + (u1 - u0) * b, 1.0 - v1)]):
            loop[layer].uv = value
    return mesh


def dilate(color, alpha, passes):
    filled = alpha > 0.5
    result = color.copy()
    for step in range(passes):
        total = numpy.zeros_like(result)
        weight = numpy.zeros(filled.shape, dtype=numpy.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx or dy:
                    shifted = numpy.roll(numpy.roll(filled, dy, axis=0), dx, axis=1)
                    total += numpy.roll(numpy.roll(result, dy, axis=0), dx, axis=1) * shifted[..., None]
                    weight += shifted
        grow = (~filled) & (weight > 0)
        result[grow] = total[grow] / weight[grow][..., None]
        filled = filled | grow
    if (~filled).any():
        result[~filled] = result[filled].mean(axis=0)
    return result


def render_pass(scene, material, name, path, transform):
    set_pass(material, name)
    scene.view_settings.view_transform = transform
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(path)
    pixels = numpy.empty(atlas_size * atlas_size * 4, dtype=numpy.float32)
    image.pixels.foreach_get(pixels)
    bpy.data.images.remove(image)
    return pixels.reshape(atlas_size, atlas_size, 4)


def save(pixels, path):
    image = bpy.data.images.new(os.path.basename(path), atlas_size, atlas_size, alpha=True)
    image.pixels.foreach_set(numpy.ascontiguousarray(pixels, dtype=numpy.float32).ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()


reset()
source = os.path.join(source_root, "trees", "fir_tree_01")
output = os.path.join(source_root, "trees", "fir_spray")
os.makedirs(output, exist_ok=True)
textures = {
    "diff": load(os.path.join(source, "fir_tree_01_twig_diff_2k.jpg"), 'sRGB'),
    "alpha": load(os.path.join(source, "fir_tree_01_twig_alpha_2k.jpg"), 'Non-Color'),
    "nor": load(os.path.join(source, "fir_tree_01_twig_nor_gl_2k.jpg"), 'Non-Color'),
}
material = twig_material(textures)
layouts = [(11, 0.7, 0.24, 0.12, 26, False), (23, 0.68, 0.22, 0.16, 24, False), (37, 0.7, 0.26, 0.08, 30, False), (51, 0.62, 0.2, 0.04, 18, True)]
for index, (seed, length, spread, droop, twigs, tip) in enumerate(layouts):
    mesh = build_spray(seed, length, spread, droop, twigs, tip)
    data = bpy.data.meshes.new("spray%d" % index)
    mesh.to_mesh(data)
    mesh.free()
    data.materials.append(material)
    obj = bpy.data.objects.new("spray%d" % index, data)
    bpy.context.scene.collection.objects.link(obj)
    column = index % 2
    row = index // 2
    obj.location = Vector((column * 1.0 - 0.5, -row * 1.0 + 0.03, 0.0))

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.cycles.filter_width = 0.8
scene.render.resolution_x = atlas_size
scene.render.resolution_y = atlas_size
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '16'
scene.view_settings.look = 'None'
scene.world = bpy.data.worlds.new("empty")
camera_data = bpy.data.cameras.new("atlas")
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 2.0
camera = bpy.data.objects.new("atlas", camera_data)
camera.location = Vector((0.0, 0.0, 5.0))
scene.collection.objects.link(camera)
scene.camera = camera

scratch = preview_root if preview_root else output
color = render_pass(scene, material, "color", os.path.join(scratch, "spray_color_raw.png"), 'Standard')
normal = render_pass(scene, material, "normal", os.path.join(scratch, "spray_normal_raw.png"), 'Raw')
occlusion = render_pass(scene, material, "occlusion", os.path.join(scratch, "spray_ao_raw.png"), 'Raw')

alpha = color[:, :, 3]
color_rgb = dilate(color[:, :, :3], alpha, 24)
normal_rgb = dilate(normal[:, :, :3], alpha, 24)
ao = dilate(occlusion[:, :, :1].repeat(3, axis=2), alpha, 24)[:, :, 0]
shaded = color_rgb * (0.55 + 0.45 * ao)[..., None]

final = numpy.ones((atlas_size, atlas_size, 4), dtype=numpy.float32)
final[:, :, :3] = shaded
save(final, os.path.join(output, "fir_spray_diff.png"))
final[:, :, :3] = normal_rgb
save(final, os.path.join(output, "fir_spray_nor_gl.png"))
final[:, :, 0] = 0.6 + 0.4 * ao
final[:, :, 1] = 0.62 - 0.12 * ao
final[:, :, 2] = 0.0
save(final, os.path.join(output, "fir_spray_arm.png"))
final[:, :, 0] = alpha
final[:, :, 1] = alpha
final[:, :, 2] = alpha
save(final, os.path.join(output, "fir_spray_alpha.png"))
print("SPRAY ATLAS written", output, "coverage %.3f" % float((alpha > 0.5).mean()))
