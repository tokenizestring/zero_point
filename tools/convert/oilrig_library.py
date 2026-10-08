import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import town_library as tl
from buildkit import linear, field, unit, sstep, cover, patchy, blur, speckle, mix, tint, flat, cavity

size = kit.size
grid_u = kit.grid_u
grid_v = kit.grid_v
tau = math.pi * 2.0
library_root = kit.library_root
preview_root = os.path.join(kit.root, "assets", "previews", "oilrig")

rig_catalog = {
    "rig_paint_white": {"tile": 2.0, "kind": "local"},
    "rig_paint_orange": {"tile": 2.0, "kind": "local"},
    "rig_paint_yellow": {"tile": 1.0, "kind": "local"},
    "rig_paint_grey": {"tile": 2.0, "kind": "local"},
    "rig_deck_green": {"tile": 4.0, "kind": "world"},
    "rig_rust": {"tile": 2.0, "kind": "local"},
    "rig_marine": {"tile": 1.2, "kind": "local"},
    "rig_grating": {"tile": 1.0, "kind": "world"},
    "rig_net": {"tile": 0.6, "kind": "local"},
    "rig_decals": {"tile": 1.0, "kind": "atlas"},
    "rig_signs": {"tile": 1.0, "kind": "atlas"},
    "rig_lifeboat": {"tile": 2.0, "kind": "local"},
    "rig_rubber": {"tile": 1.0, "kind": "local"},
    "rig_wall": {"tile": 2.4, "kind": "world"},
    "rig_ceiling": {"tile": 1.2, "kind": "world"},
    "rig_vinyl": {"tile": 2.0, "kind": "world"},
    "rig_steel": {"tile": 1.0, "kind": "local"},
    "rig_mark_white": {"tile": 2.0, "kind": "world"},
    "rig_cardboard": {"tile": 0.6, "kind": "local"},
}
alpha_sets = {"rig_grating", "rig_net", "rig_decals"}
glow_sets = {"rig_lamp_warm": ((1.0, 0.72, 0.42), 2.2), "rig_lamp_cold": ((0.78, 0.9, 1.0), 2.6), "rig_lamp_green": ((0.3, 1.0, 0.42), 2.0), "rig_screen": ((0.35, 0.75, 0.5), 0.6)}
glow_bases = {"rig_lamp_warm": "glass_dirty", "rig_lamp_cold": "glass_dirty", "rig_lamp_green": "glass_dirty", "rig_screen": "rig_signs"}

signs = {
    "name_board": (0, 896, 1024, 1024),
    "muster": (0, 800, 512, 896),
    "lifeboat_1": (512, 800, 768, 896),
    "lifeboat_2": (768, 800, 1024, 896),
    "no_smoking": (0, 704, 256, 800),
    "h2s": (256, 704, 512, 800),
    "fire_point": (512, 704, 768, 800),
    "escape": (768, 704, 1024, 800),
    "control_room": (0, 640, 256, 704),
    "radio_room": (256, 640, 512, 704),
    "medical": (512, 640, 768, 704),
    "galley": (768, 640, 1024, 704),
    "mess": (0, 576, 256, 640),
    "lockers": (256, 576, 512, 640),
    "office": (512, 576, 768, 640),
    "workshop": (768, 576, 1024, 640),
    "stores": (0, 480, 384, 576),
    "helideck": (384, 480, 768, 576),
    "cellar_level": (768, 528, 1024, 576),
    "main_level": (768, 480, 1024, 528),
    "console": (0, 224, 512, 480),
    "mimic": (512, 224, 1024, 480),
    "screen_a": (0, 64, 256, 224),
    "screen_b": (256, 64, 512, 224),
    "esd": (512, 64, 768, 224),
    "leg_a1": (768, 160, 896, 224),
    "leg_a2": (896, 160, 1024, 224),
    "leg_b1": (768, 96, 896, 160),
    "leg_b2": (896, 96, 1024, 160),
    "radio_face": (768, 0, 1024, 96),
    "chart": (0, 0, 384, 64),
    "danger": (384, 0, 768, 64),
}

decals = {
    "run_a": (0, 512, 128, 1024),
    "run_b": (128, 512, 256, 1024),
    "run_c": (256, 512, 384, 1024),
    "run_d": (384, 512, 512, 1024),
    "runs_wide": (512, 768, 1024, 1024),
    "guano_a": (512, 512, 768, 768),
    "guano_b": (768, 512, 1024, 768),
    "scorch": (0, 0, 512, 512),
    "oil_a": (512, 256, 768, 512),
    "oil_b": (768, 256, 1024, 512),
    "salt": (512, 0, 768, 256),
    "guano_runs": (768, 0, 1024, 256),
}


def register():
    kit.load_catalog()
    tl.register()
    rk.register()
    for name, entry in rig_catalog.items():
        kit.catalog[name] = entry
    for name in alpha_sets:
        kit.double_sided.add(name)
    for name, base in glow_bases.items():
        kit.hero(name, os.path.join(library_root, base + "_albedo.png"), base)
    return kit.catalog


def region_uv(table, key, margin=1.5):
    x0, y0, x1, y1 = table[key]
    return ((x0 + margin) / size, (x1 - margin) / size, (y0 + margin) / size, (y1 - margin) / size)


def save(name, albedo, rough, occlusion, height=None, gradient=None, strength=1.0, metal=None, alpha=None, texel=None):
    rk.save_set(name, albedo, rough, occlusion, rig_catalog[name]["tile"], height, gradient, strength, metal, alpha, texel)


def rust_layer(seed, repeat=2):
    return rk.shuffled(rk.resampled(rk.rust_maps(), repeat), seed, 0.5)


def streaks(seed, count, length=(0.15, 0.6), width=(2.0, 7.0)):
    rng = np.random.default_rng(seed)
    stain = np.zeros((size, size))
    for number in range(count):
        cu = rng.uniform(0.0, size)
        top = rng.uniform(0.0, size)
        span = rng.uniform(length[0], length[1]) * size
        w = rng.uniform(width[0], width[1])
        rows = np.arange(int(top - span), int(top) + int(w) + 3)
        cols = np.arange(int(cu - 6.0 * w), int(cu + 6.0 * w) + 1)
        lv, lu = np.meshgrid(rows + 0.5, cols + 0.5, indexing="ij")
        down = (top - lv) / span
        wobble = w * 0.5 * np.sin(down * rng.uniform(4.0, 12.0) + rng.uniform(0.0, tau)) + w * 0.8 * np.sin(down * rng.uniform(1.0, 3.0) + rng.uniform(0.0, tau))
        spread = w * (0.6 + 1.1 * np.sqrt(np.clip(down, 0.0, 1.0)))
        value = np.exp(-((lu - cu - wobble) / spread) ** 2) * np.clip(1.0 - down, 0.0, 1.0) ** 1.2 * (down > -0.01) * rng.uniform(0.45, 1.0)
        value *= sstep(-0.02, 0.03, down)
        where = np.ix_(rows % size, cols % size)
        stain[where] = np.maximum(stain[where], value)
    return stain


def blisters(seed, fraction, radius):
    spots = cover(speckle(seed, radius), fraction, 0.15)
    halo = np.clip(blur(spots, radius * 2.2) * 2.4 - spots, 0.0, 1.0)
    return spots, halo


