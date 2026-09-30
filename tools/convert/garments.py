import os
import numpy

import anatomy
import texels
import headtex
import bodytex


def smooth(low, high, value):
    return texels.smoothstep(low, high, value)


def male_fields(points, setup):
    joints = setup["skeleton"]["joints"]
    s = setup["figure"]["scale"]
    pelvis = numpy.asarray(joints["Bip01 Pelvis"])
    x = numpy.abs(points[:, 0])
    z = points[:, 2]
    front = smooth(0.03 * s, -0.07 * s, points[:, 1] - pelvis[1])
    top = pelvis[2] + (0.118 - 0.022 * front) * s
    hem = pelvis[2] - 0.215 * s
    waist = top - z
    leg = z - hem
    inside = numpy.minimum(numpy.minimum(waist, leg), 0.27 * s - x)
    return {"briefs": {"inside": inside, "band": waist, "hem": leg}}


def female_fields(points, setup):
    joints = setup["skeleton"]["joints"]
    s = setup["figure"]["scale"]
    landmarks = setup["figure"]["landmarks"]
    pelvis = numpy.asarray(joints["Bip01 Pelvis"])
    chest = numpy.asarray(joints["Bip01 Spine2"])
    shoulder = numpy.asarray(joints["Bip01 L UpperArm"])
    x = numpy.abs(points[:, 0])
    y = points[:, 1]
    z = points[:, 2]
    front = smooth(0.03 * s, -0.07 * s, y - pelvis[1])
    top = pelvis[2] + (0.084 - 0.024 * front) * s
    gusset = 0.028 * s
    side = 0.2 * s
    side_z = pelvis[2] + 0.03 * s
    low_front = pelvis[2] - 0.1 * s
    low_back = pelvis[2] - 0.118 * s
    u = numpy.clip((x - gusset) / (side - gusset), 0.0, 1.0)
    z_front = low_front + (side_z - low_front) * u ** 0.85
    z_back = low_back + (side_z - low_back) * u ** 2.4
    back = smooth(-0.03 * s, 0.05 * s, y - pelvis[1])
    opening = z_front * (1.0 - back) + z_back * back - 0.022 * s * smooth(gusset * 1.35, gusset * 0.7, x)
    waist = top - z
    leg = z - opening
    briefs = numpy.minimum(numpy.minimum(waist, leg), 0.27 * s - x)
    lower_center, outward, radii = landmarks["breast_l"]
    fold = lower_center[2] - radii[2]
    band_low = fold - 0.034 * s
    nipple = landmarks["nipple_l"][2]
    inner = 0.08 * s
    outer = 0.118 * s
    flank = 0.155 * s
    behind = smooth(-0.02 * s, 0.04 * s, y - chest[1])
    center_top = (nipple + 0.062 * s) * (1.0 - behind) + (chest[2] + 0.075 * s) * behind
    depth = (0.1 - 0.055 * behind) * s
    crown = center_top + depth
    neckline = numpy.where(z >= crown, x / inner - 1.0, numpy.sqrt((x / inner) ** 2 + (numpy.clip(crown - z, 0.0, None) / depth) ** 2) - 1.0) * inner
    side_top = shoulder[2] - (0.118 - 0.02 * behind) * s
    rise = 0.095 * s
    reach = flank - outer
    peak = side_top + rise
    armhole = numpy.where(x >= flank, (side_top - z) / rise, numpy.where(z >= peak, (outer - x) / reach, numpy.sqrt((numpy.clip(flank - x, 0.0, None) / reach) ** 2 + (numpy.clip(peak - z, 0.0, None) / rise) ** 2) - 1.0)) * reach
    upper = numpy.minimum(neckline, armhole)
    band = z - band_low
    bra = numpy.minimum(numpy.minimum(band, upper), 0.205 * s - x)
    return {"briefs": {"inside": briefs, "band": waist, "hem": leg}, "bra": {"inside": bra, "band": band, "hem": upper}}


fields_of = {"male": male_fields, "female": female_fields}

fabrics = {
    "male": {"briefs": {"color": (0.35, 0.325, 0.3), "band": (0.3, 0.285, 0.27), "band_width": 0.03, "seams": "fly"}},
    "female": {"briefs": {"color": (0.335, 0.365, 0.36), "band": (0.28, 0.305, 0.3), "band_width": 0.022, "seams": "plain"}, "bra": {"color": (0.335, 0.365, 0.36), "band": (0.28, 0.305, 0.3), "band_width": 0.03, "seams": "cups"}},
}


