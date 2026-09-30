import bpy
import json
import math
import os
import numpy
from mathutils import Vector

import flora_kit as kit

cache = {}


def leaf_material(textures, mask):
    material = bpy.data.materials.new("view_leaf")
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    color = kit.image_node(tree, textures["diff"], 'sRGB')
    surface = kit.image_node(tree, textures["arm"], 'Non-Color')
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(surface.outputs['Color'], split.inputs['Color'])
    shade = tree.nodes.new('ShaderNodeMath')
    shade.operation = 'MULTIPLY_ADD'
    shade.inputs[1].default_value = 0.3
    shade.inputs[2].default_value = 0.7
    tree.links.new(split.outputs['Red'], shade.inputs[0])
    tinted = tree.nodes.new('ShaderNodeVectorMath')
    tinted.operation = 'SCALE'
    tree.links.new(color.outputs['Color'], tinted.inputs[0])
    tree.links.new(shade.outputs['Value'], tinted.inputs['Scale'])
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    sign = tree.nodes.new('ShaderNodeMath')
    sign.operation = 'MULTIPLY_ADD'
    sign.inputs[1].default_value = -2.0
    sign.inputs[2].default_value = 1.0
    tree.links.new(geometry.outputs['Backfacing'], sign.inputs[0])
    normal = tree.nodes.new('ShaderNodeVectorMath')
    normal.operation = 'SCALE'
    tree.links.new(geometry.outputs['Normal'], normal.inputs[0])
    tree.links.new(sign.outputs['Value'], normal.inputs['Scale'])
    diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')
    tree.links.new(tinted.outputs['Vector'], diffuse.inputs['Color'])
    tree.links.new(normal.outputs['Vector'], diffuse.inputs['Normal'])
    through = tree.nodes.new('ShaderNodeVectorMath')
    through.operation = 'MULTIPLY'
    through.inputs[1].default_value = (0.9 * 0.45, 1.0 * 0.45, 0.55 * 0.45)
    tree.links.new(tinted.outputs['Vector'], through.inputs[0])
    translucent = tree.nodes.new('ShaderNodeBsdfTranslucent')
    tree.links.new(through.outputs['Vector'], translucent.inputs['Color'])
    tree.links.new(normal.outputs['Vector'], translucent.inputs['Normal'])
    gloss = tree.nodes.new('ShaderNodeBsdfGlossy')
    gloss.inputs['Color'].default_value = (0.012, 0.012, 0.012, 1.0)
    tree.links.new(split.outputs['Green'], gloss.inputs['Roughness'])
    tree.links.new(normal.outputs['Vector'], gloss.inputs['Normal'])
    first = tree.nodes.new('ShaderNodeAddShader')
    tree.links.new(diffuse.outputs['BSDF'], first.inputs[0])
    tree.links.new(translucent.outputs['BSDF'], first.inputs[1])
    second = tree.nodes.new('ShaderNodeAddShader')
    tree.links.new(first.outputs['Shader'], second.inputs[0])
    tree.links.new(gloss.outputs['BSDF'], second.inputs[1])
    alpha = kit.image_node(tree, mask, 'Non-Color')
    alpha.interpolation = 'Closest'
    cut = tree.nodes.new('ShaderNodeMath')
    cut.operation = 'GREATER_THAN'
    cut.inputs[1].default_value = 0.5
    tree.links.new(alpha.outputs['Color'], cut.inputs[0])
    hole = tree.nodes.new('ShaderNodeBsdfTransparent')
    blend = tree.nodes.new('ShaderNodeMixShader')
    tree.links.new(cut.outputs['Value'], blend.inputs['Fac'])
    tree.links.new(hole.outputs['BSDF'], blend.inputs[1])
    tree.links.new(second.outputs['Shader'], blend.inputs[2])
    tree.links.new(blend.outputs['Shader'], output.inputs['Surface'])
    material.surface_render_method = 'DITHERED'
    material.use_transparent_shadow = True
    material.use_backface_culling = False
    material.use_backface_culling_shadow = False
    return material


