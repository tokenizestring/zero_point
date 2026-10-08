import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
from buildkit import linear, field, unit, sstep, cover, patchy, blur, speckle, mix, tint, flat, cavity

size = kit.size
grid_u = kit.grid_u
grid_v = kit.grid_v
library_root = kit.library_root
tau = math.pi * 2.0

metal_regions = {"green": [0.0, 0.25, 0.0, 1.0], "cream": [0.25, 0.5, 0.0, 1.0], "red": [0.5, 0.75, 0.0, 1.0], "blue": [0.75, 1.0, 0.0, 1.0]}

town_catalog = {
    "town_print": {"tile": 1.0, "kind": "atlas"},
    "town_signs": {"tile": 1.0, "kind": "atlas"},
    "town_tiles": {"tile": 0.6, "kind": "world"},
    "town_quarry": {"tile": 0.9, "kind": "world"},
    "town_stripe": {"tile": 1.0, "kind": "world"},
    "town_carpet": {"tile": 1.0, "kind": "world"},
    "town_brass": {"tile": 0.5, "kind": "local"},
    "town_metal": {"tile": 1.0, "kind": "regions", "regions": metal_regions},
    "town_lino": {"tile": 2.0, "kind": "world"},
}
rail_sets = {"leather_brown": {"tile": 0.6, "kind": "local"}, "rust_iron": {"tile": 1.0, "kind": "local"}, "chequer_plate": {"tile": 1.0, "kind": "local"}}
painted_seeds = {"painted_wood_white": 1720, "painted_wood_bauxite": 1740}
town_paints = {
    "town_paint_green": (linear(34, 62, 44), linear(150, 140, 118), 1760),
    "town_paint_navy": (linear(30, 40, 72), linear(150, 146, 136), 1770),
    "town_paint_black": (linear(28, 28, 27), linear(130, 124, 116), 1780),
    "town_paint_cream": (linear(214, 198, 156), linear(150, 140, 120), 1790),
    "town_paint_red": (linear(128, 32, 26), linear(150, 130, 116), 1810),
}