def region(points, setup):
    parts = fields_of[setup["name"]](points, setup)
    inside = numpy.full(len(points), -1.0)
    owner = numpy.zeros(len(points), dtype=numpy.int32)
    for index, key in enumerate(sorted(parts)):
        better = parts[key]["inside"] > inside
        inside = numpy.where(better, parts[key]["inside"], inside)
        owner = numpy.where(better, index, owner)
    return inside, owner, parts


def edge_distance(points, setup, step=0.0015):
    value = region(points, setup)[0]
    slope = numpy.stack([(region(points + numpy.array(offset) * step, setup)[0] - value) / step for offset in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))], axis=1)
    return value / numpy.maximum(numpy.linalg.norm(slope, axis=1), 1.0)


def clip_mesh(points, triangles, uv, field):
    inside = field > 0.0
    counts = inside[triangles].sum(axis=1)
    whole = numpy.flatnonzero(counts == 3)
    mixed = numpy.flatnonzero((counts > 0) & (counts < 3))
    extra = []
    cache = {}
    out_triangles = [triangles[whole]]
    out_uv = [uv[whole]]

    def crossing(a, b):
        key = (min(a, b), max(a, b))
        if key not in cache:
            first, second = key
            t = field[first] / (field[first] - field[second])
            cache[key] = len(points) + len(extra)
            extra.append((first, second, float(numpy.clip(t, 0.0, 1.0))))
        index = cache[key]
        first, second, t = extra[index - len(points)]
        return index, (t if first == a else 1.0 - t)

    clipped_triangles = []
    clipped_uv = []
    for face in mixed:
        corners = triangles[face]
        polygon = []
        for k in range(3):
            a = int(corners[k])
            b = int(corners[(k + 1) % 3])
            if inside[a]:
                polygon.append((a, uv[face, k]))
            if inside[a] != inside[b]:
                index, t = crossing(a, b)
                polygon.append((index, uv[face, k] + (uv[face, (k + 1) % 3] - uv[face, k]) * t))
        for k in range(1, len(polygon) - 1):
            clipped_triangles.append((polygon[0][0], polygon[k][0], polygon[k + 1][0]))
            clipped_uv.append((polygon[0][1], polygon[k][1], polygon[k + 1][1]))
    if clipped_triangles:
        out_triangles.append(numpy.array(clipped_triangles, dtype=numpy.int64))
        out_uv.append(numpy.array(clipped_uv))
    all_triangles = numpy.concatenate(out_triangles)
    all_uv = numpy.concatenate(out_uv)
    used, compact = numpy.unique(all_triangles, return_inverse=True)
    return used, compact.reshape(-1, 3), all_uv, extra


def gathered(values, used, extra, count):
    table = numpy.zeros((len(used),) + values.shape[1:])
    original = used < count
    table[original] = values[used[original]]
    for slot in numpy.flatnonzero(~original):
        first, second, t = extra[used[slot] - count]
        table[slot] = values[first] * (1.0 - t) + values[second] * t
    return table


def gradient(shapes, points, epsilon=2e-5):
    value = anatomy.evaluate(shapes, points, 0.03)
    slope = numpy.stack([(anatomy.evaluate(shapes, points + numpy.array(offset) * epsilon, 0.03) - value) / epsilon for offset in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))], axis=1)
    return value, slope / numpy.maximum(numpy.linalg.norm(slope, axis=1), 1e-9)[:, None]


def membrane(points, triangles, shapes, clearance, pinned, iterations=44):
    shapes = [item for item in shapes if item.label != "nipple"]
    edges = numpy.unique(numpy.sort(numpy.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]]), axis=1), axis=0)
    points = points.copy()
    for iteration in range(iterations):
        total = numpy.zeros_like(points)
        count = numpy.zeros(len(points))
        numpy.add.at(total, edges[:, 0], points[edges[:, 1]])
        numpy.add.at(total, edges[:, 1], points[edges[:, 0]])
        numpy.add.at(count, edges[:, 0], 1.0)
        numpy.add.at(count, edges[:, 1], 1.0)
        average = total / numpy.maximum(count, 1.0)[:, None]
        points = points + (average - points) * (0.5 * (1.0 - pinned))[:, None]
        for settle in range(2):
            value, normal = gradient(shapes, points)
            points = points + normal * numpy.clip(clearance - value, 0.0, 0.004)[:, None]
    for settle in range(12):
        value, normal = gradient(shapes, points)
        short = numpy.clip(clearance - value, 0.0, 0.003)
        if float(short.max()) < 1e-5:
            break
        points = points + normal * short[:, None]
    value, normal = gradient(shapes, points)
    print("GARMENT clearance min", round(float(value.min()) * 1000.0, 2), "mm mean", round(float(value.mean()) * 1000.0, 2), "mm")
    return points


