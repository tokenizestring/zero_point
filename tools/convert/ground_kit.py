import bpy
import math
import os
import time
import numpy
import OpenImageIO

tau = math.tau
spectra = {}
spheres = {}
up = numpy.array([0.0, 0.0, 1.0], dtype=numpy.float32)


def to_linear(value):
    value = numpy.asarray(value, dtype=numpy.float32)
    return numpy.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4).astype(numpy.float32)


def to_srgb(value):
    value = numpy.clip(numpy.asarray(value, dtype=numpy.float32), 0.0, 1.0)
    return numpy.where(value <= 0.0031308, value * 12.92, 1.055 * value ** (1.0 / 2.4) - 0.055).astype(numpy.float32)


def rgb(red, green, blue):
    return to_linear(numpy.array([red, green, blue], dtype=numpy.float32) / 255.0)


def luminance(color):
    return color[..., 0] * 0.2126 + color[..., 1] * 0.7152 + color[..., 2] * 0.0722


def smoothstep(low, high, value):
    t = numpy.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def unit(field, low=1.0, high=99.0):
    a, b = numpy.percentile(field, [low, high])
    return numpy.clip((field - a) / max(b - a, 1e-9), 0.0, 1.0).astype(numpy.float32)


def tint(a, b, t):
    t = numpy.asarray(t, dtype=numpy.float32)[..., None]
    return (a * (1.0 - t) + b * t).astype(numpy.float32)


def vary(rng, colors, value=0.12, hue=0.05):
    colors = numpy.asarray(colors, dtype=numpy.float32)
    count = colors.shape[0]
    return (colors * numpy.exp(rng.normal(0.0, value, (count, 1))) * numpy.exp(rng.normal(0.0, hue, (count, 3)))).astype(numpy.float32)


def choose(rng, palette, count, weights=None):
    palette = numpy.asarray(palette, dtype=numpy.float32)
    weights = None if weights is None else numpy.asarray(weights, dtype=numpy.float64) / numpy.sum(weights)
    return palette[rng.choice(len(palette), count, p=weights)]


def radial(size):
    if size not in spectra:
        rows = numpy.fft.fftfreq(size, 1.0 / size).astype(numpy.float32)
        columns = numpy.fft.rfftfreq(size, 1.0 / size).astype(numpy.float32)
        spectra[size] = numpy.sqrt(rows[:, None] ** 2 + columns[None, :] ** 2)
    return spectra[size]


def noise(size, seed, beta=2.0, low=1.0, high=None):
    rng = numpy.random.default_rng(seed)
    radius = numpy.maximum(radial(size), 0.5)
    high = high if high else size * 0.5
    amplitude = radius ** (-beta * 0.5) / (1.0 + (low / radius) ** 6) * numpy.exp(-(radius / high) ** 4)
    amplitude[0, 0] = 0.0
    phase = rng.uniform(0.0, tau, radius.shape).astype(numpy.float32)
    field = numpy.fft.irfft2(amplitude * numpy.exp(1j * phase), s=(size, size))
    field -= field.mean()
    field /= field.std()
    return field.astype(numpy.float32)


def blur(field, sigma):
    size = field.shape[0]
    kernel = numpy.exp(-2.0 * (math.pi * sigma * radial(size) / size) ** 2)
    if field.ndim == 3:
        return numpy.stack([blur(field[..., index], sigma) for index in range(field.shape[2])], axis=-1)
    return numpy.fft.irfft2(numpy.fft.rfft2(field) * kernel, s=field.shape).astype(numpy.float32)


