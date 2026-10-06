import math
import random
from mathutils import Matrix, Vector

import flora_kit as kit
import flora_sprig as sprig
import flora_wood as wood
import flora_shrubs as shrubs

skyward = Vector((0.0, 0.0, 1.0))
green_dark = (0.024, 0.056, 0.017)
green = (0.04, 0.084, 0.025)
green_tip = (0.074, 0.126, 0.04)
dead_dark = (0.06, 0.042, 0.026)
dead = (0.15, 0.105, 0.052)
stem_color = (0.075, 0.07, 0.035)
yellow = (0.78, 0.56, 0.03)
yellow_deep = (0.72, 0.4, 0.02)


def round_outline(t, side):
    return math.sin(math.pi * min(t * 1.05, 1.0) ** 0.75) ** 0.5


def narrow_outline(t, side):
    return math.sin(math.pi * t ** 0.8) ** 0.7


standard = sprig.leaf_style(outline=round_outline, rows=8, columns=(-1.0, -0.5, 0.0, 0.5, 1.0), petiole=0.0, fold=0.35, curl=-0.5, veins=1.0, vein_strength=0.0, quilt=0.0, front=(yellow_deep, yellow), back=(yellow_deep, yellow), vein=yellow, rough=0.5, back_rough=0.5)
wing = sprig.leaf_style(outline=narrow_outline, rows=6, columns=(-1.0, 0.0, 1.0), petiole=0.0, fold=0.4, curl=0.2, veins=1.0, vein_strength=0.0, quilt=0.0, front=(yellow_deep, yellow), back=(yellow_deep, yellow), vein=yellow, rough=0.5, back_rough=0.5)


def flower(target, rng, base, direction):
    tone = (rng.uniform(0.9, 1.08),) * 3
    with target.place(sprig.basis(base, direction, Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 1.0))) @ Matrix.Scale(1.25, 4)):
        target.blob(Vector((0.0, 0.003, 0.0)), (0.0026, 0.0026, 0.004), (0.3, 0.3, 0.07), (0.2, 0.22, 0.05), 0.7, 5, 3, Vector((0.0, 1.0, 0.0)))
        with target.place(sprig.basis(Vector((0.0, 0.004, 0.001)), Vector((0.0, 0.45, 0.9)), Vector((0.0, 1.0, 0.0)))):
            target.leaf(standard, 0.014, 0.0135, tone)
        for side in (-1.0, 1.0):
            with target.place(sprig.basis(Vector((side * 0.0012, 0.004, 0.0)), Vector((side * 0.22, 1.0, 0.1)), Vector((side * 0.6, 0.0, 1.0)))):
                target.leaf(wing, 0.0115, 0.0052, tone)
        with target.place(sprig.basis(Vector((0.0, 0.004, -0.0008)), Vector((0.0, 1.0, -0.08)), Vector((0.0, 0.0, 1.0)))):
            target.leaf(wing, 0.0105, 0.0048, (tone[0] * 0.92, tone[1] * 0.85, tone[2]))


def shoot(target, rng, start, direction, length, bloom, withered):
    steps = max(3, int(length / 0.03))
    heading = direction.normalized()
    points = [start.copy()]
    for index in range(steps):
        heading = (heading + Vector((rng.uniform(-0.08, 0.08), rng.uniform(-0.04, 0.08), rng.uniform(-0.06, 0.06)))).normalized()
        points.append(points[-1] + heading * length / steps)
    low = dead_dark if withered else green_dark
    mid = dead if withered else green
    high = dead if withered else green_tip
    target.tube(points, 0.0028, 0.0013, kit.mix(low, mid, 0.5), mid, 0.7, 5)
    spacing = 0.011 if target.lite else 0.0065
    walked = 0.006
    angle = rng.uniform(0.0, math.tau)
    while walked < length:
        base, along = kit.point_on(points, walked / length)
        angle += 2.399963
        radial = Matrix.Rotation(angle, 3, along) @ kit.any_perpendicular(along)
        tilt = math.radians(rng.uniform(46.0, 76.0))
        aim = (along * math.cos(tilt) + radial * math.sin(tilt)).normalized()
        reach = rng.uniform(0.026, 0.046) * (1.0 - 0.35 * walked / length)
        shade = rng.uniform(0.8, 1.2)
        first = tuple(value * shade for value in kit.mix(low, mid, rng.uniform(0.2, 0.8)))
        second = tuple(value * shade for value in kit.mix(mid, high, rng.uniform(0.3, 1.0)))
        target.needle(base, aim, Vector((0.0, 0.0, 1.0)), reach, 0.0042 if target.lite else 0.0034, first, second, 0.5)
        side = aim.cross(along)
        if side.length > 1e-4:
            side.normalize()
            for step in range(2 if target.lite else 4):
                along_spine = base + aim * reach * (0.18 + 0.2 * step)
                turn = 1.0 if step % 2 else -1.0
                thorn = (aim * 0.55 + side * turn * 0.75 + along * rng.uniform(-0.25, 0.35)).normalized()
                target.needle(along_spine, thorn, Vector((0.0, 0.0, 1.0)), reach * rng.uniform(0.32, 0.5), 0.0026 if target.lite else 0.002, first, second, 0.5)
        if bloom and walked / length > 0.15 and rng.random() < bloom * spacing / 0.0065 * 0.42:
            flower(target, rng, base + aim * reach * 0.35, (aim + along * 0.3 + Vector((0.0, 0.0, 0.45))).normalized())
        walked += spacing


