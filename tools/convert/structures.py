import bpy
import bmesh
import math
import numpy
import os
import random
import sys
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gunkit as k
import turntable
from gunkit import v

arguments = sys.argv[sys.argv.index("--") + 1:]
source_root = arguments[0]
output_root = arguments[1]
preview_root = arguments[2]
wanted = arguments[3].split(",")
mode = arguments[4] if len(arguments) > 4 else "preview"
views = arguments[5].split(",") if len(arguments) > 5 else ["three", "front"]
samples = int(arguments[6]) if len(arguments) > 6 else 32
only = arguments[7].split(",") if len(arguments) > 7 else []
raw_root = os.path.join(os.path.dirname(os.path.normpath(source_root)), "raw")
hdri = os.path.join(raw_root, "hdri", "kloofendal_overcast_puresky_4k.hdr")

k.roots["source"] = source_root
k.roots["raw"] = raw_root

turntable.directions["overall"] = (Vector((0.75, -0.8, 0.45)), False, 40.0, 1.35)
tiers = ("twig", "wood", "stone", "metal")
pieces = ("foundation", "wall", "doorway", "window", "floor", "stairs", "roof")
openings = {"wall": None, "doorway": (-0.55, 0.55, 0.0, 2.2), "window": (-0.55, 0.55, 1.1, 2.1)}
rise = 1.2
slope = math.hypot(1.5, rise)
texture_size = 1024
bake_samples = 32
axes = {"x": v(1.0, 0.0, 0.0), "y": v(0.0, 1.0, 0.0), "z": v(0.0, 0.0, 1.0), "xz": v(1.0, 0.0, 1.0).normalized(), "zx": v(-1.0, 0.0, 1.0).normalized(), "yz": v(0.0, 1.0, 1.0).normalized(), "zy": v(0.0, -1.0, 1.0).normalized(), "ry": v(0.0, 1.5, rise).normalized(), "yr": v(0.0, -1.5, rise).normalized(), "xy": v(1.0, 1.0, 0.0).normalized(), "yx": v(-1.0, 1.0, 0.0).normalized()}
photos = {
    "bark": os.path.join(source_root, "textures", "bark_willow", "bark_willow_diff_2k.jpg"),
    "wood": os.path.join(source_root, "textures", "rough_wood", "rough_wood_diff_2k.jpg"),
    "rock": os.path.join(raw_root, "textures", "mossy_rock", "mossy_rock_diff_2k.jpg"),
    "rock_height": os.path.join(raw_root, "textures", "mossy_rock", "mossy_rock_disp_2k.jpg"),
    "concrete": os.path.join(raw_root, "textures", "rough_concrete", "rough_concrete_diff_2k.jpg"),
    "concrete_height": os.path.join(raw_root, "textures", "rough_concrete", "rough_concrete_disp_2k.jpg"),
    "chipped": os.path.join(raw_root, "textures_acg", "PaintedMetal013", "PaintedMetal013_2K-JPG_Color.jpg"),
    "flaked": os.path.join(raw_root, "textures_acg", "PaintedMetal012", "PaintedMetal012_2K-JPG_Color.jpg"),
    "plate": os.path.join(raw_root, "textures_acg", "DiamondPlate008A", "DiamondPlate008A_2K-JPG_Color.jpg"),
    "plate_height": os.path.join(raw_root, "textures_acg", "DiamondPlate008A", "DiamondPlate008A_2K-JPG_Displacement.jpg"),
    "rust": os.path.join(source_root, "textures", "rusty_metal_04", "rusty_metal_04_diff_2k.jpg"),
    "spots": os.path.join(raw_root, "textures", "rusty_metal_02", "rusty_metal_02_diff_2k.jpg"),
    "olive": os.path.join(raw_root, "textures", "green_metal_rust", "green_metal_rust_diff_2k.jpg"),
}
means = {}
metal_kinds = ("scrap", "frame", "plate", "weld", "bolt")
paints = [(0.0, (0.034, 0.042, 0.024, 1.0)), (0.3, (0.04, 0.012, 0.009, 1.0)), (0.58, (0.032, 0.04, 0.047, 1.0)), (0.82, (0.09, 0.09, 0.086, 1.0))]
stain_resolution = 320.0
stain_images = {}
stain_axes = {"py": ("X", "Z", "Y", 1.0), "ny": ("X", "Z", "Y", -1.0), "px": ("Y", "Z", "X", 1.0), "nx": ("Y", "Z", "X", -1.0), "pz": ("X", "Y", "Z", 1.0)}


def nearest(direction):
    return max(axes, key=lambda key: abs(axes[key].dot(direction.normalized())))


def rows(matrix):
    return [tuple(matrix[index]) for index in range(3)]


def grain_frame(direction):
    x_axis = direction.normalized()
    helper = v(0.0, 0.0, 1.0) if abs(x_axis.z) < 0.9 else v(0.0, 1.0, 0.0)
    y_axis = helper.cross(x_axis).normalized()
    z_axis = x_axis.cross(y_axis)
    return Matrix((tuple(x_axis), tuple(y_axis), tuple(z_axis)))


def photo_frame(direction, face):
    if face == "z":
        flat = v(direction.x, direction.y, 0.0)
        return flat.normalized().rotation_difference(v(1.0, 0.0, 0.0)).to_matrix() if flat.length > 1e-6 else Matrix.Identity(3)
    return direction.normalized().rotation_difference(v(0.0, 0.0, 1.0)).to_matrix()


def photo_mean(path):
    if path not in means:
        picture = bpy.data.images.load(path, check_existing=True)
        data = numpy.empty(picture.size[0] * picture.size[1] * 4, dtype=numpy.float32)
        picture.pixels.foreach_get(data)
        encoded = data.reshape(-1, 4)[:, :3]
        linear = numpy.where(encoded <= 0.04045, encoded / 12.92, numpy.power((encoded + 0.055) / 1.055, 2.4))
        means[path] = tuple(float(value) for value in linear.mean(axis=0))
    return means[path]


def attribute(tree, name):
    node = tree.nodes.new('ShaderNodeAttribute')
    node.attribute_type = 'GEOMETRY'
    node.attribute_name = name
    return node


def vector_math(tree, operation, a, b=None):
    node = tree.nodes.new('ShaderNodeVectorMath')
    node.operation = operation
    for index, value in enumerate((a, b)):
        if value is None:
            continue
        if isinstance(value, (tuple, list, Vector)):
            node.inputs[index].default_value = tuple(value)
        else:
            tree.links.new(value, node.inputs[index])
    return node.outputs['Value'] if operation == 'DOT_PRODUCT' else node.outputs['Vector']


def rotated(tree, coordinates, matrix):
    combine = tree.nodes.new('ShaderNodeCombineXYZ')
    for axis, row in zip(('X', 'Y', 'Z'), rows(matrix)):
        tree.links.new(vector_math(tree, 'DOT_PRODUCT', coordinates, row), combine.inputs[axis])
    return combine.outputs['Vector']


def palette(tree, factor, colors, constant=False):
    node = tree.nodes.new('ShaderNodeValToRGB')
    ramp = node.color_ramp
    ramp.interpolation = 'CONSTANT' if constant else 'LINEAR'
    ramp.elements[0].position = colors[0][0]
    ramp.elements[-1].position = colors[-1][0]
    for position, color in colors[1:-1]:
        ramp.elements.new(position)
    for element, (position, color) in zip(ramp.elements, colors):
        element.color = color
    tree.links.new(factor, node.inputs['Fac'])
    return node.outputs['Color']


def multiply(tree, a, b):
    return k.mix_color(tree, 1.0, a, b, 'MULTIPLY')


def shade(tree, color, amount):
    return multiply(tree, color, (amount, amount, amount, 1.0))


def saturation(tree, color, amount):
    node = tree.nodes.new('ShaderNodeHueSaturation')
    node.inputs['Saturation'].default_value = amount
    tree.links.new(color, node.inputs['Color'])
    return node.outputs['Color']


def luminance(tree, color):
    node = tree.nodes.new('ShaderNodeRGBToBW')
    tree.links.new(color, node.inputs['Color'])
    return node.outputs['Val']


def normalized(tree, coordinates, key, scale, amount=1.0):
    mean = photo_mean(photos[key])
    picture = k.photo(tree, coordinates, photos[key], scale, 'sRGB')
    detail = multiply(tree, picture, (1.0 / max(mean[0], 1e-4), 1.0 / max(mean[1], 1e-4), 1.0 / max(mean[2], 1e-4), 1.0))
    return saturation(tree, detail, amount) if amount < 1.0 else detail


def cells(tree, coordinates, scale, feature='F1'):
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = scale
    tree.links.new(coordinates, mapping.inputs['Vector'])
    node = tree.nodes.new('ShaderNodeTexVoronoi')
    node.feature = feature
    tree.links.new(mapping.outputs['Vector'], node.inputs['Vector'])
    return node


def relief(tree, shader, height, strength, distance, radius):
    bump = tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = distance
    tree.links.new(height, bump.inputs['Height'])
    bevel = tree.nodes.new('ShaderNodeBevel')
    bevel.samples = 8
    bevel.inputs['Radius'].default_value = radius
    tree.links.new(bump.outputs['Normal'], bevel.inputs['Normal'])
    tree.links.new(bevel.outputs['Normal'], shader.inputs['Normal'])


def facing(tree, direction):
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    return k.math_node(tree, 'ABSOLUTE', vector_math(tree, 'DOT_PRODUCT', geometry.outputs['Normal'], tuple(direction)))


def upward(tree):
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    return k.channel(tree, geometry.outputs['Normal'], 'Blue')


def height_of(tree, place):
    split = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(place, split.inputs['Vector'])
    return split.outputs['Z']


def setup(name):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    tree = result.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    place = tree.nodes.new('ShaderNodeTexCoord').outputs['Object']
    moved = vector_math(tree, 'ADD', place, attribute(tree, "seed").outputs['Vector'])
    tint = attribute(tree, "tint").outputs['Fac']
    return result, tree, shader, place, moved, tint


def splash(tree, place):
    vertical = k.math_node(tree, 'SUBTRACT', 1.0, k.ramp(tree, k.math_node(tree, 'ABSOLUTE', upward(tree)), 0.45, 0.75))
    low = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', k.ramp(tree, height_of(tree, place), 0.35, 0.0), 0.5), k.math_node(tree, 'MULTIPLY', k.ramp(tree, height_of(tree, place), -0.35, -1.5), 0.55))
    return k.math_node(tree, 'MULTIPLY', vertical, low, True)


def bark_look(name, direction):
    result, tree, shader, place, moved, tint = setup(name)
    grain = rotated(tree, moved, grain_frame(direction))
    shot = rotated(tree, moved, photo_frame(direction, "y"))
    edge, cavity = k.masks(tree, 0.004, 0.035)
    detail = normalized(tree, shot, "bark", 4.0, 0.7)
    fibers = k.stretched_noise(tree, grain, (1.5, 30.0, 30.0), 4.0)
    fissures = k.ramp(tree, k.stretched_noise(tree, grain, (3.0, 70.0, 70.0), 6.0), 0.58, 0.72)
    peel = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, grain, 1.6, 4.0, 0.6), 0.66, 0.72), k.math_node(tree, 'SUBTRACT', 1.0, fissures), True)
    tone = palette(tree, tint, [(0.0, (0.05, 0.035, 0.022, 1.0)), (0.3, (0.1, 0.07, 0.042, 1.0)), (0.55, (0.078, 0.062, 0.046, 1.0)), (0.8, (0.115, 0.085, 0.052, 1.0)), (1.0, (0.09, 0.084, 0.074, 1.0))])
    color = multiply(tree, tone, detail)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, fibers, 0.45, 0.8), 0.3), color, shade(tree, color, 0.7))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', fissures, 0.8), color, (0.012, 0.009, 0.007, 1.0))
    color = k.mix_color(tree, peel, color, (0.2, 0.14, 0.08, 1.0))
    ends = k.ramp(tree, facing(tree, direction), 0.72, 0.9)
    rings = k.wood_grain(tree, grain, 110.0, (0.0, 0.0, 0.0), 2.0, 1.2, 'X')
    cut = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, rings, 0.4, 0.95), 0.55), (0.26, 0.19, 0.11, 1.0), (0.13, 0.085, 0.045, 1.0))
    color = k.mix_color(tree, ends, color, cut)
    lichen = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, moved, 2.5, 5.0, 0.6), 0.64, 0.72), k.ramp(tree, upward(tree), 0.2, 0.8), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', lichen, 0.35), color, (0.1, 0.11, 0.075, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.8), color, (0.01, 0.008, 0.006, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    roughness = k.mix_value(tree, peel, 0.86, 0.62)
    roughness = k.mix_value(tree, ends, roughness, 0.74)
    tree.links.new(k.mix_value(tree, fissures, roughness, 0.95), shader.inputs['Roughness'])
    shader.inputs['Metallic'].default_value = 0.0
    height = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', fibers, 0.35), k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'SUBTRACT', 1.0, fissures), 0.5))
    height = k.math_node(tree, 'ADD', height, k.math_node(tree, 'MULTIPLY', luminance(tree, detail), 0.25))
    relief(tree, shader, k.math_node(tree, 'SUBTRACT', height, k.math_node(tree, 'MULTIPLY', peel, 0.2)), 0.6, 0.004, 0.003)
    return result


def twine_look(name):
    result, tree, shader, place, moved, tint = setup(name)
    edge, cavity = k.masks(tree, 0.002, 0.02)
    fibers = k.noise(tree, moved, 380.0, 4.0, 0.7)
    patches = k.noise(tree, moved, 9.0, 4.0, 0.5)
    color = k.mix_color(tree, fibers, (0.09, 0.066, 0.038, 1.0), (0.17, 0.13, 0.075, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, patches, 0.45, 0.75), 0.5), color, (0.12, 0.112, 0.095, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.85), color, (0.03, 0.022, 0.014, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = 0.92
    shader.inputs['Metallic'].default_value = 0.0
    relief(tree, shader, fibers, 0.6, 0.0012, 0.0015)
    return result


def plank_look(name, direction, face, dark):
    result, tree, shader, place, moved, tint = setup(name)
    grain = rotated(tree, moved, grain_frame(direction))
    shot = rotated(tree, moved, photo_frame(direction, face))
    edge, cavity = k.masks(tree, 0.006, 0.05)
    detail = k.mix_color(tree, k.ramp(tree, k.noise(tree, moved, 1.1, 3.0, 0.5), 0.35, 0.65), normalized(tree, shot, "wood", 0.9, 0.3), normalized(tree, vector_math(tree, 'ADD', shot, (3.7, 1.3, 5.1)), "wood", 0.62, 0.3))
    rings = k.wood_grain(tree, grain, 42.0, (0.0, 0.0, 0.0), 3.5, 2.2, 'X')
    knot = cells(tree, grain, (1.3, 6.5, 6.5))
    chosen = k.ramp(tree, k.channel(tree, knot.outputs['Color'], 'Red'), 0.7, 0.76)
    core = k.math_node(tree, 'MULTIPLY', k.ramp(tree, knot.outputs['Distance'], 0.16, 0.07), chosen, True)
    halo = k.math_node(tree, 'MULTIPLY', k.ramp(tree, knot.outputs['Distance'], 0.34, 0.14), chosen, True)
    if dark:
        tone = palette(tree, tint, [(0.0, (0.038, 0.024, 0.015, 1.0)), (0.5, (0.052, 0.033, 0.02, 1.0)), (1.0, (0.045, 0.033, 0.024, 1.0))])
    else:
        tone = palette(tree, tint, [(0.0, (0.1, 0.056, 0.028, 1.0)), (0.3, (0.13, 0.075, 0.038, 1.0)), (0.65, (0.088, 0.06, 0.038, 1.0)), (1.0, (0.145, 0.088, 0.046, 1.0))])
    color = multiply(tree, tone, detail)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, rings, 0.45, 0.95), 0.4), color, shade(tree, color, 0.62))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', halo, 0.45), color, shade(tree, color, 0.6))
    color = k.mix_color(tree, core, color, (0.03, 0.016, 0.009, 1.0))
    bleach = k.math_node(tree, 'MULTIPLY', k.ramp(tree, upward(tree), 0.35, 0.95), 0.05 if dark else 0.14)
    color = k.mix_color(tree, bleach, color, (0.13, 0.12, 0.105, 1.0))
    weathered = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, moved, 3.0, 4.0, 0.55), 0.5, 0.75), 0.3)
    color = k.mix_color(tree, weathered, color, saturation(tree, color, 0.45))
    moss = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, place, 1.8, 5.0, 0.6), 0.62, 0.74), k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', cavity, 0.8), k.math_node(tree, 'MULTIPLY', k.ramp(tree, upward(tree), 0.5, 0.9), 0.5)), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', moss, 0.55), color, (0.035, 0.045, 0.018, 1.0))
    color = k.mix_color(tree, splash(tree, place), color, (0.028, 0.02, 0.013, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.85), color, (0.014, 0.01, 0.007, 1.0))
    worn = k.math_node(tree, 'MULTIPLY', edge, k.ramp(tree, k.noise(tree, moved, 40.0, 4.0, 0.6), 0.35, 0.6), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', worn, 0.5), color, (0.3, 0.2, 0.12, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    brightness = k.ramp(tree, luminance(tree, detail), 0.6, 1.4)
    roughness = k.mix_value(tree, brightness, 0.9, 0.74)
    roughness = k.mix_value(tree, cavity, roughness, 0.95)
    tree.links.new(k.mix_value(tree, worn, roughness, 0.7), shader.inputs['Roughness'])
    shader.inputs['Metallic'].default_value = 0.0
    height = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', rings, 0.25), k.math_node(tree, 'MULTIPLY', brightness, 0.6))
    height = k.math_node(tree, 'SUBTRACT', k.math_node(tree, 'ADD', height, k.math_node(tree, 'MULTIPLY', halo, 0.2)), k.math_node(tree, 'MULTIPLY', core, 0.3))
    relief(tree, shader, height, 0.4, 0.003, 0.005)
    return result


def stone_look(name, kind):
    result, tree, shader, place, moved, tint = setup(name)
    edge, cavity = k.masks(tree, 0.012, 0.06)
    scale = 1.2 if kind == "slate" else 0.75
    detail = normalized(tree, moved, "rock", scale, 0.3)
    tinted = normalized(tree, moved, "rock", scale, 1.0)
    height = k.photo(tree, moved, photos["rock_height"], scale, 'Non-Color')
    tones = {
        "stone": [(0.0, (0.13, 0.125, 0.115, 1.0)), (0.2, (0.18, 0.165, 0.14, 1.0)), (0.4, (0.1, 0.1, 0.098, 1.0)), (0.6, (0.2, 0.18, 0.15, 1.0)), (0.8, (0.145, 0.14, 0.13, 1.0)), (1.0, (0.16, 0.13, 0.1, 1.0))],
        "slate": [(0.0, (0.04, 0.045, 0.05, 1.0)), (0.35, (0.06, 0.063, 0.067, 1.0)), (0.7, (0.036, 0.038, 0.042, 1.0)), (1.0, (0.07, 0.065, 0.06, 1.0))],
        "paver": [(0.0, (0.13, 0.125, 0.112, 1.0)), (0.5, (0.17, 0.158, 0.135, 1.0)), (1.0, (0.11, 0.108, 0.1, 1.0))],
    }
    lichen_amount = {"stone": 0.7, "slate": 0.45, "paver": 0.25}[kind]
    tone = palette(tree, tint, tones[kind])
    color = multiply(tree, tone, detail)
    mottle = k.ramp(tree, k.noise(tree, moved, 2.2, 5.0, 0.6), 0.4, 0.7)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', mottle, 0.4), color, shade(tree, color, 0.6))
    lichen = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, moved, 1.6, 5.0, 0.6), 0.52, 0.66), k.ramp(tree, k.noise(tree, moved, 7.0, 4.0, 0.6), 0.35, 0.65), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', lichen, lichen_amount), color, shade(tree, multiply(tree, tone, tinted), 1.15))
    streaks = k.ramp(tree, k.stretched_noise(tree, place, (30.0, 30.0, 1.6), 4.0), 0.52, 0.72)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', streaks, 0.45), color, shade(tree, color, 0.5))
    moss = k.math_node(tree, 'MULTIPLY', cavity, k.ramp(tree, k.noise(tree, place, 3.0, 4.0, 0.6), 0.45, 0.65), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', moss, 0.7), color, (0.03, 0.04, 0.014, 1.0))
    chips = k.math_node(tree, 'MULTIPLY', edge, k.ramp(tree, k.noise(tree, moved, 22.0, 6.0, 0.7), 0.42, 0.58), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', chips, 0.7), color, shade(tree, tone, 1.45))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', splash(tree, place), 0.7), color, (0.035, 0.03, 0.024, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.85), color, (0.018, 0.017, 0.015, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    roughness = k.mix_value(tree, k.ramp(tree, height, 0.3, 0.8), 0.9, 0.82)
    if kind == "paver":
        roughness = k.mix_value(tree, k.ramp(tree, upward(tree), 0.7, 0.95), roughness, 0.66)
    tree.links.new(k.mix_value(tree, chips, roughness, 0.78), shader.inputs['Roughness'])
    shader.inputs['Metallic'].default_value = 0.0
    bumps = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', height, 0.7), k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 16.0, 5.0, 0.6), 0.25))
    relief(tree, shader, k.math_node(tree, 'SUBTRACT', bumps, k.math_node(tree, 'MULTIPLY', chips, 0.3)), 0.7, 0.012, 0.01)
    return result


def mortar_look(name):
    result, tree, shader, place, moved, tint = setup(name)
    edge, cavity = k.masks(tree, 0.006, 0.04)
    detail = normalized(tree, moved, "concrete", 1.8, 0.15)
    height = k.photo(tree, moved, photos["concrete_height"], 1.8, 'Non-Color')
    color = multiply(tree, (0.2, 0.19, 0.17, 1.0), detail)
    damp = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, place, 2.5, 4.0, 0.55), 0.5, 0.75), 0.4)
    color = k.mix_color(tree, damp, color, shade(tree, color, 0.6))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', splash(tree, place), 0.6), color, (0.03, 0.026, 0.02, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.7), color, (0.03, 0.028, 0.025, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = 0.95
    shader.inputs['Metallic'].default_value = 0.0
    relief(tree, shader, height, 0.5, 0.004, 0.004)
    return result


