import bpy
import math
import os
import numpy
from mathutils import Euler, Vector

import ground_kit as kit

glyphs = {"A": "0E11111F111111", "B": "1E11111E11111E", "C": "0E11101010110E", "D": "1E11111111111E", "E": "1F10101E10101F", "F": "1F10101E101010", "G": "0E11101711110F", "H": "1111111F111111", "I": "0E04040404040E", "J": "0702020202120C", "K": "11121418141211", "L": "1010101010101F", "M": "111B1515111111", "N": "11191513111111", "O": "0E11111111110E", "P": "1E11111E101010", "Q": "0E11111115120D", "R": "1E11111E141211", "S": "0F10100E01011E", "T": "1F040404040404", "U": "1111111111110E", "V": "11111111110A04", "W": "11111115151B11","X": "11110A040A1111", "Y": "11110A04040404", "Z": "1F01020408101F", "0": "0E11131519110E", "1": "040C040404040E", "2": "0E11010204081F", "3": "1E01010E01011E", "4": "02060A121F0202", "5": "1F101E0101110E", "6": "0608101E11110E", "7": "1F010204080808", "8": "0E11110E11110E", "9": "0E11110F01020C", "_": "0000000000001F", ".": "00000000000C0C", " ": "00000000000000"}


def load(directory, name):
    maps = {}
    for key, suffix in (("diff", "diff"), ("normal", "nor_dx"), ("arm", "arm"), ("disp", "disp")):
        maps[key] = kit.read_image(os.path.join(directory, "%s_%s_2k.jpg" % (name, suffix))).astype(numpy.float32) / 255.0
    return maps


def relight(maps, sun=(-0.52, 0.58, 0.63), power=1.15, ambient=0.34):
    albedo = kit.to_linear(maps["diff"][..., :3])
    normal = maps["normal"][..., :3] * 2.0 - 1.0
    normal /= numpy.maximum(numpy.linalg.norm(normal, axis=-1, keepdims=True), 1e-6)
    direction = numpy.array(sun, dtype=numpy.float32) / numpy.linalg.norm(sun)
    shade = numpy.maximum(normal[..., 0] * direction[0] - normal[..., 1] * direction[1] + normal[..., 2] * direction[2], 0.0) * power + ambient * maps["arm"][..., 0]
    return albedo * shade[..., None]


def tiled(directory, name, path, cell=512):
    lit = relight(load(directory, name))
    factor = lit.shape[0] // cell
    small = lit.reshape(cell, factor, cell, factor, 3).mean(axis=(1, 3))
    kit.write_image(path, numpy.clip(kit.to_srgb(numpy.tile(small, (3, 3, 1))) * 255.0 + 0.5, 0.0, 255.0).astype(numpy.uint8))


