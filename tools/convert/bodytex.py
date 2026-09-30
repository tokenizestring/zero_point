import os
import time
import numpy

import anatomy
import skin
import texels
import headtex


def corner_frames(obj):
    mesh = obj.data
    mesh.calc_tangents(uvmap="UVMap")
    count = len(mesh.loops)
    tangent = numpy.empty(count * 3, dtype=numpy.float32)
    mesh.loops.foreach_get("tangent", tangent)
    sign = numpy.empty(count, dtype=numpy.float32)
    mesh.loops.foreach_get("bitangent_sign", sign)
    normal = numpy.empty(count * 3, dtype=numpy.float32)
    mesh.loops.foreach_get("normal", normal)
    mesh.free_tangents()
    return tangent.reshape(-1, 3, 3), sign.reshape(-1, 3), normal.reshape(-1, 3, 3)


def gradient(shapes, points, value=None, epsilon=2e-5):
    if value is None:
        value = anatomy.evaluate(shapes, points, 0.01)
    parts = [(anatomy.evaluate(shapes, points + numpy.array(offset) * epsilon, 0.01) - value) / epsilon for offset in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))]
    return value, numpy.stack(parts, axis=1)


def surface(shapes, points, chunk=400000):
    projected = numpy.empty_like(points)
    normals = numpy.empty_like(points)
    for start in range(0, len(points), chunk):
        block = points[start:start + chunk].astype(numpy.float64)
        value, grad = gradient(shapes, block)
        length2 = numpy.maximum(numpy.sum(grad * grad, axis=1), 1e-8)
        step = (value / length2)[:, None] * grad
        size = numpy.linalg.norm(step, axis=1)
        step *= numpy.minimum(1.0, 0.002 / numpy.maximum(size, 1e-12))[:, None]
        block = block - step
        value, grad = gradient(shapes, block)
        projected[start:start + chunk] = block
        normals[start:start + chunk] = grad / numpy.maximum(numpy.linalg.norm(grad, axis=1), 1e-9)[:, None]
    return projected, normals


def island_labels(triangles, uv):
    corners = numpy.asarray(triangles)
    count = len(corners)
    keys = []
    owners = []
    ends = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        low = numpy.minimum(corners[:, a], corners[:, b])
        high = numpy.maximum(corners[:, a], corners[:, b])
        swap = corners[:, a] > corners[:, b]
        first = numpy.where(swap[:, None], uv[:, b], uv[:, a])
        second = numpy.where(swap[:, None], uv[:, a], uv[:, b])
        keys.append(low.astype(numpy.int64) * (corners.max() + 1) + high)
        owners.append(numpy.arange(count))
        ends.append(numpy.concatenate([first, second], axis=1))
    keys = numpy.concatenate(keys)
    owners = numpy.concatenate(owners)
    ends = numpy.concatenate(ends)
    order = numpy.argsort(keys, kind='stable')
    keys, owners, ends = keys[order], owners[order], ends[order]
    same = (keys[1:] == keys[:-1]) & (numpy.abs(ends[1:] - ends[:-1]).max(axis=1) < 1e-6)
    parent = numpy.arange(count)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in zip(owners[:-1][same].tolist(), owners[1:][same].tolist()):
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[ra] = rb
    return numpy.array([find(index) for index in range(count)], dtype=numpy.int32)


