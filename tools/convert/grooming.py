import math
import os
import numpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import texels
import headtex

atlas_size = 2048
column = 1.0 / 8.0
tiles = {
    "long": [(index * column, 0.0, (index + 1) * column, 1.0) for index in range(6)],
    "short": [(6 * column, 0.0, 7 * column, 0.25), (6 * column, 0.25, 7 * column, 0.5), (7 * column, 0.0, 8 * column, 0.25), (7 * column, 0.25, 8 * column, 0.5)],
    "wisp": [(6 * column, 0.5, 6.5 * column, 1.0), (6.5 * column, 0.5, 7 * column, 1.0)],
    "curl": [(7 * column, 0.5, 8 * column, 0.625), (7 * column, 0.625, 8 * column, 0.75)],
    "fuzz": [(7 * column, 0.75, 8 * column, 0.875)],
    "band": [(7 * column, 0.875, 7.5 * column, 1.0)],
    "stubble": [(7.5 * column, 0.875, 8 * column, 1.0)],
}

palettes = {
    "female": {"root": (0.17, 0.11, 0.068), "mid": (0.29, 0.195, 0.12), "tip": (0.45, 0.33, 0.21), "body": (0.2, 0.14, 0.1), "band": (0.2, 0.17, 0.13)},
    "male": {"root": (0.105, 0.076, 0.056), "mid": (0.17, 0.122, 0.086), "tip": (0.29, 0.215, 0.15), "body": (0.17, 0.122, 0.09), "band": (0.2, 0.17, 0.13)},
}


def strand_tile(layers, rect, count, rng, palette, length=(0.75, 1.0), wave=0.02, clumps=5, thickness=(1.1, 1.9), spread=0.84, curl=0.0, fade=0.85, stagger=0.0, rooted=0.35):
    size = atlas_size
    u0, v0, u1, v1 = rect
    x0 = u0 * size
    y0 = v0 * size
    width = (u1 - u0) * size
    height = (v1 - v0) * size
    centers = rng.uniform(0.5 - spread * 0.5, 0.5 + spread * 0.5, clumps)
    points = []
    values = []
    root = texels.to_linear(numpy.asarray(palette["root"]))
    mid = texels.to_linear(numpy.asarray(palette["mid"]))
    tip = texels.to_linear(numpy.asarray(palette["tip"]))
    for strand in range(count):
        clump = centers[rng.integers(0, clumps)]
        start = numpy.clip(clump + rng.normal(0.0, spread * 0.22), 0.5 - spread * 0.5, 0.5 + spread * 0.5)
        reach = rng.uniform(length[0], length[1])
        steps = max(8, int(height * reach / 0.6))
        t = numpy.linspace(0.0, 1.0, steps)
        gather = rng.uniform(0.0, 0.7)
        across = start + (clump - start) * gather * t ** 1.5
        across = across + wave * (numpy.sin(t * rng.uniform(2.0, 7.0) * math.pi + rng.uniform(0.0, 6.28)) * t + rng.normal(0.0, 0.3) * t)
        if curl > 0.0:
            across = across + curl * numpy.sin(t * rng.uniform(5.0, 9.0) * math.pi + rng.uniform(0.0, 6.28))
        begin = rng.uniform(0.0, stagger) if rng.random() >= rooted else 0.0
        along = begin + t * (reach - begin)
        tone = rng.uniform(0.75, 1.25)
        shade = root[None, :] + (mid - root)[None, :] * texels.smoothstep(0.0, 0.45, along)[:, None]
        shade = shade + (tip - shade) * texels.smoothstep(0.45, 1.0, along)[:, None]
        thick = rng.uniform(thickness[0], thickness[1])
        alpha = (1.0 - fade * t ** 2.2) * thick * (0.25 + 0.75 * texels.smoothstep(0.0, 0.08, t))
        points.append(numpy.stack([x0 + numpy.clip(across, 0.03, 0.97) * width, y0 + (0.004 + along * 0.992) * height], axis=1))
        values.append(numpy.concatenate([alpha[:, None], shade * tone, (across - start)[:, None] * 0.0 + rng.uniform(-1.0, 1.0)], axis=1))
    points = numpy.concatenate(points)
    values = numpy.concatenate(values)
    weight, accumulation = headtex.splat(size, points, values, 1.25)
    layers["weight"] += weight
    layers["color"] += accumulation[:, :, :3]
    layers["side"] += accumulation[:, :, 3]


def solid_tile(layers, rect, color, rng, grain=0.25):
    size = atlas_size
    u0, v0, u1, v1 = rect
    x0, x1 = int(u0 * size), int(u1 * size)
    y0, y1 = int(v0 * size), int(v1 * size)
    noise = rng.uniform(1.0 - grain, 1.0 + grain, (y1 - y0, x1 - x0))
    rows = numpy.sin(numpy.arange(y1 - y0)[:, None] * 0.9) * 0.12 + 1.0
    layers["weight"][y0:y1, x0:x1] += 6.0
    layers["color"][y0:y1, x0:x1] += 6.0 * texels.to_linear(numpy.asarray(color))[None, None, :] * (noise * rows)[:, :, None]


def dot_tile(layers, rect, count, rng, palette):
    size = atlas_size
    u0, v0, u1, v1 = rect
    x = rng.uniform(u0 + 0.004, u1 - 0.004, count) * size
    y = rng.uniform(v0 + 0.004, v1 - 0.004, count) * size
    angle = rng.normal(-1.57, 0.5, count)
    points = []
    values = []
    tone = texels.to_linear(numpy.asarray(palette["body"]))
    for step in numpy.linspace(0.0, 1.0, 5):
        points.append(numpy.stack([x + numpy.cos(angle) * step * 3.2, y + numpy.sin(angle) * step * 3.2], axis=1))
        values.append(numpy.concatenate([numpy.full((count, 1), 1.6 * (1.0 - 0.5 * step)), numpy.tile(tone, (count, 1)) * rng.uniform(0.7, 1.3, (count, 1)), numpy.zeros((count, 1))], axis=1))
    weight, accumulation = headtex.splat(size, numpy.concatenate(points), numpy.concatenate(values), 1.1)
    layers["weight"] += weight
    layers["color"] += accumulation[:, :, :3]


shell_rect = (7 * column, 0.875, 8 * column, 1.0)


def periodic_dots(layers, rect, count, rng, palette):
    size = atlas_size
    u0, v0, u1, v1 = rect
    x0 = u0 * size
    y0 = v0 * size
    block = (u1 - u0) * size * 0.5
    x = rng.uniform(0.0, block, count)
    y = rng.uniform(0.0, block, count)
    angle = rng.normal(-1.57, 0.6, count)
    tone = texels.to_linear(numpy.asarray(palette["body"]))[None, :] * rng.uniform(0.6, 1.2, (count, 1))
    points = []
    values = []
    for step in numpy.linspace(0.0, 1.0, 4):
        for bx in (-1, 0, 1, 2):
            for by in (-1, 0, 1, 2):
                px = x + numpy.cos(angle) * step * 2.4 + bx * block
                py = y + numpy.sin(angle) * step * 2.4 + by * block
                keep = (px >= 1.0) & (px < 2.0 * block - 1.0) & (py >= 1.0) & (py < 2.0 * block - 1.0)
                points.append(numpy.stack([x0 + px[keep], y0 + py[keep]], axis=1))
                values.append(numpy.concatenate([numpy.full((int(keep.sum()), 1), 1.7 * (1.0 - 0.4 * step)), tone[keep], numpy.zeros((int(keep.sum()), 1))], axis=1))
    weight, accumulation = headtex.splat(size, numpy.concatenate(points), numpy.concatenate(values), 1.15)
    layers["weight"] += weight
    layers["color"] += accumulation[:, :, :3]