def inspect(directory, name, work, origin=(640, 640), span=720):
    maps = load(directory, name)
    size = maps["diff"].shape[0]
    half = maps["diff"][..., :3].reshape(size // 2, 2, size // 2, 2, 3).mean(axis=(1, 3))
    kit.write_image(os.path.join(work, name + "_view.png"), numpy.clip(half * 255.0 + 0.5, 0.0, 255.0).astype(numpy.uint8))
    rows = slice(origin[1], origin[1] + span)
    columns = slice(origin[0], origin[0] + span)
    grey = lambda plane: numpy.repeat(plane[rows, columns, None], 3, axis=2)
    top = numpy.concatenate([maps["diff"][rows, columns, :3], maps["normal"][rows, columns, :3]], axis=1)
    middle = numpy.concatenate([grey(maps["arm"][..., 0]), grey(maps["arm"][..., 1])], axis=1)
    bottom = numpy.concatenate([grey(maps["disp"][..., 0]), kit.to_srgb(relight(maps, (-0.75, 0.55, 0.36), 1.6, 0.3))[rows, columns]], axis=1)
    kit.write_image(os.path.join(work, name + "_crop.png"), numpy.clip(numpy.concatenate([top, middle, bottom], axis=0) * 255.0 + 0.5, 0.0, 255.0).astype(numpy.uint8))


def lit(directory, name, size, relief, path, width=1600, height=1000, samples=72):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    maps = load(directory, name)
    levels = [numpy.ascontiguousarray(maps["disp"][::-1, :, 0])]
    while levels[-1].shape[0] > 64:
        levels.append(kit.resize(levels[-1], levels[-1].shape[0] // 2))
    eye = Vector((size * 0.31, size * 0.17, 1.55))
    turn = Euler((math.radians(90.0 - 33.0), 0.0, math.radians(-32.0)), 'XYZ')
    data = bpy.data.cameras.new("view")
    data.lens = 32.0
    data.sensor_width = 36.0
    data.clip_start = 0.05
    data.clip_end = 60.0
    camera = bpy.data.objects.new("view", data)
    camera.location = eye
    camera.rotation_euler = turn
    scene.collection.objects.link(camera)
    scene.camera = camera
    rotation = numpy.array(turn.to_matrix(), dtype=numpy.float64)
    columns = int(width / 1.5)
    rows = int(height / 1.5)
    spread = 18.0 / 32.0
    a, b = numpy.meshgrid(numpy.linspace(-1.07, 1.07, columns + 1) * spread, numpy.linspace(-1.07, 1.07, rows + 1) * spread * height / width)
    ray = numpy.stack([a, b, -numpy.ones_like(a)], axis=-1) @ rotation.T
    reach = -eye.z / ray[..., 2]
    x = eye.x + ray[..., 0] * reach
    y = eye.y + ray[..., 1] * reach
    gap = numpy.hypot(numpy.gradient(x, axis=0), numpy.gradient(y, axis=0))
    level = numpy.clip(numpy.log2(numpy.maximum(gap / (size / levels[0].shape[0]), 1.0)), 0.0, len(levels) - 1.001)
    lower = numpy.floor(level).astype(numpy.int64)
    displaced = numpy.zeros_like(x)
    for index in range(len(levels) - 1):
        mask = lower == index
        if mask.any():
            part = (level[mask] - index).astype(numpy.float32)
            displaced[mask] = kit.sample(levels[index], x[mask], y[mask], size) * (1.0 - part) + kit.sample(levels[index + 1], x[mask], y[mask], size) * part
    vertices = numpy.stack([x, y, (displaced - 0.5) * relief], axis=-1).reshape(-1, 3)
    index = numpy.arange((rows + 1) * (columns + 1), dtype=numpy.int64).reshape(rows + 1, columns + 1)
    mesh = kit.make_mesh("plane", vertices, {4: numpy.stack([index[:-1, :-1], index[:-1, 1:], index[1:, 1:], index[1:, :-1]], axis=-1).reshape(-1, 4)})
    shader = kit.graph("preview")
    place = shader.position() * (1.0 / size)
    images = {}
    for key, suffix, space in (("diff", "diff", 'sRGB'), ("normal", "nor_dx", 'Non-Color'), ("arm", "arm", 'Non-Color')):
        images[key] = bpy.data.images.load(os.path.join(directory, "%s_%s_2k.jpg" % (name, suffix)))
        images[key].colorspace_settings.name = space
    normal = shader.image(images["normal"], place) * 2.0 - 1.0
    surface = shader.new('ShaderNodeBsdfPrincipled')
    shader.feed(surface.inputs['Base Color'], shader.image(images["diff"], place))
    shader.feed(surface.inputs['Roughness'], shader.image(images["arm"], place).y)
    shader.feed(surface.inputs['Normal'], shader.vector_math('NORMALIZE', shader.combine(normal.x, -normal.y, normal.z)))
    shader.tree.links.new(surface.outputs[0], shader.new('ShaderNodeOutputMaterial').inputs['Surface'])
    mesh.materials.append(shader.material)
    scene.collection.objects.link(bpy.data.objects.new("plane", mesh))
    lamp = bpy.data.lights.new("sun", 'SUN')
    lamp.energy = 5.6
    lamp.angle = math.radians(2.0)
    lamp.color = (1.0, 0.95, 0.87)
    sun = bpy.data.objects.new("sun", lamp)
    sun.rotation_euler = Euler((math.radians(90.0 - 21.0), 0.0, math.radians(-32.0 + 115.0)), 'XYZ')
    scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs['Color'].default_value = (0.62, 0.72, 0.92, 1.0)
    world.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.5
    scene.world = world
    scene.render.engine = 'CYCLES'
    kit.accelerate(scene)
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 3
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Base Contrast'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def label(image, text, left, top, scale=3):
    for position, letter in enumerate(text.upper()):
        code = glyphs.get(letter, glyphs[" "])
        for row in range(7):
            bits = int(code[row * 2:row * 2 + 2], 16)
            for column in range(5):
                if bits & (16 >> column):
                    y = top + row * scale
                    x = left + (position * 6 + column) * scale
                    image[y:y + scale, x:x + scale] = 255


def sheet(directory, names, path, columns=4, cell=(640, 400)):
    rows = (len(names) + columns - 1) // columns
    banner = 34
    canvas = numpy.full((rows * (cell[1] + banner), columns * cell[0], 3), 18, dtype=numpy.uint8)
    for index, name in enumerate(names):
        source = os.path.join(directory, name + ".png")
        left = (index % columns) * cell[0]
        top = (index // columns) * (cell[1] + banner)
        label(canvas, name, left + 10, top + 7)
        if os.path.exists(source):
            picture = kit.read_image(source)[..., :3].astype(numpy.float32)
            factor = picture.shape[1] / cell[0]
            ys = numpy.minimum((numpy.arange(cell[1]) * factor).astype(numpy.int64), picture.shape[0] - 1)
            xs = numpy.minimum((numpy.arange(cell[0]) * factor).astype(numpy.int64), picture.shape[1] - 1)
            taps = max(1, int(round(factor)))
            total = numpy.zeros((cell[1], cell[0], 3), dtype=numpy.float32)
            for oy in range(taps):
                for ox in range(taps):
                    total += picture[numpy.minimum(ys + oy, picture.shape[0] - 1)][:, numpy.minimum(xs + ox, picture.shape[1] - 1)]
            canvas[top + banner:top + banner + cell[1], left:left + cell[0]] = numpy.clip(total / (taps * taps) + 0.5, 0.0, 255.0).astype(numpy.uint8)
    kit.write_image(path, canvas)
