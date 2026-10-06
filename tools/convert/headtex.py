import bpy
import math
import os
import numpy

import texels
import faces

eye_local = numpy.array([[0.032, -0.086, 0.099], [-0.032, -0.086, 0.099]])


def load_image(path, colorspace):
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = colorspace
    data = numpy.empty(image.size[0] * image.size[1] * 4, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    width, height = image.size
    bpy.data.images.remove(image)
    return data.reshape(height, width, 4)


def save_image(path, data, colorspace, alpha=False):
    height, width = data.shape[:2]
    rgba = numpy.ones((height, width, 4), dtype=numpy.float32)
    rgba[:, :, :data.shape[2]] = numpy.clip(data, 0.0, 1.0)
    image = bpy.data.images.new(os.path.basename(path), width, height, alpha=alpha)
    image.colorspace_settings.name = colorspace
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)
    print("SAVED", path)


class canvas:
    def __init__(self, data, size, head_now, scale):
        triangles, corner_triangles = faces.triangulate(data["sizes"], data["corners"])
        uv = data["uv"][corner_triangles]
        covered, owner, weights = texels.rasterize(uv, size)
        covered, owner, weights = texels.conservative(uv, size, covered, owner, weights)
        self.size = size
        self.covered = covered
        self.owner = owner
        self.weights = weights
        points = data["points"]
        normals = faces.smooth_normals(points, data["sizes"], data["corners"])
        self.position = texels.interpolate(points[triangles], owner, weights).astype(numpy.float32)
        normal = texels.interpolate(normals[triangles], owner, weights)
        self.normal = (normal / numpy.maximum(numpy.linalg.norm(normal, axis=1), 1e-9)[:, None]).astype(numpy.float32)
        self.local = ((self.position - head_now) / scale).astype(numpy.float32)
        self.scale = scale
        a = points[triangles[:, 0]]
        b = points[triangles[:, 1]]
        c = points[triangles[:, 2]]
        ua = uv[:, 0] * size
        ub = uv[:, 1] * size
        uc = uv[:, 2] * size
        e1 = b - a
        e2 = c - a
        d1 = ub - ua
        d2 = uc - ua
        determinant = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
        determinant = numpy.where(numpy.abs(determinant) < 1e-12, 1e-12, determinant)
        du = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / determinant[:, None]
        dv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / determinant[:, None]
        self.jacobian_u = du[owner].astype(numpy.float32)
        self.jacobian_v = dv[owner].astype(numpy.float32)
        mask = numpy.zeros(size * size, dtype=bool)
        mask[covered] = True
        self.mask = mask.reshape(size, size)
        print("CANVAS", size, "covered", len(covered))

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
        flat = image.reshape(self.size * self.size, -1)
        return flat[self.covered]

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


def ellipse(local, center, radii, mirror=True):
    point = local.astype(numpy.float64)
    if mirror:
        point = numpy.stack([numpy.abs(point[:, 0]), point[:, 1], point[:, 2]], axis=1)
    q = (point - numpy.asarray(center)) / numpy.asarray(radii)
    return numpy.sum(q * q, axis=1)


def soft(local, center, radii, mirror=True, power=1.0):
    return numpy.exp(-ellipse(local, center, radii, mirror) * power)


def eye_distance(local):
    point = numpy.stack([numpy.abs(local[:, 0]), local[:, 1], local[:, 2]], axis=1).astype(numpy.float64)
    return numpy.linalg.norm(point - eye_local[0], axis=1)


def luma(rgb):
    return rgb @ numpy.array([0.2126, 0.7152, 0.0722])


def splat(size, points, values, radius=0.8):
    extra = values.shape[1] - 1
    accumulation = numpy.zeros((size, size, max(extra, 1)), dtype=numpy.float64)
    weight = numpy.zeros((size, size), dtype=numpy.float64)
    base = numpy.floor(points).astype(numpy.int64)
    reach = int(math.ceil(radius)) + 1
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            x = base[:, 0] + dx
            y = base[:, 1] + dy
            distance = numpy.hypot(x + 0.5 - points[:, 0], y + 0.5 - points[:, 1])
            w = numpy.clip(1.0 - distance / radius, 0.0, 1.0)
            valid = (w > 0.0) & (x >= 0) & (x < size) & (y >= 0) & (y < size)
            if not valid.any():
                continue
            numpy.add.at(weight, (y[valid], x[valid]), w[valid] * values[valid, 0])
            if extra > 0:
                numpy.add.at(accumulation, (y[valid], x[valid]), (w[valid] * values[valid, 0])[:, None] * values[valid, 1:])
    return weight, accumulation


