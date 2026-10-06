import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import railtrain as rt
import buildings as bd
from buildkit import V, block, emit, rod, lump, local_block, frame_block
from mathutils import Matrix

tau = math.pi * 2.0
X = V(1.0, 0.0, 0.0)
Y = V(0.0, 1.0, 0.0)
Z = V(0.0, 0.0, 1.0)
rail_top = 0.5
gauge_center = 0.7525
platform_top = rail_top + 1.2
platform_half = 2.0
platform_length = 12.0
platform_offset = 1.45
plinth = -1.0
ramp_length = 5.0


def sloped_block(part, name, xa, xb, y0, y1, za, zb, thickness, skip_top=False, mapping="box"):
    points = [V(xa, y0, za - thickness), V(xb, y0, zb - thickness), V(xb, y1, zb - thickness), V(xa, y1, za - thickness), V(xa, y0, za), V(xb, y0, zb), V(xb, y1, zb), V(xa, y1, za)]
    faces = [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 7, 6), (0, 4, 7, 3), (1, 2, 6, 5)]
    if not skip_top:
        faces.append((4, 5, 6, 7))
    emit(part, kit.Geo(points, faces), name, None, mapping)


def coping(part, rng, xa, xb, nose, inward, za, zb, strip, thick=0.13):
    far = nose + inward * rk.edge_depth
    lift = rng.uniform(-0.003, 0.003)
    corners = [V(xa, nose, za + lift), V(xb, nose, zb + lift), V(xb, far, zb + lift), V(xa, far, za + lift)]
    uv = [rk.edge_uv(xa, 0.0, strip), rk.edge_uv(xb, 0.0, strip), rk.edge_uv(xb, 1.0, strip), rk.edge_uv(xa, 1.0, strip)]
    geo = rk.facing(kit.Geo(corners, [(0, 1, 2, 3)], [uv]), Z)
    emit(part, geo, "platform_edge", None, "texture", False)
    y0, y1 = sorted((nose, far))
    sloped_block(part, "granite_ashlar", xa + 0.004, xb - 0.004, y0, y1, za + lift - 0.001, zb + lift - 0.001, thick, True)


def flags(part, rng, x0, x1, y0, y1, level, name="granite_ashlar", sizes=(0.5, 0.95), missing=None):
    y = y0
    while y < y1 - 0.05:
        depth = min(rng.uniform(*sizes), y1 - y)
        if y1 - (y + depth) < 0.25:
            depth = y1 - y
        x = x0
        while x < x1 - 0.05:
            width = min(rng.uniform(*sizes) * 1.2, x1 - x)
            if x1 - (x + width) < 0.25:
                width = x1 - x
            if missing is None or not missing(x + width * 0.5, y + depth * 0.5):
                drop = rng.uniform(0.0, 0.006)
                sloped_block(part, name, x + 0.006, x + width - 0.006, y + 0.006, y + depth - 0.006, level(x + 0.006) - drop, level(x + width - 0.006) - drop, 0.07)
            x += width
        y += depth


def platform():
    b = rk.Build("rail_platform", 201)
    rng = b.rng
    shell = b.part("shell", 30.0)
    paving = b.part("paving", 30.0)
    plants = b.part("plants", 70.0)
    half = platform_length * 0.5
    top = platform_top
    face = platform_half - 0.08
    front = kit.facade("front", half, face)
    back = kit.facade("back", half, platform_half)
    kit.wall(shell, "granite_rubble", front, kit.rect(-half, half, plinth, top - 0.12), [], 0.45)
    kit.wall(shell, "granite_rubble", back, kit.rect(-half, half, plinth, top - 0.1), [], 0.45)
    kit.wall(shell, "granite_rubble", kit.facade("left", half, platform_half), kit.rect(-platform_half, face, plinth, top - 0.12), [], 0.45)
    kit.wall(shell, "granite_rubble", kit.facade("right", half, platform_half), kit.rect(-face, platform_half, plinth, top - 0.12), [], 0.45)
    bd.damp_band(shell, front, -half, half, rng, 0.2, 0.75, "granite_rubble_damp", plinth + 0.02)
    x = -half
    while x < half - 0.1:
        width = min(rng.uniform(0.5, 0.9), half - x)
        if half - (x + width) < 0.3:
            width = half - x
        frame_block(shell, "granite_ashlar", front, x + 0.006, x + width - 0.006, top - 0.34, top - 0.13, -0.025, 0.2, 0.015)
        x += width
    for index in range(int(platform_length)):
        coping(shell, rng, -half + index, -half + index + 1.0, -platform_half, 1.0, top, top, 0)
    inner = -platform_half + rk.edge_depth
    gaps = [(rng.uniform(-half + 1.0, half - 1.0), rng.uniform(inner + 0.5, platform_half - 0.8)) for index in range(3)]
    flags(paving, rng, -half, half, inner, platform_half - 0.3, lambda x: top, "granite_ashlar", (0.5, 0.95), lambda x, y: any(abs(x - gx) < 0.3 and abs(y - gy) < 0.3 for gx, gy in gaps))
    block(paving, "dirt_debris", V(-half, inner, top - 0.2), V(half, platform_half - 0.3, top - 0.05))
    x = -half
    while x < half - 0.1:
        width = min(rng.uniform(0.7, 1.2), half - x)
        if half - (x + width) < 0.4:
            width = half - x
        block(shell, "granite_ashlar", V(x + 0.006, platform_half - 0.3, top - 0.16), V(x + width - 0.006, platform_half + 0.03, top + rng.uniform(-0.004, 0.002)), 0.015)
        x += width
    for gx, gy in gaps:
        for index in range(6):
            kit.grass_tuft(plants, V(gx + rng.uniform(-0.25, 0.25), gy + rng.uniform(-0.25, 0.25), top - 0.05), rng, (0.12, 0.35), (5, 10), 0.06)
    for index in range(26):
        kit.grass_tuft(plants, V(rng.uniform(-half, half), rng.choice((inner + rng.uniform(-0.01, 0.01), platform_half - 0.31, rng.uniform(inner, platform_half - 0.4))), top - 0.01), rng, (0.06, 0.2), (3, 7), 0.03)
    for index in range(14):
        kit.grass_tuft(plants, V(rng.uniform(-half, half), -face - 0.04, rng.uniform(0.3, 1.3)), rng, (0.08, 0.22), (3, 6), 0.04)
    outlet = V(-2.4, -face, 0.9)
    rk.lathe(shell, "rust_iron", outlet + V(0.0, 0.02, 0.0), -Y, [(0.0, 0.0), (0.075, 0.0), (0.075, 0.09), (0.06, 0.09), (0.06, 0.01), (0.0, 0.01)], 14)
    b.col("rock", "platform", V(-half, -platform_half, plinth), V(half, platform_half, top))
    return b


def platform_far():
    b = rk.Build("rail_platform_far", 202)
    part = b.part("platform", 30.0)
    half = platform_length * 0.5
    top = platform_top
    kit.wall(part, "granite_rubble", kit.facade("front", half, platform_half - 0.08), kit.rect(-half, half, plinth, top - 0.12), [], 0.1)
    kit.wall(part, "granite_rubble", kit.facade("back", half, platform_half), kit.rect(-half, half, plinth, top), [], 0.1)
    kit.wall(part, "granite_rubble", kit.facade("left", half, platform_half), kit.rect(-platform_half, platform_half - 0.08, plinth, top - 0.12), [], 0.1)
    kit.wall(part, "granite_rubble", kit.facade("right", half, platform_half), kit.rect(-platform_half + 0.08, platform_half, plinth, top - 0.12), [], 0.1)
    corners = [V(-half, -platform_half, top), V(half, -platform_half, top), V(half, -platform_half + rk.edge_depth, top), V(-half, -platform_half + rk.edge_depth, top)]
    uv = [rk.edge_uv(-half, 0.0, 0), rk.edge_uv(half, 0.0, 0), rk.edge_uv(half, 1.0, 0), rk.edge_uv(-half, 1.0, 0)]
    emit(part, kit.Geo(corners, [(0, 1, 2, 3)], [uv]), "platform_edge", None, "texture", False)
    block(part, "granite_ashlar", V(-half, -platform_half, top - 0.13), V(half, -platform_half + 0.1, top - 0.001), 0.0, "box", None, ("top", "back"))
    block(part, "granite_ashlar", V(-half, -platform_half + rk.edge_depth, top - 0.1), V(half, platform_half, top), 0.0, "box", None, ("bottom", "front", "back"))
    return b


def ramp_level(x):
    return platform_top * (ramp_length * 0.5 - x) / ramp_length


def platform_end():
    b = rk.Build("rail_platform_end", 211)
    rng = b.rng
    shell = b.part("shell", 30.0)
    paving = b.part("paving", 30.0)
    plants = b.part("plants", 70.0)
    half = ramp_length * 0.5
    face = platform_half - 0.08
    for name in ("front", "back"):
        frame = kit.facade(name, half, face)
        flip = frame[1].x
        kit.wall(shell, "granite_rubble", frame, [(-half, plinth), (half, plinth), (half, ramp_level(flip * half) - 0.12), (-half, ramp_level(-flip * half) - 0.12)], [], 0.45)
    kit.wall(shell, "granite_rubble", kit.facade("right", half, platform_half), kit.rect(-face, face, plinth, -0.1), [], 0.45)
    count = int(ramp_length)
    for side in (-1.0, 1.0):
        for index in range(count):
            xa = -half + index
            coping(shell, rng, xa, xa + 1.0, side * platform_half, -side, ramp_level(xa), ramp_level(xa + 1.0), 2)
    inner = platform_half - rk.edge_depth
    flags(paving, rng, -half, half, -inner, inner, ramp_level, "granite_ashlar", (0.5, 0.9), lambda x, y: x > 1.0 and abs(y - 0.4) < 0.35)
    sloped_block(paving, "dirt_debris", -half, half, -inner, inner, ramp_level(-half) - 0.05, ramp_level(half) - 0.05, 0.2)
    for index in range(7):
        kit.grass_tuft(plants, V(rng.uniform(1.0, 2.2), 0.4 + rng.uniform(-0.3, 0.3), ramp_level(1.6) - 0.06), rng, (0.12, 0.35), (5, 10), 0.06)
    for index in range(16):
        x = rng.uniform(-half, half)
        kit.grass_tuft(plants, V(x, rng.choice((-1.0, 1.0)) * inner, ramp_level(x) - 0.01), rng, (0.06, 0.2), (3, 7), 0.03)
    for index in range(12):
        x = rng.uniform(0.5, half + 0.2)
        kit.grass_tuft(plants, V(x, rng.uniform(-platform_half, platform_half), max(ramp_level(x), 0.0) - 0.02), rng, (0.1, 0.3), (4, 9), 0.05)
    b.ramp("nx", "rock", "slope", V(-half, -platform_half, 0.0), V(half, platform_half, platform_top))
    b.col("rock", "base", V(-half, -platform_half, plinth), V(half, platform_half, 0.0))
    return b


def platform_end_far():
    b = rk.Build("rail_platform_end_far", 212)
    part = b.part("platform", 30.0)
    half = ramp_length * 0.5
    for name in ("front", "back"):
        frame = kit.facade(name, half, platform_half)
        flip = frame[1].x
        kit.wall(part, "granite_rubble", frame, [(-half, plinth), (half, plinth), (half, ramp_level(flip * half)), (-half, ramp_level(-flip * half))], [], 0.1)
    sloped_block(part, "granite_ashlar", -half, half, -platform_half, platform_half, ramp_level(-half), ramp_level(half), 0.1)
    return b


def inclined_rail(part, start, yaw, pitch, length, band="dull"):
    matrix = Matrix.Translation(start) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'X')
    emit(part, rk.rail_geo(0.0, length, 2, True, band), "rail_steel", matrix, "texture", True)
    return matrix


def buffer():
    b = rk.Build("rail_buffer", 231)
    rng = b.rng
    frame = b.part("frame", 40.0)
    beam = b.part("beam", 40.0, 50)
    detail = b.part("detail", 40.0)
    plants = b.part("plants", 70.0)
    centre = rail_top + rt.buffer_height
    rake = math.atan2(centre - 0.04 - rail_top, 1.95)
    length = math.hypot(1.95, centre - 0.04 - rail_top)
    for side in (-1.0, 1.0):
        x = side * gauge_center
        inclined_rail(frame, V(x, 2.35, rail_top - 0.01), math.pi, rake, length + 0.12)
        inclined_rail(frame, V(x, 0.48, rail_top - 0.02), 0.0, math.pi * 0.5, centre + 0.16 - rail_top)
        for y, z in ((2.3, rail_top + 0.02), (0.52, rail_top + 0.04)):
            block(detail, "rust_iron", V(x - 0.1, y - 0.12, z - 0.05), V(x + 0.1, y + 0.12, z + 0.05), 0.008)
            for corner in (-0.07, 0.07):
                rk.prism_bolt(detail, "rust_iron", V(x + corner, y, z + 0.05), Z, 0.03, 0.016, 6)
        block(detail, "rust_iron", V(x - 0.09, 0.3, centre - 0.18), V(x + 0.09, 0.5, centre + 0.18), 0.008)
        for z in (centre - 0.1, centre + 0.1):
            rk.prism_bolt(detail, "rust_iron", V(x, 0.0, z), -Y, 0.045, 0.024, 6, 0.006)
        b.col("metal", "frame", V(x - 0.08, 0.3, rail_top), V(x + 0.08, 1.3, centre + 0.16))
        b.col("metal", "frame", V(x - 0.08, 1.3, rail_top), V(x + 0.08, 2.35, rail_top + 0.6))
    inclined_rail(frame, V(-1.05, 0.56, centre - 0.34), -math.pi * 0.5, 0.0, 2.1)
    for index in range(3):
        block(beam, "painted_wood_bauxite", V(-1.3, 0.0, centre - 0.15 + index * 0.1 + 0.002), V(1.3, 0.3, centre - 0.05 + index * 0.1 - 0.002), 0.006, "board")
    for side in (-1.0, 1.0):
        block(detail, "rust_iron", V(side * 1.3 - 0.006, -0.006, centre - 0.16), V(side * 1.3 + 0.006, 0.306, centre + 0.16))
        block(detail, "rust_iron", V(side * 1.18 - 0.03, -0.008, centre - 0.16), V(side * 1.18 + 0.03, 0.0, centre + 0.16))
        rk.lathe(beam, "rust_iron", V(side * rt.buffer_spread, 0.0, centre), -Y, [(0.0, 0.0), (0.21, 0.0), (0.21, 0.035), (0.17, 0.05), (0.0, 0.055)], 20)
        for angle in range(4):
            rk.prism_bolt(detail, "rust_iron", V(side * rt.buffer_spread + math.cos(angle * tau / 4.0 + 0.78) * 0.14, -0.045, centre + math.sin(angle * tau / 4.0 + 0.78) * 0.14), -Y, 0.03, 0.014, 6)
    rt.lamp_iron(detail, V(0.0, 0.15, centre + 0.152), Y)
    rt.oil_lamp(detail, V(0.0, 0.2, centre + 0.31), -Y)
    rk.atlas_disc(detail, "lens_red", V(0.0, 0.103, centre + 0.41), -Y, Z, 0.052, 14)
    for index in range(16):
        kit.grass_tuft(plants, V(rng.uniform(-1.2, 1.2), rng.uniform(0.2, 2.6), 0.27), rng, (0.15, 0.5), (5, 11), 0.08)
    b.col("wood", "beam", V(-1.3, 0.0, centre - 0.2), V(1.3, 0.3, centre + 0.2))
    return b


def buffer_far():
    b = rk.Build("rail_buffer_far", 232)
    part = b.part("buffer", 40.0)
    centre = rail_top + rt.buffer_height
    for side in (-1.0, 1.0):
        x = side * gauge_center
        block(part, "rust_iron", V(x - 0.05, 0.38, rail_top), V(x + 0.05, 0.52, centre + 0.15))
        geo = kit.geo_box(0.1, 2.25, 0.12)
        emit(part, geo, "rust_iron", Matrix.Translation(V(x, 1.4, (rail_top + centre) * 0.5)) @ Matrix.Rotation(-math.atan2(centre - rail_top, 1.95), 4, 'X'), "box")
    block(part, "painted_wood_bauxite", V(-1.3, 0.0, centre - 0.15), V(1.3, 0.3, centre + 0.15), 0.0, "board")
    return b


signal_height = 7.0
signal_pivot = 6.2
signal_drop = 40.0


