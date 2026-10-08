import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import oilrig_library as lib
import oilrig_kit as ok
from buildkit import V

budgets = {"near": 60000, "far": 4000}
published_root = kit.models_root
stage_root = os.path.join(lib.preview_root, "stage")


def located(folder):
    staged = os.path.join(stage_root, folder, folder + ".gltf")
    return stage_root if os.path.exists(staged) else published_root


def export_to(root, folder, objects):
    for obj in objects:
        if obj.type == 'MESH':
            obj.data.validate(verbose=False)
    kit.models_root = root
    try:
        return kit.export_building(folder, objects)
    finally:
        kit.models_root = published_root


def material_triangles(build):
    totals = {}
    for part in build.parts.values():
        for face, slot in zip(part.faces, part.face_slots):
            name = part.slots[slot]
            totals[name] = totals.get(name, 0) + len(face) - 2
    return sorted(totals.items(), key=lambda item: -item[1])


def patch(path):
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    glow = False
    for material in document.get("materials", []):
        name = material.get("name")
        if name in lib.alpha_sets:
            material["alphaMode"] = "MASK"
            material["alphaCutoff"] = 0.5
            material["doubleSided"] = True
        entry = lib.glow_sets.get(name)
        if entry is not None:
            color, strength = entry
            material["emissiveFactor"] = [float(c) for c in color]
            material.setdefault("extensions", {})["KHR_materials_emissive_strength"] = {"emissiveStrength": float(strength)}
            glow = True
    if glow:
        used = document.setdefault("extensionsUsed", [])
        if "KHR_materials_emissive_strength" not in used:
            used.append("KHR_materials_emissive_strength")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    return document


def mixed_alpha(build):
    problems = []
    for key, part in build.parts.items():
        kinds = set(name in lib.alpha_sets for name in part.slots)
        if len(kinds) > 1:
            problems.append(key)
    return problems


def summary(name, report, build):
    path = os.path.join(lib.preview_root, "report_" + name + ".json")
    entry = {"triangles": report["triangles"], "markers": report["markers"], "low": report["low"], "high": report["high"], "materials": report["materials"], "problems": report["problems"]}
    if build is not None:
        boxes = {}
        for box_name, lo, hi in build.boxes:
            prefix = "_".join(box_name.split("_")[:2])
            boxes[prefix] = boxes.get(prefix, 0) + 1
        entry["marker_kinds"] = boxes
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(entry, handle, indent=1)


def export(name, maker, far_maker, publish=False):
    lib.register()
    kit.reset_scene()
    started = time.time()
    root = published_root if publish else stage_root
    os.makedirs(root, exist_ok=True)
    b = maker()
    mixed = mixed_alpha(b)
    objects = b.finish()
    folder = "bld_rig_" + name
    path, document = export_to(root, folder, objects)
    patch(path)
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    report = rk.audit(path, document, budgets["near"])
    if mixed:
        print("WARNING mixed alpha parts", mixed, flush=True)
    print("BUILD", folder, "tris", report["triangles"], "parts", len(b.parts), "boxes", len(b.boxes), round(time.time() - started, 1), "s", flush=True)
    print("  MATERIALS", " ".join("%s:%d" % item for item in material_triangles(b)), flush=True)
    summary(folder, report, b)
    export_far(name, far_maker, publish)
    return report


def export_far(name, far_maker, publish=False):
    lib.register()
    kit.reset_scene()
    root = published_root if publish else stage_root
    os.makedirs(root, exist_ok=True)
    folder = "bld_rig_" + name + "_far"
    far = far_maker()
    mixed = mixed_alpha(far)
    objects = far.finish()
    path, document = export_to(root, folder, objects)
    patch(path)
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    report = rk.audit(path, document, budgets["far"])
    if mixed:
        print("WARNING mixed alpha parts", mixed, flush=True)
    print("BUILD", folder, "tris", report["triangles"], "parts", len(far.parts), flush=True)
    print("  MATERIALS", " ".join("%s:%d" % item for item in material_triangles(far)), flush=True)
    summary(folder, report, None)
    kit.reset_scene()
    return report


def remove(obj):
    kit.bpy.data.objects.remove(obj)


def import_model(folder):
    kit.models_root = located(folder)
    try:
        objects = kit.import_building(folder)
    finally:
        kit.models_root = published_root
    visual = []
    boxes = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        if kit.is_marker(obj.name):
            obj.hide_render = True
            low, high = kit.world_bounds([obj])
            boxes.append((obj.name, low, high))
        else:
            visual.append(obj)
    return visual, boxes


