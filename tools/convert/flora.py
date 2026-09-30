import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mathutils import Vector

import flora_kit as kit
import flora_bake
import flora_bark
import flora_birch
import flora_hawthorn
import flora_oak
import flora_pine
import flora_view
import flora_willow

arguments = sys.argv[sys.argv.index("--") + 1:]
command = arguments[0]
name = arguments[1] if len(arguments) > 1 else "all"
options = arguments[2:]
registry = {}
for module in (flora_oak, flora_birch, flora_pine, flora_hawthorn, flora_willow):
    registry.update(module.species)
selected = list(registry) if name == "all" else [name]
suffixes = ("", "_far", "_shadow")
scratch = os.path.join(kit.preview_root, "work")


def option(key, fallback):
    for entry in options:
        if entry.startswith(key + "="):
            return entry[len(key) + 1:]
    return fallback


def lods_of(record):
    return {"tree": (0, 1, 2), "shrub": (0, 1), "small": (0,)}[record["kind"]]


def build(entry, record):
    variants = [int(value) for value in option("variants", ",".join(str(index) for index in range(record["variants"]))).split(",")]
    lods = [int(value) for value in option("lods", ",".join(str(index) for index in lods_of(record))).split(",")]
    for variant in variants:
        for lod in lods:
            kit.reset()
            model = record["build"](variant, lod)
            wood_material = kit.surface_material("bark", kit.texture_set(entry, "bark"), False) if record.get("bark", True) and len(model.wood.faces) else None
            leaf_material = kit.surface_material("leaf", kit.texture_set(entry, "leaf"), True)
            objects = model.finish(kit.model_name(entry, variant, suffixes[lod]), wood_material, leaf_material)
            kit.export_model(entry, kit.model_name(entry, variant, suffixes[lod]), objects)


def look(entry, record):
    lod = int(option("lod", "0"))
    variants = [int(value) for value in option("variants", ",".join(str(index) for index in range(record["variants"]))).split(",")]
    names = [kit.model_name(entry, variant, suffixes[lod]) for variant in variants]
    angle = float(option("angle", "0"))
    direction = (-__import__("math").sin(angle), -__import__("math").cos(angle), float(option("pitch", "0.12")))
    flora_view.lineup(entry, names, os.path.join(scratch, "%s_look%s.png" % (entry, option("tag", ""))), (int(option("width", "1800")), int(option("height", "900"))), direction, 1.5, None, 0.0, option("engine", "BLENDER_EEVEE_NEXT"))


def impostor(entry, record):
    variants = [int(value) for value in option("variants", ",".join(str(index) for index in range(record["variants"]))).split(",")]
    for variant in variants:
        kit.reset()
        model = record["build"](variant, 0)
        wood_material = kit.surface_material("bark", kit.texture_set(entry, "bark"), False)
        leaf_material = kit.surface_material("leaf", kit.texture_set(entry, "leaf"), True)
        objects = model.finish(kit.model_name(entry, variant), wood_material, leaf_material)
        flora_bake.impostor(entry, variant, objects, scratch, record.get("solid", (0.1, 0.56)))


def lods(entry, record):
    variants = [int(value) for value in option("variants", ",".join(str(index) for index in range(record["variants"]))).split(",")]
    kinds = ("near", "far", "shadow", "impostor") if record["kind"] == "tree" else ("near", "far")
    paths = []
    for variant in variants:
        paths.append(os.path.join(scratch, "%s_%d_strip.png" % (entry, variant)))
        flora_view.strip(entry, variant, paths[-1], kinds)
    flora_view.stack(paths, os.path.join(kit.preview_root, "%s_lods.png" % entry))


def distance(entry, record):
    variant = int(option("variant", "0"))
    flora_view.distances(entry, variant, os.path.join(scratch, "%s_%d" % (entry, variant)))


def preview(entry, record):
    names = [kit.model_name(entry, variant) for variant in range(record["variants"])]
    flora_view.lineup(entry, names, os.path.join(kit.preview_root, "%s.png" % entry), (int(option("width", "1800")), int(option("height", "900"))))
    if record["kind"] != "small":
        lods(entry, record)


def close(entry, record):
    variant = int(option("variant", "0"))
    lod = int(option("lod", "0"))
    reach = float(option("reach", "10"))
    tall = float(option("tall", "8"))
    shots = [("walk", (0.0, -reach * 1.25, 1.7), (0.0, 0.0, tall * 0.5), 22.0), ("under", (0.6, -reach * 0.32, 1.7), (0.0, reach * 0.1, tall * 0.62), 20.0), ("trunk", (0.9, -2.6, 1.6), (0.0, 0.0, 1.0), 28.0), ("leaf", (reach * 0.42, -reach * 0.42, 1.75), (reach * 0.34, -reach * 0.2, 2.9), 35.0)]
    wanted = option("shots", "walk,under,trunk,leaf").split(",")
    flora_view.closeups(entry, kit.model_name(entry, variant, suffixes[lod]), os.path.join(scratch, "%s_%d" % (entry, variant)), [shot for shot in shots if shot[0] in wanted], (int(option("width", "1280")), int(option("height", "800"))), None, option("engine", "BLENDER_EEVEE_NEXT"), float(option("exposure", "0")))


for entry in selected:
    record = registry[entry]
    if command == "close":
        close(entry, record)
    if command == "impostor":
        impostor(entry, record)
    if command == "lods":
        lods(entry, record)
    if command == "distance":
        distance(entry, record)
    if command == "preview":
        preview(entry, record)
    if command == "atlas":
        record["atlas"]()
    if command == "bark":
        getattr(flora_bark, entry)()
    if command == "build":
        build(entry, record)
    if command == "look":
        look(entry, record)
