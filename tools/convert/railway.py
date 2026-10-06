import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import railtrain as rt
import railside as rs
from buildkit import V, block, emit, local_block
from mathutils import Matrix

arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = arguments[0] if arguments else "library"
wanted = [name for name in (arguments[1].split(",") if len(arguments) > 1 else []) if name]
samples = int(arguments[2]) if len(arguments) > 2 else 96
tau = math.pi * 2.0

gauge = 1.435
rail_top = 0.5
rail_foot = rail_top - 0.1385 * math.cos(rk.rail_cant) - 0.022 * math.sin(rk.rail_cant)
rail_center = gauge * 0.5 + 0.035 * math.cos(rk.rail_cant) + 0.1285 * rk.rail_scale * math.sin(rk.rail_cant)
panel = 12.0
sleeper_top = 0.35
sleeper_count = 18
sleeper_pitch = panel / sleeper_count
ballast_top = 0.27
shoulder = 1.6
toe = 2.5
toe_level = -0.08
ballast_tile = 2.0
X = V(1.0, 0.0, 0.0)
Y = V(0.0, 1.0, 0.0)
Z = V(0.0, 0.0, 1.0)


def rail_matrix(sign):
    return Matrix.Translation(V(sign * rail_center, 0.0, rail_foot)) @ Matrix.Rotation(-sign * rk.rail_cant, 4, 'Y')


def bed_waves(rng, count=14):
    waves = []
    for index in range(count):
        waves.append((rng.uniform(0.4, 1.0) / (1.0 + index * 0.25), rng.randint(1, 5 + index * 3), rng.uniform(-3.0, 3.0) * (1.0 + index * 0.3), rng.uniform(0.0, tau)))
    total = sum(wave[0] for wave in waves)
    return [(a / total, m, kx, phase) for a, m, kx, phase in waves]


def bed_base(x):
    ax = abs(x)
    return ballast_top if ax <= shoulder else ballast_top + (ax - shoulder) * (toe_level - ballast_top) / (toe - shoulder)


def bed_height(x, y, waves, humps=()):
    ax = abs(x)
    noise = sum(a * math.sin(tau * m * y / panel + kx * x + phase) for a, m, kx, phase in waves)
    amplitude = 0.022 if ax <= shoulder else 0.022 + (ax - shoulder) * 0.02
    if ax > 2.2:
        amplitude *= max(0.2, (toe - ax) / 0.3)
    dip = -0.012 * math.exp(-((ax - rail_center) / 0.16) ** 2)
    window = min(1.0, y / 0.6, (panel - y) / 0.6)
    extra = sum(h * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (r * r)) for cx, cy, r, h in humps) * max(window, 0.0)
    return bed_base(x) + noise * amplitude + dip + extra


def bed_geo(waves, humps=(), rows=96):
    xs = [-toe, -2.2, -1.9] + [-shoulder + 0.16 * index for index in range(21)] + [1.9, 2.2, toe]
    arc = [0.0]
    for index in range(1, len(xs)):
        arc.append(arc[-1] + math.hypot(xs[index] - xs[index - 1], bed_base(xs[index]) - bed_base(xs[index - 1])))
    points = []
    for j in range(rows + 1):
        y = panel * j / rows
        for x in xs:
            points.append(V(x, y, bed_height(x, y, waves, humps)))
    faces = []
    uvs = []
    count = len(xs)
    for j in range(rows):
        for i in range(count - 1):
            a = j * count + i
            faces.append((a, a + 1, a + count + 1, a + count))
            uvs.append([(arc[i] / ballast_tile + 0.13, panel * j / rows / ballast_tile), (arc[i + 1] / ballast_tile + 0.13, panel * j / rows / ballast_tile), (arc[i + 1] / ballast_tile + 0.13, panel * (j + 1) / rows / ballast_tile), (arc[i] / ballast_tile + 0.13, panel * (j + 1) / rows / ballast_tile)])
    return kit.Geo(points, faces, uvs)


def bed_normal(waves, humps=()):
    def sample(p):
        e = 0.02
        dx = (bed_height(p.x + e, p.y, waves, humps) - bed_height(p.x - e, p.y, waves, humps)) / (2.0 * e)
        dy = (bed_height(p.x, p.y + e, waves, humps) - bed_height(p.x, p.y - e, waves, humps)) / (2.0 * e)
        return V(-dx, -dy, 1.0).normalized()
    return sample


def spike_geo(d):
    h = d * 0.113
    path = [V(h, 0.0, -0.004), V(h, 0.0, 0.032), V(h - d * 0.015, 0.0, 0.045), V(d * 0.061, 0.0, 0.034), V(d * 0.051, 0.0, 0.0185)]
    return kit.geo_tube(path, rk.square_profile(0.010, 0.016), True, V(0.0, 1.0, 0.0))


def baseplate(part, rng, sign, y, neglect=0.07):
    matrix = rail_matrix(sign) @ Matrix.Translation(V(0.0, y, 0.0))
    local_block(part, "rust_iron", matrix, -0.18, 0.18, -0.095, 0.095, -0.026, -0.0005, 0.004)
    for d in (-1.0, 1.0):
        block(part, "rust_iron", V(min(d * 0.073, d * 0.091), -0.095, -0.0005), V(max(d * 0.073, d * 0.091), 0.095, 0.0135), 0.0, "box", matrix, ("bottom",))
    layout = [(1.0, -0.055), (1.0, 0.055), (-1.0, 0.0)] if rng.random() < 0.5 else [(1.0, 0.0), (-1.0, -0.055), (-1.0, 0.055)]
    for d, along in layout:
        if rng.random() < neglect:
            local_block(part, "rust_iron", matrix, d * 0.113 - 0.011, d * 0.113 + 0.011, along - 0.011, along + 0.011, -0.0005, 0.0015)
            continue
        lift = rng.uniform(0.008, 0.02) if rng.random() < neglect else 0.0
        emit(part, spike_geo(d), "rust_iron", matrix @ Matrix.Translation(V(0.0, along, lift)) @ Matrix.Rotation(rng.uniform(-0.12, 0.12) if lift > 0.0 else 0.0, 4, 'Z'), "given", False)


