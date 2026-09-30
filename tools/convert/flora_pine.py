import math
import random
from mathutils import Matrix, Vector

import flora_kit as kit
import flora_bark as bark
import flora_sprig as sprig
import flora_wood as wood
import flora_trees as trees

skyward = Vector((0.0, 0.0, 1.0))
needle_dark = (0.024, 0.064, 0.05)
needle_mid = (0.04, 0.096, 0.07)
needle_tip = (0.07, 0.132, 0.084)
twig_young = (0.13, 0.085, 0.05)
twig_old = (0.075, 0.056, 0.046)
cone_color = (0.15, 0.1, 0.06)


def shoot(target, rng, start, direction, length, tone, bare=0.12):
    steps = 8
    heading = direction.normalized()
    points = [start.copy()]
    for index in range(steps):
        heading = (heading + Vector((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 0.05))).normalized()
        points.append(points[-1] + heading * length / steps)
    target.tube(points, 0.0048, 0.003, twig_old, twig_young, 0.8, 5)
    spacing = 0.0042 if target.lite else 0.0017
    walked = length * bare
    angle = rng.uniform(0.0, math.tau)
    while walked < length:
        base, along = kit.point_on(points, walked / length)
        perp = kit.any_perpendicular(along)
        for pair in range(2):
            angle += 2.399963
            radial = Matrix.Rotation(angle, 3, along) @ perp
            tilt = math.radians(rng.uniform(36.0, 62.0))
            aim = (along * math.cos(tilt) + radial * math.sin(tilt)).normalized()
            reach = rng.uniform(0.055, 0.082) * (0.72 + 0.28 * math.sin(math.pi * min(1.0, walked / length * 1.15)))
            shade = rng.uniform(0.82, 1.18)
            low = tuple(kit.mix(needle_dark, needle_mid, rng.uniform(0.0, 0.7))[channel] * tone[channel] * shade for channel in range(3))
            high = tuple(kit.mix(needle_mid, needle_tip, rng.uniform(0.2, 1.0))[channel] * tone[channel] * shade for channel in range(3))
            target.needle(base, aim, Vector((0.0, 0.0, 1.0)), reach, 0.0034 if target.lite else 0.0028, low, high, 0.42)
        walked += spacing
    target.blob(points[-1] + heading * 0.006, (0.0045, 0.0045, 0.009), (0.2, 0.13, 0.07), (0.12, 0.08, 0.05), 0.7, 6, 4, heading)
    return points


def cone(target, rng, base, direction):
    target.blob(base + direction * 0.022, (0.013, 0.013, 0.024), cone_color, (0.1, 0.07, 0.045), 0.85, 8, 6, direction)


def whorl(target, rng, origin, axis, count, reach, tone, cones):
    shoot(target, rng, origin, axis, reach * rng.uniform(0.9, 1.15), tone, 0.05)
    for index in range(count):
        side = (index + 0.5) / count * 2.0 - 1.0
        direction = (Matrix.Rotation(side * rng.uniform(0.9, 1.25) + rng.uniform(-0.12, 0.12), 3, 'Z') @ axis + Vector((0.0, 0.0, rng.uniform(-0.55, 0.85)))).normalized()
        shoot(target, rng, origin, direction, reach * rng.uniform(0.65, 1.0), tone, 0.1)
        if cones and rng.random() < 0.4:
            cone(target, rng, origin + direction * 0.015, (direction + Vector((0.0, 0.0, -0.4))).normalized())


def tuft(target, rng, stem, reach, count, tone, cones):
    heading = Vector((rng.uniform(-0.08, 0.08), 1.0, 0.0)).normalized()
    points = [Vector((0.0, 0.0, 0.0)), heading * stem * 0.5 + Vector((rng.uniform(-0.01, 0.01), 0.0, 0.0)), heading * stem]
    target.tube(points, 0.007, 0.0052, twig_old, twig_old, 0.85, 6)
    whorl(target, rng, points[-1], heading, count, reach, tone, cones)


def branchlet(target, rng, tone):
    heading = Vector((0.0, 1.0, 0.0))
    points = [Vector((0.0, 0.0, 0.0))]
    for index in range(6):
        heading = (Matrix.Rotation(rng.uniform(-0.12, 0.12), 3, 'Z') @ heading).normalized()
        points.append(points[-1] + heading * 0.055)
    target.tube(points, 0.0085, 0.006, twig_old, twig_old, 0.85, 6)
    for index, side in ((2, 1.0), (3, -1.0), (4, 1.0)):
        direction = (Matrix.Rotation(side * rng.uniform(0.7, 1.0), 3, 'Z') @ heading + Vector((0.0, 0.0, rng.uniform(-0.2, 0.3)))).normalized()
        base = points[index]
        arm = [base, base + direction * 0.07, base + direction * 0.14]
        target.tube(arm, 0.0062, 0.005, twig_old, twig_old, 0.85, 5)
        whorl(target, rng, arm[-1], direction, 5, rng.uniform(0.15, 0.2), tone, False)
    whorl(target, rng, points[-1], heading, 7, rng.uniform(0.18, 0.23), tone, False)


