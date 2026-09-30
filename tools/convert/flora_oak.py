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
    envelope = (t ** 0.62) * ((1.0 - t) ** 0.33) / 0.5415
    phase = 0.2 if side < 0.0 else 0.62
    lobe = (0.5 - 0.5 * math.cos(math.tau * (t * 4.3 + phase))) ** 0.55
    depth = 0.5 * math.sin(math.pi * t) ** 0.5
    return envelope * (1.0 - depth * (1.0 - lobe))


leaf = sprig.leaf_style(outline=outline, rows=42, petiole=0.05, stalk=0.035, fold=0.1, curl=0.3, wave=0.014, wave_count=4.0, veins=5.0, slant=1.1, vein_width=0.14, vein_strength=0.3, front=((0.038, 0.09, 0.024), (0.052, 0.118, 0.03)), back=((0.078, 0.126, 0.052), (0.088, 0.138, 0.056)), vein=(0.115, 0.17, 0.056), stem=(0.1, 0.13, 0.04), rough=0.5)
twig_color = (0.07, 0.056, 0.042)
shoot_color = (0.095, 0.095, 0.05)


def leafage(target, rng, origin, axis, count, spread, tone, young):
    for index in range(count):
        angle = kit.lerp(-spread, spread, (index + rng.uniform(0.15, 0.85)) / count)
        direction = Matrix.Rotation(angle, 3, 'Z') @ axis
        direction = (direction + Vector((0.0, 0.0, rng.uniform(-0.4, 0.4)))).normalized()
        length = rng.uniform(0.072, 0.118) * (0.85 if young else 1.0)
        width = length * rng.uniform(0.54, 0.68)
        shade = trees.shift(rng, 0.8, 1.2, 0.07)
        shade = tuple(shade[channel] * tone[channel] for channel in range(3))
        wash = ((0.17, 0.16, 0.05), rng.uniform(0.15, 0.4)) if rng.random() < 0.03 else None
        flipped = rng.random() < 0.06
        hint = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), -1.0 if flipped else 1.0))
        with target.place(sprig.basis(origin + axis * rng.uniform(0.0, 0.025) + Vector((0.0, 0.0, rng.uniform(-0.012, 0.012))), direction, hint, rng.uniform(-0.35, 0.35))):
            target.leaf(leaf, length, width, shade, wash, rng.uniform(0.05, 0.55), rng.uniform(0.04, 0.3))


def shoot(target, rng, start, direction, length, tone, young, thickness):
    nodes = max(2, int(length / 0.045))
    points = [start.copy()]
    heading = direction.normalized()
    for index in range(nodes):
        heading = (Matrix.Rotation(rng.uniform(0.12, 0.34) * (1.0 if index % 2 else -1.0), 3, 'Z') @ heading + Vector((0.0, 0.0, rng.uniform(-0.12, 0.12)))).normalized()
        points.append(points[-1] + heading * length / nodes)
    target.tube(points, thickness, thickness * 0.45, twig_color if young is False else shoot_color, shoot_color, 0.85, 5)
    for index in range(1, nodes):
        if index / nodes > 0.2 and rng.random() < 0.85:
            side = 1.0 if index % 2 else -1.0
            axis = Matrix.Rotation(side * rng.uniform(0.7, 1.25), 3, 'Z') @ (points[index + 1] - points[index]).normalized()
            leafage(target, rng, points[index], axis, 1, 0.2, tone, young)
    leafage(target, rng, points[-1], heading, rng.randint(6, 9), 2.1, tone, young)
    return points


