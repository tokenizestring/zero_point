import bpy
import os
import sys
import numpy

arguments = sys.argv[sys.argv.index("--") + 1:]
source_root = arguments[0]
output_root = arguments[1]
only = arguments[2] if len(arguments) > 2 else ""

characters = [("Professions/Military_Male_01", "military_male_01", "hollow"), ("Professions/Military_Male_04", "military_male_04", "hollow"), ("Professions/Police_Male_02", "police_male_02", "hollow"), ("Adults/Male_Adult_05", "male_adult_05", "hollow"), ("Professions/Construction_Male_01", "construction_male_01", "hollow"), ("Adults/Male_Adult_01", "survivor", "castaway")]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def smoothstep(low, high, value):
    t = numpy.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def fractal(width, height, cells, octaves, seed, stretch=1):
    rng = numpy.random.default_rng(seed)
    total = numpy.zeros((height, width), dtype=numpy.float32)
    amplitude = 1.0
    norm = 0.0
    for octave in range(octaves):
        count = cells * (2 ** octave)
        grid = rng.random((count * stretch + 1, count + 1)).astype(numpy.float32)
        xs = numpy.linspace(0.0, count, width, endpoint=False)
        ys = numpy.linspace(0.0, count * stretch, height, endpoint=False)
        x0 = xs.astype(numpy.int32)
        y0 = ys.astype(numpy.int32)
        fx = (xs - x0).astype(numpy.float32)
        fy = (ys - y0).astype(numpy.float32)
        fx = fx * fx * (3.0 - 2.0 * fx)
        fy = fy * fy * (3.0 - 2.0 * fy)
        top = grid[y0][:, x0] * (1.0 - fx) + grid[y0][:, x0 + 1] * fx
        bottom = grid[y0 + 1][:, x0] * (1.0 - fx) + grid[y0 + 1][:, x0 + 1] * fx
        total += (top * (1.0 - fy)[:, None] + bottom * fy[:, None]) * amplitude
        norm += amplitude
        amplitude *= 0.5
    return total / norm


def mix(base, target, amount):
    return base + (numpy.asarray(target, dtype=numpy.float32) - base) * amount[..., None]


def scratch(rgb, allowed, count, seed):
    rng = numpy.random.default_rng(seed)
    height, width = allowed.shape
    drawn = 0
    while drawn < count:
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        if allowed[int(y), int(x)]:
            angle = rng.uniform(0.0, numpy.pi * 2.0)
            bend = rng.uniform(-0.006, 0.006)
            length = int(rng.uniform(12, 46) * width / 2048)
            fresh = rng.uniform(0.3, 0.65)
            tone = numpy.array([0.5, 0.11, 0.07], dtype=numpy.float32) if rng.random() < 0.5 else numpy.array([0.24, 0.09, 0.06], dtype=numpy.float32)
            for step in range(length * 2):
                px = int(x)
                py = int(y)
                if 1 <= px < width - 1 and 1 <= py < height - 1 and allowed[py, px]:
                    rgb[py - 1:py + 2, px - 1:px + 2] = rgb[py - 1:py + 2, px - 1:px + 2] * 0.9 + numpy.array([0.55, 0.3, 0.26], dtype=numpy.float32) * 0.1
                    rgb[py, px] = rgb[py, px] * (1.0 - fresh) + tone * fresh
                angle += bend
                x += numpy.cos(angle) * 0.5
                y += numpy.sin(angle) * 0.5
            drawn += 1


