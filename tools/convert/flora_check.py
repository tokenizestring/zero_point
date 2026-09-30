import json
import math
import os
import shutil
import struct
import sys
import numpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flora_config as config

convert_root = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(convert_root))
source_root = os.path.join(repo_root, "assets", "source", "flora")
models_root = os.path.join(repo_root, "assets", "raw", "models")
kinds = {5126: "<f4", 5125: "<u4", 5123: "<u2", 5121: "u1", 5122: "<i2", 5120: "i1"}
widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def png_info(path):
    with open(path, "rb") as handle:
        header = handle.read(26)
    if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">IIBB", header[16:26])


def accessor(document, buffers, index):
    entry = document["accessors"][index]
    view = document["bufferViews"][entry["bufferView"]]
    offset = view.get("byteOffset", 0) + entry.get("byteOffset", 0)
    kind = numpy.dtype(kinds[entry["componentType"]])
    width = widths[entry["type"]]
    stride = view.get("byteStride", kind.itemsize * width)
    data = buffers[view["buffer"]]
    if stride == kind.itemsize * width:
        return numpy.frombuffer(data, dtype=kind, count=entry["count"] * width, offset=offset).reshape(entry["count"], width)
    rows = [numpy.frombuffer(data, dtype=kind, count=width, offset=offset + stride * row) for row in range(entry["count"])]
    return numpy.stack(rows)


def node_matrix(node):
    if "matrix" in node:
        return numpy.array(node["matrix"], dtype=numpy.float64).reshape(4, 4).T
    x, y, z, w = node.get("rotation", [0.0, 0.0, 0.0, 1.0])
    sx, sy, sz = node.get("scale", [1.0, 1.0, 1.0])
    tx, ty, tz = node.get("translation", [0.0, 0.0, 0.0])
    rotation = numpy.array([[1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)], [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)], [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)]])
    matrix = numpy.identity(4)
    matrix[:3, :3] = rotation * numpy.array([sx, sy, sz])[None, :]
    matrix[:3, 3] = (tx, ty, tz)
    return matrix


