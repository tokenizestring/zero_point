import math
import numpy

import ground_kit as kit

tau = math.tau


def pick(rng, tone, groups):
    weights = numpy.stack([low + (high - low) * tone for low, high, colors in groups], axis=1)
    weights = numpy.cumsum(weights / weights.sum(axis=1, keepdims=True), axis=1)
    which = numpy.minimum((rng.random((len(tone), 1)) > weights).sum(axis=1), len(groups) - 1)
    result = numpy.zeros((len(tone), 3), dtype=numpy.float32)
    for index, (low, high, colors) in enumerate(groups):
        mask = which == index
        result[mask] = kit.choose(rng, [kit.rgb(*color) for color in colors], int(mask.sum()))
    return result


def lift(track, level):
    return numpy.concatenate([track, numpy.broadcast_to(numpy.asarray(level, dtype=numpy.float32), track.shape[:2])[..., None]], axis=-1).astype(numpy.float32)


def shades(colors, profile):
    return colors[:, None, :] * numpy.asarray(profile, dtype=numpy.float32)[None, :, None]


def swatch(rng, colors, count, value=0.12, hue=0.04):
    return kit.vary(rng, kit.choose(rng, [kit.rgb(*color) for color in colors], count), value, hue)


def bark(tile, name, lichen=(128, 134, 108), amount=0.3):
    shader = kit.graph(name)
    place = shader.attribute("loc")
    grain = shader.noise(place * (90.0, 700.0, 700.0), 1.0, 3.0, 0.65)
    blotch = shader.step(0.56, 0.74, shader.noise(place, 70.0, 3.0, 0.6))
    albedo = shader.mix(shader.attribute("col") * (grain * 0.7 + 0.65), kit.rgb(*lichen), blotch * amount)
    tile.materials[name] = shader.finish(albedo, shader.attribute("prm").x, shader.bump(grain, 0.6, 0.0006))


def chip(tile, name):
    shader = kit.graph(name)
    place = shader.attribute("loc")
    layer = shader.noise(place * (40.0, 260.0, 900.0), 1.0, 3.0, 0.7)
    crack = shader.step(0.6, 0.7, shader.noise(place, 420.0, 2.0, 0.5))
    albedo = shader.attribute("col") * (layer * 0.9 + 0.55)
    tile.materials[name] = shader.finish(shader.mix(albedo, albedo * 0.45, crack), shader.attribute("prm").x, shader.bump(layer - crack * 0.5, 0.9, 0.0008))


def rock(tile, name, grain=420.0):
    shader = kit.graph(name)
    place = shader.local() * shader.attribute("scl", True) + shader.attribute("ofs", True)
    var = shader.attribute("var", True)
    cell = shader.voronoi(place, grain, color=True)
    broad = shader.noise(place, 45.0, 3.0, 0.6)
    fleck = shader.noise(place, 1100.0, 2.0, 0.5)
    albedo = shader.attribute("tint", True) * shader.attribute("col") * ((cell.x - 0.5) * var.y * 1.6 + (broad - 0.5) * 0.35 + (fleck - 0.5) * 0.2 + 1.0)
    albedo = shader.mix(albedo, albedo * 0.3, shader.step(0.86, 0.9, cell.y) * var.y * 2.0)
    albedo = shader.mix(albedo, kit.rgb(205, 198, 188), shader.step(0.8, 0.86, cell.z) * var.y * 1.5)
    albedo = shader.mix(albedo, albedo * 0.6, shader.step(0.45, 0.55, shader.noise(place * (1.0, 1.0, 6.0), 60.0, 2.0, 0.5)) * var.z)
    tile.materials[name] = shader.finish(albedo, var.x + (fleck - 0.5) * 0.1, shader.bump(fleck * 0.6 + cell.x * 0.4, 0.5, 0.0002))


def sticks(tile, floor, count, low, high, power, thin, colors, material, forks=1.5, sides=6, steep=0.18, bend=0.5, wobble=(0.03, 0.14), field=None, rough=0.9, surface=None, loft=0.002):
    rng = tile.rng
    spot = kit.scatter(rng, count, tile.size, field)
    reach = low + (high - low) * rng.random(count) ** power
    track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), reach, 18, rng.normal(0.0, bend, count), rng.uniform(wobble[0], wobble[1], count), 2.2)
    profile = numpy.linspace(1.0, 0.45, 18)[None, :] * (reach * rng.uniform(thin[0], thin[1], count))[:, None] * (1.0 + 0.08 * rng.normal(0.0, 1.0, (count, 18)))
    settle = (lambda path, girth: floor.rest(rng, path, girth, rigid=True, batch=6, steep=steep)) if surface is None else (lambda path, girth: kit.sample(surface, path[..., 0], path[..., 1], tile.size) + rng.random((len(path), 1)) * loft - girth * 0.3)
    level = settle(track, profile)
    color = swatch(rng, colors, count)
    tile.tubes(material, lift(track, level + profile), profile, sides, color, rough, cap=True)
    parent = rng.integers(0, count, int(count * forks))
    parent = parent[reach[parent] > low * 1.4]
    node = (rng.uniform(0.2, 0.85, len(parent)) * 17).astype(numpy.int64)
    way = track[parent, node + 1] - track[parent, node]
    turn = numpy.arctan2(way[:, 1], way[:, 0]) + rng.choice([-1.0, 1.0], len(parent)) * rng.uniform(0.45, 1.0, len(parent))
    branch = kit.paths(rng, track[parent, node], turn, reach[parent] * rng.uniform(0.2, 0.5, len(parent)), 10, rng.normal(0.0, bend * 0.8, len(parent)), rng.uniform(wobble[0], wobble[1], len(parent)), 2.0, anchor=0.0)
    slim = profile[parent, node][:, None] * numpy.linspace(0.65, 0.3, 10)[None, :]
    own = settle(branch, slim) + slim
    join = kit.smoothstep(0.0, 0.45, numpy.linspace(0.0, 1.0, 10))[None, :]
    tile.tubes(material, lift(branch, (level[parent, node] + profile[parent, node])[:, None] * (1.0 - join) + own * join), slim, max(3, sides - 1), color[parent], rough, cap=True)


def carpet(tile, floor, mask, layers, points=7, material="moss", power=1.5, rough=0.92, rise=0.5, droop=0.2, inner=0.42):
    rng = tile.rng
    for amount, low, high, lift_by, colors in layers:
        count = int(mask.mean() * tile.size * tile.size / amount)
        spot = kit.scatter(rng, count, tile.size, mask ** power)
        base = floor.at(spot[:, 0], spot[:, 1])
        tile.stars(material, numpy.column_stack([spot, base + 0.001 + lift_by]), rng.uniform(low, high, count), points, rise, droop, inner, swatch(rng, colors, count, 0.12, 0.05), None, rough)


def loam(tile, name, dry=(128, 104, 82), damp=(60, 46, 36), grain=700.0):
    shader = kit.graph(name)
    place = shader.local() * shader.attribute("scl", True) + shader.attribute("ofs", True)
    coarse = shader.noise(place, 70.0, 3.0, 0.6)
    fine = shader.noise(place, grain, 2.0, 0.6)
    speck = shader.step(0.72, 0.8, shader.noise(place, 1500.0, 1.0, 0.5))
    dryness = shader.step(0.35, 1.0, shader.facing().z * 0.65 + coarse * 0.6)
    albedo = shader.attribute("tint", True) * shader.mix(kit.rgb(*damp), kit.rgb(*dry), dryness) * (fine * 0.5 + 0.75)
    albedo = shader.mix(albedo, kit.rgb(150, 136, 120), speck * 0.35)
    tile.materials[name] = shader.finish(albedo, shader.lerp(0.86, 0.97, dryness), shader.bump(fine * 0.6 + coarse * 0.4, 0.8, 0.0007))


def straw(tile, name, rot=(92, 74, 52), amount=0.35):
    shader = kit.graph(name)
    place = shader.attribute("loc")
    streak = shader.noise(place * (25.0, 1600.0, 1600.0), 1.0, 2.0, 0.6)
    blotch = shader.step(0.58, 0.8, shader.noise(place, 55.0, 3.0, 0.6))
    albedo = shader.mix(shader.attribute("col") * (streak * 0.3 + 0.85), kit.rgb(*rot), blotch * amount)
    tile.materials[name] = shader.finish(albedo, shader.attribute("prm").x + blotch * 0.15, shader.bump(streak, 0.5, 0.0002))