def stubble_shell(sheet, space, stored, names, period=0.009, lift=0.0007):
    s = space.scale
    skin = space.skin
    used = numpy.unique(skin.triangles)
    mask = numpy.zeros(len(skin.points))
    mask[used] = headtex.beard_mask(space.local(skin.points[used]))
    chosen = skin.triangles[numpy.all(mask[skin.triangles] > 0.8, axis=1)]
    indices, values = stored
    lifted = skin.points + skin.normals * lift * s
    for triangle in chosen:
        corners = lifted[triangle]
        normal = numpy.cross(corners[1] - corners[0], corners[2] - corners[0])
        axis = int(numpy.argmax(numpy.abs(normal)))
        flat = corners[:, [k for k in range(3) if k != axis]] / (period * s)
        flat = flat - numpy.floor(flat.min(axis=0))
        base = sheet.count
        for corner, vertex in enumerate(triangle):
            sheet.points.append(corners[corner])
            sheet.weights.append({names[indices[vertex, slot]]: float(values[vertex, slot]) for slot in range(indices.shape[1]) if values[vertex, slot] > 0.0})
        sheet.triangles.append((base, base + 1, base + 2))
        sheet.uv.append([(shell_rect[0] + (shell_rect[2] - shell_rect[0]) * min(flat[c, 0], 1.98) * 0.5, shell_rect[1] + (shell_rect[3] - shell_rect[1]) * min(flat[c, 1], 1.98) * 0.5) for c in range(3)])
        sheet.count += 3
    return len(chosen)


def hair_atlas(name, directory, prefix, seed=3):
    rng = numpy.random.default_rng(seed)
    size = atlas_size
    palette = palettes[name]
    layers = {"weight": numpy.zeros((size, size)), "color": numpy.zeros((size, size, 3)), "side": numpy.zeros((size, size))}
    long_counts = (150, 120, 95, 70, 48, 30)
    for index, rect in enumerate(tiles["long"]):
        strand_tile(layers, rect, long_counts[index], rng, palette, length=(0.7, 1.0) if index < 4 else (0.45, 1.0), wave=0.012 + 0.006 * index, clumps=4 + index, thickness=(1.2, 2.0), fade=0.8, stagger=0.07, rooted=0.2)
    for index, rect in enumerate(tiles["short"]):
        if name == "female":
            strand_tile(layers, rect, (66, 54, 44, 34)[index], rng, palette, length=(0.6, 1.0), wave=0.03, clumps=7, thickness=(1.0, 1.5), spread=0.92, fade=0.85, stagger=0.55, rooted=0.0)
        else:
            strand_tile(layers, rect, (70, 55, 42, 30)[index], rng, palette, length=(0.55, 1.0), wave=0.03 + 0.01 * index, clumps=5, thickness=(1.3, 2.1), fade=0.75, stagger=0.14)
    for index, rect in enumerate(tiles["wisp"]):
        strand_tile(layers, rect, (14, 8)[index], rng, palette, length=(0.5, 1.0), wave=0.05, clumps=3, thickness=(1.2, 1.8), spread=0.7, fade=0.7)
    body = dict(palette)
    body["root"] = palette["body"]
    body["mid"] = palette["body"]
    body["tip"] = tuple(c * 1.25 for c in palette["body"])
    for index, rect in enumerate(tiles["curl"]):
        strand_tile(layers, rect, (20, 12)[index], rng, body, length=(0.45, 1.0), wave=0.07, clumps=8, thickness=(1.0, 1.4), curl=0.045, fade=0.7, stagger=0.3, rooted=0.4)
    strand_tile(layers, tiles["fuzz"][0], 9, rng, body, length=(0.35, 1.0), wave=0.16, clumps=9, thickness=(1.0, 1.4), spread=0.8, curl=0.05, fade=0.5)
    if name == "male":
        periodic_dots(layers, shell_rect, 46, rng, palette)
    else:
        solid_tile(layers, tiles["band"][0], palette["band"], rng)
        dot_tile(layers, tiles["stubble"][0], 900, rng, palette)
    weight = layers["weight"]
    color = layers["color"] / numpy.maximum(weight, 1e-6)[:, :, None]
    alpha = numpy.clip(1.0 - numpy.exp(-weight * 1.5), 0.0, 1.0)
    known = weight > 0.05
    color = texels.fill(color * known[:, :, None], known)
    side = layers["side"] / numpy.maximum(weight, 1e-6)
    blurred = texels.blur(alpha, 2)
    gx = numpy.zeros_like(alpha)
    gx[:, 1:-1] = (blurred[:, 2:] - blurred[:, :-2]) * 0.5
    normal = numpy.stack([-gx * 2.2 + side * 0.12 * alpha, numpy.zeros_like(alpha), numpy.ones_like(alpha)], axis=2)
    normal /= numpy.linalg.norm(normal, axis=2)[:, :, None]
    occlusion = numpy.ones_like(alpha)
    roughness = numpy.clip(0.74 + 0.16 * (1.0 - blurred), 0.0, 1.0)
    rgba = numpy.concatenate([texels.to_srgb(numpy.clip(color, 0.0, 1.0)), alpha[:, :, None]], axis=2)
    headtex.save_image(os.path.join(directory, prefix + "_hair_albedo.png"), rgba, 'sRGB', True)
    headtex.save_image(os.path.join(directory, prefix + "_hair_orm.png"), numpy.stack([occlusion, roughness, numpy.zeros_like(alpha)], axis=2), 'Non-Color')
    headtex.save_image(os.path.join(directory, prefix + "_hair_nor_gl.png"), headtex.encode_normal(normal), 'Non-Color')
    print("ATLAS", prefix, "coverage", round(float((alpha > 0.5).mean()), 3))


