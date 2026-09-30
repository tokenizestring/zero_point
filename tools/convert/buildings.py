import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
from buildkit import V, block, emit, rod, lump, local_block, frame_block

arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = arguments[0] if arguments else "library"
wanted = [name for name in (arguments[1].split(",") if len(arguments) > 1 else []) if name]
samples = int(arguments[2]) if len(arguments) > 2 else 96
tau = math.pi * 2.0


def box_at(part, name, center, size3, yaw=0.0, bevel=0.0, mapping="box"):
    geo = kit.geo_cbox(size3[0], size3[1], size3[2], bevel) if bevel > 0.0 else kit.geo_box(size3[0], size3[1], size3[2])
    emit(part, geo, name, kit.turned(center, yaw), mapping)


def bottle(part, position, rng, lying=False, name="glass_dirty"):
    h = rng.uniform(0.2, 0.3)
    r = rng.uniform(0.03, 0.04)
    profile = [(0.0, 0.0), (r * 0.92, 0.0), (r, 0.01), (r, h * 0.6), (r * 0.55, h * 0.72), (r * 0.3, h * 0.78), (r * 0.3, h * 0.97), (r * 0.36, h), (0.0, h)]
    if lying:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r)) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, kit.geo_lathe(profile, 10), name, matrix, "given", True)


def jar(part, position, rng, name="glass_dirty", lid="rusty_metal"):
    h = rng.uniform(0.12, 0.2)
    r = rng.uniform(0.04, 0.06)
    emit(part, kit.geo_lathe([(0.0, 0.0), (r, 0.0), (r, h * 0.85), (r * 0.8, h * 0.92), (0.0, h * 0.92)], 12), name, kit.turned(position, 0.0), "given", True)
    emit(part, kit.geo_lathe([(0.0, h * 0.9), (r * 0.85, h * 0.9), (r * 0.85, h), (0.0, h)], 12), lid, kit.turned(position, 0.0), "given", True)


def tin(part, position, rng, name="rusty_metal"):
    h = rng.uniform(0.08, 0.18)
    r = rng.uniform(0.04, 0.08)
    emit(part, kit.geo_lathe([(0.0, 0.0), (r, 0.0), (r, h), (r * 0.9, h), (0.0, h - 0.004)], 12), name, kit.turned(position, rng.uniform(0, tau)), "given", True)


def plate(part, position, rng, radius=None, tilt=0.0, yaw=None, name="ceramic"):
    r = radius or rng.uniform(0.1, 0.13)
    profile = [(0.0, 0.0), (r * 0.55, 0.0), (r * 0.62, 0.006), (r, 0.022), (r * 0.97, 0.026), (r * 0.6, 0.011), (0.0, 0.009)]
    geo = kit.geo_lathe(profile, 16)
    region = kit.catalog[name]["regions"]["pattern"]
    geo.uvs = [[(region[0] + (0.5 + geo.points[i].x / (2.2 * r)) * (region[1] - region[0]), 0.5 + geo.points[i].y / (2.2 * r)) for i in face] for face in geo.faces]
    matrix = kit.Matrix.Translation(position) @ kit.Matrix.Rotation(rng.uniform(0, tau) if yaw is None else yaw, 4, 'Z') @ kit.Matrix.Rotation(tilt, 4, 'X')
    emit(part, geo, name, matrix, "texture", True)


def plain(geo, name="ceramic", scale=1.0):
    region = kit.catalog[name]["regions"]["plain"]
    tile = kit.tile_of(name)
    span = region[1] - region[0]
    geo.uvs = [[(region[0] + span * 0.1 + ((u * scale / tile) % 1.0) * span * 0.8, v * scale / tile) for u, v in face_uv] for face_uv in geo.uvs]
    return geo


def cup(part, position, rng, name="ceramic"):
    r = rng.uniform(0.035, 0.045)
    h = rng.uniform(0.07, 0.09)
    matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, plain(kit.geo_lathe([(0.0, 0.0), (r * 0.7, 0.0), (r, h * 0.3), (r * 1.05, h), (r * 0.95, h), (r * 0.9, h * 0.35), (0.0, h * 0.15)], 12)), name, matrix, "texture", True)
    path = [V(r, 0.0, h * 0.8), V(r + 0.025, 0.0, h * 0.7), V(r + 0.025, 0.0, h * 0.35), V(r, 0.0, h * 0.25)]
    emit(part, plain(kit.geo_tube(path, kit.circle(0.005, 5), True, V(0.0, 1.0, 0.0))), name, matrix, "texture", True)


def jug(part, position, rng, name="ceramic"):
    h = rng.uniform(0.18, 0.26)
    r = h * 0.38
    matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, plain(kit.geo_lathe([(0.0, 0.0), (r * 0.8, 0.0), (r, h * 0.35), (r * 0.72, h * 0.8), (r * 0.8, h), (r * 0.7, h), (r * 0.6, h * 0.8), (0.0, h * 0.1)], 14)), name, matrix, "texture", True)
    path = [V(r * 0.75, 0.0, h * 0.85), V(r + 0.05, 0.0, h * 0.75), V(r + 0.045, 0.0, h * 0.35), V(r * 0.95, 0.0, h * 0.28)]
    emit(part, plain(kit.geo_tube(path, kit.circle(0.008, 5), True, V(0.0, 1.0, 0.0))), name, matrix, "texture", True)


def pot(part, position, rng, radius=None, name="rusty_metal"):
    r = radius or rng.uniform(0.1, 0.16)
    h = r * rng.uniform(0.7, 1.0)
    matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, kit.geo_lathe([(0.0, 0.0), (r * 0.85, 0.0), (r, h * 0.2), (r, h), (r * 0.95, h), (r * 0.94, h * 0.2), (0.0, 0.008)], 14), name, matrix, "given", True)
    for sign in (-1.0, 1.0):
        path = [V(sign * r * 0.9, 0.0, h * 0.85), V(sign * (r + 0.03), 0.0, h * 0.9), V(sign * (r + 0.03), 0.0, h * 1.02), V(sign * r * 0.95, 0.0, h * 1.0)]
        emit(part, kit.geo_tube(path, kit.circle(0.006, 5), True, V(0.0, 1.0, 0.0)), name, matrix, "given", True)
    return h


def hanging_pot(part, hook, rng, drop=0.35, name="rusty_metal"):
    rod(part, name, hook, hook - V(0.0, 0.0, drop), 0.004, 4)
    r = rng.uniform(0.09, 0.13)
    h = r * 0.8
    base = hook - V(0.0, 0.0, drop + h + r * 0.75)
    pot(part, base, rng, r, name)
    arc = [base + V(-r, 0.0, h)] + [base + V(-r * math.cos(math.pi * t / 6), 0.0, h + r * 0.75 * math.sin(math.pi * t / 6)) for t in range(1, 6)] + [base + V(r, 0.0, h)]
    emit(part, kit.geo_tube(arc, kit.circle(0.004, 4), True, V(0.0, 1.0, 0.0)), name, None, "given", True)


def kettle(part, position, rng, name="rusty_metal"):
    matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.09, 0.0), (0.1, 0.04), (0.095, 0.12), (0.06, 0.15), (0.03, 0.16), (0.0, 0.165)], 14), name, matrix, "given", True)
    emit(part, kit.geo_tube([V(0.08, 0.0, 0.05), V(0.14, 0.0, 0.1), V(0.17, 0.0, 0.15)], [(0.015, 0.0), (0.0, 0.015), (-0.015, 0.0), (0.0, -0.015)], True, V(0.0, 1.0, 0.0), [1.0, 0.8, 0.5]), name, matrix, "given", True)
    emit(part, kit.geo_tube([V(-0.06, 0.0, 0.15), V(-0.04, 0.0, 0.23), V(0.04, 0.0, 0.23), V(0.06, 0.0, 0.15)], kit.circle(0.006, 5), True, V(0.0, 1.0, 0.0)), name, matrix, "given", True)


def bucket(part, position, rng, name="rusty_metal", tipped=False):
    r0 = rng.uniform(0.1, 0.12)
    r1 = r0 * 1.25
    h = rng.uniform(0.26, 0.32)
    if tipped:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r1)) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, kit.geo_lathe([(0.0, 0.0), (r0, 0.0), (r1, h), (r1 - 0.006, h), (r0 - 0.006, 0.006), (0.0, 0.006)], 16), name, matrix, "given", True)
    arc = [V(-r1, 0.0, h * 0.95)] + [V(-r1 * math.cos(math.pi * t / 6), 0.0, h * 0.95 + r1 * 0.9 * math.sin(math.pi * t / 6)) for t in range(1, 6)] + [V(r1, 0.0, h * 0.95)]
    emit(part, kit.geo_tube(arc, kit.circle(0.004, 4), True, V(0.0, 1.0, 0.0)), name, matrix, "given", True)


def lantern(part, position, rng, name="rusty_metal", glass="glass_dirty"):
    matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.08, 0.0), (0.085, 0.02), (0.08, 0.06), (0.05, 0.07), (0.0, 0.07)], 12), name, matrix, "given", True)
    emit(part, kit.geo_lathe([(0.0, 0.07), (0.035, 0.07), (0.065, 0.14), (0.06, 0.2), (0.035, 0.24), (0.0, 0.24)], 12), glass, matrix, "given", True)
    emit(part, kit.geo_lathe([(0.0, 0.235), (0.06, 0.235), (0.05, 0.27), (0.02, 0.29), (0.0, 0.29)], 12), name, matrix, "given", True)
    for angle in (0.3, 2.4, 4.5):
        emit(part, kit.geo_tube([V(0.075 * math.cos(angle), 0.075 * math.sin(angle), 0.06), V(0.085 * math.cos(angle), 0.085 * math.sin(angle), 0.15), V(0.06 * math.cos(angle), 0.06 * math.sin(angle), 0.245)], kit.circle(0.004, 4), True), name, matrix, "given", True)
    loop = [V(0.07 * math.cos(math.pi * t / 8), 0.0, 0.29 + 0.07 * math.sin(math.pi * t / 8)) for t in range(9)]
    emit(part, kit.geo_tube(loop, kit.circle(0.004, 4), True, V(0.0, 1.0, 0.0)), name, matrix, "given", True)


def oil_lamp(part, position, rng, glass="glass_dirty"):
    matrix = kit.turned(position, 0.0)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.015), (0.03, 0.03), (0.055, 0.1), (0.03, 0.12), (0.0, 0.12)], 12), "rusty_metal", matrix, "given", True)
    emit(part, kit.geo_lathe([(0.025, 0.12), (0.03, 0.14), (0.035, 0.2), (0.022, 0.3), (0.018, 0.3), (0.03, 0.2), (0.026, 0.14), (0.02, 0.12)], 10), glass, matrix, "given", True)


def chair(part, position, yaw, rng, name="timber_beam", seat="timber_planks_weathered", fallen=False):
    base = kit.turned(position, yaw)
    if fallen:
        base = kit.Matrix.Translation(position) @ kit.Matrix.Rotation(yaw, 4, 'Z') @ kit.Matrix.Translation(V(0.0, 0.0, 0.23)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X')
    for sx in (-0.19, 0.19):
        for sy in (-0.18, 0.18):
            top = 0.44 if sy < 0.0 else 0.95
            local_block(part, name, base, sx - 0.02, sx + 0.02, sy - 0.02, sy + 0.02, 0.0, top, 0.004)
    local_block(part, seat, base, -0.22, 0.22, -0.21, 0.21, 0.42, 0.455, 0.006, "board")
    for z in (0.62, 0.74, 0.86):
        local_block(part, name, base, -0.17, 0.17, 0.165, 0.19, z - 0.035, z + 0.035, 0.004)
    for sy in (-0.18, 0.18):
        local_block(part, name, base, -0.17, 0.17, sy - 0.012, sy + 0.012, 0.15, 0.18)
    local_block(part, name, base, -0.19, -0.17, -0.16, 0.16, 0.2, 0.225)
    local_block(part, name, base, 0.17, 0.19, -0.16, 0.16, 0.2, 0.225)


def table(part, x, y, z, width, depth, height, rng, top="floorboards", legs="timber_beam", yaw=0.0):
    base = kit.turned(V(x, y, z), yaw)
    boards = max(3, int(round(depth / 0.16)))
    for index in range(boards):
        y0 = -depth * 0.5 + depth * index / boards
        y1 = -depth * 0.5 + depth * (index + 1) / boards
        local_block(part, top, base, -width * 0.5, width * 0.5, y0 + 0.002, y1 - 0.002, height - 0.035 + rng.uniform(-0.002, 0.002), height, 0.004, "board")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            lx = sx * (width * 0.5 - 0.08)
            ly = sy * (depth * 0.5 - 0.07)
            local_block(part, legs, base, lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, 0.0, height - 0.035, 0.005)
    for sy in (-1.0, 1.0):
        local_block(part, legs, base, -width * 0.5 + 0.08, width * 0.5 - 0.08, sy * (depth * 0.5 - 0.07) - 0.012, sy * (depth * 0.5 - 0.07) + 0.012, height - 0.15, height - 0.035)
    for sx in (-1.0, 1.0):
        local_block(part, legs, base, sx * (width * 0.5 - 0.08) - 0.012, sx * (width * 0.5 - 0.08) + 0.012, -depth * 0.5 + 0.07, depth * 0.5 - 0.07, height - 0.15, height - 0.035)


def cabinet(part, center, width, depth, z0, z1, yaw, rng, carcass="timber_planks_weathered", paint="painted_wood_blue", doors=2, drawers=0, open_door=None):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    t = 0.02
    local_block(part, carcass, base, -hw, hw, -hd, hd, z0 + 0.06, z0 + 0.06 + t)
    local_block(part, carcass, base, -hw, hw, -hd, hd, z1 - t, z1)
    local_block(part, carcass, base, -hw, -hw + t, -hd, hd, z0, z1)
    local_block(part, carcass, base, hw - t, hw, -hd, hd, z0, z1)
    local_block(part, carcass, base, -hw, hw, hd - t, hd, z0 + 0.06, z1)
    local_block(part, paint, base, -hw + 0.01, hw - 0.01, -hd, -hd + 0.02, z0, z0 + 0.06)
    span = (width - 0.04) / max(doors, 1)
    top_doors = z1 - t - (0.16 if drawers else 0.0)
    for index in range(doors):
        dx0 = -hw + 0.02 + span * index + 0.004
        dx1 = dx0 + span - 0.008
        if open_door is not None and index == open_door:
            hinge = base @ kit.Matrix.Translation(V(dx0 if index == 0 else dx1, -hd - 0.012, z0 + 0.07)) @ kit.Matrix.Rotation(-1.9 if index == 0 else 1.9, 4, 'Z')
            if index == 0:
                local_block(part, paint, hinge, 0.0, dx1 - dx0, 0.0, 0.014, 0.0, top_doors - z0 - 0.08, 0.003, "board")
            else:
                local_block(part, paint, hinge, -(dx1 - dx0), 0.0, 0.0, 0.014, 0.0, top_doors - z0 - 0.08, 0.003, "board")
            continue
        local_block(part, paint, base, dx0, dx1, -hd - 0.014, -hd, z0 + 0.07, top_doors - 0.01, 0.003, "board")
        knob_x = dx1 - 0.05 if index % 2 == 0 else dx0 + 0.05
        local_block(part, "rusty_metal", base, knob_x - 0.012, knob_x + 0.012, -hd - 0.036, -hd - 0.014, (z0 + top_doors) * 0.5 - 0.012, (z0 + top_doors) * 0.5 + 0.012)
    for index in range(drawers):
        span_d = (width - 0.04) / drawers
        dx0 = -hw + 0.02 + span_d * index + 0.004
        pull = rng.uniform(0.0, 0.12) if rng.random() < 0.4 else 0.0
        local_block(part, paint, base, dx0, dx0 + span_d - 0.008, -hd - 0.014 - pull, -hd - pull, top_doors, z1 - t - 0.008, 0.003, "board")
        if pull > 0.0:
            local_block(part, carcass, base, dx0 + 0.01, dx0 + span_d - 0.018, -hd - pull, -hd + 0.2, top_doors + 0.01, z1 - t - 0.03)
        local_block(part, "rusty_metal", base, dx0 + span_d * 0.5 - 0.03, dx0 + span_d * 0.5 + 0.03, -hd - 0.03 - pull, -hd - 0.014 - pull, (top_doors + z1 - t) * 0.5 - 0.01, (top_doors + z1 - t) * 0.5 + 0.005)


def footprint(build, surface, tag, base, hw, hd, z0, z1):
    corners = [base @ V(sx * hw, sy * hd, 0.0) for sx in (-1, 1) for sy in (-1, 1)]
    ground = base.translation.z
    low = V(min(c.x for c in corners), min(c.y for c in corners), ground + z0)
    high = V(max(c.x for c in corners), max(c.y for c in corners), ground + z1)
    build.col(surface, tag, low, high)


def dresser(build, part, clutter, center, yaw, rng, paint="painted_wood_blue", width=1.35):
    base = kit.turned(center, yaw)
    depth = 0.46
    hw = width * 0.5
    cabinet(part, center, width, depth, 0.0, 0.86, yaw, rng, "timber_planks_weathered", paint, 2, 2)
    local_block(part, "floorboards", base, -hw - 0.03, hw + 0.03, -depth * 0.5 - 0.03, depth * 0.5, 0.86, 0.9, 0.004, "board")
    back = depth * 0.5
    front = back - 0.24
    for x in (-hw, hw - 0.025):
        local_block(part, paint, base, x, x + 0.025, front, back, 0.9, 2.02, 0.003, "board")
    local_block(part, paint, base, -hw - 0.03, hw + 0.03, front - 0.03, back, 2.02, 2.08, 0.006, "board")
    local_block(part, "timber_planks_weathered", base, -hw, hw, back - 0.015, back, 0.9, 2.02)
    shelves = (1.28, 1.62, 1.96)
    for z in shelves:
        local_block(part, paint, base, -hw + 0.025, hw - 0.025, front, back, z - 0.022, z, 0.003, "board")
        local_block(part, paint, base, -hw + 0.025, hw - 0.025, front, front + 0.012, z + 0.03, z + 0.045)
    for z in (0.9,) + shelves[:-1]:
        x = -hw + 0.12
        while x < hw - 0.1:
            roll = rng.random()
            if roll < 0.55:
                radius = rng.uniform(0.1, 0.13)
                matrix = base @ kit.Matrix.Translation(V(x, back - 0.06, z + radius * 0.96 + 0.004))
                plate(clutter, matrix.translation, rng, radius, 1.32 + rng.uniform(-0.05, 0.05), yaw)
                x += rng.uniform(0.22, 0.28)
            elif roll < 0.72:
                jug(clutter, base @ V(x, back - 0.12, z), rng)
                x += 0.2
            elif roll < 0.85:
                cup(clutter, base @ V(x, back - 0.12, z), rng)
                x += 0.12
            else:
                x += rng.uniform(0.15, 0.3)
    for index in range(4):
        cup(clutter, base @ V(-hw + 0.15 + index * (width - 0.3) / 3, -0.05, 0.9), rng)
    footprint(build, "wood", "dresser", base, hw, depth * 0.5, 0.0, 0.9)
    footprint(build, "wood", "dresser_rack", base @ kit.Matrix.Translation(V(0.0, (front + back) * 0.5, 0.0)), hw, 0.12, 1.26, 2.08)
    return base @ V(0.0, -0.1, 0.9)


def cushion_geo(sx, sy, sz, rng, puff=0.02, sag=0.0, nx=6, ny=4):
    points = []
    faces = []
    grid = {}
    for layer, z in (("bottom", -sz * 0.5), ("top", sz * 0.5)):
        for j in range(ny + 1):
            for i in range(nx + 1):
                u = i / nx
                v = j / ny
                x = (u - 0.5) * sx
                y = (v - 0.5) * sy
                edge = min(u, 1 - u, v, 1 - v)
                bulge = math.sin(math.pi * u) * math.sin(math.pi * v)
                zz = z
                if layer == "top":
                    zz = z + puff * bulge - sag * bulge + rng.uniform(-0.003, 0.003) - sz * 0.3 * (1.0 - min(edge * 5.0, 1.0))
                    inset = min(sz * 0.25, sx * 0.16, sy * 0.16) * (1.0 - min(edge * 6.0, 1.0))
                else:
                    inset = min(sz * 0.15, sx * 0.1, sy * 0.1) * (1.0 - min(edge * 6.0, 1.0))
                if abs(x) > 1e-9:
                    x -= math.copysign(inset, x)
                if abs(y) > 1e-9:
                    y -= math.copysign(inset, y)
                grid[(layer, i, j)] = len(points)
                points.append(V(x, y, zz))
    for j in range(ny):
        for i in range(nx):
            faces.append((grid[("top", i, j)], grid[("top", i + 1, j)], grid[("top", i + 1, j + 1)], grid[("top", i, j + 1)]))
            faces.append((grid[("bottom", i, j)], grid[("bottom", i, j + 1)], grid[("bottom", i + 1, j + 1)], grid[("bottom", i + 1, j)]))
    ring = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)] + [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)]
    for index in range(len(ring)):
        a = ring[index]
        b = ring[(index + 1) % len(ring)]
        faces.append((grid[("bottom",) + a], grid[("bottom",) + b], grid[("top",) + b], grid[("top",) + a]))
    return kit.Geo(points, faces)


def mattress(part, center, size3, yaw, rng, sag=0.05, name="mattress"):
    emit(part, cushion_geo(size3[0], size3[1], size3[2], rng, 0.015, sag, 8, 5), name, kit.turned(center, yaw), "box", True)


def drape(part, center, width, depth, drop, yaw, rng, name="fabric_worn", folds=5, hang_sides=(True, False)):
    nx = 14
    ny = 10
    points = []
    faces = []
    total_y = depth + (drop if hang_sides[0] else 0.0) + (drop if hang_sides[1] else 0.0)
    phase = rng.uniform(0, tau)
    for j in range(ny + 1):
        for i in range(nx + 1):
            u = i / nx
            s = j / ny * total_y - (drop if hang_sides[0] else 0.0)
            x = (u - 0.5) * width
            ripple = math.sin(u * folds * math.pi + phase + s * 3.0) * 0.02 + rng.uniform(-0.004, 0.004)
            if s < 0.0:
                y = -depth * 0.5 - 0.01 * abs(s) - ripple * 0.5
                z = s * 0.95
            elif s > depth:
                y = depth * 0.5 + 0.01 * (s - depth) + ripple * 0.5
                z = -(s - depth) * 0.95
            else:
                y = s - depth * 0.5
                z = ripple * 0.6 + 0.01
            points.append(V(x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    emit(part, kit.Geo(points, faces), name, kit.turned(center, yaw), "box", True)


def curtain(part, top_a, top_b, drop, rng, name="fabric_worn", gather=0.55, torn=True):
    nx = 12
    ny = 8
    points = []
    faces = []
    span = top_b - top_a
    normal = V(-span.y, span.x, 0.0).normalized()
    ragged = [rng.uniform(0.6, 1.0) if torn else 1.0 for index in range(nx + 1)]
    for j in range(ny + 1):
        for i in range(nx + 1):
            u = i / nx
            v = j / ny
            p = top_a + span * (u * gather) + V(0.0, 0.0, -drop * v * ragged[i]) + normal * (math.sin(u * 14.0) * 0.035 * (0.4 + 0.6 * v))
            points.append(p)
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + nx + 1, a + nx + 2, a + 1))
    emit(part, kit.Geo(points, faces), name, None, "world", True)
    rod(part, "rusty_metal", top_a + V(0.0, 0.0, 0.02), top_b + V(0.0, 0.0, 0.02), 0.008, 5)


def rug(part, center, width, depth, yaw, rng, name="fabric_tartan"):
    nx = 10
    ny = 7
    points = []
    faces = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = (i / nx - 0.5) * width
            y = (j / ny - 0.5) * depth
            curl = 0.03 if (i == 0 and j % 3 == 0) or (j == ny and i % 4 == 1) else 0.0
            points.append(V(x, y, 0.006 + rng.uniform(0.0, 0.006) + curl))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    emit(part, kit.Geo(points, faces), name, kit.turned(center, yaw), "box", True)


def iron_bed(build, part, clutter, center, yaw, rng, length=1.95, width=1.25, frame="rusty_metal", bedding=True, bare=False):
    base = kit.turned(center, yaw)
    hx = length * 0.5
    hy = width * 0.5
    for sx in (-1.0, 1.0):
        top = 1.15 if sx < 0 else 0.85
        for sy in (-1.0, 1.0):
            emit(part, kit.geo_tube([V(sx * hx, sy * hy, 0.0), V(sx * hx, sy * hy, top)], kit.circle(0.022, 8), True), frame, base, "given", True)
            emit(part, kit.geo_lathe([(0.0, 0.0), (0.03, 0.0), (0.035, 0.03), (0.0, 0.06)], 8), frame, base @ kit.Matrix.Translation(V(sx * hx, sy * hy, top)), "given", True)
        for z in (0.36, top - 0.05):
            emit(part, kit.geo_tube([V(sx * hx, -hy, z), V(sx * hx, hy, z)], kit.circle(0.013, 6), True), frame, base, "given", True)
        bars = 7
        for index in range(1, bars):
            y = -hy + width * index / bars
            emit(part, kit.geo_tube([V(sx * hx, y, 0.36), V(sx * hx, y, top - 0.05)], kit.circle(0.007, 5), True), frame, base, "given", True)
    for sy in (-1.0, 1.0):
        local_block(part, frame, base, -hx, hx, sy * hy - 0.004, sy * hy + 0.004, 0.33, 0.37)
        local_block(part, frame, base, -hx, hx, sy * hy - 0.02 * (1 if sy > 0 else -1) - 0.015, sy * hy - 0.02 * (1 if sy > 0 else -1) + 0.015, 0.33, 0.336)
    for index in range(9):
        x = -hx + 0.1 + (length - 0.2) * index / 8
        emit(part, kit.geo_box(0.02, width - 0.05, 0.004), frame, base @ kit.Matrix.Translation(V(x, 0.0, 0.37)), "box")
    if not bare:
        mattress(clutter, base @ V(0.0, 0.0, 0.47), (length - 0.08, width - 0.06, 0.2), yaw, rng, 0.06)
    if bedding and not bare:
        drape(clutter, base @ V(0.2, 0.0, 0.575), length * 0.7, width - 0.02, 0.3, yaw, rng, "fabric_tartan", 6, (True, True))
        emit(clutter, cushion_geo(0.36, 0.6, 0.12, rng, 0.04), "mattress", base @ kit.turned(V(-hx + 0.28, 0.0, 0.63), 0.1), "box", True)
    footprint(build, "metal", "bed", base, hx, hy, 0.33, 0.62)
    return base


def wardrobe(build, part, clutter, center, yaw, rng, width=1.1, depth=0.58, wood="timber_beam", paint="floorboards"):
    height = 1.95
    cabinet(part, center, width, depth, 0.0, height - 0.08, yaw, rng, "timber_planks_weathered", paint, 2, 0, 1)
    base = kit.turned(center, yaw)
    local_block(part, wood, base, -width * 0.5 - 0.04, width * 0.5 + 0.04, -depth * 0.5 - 0.04, depth * 0.5 + 0.04, height - 0.08, height, 0.01)
    rod(part, "rusty_metal", base @ V(-width * 0.5 + 0.03, 0.0, 1.6), base @ V(width * 0.5 - 0.03, 0.0, 1.6), 0.012, 6)
    curtain(clutter, base @ V(0.15, 0.02, 1.58), base @ V(0.45, 0.02, 1.58), 1.0, rng, "fabric_worn", 1.0)
    footprint(build, "wood", "wardrobe", base, width * 0.5, depth * 0.5, 0.0, height)
    return base


def range_stove(build, part, clutter, back_center, yaw, rng, width=1.2, depth=0.52, name="rusty_metal"):
    base = kit.turned(back_center, yaw)
    y0 = -width * 0.5
    y1 = width * 0.5

    def at(x, y, z):
        return base @ V(x, y, z)

    local_block(part, name, base, 0.0, depth - 0.03, y0, y1, 0.0, 0.08)
    local_block(part, name, base, 0.0, depth - 0.02, y0, y0 + 0.4, 0.08, 0.8, 0.006)
    local_block(part, name, base, 0.0, depth - 0.02, y1 - 0.4, y1, 0.08, 0.8, 0.006)
    local_block(part, "soot", base, 0.0, depth - 0.12, y0 + 0.4, y1 - 0.4, 0.08, 0.8)
    for index in range(6):
        y = y0 + 0.43 + index * (width - 0.86) / 5
        rod(part, name, at(depth - 0.06, y, 0.3), at(depth - 0.06, y, 0.62), 0.008, 6)
    for z in (0.3, 0.46, 0.62):
        rod(part, name, at(depth - 0.05, y0 + 0.4, z), at(depth - 0.05, y1 - 0.4, z), 0.009, 6)
    lump(part, "soot", at(depth - 0.25, 0.0, 0.24), (0.14, 0.18, 0.06), rng, 0.3, 1)
    for index in range(3):
        emit(part, kit.geo_tube([at(depth - 0.35, -0.1 + index * 0.08, 0.3), at(depth - 0.12, -0.05 + index * 0.06, 0.33)], kit.circle(0.03, 6), True), "timber_charred", None, "given", True)
    for side in (-1.0, 1.0):
        y_door = side * (width * 0.5 - 0.2)
        local_block(part, name, base, depth - 0.02, depth + 0.005, y_door - 0.17, y_door + 0.17, 0.2, 0.66, 0.006)
        rod(part, name, at(depth + 0.03, y_door - 0.1, 0.62), at(depth + 0.03, y_door + 0.1, 0.62), 0.008, 6)
        for end in (-0.1, 0.1):
            rod(part, name, at(depth, y_door + end, 0.62), at(depth + 0.03, y_door + end, 0.62), 0.006, 5)
    local_block(part, name, base, 0.0, depth + 0.02, y0 - 0.02, y1 + 0.02, 0.8, 0.84, 0.008)
    for side in (-0.25, 0.25):
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.11, 0.0), (0.11, 0.008), (0.0, 0.01)], 16), name, base @ kit.Matrix.Translation(V(depth * 0.5, side, 0.84)), "given", True)
    rod(part, name, at(depth + 0.05, y0, 0.74), at(depth + 0.05, y1, 0.74), 0.012, 8)
    for y in (y0 + 0.05, y1 - 0.05):
        rod(part, name, at(depth, y, 0.74), at(depth + 0.05, y, 0.74), 0.008, 5)
    local_block(part, name, base, 0.0, 0.05, y0, y1, 0.84, 1.3, 0.006)
    emit(part, kit.geo_tube([at(0.15, 0.0, 0.84), at(0.15, 0.0, 1.5), at(0.05, 0.0, 1.8)], kit.circle(0.08, 12), True), name, None, "given", True)
    kettle(clutter, at(0.3, -0.25, 0.855), rng)
    pot(clutter, at(0.3, 0.25, 0.855), rng, 0.12)
    low, high = kit.box_between(at(0.0, y0, 0.0), at(depth + 0.05, y1, 0.0))
    build.col("metal", "range", V(low.x, low.y, back_center.z), V(high.x, high.y, back_center.z + 0.86))
    build.light("fire", at(depth - 0.25, 0.0, 0.35))


def fire_recess(part, x_face, y_center, width, height, depth, direction, rng, stone="granite_ashlar", back="soot", beam="timber_beam", lintel_beam=True, hearth=True):
    x_back = x_face - direction * depth
    y0 = y_center - width * 0.5
    y1 = y_center + width * 0.5
    block(part, back, V(x_back, y0, 0.0), V(x_back + direction * 0.02, y1, height))
    block(part, back, V(x_face, y0 - 0.02, 0.0), V(x_back, y0, height))
    block(part, back, V(x_face, y1, 0.0), V(x_back, y1 + 0.02, height))
    block(part, back, V(x_face, y0, height), V(x_back, y1, height + 0.02))
    if lintel_beam:
        block(part, beam, V(x_face + direction * 0.05, y0 - 0.35, height), V(x_face - direction * 0.3, y1 + 0.35, height + 0.3), 0.01)
    else:
        block(part, stone, V(x_face + direction * 0.03, y0 - 0.3, height), V(x_face - direction * 0.35, y1 + 0.3, height + 0.28), 0.016)
    for side in (-1.0, 1.0):
        edge = y0 if side < 0 else y1
        z = 0.0
        course = 0
        while z < height - 0.05:
            h = rng.uniform(0.28, 0.4)
            if z + h > height - 0.12:
                h = height - z
            w = rng.uniform(0.2, 0.26) if course % 2 == 0 else rng.uniform(0.3, 0.38)
            block(part, stone, V(x_face + direction * 0.03, edge, z + 0.005), V(x_face - direction * 0.3, edge + side * w, z + h - 0.005), 0.014)
            z += h
            course += 1
    if hearth:
        block(part, stone, V(x_back, y0 - 0.15, -0.05), V(x_face + direction * 0.55, y1 + 0.15, 0.025), 0.012)


def fire_basket(part, x_center, y_center, rng, logs=True):
    for index in range(5):
        y = y_center - 0.2 + index * 0.1
        rod(part, "rusty_metal", V(x_center + 0.1, y, 0.12), V(x_center + 0.1, y, 0.32), 0.008, 6)
        rod(part, "rusty_metal", V(x_center - 0.1, y, 0.12), V(x_center - 0.1, y, 0.32), 0.008, 6)
    block(part, "rusty_metal", V(x_center - 0.12, y_center - 0.25, 0.1), V(x_center + 0.12, y_center + 0.25, 0.13))
    for sx in (-0.1, 0.1):
        rod(part, "rusty_metal", V(x_center + sx, y_center - 0.22, 0.3), V(x_center + sx, y_center + 0.22, 0.3), 0.007, 5)
    for sx in (-0.1, 0.1):
        for sy in (-0.22, 0.22):
            rod(part, "rusty_metal", V(x_center + sx, y_center + sy, 0.0), V(x_center + sx, y_center + sy, 0.12), 0.01, 5)
    lump(part, "soot", V(x_center, y_center, 0.145), (0.1, 0.2, 0.035), rng, 0.3, 1)
    if logs:
        for index in range(3):
            a = V(x_center - 0.05, y_center - 0.18 + index * 0.12, 0.18)
            emit(part, kit.geo_tube([a, a + V(0.06, 0.2, 0.03)], kit.circle(0.035, 7), True), "timber_charred", None, "given", True)


def ladder_stair(build, part, start, forward, width, rise, run, steps, rng, name="timber_beam", tread="timber_planks_weathered", surface="wood", tag="stair", ramp_dir="ny", broken=()):
    side = V(-forward.y, forward.x, 0.0)
    for sign in (-1.0, 1.0):
        a = start + side * (sign * (width * 0.5 + 0.025))
        b = a + forward * run + V(0.0, 0.0, rise)
        direction = (b - a).normalized()
        emit(part, kit.geo_cbox((b - a).length + 0.25, 0.05, 0.16, 0.01), name, kit.place((a + b) * 0.5 + V(0.0, 0.0, 0.03), direction, V(0.0, 0.0, 1.0)), "box")
    going = run / steps
    for index in range(steps):
        if index in broken:
            continue
        top = start.z + rise * (index + 1) / steps
        center = start + forward * (going * (index + 0.5)) + V(0.0, 0.0, top - start.z - 0.02)
        emit(part, kit.geo_cbox(width, going * 0.9, 0.035, 0.005), tread, kit.place(center, side, V(0.0, 0.0, 1.0)), "board")
    low = start - side * (width * 0.5 + 0.06)
    high = start + side * (width * 0.5 + 0.06) + forward * run + V(0.0, 0.0, rise)
    lo, hi = kit.box_between(low, high)
    build.ramp(ramp_dir, surface, tag, lo, hi)


def hanging_net(part, top_a, top_b, drop, rng, name="rope_net"):
    span = top_b - top_a
    count = max(2, int(span.length / 0.28))
    for index in range(count):
        hook = top_a.lerp(top_b, (index + 0.5) / count)
        length = drop * rng.uniform(0.7, 1.0)
        path = []
        scales = []
        steps = 7
        for step in range(steps + 1):
            t = step / steps
            sway = V(rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), 0.0)
            path.append(hook + V(0.0, 0.0, -length * t) + sway * t * 3.0)
            scales.append(0.25 + 1.0 * math.sin(math.pi * min(t * 1.15, 1.0)) ** 0.7 + rng.uniform(-0.1, 0.1))
        emit(part, kit.geo_tube(path, kit.circle(0.085, 8, rng.uniform(0, 1)), True, V(1.0, 0.0, 0.0), scales), name, None, "given", True)
        rod(part, "rusty_metal", hook + V(0.0, 0.0, 0.06), hook - V(0.0, 0.0, 0.05), 0.005, 4)
        if rng.random() < 0.5:
            glass_float(part, path[-2] + V(0.07, 0.03, 0.0), rng, 0.06)
    rod(part, "hay", top_a, top_b, 0.009, 5)


def glass_float(part, position, rng, radius=0.07):
    emit(part, kit.geo_lathe([(0.0, -radius)] + [(radius * math.sin(math.pi * t / 6), -radius * math.cos(math.pi * t / 6)) for t in range(1, 6)] + [(0.0, radius)], 10), "glass_dirty", kit.Matrix.Translation(position), "given", True)


def net_heap(part, center, size3, rng, name="rope_net", floats=True):
    lump(part, name, center + V(0.0, 0.0, size3[2] * 0.35), (size3[0] * 0.5, size3[1] * 0.5, size3[2] * 0.6), rng, 0.3, 2, center.z)
    if floats:
        for index in range(rng.randint(1, 3)):
            angle = rng.uniform(0, tau)
            glass_float(part, center + V(math.cos(angle) * size3[0] * 0.3, math.sin(angle) * size3[1] * 0.3, size3[2] * 0.55), rng)