def stain_lookup(tree, owner):
    entries = stain_images.get(owner, [])
    if not entries:
        return 0.0, 0.0, 0.0, 0.0
    coordinates = tree.nodes.new('ShaderNodeTexCoord')
    where = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(coordinates.outputs['Object'], where.inputs['Vector'])
    facing_axes = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(coordinates.outputs['Normal'], facing_axes.inputs['Vector'])
    totals = [None, None, None, None]
    for key, picture, (u0, u1, v0, v1) in entries:
        first, second, axis, sign = stain_axes[key]
        combine = tree.nodes.new('ShaderNodeCombineXYZ')
        tree.links.new(k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'SUBTRACT', where.outputs[first], u0), 1.0 / (u1 - u0)), combine.inputs['X'])
        tree.links.new(k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'SUBTRACT', where.outputs[second], v0), 1.0 / (v1 - v0)), combine.inputs['Y'])
        texture = tree.nodes.new('ShaderNodeTexImage')
        texture.image = picture
        texture.extension = 'CLIP'
        texture.interpolation = 'Linear'
        tree.links.new(combine.outputs['Vector'], texture.inputs['Vector'])
        low, high = (0.2, 0.45) if key == "pz" else (0.3, 0.6)
        weight = k.ramp(tree, k.math_node(tree, 'MULTIPLY', facing_axes.outputs[axis], sign), low, high)
        channels = tree.nodes.new('ShaderNodeSeparateColor')
        tree.links.new(texture.outputs['Color'], channels.inputs['Color'])
        for index, socket in enumerate((channels.outputs['Red'], channels.outputs['Green'], channels.outputs['Blue'], texture.outputs['Alpha'])):
            value = k.math_node(tree, 'MULTIPLY', socket, weight)
            totals[index] = value if totals[index] is None else k.math_node(tree, 'ADD', totals[index], value, True)
    return tuple(totals)


def dents(tree, coordinates, scale, threshold, reach=0.42):
    node = cells(tree, coordinates, (scale, scale, scale))
    chosen = k.ramp(tree, k.channel(tree, node.outputs['Color'], 'Red'), threshold, threshold + 0.02)
    return k.math_node(tree, 'MULTIPLY', k.ramp(tree, node.outputs['Distance'], reach, 0.0), chosen, True)


def temper(tree, amount):
    return palette(tree, amount, [(0.0, (0.16, 0.11, 0.045, 1.0)), (0.35, (0.09, 0.05, 0.05, 1.0)), (0.6, (0.04, 0.04, 0.075, 1.0)), (1.0, (0.018, 0.018, 0.02, 1.0))])


def rust_layer(tree, moved, scale):
    detail = normalized(tree, moved, "rust", scale, 0.85)
    tone = palette(tree, k.noise(tree, moved, 2.4, 4.0, 0.6), [(0.3, (0.115, 0.042, 0.014, 1.0)), (0.5, (0.068, 0.029, 0.013, 1.0)), (0.72, (0.036, 0.02, 0.011, 1.0))])
    return multiply(tree, tone, detail), detail


def scrap_look(name, direction, owner):
    result, tree, shader, place, moved, tint = setup(name)
    flow = rotated(tree, moved, grain_frame(direction))
    edge, cavity = k.masks(tree, 0.0025, 0.03)
    run, grime, halo, heat = stain_lookup(tree, owner)
    unpainted = k.ramp(tree, tint, 0.81, 0.83)
    paint = palette(tree, tint, paints, True)
    paint = k.mix_color(tree, k.noise(tree, moved, 0.8, 2.0, 0.5), shade(tree, paint, 0.8), shade(tree, paint, 1.15))
    paint = multiply(tree, paint, normalized(tree, moved, "olive", 0.7, 0.2))
    chalk = k.mix_color(tree, 0.25, saturation(tree, paint, 0.6), (0.05, 0.047, 0.042, 1.0))
    sun = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, moved, 1.6, 4.0, 0.55), 0.4, 0.85), 0.5), k.math_node(tree, 'MULTIPLY', k.ramp(tree, upward(tree), 0.3, 0.9), 0.4), True)
    faded = k.mix_color(tree, sun, paint, chalk)
    light = luminance(tree, k.photo(tree, moved, photos["flaked"], 0.75, 'sRGB'))
    heavy = luminance(tree, k.photo(tree, vector_math(tree, 'ADD', moved, (1.7, 4.2, 2.9)), photos["chipped"], 0.55, 'sRGB'))
    flakes = k.mix_value(tree, k.ramp(tree, k.noise(tree, moved, 0.9, 3.0, 0.5), 0.3, 0.7), light, heavy)
    loss = k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'FRACT', k.math_node(tree, 'MULTIPLY', tint, 13.7)), 0.3)
    loss = k.math_node(tree, 'ADD', loss, k.math_node(tree, 'MULTIPLY', splash(tree, place), 0.45))
    loss = k.math_node(tree, 'ADD', loss, k.math_node(tree, 'MULTIPLY', halo, 0.7))
    loss = k.math_node(tree, 'ADD', loss, k.math_node(tree, 'MULTIPLY', run, 0.06))
    loss = k.math_node(tree, 'ADD', loss, k.math_node(tree, 'MULTIPLY', edge, 0.45))
    peel = k.math_node(tree, 'SUBTRACT', flakes, loss)
    painted = k.math_node(tree, 'MULTIPLY', k.ramp(tree, peel, 0.17, 0.25), k.math_node(tree, 'SUBTRACT', 1.0, unpainted), True)
    lip = k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'SUBTRACT', k.ramp(tree, peel, 0.12, 0.18), painted), k.math_node(tree, 'SUBTRACT', 1.0, unpainted), True)
    rusty, detail = rust_layer(tree, moved, 1.3)
    zinc = multiply(tree, (0.11, 0.11, 0.106, 1.0), normalized(tree, moved, "spots", 2.2, 0.3))
    spotted = multiply(tree, (0.11, 0.098, 0.08, 1.0), normalized(tree, moved, "spots", 2.2, 0.6))
    survived = k.ramp(tree, k.noise(tree, moved, 5.0, 5.0, 0.6), 0.56, 0.68)
    galvanic = k.ramp(tree, k.noise(tree, vector_math(tree, 'ADD', moved, (7.1, 2.3, 5.5)), 2.6, 6.0, 0.62), 0.38, 0.6)
    exposed = k.mix_value(tree, unpainted, k.math_node(tree, 'MULTIPLY', survived, 0.6), k.math_node(tree, 'SUBTRACT', 1.0, galvanic))
    under = k.mix_color(tree, exposed, rusty, k.mix_color(tree, unpainted, zinc, spotted))
    color = k.mix_color(tree, painted, under, faded)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', lip, 0.8), color, (0.03, 0.017, 0.01, 1.0))
    run_tone = multiply(tree, k.mix_color(tree, k.noise(tree, place, 9.0, 3.0, 0.5), (0.17, 0.062, 0.018, 1.0), (0.075, 0.03, 0.012, 1.0)), detail)
    color = k.mix_color(tree, k.ramp(tree, run, 0.03, 0.55), color, run_tone)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', halo, 0.8), color, rusty)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, grime, 0.02, 0.5), 0.55), color, (0.02, 0.018, 0.015, 1.0))
    streak = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.stretched_noise(tree, flow, (0.8, 22.0, 22.0), 4.0), 0.55, 0.72), k.ramp(tree, k.noise(tree, moved, 1.3, 3.0, 0.5), 0.4, 0.62), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', streak, 0.35), color, shade(tree, color, 0.5))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', heat, 0.85), color, temper(tree, heat))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', splash(tree, place), 0.4), color, (0.03, 0.022, 0.015, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.7), color, (0.016, 0.011, 0.008, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    bare = k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'SUBTRACT', 1.0, painted), exposed)
    bare = k.math_node(tree, 'MULTIPLY', bare, k.math_node(tree, 'SUBTRACT', 1.0, k.math_node(tree, 'MAXIMUM', run, halo)), True)
    tree.links.new(k.math_node(tree, 'MULTIPLY', bare, 0.7), shader.inputs['Metallic'])
    roughness = k.mix_value(tree, bare, 0.9, 0.55)
    roughness = k.mix_value(tree, painted, roughness, k.mix_value(tree, sun, 0.55, 0.78))
    roughness = k.mix_value(tree, k.math_node(tree, 'MULTIPLY', run, 0.8), roughness, 0.86)
    tree.links.new(k.mix_value(tree, k.math_node(tree, 'MULTIPLY', grime, 0.5), roughness, 0.82), shader.inputs['Roughness'])
    pitting = k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 55.0, 4.0, 0.6), k.math_node(tree, 'SUBTRACT', 1.0, painted))
    height = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', painted, 0.25), k.math_node(tree, 'MULTIPLY', pitting, 0.45))
    height = k.math_node(tree, 'SUBTRACT', height, k.math_node(tree, 'MULTIPLY', dents(tree, moved, 3.0, 0.72), 2.2))
    height = k.math_node(tree, 'SUBTRACT', height, k.math_node(tree, 'MULTIPLY', dents(tree, vector_math(tree, 'ADD', moved, (3.3, 1.1, 7.7)), 7.0, 0.93, 0.3), 0.7))
    height = k.math_node(tree, 'ADD', height, k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 1.4, 1.0, 0.5), 1.2))
    relief(tree, shader, height, 0.45, 0.004, 0.0025)
    return result


def frame_look(name, owner):
    result, tree, shader, place, moved, tint = setup(name)
    edge, cavity = k.masks(tree, 0.004, 0.04)
    run, grime, halo, heat = stain_lookup(tree, owner)
    coat = palette(tree, tint, [(0.0, (0.02, 0.02, 0.019, 1.0)), (0.5, (0.056, 0.022, 0.013, 1.0)), (0.78, (0.03, 0.033, 0.03, 1.0))], True)
    coat = k.mix_color(tree, k.ramp(tree, k.noise(tree, moved, 2.0, 4.0, 0.55), 0.35, 0.85), coat, k.mix_color(tree, 0.35, coat, (0.075, 0.072, 0.066, 1.0)))
    rusty, detail = rust_layer(tree, moved, 1.6)
    patches = k.ramp(tree, k.math_node(tree, 'ADD', k.noise(tree, moved, 3.2, 6.0, 0.62), k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 24.0, 4.0, 0.6), 0.25)), 0.64, 0.8)
    corrosion = k.math_node(tree, 'ADD', patches, k.math_node(tree, 'MULTIPLY', cavity, 0.9))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', halo, 0.8))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', run, 0.2))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', edge, k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, moved, 9.0, 4.0, 0.6), 0.5, 0.62), 0.7)))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', splash(tree, place), 0.5), True)
    chips = k.math_node(tree, 'MULTIPLY', edge, k.ramp(tree, k.noise(tree, moved, 55.0, 4.0, 0.6), 0.45, 0.6), True)
    color = k.mix_color(tree, corrosion, coat, rusty)
    color = k.mix_color(tree, chips, color, (0.24, 0.235, 0.225, 1.0))
    run_tone = multiply(tree, k.mix_color(tree, k.noise(tree, place, 9.0, 3.0, 0.5), (0.14, 0.052, 0.017, 1.0), (0.06, 0.026, 0.011, 1.0)), detail)
    color = k.mix_color(tree, k.ramp(tree, run, 0.03, 0.55), color, run_tone)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, grime, 0.02, 0.5), 0.55), color, (0.018, 0.016, 0.014, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', heat, 0.85), color, temper(tree, heat))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.6), color, (0.014, 0.01, 0.007, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    metal = k.mix_value(tree, corrosion, 0.0, 0.05)
    tree.links.new(k.mix_value(tree, chips, metal, 1.0), shader.inputs['Metallic'])
    roughness = k.mix_value(tree, corrosion, k.mix_value(tree, k.noise(tree, moved, 6.0, 3.0, 0.5), 0.58, 0.74), 0.88)
    roughness = k.mix_value(tree, k.math_node(tree, 'MULTIPLY', run, 0.7), roughness, 0.85)
    tree.links.new(k.mix_value(tree, chips, roughness, 0.36), shader.inputs['Roughness'])
    height = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', corrosion, 0.35), k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 70.0, 4.0, 0.6), k.math_node(tree, 'MULTIPLY', corrosion, 0.5)))
    relief(tree, shader, k.math_node(tree, 'SUBTRACT', height, k.math_node(tree, 'MULTIPLY', chips, 0.2)), 0.35, 0.0015, 0.004)
    return result


def plate_look(name, owner):
    result, tree, shader, place, moved, tint = setup(name)
    edge, cavity = k.masks(tree, 0.003, 0.025)
    run, grime, halo, heat = stain_lookup(tree, owner)
    lugs = k.math_node(tree, 'MULTIPLY', k.photo(tree, moved, photos["plate_height"], 2.1, 'Non-Color'), k.ramp(tree, upward(tree), 0.4, 0.7))
    raised = k.ramp(tree, lugs, 0.3, 0.65)
    steel = multiply(tree, (0.15, 0.148, 0.142, 1.0), normalized(tree, moved, "plate", 2.1, 0.15))
    coat = palette(tree, tint, [(0.0, (0.042, 0.046, 0.04, 1.0)), (0.55, (0.075, 0.062, 0.03, 1.0))], True)
    painted = k.ramp(tree, k.math_node(tree, 'SUBTRACT', k.noise(tree, moved, 1.6, 5.0, 0.6), k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', raised, 0.35), k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'ADD', edge, halo), 0.5))), 0.44, 0.5)
    rusty, detail = rust_layer(tree, moved, 1.8)
    corrosion = k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'SUBTRACT', 1.0, raised), k.ramp(tree, k.noise(tree, moved, 3.5, 6.0, 0.62), 0.45, 0.62))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', cavity, 0.8))
    corrosion = k.math_node(tree, 'ADD', corrosion, halo)
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', run, 0.6))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', splash(tree, place), 0.4), True)
    polish = k.math_node(tree, 'MULTIPLY', raised, k.math_node(tree, 'SUBTRACT', 1.0, corrosion), True)
    dirt = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, place, 1.3, 5.0, 0.6), 0.55, 0.78), k.math_node(tree, 'SUBTRACT', 1.0, raised), True)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', painted, 0.85), steel, coat)
    color = k.mix_color(tree, corrosion, color, rusty)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', polish, 0.7), color, (0.32, 0.318, 0.31, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', dirt, 0.7), color, (0.04, 0.032, 0.022, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', grime, 0.6), color, (0.02, 0.017, 0.014, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', heat, 0.85), color, temper(tree, heat))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', cavity, 0.6), color, (0.02, 0.015, 0.011, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    metal = k.mix_value(tree, painted, 0.85, 0.0)
    metal = k.mix_value(tree, corrosion, metal, 0.08)
    metal = k.mix_value(tree, polish, metal, 1.0)
    tree.links.new(k.mix_value(tree, dirt, metal, 0.0), shader.inputs['Metallic'])
    roughness = k.mix_value(tree, painted, 0.5, 0.72)
    roughness = k.mix_value(tree, corrosion, roughness, 0.9)
    roughness = k.mix_value(tree, polish, roughness, 0.28)
    tree.links.new(k.mix_value(tree, dirt, roughness, 0.95), shader.inputs['Roughness'])
    height = k.math_node(tree, 'ADD', lugs, k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 60.0, 4.0, 0.6), k.math_node(tree, 'MULTIPLY', corrosion, 0.3)))
    height = k.math_node(tree, 'SUBTRACT', height, k.math_node(tree, 'MULTIPLY', dents(tree, moved, 2.5, 0.8), 0.8))
    relief(tree, shader, height, 0.9, 0.003, 0.003)
    return result


def weld_look(name, direction, owner):
    result, tree, shader, place, moved, tint = setup(name)
    along = rotated(tree, moved, grain_frame(direction))
    edge, cavity = k.masks(tree, 0.0012, 0.01)
    run, grime, halo, heat = stain_lookup(tree, owner)
    split_axes = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(along, split_axes.inputs['Vector'])
    ripple = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', k.math_node(tree, 'SINE', k.math_node(tree, 'MULTIPLY', split_axes.outputs['X'], math.tau / 0.0032)), 0.5), 0.5)
    tint_noise = k.noise(tree, moved, 45.0, 3.0, 0.5)
    color = k.mix_color(tree, tint_noise, (0.06, 0.056, 0.052, 1.0), (0.035, 0.033, 0.036, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, moved, 14.0, 3.0, 0.5), 0.45, 0.7), 0.7), color, temper(tree, k.noise(tree, moved, 20.0, 2.0, 0.5)))
    rusty, detail = rust_layer(tree, moved, 3.0)
    corrosion = k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', cavity, 0.9), k.ramp(tree, k.noise(tree, moved, 30.0, 4.0, 0.6), 0.55, 0.7))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', run, 0.5), True)
    color = k.mix_color(tree, corrosion, color, rusty)
    slag = k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, moved, 160.0, 2.0, 0.5), 0.62, 0.7), 0.8, True)
    color = k.mix_color(tree, slag, color, (0.012, 0.011, 0.01, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    tree.links.new(k.mix_value(tree, corrosion, 0.75, 0.1), shader.inputs['Metallic'])
    tree.links.new(k.mix_value(tree, corrosion, k.mix_value(tree, ripple, 0.42, 0.6), 0.88), shader.inputs['Roughness'])
    relief(tree, shader, k.math_node(tree, 'ADD', k.math_node(tree, 'MULTIPLY', ripple, 0.7), k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 90.0, 3.0, 0.6), 0.4)), 0.7, 0.0006, 0.0012)
    return result