def weather_skin(rgb, skin, extremity, grime, blotch, strength, seed):
    height, width = grime.shape
    luma = rgb @ numpy.array([0.3, 0.59, 0.11], dtype=numpy.float32)
    streaks = fractal(width, height, 2, 5, seed + 5, 6)
    soot = fractal(width, height, 5, 5, seed + 9)
    tanned = (rgb * 0.78 + luma[..., None] * 0.22) * numpy.array([0.97, 0.9, 0.8], dtype=numpy.float32)
    dirty = mix(tanned, tanned * numpy.array([0.46, 0.41, 0.35], dtype=numpy.float32), numpy.clip(0.25 + smoothstep(0.3, 0.75, grime) * (0.55 + 0.45 * extremity), 0.0, 1.0) * strength)
    dirty = mix(dirty, dirty * numpy.array([0.62, 0.56, 0.5], dtype=numpy.float32), smoothstep(0.55, 0.75, streaks) * 0.6 * strength)
    dirty = mix(dirty, numpy.array([0.11, 0.1, 0.09], dtype=numpy.float32), smoothstep(0.7, 0.86, soot) * (0.35 + 0.35 * extremity) * strength)
    bruised = mix(dirty, numpy.array([0.33, 0.25, 0.27], dtype=numpy.float32), smoothstep(0.72, 0.8, blotch) * 0.25 * strength)
    result = mix(rgb, bruised, skin.astype(numpy.float32))
    scratch(result, skin, int(70 * strength), seed)
    return result


def hollow(image, name, directory):
    width, height = image.size
    pixels = read_pixels(image).reshape(height, width, 4)
    rgb = pixels[:, :, :3].copy()
    brightest = rgb.max(axis=2)
    darkest = rgb.min(axis=2)
    saturation = (brightest - darkest) / numpy.maximum(brightest, 1e-4)
    used = brightest > 0.03
    skin = used & (rgb[:, :, 0] >= rgb[:, :, 1]) & (rgb[:, :, 1] >= rgb[:, :, 2] * 0.85) & (saturation > 0.14) & (saturation < 0.62) & (brightest > 0.22) & ((rgb[:, :, 0] - rgb[:, :, 2]) > 0.07)
    cloth = used & ~skin
    grime = fractal(width, height, 6, 5, 111)
    blotch = fractal(width, height, 3, 4, 123)
    tears = fractal(width, height, 3, 4, 151, 4) + (fractal(width, height, 64, 2, 153) - 0.5) * 0.09
    blood = fractal(width, height, 5, 4, 161)
    luma = rgb @ numpy.array([0.3, 0.59, 0.11], dtype=numpy.float32)
    pale = mix(rgb, luma[..., None] * numpy.array([0.93, 0.9, 0.86], dtype=numpy.float32), numpy.full(luma.shape, 0.45, dtype=numpy.float32))
    rgb = mix(rgb, pale, skin.astype(numpy.float32))
    rgb = weather_skin(rgb, skin, numpy.zeros_like(grime), grime, blotch, 1.1, 171)
    faded = rgb * 0.35 + luma[..., None] * numpy.array([0.9, 0.86, 0.76], dtype=numpy.float32) * 0.65
    faded = faded * (0.45 + 0.55 * grime[..., None])
    faded = mix(faded, faded * numpy.array([0.62, 0.52, 0.4], dtype=numpy.float32), smoothstep(0.48, 0.64, blotch))
    faded = mix(faded, numpy.array([0.18, 0.14, 0.1], dtype=numpy.float32), smoothstep(0.5, 0.85, grime) * 0.65)
    faded = mix(faded, numpy.array([0.2, 0.035, 0.025], dtype=numpy.float32), smoothstep(0.7, 0.8, blood) * 0.8)
    faded = mix(faded, numpy.array([0.5, 0.46, 0.38], dtype=numpy.float32), (smoothstep(0.7, 0.735, tears) - smoothstep(0.735, 0.742, tears)) * 0.7)
    faded = mix(faded, numpy.array([0.05, 0.04, 0.03], dtype=numpy.float32), smoothstep(0.738, 0.745, tears))
    rgb = mix(rgb, faded, cloth.astype(numpy.float32))
    rgb = mix(rgb, numpy.array([0.24, 0.05, 0.03], dtype=numpy.float32), (skin & (blood > 0.78)).astype(numpy.float32) * 0.55)
    pixels[:, :, :3] = numpy.clip(rgb, 0.0, 1.0)
    weathered = bpy.data.images.new(name, width, height, alpha=True)
    weathered.pixels.foreach_set(pixels.ravel())
    weathered.filepath_raw = os.path.join(directory, name + ".png")
    weathered.file_format = 'PNG'
    weathered.save()
    return weathered


