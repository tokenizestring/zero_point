import math
import os
import time
import numpy
import fauna_hoofed_field as fields
import fauna_hoofed_render as render


def triangulate(model):
    points = model["points"]
    vertices = []
    loops = []
    owner = []
    cursor = 0
    for index, face in enumerate(model["faces"]):
        count = len(face)
        if count == 3:
            picks = [(0, 1, 2)]
        else:
            near = numpy.linalg.norm(points[face[0]] - points[face[2]]) <= numpy.linalg.norm(points[face[1]] - points[face[3]])
            picks = [(0, 1, 2), (0, 2, 3)] if near else [(0, 1, 3), (1, 2, 3)]
        for pick in picks:
            vertices.append([face[i] for i in pick])
            loops.append([cursor + i for i in pick])
            owner.append(index)
        cursor += count
    return numpy.array(vertices, dtype=numpy.int64), numpy.array(loops, dtype=numpy.int64), numpy.array(owner, dtype=numpy.int64)


def vertex_normals(points, triangles):
    corners = points[triangles]
    face = numpy.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    total = numpy.zeros_like(points)
    for index in range(3):
        a = corners[:, index]
        b = corners[:, (index + 1) % 3]
        c = corners[:, (index + 2) % 3]
        u = b - a
        v = c - a
        cosine = numpy.sum(u * v, axis=1) / numpy.maximum(numpy.linalg.norm(u, axis=1) * numpy.linalg.norm(v, axis=1), 1e-12)
        angle = numpy.arccos(numpy.clip(cosine, -1.0, 1.0))
        unit = face / numpy.maximum(numpy.linalg.norm(face, axis=1), 1e-12)[:, None]
        numpy.add.at(total, triangles[:, index], unit * angle[:, None])
    return total / numpy.maximum(numpy.linalg.norm(total, axis=1), 1e-12)[:, None]


def model_normals(model, triangles):
    normals = vertex_normals(model["points"], triangles)
    override = model.get("normal")
    if override is not None:
        chosen = ~numpy.isnan(override[:, 0])
        normals[chosen] = override[chosen]
    return normals


def engine_tangents(points, triangles, uv, normals):
    flat = triangles.reshape(-1)
    keys = numpy.column_stack([flat, numpy.round(uv.reshape(-1, 2) * 65535.0).astype(numpy.int64)])
    unique, inverse = numpy.unique(keys, axis=0, return_inverse=True)
    inverse = inverse.reshape(-1)
    corners = points[triangles]
    e1 = corners[:, 1] - corners[:, 0]
    e2 = corners[:, 2] - corners[:, 0]
    d1 = uv[:, 1] - uv[:, 0]
    d2 = uv[:, 2] - uv[:, 0]
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    good = numpy.abs(det) > 1e-14
    safe = numpy.where(good, det, 1.0)
    tangent = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / safe[:, None] * good[:, None]
    bitangent = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / safe[:, None] * good[:, None]
    tangent_sum = numpy.zeros((len(unique), 3))
    bitangent_sum = numpy.zeros((len(unique), 3))
    numpy.add.at(tangent_sum, inverse, numpy.repeat(tangent, 3, axis=0))
    numpy.add.at(bitangent_sum, inverse, numpy.repeat(bitangent, 3, axis=0))
    normal = normals[flat]
    t = tangent_sum[inverse]
    t = t - normal * numpy.sum(normal * t, axis=1)[:, None]
    length = numpy.linalg.norm(t, axis=1)
    fallback = numpy.cross(normal, numpy.array([0.0, 0.0, 1.0]))
    t = numpy.where(length[:, None] > 1e-9, t / numpy.maximum(length, 1e-12)[:, None], fallback)
    sign = numpy.where(numpy.sum(numpy.cross(normal, t) * bitangent_sum[inverse], axis=1) < 0.0, -1.0, 1.0)
    return t.reshape(-1, 3, 3), sign.reshape(-1, 3), tangent, bitangent