def resize(field, size):
    source = field.shape[0]
    if source == size:
        return field
    if field.ndim == 3:
        return numpy.stack([resize(field[..., index], size) for index in range(field.shape[2])], axis=-1)
    if source > size and source % size == 0:
        factor = source // size
        return field.reshape(size, factor, size, factor).mean(axis=(1, 3)).astype(numpy.float32)
    spectrum = numpy.fft.rfft2(field)
    half = min(source, size) // 2
    padded = numpy.zeros((size, size // 2 + 1), dtype=spectrum.dtype)
    padded[:half, :half] = spectrum[:half, :half]
    padded[-half:, :half] = spectrum[-half:, :half]
    return (numpy.fft.irfft2(padded, s=(size, size)) * (size / source) ** 2).astype(numpy.float32)


def sample(field, x, y, extent):
    size = field.shape[0]
    fx = numpy.asarray(x, dtype=numpy.float64) / extent * size - 0.5
    fy = numpy.asarray(y, dtype=numpy.float64) / extent * size - 0.5
    ix = numpy.floor(fx).astype(numpy.int64)
    iy = numpy.floor(fy).astype(numpy.int64)
    tx = (fx - ix).astype(numpy.float32)
    ty = (fy - iy).astype(numpy.float32)
    ix0 = ix % size
    ix1 = (ix + 1) % size
    iy0 = iy % size
    iy1 = (iy + 1) % size
    if field.ndim == 3:
        tx = tx[..., None]
        ty = ty[..., None]
    return (field[iy0, ix0] * (1.0 - tx) + field[iy0, ix1] * tx) * (1.0 - ty) + (field[iy1, ix0] * (1.0 - tx) + field[iy1, ix1] * tx) * ty


def slopes(field, extent):
    scale = field.shape[0] / extent * 0.5
    return (numpy.roll(field, -1, axis=1) - numpy.roll(field, 1, axis=1)) * scale, (numpy.roll(field, -1, axis=0) - numpy.roll(field, 1, axis=0)) * scale


def warp(field, seed, amount, scale=6.0, beta=3.0):
    size = field.shape[0]
    coordinate = (numpy.arange(size, dtype=numpy.float32) + 0.5) / size
    x, y = numpy.meshgrid(coordinate, coordinate)
    return sample(field, x + noise(size, seed, beta, 1.0, scale) * amount, y + noise(size, seed + 1, beta, 1.0, scale) * amount, 1.0).astype(numpy.float32)


def worley(size, cells, seed, jitter=1.0):
    rng = numpy.random.default_rng(seed)
    grid = numpy.stack(numpy.meshgrid(numpy.arange(cells), numpy.arange(cells)), axis=-1).astype(numpy.float32)
    points = grid + 0.5 + (rng.random((cells, cells, 2)).astype(numpy.float32) - 0.5) * jitter
    coordinate = (numpy.arange(size, dtype=numpy.float32) + 0.5) * cells / size
    px, py = numpy.meshgrid(coordinate, coordinate)
    cx = numpy.floor(px).astype(numpy.int32)
    cy = numpy.floor(py).astype(numpy.int32)
    first = numpy.full((size, size), 1e9, dtype=numpy.float32)
    second = numpy.full((size, size), 1e9, dtype=numpy.float32)
    ident = numpy.zeros((size, size), dtype=numpy.int32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            nx = cx + ox
            ny = cy + oy
            wx = nx % cells
            wy = ny % cells
            distance = numpy.hypot(px - (points[wy, wx, 0] + (nx - wx)), py - (points[wy, wx, 1] + (ny - wy)))
            closer = distance < first
            second = numpy.where(closer, first, numpy.minimum(second, distance))
            ident = numpy.where(closer, wy * cells + wx, ident)
            first = numpy.where(closer, distance, first)
    return first, second, ident


def scatter(rng, count, extent, density=None):
    if density is None:
        return rng.uniform(0.0, extent, (count, 2))
    peak = float(density.max())
    ratio = max(float(density.mean()) / max(peak, 1e-9), 0.01)
    chosen = []
    needed = count
    while needed > 0:
        candidates = rng.uniform(0.0, extent, (int(needed / ratio * 1.2) + 64, 2))
        keep = rng.random(len(candidates)) * peak < sample(density, candidates[:, 0], candidates[:, 1], extent)
        picked = candidates[keep][:needed]
        chosen.append(picked)
        needed -= len(picked)
    return numpy.concatenate(chosen)


def spaced(rng, count, extent, distance, density=None, attempts=60):
    cells = max(1, int(extent / distance))
    cell = extent / cells
    buckets = {}
    points = []
    peak = float(density.max()) if density is not None else 1.0
    for attempt in range(count * attempts):
        if len(points) >= count:
            break
        x, y = rng.uniform(0.0, extent, 2)
        if density is not None and rng.random() * peak > sample(density, x, y, extent):
            continue
        ix = int(x / cell) % cells
        iy = int(y / cell) % cells
        clear = True
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                for qx, qy in buckets.get(((ix + ox) % cells, (iy + oy) % cells), ()):
                    dx = abs(qx - x)
                    dy = abs(qy - y)
                    if math.hypot(min(dx, extent - dx), min(dy, extent - dy)) < distance:
                        clear = False
        if clear:
            buckets.setdefault((ix, iy), []).append((x, y))
            points.append((x, y))
    return numpy.array(points, dtype=numpy.float64).reshape(-1, 2)


def euler_matrix(euler):
    euler = numpy.asarray(euler, dtype=numpy.float64)
    cx, cy, cz = numpy.cos(euler).T
    sx, sy, sz = numpy.sin(euler).T
    matrix = numpy.empty((len(euler), 3, 3), dtype=numpy.float64)
    matrix[:, 0, 0] = cy * cz
    matrix[:, 0, 1] = sx * sy * cz - cx * sz
    matrix[:, 0, 2] = cx * sy * cz + sx * sz
    matrix[:, 1, 0] = cy * sz
    matrix[:, 1, 1] = sx * sy * sz + cx * cz
    matrix[:, 1, 2] = cx * sy * sz - sx * cz
    matrix[:, 2, 0] = -sy
    matrix[:, 2, 1] = sx * cy
    matrix[:, 2, 2] = cx * cy
    return matrix


def matrix_euler(matrix):
    return numpy.stack([numpy.arctan2(matrix[:, 2, 1], matrix[:, 2, 2]), -numpy.arcsin(numpy.clip(matrix[:, 2, 0], -1.0, 1.0)), numpy.arctan2(matrix[:, 1, 0], matrix[:, 0, 0])], axis=1)


def lean_matrix(gx, gy):
    normal = numpy.stack([-gx, -gy, numpy.ones_like(gx)], axis=1)
    normal /= numpy.linalg.norm(normal, axis=1, keepdims=True)
    vx = -normal[:, 1]
    vy = normal[:, 0]
    c = normal[:, 2]
    k = 1.0 / (1.0 + c)
    matrix = numpy.empty((len(gx), 3, 3), dtype=numpy.float64)
    matrix[:, 0, 0] = 1.0 - k * vy * vy
    matrix[:, 0, 1] = k * vx * vy
    matrix[:, 0, 2] = vy
    matrix[:, 1, 0] = k * vx * vy
    matrix[:, 1, 1] = 1.0 - k * vx * vx
    matrix[:, 1, 2] = -vx
    matrix[:, 2, 0] = -vy
    matrix[:, 2, 1] = vx
    matrix[:, 2, 2] = 1.0 - k * (vx * vx + vy * vy)
    return matrix


def icosphere(level):
    if level not in spheres:
        t = (1.0 + 5.0 ** 0.5) / 2.0
        vertices = [numpy.array(v, dtype=numpy.float64) / math.sqrt(1.0 + t * t) for v in ((-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1))]
        faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
        for step in range(level):
            cache = {}
            refined = []
            for a, b, c in faces:
                middle = []
                for first, second in ((a, b), (b, c), (c, a)):
                    key = (min(first, second), max(first, second))
                    if key not in cache:
                        point = vertices[first] + vertices[second]
                        vertices.append(point / numpy.linalg.norm(point))
                        cache[key] = len(vertices) - 1
                    middle.append(cache[key])
                refined += [(a, middle[0], middle[2]), (b, middle[1], middle[0]), (c, middle[2], middle[1]), (middle[0], middle[1], middle[2])]
            faces = refined
        spheres[level] = (numpy.array(vertices, dtype=numpy.float32), numpy.array(faces, dtype=numpy.int32))
    return spheres[level]


def ripple(points, seed, frequency, octaves=3, gain=0.5, waves=5):
    rng = numpy.random.default_rng(seed)
    total = numpy.zeros(points.shape[:-1], dtype=numpy.float32)
    weight = 0.0
    amplitude = 1.0
    for octave in range(octaves):
        direction = rng.normal(0.0, 1.0, (waves, 3))
        direction *= frequency * 2.0 ** octave * rng.uniform(0.7, 1.3, (waves, 1)) / numpy.linalg.norm(direction, axis=1, keepdims=True)
        total += amplitude * numpy.sin(points @ direction.T.astype(numpy.float32) + rng.uniform(0.0, tau, waves).astype(numpy.float32)).sum(axis=-1) / math.sqrt(waves * 0.5)
        weight += amplitude * amplitude
        amplitude *= gain
    return total / math.sqrt(weight)


def pebble(seed, level=4, lump=0.12, grain=0.015):
    vertices, faces = icosphere(level)
    radius = 1.0 + lump * ripple(vertices, seed, 1.1, 2, 0.45) + grain * ripple(vertices, seed + 7, 7.0, 2, 0.6)
    return vertices * radius[:, None], faces


def shard(seed, level=4, planes=14, sharp=16.0, grain=0.02):
    rng = numpy.random.default_rng(seed)
    vertices, faces = icosphere(level)
    normals = rng.normal(0.0, 1.0, (planes, 3))
    normals = numpy.concatenate([normals / numpy.linalg.norm(normals, axis=1, keepdims=True), numpy.eye(3), -numpy.eye(3)]).astype(numpy.float32)
    offsets = numpy.concatenate([rng.uniform(0.55, 1.0, planes), rng.uniform(0.8, 1.0, 6)]).astype(numpy.float32)
    reach = numpy.maximum(vertices @ normals.T, 0.0) / offsets
    radius = (reach ** sharp).sum(axis=1) ** (-1.0 / sharp)
    radius = radius * (1.0 + grain * ripple(vertices, seed + 3, 5.0, 3, 0.6))
    return vertices * radius[:, None], faces


def chunk(seed, level=4, planes=10, sharp=6.0, lump=0.14, grain=0.05):
    rng = numpy.random.default_rng(seed)
    vertices, faces = icosphere(level)
    normals = rng.normal(0.0, 1.0, (planes, 3))
    normals = (normals / numpy.linalg.norm(normals, axis=1, keepdims=True)).astype(numpy.float32)
    offsets = rng.uniform(0.62, 1.0, planes).astype(numpy.float32)
    reach = numpy.maximum(vertices @ normals.T, 1e-4) / offsets
    radius = ((reach ** sharp).sum(axis=1) + 0.35 ** sharp) ** (-1.0 / sharp)
    radius = radius * (1.0 + lump * ripple(vertices, seed + 5, 1.6, 2, 0.5)) * (1.0 + grain * ripple(vertices, seed + 9, 7.0, 3, 0.6))
    return vertices * radius[:, None], faces


def clod(seed, level=3, lump=0.26):
    vertices, faces = icosphere(level)
    radius = numpy.maximum(1.0 + lump * ripple(vertices, seed, 1.5, 3, 0.62), 0.4)
    return vertices * radius[:, None], faces


def frames(spine, side=None):
    tangent = numpy.gradient(spine, axis=1)
    tangent /= numpy.maximum(numpy.linalg.norm(tangent, axis=-1, keepdims=True), 1e-9)
    if side is None:
        side = numpy.cross(up, tangent)
        length = numpy.linalg.norm(side, axis=-1, keepdims=True)
        side = numpy.where(length < 0.05, numpy.cross(numpy.array([0.0, 1.0, 0.0], dtype=numpy.float32), tangent), side)
    else:
        side = side - tangent * (side * tangent).sum(axis=-1, keepdims=True)
    side = side / numpy.maximum(numpy.linalg.norm(side, axis=-1, keepdims=True), 1e-9)
    return tangent, side.astype(numpy.float32), numpy.cross(tangent, side).astype(numpy.float32)


def paths(rng, start, heading, length, steps, curl=0.0, wobble=0.0, waves=1.5, anchor=None):
    count = len(start)
    t = numpy.linspace(0.0, 1.0, steps, dtype=numpy.float32)[None, :]
    curl = numpy.broadcast_to(numpy.asarray(curl, dtype=numpy.float32), (count,))
    wobble = numpy.broadcast_to(numpy.asarray(wobble, dtype=numpy.float32), (count,))
    angle = numpy.asarray(heading, dtype=numpy.float32)[:, None] + curl[:, None] * (t - 0.5) + wobble[:, None] * numpy.sin(t * tau * waves * rng.uniform(0.6, 1.4, (count, 1)) + rng.uniform(0.0, tau, (count, 1)))
    step = (numpy.broadcast_to(numpy.asarray(length, dtype=numpy.float32), (count,)) / (steps - 1))[:, None]
    x = numpy.cumsum(numpy.cos(angle) * step, axis=1) - numpy.cos(angle) * step
    y = numpy.cumsum(numpy.sin(angle) * step, axis=1) - numpy.sin(angle) * step
    if anchor is None:
        x -= x.mean(axis=1, keepdims=True)
        y -= y.mean(axis=1, keepdims=True)
    else:
        pivot = int(round(anchor * (steps - 1)))
        x -= x[:, pivot:pivot + 1].copy()
        y -= y[:, pivot:pivot + 1].copy()
    return numpy.stack([start[:, 0:1] + x, start[:, 1:2] + y], axis=-1).astype(numpy.float32)


def streams(rng, start, flow, extent, length, steps, sway=0.2, drift=0.03):
    count = len(start)
    step = numpy.broadcast_to(numpy.asarray(length, dtype=numpy.float64), (count,)) / (steps - 1)
    points = numpy.empty((count, steps, 2), dtype=numpy.float32)
    position = numpy.asarray(start, dtype=numpy.float64).copy()
    turn = rng.normal(0.0, sway, count)
    for index in range(steps):
        points[:, index] = position
        turn = turn + rng.normal(0.0, drift, count)
        heading = sample(flow, position[:, 0], position[:, 1], extent)
        angle = numpy.arctan2(heading[:, 1], heading[:, 0]) + turn
        position = position + step[:, None] * numpy.stack([numpy.cos(angle), numpy.sin(angle)], axis=1)
    return points


def upright(base, heading, length, steps, lean, bend):
    count = len(base)
    t = numpy.linspace(0.0, 1.0, steps, dtype=numpy.float32)[None, :]
    tilt = numpy.asarray(lean, dtype=numpy.float32)[:, None] + numpy.asarray(bend, dtype=numpy.float32)[:, None] * t ** 1.5
    step = (numpy.asarray(length, dtype=numpy.float32) / (steps - 1))[:, None]
    out = numpy.cumsum(numpy.sin(tilt) * step, axis=1) - numpy.sin(tilt) * step
    rise = numpy.cumsum(numpy.cos(tilt) * step, axis=1) - numpy.cos(tilt) * step
    forward = numpy.stack([numpy.cos(heading), numpy.sin(heading)], axis=1).astype(numpy.float32)
    spine = numpy.concatenate([base[:, None, :2] + forward[:, None, :] * out[..., None], (base[:, 2:3] + rise)[..., None]], axis=-1).astype(numpy.float32)
    side = numpy.broadcast_to(numpy.stack([-forward[:, 1], forward[:, 0], numpy.zeros(count, dtype=numpy.float32)], axis=1)[:, None, :], spine.shape)
    return spine, side


def spread(value, count, steps):
    value = numpy.asarray(value, dtype=numpy.float32)
    if value.ndim == 1:
        value = value[None, None, :]
    elif value.ndim == 2:
        value = value[:, None, :]
    return numpy.broadcast_to(value, (count, steps, 3))


def scalar(value, count, steps):
    value = numpy.asarray(value, dtype=numpy.float32)
    if value.ndim == 0:
        value = value[None, None]
    elif value.ndim == 1:
        value = value[:, None]
    return numpy.broadcast_to(value, (count, steps))


def sweep(spine, radius, sides=4, flat=1.0, side=None):
    spine = numpy.asarray(spine, dtype=numpy.float32)
    count, steps = spine.shape[:2]
    radius = scalar(radius, count, steps)
    flat = scalar(flat, count, steps)
    tangent, side, normal = frames(spine, side)
    angle = numpy.arange(sides, dtype=numpy.float32) * (tau / sides) + tau * 0.25
    across = numpy.cos(angle)[None, None, :] * radius[:, :, None]
    along = numpy.sin(angle)[None, None, :] * (radius * flat)[:, :, None]
    points = spine[:, :, None, :] + side[:, :, None, :] * across[..., None] + normal[:, :, None, :] * along[..., None]
    ring = numpy.arange(sides)
    base = (numpy.arange(steps - 1) * sides)[:, None]
    quads = numpy.stack([base + ring, base + (ring + 1) % sides, base + sides + (ring + 1) % sides, base + sides + ring], axis=-1).reshape(-1, 4)
    return points, quads, across, along


def average(level, window):
    if window < 1:
        return level
    padded = numpy.pad(level, ((0, 0), (window, window)), mode="edge")
    total = numpy.cumsum(numpy.pad(padded, ((0, 0), (1, 0))), axis=1)
    width = 2 * window + 1
    return (total[:, width:] - total[:, :-width]) / width


def accelerate(scene):
    preferences = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            preferences.compute_device_type = kind
        except TypeError:
            continue
        preferences.get_devices()
        if any(device.type == kind for device in preferences.devices):
            for device in preferences.devices:
                device.use = device.type == kind
            scene.cycles.device = 'GPU'
            return kind
    scene.cycles.device = 'CPU'
    return 'CPU'


def make_mesh(name, vertices, faces, attributes=None):
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(vertices))
    mesh.vertices.foreach_set("co", numpy.ascontiguousarray(vertices, dtype=numpy.float32).ravel())
    starts = []
    corners = []
    total = 0
    for arity in sorted(faces):
        block = numpy.ascontiguousarray(faces[arity], dtype=numpy.int32)
        starts.append(numpy.arange(len(block), dtype=numpy.int32) * arity + total)
        corners.append(block.ravel())
        total += block.size
    mesh.loops.add(total)
    mesh.polygons.add(sum(len(start) for start in starts))
    mesh.polygons.foreach_set("loop_start", numpy.concatenate(starts))
    mesh.loops.foreach_set("vertex_index", numpy.concatenate(corners))
    mesh.update(calc_edges=True)
    for key, values in (attributes or {}).items():
        attribute = mesh.attributes.new(key, 'FLOAT_VECTOR', 'POINT')
        attribute.data.foreach_set("vector", numpy.ascontiguousarray(values, dtype=numpy.float32).ravel())
    mesh.shade_smooth()
    return mesh


def write_image(path, pixels, kind="uint8", quality=None):
    pixels = numpy.ascontiguousarray(pixels if pixels.ndim == 3 else pixels[:, :, None])
    spec = OpenImageIO.ImageSpec(pixels.shape[1], pixels.shape[0], pixels.shape[2], kind)
    if quality:
        spec.attribute("Compression", "jpeg:%d" % quality)
        spec.attribute("jpeg:subsampling", "4:4:4")
    target = OpenImageIO.ImageOutput.create(path)
    if target is None or not target.open(path, spec):
        raise RuntimeError("cannot write " + path)
    target.write_image(pixels)
    target.close()


def read_image(path):
    source = OpenImageIO.ImageInput.open(path)
    if source is None:
        raise RuntimeError("cannot read " + path)
    spec = source.spec()
    pixels = numpy.asarray(source.read_image(0, 0, 0, spec.nchannels, "uint8")).reshape(spec.height, spec.width, spec.nchannels)
    source.close()
    return pixels


def read_passes(path, factor):
    source = OpenImageIO.ImageInput.open(path)
    spec = source.spec()
    names = list(spec.channelnames)
    size = spec.width // factor
    result = {}
    for key, channels in (("albedo", ("albedo.R", "albedo.G", "albedo.B")), ("normal", ("Normal.X", "Normal.Y", "Normal.Z")), ("ao", ("AO.R",)), ("rough", ("rough.X",)), ("height", ("height.X",)), ("mask", ("mask.X",))):
        planes = []
        for channel in channels:
            index = names.index("ViewLayer." + channel)
            plane = numpy.asarray(source.read_image(0, 0, index, index + 1, "float")).reshape(spec.height, spec.width)
            planes.append(plane.reshape(size, factor, size, factor).mean(axis=(1, 3)) if factor > 1 else plane)
        result[key] = numpy.stack(planes, axis=-1) if len(planes) > 1 else planes[0]
    source.close()
    return result


class wire:
    def __init__(self, owner, socket, vector):
        self.owner = owner
        self.socket = socket
        self.vector = vector
        self.parts = None

    def binary(self, other, operation, swap=False):
        first, second = (other, self) if swap else (self, other)
        wide = self.vector or (isinstance(other, wire) and other.vector) or (not isinstance(other, wire) and numpy.ndim(other) > 0)
        return self.owner.vector_math(operation, first, second) if wide else self.owner.math(operation, first, second)

    def __add__(self, other):
        return self.binary(other, 'ADD')

    def __radd__(self, other):
        return self.binary(other, 'ADD', True)

    def __sub__(self, other):
        return self.binary(other, 'SUBTRACT')

    def __rsub__(self, other):
        return self.binary(other, 'SUBTRACT', True)

    def __mul__(self, other):
        return self.binary(other, 'MULTIPLY')

    def __rmul__(self, other):
        return self.binary(other, 'MULTIPLY', True)

    def __truediv__(self, other):
        return self.binary(other, 'DIVIDE')

    def __rtruediv__(self, other):
        return self.binary(other, 'DIVIDE', True)

    def __neg__(self):
        return self.binary(-1.0, 'MULTIPLY')

    def split(self):
        if self.parts is None:
            node = self.owner.new('ShaderNodeSeparateXYZ')
            self.owner.feed(node.inputs[0], self)
            self.parts = [wire(self.owner, node.outputs[index], False) for index in range(3)]
        return self.parts

    @property
    def x(self):
        return self.split()[0]

    @property
    def y(self):
        return self.split()[1]

    @property
    def z(self):
        return self.split()[2]


class graph:
    def __init__(self, name):
        self.material = bpy.data.materials.new(name)
        self.material.use_nodes = True
        self.tree = self.material.node_tree
        self.tree.nodes.clear()

    def new(self, kind, **settings):
        node = self.tree.nodes.new(kind)
        for key, value in settings.items():
            setattr(node, key, value)
        return node

    def feed(self, socket, value):
        if isinstance(value, wire):
            self.tree.links.new(value.socket, socket)
        elif socket.type == 'VALUE':
            socket.default_value = float(value)
        elif socket.type == 'RGBA':
            socket.default_value = tuple(float(v) for v in numpy.broadcast_to(numpy.asarray(value, dtype=numpy.float64), (3,))) + (1.0,)
        else:
            socket.default_value = tuple(float(v) for v in numpy.broadcast_to(numpy.asarray(value, dtype=numpy.float64), (3,)))

    def math(self, operation, a, b=None, c=None, clamp=False):
        node = self.new('ShaderNodeMath', operation=operation, use_clamp=clamp)
        for index, value in enumerate((a, b, c)):
            if value is not None:
                self.feed(node.inputs[index], value)
        return wire(self, node.outputs[0], False)

    def vector_math(self, operation, a, b=None):
        node = self.new('ShaderNodeVectorMath', operation=operation)
        self.feed(node.inputs[0], a)
        if b is not None:
            self.feed(node.inputs[1], b)
        scalar_result = operation in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE')
        return wire(self, node.outputs[1 if scalar_result else 0], not scalar_result)

    def combine(self, x, y, z):
        node = self.new('ShaderNodeCombineXYZ')
        for index, value in enumerate((x, y, z)):
            self.feed(node.inputs[index], value)
        return wire(self, node.outputs[0], True)

    def attribute(self, name, instancer=False):
        node = self.new('ShaderNodeAttribute', attribute_name=name, attribute_type='INSTANCER' if instancer else 'GEOMETRY')
        return wire(self, node.outputs['Vector'], True)

    def position(self):
        return wire(self, self.new('ShaderNodeNewGeometry').outputs['Position'], True)

    def local(self):
        return wire(self, self.new('ShaderNodeTexCoord').outputs['Object'], True)

    def facing(self):
        return wire(self, self.new('ShaderNodeNewGeometry').outputs['Normal'], True)

    def mix(self, a, b, factor):
        node = self.new('ShaderNodeMix', data_type='RGBA', clamp_factor=True)
        self.feed(node.inputs[0], factor)
        self.feed(node.inputs[6], a)
        self.feed(node.inputs[7], b)
        return wire(self, node.outputs[2], True)

    def lerp(self, a, b, factor):
        node = self.new('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        self.feed(node.inputs[0], factor)
        self.feed(node.inputs[2], a)
        self.feed(node.inputs[3], b)
        return wire(self, node.outputs[0], False)

    def step(self, low, high, value):
        node = self.new('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        self.feed(node.inputs['Value'], value)
        self.feed(node.inputs['From Min'], low)
        self.feed(node.inputs['From Max'], high)
        return wire(self, node.outputs['Result'], False)

    def noise(self, vector, scale, detail=2.0, rough=0.5, distortion=0.0, color=False):
        node = self.new('ShaderNodeTexNoise', noise_dimensions='3D')
        self.feed(node.inputs['Vector'], vector)
        self.feed(node.inputs['Scale'], scale)
        self.feed(node.inputs['Detail'], detail)
        self.feed(node.inputs['Roughness'], rough)
        self.feed(node.inputs['Distortion'], distortion)
        return wire(self, node.outputs['Color'], True) if color else wire(self, node.outputs['Fac'], False)

    def voronoi(self, vector, scale, feature='F1', randomness=1.0, color=False):
        node = self.new('ShaderNodeTexVoronoi', feature=feature)
        self.feed(node.inputs['Vector'], vector)
        self.feed(node.inputs['Scale'], scale)
        self.feed(node.inputs['Randomness'], randomness)
        return wire(self, node.outputs['Color'], True) if color else wire(self, node.outputs['Distance'], False)

    def ramp(self, factor, stops, interpolation='LINEAR'):
        node = self.new('ShaderNodeValToRGB')
        node.color_ramp.interpolation = interpolation
        elements = node.color_ramp.elements
        while len(elements) < len(stops):
            elements.new(0.5)
        for element, (position, color) in zip(elements, stops):
            element.position = position
            element.color = tuple(float(v) for v in numpy.broadcast_to(numpy.asarray(color, dtype=numpy.float64), (3,))) + (1.0,)
        self.feed(node.inputs[0], factor)
        return wire(self, node.outputs['Color'], True)

    def image(self, image, vector, smooth=False):
        node = self.new('ShaderNodeTexImage', image=image, interpolation='Cubic' if smooth else 'Linear', extension='REPEAT')
        self.feed(node.inputs['Vector'], vector)
        return wire(self, node.outputs['Color'], True)

    def bump(self, height, strength=1.0, distance=0.001, normal=None):
        node = self.new('ShaderNodeBump')
        self.feed(node.inputs['Strength'], strength)
        self.feed(node.inputs['Distance'], distance)
        self.feed(node.inputs['Height'], height)
        if normal is not None:
            self.feed(node.inputs['Normal'], normal)
        return wire(self, node.outputs['Normal'], True)

    def finish(self, albedo, rough, normal=None, lift=None, mask=0.0):
        output = self.new('ShaderNodeOutputMaterial')
        diffuse = self.new('ShaderNodeBsdfDiffuse')
        diffuse.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        if normal is not None:
            self.feed(diffuse.inputs['Normal'], normal)
        self.tree.links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
        height = self.position().z
        if lift is not None:
            height = height + lift
        for name, socket, value in (("albedo", 'Color', albedo), ("rough", 'Value', rough), ("height", 'Value', height), ("mask", 'Value', mask)):
            node = self.new('ShaderNodeOutputAOV', aov_name=name)
            self.feed(node.inputs[socket], value)
        return self.material


class bed:
    def __init__(self, height, extent, size):
        self.size = size
        self.extent = extent
        self.cell = extent / size
        center = (numpy.arange(size) + 0.5) * self.cell
        self.h = numpy.ascontiguousarray(sample(height, center[None, :], center[:, None], extent), dtype=numpy.float32)
        self.base = self.h.copy()
        self.kept = None

    def index(self, x, y):
        return numpy.floor(numpy.asarray(y) / self.cell).astype(numpy.int64) % self.size, numpy.floor(numpy.asarray(x) / self.cell).astype(numpy.int64) % self.size

    def at(self, x, y):
        return self.h[self.index(x, y)]

    def lift(self, x, y, z):
        numpy.maximum.at(self.h, self.index(x, y), numpy.asarray(z, dtype=numpy.float32))

    def swell(self, field):
        self.h += resize(numpy.asarray(field, dtype=numpy.float32), self.size)

    def mat(self, sigma):
        return blur(self.h, sigma / self.cell)

    def slab(self, rng, track, depth, field=None, surface=None, tilt=0.04, rank=None, pivot=0.0):
        count, steps = track.shape[:2]
        ground = sample(self.h if surface is None else surface, track[..., 0], track[..., 1], self.extent)
        local = 1.0 if field is None else sample(field, track[..., 0], track[..., 1], self.extent)
        reach = numpy.linalg.norm(track[:, 1:] - track[:, :-1], axis=-1).sum(axis=1, keepdims=True) * 0.5
        lean = rng.normal(0.0, tilt, (count, 1)) * reach * (numpy.linspace(-1.0, 1.0, steps, dtype=numpy.float32)[None, :] - pivot)
        rank = rng.random((count, 1)) if rank is None else rank
        return (ground + numpy.maximum(rank * depth * local + lean, 0.0)).astype(numpy.float32)

    def rest(self, rng, track, radius, stiff=0.5, rigid=False, half=None, batch=160, steep=0.18, order=None, mark=True):
        count, steps = track.shape[:2]
        level = numpy.zeros((count, steps), dtype=numpy.float32)
        radius = scalar(radius, count, steps)
        half = None if half is None else scalar(half, count, steps)
        order = rng.permutation(count) if order is None else order
        reach = numpy.linalg.norm(track[:, 1:] - track[:, :-1], axis=-1).sum(axis=1) * 0.5
        span = float(numpy.linalg.norm(track[:, 1:] - track[:, :-1], axis=-1).mean())
        fine = max(1, int(math.ceil(span / self.cell)))
        dense = (steps - 1) * fine + 1
        place = numpy.arange(dense) / fine
        left = numpy.minimum(place.astype(numpy.int64), steps - 2)
        part = (place - left).astype(numpy.float32)[None, :]
        t = numpy.linspace(-1.0, 1.0, dense, dtype=numpy.float32)[None, :]
        window = max(1, int(round(stiff * dense * 0.5)))
        for begin in range(0, count, batch):
            pick = order[begin:begin + batch]
            xy = track[pick]
            fx = xy[:, left, 0] * (1.0 - part) + xy[:, left + 1, 0] * part
            fy = xy[:, left, 1] * (1.0 - part) + xy[:, left + 1, 1] * part
            fr = radius[pick][:, left] * (1.0 - part) + radius[pick][:, left + 1] * part
            ground = self.at(fx, fy)
            if half is not None:
                ax = -numpy.gradient(fy, axis=1)
                ay = numpy.gradient(fx, axis=1)
                norm = numpy.maximum(numpy.hypot(ax, ay), 1e-9)
                fh = half[pick][:, left] * (1.0 - part) + half[pick][:, left + 1] * part
                ax = ax / norm * fh
                ay = ay / norm * fh
                for sign in (-0.8, 0.8):
                    ground = numpy.maximum(ground, self.at(fx + ax * sign, fy + ay * sign))
            if rigid:
                before = t[0, :dense // 2]
                after = t[0, (dense + 1) // 2:]
                chord = (ground[:, :dense // 2, None] * after[None, None, :] - ground[:, None, (dense + 1) // 2:] * before[None, :, None]) / (after[None, None, :] - before[None, :, None])
                best = chord.reshape(len(pick), -1).argmax(axis=1)
                row = numpy.arange(len(pick))
                first = best // len(after)
                second = best % len(after) + (dense + 1) // 2
                slope = (ground[row, second] - ground[row, first]) / (t[0, second] - t[0, first])
                limit = steep * reach[pick]
                settled = ground[row, first][:, None] + numpy.clip(slope, -limit, limit)[:, None] * (t - t[0, first][:, None])
                settled = settled + numpy.maximum((ground - settled).max(axis=1, keepdims=True), 0.0)
            else:
                settled = ground.copy()
                for iteration in range(3):
                    settled = numpy.maximum(ground, average(settled, window))
                padded = numpy.pad(settled, ((0, 0), (fine // 2, fine // 2)), mode="edge")
                for shift in range(2 * (fine // 2) + 1):
                    settled = numpy.maximum(settled, padded[:, shift:shift + dense])
            knots = settled[:, ::fine]
            level[pick] = knots
            if not mark:
                continue
            top = knots[:, left] * (1.0 - part) + knots[:, left + 1] * part + fr * 2.0
            if half is None:
                self.lift(fx, fy, top)
            else:
                lanes = max(3, int(math.ceil(float(fh.max()) * 2.0 / self.cell)) + 1)
                for lane in numpy.linspace(-1.0, 1.0, lanes):
                    self.lift(fx + ax * lane, fy + ay * lane, top)
        return level

    def drop(self, rng, position, axes, euler, tries=5, spread=1.0, sink=0.1, lean=0.6, order=None, perch=None):
        count = len(position)
        axes = numpy.asarray(axes, dtype=numpy.float64)
        rotation = euler_matrix(euler)
        shape = numpy.einsum('mij,mj,mkj->mik', rotation, 1.0 / axes ** 2, rotation)
        inverse = numpy.einsum('mij,mj,mkj->mik', rotation, axes ** 2, rotation)
        extent = numpy.sqrt(numpy.stack([inverse[:, 0, 0], inverse[:, 1, 1], inverse[:, 2, 2]], axis=1))
        result = numpy.zeros((count, 3), dtype=numpy.float64)
        slope = numpy.zeros((count, 2), dtype=numpy.float64)
        jitter = rng.normal(0.0, 1.0, (count, tries, 2))
        jitter[:, 0] = 0.0
        size = self.size
        cell = self.cell
        self.kept = numpy.ones(count, dtype=bool)
        for item in (range(count) if order is None else order):
            a = shape[item]
            rx = max(1, int(math.ceil(extent[item, 0] / cell)))
            ry = max(1, int(math.ceil(extent[item, 1] / cell)))
            ox = numpy.arange(-rx, rx + 1)
            oy = numpy.arange(-ry, ry + 1)
            dx = (ox * cell)[None, :]
            dy = (oy * cell)[:, None]
            b = a[0, 2] * dx + a[1, 2] * dy
            disc = b * b - a[2, 2] * (a[0, 0] * dx * dx + 2.0 * a[0, 1] * dx * dy + a[1, 1] * dy * dy - 1.0)
            valid = disc > 0.0
            root = numpy.sqrt(numpy.maximum(disc, 0.0)) / a[2, 2]
            middle = -b / a[2, 2]
            bottom = middle - root
            reach = spread * max(extent[item, 0], extent[item, 1])
            best = None
            for attempt in range(tries):
                ix = int(math.floor((position[item, 0] + jitter[item, attempt, 0] * reach) / cell))
                iy = int(math.floor((position[item, 1] + jitter[item, attempt, 1] * reach) / cell))
                rows = (iy + oy) % size
                columns = (ix + ox) % size
                patch = self.h[numpy.ix_(rows, columns)]
                level = float((patch - bottom)[valid].max())
                if best is None or level < best[0]:
                    best = (level, ix, iy, rows, columns, patch)
            level, ix, iy, rows, columns, patch = best
            if perch is not None and level - float((self.base[numpy.ix_(rows, columns)] - bottom)[valid].max()) > perch * extent[item, 2]:
                self.kept[item] = False
                result[item] = ((ix + 0.5) * cell, (iy + 0.5) * cell, level)
                continue
            if lean > 0.0:
                weight = valid.astype(numpy.float64)
                total = weight.sum()
                centered = (patch - (patch * weight).sum() / total) * weight
                slope[item, 0] = (centered * dx).sum() / max((weight * dx * dx).sum(), 1e-12)
                slope[item, 1] = (centered * dy).sum() / max((weight * dy * dy).sum(), 1e-12)
            level -= sink * extent[item, 2]
            self.h[numpy.ix_(rows, columns)] = numpy.where(valid, numpy.maximum(patch, level + middle + root), patch)
            result[item] = ((ix + 0.5) * cell, (iy + 0.5) * cell, level)
        steep = numpy.linalg.norm(slope, axis=1, keepdims=True)
        slope = slope * numpy.minimum(1.0, 0.6 / numpy.maximum(steep, 1e-9)) * lean
        return result, matrix_euler(numpy.einsum('mij,mjk->mik', lean_matrix(slope[:, 0], slope[:, 1]), rotation))


class tile:
    def __init__(self, name, size, seed, work, field=2048, grid=1024, margin=0.12):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.name = name
        self.size = size
        self.work = work
        self.field = field
        self.grid = grid
        self.margin = margin
        self.seed = seed
        self.rng = numpy.random.default_rng(seed)
        self.height = numpy.zeros((field, field), dtype=numpy.float32)
        self.soups = {}
        self.materials = {}
        self.groups = {}
        self.extents = {}
        self.marks = {}
        self.water = None
        self.triangles = 0
        self.instances = 0
        self.started = time.time()
        os.makedirs(work, exist_ok=True)

    def note(self, text):
        print("GROUND %s %6.1fs %s" % (self.name, time.time() - self.started, text), flush=True)

    def axis(self, size=None):
        size = size or self.field
        return (numpy.arange(size, dtype=numpy.float32) + 0.5) * (self.size / size)

    def image(self, name, pixels):
        pixels = numpy.asarray(pixels, dtype=numpy.float32)
        path = os.path.join(self.work, self.name + "_" + name + ".exr")
        write_image(path, pixels[::-1], "float")
        image = bpy.data.images.load(path)
        image.colorspace_settings.name = 'Non-Color'
        return image

    def plain(self, name, scale=300.0, contrast=0.12, stretch=(1.0, 1.0, 1.0), instanced=False):
        shader = graph(name)
        color = shader.attribute("tint", True) * shader.attribute("col") if instanced else shader.attribute("col")
        rough = shader.attribute("var", True).x if instanced else shader.attribute("prm").x
        place = (shader.local() + shader.attribute("ofs", True)) if instanced else shader.attribute("loc")
        grain = shader.noise(place * stretch, scale, 2.0, 0.6)
        self.materials[name] = shader.finish(color * (grain * (2.0 * contrast) + (1.0 - contrast)), rough)
        return shader

    def soil(self, name, albedo, rough, micro, strength=1.0):
        shader = graph(name)
        place = shader.position() * (1.0 / self.size)
        color = shader.image(self.image(name + "_albedo", albedo), place)
        data = shader.image(self.image(name + "_data", numpy.stack([rough, micro, numpy.zeros_like(rough)], axis=-1)), place, True)
        self.materials[name] = shader.finish(color, data.x, shader.bump(data.y, strength, 0.001), data.y * 0.001)
        return shader

    def copies(self, center, radius):
        center = numpy.asarray(center, dtype=numpy.float64)
        home = numpy.mod(center, self.size)
        low = -self.margin
        high = self.size + self.margin
        index = []
        shift = []
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                moved = home + numpy.array([ox * self.size, oy * self.size])
                keep = numpy.nonzero((moved[:, 0] + radius > low) & (moved[:, 0] - radius < high) & (moved[:, 1] + radius > low) & (moved[:, 1] - radius < high))[0]
                index.append(keep)
                shift.append(moved[keep] - center[keep])
        return numpy.concatenate(index), numpy.concatenate(shift).astype(numpy.float32)

    def emit(self, material, points, faces, col, prm, loc):
        count, size = points.shape[:2]
        low = points[..., :2].min(axis=1)
        high = points[..., :2].max(axis=1)
        index, shift = self.copies((low + high) * 0.5, ((high - low) * 0.5).max(axis=1))
        moved = points[index].astype(numpy.float32)
        moved[..., 0] += shift[:, None, 0]
        moved[..., 1] += shift[:, None, 1]
        offset = (numpy.arange(len(index), dtype=numpy.int64) * size)[:, None, None]
        part = {"v": moved.reshape(-1, 3), "col": numpy.asarray(col, dtype=numpy.float32)[index].reshape(-1, 3), "prm": numpy.asarray(prm, dtype=numpy.float32)[index].reshape(-1, 3), "loc": numpy.asarray(loc, dtype=numpy.float32)[index].reshape(-1, 3), "f": {arity: (block[None, :, :] + offset).reshape(-1, arity) for arity, block in faces.items()}}
        self.soups.setdefault(material, []).append(part)

    def tubes(self, material, spine, radius, sides=4, color=(0.2, 0.2, 0.2), rough=0.8, flat=1.0, side=None, cap=False):
        spine = numpy.asarray(spine, dtype=numpy.float32)
        count, steps = spine.shape[:2]
        points, quads, across, along = sweep(spine, radius, sides, flat, side)
        length = numpy.concatenate([numpy.zeros((count, 1), dtype=numpy.float32), numpy.cumsum(numpy.linalg.norm(spine[:, 1:] - spine[:, :-1], axis=-1), axis=1)], axis=1)
        offset = self.rng.uniform(0.0, 8.0, (count, 1, 3)).astype(numpy.float32)
        loc = numpy.stack([numpy.broadcast_to(length[:, :, None], across.shape), across, along], axis=-1).reshape(count, steps * sides, 3) + offset
        col = numpy.broadcast_to(spread(color, count, steps)[:, :, None, :], points.shape).reshape(count, steps * sides, 3)
        prm = numpy.empty(points.shape, dtype=numpy.float32)
        prm[..., 0] = scalar(rough, count, steps)[:, :, None]
        prm[..., 1] = self.rng.random((count, 1, 1), dtype=numpy.float32)
        prm[..., 2] = numpy.linspace(0.0, 1.0, steps, dtype=numpy.float32)[None, :, None]
        prm = prm.reshape(count, steps * sides, 3)
        points = points.reshape(count, steps * sides, 3)
        ring = numpy.arange(sides)
        faces = {4: quads}
        if cap:
            ends = [0, steps - 1]
            points = numpy.concatenate([points, spine[:, ends, :]], axis=1)
            col = numpy.concatenate([col, spread(color, count, steps)[:, ends, :] * 0.8], axis=1)
            prm = numpy.concatenate([prm, prm[:, [0, (steps - 1) * sides], :]], axis=1)
            loc = numpy.concatenate([loc, numpy.stack([length[:, ends], numpy.zeros((count, 2), dtype=numpy.float32), numpy.zeros((count, 2), dtype=numpy.float32)], axis=-1) + offset], axis=1)
            first = steps * sides
            last = (steps - 1) * sides
            faces[3] = numpy.concatenate([numpy.stack([numpy.full(sides, first), (ring + 1) % sides, ring], axis=-1), numpy.stack([numpy.full(sides, first + 1), last + ring, last + (ring + 1) % sides], axis=-1)])
        self.emit(material, points, faces, col, prm, loc)

    def ribbons(self, material, spine, width, across=3, color=(0.2, 0.2, 0.2), rough=0.8, side=None, fold=0.0, curl=0.0, twist=None, shade=0.0, wave=None):
        spine = numpy.asarray(spine, dtype=numpy.float32)
        count, steps = spine.shape[:2]
        width = scalar(width, count, steps)
        tangent, side, normal = frames(spine, side)
        if twist is not None:
            angle = scalar(twist, count, steps)[..., None]
            side, normal = side * numpy.cos(angle) + normal * numpy.sin(angle), normal * numpy.cos(angle) - side * numpy.sin(angle)
        u = numpy.linspace(-1.0, 1.0, across, dtype=numpy.float32)
        lift = (scalar(fold, count, steps)[:, :, None] * numpy.abs(u) + scalar(curl, count, steps)[:, :, None] * u * u) * width[:, :, None]
        if wave is not None:
            lift = lift + wave
        reach = u[None, None, :] * width[:, :, None]
        points = spine[:, :, None, :] + side[:, :, None, :] * reach[..., None] + normal[:, :, None, :] * lift[..., None]
        length = numpy.concatenate([numpy.zeros((count, 1), dtype=numpy.float32), numpy.cumsum(numpy.linalg.norm(spine[:, 1:] - spine[:, :-1], axis=-1), axis=1)], axis=1)
        offset = self.rng.uniform(0.0, 8.0, (count, 1, 3)).astype(numpy.float32)
        loc = numpy.stack([numpy.broadcast_to(length[:, :, None], reach.shape), reach, lift], axis=-1).reshape(count, steps * across, 3) + offset
        col = (spread(color, count, steps)[:, :, None, :] * (1.0 - shade * numpy.abs(u))[None, None, :, None]).reshape(count, steps * across, 3)
        prm = numpy.empty(points.shape, dtype=numpy.float32)
        prm[..., 0] = scalar(rough, count, steps)[:, :, None]
        prm[..., 1] = self.rng.random((count, 1, 1), dtype=numpy.float32)
        prm[..., 2] = numpy.linspace(0.0, 1.0, steps, dtype=numpy.float32)[None, :, None]
        lane = numpy.arange(across - 1)
        base = (numpy.arange(steps - 1) * across)[:, None]
        faces = {4: numpy.stack([base + lane, base + across + lane, base + across + lane + 1, base + lane + 1], axis=-1).reshape(-1, 4)}
        self.emit(material, points.reshape(count, steps * across, 3), faces, col, prm.reshape(count, steps * across, 3), loc)

    def stars(self, material, center, radius, points=6, rise=0.5, droop=0.3, inner=0.45, color=(0.1, 0.2, 0.05), tip=None, rough=0.9, tilt=0.25):
        center = numpy.asarray(center, dtype=numpy.float32)
        count = len(center)
        radius = numpy.broadcast_to(numpy.asarray(radius, dtype=numpy.float32), (count,))
        rim = 2 * points
        even = numpy.arange(rim) % 2 == 0
        angle = numpy.arange(rim) * (math.pi / points) + self.rng.uniform(0.0, tau, (count, 1))
        reach = numpy.where(even, 1.0, inner)[None, :] * radius[:, None] * self.rng.uniform(0.75, 1.15, (count, rim))
        x = numpy.cos(angle) * reach
        y = numpy.sin(angle) * reach
        lean = self.rng.normal(0.0, tilt, (count, 2))
        z = numpy.where(even, -droop, rise * 0.35)[None, :] * radius[:, None] + x * lean[:, 0:1] + y * lean[:, 1:2]
        top = center + numpy.stack([numpy.zeros(count), numpy.zeros(count), rise * radius], axis=1)
        vertices = numpy.concatenate([top[:, None, :], center[:, None, :] + numpy.stack([x, y, z], axis=-1)], axis=1).astype(numpy.float32)
        color = spread(color, count, 1)[:, 0, :]
        tip = color * 0.7 if tip is None else spread(tip, count, 1)[:, 0, :]
        col = numpy.concatenate([color[:, None, :], numpy.where(even[None, :, None], tip[:, None, :], (color * 0.55)[:, None, :])], axis=1)
        prm = numpy.empty(vertices.shape, dtype=numpy.float32)
        prm[..., 0] = scalar(rough, count, 1)
        prm[..., 1] = self.rng.random((count, 1), dtype=numpy.float32)
        prm[..., 2] = numpy.concatenate([numpy.zeros(1), numpy.ones(rim)])[None, :]
        step = numpy.arange(rim)
        faces = {3: numpy.stack([numpy.zeros(rim, dtype=numpy.int64), 1 + step, 1 + (step + 1) % rim], axis=-1)}
        self.emit(material, vertices, faces, col, prm, vertices - center[:, None, :] + self.rng.uniform(0.0, 8.0, (count, 1, 3)).astype(numpy.float32))

    def grit(self, material, center, size, color, rough=0.9, level=1, lump=0.22, euler=None):
        base, faces = icosphere(level)
        center = numpy.asarray(center, dtype=numpy.float32)
        count = len(center)
        size = numpy.asarray(size, dtype=numpy.float32)
        size = numpy.broadcast_to(size[:, None] if size.ndim == 1 else size, (count, 3))
        swell = numpy.clip(1.0 + lump * self.rng.normal(0.0, 1.0, (count, len(base))), 0.5, 1.6).astype(numpy.float32)
        local = base[None, :, :] * swell[..., None] * size[:, None, :]
        rotation = euler_matrix(self.rng.uniform(0.0, tau, (count, 3)) if euler is None else euler).astype(numpy.float32)
        local = numpy.einsum('mij,mvj->mvi', rotation, local)
        col = numpy.broadcast_to(spread(color, count, 1), local.shape)
        prm = numpy.empty(local.shape, dtype=numpy.float32)
        prm[..., 0] = scalar(rough, count, 1)
        prm[..., 1] = self.rng.random((count, 1), dtype=numpy.float32)
        prm[..., 2] = 0.0
        self.emit(material, center[:, None, :] + local, {3: faces}, col, prm, local + self.rng.uniform(0.0, 8.0, (count, 1, 3)).astype(numpy.float32))

    def plates(self, material, center, radius, thick, color, rough=0.85, rings=3, sectors=12, ragged=0.22, dome=0.0, tilt=0.0, edge=None, stretch=(0.55, 1.0), bend=0.0, corners=0):
        center = numpy.asarray(center, dtype=numpy.float32)
        count = len(center)
        radius = numpy.broadcast_to(numpy.asarray(radius, dtype=numpy.float32), (count,))
        thick = numpy.broadcast_to(numpy.asarray(thick, dtype=numpy.float32), (count,))
        angle = numpy.arange(sectors) * (tau / sectors)
        outline = numpy.ones((count, sectors))
        if corners:
            turn = numpy.sort((numpy.arange(corners)[None, :] + self.rng.uniform(0.15, 0.85, (count, corners))) * (tau / corners), axis=1)
            far = self.rng.uniform(1.0 - ragged * 1.6, 1.0 + ragged, (count, corners))
            for corner in range(corners):
                a1 = turn[:, corner:corner + 1]
                a2 = turn[:, (corner + 1) % corners:(corner + 1) % corners + 1]
                r1 = far[:, corner:corner + 1]
                r2 = far[:, (corner + 1) % corners:(corner + 1) % corners + 1]
                wide = numpy.mod(a2 - a1, tau)
                from_first = numpy.mod(angle[None, :] - a1, tau)
                inside = from_first < wide
                chord = r1 * r2 * numpy.sin(wide) / numpy.maximum(r1 * numpy.sin(from_first) + r2 * numpy.sin(wide - from_first), 1e-6)
                outline = numpy.where(inside, chord, outline)
            outline = numpy.clip(outline + self.rng.normal(0.0, ragged * 0.12, (count, sectors)), 0.3, 1.8)
        else:
            for harmonic in (2, 3, 4, 5):
                outline += ragged * self.rng.uniform(0.2, 1.0, (count, 1)) / (harmonic - 1) * numpy.cos(harmonic * angle[None, :] + self.rng.uniform(0.0, tau, (count, 1)))
            outline = numpy.clip(outline + self.rng.normal(0.0, ragged * 0.3, (count, sectors)), 0.35, 1.8)
        yaw = self.rng.uniform(0.0, tau, (count, 1))
        squash = self.rng.uniform(stretch[0], stretch[1], (count, 1))
        lean = self.rng.normal(0.0, tilt, (count, 2)) if tilt else numpy.zeros((count, 2))
        curve = self.rng.normal(0.0, 1.0, (count, 1)) * bend
        rows = [numpy.stack([numpy.zeros(count), numpy.zeros(count), thick + dome * radius], axis=1)[:, None, :]]
        for ring in list(range(1, rings + 1)) + [rings]:
            rho = ring / rings
            lx = numpy.cos(angle)[None, :] * outline * rho * radius[:, None]
            ly = numpy.sin(angle)[None, :] * outline * rho * radius[:, None] * squash
            x = lx * numpy.cos(yaw) - ly * numpy.sin(yaw)
            y = lx * numpy.sin(yaw) + ly * numpy.cos(yaw)
            z = thick[:, None] + dome * radius[:, None] * (1.0 - rho * rho) + curve * lx * lx / numpy.maximum(radius[:, None], 1e-6) + x * lean[:, 0:1] + y * lean[:, 1:2]
            rows.append(numpy.stack([x, y, z if len(rows) <= rings else z - thick[:, None]], axis=-1))
        vertices = numpy.concatenate(rows, axis=1).astype(numpy.float32)
        step = numpy.arange(sectors)
        quads = []
        for ring in range(rings):
            first = 1 + ring * sectors
            quads.append(numpy.stack([first + step, first + sectors + step, first + sectors + (step + 1) % sectors, first + (step + 1) % sectors], axis=-1))
        faces = {3: numpy.stack([numpy.zeros(sectors, dtype=numpy.int64), 1 + step, 1 + (step + 1) % sectors], axis=-1), 4: numpy.concatenate(quads)}
        color = spread(color, count, 1)[:, 0, :]
        edge = color * 0.75 if edge is None else spread(edge, count, 1)[:, 0, :]
        col = numpy.concatenate([numpy.broadcast_to(color[:, None, :], (count, 1 + rings * sectors, 3)), numpy.broadcast_to(edge[:, None, :], (count, sectors, 3))], axis=1)
        prm = numpy.empty(vertices.shape, dtype=numpy.float32)
        prm[..., 0] = scalar(rough, count, 1)
        prm[..., 1] = self.rng.random((count, 1), dtype=numpy.float32)
        prm[..., 2] = numpy.concatenate([numpy.zeros(1), numpy.repeat(numpy.arange(1, rings + 1) / rings, sectors), numpy.ones(sectors)])[None, :]
        self.emit(material, center[:, None, :] + vertices, faces, col, prm, vertices + self.rng.uniform(0.0, 8.0, (count, 1, 3)).astype(numpy.float32))

    def variant(self, group, vertices, faces, material, col=None, prm=None):
        if group not in self.groups:
            self.groups[group] = bpy.data.collections.new(group)
            self.extents[group] = []
        vertices = numpy.asarray(vertices, dtype=numpy.float32)
        faces = faces if isinstance(faces, dict) else {3: faces}
        mesh = make_mesh(group, vertices, faces, {"col": numpy.ones_like(vertices) if col is None else col, "prm": numpy.zeros_like(vertices) if prm is None else prm})
        mesh.materials.append(self.materials[material])
        self.groups[group].objects.link(bpy.data.objects.new("%s_%04d" % (group, len(self.extents[group])), mesh))
        self.extents[group].append(numpy.abs(vertices).max(axis=0))
        return len(self.extents[group]) - 1

    def place(self, group, position, euler, scale, variant, tint, var=None, ofs=None):
        position = numpy.asarray(position, dtype=numpy.float32)
        count = len(position)
        scale = numpy.asarray(scale, dtype=numpy.float32)
        scale = numpy.broadcast_to(scale[:, None] if scale.ndim == 1 else scale, (count, 3))
        variant = numpy.broadcast_to(numpy.asarray(variant, dtype=numpy.int32), (count,))
        extent = numpy.asarray(self.extents[group], dtype=numpy.float32)[variant]
        index, shift = self.copies(position[:, :2], (extent * scale).max(axis=1))
        moved = position[index].copy()
        moved[:, :2] += shift
        mesh = bpy.data.meshes.new(group + "_points")
        mesh.vertices.add(len(index))
        mesh.vertices.foreach_set("co", moved.ravel())
        tint = numpy.broadcast_to(numpy.asarray(tint, dtype=numpy.float32), (count, 3))
        var = numpy.zeros((count, 3), dtype=numpy.float32) if var is None else numpy.broadcast_to(numpy.asarray(var, dtype=numpy.float32), (count, 3))
        ofs = self.rng.uniform(0.0, 8.0, (count, 3)) if ofs is None else ofs
        for key, values in (("rot", euler), ("scl", scale), ("tint", tint), ("var", var), ("ofs", ofs)):
            attribute = mesh.attributes.new(key, 'FLOAT_VECTOR', 'POINT')
            attribute.data.foreach_set("vector", numpy.ascontiguousarray(numpy.asarray(values, dtype=numpy.float32)[index]).ravel())
        attribute = mesh.attributes.new("pick", 'INT', 'POINT')
        attribute.data.foreach_set("value", numpy.ascontiguousarray(variant[index]))
        holder = bpy.data.objects.new(group + "_points", mesh)
        bpy.context.scene.collection.objects.link(holder)
        modifier = holder.modifiers.new("scatter", 'NODES')
        modifier.node_group = self.instancer(group)
        self.instances += len(index)

    def instancer(self, group):
        name = "scatter_" + group
        if name in bpy.data.node_groups:
            return bpy.data.node_groups[name]
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        tree.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        source = tree.nodes.new('NodeGroupInput')
        target = tree.nodes.new('NodeGroupOutput')
        points = tree.nodes.new('GeometryNodeMeshToPoints')
        instance = tree.nodes.new('GeometryNodeInstanceOnPoints')
        info = tree.nodes.new('GeometryNodeCollectionInfo')
        info.inputs['Collection'].default_value = self.groups[group]
        info.inputs['Separate Children'].default_value = True
        info.inputs['Reset Children'].default_value = True
        instance.inputs['Pick Instance'].default_value = True
        tree.links.new(source.outputs[0], points.inputs['Mesh'])
        tree.links.new(points.outputs['Points'], instance.inputs['Points'])
        tree.links.new(info.outputs[0], instance.inputs['Instance'])
        for key, kind, socket in (("rot", 'FLOAT_VECTOR', 'Rotation'), ("scl", 'FLOAT_VECTOR', 'Scale'), ("pick", 'INT', 'Instance Index')):
            named = tree.nodes.new('GeometryNodeInputNamedAttribute')
            named.data_type = kind
            named.inputs['Name'].default_value = key
            tree.links.new(named.outputs['Attribute'], instance.inputs[socket])
        tree.links.new(instance.outputs['Instances'], target.inputs[0])
        return tree

    def ground(self, material, grid=None):
        grid = grid or self.grid
        pad = int(math.ceil(self.margin / self.size * grid))
        line = numpy.arange(-pad, grid + pad + 1, dtype=numpy.float64) * (self.size / grid)
        x, y = numpy.meshgrid(line, line)
        vertices = numpy.stack([x, y, sample(self.height, x, y, self.size)], axis=-1).reshape(-1, 3)
        side = len(line)
        index = numpy.arange(side * side, dtype=numpy.int64).reshape(side, side)
        quads = numpy.stack([index[:-1, :-1], index[:-1, 1:], index[1:, 1:], index[1:, :-1]], axis=-1).reshape(-1, 4)
        mesh = make_mesh("ground", vertices, {4: quads})
        mesh.materials.append(self.materials[material])
        bpy.context.scene.collection.objects.link(bpy.data.objects.new("ground", mesh))
        self.triangles += len(quads) * 2

    def build(self):
        for material, parts in self.soups.items():
            offsets = numpy.cumsum([0] + [len(part["v"]) for part in parts])
            faces = {}
            for part, offset in zip(parts, offsets):
                for arity, block in part["f"].items():
                    faces.setdefault(arity, []).append(block + offset)
            faces = {arity: numpy.concatenate(blocks) for arity, blocks in faces.items()}
            mesh = make_mesh(material, numpy.concatenate([part["v"] for part in parts]), faces, {key: numpy.concatenate([part[key] for part in parts]) for key in ("col", "prm", "loc")})
            mesh.materials.append(self.materials[material])
            bpy.context.scene.collection.objects.link(bpy.data.objects.new(material, mesh))
            count = sum(len(block) * (arity - 2) for arity, block in faces.items())
            self.triangles += count
            self.note("mesh %-12s %9d triangles" % (material, count))
        self.soups = {}

    def render(self, resolution, samples, distance):
        scene = bpy.context.scene
        layer = bpy.context.view_layer
        self.build()
        data = bpy.data.cameras.new("bake")
        data.type = 'ORTHO'
        data.ortho_scale = self.size
        data.clip_start = 0.05
        data.clip_end = 20.0
        camera = bpy.data.objects.new("bake", data)
        camera.location = (self.size * 0.5, self.size * 0.5, 6.0)
        scene.collection.objects.link(camera)
        scene.camera = camera
        world = bpy.data.worlds.new("bake")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
        world.light_settings.distance = distance
        scene.world = world
        scene.render.engine = 'CYCLES'
        device = accelerate(scene)
        scene.cycles.samples = samples
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.use_denoising = False
        scene.cycles.max_bounces = 0
        scene.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'
        scene.cycles.filter_width = 1.5
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        layer.use_pass_normal = True
        layer.use_pass_ambient_occlusion = True
        for name, kind in (("albedo", 'COLOR'), ("rough", 'VALUE'), ("height", 'VALUE'), ("mask", 'VALUE')):
            aov = layer.aovs.add()
            aov.name = name
            aov.type = kind
        scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
        scene.render.image_settings.color_depth = '32'
        scene.render.image_settings.exr_codec = 'ZIP'
        path = os.path.join(self.work, self.name + "_passes.exr")
        scene.render.filepath = path
        self.note("render %d px %d samples on %s, %d triangles, %d instances" % (resolution, samples, device, self.triangles, self.instances))
        bpy.ops.render.render(write_still=True)
        self.note("rendered")
        return path


def dilate(field, radius):
    result = field.copy()
    for oy in range(-radius, radius + 1):
        for ox in range(-radius, radius + 1):
            if (ox or oy) and ox * ox + oy * oy <= radius * radius:
                numpy.maximum(result, numpy.roll(field, (oy, ox), axis=(0, 1)), out=result)
    return result


def bounded(across, along, steep):
    slope = numpy.maximum(numpy.hypot(across, along), 1e-6)
    limit = steep * numpy.tanh(slope / steep) / slope
    return across * limit, along * limit


def levels(height, trim, stretch):
    low, high = numpy.percentile(height, [trim, 100.0 - trim])
    probe = height.ravel()[::7]

    def scales(pivot):
        below = max(pivot - low, 1e-9)
        above = max(high - pivot, 1e-9)
        base = 0.49 / max(below, above)
        return min(0.49 / below, base * stretch), min(0.49 / above, base * stretch)

    first, last = float(low), float(high)
    for step in range(48):
        pivot = (first + last) * 0.5
        under, over = scales(pivot)
        shifted = probe - pivot
        if 0.5 + float(numpy.where(shifted < 0.0, shifted * under, shifted * over).mean()) > 0.5:
            first = pivot
        else:
            last = pivot
    pivot = (first + last) * 0.5
    under, over = scales(pivot)
    shifted = height - pivot
    return numpy.clip(0.5 + numpy.where(shifted < 0.0, shifted * under, shifted * over), 0.0, 1.0), 1.0 / over, low, high


def compose(passes, pixel, bump=1.0, occlusion=1.0, cavity=0.35, trim=0.2, fill=0, soften=1.0, keep=1.0, steep=2.5, meso=8.0, envelope=1.0, water=None, level=None, stretch=1.0):
    albedo = numpy.clip(passes["albedo"], 0.0, 1.0)
    normal = passes["normal"].astype(numpy.float32)
    across, along = bounded(normal[..., 0] / numpy.maximum(normal[..., 2], 1e-3) * bump, -normal[..., 1] / numpy.maximum(normal[..., 2], 1e-3) * bump, steep)
    ao = numpy.clip(passes["ao"], 0.0, 1.0) ** occlusion
    albedo = albedo * (1.0 - cavity * (1.0 - ao))[..., None]
    height = passes["height"].astype(numpy.float32)
    rough = numpy.clip(passes["rough"], 0.03, 1.0).astype(numpy.float32)
    wet = numpy.zeros_like(height)
    if water is not None and level is not None:
        dark, gloss, edge = water
        depth = numpy.maximum(level - height, 0.0)
        wet = smoothstep(0.0, edge, depth)
        absorb = numpy.exp(-depth[..., None] / numpy.array([0.02, 0.016, 0.011], dtype=numpy.float32))
        albedo = albedo * (1.0 - wet[..., None] * (1.0 - dark * absorb))
        rough = rough * (1.0 - wet) + gloss * wet
        ao = ao + (1.0 - ao) * 0.6 * wet
        height = numpy.maximum(height, level)
    if fill:
        height = blur(dilate(height, fill), soften) * (1.0 - keep) + height * keep
    if meso:
        smooth = blur(height, meso)
        across = across - blur(across, meso) - (numpy.roll(smooth, -1, axis=1) - numpy.roll(smooth, 1, axis=1)) * (envelope * 0.5 / pixel)
        along = along - blur(along, meso) - (numpy.roll(smooth, -1, axis=0) - numpy.roll(smooth, 1, axis=0)) * (envelope * 0.5 / pixel)
        across, along = bounded(across, along, steep)
    across = across * (1.0 - wet)
    along = along * (1.0 - wet)
    normal = numpy.stack([across, along, numpy.ones_like(across)], axis=-1)
    normal /= numpy.linalg.norm(normal, axis=-1, keepdims=True)
    height = height.astype(numpy.float64)
    mapped, span, low, high = levels(height, trim, stretch)
    print("GROUND height metres min %.4f low %.4f mean %.4f high %.4f max %.4f, ao mean %.3f, up mean %.3f" % (height.min(), low, height.mean(), high, height.max(), ao.mean(), normal[..., 2].mean()), flush=True)
    return {"albedo": albedo.astype(numpy.float32), "normal": normal, "ao": ao.astype(numpy.float32), "rough": rough, "height": mapped.astype(numpy.float32), "relief": span}


def export(maps, directory, name):
    os.makedirs(directory, exist_ok=True)
    quantize = lambda value: numpy.clip(value * 255.0 + 0.5, 0.0, 255.0).astype(numpy.uint8)
    write_image(os.path.join(directory, name + "_diff_2k.jpg"), quantize(to_srgb(maps["albedo"])), quality=95)
    write_image(os.path.join(directory, name + "_nor_dx_2k.jpg"), quantize(maps["normal"] * 0.5 + 0.5), quality=95)
    write_image(os.path.join(directory, name + "_arm_2k.jpg"), quantize(numpy.stack([maps["ao"], maps["rough"], numpy.zeros_like(maps["ao"])], axis=-1)), quality=95)
    write_image(os.path.join(directory, name + "_disp_2k.jpg"), quantize(maps["height"]), quality=95)
