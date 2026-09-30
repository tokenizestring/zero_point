import math
import os
import numpy

import flora_kit as kit


def tile_rows(pattern, size, anchor):
    period = pattern.shape[0]
    rows = (numpy.arange(size) - anchor) % period
    return pattern[rows]


def compose(species, zones, builders, seed, relief, part="bark", size=kit.atlas_size, tongue=(9, 7, 1.5)):
    rng = numpy.random.default_rng(seed)
    layers = []
    for (start, end), builder in zip(zones, builders):
        period = max(8, int(round((end - start) * size)))
        pattern = builder(size, period, rng)
        anchor = int(round(start * size))
        layers.append({key: tile_rows(value, size, anchor) for key, value in pattern.items()})
    result = layers[0]
    for index in range(1, len(layers)):
        low = zones[index - 1][1] * size
        high = zones[index][0] * size
        rows = numpy.arange(size, dtype=numpy.float32)[:, None]
        x = numpy.clip((rows - low) / max(high - low, 1.0), 0.0, 1.0)
        ragged = kit.fbm(size, size, tongue[0], tongue[1], 4, rng)
        weight = kit.step(x + (ragged - 0.5) * tongue[2] * numpy.sin(math.pi * x), 0.3, 0.7)
        weight = numpy.where(x <= 0.0, 0.0, numpy.where(x >= 1.0, 1.0, weight)).astype(numpy.float32)
        result = {key: (result[key] * (1.0 - (weight[:, :, None] if result[key].ndim == 3 else weight)) + layers[index][key] * (weight[:, :, None] if result[key].ndim == 3 else weight)) for key in result}
    height = result["height"]
    occlusion = kit.height_occlusion(height, size / 90.0, 2.2) * kit.height_occlusion(height, size / 400.0, 1.4)
    albedo = numpy.clip(result["albedo"] * (0.55 + 0.45 * occlusion[:, :, None]), 0.0, 1.0)
    textures = kit.texture_set(species, part)
    kit.write_png(textures["diff"], kit.to_srgb(albedo))
    kit.write_png(textures["nor_gl"], kit.height_normal(height, relief * size / 1024.0))
    kit.write_png(textures["arm"], numpy.stack([occlusion * 0.8 + 0.2, numpy.clip(result["rough"], 0.05, 1.0), numpy.zeros_like(occlusion)], axis=2))
    os.makedirs(kit.preview_root, exist_ok=True)
    shade = kit.height_normal(height, relief * size / 1024.0) * 2.0 - 1.0
    light = numpy.clip(shade[:, :, 0] * -0.45 + shade[:, :, 1] * 0.35 + shade[:, :, 2] * 0.82, 0.0, 1.0)
    preview = kit.to_srgb(numpy.clip(albedo * (0.35 + 1.0 * light[:, :, None]), 0.0, 1.0))
    kit.write_png(os.path.join(kit.preview_root, "%s_%s.png" % (species, part)), preview[::2, ::2])
    print("BARK", species, part, [round(float(value), 3) for value in albedo.mean(axis=(0, 1))])