class sheet:
    def __init__(self, uv, positions, frames, size, triangles=None):
        tangent, sign, normal = frames
        covered, owner, weights = texels.rasterize(uv, size)
        covered, owner, weights = texels.conservative(uv, size, covered, owner, weights)
        self.size = size
        self.covered = covered
        self.owner = owner
        self.weights = weights
        self.position = texels.interpolate(positions, owner, weights)
        n = texels.interpolate(normal, owner, weights)
        self.normal = n / numpy.maximum(numpy.linalg.norm(n, axis=1), 1e-9)[:, None]
        t = texels.interpolate(tangent, owner, weights)
        t = t - self.normal * numpy.sum(t * self.normal, axis=1)[:, None]
        self.tangent = t / numpy.maximum(numpy.linalg.norm(t, axis=1), 1e-9)[:, None]
        s = numpy.sign(texels.interpolate(sign, owner, weights))
        s[s == 0.0] = 1.0
        self.bitangent = numpy.cross(self.normal, self.tangent) * s[:, None]
        mask = numpy.zeros(size * size, dtype=bool)
        mask[covered] = True
        self.mask = mask.reshape(size, size)
        corners = numpy.asarray(uv, dtype=numpy.float64) * size
        e1 = positions[:, 1] - positions[:, 0]
        e2 = positions[:, 2] - positions[:, 0]
        d1 = corners[:, 1] - corners[:, 0]
        d2 = corners[:, 2] - corners[:, 0]
        determinant = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
        determinant = numpy.where(numpy.abs(determinant) < 1e-12, 1e-12, determinant)
        du = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / determinant[:, None]
        dv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / determinant[:, None]
        self.jacobian_u = du[owner].astype(numpy.float32)
        self.jacobian_v = dv[owner].astype(numpy.float32)
        self.guard = None
        if triangles is not None:
            labels = island_labels(triangles, numpy.asarray(uv, dtype=numpy.float64))
            guard = numpy.full(size * size, -1, dtype=numpy.int32)
            guard[covered] = labels[owner]
            self.guard = guard.reshape(size, size)
        print("BODY SHEET", size, "covered", len(covered))

    def image(self, values, fill=True):
        values = numpy.asarray(values, dtype=numpy.float32)
        channels = 1 if values.ndim == 1 else values.shape[1]
        result = numpy.zeros((self.size * self.size, channels), dtype=numpy.float32)
        result[self.covered] = values.reshape(len(self.covered), channels)
        result = result.reshape(self.size, self.size, channels)
        if fill:
            result = texels.fill(result, self.mask).astype(numpy.float32)
        return result

    def sample(self, image):
        return image.reshape(self.size * self.size, -1)[self.covered]

    def to_uv(self, direction, indices):
        ju = self.jacobian_u[indices].astype(numpy.float64)
        jv = self.jacobian_v[indices].astype(numpy.float64)
        a = numpy.sum(ju * ju, axis=1)
        b = numpy.sum(ju * jv, axis=1)
        c = numpy.sum(jv * jv, axis=1)
        pu = numpy.sum(ju * direction, axis=1)
        pv = numpy.sum(jv * direction, axis=1)
        determinant = numpy.maximum(a * c - b * b, 1e-24)
        return numpy.stack([(c * pu - b * pv) / determinant, (a * pv - b * pu) / determinant], axis=1)


def slopes(page, height):
    image = page.image(height)[:, :, 0].astype(numpy.float64)
    dx = numpy.zeros_like(image)
    dy = numpy.zeros_like(image)
    dx[:, 1:-1] = (image[:, 2:] - image[:, :-2]) * 0.5
    dy[1:-1, :] = (image[2:, :] - image[:-2, :]) * 0.5
    su = numpy.linalg.norm(page.jacobian_u, axis=1)
    sv = numpy.linalg.norm(page.jacobian_v, axis=1)
    return page.sample(dx[:, :, None])[:, 0] / numpy.maximum(su, 1e-7), page.sample(dy[:, :, None])[:, 0] / numpy.maximum(sv, 1e-7)


def anchor(zone, rng, floor=0.6):
    candidates = numpy.flatnonzero(zone > floor)
    if not len(candidates):
        return None
    return int(candidates[rng.integers(0, len(candidates))])