def castaway(image, head, name, directory):
    width, height = image.size
    pixels = read_pixels(image).reshape(height, width, 4)
    rgb = pixels[:, :, :3].copy()
    u, v = numpy.meshgrid((numpy.arange(width) + 0.5) / width, 1.0 - (numpy.arange(height) + 0.5) / height)
    luma = rgb @ numpy.array([0.3, 0.59, 0.11], dtype=numpy.float32)
    saturation = rgb.max(axis=2) - rgb.min(axis=2)
    used = rgb.max(axis=2) > 0.03
    grime = fractal(width, height, 6, 5, 11)
    blotch = fractal(width, height, 3, 4, 23)
    tears = fractal(width, height, 3, 4, 51, 4) + (fractal(width, height, 64, 2, 53) - 0.5) * 0.09
    blood = fractal(width, height, 5, 4, 61)
    if head:
        rgb = weather_skin(rgb, used, numpy.zeros_like(grime), grime, blotch, 0.6, 71)
    else:
        def box(x0, x1, y0, y1):
            return (u >= x0) & (u <= x1) & (v >= y0) & (v <= y1)
        cloth = (box(0.0, 0.3, 0.0, 0.25) | box(0.7, 1.0, 0.0, 0.25) | box(0.0, 0.315, 0.43, 0.63) | box(0.685, 1.0, 0.43, 0.63) | box(0.32, 0.69, 0.0, 0.88)) & used
        shoes = (box(0.2, 0.36, 0.69, 1.0) | box(0.63, 0.8, 0.69, 1.0)) & (saturation < 0.12) & used & ~cloth
        skin = used & ~cloth & ~shoes
        extremity = smoothstep(0.55, 0.95, v)
        rgb = weather_skin(rgb, skin, extremity, grime, blotch, 1.0, 71)
        faded = rgb * 0.25 + luma[..., None] * numpy.array([0.95, 0.87, 0.7], dtype=numpy.float32) * 0.75
        faded = faded * (0.5 + 0.5 * grime[..., None])
        faded = mix(faded, faded * numpy.array([0.66, 0.53, 0.36], dtype=numpy.float32), smoothstep(0.5, 0.66, blotch))
        faded = mix(faded, numpy.array([0.23, 0.18, 0.12], dtype=numpy.float32), smoothstep(0.55, 0.88, grime) * 0.6)
        faded = mix(faded, numpy.array([0.24, 0.06, 0.035], dtype=numpy.float32), smoothstep(0.8, 0.86, blood) * 0.7)
        faded = mix(faded, numpy.array([0.58, 0.53, 0.43], dtype=numpy.float32), (smoothstep(0.72, 0.755, tears) - smoothstep(0.755, 0.762, tears)) * 0.7)
        faded = mix(faded, numpy.array([0.06, 0.045, 0.035], dtype=numpy.float32), smoothstep(0.758, 0.764, tears))
        rgb = mix(rgb, faded, cloth.astype(numpy.float32))
        rgb = mix(rgb, numpy.array([0.17, 0.13, 0.09], dtype=numpy.float32), shoes.astype(numpy.float32) * (0.55 + 0.35 * grime))
    pixels[:, :, :3] = numpy.clip(rgb, 0.0, 1.0)
    weathered = bpy.data.images.new(name, width, height, alpha=True)
    weathered.pixels.foreach_set(pixels.ravel())
    weathered.filepath_raw = os.path.join(directory, name + ".png")
    weathered.file_format = 'PNG'
    weathered.save()
    return weathered


def read_pixels(image):
    pixels = numpy.empty(image.size[0] * image.size[1] * 4, dtype=numpy.float32)
    image.pixels.foreach_get(pixels)
    return pixels.reshape(-1, 4)