def cell_a(target, rng):
    tuft(target, rng, 0.06, 0.2, 8, (1.0, 1.0, 1.0), False)


def cell_b(target, rng):
    branchlet(target, rng, (0.95, 0.98, 1.0))


def cell_c(target, rng):
    tuft(target, rng, 0.05, 0.18, 9, (1.05, 1.03, 0.96), True)


builders = {"a": cell_a, "b": cell_b, "c": cell_c}
lengths = {"f0": 0.7, "f1": 0.78, "f2": 0.86, "f3": 0.92}


def frames(rng, points, lod, aim=None):
    result = []
    length = kit.path_length(points)
    walked = 0.15
    while walked < 0.9:
        base, along = kit.point_on(points, walked)
        direction = wood.deflect(rng, along, math.radians(rng.uniform(30.0, 62.0)), skyward, 0.55)
        forward, right, up = wood.frame_of(direction, rng.uniform(-0.6, 0.6), skyward)
        result.append((base, forward, right, up, rng.choice(("a", "a", "c", "b")), rng.uniform(1.15, 1.5), rng.uniform(0.0, 0.12), rng.random() < 0.5))
        walked += rng.uniform(0.075, 0.105) / max(length, 0.4)
    base, along = kit.point_on(points, 0.9)
    for roll in (rng.uniform(-0.4, 0.4), rng.uniform(0.9, 1.4), rng.uniform(-1.4, -0.9)):
        forward, right, up = wood.frame_of((along + skyward * 0.35).normalized(), roll, skyward)
        result.append((base, forward, right, up, rng.choice(("b", "a", "c")), rng.uniform(1.2, 1.5), rng.uniform(0.0, 0.1), rng.random() < 0.5))
    return result


def far(name):
    def builder(target, rng):
        trees.bough(target, rng, frames, builders, lengths[name], 0.016, twig_old)
    return builder