def pack_weights(table, count=4):
    order = numpy.argsort(-table, axis=1)[:, :count]
    values = numpy.take_along_axis(table, order, axis=1)
    values = numpy.maximum(values, 0.0)
    values = values / numpy.maximum(values.sum(axis=1), 1e-9)[:, None]
    return order.astype(numpy.int32), values.astype(numpy.float32)


def build(setup, shapes, points, triangles, uv, indices, values, names, clearance=0.0026):
    field = edge_distance(points, setup)
    used, faces, face_uv, extra = clip_mesh(points, triangles, uv, field)
    count = len(points)
    positions = gathered(points, used, extra, count)
    table = numpy.zeros((count, len(names)))
    for slot in range(indices.shape[1]):
        numpy.add.at(table, (numpy.arange(count), indices[:, slot]), values[:, slot])
    weights = gathered(table, used, extra, count)
    distance = numpy.clip(edge_distance(positions, setup), 0.0, None)
    ramp = smooth(0.0, 0.014, distance)
    pinned = 1.0 - smooth(0.0, 0.008, distance)
    lifted = membrane(positions, faces, shapes, 0.001 + (clearance - 0.001) * ramp, pinned)
    covered = numpy.all(field[triangles] > 0.016, axis=1)
    print("GARMENT vertices", len(positions), "triangles", len(faces), "cut edges", len(extra), "covered body triangles", int(covered.sum()))
    return lifted, faces, face_uv, pack_weights(weights), covered


def dashes(coordinate, period, fill):
    phase = coordinate / period
    return ((phase - numpy.floor(phase)) < fill).astype(numpy.float64)


