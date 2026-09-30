import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
from buildkit import V, block, emit, rod, local_block
from mathutils import Matrix, Vector

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
buffer_height = 1.05
hook_height = 1.0
buffer_spread = 0.86
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


def end_gear(b, part, y, direction, rng, body="loco_black", oval=1.0, stock=0.26, links=3, pipe=True):
    forward = V(0.0, direction, 0.0)
    for side in (-1.0, 1.0):
        rk.buffer(part, V(side * buffer_spread, y, buffer_height), forward, body, "rust_iron", stock, 0.5, oval)
    rk.drawgear(part, V(0.0, y, hook_height), forward, rng, body, "rust_iron", links)
    if not pipe:
        return
    pipe_x = -0.34 * direction
    rk.pipe(part, body, [V(pipe_x, y - 0.06 * direction, 0.55), V(pipe_x, y + 0.035 * direction, 0.62), V(pipe_x, y + 0.035 * direction, 1.16), V(pipe_x, y + 0.13 * direction, 1.22)], 0.022, 8, 0.05)
    hose = [V(pipe_x, y + 0.13 * direction, 1.22), V(pipe_x - 0.02, y + 0.2 * direction, 1.12), V(pipe_x - 0.06, y + 0.17 * direction, 0.86), V(pipe_x - 0.1, y + 0.06 * direction, 0.74)]
    rk.pipe(part, "loco_black", hose, 0.03, 8, 0.08)
    rk.lathe(part, "rust_iron", hose[-1], V(0.0, -direction, -0.4), [(0.0, -0.02), (0.045, -0.02), (0.045, 0.02), (0.03, 0.03), (0.0, 0.03)], 10)


def wasp_face(part, y, direction, x_half, z0, z1):
    for side in (-1.0, 1.0):
        xa, xb = (0.0, x_half) if side > 0 else (-x_half, 0.0)
        corners = [V(xa, y, z0), V(xb, y, z0), V(xb, y, z1), V(xa, y, z1)]
        geo = rk.facing(kit.Geo(corners, [(0, 1, 2, 3)]), V(0.0, direction, 0.0))
        rk.planar(part, geo, "wasp_stripes", V(0.0, y, z0), V(side, 0.0, 0.0), Z)


def wasp_beam(part, y, direction, x_half, z0, z1, thickness=0.035):
    back_y = y - thickness * direction
    wasp_face(part, y, direction, x_half, z0, z1)
    block(part, "loco_black", V(-x_half, min(y, back_y), z0), V(x_half, max(y, back_y), z1), 0.0, "box", None, ("front",) if direction < 0 else ("back",))


def lamp_iron(part, position, direction):
    side = Z.cross(direction).normalized()
    rk.bar(part, "loco_black", [position, position + direction * 0.05, position + direction * 0.05 + Z * 0.16], 0.008, 0.04, side, 0.0)


def oil_lamp(part, position, direction):
    frame = kit.place(position, direction, Z)
    side = Z.cross(direction).normalized()
    local_block(part, "loco_black", frame, -0.07, 0.07, -0.075, 0.075, 0.0, 0.2, 0.008)
    emit(part, kit.geo_lathe([(0.0, 0.2), (0.06, 0.2), (0.045, 0.235), (0.03, 0.245), (0.03, 0.275), (0.0, 0.28)], 10), "loco_black", Matrix.Translation(position), "given", True)
    rk.lathe(part, "loco_black", position + direction * 0.07 + Z * 0.1, direction, [(0.062, 0.0), (0.062, 0.02), (0.05, 0.026)], 14)
    rk.atlas_disc(part, "lens_clear", position + direction * 0.095 + Z * 0.1, direction, Z, 0.05, 12)
    handle = [position + Z * 0.28 + side * 0.05, position + Z * 0.34 + side * 0.04, position + Z * 0.34 - side * 0.04, position + Z * 0.28 - side * 0.05]
    rk.pipe(part, "rust_iron", handle, 0.005, 5, 0.015)


def round_lamp(part, position, direction, radius=0.085, lens="lens_clear", body="loco_black"):
    rk.lathe(part, body, position, direction, [(0.0, -0.09), (radius * 0.6, -0.085), (radius, -0.03), (radius, 0.03), (radius * 0.88, 0.04), (radius * 0.84, 0.02)], 16)
    rk.atlas_disc(part, lens, position + direction.normalized() * 0.02, direction, Z if abs(direction.z) < 0.9 else Y, radius * 0.84, 14)


def brake_block(part, x, y, z, direction):
    frame = kit.place(V(x, y, z), V(0.0, direction, 0.0), Z)
    local_block(part, "rust_iron", frame, 0.0, 0.05, -0.05, 0.05, -0.13, 0.13, 0.008)
    rk.bar(part, "loco_black", [V(x, y + direction * 0.02, z + 0.1), V(x - math.copysign(0.1, x), y + direction * 0.02, z + 0.62)], 0.05, 0.015, Y)


def sandbox(part, rng, side, y0, y1, wheel_y):
    x0, x1 = sorted((side * 0.92, side * 1.22))
    block(part, "loco_black", V(x0, y0, 0.78), V(x1, y1, 1.24), 0.012)
    local_block(part, "loco_black", Matrix.Translation(V((x0 + x1) * 0.5, (y0 + y1) * 0.5, 1.30)), -0.1, 0.1, -0.1, 0.1, 0.0, 0.02, 0.005)
    rk.lathe(part, "rust_iron", V((x0 + x1) * 0.5, (y0 + y1) * 0.5, 1.32), Z, [(0.0, 0.0), (0.03, 0.0), (0.03, 0.025), (0.0, 0.03)], 8)
    toward = 1.0 if wheel_y > (y0 + y1) * 0.5 else -1.0
    start = V(side * 1.0, y1 if toward > 0 else y0, 0.8)
    rk.pipe(part, "rust_iron", [start, V(side * 0.86, start.y + toward * 0.04, 0.62), V(side * 0.76, wheel_y - toward * 0.56, 0.32), V(side * 0.755, wheel_y - toward * 0.36, 0.09)], 0.017, 6, 0.08)


loco_axles = (1.5, 0.1, -1.3)
loco_radius = 0.546
open_door = (1.0, 2)


def loco_frames(b, rng):
    frame = b.part("frame", 40.0, 50)
    detail = b.part("detail", 40.0)
    rk.slab(frame, V(-1.3, -3.5, 1.26), V(1.3, 3.5, 1.30), "chequer_plate", "loco_black")
    for side in (-1.0, 1.0):
        block(frame, "loco_black", V(side * 1.27, -3.46, 1.14), V(side * 1.3, 3.46, 1.26))
        rk.rivets(detail, "loco_black", V(side * 1.3, -3.4, 1.2), V(side * 1.3, 3.4, 1.2), 0.17, V(side, 0.0, 0.0), 0.011)
        block(frame, "loco_black", V(side * 0.58, -3.46, 0.42), V(side * 0.62, 3.46, 1.26))
        for y in (-3.4, -2.3, 2.45, 3.4):
            block(frame, "loco_black", V(side * 0.62, y - 0.012, 0.9), V(side * 1.27, y + 0.012, 1.26))
        for end in (-1.0, 1.0):
            rk.bar(detail, "loco_black", [V(side * 0.755, end * 3.44, 0.74), V(side * 0.755, end * 3.38, 0.4), V(side * 0.755, end * 3.3, 0.085)], 0.022, 0.07, X)
    block(frame, "loco_black", V(-0.45, -3.1, 0.5), V(0.45, 3.1, 1.26))
    block(frame, "loco_black", V(-0.58, -0.35, 0.3), V(0.58, 0.5, 0.62), 0.03)
    for y in (-2.2, -0.6, 0.85, 2.3):
        block(frame, "loco_black", V(-0.58, y - 0.02, 0.62), V(0.58, y + 0.02, 1.2))
    for direction in (-1.0, 1.0):
        y = direction * 3.5
        wasp_beam(frame, y, direction, 1.28, 0.7, 1.3)
        for side in (-1.0, 1.0):
            rk.rivets(detail, "rust_iron", V(side * 1.22, y, 0.76), V(side * 1.22, y, 1.24), 0.12, V(0.0, direction, 0.0), 0.012)
            rk.rivets(detail, "rust_iron", V(side * 0.62, y, 0.76), V(side * 0.62, y, 1.24), 0.12, V(0.0, direction, 0.0), 0.012)
        end_gear(b, detail, y, direction, rng)
        for x in (-0.95, 0.0, 0.95):
            lamp_iron(detail, V(x, y - direction * 0.06, 1.30), V(0.0, direction, 0.0))
    oil_lamp(detail, V(0.95, 3.49, 1.46), Y)
    oil_lamp(detail, V(-0.95, -3.49, 1.46), -Y)
    tops = [0.1, 0.5, 0.9]
    outs = [1.7, 1.57, 1.44]
    for side in (-1.0, 1.0):
        rk.steps_unit(b, frame, side, -3.15, -2.3, tops, outs)
        rk.steps_unit(b, frame, side, 2.9, 3.44, tops, outs)
        sandbox(frame, rng, side, 2.12, 2.5, loco_axles[0])
        sandbox(frame, rng, side, -2.25, -1.9, loco_axles[2])
        for axle in loco_axles:
            brake_block(detail, side * 0.755, axle - 0.585, loco_radius, 1.0)
    block(frame, "loco_black", V(-1.22, -3.2, 0.62), V(-0.7, -2.4, 1.2), 0.02)
    rk.lathe(detail, "rust_iron", V(-1.22, -2.62, 1.05), V(-1.0, 0.0, 0.6), [(0.0, 0.0), (0.04, 0.0), (0.04, 0.06), (0.055, 0.06), (0.055, 0.085), (0.0, 0.09)], 10)
    for y in (-3.05, -2.55):
        block(detail, "rust_iron", V(-1.23, y - 0.02, 0.6), V(-0.69, y + 0.02, 1.21))
    tank = Matrix.Translation(V(0.95, -3.2, 0.85)) @ Matrix.Rotation(-math.pi * 0.5, 4, 'X')
    emit(frame, kit.geo_lathe([(0.0, 0.0), (0.12, 0.0), (0.2, 0.05), (0.2, 0.8), (0.12, 0.85), (0.0, 0.85)], 20), "loco_black", tank, "given", True)
    for offset in (0.2, 0.65):
        emit(detail, kit.geo_lathe([(0.205, offset - 0.02), (0.212, offset - 0.02), (0.212, offset + 0.02), (0.205, offset + 0.02)], 20), "rust_iron", tank, "given", True)
    rk.pipe(detail, "rust_iron", [V(0.95, -2.75, 0.65), V(0.95, -2.75, 0.56), V(0.7, -2.75, 0.56), V(0.7, -1.95, 0.56)], 0.012, 6, 0.03)
    b.col("metal", "frame", V(-1.3, -3.5, 0.35), V(1.3, 3.5, 1.3))
    for number, axle in enumerate(loco_axles):
        rk.wheelset(b, "wheel_%d" % (number + 1), axle, loco_radius, 10, "loco_black", True, segments=64)
        for side in (-1.0, 1.0):
            block(frame, "loco_black", V(side * 0.62, axle - 0.13, 0.42), V(side * 0.676, axle + 0.13, 0.68), 0.01)
            for offset in (-0.165, 0.165):
                block(frame, "loco_black", V(side * 0.62, axle + offset - 0.025, 0.34), V(side * 0.662, axle + offset + 0.025, 0.96))
            block(frame, "rust_iron", V(side * 0.62, axle - 0.2, 0.31), V(side * 0.662, axle + 0.2, 0.345))
            for offset in (-0.165, 0.165):
                rk.prism_bolt(detail, "rust_iron", V(side * 0.641, axle + offset, 0.31), -Z, 0.03, 0.016, 6)
    for direction in (-1.0, 1.0):
        for z in (0.745, 1.255):
            rk.rivets(detail, "rust_iron", V(-1.15, direction * 3.5, z), V(1.15, direction * 3.5, z), 0.144, V(0.0, direction, 0.0), 0.012)
    return frame, detail


