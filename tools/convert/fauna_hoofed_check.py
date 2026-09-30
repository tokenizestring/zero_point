import json
import math
import os
import struct
import sys
import zlib
import numpy

kinds = {5120: numpy.int8, 5121: numpy.uint8, 5122: numpy.int16, 5123: numpy.uint16, 5125: numpy.uint32, 5126: numpy.float32}
widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    buffers = []
    for entry in document.get("buffers", []):
        with open(os.path.join(os.path.dirname(path), entry["uri"]), "rb") as handle:
            buffers.append(handle.read())
    return document, buffers


def accessor(document, buffers, index):
    entry = document["accessors"][index]
    view = document["bufferViews"][entry["bufferView"]]
    kind = numpy.dtype(kinds[entry["componentType"]])
    width = widths[entry["type"]]
    offset = view.get("byteOffset", 0) + entry.get("byteOffset", 0)
    stride = view.get("byteStride", kind.itemsize * width)
    raw = buffers[view["buffer"]]
    if stride == kind.itemsize * width:
        data = numpy.frombuffer(raw, dtype=kind, count=entry["count"] * width, offset=offset)
    else:
        data = numpy.array([numpy.frombuffer(raw, dtype=kind, count=width, offset=offset + stride * row) for row in range(entry["count"])])
    return data.reshape(entry["count"], width).astype(numpy.float64)


def png_pixels(path):
    try:
        from PIL import Image
        with Image.open(path) as image:
            mode = image.mode
            data = numpy.array(image.convert("RGBA" if "A" in mode else "RGB"))
        return data, 6 if "A" in mode else 2
    except ImportError:
        pass
    try:
        import bpy
        image = bpy.data.images.load(path, check_existing=False)
        width, height = image.size
        depth = image.depth
        data = numpy.empty(width * height * 4, dtype=numpy.float32)
        image.pixels.foreach_get(data)
        bpy.data.images.remove(image)
        return numpy.rint(data.reshape(height, width, 4) * 255.0).astype(numpy.uint8), 6 if depth == 32 else 2
    except ImportError:
        pass
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png: " + path)
    cursor = 8
    chunks = b""
    header = None
    while cursor < len(raw):
        length, tag = struct.unpack(">I4s", raw[cursor:cursor + 8])
        body = raw[cursor + 8:cursor + 8 + length]
        if tag == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            chunks += body
        cursor += 12 + length
    width, height, depth, color, compression, filtering, interlace = header
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    if depth != 8 or interlace != 0:
        raise ValueError("unsupported png layout: " + path)
    data = numpy.frombuffer(zlib.decompress(chunks), dtype=numpy.uint8).reshape(height, width * channels + 1)
    rows = numpy.zeros((height, width * channels), dtype=numpy.uint8)
    previous = numpy.zeros(width * channels, dtype=numpy.int32)
    for y in range(height):
        kind = int(data[y, 0])
        line = data[y, 1:].astype(numpy.int32)
        if kind == 1:
            for channel in range(channels):
                line[channel::channels] = numpy.cumsum(line[channel::channels]) & 255
        elif kind == 2:
            line = (line + previous) & 255
        elif kind in (3, 4):
            out = numpy.zeros_like(line)
            for x in range(len(line)):
                left = out[x - channels] if x >= channels else 0
                up = previous[x]
                corner = previous[x - channels] if x >= channels else 0
                if kind == 3:
                    guess = (left + up) // 2
                else:
                    p = left + up - corner
                    pa, pb, pc = abs(p - left), abs(p - up), abs(p - corner)
                    guess = left if (pa <= pb and pa <= pc) else (up if pb <= pc else corner)
                out[x] = (line[x] + guess) & 255
            line = out
        rows[y] = line
        previous = line
    return rows.reshape(height, width, channels), color


def quaternion_matrix(q):
    x, y, z, w = q
    return numpy.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def node_trs(node):
    return numpy.array(node.get("translation", [0.0, 0.0, 0.0]), dtype=numpy.float64), numpy.array(node.get("rotation", [0.0, 0.0, 0.0, 1.0]), dtype=numpy.float64), numpy.array(node.get("scale", [1.0, 1.0, 1.0]), dtype=numpy.float64)


def parents(document):
    result = {}
    for index, node in enumerate(document["nodes"]):
        for child in node.get("children", []):
            result[child] = index
    return result