def spray(target, rng, length, nodes, reach, bloom, withered):
    heading = Vector((0.0, 1.0, 0.0))
    points = [Vector((0.0, 0.0, 0.0))]
    joints = []
    for index in range(nodes):
        heading = (Matrix.Rotation(rng.uniform(0.1, 0.3) * (1.0 if index % 2 else -1.0), 3, 'Z') @ heading).normalized()
        heading = (heading + Vector((-heading.x * 0.3, 0.0, rng.uniform(-0.06, 0.06)))).normalized()
        points.append(points[-1] + heading * length / nodes)
        joints.append((points[-1].copy(), heading.copy(), index))
    target.tube(points, 0.0042, 0.002, stem_color, kit.mix(stem_color, green, 0.6), 0.85, 5)
    for point, along, index in joints:
        t = (index + 1) / nodes
        for side in (1.0, -1.0, rng.choice((1.0, -1.0))):
            direction = (Matrix.Rotation(side * rng.uniform(0.4, 1.0), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.45, 0.45)))).normalized()
            span = reach * (1.0 - 0.4 * t) * rng.uniform(0.7, 1.15)
            shoot(target, rng, point, direction, span, bloom, withered)
    shoot(target, rng, points[-1], heading, reach * 0.9, bloom, withered)


def cell(length, nodes, reach, bloom, withered):
    def builder(target, rng):
        spray(target, rng, length, nodes, reach, bloom, withered)
    return builder


builders = {"a": cell(0.26, 8, 0.13, 0.95, False), "b": cell(0.24, 8, 0.14, 0.5, False), "c": cell(0.25, 8, 0.13, 0.1, False), "d": cell(0.24, 7, 0.13, 0.0, True)}


def patch(bloom, seed):
    def builder(target, rng):
        target.lite = True
        target.front = True
        for index in range(16):
            angle = rng.uniform(0.0, math.tau)
            radius = 0.3 * math.sqrt(rng.random())
            origin = Vector((math.cos(angle) * radius, math.sin(angle) * radius, -0.12))
            heading = rng.uniform(0.0, math.tau)
            tilt = rng.uniform(0.85, 1.3)
            direction = Vector((math.cos(heading) * math.sin(tilt), math.sin(heading) * math.sin(tilt), math.cos(tilt)))
            matrix = sprig.basis(origin, direction, Vector((0.0, 0.0, 1.0)), rng.uniform(-0.5, 0.5))
            with target.place(matrix):
                builders[rng.choice(("a", "b", "c") if bloom else ("c", "c", "b"))](target, random.Random(rng.randint(0, 1 << 30)))
    return builder


def atlas():
    sheet = sprig.atlas_c("gorse")
    sheet.cell("a", (0.0, 0.66, 0.34, 1.0), builders["a"], 1011)
    sheet.cell("b", (0.34, 0.66, 0.68, 1.0), builders["b"], 1023)
    sheet.cell("c", (0.0, 0.32, 0.34, 0.66), builders["c"], 1037)
    sheet.cell("d", (0.34, 0.32, 0.68, 0.66), builders["d"], 1049)
    sheet.cell("p0", (0.0, 0.0, 0.32, 0.32), patch(True, 1), 1061, 0.02, 1.2)
    sheet.cell("p1", (0.32, 0.0, 0.64, 0.32), patch(True, 2), 1063, 0.02, 1.2)
    sheet.cell("p2", (0.64, 0.0, 0.96, 0.32), patch(False, 3), 1069, 0.02, 1.2)
    sheet.cell("fill", (0.68, 0.66, 1.0, 1.0), shrubs.foliage_slab(0.32, 0.34, ((0.012, 0.022, 0.008), (0.022, 0.042, 0.014), (0.04, 0.03, 0.016), (0.03, 0.06, 0.02), (0.05, 0.085, 0.026)), 0.012, 0.7, 31), 1, 0.0, 1.0, 0.035, (-0.16, 0.0, 0.16, 0.34))
    sheet.cell("stem", (0.68, 0.32, 0.84, 0.66), shrubs.bark_slab(0.16, 0.34, (0.045, 0.034, 0.024), (0.15, 0.125, 0.09), 5, 0.004, 0.88, 33), 1, 0.0, 1.0, 0.035, (-0.08, 0.0, 0.08, 0.34))
    return sheet.render()