def signal_arm(part, detail, matrix):
    local_block(part, "loco_black", matrix, -1.3, 0.16, -0.012, 0.012, -0.13, 0.13)
    u0, v0, u1, v1 = rk.sign_uv("arm_front")
    corners = [matrix @ V(-1.3, -0.0135, -0.13), matrix @ V(0.16, -0.0135, -0.13), matrix @ V(0.16, -0.0135, 0.13), matrix @ V(-1.3, -0.0135, 0.13)]
    rk.quad(part, "rail_signs", corners, "texture", False, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    u0, v0, u1, v1 = rk.sign_uv("arm_back")
    corners = [matrix @ V(0.16, 0.0135, -0.13), matrix @ V(-1.3, 0.0135, -0.13), matrix @ V(-1.3, 0.0135, 0.13), matrix @ V(0.16, 0.0135, 0.13)]
    rk.quad(part, "rail_signs", corners, "texture", False, [(u1, v0), (u0, v0), (u0, v1), (u1, v1)])
    turn = matrix.to_3x3()
    for name, angle in (("lens_red", 0.0), ("lens_green", -math.radians(signal_drop))):
        center = matrix @ V(0.34 * math.cos(angle), 0.0, 0.34 * math.sin(angle))
        emit(detail, kit.geo_lathe([(0.082, -0.014), (0.105, -0.014), (0.105, 0.014), (0.082, 0.014), (0.082, -0.014)], 18), "loco_black", rk.frame_along(center, turn @ V(0.0, -1.0, 0.0)), "given", False)
        rk.atlas_disc(detail, name, center + turn @ V(0.0, -0.004, 0.0), turn @ V(0.0, -1.0, 0.0), Z, 0.083, 16)
        rk.atlas_disc(detail, name, center + turn @ V(0.0, 0.004, 0.0), turn @ V(0.0, 1.0, 0.0), Z, 0.083, 16)
        rk.bar(detail, "loco_black", [matrix @ V(0.1, 0.0, 0.0), matrix @ V(0.26 * math.cos(angle), 0.0, 0.26 * math.sin(angle))], 0.05, 0.016, turn @ V(0.0, 1.0, 0.0))
    rk.lathe(detail, "rust_iron", matrix @ V(0.0, -0.03, 0.0), turn @ V(0.0, -1.0, 0.0), [(0.0, 0.0), (0.04, 0.0), (0.04, 0.02), (0.02, 0.03), (0.0, 0.03)], 10)


def signal():
    b = rk.Build("rail_signal", 221)
    rng = b.rng
    post = b.part("post", 40.0, 50)
    detail = b.part("detail", 40.0)
    height = signal_height
    emit(post, kit.geo_frustum(0.11, 0.11, 0.075, 0.075, height), "painted_wood_white", None, "board")
    emit(post, kit.geo_frustum(0.116, 0.116, 0.111, 0.111, 1.15), "soot", None, "box")
    block(post, "concrete", V(-0.3, -0.3, -0.6), V(0.3, 0.3, 0.05), 0.03)
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.1, 0.0), (0.1, 0.03), (0.04, 0.06), (0.03, 0.12), (0.075, 0.2), (0.075, 0.24), (0.02, 0.32), (0.012, 0.52), (0.0, 0.54)], 14), "red", Matrix.Translation(V(0.0, 0.0, height)))
    arm = Matrix.Translation(V(0.0, -0.125, signal_pivot)) @ Matrix.Rotation(-math.radians(signal_drop), 4, 'Y')
    signal_arm(post, detail, arm)
    block(detail, "loco_black", V(-0.05, -0.115, signal_pivot - 0.09), V(0.05, -0.075, signal_pivot + 0.09), 0.006)
    lamp = V(0.34, 0.03, signal_pivot)
    local_block(detail, "loco_black", Matrix.Translation(lamp), -0.085, 0.085, -0.085, 0.085, -0.12, 0.1, 0.008)
    emit(detail, kit.geo_lathe([(0.0, 0.1), (0.07, 0.1), (0.05, 0.14), (0.03, 0.15), (0.03, 0.19), (0.0, 0.2)], 12), "loco_black", Matrix.Translation(lamp), "given", True)
    rk.lathe(detail, "loco_black", lamp + V(0.0, -0.085, 0.0), -Y, [(0.06, 0.0), (0.06, 0.03), (0.05, 0.035)], 14)
    rk.atlas_disc(detail, "lens_clear", lamp + V(0.0, -0.1, 0.0), -Y, Z, 0.05, 12)
    block(detail, "loco_black", V(0.06, -0.02, signal_pivot - 0.14), V(0.34, 0.06, signal_pivot - 0.12))
    rk.bar(detail, "loco_black", [V(0.07, 0.02, signal_pivot - 0.45), V(0.3, 0.02, signal_pivot - 0.14)], 0.03, 0.01, Y)
    b.light("warm", lamp + V(0.0, -0.14, 0.0))
    for side in (-1.0, 1.0):
        rk.bar(detail, "loco_black", [V(side * 0.17, 0.95, 0.05), V(side * 0.17, 0.2, 5.95)], 0.045, 0.012, X)
    rung = 0.35
    while rung < 5.9:
        y = 0.95 - 0.75 * (rung - 0.05) / 5.9
        rk.pipe(detail, "loco_black", [V(-0.17, y, rung), V(0.17, y, rung)], 0.009, 6)
        rung += 0.29
    for z in (2.2, 4.0, 5.7):
        y = 0.95 - 0.75 * (z - 0.05) / 5.9
        for side in (-1.0, 1.0):
            rk.bar(detail, "loco_black", [V(side * 0.17, y, z), V(side * 0.06, 0.09, z)], 0.03, 0.008, Z)
    pivot = V(0.0, -0.16, 1.05)
    block(detail, "loco_black", V(-0.06, -0.2, 0.95), V(0.06, -0.11, 1.15), 0.006)
    rk.bar(detail, "loco_black", [pivot + V(-0.42, -0.02, -0.1), pivot + V(0.0, -0.02, 0.0), pivot + V(0.3, -0.02, 0.07)], 0.05, 0.016, Y)
    rk.lathe(detail, "rust_iron", pivot + V(-0.36, -0.06, -0.085), -Y, [(0.0, 0.0), (0.13, 0.0), (0.13, 0.05), (0.0, 0.05)], 16)
    rk.lathe(detail, "rust_iron", pivot + V(0.0, -0.035, 0.0), -Y, [(0.0, 0.0), (0.03, 0.0), (0.03, 0.02), (0.0, 0.02)], 8)
    rk.pipe(detail, "rust_iron", [pivot + V(0.27, -0.02, 0.07), arm @ V(0.16, 0.035, -0.03)], 0.007, 6)
    rk.lathe(detail, "rust_iron", V(0.0, -0.19, 0.32), -Y, [(0.0, -0.012), (0.09, -0.012), (0.1, -0.006), (0.085, 0.0), (0.1, 0.006), (0.09, 0.012), (0.0, 0.012)], 16)
    block(detail, "loco_black", V(-0.02, -0.19, 0.2), V(0.02, -0.11, 0.44))
    rk.pipe(detail, "rust_iron", [pivot + V(-0.42, -0.02, -0.1), V(-0.09, -0.19, 0.36)], 0.004, 5)
    rk.pipe(detail, "rust_iron", [V(0.0, -0.19, 0.225), V(0.6, -0.6, 0.12), V(1.6, -0.75, 0.1)], 0.004, 5)
    b.col("wood", "post", V(-0.11, -0.11, 0.0), V(0.11, 0.11, height))
    return b


