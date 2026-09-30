import json
import math
import os
import struct
import zlib
from urllib.parse import unquote
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(here))
models_root = os.path.join(root, "assets", "raw", "models")
library_root = os.path.join(models_root, "_library")
preview_root = os.path.join(root, "assets", "previews", "buildings")
hdri_path = os.path.join(root, "assets", "raw", "hdri", "kloofendal_overcast_puresky_4k.hdr")
size = 1024
catalog = {}
swatches = {}


def write_png(path, data):
    array = np.clip(np.rint(np.asarray(data, dtype=np.float64) * 255.0), 0, 255).astype(np.uint8)[::-1]
    height, width = array.shape[:2]
    channels = 1 if array.ndim == 2 else array.shape[2]
    flat_rows = array.reshape(height, width * channels).astype(np.int16)
    filtered = flat_rows.copy()
    filtered[:, channels:] = (flat_rows[:, channels:] - flat_rows[:, :-channels]) % 256
    raw = np.empty((height, width * channels + 1), np.uint8)
    raw[:, 0] = 1
    raw[:, 1:] = filtered.astype(np.uint8)

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    kind = {1: 0, 3: 2, 4: 6}[channels]
    header = struct.pack(">IIBBBBB", width, height, 8, kind, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw.tobytes(), 6)) + chunk(b"IEND", b""))


def srgb(color):
    c = np.clip(color, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0.0031308), 1.0 / 2.4) - 0.055)


def linear(r, g, b):
    return np.array([((channel / 255.0 + 0.055) / 1.055) ** 2.4 if channel > 10.31 else channel / 255.0 / 12.92 for channel in (r, g, b)])


grid_v, grid_u = np.meshgrid(np.arange(size) + 0.5, np.arange(size) + 0.5, indexing="ij")


def field(seed, low, high=None, beta=2.0, su=1.0, sv=1.0):
    rng = np.random.default_rng(seed)
    white = np.fft.rfft2(rng.standard_normal((size, size)))
    fy = (np.fft.fftfreq(size) * size)[:, None] * sv
    fx = (np.fft.rfftfreq(size) * size)[None, :] * su
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1e-6
    amplitude = f ** (-beta * 0.5)
    amplitude *= 1.0 - np.exp(-((f / max(low, 1e-3)) ** 4))
    if high is not None:
        amplitude *= np.exp(-((f / high) ** 2))
    out = np.fft.irfft2(white * amplitude, s=(size, size))
    out -= out.mean()
    return out / (out.std() + 1e-12)


def unit(x):
    return 0.5 + 0.5 * np.tanh(0.85 * x)


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def cover(x, fraction, soft=0.1):
    t = float(np.quantile(x, 1.0 - fraction))
    s = soft * (float(np.std(x)) + 1e-9)
    return sstep(t - s, t + s, x)


def patchy(seed, fraction, low, high, region=0.8, soft=0.12, beta=1.8):
    return cover(field(seed, low, high, beta) + region * field(seed + 1, 1.5, 12.0, 2.2), fraction, soft)


def blur(image, sigma):
    if image.ndim == 3:
        return np.stack([blur(image[:, :, c], sigma) for c in range(image.shape[2])], -1)
    fy = np.fft.fftfreq(size)[:, None]
    fx = np.fft.rfftfreq(size)[None, :]
    kernel = np.exp(-2.0 * math.pi * math.pi * sigma * sigma * (fx * fx + fy * fy))
    return np.fft.irfft2(np.fft.rfft2(image) * kernel, s=image.shape)


def speckle(seed, sigma):
    rng = np.random.default_rng(seed)
    out = blur(rng.standard_normal((size, size)), sigma)
    out -= out.mean()
    return out / (out.std() + 1e-12)


def voronoi(cells_u, cells_v, seed, jitter=0.85):
    rng = np.random.default_rng(seed)
    jx = rng.random((cells_v, cells_u))
    jy = rng.random((cells_v, cells_u))
    su = size / cells_u
    sv = size / cells_v
    cu = np.floor(grid_u / su).astype(np.int64)
    cv = np.floor(grid_v / sv).astype(np.int64)
    first = np.full((size, size), 1e9)
    second = np.full((size, size), 1e9)
    ident = np.zeros((size, size), np.int64)
    for ov in (-1, 0, 1):
        for ou in (-1, 0, 1):
            nu = cu + ou
            nv = cv + ov
            wu = nu % cells_u
            wv = nv % cells_v
            pu = (nu + 0.5 + (jx[wv, wu] - 0.5) * jitter) * su
            pv = (nv + 0.5 + (jy[wv, wu] - 0.5) * jitter) * sv
            d = np.hypot(grid_u - pu, grid_v - pv)
            closer = d < first
            second = np.where(closer, first, np.minimum(second, d))
            ident = np.where(closer, wv * cells_u + wu, ident)
            first = np.where(closer, d, first)
    return first, second, ident


def site_voronoi(sites, tile, stretch=1.0, rounding=0.0):
    scale = size / tile
    best = [np.full((size, size), 1e18) for index in range(3)]
    vx = [np.zeros((size, size)) for index in range(3)]
    vy = [np.zeros((size, size)) for index in range(3)]
    id1 = np.zeros((size, size), np.int64)
    for index, (sx, sy) in enumerate(sites):
        dx = ((grid_u - sx * scale) + size * 0.5) % size - size * 0.5
        dy = (((grid_v - sy * scale) + size * 0.5) % size - size * 0.5) * stretch
        d = dx * dx + dy * dy
        c1 = d < best[0]
        c2 = (~c1) & (d < best[1])
        c3 = (~c1) & (~c2) & (d < best[2])
        up = c1 | c2
        best[2] = np.where(up, best[1], np.where(c3, d, best[2]))
        vx[2] = np.where(up, vx[1], np.where(c3, dx, vx[2]))
        vy[2] = np.where(up, vy[1], np.where(c3, dy, vy[2]))
        best[1] = np.where(c1, best[0], np.where(c2, d, best[1]))
        vx[1] = np.where(c1, vx[0], np.where(c2, dx, vx[1]))
        vy[1] = np.where(c1, vy[0], np.where(c2, dy, vy[1]))
        best[0] = np.where(c1, d, best[0])
        vx[0] = np.where(c1, dx, vx[0])
        vy[0] = np.where(c1, dy, vy[0])
        id1 = np.where(c1, index, id1)
    edges = []
    for k in (1, 2):
        ex = vx[0] - vx[k]
        ey = vy[0] - vy[k]
        length = np.hypot(ex, ey) + 1e-9
        scaled = (best[k] - best[0]) / (2.0 * length)
        edges.append(scaled / np.sqrt((ex / length) ** 2 + (stretch * ey / length) ** 2) / scale)
    if rounding > 0.0:
        edge = -rounding * np.log(np.exp(-edges[0] / rounding) + np.exp(-edges[1] / rounding))
    else:
        edge = np.minimum(edges[0], edges[1])
    return id1, edge, vx[0] / scale, vy[0] / (stretch * scale)


def cavity(height, sigma, depth):
    return np.clip((blur(height, sigma) - height) / depth, 0.0, 1.0)


def normal_map(height, texel, strength=1.0):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / (2.0 * texel) * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / (2.0 * texel) * strength
    n = np.stack([-dx, -dy, np.ones_like(height)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def mix(a, b, t):
    t = np.asarray(t, dtype=np.float64)
    if t.ndim == 2 and ((np.ndim(a) >= 1 and np.shape(a)[-1] == 3) or (np.ndim(b) >= 1 and np.shape(b)[-1] == 3)):
        t = t[:, :, None]
    return a * (1.0 - t) + b * t


def tint(color, amount):
    return color * np.asarray(amount, dtype=np.float64)[:, :, None]


def flat(color):
    return np.broadcast_to(np.asarray(color, dtype=np.float64), (size, size, 3)).copy()


def swatch(name, albedo, normal, occlusion):
    light = np.array([-0.45, 0.55, 0.7])
    light /= np.linalg.norm(light)
    lambert = np.clip(normal @ light, 0.0, 1.0)
    shaded = srgb(albedo * (0.25 + 0.95 * lambert)[:, :, None] * np.clip(occlusion, 0, 1)[:, :, None])
    swatches[name] = shaded.reshape(256, 4, 256, 4, 3).mean(axis=(1, 3))


def write_sheet():
    names = list(swatches)
    columns = 8
    rows = (len(names) + columns - 1) // columns
    sheet = np.full((rows * 264, columns * 264, 3), 0.1)
    for number, name in enumerate(names):
        r = rows - 1 - number // columns
        c = number % columns
        sheet[r * 264 + 4:r * 264 + 260, c * 264 + 4:c * 264 + 260] = swatches[name]
    os.makedirs(preview_root, exist_ok=True)
    write_png(os.path.join(preview_root, "library_swatches.png"), sheet)


def save(name, albedo, rough, occlusion, height, tile, strength=1.0, metal=None, extra=None):
    os.makedirs(library_root, exist_ok=True)
    normal = normal_map(height, tile / size, strength)
    swatch(name, albedo, normal, occlusion)
    write_png(os.path.join(library_root, name + "_albedo.png"), srgb(albedo))
    orm = np.stack([np.clip(occlusion, 0.0, 1.0), np.clip(rough, 0.03, 1.0), np.zeros((size, size)) if metal is None else np.clip(metal, 0.0, 1.0)], -1)
    write_png(os.path.join(library_root, name + "_orm.png"), orm)
    write_png(os.path.join(library_root, name + "_normal.png"), normal * 0.5 + 0.5)
    entry = {"tile": tile}
    if extra:
        entry.update(extra)
    catalog[name] = entry
    print("LIBRARY", name, "tile", tile, "albedo", np.round(albedo.reshape(-1, 3).mean(0), 3).tolist(), "rough", round(float(np.mean(rough)), 3), flush=True)


def polygon_sdf(xs, ys, points):
    distance = np.full(xs.shape, -1e9)
    count = len(points)
    for index in range(count):
        ax, ay = points[index]
        bx, by = points[(index + 1) % count]
        ex = bx - ax
        ey = by - ay
        length = math.hypot(ex, ey)
        if length < 1e-9:
            continue
        distance = np.maximum(distance, ((xs - ax) * ey - (ys - ay) * ex) / length)
    return distance


def window(points, margin):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    u0 = int(math.floor(min(xs))) - margin
    u1 = int(math.ceil(max(xs))) + margin
    v0 = int(math.floor(min(ys))) - margin
    v1 = int(math.ceil(max(ys))) + margin
    cols = np.arange(u0, u1)
    rows = np.arange(v0, v1)
    lv, lu = np.meshgrid(rows + 0.5, cols + 0.5, indexing="ij")
    return np.ix_(rows % size, cols % size), lu, lv


def granite_palette(rng, count):
    choices = [linear(158, 128, 112), linear(138, 130, 124), linear(150, 134, 116), linear(112, 108, 106), linear(142, 108, 90), linear(168, 152, 138), linear(160, 126, 118), linear(124, 116, 108)]
    weights = np.array([0.24, 0.18, 0.15, 0.09, 0.08, 0.08, 0.12, 0.06])
    picks = rng.choice(len(choices), count, p=weights / weights.sum())
    return np.array([choices[p] for p in picks]) * rng.uniform(0.84, 1.08, (count, 1))


def granite_grains(seed):
    dark = cover(speckle(seed, 0.8), 0.06, 0.5) * 0.6
    light = cover(speckle(seed + 1, 1.0), 0.12, 0.5) * 0.6
    pink = cover(speckle(seed + 2, 1.4), 0.3, 0.6)
    return dark, light, pink


def lichens(seed, mask, amount):
    crust = patchy(seed, 0.08 * amount, 14.0, 300.0, 0.9) * mask
    orange = patchy(seed + 2, 0.015 * amount, 40.0, 400.0, 0.7) * mask
    black = patchy(seed + 4, 0.02 * amount, 50.0, 450.0, 0.6) * mask
    return crust, orange, black


def apply_lichen(albedo, seed, crust, orange, black):
    grain = (0.85 + 0.3 * unit(speckle(seed, 1.4)))[:, :, None]
    albedo = mix(albedo, linear(158, 164, 140) * grain, crust * 0.72)
    albedo = mix(albedo, linear(186, 128, 44) * grain, orange * 0.8)
    return mix(albedo, linear(34, 33, 30), black * 0.75)


def rubble_sites(rng, tile):
    heights = []
    total = 0.0
    while total < tile - 0.1:
        h = rng.uniform(0.11, 0.28)
        heights.append(h)
        total += h
    heights = np.array(heights) * tile / sum(heights)
    sites = []
    y = 0.0
    for h in heights:
        steps = []
        run = 0.0
        while run < tile - 0.12:
            step = rng.uniform(0.17, 0.5) * (h / 0.2) ** 0.6
            steps.append(step)
            run += step
        steps = np.array(steps) * tile / sum(steps)
        x = rng.uniform(0.0, tile)
        for step in steps:
            cx = x + step * 0.5 + rng.uniform(-0.1, 0.1) * step
            cy = y + h * 0.5 + rng.uniform(-0.09, 0.09) * h
            if h > 0.22 and rng.random() < 0.22:
                sites.append((cx % tile, (y + h * 0.27) % tile))
                sites.append(((cx + rng.uniform(-0.05, 0.05)) % tile, (y + h * 0.75) % tile))
            else:
                sites.append((cx % tile, cy % tile))
            if rng.random() < 0.12:
                sites.append(((x + rng.uniform(-0.03, 0.03)) % tile, (y + h * rng.choice([0.08, 0.92])) % tile))
            x += step
        y += h
    return sites


def stone_field(seed, tile, sites, joint, amp, fall, tilt, edge_amount, stretch=1.0, rounding=0.0):
    rng = np.random.default_rng(seed)
    ident, edge, ax, ay = site_voronoi(sites, tile, stretch, rounding)
    count = len(sites)
    half = rng.uniform(joint[0], joint[1], count)[ident]
    rough_edge = field(seed + 1, 24.0, 380.0, 1.3) * edge_amount + field(seed + 2, 4.0, 60.0, 2.0) * edge_amount * 0.8
    depth = edge - half + rough_edge
    stone = depth > 0.0
    a = rng.uniform(amp[0], amp[1], count)[ident]
    f = rng.uniform(fall[0], fall[1], count)[ident]
    t = np.clip(depth / f, 0.0, 1.0)
    su = rng.uniform(-tilt, tilt, count)[ident]
    sv = rng.uniform(-tilt, tilt, count)[ident]
    bumps = field(seed + 3, 6.0, 260.0, 1.8)
    profile = a * (1.0 - (1.0 - t) ** 2.3) + ax * su + ay * sv + bumps * 0.0028 * t
    return ident, stone, np.maximum(depth, 0.0), profile


def make_rubble():
    tile = 2.4
    seed = 1100
    rng = np.random.default_rng(seed)
    sites = rubble_sites(rng, tile)
    count = len(sites)
    ident, stone, depth, profile = stone_field(seed + 10, tile, sites, (0.005, 0.011), (0.012, 0.03), (0.014, 0.034), 0.03, 0.0035, 2.4, 0.012)
    colors = granite_palette(np.random.default_rng(seed + 20), count)
    pinkness = np.random.default_rng(seed + 21).uniform(0.0, 1.0, count)[ident]
    base = colors[ident]
    base = tint(base, 0.8 + 0.34 * unit(field(seed + 22, 5.0, 80.0, 2.0)))
    base = tint(base, 0.84 + 0.2 * unit(field(seed + 23, 1.5, 14.0, 2.2)))
    dark, light, pink = granite_grains(seed + 30)
    albedo = tint(base, 1.0 - 0.45 * dark)
    albedo = mix(albedo, linear(200, 192, 180), light * 0.28)
    albedo = mix(albedo, linear(190, 132, 116), pink * 0.28 * pinkness)
    rim = sstep(0.01, 0.0, depth) * stone
    albedo = mix(albedo, albedo * 1.08, rim * 0.5)
    mortar_height = -0.012 + 0.0016 * field(seed + 40, 40.0, 500.0, 1.2) - 0.005 * patchy(seed + 41, 0.3, 6.0, 120.0)
    height = np.where(stone, profile, mortar_height)
    sand = speckle(seed + 42, 0.8)
    mortar = flat(linear(134, 126, 110)) * (0.6 + 0.3 * unit(field(seed + 43, 4.0, 80.0, 2.0)))[:, :, None] * (1.0 + 0.1 * sand)[:, :, None]
    albedo = np.where(stone[:, :, None], albedo, mortar)
    crust, orange, black = lichens(seed + 50, stone, 1.3)
    albedo = apply_lichen(albedo, seed + 55, crust, orange, black)
    streaks = cover(field(seed + 60, 2.0, 90.0, 2.0, 1.0, 7.0), 0.3, 0.4)
    albedo = tint(albedo, 1.0 - 0.22 * streaks)
    stain = patchy(seed + 61, 0.18, 3.0, 60.0, 1.0, 0.5)
    albedo = mix(albedo, albedo * np.array([0.62, 0.6, 0.56]), stain * 0.6)
    grime = cavity(height, 3.0, 0.008)
    albedo = tint(albedo, 1.0 - 0.5 * grime)
    moss = patchy(seed + 70, 0.1, 8.0, 200.0) * (~stone)
    albedo = mix(albedo, linear(58, 74, 26) * (0.7 + 0.5 * unit(speckle(seed + 71, 1.2)))[:, :, None], moss * 0.85)
    height = height + moss * 0.005 * unit(speckle(seed + 72, 1.5))
    rough = np.where(stone, 0.78 + 0.05 * field(seed + 80, 8.0, 200.0) - 0.1 * light, 0.93)
    rough = mix(rough, 0.9, crust)
    occlusion = 1.0 - 0.5 * cavity(height, 2.0, 0.006) - 0.3 * cavity(height, 9.0, 0.014)
    save("granite_rubble", albedo, rough, occlusion, height, tile, 0.8, extra={"kind": "world"})
    wet = unit(field(seed + 90, 2.0, 40.0, 2.0))
    algae = patchy(seed + 91, 0.45, 5.0, 120.0, 1.0, 0.4)
    damp = tint(albedo, 0.58 + 0.1 * wet)
    damp = mix(damp, linear(52, 62, 40), algae * 0.5 * stone)
    cushion = np.clip(patchy(seed + 93, 0.5, 8.0, 200.0, 0.8, 0.3) * (~stone) + patchy(seed + 95, 0.12, 10.0, 200.0, 0.8, 0.3) * stone, 0.0, 1.0)
    moss_color = mix(linear(66, 90, 26), linear(34, 50, 16), unit(field(seed + 94, 20.0, 400.0, 1.5)))
    damp = mix(damp, moss_color * (0.75 + 0.5 * unit(speckle(seed + 96, 1.0)))[:, :, None], cushion * 0.92)
    damp_height = height + cushion * (0.006 + 0.004 * unit(speckle(seed + 97, 1.6)))
    damp_rough = mix(rough * 0.7, 0.94, cushion)
    damp_occlusion = 1.0 - 0.5 * cavity(damp_height, 2.0, 0.006) - 0.3 * cavity(damp_height, 9.0, 0.014)
    save("granite_rubble_damp", damp, damp_rough, damp_occlusion, damp_height, tile, 0.8, extra={"kind": "world"})


def make_ashlar():
    tile = 1.6
    seed = 1200
    dark, light, pink = granite_grains(seed)
    base = mix(linear(142, 120, 108), linear(124, 118, 112), unit(field(seed + 3, 1.5, 20.0, 2.2)))
    base = tint(base, 0.82 + 0.3 * unit(field(seed + 5, 4.0, 80.0, 1.8)))
    base = mix(base, base * np.array([0.6, 0.6, 0.57]), patchy(seed + 16, 0.22, 2.5, 50.0, 1.0, 0.6) * 0.65)
    albedo = tint(base, 1.0 - 0.45 * dark)
    albedo = mix(albedo, linear(204, 196, 186), light * 0.3)
    albedo = mix(albedo, linear(190, 134, 118), pink * 0.26)
    first, second, ident = voronoi(170, 170, seed + 6, 0.9)
    pecks = sstep(0.0, 2.2, first) * 0.0005
    lines = np.sin((grid_u + grid_v * 0.35) / size * math.pi * 2.0 * 220.0 + field(seed + 7, 2.0, 40.0) * 2.0) * 0.0002
    height = pecks + lines + field(seed + 8, 2.0, 60.0, 2.2) * 0.0014 + field(seed + 9, 60.0, 400.0, 1.2) * 0.00025
    crust, orange, black = lichens(seed + 10, np.ones((size, size)), 1.4)
    albedo = apply_lichen(albedo, seed + 14, crust, orange, black)
    rust = cover(field(seed + 11, 3.0, 50.0, 2.0, 1.0, 5.0), 0.04, 0.4)
    albedo = mix(albedo, linear(128, 78, 44), rust * 0.3)
    streaks = cover(field(seed + 12, 3.0, 90.0, 2.0, 1.0, 6.0), 0.28, 0.4)
    albedo = tint(albedo, 1.0 - 0.22 * streaks)
    chips = patchy(seed + 13, 0.025, 25.0, 300.0, 0.4)
    albedo = mix(albedo, linear(206, 178, 166), chips * 0.6)
    height = height - chips * 0.002
    rough = 0.76 + 0.04 * field(seed + 15, 6.0, 200.0) - 0.1 * light + 0.1 * crust
    occlusion = 1.0 - 0.45 * cavity(height, 2.0, 0.0012)
    save("granite_ashlar", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "local"})


def cracks(seed, cells, width, keep):
    first, second, ident = voronoi(cells, cells, seed, 0.95)
    rng = np.random.default_rng(seed + 1)
    border = (second - first) * 0.5 + field(seed + 2, 10.0, 200.0, 1.5) * 1.5
    active = rng.random(cells * cells) < keep
    line = sstep(width, 0.0, border) * active[ident]
    return line * cover(field(seed + 3, 3.0, 50.0, 2.0), 0.45, 0.5)


def make_render(name, wash, under, seed):
    tile = 2.5
    base = flat(linear(156, 150, 138)) * (0.86 + 0.22 * unit(field(seed, 3.0, 80.0, 2.0)))[:, :, None]
    base = base * (1.0 + 0.12 * speckle(seed + 1, 0.7))[:, :, None]
    thickness = unit(field(seed + 2, 2.0, 60.0, 2.0))
    coat = flat(wash) * (0.94 + 0.08 * thickness)[:, :, None]
    coat = coat * (1.0 + 0.03 * field(seed + 3, 6.0, 200.0, 1.6, 1.0, 0.3))[:, :, None]
    lower = flat(under) * (0.92 + 0.1 * unit(field(seed + 4, 3.0, 60.0, 2.0)))[:, :, None]
    peel_field = field(seed + 5, 3.5, 160.0, 1.9) + 0.35 * field(seed + 6, 20.0, 300.0, 1.5)
    old = cover(peel_field, 0.1, 0.03)
    bare = cover(peel_field, 0.035, 0.03)
    albedo = mix(coat, lower, old)
    albedo = mix(albedo, base, bare)
    lip = np.clip(old * (1.0 - old) * 4.0 + bare * (1.0 - bare) * 4.0, 0.0, 1.0)
    albedo = mix(albedo, albedo * 0.75, lip * 0.5)
    streaks = cover(field(seed + 7, 1.5, 70.0, 2.0, 1.0, 9.0), 0.34, 0.45)
    albedo = mix(albedo, albedo * np.array([0.68, 0.64, 0.56]), streaks * 0.5)
    albedo = tint(albedo, 0.84 + 0.16 * unit(field(seed + 17, 1.0, 12.0, 2.2)))
    algae = patchy(seed + 8, 0.2, 1.2, 30.0, 0.6, 0.6, 2.2)
    albedo = mix(albedo, albedo * np.array([0.66, 0.72, 0.58]), algae * 0.45)
    speck = cover(speckle(seed + 10, 1.2), 0.1, 0.3) * cover(field(seed + 11, 3.0, 60.0, 2.0), 0.3, 0.4)
    albedo = mix(albedo, linear(44, 46, 38), speck * 0.55)
    crack = cracks(seed + 12, 7, 1.1, 0.45)
    albedo = mix(albedo, linear(64, 60, 54), crack * 0.8)
    height = field(seed + 13, 1.5, 30.0, 2.4) * 0.0025 + speckle(seed + 14, 0.8) * 0.00012 + field(seed + 15, 40.0, 400.0, 1.2) * 0.00015
    height = height - old * 0.0004 - bare * 0.0012 + lip * 0.00025 - crack * 0.0008
    rough = 0.9 + 0.03 * field(seed + 16, 5.0, 100.0) - 0.04 * old + 0.04 * bare
    occlusion = 1.0 - 0.45 * cavity(height, 2.0, 0.0006) - 0.2 * crack
    save(name, albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "world"})


