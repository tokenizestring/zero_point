import bpy
import bmesh
import json
import math
import os
import pickle
import shutil
import numpy
from mathutils import Vector
import fauna_hoofed_field as fields
import fauna_hoofed_cage as cages
import fauna_hoofed_motion as motion
import fauna_hoofed_paint as paint
import fauna_hoofed_parts as parts
import fauna_hoofed_render as render
import fauna_hoofed_species as species

island_scales = {"head": 1.6, "nose": 2.0, "chin": 1.7, "eyeball": 3.2, "ear_l": 1.25, "ear_r": 1.25, "mouth": 0.6, "nostril": 1.0, "hoof": 1.1, "hoof_sole": 0.5, "hoof_top": 0.25, "antler": 0.75}


def assemble(blueprint):
    f = blueprint["field"]
    b = cages.build_skin(blueprint)
    skin = cages.finish(b)
    skin = cages.relax(f, skin, blueprint["cage"]["skin"])
    skin["faces"] = render.oriented(skin["points"], skin["faces"])
    cages.audit(f, skin, blueprint["cage"]["skin"])
    pieces = species.pieces(blueprint["name"], blueprint)
    for piece in pieces:
        if piece["part"] not in ("eyeball", "lock"):
            piece["faces"] = render.oriented(piece["points"], piece["faces"])
    model = parts.combine(skin, pieces)
    model["meta"] = b.meta
    model["mapping"] = skin["mapping"]
    model["points"] = model["points"] * blueprint["scale"]
    model["scale"] = blueprint["scale"]
    return model


def select_only(obj):
    for other in bpy.context.scene.objects:
        other.select_set(other is obj)
    bpy.context.view_layer.objects.active = obj


def loop_faces(mesh):
    sizes = numpy.empty(len(mesh.polygons), dtype=numpy.int32)
    mesh.polygons.foreach_get("loop_total", sizes)
    return numpy.repeat(numpy.arange(len(sizes)), sizes)


def unwrap(model, scales=island_scales, margin=0.0035):
    obj = render.mesh_object("unwrap", model["points"], model["faces"])
    mesh = obj.data
    mesh.uv_layers.new(name="uv")
    tags = model["tags"]
    cut = set((min(a, c), max(a, c)) for a, c in model["cuts"])
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for edge in bm.edges:
        key = (min(edge.verts[0].index, edge.verts[1].index), max(edge.verts[0].index, edge.verts[1].index))
        linked = edge.link_faces
        edge.seam = key in cut or len(linked) != 2 or tags[linked[0].index] != tags[linked[1].index]
    bm.to_mesh(mesh)
    bm.free()
    select_only(obj)
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data
    layer = mesh.uv_layers[0]
    uv = numpy.empty(len(mesh.loops) * 2, dtype=numpy.float32)
    layer.uv.foreach_get("vector", uv)
    uv = uv.reshape(-1, 2).astype(numpy.float64)
    owner = loop_faces(mesh)
    factor = numpy.array([scales.get(tag, 1.0) for tag in tags])[owner]
    names = sorted(set(tags))
    code = numpy.array([names.index(tag) for tag in tags])[owner]
    for index in range(len(names)):
        chosen = code == index
        center = uv[chosen].mean(axis=0)
        uv[chosen] = center[None, :] + (uv[chosen] - center[None, :]) * factor[chosen][:, None]
    layer.uv.foreach_set("vector", uv.astype(numpy.float32).ravel())
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data
    packed = numpy.empty(len(mesh.loops) * 2, dtype=numpy.float32)
    mesh.uv_layers[0].uv.foreach_get("vector", packed)
    model["uv"] = packed.reshape(-1, 2).astype(numpy.float64)
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh)
    return model


def layout_image(model, path, size=1024):
    image = numpy.zeros((size, size, 4), dtype=numpy.float32)
    image[:, :, 3] = 1.0
    image[:, :, :3] = 0.08
    uv = model["uv"]
    names = sorted(set(model["tags"]))
    start = 0
    rng = numpy.random.default_rng(3)
    colors = {name: 0.35 + 0.65 * rng.random(3) for name in names}
    steps = numpy.linspace(0.0, 1.0, 48)
    for face, tag in zip(model["faces"], model["tags"]):
        corners = uv[start:start + len(face)]
        start += len(face)
        for index in range(len(face)):
            a = corners[index]
            c = corners[(index + 1) % len(face)]
            line = a[None, :] + (c - a)[None, :] * steps[:, None]
            x = numpy.clip((line[:, 0] * size).astype(numpy.int64), 0, size - 1)
            y = numpy.clip(((1.0 - line[:, 1]) * size).astype(numpy.int64), 0, size - 1)
            image[y, x, :3] = colors[tag]
    render.save_pixels(path, image)


