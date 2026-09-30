import math
import random
from mathutils import Matrix, Vector

import flora_kit as kit
import flora_bark as bark
import flora_sprig as sprig
import flora_wood as wood
import flora_trees as trees

skyward = Vector((0.0, 0.0, 1.0))


def outline(t, side):
    rise = min(t / 0.36, 1.0) ** 0.7
    fall = max(0.0, 1.0 - max(t - 0.36, 0.0) / 0.64) ** 0.9
    teeth = 1.0 + 0.05 * ((t * 24.0) % 1.0 - 0.5)
    return rise * fall * teeth


leaf = sprig.leaf_style(outline=outline, rows=36, columns=(-1.0, -0.5, -0.12, 0.12, 0.5, 1.0), petiole=0.07, stalk=0.06, fold=0.22, curl=0.6, veins=12.0, slant=0.8, vein_width=0.1, vein_strength=0.12, midrib_width=0.13, front=((0.082, 0.142, 0.062), (0.098, 0.165, 0.07)), back=((0.17, 0.215, 0.145), (0.19, 0.235, 0.16)), vein=(0.17, 0.22, 0.1), stem=(0.13, 0.15, 0.05), rough=0.38, back_rough=0.75)
twig_color = (0.12, 0.115, 0.05)
old_twig = (0.085, 0.075, 0.05)


def blade(target, rng, origin, direction, size, tone):
    shade = trees.shift(rng, 0.84, 1.18, 0.06)
    shade = tuple(shade[channel] * tone[channel] for channel in range(3))
    wash = ((0.26, 0.23, 0.05), rng.uniform(0.2, 0.5)) if rng.random() < 0.03 else None
    hint = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), -1.0 if rng.random() < 0.24 else 1.0))
    length = size * rng.uniform(0.85, 1.15)
    with target.place(sprig.basis(origin, direction, hint, rng.uniform(-0.5, 0.5))):
        target.leaf(leaf, length, length * rng.uniform(0.15, 0.2), shade, wash, rng.uniform(0.2, 0.95), rng.uniform(0.1, 0.34), rng.uniform(-0.6, 0.6))


def wand(target, rng, start, direction, length, size, tone, thickness, droop):
    nodes = max(4, int(length / 0.017))
    points = [start.copy()]
    heading = direction.normalized()
    sag = rng.choice((-1.0, 1.0)) * droop
    for index in range(nodes):
        heading = (Matrix.Rotation(sag * 0.035, 3, 'Z') @ heading + Vector((0.0, 0.0, rng.uniform(-0.03, 0.03)))).normalized()
        points.append(points[-1] + heading * length / nodes)
    target.tube(points, thickness, thickness * 0.35, twig_color, (0.15, 0.17, 0.06), 0.6, 4)
    for index in range(1, nodes + 1):
        t = index / nodes
        side = 1.0 if index % 2 else -1.0
        along = (points[index] - points[index - 1]).normalized()
        aim = (Matrix.Rotation(side * rng.uniform(0.45, 0.85), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.35, 0.35)))).normalized()
        blade(target, rng, points[index], aim, size * (1.0 - 0.45 * t ** 2) * (0.6 + 0.4 * min(1.0, t * 5.0)), tone)
    return points


def spray(target, rng, length, tone, twigs):
    main = wand(target, rng, Vector((0.0, 0.0, 0.0)), Vector((rng.uniform(-0.08, 0.08), 1.0, 0.0)), length, 0.125, tone, 0.0026, rng.uniform(0.3, 1.0))
    for index in range(twigs):
        node = int(len(main) * rng.uniform(0.08, 0.5))
        side = 1.0 if index % 2 else -1.0
        along = (main[node + 1] - main[node]).normalized()
        direction = (Matrix.Rotation(side * rng.uniform(0.45, 0.8), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.25, 0.25)))).normalized()
        wand(target, rng, main[node], direction, length * rng.uniform(0.35, 0.6), 0.105, tone, 0.0017, rng.uniform(0.3, 1.2))


def cell_a(target, rng):
    spray(target, rng, 0.62, (1.0, 1.0, 1.0), 7)


def cell_b(target, rng):
    spray(target, rng, 0.5, (0.94, 0.98, 0.98), 8)


def cell_c(target, rng):
    spray(target, rng, 0.56, (1.08, 1.05, 0.94), 6)


builders = {"a": cell_a, "b": cell_b, "c": cell_c}
lengths = {"f0": 0.7, "f1": 0.78, "f2": 0.86}


def frames(rng, points, lod, aim=None):
    result = []
    length = kit.path_length(points)
    walked = 0.1
    while walked < 0.92:
        base, along = kit.point_on(points, walked)
        direction = wood.deflect(rng, along, math.radians(rng.uniform(30.0, 65.0)))
        direction = (direction + Vector((0.0, 0.0, -0.22))).normalized()
        forward, right, up = wood.frame_of(direction, rng.uniform(-0.7, 0.7), skyward if aim is None else aim(base))
        result.append((base, forward, right, up, rng.choice(("a", "b", "c")), rng.uniform(0.9, 1.2), rng.uniform(0.1, 0.4), rng.random() < 0.5))
        walked += rng.uniform(0.1, 0.14) / max(length, 0.4)
    base, along = kit.point_on(points, 0.9)
    for roll in (rng.uniform(-0.4, 0.4), rng.uniform(0.7, 1.3), rng.uniform(-1.3, -0.7)):
        forward, right, up = wood.frame_of((along + Vector((0.0, 0.0, -0.1))).normalized(), roll, skyward if aim is None else aim(base))
        result.append((base, forward, right, up, rng.choice(("a", "b", "c")), rng.uniform(0.95, 1.2), rng.uniform(0.1, 0.35), rng.random() < 0.5))
    return result