def signal_far():
    b = rk.Build("rail_signal_far", 222)
    post = b.part("post", 40.0)
    emit(post, kit.geo_frustum(0.11, 0.11, 0.075, 0.075, signal_height), "painted_wood_white", None, "board")
    arm = Matrix.Translation(V(0.0, -0.125, signal_pivot)) @ Matrix.Rotation(-math.radians(signal_drop), 4, 'Y')
    u0, v0, u1, v1 = rk.sign_uv("arm_front")
    corners = [arm @ V(-1.3, -0.0135, -0.13), arm @ V(0.16, -0.0135, -0.13), arm @ V(0.16, -0.0135, 0.13), arm @ V(-1.3, -0.0135, 0.13)]
    rk.quad(post, "rail_signs", corners, "texture", False, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    u0, v0, u1, v1 = rk.sign_uv("arm_back")
    corners = [arm @ V(0.16, 0.0135, -0.13), arm @ V(-1.3, 0.0135, -0.13), arm @ V(-1.3, 0.0135, 0.13), arm @ V(0.16, 0.0135, 0.13)]
    rk.quad(post, "rail_signs", corners, "texture", False, [(u1, v0), (u0, v0), (u0, v1), (u1, v1)])
    block(post, "loco_black", V(0.25, -0.06, signal_pivot - 0.12), V(0.43, 0.12, signal_pivot + 0.2))
    for side in (-1.0, 1.0):
        rk.bar(post, "loco_black", [V(side * 0.17, 0.95, 0.05), V(side * 0.17, 0.2, 5.95)], 0.045, 0.012, X)
    return b


crossing_half = 4.0
crossing_road = 2.5
crossing_deck = 1.88


def gate(b, part, detail, rng, hinge, yaw, length=2.35, fallen=False, sag=0.0):
    paint = "painted_wood_white"
    matrix = Matrix.Translation(hinge) @ Matrix.Rotation(yaw, 4, 'Z')
    if fallen:
        matrix = Matrix.Translation(hinge + V(0.0, 0.0, 0.06)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(math.radians(86.0), 4, 'X')
    elif sag != 0.0:
        matrix = matrix @ Matrix.Translation(V(0.0, 0.0, 1.2)) @ Matrix.Rotation(math.radians(sag), 4, 'Y') @ Matrix.Translation(V(0.0, 0.0, -1.2))
    z0 = 0.2
    z1 = 1.45
    local_block(part, paint, matrix, 0.0, 0.1, -0.04, 0.04, z0 - 0.05, z1 + 0.1, 0.006, "board")
    local_block(part, paint, matrix, length - 0.08, length, -0.035, 0.035, z0, z1 - 0.12, 0.006, "board")
    local_block(part, paint, matrix, 0.1, length - 0.08, -0.035, 0.035, z1 - 0.1, z1, 0.006, "board")
    for index, z in enumerate((z0 + 0.06, z0 + 0.3, z0 + 0.56, z0 + 0.84)):
        if index == 2 and sag != 0.0:
            local_block(part, paint, matrix, 0.1, length * 0.55, -0.012, 0.012, z - 0.05, z + 0.05, 0.003, "board")
            continue
        local_block(part, paint, matrix, 0.1, length - 0.08, -0.012, 0.012, z - 0.05, z + 0.05, 0.003, "board")
    start = V(0.12, 0.024, z0 + 0.04)
    end = V(length - 0.1, 0.024, z1 - 0.06)
    emit(part, kit.geo_box((end - start).length, 0.09, 0.022), paint, matrix @ kit.place((start + end) * 0.5, (end - start).normalized(), Y), "board")
    local_block(part, paint, matrix, length * 0.5 - 0.04, length * 0.5 + 0.04, -0.036, -0.012, z0, z1 - 0.1, 0.003, "board")
    turn = matrix.to_3x3()
    for face in (-1.0, 1.0):
        center = matrix @ V(length * 0.5, face * 0.0375, z0 + 0.72)
        rk.atlas_disc(part, "target", center, turn @ V(0.0, face, 0.0), turn @ Z, 0.26, 20, "rail_signs", 0.98)
    emit(part, kit.geo_lathe([(0.0, -0.036), (0.27, -0.036), (0.27, 0.036), (0.0, 0.036)], 20), paint, matrix @ Matrix.Translation(V(length * 0.5, 0.0, z0 + 0.72)) @ Matrix.Rotation(math.pi * 0.5, 4, 'X'), "box", False)
    for z in (z0 + 0.08, z1 - 0.05):
        local_block(detail, "rust_iron", matrix, -0.03, 0.62, 0.036, 0.044, z - 0.025, z + 0.025)
        rk.lathe(detail, "rust_iron", matrix @ V(-0.03, 0.04, z - 0.05), turn @ Z, [(0.0, 0.0), (0.018, 0.0), (0.018, 0.1), (0.0, 0.1)], 8)
    local_block(detail, "rust_iron", matrix, length - 0.02, length + 0.06, -0.01, 0.01, z0 + 0.62, z0 + 0.66)


def gate_post(b, part, position, height=1.75, size=0.2):
    half = size * 0.5
    block(part, "painted_wood_white", position + V(-half, -half, -0.5), position + V(half, half, height), 0.012, "board")
    emit(part, kit.geo_frustum(half + 0.02, half + 0.02, 0.03, 0.03, 0.12), "painted_wood_white", Matrix.Translation(position + V(0.0, 0.0, height)), "board")
    block(part, "soot", position + V(-half - 0.004, -half - 0.004, -0.4), position + V(half + 0.004, half + 0.004, 0.32))
    b.col("wood", "post", position + V(-half, -half, 0.0), position + V(half, half, height))


def warning_sign(part, detail, position, normal, height=2.4):
    side = Z.cross(normal).normalized()
    block(part, "rust_iron", position + V(-0.04, -0.04, -0.4), position + V(0.04, 0.04, height), 0.006)
    center = position + V(0.0, 0.0, height - 0.32) + normal * 0.05
    frame = kit.plane(center, normal)
    frame_block(part, "loco_black", frame, -0.46, 0.46, -0.31, 0.31, 0.0, 0.012, 0.004)
    rk.atlas_panel(detail, "beware", center + normal * 0.002, normal, Z, 0.9, 0.6)
    for a in (-0.4, 0.4):
        for up in (-0.25, 0.25):
            rk.prism_bolt(detail, "rust_iron", center + side * a + Z * up, normal, 0.022, 0.01, 6)


def crossing():
    b = rk.Build("rail_crossing", 241)
    rng = b.rng
    deck = b.part("deck", 40.0, 50)
    gates = b.part("gates", 40.0, 50)
    detail = b.part("detail", 40.0)
    plants = b.part("plants", 70.0)
    road = crossing_road
    level = rail_top - 0.012
    quarter = Matrix.Rotation(math.pi * 0.5, 4, 'Z')
    rows = [-0.52, -0.26, 0.0, 0.26, 0.52] + [side * (0.97 + index * 0.26) for side in (-1.0, 1.0) for index in range(4)]
    for x in rows:
        for end in (-1.0, 1.0):
            geo = rk.sleeper_geo(rng, rng.randrange(rk.strip_count), (rng.randrange(8), rng.randrange(8)), road - 0.006, 0.25, 0.13, rng.uniform(0.8, 1.7), (rng.uniform(0.15, 0.4) if rng.random() < 0.4 else 0.0, 0.0), rng.random() < 0.5)
            emit(deck, geo, "sleeper_timber", Matrix.Translation(V(x + rng.uniform(-0.004, 0.004), end * road * 0.5, level - rng.uniform(0.0, 0.008))) @ Matrix.Rotation(rng.uniform(-0.006, 0.006), 4, 'Z') @ quarter, "texture", True)
        for y in (-road + 0.3, -0.4, 0.4, road - 0.3):
            rk.prism_bolt(detail, "rust_iron", V(x, y + rng.uniform(-0.03, 0.03), level - 0.004), Z, 0.035, 0.012, 4, 0.0, 0.0, 0.78)
    x_top = crossing_deck
    slope = math.atan2(level - 0.02, crossing_half - x_top)
    count = 9
    pitch = math.hypot(crossing_half - x_top, level - 0.02) / count
    for side in (-1.0, 1.0):
        for index in range(count):
            reach = (index + 0.5) * pitch
            for end in (-1.0, 1.0):
                geo = rk.sleeper_geo(rng, rng.randrange(rk.strip_count), (rng.randrange(8), rng.randrange(8)), road - 0.006, 0.24, 0.13, rng.uniform(0.8, 1.7), (rng.uniform(0.15, 0.4) if rng.random() < 0.4 else 0.0, 0.0), rng.random() < 0.5)
                position = V(side * (x_top + reach * math.cos(slope)), end * road * 0.5, level - reach * math.sin(slope) - rng.uniform(0.0, 0.006))
                emit(deck, geo, "sleeper_timber", Matrix.Translation(position) @ Matrix.Rotation(side * slope, 4, 'Y') @ quarter, "texture", True)
        x0, x1 = sorted((side * x_top, side * crossing_half))
        z0, z1 = (level - 0.04, -0.02) if side > 0 else (-0.02, level - 0.04)
        sloped_block(deck, "dirt_debris", x0, x1, -road + 0.05, road - 0.05, z0, z1, 0.4)
        for y in (-road + 0.06, road - 0.06):
            rk.bar(deck, "timber_beam", [V(side * x_top, y, level - 0.06), V(side * crossing_half, y, -0.04)], 0.14, 0.12, Z)
    posts = [V(2.75, 2.72, 0.0), V(2.75, -2.72, 0.0), V(-2.75, 2.72, 0.0), V(-2.75, -2.72, 0.0)]
    for position in posts:
        gate_post(b, gates, position)
    gate(b, gates, detail, rng, posts[0] + V(0.12, 0.0, 0.0), math.radians(4.0))
    gate(b, gates, detail, rng, posts[1] + V(0.1, 0.06, 0.0), math.radians(38.0), 2.35, False, 5.0)
    gate(b, gates, detail, rng, posts[2] + V(-0.12, 0.0, 0.0), math.radians(183.0))
    gate(b, gates, detail, rng, posts[3] + V(-0.6, -0.5, 0.0), math.radians(200.0), 2.35, True)
    warning_sign(gates, detail, V(3.3, -3.15, 0.0), X)
    warning_sign(gates, detail, V(-3.3, 3.15, 0.0), -X)
    for index in range(40):
        side = rng.choice((-1.0, 1.0))
        kit.grass_tuft(plants, V(rng.uniform(-crossing_half, crossing_half), side * (road + rng.uniform(0.0, 0.5)), 0.0 if rng.random() < 0.5 else 0.2), rng, (0.15, 0.5), (5, 11), 0.08)
    for position in posts:
        for index in range(5):
            kit.grass_tuft(plants, position + V(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.0), rng, (0.15, 0.45), (5, 10), 0.06)
    b.col("wood", "deck", V(-crossing_deck, -road, 0.1), V(crossing_deck, road, level))
    b.ramp("nx", "wood", "approach", V(crossing_deck, -road, 0.0), V(crossing_half, road, level))
    b.ramp("px", "wood", "approach", V(-crossing_half, -road, 0.0), V(-crossing_deck, road, level))
    b.col("wood", "gate", V(2.87, 2.68, 0.15), V(5.25, 2.95, 1.45))
    b.col("wood", "gate", V(-5.25, 2.5, 0.15), V(-2.87, 2.76, 1.45))
    return b


def crossing_far():
    b = rk.Build("rail_crossing_far", 242)
    part = b.part("crossing", 40.0)
    level = rail_top - 0.012
    block(part, "timber_beam", V(-0.645, -crossing_road, level - 0.13), V(0.645, crossing_road, level), 0.0, "box", None, ("bottom",))
    for side in (-1.0, 1.0):
        block(part, "timber_beam", V(side * 0.845, -crossing_road, level - 0.13), V(side * crossing_deck, crossing_road, level), 0.0, "box", None, ("bottom",))
        x0, x1 = sorted((side * crossing_deck, side * crossing_half))
        z0, z1 = (level, 0.02) if side > 0 else (0.02, level)
        sloped_block(part, "timber_planks_weathered", x0, x1, -crossing_road, crossing_road, z0, z1, 0.3)
        for y in (-2.72, 2.72):
            block(part, "painted_wood_white", V(side * 2.75 - 0.1, y - 0.1, 0.0), V(side * 2.75 + 0.1, y + 0.1, 1.8), 0.0, "board")
    for x0, x1, y in ((2.87, 5.2, 2.75), (-5.2, -2.87, 2.7)):
        block(part, "painted_wood_white", V(x0, y - 0.03, 0.2), V(x1, y + 0.03, 1.45), 0.0, "board")
    return b


gate_length = 2.35
gate_pivot = 0.205
gate_low = 0.14
gate_high = 1.42
gate_hinges = (gate_low + 0.07, gate_high - 0.07)
gate_heel = (0.035, 0.165)
gate_head = gate_length - 0.09
gate_pales = 18
gate_target = V(gate_length * 0.5 + 0.06, 0.0, 0.98)
post_half = 0.13
post_height = 1.95
post_lamp = V(0.0, 0.0, post_height + 0.36)
sign_plate = (0.84, 0.56)
sign_center = 1.85
sign_post = 2.25


def card(part, name, x0, x1, z0, z1, y, side, mapping="board"):
    geo = kit.Geo([V(x0, y, z0), V(x1, y, z0), V(x1, y, z1), V(x0, y, z1)], [(0, 1, 2, 3)])
    emit(part, rk.facing(geo, V(0.0, side, 0.0)), name, None, mapping)


def pale_positions():
    pitch = (gate_head - gate_heel[1] - 0.07) / (gate_pales - 1)
    return [gate_heel[1] + 0.035 + index * pitch for index in range(gate_pales)]


def crossing_gate():
    b = rk.Build("rail_crossing_gate", 261)
    rng = b.rng
    wood = b.part("leaf", 40.0, 50)
    iron = b.part("iron", 40.0)
    paint = "painted_wood_white"
    heel0, heel1 = gate_heel
    block(wood, paint, V(heel0, -0.055, gate_low - 0.04), V(heel1, 0.055, gate_high + 0.1), 0.008, "board")
    emit(wood, kit.geo_frustum(0.069, 0.059, 0.03, 0.024, 0.05), paint, Matrix.Translation(V((heel0 + heel1) * 0.5, 0.0, gate_high + 0.1)), "board")
    block(wood, paint, V(gate_head, -0.04, gate_low), V(gate_length, 0.04, gate_high - 0.01), 0.006, "board")
    emit(wood, kit.geo_frustum(0.047, 0.042, 0.02, 0.018, 0.03), paint, Matrix.Translation(V(gate_head + 0.045, 0.0, gate_high - 0.01)), "board")
    block(wood, paint, V(heel1 - 0.01, -0.055, gate_high - 0.12), V(gate_head + 0.01, 0.055, gate_high), 0.008, "board")
    for z0, z1 in ((gate_low, gate_low + 0.1), (0.72, 0.8)):
        block(wood, paint, V(heel1 - 0.01, -0.035, z0), V(gate_head + 0.01, 0.035, z1), 0.006, "board")
    for index, x in enumerate(pale_positions()):
        if index == 11:
            for z in (gate_low + 0.05, 0.76):
                rk.prism_bolt(iron, "rust_iron", V(x, 0.035, z), Y, 0.014, 0.004, 4)
            continue
        top = 0.62 + rng.uniform(-0.03, 0.03) if index == 4 else gate_high - 0.12
        lean = rng.uniform(-0.004, 0.004)
        block(wood, paint, V(x - 0.034 + lean, 0.035, gate_low + 0.012), V(x + 0.034 + lean, 0.056, top), 0.004, "board")
        for z in (gate_low + 0.05, 0.76):
            rk.prism_bolt(iron, "rust_iron", V(x, 0.056, z), Y, 0.014, 0.004, 4)
    start = V(heel1 + 0.03, -0.0575, gate_low + 0.08)
    end = V(gate_head - 0.03, -0.0575, gate_high - 0.15)
    kit.member(wood, paint, start, end, 0.095, 0.045, Y, 0.006, "board")
    block(wood, paint, V(gate_target.x - 0.035, -0.08, 0.72), V(gate_target.x + 0.035, -0.035, gate_high - 0.12), 0.004, "board")
    for z, face in ((gate_hinges[0], 0.035), (gate_hinges[1], 0.055)):
        for side in (-1.0, 1.0):
            block(iron, "rust_iron", V(0.0, side * face, z - 0.025), V(0.72, side * (face + 0.008), z + 0.025), 0.002)
            for x in (0.26, 0.47, 0.68):
                rk.prism_bolt(iron, "rust_iron", V(x, side * (face + 0.008), z), V(0.0, side, 0.0), 0.024, 0.008, 6)
        block(iron, "rust_iron", V(0.012, -face - 0.008, z - 0.025), V(0.045, face + 0.008, z + 0.025), 0.002)
        rk.lathe(iron, "rust_iron", V(0.0, 0.0, z - 0.03), Z, [(0.014, 0.0), (0.03, 0.0), (0.03, 0.06), (0.014, 0.06), (0.014, 0.0)], 12, False)
    for side, y in ((1.0, 0.056), (-1.0, -0.08)):
        center = V(gate_target.x, y, gate_target.z)
        rk.lathe(iron, "rust_iron", center, V(0.0, side, 0.0), [(0.0, 0.0), (0.31, 0.0), (0.31, 0.012), (0.0, 0.012)], 24, False)
        rk.atlas_disc(iron, "target", center + V(0.0, side * 0.0125, 0.0), V(0.0, side, 0.0), Z, 0.3, 24, "rail_signs", 0.98)
        for angle in (0.6, 2.2, 3.8, 5.4):
            rk.prism_bolt(iron, "rust_iron", center + V(math.cos(angle) * 0.27, side * 0.0125, math.sin(angle) * 0.27), V(0.0, side, 0.0), 0.016, 0.005, 6)
    block(iron, "rust_iron", V(gate_head - 0.02, -0.012, 0.93), V(gate_length + 0.07, 0.012, 0.975), 0.003)
    block(iron, "rust_iron", V(gate_head - 0.03, 0.04, 0.89), V(gate_head + 0.06, 0.048, 1.01), 0.002)
    rk.pipe(iron, "rust_iron", [V(gate_length - 0.05, 0.048, 0.9), V(gate_length - 0.05, 0.1, 0.9), V(gate_length - 0.05, 0.1, 1.0), V(gate_length - 0.05, 0.048, 1.0)], 0.008, 6, 0.02)
    return b


def crossing_gate_far():
    b = rk.Build("rail_crossing_gate_far", 262)
    part = b.part("leaf", 40.0)
    paint = "painted_wood_white"
    heel0, heel1 = gate_heel
    block(part, paint, V(heel0, -0.055, gate_low - 0.04), V(heel1, 0.055, gate_high + 0.14), 0.0, "board")
    block(part, paint, V(gate_head, -0.04, gate_low), V(gate_length, 0.04, gate_high), 0.0, "board")
    block(part, paint, V(heel1, -0.055, gate_high - 0.12), V(gate_head, 0.055, gate_high), 0.0, "board")
    for z0, z1 in ((gate_low, gate_low + 0.1), (0.72, 0.8)):
        block(part, paint, V(heel1, -0.035, z0), V(gate_head, 0.035, z1), 0.0, "board")
    for index, x in enumerate(pale_positions()):
        if index == 11:
            continue
        top = 0.62 if index == 4 else gate_high - 0.12
        card(part, paint, x - 0.034, x + 0.034, gate_low, top, 0.056, 1.0)
        card(part, paint, x - 0.034, x + 0.034, gate_low, top, 0.034, -1.0)
    kit.member(part, paint, V(heel1 + 0.03, -0.0575, gate_low + 0.08), V(gate_head - 0.03, -0.0575, gate_high - 0.15), 0.095, 0.045, Y, 0.0, "board")
    for side, y in ((1.0, 0.068), (-1.0, -0.092)):
        rk.atlas_disc(part, "target", V(gate_target.x, y, gate_target.z), V(0.0, side, 0.0), Z, 0.3, 10, "rail_signs", 0.98)
    return b


def gate_lamp(part, detail, center):
    body = "loco_black"
    base = center - Z * 0.14
    rk.lathe(part, body, base, Z, [(0.0, 0.0), (0.098, 0.0), (0.104, 0.015), (0.104, 0.27), (0.096, 0.282), (0.068, 0.335), (0.044, 0.352), (0.044, 0.4), (0.0, 0.4)], 20, False)
    rk.lathe(part, body, base + Z * 0.41, Z, [(0.0, 0.035), (0.072, 0.012), (0.074, 0.0), (0.0, 0.0)], 16, False)
    for angle in (0.5, 2.6, 4.7):
        rk.pipe(detail, body, [base + V(math.cos(angle) * 0.04, math.sin(angle) * 0.04, 0.395), base + V(math.cos(angle) * 0.05, math.sin(angle) * 0.05, 0.415)], 0.004, 4, 0.0, False)
    for direction, radius, lens in ((Y, 0.068, "lens_red"), (-Y, 0.068, "lens_red"), (X, 0.042, "lens_clear"), (-X, 0.042, "lens_clear")):
        rim = center + direction * 0.1
        rk.lathe(part, body, rim, direction, [(radius + 0.006, -0.04), (radius + 0.008, 0.0), (radius + 0.012, 0.012), (radius + 0.008, 0.026), (radius - 0.004, 0.022)], 20, False)
        rk.atlas_disc(detail, lens, rim + direction * 0.016, direction, Z, radius, 18)
    side = V(math.cos(0.8), math.sin(0.8), 0.0)
    rk.pipe(detail, body, [center + side * 0.106 + Z * 0.1, center + side * 0.106 - Z * 0.1], 0.006, 6, 0.0)
    handle = [base + V(-0.06, 0.0, 0.33), base + V(-0.05, 0.0, 0.47), base + V(0.05, 0.0, 0.47), base + V(0.06, 0.0, 0.33)]
    rk.pipe(detail, "rust_iron", handle, 0.006, 6, 0.03)
    rk.lathe(detail, body, base - Z * 0.03, Z, [(0.0, 0.0), (0.06, 0.0), (0.075, 0.03), (0.0, 0.03)], 16, False)


def crossing_post():
    b = rk.Build("rail_crossing_post", 263)
    rng = b.rng
    wood = b.part("post", 40.0)
    iron = b.part("iron", 40.0)
    lamp = b.part("lamp", 40.0)
    plants = b.part("plants", 70.0)
    half = post_half
    paint = "painted_wood_white"
    block(wood, paint, V(-half, -half, -0.6), V(half, half, post_height), 0.014, "board")
    emit(wood, kit.geo_frustum(half + 0.02, half + 0.02, 0.03, 0.03, 0.12), paint, Matrix.Translation(V(0.0, 0.0, post_height)), "board")
    block(wood, "soot", V(-half - 0.004, -half - 0.004, -0.6), V(half + 0.004, half + 0.004, 0.32 + rng.uniform(-0.02, 0.02)), 0.01)
    block(wood, "concrete", V(-half - 0.09, -half - 0.09, -0.3), V(half + 0.09, half + 0.09, 0.03), 0.02)
    for z in (0.5, 1.72):
        block(iron, "rust_iron", V(-half - 0.006, -half - 0.006, z), V(half + 0.006, half + 0.006, z + 0.045), 0.003)
    for z in gate_hinges:
        block(iron, "rust_iron", V(half - 0.004, -0.05, z - 0.06), V(half + 0.012, 0.05, z + 0.05), 0.003)
        for dy in (-0.03, 0.03):
            for dz in (-0.04, 0.03):
                rk.prism_bolt(iron, "rust_iron", V(half + 0.012, dy, z + dz), X, 0.02, 0.008, 6)
        block(iron, "rust_iron", V(half + 0.012, -0.019, z - 0.055), V(gate_pivot + 0.016, 0.019, z - 0.031), 0.003)
        rk.pipe(iron, "rust_iron", [V(gate_pivot, 0.0, z - 0.05), V(gate_pivot, 0.0, z + 0.04)], 0.0135, 8)
    for side in (-1.0, 1.0):
        center = V(0.0, side * (half + 0.004), 1.62)
        rk.lathe(iron, "rust_iron", center, V(0.0, side, 0.0), [(0.0, 0.0), (0.205, 0.0), (0.205, 0.01), (0.0, 0.01)], 24, False)
        rk.atlas_disc(iron, "target", center + V(0.0, side * 0.0105, 0.0), V(0.0, side, 0.0), Z, 0.2, 24, "rail_signs", 0.98)
        for dz in (-0.14, 0.14):
            rk.prism_bolt(iron, "rust_iron", center + V(0.0, side * 0.0105, dz), V(0.0, side, 0.0), 0.02, 0.006, 6)
    rk.pipe(iron, "loco_black", [V(0.0, 0.0, post_height + 0.1), post_lamp - Z * 0.17], 0.022, 8)
    gate_lamp(lamp, iron, post_lamp)
    b.light("warm", post_lamp)
    for index in range(7):
        angle = rng.uniform(0.0, tau)
        kit.grass_tuft(plants, V(math.cos(angle) * rng.uniform(0.25, 0.42), math.sin(angle) * rng.uniform(0.25, 0.42), 0.0), rng, (0.15, 0.42), (5, 11), 0.06)
    b.col("wood", "post", V(-half, -half, 0.0), V(half, half, post_height + 0.12))
    return b


def crossing_post_far():
    b = rk.Build("rail_crossing_post_far", 264)
    part = b.part("post", 40.0)
    half = post_half
    block(part, "painted_wood_white", V(-half, -half, -0.3), V(half, half, post_height), 0.0, "board")
    emit(part, kit.geo_frustum(half + 0.02, half + 0.02, 0.03, 0.03, 0.12), "painted_wood_white", Matrix.Translation(V(0.0, 0.0, post_height)), "board")
    block(part, "soot", V(-half - 0.004, -half - 0.004, -0.3), V(half + 0.004, half + 0.004, 0.32), 0.0, "box", None, ("top", "bottom"))
    block(part, "loco_black", V(-0.02, -0.02, post_height + 0.1), V(0.02, 0.02, post_lamp.z - 0.14))
    rk.lathe(part, "loco_black", post_lamp - Z * 0.14, Z, [(0.0, 0.0), (0.104, 0.0), (0.104, 0.27), (0.044, 0.352), (0.0, 0.42)], 8, False)
    for side in (-1.0, 1.0):
        rk.atlas_disc(part, "target", V(0.0, side * (half + 0.015), 1.62), V(0.0, side, 0.0), Z, 0.2, 10, "rail_signs", 0.98)
        rk.atlas_disc(part, "lens_red", post_lamp + V(0.0, side * 0.106, 0.0), V(0.0, side, 0.0), Z, 0.07, 6)
    for z in gate_hinges:
        block(part, "rust_iron", V(half, -0.019, z - 0.055), V(gate_pivot + 0.016, 0.019, z + 0.04))
    return b


def crossing_sign():
    b = rk.Build("rail_crossing_sign", 265)
    rng = b.rng
    post = b.part("post", 40.0)
    plate = b.part("plate", 40.0)
    plants = b.part("plants", 70.0)
    width, height = sign_plate
    emit(post, kit.geo_frustum(0.065, 0.065, 0.052, 0.052, sign_post + 0.5), "concrete", Matrix.Translation(V(0.0, 0.0, -0.5)), "box")
    emit(post, kit.geo_frustum(0.052, 0.052, 0.004, 0.004, 0.07), "concrete", Matrix.Translation(V(0.0, 0.0, sign_post)), "box")
    block(post, "dirt_debris", V(-0.16, -0.16, -0.12), V(0.16, 0.16, 0.012), 0.03)
    face = -0.0545
    back = face - 0.004
    front = back - 0.014
    rk.atlas_panel(plate, "cast_beware", V(0.0, front - 0.0005, sign_center), -Y, Z, width, height, 0, "rail_plates")
    block(plate, "loco_black", V(-width * 0.5, front, sign_center - height * 0.5), V(width * 0.5, back, sign_center + height * 0.5), 0.0, "box", None, ("front",))
    for dz in (-0.17, 0.0, 0.17):
        block(plate, "rust_iron", V(-width * 0.5 + 0.03, back, sign_center + dz - 0.012), V(width * 0.5 - 0.03, face + 0.01, sign_center + dz + 0.012), 0.002)
    for dz in (0.205, -0.21):
        bolt = V(0.0, front - 0.0005, sign_center + dz)
        rk.prism_bolt(plate, "rust_iron", bolt, -Y, 0.022, 0.007, 6)
        rk.prism_bolt(plate, "rust_iron", V(0.0, -face - 0.001, sign_center + dz), Y, 0.03, 0.012, 6, 0.045)
        rk.pipe(plate, "rust_iron", [V(0.0, -face - 0.004, sign_center + dz), V(0.0, -face + 0.03, sign_center + dz)], 0.007, 6)
    for index in range(9):
        angle = rng.uniform(0.0, tau)
        kit.grass_tuft(plants, V(math.cos(angle) * rng.uniform(0.12, 0.4), math.sin(angle) * rng.uniform(0.12, 0.4), 0.0), rng, (0.15, 0.5), (5, 12), 0.06)
    b.col("concrete", "post", V(-0.065, -0.065, 0.0), V(0.065, 0.065, sign_post + 0.07))
    b.col("metal", "plate", V(-width * 0.5, front, sign_center - height * 0.5), V(width * 0.5, -0.0545, sign_center + height * 0.5))
    return b


def crossing_sign_far():
    b = rk.Build("rail_crossing_sign_far", 266)
    part = b.part("sign", 40.0)
    width, height = sign_plate
    block(part, "concrete", V(-0.06, -0.06, -0.2), V(0.06, 0.06, sign_post + 0.05), 0.0, "box", None, ("bottom",))
    front = -0.0545 - 0.018
    rk.atlas_panel(part, "cast_beware", V(0.0, front - 0.0005, sign_center), -Y, Z, width, height, 0, "rail_plates")
    block(part, "loco_black", V(-width * 0.5, front, sign_center - height * 0.5), V(width * 0.5, -0.0545, sign_center + height * 0.5), 0.0, "box", None, ("front",))
    return b


tower_half = 1.3
tower_top = 3.45
tank_half = 1.5
tank_height = 1.45


def water_tower():
    b = rk.Build("rail_water_tower", 251)
    rng = b.rng
    shell = b.part("shell", 30.0)
    tank = b.part("tank", 40.0, 50)
    detail = b.part("detail", 40.0)
    joinery = b.part("joinery", 30.0)
    plants = b.part("plants", 70.0)
    half = tower_half
    wall_t = 0.45
    top = tower_top
    door = (-0.45, 0.45, 0.0, 2.0)
    slit = (-0.2, 0.2, 1.5, 2.3)
    frames = {name: kit.facade(name, half, half) for name in ("front", "back", "left", "right")}
    kit.wall(shell, "granite_rubble", frames["front"], kit.rect(-half, half, plinth, top - 0.15), [kit.rect(*slit)], wall_t)
    kit.wall(shell, "granite_rubble", frames["back"], kit.rect(-half, half, plinth, top - 0.15), [kit.rect(door[0], door[1], -0.05, door[3])], wall_t)
    for name in ("left", "right"):
        kit.wall(shell, "granite_rubble", frames[name], kit.rect(-half, half, plinth, top - 0.15), [], wall_t)
    for corner, ua, ub in ((V(-half, -half, 0.0), X, Y), (V(half, -half, 0.0), -X, Y), (V(half, half, 0.0), -X, -Y), (V(-half, half, 0.0), X, -Y)):
        kit.quoins(shell, "granite_ashlar", corner, ua, ub, -0.2, top - 0.17, rng)
    for name, frame in frames.items():
        a = -half - 0.06
        while a < half + 0.05:
            width = min(rng.uniform(0.5, 0.85), half + 0.06 - a)
            if half + 0.06 - (a + width) < 0.3:
                width = half + 0.06 - a
            frame_block(shell, "granite_ashlar", frame, a + 0.006, a + width - 0.006, top - 0.16, top, -0.07, 0.3, 0.015)
            a += width
        bd.damp_band(shell, frame, -half, half, rng, 0.3, 1.0, "granite_rubble_damp", -0.3, 0.003, [(door[0] - 0.02, door[1] + 0.02)] if name == "back" else ())
    kit.lintel_stone(shell, "granite_ashlar", frames["back"], door[0], door[1], door[3], 0.3, 0.32, 0.025, 0.14)
    kit.jamb_stones(shell, "granite_ashlar", frames["back"], door[0], -1.0, 0.0, door[3], rng)
    kit.jamb_stones(shell, "granite_ashlar", frames["back"], door[1], 1.0, 0.0, door[3], rng)
    kit.door_frame(joinery, "painted_wood_green", frames["back"], door[0] + 0.02, door[1] - 0.02, 0.0, door[3], 0.16)
    kit.door_leaf(joinery, "painted_wood_green", frames["back"], door[1] - 0.09, -1.0, 0.27, 0.02, 1.92, 0.72, 3.0, rng)
    kit.lintel_stone(shell, "granite_ashlar", frames["front"], slit[0], slit[1], slit[3], 0.22, 0.3, 0.02, 0.12)
    kit.sill_stone(shell, "granite_ashlar", frames["front"], slit[0], slit[1], slit[2], 0.18, 0.06, 0.09, 0.07)
    for a in (-0.07, 0.07):
        frame_block(joinery, "rust_iron", frames["front"], a - 0.01, a + 0.01, slit[2], slit[3], 0.1, 0.12)
    frame_block(joinery, "soot", frames["front"], slit[0], slit[1], slit[2], slit[3], wall_t - 0.02, wall_t)
    block(shell, "concrete", V(-half + wall_t, -half + wall_t, top - 0.3), V(half - wall_t, half - wall_t, top - 0.15))
    base = top
    lid = base + tank_height
    for beam in (-1.0, -0.34, 0.34, 1.0):
        block(tank, "loco_black", V(-tank_half, beam * 1.15 - 0.06, base), V(tank_half, beam * 1.15 + 0.06, base + 0.16), 0.006)
    floor = base + 0.16
    panels = 3
    courses = 2
    for name in ("front", "back", "left", "right"):
        frame = kit.facade(name, tank_half, tank_half)
        normal = frame[3]
        rk.zoned(tank, kit.geo_slab(frame[0], frame[1], frame[2], frame[3], kit.rect(-tank_half, tank_half, floor, lid), [], -0.02, 0.0), "wagon_grey", floor, None, False, rng.random())
        emit(tank, kit.geo_slab(frame[0], frame[1], frame[2], frame[3], kit.rect(-tank_half + 0.02, tank_half - 0.02, floor, lid), [], -0.03, -0.02, False), "rust_iron", None, "world", False)
        for index in range(panels + 1):
            a = -tank_half + 2.0 * tank_half * index / panels
            rk.frame_zoned(tank, "wagon_grey", frame, max(a - 0.035, -tank_half), min(a + 0.035, tank_half), floor, lid, -0.035, 0.0, floor, 0.37)
            rk.rivets(detail, "rust_iron", kit.frame_point(frame, min(max(a, -tank_half + 0.02), tank_half - 0.02), floor + 0.07, 0.035), kit.frame_point(frame, min(max(a, -tank_half + 0.02), tank_half - 0.02), lid - 0.07, 0.035), 0.13, normal, 0.012)
        for index in range(courses + 1):
            z = floor + (lid - floor) * index / courses
            rk.frame_zoned(tank, "wagon_grey", frame, -tank_half, tank_half, max(z - 0.035, floor), min(z + 0.035, lid), -0.04, 0.0, floor, 0.59)
            rk.rivets(detail, "rust_iron", kit.frame_point(frame, -tank_half + 0.1, min(max(z, floor + 0.02), lid - 0.02), 0.04), kit.frame_point(frame, tank_half - 0.1, min(max(z, floor + 0.02), lid - 0.02), 0.04), 0.13, normal, 0.012)
        for column in range(panels):
            for row in range(courses):
                a0 = -tank_half + 2.0 * tank_half * column / panels + 0.05
                a1 = -tank_half + 2.0 * tank_half * (column + 1) / panels - 0.05
                z0 = floor + (lid - floor) * row / courses + 0.05
                z1 = floor + (lid - floor) * (row + 1) / courses - 0.05
                for p, q in (((a0, z0), (a1, z1)), ((a0, z1), (a1, z0))):
                    rk.bar(tank, "wagon_grey", [kit.frame_point(frame, p[0], p[1], 0.008), kit.frame_point(frame, q[0], q[1], 0.008)], 0.035, 0.016, normal)
    rk.slab(tank, V(-tank_half, -tank_half, floor - 0.02), V(tank_half, tank_half, floor), "rust_iron", "loco_black")
    water = kit.Geo([V(-tank_half + 0.03, -tank_half + 0.03, lid - 0.3), V(tank_half - 0.03, -tank_half + 0.03, lid - 0.3), V(tank_half - 0.03, tank_half - 0.03, lid - 0.3), V(-tank_half + 0.03, tank_half - 0.03, lid - 0.3)], [(0, 1, 2, 3)])
    emit(tank, water, "glass_dirty", None, "box", False)
    for offset in (-0.5, 0.5):
        rk.pipe(detail, "rust_iron", [V(-tank_half + 0.03, offset, lid - 0.12), V(tank_half - 0.03, offset, lid - 0.12)], 0.014, 6)
        rk.pipe(detail, "rust_iron", [V(offset, -tank_half + 0.03, lid - 0.16), V(offset, tank_half - 0.03, lid - 0.16)], 0.014, 6)
    front = -tank_half
    pivot = V(-0.6, front - 0.28, base + 0.75)
    rk.pipe(tank, "loco_black", [V(-0.6, front + 0.3, floor - 0.1), V(-0.6, front - 0.28, floor - 0.1), pivot], 0.085, 12, 0.14)
    rk.lathe(detail, "rust_iron", pivot - V(0.0, 0.0, 0.2), Z, [(0.1, 0.0), (0.13, 0.0), (0.13, 0.04), (0.1, 0.04)], 14, False)
    rk.lathe(detail, "rust_iron", pivot + V(0.0, 0.0, 0.02), Z, [(0.0, 0.0), (0.13, 0.0), (0.13, 0.05), (0.1, 0.1), (0.05, 0.13), (0.0, 0.14)], 14)
    arm_end = pivot + V(2.7, -0.12, 0.12)
    rk.pipe(tank, "loco_black", [pivot, pivot + V(0.3, -0.01, 0.0), arm_end, arm_end + V(0.12, 0.0, -0.22)], 0.075, 12, 0.12)
    for t in (0.35, 0.7):
        joint = pivot.lerp(arm_end, t)
        rk.lathe(detail, "rust_iron", joint - X * 0.02, X, [(0.078, 0.0), (0.105, 0.0), (0.105, 0.04), (0.078, 0.04)], 12, False)
    king = pivot + V(0.0, 0.0, 1.0)
    rk.pipe(detail, "loco_black", [pivot + V(0.0, 0.0, 0.14), king], 0.03, 8)
    rk.pipe(detail, "rust_iron", [king, pivot.lerp(arm_end, 0.85) + V(0.0, 0.0, 0.08)], 0.012, 6)
    bag = arm_end + V(0.12, 0.0, -0.22)
    path = [bag, bag + V(0.0, 0.0, -0.4), bag + V(0.03, 0.02, -0.8), bag + V(0.1, 0.06, -1.15), bag + V(0.2, 0.08, -1.4)]
    emit(tank, kit.geo_tube(path, kit.circle(0.085, 12), False, X, [1.0, 1.05, 0.95, 0.85, 0.8]), "fabric_worn", None, "given", True)
    rk.lathe(detail, "rust_iron", bag - V(0.0, 0.0, 0.02), Z, [(0.088, 0.0), (0.1, 0.0), (0.1, 0.05), (0.088, 0.05)], 12, False)
    rk.chain(detail, "rust_iron", [pivot + V(0.5, -0.06, -0.06), pivot + V(0.52, -0.08, -1.9)], 0.06, 0.028, 0.006, rng, 5, 3)
    emit(detail, kit.geo_tube([pivot + V(0.52, -0.08, -1.92) + V(math.cos(tau * s / 12.0) * 0.07, 0.0, math.sin(tau * s / 12.0) * 0.07 - 0.07) for s in range(13)], kit.circle(0.008, 5), False, Y), "rust_iron", None, "given", True)
    wheel = V(-0.6, front - 0.1, floor - 0.1)
    rk.pipe(detail, "rust_iron", [wheel, wheel + V(-0.3, 0.0, 0.0)], 0.014, 6)
    ring = [wheel + V(-0.3, math.cos(tau * s / 16.0) * 0.15, math.sin(tau * s / 16.0) * 0.15) for s in range(17)]
    emit(detail, kit.geo_tube(ring, kit.circle(0.012, 6), False, X), "rust_iron", None, "given", True)
    for s in range(4):
        angle = tau * s / 4.0 + 0.3
        rk.pipe(detail, "rust_iron", [wheel + V(-0.3, 0.0, 0.0), wheel + V(-0.3, math.cos(angle) * 0.15, math.sin(angle) * 0.15)], 0.008, 5)
    board = kit.facade("front", tank_half, tank_half)
    frame_block(detail, "painted_wood_white", board, 0.72, 0.9, floor + 0.12, lid - 0.1, -0.045, -0.025, 0.003, "board")
    for index in range(6):
        z = floor + 0.2 + index * 0.2
        frame_block(detail, "soot", board, 0.73, 0.82, z - 0.006, z + 0.006, -0.047, -0.045)
    rk.swatch(detail, kit.geo_box(0.2, 0.012, 0.05), "red", Matrix.Translation(V(0.83, front - 0.053, floor + 0.78)), False)
    rk.pipe(detail, "rust_iron", [V(0.83, front - 0.05, floor + 0.8), V(0.83, front - 0.05, lid + 0.12), V(0.83, front + 0.12, lid + 0.12)], 0.004, 5)
    rk.lathe(detail, "rust_iron", V(0.8, front - 0.05, lid + 0.12), X, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.02), (0.0, 0.02)], 12)
    overflow = V(1.1, tank_half, lid - 0.18)
    rk.pipe(detail, "rust_iron", [overflow - Y * 0.05, overflow + Y * 0.16, overflow + V(0.0, 0.16, -1.3), overflow + V(0.0, 0.0, -tank_height - 0.2), overflow + V(0.0, 0.0, -tank_height - 3.2)], 0.04, 10, 0.08)
    for side in (-1.0, 1.0):
        rk.bar(detail, "loco_black", [V(-half - 0.34, side * 0.19 - 0.6, 0.0), V(-tank_half - 0.12, side * 0.19 - 0.6, lid + 0.45)], 0.045, 0.012, Y)
    rung = 0.3
    while rung < lid + 0.3:
        x = -half - 0.34 + (half + 0.34 - tank_half - 0.12) * rung / (lid + 0.45)
        rk.pipe(detail, "loco_black", [V(x, -0.79, rung), V(x, -0.41, rung)], 0.009, 6)
        rung += 0.29
    for z in (1.6, 3.0, lid - 0.1):
        x = -half - 0.34 + (half + 0.34 - tank_half - 0.12) * z / (lid + 0.45)
        for side in (-1.0, 1.0):
            rk.bar(detail, "loco_black", [V(x, side * 0.19 - 0.6, z), V(-half if z < top else -tank_half, side * 0.19 - 0.6, z)], 0.03, 0.008, Z)
    bd.base_weeds(plants, -half, half, -half, half, rng, 1.2, lambda p: p.y > half - 0.1 and abs(p.x) < 0.6, 0.15, 0.25, 0.0)
    kit.ivy(plants, V(half + 0.02, 0.5, 0.0), X, rng, 2.8, 0.7, 5, 26.0)
    kit.ivy(plants, V(-0.9, -half - 0.02, 0.0), -Y, rng, 1.6, 0.5, 3, 22.0)
    b.col("rock", "base", V(-half, -half, plinth), V(half, half, top))
    b.col("metal", "tank", V(-tank_half, -tank_half, top), V(tank_half, tank_half, lid))
    return b