def crab_pot(part, center, yaw, rng, net="rope_net", wood="timber_beam", base="timber_planks_weathered"):
    matrix = kit.turned(center, yaw)
    local_block(part, base, matrix, -0.3, 0.3, -0.22, 0.22, 0.0, 0.025, 0.003, "board")
    for index in range(3):
        x = -0.24 + 0.48 * index / 2
        arc = [V(x, -0.2 * math.cos(math.pi * t / 8), 0.02 + 0.28 * math.sin(math.pi * t / 8)) for t in range(9)]
        emit(part, kit.geo_tube(arc, kit.circle(0.008, 5), True, V(1.0, 0.0, 0.0)), wood, matrix, "given", True)
    emit(part, kit.geo_lump(0.29, 0.2, 0.28, rng, 2, 0.04, 0.0), net, matrix @ kit.Matrix.Translation(V(0.0, 0.0, 0.02)), "box", True)
    emit(part, kit.geo_lathe([(0.07, 0.0), (0.05, 0.08), (0.045, 0.09), (0.065, 0.01)], 10), wood, matrix @ kit.Matrix.Translation(V(0.0, 0.0, 0.22)), "given", True)


def oar(part, a, b, rng, name="timber_beam"):
    direction = (b - a).normalized()
    length = (b - a).length
    blade_start = a + direction * (length * 0.7)
    rod(part, name, a, blade_start, 0.022, 7)
    emit(part, kit.geo_cbox(length * 0.3, 0.14, 0.018, 0.006), name, kit.place((blade_start + b) * 0.5, direction, V(0.0, 0.0, 1.0) if abs(direction.z) < 0.9 else V(1.0, 0.0, 0.0)), "box")


def rope_coil(part, center, rng, radius=0.18, turns=4, name="hay"):
    path = []
    for step in range(turns * 16 + 1):
        angle = tau * step / 16.0
        r = radius * (1.0 - 0.12 * step / (turns * 16))
        path.append(center + V(math.cos(angle) * r, math.sin(angle) * r, 0.02 + 0.018 * step / 16.0))
    emit(part, kit.geo_tube(path, kit.circle(0.014, 6), True), name, None, "given", True)


def sea_chest(build, part, center, yaw, rng, wood="timber_planks_weathered", iron="rusty_metal"):
    matrix = kit.turned(center, yaw)
    local_block(part, wood, matrix, -0.45, 0.45, -0.25, 0.25, 0.0, 0.4, 0.01, "board")
    local_block(part, wood, matrix, -0.47, 0.47, -0.27, 0.27, 0.4, 0.5, 0.015, "board")
    for x in (-0.3, 0.3):
        local_block(part, iron, matrix, x - 0.02, x + 0.02, -0.275, 0.275, 0.0, 0.505)
    for sign in (-1.0, 1.0):
        rod(part, iron, matrix @ V(sign * 0.46, -0.08, 0.3), matrix @ V(sign * 0.46, 0.08, 0.3), 0.01, 5)
    footprint(build, "wood", "chest", matrix, 0.47, 0.27, 0.0, 0.5)


def crate(part, center, size3, yaw, rng, name="timber_planks_weathered", broken=False):
    matrix = kit.turned(center, yaw)
    sx, sy, sz = size3
    slats = 3
    for side in (-1.0, 1.0):
        for index in range(slats):
            if broken and rng.random() < 0.3:
                continue
            z0 = sz * index / slats + 0.005
            z1 = sz * (index + 1) / slats - 0.01
            local_block(part, name, matrix, -sx * 0.5, sx * 0.5, side * sy * 0.5 - 0.009, side * sy * 0.5 + 0.009, z0, z1, 0.002, "board")
            local_block(part, name, matrix @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Z'), -sy * 0.5, sy * 0.5, side * sx * 0.5 - 0.009, side * sx * 0.5 + 0.009, z0, z1, 0.002, "board")
    local_block(part, name, matrix, -sx * 0.5, sx * 0.5, -sy * 0.5, sy * 0.5, 0.0, 0.015, 0.0, "board")
    for x in (-sx * 0.5 + 0.03, sx * 0.5 - 0.03):
        for y in (-sy * 0.5 + 0.03, sy * 0.5 - 0.03):
            local_block(part, name, matrix, x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, sz, 0.002)


def sack(part, center, rng, name="fabric_worn", scale=1.0):
    lump(part, name, center + V(0.0, 0.0, 0.18 * scale), (0.24 * scale, 0.18 * scale, 0.22 * scale), rng, 0.15, 2, center.z)
    lump(part, name, center + V(0.0, 0.0, 0.42 * scale), (0.07 * scale, 0.06 * scale, 0.06 * scale), rng, 0.2, 1)


def books(part, start, direction, length, rng, name="fabric_worn"):
    travelled = 0.0
    depth_axis = V(-direction.y, direction.x, 0.0)
    while travelled < length - 0.03:
        w = rng.uniform(0.025, 0.05)
        h = rng.uniform(0.17, 0.25)
        d = rng.uniform(0.12, 0.17)
        center = start + direction * (travelled + w * 0.5) + depth_axis * (d * 0.5) + V(0.0, 0.0, h * 0.5)
        emit(part, kit.geo_cbox(w, d, h, 0.003), name if rng.random() < 0.7 else "wallpaper_faded", kit.place(center, direction, V(0.0, 0.0, 1.0)) @ kit.Matrix.Rotation(rng.uniform(-0.12, 0.12) if rng.random() < 0.3 else 0.0, 4, 'Y'), "box")
        travelled += w + 0.003


def shelf(part, a, b, depth, inward, rng, name="timber_planks_weathered", bracket="rusty_metal"):
    direction = (b - a).normalized()
    length = (b - a).length
    center = (a + b) * 0.5 + inward * (depth * 0.5) - V(0.0, 0.0, 0.0125)
    emit(part, kit.geo_cbox(length, depth, 0.025, 0.004), name, kit.place(center, direction, V(0.0, 0.0, 1.0)), "board")
    for t in (0.12, 0.88):
        p = a.lerp(b, t)
        block(part, bracket, p + inward * 0.0 + direction * -0.012 + V(0.0, 0.0, -0.2), p + inward * (depth * 0.85) + direction * 0.012 + V(0.0, 0.0, -0.025))


def armchair(build, part, center, yaw, rng, name="fabric_worn", legs="timber_beam"):
    base = kit.turned(center, yaw)
    for sx in (-0.3, 0.3):
        for sy in (-0.3, 0.3):
            local_block(part, legs, base, sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.12, 0.005)
    emit(part, cushion_geo(0.78, 0.74, 0.24, rng, 0.02), name, base @ kit.Matrix.Translation(V(0.0, 0.0, 0.24)), "box", True)
    emit(part, cushion_geo(0.58, 0.56, 0.14, rng, 0.05, 0.02), name, base @ kit.Matrix.Translation(V(0.02, -0.04, 0.41)), "box", True)
    emit(part, cushion_geo(0.74, 0.62, 0.2, rng, 0.03), name, base @ kit.Matrix.Translation(V(0.0, 0.32, 0.68)) @ kit.Matrix.Rotation(math.pi * 0.5 - 0.18, 4, 'X'), "box", True)
    for sx in (-1.0, 1.0):
        emit(part, cushion_geo(0.14, 0.7, 0.3, rng, 0.03), name, base @ kit.Matrix.Translation(V(sx * 0.33, 0.0, 0.5)), "box", True)
    lump(part, "mattress", base @ V(0.1, -0.2, 0.47), (0.08, 0.06, 0.04), rng, 0.4, 1)
    footprint(build, "fabric", "armchair", base, 0.4, 0.38, 0.0, 0.5)


def stone_sink(build, part, clutter, center, yaw, rng, width=0.9, depth=0.55):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    for x in (-hw + 0.05, hw - 0.25):
        local_block(part, "brick_red", base, x, x + 0.2, -hd + 0.05, hd, 0.0, 0.62, 0.004)
    local_block(part, "granite_ashlar", base, -hw, hw, -hd, hd, 0.62, 0.66, 0.01)
    local_block(part, "granite_ashlar", base, -hw, -hw + 0.06, -hd, hd, 0.66, 0.86, 0.01)
    local_block(part, "granite_ashlar", base, hw - 0.06, hw, -hd, hd, 0.66, 0.86, 0.01)
    local_block(part, "granite_ashlar", base, -hw + 0.06, hw - 0.06, -hd, -hd + 0.06, 0.66, 0.86, 0.01)
    local_block(part, "granite_ashlar", base, -hw + 0.06, hw - 0.06, hd - 0.06, hd, 0.66, 0.86, 0.01)
    pump = base @ kit.Matrix.Translation(V(0.0, hd - 0.1, 0.86))
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.06, 0.0), (0.055, 0.05), (0.05, 0.5), (0.06, 0.52), (0.06, 0.56), (0.0, 0.57)], 12), "rusty_metal", pump, "given", True)
    emit(part, kit.geo_tube([V(0.0, 0.0, 0.34), V(0.0, -0.12, 0.34), V(0.0, -0.16, 0.28)], kit.circle(0.02, 8), True), "rusty_metal", pump, "given", True)
    emit(part, kit.geo_tube([V(0.0, 0.0, 0.56), V(0.05, 0.05, 0.64), V(0.35, 0.1, 0.6)], kit.circle(0.014, 6), True), "rusty_metal", pump, "given", True)
    footprint(build, "rock", "sink", base, hw, hd, 0.0, 0.86)


def hay_bale(part, center, yaw, rng, size3=(0.9, 0.45, 0.36), name="hay", twine="rope_net", roll=0.0):
    matrix = kit.turned(center + V(0.0, 0.0, size3[2] * 0.5), yaw) @ kit.Matrix.Rotation(roll, 4, 'X')
    emit(part, kit.geo_cbox(size3[0], size3[1], size3[2], 0.035), name, matrix, "box")
    for x in (-size3[0] * 0.25, size3[0] * 0.25):
        emit(part, kit.geo_box(0.012, size3[1] + 0.006, size3[2] + 0.006), twine, matrix @ kit.Matrix.Translation(V(x, 0.0, 0.0)), "box")


def barrel(build, part, center, rng, radius=0.3, height=0.9, wood="timber_planks_weathered", iron="rusty_metal", water=True):
    profile = [(radius * 0.86, 0.0), (radius * 0.97, height * 0.2), (radius, height * 0.5), (radius * 0.97, height * 0.8), (radius * 0.86, height), (radius * 0.8, height), (radius * 0.8, height - 0.04)]
    emit(part, kit.geo_lathe(profile, 18, 0.0, True), wood, kit.Matrix.Translation(center), "given", True)
    for z in (height * 0.12, height * 0.38, height * 0.62, height * 0.88):
        r = radius * (0.86 + 0.14 * math.sin(math.pi * z / height)) + 0.004
        emit(part, kit.geo_lathe([(r, z - 0.02), (r + 0.004, z - 0.02), (r + 0.004, z + 0.02), (r, z + 0.02)], 18), iron, kit.Matrix.Translation(center), "given", True)
    if water:
        emit(part, kit.geo_lathe([(0.0, height - 0.12), (radius * 0.81, height - 0.12)], 18), "glass_dirty", kit.Matrix.Translation(center), "given", True)
    build.col("wood", "barrel", center + V(-radius, -radius, 0.0), center + V(radius, radius, height))


def anchor(part, foot, top, rng, name="rusty_metal"):
    axis = (top - foot).normalized()
    side = axis.cross(V(0.0, 0.0, 1.0))
    if side.length < 1e-4:
        side = V(1.0, 0.0, 0.0)
    side.normalize()
    rod(part, name, foot, top, 0.025, 8)
    length = (top - foot).length
    arms = []
    for sign in (-1.0, 1.0):
        path = [foot, foot + side * (sign * length * 0.18) + axis * (length * 0.02), foot + side * (sign * length * 0.3) + axis * (length * 0.14), foot + side * (sign * length * 0.33) + axis * (length * 0.27)]
        emit(part, kit.geo_tube(path, kit.circle(0.022, 7), True), name, None, "given", True)
        tip = path[-1]
        normal = axis.cross(side)
        points = [tip + axis * 0.1, tip - axis * 0.08 + side * (sign * 0.07), tip - axis * 0.08 - side * (sign * 0.07)]
        emit(part, solid([p + normal * 0.006 for p in points] + [p - normal * 0.006 for p in points], [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]), name, None, "box")
    stock_center = top - axis * (length * 0.08)
    cross_axis = axis.cross(side).normalized()
    rod(part, name, stock_center - cross_axis * (length * 0.3), stock_center + cross_axis * (length * 0.3), 0.02, 7)
    ring = [top + axis * 0.06 + (side * math.cos(tau * t / 12) + axis * math.sin(tau * t / 12)) * 0.06 for t in range(13)]
    emit(part, kit.geo_tube(ring, kit.circle(0.01, 5), False), name, None, "given", True)


def log_pile(build, part, x0, x1, y_wall, outward, rng, rows=4, name="timber_beam", length=0.4):
    radius = 0.075
    for row in range(rows):
        count = int((x1 - x0) / (radius * 2.0)) - (row % 2)
        for index in range(count):
            if row == rows - 1 and rng.random() < 0.35:
                continue
            r = radius * rng.uniform(0.75, 1.1)
            x = x0 + radius * (1 + (row % 2)) + index * radius * 2.0
            z = -0.1 + radius + row * radius * 1.74
            l = length * rng.uniform(0.85, 1.1)
            start = V(x, y_wall + outward * 0.03, z)
            emit(part, kit.geo_tube([start, start + V(0.0, outward * l, rng.uniform(-0.01, 0.01))], kit.circle(r, 8, rng.uniform(0, 1)), True), name, None, "given", True)
    build.col("wood", "logs", V(x0, min(y_wall, y_wall + outward * length), -0.1), V(x1, max(y_wall, y_wall + outward * length), -0.1 + rows * radius * 1.74 + radius))


def long_tool(part, foot, top, kind, rng, wood="timber_beam", iron="rusty_metal"):
    axis = (top - foot).normalized()
    rod(part, wood, foot + axis * 0.25, top, 0.016, 7)
    side = axis.cross(V(0.0, 0.0, 1.0))
    if side.length < 1e-3:
        side = V(1.0, 0.0, 0.0)
    side.normalize()
    normal = axis.cross(side).normalized()
    if kind == "spade":
        emit(part, kit.geo_cbox(0.3, 0.2, 0.006, 0.002), iron, kit.place(foot + axis * 0.15, axis, normal), "box")
    elif kind == "fork":
        for t in (-0.075, -0.025, 0.025, 0.075):
            rod(part, iron, foot + side * t, foot + axis * 0.3 + side * t * 0.6, 0.005, 4)
        rod(part, iron, foot + axis * 0.3 - side * 0.05, foot + axis * 0.3 + side * 0.05, 0.007, 4)
    elif kind == "rake":
        rod(part, iron, foot - side * 0.2 + axis * 0.25, foot + side * 0.2 + axis * 0.25, 0.008, 5)
        for index in range(9):
            p = foot + side * (-0.2 + 0.05 * index) + axis * 0.25
            rod(part, iron, p, p + normal * 0.07, 0.003, 4)
    elif kind == "scythe":
        path = [top - axis * 0.05, top + normal * 0.15 + side * 0.25, top + normal * 0.2 + side * 0.6, top + normal * 0.12 + side * 0.85]
        emit(part, kit.geo_tube(path, [(-0.002, -0.035), (0.002, -0.035), (0.002, 0.02), (-0.002, 0.02)], True, axis, [1.0, 1.0, 0.7, 0.15]), iron, None, "given")
    elif kind == "hoe":
        emit(part, kit.geo_box(0.012, 0.16, 0.12), iron, kit.place(foot + axis * 0.25 + normal * 0.06, axis, normal), "box")
    elif kind == "broom":
        lump(part, "hay", foot + axis * 0.15, (0.13, 0.06, 0.16), rng, 0.2, 1)


def base_weeds(part, x0, x1, y0, y1, rng, density=1.0, avoid=None, ferns=0.1, nettles=0.2, z=-0.1):
    perimeter = []
    step = 0.35 / max(density, 0.05)
    x = x0
    while x <= x1:
        perimeter.append((V(x, y0, 0.0), V(0.0, -1.0, 0.0)))
        perimeter.append((V(x, y1, 0.0), V(0.0, 1.0, 0.0)))
        x += step * rng.uniform(0.6, 1.4)
    y = y0
    while y <= y1:
        perimeter.append((V(x0, y, 0.0), V(-1.0, 0.0, 0.0)))
        perimeter.append((V(x1, y, 0.0), V(1.0, 0.0, 0.0)))
        y += step * rng.uniform(0.6, 1.4)
    for p, out in perimeter:
        if avoid is not None and avoid(p):
            continue
        position = p + out * rng.uniform(0.04, 0.3) + V(0.0, 0.0, z)
        roll = rng.random()
        if roll < nettles:
            kit.nettle(part, position, rng)
        elif roll < nettles + ferns:
            kit.fern(part, position, rng)
        else:
            kit.grass_tuft(part, position, rng, (0.15, 0.45), (6, 14), 0.1)


def damp_band(part, frame, a0, a1, rng, low=0.35, high=0.95, name="granite_rubble_damp", z_base=-0.2, t=0.003, gaps=()):
    edges = [a0]
    for g0, g1 in sorted(gaps):
        edges += [max(a0, min(a1, g0)), max(a0, min(a1, g1))]
    edges.append(a1)
    for s0, s1 in zip(edges[0::2], edges[1::2]):
        if s1 - s0 < 0.4:
            continue
        points = [(s0, z_base), (s0, rng.uniform(low, high))]
        a = s0 + rng.uniform(0.15, 0.4)
        while a < s1 - 0.15:
            points.append((a, rng.uniform(low, high)))
            a += rng.uniform(0.15, 0.45)
        points.append((s1, rng.uniform(low, high)))
        points.append((s1, z_base))
        smoothed = points[:2] + [(points[i][0], (points[i - 1][1] + points[i][1] * 2.0 + points[i + 1][1]) * 0.25) for i in range(2, len(points) - 2)] + points[-2:]
        kit.skin(part, name, frame, smoothed, [], t, 0.0, False)


def wash_panel(part, frame, a0, a1, top, rng, holes, patches=6, name="render_white", thickness=0.006, low=(0.3, 0.65)):
    outline = [(a0, rng.uniform(*low))]
    a = a0 + rng.uniform(0.2, 0.5)
    while a < a1 - 0.2:
        outline.append((a, rng.uniform(*low)))
        a += rng.uniform(0.2, 0.5)
    outline += [(a1, rng.uniform(*low)), (a1, top), (a0, top)]
    blobs = kit.scatter_patches((a0 + 0.03, a1 - 0.03, low[1] + 0.05, top - 0.03), holes, patches, (0.14, 0.5), rng, (0.5, 1.2))
    kit.skin(part, name, frame, outline, holes + blobs, thickness)


def plaster_wall(part, frame, a_low, a_high, z0, z1, openings, rng, patches=6, avoid=(), name="plaster_interior", thickness=0.015):
    inward = (frame[0], -frame[1], frame[2], -frame[3])
    notches = [(-o[1], -o[0], o[3]) for o in openings if o[2] <= z0 + 1e-6]
    holes = [kit.rect(-o[1], -o[0], o[2], o[3]) for o in openings if o[2] > z0 + 1e-6]
    outline = kit.notched(-a_high, -a_low, z0, z1, notches)
    blocked = holes + [kit.rect(n0 - 0.05, n1 + 0.05, z0, top + 0.05) for n0, n1, top in notches] + [kit.rect(-r[1], -r[0], r[2], r[3]) for r in avoid]
    blobs = kit.scatter_patches((-a_high + 0.04, -a_low - 0.04, z0 + 0.06, z1 - 0.06), blocked, patches, (0.15, 0.45), rng, (0.6, 1.3))
    kit.skin(part, name, inward, outline, holes + blobs, thickness)


def window_surround(shell, joinery, frame, w, wall_t, dressed="granite_ashlar", board="floorboards", beam="timber_beam"):
    kit.lintel_stone(shell, dressed, frame, w[0], w[1], w[3], 0.26, 0.3, 0.02, 0.18)
    kit.sill_stone(shell, dressed, frame, w[0], w[1], w[2], 0.18, 0.06, 0.09, 0.07)
    frame_block(joinery, board, frame, w[0] - 0.05, w[1] + 0.05, w[2] - 0.03, w[2] + 0.005, 0.2, wall_t + 0.03, 0.004, "board")
    frame_block(joinery, beam, frame, w[0] - 0.15, w[1] + 0.15, w[3], w[3] + 0.12, wall_t - 0.28, wall_t + 0.004, 0.006)


def roof_cols(build, gable, x0, x1, steps, surface="rock", tag="roof", sides=(-1.0, 1.0), depth=0.22):
    for side in sides:
        for index in range(steps):
            outer = gable.edge - gable.edge * index / steps
            inner = gable.edge - gable.edge * (index + 1) / steps
            y_a = gable.origin_y + side * outer
            y_b = gable.origin_y + side * inner
            build.col(surface, tag, V(x0, min(y_a, y_b), gable.under(y_a, depth)), V(x1, max(y_a, y_b), gable.top(y_b) + 0.02))


def gable_cols(build, tag, x0, x1, gable, base, parapet, steps=4, surface="rock"):
    for index in range(steps):
        z0 = base + (gable.ridge_top - base) * index / steps
        z1 = base + (gable.ridge_top - base) * (index + 1) / steps + parapet
        reach = min(gable.half, (gable.ridge_top + parapet - z0) / gable.tan)
        build.col(surface, tag, V(x0, -reach, z0), V(x1, reach, z1))


def aerial(part, base, height, rng, name="rusty_metal"):
    top = base + V(rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.08), height)
    rod(part, name, base, top, 0.016, 7)
    boom_a = top - V(0.0, 0.0, 0.05)
    boom_b = boom_a + V(-0.25, -0.85, -0.4)
    rod(part, name, boom_a, boom_b, 0.01, 6)
    for t in (0.12, 0.3, 0.48, 0.66, 0.84, 0.97):
        p = boom_a.lerp(boom_b, t)
        half = 0.3 - t * 0.12
        rod(part, name, p + V(-half, 0.0, rng.uniform(-0.03, 0.06)), p + V(half, 0.0, rng.uniform(-0.12, 0.02)), 0.005, 4)
    rod(part, name, boom_a.lerp(boom_b, 0.3), boom_a.lerp(boom_b, 0.3) + V(0.0, 0.1, -0.5), 0.003, 3)


def region_box(part, name, region_key, matrix, x0, x1, y0, y1, z0, z1, bevel=0.0):
    region = kit.catalog[name]["regions"][region_key]
    low = V(min(x0, x1), min(y0, y1), min(z0, z1))
    high = V(max(x0, x1), max(y0, y1), max(z0, z1))
    extent = high - low
    geo = kit.geo_cbox(extent.x, extent.y, extent.z, bevel) if bevel > 0.0 else kit.geo_box(extent.x, extent.y, extent.z)
    reach = max(extent.x, extent.y, extent.z)
    span = (region[1] - region[0]) * 0.84
    offset_v = kit.rng.random()
    uvs = []
    for face in geo.faces:
        corners = [geo.points[i] for i in face]
        flat = kit.project(corners, kit.newell(corners), 1.0, (0.0, 0.0))
        uvs.append([(region[0] + (region[1] - region[0]) * 0.08 + (u / reach + 0.5) * span, offset_v + v / reach * span) for u, v in flat])
    geo.uvs = uvs
    emit(part, geo, name, matrix @ kit.Matrix.Translation((low + high) * 0.5), "texture")


def picture(part, center, normal, width, height, rng, inner="wallpaper_faded", frame_name="timber_beam", tilt=0.0):
    matrix = kit.frame_matrix(kit.plane(center, normal)) @ kit.Matrix.Rotation(tilt, 4, 'Y')
    fw = 0.035
    hw = width * 0.5
    hh = height * 0.5
    local_block(part, inner, matrix, -hw + fw * 0.5, hw - fw * 0.5, -0.014, -0.004, -hh + fw * 0.5, hh - fw * 0.5)
    for x0, x1, z0, z1 in ((-hw, hw, hh - fw, hh), (-hw, hw, -hh, -hh + fw), (-hw, -hw + fw, -hh + fw, hh - fw), (hw - fw, hw, -hh + fw, hh - fw)):
        local_block(part, frame_name, matrix, x0, x1, -0.03, 0.0, z0, z1, 0.004)


def coat_rail(part, clutter, a, b, inward, rng, coats=2):
    direction = (b - a).normalized()
    emit(part, kit.geo_cbox((b - a).length, 0.02, 0.09, 0.004), "timber_beam", kit.place((a + b) * 0.5 + inward * 0.01, direction, V(0.0, 0.0, 1.0)), "box")
    count = max(2, int((b - a).length / 0.18))
    hooks = []
    for index in range(count):
        p = a.lerp(b, (index + 0.5) / count) + inward * 0.02
        rod(part, "rusty_metal", p, p + inward * 0.06 + V(0.0, 0.0, 0.03), 0.005, 4)
        hooks.append(p + inward * 0.07)
    for hook in rng.sample(hooks, min(coats, len(hooks))):
        curtain(clutter, hook - direction * 0.16, hook + direction * 0.16, rng.uniform(0.8, 1.05), rng, "fabric_worn", 1.0, False)


def chest_of_drawers(build, part, center, yaw, rng, width=0.9, depth=0.46, height=0.95, wood="floorboards", rows=4):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    t = 0.02
    local_block(part, wood, base, -hw, -hw + t, -hd, hd, 0.05, height, 0.003, "board")
    local_block(part, wood, base, hw - t, hw, -hd, hd, 0.05, height, 0.003, "board")
    local_block(part, wood, base, -hw, hw, hd - t, hd, 0.05, height, 0.0, "board")
    local_block(part, wood, base, -hw - 0.02, hw + 0.02, -hd - 0.02, hd, height, height + 0.03, 0.006, "board")
    local_block(part, wood, base, -hw, hw, -hd + 0.02, hd, 0.0, 0.08, 0.0, "board")
    span = (height - 0.1) / rows
    for row in range(rows):
        z0 = 0.09 + span * row
        z1 = z0 + span - 0.012
        pull = rng.uniform(0.05, 0.22) if rng.random() < 0.45 else 0.0
        if rng.random() < 0.15:
            local_block(part, "soot", base, -hw + t, hw - t, -hd + 0.01, -hd + 0.02, z0, z1)
            continue
        local_block(part, wood, base, -hw + t + 0.004, hw - t - 0.004, -hd - pull, -hd - pull + 0.02, z0, z1, 0.003, "board")
        if pull > 0.0:
            local_block(part, "timber_planks_weathered", base, -hw + t + 0.01, hw - t - 0.01, -hd - pull + 0.02, hd - 0.04, z0 + 0.01, z0 + 0.02)
            for sx in (-1.0, 1.0):
                local_block(part, "timber_planks_weathered", base, sx * (hw - t - 0.015) - 0.006, sx * (hw - t - 0.015) + 0.006, -hd - pull + 0.02, hd - 0.04, z0 + 0.01, z1 - 0.02)
        for sx in (-0.22, 0.22):
            emit(part, kit.geo_lathe([(0.0, 0.0), (0.014, 0.0), (0.018, 0.012), (0.0, 0.02)], 8), "rusty_metal", base @ kit.Matrix.Translation(V(sx * width, -hd - pull, (z0 + z1) * 0.5)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)
    footprint(build, "wood", "drawers", base, hw, hd, 0.0, height + 0.03)
    return base @ V(0.0, 0.0, height + 0.03)


def washstand(build, part, clutter, center, yaw, rng):
    base = kit.turned(center, yaw)
    table(part, center.x, center.y, center.z, 0.8, 0.45, 0.76, rng, "floorboards", "timber_beam", yaw)
    local_block(part, "timber_beam", base, -0.4, 0.4, 0.2, 0.225, 0.76, 0.98, 0.004)
    bowl = base @ V(-0.12, 0.0, 0.76)
    emit(clutter, plain(kit.geo_lathe([(0.0, 0.0), (0.08, 0.0), (0.17, 0.09), (0.18, 0.1), (0.165, 0.1), (0.075, 0.015), (0.0, 0.012)], 16)), "ceramic", kit.Matrix.Translation(bowl), "texture", True)
    jug(clutter, base @ V(0.2, 0.02, 0.76), rng)
    footprint(build, "wood", "washstand", base, 0.4, 0.225, 0.0, 0.76)


def sofa(build, part, center, yaw, rng, width=1.7, name="fabric_worn", legs="timber_beam"):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    for sx in (-hw + 0.08, hw - 0.08):
        for sy in (-0.3, 0.3):
            local_block(part, legs, base, sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.12, 0.005)
    emit(part, cushion_geo(width, 0.78, 0.24, rng, 0.02, 0.0, 10, 4), name, base @ kit.Matrix.Translation(V(0.0, 0.0, 0.24)), "box", True)
    seats = 3
    for index in range(seats):
        x = -hw + 0.17 + (width - 0.34) * (index + 0.5) / seats
        emit(part, cushion_geo((width - 0.34) / seats - 0.01, 0.58, 0.14, rng, 0.05, 0.03 if index != 1 else 0.06), name, base @ kit.Matrix.Translation(V(x, -0.05, 0.41)) @ kit.Matrix.Rotation(rng.uniform(-0.05, 0.05), 4, 'Z'), "box", True)
    emit(part, cushion_geo(width - 0.06, 0.62, 0.2, rng, 0.03, 0.0, 10, 4), name, base @ kit.Matrix.Translation(V(0.0, 0.33, 0.68)) @ kit.Matrix.Rotation(math.pi * 0.5 - 0.2, 4, 'X'), "box", True)
    for sx in (-1.0, 1.0):
        emit(part, cushion_geo(0.16, 0.74, 0.32, rng, 0.03), name, base @ kit.Matrix.Translation(V(sx * (hw - 0.08), 0.0, 0.5)), "box", True)
    lump(part, "mattress", base @ V(0.3, -0.18, 0.48), (0.1, 0.07, 0.04), rng, 0.4, 1)
    footprint(build, "fabric", "sofa", base, hw, 0.4, 0.0, 0.52)


def bookcase(build, part, clutter, center, yaw, rng, width=0.9, height=1.8, depth=0.28, wood="floorboards", fill=0.7):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    local_block(part, wood, base, -hw, -hw + 0.022, -hd, hd, 0.0, height, 0.003, "board")
    local_block(part, wood, base, hw - 0.022, hw, -hd, hd, 0.0, height, 0.003, "board")
    local_block(part, "timber_planks_weathered", base, -hw, hw, hd - 0.012, hd, 0.0, height)
    local_block(part, wood, base, -hw - 0.02, hw + 0.02, -hd - 0.02, hd, height, height + 0.03, 0.005, "board")
    shelves = int(height / 0.34)
    for index in range(shelves):
        z = 0.06 + index * (height - 0.08) / shelves
        local_block(part, wood, base, -hw + 0.022, hw - 0.022, -hd + 0.005, hd - 0.012, z, z + 0.022, 0.0, "board")
        if rng.random() < fill:
            start = base @ V(-hw + 0.04, hd - 0.03, z + 0.022)
            direction = (base @ V(1.0, 0.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))
            depth_axis = V(-direction.y, direction.x, 0.0)
            length = (width - 0.1) * rng.uniform(0.4, 1.0)
            books(clutter, start - depth_axis * 0.17, direction, length, rng)
    footprint(build, "wood", "bookcase", base, hw, hd, 0.0, height + 0.03)


def piano(build, part, clutter, center, yaw, rng, wood="timber_beam"):
    base = kit.turned(center, yaw)
    local_block(part, wood, base, -0.72, 0.72, -0.05, 0.3, 0.0, 1.25, 0.012)
    local_block(part, wood, base, -0.72, 0.72, -0.34, -0.05, 0.62, 0.74, 0.008)
    for sx in (-0.68, 0.68):
        local_block(part, wood, base, sx - 0.04, sx + 0.04, -0.32, -0.2, 0.0, 0.62, 0.01)
    region_box(part, "ceramic", "plain", base, -0.62, 0.62, -0.33, -0.19, 0.74, 0.756)
    for index in range(36):
        if index % 7 in (2, 6):
            continue
        x = -0.6 + index * (1.2 / 36.0) + 0.017
        if rng.random() < 0.08:
            continue
        local_block(part, "soot", base, x - 0.006, x + 0.006, -0.28, -0.19, 0.756, 0.768)
    local_block(part, wood, base, -0.66, 0.66, -0.07, -0.05, 0.76, 0.92, 0.004)
    emit(part, kit.geo_box(0.6, 0.012, 0.22), wood, base @ kit.Matrix.Translation(V(0.0, -0.1, 1.0)) @ kit.Matrix.Rotation(0.25, 4, 'X'), "box")
    emit(part, kit.geo_cbox(1.5, 0.42, 0.03, 0.008), wood, base @ kit.Matrix.Translation(V(0.0, 0.13, 1.27)) @ kit.Matrix.Rotation(-0.12, 4, 'X'), "box")
    for sx in (-0.1, 0.1):
        local_block(part, "rusty_metal", base, sx - 0.02, sx + 0.02, -0.12, -0.05, 0.03, 0.045)
    stool = base @ V(0.35, -0.85, 0.0)
    emit(clutter, kit.geo_lathe([(0.0, 0.0), (0.16, 0.0), (0.17, 0.03), (0.16, 0.06), (0.0, 0.06)], 14), "fabric_worn", kit.Matrix.Translation(stool + V(0.0, 0.0, 0.17)) @ kit.Matrix.Rotation(1.45, 4, 'Y'), "given", True)
    emit(clutter, kit.geo_tube([V(0.0, 0.0, 0.0), V(0.0, 0.0, -0.42)], kit.circle(0.03, 8), True), "timber_beam", kit.Matrix.Translation(stool + V(0.0, 0.0, 0.17)) @ kit.Matrix.Rotation(1.45, 4, 'Y'), "given", True)
    footprint(build, "wood", "piano", base @ kit.Matrix.Translation(V(0.0, -0.02, 0.0)), 0.72, 0.32, 0.0, 1.27)


def parlour_fireplace(build, part, face_center, normal, rng, width=1.3, paint="painted_wood_green", tiles="kitchen_tiles", lit=True):
    matrix = kit.frame_matrix(kit.plane(face_center, normal))
    hw = width * 0.5
    for sx in (-1.0, 1.0):
        local_block(part, paint, matrix, sx * hw, sx * (hw - 0.14), -0.05, 0.0, 0.0, 0.98, 0.006, "board")
        local_block(part, tiles, matrix, sx * (hw - 0.14), sx * 0.23, -0.018, 0.0, 0.0, 0.98)
    local_block(part, paint, matrix, -hw, hw, -0.06, 0.0, 0.98, 1.12, 0.006, "board")
    local_block(part, paint, matrix, -hw - 0.07, hw + 0.07, -0.18, 0.0, 1.12, 1.16, 0.008, "board")
    local_block(part, "rusty_metal", matrix, -0.23, 0.23, -0.03, 0.0, 0.64, 0.98, 0.004)
    local_block(part, "rusty_metal", matrix, -0.23, -0.19, -0.03, 0.0, 0.0, 0.64, 0.004)
    local_block(part, "rusty_metal", matrix, 0.19, 0.23, -0.03, 0.0, 0.0, 0.64, 0.004)
    local_block(part, "soot", matrix, -0.19, 0.19, 0.26, 0.28, 0.0, 0.64)
    local_block(part, "soot", matrix, -0.21, -0.19, 0.0, 0.28, 0.0, 0.64)
    local_block(part, "soot", matrix, 0.19, 0.21, 0.0, 0.28, 0.0, 0.64)
    local_block(part, "soot", matrix, -0.19, 0.19, 0.0, 0.28, 0.64, 0.66)
    for index in range(5):
        x = -0.16 + index * 0.08
        rod(part, "rusty_metal", matrix @ V(x, -0.02, 0.1), matrix @ V(x, -0.02, 0.3), 0.007, 5)
    local_block(part, "rusty_metal", matrix, -0.19, 0.19, -0.03, 0.2, 0.08, 0.1)
    lump(part, "soot", matrix @ V(0.0, 0.1, 0.12), (0.14, 0.08, 0.03), rng, 0.3, 1)
    local_block(part, tiles, matrix, -hw, hw, -0.45, 0.0, 0.0, 0.02)
    local_block(part, "rusty_metal", matrix, -hw + 0.05, hw - 0.05, -0.46, -0.44, 0.02, 0.1)
    if lit:
        build.light("fire", matrix @ V(0.0, 0.1, 0.25))
    return matrix


def belfast_sink(build, part, clutter, center, yaw, rng, wood="timber_planks_weathered"):
    base = kit.turned(center, yaw)
    for sx in (-0.5, 0.5):
        for sy in (-0.2, 0.2):
            local_block(part, "timber_beam", base, sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.62, 0.004)
    local_block(part, wood, base, -0.56, 0.56, -0.26, 0.26, 0.58, 0.62, 0.004, "board")
    region_box(part, "ceramic", "plain", base, -0.52, 0.1, -0.24, 0.24, 0.62, 0.66, 0.006)
    region_box(part, "ceramic", "plain", base, -0.52, -0.47, -0.24, 0.24, 0.66, 0.88, 0.008)
    region_box(part, "ceramic", "plain", base, 0.05, 0.1, -0.24, 0.24, 0.66, 0.88, 0.008)
    region_box(part, "ceramic", "plain", base, -0.47, 0.05, -0.24, -0.19, 0.66, 0.88, 0.008)
    region_box(part, "ceramic", "plain", base, -0.47, 0.05, 0.19, 0.24, 0.66, 0.88, 0.008)
    emit(part, kit.geo_cbox(0.46, 0.48, 0.03, 0.004), wood, base @ kit.Matrix.Translation(V(0.34, 0.0, 0.86)) @ kit.Matrix.Rotation(-0.06, 4, 'Y'), "board")
    for index in range(6):
        local_block(part, wood, base, 0.14 + index * 0.075, 0.17 + index * 0.075, -0.22, 0.22, 0.875, 0.885)
    for sx in (-0.3, -0.12):
        emit(part, kit.geo_tube([base @ V(sx, 0.3, 1.12), base @ V(sx, 0.2, 1.12), base @ V(sx, 0.16, 1.06)], kit.circle(0.012, 6), True), "rusty_metal", None, "given", True)
        rod(part, "rusty_metal", base @ V(sx - 0.03, 0.2, 1.15), base @ V(sx + 0.03, 0.2, 1.15), 0.006, 4)
    curtain(clutter, base @ V(-0.52, -0.27, 0.57), base @ V(0.52, -0.27, 0.57), 0.5, rng, "fabric_worn", 0.7)
    footprint(build, "wood", "sink", base, 0.56, 0.26, 0.0, 0.88)


def balustrade(build, part, a, b, rng, height=0.92, spacing=0.12, wood="timber_beam", paint="painted_wood_green", missing=0.1, newels=(True, True), collide=True, tag="rail"):
    axis = b - a
    flat_length = math.hypot(axis.x, axis.y)
    direction = axis.normalized()
    up = V(0.0, 0.0, 1.0)
    emit(part, kit.geo_cbox(axis.length + 0.04, 0.06, 0.05, 0.012), wood, kit.place((a + b) * 0.5 + up * height, direction, up), "box")
    count = max(2, int(flat_length / spacing))
    for index in range(1, count):
        if rng.random() < missing:
            continue
        p = a.lerp(b, index / count)
        lean = V(rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0.0) if rng.random() < 0.12 else V(0.0, 0.0, 0.0)
        top = p + up * (height - 0.025) + lean
        emit(part, kit.geo_box((top - p).length, 0.028, 0.028), paint, kit.place((p + top) * 0.5, (top - p).normalized(), direction if abs(direction.z) < 0.9 else V(1.0, 0.0, 0.0)), "board")
    for use, p in zip(newels, (a, b)):
        if use:
            block(part, wood, p + V(-0.045, -0.045, 0.0), p + V(0.045, 0.045, height + 0.14), 0.008)
            emit(part, kit.geo_lathe([(0.0, 0.0), (0.05, 0.0), (0.06, 0.03), (0.03, 0.07), (0.0, 0.08)], 8), wood, kit.Matrix.Translation(p + up * (height + 0.14)), "given", True)
    if collide and abs(axis.z) < 0.05:
        low, high = kit.box_between(a - V(0.035, 0.035, 0.0), b + V(0.035, 0.035, 0.0))
        build.col("wood", tag, low, V(high.x, high.y, max(a.z, b.z) + height + 0.03))


def laths(part, origin, u_axis, v_axis, u0, u1, v0, v1, rng, name="timber_planks_weathered", width=0.03, gap=0.014, thick=0.008, missing=0.08):
    normal = u_axis.cross(v_axis).normalized()
    v = v0
    while v < v1 - width:
        if rng.random() > missing:
            start = u0 + rng.uniform(0.0, 0.06)
            end = u1 - rng.uniform(0.0, 0.06)
            center = origin + u_axis * ((start + end) * 0.5) + v_axis * (v + width * 0.5)
            emit(part, kit.geo_box(end - start, width, thick), name, kit.place(center, u_axis, normal), "board")
        v += width + gap


def paper_peel(part, frame, a, top, width, length, rng, name="wallpaper_faded", back="plaster_interior", curl=0.22):
    origin, along, up, normal = frame
    steps = 7
    front = []
    for index in range(steps + 1):
        t = index / steps
        out = curl * t * t * rng.uniform(0.85, 1.15)
        drop = length * (t - 0.18 * t * t * t)
        roll = 0.06 * math.sin(t * 4.0) * t
        for edge in (0.0, 1.0):
            front.append(origin + along * (a + width * edge + (0.03 * t if edge else -0.02 * t)) + up * (top - drop + roll) + normal * (0.004 + out + 0.02 * edge * t))
    faces = []
    for index in range(steps):
        i = index * 2
        faces.append((i, i + 1, i + 3, i + 2))
    emit(part, kit.Geo(list(front), [kit.orient(f, front, normal) for f in faces], None), name, None, "world")
    emit(part, kit.Geo(list(front), [kit.orient(f, front, -normal) for f in faces], None), back, None, "world")


def wheel_spoked(part, center, axis, radius, rng, spokes=12, rim="timber_beam", tyre="rusty_metal", hub_radius=0.09, width=0.07, thin=False):
    axis = axis.normalized()
    side = axis.orthogonal().normalized()
    other = axis.cross(side)
    ring = [center + (side * math.cos(tau * t / 24) + other * math.sin(tau * t / 24)) * radius for t in range(25)]
    if thin:
        emit(part, kit.geo_tube(ring, kit.circle(0.016, 6), False, axis), "soot", None, "given", True)
        emit(part, kit.geo_tube([center + (side * math.cos(tau * t / 24) + other * math.sin(tau * t / 24)) * (radius - 0.022) for t in range(25)], kit.circle(0.008, 5), False, axis), tyre, None, "given", True)
    else:
        profile = [(-0.04, -width * 0.5), (0.04, -width * 0.5), (0.04, width * 0.5), (-0.04, width * 0.5)]
        emit(part, kit.geo_tube(ring, profile, False, axis), rim, None, "given")
        emit(part, kit.geo_tube([center + (side * math.cos(tau * t / 24) + other * math.sin(tau * t / 24)) * (radius + 0.045) for t in range(25)], [(-0.006, -width * 0.55), (0.006, -width * 0.55), (0.006, width * 0.55), (-0.006, width * 0.55)], False, axis), tyre, None, "given")
    hub = kit.place(center, axis, side)
    emit(part, kit.geo_lathe([(0.0, -width * 0.9), (hub_radius * 0.6, -width * 0.9), (hub_radius, -width * 0.3), (hub_radius, width * 0.3), (hub_radius * 0.6, width * 0.9), (0.0, width * 0.9)], 10), tyre if thin else rim, hub @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)
    for index in range(spokes):
        angle = tau * index / spokes + 0.13
        outward = side * math.cos(angle) + other * math.sin(angle)
        a = center + outward * hub_radius * 0.8
        b = center + outward * (radius - (0.02 if thin else 0.035))
        if thin:
            emit(part, kit.geo_tube([a, b], kit.circle(0.002, 3), False), tyre, None, "given", True)
        else:
            emit(part, kit.geo_box((b - a).length, 0.05, 0.035), rim, kit.place((a + b) * 0.5, outward, axis), "box")


def bicycle(part, position, yaw, lean, rng, name="rusty_metal"):
    matrix = kit.Matrix.Translation(position) @ kit.Matrix.Rotation(yaw, 4, 'Z') @ kit.Matrix.Rotation(lean, 4, 'X')

    def at(x, y, z):
        return matrix @ V(x, y, z)

    axis = (at(0.0, 1.0, 0.0) - at(0.0, 0.0, 0.0))
    for x in (-0.52, 0.54):
        wheel_spoked(part, at(x, 0.0, 0.34), axis, 0.33, rng, 14, name, name, 0.025, 0.04, True)
    tubes = [((0.0, 0.0, 0.3), (-0.13, 0.0, 0.84)), ((-0.13, 0.0, 0.84), (0.4, 0.0, 0.86)), ((0.42, 0.0, 0.74), (0.0, 0.0, 0.3)), ((0.0, 0.0, 0.3), (-0.52, 0.0, 0.34)), ((-0.13, 0.0, 0.8), (-0.52, 0.0, 0.34)), ((0.4, 0.0, 0.9), (0.44, 0.0, 0.7)), ((0.44, 0.0, 0.7), (0.54, 0.0, 0.34)), ((0.4, 0.0, 0.9), (0.38, 0.0, 1.0)), ((-0.13, 0.0, 0.84), (-0.15, 0.0, 0.93))]
    for a, c in tubes:
        rod(part, name, at(*a), at(*c), 0.013, 6)
    bar = [at(0.28, -0.2, 0.96), at(0.36, -0.22, 1.0), at(0.38, 0.0, 1.0), at(0.36, 0.22, 1.0), at(0.28, 0.2, 0.96)]
    emit(part, kit.geo_tube(bar, kit.circle(0.011, 6), True), name, None, "given", True)
    lump(part, "fabric_worn", at(-0.17, 0.0, 0.95), (0.13, 0.07, 0.035), rng, 0.15, 1)
    emit(part, kit.geo_lathe([(0.0, -0.004), (0.09, -0.004), (0.09, 0.004), (0.0, 0.004)], 12), name, matrix @ kit.Matrix.Translation(V(0.0, 0.045, 0.3)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)
    rod(part, name, at(0.0, -0.06, 0.3), at(0.0, 0.06, 0.3), 0.012, 6)
    rod(part, name, at(0.0, 0.06, 0.3), at(0.1, 0.07, 0.17), 0.008, 5)
    rod(part, name, at(0.0, -0.06, 0.3), at(-0.1, -0.07, 0.43), 0.008, 5)
    for p in ((0.1, 0.11, 0.17), (-0.1, -0.11, 0.43)):
        emit(part, kit.geo_box(0.09, 0.07, 0.02), name, matrix @ kit.Matrix.Translation(V(*p)), "box")
    arc = [at(-0.52 + 0.36 * math.cos(math.pi * (0.15 + 0.7 * t / 8)), 0.0, 0.34 + 0.36 * math.sin(math.pi * (0.15 + 0.7 * t / 8))) for t in range(9)]
    emit(part, kit.geo_tube(arc, [(-0.002, -0.025), (0.002, -0.025), (0.002, 0.025), (-0.002, 0.025)], True, axis), name, None, "given")


def dustbin(part, position, rng, fallen_lid=True, name="corrugated_rusty"):
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.2, 0.0), (0.24, 0.62), (0.235, 0.62), (0.195, 0.01), (0.0, 0.01)], 16), name, kit.turned(position, rng.uniform(0, tau)), "given", True)
    lid = position + (V(rng.uniform(0.3, 0.5), rng.uniform(-0.3, 0.3), 0.02) if fallen_lid else V(0.0, 0.0, 0.62))
    emit(part, kit.geo_lathe([(0.0, 0.05), (0.06, 0.05), (0.24, 0.0), (0.26, 0.0), (0.26, -0.02), (0.24, -0.015), (0.0, 0.03)], 16), name, kit.turned(lid, 0.0, 0.0 if not fallen_lid else 0.12), "given", True)


