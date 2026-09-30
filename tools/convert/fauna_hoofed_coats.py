import math
import numpy
import fauna_hoofed_field as fields
import fauna_hoofed_paint as paint

smooth = fields.smoothstep


def tint(color, target, amount):
    target = numpy.asarray(target, dtype=numpy.float64)
    return color + ((target[None, :] if target.ndim == 1 else target) - color) * numpy.clip(amount, 0.0, 1.0)[:, None]


def ellipse(points, center, radii):
    q = (points - numpy.asarray(center)[None, :]) / numpy.asarray(radii)[None, :]
    return numpy.sqrt(numpy.sum(q * q, axis=1))


def segment(points, a, b):
    a = numpy.asarray(a, dtype=numpy.float64)
    ab = numpy.asarray(b, dtype=numpy.float64) - a
    t = numpy.clip(((points - a) @ ab) / float(ab @ ab), 0.0, 1.0)
    return numpy.linalg.norm(points - a - t[:, None] * ab, axis=1), t


def eye_paint(c, k, color, rough, relief, iris=(0.2, 0.11, 0.05), pupil_wide=0.62, pupil_tall=0.26):
    eye = c.blueprint["cage"]["eye"]
    ball = c.tagged("eyeball")
    center = numpy.asarray(eye["center"]) * numpy.array([1.0, 1.0, 1.0])
    mirrored = c.position * numpy.array([1.0, 1.0, 1.0])
    mirrored[:, 0] = numpy.abs(mirrored[:, 0])
    direction = mirrored - center[None, :]
    direction /= numpy.maximum(numpy.linalg.norm(direction, axis=1), 1e-9)[:, None]
    axis = fields.unit(eye["axis"])
    slit = fields.unit(numpy.asarray(eye["slit"]) - axis * float(numpy.asarray(eye["slit"]) @ axis))
    up = numpy.cross(axis, slit)
    a = direction @ slit
    b = direction @ up
    radial = numpy.sqrt(a * a + b * b)
    iris_mask = smooth(0.8, 0.72, radial)
    pupil = smooth(1.0, 0.8, numpy.sqrt((a / pupil_wide) ** 2 + (b / pupil_tall) ** 2))
    spokes = paint.value_noise(numpy.column_stack([numpy.arctan2(b, a) * 3.0, radial * 0.5, numpy.zeros(len(a))]), 0.12, 5)
    shade = numpy.tile(numpy.array([0.22, 0.17, 0.14]), (len(a), 1))
    shade = tint(shade, numpy.array(iris) * 1.0, iris_mask)
    shade = shade * (0.8 + 0.4 * spokes)[:, None]
    shade = tint(shade, (0.012, 0.012, 0.016), pupil)
    color[ball] = shade[ball]
    rough[ball] = 0.08
    relief[ball] = 0.0
    lid = c.tagged("head") & (numpy.linalg.norm(mirrored - center[None, :], axis=1) < eye["radius"] + 0.0042)
    return ball, lid