def bonnet_outline(half, base, top, radius, steps=4):
    points = [(half, base), (half, top - radius)]
    points += rk.arc_points(half - radius, top - radius, radius, 0.0, math.pi * 0.5, steps)[1:]
    return points


def loco_bonnet(b, rng, detail):
    body = b.part("body", 40.0, 50)
    half = 0.72
    base = 1.3
    top = 2.72
    radius = 0.16
    y0 = -1.2
    y1 = 3.1
    side_outline = bonnet_outline(half, base, top, radius)
    door_width = 0.78
    for side in (-1.0, 1.0):
        frame = kit.plane(V(side * half, 0.0, 0.0), V(side, 0.0, 0.0))
        a_low, a_high = sorted((frame[1].y * y0, frame[1].y * y1))
        holes = []
        if side == open_door[0]:
            ya = -1.05 + open_door[1] * 0.8
            d0, d1 = sorted((frame[1].y * (ya + 0.02), frame[1].y * (ya + door_width - 0.02)))
            holes.append(kit.rect(d0, d1, 1.43, 2.47))
        shift = 0.13 if side > 0 else 0.57
        rk.zoned(body, slab_of(frame, kit.rect(a_low, a_high, base, top - radius), holes, -0.006, 0.0), "loco_green", base, None, False, shift)
        arc = rk.geo_sheet([(side * x, z) for x, z in side_outline[1:]], y0, y1, 6)
        rk.remap(arc, lambda s, y, shift=shift, side=side: (side * y / 2.0 + shift, (top - radius - base + s) / 2.0))
        emit(body, rk.away(arc, V(0.0, 1.0, 2.0)), "loco_green", None, "texture", True)
    crown = [(-half + radius, top), (-0.3, top + 0.012), (0.0, top + 0.016), (0.3, top + 0.012), (half - radius, top)]
    geo = rk.geo_sheet(crown, y0, y1, 6)
    rk.remap(geo, lambda s, y: (y / 2.0 + 0.31, 0.2 + s / 2.0))
    emit(body, rk.facing(geo, Z), "loco_green", None, "texture", True)
    closed = list(side_outline) + list(reversed(crown[1:-1])) + [(-x, z) for x, z in reversed(side_outline)]
    front = kit.geo_slab(V(0.0, y1, 0.0), X, Z, Y, closed, [kit.rect(-0.5, 0.5, 1.5, 2.5)], -0.02, 0.0)
    rk.zoned(body, front, "loco_green", base)
    core = kit.Geo([V(-0.62, y1 - 0.06, 1.38), V(0.62, y1 - 0.06, 1.38), V(0.62, y1 - 0.06, 2.62), V(-0.62, y1 - 0.06, 2.62)], [(0, 1, 2, 3)])
    emit(body, rk.facing(core, Y), "soot", None, "box", False)
    for index in range(25):
        x = -0.48 + index * 0.04
        block(detail, "loco_black", V(x - 0.006, y1 - 0.05, 1.5), V(x + 0.006, y1 - 0.02, 2.5))
    for z in (1.83, 2.17):
        block(detail, "loco_black", V(-0.5, y1 - 0.03, z - 0.012), V(0.5, y1 - 0.012, z + 0.012))
    for x0, x1, z0, z1 in ((-0.54, 0.54, 1.46, 1.5), (-0.54, 0.54, 2.5, 2.54), (-0.54, -0.5, 1.5, 2.5), (0.5, 0.54, 1.5, 2.5)):
        block(detail, "loco_black", V(x0, y1 - 0.01, z0), V(x1, y1 + 0.025, z1), 0.006)
    for x in (-0.63, 0.63):
        rk.rivets(detail, "loco_green", V(x, y1, 1.42), V(x, y1, 2.5), 0.12, Y, 0.009)
    round_lamp(detail, V(0.0, y1 + 0.085, 2.62), Y, 0.072)
    b.light("warm", V(0.0, y1 + 0.16, 2.62))
    for side in (-1.0, 1.0):
        normal = V(side, 0.0, 0.0)
        along = V(0.0, side, 0.0)
        for index in range(5):
            ya = -1.05 + index * 0.8
            yb = ya + door_width
            z0 = 1.4
            z1 = 2.5
            for hinge in (ya + 0.12, (ya + yb) * 0.5, yb - 0.12):
                rk.lathe(detail, "loco_black", V(side * (half + 0.012), hinge - 0.05, z1 + 0.012), Y, [(0.0, 0.0), (0.012, 0.0), (0.012, 0.1), (0.0, 0.1)], 8)
            if (side, index) == open_door:
                swing = Matrix.Translation(V(side * (half + 0.006), (ya + yb) * 0.5, z1 + 0.005)) @ Matrix.Rotation(-side * math.radians(72.0), 4, 'Y')
                leaf = rk.planar_uv(kit.geo_cbox(0.01, door_width, z1 - z0, 0.004), "loco_green", V(0.0, 0.0, -(z1 - z0) * 0.5), Y, Z, 1.0, (0.4, 0.0))
                emit(body, leaf, "loco_green", swing @ Matrix.Translation(V(0.0, 0.0, -(z1 - z0) * 0.5)), "texture", False)
                tip = swing @ V(0.0, door_width * 0.3, -(z1 - z0) + 0.06)
                rk.pipe(detail, "rust_iron", [tip, V(side * (half + 0.02), (ya + yb) * 0.5 + door_width * 0.3, 1.62)], 0.008, 6)
                continue
            matrix = Matrix.Translation(V(side * (half + 0.004), (ya + yb) * 0.5, (z0 + z1) * 0.5))
            rk.planar(body, kit.geo_cbox(0.01, door_width, z1 - z0, 0.004), "loco_green", V(0.0, 0.0, z0), Y, Z, matrix, False, 1.0, (rng.random(), 0.0))
            handle_y = (ya + yb) * 0.5 + rng.uniform(-0.02, 0.02)
            rk.lathe(detail, "rust_iron", V(side * (half + 0.009), handle_y, z0 + 0.22), normal, [(0.0, 0.0), (0.014, 0.0), (0.014, 0.03), (0.0, 0.03)], 6)
            block(detail, "rust_iron", V(side * (half + 0.035) - 0.006, handle_y - 0.05, z0 + 0.212), V(side * (half + 0.035) + 0.006, handle_y + 0.05, z0 + 0.228))
            if index in (0, 1, 3):
                origin = V(side * (half + 0.009), ya + 0.09 if side > 0 else yb - 0.09, 1.92)
                rk.louvres(detail, "loco_green", origin, along, Z, normal, door_width - 0.18, 9, 0.055)
            else:
                rk.rivets(detail, "loco_green", V(side * (half + 0.009), ya + 0.1, 2.2), V(side * (half + 0.009), yb - 0.1, 2.2), 0.145, normal, 0.008)
        rk.rivets(detail, "loco_green", V(side * half, y0 + 0.06, 1.35), V(side * half, y1 - 0.06, 1.35), 0.14, normal, 0.009)
        stands = [(V(side * (half + 0.075), y, 2.6), V(side * 0.075, 0.0, 0.0)) for y in (-0.95, 0.05, 1.05, 2.05, 2.95)]
        rk.handrail(detail, "loco_black", [V(side * (half + 0.075), -1.05, 2.6), V(side * (half + 0.075), 3.02, 2.6)], 0.014, stands)
        block(body, "loco_green", V(side * half - 0.006, y0, 2.54), V(side * half + 0.014, y1, 2.56))
        rk.atlas_panel(detail, "builder", V(side * (half + 0.016), 2.54, 1.74), normal, Z, 0.22, 0.09)
    for y in (-0.6, 1.0):
        local_block(body, "loco_green", Matrix.Translation(V(0.0, y, top + 0.012)), -0.32, 0.32, -0.3, 0.3, 0.0, 0.014, 0.004)
        for sx in (-1.0, 1.0):
            rk.pipe(detail, "rust_iron", [V(sx * 0.2, y - 0.06, top + 0.026), V(sx * 0.2, y - 0.06, top + 0.06), V(sx * 0.2, y + 0.06, top + 0.06), V(sx * 0.2, y + 0.06, top + 0.026)], 0.007, 5, 0.02)
    for sx in (-1.0, 1.0):
        for y in (-0.95, 2.6):
            rk.pipe(detail, "rust_iron", [V(sx * 0.42, y - 0.05, top + 0.005), V(sx * 0.42, y - 0.05, top + 0.07), V(sx * 0.42, y + 0.05, top + 0.07), V(sx * 0.42, y + 0.05, top + 0.005)], 0.011, 6, 0.03)
    stack = V(0.0, 2.2, top + 0.01)
    rk.lathe(detail, "loco_black", stack, Z, [(0.19, 0.0), (0.19, 0.02), (0.11, 0.025), (0.1, 0.06), (0.13, 0.5), (0.175, 0.66), (0.18, 0.69), (0.165, 0.69)], 18)
    rk.lathe(detail, "soot", stack, Z, [(0.165, 0.69), (0.12, 0.5), (0.09, 0.2), (0.0, 0.2)], 18)
    for angle in range(6):
        rk.prism_bolt(detail, "rust_iron", stack + V(math.cos(angle * tau / 6.0) * 0.155, math.sin(angle * tau / 6.0) * 0.155, 0.02), Z, 0.024, 0.012, 6)
    rk.lathe(detail, "loco_black", V(0.0, 0.25, top + 0.01), Z, [(0.11, 0.0), (0.11, 0.1), (0.2, 0.12), (0.2, 0.15), (0.1, 0.2), (0.0, 0.21)], 16)
    rk.lathe(detail, "rust_iron", V(0.0, 2.85, top + 0.012), Z, [(0.07, 0.0), (0.07, 0.035), (0.085, 0.035), (0.085, 0.06), (0.03, 0.07), (0.0, 0.07)], 12)
    b.col("metal", "bonnet", V(-half, y0, base), V(half, y1 + 0.02, top))
    return body