def fabric_maps(setup, page, directory, prefix, seed=41):
    name = setup["name"]
    s = setup["figure"]["scale"]
    joints = setup["skeleton"]["joints"]
    pelvis = numpy.asarray(joints["Bip01 Pelvis"])
    points = page.position.astype(numpy.float64)
    inside, owner, parts = region(points, setup)
    edge = numpy.clip(edge_distance(points, setup), 0.0, None)
    keys = sorted(parts)
    color = numpy.zeros((len(points), 3))
    height = numpy.zeros(len(points))
    roughness = numpy.full(len(points), 0.9)
    theta = numpy.arctan2(points[:, 0], -(points[:, 1] - pelvis[1]))
    around = theta * 0.13 * s
    fade = texels.noise(points, 9.0, seed, 3)
    blotch = smooth(0.52, 0.78, texels.noise(points, 22.0, seed + 1, 3))
    grain = texels.noise(points, 1400.0, seed + 2, 2)
    weave = texels.noise(points * numpy.array([2600.0, 2600.0, 700.0]), 1.0, seed + 3, 1)
    pill = smooth(0.7, 0.9, texels.noise(points, 520.0, seed + 4, 2))
    folds = texels.noise(points * numpy.array([14.0, 14.0, 70.0]), 1.0, seed + 5, 3) - 0.5
    creases = texels.noise(points * numpy.array([55.0, 55.0, 16.0]), 1.0, seed + 6, 2) - 0.5
    for index, key in enumerate(keys):
        chosen = owner == index
        if not chosen.any():
            continue
        spec = fabrics[name][key]
        base = texels.to_linear(numpy.asarray(spec["color"]))
        band_tone = texels.to_linear(numpy.asarray(spec["band"]))
        band = smooth(spec["band_width"] * s, spec["band_width"] * s - 0.0012, parts[key]["band"][chosen])
        hem = smooth(0.0095, 0.0083, edge[chosen]) * (1.0 - band)
        tone = base[None, :] * (0.86 + 0.28 * fade[chosen, None]) * (0.95 + 0.1 * grain[chosen, None]) * (0.97 + 0.06 * weave[chosen, None])
        tone = tone * (1.0 - blotch[chosen, None] * numpy.array([0.16, 0.18, 0.2]))
        tone = tone * (1.0 + pill[chosen, None] * 0.12)
        ribs = 0.5 + 0.5 * numpy.sin(around[chosen] / 0.0019 * 2.0 * numpy.pi)
        tone = tone * (1.0 - band[:, None]) + band_tone[None, :] * (0.88 + 0.2 * ribs[:, None]) * (0.9 + 0.2 * fade[chosen, None]) * band[:, None]
        stitch_line = numpy.exp(-((edge[chosen] - 0.0072) / 0.0006) ** 2) * dashes(around[chosen] + points[chosen, 2] * 0.35, 0.0034, 0.62) * (1.0 - band)
        band_edge = numpy.exp(-((parts[key]["band"][chosen] - spec["band_width"] * s + 0.003) / 0.0006) ** 2) * dashes(around[chosen], 0.0034, 0.62)
        stitches = numpy.clip(stitch_line + band_edge, 0.0, 1.0)
        seam = numpy.zeros(int(chosen.sum()))
        x = points[chosen, 0]
        ahead = points[chosen, 1] < pelvis[1]
        if spec["seams"] == "fly":
            seam = numpy.maximum(seam, numpy.exp(-((numpy.abs(x) - 0.034 * s - 0.1 * numpy.clip(parts[key]["band"][chosen], 0.0, 0.2)) / 0.0011) ** 2) * ahead * smooth(0.19 * s, 0.17 * s, parts[key]["band"][chosen]))
            seam = numpy.maximum(seam, numpy.exp(-(x / 0.0011) ** 2) * (~ahead))
        elif spec["seams"] == "cups":
            seam = numpy.maximum(seam, numpy.exp(-(x / 0.0011) ** 2) * ahead * 0.8)
            seam = numpy.maximum(seam, numpy.exp(-((numpy.abs(x) - 0.128 * s) / 0.0011) ** 2) * 0.8)
        else:
            seam = numpy.maximum(seam, numpy.exp(-((numpy.abs(x) - 0.118 * s) / 0.0011) ** 2) * 0.8)
        rim = smooth(0.0016, 0.0, edge[chosen])
        fray = smooth(0.006, 0.0, edge[chosen]) * smooth(0.45, 0.8, texels.noise(points[chosen], 900.0, seed + 7, 2))
        tone = tone * (1.0 - hem[:, None] * 0.07) * (1.0 - seam[:, None] * 0.25) * (1.0 - stitches[:, None] * 0.3) * (1.0 - rim[:, None] * 0.35)
        tone = tone * (1.0 + fray[:, None] * 0.35)
        grime = smooth(0.035, 0.0, edge[chosen]) * (0.4 + 0.6 * fade[chosen]) * 0.22
        earth = numpy.array([0.16, 0.12, 0.09])
        tone = tone * (1.0 - grime[:, None]) + earth[None, :] * grime[:, None]
        color[chosen] = tone
        relief = band * (0.00045 + 0.00006 * ribs) + hem * 0.0003 + smooth(0.0, 0.002, edge[chosen]) * 0.00025
        relief = relief - seam * 0.00025 - stitches * 0.00008
        relief = relief + folds[chosen] * 0.0007 * (1.0 - band) + creases[chosen] * 0.00035 * (1.0 - band)
        relief = relief + (grain[chosen] - 0.5) * 0.00003 + (weave[chosen] - 0.5) * 0.00002 + pill[chosen] * 0.00004
        height[chosen] = relief
        roughness[chosen] = 0.9 - 0.05 * band + 0.05 * (grain[chosen] - 0.5) + 0.05 * grime
    sx, sy = bodytex.slopes(page, height)
    normal = numpy.stack([-sx, -sy, numpy.ones(len(points))], axis=1)
    normal /= numpy.linalg.norm(normal, axis=1)[:, None]
    shade = numpy.clip(1.0 + folds * 0.35 + creases * 0.2, 0.75, 1.0)
    headtex.save_image(os.path.join(directory, prefix + "_underwear_albedo.png"), page.image(texels.to_srgb(numpy.clip(color, 0.0, 1.0))), 'sRGB')
    headtex.save_image(os.path.join(directory, prefix + "_underwear_nor_gl.png"), page.image(headtex.encode_normal(normal)), 'Non-Color')
    headtex.save_image(os.path.join(directory, prefix + "_underwear_orm.png"), page.image(numpy.stack([shade, numpy.clip(roughness, 0.05, 1.0), numpy.zeros(len(points))], axis=1)), 'Non-Color')
