import bpy
import bmesh
import json
import math
import os
import random
import struct
import zlib
import numpy
from mathutils import Matrix, Vector

convert_root = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(convert_root))
source_root = os.path.join(repo_root, "assets", "source", "flora")
models_root = os.path.join(repo_root, "assets", "raw", "models")
preview_root = os.path.join(repo_root, "assets", "previews", "flora")
atlas_size = 2048
impostor_frames = 8
impostor_columns = 4
impostor_cell = (256, 512)


def v(x, y, z):
    return Vector((x, y, z))


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(edge0, edge1, value):
    t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, t):
    return tuple(a[index] + (b[index] - a[index]) * t for index in range(len(a)))


def model_name(species, variant, suffix=""):
    return "flora_%s_%d%s" % (species, variant, suffix)


def species_directory(species):
    return os.path.join(source_root, species)


def export_directory(species):
    return os.path.join(source_root, species, "export")


def model_directory(species, name):
    return os.path.join(export_directory(species), name)


def texture_directory(species):
    return model_directory(species, model_name(species, 0))


def texture_path(species, part, kind, size="2k"):
    return os.path.join(texture_directory(species), "flora_%s_%s_%s_%s.png" % (species, part, kind, size))


def texture_set(species, part, size="2k"):
    return {kind: texture_path(species, part, kind, size) for kind in ("diff", "alpha", "nor_gl", "arm")}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def accelerate(scene):
    preferences = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            preferences.compute_device_type = kind
        except TypeError:
            continue
        preferences.get_devices()
        devices = [device for device in preferences.devices if device.type == kind]
        if devices:
            for device in preferences.devices:
                device.use = device.type == kind
            scene.cycles.device = 'GPU'
            return kind
    scene.cycles.device = 'CPU'
    return 'CPU'