def far(name):
    def builder(target, rng):
        trees.bough(target, rng, frames, builders, lengths[name], 0.01, old_twig)
    return builder


def atlas():
    sheet = sprig.atlas_c("willow")
    for index, name in enumerate(("a", "b", "c")):
        sheet.cell(name, (index / 3.0, 0.42, (index + 1) / 3.0, 1.0), builders[name], 811 + index * 13)
    for index, name in enumerate(sorted(lengths)):
        sheet.cell(name, (index / 3.0, 0.0, (index + 1) / 3.0, 0.42), far(name), 857 + index * 17, 0.02, 0.9)
    return sheet.render()


profiles = (
    {"height": 9.0, "spread": 4.6, "fork": 0.55, "radius": 0.34, "stems": ((0.0, 0.28), (2.1, 0.42), (4.2, 0.3), (5.3, 0.2)), "center": (0.5, 0.0, 5.6), "up": 3.3, "down": 3.0, "targets": 2000, "clumps": 28, "size": 1.9, "split": 4.4, "plan": {"shadow_thin": 1, "shadow_cards": 2, "shadow_scale": 1.15}},
    {"height": 7.4, "spread": 4.0, "fork": 0.4, "radius": 0.3, "stems": ((0.4, 0.34), (2.6, 0.3), (4.6, 0.4)), "center": (0.2, 0.2, 4.6), "up": 2.7, "down": 2.6, "targets": 1700, "clumps": 24, "size": 1.8, "split": 4.0, "plan": {"shadow_thin": 1, "shadow_cards": 2, "shadow_scale": 1.15, "far_cards": 3}},
    {"height": 8.2, "spread": 4.4, "fork": 0.35, "radius": 0.36, "stems": ((0.0, 0.75), (1.4, 0.25), (2.9, 0.3), (4.1, 0.2), (5.4, 0.34)), "center": (1.6, 0.0, 4.9), "up": 3.1, "down": 2.8, "targets": 2000, "clumps": 28, "size": 1.9, "split": 4.2, "plan": {"shadow_thin": 1, "shadow_cards": 2, "shadow_scale": 1.15}},
)
table = ((0.2, (12, 7, 5), (0.012, 0.06, 0.25)), (0.1, (9, 6, 4), (0.02, 0.1, 0.3)), (0.05, (7, 4, 3), (0.03, 0.15, 0.4)), (0.025, (5, 3, 0), (0.04, 0.25, 0.6)), (0.012, (4, 0, 0), (0.05, 0.3, 0.6)), (0.0, (3, 0, 0), (0.05, 0.3, 0.6)))


def skeleton(variant):
    profile = profiles[variant]
    rng = random.Random(8087 + variant * 521)
    height = profile["height"]
    spread = profile["spread"]
    phase = rng.uniform(0.0, 10.0)
    low = [Vector((0.0, 0.0, level)) for level in (-0.45, -0.22, 0.0, 0.12, 0.26, profile["fork"])]
    stems = []
    root = None
    for index, (azimuth, tilt) in enumerate(profile["stems"]):
        outward = Vector((math.cos(azimuth), math.sin(azimuth), 0.0))
        heading = (skyward + outward * tilt).normalized()
        length = (height * rng.uniform(0.62, 0.78) - profile["fork"]) / max(heading.z, 0.5)
        path = wood.grow(rng, low[-1] + outward * 0.06, heading, length, 0.36, 0.04, lambda point, t: (skyward, 0.12 * t), 0.2, (0.9, 1.5))
        if root is None:
            root = wood.limb_c(low + path[1:], 0)
            stems.append(root)
        else:
            stems.append(wood.limb_c([low[-2]] + path, 0, root, root.marks()[len(low) - 2]))
    root.shape = trees.flare_shape(phase, 1.0, 0.7, 5.0, 0.06)
    center = Vector(profile["center"])
    targets = wood.clump_points(rng, profile["targets"], center, (spread, spread * 0.92), profile["up"], profile["down"], profile["clumps"], profile["size"], (0.45, 0.88))
    created = wood.colonize(rng, root, targets, 0.36, 2.2, 0.5, 0.4, 0.14, 90, 3, profile["fork"] + 1.0, 0.14, None, 0)
    leafy = trees.leafy_tips(created, 0.8, 0.6)
    for stem in stems:
        stem.leafy = True
        stem.bare = max(0.0, 1.0 - 0.9 / stem.length())
        leafy.append(stem)
    wood.assign_radii(root, profile["radius"], 0.005, 2.0, 0.5, 0.08)
    reach = 0.0
    for stem in stems:
        for index, point in enumerate(stem.points):
            if 1.1 < point.z < 1.5:
                reach = max(reach, math.hypot(point.x, point.y) + stem.radii[index])
    print("STEMS willow", variant, round(reach, 3))
    trees.census("willow", variant, root, leafy)
    profile["aim"] = trees.crown_aim(center, spread, profile["up"], profile["down"], 0.45)
    return root, leafy, wood.crown_shade(center, spread, profile["up"], profile["down"]), profile


def build(variant, lod):
    return trees.assemble("willow", variant, lod, skeleton, frames, lengths, bark.willow_zones, 2.0, 1.2, table, 9409, 0.35)


species = {"willow": {"kind": "tree", "variants": 3, "atlas": atlas, "build": build, "solid": (0.14, 0.62)}}