def water_tower_far():
    b = rk.Build("rail_water_tower_far", 252)
    part = b.part("tower", 30.0)
    half = tower_half
    for name in ("front", "back", "left", "right"):
        kit.wall(part, "granite_rubble", kit.facade(name, half, half), kit.rect(-half, half, plinth, tower_top), [], 0.1)
        frame = kit.facade(name, tank_half, tank_half)
        rk.zoned(part, kit.geo_slab(frame[0], frame[1], frame[2], frame[3], kit.rect(-tank_half, tank_half, tower_top, tower_top + tank_height), [], -0.02, 0.0, False), "wagon_grey", tower_top, None, False, 0.3)
    top = tower_top + tank_height - 0.3
    emit(part, kit.Geo([V(-tank_half, -tank_half, top), V(tank_half, -tank_half, top), V(tank_half, tank_half, top), V(-tank_half, tank_half, top)], [(0, 1, 2, 3)]), "glass_dirty", None, "box", False)
    emit(part, kit.Geo([V(-tank_half, -tank_half, tower_top), V(-tank_half, tank_half, tower_top), V(tank_half, tank_half, tower_top), V(tank_half, -tank_half, tower_top)], [(0, 1, 2, 3)]), "rust_iron", None, "box", False)
    rk.pipe(part, "loco_black", [V(-0.6, -tank_half - 0.28, tower_top + 0.75), V(2.1, -tank_half - 0.4, tower_top + 0.87)], 0.075, 6)
    return b


def stove(b, part, position, flue, name="rusty_metal", light=False):
    profile = [(0.0, 0.12), (0.17, 0.12), (0.19, 0.16), (0.2, 0.42), (0.23, 0.5), (0.2, 0.58), (0.17, 0.78), (0.19, 0.8), (0.19, 0.83), (0.0, 0.83)]
    emit(part, kit.geo_lathe(profile, 18), name, Matrix.Translation(position), "given", True)
    for index in range(3):
        angle = tau * index / 3.0 + 0.5
        rk.pipe(part, name, [position + V(math.cos(angle) * 0.14, math.sin(angle) * 0.14, 0.13), position + V(math.cos(angle) * 0.2, math.sin(angle) * 0.2, 0.0)], 0.016, 6)
    local_block(part, name, Matrix.Translation(position), -0.09, 0.09, -0.225, -0.19, 0.24, 0.42, 0.006)
    local_block(part, "soot", Matrix.Translation(position), -0.06, 0.06, -0.23, -0.224, 0.27, 0.39)
    rk.pipe(part, name, [position + V(0.0, 0.0, 0.83)] + list(flue), 0.06, 12, 0.12)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.24, 0.0), (0.24, 0.012), (0.0, 0.012)], 16), name, Matrix.Translation(position), "given", True)
    b.col("metal", "stove", position + V(-0.22, -0.22, 0.0), position + V(0.22, 0.22, 0.85))
    if light:
        b.light("fire", position + V(0.0, -0.3, 0.33))


lever_colours = ("yellow", "red", "red", "black", "blue", "black", "leather", "white")


def lever_frame(part, detail, origin, rng, colours=lever_colours, pulled=(2, 5)):
    count = len(colours)
    width = count * 0.14 + 0.24
    block(part, "loco_black", origin + V(-width * 0.5, -0.2, 0.0), origin + V(width * 0.5, 0.24, 0.045), 0.006)
    block(part, "loco_black", origin + V(-width * 0.5, -0.2, 0.045), origin + V(-width * 0.5 + 0.04, 0.24, 0.24), 0.004)
    block(part, "loco_black", origin + V(width * 0.5 - 0.04, -0.2, 0.045), origin + V(width * 0.5, 0.24, 0.24), 0.004)
    for index, colour in enumerate(colours):
        x = origin.x - (count - 1) * 0.07 + index * 0.14
        lean = math.radians(-13.0 if index in pulled else 11.0)
        base = V(x, origin.y, origin.z + 0.03)
        direction = V(0.0, -math.sin(lean), math.cos(lean))
        lower = base + direction * 0.74
        top = base + direction * 1.16
        rk.swatch(detail, kit.geo_tube([base, lower], rk.square_profile(0.034, 0.016), True, X), colour, None, False)
        rk.swatch(detail, kit.geo_tube([lower, top], kit.circle(0.013, 8), True), "steel", None, True)
        catch = lower + direction * 0.06 + Y * 0.035
        rk.swatch(detail, kit.geo_tube([catch, catch + direction * 0.3, catch + direction * 0.33 - Y * 0.03], kit.circle(0.007, 6), True), "steel", None, True)
        rk.swatch(detail, kit.geo_box(0.05, 0.004, 0.03), "brass", Matrix.Translation(base + direction * 0.5 - Y * 0.012), False)
        for y0, y1 in ((-0.19, -0.02), (0.02, 0.23)):
            block(detail, "rust_iron", V(x - 0.045, origin.y + y0, origin.z + 0.045), V(x - 0.03, origin.y + y1, origin.z + 0.06 + 0.04 * (1.0 - abs(y0 + y1) * 2.0)))
    return width


def block_instrument(part, detail, position, index):
    local_block(part, "timber_beam", Matrix.Translation(position), -0.13, 0.13, -0.09, 0.09, 0.0, 0.3, 0.008)
    rk.atlas_disc(detail, "gauge_%d" % (index % 6), position + V(0.0, 0.092, 0.17), Y, Z, 0.085, 16, "rail_signs", 0.95)
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.015), (0.035, 0.05), (0.0, 0.06)], 12), "brass", Matrix.Translation(position + V(0.0, 0.0, 0.3)))
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.012, 0.0), (0.012, 0.03), (0.02, 0.04), (0.0, 0.045)], 8), "brass", rk.frame_along(position + V(0.0, 0.09, 0.05), Y))


