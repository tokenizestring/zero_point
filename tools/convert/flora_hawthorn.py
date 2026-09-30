import math
import random
from mathutils import Matrix, Vector

import flora_kit as kit
import flora_bark as bark
import flora_sprig as sprig
import flora_wood as wood
import flora_trees as trees

skyward = Vector((0.0, 0.0, 1.0))
downwind = Vector((1.0, 0.0, 0.0))


def outline(t, side):
    envelope = (t ** 0.9) * ((1.0 - t) ** 0.4) / 0.448
    first = 0.43 if side < 0.0 else 0.4
    second = 0.69 if side < 0.0 else 0.66
    cut = 1.0 - 0.62 * math.exp(-((t - first) / 0.045) ** 2) - 0.5 * math.exp(-((t - second) / 0.04) ** 2)
    teeth = 1.0 + 0.07 * ((t * 9.0) % 1.0 - 0.5) * (1.0 if t > 0.45 else 0.0)
    return envelope * cut * teeth


def round_petal(t, side):
    return math.sin(math.pi * min(t * 1.08, 1.0) ** 0.8) ** 0.45


leaf = sprig.leaf_style(outline=outline, rows=40, petiole=0.22, stalk=0.03, fold=0.1, curl=0.2, sweep=0.38, veins=4.0, slant=1.2, vein_width=0.14, vein_strength=0.25, front=((0.032, 0.08, 0.02), (0.046, 0.102, 0.026)), back=((0.068, 0.115, 0.046), (0.078, 0.126, 0.05)), vein=(0.09, 0.14, 0.045), stem=(0.1, 0.1, 0.04), rough=0.4)
petal = sprig.leaf_style(outline=round_petal, rows=8, columns=(-1.0, -0.5, 0.0, 0.5, 1.0), petiole=0.0, fold=-0.18, curl=-0.35, veins=1.0, vein_strength=0.0, quilt=0.0, front=((0.72, 0.7, 0.62), (0.86, 0.86, 0.82)), back=((0.7, 0.68, 0.62), (0.8, 0.8, 0.76)), vein=(0.8, 0.8, 0.75), rough=0.55, back_rough=0.6)
twig_color = (0.075, 0.058, 0.045)
shoot_color = (0.11, 0.065, 0.04)
stalk_color = (0.1, 0.14, 0.05)


def blade(target, rng, origin, direction, tone):
    shade = trees.shift(rng, 0.8, 1.2, 0.07)
    shade = tuple(shade[channel] * tone[channel] for channel in range(3))
    hint = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), -1.0 if rng.random() < 0.06 else 1.0))
    length = rng.uniform(0.03, 0.046)
    with target.place(sprig.basis(origin, direction, hint, rng.uniform(-0.35, 0.35))):
        target.leaf(leaf, length * 1.2, length * rng.uniform(0.78, 0.92), shade, None, rng.uniform(0.0, 0.4), rng.uniform(0.02, 0.22))


def flower(target, rng, center, facing):
    size = rng.uniform(0.0062, 0.0078)
    frame = sprig.basis(center, facing, Vector((rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), 0.2)))
    with target.place(frame):
        turn = rng.uniform(0.0, math.tau)
        for index in range(5):
            angle = turn + math.tau * index / 5.0
            direction = Vector((math.cos(angle), 0.18, math.sin(angle))).normalized()
            with target.place(sprig.basis(Vector((0.0, 0.0006, 0.0)), direction, Vector((0.0, 1.0, 0.0)))):
                target.leaf(petal, size, size * 0.95, (rng.uniform(0.93, 1.05),) * 3)
        target.blob(Vector((0.0, 0.0012, 0.0)), (0.0016, 0.0016, 0.001), (0.5, 0.52, 0.2), (0.35, 0.42, 0.14), 0.6, 6, 3, Vector((0.0, 1.0, 0.0)))
        for index in range(7):
            angle = turn + math.tau * (index + 0.5) / 7.0
            target.blob(Vector((math.cos(angle) * 0.003, 0.0026, math.sin(angle) * 0.003)), (0.00055, 0.00055, 0.00055), (0.5, 0.16, 0.2), (0.4, 0.12, 0.16), 0.6, 4, 2)