prints = {
    "newspaper": (0, 672, 256, 1024),
    "notice": (256, 672, 512, 1024),
    "poster": (512, 672, 768, 1024),
    "letter": (768, 832, 896, 1024),
    "envelope": (896, 960, 1024, 1024),
    "card": (896, 832, 1024, 960),
    "calendar": (768, 672, 896, 832),
    "portrait_a": (896, 672, 1024, 832),
    "spines": (0, 448, 512, 576),
    "portrait_b": (512, 448, 608, 576),
    "seascape": (608, 448, 832, 576),
    "ship": (832, 448, 1024, 576),
    "chalkboard": (0, 192, 512, 448),
    "harbour": (512, 320, 768, 448),
    "map": (768, 320, 1024, 448),
    "clock": (512, 192, 640, 320),
    "dartboard": (640, 192, 768, 320),
    "hymns": (768, 192, 896, 320),
    "music": (896, 192, 1024, 320),
    "enamel_tea": (0, 96, 256, 192),
    "enamel_smoke": (0, 0, 256, 96),
    "enamel_soap": (256, 96, 512, 192),
    "enamel_oil": (256, 0, 512, 96),
    "medicine": (512, 96, 768, 192),
    "menu": (768, 96, 1024, 192),
    "police_notice": (512, 0, 768, 96),
    "cards": (768, 0, 1024, 96),
}
label_names = ["peas", "beans", "peaches", "beef", "soup", "sardines", "milk", "cocoa", "jam", "marmalade", "pickles", "honey", "ale", "stout", "gin", "cider"]
for number, key in enumerate(label_names):
    prints["label_" + key] = (128 * (number % 8), 624 - 48 * (number // 8), 128 * (number % 8) + 128, 672 - 48 * (number // 8))
for number in range(16):
    prints["spine_" + str(number)] = (32 * number, 448, 32 * number + 32, 576)
for number in range(4):
    prints["medicine_" + str(number)] = (512 + 64 * number, 96, 576 + 64 * number, 192)
    prints["card_" + str(number)] = (768 + 64 * number, 0, 832 + 64 * number, 96)

signs = {
    "shop_fascia": (0, 928, 1024, 1024),
    "pub_fascia": (0, 832, 1024, 928),
    "garage_fascia": (0, 736, 1024, 832),
    "fuel_fascia": (0, 640, 1024, 736),
    "pub_board": (0, 576, 512, 640),
    "police_board": (512, 576, 1024, 640),
    "clinic_plate": (0, 448, 192, 576),
    "clinic_board": (192, 448, 704, 576),
    "school_plaque": (704, 448, 1024, 576),
    "hall_plaque": (0, 320, 256, 448),
    "church_board": (512, 192, 832, 448),
    "pub_sign": (0, 0, 256, 320),
    "hall_clock": (256, 64, 512, 320),
    "police_lamp": (832, 320, 1024, 448),
    "fuel_globe": (832, 192, 1024, 320),
    "flats_plaque": (512, 64, 832, 192),
    "shop_window": (256, 320, 512, 448),
    "garage_door": (832, 64, 1024, 192),
    "open_sign": (512, 0, 704, 64),
    "pump_plate": (704, 0, 1024, 64),
    "fuel_board": (256, 0, 512, 64),
}


def register():
    kit.load_catalog()
    for name, entry in town_catalog.items():
        kit.catalog.setdefault(name, entry)
    for name, entry in rail_sets.items():
        kit.catalog.setdefault(name, entry)
    for name, seed in painted_seeds.items():
        kit.catalog.setdefault(name, {"tile": 1.0, "kind": "boards", "boards": kit.board_layout(np.random.default_rng(seed), 1.0, 0.09, 0.16)})
    for name, (paint, primer, seed) in town_paints.items():
        kit.catalog.setdefault(name, {"tile": 1.0, "kind": "boards", "boards": kit.board_layout(np.random.default_rng(seed), 1.0, 0.09, 0.16)})
    return kit.catalog


def region_uv(table, key, margin=1.0):
    x0, y0, x1, y1 = table[key]
    return ((x0 + margin) / size, (x1 - margin) / size, (y0 + margin) / size, (y1 - margin) / size)


def read_pixels(path):
    image = kit.bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    data = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    kit.bpy.data.images.remove(image)
    return data.reshape(height, width, 4).astype(np.float64)


font_files = {
    "sans": ("GILB____.TTF", "arialbd.ttf"),
    "serif": ("timesbd.ttf", "georgiab.ttf"),
    "slab": ("ROCKB.TTF", "timesbd.ttf"),
    "engraved": ("ENGR.TTF", "timesbd.ttf"),
    "condensed": ("BERNHC.TTF", "arialbd.ttf"),
    "algerian": ("ALGER.TTF", "timesbd.ttf"),
    "script": ("BRUSHSCI.TTF", "timesbd.ttf"),
    "hand": ("Inkfree.ttf", "segoepr.ttf", "LHANDW.TTF"),
    "chalk": ("LHANDW.TTF", "segoepr.ttf"),
    "gothic": ("OLDENGL.TTF", "timesbd.ttf"),
    "titling": ("PERTIBD.TTF", "timesbd.ttf"),
    "copper": ("COPRGTB.TTF", "arialbd.ttf"),
    "bodoni": ("BOD_B.TTF", "timesbd.ttf"),
    "playbill": ("PLAYBILL.TTF", "BERNHC.TTF"),
    "stencil": ("STENCIL.TTF", "arialbd.ttf"),
    "elephant": ("ELEPHNT.TTF", "timesbd.ttf"),
    "castellar": ("CASTELAR.TTF", "timesbd.ttf"),
    "typewriter": ("courbd.ttf", "cour.ttf", "timesbd.ttf"),
    "goudy": ("GOUDOSB.TTF", "timesbd.ttf"),
}


def text_mask(items, resolution=2048, temporary_name="town_mask.tmp.png"):
    bpy = kit.bpy
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
    for key, files in font_files.items():
        for entry in files:
            if os.path.exists(os.path.join(folder, entry)):
                fonts[key] = bpy.data.fonts.load(os.path.join(folder, entry))
                break
    created = []
    for item in items:
        body, font, cx, cy, cap, limit, spacing, angle = item
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
        obj.rotation_euler = (0.0, 0.0, angle)
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
    temporary = os.path.join(library_root, temporary_name)
    scene.render.filepath = temporary
    bpy.ops.render.render(write_still=True)
    mask = np.clip(read_pixels(temporary)[:, :, 0], 0.0, 1.0)
    os.remove(temporary)
    factor = mask.shape[0] // size
    return mask.reshape(size, factor, size, factor).mean(axis=(1, 3)) if factor > 1 else mask


class Canvas:
    def __init__(self, color, rough=0.85):
        self.albedo = flat(color)
        self.rough = np.full((size, size), rough)
        self.height = np.zeros((size, size))
        self.metal = np.zeros((size, size))
        self.items = []
        self.inks = []

    def say(self, table, key, body, cap, font="serif", dx=0.0, dy=0.0, limit=None, spacing=1.0, angle=0.0, ink=(0.04, 0.035, 0.03), strength=0.92):
        x0, y0, x1, y1 = table[key]
        self.items.append((body, font, (x0 + x1) * 0.5 + dx, (y0 + y1) * 0.5 + dy, cap, limit if limit is not None else (x1 - x0) * 0.88, spacing, angle))
        self.inks.append((table[key], ink, strength))

    def ink(self, mask_table):
        mask = text_mask(self.items) if self.items else np.zeros((size, size))
        layer = np.zeros((size, size, 3))
        weight = np.zeros((size, size))
        for (x0, y0, x1, y1), color, strength in self.inks:
            sub = (slice(y0, y1), slice(x0, x1))
            layer[sub] = np.asarray(color)
            weight[sub] = strength
        return mask, layer, weight


def window_of(box):
    x0, y0, x1, y1 = box
    sub = (slice(y0, y1), slice(x0, x1))
    return sub, grid_u[sub] - x0, grid_v[sub] - y0, x1 - x0, y1 - y0


def rect_mask(lu, lv, a0, b0, a1, b1, soft=0.6):
    return sstep(a0 - soft, a0 + soft, lu) * sstep(a1 + soft, a1 - soft, lu) * sstep(b0 - soft, b0 + soft, lv) * sstep(b1 + soft, b1 - soft, lv)


def ellipse_mask(lu, lv, cx, cy, rx, ry, soft=1.0):
    d = np.hypot((lu - cx) / max(rx, 1e-6), (lv - cy) / max(ry, 1e-6))
    return sstep(1.0 + soft / max(min(rx, ry), 1e-6), 1.0 - soft / max(min(rx, ry), 1e-6), d)


def radial_ticks(theta, r, count, width):
    period = tau * np.maximum(r, 1.0) / count
    distance = np.abs(((theta / tau * count + 0.5) % 1.0) - 0.5) * period
    return sstep(width + 0.5, width - 0.5, distance)


def soften(image):
    total = image * 4.0
    for axis in (0, 1):
        for shift in (-1, 1):
            total = total + np.roll(image, shift, axis)
    return total / 8.0


def paper(canvas, box, seed, color, age=0.5, fold=False, foxing=0.5):
    sub, lu, lv, w, h = window_of(box)
    base = flat(color)[sub] * (0.9 + 0.12 * unit(field(seed, 2.0, 50.0, 2.0)[sub]))[:, :, None]
    edge = np.minimum(np.minimum(lu, w - lu), np.minimum(lv, h - lv))
    yellow = sstep(14.0, 0.0, edge) * age + unit(field(seed + 1, 1.5, 20.0, 2.2)[sub]) * age * 0.5
    base = mix(base, base * np.array([0.86, 0.76, 0.56]), np.clip(yellow, 0.0, 1.0) * 0.6)
    stain_field = field(seed + 2, 1.5, 30.0, 2.2)[sub]
    level = float(np.quantile(stain_field, 0.9))
    stain = sstep(level - 0.15, level + 0.1, stain_field) * age
    ring = sstep(0.1, 0.0, np.abs(stain_field - level)) * age
    base = mix(base, base * np.array([0.8, 0.68, 0.48]), stain * 0.5)
    base = mix(base, base * np.array([0.55, 0.45, 0.32]), ring * 0.5)
    spots = cover(speckle(seed + 3, 1.2), 0.03 * foxing, 0.3)[sub]
    base = mix(base, linear(130, 90, 50), spots * 0.6 * age)
    height = field(seed + 4, 2.0, 80.0, 2.0)[sub] * 0.0003
    if fold:
        crease = np.maximum(sstep(1.5, 0.0, np.abs(lu - w * 0.5)), sstep(1.5, 0.0, np.abs(lv - h * 0.5)))
        base = mix(base, base * 0.78, crease * 0.6)
        height = height - crease * 0.0004
    canvas.albedo[sub] = base
    canvas.rough[sub] = 0.86 + 0.06 * unit(field(seed + 5, 3.0, 60.0)[sub])
    canvas.height[sub] = height
    return sub, lu, lv, w, h


def bars(canvas, box, seed, x0, x1, y0, y1, line=2.0, gap=2.4, color=(0.18, 0.17, 0.16), columns=1, gutter=6.0, ragged=0.3):
    sub, lu, lv, w, h = window_of(box)
    rng = np.random.default_rng(seed)
    width = (x1 - x0 - gutter * (columns - 1)) / columns
    for column in range(columns):
        cx0 = x0 + column * (width + gutter)
        y = y1 - line
        while y > y0:
            end = cx0 + width * (rng.uniform(0.3, 0.8) if rng.random() < ragged * 0.4 else rng.uniform(0.92, 1.0))
            stroke = rect_mask(lu, lv, cx0, y, end, y + line, 0.4) * (0.55 + 0.45 * unit(speckle(seed + column, 0.6)[sub]))
            canvas.albedo[sub] = mix(canvas.albedo[sub], np.asarray(color), stroke * 0.85)
            y -= line + gap
            if rng.random() < 0.08:
                y -= line + gap


def halftone(canvas, box, seed, x0, y0, x1, y1, scene=None):
    sub, lu, lv, w, h = window_of(box)
    inside = rect_mask(lu, lv, x0, y0, x1, y1)
    tone = unit(field(seed, 1.0, 20.0, 2.0)[sub] * 1.2)
    if scene is not None:
        tone = scene(lu, lv)
    dots = 0.5 + 0.5 * np.sin(lu * 2.2) * np.sin(lv * 2.2)
    ink = sstep(tone - 0.1, tone + 0.1, dots)
    canvas.albedo[sub] = mix(canvas.albedo[sub], linear(40, 38, 36), inside * (1.0 - ink) * 0.85)


def sepia_portrait(canvas, box, seed, woman=False):
    sub, lu, lv, w, h = window_of(box)
    cx = w * 0.5
    back = mix(linear(150, 124, 92), linear(96, 76, 56), sstep(0.0, h, lv) * 0.5 + 0.3 * unit(field(seed, 1.5, 12.0, 2.0)[sub]))
    body_top = h * 0.36
    shoulders = ellipse_mask(lu, lv, cx, body_top - h * 0.14, w * 0.42, h * 0.26)
    head = ellipse_mask(lu, lv, cx, h * 0.58, w * 0.17, h * 0.17)
    neck = rect_mask(lu, lv, cx - w * 0.07, body_top - 0.05 * h, cx + w * 0.07, h * 0.48)
    hair = ellipse_mask(lu, lv, cx, h * 0.66 + (h * 0.01 if woman else 0.0), w * (0.2 if woman else 0.18), h * (0.13 if woman else 0.1)) * sstep(h * 0.64, h * 0.69, lv)
    if woman:
        hair = np.maximum(hair, ellipse_mask(lu, lv, cx, h * 0.77, w * 0.1, h * 0.05))
        hair = np.maximum(hair, ellipse_mask(lu, lv, cx - w * 0.17, h * 0.58, w * 0.05, h * 0.1) + ellipse_mask(lu, lv, cx + w * 0.17, h * 0.58, w * 0.05, h * 0.1))
    skin = linear(196, 164, 128) * (0.9 + 0.1 * unit(field(seed + 1, 3.0, 30.0)[sub]))[:, :, None]
    cloth = linear(46, 38, 32) if not woman else linear(84, 66, 52)
    image = mix(back, cloth, shoulders)
    image = mix(image, skin, np.maximum(neck, head) * (1.0 - shoulders * 0.6))
    image = mix(image, linear(52, 40, 30), hair)
    eyes = np.maximum(ellipse_mask(lu, lv, cx - w * 0.06, h * 0.6, w * 0.022, h * 0.012), ellipse_mask(lu, lv, cx + w * 0.06, h * 0.6, w * 0.022, h * 0.012))
    image = mix(image, linear(60, 46, 36), eyes * 0.8)
    image = mix(image, linear(120, 86, 70), ellipse_mask(lu, lv, cx, h * 0.515, w * 0.04, h * 0.01) * 0.6)
    if not woman:
        image = mix(image, linear(220, 210, 190), rect_mask(lu, lv, cx - w * 0.05, body_top - h * 0.08, cx + w * 0.05, body_top + h * 0.02) * 0.8)
    oval = ellipse_mask(lu, lv, cx, h * 0.5, w * 0.44, h * 0.46, 2.0)
    mount = linear(206, 196, 170) * (0.9 + 0.1 * unit(field(seed + 2, 2.0, 40.0)[sub]))[:, :, None]
    image = soften(soften(image))
    image = mix(mount, image, oval)
    image = mix(image, image * np.array([0.7, 0.62, 0.5]), cover(field(seed + 3, 2.0, 40.0)[sub], 0.2, 0.5) * 0.5)
    canvas.albedo[sub] = image * (0.92 + 0.12 * unit(speckle(seed + 4, 0.7)[sub]))[:, :, None]
    canvas.rough[sub] = np.where(oval > 0.5, 0.35, 0.8)


def painting(canvas, box, seed, kind):
    sub, lu, lv, w, h = window_of(box)
    s = lv / h
    t = lu / w
    n1 = field(seed, 2.0, 40.0, 2.0)[sub]
    n2 = field(seed + 1, 6.0, 120.0, 1.7)[sub]
    horizon = 0.45 + 0.02 * np.sin(t * 9.0)
    sky = mix(linear(150, 160, 170), linear(214, 196, 160), sstep(1.0, horizon, s))
    clouds = cover(field(seed + 2, 1.5, 18.0, 2.2, 1.0, 2.5)[sub], 0.35, 0.6) * sstep(horizon, 1.0, s)
    sky = mix(sky, linear(230, 224, 210), clouds * 0.6)
    sea_top = linear(70, 96, 104) if kind != "ship" else linear(46, 58, 62)
    sea = mix(sea_top, linear(30, 50, 56), sstep(horizon, 0.0, s))
    streak = unit(field(seed + 3, 1.0, 60.0, 1.8, 3.0, 0.15)[sub])
    sea = mix(sea, linear(180, 190, 186), sstep(0.75, 0.95, streak) * 0.4)
    image = np.where((s > horizon)[:, :, None], sky, sea)
    if kind == "seascape":
        cliff = (s < horizon + 0.25 * sstep(0.35, 0.0, t) + 0.05 * n1) & (t < 0.38)
        image = np.where(cliff[:, :, None], mix(linear(80, 70, 52), linear(60, 76, 44), unit(n2)), image)
        hull = rect_mask(lu, lv, w * 0.62, h * (horizon - 0.06), w * 0.72, h * (horizon - 0.03))
        sail = (lu > w * 0.66) & (lu < w * 0.66 + (lv - h * (horizon - 0.03)) * -0.0 + w * 0.05 * (1.0 - (lv - h * (horizon - 0.03)) / (h * 0.25))) & (lv > h * (horizon - 0.03)) & (lv < h * (horizon + 0.22))
        image = mix(image, linear(40, 30, 24), hull)
        image = np.where(sail[:, :, None], linear(226, 220, 200), image)
    elif kind == "ship":
        sky_dark = mix(linear(60, 66, 70), linear(150, 130, 100), sstep(horizon, 1.0, s) * unit(n1))
        image = np.where((s > horizon)[:, :, None], sky_dark, image)
        base = h * (horizon - 0.08)
        hull = rect_mask(lu, lv, w * 0.3, base, w * 0.72, base + h * 0.07) * sstep(w * 0.26, w * 0.34, lu + (lv - base) * 0.6)
        image = mix(image, linear(30, 22, 18), hull)
        for mast in (0.4, 0.52, 0.64):
            image = mix(image, linear(30, 22, 18), rect_mask(lu, lv, w * mast - 0.8, base + h * 0.06, w * mast + 0.8, base + h * 0.48))
            for level, span in ((0.12, 0.09), (0.24, 0.075), (0.35, 0.055)):
                image = mix(image, linear(196, 184, 156), rect_mask(lu, lv, w * (mast - span * 0.5), base + h * level, w * (mast + span * 0.5), base + h * (level + 0.09)) * 0.95)
    else:
        quay = h * (horizon + 0.02)
        image = np.where((lv < quay)[:, :, None], image, sky)
        x = 0.0
        rng = np.random.default_rng(seed + 9)
        colors = [linear(214, 190, 150), linear(200, 160, 140), linear(170, 186, 190), linear(220, 214, 196), linear(186, 140, 110)]
        while x < w:
            bw = rng.uniform(w * 0.07, w * 0.13)
            bh = rng.uniform(h * 0.16, h * 0.28)
            house = rect_mask(lu, lv, x, quay, x + bw, quay + bh)
            image = mix(image, colors[rng.integers(0, len(colors))] * rng.uniform(0.8, 1.05), house)
            roof = rect_mask(lu, lv, x - 1, quay + bh, x + bw + 1, quay + bh + h * 0.04)
            image = mix(image, linear(70, 72, 80), roof)
            for wx in np.arange(x + bw * 0.2, x + bw * 0.8, bw * 0.3):
                for wy in (quay + bh * 0.25, quay + bh * 0.6):
                    image = mix(image, linear(40, 44, 50), rect_mask(lu, lv, wx, wy, wx + bw * 0.12, wy + bh * 0.16))
            x += bw + 1.0
        wall = rect_mask(lu, lv, 0, quay - h * 0.06, w, quay)
        image = mix(image, linear(140, 120, 100), wall)
        for boat in range(3):
            bx = w * (0.15 + 0.3 * boat + rng.uniform(-0.05, 0.05))
            image = mix(image, linear(rng.integers(60, 200), 50, 40), rect_mask(lu, lv, bx, h * 0.18, bx + w * 0.1, h * 0.24))
    image = image * (0.88 + 0.16 * unit(n2))[:, :, None]
    strokes_field = field(seed + 7, 2.0, 300.0, 1.4, 1.0, 0.3)[sub]
    image = image * (0.94 + 0.08 * unit(strokes_field))[:, :, None]
    varnish = mix(image, image * np.array([0.84, 0.74, 0.52]), 0.35 + 0.2 * unit(n1))
    canvas.albedo[sub] = varnish
    craquelure = kit.cracks(seed + 8, 40, 0.5, 0.9)[sub]
    canvas.albedo[sub] = mix(canvas.albedo[sub], canvas.albedo[sub] * 0.6, craquelure * 0.5)
    canvas.rough[sub] = 0.45 + 0.2 * unit(n1)
    canvas.height[sub] = strokes_field * 0.0002 - craquelure * 0.0002


def make_print():
    seed = 7100
    canvas = Canvas(linear(200, 190, 164))
    say = canvas.say
    table = prints
    navy = (0.02, 0.025, 0.06)
    black = (0.03, 0.028, 0.025)
    red = (0.36, 0.03, 0.02)
    sub, lu, lv, w, h = paper(canvas, table["newspaper"], seed, linear(196, 188, 160), 0.7, True)
    say(table, "newspaper", "The Island Gazette", 26.0, "gothic", 0.0, 150.0, 236.0)
    say(table, "newspaper", "ST AUBIN  -  FRIDAY  -  ONE PENNY", 7.0, "serif", 0.0, 128.0, 230.0)
    say(table, "newspaper", "ISLAND TO BE", 24.0, "condensed", 0.0, 102.0, 236.0)
    say(table, "newspaper", "EVACUATED", 30.0, "condensed", 0.0, 74.0, 236.0)
    say(table, "newspaper", "LAST BOATS LEAVE SATURDAY", 10.0, "serif", 0.0, 52.0, 236.0)
    for line_v in (119.0, 136.0, 41.0):
        canvas.albedo[sub] = mix(canvas.albedo[sub], linear(40, 38, 34), rect_mask(lu, lv, 8, h * 0.5 + line_v - 0.8, w - 8, h * 0.5 + line_v + 0.8))
    halftone(canvas, table["newspaper"], seed + 11, 10, 150, 150, 215)
    bars(canvas, table["newspaper"], seed + 12, 156, 246, 150, 215, 2.0, 2.6)
    bars(canvas, table["newspaper"], seed + 13, 10, 246, 12, 144, 2.0, 2.6, columns=3)
    paper(canvas, table["notice"], seed + 20, linear(212, 202, 172), 0.6, True)
    sub, lu, lv, w, h = window_of(table["notice"])
    border = rect_mask(lu, lv, 12, 12, w - 12, h - 12) - rect_mask(lu, lv, 15, 15, w - 15, h - 15)
    canvas.albedo[sub] = mix(canvas.albedo[sub], linear(30, 28, 26), np.clip(border, 0.0, 1.0) * 0.9)
    for body, cap, font, dy in (("NOTICE", 40.0, "titling", 140.0), ("BY ORDER OF THE PARISH", 11.0, "serif", 108.0), ("ALL RESIDENTS OF", 14.0, "serif", 76.0), ("SAINT AUBIN", 22.0, "titling", 52.0), ("MUST LEAVE THE ISLAND", 14.0, "serif", 26.0), ("BY THE LAST BOAT", 14.0, "serif", 4.0), ("SATURDAY  6 P.M.", 16.0, "condensed", -22.0), ("One case for each person.", 10.0, "serif", -54.0), ("Leave every door unlocked.", 10.0, "serif", -72.0), ("Turn all livestock out.", 10.0, "serif", -90.0), ("God save the King.", 10.0, "serif", -112.0), ("HARBOUR OFFICE", 11.0, "titling", -144.0)):
        say(table, "notice", body, cap, font, 0.0, dy, 210.0)
    paper(canvas, table["poster"], seed + 30, linear(176, 196, 206), 0.5, False)
    for body, cap, font, dy, ink in (("ST AUBIN", 26.0, "playbill", 136.0, navy), ("REGATTA", 54.0, "playbill", 92.0, red), ("SATURDAY 14th AUGUST", 13.0, "serif", 48.0, navy), ("SAILING  -  ROWING", 13.0, "condensed", 20.0, navy), ("SWIMMING RACES", 13.0, "condensed", 0.0, navy), ("GRAND", 16.0, "playbill", -34.0, red), ("FIREWORKS", 34.0, "playbill", -62.0, red), ("BAND OF THE ISLAND MILITIA", 9.0, "serif", -100.0, navy), ("ADMISSION SIXPENCE", 11.0, "serif", -124.0, navy), ("TEAS ON THE QUAY", 11.0, "serif", -146.0, navy)):
        say(table, "poster", body, cap, font, 0.0, dy, 224.0, 1.0, 0.0, ink)
    paper(canvas, table["letter"], seed + 40, linear(222, 214, 192), 0.5, True)
    sub, lu, lv, w, h = window_of(table["letter"])
    for row in range(14):
        canvas.albedo[sub] = mix(canvas.albedo[sub], linear(150, 170, 196), rect_mask(lu, lv, 6, 18 + row * 12.0, w - 6, 18.6 + row * 12.0) * 0.5)
    for index, body in enumerate(("My dearest Marie,", "The boat leaves on", "Saturday. Take only", "what you can carry.", "I will wait for you", "by the harbour wall", "until the last one.", "All my love,", "Jean")):
        say(table, "letter", body, 10.0, "hand", -6.0 if index < 7 else 8.0, 72.0 - index * 18.0, 118.0, 1.0, 0.0, (0.05, 0.06, 0.16))
    paper(canvas, table["envelope"], seed + 50, linear(196, 172, 124), 0.6)
    sub, lu, lv, w, h = window_of(table["envelope"])
    canvas.albedo[sub] = mix(canvas.albedo[sub], linear(130, 50, 46) * (0.8 + 0.3 * unit(speckle(seed + 51, 0.8)[sub]))[:, :, None], rect_mask(lu, lv, w - 30, h - 34, w - 8, h - 8))
    for radius in (11.0, 14.0):
        ring = sstep(1.2, 0.0, np.abs(np.hypot(lu - (w - 30), lv - (h - 24)) - radius))
        canvas.albedo[sub] = mix(canvas.albedo[sub], linear(40, 36, 40), ring * 0.7)
    for index, body in enumerate(("Mme M. Le Brun", "4 Harbour Row", "St Aubin")):
        say(table, "envelope", body, 8.0, "hand", -14.0, 4.0 - index * 11.0, 90.0, 1.0, 0.0, (0.05, 0.06, 0.16))
    paper(canvas, table["card"], seed + 60, linear(224, 220, 206), 0.4)
    for index, (body, cap) in enumerate((("PARISH OF ST AUBIN", 9.0), ("ALL WATER", 11.0), ("MUST BE BOILED", 11.0), ("BEFORE DRINKING", 11.0), ("by order", 8.0), ("Constable", 8.0))):
        say(table, "card", body, cap, "typewriter", 0.0, 44.0 - index * 18.0, 116.0)
    paper(canvas, table["calendar"], seed + 70, linear(220, 214, 196), 0.5)
    sub, lu, lv, w, h = window_of(table["calendar"])
    picture_box = (table["calendar"][0] + 8, table["calendar"][1] + 84, table["calendar"][2] - 8, table["calendar"][3] - 8)
    painting(canvas, picture_box, seed + 71, "seascape")
    say(table, "calendar", "AUGUST", 11.0, "titling", 0.0, -6.0, 100.0, 1.2, 0.0, red)
    for day in range(31):
        column = (day + 3) % 7
        row = (day + 3) // 7
        say(table, "calendar", str(day + 1), 6.5, "sans", -48.0 + column * 16.0, -22.0 - row * 12.0, 14.0, 1.0, 0.0, red if column == 6 else black)
    ring = sstep(1.3, 0.0, np.abs(np.hypot(lu - (w * 0.5 - 48.0 + 5 * 16.0), lv - (h * 0.5 - 22.0 - 2 * 12.0)) - 7.0))
    canvas.albedo[sub] = mix(canvas.albedo[sub], linear(160, 30, 30), ring * 0.8)
    sepia_portrait(canvas, table["portrait_a"], seed + 80, False)
    sepia_portrait(canvas, table["portrait_b"], seed + 81, True)
    painting(canvas, table["seascape"], seed + 82, "seascape")
    painting(canvas, table["ship"], seed + 83, "ship")
    painting(canvas, table["harbour"], seed + 84, "harbour")
    label_style = {
        "peas": (linear(70, 112, 58), (0.9, 0.86, 0.7), linear(200, 170, 60), "PEAS"),
        "beans": (linear(170, 64, 36), (0.95, 0.9, 0.75), linear(40, 40, 60), "BAKED BEANS"),
        "peaches": (linear(226, 160, 60), (0.45, 0.06, 0.03), linear(120, 40, 30), "PEACHES"),
        "beef": (linear(150, 30, 30), (0.95, 0.88, 0.6), linear(40, 40, 40), "CORNED BEEF"),
        "soup": (linear(220, 210, 180), (0.5, 0.05, 0.03), linear(170, 40, 30), "TOMATO SOUP"),
        "sardines": (linear(48, 70, 120), (0.95, 0.9, 0.7), linear(200, 170, 60), "SARDINES"),
        "milk": (linear(80, 120, 170), (0.98, 0.97, 0.94), linear(230, 230, 220), "COND. MILK"),
        "cocoa": (linear(90, 56, 38), (0.92, 0.8, 0.5), linear(200, 160, 80), "COCOA"),
        "jam": (linear(214, 206, 180), (0.5, 0.04, 0.06), linear(150, 30, 40), "STRAWBERRY JAM"),
        "marmalade": (linear(220, 130, 40), (0.2, 0.06, 0.02), linear(90, 40, 20), "MARMALADE"),
        "pickles": (linear(90, 120, 60), (0.95, 0.92, 0.75), linear(40, 50, 30), "PICKLES"),
        "honey": (linear(200, 160, 70), (0.25, 0.12, 0.02), linear(110, 70, 20), "ISLAND HONEY"),
        "ale": (linear(222, 208, 170), (0.4, 0.04, 0.03), linear(150, 30, 30), "PALE ALE"),
        "stout": (linear(30, 28, 26), (0.85, 0.78, 0.55), linear(180, 150, 80), "STOUT"),
        "gin": (linear(226, 226, 214), (0.06, 0.2, 0.08), linear(40, 100, 50), "DRY GIN"),
        "cider": (linear(60, 96, 50), (0.9, 0.8, 0.42), linear(200, 170, 70), "CIDER"),
    }
    for number, key in enumerate(label_names):
        name = "label_" + key
        ground_color, ink_color, band_color, title = label_style[key]
        sub, lu, lv, w, h = window_of(table[name])
        ground = flat(ground_color)[sub] * (0.88 + 0.16 * unit(field(seed + 100 + number, 3.0, 40.0)[sub]))[:, :, None]
        band = np.maximum(rect_mask(lu, lv, 0, 0, w, 6), rect_mask(lu, lv, 0, h - 6, w, h))
        ground = mix(ground, band_color, band)
        oval = ellipse_mask(lu, lv, w * 0.5, h * 0.5, w * 0.34, h * 0.32) - ellipse_mask(lu, lv, w * 0.5, h * 0.5, w * 0.33, h * 0.3)
        ground = mix(ground, band_color, np.clip(oval, 0.0, 1.0) * 0.8)
        fade = cover(field(seed + 120 + number, 2.0, 40.0)[sub], 0.3, 0.5)
        ground = mix(ground, ground * np.array([0.8, 0.74, 0.62]) + 0.05, fade * 0.5)
        canvas.albedo[sub] = ground
        canvas.rough[sub] = 0.6 + 0.2 * fade
        say(table, name, title, 13.0, "condensed" if number % 3 else "slab", 0.0, 1.0, 92.0, 1.0, 0.0, ink_color)
    spine_colors = [linear(110, 30, 34), linear(36, 46, 82), linear(40, 76, 50), linear(108, 74, 44), linear(28, 26, 26), linear(170, 140, 96), linear(70, 84, 100), linear(130, 60, 40), linear(60, 40, 64), linear(150, 120, 60), linear(90, 30, 30), linear(46, 60, 44), linear(180, 170, 150), linear(56, 50, 70), linear(120, 96, 70), linear(34, 60, 70)]
    titles = ["BLEAK HOUSE", "HYMNS", "ATLAS", "SEA STORIES", "HOLY BIBLE", "COOKERY", "TIDES 1938", "IVANHOE", "POEMS", "GARDENING", "LAW", "BIRDS", "KIDNAPPED", "SERMONS", "FARMING", "NAVIGATION"]
    for number in range(16):
        name = "spine_" + str(number)
        sub, lu, lv, w, h = window_of(table[name])
        cloth = flat(spine_colors[number])[sub] * (0.85 + 0.2 * unit(speckle(seed + 200 + number, 0.7)[sub]))[:, :, None]
        worn = sstep(10.0, 0.0, np.minimum(lv, h - lv)) * 0.5 + cover(field(seed + 220 + number, 2.0, 40.0)[sub], 0.15, 0.5) * 0.4
        cloth = mix(cloth, cloth * 1.5 + 0.05, worn)
        gold = linear(170, 136, 60)
        bands = np.maximum(np.maximum(rect_mask(lu, lv, 3, 12, w - 3, 14), rect_mask(lu, lv, 3, 17, w - 3, 18)), np.maximum(rect_mask(lu, lv, 3, h - 14, w - 3, h - 12), rect_mask(lu, lv, 3, h - 18, w - 3, h - 17)))
        cloth = mix(cloth, gold, bands * (0.8 if number % 4 else 0.0))
        canvas.albedo[sub] = cloth
        canvas.rough[sub] = 0.82
        canvas.height[sub] = speckle(seed + 240 + number, 0.6)[sub] * 0.0001
        say(table, name, titles[number], 9.0, "serif", 0.0, 0.0, 88.0, 1.05, math.pi * 0.5, (0.65, 0.5, 0.2) if number % 4 else (0.9, 0.86, 0.75), 0.85)
    sub, lu, lv, w, h = window_of(table["chalkboard"])
    slate = flat(linear(34, 40, 38))[sub] * (0.85 + 0.25 * unit(field(seed + 300, 2.0, 60.0)[sub]))[:, :, None]
    smear = cover(field(seed + 301, 1.5, 20.0, 2.0, 2.5, 1.0)[sub], 0.35, 0.6)
    slate = mix(slate, linear(110, 116, 112), smear * 0.3)
    frame_band = np.clip(1.0 - rect_mask(lu, lv, 10, 10, w - 10, h - 10), 0.0, 1.0)
    canvas.albedo[sub] = mix(slate, linear(96, 66, 42) * (0.8 + 0.3 * unit(field(seed + 302, 3.0, 300.0, 1.4, 4.0, 0.5)[sub]))[:, :, None], frame_band)
    canvas.rough[sub] = np.where(frame_band > 0.5, 0.6, 0.92)
    chalk = (0.82, 0.83, 0.78)
    for body, cap, dx, dy in (("Monday 11th", 16.0, 150.0, 96.0), ("SPELLING", 22.0, -150.0, 92.0), ("1. harbour", 15.0, -150.0, 60.0), ("2. island", 15.0, -150.0, 36.0), ("3. anchor", 15.0, -150.0, 12.0), ("4. lighthouse", 15.0, -140.0, -12.0), ("5. evacuate", 15.0, -144.0, -36.0), ("7 x 8 = 56", 18.0, 120.0, 40.0), ("9 x 6 = 54", 18.0, 120.0, 10.0), ("12 x 12 = 144", 18.0, 130.0, -20.0), ("Home time 3.30", 14.0, 110.0, -80.0)):
        say(table, "chalkboard", body, cap, "chalk", dx, dy, 240.0, 1.0, 0.0, chalk, 0.75)
    sub, lu, lv, w, h = window_of(table["clock"])
    cx = w * 0.5
    cy = h * 0.5
    r = np.hypot(lu - cx, lv - cy)
    theta = np.arctan2(lv - cy, lu - cx)
    face = linear(226, 220, 200) * (0.92 + 0.08 * unit(field(seed + 310, 2.0, 30.0)[sub]))[:, :, None]
    face = mix(face, face * np.array([0.8, 0.72, 0.56]), cover(field(seed + 311, 2.0, 30.0)[sub], 0.25, 0.5) * 0.5)
    ticks = radial_ticks(theta, r, 60, 0.6) * (r > 52) * (r < 57)
    tick_hours = radial_ticks(theta, r, 12, 1.6) * (r > 46) * (r < 57)
    hands = np.zeros_like(r)
    for angle, length, width in ((math.pi * 0.5 - tau * (10.7 / 12.0), 30.0, 2.4), (math.pi * 0.5 - tau * (42.0 / 60.0), 44.0, 1.6)):
        ax = math.cos(angle)
        ay = math.sin(angle)
        along = (lu - cx) * ax + (lv - cy) * ay
        across = np.abs(-(lu - cx) * ay + (lv - cy) * ax)
        hands = np.maximum(hands, sstep(width + 0.6, width - 0.6, across) * (along > -6.0) * (along < length))
    hands = np.maximum(hands, sstep(5.0, 3.5, r))
    bezel = sstep(1.5, 0.0, np.abs(r - 61.0)) + sstep(60.0, 62.0, r)
    image = mix(face, linear(20, 18, 16), np.clip(ticks + tick_hours + hands, 0.0, 1.0))
    canvas.albedo[sub] = mix(image, linear(120, 92, 46), np.clip(bezel, 0.0, 1.0))
    canvas.rough[sub] = 0.3
    for hour, numeral in enumerate(("XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI")):
        angle = math.pi * 0.5 - tau * hour / 12.0
        say(table, "clock", numeral, 9.0, "serif", math.cos(angle) * 40.0, math.sin(angle) * 40.0, 22.0, 1.0, angle - math.pi * 0.5, black)
    sub, lu, lv, w, h = window_of(table["dartboard"])
    cx = w * 0.5
    cy = h * 0.5
    r = np.hypot(lu - cx, lv - cy) / 48.0
    theta = np.arctan2(lv - cy, lu - cx)
    segment = np.floor(((theta + math.pi / 20.0) % tau) / (tau / 20.0)).astype(np.int64)
    dark = segment % 2 == 0
    sisal = (0.85 + 0.25 * unit(speckle(seed + 320, 0.6)[sub]))[:, :, None]
    board = np.where(dark[:, :, None], linear(26, 24, 22), linear(214, 196, 150)) * sisal
    ring_color = np.where(dark[:, :, None], linear(150, 30, 26), linear(40, 110, 60))
    board = np.where((((r > 0.58) & (r < 0.63)) | ((r > 0.95) & (r < 1.0)))[:, :, None], ring_color, board)
    board = np.where((r < 0.09)[:, :, None], linear(40, 110, 60), board)
    board = np.where((r < 0.04)[:, :, None], linear(150, 30, 26), board)
    board = np.where((r >= 1.0)[:, :, None], linear(20, 20, 20), board)
    wires = sstep(0.012, 0.0, np.abs(r - 0.63)) + sstep(0.012, 0.0, np.abs(r - 1.0)) + sstep(0.012, 0.0, np.abs(r - 0.58)) + sstep(0.012, 0.0, np.abs(r - 0.95))
    board = mix(board, linear(170, 170, 160), np.clip(wires, 0.0, 1.0) * (r < 1.02) * 0.7)
    holes = cover(speckle(seed + 321, 0.6)[sub], 0.06, 0.2)
    board = mix(board, board * 0.5, holes * 0.6)
    canvas.albedo[sub] = board * np.where((r > 1.0)[:, :, None], 1.0, 1.0)
    canvas.rough[sub] = 0.95
    canvas.height[sub] = speckle(seed + 322, 0.6)[sub] * 0.0003 - holes * 0.0004
    for index, number in enumerate((6, 13, 4, 18, 1, 20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10)):
        angle = tau * index / 20.0
        say(table, "dartboard", str(number), 6.0, "sans", math.cos(angle) * 55.0, math.sin(angle) * 55.0, 14.0, 1.0, angle - math.pi * 0.5, (0.9, 0.9, 0.86))
    sub, lu, lv, w, h = window_of(table["hymns"])
    wood = flat(linear(56, 36, 24))[sub] * (0.8 + 0.3 * unit(field(seed + 330, 2.0, 300.0, 1.4, 6.0, 0.5)[sub]))[:, :, None]
    for row in range(4):
        slip = rect_mask(lu, lv, 14, 8 + row * 22.0, w - 14, 26 + row * 22.0)
        wood = mix(wood, linear(22, 20, 18), slip)
    canvas.albedo[sub] = wood
    canvas.rough[sub] = 0.55
    say(table, "hymns", "HYMNS", 11.0, "titling", 0.0, 50.0, 100.0, 1.2, 0.0, (0.7, 0.55, 0.25))
    for row, number in enumerate(("330", "22", "162", "47")):
        say(table, "hymns", number, 15.0, "serif", 0.0, -47.0 + row * 22.0, 80.0, 1.1, 0.0, (0.86, 0.84, 0.78))
    paper(canvas, table["music"], seed + 340, linear(222, 214, 190), 0.6)
    sub, lu, lv, w, h = window_of(table["music"])
    rng = np.random.default_rng(seed + 341)
    for staff in range(5):
        top = h - 26 - staff * 21.0
        for line_index in range(5):
            canvas.albedo[sub] = mix(canvas.albedo[sub], linear(40, 38, 34), rect_mask(lu, lv, 8, top - line_index * 2.6, w - 8, top - line_index * 2.6 + 0.6))
        x = 16.0
        while x < w - 12:
            y = top - rng.integers(0, 9) * 1.3
            canvas.albedo[sub] = mix(canvas.albedo[sub], linear(30, 28, 26), ellipse_mask(lu, lv, x, y - 4.0, 2.0, 1.5, 0.5))
            canvas.albedo[sub] = mix(canvas.albedo[sub], linear(30, 28, 26), rect_mask(lu, lv, x + 1.4, y - 4.0, x + 2.0, y + 6.0, 0.3))
            x += rng.uniform(6.0, 11.0)
    say(table, "music", "HOME, SWEET HOME", 8.0, "serif", 0.0, 56.0, 110.0)
    enamel = {"enamel_tea": (linear(30, 52, 110), (0.92, 0.9, 0.82), "ROYAL ISLE TEA", "sans"), "enamel_smoke": (linear(150, 26, 24), (0.95, 0.8, 0.2), "SEAGULL CIGARETTES", "condensed"), "enamel_soap": (linear(226, 186, 40), (0.05, 0.08, 0.25), "SUNSHINE SOAP", "slab"), "enamel_oil": (linear(30, 90, 50), (0.95, 0.94, 0.88), "SEALION MOTOR OIL", "sans")}
    for key, (ground_color, ink_color, title, font) in enamel.items():
        sub, lu, lv, w, h = window_of(table[key])
        ground = flat(ground_color)[sub] * (0.92 + 0.1 * unit(field(seed + 400, 2.0, 40.0)[sub]))[:, :, None]
        rim = np.clip(1.0 - rect_mask(lu, lv, 6, 6, w - 6, h - 6), 0.0, 1.0)
        ground = mix(ground, np.asarray(ink_color), rim * 0.95)
        chip_field = field(seed + 401, 6.0, 300.0, 1.6)[sub] + 0.5 * sstep(10.0, 0.0, np.minimum(np.minimum(lu, w - lu), np.minimum(lv, h - lv)))
        chips = cover(chip_field, 0.06, 0.05)
        rust = mix(linear(30, 26, 24), linear(110, 56, 26), unit(field(seed + 402, 4.0, 100.0)[sub]))
        canvas.albedo[sub] = mix(ground, rust, chips)
        canvas.rough[sub] = np.where(chips > 0.5, 0.85, 0.22)
        canvas.height[sub] = -chips * 0.0006
        say(table, key, title, 30.0 if len(title) < 15 else 24.0, font, 0.0, 0.0, w * 0.86, 1.0, 0.0, ink_color, 0.95)
    for number, title in enumerate(("ASPIRIN", "IODINE", "QUININE", "MORPHIA")):
        name = "medicine_" + str(number)
        paper(canvas, table[name], seed + 500 + number, linear(232, 228, 214), 0.4)
        sub, lu, lv, w, h = window_of(table[name])
        frame_line = np.clip(rect_mask(lu, lv, 4, 4, w - 4, h - 4) - rect_mask(lu, lv, 6, 6, w - 6, h - 6), 0.0, 1.0)
        canvas.albedo[sub] = mix(canvas.albedo[sub], linear(150, 30, 30), frame_line)
        say(table, name, title, 10.0, "serif", 0.0, 10.0, 56.0, 1.0, 0.0, red)
        say(table, name, "POISON" if number == 3 else "B.P.", 7.0, "sans", 0.0, -14.0, 50.0, 1.0, 0.0, black)
    sub, lu, lv, w, h = window_of(table["menu"])
    slate = flat(linear(30, 34, 32))[sub] * (0.85 + 0.25 * unit(field(seed + 600, 2.0, 60.0)[sub]))[:, :, None]
    canvas.albedo[sub] = mix(slate, linear(80, 56, 36), np.clip(1.0 - rect_mask(lu, lv, 6, 6, w - 6, h - 6), 0.0, 1.0))
    canvas.rough[sub] = 0.92
    for body, cap, dy in (("TODAY", 16.0, 30.0), ("Crab sandwich  1/6", 12.0, 6.0), ("Ploughman's  1/-", 12.0, -14.0), ("Mild  6d   Bitter  7d", 12.0, -34.0)):
        say(table, "menu", body, cap, "chalk", 0.0, dy, 230.0, 1.0, 0.0, chalk, 0.75)
    paper(canvas, table["police_notice"], seed + 610, linear(214, 206, 180), 0.6)
    for body, cap, dy in (("POLICE NOTICE", 18.0, 28.0), ("LOOTERS WILL BE PROSECUTED", 11.0, 4.0), ("Property left behind remains", 8.0, -16.0), ("the property of its owner.", 8.0, -28.0)):
        say(table, "police_notice", body, cap, "titling" if cap > 15 else "serif", 0.0, dy, 236.0)
    for number, (rank, colour) in enumerate((("A", (0.03, 0.03, 0.03)), ("K", (0.5, 0.02, 0.02)), ("Q", (0.03, 0.03, 0.03)), ("7", (0.5, 0.02, 0.02)))):
        name = "card_" + str(number)
        sub, lu, lv, w, h = window_of(table[name])
        card = flat(linear(232, 228, 216))[sub] * (0.9 + 0.1 * unit(field(seed + 620 + number, 2.0, 30.0)[sub]))[:, :, None]
        pip = ellipse_mask(lu, lv, w * 0.5, h * 0.5, 9.0, 11.0) if number % 2 else rect_mask(lu, lv, w * 0.5 - 8, h * 0.5 - 8, w * 0.5 + 8, h * 0.5 + 8)
        card = mix(card, np.asarray(colour) * 3.0, pip)
        card = mix(card, linear(120, 110, 100), np.clip(1.0 - rect_mask(lu, lv, 2, 2, w - 2, h - 2), 0.0, 1.0))
        canvas.albedo[sub] = card
        canvas.rough[sub] = 0.5
        say(table, name, rank, 14.0, "serif", -20.0, 34.0, 20.0, 1.0, 0.0, colour)
        say(table, name, rank, 14.0, "serif", 20.0, -34.0, 20.0, 1.0, math.pi, colour)
    paper(canvas, table["map"], seed + 700, linear(214, 196, 150), 0.7)
    sub, lu, lv, w, h = window_of(table["map"])
    theta = np.arctan2(lv - h * 0.52, (lu - w * 0.5) * 0.6)
    radius = np.hypot((lu - w * 0.5) / (w * 0.36), (lv - h * 0.52) / (h * 0.36))
    shore = 1.0 + 0.12 * np.sin(theta * 3.0 + 1.0) + 0.08 * np.sin(theta * 7.0) + 0.05 * field(seed + 701, 4.0, 40.0)[sub]
    land = radius < shore
    sea_hatch = sstep(0.5, 0.0, np.abs(((lv * 0.6 + lu * 0.2) % 5.0) - 2.5)) * (~land) * sstep(1.6, 1.0, radius / shore)
    image = canvas.albedo[sub]
    image = mix(image, linear(110, 140, 150), sea_hatch * 0.4)
    image = np.where(land[:, :, None], mix(image, linear(170, 176, 120), 0.4), image)
    coast = sstep(0.04, 0.0, np.abs(radius - shore))
    image = mix(image, linear(60, 50, 40), coast * 0.9)
    for a, b, c, d in ((0.3, 0.4, 0.62, 0.5), (0.62, 0.5, 0.78, 0.66), (0.3, 0.4, 0.42, 0.7), (0.42, 0.7, 0.66, 0.74)):
        steps = 40
        for index in range(steps):
            t = index / steps
            px = (a + (c - a) * t) * w
            py = (b + (d - b) * t) * h
            image = mix(image, linear(150, 40, 30), ellipse_mask(lu, lv, px, py, 1.0, 1.0, 0.5) * 0.8)
    canvas.albedo[sub] = image
    for body, dx, dy, cap in (("ST AUBIN", 6.0, -26.0, 8.0), ("GOREY", 72.0, 6.0, 7.0), ("ST OUEN", -82.0, 18.0, 7.0), ("THE ISLAND", 0.0, 50.0, 10.0)):
        say(table, "map", body, cap, "serif", dx, dy, 90.0)
    mask, layer, weight = canvas.ink(table)
    canvas.albedo = mix(canvas.albedo, layer, mask * weight)
    canvas.height -= mask * weight * 0.00005
    occlusion = 1.0 - 0.3 * cavity(canvas.height, 1.5, 0.0003)
    kit.save("town_print", canvas.albedo, canvas.rough, occlusion, canvas.height, 1.0, 1.0, metal=canvas.metal, extra=town_catalog["town_print"])


def painted_board(canvas, box, seed, paint, trim, boards=1, grain=True):
    sub, lu, lv, w, h = window_of(box)
    wood = linear(118, 100, 80) * (0.8 + 0.3 * unit(field(seed, 2.0, 400.0, 1.4, 6.0, 0.4)[sub]))[:, :, None]
    wood = mix(wood, wood * 0.6, sstep(0.55, 0.95, 0.5 + 0.5 * np.sin(lv * 0.45 + field(seed + 1, 1.0, 20.0)[sub] * 3.0))[:, :, None] * 0.5)
    coat = flat(paint)[sub] * (0.9 + 0.12 * unit(field(seed + 2, 2.0, 60.0, 2.0)[sub]))[:, :, None]
    sun = sstep(h * 0.2, h, lv)
    coat = mix(coat, coat * 1.25 + 0.04, (sun * 0.3 + 0.2 * unit(field(seed + 3, 1.5, 20.0)[sub]))[:, :, None] * 0.6)
    flake = cover(field(seed + 4, 4.0, 200.0, 1.7, 3.0, 1.0)[sub] + 0.5 * field(seed + 5, 20.0, 400.0, 1.4)[sub], 0.12, 0.04)
    bare = cover(field(seed + 4, 4.0, 200.0, 1.7, 3.0, 1.0)[sub] + 0.5 * field(seed + 5, 20.0, 400.0, 1.4)[sub], 0.06, 0.04)
    edge = np.minimum(np.minimum(lu, w - lu), np.minimum(lv, h - lv))
    rim = sstep(7.0, 5.0, edge) - sstep(3.0, 1.5, edge)
    image = mix(coat, flat(trim)[sub], np.clip(rim, 0.0, 1.0) * 0.9)
    image = mix(image, linear(170, 160, 140), flake * 0.7)
    image = mix(image, wood, bare)
    joint = np.zeros_like(lu)
    for index in range(1, boards):
        joint = np.maximum(joint, sstep(1.6, 0.4, np.abs(lv - h * index / boards)))
    image = mix(image, linear(20, 18, 16), joint * 0.8)
    streak = cover(field(seed + 6, 2.0, 120.0, 2.0, 1.0, 8.0)[sub], 0.25, 0.4)
    image = mix(image, image * np.array([0.62, 0.58, 0.52]), streak * 0.45)
    mold = cover(speckle(seed + 7, 1.2)[sub], 0.08, 0.3) * cover(field(seed + 8, 2.0, 40.0)[sub], 0.2, 0.4)
    image = mix(image, linear(40, 44, 34), mold * 0.6)
    canvas.albedo[sub] = image
    canvas.rough[sub] = 0.6 + 0.25 * flake + 0.1 * bare
    canvas.height[sub] = (1.0 - flake) * 0.0003 + rim * 0.0015 - joint * 0.002 + field(seed + 9, 3.0, 300.0, 1.4, 6.0, 0.4)[sub] * 0.0002 * bare
    return flake


def enamel_panel(canvas, box, seed, ground_color, rim_color, chip=0.07):
    sub, lu, lv, w, h = window_of(box)
    ground = flat(ground_color)[sub] * (0.94 + 0.08 * unit(field(seed, 2.0, 40.0)[sub]))[:, :, None]
    edge = np.minimum(np.minimum(lu, w - lu), np.minimum(lv, h - lv))
    ground = mix(ground, np.asarray(rim_color), np.clip(sstep(9.0, 7.0, edge) - sstep(4.0, 3.0, edge), 0.0, 1.0))
    chip_field = field(seed + 1, 6.0, 300.0, 1.6)[sub] + 0.5 * sstep(10.0, 0.0, edge)
    chips = cover(chip_field, chip, 0.05)
    rust = mix(linear(30, 26, 24), linear(110, 56, 26), unit(field(seed + 2, 4.0, 100.0)[sub]))
    canvas.albedo[sub] = mix(ground, rust, chips)
    canvas.rough[sub] = np.where(chips > 0.5, 0.85, 0.2)
    canvas.height[sub] = -chips * 0.0006
    return chips


def stone_plaque(canvas, box, seed, color=None):
    sub, lu, lv, w, h = window_of(box)
    base = flat(color if color is not None else linear(150, 142, 132))[sub] * (0.85 + 0.2 * unit(field(seed, 3.0, 120.0, 1.8)[sub]))[:, :, None]
    grains = cover(speckle(seed + 1, 0.8)[sub], 0.08, 0.5)
    base = mix(base, base * 0.6, grains * 0.5)
    crust = patchy(seed + 2, 0.12, 14.0, 300.0, 0.9)[sub]
    base = mix(base, linear(150, 156, 132), crust * 0.6)
    black = patchy(seed + 3, 0.06, 40.0, 400.0, 0.6)[sub]
    base = mix(base, linear(40, 40, 36), black * 0.6)
    streak = cover(field(seed + 4, 2.0, 90.0, 2.0, 1.0, 6.0)[sub], 0.3, 0.4)
    base = tint(base, 1.0 - 0.25 * streak)
    edge = np.minimum(np.minimum(lu, w - lu), np.minimum(lv, h - lv))
    bevel = sstep(10.0, 2.0, edge)
    base = mix(base, base * 1.12, bevel * 0.4)
    canvas.albedo[sub] = base
    canvas.rough[sub] = 0.82
    canvas.height[sub] = field(seed + 5, 6.0, 300.0, 1.6)[sub] * 0.0004 - bevel * 0.002


def make_signs():
    seed = 8100
    canvas = Canvas(linear(60, 58, 54), 0.7)
    say = canvas.say
    table = signs
    gold = (0.62, 0.44, 0.14)
    cream = (0.8, 0.76, 0.62)
    white = (0.9, 0.9, 0.86)
    gilded = []
    incised = []
    painted_board(canvas, table["shop_fascia"], seed, linear(84, 24, 26), linear(40, 34, 30), 2)
    say(table, "shop_fascia", "J. LE CORNU & SON", 46.0, "bodoni", 0.0, 9.0, 760.0, 1.06, 0.0, gold)
    say(table, "shop_fascia", "GROCER  &  PROVISION MERCHANT", 14.0, "bodoni", 0.0, -30.0, 700.0, 1.2, 0.0, gold)
    say(table, "shop_fascia", "Est. 1871", 13.0, "script", -430.0, -4.0, 110.0, 1.0, 0.0, gold)
    say(table, "shop_fascia", "TEAS", 16.0, "bodoni", 430.0, 0.0, 110.0, 1.1, 0.0, gold)
    gilded.append("shop_fascia")
    painted_board(canvas, table["pub_fascia"], seed + 10, linear(26, 52, 36), linear(150, 120, 60), 2)
    say(table, "pub_fascia", "THE OLD ANCHOR", 54.0, "algerian", 0.0, 2.0, 700.0, 1.12, 0.0, cream)
    say(table, "pub_fascia", "ALES", 18.0, "serif", -420.0, 2.0, 120.0, 1.2, 0.0, cream)
    say(table, "pub_fascia", "STOUT", 18.0, "serif", 420.0, 2.0, 120.0, 1.2, 0.0, cream)
    gilded.append("pub_fascia")
    painted_board(canvas, table["garage_fascia"], seed + 20, linear(214, 208, 190), linear(30, 50, 100), 1)
    say(table, "garage_fascia", "ST AUBIN MOTOR WORKS", 44.0, "sans", 0.0, 10.0, 880.0, 1.08, 0.0, (0.04, 0.07, 0.2))
    say(table, "garage_fascia", "REPAIRS  -  PETROL  -  OILS  -  CYCLES  -  CARS FOR HIRE", 14.0, "sans", 0.0, -30.0, 840.0, 1.1, 0.0, (0.35, 0.04, 0.03))
    painted_board(canvas, table["fuel_fascia"], seed + 30, linear(170, 34, 26), linear(220, 190, 60), 1)
    say(table, "fuel_fascia", "ISLE  SERVICE  STATION", 44.0, "condensed", 0.0, 8.0, 860.0, 1.14, 0.0, (0.94, 0.86, 0.5))
    say(table, "fuel_fascia", "MOTOR SPIRIT  -  LUBRICATING OILS  -  TYRES", 14.0, "sans", 0.0, -30.0, 800.0, 1.1, 0.0, (0.94, 0.9, 0.8))
    painted_board(canvas, table["pub_board"], seed + 40, linear(26, 52, 36), linear(150, 120, 60), 1)
    say(table, "pub_board", "FREE HOUSE  -  FINE ALES & SPIRITS", 22.0, "serif", 0.0, 0.0, 460.0, 1.1, 0.0, cream)
    gilded.append("pub_board")
    enamel_panel(canvas, table["police_board"], seed + 50, linear(26, 40, 96), linear(220, 220, 214))
    say(table, "police_board", "POLICE  STATION", 32.0, "sans", 0.0, 0.0, 440.0, 1.18, 0.0, white)
    sub, lu, lv, w, h = window_of(table["clinic_plate"])
    plate = mix(linear(176, 136, 66), linear(140, 104, 50), unit(field(seed + 60, 3.0, 80.0, 1.8)[sub]))
    tarnish = cover(field(seed + 61, 2.0, 60.0, 2.0)[sub], 0.4, 0.5)
    plate = mix(plate, linear(80, 64, 38), tarnish * 0.6)
    verdigris = cover(field(seed + 62, 3.0, 120.0, 1.8)[sub], 0.1, 0.3)
    plate = mix(plate, linear(80, 140, 110), verdigris * 0.7)
    edge = np.minimum(np.minimum(lu, w - lu), np.minimum(lv, h - lv))
    screws = np.zeros_like(lu)
    for sx, sy in ((10.0, 10.0), (w - 10.0, 10.0), (10.0, h - 10.0), (w - 10.0, h - 10.0)):
        screws = np.maximum(screws, ellipse_mask(lu, lv, sx, sy, 4.0, 4.0, 0.6))
    plate = mix(plate, linear(60, 50, 34), screws * 0.8)
    canvas.albedo[sub] = plate
    canvas.rough[sub] = 0.3 + 0.35 * tarnish + 0.4 * verdigris
    canvas.metal[sub] = np.clip(1.0 - verdigris, 0.0, 1.0)
    canvas.height[sub] = sstep(6.0, 1.0, edge) * -0.001 + screws * 0.0008
    for body, cap, dy in (("Dr. J. P. RENOUF", 20.0, 30.0), ("M.B., Ch.B.", 13.0, 4.0), ("PHYSICIAN & SURGEON", 12.0, -22.0), ("Surgery hours 9 - 11", 10.0, -42.0)):
        say(table, "clinic_plate", body, cap, "engraved" if cap < 15.0 else "serif", 0.0, dy, 176.0, 1.0, 0.0, (0.03, 0.025, 0.02))
    incised.append(("clinic_plate", 0.0008))
    painted_board(canvas, table["clinic_board"], seed + 70, linear(30, 46, 60), linear(200, 196, 180), 1)
    say(table, "clinic_board", "ST AUBIN SURGERY", 38.0, "titling", 0.0, 24.0, 470.0, 1.12, 0.0, white)
    say(table, "clinic_board", "Consulting hours  9 - 11 a.m.   5 - 7 p.m.", 15.0, "serif", 0.0, -14.0, 470.0, 1.0, 0.0, white)
    say(table, "clinic_board", "PLEASE RING", 13.0, "sans", 0.0, -40.0, 300.0, 1.2, 0.0, white)
    stone_plaque(canvas, table["school_plaque"], seed + 80)
    say(table, "school_plaque", "PAROCHIAL SCHOOL", 28.0, "titling", 0.0, 22.0, 290.0, 1.1, 0.0, (0.08, 0.075, 0.07))
    say(table, "school_plaque", "1887", 30.0, "titling", 0.0, -24.0, 160.0, 1.3, 0.0, (0.08, 0.075, 0.07))
    incised.append(("school_plaque", 0.0025))
    stone_plaque(canvas, table["hall_plaque"], seed + 90)
    say(table, "hall_plaque", "PARISH HALL", 30.0, "titling", 0.0, 20.0, 230.0, 1.1, 0.0, (0.08, 0.075, 0.07))
    say(table, "hall_plaque", "A.D. 1903", 20.0, "titling", 0.0, -28.0, 170.0, 1.25, 0.0, (0.08, 0.075, 0.07))
    incised.append(("hall_plaque", 0.0025))
    stone_plaque(canvas, table["flats_plaque"], seed + 95, linear(196, 190, 176))
    say(table, "flats_plaque", "HARBOUR VIEW", 34.0, "sans", 0.0, 16.0, 300.0, 1.2, 0.0, (0.08, 0.075, 0.07))
    say(table, "flats_plaque", "1936", 26.0, "sans", 0.0, -28.0, 140.0, 1.6, 0.0, (0.08, 0.075, 0.07))
    incised.append(("flats_plaque", 0.002))
    painted_board(canvas, table["church_board"], seed + 100, linear(26, 34, 70), linear(160, 130, 60), 4)
    for body, cap, dy, font in (("ST AUBIN'S CHURCH", 24.0, 100.0, "titling"), ("SERVICES", 18.0, 66.0, "serif"), ("Holy Communion   8 a.m.", 14.0, 34.0, "serif"), ("Matins   11 a.m.", 14.0, 10.0, "serif"), ("Evensong   6.30 p.m.", 14.0, -14.0, "serif"), ("All are welcome", 13.0, -48.0, "script"), ("Vicar  Rev. A. Le Couteur", 11.0, -84.0, "serif")):
        say(table, "church_board", body, cap, font, 0.0, dy, 290.0, 1.04, 0.0, (0.86, 0.8, 0.6))
    gilded.append("church_board")
    sub, lu, lv, w, h = window_of(table["pub_sign"])
    painted_board(canvas, table["pub_sign"], seed + 110, linear(30, 56, 52), linear(160, 124, 56), 1)
    cx = w * 0.5
    cy = h * 0.47
    ring = sstep(3.0, 0.0, np.abs(np.hypot(lu - cx, lv - (cy + 78.0)) - 16.0))
    shank = rect_mask(lu, lv, cx - 6.0, cy - 60.0, cx + 6.0, cy + 64.0)
    stock = rect_mask(lu, lv, cx - 46.0, cy + 46.0, cx + 46.0, cy + 56.0)
    theta = np.arctan2(lv - (cy - 20.0), lu - cx)
    arm = sstep(5.0, 0.0, np.abs(np.hypot(lu - cx, lv - (cy - 20.0)) - 58.0)) * (lv < cy - 20.0)
    flukes = np.maximum(ellipse_mask(lu, lv, cx - 58.0, cy - 14.0, 12.0, 18.0), ellipse_mask(lu, lv, cx + 58.0, cy - 14.0, 12.0, 18.0))
    anchor_mask = np.clip(ring + shank + stock + arm + flukes, 0.0, 1.0)
    shadow = np.roll(np.roll(anchor_mask, -4, 0), 4, 1)
    image = canvas.albedo[sub]
    image = mix(image, image * 0.35, shadow * 0.7)
    iron = linear(70, 72, 76) * (0.8 + 0.35 * unit(field(seed + 111, 3.0, 60.0)[sub]))[:, :, None]
    image = mix(image, iron, anchor_mask)
    rope = sstep(3.5, 0.0, np.abs((lu - cx) * 0.6 + np.sin(lv * 0.08) * 22.0)) * (lv > cy - 60.0) * (lv < cy + 40.0)
    image = mix(image, linear(170, 140, 90), rope * 0.8 * (1.0 - anchor_mask * 0.5))
    canvas.albedo[sub] = image
    say(table, "pub_sign", "THE OLD", 30.0, "algerian", 0.0, 126.0, 220.0, 1.1, 0.0, cream)
    say(table, "pub_sign", "ANCHOR", 34.0, "algerian", 0.0, -128.0, 220.0, 1.1, 0.0, cream)
    gilded.append("pub_sign")
    sub, lu, lv, w, h = window_of(table["hall_clock"])
    cx = w * 0.5
    cy = h * 0.5
    r = np.hypot(lu - cx, lv - cy)
    theta = np.arctan2(lv - cy, lu - cx)
    face = linear(222, 218, 200) * (0.9 + 0.1 * unit(field(seed + 120, 2.0, 30.0)[sub]))[:, :, None]
    face = mix(face, face * np.array([0.7, 0.66, 0.56]), cover(field(seed + 121, 1.5, 30.0, 2.0, 1.0, 5.0)[sub], 0.3, 0.5) * 0.6)
    ticks = radial_ticks(theta, r, 60, 1.0) * (r > 104) * (r < 114)
    hours = radial_ticks(theta, r, 12, 3.2) * (r > 92) * (r < 114)
    hands = np.zeros_like(r)
    for angle, length, width in ((math.pi * 0.5 - tau * (5.2 / 12.0), 60.0, 4.5), (math.pi * 0.5 - tau * (9.0 / 60.0), 88.0, 3.0)):
        ax = math.cos(angle)
        ay = math.sin(angle)
        along = (lu - cx) * ax + (lv - cy) * ay
        across = np.abs(-(lu - cx) * ay + (lv - cy) * ax)
        hands = np.maximum(hands, sstep(width + 0.8, width - 0.8, across) * (along > -12.0) * (along < length))
    hands = np.maximum(hands, sstep(9.0, 7.0, r))
    bezel = np.clip(sstep(3.0, 0.0, np.abs(r - 122.0)) + sstep(121.0, 124.0, r), 0.0, 1.0)
    image = mix(face, linear(20, 18, 16), np.clip(ticks + hours + hands, 0.0, 1.0))
    canvas.albedo[sub] = mix(image, linear(40, 44, 40), bezel)
    canvas.rough[sub] = 0.35
    canvas.height[sub] = -hands * 0.0003
    for hour, numeral in enumerate(("XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI")):
        angle = math.pi * 0.5 - tau * hour / 12.0
        say(table, "hall_clock", numeral, 17.0, "serif", math.cos(angle) * 78.0, math.sin(angle) * 78.0, 44.0, 1.0, angle - math.pi * 0.5, (0.04, 0.035, 0.03))
    enamel_panel(canvas, table["police_lamp"], seed + 130, linear(30, 50, 120), linear(30, 50, 120), 0.03)
    say(table, "police_lamp", "POLICE", 46.0, "sans", 0.0, 0.0, 170.0, 1.1, 0.0, white)
    enamel_panel(canvas, table["fuel_globe"], seed + 140, linear(226, 222, 210), linear(170, 34, 26), 0.03)
    sub, lu, lv, w, h = window_of(table["fuel_globe"])
    canvas.albedo[sub] = mix(canvas.albedo[sub], linear(170, 34, 26), rect_mask(lu, lv, 10, h * 0.5 - 22, w - 10, h * 0.5 + 22))
    say(table, "fuel_globe", "ISLE", 40.0, "condensed", 0.0, 0.0, 170.0, 1.2, 0.0, white)
    painted_board(canvas, table["shop_window"], seed + 150, linear(18, 20, 22), linear(18, 20, 22), 1)
    say(table, "shop_window", "TEAS  -  COFFEES", 22.0, "bodoni", 0.0, 22.0, 240.0, 1.1, 0.0, gold)
    say(table, "shop_window", "Provisions", 26.0, "script", 0.0, -16.0, 220.0, 1.0, 0.0, gold)
    gilded.append("shop_window")
    enamel_panel(canvas, table["garage_door"], seed + 160, linear(214, 210, 198), linear(150, 26, 24))
    say(table, "garage_door", "NO SMOKING", 26.0, "sans", 0.0, 14.0, 170.0, 1.1, 0.0, (0.45, 0.03, 0.02))
    say(table, "garage_door", "BY ORDER", 13.0, "sans", 0.0, -24.0, 120.0, 1.2, 0.0, (0.05, 0.05, 0.05))
    paper(canvas, table["open_sign"], seed + 170, linear(220, 214, 196), 0.5)
    say(table, "open_sign", "CLOSED", 34.0, "slab", 0.0, 0.0, 170.0, 1.15, 0.0, (0.4, 0.03, 0.02))
    enamel_panel(canvas, table["pump_plate"], seed + 180, linear(240, 200, 40), linear(170, 34, 26))
    say(table, "pump_plate", "MOTOR SPIRIT  1/9", 26.0, "condensed", 0.0, 0.0, 290.0, 1.1, 0.0, (0.45, 0.04, 0.03))
    painted_board(canvas, table["fuel_board"], seed + 190, linear(214, 208, 190), linear(170, 34, 26), 1)
    say(table, "fuel_board", "OILS  -  TYRES  -  BATTERIES", 18.0, "sans", 0.0, 0.0, 236.0, 1.1, 0.0, (0.35, 0.04, 0.03))
    mask, layer, weight = canvas.ink(table)
    shadow = np.roll(np.roll(mask, -2, 0), 2, 1)
    for key in gilded:
        x0, y0, x1, y1 = table[key]
        sub = (slice(y0, y1), slice(x0, x1))
        canvas.albedo[sub] = mix(canvas.albedo[sub], canvas.albedo[sub] * 0.35, shadow[sub] * 0.65)
    worn = cover(field(seed + 200, 4.0, 200.0, 1.7), 0.15, 0.05)
    canvas.albedo = mix(canvas.albedo, layer, mask * weight * (1.0 - worn * 0.6))
    canvas.height += mask * weight * 0.0002
    for key, depth in incised:
        x0, y0, x1, y1 = table[key]
        sub = (slice(y0, y1), slice(x0, x1))
        canvas.height[sub] -= mask[sub] * (depth + 0.0002)
        canvas.albedo[sub] = mix(canvas.albedo[sub], canvas.albedo[sub] * 0.45, blur(mask, 1.0)[sub] * 0.5)
    for key in gilded:
        x0, y0, x1, y1 = table[key]
        sub = (slice(y0, y1), slice(x0, x1))
        canvas.metal[sub] = np.maximum(canvas.metal[sub], mask[sub] * 0.75 * (1.0 - worn[sub]))
        canvas.rough[sub] = mix(canvas.rough[sub], 0.35, mask[sub] * (1.0 - worn[sub]))
    occlusion = 1.0 - 0.35 * cavity(canvas.height, 1.5, 0.0006)
    kit.save("town_signs", canvas.albedo, np.clip(canvas.rough, 0.05, 1.0), occlusion, canvas.height, 1.0, 1.0, metal=canvas.metal, extra=town_catalog["town_signs"])


def make_tiles():
    tile = 0.6
    seed = 7200
    pitch = 256.0
    cu = np.floor(grid_u / pitch).astype(np.int64)
    cv = np.floor(grid_v / pitch).astype(np.int64)
    fu = grid_u / pitch - cu
    fv = grid_v / pitch - cv
    ident = cv * 4 + cu
    checker = ((cu + cv) % 2 == 0)
    rng = np.random.default_rng(seed)
    red = linear(146, 60, 44)
    cream = linear(206, 188, 150)
    black = linear(36, 32, 30)
    slate = linear(84, 92, 100)
    tone = rng.uniform(0.9, 1.06, 16)[ident]
    base = np.where(checker[:, :, None], red, cream)
    diamond = sstep(0.315, 0.3, np.abs(fu - 0.5) + np.abs(fv - 0.5))
    inner = sstep(0.1, 0.09, np.maximum(np.abs(fu - 0.5), np.abs(fv - 0.5)))
    corner = sstep(0.18, 0.165, np.abs(fu - np.round(fu)) + np.abs(fv - np.round(fv)))
    albedo = mix(base, np.where(checker[:, :, None], black, slate), diamond)
    albedo = mix(albedo, np.where(checker[:, :, None], cream, red), inner)
    albedo = mix(albedo, black, corner)
    albedo = tint(albedo, tone * (0.92 + 0.1 * unit(field(seed + 1, 4.0, 200.0, 1.6))))
    edge = np.minimum(np.minimum(fu, 1.0 - fu), np.minimum(fv, 1.0 - fv)) * pitch
    grout = sstep(2.2, 1.0, edge + field(seed + 2, 30.0, 400.0) * 0.4)
    worn = cover(field(seed + 3, 1.5, 30.0, 2.0), 0.3, 0.5)
    albedo = mix(albedo, albedo * np.array([1.12, 1.1, 1.05]) + 0.02, worn * 0.4)
    dirt = cover(field(seed + 4, 2.0, 60.0, 2.0), 0.35, 0.6)
    albedo = mix(albedo, albedo * np.array([0.62, 0.58, 0.52]), dirt * 0.5)
    cracked = rng.random(16)[ident] < 0.2
    crack_line = sstep(1.4, 0.0, np.abs((fu - 0.5) * rng.uniform(-1.0, 1.0, 16)[ident] + (fv - 0.5) - field(seed + 5, 10.0, 200.0) * 0.06) * pitch) * cracked
    missing = ident == 6
    bed = linear(116, 108, 96) * (0.8 + 0.3 * unit(field(seed + 6, 6.0, 200.0)))[:, :, None]
    albedo = mix(albedo, linear(40, 36, 30), crack_line * 0.85)
    albedo = mix(albedo, linear(58, 54, 48) * (0.7 + 0.4 * unit(field(seed + 7, 8.0, 300.0)))[:, :, None], grout)
    albedo = np.where(missing[:, :, None], bed, albedo)
    tilt_u = rng.uniform(-1.0, 1.0, 16)[ident]
    tilt_v = rng.uniform(-1.0, 1.0, 16)[ident]
    height = (fu - 0.5) * tilt_u * 0.0008 + (fv - 0.5) * tilt_v * 0.0008 - grout * 0.0018 - crack_line * 0.0006
    height = np.where(missing, -0.006 + field(seed + 8, 6.0, 200.0) * 0.0006, height)
    rough = np.where(missing, 0.95, 0.42 + 0.3 * worn + 0.2 * dirt) + 0.4 * grout
    occlusion = 1.0 - 0.45 * grout - 0.3 * cavity(height, 2.0, 0.0008)
    kit.save("town_tiles", albedo, np.clip(rough, 0.05, 1.0), occlusion, height, tile, 1.0, extra=town_catalog["town_tiles"])


def make_quarry():
    tile = 0.9
    seed = 7300
    pitch = 256.0
    cu = np.floor(grid_u / pitch).astype(np.int64)
    cv = np.floor(grid_v / pitch).astype(np.int64)
    fu = grid_u / pitch - cu
    fv = grid_v / pitch - cv
    ident = cv * 4 + cu
    rng = np.random.default_rng(seed)
    checker = (cu + cv) % 2 == 0
    tone = rng.uniform(0.82, 1.12, 16)[ident]
    base = np.where(checker[:, :, None], linear(128, 56, 40), linear(52, 46, 48))
    albedo = tint(base, tone * (0.86 + 0.2 * unit(field(seed + 1, 3.0, 100.0, 1.8))))
    edge = np.minimum(np.minimum(fu, 1.0 - fu), np.minimum(fv, 1.0 - fv)) * pitch + field(seed + 2, 40.0, 500.0) * 1.2
    grout = sstep(3.5, 2.0, edge)
    chip = sstep(8.0, 3.0, edge) * cover(field(seed + 3, 20.0, 300.0), 0.12, 0.3)
    scuff = cover(field(seed + 4, 2.0, 40.0, 2.0, 3.0, 1.0), 0.3, 0.6)
    grease = cover(field(seed + 5, 1.5, 30.0, 2.0), 0.2, 0.5)
    albedo = mix(albedo, albedo * np.array([1.2, 1.15, 1.1]) + 0.02, scuff * 0.35)
    albedo = mix(albedo, albedo * np.array([0.55, 0.5, 0.44]), grease * 0.5)
    albedo = mix(albedo, linear(150, 110, 90), chip * 0.6)
    albedo = mix(albedo, linear(86, 80, 70) * (0.7 + 0.4 * unit(field(seed + 6, 8.0, 200.0)))[:, :, None], grout)
    crack = kit.cracks(seed + 7, 9, 0.9, 0.35)
    albedo = mix(albedo, linear(30, 26, 22), crack * (1.0 - grout) * 0.8)
    height = sstep(0.0, 8.0, edge) * 0.0015 - grout * 0.003 - chip * 0.0012 - crack * 0.0006 + field(seed + 8, 6.0, 200.0) * 0.0002
    rough = 0.72 + 0.1 * unit(field(seed + 9, 4.0, 100.0)) - 0.15 * grease + 0.2 * grout
    occlusion = 1.0 - 0.45 * grout - 0.3 * cavity(height, 2.0, 0.001)
    kit.save("town_quarry", albedo, rough, occlusion, height, tile, 1.0, extra=town_catalog["town_quarry"])


def make_stripe():
    tile = 1.0
    seed = 7400
    ground = mix(linear(214, 202, 168), linear(204, 194, 160), unit(field(seed, 2.0, 30.0)))
    phase = (grid_u / size * 8.0) % 1.0
    broad = sstep(0.12, 0.13, phase) * sstep(0.47, 0.46, phase)
    pin = sstep(0.012, 0.004, np.abs(phase - 0.06)) + sstep(0.012, 0.004, np.abs(phase - 0.53))
    albedo = mix(ground, linear(120, 140, 108) * (0.92 + 0.1 * unit(speckle(seed + 1, 0.8)))[:, :, None], broad)
    albedo = mix(albedo, linear(170, 140, 80), np.clip(pin, 0.0, 1.0) * 0.8)
    sprig_u = ((grid_u / size * 8.0) % 1.0 - 0.765) * (size / 8.0)
    sprig_v = ((grid_v / size * 10.0) % 1.0 - 0.5) * (size / 10.0)
    leaf = sstep(1.0, 0.6, np.hypot(sprig_u / 7.0, sprig_v / 3.0)) + sstep(1.0, 0.6, np.hypot((sprig_u - 4.0) / 3.0, (sprig_v - 6.0) / 6.0)) + sstep(1.0, 0.6, np.hypot((sprig_u + 4.0) / 3.0, (sprig_v - 6.0) / 6.0))
    bud = sstep(1.0, 0.6, np.hypot(sprig_u / 3.4, (sprig_v - 11.0) / 3.4))
    albedo = mix(albedo, linear(120, 136, 96), np.clip(leaf, 0.0, 1.0) * 0.8)
    albedo = mix(albedo, linear(170, 90, 84), bud * 0.85)
    fade = unit(field(seed + 2, 1.2, 20.0, 2.2))
    albedo = mix(albedo, ground * 1.03, 0.15 + 0.3 * fade)
    seam = sstep(2.5, 0.0, np.minimum(grid_u % (size * 0.5), size * 0.5 - grid_u % (size * 0.5)))
    albedo = mix(albedo, albedo * 0.74, seam * 0.8)
    stain_field = field(seed + 3, 1.3, 25.0, 2.3)
    stain = cover(stain_field, 0.18, 0.2)
    ring = sstep(0.12, 0.0, np.abs(stain_field - float(np.quantile(stain_field, 0.82))))
    albedo = mix(albedo, albedo * np.array([0.78, 0.64, 0.44]), stain * 0.55)
    albedo = mix(albedo, albedo * np.array([0.52, 0.4, 0.26]), ring * 0.5)
    mold = cover(speckle(seed + 4, 1.2), 0.14, 0.3) * cover(field(seed + 5, 2.0, 30.0, 2.0), 0.18, 0.4)
    albedo = mix(albedo, linear(48, 52, 40), mold * 0.75)
    albedo = tint(albedo, 1.0 - 0.18 * cover(field(seed + 6, 1.0, 40.0, 2.0, 1.0, 4.0), 0.3, 0.5))
    height = field(seed + 7, 2.0, 50.0, 2.2) * 0.0004 + seam * 0.0003
    rough = 0.82 + 0.05 * field(seed + 8, 3.0, 60.0) + 0.06 * stain
    occlusion = 1.0 - 0.3 * cavity(height, 2.0, 0.0002)
    kit.save("town_stripe", albedo, rough, occlusion, height, tile, 1.0, extra=town_catalog["town_stripe"])


def make_carpet():
    tile = 1.0
    seed = 7500
    cells = 6.0
    a = (grid_u + grid_v) / size * cells
    b = (grid_u - grid_v) / size * cells
    fa = a % 1.0
    fb = b % 1.0
    lattice = np.maximum(sstep(0.44, 0.47, np.abs(fa - 0.5)), sstep(0.44, 0.47, np.abs(fb - 0.5)))
    cx = np.abs(fa - 0.5)
    cy = np.abs(fb - 0.5)
    medallion = sstep(0.2, 0.17, cx + cy) - sstep(0.12, 0.09, cx + cy)
    core = sstep(0.07, 0.05, np.maximum(cx, cy))
    petals = sstep(0.05, 0.03, np.abs(np.hypot(cx, cy) - 0.3)) * sstep(0.2, 0.0, np.minimum(cx, cy))
    field_color = linear(116, 28, 26) * (0.86 + 0.2 * unit(field(seed, 2.0, 40.0)))[:, :, None]
    albedo = mix(field_color, linear(28, 34, 66), lattice)
    albedo = mix(albedo, linear(196, 160, 90), np.clip(medallion, 0.0, 1.0) * 0.9)
    albedo = mix(albedo, linear(28, 34, 66), core)
    albedo = mix(albedo, linear(210, 196, 160), np.clip(petals, 0.0, 1.0) * 0.8)
    pile = speckle(seed + 1, 0.7)
    albedo = tint(albedo, 0.88 + 0.16 * unit(pile))
    worn = cover(field(seed + 2, 1.2, 25.0, 2.0) + 0.5 * field(seed + 3, 8.0, 200.0, 1.6), 0.14, 0.12)
    backing = linear(150, 134, 104) * (0.8 + 0.3 * unit(speckle(seed + 4, 0.6)))[:, :, None]
    threads = sstep(0.4, 0.0, np.abs(((grid_u * 0.5) % 2.0) - 1.0)) * 0.3
    albedo = mix(albedo, backing * (1.0 - threads)[:, :, None], worn * 0.9)
    thin = cover(field(seed + 2, 1.2, 25.0, 2.0) + 0.5 * field(seed + 3, 8.0, 200.0, 1.6), 0.35, 0.3)
    albedo = mix(albedo, albedo * np.array([1.1, 1.0, 0.92]) + 0.03, (thin - worn).clip(0.0, 1.0) * 0.45)
    stain_field = field(seed + 5, 1.5, 25.0, 2.2)
    stain = cover(stain_field, 0.15, 0.25)
    albedo = mix(albedo, albedo * np.array([0.55, 0.5, 0.42]), stain * 0.55)
    holes = cover(field(seed + 6, 30.0, 400.0, 1.5), 0.01, 0.2)
    albedo = mix(albedo, linear(14, 12, 10), holes)
    height = pile * 0.0004 * (1.0 - worn) - worn * 0.0015 - holes * 0.002
    rough = 0.95 - 0.05 * worn
    occlusion = 1.0 - 0.3 * cavity(height, 1.0, 0.0004) - 0.5 * holes
    kit.save("town_carpet", albedo, rough, occlusion, height, tile, 1.0, extra=town_catalog["town_carpet"])


def make_brass():
    tile = 0.5
    seed = 7600
    base = mix(linear(178, 134, 60), linear(150, 110, 48), unit(field(seed, 3.0, 80.0, 1.8)))
    tarnish = cover(field(seed + 1, 2.0, 60.0, 2.0) + 0.4 * field(seed + 2, 10.0, 200.0, 1.6), 0.45, 0.5)
    albedo = mix(base, linear(78, 60, 34), tarnish * 0.75)
    verdigris = cover(field(seed + 3, 3.0, 120.0, 1.8) + 0.6 * speckle(seed + 4, 1.5), 0.08, 0.3)
    albedo = mix(albedo, linear(84, 140, 112) * (0.8 + 0.3 * unit(speckle(seed + 5, 0.8)))[:, :, None], verdigris * 0.9)
    scratch = cover(field(seed + 6, 2.0, 600.0, 1.2, 18.0, 0.5), 0.03, 0.2)
    albedo = mix(albedo, linear(214, 180, 110), scratch * 0.6 * (1.0 - verdigris))
    height = field(seed + 7, 4.0, 200.0, 1.6) * 0.0002 + verdigris * 0.0003 - scratch * 0.0001
    rough = 0.28 + 0.35 * tarnish + 0.5 * verdigris - 0.1 * scratch
    metal = np.clip(1.0 - verdigris * 1.1, 0.0, 1.0)
    occlusion = 1.0 - 0.3 * cavity(height, 1.5, 0.0002)
    kit.save("town_brass", albedo, np.clip(rough, 0.1, 1.0), occlusion, height, tile, 1.0, metal=metal, extra=town_catalog["town_brass"])


def make_metal():
    tile = 1.0
    seed = 7700
    strip = np.floor(grid_u / 256.0).astype(np.int64)
    paints = np.array([linear(76, 92, 70), linear(206, 200, 182), linear(150, 32, 28), linear(34, 50, 84)])
    coat = paints[strip] * (0.9 + 0.14 * unit(field(seed, 2.0, 60.0, 2.0)))[:, :, None]
    chalk = cover(field(seed + 1, 1.5, 30.0, 2.0), 0.4, 0.6)
    coat = mix(coat, coat * 1.12 + 0.03, chalk * 0.4)
    chip_field = field(seed + 2, 6.0, 300.0, 1.7) + 0.5 * field(seed + 3, 30.0, 500.0, 1.4)
    primer = cover(chip_field, 0.12, 0.04)
    bare = cover(chip_field, 0.06, 0.04)
    rust = mix(linear(104, 50, 24), linear(60, 32, 18), unit(field(seed + 4, 10.0, 300.0, 1.6)))
    albedo = mix(coat, linear(110, 108, 102), primer)
    albedo = mix(albedo, rust, bare)
    edge = np.clip(primer * (1.0 - primer) * 4.0, 0.0, 1.0)
    albedo = mix(albedo, albedo * 0.7, edge * 0.4)
    runs = cover(field(seed + 5, 3.0, 100.0, 2.0, 1.0, 10.0), 0.18, 0.4) * sstep(0.0, 0.3, unit(field(seed + 6, 1.0, 10.0)))
    albedo = mix(albedo, albedo * np.array([0.9, 0.62, 0.42]) + np.array([0.04, 0.012, 0.0]), runs * 0.4)
    scratch = cover(field(seed + 7, 2.0, 600.0, 1.2, 20.0, 0.5), 0.02, 0.2)
    albedo = mix(albedo, linear(160, 158, 150), scratch * 0.7)
    grime = cover(field(seed + 8, 1.5, 40.0, 2.0, 1.0, 3.0), 0.3, 0.5)
    albedo = tint(albedo, 1.0 - 0.2 * grime)
    height = field(seed + 9, 1.0, 12.0, 2.4) * 0.0015 + (1.0 - primer) * 0.0002 + edge * 0.0002 - bare * 0.0003
    rough = mix(0.48 + 0.1 * grime, 0.75, primer)
    rough = mix(rough, 0.92, bare)
    rough = mix(rough, 0.4, scratch)
    metal = np.clip(scratch * 0.9 + bare * 0.0, 0.0, 1.0)
    occlusion = 1.0 - 0.3 * cavity(height, 1.5, 0.0004)
    kit.save("town_metal", albedo, rough, occlusion, height, tile, 1.0, metal=metal, extra=town_catalog["town_metal"])


def make_lino():
    tile = 2.0
    seed = 7800
    marble = field(seed, 1.5, 80.0, 1.8, 3.0, 1.0) + 0.6 * field(seed + 1, 8.0, 300.0, 1.5, 6.0, 1.0)
    veins = sstep(0.25, 0.0, np.abs(marble))
    base = mix(linear(108, 52, 38), linear(78, 40, 32), unit(field(seed + 2, 2.0, 40.0)))
    albedo = mix(base, linear(150, 104, 80), veins * 0.5)
    albedo = tint(albedo, 0.9 + 0.12 * unit(speckle(seed + 3, 0.8)))
    seam_u = np.minimum(grid_u % (size * 0.5), size * 0.5 - grid_u % (size * 0.5))
    seam = sstep(2.0, 0.5, seam_u)
    worn = cover(field(seed + 4, 1.2, 25.0, 2.0) + 0.6 * field(seed + 5, 8.0, 200.0, 1.6), 0.12, 0.1)
    jute = linear(140, 120, 88) * (0.8 + 0.3 * unit(speckle(seed + 6, 0.6)))[:, :, None]
    weave = (np.sin(grid_u * 1.6) * np.sin(grid_v * 1.6)) * 0.5 + 0.5
    albedo = mix(albedo, jute * (0.85 + 0.2 * weave)[:, :, None], worn)
    scuff = cover(field(seed + 7, 1.5, 30.0, 2.0, 2.0, 1.0), 0.35, 0.5)
    albedo = mix(albedo, albedo * np.array([1.15, 1.1, 1.05]), scuff * 0.3 * (1.0 - worn))
    dirt = cover(field(seed + 8, 2.0, 50.0, 2.0), 0.3, 0.6)
    albedo = mix(albedo, albedo * np.array([0.6, 0.56, 0.5]), dirt * 0.45)
    crack = kit.cracks(seed + 9, 6, 1.1, 0.3)
    albedo = mix(albedo, linear(30, 24, 20), np.maximum(crack, seam) * 0.8)
    height = -worn * 0.0008 - seam * 0.001 - crack * 0.0006 + speckle(seed + 10, 0.8) * 0.00005 + worn * weave * 0.0002
    rough = 0.5 + 0.3 * worn + 0.15 * dirt - 0.1 * (1.0 - scuff)
    occlusion = 1.0 - 0.35 * cavity(height, 2.0, 0.0005)
    kit.save("town_lino", albedo, np.clip(rough, 0.1, 1.0), occlusion, height, tile, 1.0, extra=town_catalog["town_lino"])


def make_paints():
    for name, (paint, primer, seed) in town_paints.items():
        kit.make_painted(name, paint, primer, seed)


makers = {
    "town_paints": make_paints,
    "town_print": make_print,
    "town_signs": make_signs,
    "town_tiles": make_tiles,
    "town_quarry": make_quarry,
    "town_stripe": make_stripe,
    "town_carpet": make_carpet,
    "town_brass": make_brass,
    "town_metal": make_metal,
    "town_lino": make_lino,
}


def build(names=None):
    register()
    for name, maker in makers.items():
        if not names or name in names:
            maker()
    print("TOWN LIBRARY DONE", flush=True)