box_hx = 2.0
box_hy = 1.5
box_floor = 2.325
box_base = 2.18
box_eaves = 4.62
box_sill = 3.2
box_head = 4.4


def box_gable():
    pitch = 35.0
    overhang = 0.35
    eave = box_eaves - overhang * math.tan(math.radians(pitch)) + 0.04 / math.cos(math.radians(pitch))
    return kit.Gable(-box_hx - 0.3, box_hx + 0.3, box_hy, overhang, eave, pitch)


def signal_box():
    b = rk.Build("rail_signal_box", 261)
    rng = b.rng
    shell = b.part("shell", 30.0)
    cabin = b.part("cabin", 30.0)
    roof = b.part("roof", 50.0)
    joinery = b.part("joinery", 30.0)
    floors = b.part("floors", 30.0)
    interior = b.part("interior", 40.0)
    detail = b.part("detail", 40.0)
    clutter = b.part("clutter", 45.0)
    plants = b.part("plants", 70.0)
    hx = box_hx
    hy = box_hy
    wall_t = 0.3
    ix = hx - wall_t
    iy = hy - wall_t
    skin = 0.12
    white = "painted_wood_white"
    green = "painted_wood_green"
    gable = box_gable()
    front = kit.facade("front", hx, hy)
    back = kit.facade("back", hx, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    low_door = (-1.55, -0.6, 0.0, 2.05)
    low_windows = [(-1.25, -0.65, 1.05, 1.75), (0.65, 1.25, 1.05, 1.75)]
    kit.wall(shell, "brick_red", front, kit.rect(-hx, hx, plinth, box_base), [kit.rect(*w) for w in low_windows], wall_t)
    kit.wall(shell, "brick_red", back, kit.rect(-hx, hx, plinth, box_base), [kit.rect(low_door[0], low_door[1], -0.05, low_door[3])], wall_t)
    kit.wall(shell, "brick_red", left, kit.rect(-hy, hy, plinth, box_base), [], wall_t)
    kit.wall(shell, "brick_red", right, kit.rect(-hy, hy, plinth, box_base), [], wall_t)
    kit.wall_boxes(b, "rock", "base_front", front, -hx, hx, plinth, box_base, wall_t, low_windows)
    kit.wall_boxes(b, "rock", "base_back", back, -hx, hx, plinth, box_base, wall_t, [low_door])
    kit.wall_boxes(b, "rock", "base_left", left, -hy, hy, plinth, box_base, wall_t, [])
    kit.wall_boxes(b, "rock", "base_right", right, -hy, hy, plinth, box_base, wall_t, [])
    for frame, a_high in ((front, hx), (back, hx), (left, hy), (right, hy)):
        spans = ((-a_high - 0.03, low_door[0] - 0.02), (low_door[1] + 0.02, a_high + 0.03)) if frame is back else ((-a_high - 0.03, a_high + 0.03),)
        for a0, a1 in spans:
            frame_block(shell, "granite_ashlar", frame, a0, a1, -0.35, 0.14, -0.035, 0.1, 0.012)
    for w in low_windows:
        kit.lintel_stone(shell, "granite_ashlar", front, w[0], w[1], w[3], 0.2, 0.28, 0.02, 0.12)
        kit.sill_stone(shell, "granite_ashlar", front, w[0], w[1], w[2], 0.16, 0.06, 0.08, 0.06)
        kit.casement_window(joinery, green, front, w[0], w[1], w[2], w[3], 0.1, rng, [0.0], 0.5, 0.3, 2)
        for a in (w[0] + 0.15, (w[0] + w[1]) * 0.5, w[1] - 0.15):
            frame_block(joinery, "rust_iron", front, a - 0.01, a + 0.01, w[2], w[3], 0.03, 0.05)
    kit.lintel_stone(shell, "granite_ashlar", back, low_door[0], low_door[1], low_door[3], 0.22, 0.28, 0.02, 0.12)
    kit.door_frame(joinery, green, back, low_door[0] + 0.01, low_door[1] - 0.01, 0.0, low_door[3], 0.1)
    kit.door_leaf(joinery, green, back, low_door[1] - 0.08, -1.0, 0.1, 0.02, 1.96, 0.79, -88.0, rng, "ledged", 3.0)
    block(floors, "concrete", V(-ix, -iy, -0.2), V(ix, iy, 0.0))
    b.col("rock", "floor", V(-ix, -iy, -0.3), V(ix, iy, 0.0))
    kit.joists(floors, "timber_beam", -ix, ix, -hy + 0.1, hy - 0.1, box_floor - 0.025, "y", 0.4, 0.07, 0.12)
    kit.floor_boards(floors, "floorboards", -hx + skin, hx - skin, -hy + skin, hy - skin, box_floor, "x", rng, 0.025, 0.004, None, (0.12, 0.17), 0.02, [-0.7, 0.9])
    b.col("wood", "upper_floor", V(-hx, -hy, box_base), V(hx, hy, box_floor))
    units = 5
    span = 2.0 * (hx - 0.2) / units
    front_windows = [(-hx + 0.2 + span * index, -hx + 0.2 + span * (index + 1), box_sill, box_head) for index in range(units)]
    left_windows = [(0.2, 1.15, box_sill, box_head)]
    left_door = (-1.4, -0.4, box_floor, box_floor + 2.08)
    right_windows = [(-1.25, -0.08, box_sill, box_head), (0.08, 1.25, box_sill, box_head)]
    back_windows = [(-0.45, 0.45, 3.35, 4.25)]
    apex = lambda a: gable.under(a, 0.05)
    walls = ((front, hx, front_windows, None, None), (back, hx, back_windows, None, None), (left, hy, left_windows, left_door, apex), (right, hy, right_windows, None, apex))
    for frame, a_high, windows, door, crest in walls:
        holes = [tuple(w) for w in windows] + ([door] if door else [])
        wall_top = box_eaves
        rk.plank_wall(cabin, white, frame, -a_high + 0.1, a_high - 0.1, box_base + 0.1, wall_top, 0.0, 0.025, 0.14, holes, 0.003, False)
        rk.plank_wall(interior, green, frame, -a_high + skin, a_high - skin, box_floor, box_sill - 0.06, skin - 0.02, skin, 0.11, holes, 0.003, True)
        rk.plank_wall(interior, white, frame, -a_high + skin, a_high - skin, box_sill - 0.06, wall_top, skin - 0.02, skin, 0.11, holes, 0.003, True)
        if crest is not None:
            rk.plank_wall(cabin, white, frame, -a_high + 0.02, a_high - 0.02, wall_top, gable.ridge_top, 0.0, 0.025, 0.14, (), 0.003, True, crest)
            rk.plank_wall(interior, white, frame, -a_high + skin, a_high - skin, wall_top, gable.ridge_top, skin - 0.02, skin, 0.11, (), 0.003, True, lambda a: gable.under(a, 0.12))
            for side in (-1.0, 1.0):
                x = frame[0].x + frame[3].x * 0.016
                kit.segmented(cabin, green, gable.point(side, x, gable.distance(hy) - 0.1, -0.11), gable.point(side, x, gable.run, -0.11), 0.03, 0.17, gable.normal(side), 1.0)
        for a0, a1 in ((-a_high, -a_high + 0.1), (a_high - 0.1, a_high)):
            frame_block(cabin, green, frame, a0, a1, box_base, wall_top, -0.012, skin, 0.004, "board")
        frame_block(cabin, green, frame, -a_high + 0.1, a_high - 0.1, box_base, box_base + 0.1, -0.012, skin, 0.004, "board")
        for w in windows:
            frame_block(cabin, green, frame, w[0] - 0.04, w[1] + 0.04, w[2] - 0.06, w[2], -0.03, skin + 0.04, 0.004, "board")
            kit.sash_window(joinery, white, frame, w[0], w[1], w[2], w[3], 0.02, rng, 0.0, 0.5, 0.25, 2, 2)
        if door:
            kit.door_frame(joinery, green, frame, door[0], door[1], door[2], door[3], 0.0, 0.06, skin)
            kit.door_leaf(joinery, green, frame, door[0] + 0.06, 1.0, 0.06, door[2] + 0.01, 1.99, 0.86, 84.0, rng, "panel")
        openings = [door] if door else []
        kit.wall_boxes(b, "wood", "cabin", frame, -a_high, a_high, box_base, box_eaves, skin, openings)
    rk.atlas_panel(detail, "signal_box", V(0.0, -hy - 0.03, box_base + 0.6), -Y, Z, 1.7, 0.38)
    frame_block(cabin, green, front, -0.9, 0.9, box_base + 0.38, box_base + 0.82, -0.028, 0.0, 0.004, "board")
    moss = kit.smooth_noise(random.Random(9), 5, 1.2)
    for side in (-1.0, 1.0):
        kit.slate_roof(roof, gable, side, rng, lambda x, d: moss(V(x * 0.5, d * 0.7, side)) > 0.45, lambda x, d: rng.random() < 0.008, lambda x, d: rng.uniform(0.05, 0.14) if rng.random() < 0.02 else 0.0)
        kit.roof_boards(roof, gable, side, -hx - 0.3, hx + 0.3, 0.0, gable.run + 0.02, rng, "timber_planks_weathered", 0.022, -0.001)
        kit.roof_rafters(roof, gable, side, [-hx + 0.06 + index * (2.0 * hx - 0.12) / 8 for index in range(9)], 0.0, gable.run - 0.02, -0.023)
        block(roof, "timber_beam", V(-hx + 0.02, side * (hy - skin), box_eaves - 0.1), V(hx - 0.02, side * (hy - 0.01), box_eaves + 0.0), 0.006)
        for end in (-1.0, 1.0):
            kit.segmented(roof, green, gable.point(side, end * (hx + 0.3), 0.0, -0.06), gable.point(side, end * (hx + 0.3), gable.run, -0.06), 0.03, 0.2, gable.normal(side), 1.2)
        gutter_z = kit.gutter(roof, gable, side, -hx - 0.3, hx + 0.3, rng, 0.02)
    kit.downpipe(roof, hx + 0.12, -gable.edge - 0.04, -hy, gutter_z - 0.03, 0.05, rng)
    kit.segmented(roof, "timber_beam", V(-hx, 0.0, gable.ridge_top - 0.2), V(hx, 0.0, gable.ridge_top - 0.2), 0.04, 0.3, Z, 1.0, "box")
    kit.ridge_tiles(roof, gable, -hx - 0.3, hx + 0.3, rng)
    for end in (-1.0, 1.0):
        rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.05), (0.02, 0.1), (0.045, 0.2), (0.015, 0.3), (0.0, 0.45)], 10), "white", Matrix.Translation(V(end * (hx + 0.3), 0.0, gable.ridge_top + 0.05)))
    bd.roof_cols(b, gable, -hx - 0.3, hx + 0.3, 4)
    stair_x = -hx - 0.55
    bd.ladder_stair(b, floors, V(stair_x, -2.2, 0.0), Y, 0.9, box_floor, 2.5, 11, rng, "timber_beam", "timber_planks_weathered", "wood", "stair", "py")
    landing = (V(-hx - 1.02, 0.3, box_floor - 0.14), V(-hx, 1.4, box_floor))
    kit.floor_boards(floors, "timber_planks_weathered", landing[0].x, landing[1].x, landing[0].y, landing[1].y, box_floor, "y", rng, 0.035, 0.006, None, (0.14, 0.19), 0.02)
    for y in (landing[0].y + 0.05, landing[1].y - 0.05):
        block(floors, "timber_beam", V(landing[0].x, y - 0.04, box_floor - 0.16), V(landing[1].x, y + 0.04, box_floor - 0.035), 0.006)
    for x, y in ((landing[0].x + 0.06, landing[0].y + 0.06), (landing[0].x + 0.06, landing[1].y - 0.06)):
        block(floors, "timber_beam", V(x - 0.06, y - 0.06, -0.3), V(x + 0.06, y + 0.06, box_floor - 0.16), 0.008)
        b.col("wood", "stair_post", V(x - 0.06, y - 0.06, 0.0), V(x + 0.06, y + 0.06, box_floor - 0.16))
    b.col("wood", "landing", landing[0], landing[1])
    outer = landing[0].x + 0.04
    bd.balustrade(b, floors, V(outer, -2.2, 0.06), V(outer, 0.3, box_floor), rng, 0.95, 0.14, "timber_beam", white, 0.12, (True, False), False)
    bd.balustrade(b, floors, V(outer, 0.3, box_floor), V(outer, landing[1].y - 0.04, box_floor), rng, 0.95, 0.14, "timber_beam", white, 0.1, (True, True), False)
    bd.balustrade(b, floors, V(outer, landing[1].y - 0.04, box_floor), V(landing[1].x - 0.05, landing[1].y - 0.04, box_floor), rng, 0.95, 0.14, "timber_beam", white, 0.1, (False, False), False)
    origin = V(0.0, -hy + skin + 0.62, box_floor)
    lever_frame(interior, detail, origin, rng)
    b.col("metal", "levers", origin + V(-0.68, -0.2, 0.0), origin + V(0.68, 0.24, 0.95))
    shelf_y = -hy + skin + 0.3
    block(interior, "timber_beam", V(-1.3, shelf_y - 0.13, box_floor + 1.72), V(1.3, shelf_y + 0.13, box_floor + 1.755), 0.006)
    for x in (-1.2, 0.0, 1.2):
        rk.pipe(detail, "rust_iron", [V(x, shelf_y, box_floor + 1.755), V(x, shelf_y, gable.under(shelf_y, 0.2))], 0.009, 6)
    for index, x in enumerate((-0.85, -0.2, 0.75)):
        block_instrument(interior, detail, V(x, shelf_y, box_floor + 1.755), index + 1)
    bd.table(interior, 0.55, hy - skin - 0.36, box_floor, 1.1, 0.6, 0.78, rng)
    b.col("wood", "desk", V(0.0, hy - skin - 0.66, box_floor), V(1.1, hy - skin - 0.06, box_floor + 0.78))
    rk.swatch(clutter, kit.geo_cbox(0.4, 0.3, 0.03, 0.004), "cream", Matrix.Translation(V(0.45, hy - skin - 0.36, box_floor + 0.795)) @ Matrix.Rotation(0.1, 4, 'Z'), False)
    rk.atlas_panel(clutter, "timetable", V(0.45, hy - skin - 0.36, box_floor + 0.812), Z, V(-math.sin(0.1), math.cos(0.1), 0.0), 0.26, 0.36)
    bd.oil_lamp(clutter, V(0.95, hy - skin - 0.25, box_floor + 0.78), rng)
    b.light("warm", V(0.95, hy - skin - 0.25, box_floor + 1.05))
    bd.chair(interior, V(0.5, hy - skin - 0.95, box_floor), math.pi + 0.3, rng)
    stove_at = V(1.5, hy - skin - 0.42, box_floor)
    stove(b, interior, stove_at, [stove_at + V(0.0, 0.0, 1.6), stove_at + V(0.0, 0.0, gable.top(stove_at.y) - box_floor + 0.75)])
    block(interior, "granite_ashlar", stove_at + V(-0.33, -0.35, 0.0), stove_at + V(0.33, 0.35, 0.03), 0.008)
    rk.lathe(roof, "rusty_metal", V(stove_at.x, stove_at.y, gable.top(stove_at.y) + 0.72), Z, [(0.062, 0.0), (0.12, 0.05), (0.12, 0.07), (0.0, 0.14)], 12)
    bd.bucket(clutter, stove_at + V(-0.05, -0.5, 0.0), rng)
    bd.kettle(clutter, stove_at + V(0.0, 0.0, 0.83), rng)
    clock = V(-1.2, hy - skin - 0.004, box_floor + 1.7)
    rk.atlas_disc(detail, "clock", clock, -Y, Z, 0.2, 24, "rail_signs", 0.94)
    emit(detail, kit.geo_lathe([(0.2, 0.0), (0.235, 0.0), (0.235, 0.05), (0.21, 0.06), (0.2, 0.045), (0.2, 0.0)], 24), "timber_beam", rk.frame_along(clock + V(0.0, 0.003, 0.0), -Y), "given", True)
    rk.atlas_panel(detail, "notice", V(-0.72, hy - skin - 0.004, box_floor + 1.45), -Y, Z, 0.3, 0.37)
    bd.armchair(b, interior, V(1.3, -0.25, box_floor), -1.9, rng)
    b.loot("toolbox", V(-1.2, -0.4, box_floor))
    b.loot("box", V(1.2, 0.6, box_floor))
    hook = V(0.0, 0.2, gable.under(0.2, 0.2))
    rod(clutter, "rusty_metal", hook, hook - V(0.0, 0.0, 0.9), 0.004, 4)
    bd.lantern(clutter, hook - V(0.0, 0.0, 1.2), rng)
    b.light("warm", hook - V(0.0, 0.0, 1.0))
    for index in range(8):
        x = -0.49 + index * 0.14
        rod(interior, "rusty_metal", V(x, -hy + skin + 0.62, 0.35), V(x, -hy + skin + 0.62, box_floor - 0.15), 0.014, 6)
        rod(interior, "rusty_metal", V(x, -iy + 0.02, 0.35), V(x, -hy + skin + 0.62, 0.35), 0.012, 6)
    block(interior, "timber_beam", V(-0.7, -hy + skin + 0.5, 0.0), V(0.7, -hy + skin + 0.74, 0.3), 0.01)
    bd.shelf(interior, V(ix, -0.9, 1.4), V(ix, 0.7, 1.4), 0.24, -X, rng)
    for y in (-0.7, -0.2, 0.4):
        bd.lantern(clutter, V(ix - 0.12, y, 1.4), rng)
    lump(clutter, "soot", V(-1.2, 0.5, 0.0), (0.45, 0.5, 0.22), rng, 0.3, 2, 0.0)
    b.col("rock", "coal", V(-1.65, 0.0, 0.0), V(-0.75, 1.0, 0.18))
    bd.long_tool(clutter, V(-1.5, -0.9, 0.0), V(-1.66, -1.1, 1.3), "spade", rng)
    bd.crate(clutter, V(0.9, -0.7, 0.0), (0.6, 0.45, 0.4), 0.2, rng)
    b.loot("box", V(0.9, -0.7, 0.42))
    b.loot("toolbox", V(0.2, 0.7, 0.0))
    bd.base_weeds(plants, -hx, hx, -hy, hy, rng, 1.1, lambda p: (p.y > hy - 0.1 and low_door[0] - 0.2 < -p.x < low_door[1] + 0.2) or p.x < -hx + 0.1, 0.1, 0.2, 0.0)
    kit.ivy(plants, V(hx + 0.02, 0.6, 0.0), X, rng, 2.4, 0.6, 4, 24.0)
    return b