def strokes(sheet, roots, directions, lengths, widths, strength, rng, bend=0.0, taper=0.7, step=0.45):
    size = sheet.size
    samples = []
    values = []
    guard = getattr(sheet, "guard", None)
    for index in range(len(roots)):
        length = lengths[index]
        count = max(2, int(length / step))
        t = numpy.linspace(0.0, 1.0, count)
        curl = bend * rng.uniform(-1.0, 1.0)
        direction = directions[index]
        normal = numpy.array([-direction[1], direction[0]])
        path = roots[index][None, :] + direction[None, :] * (t * length)[:, None] + normal[None, :] * (curl * length * t * t)[:, None]
        alpha = strength[index] * (1.0 - taper * t ** 1.5)
        if guard is not None:
            column = numpy.clip(path[:, 0].astype(numpy.int64), 0, size - 1)
            row = numpy.clip(path[:, 1].astype(numpy.int64), 0, size - 1)
            labels = guard[row, column]
            alpha = alpha * (labels == labels[0])
        samples.append(path)
        values.append(numpy.stack([alpha, t], axis=1))
    samples = numpy.concatenate(samples)
    values = numpy.concatenate(values)
    weight, accumulation = splat(size, samples, numpy.c_[values[:, 0], values[:, 1]], widths if numpy.isscalar(widths) else float(numpy.mean(widths)))
    coverage = 1.0 - numpy.exp(-weight * 1.6)
    along = accumulation[:, :, 0] / numpy.maximum(weight, 1e-9)
    return coverage, along


def sample_roots(sheet, density, count, rng):
    probability = numpy.clip(density, 0.0, None)
    total = probability.sum()
    if total <= 0.0 or count <= 0:
        return numpy.zeros(0, dtype=numpy.int64)
    chosen = rng.choice(len(probability), size=count, replace=True, p=probability / total)
    return chosen


def texel_xy(sheet, indices, rng):
    flat = sheet.covered[indices]
    y = flat // sheet.size
    x = flat % sheet.size
    return numpy.stack([x + rng.uniform(0.0, 1.0, len(flat)), y + rng.uniform(0.0, 1.0, len(flat))], axis=1)


def uv_directions(sheet, indices, world):
    direction = sheet.to_uv(world, indices)
    return direction / numpy.maximum(numpy.linalg.norm(direction, axis=1), 1e-9)[:, None]


def tangent_toward(normal, target):
    projected = target - normal * numpy.sum(target * normal, axis=1)[:, None]
    return projected / numpy.maximum(numpy.linalg.norm(projected, axis=1), 1e-9)[:, None]


def growth_beard(local, normal):
    down = numpy.array([0.0, 0.0, -1.0])
    forward = numpy.array([0.0, -1.0, 0.0])
    side = numpy.stack([numpy.sign(local[:, 0]), numpy.zeros(len(local)), numpy.zeros(len(local))], axis=1)
    chin = texels.smoothstep(0.035, 0.012, numpy.abs(local[:, 0])) * texels.smoothstep(0.03, -0.02, local[:, 2])
    neck = texels.smoothstep(-0.005, -0.03, local[:, 2])
    target = down[None, :] * (1.0 - 0.6 * neck[:, None]) + forward[None, :] * (0.35 * chin[:, None] - 0.6 * neck[:, None]) + side * 0.15
    return tangent_toward(normal.astype(numpy.float64), target)


def beard_mask(local):
    x = numpy.abs(local[:, 0]).astype(numpy.float64)
    y = local[:, 1].astype(numpy.float64)
    z = local[:, 2].astype(numpy.float64)
    upper = 0.058 - 0.35 * texels.smoothstep(0.02, 0.07, x) * (x - 0.02) + 0.012 * texels.smoothstep(0.045, 0.07, x)
    cheek = texels.smoothstep(upper + 0.004, upper - 0.004, z)
    lip_gap = 1.0 - soft(local, (0.0, -0.125, 0.027), (0.026, 0.03, 0.0075), False, 1.5) * texels.smoothstep(0.03, 0.02, x)
    front = texels.smoothstep(0.03, 0.0, y + 0.04 * texels.smoothstep(0.06, 0.08, x))
    neck = texels.smoothstep(-0.075, -0.04, z + 0.25 * (y + 0.06) * texels.smoothstep(0.0, 1.0, 1.0))
    sideburn = soft(local, (0.07, -0.02, 0.07), (0.012, 0.02, 0.03), True) * texels.smoothstep(0.1, 0.07, z)
    return numpy.clip(numpy.maximum(cheek * front * neck, sideburn) * lip_gap, 0.0, 1.0)


def lip_mask(sheet, color):
    local = sheet.local
    region = soft(local, (0.0, -0.123, 0.026), (0.03, 0.025, 0.013), False, 1.0)
    rgb = color.astype(numpy.float64)
    red = rgb[:, 0] / numpy.maximum(rgb[:, 1], 1e-3)
    skin_red = numpy.median(red[region > 0.3]) if (region > 0.3).any() else 1.6
    lips = texels.smoothstep(skin_red * 0.98, skin_red * 1.12, red) * texels.smoothstep(0.35, 0.8, region)
    return lips


def hairline(local, spec):
    point = local.astype(numpy.float64)
    center = numpy.asarray(spec["center"])
    q = point - center
    theta = numpy.degrees(numpy.arctan2(numpy.abs(q[:, 0]), -q[:, 1]))
    angles = numpy.array([a for a, h in spec["line"]])
    heights = numpy.array([h for a, h in spec["line"]])
    line = numpy.interp(theta, angles, heights)
    ear = soft(local, (0.078, 0.004, 0.08), (0.014, 0.021, 0.027), True, 1.0)
    return point[:, 2] - line - ear * 0.05


