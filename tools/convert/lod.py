import bpy
import json
import os
import sys

arguments = sys.argv[sys.argv.index("--") + 1:]
models_root = arguments[0]
jobs = [entry.split(":") for entry in arguments[1].split(",")]


def triangles(objects):
    return sum(len(polygon.vertices) - 2 for obj in objects for polygon in obj.data.polygons)


for name, target in jobs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    directory = os.path.join(models_root, name)
    source = next(entry for entry in os.listdir(directory) if entry.endswith(".gltf"))
    bpy.ops.import_scene.gltf(filepath=os.path.join(directory, source), merge_vertices=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    before = triangles(meshes)
    ratio = min(1.0, float(target) / max(before, 1))
    for obj in meshes:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.object.mode_set(mode='OBJECT')
        if obj.data.has_custom_normals:
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        modifier = obj.modifiers.new("lod", 'DECIMATE')
        modifier.decimate_type = 'COLLAPSE'
        modifier.ratio = ratio
        modifier.delimit = set()
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier="lod")
    after = triangles(meshes)
    output = os.path.join(models_root, name + "_far")
    os.makedirs(output, exist_ok=True)
    path = os.path.join(output, name + "_far.gltf")
    for obj in bpy.context.scene.objects:
        obj.select_set(obj.type == 'MESH')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_keep_originals=True, export_yup=True, export_apply=True, export_skins=False, export_animations=False, export_morph=False, export_cameras=False, export_lights=False, export_extras=False)
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    for image in document.get("images", []):
        if "uri" in image:
            uri = image["uri"]
            if os.path.isabs(uri) is False:
                uri = os.path.normpath(os.path.join(output, uri))
            image["uri"] = os.path.relpath(uri, output).replace("\\", "/")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    print("LOD", name, before, "->", after)
