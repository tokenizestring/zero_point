import bpy
import os
import sys
import time
import numpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import fauna_hoofed_field as fields
import fauna_hoofed_cage as cages
import fauna_hoofed_build as build
import fauna_hoofed_coats as coats
import fauna_hoofed_paint as paint
import fauna_hoofed_render as render
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
    prefix = os.path.join(paths["scratch"], name + "_sculpt")
    render.shots(prefix, prefix + ".png", render.sheet_rows(extent, tuple(blueprint["marks"]["eye"] * f.scale * numpy.array([0.0, 1.0, 1.0])), f.scale))
    render.shots(prefix, prefix + "_detail.png", render.detail_rows(blueprint["marks"], f.scale))
    print("SCULPT sheet", round(time.time() - started, 1), "s")


def stage_model(name, paths, views=True):
    started = time.time()
    render.reset()
    blueprint = species.build(name)
    model = build.assemble(blueprint)
    triangles = sum(len(face) - 2 for face in model["faces"])
    print("MODEL", name, len(model["points"]), "vertices", triangles, "triangles", round(time.time() - started, 1), "s")
    model = build.unwrap(model)
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
        render.shots(prefix, prefix + ".png", render.sheet_rows(extent, tuple(marks["eye"] * scale * numpy.array([0.0, 1.0, 1.0])), scale))
        render.shots(prefix, prefix + "_detail.png", render.detail_rows(marks, scale))
        under = {"target": (0.0, 0.0, 0.7 * scale), "direction": (0.35, 0.0, -1.0), "ortho": 1.7 * scale, "resolution": (1400, 700)}
        rump = {"target": (0.0, 0.5 * scale, 0.95 * scale), "direction": (0.35, 1.0, 0.2), "ortho": 0.9 * scale, "resolution": (800, 700)}
        shoulder = {"target": (0.0, -0.45 * scale, 0.85 * scale), "direction": (1.0, -0.5, 0.1), "ortho": 0.9 * scale, "resolution": (800, 700)}
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
    paint.write(c, c.encode_normal(normal, slope), normal_path)
    paint.write(c, numpy.column_stack([occlusion, result["rough"], numpy.zeros(len(occlusion))]), orm)
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
    prefix = os.path.join(paths["scratch"], name + "_look")
    render.shots(prefix, prefix + ".png", render.sheet_rows(extent, tuple(marks["eye"] * scale * numpy.array([0.0, 1.0, 1.0])), scale))
    render.shots(prefix, prefix + "_detail.png", render.detail_rows(marks, scale))
    print("LOOK sheets", round(time.time() - started, 1), "s")


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


main()