def cab_arc(x, half, eaves, rise):
    return eaves + rise * (1.0 - (x / half) ** 2)


def window_trim(part, matrix, a0, a1, z0, z1, name="loco_black", width=0.025):
    for fx0, fx1, fz0, fz1 in ((a0 - width, a1 + width, z0 - width, z0), (a0 - width, a1 + width, z1, z1 + width), (a0 - width, a0, z0, z1), (a1, a1 + width, z0, z1)):
        local_block(part, name, matrix, fx0, fx1, -0.01, 0.004, fz0, fz1)


def slab_of(frame, outline, holes, t0, t1, sides=True):
    return kit.geo_slab(frame[0], frame[1], frame[2], frame[3], outline, holes, t0, t1, sides)


def loco_cab(b, rng, body, detail):
    cab = b.part("cab", 40.0, 50)
    glass = b.part("glass", 30.0)
    half = 1.3
    y0 = -3.3
    y1 = -1.2
    floor = 1.3
    eaves = 3.25
    rise = 0.34
    skin = 0.02
    split = 2.2
    wasp_top = 2.14
    arc = [(half - 2.0 * half * s / 12.0, cab_arc(half - 2.0 * half * s / 12.0, half, eaves, rise)) for s in range(13)]
    door = (-3.15, -2.3, 3.2)
    side_window = (-2.15, -1.42, 2.27, 3.0)
    front_windows = [(0.79, 1.2, 2.27, 3.0, "shard"), (-1.2, -0.79, 2.27, 3.0, "whole"), (-0.48, 0.48, 2.84, 3.12, "shard")]
    rear_windows = [(0.16, 1.04, 2.27, 3.0, "whole"), (-1.04, -0.16, 2.27, 3.0, "shard")]
    for key, y, normal, windows in (("front", y1, Y, front_windows), ("rear", y0, -Y, rear_windows)):
        frame = kit.plane(V(0.0, y, 0.0), normal)
        flip = frame[1].x
        holes = [kit.rect(min(flip * w[0], flip * w[1]), max(flip * w[0], flip * w[1]), w[2], w[3]) for w in windows]
        bottom = floor if key == "front" else wasp_top
        outer = slab_of(frame, [(-half, bottom), (half, bottom)] + arc, holes, -skin, 0.0)
        rk.zoned(body, outer, "loco_green", floor, None, False, 0.21 if key == "front" else 0.63)
        if key == "rear":
            wasp_face(body, y, -1.0, half, floor, wasp_top)
        rk.zoned(cab, slab_of(frame, kit.rect(-half + skin, half - skin, floor, split), [], -2.0 * skin, -skin, False), "loco_green", floor, None, False, 0.4)
        upper = [(-half + skin, split), (half - skin, split)] + [(max(min(x, half - skin), -half + skin), z - 0.02) for x, z in arc]
        rk.planar(cab, slab_of(frame, upper, holes, -2.0 * skin, -skin, True), "coach_livery", V(0.0, 0.0, 0.74), X, Z, None, False, 0.685, (0.37, 0.0))
        matrix = kit.frame_matrix(frame)
        for w, hole in zip(windows, holes):
            a0 = hole[0][0]
            a1 = hole[1][0]
            kit.pane(glass, matrix, a0, a1, w[2], w[3], skin * 0.5, w[4], rng)
            window_trim(detail, matrix, a0, a1, w[2], w[3])
    for sign, state in ((-1.0, "missing"), (1.0, "shard")):
        x = sign * half
        normal = V(sign, 0.0, 0.0)
        frame = kit.plane(V(x, 0.0, 0.0), normal)
        along = frame[1]
        a_low, a_high = sorted((along.y * y0, along.y * y1))
        d0, d1 = sorted((along.y * door[0], along.y * door[1]))
        w0, w1 = sorted((along.y * side_window[0], along.y * side_window[1]))
        hole = kit.rect(w0, w1, side_window[2], side_window[3])
        outer = slab_of(frame, kit.notched(a_low, a_high, floor, eaves, [(d0, d1, door[2])]), [hole], -skin, 0.0)
        rk.zoned(body, outer, "loco_green", floor, None, False, 0.05 if sign > 0 else 0.47)
        for r0, r1 in ((a_low + skin, d0), (d1, a_high - skin)):
            if r1 - r0 > 0.02:
                rk.zoned(cab, slab_of(frame, kit.rect(r0, r1, floor, split), [], -2.0 * skin, -skin, False), "loco_green", floor, None, False, 0.71)
        high_outline = kit.notched(a_low + skin, a_high - skin, split, eaves - 0.02, [(d0, d1, door[2])])
        rk.planar(cab, slab_of(frame, high_outline, [hole], -2.0 * skin, -skin, True), "coach_livery", V(0.0, 0.0, 0.74), Y, Z, None, False, 0.685, (0.11, 0.0))
        matrix = kit.frame_matrix(frame)
        kit.pane(glass, matrix, w0, w1, side_window[2], side_window[3], skin * 0.5, state, rng)
        window_trim(detail, matrix, w0, w1, side_window[2], side_window[3])
        for a in (d0 - 0.06, d1 + 0.06):
            p = kit.frame_point(frame, a, 0.0, 0.055)
            stands = [(V(p.x, p.y, 1.59), normal * 0.055), (V(p.x, p.y, 2.71), normal * 0.055)]
            rk.handrail(detail, "loco_black", [V(p.x, p.y, 1.55), V(p.x, p.y, 2.75)], 0.013, stands)
        for a in (a_low + 0.035, a_high - 0.035):
            p = kit.frame_point(frame, a, 0.0, 0.003)
            rk.rivets(detail, "loco_green", V(p.x, p.y, floor + 0.08), V(p.x, p.y, eaves - 0.08), 0.13, normal, 0.009)
            rk.zoned(body, kit.geo_box(0.004, 0.07, eaves - floor), "loco_green", floor, Matrix.Translation(V(p.x - normal.x * 0.001, p.y, (floor + eaves) * 0.5)), False, 0.83)
        for a_from, a_to in ((a_low + 0.1, d0 - 0.05), (d1 + 0.05, a_high - 0.1)):
            if a_to - a_from > 0.08:
                for z in (2.19, 3.12):
                    rk.rivets(detail, "loco_green", kit.frame_point(frame, a_from, z, 0.0), kit.frame_point(frame, a_to, z, 0.0), 0.11, normal, 0.008)
        hinge_a = d0 if sign > 0 else d1
        for z in (1.62, 2.3, 2.98):
            p = kit.frame_point(frame, hinge_a, z, 0.012)
            rk.lathe(detail, "loco_black", V(p.x, p.y, z - 0.05), Z, [(0.0, 0.0), (0.013, 0.0), (0.013, 0.1), (0.0, 0.1)], 8)
        p0 = kit.frame_point(frame, d0 - 0.08, door[2] + 0.02, 0.0)
        p1 = kit.frame_point(frame, d1 + 0.08, door[2] + 0.02, 0.025)
        block(detail, "loco_black", V(min(p0.x, p1.x), min(p0.y, p1.y), door[2] + 0.02), V(max(p0.x, p1.x), max(p0.y, p1.y), door[2] + 0.035))
        rk.atlas_panel(detail, "number", kit.frame_point(frame, (w0 + w1) * 0.5, 2.02, 0.004), normal, Z, 0.5, 0.125)
        leaf = Matrix.Translation(V(sign * (half - 2.0 * skin - 0.004), door[0], 0.0)) @ Matrix.Rotation(math.radians(-6.0) * sign, 4, 'Z')
        reach = -sign * 0.82
        lx0, lx1 = sorted((0.0, reach))
        local_block(cab, "loco_green", leaf, lx0, lx1, 0.0, 0.03, floor + 0.04, 2.25, 0.004)
        for px0, px1, pz0, pz1 in ((lx0, lx0 + 0.07, 2.25, 3.14), (lx1 - 0.07, lx1, 2.25, 3.14), (lx0 + 0.07, lx1 - 0.07, 3.06, 3.14)):
            local_block(cab, "loco_green", leaf, px0, px1, 0.0, 0.03, pz0, pz1, 0.004)
        kit.pane(glass, leaf, lx0 + 0.07, lx1 - 0.07, 2.25, 3.06, 0.013, "shard" if sign > 0 else "whole", rng)
        local_block(detail, "rust_iron", leaf, reach * 0.9 - 0.06, reach * 0.9 + 0.06, 0.03, 0.055, 2.09, 2.11)
    roof_half = half + 0.06
    top_arc = [(roof_half - 2.0 * roof_half * s / 14.0, cab_arc(roof_half - 2.0 * roof_half * s / 14.0, roof_half, eaves - 0.01, rise + 0.035)) for s in range(15)]
    roof_outline = top_arc + [(x, z - 0.04) for x, z in reversed(top_arc)]
    emit(body, rk.geo_prism(roof_outline, y0 - 0.09, y1 + 0.09, 3), "loco_black", None, "given", True)
    inner = half - skin
    ceiling = rk.geo_sheet([(inner - 2.0 * inner * s / 10.0, cab_arc(inner - 2.0 * inner * s / 10.0, half, eaves, rise) - 0.022) for s in range(11)], y0 + skin, y1 - skin, 1)
    rk.planar(cab, rk.facing(ceiling, -Z), "coach_livery", V(-1.4, 0.0, 0.0), Y, X, None, True, 0.345, (0.0, 0.52))
    for side in (-1.0, 1.0):
        block(detail, "loco_black", V(side * roof_half - 0.015, y0 - 0.09, eaves - 0.06), V(side * roof_half + 0.015, y1 + 0.09, eaves - 0.02))
    rk.lathe(detail, "loco_black", V(0.0, -2.25, eaves + rise + 0.02), Z, [(0.16, 0.0), (0.16, 0.035), (0.22, 0.05), (0.22, 0.065), (0.0, 0.085)], 14)
    for sx in (-0.35, 0.35):
        rk.lathe(detail, "rust_iron", V(sx, y1 - 0.02, eaves + rise - 0.015), V(0.0, 1.0, 0.12), [(0.02, 0.0), (0.022, 0.12), (0.05, 0.26), (0.06, 0.28), (0.045, 0.27)], 10)
    round_lamp(detail, V(0.0, y0 - 0.075, 3.12), -Y, 0.07, "lens_red")
    b.light("warm", V(0.0, y0 - 0.16, 3.12))
    wall = 2.0 * skin
    kit.floor_boards(cab, "floorboards", -half + wall, half - wall, y0 + wall, y1 - wall, floor + 0.025, "y", rng, 0.025, 0.004, None, (0.14, 0.2), 0.0)
    for side in (-1.0, 1.0):
        block(cab, "chequer_plate", V(side * half, door[0], floor), V(side * (half - wall), door[1], floor + 0.026))
    b.col("metal", "cab_front", V(-half, y1 - wall, floor), V(half, y1, eaves))
    b.col("metal", "cab_rear", V(-half, y0, floor), V(half, y0 + wall, eaves))
    for side in (-1.0, 1.0):
        xa, xb = sorted((side * half, side * (half - wall)))
        b.col("metal", "cab_side", V(xa, door[1], floor), V(xb, y1, eaves))
        b.col("metal", "cab_side", V(xa, y0, floor), V(xb, door[0], eaves))
    b.col("metal", "cab_roof", V(-roof_half, y0 - 0.09, eaves), V(roof_half, y1 + 0.09, eaves + rise + 0.04))
    return cab, glass