def make_plaster():
    tile = 2.5
    seed = 1400
    base = flat(linear(200, 190, 168)) * (0.9 + 0.12 * unit(field(seed, 2.0, 40.0, 2.0)))[:, :, None]
    base = base * (1.0 + 0.04 * speckle(seed + 1, 0.8))[:, :, None]
    distemper = flat(linear(204, 200, 182)) * (0.94 + 0.08 * unit(field(seed + 4, 2.0, 40.0)))[:, :, None]
    flake_field = field(seed + 2, 6.0, 200.0, 1.7) + 0.4 * field(seed + 3, 30.0, 350.0, 1.4) + 0.7 * field(seed + 13, 1.5, 10.0, 2.2)
    bare = cover(flake_field, 0.12, 0.03)
    albedo = mix(distemper, base * 0.92, bare)
    lip = np.clip(bare * (1.0 - bare) * 4.0, 0.0, 1.0)
    albedo = mix(albedo, albedo * 0.8, lip * 0.5)
    stain_field = field(seed + 5, 1.2, 25.0, 2.3)
    stain = cover(stain_field, 0.1, 0.35)
    threshold = float(np.quantile(stain_field, 0.9))
    ring = sstep(0.1, 0.0, np.abs(stain_field - threshold))
    albedo = mix(albedo, albedo * np.array([0.84, 0.76, 0.62]), stain * 0.45)
    albedo = mix(albedo, albedo * np.array([0.66, 0.56, 0.42]), ring * 0.4)
    mold = cover(speckle(seed + 6, 1.3), 0.12, 0.3) * cover(field(seed + 7, 2.0, 40.0, 2.0), 0.18, 0.4)
    albedo = mix(albedo, linear(52, 58, 48), mold * 0.7)
    grime = cover(field(seed + 8, 1.0, 50.0, 2.0, 1.0, 5.0), 0.3, 0.5)
    albedo = tint(albedo, 1.0 - 0.16 * grime)
    crack = cracks(seed + 9, 6, 1.0, 0.4)
    albedo = mix(albedo, linear(74, 68, 60), crack * 0.8)
    height = field(seed + 10, 1.5, 40.0, 2.4) * 0.0015 + speckle(seed + 11, 0.8) * 0.0001 + (1.0 - bare) * 0.0002 + lip * 0.0002 - crack * 0.0007
    rough = 0.88 + 0.03 * field(seed + 12, 4.0, 80.0) + 0.05 * bare
    occlusion = 1.0 - 0.4 * cavity(height, 2.0, 0.0005) - 0.25 * crack
    save("plaster_interior", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "world"})


def motif(lu, lv, cx, cy, radius, lobes, phase):
    r = np.hypot(lu - cx, lv - cy)
    theta = np.arctan2(lv - cy, lu - cx) + phase
    return radius * (0.62 + 0.38 * np.abs(np.cos(theta * lobes * 0.5))) - r


def make_wallpaper():
    tile = 1.0
    seed = 1500
    ground = mix(linear(216, 200, 164), linear(204, 190, 154), unit(field(seed, 2.0, 30.0)))
    stripe_u = (grid_u / size * 16.0) % 1.0
    stripes = sstep(0.035, 0.0, np.abs(stripe_u - 0.5)) * 0.5 + sstep(0.012, 0.0, np.abs(stripe_u - 0.08)) * 0.35
    albedo = mix(ground, linear(172, 146, 98), stripes)
    rose = np.zeros((size, size))
    leaf = np.zeros((size, size))
    heart = np.zeros((size, size))
    step = size / 4.0
    for column in range(4):
        for row in range(4):
            cx = (column + 0.5) * step
            cy = (row + 0.5 + (0.5 if column % 2 else 0.0)) * step
            lu = cx + ((grid_u - cx) + size * 0.5) % size - size * 0.5
            lv = cy + ((grid_v - cy) + size * 0.5) % size - size * 0.5
            rose = np.maximum(rose, sstep(-1.5, 1.5, motif(lu, lv, cx, cy, step * 0.2, 5, column * 0.7 + row)))
            heart = np.maximum(heart, sstep(-1.0, 1.0, motif(lu, lv, cx, cy, step * 0.09, 5, column + row * 0.3 + 0.6)))
            for angle in (0.6, 2.5, 4.2):
                a = angle + column
                lx = cx + math.cos(a) * step * 0.3
                ly = cy + math.sin(a) * step * 0.3
                ex = (lu - lx) * math.cos(a) + (lv - ly) * math.sin(a)
                ey = -(lu - lx) * math.sin(a) + (lv - ly) * math.cos(a)
                leaf = np.maximum(leaf, sstep(-0.05, 0.08, 1.0 - np.hypot(ex / (step * 0.13), ey / (step * 0.055))))
    ink = (0.85 + 0.2 * unit(speckle(seed + 1, 1.0)))[:, :, None]
    albedo = mix(albedo, linear(128, 148, 104) * ink, leaf * 0.85)
    albedo = mix(albedo, linear(184, 108, 104) * ink, rose * 0.85)
    albedo = mix(albedo, linear(140, 70, 70), heart * 0.85)
    fade = unit(field(seed + 2, 1.2, 20.0, 2.2))
    albedo = mix(albedo, ground * 1.02, 0.18 + 0.3 * fade)
    seam = sstep(2.5, 0.0, np.minimum(grid_u % (size * 0.5), size * 0.5 - grid_u % (size * 0.5)))
    albedo = mix(albedo, albedo * 0.76, seam * 0.8)
    stain_field = field(seed + 3, 1.3, 25.0, 2.3)
    stain = cover(stain_field, 0.16, 0.2)
    threshold = float(np.quantile(stain_field, 0.84))
    ring = sstep(0.12, 0.0, np.abs(stain_field - threshold))
    albedo = mix(albedo, albedo * np.array([0.8, 0.66, 0.46]), stain * 0.55)
    albedo = mix(albedo, albedo * np.array([0.55, 0.42, 0.28]), ring * 0.5)
    mold = cover(speckle(seed + 4, 1.2), 0.12, 0.3) * cover(field(seed + 5, 2.0, 30.0, 2.0), 0.15, 0.4)
    albedo = mix(albedo, linear(52, 54, 44), mold * 0.7)
    grime = cover(field(seed + 6, 1.0, 40.0, 2.0, 1.0, 4.0), 0.3, 0.5)
    albedo = tint(albedo, 1.0 - 0.18 * grime)
    height = field(seed + 7, 2.0, 50.0, 2.2) * 0.0004 + speckle(seed + 8, 0.7) * 0.00005 + seam * 0.0003
    rough = 0.82 + 0.04 * field(seed + 9, 3.0, 60.0) + 0.06 * stain
    occlusion = 1.0 - 0.3 * cavity(height, 2.0, 0.0002)
    save("wallpaper_faded", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "world"})


def board_layout(rng, tile, low, high):
    widths = []
    total = 0.0
    while total < tile - low * 0.5:
        w = rng.uniform(low, high)
        widths.append(w)
        total += w
    widths = np.array(widths) * tile / sum(widths)
    edges = np.concatenate([[0.0], np.cumsum(widths)]) / tile
    edges[-1] = 1.0
    return [(float(edges[i]), float(edges[i + 1])) for i in range(len(widths))]


def board_fields(seed, boards, gap_px, ends):
    rng = np.random.default_rng(seed)
    index = np.zeros((size, size), np.int64)
    across = np.zeros((size, size))
    for number, (v0, v1) in enumerate(boards):
        r0 = int(round(v0 * size))
        r1 = int(round(v1 * size))
        index[r0:r1, :] = number
        across[r0:r1, :] = ((np.arange(r0, r1) + 0.5 - r0) / max(r1 - r0, 1))[:, None]
    shift = rng.integers(0, size, len(boards))
    lengthwise = (grid_u + shift[index]) % size
    gap = gap_px / 2.0
    width_px = np.array([(b[1] - b[0]) * size for b in boards])[index]
    edge_distance = np.minimum(across, 1.0 - across) * width_px
    joint = sstep(gap + 1.2, gap, edge_distance)
    if ends:
        cut_at = rng.uniform(0.0, size, len(boards))
        has_cut = rng.random(len(boards)) < ends
        distance = np.abs(((grid_u - cut_at[index]) + size * 0.5) % size - size * 0.5)
        joint = np.maximum(joint, sstep(gap + 1.2, gap, distance) * has_cut[index])
    return index, across, lengthwise, edge_distance, joint, width_px


def grain_pattern(seed, lengthwise, across, index, width_px, rings, knot_chance, count):
    rng = np.random.default_rng(seed)
    bend = np.zeros((size, size))
    knot = np.zeros((size, size))
    for board in range(count):
        for attempt in range(3):
            if rng.random() > knot_chance:
                continue
            ku = rng.uniform(0, size)
            kv = rng.uniform(0.2, 0.8)
            radius = rng.uniform(4.0, 11.0)
            mask = index == board
            du = ((lengthwise - ku) + size * 0.5) % size - size * 0.5
            dv = (across - kv) * width_px
            influence = np.exp(-(np.hypot(du / 2.6, dv) / (radius * 2.4)) ** 2) * mask
            bend += influence * np.sign(dv + 1e-6) * radius * 1.4
            knot = np.maximum(knot, sstep(radius * 0.55, radius * 0.25, np.hypot(du / 1.5, dv)) * mask)
    wave = field(seed + 1, 1.0, 30.0, 2.2) * 5.0
    phase = (across * width_px + bend + wave + field(seed + 2, 0.5, 8.0, 2.0, 3.0, 1.0) * 3.0) / rings + index * 3.7
    late = sstep(0.55, 0.95, 0.5 + 0.5 * np.sin(phase * 2.0 * math.pi))
    fibre = field(seed + 3, 2.0, 700.0, 1.2, 14.0, 0.7)
    return late, knot, fibre


def make_planks():
    tile = 2.0
    seed = 1600
    boards = board_layout(np.random.default_rng(seed), tile, 0.15, 0.28)
    index, across, lengthwise, edge_distance, joint, width_px = board_fields(seed + 1, boards, 3.0, 0.0)
    late, knot, fibre = grain_pattern(seed + 2, lengthwise, across, index, width_px, 7.0, 0.5, len(boards))
    tone = np.random.default_rng(seed + 3).uniform(0.78, 1.18, len(boards))[index]
    warmth = np.random.default_rng(seed + 4).uniform(0.0, 1.0, len(boards))[index]
    grey = mix(linear(140, 134, 124), linear(128, 108, 86), warmth * 0.6)
    albedo = tint(grey, tone * (0.9 + 0.1 * fibre))
    albedo = mix(albedo, albedo * 0.62, late * 0.55)
    albedo = mix(albedo, linear(58, 46, 36), knot * 0.85)
    weather = cover(field(seed + 5, 1.5, 40.0, 2.0, 2.0, 1.0), 0.35, 0.5)
    albedo = mix(albedo, albedo * np.array([1.08, 1.08, 1.1]), weather * 0.4)
    stain = cover(field(seed + 6, 1.0, 30.0, 2.0, 1.0, 5.0), 0.25, 0.5)
    albedo = tint(albedo, 1.0 - 0.25 * stain)
    check = cover(field(seed + 7, 1.0, 300.0, 1.4, 30.0, 0.6), 0.04, 0.2) * cover(field(seed + 8, 2.0, 40.0, 2.0, 4.0, 1.0), 0.5, 0.5)
    albedo = mix(albedo, linear(30, 26, 22), check * 0.9)
    lichen = patchy(seed + 9, 0.04, 25.0, 300.0, 0.8)
    albedo = mix(albedo, linear(150, 158, 128), lichen * 0.6)
    nail = np.zeros((size, size))
    halo = np.zeros((size, size))
    for nu in np.array([0.1, 0.5, 0.9]) * size:
        for fraction in (0.28, 0.72):
            du = ((grid_u - nu - (index * 7) % 5) + size * 0.5) % size - size * 0.5
            dv = (across - fraction) * width_px
            nail = np.maximum(nail, sstep(3.2, 2.0, np.hypot(du, dv)))
            halo = np.maximum(halo, sstep(9.0, 2.0, np.hypot(du * 1.6, np.minimum(dv, 0.0) * 0.4)))
    albedo = mix(albedo, linear(96, 56, 30), halo * 0.35)
    albedo = mix(albedo, linear(60, 34, 20), nail * 0.9)
    albedo = mix(albedo, linear(10, 9, 8), joint)
    height = -late * 0.0009 + fibre * 0.00018 - knot * 0.0004 - check * 0.0012 - joint * 0.006 - nail * 0.0005
    height += sstep(0.0, 5.0, edge_distance) * 0.0015 - 0.0015
    rough = 0.86 + 0.05 * fibre - 0.05 * late + 0.06 * joint
    occlusion = 1.0 - 0.7 * joint - 0.35 * cavity(height, 2.0, 0.001) - 0.3 * check
    save("timber_planks_weathered", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "boards", "boards": boards})


def make_floorboards():
    tile = 2.0
    seed = 1700
    boards = board_layout(np.random.default_rng(seed), tile, 0.12, 0.19)
    index, across, lengthwise, edge_distance, joint, width_px = board_fields(seed + 1, boards, 2.5, 0.45)
    late, knot, fibre = grain_pattern(seed + 2, lengthwise, across, index, width_px, 5.0, 0.5, len(boards))
    tone = np.random.default_rng(seed + 3).uniform(0.78, 1.18, len(boards))[index]
    base = mix(linear(108, 86, 64), linear(90, 72, 56), unit(field(seed + 4, 1.0, 20.0)))
    albedo = tint(base, tone * (0.92 + 0.08 * fibre))
    albedo = mix(albedo, albedo * 0.6, late * 0.6)
    albedo = mix(albedo, linear(40, 28, 18), knot * 0.85)
    dirt = cover(field(seed + 5, 1.5, 40.0, 2.0), 0.4, 0.6)
    albedo = mix(albedo, albedo * np.array([0.74, 0.72, 0.7]), dirt * 0.6)
    worn = cover(field(seed + 6, 1.2, 20.0, 2.2, 2.0, 1.0), 0.2, 0.5)
    albedo = mix(albedo, albedo * np.array([1.18, 1.14, 1.08]), worn * 0.5)
    water_field = field(seed + 7, 1.5, 30.0, 2.2)
    stain = cover(water_field, 0.12, 0.2)
    ring = sstep(0.12, 0.0, np.abs(water_field - float(np.quantile(water_field, 0.88))))
    albedo = mix(albedo, albedo * 0.72, stain * 0.5)
    albedo = mix(albedo, albedo * 0.52, ring * 0.45)
    nail = np.zeros((size, size))
    for joist in range(5):
        nu = (joist + 0.5) * size / 5.0
        for fraction in (0.22, 0.78):
            du = ((grid_u - nu - (index * 5) % 4) + size * 0.5) % size - size * 0.5
            nail = np.maximum(nail, sstep(2.6, 1.4, np.hypot(du, (across - fraction) * width_px)))
    albedo = mix(albedo, linear(24, 20, 18), nail * 0.9)
    albedo = mix(albedo, linear(8, 7, 6), joint)
    height = -late * 0.0005 + fibre * 0.0001 - knot * 0.0003 - joint * 0.005 - nail * 0.0003 + sstep(0.0, 4.0, edge_distance) * 0.001 - 0.001
    rough = 0.74 + 0.06 * fibre + 0.1 * dirt - 0.14 * worn + 0.1 * joint
    occlusion = 1.0 - 0.75 * joint - 0.3 * cavity(height, 2.0, 0.0008)
    save("floorboards", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "boards", "boards": boards})


def make_painted(name, paint, primer, seed):
    tile = 1.0
    boards = board_layout(np.random.default_rng(seed), tile, 0.09, 0.16)
    index, across, lengthwise, edge_distance, joint, width_px = board_fields(seed + 1, boards, 2.5, 0.0)
    late, knot, fibre = grain_pattern(seed + 2, lengthwise, across, index, width_px, 6.0, 0.35, len(boards))
    wood = tint(flat(linear(124, 116, 104)), 0.9 + 0.1 * fibre)
    wood = mix(wood, wood * 0.6, late * 0.6)
    chalky = mix(flat(paint), flat(linear(206, 208, 200)), 0.22)
    coat = mix(flat(paint), chalky, unit(field(seed + 4, 1.2, 8.0, 2.3)) * 0.7)
    coat = tint(coat, 0.95 + 0.07 * unit(field(seed + 5, 4.0, 200.0, 1.6, 0.3, 1.0)))
    flake_field = 1.25 * field(seed + 12, 1.5, 9.0, 2.3) + 0.7 * field(seed + 6, 8.0, 260.0, 1.6, 3.0, 1.0) + 0.3 * field(seed + 7, 40.0, 450.0, 1.3, 4.0, 1.0) + 0.25 * late
    under = cover(flake_field, 0.11, 0.025)
    bare = cover(flake_field, 0.065, 0.025)
    alligator = cracks(seed + 8, 22, 0.9, 0.8)
    albedo = mix(coat, flat(primer) * (0.9 + 0.1 * unit(speckle(seed + 9, 1.0)))[:, :, None], under)
    albedo = mix(albedo, wood, bare)
    edge = np.clip(under * (1.0 - under) * 4.0 + bare * (1.0 - bare) * 4.0, 0.0, 1.0)
    albedo = mix(albedo, albedo * 0.72, edge * 0.5)
    albedo = mix(albedo, albedo * 0.6, alligator * (1.0 - bare) * 0.6)
    grime = cover(field(seed + 10, 1.5, 40.0, 2.0, 1.0, 3.0), 0.3, 0.5)
    albedo = tint(albedo, 1.0 - 0.22 * grime)
    albedo = mix(albedo, linear(10, 9, 8), joint)
    height = 0.0003 * (1.0 - bare) + 0.00015 * (1.0 - under) + edge * 0.0002 - late * bare * 0.0005 - alligator * 0.0002 - joint * 0.004
    height += sstep(0.0, 4.0, edge_distance) * 0.001 + fibre * 0.00005
    rough = mix(mix(0.55 + 0.08 * unit(field(seed + 11, 3.0, 60.0)), 0.7, under), 0.86, bare) + 0.1 * grime
    occlusion = 1.0 - 0.7 * joint - 0.3 * cavity(height, 1.5, 0.0004)
    save(name, albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "boards", "boards": boards})


def make_beam():
    tile = 2.0
    seed = 1800
    along = field(seed, 0.5, 20.0, 2.0, 4.0, 1.0)
    late = sstep(0.4, 0.95, 0.5 + 0.5 * np.sin((grid_v / size * 34.0 + along * 0.6 + field(seed + 1, 1.0, 10.0, 2.0, 6.0, 1.0) * 0.4) * 2.0 * math.pi))
    fibre = field(seed + 2, 2.0, 700.0, 1.2, 16.0, 0.7)
    base = mix(linear(98, 74, 52), linear(78, 58, 42), unit(field(seed + 3, 1.0, 20.0, 2.0, 2.0, 1.0)))
    albedo = tint(base, 0.9 + 0.1 * fibre)
    albedo = mix(albedo, albedo * 0.6, late * 0.5)
    flecks = cover(field(seed + 4, 20.0, 500.0, 1.4, 0.3, 3.0), 0.12, 0.3)
    albedo = mix(albedo, albedo * 1.25, flecks * 0.35)
    adze = ((grid_u / size * 24.0 + field(seed + 5, 1.0, 12.0, 2.0) * 0.4) % 1.0 - 0.5) ** 2 * 4.0
    adze_mask = cover(field(seed + 6, 1.5, 20.0, 2.0), 0.5, 0.6)
    check = cover(field(seed + 7, 1.0, 300.0, 1.4, 40.0, 0.6), 0.03, 0.2)
    albedo = mix(albedo, linear(22, 16, 12), check * 0.95)
    worm = cover(speckle(seed + 8, 0.9), 0.04, 0.3) * cover(field(seed + 9, 3.0, 40.0), 0.25, 0.4)
    albedo = mix(albedo, linear(20, 15, 10), worm * 0.9)
    dust = cover(field(seed + 10, 1.5, 30.0, 2.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * np.array([1.15, 1.12, 1.1]), dust * 0.35)
    height = adze * adze_mask * 0.0025 - late * 0.0004 + fibre * 0.00015 - check * 0.003 - worm * 0.0008 + field(seed + 11, 1.0, 20.0, 2.0) * 0.001
    rough = 0.74 + 0.06 * fibre + 0.1 * dust - 0.06 * late
    occlusion = 1.0 - 0.4 * cavity(height, 2.0, 0.0012) - 0.5 * check
    save("timber_beam", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "local"})


def make_charred():
    tile = 0.8
    seed = 1900
    first, second, ident = voronoi(10, 34, seed, 0.9)
    border = (second - first) * 0.5 + field(seed + 1, 20.0, 300.0, 1.5) * 1.2
    crack = sstep(2.6, 0.6, border)
    block = sstep(0.0, 9.0, border)
    lift = np.random.default_rng(seed + 2).uniform(0.6, 1.2, 10 * 34)[ident]
    albedo = flat(linear(22, 21, 20)) * (0.8 + 0.4 * unit(field(seed + 3, 10.0, 300.0, 1.6)))[:, :, None]
    sheen = cover(field(seed + 4, 6.0, 120.0, 1.8), 0.3, 0.5)
    albedo = mix(albedo, linear(48, 46, 44), sheen * 0.4)
    ember = cover(field(seed + 5, 1.5, 30.0, 2.0, 3.0, 1.0), 0.15, 0.5)
    albedo = mix(albedo, linear(72, 46, 26), ember * 0.45 * (1.0 - crack))
    ash = cover(field(seed + 6, 20.0, 400.0, 1.6), 0.3, 0.5) * crack
    albedo = mix(albedo, linear(140, 136, 128), ash * 0.6)
    albedo = mix(albedo, linear(4, 4, 4), crack * (1.0 - ash) * 0.9)
    height = block * lift * 0.004 - crack * 0.003 + field(seed + 7, 30.0, 500.0, 1.3, 3.0, 1.0) * 0.0003
    rough = 0.82 - 0.3 * sheen + 0.1 * crack
    occlusion = 1.0 - 0.7 * crack - 0.3 * cavity(height, 3.0, 0.002)
    save("timber_charred", albedo, rough, occlusion, height, tile, 0.9, extra={"kind": "local"})


def cell_tiles(seed, columns, courses, stagger, gap_u_px, chip):
    rng = np.random.default_rng(seed)
    cell_u = size / columns
    cell_v = size / courses
    index = np.full((size, size), -1, np.int64)
    local_u = np.zeros((size, size))
    local_v = np.zeros((size, size))
    edge = np.zeros((size, size))
    cells = []
    noise = field(seed + 1, 30.0, 400.0, 1.4)
    for course in range(courses):
        offset = cell_u * 0.5 * (course % 2) * stagger
        for column in range(columns):
            u0 = column * cell_u + offset
            u1 = u0 + cell_u
            v0 = course * cell_v
            v1 = v0 + cell_v
            c = rng.uniform(0.0, chip)
            d = rng.uniform(0.0, chip)
            left = u0 + gap_u_px * 0.5
            right = u1 - gap_u_px * 0.5
            points = [(left, v0 + c), (left + c * 1.3, v0), (right - d * 1.3, v0), (right, v0 + d), (right, v1 + 4.0), (left, v1 + 4.0)]
            where, lu, lv = window(points, 3)
            sdf = polygon_sdf(lu, lv, points) + noise[where] * 0.8
            inside = (sdf < 0.0) & (lv < v1)
            index[where] = np.where(inside, course * columns + column, index[where])
            local_u[where] = np.where(inside, (lu - u0) / cell_u, local_u[where])
            local_v[where] = np.where(inside, (lv - v0) / cell_v, local_v[where])
            edge[where] = np.where(inside, -sdf, edge[where])
            if u1 <= size:
                cells.append([float(left / size), float(right / size), float(v0 / size), float(v1 / size)])
    return index, local_u, local_v, edge, cells


def make_slates():
    tile = 1.2
    seed = 2000
    columns = 4
    courses = 6
    index, local_u, local_v, edge, cells = cell_tiles(seed, columns, courses, True, 3.5, 9.0)
    slate = index >= 0
    count = courses * columns
    rng = np.random.default_rng(seed + 5)
    palette = np.array([linear(60, 64, 72), linear(66, 62, 70), linear(60, 66, 64), linear(72, 74, 78), linear(54, 56, 62), linear(80, 80, 83)])
    picks = palette[rng.choice(len(palette), count, p=[0.34, 0.18, 0.14, 0.14, 0.14, 0.06])] * rng.uniform(0.9, 1.1, (count, 1))
    base = picks[np.maximum(index, 0)]
    cleavage = field(seed + 6, 4.0, 500.0, 1.3, 0.25, 1.0)
    albedo = tint(base, 0.93 + 0.07 * cleavage)
    weathered = cover(field(seed + 7, 2.0, 60.0, 2.0), 0.3, 0.6)
    albedo = mix(albedo, albedo * np.array([1.25, 1.25, 1.2]), weathered * 0.35)
    near_butt = sstep(0.8, 0.1, local_v)
    crust = patchy(seed + 8, 0.06, 14.0, 300.0, 0.8) * slate * (0.4 + 0.6 * near_butt)
    orange = patchy(seed + 10, 0.01, 40.0, 400.0, 0.6) * slate
    black = patchy(seed + 12, 0.015, 50.0, 400.0, 0.6) * slate
    albedo = apply_lichen(albedo, seed + 14, crust, orange, black)
    rust = cover(field(seed + 15, 3.0, 60.0, 2.0, 1.0, 3.0), 0.05, 0.4) * slate
    albedo = mix(albedo, linear(120, 82, 52), rust * 0.3)
    gap_moss = cover(field(seed + 16, 8.0, 200.0, 1.8), 0.3, 0.4) * (~slate)
    albedo = np.where(slate[:, :, None], albedo, mix(flat(linear(14, 15, 16)), linear(34, 44, 18), gap_moss * 0.6))
    sawtooth = -0.006 * ((grid_v / (size / courses)) % 1.0)
    height = np.where(slate, sawtooth + sstep(0.0, 4.0, edge) * 0.0012 + cleavage * 0.00012 + crust * 0.0002, sawtooth - 0.004)
    under_step = sstep(14.0, 0.0, grid_v % (size / courses))
    rough = np.where(slate, 0.6 + 0.07 * cleavage + 0.2 * crust + 0.1 * weathered, 0.95)
    occlusion = 1.0 - 0.6 * (~slate) - 0.25 * under_step * slate - 0.3 * cavity(height, 2.0, 0.001)
    save("slate_roof", albedo, rough, occlusion, height, tile, 0.9, extra={"kind": "cells", "cells": cells, "columns": columns, "courses": courses})
    clumps = field(seed + 20, 3.0, 60.0, 2.0) + 0.9 * near_butt + 0.6 * (~slate)
    cushion = cover(clumps, 0.38, 0.25)
    inner = cover(clumps, 0.24, 0.4)
    tufts = unit(speckle(seed + 21, 1.8))
    moss_color = mix(linear(68, 84, 30), linear(38, 50, 20), unit(field(seed + 22, 12.0, 300.0, 1.6)))
    moss_color = mix(moss_color, linear(104, 98, 50), cover(field(seed + 23, 6.0, 100.0), 0.2, 0.5) * 0.6)
    mossy = mix(albedo, moss_color * (0.65 + 0.6 * tufts)[:, :, None], cushion * 0.95)
    mossy = mix(mossy, mossy * 0.7, (cushion - inner).clip(0.0, 1.0) * 0.6)
    moss_height = height + cushion * 0.004 + inner * 0.006 + cushion * tufts * 0.003
    moss_rough = mix(rough, 0.95, cushion)
    moss_occlusion = 1.0 - 0.6 * (~slate) * (1.0 - cushion) - 0.4 * cavity(moss_height, 2.5, 0.002)
    save("roof_moss", mossy, moss_rough, moss_occlusion, moss_height, tile, 0.9, extra={"kind": "cells", "cells": cells, "columns": columns, "courses": courses})


