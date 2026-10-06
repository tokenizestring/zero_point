import json
import os
import shutil
import sys

import numpy
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import texels


people = ("survivor_male", "survivor_female")
texture_slots = (("pbrMetallicRoughness", "baseColorTexture"), ("pbrMetallicRoughness", "metallicRoughnessTexture"), (None, "normalTexture"), (None, "occlusionTexture"), (None, "emissiveTexture"))
flat_normal = (128, 128, 255, 255)


def accessor(document, blob, index):
    info = document["accessors"][index]
    view = document["bufferViews"][info["bufferView"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[info["type"]]
    kind = {5126: numpy.float32, 5125: numpy.uint32, 5123: numpy.uint16, 5121: numpy.uint8}[info["componentType"]]
    start = view.get("byteOffset", 0) + info.get("byteOffset", 0)
    item = numpy.dtype(kind).itemsize * components
    stride = view.get("byteStride", item)
    raw = numpy.frombuffer(blob, dtype=numpy.uint8, count=stride * (info["count"] - 1) + item, offset=start)
    rows = numpy.lib.stride_tricks.as_strided(raw, shape=(info["count"], item), strides=(stride, 1))
    return numpy.frombuffer(numpy.ascontiguousarray(rows).tobytes(), dtype=kind).reshape(info["count"], components)


def material_index(document, suffix):
    for index, material in enumerate(document["materials"]):
        if material["name"].endswith(suffix):
            return index
    return -1


def region(document, blob, material, size):
    corners = []
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            if primitive["material"] == material:
                uv = accessor(document, blob, primitive["attributes"]["TEXCOORD_0"]).astype(numpy.float64)
                indices = accessor(document, blob, primitive["indices"]).reshape(-1, 3).astype(numpy.int64)
                corners.append(uv[indices])
    mask = numpy.zeros(size * size, dtype=bool)
    if corners:
        covered, _, _ = texels.rasterize(numpy.concatenate(corners), size)
        mask[covered] = True
    return mask.reshape(size, size)


def grow(mask, steps):
    for _ in range(steps):
        mask = mask | numpy.roll(mask, 1, 0) | numpy.roll(mask, -1, 0) | numpy.roll(mask, 1, 1) | numpy.roll(mask, -1, 1)
    return mask


def blank(source, target, mask, flat):
    image = numpy.array(Image.open(source))
    ring = grow(mask, 8) & ~mask
    fill = numpy.asarray(flat[:image.shape[2]] if flat else numpy.median(image[ring], axis=0), dtype=image.dtype)
    image[mask] = fill
    Image.fromarray(image).save(target)


def view_range(document, index):
    info = document["accessors"][index]
    view = document["bufferViews"][info["bufferView"]]
    start = view.get("byteOffset", 0) + info.get("byteOffset", 0)
    return start, view.get("byteStride", 12), info["count"]


def write_vectors(data, document, index, values):
    start, stride, count = view_range(document, index)
    for row in range(count):
        data[start + row * stride:start + row * stride + 12] = values[row].astype(numpy.float32).tobytes()


def clearance(points, shown, chunk=256):
    result = numpy.zeros(len(points))
    for start in range(0, len(points), chunk):
        block = points[start:start + chunk]
        result[start:start + chunk] = numpy.min(numpy.linalg.norm(block[:, None, :] - shown[None, :, :], axis=2), axis=1)
    return result


def drape(document, blob, garment, covered, iterations=60, depth=0.22, width=0.12):
    data = bytearray(blob)
    if garment < 0 or covered < 0:
        return bytes(data)
    skin = []
    rest = []
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            if primitive["material"] == covered:
                skin.append(accessor(document, blob, primitive["attributes"]["POSITION"]))
            elif primitive["material"] != garment and document["materials"][primitive["material"]].get("alphaMode", "OPAQUE") == "OPAQUE":
                rest.append(accessor(document, blob, primitive["attributes"]["POSITION"]))
    hidden_skin = numpy.concatenate(skin).astype(numpy.float64)
    low = hidden_skin.min(axis=0)
    high = hidden_skin.max(axis=0)
    middle = (low + high) * 0.5
    shown_skin = numpy.concatenate(rest).astype(numpy.float64)
    shown_skin = shown_skin[numpy.all((shown_skin > low - 0.1) & (shown_skin < high + 0.1), axis=1)]
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            if primitive["material"] != garment:
                continue
            positions = accessor(document, blob, primitive["attributes"]["POSITION"]).astype(numpy.float64)
            triangles = accessor(document, blob, primitive["indices"]).reshape(-1, 3).astype(numpy.int64)
            keys = numpy.round(positions * 20000.0).astype(numpy.int64)
            _, welded, inverse = numpy.unique(keys, axis=0, return_index=True, return_inverse=True)
            inverse = inverse.ravel()
            points = positions[welded].copy()
            faces = inverse[triangles]
            edges = numpy.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
            edges = numpy.concatenate([edges, edges[:, ::-1]])
            degree = numpy.bincount(edges[:, 0], minlength=len(points)).astype(numpy.float64)
            pairs, counts = numpy.unique(numpy.sort(edges[:len(edges) // 2], axis=1), axis=0, return_counts=True)
            border = numpy.zeros(len(points), dtype=bool)
            border[pairs[counts == 1].ravel()] = True
            region = (points[:, 2] > middle[2]) & (numpy.abs(points[:, 0] - middle[0]) < width) & (points[:, 1] > low[1] - 0.02) & (points[:, 1] < low[1] + depth) & ~border
            weight = numpy.zeros(len(points))
            weight[region] = numpy.clip((clearance(points[region], shown_skin) - 0.012) / 0.02, 0.0, 1.0)
            region &= weight > 0.0
            start = points.copy()
            for _ in range(iterations):
                total = numpy.zeros_like(points)
                numpy.add.at(total, edges[:, 0], points[edges[:, 1]])
                average = total / numpy.maximum(degree, 1.0)[:, None]
                points[region] = average[region]
            points = start + (points - start) * weight[:, None]
            normals = numpy.zeros_like(points)
            corners = points[faces]
            face_normals = numpy.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
            for corner in range(3):
                numpy.add.at(normals, faces[:, corner], face_normals)
            normals /= numpy.maximum(numpy.linalg.norm(normals, axis=1), 1e-9)[:, None]
            original_normals = accessor(document, blob, primitive["attributes"]["NORMAL"]).astype(numpy.float64)
            moved = region[inverse]
            final_normals = numpy.where(moved[:, None], normals[inverse], original_normals)
            write_vectors(data, document, primitive["attributes"]["POSITION"], points[inverse])
            write_vectors(data, document, primitive["attributes"]["NORMAL"], final_normals)
            print("draped", int(region.sum()), "garment points")
    return bytes(data)


def compact(document, blob):
    used = []
    for node in document["nodes"]:
        if "mesh" in node:
            for primitive in document["meshes"][node["mesh"]]["primitives"]:
                used.extend(primitive["attributes"].values())
                used.append(primitive["indices"])
    for skin in document.get("skins", []):
        used.append(skin["inverseBindMatrices"])
    used = sorted(set(used))
    accessor_remap = {old: new for new, old in enumerate(used)}
    data = bytearray()
    views = []
    accessors = []
    for old in used:
        info = dict(document["accessors"][old])
        view = dict(document["bufferViews"][info["bufferView"]])
        start = view.get("byteOffset", 0)
        while len(data) % 4:
            data.append(0)
        view["byteOffset"] = len(data)
        view["buffer"] = 0
        data += blob[start:start + view["byteLength"]]
        info["bufferView"] = len(views)
        views.append(view)
        accessors.append(info)
    document["accessors"] = accessors
    document["bufferViews"] = views
    document["buffers"] = [{"byteLength": len(data)}]
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            if all(index in accessor_remap for index in primitive["attributes"].values()) and primitive["indices"] in accessor_remap:
                primitive["attributes"] = {key: accessor_remap[index] for key, index in primitive["attributes"].items()}
                primitive["indices"] = accessor_remap[primitive["indices"]]
    referenced = {node["mesh"] for node in document["nodes"] if "mesh" in node}
    for index, mesh in enumerate(document["meshes"]):
        if index not in referenced:
            mesh["primitives"] = []
    for skin in document.get("skins", []):
        skin["inverseBindMatrices"] = accessor_remap[skin["inverseBindMatrices"]]
    return bytes(data)


def texture_infos(material):
    for group, slot in texture_slots:
        holder = material.get(group, {}) if group else material
        if slot in holder:
            yield holder[slot]


def keep_materials(document, kept):
    remap = {old: new for new, old in enumerate(kept)}
    document["materials"] = [document["materials"][index] for index in kept]
    for mesh in document["meshes"]:
        mesh["primitives"] = [primitive for primitive in mesh["primitives"] if primitive.get("material", 0) in remap]
        for primitive in mesh["primitives"]:
            primitive["material"] = remap[primitive.get("material", 0)]
    for node in document["nodes"]:
        if "mesh" in node and not document["meshes"][node["mesh"]]["primitives"]:
            node.pop("mesh")
            node.pop("skin", None)
    used = sorted({info["index"] for material in document["materials"] for info in texture_infos(material)})
    texture_remap = {old: new for new, old in enumerate(used)}
    document["textures"] = [document["textures"][index] for index in used]
    for material in document["materials"]:
        for info in texture_infos(material):
            info["index"] = texture_remap[info["index"]]
    images = sorted({texture["source"] for texture in document["textures"]})
    image_remap = {old: new for new, old in enumerate(images)}
    document["images"] = [document["images"][index] for index in images]
    for texture in document["textures"]:
        texture["source"] = image_remap[texture["source"]]


def write(document, blob, source, target, name, blanked):
    os.makedirs(target, exist_ok=True)
    document["buffers"][0]["uri"] = name + ".bin"
    with open(os.path.join(target, name + ".bin"), "wb") as handle:
        handle.write(blob)
    for image in document["images"]:
        if image["uri"] in blanked:
            blanked[image["uri"]](os.path.join(target, image["uri"]))
        else:
            shutil.copyfile(os.path.join(source, image["uri"]), os.path.join(target, image["uri"]))
    with open(os.path.join(target, name + ".gltf"), "w") as handle:
        json.dump(document, handle, indent=1)
    print("written", name, len(document["materials"]), "materials", len(document["images"]), "images")


def publish(source_root, raw_root, name):
    source = os.path.join(source_root, name)
    blob_path = os.path.join(source, name + ".bin")
    with open(os.path.join(source, name + ".gltf")) as handle:
        original = json.load(handle)
    with open(blob_path, "rb") as handle:
        blob = handle.read()
    body = material_index(original, "_body")
    covered = material_index(original, "_covered_body")
    pubic = material_index(original, "_pubic_hair")
    underwear = material_index(original, "_underwear")
    albedo = os.path.join(source, name + "_body_albedo.png")
    size = Image.open(albedo).size[0]
    hidden = grow(region(original, blob, covered, size), 3) & ~grow(region(original, blob, body, size), 1)
    print(name, "hiding", int(hidden.sum()), "body texels")
    blanked = {
        name + "_body_albedo.png": lambda target: blank(albedo, target, hidden, None),
        name + "_body_orm.png": lambda target: blank(os.path.join(source, name + "_body_orm.png"), target, hidden, None),
        name + "_body_nor_gl.png": lambda target: blank(os.path.join(source, name + "_body_nor_gl.png"), target, hidden, flat_normal),
    }
    clothed = json.loads(json.dumps(original))
    draped = drape(original, blob, underwear, covered)
    keep_materials(clothed, [index for index in range(len(original["materials"])) if index not in (covered, pubic)])
    write(clothed, compact(clothed, draped), source, os.path.join(raw_root, name), name, blanked)
    bare = json.loads(json.dumps(original))
    keep_materials(bare, [index for index in range(len(original["materials"])) if index != underwear])
    write(bare, compact(bare, blob), source, os.path.join(raw_root, name + "_nude"), name + "_nude", {})


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    source_root, raw_root = arguments[0], arguments[1]
    for name in people:
        publish(source_root, raw_root, name)


if __name__ == "__main__":
    main()
