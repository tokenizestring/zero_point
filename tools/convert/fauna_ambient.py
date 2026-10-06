import bpy
import json
import math
import os
import shutil
import sys
import time
import numpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import fauna_ambient_birds as birds
import fauna_ambient_fish as fish
import fauna_ambient_kit as kit
import fauna_hoofed_build as build
import fauna_hoofed_render as render

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
species = {"bird_gull": (birds, "gull"), "bird_crow": (birds, "crow"), "fish_mackerel": (fish, "mackerel"), "fish_bass": (fish, "bass")}
islands = {"head": 1.7, "bill": 1.5, "eyeball": 1.6, "wing_lower": 0.75, "tail_lower": 0.6, "finger_lower": 0.6, "fin": 0.7, "spiny": 0.8, "pectoral": 0.7}


def folders(name):
    source = os.path.join(root, "assets", "source", "fauna", name)
    paths = {"source": source, "models": os.path.join(root, "assets", "raw", "models", name), "previews": os.path.join(root, "assets", "previews", "fauna"), "scratch": os.path.join(source, "work")}
    for key in ("source", "previews", "scratch"):
        os.makedirs(paths[key], exist_ok=True)
    return paths


def blueprint(name):
    module, kind = species[name]
    return module, module.build(kind)


def framing(points, bird):
    low = points.min(axis=0)
    high = points.max(axis=0)
    center = 0.5 * (low + high)
    size = high - low
    span = max(size[0], size[1])
    side = {"target": tuple(center), "direction": (1.0, 0.0, 0.0), "ortho": render.fit(size[1], max(size[2], size[1] * 0.45), (1400, 800)), "resolution": (1400, 800)}
    three = {"target": tuple(center), "direction": (0.75, 0.65, 0.45) if bird else (0.8, 0.5, 0.35), "distance": span * 3.2, "lens": 60.0, "resolution": (1000, 800)}
    front = {"target": tuple(center), "direction": (0.0, 1.0, 0.0), "ortho": render.fit(size[0], max(size[2], size[0] * 0.5), (1000, 700)), "resolution": (1000, 700)}
    top = {"target": tuple(center), "direction": (0.0, 0.0, 1.0), "ortho": render.fit(size[0], size[1], (1000, 900)), "resolution": (1000, 900)}
    under = {"target": tuple(center), "direction": (0.15, -0.35, -1.0), "ortho": render.fit(size[0], size[1], (1000, 900)), "resolution": (1000, 900)}
    return [[side, three], [front, top, under]]


def studio():
    scene = render.studio(samples=32, ground=False)
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.56, 0.64, 1.0)
    return scene


def stage_model(name, paths):
    started = time.time()
    render.reset()
    module, spec = blueprint(name)
    model = module.assemble(spec)
    triangles = sum(len(face) - 2 for face in model["faces"])
    print("MODEL", name, len(model["points"]), "vertices", triangles, "triangles")
    model = build.unwrap(model, dict(build.island_scales, **islands))
    model["occlusion"] = kit.occlusion(model)
    build.save(model, os.path.join(paths["source"], name + "_model.pickle"))
    render.reset()
    studio()
    build.layout_image(model, os.path.join(paths["scratch"], name + "_uv.png"))
    obj = render.mesh_object("cage", model["points"], model["faces"])
    obj.data.materials.append(render.plain("clay", (0.55, 0.52, 0.48), 0.65))
    render.wire(obj, 0.0003)
    prefix = os.path.join(paths["scratch"], name + "_model")
    render.shots(prefix, prefix + ".png", framing(model["points"], name.startswith("bird")))
    print("MODEL done", round(time.time() - started, 1), "s")


def stage_texture(name, paths, size=1024):
    started = time.time()
    render.reset()
    module, spec = blueprint(name)
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    c = kit.canvas(model, size)
    occlusion = c.blend(model["occlusion"][c.triangles][:, :, None])[:, 0]
    result = module.coat(c, spec, occlusion)
    kit.write_textures(c, result["color"], result["rough"], result["height"], result["relief"], occlusion, paths["source"], name)
    print("TEXTURE", name, size, round(time.time() - started, 1), "s")


def textures(directory, name):
    return [os.path.join(directory, name + suffix) for suffix in ("_albedo.png", "_normal.png", "_orm.png")]


def stage_look(name, paths):
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    render.reset()
    studio()
    obj = kit.mesh_object(model, name)
    obj.data.materials.append(build.material(name, *textures(paths["source"], name)))
    prefix = os.path.join(paths["scratch"], name + "_look")
    render.shots(prefix, prefix + ".png", framing(model["points"], name.startswith("bird")))
    print("LOOK", name)


def stage_export(name, paths):
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    folder = paths["models"]
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    copies = []
    for source in textures(paths["source"], name):
        target = os.path.join(folder, os.path.basename(source))
        shutil.copy(source, target)
        copies.append(target)
    path = kit.export(model, name, folder, copies)
    print("EXPORT", path)


