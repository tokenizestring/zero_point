import math
import random
from mathutils import Matrix, Vector

import flora_kit as kit
import flora_sprig as sprig
import flora_wood as wood

skyward = Vector((0.0, 0.0, 1.0))


def gradient(lobe, point):
    center, radii = lobe
    outward = Vector(((point.x - center.x) / (radii[0] ** 2), (point.y - center.y) / (radii[1] ** 2), (point.z - center.z) / (radii[2] ** 2)))
    return outward.normalized() if outward.length > 1e-6 else skyward.copy()


def depth(lobe, point):
    center, radii = lobe
    return math.sqrt(((point.x - center.x) / radii[0]) ** 2 + ((point.y - center.y) / radii[1]) ** 2 + ((point.z - center.z) / radii[2]) ** 2)


def lobe_shade(lobes, lift=0.3, facing_weight=0.2):
    def shade(point, facing):
        lobe = min(lobes, key=lambda entry: depth(entry, point))
        outward = gradient(lobe, point)
        turned = facing if facing.dot(outward) >= 0.0 else -facing
        return (outward * (1.0 - lift - facing_weight) + turned * facing_weight + skyward * lift).normalized()
    return shade


def shell(rng, lobes, count, inset=0.8, floor=0.05, dip=-0.15):
    weights = [radii[0] * radii[1] + radii[2] * (radii[0] + radii[1]) for center, radii in lobes]
    result = []
    guard = 0
    while len(result) < count and guard < count * 60:
        guard += 1
        index = rng.choices(range(len(lobes)), weights)[0]
        center, radii = lobes[index]
        direction = wood.random_unit(rng)
        if direction.z < dip:
            continue
        point = Vector((center.x + direction.x * radii[0] * inset, center.y + direction.y * radii[1] * inset, center.z + direction.z * radii[2] * inset))
        if point.z < floor:
            continue
        if any(depth(other, point) < inset * 0.97 for position, other in enumerate(lobes) if position != index):
            continue
        result.append((point, gradient(lobes[index], point)))
    return result


def ripple(u, v, seeds):
    total = 0.0
    for index, (frequency, rate, phase, weight) in enumerate(seeds):
        total += math.sin(math.tau * frequency * u + phase) * math.cos(v * rate + phase * 1.7) * weight
    return total


def bark_slab(width, height, dark, light, ridges=5, relief=0.004, rough=0.85, seed=5):
    def builder(target, rng):
        local = random.Random(seed)
        seeds = [(local.randint(1, ridges), local.uniform(2.0, 9.0), local.uniform(0.0, math.tau), local.uniform(0.4, 1.0)) for index in range(7)]
        fine = [(local.randint(ridges, ridges * 4), local.uniform(20.0, 60.0), local.uniform(0.0, math.tau), local.uniform(0.3, 0.8)) for index in range(6)]

        def shade(u, v):
            coarse = ripple(u, v * 3.0, seeds) / 3.0
            detail = ripple(u, v * 3.0, fine) / 2.4
            value = kit.clamp(0.5 + coarse * 0.6 + detail * 0.4, 0.0, 1.0)
            tint = kit.mix(dark, light, value)
            return tint[0], tint[1], tint[2], rough, (coarse * 0.7 + detail * 0.5) * relief
        target.slab(width, height, 48, 160, shade)
    return builder


def foliage_slab(width, height, colors, relief=0.01, rough=0.6, seed=9):
    def builder(target, rng):
        local = random.Random(seed)
        seeds = [(local.randint(1, 6), local.uniform(4.0, 18.0), local.uniform(0.0, math.tau), local.uniform(0.4, 1.0)) for index in range(8)]
        fine = [(local.randint(6, 22), local.uniform(30.0, 90.0), local.uniform(0.0, math.tau), local.uniform(0.3, 0.8)) for index in range(8)]

        def shade(u, v):
            coarse = ripple(u, v * 2.0, seeds) / 3.2
            detail = ripple(u, v * 2.0, fine) / 2.8
            value = kit.clamp(0.5 + coarse * 0.5 + detail * 0.6, 0.0, 0.999) * (len(colors) - 1)
            index = int(value)
            tint = kit.mix(colors[index], colors[index + 1], value - index)
            return tint[0], tint[1], tint[2], rough, (coarse * 0.5 + detail * 0.8) * relief
        target.slab(width, height, 96, 96, shade)
    return builder


def card_frame(point, outward, rng, lean=0.8, spin=None):
    tangent = skyward - outward * skyward.dot(outward)
    if tangent.length < 1e-3:
        tangent = kit.any_perpendicular(outward)
    tangent.normalize()
    angle = rng.uniform(-0.9, 0.9) if spin is None else spin
    tangent = Matrix.Rotation(angle, 3, outward) @ tangent
    forward = (outward * (1.0 - lean) + tangent * lean).normalized()
    right = forward.cross(outward)
    if right.length < 1e-4:
        right = kit.any_perpendicular(forward)
    right.normalize()
    up = right.cross(forward).normalized()
    return forward, right, up


def patch_frame(point, outward, rng):
    tangent = kit.any_perpendicular(outward)
    tangent = Matrix.Rotation(rng.uniform(0.0, math.tau), 3, outward) @ tangent
    right = tangent.cross(outward).normalized()
    return tangent, right, outward