def make_pantiles():
    tile = 1.2
    seed = 2100
    columns = 5
    courses = 4
    index, local_u, local_v, edge, cells = cell_tiles(seed, columns, courses, False, 2.0, 6.0)
    tiles = index >= 0
    count = courses * columns
    rng = np.random.default_rng(seed + 5)
    palette = np.array([linear(150, 90, 62), linear(132, 76, 54), linear(160, 106, 78), linear(112, 70, 56), linear(148, 110, 92)])
    picks = palette[rng.choice(len(palette), count, p=[0.32, 0.24, 0.18, 0.14, 0.12])] * rng.uniform(0.84, 1.1, (count, 1))
    base = picks[np.maximum(index, 0)]
    trough = sstep(0.2, -0.8, np.cos(local_u * 2.0 * math.pi))
    albedo = tint(base, 0.9 + 0.12 * unit(field(seed + 6, 8.0, 300.0, 1.5)))
    grime = cover(field(seed + 17, 1.5, 40.0, 2.0), 0.45, 0.6)
    albedo = mix(albedo, linear(98, 86, 76), grime * 0.42)
    albedo = mix(albedo, albedo * np.array([0.72, 0.74, 0.72]), trough * 0.3)
    crust = patchy(seed + 7, 0.11, 14.0, 300.0, 0.8) * tiles
    black = patchy(seed + 9, 0.05, 50.0, 400.0, 0.6) * tiles
    albedo = apply_lichen(albedo, seed + 11, crust, np.zeros((size, size)), black)
    moss = cover(field(seed + 12, 6.0, 200.0, 1.8) + trough * 0.8 + sstep(0.3, 0.0, local_v) * 0.8, 0.1, 0.3) * tiles
    albedo = mix(albedo, linear(60, 78, 24) * (0.7 + 0.6 * unit(speckle(seed + 13, 1.5)))[:, :, None], moss * 0.85)
    albedo = np.where(tiles[:, :, None], albedo, flat(linear(22, 16, 12)))
    sawtooth = -0.008 * ((grid_v / (size / courses)) % 1.0)
    height = np.where(tiles, sawtooth + sstep(0.0, 4.0, edge) * 0.0015 + moss * 0.004 * unit(speckle(seed + 14, 1.5)) + field(seed + 15, 40.0, 500.0, 1.2) * 0.0002, sawtooth - 0.004)
    under_step = sstep(16.0, 0.0, grid_v % (size / courses))
    rough = np.where(tiles, 0.8 + 0.05 * field(seed + 16, 5.0, 100.0) + 0.1 * moss, 0.95)
    occlusion = 1.0 - 0.6 * (~tiles) - 0.3 * under_step * tiles - 0.15 * trough - 0.3 * cavity(height, 2.0, 0.001)
    save("clay_roof_tiles", albedo, rough, occlusion, height, tile, 0.9, extra={"kind": "cells", "cells": cells, "columns": columns, "courses": courses})


def make_tiles():
    tile = 1.2
    seed = 2200
    count = 8
    pitch = size / count
    cu = np.floor(grid_u / pitch).astype(np.int64)
    cv = np.floor(grid_v / pitch).astype(np.int64)
    fu = grid_u / pitch - cu
    fv = grid_v / pitch - cv
    distance = np.minimum(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv)) * pitch
    face = distance > 1.6
    rng = np.random.default_rng(seed)
    ident = cv * count + cu
    shade = rng.uniform(0.92, 1.05, count * count)[ident]
    glaze = mix(linear(224, 218, 198), linear(212, 210, 192), unit(field(seed + 1, 2.0, 40.0)))
    band = cv == 5
    glaze = np.where(band[:, :, None], flat(linear(70, 104, 84)) * (0.9 + 0.1 * unit(field(seed + 2, 6.0, 100.0)))[:, :, None], glaze)
    albedo = tint(glaze, shade)
    craze = cracks(seed + 3, 40, 0.6, 0.9)
    albedo = mix(albedo, albedo * np.array([0.6, 0.55, 0.46]), craze * 0.45)
    chipped = rng.random(count * count) < 0.12
    chip_corner = sstep(9.0, 5.0, np.hypot(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv)) * pitch + field(seed + 4, 30.0, 300.0) * 2.0) * chipped[ident]
    albedo = mix(albedo, linear(152, 126, 102), chip_corner)
    broken = rng.random(count * count) < 0.07
    crack_line = sstep(1.3, 0.0, np.abs((fu - 0.5) * 0.7 + (fv - 0.5) - field(seed + 5, 10.0, 200.0) * 0.05) * pitch) * broken[ident]
    albedo = mix(albedo, linear(40, 36, 30), crack_line * 0.9)
    missing = ident == 19
    grout = linear(92, 86, 74) * (0.6 + 0.4 * unit(field(seed + 6, 8.0, 200.0)))[:, :, None]
    albedo = np.where((face & ~missing)[:, :, None], albedo, grout)
    grease = cover(field(seed + 7, 1.5, 30.0, 2.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * np.array([0.64, 0.57, 0.44]), grease * 0.45)
    drip = cover(field(seed + 8, 3.0, 80.0, 2.0, 1.0, 6.0), 0.2, 0.4)
    albedo = tint(albedo, 1.0 - 0.18 * drip)
    height = np.where(face & ~missing, sstep(1.5, 6.0, distance) * 0.0012 + 0.001, -0.0015) - chip_corner * 0.001 - crack_line * 0.0005 + field(seed + 9, 3.0, 40.0) * 0.00008
    rough = np.where(face & ~missing, 0.12 + 0.3 * grease + 0.1 * drip + 0.5 * chip_corner, 0.92)
    occlusion = 1.0 - 0.5 * (~face) - 0.3 * cavity(height, 2.0, 0.0008)
    save("kitchen_tiles", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "world"})


def make_concrete():
    tile = 2.0
    seed = 2300
    base = mix(linear(144, 140, 132), linear(120, 118, 112), unit(field(seed, 1.5, 30.0, 2.0)))
    albedo = tint(base, 0.9 + 0.16 * unit(field(seed + 1, 6.0, 200.0, 1.6)))
    first, second, ident = voronoi(60, 60, seed + 2, 1.0)
    exposed = cover(field(seed + 4, 3.0, 60.0), 0.3, 0.5) * sstep(4.0, 1.0, first)
    pebble = linear(122, 112, 102) * np.random.default_rng(seed + 3).uniform(0.6, 1.3, (60 * 60, 1))[ident]
    albedo = mix(albedo, pebble, exposed * 0.7)
    pores = cover(speckle(seed + 5, 1.0), 0.05, 0.3)
    albedo = mix(albedo, linear(40, 38, 36), pores * 0.8)
    stains = cover(field(seed + 6, 1.2, 40.0, 2.0, 1.0, 6.0), 0.25, 0.5)
    albedo = tint(albedo, 1.0 - 0.3 * stains)
    efflo = cover(field(seed + 7, 2.0, 50.0, 2.0, 1.0, 3.0), 0.12, 0.5)
    albedo = mix(albedo, linear(200, 198, 190), efflo * 0.3)
    moss = patchy(seed + 8, 0.06, 8.0, 200.0, 0.8)
    albedo = mix(albedo, linear(62, 76, 32), moss * 0.6)
    crack = cracks(seed + 9, 5, 1.0, 0.35)
    albedo = mix(albedo, linear(30, 28, 26), crack * 0.8)
    height = field(seed + 10, 2.0, 60.0, 2.2) * 0.0012 + exposed * 0.0008 * sstep(4.0, 0.0, first) - pores * 0.0012 - crack * 0.001 + speckle(seed + 11, 0.8) * 0.0001
    rough = 0.88 + 0.04 * field(seed + 12, 4.0, 100.0) + 0.05 * moss - 0.08 * stains
    occlusion = 1.0 - 0.4 * cavity(height, 2.0, 0.0008) - 0.3 * crack
    save("concrete", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "world"})


def make_rusty():
    tile = 1.0
    seed = 2400
    rust = mix(linear(92, 44, 22), linear(122, 62, 30), unit(field(seed, 6.0, 200.0, 1.7)))
    rust = mix(rust, linear(52, 30, 20), cover(field(seed + 1, 10.0, 300.0, 1.6), 0.3, 0.5))
    rust = tint(rust, 0.82 + 0.36 * unit(speckle(seed + 2, 1.0)))
    paint_field = field(seed + 3, 3.0, 200.0, 1.8) + 0.4 * field(seed + 4, 30.0, 400.0, 1.4)
    paint = cover(paint_field, 0.5, 0.04)
    coat = flat(linear(36, 36, 36)) * (0.85 + 0.25 * unit(field(seed + 5, 5.0, 100.0)))[:, :, None]
    albedo = mix(rust, coat, paint)
    blister = np.clip(paint * (1.0 - paint) * 4.0, 0.0, 1.0)
    pits = cover(speckle(seed + 6, 1.2), 0.07, 0.3) * (1.0 - paint)
    albedo = mix(albedo, linear(28, 16, 10), pits * 0.9)
    scratch = cover(field(seed + 7, 2.0, 600.0, 1.2, 20.0, 0.5), 0.02, 0.2)
    albedo = mix(albedo, linear(150, 150, 148), scratch * 0.8)
    streak = cover(field(seed + 8, 2.0, 80.0, 2.0, 1.0, 6.0), 0.25, 0.5)
    albedo = mix(albedo, albedo * np.array([1.18, 0.96, 0.82]), streak * 0.3)
    height = (1.0 - paint) * field(seed + 9, 20.0, 600.0, 1.4) * 0.00025 + paint * 0.0002 + blister * 0.0004 - pits * 0.0006 + field(seed + 10, 3.0, 60.0) * 0.0004
    rough = mix(0.88 + 0.05 * field(seed + 11, 10.0, 200.0), 0.52, paint)
    rough = mix(rough, 0.35, scratch)
    occlusion = 1.0 - 0.4 * cavity(height, 1.5, 0.0003) - 0.3 * pits
    save("rusty_metal", albedo, rough, occlusion, height, tile, 1.0, metal=scratch * 0.9, extra={"kind": "local"})


def make_corrugated():
    tile = 1.0
    seed = 2500
    waves = 13
    trough = sstep(-0.2, -0.9, np.cos(grid_u / size * waves * 2.0 * math.pi))
    first, second, ident = voronoi(90, 90, seed, 1.0)
    spangle = np.random.default_rng(seed + 1).uniform(0.88, 1.12, 8100)[ident]
    zinc = flat(linear(150, 152, 150)) * spangle[:, :, None]
    dull = cover(field(seed + 2, 2.0, 60.0, 2.0), 0.4, 0.6)
    zinc = mix(zinc, linear(172, 172, 166), dull * 0.6)
    rust_colour = mix(linear(106, 52, 24), linear(70, 36, 18), unit(field(seed + 3, 10.0, 300.0, 1.6)))
    rust_colour = tint(rust_colour, 0.82 + 0.36 * unit(speckle(seed + 4, 1.0)))
    patches = field(seed + 5, 3.0, 200.0, 1.8) + 0.4 * field(seed + 6, 20.0, 400.0, 1.4) + trough * 0.5 + 0.6 * field(seed + 7, 2.0, 120.0, 1.8, 1.0, 10.0)
    rusty = cover(patches, 0.35, 0.05)
    albedo = mix(zinc, rust_colour, rusty)
    oxide_paint = cover(field(seed + 8, 2.5, 150.0, 1.8), 0.15, 0.05) * (1.0 - rusty)
    albedo = mix(albedo, linear(98, 42, 32), oxide_paint * 0.8)
    runs = cover(field(seed + 9, 3.0, 100.0, 2.0, 1.0, 12.0), 0.15, 0.4) * (1.0 - rusty)
    albedo = mix(albedo, linear(92, 52, 28), runs * 0.4)
    albedo = tint(albedo, 1.0 - 0.15 * trough)
    height = rusty * (0.0002 + field(seed + 10, 30.0, 600.0, 1.3) * 0.00015) + field(seed + 11, 4.0, 60.0) * 0.0002
    rough = mix(mix(0.42 + 0.1 * dull, 0.9, rusty), 0.7, oxide_paint)
    metal = mix(mix(0.85 - 0.3 * dull, 0.05, rusty), 0.0, oxide_paint)
    occlusion = 1.0 - 0.22 * trough - 0.3 * cavity(height, 1.5, 0.0003)
    save("corrugated_rusty", albedo, rough, occlusion, height, tile, 1.0, metal=metal, extra={"kind": "local", "waves": waves})


def make_glass():
    tile = 1.0
    seed = 2600
    film = unit(field(seed, 1.2, 14.0, 2.3)) * 0.8
    drips = cover(field(seed + 1, 4.0, 200.0, 1.8, 1.0, 10.0), 0.2, 0.6)
    spots = cover(speckle(seed + 2, 1.6), 0.05, 0.3)
    dirt = np.clip(film * 0.55 + drips * 0.3 + spots * 0.4, 0.0, 1.0)
    albedo = mix(flat(linear(16, 19, 21)), linear(84, 80, 70), dirt * 0.45)
    height = field(seed + 3, 1.0, 12.0, 2.5) * 0.0006 + field(seed + 4, 12.0, 60.0, 2.0) * 0.00008
    save("glass_dirty", albedo, 0.04 + 0.55 * dirt, np.ones((size, size)), height, tile, 1.0, extra={"kind": "local"})


def make_tartan():
    tile = 1.0
    seed = 2700
    sett = [(40, linear(62, 84, 58)), (14, linear(38, 42, 68)), (6, linear(160, 60, 46)), (14, linear(38, 42, 68)), (40, linear(62, 84, 58)), (6, linear(26, 26, 26)), (20, linear(150, 58, 44)), (6, linear(210, 196, 150)), (20, linear(150, 58, 44)), (6, linear(26, 26, 26))]
    total = sum(width for width, color in sett)
    repeats = 4
    scale = size / (total * repeats)
    lookup = np.zeros((size, 3))
    position = 0.0
    for repeat in range(repeats):
        for width, color in sett:
            start = int(round(position))
            position += width * scale
            lookup[start:int(round(position))] = color
    warp_color = lookup[grid_u.astype(np.int64) % size]
    weft_color = lookup[grid_v.astype(np.int64) % size]
    twill = ((grid_u.astype(np.int64) + grid_v.astype(np.int64)) % 4) < 2
    albedo = np.where(twill[:, :, None], warp_color, weft_color) * 0.5 + (warp_color + weft_color) * 0.25
    fade = unit(field(seed, 1.5, 30.0, 2.0))
    albedo = mix(albedo, albedo * 0.6 + linear(180, 170, 150) * 0.4, 0.25 + 0.3 * fade)
    albedo = tint(albedo, 0.9 + 0.2 * unit(speckle(seed + 1, 0.9)))
    stain_field = field(seed + 2, 1.5, 25.0, 2.2)
    stain = cover(stain_field, 0.14, 0.2)
    ring = sstep(0.12, 0.0, np.abs(stain_field - float(np.quantile(stain_field, 0.86))))
    albedo = mix(albedo, albedo * np.array([0.76, 0.66, 0.52]), stain * 0.5)
    albedo = mix(albedo, albedo * 0.56, ring * 0.4)
    holes = cover(field(seed + 3, 30.0, 400.0, 1.5), 0.012, 0.2)
    albedo = mix(albedo, linear(10, 9, 8), holes)
    thread = np.where(twill, np.sin(grid_u * math.pi * 0.5) ** 2, np.sin(grid_v * math.pi * 0.5) ** 2) * 0.00025
    height = thread + speckle(seed + 4, 1.0) * 0.00015 - holes * 0.001
    rough = 0.92 + 0.04 * speckle(seed + 5, 1.0)
    occlusion = 1.0 - 0.3 * cavity(height, 1.0, 0.0002) - 0.6 * holes
    save("fabric_tartan", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "local"})