def deer(c, kind):
    stag = kind == "stag"
    k = c.blueprint["marks"]
    p = c.position
    n = c.normal
    count = len(p)
    side = c.side
    body = c.tagged("body")
    head = c.tagged("head", "nose", "chin")
    legs = c.tagged("fore_l", "fore_r", "hind_l", "hind_r")
    ears = c.tagged("ear_l", "ear_r")
    tail = c.tagged("tail")
    rump = c.tagged("rump")
    hoof = c.tagged("hoof", "hoof_sole", "hoof_top")
    antler = c.tagged("antler")
    mouth = c.tagged("mouth")
    nostril = c.tagged("nostril")
    neck_axis = fields.unit(k["neck_base"] - k["neck_top"])
    neckness = smooth(-0.42, -0.58, p[:, 1]) * body
    along = (p - k["nose"][None, :]) @ k["head_axis"]

    flow = numpy.tile(numpy.array([0.0, 1.0, -0.3]), (count, 1))
    flow = flow + (neck_axis[None, :] - flow) * neckness[:, None]
    flow[head] = k["head_axis"] + numpy.array([0.0, 0.0, -0.25])
    flow[legs] = numpy.array([0.0, 0.12, -1.0])
    flow[rump | tail] = numpy.array([0.0, 0.25, -1.0])
    ear_axis = fields.unit(c.blueprint["cage"]["ear"]["axis"])
    flow[ears] = ear_axis * numpy.array([1.0, 1.0, 1.0])
    flow[ears, 0] *= side[ears]
    flow[antler] = numpy.array([0.25, 0.3, 0.9])
    flow[antler, 0] *= side[antler]
    flow[hoof] = numpy.array([1.0, 0.0, 0.0])

    fine = c.fur(flow, 0.0034, 0.0013, 10, 1)
    coarse = c.fur(flow, 0.0085, 0.0028, 12, 2)
    blend = numpy.where(head | legs | ears, 0.72, 0.42)
    fur = fine * blend + coarse * (1.0 - blend)
    mottle = paint.fbm(p, 0.09, 3, 11)
    patch = paint.fbm(p, 0.03, 3, 12)

    color = numpy.tile(numpy.array([0.57, 0.335, 0.18]), (count, 1))
    dorsal = numpy.exp(-(p[:, 0] / 0.04) ** 2) * smooth(0.35, 0.85, n[:, 2]) * body
    color = tint(color, (0.3, 0.19, 0.11), dorsal * 0.7)
    under = smooth(-0.05, -0.7, n[:, 2]) * body * (1.0 - neckness)
    low = smooth(0.95, 0.72, p[:, 2]) * body * (1.0 - neckness)
    color = tint(color, (0.76, 0.66, 0.5), numpy.clip(under * 0.9 + low * 0.25, 0.0, 1.0))
    if stag:
        mane = neckness * smooth(0.5, -0.3, n[:, 2] * 0.6 + n[:, 1] * -0.8)
        color = tint(color, (0.36, 0.25, 0.16), numpy.clip(neckness * 0.35 + mane * 0.4, 0.0, 1.0))
    else:
        mane = numpy.zeros(count)

    inner = smooth(0.15, 0.7, -n[:, 0] * side) * legs
    color = tint(color, (0.74, 0.64, 0.5), inner * 0.85)
    shin = smooth(0.5, 0.2, p[:, 2]) * legs * (1.0 - inner)
    color = tint(color, (0.4, 0.28, 0.18), shin * 0.55)

    patch_shape = ellipse(p, (0.0, 0.66, 0.985), (0.135, 0.2, 0.19)) + (patch - 0.5) * 0.25
    facing = smooth(0.05, 0.45, n[:, 1])
    rump_mask = smooth(1.05, 0.85, patch_shape) * facing * (body | rump | legs | tail)
    border = smooth(0.25, 0.0, numpy.abs(patch_shape - 1.0)) * facing * smooth(0.98, 1.08, p[:, 2]) * (body | rump)
    color = tint(color, (0.87, 0.77, 0.58), rump_mask)
    color = tint(color, (0.22, 0.14, 0.09), border * 0.7)
    color[tail] = numpy.array([0.85, 0.74, 0.55])
    tail_top = tail & (n[:, 1] > 0.3) & (numpy.abs(p[:, 0]) < 0.012)
    color = tint(color, (0.4, 0.25, 0.14), tail_top * 0.8)

    face = head
    color[face] = numpy.array([0.52, 0.34, 0.2])
    crown = smooth(0.2, 0.8, n[:, 2]) * face * smooth(0.12, 0.3, along)
    color = tint(color, (0.4, 0.26, 0.16), crown * 0.45)
    muzzle = smooth(0.17, 0.04, along) * face
    color = tint(color, (0.47, 0.37, 0.29), muzzle * 0.8)
    jaw = smooth(-0.2, -0.75, n @ k["head_up"]) * face
    color = tint(color, (0.74, 0.66, 0.54), jaw * 0.7)
    chin = (c.tagged("chin") | (face & (((p - k["nose"][None, :]) @ k["head_up"]) < -0.016) & (along < 0.06))).astype(numpy.float64)
    color = tint(color, (0.82, 0.77, 0.66), chin * 0.9)
    mirrored = p.copy()
    mirrored[:, 0] = numpy.abs(mirrored[:, 0])
    lip_spot = smooth(0.022, 0.008, numpy.linalg.norm(mirrored - (k["mouth"] - k["head_axis"] * 0.03 - k["head_up"] * 0.006)[None, :], axis=1)) * face
    color = tint(color, (0.1, 0.07, 0.06), lip_spot * 0.85)
    pad = smooth(0.034, 0.024, numpy.linalg.norm(p - (k["nose"] + k["head_up"] * 0.006)[None, :], axis=1)) * (c.tagged("nose") | face) * smooth(-0.012, -0.004, (p - k["nose"][None, :]) @ k["head_up"])
    color = tint(color, (0.045, 0.04, 0.04), pad)
    eye_center = numpy.asarray(c.blueprint["cage"]["eye"]["center"])
    eye_distance = numpy.linalg.norm(mirrored - eye_center[None, :], axis=1)
    ring = smooth(0.06, 0.035, eye_distance) * face
    color = tint(color, (0.66, 0.52, 0.36), ring * 0.45)
    gland_a = eye_center + fields.unit(c.blueprint["cage"]["eye"]["axis"]) * 0.018 - k["head_axis"] * 0.024 - k["head_up"] * 0.006
    gland_b = gland_a - k["head_axis"] * 0.03 - k["head_up"] * 0.012
    gland, gland_t = segment(mirrored, gland_a, gland_b)
    gland_mask = smooth(0.007, 0.002, gland) * face
    color = tint(color, (0.1, 0.07, 0.06), gland_mask * 0.9)

    face_dir = numpy.asarray(c.blueprint["cage"]["ear"]["face"], dtype=numpy.float64)
    facing_in = smooth(0.0, 0.5, n[:, 0] * side * face_dir[0] + n[:, 1] * face_dir[1] + n[:, 2] * face_dir[2])
    color[ears] = numpy.array([0.47, 0.34, 0.23])
    color = tint(color, (0.84, 0.76, 0.62), facing_in * ears)
    ear_root = numpy.asarray(c.blueprint["cage"]["ear"]["root"])
    ear_along = (mirrored - ear_root[None, :]) @ ear_axis
    deep = smooth(0.06, 0.0, ear_along) * facing_in * ears
    color = tint(color, (0.5, 0.36, 0.33), deep * 0.6)
    tip = smooth(0.125, 0.165, ear_along) * ears
    color = tint(color, (0.22, 0.15, 0.1), tip * 0.75)

    grime = smooth(0.55, 0.75, paint.fbm(p, 0.05, 3, 21)) * smooth(0.45, 0.1, p[:, 2]) * legs
    color = tint(color, (0.3, 0.24, 0.17), grime * 0.35)
    furry = body | head | legs | ears | tail | rump
    shade = 0.74 + 0.46 * fur + (mottle - 0.5) * 0.14
    color = numpy.where(furry[:, None], color * shade[:, None], color)
    fleck = smooth(0.62, 0.9, fine) * furry
    color = tint(color, color * 1.18 + 0.03, fleck * 0.5)

    rough = numpy.full(count, 0.8)
    rough[furry] = 0.74 + 0.16 * (1.0 - fur[furry])
    rough = rough + (0.3 - rough) * pad
    relief = numpy.full(count, 0.0016)
    relief[head] = 0.0008
    relief[legs] = 0.0009
    relief[ears] = 0.0005
    relief[rump | tail] = 0.002
    relief = relief + mane * 0.0012
    relief = relief * (1.0 - pad) * (1.0 - gland_mask)

    color[mouth] = numpy.array([0.4, 0.18, 0.17]) * (0.8 + 0.3 * mottle[mouth])[:, None]
    rough[mouth] = 0.35
    relief[mouth] = 0.0
    color[nostril] = numpy.array([0.035, 0.025, 0.025])
    rough[nostril] = 0.4
    relief[nostril] = 0.0

    keratin = paint.fbm(p * numpy.array([1.0, 1.0, 6.0])[None, :], 0.02, 3, 31)
    wall = numpy.array([0.1, 0.085, 0.075])[None, :] * (0.75 + 0.5 * keratin)[:, None]
    wall = tint(wall, (0.3, 0.26, 0.21), smooth(0.012, 0.0, p[:, 2]) * 0.6)
    color[hoof] = wall[hoof]
    sole = c.tagged("hoof_sole")
    color[sole] = numpy.array([0.24, 0.21, 0.18]) * (0.8 + 0.4 * mottle[sole])[:, None]
    rough[hoof] = 0.42 + 0.2 * keratin[hoof]
    relief[hoof] = 0.0003

    if antler.any():
        travel = c.coord[:, 0]
        pointed = c.coord[:, 1]
        bark = numpy.array([0.34, 0.23, 0.14])[None, :] * (0.55 + 0.8 * coarse)[:, None]
        bark = tint(bark, (0.2, 0.13, 0.08), smooth(0.55, 0.3, fine) * 0.5)
        ivory = smooth(0.55, 0.95, travel) * pointed
        bark = tint(bark, (0.84, 0.78, 0.64), ivory)
        color[antler] = bark[antler]
        rough[antler] = (0.62 - 0.27 * ivory)[antler]
        relief[antler] = (0.0014 * (1.0 - ivory))[antler]

    ball, lid = eye_paint(c, k, color, rough, relief)
    color = tint(color, (0.07, 0.05, 0.045), lid * 0.95)
    rough = numpy.where(lid, 0.45, rough)
    relief = numpy.where(lid, 0.0002, relief)
    return {"color": numpy.clip(color, 0.0, 1.0), "rough": numpy.clip(rough, 0.04, 1.0), "height": fur, "relief": relief}


def coat(name, c):
    if name == "deer_stag":
        return deer(c, "stag")
    if name == "deer_hind":
        return deer(c, "hind")
    raise ValueError(name)