def inspect(directory, name):
    errors = []
    stats = {"triangles": 0, "low": [0.0, 0.0, 0.0], "high": [0.0, 0.0, 0.0], "radius": 0.0, "materials": {}, "trunk": 0.0, "parts": []}
    path = os.path.join(directory, name + ".gltf")
    if os.path.isfile(path) is False:
        return ["missing " + path], stats
    if len(name) > 41 or name != name.lower() or all(ord(letter) < 128 for letter in name) is False:
        errors.append("bad model name " + name)
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    buffers = []
    for entry in document.get("buffers", []):
        file_path = os.path.join(directory, entry.get("uri", ""))
        if os.path.isfile(file_path) is False:
            errors.append("missing buffer " + entry.get("uri", "?"))
            buffers.append(b"")
            continue
        with open(file_path, "rb") as handle:
            buffers.append(handle.read())
        if len(buffers[-1]) < entry["byteLength"]:
            errors.append("short buffer " + entry["uri"])
    images = []
    for entry in document.get("images", []):
        file_path = os.path.normpath(os.path.join(directory, entry.get("uri", "").replace("/", os.sep)))
        images.append(file_path)
        if os.path.isfile(file_path) is False:
            errors.append("missing image " + entry.get("uri", "?"))
            continue
        info = png_info(file_path)
        if info is None:
            errors.append("not a png " + entry["uri"])
        elif info[0] & (info[0] - 1) or info[1] & (info[1] - 1) or info[0] > 2048 or info[1] > 2048 or info[2] != 8:
            errors.append("bad image size %s %s" % (entry["uri"], info))

    def image_of(reference):
        if reference is None or "index" not in reference:
            return None
        return images[document["textures"][reference["index"]]["source"]]

    masked = []
    for index, material in enumerate(document.get("materials", [])):
        shading = material.get("pbrMetallicRoughness", {})
        if shading.get("metallicFactor", None) != 0:
            errors.append("material %s metallicFactor is not 0" % material.get("name"))
        files = {"diff": image_of(shading.get("baseColorTexture")), "nor_gl": image_of(material.get("normalTexture")), "arm": image_of(shading.get("metallicRoughnessTexture")), "occlusion": image_of(material.get("occlusionTexture"))}
        for key, value in files.items():
            if value is None:
                errors.append("material %s has no %s texture" % (material.get("name"), key))
        mask = files["diff"].replace("_diff_", "_alpha_") if files["diff"] and "_diff_" in os.path.basename(files["diff"]) else None
        has_mask = mask is not None and os.path.isfile(mask)
        cut = material.get("alphaMode") == "MASK"
        if has_mask and cut is False:
            errors.append("material %s has an alpha mask but is not MASK" % material.get("name"))
        if cut and has_mask is False:
            errors.append("material %s is MASK without an alpha mask file" % material.get("name"))
        if cut and material.get("doubleSided") is not True:
            errors.append("material %s is MASK but single sided" % material.get("name"))
        if cut and abs(material.get("alphaCutoff", 0.5) - 0.5) > 1e-6:
            errors.append("material %s alphaCutoff is not 0.5" % material.get("name"))
        masked.append(cut)
        stats["materials"][material.get("name", str(index))] = {"diff": files["diff"], "nor_gl": files["nor_gl"], "arm": files["arm"], "alpha": mask if has_mask else None, "cut": cut}
    low = numpy.array([1e9, 1e9, 1e9])
    high = numpy.array([-1e9, -1e9, -1e9])
    chest = []
    feet = []
    scene = document["scenes"][document.get("scene", 0)]
    pending = [(index, numpy.identity(4)) for index in scene.get("nodes", [])]
    while pending:
        index, parent = pending.pop()
        node = document["nodes"][index]
        world = parent @ node_matrix(node)
        for child in node.get("children", []):
            pending.append((child, world))
        if "mesh" not in node:
            continue
        stats["parts"].append(node.get("name", "?"))
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            attributes = primitive.get("attributes", {})
            missing = [key for key in ("POSITION", "NORMAL", "TEXCOORD_0") if key not in attributes]
            if missing or "indices" not in primitive or "material" not in primitive:
                errors.append("primitive of %s lacks %s" % (node.get("name"), missing + [key for key in ("indices", "material") if key not in primitive]))
                continue
            if primitive.get("mode", 4) != 4:
                errors.append("primitive of %s is not a triangle list" % node.get("name"))
            if document["accessors"][attributes["POSITION"]]["componentType"] != 5126 or document["accessors"][attributes["TEXCOORD_0"]]["componentType"] != 5126:
                errors.append("primitive of %s uses non float attributes" % node.get("name"))
                continue
            positions = accessor(document, buffers, attributes["POSITION"]).astype(numpy.float64)
            normals = accessor(document, buffers, attributes["NORMAL"]).astype(numpy.float64)
            uvs = accessor(document, buffers, attributes["TEXCOORD_0"]).astype(numpy.float64)
            indices = accessor(document, buffers, primitive["indices"]).astype(numpy.int64).ravel()
            if len(normals) != len(positions) or len(uvs) != len(positions):
                errors.append("attribute counts differ in %s" % node.get("name"))
                continue
            if len(indices) % 3 or (len(indices) and int(indices.max()) >= len(positions)):
                errors.append("bad indices in %s" % node.get("name"))
                continue
            if bool(numpy.isfinite(positions).all() and numpy.isfinite(normals).all() and numpy.isfinite(uvs).all()) is False:
                errors.append("non finite values in %s" % node.get("name"))
                continue
            lengths = numpy.linalg.norm(normals, axis=1)
            if len(lengths) and (abs(lengths - 1.0) > 0.02).mean() > 0.001:
                errors.append("normals of %s are not unit length" % node.get("name"))
            positions = positions @ world[:3, :3].T + world[:3, 3]
            normals = normals @ world[:3, :3].T
            low = numpy.minimum(low, positions.min(axis=0))
            high = numpy.maximum(high, positions.max(axis=0))
            stats["radius"] = max(stats["radius"], float(numpy.sqrt(positions[:, 0] ** 2 + positions[:, 2] ** 2).max()))
            stats["triangles"] += len(indices) // 3
            cut = masked[primitive["material"]] if primitive["material"] < len(masked) else False
            corners = positions[indices].reshape(-1, 3, 3)
            face = numpy.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
            if cut:
                if len(uvs) and (uvs.min() < -0.01 or uvs.max() > 1.01):
                    errors.append("atlas uvs of %s leave the 0..1 range" % node.get("name"))
            else:
                agreement = (face * normals[indices].reshape(-1, 3, 3).sum(axis=1)).sum(axis=1)
                area = numpy.linalg.norm(face, axis=1)
                if len(agreement) and area[agreement < 0.0].sum() > (0.03 if name.endswith("_shadow") else 0.005) * area.sum():
                    errors.append("winding of %s disagrees with its normals" % node.get("name"))
                for first, second in ((0, 1), (1, 2), (2, 0)):
                    start = corners[:, first]
                    end = corners[:, second]
                    crossing = (start[:, 1] - 1.3) * (end[:, 1] - 1.3) < 0.0
                    if crossing.any():
                        ratio = (1.3 - start[crossing, 1]) / (end[crossing, 1] - start[crossing, 1])
                        chest.append(start[crossing] + (end[crossing] - start[crossing]) * ratio[:, None])
                feet.append(positions[positions[:, 1] < 0.3])
    if stats["triangles"] == 0:
        errors.append("no triangles")
        return errors, stats
    stats["low"] = [float(value) for value in low]
    stats["high"] = [float(value) for value in high]
    if chest and sum(len(entry) for entry in feet):
        band = numpy.concatenate(chest)[:, [0, 2]]
        foot = numpy.concatenate(feet)[:, [0, 2]].mean(axis=0)
        band = band[numpy.sqrt(((band - foot) ** 2).sum(axis=1)) < 1.6]
        if len(band):
            center = (band.min(axis=0) + band.max(axis=0)) * 0.5
            stats["trunk"] = float(numpy.median(numpy.sqrt(((band - center) ** 2).sum(axis=1))))
    return errors, stats