def make_fabric():
    tile = 1.0
    seed = 2750
    u = grid_u.astype(np.int64)
    v = grid_v.astype(np.int64)
    herring = ((u + np.where((v // 24) % 2 == 0, v, -v)) % 6) < 3
    base = mix(linear(134, 120, 98), linear(118, 110, 94), unit(field(seed, 2.0, 40.0)))
    albedo = tint(base, np.where(herring, 1.0, 0.86))
    albedo = tint(albedo, 0.9 + 0.2 * unit(speckle(seed + 1, 0.9)))
    stripe = sstep(0.06, 0.02, np.abs(((grid_u / size * 8.0) % 1.0) - 0.5))
    albedo = mix(albedo, albedo * np.array([0.78, 0.7, 0.66]), stripe * 0.35)
    bare = cover(field(seed + 2, 2.0, 60.0, 2.0), 0.2, 0.5)
    albedo = mix(albedo, albedo * np.array([1.22, 1.2, 1.16]), bare * 0.5)
    stain_field = field(seed + 3, 1.5, 25.0, 2.2)
    stain = cover(stain_field, 0.16, 0.25)
    ring = sstep(0.1, 0.0, np.abs(stain_field - float(np.quantile(stain_field, 0.84))))
    albedo = mix(albedo, albedo * np.array([0.7, 0.62, 0.5]), stain * 0.55)
    albedo = mix(albedo, albedo * 0.6, ring * 0.4)
    albedo = tint(albedo, 1.0 - 0.25 * cover(field(seed + 4, 1.0, 30.0, 2.0, 1.0, 3.0), 0.3, 0.5))
    holes = cover(field(seed + 5, 30.0, 400.0, 1.5), 0.008, 0.2)
    albedo = mix(albedo, linear(12, 10, 8), holes)
    thread = np.where(herring, 0.0002, 0.0) + np.sin(grid_u * math.pi * 0.5) ** 2 * 0.0001
    height = thread + speckle(seed + 6, 1.0) * 0.00012 - holes * 0.001
    rough = 0.93 + 0.03 * speckle(seed + 7, 1.0)
    occlusion = 1.0 - 0.3 * cavity(height, 1.0, 0.0002) - 0.6 * holes
    save("fabric_worn", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "local"})


def make_mattress():
    tile = 1.0
    seed = 2800
    stripe_phase = (grid_v / size * 1000.0) % 34.0
    stripes = np.clip(sstep(2.6, 1.6, np.abs(stripe_phase - 4.0)) + sstep(2.6, 1.6, np.abs(stripe_phase - 10.0)) + sstep(5.5, 4.5, np.abs(stripe_phase - 23.0)), 0.0, 1.0)
    cloth = mix(linear(214, 206, 184), linear(202, 194, 172), unit(field(seed, 2.0, 30.0)))
    albedo = mix(cloth, linear(46, 58, 104), stripes * 0.92)
    twill = ((grid_u.astype(np.int64) + grid_v.astype(np.int64)) % 3) == 0
    albedo = tint(albedo, np.where(twill, 0.94, 1.0))
    stain_field = field(seed + 1, 1.3, 20.0, 2.2) + 0.25 * field(seed + 2, 10.0, 200.0, 1.5)
    stain = cover(stain_field, 0.3, 0.15)
    ring = sstep(0.1, 0.0, np.abs(stain_field - float(np.quantile(stain_field, 0.7))))
    albedo = mix(albedo, albedo * np.array([0.8, 0.64, 0.4]), stain * 0.65)
    albedo = mix(albedo, albedo * np.array([0.52, 0.4, 0.26]), ring * 0.6)
    mold = cover(speckle(seed + 3, 1.5), 0.12, 0.3) * cover(field(seed + 4, 2.0, 40.0), 0.2, 0.4)
    albedo = mix(albedo, linear(40, 40, 36), mold * 0.8)
    albedo = tint(albedo, 1.0 - 0.2 * cover(field(seed + 5, 1.0, 20.0, 2.0), 0.4, 0.6))
    button = np.zeros((size, size))
    dimple = np.zeros((size, size))
    for cu in range(4):
        for cv in range(4):
            cx = (cu + 0.5) * size / 4.0
            cy = (cv + 0.5 + (0.5 if cu % 2 else 0.0)) * size / 4.0
            r = np.hypot(((grid_u - cx) + size * 0.5) % size - size * 0.5, ((grid_v - cy) + size * 0.5) % size - size * 0.5)
            button = np.maximum(button, sstep(9.0, 7.0, r))
            dimple = np.maximum(dimple, np.exp(-(r / 70.0) ** 2))
    albedo = mix(albedo, linear(40, 38, 34), button * 0.9)
    height = -dimple * 0.008 + np.where(twill, 0.0001, 0.0) + speckle(seed + 6, 1.0) * 0.00008
    rough = 0.93 + 0.03 * speckle(seed + 7, 1.0)
    occlusion = 1.0 - 0.35 * dimple - 0.3 * button
    save("mattress", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "local"})


def make_bricks():
    tile = 1.2
    seed = 2900
    courses = 16
    per_course = 6
    course_px = size / courses
    brick_px = size / per_course
    cv = np.floor(grid_v / course_px).astype(np.int64)
    shift = (cv % 2) * brick_px * 0.5
    cu = np.floor((grid_u + shift) / brick_px).astype(np.int64) % per_course
    fu = ((grid_u + shift) % brick_px) / brick_px
    fv = (grid_v % course_px) / course_px
    joint = 0.01 / tile * size
    distance = np.minimum(np.minimum(fu, 1 - fu) * brick_px, np.minimum(fv, 1 - fv) * course_px)
    edge_noise = field(seed, 20.0, 400.0, 1.4) * 1.2
    brick = (distance + edge_noise) > joint * 0.5
    ident = cv * per_course + cu
    rng = np.random.default_rng(seed + 1)
    palette = np.array([linear(152, 64, 46), linear(122, 52, 42), linear(172, 86, 58), linear(98, 46, 42), linear(162, 102, 78)])
    picks = palette[rng.choice(len(palette), courses * per_course, p=[0.34, 0.22, 0.2, 0.12, 0.12])] * rng.uniform(0.86, 1.12, (courses * per_course, 1))
    albedo = picks[ident] * (0.9 + 0.18 * unit(field(seed + 2, 10.0, 300.0, 1.6)))[:, :, None]
    albedo = tint(albedo, 1.0 + 0.08 * speckle(seed + 3, 0.9))
    mortar = linear(152, 146, 132) * (0.6 + 0.3 * unit(field(seed + 4, 6.0, 200.0)))[:, :, None]
    albedo = np.where(brick[:, :, None], albedo, mortar)
    soot = cover(field(seed + 5, 1.5, 30.0, 2.0), 0.3, 0.5)
    albedo = tint(albedo, 1.0 - 0.4 * soot)
    efflo = cover(field(seed + 6, 3.0, 80.0, 2.0), 0.1, 0.5)
    albedo = mix(albedo, linear(200, 196, 186), efflo * 0.25)
    lichen = patchy(seed + 7, 0.05, 20.0, 300.0, 0.6) * brick
    albedo = mix(albedo, linear(150, 154, 130), lichen * 0.5)
    height = np.where(brick, 0.002 * sstep(joint * 0.5, joint * 0.5 + 3.0, distance + edge_noise) + field(seed + 8, 20.0, 500.0, 1.3) * 0.0002, -0.003)
    rough = np.where(brick, 0.84 + 0.05 * field(seed + 9, 8.0, 200.0), 0.94)
    occlusion = 1.0 - 0.5 * (~brick) - 0.3 * cavity(height, 2.0, 0.0012)
    save("brick_red", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "world"})


def make_cobbles():
    tile = 1.6
    seed = 3000
    rng = np.random.default_rng(seed)
    sites = []
    y = 0.0
    heights = []
    while y < tile - 0.05:
        h = rng.uniform(0.1, 0.14)
        heights.append(h)
        y += h
    heights = np.array(heights) * tile / sum(heights)
    y = 0.0
    for h in heights:
        widths = []
        run = 0.0
        while run < tile - 0.08:
            w = rng.uniform(0.11, 0.18)
            widths.append(w)
            run += w
        widths = np.array(widths) * tile / sum(widths)
        x = rng.uniform(0.0, tile)
        for w in widths:
            sites.append(((x + w * 0.5 + rng.uniform(-0.1, 0.1) * w) % tile, (y + h * 0.5 + rng.uniform(-0.1, 0.1) * h) % tile))
            x += w
        y += h
    ident, stone, depth, profile = stone_field(seed + 1, tile, sites, (0.008, 0.013), (0.012, 0.02), (0.02, 0.035), 0.02, 0.003, 1.0, 0.012)
    colors = granite_palette(np.random.default_rng(seed + 2), len(sites)) * 0.85
    dark, light, pink = granite_grains(seed + 3)
    albedo = tint(colors[ident], 1.0 - 0.4 * dark)
    albedo = mix(albedo, linear(210, 204, 194), light * 0.28)
    polish = sstep(0.004, 0.02, depth)
    albedo = mix(albedo, albedo * 1.1, polish * 0.3)
    soil = mix(linear(60, 48, 36), linear(42, 36, 28), unit(field(seed + 4, 10.0, 300.0)))
    moss = cover(field(seed + 5, 6.0, 200.0), 0.4, 0.4)
    soil = mix(soil, linear(52, 70, 22) * (0.7 + 0.6 * unit(speckle(seed + 6, 1.2)))[:, :, None], moss * 0.85)
    albedo = np.where(stone[:, :, None], albedo, soil)
    height = np.where(stone, profile, -0.01 + field(seed + 7, 40.0, 500.0, 1.2) * 0.0015 + moss * 0.003)
    albedo = tint(albedo, 1.0 - 0.35 * cavity(height, 3.0, 0.008))
    rough = np.where(stone, 0.64 + 0.08 * field(seed + 8, 5.0, 100.0) - 0.1 * polish, 0.96)
    occlusion = 1.0 - 0.5 * cavity(height, 2.0, 0.005) - 0.3 * cavity(height, 8.0, 0.01)
    save("cobbles", albedo, rough, occlusion, height, tile, 0.9, extra={"kind": "world"})


def strokes(seed, count, length_range, width_range, angle_center, angle_spread, wild, colors, tile):
    rng = np.random.default_rng(seed)
    albedo = flat(colors[0])
    top = np.full((size, size), -1.0)
    scale = size / tile
    for stroke in range(count):
        cx = rng.uniform(0, size)
        cy = rng.uniform(0, size)
        angle = rng.uniform(0.0, math.pi) if rng.random() < wild else angle_center + rng.normal(0.0, angle_spread)
        length = rng.uniform(*length_range) * scale
        width = rng.uniform(*width_range) * scale
        dx = math.cos(angle) * length * 0.5
        dy = math.sin(angle) * length * 0.5
        points = [(cx - dx, cy - dy), (cx + dx, cy + dy)]
        where, lu, lv = window(points, int(width) + 2)
        ax, ay = points[0]
        ex = 2.0 * dx
        ey = 2.0 * dy
        t = np.clip(((lu - ax) * ex + (lv - ay) * ey) / (ex * ex + ey * ey), 0.0, 1.0)
        d = np.hypot(lu - (ax + ex * t), lv - (ay + ey * t))
        profile = np.sqrt(np.clip(1.0 - (d / (width * 0.5)) ** 2, 0.0, 1.0))
        level = rng.uniform(-0.003, 0.003) + profile * width / scale * 0.5
        choice = colors[1 + rng.integers(0, len(colors) - 1)] * rng.uniform(0.8, 1.15)
        current = top[where]
        take = (profile > 0.0) & (level > current)
        top[where] = np.where(take, level, current)
        albedo[where] = np.where(take[:, :, None], (0.75 + 0.35 * profile)[:, :, None] * choice, albedo[where])
    return albedo, np.maximum(top, -0.004)


def make_hay():
    tile = 1.0
    seed = 3100
    colors = [linear(40, 30, 14), linear(196, 160, 82), linear(176, 142, 70), linear(212, 184, 112), linear(150, 124, 66), linear(120, 104, 70), linear(96, 84, 60)]
    albedo, height = strokes(seed, 9000, (0.04, 0.16), (0.0018, 0.0035), 0.0, 0.3, 0.25, colors, tile)
    old = cover(field(seed + 1, 2.0, 40.0, 2.0), 0.35, 0.5)
    albedo = mix(albedo, albedo * np.array([0.7, 0.68, 0.62]), old * 0.5)
    albedo = tint(albedo, 0.85 + 0.2 * unit(field(seed + 2, 4.0, 60.0)))
    rough = 0.72 + 0.12 * unit(speckle(seed + 3, 1.0))
    occlusion = 1.0 - 0.6 * cavity(height, 2.0, 0.002)
    save("hay", albedo, rough, occlusion, height, tile, 0.7, extra={"kind": "local"})


def make_dirt():
    tile = 2.0
    seed = 3200
    soil = mix(linear(86, 70, 54), linear(62, 52, 42), unit(field(seed, 2.0, 60.0, 2.0)))
    soil = mix(soil, linear(106, 94, 78), cover(field(seed + 1, 3.0, 80.0), 0.3, 0.5) * 0.6)
    soil = mix(soil, soil * 0.62, cover(field(seed + 11, 1.5, 30.0, 2.2), 0.25, 0.6))
    albedo = tint(soil, 0.85 + 0.25 * unit(speckle(seed + 2, 1.0)))
    first, second, ident = voronoi(70, 70, seed + 3, 1.0)
    rng = np.random.default_rng(seed + 4)
    keep = rng.random(4900) < 0.4
    radius = rng.uniform(2.0, 6.0, 4900)
    pebble = sstep(radius[ident], radius[ident] * 0.5, first) * keep[ident]
    tone = rng.uniform(0.7, 1.4, 4900)[ident]
    albedo = mix(albedo, linear(130, 126, 118) * tone[:, :, None], pebble)
    leaf_colors = [linear(40, 30, 18), linear(120, 72, 34), linear(96, 60, 30), linear(140, 100, 50), linear(70, 50, 30)]
    leaves, leaf_height = strokes(seed + 5, 800, (0.02, 0.05), (0.008, 0.018), 0.0, 3.0, 1.0, leaf_colors, tile)
    leaf_mask = sstep(-0.0035, -0.002, leaf_height)
    twig_colors = [linear(40, 30, 18), linear(70, 54, 38), linear(52, 40, 28), linear(160, 140, 100)]
    twigs, twig_height = strokes(seed + 6, 1000, (0.03, 0.12), (0.002, 0.005), 0.0, 3.0, 1.0, twig_colors, tile)
    twig_mask = sstep(-0.0035, -0.002, twig_height)
    patch = cover(field(seed + 7, 2.0, 40.0), 0.45, 0.6)
    albedo = mix(albedo, leaves, leaf_mask * patch)
    albedo = mix(albedo, twigs, twig_mask * (0.4 + 0.6 * patch))
    moss = patchy(seed + 8, 0.1, 3.0, 80.0, 0.8, 0.3)
    albedo = mix(albedo, linear(58, 72, 28), moss * 0.7)
    height = field(seed + 9, 2.0, 100.0, 2.0) * 0.004 + pebble * 0.004 * sstep(radius[ident], 0.0, first) + leaf_height * leaf_mask * patch * 0.5 + twig_height * twig_mask * 0.6 + speckle(seed + 10, 0.8) * 0.0003
    rough = 0.92 - 0.1 * pebble + 0.04 * moss
    occlusion = 1.0 - 0.5 * cavity(height, 2.0, 0.003) - 0.2 * cavity(height, 10.0, 0.01)
    save("dirt_debris", albedo, rough, occlusion, height, tile, 0.9, extra={"kind": "world"})


def make_soot():
    tile = 1.0
    seed = 3300
    relief = field(seed, 3.0, 200.0, 1.8)
    base = flat(linear(22, 21, 20)) * (0.75 + 0.45 * unit(field(seed + 1, 3.0, 100.0, 1.8)))[:, :, None]
    creosote = cover(field(seed + 2, 3.0, 120.0, 1.8), 0.22, 0.4)
    albedo = mix(base, linear(26, 18, 10), creosote * 0.8)
    ash = cover(field(seed + 3, 2.0, 60.0, 2.0), 0.25, 0.5)
    albedo = mix(albedo, linear(96, 92, 88), ash * 0.35)
    height = relief * 0.0012 + creosote * 0.0006 * unit(speckle(seed + 4, 1.4))
    occlusion = 1.0 - 0.4 * cavity(height, 2.0, 0.0008)
    save("soot", albedo, mix(0.95, 0.3, creosote), occlusion, height, tile, 1.0, extra={"kind": "world"})


def make_ceramic():
    tile = 0.5
    seed = 3400
    glaze = mix(linear(232, 226, 206), linear(222, 214, 190), unit(field(seed, 2.0, 30.0)))
    craze = cracks(seed + 1, 30, 0.6, 0.85)
    plain = mix(glaze, glaze * np.array([0.6, 0.55, 0.45]), craze * 0.45)
    pattern = np.zeros((size, size))
    step = size / 8.0
    for column in range(9):
        for row in range(9):
            cx = column * step + (step * 0.5 if row % 2 else 0.0)
            cy = row * step
            du = ((grid_u - cx) + size * 0.5) % size - size * 0.5
            dv = ((grid_v - cy) + size * 0.5) % size - size * 0.5
            r = np.hypot(du, dv)
            theta = np.arctan2(dv, du)
            flower = sstep(0.0, 2.0, step * 0.16 * (0.55 + 0.45 * np.abs(np.cos(theta * 2.5 + column))) - r)
            ring = sstep(1.5, 0.0, np.abs(r - step * 0.3)) * sstep(0.2, 0.6, 0.5 + 0.5 * np.cos(theta * 6.0 + row))
            pattern = np.maximum(pattern, np.maximum(flower, ring * 0.7))
    blue = mix(plain, linear(52, 76, 140) * (0.8 + 0.3 * unit(speckle(seed + 2, 1.2)))[:, :, None], pattern * 0.9)
    albedo = np.where((grid_u < size * 0.5)[:, :, None], plain, blue)
    grime = cover(field(seed + 3, 1.5, 30.0, 2.0), 0.25, 0.5)
    albedo = mix(albedo, albedo * np.array([0.7, 0.66, 0.56]), grime * 0.45)
    chips = patchy(seed + 4, 0.04, 12.0, 300.0, 0.5)
    albedo = mix(albedo, linear(160, 136, 110), chips)
    height = -craze * 0.00008 - chips * 0.0006 + field(seed + 5, 2.0, 30.0) * 0.00005
    rough = 0.08 + 0.3 * grime + 0.6 * chips
    occlusion = 1.0 - 0.2 * craze - 0.2 * chips
    save("ceramic", albedo, rough, occlusion, height, tile, 1.0, extra={"kind": "regions", "regions": {"plain": [0.0, 0.5, 0.0, 1.0], "pattern": [0.5, 1.0, 0.0, 1.0]}})


def make_terracotta():
    tile = 0.6
    seed = 3500
    base = mix(linear(152, 86, 58), linear(128, 72, 50), unit(field(seed, 2.0, 40.0)))
    albedo = tint(base, 0.86 + 0.2 * unit(field(seed + 1, 10.0, 300.0, 1.6)))
    scale = patchy(seed + 2, 0.1, 8.0, 160.0, 0.8)
    albedo = mix(albedo, linear(196, 190, 174), scale * 0.5)
    algae = cover(field(seed + 3, 2.0, 40.0), 0.2, 0.5)
    albedo = mix(albedo, linear(58, 70, 34), algae * 0.45)
    soot = cover(field(seed + 4, 1.5, 30.0, 2.0, 1.0, 3.0), 0.3, 0.5)
    albedo = tint(albedo, 1.0 - 0.45 * soot)
    height = field(seed + 5, 10.0, 400.0, 1.4) * 0.0002 + scale * 0.0003
    occlusion = 1.0 - 0.3 * cavity(height, 1.5, 0.0002)
    save("terracotta", albedo, 0.84 + 0.06 * scale, occlusion, height, tile, 1.0, extra={"kind": "local"})


def make_foliage():
    tile = 0.5
    seed = 3600
    base = mix(linear(56, 88, 30), linear(46, 74, 24), unit(field(seed, 4.0, 80.0)))
    base = mix(base, linear(86, 108, 40), cover(field(seed + 1, 6.0, 120.0), 0.15, 0.5) * 0.35)
    veins = sstep(0.55, 0.8, 0.5 + 0.5 * np.sin(grid_u / size * 2.0 * math.pi * 60.0 + field(seed + 2, 1.0, 10.0) * 2.0))
    albedo = mix(base, base * 1.22, veins * 0.3)
    dead = cover(field(seed + 3, 2.0, 50.0), 0.12, 0.4)
    albedo = mix(albedo, linear(128, 96, 46), dead * 0.7)
    spots = cover(speckle(seed + 4, 1.5), 0.06, 0.3)
    albedo = mix(albedo, linear(62, 42, 22), spots * 0.45)
    height = veins * 0.0002 + field(seed + 5, 4.0, 100.0) * 0.0002
    occlusion = 1.0 - 0.2 * cavity(height, 1.5, 0.0002)
    save("foliage", albedo, 0.55 + 0.25 * dead, occlusion, height, tile, 1.0, extra={"kind": "local"})


def make_net():
    tile = 0.5
    seed = 3700
    albedo = flat(linear(14, 15, 13))
    height = np.full((size, size), -0.006)
    colors = [linear(84, 120, 96), linear(110, 92, 66), linear(74, 108, 128)]
    for layer in range(3):
        mesh = size / 12.0
        dx = field(seed + layer * 10, 1.0, 12.0, 2.0) * 18.0
        dy = field(seed + layer * 10 + 1, 1.0, 12.0, 2.0) * 18.0
        a = ((grid_u + dx + grid_v + dy) / mesh + layer * 0.37) % 1.0
        b = ((grid_u + dx - grid_v - dy) / mesh + layer * 0.61) % 1.0
        line_a = sstep(0.075, 0.035, np.minimum(a, 1.0 - a))
        line_b = sstep(0.075, 0.035, np.minimum(b, 1.0 - b))
        knot = sstep(0.14, 0.08, np.hypot(np.minimum(a, 1.0 - a), np.minimum(b, 1.0 - b)))
        twine = np.clip(np.maximum(np.maximum(line_a, line_b), knot), 0.0, 1.0)
        level = -0.004 + layer * 0.002 + twine * 0.001 + knot * 0.0008
        color = colors[layer] * (0.85 - 0.2 * (2 - layer) + 0.3 * unit(speckle(seed + layer, 1.0)))[:, :, None]
        take = (twine > 0.3) & (level > height)
        albedo = np.where(take[:, :, None], color * (0.7 + 0.3 * twine)[:, :, None], albedo)
        height = np.where(take, level, height)
    albedo = tint(albedo, 1.0 - 0.3 * cover(field(seed + 40, 2.0, 30.0), 0.4, 0.5))
    occlusion = 1.0 - 0.6 * cavity(height, 3.0, 0.003)
    save("rope_net", albedo, 0.9 * np.ones((size, size)), occlusion, height, tile, 0.8, extra={"kind": "local"})


makers = {
    "granite_rubble": make_rubble,
    "granite_ashlar": make_ashlar,
    "render_white": lambda: make_render("render_white", linear(228, 226, 216), linear(186, 182, 172), 1300),
    "render_pink": lambda: make_render("render_pink", linear(222, 178, 166), linear(228, 224, 212), 1350),
    "plaster_interior": make_plaster,
    "wallpaper_faded": make_wallpaper,
    "timber_planks_weathered": make_planks,
    "floorboards": make_floorboards,
    "painted_wood_green": lambda: make_painted("painted_wood_green", linear(70, 104, 80), linear(206, 198, 178), 1650),
    "painted_wood_blue": lambda: make_painted("painted_wood_blue", linear(82, 110, 140), linear(200, 156, 132), 1680),
    "timber_beam": make_beam,
    "timber_charred": make_charred,
    "slate_roof": make_slates,
    "clay_roof_tiles": make_pantiles,
    "kitchen_tiles": make_tiles,
    "concrete": make_concrete,
    "rusty_metal": make_rusty,
    "corrugated_rusty": make_corrugated,
    "glass_dirty": make_glass,
    "fabric_worn": make_fabric,
    "fabric_tartan": make_tartan,
    "mattress": make_mattress,
    "brick_red": make_bricks,
    "cobbles": make_cobbles,
    "hay": make_hay,
    "dirt_debris": make_dirt,
    "soot": make_soot,
    "ceramic": make_ceramic,
    "terracotta": make_terracotta,
    "foliage": make_foliage,
    "rope_net": make_net,
}
companions = {"granite_rubble_damp": "granite_rubble", "roof_moss": "slate_roof"}


def load_catalog():
    path = os.path.join(library_root, "library.json")
    if os.path.exists(path) and not catalog:
        with open(path, "r", encoding="utf-8") as handle:
            catalog.update(json.load(handle))
    return catalog


def build_library(names=None):
    os.makedirs(library_root, exist_ok=True)
    load_catalog()
    chosen = set(companions.get(name, name) for name in names) if names else set(makers)
    for name, maker in makers.items():
        if name in chosen:
            maker()
    with open(os.path.join(library_root, "library.json"), "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=1, sort_keys=True)
    write_sheet()
    print("LIBRARY DONE", len(catalog), "materials", flush=True)


import random

try:
    import bpy
    import bmesh
    from mathutils import Matrix, Vector, geometry
except ImportError:
    bpy = None

rng = random.Random(1)
double_sided = {"foliage", "rope_net", "fabric_worn", "fabric_tartan"}
material_cache = {}
tau = math.pi * 2.0


def V(x, y, z):
    return Vector((x, y, z))


def tile_of(name):
    load_catalog()
    return catalog.get(base_of(name), {}).get("tile", 1.0)


def base_of(name):
    return hero_bases.get(name, name)


hero_bases = {}
hero_albedo = {}


def gltf_group():
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
        group.interface.new_socket(name="Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
        group.interface.new_socket(name="Thickness", in_out='INPUT', socket_type='NodeSocketFloat')
    return group


def load_image(path, colorspace):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = colorspace
    return image


def hero(name, albedo_path, base):
    hero_bases[name] = base
    hero_albedo[name] = albedo_path


def material(name):
    cached = material_cache.get(name)
    if cached is not None:
        try:
            cached.name
            return cached
        except ReferenceError:
            pass
    base = base_of(name)
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    result.use_backface_culling = base not in double_sided
    tree = result.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = load_image(hero_albedo.get(name, os.path.join(library_root, base + "_albedo.png")), 'sRGB')
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    packed = tree.nodes.new('ShaderNodeTexImage')
    packed.image = load_image(os.path.join(library_root, base + "_orm.png"), 'Non-Color')
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(packed.outputs['Color'], split.inputs['Color'])
    tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
    tree.links.new(split.outputs['Blue'], shader.inputs['Metallic'])
    settings = tree.nodes.new('ShaderNodeGroup')
    settings.node_tree = gltf_group()
    tree.links.new(split.outputs['Red'], settings.inputs['Occlusion'])
    bumps = tree.nodes.new('ShaderNodeTexImage')
    bumps.image = load_image(os.path.join(library_root, base + "_normal.png"), 'Non-Color')
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(bumps.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    material_cache[name] = result
    return result


def newell(points):
    x = y = z = 0.0
    count = len(points)
    for index in range(count):
        a = points[index]
        b = points[(index + 1) % count]
        x += (a.y - b.y) * (a.z + b.z)
        y += (a.z - b.z) * (a.x + b.x)
        z += (a.x - b.x) * (a.y + b.y)
    return Vector((x, y, z))


def project(points, normal, tile, offset):
    ax = abs(normal.x)
    ay = abs(normal.y)
    az = abs(normal.z)
    ou, ov = offset
    if az >= ax and az >= ay:
        s = 1.0 if normal.z >= 0.0 else -1.0
        return [(p.x / tile + ou, s * p.y / tile + ov) for p in points]
    if ax >= ay:
        s = 1.0 if normal.x >= 0.0 else -1.0
        return [(s * p.y / tile + ou, p.z / tile + ov) for p in points]
    s = -1.0 if normal.y >= 0.0 else 1.0
    return [(s * p.x / tile + ou, p.z / tile + ov) for p in points]


class Geo:
    __slots__ = ("points", "faces", "uvs")

    def __init__(self, points=None, faces=None, uvs=None):
        self.points = points if points is not None else []
        self.faces = faces if faces is not None else []
        self.uvs = uvs

    def extend(self, other):
        base = len(self.points)
        self.points.extend(other.points)
        self.faces.extend(tuple(base + i for i in face) for face in other.faces)
        if self.uvs is not None or other.uvs is not None:
            mine = self.uvs if self.uvs is not None else [None] * (len(self.faces) - len(other.faces))
            theirs = other.uvs if other.uvs is not None else [None] * len(other.faces)
            self.uvs = mine + theirs
        return self


class Part:
    def __init__(self, name, sharp=35.0):
        self.name = name
        self.sharp = sharp
        self.points = []
        self.faces = []
        self.loops = []
        self.slots = []
        self.lookup = {}
        self.face_slots = []
        self.smooth = []

    def slot(self, name):
        if name not in self.lookup:
            self.lookup[name] = len(self.slots)
            self.slots.append(name)
        return self.lookup[name]

    def add(self, points, faces, uvs, name, smooth):
        base = len(self.points)
        self.points.extend((p.x, p.y, p.z) for p in points)
        index = self.slot(name)
        for face, face_uv in zip(faces, uvs):
            self.faces.append(tuple(base + i for i in face))
            self.loops.extend(face_uv)
            self.face_slots.append(index)
            self.smooth.append(smooth)

    def triangles(self):
        return sum(len(face) - 2 for face in self.faces)

    def build(self):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.points, [], self.faces)
        layer = mesh.uv_layers.new(name="UVMap")
        flat_uv = [value for uv in self.loops for value in uv]
        layer.data.foreach_set("uv", flat_uv)
        mesh.polygons.foreach_set("material_index", self.face_slots)
        mesh.polygons.foreach_set("use_smooth", self.smooth)
        for name in self.slots:
            mesh.materials.append(material(name))
        mesh.set_sharp_from_angle(angle=math.radians(self.sharp))
        mesh.update()
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def deform(part, function):
    part.points = [function(p) for p in part.points]


def sagging(x0, x1, z0, z1, amount):
    def apply(p):
        x, y, z = p
        if x <= x0 or x >= x1 or z <= z0:
            return p
        t = min((z - z0) / (z1 - z0), 1.0)
        return (x, y, z - amount * math.sin(math.pi * (x - x0) / (x1 - x0)) * t)
    return apply


def boards_of(name):
    return catalog.get(base_of(name), {}).get("boards")


def pick_board(name, width):
    boards = boards_of(name)
    tile = tile_of(name)
    ranked = sorted(boards, key=lambda b: abs((b[1] - b[0]) * tile - width) + rng.random() * 0.03)
    return ranked[0]


def emit(part, geo, name, matrix=None, mapping="box", smooth=False, offset=None, scale=1.0):
    tile = tile_of(name) / scale
    if offset is None:
        offset = (0.0, 0.0) if mapping == "world" else (rng.random(), rng.random())
    points = [matrix @ p for p in geo.points] if matrix is not None else list(geo.points)
    uvs = []
    if mapping == "board" and not boards_of(name):
        mapping = "box"
    if mapping == "board":
        low = Vector((min(p.x for p in geo.points), min(p.y for p in geo.points), min(p.z for p in geo.points)))
        high = Vector((max(p.x for p in geo.points), max(p.y for p in geo.points), max(p.z for p in geo.points)))
        extent = high - low
        long_axis = max(range(3), key=lambda axis: extent[axis])
        others = [axis for axis in range(3) if axis != long_axis]
        board = pick_board(name, max(extent[others[0]], extent[others[1]]))
        span = board[1] - board[0]
        inset = span * 0.06
    for number, face in enumerate(geo.faces):
        if mapping == "texture":
            uvs.append(geo.uvs[number])
            continue
        if mapping == "given" and geo.uvs is not None and geo.uvs[number] is not None:
            uvs.append([(u / tile + offset[0], v / tile + offset[1]) for u, v in geo.uvs[number]])
            continue
        if mapping == "world":
            corners = [points[i] for i in face]
            uvs.append(project(corners, newell(corners), tile, offset))
            continue
        corners = [geo.points[i] for i in face]
        normal = newell(corners)
        if mapping == "board" and abs(normal[long_axis]) < 0.7 * normal.length:
            across_axis = others[0] if abs(normal[others[1]]) >= abs(normal[others[0]]) else others[1]
            lo = low[across_axis]
            width = max(extent[across_axis], 1e-5)
            uvs.append([(p[long_axis] / tile + offset[0], board[0] + inset + (p[across_axis] - lo) / width * (span - 2.0 * inset)) for p in corners])
            continue
        uvs.append(project(corners, normal, tile, offset))
    part.add(points, geo.faces, uvs, name, smooth)


def orient(face, points, expected):
    corners = [points[i] for i in face]
    if newell(corners).dot(expected) < 0.0:
        return tuple(reversed(face))
    return face


def geo_box(sx, sy, sz, skip=()):
    hx = sx * 0.5
    hy = sy * 0.5
    hz = sz * 0.5
    points = [V(-hx, -hy, -hz), V(hx, -hy, -hz), V(hx, hy, -hz), V(-hx, hy, -hz), V(-hx, -hy, hz), V(hx, -hy, hz), V(hx, hy, hz), V(-hx, hy, hz)]
    named = {"bottom": (0, 3, 2, 1), "top": (4, 5, 6, 7), "front": (0, 1, 5, 4), "back": (2, 3, 7, 6), "left": (0, 4, 7, 3), "right": (1, 2, 6, 5)}
    return Geo(points, [face for key, face in named.items() if key not in skip])


def geo_cbox(sx, sy, sz, b):
    h = (sx * 0.5, sy * 0.5, sz * 0.5)
    b = min(b, h[0] * 0.45, h[1] * 0.45, h[2] * 0.45)
    points = []
    index = {}
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                s = (2 * i - 1, 2 * j - 1, 2 * k - 1)
                for axis in range(3):
                    p = [s[c] * (h[c] if c == axis else h[c] - b) for c in range(3)]
                    index[(i, j, k, axis)] = len(points)
                    points.append(Vector(p))
    faces = []
    for axis in range(3):
        for side in (0, 1):
            corners = [(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1) if (i, j, k)[axis] == side]
            others = [c for c in range(3) if c != axis]
            center = Vector((0.0, 0.0, 0.0))
            ordered = sorted(corners, key=lambda c: math.atan2(2 * c[others[1]] - 1, 2 * c[others[0]] - 1))
            face = tuple(index[c + (axis,)] for c in ordered)
            normal = Vector((0.0, 0.0, 0.0))
            normal[axis] = 2 * side - 1
            faces.append(orient(face, points, normal))
    for axis in range(3):
        a, bb = [c for c in range(3) if c != axis]
        for sa in (0, 1):
            for sb in (0, 1):
                ends = []
                for e in (0, 1):
                    c = [0, 0, 0]
                    c[a] = sa
                    c[bb] = sb
                    c[axis] = e
                    ends.append(tuple(c))
                face = (index[ends[0] + (a,)], index[ends[1] + (a,)], index[ends[1] + (bb,)], index[ends[0] + (bb,)])
                normal = Vector((0.0, 0.0, 0.0))
                normal[a] = 2 * sa - 1
                normal[bb] = 2 * sb - 1
                faces.append(orient(face, points, normal))
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                face = (index[(i, j, k, 0)], index[(i, j, k, 1)], index[(i, j, k, 2)])
                faces.append(orient(face, points, Vector((2 * i - 1, 2 * j - 1, 2 * k - 1))))
    return Geo(points, faces)


def geo_lathe(profile, segments, phase=0.0, cap_start=False, cap_end=False):
    points = []
    rings = []
    for r, z in profile:
        if r < 1e-7:
            rings.append([len(points)] * segments)
            points.append(V(0.0, 0.0, z))
            continue
        ring = []
        for s in range(segments):
            angle = phase + tau * s / segments
            ring.append(len(points))
            points.append(V(r * math.cos(angle), r * math.sin(angle), z))
        rings.append(ring)
    arc = [0.0]
    for index in range(1, len(profile)):
        arc.append(arc[-1] + math.hypot(profile[index][0] - profile[index - 1][0], profile[index][1] - profile[index - 1][1]))
    reach = tau * max(r for r, z in profile)
    faces = []
    uvs = []
    for index in range(len(profile) - 1):
        for s in range(segments):
            t = (s + 1) % segments
            u0 = reach * s / segments
            u1 = reach * (s + 1) / segments
            quad = [(rings[index][s], (u0, arc[index])), (rings[index][t], (u1, arc[index])), (rings[index + 1][t], (u1, arc[index + 1])), (rings[index + 1][s], (u0, arc[index + 1]))]
            cleaned = []
            for vertex, uv in quad:
                if not cleaned or cleaned[-1][0] != vertex:
                    cleaned.append((vertex, uv))
            if len(cleaned) > 1 and cleaned[0][0] == cleaned[-1][0]:
                cleaned.pop()
            if len(cleaned) >= 3:
                faces.append(tuple(v for v, uv in cleaned))
                uvs.append([uv for v, uv in cleaned])
    if cap_start and profile[0][0] > 1e-7:
        ring = rings[0]
        faces.append(tuple(reversed(ring)))
        uvs.append([(points[i].x, points[i].y) for i in reversed(ring)])
    if cap_end and profile[-1][0] > 1e-7:
        ring = rings[-1]
        faces.append(tuple(ring))
        uvs.append([(points[i].x, points[i].y) for i in ring])
    return Geo(points, faces, uvs)


def frames_along(path, up):
    count = len(path)
    tangents = []
    for index in range(count):
        ahead = path[min(index + 1, count - 1)]
        behind = path[max(index - 1, 0)]
        tangents.append((ahead - behind).normalized())
    normal = up - tangents[0] * up.dot(tangents[0])
    if normal.length < 1e-6:
        normal = tangents[0].orthogonal()
    normal.normalize()
    frames = []
    for index in range(count):
        if index > 0:
            normal = tangents[index - 1].rotation_difference(tangents[index]) @ normal
            normal = (normal - tangents[index] * normal.dot(tangents[index])).normalized()
        side = normal.cross(tangents[index]).normalized()
        frames.append((tangents[index], side, normal))
    return frames


def circle(radius, sides, phase=0.0):
    return [(radius * math.cos(phase + tau * s / sides), radius * math.sin(phase + tau * s / sides)) for s in range(sides)]


def geo_tube(path, profile, caps=True, up=None, scales=None, closed_profile=True):
    frames = frames_along(path, up if up is not None else V(0.0, 0.0, 1.0))
    points = []
    rings = []
    count = len(profile)
    for index, center in enumerate(path):
        tangent, side, normal = frames[index]
        scale = scales[index] if scales is not None else 1.0
        ring = []
        for px, py in profile:
            ring.append(len(points))
            points.append(center + side * (px * scale) + normal * (py * scale))
        rings.append(ring)
    along = [0.0]
    for index in range(1, len(path)):
        along.append(along[-1] + (path[index] - path[index - 1]).length)
    around = [0.0]
    for index in range(1, count + 1):
        a = profile[index - 1]
        b = profile[index % count]
        around.append(around[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    faces = []
    uvs = []
    spans = count if closed_profile else count - 1
    for index in range(len(path) - 1):
        for j in range(spans):
            k = (j + 1) % count
            faces.append((rings[index][j], rings[index][k], rings[index + 1][k], rings[index + 1][j]))
            uvs.append([(around[j], along[index]), (around[j + 1], along[index]), (around[j + 1], along[index + 1]), (around[j], along[index + 1])])
    if caps and closed_profile:
        faces.append(tuple(reversed(rings[0])))
        uvs.append([(profile[j][0], profile[j][1]) for j in reversed(range(count))])
        faces.append(tuple(rings[-1]))
        uvs.append([(profile[j][0], profile[j][1]) for j in range(count)])
    return Geo(points, faces, uvs)


def signed_area(polygon):
    return 0.5 * sum(polygon[i][0] * polygon[(i + 1) % len(polygon)][1] - polygon[(i + 1) % len(polygon)][0] * polygon[i][1] for i in range(len(polygon)))


def geo_slab(origin, along, up, normal, outline, holes, t0, t1, sides=True):
    if signed_area(outline) < 0.0:
        outline = list(reversed(outline))
    holes = [list(reversed(h)) if signed_area(h) > 0.0 else list(h) for h in holes]
    loops = [outline] + holes
    flat_points = []
    for loop in loops:
        flat_points.extend(loop)
    triangles = geometry.tessellate_polygon([[V(a, b, 0.0) for a, b in loop] for loop in loops])
    points = []
    for t in (t0, t1):
        for a, b in flat_points:
            points.append(origin + along * a + up * b + normal * t)
    count = len(flat_points)
    faces = []
    for tri in triangles:
        a, b, c = tri
        pa, pb, pc = flat_points[a], flat_points[b], flat_points[c]
        ccw = (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0]) > 0.0
        front = (count + a, count + b, count + c) if ccw else (count + a, count + c, count + b)
        back = (a, c, b) if ccw else (a, b, c)
        faces.append(orient(front, points, normal))
        faces.append(orient(back, points, -normal))
    if sides:
        start = 0
        for loop in loops:
            n = len(loop)
            for i in range(n):
                j = (i + 1) % n
                pa = loop[i]
                pb = loop[j]
                da = pb[0] - pa[0]
                db = pb[1] - pa[1]
                expected = along * db - up * da
                face = (start + i, start + j, count + start + j, count + start + i)
                faces.append(orient(face, points, expected))
            start += n
    return Geo(points, faces)


def geo_grid(width, height, nx, ny, lift=None):
    points = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -width * 0.5 + width * i / nx
            y = -height * 0.5 + height * j / ny
            points.append(V(x, y, lift(x, y) if lift else 0.0))
    faces = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return Geo(points, faces)


def smooth_noise(rng_local, count=5, scale=1.0):
    waves = []
    for index in range(count):
        direction = Vector((rng_local.gauss(0, 1), rng_local.gauss(0, 1), rng_local.gauss(0, 1))).normalized()
        waves.append((direction * rng_local.uniform(1.0, 3.5) * scale, rng_local.uniform(0, tau), rng_local.uniform(0.4, 1.0) / (index + 1) ** 0.5))
    total = sum(w for d, p, w in waves)

    def sample(point):
        return sum(math.sin(d.dot(point) + p) * w for d, p, w in waves) / total

    return sample


def geo_lump(rx, ry, rz, rng_local, subdivisions=2, rough=0.25, floor=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    sample = smooth_noise(rng_local, 6)
    fine = smooth_noise(rng_local, 5, 3.0)
    points = []
    lookup = {}
    for vert in bm.verts:
        n = vert.co.normalized()
        scale = 1.0 + rough * sample(n) + rough * 0.35 * fine(n)
        p = V(n.x * rx * scale, n.y * ry * scale, n.z * rz * scale)
        if floor is not None and p.z < floor:
            p.z = floor
        lookup[vert] = len(points)
        points.append(p)
    faces = [tuple(lookup[v] for v in face.verts) for face in bm.faces]
    bm.free()
    return Geo(points, faces)


def place(position, forward=None, up=None):
    matrix = Matrix.Identity(4)
    if forward is not None:
        x_axis = forward.normalized()
        z_axis = up if up is not None else V(0.0, 0.0, 1.0)
        z_axis = z_axis - x_axis * z_axis.dot(x_axis)
        if z_axis.length < 1e-6:
            z_axis = x_axis.orthogonal()
        z_axis.normalize()
        y_axis = z_axis.cross(x_axis)
        matrix = Matrix((tuple(x_axis) + (0.0,), tuple(y_axis) + (0.0,), tuple(z_axis) + (0.0,), (0.0, 0.0, 0.0, 1.0))).transposed()
    matrix.translation = position
    return matrix


def turned(position, yaw=0.0, pitch=0.0, roll=0.0):
    return Matrix.Translation(position) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'Y') @ Matrix.Rotation(roll, 4, 'X')


def block(part, name, low, high, bevel=0.0, mapping="box", matrix=None, skip=()):
    low, high = V(min(low.x, high.x), min(low.y, high.y), min(low.z, high.z)), V(max(low.x, high.x), max(low.y, high.y), max(low.z, high.z))
    size3 = high - low
    if size3.x < 1e-5 or size3.y < 1e-5 or size3.z < 1e-5:
        return
    geo = geo_cbox(size3.x, size3.y, size3.z, bevel) if bevel > 0.0 else geo_box(size3.x, size3.y, size3.z, skip)
    local = Matrix.Translation((low + high) * 0.5)
    emit(part, geo, name, local if matrix is None else matrix @ local, mapping)


def member(part, name, a, b, width, height, up=None, bevel=0.0, mapping="board", extend=0.0):
    axis = b - a
    length = axis.length + extend * 2.0
    if length < 1e-4:
        return
    forward = axis.normalized()
    if up is None:
        up = V(0.0, 0.0, 1.0) if abs(forward.z) < 0.9 else V(1.0, 0.0, 0.0)
    geo = geo_cbox(length, width, height, bevel) if bevel > 0.0 else geo_box(length, width, height)
    emit(part, geo, name, place((a + b) * 0.5, forward, up), mapping)


def rod(part, name, a, b, radius, sides=8, mapping="given", caps=True):
    if (b - a).length < 1e-4:
        return
    emit(part, geo_tube([a, b], circle(radius, sides), caps), name, None, mapping, True)


class Build:
    def __init__(self, name, seed):
        global rng
        self.name = name
        self.rng = random.Random(seed)
        rng = self.rng
        self.parts = {}
        self.boxes = []
        self.counters = {}
        load_catalog()

    def part(self, key, sharp=35.0):
        if key not in self.parts:
            self.parts[key] = Part(self.name + "_" + key, sharp)
        return self.parts[key]

    def unique(self, base):
        self.counters[base] = self.counters.get(base, 0) + 1
        return base + "_" + str(self.counters[base])

    def col(self, surface, tag, low, high):
        lo = V(min(low.x, high.x), min(low.y, high.y), min(low.z, high.z))
        hi = V(max(low.x, high.x), max(low.y, high.y), max(low.z, high.z))
        if (hi - lo).x < 0.01 or (hi - lo).y < 0.01 or (hi - lo).z < 0.01:
            return
        self.boxes.append((self.unique("col_" + surface + "_" + tag), lo, hi))

    def ramp(self, direction, surface, tag, low, high):
        lo = V(min(low.x, high.x), min(low.y, high.y), min(low.z, high.z))
        hi = V(max(low.x, high.x), max(low.y, high.y), max(low.z, high.z))
        self.boxes.append((self.unique("ramp_" + direction + "_" + surface + "_" + tag), lo, hi))

    def loot(self, kind, position):
        self.boxes.append((self.unique("loot_" + kind), position + V(-0.05, -0.05, 0.0), position + V(0.05, 0.05, 0.1)))

    def light(self, kind, position):
        self.boxes.append((self.unique("light_" + kind), position - V(0.05, 0.05, 0.05), position + V(0.05, 0.05, 0.05)))

    def finish(self):
        objects = []
        marker = None
        for key, part in self.parts.items():
            if part.faces:
                objects.append(part.build())
                if marker is None:
                    marker = material(part.slots[0])
        for name, lo, hi in self.boxes:
            objects.append(box_object(name, lo, hi, marker))
        return objects

    def triangles(self):
        return sum(part.triangles() for part in self.parts.values())


def box_object(name, lo, hi, marker=None):
    points = [(lo.x, lo.y, lo.z), (hi.x, lo.y, lo.z), (hi.x, hi.y, lo.z), (lo.x, hi.y, lo.z), (lo.x, lo.y, hi.z), (hi.x, lo.y, hi.z), (hi.x, hi.y, hi.z), (lo.x, hi.y, hi.z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (0, 4, 7, 3), (1, 2, 6, 5)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0] * 6)
    if marker is not None:
        mesh.materials.append(marker)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def frame_point(frame, a, b, t):
    origin, along, up, normal = frame
    return origin + along * a + up * b + normal * t


def box_between(p, q):
    return V(min(p.x, q.x), min(p.y, q.y), min(p.z, q.z)), V(max(p.x, q.x), max(p.y, q.y), max(p.z, q.z))


def wall_boxes(build, surface, tag, frame, a0, a1, b0, b1, thickness, openings, t_out=0.0, door_min=1.04):
    widened = []
    for o in openings:
        if o[3] - o[2] >= 1.9 and o[1] - o[0] < door_min:
            middle = (o[0] + o[1]) * 0.5
            o = (middle - door_min * 0.5, middle + door_min * 0.5, o[2], o[3])
        widened.append(o)
    openings = widened
    cuts = sorted(set([a0, a1] + [c for o in openings for c in (o[0], o[1]) if a0 < c < a1]))
    columns = []
    for c0, c1 in zip(cuts[:-1], cuts[1:]):
        middle = (c0 + c1) * 0.5
        blocked = sorted((o[2], o[3]) for o in openings if o[0] <= middle <= o[1])
        free = []
        start = b0
        for lo, hi in blocked:
            if lo > start + 0.01:
                free.append((start, min(lo, b1)))
            start = max(start, hi)
        if start < b1 - 0.01:
            free.append((start, b1))
        if columns and columns[-1][2] == free:
            columns[-1] = (columns[-1][0], c1, free)
        else:
            columns.append((c0, c1, free))
    for c0, c1, free in columns:
        for lo, hi in free:
            low, high = box_between(frame_point(frame, c0, lo, t_out - thickness), frame_point(frame, c1, hi, t_out))
            build.col(surface, tag, low, high)


def rect(a0, a1, b0, b1):
    return [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]


def notched(a0, a1, b0, b1, notches):
    points = [(a0, b0)]
    for n0, n1, top in sorted(notches):
        points += [(n0, b0), (n0, top), (n1, top), (n1, b0)]
    points += [(a1, b0), (a1, b1), (a0, b1)]
    return points


def plane(origin, normal):
    return (origin, V(0.0, 0.0, 1.0).cross(normal).normalized(), V(0.0, 0.0, 1.0), normal.normalized())


def blob(cx, cy, rx, ry, rng_local, count=26, rough=0.34):
    harmonics = [(k, rng_local.uniform(0.0, rough) / k ** 0.65, rng_local.uniform(0.0, tau)) for k in range(2, 10)]
    turn = rng_local.uniform(0.0, math.pi)
    cosine = math.cos(turn)
    sine = math.sin(turn)
    points = []
    for index in range(count):
        angle = tau * index / count
        scale = max(0.35, 1.0 + sum(a * math.cos(k * angle + p) for k, a, p in harmonics))
        scale *= 1.0 + rng_local.uniform(-0.035, 0.035)
        px = math.cos(angle) * rx * scale
        py = math.sin(angle) * ry * scale
        points.append((cx + px * cosine - py * sine, cy + px * sine + py * cosine))
    return points


def wander(rng_local, count=4):
    waves = [(rng_local.uniform(0.6, 3.2), rng_local.uniform(0.0, tau), rng_local.uniform(0.4, 1.0)) for index in range(count)]
    total = sum(w for f, p, w in waves)

    def sample(x):
        return 0.5 + 0.5 * sum(math.sin(f * x + p) * w for f, p, w in waves) / total

    return sample


def polygon_bounds(polygon):
    return min(p[0] for p in polygon), max(p[0] for p in polygon), min(p[1] for p in polygon), max(p[1] for p in polygon)


def overlaps(box_a, box_b, margin):
    return not (box_a[1] + margin < box_b[0] or box_b[1] + margin < box_a[0] or box_a[3] + margin < box_b[2] or box_b[3] + margin < box_a[2])


def scatter_patches(region, avoid, count, size_range, rng_local, aspect=(0.6, 1.2), bias=None, attempts=60):
    a0, a1, b0, b1 = region
    patches = []
    taken = [polygon_bounds(p) for p in avoid]
    for number in range(count):
        for attempt in range(attempts):
            rx = rng_local.uniform(*size_range)
            ry = rx * rng_local.uniform(*aspect)
            cx = rng_local.uniform(a0 + rx * 1.4, a1 - rx * 1.4)
            cy = bias(rng_local) if bias is not None else rng_local.uniform(b0 + ry * 1.4, b1 - ry * 1.4)
            cy = min(max(cy, b0 + ry * 1.4), b1 - ry * 1.4)
            shape = blob(cx, cy, rx, ry, rng_local)
            bounds = polygon_bounds(shape)
            if bounds[0] < a0 + 0.03 or bounds[1] > a1 - 0.03 or bounds[2] < b0 + 0.03 or bounds[3] > b1 - 0.03:
                continue
            if any(overlaps(bounds, other, 0.06) for other in taken):
                continue
            patches.append(shape)
            taken.append(bounds)
            break
    return patches


def export_building(folder, objects):
    directory = os.path.join(models_root, folder)
    os.makedirs(directory, exist_ok=True)
    for entry in os.listdir(directory):
        if entry.endswith((".gltf", ".bin")):
            os.remove(os.path.join(directory, entry))
    path = os.path.join(directory, folder + ".gltf")
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in objects)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_keep_originals=True, export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_yup=True, export_apply=True, export_skins=False, export_animations=False, export_morph=False, export_cameras=False, export_lights=False, export_extras=False)
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    for image in document.get("images", []):
        if "uri" in image:
            uri = unquote(image["uri"])
            absolute = uri if os.path.isabs(uri) else os.path.normpath(os.path.join(directory, uri))
            image["uri"] = os.path.relpath(absolute, directory).replace("\\", "/")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
    return path, document


def audit(path, document):
    directory = os.path.dirname(path)
    names = [node.get("name", "") for node in document.get("nodes", [])]
    problems = []
    if len(set(names)) != len(names):
        problems.append("duplicate node names")
    for name in names:
        if not name.isascii() or len(name) > 47 or "." in name:
            problems.append("bad name " + name)
    triangles = 0
    markers = {"col": 0, "ramp": 0, "loot": 0, "light": 0}
    accessors = document.get("accessors", [])
    for node in document.get("nodes", []):
        if "mesh" not in node:
            continue
        name = node.get("name", "")
        mesh = document["meshes"][node["mesh"]]
        for primitive in mesh["primitives"]:
            if "TEXCOORD_0" not in primitive["attributes"]:
                problems.append("no uv " + name)
            count = accessors[primitive["indices"]]["count"] // 3 if "indices" in primitive else accessors[primitive["attributes"]["POSITION"]]["count"] // 3
            prefix = name.split("_")[0]
            if prefix in markers:
                continue
            triangles += count
        prefix = name.split("_")[0]
        if prefix in markers:
            markers[prefix] += 1
        if "scale" in node or "rotation" in node:
            problems.append("transform on " + name)
    for image in document.get("images", []):
        uri = image.get("uri", "")
        if not os.path.exists(os.path.normpath(os.path.join(directory, uri))):
            problems.append("missing image " + uri)
    stray = [entry for entry in os.listdir(directory) if entry.endswith(".png") and not any(image.get("uri", "") == entry for image in document.get("images", []))]
    if stray:
        problems.append("stray files " + ",".join(stray))
    materials = [m.get("name") for m in document.get("materials", [])]
    print("AUDIT", os.path.basename(path), "tris", triangles, "markers", markers, "materials", len(materials), "images", len(document.get("images", [])), "problems", problems if problems else "none", flush=True)
    return triangles, markers, materials, problems


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    material_cache.clear()


def facade(side, half_x, half_y):
    if side == "front":
        return (V(0.0, -half_y, 0.0), V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), V(0.0, -1.0, 0.0))
    if side == "back":
        return (V(0.0, half_y, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), V(0.0, 1.0, 0.0))
    if side == "left":
        return (V(-half_x, 0.0, 0.0), V(0.0, -1.0, 0.0), V(0.0, 0.0, 1.0), V(-1.0, 0.0, 0.0))
    return (V(half_x, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), V(1.0, 0.0, 0.0))


def shifted(frame, offset):
    origin, along, up, normal = frame
    return (origin + offset, along, up, normal)


def frame_matrix(frame):
    origin, along, up, normal = frame
    inward = -normal
    return Matrix(((along.x, inward.x, up.x, origin.x), (along.y, inward.y, up.y, origin.y), (along.z, inward.z, up.z, origin.z), (0.0, 0.0, 0.0, 1.0)))


def along_of(frame, point):
    return (point - frame[0]).dot(frame[1])


def frame_block(part, name, frame, a0, a1, b0, b1, d0, d1, bevel=0.0, mapping="box"):
    block(part, name, V(min(a0, a1), min(d0, d1), min(b0, b1)), V(max(a0, a1), max(d0, d1), max(b0, b1)), bevel, mapping, frame_matrix(frame))


def wall(part, name, frame, outline, holes, thickness, t_out=0.0):
    origin, along, up, normal = frame
    emit(part, geo_slab(origin, along, up, normal, outline, holes, t_out - thickness, t_out), name, None, "world")


def skin(part, name, frame, outline, holes, thickness, t_out=0.0, sides=True):
    origin, along, up, normal = frame
    emit(part, geo_slab(origin, along, up, normal, outline, holes, t_out, t_out + thickness, sides), name, None, "world")


def prism(part, name, matrix, polygon, y0, y1, mapping="box"):
    emit(part, geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), V(0.0, -1.0, 0.0), polygon, [], -y1, -y0), name, matrix, mapping)