def paint_scalp(sheet, rgb, inside, spec, rng):
    local = sheet.local.astype(numpy.float64)
    normal = sheet.normal.astype(numpy.float64)
    base = texels.to_linear(numpy.asarray(spec["root"]))
    tip = texels.to_linear(numpy.asarray(spec["tip"]))
    tone = texels.noise(local, 60.0, 5, 3)
    fine = texels.noise(local * numpy.array([1.0, 1.0, 1.0]), 900.0, 9, 2)
    painted = base[None, :] * (0.75 + 0.5 * tone[:, None]) * (0.85 + 0.3 * fine[:, None])
    target = numpy.asarray(spec["flow"])
    direction = tangent_toward(normal, (numpy.asarray(target)[None, :] - local))
    count = int(spec["strands"])
    roots = sample_roots(sheet, inside, count, rng)
    if len(roots):
        xy = texel_xy(sheet, roots, rng)
        uvdir = uv_directions(sheet, roots, direction[roots])
        scale = 1.0 / numpy.maximum(numpy.linalg.norm(sheet.jacobian_u[roots], axis=1), 1e-9)
        lengths = numpy.clip(rng.uniform(spec["length"][0], spec["length"][1], len(roots)) * scale, 3.0, 400.0)
        coverage, along = strokes(sheet, xy, uvdir, lengths, 0.9, rng.uniform(0.35, 0.8, len(roots)), rng, 0.08, 0.3)
        covered = sheet.sample(coverage[:, :, None])[:, 0]
        light = tip[None, :] * (0.8 + 0.4 * tone[:, None])
        painted = painted * (1.0 - covered[:, None] * 0.3) + light * (covered[:, None] * 0.35)
    return rgb * (1.0 - inside[:, None]) + painted * inside[:, None]


def micro_height(sheet, spec, rng):
    local = sheet.local.astype(numpy.float64)
    position = sheet.position.astype(numpy.float64)
    nose = soft(local, (0.0, -0.135, 0.065), (0.02, 0.03, 0.03), False)
    cheeks = soft(local, (0.045, -0.095, 0.06), (0.03, 0.03, 0.03), True)
    pore_scale = 1.0 / (0.0011 + 0.0005 * numpy.clip(nose + cheeks * 0.6, 0.0, 1.0))
    nearest, second, identity = texels.cells(position, 900.0, 11)
    pores = -numpy.exp(-(nearest / 0.28) ** 2) * (0.6 + 0.8 * nose + 0.4 * cheeks)
    network_a, network_b, network_id = texels.cells(position, 320.0, 17)
    creases = -numpy.exp(-((network_b - network_a) / 0.06) ** 2) * 0.5
    height = (pores * 0.000012 + creases * 0.000008) * spec["micro"]
    return height


def line_field(local, points, width, depth, mirror=True):
    point = local.astype(numpy.float64)
    if mirror:
        point = numpy.stack([numpy.abs(point[:, 0]), point[:, 1], point[:, 2]], axis=1)
    best = numpy.full(len(point), numpy.inf)
    along = numpy.zeros(len(point))
    total = sum(numpy.linalg.norm(numpy.asarray(points[i + 1]) - numpy.asarray(points[i])) for i in range(len(points) - 1))
    walked = 0.0
    for index in range(len(points) - 1):
        a = numpy.asarray(points[index], dtype=numpy.float64)
        b = numpy.asarray(points[index + 1], dtype=numpy.float64)
        ab = b - a
        length = numpy.linalg.norm(ab)
        t = numpy.clip((point - a) @ ab / max(length * length, 1e-12), 0.0, 1.0)
        distance = numpy.linalg.norm(point - (a + t[:, None] * ab), axis=1)
        closer = distance < best
        best = numpy.where(closer, distance, best)
        along = numpy.where(closer, (walked + t * length) / max(total, 1e-9), along)
        walked += length
    fade = texels.smoothstep(0.0, 0.25, along) * texels.smoothstep(1.0, 0.7, along)
    return -depth * numpy.exp(-(best / width) ** 2) * fade


def wrinkle_height(sheet, spec):
    local = sheet.local
    height = numpy.zeros(len(local))
    for points, width, depth in spec.get("wrinkles", []):
        height += line_field(local, points, width, depth)
    return height


def height_to_normal(sheet, height_image):
    size = sheet.size
    dx = numpy.zeros_like(height_image)
    dy = numpy.zeros_like(height_image)
    dx[:, 1:-1] = (height_image[:, 2:] - height_image[:, :-2]) * 0.5
    dy[1:-1, :] = (height_image[2:, :] - height_image[:-2, :]) * 0.5
    ju = numpy.linalg.norm(sheet.jacobian_u, axis=1)
    jv = numpy.linalg.norm(sheet.jacobian_v, axis=1)
    su = sheet.image(ju)[:, :, 0]
    sv = sheet.image(jv)[:, :, 0]
    slope_x = dx / numpy.maximum(su, 1e-7)
    slope_y = dy / numpy.maximum(sv, 1e-7)
    return slope_x, slope_y


def combine_normals(base, slope_x, slope_y):
    n = numpy.stack([base[:, :, 0] - slope_x, base[:, :, 1] - slope_y, base[:, :, 2]], axis=2)
    return n / numpy.maximum(numpy.linalg.norm(n, axis=2), 1e-9)[:, :, None]