def rasterize(uv, size, corners=None):
    owner = numpy.full((size, size), -1, dtype=numpy.int32)
    weights = numpy.zeros((size, size, 3), dtype=numpy.float32)
    place = numpy.zeros((size, size, 3), dtype=numpy.float32)
    clash = 0
    pixel = uv * size - 0.5
    low = numpy.floor(pixel.min(axis=1)).astype(numpy.int64)
    high = numpy.ceil(pixel.max(axis=1)).astype(numpy.int64)
    for index in range(len(pixel)):
        x0 = max(int(low[index, 0]), 0)
        x1 = min(int(high[index, 0]), size - 1)
        y0 = max(int(low[index, 1]), 0)
        y1 = min(int(high[index, 1]), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        a, b, c = pixel[index]
        det = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(det) < 1e-10:
            continue
        gx = numpy.arange(x0, x1 + 1, dtype=numpy.float64)[None, :]
        gy = numpy.arange(y0, y1 + 1, dtype=numpy.float64)[:, None]
        w1 = ((gx - a[0]) * (c[1] - a[1]) - (gy - a[1]) * (c[0] - a[0])) / det
        w2 = ((b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])) / det
        w0 = 1.0 - w1 - w2
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if inside.any():
            view = owner[y0:y1 + 1, x0:x1 + 1]
            fresh = inside & (view < 0)
            core = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
            take = fresh | (inside & core)
            stacked = numpy.stack([w0, w1, w2], axis=-1)
            if corners is not None:
                where = (stacked @ corners[index]).astype(numpy.float32)
                spot = place[y0:y1 + 1, x0:x1 + 1]
                clash += int((core & (view >= 0) & (numpy.linalg.norm(spot - where, axis=-1) > 0.04)).sum())
                spot[take] = where[take]
            view[take] = index
            weights[y0:y1 + 1, x0:x1 + 1][take] = stacked[take]
    if corners is not None:
        print("RASTER", size, "overlapping texels", clash)
    return owner, weights


def hashed(ix, iy, iz, seed):
    h = (ix.astype(numpy.uint64) * numpy.uint64(374761393) + iy.astype(numpy.uint64) * numpy.uint64(668265263) + iz.astype(numpy.uint64) * numpy.uint64(2246822519) + numpy.uint64(seed * 974711 + 12345)) & numpy.uint64(0xFFFFFFFF)
    h = ((h ^ (h >> numpy.uint64(13))) * numpy.uint64(1274126177)) & numpy.uint64(0xFFFFFFFF)
    h = h ^ (h >> numpy.uint64(16))
    return (h & numpy.uint64(0xFFFFFF)).astype(numpy.float64) / float(0xFFFFFF)


def value_noise(points, scale, seed=0):
    q = points / scale + 1000.0
    base = numpy.floor(q)
    f = q - base
    f = f * f * (3.0 - 2.0 * f)
    ix = base[:, 0].astype(numpy.int64)
    iy = base[:, 1].astype(numpy.int64)
    iz = base[:, 2].astype(numpy.int64)
    total = numpy.zeros(len(points))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                weight = (f[:, 0] if dx else 1.0 - f[:, 0]) * (f[:, 1] if dy else 1.0 - f[:, 1]) * (f[:, 2] if dz else 1.0 - f[:, 2])
                total += weight * hashed(ix + dx, iy + dy, iz + dz, seed)
    return total


def fbm(points, scale, octaves=4, seed=0, gain=0.5):
    total = numpy.zeros(len(points))
    amplitude = 1.0
    norm = 0.0
    for octave in range(octaves):
        total += amplitude * value_noise(points, scale / (2.0 ** octave), seed + octave * 17)
        norm += amplitude
        amplitude *= gain
    return total / norm


def dilate(image, valid, passes=24):
    image = image.copy()
    valid = valid.copy()
    for step in range(passes):
        if valid.all():
            break
        total = numpy.zeros_like(image)
        count = numpy.zeros(valid.shape, dtype=numpy.float32)
        for axis, offset in ((0, 1), (0, -1), (1, 1), (1, -1)):
            shifted = numpy.roll(valid, offset, axis=axis)
            total += numpy.roll(image, offset, axis=axis) * shifted[..., None]
            count += shifted
        grow = (~valid) & (count > 0)
        image[grow] = total[grow] / count[grow][:, None]
        valid |= grow
    return image


def streaks(lookup, index, step, noise, reach):
    rows, cols = lookup.shape
    total = noise.copy()
    weight = numpy.ones(len(index))
    y0, x0 = numpy.divmod(index, cols)
    for direction in (1.0, -1.0):
        x = x0.astype(numpy.float64)
        y = y0.astype(numpy.float64)
        here = numpy.arange(len(index))
        alive = numpy.ones(len(index), dtype=bool)
        for stride in range(1, reach + 1):
            x = x + step[here, 0] * direction
            y = y + step[here, 1] * direction
            xi = numpy.rint(x).astype(numpy.int64)
            yi = numpy.rint(y).astype(numpy.int64)
            inside = (xi >= 0) & (xi < cols) & (yi >= 0) & (yi < rows)
            found = numpy.where(inside, lookup[numpy.clip(yi, 0, rows - 1), numpy.clip(xi, 0, cols - 1)], -1)
            alive &= found >= 0
            here = numpy.where(alive, found, here)
            window = 0.5 + 0.5 * math.cos(math.pi * stride / (reach + 1.0))
            total += numpy.where(alive, noise[here], 0.0) * window
            weight += alive * window
    return total / weight