def write_image(name, width, height, pixels, path):
    image = bpy.data.images.new(name, width, height, alpha=True)
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    image.colorspace_settings.name = 'Non-Color'
    return image


def linked_image(socket):
    for link in socket.links:
        if link.from_node.type == 'TEX_IMAGE':
            return link.from_node
    return None


sources = {}

arm_chains = {
    "right": ["Bip01 R Forearm", "Bip01 R ForeTwist", "Bip01 R ForeTwist1", "Bip01 R Hand"] + ["Bip01 R Finger%d%s" % (finger, joint) for finger in range(5) for joint in ("", "1", "2")],
    "left": ["Bip01 L Forearm", "Bip01 L ForeTwist", "Bip01 L ForeTwist1", "Bip01 L Hand"] + ["Bip01 L Finger%d%s" % (finger, joint) for finger in range(5) for joint in ("", "1", "2")],
}


def box_blur(field, radius):
    result = field.copy()
    for axis in (0, 1):
        total = numpy.zeros_like(result)
        for offset in range(-radius, radius + 1):
            total += numpy.roll(result, offset, axis=axis)
        result = total / (radius * 2 + 1)
    return result


def crop_pixels(image, x0, y0, x1, y1, size):
    width, height = image.size
    pixels = read_pixels(image).reshape(height, width, 4)[y0:y1, x0:x1].copy()
    temporary = bpy.data.images.new("crop", x1 - x0, y1 - y0, alpha=True, float_buffer=True)
    temporary.pixels.foreach_set(pixels.ravel())
    temporary.scale(size, size)
    result = numpy.empty(size * size * 4, dtype=numpy.float32)
    temporary.pixels.foreach_get(result)
    bpy.data.images.remove(temporary)
    return result.reshape(size, size, 4)


def weather_arm(color, normal, surface, seed):
    size = color.shape[0]
    rgb = box_blur(color[:, :, :3], 1) * 0.35 + color[:, :, :3] * 0.65
    nx = normal[:, :, 0] * 2.0 - 1.0
    ny = normal[:, :, 1] * 2.0 - 1.0
    divergence = (numpy.roll(nx, -1, axis=1) - numpy.roll(nx, 1, axis=1)) + (numpy.roll(ny, -1, axis=0) - numpy.roll(ny, 1, axis=0))
    cavity = box_blur(numpy.clip(-divergence * 2.4 - 0.08, 0.0, 1.0), 3)
    broad = fractal(size, size, 4, 4, seed)
    luma = rgb @ numpy.array([0.3, 0.59, 0.11], dtype=numpy.float32)
    rgb = rgb * 0.86 + luma[..., None] * 0.14
    dirt = numpy.clip(cavity * 0.9 + smoothstep(0.55, 0.8, broad) * 0.25, 0.0, 1.0)
    rgb = mix(rgb, rgb * numpy.array([0.66, 0.6, 0.55], dtype=numpy.float32), dirt * 0.5)
    scratch(rgb, numpy.ones((size, size), dtype=bool), 3, seed + 11)
    normal = box_blur(normal, 1) * 0.5 + normal * 0.5
    surface = surface.copy()
    surface[:, :, 1] = numpy.clip(numpy.clip(surface[:, :, 1], 0.5, 0.72) + dirt * 0.12, 0.45, 0.85)
    color = color.copy()
    color[:, :, :3] = numpy.clip(rgb, 0.0, 1.0)
    color[:, :, 3] = 1.0
    normal[:, :, 3] = 1.0
    surface[:, :, 3] = 1.0
    return color, normal, surface


