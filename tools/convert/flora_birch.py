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
    rise = min(t / 0.3, 1.0) ** 0.75
    fall = max(0.0, 1.0 - max(t - 0.3, 0.0) / 0.7) ** 1.15
    teeth = 1.0 + 0.1 * ((t * 11.0) % 1.0 - 0.5) + 0.05 * ((t * 33.0) % 1.0 - 0.5)
    return rise * fall * teeth


leaf = sprig.leaf_style(outline=outline, rows=44, petiole=0.32, stalk=0.022, fold=0.12, curl=0.25, wave=0.01, wave_count=3.0, veins=7.0, slant=1.3, vein_width=0.12, vein_strength=0.22, front=((0.07, 0.145, 0.028), (0.086, 0.168, 0.034)), back=((0.1, 0.162, 0.06), (0.112, 0.176, 0.066)), vein=(0.13, 0.19, 0.06), stem=(0.11, 0.15, 0.045), rough=0.45)
twig_color = (0.04, 0.026, 0.024)
catkin_color = (0.17, 0.15, 0.05)


def blade(target, rng, origin, direction, size, tone):
    shade = trees.shift(rng, 0.82, 1.2, 0.06)
    shade = tuple(shade[channel] * tone[channel] for channel in range(3))
    wash = ((0.24, 0.21, 0.04), rng.uniform(0.2, 0.55)) if rng.random() < 0.04 else None
    hint = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), -1.0 if rng.random() < 0.08 else 1.0))
    length = size * rng.uniform(0.85, 1.15)
    with target.place(sprig.basis(origin, direction, hint, rng.uniform(-0.4, 0.4))):
        target.leaf(leaf, length * 1.32, length * rng.uniform(0.74, 0.86), shade, wash, rng.uniform(0.0, 0.45), rng.uniform(0.02, 0.25))


def strand(target, rng, length, fullness, tone, catkins):
    nodes = max(6, int(length / 0.024))
    phase = rng.uniform(0.0, math.tau)
    sway = rng.uniform(0.02, 0.05) * length
    points = [Vector((math.sin(index / nodes * 2.6 + phase) * sway - math.sin(phase) * sway, length * index / nodes, math.sin(index / nodes * 3.1 + phase * 0.7) * 0.015 * length)) for index in range(nodes + 1)]
    target.tube(points, 0.0019, 0.0006, twig_color, twig_color, 0.7, 4)
    for index in range(2, nodes):
        t = index / nodes
        along = (points[index + 1] - points[index - 1]).normalized()
        side = 1.0 if index % 2 else -1.0
        if rng.random() > fullness:
            continue
        size = 0.046 * (1.0 - 0.3 * t)
        if rng.random() < 0.45 and t < 0.85:
            reach = rng.uniform(0.08, 0.22) * (1.0 - 0.45 * t)
            heading = (Matrix.Rotation(side * rng.uniform(0.45, 0.85), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.25, 0.25)))).normalized()
            steps = max(2, int(reach / 0.028))
            shoot = [points[index] + heading * reach * step / steps + Vector((side * 0.006 * math.sin(step * 1.7), 0.0, 0.0)) for step in range(steps + 1)]
            target.tube(shoot, 0.0011, 0.0005, twig_color, twig_color, 0.7, 3)
            for step in range(1, steps + 1):
                flip = 1.0 if step % 2 else -1.0
                blade(target, rng, shoot[step], (Matrix.Rotation(flip * rng.uniform(0.4, 1.0), 3, 'Z') @ heading + Vector((0.0, 0.0, rng.uniform(-0.3, 0.3)))).normalized(), size, tone)
        else:
            for count in range(rng.randint(2, 3)):
                blade(target, rng, points[index], (Matrix.Rotation(side * rng.uniform(0.35, 1.15), 3, 'Z') @ along + Vector((0.0, 0.0, rng.uniform(-0.35, 0.35)))).normalized(), size, tone)
        if catkins and rng.random() < 0.09 and t > 0.25:
            heading = (Matrix.Rotation(-side * rng.uniform(0.2, 0.6), 3, 'Z') @ along).normalized()
            start = points[index] + heading * 0.012
            target.tube([start, start + heading * 0.014, start + heading * 0.028], 0.0032, 0.0026, catkin_color, (0.12, 0.1, 0.04), 0.8, 6)
    for count in range(2):
        blade(target, rng, points[-1], (Matrix.Rotation(rng.uniform(-0.6, 0.6), 3, 'Z') @ Vector((0.0, 1.0, 0.0))).normalized(), 0.034, tone)