def gltf_group():
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
        group.interface.new_socket(name="Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
        group.interface.new_socket(name="Thickness", in_out='INPUT', socket_type='NodeSocketFloat')
    return group


def load_image(path, colorspace):
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = colorspace
    return image


def material(name, albedo, normal, orm):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    result.use_backface_culling = True
    tree = result.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = load_image(albedo, 'sRGB')
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Metallic'].default_value = 0.0
    packed = tree.nodes.new('ShaderNodeTexImage')
    packed.image = load_image(orm, 'Non-Color')
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(packed.outputs['Color'], split.inputs['Color'])
    tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
    tree.links.new(split.outputs['Blue'], shader.inputs['Metallic'])
    settings = tree.nodes.new('ShaderNodeGroup')
    settings.node_tree = gltf_group()
    tree.links.new(split.outputs['Red'], settings.inputs['Occlusion'])
    bumps = tree.nodes.new('ShaderNodeTexImage')
    bumps.image = load_image(normal, 'Non-Color')
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(bumps.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    return result


def mesh_from_model(model, name):
    triangles, loops, owner = paint.triangulate(model)
    obj = render.mesh_object(name, model["points"], triangles.tolist())
    mesh = obj.data
    if len(mesh.polygons) != len(triangles):
        raise RuntimeError("mesh lost faces")
    layer = mesh.uv_layers.new(name="uv")
    layer.uv.foreach_set("vector", model["uv"][loops].reshape(-1).astype(numpy.float32))
    mesh.normals_split_custom_set_from_vertices(paint.model_normals(model, triangles).tolist())
    return obj, triangles, owner


def texture_paths(directory, name):
    return [os.path.join(directory, name + suffix) for suffix in ("_albedo.png", "_normal.png", "_orm.png")]


def armature_object(name, bones, scale):
    data = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    created = {}
    for bone_name, parent, position in bones:
        bone = data.edit_bones.new(bone_name)
        bone.head = Vector(position) * scale
        bone.tail = bone.head + Vector((0.0, 0.06 * scale, 0.0))
        bone.roll = 0.0
        if parent is not None:
            bone.parent = created[parent]
            bone.use_connect = False
        created[bone_name] = bone
    bpy.ops.object.mode_set(mode='OBJECT')
    for bone in obj.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    return obj


def skinned_object(model, name, armature, names, order, kept, textures):
    obj, triangles, owner = mesh_from_model(model, name)
    obj.data.materials.append(material(name, *textures))
    groups = [obj.vertex_groups.new(name=bone) for bone in names]
    for vertex in range(len(order)):
        for column in range(order.shape[1]):
            if kept[vertex, column] > 0.0:
                groups[int(order[vertex, column])].add([vertex], float(kept[vertex, column]), 'REPLACE')
    attach(obj, armature)
    return obj


def attach(obj, armature):
    obj.parent = armature
    obj.matrix_parent_inverse = armature.matrix_world.inverted()
    modifier = obj.modifiers.new("armature", 'ARMATURE')
    modifier.object = armature


def group_weights(obj, names, limit=4):
    mesh = obj.data
    lookup = {group.index: names.index(group.name) for group in obj.vertex_groups if group.name in names}
    dense = numpy.zeros((len(mesh.vertices), len(names)))
    for vertex in mesh.vertices:
        for element in vertex.groups:
            if element.group in lookup:
                dense[vertex.index, lookup[element.group]] = element.weight
    order = numpy.argsort(-dense, axis=1)[:, :limit]
    kept = numpy.take_along_axis(dense, order, axis=1)
    kept[kept < 0.004] = 0.0
    total = kept.sum(axis=1)
    kept[total < 1e-6, 0] = 1.0
    kept /= kept.sum(axis=1)[:, None]
    return order, kept


def reduced_object(source, name, armature, names, ratio):
    mesh = source.data.copy()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for group in source.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    modifier = obj.modifiers.new("reduce", 'DECIMATE')
    modifier.decimate_type = 'COLLAPSE'
    modifier.ratio = ratio
    modifier.use_symmetry = True
    modifier.symmetry_axis = 'X'
    modifier.use_collapse_triangulate = True
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier="reduce")
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    obj.data.polygons.foreach_set("use_smooth", numpy.ones(len(obj.data.polygons), dtype=bool))
    obj.data.name = name
    order, kept = group_weights(obj, names)
    for group in obj.vertex_groups:
        group.remove(list(range(len(obj.data.vertices))))
    for vertex in range(len(order)):
        for column in range(order.shape[1]):
            if kept[vertex, column] > 0.0:
                obj.vertex_groups[names[int(order[vertex, column])]].add([vertex], float(kept[vertex, column]), 'REPLACE')
    attach(obj, armature)
    return obj


def export_gltf(path, animations):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', export_image_format='AUTO', export_keep_originals=not animations, export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_skins=True, export_animations=animations, export_force_sampling=animations, export_optimize_animation_size=False, export_anim_single_armature=True, export_morph=False, export_yup=True, export_apply=False, use_selection=False, export_extras=False, export_cameras=False, export_lights=False)


def only(objects):
    keep = set(objects)
    hidden = []
    for obj in list(bpy.context.scene.objects):
        if obj not in keep:
            hidden.append((obj, obj.parent))
            obj.parent = None
            bpy.context.scene.collection.objects.unlink(obj)
    return hidden


def restore(hidden):
    for obj, parent in hidden:
        bpy.context.scene.collection.objects.link(obj)
        if parent is not None:
            obj.parent = parent
            obj.matrix_parent_inverse = parent.matrix_world.inverted()


def patch_material(path):
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    for entry in document.get("materials", []):
        entry.setdefault("pbrMetallicRoughness", {})
        entry["pbrMetallicRoughness"]["metallicFactor"] = 0.0
        entry["pbrMetallicRoughness"]["roughnessFactor"] = 1.0
        entry.pop("emissiveFactor", None)
        entry["doubleSided"] = False
    for entry in document.get("images", []):
        entry["uri"] = entry["uri"].replace("\\", "/")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    return document


def strip_scale(path):
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    for animation in document.get("animations", []):
        channels = [channel for channel in animation["channels"] if channel["target"]["path"] in ("translation", "rotation")]
        used = sorted(set(channel["sampler"] for channel in channels))
        remap = {old: new for new, old in enumerate(used)}
        animation["samplers"] = [animation["samplers"][old] for old in used]
        for channel in channels:
            channel["sampler"] = remap[channel["sampler"]]
        animation["channels"] = channels
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    return document


def export_clips(blueprint, clips, directory, scale):
    render.reset()
    scene = bpy.context.scene
    scene.render.fps = 30
    armature = armature_object(blueprint["rig_name"], blueprint["bones"], scale)
    names = [bone[0] for bone in blueprint["bones"]]
    os.makedirs(directory, exist_ok=True)
    for clip in clips:
        armature.animation_data_clear()
        for action in list(bpy.data.actions):
            bpy.data.actions.remove(action)
        armature.animation_data_create()
        armature.animation_data.action = bpy.data.actions.new(clip["name"])
        previous = {}
        for frame in range(clip["frames"]):
            for index, name in enumerate(names):
                bone = armature.pose.bones[name]
                q = motion.quaternion(clip["local"][frame, index])
                if name in previous and float(q @ previous[name]) < 0.0:
                    q = -q
                previous[name] = q
                bone.rotation_quaternion = q.tolist()
                bone.location = clip["shift"][frame, index].tolist()
                bone.keyframe_insert("rotation_quaternion", frame=frame)
                bone.keyframe_insert("location", frame=frame)
        scene.frame_start = 0
        scene.frame_end = clip["frames"] - 1
        path = os.path.join(directory, clip["name"] + ".gltf")
        export_gltf(path, True)
        strip_scale(path)
    return armature


def save(model, path):
    with open(path, "wb") as handle:
        pickle.dump(model, handle)


def load(path):
    with open(path, "rb") as handle:
        return pickle.load(handle)