def load_pixels(path):
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = 'Non-Color'
    width, height = image.size
    data = numpy.empty(width * height * 4, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(height, width, 4)


def write_png(path, data):
    pixels = numpy.clip(numpy.asarray(data, dtype=numpy.float32), 0.0, 1.0)
    if pixels.ndim == 2:
        pixels = pixels[:, :, None]
    height, width, channels = pixels.shape
    if channels == 2:
        pixels = numpy.concatenate([pixels, numpy.zeros((height, width, 1), dtype=numpy.float32)], axis=2)
        channels = 3
    bytes_ = (pixels[::-1] * 255.0 + 0.5).astype(numpy.uint8)
    raw = numpy.concatenate([numpy.zeros((height, 1), dtype=numpy.uint8), bytes_.reshape(height, width * channels)], axis=1).tobytes()
    kind = {1: 0, 3: 2, 4: 6}[channels]

    def chunk(tag, payload):
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, kind, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def png_size(path):
    with open(path, "rb") as handle:
        header = handle.read(26)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height, depth, kind = struct.unpack(">IIBB", header[16:26])
    return width, height, depth, kind


def to_srgb(linear):
    linear = numpy.clip(linear, 0.0, 1.0)
    return numpy.where(linear <= 0.0031308, linear * 12.92, 1.055 * numpy.power(numpy.maximum(linear, 1e-8), 1.0 / 2.4) - 0.055)


def to_linear(encoded):
    encoded = numpy.clip(encoded, 0.0, 1.0)
    return numpy.where(encoded <= 0.04045, encoded / 12.92, numpy.power((encoded + 0.055) / 1.055, 2.4))


def flood(color, weight, keep=0.35):
    weight = weight.astype(numpy.float32)
    levels = [(color * weight[:, :, None], weight)]
    while levels[-1][1].shape[0] > 1 and levels[-1][1].shape[1] > 1:
        total, count = levels[-1]
        rows = total.shape[0] // 2
        columns = total.shape[1] // 2
        levels.append((total[:rows * 2, :columns * 2].reshape(rows, 2, columns, 2, -1).sum(axis=(1, 3)), count[:rows * 2, :columns * 2].reshape(rows, 2, columns, 2).sum(axis=(1, 3))))
    total, count = levels[-1]
    filled = total / numpy.maximum(count, 1e-6)[:, :, None]
    for total, count in reversed(levels[:-1]):
        grown = numpy.repeat(numpy.repeat(filled, 2, axis=0), 2, axis=1)
        pad_rows = total.shape[0] - grown.shape[0]
        pad_columns = total.shape[1] - grown.shape[1]
        if pad_rows > 0 or pad_columns > 0:
            grown = numpy.pad(grown, ((0, max(pad_rows, 0)), (0, max(pad_columns, 0)), (0, 0)), mode='edge')
        grown = grown[:total.shape[0], :total.shape[1]]
        known = count > 1e-5
        filled = numpy.where(known[:, :, None], total / numpy.maximum(count, 1e-6)[:, :, None], grown)
    solid = weight > keep
    return numpy.where(solid[:, :, None], color, filled)


def grow(color, alpha, passes):
    result = color.copy()
    known = alpha > 0.02
    for index in range(passes):
        total = numpy.zeros_like(result)
        count = numpy.zeros(alpha.shape, dtype=numpy.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            shifted_known = numpy.roll(numpy.roll(known, dy, 0), dx, 1)
            total += numpy.roll(numpy.roll(result, dy, 0), dx, 1) * shifted_known[:, :, None]
            count += shifted_known
        fill = (known == False) & (count > 0)
        result[fill] = total[fill] / count[fill][:, None]
        known = known | fill
    return result, known


def lattice(grid, x, y):
    rows, columns = grid.shape
    x0 = numpy.floor(x).astype(numpy.int64)
    y0 = numpy.floor(y).astype(numpy.int64)
    fx = x - x0
    fy = y - y0
    fx = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
    fy = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0)
    x1 = (x0 + 1) % columns
    y1 = (y0 + 1) % rows
    x0 = x0 % columns
    y0 = y0 % rows
    top = grid[y0, x0] * (1.0 - fx) + grid[y0, x1] * fx
    bottom = grid[y1, x0] * (1.0 - fx) + grid[y1, x1] * fx
    return top * (1.0 - fy) + bottom * fy


def noise(width, height, cells_x, cells_y, rng, warp=None):
    grid = rng.random((max(1, int(cells_y)), max(1, int(cells_x)))).astype(numpy.float32)
    xs = (numpy.arange(width, dtype=numpy.float32) + 0.5) / width * grid.shape[1]
    ys = (numpy.arange(height, dtype=numpy.float32) + 0.5) / height * grid.shape[0]
    x, y = numpy.meshgrid(xs, ys)
    if warp is not None:
        x = x + warp[0] * grid.shape[1]
        y = y + warp[1] * grid.shape[0]
    return lattice(grid, x, y)


def fbm(width, height, cells_x, cells_y, octaves, rng, gain=0.5, warp=None):
    total = numpy.zeros((height, width), dtype=numpy.float32)
    amplitude = 1.0
    weight = 0.0
    for octave in range(octaves):
        total += noise(width, height, cells_x * 2 ** octave, cells_y * 2 ** octave, rng, warp) * amplitude
        weight += amplitude
        amplitude *= gain
    return total / weight


def worley(width, height, cells_x, cells_y, rng, jitter=1.0, warp=None):
    cells_x = max(1, int(cells_x))
    cells_y = max(1, int(cells_y))
    points_x = (rng.random((cells_y, cells_x)).astype(numpy.float32) - 0.5) * jitter + 0.5
    points_y = (rng.random((cells_y, cells_x)).astype(numpy.float32) - 0.5) * jitter + 0.5
    xs = (numpy.arange(width, dtype=numpy.float32) + 0.5) / width * cells_x
    ys = (numpy.arange(height, dtype=numpy.float32) + 0.5) / height * cells_y
    x, y = numpy.meshgrid(xs, ys)
    if warp is not None:
        x = x + warp[0] * cells_x
        y = y + warp[1] * cells_y
    cx = numpy.floor(x).astype(numpy.int64)
    cy = numpy.floor(y).astype(numpy.int64)
    first = numpy.full((height, width), 1e9, dtype=numpy.float32)
    second = numpy.full((height, width), 1e9, dtype=numpy.float32)
    identity = numpy.zeros((height, width), dtype=numpy.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx = cx + dx
            ny = cy + dy
            wx = nx % cells_x
            wy = ny % cells_y
            px = nx + points_x[wy, wx]
            py = ny + points_y[wy, wx]
            distance = numpy.sqrt((px - x) ** 2 + (py - y) ** 2)
            closer = distance < first
            second = numpy.where(closer, first, numpy.minimum(second, distance))
            identity = numpy.where(closer, wy * cells_x + wx, identity)
            first = numpy.where(closer, distance, first)
    return first, second, identity


def blur(image, radius_x, radius_y=None):
    radius_y = radius_x if radius_y is None else radius_y
    squeeze = image.ndim == 2
    data = image[:, :, None] if squeeze else image
    height, width = data.shape[:2]
    fy = numpy.fft.fftfreq(height)[:, None]
    fx = numpy.fft.rfftfreq(width)[None, :]
    kernel = numpy.exp(-2.0 * (math.pi ** 2) * ((fx * radius_x) ** 2 + (fy * radius_y) ** 2))
    result = numpy.stack([numpy.fft.irfft2(numpy.fft.rfft2(data[:, :, channel]) * kernel, s=(height, width)) for channel in range(data.shape[2])], axis=2).astype(numpy.float32)
    return result[:, :, 0] if squeeze else result


def height_normal(height, strength):
    dx = (numpy.roll(height, -1, axis=1) - numpy.roll(height, 1, axis=1)) * 0.5 * strength
    dy = (numpy.roll(height, -1, axis=0) - numpy.roll(height, 1, axis=0)) * 0.5 * strength
    length = numpy.sqrt(dx * dx + dy * dy + 1.0)
    return numpy.stack([-dx / length * 0.5 + 0.5, -dy / length * 0.5 + 0.5, 1.0 / length * 0.5 + 0.5], axis=2).astype(numpy.float32)


def height_occlusion(height, radius, strength):
    return numpy.clip(1.0 - (blur(height, radius) - height) * strength, 0.0, 1.0).astype(numpy.float32)


def ramp(value, stops):
    value = numpy.clip(value, 0.0, 1.0)
    result = numpy.zeros(value.shape + (3,), dtype=numpy.float32)
    for index in range(len(stops) - 1):
        t0, c0 = stops[index]
        t1, c1 = stops[index + 1]
        local = numpy.clip((value - t0) / max(t1 - t0, 1e-6), 0.0, 1.0)
        inside = (value >= t0) if index == 0 else (value > t0)
        segment = numpy.array(c0, dtype=numpy.float32)[None, None, :] * (1.0 - local[:, :, None]) + numpy.array(c1, dtype=numpy.float32)[None, None, :] * local[:, :, None]
        result = numpy.where(inside[:, :, None], segment, result)
    result = numpy.where((value < stops[0][0])[:, :, None], numpy.array(stops[0][1], dtype=numpy.float32)[None, None, :], result)
    return result


def blend(base, top, mask):
    return base * (1.0 - mask[:, :, None]) + top * mask[:, :, None]


def step(value, edge0, edge1):
    t = numpy.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def image_node(tree, path, colorspace):
    node = tree.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(path, check_existing=True)
    node.image.colorspace_settings.name = colorspace
    return node


def emission_material(name, builder):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    emission = tree.nodes.new('ShaderNodeEmission')
    tree.links.new(builder(tree), emission.inputs['Color'])
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return material


def tint_color(tree):
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_name = "tint"
    attribute.attribute_type = 'GEOMETRY'
    return attribute.outputs['Color']


def tint_alpha(tree):
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_name = "tint"
    attribute.attribute_type = 'GEOMETRY'
    return attribute.outputs['Alpha']


def normal_color(tree):
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    scale = tree.nodes.new('ShaderNodeVectorMath')
    scale.operation = 'MULTIPLY_ADD'
    tree.links.new(geometry.outputs['Normal'], scale.inputs[0])
    scale.inputs[1].default_value = (0.5, 0.5, 0.5)
    scale.inputs[2].default_value = (0.5, 0.5, 0.5)
    return scale.outputs['Vector']


def occlusion_color(distance):
    def builder(tree):
        occlusion = tree.nodes.new('ShaderNodeAmbientOcclusion')
        occlusion.inputs['Distance'].default_value = distance
        occlusion.samples = 16
        return occlusion.outputs['AO']
    return builder


def depth_color(tree):
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    separate = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(geometry.outputs['Position'], separate.inputs[0])
    return separate.outputs['Z']


def surface_material(name, textures, cut):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = image_node(tree, textures["diff"], 'sRGB')
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    normal_image = image_node(tree, textures["nor_gl"], 'Non-Color')
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(normal_image.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    shader.inputs['Roughness'].default_value = 0.7
    material["flora_cut"] = 1 if cut else 0
    material["flora_textures"] = json.dumps(textures)
    return material


def pass_material(name, kind, image_path, alpha_path):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    if kind == "albedo":
        color = image_node(tree, image_path, 'sRGB')
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
        alpha = image_node(tree, alpha_path, 'Non-Color')
        cut = tree.nodes.new('ShaderNodeMath')
        cut.operation = 'GREATER_THAN'
        cut.inputs[1].default_value = 0.5
        tree.links.new(alpha.outputs['Color'], cut.inputs[0])
        hole = tree.nodes.new('ShaderNodeBsdfTransparent')
        blend_node = tree.nodes.new('ShaderNodeMixShader')
        tree.links.new(cut.outputs['Value'], blend_node.inputs['Fac'])
        tree.links.new(hole.outputs['BSDF'], blend_node.inputs[1])
        tree.links.new(shader, blend_node.inputs[2])
        shader = blend_node.outputs['Shader']
    tree.links.new(shader, output.inputs['Surface'])
    return material


def material_entry(name, textures, cut, base_index):
    entry = {"name": name, "doubleSided": bool(cut), "pbrMetallicRoughness": {"baseColorTexture": {"index": base_index}, "metallicRoughnessTexture": {"index": base_index + 2}, "metallicFactor": 0.0, "roughnessFactor": 1.0}, "normalTexture": {"index": base_index + 1}, "occlusionTexture": {"index": base_index + 2}}
    if cut:
        entry["alphaMode"] = "MASK"
        entry["alphaCutoff"] = 0.5
    return entry


def patch_materials(document, directory):
    materials = []
    textures = []
    images = []
    for material in document.get("materials", []):
        source = bpy.data.materials.get(material["name"])
        files = json.loads(source["flora_textures"])
        cut = bool(source["flora_cut"])
        base = len(textures)
        for kind in ("diff", "nor_gl", "arm"):
            textures.append({"sampler": 0, "source": len(images)})
            images.append({"mimeType": "image/png", "name": os.path.basename(files[kind]), "uri": os.path.relpath(files[kind], directory).replace("\\", "/")})
        materials.append(material_entry(material["name"], files, cut, base))
    document["materials"] = materials
    document["textures"] = textures
    document["images"] = images
    document["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]


def export_model(species, name, objects):
    directory = model_directory(species, name)
    os.makedirs(directory, exist_ok=True)
    for stale in os.listdir(directory):
        if stale.endswith(".gltf") or stale.endswith(".bin"):
            os.remove(os.path.join(directory, stale))
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in objects)
    path = os.path.join(directory, name + ".gltf")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_keep_originals=True, export_yup=True, export_apply=True, export_skins=False, export_animations=False, export_morph=False, export_cameras=False, export_lights=False, export_extras=False)
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    patch_materials(document, directory)
    document["asset"]["generator"] = "zero point flora"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    triangles = sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in objects)
    print("EXPORTED", name, triangles)
    return triangles


def write_quad(species, name, textures, width, bottom, top):
    directory = model_directory(species, name)
    os.makedirs(directory, exist_ok=True)
    half = width * 0.5
    positions = [(-half, bottom, 0.0), (half, bottom, 0.0), (half, top, 0.0), (-half, top, 0.0)]
    normals = [(0.0, 0.0, -1.0)] * 4
    uvs = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    blob = struct.pack("<12f", *[c for p in positions for c in p]) + struct.pack("<12f", *[c for n in normals for c in n]) + struct.pack("<8f", *[c for u in uvs for c in u]) + struct.pack("<6I", 0, 1, 2, 0, 2, 3)
    with open(os.path.join(directory, name + ".bin"), "wb") as handle:
        handle.write(blob)
    images = [{"mimeType": "image/png", "name": os.path.basename(textures[kind]), "uri": os.path.relpath(textures[kind], directory).replace("\\", "/")} for kind in ("diff", "nor_gl", "arm")]
    document = {
        "asset": {"version": "2.0", "generator": "zero point flora"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "impostor", "mesh": 0}],
        "meshes": [{"name": "impostor", "primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]}],
        "materials": [{"name": "impostor", "alphaMode": "MASK", "alphaCutoff": 0.5, "doubleSided": True, "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicRoughnessTexture": {"index": 2}, "metallicFactor": 0.0, "roughnessFactor": 1.0}, "normalTexture": {"index": 1}, "occlusionTexture": {"index": 2}}],
        "textures": [{"source": 0}, {"source": 1}, {"source": 2}],
        "images": images,
        "buffers": [{"uri": name + ".bin", "byteLength": len(blob)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 48}, {"buffer": 0, "byteOffset": 96, "byteLength": 32}, {"buffer": 0, "byteOffset": 128, "byteLength": 24}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-half, bottom, 0.0], "max": [half, top, 0.0]}, {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"}, {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC2"}, {"bufferView": 3, "componentType": 5125, "count": 6, "type": "SCALAR"}],
    }
    with open(os.path.join(directory, name + ".gltf"), "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)


def frames(points, crest):
    count = len(points)
    tangents = []
    for index in range(count):
        tangent = points[min(index + 1, count - 1)] - points[max(index - 1, 0)]
        tangents.append(tangent.normalized() if tangent.length > 1e-9 else Vector((0.0, 0.0, 1.0)))
    side = -(crest - tangents[0] * crest.dot(tangents[0]))
    if side.length < 1e-4:
        side = tangents[0].cross(Vector((1.0, 0.0, 0.0)))
        if side.length < 1e-4:
            side = tangents[0].cross(Vector((0.0, 1.0, 0.0)))
    side.normalize()
    result = []
    for index in range(count):
        side = side - tangents[index] * side.dot(tangents[index])
        if side.length < 1e-6:
            side = tangents[index].cross(Vector((0.0, 0.0, 1.0)))
        side.normalize()
        result.append((tangents[index], side.copy(), tangents[index].cross(side).normalized()))
    return result


def point_on(points, s):
    s = clamp(s, 0.0, 1.0)
    index = min(int(s * (len(points) - 1)), len(points) - 2)
    local = s * (len(points) - 1) - index
    return points[index].lerp(points[index + 1], local), (points[index + 1] - points[index]).normalized()


def path_length(points):
    return sum((points[index + 1] - points[index]).length for index in range(len(points) - 1))


def resample(points, count):
    lengths = [0.0]
    for index in range(len(points) - 1):
        lengths.append(lengths[-1] + (points[index + 1] - points[index]).length)
    total = lengths[-1]
    result = []
    cursor = 0
    for step_index in range(count):
        target = total * step_index / max(count - 1, 1)
        while cursor < len(points) - 2 and lengths[cursor + 1] < target:
            cursor += 1
        span = max(lengths[cursor + 1] - lengths[cursor], 1e-9)
        result.append(points[cursor].lerp(points[cursor + 1], clamp((target - lengths[cursor]) / span, 0.0, 1.0)))
    return result


def any_perpendicular(direction):
    side = direction.cross(Vector((0.0, 0.0, 1.0)))
    if side.length < 1e-4:
        side = direction.cross(Vector((1.0, 0.0, 0.0)))
    return side.normalized()


def rotate_about(vector, axis, angle):
    return Matrix.Rotation(angle, 3, axis) @ vector


def human(scene, location, facing):
    outline = [(-0.10, 0.0), (-0.20, 0.0), (-0.21, 0.06), (-0.13, 0.10), (-0.155, 0.48), (-0.17, 0.90), (-0.19, 1.02), (-0.245, 0.80), (-0.30, 0.78), (-0.31, 0.86), (-0.285, 1.10), (-0.265, 1.42), (-0.20, 1.49), (-0.075, 1.53), (-0.065, 1.575), (-0.10, 1.63), (-0.105, 1.71), (-0.075, 1.78), (0.0, 1.80), (0.075, 1.78), (0.105, 1.71), (0.10, 1.63), (0.065, 1.575), (0.075, 1.53), (0.20, 1.49), (0.265, 1.42), (0.285, 1.10), (0.31, 0.86), (0.30, 0.78), (0.245, 0.80), (0.19, 1.02), (0.17, 0.90), (0.155, 0.48), (0.13, 0.10), (0.21, 0.06), (0.20, 0.0), (0.10, 0.0), (0.02, 0.0), (0.025, 0.45), (0.0, 0.84), (-0.025, 0.45), (-0.02, 0.0)]
    mesh = bpy.data.meshes.new("human")
    bm = bmesh.new()
    verts = [bm.verts.new((x, 0.0, z)) for x, z in outline]
    bm.faces.new(verts)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    material = bpy.data.materials.new("human")
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    emission = tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (0.75, 0.16, 0.06, 1.0)
    emission.inputs['Strength'].default_value = 1.0
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    mesh.materials.append(material)
    obj = bpy.data.objects.new("human", mesh)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, math.atan2(facing.y, facing.x) + math.pi * 0.5)
    scene.collection.objects.link(obj)
    return obj