def quoins(part, name, corner, ua, ub, z0, z1, rng_local, protrude=0.025, joint=0.012, bevel=0.02, long_range=(0.42, 0.6), short_range=(0.2, 0.3)):
    z = z0
    course = 0
    while z < z1 - 0.1:
        h = rng_local.uniform(0.24, 0.34)
        if z + h > z1 - 0.12:
            h = z1 - z
        la = rng_local.uniform(*long_range) if course % 2 == 0 else rng_local.uniform(*short_range)
        lb = rng_local.uniform(*short_range) if course % 2 == 0 else rng_local.uniform(*long_range)
        p = protrude * rng_local.uniform(0.6, 1.3)
        corners = [corner + ua * s + ub * t for s in (-p, la - joint * 0.5) for t in (-p, lb - joint * 0.5)]
        low = V(min(q.x for q in corners), min(q.y for q in corners), z + joint * 0.5)
        high = V(max(q.x for q in corners), max(q.y for q in corners), z + h - joint * 0.5)
        block(part, name, low, high, bevel * rng_local.uniform(0.7, 1.3))
        z += h
        course += 1


def lintel_stone(part, name, frame, a0, a1, b, height=0.28, depth=0.3, protrude=0.02, extend=0.2, bevel=0.018):
    frame_block(part, name, frame, a0 - extend, a1 + extend, b, b + height, -protrude, depth, bevel)


