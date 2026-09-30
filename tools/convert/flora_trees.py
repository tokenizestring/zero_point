import math
import random
from mathutils import Matrix, Vector

import flora_kit as kit
import flora_sprig as sprig
import flora_wood as wood

skyward = Vector((0.0, 0.0, 1.0))


def shift(rng, low, high, warm=0.0):
    value = rng.uniform(low, high)
    return (value * (1.0 + warm * rng.uniform(-1.0, 1.0)), value, value * (1.0 - warm * rng.uniform(0.0, 1.0)))


def bough(target, rng, frames, builders, length, radius, color, rise=None):
    target.lite = True
    target.front = True
    if rise is None:
        points = [Vector((math.sin(index * 1.3) * 0.015 * length, length * index / 5.0, 0.0)) for index in range(6)]
        world = Matrix.Identity(4)
    else:
        points = [Vector((length * index / 5.0 * math.cos(rise), math.sin(index * 1.3) * 0.015 * length, length * index / 5.0 * math.sin(rise))) for index in range(6)]
        world = Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, -1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
    with target.place(world):
        if radius > 0.0:
            target.tube(points, radius, radius * 0.45, color, color, 0.85, 5)
        for origin, forward, right, up, name, scale, bend, mirror in frames(rng, points, 0):
            across = right * (-scale if mirror else scale)
            matrix = Matrix(((across.x, forward.x * scale, up.x * scale, origin.x), (across.y, forward.y * scale, up.y * scale, origin.y), (across.z, forward.z * scale, up.z * scale, origin.z), (0.0, 0.0, 0.0, 1.0)))
            with target.place(matrix):
                builders[name](target, random.Random(rng.randint(0, 1 << 30)))


def crown_aim(center, radius, up, down, lift=0.5):
    def aim(point):
        rise = point.z - center.z
        vertical = up if rise > 0.0 else down
        outward = Vector(((point.x - center.x) / (radius * radius), (point.y - center.y) / (radius * radius), rise / (vertical * vertical)))
        if outward.length < 1e-6:
            return skyward.copy()
        return (outward.normalized() * (1.0 - lift) + skyward * lift).normalized()
    return aim


def dress(model, rng, leafy, frames, cells, lengths, shade, lod, split, plan=None, fold=0.12, limits=(0.85, 1.2), aim=None, hang=False):
    plan = {} if plan is None else plan
    names = sorted(lengths)
    sprays = 0
    boughs = 0
    thin = plan.get("shadow_thin", 2)
    turns = plan.get("far_cards", 2) if lod == 1 else plan.get("shadow_cards", 1)
    rows = plan.get("far_rows", 1) if lod == 1 else 1
    for index, limb in enumerate(leafy):
        points = wood.tail(limb.points, limb.bare)
        if lod == 0:
            low = points[0].z < split
            for origin, forward, right, up, name, scale, bend, mirror in frames(rng, points, 0, aim):
                model.card(cells[name], origin, forward, right, up, scale, bend if low else 0.0, fold * rng.uniform(0.7, 1.3), 2 if low else 1, 2, mirror, shade)
                sprays += 1
            continue
        if lod == 2 and index % thin:
            continue
        forward = (points[-1] - points[0]).normalized()
        roll = rng.uniform(0.0, math.pi)
        for turn in range(turns):
            name = rng.choice(names)
            scale = kit.clamp(kit.path_length(points) / lengths[name], limits[0], limits[1]) * (plan.get("shadow_scale", 1.3) if lod == 2 else 1.0)
            mirror = rng.random() < 0.5
            if hang:
                flat = Vector((forward.x, forward.y, 0.0))
                flat = flat.normalized() if flat.length > 1e-4 else Vector((1.0, 0.0, 0.0))
                right = Matrix.Rotation(math.pi * turn / turns, 3, 'Z') @ flat
                ahead = skyward.copy()
                up = right.cross(ahead).normalized()
                mirror = mirror and turn > 0
            else:
                ahead, right, up = wood.frame_of(forward, roll + math.pi * turn / turns)
            model.card(cells[name], points[0], ahead, right, up, scale, 0.08 if rows > 1 else 0.0, 0.0, rows, 1, mirror, shade)
            boughs += 1
    print("DRESS", lod, "sprays", sprays, "boughs", boughs, "wood", sum(len(face.verts) - 2 for face in model.wood.faces), "leaf", len(model.leaf.faces) * 2)


def assemble(name, variant, lod, skeleton, frames, lengths, zones, metres, girth, table, seed, fold=0.4, hang=False):
    root, leafy, shade, profile = skeleton(variant)
    cells = sprig.load_cells(name)
    model = wood.model_c(zones, metres, girth)
    rng = random.Random(seed + variant * 31 + lod)
    for limb in wood.walk(root):
        limb.skip = limb.radii[0] < profile.get("skip_radius", 0.045) and limb.points[0].z >= profile["split"] + 0.5
    wood.mesh_limbs(model, root, lod, table, rng, profile.get("gauge", 1.0))
    dress(model, rng, leafy, frames, cells, lengths, shade, lod, profile["split"], profile.get("plan", {}), fold, (0.85, 1.2), profile.get("aim"), hang)
    return model


def trunk_path(rng, fork, lean, phase, wobble=0.06):
    levels = [-0.6, -0.3, 0.0, 0.15, 0.32, 0.55, 0.8, 1.1, 1.45]
    levels = [level for level in levels if level < fork - 0.15]
    while levels[-1] < fork - 0.05:
        levels.append(min(levels[-1] + 0.36, fork))
    return [Vector((lean.x * level + wobble * math.sin(level * 0.9 + phase), lean.y * level + wobble * math.cos(level * 0.7 + phase), level)) for level in levels]


def flare_shape(phase, amount, reach=1.5, lobes=5.0, gnarl=0.06):
    def shape(point, angle, s):
        rise = max(point.z, -0.25)
        swell = max(0.0, 1.0 - max(rise, 0.0) / reach) ** 2 + max(0.0, -rise) * 0.8
        ripple = 0.5 + 0.35 * math.cos(angle * lobes + phase) + 0.15 * math.cos(angle * 3.0 - phase * 1.7)
        knot = gnarl * math.sin(angle * 2.0 + point.z * 1.3 + phase) + gnarl * 0.66 * math.sin(angle * 3.0 - point.z * 2.3)
        return 1.0 + swell * (0.35 + 0.6 * ripple) * amount + knot
    return shape


def leafy_tips(created, span=0.8, minimum=0.7):
    leafy = []
    for limb in created:
        length = limb.length()
        if length < minimum:
            heading = (limb.points[-1] - limb.points[-2]).normalized()
            limb.points.append(limb.points[-1] + heading * (minimum - length))
            length = minimum
        limb.leafy = True
        limb.bare = max(0.0, 1.0 - span / length)
        leafy.append(limb)
    return leafy


def census(name, variant, root, leafy):
    counts = {}
    for limb in wood.walk(root):
        counts[limb.level] = counts.get(limb.level, 0) + 1
    print("SKELETON", name, variant, counts, "leafy", len(leafy))