def signal_box_far():
    b = rk.Build("rail_signal_box_far", 262)
    part = b.part("box", 30.0)
    hx = box_hx
    hy = box_hy
    gable = box_gable()
    for name, a_high in (("front", hx), ("back", hx), ("left", hy), ("right", hy)):
        frame = kit.facade(name, hx, hy)
        kit.wall(part, "brick_red", frame, kit.rect(-a_high, a_high, plinth, box_base), [], 0.1)
        outline = kit.rect(-a_high, a_high, box_base, box_eaves)
        if name in ("left", "right"):
            outline = [(-a_high, box_base), (a_high, box_base), (a_high, box_eaves), (0.0, gable.under(0.0, 0.05)), (-a_high, box_eaves)]
        emit(part, kit.geo_slab(frame[0], frame[1], frame[2], frame[3], outline, [], -0.05, 0.0, False), "painted_wood_white", None, "box", False)
    kit.skin(part, "glass_dirty", kit.facade("front", hx, hy), kit.rect(-hx + 0.2, hx - 0.2, box_sill, box_head), [], 0.004, 0.002, False)
    kit.skin(part, "glass_dirty", kit.facade("right", hx, hy), kit.rect(-1.25, 1.25, box_sill, box_head), [], 0.004, 0.002, False)
    for side in (-1.0, 1.0):
        kit.roof_slab(part, gable, side, -hx - 0.3, hx + 0.3, "slate_roof", 0.1)
    points = [V(-hx - 1.0, -2.2, 0.0), V(-hx - 0.1, -2.2, 0.0), V(-hx - 0.1, 0.3, box_floor), V(-hx - 1.0, 0.3, box_floor)]
    emit(part, kit.Geo(points, [(0, 1, 2, 3), (3, 2, 1, 0)]), "timber_planks_weathered", None, "box", False)
    block(part, "timber_planks_weathered", V(-hx - 1.0, 0.3, box_floor - 0.14), V(-hx, 1.4, box_floor), 0.0, "box")
    return b


station_hx = 6.0
station_hy = 2.5
station_wall = 0.45
station_eaves = 3.3
station_pitch = 38.0
station_plinth = -2.4
canopy_depth = 2.6
canopy_half = 5.7
canopy_top = 3.16
canopy_pitch = 7.0


def station_gable():
    overhang = 0.3
    eave = station_eaves - overhang * math.tan(math.radians(station_pitch)) + 0.03 / math.cos(math.radians(station_pitch))
    return kit.Gable(-station_hx + station_wall, station_hx - station_wall, station_hy, overhang, eave, station_pitch)


def station_canopy():
    edge = canopy_depth + 0.1
    return kit.Gable(-canopy_half, canopy_half, canopy_depth, 0.1, canopy_top - edge * math.tan(math.radians(canopy_pitch)), canopy_pitch, -station_hy)


def bench(b, part, start, end, inward, rng, paint="painted_wood_green", frame="timber_beam", collide=True):
    if (end - start).cross(inward).z < 0.0:
        start, end = end, start
    direction = (end - start).normalized()
    length = (end - start).length
    matrix = Matrix((tuple((direction.x, inward.x, 0.0, start.x)), (direction.y, inward.y, 0.0, start.y), (0.0, 0.0, 1.0, start.z), (0.0, 0.0, 0.0, 1.0)))
    for index in range(4):
        y = 0.1 + index * 0.1
        local_block(part, paint, matrix, 0.0, length, y, y + 0.085, 0.42, 0.45, 0.004, "board")
    for index in range(3):
        z = 0.56 + index * 0.13
        local_block(part, paint, matrix, 0.0, length, 0.03 - index * 0.012, 0.055 - index * 0.012, z, z + 0.1, 0.004, "board")
    count = max(2, int(round(length / 1.2)) + 1)
    for index in range(count):
        x = 0.06 + (length - 0.12) * index / (count - 1)
        local_block(part, frame, matrix, x - 0.03, x + 0.03, 0.0, 0.06, 0.0, 0.95, 0.006)
        local_block(part, frame, matrix, x - 0.03, x + 0.03, 0.44, 0.5, 0.0, 0.42, 0.006)
        local_block(part, frame, matrix, x - 0.025, x + 0.025, 0.06, 0.5, 0.36, 0.42, 0.004)
        local_block(part, frame, matrix, x - 0.025, x + 0.025, 0.03, 0.5, 0.62, 0.66, 0.004)
        local_block(part, frame, matrix, x - 0.025, x + 0.025, 0.44, 0.5, 0.42, 0.66, 0.004)
    if collide:
        low, high = kit.box_between(matrix @ V(0.0, 0.0, 0.0), matrix @ V(length, 0.5, 0.0))
        b.col("wood", "bench", V(low.x, low.y, start.z), V(high.x, high.y, start.z + 0.46))


def trolley(b, part, detail, center, yaw, rng):
    matrix = Matrix.Translation(center) @ Matrix.Rotation(yaw, 4, 'Z')
    for index in range(5):
        y = -0.36 + index * 0.145
        local_block(part, "timber_planks_weathered", matrix, -0.75, 0.75, y, y + 0.14, 0.4, 0.435, 0.003, "board")
    for y in (-0.37, 0.33):
        local_block(part, "timber_beam", matrix, -0.78, 0.78, y, y + 0.05, 0.31, 0.4, 0.006)
    for x in (-0.78, 0.72):
        local_block(part, "timber_beam", matrix, x, x + 0.06, -0.37, 0.38, 0.31, 0.4, 0.006)
    for y in (-0.34, 0.34):
        local_block(part, "timber_beam", matrix, 0.72, 0.78, y - 0.025, y + 0.025, 0.4, 1.12, 0.006)
    for z in (0.72, 1.06):
        local_block(part, "timber_beam", matrix, 0.73, 0.77, -0.34, 0.34, z, z + 0.05, 0.004)
    turn = matrix.to_3x3()
    for x, radius in ((-0.5, 0.16), (0.5, 0.16)):
        rk.pipe(detail, "rust_iron", [matrix @ V(x, -0.42, radius), matrix @ V(x, 0.42, radius)], 0.014, 6)
        for y in (-0.42, 0.42):
            rk.lathe(detail, "rust_iron", matrix @ V(x, y - 0.02, radius), turn @ Y, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.012), (radius - 0.025, 0.012), (radius - 0.025, 0.0), (radius, 0.0), (radius, 0.04), (radius - 0.025, 0.04), (radius - 0.025, 0.028), (0.05, 0.028), (0.05, 0.04), (0.0, 0.04)], 16)
        for y in (-0.3, 0.3):
            local_block(detail, "rust_iron", matrix, x - 0.02, x + 0.02, y - 0.006, y + 0.006, radius - 0.02, 0.31)
    rk.pipe(detail, "rust_iron", [matrix @ V(-0.78, 0.0, 0.34), matrix @ V(-1.1, 0.0, 0.3), matrix @ V(-1.75, 0.0, 0.62)], 0.014, 6, 0.06)
    rk.pipe(detail, "rust_iron", [matrix @ V(-1.75, -0.16, 0.62), matrix @ V(-1.75, 0.16, 0.62)], 0.014, 6)
    low, high = kit.box_between(matrix @ V(-0.78, -0.4, 0.0), matrix @ V(0.78, 0.4, 0.0))
    box_low = V(min(low.x, high.x), min(low.y, high.y), center.z)
    b.col("wood", "trolley", box_low, V(max(low.x, high.x), max(low.y, high.y), center.z + 0.44))
    return matrix


def fire_bucket(part, detail, hook):
    rk.pipe(detail, "rust_iron", [hook, hook - Y * 0.08, hook - Y * 0.08 - Z * 0.03], 0.006, 5, 0.015)
    base = hook - Y * 0.17 - Z * 0.36
    rk.swatch(part, kit.geo_lathe([(0.0, 0.0), (0.085, 0.0), (0.105, 0.04), (0.145, 0.3), (0.138, 0.3), (0.1, 0.045), (0.0, 0.012)], 14), "red", Matrix.Translation(base))
    arc = [base + V(-0.14 * math.cos(math.pi * t / 8.0), 0.0, 0.29 + 0.1 * math.sin(math.pi * t / 8.0)) for t in range(9)]
    emit(detail, kit.geo_tube(arc, kit.circle(0.004, 4), True, Y), "rust_iron", None, "given", True)


def safe(b, part, detail, center, yaw):
    matrix = Matrix.Translation(center) @ Matrix.Rotation(yaw, 4, 'Z')
    emit(part, kit.geo_cbox(0.62, 0.58, 0.82, 0.02), "loco_black", matrix @ Matrix.Translation(V(0.0, 0.0, 0.47)), "box")
    local_block(part, "loco_black", matrix, -0.28, 0.28, -0.29, 0.29, 0.0, 0.06)
    local_block(part, "loco_black", matrix, -0.25, 0.25, -0.31, -0.29, 0.14, 0.8, 0.006)
    turn = matrix.to_3x3()
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.015), (0.02, 0.02), (0.02, 0.05), (0.0, 0.055)], 12), "brass", rk.frame_along(matrix @ V(0.12, -0.31, 0.5), turn @ V(0.0, -1.0, 0.0)))
    rk.pipe(detail, "rust_iron", [matrix @ V(0.02, -0.33, 0.44), matrix @ V(-0.1, -0.33, 0.44)], 0.009, 6)
    rk.swatch(detail, kit.geo_box(0.2, 0.004, 0.07), "brass", matrix @ Matrix.Translation(V(0.0, -0.312, 0.68)), False)
    for z in (0.25, 0.7):
        rk.lathe(detail, "rust_iron", matrix @ V(-0.26, -0.32, z - 0.04), Z, [(0.0, 0.0), (0.014, 0.0), (0.014, 0.08), (0.0, 0.08)], 8)
    low, high = kit.box_between(matrix @ V(-0.31, -0.29, 0.0), matrix @ V(0.31, 0.29, 0.0))
    b.col("metal", "safe", V(min(low.x, high.x), min(low.y, high.y), center.z), V(max(low.x, high.x), max(low.y, high.y), center.z + 0.88))


def canopy_bracket(part, detail, x, wall_y, top, reach=2.05, drop=1.25, paint="painted_wood_green"):
    corner = V(x, wall_y, top)
    rk.bar(part, paint, [corner - Z * drop, corner], 0.05, 0.02, X)
    rk.bar(part, paint, [corner, corner - Y * reach], 0.05, 0.02, X)
    arc = [corner + V(0.0, -reach * (1.0 - math.cos(math.pi * 0.5 * t / 10.0)), -drop * (1.0 - math.sin(math.pi * 0.5 * t / 10.0))) for t in range(11)]
    rk.bar(part, paint, arc, 0.045, 0.02, X)
    for radius, along, down in ((0.2, 0.34, 0.3), (0.13, 0.8, 0.22), (0.13, 0.26, 0.72)):
        center = corner + V(0.0, -along, -down)
        ring = [center + V(0.0, math.cos(tau * t / 14.0) * radius, math.sin(tau * t / 14.0) * radius) for t in range(15)]
        emit(detail, kit.geo_tube(ring, rk.square_profile(0.014, 0.02), False, X), paint, None, "given", False)
    for offset in (0.12, drop - 0.12):
        rk.prism_bolt(detail, "rust_iron", corner + V(0.03, 0.0, -offset), X, 0.03, 0.012, 6)


def valance(part, rng, a, b, top, paint="painted_wood_white", width=0.12, depth=0.34, missing=0.06):
    direction = (b - a).normalized()
    normal = direction.cross(Z)
    count = int(round((b - a).length / width))
    pitch = (b - a).length / count
    for index in range(count):
        if rng.random() < missing:
            continue
        drop = depth * (1.0 if index % 2 == 0 else 0.86)
        origin = a + direction * (pitch * (index + 0.5)) + Z * (top + rng.uniform(-0.004, 0.0))
        outline = [(-pitch * 0.5 + 0.003, 0.0), (pitch * 0.5 - 0.003, 0.0), (pitch * 0.5 - 0.003, -drop + 0.07), (0.0, -drop), (-pitch * 0.5 + 0.003, -drop + 0.07)]
        geo = kit.geo_slab(origin, direction, Z, normal, outline, [], -0.011, 0.011)
        geo.uvs = [[((geo.points[i] - origin).dot(Z) + index * 0.37, 0.2 + (geo.points[i] - origin).dot(direction) * 0.8 + (geo.points[i] - origin).dot(normal)) for i in face] for face in geo.faces]
        emit(part, geo, paint, None, "given", False)


step_width = 1.5
step_landing = 1.0
step_risers = 8
step_going = 0.3
step_cheek = 0.35


step_parapet = 0.9
step_foot = 0.55


def step_layout(center_x, wall_y):
    y_land = wall_y + step_landing
    y_end = y_land + step_going * (step_risers - 1)
    return center_x - step_width * 0.5, center_x + step_width * 0.5, y_land, y_end


def parapet_top(y, y_land, y_foot, drop):
    t = max(0.0, min((y - y_land) / (y_foot - y_land), 1.0))
    return step_parapet + (step_foot - drop - step_parapet) * t


def rear_steps(b, shell, floors, plants, rng, center_x, wall_y, drop=platform_top):
    stone = "granite_rubble"
    dressed = "granite_ashlar"
    rise = drop / step_risers
    x0, x1, y_land, y_end = step_layout(center_x, wall_y)
    y_foot = y_end + 0.15
    base = -drop - 0.3
    cap = 0.12
    block(shell, stone, V(x0, wall_y, base), V(x1, y_land, -0.14), 0.0, "world")
    joint = center_x + rng.uniform(-0.2, 0.2)
    for a0, a1 in ((x0, joint), (joint, x1)):
        block(floors, dressed, V(a0 + 0.006, wall_y + 0.01, -0.14), V(a1 - 0.006, y_land - 0.004, -0.02), 0.012)
    for index in range(step_risers - 1):
        top = -rise * (index + 1) - rng.uniform(0.0, 0.008)
        y0 = y_land + step_going * index
        joint = center_x + rng.uniform(-0.45, 0.45)
        for a0, a1 in ((x0, joint), (joint, x1)):
            block(floors, dressed, V(a0 + 0.005, y0 + 0.004, top - rise - 0.03), V(a1 - 0.005, y0 + step_going + 0.02, top), 0.014)
        block(shell, stone, V(x0, y0 + 0.02, base), V(x1, y0 + step_going, top - rise - 0.03), 0.0, "world")
    for side, edge in ((-1.0, x0), (1.0, x1)):
        outer = edge + side * step_cheek
        frame = kit.plane(V(outer, 0.0, 0.0), V(side, 0.0, 0.0))
        flip = frame[1].y
        profile = [(wall_y, base), (y_foot, base), (y_foot, parapet_top(y_foot, y_land, y_foot, drop)), (y_land, step_parapet), (wall_y, step_parapet)]
        kit.wall(shell, stone, frame, [(flip * y, z) for y, z in profile], [], step_cheek)
        middle = edge + side * step_cheek * 0.5
        kit.member(shell, dressed, V(middle, wall_y, step_parapet + cap * 0.5), V(middle, y_land, step_parapet + cap * 0.5), step_cheek + 0.08, cap, Z, 0.012, "box")
        kit.member(shell, dressed, V(middle, y_land - 0.06, step_parapet + cap * 0.5), V(middle, y_foot, parapet_top(y_foot, y_land, y_foot, drop) + cap * 0.5), step_cheek + 0.08, cap, Z, 0.012, "box")
        newel = parapet_top(y_foot, y_land, y_foot, drop) + cap
        block(shell, dressed, V(middle - step_cheek * 0.5 - 0.05, y_end - 0.12, base + 0.2), V(middle + step_cheek * 0.5 + 0.05, y_end + 0.28, newel), 0.015)
        block(shell, dressed, V(middle - step_cheek * 0.5 - 0.07, y_end - 0.14, newel), V(middle + step_cheek * 0.5 + 0.07, y_end + 0.3, newel + 0.08), 0.015)
        xa, xb = sorted((edge, outer))
        b.col("rock", "cheek", V(xa, wall_y, -drop), V(xb, y_land, step_parapet + cap))
        segments = 5
        for index in range(segments):
            ya = y_land + (y_end + 0.3 - y_land) * index / segments
            yb = y_land + (y_end + 0.3 - y_land) * (index + 1) / segments
            b.col("rock", "cheek", V(xa, ya, -drop), V(xb, yb, parapet_top((ya + yb) * 0.5, y_land, y_foot, drop) + cap))
        for index in range(step_risers - 1):
            if rng.random() < 0.6:
                y = y_land + step_going * (index + rng.uniform(0.3, 0.9))
                kit.grass_tuft(plants, V(edge - side * rng.uniform(0.03, 0.08), y, -rise * (index + 1)), rng, (0.08, 0.22), (4, 9), 0.05)
    for x in (x0 - step_cheek - 0.2, x1 + step_cheek + 0.2):
        for index in range(4):
            kit.grass_tuft(plants, V(x + rng.uniform(-0.15, 0.15), rng.uniform(wall_y + 0.2, y_end), -drop - 0.02), rng, (0.2, 0.5), (6, 14), 0.1)
    b.ramp("ny", "rock", "steps", V(x0, y_land, -drop), V(x1, y_end + step_going * 0.5, -rise * 0.5))
    b.col("rock", "landing", V(x0, wall_y, -drop), V(x1, y_land, -0.02))


def base_course(shell, frame, rng, a_low, a_high, gaps, c0, c1, start=0.0):
    edges = [a_low + start]
    for g0, g1 in sorted(gaps):
        edges += [max(a_low, min(a_high, g0)), max(a_low, min(a_high, g1))]
    edges.append(a_high)
    for s0, s1 in zip(edges[0::2], edges[1::2]):
        a = s0
        while a < s1 - 0.1:
            width = rng.uniform(0.5, 0.95)
            if s1 - (a + width) < 0.3:
                width = s1 - a
            frame_block(shell, "granite_ashlar", frame, a + 0.008, a + width - 0.008, c0, c1 + rng.uniform(-0.04, 0.04), -0.04 * rng.uniform(0.7, 1.2), 0.25, 0.022)
            a += width