def corymb(target, rng, origin, axis, count):
    target.front = True
    for index in range(count):
        angle = index * 2.399963 + rng.uniform(-0.3, 0.3)
        spread = 0.012 + 0.024 * math.sqrt((index + 0.5) / count)
        offset = Vector((math.cos(angle) * spread, math.sin(angle) * spread * 0.9, rng.uniform(0.012, 0.022)))
        tip = origin + axis * rng.uniform(0.012, 0.03) + offset
        target.tube([origin, origin.lerp(tip, 0.55) + Vector((0.0, 0.0, 0.003)), tip], 0.0006, 0.0005, stalk_color, stalk_color, 0.7, 3)
        flower(target, rng, tip, (Vector((offset.x * 8.0, offset.y * 8.0, 1.0))).normalized())
    target.front = False


def shoot(target, rng, start, direction, length, tone, bloom):
    nodes = max(2, int(length / 0.018))
    points = [start.copy()]
    heading = direction.normalized()
    for index in range(nodes):
        heading = (Matrix.Rotation(rng.uniform(0.1, 0.3) * (1.0 if index % 2 else -1.0), 3, 'Z') @ heading + Vector((0.0, 0.0, rng.uniform(-0.1, 0.1)))).normalized()
        points.append(points[-1] + heading * length / nodes)
    target.tube(points, 0.0017, 0.0008, shoot_color, shoot_color, 0.8, 4)
    for index in range(1, nodes + 1):
        side = 1.0 if index % 2 else -1.0
        for count in range(rng.randint(1, 3)):
            blade(target, rng, points[index], (Matrix.Rotation(side * rng.uniform(0.4, 1.3), 3, 'Z') @ heading + Vector((0.0, 0.0, rng.uniform(-0.35, 0.35)))).normalized(), tone)
            side = -side
    if rng.random() < bloom:
        corymb(target, rng, points[-1] + Vector((0.0, 0.0, 0.006)), heading, rng.randint(11, 17))
    return points


