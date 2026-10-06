import bpy
import json
import os
import shutil
import sys
import time
import numpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import fauna_hoofed_field as fields
import fauna_hoofed_cage as cages
import fauna_hoofed_build as build
import fauna_hoofed_check as check
import fauna_hoofed_clips as clip_maker
import fauna_hoofed_coats as coats
import fauna_hoofed_paint as paint
import fauna_hoofed_render as render
import fauna_hoofed_rig as rigs
import fauna_hoofed_species as species

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def folders(name, scratch):
    source = os.path.join(root, "assets", "source", "fauna", name)
    paths = {"source": source, "export": os.path.join(source, "export"), "previews": os.path.join(root, "assets", "previews", "fauna"), "raw": os.path.join(root, "assets", "raw"), "scratch": scratch or os.path.join(source, "work")}
    for key in ("source", "export", "previews", "scratch"):
        os.makedirs(paths[key], exist_ok=True)
    return paths


def stage_sculpt(name, paths, voxel=0.006):
    started = time.time()
    blueprint = species.build(name)
    f = blueprint["field"]
    f.scale = blueprint["scale"]
    low, high = blueprint["bounds"]
    points, quads = f.polygonize(low * f.scale, high * f.scale, voxel)
    print("SCULPT", name, len(points), "points", len(quads), "quads", round(time.time() - started, 1), "s")
    render.reset()
    render.studio()
    obj = render.mesh_object("sculpt", points, quads.tolist())
    obj.data.materials.append(render.plain("clay", (0.55, 0.52, 0.48), 0.65))
    extent = {key: value * f.scale for key, value in blueprint["extent"].items()}
    extent["height"] = extent["body"] * 1.06
    prefix = os.path.join(paths["scratch"], name + "_sculpt")
    render.shots(prefix, prefix + ".png", render.sheet_rows(extent, tuple(blueprint["marks"]["eye"] * f.scale * numpy.array([0.0, 1.0, 1.0])), f.scale, blueprint.get("zoom", 1.0)))
    render.shots(prefix, prefix + "_detail.png", render.detail_rows(blueprint["marks"], f.scale, blueprint.get("zoom", 1.0)))
    print("SCULPT sheet", round(time.time() - started, 1), "s")


def stage_model(name, paths, views=True):
    started = time.time()
    render.reset()
    blueprint = species.build(name)
    model = build.assemble(blueprint)
    triangles = sum(len(face) - 2 for face in model["faces"])
    print("MODEL", name, len(model["points"]), "vertices", triangles, "triangles", round(time.time() - started, 1), "s")
    model = build.unwrap(model, dict(build.island_scales, **blueprint.get("islands", {})))
    build.save(model, os.path.join(paths["source"], name + "_model.pickle"))
    print("MODEL unwrapped", round(time.time() - started, 1), "s")
    if views:
        scale = blueprint["scale"]
        render.reset()
        render.studio()
        build.layout_image(model, os.path.join(paths["scratch"], name + "_uv.png"))
        obj = render.mesh_object("cage", model["points"], model["faces"])
        obj.data.materials.append(render.plain("clay", (0.55, 0.52, 0.48), 0.65))
        render.wire(obj)
        marks = blueprint["marks"]
        extent = {key: value * scale for key, value in blueprint["extent"].items()}
        prefix = os.path.join(paths["scratch"], name + "_model")
        render.shots(prefix, prefix + ".png", render.sheet_rows(extent, tuple(marks["eye"] * scale * numpy.array([0.0, 1.0, 1.0])), scale, blueprint.get("zoom", 1.0)))
        render.shots(prefix, prefix + "_detail.png", render.detail_rows(marks, scale, blueprint.get("zoom", 1.0)))
        wide = scale * blueprint.get("zoom", 1.0)
        under = {"target": (0.0, 0.0, 0.7 * wide), "direction": (0.35, 0.0, -1.0), "ortho": 1.7 * wide, "resolution": (1400, 700)}
        rump = {"target": (0.0, 0.5 * wide, 0.95 * wide), "direction": (0.35, 1.0, 0.2), "ortho": 0.9 * wide, "resolution": (800, 700)}
        shoulder = {"target": (0.0, -0.45 * wide, 0.85 * wide), "direction": (1.0, -0.5, 0.1), "ortho": 0.9 * wide, "resolution": (800, 700)}
        render.shots(prefix, prefix + "_under.png", [[under], [rump, shoulder]])
        print("MODEL sheets", round(time.time() - started, 1), "s")