def decode_normal(image, directx=True):
    n = image[:, :, :3].astype(numpy.float64) * 2.0 - 1.0
    if directx:
        n[:, :, 1] = -n[:, :, 1]
    return n / numpy.maximum(numpy.linalg.norm(n, axis=2), 1e-9)[:, :, None]


def encode_normal(n):
    return numpy.clip(n * 0.5 + 0.5, 0.0, 1.0)


hairlines = {
    "female": {"center": (0.0, 0.0, 0.085), "line": [(0.0, 0.176), (20.0, 0.175), (40.0, 0.168), (55.0, 0.153), (64.0, 0.138), (72.0, 0.118), (80.0, 0.092), (88.0, 0.09), (96.0, 0.104), (106.0, 0.095), (116.0, 0.07), (135.0, 0.04), (155.0, 0.002), (180.0, -0.012)]},
    "male": {"center": (0.0, 0.0, 0.085), "line": [(0.0, 0.168), (20.0, 0.17), (38.0, 0.167), (52.0, 0.152), (62.0, 0.135), (70.0, 0.112), (78.0, 0.08), (86.0, 0.085), (94.0, 0.105), (104.0, 0.1), (113.0, 0.07), (135.0, 0.035), (155.0, 0.0), (180.0, -0.012)]},
}

looks = {
    "male": {
        "micro": 0.7,
        "tan": (0.98, 0.95, 0.92),
        "sun": 0.55,
        "stubble": 7000,
        "stubble_color": (0.03, 0.022, 0.017),
        "stubble_shadow": 0.3,
        "wrinkles": [
            ([(0.0, -0.103, 0.149), (0.015, -0.101, 0.1495), (0.03, -0.096, 0.148), (0.043, -0.087, 0.146)], 0.0006, 0.00005),
            ([(0.0, -0.1, 0.161), (0.016, -0.098, 0.162), (0.031, -0.093, 0.161), (0.044, -0.084, 0.158)], 0.0006, 0.00006),
            ([(0.0, -0.096, 0.173), (0.017, -0.094, 0.174), (0.032, -0.089, 0.172)], 0.0007, 0.00004),
            ([(0.052, -0.076, 0.105), (0.058, -0.071, 0.109), (0.064, -0.064, 0.114)], 0.0004, 0.00006),
            ([(0.053, -0.075, 0.099), (0.06, -0.069, 0.1), (0.067, -0.061, 0.1)], 0.0004, 0.00007),
            ([(0.052, -0.076, 0.093), (0.058, -0.071, 0.088), (0.064, -0.065, 0.082)], 0.0004, 0.00005),
            ([(0.017, -0.119, 0.052), (0.024, -0.114, 0.036), (0.029, -0.109, 0.02), (0.032, -0.102, 0.006)], 0.0012, 0.00016),
            ([(0.019, -0.106, 0.083), (0.03, -0.103, 0.081), (0.042, -0.097, 0.083)], 0.0006, 0.00005),
            ([(0.004, -0.121, 0.123), (0.006, -0.12, 0.13), (0.007, -0.118, 0.137)], 0.0005, 0.00005),
        ],
        "lip_lines": 0.000018,
        "hair": None,
        "scalp_tint": (0.085, 0.062, 0.048),
        "hairline_strokes": 5200,
        "grade": (0.84, 1.08),
        "relight": 0.5,
        "freckles": 0.0,
        "roughness_bias": 0.05,
    },
    "female": {
        "micro": 0.5,
        "tan": (0.89, 0.825, 0.77),
        "grade": (0.88, 0.93),
        "relight": 0.4,
        "sun": 0.5,
        "stubble": 0,
        "wrinkles": [
            ([(0.053, -0.075, 0.1), (0.06, -0.069, 0.101), (0.066, -0.062, 0.101)], 0.0004, 0.000025),
            ([(0.052, -0.076, 0.094), (0.058, -0.071, 0.089), (0.063, -0.066, 0.084)], 0.0004, 0.00002),
            ([(0.017, -0.119, 0.052), (0.023, -0.114, 0.037), (0.028, -0.109, 0.022)], 0.0012, 0.00007),
        ],
        "lip_lines": 0.000014,
        "hair": {"center": hairlines["female"]["center"], "line": hairlines["female"]["line"], "root": (0.12, 0.08, 0.05), "tip": (0.24, 0.16, 0.1), "flow": (0.0, 0.105, 0.03), "strands": 60000, "length": (0.008, 0.02), "wisps": 5200},
        "brows": [(0.0105, 0.1148, 0.0064), (0.02, 0.118, 0.0066), (0.029, 0.1208, 0.006), (0.037, 0.1222, 0.005), (0.045, 0.1212, 0.0038), (0.0535, 0.1172, 0.0024)],
        "brow_color": (0.105, 0.074, 0.054),
        "brow_strokes": 4200,
        "freckles": 1.0,
        "lip_tint": (0.62, 0.3, 0.28),
        "contour": 0.6,
        "seam_roughness": 0.6,
        "roughness_bias": 0.05,
    },
}