def check(name, root):
    entry = config.species[name]
    kind = entry["kind"]
    errors = []
    report = {}
    shared = {}
    for variant in range(entry["variants"]):
        near = None
        for suffix in config.suffixes(kind):
            model = config.model_name(name, variant, suffix)
            found, stats = inspect(os.path.join(root, model), model)
            errors.extend("%s: %s" % (model, text) for text in found)
            report[model] = stats
            if stats["triangles"] == 0:
                continue
            budget = config.budgets[kind][suffix]
            if stats["triangles"] < budget[0] or stats["triangles"] > budget[1]:
                errors.append("%s: %d triangles outside budget %d..%d" % (model, stats["triangles"], budget[0], budget[1]))
            height = stats["high"][1]
            for label, files in stats["materials"].items():
                if suffix != "_impostor":
                    shared.setdefault(label, set()).add((files["diff"], files["nor_gl"], files["arm"]))
            if suffix == "":
                near = stats
                if stats["low"][1] < config.base[kind][0] or stats["low"][1] > config.base[kind][1]:
                    errors.append("%s: base at %.3f is not near the ground" % (model, stats["low"][1]))
                if height < entry["height"][0] * 0.97 or height > entry["height"][1] * 1.03:
                    errors.append("%s: height %.2f outside %.2f..%.2f" % (model, height, entry["height"][0], entry["height"][1]))
                across = max(stats["high"][0] - stats["low"][0], stats["high"][2] - stats["low"][2])
                if "across" in entry and (across < entry["across"][0] * 0.95 or across > entry["across"][1] * 1.05):
                    errors.append("%s: width %.2f outside %.2f..%.2f" % (model, across, entry["across"][0], entry["across"][1]))
            elif near is not None and suffix in ("_far", "_shadow"):
                if abs(height - near["high"][1]) > max(0.12 * near["high"][1], 0.08):
                    errors.append("%s: height %.2f differs from near %.2f" % (model, height, near["high"][1]))
                if abs(stats["radius"] - near["radius"]) > max(0.25 * near["radius"], 0.1):
                    errors.append("%s: radius %.2f differs from near %.2f" % (model, stats["radius"], near["radius"]))
                if stats["low"][1] < config.base[kind][0] or stats["low"][1] > config.base[kind][1] + 0.3:
                    errors.append("%s: base at %.3f is not near the ground" % (model, stats["low"][1]))
            elif near is not None and suffix == "_impostor":
                top = stats["high"][1]
                bottom = stats["low"][1]
                wide = stats["high"][0] - stats["low"][0]
                if top < near["high"][1] or top > near["high"][1] + 0.08 * (near["high"][1] - near["low"][1]):
                    errors.append("%s: quad top %.2f does not match near top %.2f" % (model, top, near["high"][1]))
                if bottom > near["low"][1] or bottom < near["low"][1] - 0.08 * (near["high"][1] - near["low"][1]):
                    errors.append("%s: quad bottom %.2f does not match near bottom %.2f" % (model, bottom, near["low"][1]))
                if wide < near["radius"] * 2.0 or wide > near["radius"] * 2.0 * 1.12:
                    errors.append("%s: quad width %.2f does not match near diameter %.2f" % (model, wide, near["radius"] * 2.0))
                if abs(stats["high"][0] + stats["low"][0]) > 1e-4:
                    errors.append("%s: quad is not centred" % model)
    for label, sets in shared.items():
        if len(sets) > 1:
            errors.append("%s: material %s does not share one texture set across models" % (name, label))
    return errors, report