def arm_detail(directory):
    for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
        for slot_index, slot in enumerate(obj.material_slots):
            if slot.material and slot.material.name in sources:
                original, normal_image, surface_image = sources[slot.material.name]
                uv = obj.data.uv_layers.active.data
                for side, names in arm_chains.items():
                    groups = {obj.vertex_groups[name].index for name in names if name in obj.vertex_groups}
                    arm = set()
                    for vertex in obj.data.vertices:
                        best = max(vertex.groups, key=lambda g: g.weight, default=None)
                        if best and best.group in groups:
                            arm.add(vertex.index)
                    polygons = [p for p in obj.data.polygons if p.material_index == slot_index and all(i in arm for i in p.vertices)]
                    if len(polygons) < 20:
                        continue
                    us = [uv[loop].uv[0] for p in polygons for loop in p.loop_indices]
                    vs = [uv[loop].uv[1] for p in polygons for loop in p.loop_indices]
                    width, height = original.size
                    x0 = max(0, int((min(us) - 0.006) * width))
                    x1 = min(width, int(numpy.ceil((max(us) + 0.006) * width)))
                    y0 = max(0, int((min(vs) - 0.006) * height))
                    y1 = min(height, int(numpy.ceil((max(vs) + 0.006) * height)))
                    color = crop_pixels(original, x0, y0, x1, y1, 1024)
                    normal = crop_pixels(normal_image, x0, y0, x1, y1, 1024)
                    surface = crop_pixels(surface_image, x0, y0, x1, y1, 1024)
                    color, normal, surface = weather_arm(color, normal, surface, 131 if side == "right" else 137)
                    name = slot.material.name + "_" + side + "_arm"
                    material = bpy.data.materials.new(name)
                    material.use_nodes = True
                    tree = material.node_tree
                    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
                    albedo_node = tree.nodes.new('ShaderNodeTexImage')
                    albedo_node.image = write_image(name + "_color", 1024, 1024, color, os.path.join(directory, name + "_color.png"))
                    albedo_node.image.colorspace_settings.name = 'sRGB'
                    tree.links.new(albedo_node.outputs['Color'], shader.inputs['Base Color'])
                    normal_node = tree.nodes.new('ShaderNodeTexImage')
                    normal_node.image = write_image(name + "_normal", 1024, 1024, normal, os.path.join(directory, name + "_normal.png"))
                    mapping = tree.nodes.new('ShaderNodeNormalMap')
                    tree.links.new(normal_node.outputs['Color'], mapping.inputs['Color'])
                    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
                    surface_node = tree.nodes.new('ShaderNodeTexImage')
                    surface_node.image = write_image(name + "_surface", 1024, 1024, surface, os.path.join(directory, name + "_surface.png"))
                    split = tree.nodes.new('ShaderNodeSeparateColor')
                    tree.links.new(surface_node.outputs['Color'], split.inputs['Color'])
                    tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
                    tree.links.new(split.outputs['Blue'], shader.inputs['Metallic'])
                    obj.data.materials.append(material)
                    new_index = len(obj.data.materials) - 1
                    for polygon in polygons:
                        polygon.material_index = new_index
                        for loop in polygon.loop_indices:
                            u, v = uv[loop].uv
                            uv[loop].uv = ((u * width - x0) / (x1 - x0), (v * height - y0) / (y1 - y0))
                    print("ARM DETAIL", side, len(polygons), "polygons crop", x0, y0, x1, y1)
                return


