import bpy
import bmesh
import math
import os
import pickle
import numpy
import fauna_hoofed_field as fields
import fauna_hoofed_cage as cages
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
    pieces = species.pieces(blueprint)
    for piece in pieces:
        if piece["part"] != "eyeball":
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
    return obj, triangles, owner


def texture_paths(directory, name):
    return [os.path.join(directory, name + suffix) for suffix in ("_albedo.png", "_normal.png", "_orm.png")]


def save(model, path):
    with open(path, "wb") as handle:
        pickle.dump(model, handle)


def load(path):
    with open(path, "rb") as handle:
        return pickle.load(handle)