def drip(source, seed, low=0.975, high=0.996, thin=0.4):
    decay = low + (high - low) * unit(field(seed, 6.0, 300.0, 1.3)[size // 3])
    sway = np.round(3.0 * field(seed + 1, 2.0, 30.0, 2.0)[:, size // 5]).astype(np.int64)
    carry = np.zeros(size)
    out = np.zeros((size, size))
    for repeat in range(2):
        for row in range(size - 1, -1, -1):
            carry = np.maximum(source[row], carry * decay)
            if repeat:
                out[row] = np.roll(carry, sway[row])
    trickle = cover(field(seed + 2, 8.0, 300.0, 1.3, 1.0, 10.0), thin, 0.45)
    wash = blur(out, 1.6)
    return np.clip(wash * (0.55 + 0.45 * trickle), 0.0, 1.0)


def marine(seed, tile, coat, primer, rough_paint, scan=None, bare_amount=0.06, blister_amount=0.03, streak_count=40, streak_strength=0.8, chalk=0.35, salt=0.3, grime=0.3, rust_repeat=2):
    rust = rust_layer(seed + 90, rust_repeat)
    n = field(seed + 1, 3.0, 60.0, 1.8)
    fine = field(seed + 2, 20.0, 300.0, 1.4)
    flake_field = n + 0.55 * fine + 0.35 * field(seed + 3, 60.0, 500.0, 1.2)
    under = cover(flake_field, bare_amount * 1.7, 0.02)
    bare = cover(flake_field, bare_amount, 0.02)
    if scan is not None:
        keep = cover(field(seed + 13, 1.2, 8.0, 2.3), 0.4, 0.5)
        peeled = scan["bare"] * keep
        bare = np.maximum(bare, peeled)
        under = np.maximum(under, np.clip(blur(peeled, 1.4) * 2.2, 0.0, 1.0))
    spots, halo = blisters(seed + 4, blister_amount, 1.3)
    bare = np.maximum(bare, spots)
    big = sstep(0.2, 0.55, blur(bare, 4.0))
    chosen = spots * cover(field(seed + 9, 4.0, 200.0, 1.5), 0.3, 0.2)
    source = np.clip(big + chosen * 0.7, 0.0, 1.0)
    run = drip(source, seed + 5, 0.975 if streak_count else 0.0, 0.995 if streak_count else 0.0, 0.5) * (1.0 - bare) * 0.85
    run = np.clip(run + streaks(seed + 10, streak_count // 4, (0.15, 0.5), (2.5, 6.0)) * 0.45 + halo * 0.5, 0.0, 1.0)
    albedo = coat.copy()
    lum = rk.luminance(albedo)[:, :, None]
    fade = cover(field(seed + 6, 1.2, 9.0, 2.2), 0.45, 0.6)
    albedo = mix(albedo, albedo * 0.7 + lum * 0.45 + 0.03, fade * chalk)
    blotch = unit(field(seed + 14, 1.0, 6.0, 2.4))
    albedo = albedo * (0.8 + 0.28 * blotch)[:, :, None]
    film = cover(field(seed + 15, 1.5, 30.0, 2.0) + 0.5 * field(seed + 16, 10.0, 200.0, 1.6), 0.45, 0.6)
    albedo = mix(albedo, albedo * np.array([0.78, 0.74, 0.64]), film * grime)
    dirt = cover(field(seed + 7, 2.0, 120.0, 1.7, 1.0, 6.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * np.array([0.68, 0.68, 0.64]), dirt * grime)
    albedo = mix(albedo, primer * (0.85 + 0.25 * unit(fine))[:, :, None], under * (1.0 - bare))
    edge = np.clip(under * (1.0 - under) * 4.0, 0.0, 1.0)
    albedo = mix(albedo, albedo * 0.72, edge * 0.45)
    stain_color = albedo * np.array([0.6, 0.33, 0.16]) + np.array([0.07, 0.022, 0.005])
    albedo = mix(albedo, stain_color, np.clip(np.sqrt(run) * streak_strength, 0.0, 1.0))
    patch = rust["albedo"] * (1.05 + 0.4 * unit(fine))[:, :, None]
    patch = mix(patch, linear(150, 78, 34) * (0.8 + 0.3 * unit(speckle(seed + 11, 1.0)))[:, :, None], cover(field(seed + 12, 6.0, 200.0, 1.6), 0.35, 0.3) * 0.5)
    albedo = mix(albedo, patch, bare)
    crust = cover(field(seed + 8, 4.0, 200.0, 1.6, 1.0, 3.0) + 0.8 * run, salt * 0.4, 0.3) * (1.0 - bare)
    albedo = mix(albedo, linear(214, 210, 198), crust * 0.35 * salt)
    rough = mix(np.clip(rough_paint + 0.15 * fade * chalk + 0.08 * dirt, 0.0, 1.0), 0.72, under)
    rough = mix(rough, np.maximum(rust["rough"], 0.8), bare)
    rough = mix(rough, 0.8, np.clip(run * 0.6 + crust * 0.5, 0.0, 1.0))
    metal = np.zeros((size, size))
    lip = np.clip(blur(under, 1.0) - under, 0.0, 1.0)
    height = -under * 0.0003 - bare * 0.0004 + lip * 0.0005 + spots * 0.0006 + halo * 0.0002 + n * 0.00012 + run * 0.00008
    gx, gy = rk.gradient_of(height, tile / size)
    gx = gx * (1.0 - bare) + rust["gx"] * bare * 0.9
    gy = gy * (1.0 - bare) + rust["gy"] * bare * 0.9
    occlusion = mix(np.ones((size, size)), np.clip(0.72 + 0.28 * rust["ao"], 0.0, 1.0), bare) - 0.25 * cavity(height, 1.5, 0.0004)
    return albedo, rough, metal, occlusion, (gx, gy), bare, run


def painted_scan(name, seed, acg=True):
    maps = rk.shuffled(rk.scan_acg(name) if acg else rk.scan(name), seed, 0.5)
    rgb = maps["albedo"]
    lum = rk.luminance(rgb)
    ratio = rgb[:, :, 0] / (rgb[:, :, 2] + 0.01)
    rusty = sstep(1.25, 1.8, ratio) * sstep(0.01, 0.04, lum)
    bare = np.clip(np.maximum(rusty, sstep(0.45, 0.3, lum) * sstep(0.2, 0.45, maps["metal"])), 0.0, 1.0)
    maps["bare"] = bare
    maps["relief"] = lum / max(float(np.median(lum)), 1e-3)
    return maps


def coat_from(maps, color, seed, variation=0.08):
    relief = np.clip(maps["relief"], 0.75, 1.15)
    coat = np.asarray(color) * relief[:, :, None]
    coat = tint(coat, 1.0 - variation + 2.0 * variation * unit(field(seed + 40, 1.5, 30.0, 2.0)))
    return coat


def make_paint(name, color, primer, seed, bare_amount, blister_amount, streak_count, chalk, salt, grime, rough_paint=0.48, scan="PaintedMetal012", keep=1.0, wash=0.0):
    maps = painted_scan(scan, seed)
    maps["bare"] = maps["bare"] * cover(field(seed + 60, 1.0, 6.0, 2.4), keep, 0.4) if keep < 1.0 else maps["bare"]
    coat = coat_from(maps, color, seed)
    rough = np.clip(rough_paint + 0.12 * unit(field(seed + 41, 4.0, 200.0, 1.6)), 0.0, 1.0)
    albedo, rough, metal, occlusion, gradient, bare, run = marine(seed, rig_catalog[name]["tile"], coat, primer, rough, maps, bare_amount, blister_amount, streak_count, 0.8, chalk, salt, grime)
    if wash > 0.0:
        sheet = cover(field(seed + 61, 1.5, 40.0, 1.8, 1.0, 7.0), 0.35, 0.6) * (1.0 - bare)
        albedo = mix(albedo, albedo * np.array([0.82, 0.62, 0.46]) + np.array([0.02, 0.008, 0.002]), sheet * wash)
        grime_band = cover(field(seed + 62, 1.0, 12.0, 2.0, 1.0, 3.0), 0.4, 0.6)
        albedo = mix(albedo, albedo * np.array([0.72, 0.7, 0.64]), grime_band * wash * 0.6)
    gx = gradient[0] + maps["gx"] * (1.0 - bare) * 0.35
    gy = gradient[1] + maps["gy"] * (1.0 - bare) * 0.35
    save(name, albedo, rough, occlusion, gradient=(gx, gy), metal=metal)


def make_paints():
    make_paint("rig_paint_white", linear(200, 198, 188), linear(150, 74, 52), 9100, 0.022, 0.012, 46, 0.3, 0.45, 0.4, 0.48, "PaintedMetal012", 0.35, 0.55)
    make_paint("rig_paint_orange", linear(214, 92, 30), linear(120, 112, 104), 9200, 0.05, 0.025, 40, 0.55, 0.35, 0.3, 0.5)
    make_paint("rig_paint_yellow", linear(212, 168, 48), linear(130, 120, 106), 9300, 0.07, 0.03, 26, 0.55, 0.3, 0.45, 0.52)
    make_paint("rig_paint_grey", linear(120, 124, 124), linear(150, 74, 52), 9400, 0.05, 0.03, 36, 0.25, 0.4, 0.35, 0.5)


def make_deck():
    seed = 9500
    tile = rig_catalog["rig_deck_green"]["tile"]
    maps = rk.shuffled(rk.scan("green_metal_rust", 2), seed, 0.5)
    lum = rk.luminance(maps["albedo"])
    relief = np.clip(lum / max(float(np.median(lum)), 1e-3), 0.7, 1.25)
    coat = linear(58, 92, 70) * relief[:, :, None]
    coat = tint(coat, 0.86 + 0.24 * unit(field(seed + 1, 1.2, 12.0, 2.2)))
    grit = speckle(seed + 2, 0.7)
    coat = tint(coat, 0.94 + 0.08 * unit(grit))
    u = grid_u / size
    v = grid_v / size
    seam_u = np.minimum(u, 1.0 - u) * tile
    seam_v = np.minimum(np.abs(v - 0.5), np.minimum(v, 1.0 - v)) * tile
    shifted_u = np.minimum(np.abs(u - 0.5), np.minimum(u, 1.0 - u)) * tile
    lower = v < 0.5
    seam = np.where(lower, sstep(0.011, 0.004, seam_u), sstep(0.011, 0.004, shifted_u)) + sstep(0.011, 0.004, seam_v)
    seam = np.clip(seam, 0.0, 1.0)
    bead = np.clip(np.where(lower, sstep(0.012, 0.0, seam_u), sstep(0.012, 0.0, shifted_u)) + sstep(0.012, 0.0, seam_v), 0.0, 1.0)
    path = cover(field(seed + 3, 3.0, 40.0, 1.9) + 0.6 * field(seed + 4, 12.0, 160.0, 1.6), 0.2, 0.3)
    scuff = cover(field(seed + 5, 10.0, 400.0, 1.4, 6.0, 1.0), 0.22, 0.25) * (0.4 + 0.6 * path)
    rough = np.clip(0.62 + 0.1 * unit(grit), 0.0, 1.0)
    albedo, rough, metal, occlusion, gradient, bare, run = marine(seed, tile, coat, linear(92, 84, 76), rough, None, 0.025, 0.015, 0, 0.6, 0.15, 0.45, 0.3, 2)
    steel = mix(linear(62, 58, 54), linear(84, 58, 40), unit(field(seed + 11, 4.0, 100.0, 1.7)) * 0.6) * (0.8 + 0.3 * unit(field(seed + 6, 20.0, 400.0, 1.4)))[:, :, None]
    worn = np.clip(path * 0.75 + scuff * 0.45, 0.0, 1.0) * (1.0 - bare)
    albedo = mix(albedo, steel, worn * 0.75)
    weld_rust = bead * (0.5 + 0.5 * unit(field(seed + 7, 30.0, 400.0, 1.4)))
    rust = rust_layer(seed + 8, 2)
    albedo = mix(albedo, rust["albedo"] * 1.1, np.clip(weld_rust * 0.85 + blur(bead, 4.0) * 0.4, 0.0, 1.0))
    oil = cover(field(seed + 9, 2.0, 40.0, 2.0), 0.08, 0.5)
    albedo = mix(albedo, linear(26, 24, 22), oil * 0.5)
    puddle = cover(field(seed + 10, 1.5, 20.0, 2.2), 0.12, 0.4)
    albedo = mix(albedo, albedo * np.array([0.82, 0.62, 0.45]), puddle * 0.45)
    metal = np.clip(worn * 0.55 * (1.0 - oil), 0.0, 1.0)
    rough = mix(rough, 0.5, worn * 0.6)
    rough = mix(rough, 0.3, oil * 0.6)
    height = bead * 0.0015 - seam * 0.0004 + grit * 0.00006 * (1.0 - worn) - worn * 0.0002
    gx, gy = rk.gradient_of(height, tile / size)
    gx = gx + gradient[0] + maps["gx"] * 0.25
    gy = gy + gradient[1] + maps["gy"] * 0.25
    occlusion = occlusion - 0.25 * seam
    save("rig_deck_green", albedo, rough, occlusion, gradient=(gx, gy), metal=metal)


def make_rust():
    seed = 9600
    maps = rk.shuffled(rk.scan("rusty_metal_04", 1), seed, 0.5)
    base = rust_layer(seed + 1, 2)
    weight = cover(field(seed + 2, 1.5, 10.0, 2.2), 0.55, 0.5)
    albedo = mix(maps["albedo"], base["albedo"], weight * 0.6)
    run = streaks(seed + 3, 60, (0.2, 0.8), (2.0, 9.0))
    albedo = mix(albedo, albedo * np.array([1.35, 0.8, 0.5]) + np.array([0.03, 0.01, 0.0]), run * 0.55)
    dark = cover(field(seed + 4, 5.0, 150.0, 1.7, 1.0, 4.0), 0.3, 0.4)
    albedo = mix(albedo, albedo * 0.55, dark * 0.5)
    scale = cover(field(seed + 5, 18.0, 500.0, 1.3), 0.2, 0.2)
    albedo = mix(albedo, linear(52, 34, 26), scale * 0.4)
    salt = cover(field(seed + 6, 3.0, 100.0, 1.8, 1.0, 6.0) + 0.5 * run, 0.08, 0.3)
    albedo = mix(albedo, linear(170, 160, 146), salt * 0.3)
    rough = np.clip(mix(maps["rough"], base["rough"], weight * 0.6) * 0.5 + 0.45 + 0.08 * scale, 0.0, 1.0)
    metal = np.clip(maps["metal"] * 0.35 * (1.0 - weight), 0.0, 1.0)
    height = field(seed + 7, 20.0, 400.0, 1.4) * 0.0004 + scale * 0.0005
    occlusion = np.clip(0.7 + 0.3 * maps["ao"], 0.0, 1.0) - 0.2 * cavity(height, 1.5, 0.0005)
    gx, gy = rk.gradient_of(height, 2.0 / size)
    save("rig_rust", albedo, rough, occlusion, gradient=(gx + maps["gx"] * 0.6, gy + maps["gy"] * 0.6), metal=metal)


def scatter_cones(rng, count, radius, height_range, existing, ident_map, palette_ids, start):
    scale = size / rig_catalog["rig_marine"]["tile"]
    for index in range(count):
        cx = rng.uniform(0.0, size)
        cy = rng.uniform(0.0, size)
        r = rng.uniform(radius[0], radius[1]) * scale
        top = rng.uniform(height_range[0], height_range[1])
        reach = int(r * 1.2) + 2
        cols = np.arange(int(cx) - reach, int(cx) + reach + 1)
        rows = np.arange(int(cy) - reach, int(cy) + reach + 1)
        lv, lu = np.meshgrid(rows + 0.5 - cy, cols + 0.5 - cx, indexing="ij")
        d = np.hypot(lu, lv * rng.uniform(0.85, 1.15)) / r
        cone = top * np.clip(1.0 - d, 0.0, 1.0) ** 0.7
        crater = sstep(0.32, 0.2, d) * top * 0.75
        z = cone - crater
        where = np.ix_(rows % size, cols % size)
        current = existing[where]
        take = (d < 1.0) & (z > current)
        existing[where] = np.where(take, z, current)
        ident_map[where] = np.where(take, start + index, ident_map[where])
        palette_ids.append(int(rng.integers(0, 4)))
    return existing


def make_marine():
    seed = 9700
    tile = rig_catalog["rig_marine"]["tile"]
    rng = np.random.default_rng(seed)
    rust = rust_layer(seed + 1, 1)
    height = np.zeros((size, size))
    ident = np.full((size, size), -1, np.int64)
    kinds = []
    scatter_cones(rng, 1500, (0.004, 0.01), (0.002, 0.005), height, ident, kinds, 0)
    scatter_cones(rng, 420, (0.01, 0.022), (0.004, 0.01), height, ident, kinds, 1500)
    barnacle = (ident >= 0) * cover(field(seed + 12, 1.5, 10.0, 2.0), 0.6, 0.4)
    shells = [linear(150, 146, 132), linear(126, 122, 108), linear(104, 100, 90), linear(168, 164, 150)]
    palette = np.array(shells)[np.array(kinds)][np.clip(ident, 0, None)]
    crater = sstep(0.0005, -0.001, height - blur(height, 2.0))
    shell = tint(palette, 0.8 + 0.3 * unit(speckle(seed + 2, 0.8)))
    shell = mix(shell, linear(36, 34, 30), crater * 0.6)
    shell = mix(shell, linear(70, 80, 44), cover(field(seed + 13, 4.0, 100.0, 1.7), 0.35, 0.4)[:, :, None] * 0.45)
    height = height * barnacle
    mussel_zone = cover(field(seed + 3, 1.2, 8.0, 2.2), 0.35, 0.3)
    mid, edge2, vx, vy = kit.site_voronoi([(rng.uniform(0.0, tile), rng.uniform(0.0, tile)) for index in range(420)], tile, 1.6, 0.002)
    mussel = sstep(0.0, 0.004, edge2) * mussel_zone
    mussel_color = mix(linear(22, 24, 34), linear(46, 48, 60), unit(field(seed + 4, 30.0, 400.0, 1.4)))
    mussel_color = mix(mussel_color, linear(92, 70, 46), sstep(0.006, 0.0, edge2) * mussel_zone * 0.5)
    weed_zone = cover(field(seed + 5, 1.5, 14.0, 2.0), 0.4, 0.35)
    weed_strands = cover(field(seed + 6, 4.0, 300.0, 1.4, 1.0, 9.0), 0.45, 0.3)
    weed = np.clip(weed_zone * (0.5 + 0.7 * weed_strands), 0.0, 1.0)
    weed_color = mix(linear(54, 66, 26), linear(88, 92, 34), unit(field(seed + 7, 6.0, 200.0, 1.6)))
    weed_color = mix(weed_color, linear(70, 52, 30), cover(field(seed + 8, 2.0, 40.0), 0.3, 0.4)[:, :, None] * 0.6)
    lime = cover(field(seed + 9, 10.0, 300.0, 1.5), 0.25, 0.3) * (1.0 - mussel_zone)
    albedo = mix(rust["albedo"] * 0.8, linear(170, 164, 150), lime * 0.7)
    albedo = mix(albedo, mussel_color, mussel)
    albedo = mix(albedo, weed_color, weed * (1.0 - barnacle * 0.7))
    albedo = mix(albedo, shell, barnacle * (1.0 - weed * 0.5))
    slime = cover(field(seed + 10, 2.0, 30.0, 2.0), 0.4, 0.5)
    albedo = mix(albedo, albedo * np.array([0.7, 0.78, 0.6]), slime * 0.35)
    height = height + mussel * 0.006 * (0.6 + 0.4 * unit(field(seed + 11, 20.0, 300.0))) + weed * 0.002 + lime * 0.0008
    rough = np.clip(0.75 - 0.25 * weed - 0.15 * slime + 0.15 * barnacle - 0.2 * mussel, 0.2, 1.0)
    occlusion = 1.0 - 0.6 * cavity(height, 2.0, 0.003) - 0.3 * crater
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_marine", albedo, rough, occlusion, gradient=(gx * 0.7 + rust["gx"] * 0.3, gy * 0.7 + rust["gy"] * 0.3))


def make_grating():
    seed = 9800
    tile = rig_catalog["rig_grating"]["tile"]
    px = size / tile
    u = grid_u
    v = grid_v
    pitch = size / 30.0
    bar_half = 6.2
    along = np.abs(((u + pitch * 0.5) % pitch) - pitch * 0.5)
    bars = sstep(bar_half + 0.8, bar_half - 0.8, along)
    cross_pitch = size / 10.0
    cross_d = np.abs(((v + cross_pitch * 0.5) % cross_pitch) - cross_pitch * 0.5)
    rods = sstep(7.5, 6.0, cross_d)
    band = sstep(5.5, 4.0, np.minimum(v, size - v))
    alpha = np.clip(np.maximum(np.maximum(bars, rods), band), 0.0, 1.0)
    holes = cover(field(seed + 1, 6.0, 200.0, 1.6), 0.025, 0.1) * sstep(0.3, 0.6, unit(field(seed + 2, 40.0, 400.0)))
    alpha = alpha * (1.0 - holes)
    zinc = rk.scan_acg("SheetMetal002")
    galv = zinc["albedo"] * 0.55 + 0.06
    twist = 0.5 + 0.5 * np.sin((u / cross_pitch * 9.0 + v * 0.0) * tau)
    serration = 0.5 + 0.5 * np.sin(v / (px * 0.012) * tau)
    rust = rust_layer(seed + 3, 2)
    rusty = cover(field(seed + 4, 1.5, 20.0, 2.0) + 0.6 * field(seed + 5, 20.0, 300.0, 1.4), 0.45, 0.3)
    joints = np.clip(blur(rods * bars, 3.0) * 3.0, 0.0, 1.0)
    rusty = np.clip(rusty + joints * 0.6, 0.0, 1.0)
    white = cover(field(seed + 6, 6.0, 200.0, 1.6), 0.25, 0.4) * (1.0 - rusty)
    albedo = mix(galv, linear(196, 194, 186), white * 0.6)
    albedo = mix(albedo, rust["albedo"] * 1.15, rusty)
    paint = cover(field(seed + 7, 1.2, 8.0, 2.4), 0.15, 0.4)
    albedo = mix(albedo, linear(190, 150, 40) * (0.8 + 0.3 * unit(speckle(seed + 8, 1.0)))[:, :, None], paint * (1.0 - rusty) * 0.7)
    edge_dark = sstep(bar_half - 0.5, bar_half + 0.5, along) * (1.0 - rods)
    albedo = tint(albedo, 1.0 - 0.35 * edge_dark)
    dirt = cover(field(seed + 9, 2.0, 60.0, 2.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * np.array([0.55, 0.5, 0.45]), dirt * 0.5)
    height = bars * (0.0015 + 0.0004 * serration) + rods * (0.0022 + 0.0006 * twist) + band * 0.002
    gx, gy = rk.gradient_of(height, tile / size)
    metal = np.clip(0.8 * (1.0 - rusty) * (1.0 - paint * 0.8) * (1.0 - dirt * 0.4), 0.0, 1.0)
    rough = np.clip(mix(0.42 + 0.2 * white, 0.85, rusty) + 0.15 * dirt, 0.0, 1.0)
    occlusion = 1.0 - 0.45 * joints - 0.25 * edge_dark
    save("rig_grating", albedo, rough, occlusion, gradient=(gx + rust["gx"] * rusty * 0.6, gy + rust["gy"] * rusty * 0.6), metal=metal, alpha=alpha)


def make_net():
    seed = 9900
    tile = rig_catalog["rig_net"]["tile"]
    pitch = size / 6.0
    a = (grid_u + grid_v) / math.sqrt(2.0)
    b = (grid_u - grid_v) / math.sqrt(2.0)
    p = pitch / math.sqrt(2.0) * 2.0
    da = np.abs(((a + p * 0.5) % p) - p * 0.5)
    db = np.abs(((b + p * 0.5) % p) - p * 0.5)
    rope = 7.5
    strand_a = sstep(rope + 1.0, rope - 1.0, da)
    strand_b = sstep(rope + 1.0, rope - 1.0, db)
    knot = sstep(rope * 2.2, rope * 1.4, np.hypot(da, db))
    alpha = np.clip(np.maximum(np.maximum(strand_a, strand_b), knot), 0.0, 1.0)
    twist_a = 0.5 + 0.5 * np.sin(b / 9.0 * tau + da * 0.3)
    twist_b = 0.5 + 0.5 * np.sin(a / 9.0 * tau + db * 0.3)
    fibre = np.maximum(strand_a * twist_a, strand_b * twist_b)
    base = mix(linear(96, 100, 82), linear(62, 64, 54), unit(field(seed + 1, 2.0, 40.0, 2.0)))
    base = tint(base, 0.8 + 0.3 * fibre)
    green = cover(field(seed + 2, 2.0, 40.0, 2.0), 0.3, 0.4)
    base = mix(base, linear(60, 76, 40), green * 0.5)
    guano = cover(field(seed + 3, 6.0, 200.0, 1.6), 0.08, 0.3)
    base = mix(base, linear(210, 206, 196), guano * 0.6)
    base = tint(base, 1.0 - 0.4 * knot)
    torn = cover(field(seed + 4, 3.0, 60.0, 1.8), 0.02, 0.1)
    alpha = alpha * (1.0 - torn)
    height = (strand_a * (1.0 - da / (rope + 1.0)) + strand_b * (1.0 - db / (rope + 1.0))) * 0.003 + knot * 0.004 + fibre * 0.0006
    gx, gy = rk.gradient_of(height, tile / size)
    occlusion = 1.0 - 0.4 * knot * 0.5
    save("rig_net", base, np.clip(0.88 + 0.06 * fibre, 0.0, 1.0), occlusion, gradient=(gx, gy), alpha=alpha)


def make_lifeboat():
    seed = 10000
    tile = rig_catalog["rig_lifeboat"]["tile"]
    gel = linear(232, 98, 28)
    coat = flat(gel) * (0.9 + 0.12 * unit(field(seed + 1, 1.5, 20.0, 2.0)))[:, :, None]
    chalk = cover(field(seed + 2, 1.2, 10.0, 2.2), 0.6, 0.6)
    coat = mix(coat, coat * 0.65 + linear(200, 170, 150) * 0.45, chalk * 0.55)
    weave_u = 0.5 + 0.5 * np.sin(grid_u / 6.0 * tau)
    weave_v = 0.5 + 0.5 * np.sin(grid_v / 6.0 * tau)
    weave = np.where((np.floor(grid_u / 12.0) + np.floor(grid_v / 12.0)) % 2 == 0, weave_u, weave_v)
    worn = cover(field(seed + 3, 3.0, 120.0, 1.7) + 0.5 * field(seed + 4, 20.0, 300.0, 1.4), 0.06, 0.06)
    glass = linear(222, 200, 166) * (0.75 + 0.3 * weave)[:, :, None]
    coat = mix(coat, glass, worn)
    algae = cover(field(seed + 5, 2.0, 80.0, 1.8, 1.0, 6.0), 0.12, 0.4)
    coat = mix(coat, linear(96, 92, 44), algae * 0.35)
    run = drip(np.clip(worn + cover(speckle(seed + 6, 1.0), 0.01, 0.2), 0.0, 1.0), seed + 9, 0.96, 0.985, 0.6)
    coat = mix(coat, coat * np.array([0.72, 0.66, 0.6]), run * 0.3 * (1.0 - worn))
    scratch = cover(field(seed + 7, 2.0, 700.0, 1.2, 20.0, 0.5), 0.02, 0.2)
    coat = mix(coat, linear(236, 214, 190), scratch * 0.6)
    rough = np.clip(0.35 + 0.35 * chalk + 0.3 * worn + 0.15 * algae + 0.2 * run, 0.0, 1.0)
    height = -worn * 0.0004 + weave * worn * 0.0002 - scratch * 0.0002 + field(seed + 8, 8.0, 200.0, 1.6) * 0.0001
    occlusion = 1.0 - 0.25 * cavity(height, 1.5, 0.0003)
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_lifeboat", coat, rough, occlusion, gradient=(gx, gy))


def make_rubber():
    seed = 10100
    tile = rig_catalog["rig_rubber"]["tile"]
    maps = rk.shuffled(rk.scan_acg("Rubber004"), seed, 0.5)
    albedo = maps["albedo"] * 1.4 + 0.008
    bloom = cover(field(seed + 1, 1.5, 20.0, 2.0), 0.4, 0.5)
    albedo = mix(albedo, linear(96, 94, 90), bloom * 0.35)
    craze = kit.cracks(seed + 2, 30, 0.8, 0.7)
    albedo = mix(albedo, linear(10, 10, 10), craze * 0.7)
    scuff = cover(field(seed + 3, 3.0, 300.0, 1.4, 6.0, 1.0), 0.2, 0.3)
    albedo = mix(albedo, linear(70, 68, 64), scuff * 0.4)
    salt = cover(field(seed + 4, 4.0, 200.0, 1.6), 0.12, 0.3)
    albedo = mix(albedo, linear(170, 166, 156), salt * 0.3)
    rough = np.clip(maps["rough"] + 0.2 * bloom + 0.1 * salt, 0.4, 1.0)
    height = -craze * 0.0006 + field(seed + 5, 20.0, 400.0, 1.4) * 0.0002
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_rubber", albedo, rough, np.clip(0.8 + 0.2 * maps["ao"], 0.0, 1.0) - 0.4 * craze, gradient=(gx + maps["gx"] * 0.5, gy + maps["gy"] * 0.5))


def make_wall():
    seed = 10200
    tile = rig_catalog["rig_wall"]["tile"]
    u = grid_u / size
    panel = 4.0
    local = (u * panel) % 1.0
    seam = sstep(0.0035, 0.0012, np.minimum(local, 1.0 - local))
    trim = sstep(0.006, 0.003, np.minimum(local, 1.0 - local))
    index = np.floor(u * panel).astype(np.int64)
    tone = np.array([1.0, 0.97, 1.02, 0.985])[index % 4]
    base = linear(206, 200, 182) * tone[:, :, None]
    base = tint(base, 0.95 + 0.06 * unit(field(seed + 1, 2.0, 60.0, 2.0)))
    stipple = speckle(seed + 2, 0.7)
    base = tint(base, 0.97 + 0.04 * unit(stipple))
    damp = cover(field(seed + 3, 1.2, 8.0, 2.4, 1.0, 1.6), 0.18, 0.35)
    tide = sstep(0.06, 0.0, np.abs(blur(damp, 3.0) - 0.5)) * 0.8
    base = mix(base, base * np.array([0.8, 0.7, 0.54]), damp * 0.5)
    base = mix(base, base * np.array([0.6, 0.5, 0.36]), tide * 0.45)
    mould = cover(speckle(seed + 4, 1.1), 0.12, 0.3) * cover(field(seed + 5, 2.0, 20.0, 2.0), 0.25, 0.4)
    base = mix(base, linear(42, 46, 36), mould * 0.65)
    scuff = cover(field(seed + 6, 4.0, 300.0, 1.5, 4.0, 1.0), 0.12, 0.3)
    base = mix(base, base * 0.75, scuff * 0.4)
    grime = cover(field(seed + 7, 1.5, 30.0, 2.0, 1.0, 4.0), 0.3, 0.5)
    base = mix(base, base * np.array([0.78, 0.76, 0.7]), grime * 0.4)
    screws = np.zeros((size, size))
    v = grid_v / size
    for k in range(5):
        cy = (k + 0.5) / 5.0
        d = np.hypot((np.minimum(local, 1.0 - local)) * size / panel, (v - cy) * size)
        screws = np.maximum(screws, sstep(3.0, 1.5, d))
    metal_trim = linear(150, 150, 146)
    base = mix(base, metal_trim, trim * 0.85)
    base = mix(base, linear(30, 30, 28), seam)
    base = mix(base, linear(60, 58, 54), screws * 0.8)
    height = -seam * 0.0015 + trim * 0.0004 + screws * 0.0003 + stipple * 0.00003 - damp * 0.0001
    rough = np.clip(0.55 + 0.15 * damp + 0.2 * mould - 0.25 * trim, 0.1, 1.0)
    metal = trim * 0.7
    occlusion = 1.0 - 0.5 * seam - 0.2 * cavity(height, 1.5, 0.0003)
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_wall", base, rough, occlusion, gradient=(gx, gy), metal=metal)


def make_ceiling():
    seed = 10300
    tile = rig_catalog["rig_ceiling"]["tile"]
    pitch = size / 2.0
    lu = grid_u % pitch
    lv = grid_v % pitch
    edge = np.minimum(np.minimum(lu, pitch - lu), np.minimum(lv, pitch - lv))
    tbar = sstep(9.0, 7.0, edge)
    cell = (np.floor(grid_u / pitch) + 2 * np.floor(grid_v / pitch)).astype(np.int64)
    tone = np.array([1.0, 0.94, 0.97, 0.9])[cell % 4]
    fissure = cover(field(seed + 1, 30.0, 500.0, 1.2), 0.25, 0.3) * cover(speckle(seed + 2, 1.0), 0.4, 0.4)
    tile_color = linear(214, 210, 198) * tone[:, :, None]
    tile_color = mix(tile_color, tile_color * 0.75, fissure * 0.6)
    stain = cover(field(seed + 3, 1.5, 12.0, 2.3), 0.22, 0.4)
    ring = sstep(0.08, 0.0, np.abs(blur(stain, 2.0) - 0.5))
    tile_color = mix(tile_color, tile_color * np.array([0.82, 0.68, 0.48]), stain * 0.5)
    tile_color = mix(tile_color, tile_color * np.array([0.58, 0.46, 0.3]), ring * 0.55)
    smoke = cover(field(seed + 4, 1.2, 10.0, 2.2), 0.3, 0.5)
    tile_color = mix(tile_color, tile_color * 0.75, smoke * 0.35)
    bar_color = linear(176, 176, 170)
    albedo = mix(tile_color, bar_color, tbar)
    rust_dots = cover(speckle(seed + 5, 1.2), 0.08, 0.3) * tbar
    albedo = mix(albedo, linear(110, 60, 30), rust_dots * 0.7)
    height = -tbar * 0.0 + (1.0 - tbar) * -0.002 * sstep(9.0, 20.0, edge) - fissure * 0.0004
    rough = np.where(tbar > 0.5, 0.45, 0.92)
    metal = tbar * 0.6
    occlusion = 1.0 - 0.3 * sstep(14.0, 9.0, edge) * (1.0 - tbar) - 0.2 * fissure
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_ceiling", albedo, rough, occlusion, gradient=(gx, gy), metal=metal)


def make_vinyl():
    seed = 10400
    tile = rig_catalog["rig_vinyl"]["tile"]
    base = mix(linear(104, 110, 112), linear(88, 94, 98), unit(field(seed + 1, 2.0, 40.0, 2.0)))
    chips = cover(speckle(seed + 2, 0.9), 0.12, 0.2)
    light = cover(speckle(seed + 3, 0.8), 0.08, 0.2)
    base = mix(base, linear(56, 60, 64), chips * 0.6)
    base = mix(base, linear(170, 172, 168), light * 0.5)
    u = grid_u / size
    seam = sstep(1.6, 0.6, np.minimum(grid_u % (size * 0.5), size * 0.5 - grid_u % (size * 0.5)))
    worn = cover(field(seed + 4, 1.2, 10.0, 2.3) + 0.5 * field(seed + 5, 10.0, 200.0, 1.6), 0.25, 0.3)
    base = mix(base, base * 0.82 + 0.02, worn * 0.4)
    scuff = cover(field(seed + 6, 3.0, 400.0, 1.4, 5.0, 1.0), 0.2, 0.3)
    base = mix(base, linear(40, 40, 40), scuff * 0.3)
    dirt = cover(field(seed + 7, 2.0, 50.0, 2.0), 0.3, 0.6)
    base = mix(base, base * np.array([0.7, 0.66, 0.58]), dirt * 0.45)
    lift = cover(field(seed + 8, 2.0, 60.0, 2.0), 0.03, 0.2)
    base = mix(base, linear(46, 40, 32), lift * 0.7)
    base = mix(base, linear(30, 30, 30), seam * 0.8)
    height = -seam * 0.0008 - worn * 0.0001 + lift * 0.0006 + chips * 0.00002
    rough = np.clip(0.42 + 0.25 * worn + 0.2 * dirt - 0.05 * light, 0.1, 1.0)
    occlusion = 1.0 - 0.4 * seam - 0.2 * cavity(height, 1.5, 0.0003)
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_vinyl", base, rough, occlusion, gradient=(gx, gy))


def make_steel():
    seed = 10500
    tile = rig_catalog["rig_steel"]["tile"]
    brush = field(seed + 1, 2.0, 700.0, 1.0, 40.0, 0.3)
    base = linear(168, 168, 166) * (0.86 + 0.14 * unit(brush))[:, :, None]
    smear = cover(field(seed + 2, 2.0, 40.0, 2.0), 0.35, 0.5)
    base = mix(base, base * np.array([0.7, 0.68, 0.64]), smear * 0.5)
    spots = cover(speckle(seed + 3, 1.6), 0.1, 0.3) * cover(field(seed + 4, 2.0, 30.0), 0.4, 0.4)
    base = mix(base, linear(210, 206, 196), spots * 0.4)
    tea = cover(field(seed + 5, 3.0, 100.0, 1.7), 0.12, 0.3)
    base = mix(base, linear(150, 100, 60), tea * 0.4)
    scratch = cover(field(seed + 6, 2.0, 700.0, 1.2, 25.0, 0.4), 0.03, 0.2)
    base = mix(base, linear(200, 200, 198), scratch * 0.5)
    rough = np.clip(0.28 + 0.08 * unit(brush) + 0.3 * smear + 0.2 * spots + 0.3 * tea, 0.05, 1.0)
    metal = np.clip(1.0 - 0.5 * tea - 0.3 * smear, 0.0, 1.0)
    height = brush * 0.00004 - scratch * 0.0001
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_steel", base, rough, np.ones((size, size)) - 0.1 * smear, gradient=(gx, gy), metal=metal)


def make_marking():
    seed = 10600
    tile = rig_catalog["rig_mark_white"]["tile"]
    deck = linear(58, 92, 70) * (0.85 + 0.25 * unit(field(seed + 1, 1.2, 12.0, 2.2)))[:, :, None]
    coat = linear(214, 212, 204) * (0.9 + 0.12 * unit(field(seed + 2, 2.0, 60.0, 2.0)))[:, :, None]
    grit = speckle(seed + 3, 0.7)
    wear_field = field(seed + 4, 2.0, 40.0, 2.0) + 0.6 * field(seed + 5, 20.0, 400.0, 1.4)
    worn = cover(wear_field, 0.22, 0.05)
    deep = cover(wear_field, 0.07, 0.05)
    rust = rust_layer(seed + 6, 2)
    albedo = mix(coat, deck, worn)
    albedo = mix(albedo, rust["albedo"], deep)
    tyre = cover(field(seed + 7, 2.0, 200.0, 1.5, 8.0, 1.0), 0.15, 0.3)
    albedo = mix(albedo, linear(40, 40, 40), tyre * 0.45 * (1.0 - worn))
    grime = cover(field(seed + 8, 1.5, 30.0, 2.0), 0.4, 0.5)
    albedo = mix(albedo, albedo * np.array([0.72, 0.72, 0.66]), grime * 0.45)
    guano = cover(field(seed + 9, 8.0, 300.0, 1.5), 0.04, 0.2)
    albedo = mix(albedo, linear(232, 230, 220), guano * 0.6)
    crack = kit.cracks(seed + 10, 18, 1.0, 0.5) * (1.0 - worn)
    albedo = mix(albedo, albedo * 0.5, crack * 0.6)
    height = (1.0 - worn) * 0.0004 - deep * 0.0002 + grit * 0.00006 - crack * 0.0003
    rough = np.clip(0.6 + 0.1 * unit(grit) + 0.2 * deep - 0.1 * tyre, 0.1, 1.0)
    occlusion = 1.0 - 0.3 * cavity(height, 1.5, 0.0004)
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_mark_white", albedo, rough, occlusion, gradient=(gx, gy))


def make_cardboard():
    seed = 10900
    tile = rig_catalog["rig_cardboard"]["tile"]
    flute = 0.5 + 0.5 * np.sin(grid_v / size * tile / 0.006 * tau)
    base = mix(linear(150, 112, 72), linear(126, 92, 58), unit(field(seed + 1, 2.0, 40.0, 2.0)))
    base = tint(base, 0.92 + 0.08 * flute)
    fibre = speckle(seed + 2, 0.6)
    base = tint(base, 0.95 + 0.06 * unit(fibre))
    tape_v = np.abs(grid_v / size - 0.5)
    tape = sstep(0.045, 0.04, tape_v)
    base = mix(base, linear(170, 140, 96) * (0.9 + 0.15 * unit(field(seed + 3, 8.0, 200.0, 1.6)))[:, :, None], tape * 0.85)
    print_mask = cover(field(seed + 4, 6.0, 120.0, 1.7), 0.08, 0.15) * (1.0 - tape)
    base = mix(base, linear(40, 36, 34), print_mask * 0.7)
    water = cover(field(seed + 5, 1.5, 15.0, 2.3), 0.25, 0.4)
    ring = sstep(0.08, 0.0, np.abs(blur(water, 2.0) - 0.5))
    base = mix(base, base * np.array([0.7, 0.62, 0.52]), water * 0.45)
    base = mix(base, base * np.array([0.5, 0.42, 0.34]), ring * 0.5)
    mould = cover(speckle(seed + 6, 1.2), 0.06, 0.3) * water
    base = mix(base, linear(50, 54, 40), mould * 0.6)
    crease = cover(field(seed + 7, 2.0, 300.0, 1.3, 10.0, 0.6), 0.04, 0.2)
    base = mix(base, base * 0.7, crease * 0.6)
    height = flute * 0.0003 - crease * 0.0005 + tape * 0.0002
    rough = np.clip(0.88 - 0.4 * tape + 0.05 * water, 0.2, 1.0)
    occlusion = 1.0 - 0.3 * cavity(height, 1.5, 0.0003)
    gx, gy = rk.gradient_of(height, tile / size)
    save("rig_cardboard", base, rough, occlusion, gradient=(gx, gy))


def draw_run(alpha, color, sub, lu, lv, w, h, rng, count, width, length, origin_top=True, palette=None):
    for index in range(count):
        cu = rng.uniform(w * 0.1, w * 0.9)
        top = h - rng.uniform(0.0, h * 0.08)
        span = rng.uniform(length[0], length[1]) * h
        wd = rng.uniform(width[0], width[1])
        down = (top - lv) / span
        wob = wd * 0.6 * np.sin(down * rng.uniform(3.0, 9.0) + rng.uniform(0.0, tau)) + wd * 1.2 * np.sin(down * rng.uniform(0.6, 2.0) + rng.uniform(0.0, tau))
        spread = wd * (0.5 + 1.0 * np.sqrt(np.clip(down, 0.0, 1.0)))
        value = np.exp(-((lu - cu - wob) / spread) ** 2) * np.clip(1.0 - down, 0.0, 1.0) ** 0.9 * (down > -0.02) * sstep(-0.03, 0.02, down)
        strength = rng.uniform(0.6, 1.0)
        tint_color = palette[int(rng.integers(0, len(palette)))] if palette is not None else color
        weight = value * strength
        alpha[sub] = np.maximum(alpha[sub], weight)
        color[sub] = mix(color[sub], np.asarray(tint_color) * (0.75 + 0.4 * np.clip(1.0 - down, 0.0, 1.0))[:, :, None], np.clip(weight * 1.5, 0.0, 1.0))


def make_decals():
    seed = 10700
    rng = np.random.default_rng(seed)
    albedo = flat(linear(110, 64, 34))
    alpha = np.zeros((size, size))
    rough = np.full((size, size), 0.85)
    height = np.zeros((size, size))
    noise = field(seed + 1, 8.0, 300.0, 1.5)
    rusts = [linear(120, 58, 26), linear(98, 50, 26), linear(140, 74, 34), linear(84, 44, 24)]
    for key, count, width, length in (("run_a", 3, (3.0, 7.0), (0.5, 0.95)), ("run_b", 5, (2.0, 5.0), (0.3, 0.9)), ("run_c", 2, (5.0, 10.0), (0.6, 1.0)), ("run_d", 7, (1.5, 4.0), (0.2, 0.7))):
        sub, lu, lv, w, h = tl.window_of(decals[key])
        draw_run(alpha, albedo, sub, lu, lv, w, h, rng, count, width, length, True, rusts)
    sub, lu, lv, w, h = tl.window_of(decals["runs_wide"])
    draw_run(alpha, albedo, sub, lu, lv, w, h, rng, 26, (1.5, 5.0), (0.2, 0.95), True, rusts)
    warp_a = field(seed + 21, 6.0, 120.0, 1.8)
    warp_b = field(seed + 22, 6.0, 120.0, 1.8)
    for key in ("guano_a", "guano_b"):
        sub, lu, lv, w, h = tl.window_of(decals[key])
        mask = np.zeros(lu.shape)
        wu = lu + warp_a[sub] * 5.0
        wv = lv + warp_b[sub] * 5.0
        for index in range(int(rng.integers(10, 16))):
            cx = rng.uniform(w * 0.18, w * 0.82)
            cy = rng.uniform(h * 0.18, h * 0.82)
            r = rng.uniform(3.0, 14.0) * rng.uniform(0.6, 1.0)
            stretch = rng.uniform(0.6, 1.0)
            angle = rng.uniform(0.0, tau)
            du = (wu - cx) * math.cos(angle) + (wv - cy) * math.sin(angle)
            dv = (-(wu - cx) * math.sin(angle) + (wv - cy) * math.cos(angle)) / stretch
            d = np.hypot(du, dv) / r + 0.18 * noise[sub]
            mask = np.maximum(mask, sstep(1.05, 0.85, d))
            for spray in range(int(rng.integers(4, 14))):
                reach = r * (1.2 + rng.pareto(2.0) * 0.9)
                theta = rng.uniform(0.0, tau)
                sx = cx + math.cos(theta) * reach
                sy = cy + math.sin(theta) * reach
                mask = np.maximum(mask, sstep(1.0, 0.7, np.hypot(lu - sx, lv - sy) / rng.uniform(0.8, 2.6)))
        white =mix(linear(232, 230, 222), linear(200, 196, 184), unit(noise[sub]))
        dark_core = sstep(0.95, 1.0, mask) * cover(field(seed + 20, 10.0, 300.0)[sub], 0.3, 0.4)
        color = mix(white, linear(70, 66, 56), dark_core * 0.6)
        albedo[sub] = mix(albedo[sub], color, sstep(0.05, 0.5, mask))
        alpha[sub] = np.maximum(alpha[sub], mask)
        rough[sub] = np.where(mask > 0.5, 0.75, rough[sub])
        height[sub] = height[sub] + mask * 0.0006
    sub, lu, lv, w, h = tl.window_of(decals["guano_runs"])
    draw_run(alpha, albedo, sub, lu, lv, w, h, rng, 10, (2.0, 6.0), (0.2, 0.9), True, [linear(226, 222, 212), linear(200, 196, 186), linear(214, 210, 198)])
    sub, lu, lv, w, h = tl.window_of(decals["scorch"])
    rise = lv / h
    plume_width = w * (0.12 + 0.36 * rise)
    turb = field(seed + 30, 3.0, 80.0, 1.8)[sub]
    plume = sstep(1.0, 0.45, np.abs(lu - w * 0.5 + turb * w * 0.06) / plume_width) * sstep(0.0, 0.08, rise) * sstep(1.0, 0.75, rise)
    plume = np.clip(plume * (0.7 + 0.6 * unit(field(seed + 31, 6.0, 200.0, 1.6)[sub])), 0.0, 1.0)
    soot = mix(linear(20, 18, 16), linear(70, 62, 52), sstep(0.3, 1.0, rise) * (1.0 - plume))
    albedo[sub] = mix(albedo[sub], soot, sstep(0.05, 0.6, plume))
    alpha[sub] = np.maximum(alpha[sub], plume)
    rough[sub] = np.where(plume > 0.5, 0.95, rough[sub])
    for key in ("oil_a", "oil_b"):
        sub, lu, lv, w, h = tl.window_of(decals[key])
        blob = np.zeros(lu.shape)
        for index in range(int(rng.integers(4, 8))):
            cx = rng.uniform(w * 0.25, w * 0.75)
            cy = rng.uniform(h * 0.25, h * 0.75)
            rx = rng.uniform(16.0, 60.0)
            ry = rx * rng.uniform(0.5, 1.2)
            blob = np.maximum(blob, sstep(1.0, 0.6, np.hypot((lu - cx) / rx, (lv - cy) / ry) + 0.25 * noise[sub]))
        ring = sstep(0.12, 0.0, np.abs(blob - 0.55))
        color = mix(linear(22, 20, 18), linear(48, 40, 30), ring)
        albedo[sub] = mix(albedo[sub], color, sstep(0.05, 0.5, blob))
        alpha[sub] = np.maximum(alpha[sub], blob * 0.95)
        rough[sub] = np.where(blob > 0.5, 0.25, rough[sub])
    sub, lu, lv, w, h = tl.window_of(decals["salt"])
    crust = sstep(0.35, 0.6, unit(field(seed + 40, 3.0, 120.0, 1.8)[sub]) * (1.0 - np.hypot(lu / w - 0.5, lv / h - 0.5) * 1.6))
    albedo[sub] = mix(albedo[sub], linear(210, 206, 196) * (0.85 + 0.2 * unit(speckle(seed + 41, 0.8)[sub]))[:, :, None], sstep(0.05, 0.5, crust))
    alpha[sub] = np.maximum(alpha[sub], crust)
    rough[sub] = np.where(crust > 0.5, 0.95, rough[sub])
    height = height + alpha * 0.0003
    gx, gy = rk.gradient_of(height, 1.0 / size)
    save("rig_decals", albedo, rough, np.ones((size, size)), gradient=(gx, gy), alpha=np.clip(alpha, 0.0, 1.0))


def stencil_board(canvas, box, seed, ground, rim, chip=0.08):
    tl.enamel_panel(canvas, box, seed, ground, rim, chip)
    sub, lu, lv, w, h = tl.window_of(box)
    run = streaks(seed + 3, 6, (0.3, 0.9), (1.5, 4.0))[sub]
    canvas.albedo[sub] = mix(canvas.albedo[sub], canvas.albedo[sub] * np.array([0.85, 0.55, 0.32]) + np.array([0.03, 0.01, 0.0]), run * 0.6)
    canvas.rough[sub] = np.clip(canvas.rough[sub] + 0.3, 0.0, 1.0)


def console_panel(canvas, box, seed, rng):
    sub, lu, lv, w, h = tl.window_of(box)
    base = linear(150, 146, 132) * (0.9 + 0.12 * unit(field(seed, 2.0, 40.0)[sub]))[:, :, None]
    image = base.copy()
    for row in range(5):
        for column in range(14):
            cx = 22.0 + column * (w - 44.0) / 13.0
            cy = 24.0 + row * (h - 48.0) / 4.0
            kind = rng.integers(0, 4)
            if kind == 0:
                m = tl.ellipse_mask(lu, lv, cx, cy, 7.0, 7.0, 0.7)
                c = [linear(160, 30, 24), linear(40, 120, 40), linear(200, 150, 30), linear(220, 220, 210)][int(rng.integers(0, 4))]
            elif kind == 1:
                m = tl.rect_mask(lu, lv, cx - 9.0, cy - 6.0, cx + 9.0, cy + 6.0)
                c = linear(30, 30, 32)
            elif kind == 2:
                m = tl.rect_mask(lu, lv, cx - 3.0, cy - 9.0, cx + 3.0, cy + 9.0)
                c = linear(200, 200, 196)
            else:
                m = tl.rect_mask(lu, lv, cx - 11.0, cy - 7.0, cx + 11.0, cy + 7.0)
                c = linear(236, 230, 200) if rng.random() < 0.5 else linear(200, 90, 40)
            image = mix(image, np.asarray(c), m)
            canvas.height[sub] = canvas.height[sub] + m * 0.001
    grime = cover(field(seed + 3, 2.0, 40.0)[sub], 0.35, 0.5)
    canvas.albedo[sub] = mix(image, image * 0.6, grime * 0.4)
    canvas.rough[sub] = 0.55


def mimic_panel(canvas, box, seed, rng):
    sub, lu, lv, w, h = tl.window_of(box)
    image = linear(176, 184, 176) * (0.9 + 0.1 * unit(field(seed, 2.0, 40.0)[sub]))[:, :, None]
    lines = np.zeros(lu.shape)
    for index in range(16):
        if rng.random() < 0.5:
            y = rng.uniform(20.0, h - 20.0)
            x0 = rng.uniform(10.0, w * 0.5)
            x1 = rng.uniform(x0 + 40.0, w - 10.0)
            lines = np.maximum(lines, tl.rect_mask(lu, lv, x0, y - 1.5, x1, y + 1.5, 0.5))
        else:
            x = rng.uniform(20.0, w - 20.0)
            y0 = rng.uniform(10.0, h * 0.5)
            y1 = rng.uniform(y0 + 30.0, h - 10.0)
            lines = np.maximum(lines, tl.rect_mask(lu, lv, x - 1.5, y0, x + 1.5, y1, 0.5))
    vessels = np.zeros(lu.shape)
    for index in range(6):
        cx = rng.uniform(40.0, w - 40.0)
        cy = rng.uniform(40.0, h - 40.0)
        rx = rng.uniform(18.0, 40.0)
        ry = rng.uniform(10.0, 22.0)
        outer = tl.ellipse_mask(lu, lv, cx, cy, rx, ry, 1.0)
        inner = tl.ellipse_mask(lu, lv, cx, cy, rx - 3.0, ry - 3.0, 1.0)
        vessels = np.maximum(vessels, np.clip(outer - inner, 0.0, 1.0))
    lamps = np.zeros(lu.shape)
    for index in range(24):
        lamps = np.maximum(lamps, tl.ellipse_mask(lu, lv, rng.uniform(10.0, w - 10.0), rng.uniform(10.0, h - 10.0), 3.5, 3.5, 0.6))
    image = mix(image, linear(30, 50, 110), lines)
    image = mix(image, linear(20, 20, 20), vessels)
    image = mix(image, linear(170, 30, 20), lamps)
    yellowed = cover(field(seed + 4, 1.5, 20.0)[sub], 0.5, 0.5)
    canvas.albedo[sub] = mix(image, image * np.array([0.9, 0.8, 0.6]), yellowed * 0.5)
    canvas.rough[sub] = 0.4


def screen_face(canvas, box, seed, cracked):
    sub, lu, lv, w, h = tl.window_of(box)
    bezel = 12.0
    inside = tl.rect_mask(lu, lv, bezel, bezel, w - bezel, h - bezel, 1.0)
    glass = linear(16, 20, 18) * (0.8 + 0.4 * sstep(h, 0.0, lv + lu * 0.4))[:, :, None]
    case = linear(170, 164, 148) * (0.9 + 0.1 * unit(field(seed, 3.0, 40.0)[sub]))[:, :, None]
    image = mix(case, glass, inside)
    dust = cover(field(seed + 1, 3.0, 60.0)[sub], 0.4, 0.5) * inside
    image = mix(image, linear(80, 78, 70), dust * 0.25)
    if cracked:
        cx = w * 0.62
        cy = h * 0.4
        theta = np.arctan2(lv - cy, lu - cx)
        r = np.hypot(lu - cx, lv - cy)
        spokes = np.abs(np.sin(theta * 7.0 + field(seed + 2, 4.0, 60.0)[sub] * 0.8)) < 0.05
        rings = np.abs(np.sin(r * 0.12)) < 0.06
        crack = (spokes | (rings & (r < 60.0))) * inside
        image = mix(image, linear(170, 176, 170), crack * 0.6)
    canvas.albedo[sub] = image
    canvas.rough[sub] = np.where(inside > 0.5, 0.08, 0.5)


def make_signs():
    seed = 10800
    rng = np.random.default_rng(seed)
    canvas = tl.Canvas(linear(120, 118, 112), 0.6)
    say = canvas.say
    table = signs
    white = (0.88, 0.88, 0.84)
    black = (0.03, 0.03, 0.03)
    stencil_board(canvas, table["name_board"], seed, linear(214, 210, 198), linear(40, 40, 40), 0.06)
    say(table, "name_board", "ECREHOU  ALPHA", 84.0, "stencil", 0.0, 0.0, 960.0, 1.12, 0.0, black)
    stencil_board(canvas, table["muster"], seed + 1, linear(24, 120, 60), linear(230, 230, 220))
    say(table, "muster", "MUSTER  STATION", 46.0, "sans", 0.0, 6.0, 470.0, 1.1, 0.0, white)
    say(table, "muster", "LIFEBOATS  1 & 2", 18.0, "sans", 0.0, -30.0, 400.0, 1.2, 0.0, white)
    for key, label in (("lifeboat_1", "LIFEBOAT  No.1"), ("lifeboat_2", "LIFEBOAT  No.2")):
        stencil_board(canvas, table[key], seed + 2 + len(key), linear(24, 120, 60), linear(230, 230, 220))
        say(table, key, label, 30.0, "sans", 0.0, 0.0, 230.0, 1.1, 0.0, white)
    stencil_board(canvas, table["no_smoking"], seed + 5, linear(226, 222, 212), linear(170, 30, 26))
    say(table, "no_smoking", "NO SMOKING", 32.0, "sans", 0.0, 16.0, 230.0, 1.1, 0.0, (0.5, 0.04, 0.03))
    say(table, "no_smoking", "OR NAKED FLAMES", 18.0, "sans", 0.0, -24.0, 230.0, 1.1, 0.0, (0.05, 0.05, 0.05))
    stencil_board(canvas, table["h2s"], seed + 6, linear(232, 182, 30), linear(30, 30, 30))
    say(table, "h2s", "DANGER", 36.0, "sans", 0.0, 18.0, 230.0, 1.1, 0.0, black)
    say(table, "h2s", "H2S  GAS  AREA", 20.0, "sans", 0.0, -24.0, 230.0, 1.1, 0.0, black)
    stencil_board(canvas, table["fire_point"], seed + 7, linear(176, 30, 26), linear(230, 230, 220))
    say(table, "fire_point", "FIRE  POINT", 38.0, "sans", 0.0, 0.0, 230.0, 1.1, 0.0, white)
    stencil_board(canvas, table["escape"], seed + 8, linear(24, 120, 60), linear(230, 230, 220))
    say(table, "escape", "ESCAPE  ROUTE", 32.0, "sans", 0.0, 10.0, 230.0, 1.1, 0.0, white)
    say(table, "escape", ">>>", 22.0, "sans", 0.0, -26.0, 120.0, 1.3, 0.0, white)
    for key, label in (("control_room", "CENTRAL CONTROL ROOM"), ("radio_room", "RADIO ROOM"), ("medical", "SICK BAY"), ("galley", "GALLEY"), ("mess", "MESS ROOM"), ("lockers", "CHANGING ROOM"), ("office", "OFFICE"), ("workshop", "WORKSHOP")):
        stencil_board(canvas, table[key], seed + 10 + len(label), linear(220, 218, 208), linear(30, 60, 120), 0.04)
        say(table, key, label, 26.0, "sans", 0.0, 0.0, 230.0, 1.08, 0.0, (0.06, 0.12, 0.3))
    stencil_board(canvas, table["stores"], seed + 30, linear(232, 182, 30), linear(30, 30, 30))
    say(table, "stores", "BONDED  STORE", 36.0, "sans", 0.0, 16.0, 350.0, 1.1, 0.0, black)
    say(table, "stores", "AUTHORISED  PERSONNEL  ONLY", 18.0, "sans", 0.0, -26.0, 350.0, 1.1, 0.0, black)
    stencil_board(canvas, table["helideck"], seed + 31, linear(226, 222, 212), linear(170, 30, 26))
    say(table, "helideck", "HELIDECK", 34.0, "sans", 0.0, 16.0, 350.0, 1.1, 0.0, (0.5, 0.04, 0.03))
    say(table, "helideck", "NO ACCESS WHEN ROTORS TURNING", 16.0, "sans", 0.0, -26.0, 350.0, 1.05, 0.0, black)
    stencil_board(canvas, table["cellar_level"], seed + 32, linear(232, 182, 30), linear(30, 30, 30))
    say(table, "cellar_level", "CELLAR DECK  +16M", 24.0, "sans", 0.0, 0.0, 236.0, 1.05, 0.0, black)
    stencil_board(canvas, table["main_level"], seed + 33, linear(232, 182, 30), linear(30, 30, 30))
    say(table, "main_level", "MAIN DECK  +24M", 24.0, "sans", 0.0, 0.0, 236.0, 1.05, 0.0, black)
    console_panel(canvas, table["console"], seed + 40, rng)
    mimic_panel(canvas, table["mimic"], seed + 41, rng)
    screen_face(canvas, table["screen_a"], seed + 42, False)
    screen_face(canvas, table["screen_b"], seed + 43, True)
    stencil_board(canvas, table["esd"], seed + 44, linear(220, 216, 204), linear(40, 40, 40), 0.03)
    sub, lu, lv, w, h = tl.window_of(table["esd"])
    for index, (cx, cy) in enumerate(((64.0, 70.0), (128.0, 70.0), (192.0, 70.0))):
        canvas.albedo[sub] = mix(canvas.albedo[sub], linear(190, 26, 20), tl.ellipse_mask(lu, lv, cx, cy, 22.0, 22.0, 1.0))
        canvas.albedo[sub] = mix(canvas.albedo[sub], linear(232, 182, 30), np.clip(tl.ellipse_mask(lu, lv, cx, cy, 30.0, 30.0, 1.0) - tl.ellipse_mask(lu, lv, cx, cy, 23.0, 23.0, 1.0), 0.0, 1.0))
    say(table, "esd", "EMERGENCY SHUTDOWN", 18.0, "sans", 0.0, 50.0, 230.0, 1.05, 0.0, black)
    for index, label in enumerate(("ESD 1", "ESD 2", "ABANDON")):
        say(table, "esd", label, 11.0, "sans", -64.0 + index * 64.0, -38.0, 60.0, 1.0, 0.0, black)
    for key, label in (("leg_a1", "A1"), ("leg_a2", "A2"), ("leg_b1", "B1"), ("leg_b2", "B2")):
        stencil_board(canvas, table[key], seed + 50 + len(key), linear(232, 182, 30), linear(232, 182, 30), 0.1)
        say(table, key, label, 50.0, "stencil", 0.0, 0.0, 110.0, 1.1, 0.0, black)
    sub, lu, lv, w, h = tl.window_of(table["radio_face"])
    face = linear(46, 52, 50) * (0.9 + 0.15 * unit(field(seed + 60, 3.0, 60.0)[sub]))[:, :, None]
    for index in range(6):
        cx = 30.0 + index * 40.0
        face = mix(face, linear(30, 30, 30), tl.ellipse_mask(lu, lv, cx, 30.0, 12.0, 12.0, 0.8))
        face = mix(face, linear(200, 200, 190), tl.rect_mask(lu, lv, cx - 1.5, 30.0, cx + 1.5, 40.0, 0.5))
    face = mix(face, linear(220, 190, 110), tl.rect_mask(lu, lv, 20.0, 56.0, w - 20.0, 84.0, 1.0))
    face = mix(face, linear(30, 30, 30), tl.rect_mask(lu, lv, 24.0, 68.0, w - 24.0, 70.0, 0.4))
    canvas.albedo[sub] = face
    canvas.rough[sub] = 0.5
    sub, lu, lv, w, h = tl.window_of(table["chart"])
    tl.paper(canvas, table["chart"], seed + 70, linear(220, 214, 196), 0.7)
    say(table, "chart", "PERMIT TO WORK - ISSUED  14 / 03", 16.0, "typewriter", 0.0, 12.0, 360.0, 1.0, 0.0, (0.1, 0.1, 0.12))
    say(table, "chart", "AREA AUTHORITY: ________   ISOLATIONS: 4", 12.0, "typewriter", 0.0, -14.0, 360.0, 1.0, 0.0, (0.1, 0.1, 0.12))
    stencil_board(canvas, table["danger"], seed + 80, linear(232, 182, 30), linear(30, 30, 30))
    say(table, "danger", "DANGER  -  HIGH VOLTAGE  -  KEEP OUT", 22.0, "sans", 0.0, 0.0, 370.0, 1.05, 0.0, black)
    mask, layer, weight = canvas.ink(table)
    worn = cover(field(seed + 90, 4.0, 200.0, 1.7), 0.12, 0.05)
    canvas.albedo = mix(canvas.albedo, layer, mask * weight * (1.0 - worn * 0.7))
    canvas.height += mask * weight * 0.0002
    occlusion = 1.0 - 0.3 * cavity(canvas.height, 1.5, 0.0006)
    gx, gy = rk.gradient_of(canvas.height, 1.0 / size)
    save("rig_signs", canvas.albedo, np.clip(canvas.rough, 0.05, 1.0), occlusion, gradient=(gx, gy), metal=canvas.metal)


makers = {
    "paints": make_paints,
    "rig_deck_green": make_deck,
    "rig_rust": make_rust,
    "rig_marine": make_marine,
    "rig_grating": make_grating,
    "rig_net": make_net,
    "rig_lifeboat": make_lifeboat,
    "rig_rubber": make_rubber,
    "rig_wall": make_wall,
    "rig_ceiling": make_ceiling,
    "rig_vinyl": make_vinyl,
    "rig_steel": make_steel,
    "rig_mark_white": make_marking,
    "rig_decals": make_decals,
    "rig_signs": make_signs,
    "rig_cardboard": make_cardboard,
}


def build(names=None):
    register()
    os.makedirs(preview_root, exist_ok=True)
    for name, maker in makers.items():
        if not names or name in names:
            maker()
    rk.write_sheet(os.path.join(preview_root, "library_rig.png"))
    print("RIG LIBRARY DONE", len(rk.swatches), "sets", flush=True)