def gauge(part, detail, center, normal, up, radius, index):
    rk.atlas_disc(part, "gauge_%d" % index, center + normal * 0.012, normal, up, radius, 16, "rail_signs", 0.95)
    rk.lathe(detail, "loco_black", center, normal, [(radius * 1.02, 0.0), (radius * 1.02, 0.012)], 16)


def lever(part, base, direction, length, knob="red", radius=0.009, ball=0.022):
    tip = base + direction.normalized() * length
    emit(part, kit.geo_tube([base, tip], kit.circle(radius, 6), True), "loco_black", None, "given", True)
    rk.swatch(part, kit.geo_lathe([(0.0, -ball), (ball * 0.8, -ball * 0.6), (ball, 0.0), (ball * 0.8, ball * 0.6), (0.0, ball)], 8), knob, rk.frame_along(tip, direction))


def loco_interior(b, rng, cab, detail):
    floor = 1.325
    front = -1.24
    rear = -3.26
    desk = [(front, floor), (-1.72, floor), (-1.72, 2.06), (-1.56, 2.36), (front, 2.36)]
    rk.zoned(cab, rk.prism_x(desk, -0.56, 0.56), "loco_green", floor, None, False, 0.27)
    panel_up = V(0.0, 0.16, 0.3).normalized()
    panel_normal = V(0.0, -0.3, 0.16).normalized()
    origin = V(0.0, -1.64, 2.21)
    for index in range(6):
        center = origin + X * ((index % 3 - 1) * 0.17) + panel_up * ((index // 3 - 0.5) * 0.15) + panel_normal * 0.004
        gauge(cab, detail, center, panel_normal, panel_up, 0.058, index)
    for index, name in enumerate(("fuel", "oil", "on_off", "horn")):
        rk.atlas_panel(detail, name, V(-0.42 + index * 0.28, -1.723, 1.95), -Y, Z, 0.12, 0.06)
    for region, x in (("lens_red", -0.48), ("lens_amber", -0.43), ("lens_green", 0.43), ("lens_red", 0.48)):
        rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.014, 0.0), (0.012, 0.01), (0.0, 0.014)], 8), region, rk.frame_along(origin + X * x + panel_up * 0.09 + panel_normal * 0.004, panel_normal))
    block(cab, "loco_black", V(-0.5, -1.56, 2.36), V(0.5, front, 2.375), 0.004)
    lever(detail, V(-0.3, -1.42, 2.375), V(0.0, -0.35, 1.0), 0.26, "red")
    lever(detail, V(-0.12, -1.42, 2.375), V(0.0, 0.25, 1.0), 0.2, "black")
    lever(detail, V(0.12, -1.45, 2.375), V(0.0, -0.1, 1.0), 0.17, "brass")
    for x in (-0.3, -0.12, 0.12):
        local_block(detail, "loco_black", Matrix.Translation(V(x, -1.43, 2.375)), -0.03, 0.03, -0.09, 0.09, 0.0, 0.012, 0.003)
    rk.lathe(detail, "loco_black", V(0.36, -1.45, 2.375), Z, [(0.0, 0.0), (0.06, 0.0), (0.06, 0.05), (0.045, 0.09), (0.0, 0.09)], 12)
    for angle, knob in ((0.5, "brass"), (2.4, "red")):
        lever(detail, V(0.36, -1.45, 2.445), V(math.cos(angle), math.sin(angle) * 0.6, 0.18), 0.19, knob, 0.008, 0.018)
    for index, x in enumerate((-0.2, -0.1, 0.0)):
        end = -0.56 - index * 0.07
        path = rk.fillet_path([V(x, front - 0.03, 2.375), V(x, front - 0.03, 2.6 + index * 0.045), V(end, front - 0.03, 2.6 + index * 0.045), V(end, front - 0.03, 3.1)], 0.04)
        rk.swatch(detail, kit.geo_tube(path, kit.circle(0.007, 6), True, Y), "copper", None, True)
    for position in (V(-0.78, -2.02, floor), V(0.78, -2.02, floor)):
        rk.lathe(detail, "loco_black", position, Z, [(0.0, 0.0), (0.13, 0.0), (0.12, 0.02), (0.035, 0.04), (0.035, 0.5), (0.1, 0.52), (0.1, 0.54), (0.0, 0.54)], 12)
        emit(cab, kit.geo_cbox(0.4, 0.38, 0.08, 0.03), "leather_brown", Matrix.Translation(position + V(0.0, 0.0, 0.58)), "box", True)
        emit(cab, kit.geo_cbox(0.36, 0.06, 0.26, 0.025), "leather_brown", Matrix.Translation(position + V(0.0, -0.2, 0.82)) @ Matrix.Rotation(-0.12, 4, 'X'), "box", True)
        rk.bar(detail, "loco_black", [position + V(0.0, -0.17, 0.54), position + V(0.0, -0.23, 0.7)], 0.012, 0.04, X)
        b.col("fabric", "seat", position + V(-0.2, -0.22, 0.0), position + V(0.2, 0.19, 0.62))
    column = V(1.02, -2.72, floor)
    emit(detail, kit.geo_tube([column, column + V(0.0, 0.0, 0.95)], kit.circle(0.03, 8), True), "loco_black", None, "given", True)
    wheel_center = column + V(0.0, 0.0, 0.98)
    ring = [wheel_center + V(math.cos(tau * s / 16.0) * 0.19, math.sin(tau * s / 16.0) * 0.19, 0.0) for s in range(17)]
    emit(detail, kit.geo_tube(ring, kit.circle(0.013, 6), False, Z), "rust_iron", None, "given", True)
    for s in range(4):
        angle = tau * s / 4.0 + 0.4
        emit(detail, kit.geo_tube([wheel_center, wheel_center + V(math.cos(angle) * 0.19, math.sin(angle) * 0.19, 0.0)], kit.circle(0.009, 5), False), "rust_iron", None, "given", True)
    rk.lathe(detail, "loco_black", wheel_center - V(0.0, 0.0, 0.04), Z, [(0.0, 0.0), (0.04, 0.0), (0.04, 0.06), (0.0, 0.07)], 8)
    b.col("metal", "handbrake", column - V(0.06, 0.06, 0.0), column + V(0.06, 0.06, 1.0))
    extinguisher = V(0.0, rear + 0.085, 2.0)
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.065, 0.0), (0.07, 0.02), (0.07, 0.36), (0.045, 0.42), (0.02, 0.44), (0.02, 0.47), (0.0, 0.47)], 12), "red", Matrix.Translation(extinguisher - V(0.0, 0.0, 0.25)))
    rk.atlas_panel(detail, "fire", extinguisher + V(0.0, 0.072, -0.08), Y, Z, 0.09, 0.12)
    rk.pipe(detail, "loco_black", [extinguisher + V(0.0, 0.0, 0.2), extinguisher + V(0.07, 0.03, 0.22), extinguisher + V(0.1, 0.04, 0.05), extinguisher + V(0.09, 0.04, -0.12)], 0.009, 6, 0.03)
    for z0, z1 in ((-0.12, -0.08), (0.06, 0.1)):
        block(detail, "loco_black", extinguisher + V(-0.08, -0.085, z0), extinguisher + V(0.08, -0.06, z1))
    locker = (V(-1.24, -1.66, floor), V(-0.64, front, floor + 0.9))
    block(cab, "loco_green", locker[0], locker[1], 0.006)
    local_block(cab, "loco_green", Matrix.Translation(V(-0.66, -1.672, floor + 0.04)) @ Matrix.Rotation(math.radians(-145.0), 4, 'Z'), 0.0, 0.56, 0.0, 0.012, 0.0, 0.82, 0.003)
    b.col("metal", "locker", locker[0], locker[1])
    panel = V(0.635, front - 0.001, 2.62)
    block(cab, "loco_black", panel + V(-0.1, -0.05, -0.2), panel + V(0.1, 0.0, 0.2), 0.006)
    for index, name in enumerate(("engine_stop", "brake", "vacuum", "sand")):
        rk.atlas_panel(detail, name, panel + V(0.0, -0.052, 0.135 - 0.09 * index), -Y, Z, 0.15, 0.075)
    rk.pipe(detail, "loco_black", [panel + V(0.0, -0.025, 0.2), panel + V(0.0, -0.025, 0.62)], 0.012, 6)
    lamp = V(0.0, -2.25, 3.25 + 0.34 - 0.06)
    rk.lathe(detail, "loco_black", lamp, -Z, [(0.0, -0.02), (0.085, -0.02), (0.085, 0.0), (0.07, 0.012)], 12)
    rk.swatch(detail, kit.geo_lathe([(0.07, 0.0), (0.06, 0.04), (0.03, 0.06), (0.0, 0.065)], 12), "lens_clear", rk.frame_along(lamp, -Z))
    b.light("warm", lamp - V(0.0, 0.0, 0.12))
    for y_a, y_b in ((front - 0.018, front), (rear, rear + 0.018)):
        block(cab, "floorboards", V(-1.25, y_a, 2.17), V(1.25, y_b, 2.23), 0.004, "board")
    rk.atlas_panel(detail, "timetable", V(0.0, rear + 0.006, 2.72), Y, Z, 0.22, 0.32)
    b.col("metal", "desk", V(-0.56, -1.72, floor), V(0.56, front, 2.36))