def cone(seed):
    rng = numpy.random.default_rng(seed)
    count = int(rng.integers(64, 90))
    t = (numpy.arange(count) + 0.5) / count
    turn = numpy.arange(count) * 2.39996 + rng.uniform(0.0, tau)
    peak = rng.uniform(0.32, 0.42)
    girth = rng.uniform(0.27, 0.33)
    body = girth * numpy.sqrt(numpy.maximum(1.0 - numpy.where(t > peak, (t - peak) / (1.0 - peak), (peak - t) / (peak + 0.04)) ** 2, 0.0))
    core = body * 0.4 + 0.015
    flare = rng.uniform(0.85, 1.25) * (0.55 + 0.45 * numpy.sin(math.pi * numpy.minimum(t * 1.4, 1.0)))
    radial = numpy.stack([numpy.zeros(count), numpy.cos(turn), numpy.sin(turn)], axis=1)
    axis = numpy.array([1.0, 0.0, 0.0])
    direction = axis[None, :] * numpy.cos(flare)[:, None] + radial * numpy.sin(flare)[:, None]
    start = numpy.stack([t - 0.5, core * numpy.cos(turn), core * numpy.sin(turn)], axis=1)
    reach = (body - core) / numpy.maximum(numpy.sin(flare), 0.3) + 0.04
    steps = numpy.array([0.0, 0.4, 0.8, 1.0])
    spine = start[:, None, :] + direction[:, None, :] * (reach[:, None] * steps[None, :])[..., None]
    width = (body * 0.52 + 0.026)[:, None] * numpy.array([0.4, 0.85, 1.0, 0.8])[None, :]
    thick = numpy.array([0.012, 0.016, 0.03, 0.036])[None, :] * rng.uniform(0.8, 1.2, (count, 1))
    points, quads, across, along = kit.sweep(spine, width, 6, thick / width, numpy.broadcast_to(numpy.cross(axis[None, :], radial)[:, None, :], spine.shape).astype(numpy.float32))
    shell = points.reshape(-1, 3)
    tips = (spine[:, -1, :] + direction * 0.018).astype(numpy.float32)
    ball, ball_faces = kit.icosphere(2)
    heart = ball * numpy.array([0.46, core.max() * 1.1, core.max() * 1.1], dtype=numpy.float32)
    vertices = numpy.concatenate([shell, tips, heart])
    ring = numpy.arange(6)
    last = (numpy.arange(count) * 24 + 18)[:, None]
    caps = numpy.stack([numpy.broadcast_to((len(shell) + numpy.arange(count))[:, None], (count, 6)), last + ring, last + (ring + 1) % 6], axis=-1).reshape(-1, 3)
    faces = {3: numpy.concatenate([caps, ball_faces + len(shell) + count]), 4: (quads[None, :, :] + (numpy.arange(count) * 24)[:, None, None]).reshape(-1, 4)}
    tone = rng.uniform(0.8, 1.2, (count, 1, 1))
    ramp = numpy.array([[0.2, 0.18, 0.16], [0.42, 0.38, 0.34], [0.8, 0.78, 0.76], [1.3, 1.38, 1.46]])
    col = numpy.concatenate([numpy.broadcast_to((ramp[None, :, :] * tone)[:, :, None, :], (count, 4, 6, 3)).reshape(-1, 3), numpy.full((count, 3), 0.55), numpy.full((len(heart), 3), 0.2)]).astype(numpy.float32)
    return vertices, faces, col