def manifest(root):
    result = {"version": 1, "units": "metres", "up": "+Y", "species": {}}
    for name in config.order:
        entry = config.species[name]
        kind = entry["kind"]
        if all(os.path.isfile(os.path.join(root, config.model_name(name, variant, suffix), config.model_name(name, variant, suffix) + ".gltf")) for variant in range(entry["variants"]) for suffix in config.suffixes(kind)) is False:
            continue
        record = {"kind": kind, "biomes": entry["biomes"], "blocks_movement": entry["block"], "variants": []}
        materials = {}
        for variant in range(entry["variants"]):
            models = {}
            triangles = {}
            near = None
            for suffix in config.suffixes(kind):
                model = config.model_name(name, variant, suffix)
                found, stats = inspect(os.path.join(root, model), model)
                label = suffix[1:] if suffix else "near"
                models[label] = model
                triangles[label] = stats["triangles"]
                if suffix == "":
                    near = stats
                for material, files in stats["materials"].items():
                    materials.setdefault(material, files["cut"])
            height = near["high"][1]
            item = {"name": config.model_name(name, variant), "models": models, "height": round(height, 3), "width": round(max(near["high"][0] - near["low"][0], near["high"][2] - near["low"][2]), 3), "radius": round(near["radius"], 3), "bounds_min": [round(value, 3) for value in near["low"]], "bounds_max": [round(value, 3) for value in near["high"]], "triangles": triangles, "sway": float("%.2g" % (entry["sway"] / (height * height))) if entry["sway"] > 0.0 else 0.0}
            if kind == "tree":
                item["distances"] = {"near": entry["near"], "impostor": entry["impostor"], "far": entry["far"], "shadow": entry["shadow"]}
                item["trunk_radius"] = entry["trunk"][variant] if "trunk" in entry else round(near["trunk"], 3)
            elif kind == "shrub":
                item["distances"] = {"near": entry["near"], "far": entry["far"], "shadow": entry["shadow"]}
            else:
                item["distances"] = {"near": 1000.0, "far": entry["far"], "shadow": entry["shadow"]}
            record["variants"].append(item)
        record["materials"] = {material: {"alpha_cut": cut} for material, cut in sorted(materials.items())}
        if "notes" in entry:
            record["notes"] = entry["notes"]
        result["species"][name] = record
    os.makedirs(source_root, exist_ok=True)
    with open(os.path.join(source_root, "flora.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1)
    return result


def run(names, root):
    failed = False
    for name in names:
        errors, report = check(name, root)
        for model in sorted(report):
            stats = report[model]
            print("%-28s %6d tris  y %.2f..%.2f  radius %.2f  trunk %.3f" % (model, stats["triangles"], stats["low"][1], stats["high"][1], stats["radius"], stats["trunk"]))
        for text in errors:
            print("ERROR", text)
        print("CHECK", name, "FAILED" if errors else "PASSED", len(errors))
        failed = failed or bool(errors)
    return failed is False


def publish(name):
    entry = config.species[name]
    staged = os.path.join(source_root, name, "export")
    if run([name], staged) is False:
        print("PUBLISH", name, "refused")
        return False
    for variant in range(entry["variants"]):
        for suffix in config.suffixes(entry["kind"]):
            model = config.model_name(name, variant, suffix)
            target = os.path.join(models_root, model)
            if os.path.isdir(target):
                shutil.rmtree(target)
            shutil.copytree(os.path.join(staged, model), target)
    passed = run([name], models_root)
    manifest(models_root)
    print("PUBLISH", name, "done" if passed else "copied but published check failed")
    return passed


if __name__ == "__main__":
    arguments = sys.argv[1:]
    action = arguments[0] if arguments else "check"
    chosen = config.order if len(arguments) < 2 or arguments[1] == "all" else [arguments[1]]
    passed = True
    if action == "publish":
        for entry in chosen:
            passed = publish(entry) and passed
    elif action == "manifest":
        manifest(models_root)
    else:
        published = len(arguments) > 2 and arguments[2] == "published"
        for entry in chosen:
            if published or os.path.isdir(os.path.join(source_root, entry, "export")):
                passed = run([entry], models_root if published else os.path.join(source_root, entry, "export")) and passed
    sys.exit(0 if passed else 1)