def fishplate(part, sign, end):
    matrix = rail_matrix(sign)
    y0, y1 = (0.0, 0.2285) if end == 0 else (panel - 0.2285, panel)
    s = rk.rail_scale
    for side in (-1.0, 1.0):
        outline = [(side * 0.0085, 0.034 * s), (side * 0.026, 0.034 * s), (side * 0.031, 0.040 * s), (side * 0.031, 0.090 * s), (side * 0.026, 0.0965 * s), (side * 0.0085, 0.0965 * s)]
        emit(part, rk.geo_prism(outline, y0, y1, 1, True, True), "rust_iron", matrix, "given", False)
    for number, offset in enumerate((0.057, 0.171)):
        y = y0 + offset if end == 0 else y1 - offset
        head = 1.0 if (number + end) % 2 == 0 else -1.0
        rotation = matrix.to_3x3()
        rk.prism_bolt(part, "rust_iron", matrix @ V(head * 0.031, y, 0.0655 * s), rotation @ V(head, 0.0, 0.0), 0.034, 0.016, 4, 0.0, 0.0, math.pi * 0.25, V(0.0, 1.0, 0.0))
        rk.prism_bolt(part, "rust_iron", matrix @ V(-head * 0.031, y, 0.0655 * s), rotation @ V(-head, 0.0, 0.0), 0.036, 0.02, 6, 0.004, 0.012, 0.0, V(0.0, 1.0, 0.0))


def sleeper_layout(rng, rotten=3):
    layout = []
    doomed = set(rng.sample(range(sleeper_count), rotten))
    for index in range(sleeper_count):
        skew = rng.uniform(-0.012, 0.012)
        if rng.random() < 0.12:
            skew = rng.uniform(-0.045, 0.045)
        layout.append({"y": (index + 0.5) * sleeper_pitch + rng.uniform(-0.02, 0.02), "x": rng.uniform(-0.035, 0.035), "yaw": skew, "roll": rng.uniform(-0.012, 0.012), "lift": rng.uniform(-0.004, 0.004), "rotten": index in doomed})
    return layout


def inside_sleeper(layout, x, y, margin=0.0):
    if abs(x) > 1.3 + margin + 0.04:
        return False
    for item in layout:
        if abs(y - item["y"] - math.tan(item["yaw"]) * x) < 0.125 + margin:
            return True
    return False


def scatter_stones(part, rng, prototypes, layout, waves, humps, count, extra_on_sleepers=10):
    placed = 0
    attempts = 0
    while placed < count and attempts < count * 20:
        attempts += 1
        radius = rng.uniform(0.02, 0.043) * (1.25 if rng.random() < 0.08 else 1.0)
        roll = rng.random()
        if roll < 0.36:
            item = rng.choice(layout)
            x = rng.uniform(-1.5, 1.5)
            y = item["y"] + math.tan(item["yaw"]) * x + rng.choice((-1.0, 1.0)) * (0.125 + radius * rng.uniform(0.3, 1.4))
        elif roll < 0.72:
            x = rng.choice((-1.0, 1.0)) * rng.uniform(1.45, 2.38)
            y = rng.uniform(0.0, panel)
        else:
            x = rng.uniform(-1.6, 1.6)
            y = rng.uniform(0.0, panel)
        if y < radius + 0.004 or y > panel - radius - 0.004:
            continue
        if abs(abs(x) - rail_center) < 0.1 + radius:
            continue
        if inside_sleeper(layout, x, y, radius * 0.6):
            continue
        z = bed_height(x, y, waves, humps) + radius * rng.uniform(-0.1, 0.3)
        rk.stone(part, prototypes, rng, V(x, y, z), radius)
        placed += 1
    for index in range(extra_on_sleepers):
        item = rng.choice(layout)
        radius = rng.uniform(0.018, 0.034)
        x = rng.choice((-1.0, 1.0)) * rng.uniform(0.95, 1.25) if rng.random() < 0.6 else rng.uniform(-0.55, 0.55)
        y = item["y"] + math.tan(item["yaw"]) * x + rng.uniform(-0.09, 0.09)
        rk.stone(part, prototypes, rng, V(x, y, sleeper_top + radius * 0.3), radius)
    return placed


def track_core(b, rng, band, neglect, waves, humps, stones):
    bed = b.part("bed", 60.0)
    emit(bed, bed_geo(waves, humps), "ballast_stone", None, "texture", True)
    b.shading["bed"] = bed_normal(waves, humps)
    layout = sleeper_layout(rng)
    sleepers = b.part("sleepers", 60.0, 50)
    for item in layout:
        wear = 2.4 if item["rotten"] else rng.uniform(0.7, 1.3)
        splits = tuple(rng.uniform(0.15, 0.42) if rng.random() < (0.7 if item["rotten"] else 0.35) else 0.0 for end in range(2))
        strip = rng.choice((1, 3, 5)) if item["rotten"] else rng.randrange(rk.strip_count)
        geo = rk.sleeper_geo(rng, strip, (rng.randrange(8), rng.randrange(8)), 2.6 + rng.uniform(-0.02, 0.02), 0.25, 0.13, wear, splits, rng.random() < 0.5)
        matrix = Matrix.Translation(V(item["x"], item["y"], sleeper_top + item["lift"])) @ Matrix.Rotation(item["yaw"], 4, 'Z') @ Matrix.Rotation(item["roll"], 4, 'X')
        emit(sleepers, geo, "sleeper_timber", matrix, "texture", True)
    rails = b.part("rails", 40.0)
    fastenings = b.part("fastenings", 50.0, 50)
    for sign in (-1.0, 1.0):
        emit(rails, rk.rail_geo(0.003, panel - 0.003, 32, sign < 0.0, band), "rail_steel", rail_matrix(sign), "texture", True)
        for end in (0, 1):
            fishplate(fastenings, sign, end)
        for item in layout:
            baseplate(fastenings, rng, sign, item["y"] + math.tan(item["yaw"]) * sign * rail_center, neglect)
    prototypes = rk.stone_prototypes(rng)
    scatter_stones(b.part("stones", 30.0), rng, prototypes, layout, waves, humps, stones)
    return layout