def spray(target, rng, length, nodes, reach, tone, fan):
    heading = Vector((0.0, 1.0, 0.0))
    points = [Vector((0.0, 0.0, 0.0))]
    joints = []
    for index in range(nodes):
        kink = rng.uniform(0.16, 0.4) * (1.0 if index % 2 else -1.0)
        heading = (Matrix.Rotation(kink, 3, 'Z') @ heading).normalized()
        heading = (heading + Vector((-heading.x * 0.3, 0.0, rng.uniform(-0.08, 0.08)))).normalized()
        points.append(points[-1] + heading * length / nodes)
        joints.append((points[-1].copy(), heading.copy(), index))
    target.tube(points, 0.008, 0.0032, twig_color, twig_color, 0.88, 6)
    for point, along, index in joints[:-1]:
        t = (index + 1) / nodes
        sides = (1.0, -1.0) if rng.random() < 0.35 else ((1.0,) if index % 2 else (-1.0,))
        for side in sides:
            young = rng.random() < 0.22
            local = tuple(tone[channel] * ((1.22, 1.16, 0.9)[channel] if young else 1.0) for channel in range(3))
            direction = Matrix.Rotation(side * rng.uniform(0.7, 1.1) * fan, 3, 'Z') @ along
            direction = (direction + Vector((0.0, 0.0, rng.uniform(-0.3, 0.3)))).normalized()
            span = reach * (1.0 - 0.55 * t) * rng.uniform(0.8, 1.15) * (0.6 + 0.4 * min(1.0, t * 4.0))
            stem = shoot(target, rng, point, direction, span, local, young, 0.0044)
            if span > reach * 0.5 and rng.random() < 0.85:
                base = stem[max(1, len(stem) // 2)]
                shoot(target, rng, base, (Matrix.Rotation(-side * rng.uniform(0.6, 1.0), 3, 'Z') @ direction).normalized(), span * rng.uniform(0.45, 0.6), local, young, 0.003)
        if t > 0.25 and rng.random() < 0.6:
            leafage(target, rng, point, (Matrix.Rotation(rng.uniform(-1.4, 1.4), 3, 'Z') @ along).normalized(), rng.randint(3, 5), 1.3, tone, False)
    shoot(target, rng, points[-1], heading, reach * 0.4, tone, False, 0.004)


def cell_a(target, rng):
    spray(target, rng, 0.56, 10, 0.3, (1.0, 1.0, 1.0), 1.0)


def cell_b(target, rng):
    spray(target, rng, 0.46, 8, 0.38, (0.94, 0.97, 0.95), 1.15)


def cell_c(target, rng):
    spray(target, rng, 0.5, 9, 0.27, (1.08, 1.05, 0.96), 0.9)


builders = {"a": cell_a, "b": cell_b, "c": cell_c}
lengths = {"f0": 0.7, "f1": 0.76, "f2": 0.82, "f3": 0.88}


def frames(rng, points, lod, aim=None):
    result = []
    length = kit.path_length(points)
    walked = 0.12
    while walked < 0.86:
        base, along = kit.point_on(points, walked)
        hint = skyward if aim is None else aim(base)
        direction = wood.deflect(rng, along, math.radians(rng.uniform(40.0, 72.0)))
        direction = (direction - hint * direction.dot(hint) * 0.55).normalized()
        forward, right, up = wood.frame_of(direction, rng.uniform(-0.5, 0.5), hint)
        result.append((base, forward, right, up, rng.choice(("a", "b", "c")), rng.uniform(0.8, 1.05), rng.uniform(0.05, 0.3), rng.random() < 0.5))
        walked += rng.uniform(0.13, 0.18) / max(length, 0.4)
    base, along = kit.point_on(points, 0.84)
    hint = skyward if aim is None else aim(base)
    for roll in (rng.uniform(-0.4, 0.4), rng.uniform(0.5, 1.1), rng.uniform(-1.1, -0.5)):
        forward, right, up = wood.frame_of((along + hint * 0.15).normalized(), roll, hint)
        result.append((base, forward, right, up, rng.choice(("a", "c", "b")), rng.uniform(0.9, 1.1), rng.uniform(0.05, 0.25), rng.random() < 0.5))
    return result


def far(name):
    def builder(target, rng):
        trees.bough(target, rng, frames, builders, lengths[name], 0.014, twig_color)
    return builder


def atlas():
    sheet = sprig.atlas_c("oak")
    sheet.cell("a", (0.0, 0.5, 0.5, 1.0), cell_a, 11)
    sheet.cell("b", (0.5, 0.5, 1.0, 1.0), cell_b, 23)
    sheet.cell("c", (0.0, 0.0, 0.5, 0.5), cell_c, 37)
    for index, name in enumerate(sorted(lengths)):
        sheet.cell(name, (0.5 + 0.25 * (index % 2), 0.25 * (index // 2), 0.75 + 0.25 * (index % 2), 0.25 + 0.25 * (index // 2)), far(name), 101 + index * 17, 0.02, 1.2)
    return sheet.render()


profiles = (
    {"height": 14.2, "spread": 8.4, "fork": 2.6, "radius": 0.52, "limbs": 6, "broken": True, "center": 6.4, "down": 3.4, "lean": 0.02, "tilt": 0.4, "flare": 1.0, "targets": 1600, "influence": 2.3, "kill": 0.72, "split": 5.2, "clumps": 30, "size": 2.7, "plan": {}},
    {"height": 12.6, "spread": 5.5, "fork": 3.2, "radius": 0.36, "limbs": 5, "broken": False, "center": 6.9, "down": 3.3, "lean": 0.05, "tilt": 0.5, "flare": 0.85, "targets": 1000, "influence": 2.2, "kill": 0.66, "split": 6.5, "clumps": 20, "size": 2.2, "offset": (1.0, -0.4), "plan": {"shadow_thin": 1}},
    {"height": 6.5, "spread": 2.3, "fork": 1.8, "radius": 0.13, "limbs": 0, "broken": False, "center": 3.9, "down": 2.1, "lean": 0.06, "tilt": 0.07, "flare": 0.6, "targets": 700, "influence": 1.5, "kill": 0.38, "split": 9.0, "clumps": 11, "size": 1.2, "shell": (0.25, 0.8), "gauge": 0.4, "plan": {"far_cards": 3, "far_rows": 2, "shadow_thin": 1, "shadow_cards": 2, "shadow_scale": 1.1}},
)
table = ((0.3, (14, 8, 5), (0.012, 0.06, 0.25)), (0.16, (10, 6, 4), (0.02, 0.1, 0.3)), (0.08, (7, 5, 3), (0.03, 0.15, 0.4)), (0.04, (5, 3, 3), (0.04, 0.25, 0.6)), (0.02, (4, 0, 0), (0.05, 0.3, 0.6)), (0.0, (3, 0, 0), (0.05, 0.3, 0.6)))


def skeleton(variant):
    profile = profiles[variant]
    rng = random.Random(7001 + variant * 977)
    height = profile["height"]
    spread = profile["spread"]
    fork = profile["fork"]
    center = Vector((profile.get("offset", (0.0, 0.0))[0], profile.get("offset", (0.0, 0.0))[1], profile["center"]))
    lean_angle = rng.uniform(0.0, math.tau)
    lean = Vector((math.cos(lean_angle), math.sin(lean_angle), 0.0)) * profile["lean"]
    phase = rng.uniform(0.0, 10.0)
    trunk = trees.trunk_path(rng, fork, lean, phase)
    tilt_angle = rng.uniform(0.0, math.tau)
    tilt = Vector((math.cos(tilt_angle), math.sin(tilt_angle), 0.0))
    leader = wood.grow(rng, trunk[-1], (skyward + tilt * profile["tilt"]).normalized(), (height - fork) * 0.6, 0.35, 0.05, lambda point, t: (skyward, 0.2), 0.3, (0.8, 1.3))
    root = wood.limb_c(trunk + leader[1:], 0)
    root.zone = 0
    root.switch = 1.7
    root.shape = trees.flare_shape(phase, profile["flare"])
    marks = root.marks()
    broken = []
    for index in range(profile["limbs"]):
        azimuth = tilt_angle + math.tau * (index + 1) / (profile["limbs"] + 1) + rng.uniform(-0.25, 0.25)
        elevation = math.radians(rng.uniform(6.0, 22.0) if index % 2 == 0 else rng.uniform(28.0, 52.0))
        heading = Vector((math.cos(azimuth) * math.cos(elevation), math.sin(azimuth) * math.cos(elevation), math.sin(elevation)))
        level = fork - rng.uniform(0.0, 0.85)
        node = min(range(len(trunk)), key=lambda entry: abs(trunk[entry].z - level))
        points = wood.grow(rng, trunk[node], heading, spread * rng.uniform(0.5, 0.66) / max(math.cos(elevation), 0.5), 0.35, 0.05, lambda point, t: (skyward, -0.03 + 0.45 * t * t), 0.34, (0.8, 1.3))
        limb = wood.limb_c(points, 1, root, marks[node])
        limb.zone = 1
        if profile["broken"] and index == 2:
            limb.points = limb.points[:max(4, int(rng.uniform(2.0, 2.8) / 0.35)) + 1]
            limb.broken = True
            limb.own = 40.0
            broken.append(limb)
    targets = wood.clump_points(rng, profile["targets"], center, (spread, spread), height - center.z, profile["down"], profile["clumps"], profile["size"], profile.get("shell", (0.55, 0.86)))
    created = wood.colonize(rng, root, targets, 0.38, profile["influence"], profile["kill"], 0.35, 0.12, 90, 3, fork - 0.4, 0.15, broken, 1)
    leafy = trees.leafy_tips(created)
    wood.assign_radii(root, profile["radius"], 0.006, 2.0, 0.45, 0.08)
    trees.census("oak", variant, root, leafy)
    profile["aim"] = trees.crown_aim(center, spread, height - center.z, profile["down"])
    return root, leafy, wood.crown_shade(center, spread, height - center.z, profile["down"]), profile


def build(variant, lod):
    return trees.assemble("oak", variant, lod, skeleton, frames, lengths, bark.oak_zones, 2.6, 1.6, table, 9001)


species = {"oak": {"kind": "tree", "variants": 3, "atlas": atlas, "build": build}}
