import importlib
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


class palette:
    def __init__(self, c):
        self.c = c
        k = c.blueprint["marks"]
        self.k = k
        self.p = c.position
        self.n = c.normal
        self.count = len(self.p)
        self.side = c.side
        self.mirrored = self.p.copy()
        self.mirrored[:, 0] = numpy.abs(self.mirrored[:, 0])
        self.body = c.tagged("body", "lock")
        self.lock = c.tagged("lock")
        self.head = c.tagged("head", "nose", "chin")
        self.legs = c.tagged("fore_l", "fore_r", "hind_l", "hind_r")
        self.fore = c.tagged("fore_l", "fore_r")
        self.hind = c.tagged("hind_l", "hind_r")
        self.ears = c.tagged("ear_l", "ear_r")
        self.tail = c.tagged("tail")
        self.rump = c.tagged("rump")
        self.hoof = c.tagged("hoof", "hoof_sole", "hoof_top")
        self.sole = c.tagged("hoof_sole")
        self.mouth = c.tagged("mouth")
        self.nostril = c.tagged("nostril")
        self.ball = c.tagged("eyeball")
        self.furry = self.body | self.head | self.legs | self.ears | self.tail | self.rump
        self.along = (self.p - k["nose"][None, :]) @ k["head_axis"]
        self.height = (self.p - k["nose"][None, :]) @ k["head_up"]
        tube = self.body | c.tagged("head")
        self.around = numpy.where(tube, c.coord[:, 1] * 2.0, numpy.clip(0.5 - 0.5 * self.n[:, 2], 0.0, 1.0))
        self.ring = c.coord[:, 0]
        eye = c.blueprint["cage"]["eye"]
        self.eye_center = numpy.asarray(eye["center"], dtype=numpy.float64)
        self.eye_axis = fields.unit(eye["axis"])
        self.eye_radius = eye["radius"]
        self.eye_distance = numpy.linalg.norm(self.mirrored - self.eye_center[None, :], axis=1)
        lid = c.vertex_mask("eye")
        self.lid = smooth(0.97, 1.0, lid) * smooth(0.55, 1.0, c.coord[:, 0])
        self.lip = c.vertex_mask("lip")
        ear = c.blueprint["cage"]["ear"]
        self.ear_axis = fields.unit(ear["axis"])
        self.ear_root = numpy.asarray(ear["root"], dtype=numpy.float64)
        face = numpy.asarray(ear["face"], dtype=numpy.float64)
        self.ear_inner = smooth(0.0, 0.5, self.n[:, 0] * self.side * face[0] + self.n[:, 1] * face[1] + self.n[:, 2] * face[2]) * self.ears
        self.ear_along = ((self.mirrored - self.ear_root[None, :]) @ self.ear_axis) / ear["length"]
        self.inner_leg = smooth(0.1, 0.65, -self.n[:, 0] * self.side) * self.legs
        path = c.model["points"][numpy.array(c.model["meta"]["lip_upper"])] / c.scale
        self.lip_distance = numpy.full(self.count, 1.0)
        near = numpy.flatnonzero((self.along < float(((path - k["nose"][None, :]) @ k["head_axis"]).max()) + 0.03) & (self.head | self.mouth))
        for index in range(len(path) - 1):
            distance, travel = segment(self.mirrored[near], path[index], path[index + 1])
            self.lip_distance[near] = numpy.minimum(self.lip_distance[near], distance)

    def flow(self, body=(0.0, 1.0, -0.3), legs=(0.0, 0.12, -1.0), neck=None, neck_start=-0.42, neck_end=-0.58):
        k = self.k
        flow = numpy.tile(numpy.asarray(body, dtype=numpy.float64), (self.count, 1))
        axis = fields.unit(k["neck_base"] - k["neck_top"]) if neck is None else numpy.asarray(neck)
        self.neckness = smooth(neck_start, neck_end, self.p[:, 1]) * self.body
        flow = flow + (axis[None, :] - flow) * self.neckness[:, None]
        flow[self.head] = k["head_axis"] + numpy.array([0.0, 0.0, -0.25])
        flow[self.legs] = numpy.asarray(legs)
        flow[self.rump | self.tail] = numpy.array([0.0, 0.25, -1.0])
        flow[self.ears] = self.ear_axis
        flow[self.ears, 0] *= self.side[self.ears]
        antler = self.c.tagged("antler", "horn", "tusk")
        flow[antler] = numpy.array([0.25, 0.3, 0.9])
        flow[antler, 0] *= self.side[antler]
        flow[self.hoof] = numpy.array([1.0, 0.0, 0.0])
        return flow

    def eyes(self, color, rough, relief, iris=(0.2, 0.11, 0.05), wide=0.62, tall=0.26, skin=(0.07, 0.05, 0.045)):
        eye = self.c.blueprint["cage"]["eye"]
        direction = self.mirrored - self.eye_center[None, :]
        direction /= numpy.maximum(numpy.linalg.norm(direction, axis=1), 1e-9)[:, None]
        slit = fields.unit(numpy.asarray(eye["slit"]) - self.eye_axis * float(numpy.asarray(eye["slit"]) @ self.eye_axis))
        up = numpy.cross(self.eye_axis, slit)
        a = direction @ slit
        b = direction @ up
        radial = numpy.sqrt(a * a + b * b)
        iris_mask = smooth(0.82, 0.72, radial)
        pupil = smooth(1.0, 0.8, numpy.sqrt((a / wide) ** 2 + (b / tall) ** 2))
        spokes = paint.value_noise(numpy.column_stack([numpy.arctan2(b, a) * 3.0, radial * 0.5, numpy.zeros(len(a))]), 0.12, 5)
        shade = numpy.tile(numpy.array([0.2, 0.16, 0.13]), (len(a), 1))
        shade = tint(shade, numpy.array(iris), iris_mask)
        shade = shade * (0.8 + 0.4 * spokes)[:, None]
        shade = tint(shade, (0.012, 0.012, 0.016), pupil)
        color[self.ball] = shade[self.ball]
        rough[self.ball] = 0.08
        relief[self.ball] = 0.0
        color[:] = tint(color, skin, self.lid * 0.96)
        rough[:] = numpy.where(self.lid > 0.5, 0.42, rough)
        relief[:] = relief * (1.0 - self.lid)

    def keratin(self, color, rough, relief, wall=(0.1, 0.085, 0.075), wear=(0.3, 0.26, 0.21), under=(0.24, 0.21, 0.18)):
        grain = paint.fbm(self.p * numpy.array([1.0, 1.0, 6.0])[None, :], 0.02, 3, 31)
        shade = numpy.array(wall)[None, :] * (0.75 + 0.5 * grain)[:, None]
        shade = tint(shade, wear, smooth(0.012, 0.0, self.p[:, 2]) * 0.6)
        color[self.hoof] = shade[self.hoof]
        color[self.sole] = numpy.array(under) * (0.8 + 0.4 * grain[self.sole])[:, None]
        rough[self.hoof] = 0.42 + 0.2 * grain[self.hoof]
        relief[self.hoof] = 0.0003

    def cavity(self, color, rough, relief, flesh=(0.4, 0.18, 0.17), dark=(0.035, 0.025, 0.025), lip=(0.09, 0.065, 0.06)):
        line = smooth(0.0032, 0.0012, self.lip_distance) * self.head
        color[:] = tint(color, lip, line * 0.85)
        relief[:] = relief * (1.0 - line)
        color[self.mouth] = tint(numpy.tile(numpy.array(flesh), (self.count, 1)), lip, smooth(0.008, 0.002, self.lip_distance))[self.mouth]
        rough[self.mouth] = 0.35
        relief[self.mouth] = 0.0
        color[self.nostril] = numpy.array(dark)
        rough[self.nostril] = 0.4
        relief[self.nostril] = 0.0