def sunburn(local):
    nose = soft(local, (0.0, -0.14, 0.07), (0.016, 0.03, 0.03), False)
    bridge = soft(local, (0.0, -0.128, 0.09), (0.01, 0.03, 0.02), False)
    cheeks = soft(local, (0.042, -0.1, 0.07), (0.02, 0.03, 0.017), True)
    forehead = soft(local, (0.0, -0.1, 0.16), (0.04, 0.05, 0.03), False) * 0.6
    ears = soft(local, (0.08, 0.008, 0.105), (0.012, 0.02, 0.018), True) * 0.8
    chin = soft(local, (0.0, -0.12, -0.005), (0.02, 0.03, 0.015), False) * 0.4
    return numpy.clip(nose + bridge * 0.7 + cheeks + forehead + ears + chin, 0.0, 1.0)


def freckle_field(sheet, amount):
    local = sheet.local.astype(numpy.float64)
    position = sheet.position.astype(numpy.float64)
    density = numpy.clip(soft(local, (0.0, -0.13, 0.08), (0.012, 0.03, 0.02), False) * 0.9 + soft(local, (0.035, -0.105, 0.075), (0.028, 0.03, 0.02), True) * 0.8 + soft(local, (0.0, -0.1, 0.16), (0.05, 0.04, 0.03), False) * 0.25, 0.0, 1.0) * amount
    nearest, second, identity = texels.cells(position, 420.0, 41)
    cell = numpy.floor(position * 420.0)
    size = 0.18 + 0.2 * texels.hash_points(cell, 43)
    spot = texels.smoothstep(size, size * 0.45, nearest) * (identity < density * 0.75)
    strength = 0.35 + 0.65 * texels.hash_points(cell, 47)
    return spot * strength


def mole_field(sheet, count, seed):
    position = sheet.position.astype(numpy.float64)
    nearest, second, identity = texels.cells(position, 45.0, seed)
    local = sheet.local.astype(numpy.float64)
    face = soft(local, (0.0, -0.09, 0.07), (0.07, 0.08, 0.1), False)
    return texels.smoothstep(0.1, 0.05, nearest) * (identity < count) * face


def brow_field(sheet, points):
    local = sheet.local.astype(numpy.float64)
    x = numpy.abs(local[:, 0])
    z = local[:, 2]
    front = texels.smoothstep(-0.07, -0.09, local[:, 1])
    xs = numpy.array([p[0] for p in points])
    zs = numpy.array([p[1] for p in points])
    widths = numpy.array([p[2] for p in points])
    center = numpy.interp(x, xs, zs)
    width = numpy.interp(x, xs, widths)
    along = numpy.clip((x - xs[0]) / (xs[-1] - xs[0]), 0.0, 1.0)
    inside = texels.smoothstep(1.0, 0.6, numpy.abs(z - center) / numpy.maximum(width * 0.5, 1e-6))
    ends = texels.smoothstep(xs[0] - 0.003, xs[0] + 0.002, x) * texels.smoothstep(xs[-1] + 0.002, xs[-1] - 0.003, x)
    return inside * ends * front, along, center


def brow_direction(sheet, along):
    local = sheet.local.astype(numpy.float64)
    side = numpy.sign(local[:, 0])
    count = len(local)
    up = numpy.stack([0.25 * side, numpy.zeros(count), numpy.ones(count)], axis=1)
    out = numpy.stack([side, numpy.zeros(count), 0.3 * numpy.ones(count)], axis=1)
    down = numpy.stack([side, numpy.zeros(count), -0.3 * numpy.ones(count)], axis=1)
    t = along[:, None]
    blend = up * (1.0 - texels.smoothstep(0.0, 0.35, t)) + out * texels.smoothstep(0.0, 0.35, t) * (1.0 - texels.smoothstep(0.6, 1.0, t)) + down * texels.smoothstep(0.6, 1.0, t)
    return tangent_toward(sheet.normal.astype(numpy.float64), blend)


def hair_strokes(sheet, density, count, direction, length_range, width, opacity, bend, taper, scale, rng):
    roots = sample_roots(sheet, density, count, rng)
    if not len(roots):
        return numpy.zeros(len(sheet.covered))
    xy = texel_xy(sheet, roots, rng)
    uvdir = uv_directions(sheet, roots, direction[roots])
    texel = 1.0 / numpy.maximum(numpy.linalg.norm(sheet.jacobian_u[roots], axis=1), 1e-9)
    lengths = numpy.clip(rng.uniform(length_range[0], length_range[1], len(roots)) * texel * scale, 1.5, 400.0)
    coverage, t = strokes(sheet, xy, uvdir, lengths, width, rng.uniform(opacity[0], opacity[1], len(roots)), rng, bend, taper)
    return sheet.sample(coverage[:, :, None])[:, 0]