def track():
    b = rk.Build("rail_track", 11)
    rng = b.rng
    waves = bed_waves(rng)
    track_core(b, rng, "bright", 0.07, waves, (), 1250)
    return b


def plant(part, geo, name, position, scale, yaw, extra=None):
    matrix = Matrix.Translation(position) @ Matrix.Rotation(yaw, 4, 'Z')
    if extra is not None:
        matrix = matrix @ extra
    emit(part, geo, name, matrix @ Matrix.Diagonal((scale, scale, scale, 1.0)), "texture", True)


def free_spot(rng, layout, x_range, waves, humps, both_sides=True, margin=0.1, attempts=40):
    for attempt in range(attempts):
        x = rng.uniform(x_range[0], x_range[1]) * (rng.choice((-1.0, 1.0)) if both_sides else 1.0)
        y = rng.uniform(0.4, panel - 0.4)
        if abs(abs(x) - rail_center) < 0.16:
            continue
        if inside_sleeper(layout, x, y, margin):
            continue
        return V(x, y, bed_height(x, y, waves, humps) - 0.012)
    return None


def track_weeds():
    b = rk.Build("rail_track_weeds", 21)
    rng = b.rng
    waves = bed_waves(random.Random(11))
    humps = [(rng.uniform(-2.0, 2.0), rng.uniform(1.2, 10.8), rng.uniform(0.35, 0.8), rng.uniform(-0.05, 0.06)) for index in range(7)]
    layout = track_core(b, rng, "bright", 0.16, waves, humps, 850)
    rk.external_material(b, "ext_grass_clumps", "grass_clumps")
    grass = b.part("grass", 60.0)
    b.shading["grass"] = lambda p: V(0.0, 0.0, 1.0)
    for index in range(36):
        spot = free_spot(rng, layout, (1.3, 2.4), waves, humps)
        if spot is not None:
            rk.grass_card(grass, "ext_grass_clumps", rng, spot, rng.uniform(0.4, 0.8), rng.choice((0, 0, 1, 1, 2, 3)))
    for index in range(12):
        spot = free_spot(rng, layout, (-0.5, 0.5), waves, humps, False)
        if spot is not None:
            rk.grass_card(grass, "ext_grass_clumps", rng, spot, rng.uniform(0.28, 0.45), rng.choice((0, 3, 3, 2)))
    for index in range(8):
        spot = free_spot(rng, layout, (0.95, 1.3), waves, humps)
        if spot is not None:
            rk.grass_card(grass, "ext_grass_clumps", rng, spot, rng.uniform(0.3, 0.5), rng.choice((0, 3, 2)))
    weeds = b.part("weeds", 60.0)
    rk.external_material(b, "ext_grass_medium_01", "grass_medium_01")
    blades = rk.load_plants("grass_medium_01", {"tall_a": 1.0, "tall_b": 1.0, "tall_c": 1.0, "small_a": 0.5})
    for index in range(8):
        spot = free_spot(rng, layout, (0.95, 2.35) if index % 3 else (-0.55, 0.55), waves, humps, index % 3 != 0)
        if spot is not None:
            key = rng.choice(("tall_a", "tall_b", "tall_c", "small_a"))
            plant(weeds, blades[key], "ext_grass_medium_01", spot, rng.uniform(1.2, 1.9) if spot.x * spot.x > 0.6 else rng.uniform(0.9, 1.2), rng.uniform(0.0, tau))
    rk.external_material(b, "ext_weed_plant_02", "weed_plant_02")
    docks = rk.load_plants("weed_plant_02", {"a": 0.13, "b": 0.13, "c": 0.13})
    for index in range(6):
        spot = free_spot(rng, layout, (0.95, 2.2) if index % 2 else (-0.5, 0.5), waves, humps, index % 2 != 0)
        if spot is not None:
            plant(weeds, docks[rng.choice(("a", "b", "c"))], "ext_weed_plant_02", spot, rng.uniform(1.3, 1.9), rng.uniform(0.0, tau))
    rk.external_material(b, "ext_nettle_plant", "nettle_plant")
    nettles = rk.load_plants("nettle_plant", {"tall_a": 0.06, "medium_a": 0.07})
    patch = V(rng.choice((-1.0, 1.0)) * 1.95, rng.uniform(3.0, 9.0), 0.0)
    for index in range(4):
        x = patch.x + rng.uniform(-0.3, 0.3)
        y = patch.y + rng.uniform(-0.5, 0.5)
        plant(weeds, nettles[rng.choice(("tall_a", "medium_a"))], "ext_nettle_plant", V(x, y, bed_height(x, y, waves, humps) - 0.015), rng.uniform(2.6, 3.6), rng.uniform(0.0, tau))
    rk.external_material(b, "ext_fern_02", "fern_02")
    ferns = rk.load_plants("fern_02", {"a": 0.6, "d": 0.6})
    for index in range(2):
        x = (1.0 if index else -1.0) * rng.uniform(2.1, 2.35)
        y = rng.uniform(1.0, 11.0)
        plant(weeds, ferns[rng.choice(("a", "d"))], "ext_fern_02", V(x, y, bed_height(x, y, waves, humps) - 0.01), rng.uniform(0.8, 1.1), rng.uniform(0.0, tau))
    rk.external_material(b, "ext_shrub_04", "shrub_04")
    twigs = [rk.load_plants("shrub_04", {"whole": 0.07})["whole"], rk.load_plants("shrub_04", {"whole": 0.025})["whole"]]
    upright = Matrix.Rotation(math.pi * 0.5, 4, 'Y')
    for index in range(2):
        x = (1.0 if index else -1.0) * rng.uniform(1.75, 2.15)
        y = rng.uniform(1.5, 10.5)
        base = V(x, y, bed_height(x, y, waves, humps) - 0.02)
        size_value = rng.uniform(1.9, 2.7)
        start = rng.uniform(0.0, tau)
        for copy in range(2):
            plant(weeds, twigs[copy], "ext_shrub_04", base, size_value * (1.0 if copy == 0 else rng.uniform(0.7, 0.85)), start + math.pi * copy + rng.uniform(-0.3, 0.3), Matrix.Rotation(rng.uniform(-0.08, 0.08), 4, 'X') @ upright)
        rk.grass_card(grass, "ext_grass_clumps", rng, base, rng.uniform(0.4, 0.6), rng.choice((0, 3)))
    debris = b.part("debris", 40.0)
    for index in range(2):
        x = rng.choice((-1.0, 1.0)) * rng.uniform(1.7, 2.2)
        y = rng.uniform(1.5, 10.5)
        z = bed_height(x, y, waves, humps)
        kit.lump(debris, "dirt_debris", V(x, y, z - 0.02), (rng.uniform(0.35, 0.55), rng.uniform(0.25, 0.4), 0.06), rng, 0.3, 2, z - 0.05)
        for tuft in range(3):
            rk.grass_card(grass, "ext_grass_clumps", rng, V(x + rng.uniform(-0.3, 0.3), y + rng.uniform(-0.25, 0.25), z + 0.01), rng.uniform(0.35, 0.6), rng.choice((0, 1, 3)))
    return b