def stage_texture(name, paths, size=2048, views=True):
    started = time.time()
    render.reset()
    blueprint = species.build(name)
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    c = paint.canvas(model, blueprint, size)
    low = paint.canvas(model, blueprint, size // 2) if size > 1024 else c
    normal, occlusion = low.surface()
    if low is not c:
        normal = paint.transfer(low, normal, c)
        normal /= numpy.maximum(numpy.linalg.norm(normal, axis=1), 1e-9)[:, None]
        occlusion = paint.transfer(low, occlusion, c)
    result = coats.coat(name, c)
    slope = c.relief(result["height"], 1.0) * result["relief"][:, None]
    albedo, normal_path, orm = build.texture_paths(paths["source"], name)
    shaded = result["color"] * (0.82 + 0.18 * occlusion)[:, None]
    paint.write(c, shaded, albedo)
    paint.write(c, c.encode_normal(normal, slope), normal_path, fill=(0.5, 0.5, 1.0))
    paint.write(c, numpy.column_stack([occlusion, result["rough"], numpy.zeros(len(occlusion))]), orm, fill=(1.0, 0.8, 0.0))
    print("TEXTURE", name, size, round(time.time() - started, 1), "s")
    if views:
        stage_look(name, paths, blueprint, model)


def stage_look(name, paths, blueprint=None, model=None):
    started = time.time()
    blueprint = blueprint or species.build(name)
    model = model or build.load(os.path.join(paths["source"], name + "_model.pickle"))
    scale = blueprint["scale"]
    render.reset()
    render.studio()
    obj, triangles, owner = build.mesh_from_model(model, name)
    obj.data.materials.append(build.material(name, *build.texture_paths(paths["source"], name)))
    marks = blueprint["marks"]
    extent = {key: value * scale for key, value in blueprint["extent"].items()}
    extent["height"] = extent["body"] * 1.06
    prefix = os.path.join(paths["scratch"], name + "_look")
    render.shots(prefix, prefix + ".png", render.sheet_rows(extent, tuple(marks["eye"] * scale * numpy.array([0.0, 1.0, 1.0])), scale, blueprint.get("zoom", 1.0)))
    render.shots(prefix, prefix + "_detail.png", render.detail_rows(marks, scale, blueprint.get("zoom", 1.0)))
    print("LOOK sheets", round(time.time() - started, 1), "s")


def stage_rig(name, paths, ratio=0.33):
    started = time.time()
    render.reset()
    blueprint = species.build(name)
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    names, order, kept = rigs.weights(model, blueprint)
    character = os.path.join(paths["export"], "characters", name)
    reduced = os.path.join(paths["export"], "characters", name + "_lod")
    for folder in (character, reduced):
        if os.path.isdir(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)
    for source in build.texture_paths(paths["source"], name):
        shutil.copy(source, character)
    armature = build.armature_object(blueprint["rig_name"], blueprint["bones"], model["scale"])
    obj = build.skinned_object(model, name, armature, names, order, kept, build.texture_paths(character, name))
    lod = build.reduced_object(obj, name + "_lod", armature, names, ratio)
    for shown, folder, label in ((obj, character, name), (lod, reduced, name + "_lod")):
        hidden = build.only([armature, shown])
        build.export_gltf(os.path.join(folder, label + ".gltf"), False)
        build.patch_material(os.path.join(folder, label + ".gltf"))
        build.restore(hidden)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(paths["source"], name + ".blend"))
    print("RIG", name, len(names), "bones", len(obj.data.polygons), "triangles", len(lod.data.polygons), "lod triangles", round(time.time() - started, 1), "s")