def stage_check(name, paths):
    module, spec = blueprint(name)
    report = kit.inspect(os.path.join(paths["models"], name + ".gltf"), spec["budget"], 1024)
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    points = model["points"]
    part = numpy.array(model["part"])
    if name.startswith("bird"):
        trunk = numpy.isin(part, ["body"])
        report["body_half_width"] = round(float(numpy.abs(points[trunk, 0]).max()), 4)
        report["wing_root"] = round(float(numpy.abs(points[part == "wing", 0]).min()), 4)
        report["wingspan"] = round(float(points[:, 0].max() - points[:, 0].min()), 4)
        if report["wing_root"] >= 0.06:
            report["errors"].append("wing root at |x| %.3f" % report["wing_root"])
    else:
        report["rings"] = len(spec["rings"])
        report["length"] = round(float(points[:, 1].max() - points[:, 1].min()), 4)
        if report["rings"] < 12:
            report["errors"].append("only %d rings along the body" % report["rings"])
    report["origin_offset"] = [round(float(v), 4) for v in 0.5 * (points.min(axis=0) + points.max(axis=0))]
    with open(os.path.join(paths["source"], name + "_check.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
    for key, value in report.items():
        print("CHECK", key, value)
    print("CHECK", name, "PASSED" if not report["errors"] else "FAILED")
    return report


def deform(base, bird, phase, length):
    moved = base.copy()
    if bird:
        reach = numpy.abs(base[:, 0])
        arm = numpy.clip((reach - 0.05) / 0.25, 0.0, 1.0)
        hand = numpy.clip((reach - 0.3) / 0.35, 0.0, 1.0)
        angle = (math.radians(38.0) * math.sin(phase) * arm + math.radians(14.0) * math.sin(phase - 0.7) * hand) * numpy.sign(base[:, 0])
        moved[:, 0] = base[:, 0] * numpy.cos(angle) - base[:, 2] * numpy.sin(angle)
        moved[:, 2] = base[:, 0] * numpy.sin(angle) + base[:, 2] * numpy.cos(angle)
    else:
        head = base[:, 1].max()
        reach = numpy.clip((head - base[:, 1]) / length, 0.0, 1.0)
        moved[:, 0] = base[:, 0] + 0.085 * length * (0.12 + reach * reach) * numpy.sin(2.0 * math.pi * (base[:, 1] / (length * 0.95)) + phase)
    return moved


def stage_previews(name, paths):
    started = time.time()
    bird = name.startswith("bird")
    render.reset()
    scene = studio()
    bpy.ops.import_scene.gltf(filepath=os.path.join(paths["models"], name + ".gltf"))
    obj = next(o for o in scene.objects if o.type == 'MESH')
    count = len(obj.data.vertices)
    base = numpy.empty(count * 3, dtype=numpy.float32)
    obj.data.vertices.foreach_get("co", base)
    base = base.reshape(-1, 3).astype(numpy.float64)
    prefix = os.path.join(paths["scratch"], name + "_sheet")
    render.shots(prefix, os.path.join(paths["previews"], name + "_sheet.png"), framing(base, bird))
    length = float(base[:, 1].max() - base[:, 1].min())
    center = 0.5 * (base.min(axis=0) + base.max(axis=0))
    span = float(base[:, 0].max() - base[:, 0].min())
    rows = []
    for direction, label in (((0.15, 1.0, 0.25), "front"), ((0.75, 0.55, 0.5), "three")) if bird else (((0.0, 0.0, 1.0), "top"), ((0.7, 0.35, 0.55), "three")):
        tiles = []
        for index in range(8):
            phase = 2.0 * math.pi * index / 8.0
            moved = deform(base, bird, phase, length)
            obj.data.vertices.foreach_set("co", moved.astype(numpy.float32).ravel())
            obj.data.update()
            file = os.path.join(paths["scratch"], name + "_motion_tile.png")
            wide = (span if bird else length) * 1.15
            render.shoot(file, tuple(center), direction, 6.0, ortho=wide, resolution=(420, 300 if bird else 260))
            tiles.append(render.pixels_of(file))
            os.remove(file)
        rows.append(tiles)
    obj.data.vertices.foreach_set("co", base.astype(numpy.float32).ravel())
    render.compose(rows, os.path.join(paths["previews"], name + "_motion.png"), gap=2)
    print("PREVIEWS", name, round(time.time() - started, 1), "s")


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    name = arguments[0]
    stages = [a for a in arguments[1:] if not a.startswith("--")] or ["all"]
    paths = folders(name)
    for stage in stages:
        if stage in ("model", "all"):
            stage_model(name, paths)
        if stage in ("texture", "all"):
            stage_texture(name, paths)
        if stage in ("look", "all"):
            stage_look(name, paths)
        if stage in ("export", "all"):
            stage_export(name, paths)
        if stage in ("check", "all"):
            stage_check(name, paths)
        if stage in ("previews", "all"):
            stage_previews(name, paths)


main()