def atlas():
    sheet = sprig.atlas_c("pine")
    sheet.cell("a", (0.0, 0.5, 0.5, 1.0), cell_a, 411, 0.02, 1.25)
    sheet.cell("b", (0.5, 0.5, 1.0, 1.0), cell_b, 423, 0.02, 1.25)
    sheet.cell("c", (0.0, 0.0, 0.5, 0.5), cell_c, 437, 0.02, 1.25)
    for index, name in enumerate(sorted(lengths)):
        sheet.cell(name, (0.5 + 0.25 * (index % 2), 0.25 * (index // 2), 0.75 + 0.25 * (index % 2), 0.25 + 0.25 * (index // 2)), far(name), 501 + index * 17, 0.02, 1.35)
    return sheet.render()


profiles = (
    {"height": 16.6, "radius": 0.28, "center": 13.6, "up": 2.0, "down": 2.9, "spread": 4.9, "offset": (0.0, 0.0), "lean": 0.015, "bow": 0.0, "boughs": 6, "stubs": 5, "targets": 1500, "influence": 1.9, "kill": 0.45, "clumps": 9, "size": 1.9, "split": 9.0, "plan": {"shadow_thin": 1}},
    {"height": 13.8, "radius": 0.24, "center": 11.0, "up": 2.0, "down": 2.6, "spread": 4.2, "offset": (1.3, 0.4), "lean": 0.06, "bow": 0.25, "boughs": 5, "stubs": 4, "targets": 1400, "influence": 1.9, "kill": 0.45, "clumps": 7, "size": 1.8, "split": 10.4, "plan": {"shadow_thin": 1}},
    {"height": 12.2, "radius": 0.27, "center": 8.9, "up": 2.6, "down": 3.6, "spread": 5.2, "offset": (-0.5, 0.6), "lean": 0.03, "bow": 0.1, "boughs": 7, "stubs": 3, "targets": 1500, "influence": 1.9, "kill": 0.45, "clumps": 11, "size": 1.8, "split": 7.0, "plan": {"shadow_thin": 1}},
)
table = ((0.2, (14, 8, 5), (0.012, 0.06, 0.25)), (0.1, (10, 6, 4), (0.02, 0.1, 0.3)), (0.05, (7, 5, 3), (0.03, 0.15, 0.4)), (0.025, (5, 3, 3), (0.04, 0.25, 0.6)), (0.012, (4, 0, 0), (0.05, 0.3, 0.6)), (0.0, (3, 0, 0), (0.05, 0.3, 0.6)))


def skeleton(variant):
    profile = profiles[variant]
    rng = random.Random(7607 + variant * 811)
    height = profile["height"]
    spread = profile["spread"]
    lean_angle = rng.uniform(0.0, math.tau)
    lean_axis = Vector((math.cos(lean_angle), math.sin(lean_angle), 0.0))
    phase = rng.uniform(0.0, 10.0)
    heading = (skyward + lean_axis * profile["lean"]).normalized()
    low = [Vector((lean_axis.x * profile["lean"] * level, lean_axis.y * profile["lean"] * level, level)) for level in (-0.5, -0.25, 0.0, 0.12, 0.28, 0.5, 0.8, 1.2)]
    points = [low[-1].copy()]
    steps = int((height * 0.94 - 1.2) / 0.45)
    for index in range(1, steps + 1):
        t = index / steps
        drift = heading + lean_axis * profile["bow"] * (0.5 - t) * 0.5 + Vector((math.sin(t * 6.0 + phase), math.cos(t * 4.7 + phase), 0.0)) * 0.03
        points.append(points[-1] + drift.normalized() * (height * 0.94 - 1.2) / steps)
    root = wood.limb_c(low + points[1:], 0)
    root.shape = trees.flare_shape(phase, 0.55, 1.0, 5.0, 0.025)
    root.zone = 0
    root.switch = height * rng.uniform(0.42, 0.52)
    marks = root.marks()
    top = root.points[-1]
    center = Vector((top.x * 0.7 + profile["offset"][0], top.y * 0.7 + profile["offset"][1], profile["center"]))
    floor = center.z - profile["down"]
    base_angle = rng.uniform(0.0, math.tau)
    for index in range(profile["boughs"]):
        level = floor + (height * 0.9 - floor) * (index + rng.uniform(0.1, 0.9)) / profile["boughs"]
        node = min(range(len(root.points)), key=lambda entry: abs(root.points[entry].z - level))
        azimuth = base_angle + index * 2.4 + rng.uniform(-0.3, 0.3)
        elevation = math.radians(rng.uniform(-4.0, 22.0) + 28.0 * (index / profile["boughs"]) ** 2)
        direction = Vector((math.cos(azimuth) * math.cos(elevation), math.sin(azimuth) * math.cos(elevation), math.sin(elevation)))
        reach = spread * rng.uniform(0.5, 0.78) * (1.0 - 0.35 * index / profile["boughs"])
        path = wood.grow(rng, root.points[node], direction, reach, 0.34, 0.05, lambda point, t: (skyward, -0.05 + 0.5 * t * t), 0.36, (0.8, 1.3))
        limb = wood.limb_c(path, 1, root, marks[node])
        limb.zone = 1
    stubs = []
    for index in range(profile["stubs"]):
        level = rng.uniform(2.2, max(2.6, floor - 0.6))
        node = min(range(len(root.points)), key=lambda entry: abs(root.points[entry].z - level))
        azimuth = rng.uniform(0.0, math.tau)
        direction = Vector((math.cos(azimuth), math.sin(azimuth), rng.uniform(-0.25, 0.2))).normalized()
        path = wood.grow(rng, root.points[node], direction, rng.uniform(0.35, 1.1), 0.22, 0.12, lambda point, t: (skyward, -0.25), 0.3, (0.3, 0.5))
        stub = wood.limb_c(path, 1, root, marks[node])
        stub.zone = 0 if level < root.switch else 1
        stub.broken = True
        stub.own = rng.uniform(0.6, 2.0)
        stubs.append(stub)
    targets = wood.clump_points(rng, profile["targets"], center, (spread, spread), profile["up"], profile["down"], profile["clumps"], profile["size"], (0.45, 0.9))
    created = wood.colonize(rng, root, targets, 0.36, profile["influence"], profile["kill"], 0.4, 0.22, 90, 3, floor - 0.5, 0.14, stubs, 1)
    leafy = trees.leafy_tips(created, 0.8, 0.6)
    root.leafy = True
    root.bare = max(0.0, 1.0 - 0.9 / root.length())
    leafy.append(root)
    wood.assign_radii(root, profile["radius"], 0.006, 2.0, 0.5, 0.08)
    trees.census("pine", variant, root, leafy)
    profile["aim"] = None
    return root, leafy, wood.crown_shade(center, spread, profile["up"] + 0.8, profile["down"], (0.5, 0.2, 0.42)), profile


def build(variant, lod):
    return trees.assemble("pine", variant, lod, skeleton, frames, lengths, bark.pine_zones, 2.4, 1.4, table, 9203)


species = {"pine": {"kind": "tree", "variants": 3, "atlas": atlas, "build": build, "solid": (0.14, 0.62)}}
