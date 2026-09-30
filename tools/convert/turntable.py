import bpy
import os
import sys
from mathutils import Vector

directions = {
    "side": (Vector((0.0, -1.0, 0.06)), True, 50.0, 1.0),
    "other": (Vector((0.0, 1.0, 0.06)), True, 50.0, 1.0),
    "three": (Vector((0.75, -0.8, 0.45)), False, 55.0, 1.0),
    "wide": (Vector((0.7, -0.85, 0.55)), False, 32.0, 1.0),
    "back": (Vector((-0.85, -0.6, 0.35)), False, 55.0, 1.0),
    "top": (Vector((0.05, -0.25, 1.0)), True, 50.0, 1.0),
    "close": (Vector((-0.35, -0.9, 0.3)), False, 85.0, 0.5),
    "front": (Vector((1.0, -0.35, 0.25)), False, 70.0, 0.7),
    "under": (Vector((0.2, -0.7, -0.55)), False, 60.0, 0.8),
}


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
            print("CYCLES DEVICE", kind, [device.name for device in devices])
            return kind
    scene.cycles.device = 'CPU'
    print("CYCLES DEVICE CPU")
    return 'CPU'


def bounds(objects):
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            low = Vector((min(low.x, point.x), min(low.y, point.y), min(low.z, point.z)))
            high = Vector((max(high.x, point.x), max(high.y, point.y), max(high.z, point.z)))
    return low, high


def studio(scene, hdri_path, scale=1.0):
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    tree = world.node_tree
    background = tree.nodes["Background"]
    environment = tree.nodes.new('ShaderNodeTexEnvironment')
    environment.image = bpy.data.images.load(hdri_path, check_existing=True)
    tree.links.new(environment.outputs['Color'], background.inputs['Color'])
    background.inputs['Strength'].default_value = 0.55
    scene.world = world
    created = []
    for name, location, energy, size, color in (("key", (-0.9, -1.2, 1.3), 90.0, 0.9, (1.0, 0.95, 0.88)), ("rim", (1.1, 0.9, 0.8), 70.0, 0.6, (0.85, 0.92, 1.0)), ("fill", (0.6, -1.4, -0.2), 18.0, 1.2, (1.0, 1.0, 1.0))):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy = energy * scale * scale
        data.size = size * scale
        data.color = color
        light = bpy.data.objects.new(name, data)
        light.location = Vector(location) * scale
        light.rotation_euler = (Vector((0.0, 0.0, 0.0)) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(light)
        created.append(light)
    floor_data = bpy.data.meshes.new("floor")
    floor_data.from_pydata([(-6.0, -6.0, 0.0), (6.0, -6.0, 0.0), (6.0, 6.0, 0.0), (-6.0, 6.0, 0.0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("floor", floor_data)
    material = bpy.data.materials.new("floor")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (0.045, 0.045, 0.047, 1.0)
    shader.inputs['Roughness'].default_value = 0.55
    floor_data.materials.append(material)
    scene.collection.objects.link(floor)
    created.append(floor)
    return floor, created


def render_views(objects, output_root, name, views, samples, hdri_path, resolution=(1600, 900)):
    scene = bpy.context.scene
    low, high = bounds(objects)
    offset = Vector(((low.x + high.x) * 0.5, (low.y + high.y) * 0.5, low.z))
    for obj in objects:
        if obj.parent is None:
            obj.location -= offset
    bpy.context.view_layer.update()
    low, high = bounds(objects)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    accelerate(scene)
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    size = high - low
    floor, created = studio(scene, hdri_path, max(max(size.x, size.y, size.z) / 0.7, 1.0))
    floor.location.z = low.z - 0.002
    target = (low + high) * 0.5
    reach = max(size.x, size.y, size.z) * 1.15
    os.makedirs(output_root, exist_ok=True)
    for view in views:
        direction, orthographic, lens, zoom = directions[view]
        focus = target if view != "close" else Vector((low.x + size.x * 0.32, target.y, target.z + size.z * 0.1))
        data = bpy.data.cameras.new("view")
        data.lens = lens
        data.clip_start = 0.005
        if orthographic:
            data.type = 'ORTHO'
            data.ortho_scale = reach * 1.08 * zoom
        camera = bpy.data.objects.new("view", data)
        scene.collection.objects.link(camera)
        camera.location = focus + direction.normalized() * reach * zoom * (1.0 if orthographic else 1.35)
        camera.rotation_euler = (focus - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.camera = camera
        scene.render.filepath = os.path.join(output_root, name + "_" + view + ".png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(camera)
        print("RENDERED", name, view)
    for obj in created:
        bpy.data.objects.remove(obj)
    for obj in objects:
        if obj.parent is None:
            obj.location += offset
    bpy.context.view_layer.update()


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=arguments[0])
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    render_views(meshes, arguments[1], os.path.splitext(os.path.basename(arguments[0]))[0], arguments[3].split(",") if len(arguments) > 3 else ["side", "three", "close"], int(arguments[4]) if len(arguments) > 4 else 64, arguments[2])