def cell_a(target, rng):
    strand(target, rng, 0.92, 0.9, (1.0, 1.0, 1.0), False)


def cell_b(target, rng):
    strand(target, rng, 0.74, 0.95, (0.95, 0.98, 0.98), False)


def cell_c(target, rng):
    strand(target, rng, 0.84, 0.85, (1.08, 1.04, 0.92), True)


def cell_d(target, rng):
    strand(target, rng, 0.62, 0.95, (1.0, 1.02, 0.95), False)


builders = {"a": cell_a, "b": cell_b, "c": cell_c, "d": cell_d}
lengths = {"f0": 0.75, "f1": 0.8, "f2": 0.85}


def frames(rng, points, lod, aim=None):
    result = []
    length = kit.path_length(points)
    walked = 0.1
    while walked <= 1.0:
        base, along = kit.point_on(points, min(walked, 0.99))
        flat = Vector((along.x, along.y, 0.0))
        flat = flat.normalized() if flat.length > 1e-4 else Vector((1.0, 0.0, 0.0))
        yaw = rng.uniform(0.0, math.tau)
        direction = (Vector((0.0, 0.0, -1.0)) + flat * rng.uniform(0.05, 0.4) + Vector((math.cos(yaw), math.sin(yaw), 0.0)) * rng.uniform(0.0, 0.25)).normalized()
        face = rng.uniform(0.0, math.tau)
        forward, right, up = wood.frame_of(direction, 0.0, Vector((math.cos(face), math.sin(face), 0.0)))
        result.append((base, forward, right, up, rng.choice(("a", "b", "c", "d")), rng.uniform(0.85, 1.15), rng.uniform(0.03, 0.15), rng.random() < 0.5))
        walked += rng.uniform(0.08, 0.12) / max(length, 0.4)
    return result


def far(name):
    def builder(target, rng):
        trees.bough(target, rng, frames, builders, lengths[name], 0.0, twig_color, 0.6)
    return builder


def atlas():
    sheet = sprig.atlas_c("birch")
    for index, name in enumerate(("a", "b", "c", "d")):
        sheet.cell(name, (0.25 * index, 0.45, 0.25 * index + 0.25, 1.0), builders[name], 211 + index * 13)
    for index, name in enumerate(sorted(lengths)):
        sheet.cell(name, (index / 3.0, 0.0, (index + 1) / 3.0, 0.45), far(name), 307 + index * 19, 0.02, 1.0)
    return sheet.render()


profiles = (
    {"height": 12.0, "spread": 2.7, "base": 4.2, "radius": 0.17, "lean": 0.02, "bow": 0.0, "fork": None, "targets": 1400, "influence": 1.6, "kill": 0.42, "clumps": 24, "size": 1.35, "split": 6.0, "plan": {"shadow_thin": 1}},
    {"height": 10.6, "spread": 3.3, "base": 3.6, "radius": 0.2, "lean": 0.03, "bow": 0.0, "fork": 2.3, "targets": 1500, "influence": 1.6, "kill": 0.42, "clumps": 26, "size": 1.35, "split": 6.0, "plan": {"shadow_thin": 1}},
    {"height": 9.2, "spread": 2.5, "base": 3.4, "radius": 0.14, "lean": 0.2, "bow": 0.55, "fork": None, "targets": 1100, "influence": 1.5, "kill": 0.4, "clumps": 20, "size": 1.25, "split": 6.0, "plan": {"shadow_thin": 1}},
)
table = ((0.12, (12, 7, 5), (0.01, 0.05, 0.2)), (0.06, (8, 5, 4), (0.015, 0.08, 0.3)), (0.03, (6, 4, 3), (0.02, 0.12, 0.4)), (0.015, (4, 3, 0), (0.03, 0.2, 0.5)), (0.0, (3, 0, 0), (0.04, 0.3, 0.6)))