class canvas:
    def __init__(self, model, blueprint, size):
        started = time.time()
        self.size = size
        self.model = model
        self.blueprint = blueprint
        self.scale = model["scale"]
        self.field = blueprint["field"]
        self.groups = blueprint["cage"]["skin"]
        triangles, loops, owner = triangulate(model)
        self.triangles = triangles
        self.corner_uv = model["uv"][loops]
        self.face_of = owner
        points = model["points"]
        self.normals = model_normals(model, triangles)
        self.corner_tangent, self.corner_sign, tangent, bitangent = engine_tangents(points, triangles, self.corner_uv, self.normals)
        tri, weights = rasterize(self.corner_uv, size, points[triangles])
        self.valid = tri >= 0
        self.index = numpy.flatnonzero(self.valid.reshape(-1))
        self.lookup = numpy.full(size * size, -1, dtype=numpy.int64)
        self.lookup[self.index] = numpy.arange(len(self.index))
        self.lookup = self.lookup.reshape(size, size)
        self.tri = tri.reshape(-1)[self.index]
        self.weights = weights.reshape(-1, 3)[self.index].astype(numpy.float64)
        self.weights /= self.weights.sum(axis=1)[:, None]
        self.position = self.blend(points[triangles]) / self.scale
        normal = self.blend(self.normals[triangles])
        self.normal = normal / numpy.maximum(numpy.linalg.norm(normal, axis=1), 1e-12)[:, None]
        t = self.blend(self.corner_tangent)
        t = t - self.normal * numpy.sum(self.normal * t, axis=1)[:, None]
        self.tangent = t / numpy.maximum(numpy.linalg.norm(t, axis=1), 1e-12)[:, None]
        self.bitangent = numpy.cross(self.normal, self.tangent) * self.corner_sign[self.tri, 0][:, None]
        self.du = tangent[self.tri] / self.scale
        self.dv = bitangent[self.tri] / self.scale
        names = sorted(set(model["tags"]))
        self.tag_names = names
        codes = numpy.array([names.index(tag) for tag in model["tags"]])
        self.tag = codes[owner][self.tri]
        self.detail = self.blend(model["detail"].astype(numpy.float64)[triangles][:, :, None])[:, 0]
        self.coord = self.blend(model["coord"][triangles])
        self.side = numpy.where(self.position[:, 0] >= 0.0, 1.0, -1.0)
        print("CANVAS", size, len(self.index), "texels", round(100.0 * len(self.index) / (size * size), 1), "% used", round(time.time() - started, 1), "s")

    def blend(self, corners):
        picked = corners[self.tri]
        return picked[:, 0] * self.weights[:, 0:1] + picked[:, 1] * self.weights[:, 1:2] + picked[:, 2] * self.weights[:, 2:3]

    def tagged(self, *names):
        codes = [self.tag_names.index(name) for name in names if name in self.tag_names]
        return numpy.isin(self.tag, codes)

    def vertex_mask(self, *names):
        part = numpy.isin(numpy.array(self.model["part"]), names).astype(numpy.float64)
        return self.blend(part[self.triangles][:, :, None])[:, 0]

    def grid(self, values, fill=0.0):
        values = numpy.asarray(values)
        shape = (self.size * self.size,) + values.shape[1:]
        image = numpy.full(shape, fill, dtype=numpy.float32)
        image[self.index] = values
        return image.reshape((self.size, self.size) + values.shape[1:])

    def surface(self):
        started = time.time()
        f = self.field
        moved = f.project(self.position, self.groups, iterations=3, limit=0.006)
        drift = numpy.linalg.norm(moved - self.position, axis=1)
        value, gradient = f.sample(moved, self.groups)
        detail = gradient / numpy.maximum(numpy.linalg.norm(gradient, axis=1), 1e-9)[:, None]
        trust = self.detail * (1.0 - fields.smoothstep(0.004, 0.012, drift)) * fields.smoothstep(0.2, 0.6, numpy.sum(detail * self.normal, axis=1))
        blended = self.normal + (detail - self.normal) * trust[:, None]
        blended /= numpy.maximum(numpy.linalg.norm(blended, axis=1), 1e-9)[:, None]
        occlusion = numpy.ones(len(self.position))
        for radius, share in ((0.012, 0.18), (0.035, 0.24), (0.09, 0.3), (0.2, 0.28)):
            open_space = f.evaluate(self.position + self.normal * radius, self.groups)
            occlusion -= share * numpy.clip(1.0 - open_space / radius, 0.0, 1.0)
        print("SURFACE", round(time.time() - started, 1), "s")
        return blended, numpy.clip(occlusion, 0.0, 1.0)

    def flow_step(self, flow, length):
        flow = flow - self.normal * numpy.sum(self.normal * flow, axis=1)[:, None]
        flow /= numpy.maximum(numpy.linalg.norm(flow, axis=1), 1e-9)[:, None]
        a11 = numpy.sum(self.du * self.du, axis=1)
        a12 = numpy.sum(self.du * self.dv, axis=1)
        a22 = numpy.sum(self.dv * self.dv, axis=1)
        b1 = numpy.sum(self.du * flow, axis=1)
        b2 = numpy.sum(self.dv * flow, axis=1)
        det = numpy.maximum(a11 * a22 - a12 * a12, 1e-18)
        step = numpy.column_stack([(a22 * b1 - a12 * b2) / det, (a11 * b2 - a12 * b1) / det]) * (length * self.size)
        size = numpy.linalg.norm(step, axis=1)
        return step * numpy.minimum(1.0, 3.0 / numpy.maximum(size, 1e-9))[:, None]

    def fur(self, flow, grain, stride, reach, seed):
        noise = value_noise(self.position, grain, seed)
        noise = numpy.clip((noise - 0.5) * 1.6 + 0.5, 0.0, 1.0)
        return streaks(self.lookup, self.index, self.flow_step(flow, stride), noise, reach)

    def relief(self, height, depth):
        image = self.grid(height, 0.5)
        image = dilate(image[..., None], self.valid, 4)[..., 0]
        gx = (numpy.roll(image, -1, axis=1) - numpy.roll(image, 1, axis=1)) * 0.5
        gy = (numpy.roll(image, -1, axis=0) - numpy.roll(image, 1, axis=0)) * 0.5
        gx = gx.reshape(-1)[self.index] * self.size
        gy = gy.reshape(-1)[self.index] * self.size
        lu = numpy.maximum(numpy.linalg.norm(self.du, axis=1), 1e-9)
        lv = numpy.maximum(numpy.linalg.norm(self.dv, axis=1), 1e-9)
        return numpy.column_stack([-gx / lu * depth, -gy / lv * depth])

    def encode_normal(self, world, slope):
        x = numpy.sum(world * self.tangent, axis=1)
        y = numpy.sum(world * self.bitangent, axis=1)
        z = numpy.maximum(numpy.sum(world * self.normal, axis=1), 0.05)
        local = numpy.column_stack([x / z + slope[:, 0], y / z + slope[:, 1], numpy.ones(len(x))])
        local /= numpy.linalg.norm(local, axis=1)[:, None]
        return local * 0.5 + 0.5