def surface_marks(points, normals, zones, color, name, scale, rng):
    spec = skin.marks[name]
    for zone, length in spec["scratches"]:
        index = anchor(zones[zone], rng)
        if index is None:
            continue
        origin = points[index]
        normal = normals[index]
        heading = rng.normal(0.0, 1.0, 3)
        heading -= normal * (heading @ normal)
        heading /= numpy.linalg.norm(heading)
        across = numpy.cross(normal, heading)
        local = points - origin
        near = numpy.flatnonzero((numpy.abs(local @ normal) < 0.012) & (numpy.linalg.norm(local, axis=1) < length * scale))
        if not len(near):
            continue
        along = local[near] @ heading / (length * scale * 0.5)
        wobble = (texels.noise(points[near], 260.0, 71, 2) - 0.5) * 0.0018
        side = numpy.abs(local[near] @ across + wobble)
        ends = texels.smoothstep(1.0, 0.7, numpy.abs(along))
        broken = texels.smoothstep(0.22, 0.42, texels.noise(points[near], 600.0, 73, 1))
        line = texels.smoothstep(0.0007, 0.00025, side) * ends * broken
        halo = texels.smoothstep(0.003, 0.0006, side) * ends
        color[near] = color[near] * (1.0 - line[:, None] * numpy.array([0.12, 0.5, 0.55])) * (1.0 + halo[:, None] * numpy.array([0.05, -0.04, -0.04]))
    for zone, radius in spec["bruises"]:
        index = anchor(zones[zone], rng)
        if index is None:
            continue
        origin = points[index]
        normal = normals[index]
        local = points - origin
        near = numpy.flatnonzero((numpy.linalg.norm(local, axis=1) < radius * scale * 1.6) & (normals @ normal > 0.3))
        if not len(near):
            continue
        q = numpy.linalg.norm(local[near], axis=1) / (radius * scale) + (texels.noise(points[near], 110.0, 83, 2) - 0.5) * 0.6
        blotch = texels.smoothstep(1.0, 0.25, q)
        core = texels.smoothstep(0.55, 0.0, q)
        color[near] = color[near] * (1.0 - blotch[:, None] * numpy.array([0.08, 0.13, 0.03])) * (1.0 - core[:, None] * numpy.array([0.07, 0.09, 0.0])) * (1.0 + (blotch - core)[:, None] * numpy.array([0.0, 0.025, -0.05]))
    return color


def hair_pass(page, normals, zones, color, name, scale, rng):
    directions = {"limb": zones["direction"], "down": numpy.tile(numpy.array([0.0, 0.0, -1.0]), (len(normals), 1))}
    inward = numpy.stack([-0.45 * numpy.sign(page.position[:, 0]), numpy.zeros(len(normals)), -numpy.ones(len(normals))], axis=1)
    directions["inward"] = inward
    total = numpy.zeros(len(normals))
    gain = min(1.0, page.size / 4096.0)
    for layer in skin.hair_layers[name]:
        field = headtex.tangent_toward(normals, directions[layer["field"]])
        cover = headtex.hair_strokes(page, zones[layer["zone"]], layer["count"], field, layer["length"], 0.75, (layer["opacity"][0] * gain, layer["opacity"][1] * gain), layer["bend"], 0.5, scale, rng)
        tone = texels.to_linear(numpy.asarray(layer["tone"]))
        color = color * (1.0 - cover[:, None]) + tone[None, :] * cover[:, None]
        total = numpy.maximum(total, cover)
    return color, total