def solid_material(textures):
    material = bpy.data.materials.new("view_solid")
    material.use_nodes = True
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = kit.image_node(tree, textures["diff"], 'sRGB')
    surface = kit.image_node(tree, textures["arm"], 'Non-Color')
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(surface.outputs['Color'], split.inputs['Color'])
    shade = tree.nodes.new('ShaderNodeMath')
    shade.operation = 'MULTIPLY_ADD'
    shade.inputs[1].default_value = 0.3
    shade.inputs[2].default_value = 0.7
    tree.links.new(split.outputs['Red'], shade.inputs[0])
    tinted = tree.nodes.new('ShaderNodeVectorMath')
    tinted.operation = 'SCALE'
    tree.links.new(color.outputs['Color'], tinted.inputs[0])
    tree.links.new(shade.outputs['Value'], tinted.inputs['Scale'])
    tree.links.new(tinted.outputs['Vector'], shader.inputs['Base Color'])
    tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
    normal_image = kit.image_node(tree, textures["nor_gl"], 'Non-Color')
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(normal_image.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    shader.inputs['Metallic'].default_value = 0.0
    material.use_backface_culling = True
    return material


def impostor_material(textures, mask, frame, blend_amount, right, facing):
    material = bpy.data.materials.new("view_impostor")
    material.use_nodes = True
    tree = material.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    coordinate = tree.nodes.new('ShaderNodeUVMap')
    samples = []
    for index in (frame % kit.impostor_frames, (frame + 1) % kit.impostor_frames):
        mapping = tree.nodes.new('ShaderNodeMapping')
        mapping.vector_type = 'POINT'
        mapping.inputs['Scale'].default_value = (1.0 / kit.impostor_columns, 0.5, 1.0)
        mapping.inputs['Location'].default_value = ((index % kit.impostor_columns) / kit.impostor_columns, 0.5 - 0.5 * (index // kit.impostor_columns), 0.0)
        tree.links.new(coordinate.outputs['UV'], mapping.inputs['Vector'])
        entry = {}
        for key, path, space in (("diff", textures["diff"], 'sRGB'), ("nor", textures["nor_gl"], 'Non-Color'), ("arm", textures["arm"], 'Non-Color'), ("alpha", mask, 'Non-Color')):
            node = kit.image_node(tree, path, space)
            node.extension = 'EXTEND'
            node.interpolation = 'Closest' if key == "alpha" else 'Linear'
            tree.links.new(mapping.outputs['Vector'], node.inputs['Vector'])
            entry[key] = node
        samples.append(entry)
    mixed = {}
    for key in ("diff", "nor", "arm", "alpha"):
        mixer = tree.nodes.new('ShaderNodeMix')
        mixer.data_type = 'RGBA'
        mixer.inputs[0].default_value = blend_amount
        tree.links.new(samples[0][key].outputs['Color'], mixer.inputs[6])
        tree.links.new(samples[1][key].outputs['Color'], mixer.inputs[7])
        mixed[key] = mixer.outputs[2]
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(mixed["nor"], split.inputs['Color'])
    parts = []
    for channel in ('Red', 'Green'):
        expand = tree.nodes.new('ShaderNodeMath')
        expand.operation = 'MULTIPLY_ADD'
        expand.inputs[1].default_value = 2.0
        expand.inputs[2].default_value = -1.0
        tree.links.new(split.outputs[channel], expand.inputs[0])
        parts.append(expand)
    squares = tree.nodes.new('ShaderNodeMath')
    squares.operation = 'MULTIPLY'
    tree.links.new(parts[0].outputs['Value'], squares.inputs[0])
    tree.links.new(parts[0].outputs['Value'], squares.inputs[1])
    squares_y = tree.nodes.new('ShaderNodeMath')
    squares_y.operation = 'MULTIPLY'
    tree.links.new(parts[1].outputs['Value'], squares_y.inputs[0])
    tree.links.new(parts[1].outputs['Value'], squares_y.inputs[1])
    total = tree.nodes.new('ShaderNodeMath')
    total.operation = 'ADD'
    tree.links.new(squares.outputs['Value'], total.inputs[0])
    tree.links.new(squares_y.outputs['Value'], total.inputs[1])
    rest = tree.nodes.new('ShaderNodeMath')
    rest.operation = 'SUBTRACT'
    rest.use_clamp = True
    rest.inputs[0].default_value = 1.0
    tree.links.new(total.outputs['Value'], rest.inputs[1])
    depth = tree.nodes.new('ShaderNodeMath')
    depth.operation = 'SQRT'
    tree.links.new(rest.outputs['Value'], depth.inputs[0])
    accumulated = None
    for source, axis in ((parts[0].outputs['Value'], right), (parts[1].outputs['Value'], Vector((0.0, 0.0, 1.0))), (depth.outputs['Value'], facing)):
        scaled = tree.nodes.new('ShaderNodeVectorMath')
        scaled.operation = 'SCALE'
        scaled.inputs[0].default_value = axis
        tree.links.new(source, scaled.inputs['Scale'])
        if accumulated is None:
            accumulated = scaled.outputs['Vector']
        else:
            adder = tree.nodes.new('ShaderNodeVectorMath')
            adder.operation = 'ADD'
            tree.links.new(accumulated, adder.inputs[0])
            tree.links.new(scaled.outputs['Vector'], adder.inputs[1])
            accumulated = adder.outputs['Vector']
    surface = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(mixed["arm"], surface.inputs['Color'])
    shade = tree.nodes.new('ShaderNodeMath')
    shade.operation = 'MULTIPLY_ADD'
    shade.inputs[1].default_value = 0.3
    shade.inputs[2].default_value = 0.7
    tree.links.new(surface.outputs['Red'], shade.inputs[0])
    tinted = tree.nodes.new('ShaderNodeVectorMath')
    tinted.operation = 'SCALE'
    tree.links.new(mixed["diff"], tinted.inputs[0])
    tree.links.new(shade.outputs['Value'], tinted.inputs['Scale'])
    diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')
    tree.links.new(tinted.outputs['Vector'], diffuse.inputs['Color'])
    tree.links.new(accumulated, diffuse.inputs['Normal'])
    through = tree.nodes.new('ShaderNodeVectorMath')
    through.operation = 'MULTIPLY'
    through.inputs[1].default_value = (0.9 * 0.45, 1.0 * 0.45, 0.55 * 0.45)
    tree.links.new(tinted.outputs['Vector'], through.inputs[0])
    translucent = tree.nodes.new('ShaderNodeBsdfTranslucent')
    tree.links.new(through.outputs['Vector'], translucent.inputs['Color'])
    tree.links.new(accumulated, translucent.inputs['Normal'])
    combined = tree.nodes.new('ShaderNodeAddShader')
    tree.links.new(diffuse.outputs['BSDF'], combined.inputs[0])
    tree.links.new(translucent.outputs['BSDF'], combined.inputs[1])
    cut = tree.nodes.new('ShaderNodeMath')
    cut.operation = 'GREATER_THAN'
    cut.inputs[1].default_value = 0.5
    tree.links.new(mixed["alpha"], cut.inputs[0])
    hole = tree.nodes.new('ShaderNodeBsdfTransparent')
    blend = tree.nodes.new('ShaderNodeMixShader')
    tree.links.new(cut.outputs['Value'], blend.inputs['Fac'])
    tree.links.new(hole.outputs['BSDF'], blend.inputs[1])
    tree.links.new(combined.outputs['Shader'], blend.inputs[2])
    tree.links.new(blend.outputs['Shader'], output.inputs['Surface'])
    material.surface_render_method = 'DITHERED'
    material.use_transparent_shadow = True
    material.use_backface_culling = False
    return material


def read_document(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def material_files(document, directory, index):
    material = document["materials"][index]

    def resolve(reference):
        image = document["images"][document["textures"][reference["index"]]["source"]]
        return os.path.normpath(os.path.join(directory, image["uri"]))

    textures = {"diff": resolve(material["pbrMetallicRoughness"]["baseColorTexture"]), "nor_gl": resolve(material["normalTexture"]), "arm": resolve(material["pbrMetallicRoughness"]["metallicRoughnessTexture"])}
    return textures, material.get("alphaMode") == "MASK"


def load_model(species, name, location, yaw=0.0, root=None):
    directory = os.path.join(root, name) if root else kit.model_directory(species, name)
    path = os.path.join(directory, name + ".gltf")
    document = read_document(path)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    created = [obj for obj in bpy.data.objects if obj not in before]
    lookup = {material["name"]: index for index, material in enumerate(document["materials"])}
    for obj in created:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            base = slot.material.name.split(".")[0]
            textures, cut = material_files(document, directory, lookup[base])
            key = (textures["diff"], cut)
            if key not in cache:
                cache[key] = leaf_material(textures, textures["diff"].replace("_diff_", "_alpha_")) if cut else solid_material(textures)
            slot.material = cache[key]
    roots = [obj for obj in created if obj.parent is None]
    for obj in roots:
        obj.location = obj.location + location
        obj.rotation_mode = 'XYZ'
        obj.rotation_euler = (obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z + yaw)
    return [obj for obj in created if obj.type == 'MESH']


def load_impostor(species, name, location, camera_location, root=None):
    directory = os.path.join(root, name) if root else kit.model_directory(species, name)
    document = read_document(os.path.join(directory, name + ".gltf"))
    textures, cut = material_files(document, directory, 0)
    low = document["accessors"][0]["min"]
    high = document["accessors"][0]["max"]
    toward = Vector((camera_location.x - location.x, camera_location.y - location.y, 0.0)).normalized()
    right = Vector((-toward.y, toward.x, 0.0))
    turn = (math.atan2(toward.x, toward.y) / math.tau + 1.0) % 1.0 * kit.impostor_frames
    frame = int(math.floor(turn))
    mesh = bpy.data.meshes.new(name)
    corners = [location + right * low[0] + Vector((0.0, 0.0, low[1])), location + right * high[0] + Vector((0.0, 0.0, low[1])), location + right * high[0] + Vector((0.0, 0.0, high[1])), location + right * low[0] + Vector((0.0, 0.0, high[1]))]
    mesh.from_pydata([tuple(corner) for corner in corners], [], [(0, 1, 2, 3)])
    layer = mesh.uv_layers.new(name="UVMap")
    for loop, uv in zip(mesh.loops, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
        layer.data[loop.index].uv = uv
    mesh.materials.append(impostor_material(textures, textures["diff"].replace("_diff_", "_alpha_"), frame, turn - frame, right, toward))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return [obj]


def stage(scene, azimuth=2.2, elevation=0.78, sun_strength=4.0, sky_strength=2.4, ground=(0.13, 0.125, 0.115)):
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    tree = world.node_tree
    background = tree.nodes["Background"]
    sky = tree.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'HOSEK_WILKIE'
    sky.sun_direction = Vector((math.cos(azimuth) * math.cos(elevation), math.sin(azimuth) * math.cos(elevation), math.sin(elevation)))
    sky.turbidity = 2.6
    sky.ground_albedo = 0.3
    tree.links.new(sky.outputs['Color'], background.inputs['Color'])
    background.inputs['Strength'].default_value = sky_strength
    scene.world = world
    data = bpy.data.lights.new("sun", 'SUN')
    data.energy = sun_strength
    data.angle = math.radians(1.2)
    data.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new("sun", data)
    sun.rotation_euler = Vector((math.cos(azimuth) * math.cos(elevation), math.sin(azimuth) * math.cos(elevation), math.sin(elevation))).to_track_quat('Z', 'Y').to_euler()
    scene.collection.objects.link(sun)
    mesh = bpy.data.meshes.new("ground")
    mesh.from_pydata([(-400.0, -400.0, 0.0), (400.0, -400.0, 0.0), (400.0, 400.0, 0.0), (-400.0, 400.0, 0.0)], [], [(0, 1, 2, 3)])
    material = bpy.data.materials.new("ground")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (ground[0], ground[1], ground[2], 1.0)
    shader.inputs['Roughness'].default_value = 0.9
    mesh.materials.append(material)
    floor = bpy.data.objects.new("ground", mesh)
    scene.collection.objects.link(floor)
    return sun, floor


def configure(scene, resolution, samples=48, engine='BLENDER_EEVEE_NEXT'):
    scene.render.engine = engine
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    if engine == 'CYCLES':
        kit.accelerate(scene)
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.transparent_max_bounces = 48
    else:
        scene.eevee.taa_render_samples = samples
        scene.eevee.use_shadows = True
        scene.eevee.shadow_ray_count = 2
        scene.eevee.shadow_step_count = 8
        scene.eevee.use_raytracing = True
        scene.eevee.ray_tracing_method = 'SCREEN'
        scene.eevee.fast_gi_method = 'AMBIENT_OCCLUSION_ONLY'
        scene.eevee.fast_gi_distance = 3.0
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 2.0


def shoot(scene, path, target, direction, distance, lens=50.0, orthographic=0.0, shift=(0.0, 0.0)):
    data = bpy.data.cameras.new("view")
    data.lens = lens
    data.clip_start = 0.05
    data.clip_end = 3000.0
    data.shift_x = shift[0]
    data.shift_y = shift[1]
    if orthographic:
        data.type = 'ORTHO'
        data.ortho_scale = orthographic
    camera = bpy.data.objects.new("view", data)
    scene.collection.objects.link(camera)
    camera.location = target + direction.normalized() * distance
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = camera
    scene.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)
    print("VIEW", path)


def extent(objects):
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            low = Vector((min(low.x, point.x), min(low.y, point.y), min(low.z, point.z)))
            high = Vector((max(high.x, point.x), max(high.y, point.y), max(high.z, point.z)))
    return low, high


def closeups(species, name, prefix, shots, resolution=(1280, 800), root=None, engine='BLENDER_EEVEE_NEXT', exposure=0.0):
    kit.reset()
    cache.clear()
    scene = bpy.context.scene
    configure(scene, resolution, 48, engine)
    scene.view_settings.exposure = exposure
    stage(scene, -2.2, 0.85)
    objects = load_model(species, name, Vector((0.0, 0.0, 0.0)), 0.0, root)
    kit.human(scene, Vector((1.4, -0.6, 0.0)), Vector((0.0, -1.0, 0.0)))
    for tag, eye, target, lens in shots:
        eye = Vector(eye)
        target = Vector(target)
        shoot(scene, prefix + "_" + tag + ".png", target, eye - target, (eye - target).length, lens)


def strip(species, variant, path, kinds, resolution=(1800, 640), direction=(0.0, -1.0, 0.12), gap=1.0):
    kit.reset()
    cache.clear()
    scene = bpy.context.scene
    configure(scene, resolution, 48)
    stage(scene, math.atan2(direction[1], direction[0]) - 0.75, 0.82)
    view = Vector(direction).normalized()
    across = Vector((-view.y, view.x, 0.0)).normalized()
    cursor = 0.0
    tallest = 1.0
    for kind in reversed(kinds):
        name = kit.model_name(species, variant, "" if kind == "near" else "_" + kind)
        if kind == "impostor":
            document = read_document(os.path.join(kit.model_directory(species, name), name + ".gltf"))
            span = document["accessors"][0]["max"][0]
            cursor += span
            load_impostor(species, name, -across * cursor, -across * cursor + Vector((view.x, view.y, 0.0)) * 120.0)
            tallest = max(tallest, document["accessors"][0]["max"][1])
        else:
            objects = load_model(species, name, Vector((0.0, 0.0, 0.0)))
            bpy.context.view_layer.update()
            low, high = extent(objects)
            span = max(abs(Vector((x, y, 0.0)).dot(across)) for x in (low.x, high.x) for y in (low.y, high.y))
            cursor += span
            for obj in objects:
                if obj.parent is None:
                    obj.location = obj.location - across * cursor
            tallest = max(tallest, high.z)
        cursor += span + gap
    kit.human(scene, -across * (cursor + 0.2) + view * 0.3, view)
    cursor += 0.8
    width = cursor + 0.6
    tall = max(tallest, 1.9) + 0.6
    scene.render.resolution_y = int(kit.clamp(resolution[0] * tall * 1.3 / width, 260, resolution[1]))
    aspect = resolution[0] / scene.render.resolution_y
    shoot(scene, path, -across * (cursor * 0.5 - 0.1) + Vector((0.0, 0.0, tall * 0.5 - 0.15)), view, 120.0, 50.0, max(width, tall * aspect) * 1.03)


def stack(paths, path):
    images = [kit.load_pixels(entry)[:, :, :3] for entry in paths]
    kit.write_png(path, numpy.concatenate(list(reversed(images)), axis=0))


def distances(species, variant, prefix, spans=(30.0, 150.0), kinds=("near", "far", "impostor")):
    results = []
    for span in spans:
        kit.reset()
        cache.clear()
        scene = bpy.context.scene
        stage(scene, -2.2, 0.85)
        widest = 1.0
        tallest = 1.0
        loaded = []
        for index, kind in enumerate(kinds):
            name = kit.model_name(species, variant, "" if kind == "near" else "_" + kind)
            if kind == "impostor":
                document = read_document(os.path.join(kit.model_directory(species, name), name + ".gltf"))
                widest = max(widest, document["accessors"][0]["max"][0])
                tallest = max(tallest, document["accessors"][0]["max"][1])
                loaded.append((kind, name, None))
            else:
                objects = load_model(species, name, Vector((0.0, 0.0, 0.0)))
                bpy.context.view_layer.update()
                low, high = extent(objects)
                widest = max(widest, abs(low.x), abs(high.x), abs(low.y), abs(high.y))
                tallest = max(tallest, high.z)
                loaded.append((kind, name, objects))
        spacing = widest * 2.0 + 1.5
        eye = Vector((0.0, -span, 1.7))
        for index, (kind, name, objects) in enumerate(loaded):
            offset = Vector(((index - (len(loaded) - 1) * 0.5) * spacing, 0.0, 0.0))
            if objects is None:
                load_impostor(species, name, offset, eye)
            else:
                for obj in objects:
                    if obj.parent is None:
                        obj.location = obj.location + offset
        focal = 960.0
        width = int(min(1920, max(240, spacing * len(loaded) / span * focal * 1.08)))
        height = int(min(1080, max(140, (tallest + 3.0) / span * focal * 1.25)))
        configure(scene, (width, height), 48)
        path = prefix + "_d%d.png" % int(span)
        shoot(scene, path, Vector((0.0, 0.0, tallest * 0.5)), eye - Vector((0.0, 0.0, tallest * 0.5)), (eye - Vector((0.0, 0.0, tallest * 0.5))).length, focal * 36.0 / width)
        if width < 900:
            factor = int(math.ceil(1400.0 / width))
            pixels = kit.load_pixels(path)[:, :, :3]
            kit.write_png(path, numpy.repeat(numpy.repeat(pixels, factor, axis=0), factor, axis=1))
        results.append(path)
    return results


def lineup(species, names, path, resolution=(1800, 900), direction=(0.0, -1.0, 0.12), gap=1.5, root=None, yaw=0.0, engine='BLENDER_EEVEE_NEXT', close=None):
    kit.reset()
    cache.clear()
    scene = bpy.context.scene
    configure(scene, resolution, 48, engine)
    stage(scene, math.atan2(direction[1], direction[0]) - 0.75, 0.82)
    cursor = 0.0
    everything = []
    view = Vector(direction).normalized()
    across = Vector((-view.y, view.x, 0.0)).normalized()
    for name in reversed(names):
        objects = load_model(species, name, Vector((0.0, 0.0, 0.0)), yaw, root)
        bpy.context.view_layer.update()
        low, high = extent(objects)
        span = max(abs((Vector((low.x, low.y, 0.0))).dot(across)), abs((Vector((high.x, high.y, 0.0))).dot(across)), abs(Vector((low.x, high.y, 0.0)).dot(across)), abs(Vector((high.x, low.y, 0.0)).dot(across)))
        cursor += span
        for obj in objects:
            if obj.parent is None:
                obj.location = obj.location - across * cursor
        kit.human(scene, -across * (cursor + span + 0.45) + view * 0.3, view)
        cursor += span + gap + 0.9
        everything.extend(objects)
    bpy.context.view_layer.update()
    low, high = extent(everything)
    low.z = 0.0
    center = (low + high) * 0.5
    width = cursor + 1.0
    tall = max(high.z, 1.9) + 0.5
    scene.render.resolution_y = int(kit.clamp(resolution[0] * tall * 1.25 / width, 360, resolution[1]))
    aspect = resolution[0] / scene.render.resolution_y
    scale = max(width, tall * aspect) * 1.04
    target = -across * (cursor * 0.5 - 0.2) + Vector((0.0, 0.0, tall * 0.5 - 0.1))
    shoot(scene, path, target, view, 120.0, 50.0, scale)
    if close:
        for index, (file_path, anchor, offset, lens) in enumerate(close):
            shoot(scene, file_path, anchor, offset, offset.length, lens)