def deer(c, kind):
    stag = kind == "stag"
    m = palette(c)
    k = m.k
    p = m.p
    n = m.n
    count = m.count
    flow = m.flow()
    fine = c.fur(flow, 0.0034, 0.0013, 12, 1)
    coarse = c.fur(flow, 0.008, 0.0028, 14, 2)
    blend = numpy.where(m.head | m.legs | m.ears, 0.7, 0.45)
    fur = fine * blend + coarse * (1.0 - blend)
    mottle = paint.fbm(p, 0.1, 3, 11)
    patch = paint.fbm(p, 0.03, 3, 12)

    color = numpy.tile(numpy.array([0.5, 0.305, 0.18]), (count, 1))
    color = tint(color, (0.56, 0.36, 0.21), smooth(0.35, 0.7, mottle) * 0.5)
    trunk = (m.body | m.rump | m.tail).astype(numpy.float64)
    up = n[:, 2]
    dorsal = numpy.exp(-(p[:, 0] / 0.045) ** 2) * smooth(0.35, 0.85, up) * trunk
    color = tint(color, (0.29, 0.185, 0.115), dorsal * 0.7)
    color = tint(color, (0.43, 0.26, 0.15), smooth(0.15, 0.85, up) * trunk * 0.3)
    under = smooth(-0.12, -0.85, up + (mottle - 0.5) * 0.35) * numpy.maximum((m.body | m.rump) * smooth(-0.6, -0.48, p[:, 1]), m.legs * smooth(0.58, 0.68, p[:, 2]))
    color = tint(color, (0.7, 0.6, 0.46), under * 0.9)

    head_blend = smooth(0.46, 0.37, m.along) * m.head
    neck_axis = fields.unit(k["neck_top"] - k["neck_base"])
    neck_travel = ((p - k["neck_base"][None, :]) @ neck_axis) / float(numpy.linalg.norm(k["neck_top"] - k["neck_base"]))
    neck = smooth(0.12, 0.4, neck_travel) * smooth(1.02, 0.84, neck_travel) * smooth(-0.34, -0.5, p[:, 1]) * (m.body | m.head)
    throat = smooth(-0.2, 0.5, n @ numpy.cross(fields.lateral, neck_axis))
    if stag:
        color = tint(color, (0.35, 0.255, 0.19), neck * (0.35 + 0.45 * throat))
        shag = neck * (0.4 + 0.6 * throat)
    else:
        color = tint(color, (0.52, 0.36, 0.24), neck * 0.3)
        shag = numpy.zeros(count)

    color = tint(color, (0.7, 0.6, 0.47), m.inner_leg * (0.5 + 0.35 * smooth(0.75, 0.35, p[:, 2])))
    shin = smooth(0.5, 0.18, p[:, 2]) * m.legs * (1.0 - m.inner_leg)
    color = tint(color, (0.4, 0.29, 0.2), shin * 0.5)

    shape = ellipse(p, (0.0, 0.66, 0.985), (0.14, 0.21, 0.195)) + (patch - 0.5) * 0.22
    facing = smooth(0.0, 0.4, n[:, 1])
    rear = (m.body | m.rump | m.hind | m.tail).astype(numpy.float64)
    patch_mask = smooth(1.04, 0.86, shape) * facing * rear
    border = smooth(0.2, 0.02, numpy.abs(shape - 1.02)) * facing * smooth(0.9, 1.06, p[:, 2]) * rear
    color = tint(color, (0.86, 0.77, 0.6), patch_mask)
    color = tint(color, (0.2, 0.13, 0.09), border * 0.75)
    color = tint(color, (0.84, 0.74, 0.56), m.tail.astype(numpy.float64))
    color = tint(color, (0.42, 0.27, 0.16), m.tail * smooth(-0.1, 0.5, n[:, 1]) * smooth(0.024, 0.004, numpy.abs(p[:, 0])) * 0.8)

    face = m.head.astype(numpy.float64)
    crown = smooth(0.25, 0.75, n @ k["head_up"]) * head_blend * smooth(0.14, 0.3, m.along)
    color = tint(color, (0.38, 0.26, 0.17), crown * 0.45)
    muzzle = smooth(0.18, 0.05, m.along) * face
    color = tint(color, (0.45, 0.36, 0.29), muzzle * 0.75)
    jaw = smooth(-0.15, -0.7, n @ k["head_up"]) * head_blend * smooth(0.36, 0.26, m.along)
    color = tint(color, (0.72, 0.64, 0.52), jaw * 0.6)
    chin = numpy.maximum(c.tagged("chin").astype(numpy.float64), face * smooth(-0.014, -0.022, m.height) * smooth(0.075, 0.045, m.along))
    color = tint(color, (0.74, 0.68, 0.57), chin * 0.9)
    spot = smooth(0.02, 0.007, numpy.linalg.norm(m.mirrored - (k["mouth"] - k["head_axis"] * 0.034 - k["head_up"] * 0.007)[None, :], axis=1)) * face
    color = tint(color, (0.1, 0.07, 0.06), spot * 0.8)
    pad = smooth(0.036, 0.026, numpy.linalg.norm(p - (k["nose"] + k["head_up"] * 0.006)[None, :], axis=1)) * numpy.maximum(face, c.tagged("nose")) * smooth(-0.013, -0.006, m.height)
    color = tint(color, (0.05, 0.043, 0.042), pad)
    ring = smooth(0.05, 0.03, m.eye_distance) * face
    color = tint(color, (0.63, 0.49, 0.34), ring * 0.4)
    gland_a = m.eye_center + m.eye_axis * 0.018 - k["head_axis"] * 0.024 - k["head_up"] * 0.006
    gland, travel = segment(m.mirrored, gland_a, gland_a - k["head_axis"] * 0.028 - k["head_up"] * 0.011)
    gland_mask = smooth(0.006, 0.002, gland) * face
    color = tint(color, (0.1, 0.07, 0.06), gland_mask * 0.85)

    color[m.ears] = numpy.array([0.45, 0.33, 0.23])
    color = tint(color, (0.82, 0.75, 0.62), m.ear_inner)
    color = tint(color, (0.5, 0.36, 0.33), smooth(0.4, 0.12, m.ear_along) * smooth(0.5, 1.0, m.ear_inner) * 0.35)
    color = tint(color, (0.22, 0.15, 0.1), smooth(0.72, 0.97, m.ear_along) * m.ears * 0.75)

    grime = smooth(0.55, 0.75, paint.fbm(p, 0.05, 3, 21)) * smooth(0.4, 0.08, p[:, 2]) * m.legs
    color = tint(color, (0.3, 0.24, 0.17), grime * 0.3)
    shade = 0.8 + 0.34 * fur + (mottle - 0.5) * 0.1
    shade = numpy.where(m.lock, shade * (0.78 + 0.4 * c.coord[:, 0]), shade)
    color = numpy.where(m.furry[:, None], color * shade[:, None], color)
    tips = smooth(0.66, 0.92, fine) * m.furry
    color = tint(color, color * 1.12 + 0.015, tips * 0.35)

    rough = numpy.full(count, 0.8)
    rough[m.furry] = 0.74 + 0.16 * (1.0 - fur[m.furry])
    rough = rough + (0.3 - rough) * pad
    relief = numpy.full(count, 0.0015)
    relief[m.head] = 0.0008
    relief[m.legs] = 0.0009
    relief[m.ears] = 0.0005
    relief[m.rump | m.tail] = 0.002
    relief = (relief + shag * 0.0012) * (1.0 - pad) * (1.0 - gland_mask)

    m.cavity(color, rough, relief)
    m.keratin(color, rough, relief)
    antler = c.tagged("antler")
    if antler.any():
        travel = c.coord[:, 0]
        bark = numpy.array([0.33, 0.225, 0.14])[None, :] * (0.55 + 0.8 * coarse)[:, None]
        bark = tint(bark, (0.19, 0.125, 0.08), smooth(0.55, 0.3, fine) * 0.5)
        ivory = smooth(0.5, 0.95, travel) * c.coord[:, 1]
        bark = tint(bark, (0.84, 0.78, 0.64), ivory)
        color[antler] = bark[antler]
        rough[antler] = (0.62 - 0.27 * ivory)[antler]
        relief[antler] = (0.0014 * (1.0 - ivory))[antler]
    m.eyes(color, rough, relief)
    return {"color": numpy.clip(color, 0.0, 1.0), "rough": numpy.clip(rough, 0.04, 1.0), "height": fur, "relief": relief}


def coat(name, c):
    if name == "deer_stag":
        return deer(c, "stag")
    if name == "deer_hind":
        return deer(c, "hind")
    module = importlib.import_module("fauna_hoofed_" + name)
    return module.coat(c, palette(c))