def sill_stone(part, name, frame, a0, a1, b, depth=0.2, protrude=0.06, thick=0.09, extend=0.07, bevel=0.012):
    frame_block(part, name, frame, a0 - extend, a1 + extend, b - thick, b, -protrude, depth, bevel)


def jamb_stones(part, name, frame, edge_a, away, b0, b1, rng_local, depth=0.3, protrude=0.018, bevel=0.016):
    b = b0
    course = 0
    while b < b1 - 0.1:
        h = rng_local.uniform(0.26, 0.36)
        if b + h > b1 - 0.12:
            h = b1 - b
        w = rng_local.uniform(0.2, 0.28) if course % 2 == 0 else rng_local.uniform(0.34, 0.44)
        frame_block(part, name, frame, edge_a, edge_a + away * w, b + 0.006, b + h - 0.006, -protrude * rng_local.uniform(0.6, 1.2), depth, bevel)
        b += h
        course += 1


def local_block(part, name, matrix, x0, x1, y0, y1, z0, z1, bevel=0.0, mapping="box"):
    block(part, name, V(min(x0, x1), min(y0, y1), min(z0, z1)), V(max(x0, x1), max(y0, y1), max(z0, z1)), bevel, mapping, matrix)


def pane(part, matrix, x0, x1, z0, z1, y, state, rng_local, name="glass_dirty"):
    if state == "missing":
        return
    if state == "whole":
        local_block(part, name, matrix, x0, x1, y, y + 0.004, z0, z1)
        return
    w = x1 - x0
    h = z1 - z0
    corner = rng_local.choice(((x0, z0, 1, 1), (x1, z0, -1, 1), (x1, z1, -1, -1), (x0, z1, 1, -1)))
    cx, cz, sx, sz = corner
    reach_x = w * rng_local.uniform(0.35, 0.95)
    reach_z = h * rng_local.uniform(0.3, 0.9)
    points = [(cx, cz), (cx + sx * reach_x, cz)]
    steps = rng_local.randint(1, 3)
    for step in range(steps):
        t = (step + 1) / (steps + 1)
        points.append((cx + sx * reach_x * (1 - t) * rng_local.uniform(0.6, 1.1), cz + sz * reach_z * t * rng_local.uniform(0.7, 1.2)))
    points.append((cx, cz + sz * reach_z))
    points = [(min(max(px, x0), x1), min(max(pz, z0), z1)) for px, pz in points]
    if abs(signed_area(points)) < 1e-4:
        return
    prism(part, name, matrix, points, y, y + 0.004)


def glazed_leaf(part, paint, matrix, x0, x1, z0, z1, depth, cols, rows, rng_local, glass_states, stile=0.045, bottom=0.06, bar=0.018):
    local_block(part, paint, matrix, x0, x0 + stile, 0.0, depth, z0, z1, 0.003, "board")
    local_block(part, paint, matrix, x1 - stile, x1, 0.0, depth, z0, z1, 0.003, "board")
    local_block(part, paint, matrix, x0 + stile, x1 - stile, 0.0, depth, z0, z0 + bottom, 0.003, "board")
    local_block(part, paint, matrix, x0 + stile, x1 - stile, 0.0, depth, z1 - stile, z1, 0.003, "board")
    ix0 = x0 + stile
    ix1 = x1 - stile
    iz0 = z0 + bottom
    iz1 = z1 - stile
    for c in range(1, cols):
        x = ix0 + (ix1 - ix0) * c / cols
        local_block(part, paint, matrix, x - bar * 0.5, x + bar * 0.5, depth * 0.2, depth * 0.8, iz0, iz1, 0.0, "board")
    for r in range(1, rows):
        z = iz0 + (iz1 - iz0) * r / rows
        local_block(part, paint, matrix, ix0, ix1, depth * 0.2, depth * 0.8, z - bar * 0.5, z + bar * 0.5, 0.0, "board")
    for c in range(cols):
        for r in range(rows):
            px0 = ix0 + (ix1 - ix0) * c / cols + bar * 0.5
            px1 = ix0 + (ix1 - ix0) * (c + 1) / cols - bar * 0.5
            pz0 = iz0 + (iz1 - iz0) * r / rows + bar * 0.5
            pz1 = iz0 + (iz1 - iz0) * (r + 1) / rows - bar * 0.5
            pane(part, matrix, px0, px1, pz0, pz1, depth * 0.45, glass_states(), rng_local)


def glass_chooser(rng_local, whole, shard):
    def choose():
        roll = rng_local.random()
        if roll < whole:
            return "whole"
        if roll < whole + shard:
            return "shard"
        return "missing"
    return choose


def window_frame(part, paint, frame, a0, a1, b0, b1, depth, fw=0.065, fd=0.085):
    frame_block(part, paint, frame, a0, a0 + fw, b0, b1, depth, depth + fd, 0.004, "board")
    frame_block(part, paint, frame, a1 - fw, a1, b0, b1, depth, depth + fd, 0.004, "board")
    frame_block(part, paint, frame, a0 + fw, a1 - fw, b1 - fw, b1, depth, depth + fd, 0.004, "board")
    frame_block(part, paint, frame, a0 + fw, a1 - fw, b0, b0 + 0.07, depth - 0.035, depth + fd, 0.004, "board")
    return a0 + fw, a1 - fw, b0 + 0.07, b1 - fw


def casement_window(part, paint, frame, a0, a1, b0, b1, depth, rng_local, leaf_angles=None, whole=0.35, shard=0.3, rows=3):
    ia0, ia1, ib0, ib1 = window_frame(part, paint, frame, a0, a1, b0, b1, depth)
    base = frame_matrix(frame)
    choose = glass_chooser(rng_local, whole, shard)
    if ia1 - ia0 > 0.55:
        middle = (ia0 + ia1) * 0.5
        frame_block(part, paint, frame, middle - 0.028, middle + 0.028, ib0, ib1, depth, depth + 0.085, 0.003, "board")
        spans = [(ia0, middle - 0.028, True), (middle + 0.028, ia1, False)]
    else:
        spans = [(ia0, ia1, True)]
    angles = leaf_angles or [0.0] * len(spans)
    for (x0, x1, hinge_left), angle in zip(spans, angles):
        if angle is None:
            continue
        w = x1 - x0 - 0.006
        if hinge_left:
            matrix = base @ Matrix.Translation(V(x0 + 0.003, depth + 0.012, 0.0)) @ Matrix.Rotation(-math.radians(angle), 4, 'Z')
            glazed_leaf(part, paint, matrix, 0.0, w, ib0 + 0.004, ib1 - 0.004, 0.042, 1, rows, rng_local, choose)
        else:
            matrix = base @ Matrix.Translation(V(x1 - 0.003, depth + 0.012, 0.0)) @ Matrix.Rotation(math.radians(angle), 4, 'Z')
            glazed_leaf(part, paint, matrix, -w, 0.0, ib0 + 0.004, ib1 - 0.004, 0.042, 1, rows, rng_local, choose)


def sash_window(part, paint, frame, a0, a1, b0, b1, depth, rng_local, lift=0.0, whole=0.3, shard=0.3, cols=3, rows=2):
    ia0, ia1, ib0, ib1 = window_frame(part, paint, frame, a0, a1, b0, b1, depth, 0.07, 0.11)
    base = frame_matrix(frame)
    choose = glass_chooser(rng_local, whole, shard)
    middle = (ib0 + ib1) * 0.5
    upper = base @ Matrix.Translation(V(0.0, depth + 0.012, 0.0))
    glazed_leaf(part, paint, upper, ia0 + 0.003, ia1 - 0.003, middle - 0.02, ib1 - 0.003, 0.04, cols, rows, rng_local, choose, 0.045, 0.035, 0.016)
    lower = base @ Matrix.Translation(V(0.0, depth + 0.055, min(lift, middle - ib0 - 0.05)))
    glazed_leaf(part, paint, lower, ia0 + 0.003, ia1 - 0.003, ib0 + 0.003, middle + 0.02, 0.04, cols, rows, rng_local, choose, 0.045, 0.06, 0.016)


def shutter(part, paint, frame, hinge_a, direction, b0, b1, width, angle, rng_local, style="ledged", hang=0.0, iron="rusty_metal"):
    thick = 0.024 if style == "ledged" else 0.03
    base = frame_matrix(frame) @ Matrix.Translation(V(hinge_a, -thick - 0.006, 0.0))
    swing = Matrix.Rotation(-direction * math.radians(angle), 4, 'Z')
    pivot = V(0.0, 0.0, b1 - 0.12)
    sag = Matrix.Translation(pivot) @ Matrix.Rotation(direction * math.radians(hang), 4, 'Y') @ Matrix.Translation(-pivot)
    matrix = base @ swing @ sag
    x0, x1 = (0.0, width) if direction > 0 else (-width, 0.0)
    if style == "ledged":
        count = max(2, int(round(width / 0.12)))
        for index in range(count):
            a = x0 + width * index / count + 0.002
            b = x0 + width * (index + 1) / count - 0.002
            local_block(part, paint, matrix, a, b, 0.0, thick, b0 + rng_local.uniform(0.0, 0.01), b1 - rng_local.uniform(0.0, 0.015), 0.002, "board")
        for z in (b0 + 0.12, b1 - 0.12):
            local_block(part, paint, matrix, x0 + 0.03, x1 - 0.03, thick, thick + 0.02, z - 0.045, z + 0.045, 0.003, "board")
        for z in (b0 + 0.12, b1 - 0.12):
            local_block(part, iron, matrix, x0 + (0.0 if direction > 0 else width * 0.35), x0 + (width * 0.65 if direction > 0 else width), -0.004, 0.0, z - 0.018, z + 0.018)
    else:
        local_block(part, paint, matrix, x0, x0 + 0.05, 0.0, thick, b0, b1, 0.003, "board")
        local_block(part, paint, matrix, x1 - 0.05, x1, 0.0, thick, b0, b1, 0.003, "board")
        rails = [(b0, b0 + 0.09), ((b0 + b1) * 0.5 - 0.03, (b0 + b1) * 0.5 + 0.03), (b1 - 0.07, b1)]
        for z0, z1 in rails:
            local_block(part, paint, matrix, x0 + 0.05, x1 - 0.05, 0.0, thick, z0, z1, 0.003, "board")
        for (z0, z1), (z2, z3) in zip(rails[:-1], rails[1:]):
            z = z1 + 0.03
            while z < z2 - 0.02:
                if rng_local.random() > 0.06:
                    slat = Matrix.Translation(V((x0 + x1) * 0.5, thick * 0.5, z)) @ Matrix.Rotation(math.radians(48.0 + rng_local.uniform(-6.0, 6.0)), 4, 'X')
                    emit(part, geo_box(width - 0.1, 0.045, 0.007), paint, matrix @ slat, "board")
                z += 0.038
        for z in (b0 + 0.15, b1 - 0.15):
            local_block(part, iron, matrix, x0 + (0.0 if direction > 0 else width - 0.12), x0 + (0.12 if direction > 0 else width), -0.004, 0.0, z - 0.015, z + 0.015)


def door_leaf(part, paint, frame, hinge_a, direction, d_axis, b0, height, width, angle, rng_local, style="ledged", hang=0.0, iron="rusty_metal"):
    thick = 0.045
    base = frame_matrix(frame) @ Matrix.Translation(V(hinge_a, d_axis, 0.0))
    swing = Matrix.Rotation(direction * math.radians(angle), 4, 'Z')
    pivot = V(0.0, 0.0, b0 + height - 0.2)
    sag = Matrix.Translation(pivot) @ Matrix.Rotation(-direction * math.radians(hang), 4, 'Y') @ Matrix.Translation(-pivot)
    matrix = base @ swing @ sag
    x0, x1 = (0.0, width) if direction > 0 else (-width, 0.0)
    b1 = b0 + height
    if style == "ledged":
        count = max(4, int(round(width / 0.15)))
        for index in range(count):
            a = x0 + width * index / count + 0.002
            b = x0 + width * (index + 1) / count - 0.002
            local_block(part, paint, matrix, a, b, 0.0, 0.028, b0 + rng_local.uniform(0.0, 0.02), b1 - rng_local.uniform(0.0, 0.01), 0.002, "board")
        levels = (b0 + 0.18, (b0 + b1) * 0.5, b1 - 0.18)
        for z in levels:
            local_block(part, paint, matrix, x0 + 0.04, x1 - 0.04, 0.028, thick, z - 0.07, z + 0.07, 0.004, "board")
        for z_low, z_high in ((levels[0], levels[1]), (levels[1], levels[2])):
            start = V(x0 + 0.08 if direction > 0 else x1 - 0.08, 0.0, z_low + 0.07)
            end = V(x1 - 0.08 if direction > 0 else x0 + 0.08, 0.0, z_high - 0.07)
            forward = (end - start).normalized()
            emit(part, geo_box((end - start).length, 0.11, 0.017), paint, matrix @ place((start + end) * 0.5 + V(0.0, 0.0365, 0.0), forward, V(0.0, 1.0, 0.0)), "board")
        for z in (levels[0], levels[2]):
            local_block(part, iron, matrix, x0 + (0.0 if direction > 0 else width * 0.45), x0 + (width * 0.55 if direction > 0 else width), -0.005, 0.0, z - 0.022, z + 0.022)
        local_block(part, iron, matrix, (x1 - 0.1) if direction > 0 else (x0 + 0.05), (x1 - 0.05) if direction > 0 else (x0 + 0.1), -0.02, 0.0, b0 + 1.0, b0 + 1.05)
    else:
        stile = 0.11
        local_block(part, paint, matrix, x0, x0 + stile, 0.0, thick, b0, b1, 0.004, "board")
        local_block(part, paint, matrix, x1 - stile, x1, 0.0, thick, b0, b1, 0.004, "board")
        rails = [(b0, b0 + 0.22), (b0 + 0.95, b0 + 1.12), (b1 - 0.13, b1)]
        for z0, z1 in rails:
            local_block(part, paint, matrix, x0 + stile, x1 - stile, 0.0, thick, z0, z1, 0.004, "board")
        muntin = (x0 + x1) * 0.5
        local_block(part, paint, matrix, muntin - 0.05, muntin + 0.05, 0.0, thick, rails[0][1], rails[2][0], 0.004, "board")
        for (z0, z1), (z2, z3) in zip(rails[:-1], rails[1:]):
            for px0, px1 in ((x0 + stile, muntin - 0.05), (muntin + 0.05, x1 - stile)):
                if rng_local.random() < 0.15:
                    continue
                local_block(part, paint, matrix, px0 + 0.005, px1 - 0.005, thick * 0.35, thick * 0.65, z1 + 0.005, z2 - 0.005, 0.0, "board")
                for side_y in (thick * 0.3, thick * 0.7):
                    local_block(part, paint, matrix, px0, px1, side_y - 0.008, side_y + 0.008, z1, z1 + 0.018, 0.0, "board")
                    local_block(part, paint, matrix, px0, px1, side_y - 0.008, side_y + 0.008, z2 - 0.018, z2, 0.0, "board")
        local_block(part, iron, matrix, muntin - 0.12, muntin + 0.12, -0.012, 0.0, b0 + 1.0, b0 + 1.06)
        emit(part, geo_lathe([(0.0, 0.0), (0.02, 0.0), (0.022, 0.012), (0.01, 0.02), (0.0, 0.022)], 10), iron, matrix @ Matrix.Translation(V(x1 - 0.12 if direction > 0 else x0 + 0.12, 0.0, b0 + 1.0)) @ Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)


def door_frame(part, paint, frame, a0, a1, b0, b1, depth, fw=0.07, fd=0.11):
    frame_block(part, paint, frame, a0, a0 + fw, b0, b1, depth, depth + fd, 0.004, "board")
    frame_block(part, paint, frame, a1 - fw, a1, b0, b1, depth, depth + fd, 0.004, "board")
    frame_block(part, paint, frame, a0, a1, b1 - fw, b1, depth, depth + fd, 0.004, "board")
    return a0 + fw, a1 - fw, b1 - fw


class Gable:
    def __init__(self, x0, x1, half, overhang, eave_top, pitch_degrees, origin_y=0.0):
        self.x0 = x0
        self.x1 = x1
        self.half = half
        self.edge = half + overhang
        self.pitch = math.radians(pitch_degrees)
        self.tan = math.tan(self.pitch)
        self.cos = math.cos(self.pitch)
        self.sin = math.sin(self.pitch)
        self.eave_top = eave_top
        self.ridge_top = eave_top + self.edge * self.tan
        self.run = self.edge / self.cos
        self.origin_y = origin_y

    def top(self, y):
        return self.ridge_top - abs(y - self.origin_y) * self.tan

    def under(self, y, depth):
        return self.top(y) - depth / self.cos

    def point(self, side, x, d, lift=0.0):
        return V(x, self.origin_y + side * (self.edge - d * self.cos), self.eave_top + d * self.sin) + self.normal(side) * lift

    def normal(self, side):
        return V(0.0, side * self.sin, self.cos)

    def upslope(self, side):
        return V(0.0, -side * self.cos, self.sin)

    def distance(self, y):
        return (self.edge - abs(y - self.origin_y)) / self.cos


def roof_slab(part, gable, side, x0, x1, name, depth=0.2, d0=0.0, d1=None):
    d1 = gable.run if d1 is None else d1
    tile = tile_of(name)
    top = [gable.point(side, x0, d0), gable.point(side, x1, d0), gable.point(side, x1, d1), gable.point(side, x0, d1)]
    points = top + [p - gable.normal(side) * depth for p in top]
    flat_uv = [(x0 / tile, d0 / tile), (x1 / tile, d0 / tile), (x1 / tile, d1 / tile), (x0 / tile, d1 / tile)]
    faces = []
    uvs = []
    for face, face_uv, expected in (((0, 1, 2, 3), flat_uv, gable.normal(side)), ((4, 5, 6, 7), flat_uv, -gable.normal(side)), ((0, 1, 5, 4), [flat_uv[0], flat_uv[1], (flat_uv[1][0], flat_uv[1][1] - depth / tile), (flat_uv[0][0], flat_uv[0][1] - depth / tile)], -gable.upslope(side)), ((3, 2, 6, 7), [flat_uv[3], flat_uv[2], (flat_uv[2][0], flat_uv[2][1] + depth / tile), (flat_uv[3][0], flat_uv[3][1] + depth / tile)], gable.upslope(side)), ((0, 3, 7, 4), [flat_uv[0], flat_uv[3], (flat_uv[3][0] - depth / tile, flat_uv[3][1]), (flat_uv[0][0] - depth / tile, flat_uv[0][1])], V(-1.0, 0.0, 0.0)), ((1, 2, 6, 5), [flat_uv[1], flat_uv[2], (flat_uv[2][0] + depth / tile, flat_uv[2][1]), (flat_uv[1][0] + depth / tile, flat_uv[1][1])], V(1.0, 0.0, 0.0))):
        oriented, oriented_uv = oriented_face(face, face_uv, points, expected)
        faces.append(oriented)
        uvs.append(oriented_uv)
    emit(part, Geo(points, faces, uvs), name, None, "texture")


def oriented_face(face, face_uv, points, expected):
    if newell([points[i] for i in face]).dot(expected) < 0.0:
        return tuple(reversed(face)), list(reversed(face_uv))
    return face, face_uv


def slate_geo(gable, side, xa, xb, d0, length, thick, lift_butt, cell, tile, rng_local, broken=False, spin=0.0):
    cu0, cu1, cv0, cv1 = cell
    cx = (xa + xb) * 0.5
    cd = d0 + length * 0.5
    cosine = math.cos(spin)
    sine = math.sin(spin)
    up = gable.upslope(side)

    def at(x, d, n):
        rx = cx + (x - cx) * cosine - (d - cd) * sine
        rd = cd + (x - cx) * sine + (d - cd) * cosine
        return gable.point(side, rx, rd, n)

    def lift(d):
        return lift_butt * (1.0 - (d - d0) / length)

    def uv(x, d):
        return (cu0 + (x - xa) / (xb - xa) * (cu1 - cu0), cv0 + (d - d0) / tile)

    outline = [(xa, d0), (xb, d0), (xb, d0 + length), (xa, d0 + length)]
    if broken:
        cut_x = rng_local.uniform(0.05, 0.14)
        cut_d = rng_local.uniform(0.04, 0.14)
        if rng_local.random() < 0.5:
            outline = [(xa, d0 + cut_d), (xa + cut_x, d0), (xb, d0), (xb, d0 + length), (xa, d0 + length)]
        else:
            outline = [(xa, d0), (xb - cut_x, d0), (xb, d0 + cut_d), (xb, d0 + length), (xa, d0 + length)]
    count = len(outline)
    points = [at(x, d, lift(d)) for x, d in outline] + [at(x, d, lift(d) + thick) for x, d in outline]
    faces = []
    uvs = []
    face, face_uv = oriented_face(tuple(range(count, 2 * count)), [uv(x, d) for x, d in outline], points, gable.normal(side))
    faces.append(face)
    uvs.append(face_uv)
    sliver = thick / tile
    for i in range(count):
        j = (i + 1) % count
        (xi, di), (xj, dj) = outline[i], outline[j]
        if di > d0 + length - 1e-6 and dj > d0 + length - 1e-6:
            continue
        expected = V(dj - di, 0.0, 0.0) + up * (xi - xj)
        base = [uv(xi, di), uv(xj, dj), (uv(xj, dj)[0], uv(xj, dj)[1] + sliver), (uv(xi, di)[0], uv(xi, di)[1] + sliver)]
        face, face_uv = oriented_face((i, j, count + j, count + i), base, points, expected)
        faces.append(face)
        uvs.append(face_uv)
    return Geo(points, faces, uvs)


def slate_roof(part, gable, side, rng_local, moss=None, missing=None, slipped=None, name="slate_roof", moss_name="roof_moss", gauge=0.2, length=0.46, width=0.3, thick=0.008, gap=0.004, x0=None, x1=None, d_end=None):
    x0 = gable.x0 if x0 is None else x0
    x1 = gable.x1 if x1 is None else x1
    tile = tile_of(name)
    cells = catalog[name]["cells"]
    end = (gable.run if d_end is None else d_end)
    course = 0
    d = 0.0
    count = 0
    while d < end - 0.06:
        span = min(length, end + 0.03 - d)
        offset = (width * 0.5) if course % 2 else 0.0
        edges = [x0]
        x = x0 + offset if offset > 0.0 else x0 + width
        while x < x1 - 0.1:
            edges.append(x)
            x += width
        edges.append(x1)
        if len(edges) > 2 and edges[1] - edges[0] < 0.1:
            edges.pop(1)
        for xa, xb in zip(edges[:-1], edges[1:]):
            xa_g = xa + gap * 0.5
            xb_g = xb - gap * 0.5
            mid = (xa + xb) * 0.5
            if missing is not None and missing(mid, d):
                continue
            slip = slipped(mid, d) if slipped is not None else 0.0
            lift_butt = thick * (1.0 if course == 0 else 2.0) + rng_local.uniform(-0.0015, 0.0015)
            spin = rng_local.uniform(-0.012, 0.012) + (rng_local.uniform(-0.12, 0.12) if slip > 0.0 else 0.0)
            broken = rng_local.random() < 0.05
            cell = rng_local.choice(cells)
            chosen = moss_name if moss is not None and moss(mid, d) else name
            geo = slate_geo(gable, side, xa_g, xb_g, d - slip + rng_local.uniform(-0.004, 0.004), span, thick, lift_butt + (0.006 if slip > 0.0 else 0.0), cell, tile, rng_local, broken, spin)
            emit(part, geo, chosen, None, "texture")
            count += 1
        d += gauge
        course += 1
    return count


def pantile_roof(part, gable, side, rng_local, x0=None, x1=None, missing=None, name="clay_roof_tiles", gauge=0.3, width=0.24, amplitude=0.022, step=0.06, d_end=None, lift=0.0):
    tile = tile_of(name)
    courses = catalog[name]["courses"]
    x0 = gable.x0 if x0 is None else x0
    x1 = gable.x1 if x1 is None else x1
    first = math.floor(x0 / width) * width
    last = math.ceil(x1 / width) * width
    end = gable.run if d_end is None else d_end
    normal = gable.normal(side)
    down = -gable.upslope(side)
    d = 0.0
    course = 0
    count = 0
    while d < end - 0.05:
        length = min(gauge + 0.07, end + 0.04 - d)
        sag = rng_local.uniform(-0.004, 0.004)
        runs = []
        x = first
        start = None
        while x < last - 1e-6:
            present = not (missing is not None and missing(x + width * 0.5, d))
            if present and start is None:
                start = x
            if not present and start is not None:
                runs.append((start, x))
                start = None
            if present:
                count += 1
            x += width
        if start is not None:
            runs.append((start, last))
        v0 = (course % courses) / courses
        for xa, xb in runs:
            columns = max(1, int(round((xb - xa) / step)))
            points = []
            for j in range(columns + 1):
                x = xa + (xb - xa) * j / columns
                wave = amplitude * math.cos(tau * x / width) + sag * math.sin(x * 0.9) + rng_local.uniform(-0.0015, 0.0015)
                points.append(gable.point(side, x, d, lift + 0.012 + wave))
                points.append(gable.point(side, x, d, lift + 0.034 + wave))
                points.append(gable.point(side, x, d + length, lift + 0.006 + wave * 0.9))
            faces = []
            uvs = []
            for j in range(columns):
                a = j * 3
                xj = xa + (xb - xa) * j / columns
                xk = xa + (xb - xa) * (j + 1) / columns
                face, face_uv = oriented_face((a, a + 3, a + 4, a + 1), [(xj / tile, v0 - 0.012), (xk / tile, v0 - 0.012), (xk / tile, v0 + 0.002), (xj / tile, v0 + 0.002)], points, down)
                faces.append(face)
                uvs.append(face_uv)
                face, face_uv = oriented_face((a + 1, a + 4, a + 5, a + 2), [(xj / tile, v0 + 0.002), (xk / tile, v0 + 0.002), (xk / tile, v0 + length / tile), (xj / tile, v0 + length / tile)], points, normal)
                faces.append(face)
                uvs.append(face_uv)
            emit(part, Geo(points, faces, uvs), name, None, "texture", True)
        d += gauge
        course += 1
    return count