def prepare_material(material, textures, directory, style):
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = linked_image(shader.inputs['Base Color'])
    specular = linked_image(shader.inputs['Specular IOR Level'])
    normal_map = next((node for node in tree.nodes if node.type == 'NORMAL_MAP'), None)
    normal = linked_image(normal_map.inputs['Color']) if normal_map else None

    for node in (color, specular, normal):
        if node and node.image:
            node.image.filepath = os.path.join(textures, os.path.basename(node.image.filepath.replace('\\', '/')))
            node.image.reload()

    if color and color.image:
        color.image.name = material.name + "_color"

    original = color.image if color else None

    if color and color.image and style == "castaway" and "opacity" not in material.name.lower():
        color.image = castaway(color.image, "head" in material.name.lower(), material.name + "_color", directory)

    if color and color.image and style == "hollow" and "opacity" not in material.name.lower():
        color.image = hollow(color.image, material.name + "_color", directory)

    if normal and normal.image and normal.image.size[0]:
        pixels = read_pixels(normal.image)
        pixels[:, 1] = 1.0 - pixels[:, 1]
        pixels[:, 3] = 1.0
        normal.image = write_image(material.name + "_normal", normal.image.size[0], normal.image.size[1], pixels, os.path.join(directory, material.name + "_normal.png"))

    if specular and specular.image and specular.image.size[0]:
        pixels = read_pixels(specular.image)
        strength = pixels[:, :3].mean(axis=1)
        surface = numpy.ones_like(pixels)
        surface[:, 1] = numpy.clip(0.92 - strength * 0.8, 0.28, 0.95)
        surface[:, 2] = 0.0
        image = write_image(material.name + "_surface", specular.image.size[0], specular.image.size[1], surface, os.path.join(directory, material.name + "_surface.png"))
        for link in list(shader.inputs['Specular IOR Level'].links):
            tree.links.remove(link)
        shader.inputs['Specular IOR Level'].default_value = 0.5
        tree.nodes.remove(specular)
        texture = tree.nodes.new('ShaderNodeTexImage')
        texture.image = image
        separate = tree.nodes.new('ShaderNodeSeparateColor')
        tree.links.new(texture.outputs['Color'], separate.inputs['Color'])
        tree.links.new(separate.outputs['Green'], shader.inputs['Roughness'])
        tree.links.new(separate.outputs['Blue'], shader.inputs['Metallic'])

        if style == "castaway" and original and normal and normal.image and "body" in material.name.lower():
            sources[material.name] = (original, normal.image, image)

    for link in list(shader.inputs['Alpha'].links):
        tree.links.remove(link)

    if color and "opacity" in material.name.lower():
        tree.links.new(color.outputs['Alpha'], shader.inputs['Alpha'])


def export(path, animations):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_skins=True, export_animations=animations, export_force_sampling=animations, export_optimize_animation_size=False, export_anim_single_armature=True, export_morph=False, export_yup=True, export_apply=False, use_selection=False, export_extras=False, export_cameras=False, export_lights=False)


for character, output, style in characters:
    if only and output != only:
        continue
    reset()
    name = os.path.basename(character)
    root = os.path.join(source_root, "Avatars", character.replace('/', os.sep))
    directory = os.path.join(output_root, "characters", output)
    os.makedirs(directory, exist_ok=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(root, "Export", name + ".fbx"), use_anim=False)
    for obj in list(bpy.data.objects):
        if obj.type == 'EMPTY':
            bpy.data.objects.remove(obj, do_unlink=True)
    sources.clear()
    for material in list(bpy.data.materials):
        if material.use_nodes:
            prepare_material(material, os.path.join(root, "Textures"), directory, style)
    if style == "castaway":
        arm_detail(directory)
    export(os.path.join(directory, output + ".gltf"), False)
    print("CONVERTED character", name, "as", output)

clip_directory = os.path.join(output_root, "animations")
os.makedirs(clip_directory, exist_ok=True)

for folder in ([] if only else sorted(os.listdir(os.path.join(source_root, "Animations")))):
    for file in sorted(os.listdir(os.path.join(source_root, "Animations", folder))):
        if file.endswith(".fbx"):
            reset()
            bpy.ops.import_scene.fbx(filepath=os.path.join(source_root, "Animations", folder, file), use_anim=True)
            for obj in list(bpy.data.objects):
                if obj.type != 'ARMATURE':
                    bpy.data.objects.remove(obj, do_unlink=True)
            armature = next(obj for obj in bpy.data.objects if obj.type == 'ARMATURE')
            if armature.animation_data and armature.animation_data.action:
                start, end = armature.animation_data.action.frame_range
                bpy.context.scene.frame_start = int(start)
                bpy.context.scene.frame_end = int(end)
            export(os.path.join(clip_directory, file.replace(".max.fbx", "") + ".gltf"), True)
            print("CONVERTED clip", file, bpy.context.scene.frame_start, bpy.context.scene.frame_end)