def sea_material(dark=False):
    bpy = kit.bpy
    material = bpy.data.materials.new("preview_sea")
    material.use_nodes = True
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (0.006, 0.02, 0.024, 1.0)
    shader.inputs['Roughness'].default_value = 0.06
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 0.35
    noise.inputs['Detail'].default_value = 6.0
    coords = tree.nodes.new('ShaderNodeTexCoord')
    tree.links.new(coords.outputs['Object'], noise.inputs['Vector'])
    bump = tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    bump.inputs['Distance'].default_value = 0.4
    tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return material


def sea_plane(extent=1500.0):
    bpy = kit.bpy
    mesh = bpy.data.meshes.new("preview_sea")
    mesh.from_pydata([(-extent, -extent, 0.0), (extent, -extent, 0.0), (extent, extent, 0.0), (-extent, extent, 0.0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(sea_material())
    obj = bpy.data.objects.new("preview_sea", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def seabed_plane():
    ground = kit.ground(ok.seabed - 0.4, 300.0, "dirt_debris", 6.0)
    return ground


groups = {
    "jacket": {"models": ["jacket"], "sea": True},
    "jacket_under": {"models": ["jacket"], "sea": False, "seabed": True},
    "cellar": {"models": ["jacket", "cellar"], "sea": True},
    "main": {"models": ["jacket", "cellar", "main"], "sea": True},
    "rig": {"models": ["jacket", "cellar", "main", "quarters", "helideck", "derrick"], "sea": True},
    "quarters": {"models": ["quarters"], "sea": False},
    "helideck": {"models": ["quarters", "helideck", "main"], "sea": True},
    "derrick": {"models": ["main", "derrick"], "sea": True},
    "far": {"models": ["jacket_far", "cellar_far", "main_far", "quarters_far", "helideck_far", "derrick_far"], "sea": True},
}

shots = {
    "jacket": {
        "three": ((-48.0, -62.0, 14.0), (0.0, -4.0, 2.0), 30.0),
        "landing": ((-9.0, -34.0, 3.2), (0.5, -17.0, 6.0), 34.0),
        "tower": ((14.0, -32.0, 9.0), (-0.5, -16.4, 9.0), 30.0),
        "splash": ((-26.0, -22.0, 1.6), (-16.0, -13.5, 0.5), 32.0),
        "on_landing": ((5.5, -19.8, 3.65), (-2.0, -16.0, 4.6), 22.0),
        "in_tower": ((2.9, -16.9, 3.65), (-2.6, -16.9, 5.6), 18.0),
        "sea_stair": ((24.0, -31.0, 3.0), (9.5, -19.9, 0.2), 30.0),
        "from_water": ((17.5, -19.9, 0.15), (8.0, -19.9, 1.6), 22.0),
    },
    "jacket_under": {
        "under": ((-52.0, -66.0, -6.0), (0.0, 0.0, -10.0), 26.0),
        "base": ((-30.0, -34.0, -22.0), (0.0, 0.0, -22.0), 24.0),
    },
    "cellar": {
        "three": ((-52.0, -60.0, 24.0), (0.0, 0.0, 14.0), 30.0),
        "deck_sw": ((-20.0, -17.0, 17.65), (0.0, 2.0, 17.0), 22.0),
        "deck_ne": ((20.0, 16.0, 17.65), (-2.0, 0.0, 17.2), 22.0),
        "wellbay": ((-1.0, -2.5, 17.7), (-6.0, 4.5, 17.0), 20.0),
        "arrival": ((3.0, -16.4, 17.65), (12.0, -18.0, 18.5), 22.0),
        "stair": ((4.2, -16.0, 17.7), (12.5, -18.5, 20.5), 20.0),
    },
    "main": {
        "three": ((-60.0, -55.0, 38.0), (0.0, 0.0, 22.0), 30.0),
        "deck_sw": ((-22.0, -18.0, 25.65), (0.0, 0.0, 26.0), 22.0),
        "deck_ne": ((10.0, 18.0, 25.65), (-8.0, 0.0, 25.5), 22.0),
        "arrival": ((6.0, -17.8, 25.65), (11.0, -10.0, 25.8), 22.0),
        "workshop": ((-4.6, -15.1, 25.65), (-9.2, -18.9, 24.9), 16.0, 1.5),
        "store": ((1.7, -15.0, 25.6), (-2.6, -18.8, 24.8), 16.0, 1.5),
        "lifeboat": ((-2.0, 12.0, 25.65), (8.0, 21.0, 22.0), 22.0),
        "drill": ((3.5, 10.5, 26.5), (-6.0, 4.5, 28.0), 22.0),
        "cellar_under": ((-20.0, -17.0, 17.65), (0.0, 2.0, 17.0), 22.0, 0.8),
        "cellar_wellbay": ((-1.0, -2.5, 17.7), (-6.0, 4.5, 17.0), 20.0, 0.8),
        "cellar_ne": ((20.0, 16.0, 17.65), (-2.0, 0.0, 17.2), 22.0, 0.8),
        "cellar_collapse": ((17.0, 12.8, 17.65), (22.0, 18.0, 15.8), 20.0, 0.8),
        "cellar_process": ((-12.0, 6.0, 17.65), (-20.0, 12.0, 17.5), 20.0, 0.8),
        "drill_floor": ((-2.0, 1.0, 30.15), (-7.0, 6.0, 29.5), 18.0),
        "blast": ((-11.0, -9.5, 25.65), (-17.5, -4.0, 26.5), 20.0),
        "crane": ((-4.0, -24.0, 30.0), (-15.0, -8.0, 30.0), 24.0),
    },
    "quarters": {
        "west": ((-6.0, -24.0, 30.0), (18.5, 0.0, 28.5), 28.0),
        "east": ((52.0, 22.0, 31.0), (18.5, 0.0, 28.5), 28.0),
        "lobby": ((17.3, -7.6, 25.7), (12.6, -11.4, 25.0), 16.0, 1.6),
        "locker": ((17.3, -1.6, 25.7), (12.6, -6.5, 25.0), 16.0, 1.6),
        "galley": ((16.9, -0.4, 25.7), (12.6, 4.6, 25.0), 16.0, 1.6),
        "mess": ((17.3, 11.2, 25.7), (12.6, 5.6, 25.0), 16.0, 1.6),
        "recreation": ((19.9, 4.4, 25.7), (24.4, -1.6, 25.0), 16.0, 1.6),
        "provisions": ((19.9, 11.2, 25.7), (24.4, 5.6, 25.0), 16.0, 1.6),
        "corridor": ((18.6, -9.5, 25.7), (18.6, 11.0, 25.6), 18.0, 1.6),
        "stair": ((19.6, -9.6, 25.7), (23.5, -11.0, 27.0), 16.0, 1.6),
        "medical": ((17.3, -7.6, 28.9), (12.6, -11.4, 28.2), 16.0, 1.6),
        "cabin_w": ((17.3, -2.9, 28.9), (12.6, -6.6, 28.2), 16.0, 1.6),
        "cabin_e": ((19.9, 1.6, 28.9), (24.4, -2.0, 28.2), 16.0, 1.6),
        "showers": ((19.9, -2.9, 28.9), (24.4, -6.6, 28.2), 16.0, 1.6),
        "control": ((17.3, 11.2, 32.1), (12.6, -0.5, 31.2), 16.0, 1.6),
        "control_back": ((12.8, 9.0, 32.1), (17.5, 0.0, 31.4), 16.0, 1.6),
        "radio": ((19.9, -2.9, 32.1), (24.4, -6.6, 31.4), 16.0, 1.6),
        "oim": ((17.3, -7.6, 32.1), (12.6, -11.4, 31.4), 16.0, 1.6),
        "meeting": ((19.9, 4.6, 32.1), (24.0, -2.0, 31.4), 16.0, 1.6),
        "roof": ((12.8, -11.4, 35.4), (24.0, 10.0, 33.8), 18.0),
    },
    "helideck": {
        "above": ((21.0, -18.0, 52.0), (21.0, 4.0, 36.0), 30.0),
        "edge": ((10.0, -8.5, 37.7), (24.0, 6.0, 36.2), 20.0),
        "stair": ((15.6, -11.4, 35.3), (18.0, -6.0, 36.5), 20.0),
        "under": ((13.2, -7.6, 35.0), (22.0, 6.0, 34.6), 18.0),
    },
    "derrick": {
        "tower": ((4.0, 18.0, 25.7), (-6.0, 4.5, 40.0), 22.0),
        "flare": ((-15.5, 19.3, 25.9), (-50.0, 17.5, 33.0), 24.0),
        "walk": ((-26.0, 17.5, 25.9), (-45.0, 17.5, 32.5), 20.0),
        "tip": ((-62.5, 16.4, 39.6), (0.0, 0.0, 28.0), 24.0),
        "monkey": ((-6.0, 9.6, 51.2), (-6.0, 4.5, 40.0), 18.0),
        "crown": ((-3.0, -6.0, 66.0), (-6.0, 4.5, 58.0), 24.0),
    },
    "rig": {
        "sea_sw": ((-125.0, -150.0, 20.0), (0.0, 0.0, 18.0), 30.0),
        "sea_ne": ((140.0, 115.0, 32.0), (0.0, 0.0, 20.0), 30.0),
        "sea_nw": ((-140.0, 110.0, 12.0), (-8.0, 0.0, 22.0), 28.0),
        "air": ((-95.0, -80.0, 90.0), (0.0, 0.0, 22.0), 30.0),
        "boat": ((-20.0, -60.0, 1.8), (0.0, -10.0, 16.0), 24.0),
        "lod_sw": ((-62.0, -76.0, 18.0), (-4.0, 0.0, 22.0), 30.0),
        "lod_ne": ((70.0, 66.0, 26.0), (-4.0, 0.0, 24.0), 30.0),
    },
    "far": {
        "sea_sw": ((-125.0, -150.0, 20.0), (0.0, 0.0, 18.0), 30.0),
        "sea_ne": ((140.0, 115.0, 32.0), (0.0, 0.0, 20.0), 30.0),
        "sea_nw": ((-140.0, 110.0, 12.0), (-8.0, 0.0, 22.0), 28.0),
        "air": ((-95.0, -80.0, 90.0), (0.0, 0.0, 22.0), 30.0),
        "lod_sw": ((-62.0, -76.0, 18.0), (-4.0, 0.0, 22.0), 30.0),
        "lod_ne": ((70.0, 66.0, 26.0), (-4.0, 0.0, 24.0), 30.0),
        "shore": ((-420.0, -300.0, 25.0), (0.0, 0.0, 25.0), 50.0),
    },
}

plans = {
    "jacket": [("LANDING", 4.2, 0.5, 4.0), ("TOWER", 14.0, 4.0, 15.5)],
    "cellar": [("CELLAR", 21.5, 15.0, 23.0)],
    "main": [("MAIN", 31.0, 23.0, 30.0)],
    "quarters": [("GROUND", 26.9, 23.5, 27.0), ("FIRST", 30.1, 27.0, 30.2), ("SECOND", 33.3, 30.2, 33.4), ("ROOF", 35.3, 33.4, 35.3)],
    "helideck": [("HELIDECK", 40.0, 33.5, 38.0)],
    "derrick": [("DRILL FLOOR", 33.0, 28.0, 33.0), ("FLARE", 60.0, 24.0, 60.0)],
}

extra_shots = {}


def setup_scene(group, samples):
    entry = groups[group]
    all_visual = []
    all_boxes = []
    for model in entry["models"]:
        folder = "bld_rig_" + model
        if not os.path.exists(os.path.join(located(folder), folder, folder + ".gltf")):
            print("MISSING", folder, flush=True)
            continue
        visual, boxes = import_model(folder)
        all_visual.extend(visual)
        all_boxes.extend(boxes)
    kit.daylight(1.0, 3.6, (0.45, 0.62, -0.55))
    if entry.get("sea"):
        sea_plane()
    if entry.get("seabed"):
        seabed_plane()
    for name, low, high in all_boxes:
        if not name.startswith("light_"):
            continue
        kind = name.split("_")[1]
        color = {"warm": (1.0, 0.72, 0.42), "cold": (0.78, 0.88, 1.0), "fire": (1.0, 0.45, 0.15)}.get(kind, (1.0, 1.0, 1.0))
        kit.point_light((low + high) * 0.5, 140.0 if kind == "cold" else 110.0, 0.12, color)
    return all_visual, all_boxes


def preview(wanted, which, samples):
    lib.register()
    for group in wanted or ["jacket"]:
        kit.reset_scene()
        lib.register()
        visual, boxes = setup_scene(group, samples)
        prefix = os.path.join(lib.preview_root, group + "_")
        table = dict(shots.get(group, {}))
        table.update(extra_shots.get(group, {}))
        todo = which or (list(table) + (["plan"] if group in plans else []))
        for key in todo:
            if key == "plan" or key not in table:
                continue
            position, aim, lens = table[key][:3]
            exposure = table[key][3] if len(table[key]) > 3 else 0.0
            kit.render_settings(samples, (1600, 900), exposure)
            cam = kit.camera(V(*position), V(*aim), lens, None, 0.03, 3000.0)
            kit.shoot(prefix + key + ".png")
            remove(cam)
        if "plan" in todo and group in plans and visual:
            low, high = kit.world_bounds(visual)
            kit.plan_sheet(group, plans[group], boxes, low, high, max(16, samples // 2), prefix + "plan.png")


def room_shots(group, table):
    extra_shots.setdefault(group, {}).update(table)


def sheet(names):
    rows = []
    for group in names or ["jacket"]:
        entries = []
        for key in list(shots.get(group, {})) + ["plan"]:
            path = os.path.join(lib.preview_root, group + "_" + key + ".png")
            if os.path.exists(path):
                entries.append((key, path))
        rows.append((group, entries))
    kit.contact_sheet(rows, os.path.join(lib.preview_root, "sheet_" + "_".join(names or ["jacket"]) + ".png"))