def far_box(part, name, low, high, uv_faces):
    points = [V(low.x, low.y, low.z), V(high.x, low.y, low.z), V(high.x, high.y, low.z), V(low.x, high.y, low.z), V(low.x, low.y, high.z), V(high.x, low.y, high.z), V(high.x, high.y, high.z), V(low.x, high.y, high.z)]
    named = {"top": (4, 5, 6, 7), "front": (0, 1, 5, 4), "back": (2, 3, 7, 6), "left": (0, 4, 7, 3), "right": (1, 2, 6, 5)}
    faces = []
    uvs = []
    for key, mapped in uv_faces.items():
        faces.append(named[key])
        uvs.append(mapped)
    emit(part, kit.Geo(points, faces, uvs), name, None, "texture", False)


def track_far(name="rail_track_far"):
    b = rk.Build(name, 12)
    rng = b.rng
    part = b.part("track", 30.0)
    segments = 8
    xs = [-toe, -shoulder, shoulder, toe]
    zs = [toe_level, ballast_top, ballast_top, toe_level]
    arc = [0.0, 0.966, 4.166, 5.132]
    points = []
    for j in range(segments + 1):
        for x, z in zip(xs, zs):
            points.append(V(x, panel * j / segments, z))
    faces = []
    uvs = []
    for j in range(segments):
        for i in range(3):
            a = j * 4 + i
            faces.append((a, a + 1, a + 5, a + 4))
            va = panel * j / segments / ballast_tile
            vb = panel * (j + 1) / segments / ballast_tile
            uvs.append([(arc[i] / ballast_tile + 0.13, va), (arc[i + 1] / ballast_tile + 0.13, va), (arc[i + 1] / ballast_tile + 0.13, vb), (arc[i] / ballast_tile + 0.13, vb)])
    emit(part, kit.Geo(points, faces, uvs), "ballast_stone", None, "texture", True)
    b0, b1 = rk.rail_rows["bright"]
    s0, s1 = rk.rail_rows["side"]
    for sign in (-1.0, 1.0):
        c = sign * (gauge * 0.5 + 0.035)
        outline = [(c - 0.04, 0.36), (c - 0.035, rail_top), (c + 0.035, rail_top), (c + 0.04, 0.36)]
        points = []
        for j in range(segments + 1):
            for x, z in outline:
                points.append(V(x, panel * j / segments, z))
        faces = []
        uvs = []
        inner_first = sign > 0.0
        bands = [((s1 - 40.0) / rk.size, (s0 + 4.0) / rk.size), ((b0 + 2.0) / rk.size, (b1 - 2.0) / rk.size) if inner_first else ((b1 - 2.0) / rk.size, (b0 + 2.0) / rk.size), ((s0 + 4.0) / rk.size, (s1 - 40.0) / rk.size)]
        for j in range(segments):
            for i in range(3):
                a = j * 4 + i
                ua = panel * j / segments / 1.5
                ub = panel * (j + 1) / segments / 1.5
                faces.append((a, a + 1, a + 5, a + 4))
                uvs.append([(ua, bands[i][0]), (ua, bands[i][1]), (ub, bands[i][1]), (ub, bands[i][0])])
        emit(part, kit.Geo(points, faces, uvs), "rail_steel", None, "texture", False)
    for index in range(sleeper_count):
        y = (index + 0.5) * sleeper_pitch
        strip = rng.randrange(rk.strip_count)
        v0 = (strip * rk.strip_rows + 2.0) / rk.size
        v1 = ((strip + 1) * rk.strip_rows - 2.0) / rk.size
        vm = (v0 + v1) * 0.5
        tile = rng.randrange(8)
        e0 = (rk.strip_count * rk.strip_rows + (tile // 4) * rk.end_rows + 3.0) / rk.size
        e1 = (rk.strip_count * rk.strip_rows + (tile // 4 + 1) * rk.end_rows - 3.0) / rk.size
        c0 = (tile % 4) * 0.25 + 0.006
        c1 = (tile % 4 + 1) * 0.25 - 0.006
        mapped = {"top": [(0.0, v0), (1.0, v0), (1.0, v1), (0.0, v1)], "front": [(0.0, vm), (1.0, vm), (1.0, v0), (0.0, v0)], "back": [(1.0, vm), (0.0, vm), (0.0, v1), (1.0, v1)], "left": [(c0, e0), (c0, e1), (c1, e1), (c1, e0)], "right": [(c0, e0), (c1, e0), (c1, e1), (c0, e1)]}
        far_box(part, "sleeper_timber", V(-1.3, y - 0.125, ballast_top - 0.02), V(1.3, y + 0.125, sleeper_top), mapped)
    return b


models = {
    "rail_track": (track, track_far, 40000, 400),
    "rail_track_weeds": (track_weeds, lambda: track_far("rail_track_weeds_far"), 50000, 400),
}
models.update(rt.models)
models.update(rs.models)


def build(name):
    maker, far_maker, budget, far_budget = models[name]
    rk.register()
    kit.reset_scene()
    started = time.time()
    b = maker()
    objects = b.finish()
    path, document = rk.export_model(name, objects, getattr(b, "externals", None))
    result = rk.audit(path, document, budget)
    print("BUILD", name, "parts", len(b.parts), "boxes", len(b.boxes), round(time.time() - started, 1), "s", flush=True)
    far_result = None
    if far_maker is not None:
        kit.reset_scene()
        far = far_maker()
        objects = far.finish()
        path, document = rk.export_model(name + "_far", objects, getattr(far, "externals", None))
        far_result = rk.audit(path, document, far_budget)
    if name in rt.models:
        rt.record(name, result["triangles"], far_result["triangles"] if far_result else 0, result["low"], result["high"])
    failed = result["problems"] + (far_result["problems"] if far_result else [])
    if failed:
        raise SystemExit("AUDIT FAILED " + name + " " + str(failed))


def place(name, offset=(0.0, 0.0, 0.0), yaw=0.0):
    objects = kit.import_building(name)
    matrix = Matrix.Translation(V(*offset)) @ Matrix.Rotation(yaw, 4, 'Z')
    for obj in objects:
        if obj.parent is None:
            obj.matrix_world = matrix @ obj.matrix_world
    boxes = []
    kit.bpy.context.view_layer.update()
    for obj in objects:
        if obj.type == 'MESH' and kit.is_marker(obj.name):
            obj.hide_render = True
            low, high = kit.world_bounds([obj])
            boxes.append((obj.name, low, high))
    rk.fix_alpha(objects)
    return objects, boxes


def place_vehicle(name, offset=(0.0, 0.0, 0.0), far=False):
    suffix = "_far" if far else ""
    objects, boxes = place(name + suffix, offset)
    for y in rt.specs[name]["axles"]:
        wheels, unused = place("train_wheelset" + suffix, (offset[0], offset[1] + y, offset[2] + rt.wheel_radius))
        objects += wheels
    return objects, boxes


def remove(obj):
    kit.bpy.data.objects.remove(obj)


def shot(path, position, target, lens=35.0, exposure=0.0, fill=None, clip=0.05, resolution=(1600, 900)):
    kit.render_settings(samples, resolution, exposure)
    kit.bpy.context.scene.cycles.transparent_max_bounces = 32
    cam = kit.camera(V(*position), V(*target), lens, None, clip)
    light = kit.point_light(V(*position) + V(0.0, 0.0, 0.3), fill, 0.4, (1.0, 0.93, 0.85)) if fill else None
    kit.shoot(path)
    remove(cam)
    if light is not None:
        remove(light)


def preview_track(name, which=None):
    kit.reset_scene()
    rk.register()
    other = "rail_track_weeds" if os.path.exists(os.path.join(kit.models_root, "rail_track_weeds", "rail_track_weeds.gltf")) else "rail_track"
    for index, model in enumerate((other if name == "rail_track" else "rail_track", name, other if name == "rail_track" else "rail_track")):
        place(model, (0.0, (index - 1) * panel, 0.0))
    kit.daylight(1.0, 3.2, (0.55, 0.5, -0.62))
    kit.ground(-0.002, 400.0)
    prefix = os.path.join(rk.preview_root, name + "_")
    todo = which or ["three", "detail", "joint", "along", "side"]
    if "three" in todo:
        shot(prefix + "three.png", (5.2, -2.6, 2.7), (0.0, 5.2, 0.2), 32.0)
    if "detail" in todo:
        shot(prefix + "detail.png", (1.75, 4.55, 0.78), (0.62, 5.62, 0.36), 45.0)
    if "joint" in todo:
        shot(prefix + "joint.png", (-1.75, -0.95, 0.85), (-0.72, 0.1, 0.4), 50.0)
    if "along" in todo:
        shot(prefix + "along.png", (0.25, -5.5, 1.64), (0.0, 12.0, 0.2), 28.0)
    if "side" in todo:
        shot(prefix + "side.png", (7.5, 6.0, 1.7), (0.0, 6.0, 0.35), 30.0)


on_track = [("rail_track", (0.0, -6.0, -0.5))]
sun_side = (-0.5, -0.45, -0.7)
views = {
    "train_wheelset": {
        "ground": -0.48,
        "sun": sun_side,
        "shots": [("three", (1.9, 1.5, 0.75), (0.2, 0.0, 0.0), 40.0, 0.0, None)],
    },
    "train_locomotive": {
        "context": on_track,
        "ground": -0.502,
        "sun": sun_side,
        "shots": [
            ("three", (6.2, 8.0, 3.3), (0.0, 0.2, 1.5), 35.0, 0.0, None),
            ("rear", (-5.6, -8.2, 3.2), (0.0, -0.6, 1.6), 35.0, 0.0, None),
            ("detail", (3.2, 5.2, 1.5), (0.8, 2.9, 1.0), 40.0, 0.0, None),
            ("wheels", (3.4, 0.9, 0.75), (0.7, 0.3, 0.75), 35.0, 0.6, None),
            ("cab", (0.0, -2.35, 2.925), (-0.1, -0.7, 2.5), 14.0, 2.2, 16.0),
            ("cab_rear", (-0.35, -1.25, 2.925), (0.45, -2.6, 2.45), 15.0, 2.2, 16.0),
            ("front", (1.1, 5.9, 2.3), (0.0, 2.56, 2.05), 35.0, 0.0, None),
            ("engine", (2.1, 1.25, 2.05), (0.2, 1.4, 1.8), 26.0, 1.4, 10.0),
            ("under", (3.4, 0.6, 0.42), (0.0, -0.4, 0.42), 24.0, 1.0, 12.0),
        ],
        "levels": [("STEPS", 1.22, -0.5, 1.0), ("FOOTPLATE", 3.2, 1.0, 3.3), ("ROOF", 5.0, 3.3, 4.0)],
    },
    "train_wagon_flat": {
        "context": on_track,
        "ground": -0.502,
        "sun": sun_side,
        "shots": [
            ("three", (5.4, 6.6, 3.0), (0.0, 0.2, 1.0), 35.0, 0.0, None),
            ("detail", (3.1, 4.2, 1.3), (0.9, 2.3, 0.75), 40.0, 0.3, None),
        ],
        "levels": [("STEPS", 1.22, -0.5, 1.0), ("DECK", 4.0, 1.0, 3.0)],
    },
    "train_wagon_open": {
        "context": on_track,
        "ground": -0.502,
        "sun": sun_side,
        "shots": [
            ("three", (-5.4, 6.6, 3.4), (0.0, 0.2, 1.2), 35.0, 0.0, None),
            ("detail", (3.4, -5.0, 2.6), (0.4, -2.0, 1.5), 40.0, 0.0, None),
            ("inside", (0.0, 1.6, 2.91), (0.1, -1.6, 1.9), 18.0, 0.4, None),
        ],
        "levels": [("STEPS", 1.22, -0.5, 1.0), ("FLOOR", 4.0, 1.0, 3.0)],
    },
    "train_wagon_box": {
        "context": on_track,
        "ground": -0.502,
        "sun": sun_side,
        "shots": [
            ("three", (5.6, 6.6, 3.3), (0.0, 0.2, 1.9), 35.0, 0.0, None),
            ("detail", (-4.2, -5.0, 2.4), (-0.4, -1.4, 1.8), 40.0, 0.0, None),
            ("inside", (0.0, -1.7, 2.91), (0.15, 1.9, 2.2), 15.0, 1.6, 12.0),
        ],
        "levels": [("STEPS", 1.22, -0.5, 1.0), ("FLOOR", 3.2, 1.0, 3.3), ("ROOF", 5.0, 3.3, 4.0)],
    },
    "train_coach": {
        "context": [("rail_track", (0.0, -12.0, -0.5)), ("rail_track", (0.0, 0.0, -0.5))],
        "ground": -0.502,
        "sun": sun_side,
        "shots": [
            ("three", (7.0, 10.5, 3.6), (0.0, 0.6, 1.8), 35.0, 0.0, None),
            ("detail", (3.6, 7.6, 2.3), (0.6, 4.6, 1.5), 40.0, 0.0, None),
            ("bogie", (3.6, 3.6, 0.9), (0.8, 3.0, 0.7), 35.0, 0.6, None),
            ("inside", (0.0, -4.1, 2.91), (0.0, 1.0, 2.4), 15.0, 1.4, 14.0),
            ("inside_bay", (0.35, 0.3, 2.91), (-1.2, -1.6, 2.2), 15.0, 1.4, 14.0),
        ],
        "levels": [("STEPS", 1.22, -0.5, 1.0), ("FLOOR", 3.2, 1.0, 3.3), ("ROOF", 5.0, 3.3, 4.0)],
    },
    "rail_platform": {
        "context": [("rail_track", (-12.0, -3.45, 0.0), -math.pi * 0.5), ("rail_track", (0.0, -3.45, 0.0), -math.pi * 0.5), ("rail_platform_end", (8.5, 0.0, 0.0), 0.0), ("rail_platform_end", (-8.5, 0.0, 0.0), math.pi)],
        "shots": [
            ("three", (10.5, -9.5, 5.2), (0.5, -0.5, 1.0), 35.0, 0.0, None),
            ("detail", (2.6, -4.3, 2.5), (0.2, -1.5, 1.55), 40.0, 0.0, None),
        ],
        "levels": [("TOP", 6.0, -1.0, 3.0)],
    },
    "rail_platform_end": {
        "context": [("rail_track", (-6.0, -3.45, 0.0), -math.pi * 0.5), ("rail_platform", (-8.5, 0.0, 0.0), 0.0)],
        "shots": [
            ("three", (7.0, -7.0, 3.6), (0.0, -0.5, 0.8), 35.0, 0.0, None),
            ("detail", (3.6, -3.4, 1.5), (1.2, -1.2, 0.5), 40.0, 0.0, None),
        ],
        "levels": [("TOP", 6.0, -1.0, 3.0)],
    },
    "rail_buffer": {
        "context": [("rail_track", (0.0, -9.6, 0.0))],
        "shots": [
            ("three", (4.2, -4.4, 2.6), (0.0, 0.6, 1.0), 35.0, 0.0, None),
            ("detail", (-1.9, -1.6, 1.9), (0.2, 0.4, 1.4), 40.0, 0.0, None),
        ],
        "levels": [("TOP", 6.0, 0.0, 3.0)],
    },
    "rail_signal": {
        "context": [("rail_track", (2.4, -6.0, 0.0))],
        "shots": [
            ("three", (2.6, -9.5, 3.4), (0.0, 0.0, 3.7), 28.0, 0.0, None),
            ("detail", (1.6, -3.4, 5.6), (-0.1, 0.0, 6.2), 45.0, 0.0, None),
            ("base", (1.9, -2.2, 1.3), (0.0, 0.1, 0.8), 40.0, 0.0, None),
        ],
    },
    "rail_crossing": {
        "context": [("rail_track", (0.0, -12.0, 0.0)), ("rail_track", (0.0, 0.0, 0.0))],
        "shots": [
            ("three", (9.0, -8.0, 4.6), (0.0, 0.0, 0.5), 35.0, 0.0, None),
            ("detail", (5.6, 0.6, 1.5), (2.6, 2.6, 0.8), 40.0, 0.0, None),
            ("road", (8.5, -0.4, 1.64), (0.0, 0.0, 0.7), 30.0, 0.0, None),
        ],
        "levels": [("TOP", 6.0, -0.5, 3.0)],
    },
    "rail_crossing_gate": {
        "context": [("rail_crossing_post", (-0.205, 0.0, 0.0)), ("rail_crossing_post", (4.905, 0.0, 0.0), math.pi), ("rail_crossing_gate", (4.7, 0.0, 0.0), math.pi), ("rail_crossing_sign", (-1.3, -1.4, 0.0), 0.0)],
        "shots": [
            ("three", (4.6, -5.6, 2.1), (2.1, 0.0, 0.95), 35.0, 0.0, None),
            ("detail", (0.95, -1.25, 1.35), (0.15, 0.0, 0.85), 40.0, 0.0, None),
            ("back", (1.6, 3.4, 1.5), (1.5, 0.0, 0.85), 35.0, 0.0, None),
        ],
    },
    "rail_crossing_post": {
        "context": [("rail_crossing_gate", (0.205, 0.0, 0.0), math.radians(-35.0))],
        "shots": [
            ("three", (1.7, -2.6, 2.2), (0.1, 0.0, 1.45), 35.0, 0.0, None),
            ("lamp", (0.75, -1.05, 2.6), (0.0, 0.0, 2.3), 40.0, 0.0, None),
        ],
        "levels": [("TOP", 3.2, 0.0, 2.7)],
    },
    "rail_crossing_sign": {
        "shots": [
            ("three", (0.9, -2.3, 1.75), (0.0, 0.0, 1.6), 35.0, 0.0, None),
            ("detail", (0.25, -1.05, 1.95), (0.0, 0.0, 1.85), 40.0, 0.0, None),
            ("back", (-1.0, 1.9, 1.8), (0.0, 0.0, 1.6), 35.0, 0.0, None),
        ],
        "levels": [("TOP", 3.0, 0.0, 2.4)],
    },
    "rail_water_tower": {
        "context": [("rail_track", (-6.0, -3.6, 0.0), -math.pi * 0.5)],
        "shots": [
            ("three", (6.8, -8.2, 3.4), (0.3, -0.4, 2.7), 35.0, 0.0, None),
            ("detail", (3.6, -4.4, 3.6), (0.4, -1.6, 4.1), 40.0, 0.0, None),
            ("rear", (-4.6, 6.4, 2.4), (0.0, 0.2, 2.4), 35.0, 0.0, None),
        ],
    },
    "rail_signal_box": {
        "context": [("rail_track", (-6.0, -4.2, 0.0), -math.pi * 0.5)],
        "shots": [
            ("three", (6.6, -7.4, 3.4), (0.0, -0.2, 2.6), 35.0, 0.0, None),
            ("rear", (-6.6, 5.6, 3.6), (-0.4, 0.0, 2.4), 35.0, 0.0, None),
            ("detail", (-4.6, -3.6, 2.2), (-2.3, -0.4, 2.0), 40.0, 0.0, None),
            ("inside", (-1.5, 0.7, 3.965), (0.7, -1.1, 3.5), 15.0, 1.0, 8.0),
            ("inside_rear", (1.2, -0.6, 3.965), (-0.4, 1.3, 3.7), 15.0, 1.0, 8.0),
            ("ground", (1.2, 0.8, 1.64), (-0.8, -0.9, 1.0), 15.0, 1.6, 10.0),
        ],
        "levels": [("GROUND", 2.1, -0.5, 2.1), ("CABIN", 4.4, 2.1, 4.6), ("ROOF", 8.0, 4.6, 7.0)],
    },
    "bld_station": {
        "context": [("rail_platform", (0.0, -4.5, -1.7)), ("rail_platform_end", (8.5, -4.5, -1.7), 0.0), ("rail_platform_end", (-8.5, -4.5, -1.7), math.pi), ("rail_track", (-12.0, -7.95, -1.7), -math.pi * 0.5), ("rail_track", (0.0, -7.95, -1.7), -math.pi * 0.5)],
        "ground": -1.702,
        "shots": [
            ("three", (10.5, -14.0, 3.4), (0.4, -2.6, 1.2), 35.0, 0.0, None),
            ("rear", (-10.0, 10.5, 4.2), (0.0, 0.6, 1.4), 35.0, 0.0, None),
            ("detail", (4.4, -6.6, 1.6), (1.6, -2.9, 1.5), 35.0, 0.3, None),
            ("waiting", (-0.2, 1.1, 1.64), (-5.0, -0.7, 1.25), 15.0, 1.2, 14.0),
            ("hatch", (-4.7, -1.1, 1.64), (0.6, -0.4, 1.55), 16.0, 1.2, 14.0),
            ("office", (4.9, -1.4, 1.64), (0.8, 0.4, 1.2), 15.0, 1.2, 14.0),
            ("steps", (1.2, 10.4, 0.2), (-3.0, 4.2, -0.8), 30.0, 0.0, None),
            ("steps_top", (-3.0, 2.2, 1.64), (-3.0, 5.6, -1.4), 28.0, 0.3, None),
        ],
        "levels": [("YARD", -0.06, -1.8, -0.06), ("FLOOR", 2.9, -0.5, 2.9), ("ROOF", 9.0, 2.9, 7.0)],
    },
}


def preview_model(name, which=None):
    spec = views[name]
    kit.reset_scene()
    rk.register()
    objects, boxes = place_vehicle(name) if name in rt.specs else place(name)
    for entry in spec.get("context", []):
        place(entry[0], entry[1], entry[2] if len(entry) > 2 else 0.0)
    kit.daylight(1.0, 3.2, spec.get("sun", (0.55, 0.5, -0.62)))
    kit.ground(spec.get("ground", -0.002), 400.0)
    prefix = os.path.join(rk.preview_root, name + "_")
    for key, position, target, lens, exposure, fill in spec["shots"]:
        if which and key not in which:
            continue
        shot(prefix + key + ".png", position, target, lens, exposure, fill, 0.03 if fill else 0.05)
    if "levels" in spec and (not which or "plan" in which):
        visual = [obj for obj in objects if obj.type == 'MESH' and not kit.is_marker(obj.name)]
        low, high = kit.world_bounds(visual)
        kit.plan_sheet(name, spec["levels"], boxes, low, high, max(24, samples // 3), prefix + "plan.png")


previews = {
    "rail_track": preview_track,
    "rail_track_weeds": preview_track,
}
consist = ["train_locomotive", "train_coach", "train_wagon_box", "train_wagon_open", "train_wagon_flat"]


def place_train(names, front_x, y, z):
    turn = -math.pi * 0.5
    x = front_x
    for name in names:
        length = rt.specs[name]["length_over_buffers"]
        center = x - length * 0.5
        place(name, (center, y, z), turn)
        for axle in rt.specs[name]["axles"]:
            place("train_wheelset", (center + axle, y, z + rt.wheel_radius), turn)
        x = center - length * 0.5 - rt.coupling_gap


def preview_scene(which=None):
    kit.reset_scene()
    rk.register()
    formation = -rs.platform_top
    platform_y = -rs.station_hy - rs.platform_half
    line = platform_y - rs.platform_half - rs.platform_offset
    place("bld_station")
    place("rail_platform", (0.0, platform_y, formation))
    place("rail_platform_end", (8.5, platform_y, formation), 0.0)
    place("rail_platform_end", (-8.5, platform_y, formation), math.pi)
    for index, x in enumerate((-36.0, -24.0, -12.0, 0.0, 12.0, 24.0)):
        place("rail_track_weeds" if index % 2 else "rail_track", (x, line, formation), -math.pi * 0.5)
    place_train(consist, 14.4, line, formation + rs.rail_top)
    place("rail_signal", (22.0, line + 2.4, formation), -math.pi * 0.5)
    place("rail_signal_box", (-20.0, line + 4.2, formation), 0.0)
    place("rail_water_tower", (-33.0, line + 3.6, formation), 0.0)
    kit.daylight(1.0, 3.2, (0.42, 0.56, -0.62))
    kit.ground(formation - 0.002, 600.0)
    prefix = os.path.join(rk.preview_root, "railway_scene_")
    todo = which or ["train", "overview", "platform"]
    if "train" in todo:
        shot(prefix + "train.png", (-5.0, line - 46.0, 1.2), (-5.0, line, -0.1), 35.0, 0.0, None, 0.05, (2400, 900))
    if "overview" in todo:
        shot(prefix + "overview.png", (26.0, line - 30.0, 13.0), (-6.0, -4.0, -1.0), 30.0)
    if "platform" in todo:
        shot(prefix + "platform.png", (-4.0, -3.4, 1.62), (14.0, line + 0.8, 0.4), 24.0)


sheet_rows = [
    ("track", [("plain", "rail_track_three"), ("weeds", "rail_track_weeds_three"), ("joint", "rail_track_joint"), ("along", "rail_track_along")]),
    ("wheelset", [("three", "train_wheelset_three")]),
    ("locomotive", [("three", "train_locomotive_three"), ("rear", "train_locomotive_rear"), ("front", "train_locomotive_front"), ("engine", "train_locomotive_engine"), ("under", "train_locomotive_under"), ("cab", "train_locomotive_cab")]),
    ("flat wagon", [("three", "train_wagon_flat_three"), ("detail", "train_wagon_flat_detail"), ("plan", "train_wagon_flat_plan")]),
    ("open wagon", [("three", "train_wagon_open_three"), ("detail", "train_wagon_open_detail"), ("inside", "train_wagon_open_inside"), ("plan", "train_wagon_open_plan")]),
    ("box van", [("three", "train_wagon_box_three"), ("detail", "train_wagon_box_detail"), ("inside", "train_wagon_box_inside"), ("plan", "train_wagon_box_plan")]),
    ("coach", [("three", "train_coach_three"), ("detail", "train_coach_detail"), ("bogie", "train_coach_bogie"), ("inside", "train_coach_inside"), ("bay", "train_coach_inside_bay"), ("plan", "train_coach_plan")]),
    ("platform", [("three", "rail_platform_three"), ("detail", "rail_platform_detail"), ("end", "rail_platform_end_three"), ("end detail", "rail_platform_end_detail")]),
    ("buffer signal", [("buffer", "rail_buffer_three"), ("buffer detail", "rail_buffer_detail"), ("signal", "rail_signal_three"), ("signal arm", "rail_signal_detail"), ("signal base", "rail_signal_base")]),
    ("crossing", [("three", "rail_crossing_three"), ("detail", "rail_crossing_detail"), ("road", "rail_crossing_road")]),
    ("crossing kit", [("gates", "rail_crossing_gate_three"), ("gate back", "rail_crossing_gate_back"), ("post", "rail_crossing_post_three"), ("lamp", "rail_crossing_post_lamp"), ("sign", "rail_crossing_sign_three"), ("sign detail", "rail_crossing_sign_detail")]),
    ("water tower", [("three", "rail_water_tower_three"), ("detail", "rail_water_tower_detail"), ("rear", "rail_water_tower_rear")]),
    ("signal box", [("three", "rail_signal_box_three"), ("rear", "rail_signal_box_rear"), ("inside", "rail_signal_box_inside"), ("ground", "rail_signal_box_ground"), ("plan", "rail_signal_box_plan")]),
    ("station", [("three", "bld_station_three"), ("rear", "bld_station_rear"), ("steps", "bld_station_steps"), ("waiting", "bld_station_waiting"), ("office", "bld_station_office"), ("plan", "bld_station_plan")]),
    ("scene", [("train", "railway_scene_train"), ("overview", "railway_scene_overview"), ("platform", "railway_scene_platform")]),
]


def write_railway_sheet():
    rows = [(title, [(label, os.path.join(rk.preview_root, stem + ".png")) for label, stem in entries]) for title, entries in sheet_rows]
    kit.contact_sheet(rows, os.path.join(rk.preview_root, "railway_sheet.png"), (400, 225))


def main():
    started = time.time()
    os.makedirs(rk.preview_root, exist_ok=True)
    kit.preview_root = rk.preview_root
    if mode == "library":
        rk.build_library(wanted)
    elif mode == "build":
        for name in wanted or list(models):
            build(name)
    elif mode == "preview":
        which = arguments[3].split(",") if len(arguments) > 3 else None
        for name in wanted or list(previews) + list(views):
            previews.get(name, preview_model)(name, which)
    elif mode == "scene":
        preview_scene([name for name in wanted if name != "all"] or None)
    elif mode == "sheet":
        write_railway_sheet()
    print("DONE", mode, round(time.time() - started, 1), "s", flush=True)


if __name__ == "__main__":
    main()