def suitcase(part, position, yaw, rng, opened=False, name="fabric_worn"):
    base = kit.turned(position, yaw)
    if opened:
        local_block(part, name, base, -0.3, 0.3, -0.2, 0.2, 0.0, 0.09, 0.012)
        emit(part, kit.geo_cbox(0.6, 0.4, 0.08, 0.012), name, base @ kit.Matrix.Translation(V(0.0, 0.22, 0.25)) @ kit.Matrix.Rotation(1.35, 4, 'X'), "box")
        lump(part, "fabric_tartan", base @ V(0.0, 0.0, 0.11), (0.24, 0.16, 0.06), rng, 0.3, 2)
    else:
        local_block(part, name, base, -0.3, 0.3, -0.2, 0.2, 0.0, 0.18, 0.015)
        for sx in (-0.18, 0.18):
            local_block(part, "rusty_metal", base, sx - 0.015, sx + 0.015, -0.203, 0.203, -0.002, 0.183)
        emit(part, kit.geo_tube([base @ V(-0.07, -0.2, 0.09), base @ V(-0.06, -0.24, 0.09), base @ V(0.06, -0.24, 0.09), base @ V(0.07, -0.2, 0.09)], kit.circle(0.008, 5), True, V(0.0, 0.0, 1.0)), "rusty_metal", None, "given", True)


def ceiling_frame(z):
    return (V(0.0, 0.0, z), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0), V(0.0, 0.0, -1.0))


def ceiling(part, z, x0, x1, y0, y1, rng, patches=2, holes=(), name="plaster_interior", thickness=0.02, notches=None):
    frame = ceiling_frame(z)
    blocked = [kit.rect(h[0], h[1], -h[3], -h[2]) for h in holes]
    blobs = kit.scatter_patches((x0 + 0.1, x1 - 0.1, -y1 + 0.1, -y0 - 0.1), blocked, patches, (0.2, 0.55), rng, (0.6, 1.2))
    outline = kit.rect(x0, x1, -y1, -y0) if notches is None else notches
    kit.skin(part, name, frame, outline, blocked + blobs, thickness)
    return blobs


def wall_paper(part, frame, a_low, a_high, z0, z1, openings, rng, patches=4, peels=3, name="wallpaper_faded", thickness=0.005, avoid=()):
    inward = (frame[0], -frame[1], frame[2], -frame[3])
    notches = [(-o[1], -o[0], o[3]) for o in openings if o[2] <= z0 + 1e-6]
    holes = [kit.rect(-o[1], -o[0], o[2], o[3]) for o in openings if o[2] > z0 + 1e-6]
    outline = kit.notched(-a_high, -a_low, z0, z1, notches)
    blocked = holes + [kit.rect(n0 - 0.05, n1 + 0.05, z0, top + 0.05) for n0, n1, top in notches] + [kit.rect(-r[1], -r[0], r[2], r[3]) for r in avoid]
    blobs = kit.scatter_patches((-a_high + 0.04, -a_low - 0.04, z0 + 0.3, z1 - 0.04), blocked, patches, (0.15, 0.5), rng, (0.8, 1.8))
    kit.skin(part, name, inward, outline, holes + blobs, thickness)
    for shape in blobs[:peels]:
        bounds = kit.polygon_bounds(shape)
        paper_peel(part, (inward[0] + inward[3] * thickness, inward[1], inward[2], inward[3]), bounds[0] + 0.02, bounds[2] + 0.02, max(0.12, (bounds[1] - bounds[0]) * 0.7), min(0.7, bounds[3] - bounds[2] + 0.25), rng)


def reveal_skin(part, name, frame, opening, depth, thickness=0.018):
    a0, a1, b0, b1 = opening
    frame_block(part, name, frame, a0, a0 + thickness, b0, b1, -0.0, depth)
    frame_block(part, name, frame, a1 - thickness, a1, b0, b1, -0.0, depth)
    frame_block(part, name, frame, a0, a1, b1 - thickness, b1, -0.0, depth)


def render_wall(part, frame, a0, a1, z_top, openings, rng, patches, name="render_white", thickness=0.02, big=1, low=(0.35, 0.6), top_loss=0.0, extra_holes=(), margin=0.0):
    doors = sorted(o for o in openings if o[2] <= low[1] + 0.05)
    holes = [kit.rect(o[0] - margin, o[1] + margin, o[2] - margin, o[3] + margin) for o in openings if o[2] > low[1] + 0.05]
    bottom = [(a0, rng.uniform(*low), 0)]
    a = a0 + rng.uniform(0.25, 0.6)
    while a < a1 - 0.25:
        if not any(d[0] - margin - 0.2 < a < d[1] + margin + 0.2 for d in doors):
            bottom.append((a, rng.uniform(*low), 0))
        a += rng.uniform(0.25, 0.6)
    bottom.append((a1, rng.uniform(*low), 0))
    for d in doors:
        bottom += [(d[0] - margin, low[0], 0), (d[0] - margin, d[3] + margin, 1), (d[1] + margin, d[3] + margin, 2), (d[1] + margin, low[0], 3)]
    bottom.sort(key=lambda p: (p[0], p[2]))
    outline = [(p[0], p[1]) for p in bottom] + [(a1, z_top)]
    if top_loss > 0.0:
        edge = kit.wander(rng)
        a = a1 - rng.uniform(0.12, 0.3)
        while a > a0 + 0.15:
            outline.append((a, z_top - top_loss * edge(a * 1.7) + rng.uniform(-0.03, 0.03)))
            a -= rng.uniform(0.12, 0.3)
    outline.append((a0, z_top))
    blocked = holes + [kit.rect(d[0] - margin - 0.08, d[1] + margin + 0.08, low[0], d[3] + margin + 0.08) for d in doors] + list(extra_holes)
    region = (a0 + 0.06, a1 - 0.06, low[1] + 0.1, z_top - top_loss - 0.1)
    sink = lambda r: region[2] + (region[3] - region[2]) * r.random() ** 1.9
    blobs = kit.scatter_patches(region, blocked, big, (0.55, 1.1), rng, (0.5, 0.9), sink)
    blobs += kit.scatter_patches(region, blocked + blobs, patches, (0.12, 0.5), rng, (0.45, 1.5), sink)
    kit.skin(part, name, frame, outline, holes + list(extra_holes) + blobs, thickness)
    return blobs