def plates(width, height, rng, cells_x, cell_height, jitter, warp_amount, edge, ragged=0.0):
    warp = ((kit.fbm(width, height, 3, max(1, height // (width // 3 + 1)), 3, rng) - 0.5) * warp_amount, (kit.fbm(width, height, 4, max(1, height // (width // 3 + 1)), 3, rng) - 0.5) * warp_amount)
    if ragged:
        warp = (warp[0] + (kit.fbm(width, height, 28, max(2, height * 28 // width), 3, rng) - 0.5) * ragged, warp[1] + (kit.fbm(width, height, 28, max(2, height * 28 // width), 3, rng) - 0.5) * ragged)
    first, second, identity = kit.worley(width, height, cells_x, max(1, int(round(height / cell_height))), rng, jitter, warp)
    tone = numpy.random.default_rng(int(rng.integers(1 << 30))).random(int(identity.max()) + 1).astype(numpy.float32)[identity]
    return kit.step(second - first, edge[0], edge[1]), tone


def cells_for(height, pixels, scale, minimum=1):
    return max(minimum, int(round(height / (pixels * scale))))


def fissures(width, height, rng, cells_x, cell_height, octaves, warp_amount, gain=0.5):
    scale = width / 1024.0
    warp = ((kit.fbm(width, height, 4, cells_for(height, 300.0, scale, 1), 3, rng) - 0.5) * warp_amount, (kit.fbm(width, height, 5, cells_for(height, 260.0, scale, 1), 3, rng) - 0.5) * warp_amount * 0.5)
    field = kit.fbm(width, height, cells_x, cells_for(height, cell_height, scale, 1), octaves, rng, gain, warp)
    return numpy.abs(field - field.mean()) / max(float(field.std()), 1e-6)


def spots(width, height, rng, cells_x, cell_height, fraction, radius):
    scale = width / 1024.0
    wobble = ((kit.fbm(width, height, 24, cells_for(height, 40.0, scale, 2), 2, rng) - 0.5) * 0.02, (kit.fbm(width, height, 24, cells_for(height, 40.0, scale, 2), 2, rng) - 0.5) * 0.02)
    first, second, identity = kit.worley(width, height, cells_x, cells_for(height, cell_height, scale, 1), rng, 1.0, wobble)
    chosen = (numpy.random.default_rng(int(rng.integers(1 << 30))).random(int(identity.max()) + 1) < fraction).astype(numpy.float32)[identity]
    size = numpy.random.default_rng(int(rng.integers(1 << 30))).uniform(0.5, 1.0, int(identity.max()) + 1).astype(numpy.float32)[identity]
    return kit.step(first, radius * size, radius * size * 0.72) * chosen


def color(values):
    return numpy.array(values, dtype=numpy.float32)[None, None, :]


def moss_layer(width, height, rng, relief, albedo, level, band_weight, patch):
    scale = width / 1024.0
    u = (numpy.arange(width, dtype=numpy.float32) + 0.5) / width
    band = numpy.cos(math.tau * (u - 0.5))[None, :] * band_weight
    field = kit.fbm(width, height, patch, cells_for(height, 1024.0 / patch, scale, 2), 4, rng) + band + level + (0.5 - relief) * 0.1
    moss = kit.step(field, 0.57, 0.64)
    tufts = kit.fbm(width, height, 80, cells_for(height, 13.0, scale, 6), 3, rng)
    clump = kit.fbm(width, height, 22, cells_for(height, 46.0, scale, 3), 3, rng)
    cushion = kit.blur(relief, 6.0 * scale) * 0.4 + 0.5 + clump * 0.22 + tufts * 0.14
    relief = relief * (1.0 - moss) + cushion * moss
    tint = kit.ramp(numpy.clip(tufts * 0.55 + clump * 0.55, 0.0, 1.0), [(0.0, (0.012, 0.026, 0.006)), (0.45, (0.032, 0.062, 0.013)), (0.75, (0.062, 0.1, 0.022)), (1.0, (0.105, 0.14, 0.036))])
    return relief, kit.blend(albedo, tint, moss), moss


def oak_zone(moss_level, band_weight):
    def builder(width, height, rng):
        scale = width / 1024.0
        ridge, ridge_tone = plates(width, height, rng, 22, 190.0 * scale, 1.0, 0.1, (0.0, 0.34), 0.014)
        ridge = ridge ** 0.5
        split, split_tone = plates(width, height, rng, 40, 64.0 * scale, 1.0, 0.04, (0.0, 0.3), 0.012)
        split = split ** 0.45
        cross = kit.step(fissures(width, height, rng, 7, 26.0, 3, 0.05), 0.0, 0.22)
        fibre = kit.fbm(width, height, 170, cells_for(height, 200.0, scale, 2), 3, rng)
        flake = kit.fbm(width, height, 90, cells_for(height, 16.0, scale, 4), 5, rng, 0.62)
        relief = ridge * (0.46 + 0.2 * ridge_tone + 0.22 * split * (0.75 + 0.25 * split_tone) + 0.12 * cross) * (0.8 + 0.2 * fibre) + (flake - 0.5) * 0.26
        relief = numpy.clip(relief * 1.08 + 0.05, 0.0, 1.0)
        albedo = kit.ramp(relief, [(0.0, (0.013, 0.01, 0.008)), (0.25, (0.035, 0.027, 0.02)), (0.55, (0.077, 0.061, 0.046)), (0.8, (0.12, 0.098, 0.075)), (1.0, (0.165, 0.14, 0.108))])
        tone = kit.fbm(width, height, 7, cells_for(height, 150.0, scale, 2), 3, rng)
        albedo = albedo * (0.8 + 0.4 * tone[:, :, None]) * (0.86 + 0.28 * flake[:, :, None]) * (0.88 + 0.24 * ridge_tone[:, :, None])
        algae = kit.step(kit.fbm(width, height, 5, cells_for(height, 210.0, scale, 2), 4, rng), 0.45, 0.75) * kit.step(relief, 0.3, 0.7)
        albedo = kit.blend(albedo, albedo * color((0.8, 1.0, 0.66)) + color((0.0, 0.006, 0.0)), algae * 0.7)
        crust = kit.fbm(width, height, 110, cells_for(height, 9.0, scale, 8), 3, rng)
        lichen = spots(width, height, rng, 11, 92.0, 0.28, 0.4) * kit.step(relief, 0.4, 0.7) * kit.step(crust, 0.25, 0.6)
        albedo = kit.blend(albedo, color((0.2, 0.225, 0.185)) * (0.7 + 0.6 * crust[:, :, None]), lichen * 0.55)
        gold = spots(width, height, rng, 34, 30.0, 0.04, 0.36) * kit.step(relief, 0.5, 0.8)
        albedo = kit.blend(albedo, color((0.3, 0.24, 0.06)) * (0.7 + 0.6 * crust[:, :, None]), gold * 0.5)
        relief = relief + lichen * 0.02 * crust
        relief, albedo, moss = moss_layer(width, height, rng, relief, albedo, moss_level, band_weight, 5)
        rough = 0.9 + moss * 0.06 - lichen * 0.05
        return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": rough.astype(numpy.float32)}
    return builder


def diamonds(width, height, rng, cells_x, cell_height, fraction, size, aspect):
    scale = width / 1024.0
    cells_y = cells_for(height, cell_height, scale, 1)
    points_x = rng.random((cells_y, cells_x)).astype(numpy.float32)
    points_y = rng.random((cells_y, cells_x)).astype(numpy.float32)
    chosen = rng.random((cells_y, cells_x)) < fraction
    sizes = rng.uniform(0.55, 1.0, (cells_y, cells_x)).astype(numpy.float32) * size * scale
    xs = (numpy.arange(width, dtype=numpy.float32) + 0.5) / width * cells_x
    ys = (numpy.arange(height, dtype=numpy.float32) + 0.5) / height * cells_y
    x, y = numpy.meshgrid(xs, ys)
    cx = numpy.floor(x).astype(numpy.int64)
    cy = numpy.floor(y).astype(numpy.int64)
    field = numpy.full((height, width), 9.0, dtype=numpy.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx = cx + dx
            ny = cy + dy
            wx = nx % cells_x
            wy = ny % cells_y
            across = numpy.abs(nx + points_x[wy, wx] - x) * (width / cells_x)
            along = numpy.abs(ny + points_y[wy, wx] - y) * (height / cells_y)
            value = across / sizes[wy, wx] + along / (sizes[wy, wx] * aspect)
            field = numpy.where(chosen[wy, wx], numpy.minimum(field, value), field)
    return field


def birch_base(width, height, rng):
    scale = width / 1024.0
    ridge, ridge_tone = plates(width, height, rng, 15, 150.0 * scale, 1.0, 0.1, (0.0, 0.36), 0.02)
    ridge = ridge ** 0.5
    split, split_tone = plates(width, height, rng, 30, 46.0 * scale, 1.0, 0.04, (0.0, 0.3), 0.015)
    split = split ** 0.45
    flake = kit.fbm(width, height, 70, cells_for(height, 12.0, scale, 4), 5, rng, 0.62)
    relief = numpy.clip(ridge * (0.5 + 0.22 * ridge_tone + 0.28 * split) + (flake - 0.5) * 0.3 + 0.05, 0.0, 1.0)
    albedo = kit.ramp(relief, [(0.0, (0.005, 0.005, 0.005)), (0.35, (0.016, 0.015, 0.014)), (0.7, (0.04, 0.037, 0.034)), (1.0, (0.085, 0.08, 0.074))])
    albedo = albedo * (0.8 + 0.4 * split_tone[:, :, None])
    pale = kit.step(ridge_tone, 0.72, 0.86) * kit.step(relief, 0.55, 0.8)
    albedo = kit.blend(albedo, color((0.4, 0.385, 0.35)) * (0.7 + 0.5 * flake[:, :, None]), pale * 0.6)
    relief, albedo, moss = moss_layer(width, height, rng, relief, albedo, -0.08, 0.04, 5)
    return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": (0.9 + moss * 0.05).astype(numpy.float32)}


def birch_white(width, height, rng):
    scale = width / 1024.0
    tone = kit.fbm(width, height, 3, cells_for(height, 70.0, scale, 2), 4, rng)
    band = kit.fbm(width, height, 2, cells_for(height, 11.0, scale, 6), 3, rng)
    grain = kit.fbm(width, height, 9, cells_for(height, 3.0, scale, 12), 2, rng)
    albedo = kit.ramp(numpy.clip(tone * 0.55 + band * 0.45, 0.0, 1.0), [(0.0, (0.36, 0.345, 0.32)), (0.45, (0.56, 0.545, 0.51)), (1.0, (0.72, 0.705, 0.67))])
    warm = kit.step(kit.fbm(width, height, 4, cells_for(height, 120.0, scale, 2), 3, rng), 0.45, 0.75)
    albedo = kit.blend(albedo, albedo * color((1.0, 0.86, 0.74)), warm * 0.6)
    albedo = albedo * (0.92 + 0.16 * grain[:, :, None])
    dash = kit.step(kit.fbm(width, height, 12, cells_for(height, 4.2, scale, 10), 2, rng), 0.68, 0.73) * kit.step(kit.fbm(width, height, 6, cells_for(height, 60.0, scale, 3), 2, rng), 0.35, 0.6)
    albedo = kit.blend(albedo, color((0.1, 0.085, 0.075)), dash * 0.85)
    peel = kit.step(fissures(width, height, rng, 3, 20.0, 2, 0.015), 0.1, 0.0)
    albedo = kit.blend(albedo, color((0.2, 0.17, 0.145)), peel * 0.55)
    field = diamonds(width, height, rng, 5, 210.0, 0.45, 52.0, 1.15)
    edge = kit.fbm(width, height, 30, cells_for(height, 34.0, scale, 3), 3, rng)
    eye = kit.step(field + (edge - 0.5) * 0.7, 1.0, 0.72)
    rugged, rugged_tone = plates(width, height, rng, 40, 30.0 * scale, 1.0, 0.03, (0.0, 0.3), 0.015)
    rugged = rugged ** 0.5
    dark = kit.ramp(rugged, [(0.0, (0.004, 0.004, 0.004)), (0.5, (0.014, 0.013, 0.012)), (1.0, (0.04, 0.037, 0.034))])
    stain = kit.blur(eye, 3.0 * scale, 46.0 * scale)
    albedo = kit.blend(albedo, albedo * color((0.62, 0.6, 0.57)), numpy.clip(stain * 1.6, 0.0, 1.0) * 0.6)
    albedo = kit.blend(albedo, dark, eye)
    algae = kit.step(kit.fbm(width, height, 4, cells_for(height, 200.0, scale, 2), 3, rng), 0.55, 0.85)
    albedo = kit.blend(albedo, albedo * color((0.78, 0.92, 0.66)), algae * 0.4 * (1.0 - eye))
    relief = 0.62 + band * 0.05 + dash * 0.1 - peel * 0.14 + (grain - 0.5) * 0.04
    relief = relief * (1.0 - eye) + (0.3 + rugged * 0.5) * eye
    rough = 0.52 + eye * 0.38 + dash * 0.2
    return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": rough.astype(numpy.float32)}


def birch_twig(width, height, rng):
    scale = width / 1024.0
    tone = kit.fbm(width, height, 8, cells_for(height, 40.0, scale, 2), 4, rng)
    grain = kit.fbm(width, height, 60, cells_for(height, 8.0, scale, 6), 3, rng)
    albedo = kit.ramp(numpy.clip(tone * 0.6 + grain * 0.4, 0.0, 1.0), [(0.0, (0.022, 0.014, 0.013)), (0.5, (0.05, 0.03, 0.027)), (1.0, (0.095, 0.06, 0.05))])
    dots = spots(width, height, rng, 26, 20.0, 0.3, 0.3)
    albedo = kit.blend(albedo, color((0.26, 0.22, 0.18)), dots * 0.8)
    relief = 0.5 + (grain - 0.5) * 0.2 + dots * 0.12
    return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": numpy.full((height, width), 0.62, dtype=numpy.float32)}


birch_zones = ((0.02, 0.18), (0.36, 0.72), (0.82, 0.98))


def birch():
    compose("birch", birch_zones, (birch_base, birch_white, birch_twig), 5203, 6.0, "bark", kit.atlas_size, (16, 3, 2.6))


def terraces(field, steps):
    scaled = (field - field.min()) / max(float(field.max() - field.min()), 1e-6) * steps
    level = numpy.floor(scaled) / steps
    fraction = scaled - numpy.floor(scaled)
    return level.astype(numpy.float32), kit.step(fraction, 0.14, 0.0), fraction.astype(numpy.float32)


def pine_plated(width, height, rng):
    scale = width / 1024.0
    plate, tone = plates(width, height, rng, 10, 300.0 * scale, 1.0, 0.2, (0.0, 0.2), 0.05)
    other, other_tone = plates(width, height, rng, 6, 190.0 * scale, 1.0, 0.16, (0.0, 0.16), 0.05)
    plate = numpy.minimum(plate, other) ** 0.45
    tone = tone * 0.6 + other_tone * 0.4
    level, edge, fraction = terraces(kit.fbm(width, height, 12, cells_for(height, 64.0, scale, 3), 3, rng), 8)
    grain = kit.fbm(width, height, 80, cells_for(height, 12.0, scale, 4), 4, rng, 0.6)
    relief = numpy.clip(plate * (0.48 + 0.14 * tone + 0.24 * level + 0.05 * fraction) + (grain - 0.5) * 0.12 - edge * plate * 0.05 + 0.04, 0.0, 1.0)
    surface = kit.ramp(numpy.clip(level * 0.55 + grain * 0.35 + tone * 0.2, 0.0, 1.0), [(0.0, (0.075, 0.055, 0.05)), (0.4, (0.135, 0.1, 0.088)), (0.75, (0.2, 0.15, 0.13)), (1.0, (0.27, 0.195, 0.16))])
    albedo = kit.blend(color((0.012, 0.01, 0.009)) * numpy.ones((height, width, 1), dtype=numpy.float32), surface, kit.step(relief, 0.1, 0.36))
    albedo = kit.blend(albedo, albedo * color((0.6, 0.54, 0.5)), edge * 0.6)
    crust = kit.fbm(width, height, 110, cells_for(height, 9.0, scale, 8), 3, rng)
    lichen = spots(width, height, rng, 9, 120.0, 0.3, 0.4) * kit.step(relief, 0.45, 0.7) * kit.step(crust, 0.3, 0.6)
    albedo = kit.blend(albedo, color((0.24, 0.27, 0.22)) * (0.7 + 0.6 * crust[:, :, None]), lichen * 0.5)
    relief, albedo, moss = moss_layer(width, height, rng, relief, albedo, -0.12, 0.05, 5)
    return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": (0.88 + moss * 0.06).astype(numpy.float32)}


def pine_orange(width, height, rng):
    scale = width / 1024.0
    flake, tone = plates(width, height, rng, 11, 210.0 * scale, 1.0, 0.1, (0.0, 0.1), 0.03)
    flake = flake ** 0.5
    level, edge, fraction = terraces(kit.fbm(width, height, 9, cells_for(height, 44.0, scale, 3), 3, rng), 10)
    grain = kit.fbm(width, height, 70, cells_for(height, 10.0, scale, 4), 4, rng, 0.6)
    relief = numpy.clip(flake * (0.55 + 0.1 * tone + 0.2 * level + 0.08 * fraction) + (grain - 0.5) * 0.1 + 0.05, 0.0, 1.0)
    surface = kit.ramp(numpy.clip(level * 0.5 + fraction * 0.25 + grain * 0.25 + tone * 0.15, 0.0, 1.0), [(0.0, (0.22, 0.095, 0.045)), (0.4, (0.35, 0.155, 0.07)), (0.72, (0.46, 0.225, 0.105)), (1.0, (0.56, 0.335, 0.17))])
    albedo = kit.blend(color((0.05, 0.026, 0.016)) * numpy.ones((height, width, 1), dtype=numpy.float32), surface, kit.step(relief, 0.08, 0.3))
    grey = kit.step(kit.fbm(width, height, 6, cells_for(height, 150.0, scale, 2), 3, rng), 0.55, 0.78)
    albedo = kit.blend(albedo, albedo * color((0.62, 0.72, 0.85)) + color((0.03, 0.03, 0.03)), grey * 0.55)
    albedo = kit.blend(albedo, albedo * color((0.62, 0.52, 0.45)), edge * 0.65)
    return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": numpy.full((height, width), 0.78, dtype=numpy.float32)}


pine_zones = ((0.02, 0.37), (0.63, 0.98))


def pine():
    compose("pine", pine_zones, (pine_plated, pine_orange), 6301, 7.0, "bark", kit.atlas_size, (14, 3, 2.4))


def hawthorn_zone(width, height, rng):
    scale = width / 1024.0
    ridge, ridge_tone = plates(width, height, rng, 16, 120.0 * scale, 1.0, 0.12, (0.0, 0.34), 0.03)
    ridge = ridge ** 0.5
    scale_plate, scale_tone = plates(width, height, rng, 34, 40.0 * scale, 1.0, 0.05, (0.0, 0.32), 0.02)
    scale_plate = scale_plate ** 0.5
    fibre = kit.fbm(width, height, 150, cells_for(height, 180.0, scale, 2), 3, rng)
    flake = kit.fbm(width, height, 90, cells_for(height, 14.0, scale, 4), 5, rng, 0.62)
    relief = numpy.clip(ridge * (0.45 + 0.2 * ridge_tone + 0.3 * scale_plate * (0.7 + 0.3 * scale_tone)) * (0.85 + 0.15 * fibre) + (flake - 0.5) * 0.24 + 0.05, 0.0, 1.0)
    albedo = kit.ramp(relief, [(0.0, (0.02, 0.013, 0.009)), (0.25, (0.06, 0.036, 0.022)), (0.55, (0.1, 0.078, 0.06)), (0.8, (0.15, 0.13, 0.11)), (1.0, (0.21, 0.19, 0.165))])
    albedo = albedo * (0.82 + 0.36 * scale_tone[:, :, None]) * (0.88 + 0.24 * flake[:, :, None])
    crust = kit.fbm(width, height, 110, cells_for(height, 9.0, scale, 8), 3, rng)
    lichen = spots(width, height, rng, 8, 100.0, 0.55, 0.46) * kit.step(crust, 0.2, 0.55)
    albedo = kit.blend(albedo, color((0.3, 0.33, 0.27)) * (0.7 + 0.6 * crust[:, :, None]), lichen * 0.72)
    gold = spots(width, height, rng, 18, 56.0, 0.22, 0.42) * kit.step(crust, 0.3, 0.6)
    albedo = kit.blend(albedo, color((0.42, 0.3, 0.05)) * (0.7 + 0.6 * crust[:, :, None]), gold * 0.75)
    relief = relief + (lichen + gold) * 0.03 * crust
    relief, albedo, moss = moss_layer(width, height, rng, relief, albedo, -0.1, 0.06, 5)
    rough = 0.9 + moss * 0.05 - lichen * 0.05
    return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": rough.astype(numpy.float32)}


def willow_zone(width, height, rng):
    scale = width / 1024.0
    ridge, ridge_tone = plates(width, height, rng, 12, 230.0 * scale, 1.0, 0.22, (0.0, 0.42), 0.05)
    ridge = ridge ** 0.55
    split, split_tone = plates(width, height, rng, 26, 90.0 * scale, 1.0, 0.08, (0.0, 0.36), 0.025)
    split = split ** 0.5
    fibre = kit.fbm(width, height, 150, cells_for(height, 220.0, scale, 2), 3, rng)
    flake = kit.fbm(width, height, 80, cells_for(height, 18.0, scale, 4), 5, rng, 0.62)
    relief = numpy.clip(ridge * (0.5 + 0.2 * ridge_tone + 0.26 * split) * (0.8 + 0.2 * fibre) + (flake - 0.5) * 0.22 + 0.05, 0.0, 1.0)
    albedo = kit.ramp(relief, [(0.0, (0.016, 0.012, 0.009)), (0.25, (0.042, 0.033, 0.024)), (0.55, (0.09, 0.076, 0.058)), (0.8, (0.14, 0.125, 0.1)), (1.0, (0.2, 0.18, 0.15))])
    albedo = albedo * (0.82 + 0.36 * split_tone[:, :, None]) * (0.88 + 0.24 * flake[:, :, None])
    algae = kit.step(kit.fbm(width, height, 4, cells_for(height, 240.0, scale, 2), 4, rng), 0.35, 0.7) * kit.step(relief, 0.25, 0.7)
    albedo = kit.blend(albedo, albedo * color((0.7, 1.0, 0.55)) + color((0.0, 0.012, 0.0)), algae * 0.8)
    crust = kit.fbm(width, height, 110, cells_for(height, 9.0, scale, 8), 3, rng)
    lichen = spots(width, height, rng, 9, 110.0, 0.35, 0.42) * kit.step(relief, 0.4, 0.7) * kit.step(crust, 0.25, 0.6)
    albedo = kit.blend(albedo, color((0.24, 0.27, 0.21)) * (0.7 + 0.6 * crust[:, :, None]), lichen * 0.6)
    relief, albedo, moss = moss_layer(width, height, rng, relief, albedo, 0.0, 0.08, 4)
    rough = 0.9 + moss * 0.06 - lichen * 0.05
    return {"albedo": albedo.astype(numpy.float32), "height": relief.astype(numpy.float32), "rough": rough.astype(numpy.float32)}


willow_zones = ((0.0, 1.0),)


def willow():
    compose("willow", willow_zones, (willow_zone,), 8513, 8.5)


hawthorn_zones = ((0.0, 1.0),)


def hawthorn():
    compose("hawthorn", hawthorn_zones, (hawthorn_zone,), 7411, 8.0)


oak_zones = ((0.02, 0.36), (0.46, 0.98))


def oak():
    compose("oak", oak_zones, (oak_zone(0.06, 0.03), oak_zone(-0.11, 0.1)), 4101, 8.5)