def body_maps(setup, shapes, frames, uv, positions, triangles, occlusion, palette, seam_color, directory, prefix, size=4096, chunk=500000):
    started = time.time()
    name = setup["name"]
    scale = setup["figure"]["scale"]
    rng = numpy.random.default_rng(23 if name == "male" else 29)
    page = sheet(uv, positions, frames, size, triangles)
    points, normals = surface(shapes, page.position)
    print("BODY surface", round(time.time() - started, 1), "s")
    tangent_normal = numpy.stack([numpy.sum(normals * page.tangent, axis=1), numpy.sum(normals * page.bitangent, axis=1), numpy.sum(normals * page.normal, axis=1)], axis=1)
    ambient = numpy.ones(len(points)) if occlusion is None else page.sample(occlusion[:, :, None])[:, 0].astype(numpy.float64)
    color = numpy.empty((len(points), 3))
    roughness = numpy.empty(len(points))
    detail = numpy.empty(len(points))
    lines = numpy.empty(len(points))
    keys = ("forearm", "forearm_hair", "shin", "thigh", "upper_arm", "chest", "trail", "pubic", "armpit")
    zones = {key: numpy.empty(len(points), dtype=numpy.float32) for key in keys}
    zones["direction"] = numpy.empty((len(points), 3), dtype=numpy.float32)
    for start in range(0, len(points), chunk):
        stop = start + chunk
        block = points[start:stop]
        block_normals = normals[start:stop]
        nails = skin.nail_fields(shapes, block)
        c, r, d, n = skin.tones(block, block_normals, setup, nails, palette, skin.vein_field(shapes, block))
        local = skin.regions(block, block_normals, setup)
        skin_weight = 1.0 - n
        shaded, r = skin.pigment(c, r, local, palette)
        shaded, r, streaks = skin.weathering(block, block_normals, setup, shaded, r, ambient[start:stop], local, palette)
        color[start:stop] = c * n[:, None] + shaded * skin_weight[:, None]
        roughness[start:stop] = r
        detail[start:stop] = d
        lines[start:stop] = streaks
        for key in keys:
            zones[key][start:stop] = local[key] * skin_weight
        zones["direction"][start:stop] = local["direction"]
    print("BODY tones", round(time.time() - started, 1), "s")
    color = surface_marks(points, normals, zones, color, name, scale, rng)
    if seam_color is not None:
        field, reach = seam_color
        tint, weight = field(points)
        color = color * (1.0 - weight[:, None]) + tint * weight[:, None]
        head_now, head_scale = setup["placement"]
        local = (points - head_now) / head_scale
        close = numpy.flatnonzero((local[:, 2] > -0.05) & (local[:, 1] > 0.0))
        if len(close):
            look = headtex.looks[name]
            tone = texels.to_linear(numpy.asarray(look.get("scalp_tint") or look["hair"]["root"]))
            nape = texels.smoothstep(-0.008, 0.006, headtex.hairline(local[close], headtex.hairlines[name]))
            color[close] = color[close] * (1.0 - nape[:, None] * 0.86) + tone[None, :] * (nape[:, None] * 0.86)
    color, hair = hair_pass(page, normals, zones, color, name, scale, rng)
    print("BODY hair", round(time.time() - started, 1), "s")
    height = numpy.zeros(len(points))
    for start in range(0, len(points), chunk):
        stop = start + chunk
        height[start:stop] = skin.micro_height(points[start:stop], detail[start:stop], hair[start:stop])
    height += hair * 0.00002 - lines * 0.00003
    sx, sy = slopes(page, height)
    combined = numpy.stack([tangent_normal[:, 0] - sx, tangent_normal[:, 1] - sy, tangent_normal[:, 2]], axis=1)
    combined /= numpy.maximum(numpy.linalg.norm(combined, axis=1), 1e-9)[:, None]
    print("BODY detail", round(time.time() - started, 1), "s")
    headtex.save_image(os.path.join(directory, prefix + "_body_albedo.png"), page.image(texels.to_srgb(numpy.clip(color, 0.0, 1.0))), 'sRGB')
    headtex.save_image(os.path.join(directory, prefix + "_body_nor_gl.png"), page.image(headtex.encode_normal(combined)), 'Non-Color')
    orm = numpy.stack([numpy.clip(0.3 + 0.7 * ambient, 0.0, 1.0), numpy.clip(roughness + hair * 0.06, 0.05, 1.0), numpy.zeros(len(points))], axis=1)
    headtex.save_image(os.path.join(directory, prefix + "_body_orm.png"), page.image(orm), 'Non-Color')
    print("BODY maps done", round(time.time() - started, 1), "s")
    return page