def cottage():
    b = kit.Build("cottage", 101)
    rng = b.rng
    shell = b.part("shell", 30.0)
    roof = b.part("roof", 50.0)
    joinery = b.part("joinery", 30.0)
    floors = b.part("floors", 30.0)
    interior = b.part("interior", 40.0)
    clutter = b.part("clutter", 45.0)
    debris = b.part("debris", 40.0)
    plants = b.part("plants", 70.0)
    hx = 4.5
    hy = 3.0
    wall_t = 0.6
    ix = hx - wall_t
    iy = hy - wall_t
    gable = kit.Gable(-ix, ix, hy, 0.22, 3.12, 42.0)
    wall_top = gable.under(hy, 0.03)
    loft = 2.45
    joist_depth = 0.16
    board_t = 0.025
    ceiling = loft - board_t
    paint = "painted_wood_blue"
    stone = "granite_rubble"
    dressed = "granite_ashlar"
    parapet = 0.16
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    door = (-0.5, 0.5, 0.0, 2.1)
    front_windows = [(-3.05, -2.15, 0.85, 2.0), (2.15, 3.05, 0.85, 2.0)]
    back_windows = [(2.1, 2.9, 1.0, 1.9), (-2.9, -2.1, 0.95, 1.95)]
    right_windows = [(1.0, 1.55, 2.85, 3.5)]
    left_windows = [(-1.55, -1.0, 2.85, 3.5)]

    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [kit.rect(door[0], door[1], -0.05, door[3])] + [kit.rect(*w) for w in front_windows], wall_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [kit.rect(*w) for w in back_windows], wall_t)
    for frame, windows in ((left, left_windows), (right, right_windows)):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.top(hy) + parapet), (0.0, gable.ridge_top + parapet), (-hy, gable.top(hy) + parapet)]
        kit.wall(shell, stone, frame, outline, [kit.rect(*w) for w in windows], wall_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, -1.5, wall_top, wall_t, [door] + front_windows)
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, -1.5, wall_top, wall_t, back_windows)
    kit.wall_boxes(b, "rock", "left", left, -hy, hy, -1.5, wall_top, wall_t, left_windows)
    kit.wall_boxes(b, "rock", "right", right, -hy, hy, -1.5, wall_top, wall_t, right_windows)
    gable_cols(b, "left_gable", -hx, -ix, gable, wall_top, parapet)
    gable_cols(b, "right_gable", ix, hx, gable, wall_top, parapet)
    for corner, ua, ub in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0))):
        kit.quoins(shell, dressed, corner, ua, ub, 0.2, gable.top(hy) + parapet - 0.02, rng)
    for frame, windows in ((front, front_windows), (back, back_windows), (left, left_windows), (right, right_windows)):
        for w in windows:
            window_surround(shell, joinery, frame, w, wall_t)
    a0, a1, b0, b1 = door
    kit.lintel_stone(shell, dressed, front, a0, a1, b1, 0.3, 0.32, 0.025, 0.12)
    kit.jamb_stones(shell, dressed, front, a0, -1.0, 0.0, b1, rng)
    kit.jamb_stones(shell, dressed, front, a1, 1.0, 0.0, b1, rng)
    frame_block(shell, dressed, front, a0 - 0.05, a1 + 0.05, -0.2, 0.0, -0.22, wall_t, 0.015)
    frame_block(joinery, "timber_beam", front, a0 - 0.2, a1 + 0.2, b1, b1 + 0.16, wall_t - 0.3, wall_t + 0.004, 0.008)
    for frame, a_low, a_high in ((front, -ix, ix), (back, -ix, ix), (left, -hy, hy), (right, -hy, hy)):
        a = a_low + (0.0 if frame in (left, right) else 0.02)
        while a < a_high - 0.15:
            w = rng.uniform(0.5, 0.95)
            if a_high - (a + w) < 0.3:
                w = a_high - a
            if not (frame is front and a + w > -1.25 and a < 1.25):
                frame_block(shell, dressed, frame, a + 0.008, a + w - 0.008, -0.5, 0.2 + rng.uniform(-0.04, 0.04), -0.04 * rng.uniform(0.7, 1.2), 0.25, 0.022)
            a += w
        damp_band(shell, frame, a_low, a_high, rng, 0.3, 0.85 if frame is not back else 1.35, gaps=[(door[0] - 0.02, door[1] + 0.02)] if frame is front else ())
    wash_top = wall_top - 0.04
    surrounds = [kit.rect(w[0] - 0.26, w[1] + 0.26, w[2] - 0.17, w[3] + 0.33) for w in front_windows]
    wash_panel(shell, front, -ix + 0.03, door[0] - 0.46, wash_top, rng, [surrounds[0]], 7)
    wash_panel(shell, front, door[1] + 0.46, ix - 0.03, wash_top, rng, [surrounds[1]], 7)
    kit.skin(shell, "render_white", front, kit.rect(door[0] - 0.46, door[1] + 0.46, 2.92, wash_top), [], 0.006)

    plaster_wall(interior, kit.facade("front", ix, iy), -ix, ix, 0.0, ceiling, [door] + front_windows, rng, 7)
    plaster_wall(interior, kit.facade("back", ix, iy), -ix, ix, 0.0, ceiling, back_windows, rng, 7)
    plaster_wall(interior, kit.facade("left", ix, hy), -iy, iy, 0.0, ceiling, [], rng, 4, [(-1.3, 1.3, 0.0, ceiling)])
    plaster_wall(interior, kit.facade("right", ix, hy), -iy, iy, 0.0, ceiling, [], rng, 4, [(-0.95, 0.95, 0.0, ceiling)])

    breast_left = (-ix, -ix + 0.6, -1.25, 1.25)
    breast_right = (ix - 0.5, ix, -0.9, 0.9)
    for breast, opening_top, tag in ((breast_left, 1.65, "breast_left"), (breast_right, 1.23, "breast_right")):
        block(shell, stone, V(breast[0], breast[2], 0.0), V(breast[1], breast[2] + 0.45, ceiling), 0.0, "world")
        block(shell, stone, V(breast[0], breast[3] - 0.45, 0.0), V(breast[1], breast[3], ceiling), 0.0, "world")
        block(shell, stone, V(breast[0], breast[2] + 0.45, opening_top), V(breast[1], breast[3] - 0.45, ceiling), 0.0, "world")
        b.col("rock", tag, V(breast[0], breast[2], 0.0), V(breast[1], breast[2] + 0.45, loft))
        b.col("rock", tag, V(breast[0], breast[3] - 0.45, 0.0), V(breast[1], breast[3], loft))
        b.col("rock", tag, V(breast[0], breast[2] + 0.45, opening_top - 0.3), V(breast[1], breast[3] - 0.45, loft))
    fire_recess(shell, breast_left[1], 0.0, 1.6, 1.35, 0.5, 1.0, rng)
    range_stove(b, interior, clutter, V(breast_left[1] - 0.5, 0.0, 0.0), 0.0, rng, 1.25, 0.5)
    fire_recess(shell, breast_right[0], 0.0, 0.9, 0.95, 0.4, -1.0, rng, lintel_beam=False)
    fire_basket(interior, breast_right[0] + 0.2, 0.0, rng)
    b.light("fire", V(breast_right[0] + 0.2, 0.0, 0.25))
    block(interior, "timber_beam", V(breast_right[0] - 0.12, breast_right[2] - 0.08, 1.28), V(breast_right[0] + 0.02, breast_right[3] + 0.08, 1.33), 0.006)
    for y in (-0.6, -0.3, 0.35):
        bottle(clutter, V(breast_right[0] - 0.06, y, 1.33), rng)
    jug(clutter, V(breast_right[0] - 0.05, 0.62, 1.33), rng)

    stack_z = gable.ridge_top + 1.0
    for x_stack in (-hx + 0.34, hx - 0.34):
        kit.chimney(roof, dressed, x_stack, 0.0, 0.68, 1.0, gable.top(0.5) - 0.3, stack_z, rng, 2)
        b.col("rock", "chimney", V(x_stack - 0.34, -0.5, gable.top(0.5) - 0.3), V(x_stack + 0.34, 0.5, stack_z + 0.12))
    for x_flue in (-ix + 0.22, ix - 0.22):
        block(shell, stone, V(x_flue - 0.23, -0.5, loft), V(x_flue + 0.23, 0.5, gable.top(0.5) - 0.2), 0.0, "world")
        b.col("rock", "flue", V(x_flue - 0.23, -0.5, loft), V(x_flue + 0.23, 0.5, gable.top(0.5)))
    kit.gable_coping(roof, dressed, gable, -hx + wall_t * 0.5, wall_t, rng, 0.12, 0.05, parapet)
    kit.gable_coping(roof, dressed, gable, hx - wall_t * 0.5, wall_t, rng, 0.12, 0.05, parapet)
    aerial(roof, V(hx - 0.02, 0.2, stack_z - 0.7), 2.3, rng)
    for z in (stack_z - 0.5, stack_z - 0.1):
        block(roof, "rusty_metal", V(hx - 0.7, -0.52, z), V(hx + 0.02, 0.52, z + 0.025))

    moss_field = kit.smooth_noise(random.Random(7), 5, 1.2)
    hole = (1.25, 1.95, 1.4, 2.05)
    kit.slate_roof(roof, gable, -1.0, rng, lambda x, d: moss_field(V(x * 0.5, d * 0.7, 0.0)) > 0.35 or (d < 0.5 and rng.random() < 0.3), lambda x, d: rng.random() < 0.006, lambda x, d: rng.uniform(0.05, 0.16) if rng.random() < 0.02 else 0.0)
    kit.slate_roof(roof, gable, 1.0, rng, lambda x, d: moss_field(V(x * 0.5, d * 0.7, 2.0)) > 0.0 or (d < 0.6 and rng.random() < 0.6), lambda x, d: (0.85 < x < 2.35 and 1.15 < d < 2.3 and rng.random() < 0.8) or rng.random() < 0.012, lambda x, d: rng.uniform(0.05, 0.16) if rng.random() < 0.03 else 0.0)
    rafter_xs = [-ix + 0.2 + i * (2 * ix - 0.4) / 16 for i in range(17)]
    for side in (-1.0, 1.0):
        kit.roof_boards(roof, gable, side, -ix, ix, 0.0, gable.run + 0.02, rng, "timber_planks_weathered", 0.022, -0.001, [hole] if side > 0 else ())
        kit.roof_rafters(roof, gable, side, rafter_xs, 0.0, gable.run - 0.02, -0.023)
        block(roof, "timber_beam", V(-ix, side * iy, wall_top - 0.02), V(ix, side * (iy + 0.16), wall_top + 0.1), 0.006)
        kit.segmented(roof, paint, gable.point(side, -ix, -0.013, -0.095), gable.point(side, ix, -0.013, -0.095), 0.025, 0.17, gable.normal(side), 1.3)
    kit.segmented(roof, "timber_beam", V(-ix, 0.0, gable.ridge_top - 0.195), V(ix, 0.0, gable.ridge_top - 0.195), 0.04, 0.33, V(0.0, 0.0, 1.0), 0.9, "box")
    for x in (-2.6, -0.9, 0.9, 2.6):
        z = 4.75
        reach = (gable.under(0.0, 0.18) - z) / gable.tan
        block(roof, "timber_beam", V(x - 0.03, -reach, z - 0.08), V(x + 0.03, reach, z + 0.08), 0.006)
    kit.ridge_tiles(roof, gable, -ix, ix, rng)
    gutter_z = kit.gutter(roof, gable, -1.0, -ix - 0.3, ix + 0.3, rng, 0.03)
    kit.gutter(roof, gable, 1.0, -ix - 0.3, ix + 0.3, rng, 0.05, broken_at=2.6)
    kit.downpipe(roof, -ix - 0.15, -gable.edge - 0.04, -hy, gutter_z - 0.03, -0.1, rng)
    kit.downpipe(roof, ix + 0.15, gable.edge + 0.04, hy, gutter_z - 0.03, -0.1, rng, broken=1.15, lean=0.05)
    roof_cols(b, gable, -hx, hx, 6)
    sag_roof = (roof, -ix, ix, gable.eave_top + 0.1, gable.ridge_top, 0.075)

    kit.flagstones(floors, dressed, -ix, 0.84, -iy, iy, 0.0, rng, (0.4, 0.7), 0.012, 0.06, 0.012, 0.005, "dirt_debris", lambda x, y: x < -ix + 0.62 and -1.3 < y < 1.3)
    kit.joists(floors, "timber_beam", 0.96, ix, -iy, iy, -0.028, "x", 0.5, 0.08, 0.14)
    kit.floor_boards(floors, "floorboards", 0.96, ix, -iy, iy, 0.0, "y", rng, width_range=(0.14, 0.19), joints=[-1.1, 0.7], holes=[(breast_right[0], ix, breast_right[2], breast_right[3]), (2.15, 2.95, -iy, -1.55)], ragged=0.25)
    block(floors, "dirt_debris", V(0.96, -iy, -0.24), V(ix, iy, -0.17))
    b.col("rock", "floor", V(-ix, -iy, -0.3), V(0.84, iy, 0.0))
    b.col("wood", "floor", V(0.84, -iy, -0.3), V(ix, iy, 0.0))
    opening = (-0.3, 0.84, -1.1, 2.0)
    kit.joists(floors, "timber_beam", -ix, ix, -iy, iy, ceiling, "y", 0.5, 0.09, joist_depth, lambda x: [(-iy, opening[2] - 0.09), (opening[3] + 0.09, iy)] if opening[0] - 0.05 < x < opening[1] else [(-iy, iy)])
    for y in (opening[2] - 0.09, opening[3]):
        block(floors, "timber_beam", V(opening[0] - 0.4, y, ceiling - joist_depth), V(0.9, y + 0.09, ceiling), 0.0)
    kit.floor_boards(floors, "floorboards", -ix, ix, -iy, iy, loft, "x", rng, width_range=(0.14, 0.2), joints=[-2.1, -1.1, 1.4, 2.4], holes=[opening, (-3.3, -2.7, 1.05, 1.5)], ragged=0.0)
    b.col("wood", "loft", V(-ix, -iy, ceiling - joist_depth), V(opening[0], iy, loft))
    b.col("wood", "loft", V(opening[1], -iy, ceiling - joist_depth), V(ix, iy, loft))
    b.col("wood", "loft", V(opening[0], -iy, ceiling - joist_depth), V(opening[1], opening[2], loft))
    b.col("wood", "loft", V(opening[0], opening[3], ceiling - joist_depth), V(opening[1], iy, loft))
    rail_x = opening[0] - 0.04
    rail_y = (-0.1, opening[3] + 0.04)
    for y in (rail_y[0] + 0.04, 0.98, rail_y[1] - 0.04):
        block(floors, "timber_beam", V(rail_x - 0.03, y - 0.03, loft), V(rail_x + 0.03, y + 0.03, loft + 0.95), 0.006)
    block(floors, "timber_beam", V(rail_x - 0.04, rail_y[0], loft + 0.9), V(rail_x + 0.04, rail_y[1], loft + 0.96), 0.006)
    block(floors, "timber_beam", V(rail_x - 0.02, rail_y[0] + 0.03, loft + 0.45), V(rail_x + 0.02, rail_y[1] - 0.03, loft + 0.49), 0.004)
    b.col("wood", "rail", V(rail_x - 0.04, rail_y[0], loft), V(rail_x + 0.04, rail_y[1], loft + 0.96))
    ladder_stair(b, floors, V(0.27, 1.35, 0.0), V(0.0, -1.0, 0.0), 0.68, loft, 2.4, 11, rng, ramp_dir="ny")
    crate(clutter, V(0.27, -0.65, 0.0), (0.62, 0.5, 0.45), 0.08, rng)
    crate(clutter, V(0.3, -0.05, 0.0), (0.55, 0.42, 0.36), -0.12, rng, broken=True)
    sack(clutter, V(0.25, 0.5, 0.0), rng)
    sack(clutter, V(0.33, -0.62, 0.45), rng, "fabric_worn", 0.8)

    partition = kit.plane(V(0.9, 0.0, 0.0), V(1.0, 0.0, 0.0))
    doorway = (-2.2, -1.25, 0.0, 2.1)
    kit.wall(interior, "plaster_interior", partition, kit.notched(-iy, iy, 0.0, ceiling, [(doorway[0], doorway[1], doorway[3])]), [], 0.12, 0.06)
    kit.wall_boxes(b, "wood", "partition", partition, -iy, iy, 0.0, ceiling, 0.12, [doorway], 0.06)
    kit.door_frame(joinery, paint, kit.plane(V(0.96, 0.0, 0.0), V(1.0, 0.0, 0.0)), doorway[0], doorway[1], 0.0, doorway[3], 0.0, 0.07, 0.12)
    for y in (0.35, 1.3):
        block(interior, "timber_beam", V(0.839, y, 0.0), V(0.961, y + 0.1, ceiling))
    kit.door_leaf(joinery, paint, kit.plane(V(0.96, 0.0, 0.0), V(1.0, 0.0, 0.0)), doorway[1] - 0.07, -1.0, 0.0, 0.01, 2.02, 0.8, -100.0, rng, hang=4.0)

    kit.door_frame(joinery, paint, front, a0 + 0.02, a1 - 0.02, 0.0, b1, 0.18)
    kit.door_leaf(joinery, paint, front, a1 - 0.09, -1.0, 0.3, 0.02, 2.02, 0.86, 96.0, rng)
    window_states = ((("open", "hang"), [0.0, 35.0]), (("missing", "ajar"), [None, 0.0]))
    for w, (shutters, leaves) in zip(front_windows, window_states):
        wa0, wa1, wb0, wb1 = w
        kit.casement_window(joinery, paint, front, wa0, wa1, wb0, wb1, 0.12, rng, leaves)
        width = (wa1 - wa0) * 0.5 + 0.02
        for leaf, hinge_a, direction in ((shutters[0], wa0 - 0.01, 1.0), (shutters[1], wa1 + 0.01, -1.0)):
            if leaf == "missing":
                continue
            angle = {"open": 172.0, "hang": 155.0, "ajar": 115.0, "closed": 0.0}[leaf]
            kit.shutter(joinery, paint, front, hinge_a, direction, wb0, wb1, width, angle, rng, "ledged", 13.0 if leaf == "hang" else 0.0)
        box_y = -hy - 0.2
        block(joinery, "timber_planks_weathered", V(wa0 - 0.05, box_y - 0.1, wb0 - 0.3), V(wa1 + 0.05, box_y + 0.1, wb0 - 0.12), 0.004, "board")
        block(joinery, "dirt_debris", V(wa0 - 0.03, box_y - 0.08, wb0 - 0.14), V(wa1 + 0.03, box_y + 0.08, wb0 - 0.125))
        for x in (wa0 + 0.05, wa1 - 0.05):
            block(joinery, "rusty_metal", V(x - 0.012, box_y + 0.08, wb0 - 0.42), V(x + 0.012, -hy, wb0 - 0.28))
        for index in range(7):
            kit.grass_tuft(plants, V(rng.uniform(wa0, wa1), box_y + rng.uniform(-0.05, 0.05), wb0 - 0.125), rng, (0.1, 0.3), (3, 7), 0.03)
    shutter_w = (front_windows[1][1] - front_windows[1][0]) * 0.5 + 0.02
    fallen = kit.Matrix.Translation(V(2.2, -hy - 0.75, -0.08)) @ kit.Matrix.Rotation(0.5, 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5 - 0.06, 4, 'X')
    for index in range(4):
        local_block(joinery, paint, fallen, shutter_w * index / 4 + 0.002, shutter_w * (index + 1) / 4 - 0.002, 0.0, 0.024, 0.0, 1.15, 0.002, "board")
    for z in (0.12, 1.03):
        local_block(joinery, paint, fallen, 0.03, shutter_w - 0.03, 0.024, 0.044, z - 0.045, z + 0.045, 0.003, "board")
    kit.casement_window(joinery, paint, back, back_windows[0][0], back_windows[0][1], back_windows[0][2], back_windows[0][3], 0.12, rng, [0.0, 0.0], 0.6, 0.25)
    bw = back_windows[1]
    kit.window_frame(joinery, paint, back, bw[0], bw[1], bw[2], bw[3], 0.12)
    for index in range(4):
        z = bw[2] + 0.12 + index * 0.24 + rng.uniform(-0.03, 0.03)
        c = kit.frame_point(back, (bw[0] + bw[1]) * 0.5, z, 0.02)
        emit(joinery, kit.geo_box(bw[1] - bw[0] + 0.34, 0.16, 0.022), "timber_planks_weathered", kit.Matrix.Translation(c) @ kit.Matrix.Rotation(rng.uniform(-0.12, 0.12), 4, 'Y') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "board")
    b.col("wood", "boards", V(-bw[1], hy, bw[2]), V(-bw[0], hy + 0.05, bw[3]))
    for frame, windows in ((left, left_windows), (right, right_windows)):
        for w in windows:
            kit.casement_window(joinery, paint, frame, w[0], w[1], w[2], w[3], 0.1, rng, [0.0], 0.2, 0.4, 2)
    curtain(clutter, V(-3.1, -iy + 0.06, 2.02), V(-2.1, -iy + 0.06, 2.02), 0.9, rng, "fabric_worn", 0.45)
    curtain(clutter, V(3.1, -iy + 0.06, 2.02), V(2.1, -iy + 0.06, 2.02), 1.1, rng, "fabric_worn", 0.4)

    porch_x = 1.2
    porch_y0 = -hy - 1.6
    lean = kit.Gable(-porch_x - 0.12, porch_x + 0.12, 1.6, 0.15, 2.94 - 1.75 * math.tan(math.radians(20.0)), 20.0, -hy)
    for sx in (-1.0, 1.0):
        x0 = sx * porch_x - (0.3 if sx > 0 else 0.0)
        block(shell, stone, V(x0, porch_y0, -1.5), V(x0 + 0.3, -hy, 0.9), 0.0, "world")
        block(shell, dressed, V(x0 - 0.03, porch_y0 - 0.03, 0.9), V(x0 + 0.33, -hy, 0.98), 0.012)
        b.col("rock", "porch", V(x0, porch_y0, -1.5), V(x0 + 0.3, -hy, 0.98))
        post = V(sx * (porch_x - 0.15), porch_y0 + 0.15, 0.98)
        block(joinery, "timber_beam", post - V(0.06, 0.06, 0.0), post + V(0.06, 0.06, 1.14), 0.008)
        a = post + V(0.0, 0.0, 0.75)
        emit(joinery, kit.geo_cbox(0.55, 0.06, 0.06, 0.006), "timber_beam", kit.place(a + V(-sx * 0.17, 0.0, 0.17), V(-sx, 0.0, 1.0), V(0.0, 1.0, 0.0)), "box")
        b.col("wood", "post", post - V(0.06, 0.06, 0.0), post + V(0.06, 0.06, 1.14))
        bench_x0 = x0 + (0.3 if sx < 0 else -0.36)
        block(interior, "timber_planks_weathered", V(bench_x0, porch_y0 + 0.3, 0.42), V(bench_x0 + 0.36, -hy - 0.1, 0.46), 0.004, "board")
        for y in (porch_y0 + 0.4, -hy - 0.25):
            block(interior, "timber_beam", V(bench_x0 + 0.02, y - 0.03, 0.0), V(bench_x0 + 0.08, y + 0.03, 0.42), 0.004)
    block(joinery, "timber_beam", V(-porch_x, porch_y0 + 0.08, 2.12), V(porch_x, porch_y0 + 0.22, 2.25), 0.008)
    kit.flagstones(floors, dressed, -porch_x + 0.3, porch_x - 0.3, porch_y0, -hy, 0.0, rng, (0.35, 0.6), 0.012, 0.08, 0.012, 0.006, "dirt_debris")
    block(floors, dressed, V(-0.85, porch_y0 - 0.38, -0.5), V(0.85, porch_y0 - 0.01, -0.16), 0.02)
    block(floors, "concrete", V(-porch_x + 0.3, porch_y0, -1.5), V(porch_x - 0.3, -hy, -0.1))
    b.col("rock", "porch_floor", V(-porch_x + 0.3, porch_y0, -1.5), V(porch_x - 0.3, -hy, 0.0))
    b.col("rock", "step", V(-0.85, porch_y0 - 0.38, -1.5), V(0.85, porch_y0, -0.16))
    kit.slate_roof(roof, lean, -1.0, rng, lambda x, d: rng.random() < 0.3, lambda x, d: rng.random() < 0.03, None)
    kit.roof_rafters(roof, lean, -1.0, [-porch_x + 0.05 + i * (2 * porch_x - 0.1) / 5 for i in range(6)], 0.0, lean.run, -0.023, "timber_beam", 0.06, 0.1)
    kit.roof_boards(roof, lean, -1.0, -porch_x - 0.12, porch_x + 0.12, 0.0, lean.run, rng)
    block(roof, "rusty_metal", V(-porch_x - 0.12, -hy - 0.07, 2.9), V(porch_x + 0.12, -hy, 2.99))
    roof_cols(b, lean, -porch_x - 0.12, porch_x + 0.12, 2, "rock", "porch_roof", (-1.0,), 0.16)
    lantern(clutter, V(-0.72, porch_y0 + 0.7, 0.46), rng)
    crab_pot(clutter, V(1.85, -hy - 0.45, -0.1), 0.2, rng)
    crab_pot(clutter, V(2.5, -hy - 0.4, -0.1), -0.3, rng)
    crab_pot(clutter, V(2.15, -hy - 0.42, 0.2), 0.05, rng)
    anchor(clutter, V(-1.75, -hy - 0.55, -0.08), V(-1.6, -hy - 0.06, 1.25), rng)
    barrel(b, clutter, V(ix + 0.15, hy + 0.42, -0.1), rng)
    for row in range(4):
        for index in range(7 - (row % 2)):
            if row == 3 and rng.random() < 0.4:
                continue
            r = 0.075 * rng.uniform(0.75, 1.1)
            y = -2.6 + 0.075 * (1 + (row % 2)) + index * 0.15
            start = V(-hx - 0.04, y, -0.1 + 0.075 + row * 0.13)
            emit(clutter, kit.geo_tube([start, start + V(-0.42 * rng.uniform(0.85, 1.1), 0.0, 0.0)], kit.circle(r, 8, rng.uniform(0, 1)), True), "timber_beam", None, "given", True)
    b.col("wood", "logs", V(-hx - 0.46, -2.62, -0.1), V(-hx, -1.5, 0.5))

    dresser(b, interior, clutter, V(-1.28, -iy + 0.23, 0.0), math.pi, rng, paint)
    b.loot("food", V(-1.28, -iy + 0.26, 0.9))
    table(interior, -1.9, 0.35, 0.0, 1.4, 0.8, 0.76, rng)
    b.col("wood", "table", V(-2.6, -0.05, 0.0), V(-1.2, 0.75, 0.76))
    chair(interior, V(-2.3, -0.28, 0.0), 0.1, rng)
    chair(interior, V(-1.4, 1.05, 0.0), math.pi + 0.3, rng)
    chair(interior, V(-1.0, 1.6, 0.0), 1.2, rng, fallen=True)
    plate(clutter, V(-2.2, 0.3, 0.76), rng, 0.12, 0.0)
    cup(clutter, V(-1.95, 0.55, 0.76), rng)
    bottle(clutter, V(-1.55, 0.25, 0.76), rng)
    bottle(clutter, V(-1.7, 0.6, 0.76), rng, True)
    lantern(clutter, V(-2.45, 0.5, 0.76), rng)
    b.loot("food", V(-1.45, 0.45, 0.76))
    lantern(clutter, V(-2.5, 1.3, 1.62), rng)
    rod(clutter, "rusty_metal", V(-2.47, 1.3, 1.9), V(-2.47, 1.3, ceiling - joist_depth), 0.004, 4)
    b.light("warm", V(-2.5, 1.3, 1.78))
    stone_sink(b, interior, clutter, V(-2.5, iy - 0.28, 0.0), 0.0, rng)
    bucket(clutter, V(-1.8, iy - 0.3, 0.0), rng)
    shelf(interior, V(-3.85, iy, 1.6), V(-3.05, iy, 1.6), 0.22, V(0.0, -1.0, 0.0), rng)
    for x in (-3.7, -3.5, -3.3):
        jar(clutter, V(x, iy - 0.11, 1.6), rng)
    tin(clutter, V(-3.13, iy - 0.1, 1.6), rng)
    for x in (-1.75, -1.45, -1.15):
        hanging_pot(clutter, V(x, -0.75, ceiling - joist_depth), rng, 0.3)
    hanging_net(clutter, V(-3.75, -2.0, ceiling - joist_depth - 0.02), V(-2.4, -1.5, ceiling - joist_depth - 0.02), 1.0, rng)
    rug(clutter, V(-1.8, 0.3, 0.06), 1.9, 1.3, 0.05, rng)
    bucket(clutter, V(-3.2, -1.2, 0.0), rng, tipped=True)
    crate(clutter, V(-3.55, -2.05, 0.0), (0.5, 0.4, 0.35), 0.1, rng)
    b.loot("toolbox", V(-2.75, -2.05, 0.0))
    b.loot("box", V(-3.45, 1.85, 0.0))
    long_tool(clutter, V(-0.3, iy - 0.08, 0.0), V(-0.22, iy - 0.02, 1.45), "broom", rng)

    table(interior, 3.45, -2.05, 0.0, 0.7, 0.5, 0.72, rng)
    oil_lamp(clutter, V(3.55, -2.05, 0.72), rng)
    b.light("warm", V(3.55, -2.05, 0.95))
    books(clutter, V(3.17, -2.15, 0.72), V(1.0, 0.0, 0.0), 0.25, rng)
    b.col("wood", "side_table", V(3.1, -2.3, 0.0), V(3.8, -1.8, 0.72))
    armchair(b, interior, V(2.75, -1.25, 0.0), 2.62, rng)
    iron_bed(b, interior, clutter, V(2.9, 1.72, 0.0), 0.0, rng)
    b.loot("medical", V(3.35, 1.72, 0.62))
    emit(clutter, plain(kit.geo_lathe([(0.0, 0.0), (0.09, 0.0), (0.11, 0.1), (0.12, 0.14), (0.1, 0.14), (0.0, 0.02)], 12)), "ceramic", kit.Matrix.Translation(V(3.2, 1.45, 0.0)), "texture", True)
    wardrobe(b, interior, clutter, V(1.27, 0.75, 0.0), math.pi * 0.5, rng)
    b.loot("box", V(1.25, -0.15, 0.0))
    rug(clutter, V(2.5, 0.0, 0.0), 1.2, 0.8, 1.57, rng)
    shelf(interior, V(1.1, iy, 1.7), V(1.9, iy, 1.7), 0.22, V(0.0, -1.0, 0.0), rng)
    books(clutter, V(1.15, iy - 0.2, 1.7), V(1.0, 0.0, 0.0), 0.4, rng)
    jug(clutter, V(1.75, iy - 0.11, 1.7), rng)

    net_heap(clutter, V(-2.9, -1.4, loft), (1.1, 0.9, 0.35), rng)
    net_heap(clutter, V(-3.3, 1.0, loft), (0.8, 1.0, 0.3), rng, floats=False)
    crab_pot(clutter, V(-1.9, -1.75, loft), 0.3, rng)
    crab_pot(clutter, V(-1.25, -1.8, loft), -0.2, rng)
    crab_pot(clutter, V(-1.6, -1.78, loft + 0.3), 0.1, rng)
    sea_chest(b, interior, V(2.9, -1.55, loft), 0.0, rng)
    b.loot("military", V(1.85, 0.2, loft))
    mattress(clutter, V(2.8, 1.25, loft + 0.08), (1.9, 0.8, 0.16), 0.0, rng, 0.03)
    drape(clutter, V(3.0, 1.25, loft + 0.17), 1.1, 0.85, 0.08, 0.2, rng, "fabric_worn", 4, (True, False))
    lantern(clutter, V(2.3, 0.55, loft), rng)
    b.light("warm", V(2.3, 0.55, loft + 0.2))
    for index in range(3):
        oar(clutter, V(-3.0 + index * 0.1, -0.95 + index * 0.18, loft + 0.02), V(-3.4, -0.75 + index * 0.18, loft + 2.2), rng)
    rope_coil(clutter, V(-2.1, 0.3, loft), rng)
    rope_coil(clutter, V(-2.15, 0.33, loft + 0.08), rng, 0.15, 3)
    chair(clutter, V(1.5, -1.75, loft), 0.8, rng, fallen=True)
    crate(clutter, V(-0.7, -1.9, loft), (0.6, 0.45, 0.4), 0.0, rng, broken=True)
    sack(clutter, V(-0.8, 1.9, loft), rng)
    sack(clutter, V(-1.3, 1.95, loft), rng, scale=0.85)

    kit.scatter_chips(debris, "plaster_interior", -ix + 0.1, -0.7, -iy + 0.05, -iy + 0.45, 0.0, 22, rng)
    kit.scatter_chips(debris, "plaster_interior", 1.1, ix - 0.6, -iy + 0.05, -iy + 0.45, 0.0, 18, rng)
    kit.scatter_chips(debris, "plaster_interior", -ix + 0.7, ix - 0.6, iy - 0.4, iy - 0.05, 0.0, 30, rng)
    kit.scatter_chips(debris, "plaster_interior", 0.96, 1.4, -1.1, 2.3, 0.0, 14, rng)
    kit.scatter_chips(debris, "glass_dirty", -3.1, -2.1, -iy + 0.05, -iy + 0.6, 0.0, 14, rng, (0.02, 0.06), (0.003, 0.004))
    kit.scatter_chips(debris, "glass_dirty", 2.1, 3.1, -iy + 0.05, -iy + 0.6, 0.0, 12, rng, (0.02, 0.06), (0.003, 0.004))
    kit.scatter_chips(debris, "foliage", -0.7, 0.7, -iy + 0.02, -0.8, 0.0, 36, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    kit.scatter_chips(debris, "slate_roof", 1.0, 2.5, 1.2, 2.2, loft, 9, rng, (0.1, 0.18), (0.006, 0.008))
    kit.plank_debris(debris, "timber_planks_weathered", 1.2, 2.2, 1.0, 2.0, loft, 3, rng, (0.3, 0.8))
    kit.scatter_chips(debris, "slate_roof", 0.5, 2.8, hy + 0.3, hy + 0.9, -0.1, 12, rng, (0.1, 0.18), (0.006, 0.008))
    kit.scatter_chips(debris, "foliage", -1.0, 1.0, porch_y0 + 0.1, -hy - 0.1, 0.0, 30, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    lump(debris, "dirt_debris", V(2.5, -1.9, -0.13), (0.45, 0.4, 0.08), rng, 0.3, 2, -0.17)
    for index in range(5):
        kit.grass_tuft(plants, V(rng.uniform(2.2, 2.9), rng.uniform(-2.3, -1.7), -0.12), rng, (0.2, 0.5), (5, 10), 0.06)

    base_weeds(plants, -hx, hx, -hy, hy, rng, 1.3, lambda p: (abs(p.x) < 1.4 and p.y < 0.0) or (p.x < -hx + 0.1 and -2.7 < p.y < -1.4))
    base_weeds(plants, -porch_x, porch_x, porch_y0, -hy, rng, 0.9, lambda p: p.y > -hy - 0.15 or abs(p.x) < 0.95)
    kit.ivy(plants, V(-hx - 0.02, 1.9, -0.1), V(-1.0, 0.0, 0.0), rng, 3.8, 0.9, 7, 30.0)
    kit.ivy(plants, V(-3.3, hy + 0.02, -0.1), V(0.0, 1.0, 0.0), rng, 2.9, 0.8, 6, 28.0)
    kit.ivy(plants, V(hx + 0.02, 2.3, -0.1), V(1.0, 0.0, 0.0), rng, 1.9, 0.5, 3, 24.0)
    for index in range(12):
        lump(plants, "roof_moss", V(rng.uniform(-ix, ix), rng.uniform(-0.05, 0.08), gable.ridge_top + 0.085), (rng.uniform(0.06, 0.14), 0.09, 0.035), rng, 0.3, 1)
    for index in range(8):
        d = rng.uniform(0.1, 0.5)
        lump(plants, "roof_moss", gable.point(1.0, rng.uniform(-ix, ix), d, 0.03), (rng.uniform(0.08, 0.16), rng.uniform(0.05, 0.1), 0.03), rng, 0.3, 1)
    kit.deform(sag_roof[0], kit.sagging(*sag_roof[1:]))
    kit.deform(plants, kit.sagging(-ix, ix, gable.ridge_top - 0.3, gable.ridge_top, 0.075))
    return b


def upright_slab(part, name, frame, outline, thickness, t_out=0.0):
    origin, along, up, normal = frame
    geo = kit.geo_slab(origin, along, up, normal, outline, [], t_out - thickness, t_out)
    geo.uvs = [[((geo.points[i] - origin).dot(up), (geo.points[i] - origin).dot(along) + (geo.points[i] - origin).dot(normal)) for i in face] for face in geo.faces]
    emit(part, geo, name, None, "given")


def far_trim(shell, gable, hx, hy, wall_t, tops, parapet=None, quoin=0.45, name="granite_ashlar"):
    for index, (sx, sy) in enumerate(((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))):
        block(shell, name, V(sx * (hx - quoin), sy * (hy - quoin), -0.3), V(sx * (hx + 0.025), sy * (hy + 0.025), tops[index]))
    if parapet is not None:
        for sx in (-1.0, 1.0):
            for side in (-1.0, 1.0):
                a = gable.point(side, sx * (hx - wall_t * 0.5), gable.distance(gable.half), parapet + 0.06)
                c = gable.point(side, sx * (hx - wall_t * 0.5), gable.run, parapet + 0.06)
                kit.member(shell, name, a, c, wall_t + 0.1, 0.12, gable.normal(side), 0.0, "box")


def cottage_far():
    b = kit.Build("cottage_far", 102)
    shell = b.part("shell", 30.0)
    hx, hy, ix = 4.5, 3.0, 3.9
    gable = kit.Gable(-ix, ix, hy, 0.22, 3.12, 42.0)
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    for frame in (front, back):
        kit.wall(shell, "granite_rubble", frame, kit.rect(-ix, ix, -1.5, wall_top), [], 0.6)
    for side in ("left", "right"):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.top(hy) + 0.16), (0.0, gable.ridge_top + 0.16), (-hy, gable.top(hy) + 0.16)]
        kit.wall(shell, "granite_rubble", kit.facade(side, hx, hy), outline, [], 0.6)
    for frame, openings in ((front, [(-0.5, 0.5, 0.0, 2.1), (-3.05, -2.15, 0.85, 2.0), (2.15, 3.05, 0.85, 2.0)]), (back, [(2.1, 2.9, 1.0, 1.9), (-2.9, -2.1, 0.95, 1.95)])):
        for a0, a1, b0, b1 in openings:
            kit.skin(shell, "soot", frame, kit.rect(a0, a1, b0, b1), [], 0.004, 0.002, False)
    kit.skin(shell, "render_white", front, kit.rect(-ix + 0.03, -0.96, 0.5, wall_top - 0.04), [kit.rect(-3.3, -1.9, 0.7, 2.35)], 0.003, 0.0, False)
    kit.skin(shell, "render_white", front, kit.rect(0.96, ix - 0.03, 0.5, wall_top - 0.04), [kit.rect(1.9, 3.3, 0.7, 2.35)], 0.003, 0.0, False)
    kit.roof_slab(shell, gable, -1.0, -ix, ix, "slate_roof")
    kit.roof_slab(shell, gable, 1.0, -ix, ix, "roof_moss")
    for x in (-hx + 0.34, hx - 0.34):
        block(shell, "granite_ashlar", V(x - 0.34, -0.5, gable.top(0.5) - 0.3), V(x + 0.34, 0.5, gable.ridge_top + 1.12))
        block(shell, "terracotta", V(x - 0.1, -0.35, gable.ridge_top + 1.12), V(x + 0.1, -0.15, gable.ridge_top + 1.6))
        block(shell, "terracotta", V(x - 0.1, 0.15, gable.ridge_top + 1.12), V(x + 0.1, 0.35, gable.ridge_top + 1.45))
    lean = kit.Gable(-1.32, 1.32, 1.6, 0.15, 2.94 - 1.75 * math.tan(math.radians(20.0)), 20.0, -hy)
    kit.roof_slab(shell, lean, -1.0, -1.32, 1.32, "slate_roof", 0.16)
    for sx in (-1.0, 1.0):
        x0 = sx * 1.2 - (0.3 if sx > 0 else 0.0)
        block(shell, "granite_rubble", V(x0, -4.6, -1.5), V(x0 + 0.3, -hy, 0.98), 0.0, "world")
        block(shell, "timber_beam", V(sx * 1.05 - 0.06, -4.51, 0.98), V(sx * 1.05 + 0.06, -4.39, 2.2))
    block(shell, "concrete", V(-0.9, -4.6, -1.5), V(0.9, -hy, 0.0))
    block(shell, "terracotta", V(-ix, -0.13, gable.ridge_top - 0.04), V(ix, 0.13, gable.ridge_top + 0.09))
    for a0, a1 in ((-3.53, -3.06), (-2.14, -1.67)):
        kit.skin(shell, "painted_wood_blue", front, kit.rect(a0, a1, 0.85, 2.0), [], 0.025, 0.004, False)
    for frame, spans in ((front, ((-ix, -1.25), (1.25, ix))), (back, ((-ix, ix),)), (kit.facade("left", hx, hy), ((-hy, hy),)), (kit.facade("right", hx, hy), ((-hy, hy),))):
        for a0, a1 in spans:
            frame_block(shell, "granite_ashlar", frame, a0, a1, -0.5, 0.2, -0.04, 0.0)
    far_trim(shell, gable, hx, hy, 0.6, [gable.top(hy) + 0.14] * 4, 0.16)
    return b


def window_dress(shell, joinery, frame, w, wall_t, render=None, depth=0.12, dressed="granite_ashlar", board="floorboards", beam="timber_beam"):
    kit.sill_stone(shell, dressed, frame, w[0], w[1], w[2], 0.16, 0.07, 0.08, 0.06)
    frame_block(joinery, board, frame, w[0] - 0.05, w[1] + 0.05, w[2] - 0.03, w[2] + 0.005, 0.22, wall_t + 0.03, 0.004, "board")
    frame_block(joinery, beam, frame, w[0] - 0.15, w[1] + 0.15, w[3], w[3] + 0.12, wall_t - 0.26, wall_t + 0.004, 0.006)
    if render is not None:
        reveal_skin(shell, render, frame, w, depth)