def needles(tile):
    rng = tile.rng
    size = tile.size
    n = tile.field
    seed = tile.seed
    moss = kit.smoothstep(1.05, 1.5, kit.warp(kit.noise(n, seed + 3, 3.0, 3.0, 16.0), seed + 4, 0.025)) * kit.smoothstep(-0.7, 0.4, kit.noise(n, seed + 13, 3.0, 1.0, 5.0))
    bare = kit.smoothstep(1.25, 1.9, kit.warp(kit.noise(n, seed + 5, 3.0, 3.0, 12.0), seed + 12, 0.04)) * (1.0 - moss)
    tone = kit.unit(kit.noise(n, seed + 6, 2.8, 1.5, 10.0))
    tile.height = kit.noise(n, seed + 1, 3.4, 1.0, 12.0) * 0.007 + kit.noise(n, seed + 2, 2.6, 10.0, 80.0) * 0.0018
    fine = kit.unit(kit.noise(n, seed + 7, 1.2, 40.0))
    mottle = kit.unit(kit.noise(n, seed + 8, 2.4, 4.0, 60.0))
    albedo = kit.tint(kit.rgb(44, 34, 26), kit.rgb(82, 64, 46), fine * 0.55 + mottle * 0.45)
    albedo = kit.tint(albedo, kit.rgb(136, 112, 86), kit.smoothstep(0.9, 0.98, kit.unit(kit.noise(n, seed + 9, 0.4, 120.0))) * 0.6)
    tile.soil("humus", albedo, 0.97 - 0.07 * fine, kit.noise(n, seed + 10, 1.4, 80.0) * 0.3)
    tile.ground("humus")
    tile.plain("needle", 500.0, 0.1)
    tile.plain("crumb", 300.0, 0.15)
    tile.plain("moss", 600.0, 0.12)
    tile.plain("cone", 260.0, 0.18, instanced=True)
    bark(tile, "bark")
    chip(tile, "flake")
    floor = kit.bed(tile.height, size, 1024)
    cover = numpy.clip(1.0 - 0.92 * bare, 0.08, 1.0)
    veil = cover * (1.0 - 0.8 * moss)
    fresh = [(0.5, 0.22, [(128, 80, 50), (142, 92, 58), (112, 72, 46), (134, 86, 56)]), (0.2, 0.25, [(160, 112, 70), (172, 128, 82), (152, 106, 66)]), (0.1, 0.36, [(190, 165, 120), (176, 152, 110), (200, 180, 138), (184, 160, 124)]), (0.15, 0.16, [(150, 140, 125), (128, 118, 104), (138, 126, 108), (160, 148, 128)]), (0.1, 0.03, [(74, 56, 42), (62, 50, 40), (88, 64, 46)]), (0.01, 0.015, [(96, 108, 58), (110, 118, 64)])]
    stale = [(0.7, 0.6, [(66, 52, 40), (54, 44, 35), (82, 62, 44), (96, 74, 54)]), (0.2, 0.25, [(110, 100, 88), (96, 86, 74)]), (0.1, 0.15, [(120, 82, 54), (104, 70, 46)])]
    shapes = [cone(seed + 100 + index) for index in range(6)]
    for vertices, faces, col in shapes:
        tile.variant("cone", vertices, faces, "cone", col)
    extent = numpy.asarray(tile.extents["cone"], dtype=numpy.float64)

    def shade_at(spot):
        return kit.sample(tone, spot[:, 0], spot[:, 1], size)

    def pine(count, pairs, depth, field, surface):
        spot = kit.scatter(rng, count, size, field)
        heading = rng.uniform(0.0, tau, count)
        reach = rng.uniform(0.045, 0.105, count)
        fork = rng.uniform(0.03, 0.4, count)
        color = kit.vary(rng, pick(rng, shade_at(spot), fresh), 0.1, 0.03)
        girth = rng.uniform(0.85, 1.15, (count, 1)) * 0.00095
        rank = rng.random((count, 1))
        for sign in ((-0.5, 0.5) if pairs else (0.0,)):
            track = kit.paths(rng, spot, heading + fork * sign, reach * rng.uniform(0.9, 1.0, count), 5, rng.normal(0.0, 0.22, count), anchor=0.0)
            level = floor.slab(rng, track, depth, field, surface, 0.03, rank, -1.0)
            tile.tubes("needle", lift(track, level + 0.001), numpy.array([1.0, 1.0, 0.95, 0.8, 0.3])[None, :] * girth, 3, shades(kit.vary(rng, color, 0.05, 0.02), [0.7, 0.95, 1.0, 1.0, 0.85]), rng.uniform(0.6, 0.8, count))
        if pairs:
            stub = kit.paths(rng, spot, heading, 0.0055, 2, anchor=0.25)
            tile.tubes("needle", lift(stub, level[:, 0:1] + 0.0011), 0.00125, 4, swatch(rng, [(64, 50, 40), (52, 42, 36), (80, 62, 48)], count), 0.85)

    def fir(count, depth, field, surface):
        spot = kit.scatter(rng, count, size, field)
        track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), rng.uniform(0.013, 0.03, count), 4, rng.normal(0.0, 0.15, count))
        level = floor.slab(rng, track, depth, field, surface, 0.08)
        color = kit.vary(rng, pick(rng, shade_at(spot), fresh), 0.1, 0.03)
        tile.ribbons("needle", lift(track, level + 0.0004), numpy.array([0.75, 1.0, 1.0, 0.7])[None, :] * rng.uniform(0.0008, 0.0011, (count, 1)), 3, shades(color, [0.85, 1.0, 1.0, 0.9]), rng.uniform(0.55, 0.8, count), fold=-0.3, shade=0.12)

    def twigs(count):
        spot = kit.scatter(rng, count, size)
        reach = 0.05 + 0.22 * rng.random(count) ** 2.2
        track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), reach, 18, rng.normal(0.0, 0.5, count), rng.uniform(0.03, 0.14, count), 2.2)
        profile = numpy.linspace(1.0, 0.45, 18)[None, :] * (reach * rng.uniform(0.013, 0.024, count))[:, None] * (1.0 + 0.08 * rng.normal(0.0, 1.0, (count, 18)))
        level = floor.rest(rng, track, profile, rigid=True, batch=6)
        color = swatch(rng, [(92, 76, 62), (110, 92, 74), (74, 60, 50), (124, 108, 92), (84, 64, 48)], count)
        tile.tubes("bark", lift(track, level + profile), profile, 6, color, 0.9, cap=True)
        parent = rng.integers(0, count, int(count * 1.5))
        parent = parent[reach[parent] > 0.07]
        node = (rng.uniform(0.25, 0.85, len(parent)) * 17).astype(numpy.int64)
        way = track[parent, node + 1] - track[parent, node]
        turn = numpy.arctan2(way[:, 1], way[:, 0]) + rng.choice([-1.0, 1.0], len(parent)) * rng.uniform(0.5, 1.1, len(parent))
        branch = kit.paths(rng, track[parent, node], turn, reach[parent] * rng.uniform(0.2, 0.45, len(parent)), 10, rng.normal(0.0, 0.4, len(parent)), rng.uniform(0.03, 0.1, len(parent)), 2.0, anchor=0.0)
        slim = profile[parent, node][:, None] * numpy.linspace(0.6, 0.25, 10)[None, :]
        own = floor.rest(rng, branch, slim, rigid=True, batch=6) + slim
        join = kit.smoothstep(0.0, 0.45, numpy.linspace(0.0, 1.0, 10))[None, :]
        tile.tubes("bark", lift(branch, (level[parent, node] + profile[parent, node])[:, None] * (1.0 - join) + own * join), slim, 5, color[parent], 0.9, cap=True)

    def flakes(count):
        spot = kit.scatter(rng, count, size)
        span = 0.003 + 0.013 * rng.random(count) ** 2.4
        thick = span * rng.uniform(0.1, 0.26, count) + 0.0006
        ring = numpy.arange(7) * (tau / 6.0)
        reach = numpy.where(numpy.arange(7) < 6, 0.7, 0.0)[None, :] * span[:, None]
        around_x = spot[:, 0:1] + numpy.cos(ring)[None, :] * reach
        around_y = spot[:, 1:2] + numpy.sin(ring)[None, :] * reach
        base = floor.at(around_x, around_y).max(axis=1)
        color = swatch(rng, [(98, 80, 66), (120, 78, 56), (92, 72, 60), (110, 86, 64), (130, 94, 68), (84, 68, 56)], count)
        tile.plates("flake", numpy.column_stack([spot, base]), span, thick, color, 0.9, 3, 20, 0.28, tilt=0.12, edge=color * 1.35, bend=0.2, corners=6)
        floor.lift(around_x, around_y, (base + thick)[:, None])

    def scales(count):
        spot = kit.scatter(rng, count, size)
        track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), rng.uniform(0.009, 0.016, count), 4)
        half = numpy.array([0.35, 0.8, 1.0, 0.7])[None, :] * rng.uniform(0.0035, 0.006, (count, 1))
        level = floor.rest(rng, track, 0.0008, rigid=True, half=half, batch=30)
        color = swatch(rng, [(112, 80, 54), (96, 68, 48), (128, 96, 68)], count)
        tile.tubes("bark", lift(track, level + 0.001), half, 6, shades(color, [0.55, 0.8, 1.0, 1.25]), 0.85, 0.2, cap=True)

    def cones(count):
        spot = kit.scatter(rng, count, size)
        scale = rng.uniform(0.028, 0.046, count)
        which = rng.integers(0, len(shapes), count)
        euler = numpy.column_stack([rng.uniform(0.0, tau, count), rng.normal(0.0, 0.15, count), rng.uniform(0.0, tau, count)])
        where, turned = floor.drop(rng, spot, extent[which] * scale[:, None] * 0.85, euler, 3, 0.5, 0.12, 0.5)
        tile.marks.setdefault("cone", []).extend(where[:, :2].tolist())
        tile.place("cone", where, turned, scale, which, swatch(rng, [(118, 84, 56), (100, 74, 52), (134, 100, 70), (92, 70, 54)], count, 0.1, 0.03), numpy.column_stack([rng.uniform(0.8, 0.92, count), rng.random(count), numpy.zeros(count)]))

    count = 38000
    spot = kit.scatter(rng, count, size, 0.35 + bare)
    girth = rng.uniform(0.0008, 0.0026, count) * rng.uniform(0.6, 1.4, count)
    base = floor.at(spot[:, 0], spot[:, 1])
    tile.grit("crumb", numpy.column_stack([spot, base + girth * 0.5]), girth[:, None] * rng.uniform(0.6, 1.3, (count, 3)), swatch(rng, [(40, 30, 23), (58, 44, 32), (82, 64, 46), (26, 20, 16)], count, 0.15), 0.95, 0)
    floor.lift(spot[:, 0], spot[:, 1], base + girth)
    count = 110000
    spot = kit.scatter(rng, count, size, cover)
    track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), rng.uniform(0.005, 0.022, count), 2)
    level = floor.slab(rng, track, 0.003, cover, None, 0.06)
    tile.tubes("needle", lift(track, level + 0.0006), 0.00065, 3, kit.vary(rng, pick(rng, shade_at(spot), stale), 0.18, 0.05), 0.85)
    floor.swell(cover * 0.003)
    tile.marks["moss"] = [(((numpy.argmax(moss) % n) + 0.5) * size / n, ((numpy.argmax(moss) // n) + 0.5) * size / n)]
    tile.note("base litter laid")
    for share, depth, field, part in ((0.4, 0.006, cover, 0.2), (0.4, 0.006, veil, 0.35), (0.2, 0.003, veil, 0.45)):
        surface = floor.mat(0.012)
        pine(int(42000 * share), True, depth, field, surface)
        pine(int(24000 * share), False, depth, field, surface)
        fir(int(60000 * share), depth, field, surface)
        floor.swell(field * depth)
        if field is cover:
            floor.swell(kit.blur(moss, n * 0.004) * 0.008)
            for amount, low, high, rise, colors in ((0.000022, 0.0035, 0.006, 0.0, [(56, 72, 32), (66, 82, 36), (48, 62, 28), (74, 84, 40)]), (0.000011, 0.0024, 0.0044, 0.0018, [(92, 106, 48), (108, 118, 54), (82, 96, 44), (126, 126, 64), (116, 102, 58)])):
                count = int(moss.mean() * size * size / amount)
                spot = kit.scatter(rng, count, size, moss ** 1.5)
                base = floor.at(spot[:, 0], spot[:, 1])
                tile.stars("moss", numpy.column_stack([spot, base + 0.001 + rise]), rng.uniform(low, high, count), 7, 0.5, 0.2, 0.42, swatch(rng, colors, count, 0.12, 0.05), None, 0.92)
            floor.swell(moss * 0.004)
        twigs(int(200 * part))
        flakes(int(300 * part))
        cones(int(16 * part) + 1)
        scales(int(420 * part))
        tile.note("litter round laid")


def heath(tile):
    rng = tile.rng
    size = tile.size
    n = tile.field
    seed = tile.seed
    ragged = kit.smoothstep(-0.7, 0.7, kit.noise(n, seed + 13, 1.6, 40.0, 180.0))
    lichen = kit.smoothstep(1.2, 1.6, kit.warp(kit.noise(n, seed + 1, 2.4, 6.0, 30.0), seed + 2, 0.015)) * kit.smoothstep(-0.5, 0.5, kit.noise(n, seed + 3, 3.0, 1.0, 5.0)) * (0.5 + 0.5 * ragged)
    moss = kit.smoothstep(1.35, 1.7, kit.warp(kit.noise(n, seed + 4, 2.6, 5.0, 26.0), seed + 5, 0.015)) * (1.0 - lichen) * (0.55 + 0.45 * ragged)
    gravel = kit.smoothstep(0.6, 1.7, kit.noise(n, seed + 6, 3.0, 1.5, 8.0)) * (1.0 - lichen) * (1.0 - moss)
    tone = kit.unit(kit.noise(n, seed + 7, 2.8, 1.5, 9.0))
    tile.height = kit.noise(n, seed + 8, 3.2, 1.0, 10.0) * 0.006 + kit.noise(n, seed + 9, 2.4, 10.0, 90.0) * 0.0011 + kit.blur(lichen, n * 0.0025) * (0.009 + 0.003 * ragged) + kit.blur(moss, n * 0.003) * 0.008 - kit.blur(gravel, n * 0.004) * 0.004
    fine = kit.unit(kit.noise(n, seed + 10, 1.0, 50.0))
    mottle = kit.unit(kit.noise(n, seed + 11, 2.2, 5.0, 70.0))
    albedo = kit.tint(kit.rgb(52, 42, 35), kit.rgb(90, 72, 58), fine * 0.5 + mottle * 0.5)
    albedo = kit.tint(albedo, kit.rgb(118, 102, 88), gravel * (0.2 + 0.3 * fine))
    albedo = kit.tint(albedo, kit.rgb(66, 64, 52), kit.smoothstep(0.15, 0.6, lichen))
    albedo = kit.tint(albedo, kit.rgb(44, 46, 30), kit.smoothstep(0.15, 0.6, moss))
    tile.soil("peat", albedo, 0.97 - 0.06 * fine, kit.noise(n, seed + 12, 1.2, 70.0) * 0.35)
    tile.ground("peat")
    tile.plain("litter", 500.0, 0.12)
    tile.plain("grit", 500.0, 0.18)
    tile.plain("moss", 600.0, 0.12)
    tile.plain("lichen", 700.0, 0.1)
    tile.plain("clod", 160.0, 0.2, instanced=True)
    bark(tile, "stem", (150, 152, 138), 0.18)
    rock(tile, "stone")
    floor = kit.bed(tile.height, size, 1024)
    cover = numpy.clip(1.0 - 0.9 * kit.smoothstep(0.1, 0.5, lichen + moss) - 0.35 * gravel, 0.06, 1.0)
    foliage = [(0.35, 0.3, [(120, 84, 58), (104, 72, 50), (134, 96, 66)]), (0.35, 0.2, [(78, 60, 46), (64, 50, 40), (90, 70, 54)]), (0.2, 0.3, [(110, 98, 86), (124, 112, 98)]), (0.06, 0.18, [(140, 132, 120), (152, 144, 130)]), (0.04, 0.02, [(48, 40, 34)])]
    debris = [(0.45, 0.4, [(92, 68, 50), (80, 60, 46), (104, 76, 54)]), (0.4, 0.35, [(66, 52, 42), (56, 45, 37), (76, 60, 48)]), (0.1, 0.2, [(108, 96, 84), (120, 108, 94)]), (0.05, 0.05, [(44, 37, 32)])]
    for index in range(8):
        vertices, faces = kit.clod(seed + 80 + index, 3, 0.28)
        tile.variant("clod", vertices, faces, "clod")
    count = 1600
    spot = kit.scatter(rng, count, size, cover)
    scale = (0.002 + 0.007 * rng.random((count, 1)) ** 2.0) * numpy.column_stack([numpy.ones(count), rng.uniform(0.7, 1.0, count), rng.uniform(0.45, 0.75, count)])
    which = rng.integers(0, 8, count)
    where, turned = floor.drop(rng, spot, numpy.asarray(tile.extents["clod"], dtype=numpy.float64)[which] * scale * 0.9, numpy.column_stack([rng.normal(0.0, 0.3, count), rng.normal(0.0, 0.3, count), rng.uniform(0.0, tau, count)]), 1, 0.0, 0.45, 0.3)
    tile.place("clod", where, turned, scale, which, swatch(rng, [(56, 45, 37), (72, 58, 46), (46, 38, 32), (84, 68, 54)], count, 0.12, 0.03), numpy.column_stack([rng.uniform(0.93, 0.98, count), rng.random(count), numpy.zeros(count)]))
    for index in range(8):
        vertices, faces = kit.pebble(seed + 40 + index, 4, 0.16)
        tile.variant("stone", vertices, faces, "stone")
    for index in range(8):
        vertices, faces = kit.shard(seed + 60 + index, 3, 12, 10.0, 0.03)
        tile.variant("stone", vertices, faces, "stone")
    extent = numpy.asarray(tile.extents["stone"], dtype=numpy.float64)
    spot = kit.spaced(rng, 12, size, 0.22)
    count = len(spot)
    scale = rng.uniform(0.01, 0.022, (count, 1)) * numpy.column_stack([numpy.ones(count), rng.uniform(0.6, 0.9, count), rng.uniform(0.4, 0.7, count)])
    which = rng.integers(0, 8, count)
    where, turned = floor.drop(rng, spot, extent[which] * scale * 0.9, numpy.column_stack([rng.normal(0.0, 0.2, count), rng.normal(0.0, 0.2, count), rng.uniform(0.0, tau, count)]), 1, 0.0, 0.4, 0.3)
    tile.marks["quartz"] = where[:, :2].tolist()
    tile.place("stone", where, turned, scale, which, swatch(rng, [(214, 208, 196), (200, 194, 182), (222, 214, 200), (196, 184, 168)], count, 0.05, 0.02), numpy.column_stack([rng.uniform(0.55, 0.7, count), numpy.full(count, 0.06), numpy.zeros(count)]))
    count = 300
    spot = kit.scatter(rng, count, size, 0.12 + gravel)
    scale = rng.uniform(0.0025, 0.007, (count, 1)) * numpy.column_stack([numpy.ones(count), rng.uniform(0.6, 1.0, count), rng.uniform(0.45, 0.8, count)])
    which = rng.integers(8, 16, count)
    where, turned = floor.drop(rng, spot, extent[which] * scale * 0.9, numpy.column_stack([rng.normal(0.0, 0.3, count), rng.normal(0.0, 0.3, count), rng.uniform(0.0, tau, count)]), 2, 1.0, 0.3, 0.4)
    tile.place("stone", where, turned, scale, which, swatch(rng, [(150, 128, 116), (130, 126, 120), (166, 156, 146), (88, 84, 82), (140, 114, 100), (176, 168, 158)], count, 0.1, 0.03), numpy.column_stack([rng.uniform(0.78, 0.9, count), rng.uniform(0.2, 0.4, count), numpy.zeros(count)]))
    count = 46000
    spot = kit.scatter(rng, count, size, 0.2 + gravel)
    girth = rng.uniform(0.0007, 0.0026, count) * rng.uniform(0.6, 1.3, count)
    base = floor.at(spot[:, 0], spot[:, 1])
    tile.grit("grit", numpy.column_stack([spot, base + girth * 0.3]), girth[:, None] * rng.uniform(0.6, 1.2, (count, 3)), swatch(rng, [(144, 122, 110), (126, 122, 116), (160, 152, 142), (90, 86, 84), (134, 110, 96), (180, 174, 164), (108, 94, 82), (120, 100, 88)], count, 0.14, 0.04), 0.85, 0)
    count = 70000
    spot = kit.scatter(rng, count, size, cover)
    girth = rng.uniform(0.0008, 0.003, count) * rng.uniform(0.6, 1.3, count)
    base = floor.at(spot[:, 0], spot[:, 1])
    tile.grit("grit", numpy.column_stack([spot, base + girth * 0.4]), girth[:, None] * rng.uniform(0.6, 1.2, (count, 3)), swatch(rng, [(56, 45, 37), (72, 58, 46), (44, 36, 30), (90, 72, 58)], count, 0.15, 0.04), 0.95, 0)

    def litter(count, depth, surface):
        spot = kit.scatter(rng, count, size, cover)
        spot = spot[floor.at(spot[:, 0], spot[:, 1]) - kit.sample(surface, spot[:, 0], spot[:, 1], size) < 0.0025]
        track = kit.paths(rng, spot, rng.uniform(0.0, tau, len(spot)), rng.uniform(0.002, 0.0055, len(spot)), 2)
        level = floor.slab(rng, track, depth, cover, surface, 0.1)
        tile.tubes("litter", lift(track, level + 0.0005), rng.uniform(0.0004, 0.0007, (len(spot), 1)), 3, kit.vary(rng, pick(rng, kit.sample(tone, spot[:, 0], spot[:, 1], size), debris), 0.15, 0.05), 0.92)
        floor.swell(cover * depth)

    def offshoots(track, reach, amount, keep, low, high, scale, steps):
        parent = numpy.repeat(numpy.arange(len(track)), amount)
        parent = parent[rng.random(len(parent)) < keep]
        node = rng.integers(low, high, len(parent))
        way = track[parent, node + 1] - track[parent, node]
        turn = numpy.arctan2(way[:, 1], way[:, 0]) + rng.choice([-1.0, 1.0], len(parent)) * rng.uniform(0.3, 0.85, len(parent))
        length = reach[parent] * rng.uniform(scale[0], scale[1], len(parent)) * (1.25 - 0.6 * node / track.shape[1])
        return parent, node, kit.paths(rng, track[parent, node], turn, length, steps, rng.normal(0.0, 0.6, len(parent)), anchor=0.0), length

    def sprigs(count, surface):
        spot = kit.scatter(rng, count, size, cover)
        reach = rng.uniform(0.05, 0.14, count)
        track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), reach, 12, rng.normal(0.0, 0.6, count), rng.uniform(0.05, 0.18, count), 1.6)
        girth = numpy.linspace(1.0, 0.5, 12)[None, :] * rng.uniform(0.0008, 0.0014, (count, 1))
        level = kit.sample(surface, track[..., 0], track[..., 1], size) + rng.random((count, 1)) * 0.002 + girth * 0.7
        tile.tubes("stem", lift(track, level), girth, 4, swatch(rng, [(124, 112, 100), (98, 82, 70), (142, 134, 122), (80, 66, 56)], count), 0.9)
        parent, node, shoot, length = offshoots(track, reach, 10, 0.7, 2, 11, (0.15, 0.4), 6)
        knob = rng.uniform(0.0008, 0.0013, (len(parent), 1)) * (1.0 + 0.3 * rng.normal(0.0, 1.0, (len(parent), 6))) * numpy.array([0.7, 1.0, 1.0, 1.0, 0.9, 0.5])[None, :]
        height = level[parent, node][:, None] + numpy.linspace(0.0, 1.0, 6)[None, :] * rng.normal(0.0005, 0.0012, (len(parent), 1)) + knob * 0.5
        color = kit.vary(rng, pick(rng, kit.sample(tone, shoot[:, 0, 0], shoot[:, 0, 1], size), foliage), 0.12, 0.04)
        tile.tubes("litter", lift(shoot, height), knob, 4, color, 0.9)
        child, joint, twiglet, reach_of = offshoots(shoot, length, 2, 0.6, 1, 5, (0.3, 0.6), 4)
        slim = knob[child][:, :4] * 0.8
        tile.tubes("litter", lift(twiglet, height[child, joint][:, None] + slim * 0.3), slim, 3, color[child], 0.9)
        bloom = numpy.nonzero(rng.random(len(parent)) < 0.4)[0]
        center = numpy.concatenate([shoot[bloom][:, 2:6, :], (height[bloom][:, 2:6] + knob[bloom][:, 2:6] * 0.8)[..., None]], axis=-1).reshape(-1, 3)
        center[:, :2] += rng.normal(0.0, 0.0008, (len(center), 2))
        tile.grit("litter", center, rng.uniform(0.0009, 0.0015, len(center)), swatch(rng, [(150, 128, 112), (166, 146, 126), (128, 104, 98), (176, 160, 140)], len(center), 0.1, 0.04), 0.9, 0)

    litter(250000, 0.004, floor.mat(0.008))
    tile.note("litter laid")
    surface = floor.mat(0.006)
    sticks(tile, floor, 850, 0.035, 0.26, 1.8, (0.008, 0.015), [(150, 142, 130), (132, 124, 112), (110, 98, 86), (84, 70, 60), (164, 156, 144), (96, 80, 66)], "stem", 2.2, 5, 0.15, 0.8, (0.08, 0.3), surface=surface, loft=0.004)
    sprigs(480, surface)
    litter(50000, 0.002, surface)
    tile.note("stems laid")
    carpet(tile, floor, lichen, ((0.000009, 0.002, 0.0036, 0.0, [(112, 114, 96), (98, 100, 84), (126, 128, 108)]), (0.000006, 0.0014, 0.003, 0.0014, [(186, 190, 168), (200, 202, 180), (170, 176, 152), (192, 190, 160), (206, 206, 190), (150, 152, 130)])), 5, "lichen", 1.2, 0.95, 0.9, 0.5, 0.35)
    carpet(tile, floor, moss, ((0.000022, 0.0035, 0.006, 0.0, [(58, 64, 34), (70, 74, 40), (50, 54, 30), (80, 78, 44)]), (0.000011, 0.0024, 0.0044, 0.0018, [(84, 90, 48), (100, 102, 56), (76, 84, 44), (112, 106, 60), (96, 84, 50)])))
    count = 1800
    spot = kit.scatter(rng, count, size, cover)
    tile.stars("lichen", numpy.column_stack([spot, floor.at(spot[:, 0], spot[:, 1]) + 0.001]), rng.uniform(0.0012, 0.0026, count), 5, 0.9, 0.5, 0.35, swatch(rng, [(186, 190, 168), (170, 176, 152), (200, 202, 180)], count, 0.1, 0.04), None, 0.95)
    tile.marks["lichen"] = [(((numpy.argmax(lichen) % n) + 0.5) * size / n, ((numpy.argmax(lichen) // n) + 0.5) * size / n)]


def moor(tile):
    rng = tile.rng
    size = tile.size
    n = tile.field
    seed = tile.seed
    near, far, ident = kit.worley(n, 7, seed + 1, 0.9)
    mound = kit.smoothstep(0.72, 0.08, near) ** 1.5 * kit.smoothstep(0.0, 0.3, far - near) * rng.uniform(0.35, 1.0, 49)[ident] * (0.8 + 0.2 * kit.noise(n, seed + 2, 2.4, 6.0, 40.0))
    sphagnum = kit.smoothstep(1.0, 1.4, kit.warp(kit.noise(n, seed + 3, 2.8, 3.0, 14.0), seed + 4, 0.02)) * (1.0 - kit.smoothstep(0.1, 0.5, mound))
    gaps = kit.smoothstep(0.75, 1.3, kit.warp(kit.noise(n, seed + 5, 2.6, 3.0, 16.0), seed + 6, 0.02)) * (1.0 - kit.smoothstep(0.1, 0.5, mound)) * (1.0 - sphagnum)
    tone = kit.unit(kit.noise(n, seed + 7, 2.8, 1.5, 9.0))
    tile.height = kit.noise(n, seed + 8, 3.2, 1.0, 6.0) * 0.008 + mound * 0.036 + kit.blur(sphagnum, n * 0.004) * 0.016 - kit.blur(gaps, n * 0.004) * 0.012
    fine = kit.unit(kit.noise(n, seed + 9, 1.0, 50.0))
    albedo = kit.tint(kit.rgb(36, 29, 25), kit.rgb(62, 50, 40), fine)
    albedo = kit.tint(albedo, kit.rgb(28, 23, 20), kit.smoothstep(0.3, 0.9, gaps))
    albedo = kit.tint(albedo, kit.rgb(70, 78, 40), kit.smoothstep(0.15, 0.6, sphagnum))
    tile.soil("peat", albedo, numpy.clip(0.78 - 0.55 * kit.smoothstep(0.2, 0.8, gaps) + 0.12 * (fine - 0.5), 0.18, 1.0), kit.noise(n, seed + 10, 1.2, 70.0) * 0.3 * (1.0 - 0.8 * gaps))
    tile.ground("peat")
    straw(tile, "thatch")
    tile.plain("blade", 700.0, 0.1, (0.05, 1.0, 1.0))
    tile.plain("sphagnum", 500.0, 0.12)
    floor = kit.bed(tile.height, size, 1024)
    cover = numpy.clip(1.0 - 0.95 * gaps - 0.9 * sphagnum, 0.03, 1.0) * (0.65 + 0.35 * kit.smoothstep(0.0, 0.5, mound))
    small = kit.resize(mound, 512)
    angle = kit.noise(512, seed + 11, 3.6, 1.0, 3.5) * 2.6
    mx, my = kit.slopes(kit.blur(small, 4.0), size)
    swirl = numpy.stack([numpy.cos(angle), numpy.sin(angle)], axis=-1)
    fall = numpy.stack([-mx, -my], axis=-1) / numpy.maximum(numpy.hypot(mx, my), 1e-6)[..., None]
    pull = kit.smoothstep(0.25, 0.75, small)[..., None]
    flow = swirl * (1.0 - pull) + fall * pull * 1.2
    flow = (flow / numpy.maximum(numpy.linalg.norm(flow, axis=-1, keepdims=True), 1e-6)).astype(numpy.float32)
    dry = [(0.35, 0.2, [(196, 170, 110), (184, 158, 104), (204, 180, 124)]), (0.3, 0.45, [(214, 196, 150), (226, 214, 180), (206, 190, 148)]), (0.2, 0.25, [(180, 172, 150), (196, 186, 160)]), (0.15, 0.1, [(150, 130, 96), (136, 116, 86)])]
    old = [(0.5, 0.4, [(150, 132, 100), (128, 110, 84), (140, 120, 90)]), (0.3, 0.4, [(168, 150, 116), (156, 142, 112)]), (0.2, 0.2, [(110, 98, 80), (96, 84, 68)])]

    def thatch(count, low, high, depth, field, palette, wide):
        start = kit.scatter(rng, count, size, field)
        track = kit.streams(rng, start, flow, size, rng.uniform(low, high, count), 14, 0.35, 0.05)
        level = floor.slab(rng, track, depth, field, floor.mat(0.02), 0.05)
        t = numpy.linspace(0.0, 1.0, 14)
        width = numpy.interp(t, [0.0, 0.2, 0.7, 1.0], [0.6, 1.0, 0.75, 0.12])[None, :] * rng.uniform(wide[0], wide[1], (count, 1))
        color = kit.vary(rng, pick(rng, kit.sample(tone, start[:, 0], start[:, 1], size), palette), 0.1, 0.03)
        twist = rng.normal(0.0, 0.5, (count, 1)) * (t[None, :] - 0.3) + rng.normal(0.0, 0.25, (count, 1))
        tile.ribbons("thatch", lift(track, level + 0.0006), width, 3, shades(color, numpy.interp(t, [0.0, 0.25, 1.0], [0.72, 1.0, 1.08])), rng.uniform(0.58, 0.78, count), fold=rng.uniform(0.1, 0.45, count), twist=twist, shade=0.1)
        floor.swell(field * depth)

    thatch(50000, 0.03, 0.1, 0.006, cover, old, (0.001, 0.002))
    tile.note("underlayer laid")
    carpet(tile, floor, sphagnum, ((0.00004, 0.0045, 0.0075, 0.0, [(104, 116, 52), (120, 128, 58), (92, 100, 46)]), (0.00002, 0.003, 0.0055, 0.002, [(150, 168, 72), (170, 176, 84), (186, 170, 84), (196, 186, 100), (150, 72, 60), (164, 150, 70)])), 10, "sphagnum", 1.3, 0.68, 0.55, 0.2, 0.55)
    thatch(46000, 0.14, 0.38, 0.016, cover, dry, (0.0012, 0.0026))
    tile.note("thatch laid")
    thatch(9000, 0.08, 0.22, 0.012, kit.smoothstep(0.3, 0.8, mound) + 0.001, dry, (0.0011, 0.0022))
    taper = numpy.array([0.8, 1.0, 0.9, 0.7, 0.45, 0.1])[None, :]
    count = 40000
    spot = kit.scatter(rng, count, size, (0.4 + mound) * (1.0 - 0.9 * gaps) * (1.0 - 0.6 * sphagnum))
    base = numpy.column_stack([spot, floor.at(spot[:, 0], spot[:, 1]) - 0.006])
    spine, side = kit.upright(base, rng.uniform(0.0, tau, count), rng.uniform(0.03, 0.075, count), 6, numpy.clip(rng.normal(1.1, 0.2, count), 0.5, 1.45), rng.uniform(-0.1, 0.3, count))
    green = swatch(rng, [(108, 138, 62), (122, 146, 70), (96, 126, 56), (132, 150, 76)], count, 0.1, 0.04)
    ramp = numpy.array([[1.4, 1.2, 1.3], [1.12, 1.06, 1.1], [1.0, 1.0, 1.0], [0.95, 0.97, 0.95], [0.98, 0.95, 0.9], [1.15, 0.95, 0.8]])
    tile.ribbons("blade", spine, taper * rng.uniform(0.0009, 0.0016, (count, 1)), 3, green[:, None, :] * ramp[None, :, :], rng.uniform(0.42, 0.58, count), side, 0.5, shade=0.15)
    tile.marks["tussock"] = [(((numpy.argmax(mound) % n) + 0.5) * size / n, ((numpy.argmax(mound) // n) + 0.5) * size / n)]
    tile.marks["sphagnum"] = [(((numpy.argmax(sphagnum) % n) + 0.5) * size / n, ((numpy.argmax(sphagnum) // n) + 0.5) * size / n)]


def turf(tile):
    rng = tile.rng
    size = tile.size
    n = tile.field
    seed = tile.seed
    bare = kit.smoothstep(1.35, 1.9, kit.warp(kit.noise(n, seed + 1, 2.6, 3.0, 18.0), seed + 2, 0.02))
    moss = kit.smoothstep(1.15, 1.6, kit.warp(kit.noise(n, seed + 3, 2.6, 3.0, 16.0), seed + 4, 0.02)) * (1.0 - bare)
    clover = kit.smoothstep(0.7, 1.5, kit.warp(kit.noise(n, seed + 5, 2.8, 2.0, 9.0), seed + 6, 0.03)) * (1.0 - bare) * (1.0 - moss)
    tone = kit.unit(kit.noise(n, seed + 7, 2.8, 1.5, 8.0))
    lush = kit.unit(kit.noise(n, seed + 8, 3.0, 1.0, 6.0))
    tile.height = kit.noise(n, seed + 9, 3.2, 1.0, 8.0) * 0.006 + kit.noise(n, seed + 10, 2.4, 10.0, 80.0) * 0.0015 - kit.blur(bare, n * 0.004) * 0.006
    fine = kit.unit(kit.noise(n, seed + 11, 1.0, 50.0))
    mottle = kit.unit(kit.noise(n, seed + 12, 2.2, 5.0, 70.0))
    albedo = kit.tint(kit.rgb(62, 48, 36), kit.rgb(104, 84, 62), fine * 0.5 + mottle * 0.5)
    tile.soil("earth", albedo, 0.96 - 0.06 * fine, kit.noise(n, seed + 13, 1.2, 70.0) * 0.4)
    tile.ground("earth")
    tile.plain("blade", 700.0, 0.1, (0.05, 1.0, 1.0))
    tile.plain("leaf", 900.0, 0.08)
    tile.plain("moss", 600.0, 0.12)
    tile.plain("crumb", 400.0, 0.16)
    straw(tile, "thatch")
    floor = kit.bed(tile.height, size, 1024)
    grass = numpy.clip(1.0 - 0.97 * bare - 0.75 * moss, 0.02, 1.0)
    count = 26000
    spot = kit.scatter(rng, count, size, 0.1 + bare * 3.0)
    girth = rng.uniform(0.001, 0.004, count) * rng.uniform(0.6, 1.3, count)
    tile.grit("crumb", numpy.column_stack([spot, floor.at(spot[:, 0], spot[:, 1]) + girth * 0.3]), girth[:, None] * rng.uniform(0.6, 1.2, (count, 3)), swatch(rng, [(70, 55, 42), (92, 74, 56), (56, 44, 34), (112, 92, 70), (128, 116, 102)], count, 0.14, 0.04), 0.95, 0)
    count = 30000
    spot = kit.scatter(rng, count, size, 0.25 + grass)
    track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), rng.uniform(0.015, 0.06, count), 6, rng.normal(0.0, 0.6, count))
    level = floor.slab(rng, track, 0.004, None, None, 0.08)
    taper = numpy.array([0.7, 1.0, 1.0, 0.9, 0.7, 0.3])[None, :]
    tile.ribbons("thatch", lift(track, level + 0.0006), taper * rng.uniform(0.0008, 0.0016, (count, 1)), 3, swatch(rng, [(176, 156, 108), (158, 138, 96), (190, 174, 130), (134, 114, 82), (120, 104, 78)], count, 0.12, 0.04), rng.uniform(0.6, 0.8, count), fold=rng.uniform(0.1, 0.4, count), shade=0.1)
    floor.swell(grass * 0.003)
    carpet(tile, floor, moss, ((0.000022, 0.0035, 0.006, 0.0, [(66, 82, 34), (78, 92, 40), (58, 72, 30), (88, 96, 44)]), (0.000011, 0.0024, 0.0044, 0.0018, [(104, 122, 52), (120, 134, 60), (94, 112, 48), (138, 142, 68), (126, 124, 60)])))
    tufts = kit.scatter(rng, 13000, size, grass)
    vigour = 0.6 + 0.8 * kit.sample(lush, tufts[:, 0], tufts[:, 1], size) * kit.sample(grass, tufts[:, 0], tufts[:, 1], size)
    parent = numpy.repeat(numpy.arange(len(tufts)), rng.integers(9, 19, len(tufts)))
    count = len(parent)
    spot = tufts[parent] + rng.normal(0.0, 0.005, (count, 2))
    base = numpy.column_stack([spot, floor.at(spot[:, 0], spot[:, 1]) - 0.003])
    reach = rng.uniform(0.03, 0.058, count) * vigour[parent] * rng.uniform(0.75, 1.1, count)
    spine, side = kit.upright(base, rng.uniform(0.0, tau, count), reach, 6, numpy.clip(rng.normal(0.55, 0.3, count), 0.05, 1.35), rng.uniform(0.15, 1.0, count))
    wide = numpy.array([0.85, 1.0, 0.95, 0.8, 0.55, 0.12])[None, :] * (rng.uniform(0.0011, 0.0019, len(tufts))[parent] * rng.uniform(0.8, 1.2, count))[:, None]
    hue = kit.vary(rng, pick(rng, kit.sample(tone, tufts[:, 0], tufts[:, 1], size), [(0.5, 0.25, [(82, 110, 50), (90, 116, 54), (74, 102, 48)]), (0.32, 0.4, [(104, 124, 60), (114, 130, 66), (98, 118, 58)]), (0.18, 0.35, [(126, 132, 70), (138, 138, 78), (120, 124, 66)])]), 0.08, 0.03)[parent]
    hue = kit.vary(rng, hue, 0.1, 0.03)
    dead = rng.random(count) < 0.12
    hue[dead] = swatch(rng, [(176, 156, 104), (160, 140, 96), (190, 172, 124), (140, 118, 84)], int(dead.sum()), 0.1, 0.04)
    ramp = numpy.array([[1.45, 1.3, 1.25], [1.15, 1.1, 1.1], [1.0, 1.0, 1.0], [0.96, 0.98, 0.95], [1.0, 0.98, 0.9], [1.25, 1.05, 0.8]])
    tile.ribbons("blade", spine, wide, 3, hue[:, None, :] * ramp[None, :, :], numpy.where(dead, 0.72, rng.uniform(0.42, 0.58, count)), side, rng.uniform(0.25, 0.6, count), twist=rng.normal(0.0, 0.5, (count, 1)) * numpy.linspace(0.0, 1.0, 6)[None, :], shade=0.18)
    tile.note("grass grown")
    count = 3400
    spot = kit.scatter(rng, count, size, 0.04 + clover ** 1.5)
    rise = floor.at(spot[:, 0], spot[:, 1]) + rng.uniform(0.018, 0.04, count) * (0.7 + 0.5 * kit.sample(lush, spot[:, 0], spot[:, 1], size))
    span = rng.uniform(0.0075, 0.013, count)
    first = rng.uniform(0.0, tau, count)
    lean = rng.normal(0.0, 0.18, (count, 2))
    green = swatch(rng, [(78, 110, 58), (86, 116, 62), (70, 102, 56), (94, 120, 68)], count, 0.08, 0.03)
    t = numpy.linspace(0.0, 1.0, 6)
    profile = numpy.array([0.14, 0.62, 0.95, 1.0, 0.84, 0.36])
    mark = numpy.array([[0.85, 0.9, 0.85], [0.95, 0.98, 0.95], [1.45, 1.3, 1.45], [1.18, 1.12, 1.18], [0.98, 1.0, 0.98], [0.9, 0.95, 0.9]])
    for leaflet in range(3):
        angle = first + leaflet * (tau / 3.0) + rng.normal(0.0, 0.12, count)
        way = numpy.stack([numpy.cos(angle), numpy.sin(angle)], axis=1)
        along = (0.06 + 0.94 * t)[None, :] * span[:, None]
        xy = spot[:, None, :] + way[:, None, :] * along[..., None]
        z = rise[:, None] + along * (way[:, 0:1] * lean[:, 0:1] + way[:, 1:2] * lean[:, 1:2]) + along * rng.uniform(0.05, 0.3, (count, 1)) - (along / span[:, None]) ** 2 * span[:, None] * rng.uniform(0.1, 0.4, (count, 1))
        spine = numpy.concatenate([xy, z[..., None]], axis=-1).astype(numpy.float32)
        tile.ribbons("leaf", spine, profile[None, :] * (span * rng.uniform(0.4, 0.5, count))[:, None], 5, green[:, None, :] * mark[None, :, :] * rng.uniform(0.92, 1.08, (count, 1, 1)), rng.uniform(0.45, 0.6, count), fold=rng.uniform(0.05, 0.25, count), shade=0.1)
    tile.marks["clover"] = [(((numpy.argmax(clover) % n) + 0.5) * size / n, ((numpy.argmax(clover) // n) + 0.5) * size / n)]
    tile.marks["bare"] = [(((numpy.argmax(bare) % n) + 0.5) * size / n, ((numpy.argmax(bare) // n) + 0.5) * size / n)]


def stones(tile, floor, group, count, low, high, power, colors, variants, flat=(0.45, 0.8), sink=0.3, field=None, rough=(0.78, 0.9), speckle=(0.2, 0.4), tries=2, spread=1.0, lean=0.4, tilt=0.3, stain=0.0, order=None):
    rng = tile.rng
    spot = kit.scatter(rng, count, tile.size, field)
    scale = (low + (high - low) * rng.random((count, 1)) ** power) * numpy.column_stack([numpy.ones(count), rng.uniform(0.62, 1.0, count), rng.uniform(flat[0], flat[1], count)])
    which = rng.integers(variants[0], variants[1], count)
    rank = numpy.argsort(-scale[:, 0]) if order is None else order
    spot, scale, which = spot[rank], scale[rank], which[rank]
    extent = numpy.asarray(tile.extents[group], dtype=numpy.float64)[which]
    where, turned = floor.drop(rng, spot, extent * scale * 0.9, numpy.column_stack([rng.normal(0.0, tilt, count), rng.normal(0.0, tilt, count), rng.uniform(0.0, tau, count)]), tries, spread, sink, lean)
    tile.place(group, where, turned, scale, which, swatch(rng, colors, count, 0.1, 0.03), numpy.column_stack([rng.uniform(rough[0], rough[1], count), rng.uniform(speckle[0], speckle[1], count), numpy.full(count, stain)]))
    return where, scale


def soil(tile):
    rng = tile.rng
    size = tile.size
    n = tile.field
    seed = tile.seed
    tone = kit.unit(kit.noise(n, seed + 1, 2.8, 1.5, 8.0))
    lumps = kit.smoothstep(-0.6, 1.2, kit.noise(n, seed + 2, 2.8, 2.0, 10.0))
    tile.height = kit.noise(n, seed + 3, 3.0, 1.0, 9.0) * 0.009 + kit.noise(n, seed + 4, 2.2, 10.0, 60.0) * 0.003
    fine = kit.unit(kit.noise(n, seed + 5, 1.0, 50.0))
    mottle = kit.unit(kit.noise(n, seed + 6, 2.2, 5.0, 70.0))
    albedo = kit.tint(kit.rgb(54, 42, 33), kit.rgb(94, 74, 58), fine * 0.45 + mottle * 0.35 + tone * 0.2)
    tile.soil("earth", albedo, 0.95 - 0.06 * fine, kit.noise(n, seed + 7, 1.2, 60.0) * 0.5)
    tile.ground("earth")
    loam(tile, "clod")
    rock(tile, "stone")
    tile.plain("crumb", 400.0, 0.18)
    straw(tile, "straw", (110, 92, 66), 0.3)
    bark(tile, "root", (120, 100, 80), 0.1)
    floor = kit.bed(tile.height, size, 1024)
    for index in range(6):
        vertices, faces = kit.clod(seed + 20 + index, 4, 0.24)
        tile.variant("clod", vertices, faces, "clod")
    for index in range(10):
        vertices, faces = kit.clod(seed + 40 + index, 3, 0.3)
        tile.variant("clod", vertices, faces, "clod")
    for index in range(8):
        vertices, faces = kit.pebble(seed + 60 + index, 3, 0.15)
        tile.variant("stone", vertices, faces, "stone")
    browns = [(1.0, 0.98, 0.96), (0.9, 0.88, 0.86), (1.1, 1.06, 1.02), (0.8, 0.78, 0.76), (1.18, 1.12, 1.06)]
    tints = lambda count: numpy.asarray(browns, dtype=numpy.float32)[rng.integers(0, len(browns), count)] * numpy.exp(rng.normal(0.0, 0.08, (count, 1))).astype(numpy.float32)

    def clods(count, low, high, power, variants, field, sink, tries):
        spot = kit.scatter(rng, count, size, field)
        scale = (low + (high - low) * rng.random((count, 1)) ** power) * numpy.column_stack([numpy.ones(count), rng.uniform(0.7, 1.0, count), rng.uniform(0.5, 0.85, count)])
        which = rng.integers(variants[0], variants[1], count)
        rank = numpy.argsort(-scale[:, 0])
        spot, scale, which = spot[rank], scale[rank], which[rank]
        extent = numpy.asarray(tile.extents["clod"], dtype=numpy.float64)[which]
        where, turned = floor.drop(rng, spot, extent * scale * 0.88, numpy.column_stack([rng.normal(0.0, 0.35, count), rng.normal(0.0, 0.35, count), rng.uniform(0.0, tau, count)]), tries, 1.0, sink, 0.5)
        tile.place("clod", where, turned, scale, which, tints(count))

    clods(520, 0.022, 0.05, 1.6, (0, 6), 0.15 + lumps, 0.3, 2)
    clods(4200, 0.009, 0.022, 1.5, (6, 16), 0.3 + lumps, 0.2, 3)
    tile.note("large clods dropped")
    stones(tile, floor, "stone", 260, 0.004, 0.016, 2.0, [(150, 140, 130), (168, 150, 138), (120, 116, 112), (186, 178, 166), (140, 120, 106)], (0, 8), sink=0.35)
    clods(30000, 0.003, 0.009, 1.4, (6, 16), None, 0.15, 3)
    tile.note("small clods dropped")
    count = 130000
    spot = kit.scatter(rng, count, size)
    girth = rng.uniform(0.0008, 0.003, count) * rng.uniform(0.6, 1.3, count)
    tile.grit("crumb", numpy.column_stack([spot, floor.at(spot[:, 0], spot[:, 1]) + girth * 0.3]), girth[:, None] * rng.uniform(0.6, 1.2, (count, 3)), swatch(rng, [(84, 66, 52), (104, 84, 66), (66, 52, 41), (122, 100, 80), (54, 43, 35)], count, 0.14, 0.04), 0.95, 0)
    count = 700
    spot = kit.scatter(rng, count, size)
    reach = rng.uniform(0.015, 0.09, count)
    track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), reach, 8, rng.normal(0.0, 0.15, count))
    girth = rng.uniform(0.0009, 0.0019, (count, 1)) * numpy.ones((1, 8))
    level = floor.rest(rng, track, girth, rigid=True, batch=8, steep=0.3)
    tile.tubes("straw", lift(track, level + girth * 0.6), girth, 5, swatch(rng, [(190, 168, 116), (172, 150, 104), (204, 186, 138), (150, 128, 90), (128, 108, 80)], count, 0.12, 0.04), rng.uniform(0.6, 0.78, count), 0.55, cap=True)
    count = 520
    spot = kit.scatter(rng, count, size)
    reach = rng.uniform(0.03, 0.16, count)
    track = kit.paths(rng, spot, rng.uniform(0.0, tau, count), reach, 16, rng.normal(0.0, 1.2, count), rng.uniform(0.15, 0.5, count), 2.5)
    girth = numpy.linspace(1.0, 0.35, 16)[None, :] * rng.uniform(0.0004, 0.0011, (count, 1))
    level = floor.rest(rng, track, girth, 0.3, batch=8)
    tile.tubes("root", lift(track, level + girth), girth, 4, swatch(rng, [(150, 128, 100), (120, 98, 76), (92, 72, 56), (170, 150, 122)], count, 0.12, 0.04), 0.88)


catalog = {
    "ground_needles": {"size": 2.0, "seed": 1101, "build": needles, "grid": 768, "reach": 0.025, "compose": {"cavity": 0.4, "occlusion": 0.5, "fill": 3, "soften": 1.5, "keep": 0.3}, "text": "Conifer forest floor: thick mat of red-brown and straw pine and fir needles with small cones, twigs, bark flakes, moss patches and dark humus."},
    "ground_heath": {"size": 2.0, "seed": 2203, "build": heath, "grid": 1024, "reach": 0.03, "compose": {"cavity": 0.35, "occlusion": 0.6, "fill": 2, "soften": 1.0, "keep": 0.4}, "text": "Coastal heath floor: dark peaty soil with dead heather sprigs and wiry stems, fine leaf litter, grey-green lichen and moss cushions, granite grit and a few quartz pebbles."},
    "ground_moor": {"size": 2.5, "seed": 3307, "build": moor, "grid": 1024, "reach": 0.04, "compose": {"cavity": 0.4, "occlusion": 0.6, "fill": 4, "soften": 3.0, "keep": 0.25}, "text": "Upland moor: matted thatch of bleached straw-gold dead grass lying in swirls over low tussocks, fresh green shoots, dark wet peat in the gaps and sphagnum patches."},
    "ground_turf": {"size": 2.0, "seed": 4409, "build": turf, "grid": 768, "reach": 0.03, "compose": {"cavity": 0.4, "occlusion": 0.6, "fill": 4, "soften": 2.5, "keep": 0.25}, "text": "Short dense meadow turf seen from above: fine grass blades in tufts with clover leaves, small moss patches, dry thatch and a little bare earth."},
    "ground_soil": {"size": 2.0, "seed": 5501, "build": soil, "grid": 768, "reach": 0.04, "compose": {"cavity": 0.4, "occlusion": 0.7}, "text": "Tilled field soil: dark brown crumbly clods of varied size with small stones, bits of straw and fine roots, no furrows."},
}