def world(document, translations=None, rotations=None):
    nodes = document["nodes"]
    parent = parents(document)
    cache = {}

    def solve(index):
        if index in cache:
            return cache[index]
        t, r, s = node_trs(nodes[index])
        if translations is not None and index in translations:
            t = translations[index]
        if rotations is not None and index in rotations:
            r = rotations[index]
        local = numpy.eye(4)
        local[:3, :3] = quaternion_matrix(r / numpy.linalg.norm(r)) * s[None, :]
        local[:3, 3] = t
        cache[index] = solve(parent[index]) @ local if index in parent else local
        return cache[index]

    return {index: solve(index) for index in range(len(nodes))}


def to_blender(point):
    return numpy.array([point[0], -point[2], point[1]])


def check_character(path, report, errors, low=6000, high=24000, bones_limit=128):
    document, buffers = load(path)
    name = os.path.splitext(os.path.basename(path))[0]

    def fail(message):
        errors.append(name + ": " + message)

    if os.path.basename(os.path.dirname(path)) != name:
        fail("file name differs from the folder name")
    if len(document.get("skins", [])) != 1:
        fail("expected one skin, found %d" % len(document.get("skins", [])))
        return document
    skin = document["skins"][0]
    nodes = document["nodes"]
    parent = parents(document)
    needed = set()
    for joint in skin["joints"]:
        walk = joint
        while walk is not None:
            needed.add(walk)
            walk = parent.get(walk)
    names = [nodes[index]["name"] for index in sorted(needed)]
    report["bones"] = len(needed)
    if len(needed) > bones_limit:
        fail("%d bones over the limit" % len(needed))
    if len(set(names)) != len(names):
        fail("duplicate bone names")
    for bone in names:
        if not bone.isascii() or len(bone) > 47 or bone.startswith("Bip01"):
            fail("bad bone name " + bone)
    if "root" not in names:
        fail("no root bone")
    roots = [index for index in needed if index not in parent]
    if len(roots) != 1:
        fail("expected a single armature node above the bones")
    for index in roots:
        t, r, s = node_trs(nodes[index])
        if numpy.abs(t).max() > 1e-6 or numpy.abs(r - numpy.array([0.0, 0.0, 0.0, 1.0])).max() > 1e-6 or numpy.abs(s - 1.0).max() > 1e-6:
            fail("armature object is not at identity")
    if document.get("extensionsUsed"):
        fail("extensions in use: %s" % document["extensionsUsed"])
    for entry in document.get("buffers", []):
        if not entry.get("uri", "").endswith(".bin"):
            fail("buffer is not an external bin")
    for entry in document["accessors"]:
        if "sparse" in entry:
            fail("sparse accessor")
    meshes = [node for node in nodes if "mesh" in node]
    if len(meshes) != 1 or "skin" not in meshes[0]:
        fail("expected exactly one skinned mesh node")
        return document
    t, r, s = node_trs(meshes[0])
    if numpy.abs(t).max() > 1e-6 or numpy.abs(r - numpy.array([0.0, 0.0, 0.0, 1.0])).max() > 1e-6 or numpy.abs(s - 1.0).max() > 1e-6:
        fail("mesh object is not at identity")
    materials = document.get("materials", [])
    if len(materials) != 1:
        fail("expected one material, found %d" % len(materials))
    triangles = 0
    low_corner = numpy.full(3, numpy.inf)
    high_corner = numpy.full(3, -numpy.inf)
    for primitive in document["meshes"][meshes[0]["mesh"]]["primitives"]:
        attributes = primitive.get("attributes", {})
        for key in ("POSITION", "NORMAL", "TEXCOORD_0", "JOINTS_0", "WEIGHTS_0"):
            if key not in attributes:
                fail("primitive lacks " + key)
        if "JOINTS_1" in attributes or "WEIGHTS_1" in attributes:
            fail("more than four influences")
        if "targets" in primitive:
            fail("morph targets present")
        if "indices" not in primitive or "material" not in primitive:
            fail("primitive lacks indices or material")
            continue
        if primitive.get("mode", 4) != 4:
            fail("primitive is not a triangle list")
        indices = accessor(document, buffers, primitive["indices"])
        triangles += len(indices) // 3
        positions = accessor(document, buffers, attributes["POSITION"])
        low_corner = numpy.minimum(low_corner, positions.min(axis=0))
        high_corner = numpy.maximum(high_corner, positions.max(axis=0))
        weights = accessor(document, buffers, attributes["WEIGHTS_0"])
        if document["accessors"][attributes["WEIGHTS_0"]]["componentType"] != 5126:
            weights = weights / (255.0 if document["accessors"][attributes["WEIGHTS_0"]]["componentType"] == 5121 else 65535.0)
        if numpy.abs(weights.sum(axis=1) - 1.0).max() > 2e-3:
            fail("weights are not normalised (max error %.4f)" % numpy.abs(weights.sum(axis=1) - 1.0).max())
        joints = accessor(document, buffers, attributes["JOINTS_0"])
        if joints.max() >= len(skin["joints"]):
            fail("joint index out of range")
        uv = accessor(document, buffers, attributes["TEXCOORD_0"])
        if uv.min() < -1e-4 or uv.max() > 1.0001:
            fail("uv outside the unit square")
        normals = accessor(document, buffers, attributes["NORMAL"])
        if numpy.abs(numpy.linalg.norm(normals, axis=1) - 1.0).max() > 1e-2:
            fail("normals are not unit length")
    report["triangles"] = triangles
    report["bounds"] = [to_blender(low_corner).tolist(), to_blender(high_corner).tolist()]
    if triangles < low or triangles > high:
        fail("%d triangles outside the budget %d-%d" % (triangles, low, high))
    if abs(low_corner[1]) > 0.012:
        fail("lowest point is %.3f m from the ground" % low_corner[1])
    for entry in materials:
        pbr = entry.get("pbrMetallicRoughness", {})
        if pbr.get("metallicFactor", 1.0) != 0.0:
            fail("metallicFactor is not 0")
        if pbr.get("roughnessFactor", 1.0) != 1.0:
            fail("roughnessFactor is not 1")
        if entry.get("alphaMode", "OPAQUE") != "OPAQUE":
            fail("alpha mode " + entry["alphaMode"])
        if any(abs(v) > 0.0 for v in entry.get("emissiveFactor", [0.0, 0.0, 0.0])) or "emissiveTexture" in entry:
            fail("emission present")
        slots = {"base": pbr.get("baseColorTexture"), "surface": pbr.get("metallicRoughnessTexture"), "normal": entry.get("normalTexture"), "occlusion": entry.get("occlusionTexture")}
        for label, slot in slots.items():
            if slot is None:
                fail("material lacks the %s texture" % label)
        if any(slot is None for slot in slots.values()):
            continue
        files = {label: document["images"][document["textures"][slot["index"]]["source"]]["uri"] for label, slot in slots.items()}
        report["images"] = files
        if files["surface"] != files["occlusion"]:
            fail("occlusion and roughness are not the same packed image")
        if len(set(files.values())) != 3:
            fail("expected three distinct images")
        for label, uri in files.items():
            file = os.path.normpath(os.path.join(os.path.dirname(path), uri.replace("%20", " ")))
            if not os.path.isfile(file):
                fail("missing image " + uri)
                continue
            pixels, color = png_pixels(file)
            if label == "base" and color != 2:
                fail("base colour has an alpha channel")
            if label == "surface" and int(pixels[:, :, 2].max()) != 0:
                fail("metallic channel is not zero")
            if label == "surface":
                report["roughness_range"] = [int(pixels[:, :, 1].min()), int(pixels[:, :, 1].max())]
    matrices = accessor(document, buffers, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    rest = world(document)
    worst = 0.0
    for slot, joint in enumerate(skin["joints"]):
        worst = max(worst, float(numpy.abs(matrices[slot] @ rest[joint] - numpy.eye(4)).max()))
    if worst > 1e-4:
        fail("inverse bind matrices do not match the rest pose (%.5f)" % worst)
    report["rest"] = {nodes[index]["name"]: [list(map(float, part)) for part in node_trs(nodes[index])] for index in sorted(needed)}
    report["order"] = names
    return document


def check_lod(path, main_report, report, errors, ratio=(0.25, 0.4)):
    document = check_character(path, report, errors, 0, 1000000)
    name = os.path.splitext(os.path.basename(path))[0]
    if report.get("rest") != main_report.get("rest") or report.get("order") != main_report.get("order"):
        errors.append(name + ": skeleton differs from the full character")
    share = report.get("triangles", 0) / max(main_report.get("triangles", 1), 1)
    report["share"] = share
    if share < ratio[0] or share > ratio[1]:
        errors.append(name + ": %.0f%% of the triangles" % (share * 100.0))
    for label, uri in report.get("images", {}).items():
        if not uri.startswith("../"):
            errors.append(name + ": image %s is not shared with the full character" % uri)
    return document


def read_clip(path):
    document, buffers = load(path)
    animation = document["animations"][0]
    tracks = {}
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        tracks[(channel["target"]["node"], channel["target"]["path"])] = (accessor(document, buffers, sampler["input"])[:, 0], accessor(document, buffers, sampler["output"]), sampler.get("interpolation", "LINEAR"))
    return document, tracks


def check_clip(path, character_report, loop, report, errors):
    name = os.path.splitext(os.path.basename(path))[0]

    def fail(message):
        errors.append(name + ": " + message)

    if len(name) > 42 or not name.isascii():
        fail("bad clip name")
    document, buffers = load(path)
    if len(document.get("animations", [])) != 1:
        fail("expected one animation, found %d" % len(document.get("animations", [])))
        return None
    if any("mesh" in node for node in document["nodes"]):
        fail("clip file contains a mesh")
    document, tracks = read_clip(path)
    nodes = document["nodes"]
    rest = character_report["rest"]
    for index, node in enumerate(nodes):
        if node["name"] not in rest:
            fail("node %s is not in the character" % node["name"])
            continue
        t, r, s = node_trs(node)
        reference = rest[node["name"]]
        if numpy.abs(t - reference[0]).max() > 1e-4 or min(numpy.abs(r - reference[1]).max(), numpy.abs(r + reference[1]).max()) > 1e-4 or numpy.abs(s - reference[2]).max() > 1e-4:
            fail("rest pose of %s differs from the character" % node["name"])
    if set(node["name"] for node in nodes) != set(rest):
        fail("bone set differs from the character")
    frames = None
    for (node, path_name), (times, values, mode) in tracks.items():
        if path_name not in ("translation", "rotation"):
            fail("%s channel on %s" % (path_name, nodes[node]["name"]))
        if mode != "LINEAR":
            fail("interpolation " + mode)
        frames = len(times) if frames is None else frames
        if len(times) != frames:
            fail("channels have different key counts")
        if len(times) > 1 and numpy.abs(numpy.diff(times) - 1.0 / 30.0).max() > 1e-4:
            fail("keys are not sampled at 30 fps")
        if abs(times[0]) > 1e-5:
            fail("clip does not start at time zero")
    report["frames"] = frames
    report["duration"] = (frames - 1) / 30.0
    parent = parents(document)
    for (node, path_name), (times, values, mode) in tracks.items():
        if node not in parent or nodes[node]["name"] == "root":
            if numpy.abs(values - values[0:1]).max() > 1e-6:
                fail("%s moves" % nodes[node]["name"])
    if loop:
        worst = 0.0
        shift = 0.0
        for (node, path_name), (times, values, mode) in tracks.items():
            if path_name == "rotation":
                a = values[0] / numpy.linalg.norm(values[0])
                c = values[-1] / numpy.linalg.norm(values[-1])
                worst = max(worst, math.degrees(2.0 * math.acos(min(1.0, abs(float(a @ c))))))
            else:
                shift = max(shift, float(numpy.abs(values[0] - values[-1]).max()))
        report["loop_error_degrees"] = worst
        report["loop_error_metres"] = shift
        if worst > 0.01 or shift > 1e-5:
            fail("loop does not close (%.4f degrees, %.6f m)" % (worst, shift))
    return document, tracks


def poses(document, tracks):
    nodes = document["nodes"]
    count = max(len(times) for times, values, mode in tracks.values())
    result = []
    for frame in range(count):
        translations = {node: values[min(frame, len(values) - 1)] for (node, path_name), (times, values, mode) in tracks.items() if path_name == "translation"}
        rotations = {node: values[min(frame, len(values) - 1)] for (node, path_name), (times, values, mode) in tracks.items() if path_name == "rotation"}
        matrices = world(document, translations, rotations)
        result.append({nodes[index]["name"]: matrices[index] for index in matrices})
    return result


def foot_points(frames, foot):
    offsets = {key: numpy.array([foot[key][0], foot[key][1], foot[key][2], 1.0]) for key in ("toe", "heel")}
    origin = numpy.array([to_blender(frame[foot["bone"]][:3, 3]) for frame in frames])
    toe = numpy.array([to_blender((frame[foot["bone"]] @ offsets["toe"])[:3]) for frame in frames])
    heel = numpy.array([to_blender((frame[foot["bone"]] @ offsets["heel"])[:3]) for frame in frames])
    return origin, toe, heel


def check_gait(document, tracks, clip, feet, report, errors):
    name = clip["name"]
    frames = poses(document, tracks)
    speed = clip["speed"]
    worst_slide = 0.0
    lowest = 0.0
    worst_lift = 0.0
    samples = 0
    for foot in feet:
        origin, toe, heel = foot_points(frames, foot)
        lowest = min(lowest, float(toe[:, 2].min()), float(heel[:, 2].min()))
        for start, end in clip["contacts"][foot["bone"]]:
            period = clip["duration"]
            for frame in range(len(frames) - 1):
                time = frame / 30.0
                inside = any(begin - 1e-6 <= time and time + 1.0 / 30.0 <= finish + 1e-6 for begin, finish in ((start, end), (start - period, end - period), (start + period, end + period)))
                if inside:
                    velocity = (origin[frame + 1] - origin[frame]) * 30.0
                    worst_slide = max(worst_slide, float(numpy.linalg.norm(velocity - numpy.array([0.0, speed, 0.0]))))
                    worst_lift = max(worst_lift, abs(float(toe[frame, 2])), abs(float(heel[frame, 2])), abs(float(toe[frame + 1, 2])), abs(float(heel[frame + 1, 2])))
                    samples += 1
    report["slide_percent"] = 100.0 * worst_slide / max(speed, 1e-6)
    report["slide_samples"] = samples
    report["lowest_point"] = lowest
    report["stance_height_error"] = worst_lift
    if samples == 0:
        errors.append(name + ": no stance samples")
    if worst_slide > 0.08 * speed:
        errors.append(name + ": feet slide %.1f%% of the speed" % report["slide_percent"])
    if lowest < -0.01:
        errors.append(name + ": a foot reaches %.3f m below the ground" % lowest)
    if worst_lift > 0.01:
        errors.append(name + ": stance feet are %.3f m off the ground" % worst_lift)


def run(root, manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    name = manifest["name"]
    errors = []
    summary = {"name": name, "clips": {}}
    main = {}
    character = os.path.join(root, "characters", name, name + ".gltf")
    check_character(character, main, errors, manifest.get("triangle_budget", [8000, 20000])[0], manifest.get("triangle_budget", [8000, 20000])[1])
    summary["character"] = {key: main.get(key) for key in ("bones", "triangles", "bounds", "images", "roughness_range")}
    lod = {}
    check_lod(os.path.join(root, "characters", name + "_lod", name + "_lod.gltf"), main, lod, errors)
    summary["lod"] = {key: lod.get(key) for key in ("bones", "triangles", "share", "images")}
    if main.get("bones") != manifest.get("bones"):
        errors.append("manifest bone count %s differs from the file (%s)" % (manifest.get("bones"), main.get("bones")))
    if main.get("triangles") != manifest.get("triangles") or lod.get("triangles") != manifest.get("lod_triangles"):
        errors.append("manifest triangle counts differ from the files")
    for bone in (manifest.get("head_bone"), manifest.get("jaw_bone")):
        if bone not in main.get("rest", {}):
            errors.append("manifest bone %s is not in the skeleton" % bone)
    for clip in manifest["clips"]:
        entry = {}
        file = os.path.join(root, "animations", clip["name"] + ".gltf")
        if not os.path.isfile(file):
            errors.append("missing clip " + clip["name"])
            continue
        loaded = check_clip(file, main, clip["loop"], entry, errors)
        if loaded is not None:
            if entry.get("frames") != clip["frames"] or abs(entry.get("duration", 0.0) - clip["duration"]) > 1e-3:
                errors.append(clip["name"] + ": manifest frame count or duration differs from the file")
            if clip.get("speed", 0.0) > 0.0:
                check_gait(loaded[0], loaded[1], clip, manifest["feet"], entry, errors)
        summary["clips"][clip["name"]] = entry
    summary["errors"] = errors
    return summary


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    result = run(arguments[0], arguments[1])
    print(json.dumps(result, indent=1))
    print("CHECK", result["name"], "PASSED" if not result["errors"] else "FAILED (%d)" % len(result["errors"]))
    sys.exit(1 if result["errors"] else 0)