def rear_steps_far(part, center_x, wall_y, drop=platform_top):
    x0, x1, y_land, y_end = step_layout(center_x, wall_y)
    y_foot = y_end + 0.15
    rise = drop / step_risers
    block(part, "granite_ashlar", V(x0, wall_y, -drop - 0.2), V(x1, y_land, -0.02))
    outline = [(y_land, -drop - 0.2), (y_end, -drop - 0.2)]
    for index in reversed(range(step_risers - 1)):
        outline += [(y_land + step_going * (index + 1), -rise * (index + 1)), (y_land + step_going * index, -rise * (index + 1))]
    kit.wall(part, "granite_ashlar", kit.plane(V(x1, 0.0, 0.0), X), outline, [], step_width)
    for side, edge in ((-1.0, x0), (1.0, x1)):
        outer = edge + side * step_cheek
        frame = kit.plane(V(outer, 0.0, 0.0), V(side, 0.0, 0.0))
        flip = frame[1].y
        cheek = [(wall_y, -drop - 0.2), (y_foot, -drop - 0.2), (y_foot, parapet_top(y_foot, y_land, y_foot, drop) + 0.12), (y_land, step_parapet + 0.12), (wall_y, step_parapet + 0.12)]
        kit.wall(part, "granite_rubble", frame, [(flip * y, z) for y, z in cheek], [], step_cheek)