def corrugated_sheet(part, origin, across, along, width, length, rng_local, name="corrugated_rusty", depth=0.009, waves=13.0, segments=6, thickness=0.0015, sag=0.0, rows=1, phase=0.0, warp=0.0):
    tile = tile_of(name)
    across = across.normalized()
    along = along.normalized()
    normal = across.cross(along).normalized()
    pitch = 1.0 / waves
    columns = max(2, int(round(width / pitch * segments)))
    front = []
    for r in range(rows + 1):
        t = length * r / rows
        bend = sag * math.sin(math.pi * r / rows) if rows > 1 else 0.0
        for c in range(columns + 1):
            s = width * c / columns
            lift = depth * math.cos(tau * (s + phase) / pitch) - bend + warp * (s / width - 0.5) * (t / length)
            front.append(origin + across * s + along * t + normal * lift)
    back = [p - normal * thickness for p in front]
    points = front + back
    total = len(front)
    faces = []
    uvs = []
    for r in range(rows):
        for c in range(columns):
            a = r * (columns + 1) + c
            quad = (a, a + 1, a + columns + 2, a + columns + 1)
            s0 = (width * c / columns + phase) / tile
            s1 = (width * (c + 1) / columns + phase) / tile
            t0 = length * r / rows / tile
            t1 = length * (r + 1) / rows / tile
            quad_uv = [(s0, t0), (s1, t0), (s1, t1), (s0, t1)]
            face, face_uv = oriented_face(quad, quad_uv, points, normal)
            faces.append(face)
            uvs.append(face_uv)
            face, face_uv = oriented_face(tuple(total + i for i in quad), quad_uv, points, -normal)
            faces.append(face)
            uvs.append(face_uv)
    emit(part, Geo(points, faces, uvs), name, None, "texture", True)


def ragged_top(a0, a1, profile, rng_local, step=(0.16, 0.44), course=0.13, jitter=0.03):
    points = []
    a = a0
    previous = None
    while a < a1 - 1e-6:
        span = min(rng_local.uniform(*step), a1 - a)
        if a1 - (a + span) < step[0] * 0.5:
            span = a1 - a
        level = profile(a + span * 0.5)
        level = (round(level / course) + rng_local.choice((-1, 0, 0, 0, 1))) * course + rng_local.uniform(-jitter, jitter)
        if previous is not None and abs(level - previous) > 1e-3:
            points.append((a - 0.03, previous))
            points.append((a + 0.03, level))
        else:
            points.append((a, level))
        previous = level
        a += span
    points.append((a1, previous))
    return points


def piecewise(pairs):
    def sample(a):
        if a <= pairs[0][0]:
            return pairs[0][1]
        for (a0, h0), (a1, h1) in zip(pairs[:-1], pairs[1:]):
            if a <= a1:
                t = (a - a0) / max(a1 - a0, 1e-9)
                return h0 + (h1 - h0) * t
        return pairs[-1][1]
    return sample


def ruin_boxes(build, surface, tag, frame, top_points, z_bottom, thickness, tolerance=0.22):
    spans = []
    for (a0, h0), (a1, h1) in zip(top_points[:-1], top_points[1:]):
        if a1 - a0 < 0.08:
            continue
        height = min(h0, h1)
        if spans and abs(spans[-1][2] - height) < tolerance:
            spans[-1] = (spans[-1][0], a1, min(spans[-1][2], height))
        else:
            spans.append((a0, a1, height))
    for a0, a1, height in spans:
        if height <= z_bottom + 0.05:
            continue
        low, high = box_between(frame_point(frame, a0, z_bottom, -thickness), frame_point(frame, a1, height, 0.0))
        build.col(surface, tag, low, high)


def roof_boards(part, gable, side, x0, x1, d0, d1, rng_local, name="timber_planks_weathered", thick=0.022, lift=0.0, holes=()):
    d = d0
    while d < d1 - 0.02:
        w = min(rng_local.uniform(0.15, 0.22), d1 - d)
        spans = [(x0, x1)]
        for hx0, hx1, hd0, hd1 in holes:
            if hd0 < d + w * 0.5 < hd1:
                cut = []
                for s0, s1 in spans:
                    if hx1 <= s0 or hx0 >= s1:
                        cut.append((s0, s1))
                        continue
                    left_end = hx0 - rng_local.uniform(0.0, 0.25)
                    right_start = hx1 + rng_local.uniform(0.0, 0.25)
                    if left_end > s0 + 0.1:
                        cut.append((s0, left_end))
                    if right_start < s1 - 0.1:
                        cut.append((right_start, s1))
                spans = cut
        for s0, s1 in spans:
            start = s0
            while start < s1 - 1e-4:
                end = min(start + rng_local.uniform(0.7, 1.3), s1)
                if s1 - end < 0.3:
                    end = s1
                a = gable.point(side, start, d + w * 0.5, lift - thick * 0.5)
                b = gable.point(side, end, d + w * 0.5, lift - thick * 0.5)
                emit(part, geo_box(end - start - 0.002, w - 0.004, thick), name, place((a + b) * 0.5, V(1.0, 0.0, 0.0), gable.normal(side)), "board")
                start = end
        d += w


def segmented(part, name, a, b, width, height, up, step=1.0, mapping="board", bevel=0.0):
    length = (b - a).length
    count = max(1, int(round(length / step)))
    for index in range(count):
        p = a.lerp(b, index / count)
        q = a.lerp(b, (index + 1) / count)
        geo = geo_cbox((q - p).length, width, height, bevel) if bevel > 0.0 else geo_box((q - p).length, width, height)
        emit(part, geo, name, place((p + q) * 0.5, (q - p).normalized(), up), mapping)


def roof_rafters(part, gable, side, xs, d0, d1, lift, name="timber_beam", width=0.065, depth=0.14):
    for x in xs:
        a = gable.point(side, x, d0, lift - depth * 0.5)
        b = gable.point(side, x, d1, lift - depth * 0.5)
        emit(part, geo_box((b - a).length, width, depth), name, place((a + b) * 0.5, (b - a).normalized(), gable.normal(side)), "box")


def ridge_tiles(part, gable, x0, x1, rng_local, name="terracotta", bed="concrete", radius=0.13, length=0.42):
    profile = []
    for step in range(9):
        angle = math.pi * step / 8
        profile.append((radius * math.cos(angle), radius * math.sin(angle)))
    for step in range(8, -1, -1):
        angle = math.pi * step / 8
        profile.append(((radius - 0.018) * math.cos(angle), (radius - 0.018) * math.sin(angle)))
    x = x0
    while x < x1 - 0.05:
        end = min(x + length, x1)
        base = V(0.0, 0.0, gable.ridge_top - 0.035 + rng_local.uniform(-0.004, 0.006))
        path = [V(x, 0.0, 0.0) + base, V(end + 0.02, 0.0, 0.0) + base]
        emit(part, geo_tube(path, profile, True, V(0.0, 0.0, 1.0)), name, None, "given", True)
        x = end
    segmented(part, bed, V(x0, gable.origin_y, gable.ridge_top - 0.035), V(x1, gable.origin_y, gable.ridge_top - 0.035), 0.2, 0.03, V(0.0, 0.0, 1.0), 0.8, "box")


def gable_coping(part, name, gable, x_center, width, rng_local, height=0.12, overhang=0.05, extra=0.1):
    for side in (-1.0, 1.0):
        d = gable.distance(gable.half)
        while d < gable.run - 0.1:
            step = min(rng_local.uniform(0.45, 0.65), gable.run - d)
            a = gable.point(side, x_center, d, extra + height * 0.5)
            b = gable.point(side, x_center, d + step - 0.01, extra + height * 0.5)
            emit(part, geo_cbox((b - a).length, width + overhang * 2.0, height, 0.012), name, place((a + b) * 0.5, (b - a).normalized(), gable.normal(side)), "box")
            d += step
    apex = V(x_center, 0.0, gable.ridge_top + extra + height * 0.5)
    block(part, name, apex - V(width * 0.5 + overhang, 0.22, height * 0.5), apex + V(width * 0.5 + overhang, 0.22, height * 0.9), 0.015)


def gutter(part, gable, side, x0, x1, rng_local, sag=0.03, name="rusty_metal", radius=0.06, drop=0.05, broken_at=None):
    y = side * (gable.edge - 0.02)
    z = gable.eave_top - drop - radius
    profile = []
    for step in range(9):
        angle = math.pi + math.pi * step / 8
        profile.append((radius * math.cos(angle), radius * math.sin(angle)))
    for step in range(8, -1, -1):
        angle = math.pi + math.pi * step / 8
        profile.append(((radius - 0.005) * math.cos(angle), (radius - 0.005) * math.sin(angle)))
    segments = []
    if broken_at is None:
        segments.append((x0, x1, 0.0))
    else:
        segments.append((x0, broken_at - 0.05, 0.0))
        segments.append((broken_at + 0.05, x1, 0.35))
    for s0, s1, droop in segments:
        path = []
        steps = max(2, int((s1 - s0) / 0.4))
        for index in range(steps + 1):
            t = index / steps
            x = s0 + (s1 - s0) * t
            fall = sag * math.sin(math.pi * (x - x0) / max(x1 - x0, 1e-3)) + droop * t * t
            path.append(V(x, y + side * radius, z - fall))
        emit(part, geo_tube(path, profile, True, V(0.0, 0.0, 1.0)), name, None, "given", True)
        for index in range(0, steps + 1, 2):
            p = path[index]
            block(part, name, V(p.x - 0.015, p.y - radius - 0.012, p.z - radius - 0.008), V(p.x + 0.015, p.y + radius + 0.012, p.z - radius))
    return z


def downpipe(part, x, y_top, y_wall, z_top, z_bottom, rng_local, name="rusty_metal", radius=0.035, broken=0.0, lean=0.0):
    out = 1.0 if y_top > y_wall else -1.0
    y_pipe = y_wall + out * (radius + 0.03)
    bottom = z_bottom + broken
    path = [V(x, y_top, z_top), V(x, y_top, z_top - 0.12), V(x, y_pipe, z_top - 0.45)]
    steps = 6
    for index in range(steps + 1):
        t = index / steps
        z = z_top - 0.6 - (z_top - 0.6 - bottom) * t
        path.append(V(x + lean * t * t, y_pipe, z))
    emit(part, geo_tube(path, circle(radius, 10), True, V(1.0, 0.0, 0.0)), name, None, "given", True)
    z = z_top - 0.8
    while z > bottom + 0.3:
        block(part, name, V(x - 0.045, min(y_wall, y_pipe + out * radius), z), V(x + 0.045, max(y_wall, y_pipe + out * radius), z + 0.03))
        z -= rng_local.uniform(1.3, 1.7)
    if broken <= 0.0:
        shoe = [V(x, y_pipe, bottom + 0.14), V(x, y_pipe, bottom + 0.05), V(x, y_pipe + out * 0.14, bottom + 0.02)]
        emit(part, geo_tube(shoe, circle(radius * 1.05, 10), True, V(1.0, 0.0, 0.0)), name, None, "given", True)


def geo_frustum(bx, by, tx, ty, height):
    points = [V(-bx, -by, 0.0), V(bx, -by, 0.0), V(bx, by, 0.0), V(-bx, by, 0.0), V(-tx, -ty, height), V(tx, -ty, height), V(tx, ty, height), V(-tx, ty, height)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (0, 4, 7, 3), (1, 2, 6, 5)]
    return Geo(points, [orient(face, points, newell([points[i] for i in face])) for face in faces])


def chimney(part, name, cx, cy, sx, sy, z0, z1, rng_local, pots=2, pot_name="terracotta", cap_name=None, flaunch="concrete", broken_pot=True):
    z = z0
    course = 0
    long_x = sx >= sy
    while z < z1 - 0.12:
        h = rng_local.uniform(0.22, 0.3)
        if z + h > z1 - 0.12:
            h = z1 - z
        span = sx if long_x else sy
        split = (rng_local.uniform(-0.25, -0.1) if course % 2 == 0 else rng_local.uniform(0.1, 0.25)) * span
        for low, high in ((-span * 0.5, split), (split, span * 0.5)):
            if long_x:
                block(part, name, V(cx + low + 0.005, cy - sy * 0.5 - rng_local.uniform(0.0, 0.01), z + 0.006), V(cx + high - 0.005, cy + sy * 0.5 + rng_local.uniform(0.0, 0.01), z + h - 0.006), 0.012)
            else:
                block(part, name, V(cx - sx * 0.5 - rng_local.uniform(0.0, 0.01), cy + low + 0.005, z + 0.006), V(cx + sx * 0.5 + rng_local.uniform(0.0, 0.01), cy + high - 0.005, z + h - 0.006), 0.012)
        z += h
        course += 1
    cap = cap_name or name
    block(part, cap, V(cx - sx * 0.5 - 0.06, cy - sy * 0.5 - 0.06, z1), V(cx + sx * 0.5 + 0.06, cy + sy * 0.5 + 0.06, z1 + 0.12), 0.015)
    top = z1 + 0.12
    emit(part, geo_frustum(sx * 0.5 + 0.02, sy * 0.5 + 0.02, sx * 0.3, sy * 0.3, 0.1), flaunch, Matrix.Translation(V(cx, cy, top)), "box")
    positions = []
    for index in range(pots):
        f = (index + 0.5) / pots - 0.5
        positions.append(V(cx + (sx * f * 0.9 if long_x else 0.0), cy + (0.0 if long_x else sy * f * 0.9), top + 0.04))
    for index, position in enumerate(positions):
        height = rng_local.uniform(0.45, 0.65)
        if broken_pot and index == pots - 1:
            height *= 0.45
        profile = [(0.11, 0.0), (0.12, 0.03), (0.1, height * 0.5), (0.085, height - 0.05), (0.1, height - 0.03), (0.1, height), (0.08, height), (0.075, height * 0.4), (0.075, 0.02)]
        emit(part, geo_lathe(profile, 14, rng_local.uniform(0.0, tau), True, False), pot_name, Matrix.Translation(position), "given", True)
    return top


def flagstones(part, name, x0, x1, y0, y1, z, rng_local, size_range=(0.4, 0.75), gap=0.01, thick=0.06, bevel=0.012, uneven=0.004, bed="dirt_debris", skip=None):
    block(part, bed, V(x0, y0, z - thick - 0.02), V(x1, y1, z - 0.018))
    y = y0
    while y < y1 - 0.05:
        h = min(rng_local.uniform(*size_range), y1 - y)
        if y1 - (y + h) < 0.2:
            h = y1 - y
        x = x0
        while x < x1 - 0.05:
            w = min(rng_local.uniform(*size_range) * 1.2, x1 - x)
            if x1 - (x + w) < 0.2:
                w = x1 - x
            if skip is None or not skip((x + w * 0.5), (y + h * 0.5)):
                top = z + rng_local.uniform(-uneven, uneven * 0.3)
                block(part, name, V(x + gap * 0.5, y + gap * 0.5, top - thick), V(x + w - gap * 0.5, y + h - gap * 0.5, top), bevel * rng_local.uniform(0.6, 1.4))
            x += w
        y += h


def floor_boards(part, name, x0, x1, y0, y1, z_top, along, rng_local, thick=0.025, gap=0.004, missing=None, width_range=(0.14, 0.2), warp=0.04, joints=None, holes=(), ragged=0.0):
    across0, across1 = (y0, y1) if along == "x" else (x0, x1)
    length0, length1 = (x0, x1) if along == "x" else (y0, y1)
    c = across0
    while c < across1 - 0.02:
        w = min(rng_local.uniform(*width_range), across1 - c)
        if across1 - (c + w) < 0.06:
            w = across1 - c
        pieces = [(length0, length1)]
        if joints and length1 - length0 > 2.2:
            cut = rng_local.choice(joints)
            if length0 + 0.5 < cut < length1 - 0.5:
                pieces = [(length0, cut - 0.002), (cut + 0.002, length1)]
        for hx0, hx1, hy0, hy1 in holes:
            h_across = (hy0, hy1) if along == "x" else (hx0, hx1)
            h_length = (hx0, hx1) if along == "x" else (hy0, hy1)
            if min(c + w, h_across[1]) - max(c, h_across[0]) < w * 0.35:
                continue
            clipped = []
            for l0, l1 in pieces:
                if h_length[1] <= l0 or h_length[0] >= l1:
                    clipped.append((l0, l1))
                    continue
                left_end = h_length[0] - rng_local.uniform(0.0, ragged)
                right_start = h_length[1] + rng_local.uniform(0.0, ragged)
                if left_end > l0 + 0.05:
                    clipped.append((l0, left_end))
                if right_start < l1 - 0.05:
                    clipped.append((right_start, l1))
            pieces = clipped
        for l0, l1 in pieces:
            middle = (l0 + l1) * 0.5
            if missing is not None and missing(middle if along == "x" else c + w * 0.5, c + w * 0.5 if along == "x" else middle):
                continue
            raised = rng_local.random() < warp
            tilt = rng_local.uniform(-0.03, 0.03) if raised else 0.0
            lift = rng_local.uniform(0.004, 0.015) if raised else rng_local.uniform(-0.001, 0.001)
            center = V(middle, c + w * 0.5, z_top - thick * 0.5 + lift) if along == "x" else V(c + w * 0.5, middle, z_top - thick * 0.5 + lift)
            forward = V(1.0, 0.0, 0.0) if along == "x" else V(0.0, 1.0, 0.0)
            geo = geo_box(l1 - l0, w - gap, thick)
            matrix = place(center, forward, V(0.0, 0.0, 1.0)) @ Matrix.Rotation(tilt, 4, 'X')
            emit(part, geo, name, matrix, "board")
        c += w


def joists(part, name, x0, x1, y0, y1, z_top, along, spacing=0.45, width=0.08, depth=0.16, clip=None):
    if along == "y":
        x = x0 + spacing * 0.5
        while x < x1:
            for lo, hi in (clip(x) if clip is not None else [(y0, y1)]):
                block(part, name, V(x - width * 0.5, lo, z_top - depth), V(x + width * 0.5, hi, z_top))
            x += spacing
    else:
        y = y0 + spacing * 0.5
        while y < y1:
            for lo, hi in (clip(y) if clip is not None else [(x0, x1)]):
                block(part, name, V(lo, y - width * 0.5, z_top - depth), V(hi, y + width * 0.5, z_top))
            y += spacing


def stair(part, name, start, forward, width, rise, run, steps, rng_local, risers=True, stringer=None, tread_thick=0.035, broken=()):
    side = V(-forward.y, forward.x, 0.0)
    going = run / steps
    step_rise = rise / steps
    for index in range(steps):
        top = start.z + step_rise * (index + 1)
        front = start + forward * (going * index)
        center = front + forward * (going * 0.5 + 0.015) + V(0.0, 0.0, top - start.z - tread_thick * 0.5)
        if index not in broken:
            emit(part, geo_cbox(width, going + 0.03, tread_thick, 0.006), name, place(center, side, V(0.0, 0.0, 1.0)), "board")
        if risers:
            riser_center = front + V(0.0, 0.0, top - start.z - step_rise * 0.5 - tread_thick * 0.5) + forward * 0.012
            emit(part, geo_box(width - 0.02, 0.02, step_rise - tread_thick), name, place(riser_center, side, V(0.0, 0.0, 1.0)), "board")
    rail = stringer or name
    for sign in (-1.0, 1.0):
        a = start + side * (sign * (width * 0.5 + 0.02)) + V(0.0, 0.0, 0.05)
        b = a + forward * run + V(0.0, 0.0, rise)
        up = V(0.0, 0.0, 1.0)
        emit(part, geo_box((b - a).length + 0.1, 0.04, 0.22), rail, place((a + b) * 0.5, (b - a).normalized(), up - (b - a).normalized() * up.dot((b - a).normalized())), "board")


def grass_tuft(part, position, rng_local, height=(0.12, 0.35), blades=(6, 14), spread=0.07, name="foliage", lean=0.35):
    count = rng_local.randint(*blades)
    for blade in range(count):
        yaw = rng_local.uniform(0.0, tau)
        h = rng_local.uniform(*height)
        w = rng_local.uniform(0.008, 0.016)
        base = position + V(math.cos(yaw) * rng_local.uniform(0.0, spread), math.sin(yaw) * rng_local.uniform(0.0, spread), 0.0)
        out = V(math.cos(yaw), math.sin(yaw), 0.0)
        side = V(-out.y, out.x, 0.0)
        bend = rng_local.uniform(0.1, lean)
        mid = base + V(0.0, 0.0, h * 0.55) + out * (h * bend * 0.4)
        tip = base + V(0.0, 0.0, h * (1.0 - bend * 0.5)) + out * (h * bend)
        points = [base - side * w, base + side * w, mid + side * w * 0.7, mid - side * w * 0.7, tip]
        faces = [(0, 1, 2, 3), (3, 2, 4)]
        uvs = [[(0.0, 0.0), (w * 2, 0.0), (w * 1.7, h * 0.55), (w * 0.3, h * 0.55)], [(w * 0.3, h * 0.55), (w * 1.7, h * 0.55), (w, h)]]
        emit(part, Geo(points, faces, uvs), name, None, "given", True)


def leaf_quad(part, center, normal, up_hint, size_value, rng_local, name="foliage"):
    n = normal.normalized()
    up = up_hint - n * up_hint.dot(n)
    if up.length < 1e-4:
        up = n.orthogonal()
    up.normalize()
    side = up.cross(n).normalized()
    twist = rng_local.uniform(-0.6, 0.6)
    up2 = (up * math.cos(twist) + side * math.sin(twist)).normalized()
    side2 = up2.cross(n).normalized()
    h = size_value
    w = size_value * rng_local.uniform(0.55, 0.8)
    cup = n * (size_value * 0.15)
    points = [center - up2 * (h * 0.2), center + side2 * (w * 0.5) + up2 * (h * 0.3) + cup, center + up2 * (h * 0.8), center - side2 * (w * 0.5) + up2 * (h * 0.3) + cup]
    uvs = [[(w * 0.5, 0.0), (w, h * 0.5), (w * 0.5, h), (0.0, h * 0.5)]]
    emit(part, Geo(points, [(0, 1, 2, 3)], uvs), name, None, "given", True)


def ivy(part, start, wall_normal, rng_local, height, spread=0.6, branches=5, density=26.0, stem="timber_beam", leaf="foliage"):
    n = wall_normal.normalized()
    tangent = V(0.0, 0.0, 1.0).cross(n).normalized()
    for branch in range(branches):
        path = [start + tangent * rng_local.uniform(-0.1, 0.1)]
        direction_x = rng_local.uniform(-spread, spread)
        reach = height * rng_local.uniform(0.5, 1.0)
        steps = max(4, int(reach / 0.15))
        for index in range(1, steps + 1):
            t = index / steps
            wobble = math.sin(t * 7.0 + branch) * 0.05
            path.append(start + V(0.0, 0.0, reach * t) + tangent * (direction_x * t + wobble) + n * 0.012)
        emit(part, geo_tube(path, circle(0.008 * rng_local.uniform(0.7, 1.3), 5), True, n), stem, None, "given", True)
        leaves = int(reach * density)
        for index in range(leaves):
            t = rng_local.random()
            position = path[min(int(t * steps), steps - 1)].lerp(path[min(int(t * steps) + 1, steps)], (t * steps) % 1.0)
            position = position + tangent * rng_local.uniform(-0.07, 0.07) + V(0.0, 0.0, rng_local.uniform(-0.05, 0.05)) + n * rng_local.uniform(0.01, 0.06)
            leaf_quad(part, position, (n + V(0.0, 0.0, rng_local.uniform(0.2, 0.9)) + tangent * rng_local.uniform(-0.5, 0.5)), V(0.0, 0.0, 1.0), rng_local.uniform(0.045, 0.09), rng_local, leaf)


def nettle(part, position, rng_local, height=(0.4, 0.9), name="foliage"):
    stems = rng_local.randint(2, 5)
    for stem in range(stems):
        h = rng_local.uniform(*height)
        base = position + V(rng_local.uniform(-0.08, 0.08), rng_local.uniform(-0.08, 0.08), 0.0)
        lean = V(rng_local.uniform(-0.15, 0.15), rng_local.uniform(-0.15, 0.15), 0.0)
        tip = base + V(0.0, 0.0, h) + lean
        rod(part, name, base, tip, 0.005, 5)
        pairs = int(h / 0.1)
        for index in range(pairs):
            t = (index + 1) / (pairs + 1)
            p = base.lerp(tip, t)
            for sign in (-1.0, 1.0):
                yaw = index * 1.57 + (0.0 if sign > 0 else math.pi)
                out = V(math.cos(yaw), math.sin(yaw), 0.0)
                size_value = 0.05 + 0.07 * (1.0 - t)
                leaf_quad(part, p + out * size_value * 0.35, out + V(0.0, 0.0, 1.2), out, size_value, rng_local, name)