def stage_clips(name, paths):
    started = time.time()
    blueprint = species.build(name)
    performer, clips = clip_maker.build(blueprint)
    directory = os.path.join(paths["export"], "animations")
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    build.export_clips(blueprint, clips, directory, blueprint["scale"])
    listing = [{"name": clip["name"], "frames": clip["frames"], "duration": round(clip["duration"], 4), "loop": clip["loop"], "speed": round(clip["speed"], 3), "events": clip["events"], "contacts": clip["contacts"]} for clip in clips]
    with open(os.path.join(paths["source"], name + "_clips.json"), "w", encoding="utf-8") as handle:
        json.dump(listing, handle, indent=1)
    print("CLIPS exported", len(clips), round(time.time() - started, 1), "s")


def stage_manifest(name, paths):
    blueprint = species.build(name)
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    scale = model["scale"]
    marks = blueprint["marks"]
    facts = blueprint["facts"]
    main = {}
    lod = {}
    problems = []
    check.check_character(os.path.join(paths["export"], "characters", name, name + ".gltf"), main, problems, 0, 10 ** 9)
    check.check_character(os.path.join(paths["export"], "characters", name + "_lod", name + "_lod.gltf"), lod, problems, 0, 10 ** 9)
    part = numpy.array(model["part"])
    skin = numpy.isin(part, ["body", "head", "rump", "nose"])
    points = model["points"]
    with open(os.path.join(paths["source"], name + "_clips.json"), "r", encoding="utf-8") as handle:
        clips = json.load(handle)
    performer = clip_maker.actor(blueprint)
    feet = []
    for key in clip_maker.legs:
        leg = performer.rig.limbs[key]
        feet.append({"bone": leg.names[-1], "toe": [round(float(v), 5) for v in leg.toe], "heel": [round(float(v), 5) for v in leg.heel]})
    hull = facts["hull"]
    manifest = {
        "name": name,
        "length": round(float(points[skin][:, 1].max() - points[skin][:, 1].min()), 3),
        "shoulder_height": round(float(marks["withers"][2] * scale), 3),
        "width": round(float(points[part == "body"][:, 0].max() * 2.0), 3),
        "mass": facts["mass"],
        "eye": [0.0, round(float(marks["eye"][1] * scale), 3), round(float(marks["eye"][2] * scale), 3)],
        "mouth": [0.0, round(float((marks["nose"] - marks["head_up"] * 0.015)[1] * scale), 3), round(float((marks["nose"] - marks["head_up"] * 0.015)[2] * scale), 3)],
        "hull": {"center": [round(v * scale, 3) for v in hull["center"]], "half_length": round(hull["half_length"] * scale, 3), "radius": round(hull["radius"] * scale, 3)},
        "bones": main["bones"],
        "triangles": main["triangles"],
        "lod_triangles": lod["triangles"],
        "head_bone": "head",
        "jaw_bone": "jaw",
        "rig": blueprint["rig_name"],
        "triangle_budget": [8000, 20000],
        "feet": feet,
        "clips": clips,
    }
    if "saddle" in blueprint:
        saddle = blueprint["saddle"]
        manifest["saddle"] = {"bone": saddle["bone"], "parent": saddle["parent"], "position": [round(float(v) * scale, 3) for v in saddle["position"]], "forward": [0.0, -1.0, 0.0], "up": [0.0, 0.0, 1.0]}
    with open(os.path.join(paths["source"], name + ".json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1)
    print("MANIFEST", name, manifest["bones"], "bones", manifest["triangles"], "triangles", manifest["lod_triangles"], "lod", len(clips), "clips")


def stage_check(name, paths, root=None):
    result = check.run(root or paths["export"], os.path.join(paths["source"], name + ".json"))
    with open(os.path.join(paths["source"], name + ("_check.json" if root is None else "_check_published.json")), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1)
    for clip, entry in result["clips"].items():
        print("CHECK", clip, entry.get("frames"), "frames", "loop %.5f deg" % entry["loop_error_degrees"] if "loop_error_degrees" in entry else "", "slide %.2f%% lowest %.4f lift %.4f" % (entry["slide_percent"], entry["lowest_point"], entry["stance_height_error"]) if "slide_percent" in entry else "")
    for error in result["errors"]:
        print("CHECK ERROR", error)
    print("CHECK", name, "PASSED" if not result["errors"] else "FAILED")
    return result


def stage_motion(name, paths, only=None, view=(1.0, 0.0, 0.0), label="motion", tile=440, count=8):
    started = time.time()
    with open(os.path.join(paths["source"], name + ".json"), "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    blueprint = species.build(name)
    scale = blueprint["scale"]
    render.reset()
    scene = render.studio()
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(paths["export"], "characters", name, name + ".gltf"))
    armature = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
    extent = blueprint["extent"]
    rows = []
    for clip in manifest["clips"]:
        if only and not any(clip["name"].endswith(key) for key in only):
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(paths["export"], "animations", clip["name"] + ".gltf"))
        fresh = [obj for obj in bpy.data.objects if obj not in before]
        source = next(obj for obj in fresh if obj.type == 'ARMATURE')
        armature.animation_data_create()
        armature.animation_data.action = source.animation_data.action
        armature.animation_data.action_slot = source.animation_data.action_slot
        for obj in fresh:
            bpy.data.objects.remove(obj)
        last = clip["frames"] - 1
        tiles = []
        for index in range(count):
            frame = int(round(index * last / (float(count) if clip["loop"] else count - 1.0)))
            scene.frame_set(frame)
            file = os.path.join(paths["scratch"], "%s_tile.png" % name)
            width = extent["length"] * 1.2 * scale
            render.shoot(file, (0.0, extent["center"] * scale, extent["height"] * 0.47 * scale), view, 8.0, ortho=width, resolution=(tile, int(tile * extent["height"] * 1.02 / (extent["length"] * 1.2))))
            tiles.append(render.pixels_of(file))
            os.remove(file)
        if tile > 500:
            half = (len(tiles) + 1) // 2
            rows.append(tiles[:half])
            rows.append(tiles[half:])
        else:
            rows.append(tiles)
        print("MOTION", clip["name"], round(time.time() - started, 1), "s")
    path = os.path.join(paths["scratch"], name + "_" + label + ".png")
    render.compose(rows, path, gap=2)
    return path


def stage_pose(name, paths, picks, views=((1.0, -0.12, 0.08), (0.75, -0.6, 0.28), (0.1, -1.0, 0.15), (-0.6, 0.75, 0.35))):
    blueprint = species.build(name)
    scale = blueprint["scale"]
    render.reset()
    scene = render.studio()
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(paths["export"], "characters", name, name + ".gltf"))
    armature = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
    extent = blueprint["extent"]
    rows = []
    loaded = {}
    for pick in picks:
        clip, frame = pick.split(":")
        full = blueprint["motion"]["prefix"] + clip
        if full not in loaded:
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=os.path.join(paths["export"], "animations", full + ".gltf"))
            fresh = [obj for obj in bpy.data.objects if obj not in before]
            source = next(obj for obj in fresh if obj.type == 'ARMATURE')
            loaded[full] = (source.animation_data.action, source.animation_data.action_slot)
            for obj in fresh:
                bpy.data.objects.remove(obj)
        armature.animation_data_create()
        armature.animation_data.action = loaded[full][0]
        armature.animation_data.action_slot = loaded[full][1]
        scene.frame_set(int(frame))
        tiles = []
        for view in views:
            file = os.path.join(paths["scratch"], "%s_pose_tile.png" % name)
            render.shoot(file, (0.0, extent["center"] * scale, extent["body"] * 0.5 * scale), view, 8.0, ortho=extent["length"] * 1.05 * scale, resolution=(760, 600))
            tiles.append(render.pixels_of(file))
            os.remove(file)
        rows.append(tiles)
    render.compose(rows, os.path.join(paths["scratch"], name + "_pose.png"), gap=2)