def bolt_look(name, owner):
    result, tree, shader, place, moved, tint = setup(name)
    edge, cavity = k.masks(tree, 0.0008, 0.006)
    run, grime, halo, heat = stain_lookup(tree, owner)
    rusty, detail = rust_layer(tree, moved, 4.0)
    zinc = multiply(tree, (0.22, 0.22, 0.212, 1.0), normalized(tree, moved, "spots", 3.0, 0.4))
    steel = k.mix_color(tree, k.ramp(tree, tint, 0.62, 0.66), (0.045, 0.043, 0.041, 1.0), zinc)
    corrosion = k.math_node(tree, 'ADD', k.ramp(tree, k.noise(tree, moved, 70.0, 4.0, 0.6), 0.4, 0.62), k.math_node(tree, 'MULTIPLY', k.ramp(tree, tint, 0.55, 0.2), 0.9))
    corrosion = k.math_node(tree, 'ADD', corrosion, k.math_node(tree, 'MULTIPLY', cavity, 0.9), True)
    worn = k.math_node(tree, 'MULTIPLY', edge, k.ramp(tree, corrosion, 0.7, 0.3), True)
    color = k.mix_color(tree, corrosion, steel, rusty)
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', worn, 0.6), color, (0.3, 0.295, 0.285, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', grime, 0.5), color, (0.02, 0.018, 0.015, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    tree.links.new(k.mix_value(tree, corrosion, 0.9, 0.08), shader.inputs['Metallic'])
    tree.links.new(k.mix_value(tree, corrosion, 0.38, 0.9), shader.inputs['Roughness'])
    relief(tree, shader, k.math_node(tree, 'MULTIPLY', k.noise(tree, moved, 180.0, 3.0, 0.6), corrosion), 0.4, 0.0005, 0.0008)
    return result


def ensure(name):
    if name in k.looks:
        return
    base, marker, owner = name.partition("@")
    parts = base.split("_")
    kind = parts[0]
    if kind == "bark":
        k.looks[name] = bark_look(name, axes[parts[1]])
    elif kind in ("plank", "beam"):
        k.looks[name] = plank_look(name, axes[parts[1]], parts[2], kind == "beam")
    elif kind in ("stone", "slate", "paver"):
        k.looks[name] = stone_look(name, kind)
    elif kind == "mortar":
        k.looks[name] = mortar_look(name)
    elif kind == "scrap":
        k.looks[name] = scrap_look(name, axes[parts[1]], owner)
    elif kind == "frame":
        k.looks[name] = frame_look(name, owner)
    elif kind == "plate":
        k.looks[name] = plate_look(name, owner)
    elif kind == "weld":
        k.looks[name] = weld_look(name, axes[parts[1]], owner)
    elif kind == "bolt":
        k.looks[name] = bolt_look(name, owner)
    elif kind == "twine":
        k.looks[name] = twine_look(name)


def sphere_directions(count):
    result = []
    for index in range(count):
        z = 1.0 - 2.0 * (index + 0.5) / count
        radius = math.sqrt(max(0.0, 1.0 - z * z))
        angle = index * math.pi * (3.0 - math.sqrt(5.0))
        result.append(v(math.cos(angle) * radius, math.sin(angle) * radius, z))
    return result


rays = sphere_directions(96)


def surface_samples(bm, dense=True):
    bm.faces.index_update()
    samples = {}
    for loops in bm.calc_loop_triangles():
        a, b, c = (loop.vert.co for loop in loops)
        normal = (b - a).cross(c - a)
        if normal.length < 1e-12:
            continue
        normal.normalize()
        center = (a + b + c) / 3.0
        points = [center] + ([center.lerp(corner, 0.85) for corner in (a, b, c)] + [center.lerp((first + second) * 0.5, 0.85) for first, second in ((a, b), (b, c), (c, a))] if dense else [])
        samples.setdefault(loops[0].face.index, []).extend((point, normal) for point in points)
    return samples


def open_rays(tree, samples, limit):
    escaped = 0
    total = 0
    for point, normal in samples:
        origin = point + normal * 0.0006
        for direction in rays:
            if direction.dot(normal) > 0.05:
                total += 1
                if tree.ray_cast(origin, direction, 60.0)[0] is None:
                    escaped += 1
                    if escaped >= limit:
                        return escaped, total
    return escaped, total


def cull(bm, limit=0.35):
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    samples = surface_samples(bm)
    hidden = [face for face in bm.faces if face.calc_area() < limit and open_rays(tree, samples.get(face.index, []), 1)[0] == 0]
    bmesh.ops.delete(bm, geom=hidden, context='FACES_ONLY')
    return len(hidden)


def smooth_step(low, high, values):
    blend = numpy.clip((values - low) / (high - low), 0.0, 1.0)
    return blend * blend * (3.0 - 2.0 * blend)


def noise_line(values, seed):
    table = numpy.random.default_rng(int(seed * 7919.0) % 2147483647).random(128)
    index = numpy.floor(values).astype(numpy.int64)
    fraction = values - index
    fraction = fraction * fraction * (3.0 - 2.0 * fraction)
    return table[index % 128] + (table[(index + 1) % 128] - table[index % 128]) * fraction


def screen(canvas, rows, columns, channel, value):
    region = canvas[rows, columns, channel]
    canvas[rows, columns, channel] = 1.0 - (1.0 - region) * (1.0 - numpy.clip(value, 0.0, 1.0))


def window(canvas, extent, u_low, u_high, v_low, v_high):
    u0, u1, v0, v1 = extent
    height, width = canvas.shape[:2]
    i0 = max(0, int((u_low - u0) * stain_resolution))
    i1 = min(width, int((u_high - u0) * stain_resolution) + 2)
    j0 = max(0, int((v_low - v0) * stain_resolution))
    j1 = min(height, int((v_high - v0) * stain_resolution) + 2)
    if i0 >= i1 or j0 >= j1:
        return None
    return slice(j0, j1), slice(i0, i1), u0 + (numpy.arange(i0, i1) + 0.5) / stain_resolution, v0 + (numpy.arange(j0, j1) + 0.5) / stain_resolution


def paint_drip(canvas, extent, u, w, flow, strength, width, length, seed):
    rng = numpy.random.default_rng(int(seed * 7919.0) % 2147483647)
    for index in range(1 + int(rng.random() * 2.7)):
        offset = 0.0 if index == 0 else (rng.random() - 0.5) * width * 2.4
        reach = length if index == 0 else length * (0.3 + 0.6 * rng.random())
        size = width if index == 0 else width * (0.35 + 0.35 * rng.random())
        power = strength if index == 0 else strength * (0.45 + 0.4 * rng.random())
        center = u + offset
        low, high = (w - reach * 3.0, w + size * 2.0) if flow < 0.0 else (w - size * 2.0, w + reach * 3.0)
        cut = window(canvas, extent, center - size * 5.0 - 0.015, center + size * 5.0 + 0.015, low, high)
        if cut is None:
            continue
        rows, columns, us, vs = cut
        along = (vs - w) * flow
        reached = numpy.clip(along, 0.0, None)
        wobble = (noise_line(reached * 7.0, seed + index * 3.1) - 0.5) * size * 1.6
        spread = size * (0.6 + 0.9 * numpy.sqrt(reached / reach))
        fade = numpy.exp(-reached / reach) * smooth_step(-size * 0.8, size * 0.5, along)
        breakup = 0.6 + 0.4 * noise_line(reached * 26.0, seed * 1.7 + index)
        lateral = us[None, :] - (center + wobble[:, None])
        profile = numpy.exp(-(lateral / spread[:, None]) ** 2)
        value = power * profile * (fade * breakup)[:, None]
        screen(canvas, rows, columns, 0, value)
        screen(canvas, rows, columns, 1, power * numpy.exp(-(lateral / (spread[:, None] * 1.8)) ** 2) * (numpy.exp(-reached / (reach * 1.6)) * smooth_step(-size, size, along))[:, None] * 0.3)


def paint_halo(canvas, extent, u, w, radius, strength, channel, seed):
    cut = window(canvas, extent, u - radius * 2.6, u + radius * 2.6, w - radius * 2.6, w + radius * 2.6)
    if cut is None:
        return
    rows, columns, us, vs = cut
    across = us[None, :] - u
    upward_offset = vs[:, None] - w
    angle = numpy.arctan2(upward_offset, across)
    wobble = 0.8 + 0.2 * numpy.sin(angle * 3.0 + seed) + 0.12 * numpy.sin(angle * 5.0 + seed * 2.3)
    distance = numpy.sqrt(across * across + upward_offset * upward_offset) / (radius * wobble)
    screen(canvas, rows, columns, channel, strength * numpy.exp(-distance * distance))


def paint_ring(canvas, extent, u, w, half_u, half_w, radius, strength, channel, seed):
    cut = window(canvas, extent, u - half_u - radius * 2.6, u + half_u + radius * 2.6, w - half_w - radius * 2.6, w + half_w + radius * 2.6)
    if cut is None:
        return
    rows, columns, us, vs = cut
    across = us[None, :] - u
    upward_offset = vs[:, None] - w
    outside = numpy.sqrt(numpy.clip(numpy.abs(across) - half_u, 0.0, None) ** 2 + numpy.clip(numpy.abs(upward_offset) - half_w, 0.0, None) ** 2)
    angle = numpy.arctan2(upward_offset, across)
    wobble = 0.75 + 0.25 * numpy.sin(angle * 4.0 + seed) + 0.15 * numpy.sin(angle * 7.0 + seed * 1.9)
    value = strength * numpy.exp(-(outside / (radius * wobble)) ** 2) * smooth_step(0.0, 0.004, outside)
    screen(canvas, rows, columns, channel, value)


def paint_line(canvas, extent, u0, w0, u1, w1, width, strength, channel):
    cut = window(canvas, extent, min(u0, u1) - width * 3.0, max(u0, u1) + width * 3.0, min(w0, w1) - width * 3.0, max(w0, w1) + width * 3.0)
    if cut is None:
        return
    rows, columns, us, vs = cut
    du = u1 - u0
    dw = w1 - w0
    span = max(du * du + dw * dw, 1e-9)
    blend = numpy.clip(((us[None, :] - u0) * du + (vs[:, None] - w0) * dw) / span, 0.0, 1.0)
    distance = numpy.sqrt((us[None, :] - (u0 + du * blend)) ** 2 + (vs[:, None] - (w0 + dw * blend)) ** 2)
    screen(canvas, rows, columns, channel, strength * numpy.exp(-(distance / width) ** 2))


def stain_extent(key, ops):
    lows = [1e9, 1e9]
    highs = [-1e9, -1e9]
    for op in ops:
        if op[0] == "drip":
            u, w, flow, strength, width, length = op[1:7]
            spans = ((u - width * 6.0 - 0.02, u + width * 6.0 + 0.02), (w - length * 3.0, w + 0.03) if flow < 0.0 else (w - 0.03, w + length * 3.0))
        elif op[0] == "halo":
            u, w, radius = op[1:4]
            spans = ((u - radius * 2.6, u + radius * 2.6), (w - radius * 2.6, w + radius * 2.6))
        elif op[0] == "ring":
            u, w, half_u, half_w, radius = op[1:6]
            spans = ((u - half_u - radius * 2.6, u + half_u + radius * 2.6), (w - half_w - radius * 2.6, w + half_w + radius * 2.6))
        else:
            u0, w0, u1, w1, width = op[1:6]
            spans = ((min(u0, u1) - width * 3.0, max(u0, u1) + width * 3.0), (min(w0, w1) - width * 3.0, max(w0, w1) + width * 3.0))
        for axis, (low, high) in enumerate(spans):
            lows[axis] = min(lows[axis], low)
            highs[axis] = max(highs[axis], high)
    limits = ((-1.8, 1.8), (-1.8, 1.8)) if key == "pz" else ((-1.8, 1.8), (-1.8, 3.2))
    return tuple(value for axis in range(2) for value in (max(lows[axis], limits[axis][0]), min(highs[axis], limits[axis][1])))


def bind_stains(part):
    entries = []
    for key in sorted(part.stains):
        ops = part.stains[key]
        if not ops:
            continue
        extent = stain_extent(key, ops)
        width = max(4, int(math.ceil((extent[1] - extent[0]) * stain_resolution)))
        height = max(4, int(math.ceil((extent[3] - extent[2]) * stain_resolution)))
        extent = (extent[0], extent[0] + width / stain_resolution, extent[2], extent[2] + height / stain_resolution)
        canvas = numpy.zeros((height, width, 4), dtype=numpy.float32)
        for op in ops:
            if op[0] == "drip":
                paint_drip(canvas, extent, *op[1:])
            elif op[0] == "halo":
                paint_halo(canvas, extent, *op[1:])
            elif op[0] == "ring":
                paint_ring(canvas, extent, *op[1:])
            else:
                paint_line(canvas, extent, *op[1:])
        for axis in (0, 1):
            canvas = (numpy.roll(canvas, 1, axis) + canvas * 2.0 + numpy.roll(canvas, -1, axis)) * 0.25
        picture = bpy.data.images.new(part.name + "_stain_" + key, width, height, alpha=True, float_buffer=False)
        picture.colorspace_settings.name = 'Non-Color'
        picture.alpha_mode = 'CHANNEL_PACKED'
        picture.pixels.foreach_set(numpy.ascontiguousarray(numpy.clip(canvas, 0.0, 1.0), dtype=numpy.float32).ravel())
        picture.update()
        entries.append((key, picture, extent))
        print("STAIN", part.name, key, width, "x", height, len(ops), "marks", flush=True)
    stain_images[part.name] = entries
    part.slots = [slot + "@" + part.name if slot.split("_")[0] in metal_kinds else slot for slot in part.slots]


def finish(part, sharp=32.0):
    if getattr(part, "stains", None) is not None:
        bind_stains(part)
    for look in part.slots:
        ensure(look)
    bm = bmesh.new()
    for mesh, index in part.meshes:
        before = len(bm.faces)
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        for face in bm.faces[before:]:
            face.material_index = index
        bpy.data.meshes.remove(mesh)
    removed = cull(bm, getattr(part, "cull_limit", 0.35))
    mesh = bpy.data.meshes.new(part.name)
    bm.to_mesh(mesh)
    bm.free()
    for look in part.slots:
        mesh.materials.append(k.material(look))
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.set_sharp_from_angle(angle=math.radians(sharp))
    obj = bpy.data.objects.new(part.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new("weighted", 'WEIGHTED_NORMAL')
    modifier.keep_sharp = True
    modifier.weight = 50
    bpy.context.view_layer.update()
    final = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    obj.modifiers.clear()
    obj.data = final
    bpy.data.meshes.remove(mesh)
    final.name = part.name
    print("CULLED", part.name, removed, "faces", flush=True)
    return obj


def weight_islands(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.index_update()
    bm.faces.index_update()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    layer = bm.loops.layers.uv.active
    samples = surface_samples(bm, False)
    seen = []
    for face in bm.faces:
        escaped, total = open_rays(tree, samples.get(face.index, []), 1000)
        seen.append(escaped / max(total, 1))
    parent = list(range(len(bm.faces)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            first, second = edge.link_faces
            corners = [{loop.vert.index: loop[layer].uv.copy() for loop in face.loops if loop.vert in edge.verts} for face in (first, second)]
            if all((corners[0][key] - corners[1][key]).length < 1e-5 for key in corners[0]):
                parent[root(first.index)] = root(second.index)
    islands = {}
    for face in bm.faces:
        islands.setdefault(root(face.index), []).append(face)
    for faces in islands.values():
        scale = 0.3 + 0.7 * math.sqrt(max(seen[face.index] for face in faces))
        loops = [loop for face in faces for loop in face.loops]
        center = sum((loop[layer].uv for loop in loops), Vector((0.0, 0.0))) / len(loops)
        for loop in loops:
            loop[layer].uv = center + (loop[layer].uv - center) * scale
            loop[layer].select = True
            loop[layer].select_edge = True
    bm.to_mesh(obj.data)
    bm.free()
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.view_layer.objects:
        other.select_set(other == obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.005)
    bpy.ops.object.mode_set(mode='OBJECT')


def turned(center, yaw=0.0, pitch=0.0, roll=0.0):
    return Matrix.Translation(center) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'Y') @ Matrix.Rotation(roll, 4, 'X')


def stamp(bm, rng, tint=None):
    seed = bm.verts.layers.float_vector.get("seed")
    if seed is None:
        seed = bm.verts.layers.float_vector.new("seed")
    value = bm.verts.layers.float.get("tint")
    if value is None:
        value = bm.verts.layers.float.new("tint")
    offset = (rng.uniform(0.0, 40.0), rng.uniform(0.0, 40.0), rng.uniform(0.0, 40.0))
    level = rng.random() if tint is None else tint
    for vert in bm.verts:
        vert[seed] = offset
        vert[value] = level
    return bm


def put(part, bm, look, rng, matrix=None, bevel=0.0, segments=1, tint=None):
    stamp(bm, rng, tint)
    part.add(bm, look, matrix, bevel, segments, 40.0)


def block(part, look, center, size, rng, yaw=0.0, pitch=0.0, roll=0.0, bevel=0.005, segments=1, tint=None):
    put(part, k.box(*size), look, rng, turned(center, yaw, pitch, roll), bevel, segments, tint)


def board(part, look, center, length, width, thickness, forward, up, rng, bevel=0.004, segments=1, tint=None):
    put(part, k.box(length, width, thickness), look, rng, k.place(center, forward, up), bevel, segments, tint)


def plank(part, look, start, end, width, thickness, up, rng, bow=0.004, bevel=0.004, tint=None):
    forward = (end - start).normalized()
    normal = (up - forward * up.dot(forward)).normalized()
    path = [start, (start + end) * 0.5 + normal * (rng.uniform(-1.0, 1.0) * bow), end]
    put(part, k.sweep(path, k.rectangle(width, thickness), up=normal), look, rng, None, bevel, 1, tint)


def stick(part, start, end, radius, rng, sides=6, wobble=1.0, taper=0.8, bend=None, look=None, count=None):
    axis = end - start
    length = axis.length
    forward = axis.normalized()
    side = (bend - forward * bend.dot(forward)).normalized() if bend is not None else (Matrix.Rotation(rng.uniform(0.0, math.tau), 3, forward) @ forward.orthogonal()).normalized()
    other = forward.cross(side)
    count = count or max(2, min(6, int(length / 0.5) + 2))
    amount = min(radius * 0.45, length * 0.012) * wobble
    lean = rng.uniform(-1.0, 1.0)
    drift = 0.0 if bend is not None else rng.uniform(-1.0, 1.0)
    path = []
    scales = []
    for index in range(count + 1):
        t = index / count
        arc = math.sin(math.pi * t)
        path.append(start + axis * t + side * (lean * arc * amount) + other * (drift * arc * amount * 0.6))
        scales.append((1.0 - (1.0 - taper) * t) * rng.uniform(0.95, 1.05))
    put(part, k.sweep(path, k.circle(radius, sides, rng.uniform(0.0, math.tau)), up=side, scales=scales), look or "bark_" + nearest(forward), rng)


def binding(part, center, axis, across, reach, width, rng, turns=2.5, wire=0.0055):
    forward = axis.normalized()
    side = (across - forward * across.dot(forward)).normalized()
    other = forward.cross(side)
    count = max(10, int(turns * 10))
    phase = rng.uniform(0.0, math.tau)
    path = []
    for index in range(count + 1):
        t = index / count
        angle = phase + math.tau * turns * t
        path.append(center + forward * (width * (t - 0.5)) + side * (math.cos(angle) * (reach[0] + wire)) + other * (math.sin(angle) * (reach[1] + wire)))
    put(part, k.sweep(path, k.circle(wire, 3), up=forward), "twine", rng)


def nail(part, center, normal, rng, radius=0.0065, look="iron"):
    head = k.revolve([(0.0, 0.0), (radius, 0.0), (radius * 0.9, radius * 0.4), (0.0, radius * 0.5)], 6, rng.uniform(0.0, 1.0))
    put(part, head, look, rng, k.axis_frame(center - normal * 0.001, normal))


def stain_key(normal):
    if normal.z > 0.3:
        return "pz"
    if abs(normal.y) >= abs(normal.x):
        return "py" if normal.y > 0.0 else "ny"
    return "px" if normal.x > 0.0 else "nx"


def stain_point(key, point):
    if key == "pz":
        return point.x, point.y
    if key in ("py", "ny"):
        return point.x, point.z
    return point.y, point.z


def stainable(part, normal):
    return getattr(part, "stains", None) is not None and normal.z > -0.3 and stain_key(normal) in part.stain_keys


def mark(part, point, normal, kind, *data):
    if stainable(part, normal):
        key = stain_key(normal)
        u, w = stain_point(key, point)
        part.stains.setdefault(key, []).append((kind, u, w) + data)


def drip(part, point, normal, rng, strength=1.0, width=0.008, length=0.35):
    if normal.z > 0.3 and abs(normal.y) < 0.2:
        mark(part, point, normal, "halo", width * rng.uniform(2.5, 4.0), strength * rng.uniform(0.4, 0.8), 2, rng.uniform(0.0, 100.0))
        return
    flow = (1.0 if normal.y > 0.0 else -1.0) if normal.z > 0.3 else -1.0
    mark(part, point, normal, "drip", flow, strength * rng.uniform(0.55, 1.0), width * rng.uniform(0.7, 1.3), length * rng.uniform(0.45, 1.4), rng.uniform(0.0, 100.0))


def halo(part, point, normal, radius, strength, rng, channel=2):
    mark(part, point, normal, "halo", radius, strength, channel, rng.uniform(0.0, 100.0))


def ring(part, center, across, up, width, height, normal, radius, strength, rng):
    if stainable(part, normal):
        key = stain_key(normal)
        u, w = stain_point(key, center)
        spans = [abs(value) for value in stain_point(key, across * (width * 0.5))]
        heights = [abs(value) for value in stain_point(key, up * (height * 0.5))]
        part.stains.setdefault(key, []).append(("ring", u, w, spans[0] + heights[0], spans[1] + heights[1], radius, strength, 2, rng.uniform(0.0, 100.0)))


def streak(part, start, end, normal, width, strength, channel):
    if stainable(part, normal):
        key = stain_key(normal)
        u0, w0 = stain_point(key, start)
        u1, w1 = stain_point(key, end)
        part.stains.setdefault(key, []).append(("line", u0, w0, u1, w1, width, strength, channel))


def seam(part, start, end, normal, rng, strength=0.6, spacing=0.05, length=0.25, chance=0.7):
    count = max(1, int((end - start).length / spacing))
    for index in range(count):
        if rng.random() < chance:
            drip(part, start.lerp(end, (index + rng.random()) / count), normal, rng, strength * rng.uniform(0.3, 1.0), rng.uniform(0.005, 0.012), length * rng.uniform(0.3, 1.2))
    streak(part, start, end, normal, 0.006, strength * 0.5, 1)


def frame_of(point, normal, rng):
    return k.axis_frame(point, normal) @ Matrix.Rotation(rng.uniform(0.0, 1.0), 4, 'X')


def chart(bm):
    return bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap"), bm.faces.layers.int.get("mapped") or bm.faces.layers.int.new("mapped")


def flat_chart(bm):
    layer, mapped = chart(bm)
    bm.normal_update()
    for face in bm.faces:
        face[mapped] = 1
        hidden = face.normal.x < -0.5
        for loop in face.loops:
            loop[layer].uv = (0.0, 0.0) if hidden else (loop.vert.co.y, loop.vert.co.z)
    return bm


def unrolled(bm, sides, stations, girths, outline=None):
    layer, mapped = chart(bm)
    bm.verts.index_update()
    for face in bm.faces:
        face[mapped] = 1
        rings = [loop.vert.index // sides for loop in face.loops]
        slots = [loop.vert.index % sides for loop in face.loops]
        if len(set(rings)) == 1:
            first = rings[0] == 0
            for loop, slot in zip(face.loops, slots):
                if outline is None:
                    loop[layer].uv = (stations[rings[0]], girths[-1] * 0.5)
                else:
                    loop[layer].uv = ((stations[0] - 0.2 - outline[slot][0]) if first else (stations[-1] + 0.2 + outline[slot][0]), outline[slot][1] + girths[-1] * 0.5)
            continue
        wrapped = 0 in slots and sides - 1 in slots
        for loop, ring, slot in zip(face.loops, rings, slots):
            loop[layer].uv = (stations[ring], girths[sides if wrapped and slot == 0 else slot])
    return bm


def girth(outline):
    result = [0.0]
    for index in range(len(outline)):
        first = outline[index]
        second = outline[(index + 1) % len(outline)]
        result.append(result[-1] + math.hypot(second[0] - first[0], second[1] - first[1]))
    return result


def tek(part, point, normal, rng, stain=0.85, tint=None):
    shade = rng.random() if tint is None else tint
    put(part, flat_chart(k.shifted(k.hexagon(0.012, 0.006, "x"), 0.0027)), "bolt", rng, frame_of(point, normal, rng), 0.0, 1, shade)
    if stain > 0.0:
        drip(part, point, normal, rng, stain, 0.011, 0.36)


def hex_bolt(part, point, normal, rng, across=0.019, washer=0.017, stain=1.0, tint=None):
    shade = rng.random() if tint is None else tint
    frame = frame_of(point, normal, rng)
    lift = 0.0
    if washer > 0.0:
        put(part, flat_chart(k.shifted(k.extrude(k.circle(washer, 8), 0.0025, "x"), 0.0009)), "bolt", rng, frame, 0.0, 1, shade)
        lift = 0.0021
    height = across * 0.4
    put(part, flat_chart(k.shifted(k.hexagon(across, height, "x"), lift + height * 0.5 - 0.0003)), "bolt", rng, frame, 0.0, 1, shade)
    if stain > 0.0:
        drip(part, point, normal, rng, stain, 0.015, 0.45)


def rivet(part, point, normal, rng, radius=0.0075, stain=0.6, tint=None):
    dome = k.revolve([(0.0, -0.0004), (radius, -0.0004), (radius * 0.72, radius * 0.5), (0.0, radius * 0.68)], 6, rng.uniform(0.0, 1.0))
    put(part, flat_chart(dome), "bolt", rng, k.axis_frame(point, normal), 0.0, 1, rng.random() if tint is None else tint)
    if stain > 0.0:
        drip(part, point, normal, rng, stain, 0.009, 0.26)


def bead(part, start, end, outward, rng, radius=0.0055, face=None, heat=0.6):
    span = end - start
    length = span.length
    if length < 0.004:
        return
    out = outward.normalized()
    count = max(2, int(length / (radius * 3.4)))
    path = [start.lerp(end, index / count) + out * (radius * 0.12) for index in range(count + 1)]
    scales = []
    for index in range(count + 1):
        reach = min(index, count - index) / count * length
        size = min(1.0, 0.5 + reach / (radius * 2.2)) * rng.uniform(0.88, 1.1)
        scales.append((size, size * rng.uniform(0.9, 1.12)))
    outline = k.ellipse(radius, radius * 0.62, 6)
    put(part, unrolled(k.sweep(path, outline, up=out, scales=scales), 6, [length * index / count for index in range(count + 1)], girth(outline)), "weld_" + nearest(span), rng)
    surface = face if face is not None else out
    if heat > 0.0:
        streak(part, start, end, surface, radius * 3.2, heat, 3)
        if rng.random() < 0.7:
            drip(part, start.lerp(end, rng.random()), surface, rng, 0.7, 0.006, 0.25)


def stitch(part, start, end, outward, rng, face=None, length=0.05, gap=0.12):
    span = (end - start).length
    count = max(1, int((span + gap) / (length + gap)))
    spare = (span - count * length) / max(count, 1)
    for index in range(count):
        first = (spare * 0.5 + index * (length + spare)) / span
        bead(part, start.lerp(end, first), start.lerp(end, first + length / span), outward, rng, 0.0045, face)


def rounded(width, depth, radius=0.005, segments=2):
    return k.fillet(k.rectangle(width, depth), radius, segments)


def tube(part, start, end, width, depth, up, rng, tint, radius=0.005, look="frame"):
    outline = rounded(width, depth, radius)
    put(part, unrolled(k.sweep([start, end], outline, up=up), len(outline), [0.0, (end - start).length], girth(outline), outline), look, rng, None, 0.0, 1, tint)


def paint_tint(rng, avoid=-1, weights=(0.33, 0.3, 0.22, 0.15)):
    zones = ((0.02, 0.28), (0.32, 0.56), (0.6, 0.8), (0.84, 0.98))
    index = rng.choices(range(4), weights)[0]
    for attempt in range(8):
        if index != avoid:
            break
        index = rng.choices(range(4), weights)[0]
    return rng.uniform(*zones[index]), index


def panel_sheet(part, look, origin, across, up, width, height, rng, corrugated=True, tint=None, thickness=0.0012, pitch=0.076, depth=0.018, rows=None, lift=None, top=None, columns=None, capped=True):
    normal = across.cross(up).normalized()
    phase = origin.dot(across)
    if corrugated:
        step = pitch / 5.0
        us = [0.0]
        position = (math.floor(phase / step) + 1.0) * step - phase
        while position < width - 0.002:
            if position > 0.002:
                us.append(position)
            position += step
        us.append(width)
    else:
        count = columns or max(1, int(round(width / 0.25)))
        us = [width * index / count for index in range(count + 1)]
    fractions = rows or [0.0, 1.0]

    def wave(u):
        return depth * 0.5 * (1.0 + math.sin(math.tau * (u + phase) / pitch)) if corrugated else 0.0

    bm = bmesh.new()
    front = []
    rear = []
    for u in us:
        reach = height if top is None else top(u)
        front_column = []
        rear_column = []
        for fraction in fractions:
            along = reach * fraction
            base = origin + across * u + up * along + normal * (wave(u) + (lift(u, along) if lift else 0.0))
            rear_column.append(bm.verts.new(base))
            front_column.append(bm.verts.new(base + normal * thickness))
        front.append(front_column)
        rear.append(rear_column)
    for i in range(len(us) - 1):
        for j in range(len(fractions) - 1):
            bm.faces.new((front[i][j], front[i + 1][j], front[i + 1][j + 1], front[i][j + 1]))
        bm.faces.new((front[i][0], rear[i][0], rear[i + 1][0], front[i + 1][0]))
        if capped:
            bm.faces.new((front[i][-1], front[i + 1][-1], rear[i + 1][-1], rear[i][-1]))
    for j in range(len(fractions) - 1):
        bm.faces.new((front[0][j], front[0][j + 1], rear[0][j + 1], rear[0][j]))
        bm.faces.new((front[-1][j], rear[-1][j], rear[-1][j + 1], front[-1][j + 1]))
    layer, mapped = chart(bm)
    placed = {}
    run = 0.0
    for i, u in enumerate(us):
        run += math.hypot(u - us[i - 1], wave(u) - wave(us[i - 1])) if i else 0.0
        reach = height if top is None else top(u)
        for j, fraction in enumerate(fractions):
            placed[front[i][j]] = placed[rear[i][j]] = (run, reach * fraction)
    for face in bm.faces:
        face[mapped] = 1
        for loop in face.loops:
            loop[layer].uv = placed[loop.vert]
    put(part, bm, look, rng, None, 0.0, 1, tint)
    return {"origin": origin, "across": across, "up": up, "normal": normal, "width": width, "height": height, "wave": wave, "lift": lift, "thickness": thickness, "top": top, "corrugated": corrugated, "pitch": pitch, "depth": depth, "phase": phase}


def on_sheet(sheet, u, along, extra=0.0):
    lift = sheet["lift"](u, along) if sheet["lift"] else 0.0
    return sheet["origin"] + sheet["across"] * u + sheet["up"] * along + sheet["normal"] * (sheet["wave"](u) + lift + sheet["thickness"] + extra)


def flutes(sheet, low, high, crest, every, spacing=0.2):
    if not sheet["corrugated"]:
        count = max(1, int(round((high - low) / spacing)))
        return [low + (high - low) * index / count for index in range(count + 1)] if high > low else []
    target = 0.25 if crest else 0.75
    number = math.ceil((low + sheet["phase"]) / sheet["pitch"] - target)
    result = []
    while True:
        u = (number + target) * sheet["pitch"] - sheet["phase"]
        if u > high:
            return result
        if u >= low:
            result.append(u)
        number += every


def bend(rng, width, height, corrugated, chance, corner_high=False):
    effects = []
    heights = [0.0, 1.0]
    widths = None
    if rng.random() < chance:
        corner_u = rng.choice((0.0, width))
        corner_w = height if corner_high else 0.0
        amount = rng.uniform(0.008, 0.02)
        reach_u = rng.uniform(0.15, 0.3)
        reach_w = min(rng.uniform(0.2, 0.34), height * 0.45)
        effects.append(lambda u, w: amount * max(0.0, 1.0 - abs(u - corner_u) / reach_u) ** 2 * max(0.0, 1.0 - abs(w - corner_w) / reach_w) ** 2)
        marks = [reach_w * fraction for fraction in (0.3, 0.6, 1.0)]
        heights += [(height - value if corner_high else value) / height for value in marks]
    if not corrugated:
        bow = rng.uniform(-0.003, 0.006)
        effects.append(lambda u, w: bow * math.sin(math.pi * min(max(u / width, 0.0), 1.0)) * math.sin(math.pi * min(max(w / height, 0.0), 1.0)))
        for index in range(rng.randint(0, 2)):
            center_u = rng.uniform(0.2, 0.8) * width
            center_w = rng.uniform(0.2, 0.8) * height
            radius = rng.uniform(0.06, 0.13)
            depth = rng.uniform(0.004, 0.009)
            effects.append(lambda u, w, center_u=center_u, center_w=center_w, radius=radius, depth=depth: -depth * math.exp(-((u - center_u) ** 2 + (w - center_w) ** 2) / (radius * radius)))
        heights += [index / max(1, int(round(height / 0.13))) for index in range(1, max(1, int(round(height / 0.13))))]
        widths = max(2, int(round(width / 0.13)))
    lift = (lambda u, w: sum(effect(u, w) for effect in effects)) if effects else None
    return lift, sorted(set(round(value, 5) for value in heights)), widths


def clad(part, panel, rng, rows, corrugated_share=0.72, crest=False, every=5, split_chance=0.28, bent=0.3, look="scrap_z", lap_every=0.36, weights=(0.33, 0.3, 0.22, 0.15), top=None):
    origin = panel["origin"]
    across = panel["across"]
    up = panel["up"]
    normal = panel["normal"]
    width = panel["width"]
    height = panel["height"]
    inset = 0.004
    columns = split(inset, width - inset, rng, 0.72, 1.08)
    kinds = [rng.random() < corrugated_share for column in columns]
    order = sorted(range(len(columns)), key=lambda index: (kinds[index], rng.random()))
    layer = {index: rank for rank, index in enumerate(order)}
    extents = [[a, b] for a, b in columns]
    under = [[False, False] for column in columns]
    laps = []
    for index in range(1, len(columns)):
        lap = 0.076 if kinds[index] and kinds[index - 1] else 0.05
        if layer[index] > layer[index - 1]:
            extents[index][0] -= lap
            under[index - 1][1] = True
            laps.append((index, 0))
        else:
            extents[index - 1][1] += lap
            under[index][0] = True
            laps.append((index - 1, 1))
    made = {}
    zone = -1
    for index in order:
        a, b = extents[index]
        tint, zone = paint_tint(rng, zone, weights)
        low = inset
        high = (height if top is None else min(top(a), top(b))) - inset
        pieces = [(low, height - inset if top is None else None, 0)]
        if top is None and rng.random() < split_chance and high - low > 0.9:
            cut = rng.uniform(low + 0.4, high - 0.4)
            pieces = [(low, cut + 0.09, 0), (cut, height - inset, 1)]
        for bottom, ceiling, extra in pieces:
            span = (ceiling - bottom) if ceiling is not None else height
            lift, heights, widths = bend(rng, b - a, span, kinds[index], bent if extra == 0 else bent * 0.5, extra == 1)
            offset = 0.0014 * (layer[index] + extra * len(columns))
            sheet_top = (lambda u, a=a, bottom=bottom: top(u + a) - inset - bottom) if top is not None else None
            sheet = panel_sheet(part, look, origin + across * a + up * bottom + normal * offset, across, up, b - a, span, rng, kinds[index], tint, rows=heights, lift=lift, top=sheet_top, columns=widths, capped=False)
            sheet["tint"] = tint
            sheet["range"] = (a, b)
            made.setdefault(index, []).append((sheet, bottom, bottom + span, extra, len(pieces)))
            left = 0.03 + (0.09 if under[index][0] else 0.0)
            right = b - a - 0.03 - (0.09 if under[index][1] else 0.0)
            for row in rows:
                local = row - bottom
                covered = extra == 0 and len(pieces) > 1 and local > span - 0.12
                if 0.02 < local < span - 0.02 and not covered and (sheet_top is None or local < min(sheet_top(left), sheet_top(right)) - 0.03):
                    for u in flutes(sheet, left, right, crest, every):
                        tek(part, on_sheet(sheet, u, local), normal, rng)
            if extra == 1:
                for u in flutes(sheet, left, right, crest, 3):
                    tek(part, on_sheet(sheet, u, 0.045), normal, rng)
                seam(part, on_sheet(sheet, 0.0, 0.0), on_sheet(sheet, b - a, 0.0), normal, rng, 0.55, 0.05, 0.3)
    for index, edge in laps:
        for sheet, bottom, ceiling, extra, count in made[index]:
            u_edge = 0.0 if edge == 0 else sheet["width"]
            inward = 0.035 if edge == 0 else -0.035
            if sheet["corrugated"]:
                choices = flutes(sheet, min(u_edge, u_edge + inward * 2.2), max(u_edge, u_edge + inward * 2.2), True, 1)
                u = (choices[0] if edge == 0 else choices[-1]) if choices else u_edge + inward
            else:
                u = u_edge + inward
            span = ceiling - bottom
            steps = max(1, int((span - 0.2) / lap_every))
            for step in range(steps + 1):
                along = 0.1 + (span - 0.2) * step / max(steps, 1)
                if sheet["top"] is None or along < sheet["top"](u) - 0.06:
                    tek(part, on_sheet(sheet, u, along), normal, rng)
            reach = span if sheet["top"] is None else sheet["top"](u_edge)
            streak(part, on_sheet(sheet, u_edge, 0.0), on_sheet(sheet, u_edge, reach), normal, 0.004, 0.5, 1)
    return made


def surface_offset(made, low, high):
    result = 0.0
    for entries in made.values():
        for sheet, bottom, ceiling, extra, count in entries:
            a, b = sheet["range"]
            if a < high[0] and b > low[0] and bottom < high[1] and ceiling > low[1]:
                result = max(result, sheet["origin"].dot(sheet["normal"]) + sheet["thickness"] + (sheet["depth"] if sheet["corrugated"] else 0.004))
    return result


def overlay(part, panel, made, rng, patch, fixing, taken):
    width = panel["width"]
    height = panel["height"]
    if patch:
        size_u = rng.uniform(0.14, 0.3)
        size_w = size_u * rng.uniform(0.75, 1.3)
    else:
        size_u = rng.uniform(0.45, min(1.0, width - 0.16))
        size_w = rng.uniform(0.4, min(0.9, height - 0.16))
    if size_u > width - 0.1 or size_w > height - 0.1:
        return
    for attempt in range(12):
        a = rng.uniform(0.05, width - size_u - 0.05)
        bottom = rng.uniform(0.05, height - size_w - 0.05)
        box_low = panel["origin"] + panel["across"] * a + panel["up"] * bottom
        box_high = box_low + panel["across"] * size_u + panel["up"] * size_w
        low = v(min(box_low.x, box_high.x), min(box_low.y, box_high.y), min(box_low.z, box_high.z))
        high = v(max(box_low.x, box_high.x), max(box_low.y, box_high.y), max(box_low.z, box_high.z))
        if not any(all(low[axis] < other_high[axis] + 0.04 and high[axis] > other_low[axis] - 0.04 for axis in range(3)) for other_low, other_high in taken):
            break
    else:
        return
    taken.append((low - panel["normal"] * 0.5, high + panel["normal"] * 0.5))
    across = panel["across"]
    up = panel["up"]
    normal = panel["normal"]
    base = panel["origin"].dot(normal)
    lifted = max(0.0, surface_offset(made, (a, bottom), (a + size_u, bottom + size_w)) - base) + 0.0008
    tint, zone = paint_tint(rng)
    origin = panel["origin"] + across * a + up * bottom + normal * lifted
    thickness = 0.003 if patch else 0.0025
    lift, heights, widths = bend(rng, size_u, size_w, False, 0.0 if patch else 0.25)
    sheet = panel_sheet(part, "scrap_" + nearest(up), origin, across, up, size_u, size_w, rng, False, tint, thickness, rows=heights, lift=lift, columns=widths)
    center = on_sheet(sheet, size_u * 0.5, size_w * 0.5)
    if patch:
        ring(part, center, across, up, size_u, size_w, normal, rng.uniform(0.04, 0.09), rng.uniform(0.7, 1.0), rng)
    corners = [(0.0, 0.0), (size_u, 0.0), (size_u, size_w), (0.0, size_w)]
    if fixing == "weld":
        for index in range(4):
            u0, w0 = corners[index]
            u1, w1 = corners[(index + 1) % 4]
            direction = across * (u1 - u0) + up * (w1 - w0)
            out = direction.normalized().cross(normal)
            out = out if out.dot(across * (u0 + u1 - size_u) + up * (w0 + w1 - size_w)) > 0.0 else -out
            start = on_sheet(sheet, u0, w0, -thickness * 0.5)
            end = on_sheet(sheet, u1, w1, -thickness * 0.5)
            if patch:
                bead(part, start, end, normal + out, rng, 0.0045, normal)
            else:
                stitch(part, start, end, normal + out, rng, normal)
    else:
        inset = 0.016 if patch else 0.026
        spacing = 0.065 if patch else 0.19
        for index in range(4):
            u0, w0 = corners[index]
            u1, w1 = corners[(index + 1) % 4]
            u0 += inset if u0 < size_u * 0.5 else -inset
            u1 += inset if u1 < size_u * 0.5 else -inset
            w0 += inset if w0 < size_w * 0.5 else -inset
            w1 += inset if w1 < size_w * 0.5 else -inset
            span = math.hypot(u1 - u0, w1 - w0)
            count = max(1, int(round(span / spacing)))
            for step in range(count):
                u = u0 + (u1 - u0) * step / count
                w = w0 + (w1 - w0) * step / count
                if patch:
                    rivet(part, on_sheet(sheet, u, w), normal, rng)
                else:
                    hex_bolt(part, on_sheet(sheet, u, w), normal, rng, 0.017, 0.015, 0.9)
    seam(part, on_sheet(sheet, 0.0, 0.0), on_sheet(sheet, size_u, 0.0), normal, rng, 0.7, 0.04, 0.3)


def slab(part, look, outline, axis, offset, thickness, rng, bevel=0.004, segments=1, tint=None):
    shift = v(offset, 0.0, 0.0) if axis == "x" else v(0.0, offset, 0.0)
    put(part, k.extrude(outline, thickness, axis), look, rng, Matrix.Translation(shift), bevel, segments, tint)


def split(start, end, rng, low, high):
    span = end - start
    count = max(1, int(round(span / ((low + high) * 0.5))))
    weights = [rng.uniform(low, high) for index in range(count)]
    total = sum(weights)
    edges = [start]
    for weight in weights:
        edges.append(edges[-1] + span * weight / total)
    return list(zip(edges[:-1], edges[1:]))


def stone(part, look, low, high, rng, bevel=0.015, jitter=0.006, tint=None, segments=1):
    size = high - low
    bm = k.box(size.x, size.y, size.z)
    for vert in bm.verts:
        vert.co += v(rng.uniform(-jitter, jitter), rng.uniform(-jitter, jitter), rng.uniform(-jitter, jitter))
    put(part, bm, look, rng, Matrix.Translation((low + high) * 0.5), bevel * rng.uniform(0.8, 1.3), segments, tint)


def roof_point(side, t, height, x=0.0):
    return v(x, 0.0, rise) + v(0.0, side * 1.5, -rise) * (t / slope) + v(0.0, side * rise, 1.5) * (height / slope)


def roof_top(y):
    return rise - abs(y) * rise / 1.5


def gable_outline(y0, y1, lift, floor=0.0):
    points = [(y0, floor), (y1, floor), (y1, roof_top(y1) + lift)]
    if y0 < 0.0 < y1:
        points.append((0.0, rise + lift))
    points.append((y0, roof_top(y0) + lift))
    return points


def twig_lattice(part, region, rng, spacing=0.2, radius=0.018, depth=0.032):
    x0, x1, z0, z1 = region
    segments = []
    for direction, y in ((1.0, depth), (-1.0, -depth)):
        step = spacing * math.sqrt(2.0)
        low, high = (z0 - x1, z1 - x0) if direction > 0.0 else (z0 + x0, z1 + x1)
        c = low + rng.uniform(0.2, 0.8) * step
        while c < high:
            a, b = (max(x0, z0 - c), min(x1, z1 - c)) if direction > 0.0 else (max(x0, c - z1), min(x1, c - z0))
            if b - a > 0.1 and rng.random() > 0.06:
                start = v(a, y, direction * a + c)
                end = v(b, y, direction * b + c)
                start = v(min(max(start.x + rng.uniform(-0.06, 0.06), x0), x1), y, min(max(start.z + rng.uniform(-0.06, 0.06), z0), z1))
                end = v(min(max(end.x + rng.uniform(-0.06, 0.06), x0), x1), y, min(max(end.z + rng.uniform(-0.06, 0.06), z0), z1))
                if rng.random() < 0.12:
                    end = start.lerp(end, rng.uniform(0.55, 0.85))
                if (end - start).length > 0.1:
                    stick(part, start, end, radius * rng.uniform(0.8, 1.25), rng, 5, 1.6, 0.75, (end - start).cross(v(0.0, 1.0, 0.0)), None, max(2, min(3, int((end - start).length / 0.7) + 1)))
                    segments.append((direction, start, end))
            c += step * rng.uniform(0.85, 1.15)
    for index in range(max(1, int((x1 - x0) * 1.2))):
        x = rng.uniform(x0 + 0.05, x1 - 0.05)
        start = v(x, 0.0, z0 + rng.uniform(0.0, 0.1))
        end = v(min(max(x + rng.uniform(-0.25, 0.25), x0 + 0.02), x1 - 0.02), 0.0, z1 - rng.uniform(0.0, 0.25))
        stick(part, start, end, rng.uniform(0.01, 0.013), rng, 5, 1.2, 0.7, v(1.0, 0.0, 0.0), None, 3)
    return segments


def twig_sprigs(part, segments, region, rng, count):
    x0, x1, z0, z1 = region
    placed = 0
    for attempt in range(count * 6):
        if placed >= count or not segments:
            break
        direction, start, end = segments[rng.randrange(len(segments))]
        base = start.lerp(end, rng.uniform(0.2, 0.8))
        turn = Matrix.Rotation(rng.choice((-1.0, 1.0)) * rng.uniform(0.4, 0.9), 3, 'Y')
        heading = (turn @ (end - start).normalized() + v(0.0, rng.uniform(-0.25, 0.25), 0.0)).normalized()
        tip = base + heading * rng.uniform(0.07, 0.16)
        if x0 + 0.02 < tip.x < x1 - 0.02 and z0 + 0.02 < tip.z < z1 - 0.02 and abs(tip.y) < 0.1:
            stick(part, base, tip, 0.007, rng, 4, 0.5, 0.4, None, None, 2)
            placed += 1


def twig_knots(part, segments, region, rng, count):
    x0, x1, z0, z1 = region
    fronts = [entry for entry in segments if entry[0] > 0.0]
    backs = [entry for entry in segments if entry[0] < 0.0]
    crossings = []
    for front in fronts:
        for back in backs:
            d1 = front[2] - front[1]
            d2 = back[2] - back[1]
            denominator = d1.x * d2.z - d1.z * d2.x
            if abs(denominator) < 1e-6:
                continue
            offset = back[1] - front[1]
            t = (offset.x * d2.z - offset.z * d2.x) / denominator
            u = (offset.x * d1.z - offset.z * d1.x) / denominator
            point = front[1] + d1 * t
            if 0.1 < t < 0.9 and 0.1 < u < 0.9 and x0 + 0.08 < point.x < x1 - 0.08 and z0 + 0.08 < point.z < z1 - 0.08:
                crossings.append(v(point.x, 0.0, point.z))
    rng.shuffle(crossings)
    for center in crossings[:count]:
        binding(part, center, v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0), (0.028, 0.056), 0.05, rng, 2.0, 0.0045)


def twig_wall(kind):
    rng = random.Random(1000 + pieces.index(kind))
    part = k.assembly("twig_" + kind)
    hole = openings[kind]
    posts = [-1.43, 1.43]
    for x in posts:
        stick(part, v(x + rng.uniform(-0.01, 0.01), 0.0, 0.0), v(x + rng.uniform(-0.012, 0.012), 0.0, 3.0), 0.062, rng, 7, 0.5, 0.88, v(1.0, 0.0, 0.0))
    rails = [(0.12, hole is not None and hole[2] < 0.2), (1.5, hole is not None), (2.9, False)]
    for z, broken in rails:
        for a, b in ([(-1.49, -0.6), (0.6, 1.49)] if broken else [(-1.49, 1.49)]):
            for side in (-1.0, 1.0):
                stick(part, v(a, side * 0.093, z + rng.uniform(-0.015, 0.015)), v(b, side * 0.093, z + rng.uniform(-0.015, 0.015)), 0.038 * rng.uniform(0.9, 1.1), rng, 6, 0.6, 0.85, v(0.0, 0.0, 1.0))
        for x in posts:
            binding(part, v(x, 0.0, z), v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0), (0.068, 0.068), 0.1, rng, 3.0)
    regions = [(-1.36, 1.36, 0.05, 2.95)]
    if hole is not None:
        left, right, bottom, top = hole
        for x in (left - 0.07, right + 0.07):
            stick(part, v(x, 0.0, 0.0), v(x, 0.0, 3.0), 0.05, rng, 7, 0.4, 0.9, v(1.0, 0.0, 0.0))
        bars = [top + 0.05] + ([bottom - 0.05] if bottom > 0.2 else [])
        for z in bars:
            for side in (-1.0, 1.0):
                stick(part, v(left - 0.2, side * 0.085, z), v(right + 0.2, side * 0.085, z), 0.036, rng, 6, 0.4, 0.9, v(0.0, 0.0, 1.0))
            for x in (left - 0.07, right + 0.07):
                binding(part, v(x, 0.0, z), v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0), (0.056, 0.056), 0.09, rng, 3.0)
        regions = [(-1.36, left - 0.12, 0.05, 2.95), (right + 0.12, 1.36, 0.05, 2.95), (left - 0.02, right + 0.02, top + 0.09, 2.95)]
        if bottom > 0.2:
            regions.append((left - 0.02, right + 0.02, 0.05, bottom - 0.09))
    for region in regions:
        segments = twig_lattice(part, region, rng)
        area = (region[1] - region[0]) * (region[3] - region[2])
        twig_knots(part, segments, region, rng, max(1, int(area * 0.35)))
        twig_sprigs(part, segments, region, rng, max(1, int(area * 1.4)))
    return finish(part, 75.0)


def twig_foundation():
    rng = random.Random(1100)
    part = k.assembly("twig_foundation")
    corners = [v(-1.36, -1.36, 0.0), v(1.36, -1.36, 0.0), v(1.36, 1.36, 0.0), v(-1.36, 1.36, 0.0)]
    for corner in corners:
        stick(part, corner + v(0.0, 0.0, -1.6), corner + v(rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01), -0.07), 0.07, rng, 7, 0.4, 0.9)
    count = 25
    for index in range(count):
        y = -1.44 + 2.88 * index / (count - 1) + rng.uniform(-0.005, 0.005)
        radius = rng.uniform(0.052, 0.06)
        stick(part, v(-1.5 + rng.uniform(0.0, 0.05), y, -radius), v(1.5 - rng.uniform(0.0, 0.05), y, -radius), radius, rng, 7, 0.35, 0.86, v(0.0, 1.0, 0.0), None, 3)
    for x in (-1.05, 0.0, 1.05):
        stick(part, v(x, -1.45, -0.18), v(x, 1.45, -0.18), 0.07, rng, 7, 0.4, 0.9, v(1.0, 0.0, 0.0))
    for index in range(4):
        a = corners[index]
        b = corners[(index + 1) % 4]
        along = (b - a).normalized()
        out = v(along.y, -along.x, 0.0)
        lift = 0.085 if index % 2 else 0.0
        for z in (-0.25, -1.47):
            stick(part, a + out * 0.105 - along * 0.13 + v(0.0, 0.0, z + lift + rng.uniform(-0.015, 0.015)), b + out * 0.105 + along * 0.13 + v(0.0, 0.0, z + lift + rng.uniform(-0.015, 0.015)), 0.042, rng, 7, 0.5, 0.85, v(0.0, 0.0, 1.0))
        stick(part, a + out * 0.035 + v(0.0, 0.0, -1.5), b + out * 0.035 + v(0.0, 0.0, -0.32), 0.028, rng, 6, 0.5, 0.8, out)
        stick(part, a + out * 0.095 + v(0.0, 0.0, -0.32), b + out * 0.095 + v(0.0, 0.0, -1.5), 0.028, rng, 6, 0.5, 0.8, out)
        for fraction in (0.14, 0.28, 0.42, 0.58, 0.72, 0.86):
            base = a.lerp(b, fraction + rng.uniform(-0.02, 0.02)) - out * 0.03
            stick(part, base + v(0.0, 0.0, -1.58), base + v(rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), rng.uniform(-0.26, -0.18)), rng.uniform(0.024, 0.032), rng, 5, 0.7, 0.8, None, None, 3)
        for z, depth in ((-0.62, 0.0), (-0.78, -0.06), (-1.12, 0.0), (-1.28, -0.06)):
            stick(part, a + out * depth + along * 0.1 + v(0.0, 0.0, z + rng.uniform(-0.02, 0.02)), b + out * depth - along * 0.1 + v(0.0, 0.0, z + rng.uniform(-0.02, 0.02)), rng.uniform(0.016, 0.021), rng, 5, 1.5, 0.8, v(0.0, 0.0, 1.0), None, 3)
        binding(part, a.lerp(b, 0.5) + out * 0.065 + v(0.0, 0.0, -0.91), out, along, (0.065, 0.04), 0.07, rng, 2.0, 0.005)
        for corner, sign in ((a, 1.0), (b, -1.0)):
            binding(part, corner + out * 0.04 + along * (sign * 0.02) + v(0.0, 0.0, -0.25 + lift), along, out, (0.11, 0.046), 0.09, rng, 2.2)
    return finish(part, 75.0)


