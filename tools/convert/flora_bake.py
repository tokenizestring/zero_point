import bpy
import math
import os
import numpy
from mathutils import Vector

import flora_kit as kit
import flora_wood as wood


def impostor_textures(species, variant):
    name = kit.model_name(species, variant, "_impostor")
    directory = kit.model_directory(species, name)
    return {kind: os.path.join(directory, "%s_%s_1k.png" % (name, kind)) for kind in ("diff", "alpha", "nor_gl", "arm")}


def impostor(species, variant, objects, scratch, solid=(0.1, 0.56)):
    name = kit.model_name(species, variant, "_impostor")
    radius, low, high = wood.bounds(objects)
    width = radius * 2.0 * 1.05
    tall = (high - low) * 1.03
    bottom = (low + high) * 0.5 - tall * 0.5
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    kit.accelerate(scene)
    ratio = 2.0 * width / tall
    scene.render.resolution_x = kit.impostor_cell[0]
    scene.render.resolution_y = kit.impostor_cell[1]
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = ratio if ratio >= 1.0 else 1.0
    scene.render.pixel_aspect_y = 1.0 if ratio >= 1.0 else 1.0 / ratio
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.cycles.use_denoising = False
    scene.cycles.transparent_max_bounces = 96
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    world = bpy.data.worlds.new("impostor")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    scene.world = world
    sets = []
    for obj in objects:
        files = __import__("json").loads(obj.data.materials[0]["flora_textures"])
        cut = files["alpha"] if obj.data.materials[0]["flora_cut"] else None
        sets.append({"albedo": kit.pass_material("albedo_" + obj.name, "albedo", files["diff"], cut), "normal": kit.pass_material("normal_" + obj.name, "normal", None, cut), "occlusion": kit.pass_material("occlusion_" + obj.name, "occlusion", None, cut)})
    camera_data = bpy.data.cameras.new("impostor")
    camera_data.type = 'ORTHO'
    camera_data.sensor_fit = 'HORIZONTAL'
    camera_data.ortho_scale = width
    camera_data.clip_start = 0.1
    camera_data.clip_end = 600.0
    camera = bpy.data.objects.new("impostor", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    size = (kit.impostor_cell[1] * 2, kit.impostor_cell[0] * kit.impostor_columns)
    color_atlas = numpy.zeros((size[0], size[1], 3), dtype=numpy.float32)
    normal_atlas = numpy.zeros((size[0], size[1], 3), dtype=numpy.float32)
    occlusion_atlas = numpy.ones((size[0], size[1]), dtype=numpy.float32)
    alpha_atlas = numpy.zeros((size[0], size[1]), dtype=numpy.float32)
    center = Vector((0.0, 0.0, bottom + tall * 0.5))
    frame_path = os.path.join(scratch, "impostor_frame.png")
    for frame in range(kit.impostor_frames):
        angle = math.tau * frame / kit.impostor_frames
        toward = Vector((math.sin(angle), math.cos(angle), 0.0))
        right = Vector((-math.cos(angle), math.sin(angle), 0.0))
        up = Vector((0.0, 0.0, 1.0))
        camera.location = center + toward * 200.0
        camera.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
        results = {}
        for kind, transform, samples, strength in (("albedo", 'Standard', 24, 0.0), ("normal", 'Raw', 24, 0.0), ("occlusion", 'Raw', 128, 1.0)):
            for obj, materials in zip(objects, sets):
                material = materials[kind]
                for axis_name, axis in (("axis_X", right), ("axis_Y", up), ("axis_Z", toward)):
                    if axis_name in material.node_tree.nodes:
                        material.node_tree.nodes[axis_name].inputs[1].default_value = axis
                obj.data.materials.clear()
                obj.data.materials.append(material)
            background.inputs['Strength'].default_value = strength
            scene.view_settings.view_transform = transform
            scene.cycles.samples = samples
            scene.render.filepath = frame_path
            bpy.ops.render.render(write_still=True)
            results[kind] = kit.load_pixels(frame_path)
        alpha = results["albedo"][:, :, 3]
        column = frame % kit.impostor_columns
        row = 1 - frame // kit.impostor_columns
        rows = slice(row * kit.impostor_cell[1], (row + 1) * kit.impostor_cell[1])
        columns = slice(column * kit.impostor_cell[0], (column + 1) * kit.impostor_cell[0])
        color_atlas[rows, columns] = kit.flood(results["albedo"][:, :, :3], alpha)
        normal_atlas[rows, columns] = kit.flood(results["normal"][:, :, :3], alpha)
        occlusion_atlas[rows, columns] = kit.flood(results["occlusion"][:, :, :1], alpha)[:, :, 0]
        alpha_atlas[rows, columns] = alpha
        print("FRAME", name, frame)
    os.remove(frame_path)
    shade = numpy.clip(occlusion_atlas, 0.0, 1.0)
    alpha_atlas = kit.step(alpha_atlas, solid[0], solid[1])
    normal = normal_atlas * 2.0 - 1.0
    normal[:, :, 2] = numpy.maximum(normal[:, :, 2], 0.0)
    normal[:, :, :2] *= 0.7
    normal[:, :, 2] = numpy.sqrt(numpy.clip(1.0 - (normal[:, :, :2] ** 2).sum(axis=2), 0.0, 1.0))
    normal = normal / numpy.maximum(numpy.linalg.norm(normal, axis=2, keepdims=True), 1e-6)
    textures = impostor_textures(species, variant)
    color_atlas = kit.to_srgb(kit.to_linear(color_atlas) * (0.78 + 0.22 * shade[:, :, None]))
    kit.write_png(textures["diff"], numpy.concatenate([color_atlas, alpha_atlas[:, :, None]], axis=2))
    kit.write_png(textures["alpha"], numpy.repeat(alpha_atlas[:, :, None], 3, axis=2))
    kit.write_png(textures["nor_gl"], normal * 0.5 + 0.5)
    kit.write_png(textures["arm"], numpy.stack([0.3 + 0.7 * shade, numpy.full_like(shade, 0.78), numpy.zeros_like(shade)], axis=2))
    cut = (alpha_atlas > 0.5).astype(numpy.float32)[:, :, None]
    kit.write_png(os.path.join(scratch, name + "_preview.png"), color_atlas * shade[:, :, None] * cut + 0.2 * (1.0 - cut))
    kit.write_quad(species, name, textures, width, bottom, bottom + tall)
    print("IMPOSTOR", name, round(width, 3), round(bottom, 3), round(bottom + tall, 3), float(alpha_atlas.mean()))
