import json
import math
import os
import random
import sys
from urllib.parse import unquote

import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)

import buildkit as kit
from buildkit import V, Geo, emit, block, rod, linear, field, unit, sstep, cover, patchy, blur, speckle, mix, tint, flat, cavity

try:
    import bpy
    import bmesh
    from mathutils import Matrix, Vector, geometry
except ImportError:
    bpy = None

size = kit.size
root = kit.root
models_root = kit.models_root
library_root = kit.library_root
preview_root = os.path.join(root, "assets", "previews", "railway")
source_textures = os.path.join(root, "assets", "source", "textures")
raw_textures = os.path.join(root, "assets", "raw", "textures")
acg_textures = os.path.join(root, "assets", "raw", "textures_acg")
tau = math.pi * 2.0
grid_u = kit.grid_u
grid_v = kit.grid_v
strip_rows = 126
strip_count = 6
end_rows = 134
rail_rows = {"bright": (0, 144), "dull": (144, 288), "side": (288, 960), "cap": (960, 1024)}
swatches = {}


def read_pixels(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    data = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(height, width, 4).astype(np.float64)


def shrink(image, target):
    factor = image.shape[0] // target
    if factor <= 1:
        return image
    trimmed = image[:target * factor, :target * factor]
    return trimmed.reshape(target, factor, target, factor, -1).mean(axis=(1, 3))


def decode(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def repeated(image, repeat):
    return np.tile(image, (repeat, repeat, 1)) if image.ndim == 3 else np.tile(image, (repeat, repeat))


def slopes_of(normal_pixels, flip):
    n = normal_pixels[:, :, :3] * 2.0 - 1.0
    if flip:
        n[:, :, 1] *= -1.0
    nz = np.maximum(n[:, :, 2], 0.2)
    return -n[:, :, 0] / nz, -n[:, :, 1] / nz


def scan(name, repeat=1):
    base = None
    for folder in (source_textures, raw_textures):
        if os.path.isdir(os.path.join(folder, name)):
            base = os.path.join(folder, name, name)
    target = size // repeat
    diff = shrink(read_pixels(base + "_diff_2k.jpg")[:, :, :3], target)
    arm = shrink(read_pixels(base + "_arm_2k.jpg")[:, :, :3], target)
    flip = not os.path.exists(base + "_nor_gl_2k.jpg")
    gx, gy = slopes_of(shrink(read_pixels(base + ("_nor_dx_2k.jpg" if flip else "_nor_gl_2k.jpg")), target), flip)
    return {"albedo": repeated(decode(diff), repeat), "ao": repeated(arm[:, :, 0], repeat), "rough": repeated(arm[:, :, 1], repeat), "metal": repeated(arm[:, :, 2], repeat), "gx": repeated(gx, repeat), "gy": repeated(gy, repeat)}


def scan_acg(name, repeat=1):
    base = os.path.join(acg_textures, name, name + "_2K-JPG_")
    target = size // repeat
    color = shrink(read_pixels(base + "Color.jpg")[:, :, :3], target)
    rough = shrink(read_pixels(base + "Roughness.jpg")[:, :, :1], target)[:, :, 0]
    metal = shrink(read_pixels(base + "Metalness.jpg")[:, :, :1], target)[:, :, 0] if os.path.exists(base + "Metalness.jpg") else np.zeros((target, target))
    ao = shrink(read_pixels(base + "AmbientOcclusion.jpg")[:, :, :1], target)[:, :, 0] if os.path.exists(base + "AmbientOcclusion.jpg") else np.ones((target, target))
    gx, gy = slopes_of(shrink(read_pixels(base + "NormalGL.jpg"), target), False)
    result = {"albedo": repeated(decode(color), repeat), "ao": repeated(ao, repeat), "rough": repeated(rough, repeat), "metal": repeated(metal, repeat), "gx": repeated(gx, repeat), "gy": repeated(gy, repeat)}
    if os.path.exists(base + "Displacement.jpg"):
        result["height"] = repeated(shrink(read_pixels(base + "Displacement.jpg")[:, :, :1], target)[:, :, 0], repeat)
    return result


def shuffled(maps, seed, amount=0.5, mirror=True):
    rng = np.random.default_rng(seed)
    mask = cover(field(seed, 1.2, 5.0, 2.0), amount, 0.22)
    dy = int(rng.integers(size // 8, size // 2))
    dx = int(rng.integers(size // 8, size // 2))
    out = {}
    for key, value in maps.items():
        other = value[:, ::-1] if mirror else value
        if mirror and key == "gx":
            other = -other
        other = np.roll(other, (dy, dx), (0, 1))
        weight = mask[:, :, None] if value.ndim == 3 else mask
        out[key] = value * (1.0 - weight) + other * weight
    return out


def shifted(maps, dy, dx):
    return {key: np.roll(value, (dy, dx), (0, 1)) for key, value in maps.items()}


def blended(a, b, weight):
    out = {}
    for key in a:
        w = weight[:, :, None] if a[key].ndim == 3 else weight
        out[key] = a[key] * (1.0 - w) + b[key] * w
    return out


def luminance(color):
    return color[:, :, 0] * 0.2126 + color[:, :, 1] * 0.7152 + color[:, :, 2] * 0.0722


def gradient_of(height, texel):
    tu, tv = texel if isinstance(texel, tuple) else (texel, texel)
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / (2.0 * tu)
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / (2.0 * tv)
    return gx, gy


def save_set(name, albedo, rough, occlusion, tile, height=None, gradient=None, strength=1.0, metal=None, alpha=None, texel=None):
    os.makedirs(library_root, exist_ok=True)
    gx = np.zeros((size, size))
    gy = np.zeros((size, size))
    if height is not None:
        hx, hy = gradient_of(height, texel if texel is not None else tile / size)
        gx += hx * strength
        gy += hy * strength
    if gradient is not None:
        gx += gradient[0]
        gy += gradient[1]
    normal = np.stack([-gx, -gy, np.ones((size, size))], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    light = np.array([-0.45, 0.55, 0.7])
    light /= np.linalg.norm(light)
    shaded = kit.srgb(albedo * (0.25 + 0.95 * np.clip(normal @ light, 0.0, 1.0))[:, :, None] * np.clip(occlusion, 0.0, 1.0)[:, :, None])
    if alpha is not None:
        shaded = shaded * alpha[:, :, None] + 0.04 * (1.0 - alpha[:, :, None])
    swatches[name] = shaded.reshape(256, 4, 256, 4, 3).mean(axis=(1, 3))
    color = kit.srgb(albedo)
    if alpha is not None:
        color = np.concatenate([color, np.clip(alpha, 0.0, 1.0)[:, :, None]], -1)
    kit.write_png(os.path.join(library_root, name + "_albedo.png"), color)
    kit.write_png(os.path.join(library_root, name + "_orm.png"), np.stack([np.clip(occlusion, 0.0, 1.0), np.clip(rough, 0.03, 1.0), np.zeros((size, size)) if metal is None else np.clip(metal, 0.0, 1.0)], -1))
    kit.write_png(os.path.join(library_root, name + "_normal.png"), normal * 0.5 + 0.5)
    print("LIBRARY", name, "tile", tile, "albedo", np.round(albedo.reshape(-1, 3).mean(0), 3).tolist(), "rough", round(float(np.mean(rough)), 3), flush=True)


def write_sheet(path):
    names = list(swatches)
    if not names:
        return
    columns = 6
    rows = (len(names) + columns - 1) // columns
    sheet = np.full((rows * 264, columns * 264, 3), 0.1)
    for number, name in enumerate(names):
        r = rows - 1 - number // columns
        c = number % columns
        sheet[r * 264 + 4:r * 264 + 260, c * 264 + 4:c * 264 + 260] = swatches[name]
        kit.text(sheet, c * 264 + 8, r * 264 + 8, name.replace("_", " "), (1.0, 1.0, 1.0), 1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    kit.write_png(path, sheet)


def make_ballast():
    tile = 2.0
    seed = 5100
    rng = np.random.default_rng(seed)
    scale = size / tile
    height = -0.046 + 0.004 * field(seed + 1, 20.0, 300.0, 1.4)
    ident = np.zeros((size, size), np.int64)
    palette = [linear(132, 126, 120), linear(106, 102, 100), linear(136, 116, 104), linear(88, 82, 78), linear(120, 100, 84), linear(150, 144, 136), linear(124, 104, 96), linear(112, 108, 100)]
    weights = np.array([0.22, 0.2, 0.14, 0.1, 0.1, 0.06, 0.1, 0.08])
    layers = ((6400, (0.009, 0.017), (-0.036, -0.02)), (4700, (0.017, 0.03), (-0.026, -0.004)), (950, (0.022, 0.036), (-0.008, 0.012)))
    colors = [linear(58, 48, 40)]
    number = 0
    for count, radius, level in layers:
        picks = rng.choice(len(palette), count, p=weights)
        for index in range(count):
            number += 1
            cx = rng.uniform(0.0, size)
            cy = rng.uniform(0.0, size)
            r = rng.uniform(radius[0], radius[1]) * scale
            top = rng.uniform(level[0], level[1])
            thickness = r / scale * rng.uniform(0.7, 1.15)
            reach = int(r * 1.3) + 2
            cols = np.arange(int(cx) - reach, int(cx) + reach + 1)
            rows = np.arange(int(cy) - reach, int(cy) + reach + 1)
            lv, lu = np.meshgrid(rows + 0.5 - cy, cols + 0.5 - cx, indexing="ij")
            sides = int(rng.integers(5, 9))
            start = rng.uniform(0.0, tau)
            side = np.full(lu.shape, 1e9)
            for s in range(sides):
                angle = start + tau * (s + rng.uniform(-0.28, 0.28)) / sides
                side = np.minimum(side, (r * rng.uniform(0.62, 1.0) - (lu * math.cos(angle) + lv * math.sin(angle))) * rng.uniform(1.4, 4.5) / scale)
            cap = np.full(lu.shape, thickness)
            for f in range(int(rng.integers(1, 4))):
                angle = rng.uniform(0.0, tau)
                cap = np.minimum(cap, thickness + (lu * math.cos(angle) + lv * math.sin(angle)) * rng.uniform(0.08, 0.6) / scale)
            z = top - thickness + np.minimum(side, cap)
            where = np.ix_(rows % size, cols % size)
            current = height[where]
            take = (side > 0.0) & (z > current)
            height[where] = np.where(take, z, current)
            ident[where] = np.where(take, number, ident[where])
            colors.append(palette[picks[index]] * rng.uniform(0.82, 1.12))
    albedo = np.array(colors)[ident]
    dark, light, pink = kit.granite_grains(seed + 30)
    albedo = tint(albedo, 1.0 - 0.4 * dark)
    albedo = mix(albedo, linear(206, 200, 190), light * 0.22)
    stain = unit(field(seed + 40, 1.5, 12.0, 2.2))
    albedo = mix(albedo, albedo * np.array([0.92, 0.7, 0.52]), 0.35 + 0.45 * stain)
    oil = cover(field(seed + 41, 2.0, 30.0, 2.0), 0.14, 0.5)
    albedo = mix(albedo, albedo * 0.45, oil * 0.65)
    fines = sstep(-0.02, -0.038, height)
    dirt = mix(linear(66, 54, 42), linear(44, 36, 28), unit(field(seed + 42, 10.0, 300.0)))
    albedo = mix(albedo, dirt, fines * 0.9)
    silt = cover(field(seed + 44, 3.0, 40.0, 2.0), 0.3, 0.6) * sstep(0.004, -0.02, height)
    albedo = mix(albedo, dirt * 1.25, silt * 0.55)
    rim = np.clip((height - blur(height, 1.6)) / 0.003, 0.0, 1.0)
    albedo = mix(albedo, albedo * 1.12, rim * 0.5)
    crevice = cavity(height, 2.2, 0.008)
    albedo = tint(albedo, 1.0 - 0.55 * crevice)
    rough = 0.86 + 0.04 * field(seed + 43, 8.0, 200.0) - 0.06 * light - 0.2 * oil
    occlusion = 1.0 - 0.6 * crevice - 0.3 * cavity(height, 8.0, 0.018)
    save_set("ballast_stone", albedo, rough, occlusion, tile, height=height, strength=0.75)


def make_sleepers():
    seed = 5200
    rng = np.random.default_rng(seed)
    u = grid_u / size
    strip = np.clip(np.floor(grid_v / strip_rows), 0, strip_count - 1).astype(np.int64)
    in_strips = grid_v < strip_rows * strip_count
    across = (grid_v - strip * strip_rows) / strip_rows
    fibre = field(seed + 1, 2.0, 700.0, 1.2, 18.0, 0.7)
    wave = field(seed + 2, 0.5, 6.0, 2.0, 3.0, 1.0)
    rings = rng.uniform(5.0, 9.0, strip_count)[strip]
    late = sstep(0.5, 0.95, 0.5 + 0.5 * np.sin((across * rings + wave * 0.35 + strip * 0.37) * tau))
    tone = np.array([0.2, 0.75, 0.45, 0.95, 0.3, 0.6])[strip]
    creosote = mix(linear(62, 46, 34), linear(44, 34, 26), unit(field(seed + 3, 1.0, 20.0, 2.0, 2.0, 1.0)))
    grey = mix(linear(118, 110, 100), linear(96, 88, 78), unit(field(seed + 4, 1.5, 30.0, 2.0, 2.0, 1.0)))
    bleach = cover(field(seed + 5, 3.0, 200.0, 1.6, 8.0, 1.0), 0.45, 0.6)
    albedo = mix(creosote, grey, np.clip(tone * (0.35 + 0.85 * bleach), 0.0, 1.0))
    albedo = tint(albedo, 0.9 + 0.12 * fibre)
    albedo = mix(albedo, albedo * 0.62, late * 0.5)
    endness = np.maximum(sstep(0.2, 0.0, u), sstep(0.8, 1.0, u))
    checks = np.maximum(cover(field(seed + 6, 1.0, 300.0, 1.4, 40.0, 0.6), 0.035, 0.2), cover(field(seed + 7, 1.0, 300.0, 1.4, 30.0, 0.6), 0.12, 0.2) * endness)
    split = np.zeros((size, size))
    for s in range(strip_count):
        rows = slice(s * strip_rows, (s + 1) * strip_rows)
        a = across[rows]
        for end in (0, 1):
            along = u[rows] if end == 0 else 1.0 - u[rows]
            for k in range(int(rng.integers(0, 4))):
                reach = rng.uniform(0.04, 0.16)
                centre = rng.uniform(0.2, 0.8) + rng.uniform(-0.2, 0.2) * along / reach + 0.03 * np.sin(along * rng.uniform(40.0, 90.0) + rng.uniform(0.0, 6.0))
                width = np.maximum(rng.uniform(0.025, 0.07) * np.clip(1.0 - along / reach, 0.0, 1.0), 1e-4)
                split[rows] = np.maximum(split[rows], sstep(width, width * 0.35, np.abs(a - centre)) * (along < reach))
    seat = np.maximum(np.exp(-((u - 0.2106) * 2.6 / 0.2) ** 2), np.exp(-((u - 0.7894) * 2.6 / 0.2) ** 2))
    rust = seat * (0.55 + 0.45 * unit(field(seed + 8, 3.0, 60.0)))
    albedo = mix(albedo, linear(124, 70, 38) * (0.75 + 0.4 * unit(speckle(seed + 9, 1.2)))[:, :, None], rust * 0.6)
    four = sstep(0.27, 0.34, u) * sstep(0.73, 0.66, u)
    oil = cover(field(seed + 10, 6.0, 300.0, 1.5, 9.0, 1.0), 0.22, 0.45) * four
    albedo = mix(albedo, linear(24, 20, 17), oil * 0.55)
    tar = cover(field(seed + 11, 8.0, 400.0, 1.4, 12.0, 1.0), 0.1, 0.3) * (1.0 - tone)
    albedo = mix(albedo, linear(20, 16, 13), tar * 0.7)
    moss = patchy(seed + 13, 0.07, 18.0, 300.0, 0.9) * endness * (tone > 0.5)
    albedo = mix(albedo, linear(74, 90, 42) * (0.7 + 0.5 * unit(speckle(seed + 14, 1.3)))[:, :, None], moss * 0.8)
    dust = sstep(0.12, 0.0, np.minimum(across, 1.0 - across)) * cover(field(seed + 15, 3.0, 80.0), 0.5, 0.6)
    albedo = mix(albedo, linear(132, 120, 104), dust * 0.3)
    albedo = mix(albedo, linear(14, 11, 9), np.clip(checks + split, 0.0, 1.0) * 0.92)
    height = -late * 0.0007 + fibre * 0.00025 - checks * 0.003 - split * 0.007 + moss * 0.002
    rough = 0.84 + 0.05 * fibre - 0.3 * tar - 0.25 * oil + 0.06 * moss
    occlusion = 1.0 - 0.6 * checks - 0.75 * split - 0.3 * cavity(height, 2.0, 0.0012)
    wobble = field(seed + 20, 3.0, 40.0, 2.0)
    grain = speckle(seed + 21, 0.9)
    for r in range(2):
        for c in range(4):
            rows = slice(strip_count * strip_rows + r * end_rows, strip_count * strip_rows + (r + 1) * end_rows)
            cols = slice(c * 256, (c + 1) * 256)
            x = (grid_u[rows, cols] - c * 256) / 1024.0
            y = (grid_v[rows, cols] - rows.start) / 1024.0
            px = rng.uniform(-0.05, 0.3)
            py = rng.uniform(-0.12, 0.2)
            d = np.hypot(x - px, y - py)
            theta = np.arctan2(y - py, x - px)
            ring = sstep(0.4, 0.95, 0.5 + 0.5 * np.sin(d / rng.uniform(0.004, 0.007) * tau + wobble[rows, cols] * 2.5))
            crack = np.zeros(x.shape)
            for k in range(int(rng.integers(3, 8))):
                angle = rng.uniform(-math.pi, math.pi)
                delta = np.abs((theta - angle + math.pi) % tau - math.pi) * d
                width = rng.uniform(0.0012, 0.0035)
                inner = rng.uniform(0.0, 0.06)
                crack = np.maximum(crack, sstep(width, width * 0.3, delta) * sstep(inner, inner + 0.02, d) * sstep(inner + rng.uniform(0.08, 0.3), inner + 0.05, d))
            age = rng.uniform(0.2, 0.9)
            base = mix(linear(66, 50, 38), linear(116, 108, 98), age) * (0.9 + 0.12 * grain[rows, cols])[:, :, None]
            base = base * (1.0 - 0.38 * ring)[:, :, None]
            base = base * (1.0 - 0.9 * crack)[:, :, None] + linear(12, 10, 8) * (0.9 * crack)[:, :, None]
            albedo[rows, cols] = base
            height[rows, cols] = -ring * 0.0005 - crack * 0.004 + grain[rows, cols] * 0.0001
            rough[rows, cols] = 0.9
            occlusion[rows, cols] = 1.0 - 0.75 * crack - 0.15 * ring
    gx, gy = gradient_of(height, (2.6 / size, 0.25 / strip_rows))
    ex, ey = gradient_of(height, 1.0 / 1024.0)
    gx = np.where(in_strips, gx, ex)
    gy = np.where(in_strips, gy, ey)
    save_set("sleeper_timber", albedo, rough, occlusion, 1.0, gradient=(gx, gy))


def make_rail_steel():
    seed = 5300
    row = grid_v
    band = float(rail_rows["bright"][1])
    side0, side1 = rail_rows["side"]
    streak = field(seed, 3.0, 700.0, 1.0, 30.0, 0.35)
    line1 = field(seed + 1, 1.0, 8.0, 2.0)[0][None, :]
    line2 = field(seed + 2, 1.0, 10.0, 2.0)[0][None, :]
    bright = row < band
    a = np.where(bright, row / band, (row - band) / band)
    centre = 0.4 + 0.02 * line1
    half = np.where(bright, 0.2 + 0.02 * line2, 0.075 + 0.02 * line2)
    shine = sstep(half + 0.07, half - 0.04, np.abs(a - centre))
    shine = shine * np.where(bright, 1.0, 0.8 * cover(field(seed + 4, 4.0, 200.0, 1.6, 6.0, 1.0), 0.6, 0.6))
    steel = flat(linear(150, 150, 154)) * (0.88 + 0.14 * streak)[:, :, None]
    film = mix(linear(70, 50, 38), linear(46, 36, 30), unit(field(seed + 5, 6.0, 200.0, 1.6, 4.0, 1.0)))
    bloom = cover(speckle(seed + 6, 1.4), 0.12, 0.4) * (1.0 - shine)
    film = mix(film, linear(150, 86, 40), bloom * 0.6)
    head = mix(film, steel, shine)
    head = mix(head, linear(40, 40, 46), np.clip(shine * (1.0 - shine) * 3.0, 0.0, 1.0) * 0.5)
    pits = cover(speckle(seed + 7, 1.0), 0.015, 0.3) * shine
    head = mix(head, linear(60, 40, 30), pits * 0.8)
    head_rough = mix(0.82, 0.3 + 0.1 * unit(streak), shine) + 0.3 * pits
    head_metal = shine * (1.0 - 0.7 * pits)
    p = np.clip((row - side0) / (side1 - side0), 0.0, 1.0)
    n1 = field(seed + 8, 6.0, 90.0, 1.7, 1.0, 4.5)
    n2 = field(seed + 9, 30.0, 400.0, 1.3, 1.0, 4.5)
    rust = mix(linear(104, 60, 36), linear(66, 40, 27), unit(n1))
    rust = mix(rust, linear(148, 84, 40), cover(n2 + 0.5 * n1, 0.22, 0.3) * 0.7)
    rust = mix(rust, linear(40, 28, 22), cover(field(seed + 10, 10.0, 200.0, 1.5, 1.0, 4.5), 0.2, 0.3) * 0.7)
    rust = tint(rust, 0.85 + 0.3 * unit(speckle(seed + 11, 1.0)))
    runs = cover(field(seed + 12, 4.0, 300.0, 1.6, 1.0, 22.0), 0.2, 0.4)
    rust = mix(rust, linear(156, 96, 52), runs * 0.35)
    grime = np.exp(-((p - 0.27) / 0.09) ** 2)
    rust = mix(rust, linear(26, 22, 20), grime * 0.55)
    dusty = sstep(0.62, 0.8, p) * (0.5 + 0.5 * unit(field(seed + 13, 5.0, 100.0, 1.6, 1.0, 4.5)))
    rust = mix(rust, linear(122, 104, 88), dusty * 0.5)
    gauge = sstep(0.14, 0.04, p) * (0.6 + 0.4 * unit(field(seed + 14, 3.0, 60.0, 1.8, 8.0, 1.0)))
    rust = mix(rust, linear(84, 80, 78), gauge * 0.45)
    side_rough = 0.88 - 0.3 * gauge - 0.12 * grime + 0.04 * n2
    side_metal = gauge * 0.45
    top = (row < side0)
    albedo = np.where(top[:, :, None], head, rust)
    rough = np.where(top, head_rough, side_rough)
    metal = np.where(top, head_metal, side_metal)
    height = np.where(top, streak * 0.00004 * shine - pits * 0.0003 + bloom * 0.0001, n2 * 0.00035 + n1 * 0.0003 - grime * 0.0001)
    occlusion = np.where(top, 1.0, 1.0 - 0.35 * grime - 0.2 * cavity(height, 2.0, 0.0006))
    save_set("rail_steel", albedo, rough, occlusion, 1.5, height=height, texel=(1.5 / size, 0.4 / size), metal=metal)


cache = {}


def rust_maps():
    if "rust" not in cache:
        maps = scan("rusty_metal_04", 1)
        rgb = maps["albedo"]
        rusty = sstep(1.6, 3.0, rgb[:, :, 0] / (rgb[:, :, 2] + 0.01))
        out = {key: value.copy() for key, value in maps.items()}
        filled = rusty.copy()
        for dy, dx in ((311, 173), (-257, 389), (129, -431), (467, 97), (-391, -219), (83, 499), (-149, -347)):
            other = shifted(maps, dy, dx)
            take = (1.0 - filled) * np.roll(rusty, (dy, dx), (0, 1))
            out = blended(out, other, take)
            filled = filled + take
        rest = np.clip(1.0 - filled, 0.0, 1.0)
        mean_rust = (rgb * rusty[:, :, None]).sum((0, 1)) / max(rusty.sum(), 1.0)
        out["albedo"] = out["albedo"] * (1.0 - rest[:, :, None]) + mean_rust * rest[:, :, None]
        cache["rust"] = out
    return cache["rust"]


def resampled(maps, repeat):
    if repeat <= 1:
        return {key: value.copy() for key, value in maps.items()}
    out = {}
    for key, value in maps.items():
        small = shrink(value if value.ndim == 3 else value[:, :, None], size // repeat)
        out[key] = repeated(small if value.ndim == 3 else small[:, :, 0], repeat)
    return out


def draw_streaks(seed, count, v_range=(0.3, 0.95), length=(0.12, 0.45), width=(2.5, 8.0)):
    rng = np.random.default_rng(seed)
    stain = np.zeros((size, size))
    chip = np.zeros((size, size))
    for number in range(count):
        cu = rng.uniform(0.0, size)
        span = rng.uniform(length[0], length[1]) * size
        top = max(rng.uniform(v_range[0], v_range[1]) * size, span + 0.04 * size)
        w = rng.uniform(width[0], width[1])
        rows = np.arange(int(top - span), int(top) + int(w) + 3)
        cols = np.arange(int(cu - 5.0 * w), int(cu + 5.0 * w) + 1)
        lv, lu = np.meshgrid(rows + 0.5, cols + 0.5, indexing="ij")
        down = (top - lv) / span
        wobble = w * 0.6 * np.sin(down * rng.uniform(5.0, 14.0) + rng.uniform(0.0, tau))
        spread = w * (0.7 + 0.9 * np.sqrt(np.clip(down, 0.0, 1.0)))
        value = np.exp(-((lu - cu - wobble) / spread) ** 2) * np.clip(1.0 - down, 0.0, 1.0) ** 1.3 * (down > -0.01) * rng.uniform(0.5, 1.0)
        where = np.ix_(rows % size, cols % size)
        stain[where] = np.maximum(stain[where], value)
        chip[where] = np.maximum(chip[where], sstep(w * 0.9, w * 0.45, np.hypot(lu - cu, (lv - top) * 0.7)))
    return stain, chip


def weathered(paint, seed, bottom=0.14, bottom_amount=1.0, spots=0.025, streaks=16, grime=0.25, fade=0.3, rust_repeat=2):
    rust = shuffled(resampled(rust_maps(), rust_repeat), seed + 90, 0.5)
    v = grid_v / size
    n = field(seed + 1, 3.0, 60.0, 1.8)
    fine = field(seed + 2, 20.0, 300.0, 1.4)
    edge = sstep(bottom, 0.0, v)
    eaten = sstep(-0.05, 0.12, edge * 2.2 * bottom_amount + n * 0.6 * edge + fine * 0.25 * edge - 1.0) if bottom > 0.0 else np.zeros((size, size))
    near = sstep(bottom * 3.0 + 0.1, 0.0, v)
    blister = cover(speckle(seed + 3, 1.7) + near * 1.4 + 0.4 * n, spots, 0.12)
    patch = cover(n + 0.5 * fine, spots * 0.8, 0.06)
    stain, chip = draw_streaks(seed + 4, streaks)
    stain = stain * (0.6 + 0.4 * unit(fine))
    bare = np.clip(np.maximum(np.maximum(eaten, blister), np.maximum(patch, chip)), 0.0, 1.0)
    halo = np.clip(blur(bare, 5.0) * 1.8 - bare, 0.0, 1.0)
    chalk = cover(field(seed + 5, 1.2, 9.0, 2.2), 0.45, 0.6)
    albedo = paint["albedo"]
    grey = luminance(albedo)[:, :, None]
    albedo = mix(albedo, albedo * 0.55 + grey * 0.75 + 0.02, chalk * fade)
    dirt = cover(field(seed + 6, 2.0, 120.0, 1.8, 1.0, 9.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * np.array([0.55, 0.5, 0.45]), dirt * grime)
    albedo = mix(albedo, albedo * np.array([1.3, 0.75, 0.42]) + np.array([0.05, 0.018, 0.005]), np.clip(stain * 0.9 + halo * 0.5, 0.0, 1.0))
    albedo = mix(albedo, rust["albedo"] * (0.85 + 0.3 * unit(fine))[:, :, None], bare)
    rough = mix(np.clip(paint["rough"] + 0.12 * chalk, 0.0, 1.0), np.maximum(rust["rough"], 0.78), bare)
    rough = mix(rough, 0.8, np.clip(stain * 0.6, 0.0, 1.0))
    metal = np.zeros((size, size))
    occlusion = mix(np.clip(0.8 + 0.2 * paint["ao"], 0.0, 1.0), np.clip(0.75 + 0.25 * rust["ao"], 0.0, 1.0), bare)
    lip = np.clip(blur(bare, 1.2) - bare, 0.0, 1.0)
    height = -bare * 0.0005 + lip * 0.0006 + blister * 0.0002
    gx = paint["gx"] * (1.0 - bare) + rust["gx"] * bare * 0.8
    gy = paint["gy"] * (1.0 - bare) + rust["gy"] * bare * 0.8
    return albedo, rough, metal, occlusion, height, (gx, gy), bare


def recoloured(paint, color, keep_rust=True, contrast=1.0, rust_keep=1.0):
    rgb = paint["albedo"]
    lum = luminance(rgb)
    relative = (lum / max(float(np.median(lum)), 1e-4)) ** contrast
    result = dict(paint)
    painted = np.clip(relative, 0.3, 2.2)[:, :, None] * np.asarray(color)
    if keep_rust:
        rusty = sstep(1.35, 2.2, rgb[:, :, 0] / (rgb[:, :, 1] + 0.004))[:, :, None] * rust_keep
        painted = painted * (1.0 - rusty) + rgb * rusty
    result["albedo"] = painted
    return result


def make_loco_green():
    seed = 5500
    paint = shuffled(scan("green_metal_rust", 2), seed, 0.5)
    paint["albedo"] = paint["albedo"] * np.array([0.78, 0.86, 0.8])
    albedo, rough, metal, occlusion, height, gradient, bare = weathered(paint, seed, 0.13, 1.0, 0.03, 26, 0.3, 0.35)
    save_set("loco_green", albedo, rough, occlusion, 2.0, height=height, gradient=gradient, metal=metal)


def make_loco_black():
    seed = 5600
    paint = recoloured(shuffled(scan("green_metal_rust", 2), seed, 0.5), linear(34, 33, 32), False, 0.8)
    oil = cover(field(seed + 20, 2.0, 40.0, 2.0), 0.3, 0.5)
    paint["rough"] = np.clip(paint["rough"] * 0.9 - 0.22 * oil, 0.2, 1.0)
    paint["albedo"] = mix(paint["albedo"], paint["albedo"] * 0.6, oil * 0.6)
    dust = cover(field(seed + 21, 2.0, 60.0, 2.0, 2.0, 1.0), 0.4, 0.6)
    paint["albedo"] = mix(paint["albedo"], linear(74, 60, 48), dust * 0.3)
    paint["rough"] = np.clip(paint["rough"] + 0.2 * dust, 0.0, 1.0)
    albedo, rough, metal, occlusion, height, gradient, bare = weathered(paint, seed, 0.0, 0.0, 0.11, 10, 0.2, 0.15)
    save_set("loco_black", albedo, rough, occlusion, 2.0, height=height, gradient=gradient, metal=metal)


def make_wasp():
    seed = 5700
    base = shuffled(scan("green_metal_rust", 1), seed, 0.5)
    stripe = ((grid_u + grid_v) / size * 4.0) % 1.0
    yellow = sstep(0.0, 0.012, stripe) * sstep(0.5, 0.488, stripe)
    paint = recoloured(base, np.array([1.0, 1.0, 1.0]), True, 0.8)
    tone = mix(linear(30, 29, 28), mix(linear(196, 150, 24), linear(184, 160, 78), cover(field(seed + 30, 1.5, 12.0, 2.2), 0.5, 0.6)), yellow)
    rusty = sstep(1.35, 2.2, base["albedo"][:, :, 0] / (base["albedo"][:, :, 1] + 0.004))[:, :, None]
    paint["albedo"] = paint["albedo"] * tone * (1.0 - rusty) + base["albedo"] * rusty
    albedo, rough, metal, occlusion, height, gradient, bare = weathered(paint, seed, 0.1, 0.8, 0.07, 14, 0.4, 0.25, 1)
    save_set("wasp_stripes", albedo, rough, occlusion, 1.0, height=height, gradient=gradient, metal=metal)


def make_chequer():
    seed = 5800
    maps = scan("metal_plate", 1)
    albedo = maps["albedo"]
    grey = luminance(albedo)[:, :, None]
    albedo = albedo * 0.6 + grey * np.array([0.5, 0.42, 0.34]) * 0.9
    raised = sstep(0.55, 0.75, maps["ao"]) * sstep(0.0, 0.25, np.hypot(maps["gx"], maps["gy"]))
    worn = cover(field(seed + 1, 1.5, 20.0, 2.0), 0.4, 0.6)
    lug = np.clip(blur(sstep(0.12, 0.3, np.hypot(maps["gx"], maps["gy"])), 2.0) * 1.6, 0.0, 1.0)
    polish = lug * worn
    albedo = mix(albedo, linear(128, 124, 118), polish * 0.55)
    mud = cover(field(seed + 2, 3.0, 60.0, 2.0), 0.3, 0.5) * (1.0 - lug)
    albedo = mix(albedo, linear(70, 56, 42), mud * 0.6)
    rough = np.clip(maps["rough"] * (1.0 - 0.45 * polish) + 0.15 * mud, 0.2, 1.0)
    metal = polish * 0.7
    save_set("chequer_plate", albedo, rough, np.clip(0.7 + 0.3 * maps["ao"], 0.0, 1.0), 1.0, gradient=(maps["gx"], maps["gy"]), metal=metal)


def make_wagon_grey():
    seed = 5900
    paint = shuffled(scan("rusty_metal_04", 2), seed, 0.5)
    albedo, rough, metal, occlusion, height, gradient, bare = weathered(paint, seed, 0.16, 1.1, 0.04, 8, 0.2, 0.2)
    save_set("wagon_grey", albedo, rough, occlusion, 2.0, height=height, gradient=gradient, metal=metal)


def make_coach_livery():
    seed = 6000
    v = grid_v / size
    upper = sstep(0.497, 0.503, v)
    cream = recoloured(shuffled(scan("rusty_metal_02", 2), seed, 0.5), linear(214, 196, 150), True, 0.7, 0.22)
    maroon = recoloured(shuffled(scan("green_metal_rust", 2), seed + 1, 0.5), linear(98, 28, 30), True, 0.9)
    fade = unit(field(seed + 2, 1.0, 5.0, 2.4))
    maroon["albedo"] = mix(maroon["albedo"], maroon["albedo"] * 0.6 + linear(150, 96, 88) * 0.4, fade * 0.45)
    paint = blended(maroon, cream, upper)
    local = np.where(v < 0.5, v * 2.0, (v - 0.5) * 2.0)
    line = sstep(0.014, 0.008, np.abs(v - 0.5))
    gold = sstep(0.004, 0.002, np.abs(v - 0.5 - 0.011)) + sstep(0.004, 0.002, np.abs(v - 0.5 + 0.011))
    lining_wear = cover(field(seed + 3, 6.0, 200.0, 1.6, 6.0, 1.0), 0.6, 0.3)
    paint["albedo"] = mix(paint["albedo"], linear(24, 22, 22), line * lining_wear * 0.9)
    paint["albedo"] = mix(paint["albedo"], linear(190, 150, 60), np.clip(gold, 0.0, 1.0) * lining_wear * 0.85)
    albedo, rough, metal, occlusion, height, gradient, bare = weathered(paint, seed + 10, 0.09, 1.0, 0.011, 0, 0.0, 0.0)
    stain, chip = draw_streaks(seed + 11, 14, (0.6, 0.98), (0.1, 0.3), (2.5, 7.0))
    lower_stain, lower_chip = draw_streaks(seed + 12, 8, (0.2, 0.48), (0.08, 0.18), (2.5, 6.0))
    stain = np.maximum(stain, lower_stain)
    albedo = mix(albedo, albedo * np.array([1.1, 0.72, 0.45]) + np.array([0.03, 0.012, 0.004]), np.clip(stain * 0.7, 0.0, 1.0))
    top_grime = sstep(0.78, 1.0, v) * cover(field(seed + 13, 2.0, 120.0, 1.8, 1.0, 8.0), 0.55, 0.5)
    albedo = mix(albedo, albedo * np.array([0.5, 0.47, 0.42]), top_grime * 0.55)
    all_grime = cover(field(seed + 14, 2.0, 120.0, 1.8, 1.0, 8.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * np.array([0.62, 0.58, 0.52]), all_grime * 0.3)
    save_set("coach_livery", albedo, rough, occlusion, 2.0, height=height, gradient=gradient, metal=metal)


signs = {
    "halt": (0, 832, 1024, 1024),
    "waiting_room": (0, 768, 352, 832),
    "booking_office": (352, 768, 704, 832),
    "tickets": (704, 768, 864, 832),
    "private": (864, 768, 1024, 832),
    "number": (0, 704, 256, 768),
    "builder": (256, 704, 416, 768),
    "wagon_a": (416, 704, 576, 768),
    "wagon_b": (576, 704, 736, 768),
    "signal_box": (736, 704, 1024, 768),
    "clock": (0, 448, 256, 704),
    "beware": (256, 448, 640, 704),
    "timetable": (640, 448, 816, 704),
    "notice": (816, 448, 1024, 704),
    "arm_front": (0, 352, 512, 448),
    "arm_back": (0, 256, 512, 352),
    "target": (512, 256, 704, 448),
    "advert": (704, 256, 1024, 448),
    "fire": (768, 128, 896, 256),
    "chain": (896, 128, 1024, 256),
}
swatch_names = ("red", "signal_red", "yellow", "white", "black", "brass", "copper", "lens_green", "lens_red", "lens_amber", "lens_clear", "cream", "blue", "steel", "grey", "leather")
label_names = ("on_off", "fuel", "sand", "oil", "brake", "vacuum", "engine_stop", "horn")
gauge_names = ("MPH", "VACUUM", "AIR", "OIL", "WATER", "AMPS")
for number in range(6):
    signs["gauge_%d" % number] = (number * 128, 128, (number + 1) * 128, 256)
for number, name in enumerate(swatch_names):
    signs[name] = (number * 64, 64, (number + 1) * 64, 128)
for number, name in enumerate(label_names):
    signs[name] = (number * 128, 0, (number + 1) * 128, 64)


def sign_uv(name, margin=1.5):
    x0, y0, x1, y1 = signs[name]
    return ((x0 + margin) / size, (y0 + margin) / size, (x1 - margin) / size, (y1 - margin) / size)


def text_mask(items, resolution=2048):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'Standard'
    scene.render.image_settings.file_format = 'PNG'
    world = bpy.data.worlds.new("flat")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    scene.world = world
    white = bpy.data.materials.new("ink")
    white.use_nodes = True
    output = next(node for node in white.node_tree.nodes if node.type == 'OUTPUT_MATERIAL')
    emission = white.node_tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    white.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    fonts = {}
    folder = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    for key, files in (("sans", ("GILB____.TTF", "arialbd.ttf")), ("serif", ("timesbd.ttf", "georgiab.ttf")), ("slab", ("ROCKB.TTF", "timesbd.ttf")), ("light", ("GIL_____.TTF", "arial.ttf"))):
        for entry in files:
            if os.path.exists(os.path.join(folder, entry)):
                fonts[key] = bpy.data.fonts.load(os.path.join(folder, entry))
                break
    created = []
    for body, font, cx, cy, cap, limit, spacing in items:
        curve = bpy.data.curves.new("line", 'FONT')
        curve.body = body
        curve.align_x = 'CENTER'
        curve.align_y = 'CENTER'
        curve.size = cap / size / 0.72
        curve.space_character = spacing
        if font in fonts:
            curve.font = fonts[font]
        curve.materials.append(white)
        obj = bpy.data.objects.new("line", curve)
        obj.location = (cx / size - 0.5, cy / size - 0.5, 0.01)
        scene.collection.objects.link(obj)
        created.append((obj, limit))
    bpy.context.view_layer.update()
    for obj, limit in created:
        if limit and obj.dimensions.x > limit / size:
            factor = (limit / size) / obj.dimensions.x
            obj.scale = (factor, factor, 1.0)
    data = bpy.data.cameras.new("camera")
    data.type = 'ORTHO'
    data.ortho_scale = 1.0
    cam = bpy.data.objects.new("camera", data)
    cam.location = (0.0, 0.0, 2.0)
    scene.collection.objects.link(cam)
    scene.camera = cam
    temporary = os.path.join(library_root, "rail_signs_mask.tmp.png")
    scene.render.filepath = temporary
    bpy.ops.render.render(write_still=True)
    mask = np.clip(read_pixels(temporary)[:, :, 0], 0.0, 1.0)
    os.remove(temporary)
    factor = mask.shape[0] // size
    return mask.reshape(size, factor, size, factor).mean(axis=(1, 3)) if factor > 1 else mask


def make_signs():
    seed = 6100
    items = []

    def say(name, body, cap, font="sans", dx=0.0, dy=0.0, limit=None, spacing=1.0):
        x0, y0, x1, y1 = signs[name]
        items.append((body, font, (x0 + x1) * 0.5 + dx, (y0 + y1) * 0.5 + dy, cap, limit if limit is not None else (x1 - x0) * 0.86, spacing))

    say("halt", "HALT", 104.0, "sans", 0.0, 0.0, None, 1.35)
    say("waiting_room", "WAITING ROOM", 26.0)
    say("booking_office", "BOOKING OFFICE", 26.0)
    say("tickets", "TICKETS", 26.0)
    say("private", "PRIVATE", 26.0)
    say("number", "D2318", 34.0, "slab")
    say("builder", "LOCOMOTIVE WORKS", 7.0, "sans", 0.0, 15.0, 110.0)
    say("builder", "No 2318", 12.0, "sans", 0.0, 0.0, 100.0)
    say("builder", "1958", 9.0, "sans", 0.0, -15.0, 80.0)
    say("wagon_a", "12 T", 17.0, "sans", 0.0, 12.0)
    say("wagon_a", "B 754302", 12.0, "sans", 0.0, -13.0)
    say("wagon_b", "16 T", 17.0, "sans", 0.0, 12.0)
    say("wagon_b", "B 266041", 12.0, "sans", 0.0, -13.0)
    say("signal_box", "HALT SIGNAL BOX", 24.0)
    numerals = ("XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI")
    for hour, numeral in enumerate(numerals):
        angle = math.pi * 0.5 - tau * hour / 12.0
        say("clock", numeral, 15.0, "serif", math.cos(angle) * 88.0, math.sin(angle) * 88.0, 40.0)
    say("beware", "BEWARE", 50.0, "sans", 0.0, 62.0)
    say("beware", "OF TRAINS", 44.0, "sans", 0.0, -4.0)
    say("beware", "STOP   LOOK   LISTEN", 19.0, "sans", 0.0, -78.0)
    say("timetable", "TRAIN SERVICES", 11.0, "sans", 0.0, 104.0)
    say("timetable", "WEEKDAYS", 7.0, "sans", -42.0, 84.0, 60.0)
    say("timetable", "SUNDAYS", 7.0, "sans", 42.0, 84.0, 60.0)
    say("notice", "NOTICE", 24.0, "serif", 0.0, 92.0)
    for row, line in enumerate(("PASSENGERS ARE", "FORBIDDEN TO", "CROSS THE LINE", "EXCEPT BY THE", "CROSSING")):
        say("notice", line, 11.0, "serif", 0.0, 48.0 - row * 24.0)
    say("notice", "BY ORDER", 9.0, "serif", 0.0, -96.0)
    say("advert", "OCEAN SOAP", 40.0, "slab", 0.0, 26.0)
    say("advert", "WASHES WHITER", 17.0, "sans", 0.0, -42.0)
    for number, label in enumerate(gauge_names):
        say("gauge_%d" % number, label, 7.0, "sans", 0.0, -22.0, 60.0)
    say("fire", "FIRE", 30.0, "sans", 0.0, 30.0)
    say("fire", "PULL PIN", 9.0, "sans", 0.0, -6.0)
    say("fire", "AIM AT BASE", 9.0, "sans", 0.0, -24.0)
    say("fire", "SQUEEZE", 9.0, "sans", 0.0, -42.0)
    say("chain", "TO STOP THE TRAIN", 9.0, "sans", 0.0, 40.0)
    say("chain", "PULL DOWN", 13.0, "sans", 0.0, 17.0)
    say("chain", "THE CHAIN", 13.0, "sans", 0.0, -5.0)
    say("chain", "PENALTY FOR", 7.0, "sans", 0.0, -30.0)
    say("chain", "IMPROPER USE \u00a35", 7.0, "sans", 0.0, -43.0)
    for name, body in zip(label_names, ("ON      OFF", "FUEL", "SAND", "OIL", "BRAKE", "VACUUM", "ENGINE STOP", "HORN")):
        say(name, body, 17.0, "sans", 0.0, 0.0, 104.0)
    mask = text_mask(items)
    n1 = field(seed, 3.0, 80.0, 1.8)
    n2 = field(seed + 1, 20.0, 400.0, 1.4)
    n3 = field(seed + 2, 1.5, 20.0, 2.2)
    grain = speckle(seed + 3, 1.2)
    albedo = flat(linear(30, 30, 30))
    rough = np.full((size, size), 0.6)
    metal = np.zeros((size, size))
    height = np.zeros((size, size))
    rust_color = mix(linear(104, 56, 30), linear(54, 32, 22), unit(n2))

    def cut(name):
        x0, y0, x1, y1 = signs[name]
        return (slice(y0, y1), slice(x0, x1))

    def inside(name):
        x0, y0, x1, y1 = signs[name]
        s = cut(name)
        return np.minimum(np.minimum(grid_u[s] - x0, x1 - grid_u[s]), np.minimum(grid_v[s] - y0, y1 - grid_v[s]))

    def smear(chipped, decay=0.965):
        out = np.zeros(chipped.shape)
        carry = np.zeros(chipped.shape[1])
        for index in range(chipped.shape[0] - 1, -1, -1):
            carry = np.maximum(chipped[index], carry * decay)
            out[index] = carry
        return out

    def enamel(name, ground, ink, border=None, chips=0.07, gloss=0.28, extra=None):
        s = cut(name)
        d = inside(name)
        m = mask[s] if extra is None else np.clip(mask[s] + extra, 0.0, 1.0)
        base = np.asarray(ground) * (0.9 + 0.14 * unit(n1[s]))[:, :, None]
        base = mix(base, base * 0.7 + 0.08, unit(n3[s]) * 0.35)
        color = mix(base, np.asarray(ink) * (0.88 + 0.12 * unit(n1[s]))[:, :, None], m)
        if border is not None:
            color = mix(color, np.asarray(ink), ((d > border[0]) & (d < border[0] + border[1])).astype(np.float64))
        chip_field = n2[s] * 0.6 + n1[s] * 0.55 + sstep(12.0, 0.0, d) * 1.5
        level = float(np.quantile(chip_field, 1.0 - chips))
        chipped = sstep(level, level + 0.12, chip_field)
        ring = np.clip(sstep(level - 0.14, level, chip_field) - chipped, 0.0, 1.0)
        stain = np.clip(smear(chipped) - chipped, 0.0, 1.0)
        color = mix(color, color * np.array([1.15, 0.72, 0.42]) + np.array([0.02, 0.008, 0.002]), stain * 0.55)
        color = mix(color, linear(18, 18, 22), ring * 0.75)
        color = mix(color, rust_color[s], chipped)
        albedo[s] = color
        rough[s] = mix(gloss + 0.15 * unit(n1[s]), 0.86, chipped)
        height[s] = -chipped * 0.0004

    def cast(name, ground, ink, rim=5.0, shape=None):
        s = cut(name)
        d = inside(name) if shape is None else shape
        raised = np.clip(np.maximum(mask[s], sstep(rim, rim - 1.5, d)), 0.0, 1.0)
        base = np.asarray(ground) * (0.85 + 0.25 * unit(n1[s]))[:, :, None]
        base = mix(base, rust_color[s], sstep(0.45, 0.9, unit(n2[s] + n1[s])) * 0.55)
        worn = raised * sstep(0.35, 0.8, unit(n2[s]))
        top = mix(np.asarray(ink) * (0.9 + 0.1 * unit(n1[s]))[:, :, None], rust_color[s] * 1.3, worn * 0.6)
        albedo[s] = mix(base, top, raised)
        rough[s] = 0.62 - 0.1 * raised
        height[s] = blur_patch(raised, 0.8) * 0.0022
        if shape is not None:
            outside = shape < 0.0
            albedo[s] = np.where(outside[:, :, None], linear(20, 20, 20), albedo[s])
            height[s] = np.where(outside, 0.0, height[s])

    def blur_patch(values, sigma):
        padded = np.pad(values, 4, mode="edge")
        radius = 3
        kernel = np.exp(-(np.arange(-radius, radius + 1) ** 2) / (2.0 * sigma * sigma))
        kernel /= kernel.sum()
        out = sum(kernel[k] * padded[:, k:k + padded.shape[1] - 2 * radius] for k in range(2 * radius + 1))
        out = sum(kernel[k] * out[k:k + out.shape[0] - 2 * radius, :] for k in range(2 * radius + 1))
        return out[1:-1, 1:-1]

    def paper(name, ground, ink, marks=None):
        s = cut(name)
        d = inside(name)
        m = np.clip(mask[s] + (marks if marks is not None else 0.0), 0.0, 1.0)
        base = np.asarray(ground) * (0.88 + 0.14 * unit(n1[s]))[:, :, None] * (1.0 + 0.04 * grain[s])[:, :, None]
        color = mix(base, np.asarray(ink), m * (0.75 + 0.2 * unit(n2[s])))
        stain_field = n3[s]
        level = float(np.quantile(stain_field, 0.72))
        color = mix(color, color * np.array([0.74, 0.6, 0.4]), sstep(level - 0.2, level + 0.3, stain_field) * 0.6)
        color = mix(color, color * 0.55, sstep(0.12, 0.0, np.abs(stain_field - level)) * 0.4)
        foxing = cover(grain[s] + 0.5 * n1[s], 0.05, 0.3)
        color = mix(color, linear(110, 78, 44), foxing * 0.5)
        color = mix(color, color * 0.6, sstep(5.0, 0.0, d) * 0.6)
        albedo[s] = color
        rough[s] = 0.9
        height[s] = -sstep(3.0, 0.0, d) * 0.0002

    def swatch(name, color, rough_value, metal_value=0.0, variation=0.1, wear=None):
        s = cut(name)
        albedo[s] = np.asarray(color) * (1.0 - variation * 0.5 + variation * unit(n2[s]))[:, :, None]
        if wear is not None:
            albedo[s] = mix(albedo[s], np.asarray(wear), sstep(0.62, 0.9, unit(n1[s] + n2[s] * 0.6)) * 0.7)
        rough[s] = rough_value + 0.08 * unit(n1[s])
        metal[s] = metal_value

    green = linear(36, 84, 56)
    white = linear(226, 222, 208)
    enamel("halt", green, white, (9.0, 5.0), 0.08)
    for name in ("waiting_room", "booking_office", "tickets", "private", "signal_box"):
        enamel(name, green, white, (4.0, 2.5), 0.06)
    cast("number", linear(22, 22, 22), linear(196, 170, 96))
    x0, y0, x1, y1 = signs["builder"]
    s = cut("builder")
    oval = (1.0 - np.hypot((grid_u[s] - (x0 + x1) * 0.5) / ((x1 - x0) * 0.5 - 2.0), (grid_v[s] - (y0 + y1) * 0.5) / ((y1 - y0) * 0.5 - 2.0))) * 30.0
    cast("builder", linear(104, 24, 20), linear(196, 160, 84), 4.0, oval)
    metal[s] = np.where(oval > 0.0, 0.0, 0.0)
    cast("wagon_a", linear(24, 24, 24), linear(214, 210, 198), 4.0)
    cast("wagon_b", linear(24, 24, 24), linear(214, 210, 198), 4.0)
    x0, y0, x1, y1 = signs["clock"]
    s = cut("clock")
    cu = grid_u[s] - (x0 + x1) * 0.5
    cv = grid_v[s] - (y0 + y1) * 0.5
    radius = np.hypot(cu, cv)
    theta = np.arctan2(cv, cu)
    minute = np.abs(((theta / tau * 60.0) + 0.5) % 1.0 - 0.5) * tau / 60.0 * radius
    hour = np.abs(((theta / tau * 12.0) + 0.5) % 1.0 - 0.5) * tau / 12.0 * radius
    ticks = ((minute < 0.9) & (radius > 106.0) & (radius < 113.0)) | ((hour < 2.2) & (radius > 102.0) & (radius < 113.0)) | ((radius > 114.5) & (radius < 116.5)) | ((radius > 99.0) & (radius < 100.2))

    def hand(angle, length, width, tail=12.0):
        ax = math.cos(angle)
        ay = math.sin(angle)
        along = cu * ax + cv * ay
        across = np.abs(-cu * ay + cv * ax)
        return (along > -tail) & (along < length) & (across < width * (1.0 - 0.5 * np.clip(along / length, 0.0, 1.0)))

    hands = hand(math.pi * 0.5 - tau * (4.0 + 17.0 / 60.0) / 12.0, 58.0, 4.5) | hand(math.pi * 0.5 - tau * 17.0 / 60.0, 92.0, 3.2) | (radius < 6.0)
    paper("clock", linear(232, 226, 206), linear(16, 16, 16), (ticks | hands).astype(np.float64))
    rough[s] = 0.35
    albedo[s] = np.where((radius > 120.0)[:, :, None], linear(18, 18, 18), albedo[s])
    enamel("beware", linear(168, 30, 24), white, (10.0, 5.0), 0.09)
    x0, y0, x1, y1 = signs["timetable"]
    s = cut("timetable")
    lu = grid_u[s] - x0
    lv = grid_v[s] - y0
    rng = np.random.default_rng(seed + 9)
    lines = np.zeros(lu.shape)
    for row in range(22):
        y = 196.0 - row * 8.2
        for column in (14.0, 96.0):
            for word in range(4):
                start = column + word * 17.0 + rng.uniform(0.0, 2.0)
                lines = np.maximum(lines, ((np.abs(lv - y) < 1.3) & (lu > start) & (lu < start + rng.uniform(7.0, 14.0))).astype(np.float64))
    lines = np.maximum(lines, ((np.abs(lv - 222.0) < 0.8) & (lu > 10.0) & (lu < 166.0)).astype(np.float64))
    lines = np.maximum(lines, ((np.abs(lu - 88.0) < 0.6) & (lv > 14.0) & (lv < 216.0)).astype(np.float64))
    paper("timetable", linear(214, 204, 172), linear(30, 28, 30), lines * 0.85)
    paper("notice", linear(220, 212, 184), linear(24, 22, 22))
    x0, y0, x1, y1 = signs["arm_front"]
    for name, ground, stripe in (("arm_front", linear(178, 30, 24), white), ("arm_back", white, linear(22, 22, 22))):
        s = cut(name)
        band = ((grid_u[s] - x0 > 62.0) & (grid_u[s] - x0 < 118.0)).astype(np.float64)
        enamel(name, ground, stripe, None, 0.1, 0.4, band)
    x0, y0, x1, y1 = signs["target"]
    s = cut("target")
    disc = (np.hypot(grid_u[s] - (x0 + x1) * 0.5, grid_v[s] - (y0 + y1) * 0.5) < 82.0).astype(np.float64)
    enamel("target", white, linear(178, 30, 24), None, 0.1, 0.4, disc)
    enamel("advert", linear(26, 46, 108), linear(232, 198, 70), (8.0, 4.0), 0.1)
    for number in range(6):
        name = "gauge_%d" % number
        x0, y0, x1, y1 = signs[name]
        s = cut(name)
        cu = grid_u[s] - (x0 + x1) * 0.5
        cv = grid_v[s] - (y0 + y1) * 0.5
        radius = np.hypot(cu, cv)
        theta = np.arctan2(cv, cu)
        sweep = (math.radians(225.0) - np.where(theta < -math.pi * 0.5, theta + tau, theta)) / math.radians(270.0)
        valid = (sweep > -0.01) & (sweep < 1.01)
        minor = np.abs(((sweep * 30.0) + 0.5) % 1.0 - 0.5) * math.radians(270.0) / 30.0 * radius
        major = np.abs(((sweep * 6.0) + 0.5) % 1.0 - 0.5) * math.radians(270.0) / 6.0 * radius
        ticks = valid & (((minor < 0.7) & (radius > 40.0) & (radius < 46.0)) | ((major < 1.3) & (radius > 35.0) & (radius < 46.0)))
        red_zone = valid & (sweep > 0.82) & (radius > 46.5) & (radius < 49.0)
        needle_angle = math.radians(225.0 - 270.0 * rng.uniform(0.0, 0.12))
        ax = math.cos(needle_angle)
        ay = math.sin(needle_angle)
        along = cu * ax + cv * ay
        across = np.abs(-cu * ay + cv * ax)
        needle = ((along > -8.0) & (along < 40.0) & (across < 1.4)) | (radius < 4.5)
        paper(name, linear(222, 214, 184), linear(14, 14, 14), (ticks | needle).astype(np.float64))
        albedo[s] = np.where(red_zone[:, :, None], linear(170, 30, 24), albedo[s])
        rough[s] = 0.3
        bezel = (radius > 52.0) & (radius < 61.0)
        albedo[s] = np.where(bezel[:, :, None], linear(176, 138, 66) * (0.8 + 0.3 * unit(n2[s]))[:, :, None], albedo[s])
        metal[s] = np.where(bezel, 1.0, 0.0)
        rough[s] = np.where(bezel, 0.4, rough[s])
        height[s] = np.where(bezel, 0.002, 0.0)
        albedo[s] = np.where((radius >= 61.0)[:, :, None], linear(20, 20, 20), albedo[s])
    enamel("fire", linear(176, 28, 22), white, (6.0, 2.5), 0.05, 0.35)
    paper("chain", linear(222, 212, 176), linear(150, 26, 22))
    for name in label_names:
        enamel(name, linear(20, 20, 20), linear(222, 220, 210), (4.0, 1.5), 0.03, 0.4)
    swatch("red", linear(168, 30, 24), 0.42, 0.0, 0.12, linear(74, 40, 26))
    swatch("signal_red", linear(190, 26, 20), 0.4, 0.0, 0.1, linear(86, 44, 28))
    swatch("yellow", linear(206, 164, 30), 0.45, 0.0, 0.12, linear(90, 56, 30))
    swatch("white", linear(226, 224, 214), 0.45, 0.0, 0.08, linear(96, 60, 36))
    swatch("black", linear(14, 14, 14), 0.3, 0.0, 0.2)
    swatch("brass", linear(188, 146, 68), 0.36, 1.0, 0.25, linear(70, 56, 30))
    swatch("copper", linear(186, 104, 66), 0.38, 1.0, 0.25, linear(60, 92, 76))
    swatch("lens_green", linear(14, 92, 60), 0.08, 0.0, 0.2)
    swatch("lens_red", linear(128, 10, 10), 0.08, 0.0, 0.2)
    swatch("lens_amber", linear(190, 108, 12), 0.08, 0.0, 0.2)
    swatch("lens_clear", linear(150, 156, 150), 0.08, 0.0, 0.2)
    swatch("cream", linear(214, 198, 152), 0.5, 0.0, 0.1, linear(96, 60, 36))
    swatch("blue", linear(30, 52, 116), 0.35, 0.0, 0.1, linear(86, 44, 28))
    swatch("steel", linear(150, 150, 152), 0.32, 1.0, 0.2, linear(84, 56, 40))
    swatch("grey", linear(70, 72, 72), 0.55, 0.0, 0.15, linear(80, 50, 32))
    swatch("leather", linear(70, 40, 24), 0.55, 0.0, 0.3)
    occlusion = 1.0 - 0.25 * cavity(height, 1.5, 0.0008)
    save_set("rail_signs", albedo, rough, occlusion, 1.0, height=height, strength=1.0, metal=metal)


def make_leather():
    seed = 6200
    maps = shuffled(scan("brown_leather", 1), seed, 0.5)
    albedo = maps["albedo"] * np.array([0.62, 0.55, 0.5])
    worn = cover(field(seed + 1, 2.0, 30.0, 2.0), 0.35, 0.5)
    albedo = mix(albedo, albedo * 1.5 + 0.015, worn * 0.5)
    crack = kit.cracks(seed + 2, 14, 0.9, 0.6)
    albedo = mix(albedo, linear(150, 130, 96), crack * worn * 0.8)
    grime = cover(field(seed + 3, 3.0, 60.0, 2.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * 0.5, grime * 0.5)
    rough = np.clip(maps["rough"] * 0.9 + 0.12 * worn + 0.1 * crack, 0.25, 1.0)
    save_set("leather_brown", albedo, rough, np.clip(0.7 + 0.3 * maps["ao"], 0.0, 1.0) - 0.3 * crack, 0.6, height=-crack * 0.0005, gradient=(maps["gx"], maps["gy"]))


def make_rust():
    seed = 5400
    out = rust_maps()
    albedo = out["albedo"]
    albedo = tint(albedo, 0.8 + 0.4 * unit(field(seed + 1, 2.0, 30.0, 2.0)))
    bloom = cover(field(seed + 2, 12.0, 300.0, 1.5), 0.18, 0.3)
    albedo = mix(albedo, linear(158, 92, 44) * (0.8 + 0.3 * unit(speckle(seed + 3, 1.0)))[:, :, None], bloom * 0.45)
    dark = cover(field(seed + 4, 5.0, 150.0, 1.7), 0.25, 0.4)
    albedo = mix(albedo, albedo * 0.5, dark * 0.6)
    flakes = field(seed + 5, 25.0, 500.0, 1.3)
    rough = np.clip(0.8 + 0.08 * unit(flakes) + 0.06 * bloom, 0.0, 1.0)
    occlusion = np.clip(0.75 + 0.25 * out["ao"], 0.0, 1.0) - 0.15 * cavity(flakes * 0.0004, 2.0, 0.0006)
    save_set("rust_iron", albedo, rough, occlusion, 1.0, height=flakes * 0.0003, gradient=(out["gx"] * 0.8, out["gy"] * 0.8))


painted_sets = {
    "painted_wood_white": (linear(226, 224, 214), linear(150, 148, 142), 1720),
    "painted_wood_bauxite": (linear(122, 58, 44), linear(140, 136, 128), 1740),
}


def make_painted(name):
    paint, primer, seed = painted_sets[name]
    kit.make_painted(name, paint, primer, seed)
    swatches[name] = kit.swatches[name]


makers = {
    "ballast_stone": make_ballast,
    "sleeper_timber": make_sleepers,
    "rail_steel": make_rail_steel,
    "rust_iron": make_rust,
    "loco_green": make_loco_green,
    "loco_black": make_loco_black,
    "wasp_stripes": make_wasp,
    "chequer_plate": make_chequer,
    "wagon_grey": make_wagon_grey,
    "coach_livery": make_coach_livery,
    "painted_wood_white": lambda: make_painted("painted_wood_white"),
    "painted_wood_bauxite": lambda: make_painted("painted_wood_bauxite"),
    "rail_signs": make_signs,
    "leather_brown": make_leather,
}

rail_catalog = {
    "ballast_stone": {"tile": 2.0, "kind": "world"},
    "sleeper_timber": {"tile": 1.0, "kind": "strips"},
    "rail_steel": {"tile": 1.5, "kind": "bands"},
    "rust_iron": {"tile": 1.0, "kind": "local"},
    "loco_green": {"tile": 2.0, "kind": "zoned"},
    "loco_black": {"tile": 2.0, "kind": "local"},
    "wasp_stripes": {"tile": 1.0, "kind": "local"},
    "chequer_plate": {"tile": 1.0, "kind": "local"},
    "wagon_grey": {"tile": 2.0, "kind": "zoned"},
    "coach_livery": {"tile": 2.0, "kind": "zoned"},
    "rail_signs": {"tile": 1.0, "kind": "atlas"},
    "leather_brown": {"tile": 0.6, "kind": "local"},
}


def register():
    kit.load_catalog()
    for name, entry in rail_catalog.items():
        kit.catalog.setdefault(name, entry)
    for name, (paint, primer, seed) in painted_sets.items():
        kit.catalog.setdefault(name, {"tile": 1.0, "kind": "boards", "boards": kit.board_layout(np.random.default_rng(seed), 1.0, 0.09, 0.16)})
    return kit.catalog


def build_library(names=None):
    register()
    for name, maker in makers.items():
        if not names or name in names:
            maker()
    write_sheet(os.path.join(preview_root, "library_railway.png"))
    print("RAIL LIBRARY DONE", len(swatches), "sets", flush=True)


class Build(kit.Build):
    def __init__(self, name, seed):
        super().__init__(name, seed)
        register()
        self.origins = {}
        self.shading = {}
        self.weighted = {}

    def part(self, key, sharp=35.0, weighted=None):
        if key not in self.parts:
            self.parts[key] = kit.Part(key, sharp)
            if weighted is not None:
                self.weighted[key] = weighted
        return self.parts[key]

    def origin(self, key, position):
        self.origins[key] = position

    def finish(self):
        objects = []
        marker = None
        for key, part in self.parts.items():
            if not part.faces:
                continue
            origin = self.origins.get(key)
            if origin is not None:
                part.points = [(x - origin.x, y - origin.y, z - origin.z) for x, y, z in part.points]
            obj = part.build()
            if key in self.weighted:
                soften(obj, self.weighted[key])
            if key in self.shading:
                shift = origin if origin is not None else V(0.0, 0.0, 0.0)
                obj.data.normals_split_custom_set_from_vertices([tuple(self.shading[key](vertex.co + shift)) for vertex in obj.data.vertices])
            if origin is not None:
                obj.location = origin
            objects.append(obj)
            if marker is None:
                marker = kit.material(part.slots[0])
        for name, lo, hi in self.boxes:
            objects.append(kit.box_object(name, lo, hi, marker))
        return objects


def soften(obj, weight=50):
    modifier = obj.modifiers.new("weighted", 'WEIGHTED_NORMAL')
    modifier.keep_sharp = True
    modifier.weight = weight
    modifier.mode = 'FACE_AREA'
    bpy.context.view_layer.update()
    final = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = obj.data
    name = old.name
    obj.modifiers.clear()
    obj.data = final
    bpy.data.meshes.remove(old)
    final.name = name


def outward(face, points, center):
    corners = [points[i] for i in face]
    middle = sum(corners, V(0.0, 0.0, 0.0)) / len(corners)
    if kit.newell(corners).dot(middle - center) < 0.0:
        return tuple(reversed(face)), True
    return face, False


def geo_prism(outline, y0, y1, segments=1, cap_start=True, cap_end=True):
    n = len(outline)
    area = kit.signed_area(outline)
    points = []
    for i in range(segments + 1):
        y = y0 + (y1 - y0) * i / segments
        points.extend(V(x, y, z) for x, z in outline)
    around = [0.0]
    for j in range(n):
        a = outline[j]
        b = outline[(j + 1) % n]
        around.append(around[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    faces = []
    uvs = []
    for i in range(segments):
        ya = y0 + (y1 - y0) * i / segments
        yb = y0 + (y1 - y0) * (i + 1) / segments
        for j in range(n):
            k = (j + 1) % n
            a = i * n + j
            b = i * n + k
            c = (i + 1) * n + k
            d = (i + 1) * n + j
            if area > 0.0:
                faces.append((a, d, c, b))
                uvs.append([(around[j], ya), (around[j], yb), (around[j + 1], yb), (around[j + 1], ya)])
            else:
                faces.append((a, b, c, d))
                uvs.append([(around[j], ya), (around[j + 1], ya), (around[j + 1], yb), (around[j], yb)])
    if cap_start or cap_end:
        triangles = geometry.tessellate_polygon([[V(x, z, 0.0) for x, z in outline]])
        for wanted, ring, direction in ((cap_start, 0, -1.0), (cap_end, segments, 1.0)):
            if not wanted:
                continue
            for triangle in triangles:
                face = kit.orient(tuple(ring * n + index for index in triangle), points, V(0.0, direction, 0.0))
                faces.append(face)
                uvs.append([(points[index].x, points[index].z) for index in face])
    return Geo(points, faces, uvs)


rail_half = [(0.070, 0.0), (0.070, 0.011), (0.030, 0.0205), (0.0145, 0.030), (0.0085, 0.043), (0.0085, 0.089), (0.0145, 0.099), (0.035, 0.1065), (0.035, 0.131), (0.0315, 0.1385), (0.022, 0.1415)]
rail_height = 0.1395
rail_scale = rail_height / 0.1425
rail_cant = math.atan(0.05)


def rail_outline():
    right = [(x, z * rail_scale) for x, z in rail_half]
    left = [(-x, z) for x, z in reversed(right)]
    return right + [(0.0, rail_height)] + left


def rail_geo(y0, y1, segments, gauge_right, band="bright", caps=(True, True), tile=1.5):
    outline = rail_outline()
    n = len(outline)
    geo = geo_prism(outline, y0, y1, segments, caps[0], caps[1])
    lengths = [math.hypot(outline[(j + 1) % n][0] - outline[j][0], outline[(j + 1) % n][1] - outline[j][1]) for j in range(n)]
    top_total = sum(lengths[8:14])
    side_total = sum(lengths[0:8])
    across = {}
    walked = 0.0
    for j in range(8, 15):
        across[j] = walked / top_total
        walked += lengths[j] if j < 14 else 0.0
    down_right = {}
    walked = 0.0
    for j in range(8, -1, -1):
        down_right[j] = walked / side_total
        walked += lengths[j - 1] if j > 0 else 0.0
    down_left = {}
    walked = 0.0
    for j in range(14, 23):
        down_left[j] = walked / side_total
        walked += lengths[j] if j < 22 else 0.0
    b0, b1 = rail_rows[band]
    s0, s1 = rail_rows["side"]
    c0, c1 = rail_rows["cap"]

    def band_v(j):
        a = across[j] if gauge_right else 1.0 - across[j]
        return (b0 + 2.0 + a * (b1 - b0 - 4.0)) / size

    def side_v(p):
        return (s0 + 2.0 + p * (s1 - s0 - 4.0)) / size

    uvs = []
    number = 0
    for i in range(segments):
        for j in range(n):
            k = j + 1
            if 8 <= j <= 13:
                va, vb = band_v(j), band_v(k)
            elif j < 8:
                va, vb = side_v(down_right[j]), side_v(down_right[k])
            elif j < 22:
                va, vb = side_v(down_left[j]), side_v(down_left[k])
            else:
                va, vb = (c0 + 4.0) / size, (c1 - 4.0) / size
            mapped = []
            for index in geo.faces[number]:
                ring = index // n
                column = index % n
                y = y0 + (y1 - y0) * ring / segments
                mapped.append((y / tile, va if column == j else vb))
            uvs.append(mapped)
            number += 1
    for face in geo.faces[number:]:
        uvs.append([(0.2 + geo.points[index].x * 2.0, (c0 + 6.0) / size + geo.points[index].z * 0.3) for index in face])
    geo.uvs = uvs
    return geo


def sleeper_geo(rng, strip, end_tiles, length=2.6, width=0.25, depth=0.13, wear=1.0, splits=(0.0, 0.0), flip=False):
    half = length * 0.5
    xs = [-half, -half + 0.025, -half + 0.12, -1.02, -0.7525, -0.48, -0.16, 0.16, 0.48, 0.7525, 1.02, half - 0.12, half - 0.025, half]
    wave_w = kit.wander(rng, 3)
    wave_t = kit.wander(rng, 3)
    wave_l = kit.wander(rng, 3)
    wave_r = kit.wander(rng, 3)
    groove_y = [rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06)]
    groove_d = [rng.uniform(0.012, 0.03), rng.uniform(0.012, 0.03)]
    points = []
    params = []
    count = 7
    for x in xs:
        edge = half - abs(x)
        tip = 1.0 if edge < 0.03 else 0.0
        w = width * 0.5 + (wave_w(x * 2.0) - 0.5) * 0.008 * wear - tip * 0.004 * (1.0 if edge < 0.01 else 0.5)
        zt = -0.005 * wear * wave_t(x * 2.5) - tip * 0.005 * (1.0 if edge < 0.01 else 0.4)
        cl = (0.009 + 0.015 * wave_l(x * 3.0) * wear) * (1.0 + 0.7 * tip)
        cr = (0.009 + 0.015 * wave_r(x * 3.0) * wear) * (1.0 + 0.7 * tip)
        end = 0 if x < 0.0 else 1
        reach = splits[end]
        g = groove_d[end] * max(0.0, 1.0 - edge / reach) if reach > 0.0 else 0.0
        gy = groove_y[end] + 0.015 * math.sin(edge * 28.0) if reach > 0.0 else 0.0
        section = [(-w, -depth), (-w, zt - cl), (-w + cl, zt), (gy, zt - g), (w - cr, zt), (w, zt - cr), (w, -depth)]
        points.extend(V(x, y, z) for y, z in section)
        params.append([(depth - cl) / width, 0.0, cl / width, min(max((gy + width * 0.5) / width, 0.12), 0.88), 1.0 - cr / width, 1.0, 1.0 - (depth - cr) / width])
    v0 = (strip * strip_rows + 1.5) / size
    v1 = ((strip + 1) * strip_rows - 1.5) / size
    center = V(0.0, 0.0, -depth * 0.5)
    faces = []
    uvs = []
    for i in range(len(xs) - 1):
        for j in range(count - 1):
            face = (i * count + j, i * count + j + 1, (i + 1) * count + j + 1, (i + 1) * count + j)
            face, flipped = outward(face, points, V((xs[i] + xs[i + 1]) * 0.5, 0.0, -depth * 0.5))
            mapped = []
            for index in face:
                section = index // count
                u = (xs[section] + half) / length
                a = params[section][index % count]
                mapped.append((1.0 - u if flip else u, v0 + a * (v1 - v0)))
            faces.append(face)
            uvs.append(mapped)
    for end, base in ((0, 0), (1, (len(xs) - 1) * count)):
        tile_index = end_tiles[end]
        column = tile_index % 4
        row = tile_index // 4
        u0 = column * 0.25 + 0.004
        u1 = (column + 1) * 0.25 - 0.004
        e0 = (strip_count * strip_rows + row * end_rows + 2.0) / size
        e1 = (strip_count * strip_rows + (row + 1) * end_rows - 2.0) / size
        for a, b in ((4, 5), (5, 6), (6, 0), (0, 1), (1, 2)):
            face = kit.orient((base + 3, base + a, base + b), points, V(-1.0 if end == 0 else 1.0, 0.0, 0.0))
            faces.append(face)
            uvs.append([(u0 + (points[index].y / width + 0.5) * (u1 - u0), e0 + (points[index].z / depth + 1.0) * (e1 - e0)) for index in face])
    return Geo(points, faces, uvs)


def stone_prototypes(rng, count=24):
    prototypes = []
    for number in range(count):
        bm = bmesh.new()
        verts = []
        sx = rng.uniform(0.75, 1.0)
        sy = rng.uniform(0.55, 0.9)
        sz = rng.uniform(0.4, 0.62)
        for cx in (-1.0, 1.0):
            for cy in (-1.0, 1.0):
                for cz in (-1.0, 1.0):
                    verts.append(bm.verts.new((cx * sx * rng.uniform(0.55, 1.0), cy * sy * rng.uniform(0.55, 1.0), cz * sz * rng.uniform(0.6, 1.0))))
        for index in range(rng.randint(1, 3)):
            direction = Vector((rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0), rng.gauss(0.0, 0.6))).normalized()
            verts.append(bm.verts.new((direction.x * sx * 1.05, direction.y * sy * 1.05, direction.z * sz * 1.05)))
        result = bmesh.ops.convex_hull(bm, input=verts)
        doomed = list({item for item in result.get("geom_interior", []) + result.get("geom_unused", []) if isinstance(item, bmesh.types.BMVert)})
        if doomed:
            bmesh.ops.delete(bm, geom=doomed, context='VERTS')
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.verts.index_update()
        lookup = {vert: index for index, vert in enumerate(bm.verts)}
        points = [vert.co.copy() for vert in bm.verts]
        faces = [tuple(lookup[vert] for vert in face.verts) for face in bm.faces]
        bm.free()
        prototypes.append(Geo(points, faces))
    return prototypes


def stone(part, prototypes, rng, position, radius, name="ballast_stone", scale=0.55):
    geo = rng.choice(prototypes)
    matrix = Matrix.Translation(position) @ Matrix.Rotation(rng.uniform(0.0, tau), 4, 'Z') @ Matrix.Rotation(rng.uniform(-0.35, 0.35), 4, 'X') @ Matrix.Rotation(rng.uniform(-0.35, 0.35), 4, 'Y')
    emit(part, Geo([p * radius for p in geo.points], geo.faces), name, matrix, "box", False, None, scale)


def square_profile(a, b):
    return [(-a * 0.5, -b * 0.5), (a * 0.5, -b * 0.5), (a * 0.5, b * 0.5), (-a * 0.5, b * 0.5)]


def prism_bolt(part, name, position, direction, across, height, sides=6, washer=0.0, stub=0.0, phase=0.0, hint=None):
    radius = across * 0.5 / math.cos(math.pi / sides)
    frame = frame_along(position, direction, hint)
    offset = 0.0
    if washer > 0.0:
        emit(part, kit.geo_lathe([(0.0, 0.0), (across * 0.78, 0.0), (across * 0.78, washer), (0.0, washer)], 10), name, frame, "given", True)
        offset = washer
    emit(part, kit.geo_lathe([(0.0, offset), (radius, offset), (radius, offset + height * 0.82), (radius * 0.8, offset + height), (0.0, offset + height)], sides, phase), name, frame, "given", False)
    if stub > 0.0:
        emit(part, kit.geo_lathe([(across * 0.3, offset + height), (across * 0.3, offset + height + stub), (0.0, offset + height + stub)], 8), name, frame, "given", True)


def frame_along(position, direction, hint=None):
    z_axis = direction.normalized()
    x_axis = z_axis.orthogonal().normalized()
    if hint is not None and (hint - z_axis * hint.dot(z_axis)).length > 1e-5:
        x_axis = (hint - z_axis * hint.dot(z_axis)).normalized()
    y_axis = z_axis.cross(x_axis)
    matrix = Matrix(((x_axis.x, y_axis.x, z_axis.x, position.x), (x_axis.y, y_axis.y, z_axis.y, position.y), (x_axis.z, y_axis.z, z_axis.z, position.z), (0.0, 0.0, 0.0, 1.0)))
    return matrix


grass_sprites = ((0.0, 0.1992, 0.4922, 0.5), (0.5176, 0.0601, 0.9829, 0.5), (0.0156, 0.6694, 0.4805, 1.0), (0.5254, 0.8477, 0.9624, 1.0))


def model_file(folder):
    directory = os.path.join(models_root, folder)
    return next(os.path.join(directory, entry) for entry in sorted(os.listdir(directory)) if entry.endswith(".gltf"))


def external_material(build, name, folder, index=0):
    path = model_file(folder)
    with open(path, "r", encoding="utf-8") as handle:
        source = json.load(handle)
    reference = source["materials"][index]["pbrMetallicRoughness"]["baseColorTexture"]["index"]
    uri = unquote(source["images"][source["textures"][reference]["source"]]["uri"])
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.use_backface_culling = False
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = kit.load_image(os.path.normpath(os.path.join(os.path.dirname(path), uri)), 'sRGB')
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    kit.material_cache[name] = material
    kit.catalog.setdefault(name, {"tile": 1.0, "kind": "external"})
    if not hasattr(build, "externals"):
        build.externals = {}
    build.externals[name] = (path, index)
    return material


def load_plants(folder, ratios):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=model_file(folder))
    created = [obj for obj in bpy.data.objects if obj not in before]
    result = {}
    for obj in created:
        if obj.type != 'MESH':
            continue
        short = obj.name.replace(folder + "_", "").replace("_LOD0", "")
        if short == obj.name:
            short = "whole"
        if short not in ratios:
            continue
        ratio = ratios[short]
        if ratio < 0.999:
            modifier = obj.modifiers.new("decimate", 'DECIMATE')
            modifier.ratio = ratio
        bpy.context.view_layer.update()
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        layer = mesh.uv_layers.active.data
        points = [vertex.co.copy() for vertex in mesh.vertices]
        faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
        uvs = [[tuple(layer[loop].uv) for loop in polygon.loop_indices] for polygon in mesh.polygons]
        result[short] = Geo(points, faces, uvs)
        bpy.data.meshes.remove(mesh)
    for obj in created:
        data = obj.data
        bpy.data.objects.remove(obj)
        if data is not None and data.users == 0 and isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
    return result


def triangles_of(geo):
    return sum(len(face) - 2 for face in geo.faces)


def grass_card(part, name, rng, position, width, sprite, cards=3, lean=0.18):
    u0, top, u1, bottom = grass_sprites[sprite]
    height = width * ((bottom - top) / (u1 - u0))
    start = rng.uniform(0.0, math.pi)
    for index in range(cards):
        angle = start + math.pi * index / cards + rng.uniform(-0.2, 0.2)
        along = V(math.cos(angle), math.sin(angle), 0.0)
        out = V(-along.y, along.x, 0.0)
        shift = out * rng.uniform(-0.04, 0.04) * width
        tilt = out * (lean * height * rng.uniform(-1.0, 1.0))
        base = position + shift
        points = [base - along * (width * 0.5), base + along * (width * 0.5), base + along * (width * 0.5) + V(0.0, 0.0, height) + tilt, base - along * (width * 0.5) + V(0.0, 0.0, height) + tilt]
        flip = rng.random() < 0.5
        ua, ub = (u1, u0) if flip else (u0, u1)
        emit(part, Geo(points, [(0, 1, 2, 3)], [[(ua, 1.0 - bottom), (ub, 1.0 - bottom), (ub, 1.0 - top), (ua, 1.0 - top)]]), name, None, "texture", True)


def fix_alpha(objects):
    seen = set()
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            material = slot.material
            if material is None or material.name in seen or not material.use_nodes:
                continue
            seen.add(material.name)
            tree = material.node_tree
            shader = next((node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
            if shader is None or not shader.inputs['Base Color'].links:
                continue
            if not material.use_backface_culling:
                geometry_node = tree.nodes.new('ShaderNodeNewGeometry')
                sign = tree.nodes.new('ShaderNodeMath')
                sign.operation = 'MULTIPLY_ADD'
                sign.inputs[1].default_value = -2.0
                sign.inputs[2].default_value = 1.0
                tree.links.new(geometry_node.outputs['Backfacing'], sign.inputs[0])
                turn = tree.nodes.new('ShaderNodeVectorMath')
                turn.operation = 'SCALE'
                tree.links.new(shader.inputs['Normal'].links[0].from_socket if shader.inputs['Normal'].links else geometry_node.outputs['Normal'], turn.inputs[0])
                tree.links.new(sign.outputs[0], turn.inputs['Scale'])
                tree.links.new(turn.outputs['Vector'], shader.inputs['Normal'])
            source = shader.inputs['Base Color'].links[0].from_node
            if source.type != 'TEX_IMAGE' or source.image is None:
                continue
            path = bpy.path.abspath(source.image.filepath)
            mask = path.replace("_diff_", "_alpha_")
            if "_diff_" not in path or not os.path.exists(mask):
                continue
            for link in list(shader.inputs['Alpha'].links):
                tree.links.remove(link)
            texture = tree.nodes.new('ShaderNodeTexImage')
            texture.image = kit.load_image(mask, 'Non-Color')
            if source.inputs['Vector'].links:
                tree.links.new(source.inputs['Vector'].links[0].from_socket, texture.inputs['Vector'])
            step = tree.nodes.new('ShaderNodeMath')
            step.operation = 'GREATER_THAN'
            step.inputs[1].default_value = 0.5
            tree.links.new(texture.outputs['Color'], step.inputs[0])
            tree.links.new(step.outputs[0], shader.inputs['Alpha'])


def apply_external(document, directory, material, template):
    source_path, source_index = template
    with open(source_path, "r", encoding="utf-8") as handle:
        source = json.load(handle)
    source_directory = os.path.dirname(source_path)
    if not document.get("samplers"):
        document["samplers"] = [{"magFilter": 9729, "minFilter": 9987}]

    def texture(reference):
        image = source["images"][source["textures"][reference["index"]]["source"]]
        absolute = os.path.normpath(os.path.join(source_directory, unquote(image["uri"])))
        uri = os.path.relpath(absolute, directory).replace("\\", "/")
        images = document.setdefault("images", [])
        found = next((number for number, existing in enumerate(images) if existing.get("uri") == uri), None)
        if found is None:
            images.append({"uri": uri, "mimeType": image.get("mimeType", "image/jpeg")})
            found = len(images) - 1
        textures = document.setdefault("textures", [])
        textures.append({"sampler": 0, "source": found})
        result = dict(reference)
        result["index"] = len(textures) - 1
        return result

    name = material["name"]
    copy = json.loads(json.dumps(source["materials"][source_index]))
    for key in ("normalTexture", "occlusionTexture", "emissiveTexture"):
        if key in copy:
            copy[key] = texture(copy[key])
    pbr = copy.get("pbrMetallicRoughness", {})
    for key in ("baseColorTexture", "metallicRoughnessTexture"):
        if key in pbr:
            pbr[key] = texture(pbr[key])
    material.clear()
    material.update(copy)
    material["name"] = name


def export_model(folder, objects, externals=None):
    path, document = kit.export_building(folder, objects)
    if externals:
        directory = os.path.dirname(path)
        for material in document.get("materials", []):
            template = externals.get(material.get("name"))
            if template is not None:
                apply_external(document, directory, material, template)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=1)
    return path, document


def audit(path, document, limit=None):
    directory = os.path.dirname(path)
    names = [node.get("name", "") for node in document.get("nodes", [])]
    problems = []
    if len(set(names)) != len(names):
        problems.append("duplicate node names")
    for name in names:
        if not name.isascii() or len(name) > 41 or "." in name:
            problems.append("bad name " + name)
    triangles = 0
    markers = {"col": 0, "ramp": 0, "loot": 0, "light": 0}
    accessors = document.get("accessors", [])
    low = [1e9, 1e9, 1e9]
    high = [-1e9, -1e9, -1e9]
    parts = {}
    for node in document.get("nodes", []):
        if "mesh" not in node:
            continue
        name = node.get("name", "")
        prefix = name.split("_")[0]
        mesh = document["meshes"][node["mesh"]]
        shift = node.get("translation", [0.0, 0.0, 0.0])
        count = 0
        for primitive in mesh["primitives"]:
            if "TEXCOORD_0" not in primitive["attributes"]:
                problems.append("no uv " + name)
            count += accessors[primitive["indices"]]["count"] // 3
            position = accessors[primitive["attributes"]["POSITION"]]
            if prefix not in markers:
                for axis in range(3):
                    low[axis] = min(low[axis], position["min"][axis] + shift[axis])
                    high[axis] = max(high[axis], position["max"][axis] + shift[axis])
        if prefix in markers:
            markers[prefix] += 1
        else:
            triangles += count
            parts[name] = count
        if "scale" in node or "rotation" in node:
            problems.append("transform on " + name)
    for image in document.get("images", []):
        uri = unquote(image.get("uri", ""))
        if not os.path.exists(os.path.normpath(os.path.join(directory, uri))):
            problems.append("missing image " + uri)
    stray = [entry for entry in os.listdir(directory) if entry.endswith(".png") and not any(image.get("uri", "") == entry for image in document.get("images", []))]
    if stray:
        problems.append("stray files " + ",".join(stray))
    if limit is not None and triangles > limit:
        problems.append("over budget %d > %d" % (triangles, limit))
    materials = [material.get("name") for material in document.get("materials", [])]
    blender_low = (round(low[0], 3), round(-high[2], 3), round(low[1], 3))
    blender_high = (round(high[0], 3), round(-low[2], 3), round(high[1], 3))
    print("AUDIT", os.path.basename(path), "tris", triangles, "markers", markers, "materials", len(materials), materials, "bounds", blender_low, blender_high, "problems", problems if problems else "none", flush=True)
    for name, count in parts.items():
        print("  PART", name, count, flush=True)
    return triangles, markers, materials, problems


def remap(geo, function):
    geo.uvs = [[function(u, w) for u, w in face_uv] for face_uv in geo.uvs]
    return geo


def planar(part, geo, name, origin, u_axis, v_axis, matrix=None, smooth=False, scale=1.0, offset=(0.0, 0.0), local=False):
    tile = kit.tile_of(name) / scale
    world = [matrix @ p for p in geo.points] if matrix is not None and not local else geo.points
    uvs = [[((world[i] - origin).dot(u_axis) / tile + offset[0], (world[i] - origin).dot(v_axis) / tile + offset[1]) for i in face] for face in geo.faces]
    emit(part, Geo(geo.points, geo.faces, uvs), name, matrix, "texture", smooth)


def away(geo, center):
    faces = []
    uvs = [] if geo.uvs is not None else None
    for number, face in enumerate(geo.faces):
        corners = [geo.points[i] for i in face]
        middle = sum(corners, V(0.0, 0.0, 0.0)) / len(corners)
        flip = kit.newell(corners).dot(middle - center) < 0.0
        faces.append(tuple(reversed(face)) if flip else face)
        if uvs is not None:
            uvs.append(list(reversed(geo.uvs[number])) if flip else geo.uvs[number])
    geo.faces = faces
    geo.uvs = uvs
    return geo


def facing(geo, direction):
    faces = []
    uvs = [] if geo.uvs is not None else None
    for number, face in enumerate(geo.faces):
        flip = kit.newell([geo.points[i] for i in face]).dot(direction) < 0.0
        faces.append(tuple(reversed(face)) if flip else face)
        if uvs is not None:
            uvs.append(list(reversed(geo.uvs[number])) if flip else geo.uvs[number])
    geo.faces = faces
    geo.uvs = uvs
    return geo


def geo_sheet(outline, y0, y1, segments=1):
    n = len(outline)
    points = []
    for i in range(segments + 1):
        y = y0 + (y1 - y0) * i / segments
        points.extend(V(x, y, z) for x, z in outline)
    along = [0.0]
    for j in range(1, n):
        along.append(along[-1] + math.hypot(outline[j][0] - outline[j - 1][0], outline[j][1] - outline[j - 1][1]))
    faces = []
    uvs = []
    for i in range(segments):
        ya = y0 + (y1 - y0) * i / segments
        yb = y0 + (y1 - y0) * (i + 1) / segments
        for j in range(n - 1):
            a = i * n + j
            faces.append((a, a + 1, a + n + 1, a + n))
            uvs.append([(along[j], ya), (along[j + 1], ya), (along[j + 1], yb), (along[j], yb)])
    return Geo(points, faces, uvs)


def arc_points(cx, cz, radius, a0, a1, steps):
    return [(cx + radius * math.cos(a0 + (a1 - a0) * s / steps), cz + radius * math.sin(a0 + (a1 - a0) * s / steps)) for s in range(steps + 1)]


def rounded_rect(x0, z0, x1, z1, radius, steps=4, corners=(True, True, True, True)):
    points = []
    for index, (cx, cz, start) in enumerate(((x1 - radius, z1 - radius, 0.0), (x0 + radius, z1 - radius, math.pi * 0.5), (x0 + radius, z0 + radius, math.pi), (x1 - radius, z0 + radius, math.pi * 1.5))):
        if corners[index] and radius > 0.0:
            points.extend(arc_points(cx, cz, radius, start, start + math.pi * 0.5, steps))
        else:
            points.append(((x1, z1), (x0, z1), (x0, z0), (x1, z0))[index])
    return points


def fillet_path(points, radius, steps=4):
    result = [points[0].copy()]
    for index in range(1, len(points) - 1):
        p = points[index]
        d1 = points[index - 1] - p
        d2 = points[index + 1] - p
        l1 = d1.length
        l2 = d2.length
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        d1 = d1 / l1
        d2 = d2 / l2
        cosine = max(-0.9999, min(0.9999, d1.dot(d2)))
        half = math.acos(cosine) * 0.5
        if half > math.pi * 0.5 - 0.02:
            result.append(p.copy())
            continue
        reach = min(radius / math.tan(half), l1 * 0.45, l2 * 0.45)
        r = reach * math.tan(half)
        start = p + d1 * reach
        end = p + d2 * reach
        center = p + (d1 + d2).normalized() * (r / math.sin(half))
        a = start - center
        c = end - center
        for s in range(steps + 1):
            t = s / steps
            blend = (a * (1.0 - t) + c * t)
            if blend.length < 1e-9:
                continue
            result.append(center + blend.normalized() * r)
    result.append(points[-1].copy())
    return result


def pipe(part, name, points, radius, sides=8, bend=0.0, caps=True, up=None):
    path = fillet_path(points, bend) if bend > 0.0 and len(points) > 2 else points
    emit(part, kit.geo_tube(path, kit.circle(radius, sides), caps, up), name, None, "given", True)


def bar(part, name, points, width, height, up=None, bend=0.0, caps=True, smooth=False):
    path = fillet_path(points, bend) if bend > 0.0 and len(points) > 2 else points
    emit(part, kit.geo_tube(path, square_profile(width, height), caps, up), name, None, "given", smooth)


def quad(part, name, corners, mapping="box", smooth=False, uv=None):
    geo = Geo(list(corners), [(0, 1, 2, 3)], [uv] if uv is not None else None)
    emit(part, geo, name, None, "texture" if uv is not None else mapping, smooth)


def atlas_quad(part, region, corners, turn=0, name="rail_signs"):
    u0, v0, u1, v1 = sign_uv(region)
    uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    uv = uv[turn:] + uv[:turn]
    quad(part, name, corners, "texture", False, uv)


def atlas_panel(part, region, center, normal, up, width, height, turn=0, name="rail_signs"):
    n = normal.normalized()
    upward = (up - n * up.dot(n)).normalized()
    right = upward.cross(n)
    corners = [center - right * (width * 0.5) - upward * (height * 0.5), center + right * (width * 0.5) - upward * (height * 0.5), center + right * (width * 0.5) + upward * (height * 0.5), center - right * (width * 0.5) + upward * (height * 0.5)]
    atlas_quad(part, region, corners, turn, name)


def atlas_disc(part, region, center, normal, up, radius, segments=20, name="rail_signs", inset=0.92):
    u0, v0, u1, v1 = sign_uv(region)
    n = normal.normalized()
    upward = (up - n * up.dot(n)).normalized()
    side = upward.cross(n)
    points = [center] + [center + (side * math.cos(tau * s / segments) + upward * math.sin(tau * s / segments)) * radius for s in range(segments)]
    mapped = [((u0 + u1) * 0.5, (v0 + v1) * 0.5)] + [((u0 + u1) * 0.5 + math.cos(tau * s / segments) * (u1 - u0) * 0.5 * inset, (v0 + v1) * 0.5 + math.sin(tau * s / segments) * (v1 - v0) * 0.5 * inset) for s in range(segments)]
    faces = []
    uvs = []
    for s in range(segments):
        t = (s + 1) % segments
        faces.append((0, 1 + s, 1 + t))
        uvs.append([mapped[0], mapped[1 + s], mapped[1 + t]])
    emit(part, facing(Geo(points, faces, uvs), n), name, None, "texture", False)


def swatch_geo(geo, region):
    u0, v0, u1, v1 = sign_uv(region, 6.0)
    if geo.uvs is None:
        geo.uvs = [[(p.x + p.z, p.y - p.z) for p in (geo.points[i] for i in face)] for face in geo.faces]
    lows_u = min(u for face in geo.uvs for u, w in face)
    highs_u = max(u for face in geo.uvs for u, w in face)
    lows_w = min(w for face in geo.uvs for u, w in face)
    highs_w = max(w for face in geo.uvs for u, w in face)
    span_u = max(highs_u - lows_u, 1e-6)
    span_w = max(highs_w - lows_w, 1e-6)
    geo.uvs = [[(u0 + (u1 - u0) * (u - lows_u) / span_u, v0 + (v1 - v0) * (w - lows_w) / span_w) for u, w in face] for face in geo.uvs]
    return geo


def swatch(part, geo, region, matrix=None, smooth=True):
    emit(part, swatch_geo(geo, region), "rail_signs", matrix, "texture", smooth)


def axis_matrix(position, axis, hint=None):
    return frame_along(position, axis, hint)


def turned_geo(profile, segments=16, phase=0.0):
    return kit.geo_lathe(profile, segments, phase)


def lathe(part, name, position, axis, profile, segments=16, smooth=True, hint=None, phase=0.0):
    emit(part, kit.geo_lathe(profile, segments, phase), name, frame_along(position, axis, hint), "given", smooth)


def rivet_geo(radius=0.009, height=None):
    h = height if height is not None else radius * 0.62
    return kit.geo_lathe([(radius, 0.0), (radius * 0.72, h * 0.7), (0.0, h)], 6)


rivet_cache = {}


def rivet(part, name, position, normal, radius=0.009):
    key = round(radius, 4)
    if key not in rivet_cache:
        rivet_cache[key] = rivet_geo(radius)
    emit(part, rivet_cache[key], name, frame_along(position, normal), "box", True)


def rivets(part, name, a, b, spacing, normal, radius=0.009, ends=True):
    length = (b - a).length
    count = max(1, int(round(length / spacing)))
    for index in range(count + 1):
        if not ends and index in (0, count):
            continue
        rivet(part, name, a.lerp(b, index / count), normal, radius)


def chain_link_geo(length, width, wire, sides=6, steps=5):
    r = width * 0.5 - wire
    straight = length * 0.5 - width * 0.5
    path = []
    for s in range(steps + 1):
        angle = math.pi * s / steps
        path.append(V(r * math.cos(angle), 0.0, straight + r * math.sin(angle)))
    for s in range(steps + 1):
        angle = math.pi + math.pi * s / steps
        path.append(V(r * math.cos(angle), 0.0, -straight + r * math.sin(angle)))
    points = []
    rings = []
    count = len(path)
    for index, center in enumerate(path):
        ahead = path[(index + 1) % count]
        behind = path[index - 1]
        tangent = (ahead - behind).normalized()
        normal = V(0.0, 1.0, 0.0)
        side = normal.cross(tangent).normalized()
        ring = []
        for s in range(sides):
            angle = tau * s / sides
            ring.append(len(points))
            points.append(center + side * (wire * math.cos(angle)) + normal * (wire * math.sin(angle)))
        rings.append(ring)
    faces = []
    uvs = []
    for index in range(count):
        following = (index + 1) % count
        for s in range(sides):
            t = (s + 1) % sides
            faces.append((rings[index][s], rings[index][t], rings[following][t], rings[following][s]))
            uvs.append([(s * wire, index * 0.02), ((s + 1) * wire, index * 0.02), ((s + 1) * wire, (index + 1) * 0.02), (s * wire, (index + 1) * 0.02)])
    return away_axis(Geo(points, faces, uvs), path)


def away_axis(geo, path):
    faces = []
    uvs = []
    for number, face in enumerate(geo.faces):
        corners = [geo.points[i] for i in face]
        middle = sum(corners, V(0.0, 0.0, 0.0)) / len(corners)
        nearest = min(path, key=lambda p: (p - middle).length_squared)
        flip = kit.newell(corners).dot(middle - nearest) < 0.0
        faces.append(tuple(reversed(face)) if flip else face)
        uvs.append(list(reversed(geo.uvs[number])) if flip else geo.uvs[number])
    geo.faces = faces
    geo.uvs = uvs
    return geo


link_cache = {}


def chain(part, name, points, link=0.11, width=0.05, wire=0.009, rng=None, sides=6, steps=4):
    key = (round(link, 4), round(width, 4), round(wire, 4), sides, steps)
    if key not in link_cache:
        link_cache[key] = chain_link_geo(link, width, wire, sides, steps)
    geo = link_cache[key]
    pitch = link - wire * 4.0
    carry = 0.0
    number = 0
    for index in range(len(points) - 1):
        a = points[index]
        b = points[index + 1]
        span = (b - a).length
        if span < 1e-6:
            continue
        direction = (b - a) / span
        position = carry
        while position < span:
            center = a + direction * position
            hint = direction.orthogonal().normalized()
            if abs(direction.z) < 0.9:
                hint = V(0.0, 0.0, 1.0).cross(direction).normalized()
            frame = frame_along(center, direction, hint)
            twist = Matrix.Rotation((math.pi * 0.5 if number % 2 else 0.0) + (rng.uniform(-0.25, 0.25) if rng is not None else 0.0), 4, 'Z')
            emit(part, geo, name, frame @ twist, "given", True)
            number += 1
            position += pitch
        carry = position - span
    return number


def sagging(a, b, sag, steps=8):
    return [a.lerp(b, s / steps) - V(0.0, 0.0, sag * math.sin(math.pi * s / steps)) for s in range(steps + 1)]


def leaf_spring(part, name, center, span, leaves=7, width=0.09, thickness=0.011, camber=0.07, axis=None, shackles=True):
    direction = (axis if axis is not None else V(0.0, 1.0, 0.0)).normalized()
    side = V(0.0, 0.0, 1.0).cross(direction).normalized()
    for leaf in range(leaves):
        reach = span * 0.5 * (1.0 - 0.78 * leaf / max(leaves - 1, 1))
        lift = -leaf * thickness
        path = []
        steps = 6
        for s in range(steps + 1):
            t = -1.0 + 2.0 * s / steps
            along = t * reach
            path.append(center + direction * along + V(0.0, 0.0, lift + camber * (along / (span * 0.5)) ** 2))
        emit(part, kit.geo_tube(path, square_profile(width, thickness * 0.92), True, V(0.0, 0.0, 1.0)), name, None, "given", False)
    block(part, name, center - side * (width * 0.5 + 0.008) - direction * 0.035 + V(0.0, 0.0, -leaves * thickness - 0.004), center + side * (width * 0.5 + 0.008) + direction * 0.035 + V(0.0, 0.0, thickness * 0.5 + 0.006), 0.003)
    ends = [center + direction * (span * 0.5 * sign) + V(0.0, 0.0, camber) for sign in (-1.0, 1.0)]
    if shackles:
        for end in ends:
            emit(part, kit.geo_tube([end - side * (width * 0.5 + 0.012), end + side * (width * 0.5 + 0.012)], kit.circle(0.016, 8), True, V(0.0, 0.0, 1.0)), name, None, "given", True)
    return ends


def lathe_uv(profile, segments, v_values, repeats, phase=0.0):
    points = []
    rings = []
    for r, z in profile:
        ring = []
        for s in range(segments):
            angle = phase + tau * s / segments
            ring.append(len(points))
            points.append(V(r * math.cos(angle), r * math.sin(angle), z))
        rings.append(ring)
    faces = []
    uvs = []
    for index in range(len(profile) - 1):
        for s in range(segments):
            t = (s + 1) % segments
            faces.append((rings[index][s], rings[index][t], rings[index + 1][t], rings[index + 1][s]))
            ua = repeats * s / segments
            ub = repeats * (s + 1) / segments
            uvs.append([(ua, v_values[index]), (ub, v_values[index]), (ub, v_values[index + 1]), (ua, v_values[index + 1])])
    return Geo(points, faces, uvs)


def wheelset(b, key, y, radius, spokes=10, body="loco_black", balance=False, disc=False, back=0.68, axle_radius=0.075, hub_radius=0.12, hub_out=0.05, segments=48, journal=0.0):
    part = b.part(key, 40.0)
    b.origin(key, V(0.0, y, radius))
    rim = radius - 0.07
    b0, b1 = rail_rows["bright"]
    tread = [(radius + 0.028, 0.0), (radius + 0.028, 0.012), (radius + 0.004, 0.032), (radius, 0.040), (radius - 0.0043, 0.125), (radius - 0.010, 0.135)]
    tread_v = [(b0 + 2.0 + (a / 0.135) * (b1 - b0 - 4.0)) / size for r, a in tread]
    rng = b.rng
    for side in (-1.0, 1.0):
        turn = rng.uniform(0.0, tau)
        matrix = Matrix.Translation(V(side * back, y, radius)) @ Matrix.Rotation(side * math.pi * 0.5, 4, 'Y') @ Matrix.Rotation(turn, 4, 'Z')
        emit(part, lathe_uv(tread, segments, tread_v, 2.0), "rail_steel", matrix, "texture", True)
        emit(part, kit.geo_lathe([(radius - 0.010, 0.135), (rim, 0.135), (rim, 0.0), (radius + 0.028, 0.0)], segments), body, matrix, "given", True)
        emit(part, kit.geo_lathe([(0.0, -0.02), (hub_radius, -0.02), (hub_radius, 0.135 + hub_out), (hub_radius * 0.62, 0.135 + hub_out + 0.012), (hub_radius * 0.62, 0.135 + hub_out + 0.03), (0.0, 0.135 + hub_out + 0.03)], 28), body, matrix, "given", True)
        if disc:
            emit(part, kit.geo_lathe([(rim, 0.075), (rim - 0.04, 0.06), (hub_radius + 0.06, 0.085), (hub_radius, 0.10)], segments // 2), body, matrix, "given", True)
            emit(part, kit.geo_lathe([(hub_radius, 0.07), (hub_radius + 0.06, 0.055), (rim - 0.04, 0.035), (rim, 0.045)], segments // 2), body, matrix, "given", True)
        else:
            for spoke in range(spokes):
                angle = tau * spoke / spokes
                out = V(math.cos(angle), math.sin(angle), 0.0)
                path = [out * (hub_radius - 0.01) + V(0.0, 0.0, 0.07), out * (rim + 0.004) + V(0.0, 0.0, 0.066)]
                emit(part, kit.geo_tube(path, ellipse(0.034, 0.026, 8), False, V(0.0, 0.0, 1.0), [1.0, 0.72]), body, matrix, "given", True)
            if balance:
                outline = [(math.cos(-0.62 + 1.24 * s / 8) * (rim - 0.002), math.sin(-0.62 + 1.24 * s / 8) * (rim - 0.002)) for s in range(9)]
                outline += [(math.cos(0.62 - 1.24 * s / 4) * rim * 0.62, math.sin(0.62 - 1.24 * s / 4) * rim * 0.62) for s in range(5)]
                emit(part, kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), outline, [], 0.035, 0.1), body, matrix, "box", False)
    reach = max(back - 0.02, journal)
    emit(part, kit.geo_lathe([(axle_radius, -reach), (axle_radius, reach)], 12), body, Matrix.Translation(V(0.0, y, radius)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)
    return part


def ellipse(a, b, sides):
    return [(a * math.cos(tau * s / sides), b * math.sin(tau * s / sides)) for s in range(sides)]


def buffer(part, base, direction, body="loco_black", head="rust_iron", stock=0.26, length=0.5, oval=1.0):
    forward = direction.normalized()
    frame = frame_along(base, forward, V(1.0, 0.0, 0.0))
    emit(part, kit.geo_cbox(0.3, 0.3, 0.025, 0.006), body, frame @ Matrix.Translation(V(0.0, 0.0, 0.0125)), "box", False)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            prism_bolt(part, head, frame @ V(sx * 0.115, sy * 0.115, 0.025), forward, 0.032, 0.016, 6)
    emit(part, kit.geo_lathe([(0.118, 0.025), (0.112, 0.06), (0.092, stock), (0.1, stock), (0.1, stock + 0.03), (0.06, stock + 0.03)], 20), body, frame, "given", True)
    emit(part, kit.geo_lathe([(0.056, stock + 0.03), (0.056, length - 0.05)], 14), head, frame, "given", True)
    face = kit.geo_lathe([(0.06, length - 0.06), (0.19, length - 0.032), (0.19, length - 0.012), (0.13, length - 0.003), (0.0, length)], 24)
    if oval != 1.0:
        face = Geo([V(p.x * oval, p.y, p.z) for p in face.points], face.faces, face.uvs)
    emit(part, face, head, frame, "given", True)


hook_outline = [(0.0, -0.045), (0.14, -0.05), (0.2, -0.075), (0.265, -0.06), (0.30, -0.015), (0.30, 0.045), (0.275, 0.085), (0.245, 0.095), (0.235, 0.07), (0.25, 0.04), (0.25, 0.0), (0.225, -0.02), (0.19, -0.015), (0.175, 0.02), (0.15, 0.045), (0.0, 0.045)]


def drawgear(part, base, direction, rng, body="loco_black", iron="rust_iron", links=3):
    forward = direction.normalized()
    side = V(0.0, 0.0, 1.0).cross(forward).normalized()
    matrix = Matrix((tuple((forward.x, side.x, 0.0, base.x)), (forward.y, side.y, 0.0, base.y), (0.0, 0.0, 1.0, base.z), (0.0, 0.0, 0.0, 1.0)))
    emit(part, geo_prism(hook_outline, -0.025, 0.025, 1), iron, matrix, "given", False)
    emit(part, kit.geo_cbox(0.02, 0.24, 0.3, 0.005), body, matrix @ Matrix.Translation(V(0.01, 0.0, 0.0)), "box", False)
    for sy in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            prism_bolt(part, iron, matrix @ V(0.02, sy * 0.085, sz * 0.11), forward, 0.03, 0.015, 6)
    top = matrix @ V(0.21, 0.0, -0.02)
    points = [top]
    for index in range(links):
        points.append(points[-1] + V(rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012), -0.204))
    link = chain_link_geo(0.28, 0.13, 0.019, 8, 6)
    for index in range(links):
        center = (points[index] + points[index + 1]) * 0.5
        down = (points[index + 1] - points[index]).normalized()
        hint = side if index % 2 == 0 else forward
        emit(part, link, iron, frame_along(center, down, hint) @ Matrix.Rotation(rng.uniform(-0.15, 0.15), 4, 'Z'), "given", True)
    return points[-1]


def louvres(part, name, origin, along, up, normal, width, count, pitch, depth=0.014, inset=0.03):
    for index in range(count):
        base = origin + up * (index * pitch)
        a = base + along * inset
        c = base + along * (width - inset)
        top_a = a + up * (pitch * 0.82)
        top_c = c + up * (pitch * 0.82)
        out_a = a + normal * depth + up * (pitch * 0.12)
        out_c = c + normal * depth + up * (pitch * 0.12)
        points = [top_a, top_c, out_c, out_a, a, c]
        faces = [(0, 3, 2, 1), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5)]
        emit(part, facing_outward(Geo(points, faces), (a + c) * 0.5 + up * (pitch * 0.4) - normal * 0.05), name, None, "box", False)


def facing_outward(geo, center):
    geo.faces = [outward(face, geo.points, center)[0] for face in geo.faces]
    return geo


def prism_x(outline_yz, x0, x1, segments=1, cap_start=True, cap_end=True):
    geo = geo_prism([(-y, z) for y, z in outline_yz], x0, x1, segments, cap_start, cap_end)
    turn = Matrix.Rotation(-math.pi * 0.5, 4, 'Z')
    geo.points = [turn @ p for p in geo.points]
    return geo


def zoned(part, geo, name, base, matrix=None, smooth=False, shift=0.0):
    emit(part, geo, name, matrix, "world", smooth, (shift, -base / kit.tile_of(name)))


def steps_unit(b, part, side, y0, y1, tops, outs, inner=1.3, plate=1.26, tread="chequer_plate", iron="loco_black", surface="metal", tag="step"):
    profile = [(inner, plate), (inner + 0.13, plate), (outs[0] + 0.025, tops[0] + 0.08), (outs[0] + 0.025, tops[0] - 0.05), (outs[0] - 0.1, tops[0] - 0.05)]
    outline = [(side * x, z) for x, z in profile]
    for y in (y0, y1 - 0.012):
        emit(part, geo_prism(outline, y, y + 0.012, 1), iron, None, "given", False)
    previous = tops[0] - 0.5
    for top, out in zip(tops, outs):
        x_low, x_high = sorted((side * max(inner, out - 0.27), side * out))
        slab(part, V(x_low, y0 + 0.012, top - 0.012), V(x_high, y1 - 0.012, top), tread, iron, True, V(0.0, y0, 0.0))
        lip_a, lip_b = sorted((side * (out - 0.012), side * out))
        block(part, iron, V(lip_a, y0 + 0.012, top - 0.035), V(lip_b, y1 - 0.012, top - 0.012))
        col_low, col_high = sorted((side * inner, side * out))
        b.col(surface, tag, V(col_low, y0, max(previous, tops[0] - 0.4)), V(col_high, y1, top))
        previous = top


def planar_uv(geo, name, origin, u_axis, v_axis, scale=1.0, offset=(0.0, 0.0)):
    tile = kit.tile_of(name) / scale
    uvs = [[((geo.points[i] - origin).dot(u_axis) / tile + offset[0], (geo.points[i] - origin).dot(v_axis) / tile + offset[1]) for i in face] for face in geo.faces]
    return Geo(geo.points, geo.faces, uvs)


def inside_box(part, name, low, high, skip=(), mapping="box"):
    size3 = high - low
    geo = kit.geo_box(size3.x, size3.y, size3.z, skip)
    geo.faces = [tuple(reversed(face)) for face in geo.faces]
    emit(part, geo, name, Matrix.Translation((low + high) * 0.5), mapping)


def handrail(part, name, points, radius=0.014, stand=None, knob=0.022, bend=0.04, sides=8):
    pipe(part, name, points, radius, sides, bend)
    if stand is not None:
        for position, direction in stand:
            foot = position - direction
            emit(part, kit.geo_tube([foot, position], kit.circle(radius * 0.85, 6), False), name, None, "given", True)
            emit(part, kit.geo_lathe([(0.0, -knob), (knob * 0.8, -knob * 0.6), (knob, 0.0), (knob * 0.8, knob * 0.6), (0.0, knob)], 8), name, frame_along(position, direction), "given", True)
            emit(part, kit.geo_lathe([(knob * 1.3, 0.0), (knob * 1.3, 0.006), (radius, 0.012)], 8), name, frame_along(foot, direction), "given", True)


def slab(part, low, high, top, side, bottom=True, top_origin=None, scale=1.0):
    lo = V(min(low.x, high.x), min(low.y, high.y), min(low.z, high.z))
    hi = V(max(low.x, high.x), max(low.y, high.y), max(low.z, high.z))
    points = [V(lo.x, lo.y, hi.z), V(hi.x, lo.y, hi.z), V(hi.x, hi.y, hi.z), V(lo.x, hi.y, hi.z)]
    planar(part, Geo(points, [(0, 1, 2, 3)]), top, top_origin if top_origin is not None else V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), None, False, scale)
    block(part, side, lo, hi, 0.0, "box", None, ("top",) if bottom else ("top", "bottom"))