def twig_floor():
    rng = random.Random(1400)
    part = k.assembly("twig_floor")
    count = 26
    ys = []
    for index in range(count):
        y = -1.44 + 2.88 * index / (count - 1) + rng.uniform(-0.004, 0.004)
        radius = rng.uniform(0.05, 0.057)
        ys.append(y)
        stick(part, v(-1.5 + rng.uniform(0.0, 0.025), y, -radius), v(1.5 - rng.uniform(0.0, 0.025), y, -radius), radius, rng, 6, 0.35, 0.86, v(0.0, 1.0, 0.0), None, 3)
    for x in (-1.15, 0.0, 1.15):
        stick(part, v(x, -1.47, -0.17), v(x, 1.47, -0.17), 0.066, rng, 7, 0.4, 0.9, v(1.0, 0.0, 0.0))
        for y in (ys[0], ys[count // 2], ys[-1]):
            binding(part, v(x, y, -0.113), v(1.0, 0.0, 0.0), v(0.0, 0.0, 1.0), (0.12, 0.066), 0.08, rng, 2.0)
    return finish(part, 75.0)


def twig_stairs():
    rng = random.Random(1500)
    part = k.assembly("twig_stairs")
    for x in (-1.17, 1.17):
        stick(part, v(x, -1.55, 0.03), v(x, 1.42, 3.0), 0.066, rng, 7, 0.4, 0.9, v(1.0, 0.0, 0.0))
        stick(part, v(x, 1.42, 0.0), v(x, 1.42, 3.0), 0.062, rng, 7, 0.4, 0.9, v(1.0, 0.0, 0.0))
        stick(part, v(x, 0.0, 0.0), v(x, 0.0, 1.58), 0.055, rng, 7, 0.4, 0.9, v(1.0, 0.0, 0.0))
        stick(part, v(x, -1.47, 0.05), v(x, 1.48, 0.05), 0.048, rng, 6, 0.4, 0.9, v(0.0, 0.0, 1.0))
        stick(part, v(x, -0.75, 0.0), v(x, -0.75, 0.83), 0.03, rng, 6, 0.5, 0.8, v(0.0, 1.0, 0.0), None, 3)
        stick(part, v(x, 0.72, 0.0), v(x, 0.72, 2.3), 0.032, rng, 6, 0.5, 0.8, v(0.0, 1.0, 0.0), None, 4)
        stick(part, v(x, 0.02, 0.08), v(x, 1.4, 1.85), 0.03, rng, 6, 0.5, 0.8, v(1.0, 0.0, 0.0), None, 4)
        binding(part, v(x, 0.0, 1.58), v(0.0, 1.0, 1.0), v(1.0, 0.0, 0.0), (0.075, 0.075), 0.1, rng, 2.2)
        binding(part, v(x, 1.42, 3.0), v(0.0, 1.0, 1.0), v(1.0, 0.0, 0.0), (0.075, 0.075), 0.1, rng, 2.2)
    for step in range(12):
        top = 0.25 * (step + 1)
        for offset in (0.07, 0.185):
            radius = rng.uniform(0.037, 0.043)
            y = -1.5 + 0.25 * step + offset
            stick(part, v(-1.13, y, top - radius), v(1.13, y, top - radius), radius, rng, 6, 0.4, 0.88, v(0.0, 1.0, 0.0), None, 3)
        if step % 2 == 0:
            for x in (-1.17, 1.17):
                binding(part, v(x, -1.5 + 0.25 * step + 0.128, top - 0.04), v(0.0, 1.0, 1.0), v(1.0, 0.0, 0.0), (0.072, 0.072), 0.1, rng, 2.5)
    return finish(part, 75.0)


def twig_roof():
    rng = random.Random(1600)
    part = k.assembly("twig_roof")
    rafters = (-1.42, -0.71, 0.0, 0.71, 1.42)
    for side in (-1.0, 1.0):
        for x in rafters:
            stick(part, roof_point(side, 1.85, -0.045, x + rng.uniform(-0.02, 0.02)), roof_point(side, -0.05, -0.045, x + rng.uniform(-0.02, 0.02)), 0.046, rng, 6, 0.4, 0.85, v(1.0, 0.0, 0.0))
            binding(part, roof_point(side, 1.8, -0.02, x), v(0.0, 1.0, 0.0), v(0.0, 0.0, 1.0), (0.07, 0.05), 0.09, rng, 2.0)
        stick(part, roof_point(side, 1.94, 0.015, -1.52), roof_point(side, 1.94, 0.015, 1.52), 0.042, rng, 6, 0.4, 0.88, v(0.0, 0.0, 1.0))
        t = 0.08
        while t < 1.92:
            stick(part, roof_point(side, t, 0.027, -1.51 + rng.uniform(0.0, 0.04)), roof_point(side, t + rng.uniform(-0.02, 0.02), 0.027, 1.51 - rng.uniform(0.0, 0.04)), rng.uniform(0.022, 0.03), rng, 5, 0.6, 0.8, v(0.0, 0.0, 1.0), None, 3)
            t += rng.uniform(0.09, 0.11)
    stick(part, v(-1.54, 0.0, rise + 0.035), v(1.54, 0.0, rise + 0.035), 0.055, rng, 7, 0.4, 0.88, v(0.0, 0.0, 1.0))
    for x in rafters:
        binding(part, v(x, 0.0, rise + 0.02), v(1.0, 0.0, 0.0), v(0.0, 1.0, 0.0), (0.062, 0.07), 0.1, rng, 2.5)
        stick(part, v(x, -1.45, 0.045), v(x, 1.45, 0.045), 0.042, rng, 6, 0.4, 0.88, v(0.0, 0.0, 1.0))
    for index in range(18):
        y = -1.36 + 2.72 * index / 17.0
        stick(part, v(-1.46, y + rng.uniform(-0.02, 0.02), 0.103), v(1.46, y + rng.uniform(-0.02, 0.02), 0.103), rng.uniform(0.017, 0.022), rng, 5, 0.6, 0.8, v(0.0, 1.0, 0.0), None, 3)
    for sign in (-1.0, 1.0):
        x = sign * 1.47
        stick(part, v(x, -1.5, 0.05), v(x, 1.5, 0.05), 0.04, rng, 6, 0.4, 0.88, v(0.0, 0.0, 1.0))
        stick(part, v(x, -0.72, 0.62), v(x, 0.72, 0.62), 0.03, rng, 6, 0.4, 0.85, v(0.0, 0.0, 1.0))
        y = -1.34
        while y < 1.38:
            stick(part, v(x + rng.uniform(-0.01, 0.01), y, 0.02), v(x + rng.uniform(-0.01, 0.01), y + rng.uniform(-0.03, 0.03), roof_top(y) - 0.02), rng.uniform(0.02, 0.026), rng, 5, 0.6, 0.8, v(0.0, 1.0, 0.0), None, 3)
            y += rng.uniform(0.16, 0.2)
    return finish(part, 75.0)


def wood_boards(part, region, side, rng, look="plank_z_y"):
    x0, x1, z0, z1 = region
    placed = []
    for a, b in split(x0, x1, rng, 0.17, 0.27):
        gap = rng.uniform(0.004, 0.011)
        width = b - a - gap
        thickness = rng.uniform(0.03, 0.036)
        y = side * (0.08 + thickness * 0.5 + rng.uniform(-0.002, 0.002))
        x = (a + b) * 0.5
        plank(part, look, v(x + rng.uniform(-0.003, 0.003), y, z0 + rng.uniform(0.0, 0.012)), v(x + rng.uniform(-0.003, 0.003), y, z1 - rng.uniform(0.0, 0.02)), width, thickness, v(0.0, side, 0.0), rng, 0.005, 0.004)
        placed.append((x, width))
    return placed


def strap(part, corner, side, rng):
    face = side * 0.1475
    reach = -1.0 if corner.x > 0.0 else 1.0
    block(part, "iron", v(corner.x + reach * 0.13, face, corner.z), (0.3, 0.005, 0.045), rng, 0.0, 0.0, 0.0, 0.0015, 1)
    block(part, "iron", v(corner.x, face, corner.z - 0.13), (0.045, 0.005, 0.3), rng, 0.0, 0.0, 0.0, 0.0015, 1)
    for offset in (v(reach * 0.22, 0.0, 0.0), v(0.0, 0.0, -0.22), v(0.0, 0.0, 0.0)):
        nail(part, v(corner.x, face + side * 0.0025, corner.z) + offset, v(0.0, side, 0.0), rng, 0.007)


def wood_wall(kind):
    rng = random.Random(2000 + pieces.index(kind))
    part = k.assembly("wood_" + kind)
    hole = openings[kind]
    for x in (-1.43, 1.43):
        block(part, "beam_z_y", v(x, 0.0, 1.5), (0.14, 0.29, 3.0), rng, 0.0, 0.0, 0.0, 0.012, 2)
    block(part, "beam_x_y", v(0.0, 0.0, 2.925), (2.72, 0.29, 0.15), rng, 0.0, 0.0, 0.0, 0.01, 2)
    regions = [(-1.36, 1.36, 0.15, 2.85)]
    battens = [(0.62, [(-1.36, 1.36)]), (2.52, [(-1.36, 1.36)])]
    braces = [((-1.3, 0.68), (1.3, 2.46))]
    if hole is None or hole[2] > 0.2:
        block(part, "beam_x_y", v(0.0, 0.0, 0.075), (2.72, 0.29, 0.15), rng, 0.0, 0.0, 0.0, 0.01, 2)
    else:
        for x in (-1.025, 1.025):
            block(part, "beam_x_y", v(x, 0.0, 0.075), (0.67, 0.29, 0.15), rng, 0.0, 0.0, 0.0, 0.01, 2)
    if hole is not None:
        left, right, bottom, top = hole
        base = 0.0 if bottom < 0.2 else 0.15
        for x in (left - 0.07, right + 0.07):
            block(part, "beam_z_y", v(x, 0.0, (base + 2.85) * 0.5), (0.14, 0.29, 2.85 - base), rng, 0.0, 0.0, 0.0, 0.012, 2)
        block(part, "beam_x_y", v(0.0, 0.0, top + 0.075), (right - left, 0.29, 0.15), rng, 0.0, 0.0, 0.0, 0.01, 2)
        regions = [(-1.36, left - 0.14, 0.15, 2.85), (right + 0.14, 1.36, 0.15, 2.85), (left, right, top + 0.15, 2.85)]
        braces = [((-1.32, 0.68), (left - 0.2, 2.46)), ((right + 0.2, 2.46), (1.32, 0.68))]
        if bottom > 0.2:
            block(part, "beam_x_y", v(0.0, 0.0, bottom - 0.065), (right - left, 0.29, 0.13), rng, 0.0, 0.0, 0.0, 0.01, 2)
            regions.append((left, right, 0.15, bottom - 0.13))
            for side in (-1.0, 1.0):
                block(part, "beam_x_y", v(0.0, side * 0.148, bottom - 0.0125), (right - left + 0.2, 0.06, 0.025), rng, 0.0, 0.0, 0.0, 0.004, 1)
        else:
            battens[0] = (0.62, [(-1.36, left - 0.14), (right + 0.14, 1.36)])
    for side in (-1.0, 1.0):
        placed = []
        for region in regions:
            placed += wood_boards(part, region, side, rng)
        for z, spans in battens:
            for a, b in spans:
                plank(part, "beam_x_y", v(a, side * 0.127, z), v(b, side * 0.127, z), 0.11, 0.028, v(0.0, side, 0.0), rng, 0.003, 0.004)
                for x, width in placed:
                    if a + 0.03 < x < b - 0.03:
                        nail(part, v(x + rng.uniform(-0.25, 0.25) * width, side * 0.141, z + rng.uniform(-0.03, 0.03)), v(0.0, side, 0.0), rng)
        for start, end in braces:
            a = v(start[0] * side, side * 0.127, start[1])
            b = v(end[0] * side, side * 0.127, end[1])
            plank(part, "beam_" + nearest(b - a) + "_y", a, b, 0.1, 0.028, v(0.0, side, 0.0), rng, 0.003, 0.004)
            for index in range(3):
                spot = a.lerp(b, 0.25 + index * 0.25)
                nail(part, v(spot.x, side * 0.141, spot.z), v(0.0, side, 0.0), rng)
        for corner in (v(-1.43, 0.0, 2.925), v(1.43, 0.0, 2.925)):
            strap(part, corner, side, rng)
    return finish(part)


def wood_deck(part, rng, z_top, thickness, nails_at):
    for a, b in split(-1.5, 1.5, rng, 0.18, 0.24):
        gap = rng.uniform(0.005, 0.01)
        y = (a + b) * 0.5
        z = z_top - thickness * 0.5 + rng.uniform(-0.002, 0.0)
        plank(part, "plank_x_z", v(-1.5 + rng.uniform(0.0, 0.015), y, z), v(1.5 - rng.uniform(0.0, 0.015), y, z), b - a - gap, thickness, v(0.0, 0.0, 1.0), rng, 0.003, 0.004)
        for x in nails_at:
            nail(part, v(x + rng.uniform(-0.02, 0.02), y + rng.uniform(-0.3, 0.3) * (b - a), z_top), v(0.0, 0.0, 1.0), rng)


def wood_foundation():
    rng = random.Random(2100)
    part = k.assembly("wood_foundation")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            block(part, "beam_z_y", v(sx * 1.37, sy * 1.37, -0.8), (0.26, 0.26, 1.6), rng, 0.0, 0.0, 0.0, 0.015, 2)
    for sign in (-1.0, 1.0):
        block(part, "beam_x_y", v(0.0, sign * 1.43, -0.1725), (2.48, 0.14, 0.255), rng, 0.0, 0.0, 0.0, 0.01, 2)
        block(part, "beam_y_x", v(sign * 1.43, 0.0, -0.1725), (0.14, 2.48, 0.255), rng, 0.0, 0.0, 0.0, 0.01, 2)
    for x in (-0.62, 0.0, 0.62):
        block(part, "beam_y_z", v(x, 0.0, -0.145), (0.07, 2.72, 0.2), rng, 0.0, 0.0, 0.0, 0.004, 1)
    wood_deck(part, rng, 0.0, 0.045, (-1.43, 0.0, 1.43))
    for index, (normal, along) in enumerate(((v(0.0, -1.0, 0.0), v(1.0, 0.0, 0.0)), (v(1.0, 0.0, 0.0), v(0.0, 1.0, 0.0)), (v(0.0, 1.0, 0.0), v(-1.0, 0.0, 0.0)), (v(-1.0, 0.0, 0.0), v(0.0, -1.0, 0.0)))):
        flat = "x" if abs(along.x) > 0.5 else "y"
        face = "y" if flat == "x" else "x"
        for row, (a, b) in enumerate(split(-1.6, -0.3, rng, 0.19, 0.25)):
            gap = rng.uniform(0.005, 0.01)
            thickness = rng.uniform(0.028, 0.034)
            center = normal * (1.47 - thickness * 0.5) + v(0.0, 0.0, (a + b) * 0.5)
            plank(part, "plank_" + flat + "_" + face, center - along * 1.25, center + along * 1.25, b - a - gap, thickness, normal, rng, 0.004, 0.004)
            end = 1.0 if row % 2 else -1.0
            nail(part, center + along * (end * 1.19) + normal * (thickness * 0.5), normal, rng)
        start = normal * 1.4825 - along * 1.2 + v(0.0, 0.0, -1.52)
        finish_at = normal * 1.4825 + along * 1.2 + v(0.0, 0.0, -0.38)
        plank(part, "beam_" + nearest(finish_at - start) + "_" + face, start, finish_at, 0.12, 0.025, normal, rng, 0.004, 0.004)
        for index_nail in range(4):
            nail(part, start.lerp(finish_at, 0.15 + index_nail * 0.233) + normal * 0.0125, normal, rng)
    return finish(part)


def wood_floor():
    rng = random.Random(2400)
    part = k.assembly("wood_floor")
    wood_deck(part, rng, 0.0, 0.045, (-1.46, 0.0, 1.46))
    for sign in (-1.0, 1.0):
        block(part, "beam_x_y", v(0.0, sign * 1.46, -0.125), (3.0, 0.08, 0.16), rng, 0.0, 0.0, 0.0, 0.008, 1)
        block(part, "beam_y_x", v(sign * 1.46, 0.0, -0.125), (0.08, 2.84, 0.16), rng, 0.0, 0.0, 0.0, 0.008, 1)
    for x in (-0.73, 0.0, 0.73):
        block(part, "beam_y_z", v(x, 0.0, -0.155), (0.07, 2.84, 0.22), rng, 0.0, 0.0, 0.0, 0.006, 1)
    for x in (-1.095, -0.365, 0.365, 1.095):
        block(part, "beam_x_y", v(x, rng.uniform(-0.05, 0.05), -0.13), (0.66, 0.05, 0.16), rng, 0.0, 0.0, 0.0, 0.004, 1)
    return finish(part)


def wood_stairs():
    rng = random.Random(2500)
    part = k.assembly("wood_stairs")
    for sign in (-1.0, 1.0):
        slab(part, "beam_yz_x", [(-1.5, 0.0), (-1.5, 0.3), (1.25, 3.05), (1.5, 3.05), (1.5, 2.876), (-1.376, 0.0)], "x", sign * 1.1825, 0.035, rng, 0.006, 1)
        for a, b in split(-1.376, 1.5, rng, 0.2, 0.26):
            gap = rng.uniform(0.004, 0.009)
            y0 = a + gap * 0.5
            y1 = b - gap * 0.5
            slab(part, "plank_z_x", [(y0, 0.0), (y1, 0.0), (y1, y1 + 1.396), (y0, max(y0 + 1.396, 0.02))], "x", sign * 1.155, 0.03, rng, 0.004, 1)
    for step in range(12):
        top = 0.25 * (step + 1)
        y = -1.5 + 0.25 * step
        plank(part, "plank_x_z", v(-1.165, y + 0.1125, top - 0.0225), v(1.165, y + 0.1125 + rng.uniform(-0.004, 0.004), top - 0.0225), 0.275, 0.045, v(0.0, 0.0, 1.0), rng, 0.002, 0.005)
        plank(part, "plank_x_y", v(-1.14, y + 0.0125, 0.25 * step + (top - 0.045 - 0.25 * step) * 0.5), v(1.14, y + 0.0125, 0.25 * step + (top - 0.045 - 0.25 * step) * 0.5), top - 0.045 - 0.25 * step, 0.025, v(0.0, -1.0, 0.0), rng, 0.002, 0.004)
        for x in (-1.08, 1.08):
            nail(part, v(x + rng.uniform(-0.02, 0.02), y + 0.12 + rng.uniform(-0.04, 0.04), top), v(0.0, 0.0, 1.0), rng)
    for a, b in split(-1.14, 1.14, rng, 0.19, 0.26):
        gap = rng.uniform(0.004, 0.009)
        x = (a + b) * 0.5
        plank(part, "plank_z_y", v(x, 1.485, 0.0), v(x, 1.485, 2.955 - rng.uniform(0.0, 0.01)), b - a - gap, 0.03, v(0.0, 1.0, 0.0), rng, 0.003, 0.004)
    return finish(part)


def wood_roof():
    rng = random.Random(2600)
    part = k.assembly("wood_roof")
    exposure = 0.32
    length = 0.7
    lean = 0.018 / exposure
    for side in (-1.0, 1.0):
        row = 0
        while 2.0 - row * exposure > 0.12:
            butt = 2.0 - row * exposure
            for a, b in split(-1.51, 1.51, rng, 0.19, 0.36):
                gap = rng.uniform(0.004, 0.012)
                x = (a + b) * 0.5
                tip = butt + rng.uniform(-0.012, 0.012)
                upper = max(tip - length, -0.03)
                span = tip - upper
                bottom = roof_point(side, tip, 0.03 + span * 0.5 * lean, x)
                crown = roof_point(side, upper, 0.03 - span * 0.5 * lean, x + rng.uniform(-0.01, 0.01))
                board(part, "plank_" + nearest(bottom - crown) + "_z", (bottom + crown) * 0.5, span, b - a - gap, rng.uniform(0.016, 0.02), (bottom - crown).normalized(), v(0.0, side * rise, 1.5).normalized(), rng, 0.003, 1)
            row += 1
        for a, b in split(-1.52, 1.52, rng, 1.2, 1.8):
            board(part, "plank_x_z", roof_point(side, 0.06, 0.065, (a + b) * 0.5), b - a - 0.004, 0.22, 0.028, v(1.0, 0.0, 0.0), v(0.0, side * rise, 1.5).normalized(), rng, 0.004, 1)
            for x in (a + 0.1, (a + b) * 0.5, b - 0.1):
                nail(part, roof_point(side, 0.08 + rng.uniform(-0.04, 0.04), 0.079, x), v(0.0, side * rise, 1.5).normalized(), rng)
    for sign in (-1.0, 1.0):
        for a, b in split(-1.5, 1.5, rng, 0.2, 0.28):
            gap = rng.uniform(0.004, 0.009)
            slab(part, "plank_z_x", gable_outline(a + gap * 0.5, b - gap * 0.5, 0.02), "x", sign * 1.485, 0.03, rng, 0.004, 1)
        for half in (-1.0, 1.0):
            outline = [(0.0, rise + 0.085), (half * 1.6, 0.005), (half * 1.331, 0.005), (0.0, rise - 0.13)]
            slab(part, "beam_" + nearest(v(0.0, half * 1.5, -rise)) + "_x", outline if half > 0.0 else list(reversed(outline)), "x", sign * 1.514, 0.028, rng, 0.004, 1)
            for fraction in (0.2, 0.5, 0.8):
                y = half * 1.45 * fraction
                nail(part, v(sign * 1.528, y, roof_top(y) + 0.0), v(sign, 0.0, 0.0), rng)
    for a, b in split(-1.5, 1.5, rng, 0.2, 0.28):
        gap = rng.uniform(0.004, 0.009)
        x = (a + b) * 0.5
        plank(part, "plank_y_z", v(x, -1.5, 0.014), v(x, 1.5, 0.014), b - a - gap, 0.028, v(0.0, 0.0, -1.0), rng, 0.003, 0.004)
    for y in (-0.75, 0.75):
        plank(part, "beam_x_z", v(-1.36, y, -0.015), v(1.36, y, -0.015), 0.1, 0.03, v(0.0, 0.0, -1.0), rng, 0.003, 0.004)
    return finish(part)


def courses(breaks, rng, low=0.27, high=0.38):
    result = []
    for z0, z1 in zip(breaks[:-1], breaks[1:]):
        result += split(z0, z1, rng, low, high)
    return result


def carve(intervals, gap):
    result = []
    for a, b in intervals:
        if gap[1] <= a or gap[0] >= b:
            result.append((a, b))
            continue
        if gap[0] > a:
            result.append((a, gap[0]))
        if gap[1] < b:
            result.append((gap[1], b))
    return result


def stone_row(part, a, b, c0, c1, index, rng, joint=0.022, depth=0.125, face_depth=0.115):
    j = joint * 0.5
    first = 0.42 if index % 2 == 0 else 0.28
    last = 0.28 if index % 2 == 0 else 0.42
    if b - a < first + last + 0.3:
        for x0, x1 in split(a, b, rng, 0.3, 0.55):
            stone(part, "stone", v(x0 + j, -depth - rng.uniform(0.0, 0.006), c0 + j), v(x1 - j, depth + rng.uniform(0.0, 0.006), c1 - j), rng, 0.022, 0.011, None, 2)
        return
    for x0, x1 in ((a, a + first), (b - last, b)):
        stone(part, "stone", v(x0 + j, -depth - rng.uniform(0.0, 0.006), c0 + j), v(x1 - j, depth + rng.uniform(0.0, 0.006), c1 - j), rng, 0.022, 0.011, None, 2)
    for side in (-1.0, 1.0):
        for x0, x1 in split(a + first, b - last, rng, 0.36, 0.8):
            outer = side * (face_depth + rng.uniform(-0.008, 0.004))
            inner = side * 0.07
            stone(part, "stone", v(x0 + j, min(inner, outer), c0 + j), v(x1 - j, max(inner, outer), c1 - j), rng, 0.022, 0.011, None, 2)


def stone_wall(kind):
    rng = random.Random(3000 + pieces.index(kind))
    part = k.assembly("stone_" + kind)
    hole = openings[kind]
    breaks = [0.0, 3.0]
    obstacles = []
    cores = [(-1.485, 1.485, 0.015, 2.985)]
    if hole is not None:
        left, right, bottom, top = hole
        obstacles.append((left, right, bottom, top))
        lintel = (left - 0.3, right + 0.3, top, top + 0.3)
        obstacles.append(lintel)
        breaks += [top, top + 0.3]
        stone(part, "stone", v(lintel[0] + 0.011, -0.132, top + 0.004), v(lintel[1] - 0.011, 0.132, lintel[3] - 0.011), rng, 0.02, 0.006)
        cores = [(-1.485, left - 0.025, 0.015, 2.985), (right + 0.025, 1.485, 0.015, 2.985), (left - 0.03, right + 0.03, top + 0.02, 2.985)]
        if bottom > 0.2:
            sill = (left - 0.22, right + 0.22, bottom - 0.14, bottom)
            obstacles.append(sill)
            breaks += [sill[2], bottom]
            stone(part, "stone", v(sill[0] + 0.011, -0.155, sill[2] + 0.011), v(sill[1] - 0.011, 0.155, bottom), rng, 0.016, 0.004)
            cores.append((left - 0.03, right + 0.03, 0.015, sill[2] - 0.01))
            for x in (-0.3, 0.0, 0.3):
                put(part, k.revolve([(0.0, bottom - 0.03), (0.013, bottom - 0.03), (0.013, top + 0.03), (0.0, top + 0.03)], 8), "iron", rng, k.axis_frame(v(x, 0.0, 0.0), v(0.0, 0.0, 1.0)))
            block(part, "iron", v(0.0, 0.0, (bottom + top) * 0.5), (right - left + 0.06, 0.045, 0.009), rng, 0.0, 0.0, 0.0, 0.002, 1)
    for x0, x1, z0, z1 in cores:
        block(part, "mortar", v((x0 + x1) * 0.5, 0.0, (z0 + z1) * 0.5), (x1 - x0, 0.176, z1 - z0), rng, 0.0, 0.0, 0.0, 0.0, 1)
    for index, (c0, c1) in enumerate(courses(sorted(set(breaks)), rng, 0.29, 0.4)):
        intervals = [(-1.5, 1.5)]
        for x0, x1, z0, z1 in obstacles:
            if z0 <= c0 + 1e-4 and z1 >= c1 - 1e-4:
                intervals = carve(intervals, (x0, x1))
        for a, b in intervals:
            stone_row(part, a, b, c0, c1, index, rng)
    return finish(part)


def stone_foundation():
    rng = random.Random(3100)
    part = k.assembly("stone_foundation")
    block(part, "mortar", v(0.0, 0.0, -0.84), (2.92, 2.92, 1.52), rng, 0.0, 0.0, 0.0, 0.0, 1)
    j = 0.011
    for index, (c0, c1) in enumerate(split(-1.6, -0.1, rng, 0.33, 0.46)):
        for axis in ("x", "y"):
            full = (index % 2 == 0) == (axis == "x")
            reach = 1.5 if full else 1.28
            for sign in (-1.0, 1.0):
                for a, b in split(-reach, reach, rng, 0.45, 0.9):
                    depth = rng.uniform(0.18, 0.22)
                    outer = sign * (1.5 - rng.uniform(0.0, 0.008))
                    inner = sign * (1.5 - depth)
                    if axis == "x":
                        stone(part, "stone", v(a + j, min(inner, outer), c0 + j), v(b - j, max(inner, outer), c1 - j), rng, 0.026, 0.014)
                    else:
                        stone(part, "stone", v(min(inner, outer), a + j, c0 + j), v(max(inner, outer), b - j, c1 - j), rng, 0.026, 0.014)
    for x0, x1 in split(-1.5, 1.5, rng, 0.62, 0.95):
        for y0, y1 in split(-1.5, 1.5, rng, 0.55, 0.9):
            stone(part, "paver", v(x0 + 0.008, y0 + 0.008, -0.1), v(x1 - 0.008, y1 - 0.008, -0.002), rng, 0.014, 0.003)
    return finish(part)


def stone_floor():
    rng = random.Random(3400)
    part = k.assembly("stone_floor")
    block(part, "mortar", v(0.0, 0.0, -0.095), (2.76, 2.76, 0.1), rng, 0.0, 0.0, 0.0, 0.0, 1)
    for x0, x1 in split(-1.5, 1.5, rng, 0.5, 0.8):
        for y0, y1 in split(-1.5, 1.5, rng, 0.45, 0.75):
            stone(part, "paver", v(x0 + 0.007, y0 + 0.007, -0.045), v(x1 - 0.007, y1 - 0.007, -0.002), rng, 0.012, 0.002)
    for sign in (-1.0, 1.0):
        inner = sign * 1.38
        outer = sign * 1.5
        start, end = (-1.5, 1.38) if sign > 0.0 else (-1.38, 1.5)
        for a, b in split(start, end, rng, 0.7, 1.1):
            stone(part, "stone", v(a + 0.008, min(inner, outer), -0.15), v(b - 0.008, max(inner, outer), -0.047), rng, 0.012, 0.003)
        start, end = (-1.38, 1.5) if sign > 0.0 else (-1.5, 1.38)
        for a, b in split(start, end, rng, 0.7, 1.1):
            stone(part, "stone", v(min(inner, outer), a + 0.008, -0.15), v(max(inner, outer), b - 0.008, -0.047), rng, 0.012, 0.003)
        for a, b in split(-1.38, 1.38, rng, 0.8, 1.3):
            stone(part, "stone", v(a + 0.01, sign * 0.75 - 0.13, -0.3), v(b - 0.01, sign * 0.75 + 0.13, -0.145), rng, 0.016, 0.004)
    return finish(part)


def stone_stairs():
    rng = random.Random(3500)
    part = k.assembly("stone_stairs")
    j = 0.009
    for step in range(12):
        z0 = 0.25 * step
        z1 = z0 + 0.25
        front = -1.5 + 0.25 * step
        block(part, "mortar", v(0.0, (front + 0.03 + 1.47) * 0.5, (z0 + z1 - 0.02) * 0.5), (2.34, 1.47 - front - 0.03, 0.23), rng, 0.0, 0.0, 0.0, 0.0, 1)
        for y0, y1 in split(front, 1.5, rng, 0.55, 0.95):
            for x0, x1 in split(-1.2, 1.2, rng, 0.7, 1.3):
                stone(part, "stone", v(x0 + j, y0 + j, z0 + j), v(x1 - j, y1 - j, z1 - (0.0 if y0 == front else j)), rng, 0.02, 0.007)
    return finish(part)


def stone_roof():
    rng = random.Random(3600)
    part = k.assembly("stone_roof")
    exposure = 0.3
    length = 0.64
    lean = 0.026 / exposure
    for side in (-1.0, 1.0):
        normal = v(0.0, side * rise, 1.5).normalized()
        row = 0
        while 2.0 - row * exposure > 0.1:
            butt = 2.0 - row * exposure
            for a, b in split(-1.51, 1.51, rng, 0.3, 0.46):
                x = (a + b) * 0.5
                tip = butt + rng.uniform(-0.015, 0.015)
                upper = max(tip - length, -0.03)
                span = tip - upper
                bottom = roof_point(side, tip, 0.028 + span * 0.5 * lean, x)
                crown = roof_point(side, upper, 0.028 - span * 0.5 * lean, x + rng.uniform(-0.01, 0.01))
                put(part, k.box(span, b - a - rng.uniform(0.006, 0.014), rng.uniform(0.022, 0.028)), "slate", rng, k.place((bottom + crown) * 0.5, (bottom - crown).normalized(), normal) @ Matrix.Rotation(rng.uniform(-0.02, 0.02), 4, 'Z'), 0.006, 1)
            row += 1
    for a, b in split(-1.53, 1.53, rng, 0.38, 0.55):
        stone(part, "stone", v(a + 0.006, -0.1, rise - 0.04), v(b - 0.006, 0.1, rise + 0.1), rng, 0.02, 0.008)
    for sign in (-1.0, 1.0):
        x = sign * 1.45
        for index, (c0, c1) in enumerate(split(0.0, rise - 0.02, rng, 0.2, 0.28)):
            w0 = (rise - c0) * 1.5 / rise
            w1 = max((rise - c1) * 1.5 / rise, 0.0)
            if w1 < 0.12:
                slab(part, "stone", [(-w0 + 0.01, c0 + 0.01), (w0 - 0.01, c0 + 0.01), (0.0, c1 + 0.03)], "x", x, 0.12, rng, 0.012, 1)
                continue
            pieces_across = split(-w1, w1, rng, 0.32, 0.6)
            edges = [pieces_across[0][0]] + [pair[1] for pair in pieces_across]
            for piece in range(len(edges) - 1):
                y0 = edges[piece] + 0.01
                y1 = edges[piece + 1] - 0.01
                bottom_left = -w0 + 0.01 if piece == 0 else y0
                bottom_right = w0 - 0.01 if piece == len(edges) - 2 else y1
                slab(part, "stone", [(bottom_left, c0 + 0.01), (bottom_right, c0 + 0.01), (y1, c1 - 0.01), (y0, c1 - 0.01)], "x", x + sign * rng.uniform(-0.006, 0.004), 0.12, rng, 0.012, 1)
    block(part, "mortar", v(0.0, 0.0, 0.04), (2.86, 2.96, 0.07), rng, 0.0, 0.0, 0.0, 0.0, 1)
    for x0, x1 in split(-1.5, 1.5, rng, 0.6, 0.9):
        for y0, y1 in split(-1.5, 1.5, rng, 0.6, 0.9):
            stone(part, "paver", v(x0 + 0.007, y0 + 0.007, 0.0), v(x1 - 0.007, y1 - 0.007, 0.05), rng, 0.012, 0.003)
    return finish(part)


wall_face = 0.1
sheet_plane = 0.07


def frame_shade(rng):
    return rng.uniform(0.05, 0.45) if rng.random() < 0.7 else rng.uniform(0.8, 0.95)


def wall_panel(x0, x1, z0, z1, side):
    return {"origin": v(x1 if side > 0.0 else x0, side * sheet_plane, z0), "across": v(-side, 0.0, 0.0), "up": v(0.0, 0.0, 1.0), "normal": v(0.0, side, 0.0), "width": x1 - x0, "height": z1 - z0}


def butt(part, x, z0, z1, rng):
    for side in (-1.0, 1.0):
        bead(part, v(x, side * wall_face, z0), v(x, side * wall_face, z1), v(0.0, side, 0.0), rng)


def ledge(part, x0, x1, z, rng):
    for side in (-1.0, 1.0):
        bead(part, v(x0, side * wall_face, z), v(x1, side * wall_face, z), v(0.0, side, 0.0), rng)


def dress(part, faces, rng, plate_chance=0.6, patches=(1, 2)):
    for side, entries in faces.items():
        taken = []
        roomy = [entry for entry in entries if entry[0]["width"] > 0.75 and entry[0]["height"] > 0.65]
        if roomy and rng.random() < plate_chance:
            panel, made = rng.choice(roomy)
            overlay(part, panel, made, rng, False, rng.choice(("bolt", "bolt", "weld")), taken)
        for index in range(rng.randint(*patches)):
            panel, made = rng.choice(entries)
            overlay(part, panel, made, rng, True, rng.choice(("rivet", "weld")), taken)


def metal_wall(kind):
    rng = random.Random(4000 + pieces.index(kind))
    part = k.assembly("metal_" + kind)
    part.stains = {}
    part.cull_limit = 20.0
    part.stain_keys = ("py", "ny")
    hole = openings[kind]
    shade = frame_shade(rng)
    depth = wall_face * 2.0
    facing = v(0.0, 1.0, 0.0)
    for x in (-1.46, 1.46):
        tube(part, v(x, 0.0, 0.0), v(x, 0.0, 3.0), 0.08, depth, facing, rng, shade)
    rails = [(2.96, -1.42, 1.42)]
    left, right, bottom, top = hole if hole is not None else (0.0, 0.0, 0.0, 0.0)
    door = hole is not None and bottom < 0.2
    if hole is None:
        rails += [(0.04, -1.42, 1.42), (1.5, -1.42, 1.42)]
        panels = [(-1.42, 1.42, 0.08, 1.46), (-1.42, 1.42, 1.54, 2.92)]
    else:
        jamb_low = 0.0 if door else 0.08
        for x in (left - 0.04, right + 0.04):
            tube(part, v(x, 0.0, jamb_low), v(x, 0.0, 2.92), 0.08, depth, facing, rng, shade)
            ledge(part, x - 0.04, x + 0.04, 2.92, rng)
            if not door:
                ledge(part, x - 0.04, x + 0.04, 0.08, rng)
        sides = [(-1.42, left - 0.08), (right + 0.08, 1.42)]
        rails += [(1.5, a, b) for a, b in sides] + [(top + 0.04, left, right)]
        rails += [(0.04, a, b) for a, b in sides] if door else [(0.04, -1.42, 1.42), (bottom - 0.04, left, right)]
        panels = [(a, b, z0, z1) for a, b in sides for z0, z1 in ((0.08, 1.46), (1.54, 2.92))] + [(left, right, top + 0.08, 2.92)]
        if not door:
            panels.append((left, right, 0.08, bottom - 0.08))
        for x, lean in ((left, 1.0), (right, -1.0)):
            bead(part, v(x, -wall_face, top), v(x, wall_face, top), v(lean, 0.0, -1.0), rng, 0.006, None, 0.0)
            if not door:
                bead(part, v(x, -wall_face, bottom), v(x, wall_face, bottom), v(lean, 0.0, 1.0), rng, 0.006, None, 0.0)
    for z, x0, x1 in rails:
        tube(part, v(x0, 0.0, z), v(x1, 0.0, z), 0.08, depth, facing, rng, shade)
        for x in (x0, x1):
            butt(part, x, z - 0.04, z + 0.04, rng)
        if 0.2 < z < 2.9:
            for side in (-1.0, 1.0):
                seam(part, v(x0, side * wall_face, z + 0.04), v(x1, side * wall_face, z + 0.04), v(0.0, side, 0.0), rng, 0.5, 0.06, 0.3)
    faces = {1.0: [], -1.0: []}
    for x0, x1, z0, z1 in panels:
        middle = (z0 + z1) * 0.5
        rows = [0.035, z1 - z0 - 0.035]
        if z1 - z0 > 0.9:
            tube(part, v(x0, 0.0, middle), v(x1, 0.0, middle), 0.05, sheet_plane * 2.0, facing, rng, shade)
            rows.append(middle - z0)
        for side in (-1.0, 1.0):
            panel = wall_panel(x0, x1, z0, z1, side)
            faces[side].append((panel, clad(part, panel, rng, rows)))
    dress(part, faces, rng)
    for side in (-1.0, 1.0):
        seam(part, v(-1.5, side * wall_face, 3.0), v(1.5, side * wall_face, 3.0), v(0.0, side, 0.0), rng, 0.45, 0.07, 0.35)
    if door:
        for zc in (0.32, 1.12, 1.92):
            barrel = k.revolve([(0.0, -0.075), (0.011, -0.075), (0.018, -0.066), (0.018, 0.066), (0.011, 0.075), (0.0, 0.075)], 10, rng.uniform(0.0, 1.0))
            put(part, barrel, "frame", rng, k.axis_frame(v(left - 0.008, 0.0, zc), v(0.0, 0.0, 1.0)), 0.0, 1, shade)
            put(part, k.revolve([(0.0, 0.07), (0.007, 0.07), (0.007, 0.083), (0.0, 0.083)], 8), "bolt", rng, k.axis_frame(v(left - 0.008, 0.0, zc), v(0.0, 0.0, 1.0)))
            for lean in (-1.0, 1.0):
                bead(part, v(left, lean * 0.0165, zc - 0.06), v(left, lean * 0.0165, zc + 0.06), v(1.0, lean, 0.0), rng, 0.0045, None, 0.0)
                block(part, "frame", v(left - 0.04, lean * (wall_face + 0.006), zc), (0.07, 0.012, 0.22), rng, 0.0, 0.0, 0.0, 0.0015, 1, shade)
                for offset in (-0.07, 0.07):
                    hex_bolt(part, v(left - 0.04, lean * (wall_face + 0.012), zc + offset), v(0.0, lean, 0.0), rng, 0.02, 0.0, 0.9)
                stitch(part, v(left - 0.075, lean * (wall_face + 0.006), zc - 0.11), v(left - 0.075, lean * (wall_face + 0.006), zc + 0.11), v(-1.0, lean, 0.0), rng, v(0.0, lean, 0.0), 0.06, 0.08)
        block(part, "frame", v(right, 0.0, 1.07), (0.012, 0.05, 0.12), rng, 0.0, 0.0, 0.0, 0.002, 1, shade)
        for side in (-1.0, 1.0):
            seam(part, v(left, side * wall_face, top + 0.08), v(right, side * wall_face, top + 0.08), v(0.0, side, 0.0), rng, 0.5, 0.05, 0.12)
    elif hole is not None:
        grille = rng.uniform(0.05, 0.45)
        for index in range(9):
            x = -0.44 + 0.11 * index
            tube(part, v(x, 0.0, bottom - 0.004), v(x, 0.0, top + 0.004), 0.016, 0.016, facing, rng, grille, 0.002)
            for side in (-1.0, 1.0):
                bead(part, v(x - 0.008, side * 0.008, bottom), v(x + 0.008, side * 0.008, bottom), v(0.0, side, 1.0), rng, 0.004, None, 0.0)
        for z in (bottom + 0.33, bottom + 0.67):
            tube(part, v(left, 0.0, z), v(right, 0.0, z), 0.04, 0.008, facing, rng, grille, 0.0015)
        for side in (-1.0, 1.0):
            seam(part, v(left, side * wall_face, bottom), v(right, side * wall_face, bottom), v(0.0, side, 0.0), rng, 0.8, 0.04, 0.45)
            seam(part, v(left, side * wall_face, top + 0.08), v(right, side * wall_face, top + 0.08), v(0.0, side, 0.0), rng, 0.5, 0.05, 0.12)
    return finish(part, 55.0)


sides_around = ((v(0.0, 1.0, 0.0), v(-1.0, 0.0, 0.0)), (v(1.0, 0.0, 0.0), v(0.0, 1.0, 0.0)), (v(0.0, -1.0, 0.0), v(1.0, 0.0, 0.0)), (v(-1.0, 0.0, 0.0), v(0.0, -1.0, 0.0)))


def deck(part, rng, bolt_rows, spacing=0.5):
    up = v(0.0, 0.0, 1.0)
    tint = rng.random()
    for x0, x1 in ((-1.5, -0.5), (-0.5, 0.5), (0.5, 1.5)):
        tint = (tint + rng.uniform(0.3, 0.7)) % 1.0
        block(part, "plate", v((x0 + x1) * 0.5, 0.0, -0.004), (x1 - x0 - 0.003, 3.0, 0.008), rng, 0.0, 0.0, 0.0, 0.0015, 1, tint)
        for x in (x0 + 0.035, x1 - 0.035):
            count = int(2.8 / spacing)
            for index in range(count + 1):
                rivet(part, v(x, -1.4 + 2.8 * index / count, 0.0), up, rng, 0.008, 0.8)
        for y in bolt_rows:
            count = max(1, int((x1 - x0 - 0.2) / 0.4))
            for index in range(count + 1):
                rivet(part, v(x0 + 0.1 + (x1 - x0 - 0.2) * index / count, y, 0.0), up, rng, 0.008, 0.8)
    for x in (-0.5, 0.5):
        streak(part, v(x, -1.5, 0.0), v(x, 1.5, 0.0), up, 0.006, 0.6, 1)


def metal_foundation():
    rng = random.Random(4100)
    part = k.assembly("metal_foundation")
    part.stains = {}
    part.cull_limit = 20.0
    part.stain_keys = ("py", "ny", "px", "nx", "pz")
    shade = frame_shade(rng)
    up = v(0.0, 0.0, 1.0)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            tube(part, v(sx * 1.44, sy * 1.44, -1.6), v(sx * 1.44, sy * 1.44, -0.008), 0.12, 0.12, v(0.0, 1.0, 0.0), rng, shade)
    for x in (-0.5, 0.5):
        tube(part, v(x, -1.38, -0.058), v(x, 1.38, -0.058), 0.08, 0.1, up, rng, shade)
    for normal, across in sides_around:
        start = normal * 1.44 - across * 1.38
        for z, tall in ((-0.078, 0.14), (-1.55, 0.1)):
            tube(part, start + up * z, start + across * 2.76 + up * z, tall, 0.12, normal, rng, shade)
            for end in (0.0, 2.76):
                bead(part, normal * 1.5 - across * 1.38 + across * end + up * (z - tall * 0.5), normal * 1.5 - across * 1.38 + across * end + up * (z + tall * 0.5), normal, rng)
        tube(part, normal * 1.44 + up * -1.5, normal * 1.44 + up * -0.148, 0.1, 0.12, normal, rng, shade)
        for z in (-1.5, -0.148):
            bead(part, normal * 1.5 - across * 0.05 + up * z, normal * 1.5 + across * 0.05 + up * z, normal, rng)
        tube(part, start + up * -0.824, start + across * 2.76 + up * -0.824, 0.05, 0.06, normal, rng, shade)
        faces = {1.0: []}
        for u0, u1 in ((0.0, 1.33), (1.43, 2.76)):
            panel = {"origin": normal * 1.47 - across * 1.38 + across * u0 + up * -1.5, "across": across, "up": up, "normal": normal, "width": u1 - u0, "height": 1.352}
            faces[1.0].append((panel, clad(part, panel, rng, [0.035, 1.317, 0.676], 0.8, False, 5, 0.2, 0.35)))
        dress(part, faces, rng, 0.3, (0, 1))
        seam(part, normal * 1.5 - across * 1.5 + up * -0.148, normal * 1.5 + across * 1.5 + up * -0.148, normal, rng, 0.6, 0.05, 0.35)
        seam(part, normal * 1.5 - across * 1.5 + up * -0.008, normal * 1.5 + across * 1.5 + up * -0.008, normal, rng, 0.4, 0.08, 0.12)
    deck(part, rng, (-1.44, 1.44))
    return finish(part, 55.0)


def channel_outline(sign, web, reach, top, bottom, flange=0.0085, thickness=0.008):
    inner = web - sign * thickness
    tip = web - sign * reach
    return [(web, bottom), (web, top), (tip, top), (tip, top - flange), (inner, top - flange), (inner, bottom + flange), (tip, bottom + flange), (tip, bottom)]


def beam_outline(center, top, bottom, half=0.041, flange=0.0074, web=0.0025):
    return [(center - half, bottom), (center + half, bottom), (center + half, bottom + flange), (center + web, bottom + flange), (center + web, top - flange), (center + half, top - flange), (center + half, top), (center - half, top), (center - half, top - flange), (center - web, top - flange), (center - web, bottom + flange), (center - half, bottom + flange)]


def metal_floor():
    rng = random.Random(4400)
    part = k.assembly("metal_floor")
    part.stains = {}
    part.cull_limit = 20.0
    part.stain_keys = ("py", "ny", "px", "nx", "pz")
    shade = frame_shade(rng)
    down = v(0.0, 0.0, -1.0)
    for sign in (-1.0, 1.0):
        put(part, k.extrude(channel_outline(sign, sign * 1.5, 0.075, -0.008, -0.158), 3.0, "x"), "frame", rng, None, 0.0012, 1, shade)
        put(part, k.extrude(channel_outline(sign, sign * 1.5, 0.075, -0.008, -0.158), 2.85, "y"), "frame", rng, None, 0.0012, 1, shade)
        for end in (-1.0, 1.0):
            bead(part, v(sign * 1.5, end * 1.425, -0.158), v(sign * 1.5, end * 1.425, -0.008), v(sign, 0.0, 0.0), rng)
        for normal in (v(0.0, sign, 0.0), v(sign, 0.0, 0.0)):
            across = normal.cross(v(0.0, 0.0, 1.0))
            seam(part, normal * 1.5 - across * 1.5 + v(0.0, 0.0, -0.008), normal * 1.5 + across * 1.5 + v(0.0, 0.0, -0.008), normal, rng, 0.55, 0.05, 0.14)
            for index in range(9):
                hex_bolt(part, normal * 1.5 + across * (-1.2 + 0.3 * index) + v(0.0, 0.0, -0.083), normal, rng, 0.019, 0.0, 0.8)
    for x in (-0.5, 0.5):
        put(part, k.extrude(beam_outline(x, -0.008, -0.168), 2.85, "y"), "frame", rng, None, 0.001, 1, shade)
        for end in (-1.0, 1.0):
            for lean in (-1.0, 1.0):
                bead(part, v(x + lean * 0.0025, end * 1.425, -0.15), v(x + lean * 0.0025, end * 1.425, -0.0165), v(lean, -end, 0.0), rng, 0.005, None, 0.0)
    for x0, x1 in ((-1.425, -0.541), (-0.459, 0.459), (0.541, 1.425)):
        outline = [(-0.003, -0.108), (-0.003, -0.008), (0.047, -0.008), (0.047, -0.0155), (0.003, -0.0155), (0.003, -0.1005), (0.047, -0.1005), (0.047, -0.108)]
        put(part, k.extrude(outline, x1 - x0, "x"), "frame", rng, Matrix.Translation(v((x0 + x1) * 0.5, 0.0, 0.0)), 0.001, 1, shade)
        for x, lean in ((x0, 1.0), (x1, -1.0)):
            bead(part, v(x, -0.003, -0.1), v(x, -0.003, -0.016), v(lean, -1.0, 0.0), rng, 0.0045, None, 0.0)
    deck(part, rng, (-1.46, 1.46, 0.022), 0.45)
    for y in (-1.46, 1.46):
        for x in (-1.46, 1.46):
            halo(part, v(x, y, 0.0), v(0.0, 0.0, 1.0), 0.12, 0.6, rng)
    return finish(part, 55.0)


def post(part, x, y0, y1, z0, z1, z2, rng, shade):
    put(part, k.extrude([(y0, z0), (y1, z0), (y1, z2), (y0, z1)], 0.07, "x"), "frame", rng, Matrix.Translation(v(x, 0.0, 0.0)), 0.0015, 1, shade)


def foot(part, center, size, rng, shade, anchors):
    block(part, "frame", center + v(0.0, 0.0, 0.006), (size[0], size[1], 0.012), rng, 0.0, 0.0, 0.0, 0.0015, 1, shade)
    for offset in anchors:
        hex_bolt(part, center + offset + v(0.0, 0.0, 0.012), v(0.0, 0.0, 1.0), rng, 0.022, 0.02, 0.8)


def metal_stairs():
    rng = random.Random(4500)
    part = k.assembly("metal_stairs")
    part.stains = {}
    part.cull_limit = 20.0
    part.stain_keys = ("px", "nx", "pz")
    shade = frame_shade(rng)
    pitch_line = v(0.0, 1.0, 1.0).normalized()
    square = v(0.0, -1.0, 1.0).normalized()
    up = v(0.0, 0.0, 1.0)
    for sign in (-1.0, 1.0):
        outward = v(sign, 0.0, 0.0)
        put(part, k.extrude([(-1.5, 0.0), (1.5, 3.0), (1.18, 3.0), (-1.5, 0.32)], 0.008, "x"), "frame", rng, Matrix.Translation(v(sign * 1.186, 0.0, 0.0)), 0.0012, 1, shade)
        put(part, k.extrude([(-1.5, 0.012), (-1.3, 0.012), (-1.3, 0.2)], 0.008, "x"), "frame", rng, Matrix.Translation(v(sign * 1.186, 0.0, 0.0)), 0.001, 1, shade)
        flange = sign * 1.155
        for (y0, z0), (y1, z1), offset in (((-1.5, 0.32), (1.18, 3.0), -0.0045), ((-1.5, 0.0), (1.5, 3.0), 0.0045)):
            start = v(flange, y0, z0) + pitch_line * 0.012 + square * offset
            end = v(flange, y1, z1) - pitch_line * 0.012 + square * offset
            put(part, k.sweep([start, end], k.rectangle(0.07, 0.009), up=square), "frame", rng, None, 0.0012, 1, shade)
        seam(part, v(sign * 1.19, -1.49, 0.33), v(sign * 1.19, 1.17, 2.99), outward, rng, 0.55, 0.06, 0.3)
        foot(part, v(sign * 1.13, -1.4, 0.0), (0.12, 0.2, 0.012), rng, shade, (v(-sign * 0.03, -0.06, 0.0), v(-sign * 0.03, 0.06, 0.0)))
        bead(part, v(sign * 1.182, -1.49, 0.012), v(sign * 1.182, -1.31, 0.012), v(-sign, 0.0, 1.0), rng, 0.005, None, 0.0)
        post(part, sign * 1.145, -0.035, 0.035, 0.012, 1.465, 1.535, rng, shade)
        post(part, sign * 1.145, 1.405, 1.475, 0.012, 2.905, 2.975, rng, shade)
        for y in (0.0, 1.44):
            foot(part, v(sign * 1.13, min(y, 1.43), 0.0), (0.13, 0.13, 0.012), rng, shade, (v(-sign * 0.045, -0.045, 0.0), v(-sign * 0.045, 0.045, 0.0)))
            for lean in (-1.0, 1.0):
                bead(part, v(sign * 1.11, y + lean * 0.035, 0.012), v(sign * 1.18, y + lean * 0.035, 0.012), v(0.0, lean, 1.0), rng, 0.005, None, 0.0)
        bead(part, v(sign * 1.182, -0.035, 1.465), v(sign * 1.182, 0.035, 1.535), v(-sign, 0.0, 0.0), rng, 0.005, None, 0.0)
    for y, z in ((0.0, 0.5), (1.44, 0.06), (1.44, 2.86)):
        tube(part, v(-1.11, y, z), v(1.11, y, z), 0.06, 0.06, v(0.0, 1.0, 0.0), rng, shade)
        for x, lean in ((-1.11, 1.0), (1.11, -1.0)):
            for face in (-1.0, 1.0):
                bead(part, v(x, y + face * 0.03, z - 0.03), v(x, y + face * 0.03, z + 0.03), v(lean, face, 0.0), rng, 0.0045, None, 0.0)
    for index, (a, b) in enumerate(((v(-1.1, 1.436, 0.12), v(1.1, 1.436, 2.8)), (v(1.1, 1.444, 0.12), v(-1.1, 1.444, 2.8)))):
        tube(part, a, b, 0.05, 0.008, v(0.0, 1.0, 0.0), rng, shade, 0.0015)
    hex_bolt(part, v(0.0, 1.448, 1.46), v(0.0, 1.0, 0.0), rng, 0.022, 0.02, 0.0)
    for step in range(12):
        top = 0.25 * (step + 1)
        y0 = -1.5 + 0.25 * step
        put(part, k.extrude([(y0, top), (y0 + 0.25, top), (y0 + 0.25, top - 0.006), (y0 + 0.006, top - 0.006), (y0 + 0.006, top - 0.04), (y0, top - 0.04)], 2.356, "x"), "plate", rng, None, 0.0012, 1, rng.random())
        for sign in (-1.0, 1.0):
            inner = sign * 1.182
            put(part, k.extrude([(inner, top - 0.006), (inner, top - 0.046), (inner - sign * 0.005, top - 0.046), (inner - sign * 0.005, top - 0.011), (inner - sign * 0.04, top - 0.011), (inner - sign * 0.04, top - 0.006)], 0.14, "y"), "frame", rng, Matrix.Translation(v(0.0, y0 + 0.09, 0.0)), 0.001, 1, shade)
            for y in (y0 + 0.05, y0 + 0.13):
                hex_bolt(part, v(sign * 1.19, y, top - 0.026), v(sign, 0.0, 0.0), rng, 0.019, 0.0, 0.9)
                rivet(part, v(sign * 1.16, y, top), up, rng, 0.008, 0.7)
    return finish(part, 55.0)


def metal_roof():
    rng = random.Random(4600)
    part = k.assembly("metal_roof")
    part.stains = {}
    part.cull_limit = 20.0
    part.stain_keys = ("pz", "px", "nx")
    shade = frame_shade(rng)
    eave = 1.98
    ridge = -0.035
    crest = 0.05 + 0.0012 + 0.018
    purlins = (0.12, 0.6, 1.08, 1.56, 1.8)
    for sign in (-1.0, 1.0):
        x = sign * 1.46
        outward = v(sign, 0.0, 0.0)
        for side in (-1.0, 1.0):
            tube(part, roof_point(side, 1.79, -0.05, x), roof_point(side, 0.0, -0.05, x), 0.06, 0.1, v(0.0, side * rise, 1.5).normalized(), rng, shade)
        tube(part, v(x, -1.47, 0.04), v(x, 1.47, 0.04), 0.06, 0.08, v(0.0, 0.0, 1.0), rng, shade)
        tube(part, v(x, 0.0, 0.08), v(x, 0.0, 1.12), 0.06, 0.06, v(1.0, 0.0, 0.0), rng, shade)
        face = x + sign * 0.03
        for z in (0.08, 1.12):
            bead(part, v(face, -0.03, z), v(face, 0.03, z), outward, rng, 0.005, outward)
        for lean in (-1.0, 1.0):
            bead(part, v(face, lean * 1.25, 0.08), v(face, lean * 1.37, 0.08), outward + v(0.0, 0.0, 0.6), rng, 0.005, outward)
            seam(part, roof_point(lean, 0.15, -0.1, face), roof_point(lean, 1.7, -0.1, face), outward, rng, 0.5, 0.06, 0.25)
        for y0, y1 in ((-1.17, -0.03), (0.03, 1.17)):
            origin_y = y0 if sign > 0.0 else y1
            panel = {"origin": v(sign * 1.462, origin_y, 0.08), "across": v(0.0, sign, 0.0), "up": v(0.0, 0.0, 1.0), "normal": outward, "width": y1 - y0, "height": roof_top(0.03) - 0.128 - 0.08}
            gable_top = (lambda u, origin_y=origin_y, sign=sign: roof_top(origin_y + sign * u) - 0.128 - 0.08)
            made = clad(part, panel, rng, [0.035], 0.85, False, 4, 0.0, 0.1, "scrap_z", 0.3, (0.3, 0.3, 0.2, 0.2), gable_top)
            if rng.random() < 0.6:
                overlay(part, panel, made, rng, True, rng.choice(("rivet", "weld")), [])
        seam(part, v(sign * 1.49, -1.47, 0.08), v(sign * 1.49, 1.47, 0.08), outward, rng, 0.4, 0.07, 0.08)
    faces = {}
    for side in (-1.0, 1.0):
        normal = v(0.0, side * rise, 1.5).normalized()
        uphill = v(0.0, -side * 1.5, rise).normalized()
        for t in purlins:
            tube(part, roof_point(side, t, 0.025, -1.49), roof_point(side, t, 0.025, 1.49), 0.04, 0.05, normal, rng, shade)
        panel = {"origin": roof_point(side, eave, 0.05, side * 1.53), "across": v(-side, 0.0, 0.0), "up": uphill, "normal": normal, "width": 3.06, "height": eave - ridge}
        made = clad(part, panel, rng, [eave - t for t in purlins[1:]], 1.0, True, 5, 0.18, 0.35, "scrap_" + nearest(uphill), 0.4, (0.2, 0.35, 0.15, 0.3))
        faces[side] = [(panel, made)]
        put(part, k.box(3.06, 0.22, 0.0012), "scrap_x", rng, k.place(roof_point(side, 0.075, crest + 0.0025), v(1.0, 0.0, 0.0), normal), 0.0, 1, rng.uniform(0.84, 0.98))
        for index in range(10):
            tek(part, roof_point(side, 0.12, crest + 0.0037, -1.35 + 0.3 * index), normal, rng)
        seam(part, roof_point(side, 0.185, crest + 0.004, -1.53), roof_point(side, 0.185, crest + 0.004, 1.53), normal, rng, 0.55, 0.05, 0.35)
        for sign in (-1.0, 1.0):
            reach = sign * side
            flashing = [(-reach * 0.0012, 0.0012), (reach * 0.07, 0.0012), (reach * 0.07, 0.0), (0.0, 0.0), (0.0, -0.07), (-reach * 0.0012, -0.07)]
            put(part, k.sweep([roof_point(side, ridge, crest + 0.0025, sign * 1.532), roof_point(side, eave, crest + 0.0025, sign * 1.532)], flashing, up=normal), "scrap_" + nearest(uphill), rng, None, 0.0, 1, rng.uniform(0.84, 0.98))
            for t in purlins:
                tek(part, roof_point(side, t, crest + 0.0037, sign * 1.495), normal, rng)
        put(part, k.box(2.86, 0.004, 0.066), "frame", rng, Matrix.Translation(v(0.0, side * 1.488, 0.035)), 0.0, 1, shade)
    dress(part, faces, rng)
    put(part, k.revolve([(0.0, -1.53), (0.02, -1.53), (0.02, 1.53), (0.0, 1.53)], 10), "scrap_x", rng, k.axis_frame(v(0.0, 0.0, rise + crest * 1.28 + 0.004), v(1.0, 0.0, 0.0)), 0.0, 1, rng.uniform(0.84, 0.98))
    for x0, x1 in ((-1.43, -0.477), (-0.477, 0.477), (0.477, 1.43)):
        block(part, "scrap_x", v((x0 + x1) * 0.5, 0.0, 0.002), (x1 - x0 - 0.003, 2.98, 0.004), rng, 0.0, 0.0, 0.0, 0.0012, 1, paint_tint(rng)[0])
    down = v(0.0, 0.0, -1.0)
    for y in (-0.75, 0.75):
        put(part, k.extrude([(y - 0.025, 0.0), (y + 0.025, 0.0), (y + 0.025, -0.005), (y - 0.02, -0.005), (y - 0.02, -0.05), (y - 0.025, -0.05)], 2.86, "x"), "frame", rng, None, 0.001, 1, shade)
        for index in range(7):
            hex_bolt(part, v(-1.2 + 0.4 * index, y + 0.012, -0.005), down, rng, 0.017, 0.0, 0.0)
    return finish(part, 55.0)


makers = {
    "twig_foundation": twig_foundation,
    "twig_wall": lambda: twig_wall("wall"),
    "twig_doorway": lambda: twig_wall("doorway"),
    "twig_window": lambda: twig_wall("window"),
    "twig_floor": twig_floor,
    "twig_stairs": twig_stairs,
    "twig_roof": twig_roof,
    "wood_foundation": wood_foundation,
    "wood_wall": lambda: wood_wall("wall"),
    "wood_doorway": lambda: wood_wall("doorway"),
    "wood_window": lambda: wood_wall("window"),
    "wood_floor": wood_floor,
    "wood_stairs": wood_stairs,
    "wood_roof": wood_roof,
    "stone_foundation": stone_foundation,
    "stone_wall": lambda: stone_wall("wall"),
    "stone_doorway": lambda: stone_wall("doorway"),
    "stone_window": lambda: stone_wall("window"),
    "stone_floor": stone_floor,
    "stone_stairs": stone_stairs,
    "stone_roof": stone_roof,
    "metal_foundation": metal_foundation,
    "metal_wall": lambda: metal_wall("wall"),
    "metal_doorway": lambda: metal_wall("doorway"),
    "metal_window": lambda: metal_wall("window"),
    "metal_floor": metal_floor,
    "metal_stairs": metal_stairs,
    "metal_roof": metal_roof,
}


def names_of(key):
    return [tier + "_" + piece for tier in (tiers if key == "structures" else (key,)) for piece in pieces]


def triangles(obj):
    return sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons)


def surface_area(obj):
    return sum(polygon.area for polygon in obj.data.polygons)


def build(key):
    objects = []
    stain_images.clear()
    for name in names_of(key):
        if name in makers and (mode == "export" or not only or name in only):
            objects.append(makers[name]())
            print("PART", name, triangles(objects[-1]), "tris", len(objects[-1].data.materials), "looks", round(surface_area(objects[-1]), 2), "m2", flush=True)
    return objects


def ground(height):
    data = bpy.data.meshes.new("ground")
    data.from_pydata([(-40.0, -40.0, height), (40.0, -40.0, height), (40.0, 40.0, height), (-40.0, 40.0, height)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new("ground", data)
    material = bpy.data.materials.new("ground")
    material.use_nodes = True
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    place = tree.nodes.new('ShaderNodeTexCoord').outputs['Object']
    color = k.mix_color(tree, k.noise(tree, place, 0.35, 6.0, 0.6), (0.035, 0.03, 0.02, 1.0), (0.07, 0.06, 0.04, 1.0))
    color = k.mix_color(tree, k.math_node(tree, 'MULTIPLY', k.ramp(tree, k.noise(tree, place, 0.12, 4.0, 0.5), 0.45, 0.6), 0.7), color, (0.045, 0.055, 0.03, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = 0.95
    data.materials.append(material)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def compose(parts, tier, origin, created):
    layout = [("foundation", v(0.0, 0.0, 0.0), 0.0), ("foundation", v(3.0, 0.0, 0.0), 0.0), ("foundation", v(3.0, -3.0, 0.0), 0.0), ("window", v(0.0, -1.5, 0.0), 0.0), ("wall", v(0.0, 1.5, 0.0), 0.0), ("wall", v(-1.5, 0.0, 0.0), math.pi * 0.5), ("doorway", v(1.5, 0.0, 0.0), math.pi * 0.5), ("wall", v(3.0, 1.5, 0.0), 0.0), ("wall", v(4.5, 0.0, 0.0), math.pi * 0.5), ("roof", v(0.0, 0.0, 3.0), 0.0), ("floor", v(3.0, 0.0, 3.0), 0.0), ("stairs", v(3.0, -3.0, 0.0), 0.0)]
    for piece, position, yaw in layout:
        name = tier + "_" + piece
        if name in parts:
            copy = parts[name].copy()
            bpy.context.scene.collection.objects.link(copy)
            copy.matrix_world = Matrix.Translation(origin + position) @ Matrix.Rotation(yaw, 4, 'Z')
            copy.hide_render = False
            created.append(copy)
    return created


def overview(objects, label, groups, view_list):
    parts = {obj.name: obj for obj in objects}
    for obj in objects:
        obj.hide_render = True
    created = []
    for index, tier in enumerate(groups):
        compose(parts, tier, v(index * 9.0, 0.0, 0.0), created)
    if created:
        low, high = turntable.bounds(created)
        floor = ground(-0.45 - low.z)
        turntable.render_views(created, preview_root, label, view_list, samples, hdri)
        bpy.data.objects.remove(floor)
    for copy in created:
        bpy.data.objects.remove(copy)
    for obj in objects:
        obj.hide_render = False


def look_up(obj, label):
    scene = bpy.context.scene
    low, high = turntable.bounds([obj])
    size = high - low
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    turntable.accelerate(scene)
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    floor, created = turntable.studio(scene, hdri, max(max(size.x, size.y, size.z) / 0.7, 1.0))
    created.remove(floor)
    bpy.data.objects.remove(floor)
    target = (low + high) * 0.5
    data = bpy.data.cameras.new("view")
    data.lens = 28.0
    camera = bpy.data.objects.new("view", data)
    scene.collection.objects.link(camera)
    camera.location = target + Vector((0.45, -0.85, -0.5)).normalized() * max(size.x, size.y, size.z) * 1.05
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = camera
    scene.render.filepath = os.path.join(preview_root, label + "_below.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)
    for light in created:
        bpy.data.objects.remove(light)
    print("RENDERED", label, "below", flush=True)


def isolate(objects, chosen):
    for obj in objects:
        obj.location = v(0.0, 0.0, 0.0) if obj == chosen else v(0.0, 0.0, -1000.0)
    bpy.context.view_layer.update()


def bake_world():
    world = bpy.data.worlds.new("bake")
    world.light_settings.distance = 0.6
    bpy.context.scene.world = world


def uv_coverage(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    layer = bm.loops.layers.uv.active
    total = 0.0
    for face in bm.faces:
        points = [loop[layer].uv for loop in face.loops]
        for index in range(1, len(points) - 1):
            a = points[index] - points[0]
            b = points[index + 1] - points[0]
            total += abs(a.x * b.y - a.y * b.x) * 0.5
    bm.free()
    return total


def unwrap(obj, margin):
    if obj.data.attributes.get("mapped") is None:
        k.unwrap(obj, margin)
        return
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.view_layer.objects:
        other.select_set(other == obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mapped = bm.faces.layers.int.get("mapped")
    loose = 0
    for face in bm.faces:
        face.select_set(face[mapped] == 0)
        loose += face[mapped] == 0
    bm.select_mode = {'FACE'}
    bm.select_flush_mode()
    bm.to_mesh(obj.data)
    bm.free()
    if loose:
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(52.0), island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    layer = bm.loops.layers.uv.active
    for face in bm.faces:
        face.select_set(True)
        for loop in face.loops:
            loop[layer].select = True
            loop[layer].select_edge = True
    bm.to_mesh(obj.data)
    bm.free()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    print("UNWRAPPED", obj.name, loose, "loose faces of", len(obj.data.polygons), flush=True)


def bake_piece(obj, directory):
    unwrap(obj, 0.005)
    weight_islands(obj)
    coverage = uv_coverage(obj)
    images = k.bake(obj, directory, texture_size, bake_samples)
    obj.data.materials.clear()
    obj.data.materials.append(k.baked_material(obj.name + "_baked", images))
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    return coverage


def caption(scene, camera, text, lens, aspect):
    data = bpy.data.curves.new("caption", 'FONT')
    data.body = text
    data.size = 0.03
    material = bpy.data.materials.new("caption")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    shader.inputs['Emission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    shader.inputs['Emission Strength'].default_value = 3.0
    data.materials.append(material)
    obj = bpy.data.objects.new("caption", data)
    for flag in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(obj, flag, False)
    scene.collection.objects.link(obj)
    obj.parent = camera
    half = 18.0 / lens
    obj.location = (-half * 0.95, -half * aspect * 0.9, -1.0)
    return obj


def tiers_sheet(gltf, target, tile=(480, 360), gap=4):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=gltf)
    parts = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == 'MESH'}
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    turntable.accelerate(scene)
    scene.render.resolution_x, scene.render.resolution_y = tile
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    floor, created = turntable.studio(scene, hdri, 4.6)
    folder = os.path.join(bpy.app.tempdir, "tiers_sheet_tiles")
    os.makedirs(folder, exist_ok=True)
    width = len(pieces) * (tile[0] + gap) + gap
    height = len(tiers) * (tile[1] + gap) + gap
    sheet = numpy.full((height, width, 4), 0.08, dtype=numpy.float32)
    sheet[:, :, 3] = 1.0
    lens = 40.0
    direction = Vector((0.75, -0.8, 0.45)).normalized()
    for column, piece in enumerate(pieces):
        present = [parts[tier + "_" + piece] for tier in tiers if tier + "_" + piece in parts]
        low, high = turntable.bounds(present)
        size = high - low
        focus = (low + high) * 0.5
        data = bpy.data.cameras.new("tile")
        data.lens = lens
        data.clip_start = 0.01
        camera = bpy.data.objects.new("tile", data)
        scene.collection.objects.link(camera)
        camera.location = focus + direction * max(size.x, size.y, size.z) * 1.15 * 1.35 * 1.35
        camera.rotation_euler = (focus - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.camera = camera
        for row, tier in enumerate(tiers):
            name = tier + "_" + piece
            if name not in parts:
                continue
            for other in parts.values():
                other.hide_render = other is not parts[name]
            floor.location.z = low.z - 0.002
            label = caption(scene, camera, tier + " " + piece, lens, tile[1] / tile[0])
            path = os.path.join(folder, name + ".png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(label)
            picture = bpy.data.images.load(path)
            pixels = numpy.empty(tile[0] * tile[1] * 4, dtype=numpy.float32)
            picture.pixels.foreach_get(pixels)
            top = height - gap - row * (tile[1] + gap)
            left = gap + column * (tile[0] + gap)
            sheet[top - tile[1]:top, left:left + tile[0]] = pixels.reshape(tile[1], tile[0], 4)
            bpy.data.images.remove(picture)
            print("TILE", name, flush=True)
        bpy.data.objects.remove(camera)
    result = bpy.data.images.new("tiers_sheet", width, height, alpha=False)
    result.pixels.foreach_set(sheet.ravel())
    result.filepath_raw = target
    result.file_format = 'PNG'
    result.save()
    print("SHEET", target, width, "x", height, flush=True)


def main():
    if mode == "sheet":
        tiers_sheet(os.path.join(output_root, "structures", "structures.gltf"), os.path.join(preview_root, "tiers_sheet.png"))
        return
    for name in wanted:
        k.reset()
        objects = build(name)
        print("BUILT", name, sum(triangles(obj) for obj in objects), "tris", flush=True)
        if mode == "preview":
            for obj in objects:
                hidden = [other for other in objects if other != obj]
                for other in hidden:
                    other.hide_render = True
                extra = ["close"] if obj.name.endswith(("_wall", "_roof", "_doorway", "_window")) and "close" not in views else []
                turntable.render_views([obj], preview_root, obj.name, views + extra, samples, hdri)
                if obj.name.endswith(("_roof", "_floor", "_stairs")):
                    look_up(obj, obj.name)
                for other in hidden:
                    other.hide_render = False
        elif mode == "overview":
            groups = [tier for tier in tiers if any(obj.name.startswith(tier + "_") for obj in objects)]
            for tier in groups:
                overview(objects, "overview_" + tier, [tier], views)
            if len(groups) > 1:
                overview(objects, "overview_lineup", groups, ["wide"])
        elif mode == "export":
            directory = os.path.join(output_root, name)
            os.makedirs(directory, exist_ok=True)
            bake_world()
            for obj in objects:
                isolate(objects, obj)
                coverage = bake_piece(obj, directory)
                print("BAKED", obj.name, triangles(obj), "tris", texture_size, "px", round(texture_size * math.sqrt(coverage / max(surface_area(obj), 1e-6)), 1), "px/m", flush=True)
            for obj in objects:
                obj.location = v(0.0, 0.0, 0.0)
            bpy.context.view_layer.update()
            k.export(os.path.join(directory, name + ".gltf"))
            for obj in objects:
                if not only or obj.name in only:
                    hidden = [other for other in objects if other != obj]
                    for other in hidden:
                        other.hide_render = True
                    turntable.render_views([obj], preview_root, obj.name + "_baked", views, samples, hdri)
                    for other in hidden:
                        other.hide_render = False


if __name__ == "__main__":
    main()