def house_notice():
    path = os.path.join(kit.models_root, "bld_house", "house_notice_albedo.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [("NOTICE", 0.17, 0.36), ("BY ORDER OF THE PARISH", 0.046, 0.22), ("ALL RESIDENTS", 0.08, 0.1), ("MUST LEAVE THE ISLAND", 0.058, 0.0), ("BY THE LAST BOAT", 0.058, -0.08), ("One case for each person.", 0.04, -0.2), ("Leave every door unlocked.", 0.04, -0.26), ("Turn all livestock out.", 0.04, -0.32), ("HARBOUR OFFICE", 0.036, -0.42)]
    kit.hero_text(path, [(body, height * 0.72, y) for body, height, y in lines], border=0.16)
    return path


def house():
    b = kit.Build("house", 201)
    rng = b.rng
    shell = b.part("shell", 30.0)
    roof = b.part("roof", 50.0)
    joinery = b.part("joinery", 30.0)
    floors = b.part("floors", 30.0)
    interior = b.part("interior", 40.0)
    clutter = b.part("clutter", 45.0)
    debris = b.part("debris", 40.0)
    plants = b.part("plants", 70.0)
    kit.hero("house_notice", os.path.join(kit.models_root, "bld_house", "house_notice_albedo.png"), "wallpaper_faded")
    hx = 4.2
    hy = 3.5
    wall_t = 0.5
    ix = hx - wall_t
    iy = hy - wall_t
    f1 = 2.9
    c1 = f1 - 0.245
    c2 = 5.4
    gable = kit.Gable(-ix, ix, hy, 0.25, 5.48, 40.0)
    wall_top = gable.under(hy, 0.03)
    parapet = 0.2
    paint = "painted_wood_green"
    stone = "granite_rubble"
    dressed = "granite_ashlar"
    render = "render_white"
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    door = (-0.5, 0.5, 0.0, 2.45)
    front_ground = [(-2.85, -1.75, 0.8, 2.2), (1.75, 2.85, 0.8, 2.2)]
    front_upper = [(-2.85, -1.75, 3.6, 4.95), (1.75, 2.85, 3.6, 4.95), (-0.45, 0.45, 3.75, 4.85)]
    back_door = (-0.95, 0.0, 0.0, 2.1)
    back_ground = [(-2.8, -1.7, 1.0, 2.2), (1.7, 2.8, 0.8, 2.2)]
    back_upper = [(1.7, 2.8, 3.6, 4.95), (-2.8, -1.7, 3.6, 4.95)]
    front_open = [door] + front_ground + front_upper
    back_open = [back_door] + back_ground + back_upper
    collapse = (1.4, ix, 0.9, iy)

    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [kit.rect(o[0], o[1], o[2] - (0.05 if o[2] <= 0.0 else 0.0), o[3]) for o in front_open], wall_t)
    broken_top = [(-1.6, wall_top), (-1.85, wall_top - 0.12), (-2.2, wall_top - 0.3), (-2.7, wall_top - 0.38), (-3.0, wall_top - 0.3), (-3.25, wall_top - 0.62), (-3.5, wall_top - 0.5), (-ix, wall_top - 0.75)]
    kit.wall(shell, stone, back, [(-ix, -1.5), (ix, -1.5), (ix, wall_top)] + broken_top, [kit.rect(o[0], o[1], o[2] - (0.05 if o[2] <= 0.0 else 0.0), o[3]) for o in back_open], wall_t)
    for index in range(len(broken_top) - 1):
        (a0, z0), (a1, z1) = broken_top[index], broken_top[index + 1]
        for count in range(2):
            a = rng.uniform(min(a0, a1), max(a0, a1))
            lump(debris, stone, kit.frame_point(back, a, min(z0, z1) + 0.06, -rng.uniform(0.08, 0.4)), (rng.uniform(0.1, 0.2), rng.uniform(0.08, 0.14), rng.uniform(0.06, 0.1)), rng, 0.2, 1, None, None, False)
    for frame in (left, right):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.top(hy) + parapet), (0.0, gable.ridge_top + parapet), (-hy, gable.top(hy) + parapet)]
        kit.wall(shell, stone, frame, outline, [], wall_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, -1.5, wall_top, wall_t, front_open)
    kit.wall_boxes(b, "rock", "back", back, -1.6, ix, -1.5, wall_top, wall_t, [o for o in back_open if o[1] > -1.6])
    kit.wall_boxes(b, "rock", "back_low", back, -ix, -1.6, -1.5, wall_top - 0.45, wall_t, [o for o in back_open if o[1] <= -1.6])
    kit.wall_boxes(b, "rock", "left", left, -hy, hy, -1.5, wall_top, wall_t, [])
    kit.wall_boxes(b, "rock", "right", right, -hy, hy, -1.5, wall_top, wall_t, [])
    gable_cols(b, "left_gable", -hx, -ix, gable, wall_top, parapet)
    gable_cols(b, "right_gable", ix, hx, gable, wall_top, parapet)
    for corner, ua, ub in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0))):
        kit.quoins(shell, dressed, corner, ua, ub, 0.36, gable.top(hy) + parapet - 0.02, rng, 0.034)
    for sx in (-1.0, 1.0):
        block(shell, "concrete", V(sx * (ix - 0.03), -hy - 0.035, -1.5), V(sx * (hx + 0.035), hy + 0.035, 0.35), 0.0, "world")
    frame_block(shell, "concrete", front, -ix, -0.66, -1.5, 0.35, -0.035, 0.1, 0.0, "world")
    frame_block(shell, "concrete", front, 0.66, ix, -1.5, 0.35, -0.035, 0.1, 0.0, "world")
    frame_block(shell, "concrete", back, -ix, -1.0, -1.5, 0.35, -0.035, 0.1, 0.0, "world")
    frame_block(shell, "concrete", back, 0.05, ix, -1.5, 0.35, -0.035, 0.1, 0.0, "world")
    for frame, openings in ((front, front_ground + front_upper), (back, back_ground + back_upper)):
        for w in openings:
            window_dress(shell, joinery, frame, w, wall_t, render)
    render_wall(shell, front, -ix + 0.03, ix - 0.03, wall_top - 0.03, front_open, rng, 9, render, 0.02, 2, (0.36, 0.5), 0.0, (), 0.0)
    render_wall(shell, back, -1.55, ix - 0.03, wall_top - 0.03, [o for o in back_open if o[1] > -1.55], rng, 8, render, 0.02, 2, (0.36, 0.55))
    render_wall(shell, back, -ix + 0.03, -1.6, 3.45, [back_ground[0]], rng, 3, render, 0.02, 1, (0.36, 0.7), 0.5)
    render_wall(shell, right, -hy + 0.05, hy - 0.05, wall_top - 0.1, [], rng, 9, render, 0.02, 3, (0.36, 0.9), 0.9)
    ghost = [(-hy + 0.05, 0.4), (hy - 0.05, 0.4), (hy - 0.05, 4.2), (0.0, 6.3), (-hy + 0.05, 4.2)]
    hearths = [kit.rect(-0.55, 0.55, 0.41, 1.5), kit.rect(-0.4, 0.4, 3.05, 3.95)]
    ghost_blobs = kit.scatter_patches((-hy + 0.1, hy - 0.1, 0.5, 4.1), hearths, 9, (0.2, 0.7), rng, (0.6, 1.4))
    kit.skin(shell, "render_pink", left, ghost, hearths + ghost_blobs, 0.015)
    for a0, a1, z0, z1 in ((-0.55, 0.55, 0.41, 1.5), (-0.4, 0.4, 3.05, 3.95)):
        frame_block(shell, "brick_red", left, a0, a1, z0, z1, -0.006, 0.05, 0.0, "world")
        frame_block(shell, dressed, left, a0 - 0.18, a1 + 0.18, z1, z1 + 0.2, -0.03, 0.2, 0.015)
    for sign in (-1.0, 1.0):
        a = kit.frame_point(left, sign * (hy - 0.05), 4.2, 0.02)
        c = kit.frame_point(left, 0.0, 6.3, 0.02)
        emit(shell, kit.geo_box((c - a).length, 0.09, 0.03), "concrete", kit.place((a + c) * 0.5, (c - a).normalized(), V(-1.0, 0.0, 0.0)), "box")
    a = -3.0
    while a < 3.05:
        if abs(a) > 0.7:
            frame_block(shell, "soot", left, a - 0.045, a + 0.045, 2.68, 2.82, -0.018, 0.0)
        a += 0.45

    a0, a1, b0, b1 = door
    frame_block(shell, dressed, front, -0.72, 0.72, -0.2, 0.0, -0.42, 0.06, 0.015)
    frame_block(shell, dressed, front, door[0], door[1], -0.2, 0.0, 0.06, wall_t)
    frame_block(shell, dressed, back, back_door[0], back_door[1], -0.2, 0.0, 0.06, wall_t)
    frame_block(shell, dressed, front, -0.9, 0.9, -0.4, -0.2, -0.75, -0.3, 0.015)
    b.col("rock", "step", kit.frame_point(front, -0.72, -1.5, 0.0), kit.frame_point(front, 0.72, 0.0, 0.42))
    b.col("rock", "step", kit.frame_point(front, -0.9, -1.5, 0.3), kit.frame_point(front, 0.9, -0.2, 0.75))
    for sx in (-1.0, 1.0):
        frame_block(joinery, paint, front, sx * 0.5, sx * 0.66, 0.0, 2.52, -0.05, 0.0, 0.006, "board")
    frame_block(joinery, paint, front, -0.74, 0.74, 2.52, 2.64, -0.2, 0.0, 0.01, "board")
    frame_block(joinery, paint, front, -0.66, 0.66, 2.45, 2.52, -0.06, 0.0, 0.006, "board")
    ja0, ja1, jtop = kit.door_frame(joinery, paint, front, a0, a1, 0.0, b1, 0.12)
    frame_block(joinery, paint, front, ja0, ja1, 2.1, 2.16, 0.12, 0.23, 0.004, "board")
    for index in range(3):
        p0 = ja0 + (ja1 - ja0) * index / 3 + 0.01
        p1 = ja0 + (ja1 - ja0) * (index + 1) / 3 - 0.01
        kit.pane(joinery, kit.frame_matrix(front), p0, p1, 2.17, jtop - 0.01, 0.17, rng.choice(["whole", "shard", "missing"]), rng)
        if index:
            frame_block(joinery, paint, front, p0 - 0.02, p0, 2.16, jtop, 0.14, 0.2)
    kit.door_leaf(joinery, paint, front, ja0 + 0.005, 1.0, 0.24, 0.015, 2.07, ja1 - ja0 - 0.01, 72.0, rng, "panel")
    notice = kit.Geo([kit.frame_point(front, 0.8, 1.12, 0.023), kit.frame_point(front, 1.22, 1.12, 0.023), kit.frame_point(front, 1.235, 1.72, 0.027), kit.frame_point(front, 0.815, 1.73, 0.023)], [(0, 1, 2, 3)], [[(0.16, 0.02), (0.84, 0.02), (0.84, 0.98), (0.16, 0.98)]])
    emit(joinery, notice, "house_notice", None, "texture")
    ba0, ba1, btop = kit.door_frame(joinery, paint, back, back_door[0] + 0.02, back_door[1] - 0.02, 0.0, back_door[3], 0.12)
    kit.door_leaf(joinery, paint, back, ba1 - 0.005, -1.0, 0.24, 0.02, 2.0, ba1 - ba0 - 0.01, 105.0, rng, "ledged", 5.0)
    frame_block(shell, dressed, back, back_door[0] - 0.1, back_door[1] + 0.1, -0.2, 0.0, -0.35, 0.06, 0.015)
    b.col("rock", "step", kit.frame_point(back, back_door[0] - 0.1, -1.5, 0.0), kit.frame_point(back, back_door[1] + 0.1, 0.0, 0.35))
    reveal_skin(shell, render, front, door, 0.12)
    reveal_skin(shell, render, back, back_door, 0.12)

    shutter_plan = {0: (("open", "open"), 0.0), 1: (("ajar", "hang"), 0.35)}
    for index, w in enumerate(front_ground):
        states, lift = shutter_plan[index]
        kit.sash_window(joinery, paint, front, w[0], w[1], w[2], w[3], 0.12, rng, lift, 0.35, 0.3)
        width = (w[1] - w[0]) * 0.5 + 0.02
        for leaf, hinge_a, direction in ((states[0], w[0] - 0.01, 1.0), (states[1], w[1] + 0.01, -1.0)):
            angle = {"open": 173.0, "hang": 150.0, "ajar": 112.0}[leaf]
            kit.shutter(joinery, paint, front, hinge_a, direction, w[2], w[3], width, angle, rng, "louvred", 12.0 if leaf == "hang" else 0.0)
    upper_plan = {0: (("open", None), 0.0), 1: (("open", "open"), 0.2), 2: ((None, None), 0.0)}
    for index, w in enumerate(front_upper):
        states, lift = upper_plan[index]
        kit.sash_window(joinery, paint, front, w[0], w[1], w[2], w[3], 0.12, rng, lift, 0.4, 0.3, 3 if index < 2 else 2, 2)
        width = (w[1] - w[0]) * 0.5 + 0.02
        for leaf, hinge_a, direction in ((states[0], w[0] - 0.01, 1.0), (states[1], w[1] + 0.01, -1.0)):
            if leaf is not None:
                kit.shutter(joinery, paint, front, hinge_a, direction, w[2], w[3], width, 173.0 if leaf == "open" else 140.0, rng, "louvred")
    for index, w in enumerate(back_ground + back_upper):
        kit.sash_window(joinery, paint, back, w[0], w[1], w[2], w[3], 0.12, rng, 0.0 if index != 1 else 0.3, 0.3 if index != 3 else 0.0, 0.3)

    stack_top = gable.ridge_top + 1.1
    for x_stack in (-hx + 0.29, hx - 0.29):
        kit.chimney(roof, dressed, x_stack, 0.0, 0.58, 1.3, gable.top(0.65) - 0.3, stack_top, rng, 3)
        b.col("rock", "chimney", V(x_stack - 0.29, -0.65, gable.top(0.65) - 0.3), V(x_stack + 0.29, 0.65, stack_top + 0.12))
    kit.gable_coping(roof, dressed, gable, -hx + wall_t * 0.5, wall_t, rng, 0.12, 0.05, parapet)
    kit.gable_coping(roof, dressed, gable, hx - wall_t * 0.5, wall_t, rng, 0.12, 0.05, parapet)
    aerial(roof, V(-hx + 0.02, -0.3, stack_top - 0.8), 2.6, rng)
    ragged = kit.smooth_noise(random.Random(31), 4, 1.5)
    moss_field = kit.smooth_noise(random.Random(32), 5, 1.2)

    def lost(x, d):
        return x > collapse[0] - 0.15 + 0.35 * ragged(V(x, d, 0.0)) and d < 3.7 + 0.4 * ragged(V(d, x, 1.0))

    kit.slate_roof(roof, gable, -1.0, rng, lambda x, d: moss_field(V(x * 0.5, d * 0.7, 0.0)) > 0.4, lambda x, d: rng.random() < 0.008, lambda x, d: rng.uniform(0.05, 0.16) if rng.random() < 0.02 else 0.0)
    kit.slate_roof(roof, gable, 1.0, rng, lambda x, d: moss_field(V(x * 0.5, d * 0.7, 2.0)) > 0.05 or (d < 0.6 and rng.random() < 0.5), lambda x, d: lost(x, d) or rng.random() < 0.015, lambda x, d: rng.uniform(0.05, 0.2) if (rng.random() < 0.03 or (x > 0.6 and rng.random() < 0.25)) else 0.0)
    kit.roof_boards(roof, gable, -1.0, -ix, ix, 0.0, gable.run + 0.02, rng, "timber_planks_weathered", 0.022, -0.001)
    kit.roof_boards(roof, gable, 1.0, -ix, ix, 0.0, gable.run + 0.02, rng, "timber_planks_weathered", 0.022, -0.001, [(collapse[0] + 0.15, ix + 0.1, -0.1, 3.55)])
    rafter_xs = [-ix + 0.2 + i * (2 * ix - 0.4) / 16 for i in range(17)]
    kit.roof_rafters(roof, gable, -1.0, rafter_xs, 0.0, gable.run - 0.02, -0.023)
    fallen = []
    for x in rafter_xs:
        if x < collapse[0] + 0.1:
            kit.roof_rafters(roof, gable, 1.0, [x], 0.0, gable.run - 0.02, -0.023)
            continue
        roll = rng.random()
        if roll < 0.3:
            kit.roof_rafters(roof, gable, 1.0, [x], 0.0, gable.run - 0.02, -0.023)
        elif roll < 0.75:
            kit.roof_rafters(roof, gable, 1.0, [x], rng.uniform(2.2, 3.4), gable.run - 0.02, -0.023)
            fallen.append(x)
        else:
            fallen.append(x)
    for side in (-1.0, 1.0):
        block(roof, "timber_beam", V(-ix, side * iy, wall_top - 0.02), V(ix if side < 0 else collapse[0], side * (iy + 0.16), wall_top + 0.1), 0.006)
        kit.segmented(roof, paint, gable.point(side, -ix, -0.013, -0.095), gable.point(side, ix if side < 0 else collapse[0], -0.013, -0.095), 0.025, 0.17, gable.normal(side), 1.3)
    kit.segmented(roof, "timber_beam", V(-ix, 0.0, gable.ridge_top - 0.195), V(ix, 0.0, gable.ridge_top - 0.195), 0.04, 0.33, V(0.0, 0.0, 1.0), 0.9, "box")
    kit.ridge_tiles(roof, gable, -ix, ix, rng)
    gutter_z = kit.gutter(roof, gable, -1.0, -ix - 0.2, ix + 0.2, rng, 0.03)
    kit.gutter(roof, gable, 1.0, -ix - 0.2, collapse[0] - 0.1, rng, 0.04)
    hanging = [V(collapse[0] - 0.1, gable.edge + 0.04, gutter_z), V(collapse[0] + 0.6, gable.edge + 0.1, gutter_z - 0.5), V(collapse[0] + 1.3, gable.edge + 0.25, gutter_z - 1.6), V(collapse[0] + 1.8, gable.edge + 0.5, gutter_z - 3.0)]
    emit(roof, kit.geo_tube(hanging, [(0.06 * math.cos(math.pi + math.pi * t / 6), 0.06 * math.sin(math.pi + math.pi * t / 6)) for t in range(7)] + [(0.055 * math.cos(math.pi + math.pi * t / 6), 0.055 * math.sin(math.pi + math.pi * t / 6)) for t in range(6, -1, -1)], True, V(0.0, 0.0, 1.0)), "rusty_metal", None, "given", True)
    kit.downpipe(roof, ix + 0.05, -gable.edge - 0.04, -hy, gutter_z - 0.03, -0.1, rng)
    kit.downpipe(roof, -ix - 0.05, gable.edge + 0.04, hy, gutter_z - 0.03, -0.1, rng, lean=0.03)
    for index in range(16):
        kit.grass_tuft(plants, V(rng.uniform(-ix, ix), -gable.edge - 0.04, gutter_z - 0.02), rng, (0.08, 0.25), (3, 6), 0.03)
    b.ramp("py", "rock", "roof", V(-hx, -gable.edge, gable.eave_top), V(hx, 0.0, gable.ridge_top))
    b.ramp("ny", "rock", "roof", V(-hx, 0.0, gable.eave_top), V(collapse[0], gable.edge, gable.ridge_top))
    b.ramp("ny", "rock", "roof", V(collapse[0], 0.0, gable.top(0.9) - 0.1), V(hx, 0.9, gable.ridge_top))
    sag_roof = (roof, -ix, ix, gable.eave_top + 0.1, gable.ridge_top, 0.06)

    block(floors, "dirt_debris", V(-ix, -iy, -0.24), V(1.05, iy, -0.17))
    kit.joists(floors, "timber_beam", -ix, 1.05, -iy, iy, -0.028, "x", 0.5, 0.08, 0.14)
    kit.floor_boards(floors, "floorboards", -ix, 0.95, -iy, iy, 0.0, "y", rng, width_range=(0.13, 0.18), joints=[-1.4, 0.2, 1.6], holes=[(-ix, -ix + 0.4, -0.8, 0.8), (-1.05, -0.95, -iy, -2.72), (-1.05, -0.95, -1.73, iy)], warp=0.03)
    block(floors, "brick_red", V(1.05, -iy, -0.12), V(ix, iy, 0.0), 0.0, "world")
    b.col("wood", "floor", V(-ix, -iy, -0.3), V(1.0, iy, 0.0))
    b.col("concrete", "floor", V(1.0, -iy, -0.3), V(ix, iy, 0.0))
    well = (-0.95, 0.05, -1.45, 1.95)
    stair_edge = -0.08
    rot = (2.6, 3.2, 1.9, 2.6)
    for x0, x1 in ((-ix, -1.05), (1.05, ix)):
        kit.joists(floors, "timber_beam", x0, x1, -iy, iy, f1 - 0.025, "x", 0.4, 0.06, 0.2)
    kit.joists(floors, "timber_beam", -0.95, 0.95, -iy, iy, f1 - 0.025, "x", 0.4, 0.06, 0.2, lambda y: [(well[1], 0.95)] if well[2] - 0.05 < y < well[3] else [(-0.95, 0.95)])
    block(floors, "timber_beam", V(well[0], well[3], f1 - 0.225), V(well[1] + 0.06, well[3] + 0.08, f1 - 0.025))
    block(floors, "timber_beam", V(well[1], well[2], f1 - 0.225), V(well[1] + 0.07, well[3], f1 - 0.025))
    kit.floor_boards(floors, "floorboards", -ix, ix, -iy, iy, f1, "y", rng, width_range=(0.13, 0.18), joints=[-1.6, -0.2, 1.3], holes=[well, rot], ragged=0.12, warp=0.03)
    b.col("wood", "upper", V(-ix, -iy, c1), V(well[0] - 0.05, iy, f1))
    b.col("wood", "upper", V(well[0] - 0.05, -iy, c1), V(well[1], well[2], f1))
    b.col("wood", "upper", V(well[0] - 0.05, well[3], c1), V(well[1], iy, f1))
    b.col("wood", "upper", V(well[1], -iy, c1), V(rot[0], iy, f1))
    b.col("wood", "upper", V(rot[0], -iy, c1), V(rot[1], rot[2], f1))
    b.col("wood", "upper", V(rot[0], rot[3], c1), V(rot[1], iy, f1))
    b.col("wood", "upper", V(rot[1], -iy, c1), V(ix, iy, f1))
    ceiling(interior, c1 + 0.02, -ix, -1.05, -iy, iy, rng, 3, [(-ix, -ix + 0.4, -0.8, 0.8)])
    ceiling(interior, c1 + 0.02, 1.05, ix, -iy, iy, rng, 2, [rot, (ix - 0.5, ix, -1.0, 1.0)])
    hall_outline = [(-0.95, -iy), (0.95, -iy), (0.95, iy), (-0.95, iy), (-0.95, well[3]), (well[1], well[3]), (well[1], well[2]), (-0.95, well[2])]
    kit.skin(interior, "plaster_interior", ceiling_frame(c1 + 0.02), [(x, -y) for x, y in hall_outline], [], 0.02)
    ceiling(interior, c2 + 0.02, -ix, -1.05, -iy, iy, rng, 3, [(-ix, -ix + 0.4, -0.8, 0.8)])
    ceiling(interior, c2 + 0.02, -0.95, 0.95, -iy, iy, rng, 2)
    right_outline = [(1.05, -iy), (ix, -iy), (ix, collapse[2] - 0.2), (2.9, collapse[2]), (2.2, collapse[2] + 0.3), (collapse[0] + 0.1, collapse[2] + 0.9), (collapse[0], 2.2), (1.05, 2.5)]
    kit.skin(interior, "plaster_interior", ceiling_frame(c2 + 0.02), [(x, -y) for x, y in right_outline], [], 0.02)
    kit.skin(interior, "plaster_interior", ceiling_frame(c2 + 0.02), [(1.05, -3.0), (1.3, -3.0), (1.25, -2.6), (1.05, -2.55)], [], 0.02)
    for y in [(-iy + 0.2 + i * 0.4) for i in range(15)]:
        for x0, x1 in ((-ix, -1.05), (-0.95, 0.95)):
            block(roof, "timber_beam", V(x0, y - 0.025, c2 + 0.02), V(x1, y + 0.025, c2 + 0.17))
        if y < collapse[2] - 0.1:
            block(roof, "timber_beam", V(1.05, y - 0.025, c2 + 0.02), V(ix, y + 0.025, c2 + 0.17))
        else:
            reach = rng.uniform(0.3, 1.3)
            block(roof, "timber_beam", V(1.05, y - 0.025, c2 + 0.02), V(1.05 + reach, y + 0.025, c2 + 0.17))
            if rng.random() < 0.5:
                a = V(1.05 + reach, y, c2 + 0.1)
                emit(debris, kit.geo_box(1.6, 0.05, 0.15), "timber_beam", kit.place(a + V(0.55, 0.0, -0.55), V(0.7, rng.uniform(-0.15, 0.15), -0.7), V(0.0, 0.0, 1.0)), "box")
    laths(interior, V(0.0, 0.0, c2 + 0.018), V(0.0, 1.0, 0.0), V(1.0, 0.0, 0.0), collapse[2] - 0.5, collapse[2] + 0.9, 1.2, 2.3, rng)
    b.col("wood", "ceiling", V(-ix, -iy, c2), V(collapse[0], iy, c2 + 0.2))
    b.col("wood", "ceiling", V(collapse[0], -iy, c2), V(ix, collapse[2], c2 + 0.2))

    left_wall = kit.plane(V(-0.95, 0.0, 0.0), V(1.0, 0.0, 0.0))
    right_wall = kit.plane(V(1.05, 0.0, 0.0), V(1.0, 0.0, 0.0))
    living_door = (-2.7, -1.75, 0.0, 2.1)
    kitchen_door = (0.9, 1.85, 0.0, 2.1)
    kit.wall(interior, "plaster_interior", left_wall, kit.notched(-iy, iy, 0.0, c1, [(living_door[0], living_door[1], living_door[3])]), [], 0.1)
    kit.wall(interior, "plaster_interior", right_wall, kit.notched(-iy, iy, 0.0, c1, [(kitchen_door[0], kitchen_door[1], kitchen_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "partition", left_wall, -iy, iy, 0.0, c1, 0.05, [living_door], -0.05)
    kit.wall_boxes(b, "wood", "partition", right_wall, -iy, iy, 0.0, c1, 0.1, [kitchen_door])
    kit.door_frame(joinery, paint, left_wall, living_door[0], living_door[1], 0.0, 2.1, 0.0, 0.06, 0.1)
    kit.door_frame(joinery, paint, right_wall, kitchen_door[0], kitchen_door[1], 0.0, 2.1, 0.0, 0.06, 0.1)
    kit.door_leaf(joinery, paint, left_wall, living_door[0] + 0.06, 1.0, 0.1, 0.01, 2.02, 0.82, 95.0, rng, "panel")
    kit.door_leaf(joinery, paint, right_wall, kitchen_door[1] - 0.06, -1.0, 0.0, 0.01, 2.02, 0.82, -110.0, rng, "panel", 3.0)
    bed_left_door = (2.1, 3.0)
    bed_right_door = (-0.2, 0.75, f1, f1 + 2.1)
    kit.wall(interior, "plaster_interior", left_wall, kit.rect(-iy, bed_left_door[0], f1, c2), [], 0.1)
    frame_block(interior, "plaster_interior", left_wall, bed_left_door[0], iy, f1 + 2.1, c2, 0.0, 0.1, 0.0, "world")
    kit.wall(interior, "plaster_interior", right_wall, kit.notched(-iy, iy, f1, c2, [(bed_right_door[0], bed_right_door[1], bed_right_door[3])]), [], 0.1)
    kit.wall_boxes(b, "wood", "partition_up", left_wall, -iy, iy, f1, c2, 0.05, [(bed_left_door[0] - 0.16, bed_left_door[1], f1, f1 + 2.1)], -0.05)
    kit.wall_boxes(b, "wood", "partition_up", right_wall, -iy, iy, f1, c2, 0.1, [bed_right_door])
    kit.door_frame(joinery, paint, left_wall, bed_left_door[0], bed_left_door[1] - 0.001, f1, f1 + 2.1, 0.0, 0.06, 0.1)
    kit.door_frame(joinery, paint, right_wall, bed_right_door[0], bed_right_door[1], f1, f1 + 2.1, 0.0, 0.06, 0.1)
    kit.door_leaf(joinery, paint, left_wall, bed_left_door[0] + 0.06, 1.0, 0.1, f1 + 0.01, 2.02, 0.76, 80.0, rng, "panel")
    kit.door_leaf(joinery, paint, right_wall, bed_right_door[0] + 0.06, 1.0, 0.0, f1 + 0.01, 2.02, 0.82, -95.0, rng, "panel")

    kit.stair(floors, "floorboards", V(-0.51, well[2], 0.0), V(0.0, 1.0, 0.0), 0.86, f1, well[3] - well[2], 15, rng, True, paint)
    b.ramp("py", "wood", "stair", V(well[0], well[2], 0.0), V(stair_edge, well[3], f1))
    balustrade(b, joinery, V(stair_edge, well[2], 0.0), V(stair_edge, well[3], f1), rng, 0.9, 0.125, newels=(True, False), collide=False)
    kit.wall(joinery, paint, kit.plane(V(stair_edge - 0.005, 0.0, 0.0), V(1.0, 0.0, 0.0)), [(well[2], 0.0), (well[3], 0.0), (well[3], f1 - 0.22)], [], 0.025)
    frame_block(joinery, paint, kit.plane(V(stair_edge, 0.0, 0.0), V(1.0, 0.0, 0.0)), 0.9, 1.6, 0.06, 1.25, -0.012, 0.0, 0.004, "board")
    frame_block(joinery, "rusty_metal", kit.plane(V(stair_edge, 0.0, 0.0), V(1.0, 0.0, 0.0)), 1.48, 1.52, 0.66, 0.7, -0.035, -0.012)
    balustrade(b, joinery, V(well[1] + 0.04, well[2], f1), V(well[1] + 0.04, -0.85, f1), rng, 0.92, 0.125, newels=(True, False), tag="landing")
    balustrade(b, joinery, V(well[0], well[2], f1), V(well[1] + 0.04, well[2], f1), rng, 0.92, 0.125, newels=(False, False), tag="landing")
    emit(debris, kit.geo_cbox(2.2, 0.06, 0.05, 0.012), "timber_beam", kit.place(V(0.52, 0.55, f1 + 0.03), V(0.12, 1.0, 0.0), V(0.0, 0.0, 1.0)), "box")
    for index in range(9):
        spot = V(rng.uniform(0.15, 0.85), rng.uniform(-0.6, 1.8), f1 + 0.016)
        emit(debris, kit.geo_box(0.88, 0.028, 0.028), paint, kit.turned(spot, rng.uniform(0.0, tau)), "board")
    for index in range(4):
        spot = V(rng.uniform(-0.8, -0.2), rng.uniform(-0.2, 1.4), 0.0)
        spot.z = (spot.y - well[2]) / (well[3] - well[2]) * f1 + 0.05
        emit(debris, kit.geo_box(0.88, 0.028, 0.028), paint, kit.turned(spot, rng.uniform(0.0, tau), rng.uniform(-0.5, 0.5)), "board")

    breasts = ((-ix, -ix + 0.4, -0.8, 0.8, 1.0, 0.23, 0.66), (ix - 0.5, ix, -1.0, 1.0, -1.0, 0.7, 1.65))
    for x0, x1, y0, y1, direction, half, top in breasts:
        for z0, z1 in ((0.0, c1), (f1, c2)):
            upper = z0 > 1.0
            opening_half = 0.23 if (upper or direction > 0) else half
            opening_top = z0 + (0.66 if (upper or direction > 0) else top)
            block(interior, "plaster_interior", V(x0, y0, z0), V(x1, -opening_half, z1), 0.0, "world")
            block(interior, "plaster_interior", V(x0, opening_half, z0), V(x1, y1, z1), 0.0, "world")
            block(interior, "plaster_interior", V(x0, -opening_half, opening_top), V(x1, opening_half, z1), 0.0, "world")
            b.col("rock", "breast", V(x0, y0, z0), V(x1, -opening_half, z1 + 0.2))
            b.col("rock", "breast", V(x0, opening_half, z0), V(x1, y1, z1 + 0.2))
            b.col("rock", "breast", V(x0, -opening_half, opening_top - 0.2), V(x1, opening_half, z1 + 0.2))
    parlour_fireplace(b, interior, V(-ix + 0.4, 0.0, 0.0), V(1.0, 0.0, 0.0), rng, 1.3, paint)
    parlour_fireplace(b, interior, V(-ix + 0.4, 0.0, f1), V(1.0, 0.0, 0.0), rng, 1.1, paint, "kitchen_tiles", False)
    parlour_fireplace(b, interior, V(ix - 0.5, 0.0, f1), V(-1.0, 0.0, 0.0), rng, 1.0, paint, "kitchen_tiles", False)
    fire_recess(interior, ix - 0.5, 0.0, 1.4, 1.4, 0.45, -1.0, rng, "brick_red")
    range_stove(b, interior, clutter, V(ix - 0.05, 0.0, 0.0), math.pi, rng, 1.2, 0.45)

    wall_paper(interior, kit.facade("front", ix, iy), -ix, -1.05, 0.0, c1, [o for o in front_ground if o[1] < -1.05], rng, 3, 2)
    wall_paper(interior, kit.facade("back", ix, iy), 1.05, ix, 0.0, c1, [o for o in back_ground if o[0] > 1.05], rng, 3, 2)
    wall_paper(interior, kit.facade("left", ix, hy), -iy, iy, 0.0, c1, [], rng, 4, 2, avoid=[(-0.85, 0.85, 0.0, c1)])
    wall_paper(interior, kit.plane(V(-1.05, 0.0, 0.0), V(1.0, 0.0, 0.0)), -iy, iy, 0.0, c1, [living_door], rng, 3, 2)
    wall_paper(interior, kit.facade("front", ix, iy), -ix, -1.05, f1, c2, [o for o in front_upper if o[1] < -1.05], rng, 3, 2)
    wall_paper(interior, kit.facade("back", ix, iy), 1.05, ix, f1, c2, [o for o in back_upper if o[0] > 1.05], rng, 3, 2)
    wall_paper(interior, kit.facade("left", ix, hy), -iy, iy, f1, c2, [], rng, 4, 3, avoid=[(-0.85, 0.85, f1, c2)])
    wall_paper(interior, kit.plane(V(-1.05, 0.0, 0.0), V(1.0, 0.0, 0.0)), -iy, bed_left_door[0] - 0.05, f1, c2, [], rng, 3, 2)
    plaster_wall(interior, kit.facade("front", ix, iy), -0.95, 0.95, 0.0, c1, [door], rng, 1)
    plaster_wall(interior, kit.facade("back", ix, iy), -0.95, 0.95, 0.0, c1, [(back_door[0], back_door[1], 0.0, 2.1)], rng, 1)
    plaster_wall(interior, kit.facade("front", ix, iy), 1.05, ix, 0.0, c1, [o for o in front_ground if o[0] > 1.05], rng, 3)
    plaster_wall(interior, kit.facade("back", ix, iy), -ix, -1.05, 0.0, c1, [o for o in back_ground if o[1] < -1.05], rng, 3)
    plaster_wall(interior, kit.facade("right", ix, hy), -iy, iy, 0.0, c1, [], rng, 4, [(-1.05, 1.05, 0.0, c1)])
    plaster_wall(interior, kit.facade("front", ix, iy), -0.95, ix, f1, c2, [o for o in front_upper if o[0] > -0.95], rng, 4)
    plaster_wall(interior, kit.facade("back", ix, iy), -1.6, 0.95, f1, c2, [], rng, 3)
    plaster_wall(interior, kit.facade("right", ix, hy), -iy, iy, f1, c2, [], rng, 6, [(-1.05, 1.05, f1, c2)])
    for x0, x1 in ((1.1, 1.68), (2.82, ix - 0.02)):
        kit.skin(interior, "kitchen_tiles", (V(0.0, iy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), V(0.0, -1.0, 0.0)), kit.rect(x0, x1, 0.62, 1.82), [], 0.012, 0.016)
    kit.skin(interior, "kitchen_tiles", (V(0.0, iy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), V(0.0, -1.0, 0.0)), kit.rect(1.68, 2.82, 0.62, 0.99), [], 0.012, 0.016)

    sofa(b, interior, V(-1.49, 0.5, 0.0), -math.pi * 0.5, rng)
    armchair(b, interior, V(-2.85, -1.35, 0.0), 0.6, rng)
    piano(b, interior, clutter, V(-3.36, 1.9, 0.0), math.pi * 0.5, rng)
    bookcase(b, interior, clutter, V(-3.55, -1.9, 0.0), math.pi * 0.5, rng, 0.9, 1.8)
    rug(clutter, V(-2.45, 0.0, 0.0), 1.5, 2.2, 0.03, rng)
    table(interior, -1.45, -0.95, 0.0, 0.55, 0.55, 0.62, rng)
    oil_lamp(clutter, V(-1.45, -0.95, 0.62), rng)
    b.light("warm", V(-1.45, -0.95, 0.86))
    b.col("wood", "side_table", V(-1.73, -1.23, 0.0), V(-1.17, -0.67, 0.62))
    b.loot("box", V(-3.3, -2.7, 0.0))
    picture(interior, V(-3.3 + 0.0, 0.0, 1.75), V(1.0, 0.0, 0.0), 0.7, 0.5, rng, "glass_dirty", "timber_beam", 0.0)
    picture(interior, V(-1.055, 1.9, 1.6), V(-1.0, 0.0, 0.0), 0.45, 0.6, rng, "wallpaper_faded", "timber_beam", 0.08)
    picture(interior, V(-1.055, -0.6, 1.65), V(-1.0, 0.0, 0.0), 0.5, 0.4, rng, "wallpaper_faded", "timber_beam", -0.05)
    for y in (-0.5, 0.2, 0.5):
        bottle(clutter, V(-ix + 0.49, y, 1.16), rng)
    curtain(clutter, V(-2.95, -iy + 0.07, 2.3), V(-1.65, -iy + 0.07, 2.3), 1.5, rng, "fabric_worn", 0.4)
    curtain(clutter, V(-1.6, iy - 0.07, 2.3), V(-2.9, iy - 0.07, 2.3), 1.3, rng, "fabric_worn", 0.35)
    coat_rail(interior, clutter, V(0.95, -2.4, 1.65), V(0.95, -1.3, 1.65), V(-1.0, 0.0, 0.0), rng, 2)
    suitcase(clutter, V(0.7, -2.15, 0.0), 1.57, rng)
    emit(clutter, kit.geo_lathe([(0.0, 0.0), (0.11, 0.0), (0.1, 0.5), (0.12, 0.52), (0.1, 0.52), (0.09, 0.02), (0.0, 0.02)], 12), "rusty_metal", kit.Matrix.Translation(V(0.78, -2.75, 0.0)), "given", True)
    rod(clutter, "timber_beam", V(0.78, -2.75, 0.02), V(0.84, -2.7, 0.92), 0.012, 6)
    lantern(clutter, V(0.45, -0.6, 2.2), rng)
    rod(clutter, "rusty_metal", V(0.47, -0.6, 2.49), V(0.47, -0.6, c1), 0.004, 4)
    b.light("warm", V(0.45, -0.6, 2.3))
    picture(interior, V(0.945, -0.2, 1.6), V(-1.0, 0.0, 0.0), 0.4, 0.55, rng, "glass_dirty", "painted_wood_green", 0.0)

    belfast_sink(b, interior, clutter, V(2.25, iy - 0.27, 0.0), 0.0, rng)
    table(interior, 2.95, -1.9, 0.0, 1.3, 0.8, 0.76, rng)
    b.col("wood", "table", V(2.3, -2.3, 0.0), V(3.6, -1.5, 0.76))
    chair(interior, V(2.7, -1.2, 0.0), 0.15, rng)
    chair(interior, V(2.0, -1.95, 0.0), math.pi * 0.5 + 0.2, rng)
    chair(interior, V(1.6, 0.35, 0.0), 2.0, rng, fallen=True)
    lantern(clutter, V(3.42, -1.75, 0.76), rng)
    b.light("warm", V(3.42, -1.75, 0.95))
    plate(clutter, V(2.5, -1.75, 0.76), rng, 0.12, 0.0)
    cup(clutter, V(2.62, -2.12, 0.76), rng)
    bottle(clutter, V(2.45, -2.0, 0.76), rng)
    b.loot("food", V(3.0, -2.0, 0.76))
    dresser(b, interior, clutter, V(1.05 + 0.24, -2.0, 0.0), math.pi * 0.5, rng, paint)
    b.loot("food", V(1.05 + 0.2, -2.0, 0.9))
    shelf(interior, V(3.0, -iy, 1.7), V(ix - 0.05, -iy, 1.7), 0.2, V(0.0, 1.0, 0.0), rng)
    for x in (3.1, 3.28, 3.46):
        jar(clutter, V(x, -iy + 0.1, 1.7), rng)
    for y in (-0.35, 0.0, 0.35):
        hanging_pot(clutter, V(2.95, y - 1.95, c1), rng, 0.45)
    bucket(clutter, V(3.35, 1.4, 0.0), rng)
    long_tool(clutter, V(1.25, 2.85, 0.0), V(1.15, 2.95, 1.4), "broom", rng)
    b.loot("toolbox", V(3.3, 2.65, 0.0))
    curtain(clutter, V(2.95, -iy + 0.07, 2.3), V(1.65, -iy + 0.07, 2.3), 1.2, rng, "fabric_worn", 0.35)

    iron_bed(b, interior, clutter, V(-2.7, -1.9, f1), 0.0, rng, 1.95, 1.35)
    suitcase(clutter, V(-2.3, -1.9, f1 + 0.64), 0.4, rng, True)
    b.loot("box", V(-1.4, -2.3, f1))
    wardrobe(b, interior, clutter, V(-3.4, 1.9, f1), math.pi * 0.5, rng)
    top = chest_of_drawers(b, interior, V(-1.3, 0.5, f1), -math.pi * 0.5, rng)
    b.loot("medical", V(-1.3, 0.5, top.z))
    washstand(b, interior, clutter, V(-2.35, 2.72, f1), 0.0, rng)
    rug(clutter, V(-2.3, 0.2, f1), 1.3, 1.9, 0.1, rng)
    chair(interior, V(-1.5, -0.6, f1), -1.2, rng)
    oil_lamp(clutter, V(-3.5, -1.0, f1 + 0.5), rng)
    table(interior, -3.45, -1.0, f1, 0.4, 0.4, 0.5, rng)
    b.light("warm", V(-3.45, -1.0, f1 + 0.75))
    for y in (-0.45, 0.3):
        bottle(clutter, V(-ix + 0.49, y, f1 + 1.16), rng)
    picture(interior, V(-ix + 0.405, 0.0, f1 + 1.65), V(1.0, 0.0, 0.0), 0.55, 0.45, rng, "glass_dirty")
    curtain(clutter, V(-2.95, -iy + 0.07, 5.05), V(-1.65, -iy + 0.07, 5.05), 1.4, rng, "fabric_worn", 0.4)
    curtain(clutter, V(-1.6, iy - 0.07, 5.05), V(-2.9, iy - 0.07, 5.05), 1.1, rng, "fabric_worn", 0.3)
    iron_bed(b, interior, clutter, V(2.45, -2.33, f1), 0.0, rng, 1.9, 0.95, bedding=False)
    chest_of_drawers(b, interior, V(3.46, -1.45, f1), -math.pi * 0.5, rng, 0.8, 0.44, 0.8, "floorboards", 3)
    b.loot("military", V(1.75, -1.0, f1))
    chair(clutter, V(2.0, 0.5, f1), 0.5, rng, fallen=True)
    table(interior, 0.5, -2.7, f1, 0.6, 0.4, 0.74, rng)
    jug(clutter, V(0.5, -2.7, f1 + 0.74), rng)
    picture(interior, V(0.945, -1.6, f1 + 1.6), V(-1.0, 0.0, 0.0), 0.4, 0.5, rng, "wallpaper_faded", "timber_beam", 0.12)

    zone = (collapse[0] + 0.2, ix - 0.15, collapse[2] + 0.1, iy - 0.1)
    for x in fallen:
        foot = V(min(max(x + rng.uniform(-0.3, 0.3), zone[0]), zone[1]), rng.uniform(1.0, 1.8), f1 + 0.08)
        head = V(x + rng.uniform(-0.2, 0.2), iy - rng.uniform(0.0, 0.3), rng.uniform(f1 + 1.6, wall_top - 0.4))
        if rng.random() < 0.45:
            head = V(foot.x + rng.uniform(-1.2, 1.2), foot.y + rng.uniform(0.6, 1.2), f1 + 0.1)
        axis = (head - foot)
        emit(debris, kit.geo_box(axis.length, 0.065, 0.14), "timber_beam", kit.place((foot + head) * 0.5, axis.normalized(), V(0.0, 0.0, 1.0) if abs(axis.normalized().z) < 0.9 else V(1.0, 0.0, 0.0)), "box")
    kit.scatter_chips(debris, "slate_roof", zone[0], zone[1], zone[2], zone[3], f1, 46, rng, (0.08, 0.17), (0.006, 0.008), 0.35)
    kit.scatter_chips(debris, "plaster_interior", zone[0] - 0.3, zone[1], zone[2] - 0.5, zone[3], f1, 50, rng, (0.04, 0.16), (0.012, 0.025))
    kit.plank_debris(debris, "timber_planks_weathered", zone[0], zone[1], zone[2], zone[3], f1 + 0.02, 12, rng, (0.4, 1.3), (0.1, 0.2), 0.022)
    lump(debris, "dirt_debris", V(3.1, 2.55, f1 - 0.02), (0.55, 0.4, 0.1), rng, 0.3, 2, f1)
    lump(debris, "dirt_debris", V(2.0, 1.7, f1 - 0.02), (0.5, 0.45, 0.07), rng, 0.3, 2, f1)
    kit.rubble_pile(debris, V(3.2, 2.6, f1), 0.5, 0.35, rng, 12)
    for index in range(5):
        kit.fern(plants, V(rng.uniform(zone[0], zone[1]), rng.uniform(2.0, zone[3]), f1 + 0.02), rng, (4, 7), (0.25, 0.5))
    for index in range(14):
        kit.grass_tuft(plants, V(rng.uniform(zone[0], zone[1]), rng.uniform(zone[2], zone[3]), f1 + 0.02), rng, (0.1, 0.3), (4, 9), 0.05)
    for index in range(9):
        lump(plants, "roof_moss", V(rng.uniform(zone[0], zone[1]), rng.uniform(zone[2], zone[3]), f1 + 0.02), (rng.uniform(0.08, 0.2), rng.uniform(0.06, 0.15), 0.03), rng, 0.3, 1)
    bucket(clutter, V(1.9, 2.4, f1), rng)
    kit.scatter_chips(debris, "plaster_interior", 1.2, ix - 0.6, -iy + 0.1, 0.5, f1, 18, rng)
    kit.scatter_chips(debris, "plaster_interior", 1.3, 3.5, 1.2, 2.9, 0.0, 26, rng)
    kit.scatter_chips(debris, "slate_roof", 2.4, 3.4, 1.7, 2.8, 0.0, 8, rng, (0.08, 0.16), (0.006, 0.008))
    kit.scatter_chips(debris, "plaster_interior", -ix + 0.5, -1.2, -iy + 0.05, -iy + 0.4, 0.0, 14, rng)
    kit.scatter_chips(debris, "plaster_interior", -ix + 0.5, -1.2, iy - 0.4, iy - 0.05, 0.0, 14, rng)
    kit.scatter_chips(debris, "plaster_interior", -0.9, 0.9, -iy + 0.1, iy - 0.1, 0.0, 20, rng)
    kit.scatter_chips(debris, "wallpaper_faded", -ix + 0.4, -1.2, -iy + 0.3, iy - 0.3, 0.0, 14, rng, (0.06, 0.18), (0.002, 0.003), 0.4)
    kit.scatter_chips(debris, "plaster_interior", -ix + 0.4, -1.2, -iy + 0.1, iy - 0.1, f1, 22, rng)
    kit.scatter_chips(debris, "foliage", -0.6, 0.9, -iy + 0.05, -1.4, 0.0, 30, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    for w in front_ground:
        kit.scatter_chips(debris, "glass_dirty", w[0], w[1], -iy + 0.05, -iy + 0.5, 0.0, 10, rng, (0.02, 0.06), (0.003, 0.004))

    bicycle(clutter, V(2.35, -hy - 0.3, -0.1), 0.06, -0.2, rng)
    dustbin(clutter, V(1.5, hy + 0.4, -0.1), rng)
    barrel(b, clutter, V(-ix - 0.05, hy + 0.45, -0.1), rng)
    post = V(-2.3, hy + 2.7, -0.1)
    rod(clutter, "rusty_metal", post, post + V(0.03, 0.05, 2.15), 0.025, 8)
    line = [V(-2.3, hy + 0.02, 2.2)] + [V(-2.3 + 0.03 * t / 8, hy + 0.02 + 2.7 * t / 8, 2.2 - 0.28 * math.sin(math.pi * t / 8)) for t in range(1, 8)] + [post + V(0.03, 0.05, 2.1)]
    emit(clutter, kit.geo_tube(line, kit.circle(0.004, 4), False), "hay", None, "given", True)
    curtain(clutter, line[3] + V(0.0, 0.0, -0.01), line[4] + V(0.0, 0.0, -0.01), 0.7, rng, "fabric_worn", 1.0)
    curtain(clutter, line[5] + V(0.0, 0.0, -0.01), line[6] + V(0.0, 0.0, -0.01), 0.45, rng, "fabric_tartan", 1.0)
    b.col("metal", "post", post - V(0.03, 0.03, 0.0), post + V(0.06, 0.08, 2.15))
    kit.rubble_pile(debris, V(3.0, hy + 0.55, -0.12), 0.85, 0.45, rng, 24)
    b.col("rock", "rubble", V(2.3, hy, -0.12), V(3.7, hy + 1.2, 0.18))
    kit.scatter_chips(debris, "slate_roof", 1.4, 4.0, hy + 0.2, hy + 1.6, -0.1, 22, rng, (0.08, 0.17), (0.006, 0.008))
    fallen_shutter = kit.Matrix.Translation(V(-2.0, -hy - 0.8, -0.08)) @ kit.Matrix.Rotation(-0.4, 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5 - 0.05, 4, 'X')
    local_block(joinery, paint, fallen_shutter, 0.0, 0.05, 0.0, 0.03, 0.0, 1.35, 0.003, "board")
    local_block(joinery, paint, fallen_shutter, 0.52, 0.57, 0.0, 0.03, 0.0, 1.35, 0.003, "board")
    for z in (0.045, 0.675, 1.31):
        local_block(joinery, paint, fallen_shutter, 0.05, 0.52, 0.0, 0.03, z - 0.04, z + 0.04, 0.003, "board")
    base_weeds(plants, -hx, hx, -hy, hy, rng, 1.2, lambda p: (abs(p.x) < 1.1 and p.y < 0.0) or (-0.1 < p.x < 1.1 and p.y > 0.0) or (p.x > 2.2 and p.y > 0.0))
    kit.ivy(plants, V(hx + 0.03, -1.8, -0.1), V(1.0, 0.0, 0.0), rng, 4.6, 1.1, 8, 28.0)
    kit.ivy(plants, V(hx + 0.03, 2.4, -0.1), V(1.0, 0.0, 0.0), rng, 3.2, 0.7, 5, 26.0)
    kit.ivy(plants, V(3.0, hy + 0.03, -0.1), V(0.0, 1.0, 0.0), rng, 2.6, 0.7, 5, 26.0)
    for index in range(10):
        lump(plants, "roof_moss", V(rng.uniform(-ix, ix), rng.uniform(-0.05, 0.08), gable.ridge_top + 0.085), (rng.uniform(0.06, 0.14), 0.09, 0.035), rng, 0.3, 1)
    kit.deform(sag_roof[0], kit.sagging(*sag_roof[1:]))
    kit.deform(plants, kit.sagging(-ix, ix, gable.ridge_top - 0.3, gable.ridge_top, 0.06))
    return b


def house_far():
    b = kit.Build("house_far", 202)
    shell = b.part("shell", 30.0)
    rng = b.rng
    hx, hy, ix = 4.2, 3.5, 3.7
    gable = kit.Gable(-ix, ix, hy, 0.25, 5.48, 40.0)
    wall_top = gable.under(hy, 0.03)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    kit.wall(shell, "granite_rubble", front, kit.rect(-ix, ix, -1.5, wall_top), [], 0.5)
    kit.wall(shell, "granite_rubble", back, [(-ix, -1.5), (ix, -1.5), (ix, wall_top), (-1.6, wall_top), (-2.4, wall_top - 0.35), (-3.2, wall_top - 0.5), (-ix, wall_top - 0.75)], [], 0.5)
    for side in ("left", "right"):
        outline = [(-hy, -1.5), (hy, -1.5), (hy, gable.top(hy) + 0.2), (0.0, gable.ridge_top + 0.2), (-hy, gable.top(hy) + 0.2)]
        kit.wall(shell, "granite_rubble", kit.facade(side, hx, hy), outline, [], 0.5)
    front_open = [(-0.5, 0.5, 0.0, 2.45), (-2.85, -1.75, 0.8, 2.2), (1.75, 2.85, 0.8, 2.2), (-2.85, -1.75, 3.6, 4.95), (1.75, 2.85, 3.6, 4.95), (-0.45, 0.45, 3.75, 4.85)]
    back_open = [(-0.95, 0.0, 0.0, 2.1), (-2.8, -1.7, 1.0, 2.2), (1.7, 2.8, 0.8, 2.2), (1.7, 2.8, 3.6, 4.95), (-2.8, -1.7, 3.6, 4.95)]
    kit.skin(shell, "render_white", front, kit.rect(-ix + 0.03, ix - 0.03, 0.4, wall_top - 0.03), [kit.rect(*o) for o in front_open[1:]] + [kit.rect(-0.5, 0.5, 0.41, 2.45)], 0.02, 0.0, False)
    kit.skin(shell, "render_white", back, kit.rect(-1.55, ix - 0.03, 0.4, wall_top - 0.03), [kit.rect(1.7, 2.8, 0.8, 2.2), kit.rect(1.7, 2.8, 3.6, 4.95), kit.rect(-0.95, 0.0, 0.41, 2.1)], 0.02, 0.0, False)
    kit.skin(shell, "render_white", kit.facade("right", hx, hy), [(-hy + 0.05, 0.5), (hy - 0.05, 0.4), (hy - 0.05, 3.9), (1.0, 4.9), (-0.8, 4.2), (-hy + 0.05, 5.0)], [], 0.02, 0.0, False)
    kit.skin(shell, "render_pink", kit.facade("left", hx, hy), [(-hy + 0.05, 0.4), (hy - 0.05, 0.4), (hy - 0.05, 4.2), (0.0, 6.3), (-hy + 0.05, 4.2)], [], 0.015, 0.0, False)
    for frame, openings in ((front, front_open), (back, back_open)):
        for a0, a1, b0, b1 in openings:
            kit.skin(shell, "soot", frame, kit.rect(a0, a1, b0, b1), [], 0.004, 0.022, False)
    kit.roof_slab(shell, gable, -1.0, -ix, ix, "slate_roof")
    kit.roof_slab(shell, gable, 1.0, -ix, 1.4, "roof_moss")
    kit.roof_slab(shell, gable, 1.0, 1.4, ix, "slate_roof", 0.2, 3.6)
    kit.roof_slab(shell, gable, 1.0, 1.4, ix, "soot", 0.05, 0.0, 3.6)
    for x in (-hx + 0.29, hx - 0.29):
        block(shell, "granite_ashlar", V(x - 0.29, -0.65, gable.top(0.65) - 0.3), V(x + 0.29, 0.65, gable.ridge_top + 1.22))
        block(shell, "terracotta", V(x - 0.1, -0.45, gable.ridge_top + 1.22), V(x + 0.1, 0.45, gable.ridge_top + 1.6))
    block(shell, "terracotta", V(-ix, -0.13, gable.ridge_top - 0.04), V(ix, 0.13, gable.ridge_top + 0.09))
    for a0, a1, b0, b1 in ((-3.43, -2.86, 0.8, 2.2), (-1.74, -1.17, 0.8, 2.2), (2.86, 3.43, 0.8, 2.2), (-3.43, -2.86, 3.6, 4.95), (1.18, 1.74, 3.6, 4.95), (2.86, 3.43, 3.6, 4.95)):
        kit.skin(shell, "painted_wood_green", front, kit.rect(a0, a1, b0, b1), [], 0.03, 0.024, False)
    for frame, spans in ((front, ((-hx, -0.72), (0.72, hx))), (back, ((-hx, -1.05), (0.1, hx))), (kit.facade("left", hx, hy), ((-hy, hy),)), (kit.facade("right", hx, hy), ((-hy, hy),))):
        for a0, a1 in spans:
            frame_block(shell, "concrete", frame, a0, a1, -1.5, 0.35, -0.035, 0.0)
    frame_block(shell, "granite_ashlar", front, -0.9, 0.9, -1.5, 0.0, -0.75, 0.0)
    far_trim(shell, gable, hx, hy, 0.5, [gable.top(hy) + 0.18] * 4, 0.2)
    return b


def sapling(part, position, rng, height=2.6, bark="timber_planks_weathered", leaf="foliage"):
    lean = V(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0.0)
    sway = V(rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), 0.0)
    trunk = [position + V(0.0, 0.0, -0.05) + lean * (t / 8) ** 1.5 + sway * math.sin(t * 0.9) + V(0.0, 0.0, height * t / 8) for t in range(9)]
    emit(part, kit.geo_tube(trunk, kit.circle(0.03, 6), True, V(1.0, 0.0, 0.0), [1.0, 0.9, 0.8, 0.68, 0.56, 0.45, 0.34, 0.24, 0.12]), bark, None, "given", True)
    for index in range(rng.randint(13, 17)):
        t = 0.28 + 0.7 * index / 16 + rng.uniform(-0.02, 0.02)
        spot = min(t * 8, 7.999)
        start = trunk[int(spot)].lerp(trunk[int(spot) + 1], spot % 1.0)
        yaw = index * 2.4 + rng.uniform(-0.4, 0.4)
        reach = rng.uniform(0.45, 0.85) * (1.25 - t) * height * 0.32
        out = V(math.cos(yaw), math.sin(yaw), 0.0)
        tip = start + out * reach + V(0.0, 0.0, reach * rng.uniform(0.45, 0.9))
        mid = start.lerp(tip, 0.5) + V(0.0, 0.0, reach * 0.1)
        emit(part, kit.geo_tube([start, mid, tip], kit.circle(0.009, 4), True, V(0.0, 0.0, 1.0), [1.0, 0.65, 0.25]), bark, None, "given", True)
        for cluster in (mid, mid.lerp(tip, 0.55), tip):
            for count in range(rng.randint(6, 9)):
                p = cluster + V(rng.uniform(-0.13, 0.13), rng.uniform(-0.13, 0.13), rng.uniform(-0.09, 0.11))
                kit.leaf_quad(part, p, V(rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 1.0), out + V(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3)), rng.uniform(0.06, 0.1), rng, leaf)
    for count in range(rng.randint(8, 12)):
        p = trunk[-1] + V(rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(-0.2, 0.06))
        kit.leaf_quad(part, p, V(rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 1.0), V(rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), 0.4), rng.uniform(0.06, 0.1), rng, leaf)


def bramble(part, position, rng, arcs=5, reach=(0.6, 1.3), name="foliage"):
    for index in range(arcs):
        yaw = rng.uniform(0.0, tau)
        span = rng.uniform(*reach)
        peak = span * rng.uniform(0.35, 0.6)
        path = [position + V(math.cos(yaw) * span * t / 7, math.sin(yaw) * span * t / 7, peak * math.sin(math.pi * min(t / 6.0, 1.0)) - 0.05) for t in range(8)]
        emit(part, kit.geo_tube(path, kit.circle(0.006, 4), True), "timber_beam", None, "given", True)
        for t in range(1, 8):
            for sign in (-1.0, 1.0):
                side = V(-math.sin(yaw), math.cos(yaw), 0.0) * sign
                kit.leaf_quad(part, path[t] + side * 0.03, V(0.0, 0.0, 1.0) + side * 0.5, side + V(math.cos(yaw), math.sin(yaw), 0.0) * 0.4, rng.uniform(0.05, 0.08), rng, name)


def campfire(build, part, position, rng, lit=True):
    for index in range(9):
        angle = tau * index / 9 + rng.uniform(-0.15, 0.15)
        lump(part, "granite_rubble", position + V(math.cos(angle) * 0.32, math.sin(angle) * 0.32, 0.05), (rng.uniform(0.07, 0.11), rng.uniform(0.06, 0.09), rng.uniform(0.05, 0.08)), rng, 0.2, 1, None, None, False)
    lump(part, "soot", position + V(0.0, 0.0, 0.02), (0.26, 0.26, 0.04), rng, 0.3, 2, position.z)
    for index in range(4):
        angle = rng.uniform(0.0, tau)
        a = position + V(math.cos(angle) * 0.22, math.sin(angle) * 0.22, 0.06)
        c = position + V(-math.cos(angle) * 0.1, -math.sin(angle) * 0.1, 0.12)
        emit(part, kit.geo_tube([a, c], kit.circle(0.03, 6), True), "timber_charred", None, "given", True)
    if lit:
        build.light("fire", position + V(0.0, 0.0, 0.25))


def workbench(build, part, clutter, center, yaw, rng, length=2.6, depth=0.58, height=0.9):
    base = kit.turned(center, yaw)
    hl = length * 0.5
    hd = depth * 0.5
    for index in range(3):
        y0 = -hd + depth * index / 3
        local_block(part, "timber_planks_weathered", base, -hl, hl, y0 + 0.003, y0 + depth / 3 - 0.003, height - 0.05, height, 0.004, "board")
    for sx in (-hl + 0.08, 0.0, hl - 0.08):
        for sy in (-hd + 0.06, hd - 0.06):
            local_block(part, "timber_beam", base, sx - 0.04, sx + 0.04, sy - 0.04, sy + 0.04, 0.0, height - 0.05, 0.005)
    local_block(part, "timber_planks_weathered", base, -hl + 0.05, hl - 0.05, -hd + 0.04, hd - 0.04, 0.22, 0.25, 0.003, "board")
    local_block(part, "timber_beam", base, -hl + 0.04, hl - 0.04, -hd + 0.03, -hd + 0.07, height - 0.16, height - 0.05)
    vice = base @ kit.Matrix.Translation(V(hl - 0.35, -hd + 0.02, height))
    local_block(part, "rusty_metal", vice, -0.08, 0.08, -0.04, 0.1, 0.0, 0.05, 0.004)
    local_block(part, "rusty_metal", vice, -0.07, 0.07, 0.04, 0.08, 0.05, 0.16, 0.004)
    local_block(part, "rusty_metal", vice, -0.07, 0.07, -0.1, -0.06, 0.05, 0.16, 0.004)
    rod(part, "rusty_metal", vice @ V(0.0, -0.2, 0.09), vice @ V(0.0, 0.06, 0.09), 0.012, 6)
    rod(part, "rusty_metal", vice @ V(-0.09, -0.2, 0.09), vice @ V(0.09, -0.2, 0.09), 0.006, 5)
    footprint(build, "wood", "bench", base, hl, hd, 0.0, height)
    return base


def jerrycan(part, position, yaw, rng, name="rusty_metal"):
    base = kit.turned(position, yaw)
    local_block(part, name, base, -0.17, 0.17, -0.085, 0.085, 0.0, 0.43, 0.02)
    for x in (-0.09, 0.0, 0.09):
        rod(part, name, base @ V(x, -0.05, 0.47), base @ V(x, 0.05, 0.47), 0.009, 5)
        rod(part, name, base @ V(x, -0.05, 0.43), base @ V(x, -0.05, 0.47), 0.009, 5)
        rod(part, name, base @ V(x, 0.05, 0.43), base @ V(x, 0.05, 0.47), 0.009, 5)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.025, 0.0), (0.025, 0.05), (0.0, 0.05)], 8), name, base @ kit.Matrix.Translation(V(0.13, 0.0, 0.43)), "given", True)