def loco_engine(b, rng):
    engine = b.part("engine", 40.0, 50)
    half = 0.72
    rk.inside_box(engine, "soot", V(-half + 0.006, -1.19, 1.3), V(half - 0.0065, 2.97, 2.71), ("bottom", "right") if open_door[0] > 0 else ("bottom", "left"))
    for sx in (-1.0, 1.0):
        block(engine, "loco_black", V(sx * 0.27 - 0.04, -0.7, 1.3), V(sx * 0.27 + 0.04, 2.0, 1.42))
    block(engine, "loco_black", V(-0.3, -0.55, 1.42), V(0.3, 1.95, 1.98), 0.025)
    heads = [-0.4 + index * 0.3 for index in range(8)]
    for y in heads:
        emit(engine, kit.geo_cbox(0.34, 0.24, 0.13, 0.04), "rust_iron", Matrix.Translation(V(0.0, y, 2.045)), "box", True)
        for sx in (-0.1, 0.1):
            rk.prism_bolt(engine, "rust_iron", V(sx, y, 2.11), Z, 0.022, 0.012, 6)
        rk.pipe(engine, "rust_iron", [V(0.16, y, 2.0), V(0.34, y, 2.0)], 0.03, 8)
    rk.pipe(engine, "rust_iron", [V(0.34, -0.5, 2.0), V(0.34, 2.0, 2.0), V(0.2, 2.2, 2.25), V(0.0, 2.2, 2.7)], 0.048, 10, 0.15)
    block(engine, "loco_black", V(0.32, 0.3, 1.55), V(0.5, 1.0, 1.8), 0.015)
    for index in range(8):
        start = V(0.41, 0.36 + index * 0.08, 1.8)
        path = rk.fillet_path([start, start + V(0.0, 0.0, 0.12 + index * 0.01), V(0.26, heads[index], 2.13 + index * 0.004), V(0.12, heads[index], 2.12)], 0.03, 3)
        rk.swatch(engine, kit.geo_tube(path, kit.circle(0.005, 5), False, Y), "copper", None, True)
    rk.lathe(engine, "loco_black", V(0.0, -0.55, 1.72), -Y, [(0.0, 0.0), (0.36, 0.0), (0.36, 0.22), (0.3, 0.26), (0.0, 0.26)], 20)
    rk.lathe(engine, "rust_iron", V(0.43, 1.35, 1.64), Y, [(0.0, 0.0), (0.085, 0.0), (0.09, 0.02), (0.09, 0.28), (0.06, 0.3), (0.0, 0.3)], 12)
    rk.lathe(engine, "loco_black", V(0.0, 2.55, 2.0), Y, [(0.0, 0.0), (0.09, 0.0), (0.09, 0.08), (0.0, 0.08)], 10)
    for blade in range(6):
        angle = tau * blade / 6.0
        out = V(math.cos(angle), 0.0, math.sin(angle))
        side = V(-out.z, 0.0, out.x)
        points = [V(0.0, 2.57, 2.0) + out * 0.08 - side * 0.04, V(0.0, 2.63, 2.0) + out * 0.08 + side * 0.04, V(0.0, 2.65, 2.0) + out * 0.42 + side * 0.09, V(0.0, 2.57, 2.0) + out * 0.42 - side * 0.09]
        emit(engine, kit.Geo(points, [(0, 1, 2, 3), (3, 2, 1, 0)]), "loco_black", None, "box", False)
    rk.lathe(engine, "rust_iron", V(-0.31, 0.6, 1.9), V(-1.0, 0.0, 0.6), [(0.0, 0.0), (0.035, 0.0), (0.035, 0.08), (0.05, 0.08), (0.05, 0.1), (0.0, 0.105)], 10)
    return engine