def stage_previews(name, paths):
    started = time.time()
    blueprint = species.build(name)
    model = build.load(os.path.join(paths["source"], name + "_model.pickle"))
    scale = blueprint["scale"]
    marks = blueprint["marks"]
    extent = {key: value * scale for key, value in blueprint["extent"].items()}
    render.reset()
    scene = render.studio(samples=48)
    bpy.ops.import_scene.gltf(filepath=os.path.join(paths["export"], "characters", name, name + ".gltf"))
    prefix = os.path.join(paths["scratch"], name + "_sheet")
    render.shots(prefix, os.path.join(paths["previews"], name + "_sheet.png"), render.sheet_rows(extent, tuple(marks["eye"] * scale * numpy.array([0.0, 1.0, 1.0])), scale, blueprint.get("zoom", 1.0)))
    render.reset()
    render.studio(samples=48)
    obj = render.mesh_object("cage", model["points"], model["faces"])
    obj.data.materials.append(render.plain("clay", (0.55, 0.52, 0.48), 0.65))
    render.wire(obj, 0.0011 * scale)
    side = {"target": (0.0, extent["center"], extent["height"] * 0.5), "direction": (1.0, 0.0, 0.0), "ortho": render.fit(extent["length"], extent["height"], (2000, 1500)), "resolution": (2000, 1500)}
    render.shots(prefix, os.path.join(paths["previews"], name + "_wire.png"), [[side]])
    path = stage_motion(name, paths)
    shutil.copy(path, os.path.join(paths["previews"], name + "_motion.png"))
    print("PREVIEWS", name, round(time.time() - started, 1), "s")