def tyre(part, position, rng, matrix=None, name="soot"):
    profile = [(0.25 + 0.085 * math.cos(tau * t / 10), 0.085 * math.sin(tau * t / 10)) for t in range(11)]
    emit(part, kit.geo_lathe(profile, 16), name, matrix if matrix is not None else kit.Matrix.Translation(position + V(0.0, 0.0, 0.085)), "given", True)


def solid(points, faces):
    middle = sum(points, V(0.0, 0.0, 0.0)) / len(points)
    oriented = []
    for face in faces:
        center = sum((points[i] for i in face), V(0.0, 0.0, 0.0)) / len(face)
        oriented.append(kit.orient(face, points, center - middle))
    return kit.Geo(points, oriented)


def dinghy(build, part, center, yaw, rng, length=2.7, beam=1.25, depth=0.46, paint="painted_wood_blue", keel="timber_beam", stations=12, girth=10, collide=True):
    base = kit.turned(center, yaw)
    points = []
    uvs_grid = []
    for i in range(stations + 1):
        t = i / stations
        x = -length * 0.5 + length * t
        half = max(beam * 0.5 * (0.72 + 0.28 * math.sin(math.pi * min(t / 0.85, 1.0) * 0.5)) * (1.0 - max(0.0, (t - 0.5) / 0.5) ** 2.2), 0.015)
        deep = depth * (0.85 + 0.15 * (1.0 - abs(t - 0.4) * 1.2)) * (1.0 - 0.6 * max(0.0, (t - 0.75) / 0.25) ** 2)
        travelled = 0.0
        previous = None
        for j in range(girth + 1):
            phi = math.pi * j / girth
            p = V(x, half * math.cos(phi), deep * math.sin(phi) ** 0.75)
            if previous is not None:
                travelled += (p - previous).length
            previous = p
            points.append(p)
            uvs_grid.append((x, travelled))
    faces = []
    uvs = []
    for i in range(stations):
        for j in range(girth):
            a = i * (girth + 1) + j
            quad = (a, a + 1, a + girth + 2, a + girth + 1)
            corners = [points[k] for k in quad]
            outward = V(0.0, corners[0].y + corners[2].y, corners[0].z + corners[2].z + 0.2)
            face, face_uv = kit.oriented_face(quad, [uvs_grid[k] for k in quad], points, outward)
            faces.append(face)
            uvs.append(face_uv)
    emit(part, kit.Geo(points, faces, uvs), paint, base, "given", True)
    transom = [points[j] for j in range(girth + 1)]
    emit(part, kit.Geo(transom, [kit.orient(tuple(range(girth + 1)), transom, V(-1.0, 0.0, 0.0))]), paint, base, "box")
    ridge = [points[i * (girth + 1) + girth // 2] + V(0.0, 0.0, 0.015) for i in range(stations + 1)]
    emit(part, kit.geo_tube(ridge, [(-0.02, -0.025), (0.02, -0.025), (0.02, 0.025), (-0.02, 0.025)], True, V(0.0, 0.0, 1.0)), keel, base, "given")
    for side in (-1.0, 1.0):
        rail = [points[i * (girth + 1) + (0 if side > 0 else girth)] + V(0.0, side * 0.012, 0.025) for i in range(stations + 1)]
        emit(part, kit.geo_tube(rail, [(-0.014, -0.025), (0.014, -0.025), (0.014, 0.025), (-0.014, 0.025)], True, V(0.0, 0.0, 1.0)), keel, base, "given")
    corners = [base @ V(sx * length * 0.5, sy * beam * 0.5, 0.0) for sx in (-1, 1) for sy in (-1, 1)]
    if collide:
        build.col("wood", "dinghy", V(min(c.x for c in corners), min(c.y for c in corners), center.z), V(max(c.x for c in corners), max(c.y for c in corners), center.z + depth))


def cart(build, part, center, yaw, rng, wood="timber_planks_weathered", beam="timber_beam", pitch=0.2):
    axle = kit.turned(center + V(0.0, 0.0, 0.6), yaw)
    body = axle @ kit.Matrix.Rotation(pitch, 4, 'Y')
    axis = (axle @ V(0.0, 1.0, 0.0)) - (axle @ V(0.0, 0.0, 0.0))
    for sy in (-0.8, 0.8):
        wheel_spoked(part, axle @ V(0.0, sy, 0.0), axis, 0.55, rng, 12, beam, "rusty_metal", 0.09, 0.07)
    rod(part, "rusty_metal", axle @ V(0.0, -0.86, 0.0), axle @ V(0.0, 0.86, 0.0), 0.03, 8)
    for index in range(7):
        y0 = -0.62 + 1.24 * index / 7
        local_block(part, wood, body, -1.05, 1.0, y0 + 0.003, y0 + 1.24 / 7 - 0.003, 0.14, 0.17, 0.003, "board")
    for sy in (-0.62, 0.62):
        local_block(part, beam, body, -1.1, 1.05, sy - 0.04, sy + 0.04, 0.05, 0.14, 0.006)
        for index in range(3):
            if rng.random() < 0.2:
                continue
            local_block(part, wood, body, -1.05, 1.0, sy - 0.012, sy + 0.012, 0.19 + index * 0.15, 0.31 + index * 0.15, 0.003, "board")
        for x in (-1.0, -0.35, 0.3, 0.95):
            local_block(part, beam, body, x - 0.025, x + 0.025, sy - 0.035 * (1 if sy > 0 else -1) - 0.02, sy - 0.035 * (1 if sy > 0 else -1) + 0.02, 0.17, 0.68, 0.004)
    local_block(part, wood, body, -1.06, -1.03, -0.6, 0.6, 0.17, 0.55, 0.003, "board")
    for sy in (-0.45, 0.45):
        local_block(part, beam, body, 1.0, 3.0, sy - 0.035, sy + 0.035, 0.06, 0.14, 0.008)
    local_block(part, beam, body, 1.5, 1.57, -0.45, 0.45, 0.07, 0.13, 0.004)
    for sy in (-0.3, 0.3):
        local_block(part, beam, body, -0.08, 0.08, sy - 0.05, sy + 0.05, -0.04, 0.05, 0.004)
    corners = [axle @ V(sx, sy, 0.0) for sx in (-1.1, 1.1) for sy in (-0.9, 0.9)]
    build.col("wood", "cart", V(min(c.x for c in corners), min(c.y for c in corners), center.z), V(max(c.x for c in corners), max(c.y for c in corners), center.z + 1.35))


def plough(part, position, yaw, rng, iron="rusty_metal", wood="timber_beam"):
    base = kit.turned(position, yaw)
    local_block(part, wood, base, -0.4, 1.3, -0.04, 0.04, 0.42, 0.5, 0.008)
    for sy in (-1.0, 1.0):
        a = base @ V(-0.35, sy * 0.04, 0.45)
        c = base @ V(-1.25, sy * 0.28, 0.95)
        emit(part, kit.geo_cbox((c - a).length, 0.045, 0.05, 0.006), wood, kit.place((a + c) * 0.5, (c - a).normalized(), V(0.0, 0.0, 1.0)), "box")
    rod(part, wood, base @ V(-1.0, -0.2, 0.8), base @ V(-1.0, 0.2, 0.8), 0.018, 6)
    share = [V(-0.2, 0.0, 0.42), V(0.35, 0.0, 0.42), V(0.55, 0.02, 0.02), V(-0.1, 0.25, 0.05), V(-0.3, 0.3, 0.3)]
    emit(part, solid([base @ p for p in share] + [base @ (p + V(0.0, 0.014, 0.0)) for p in share], [(0, 1, 2, 3, 4), (9, 8, 7, 6, 5), (0, 5, 6, 1), (1, 6, 7, 2), (2, 7, 8, 3), (3, 8, 9, 4), (4, 9, 5, 0)]), iron, None, "box")
    local_block(part, iron, base, 0.6, 0.64, -0.006, 0.006, 0.05, 0.46)
    axis = (base @ V(0.0, 1.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))
    wheel_spoked(part, base @ V(1.2, 0.0, 0.2), axis, 0.2, rng, 8, iron, iron, 0.03, 0.04, True)
    rod(part, iron, base @ V(1.2, 0.0, 0.2), base @ V(1.2, 0.0, 0.44), 0.012, 5)


def wheelbarrow(part, position, yaw, rng, wood="timber_planks_weathered", beam="timber_beam"):
    base = kit.turned(position, yaw)
    axis = (base @ V(0.0, 1.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))
    wheel_spoked(part, base @ V(0.75, 0.0, 0.25), axis, 0.2, rng, 8, beam, "rusty_metal", 0.04, 0.05)
    for sy in (-1.0, 1.0):
        a = base @ V(0.78, sy * 0.06, 0.25)
        c = base @ V(-0.85, sy * 0.3, 0.55)
        emit(part, kit.geo_cbox((c - a).length, 0.04, 0.05, 0.005), beam, kit.place((a + c) * 0.5, (c - a).normalized(), V(0.0, 0.0, 1.0)), "box")
        local_block(part, beam, base, -0.35, -0.3, sy * 0.24 - 0.02, sy * 0.24 + 0.02, 0.0, 0.42, 0.004)
        local_block(part, wood, base, -0.45, 0.45, sy * 0.3 - 0.01, sy * 0.3 + 0.01, 0.42, 0.68, 0.003, "board")
    local_block(part, wood, base, -0.45, 0.45, -0.3, 0.3, 0.4, 0.42, 0.003, "board")
    local_block(part, wood, base, 0.44, 0.46, -0.3, 0.3, 0.42, 0.7, 0.003, "board")


def churn(part, position, rng, name="corrugated_rusty", tipped=False):
    profile = [(0.0, 0.0), (0.16, 0.0), (0.165, 0.02), (0.165, 0.42), (0.11, 0.52), (0.11, 0.6), (0.13, 0.62), (0.13, 0.64), (0.0, 0.64)]
    if tipped:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, 0.165)) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -0.3))
    else:
        matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, kit.geo_lathe(profile, 16), name, matrix, "given", True)


def stall(build, part, x, y0, y1, height, rng, wood="timber_planks_weathered", post="timber_beam"):
    for y in (y0, y1):
        block(part, post, V(x - 0.06, y - 0.06, 0.0), V(x + 0.06, y + 0.06, height + 0.25), 0.008)
    z = 0.12
    while z < height - 0.1:
        h = rng.uniform(0.18, 0.24)
        if rng.random() > 0.12:
            sag = rng.uniform(-0.02, 0.02)
            emit(part, kit.geo_box(abs(y1 - y0) - 0.1, 0.03, h - 0.015), wood, kit.place(V(x, (y0 + y1) * 0.5, z + h * 0.5 + sag), V(0.0, 1.0, sag * 0.3), V(0.0, 0.0, 1.0)), "board")
        z += h
    build.col("wood", "stall", V(x - 0.06, min(y0, y1), 0.0), V(x + 0.06, max(y0, y1), height))


def hay_heap(part, center, radius, height, rng, loose=True):
    lump(part, "hay", center + V(0.0, 0.0, height * 0.25), (radius, radius * rng.uniform(0.75, 1.0), height * 0.8), rng, 0.3, 3, center.z)
    if loose:
        kit.scatter_chips(part, "hay", center.x - radius * 1.2, center.x + radius * 1.2, center.y - radius * 1.2, center.y + radius * 1.2, center.z + 0.004, int(12 * radius * radius) + 5, rng, (0.1, 0.28), (0.004, 0.012), 0.2)


def ruin():
    b = kit.Build("ruin", 301)
    rng = b.rng
    shell = b.part("shell", 30.0)
    timbers = b.part("timbers", 35.0)
    floors = b.part("floors", 35.0)
    clutter = b.part("clutter", 45.0)
    debris = b.part("debris", 40.0)
    plants = b.part("plants", 70.0)
    hx = 4.0
    hy = 2.75
    wall_t = 0.55
    ix = hx - wall_t
    iy = hy - wall_t
    stone = "granite_rubble"
    dressed = "granite_ashlar"
    char = "timber_charred"
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    window = (-2.6, -1.7, 0.9, 1.9)

    front_left = kit.ragged_top(-ix, -0.5, kit.piecewise([(-ix, 2.75), (-2.9, 2.7), (-1.5, 2.6), (-0.5, 2.35)]), rng)
    front_right = kit.ragged_top(0.5, 1.68, kit.piecewise([(0.5, 2.0), (1.68, 1.4)]), rng) + [(1.7, 0.95), (2.6, 0.95)] + kit.ragged_top(2.62, ix, kit.piecewise([(2.62, 1.3), (ix, 1.9)]), rng)
    front_top = front_left + [(-0.5, 0.0), (0.5, 0.0)] + front_right
    kit.wall(shell, stone, front, [(-ix, -1.5), (ix, -1.5)] + list(reversed(front_left + [(-0.5, -0.05), (0.5, -0.05)] + front_right)), [kit.rect(*window)], wall_t)
    gable_line = lambda a: 2.75 + (hy - abs(a)) * 0.78
    left_shape = kit.piecewise([(-hy, 2.5), (-1.6, 3.1), (-0.7, 4.4), (0.7, 4.4), (1.4, 3.7), (hy, 3.1)])
    left_profile = lambda a: min(gable_line(a), left_shape(a))
    left_top = kit.ragged_top(-hy, -0.55, left_profile, rng) + [(-0.55, 5.25), (0.55, 5.1)] + kit.ragged_top(0.55, hy, left_profile, rng)
    kit.wall(shell, stone, left, [(-hy, -1.5), (hy, -1.5)] + list(reversed(left_top)), [], wall_t)
    right_top = kit.ragged_top(-hy, hy, kit.piecewise([(-hy, 1.9), (-1.8, 1.25), (-0.6, 0.9), (0.5, 1.3), (1.5, 1.0), (2.2, 1.6), (hy, 2.0)]), rng)
    kit.wall(shell, stone, right, [(-hy, -1.5), (hy, -1.5)] + list(reversed(right_top)), [], wall_t)
    back_top = kit.ragged_top(-ix, -1.47, kit.piecewise([(-ix, 1.95), (-2.6, 1.35), (-1.47, 0.95)]), rng) + [(-1.45, 0.4), (-0.55, 0.4)] + kit.ragged_top(-0.53, 1.23, kit.piecewise([(-0.53, 1.1), (0.6, 1.6), (1.23, 2.3)]), rng) + [(1.25, 1.0), (2.05, 1.0)] + kit.ragged_top(2.07, ix, kit.piecewise([(2.07, 2.2), (ix, 2.5)]), rng)
    kit.wall(shell, stone, back, [(-ix, -1.5), (ix, -1.5)] + list(reversed(back_top)), [], wall_t)
    front_solid = [(min(a, -0.53), h) for a, h in front_left] + [(-0.53, 0.0), (0.53, 0.0)] + [(max(a, 0.53), h) for a, h in front_right]
    kit.ruin_boxes(b, "rock", "front", front, [p for p in front_solid if p[0] <= window[0]] + [(window[0], 2.6)], -1.5, wall_t)
    kit.wall_boxes(b, "rock", "front", front, window[0], window[1], -1.5, 2.5, wall_t, [window])
    kit.ruin_boxes(b, "rock", "front", front, [(window[1], 2.5)] + [p for p in front_solid if p[0] >= window[1]], -1.5, wall_t)
    kit.ruin_boxes(b, "rock", "left", left, left_top, -1.5, wall_t)
    kit.ruin_boxes(b, "rock", "right", right, right_top, -1.5, wall_t)
    kit.ruin_boxes(b, "rock", "back", back, back_top, -1.5, wall_t)
    for frame, tops in ((front, front_top), (left, left_top), (right, right_top), (back, back_top)):
        for (a0, h0), (a1, h1) in zip(tops[:-1], tops[1:]):
            if a1 - a0 < 0.1 or min(h0, h1) < 0.3:
                continue
            a = a0 + rng.uniform(0.02, 0.12)
            while a < a1 - 0.04:
                size3 = (rng.uniform(0.1, 0.2), rng.uniform(0.09, 0.17), rng.uniform(0.06, 0.12))
                if rng.random() < 0.8:
                    lump(debris, rng.choice((dressed, dressed, stone)), kit.frame_point(frame, a, min(h0, h1) + size3[2] * rng.uniform(0.1, 0.6), -rng.uniform(0.1, wall_t - 0.1)), size3, rng, 0.22, 1, None, None, False)
                a += rng.uniform(0.16, 0.34)
            if rng.random() < 0.3:
                lump(plants, "roof_moss", kit.frame_point(frame, (a0 + a1) * 0.5, min(h0, h1) + 0.02, -rng.uniform(0.1, wall_t - 0.1)), (rng.uniform(0.12, 0.25), rng.uniform(0.1, 0.18), 0.035), rng, 0.3, 1)
    for corner, ua, ub, top in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), 2.6), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), 1.75), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0), 1.85), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0), 2.35)):
        kit.quoins(shell, dressed, corner, ua, ub, -0.3, top, rng)
    kit.lintel_stone(shell, dressed, front, window[0], window[1], window[3], 0.26, 0.3, 0.02, 0.18)
    kit.sill_stone(shell, dressed, front, window[0], window[1], window[2], 0.18, 0.06, 0.09, 0.07)
    kit.sill_stone(shell, dressed, front, 1.7, 2.6, 0.95, 0.18, 0.06, 0.09, 0.07)
    kit.sill_stone(shell, dressed, back, 1.25, 2.05, 1.0, 0.18, 0.06, 0.09, 0.07)
    kit.jamb_stones(shell, dressed, front, -0.5, -1.0, 0.0, 2.2, rng)
    kit.jamb_stones(shell, dressed, front, 0.5, 1.0, 0.0, 1.85, rng)
    frame_block(shell, dressed, front, -0.55, 0.55, -0.2, 0.0, -0.22, wall_t, 0.015)
    for frame, a_low, a_high, gaps in ((front, -ix, ix, [(-0.52, 0.52)]), (back, -ix, ix, [(-1.5, -0.5)]), (left, -hy, hy, ()), (right, -hy, hy, ())):
        damp_band(shell, frame, a_low, a_high, rng, 0.25, 0.7, gaps=gaps)
    for member_a, member_b in ((V(window[0] + 0.04, -hy + 0.18, window[2]), V(window[0] + 0.04, -hy + 0.18, window[3])), (V(window[1] - 0.04, -hy + 0.18, window[2] + 0.3), V(window[1] - 0.04, -hy + 0.18, window[3])), (V(window[0], -hy + 0.18, window[3] - 0.04), V(window[1], -hy + 0.18, window[3] - 0.04))):
        emit(timbers, kit.geo_cbox((member_b - member_a).length, 0.07, 0.07, 0.006), char, kit.place((member_a + member_b) * 0.5, (member_b - member_a).normalized(), V(0.0, 1.0, 0.0)), "box")
    emit(timbers, kit.geo_cbox(1.9, 0.09, 0.08, 0.008), char, kit.place(V(-0.46, -hy + 0.2, 0.95), V(0.06, 0.0, 1.0), V(0.0, 1.0, 0.0)), "box")

    breast = (-ix, -ix + 0.55, -1.1, 1.1)
    block(shell, stone, V(breast[0], breast[2], 0.0), V(breast[1], -0.7, 3.4), 0.0, "world")
    block(shell, stone, V(breast[0], 0.7, 0.0), V(breast[1], breast[3], 3.1), 0.0, "world")
    block(shell, stone, V(breast[0], -0.7, 1.5), V(breast[1], 0.7, 3.6), 0.0, "world")
    block(shell, stone, V(breast[0], -0.5, 3.6), V(breast[1] - 0.1, 0.5, 4.4), 0.0, "world")
    fire_recess(shell, breast[1], 0.0, 1.4, 1.22, 0.5, 1.0, rng, lintel_beam=False)
    b.col("rock", "breast", V(breast[0], breast[2], 0.0), V(breast[1], -0.7, 3.1))
    b.col("rock", "breast", V(breast[0], 0.7, 0.0), V(breast[1], breast[3], 3.1))
    b.col("rock", "breast", V(breast[0], -0.7, 1.22), V(breast[1], 0.7, 3.6))
    for y, z in ((-0.95, 3.44), (-0.8, 3.45), (0.85, 3.14), (1.0, 3.15), (0.6, 3.64), (-0.6, 3.65)):
        lump(debris, stone, V(rng.uniform(breast[0] + 0.12, breast[1] - 0.12), y, z), (rng.uniform(0.12, 0.2), rng.uniform(0.1, 0.15), rng.uniform(0.07, 0.1)), rng, 0.2, 1, None, None, False)
    lump(debris, "soot", V(breast[1] - 0.25, 0.0, 0.04), (0.2, 0.42, 0.05), rng, 0.3, 2, 0.026)
    for y in (-0.38, 0.08, 0.36):
        lump(debris, stone, V(breast[1] - rng.uniform(0.12, 0.34), y, 0.09), (rng.uniform(0.09, 0.16), rng.uniform(0.08, 0.12), rng.uniform(0.06, 0.09)), rng, 0.2, 1, None, None, False)
    fire = V(-1.35, 0.15, 0.0)
    campfire(b, clutter, fire, rng)
    apex = fire + V(0.0, 0.0, 1.18)
    for angle in (0.5, 2.6, 4.7):
        rod(clutter, "rusty_metal", fire + V(math.cos(angle) * 0.48, math.sin(angle) * 0.48, 0.0), apex + V(-math.cos(angle) * 0.03, -math.sin(angle) * 0.03, 0.06), 0.009, 5)
    hanging_pot(clutter, apex, rng, 0.3)
    for frame, a_low, a_high, gaps in (((V(0.0, -iy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), V(0.0, 1.0, 0.0)), -ix, ix, [(-0.52, 0.52)]), ((V(0.0, iy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), V(0.0, -1.0, 0.0)), -ix, ix, [(0.5, 1.5)]), (kit.plane(V(-ix, 0.0, 0.0), V(1.0, 0.0, 0.0)), -iy, iy, ()), (kit.plane(V(ix, 0.0, 0.0), V(-1.0, 0.0, 0.0)), -iy, iy, ())):
        damp_band(shell, frame, a_low, a_high, rng, 0.2, 0.6, "granite_rubble_damp", -0.1, gaps=gaps)

    block(floors, "dirt_debris", V(-ix, -iy, -0.35), V(ix, iy, -0.03), 0.0, "world")
    kit.flagstones(floors, dressed, -ix + 0.55, -0.8, -1.5, 1.5, 0.0, rng, (0.4, 0.7), 0.014, 0.06, 0.012, 0.012, "dirt_debris", lambda x, y: rng.random() < 0.38)
    for index in range(16):
        lump(floors, "dirt_debris", V(rng.uniform(-ix + 0.3, ix - 0.3), rng.uniform(-iy + 0.3, iy - 0.3), -0.03), (rng.uniform(0.3, 0.8), rng.uniform(0.3, 0.7), rng.uniform(0.05, 0.11)), rng, 0.3, 2, -0.07)
    b.col("dirt", "floor", V(-ix, -iy, -0.4), V(ix, iy, 0.0))

    ridge_a = V(-ix + 0.05, iy - 0.3, 2.8)
    ridge_b = V(0.45, iy - 0.25, 0.12)
    emit(timbers, kit.geo_cbox((ridge_b - ridge_a).length, 0.14, 0.2, 0.012), char, kit.place((ridge_a + ridge_b) * 0.5, (ridge_b - ridge_a).normalized(), V(0.0, 0.0, 1.0)), "box")
    b.ramp("nx", "wood", "beam", V(-ix, iy - 0.48, 0.0), V(0.45, iy - 0.12, 2.85))
    lying = [((-2.5, -0.95, 0.1), (-0.6, -0.7, 0.12)), ((0.85, -1.7, 0.1), (2.6, -0.6, 0.55)), ((-0.2, 0.7, 0.09), (1.9, 0.4, 0.12)), ((0.8, 0.15, 0.2), (3.0, 0.05, 0.72)), ((-2.7, 1.0, 0.1), (-1.0, 1.5, 0.14))]
    for a, c in lying:
        a = V(*a)
        c = V(*c)
        emit(timbers, kit.geo_cbox((c - a).length, 0.075, 0.13, 0.008), char, kit.place((a + c) * 0.5, (c - a).normalized(), V(0.0, 0.0, 1.0)) @ kit.Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, 'X'), "box")
    slab = kit.Gable(-1.62, -0.66, 1.0, 0.0, 0.12, 56.0, -1.85)
    kit.roof_rafters(timbers, slab, 1.0, [-1.55, -1.14, -0.73], -0.05, 2.4, -0.023, char, 0.07, 0.12)
    kit.roof_boards(timbers, slab, 1.0, -1.62, -0.66, 0.0, 2.1, rng, char, 0.02, -0.001, [(-1.0, -0.6, 1.5, 2.2)])
    kit.slate_roof(timbers, slab, 1.0, rng, lambda x, d: rng.random() < 0.35, lambda x, d: (d > 1.45 and x > -1.05) or rng.random() < 0.12, lambda x, d: rng.uniform(0.04, 0.12) if rng.random() < 0.2 else 0.0, x0=-1.62, x1=-0.66, d_end=2.05)
    b.ramp("ny", "rock", "roof", V(-1.62, -2.08, 0.0), V(-0.66, -0.78, 1.95))
    leaning = [((-2.6, -1.3, 0.05), (-2.85, -iy + 0.02, 2.5)), ((-1.8, -0.95, 0.05), (-ix + 0.04, -1.6, 2.9))]
    for a, c in leaning:
        a = V(*a)
        c = V(*c)
        emit(timbers, kit.geo_cbox((c - a).length, 0.075, 0.13, 0.008), char, kit.place((a + c) * 0.5, (c - a).normalized(), V(0.0, 0.0, 1.0)), "box")
    for y in (-2.2, -1.45, 1.4, 2.35):
        emit(timbers, kit.geo_cbox(rng.uniform(0.35, 0.7), 0.09, 0.14, 0.008), char, kit.place(V(-ix + 0.2, y, left_profile(-y) - 0.4), V(1.0, 0.0, -0.15), V(0.0, 0.0, 1.0)), "box")
    kit.plank_debris(debris, char, -2.8, 2.6, -1.9, 1.5, 0.02, 16, rng, (0.3, 1.2), (0.08, 0.18), 0.022)
    kit.scatter_chips(debris, "slate_roof", -3.0, 3.0, -2.0, 2.0, 0.0, 70, rng, (0.06, 0.17), (0.006, 0.008), 0.3)
    kit.scatter_chips(debris, "slate_roof", -hx - 1.0, hx + 1.0, -hy - 1.0, -hy - 0.1, -0.1, 22, rng, (0.06, 0.17), (0.006, 0.008), 0.3)
    for index in range(10):
        lump(debris, "soot", V(rng.uniform(-2.8, 2.6), rng.uniform(-1.9, 1.5), 0.0), (rng.uniform(0.15, 0.4), rng.uniform(0.12, 0.3), 0.03), rng, 0.3, 1, -0.01)
    piles = [(V(2.75, -0.3, 0.0), 0.95, 0.7, 46), (V(hx + 0.65, -0.4, -0.12), 1.0, 0.8, 42), (V(1.0, hy - 0.2, -0.05), 0.85, 0.4, 30), (V(2.3, -hy - 0.6, -0.12), 0.8, 0.45, 28)]
    for center, radius, height, count in piles:
        kit.rubble_pile(debris, center, radius, height, rng, count)
    b.col("rock", "rubble", V(2.0, -1.1, 0.0), V(ix, 0.5, 0.35))
    b.col("rock", "rubble", V(2.5, -0.8, 0.35), V(ix, 0.2, 0.62))
    b.col("rock", "rubble", V(hx, -1.15, -0.12), V(hx + 1.4, 0.35, 0.28))
    b.col("rock", "rubble", V(hx, -0.85, 0.28), V(hx + 0.75, 0.05, 0.58))
    b.col("rock", "rubble", V(0.35, hy - 0.75, -0.05), V(1.65, hy + 0.45, 0.2))
    b.col("rock", "rubble", V(1.6, -hy - 1.3, -0.12), V(3.0, -hy, 0.22))

    iron_bed(b, clutter, clutter, V(1.45, 1.25, 0.0), 0.1, rng, 1.9, 0.9, "rusty_metal", False, True)
    bucket(clutter, V(0.95, -1.8, 0.0), rng, "rusty_metal", True)
    kettle(clutter, V(-1.85, 0.6, 0.03), rng)
    for position in (V(-2.2, -0.45, 0.02), V(-1.9, -0.6, 0.02), V(-0.75, 0.55, 0.0), V(-1.7, 0.95, 0.02), V(-0.7, -0.1, 0.0)):
        bottle(clutter, position, rng, rng.random() < 0.6)
    tin(clutter, V(-0.85, 0.35, 0.0), rng)
    tin(clutter, V(-1.0, 0.6, 0.0), rng)
    sack(clutter, V(-3.05, 1.45, 0.0), rng)
    b.loot("toolbox", V(-2.0, -1.75, 0.0))
    b.loot("military", V(2.95, 1.7, 0.0))
    b.loot("box", V(2.85, -1.8, 0.0))

    for index in range(70):
        kit.grass_tuft(plants, V(rng.uniform(-ix + 0.1, ix - 0.1), rng.uniform(-iy + 0.1, iy - 0.1), -0.03), rng, (0.15, 0.5), (6, 14), 0.1)
    for index in range(14):
        kit.nettle(plants, V(rng.uniform(-0.4, ix - 0.2), rng.uniform(-iy + 0.2, iy - 0.2) * rng.choice([1.0, 1.0, 0.4]), -0.03), rng)
    for position in (V(3.1, 0.85, 0.0), V(2.2, -1.85, 0.0), V(0.75, 1.95, 0.0), V(-0.2, 1.4, 0.0), V(0.5, -0.15, 0.0), V(-3.2, -1.75, 0.0)):
        kit.fern(plants, position, rng, (6, 10), (0.4, 0.75))
    bramble(plants, V(3.0, 0.75, 0.1), rng, 6)
    bramble(plants, V(0.9, hy + 0.2, 0.1), rng, 5)
    bramble(plants, V(hx + 0.5, -1.6, -0.05), rng, 5)
    sapling(plants, V(1.7, -0.9, 0.0), rng, 3.2)
    sapling(plants, V(-0.3, hy + 0.9, -0.1), rng, 2.2)
    base_weeds(plants, -hx, hx, -hy, hy, rng, 1.6, lambda p: abs(p.x) < 0.7 and p.y < 0.0, 0.15, 0.3)
    kit.ivy(plants, V(-hx - 0.02, -1.2, -0.1), V(-1.0, 0.0, 0.0), rng, 3.4, 1.0, 8, 30.0)
    kit.ivy(plants, V(-hx - 0.02, 1.6, -0.1), V(-1.0, 0.0, 0.0), rng, 2.6, 0.8, 6, 30.0)
    kit.ivy(plants, V(-2.4, -hy - 0.02, -0.1), V(0.0, -1.0, 0.0), rng, 2.3, 0.7, 5, 28.0)
    kit.ivy(plants, V(-ix + 0.02, 1.45, 0.0), V(1.0, 0.0, 0.0), rng, 2.4, 0.3, 4, 26.0)
    kit.ivy(plants, V(-3.0, hy + 0.02, -0.1), V(0.0, 1.0, 0.0), rng, 2.2, 0.7, 5, 28.0)
    return b