def loco_extras(b, rng, body, detail, cab):
    half = 1.3
    y0 = -3.3
    y1 = -1.2
    floor = 1.3
    eaves = 3.25
    for side in (-1.0, 1.0):
        rk.pipe(detail, "loco_black", [V(side * 1.215, -3.42, 1.1), V(side * 1.215, 3.42, 1.1)], 0.018, 8)
        for index in range(9):
            y = -3.2 + index * 0.8
            block(detail, "loco_black", V(side * 1.215 - 0.012, y - 0.015, 1.1), V(side * 1.215 + 0.012, y + 0.015, 1.26))
            emit(detail, kit.geo_lathe([(0.021, -0.02), (0.026, -0.02), (0.026, 0.02), (0.021, 0.02)], 8), "rust_iron", Matrix.Translation(V(side * 1.215, y, 1.1)) @ Matrix.Rotation(-math.pi * 0.5, 4, 'X'), "given", True)
        rk.rivets(detail, "loco_black", V(side * 0.62, -3.3, 1.06), V(side * 0.62, 3.3, 1.06), 0.22, V(side, 0.0, 0.0), 0.013)
        post = V(side * 1.24, 3.42, floor)
        rk.pipe(detail, "loco_black", [post, post + V(0.0, 0.0, 0.95)], 0.017, 8)
        rk.lathe(detail, "loco_black", post + V(0.0, 0.0, 0.95), Z, [(0.0, -0.02), (0.024, -0.012), (0.03, 0.01), (0.022, 0.03), (0.0, 0.036)], 10)
        rk.lathe(detail, "loco_black", post, Z, [(0.04, 0.0), (0.04, 0.01), (0.02, 0.03)], 10)
        for x_c in (half - 0.035,):
            for y, normal_y in ((y1, 1.0), (y0, -1.0)):
                rk.zoned(body, kit.geo_box(0.07, 0.004, eaves - floor), "loco_green", floor, Matrix.Translation(V(side * x_c, y + normal_y * 0.002, (floor + eaves) * 0.5)), False, 0.29)
                rk.rivets(detail, "loco_green", V(side * x_c, y + normal_y * 0.004, floor + 0.08), V(side * x_c, y + normal_y * 0.004, eaves - 0.08), 0.13, V(0.0, normal_y, 0.0), 0.009)
        rk.rivets(detail, "loco_green", V(side * 0.78, y1, 2.19), V(side * 1.2, y1, 2.19), 0.105, Y, 0.008)
        rk.rivets(detail, "loco_green", V(side * 0.78, y1, 3.1), V(side * 1.2, y1, 3.1), 0.105, Y, 0.008)
        pivot = V(side * 0.995, y1 + 0.012, 3.04)
        tip = pivot + V(-side * 0.13, 0.004, -0.3)
        rk.lathe(detail, "loco_black", pivot, Y, [(0.0, 0.0), (0.018, 0.0), (0.018, 0.02), (0.0, 0.024)], 8)
        rk.bar(detail, "loco_black", [pivot + V(0.0, 0.012, 0.0), tip + V(0.0, 0.012, 0.0)], 0.01, 0.004, Y)
        rk.bar(detail, "loco_black", [tip + V(side * 0.06, 0.01, 0.13), tip + V(-side * 0.06, 0.01, -0.13)], 0.012, 0.008, Y)
        for index in range(1, 5):
            y = -1.05 + index * 0.8 - 0.01
            rk.zoned(body, kit.geo_box(0.004, 0.03, 1.16), "loco_green", 1.3, Matrix.Translation(V(side * 0.722, y, 1.94)), False, 0.9)
            rk.rivets(detail, "loco_green", V(side * 0.724, y, 1.44), V(side * 0.724, y, 2.48), 0.13, V(side, 0.0, 0.0), 0.007)
        rk.rivets(detail, "loco_green", V(side * 0.56, -1.1, 2.722), V(side * 0.56, 3.0, 2.722), 0.2, Z, 0.008)
    rk.rivets(detail, "loco_green", V(-1.2, y0, 2.19), V(1.2, y0, 2.19), 0.12, -Y, 0.008)
    rk.rivets(detail, "loco_green", V(-1.2, y0, 3.1), V(1.2, y0, 3.1), 0.12, -Y, 0.008)
    stands = [(V(x, y0 - 0.06, 2.21), V(0.0, -0.06, 0.0)) for x in (-0.95, 0.0, 0.95)]
    rk.handrail(detail, "loco_black", [V(-1.05, y0 - 0.06, 2.21), V(1.05, y0 - 0.06, 2.21)], 0.014, stands)
    roof_half = half + 0.06
    top_arc = [(roof_half - 2.0 * roof_half * s / 14.0, cab_arc(roof_half - 2.0 * roof_half * s / 14.0, roof_half, eaves - 0.01, 0.375) + 0.006) for s in range(15)]
    for y in (-2.95, -2.25, -1.55):
        emit(body, rk.facing(rk.geo_sheet(top_arc, y - 0.03, y + 0.03, 1), Z), "loco_black", None, "given", True)
        for x, z in top_arc[1:-1:2]:
            rk.rivet(detail, "loco_black", V(x, y, z), Z, 0.009)
    rk.lathe(detail, "loco_black", V(0.0, -3.25, 0.36), Z, [(0.0, 0.0), (0.2, 0.0), (0.22, 0.03), (0.22, 0.4), (0.2, 0.43), (0.0, 0.43)], 18)
    rk.pipe(detail, "rust_iron", [V(0.0, -3.25, 0.36), V(0.0, -3.25, 0.22)], 0.025, 8)
    emit(detail, kit.geo_tube([V(-1.12, -1.1, 1.322), V(-1.03, 2.3, 1.322)], kit.circle(0.02, 8), True), "timber_beam", None, "given", True)
    rk.pipe(detail, "rust_iron", [V(-1.03, 2.3, 1.322), V(-1.027, 2.42, 1.322), V(-1.0, 2.47, 1.322), V(-0.97, 2.43, 1.322)], 0.009, 6, 0.02)
    bucket = V(-0.95, 3.27, floor)
    rk.lathe(detail, "rust_iron", bucket, Z, [(0.0, 0.0), (0.1, 0.0), (0.125, 0.26), (0.118, 0.26), (0.094, 0.008), (0.0, 0.008)], 14)
    rk.pipe(detail, "rust_iron", [bucket + V(-0.123, 0.0, 0.25), bucket + V(-0.1, 0.09, 0.255), bucket + V(0.0, 0.135, 0.262), bucket + V(0.1, 0.09, 0.255), bucket + V(0.123, 0.0, 0.25)], 0.004, 5, 0.03)
    front = -1.24
    cabin = 1.325
    for x in (-1.0, 1.0):
        block(detail, "loco_black", V(x - 0.06, front - 0.07, 3.04), V(x + 0.06, front, 3.11), 0.006)
    block(cab, "floorboards", V(-0.45, front - 0.13, 2.76), V(0.45, front, 2.785), 0.004, "board")
    for x in (-0.38, 0.38):
        rk.bar(detail, "rust_iron", [V(x, front - 0.12, 2.76), V(x, front - 0.005, 2.66)], 0.004, 0.02, X)
    rk.lathe(detail, "rust_iron", V(-0.27, front - 0.065, 2.785), Z, [(0.0, 0.0), (0.048, 0.0), (0.05, 0.11), (0.03, 0.125), (0.03, 0.135), (0.0, 0.135)], 12)
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.036, 0.0), (0.04, 0.08), (0.036, 0.08), (0.033, 0.008), (0.0, 0.008)], 10), "white", Matrix.Translation(V(0.08, front - 0.06, 2.785)))
    rk.lathe(detail, "rust_iron", V(0.3, front - 0.065, 2.785), Z, [(0.0, 0.0), (0.045, 0.0), (0.045, 0.06), (0.012, 0.1), (0.0, 0.1)], 10)
    rk.pipe(detail, "rust_iron", [V(0.3, front - 0.065, 2.87), V(0.36, front - 0.065, 2.93), V(0.42, front - 0.065, 2.95)], 0.005, 5)
    heater = (V(0.62, -1.52, cabin), V(1.2, front, cabin + 0.42))
    block(cab, "loco_black", heater[0], heater[1], 0.01)
    for index in range(9):
        x = 0.67 + index * 0.06
        block(detail, "rust_iron", V(x - 0.006, -1.545, cabin + 0.05), V(x + 0.006, -1.52, cabin + 0.38))
    b.col("metal", "heater", heater[0], heater[1])
    block(cab, "loco_black", V(-1.258, -2.2, 1.78), V(-1.2, -1.86, 2.12), 0.006)
    rk.pipe(detail, "loco_black", [V(-1.23, -2.03, 1.78), V(-1.23, -2.03, cabin + 0.03), V(-1.23, -1.68, cabin + 0.03)], 0.011, 6, 0.03)
    rk.swatch(detail, kit.geo_cbox(0.14, 0.2, 0.025, 0.004), "cream", Matrix.Translation(V(-0.43, -1.4, 2.3885)) @ Matrix.Rotation(0.2, 4, 'Z'), False)
    rk.atlas_panel(detail, "timetable", V(-0.43, -1.4, 2.402), Z, V(math.sin(0.2) * -1.0, math.cos(0.2), 0.0), 0.12, 0.18)
    top = V(0.72, -1.95, cab_arc(0.72, half, eaves, 0.34) - 0.03)
    rk.chain(detail, "rust_iron", [top, top - V(0.0, 0.0, 0.42)], 0.03, 0.014, 0.0032, None, 4, 2)
    emit(detail, kit.geo_tube([top - V(0.05, 0.0, 0.44), top - V(-0.05, 0.0, 0.44)], kit.circle(0.012, 6), True), "timber_beam", None, "given", True)
    emit(detail, kit.geo_box(0.12, 0.26, 0.012), "chequer_plate", Matrix.Translation(V(-0.78, -1.78, cabin + 0.04)) @ Matrix.Rotation(-0.3, 4, 'X'), "box")
    rk.pipe(detail, "loco_black", [V(0.09, -2.25, 3.545), V(0.09, -1.3, 3.545), V(0.635, -1.27, 3.45), V(0.635, -1.27, 2.83)], 0.011, 6, 0.04)
    rk.atlas_panel(detail, "notice", V(1.2585, -1.78, 1.86), -X, Z, 0.2, 0.25)


def locomotive():
    b = rk.Build("train_locomotive", 31)
    rng = b.rng
    frame, detail = loco_frames(b, rng)
    body = loco_bonnet(b, rng, detail)
    cab, glass = loco_cab(b, rng, body, detail)
    loco_interior(b, rng, cab, detail)
    loco_engine(b, rng)
    loco_extras(b, rng, body, detail, cab)
    return b


def far_wheelset(b, key, y, radius, body="loco_black"):
    part = b.part(key, 40.0)
    b.origin(key, V(0.0, y, radius))
    for side in (-1.0, 1.0):
        matrix = Matrix.Translation(V(side * 0.68, y, radius)) @ Matrix.Rotation(side * math.pi * 0.5, 4, 'Y')
        emit(part, kit.geo_lathe([(0.0, 0.0), (radius + 0.028, 0.0), (radius + 0.028, 0.03), (radius, 0.04), (radius - 0.01, 0.135), (0.0, 0.135)], 12), body, matrix, "given", True)
    emit(part, kit.geo_lathe([(0.075, -0.66), (0.075, 0.66)], 6), body, Matrix.Translation(V(0.0, y, radius)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)


def far_buffers(part, y, direction, body="loco_black"):
    for side in (-1.0, 1.0):
        rk.lathe(part, body, V(side * buffer_spread, y, buffer_height), V(0.0, direction, 0.0), [(0.11, 0.0), (0.085, 0.3), (0.06, 0.44), (0.19, 0.47), (0.19, 0.5), (0.0, 0.5)], 8)
    block(part, "rust_iron", V(-0.03, min(y, y + direction * 0.3), hook_height - 0.06), V(0.03, max(y, y + direction * 0.3), hook_height + 0.08))


def locomotive_far():
    b = rk.Build("train_locomotive_far", 32)
    part = b.part("body", 40.0)
    rk.slab(part, V(-1.3, -3.5, 1.16), V(1.3, 3.5, 1.30), "chequer_plate", "loco_black")
    for side in (-1.0, 1.0):
        block(part, "loco_black", V(side * 0.58, -3.46, 0.42), V(side * 0.62, 3.46, 1.16), 0.0, "box", None, ("top",))
        for y0, y1 in ((-3.15, -2.3), (2.9, 3.44)):
            for top, out in ((0.1, 1.7), (0.5, 1.57), (0.9, 1.44)):
                xa, xb = sorted((side * 1.3, side * out))
                block(part, "loco_black", V(xa, y0, top - 0.05), V(xb, y1, top), 0.0, "box", None, ("bottom",))
        block(part, "loco_black", V(min(side * 0.92, side * 1.22), 2.12, 0.78), V(max(side * 0.92, side * 1.22), 2.5, 1.16), 0.0, "box", None, ("top",))
        block(part, "loco_black", V(min(side * 0.92, side * 1.22), -2.25, 0.78), V(max(side * 0.92, side * 1.22), -1.9, 1.16), 0.0, "box", None, ("top",))
    block(part, "loco_black", V(-0.45, -3.1, 0.5), V(0.45, 3.1, 1.16), 0.0, "box", None, ("top",))
    block(part, "loco_black", V(-1.22, -3.2, 0.62), V(-0.7, -2.4, 1.16), 0.0, "box", None, ("top",))
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.85), (0.0, 0.85)], 8), "loco_black", Matrix.Translation(V(0.95, -3.2, 0.85)) @ Matrix.Rotation(-math.pi * 0.5, 4, 'X'), "given", True)
    for direction in (-1.0, 1.0):
        wasp_face(part, direction * 3.5, direction, 1.28, 0.7, 1.3)
        far_buffers(part, direction * 3.5, direction)
    half = 0.72
    outline = [(half, 1.3), (half, 2.58), (half - 0.14, 2.72), (-half + 0.14, 2.72), (-half, 2.58), (-half, 1.3)]
    shell = rk.geo_sheet(outline, -1.2, 3.1, 1)
    rk.zoned(part, rk.away(shell, V(0.0, 1.0, 1.8)), "loco_green", 1.3, None, True)
    front = kit.geo_slab(V(0.0, 3.1, 0.0), X, Z, Y, outline, [], -0.01, 0.0, False)
    rk.zoned(part, front, "loco_green", 1.3)
    grille = kit.Geo([V(-0.5, 3.102, 1.5), V(0.5, 3.102, 1.5), V(0.5, 3.102, 2.5), V(-0.5, 3.102, 2.5)], [(0, 1, 2, 3)])
    emit(part, rk.facing(grille, Y), "soot", None, "box", False)
    rk.lathe(part, "loco_black", V(0.0, 2.2, 2.72), Z, [(0.11, 0.0), (0.13, 0.5), (0.18, 0.69), (0.0, 0.69)], 8)
    y0 = -3.3
    y1 = -1.2
    eaves = 3.25
    arc = [(1.3 - 2.6 * s / 4.0, cab_arc(1.3 - 2.6 * s / 4.0, 1.3, eaves, 0.34)) for s in range(5)]
    for y, normal, windows in ((y1, Y, [(0.79, 1.2, 2.27, 3.0), (-1.2, -0.79, 2.27, 3.0)]), (y0, -Y, [(0.16, 1.04, 2.27, 3.0), (-1.04, -0.16, 2.27, 3.0)])):
        frame = kit.plane(V(0.0, y, 0.0), normal)
        bottom = 1.3 if normal.y > 0 else 2.14
        rk.zoned(part, slab_of(frame, [(-1.3, bottom), (1.3, bottom)] + arc, [], -0.01, 0.0, False), "loco_green", 1.3, None, False, 0.3)
        if normal.y < 0:
            wasp_face(part, y, -1.0, 1.3, 1.3, 2.14)
        for w in windows:
            pane = kit.Geo([V(w[0], y + normal.y * 0.004, w[2]), V(w[1], y + normal.y * 0.004, w[2]), V(w[1], y + normal.y * 0.004, w[3]), V(w[0], y + normal.y * 0.004, w[3])], [(0, 1, 2, 3)])
            emit(part, rk.facing(pane, normal), "glass_dirty", None, "box", False)
    for sign in (-1.0, 1.0):
        frame = kit.plane(V(sign * 1.3, 0.0, 0.0), V(sign, 0.0, 0.0))
        along = frame[1]
        a_low, a_high = sorted((along.y * y0, along.y * y1))
        rk.zoned(part, slab_of(frame, kit.rect(a_low, a_high, 1.3, eaves), [], -0.01, 0.0, False), "loco_green", 1.3, None, False, 0.6)
        for ya, yb, za, zb in ((-3.15, -2.3, 1.3, 3.2), (-2.15, -1.42, 2.27, 3.0)):
            x = sign * 1.304
            pane = kit.Geo([V(x, ya, za), V(x, yb, za), V(x, yb, zb), V(x, ya, zb)], [(0, 1, 2, 3)])
            emit(part, rk.facing(pane, V(sign, 0.0, 0.0)), "soot" if za < 2.0 else "glass_dirty", None, "box", False)
    top_arc = [(1.36 - 2.72 * s / 4.0, cab_arc(1.36 - 2.72 * s / 4.0, 1.36, eaves, 0.37)) for s in range(5)]
    emit(part, rk.geo_prism(top_arc + [(-1.36, eaves - 0.04), (1.36, eaves - 0.04)], y0 - 0.09, y1 + 0.09, 1), "loco_black", None, "given", True)
    for number, axle in enumerate(loco_axles):
        far_wheelset(b, "wheel_%d" % (number + 1), axle, loco_radius)
    return b


