import bpy
import json
import os
import sys
import tempfile
import time
import numpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ground_kit as kit
import ground_check as check
import ground_preview as preview
import ground_sets as sets

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
textures = os.path.join(root, "assets", "raw", "textures")
previews = os.path.join(root, "assets", "previews", "ground")
manifest = os.path.join(root, "assets", "source", "ground", "ground.json")


def bake(name, resolution, samples, target, work):
    entry = sets.catalog[name]
    tile = kit.tile(name, entry["size"], entry["seed"], work, entry.get("field", 2048), entry.get("grid", 1024), entry.get("margin", 0.1))
    entry["build"](tile)
    path = tile.render(resolution, samples, entry.get("reach", 0.06))
    passes = kit.read_passes(path, 2)
    if target != textures:
        numpy.savez(os.path.join(work, name + "_raw.npz"), **passes)
    maps = kit.compose(passes, entry["size"] / (resolution // 2), **entry.get("compose", {}))
    os.remove(path)
    kit.export(maps, os.path.join(target, name), name)
    tile.note("exported, relief %.4f m" % maps["relief"])
    return maps["relief"]


def record(name, relief):
    entry = sets.catalog[name]
    report = check.measure(textures, name)
    data = {"sets": {}}
    if os.path.exists(manifest):
        with open(manifest, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    data["sets"][name] = {"tile_m": entry["size"], "uv_scale": round(1.0 / entry["size"], 4), "relief_m": round(float(relief), 4), "albedo_linear": [round(value, 4) for value in report["albedo"]], "roughness": round(report["rough"][3], 4), "description": entry["text"]}
    data["sets"] = {key: data["sets"][key] for key in sets.catalog if key in data["sets"]}
    os.makedirs(os.path.dirname(manifest), exist_ok=True)
    with open(manifest, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4)
        handle.write("\n")


def relief_of(name):
    with open(manifest, "r", encoding="utf-8") as handle:
        return json.load(handle)["sets"][name]["relief_m"]


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    work = os.path.join(tempfile.gettempdir(), "zero_point_ground")
    if "--work" in arguments:
        work = arguments[arguments.index("--work") + 1]
        arguments = [value for value in arguments if value not in ("--work", work)]
    flat = "--flat" in arguments
    arguments = [value for value in arguments if value != "--flat"]
    command = arguments[0]
    names =list(sets.catalog) if len(arguments) < 2 or arguments[1] == "all" else arguments[1].split(",")
    started = time.time()
    if command == "bake":
        for name in names:
            relief = bake(name, 4096, 48, textures, work)
            record(name, relief)
            os.makedirs(previews, exist_ok=True)
            preview.tiled(os.path.join(textures, name), name, os.path.join(previews, name + "_tile.png"))
            preview.inspect(os.path.join(textures, name), name, work)
            preview.lit(os.path.join(textures, name), name, sets.catalog[name]["size"], relief, os.path.join(previews, name + ".png"))
        failed = check.run(textures, names)
        preview.sheet(previews, [name for name in sets.catalog], os.path.join(previews, "sheet.png"))
        if failed:
            raise RuntimeError("checker failed for " + ", ".join(failed))
    elif command == "draft":
        resolution = int(arguments[2]) if len(arguments) > 2 else 2048
        samples = int(arguments[3]) if len(arguments) > 3 else 24
        for name in names:
            relief = bake(name, resolution, samples, os.path.join(work, "draft"), work)
            source = os.path.join(work, "draft", name)
            preview.tiled(source, name, os.path.join(work, name + "_tile.png"), resolution // 8)
            preview.inspect(source, name, work, (resolution // 8, resolution // 8), min(720, resolution // 4))
            if not flat:
                preview.lit(source, name, sets.catalog[name]["size"], relief, os.path.join(work, name + "_lit.png"))
    elif command == "preview":
        os.makedirs(previews, exist_ok=True)
        for name in names:
            preview.tiled(os.path.join(textures, name), name, os.path.join(previews, name + "_tile.png"))
            preview.lit(os.path.join(textures, name), name, sets.catalog[name]["size"], relief_of(name), os.path.join(previews, name + ".png"))
        preview.sheet(previews, [name for name in sets.catalog], os.path.join(previews, "sheet.png"))
    elif command == "sheet":
        preview.sheet(previews, [name for name in sets.catalog], os.path.join(previews, "sheet.png"))
    elif command == "check":
        if check.run(textures, names):
            raise RuntimeError("checker failed")
    else:
        raise RuntimeError("unknown command " + command)
    print("GROUND done in %.1fs" % (time.time() - started), flush=True)


main()