def ruin_far():
    b = kit.Build("ruin_far", 302)
    rng = b.rng
    shell = b.part("shell", 30.0)
    hx, hy, ix = 4.0, 2.75, 3.45
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    kit.wall(shell, "granite_rubble", front, [(-ix, -1.5), (ix, -1.5), (ix, 1.9), (2.62, 1.3), (2.6, 0.95), (1.7, 0.95), (1.68, 1.4), (0.5, 2.0), (0.5, 0.0), (-0.5, 0.0), (-0.5, 2.35), (-1.5, 2.6), (-2.9, 2.7), (-ix, 2.75)], [], 0.55)
    kit.wall(shell, "granite_rubble", left, [(-hy, -1.5), (hy, -1.5), (hy, 2.75), (1.4, 3.7), (0.7, 4.35), (0.55, 5.1), (-0.55, 5.25), (-0.7, 4.35), (-1.6, 3.1), (-hy, 2.5)], [], 0.55)
    kit.wall(shell, "granite_rubble", right, [(-hy, -1.5), (hy, -1.5), (hy, 2.0), (2.2, 1.6), (1.5, 1.0), (0.5, 1.3), (-0.6, 0.9), (-1.8, 1.25), (-hy, 1.9)], [], 0.55)
    kit.wall(shell, "granite_rubble", back, [(-ix, -1.5), (ix, -1.5), (ix, 2.5), (2.07, 2.2), (2.05, 1.0), (1.25, 1.0), (1.23, 2.3), (0.6, 1.6), (-0.53, 1.1), (-0.55, 0.4), (-1.45, 0.4), (-1.47, 0.95), (-2.6, 1.35), (-ix, 1.95)], [], 0.55)
    kit.skin(shell, "soot", front, kit.rect(-2.6, -1.7, 0.9, 1.9), [], 0.004, 0.002, False)
    block(shell, "granite_rubble", V(-ix, -1.1, 0.0), V(-ix + 0.55, 1.1, 3.5), 0.0, "world")
    block(shell, "dirt_debris", V(-ix, -2.2, -0.35), V(ix, 2.2, -0.02), 0.0, "world")
    far_trim(shell, None, hx, hy, 0.55, [2.6, 1.75, 1.85, 2.35])
    member_a = V(-ix + 0.05, 1.9, 2.8)
    member_b = V(0.45, 1.95, 0.12)
    emit(shell, kit.geo_box((member_b - member_a).length, 0.14, 0.2), "timber_charred", kit.place((member_a + member_b) * 0.5, (member_b - member_a).normalized(), V(0.0, 0.0, 1.0)), "box")
    kit.roof_slab(shell, kit.Gable(-1.62, -0.66, 1.0, 0.0, 0.12, 56.0, -1.85), 1.0, -1.62, -0.66, "slate_roof", 0.1, 0.0, 2.05)
    return b