class surface:
    def __init__(self, points, triangles):
        self.points = numpy.asarray(points, dtype=numpy.float64)
        self.triangles = numpy.asarray(triangles, dtype=numpy.int64)
        self.tree = BVHTree.FromPolygons(self.points.tolist(), self.triangles.tolist(), all_triangles=True)
        a = self.points[self.triangles[:, 0]]
        b = self.points[self.triangles[:, 1]]
        c = self.points[self.triangles[:, 2]]
        cross = numpy.cross(b - a, c - a)
        self.areas = 0.5 * numpy.linalg.norm(cross, axis=1)
        normals = numpy.zeros_like(self.points)
        for k in range(3):
            numpy.add.at(normals, self.triangles[:, k], cross)
        self.normals = normals / numpy.maximum(numpy.linalg.norm(normals, axis=1), 1e-12)[:, None]

    def sample(self, count, density, rng):
        centers = self.points[self.triangles].mean(axis=1)
        weight = self.areas * numpy.clip(density(centers), 0.0, None)
        if weight.sum() <= 0.0:
            return numpy.zeros((0, 3)), numpy.zeros((0, 3))
        chosen = rng.choice(len(self.triangles), size=count, p=weight / weight.sum())
        r1 = numpy.sqrt(rng.uniform(0.0, 1.0, count))
        r2 = rng.uniform(0.0, 1.0, count)
        bary = numpy.stack([1.0 - r1, r1 * (1.0 - r2), r1 * r2], axis=1)
        corners = self.triangles[chosen]
        return numpy.einsum('nk,nkj->nj', bary, self.points[corners]), self.unit(numpy.einsum('nk,nkj->nj', bary, self.normals[corners]))

    def unit(self, vectors):
        return vectors / numpy.maximum(numpy.linalg.norm(vectors, axis=1), 1e-12)[:, None]

    def closest(self, point):
        location, normal, index, distance = self.tree.find_nearest(Vector(point))
        return self.resolved(location, index)

    def resolved(self, location, index):
        location = numpy.array(location)
        corners = self.triangles[index]
        a, b, c = self.points[corners]
        weights = faces_barycentric(location, a, b, c)
        smooth = weights @ self.normals[corners]
        return location, smooth / max(float(numpy.linalg.norm(smooth)), 1e-12), index, weights

    def ray(self, origin, direction):
        location, normal, index, distance = self.tree.ray_cast(Vector(origin), Vector(direction))
        if location is None:
            return None
        return self.resolved(location, index)


def faces_barycentric(p, a, b, c):
    v0 = b - a
    v1 = c - a
    v2 = p - a
    d00 = v0 @ v0
    d01 = v0 @ v1
    d11 = v1 @ v1
    d20 = v2 @ v0
    d21 = v2 @ v1
    denominator = max(d00 * d11 - d01 * d01, 1e-18)
    v = (d11 * d20 - d01 * d21) / denominator
    w = (d00 * d21 - d01 * d20) / denominator
    return numpy.clip(numpy.array([1.0 - v - w, v, w]), 0.0, 1.0)


def thin(points, spacing, rng):
    order = rng.permutation(len(points))
    kept = []
    grid = {}
    for index in order:
        key = tuple(numpy.floor(points[index] / spacing).astype(int))
        near = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for other in grid.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        if numpy.linalg.norm(points[other] - points[index]) < spacing:
                            near = True
        if not near:
            kept.append(index)
            grid.setdefault(key, []).append(index)
    return numpy.array(kept, dtype=numpy.int64)