def transfer(source, values, target, passes=10):
    values = numpy.asarray(values)
    image = source.grid(values if values.ndim > 1 else values[:, None])
    image = dilate(image, source.valid, passes)
    factor = target.size // source.size
    if factor > 1:
        image = numpy.repeat(numpy.repeat(image, factor, axis=0), factor, axis=1)
        total = numpy.zeros_like(image)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                total += numpy.roll(numpy.roll(image, dy, axis=0), dx, axis=1)
        image = total / 9.0
    picked = image.reshape(-1, image.shape[2])[target.index].astype(numpy.float64)
    return picked if values.ndim > 1 else picked[:, 0]


def write(canvas, values, path, passes=24, fill=None):
    image = canvas.grid(values)
    if image.ndim == 2:
        image = image[..., None]
    image = dilate(image, canvas.valid, passes)
    reached = canvas.valid.copy()
    for step in range(passes):
        grown = reached.copy()
        for axis, offset in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grown |= numpy.roll(reached, offset, axis=axis)
        reached = grown
    image[~reached] = numpy.asarray(fill if fill is not None else numpy.asarray(values).reshape(len(values), -1).mean(axis=0), dtype=numpy.float32)
    size = canvas.size
    rgba = numpy.ones((size, size, 4), dtype=numpy.float32)
    rgba[:, :, :3] = numpy.clip(image[:, :, :3] if image.shape[2] >= 3 else numpy.repeat(image, 3, axis=2), 0.0, 1.0)
    render.save_pixels(path, rgba[::-1])