def shed():
    b = kit.Build("shed", 401)
    rng = b.rng
    shell = b.part("shell", 40.0)
    roof = b.part("roof", 55.0)
    joinery = b.part("joinery", 30.0)
    interior = b.part("interior", 40.0)
    clutter = b.part("clutter", 45.0)
    plants = b.part("plants", 70.0)
    hx = 1.5
    hy = 2.0
    high = 2.62
    low = 2.22
    slope = (high - low) / (2.0 * hy)
    beam = "timber_beam"
    planks = "timber_planks_weathered"
    sheet = "corrugated_rusty"

    def eave(y):
        return high - (y + hy) * slope

    block(shell, "concrete", V(-hx - 0.08, -hy - 0.08, -1.5), V(hx + 0.08, hy + 0.08, 0.0), 0.0, "world")
    b.col("concrete", "floor", V(-hx - 0.08, -hy - 0.08, -1.5), V(hx + 0.08, hy + 0.08, 0.0))
    door = (-0.15, 0.8, 0.0, 2.05)
    posts = [(-hx + 0.045, -hy + 0.045), (hx - 0.045, -hy + 0.045), (-hx + 0.045, hy - 0.045), (hx - 0.045, hy - 0.045), (-hx + 0.045, 0.0), (hx - 0.045, 0.0), (door[0] - 0.045, -hy + 0.045), (door[1] + 0.045, -hy + 0.045), (0.0, hy - 0.045)]
    for x, y in posts:
        block(shell, beam, V(x - 0.045, y - 0.045, 0.0), V(x + 0.045, y + 0.045, eave(y) - 0.02), 0.006)
    for y in (-hy + 0.045, hy - 0.045):
        block(shell, beam, V(-hx, y - 0.045, eave(y) - 0.09), V(hx, y + 0.045, eave(y)), 0.006)
    for z in (0.0, 1.15):
        for x in (-hx + 0.045, hx - 0.045):
            block(shell, beam, V(x - 0.035, -hy + 0.09, z + 0.0), V(x + 0.035, hy - 0.09, z + 0.07), 0.004)
        block(shell, beam, V(-hx + 0.09, hy - 0.08, z), V(hx - 0.09, hy - 0.01, z + 0.07), 0.004)
    block(shell, beam, V(-hx + 0.09, -hy + 0.01, 0.0), V(door[0] - 0.09, -hy + 0.08, 0.07), 0.004)
    block(shell, beam, V(door[1] + 0.09, -hy + 0.01, 0.0), V(hx - 0.09, -hy + 0.08, 0.07), 0.004)
    block(shell, beam, V(door[0] - 0.09, -hy + 0.01, door[3]), V(door[1] + 0.09, -hy + 0.08, door[3] + 0.09), 0.004)
    for x in (-hx + 0.045, 0.0, hx - 0.045):
        a = V(x, -hy - 0.12, high + 0.05 + 0.12 * slope)
        c = V(x, hy + 0.2, eave(hy + 0.2) + 0.05)
        emit(roof, kit.geo_cbox((c - a).length, 0.07, 0.1, 0.006), beam, kit.place((a + c) * 0.5, (c - a).normalized(), V(0.0, 0.0, 1.0)), "box")
    for y in (-hy + 0.02, -0.65, 0.65, hy - 0.02):
        block(roof, beam, V(-hx - 0.12, y - 0.03, eave(y) + 0.1), V(hx + 0.12, y + 0.03, eave(y) + 0.15), 0.004)
    x = -hx
    while x < hx - 0.02:
        w = min(rng.uniform(0.13, 0.17), hx - x)
        middle = x + w * 0.5
        z0 = 0.02 if not (door[0] - 0.01 < middle < door[1] + 0.01) else door[3] + 0.02
        if rng.random() < 0.06 and z0 < 0.1:
            z0 += rng.uniform(0.2, 0.6)
        block(shell, planks, V(x + 0.003, -hy - 0.022, z0 + rng.uniform(0.0, 0.03)), V(x + w - 0.003, -hy, high + 0.1 - rng.uniform(0.0, 0.02)), 0.002, "board")
        x += w
    window = (0.52, 1.24, 1.27, 1.85)
    sheet_w = 0.9
    y = hy
    index = 0
    while y > -hy + 0.05:
        width = min(sheet_w, y + hy + 0.03)
        kit.corrugated_sheet(shell, V(-hx - 0.012 - 0.004 * (index % 2), y, 0.03), V(0.0, -1.0, 0.0), V(0.0, 0.0, 1.0), width, eave(y - width * 0.5) + 0.04, rng, sheet, 0.009, 13.0, 6, 0.0015, 0.0, 1, y, rng.uniform(-0.01, 0.015))
        y -= sheet_w - 0.08
        index += 1
    x = hx
    index = 0
    while x > -hx + 0.05:
        width = min(sheet_w, x + hx + 0.03)
        kit.corrugated_sheet(shell, V(x, hy + 0.012 + 0.004 * (index % 2), 0.03), V(-1.0, 0.0, 0.0), V(0.0, 0.0, 1.0), width, low + 0.06, rng, sheet, 0.009, 13.0, 6, 0.0015, 0.0, 1, x, rng.uniform(-0.01, 0.015))
        x -= sheet_w - 0.08
        index += 1
    y = -hy - 0.03
    index = 0
    while y < hy - 0.05:
        width = min(sheet_w, hy + 0.03 - y)
        top = eave(y + width * 0.5) + 0.04
        spans = [(0.03, top)]
        if y < (window[0] + window[1]) * 0.5 < y + width:
            spans = [(0.03, window[2] - 0.02), (window[3] + 0.02, top)]
        for z0, z1 in spans:
            kit.corrugated_sheet(shell, V(hx + 0.012 + 0.004 * (index % 2), y, z0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), width, z1 - z0, rng, sheet, 0.009, 13.0, 6, 0.0015, 0.0, 1, y)
        y += sheet_w - 0.08
        index += 1
    right_frame = kit.facade("right", hx, hy)
    kit.window_frame(joinery, planks, right_frame, window[0], window[1], window[2], window[3], 0.0, 0.05, 0.07)
    glaze = kit.frame_matrix(right_frame)
    choose = kit.glass_chooser(rng, 0.3, 0.4)
    wm = (window[0] + window[1]) * 0.5
    wz = (window[2] + window[3]) * 0.5
    frame_block(joinery, planks, right_frame, wm - 0.012, wm + 0.012, window[2] + 0.07, window[3] - 0.05, 0.015, 0.05)
    frame_block(joinery, planks, right_frame, window[0] + 0.05, window[1] - 0.05, wz - 0.012, wz + 0.012, 0.015, 0.05)
    for p0, p1 in ((window[0] + 0.05, wm - 0.012), (wm + 0.012, window[1] - 0.05)):
        for q0, q1 in ((window[2] + 0.07, wz - 0.012), (wz + 0.012, window[3] - 0.05)):
            kit.pane(joinery, glaze, p0, p1, q0, q1, 0.03, choose(), rng)
    roof_along = V(0.0, 1.0, -slope).normalized()
    for row, (y0, length, lift) in enumerate(((-hy - 0.2, 2.35, 0.17), (0.0, 2.3, 0.155))):
        x = -hx - 0.17
        index = 0
        while x < hx + 0.1:
            width = min(0.92, hx + 0.17 - x)
            if width < 0.2:
                break
            origin = V(x, y0, high + lift - (y0 + hy) * slope + 0.004 * (index % 2))
            kit.corrugated_sheet(roof, origin, V(1.0, 0.0, 0.0), roof_along, width, length, rng, sheet, 0.009, 13.0, 6, 0.0015, rng.uniform(0.0, 0.012), 3, x, rng.uniform(-0.02, 0.02))
            x += 0.92 - 0.09
            index += 1
    tyre(clutter, V(0.0, 0.0, 0.0), rng, kit.place(V(-0.5, 0.6, eave(0.6) + 0.27), roof_along, V(0.0, slope, 1.0)))
    lump(clutter, "granite_rubble", V(0.9, -1.1, eave(-1.1) + 0.25), (0.16, 0.12, 0.08), rng, 0.2, 1, None, None, False)
    lump(clutter, "granite_rubble", V(0.4, 1.5, eave(1.5) + 0.23), (0.14, 0.13, 0.07), rng, 0.2, 1, None, None, False)
    b.col("wood", "front", V(-hx, -hy - 0.03, 0.0), V(door[0] - 0.045, -hy + 0.09, high))
    b.col("wood", "front", V(door[1] + 0.045, -hy - 0.03, 0.0), V(hx, -hy + 0.09, high))
    b.col("wood", "front", V(door[0] - 0.045, -hy - 0.03, door[3] + 0.04), V(door[1] + 0.045, -hy + 0.09, high))
    b.col("metal", "left", V(-hx - 0.03, -hy, 0.0), V(-hx + 0.09, hy, high))
    b.col("metal", "back", V(-hx, hy - 0.09, 0.0), V(hx, hy + 0.03, low + 0.05))
    b.col("metal", "right", V(hx - 0.09, -hy, 0.0), V(hx + 0.03, window[0], high))
    b.col("metal", "right", V(hx - 0.09, window[1], 0.0), V(hx + 0.03, hy, high))
    b.col("metal", "right", V(hx - 0.09, window[0], 0.0), V(hx + 0.03, window[1], window[2]))
    b.col("metal", "right", V(hx - 0.09, window[0], window[3]), V(hx + 0.03, window[1], high))
    b.col("metal", "roof", V(-hx - 0.17, -hy - 0.2, eave(0.0) + 0.02), V(hx + 0.17, 0.0, high + 0.2))
    b.col("metal", "roof", V(-hx - 0.17, 0.0, low + 0.04), V(hx + 0.17, hy + 0.3, eave(0.0) + 0.2))
    front = kit.facade("front", hx, hy)
    kit.door_leaf(joinery, planks, front, door[1] + 0.095, -1.0, -0.03, 0.03, 1.98, 0.93, -90.0, rng, "ledged", 5.0)
    b.col("wood", "door", V(door[1] + 0.045, -hy - 0.98, 0.0), V(door[1] + 0.105, -hy - 0.03, 2.0))

    workbench(b, interior, clutter, V(-hx + 0.44, 0.45, 0.0), math.pi * 0.5, rng, 2.6, 0.66)
    b.loot("toolbox", V(-hx + 0.44, 1.1, 0.9))
    b.loot("box", V(-hx + 0.44, 0.25, 0.9))
    for index, y in enumerate((-0.76, -0.6, -0.44)):
        (tin if index % 2 else jar)(clutter, V(-hx + 0.28, y, 0.9), rng)
    pot(clutter, V(-hx + 0.52, -0.2, 0.9), rng, 0.11)
    crate(clutter, V(-hx + 0.44, -0.2, 0.25), (0.5, 0.42, 0.34), 1.5, rng)
    block(interior, planks, V(-hx + 0.095, -0.7, 1.25), V(-hx + 0.115, 1.7, 1.95), 0.002, "board")
    y = -0.5
    for kind in ("saw", "hammer", "spanner", "coil", "saw", "hammer", "spanner"):
        x = -hx + 0.13
        if kind == "saw":
            block(interior, "rusty_metal", V(x, y - 0.02, 1.35), V(x + 0.004, y + 0.1, 1.85))
            block(interior, beam, V(x - 0.005, y - 0.03, 1.78), V(x + 0.02, y + 0.1, 1.9), 0.008)
        elif kind == "hammer":
            rod(interior, beam, V(x + 0.01, y, 1.45), V(x + 0.01, y, 1.8), 0.012, 6)
            block(interior, "rusty_metal", V(x - 0.005, y - 0.05, 1.78), V(x + 0.03, y + 0.05, 1.83), 0.004)
        elif kind == "spanner":
            block(interior, "rusty_metal", V(x, y - 0.012, 1.45), V(x + 0.006, y + 0.012, 1.8))
            block(interior, "rusty_metal", V(x, y - 0.03, 1.78), V(x + 0.006, y + 0.03, 1.84))
        else:
            ring = [(0.11 + 0.028 * math.cos(tau * t / 8), 0.028 * math.sin(tau * t / 8)) for t in range(9)]
            emit(clutter, kit.geo_lathe(ring, 14), "hay", kit.Matrix.Translation(V(x + 0.03, y, 1.6)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)
        y += 0.3
    for z in (1.2, 1.62):
        shelf(interior, V(0.2, hy - 0.09, z), V(hx - 0.12, hy - 0.09, z), 0.24, V(0.0, -1.0, 0.0), rng)
        x = 0.32
        while x < hx - 0.25:
            rng.choice((tin, jar, bottle))(clutter, V(x, hy - 0.22, z), rng)
            x += rng.uniform(0.16, 0.3)
    crab_pot(clutter, V(hx - 0.5, 1.35, 0.0), 1.5, rng)
    crab_pot(clutter, V(hx - 0.5, 0.75, 0.0), 1.65, rng)
    crab_pot(clutter, V(hx - 0.5, 1.05, 0.3), 1.55, rng)
    crab_pot(clutter, V(hx - 0.48, 0.2, 0.0), 1.4, rng)
    b.col("wood", "pots", V(hx - 0.85, 0.0, 0.0), V(hx - 0.1, 1.7, 0.6))
    hanging_net(clutter, V(hx - 0.3, -1.6, eave(-1.0) - 0.05), V(hx - 0.3, -0.5, eave(-0.4) - 0.05), 1.15, rng)
    crate(clutter, V(0.95, -0.85, 0.0), (0.6, 0.4, 0.3), 0.1, rng)
    net_heap(clutter, V(0.95, -0.85, 0.28), (0.5, 0.34, 0.2), rng)
    b.col("wood", "crate", V(0.62, -1.08, 0.0), V(1.28, -0.62, 0.45))
    jerrycan(clutter, V(1.12, -1.55, 0.0), 0.4, rng)
    for index in range(3):
        oar(clutter, V(-0.5 + index * 0.17, hy - 0.55, 0.02), V(-0.42 + index * 0.13, hy - 0.13, 2.08 + index * 0.03), rng)
    long_tool(clutter, V(0.05, hy - 0.4, 0.0), V(0.08, hy - 0.13, 1.45), "spade", rng)
    anchor(clutter, V(-0.62, hy - 0.5, 0.0), V(-0.66, hy - 0.14, 0.95), rng)
    rope_coil(clutter, V(-0.25, 1.25, 0.0), rng)
    bucket(clutter, V(0.4, 1.55, 0.0), rng)
    chair(clutter, V(-0.85, -1.4, 0.0), 0.5, rng)
    lantern(clutter, V(0.0, 0.0, eave(0.0) - 0.42), rng)
    rod(clutter, "rusty_metal", V(0.0, 0.0, eave(0.0) - 0.07), V(0.0, 0.0, eave(0.0) + 0.06), 0.004, 4)
    b.light("warm", V(0.0, 0.0, eave(0.0) - 0.3))

    for x, z in ((-1.15, 1.72), (-0.93, 1.5), (-0.7, 1.8)):
        rod(clutter, "rusty_metal", V(x, -hy - 0.02, z + 0.24), V(x, -hy - 0.06, z + 0.25), 0.004, 4)
        rod(clutter, "hay", V(x, -hy - 0.05, z + 0.24), V(x, -hy - 0.1, z + 0.06), 0.006, 4)
        glass_float(clutter, V(x, -hy - 0.105, z), rng, 0.08)
    oar(clutter, V(-1.3, -hy - 0.45, -0.1), V(-1.38, -hy - 0.06, 2.2), rng)
    dinghy(b, clutter, V(hx + 0.95, 0.2, -0.14), math.pi * 0.5, rng)
    crab_pot(clutter, V(-hx - 0.55, -1.2, -0.1), 0.2, rng)
    crab_pot(clutter, V(-hx - 0.6, -0.5, -0.1), -0.3, rng)
    b.col("wood", "pots", V(-hx - 0.95, -1.5, -0.1), V(-hx - 0.2, -0.2, 0.2))
    barrel(b, clutter, V(-hx - 0.45, hy - 0.2, -0.1), rng, 0.27, 0.85)
    rail_a = V(-hx - 0.1, hy + 0.9, -0.1)
    rail_b = V(hx - 0.2, hy + 0.9, -0.1)
    for p in (rail_a, rail_b):
        rod(clutter, beam, p, p + V(0.0, 0.0, 1.35), 0.04, 6)
    rod(clutter, beam, rail_a + V(0.0, 0.0, 1.3), rail_b + V(0.0, 0.0, 1.3), 0.03, 6)
    hanging_net(clutter, rail_a + V(0.2, 0.0, 1.28), rail_b + V(-0.2, 0.0, 1.28), 1.1, rng)
    b.col("wood", "rail", rail_a + V(-0.05, -0.05, 0.0), rail_b + V(0.05, 0.05, 1.35))
    tyre(clutter, V(hx + 0.6, -hy + 0.2, -0.12), rng)
    base_weeds(plants, -hx - 0.08, hx + 0.08, -hy - 0.08, hy + 0.08, rng, 1.3, lambda p: (door[0] - 0.4 < p.x < door[1] + 0.5 and p.y < -hy) or (p.x > hx and -1.3 < p.y < 1.7) or (p.x < -hx and (-1.6 < p.y < -0.1 or p.y > hy - 0.6)))
    kit.ivy(plants, V(-0.6, hy + 0.04, -0.1), V(0.0, 1.0, 0.0), rng, 1.7, 0.5, 4, 22.0)
    for index in range(10):
        kit.grass_tuft(plants, V(hx + rng.uniform(0.3, 1.7), rng.uniform(-1.4, 1.7), -0.12), rng, (0.2, 0.5), (6, 12), 0.08)
    kit.scatter_chips(plants, "foliage", -0.2, 1.0, -hy + 0.1, -0.8, 0.0, 24, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    return b


def shed_far():
    b = kit.Build("shed_far", 402)
    rng = b.rng
    shell = b.part("shell", 40.0)
    hx, hy, high, low = 1.5, 2.0, 2.62, 2.22
    block(shell, "concrete", V(-hx - 0.08, -hy - 0.08, -1.5), V(hx + 0.08, hy + 0.08, 0.0), 0.0, "world")
    front = kit.facade("front", hx, hy)
    upright_slab(shell, "timber_planks_weathered", front, kit.rect(-hx, hx, 0.0, high + 0.1), 0.03)
    kit.skin(shell, "soot", front, kit.rect(-0.15, 0.8, 0.0, 2.05), [], 0.004, 0.002, False)
    kit.wall(shell, "corrugated_rusty", kit.facade("back", hx, hy), kit.rect(-hx, hx, 0.0, low + 0.06), [], 0.03)
    for side in ("left", "right"):
        kit.wall(shell, "corrugated_rusty", kit.facade(side, hx, hy), [(-hy, 0.0), (hy, 0.0), (hy, low + 0.06 if side == "right" else high + 0.06), (-hy, high + 0.06 if side == "right" else low + 0.06)], [], 0.03)
    slope = (high - low) / (2.0 * hy)
    along = V(0.0, 1.0, -slope).normalized()
    kit.corrugated_sheet(shell, V(-hx - 0.17, -hy - 0.2, high + 0.17 + 0.2 * slope), V(1.0, 0.0, 0.0), along, 2.0 * hx + 0.34, 4.55, rng, "corrugated_rusty", 0.0, 1.0, 1, 0.03)
    kit.skin(shell, "soot", kit.facade("right", hx, hy), kit.rect(0.52, 1.24, 1.27, 1.85), [], 0.004, 0.002, False)
    upright_slab(shell, "timber_planks_weathered", kit.plane(V(0.895, -hy - 0.5, 0.0), V(1.0, 0.0, 0.0)), kit.rect(-0.47, 0.47, 0.03, 2.0), 0.045)
    dinghy(b, shell, V(hx + 0.95, 0.2, -0.14), math.pi * 0.5, rng, stations=4, girth=4, collide=False)
    return b


def barn():
    b = kit.Build("barn", 501)
    rng = b.rng
    shell = b.part("shell", 30.0)
    roof = b.part("roof", 55.0)
    frame_part = b.part("frame", 35.0)
    joinery = b.part("joinery", 30.0)
    floors = b.part("floors", 30.0)
    interior = b.part("interior", 40.0)
    clutter = b.part("clutter", 45.0)
    hay = b.part("hay", 45.0)
    plants = b.part("plants", 70.0)
    hx = 7.0
    hy = 4.0
    wall_t = 0.55
    ix = hx - wall_t
    iy = hy - wall_t
    stone = "granite_rubble"
    dressed = "granite_ashlar"
    beam = "timber_beam"
    planks = "timber_planks_weathered"
    gable = kit.Gable(-hx - 0.2, hx + 0.2, hy, 0.3, 3.42, 38.0)
    wall_top = gable.under(hy, 0.03)
    loft = 2.6
    bay = 1.7
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    left = kit.facade("left", hx, hy)
    right = kit.facade("right", hx, hy)
    big_door = (-bay, bay, 0.0, 3.1)
    rear_door = (0.1, 1.2, 0.0, 2.1)
    slits = [(-4.27, -4.13, 1.6, 2.5), (4.13, 4.27, 1.6, 2.5)]
    gable_window = (-0.4, 0.4, 1.4, 2.2)

    kit.wall(shell, stone, front, kit.rect(-ix, ix, -1.5, wall_top), [kit.rect(big_door[0], big_door[1], -0.05, big_door[3])] + [kit.rect(*s) for s in slits], wall_t)
    kit.wall(shell, stone, back, kit.rect(-ix, ix, -1.5, wall_top), [kit.rect(rear_door[0], rear_door[1], -0.05, rear_door[3])] + [kit.rect(*s) for s in slits], wall_t)
    kit.wall(shell, stone, left, kit.rect(-hy, hy, -1.5, wall_top), [kit.rect(*gable_window)], wall_t)
    kit.wall(shell, stone, right, kit.rect(-hy, hy, -1.5, wall_top), [], wall_t)
    kit.wall_boxes(b, "rock", "front", front, -ix, ix, -1.5, wall_top, wall_t, [big_door])
    kit.wall_boxes(b, "rock", "back", back, -ix, ix, -1.5, wall_top, wall_t, [rear_door])
    kit.wall_boxes(b, "rock", "left", left, -hy, hy, -1.5, wall_top, wall_t, [gable_window])
    kit.wall_boxes(b, "rock", "right", right, -hy, hy, -1.5, wall_top, wall_t, [])
    for corner, ua, ub in ((V(-hx, -hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, -hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, 1.0, 0.0)), (V(hx, hy, 0.0), V(-1.0, 0.0, 0.0), V(0.0, -1.0, 0.0)), (V(-hx, hy, 0.0), V(1.0, 0.0, 0.0), V(0.0, -1.0, 0.0))):
        kit.quoins(shell, dressed, corner, ua, ub, -0.3, wall_top, rng, 0.03, 0.012, 0.022, (0.5, 0.7), (0.24, 0.34))
    kit.jamb_stones(shell, dressed, front, big_door[0], -1.0, 0.0, big_door[3], rng, 0.36)
    kit.jamb_stones(shell, dressed, front, big_door[1], 1.0, 0.0, big_door[3], rng, 0.36)
    frame_block(frame_part, beam, front, big_door[0] - 0.45, big_door[1] + 0.45, big_door[3], big_door[3] + 0.3, -0.02, wall_t + 0.02, 0.015)
    kit.lintel_stone(shell, dressed, back, rear_door[0], rear_door[1], rear_door[3], 0.28, 0.32, 0.02, 0.15)
    kit.jamb_stones(shell, dressed, back, rear_door[0], -1.0, 0.0, rear_door[3], rng)
    kit.jamb_stones(shell, dressed, back, rear_door[1], 1.0, 0.0, rear_door[3], rng)
    window_surround(shell, joinery, left, gable_window, wall_t)
    for frame in (front, back):
        for s in slits:
            kit.lintel_stone(shell, dressed, frame, s[0], s[1], s[3], 0.18, 0.3, 0.015, 0.14)
            kit.sill_stone(shell, dressed, frame, s[0], s[1], s[2], 0.18, 0.03, 0.08, 0.1)
    for frame, a_low, a_high in ((front, -ix, ix), (back, -ix, ix), (left, -hy, hy), (right, -hy, hy)):
        damp_band(shell, frame, a_low, a_high, rng, 0.3, 0.9 if frame is not back else 1.3, gaps=[(big_door[0] - 0.02, big_door[1] + 0.02)] if frame is front else [(rear_door[0] - 0.02, rear_door[1] + 0.02)] if frame is back else ())
        a = a_low + 0.02
        while a < a_high - 0.15:
            w = rng.uniform(0.6, 1.1)
            if a_high - (a + w) < 0.3:
                w = a_high - a
            blocked = (frame is front and a + w > big_door[0] - 0.4 and a < big_door[1] + 0.4) or (frame is back and a + w > rear_door[0] - 0.3 and a < rear_door[1] + 0.3)
            if not blocked:
                frame_block(shell, dressed, frame, a + 0.008, a + w - 0.008, -0.5, 0.2 + rng.uniform(-0.04, 0.04), -0.04 * rng.uniform(0.7, 1.2), 0.25, 0.022)
            a += w

    plate = wall_top
    for side in (-1.0, 1.0):
        block(frame_part, beam, V(-hx, side * (iy + 0.05), plate), V(hx, side * (iy + 0.25), plate + 0.12), 0.008)
    truss_xs = [-hx + 0.15, -4.67, -2.33, 0.0, 2.33, 4.67, hx - 0.15]
    collar_z = 5.35
    for x in truss_xs:
        for side in (-1.0, 1.0):
            a = gable.point(side, x, gable.distance(iy + 0.45), -0.39)
            c = gable.point(side, x, gable.run - 0.05, -0.39)
            emit(frame_part, kit.geo_cbox((c - a).length, 0.13, 0.2, 0.01), beam, kit.place((a + c) * 0.5, (c - a).normalized(), gable.normal(side)), "box")
        reach = (gable.under(0.0, 0.5) - collar_z) / gable.tan + 0.1
        block(frame_part, beam, V(x - 0.05, -reach, collar_z - 0.09), V(x + 0.05, reach, collar_z + 0.09), 0.008)
        block(frame_part, beam, V(x - 0.05, -0.06, collar_z), V(x + 0.05, 0.06, gable.ridge_top - 0.4), 0.008)
    for side in (-1.0, 1.0):
        for d in (1.7, 3.5):
            kit.segmented(frame_part, beam, gable.point(side, -hx, d, -0.215), gable.point(side, hx, d, -0.215), 0.13, 0.15, gable.normal(side), 2.33, "box", 0.008)
        xs = [-hx - 0.05 + i * 0.52 for i in range(28)]
        kit.roof_rafters(frame_part, gable, side, xs, 0.0, gable.run - 0.02, -0.023, beam, 0.05, 0.1)
    kit.segmented(frame_part, beam, V(-hx, 0.0, gable.ridge_top - 0.2), V(hx, 0.0, gable.ridge_top - 0.2), 0.05, 0.3, V(0.0, 0.0, 1.0), 2.33, "box")
    patch = (2.4, 5.2, 1.2, gable.run)
    bare = [(-5.6, -4.4, 2.3, 3.6), (-1.2, -0.2, 0.0, 0.7)]

    def lost_front(x, d):
        return (-3.4 < x < -2.2 and 3.2 < d < 4.3 and rng.random() < 0.85) or rng.random() < 0.012

    def lost_back(x, d):
        if patch[0] < x < patch[1] and d > patch[2]:
            return True
        for x0, x1, d0, d1 in bare:
            if x0 < x < x1 and d0 < d < d1 and rng.random() < 0.85:
                return True
        return rng.random() < 0.015

    kit.pantile_roof(roof, gable, -1.0, rng, None, None, lost_front)
    kit.pantile_roof(roof, gable, 1.0, rng, None, None, lost_back)
    kit.roof_boards(roof, gable, -1.0, -hx - 0.2, hx + 0.2, 0.0, gable.run + 0.02, rng, planks, 0.022, -0.001, [(-3.2, -2.5, 3.4, 4.1)])
    kit.roof_boards(roof, gable, 1.0, -hx - 0.2, hx + 0.2, 0.0, gable.run + 0.02, rng, planks, 0.022, -0.001, [(-5.3, -4.7, 2.6, 3.3)])
    up = gable.upslope(1.0)
    x = patch[0] - 0.05
    index = 0
    while x < patch[1]:
        width = min(0.95, patch[1] + 0.05 - x)
        origin = gable.point(1.0, x + width, patch[2] - 0.03, 0.045 + 0.005 * (index % 2))
        kit.corrugated_sheet(roof, origin, V(-1.0, 0.0, 0.0), up, width, gable.run - patch[2] + 0.05, rng, "corrugated_rusty", 0.009, 13.0, 6, 0.0015, 0.015, 3, -x)
        x += 0.95 - 0.09
        index += 1
    kit.ridge_tiles(roof, gable, -hx - 0.2, hx + 0.2, rng)
    for end in (-1.0, 1.0):
        x = end * (hx + 0.2)
        for side in (-1.0, 1.0):
            kit.segmented(roof, planks, gable.point(side, x, -0.05, -0.1), gable.point(side, x, gable.run, -0.1), 0.03, 0.2, gable.normal(side), 1.4)
    roof_cols(b, gable, -hx - 0.2, hx + 0.2, 7, "rock", "roof", (-1.0, 1.0), 0.28)
    sag_roof = (-hx - 0.2, hx + 0.2, gable.eave_top + 0.15, gable.ridge_top, 0.09)

    for frame, x_out, sign in ((left, -hx, -1.0), (right, hx, 1.0)):
        y = -hy
        while y < hy - 0.02:
            w = min(rng.uniform(0.16, 0.22), hy - y)
            middle = y + w * 0.5
            top = gable.under(middle, 0.03)
            z0 = wall_top - 0.12 + rng.uniform(0.0, 0.03)
            hatch = sign > 0 and -0.5 < middle < 0.5
            pieces = [(z0, top)] if not hatch else [(z0, 3.62), (4.92, top)]
            if rng.random() < 0.07:
                pieces = [(z0, z0 + (top - z0) * rng.uniform(0.3, 0.7))]
            for p0, p1 in pieces:
                if p1 - p0 > 0.08:
                    block(shell, planks, V(x_out, y + 0.004, p0), V(x_out + sign * 0.03, y + w - 0.004, p1), 0.002, "board")
            y += w
        inner = x_out - sign * 0.09
        for z in (wall_top + 0.06, 4.6, 5.7):
            reach = min(hy - 0.1, (gable.under(0.0, 0.1) - z) / gable.tan)
            if reach > 0.3:
                block(frame_part, beam, V(min(inner, inner + sign * 0.06), -reach, z - 0.05), V(max(inner, inner + sign * 0.06), reach, z + 0.05), 0.004)
        steps = 4
        for index in range(steps):
            z0 = wall_top + (gable.ridge_top - wall_top) * index / steps
            z1 = wall_top + (gable.ridge_top - wall_top) * (index + 1) / steps
            reach = (gable.ridge_top - z0) / gable.tan
            if sign > 0 and z0 < 4.9 and z1 > 3.6:
                b.col("wood", "gable", V(min(x_out, x_out - sign * 0.12), -reach, z0), V(max(x_out, x_out - sign * 0.12), -0.5, z1))
                b.col("wood", "gable", V(min(x_out, x_out - sign * 0.12), 0.5, z0), V(max(x_out, x_out - sign * 0.12), reach, z1))
            else:
                b.col("wood", "gable", V(min(x_out, x_out - sign * 0.12), -reach, z0), V(max(x_out, x_out - sign * 0.12), reach, z1))
    hoist_a = V(hx - 0.3, 0.0, 5.15)
    hoist_b = V(hx + 1.1, 0.0, 5.15)
    emit(frame_part, kit.geo_cbox((hoist_b - hoist_a).length, 0.12, 0.14, 0.01), beam, kit.place((hoist_a + hoist_b) * 0.5, V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0)), "box")
    emit(clutter, kit.geo_lathe([(0.0, -0.03), (0.09, -0.03), (0.11, -0.015), (0.09, 0.0), (0.11, 0.015), (0.09, 0.03), (0.0, 0.03)], 12), "rusty_metal", kit.Matrix.Translation(hoist_b + V(-0.15, 0.0, -0.2)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)
    rope_path = [hoist_b + V(-0.15, 0.0, -0.3), hoist_b + V(-0.13, 0.02, -1.6), hoist_b + V(-0.18, -0.03, -2.9)]
    emit(clutter, kit.geo_tube(rope_path, kit.circle(0.012, 5), True), "hay", None, "given", True)
    kit.door_leaf(joinery, planks, right, 0.5, -1.0, -0.085, 3.64, 1.26, 0.98, -150.0, rng, "ledged", 8.0)

    kit.flagstones(floors, dressed, -bay, bay, -iy, iy, 0.0, rng, (0.5, 0.9), 0.014, 0.08, 0.014, 0.008, "dirt_debris")
    block(floors, "cobbles", V(-ix, -iy, -0.2), V(-bay, iy, 0.0), 0.0, "world")
    block(floors, "dirt_debris", V(bay, -iy, -0.2), V(ix, iy, -0.01), 0.0, "world")
    block(floors, "concrete", V(-ix, -iy, -1.5), V(ix, iy, -0.2), 0.0, "world")
    frame_block(floors, dressed, front, big_door[0], big_door[1], -0.25, 0.0, -0.3, wall_t, 0.02)
    frame_block(floors, dressed, back, rear_door[0] - 0.05, rear_door[1] + 0.05, -0.2, 0.0, -0.25, wall_t, 0.015)
    b.col("rock", "floor", V(-ix, -iy, -0.4), V(bay, iy, 0.0))
    b.col("dirt", "floor", V(bay, -iy, -0.4), V(ix, iy, 0.0))
    b.col("rock", "threshold", kit.frame_point(front, big_door[0], -1.5, -wall_t), kit.frame_point(front, big_door[1], 0.0, 0.3))
    b.col("rock", "threshold", kit.frame_point(back, rear_door[0] - 0.05, -1.5, -wall_t), kit.frame_point(back, rear_door[1] + 0.05, 0.0, 0.25))

    landing = (0.85, bay, 2.1, iy)
    bearer = loft - 0.17
    for x in (bay + 0.1, 4.1):
        kit.segmented(frame_part, beam, V(x, -iy, bearer - 0.11), V(x, iy, bearer - 0.11), 0.18, 0.22, V(0.0, 0.0, 1.0), 2.3, "box", 0.01)
        for y in (-1.75, 1.75):
            block(frame_part, beam, V(x - 0.09, y - 0.09, 0.0), V(x + 0.09, y + 0.09, bearer - 0.22), 0.01)
            b.col("wood", "post", V(x - 0.09, y - 0.09, 0.0), V(x + 0.09, y + 0.09, loft - 0.3))
            for sign in (-1.0, 1.0):
                kit.member(frame_part, beam, V(x, y + sign * 0.08, bearer - 0.8), V(x, y + sign * 0.62, bearer - 0.24), 0.07, 0.08, None, 0.005, "box")
    block(frame_part, beam, V(landing[0], landing[2], 0.0), V(landing[0] + 0.14, landing[2] + 0.14, loft - 0.03), 0.01)
    b.col("wood", "post", V(landing[0], landing[2], 0.0), V(landing[0] + 0.14, landing[2] + 0.14, loft))
    block(frame_part, beam, V(landing[0] + 0.14, landing[2], loft - 0.2), V(landing[1], landing[2] + 0.1, loft - 0.03), 0.006)
    block(frame_part, beam, V(landing[0], landing[2] + 0.14, loft - 0.2), V(landing[0] + 0.1, landing[3], loft - 0.03), 0.006)
    kit.joists(frame_part, beam, bay, ix, -iy, iy, loft - 0.03, "x", 0.55, 0.07, 0.14)
    kit.floor_boards(floors, planks, bay, ix, -iy, iy, loft, "y", rng, 0.03, 0.006, None, (0.16, 0.24), 0.05, [-2.0, -0.4, 1.2, 2.4], [(3.0, 3.2, -1.4, -0.7), (5.0, 5.2, 0.9, 1.7)], 0.2)
    kit.floor_boards(floors, planks, landing[0], landing[1], landing[2], landing[3], loft, "y", rng, 0.03, 0.006, None, (0.16, 0.24))
    kit.joists(frame_part, beam, landing[0] + 0.1, landing[1], landing[2] + 0.1, landing[3], loft - 0.03, "x", 0.5, 0.07, 0.14)
    b.col("wood", "loft", V(bay, -iy, loft - 0.3), V(ix, iy, loft))
    b.col("wood", "loft", V(landing[0], landing[2], loft - 0.2), V(landing[1], landing[3], loft))
    ladder_stair(b, floors, V(1.27, -0.7, 0.0), V(0.0, 1.0, 0.0), 0.7, loft, 2.8, 12, rng, beam, planks, "wood", "stair", "py", (7,))
    for a, c in ((V(bay + 0.05, -iy + 0.2, loft), V(bay + 0.05, -0.9, loft)), (V(landing[0] + 0.05, landing[2] + 0.2, loft), V(landing[0] + 0.05, iy - 0.1, loft))):
        balustrade(b, frame_part, a, c, rng, 0.9, 0.6, beam, beam, 0.2, (True, True), True, "loft_rail")
        rod(frame_part, beam, a + V(0.0, 0.0, 0.45), c + V(0.0, 0.0, 0.45), 0.022, 6)

    for x in (-5.05, -3.45, -1.85):
        stall(b, interior, x, iy - 0.05, 1.3, 1.4, rng)
    manger_y = iy - 0.5
    block(interior, planks, V(-ix + 0.05, manger_y, 0.55), V(-bay - 0.2, manger_y + 0.03, 0.95), 0.003, "board")
    block(interior, planks, V(-ix + 0.05, manger_y, 0.52), V(-bay - 0.2, iy - 0.02, 0.55), 0.003, "board")
    for x in (-ix + 0.1, -5.05, -3.45, -bay - 0.25):
        block(interior, beam, V(x - 0.04, manger_y - 0.04, 0.0), V(x + 0.04, manger_y + 0.04, 0.95), 0.005)
    b.col("wood", "manger", V(-ix, manger_y - 0.04, 0.0), V(-bay - 0.2, iy, 0.95))
    rack_z0 = 1.35
    rod(interior, beam, V(-ix + 0.1, iy - 0.06, rack_z0), V(-bay - 0.3, iy - 0.06, rack_z0), 0.03, 6)
    rod(interior, beam, V(-ix + 0.1, iy - 0.55, rack_z0 + 0.65), V(-bay - 0.3, iy - 0.55, rack_z0 + 0.65), 0.03, 6)
    x = -ix + 0.2
    while x < -bay - 0.35:
        if rng.random() > 0.1:
            rod(interior, beam, V(x, iy - 0.06, rack_z0), V(x, iy - 0.55, rack_z0 + 0.65), 0.014, 5)
        x += 0.14
    for x in (-5.8, -4.2, -2.6):
        lump(hay, "hay", V(x, iy - 0.25, 0.63), (0.6, 0.19, 0.17), rng, 0.3, 2, 0.555, 0.0)
        lump(hay, "hay", V(x + 0.2, iy - 0.23, rack_z0 + 0.38), (0.62, 0.16, 0.3), rng, 0.3, 2, None, 0.0)
    block(floors, dressed, V(-ix + 0.05, 0.9, -0.06), V(-bay - 0.1, 1.12, 0.025), 0.012)

    stacks = [(5.4, 2.7, 2, 2, 3), (5.5, -2.5, 2, 2, 3), (2.9, -2.7, 2, 1, 2)]
    for sx, sy, nx, ny, nz in stacks:
        for k in range(nz):
            for i in range(nx):
                for j in range(ny):
                    if k == nz - 1 and rng.random() < 0.35:
                        continue
                    hay_bale(hay, V(sx + (i - (nx - 1) * 0.5) * 0.92 + rng.uniform(-0.03, 0.03), sy + (j - (ny - 1) * 0.5) * 0.47 + rng.uniform(-0.02, 0.02), loft + k * 0.37), rng.uniform(-0.05, 0.05), rng)
        b.col("grass", "bales", V(sx - nx * 0.46, sy - ny * 0.24, loft), V(sx + nx * 0.46, sy + ny * 0.24, loft + nz * 0.37))
    for position, yaw in ((V(2.7, -0.3, 0.0), 0.2), (V(2.75, -0.35, 0.37), 0.35), (V(0.5, 3.0, 0.0), 0.1), (V(1.3, 2.75, 0.0), 1.45), (V(3.7, 2.95, 0.0), 0.05)):
        hay_bale(hay, position, yaw, rng)
    b.col("grass", "bales", V(2.2, -0.62, 0.0), V(3.25, -0.02, 0.72))
    b.col("grass", "bales", V(0.05, 2.76, 0.0), V(0.95, 3.24, 0.36))
    b.col("grass", "bales", V(1.06, 2.3, 0.0), V(1.54, 3.2, 0.36))
    b.col("grass", "bales", V(3.24, 2.71, 0.0), V(4.16, 3.19, 0.36))
    for center, radius, height in ((V(4.2, 0.3, loft), 0.9, 0.6), (V(2.6, 1.2, loft), 0.6, 0.35), (V(0.0, 1.6, 0.0), 0.8, 0.4), (V(3.3, 1.7, 0.0), 0.9, 0.55), (V(-0.9, -2.7, 0.0), 0.55, 0.3)):
        hay_heap(hay, center, radius, height, rng)
    kit.scatter_chips(hay, "hay", -bay, ix - 0.3, -iy + 0.3, iy - 0.3, 0.005, 60, rng, (0.08, 0.25), (0.004, 0.01), 0.2)
    kit.scatter_chips(hay, "hay", bay + 0.2, ix - 0.3, -iy + 0.3, iy - 0.3, loft + 0.004, 50, rng, (0.08, 0.25), (0.004, 0.01), 0.2)

    cart(b, interior, V(5.5, -0.6, 0.0), math.pi * 0.5, rng)
    plough(clutter, V(-4.9, -2.4, 0.0), 0.5, rng)
    wheelbarrow(clutter, V(-3.3, -2.85, 0.0), 2.6, rng)
    for position, tipped in ((V(-2.15, -3.1, 0.0), False), (V(-2.5, -3.15, 0.0), False), (V(-2.0, -2.55, 0.0), True)):
        churn(clutter, position, rng, "corrugated_rusty", tipped)
    tools = (("fork", V(6.0, 3.15, 0.0), V(6.1, 3.42, 1.65)), ("fork", V(6.25, 3.1, 0.0), V(6.4, 3.35, 1.6)), ("rake", V(5.6, 3.15, 0.0), V(5.55, 3.42, 1.7)), ("scythe", V(-6.2, -3.0, 0.0), V(-6.38, -3.35, 1.7)), ("spade", V(-6.3, -2.2, 0.0), V(-6.42, -2.4, 1.3)), ("hoe", V(-6.3, -1.7, 0.0), V(-6.42, -1.9, 1.5)), ("broom", V(1.95, -3.2, 0.0), V(1.9, -3.42, 1.45)))
    for kind, foot, top in tools:
        long_tool(clutter, foot, top, kind, rng)
    sack(clutter, V(2.3, 3.0, 0.0), rng, "fabric_worn", 1.1)
    sack(clutter, V(2.9, 3.05, 0.0), rng)
    sack(clutter, V(2.6, 2.95, 0.4), rng, "fabric_worn", 0.9)
    barrel(b, clutter, V(4.7, 3.05, 0.0), rng, 0.3, 0.9, planks, "rusty_metal", False)
    bucket(clutter, V(-2.3, 2.2, 0.0), rng)
    bucket(clutter, V(-4.2, 0.5, 0.0), rng, "rusty_metal", True)
    crate(clutter, V(2.5, -3.05, 0.0), (0.7, 0.5, 0.45), 0.1, rng)
    crate(clutter, V(2.55, -3.05, 0.45), (0.55, 0.4, 0.35), -0.2, rng, broken=True)
    b.col("wood", "crate", V(2.12, -3.32, 0.0), V(2.88, -2.78, 0.8))
    workbench(b, interior, clutter, V(5.2, -iy + 0.32, 0.0), 0.0, rng, 2.0, 0.56)
    for x in (4.45, 4.62, 5.75, 5.95):
        rng.choice((tin, jar, bottle))(clutter, V(x, -iy + 0.2, 0.9), rng)
    b.loot("toolbox", V(5.15, -iy + 0.3, 0.9))
    b.loot("box", V(-4.25, 2.0, 0.0))
    b.loot("box", V(5.95, -1.2, loft))
    b.loot("food", V(-5.75, 2.2, 0.0))
    b.loot("military", V(5.85, 1.25, loft))
    collar = V(0.0, 0.0, collar_z - 0.09)
    rod(clutter, "rusty_metal", collar, collar - V(0.0, 0.0, 1.83), 0.004, 4)
    lantern(clutter, collar - V(0.0, 0.0, 2.19), rng)
    b.light("warm", collar - V(0.0, 0.0, 2.05))
    rod(clutter, "rusty_metal", V(-3.45, 1.3, 1.6), V(-3.45, 1.02, 1.62), 0.006, 5)
    lantern(clutter, V(-3.45, 1.05, 1.25), rng)
    b.light("warm", V(-3.45, 1.0, 1.4))
    for index, y in enumerate((-2.9, -2.3, -1.7)):
        emit(clutter, kit.geo_lathe([(0.2 + 0.05 * math.cos(tau * t / 8), 0.05 * math.sin(tau * t / 8)) for t in range(9)], 12), "fabric_worn", kit.Matrix.Translation(V(-ix + 0.06, y, 2.3 - index * 0.04)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)
        rod(clutter, "rusty_metal", V(-ix, y, 2.5 - index * 0.04), V(-ix + 0.09, y, 2.5 - index * 0.04), 0.008, 5)
    chain = [V(-ix + 0.04, -1.2 + 0.08 * t, 1.9 - 0.2 * math.sin(math.pi * t / 10)) for t in range(11)]
    emit(clutter, kit.geo_tube(chain, kit.circle(0.012, 5), True, V(1.0, 0.0, 0.0)), "rusty_metal", None, "given", True)

    kit.door_leaf(joinery, planks, front, big_door[0], 1.0, -0.04, 0.04, 3.02, bay - 0.02, -90.0, rng, "ledged", 0.0)
    kit.door_leaf(joinery, planks, front, big_door[1], -1.0, -0.04, 0.04, 3.02, bay - 0.02, -172.0, rng, "ledged", 4.0)
    b.col("wood", "door", V(-bay - 0.02, -hy - bay - 0.04, 0.0), V(-bay + 0.06, -hy - 0.04, 3.0))
    b.col("wood", "door", V(bay, -hy - 0.3, 0.0), V(bay + 1.7, -hy, 3.0))
    kit.door_frame(joinery, planks, back, rear_door[0] + 0.02, rear_door[1] - 0.02, 0.0, rear_door[3], 0.15)
    kit.door_leaf(joinery, planks, back, rear_door[1] - 0.09, -1.0, 0.27, 0.03, 2.0, 0.92, 100.0, rng, "ledged", 4.0)
    b.col("wood", "door", V(-1.31, 2.8, 0.0), V(-1.09, iy, 2.0))
    kit.casement_window(joinery, planks, left, gable_window[0], gable_window[1], gable_window[2], gable_window[3], 0.12, rng, [0.0, 0.0], 0.25, 0.4, 2)

    lean_x0 = -hx - 2.6
    for y in (-2.0, 1.6):
        block(frame_part, beam, V(lean_x0, y - 0.06, -0.12), V(lean_x0 + 0.12, y + 0.06, 2.0), 0.008)
        b.col("wood", "post", V(lean_x0, y - 0.06, -0.12), V(lean_x0 + 0.12, y + 0.06, 2.0))
    block(frame_part, beam, V(lean_x0, -2.35, 2.0), V(lean_x0 + 0.12, 1.95, 2.12), 0.008)
    block(frame_part, beam, V(-hx - 0.12, -2.35, 2.62), V(-hx, 1.95, 2.74), 0.008)
    lean_along = V(-2.75, 0.0, -0.62).normalized()
    for index in range(5):
        kit.corrugated_sheet(roof, V(-hx + 0.02, -2.4 + index * 0.86, 2.8 + 0.005 * (index % 2)), V(0.0, 1.0, 0.0), lean_along, 0.95, 2.95, rng, "corrugated_rusty", 0.009, 13.0, 6, 0.0015, 0.02, 3, index * 0.86)
    for y in (-2.0, -0.2, 1.6):
        a = V(-hx - 0.06, y, 2.72)
        c = V(lean_x0 + 0.06, y, 2.17)
        emit(frame_part, kit.geo_cbox((c - a).length + 0.2, 0.06, 0.09, 0.005), beam, kit.place((a + c) * 0.5, (c - a).normalized(), V(0.0, 0.0, 1.0)), "box")
    b.col("metal", "lean_roof", V(lean_x0 - 0.1, -2.4, 2.05), V(-hx - 1.3, 2.0, 2.45))
    b.col("metal", "lean_roof", V(-hx - 1.3, -2.4, 2.35), V(-hx, 2.0, 2.85))
    harrow = kit.turned(V(-hx - 1.35, 0.3, -0.1), 0.2)
    for i in range(4):
        local_block(clutter, beam, harrow, -0.7, 0.7, -0.6 + i * 0.4 - 0.03, -0.6 + i * 0.4 + 0.03, 0.12, 0.18, 0.004)
        for j in range(6):
            rod(clutter, "rusty_metal", harrow @ V(-0.6 + j * 0.24, -0.6 + i * 0.4, 0.0), harrow @ V(-0.6 + j * 0.24, -0.6 + i * 0.4, 0.2), 0.008, 4)
    for x in (-0.55, 0.0, 0.55):
        local_block(clutter, beam, harrow, x - 0.03, x + 0.03, -0.62, 0.62, 0.18, 0.23, 0.004)
    tyre(clutter, V(-hx - 1.9, -1.5, -0.12), rng)
    tyre(clutter, V(-hx - 1.85, -1.45, 0.05), rng)
    trough = V(5.0, -hy - 0.45, -0.12)
    block(clutter, dressed, trough + V(-0.8, -0.3, 0.0), trough + V(0.8, 0.3, 0.12), 0.015)
    for sx, sy, ex, ey in ((-0.8, -0.3, 0.8, -0.2), (-0.8, 0.2, 0.8, 0.3), (-0.8, -0.2, -0.7, 0.2), (0.7, -0.2, 0.8, 0.2)):
        block(clutter, dressed, trough + V(sx, sy, 0.12), trough + V(ex, ey, 0.5), 0.015)
    block(clutter, "glass_dirty", trough + V(-0.7, -0.2, 0.34), trough + V(0.7, 0.2, 0.36))
    b.col("rock", "trough", trough + V(-0.8, -0.3, 0.0), trough + V(0.8, 0.3, 0.5))
    for step_index in range(3):
        block(clutter, dressed, V(-3.9 + step_index * 0.3, -hy - 0.7, -0.12), V(-3.0, -hy - 0.02, 0.13 + step_index * 0.25), 0.02)
    b.col("rock", "mount", V(-3.9, -hy - 0.7, -0.12), V(-3.0, -hy, 0.38))
    b.col("rock", "mount", V(-3.3, -hy - 0.7, 0.38), V(-3.0, -hy, 0.63))
    lump(clutter, "dirt_debris", V(5.6, hy + 1.3, -0.1), (1.3, 1.0, 0.45), rng, 0.25, 2, -0.13)
    hay_heap(hay, V(5.4, hy + 1.2, 0.12), 0.85, 0.4, rng, False)
    b.col("dirt", "heap", V(4.6, hy + 0.5, -0.12), V(6.6, hy + 2.1, 0.2))
    gate = kit.Matrix.Translation(V(2.9, hy + 0.14, -0.1)) @ kit.Matrix.Rotation(0.1, 4, 'X')
    for z in (0.15, 0.45, 0.75, 1.05):
        local_block(clutter, planks, gate, -1.2, 1.2, -0.015, 0.015, z - 0.05, z + 0.05, 0.003, "board")
    for x in (-1.15, 0.0, 1.15):
        local_block(clutter, beam, gate, x - 0.04, x + 0.04, 0.015, 0.06, 0.0, 1.2, 0.004)
    emit(clutter, kit.geo_box(2.5, 0.02, 0.09), planks, gate @ kit.Matrix.Translation(V(0.0, 0.03, 0.6)) @ kit.Matrix.Rotation(0.42, 4, 'Y'), "board")
    base_weeds(plants, -hx, hx, -hy, hy, rng, 1.2, lambda p: (p.y < 0.0 and abs(p.x) < hx - 0.1 and (-4.0 < p.x < -2.9 or -2.3 < p.x < 3.6 or 4.1 < p.x < 5.9)) or (p.y > 0.0 and abs(p.x) < hx - 0.1 and (-1.4 < p.x < 0.1 or 1.6 < p.x < 4.2)), 0.1, 0.35)
    for index in range(30):
        kit.nettle(plants, V(rng.uniform(-hx - 2.4, -hx - 0.3), rng.uniform(-2.2, 1.8), -0.1), rng, (0.4, 1.0))
    for index in range(8):
        kit.nettle(plants, V(rng.uniform(4.4, 6.8), hy + rng.uniform(0.3, 2.3), -0.1), rng, (0.5, 1.1))
    kit.ivy(plants, V(hx + 0.04, -2.2, -0.1), V(1.0, 0.0, 0.0), rng, 3.2, 1.0, 8, 28.0)
    kit.ivy(plants, V(hx + 0.04, 2.6, -0.1), V(1.0, 0.0, 0.0), rng, 2.6, 0.8, 6, 28.0)
    kit.ivy(plants, V(-5.2, hy + 0.03, -0.1), V(0.0, 1.0, 0.0), rng, 2.8, 0.9, 7, 28.0)
    kit.ivy(plants, V(6.2, -hy - 0.03, -0.1), V(0.0, -1.0, 0.0), rng, 2.6, 0.5, 5, 26.0)
    for index in range(16):
        lump(plants, "roof_moss", gable.point(1.0, rng.uniform(-hx, 2.2), rng.uniform(0.1, 2.5), 0.05), (rng.uniform(0.08, 0.18), rng.uniform(0.06, 0.12), 0.035), rng, 0.3, 1)
    for index in range(40):
        kit.grass_tuft(plants, V(rng.uniform(bay + 0.2, ix - 0.2), rng.uniform(-iy + 0.2, iy - 0.2), -0.01), rng, (0.08, 0.25), (4, 8), 0.05)
    kit.scatter_chips(plants, "foliage", -bay, bay, -iy, -1.0, 0.0, 50, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    kit.scatter_chips(plants, "clay_roof_tiles", -3.6, -2.0, -2.1, -0.6, 0.004, 22, rng, (0.04, 0.09), (0.012, 0.018), 0.45)
    kit.scatter_chips(plants, "clay_roof_tiles", -6.0, -4.0, hy + 0.2, hy + 1.0, -0.1, 14, rng, (0.04, 0.09), (0.012, 0.018), 0.45)
    for part in (roof, frame_part, plants):
        kit.deform(part, kit.sagging(*sag_roof))
    return b


def barn_far():
    b = kit.Build("barn_far", 502)
    rng = b.rng
    shell = b.part("shell", 30.0)
    hx, hy, ix = 7.0, 4.0, 6.45
    gable = kit.Gable(-hx - 0.2, hx + 0.2, hy, 0.3, 3.42, 38.0)
    front = kit.facade("front", ix, hy)
    back = kit.facade("back", ix, hy)
    wall_top = gable.under(hy, 0.03)
    kit.wall(shell, "granite_rubble", front, kit.rect(-ix, ix, -1.5, wall_top), [], 0.55)
    kit.wall(shell, "granite_rubble", back, kit.rect(-ix, ix, -1.5, wall_top), [], 0.55)
    kit.skin(shell, "soot", front, kit.rect(-1.7, 1.7, 0.0, 3.1), [], 0.004, 0.002, False)
    kit.skin(shell, "soot", back, kit.rect(0.1, 1.2, 0.0, 2.1), [], 0.004, 0.002, False)
    kit.skin(shell, "soot", kit.facade("right", hx, hy), kit.rect(-0.5, 0.5, 3.62, 4.92), [], 0.004, 0.032, False)
    for side in ("left", "right"):
        frame = kit.facade(side, hx, hy)
        kit.wall(shell, "granite_rubble", frame, kit.rect(-hy, hy, -1.5, wall_top), [], 0.55)
        upright_slab(shell, "timber_planks_weathered", frame, [(-hy, wall_top - 0.12), (hy, wall_top - 0.12), (hy, wall_top), (0.0, gable.under(0.0, 0.03)), (-hy, wall_top)], 0.06, 0.03)
    kit.roof_slab(shell, gable, -1.0, -hx - 0.2, hx + 0.2, "clay_roof_tiles", 0.25)
    kit.roof_slab(shell, gable, 1.0, -hx - 0.2, 2.4, "clay_roof_tiles", 0.25)
    kit.roof_slab(shell, gable, 1.0, 5.2, hx + 0.2, "clay_roof_tiles", 0.25)
    kit.roof_slab(shell, gable, 1.0, 2.4, 5.2, "clay_roof_tiles", 0.25, 0.0, 1.2)
    kit.corrugated_sheet(shell, gable.point(1.0, 5.2, 1.2, 0.0), V(-1.0, 0.0, 0.0), gable.upslope(1.0), 2.8, gable.run - 1.2, rng, "corrugated_rusty", 0.0, 1.0, 1, 0.25)
    kit.corrugated_sheet(shell, V(-hx + 0.02, -2.4, 2.8), V(0.0, 1.0, 0.0), V(-2.75, 0.0, -0.62).normalized(), 4.4, 2.95, rng, "corrugated_rusty", 0.0, 1.0, 1, 0.03)
    for y in (-2.0, 1.6):
        block(shell, "timber_beam", V(-hx - 2.6, y - 0.06, -0.12), V(-hx - 2.48, y + 0.06, 2.12))
    block(shell, "terracotta", V(-hx - 0.2, -0.13, gable.ridge_top - 0.04), V(hx + 0.2, 0.13, gable.ridge_top + 0.09))
    upright_slab(shell, "timber_planks_weathered", kit.plane(V(-1.65, -hy - 0.88, 0.0), V(1.0, 0.0, 0.0)), kit.rect(-0.84, 0.84, 0.04, 3.06), 0.05)
    upright_slab(shell, "timber_planks_weathered", front, kit.rect(1.7, 3.38, 0.04, 3.06), 0.08, 0.12)
    block(shell, "timber_beam", V(-2.15, -hy - 0.02, 3.1), V(2.15, -hy + 0.02, 3.4))
    block(shell, "timber_beam", V(hx - 0.3, -0.06, 5.08), V(hx + 1.1, 0.06, 5.22))
    hole = [gable.point(-1.0, x, d, 0.012) for x, d in ((-3.4, 3.2), (-2.2, 3.2), (-2.2, 4.3), (-3.4, 4.3))]
    emit(shell, kit.Geo(hole, [kit.orient((0, 1, 2, 3), hole, gable.normal(-1.0))]), "soot", None, "box")
    far_trim(shell, gable, hx, hy, 0.55, [wall_top] * 4)
    return b


buildings = {
    "cottage": (cottage, cottage_far),
    "house": (house, house_far),
    "ruin": (ruin, ruin_far),
    "shed": (shed, shed_far),
    "barn": (barn, barn_far),
}
heroes = {"house": house_notice}

views = {
    "cottage": {
        "detail": ((-0.4, -8.2, 1.75), (-2.0, -3.1, 1.4), 40.0),
        "interior_a": ((-0.4, -1.5, 1.6), (-3.4, 0.4, 1.0), 16.0),
        "interior_b": ((1.3, -0.95, 1.6), (3.5, 0.95, 0.8), 14.0),
        "top": 7.9,
        "levels": [("GROUND", 2.1, -0.4, 2.2), ("LOFT", 5.0, 2.25, 4.9), ("ROOF", 9.5, 2.9, 9.0)],
    },
    "house": {
        "detail": ((2.9, -8.4, 1.7), (1.0, -3.5, 1.55), 38.0),
        "interior_a": ((-1.35, -2.45, 1.6), (-3.3, 0.9, 0.95), 15.0),
        "interior_b": ((1.95, -1.55, 4.5), (3.0, 2.7, 3.75), 15.0),
        "top": 10.3,
        "levels": [("GROUND", 2.3, -0.4, 2.5), ("UPPER", 5.2, 2.55, 5.3), ("ROOF", 11.0, 5.3, 11.0)],
    },
    "ruin": {
        "detail": ((0.3, -8.0, 1.7), (-1.5, -2.6, 1.35), 35.0),
        "interior_a": ((0.9, 0.35, 1.6), (-3.2, -0.15, 1.2), 15.0),
        "interior_b": ((-2.45, 1.2, 1.6), (2.6, -0.7, 0.75), 15.0),
        "exposure": 0.3,
        "fill": 0.0,
        "levels": [("GROUND", 1.0, -0.4, 1.2), ("TOP", 8.0, 0.9, 8.0)],
    },
    "shed": {
        "detail": ((3.6, -5.2, 1.5), (1.9, -0.4, 0.7), 38.0),
        "interior_a": ((0.45, -1.75, 1.6), (-1.3, 0.9, 1.15), 14.0),
        "interior_b": ((-0.6, -1.6, 1.6), (1.2, 1.7, 0.75), 14.0),
        "fill": 8.0,
        "levels": [("GROUND", 1.9, -0.4, 2.0), ("ROOF", 6.0, 2.0, 6.0)],
    },
    "barn": {
        "detail": ((-4.6, -10.2, 1.7), (-1.0, -4.0, 1.9), 38.0),
        "interior_a": ((0.9, -3.2, 1.6), (-4.6, 2.6, 1.0), 14.0),
        "interior_b": ((2.05, 1.7, 4.2), (6.2, -1.6, 3.3), 14.0),
        "fill": 40.0,
        "levels": [("GROUND", 2.2, -0.4, 2.3), ("LOFT", 4.6, 2.35, 4.6), ("ROOF", 12.0, 3.5, 12.0)],
    },
}


def build(name):
    maker, far_maker = buildings[name]
    kit.load_catalog()
    if name in heroes:
        heroes[name]()
    kit.reset_scene()
    started = time.time()
    b = maker()
    objects = b.finish()
    path, document = kit.export_building("bld_" + name, objects)
    triangles, markers, materials, problems = kit.audit(path, document)
    print("BUILD", name, "tris", triangles, "parts", len(b.parts), "boxes", len(b.boxes), round(time.time() - started, 1), "s", flush=True)
    for key, part in b.parts.items():
        print("  PART", part.name, part.triangles(), "tris", len(part.slots), "materials", flush=True)
    kit.reset_scene()
    far = far_maker()
    objects = far.finish()
    path, document = kit.export_building("bld_" + name + "_far", objects)
    kit.audit(path, document)


def remove(obj):
    kit.bpy.data.objects.remove(obj)


def preview(name, which=None):
    spec = views[name]
    kit.reset_scene()
    kit.load_catalog()
    objects = kit.import_building("bld_" + name)
    visual = [obj for obj in objects if obj.type == 'MESH' and not kit.is_marker(obj.name)]
    boxes = []
    for obj in objects:
        if obj.type == 'MESH' and kit.is_marker(obj.name):
            obj.hide_render = True
            low, high = kit.world_bounds([obj])
            boxes.append((obj.name, low, high))
    low, high = kit.world_bounds(visual)
    size_value = max(high.x - low.x, high.y - low.y, high.z - low.z)
    center = (low + high) * 0.5
    os.makedirs(kit.preview_root, exist_ok=True)
    kit.daylight(1.0, 3.4, (0.5, 0.62, -0.6))
    kit.ground(-0.12, 400.0)
    prefix = os.path.join(kit.preview_root, "bld_" + name + "_")
    todo = which or ["front", "back", "detail", "interior_a", "interior_b", "plan", "far"]
    kit.render_settings(samples, (1600, 900), spec.get("outside", 0.0))
    core_low, core_high = kit.world_bounds([obj for obj in visual if obj.name.endswith(("_shell", "_roof"))] or visual)
    core_high = V(core_high.x, core_high.y, min(core_high.z, spec.get("top", core_high.z)))
    target = V((core_low.x + core_high.x) * 0.5, (core_low.y + core_high.y) * 0.5, (core_high.z - 0.12) * 0.5)
    corners = [V(x, y, z) for x in (core_low.x, core_high.x) for y in (core_low.y, core_high.y) for z in (-0.12, core_high.z)]
    front_view = None
    for key, direction in (("front", V(0.7, -0.88, 0.2)), ("back", V(-0.76, 0.82, 0.24))):
        if key in todo or (key == "front" and "far" in todo):
            cam = kit.camera(target + direction.normalized() * 4.0, target, 35.0)
            kit.fit_camera(cam, corners, spec.get("margin", 0.04))
            if key in todo:
                kit.shoot(prefix + key + ".png")
            if key == "front":
                front_view = cam.location.copy()
            remove(cam)
    if "detail" in todo:
        position, aim, lens = spec["detail"]
        cam = kit.camera(V(*position), V(*aim), lens)
        kit.shoot(prefix + "detail.png")
        remove(cam)
    for key in ("interior_a", "interior_b"):
        if key not in todo:
            continue
        position, aim, lens = spec[key]
        position = V(*position)
        aim = V(*aim)
        kit.render_settings(samples, (1600, 900), spec.get("exposure", 2.9))
        cam = kit.camera(position, aim, lens, None, 0.03)
        fill = kit.point_light(position + V(0.0, 0.0, 0.35), spec.get("fill", 14.0), 0.4, (1.0, 0.93, 0.85))
        kit.shoot(prefix + key + ".png")
        remove(cam)
        remove(fill)
        kit.render_settings(samples, (1600, 900), spec.get("outside", 0.0))
    if "plan" in todo:
        kit.plan_sheet(name, spec["levels"], boxes, low, high, max(24, samples // 3), prefix + "plan.png")
    if "far" in todo:
        for obj in visual:
            obj.hide_render = True
        kit.import_building("bld_" + name + "_far")
        kit.render_settings(samples, (1600, 900), spec.get("outside", 0.0))
        cam = kit.camera(front_view, target, 35.0)
        kit.shoot(prefix + "far.png")
        remove(cam)


def sheet():
    rows = []
    for name in buildings:
        prefix = os.path.join(kit.preview_root, "bld_" + name + "_")
        rows.append((name, [(label, prefix + label + ".png") for label in ("front", "back", "detail", "interior_a", "interior_b", "plan", "far")]))
    kit.contact_sheet(rows, os.path.join(kit.preview_root, "buildings_sheet.png"))


def main():
    started = time.time()
    if mode == "library":
        kit.build_library(wanted)
    elif mode == "build":
        for name in wanted or list(buildings):
            build(name)
    elif mode == "preview":
        which = arguments[3].split(",") if len(arguments) > 3 else None
        for name in wanted or list(buildings):
            preview(name, which)
    elif mode == "sheet":
        sheet()
    print("DONE", mode, round(time.time() - started, 1), "s", flush=True)


if __name__ == "__main__":
    main()