def stem_path(rng, start, heading, length, bow, bow_axis, phase):
    points = [start.copy()]
    steps = max(6, int(length / 0.4))
    for index in range(1, steps + 1):
        t = index / steps
        lean = heading + bow_axis * bow * (t - 0.5) * -1.0
        lean.normalize()
        wobble = Vector((math.sin(t * 7.0 + phase), math.cos(t * 5.3 + phase * 1.3), 0.0)) * 0.035
        points.append(points[-1] + lean * (length / steps) + wobble * (length / steps))
    return points


def zoning(root):
    for limb in wood.walk(root):
        if limb.parent is None:
            continue
        marks = limb.marks()
        length = limb.length()
        if limb.radii[0] < 0.028:
            limb.zone = 2
            limb.switch = None
            continue
        limb.zone = 1
        thin = next((marks[index] for index in range(len(marks)) if limb.radii[index] < 0.022), 1.0)
        limb.switch = thin * length


def skeleton(variant):
    profile = profiles[variant]
    rng = random.Random(7411 + variant * 613)
    height = profile["height"]
    spread = profile["spread"]
    lean_angle = rng.uniform(0.0, math.tau)
    lean_axis = Vector((math.cos(lean_angle), math.sin(lean_angle), 0.0))
    phase = rng.uniform(0.0, 10.0)
    heading = (skyward + lean_axis * profile["lean"]).normalized()
    low = [Vector((lean_axis.x * profile["lean"] * level, lean_axis.y * profile["lean"] * level, level)) for level in (-0.5, -0.25, 0.0, 0.12, 0.28, 0.5, 0.8)]
    top = profile["fork"] if profile["fork"] else height * 0.97
    stem = stem_path(rng, low[-1], heading, (top - 0.8) / max(heading.z, 0.5), profile["bow"], lean_axis, phase)
    root = wood.limb_c(low + stem[1:], 0)
    root.shape = trees.flare_shape(phase, 0.75, 0.9, 4.0, 0.03)
    stems = [root]
    if profile["fork"]:
        split_angle = rng.uniform(0.0, math.tau)
        split_axis = Vector((math.cos(split_angle), math.sin(split_angle), 0.0))
        first = stem_path(rng, root.points[-1], (skyward + split_axis * 0.2).normalized(), height * 0.97 - profile["fork"], 0.25, split_axis, phase + 2.0)
        root.points.extend(first[1:])
        mark = root.marks()[len(low) + len(stem) - 2]
        second = wood.limb_c(stem_path(rng, root.points[len(low) + len(stem) - 2], (skyward - split_axis * 0.24).normalized(), (height * 0.9 - profile["fork"]), 0.3, -split_axis, phase + 4.0), 0, root, mark)
        stems.append(second)
    tip = root.points[-1]
    center = Vector((tip.x * 0.6, tip.y * 0.6, profile["base"] + (height - profile["base"]) * 0.52))
    up = height - center.z
    down = center.z - profile["base"]
    targets = wood.clump_points(rng, profile["targets"], center, (spread, spread), up, down, profile["clumps"], profile["size"], (0.3, 0.85))
    created = wood.colonize(rng, root, targets, 0.34, profile["influence"], profile["kill"], 0.5, 0.3, 90, 3, profile["base"] - 0.3, 0.12, None, 1)
    leafy = trees.leafy_tips(created, 0.8, 0.6)
    for other in stems:
        other.leafy = True
        other.bare = max(0.0, 1.0 - 1.3 / other.length())
        leafy.append(other)
    wood.assign_radii(root, profile["radius"], 0.004, 2.0, 0.5, 0.08)
    root.zone = 0
    root.switch = [rng.uniform(0.9, 1.3), root.length() * 0.9]
    zoning(root)
    for other in stems[1:]:
        other.zone = 1
        other.switch = other.length() * 0.88
    trees.census("birch", variant, root, leafy)
    profile["aim"] = None
    return root, leafy, wood.crown_shade(center, spread, up, down + 1.0), profile


def build(variant, lod):
    return trees.assemble("birch", variant, lod, skeleton, frames, lengths, bark.birch_zones, 2.0, 1.0, table, 9101, 0.4, True)


species = {"birch": {"kind": "tree", "variants": 3, "atlas": atlas, "build": build, "solid": (0.22, 0.74)}}