def stage_publish(name, paths):
    result = stage_check(name, paths)
    if result["errors"]:
        raise RuntimeError("staging check failed, nothing published")
    with open(os.path.join(paths["source"], name + ".json"), "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    for folder in (name, name + "_lod"):
        target = os.path.join(paths["raw"], "characters", folder)
        if os.path.isdir(target):
            shutil.rmtree(target)
        shutil.copytree(os.path.join(paths["export"], "characters", folder), target)
    os.makedirs(os.path.join(paths["raw"], "animations"), exist_ok=True)
    for clip in manifest["clips"]:
        for suffix in (".gltf", ".bin"):
            shutil.copy(os.path.join(paths["export"], "animations", clip["name"] + suffix), os.path.join(paths["raw"], "animations", clip["name"] + suffix))
    published = stage_check(name, paths, paths["raw"])
    if published["errors"]:
        raise RuntimeError("published files failed the check")
    print("PUBLISHED", name, len(manifest["clips"]), "clips")


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    name = arguments[0]
    stages = [a for a in arguments[1:] if not a.startswith("--")] or ["all"]
    scratch = next((a.split("=", 1)[1] for a in arguments if a.startswith("--scratch=")), "")
    size = int(next((a.split("=", 1)[1] for a in arguments if a.startswith("--size=")), "2048"))
    paths = folders(name, scratch)
    for stage in stages:
        if stage == "sculpt":
            stage_sculpt(name, paths)
        if stage == "model":
            stage_model(name, paths)
        if stage == "texture":
            stage_texture(name, paths, size)
        if stage == "look":
            stage_look(name, paths)
        if stage == "rig":
            stage_rig(name, paths)
        if stage == "clips":
            stage_clips(name, paths)
        if stage == "manifest":
            stage_manifest(name, paths)
        if stage == "check":
            stage_check(name, paths)
        if stage == "previews":
            stage_previews(name, paths)
        if stage == "publish":
            stage_publish(name, paths)
        if stage == "all":
            stage_model(name, paths, False)
            stage_texture(name, paths, size, False)
            stage_rig(name, paths)
            stage_clips(name, paths)
            stage_manifest(name, paths)
            stage_previews(name, paths)
            stage_publish(name, paths)
        if stage == "pose":
            stage_pose(name, paths, next(a.split("=", 1)[1].split(",") for a in arguments if a.startswith("--frames=")))
        if stage == "motion":
            picks = next((a.split("=", 1)[1].split(",") for a in arguments if a.startswith("--clips=")), None)
            if any(a == "--big" for a in arguments):
                stage_motion(name, paths, picks, (1.0, 0.0, 0.0), "motion_big", 760, int(next((a.split("=", 1)[1] for a in arguments if a.startswith("--count=")), "8")))
            else:
                stage_motion(name, paths, picks)
            if any(a == "--front" for a in arguments):
                stage_motion(name, paths, picks, (0.25, -1.0, 0.25), "motion_front", 600, 8)


main()