wagon_half = 2.75
wagon_axles = (1.525, -1.525)
wagon_radius = 0.476
underframe_top = 1.2
deck_top = 1.27


def w_iron(part, detail, rng, side, axle):
    outline = [(-0.4, 0.95), (0.4, 0.95), (0.4, 0.88), (0.16, 0.33), (-0.16, 0.33), (-0.4, 0.88)]
    holes = [[(-0.085, 0.37), (0.085, 0.37), (0.085, 0.84), (-0.085, 0.84)], [(-0.33, 0.85), (-0.14, 0.85), (-0.14, 0.45)], [(0.33, 0.85), (0.14, 0.45), (0.14, 0.85)]]
    emit(part, kit.geo_slab(V(side * 0.948, axle, 0.0), Y, Z, V(side, 0.0, 0.0), outline, holes, 0.0, 0.014), "loco_black", None, "box")
    for offset in (-0.32, -0.2, 0.2, 0.32):
        rk.prism_bolt(detail, "rust_iron", V(side * 0.962, axle + offset, 0.915), V(side, 0.0, 0.0), 0.026, 0.013, 6)
    emit(part, kit.geo_cbox(0.17, 0.17, 0.2, 0.02), "loco_black", Matrix.Translation(V(side * 1.015, axle, wagon_radius)), "box")
    emit(part, kit.geo_cbox(0.014, 0.13, 0.15, 0.004), "rust_iron", Matrix.Translation(V(side * 1.106, axle, wagon_radius)), "box")
    for offset in (-0.045, 0.045):
        rk.prism_bolt(detail, "rust_iron", V(side * 1.113, axle + offset, wagon_radius + 0.05), V(side, 0.0, 0.0), 0.022, 0.011, 6)
    leaves = 6
    ends = rk.leaf_spring(part, "rust_iron", V(side * 1.0, axle, wagon_radius + 0.1 + leaves * 0.011 + 0.004), 0.95, leaves, 0.085, 0.011, 0.085, Y)
    for end in ends:
        block(part, "loco_black", V(side * 1.0 - 0.05, end.y - 0.03, end.z - 0.02), V(side * 1.0 + 0.05, end.y + 0.03, 0.95), 0.006)


def wagon_brakes(part, detail, rng, side, full=True):
    x = side * 0.975
    for direction in (-1.0, 1.0):
        rk.bar(part, "loco_black", [V(x, direction * 0.22, 0.95), V(x, 0.0, 0.47)], 0.05, 0.012, X)
    rk.lathe(detail, "rust_iron", V(x - side * 0.01, 0.0, 0.48), V(side, 0.0, 0.0), [(0.0, 0.0), (0.05, 0.0), (0.05, 0.03), (0.0, 0.03)], 10)
    lever_x = side * 1.06
    rk.bar(part, "loco_black", [V(lever_x, 0.0, 0.48), V(lever_x, 1.2, 0.6), V(lever_x, 2.2, 0.88), V(lever_x, 2.62, 0.9)], 0.05, 0.014, X, 0.12)
    rk.lathe(detail, "rust_iron", V(lever_x, 2.62, 0.9), Y, [(0.0, 0.0), (0.018, 0.0), (0.022, 0.06), (0.018, 0.12), (0.0, 0.125)], 8)
    guard_x = side * 1.095
    rk.bar(part, "loco_black", [V(guard_x, 2.12, 0.96), V(guard_x, 2.12, 0.56), V(guard_x, 2.2, 0.56), V(guard_x, 2.2, 0.96)], 0.03, 0.008, X, 0.02)
    for index in range(7):
        rk.prism_bolt(detail, "rust_iron", V(guard_x + side * 0.004, 2.12, 0.6 + index * 0.05), V(side, 0.0, 0.0), 0.014, 0.008, 4)
    if full:
        rk.pipe(part, "rust_iron", [V(side * 0.25, 0.0, 0.48), V(side * 1.07, 0.0, 0.48)], 0.025, 8)
        for axle in wagon_axles:
            toward = 1.0 if axle > 0.0 else -1.0
            y = axle - toward * 0.51
            brake_block(detail, side * 0.755, y, wagon_radius, toward)
            rk.bar(detail, "rust_iron", [V(side * 0.755, toward * 0.06, 0.48), V(side * 0.755, y, wagon_radius + 0.02)], 0.035, 0.012, X)
        rk.bar(detail, "rust_iron", [V(side * 0.755, -0.07, 0.48), V(side * 0.755, 0.07, 0.48)], 0.06, 0.02, X)


def wagon_underframe(b, rng, fitted=False, brake_side=1.0, plate="wagon_a"):
    frame = b.part("frame", 40.0, 50)
    detail = b.part("detail", 40.0)
    for side in (-1.0, 1.0):
        outline = [(side * 0.935, 0.95), (side * 1.03, 0.95), (side * 1.03, 0.965), (side * 0.95, 0.965), (side * 0.95, 1.185), (side * 1.03, 1.185), (side * 1.03, 1.2), (side * 0.935, 1.2)]
        emit(frame, rk.geo_prism(outline, -wagon_half + 0.09, wagon_half - 0.09, 1), "loco_black", None, "given", False)
        rk.rivets(detail, "loco_black", V(side * 0.95, -2.5, 1.13), V(side * 0.95, 2.5, 1.13), 0.25, V(side, 0.0, 0.0), 0.011)
        for axle in wagon_axles:
            w_iron(frame, detail, rng, side, axle)
        block(frame, "loco_black", V(side * 0.3 - 0.04, -2.66, 0.98), V(side * 0.3 + 0.04, 2.66, 1.2))
        rk.atlas_panel(detail, plate, V(side * 0.952, -0.62 * side, 1.06), V(side, 0.0, 0.0), Z, 0.26, 0.105)
        block(detail, "rust_iron", V(side * 0.95, 0.38 * side - 0.06, 1.0), V(side * 0.957, 0.38 * side + 0.06, 1.1))
    for y in (-2.0, -1.0, 0.0, 1.0, 2.0):
        block(frame, "loco_black", V(-0.935, y - 0.04, 1.0), V(0.935, y + 0.04, 1.2))
    for direction in (-1.0, 1.0):
        y = direction * wagon_half
        block(frame, "loco_black", V(-1.22, min(y, y - direction * 0.09), 0.9), V(1.22, max(y, y - direction * 0.09), 1.2))
        for x in (-1.12, -0.6, 0.6, 1.12):
            rk.rivets(detail, "rust_iron", V(x, y, 0.95), V(x, y, 1.15), 0.1, V(0.0, direction, 0.0), 0.012)
        end_gear(b, detail, y, direction, rng, "loco_black", 1.0, 0.3, 3, fitted)
        for x in (-1.05, 1.05):
            lamp_iron(detail, V(x, y, 1.2), V(0.0, direction, 0.0))
    for number, axle in enumerate(wagon_axles):
        rk.wheelset(b, "wheel_%d" % (number + 1), axle, wagon_radius, 8, "loco_black", False, False, 0.68, 0.06, 0.1, 0.04, 48, 0.96)
    wagon_brakes(frame, detail, rng, brake_side, True)
    wagon_brakes(frame, detail, rng, -brake_side, False)
    return frame, detail