def spray(target, rng, length, nodes, reach, tone, bloom):
    heading = Vector((0.0, 1.0, 0.0))
    points = [Vector((0.0, 0.0, 0.0))]
    joints = []
    for index in range(nodes):
        heading = (Matrix.Rotation(rng.uniform(0.18, 0.42) * (1.0 if index % 2 else -1.0), 3, 'Z') @ heading).normalized()
        heading = (heading + Vector((-heading.x * 0.3, 0.0, rng.uniform(-0.08, 0.08)))).normalized()
        points.append(points[-1] + heading * length / nodes)
        joints.append((points[-1].copy(), heading.copy(), index))
    target.tube(points, 0.0045, 0.0018, twig_color, twig_color, 0.88, 5)
    for point, along, index in joints:
        t = (index + 1) / nodes
        side = 1.0 if index % 2 else -1.0
        if rng.random() < 0.4:
            spine = (Matrix.Rotation(-side * rng.uniform(0.9, 1.4), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.3, 0.3)))).normalized()
            target.tube([point, point + spine * 0.007, point + spine * 0.014], 0.0011, 0.0002, twig_color, (0.12, 0.08, 0.05), 0.7, 3)
        for branch in ((side,), (side, -side))[1 if rng.random() < 0.4 else 0]:
            direction = (Matrix.Rotation(branch * rng.uniform(0.7, 1.15), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.3, 0.3)))).normalized()
            span = reach * (1.0 - 0.5 * t) * rng.uniform(0.75, 1.15)
            stem = shoot(target, rng, point, direction, span, tone, bloom)
            if span > reach * 0.55 and rng.random() < 0.7:
                shoot(target, rng, stem[len(stem) // 2], (Matrix.Rotation(-branch * rng.uniform(0.6, 1.0), 3, 'Z') @ direction).normalized(), span * 0.55, tone, bloom)
    shoot(target, rng, points[-1], heading, reach * 0.5, tone, bloom)


def cell(length, nodes, reach, tone, bloom):
    def builder(target, rng):
        spray(target, rng, length, nodes, reach, tone, bloom)
    return builder


builders = {"a": cell(0.34, 9, 0.13, (1.0, 1.0, 1.0), 0.0), "b": cell(0.28, 8, 0.16, (0.93, 0.97, 0.95), 0.0), "c": cell(0.3, 8, 0.12, (1.1, 1.06, 0.92), 0.0), "d": cell(0.34, 9, 0.13, (1.0, 1.0, 1.0), 0.95), "e": cell(0.28, 8, 0.16, (0.95, 0.98, 0.95), 1.0), "g": cell(0.3, 8, 0.12, (1.05, 1.04, 0.95), 0.9)}
lengths = {"f0": 0.4, "f1": 0.46}
bloom_lengths = {"f2": 0.4, "f3": 0.46}


def make_frames(names):
    def frames(rng, points, lod, aim=None):
        result = []
        length = kit.path_length(points)
        walked = 0.12
        while walked < 0.9:
            base, along = kit.point_on(points, walked)
            direction = wood.deflect(rng, along, math.radians(rng.uniform(35.0, 70.0)))
            direction = (direction + downwind * 0.45 + skyward * 0.1).normalized()
            forward, right, up = wood.frame_of(direction, rng.uniform(-0.6, 0.6), skyward)
            result.append((base, forward, right, up, rng.choice(names), rng.uniform(0.85, 1.15), rng.uniform(0.03, 0.2), rng.random() < 0.5))
            walked += rng.uniform(0.11, 0.16) / max(length, 0.25)
        base, along = kit.point_on(points, 0.88)
        for roll in (rng.uniform(-0.4, 0.4), rng.uniform(0.6, 1.2), rng.uniform(-1.2, -0.6)):
            forward, right, up = wood.frame_of((along + downwind * 0.3 + skyward * 0.15).normalized(), roll, skyward)
            result.append((base, forward, right, up, rng.choice(names), rng.uniform(0.9, 1.15), rng.uniform(0.03, 0.18), rng.random() < 0.5))
        return result
    return frames


leaf_frames = make_frames(("a", "b", "c"))
bloom_frames = make_frames(("d", "e", "g"))


def far(name, frames):
    def builder(target, rng):
        trees.bough(target, rng, frames, builders, {**lengths, **bloom_lengths}[name], 0.006, twig_color)
    return builder


def atlas():
    sheet = sprig.atlas_c("hawthorn")
    for index, name in enumerate(("a", "b", "c")):
        sheet.cell(name, (index / 3.0, 0.62, (index + 1) / 3.0, 1.0), builders[name], 611 + index * 13)
    for index, name in enumerate(("d", "e", "g")):
        sheet.cell(name, (index / 3.0, 0.24, (index + 1) / 3.0, 0.62), builders[name], 653 + index * 13)
    for index, name in enumerate(("f0", "f1")):
        sheet.cell(name, (0.25 * index, 0.0, 0.25 * index + 0.25, 0.24), far(name, leaf_frames), 701 + index * 17, 0.02, 1.2)
    for index, name in enumerate(("f2", "f3")):
        sheet.cell(name, (0.5 + 0.25 * index, 0.0, 0.75 + 0.25 * index, 0.24), far(name, bloom_frames), 751 + index * 17, 0.02, 1.2)
    return sheet.render()


profiles = (
    {"height": 4.3, "trunk": 2.5, "radius": 0.16, "sweep": 0.8, "center": (1.9, 0.0, 2.75), "rx": 2.5, "ry": 1.8, "up": 1.6, "down": 1.4, "top": 2.45, "slope": 0.5, "targets": 2200, "clumps": 26, "size": 0.8, "bloom": False, "twin": False, "plan": {"far_cards": 2, "far_rows": 1, "shadow_thin": 1, "shadow_cards": 1, "shadow_scale": 1.25}},
    {"height": 3.5, "trunk": 1.8, "radius": 0.13, "sweep": 0.55, "center": (1.3, 0.0, 2.25), "rx": 2.0, "ry": 1.7, "up": 1.3, "down": 1.2, "top": 2.2, "slope": 0.42, "targets": 1900, "clumps": 22, "size": 0.75, "bloom": True, "twin": False, "plan": {"far_cards": 3, "far_rows": 1, "shadow_thin": 1, "shadow_cards": 1, "shadow_scale": 1.25}},
    {"height": 4.0, "trunk": 2.7, "radius": 0.15, "sweep": 1.1, "center": (2.6, 0.2, 2.5), "rx": 2.7, "ry": 1.6, "up": 1.4, "down": 1.2, "top": 1.75, "slope": 0.42, "targets": 2000, "clumps": 24, "size": 0.75, "bloom": False, "twin": True, "plan": {"far_cards": 2, "far_rows": 1, "shadow_thin": 1, "shadow_cards": 1, "shadow_scale": 1.25}},
)
table = ((0.1, (12, 7, 5), (0.008, 0.04, 0.15)), (0.05, (8, 5, 4), (0.012, 0.06, 0.2)), (0.025, (6, 4, 3), (0.016, 0.1, 0.3)), (0.012, (4, 3, 0), (0.02, 0.15, 0.4)), (0.0, (3, 0, 0), (0.025, 0.2, 0.5)))


def skeleton(variant):
    profile = profiles[variant]
    rng = random.Random(7841 + variant * 433)
    phase = rng.uniform(0.0, 10.0)
    low = [Vector((0.02 * level, 0.0, level)) for level in (-0.4, -0.2, 0.0, 0.1, 0.22, 0.4)]
    aim = Vector((profile["sweep"], rng.uniform(-0.15, 0.15), 0.55)).normalized()
    path = wood.grow(rng, low[-1], Vector((0.22, rng.uniform(-0.1, 0.1), 1.0)), profile["trunk"], 0.16, 0.06, lambda point, t: (aim, 0.55 + 1.2 * t), 0.3, (0.3, 0.55))
    root = wood.limb_c(low + path[1:], 0)
    root.shape = trees.flare_shape(phase, 0.9, 0.5, 4.0, 0.07)
    stems = [root]
    if profile["twin"]:
        marks = root.marks()
        node = len(low) + 1
        second_aim = Vector((profile["sweep"] * 0.8, 0.5, 0.6)).normalized()
        second = wood.limb_c(wood.grow(rng, root.points[node], Vector((0.1, 0.35, 1.0)), profile["trunk"] * 0.8, 0.16, 0.06, lambda point, t: (second_aim, 0.5 + 1.2 * t), 0.3, (0.3, 0.55)), 0, root, marks[node])
        stems.append(second)
    center = Vector(profile["center"])

    def sheltered(point):
        return point.z <= profile["top"] + profile["slope"] * point.x and point.z > 0.75

    targets = wood.clump_points(rng, profile["targets"], center, (profile["rx"], profile["ry"]), profile["up"], profile["down"], profile["clumps"], profile["size"], (0.3, 0.9), None, None, sheltered)
    created = wood.colonize(rng, root, targets, 0.2, 1.2, 0.23, 0.35, Vector((0.22, 0.0, 0.04)), 100, 3, 0.85, 0.14, None, 0)
    leafy = trees.leafy_tips(created, 0.42, 0.34)
    for stem in stems:
        stem.leafy = True
        stem.bare = max(0.0, 1.0 - 0.5 / stem.length())
        leafy.append(stem)
    wood.assign_radii(root, profile["radius"], 0.004, 2.0, 0.5, 0.08)
    trees.census("hawthorn", variant, root, leafy)
    profile["aim"] = None
    profile["split"] = 99.0
    profile["skip_radius"] = 0.0
    return root, leafy, wood.crown_shade(center, max(profile["rx"], profile["ry"]), profile["up"] + 0.5, profile["down"] + 0.6, (0.52, 0.2, 0.4)), profile


def build(variant, lod):
    blossom = profiles[variant]["bloom"]
    return trees.assemble("hawthorn", variant, lod, skeleton, bloom_frames if blossom else leaf_frames, bloom_lengths if blossom else lengths, bark.hawthorn_zones, 1.2, 0.8, table, 9307)


species = {"hawthorn": {"kind": "tree", "variants": 3, "atlas": atlas, "build": build}}