class cards:
    def __init__(self):
        self.points = []
        self.triangles = []
        self.uv = []
        self.weights = []
        self.count = 0

    def ribbon(self, path, normals, widths, rect, weights, bow=0.0):
        path = numpy.asarray(path, dtype=numpy.float64)
        steps = len(path)
        tangent = numpy.gradient(path, axis=0)
        tangent /= numpy.maximum(numpy.linalg.norm(tangent, axis=1), 1e-12)[:, None]
        across = numpy.cross(tangent, normals)
        across /= numpy.maximum(numpy.linalg.norm(across, axis=1), 1e-12)[:, None]
        lengths = numpy.r_[0.0, numpy.cumsum(numpy.linalg.norm(path[1:] - path[:-1], axis=1))]
        along = lengths / max(lengths[-1], 1e-9)
        u0, v0, u1, v1 = rect
        columns = 3 if bow > 0.0 else 2
        base = self.count
        for index in range(steps):
            half = widths[index] * 0.5
            for col in range(columns):
                s = col / (columns - 1)
                lift = bow * widths[index] * (1.0 - (2.0 * s - 1.0) ** 2)
                self.points.append(path[index] + across[index] * (s * 2.0 - 1.0) * half + normals[index] * lift)
                self.weights.append(weights[index] if isinstance(weights, list) else weights)
        for index in range(steps - 1):
            for col in range(columns - 1):
                a = base + index * columns + col
                b = a + 1
                c = a + columns + 1
                d = a + columns
                for corners in ((a, b, c), (a, c, d)):
                    self.triangles.append(corners)
                    row = []
                    for corner in corners:
                        local = corner - base
                        s = (local % columns) / (columns - 1)
                        t = along[local // columns]
                        row.append((u0 + (u1 - u0) * (0.02 + 0.96 * s), v0 + (v1 - v0) * (0.004 + 0.992 * t)))
                    self.uv.append(row)
        self.count += steps * columns

    def quad(self, corners, rect, weights):
        base = self.count
        for corner in corners:
            self.points.append(numpy.asarray(corner, dtype=numpy.float64))
            self.weights.append(weights)
        u0, v0, u1, v1 = rect
        coordinates = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
        for order in ((0, 1, 2), (0, 2, 3)):
            self.triangles.append(tuple(base + k for k in order))
            self.uv.append([coordinates[k] for k in order])
        self.count += 4

    def arrays(self, names):
        if not self.points:
            return numpy.zeros((0, 3)), numpy.zeros((0, 3), dtype=numpy.int64), numpy.zeros((0, 3, 2)), numpy.zeros((0, 4), dtype=numpy.int32), numpy.zeros((0, 4), dtype=numpy.float32)
        points = numpy.array(self.points)
        triangles = numpy.array(self.triangles, dtype=numpy.int64).reshape(-1, 3)
        uv = numpy.array(self.uv).reshape(-1, 3, 2)
        indices = numpy.zeros((len(points), 4), dtype=numpy.int32)
        values = numpy.zeros((len(points), 4), dtype=numpy.float32)
        for vertex, entry in enumerate(self.weights):
            ordered = sorted(entry.items(), key=lambda item: -item[1])[:4]
            total = sum(weight for bone, weight in ordered)
            for slot, (bone, weight) in enumerate(ordered):
                indices[vertex, slot] = names.index(bone)
                values[vertex, slot] = weight / total
        return points, triangles, uv, indices, values


def subset(arrays, mask):
    points, triangles, uv, indices, values = arrays
    if not mask.any():
        return numpy.zeros((0, 3)), numpy.zeros((0, 3), dtype=numpy.int64), numpy.zeros((0, 3, 2)), numpy.zeros((0, 4), dtype=numpy.int32), numpy.zeros((0, 4), dtype=numpy.float32)
    used, compact = numpy.unique(triangles[mask], return_inverse=True)
    return points[used], compact.reshape(-1, 3), uv[mask], indices[used], values[used]


def merged(first, second):
    if not len(second[1]):
        return first
    if not len(first[1]):
        return second
    return numpy.concatenate([first[0], second[0]]), numpy.concatenate([first[1], second[1] + len(first[0])]), numpy.concatenate([first[2], second[2]]), numpy.concatenate([first[3], second[3]]), numpy.concatenate([first[4], second[4]])


def pick(group, rng, bias=None):
    options = tiles[group]
    if bias is None:
        return options[rng.integers(0, len(options))]
    return options[int(numpy.clip(round(bias + rng.normal(0.0, 0.8)), 0, len(options) - 1))]


scalps = headtex.hairlines
brow_lines = {
    "female": headtex.looks["female"]["brows"],
    "male": [(0.012, 0.1105, 0.0055), (0.022, 0.1125, 0.006), (0.032, 0.1138, 0.0058), (0.043, 0.1135, 0.0048), (0.053, 0.1115, 0.0034), (0.059, 0.109, 0.0024)],
}
lash_tiles = {"upper": (0.0, 0.0, 1.0, 0.5), "lower": (0.0, 0.5, 1.0, 0.75), "brow": [(index / 8.0, 0.75, (index + 1) / 8.0, 1.0) for index in range(8)]}
lash_size = (1024, 512)


def lash_atlas(name, directory, prefix, seed=9):
    rng = numpy.random.default_rng(seed)
    width, height = lash_size
    weight = numpy.zeros((height, width))
    points = []
    values = []

    def strand(x, y, direction, length, bend, thick):
        steps = max(6, int(length / 0.5))
        t = numpy.linspace(0.0, 1.0, steps)
        px = x + direction[0] * length * t + bend * length * t * t
        py = y + direction[1] * length * t
        points.append(numpy.stack([px, py], axis=1))
        values.append((thick * (1.0 - 0.75 * t ** 1.5))[:, None])

    u0, v0, u1, v1 = lash_tiles["upper"]
    for index in range(150 if name == "female" else 120):
        x = rng.uniform(8.0, width - 8.0)
        reach = rng.uniform(0.62, 1.0) * (0.75 + 0.25 * math.sin(math.pi * x / width))
        strand(x, v0 * height + 2.0, (rng.normal(0.0, 0.1), 1.0), (v1 - v0) * height * reach * 0.96, rng.normal(0.0, 0.06), rng.uniform(1.5, 2.4) * (1.15 if name == "female" else 1.0))
    u0, v0, u1, v1 = lash_tiles["lower"]
    for index in range(58 if name == "female" else 46):
        x = rng.uniform(8.0, width - 8.0)
        strand(x, v0 * height + 2.0, (rng.normal(0.0, 0.18), 1.0), (v1 - v0) * height * rng.uniform(0.45, 0.95), rng.normal(0.0, 0.08), rng.uniform(1.1, 1.7))
    for rect in lash_tiles["brow"]:
        u0, v0, u1, v1 = rect
        for index in range(rng.integers(3, 6)):
            x = rng.uniform(u0 * width + 24.0, u1 * width - 24.0)
            strand(x, v0 * height + 3.0, (rng.normal(0.0, 0.12), 1.0), (v1 - v0) * height * rng.uniform(0.6, 0.95), rng.normal(0.0, 0.1), rng.uniform(1.2, 1.7))
    size = max(width, height)
    splat_weight, accumulation = headtex.splat(size, numpy.concatenate(points), numpy.concatenate(values), 1.2)
    alpha = numpy.clip(1.0 - numpy.exp(-splat_weight[:height, :width] * 1.6), 0.0, 1.0)
    tone = texels.to_srgb(texels.to_linear(numpy.asarray(palettes[name]["root"])) * (0.45 if name == "female" else 0.7))
    rgba = numpy.concatenate([numpy.tile(tone, (height, width, 1)), alpha[:, :, None]], axis=2)
    headtex.save_image(os.path.join(directory, prefix + "_lashes_albedo.png"), rgba, 'sRGB', True)


def lid_ring(space, center, radius):
    points = space.skin.points
    triangles = space.skin.triangles
    near = numpy.linalg.norm(points[triangles].mean(axis=1) - center, axis=1) < radius * 1.6
    chosen = triangles[near]
    distance = numpy.linalg.norm(points - center, axis=1) - radius
    crossings = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        ia = chosen[:, a]
        ib = chosen[:, b]
        cross = (distance[ia] > 0.0) != (distance[ib] > 0.0)
        t = distance[ia[cross]] / (distance[ia[cross]] - distance[ib[cross]])
        crossings.append(points[ia[cross]] + (points[ib[cross]] - points[ia[cross]]) * t[:, None])
    crossings = numpy.concatenate(crossings)
    crossings = crossings[crossings[:, 1] < center[1] - radius * 0.35]
    return crossings


def lashes(sheet, space, eyes, eye_radius, lookup, rng):
    s = space.scale
    for center in eyes:
        side = 1.0 if center[0] > 0.0 else -1.0
        ring = lid_ring(space, center, eye_radius * 1.05)
        if len(ring) < 12:
            continue
        q = ring - center
        middle = numpy.median(q[:, 2])
        for upper in (True, False):
            chosen = q[:, 2] > middle if upper else q[:, 2] <= middle
            subset = ring[chosen]
            order = numpy.argsort(subset[:, 0] * side)
            subset = subset[order]
            bins = numpy.linspace(subset[0, 0], subset[-1, 0], 15)
            roots = []
            for index in range(14):
                low, high = sorted((bins[index], bins[index + 1]))
                members = subset[(subset[:, 0] >= low) & (subset[:, 0] <= high)]
                if len(members):
                    roots.append(members[numpy.argmax(members[:, 2])] if upper else members[numpy.argmin(members[:, 2])])
            if len(roots) < 5:
                continue
            roots = numpy.array(roots)
            count = len(roots)
            length = (0.0095 if upper else 0.005) * s * (1.12 if space.name == "female" else 1.0)
            rect = lash_tiles["upper"] if upper else lash_tiles["lower"]
            rows = 3
            base = sheet.count
            weights = lookup(roots[count // 2])
            for index, root in enumerate(roots):
                along = index / (count - 1)
                outward = (root - center) / numpy.linalg.norm(root - center)
                vertical = numpy.array([0.0, 0.0, 1.0 if upper else -1.0])
                lateral = numpy.array([side, 0.0, 0.0]) * (along - 0.35) * 0.6
                taper = (0.5 + 0.5 * math.sin(math.pi * min(max(along, 0.06), 0.94))) * (0.8 + 0.3 * along)
                forward = numpy.array([0.0, -1.0, 0.0])
                for row in range(rows):
                    t = row / (rows - 1)
                    direction = outward * 0.45 + forward * (0.75 - 0.3 * t) + vertical * ((-0.1 if upper else 0.25) + 1.15 * t * t) + lateral
                    direction /= numpy.linalg.norm(direction)
                    sheet.points.append(root + outward * 0.0003 * s + direction * length * taper * t)
                    sheet.weights.append(weights)
            for index in range(count - 1):
                for row in range(rows - 1):
                    a = base + index * rows + row
                    b = a + rows
                    c = b + 1
                    d = a + 1
                    for corners in ((a, b, c), (a, c, d)):
                        sheet.triangles.append(corners)
                        row_uv = []
                        for corner in corners:
                            local = corner - base
                            u = (local // rows) / (count - 1)
                            v = (local % rows) / (rows - 1)
                            row_uv.append((rect[0] + (rect[2] - rect[0]) * (0.01 + 0.98 * u), rect[1] + (rect[3] - rect[1]) * (0.01 + 0.98 * v)))
                        sheet.uv.append(row_uv)
            sheet.count += count * rows


def detect_brows(space, uv, albedo, fallback):
    height, width = albedo.shape[:2]
    xs = numpy.linspace(0.008, 0.066, 30)
    zs = numpy.linspace(0.1065, 0.14, 35)
    levels = numpy.full((2, len(xs), len(zs)), numpy.nan)
    for slot, side in enumerate((1.0, -1.0)):
        for i, x in enumerate(xs):
            for j, z in enumerate(zs):
                hit = space.skin.ray(space.world((side * x, -0.25, z)), (0.0, 1.0, 0.0))
                if hit is None:
                    continue
                location, normal, index, weights = hit
                coordinate = weights @ uv[index]
                column = min(max(int(coordinate[0] * width), 0), width - 1)
                row = min(max(int(coordinate[1] * height), 0), height - 1)
                levels[slot, i, j] = float(albedo[row, column, :3] @ numpy.array([0.2126, 0.7152, 0.0722]))
    level = numpy.nanmean(levels, axis=0)
    skin_level = numpy.nanpercentile(level, 75)
    dark = numpy.clip(1.0 - level / skin_level, 0.0, 1.0)
    dark = numpy.nan_to_num(dark)
    line = []
    for i, x in enumerate(xs):
        profile = numpy.convolve(dark[i], numpy.ones(5) / 5.0, mode="same")
        peak = int(numpy.argmax(profile))
        if profile[peak] < 0.2:
            continue
        window = numpy.abs(zs - zs[peak]) < 0.0065
        weight = numpy.where(window, numpy.clip(dark[i] - 0.12, 0.0, None), 0.0)
        if weight.sum() <= 0.0:
            continue
        center = float((weight * zs).sum() / weight.sum())
        spread = float(numpy.sqrt((weight * (zs - center) ** 2).sum() / weight.sum()))
        line.append((float(x), center, float(numpy.clip(spread * 2.6, 0.002, 0.0075))))
    if len(line) < 12:
        print("BROWS detection failed, using the default line", len(line))
        return fallback
    line = line[1:-1]
    found_x = numpy.array([p[0] for p in line])
    found_z = numpy.array([p[1] for p in line])
    keep = numpy.ones(len(line), dtype=bool)
    for attempt in range(3):
        curve = numpy.polyfit(found_x[keep], found_z[keep], 2)
        keep = numpy.abs(numpy.polyval(curve, found_x) - found_z) < 0.003
        if keep.sum() < 8:
            print("BROWS detection unstable, using the default line")
            return fallback
    widths = numpy.convolve(numpy.pad([p[2] for p in line], 2, mode="edge"), numpy.ones(5) / 5.0, mode="valid")
    line = [(float(x), float(numpy.polyval(curve, x)), float(w)) for x, w in zip(found_x, widths)]
    print("BROWS detected", len(line), "from x", round(line[0][0], 4), "to", round(line[-1][0], 4), "z", round(line[0][1], 4), round(line[len(line) // 2][1], 4), round(line[-1][1], 4), "width", round(float(numpy.mean(widths)), 4))
    return line


def brows(sheet, space, lookup, rng, line=None):
    s = space.scale
    line = line or brow_lines[space.name]
    xs = numpy.array([p[0] for p in line])
    zs = numpy.array([p[1] for p in line])
    widths = numpy.array([p[2] for p in line])
    male = space.name == "male"
    count = 36 if male else 28
    for side in (1.0, -1.0):
        for index in range(count):
            x = xs[0] + (xs[-1] - xs[0]) * (index + rng.uniform(0.0, 1.0)) / count
            z = numpy.interp(x, xs, zs) + (((index * 7) % 5) / 4.0 - 0.5 + rng.uniform(-0.1, 0.1)) * 0.8 * numpy.interp(x, xs, widths)
            along = (x - xs[0]) / (xs[-1] - xs[0])
            hit = space.skin.ray(space.world((side * x, -0.25, z)), (0.0, 1.0, 0.0))
            if hit is None:
                continue
            location, normal, tri, bary = hit
            up = numpy.array([0.35 * side, 0.0, 1.0])
            out = numpy.array([side, 0.0, 0.35])
            down = numpy.array([side, 0.0, -0.3])
            a = float(texels.smoothstep(0.0, 0.3, along))
            b = float(texels.smoothstep(0.6, 1.0, along))
            heading = up * (1.0 - a) + out * a * (1.0 - b) + down * b
            heading = heading - normal * (heading @ normal)
            heading /= max(numpy.linalg.norm(heading), 1e-9)
            across = numpy.cross(normal, heading)
            shrink = 1.0 - 0.35 * b
            length = rng.uniform(0.0055, 0.0085) * s * shrink * (1.0 if male else 0.85)
            half = rng.uniform(0.0012, 0.0019) * s * (1.0 if male else 0.85)
            root = location - heading * length * 0.35 + normal * 0.00025 * s
            tip = location + heading * length * 0.65 + normal * rng.uniform(0.0004, 0.0008) * s
            sheet.quad([root - across * half, root + across * half, tip + across * half, tip - across * half], lash_tiles["brow"][rng.integers(0, 8)], lookup(location))


class head_space:
    def __init__(self, points, triangles, head_now, scale, name, everything=None):
        self.head_now = numpy.asarray(head_now, dtype=numpy.float64)
        self.scale = scale
        self.name = name
        self.skin = surface(points, triangles)
        self.follow = self.skin if everything is None else surface(points, everything)
        centers = self.follow.points[self.follow.triangles].mean(axis=1)
        local = self.local(centers)
        above = headtex.hairline(local, scalps[name])
        ear = headtex.soft(local, (0.078, 0.004, 0.08), (0.018, 0.026, 0.032), True, 1.0)
        outer = numpy.linalg.norm(local - numpy.array([0.0, -0.01, 0.1]), axis=1) > 0.06
        keep = (above > -0.02) & (ear < 0.35) & outer & (local[:, 2] > -0.06)
        used, remap = numpy.unique(self.follow.triangles[keep], return_inverse=True)
        self.scalp = surface(self.follow.points[used], remap.reshape(-1, 3))

    def local(self, points):
        return (numpy.asarray(points, dtype=numpy.float64) - self.head_now) / self.scale

    def world(self, local):
        return self.head_now + numpy.asarray(local, dtype=numpy.float64) * self.scale

    def inside(self, points):
        return headtex.hairline(self.local(points), scalps[self.name])


def scalp_roots(space, count, spacing, rng, margin=0.002, limit=None, region=None):
    def density(centers):
        depth = space.inside(centers)
        chosen = depth > margin
        if limit is not None:
            chosen &= depth < limit
        if region is not None:
            chosen &= region(space.local(centers))
        return chosen.astype(numpy.float64)

    points, normals = space.scalp.sample(count * 8, density, rng)
    if not len(points):
        return points, normals
    kept = thin(points, spacing * space.scale, rng)
    return points[kept], normals[kept]


def flow_path(space, root, target, step, limit, stop, height, rng, wander=0.0):
    point = root.copy()
    location, normal, index, weights = space.scalp.closest(point)
    path = [location + normal * height(0.0)]
    normals = [normal]
    travelled = 0.0
    total = max(numpy.linalg.norm(target - point), 1e-6)
    drift = rng.normal(0.0, wander)
    for iteration in range(limit):
        to_target = target - location
        distance = numpy.linalg.norm(to_target)
        if distance < stop:
            break
        direction = to_target - normal * (to_target @ normal)
        direction /= max(numpy.linalg.norm(direction), 1e-9)
        side = numpy.cross(normal, direction)
        drift = drift * 0.85 + rng.normal(0.0, wander) * 0.5
        direction = direction + side * drift
        direction /= numpy.linalg.norm(direction)
        location, normal, index, weights = space.scalp.closest(location + direction * step)
        travelled += step
        path.append(location + normal * height(min(travelled / total, 1.0)))
        normals.append(normal)
    return path, normals


def female_hair(sheet, space, rng):
    s = space.scale
    anchor, outward, anchor_index, anchor_weights = space.scalp.closest(space.world((0.0, 0.112, 0.03)))
    tie = anchor + outward * 0.004 * s
    ring = 0.013 * s
    axis = outward * 0.8 + numpy.array([0.0, 0.0, -0.6])
    axis /= numpy.linalg.norm(axis)
    edge_roots, edge_normals = scalp_roots(space, 520, 0.004, rng, -0.006, 0.005)
    for root in edge_roots:
        base = rng.uniform(0.0003, 0.0009) * s

        def height(t, base=base):
            return base * (0.4 + 0.6 * min(t * 3.0, 1.0))

        path, path_normals = flow_path(space, root, tie, 0.0085 * s, int(rng.integers(4, 7)), 0.03 * s, height, rng, 0.12)
        if len(path) < 3:
            continue
        widths = numpy.full(len(path), rng.uniform(0.0075, 0.0105) * s)
        sheet.ribbon(path, numpy.array(path_normals), widths, pick("short", rng), {"Bip01 Head": 1.0}, 0.0)
    layers = (
        (380, 0.0054, 0.0125, (0.0005, 0.0012), 0.05, 1, 0.0, 0.007, 0.024),
        (300, 0.012, 0.03, (0.001, 0.002), 0.02, 0, 0.0, 0.015, None),
        (220, 0.016, 0.024, (0.0026, 0.004), 0.05, 2, 0.0, 0.015, None),
        (130, 0.022, 0.016, (0.004, 0.0075), 0.12, 4, 0.0, 0.02, None),
    )
    for count, spacing, width, lift, wander, tile_bias, bow, margin, limit in layers:
        roots, normals = scalp_roots(space, count, spacing, rng, margin, limit)
        for root in roots:
            base = rng.uniform(lift[0], lift[1]) * s
            extra = rng.uniform(0.0, lift[1]) * s

            def height(t, base=base, extra=extra):
                return base * min(t * 9.0, 1.0) + extra * math.sin(math.pi * t) * 0.6

            path, path_normals = flow_path(space, root, tie, 0.012 * s, 30, 0.03 * s, height, rng, wander)
            if len(path) < 2:
                continue
            last = path[-1]
            radial = last - tie
            radial -= axis * (radial @ axis)
            radial /= max(numpy.linalg.norm(radial), 1e-9)
            path.append(tie + radial * ring - axis * 0.004 * s)
            path_normals.append(radial)
            steps = len(path)
            t = numpy.linspace(0.0, 1.0, steps)
            widths = width * s * (1.0 - 0.72 * t ** 1.6) * rng.uniform(0.8, 1.2)
            sheet.ribbon(path, numpy.array(path_normals), widths, pick("long", rng, tile_bias), {"Bip01 Head": 1.0}, bow)
    across = numpy.cross(axis, numpy.array([0.0, 0.0, 1.0]))
    across /= numpy.linalg.norm(across)
    upward = numpy.cross(across, axis)
    knot = tie + axis * 0.019 * s
    radii = (0.034 * s, 0.031 * s, 0.025 * s)
    for strand in range(76):
        lean = rng.normal(0.0, 0.3, 2)
        pole = axis + across * lean[0] + upward * lean[1]
        pole /= numpy.linalg.norm(pole)
        first = numpy.cross(pole, upward)
        first /= numpy.linalg.norm(first)
        second = numpy.cross(pole, first)
        latitude = rng.uniform(-0.3, 1.3)
        begin = rng.uniform(0.0, 2.0 * math.pi)
        arc = rng.uniform(2.0, 4.6)
        puff = rng.uniform(0.9, 1.08)
        samples = 9
        path = []
        path_normals = []
        for k in range(samples):
            angle = begin + arc * k / (samples - 1)
            direction = (first * math.cos(angle) + second * math.sin(angle)) * math.cos(latitude) + pole * math.sin(latitude)
            parts = (direction @ across, direction @ upward, direction @ axis)
            path.append(knot + (across * parts[0] * radii[0] + upward * parts[1] * radii[1] + axis * parts[2] * radii[2]) * puff)
            facing = across * parts[0] / radii[0] + upward * parts[1] / radii[1] + axis * parts[2] / radii[2]
            path_normals.append(facing / numpy.linalg.norm(facing))
        widths = rng.uniform(0.013, 0.021) * s * (1.0 - 0.25 * numpy.linspace(0.0, 1.0, samples) ** 2)
        sheet.ribbon(path, numpy.array(path_normals), widths, pick("long", rng, 1.0), {"Bip01 Head": 1.0}, 0.12)
    for strand in range(9):
        spread = rng.uniform(0.0, 2.0 * math.pi)
        direction = across * math.cos(spread) * 0.8 + upward * (-abs(math.sin(spread)) - 0.3) + axis * rng.uniform(0.1, 0.6)
        direction /= numpy.linalg.norm(direction)
        parts = (direction @ across, direction @ upward, direction @ axis)
        root = knot + across * parts[0] * radii[0] + upward * parts[1] * radii[1] + axis * parts[2] * radii[2]
        length = rng.uniform(0.03, 0.06) * s
        samples = 6
        t = numpy.linspace(0.0, 1.0, samples)
        curl = numpy.cross(direction, numpy.array([0.0, 0.0, 1.0])) * rng.uniform(-0.35, 0.35)
        path = root[None, :] + direction[None, :] * (length * t)[:, None] + numpy.array([0.0, 0.0, -1.0])[None, :] * (length * 0.55 * t * t)[:, None] + curl[None, :] * (length * t * t)[:, None]
        side = numpy.cross(direction, numpy.array([0.0, 0.0, 1.0]))
        facing = numpy.cross(side, direction)
        facing /= max(numpy.linalg.norm(facing), 1e-9)
        widths = rng.uniform(0.006, 0.011) * s * (1.0 - 0.6 * t ** 1.5)
        sheet.ribbon(path, numpy.tile(facing, (samples, 1)), widths, pick("wisp", rng), {"Bip01 Head": 1.0}, 0.0)
    band_rows = 12
    for index in range(band_rows):
        a0 = 2.0 * math.pi * index / band_rows
        a1 = 2.0 * math.pi * (index + 1) / band_rows
        r = 0.0155 * s
        p0 = tie + axis * 0.004 * s + (across * math.cos(a0) + upward * math.sin(a0)) * r
        p1 = tie + axis * 0.004 * s + (across * math.cos(a1) + upward * math.sin(a1)) * r
        sheet.quad([p0 - axis * 0.004 * s, p1 - axis * 0.004 * s, p1 + axis * 0.004 * s, p0 + axis * 0.004 * s], tiles["band"][0], {"Bip01 Head": 1.0})
    fringe, fringe_normals = scalp_roots(space, 190, 0.0075, rng, -0.004, 0.007, lambda local: local[:, 1] < 0.035)
    for root in fringe:
        location, normal, index, weights = space.scalp.closest(root)
        back = tie - location
        back -= normal * (back @ normal)
        back /= max(numpy.linalg.norm(back), 1e-9)
        heading = back + numpy.cross(normal, back) * rng.normal(0.0, 0.5)
        heading /= numpy.linalg.norm(heading)
        length = rng.uniform(0.012, 0.028) * s
        samples = 4
        path = []
        path_normals = []
        point = location
        for k in range(samples):
            near, current, near_index, near_weights = space.follow.closest(point)
            path.append(near + current * (0.0006 + 0.0012 * k / (samples - 1)) * s)
            path_normals.append(current)
            point = near + heading * length / (samples - 1)
        widths = numpy.full(samples, rng.uniform(0.005, 0.009) * s)
        sheet.ribbon(path, numpy.array(path_normals), widths, pick("wisp", rng), {"Bip01 Head": 1.0}, 0.0)
    for side in (1.0, -1.0):
        for strand in range(3):
            root_local = numpy.array([side * rng.uniform(0.05, 0.066), rng.uniform(-0.085, -0.06), rng.uniform(0.135, 0.158)])
            location, normal, index, weights = space.scalp.closest(space.world(root_local))
            length = rng.uniform(0.07, 0.12) * s
            samples = 10
            path = []
            path_normals = []
            point = location + normal * 0.004 * s
            heading = numpy.array([side * rng.uniform(0.05, 0.3), rng.uniform(-0.35, -0.05), -1.0])
            heading /= numpy.linalg.norm(heading)
            phase = rng.uniform(0.0, 6.28)
            for k in range(samples):
                t = k / (samples - 1)
                sway = numpy.array([side * 0.006 * math.sin(phase + t * 5.0), -0.008 * math.sin(phase * 0.7 + t * 4.0) * t, 0.0]) * s
                candidate = point + heading * length * t + sway
                near, near_normal, near_index, near_weights = space.skin.closest(candidate)
                offset = candidate - near
                clearance = (0.005 + 0.006 * t) * s
                if offset @ near_normal < clearance:
                    candidate = near + near_normal * clearance
                path.append(candidate)
                path_normals.append(near_normal)
            widths = rng.uniform(0.005, 0.009) * s * (1.0 - 0.6 * numpy.linspace(0.0, 1.0, samples) ** 2)
            sheet.ribbon(path, numpy.array(path_normals), widths, pick("wisp", rng), {"Bip01 Head": 1.0}, 0.0)
    roots, normals = scalp_roots(space, 24, 0.028, rng)
    for root, normal in zip(roots, normals):
        location, normal, index, weights = space.scalp.closest(root)
        direction = tie - location
        direction -= normal * (direction @ normal)
        direction /= max(numpy.linalg.norm(direction), 1e-9)
        side = numpy.cross(normal, direction)
        heading = direction + side * rng.normal(0.0, 0.4) + normal * rng.uniform(0.04, 0.2)
        heading /= numpy.linalg.norm(heading)
        length = rng.uniform(0.016, 0.034) * s
        samples = 5
        path = [location + normal * 0.004 * s + heading * length * (k / (samples - 1)) - normal * 0.003 * s * (k / (samples - 1)) ** 2 for k in range(samples)]
        widths = numpy.full(samples, rng.uniform(0.004, 0.007) * s)
        sheet.ribbon(path, numpy.tile(normal, (samples, 1)), widths, pick("wisp", rng), {"Bip01 Head": 1.0}, 0.0)


def male_hair(sheet, space, rng):
    s = space.scale
    crown = space.world((0.012, 0.062, 0.2))
    layers = (
        (1100, 0.0072, (0.022, 0.036), (0.015, 0.021), (0.0006, 0.003), 0.26, "short", 0.1, 0.4, 4),
        (520, 0.0105, (0.028, 0.048), (0.012, 0.017), (0.004, 0.011), 0.5, "short", 0.0, 1.8, 5),
        (120, 0.02, (0.024, 0.044), (0.006, 0.01), (0.008, 0.018), 0.85, "wisp", 0.0, None, 5),
    )
    for count, spacing, length_range, width_range, lift_range, mess, group, bow, bias, samples in layers:
        roots, normals = scalp_roots(space, count, spacing, rng, 0.0005)
        for root in roots:
            location, normal, index, weights = space.scalp.closest(root)
            local = space.local(location)
            away = location - crown
            away -= normal * (away @ normal)
            away /= max(numpy.linalg.norm(away), 1e-9)
            swirl = numpy.cross(normal, away)
            forward = numpy.array([0.0, -1.0, 0.0])
            forward -= normal * (forward @ normal)
            top = float(texels.smoothstep(0.15, 0.19, numpy.array([local[2]]))[0])
            fringe = top * float(texels.smoothstep(-0.03, -0.075, numpy.array([local[1]]))[0])
            sideways = numpy.array([1.0 if local[0] > -0.01 else -1.0, 0.0, 0.0])
            sideways -= normal * (sideways @ normal)
            direction = away * (1.0 - 0.45 * top) + swirl * 0.3 + forward * (0.75 * top) + sideways * (0.45 * fringe)
            side = numpy.cross(normal, direction)
            direction = direction + side * rng.normal(0.0, mess)
            direction /= max(numpy.linalg.norm(direction), 1e-9)
            shorter = 0.6 + 0.4 * top
            edge = float(texels.smoothstep(0.0, 0.03, numpy.array([space.inside(location[None, :])[0]]))[0])
            length = rng.uniform(length_range[0], length_range[1]) * s * shorter * (0.55 + 0.45 * edge)
            lift = rng.uniform(lift_range[0], lift_range[1]) * s * (0.45 + 0.55 * top) * (1.0 + 1.3 * fringe)
            path = []
            path_normals = []
            point = location
            current = normal
            for k in range(samples):
                t = k / (samples - 1)
                near, current, near_index, near_weights = space.follow.closest(point)
                path.append(near + current * (0.0009 * s + lift * t ** 1.3))
                path_normals.append(current)
                point = near + direction * length / (samples - 1)
            widths = rng.uniform(width_range[0], width_range[1]) * s * (1.0 - 0.35 * numpy.linspace(0.0, 1.0, samples) ** 2) * (0.5 + 0.5 * edge)
            tile = pick("wisp", rng) if edge < 0.4 and rng.random() < 0.8 else pick(group, rng, bias)
            sheet.ribbon(path, numpy.array(path_normals), widths, tile, {"Bip01 Head": 1.0}, bow)
    fringe, fringe_normals = scalp_roots(space, 260, 0.0065, rng, -0.005, 0.005)
    for root in fringe:
        location, normal, index, weights = space.scalp.closest(root)
        away = location - crown
        away -= normal * (away @ normal)
        away /= max(numpy.linalg.norm(away), 1e-9)
        heading = away + numpy.cross(normal, away) * rng.normal(0.0, 0.6)
        heading /= numpy.linalg.norm(heading)
        length = rng.uniform(0.008, 0.018) * s
        samples = 3
        path = []
        path_normals = []
        point = location - heading * length * 0.4
        for k in range(samples):
            near, current, near_index, near_weights = space.follow.closest(point)
            path.append(near + current * (0.0006 + 0.0014 * k / (samples - 1)) * s)
            path_normals.append(current)
            point = near + heading * length / (samples - 1)
        widths = numpy.full(samples, rng.uniform(0.005, 0.008) * s)
        sheet.ribbon(path, numpy.array(path_normals), widths, pick("wisp", rng), {"Bip01 Head": 1.0}, 0.0)


def nearest_weights(body, stored, names):
    indices, values = stored

    def lookup(point):
        location, normal, index, weights = body.closest(point)
        corner = body.triangles[index][int(numpy.argmax(weights))]
        return {names[indices[corner, slot]]: float(values[corner, slot]) for slot in range(indices.shape[1]) if values[corner, slot] > 0.0}

    return lookup


def body_patch(sheet, body, lookup, density, count, spacing, direction, length_range, width_range, lift_range, group, rng, scale):
    points, normals = body.sample(count * 6, density, rng)
    if not len(points):
        return 0
    kept = thin(points, spacing, rng)[:count]
    for root in points[kept]:
        location, normal, index, weights = body.closest(root)
        heading = numpy.asarray(direction(location), dtype=numpy.float64)
        heading -= normal * (heading @ normal)
        heading /= max(numpy.linalg.norm(heading), 1e-9)
        side = numpy.cross(normal, heading)
        heading = heading + side * rng.normal(0.0, 0.45)
        heading /= numpy.linalg.norm(heading)
        length = rng.uniform(length_range[0], length_range[1]) * scale
        lift = rng.uniform(lift_range[0], lift_range[1]) * scale
        samples = 4
        path = []
        path_normals = []
        point = location
        current = normal
        for k in range(samples):
            t = k / (samples - 1)
            near, current, near_index, near_weights = body.closest(point)
            path.append(near + current * (0.0008 * scale + lift * math.sin(math.pi * min(t * 0.8 + 0.1, 1.0))))
            path_normals.append(current)
            point = near + heading * length / (samples - 1)
        widths = numpy.full(samples, rng.uniform(width_range[0], width_range[1]) * scale)
        sheet.ribbon(path, numpy.array(path_normals), widths, pick(group, rng), lookup(location), 0.0)
    return len(kept)


def body_hair(sheet, body, lookup, skeleton, figure_scale, name, rng, exclude=None):
    joints = skeleton["joints"]
    s = figure_scale
    pelvis = numpy.asarray(joints["Bip01 Pelvis"])
    top = pelvis[2] + (0.004 if name == "male" else -0.008) * s
    bottom = pelvis[2] - 0.088 * s
    half_top = (0.058 if name == "male" else 0.05) * s

    def pubic(centers):
        t = numpy.clip((centers[:, 2] - bottom) / (top - bottom), 0.0, 1.0)
        half = 0.012 * s + (half_top - 0.012 * s) * t ** 0.8
        inside = (numpy.abs(centers[:, 0]) < half) & (centers[:, 2] > bottom) & (centers[:, 2] < top) & (centers[:, 1] < pelvis[1] - 0.03 * s)
        if exclude is not None:
            inside &= ~exclude(centers)
        return inside * (0.35 + 0.65 * numpy.sin(numpy.pi * t) ** 0.5)

    counts = {}
    counts["pubic"] = body_patch(sheet, body, lookup, pubic, 110 if name == "male" else 90, 0.0074 * s, lambda p: numpy.array([-0.35 * numpy.sign(p[0]), 0.0, -1.0]), (0.01, 0.017), (0.008, 0.012), (0.001, 0.003), "curl", rng, s)
    if name == "male":
        for side in (1.0, -1.0):
            shoulder = numpy.asarray(joints["Bip01 L UpperArm"]) * numpy.array([side, 1.0, 1.0])
            pit = shoulder + numpy.array([-0.038 * side, 0.002, -0.082]) * s

            def armpit(centers, pit=pit):
                return (numpy.linalg.norm((centers - pit) / numpy.array([0.03, 0.04, 0.035]) / s, axis=1) < 1.0).astype(numpy.float64)

            counts["armpit"] = counts.get("armpit", 0) + body_patch(sheet, body, lookup, armpit, 34, 0.0075 * s, lambda p: numpy.array([0.0, 0.0, -1.0]), (0.014, 0.024), (0.012, 0.018), (0.002, 0.006), "curl", rng, s)
        chest_center = numpy.asarray(joints["Bip01 Spine2"]) + numpy.array([0.0, -0.1, 0.03]) * s

        def chest(centers):
            q = (centers - chest_center) / (numpy.array([0.085, 0.08, 0.07]) * s)
            return numpy.clip(1.0 - numpy.sum(q * q, axis=1), 0.0, 1.0) * (centers[:, 1] < chest_center[1] + 0.05 * s)

        counts["chest"] = body_patch(sheet, body, lookup, chest, 120, 0.009 * s, lambda p: numpy.array([-0.5 * numpy.sign(p[0]), 0.0, -1.0]), (0.008, 0.014), (0.007, 0.011), (0.0008, 0.003), "fuzz", rng, s)
        navel = numpy.asarray(joints["Bip01 Spine"]) + numpy.array([0.0, -0.1, 0.0]) * s

        def trail(centers):
            return ((numpy.abs(centers[:, 0]) < 0.014 * s) & (centers[:, 2] > top) & (centers[:, 2] < navel[2] + 0.06 * s) & (centers[:, 1] < pelvis[1] - 0.05 * s)).astype(numpy.float64)

        counts["trail"] = body_patch(sheet, body, lookup, trail, 30, 0.009 * s, lambda p: numpy.array([0.0, 0.0, -1.0]), (0.007, 0.012), (0.006, 0.009), (0.0008, 0.0025), "fuzz", rng, s)
        for side in ("L", "R"):
            for label, start, end, radius, low, high, amount, spacing in (("forearm", "Forearm", "Hand", 0.06, 0.12, 0.93, 60, 0.012), ("shin", "Calf", "Foot", 0.085, 0.1, 0.9, 85, 0.014)):
                a = numpy.asarray(joints["Bip01 %s %s" % (side, start)])
                b = numpy.asarray(joints["Bip01 %s %s" % (side, end)])
                axis = (b - a) / numpy.linalg.norm(b - a)
                span = float(numpy.linalg.norm(b - a))
                facing = numpy.asarray(skeleton["axes"]["Bip01 %s Hand" % side][1]) if label == "forearm" else numpy.zeros(3)

                def limb(centers, a=a, axis=axis, span=span, radius=radius, low=low, high=high, facing=facing):
                    along = (centers - a) @ axis
                    radial = centers - a - numpy.outer(along, axis)
                    away = numpy.linalg.norm(radial, axis=1)
                    return ((away < radius * s) & (along > low * span) & (along < high * span) & (radial @ facing <= 0.004)).astype(numpy.float64)

                counts[label] = counts.get(label, 0) + body_patch(sheet, body, lookup, limb, amount, spacing * s, lambda p, axis=axis: axis, (0.008, 0.013), (0.007, 0.01), (0.0008, 0.0028), "fuzz", rng, s)
    print("BODY HAIR cards", counts)