def wagon_flat():
    b = rk.Build("train_wagon_flat", 41)
    rng = b.rng
    frame, detail = wagon_underframe(b, rng)
    deck = b.part("deck", 40.0, 50)
    load = b.part("load", 40.0)
    kit.floor_boards(deck, "timber_planks_weathered", -1.25, 1.25, -2.72, 2.72, deck_top, "x", rng, 0.07, 0.006, None, (0.17, 0.23), 0.03)
    for side in (-1.0, 1.0):
        block(frame, "loco_black", V(side * 1.2, -wagon_half, underframe_top), V(side * 1.26, wagon_half, 1.36), 0.006)
        block(frame, "loco_black", V(-1.26, side * 2.69, underframe_top), V(1.26, side * wagon_half, 1.36), 0.006)
        for index, y in enumerate((-2.1, -0.75, 0.75, 2.1)):
            block(detail, "loco_black", V(side * 1.26, y - 0.07, 1.0), V(side * 1.34, y + 0.07, 1.2), 0.006)
            if side > 0 and index == 1:
                continue
            lean = rng.uniform(-0.02, 0.05)
            rk.bar(detail, "rust_iron", [V(side * 1.3, y, 1.0), V(side * (1.3 + lean), y + rng.uniform(-0.02, 0.02), 2.15)], 0.07, 0.05, Y)
            rk.rivets(detail, "rust_iron", V(side * 1.342, y, 1.05), V(side * 1.342, y, 1.15), 0.1, V(side, 0.0, 0.0), 0.011)
    base = deck_top + 0.13
    for y in (-1.5, 1.5):
        block(deck, "timber_beam", V(0.05, y - 0.1, deck_top), V(1.15, y + 0.1, base), 0.01)
    upper = base + rk.rail_height + 0.025
    for y in (-1.5, 0.0, 1.5):
        block(load, "timber_beam", V(0.1, y - 0.04, base + rk.rail_height), V(1.0, y + 0.04, upper), 0.004)
    for layer, count, start, level in ((0, 5, 0.2, base), (1, 4, 0.28, upper)):
        for index in range(count):
            shift = rng.uniform(-0.12, 0.12)
            geo = rk.rail_geo(-2.42 + shift, 2.42 + shift, 2, rng.random() < 0.5, "dull")
            matrix = Matrix.Translation(V(start + index * 0.165 + rng.uniform(-0.008, 0.008), 0.0, level)) @ Matrix.Rotation(rng.uniform(-0.004, 0.004), 4, 'Z')
            emit(load, geo, "rail_steel", matrix, "texture", True)
    rail_top_level = upper + rk.rail_height
    quarter = Matrix.Rotation(math.pi * 0.5, 4, 'Z')
    stack_top = deck_top
    for layer in range(2):
        stack_top += 0.13
        for across in range(3):
            for along in (-1.0, 1.0):
                if layer == 1 and (across, along) in ((0, 1.0), (2, -1.0)):
                    continue
                geo = rk.sleeper_geo(rng, rng.randrange(rk.strip_count), (rng.randrange(8), rng.randrange(8)), 2.6, 0.25, 0.13, rng.uniform(0.8, 1.6), (rng.uniform(0.15, 0.4) if rng.random() < 0.4 else 0.0, 0.0), rng.random() < 0.5)
                position = V(-0.92 + across * 0.262 + rng.uniform(-0.01, 0.01), along * 1.33 + rng.uniform(-0.05, 0.05), stack_top + rng.uniform(0.0, 0.004))
                emit(load, geo, "sleeper_timber", Matrix.Translation(position) @ Matrix.Rotation(rng.uniform(-0.03, 0.03) * (2.0 if layer else 1.0), 4, 'Z') @ quarter, "texture", True)
    for y in (-1.95, 0.2, 1.98):
        path = [V(-1.29, y, 1.13), V(-1.1, y, stack_top + 0.012), V(-0.2, y, stack_top + 0.014), V(0.14, y, rail_top_level + 0.012), V(0.98, y, rail_top_level + 0.012), V(1.29, y, 1.13)]
        rk.chain(load, "rust_iron", path, 0.075, 0.036, 0.0075, rng, 5, 2)
        for side in (-1.0, 1.0):
            rk.lathe(detail, "rust_iron", V(side * 1.27, y, 1.13), V(side, 0.0, 0.0), [(0.0, 0.0), (0.03, 0.0), (0.03, 0.012), (0.012, 0.02), (0.012, 0.04), (0.0, 0.04)], 8)
    rk.bar(load, "rust_iron", [V(-0.95, -0.7, stack_top + 0.028), V(-0.32, 0.42, stack_top + 0.028)], 0.07, 0.05, Z)
    b.col("wood", "deck", V(-1.25, -wagon_half, 0.45), V(1.25, wagon_half, deck_top))
    b.col("wood", "sleepers", V(-1.06, -2.65, deck_top), V(-0.2, 2.65, stack_top))
    b.col("metal", "rails", V(0.08, -2.5, deck_top), V(1.02, 2.5, rail_top_level))
    return b


def wagon_far_base(b, part, radius=wagon_radius, axles=wagon_axles, half=wagon_half):
    for side in (-1.0, 1.0):
        block(part, "loco_black", V(min(side * 0.935, side * 1.03), -half + 0.09, 0.95), V(max(side * 0.935, side * 1.03), half - 0.09, underframe_top), 0.0, "box", None, ("top",))
        for axle in axles:
            block(part, "loco_black", V(min(side * 0.93, side * 1.1), axle - 0.085, radius - 0.1), V(max(side * 0.93, side * 1.1), axle + 0.085, radius + 0.1))
            block(part, "rust_iron", V(min(side * 0.96, side * 1.04), axle - 0.47, radius + 0.12), V(max(side * 0.96, side * 1.04), axle + 0.47, radius + 0.19), 0.0, "box", None, ("bottom",))
    for direction in (-1.0, 1.0):
        y = direction * half
        block(part, "loco_black", V(-1.22, min(y, y - direction * 0.09), 0.9), V(1.22, max(y, y - direction * 0.09), underframe_top), 0.0, "box", None, ("top",))
        far_buffers(part, y, direction)
    for number, axle in enumerate(axles):
        far_wheelset(b, "wheel_%d" % (number + 1), axle, radius)


def wagon_flat_far():
    b = rk.Build("train_wagon_flat_far", 42)
    part = b.part("body", 40.0)
    wagon_far_base(b, part)
    block(part, "timber_planks_weathered", V(-1.25, -2.72, underframe_top), V(1.25, 2.72, deck_top), 0.0, "box", None, ("bottom",))
    block(part, "timber_beam", V(-1.06, -2.65, deck_top), V(-0.2, 2.65, deck_top + 0.26), 0.0, "box", None, ("bottom",))
    block(part, "rust_iron", V(0.1, -2.45, deck_top + 0.13), V(1.02, 2.45, deck_top + 0.43), 0.0, "box", None, ("bottom",))
    for side in (-1.0, 1.0):
        for y in (-2.1, -0.75, 0.75, 2.1):
            if not (side > 0 and abs(y + 0.75) < 0.01):
                block(part, "rust_iron", V(side * 1.3 - 0.035, y - 0.025, 1.0), V(side * 1.3 + 0.035, y + 0.025, 2.15), 0.0, "box", None, ("bottom",))
    return b


models = {
    "rail_track": (track, track_far, 40000, 400),
    "rail_track_weeds": (track_weeds, lambda: track_far("rail_track_weeds_far"), 50000, 400),
    "train_locomotive": (locomotive, locomotive_far, 200000, 3000),
    "train_wagon_flat": (wagon_flat, wagon_flat_far, 120000, 2000),
}


def build(name):
    maker, far_maker, budget, far_budget = models[name]
    rk.register()
    kit.reset_scene()
    started = time.time()
    b = maker()
    objects = b.finish()
    path, document = rk.export_model(name, objects, getattr(b, "externals", None))
    rk.audit(path, document, budget)
    print("BUILD", name, "parts", len(b.parts), "boxes", len(b.boxes), round(time.time() - started, 1), "s", flush=True)
    if far_maker is not None:
        kit.reset_scene()
        far = far_maker()
        objects = far.finish()
        path, document = rk.export_model(name + "_far", objects, getattr(far, "externals", None))
        rk.audit(path, document, far_budget)


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
views = {
    "train_locomotive": {
        "context": on_track,
        "ground": -0.502,
        "sun": (-0.5, -0.45, -0.7),
        "shots": [
            ("three", (6.2, 8.0, 3.3), (0.0, 0.2, 1.5), 35.0, 0.0, None),
            ("rear", (-6.4, -7.6, 2.9), (0.0, -0.4, 1.5), 35.0, 0.0, None),
            ("detail", (2.7, 5.3, 1.9), (0.7, 2.9, 1.55), 45.0, 0.0, None),
            ("wheels", (3.4, 1.0, 0.75), (0.7, 0.4, 0.75), 35.0, 0.6, None),
            ("cab", (0.5, -2.95, 2.925), (-0.25, -1.3, 2.35), 15.0, 2.2, 16.0),
            ("cab_rear", (-0.3, -1.85, 2.925), (0.5, -3.3, 2.3), 15.0, 2.2, 16.0),
        ],
        "levels": [("STEPS", 1.22, -0.5, 1.0), ("FOOTPLATE", 3.15, 1.0, 3.2), ("ROOF", 5.0, 3.2, 4.0)],
    },
    "train_wagon_flat": {
        "context": on_track,
        "ground": -0.502,
        "sun": (-0.5, -0.45, -0.7),
        "shots": [
            ("three", (5.4, 6.4, 3.0), (0.0, 0.0, 1.0), 35.0, 0.0, None),
            ("detail", (2.9, 2.6, 1.0), (0.9, 1.4, 0.75), 40.0, 0.3, None),
        ],
    },
}


def preview_model(name, which=None):
    spec = views[name]
    kit.reset_scene()
    rk.register()
    objects, boxes = place(name)
    for extra, offset in spec.get("context", []):
        place(extra, offset)
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
    print("DONE", mode, round(time.time() - started, 1), "s", flush=True)


if __name__ == "__main__":
    main()