def fern(part, position, rng_local, fronds=(5, 9), length=(0.35, 0.7), name="foliage"):
    for frond in range(rng_local.randint(*fronds)):
        yaw = rng_local.uniform(0.0, tau)
        out = V(math.cos(yaw), math.sin(yaw), 0.0)
        side = V(-out.y, out.x, 0.0)
        span = rng_local.uniform(*length)
        points = []
        for index in range(6):
            t = index / 5
            points.append(position + out * (span * t) + V(0.0, 0.0, span * (0.8 * t - 0.75 * t * t)))
        emit(part, geo_tube(points, circle(0.004, 4), True), name, None, "given", True)
        for index in range(1, 10):
            t = index / 10
            p = position + out * (span * t) + V(0.0, 0.0, span * (0.8 * t - 0.75 * t * t))
            for sign in (-1.0, 1.0):
                leaf_quad(part, p + side * (sign * 0.03 * (1.0 - t)), V(0.0, 0.0, 1.0) + side * sign * 0.3, side * sign + out * 0.5, 0.07 * (1.0 - t * 0.6), rng_local, name)


def lump(part, name, center, radii, rng_local, rough=0.25, subdivisions=2, floor=None, yaw=None, smooth=True):
    geo = geo_lump(radii[0], radii[1], radii[2], rng_local, subdivisions, rough, None if floor is None else floor - center.z)
    emit(part, geo, name, turned(center, rng_local.uniform(0.0, tau) if yaw is None else yaw), "box", smooth)


def rubble_pile(part, center, radius, height, rng_local, count=18, names=("granite_ashlar", "granite_ashlar", "granite_rubble"), dust="dirt_debris", sizes=(0.08, 0.26)):
    lump(part, dust, center + V(0.0, 0.0, 0.0), (radius, radius * rng_local.uniform(0.7, 1.0), height * 0.7), rng_local, 0.2, 2, center.z)
    for index in range(count):
        angle = rng_local.uniform(0.0, tau)
        r = radius * math.sqrt(rng_local.random()) * 0.95
        s = rng_local.uniform(*sizes)
        local_height = height * 0.7 * max(0.0, 1.0 - (r / radius) ** 2) ** 0.5
        position = center + V(math.cos(angle) * r, math.sin(angle) * r, local_height * rng_local.uniform(0.5, 1.0))
        lump(part, rng_local.choice(names), position, (s, s * rng_local.uniform(0.6, 1.0), s * rng_local.uniform(0.4, 0.7)), rng_local, 0.18, 1, None, None, False)


def scatter_chips(part, name, x0, x1, y0, y1, z, count, rng_local, size_range=(0.03, 0.12), thick=(0.006, 0.02), tilt=0.25):
    for index in range(count):
        s = rng_local.uniform(*size_range)
        position = V(rng_local.uniform(x0, x1), rng_local.uniform(y0, y1), z)
        polygon = blob(0.0, 0.0, s, s * rng_local.uniform(0.5, 1.0), rng_local, 7, 0.35)
        t = rng_local.uniform(*thick)
        matrix = Matrix.Translation(position + V(0.0, 0.0, t * 0.5)) @ Matrix.Rotation(rng_local.uniform(0.0, tau), 4, 'Z') @ Matrix.Rotation(rng_local.uniform(-tilt, tilt), 4, 'X') @ Matrix.Rotation(math.pi * 0.5, 4, 'X')
        prism(part, name, matrix, polygon, -t * 0.5, t * 0.5)


def plank_debris(part, name, x0, x1, y0, y1, z, count, rng_local, length=(0.3, 1.4), width=(0.08, 0.2), thick=0.025):
    for index in range(count):
        l = rng_local.uniform(*length)
        w = rng_local.uniform(*width)
        center = V(rng_local.uniform(x0, x1), rng_local.uniform(y0, y1), z + thick * 0.5)
        yaw = rng_local.uniform(0.0, tau)
        tilt = rng_local.uniform(-0.12, 0.12)
        emit(part, geo_box(l, w, thick), name, turned(center + V(0.0, 0.0, abs(tilt) * l * 0.3), yaw, tilt), "board")


glyphs = {
    "A": "01110100011000111111100011000110001", "B": "11110100011000111110100011000111110", "C": "01110100011000010000100001000101110",
    "D": "11100100101000110001100011001011100", "E": "11111100001000011110100001000011111", "F": "11111100001000011110100001000010000",
    "G": "01110100011000010111100011000101111", "H": "10001100011000111111100011000110001", "I": "01110001000010000100001000010001110",
    "J": "00111000100001000010000101001001100", "K": "10001100101010011000101001001010001", "L": "10000100001000010000100001000011111",
    "M": "10001110111010110101100011000110001", "N": "10001100011100110101100111000110001", "O": "01110100011000110001100011000101110",
    "P": "11110100011000111110100001000010000", "Q": "01110100011000110001101011001001101", "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110", "T": "11111001000010000100001000010000100", "U": "10001100011000110001100011000101110",
    "V": "10001100011000110001100010101000100", "W": "10001100011000110101101011010101010", "X": "10001100010101000100010101000110001",
    "Y": "10001100011000101010001000010000100", "Z": "11111000010001000100010001000011111", "0": "01110100011001110101110011000101110",
    "1": "00100011000010000100001000010001110", "2": "01110100010000100010001000100011111", "3": "11111000100010000010000011000101110",
    "4": "00010001100101010010111110001000010", "5": "11111100001111000001000011000101110", "6": "00110010001000011110100011000101110",
    "7": "11111000010001000100010000100001000", "8": "01110100011000101110100011000101110", "9": "01110100011000101111000010001001100",
    "-": "00000000000000011111000000000000000", ".": "00000000000000000000000000110001100", ":": "00000011000110000000011000110000000",
    "/": "00000000010001000100010001000000000", " ": "00000000000000000000000000000000000", "_": "00000000000000000000000000000011111",
    "+": "00000001000010011111001000010000000", ">": "01000001000001000001000100010001000", "(": "00010001000100001000010000010000010",
    ")": "01000001000001000010000100010001000", "%": "11001110010001000100010001001110011", ",": "00000000000000000000001100010001000",
}


def text(image, x, y, string, color, scale=2):
    height, width = image.shape[:2]
    cursor = x
    for character in string.upper():
        pattern = glyphs.get(character, glyphs[" "])
        for row in range(7):
            for column in range(5):
                if pattern[row * 5 + column] == "1":
                    y0 = y + (6 - row) * scale
                    x0 = cursor + column * scale
                    if 0 <= x0 and x0 + scale <= width and 0 <= y0 and y0 + scale <= height:
                        image[y0:y0 + scale, x0:x0 + scale, :3] = color
        cursor += 6 * scale
    return cursor


def text_width(string, scale=2):
    return len(string) * 6 * scale


def fill_rect(image, x0, y0, x1, y1, color, alpha=1.0):
    height, width = image.shape[:2]
    x0 = max(0, int(round(x0)))
    x1 = min(width, int(round(x1)))
    y0 = max(0, int(round(y0)))
    y1 = min(height, int(round(y1)))
    if x1 <= x0 or y1 <= y0:
        return
    region = image[y0:y1, x0:x1, :3]
    image[y0:y1, x0:x1, :3] = region * (1.0 - alpha) + np.asarray(color) * alpha


def outline_rect(image, x0, y0, x1, y1, color, thickness=2):
    fill_rect(image, x0, y0, x1, y0 + thickness, color)
    fill_rect(image, x0, y1 - thickness, x1, y1, color)
    fill_rect(image, x0, y0, x0 + thickness, y1, color)
    fill_rect(image, x1 - thickness, y0, x1, y1, color)


def line(image, x0, y0, x1, y1, color, thickness=2):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for index in range(steps + 1):
        t = index / max(steps, 1)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        fill_rect(image, x - thickness * 0.5, y - thickness * 0.5, x + thickness * 0.5, y + thickness * 0.5, color)


def read_image(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    data = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(height, width, 4)[:, :, :3].astype(np.float64)


def downsample(image, width, height):
    h, w = image.shape[:2]
    ys = (np.arange(height) + 0.5) * h / height
    xs = (np.arange(width) + 0.5) * w / width
    y0 = np.clip(np.floor(ys - 0.5).astype(np.int64), 0, h - 1)
    x0 = np.clip(np.floor(xs - 0.5).astype(np.int64), 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    fy = np.clip(ys - 0.5 - y0, 0.0, 1.0)[:, None, None]
    fx = np.clip(xs - 0.5 - x0, 0.0, 1.0)[None, :, None]
    factor = max(1, int(min(h / height, w / width)))
    if factor > 1:
        trimmed = image[:h - h % factor, :w - w % factor]
        image = trimmed.reshape(trimmed.shape[0] // factor, factor, trimmed.shape[1] // factor, factor, 3).mean(axis=(1, 3))
        return downsample(image, width, height)
    a = image[y0][:, x0]
    b = image[y0][:, x1]
    c = image[y1][:, x0]
    d = image[y1][:, x1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def import_building(folder):
    path = os.path.join(models_root, folder, folder + ".gltf")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objects = [obj for obj in bpy.data.objects if obj not in before]
    for obj in objects:
        if obj.type == 'MESH':
            obj.data.update()
    return objects


def is_marker(name):
    return name.split("_")[0] in ("col", "ramp", "loot", "light")


def world_bounds(objects):
    low = V(1e9, 1e9, 1e9)
    high = V(-1e9, -1e9, -1e9)
    for obj in objects:
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            low = V(min(low.x, p.x), min(low.y, p.y), min(low.z, p.z))
            high = V(max(high.x, p.x), max(high.y, p.y), max(high.z, p.z))
    return low, high


def render_settings(samples, resolution=(1600, 900), exposure=0.0):
    import turntable
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 3
    scene.cycles.transparent_max_bounces = 4
    turntable.accelerate(scene)
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = exposure
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False


def studio(size_value, strength=0.55):
    import turntable
    scene = bpy.context.scene
    floor, created = turntable.studio(scene, hdri_path, max(size_value / 0.7, 1.0))
    created.remove(floor)
    mesh = floor.data
    bpy.data.objects.remove(floor)
    bpy.data.meshes.remove(mesh)
    scene.world.node_tree.nodes["Background"].inputs['Strength'].default_value = strength
    return created


def daylight(strength=1.0, sun=2.5, direction=(0.45, -0.6, -0.66), angle=18.0):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("daylight")
    world.use_nodes = True
    tree = world.node_tree
    background = tree.nodes["Background"]
    environment = tree.nodes.new('ShaderNodeTexEnvironment')
    environment.image = bpy.data.images.load(hdri_path, check_existing=True)
    tree.links.new(environment.outputs['Color'], background.inputs['Color'])
    background.inputs['Strength'].default_value = strength
    scene.world = world
    data = bpy.data.lights.new("preview_sun", 'SUN')
    data.energy = sun
    data.angle = math.radians(angle)
    data.color = (1.0, 0.96, 0.9)
    obj = bpy.data.objects.new("preview_sun", data)
    scene.collection.objects.link(obj)
    obj.rotation_euler = Vector(direction).normalized().to_track_quat('-Z', 'Y').to_euler()
    return obj


def ground(z, extent, name="dirt_debris", scale=3.0):
    tile = tile_of(name) * scale
    mesh = bpy.data.meshes.new("preview_ground")
    mesh.from_pydata([(-extent, -extent, z), (extent, -extent, z), (extent, extent, z), (-extent, extent, z)], [], [(0, 1, 2, 3)])
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", [-extent / tile, -extent / tile, extent / tile, -extent / tile, extent / tile, extent / tile, -extent / tile, extent / tile])
    mesh.materials.append(material(name))
    obj = bpy.data.objects.new("preview_ground", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def camera(position, target, lens=35.0, ortho=None, clip_start=0.05, clip_end=800.0, shift=(0.0, 0.0)):
    data = bpy.data.cameras.new("preview_camera")
    data.lens = lens
    data.clip_start = clip_start
    data.clip_end = clip_end
    data.shift_x = shift[0]
    data.shift_y = shift[1]
    if ortho is not None:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    obj = bpy.data.objects.new("preview_camera", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = position
    direction = target - position
    if abs(direction.x) + abs(direction.y) < 1e-6:
        obj.rotation_euler = (0.0, 0.0, 0.0)
    else:
        obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = obj
    return obj


def fit_camera(cam, points, margin=0.06, step=0.35):
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    for iteration in range(200):
        bpy.context.view_layer.update()
        coords = [world_to_camera_view(scene, cam, p) for p in points]
        if all(margin < c.x < 1.0 - margin and margin < c.y < 1.0 - margin and c.z > 0.0 for c in coords):
            break
        cam.location -= cam.matrix_world.to_quaternion() @ V(0.0, 0.0, -step)
    bpy.context.view_layer.update()


def area_light(position, target, energy, size_value, color=(1.0, 0.95, 0.88)):
    data = bpy.data.lights.new("preview_fill", 'AREA')
    data.energy = energy
    data.size = size_value
    data.color = color
    obj = bpy.data.objects.new("preview_fill", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (target - position).to_track_quat('-Z', 'Y').to_euler()
    return obj


def point_light(position, energy, radius=0.05, color=(1.0, 0.7, 0.4)):
    data = bpy.data.lights.new("preview_point", 'POINT')
    data.energy = energy
    data.shadow_soft_size = radius
    data.color = color
    obj = bpy.data.objects.new("preview_point", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = position
    return obj


def shoot(path):
    scene = bpy.context.scene
    scene.render.filepath = path
    started = __import__("time").time()
    bpy.ops.render.render(write_still=True)
    print("RENDERED", os.path.basename(path), round(__import__("time").time() - started, 1), "s", flush=True)


surface_colors = {"rock": (0.95, 0.45, 0.2), "wood": (0.95, 0.8, 0.25), "metal": (0.3, 0.85, 0.95), "concrete": (0.6, 0.65, 0.95), "glass": (0.7, 0.95, 1.0), "fabric": (1.0, 0.5, 0.8), "dirt": (0.7, 0.5, 0.3), "gravel": (0.75, 0.75, 0.7), "grass": (0.4, 0.9, 0.3), "sand": (0.95, 0.85, 0.55)}


def plan_overlay(image, boxes, center, scale, z_low, z_high):
    height, width = image.shape[:2]

    def to_pixel(x, y):
        return (x - center.x) / scale * width + width * 0.5, (y - center.y) / scale * height + height * 0.5

    drawn = {"col": 0, "ramp": 0, "loot": 0, "light": 0}
    ordered = sorted(boxes, key=lambda item: (item[0].startswith("ramp"), item[2].z))
    for name, lo, hi in ordered:
        if hi.z < z_low or lo.z > z_high:
            continue
        kind = name.split("_")[0]
        x0, y0 = to_pixel(lo.x, lo.y)
        x1, y1 = to_pixel(hi.x, hi.y)
        if kind == "col":
            color = surface_colors.get(name.split("_")[1], (1.0, 1.0, 1.0))
            fill_rect(image, x0, y0, x1, y1, color, 0.22)
            outline_rect(image, x0, y0, x1, y1, color, 2)
        elif kind == "ramp":
            color = (1.0, 0.3, 1.0)
            fill_rect(image, x0, y0, x1, y1, color, 0.3)
            outline_rect(image, x0, y0, x1, y1, color, 3)
            direction = name.split("_")[1]
            cx = (x0 + x1) * 0.5
            cy = (y0 + y1) * 0.5
            dx = {"px": 1, "nx": -1}.get(direction, 0)
            dy = {"py": 1, "ny": -1}.get(direction, 0)
            reach = 0.4 * (abs(x1 - x0) if dx else abs(y1 - y0))
            tip_x = cx + dx * reach
            tip_y = cy + dy * reach
            line(image, cx - dx * reach, cy - dy * reach, tip_x, tip_y, (1.0, 1.0, 1.0), 4)
            line(image, tip_x, tip_y, tip_x - dx * 14 - dy * 10, tip_y - dy * 14 - dx * 10, (1.0, 1.0, 1.0), 4)
            line(image, tip_x, tip_y, tip_x - dx * 14 + dy * 10, tip_y - dy * 14 + dx * 10, (1.0, 1.0, 1.0), 4)
        elif kind == "loot":
            cx = (x0 + x1) * 0.5
            cy = (y0 + y1) * 0.5
            fill_rect(image, cx - 9, cy - 9, cx + 9, cy + 9, (1.0, 0.92, 0.1), 1.0)
            outline_rect(image, cx - 10, cy - 10, cx + 10, cy + 10, (0.0, 0.0, 0.0), 2)
            text(image, int(cx + 12), int(cy - 6), name.split("_")[1][:3], (1.0, 0.92, 0.1), 2)
        elif kind == "light":
            cx = (x0 + x1) * 0.5
            cy = (y0 + y1) * 0.5
            color = {"warm": (1.0, 0.65, 0.2), "cold": (0.6, 0.8, 1.0), "fire": (1.0, 0.3, 0.1)}.get(name.split("_")[1], (1.0, 1.0, 1.0))
            for radius in range(9, 0, -1):
                fill_rect(image, cx - radius, cy - radius * 0.35, cx + radius, cy + radius * 0.35, color, 1.0)
                fill_rect(image, cx - radius * 0.35, cy - radius, cx + radius * 0.35, cy + radius, color, 1.0)
        drawn[kind] += 1
    return drawn


def legend(image, x, y):
    entries = [("ROCK", surface_colors["rock"]), ("WOOD", surface_colors["wood"]), ("METAL", surface_colors["metal"]), ("CONCRETE", surface_colors["concrete"]), ("FABRIC", surface_colors["fabric"]), ("DIRT", surface_colors["dirt"]), ("GRASS", surface_colors["grass"]), ("RAMP", (1.0, 0.3, 1.0)), ("LOOT", (1.0, 0.92, 0.1)), ("LIGHT", (1.0, 0.65, 0.2))]
    for label, color in entries:
        fill_rect(image, x, y, x + 22, y + 16, color, 0.9)
        x = text(image, x + 28, y + 1, label, (1.0, 1.0, 1.0), 2) + 20


def plan_sheet(name, levels, boxes, low, high, samples, out_path):
    scene = bpy.context.scene
    center = (low + high) * 0.5
    scale = max(high.x - low.x, high.y - low.y) * 1.08
    panel = 900
    render_settings(samples, (panel, panel), 0.4)
    panels = []
    for label, cut, z_low, z_high in levels:
        cam = camera(V(center.x, center.y, cut), V(center.x, center.y, cut - 10.0), 35.0, scale, 0.001, 200.0)
        temporary = os.path.join(preview_root, "_plan_" + name + ".png")
        shoot(temporary)
        bpy.data.objects.remove(cam)
        image = read_image(temporary)
        os.remove(temporary)
        image = image * 0.85
        drawn = plan_overlay(image, boxes, center, scale, z_low, z_high)
        band = np.zeros((40, panel, 3))
        text(band, 10, 12, label + "  Z %.1f TO %.1f M" % (z_low, z_high), (1.0, 1.0, 1.0), 2)
        panels.append(np.concatenate([image, band], 0))
        print("PLAN", name, label, drawn, flush=True)
    sheet = np.concatenate([np.concatenate([p, np.zeros((p.shape[0], 8, 3))], 1) for p in panels], 1)
    footer = np.zeros((44, sheet.shape[1], 3))
    legend(footer, 12, 14)
    text(footer, sheet.shape[1] - text_width("ENTRANCE -Y AT BOTTOM", 2) - 12, 15, "ENTRANCE -Y AT BOTTOM", (0.8, 0.8, 0.8), 2)
    write_png(out_path, np.clip(np.concatenate([footer, sheet], 0), 0.0, 1.0))


def contact_sheet(rows, out_path, thumb=(480, 270)):
    label_height = 26
    columns = max(len(entries) for title, entries in rows)
    sheet = np.full((len(rows) * (thumb[1] + label_height + 10) + 10, columns * (thumb[0] + 10) + 10, 3), 0.06)
    for row_index, (title, entries) in enumerate(rows):
        top = sheet.shape[0] - (row_index + 1) * (thumb[1] + label_height + 10)
        for column, (label, path) in enumerate(entries):
            if not os.path.exists(path):
                continue
            image = np.clip(read_image(path), 0.0, 1.0)
            h, w = image.shape[:2]
            fit = min(thumb[0] / w, thumb[1] / h)
            small = downsample(image, max(1, int(w * fit)), max(1, int(h * fit)))
            x = 10 + column * (thumb[0] + 10) + (thumb[0] - small.shape[1]) // 2
            y = top + (thumb[1] - small.shape[0]) // 2
            sheet[y:y + small.shape[0], x:x + small.shape[1]] = small
            text(sheet, 10 + column * (thumb[0] + 10), top + thumb[1] + 6, (title + " " + label).upper(), (0.95, 0.95, 0.95), 2)
    write_png(out_path, sheet)


def hero_text(path, lines, paper=(0.74, 0.68, 0.54), ink=(0.05, 0.045, 0.04), seed=5, font_file="timesbd.ttf", weather=0.6, border=0.0, stripe=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'Standard'
    scene.render.image_settings.file_format = 'PNG'
    world = bpy.data.worlds.new("flat")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    scene.world = world

    def emissive(name, color):
        result = bpy.data.materials.new(name)
        result.use_nodes = True
        tree = result.node_tree
        output = next(node for node in tree.nodes if node.type == 'OUTPUT_MATERIAL')
        emission = tree.nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (color[0], color[1], color[2], 1.0)
        tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        return result

    white = emissive("paper", (1.0, 1.0, 1.0))
    black = emissive("ink", (0.0, 0.0, 0.0))
    mesh = bpy.data.meshes.new("paper")
    mesh.from_pydata([(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(white)
    scene.collection.objects.link(bpy.data.objects.new("paper", mesh))
    font = None
    font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", font_file)
    if os.path.exists(font_path):
        font = bpy.data.fonts.load(font_path)
    for body, height, y in lines:
        curve = bpy.data.curves.new("line", 'FONT')
        curve.body = body
        curve.align_x = 'CENTER'
        curve.align_y = 'CENTER'
        curve.size = height
        if font is not None:
            curve.font = font
        curve.materials.append(black)
        obj = bpy.data.objects.new("line", curve)
        obj.location = (0.0, y, 0.01)
        scene.collection.objects.link(obj)
    if border > 0.0:
        for x0, x1, y0, y1 in ((-0.5 + border, 0.5 - border, 0.5 - border - 0.012, 0.5 - border), (-0.5 + border, 0.5 - border, -0.5 + border, -0.5 + border + 0.012), (-0.5 + border, -0.5 + border + 0.012, -0.5 + border, 0.5 - border), (0.5 - border - 0.012, 0.5 - border, -0.5 + border, 0.5 - border)):
            rule = bpy.data.meshes.new("rule")
            rule.from_pydata([(x0, y0, 0.01), (x1, y0, 0.01), (x1, y1, 0.01), (x0, y1, 0.01)], [], [(0, 1, 2, 3)])
            rule.materials.append(black)
            scene.collection.objects.link(bpy.data.objects.new("rule", rule))
    data = bpy.data.cameras.new("camera")
    data.type = 'ORTHO'
    data.ortho_scale = 1.0
    cam = bpy.data.objects.new("camera", data)
    cam.location = (0.0, 0.0, 2.0)
    scene.collection.objects.link(cam)
    scene.camera = cam
    temporary = path + ".tmp.png"
    scene.render.filepath = temporary
    bpy.ops.render.render(write_still=True)
    mask = np.clip(read_image(temporary)[:, :, 0], 0.0, 1.0)
    os.remove(temporary)
    if mask.shape[0] != size:
        mask = downsample(np.stack([mask] * 3, -1), size, size)[:, :, 0]
    inked = 1.0 - mask
    inked = inked * (0.75 + 0.25 * unit(field(seed, 30.0, 400.0, 1.4)))
    sheet = flat(paper) * (0.88 + 0.16 * unit(field(seed + 1, 2.0, 40.0, 2.0)))[:, :, None]
    if stripe is not None:
        band = (np.abs(grid_v / size - 0.5) > 0.5 - stripe[0])
        sheet = np.where(band[:, :, None], np.asarray(stripe[1]), sheet)
    albedo = mix(sheet, np.asarray(ink), np.clip(inked, 0.0, 1.0) * 0.92)
    stain_field = field(seed + 2, 1.5, 25.0, 2.2)
    stain = cover(stain_field, 0.25 * weather, 0.3)
    albedo = mix(albedo, albedo * np.array([0.72, 0.6, 0.42]), stain * 0.6)
    runs = cover(field(seed + 3, 2.0, 120.0, 2.0, 1.0, 9.0), 0.3 * weather, 0.4)
    albedo = mix(albedo, albedo * np.array([0.6, 0.55, 0.48]), runs * 0.45)
    fold = np.maximum(sstep(3.0, 0.0, np.abs(grid_u - size * 0.5)), sstep(3.0, 0.0, np.abs(grid_v - size * 0.5)))
    albedo = mix(albedo, albedo * 0.8, fold * 0.5 * weather)
    mold = cover(speckle(seed + 4, 1.3), 0.1, 0.3) * cover(field(seed + 5, 2.0, 30.0), 0.2 * weather, 0.4)
    albedo = mix(albedo, np.array([0.03, 0.035, 0.028]), mold * 0.6)
    write_png(path, srgb(albedo))
    print("HERO", os.path.basename(path), flush=True)