profiles = (
    {"lobes": (((0.0, 0.0, 0.5), (1.2, 1.1, 1.22)), ((0.95, 0.35, 0.36), (0.7, 0.72, 0.84))), "sprays": 300, "patches": 70, "far_sprays": 120, "far_patches": 80, "stems": 0, "bloom": ("a", "a", "b", "c")},
    {"lobes": (((-0.7, 0.0, 0.24), (0.88, 0.8, 0.86)), ((0.62, 0.22, 0.28), (0.98, 0.84, 0.9)), ((0.1, -0.85, 0.18), (0.68, 0.58, 0.66))), "sprays": 310, "patches": 80, "far_sprays": 120, "far_patches": 90, "stems": 0, "bloom": ("a", "b", "b", "c")},
    {"lobes": (((0.0, 0.0, 0.78), (0.55, 0.52, 0.58)), ((0.42, 0.2, 0.5), (0.4, 0.4, 0.46)), ((-0.3, -0.25, 0.42), (0.36, 0.34, 0.4))), "sprays": 230, "patches": 50, "far_sprays": 110, "far_patches": 60, "stems": 5, "bloom": ("a", "b", "c", "c")},
)


def build(variant, lod):
    profile = profiles[variant]
    rng = random.Random(9511 + variant * 41 + lod)
    cells = sprig.load_cells("gorse")
    lobes = [(Vector(center), radii) for center, radii in profile["lobes"]]
    shade = shrubs.lobe_shade(lobes)
    model = wood.model_c()
    for center, radii in lobes:
        model.hull(cells["fill"], center, (radii[0] * 0.64, radii[1] * 0.64, radii[2] * 0.7), 8 if lod == 0 else 6, 4 if lod == 0 else 3, 0.0, shade)
    for index in range(profile["stems"]):
        center, radii = lobes[index % len(lobes)]
        angle = rng.uniform(0.0, math.tau)
        foot = Vector((math.cos(angle) * 0.12, math.sin(angle) * 0.12, -0.08))
        tip = center + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), -radii[2] * 0.2))
        middle = foot.lerp(tip, 0.5) + Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0.05))
        model.stem(cells["stem"], [foot, foot.lerp(middle, 0.5) + Vector((0.0, 0.0, 0.02)), middle, middle.lerp(tip, 0.5), tip], [0.03, 0.026, 0.022, 0.018, 0.012], 5 if lod == 0 else 3)
    for point, outward in shrubs.shell(rng, lobes, profile["patches"] if lod == 0 else profile["far_patches"], 0.86, 0.3):
        forward, right, up = shrubs.patch_frame(point, outward, rng)
        model.card(cells[rng.choice(("p0", "p1", "p2"))], point, forward, right, up, rng.uniform(0.9, 1.2), 0.0, 0.0, 1, 1, rng.random() < 0.5, shade)
    for point, outward in shrubs.shell(rng, lobes, profile["sprays"] if lod == 0 else profile["far_sprays"], 0.8, 0.02):
        forward, right, up = shrubs.card_frame(point, outward, rng, rng.uniform(0.45, 0.8), rng.uniform(-0.5, 0.5) if point.z < 0.45 else None)
        name = rng.choice(profile["bloom"])
        if lod == 0:
            model.card(cells[name], point, forward, right, up, rng.uniform(1.0, 1.35), rng.uniform(0.0, 0.2), 0.35 * rng.uniform(0.7, 1.3), 2, 2, rng.random() < 0.5, shade)
        else:
            model.card(cells[name], point, forward, right, up, rng.uniform(1.3, 1.7), 0.0, 0.0, 1, 1, rng.random() < 0.5, shade)
    model.ground(-0.1)
    return model


species = {"gorse": {"kind": "shrub", "variants": 3, "atlas": atlas, "build": build, "bark": False}}