def station():
    b = rk.Build("bld_station", 301)
    rng = b.rng
    shell = b.part("shell", 30.0)
    roof = b.part("roof", 50.0)
    joinery = b.part("joinery", 30.0)
    floors = b.part("floors", 30.0)
    interior = b.part("interior", 40.0)
    canopy = b.part("canopy", 40.0)
    detail = b.part("detail", 40.0)
    clutter = b.part("clutter", 45.0)
    debris = b.part("debris", 40.0)
    plants = b.part("plants", 70.0)
    hx = station_hx
    hy = station_hy
    wall_t = station_wall
    ix = hx - wall_t
    iy = hy - wall_t
    gable = station_gable()
    wall_top = gable.under(hy, 0.03)
    stone = "granite_rubble"
    dressed = "granite_ashlar"
    green = "painted_wood_green"
    white = "painted_wood_white"
    parapet = 0.16
    low = station_plinth
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    wait_door = (-3.55, -2.45, 0.0, 2.2)
    office_door = (3.15, 4.25, 0.0, 2.2)
    rear_door = (2.45, 3.55, 0.0, 2.2)
    front_windows = [(-5.15, -4.25, 0.95, 2.35), (-1.75, -0.85, 0.95, 2.35), (1.0, 1.9, 0.95, 2.35)]
    back_windows = [(4.25, 5.15, 0.95, 2.35), (0.85, 1.75, 0.95, 2.35), (-2.5, -1.6, 0.95, 2.35), (-4.8, -3.9, 0.95, 2.35)]
    front_doors = [wait_door, office_door]
    kit.wall(shell, stone, front, kit.rect(-ix, ix, low, wall_top), [kit.rect(d[0], d[1], -0.05, d[3]) for d in front_doors] + [kit.rect(*w) for w in front_windows], wall_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, low, wall_top), [kit.rect(rear_door[0], rear_door[1], -0.05, rear_door[3])] + [kit.rect(*w) for w in back_windows], wall_t)
    for frame in (left, right):
        outline = [(-hy, low), (hy, low), (hy, gable.top(hy) + parapet), (0.0, gable.ridge_top + parapet), (-hy, gable.top(hy) + parapet)]
        kit.wall(shell, stone, frame, outline, [], wall_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, low, wall_top, wall_t, front_doors + front_windows)
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, low, wall_top, wall_t, [rear_door] + back_windows)
    kit.wall_boxes(b, "rock", "left", left, -hy, hy, low, wall_top, wall_t, [])
    kit.wall_boxes(b, "rock", "right", right, -hy, hy, low, wall_top, wall_t, [])
    bd.gable_cols(b, "left_gable", -hx, -ix, gable, wall_top, parapet)
    bd.gable_cols(b, "right_gable", ix, hx, gable, wall_top, parapet)
    for corner, ua, ub in ((V(-hx, -hy, 0.0), X, Y), (V(hx, -hy, 0.0), -X, Y), (V(hx, hy, 0.0), -X, -Y), (V(-hx, hy, 0.0), X, -Y)):
        kit.quoins(shell, dressed, corner, ua, ub, -platform_top - 0.25, gable.top(hy) + parapet - 0.02, rng)
    for frame, windows in ((front, front_windows), (back, back_windows)):
        for w in windows:
            bd.window_surround(shell, joinery, frame, w, wall_t)
            kit.sash_window(joinery, green, frame, w[0], w[1], w[2], w[3], 0.12, rng, rng.choice((0.0, 0.0, 0.25)), 0.3, 0.3, 2, 2)
    for frame, door in ((front, wait_door), (front, office_door), (back, rear_door)):
        kit.lintel_stone(shell, dressed, frame, door[0], door[1], door[3], 0.3, 0.32, 0.025, 0.12)
        kit.jamb_stones(shell, dressed, frame, door[0], -1.0, 0.0, door[3], rng)
        kit.jamb_stones(shell, dressed, frame, door[1], 1.0, 0.0, door[3], rng)
        frame_block(shell, dressed, frame, door[0] - 0.05, door[1] + 0.05, -0.2, 0.0, -0.1, wall_t, 0.015)
        frame_block(joinery, "timber_beam", frame, door[0] - 0.2, door[1] + 0.2, door[3], door[3] + 0.16, wall_t - 0.3, wall_t + 0.004, 0.008)
        kit.door_frame(joinery, green, frame, door[0] + 0.02, door[1] - 0.02, 0.0, door[3], 0.18)
    kit.door_leaf(joinery, green, front, wait_door[1] - 0.09, -1.0, 0.3, 0.02, 2.1, 0.92, 100.0, rng, "panel")
    kit.door_leaf(joinery, green, front, office_door[0] + 0.09, 1.0, 0.3, 0.02, 2.1, 0.92, 78.0, rng, "panel", 2.0)
    kit.door_leaf(joinery, green, back, rear_door[0] + 0.09, 1.0, 0.3, 0.02, 2.1, 0.92, 95.0, rng, "panel")
    ground = -platform_top
    stair_x = -(rear_door[0] + rear_door[1]) * 0.5
    stair_reach = step_width * 0.5 + step_cheek + 0.07
    stair_gap = (-stair_x - stair_reach, -stair_x + stair_reach)
    base_course(shell, front, rng, -ix, ix, [(d[0] - 0.3, d[1] + 0.3) for d in front_doors], -0.6, 0.22, 0.02)
    for frame, a_low, a_high, gaps in ((back, -ix, ix, [stair_gap]), (left, -hy, hy, []), (right, -hy, hy, [])):
        base_course(shell, frame, rng, a_low, a_high, gaps, ground - 0.3, ground + 0.36)
        base_course(shell, frame, rng, a_low, a_high, gaps, -0.14, 0.16)
        bd.damp_band(shell, frame, a_low, a_high, rng, ground + 0.4, ground + 1.05, "granite_rubble_damp", ground - 0.05, 0.003, gaps)
    bd.plaster_wall(interior, kit.facade("front", ix, iy), -ix, ix, 0.0, wall_top - 0.12, front_doors + front_windows, rng, 9)
    bd.plaster_wall(interior, kit.facade("back", ix, iy), -ix, ix, 0.0, wall_top - 0.12, [rear_door] + back_windows, rng, 9)
    bd.plaster_wall(interior, kit.facade("left", ix, hy), -iy, iy, 0.0, wall_top - 0.12, [], rng, 4, [(-1.05, 1.05, 0.0, wall_top)])
    bd.plaster_wall(interior, kit.facade("right", ix, hy), -iy, iy, 0.0, wall_top - 0.12, [], rng, 4, [(-0.9, 0.9, 0.0, wall_top)])
    breast_left = (-ix, -ix + 0.5, -0.95, 0.95)
    breast_right = (ix - 0.4, ix, -0.8, 0.8)
    flue_top = gable.top(0.5) - 0.2
    block(shell, stone, V(breast_left[0], breast_left[2], 0.0), V(breast_left[1], breast_left[2] + 0.42, flue_top), 0.0, "world")
    block(shell, stone, V(breast_left[0], breast_left[3] - 0.42, 0.0), V(breast_left[1], breast_left[3], flue_top), 0.0, "world")
    block(shell, stone, V(breast_left[0], breast_left[2] + 0.42, 1.2), V(breast_left[1], breast_left[3] - 0.42, flue_top), 0.0, "world")
    block(shell, stone, V(breast_right[0], breast_right[2], 0.0), V(breast_right[1], breast_right[3], flue_top), 0.0, "world")
    b.col("rock", "breast", V(breast_left[0], breast_left[2], 0.0), V(breast_left[1], breast_left[3], wall_top))
    b.col("rock", "breast", V(breast_right[0], breast_right[2], 0.0), V(breast_right[1], breast_right[3], wall_top))
    bd.fire_recess(shell, breast_left[1], 0.0, 1.06, 1.2, 0.42, 1.0, rng, dressed, "soot", "timber_beam", False)
    stove_at = V(breast_left[1] + 0.42, 0.0, 0.025)
    stove(b, interior, stove_at, [stove_at + V(0.0, 0.0, 1.55), V(breast_left[1] - 0.1, 0.0, 1.85)])
    bd.parlour_fireplace(b, interior, V(breast_right[0], 0.0, 0.0), -X, rng, 1.25, green, "kitchen_tiles", False)
    stack_z = gable.ridge_top + 1.0
    for x_stack in (-hx + 0.34, hx - 0.34):
        kit.chimney(roof, dressed, x_stack, 0.0, 0.68, 1.0, gable.top(0.5) - 0.3, stack_z, rng, 2)
        b.col("rock", "chimney", V(x_stack - 0.34, -0.5, gable.top(0.5) - 0.3), V(x_stack + 0.34, 0.5, stack_z + 0.12))
        kit.gable_coping(roof, dressed, gable, x_stack + (0.34 - wall_t * 0.5) * (-1.0 if x_stack < 0 else 1.0), wall_t, rng, 0.12, 0.05, parapet)
    moss = kit.smooth_noise(random.Random(17), 5, 1.2)
    kit.slate_roof(roof, gable, -1.0, rng, lambda x, d: moss(V(x * 0.5, d * 0.7, 0.0)) > 0.42 or (d < 0.4 and rng.random() < 0.25), lambda x, d: rng.random() < 0.006, lambda x, d: rng.uniform(0.05, 0.16) if rng.random() < 0.02 else 0.0)
    kit.slate_roof(roof, gable, 1.0, rng, lambda x, d: moss(V(x * 0.5, d * 0.7, 2.0)) > 0.12 or (d < 0.6 and rng.random() < 0.5), lambda x, d: (2.2 < x < 3.4 and 1.0 < d < 1.9 and rng.random() < 0.75) or rng.random() < 0.012, lambda x, d: rng.uniform(0.05, 0.16) if rng.random() < 0.03 else 0.0)
    rafter_xs = [-ix + 0.2 + index * (2.0 * ix - 0.4) / 22 for index in range(23)]
    for side in (-1.0, 1.0):
        kit.roof_boards(roof, gable, side, -ix, ix, 0.0, gable.run + 0.02, rng, "timber_planks_weathered", 0.022, -0.001, [(2.3, 3.2, 1.1, 1.75)] if side > 0 else ())
        kit.roof_rafters(roof, gable, side, rafter_xs, 0.0, gable.run - 0.02, -0.023)
        block(roof, "timber_beam", V(-ix, side * iy, wall_top - 0.02), V(ix, side * (iy + 0.16), wall_top + 0.1), 0.006)
        kit.segmented(roof, green, gable.point(side, -ix, -0.013, -0.095), gable.point(side, ix, -0.013, -0.095), 0.025, 0.17, gable.normal(side), 1.3)
    kit.segmented(roof, "timber_beam", V(-ix, 0.0, gable.ridge_top - 0.195), V(ix, 0.0, gable.ridge_top - 0.195), 0.04, 0.33, Z, 0.9, "box")
    for x in (-3.9, -1.6, 2.2, 4.2):
        tie = wall_top + 0.1
        kit.member(roof, "timber_beam", V(x, -iy - 0.1, tie), V(x, iy + 0.1, tie), 0.12, 0.18, Z, 0.008, "box")
        apex = gable.under(0.0, 0.2)
        kit.member(roof, "timber_beam", V(x, 0.0, tie + 0.09), V(x, 0.0, apex), 0.1, 0.1, X, 0.006, "box")
        for side in (-1.0, 1.0):
            kit.member(roof, "timber_beam", V(x, side * 0.08, tie + 0.2), V(x, side * 1.05, gable.under(1.05, 0.2)), 0.08, 0.08, X, 0.006, "box")
    kit.ridge_tiles(roof, gable, -ix, ix, rng)
    gutter_z = kit.gutter(roof, gable, 1.0, -ix - 0.3, ix + 0.3, rng, 0.04, "rusty_metal", 0.06, 0.05, -1.4)
    kit.gutter(roof, gable, -1.0, -ix - 0.3, ix + 0.3, rng, 0.03)
    kit.downpipe(roof, ix + 0.15, gable.edge + 0.04, hy, gutter_z - 0.03, -platform_top, rng, "rusty_metal", 0.035, 1.6, 0.04)
    kit.downpipe(roof, -ix - 0.15, gable.edge + 0.04, hy, gutter_z - 0.03, -platform_top, rng)
    bd.roof_cols(b, gable, -hx, hx, 6)
    room = 0.6
    partition = kit.plane(V(room, 0.0, 0.0), X)
    doorway = (0.65, 1.75, 0.0, 2.15)
    hatch = (-1.3, -0.6, 1.05, 1.8)
    outline = [(-iy, 0.0), (doorway[0], 0.0), (doorway[0], doorway[3]), (doorway[1], doorway[3]), (doorway[1], 0.0), (iy, 0.0), (iy, wall_top), (0.0, gable.under(0.0, 0.26)), (-iy, wall_top)]
    kit.wall(interior, "plaster_interior", partition, outline, [kit.rect(*hatch)], 0.14, 0.07)
    kit.wall_boxes(b, "wood", "partition", partition, -iy, iy, 0.0, wall_top, 0.14, [doorway, hatch], 0.07)
    kit.door_frame(joinery, green, kit.plane(V(room + 0.07, 0.0, 0.0), X), doorway[0], doorway[1], 0.0, doorway[3], 0.0, 0.07, 0.14)
    kit.door_leaf(joinery, green, kit.plane(V(room + 0.07, 0.0, 0.0), X), doorway[1] - 0.07, -1.0, 0.0, 0.01, 2.07, 0.94, -96.0, rng, "panel", 2.0)
    block(joinery, "timber_beam", V(room - 0.27, hatch[0] - 0.06, hatch[2] - 0.05), V(room - 0.07, hatch[1] + 0.06, hatch[2]), 0.006)
    block(joinery, "timber_beam", V(room + 0.07, hatch[0] - 0.06, hatch[2] - 0.05), V(room + 0.33, hatch[1] + 0.06, hatch[2]), 0.006)
    for y in (hatch[0] - 0.035, hatch[1]):
        block(joinery, green, V(room - 0.085, y, hatch[2]), V(room + 0.085, y + 0.035, hatch[3] + 0.035), 0.004, "board")
    block(joinery, green, V(room - 0.085, hatch[0], hatch[3]), V(room + 0.085, hatch[1], hatch[3] + 0.035), 0.004, "board")
    for index in range(6):
        y = hatch[0] + 0.06 + index * (hatch[1] - hatch[0] - 0.12) / 5.0
        rk.swatch(detail, kit.geo_tube([V(room, y, hatch[2] + 0.12), V(room, y, hatch[3])], kit.circle(0.008, 6), False), "brass", None, True)
    rk.swatch(detail, kit.geo_box(0.012, hatch[1] - hatch[0], 0.02), "brass", Matrix.Translation(V(room, (hatch[0] + hatch[1]) * 0.5, hatch[2] + 0.12)), False)
    face = room - 0.075
    rk.atlas_panel(detail, "tickets", V(face, (hatch[0] + hatch[1]) * 0.5, hatch[3] + 0.2), -X, Z, 0.5, 0.2)
    rk.atlas_panel(detail, "booking_office", V(face, (doorway[0] + doorway[1]) * 0.5, doorway[3] + 0.2), -X, Z, 0.96, 0.175)
    clock = V(face, -0.05, 2.78)
    rk.atlas_disc(detail, "clock", clock, -X, Z, 0.24, 24, "rail_signs", 0.94)
    emit(detail, kit.geo_lathe([(0.24, 0.0), (0.28, 0.0), (0.28, 0.06), (0.255, 0.07), (0.24, 0.05), (0.24, 0.0)], 24), "timber_beam", rk.frame_along(clock + X * 0.003, -X), "given", True)
    kit.floor_boards(floors, "floorboards", -ix, room - 0.07, -iy, iy, 0.0, "x", rng, 0.025, 0.004, None, (0.14, 0.19), 0.03, [-3.4, -1.2], [(breast_left[0], breast_left[1] + 0.75, -0.7, 0.7)], 0.0)
    kit.floor_boards(floors, "floorboards", room + 0.07, ix, -iy, iy, 0.0, "y", rng, 0.025, 0.004, None, (0.14, 0.19), 0.03, [-0.4, 0.9], [(breast_right[0] - 0.46, ix, -0.66, 0.66)], 0.0)
    block(floors, "dirt_debris", V(-ix, -iy, -0.2), V(ix, iy, -0.024))
    block(floors, dressed, V(breast_left[0], -0.7, -0.06), V(breast_left[1] + 0.75, 0.7, 0.025), 0.012)
    b.col("wood", "floor", V(-ix, -iy, -0.3), V(ix, iy, 0.0))
    canopy_roof = station_canopy()
    front_y = -hy - canopy_depth
    sheet = 0.95
    count = int(round(2.0 * canopy_half / sheet))
    for index in range(count):
        if index == 4:
            continue
        x1 = canopy_half - index * (2.0 * canopy_half / count)
        kit.corrugated_sheet(canopy, canopy_roof.point(-1.0, x1 + 0.02, canopy_roof.run, 0.012 + rng.uniform(0.0, 0.004)), -X, -canopy_roof.upslope(-1.0), 2.0 * canopy_half / count + 0.04, canopy_roof.run, rng, "corrugated_rusty", 0.012, 12.0, 4, 0.002, 0.0, 1, 0.0, rng.uniform(-0.01, 0.015))
    for index in range(20):
        x = -canopy_half + 0.1 + index * (2.0 * canopy_half - 0.2) / 19.0
        kit.roof_rafters(canopy, canopy_roof, -1.0, [x], 0.05, canopy_roof.run, -0.03, "timber_beam", 0.05, 0.1)
    for d in (0.35, 1.25, 2.1):
        a = canopy_roof.point(-1.0, -canopy_half, d, -0.015)
        c = canopy_roof.point(-1.0, canopy_half, d, -0.015)
        kit.segmented(canopy, "timber_beam", a, c, 0.06, 0.03, canopy_roof.normal(-1.0), 1.9, "box")
    edge_z = canopy_roof.point(-1.0, 0.0, 0.06, -0.06).z
    block(canopy, white, V(-canopy_half, front_y - 0.08, edge_z - 0.09), V(canopy_half, front_y - 0.05, edge_z + 0.06), 0.004, "board")
    block(canopy, "timber_beam", V(-canopy_half, -hy - 0.1, canopy_top - 0.17), V(canopy_half, -hy, canopy_top - 0.05), 0.006)
    valance(canopy, rng, V(-canopy_half, front_y - 0.09, 0.0), V(canopy_half, front_y - 0.09, 0.0), edge_z - 0.06)
    for end in (-1.0, 1.0):
        steps = 6
        for index in range(steps):
            ya = front_y - 0.06 + (canopy_depth + 0.06) * index / steps
            yb = front_y - 0.06 + (canopy_depth + 0.06) * (index + 1) / steps
            level = canopy_roof.top((ya + yb) * 0.5) - 0.12
            valance(canopy, rng, V(end * (canopy_half + 0.01), ya, 0.0), V(end * (canopy_half + 0.01), yb, 0.0), level)
            block(canopy, white, V(end * canopy_half - 0.015, ya, level - 0.03), V(end * canopy_half + 0.015, yb, level + 0.11), 0.0, "board")
    for x in (-5.4, -3.9, -2.1, 0.08, 2.55, 5.35):
        canopy_bracket(canopy, detail, x, -hy - 0.03, canopy_roof.under(-hy - 0.4, 0.13) - 0.02)
    board = V(0.0, front_y - 0.05, edge_z + 0.42)
    block(canopy, "timber_beam", board + V(-1.4, -0.02, -0.29), board + V(1.4, 0.02, 0.29), 0.006)
    rk.atlas_panel(detail, "halt", board + V(0.0, -0.022, 0.0), -Y, Z, 2.72, 0.51)
    for x in (-1.2, 1.2):
        block(canopy, "timber_beam", V(x - 0.035, front_y - 0.04, edge_z - 0.05), V(x + 0.035, front_y + 0.03, edge_z + 0.72), 0.006)
        rk.bar(detail, "rust_iron", [V(x, front_y + 0.03, edge_z + 0.6), V(x, front_y + 0.5, canopy_roof.top(front_y + 0.5) + 0.02)], 0.03, 0.008, X)
    b.col("metal", "canopy", V(-canopy_half, front_y - 0.1, edge_z - 0.06), V(canopy_half, -hy, canopy_top + 0.03))
    for x in (-4.4, 2.6):
        hook = V(x, -hy - 1.3, canopy_roof.under(-hy - 1.3, 0.1))
        rod(clutter, "rusty_metal", hook, hook - V(0.0, 0.0, 0.35), 0.004, 4)
        bd.lantern(clutter, hook - V(0.0, 0.0, 0.65), rng)
        b.light("warm", hook - V(0.0, 0.0, 0.5))
    rk.atlas_panel(detail, "waiting_room", V((wait_door[0] + wait_door[1]) * 0.5, -hy - 0.035, wait_door[3] + 0.47), -Y, Z, 1.05, 0.19)
    rk.atlas_panel(detail, "private", V((office_door[0] + office_door[1]) * 0.5, -hy - 0.035, office_door[3] + 0.47), -Y, Z, 0.5, 0.2)
    for name, x, width, height in (("timetable", -2.1, 0.5, 0.72), ("notice", 2.55, 0.56, 0.69)):
        block(joinery, "timber_beam", V(x - width * 0.5 - 0.04, -hy - 0.035, 0.96), V(x + width * 0.5 + 0.04, -hy, 1.04 + height), 0.006)
        rk.atlas_panel(detail, name, V(x, -hy - 0.037, 1.0 + height * 0.5), -Y, Z, width, height)
    block(joinery, "timber_beam", V(4.4, -hy - 0.06, 1.62), V(5.2, -hy, 1.7), 0.006)
    for x in (4.55, 4.8, 5.05):
        fire_bucket(clutter, detail, V(x, -hy - 0.03, 1.64))
    rk.atlas_panel(detail, "fire", V(4.8, -hy - 0.005, 1.9), -Y, Z, 0.22, 0.22)
    bench(b, interior, V(-0.75, -hy - 0.02, 0.0), V(0.9, -hy - 0.02, 0.0), -Y, rng)
    bench(b, interior, V(-5.7, -hy - 0.02, 0.0), V(-4.0, -hy - 0.02, 0.0), -Y, rng, green, "timber_beam")
    cart = trolley(b, interior, detail, V(2.2, -hy - 1.55, 0.0), math.radians(8.0), rng)
    bd.suitcase(clutter, cart @ V(-0.25, 0.05, 0.435), 0.4, rng)
    bd.suitcase(clutter, cart @ V(-0.2, 0.08, 0.62), -0.2, rng, False, "leather_brown")
    rk.crate(clutter, rng, cart @ V(0.4, 0.0, 0.435), (0.45, 0.4, 0.32), 0.1)
    for x, y in ((5.05, -3.15), (5.4, -3.55), (4.75, -3.6), (5.3, -2.95)):
        rk.churn(clutter, V(x, y, 0.0), "rusty_metal", rng.uniform(0.95, 1.05))
    b.col("metal", "churns", V(4.55, -3.8, 0.0), V(5.6, -2.75, 0.76))
    bd.bicycle(clutter, V(2.6, -hy - 0.4, 0.0), 0.06, -0.22, rng)
    lamp = V(-3.0, 0.4, gable.under(0.4, 0.2))
    rod(clutter, "rusty_metal", lamp, lamp - V(0.0, 0.0, 1.35), 0.004, 4)
    bd.lantern(clutter, lamp - V(0.0, 0.0, 1.65), rng)
    b.light("warm", lamp - V(0.0, 0.0, 1.5))
    bench(b, interior, V(-2.2, iy - 0.015, 0.0), V(0.3, iy - 0.015, 0.0), -Y, rng)
    bench(b, interior, V(0.3, -iy + 0.015, 0.0), V(-2.2, -iy + 0.015, 0.0), Y, rng)
    bench(b, interior, V(-3.9, iy - 0.015, 0.0), V(-5.3, iy - 0.015, 0.0), -Y, rng)
    bd.chair(interior, V(-3.9, -0.9, 0.0), 0.6, rng, "timber_beam", "timber_planks_weathered", True)
    bd.suitcase(clutter, V(-1.5, iy - 0.75, 0.0), 0.2, rng)
    bd.suitcase(clutter, V(-0.6, iy - 0.85, 0.0), 1.3, rng, True)
    rk.atlas_panel(detail, "advert", V(-ix + 0.004 + 0.015, -1.55, 1.75), X, Z, 0.78, 0.47)
    rk.atlas_panel(detail, "timetable", V(-0.2, iy - 0.02, 1.75), -Y, Z, 0.5, 0.72)
    block(joinery, "timber_beam", V(-0.5, iy - 0.018, 1.35), V(0.1, iy, 2.15), 0.004)
    bd.bucket(clutter, stove_at + V(0.45, 0.5, -0.025), rng)
    bd.long_tool(clutter, V(-ix + 0.6, 1.2, 0.0), V(-ix + 0.52, 1.0, 1.35), "broom", rng)
    b.loot("box", V(-4.7, iy - 0.8, 0.0))
    b.loot("food", V(-1.0, -iy + 0.3, 0.46))
    counter = V(room + 0.07 + 0.29, (hatch[0] + hatch[1]) * 0.5, 0.0)
    bd.cabinet(interior, counter, 1.3, 0.56, 0.0, 1.0, math.pi * 0.5, rng, "timber_planks_weathered", green, 2, 2)
    block(interior, "floorboards", V(room + 0.07, hatch[0] - 0.35, 1.0), V(room + 0.72, hatch[1] + 0.35, 1.04), 0.004, "board")
    b.col("wood", "counter", V(room + 0.07, hatch[0] - 0.33, 0.0), V(room + 0.7, hatch[1] + 0.33, 1.04))
    local_block(interior, "timber_beam", Matrix.Translation(V(room + 0.45, hatch[0] - 0.15, 1.04)), -0.14, 0.14, -0.1, 0.1, 0.0, 0.3, 0.004)
    for row in range(3):
        for column in range(4):
            rk.swatch(detail, kit.geo_box(0.05, 0.006, 0.07), ("cream", "blue", "red", "yellow")[(row + column) % 4], Matrix.Translation(V(room + 0.35 + column * 0.065, hatch[0] - 0.255, 1.085 + row * 0.095)), False)
    bd.table(interior, 1.85, -iy + 0.42, 0.0, 1.3, 0.7, 0.76, rng)
    b.col("wood", "desk", V(1.2, -iy + 0.07, 0.0), V(2.5, -iy + 0.77, 0.76))
    bd.chair(interior, V(1.8, -iy + 1.2, 0.0), math.pi + 0.2, rng)
    bd.books(clutter, V(1.3, -iy + 0.2, 0.76), X, 0.45, rng)
    bd.oil_lamp(clutter, V(2.3, -iy + 0.3, 0.76), rng)
    b.light("warm", V(2.3, -iy + 0.3, 1.0))
    block_instrument(interior, detail, V(2.0, -iy + 0.55, 0.76) + V(0.0, -0.3, 0.0), 2)
    rk.swatch(clutter, kit.geo_cbox(0.34, 0.26, 0.03, 0.004), "cream", Matrix.Translation(V(1.75, -iy + 0.45, 0.775)) @ Matrix.Rotation(-0.15, 4, 'Z'), False)
    safe(b, interior, detail, V(ix - 0.36, iy - 0.34, 0.0), 0.0)
    bd.shelf(interior, V(2.6, iy, 1.55), V(3.8, iy, 1.55), 0.3, -Y, rng)
    rk.crate(clutter, rng, V(2.85, iy - 0.17, 1.55), (0.36, 0.26, 0.22), 0.05)
    bd.books(clutter, V(3.08, iy - 0.22, 1.55), X, 0.36, rng)
    b.loot("medical", V(3.62, iy - 0.16, 1.55))
    bd.coat_rail(interior, clutter, V(room + 0.075, -0.2, 1.7), V(room + 0.075, 0.55, 1.7), X, rng, 2)
    rk.crate(clutter, rng, V(3.3, iy - 0.45, 0.0), (0.7, 0.55, 0.45), 0.1)
    rk.crate(clutter, rng, V(3.35, iy - 0.4, 0.468), (0.45, 0.4, 0.3), -0.2)
    b.col("wood", "parcels", V(2.9, iy - 0.76, 0.0), V(3.7, iy - 0.14, 0.78))
    b.loot("box", V(4.2, iy - 0.4, 0.0))
    b.loot("toolbox", V(ix - 0.45, -iy + 0.4, 0.0))
    rk.atlas_panel(detail, "timetable", V(room + 0.075, -1.75, 1.7), X, Z, 0.36, 0.52)
    lamp = V(3.2, 0.2, gable.under(0.2, 0.2))
    rod(clutter, "rusty_metal", lamp, lamp - V(0.0, 0.0, 1.35), 0.004, 4)
    bd.lantern(clutter, lamp - V(0.0, 0.0, 1.65), rng)
    kit.scatter_chips(debris, "plaster_interior", -ix + 0.7, room - 0.3, -iy + 0.05, -iy + 0.4, 0.0, 22, rng)
    kit.scatter_chips(debris, "plaster_interior", -ix + 0.6, room - 0.2, iy - 0.4, iy - 0.05, 0.0, 22, rng)
    kit.scatter_chips(debris, "plaster_interior", room + 0.9, ix - 0.5, -iy + 0.8, iy - 0.8, 0.0, 16, rng)
    kit.scatter_chips(debris, "glass_dirty", -1.8, -0.8, -iy + 0.05, -iy + 0.5, 0.0, 12, rng, (0.02, 0.06), (0.003, 0.004))
    kit.scatter_chips(debris, "foliage", -3.7, -2.3, -iy + 0.02, 0.6, 0.0, 40, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    kit.scatter_chips(debris, "slate_roof", 2.2, 3.4, 0.6, 1.6, 0.0, 9, rng, (0.1, 0.18), (0.006, 0.008))
    rear_steps(b, shell, floors, plants, rng, stair_x, hy)
    rk.atlas_panel(detail, "halt", V(-(rear_door[0] + rear_door[1]) * 0.5, hy + 0.035, rear_door[3] + 0.52), Y, Z, 1.4, 0.2625)
    block(joinery, "timber_beam", V(-rear_door[1] - 0.2, hy, rear_door[3] + 0.37), V(-rear_door[0] + 0.2, hy + 0.033, rear_door[3] + 0.67), 0.006)
    bd.base_weeds(plants, -hx, hx, -hy, hy, rng, 1.2, lambda p: p.y < -hy + 0.1 or (p.y > hy - 0.1 and abs(p.x - stair_x) < stair_reach + 0.1), 0.1, 0.25, ground - 0.02)
    kit.ivy(plants, V(hx + 0.02, 1.6, ground - 0.02), X, rng, 5.0, 1.0, 8, 30.0)
    kit.ivy(plants, V(2.6, hy + 0.02, ground - 0.02), Y, rng, 4.2, 0.8, 6, 26.0)
    for index in range(10):
        lump(plants, "roof_moss", V(rng.uniform(-ix, ix), rng.uniform(-0.05, 0.08), gable.ridge_top + 0.085), (rng.uniform(0.06, 0.14), 0.09, 0.035), rng, 0.3, 1)
    return b


def station_far():
    b = rk.Build("bld_station_far", 302)
    shell = b.part("shell", 30.0)
    hx = station_hx
    hy = station_hy
    wall_t = station_wall
    ix = hx - wall_t
    gable = station_gable()
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    for frame in (front, back):
        kit.wall(shell, "granite_rubble", frame, kit.rect(-ix, ix, station_plinth, wall_top), [], 0.2)
    for side in ("left", "right"):
        outline = [(-hy, station_plinth), (hy, station_plinth), (hy, gable.top(hy) + 0.16), (0.0, gable.ridge_top + 0.16), (-hy, gable.top(hy) + 0.16)]
        kit.wall(shell, "granite_rubble", kit.facade(side, hx, hy), outline, [], wall_t)
    openings = ((front, [(-3.55, -2.45, 0.0, 2.2), (3.15, 4.25, 0.0, 2.2), (-5.15, -4.25, 0.95, 2.35), (-1.75, -0.85, 0.95, 2.35), (1.0, 1.9, 0.95, 2.35)]), (back, [(2.45, 3.55, 0.0, 2.2), (4.25, 5.15, 0.95, 2.35), (0.85, 1.75, 0.95, 2.35), (-2.5, -1.6, 0.95, 2.35), (-4.8, -3.9, 0.95, 2.35)]))
    for frame, holes in openings:
        for a0, a1, b0, b1 in holes:
            kit.skin(shell, "soot", frame, kit.rect(a0, a1, b0, b1), [], 0.004, 0.002, False)
    kit.roof_slab(shell, gable, -1.0, -ix, ix, "slate_roof")
    kit.roof_slab(shell, gable, 1.0, -ix, ix, "roof_moss")
    for x in (-hx + 0.34, hx - 0.34):
        block(shell, "granite_ashlar", V(x - 0.34, -0.5, gable.top(0.5) - 0.3), V(x + 0.34, 0.5, gable.ridge_top + 1.12))
        block(shell, "terracotta", V(x - 0.1, -0.35, gable.ridge_top + 1.12), V(x + 0.1, -0.15, gable.ridge_top + 1.6))
    canopy_roof = station_canopy()
    kit.roof_slab(shell, canopy_roof, -1.0, -canopy_half, canopy_half, "corrugated_rusty", 0.06)
    edge_z = canopy_roof.point(-1.0, 0.0, 0.06, -0.06).z
    block(shell, "painted_wood_white", V(-canopy_half, -hy - canopy_depth - 0.1, edge_z - 0.36), V(canopy_half, -hy - canopy_depth - 0.07, edge_z + 0.06), 0.0, "board")
    board = V(0.0, -hy - canopy_depth - 0.05, edge_z + 0.42)
    block(shell, "timber_beam", board + V(-1.4, -0.02, -0.29), board + V(1.4, 0.02, 0.29))
    rk.atlas_panel(shell, "halt", board + V(0.0, -0.022, 0.0), -Y, Z, 2.72, 0.51)
    bd.far_trim(shell, gable, hx, hy, wall_t, [gable.top(hy) + 0.14] * 4, 0.16)
    for sx, sy in ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)):
        block(shell, "granite_ashlar", V(sx * (hx - 0.45), sy * (hy - 0.45), -platform_top - 0.2), V(sx * (hx + 0.025), sy * (hy + 0.025), -0.3))
    rear_steps_far(shell, -3.0, hy)
    return b


models = {
    "rail_platform": (platform, platform_far, 60000, 400),
    "rail_platform_end": (platform_end, platform_end_far, 40000, 300),
    "rail_buffer": (buffer, buffer_far, 40000, 300),
    "rail_signal": (signal, signal_far, 40000, 300),
    "rail_crossing": (crossing, crossing_far, 60000, 400),
    "rail_crossing_gate": (crossing_gate, crossing_gate_far, 30000, 300),
    "rail_crossing_post": (crossing_post, crossing_post_far, 30000, 300),
    "rail_crossing_sign": (crossing_sign, crossing_sign_far, 10000, 120),
    "rail_water_tower": (water_tower, water_tower_far, 80000, 500),
    "rail_signal_box": (signal_box, signal_box_far, 120000, 600),
    "bld_station": (station, station_far, 250000, 1200),
}