def fitted(image, size):
    source = image.shape[0]
    if size > source:
        return texels.upscale(image, size // source)
    if size < source:
        return texels.downsample(image, source // size)
    return numpy.asarray(image, dtype=numpy.float64)


def graded(rgb, look):
    saturation, gain = look.get("grade", (1.0, 1.0))
    level = luma(rgb)[:, None]
    return (level + (rgb - level) * saturation) * gain


def neck_relight(sheet, rgb, neck, eyes, strength):
    point, normal = neck
    position = sheet.position.astype(numpy.float64)
    height = (position - numpy.asarray(point)) @ numpy.asarray(normal)
    zone = texels.smoothstep(0.075 * sheet.scale, 0.02 * sheet.scale, height)
    if zone.max() <= 0.0 or strength <= 0.0:
        return rgb
    luminance = luma(rgb)
    smooth = texels.grid_fill(position, luminance, numpy.ones(len(luminance)), 0.008 * sheet.scale, (1, 2), 0.2)[:, 0]
    cheeks = soft(sheet.local, (0.047, -0.092, 0.06), (0.026, 0.03, 0.026), True) > 0.5
    target = float(numpy.median(luminance[cheeks & (eyes > 0.03)]))
    lift = numpy.clip(target / numpy.maximum(smooth, 1e-4), 1.0, 2.4) ** strength
    print("NECK relight target", round(target, 4), "seam level", round(float(numpy.median(smooth[zone > 0.9])), 4))
    return rgb * (1.0 + (lift[:, None] - 1.0) * zone[:, None])


def head_maps(root, name, data, head_now, scale, directory, prefix, size=4096, occlusion=None, seed=5, neck=None):
    rng = numpy.random.default_rng(seed)
    look = looks[name]
    key = faces.specs[name]["face"]
    sheet = canvas(data, size, head_now, scale)
    local = sheet.local.astype(numpy.float64)
    color_source = load_image(faces.texture_path(root, key, "color"), 'sRGB')[:, :, :3]
    normal_source = load_image(faces.texture_path(root, key, "normal"), 'Non-Color')[:, :, :3]
    spec_source = load_image(faces.texture_path(root, key, "specular"), 'Non-Color')[:, :, :1]
    color_image = texels.to_linear(fitted(color_source, size))
    rgb = sheet.sample(color_image).astype(numpy.float64)
    del color_image
    specular = sheet.sample(fitted(spec_source, size))[:, 0]
    eyes = eye_distance(local)
    lips = lip_mask(sheet, rgb)
    rgb = graded(rgb, look)
    collar = numpy.zeros(len(local))
    height = numpy.zeros(len(local))
    scalp = numpy.zeros(len(local))
    position = sheet.position.astype(numpy.float64)
    if look["hair"] is not None:
        spec = look["hair"]
        above = hairline(local, spec) + (texels.noise(position, 90.0, 51, 2) - 0.5) * 0.008
        scalp = texels.smoothstep(-0.004, 0.013, above)
        luminance = luma(rgb)
        face_zone = 1.0 - texels.smoothstep(-0.007, 0.006, above)
        middle = soft(local, (0.0, -0.1, 0.07), (0.05, 0.05, 0.04), False) > 0.5
        skin_reference = numpy.median(luminance[middle & (eyes > 0.03) & (lips < 0.1)])
        warmth = rgb[:, 0] / numpy.maximum(rgb[:, 1], 1e-4)
        inner = (local[:, 1] > -0.105) & (numpy.abs(local[:, 0]) < 0.03) & (local[:, 2] > 0.0) & (local[:, 2] < 0.055)
        nostril = soft(local, (0.0, -0.128, 0.052), (0.018, 0.012, 0.008), False) > 0.3
        protected = (eyes < 0.024) | inner | nostril | (lips > 0.2)
        hairness = texels.smoothstep(0.66, 0.46, luminance / skin_reference) * texels.smoothstep(2.7, 2.2, warmth) * (~protected)
        around_ear = soft(local, (0.078, 0.004, 0.08), (0.032, 0.042, 0.048), True) > 0.22
        hairness = numpy.maximum(hairness, texels.smoothstep(0.62, 0.44, luminance / skin_reference) * around_ear * (~protected))
        hairness = numpy.clip(texels.grid_fill(position, hairness, numpy.ones(len(hairness)), 0.002 * scale, (1,), 0.0)[:, 0] * 2.4, 0.0, 1.0)
        brows_old = soft(local, (0.035, -0.105, 0.121), (0.03, 0.03, 0.011), True) * texels.smoothstep(0.85, 0.6, luminance / skin_reference) * (eyes > 0.021)
        brows_old = numpy.clip(texels.grid_fill(position, brows_old, numpy.ones(len(brows_old)), 0.0015 * scale, (1,), 0.0)[:, 0] * 1.6, 0.0, 1.0)
        removal = numpy.clip(numpy.maximum(hairness, brows_old), 0.0, 1.0)
        hole = removal * face_zone
        known = ((removal < 0.1) & (~protected) & (face_zone > 0.5)).astype(numpy.float64)
        patch = texels.grid_fill(position, rgb, known, 0.0025 * scale)
        detail = texels.noise(position, 700.0, 3, 3) - 0.5
        speck = texels.noise(position, 2600.0, 4, 2) - 0.5
        patch = patch * (1.0 + detail[:, None] * 0.07 + speck[:, None] * 0.05)
        rgb = rgb * (1.0 - hole[:, None]) + patch * hole[:, None]
        print("HAIR removal texels", int((hole > 0.5).sum()), "skin reference", round(float(skin_reference), 4))
        luminance = luma(rgb)
        face_region = face_zone * (eyes > 0.0205) * (1.0 - lips)
        low = texels.grid_fill(position, luminance, face_region > 0.5, 0.006 * scale, (1, 2, 4), 0.5)[:, 0]
        reference = numpy.median(luminance[middle & (eyes > 0.03)])
        flatten = numpy.clip(reference / numpy.maximum(low, 1e-4), 0.75, 1.3) ** 0.12
        rgb = rgb * (1.0 + (flatten[:, None] - 1.0) * face_region[:, None])
        blurred = sheet.sample(texels.gaussian(sheet.image(rgb), 2)).astype(numpy.float64)
        rgb = rgb + (blurred - rgb) * (0.06 * face_region)[:, None]
        rgb = paint_scalp(sheet, rgb, scalp, spec, rng)
        fringe = numpy.exp(-((above + 0.001) / 0.008) ** 2) * (eyes > 0.03)
        flow = tangent_toward(sheet.normal.astype(numpy.float64), numpy.asarray(spec["flow"])[None, :] - local)
        cover = hair_strokes(sheet, fringe, spec.get("wisps", 2800), flow, (0.004, 0.013), 0.8, (0.25, 0.65), 0.35, 0.5, scale, rng)
        wisp_tone = texels.to_linear(numpy.asarray(spec["root"])) * 1.25
        rgb = rgb * (1.0 - cover[:, None] * 0.8) + wisp_tone[None, :] * (cover[:, None] * 0.8)
        height += -0.00004 * scalp
    if neck is not None:
        rgb = neck_relight(sheet, rgb, neck, eyes, look.get("relight", 0.0))
        collar = texels.smoothstep(0.05 * scale, 0.02 * scale, (position - numpy.asarray(neck[0])) @ numpy.asarray(neck[1]))
    if look.get("scalp_tint"):
        above = hairline(local, hairlines[name]) + (texels.noise(position, 110.0, 53, 2) - 0.5) * 0.009
        scalp = texels.smoothstep(-0.006, 0.009, above)
        luminance = luma(rgb)
        level = numpy.median(luminance[scalp > 0.9]) if (scalp > 0.9).any() else 0.2
        tone = texels.to_linear(numpy.asarray(look["scalp_tint"]))
        tinted = tone[None, :] * numpy.clip(luminance / max(level, 1e-3), 0.4, 1.8)[:, None]
        rgb = rgb + (tinted - rgb) * (scalp * 0.86)[:, None]
        edge = numpy.exp(-((above + 0.003) / 0.0105) ** 2) * (eyes > 0.03)
        field = tangent_toward(sheet.normal.astype(numpy.float64), numpy.tile(numpy.array([0.0, 0.35, 1.0]), (len(local), 1)))
        cover = hair_strokes(sheet, edge, look.get("hairline_strokes", 0), field, (0.003, 0.008), 0.8, (0.25, 0.6), 0.2, 0.5, scale, rng)
        rgb = rgb * (1.0 - cover[:, None] * 0.85) + tone[None, :] * (cover[:, None] * 0.85)
    if look.get("brows"):
        field, along, center = brow_field(sheet, look["brows"])
        field = field * (0.5 + 0.5 * texels.smoothstep(0.28, 0.62, texels.noise(position, 1100.0, 57, 2))) * (0.62 + 0.38 * texels.smoothstep(0.0, 0.3, along))
        brow_tone = texels.to_linear(numpy.asarray(look["brow_color"]))
        rgb = rgb * (1.0 - field[:, None] * 0.3) + (rgb * 0.45 + brow_tone * 0.55) * (field[:, None] * 0.3)
        cover = hair_strokes(sheet, field, look["brow_strokes"], brow_direction(sheet, along), (0.003, 0.0065), 0.75, (0.35, 0.8), 0.15, 0.6, scale, rng)
        rgb = rgb * (1.0 - cover[:, None] * 0.88) + brow_tone * (cover[:, None] * 0.88)
    face_skin = (eyes > 0.0205).astype(numpy.float64)
    tan = numpy.asarray(look["tan"])
    rgb = rgb * (1.0 + (tan[None, :] - 1.0) * face_skin[:, None])
    contour = look.get("contour", 0.0)
    if contour > 0.0:
        hollow = soft(local, (0.047, -0.08, 0.037), (0.02, 0.03, 0.018), True) * 0.9
        socket = soft(local, (0.03, -0.1, 0.109), (0.02, 0.02, 0.0075), True) * 0.8
        flank = soft(local, (0.0115, -0.118, 0.085), (0.005, 0.015, 0.02), True) * 0.7
        temple = soft(local, (0.06, -0.06, 0.12), (0.015, 0.03, 0.03), True) * 0.4
        under = soft(local, (0.04, -0.07, -0.012), (0.03, 0.04, 0.012), True) * 0.5
        shade = numpy.clip(hollow + socket + flank + temple + under, 0.0, 1.0) * face_skin * contour
        rgb = rgb * (1.0 - shade[:, None] * numpy.array([0.1, 0.14, 0.15]))
        ridge = numpy.clip(soft(local, (0.0, -0.136, 0.086), (0.004, 0.015, 0.025), False) + soft(local, (0.05, -0.088, 0.078), (0.016, 0.02, 0.01), True) * 0.7, 0.0, 1.0) * face_skin * contour
        rgb = rgb * (1.0 + ridge[:, None] * 0.06)
    burn = sunburn(local) * look["sun"] * face_skin
    red = numpy.array([0.62, 0.26, 0.2])
    rgb = rgb + (red[None, :] * luma(rgb)[:, None] / luma(red[None, :])[0] - rgb) * (burn * 0.3)[:, None]
    if look["freckles"] > 0.0:
        spots = freckle_field(sheet, look["freckles"])
        rgb = rgb * (1.0 - spots[:, None] * numpy.array([0.16, 0.24, 0.3]))
        flush = soft(local, (0.043, -0.1, 0.06), (0.022, 0.03, 0.02), True) * 0.5
        rgb = rgb * (1.0 + flush[:, None] * numpy.array([0.06, -0.03, -0.03]))
    if look.get("lip_tint"):
        tint = texels.to_linear(numpy.asarray(look["lip_tint"]))
        rgb = rgb + (tint[None, :] * luma(rgb)[:, None] / max(float(luma(tint[None, :])[0]), 1e-3) - rgb) * (lips * 0.35)[:, None]
    moles = mole_field(sheet, 0.08 if name == "male" else 0.05, seed + 3)
    rgb = rgb * (1.0 - moles[:, None] * numpy.array([0.45, 0.55, 0.6]))
    beard = numpy.zeros(len(local))
    if look["stubble"]:
        beard = beard_mask(local) * (1.0 - collar)
        shadow = numpy.array([0.8, 0.8, 0.84])
        rgb = rgb * (1.0 + (shadow[None, :] - 1.0) * (beard * look["stubble_shadow"])[:, None])
        cover = hair_strokes(sheet, beard, look["stubble"] * 4, growth_beard(local, sheet.normal.astype(numpy.float64)), (0.0008, 0.0022), 0.7, (0.45, 0.9), 0.25, 0.5, scale, rng)
        stubble_tone = texels.to_linear(numpy.asarray(look["stubble_color"]))
        rgb = rgb * (1.0 - cover[:, None] * 0.85) + stubble_tone * (cover[:, None] * 0.85)
        height += cover * 0.00002
    wrinkles = wrinkle_height(sheet, look)
    height += wrinkles
    crease = numpy.clip(-wrinkles / 0.00012, 0.0, 1.0)
    rgb = rgb * (1.0 - crease[:, None] * numpy.array([0.05, 0.07, 0.07]))
    lip_x = local[:, 0].astype(numpy.float64)
    height += -look["lip_lines"] * (0.5 + 0.5 * numpy.cos(2.0 * numpy.pi * lip_x / 0.0011)) ** 6 * lips
    height += micro_height(sheet, look, rng) * face_skin * (1.0 - scalp)
    albedo = sheet.image(texels.to_srgb(numpy.clip(rgb, 0.0, 1.0)))
    save_image(os.path.join(directory, prefix + "_head_albedo.png"), albedo, 'sRGB')
    del albedo
    base_normal = decode_normal(fitted(normal_source, size))
    flat_weight = sheet.image(numpy.maximum(collar, scalp * 0.85 if look["hair"] is not None else 0.0))[:, :, 0]
    base_normal = base_normal * (1.0 - flat_weight[:, :, None]) + numpy.array([0.0, 0.0, 1.0]) * flat_weight[:, :, None]
    base_normal /= numpy.maximum(numpy.linalg.norm(base_normal, axis=2), 1e-9)[:, :, None]
    height_image = sheet.image(height)[:, :, 0]
    slope_x, slope_y = height_to_normal(sheet, height_image)
    normal = combine_normals(base_normal, slope_x, slope_y)
    save_image(os.path.join(directory, prefix + "_head_nor_gl.png"), encode_normal(normal), 'Non-Color')
    del normal, base_normal, slope_x, slope_y, height_image
    roughness = numpy.clip(0.64 - specular * 0.75, 0.2, 0.78)
    tzone = soft(local, (0.0, -0.12, 0.09), (0.016, 0.04, 0.09), False) + soft(local, (0.0, -0.1, 0.155), (0.035, 0.05, 0.03), False) * 0.7 + soft(local, (0.0, -0.118, -0.002), (0.018, 0.03, 0.015), False) * 0.6
    margin = texels.smoothstep(0.0208, 0.0192, eyes) * (eyes > 0.0175)
    roughness = roughness - 0.08 * numpy.clip(tzone, 0.0, 1.0) - 0.1 * lips
    roughness = roughness * (1.0 - margin) + 0.12 * margin
    roughness = roughness + 0.1 * beard
    roughness = roughness * (1.0 - scalp) + 0.84 * scalp
    roughness = numpy.clip(roughness + look["roughness_bias"], 0.08, 0.9)
    roughness = roughness * (1.0 - collar) + look.get("seam_roughness", 0.62) * collar
    ambient = numpy.ones(len(local)) if occlusion is None else sheet.sample(occlusion[:, :, None])[:, 0]
    orm = numpy.stack([numpy.clip(0.3 + 0.7 * ambient, 0.0, 1.0), roughness, numpy.zeros(len(local))], axis=1)
    save_image(os.path.join(directory, prefix + "_head_orm.png"), sheet.image(orm), 'Non-Color')
    return sheet
