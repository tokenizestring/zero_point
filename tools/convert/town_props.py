import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import buildings as bd
import town_library as lib
import town_kit as tk
from buildkit import V, block, emit, rod, lump, local_block, frame_block

tau = math.pi * 2.0
up = V(0.0, 0.0, 1.0)
paper_sizes = {"newspaper": (0.36, 0.48), "notice": (0.3, 0.41), "poster": (0.3, 0.41), "letter": (0.19, 0.28), "envelope": (0.16, 0.08), "card": (0.13, 0.13), "police_notice": (0.3, 0.11), "music": (0.22, 0.22), "calendar": (0.2, 0.25)}


def pr(key, margin=1.0):
    return tk.atlas_uv(lib.prints, key, margin)


def sub_region(region, a0, a1, b0, b1):
    u0, u1, v0, v1 = region
    return (u0 + (u1 - u0) * a0, u0 + (u1 - u0) * a1, v0 + (v1 - v0) * b0, v0 + (v1 - v0) * b1)


def turned_dir(yaw):
    return V(math.cos(yaw), math.sin(yaw), 0.0)


def sheet(part, center, yaw, width, length, region, rng, fold=None, lift=0.003, curl=0.0):
    across = turned_dir(yaw)
    along = V(-across.y, across.x, 0.0)
    base = center + V(0.0, 0.0, lift)
    fold = rng.uniform(0.0, 0.45) if fold is None else fold
    half = length * 0.5
    p0 = base - across * (width * 0.5) - along * half
    p1 = base + across * (width * 0.5) - along * half
    p2 = base + across * (width * 0.5)
    p3 = base - across * (width * 0.5)
    raise_dir = (along * math.cos(fold) + up * math.sin(fold))
    p4 = p2 + raise_dir * half + up * curl
    p5 = p3 + raise_dir * half + up * curl
    u0, u1, v0, v1 = region
    vm = (v0 + v1) * 0.5
    emit(part, kit.Geo([p0, p1, p2, p3], [(0, 1, 2, 3)], [[(u0, v0), (u1, v0), (u1, vm), (u0, vm)]]), "town_print", None, "texture")
    emit(part, kit.Geo([p3, p2, p4, p5], [(0, 1, 2, 3)], [[(u0, vm), (u1, vm), (u1, v1), (u0, v1)]]), "town_print", None, "texture")


def papers(part, x0, x1, y0, y1, z, count, rng, kinds=("newspaper", "letter", "envelope", "notice", "card", "music")):
    for index in range(count):
        kind = rng.choice(kinds)
        w, h = paper_sizes[kind]
        scale = rng.uniform(0.85, 1.0)
        center = V(rng.uniform(x0, x1), rng.uniform(y0, y1), z + index * 0.0006)
        sheet(part, center, rng.uniform(0.0, tau), w * scale, h * scale, pr(kind), rng, rng.uniform(0.0, 0.35) if rng.random() < 0.6 else 0.0, 0.003, rng.uniform(0.0, 0.02))


def wall_sheet(part, center, normal, kind, rng, scale=1.0, tilt=0.0):
    w, h = paper_sizes[kind]
    tk.atlas_panel(part, "town_print", center, normal, w * scale, h * scale, pr(kind), tilt, 0.004)


def cylinder(points_profile, segments):
    return kit.geo_lathe(points_profile, segments)


def label_can(part, position, rng, label, radius=None, height=None, lying=False, yaw=None):
    r = radius or rng.uniform(0.035, 0.045)
    h = height or rng.uniform(0.09, 0.12)
    if lying:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r)) @ kit.Matrix.Rotation(rng.uniform(0.0, tau) if yaw is None else yaw, 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.Matrix.Translation(position)
    band(part, matrix, r, 0.0, h, pr("label_" + label, 2.0), rng, 6)
    emit(part, kit.geo_lathe([(0.0, 0.0), (r, 0.0)], 6), "rusty_metal", matrix, "given", True)
    emit(part, kit.geo_lathe([(r, h), (0.0, h - 0.003)], 6), "rusty_metal", matrix, "given", True)


def label_jar(part, position, rng, label, radius=None, height=None):
    r = radius or rng.uniform(0.04, 0.055)
    h = height or rng.uniform(0.12, 0.17)
    matrix = kit.Matrix.Translation(position)
    emit(part, kit.geo_lathe([(0.0, 0.0), (r, 0.0), (r, h * 0.85), (r * 0.82, h * 0.95)], 6), "glass_dirty", matrix, "given", True)
    emit(part, kit.geo_lathe([(r * 0.86, h * 0.93), (r * 0.86, h + 0.01), (0.0, h + 0.01)], 6), "rusty_metal", matrix, "given", True)
    band(part, matrix, r + 0.002, h * 0.25, h * 0.68, pr("label_" + label, 2.0), rng, 6)


def plate_light(part, position, rng, radius=None, tilt=0.0, yaw=None):
    r = radius or rng.uniform(0.1, 0.13)
    profile = [(0.0, 0.0), (r * 0.6, 0.0), (r, 0.022), (r * 0.94, 0.026), (0.0, 0.01)]
    geo = kit.geo_lathe(profile, 10)
    region = kit.catalog["ceramic"]["regions"]["pattern"]
    geo.uvs = [[(region[0] + (0.5 + geo.points[i].x / (2.2 * r)) * (region[1] - region[0]), 0.5 + geo.points[i].y / (2.2 * r)) for i in face] for face in geo.faces]
    matrix = kit.Matrix.Translation(position) @ kit.Matrix.Rotation(rng.uniform(0, tau) if yaw is None else yaw, 4, 'Z') @ kit.Matrix.Rotation(tilt, 4, 'X')
    emit(part, geo, "ceramic", matrix, "texture", True)


def cup_light(part, position, rng):
    r = rng.uniform(0.035, 0.045)
    h = rng.uniform(0.07, 0.09)
    matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, bd.plain(kit.geo_lathe([(0.0, 0.0), (r * 0.7, 0.0), (r, h), (r * 0.9, h), (0.0, h * 0.15)], 8)), "ceramic", matrix, "texture", True)
    rod(part, "ceramic", matrix @ V(r * 0.95, 0.0, h * 0.75), matrix @ V(r + 0.022, 0.0, h * 0.45), 0.005, 3)


def chair_light(part, position, yaw, rng, name="timber_beam", seat="timber_planks_weathered", fallen=False):
    base = kit.turned(position, yaw)
    if fallen:
        base = kit.Matrix.Translation(position) @ kit.Matrix.Rotation(yaw, 4, 'Z') @ kit.Matrix.Translation(V(0.0, 0.0, 0.23)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X')
    for sx in (-0.19, 0.19):
        for sy in (-0.18, 0.18):
            top = 0.44 if sy < 0.0 else 0.95
            local_block(part, name, base, sx - 0.02, sx + 0.02, sy - 0.02, sy + 0.02, 0.0, top)
    local_block(part, seat, base, -0.22, 0.22, -0.21, 0.21, 0.42, 0.455, 0.0, "board")
    for z in (0.66, 0.84):
        local_block(part, name, base, -0.17, 0.17, 0.165, 0.19, z - 0.04, z + 0.04)
    local_block(part, name, base, -0.17, 0.17, -0.192, -0.168, 0.15, 0.18)
    local_block(part, name, base, -0.17, 0.17, 0.168, 0.192, 0.15, 0.18)


def table_light(part, x, y, z, width, depth, height, rng, top="floorboards", legs="timber_beam", yaw=0.0):
    base = kit.turned(V(x, y, z), yaw)
    boards = max(2, int(round(depth / 0.22)))
    for index in range(boards):
        y0 = -depth * 0.5 + depth * index / boards
        y1 = -depth * 0.5 + depth * (index + 1) / boards
        local_block(part, top, base, -width * 0.5, width * 0.5, y0 + 0.002, y1 - 0.002, height - 0.035 + rng.uniform(-0.002, 0.002), height, 0.0, "board")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            lx = sx * (width * 0.5 - 0.08)
            ly = sy * (depth * 0.5 - 0.07)
            local_block(part, legs, base, lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, 0.0, height - 0.035)
    for sy in (-1.0, 1.0):
        local_block(part, legs, base, -width * 0.5 + 0.08, width * 0.5 - 0.08, sy * (depth * 0.5 - 0.07) - 0.012, sy * (depth * 0.5 - 0.07) + 0.012, height - 0.13, height - 0.035)
    for sx in (-1.0, 1.0):
        local_block(part, legs, base, sx * (width * 0.5 - 0.08) - 0.012, sx * (width * 0.5 - 0.08) + 0.012, -depth * 0.5 + 0.07, depth * 0.5 - 0.07, height - 0.13, height - 0.035)


def curtain_light(part, top_a, top_b, drop, rng, name="fabric_worn", gather=0.55, torn=True, nx=7, ny=5, rail=True):
    points = []
    faces = []
    span = top_b - top_a
    normal = V(-span.y, span.x, 0.0).normalized()
    ragged = [rng.uniform(0.6, 1.0) if torn else 1.0 for index in range(nx + 1)]
    for j in range(ny + 1):
        for i in range(nx + 1):
            u = i / nx
            v = j / ny
            points.append(top_a + span * (u * gather) + V(0.0, 0.0, -drop * v * ragged[i]) + normal * (math.sin(u * 14.0) * 0.035 * (0.4 + 0.6 * v)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + nx + 1, a + nx + 2, a + 1))
    emit(part, kit.Geo(points, faces), name, None, "world", True)
    if rail:
        rod(part, "rusty_metal", top_a + V(0.0, 0.0, 0.02), top_b + V(0.0, 0.0, 0.02), 0.008, 4)


def dresser_light(build, part, clutter, center, yaw, rng, paint="painted_wood_green", width=1.35):
    base = kit.turned(center, yaw)
    depth = 0.46
    hw = width * 0.5
    bd.cabinet(part, center, width, depth, 0.0, 0.86, yaw, rng, "timber_planks_weathered", paint, 2, 2)
    local_block(part, "floorboards", base, -hw - 0.03, hw + 0.03, -depth * 0.5 - 0.03, depth * 0.5, 0.86, 0.9, 0.0, "board")
    back = depth * 0.5
    front = back - 0.24
    for x in (-hw, hw - 0.025):
        local_block(part, paint, base, x, x + 0.025, front, back, 0.9, 2.02, 0.0, "board")
    local_block(part, paint, base, -hw - 0.03, hw + 0.03, front - 0.03, back, 2.02, 2.08, 0.0, "board")
    local_block(part, "timber_planks_weathered", base, -hw, hw, back - 0.015, back, 0.9, 2.02)
    shelves = (1.28, 1.62, 1.96)
    for z in shelves:
        local_block(part, paint, base, -hw + 0.025, hw - 0.025, front, back, z - 0.022, z, 0.0, "board")
        local_block(part, paint, base, -hw + 0.025, hw - 0.025, front, front + 0.012, z + 0.03, z + 0.045)
    for z in (0.9,) + shelves[:-1]:
        x = -hw + 0.14
        while x < hw - 0.12:
            roll = rng.random()
            if roll < 0.5:
                radius = rng.uniform(0.1, 0.13)
                plate_light(clutter, base @ V(x, back - 0.06, z + radius * 0.96 + 0.004), rng, radius, 1.32 + rng.uniform(-0.05, 0.05), yaw)
                x += rng.uniform(0.24, 0.3)
            elif roll < 0.62:
                jug_light(clutter, base @ V(x, back - 0.12, z), rng)
                x += 0.22
            elif roll < 0.75:
                cup_light(clutter, base @ V(x, back - 0.12, z), rng)
                x += 0.14
            else:
                x += rng.uniform(0.18, 0.32)
    bd.footprint(build, "wood", "dresser", base, hw, depth * 0.5, 0.0, 0.9)
    bd.footprint(build, "wood", "dresser_rack", base @ kit.Matrix.Translation(V(0.0, (front + back) * 0.5, 0.0)), hw, 0.12, 1.26, 2.08)
    return base @ V(0.0, -0.1, 0.9)


def chest_light(build, part, center, yaw, rng, width=0.9, depth=0.46, height=0.95, wood="timber_beam", rows=4):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    t = 0.02
    local_block(part, wood, base, -hw, -hw + t, -hd, hd, 0.05, height, 0.0, "board")
    local_block(part, wood, base, hw - t, hw, -hd, hd, 0.05, height, 0.0, "board")
    local_block(part, wood, base, -hw, hw, hd - t, hd, 0.05, height, 0.0, "board")
    local_block(part, wood, base, -hw - 0.02, hw + 0.02, -hd - 0.02, hd, height, height + 0.03, 0.0, "board")
    local_block(part, wood, base, -hw, hw, -hd + 0.02, hd, 0.0, 0.08, 0.0, "board")
    span = (height - 0.1) / rows
    for row in range(rows):
        z0 = 0.09 + span * row
        z1 = z0 + span - 0.012
        pull = rng.uniform(0.05, 0.22) if rng.random() < 0.4 else 0.0
        if rng.random() < 0.15:
            local_block(part, "soot", base, -hw + t, hw - t, -hd + 0.01, -hd + 0.02, z0, z1)
            continue
        local_block(part, wood, base, -hw + t + 0.004, hw - t - 0.004, -hd - pull, -hd - pull + 0.02, z0, z1, 0.0, "board")
        if pull > 0.0:
            local_block(part, "timber_planks_weathered", base, -hw + t + 0.01, hw - t - 0.01, -hd - pull + 0.02, hd - 0.04, z0 + 0.01, z0 + 0.02)
        for sx in (-0.22, 0.22):
            local_block(part, "town_brass", base, sx * width - 0.03, sx * width + 0.03, -hd - pull - 0.018, -hd - pull, (z0 + z1) * 0.5 - 0.008, (z0 + z1) * 0.5 + 0.008)
    bd.footprint(build, "wood", "drawers", base, hw, hd, 0.0, height + 0.03)
    return base @ V(0.0, 0.0, height + 0.03)


def washstand_light(build, part, clutter, center, yaw, rng):
    base = kit.turned(center, yaw)
    table_light(part, center.x, center.y, center.z, 0.8, 0.45, 0.76, rng, "floorboards", "timber_beam", yaw)
    local_block(part, "timber_beam", base, -0.4, 0.4, 0.2, 0.225, 0.76, 0.98)
    bowl = base @ V(-0.12, 0.0, 0.76)
    emit(clutter, bd.plain(kit.geo_lathe([(0.0, 0.0), (0.08, 0.0), (0.18, 0.1), (0.165, 0.1), (0.075, 0.015), (0.0, 0.012)], 10)), "ceramic", kit.Matrix.Translation(bowl), "texture", True)
    jug_light(clutter, base @ V(0.2, 0.02, 0.76), rng)
    bd.footprint(build, "wood", "washstand", base, 0.4, 0.225, 0.0, 0.76)


def wardrobe_light(build, part, clutter, center, yaw, rng, width=1.1, depth=0.58, wood="timber_beam", paint="floorboards"):
    height = 1.95
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    for x0, x1 in ((-hw, -hw + 0.02), (hw - 0.02, hw)):
        local_block(part, "timber_planks_weathered", base, x0, x1, -hd, hd, 0.0, height - 0.08)
    local_block(part, "timber_planks_weathered", base, -hw, hw, hd - 0.02, hd, 0.06, height - 0.08)
    local_block(part, "timber_planks_weathered", base, -hw, hw, -hd, hd, 0.06, 0.08)
    local_block(part, paint, base, -hw + 0.01, hw - 0.01, -hd, -hd + 0.02, 0.0, 0.06)
    local_block(part, wood, base, -hw - 0.04, hw + 0.04, -hd - 0.04, hd + 0.04, height - 0.08, height, 0.008)
    door_w = width * 0.5 - 0.01
    local_block(part, paint, base, 0.005, hw - 0.005, -hd - 0.014, -hd, 0.07, height - 0.1, 0.0, "board")
    local_block(part, "rusty_metal", base, 0.05, 0.075, -hd - 0.03, -hd - 0.014, 0.95, 1.0)
    hinge = base @ kit.Matrix.Translation(V(-hw + 0.01, -hd - 0.012, 0.07)) @ kit.Matrix.Rotation(-1.9, 4, 'Z')
    local_block(part, paint, hinge, 0.0, door_w, 0.0, 0.014, 0.0, height - 0.17, 0.0, "board")
    rod(part, "rusty_metal", base @ V(-hw + 0.03, 0.0, 1.6), base @ V(hw - 0.03, 0.0, 1.6), 0.012, 5)
    curtain_light(clutter, base @ V(-0.4, 0.02, 1.58), base @ V(-0.1, 0.02, 1.58), 1.0, rng, rng.choice(("fabric_worn", "fabric_tartan")), 1.0, False, 4, 5, False)
    bd.footprint(build, "wood", "wardrobe", base, hw, hd, 0.0, height)
    return base


def bucket_light(part, position, rng, name="rusty_metal", tipped=False):
    r0 = rng.uniform(0.1, 0.12)
    r1 = r0 * 1.25
    h = rng.uniform(0.26, 0.32)
    if tipped:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r1)) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, kit.geo_lathe([(0.0, 0.0), (r0, 0.0), (r1, h), (r1 - 0.006, h), (r0 - 0.006, 0.006), (0.0, 0.006)], 10), name, matrix, "given", True)
    arc = [matrix @ V(-r1 * math.cos(math.pi * t / 4), 0.0, h * 0.95 + r1 * 0.9 * math.sin(math.pi * t / 4)) for t in range(5)]
    emit(part, kit.geo_tube(arc, kit.circle(0.004, 3), True), name, None, "given", True)


def jug_light(part, position, rng):
    h = rng.uniform(0.18, 0.26)
    r = h * 0.38
    matrix = kit.turned(position, rng.uniform(0, tau))
    emit(part, bd.plain(kit.geo_lathe([(0.0, 0.0), (r * 0.8, 0.0), (r, h * 0.35), (r * 0.72, h * 0.8), (r * 0.8, h), (r * 0.6, h * 0.8), (0.0, h * 0.1)], 9)), "ceramic", matrix, "texture", True)
    emit(part, bd.plain(kit.geo_tube([matrix @ V(r * 0.75, 0.0, h * 0.85), matrix @ V(r + 0.05, 0.0, h * 0.7), matrix @ V(r * 0.95, 0.0, h * 0.3)], kit.circle(0.008, 3), True)), "ceramic", None, "texture", True)


def armchair_light(build, part, center, yaw, rng, name="fabric_worn", legs="timber_beam"):
    base = kit.turned(center, yaw)
    for sx in (-0.3, 0.3):
        for sy in (-0.3, 0.3):
            local_block(part, legs, base, sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.12)
    emit(part, bd.cushion_geo(0.78, 0.74, 0.24, rng, 0.02, 0.0, 4, 3), name, base @ kit.Matrix.Translation(V(0.0, 0.0, 0.24)), "box", True)
    emit(part, bd.cushion_geo(0.58, 0.56, 0.14, rng, 0.05, 0.02, 4, 3), name, base @ kit.Matrix.Translation(V(0.02, -0.04, 0.41)), "box", True)
    emit(part, bd.cushion_geo(0.74, 0.62, 0.2, rng, 0.03, 0.0, 4, 3), name, base @ kit.Matrix.Translation(V(0.0, 0.32, 0.68)) @ kit.Matrix.Rotation(math.pi * 0.5 - 0.18, 4, 'X'), "box", True)
    for sx in (-1.0, 1.0):
        emit(part, bd.cushion_geo(0.14, 0.7, 0.3, rng, 0.03, 0.0, 2, 3), name, base @ kit.Matrix.Translation(V(sx * 0.33, 0.0, 0.5)), "box", True)
    bd.footprint(build, "fabric", "armchair", base, 0.4, 0.38, 0.0, 0.5)


def sofa_light(build, part, center, yaw, rng, width=1.7, name="fabric_worn", legs="timber_beam"):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    for sx in (-hw + 0.08, hw - 0.08):
        for sy in (-0.3, 0.3):
            local_block(part, legs, base, sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.12)
    emit(part, bd.cushion_geo(width, 0.78, 0.24, rng, 0.02, 0.0, 6, 3), name, base @ kit.Matrix.Translation(V(0.0, 0.0, 0.24)), "box", True)
    for index in range(3):
        x = -hw + 0.17 + (width - 0.34) * (index + 0.5) / 3
        emit(part, bd.cushion_geo((width - 0.34) / 3 - 0.01, 0.58, 0.14, rng, 0.05, 0.03 if index != 1 else 0.06, 3, 3), name, base @ kit.Matrix.Translation(V(x, -0.05, 0.41)) @ kit.Matrix.Rotation(rng.uniform(-0.05, 0.05), 4, 'Z'), "box", True)
    emit(part, bd.cushion_geo(width - 0.06, 0.62, 0.2, rng, 0.03, 0.0, 6, 3), name, base @ kit.Matrix.Translation(V(0.0, 0.33, 0.68)) @ kit.Matrix.Rotation(math.pi * 0.5 - 0.2, 4, 'X'), "box", True)
    for sx in (-1.0, 1.0):
        emit(part, bd.cushion_geo(0.16, 0.74, 0.32, rng, 0.03, 0.0, 2, 3), name, base @ kit.Matrix.Translation(V(sx * (hw - 0.08), 0.0, 0.5)), "box", True)
    bd.footprint(build, "fabric", "sofa", base, hw, 0.4, 0.0, 0.52)


def sg(key, margin=1.5):
    return tk.atlas_uv(lib.signs, key, margin)


def tin_box(part, position, yaw, rng, label, size=(0.22, 0.16, 0.2)):
    matrix = kit.turned(position, yaw)
    sx, sy, sz = size
    region = pr("label_" + label, 2.0)
    band_region = sub_region(region, 0.0, 1.0, 0.0, 0.12)
    tk.atlas_box(part, "town_print", matrix, -sx * 0.5, sx * 0.5, -sy * 0.5, sy * 0.5, 0.0, sz, region, band_region)


def stock_row(part, start, direction, length, rng, kinds, z_room=0.3, depth=0.12):
    direction = direction.normalized()
    side = V(-direction.y, direction.x, 0.0)
    travelled = 0.05
    while travelled < length - 0.06:
        roll = rng.random()
        kind = rng.choice(kinds)
        position = start + direction * travelled + side * (depth + rng.uniform(-0.02, 0.02))
        if kind == "can":
            label_can(part, position, rng, rng.choice(("peas", "beans", "peaches", "beef", "soup", "sardines", "milk", "cocoa")), None, min(z_room - 0.02, rng.uniform(0.09, 0.12)))
            if rng.random() < 0.35 and z_room > 0.26:
                label_can(part, position + V(0.0, 0.0, 0.12), rng, rng.choice(("peas", "beans", "soup", "milk")), None, 0.1)
            travelled += rng.uniform(0.085, 0.1)
        elif kind == "jar":
            label_jar(part, position, rng, rng.choice(("jam", "marmalade", "pickles", "honey")), None, min(z_room - 0.03, rng.uniform(0.12, 0.16)))
            travelled += rng.uniform(0.11, 0.13)
        elif kind == "bottle":
            label_bottle(part, position, rng, rng.choice(("ale", "stout", "gin", "cider")))
            travelled += rng.uniform(0.08, 0.1)
        elif kind == "box":
            tin_box(part, position, math.atan2(direction.y, direction.x) + rng.uniform(-0.1, 0.1), rng, rng.choice(("cocoa", "beef", "soup", "peaches")), (0.2, 0.14, min(z_room - 0.03, rng.uniform(0.14, 0.24))))
            travelled += 0.24
        else:
            travelled += rng.uniform(0.15, 0.4)
        if rng.random() < 0.2:
            travelled += rng.uniform(0.15, 0.45)


def wall_shelves(b, part, clutter, a, c, inward, z_levels, rng, kinds=("can", "can", "jar", "bottle", "box", "gap"), depth=0.34, wood="timber_beam", board="timber_planks_weathered", surface="wood", tag="shelves"):
    direction = (c - a).normalized()
    length = (c - a).length
    inward = inward.normalized()
    top = z_levels[-1] + 0.05
    count = max(2, int(length / 0.9) + 1)
    for index in range(count):
        p = a.lerp(c, index / (count - 1))
        lo, hi = kit.box_between(p - direction * 0.025, p + direction * 0.025 + inward * depth)
        block(part, wood, V(lo.x, lo.y, a.z), V(hi.x, hi.y, a.z + top))
    lo, hi = kit.box_between(a, c + inward * 0.015)
    block(part, board, V(lo.x, lo.y, a.z), V(hi.x, hi.y, a.z + top), 0.0, "world")
    for z in z_levels:
        lo, hi = kit.box_between(a + V(0.0, 0.0, z - 0.025), c + inward * depth + V(0.0, 0.0, z))
        block(part, board, lo, hi, 0.0, "board")
        lo, hi = kit.box_between(a + inward * (depth - 0.02) + V(0.0, 0.0, z), c + inward * depth + V(0.0, 0.0, z + 0.05))
        block(part, wood, lo, hi)
    facing_ok = V(-direction.y, direction.x, 0.0).dot(inward) >= 0.0
    for z0, z1 in zip(z_levels[:-1], z_levels[1:]):
        if rng.random() < 0.9:
            if facing_ok:
                stock_row(clutter, a + V(0.0, 0.0, z0), direction, length, rng, kinds, z1 - z0 - 0.05, depth * 0.45)
            else:
                stock_row(clutter, c + V(0.0, 0.0, z0), -direction, length, rng, kinds, z1 - z0 - 0.05, depth * 0.45)
    lo, hi = kit.box_between(a, c + inward * depth)
    b.col(surface, tag, V(lo.x, lo.y, a.z), V(hi.x, hi.y, a.z + top))


def shop_counter(b, part, clutter, x0, x1, y0, y1, rng, height=0.92, paint="painted_wood_green", top="floorboards"):
    block(part, top, V(x0 - 0.03, y0, height - 0.04), V(x1 + 0.03, y1, height), 0.0, "board")
    front = kit.plane(V(x0, 0.0, 0.0), V(-1.0, 0.0, 0.0))
    along = front[1]
    a_low = min(V(0.0, y0, 0.0).dot(along), V(0.0, y1, 0.0).dot(along))
    a_high = max(V(0.0, y0, 0.0).dot(along), V(0.0, y1, 0.0).dot(along))
    frame_block(part, paint, front, a_low, a_high, 0.0, height - 0.04, 0.0, 0.04, 0.0, "board")
    count = max(2, int((a_high - a_low) / 0.7))
    for index in range(count):
        p0 = a_low + (a_high - a_low) * index / count + 0.08
        p1 = a_low + (a_high - a_low) * (index + 1) / count - 0.08
        frame_block(part, paint, front, p0, p1, 0.15, height - 0.2, -0.015, 0.0, 0.0, "board")
    frame_block(part, "timber_beam", front, a_low, a_high, 0.0, 0.1, -0.02, 0.04)
    block(part, "timber_planks_weathered", V(x1 - 0.03, y0, 0.0), V(x1, y1, height - 0.04), 0.0, "board")
    block(part, "timber_planks_weathered", V(x0 + 0.04, y0, 0.35), V(x1 - 0.03, y1, 0.37), 0.0, "board")
    for y in (y0, y1):
        block(part, "timber_planks_weathered", V(x0, min(y, y + (0.03 if y == y0 else -0.03)), 0.0), V(x1, max(y, y + (0.03 if y == y0 else -0.03)), height - 0.04))
    tk.col(b, "wood", "counter", x0, x1, y0, y1, 0.0, height)


def till(part, position, yaw, rng):
    base = kit.turned(position, yaw)
    local_block(part, "town_brass", base, -0.2, 0.2, -0.17, 0.17, 0.0, 0.1)
    local_block(part, "soot", base, -0.19, 0.19, -0.16, 0.16, 0.1, 0.24)
    emit(part, kit.geo_box(0.38, 0.16, 0.04), "town_brass", base @ kit.Matrix.Translation(V(0.0, -0.12, 0.22)) @ kit.Matrix.Rotation(-0.6, 4, 'X'), "box")
    for column in range(5):
        for row in range(3):
            p = base @ V(-0.14 + column * 0.07, -0.18 + row * 0.035, 0.235 + row * 0.022)
            rod(part, "ceramic", p, p + V(0.0, 0.0, 0.025), 0.012, 5)
    local_block(part, "town_brass", base, -0.16, 0.16, -0.02, 0.12, 0.24, 0.36)
    local_block(part, "soot", base, -0.1, 0.1, -0.025, -0.02, 0.27, 0.33)
    pull = rng.uniform(0.12, 0.25)
    local_block(part, "timber_beam", base, -0.18, 0.18, -0.17 - pull, 0.12 - pull, 0.01, 0.09)


def scales(part, position, yaw, rng):
    base = kit.turned(position, yaw)
    local_block(part, "town_brass", base, -0.18, 0.18, -0.1, 0.1, 0.0, 0.04)
    rod(part, "town_brass", base @ V(0.0, 0.0, 0.04), base @ V(0.0, 0.0, 0.32), 0.012, 6)
    rod(part, "town_brass", base @ V(-0.2, 0.0, 0.3), base @ V(0.2, 0.0, 0.33), 0.008, 5)
    for sx, drop in ((-0.2, 0.12), (0.2, 0.18)):
        pan = base @ V(sx, 0.0, 0.33 - drop)
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.09, 0.02), (0.1, 0.035), (0.0, 0.01)], 10), "town_brass", kit.Matrix.Translation(pan), "given", True)
        rod(part, "town_brass", pan + V(0.0, 0.0, 0.02), base @ V(sx, 0.0, 0.31), 0.002, 3)


def slicer(part, position, yaw, rng):
    base = kit.turned(position, yaw)
    local_block(part, "town_metal", base, -0.22, 0.22, -0.16, 0.16, 0.0, 0.08)
    emit(part, tk.region_geo(kit.geo_lathe([(0.0, -0.01), (0.15, -0.01), (0.15, 0.01), (0.0, 0.01)], 14), "town_metal", "red"), "town_metal", base @ kit.Matrix.Translation(V(0.05, 0.0, 0.24)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "texture", True)
    local_block(part, "town_metal", base, 0.07, 0.12, -0.05, 0.05, 0.08, 0.2)
    local_block(part, "rusty_metal", base, -0.2, -0.02, -0.14, 0.14, 0.08, 0.1)
    rod(part, "timber_beam", base @ V(-0.15, 0.14, 0.12), base @ V(-0.15, 0.24, 0.12), 0.015, 6)


def glass_case(part, clutter, position, yaw, rng, width=0.36, depth=0.3, height=0.26, wood="timber_beam"):
    base = kit.turned(position, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    local_block(part, wood, base, -hw, hw, -hd, hd, 0.0, 0.035, 0.0, "board")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            cx = sx * (hw - 0.011)
            cy = sy * (hd - 0.011)
            local_block(part, wood, base, cx - 0.011, cx + 0.011, cy - 0.011, cy + 0.011, 0.035, height)
    for sy in (-1.0, 1.0):
        cy = sy * (hd - 0.011)
        local_block(part, wood, base, -hw, hw, cy - 0.011, cy + 0.011, height - 0.022, height)
    for sx in (-1.0, 1.0):
        cx = sx * (hw - 0.011)
        local_block(part, wood, base, cx - 0.011, cx + 0.011, -hd, hd, height - 0.022, height)
        local_block(part, "glass_dirty", base, cx - 0.002, cx + 0.002, -hd + 0.022, hd - 0.022, 0.035, height - 0.022)
    local_block(part, "glass_dirty", base, -hw + 0.012, hw - 0.012, -hd + 0.012, hd - 0.012, height - 0.016, height - 0.012)
    local_block(part, "glass_dirty", base, -hw + 0.022, hw - 0.022, hd - 0.013, hd - 0.009, 0.035, height - 0.022)
    local_block(part, "glass_dirty", base, -hw + 0.022, -0.01, -hd + 0.009, -hd + 0.013, 0.035, height - 0.022)
    for offset in (0.06, 0.15):
        label_jar(clutter, base @ V(-hw + offset, rng.uniform(-0.03, 0.04), 0.035), rng, rng.choice(("jam", "honey", "marmalade")), 0.035, 0.1)
    tin_box(clutter, base @ V(hw - 0.075, 0.0, 0.035), yaw + rng.uniform(-0.15, 0.15), rng, "cocoa", (0.09, 0.11, 0.12))
    for index in range(3):
        kit.pane(clutter, base @ kit.Matrix.Translation(V(rng.uniform(0.0, hw - 0.04), -hd - 0.02 - rng.uniform(0.0, 0.03), 0.002)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), -0.03, 0.03, 0.0, rng.uniform(0.03, 0.06), 0.0, "shard", rng)


def sack_truck(part, position, yaw, rng, lean=0.2, name="rusty_metal"):
    base = kit.turned(position + V(0.0, 0.0, 0.02), yaw) @ kit.Matrix.Rotation(-lean, 4, 'X')
    for sx in (-1.0, 1.0):
        rod(part, name, base @ V(sx * 0.18, 0.0, 0.02), base @ V(sx * 0.16, 0.0, 1.25), 0.016, 6)
        rod(part, name, base @ V(sx * 0.16, 0.0, 1.25), base @ V(sx * 0.13, -0.1, 1.38), 0.016, 6)
        emit(part, kit.geo_lathe([(0.0, -0.025), (0.11, -0.025), (0.12, 0.0), (0.11, 0.025), (0.0, 0.025)], 10), "soot", base @ kit.Matrix.Translation(V(sx * 0.25, 0.08, 0.12)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)
    for z in (0.45, 0.85, 1.15):
        rod(part, name, base @ V(-0.17, 0.0, z), base @ V(0.17, 0.0, z), 0.01, 4)
    rod(part, name, base @ V(-0.25, 0.08, 0.12), base @ V(0.25, 0.08, 0.12), 0.012, 5)
    local_block(part, name, base, -0.2, 0.2, -0.28, 0.02, 0.0, 0.014)


def tier_stand(b, part, clutter, center, yaw, rng, width=1.2, depth=0.7):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    levels = [(0.25, depth * 0.5), (0.55, depth * 0.33), (0.85, depth * 0.17)]
    for z, half in levels:
        local_block(part, "timber_planks_weathered", base, -hw, hw, -half, half, z - 0.025, z, 0.0, "board")
        local_block(part, "painted_wood_green", base, -hw, hw, -half - 0.01, -half, z - 0.12, z, 0.0, "board")
        local_block(part, "painted_wood_green", base, -hw, hw, half, half + 0.01, z - 0.12, z, 0.0, "board")
    for sx in (-hw + 0.03, hw - 0.03):
        local_block(part, "painted_wood_green", base, sx - 0.025, sx + 0.025, -depth * 0.5, depth * 0.5, 0.0, 0.88, 0.0, "board")
    direction = (base @ V(1.0, 0.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))
    for z, half in levels:
        for side in (-1.0, 1.0):
            if rng.random() < 0.75:
                stock_row(clutter, base @ V(-hw + 0.05, side * (half - 0.06), z), direction, width - 0.1, rng, ("can", "can", "box", "jar", "gap"), 0.28, 0.0)
    bd.footprint(b, "wood", "stand", base, hw, depth * 0.5, 0.0, 0.9)


def gas_cooker(b, part, clutter, position, yaw, rng):
    base = kit.turned(position, yaw)
    painted_box(part, "cream", base, -0.3, 0.3, -0.28, 0.28, 0.12, 0.9)
    for sx in (-0.26, 0.26):
        for sy in (-0.24, 0.24):
            local_block(part, "rusty_metal", base, sx - 0.02, sx + 0.02, sy - 0.02, sy + 0.02, 0.0, 0.12)
    local_block(part, "soot", base, -0.25, 0.25, -0.29, -0.28, 0.2, 0.62)
    rod(part, "town_brass", base @ V(-0.2, -0.32, 0.6), base @ V(0.2, -0.32, 0.6), 0.008, 5)
    for sx in (-0.15, 0.15):
        for sy in (-0.12, 0.12):
            emit(part, kit.geo_lathe([(0.0, 0.0), (0.07, 0.0), (0.075, 0.015), (0.0, 0.015)], 8), "rusty_metal", base @ kit.Matrix.Translation(V(sx, sy, 0.9)), "given", True)
    painted_box(part, "cream", base, -0.3, 0.3, 0.2, 0.28, 0.9, 1.35)
    local_block(part, "rusty_metal", base, -0.28, 0.28, -0.25, 0.22, 1.22, 1.25)
    for sx in (-0.2, -0.07, 0.07, 0.2):
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.015, 0.0), (0.015, 0.025), (0.0, 0.025)], 6), "soot", base @ kit.Matrix.Translation(V(sx, -0.29, 0.82)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)
    bd.kettle(clutter, base @ V(0.15, 0.1, 0.915), rng)
    bd.footprint(b, "metal", "cooker", base, 0.3, 0.28, 0.0, 1.35)


def painted_box(part, region_key, matrix, x0, x1, y0, y1, z0, z1):
    bd.region_box(part, "town_metal", region_key, matrix, x0, x1, y0, y1, z0, z1)


def enamel_sign(part, center, normal, width, height, key, rng, tilt=0.0):
    n = normal.normalized()
    upward = (up - n * up.dot(n)).normalized()
    right = upward.cross(n).normalized()
    matrix = kit.Matrix(((right.x, -n.x, upward.x, center.x), (right.y, -n.y, upward.y, center.y), (right.z, -n.z, upward.z, center.z), (0.0, 0.0, 0.0, 1.0))) @ kit.Matrix.Rotation(tilt, 4, 'Y')
    local_block(part, "rusty_metal", matrix, -width * 0.5, width * 0.5, -0.006, 0.0, -height * 0.5, height * 0.5)
    tk.atlas_panel(part, "town_print", center + n * 0.0062, n, width, height, pr(key, 2.0), tilt, 0.0)


def sack_row(part, start, direction, count, rng, name="fabric_worn"):
    for index in range(count):
        p = start + direction * (index * 0.42 + rng.uniform(-0.04, 0.04))
        bd.sack(part, p, rng, name, rng.uniform(0.85, 1.1))


def band(part, matrix, r, z0, z1, region, rng, segments=10):
    u0, u1, v0, v1 = region
    turn = rng.uniform(0.0, tau)
    points = []
    faces = []
    uvs = []
    for s in range(segments + 1):
        angle = turn + tau * s / segments
        points.append(V(r * math.cos(angle), r * math.sin(angle), z0))
        points.append(V(r * math.cos(angle), r * math.sin(angle), z1))
    for s in range(segments):
        a = s * 2
        faces.append((a, a + 2, a + 3, a + 1))
        uvs.append([(u0 + (u1 - u0) * s / segments, v0), (u0 + (u1 - u0) * (s + 1) / segments, v0), (u0 + (u1 - u0) * (s + 1) / segments, v1), (u0 + (u1 - u0) * s / segments, v1)])
    emit(part, kit.Geo(points, faces, uvs), "town_print", matrix, "texture", True)


def label_bottle(part, position, rng, label, lying=False, broken=False):
    h = rng.uniform(0.24, 0.3)
    r = rng.uniform(0.032, 0.04)
    profile = [(0.0, 0.0), (r, 0.0), (r, h * 0.6), (r * 0.3, h * 0.8), (r * 0.32, h), (0.0, h)]
    if broken:
        profile = [(0.0, 0.0), (r, 0.0), (r, h * 0.42), (0.0, h * 0.44)]
    if lying:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r)) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.Matrix.Translation(position) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z')
    emit(part, kit.geo_lathe(profile, 6), "glass_dirty", matrix, "given", True)
    band(part, matrix, r + 0.0015, h * 0.15, h * 0.42, pr("label_" + label, 2.0), rng, 6)


def book_row(part, start, direction, length, rng, depth=(0.14, 0.2), height=(0.18, 0.27), lean_end=True, flat_chance=0.08):
    direction = direction.normalized()
    travelled = 0.0
    cloth_band = lambda number: sub_region(pr("spine_" + str(number), 1.0), 0.0, 1.0, 0.0, 0.06)
    while travelled < length - 0.03:
        w = rng.uniform(0.022, 0.05)
        h = rng.uniform(*height)
        d = rng.uniform(*depth)
        number = rng.randint(0, 15)
        spine = pr("spine_" + str(number), 1.0)
        base = start + direction * (travelled + w * 0.5)
        if rng.random() < flat_chance and length - travelled > 0.3:
            stack = rng.randint(2, 4)
            for level in range(stack):
                number = rng.randint(0, 15)
                lying_h = rng.uniform(0.025, 0.045)
                lying_w = rng.uniform(0.17, 0.24)
                matrix = kit.place(start + direction * (travelled + 0.13) + V(0.0, 0.0, level * 0.04), direction, up) @ kit.Matrix.Rotation(rng.uniform(-0.15, 0.15), 4, 'Z')
                tk.atlas_box(part, "town_print", matrix @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y'), -lying_h, 0.0, 0.0, rng.uniform(0.14, 0.18), -lying_w * 0.5, lying_w * 0.5, pr("spine_" + str(number), 1.0), cloth_band(number))
            travelled += 0.27
            continue
        lean = rng.uniform(-0.12, 0.12) if rng.random() < 0.25 else 0.0
        matrix = kit.place(base, direction, up) @ kit.Matrix.Rotation(lean, 4, 'Y')
        tk.atlas_box(part, "town_print", matrix, -w * 0.5, w * 0.5, 0.0, d, 0.0, h, spine, cloth_band(number))
        travelled += w + 0.002


def bookcase(b, part, clutter, center, yaw, rng, width=0.9, height=1.8, depth=0.3, wood="timber_beam", fill=0.8, shelves=None):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    local_block(part, wood, base, -hw, -hw + 0.022, -hd, hd, 0.0, height)
    local_block(part, wood, base, hw - 0.022, hw, -hd, hd, 0.0, height)
    local_block(part, "timber_planks_weathered", base, -hw, hw, hd - 0.012, hd, 0.0, height)
    local_block(part, wood, base, -hw - 0.02, hw + 0.02, -hd - 0.02, hd, height, height + 0.035, 0.006)
    local_block(part, wood, base, -hw, hw, -hd, -hd + 0.02, 0.0, 0.08)
    count = shelves or max(2, int(height / 0.34))
    direction = (base @ V(1.0, 0.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))
    for index in range(count + 1):
        z = 0.08 + index * (height - 0.1) / count
        local_block(part, wood, base, -hw + 0.022, hw - 0.022, -hd + 0.005, hd - 0.012, z - 0.022, z, 0.0, "board")
        if index < count and rng.random() < fill:
            gap = rng.uniform(0.0, 0.25) if rng.random() < 0.5 else 0.0
            length = (width - 0.06) * rng.uniform(0.55, 1.0) - gap
            book_row(clutter, base @ V(-hw + 0.03 + gap, -hd + 0.03, z), direction, length, rng, (0.14, min(0.2, depth - 0.05)), (0.17, min(0.26, (height - 0.1) / count - 0.04)))
    bd.footprint(b, "wood", "bookcase", base, hw, hd, 0.0, height + 0.035)
    return base


def framed(part, center, normal, width, height, region, rng, frame_name="timber_beam", tilt=0.0, mount=0.0, depth=0.03):
    n = normal.normalized()
    hint = up
    upward = (hint - n * hint.dot(n)).normalized()
    right = upward.cross(n).normalized()
    if tilt:
        c = math.cos(tilt)
        s = math.sin(tilt)
        right, upward = right * c + upward * s, upward * c - right * s
    matrix = kit.Matrix(((right.x, -n.x, upward.x, center.x), (right.y, -n.y, upward.y, center.y), (right.z, -n.z, upward.z, center.z), (0.0, 0.0, 0.0, 1.0)))
    fw = 0.035 if width > 0.25 else 0.022
    hw = width * 0.5
    hh = height * 0.5
    for x0, x1, z0, z1 in ((-hw, hw, hh - fw, hh), (-hw, hw, -hh, -hh + fw), (-hw, -hw + fw, -hh + fw, hh - fw), (hw - fw, hw, -hh + fw, hh - fw)):
        local_block(part, frame_name, matrix, x0, x1, -depth, 0.0, z0, z1)
    inner = center + n * (depth * 0.4)
    tk.atlas_panel(part, "town_print", inner, n, width - fw * 2.0 + 0.004, height - fw * 2.0 + 0.004, region, tilt, 0.0)
    if mount:
        local_block(part, "wallpaper_faded", matrix, -hw + fw, hw - fw, -depth * 0.35, -depth * 0.3, -hh + fw, hh - fw)


def disc(part, name, center, normal, radius, region, segments=20, lift=0.002):
    n = normal.normalized()
    hint = up if abs(n.z) < 0.9 else V(0.0, 1.0, 0.0)
    upward = (hint - n * hint.dot(n)).normalized()
    right = upward.cross(n).normalized()
    u0, u1, v0, v1 = region
    cu = (u0 + u1) * 0.5
    cv = (v0 + v1) * 0.5
    ru = (u1 - u0) * 0.5
    rv = (v1 - v0) * 0.5
    origin = center + n * lift
    points = [origin]
    uvs_ring = []
    for s in range(segments):
        angle = tau * s / segments
        points.append(origin + (right * math.cos(angle) + upward * math.sin(angle)) * radius)
        uvs_ring.append((cu + ru * math.cos(angle), cv + rv * math.sin(angle)))
    faces = []
    uvs = []
    for s in range(segments):
        t = (s + 1) % segments
        faces.append((0, 1 + s, 1 + t))
        uvs.append([(cu, cv), uvs_ring[s], uvs_ring[t]])
    emit(part, kit.Geo(points, faces, uvs), name, None, "texture")


def wall_clock(part, center, normal, rng, radius=0.17, case="timber_beam"):
    n = normal.normalized()
    emit(part, kit.geo_lathe([(0.0, 0.0), (radius + 0.03, 0.0), (radius + 0.035, 0.03), (radius + 0.02, 0.06), (radius, 0.065), (radius, 0.05), (0.0, 0.05)], 20), case, kit.place(center, n.orthogonal(), n), "given", True)
    disc(part, "town_print", center + n * 0.052, n, radius, pr("clock", 2.0))


def candlestick(part, position, rng, name="town_brass"):
    h = rng.uniform(0.2, 0.28)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.05, 0.0), (0.02, 0.03), (0.012, h * 0.5), (0.012, h - 0.03), (0.025, h), (0.0, h)], 8), name, kit.Matrix.Translation(position), "given", True)
    if rng.random() < 0.7:
        stub = rng.uniform(0.02, 0.1)
        emit(part, kit.geo_lathe([(0.01, h), (0.0105, h + stub), (0.0, h + stub + 0.01)], 6), "ceramic", kit.Matrix.Translation(position), "given", True)


def vase(part, position, rng, name="ceramic", tall=None, lying=False):
    h = tall or rng.uniform(0.18, 0.3)
    r = h * 0.3
    profile = [(0.0, 0.0), (r * 0.6, 0.0), (r, h * 0.3), (r * 0.9, h * 0.6), (r * 0.45, h * 0.85), (r * 0.6, h), (r * 0.5, h), (r * 0.35, h * 0.85), (0.0, h * 0.2)]
    if lying:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r)) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.Matrix.Translation(position)
    geo = kit.geo_lathe(profile, 12)
    if name == "ceramic":
        region = kit.catalog["ceramic"]["regions"]["pattern"]
        geo.uvs = [[(region[0] + (region[1] - region[0]) * (0.1 + 0.8 * ((u / (tau * r)) % 1.0)), v / h) for u, v in face] for face in geo.uvs]
        emit(part, geo, name, matrix, "texture", True)
    else:
        emit(part, geo, name, matrix, "given", True)


def mantel_clock(part, position, yaw, rng, wood="timber_beam"):
    base = kit.turned(position, yaw)
    local_block(part, wood, base, -0.16, 0.16, -0.07, 0.07, 0.0, 0.03)
    local_block(part, wood, base, -0.13, 0.13, -0.06, 0.06, 0.03, 0.2)
    emit(part, kit.geo_lathe([(0.0, -0.06), (0.13, -0.06), (0.13, 0.06), (0.0, 0.06)], 12, 0.0, True, True), wood, base @ kit.Matrix.Translation(V(0.0, 0.0, 0.2)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)
    disc(part, "town_print", base @ V(0.0, -0.062, 0.17), (base @ V(0.0, -1.0, 0.0)) - (base @ V(0.0, 0.0, 0.0)), 0.075, pr("clock", 2.0), 16)


def mantel_set(part, start, direction, facing, length, rng, photos=True):
    direction = direction.normalized()
    facing = facing.normalized()
    yaw = math.atan2(facing.x, -facing.y)
    mantel_clock(part, start + direction * (length * 0.5), yaw, rng)
    for t in (0.1, 0.9):
        candlestick(part, start + direction * (length * t), rng)
    if rng.random() < 0.7:
        vase(part, start + direction * (length * 0.3) - facing * 0.03, rng)
    if photos:
        for t, key in ((0.72, "portrait_a"), (0.27, "portrait_b")):
            p = start + direction * (length * t) - facing * 0.06 + V(0.0, 0.0, 0.085)
            framed(part, p, facing, 0.12, 0.16, pr(key), rng, "town_brass", 0.08, 0.0, 0.012)


def wireless(part, position, yaw, rng):
    base = kit.turned(position, yaw)
    local_block(part, "timber_beam", base, -0.2, 0.2, -0.12, 0.12, 0.0, 0.32, 0.015)
    local_block(part, "fabric_worn", base, -0.15, 0.15, -0.125, -0.115, 0.12, 0.28)
    for x in (-0.1, 0.0, 0.1):
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.018, 0.0), (0.018, 0.015), (0.0, 0.02)], 10), "town_brass", base @ kit.Matrix.Translation(V(x, -0.12, 0.06)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)


def birdcage(part, position, rng, name="town_brass"):
    bars = 10
    r = 0.13
    h = 0.32
    emit(part, kit.geo_lathe([(0.0, 0.0), (r + 0.01, 0.0), (r + 0.01, 0.025), (0.0, 0.025)], 12), name, kit.Matrix.Translation(position), "given", True)
    for index in range(bars):
        angle = tau * index / bars
        a = position + V(math.cos(angle) * r, math.sin(angle) * r, 0.02)
        top = position + V(math.cos(angle) * r * 0.85, math.sin(angle) * r * 0.85, h)
        rod(part, name, a, top, 0.0025, 3)
        rod(part, name, top, position + V(0.0, 0.0, h + 0.08), 0.0025, 3)
    emit(part, kit.geo_lathe([(r * 0.86, h - 0.005), (r * 0.88, h - 0.005), (r * 0.88, h + 0.005), (r * 0.86, h + 0.005)], 12), name, kit.Matrix.Translation(position), "given", True)
    rod(part, name, position + V(0.0, 0.0, h + 0.08), position + V(0.0, 0.0, h + 0.14), 0.006, 5)


def bath(b, part, center, yaw, rng, length=1.6, width=0.72, height=0.62, feet="town_brass", segments=28):
    base = kit.turned(center, yaw)

    def ring(hx, hy, z, radius):
        points = []
        straight = max(hx - radius, 0.0)
        for s in range(segments):
            angle = tau * s / segments
            cx = math.cos(angle)
            sy = math.sin(angle)
            px = straight * (1.0 if cx >= 0.0 else -1.0) + radius * cx if abs(cx) > 1e-6 else 0.0
            points.append(V(px if abs(cx) > 1e-6 else 0.0, hy * sy, z))
        return points

    hx = length * 0.5
    hy = width * 0.5
    rings = [ring(hx - 0.1, hy - 0.08, 0.14, hy - 0.08), ring(hx - 0.02, hy - 0.02, 0.36, hy - 0.02), ring(hx, hy, height - 0.03, hy), ring(hx + 0.015, hy + 0.015, height, hy + 0.015), ring(hx - 0.04, hy - 0.035, height + 0.005, hy - 0.035), ring(hx - 0.07, hy - 0.06, height - 0.12, hy - 0.06), ring(hx - 0.17, hy - 0.11, 0.21, hy - 0.11)]
    points = [p for r in rings for p in r]
    faces = []
    for index in range(len(rings) - 1):
        for s in range(segments):
            t = (s + 1) % segments
            a = index * segments
            c = (index + 1) * segments
            faces.append((a + s, a + t, c + t, c + s))
    faces.append(tuple(reversed(range(0, segments))))
    last = (len(rings) - 1) * segments
    faces.append(tuple(range(last, last + segments)))
    geo = tk.region_geo(kit.Geo(points, faces), "ceramic", "plain", length + 0.1)
    emit(part, geo, "ceramic", base, "texture", True)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            foot = base @ V(sx * (hx - 0.2), sy * (hy - 0.12), 0.0)
            emit(part, kit.geo_lathe([(0.0, 0.0), (0.045, 0.0), (0.035, 0.05), (0.03, 0.1), (0.045, 0.15), (0.0, 0.16)], 8), feet, kit.Matrix.Translation(foot), "given", True)
    tap = base @ V(-hx + 0.05, 0.0, height)
    for dy in (-0.08, 0.08):
        p = base @ V(-hx + 0.04, dy, height)
        rod(part, "town_brass", p, p + V(0.0, 0.0, 0.12), 0.012, 6)
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.03, 0.0), (0.03, 0.012), (0.0, 0.02)], 6), "town_brass", kit.Matrix.Translation(p + V(0.0, 0.0, 0.12)), "given", True)
    bd.footprint(b, "metal", "bath", base, hx + 0.02, hy + 0.02, 0.0, height)
    return base


def toilet(b, part, center, yaw, rng, cistern_height=2.0, seat_up=False, segments=14, chain=True):
    base = kit.turned(center, yaw)
    pan = base @ kit.Matrix.Scale(1.25, 4, V(0.0, 1.0, 0.0))
    emit(part, bd.plain(kit.geo_lathe([(0.0, 0.0), (0.13, 0.0), (0.12, 0.05), (0.1, 0.18), (0.16, 0.34), (0.19, 0.4), (0.17, 0.41), (0.12, 0.3), (0.05, 0.24), (0.0, 0.24)], segments)), "ceramic", pan, "texture", True)
    seat = base @ kit.Matrix.Translation(V(0.0, 0.0, 0.41))
    if seat_up:
        seat = base @ kit.Matrix.Translation(V(0.0, 0.19, 0.42)) @ kit.Matrix.Rotation(-1.45, 4, 'X') @ kit.Matrix.Translation(V(0.0, -0.21, 0.0))
    emit(part, kit.geo_lathe([(0.11, 0.0), (0.2, 0.0), (0.2, 0.025), (0.11, 0.025)], segments), "timber_beam", seat @ kit.Matrix.Scale(1.15, 4, V(0.0, 1.0, 0.0)), "given", True)
    cistern = base @ kit.Matrix.Translation(V(0.0, 0.3, cistern_height))
    local_block(part, "rusty_metal", cistern, -0.24, 0.24, -0.11, 0.11, 0.0, 0.26, 0.015)
    for sx in (-0.18, 0.18):
        local_block(part, "rusty_metal", cistern, sx - 0.015, sx + 0.015, -0.11, 0.13, -0.12, 0.0)
    rod(part, "rusty_metal", base @ V(0.0, 0.3, cistern_height), base @ V(0.0, 0.3, 0.45), 0.02, 8)
    rod(part, "rusty_metal", base @ V(0.0, 0.3, 0.45), base @ V(0.0, 0.18, 0.38), 0.02, 8)
    if chain:
        links = [base @ V(0.2, 0.2, cistern_height + 0.05)] + [base @ V(0.2 + 0.01 * math.sin(t), 0.2, cistern_height - 0.12 * t) for t in range(1, 8)]
        emit(part, kit.geo_tube(links, kit.circle(0.004, 4), True), "rusty_metal", None, "given", True)
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.015, 0.01), (0.012, 0.08), (0.0, 0.09)], 8), "ceramic", kit.Matrix.Translation(links[-1] - V(0.0, 0.0, 0.09)), "given", True)
    bd.footprint(b, "rock", "toilet", base @ kit.Matrix.Translation(V(0.0, 0.05, 0.0)), 0.22, 0.3, 0.0, 0.42)


def basin(b, part, center, yaw, rng, segments=16):
    base = kit.turned(center, yaw)
    emit(part, bd.plain(kit.geo_lathe([(0.0, 0.0), (0.12, 0.0), (0.08, 0.06), (0.07, 0.6), (0.1, 0.66), (0.0, 0.66)], max(6, segments * 3 // 4))), "ceramic", base, "texture", True)
    bowl = base @ kit.Matrix.Translation(V(0.0, 0.02, 0.66)) @ kit.Matrix.Scale(1.3, 4, V(1.0, 0.0, 0.0))
    emit(part, bd.plain(kit.geo_lathe([(0.0, 0.0), (0.12, 0.0), (0.24, 0.13), (0.25, 0.16), (0.23, 0.16), (0.11, 0.04), (0.0, 0.04)], segments)), "ceramic", bowl, "texture", True)
    for sx in (-0.12, 0.12):
        p = base @ V(sx, 0.2, 0.82)
        rod(part, "town_brass", p, p + V(0.0, 0.0, 0.08), 0.01, 6)
        rod(part, "town_brass", p + V(0.0, 0.0, 0.08), (base @ V(sx, 0.12, 0.88)), 0.008, 6)
    bd.footprint(b, "rock", "basin", base, 0.3, 0.22, 0.0, 0.82)


def wall_mirror(part, center, normal, width, height, rng, frame_name="timber_beam", cracked=True):
    n = normal.normalized()
    upward = (up - n * up.dot(n)).normalized()
    right = upward.cross(n).normalized()
    matrix = kit.Matrix(((right.x, -n.x, upward.x, center.x), (right.y, -n.y, upward.y, center.y), (right.z, -n.z, upward.z, center.z), (0.0, 0.0, 0.0, 1.0)))
    hw = width * 0.5
    hh = height * 0.5
    fw = 0.04
    for x0, x1, z0, z1 in ((-hw, hw, hh - fw, hh), (-hw, hw, -hh, -hh + fw), (-hw, -hw + fw, -hh + fw, hh - fw), (hw - fw, hw, -hh + fw, hh - fw)):
        local_block(part, frame_name, matrix, x0, x1, -0.03, 0.0, z0, z1)
    if cracked:
        kit.pane(part, matrix, -hw + fw, hw - fw, -hh + fw, hh - fw, -0.02, "shard", rng)
        kit.pane(part, matrix, -hw + fw, hw - fw, -hh + fw, hh - fw, -0.018, "shard", rng)
    else:
        local_block(part, "glass_dirty", matrix, -hw + fw, hw - fw, -0.022, -0.018, -hh + fw, hh - fw)


def chamber_pot(part, position, rng):
    emit(part, bd.plain(kit.geo_lathe([(0.0, 0.0), (0.07, 0.0), (0.11, 0.06), (0.11, 0.11), (0.125, 0.12), (0.12, 0.125), (0.1, 0.115), (0.09, 0.02), (0.0, 0.015)], 12)), "ceramic", kit.Matrix.Translation(position), "texture", True)


def flowerpot(part, position, rng, tipped=False, scale=1.0, plant=False):
    r = 0.09 * scale
    h = 0.16 * scale
    profile = [(0.0, 0.0), (r * 0.7, 0.0), (r, h), (r * 1.1, h), (r * 1.1, h * 1.12), (r * 0.98, h * 1.12), (r * 0.9, h * 0.15), (0.0, h * 0.15)]
    if tipped:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r)) @ kit.Matrix.Rotation(rng.uniform(0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5 + 0.1, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.Matrix.Translation(position)
    emit(part, kit.geo_lathe(profile, 12), "terracotta", matrix, "given", True)
    if plant and not tipped:
        lump(part, "dirt_debris", position + V(0.0, 0.0, h * 0.95), (r * 0.9, r * 0.9, 0.02), rng, 0.2, 1)
        for index in range(rng.randint(5, 9)):
            yaw = rng.uniform(0.0, tau)
            out = V(math.cos(yaw), math.sin(yaw), 0.0)
            stem_top = position + V(0.0, 0.0, h) + out * rng.uniform(0.05, 0.18) * scale + V(0.0, 0.0, rng.uniform(0.15, 0.4) * scale)
            rod(part, "timber_beam", position + V(0.0, 0.0, h), stem_top, 0.003, 3)
            kit.leaf_quad(part, stem_top, out + V(0.0, 0.0, 0.8), out, rng.uniform(0.07, 0.14) * scale, rng, "foliage")


def plant_stand(part, position, rng):
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.02), (0.03, 0.04), (0.025, 0.7), (0.15, 0.72), (0.15, 0.75), (0.0, 0.75)], 10), "timber_beam", kit.Matrix.Translation(position), "given", True)
    flowerpot(part, position + V(0.0, 0.0, 0.75), rng, False, 1.3, True)


def airer(part, clutter, center, yaw, length, rng, ceiling):
    base = kit.turned(center, yaw)
    for index in range(4):
        y = -0.18 + index * 0.12
        rod(part, "timber_beam", base @ V(-length * 0.5, y, 0.0), base @ V(length * 0.5, y, 0.0), 0.012, 6)
    for x in (-length * 0.5 + 0.08, length * 0.5 - 0.08):
        arc = [base @ V(x, -0.22 + 0.44 * t / 6, 0.03 * math.sin(math.pi * t / 6) + 0.03) for t in range(7)]
        emit(part, kit.geo_tube(arc, kit.circle(0.008, 4), True), "rusty_metal", None, "given", True)
        rod(part, "hay", base @ V(x, 0.0, 0.08), base @ V(x, 0.0, ceiling - center.z), 0.005, 4)
    for index in range(rng.randint(2, 4)):
        y = -0.18 + rng.randint(0, 3) * 0.12
        x = rng.uniform(-length * 0.35, length * 0.2)
        curtain_light(clutter, base @ V(x, y, 0.01), base @ V(x + rng.uniform(0.3, 0.55), y, 0.01), rng.uniform(0.35, 0.6), rng, rng.choice(("fabric_worn", "mattress", "fabric_tartan")), 1.0, False, 4, 4, False)


def mangle(b, part, center, yaw, rng):
    base = kit.turned(center, yaw)
    for sx in (-0.32, 0.32):
        rod(part, "rusty_metal", base @ V(sx, -0.25, 0.0), base @ V(sx, 0.0, 0.85), 0.02, 6)
        rod(part, "rusty_metal", base @ V(sx, 0.25, 0.0), base @ V(sx, 0.0, 0.85), 0.02, 6)
        rod(part, "rusty_metal", base @ V(sx, -0.12, 0.42), base @ V(sx, 0.12, 0.42), 0.015, 6)
        rod(part, "rusty_metal", base @ V(sx, 0.0, 0.85), base @ V(sx, 0.0, 1.25), 0.03, 6)
    local_block(part, "timber_planks_weathered", base, -0.38, 0.38, -0.2, 0.2, 0.42, 0.45, 0.004, "board")
    for z in (1.0, 1.13):
        rod(part, "timber_beam", base @ V(-0.31, 0.0, z), base @ V(0.31, 0.0, z), 0.055, 12)
    local_block(part, "rusty_metal", base, -0.34, 0.34, -0.05, 0.05, 1.24, 1.3, 0.006)
    wheel = base @ V(0.42, 0.0, 1.06)
    axis = (base @ V(1.0, 0.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))
    bd.wheel_spoked(part, wheel, axis, 0.3, rng, 6, "rusty_metal", "rusty_metal", 0.04, 0.03, True)
    rod(part, "rusty_metal", base @ V(0.33, 0.0, 1.06), base @ V(0.45, 0.0, 1.06), 0.02, 6)
    rod(part, "timber_beam", wheel + ((base @ V(0.0, 0.2, 0.15)) - (base @ V(0.0, 0.0, 0.0))), wheel + ((base @ V(0.1, 0.2, 0.15)) - (base @ V(0.0, 0.0, 0.0))), 0.02, 6)
    bd.footprint(b, "metal", "mangle", base, 0.45, 0.28, 0.0, 1.3)


def cot(b, part, clutter, center, yaw, rng):
    base = kit.turned(center, yaw)
    hx = 0.62
    hy = 0.34
    for sx in (-hx, hx):
        for sy in (-hy, hy):
            local_block(part, "painted_wood_white", base, sx - 0.025, sx + 0.025, sy - 0.025, sy + 0.025, 0.0, 0.95)
    for sy in (-hy, hy):
        for z in (0.32, 0.9):
            local_block(part, "painted_wood_white", base, -hx, hx, sy - 0.015, sy + 0.015, z - 0.025, z + 0.025)
        x = -hx + 0.09
        while x < hx - 0.05:
            if rng.random() > 0.08:
                local_block(part, "painted_wood_white", base, x - 0.012, x + 0.012, sy - 0.01, sy + 0.01, 0.34, 0.88)
            x += 0.09
    for sx in (-hx, hx):
        local_block(part, "painted_wood_white", base, sx - 0.015, sx + 0.015, -hy, hy, 0.3, 0.92, 0.004, "board")
    local_block(part, "timber_planks_weathered", base, -hx, hx, -hy, hy, 0.3, 0.32)
    bd.mattress(clutter, base @ V(0.0, 0.0, 0.37), (hx * 2 - 0.06, hy * 2 - 0.05, 0.1), 0.0, rng, 0.03)
    lump(clutter, "fabric_worn", base @ V(0.2, 0.05, 0.45), (0.1, 0.08, 0.1), rng, 0.3, 1)
    bd.footprint(b, "wood", "cot", base, hx, hy, 0.0, 0.95)


def sewing_table(b, part, center, yaw, rng):
    base = kit.turned(center, yaw)
    local_block(part, "timber_beam", base, -0.45, 0.45, -0.22, 0.22, 0.72, 0.76, 0.006)
    for sx in (-0.38, 0.38):
        emit(part, kit.geo_box(0.04, 0.4, 0.7), "rusty_metal", base @ kit.Matrix.Translation(V(sx, 0.0, 0.36)), "box")
    rod(part, "rusty_metal", base @ V(-0.38, 0.0, 0.12), base @ V(0.38, 0.0, 0.12), 0.012, 6)
    local_block(part, "rusty_metal", base, -0.25, 0.1, -0.15, 0.15, 0.06, 0.09, 0.004)
    axis = (base @ V(1.0, 0.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))
    bd.wheel_spoked(part, base @ V(0.3, 0.0, 0.38), axis, 0.22, rng, 5, "rusty_metal", "rusty_metal", 0.03, 0.03, True)
    head = base @ kit.Matrix.Translation(V(-0.05, 0.0, 0.76))
    local_block(part, "soot", head, -0.2, 0.2, -0.06, 0.06, 0.0, 0.05, 0.01)
    local_block(part, "soot", head, 0.12, 0.2, -0.06, 0.06, 0.05, 0.28, 0.015)
    local_block(part, "soot", head, -0.24, 0.2, -0.05, 0.05, 0.24, 0.31, 0.015)
    local_block(part, "soot", head, -0.24, -0.16, -0.055, 0.055, 0.1, 0.31, 0.012)
    emit(part, kit.geo_lathe([(0.0, -0.02), (0.06, -0.02), (0.06, 0.02), (0.0, 0.02)], 10), "town_brass", head @ kit.Matrix.Translation(V(0.22, 0.0, 0.2)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)
    bd.footprint(b, "wood", "sewing", base, 0.45, 0.22, 0.0, 0.76)


def hall_stand(b, part, clutter, center, yaw, rng):
    base = kit.turned(center, yaw)
    for sx in (-0.42, 0.42):
        local_block(part, "timber_beam", base, sx - 0.03, sx + 0.03, -0.03, 0.03, 0.0, 2.0, 0.006)
    local_block(part, "timber_beam", base, -0.45, 0.45, -0.03, 0.03, 1.95, 2.05, 0.008)
    local_block(part, "timber_beam", base, -0.42, 0.42, -0.12, 0.03, 0.55, 0.6, 0.005)
    local_block(part, "rusty_metal", base, -0.42, -0.12, -0.14, 0.02, 0.02, 0.05)
    wall_mirror(part, base @ V(0.0, -0.035, 1.35), (base @ V(0.0, -1.0, 0.0)) - (base @ V(0.0, 0.0, 0.0)), 0.5, 0.6, rng, "timber_beam", True)
    hooks = []
    for x in (-0.36, -0.12, 0.12, 0.36):
        p = base @ V(x, -0.03, 1.82)
        rod(part, "town_brass", p, base @ V(x, -0.1, 1.86), 0.006, 4)
        hooks.append(base @ V(x, -0.11, 1.86))
    for hook in rng.sample(hooks, 2):
        direction = ((base @ V(1.0, 0.0, 0.0)) - (base @ V(0.0, 0.0, 0.0))).normalized()
        curtain_light(clutter, hook - direction * 0.14, hook + direction * 0.14, rng.uniform(0.75, 1.0), rng, "fabric_worn", 1.0, False, 4, 5, False)
    for index in range(2):
        p = base @ V(-0.32 + index * 0.14, -0.06, 0.05)
        rod(part, "soot", p, p + V(rng.uniform(-0.05, 0.05), rng.uniform(-0.03, 0.03), 0.8), 0.012, 5)
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.05, 0.25), (0.045, 0.6), (0.0, 0.62)], 8), "fabric_worn", kit.Matrix.Translation(p + V(0.0, 0.0, 0.15)), "given", True)
    bd.footprint(b, "wood", "stand", base, 0.45, 0.14, 0.0, 2.05)


def coal_scuttle(part, position, rng, tipped=False):
    matrix = kit.turned(position, rng.uniform(0, tau), 0.0, 0.0 if not tipped else 1.4)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.12, 0.0), (0.15, 0.25), (0.13, 0.3), (0.0, 0.3)], 12), "town_brass", matrix, "given", True)
    lump(part, "soot", position + V(0.0, 0.0, 0.28 if not tipped else 0.08), (0.11, 0.11, 0.05), rng, 0.4, 1)


def fender(part, start, end, rng, name="town_brass"):
    rod(part, name, start + V(0.0, 0.0, 0.1), end + V(0.0, 0.0, 0.1), 0.012, 6)
    direction = (end - start).normalized()
    local_block(part, name, kit.place((start + end) * 0.5, direction, up), -(end - start).length * 0.5, (end - start).length * 0.5, -0.01, 0.01, 0.0, 0.08, 0.003)


def fire_irons(part, position, rng):
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.08, 0.0), (0.08, 0.015), (0.0, 0.02)], 10), "town_brass", kit.Matrix.Translation(position), "given", True)
    rod(part, "town_brass", position, position + V(0.0, 0.0, 0.62), 0.008, 5)
    for index in range(3):
        angle = tau * index / 3
        top = position + V(math.cos(angle) * 0.04, math.sin(angle) * 0.04, 0.6)
        rod(part, "rusty_metal", top + V(0.0, 0.0, 0.08), position + V(math.cos(angle) * 0.06, math.sin(angle) * 0.06, 0.03), 0.007, 4)


def privy(b, parts, x0, x1, y0, y1, z, rng, door_side="left", name="granite_rubble", roof_name="slate_roof"):
    shell = parts["yard"]
    t = 0.14
    height = 2.15
    lo = z - 0.4
    for wx0, wx1, wy0, wy1 in ((x0, x1, y0, y0 + t), (x0, x1, y1 - t, y1), (x1 - t, x1, y0, y1)):
        block(shell, name, V(wx0, wy0, lo), V(wx1, wy1, z + height), 0.0, "world")
        tk.col(b, "rock", "privy", wx0, wx1, wy0, wy1, lo, z + height)
    door = (y0 + t + 0.02, y1 - t - 0.02)
    block(shell, name, V(x0, y0, lo), V(x0 + t, door[0], z + height), 0.0, "world")
    block(shell, name, V(x0, door[1], lo), V(x0 + t, y1, z + height), 0.0, "world")
    block(shell, name, V(x0, door[0], z + 2.12), V(x0 + t, door[1], z + height), 0.0, "world")
    tk.col(b, "rock", "privy", x0, x0 + t, y0, door[0], lo, z + height)
    tk.col(b, "rock", "privy", x0, x0 + t, door[1], y1, lo, z + height)
    pitch = 0.18
    run = x1 - x0 + 0.24
    along = V(1.0, 0.0, -pitch).normalized()
    normal = V(pitch, 0.0, 1.0).normalized()
    center = V((x0 + x1) * 0.5, (y0 + y1) * 0.5, z + height + 0.12)
    emit(parts["roof"], kit.geo_box(run / along.x, y1 - y0 + 0.2, 0.035), roof_name, kit.place(center, along, normal), "world")
    for index in range(4):
        rod(parts["roof"], "timber_beam", V(x0 - 0.05, y0 - 0.06 + index * (y1 - y0 + 0.12) / 3, z + height + 0.1 + (x1 - x0) * 0.5 * pitch), V(x1 + 0.05, y0 - 0.06 + index * (y1 - y0 + 0.12) / 3, z + height + 0.1 - (x1 - x0) * 0.5 * pitch), 0.03, 4)
    tk.col(b, "rock", "privy_roof", x0 - 0.12, x1 + 0.12, y0 - 0.1, y1 + 0.1, z + height, z + height + 0.22)
    block(shell, "concrete", V(x0, y0, lo), V(x1, y1, z + 0.02), 0.0, "world")
    seat_x0 = x1 - t - 0.5
    block(parts["interior"], "timber_planks_weathered", V(seat_x0, y0 + t, z), V(x1 - t, y1 - t, z + 0.42), 0.004, "board")
    emit(parts["interior"], kit.geo_lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.004), (0.0, 0.004)], 12), "soot", kit.Matrix.Translation(V(seat_x0 + 0.25, (y0 + y1) * 0.5, z + 0.421)), "given", True)
    tk.col(b, "wood", "privy_seat", seat_x0, x1 - t, y0 + t, y1 - t, z, z + 0.42)
    nail = V(x1 - t - 0.01, y0 + t + 0.25, z + 1.05)
    rod(parts["interior"], "rusty_metal", nail, nail + V(-0.04, 0.0, 0.0), 0.003, 3)
    for index in range(4):
        tk.atlas_panel(parts["interior"], "town_print", nail + V(-0.006 - index * 0.002, 0.0, -0.08), V(-1.0, 0.0, 0.0), 0.13, 0.15, sub_region(pr("newspaper"), rng.uniform(0.0, 0.5), rng.uniform(0.5, 1.0), rng.uniform(0.0, 0.5), rng.uniform(0.5, 1.0)), rng.uniform(-0.1, 0.1), 0.0)
    return door


def coal_bunker(b, part, center, yaw, rng):
    base = kit.turned(center, yaw)
    for x0, x1, y0, y1 in ((-0.5, 0.5, -0.4, -0.34), (-0.5, 0.5, 0.34, 0.4), (-0.5, -0.44, -0.34, 0.34), (0.44, 0.5, -0.34, 0.34)):
        local_block(part, "concrete", base, x0, x1, y0, y1, 0.0, 0.85 if y0 > 0.0 else 0.6, 0.01)
    local_block(part, "concrete", base, -0.44, 0.44, -0.34, 0.34, 0.0, 0.05)
    lid = base @ kit.Matrix.Translation(V(0.0, 0.4, 0.86)) @ kit.Matrix.Rotation(-1.9, 4, 'X')
    local_block(part, "timber_planks_weathered", lid, -0.48, 0.48, 0.0, 0.8, 0.0, 0.025, 0.003, "board")
    lump(part, "soot", base @ V(0.0, 0.0, 0.25), (0.42, 0.3, 0.25), rng, 0.4, 2, (base @ V(0.0, 0.0, 0.0)).z)
    for index in range(8):
        lump(part, "soot", base @ V(rng.uniform(-0.4, 0.4), rng.uniform(-0.75, -0.42), 0.03), (0.04, 0.035, 0.03), rng, 0.4, 1)
    bd.footprint(b, "rock", "bunker", base, 0.5, 0.4, 0.0, 0.85)


def tin_bath(part, center, normal, rng):
    n = normal.normalized()
    matrix = kit.place(center, V(-n.y, n.x, 0.0), n) @ kit.Matrix.Scale(1.6, 4, V(1.0, 0.0, 0.0))
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.22, 0.0), (0.3, 0.26), (0.32, 0.27), (0.31, 0.28), (0.29, 0.27), (0.21, 0.01), (0.0, 0.01)], 16), "rusty_metal", matrix, "given", True)


def washing_line(part, clutter, a, b_point, rng, items=4):
    sag = 0.25
    points = [a.lerp(b_point, t / 10) - V(0.0, 0.0, sag * math.sin(math.pi * t / 10)) for t in range(11)]
    emit(part, kit.geo_tube(points, kit.circle(0.004, 4), False), "hay", None, "given", True)
    for index in range(items):
        t = rng.uniform(0.15, 0.75)
        k = int(t * 10)
        p0 = points[k].lerp(points[k + 1], (t * 10) % 1.0)
        p1 = points[min(k + 1, 9)].lerp(points[min(k + 2, 10)], (t * 10) % 1.0)
        curtain_light(clutter, p0 - V(0.0, 0.0, 0.01), p1 - V(0.0, 0.0, 0.01), rng.uniform(0.35, 0.7), rng, rng.choice(("fabric_worn", "mattress", "fabric_tartan")), 1.0, True, 4, 4, False)


def sideboard(b, part, clutter, center, yaw, rng, width=1.5, paint="timber_beam"):
    base = kit.turned(center, yaw)
    bd.cabinet(part, center, width, 0.48, 0.0, 0.86, yaw, rng, "timber_planks_weathered", paint, 3, 3, 2 if rng.random() < 0.5 else None)
    local_block(part, paint, base, -width * 0.5 - 0.03, width * 0.5 + 0.03, -0.27, 0.25, 0.86, 0.9, 0.006)
    bd.footprint(b, "wood", "sideboard", base, width * 0.5 + 0.03, 0.27, 0.0, 0.9)
    return base @ V(0.0, 0.0, 0.9)


def dressing_table(b, part, clutter, center, yaw, rng):
    base = kit.turned(center, yaw)
    chest_light(b, part, center, yaw, rng, 1.0, 0.46, 0.78, "timber_beam", 3)
    for sx in (-0.42, 0.42):
        local_block(part, "timber_beam", base, sx - 0.02, sx + 0.02, 0.1, 0.14, 0.81, 1.45, 0.004)
    wall_mirror(part, base @ V(0.0, 0.12, 1.15), (base @ V(0.0, -1.0, 0.0)) - (base @ V(0.0, 0.0, 0.0)), 0.7, 0.55, rng, "timber_beam", True)
    for index in range(rng.randint(2, 4)):
        bd.bottle(clutter, base @ V(rng.uniform(-0.4, 0.4), rng.uniform(-0.15, 0.05), 0.81), rng, rng.random() < 0.3)


def tray_items(clutter, origin, direction, rng, count=4):
    for index in range(count):
        p = origin + direction * (index * 0.12) + V(rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0.0)
        roll = rng.random()
        if roll < 0.35:
            cup_light(clutter, p, rng)
        elif roll < 0.6:
            plate_light(clutter, p, rng, None, 0.0)
        elif roll < 0.8:
            bd.bottle(clutter, p, rng, rng.random() < 0.5)
        else:
            bd.jug(clutter, p, rng)


def pub_counter(b, part, center, yaw, length, rng, depth=0.6, height=1.05, wood="timber_beam", panel="town_paint_green", ends=(True, True), tag="bar"):
    base = kit.turned(center, yaw)
    hl = length * 0.5
    hd = depth * 0.5
    local_block(part, wood, base, -hl - (0.04 if ends[0] else 0.0), hl + (0.04 if ends[1] else 0.0), -hd - 0.06, hd, height - 0.05, height, 0.006, "board")
    local_block(part, panel, base, -hl, hl, -hd, -hd + 0.035, 0.1, height - 0.05, 0.0, "board")
    local_block(part, wood, base, -hl, hl, -hd + 0.03, -hd + 0.07, 0.0, 0.1)
    count = max(1, int(round(length / 0.62)))
    for index in range(count + 1):
        a = -hl + length * index / count
        local_block(part, wood, base, max(a - 0.03, -hl), min(a + 0.03, hl), -hd - 0.025, -hd, 0.1, height - 0.05)
    for index in range(count):
        a = -hl + length * index / count
        c = -hl + length * (index + 1) / count
        local_block(part, panel, base, a + 0.09, c - 0.09, -hd - 0.014, -hd, 0.26, height - 0.2, 0.004, "board")
    for side, flag in ((-1.0, ends[0]), (1.0, ends[1])):
        if flag:
            local_block(part, panel, base, side * hl - 0.02, side * hl + 0.02, -hd, hd, 0.1, height - 0.05, 0.0, "board")
    for z in (0.12, 0.52):
        local_block(part, "timber_planks_weathered", base, -hl + 0.02, hl - 0.02, -hd + 0.04, hd - 0.03, z, z + 0.025, 0.0, "board")
    rail = -hd - 0.2
    rod(part, "town_brass", base @ V(-hl + 0.06, rail, 0.2), base @ V(hl - 0.06, rail, 0.2), 0.022, 8)
    for index in range(count + 1):
        a = min(max(-hl + length * index / count, -hl + 0.12), hl - 0.12)
        rod(part, "town_brass", base @ V(a, -hd - 0.025, 0.26), base @ V(a, rail, 0.2), 0.01, 5)
    bd.footprint(b, "wood", tag, base, hl, hd, 0.0, height)
    return base


def beer_pump(part, position, yaw, rng, label="ale", lean=0.18):
    base = kit.turned(position, yaw)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.045, 0.0), (0.042, 0.03), (0.03, 0.07), (0.0, 0.075)], 8), "town_brass", base, "given", True)
    grip = base @ kit.Matrix.Translation(V(0.0, 0.0, 0.07)) @ kit.Matrix.Rotation(-lean, 4, 'X')
    rod(part, "town_brass", grip @ V(0.0, 0.0, 0.0), grip @ V(0.0, 0.0, 0.1), 0.011, 6)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.016, 0.0), (0.024, 0.07), (0.027, 0.2), (0.019, 0.25), (0.0, 0.255)], 8), "ceramic", grip @ kit.Matrix.Translation(V(0.0, 0.0, 0.1)), "given", True)
    facing = (grip.to_3x3() @ V(0.0, -1.0, 0.0)).normalized()
    tk.atlas_panel(part, "town_print", grip @ V(0.0, -0.029, 0.27), facing, 0.075, 0.03, pr("label_" + label, 2.0), 0.0, 0.0)
    rod(part, "town_brass", base @ V(0.0, 0.03, 0.05), base @ V(0.0, 0.1, 0.06), 0.008, 5)
    rod(part, "town_brass", base @ V(0.0, 0.1, 0.06), base @ V(0.0, 0.12, 0.03), 0.007, 5)
    local_block(part, "rusty_metal", base, -0.07, 0.07, 0.06, 0.19, 0.0, 0.015)


def stool_light(part, position, rng, fallen=False, height=0.72, wood="timber_beam", seat="timber_planks_weathered"):
    if fallen:
        base = kit.Matrix.Translation(position + V(0.0, 0.0, 0.19)) @ kit.Matrix.Rotation(rng.uniform(0.0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y')
    else:
        base = kit.turned(position, rng.uniform(0.0, tau))
    emit(part, kit.geo_lathe([(0.0, height - 0.045), (0.175, height - 0.045), (0.17, height), (0.0, height)], 8), seat, base, "given", True)
    for k in range(4):
        angle = tau * k / 4 + math.pi * 0.25
        rod(part, wood, base @ V(math.cos(angle) * 0.12, math.sin(angle) * 0.12, height - 0.045), base @ V(math.cos(angle) * 0.19, math.sin(angle) * 0.19, 0.0), 0.016, 4)
        rod(part, wood, base @ V(math.cos(angle) * 0.17, math.sin(angle) * 0.17, 0.27), base @ V(math.cos(angle + tau / 4) * 0.17, math.sin(angle + tau / 4) * 0.17, 0.27), 0.009, 3)


def pub_table(b, part, position, rng, radius=0.36, height=0.72, top="timber_beam", iron="town_paint_black"):
    base = kit.turned(position, rng.uniform(0.0, tau))
    emit(part, kit.geo_lathe([(0.0, height - 0.035), (radius, height - 0.035), (radius + 0.008, height - 0.015), (radius, height), (0.0, height)], 12), top, base, "given", True)
    rod(part, iron, base @ V(0.0, 0.0, 0.1), base @ V(0.0, 0.0, height - 0.035), 0.03, 6)
    for k in range(3):
        angle = tau * k / 3
        rod(part, iron, base @ V(0.0, 0.0, 0.16), base @ V(math.cos(angle) * 0.3, math.sin(angle) * 0.3, 0.0), 0.022, 4)
    tk.col(b, "wood", "table", position.x - radius * 0.8, position.x + radius * 0.8, position.y - radius * 0.8, position.y + radius * 0.8, position.z, position.z + height)


def settle_light(b, part, center, yaw, rng, length=1.4, wood="timber_beam", seat="timber_planks_weathered", cushion="fabric_worn"):
    base = kit.turned(center, yaw)
    hl = length * 0.5
    local_block(part, seat, base, -hl + 0.03, hl - 0.03, -0.24, 0.2, 0.42, 0.46, 0.0, "board")
    local_block(part, wood, base, -hl + 0.03, hl - 0.03, -0.22, -0.2, 0.05, 0.42, 0.0, "board")
    count = max(3, int(length / 0.2))
    for index in range(count):
        a = -hl + 0.03 + (length - 0.06) * index / count
        c = -hl + 0.03 + (length - 0.06) * (index + 1) / count
        local_block(part, wood, base, a + 0.003, c - 0.003, 0.2, 0.235, 0.42, 1.4 - rng.uniform(0.0, 0.02), 0.0, "board")
    local_block(part, wood, base, -hl, hl, 0.16, 0.25, 1.38, 1.44, 0.004, "board")
    profile = [(-0.25, 0.0), (0.25, 0.0), (0.25, 1.44), (0.12, 1.44), (0.0, 0.72), (-0.25, 0.66)]
    for sx in (-1.0, 1.0):
        end = base @ kit.Matrix.Translation(V(sx * (hl - 0.015), 0.0, 0.0)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Z')
        kit.prism(part, wood, end, profile, -0.015, 0.015)
    if cushion and rng.random() < 0.7:
        emit(part, bd.cushion_geo(length - 0.2, 0.4, 0.07, rng, 0.03), cushion, base @ kit.Matrix.Translation(V(rng.uniform(-0.05, 0.05), -0.02, 0.5)), "box", True)
    bd.footprint(b, "wood", "settle", base, hl, 0.25, 0.0, 1.44)


def pint_glass(part, position, rng, tipped=False, broken=False):
    r = rng.uniform(0.034, 0.04)
    h = rng.uniform(0.12, 0.15) * (0.55 if broken else 1.0)
    profile = [(0.0, 0.0), (r * 0.82, 0.0), (r, h), (r * 0.92, h), (r * 0.76, 0.012), (0.0, 0.012)]
    if tipped:
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, r)) @ kit.Matrix.Rotation(rng.uniform(0.0, tau), 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -h * 0.5))
    else:
        matrix = kit.Matrix.Translation(position)
    emit(part, kit.geo_lathe(profile, 6), "glass_dirty", matrix, "given", True)


def wall_matrix(center, normal):
    n = normal.normalized()
    upward = (up - n * up.dot(n)).normalized()
    right = upward.cross(n).normalized()
    return kit.Matrix(((right.x, -n.x, upward.x, center.x), (right.y, -n.y, upward.y, center.y), (right.z, -n.z, upward.z, center.z), (0.0, 0.0, 0.0, 1.0)))


def dartboard(part, center, normal, rng, radius=0.23, cabinet="town_paint_black"):
    n = normal.normalized()
    matrix = wall_matrix(center, n)
    local_block(part, cabinet, matrix, -0.36, 0.36, -0.04, 0.0, -0.4, 0.4)
    emit(part, kit.geo_lathe([(0.0, 0.0), (radius + 0.012, 0.0), (radius + 0.012, 0.035), (0.0, 0.035)], 16), "soot", kit.place(center + n * 0.04, n.orthogonal(), n), "given", True)
    disc(part, "town_print", center + n * 0.076, n, radius, pr("dartboard", 2.0), 20)
    for sx, swing in ((-1.0, 2.6), (1.0, 2.9)):
        door = matrix @ kit.Matrix.Translation(V(sx * 0.36, -0.045, 0.0)) @ kit.Matrix.Rotation(sx * swing, 4, 'Z')
        local_block(part, cabinet, door, min(0.0, -sx * 0.36), max(0.0, -sx * 0.36), -0.02, 0.0, -0.4, 0.4, 0.0, "board")
    for index in range(3):
        angle = rng.uniform(0.0, tau)
        reach = rng.uniform(0.02, 0.17)
        tip = center + n * 0.076 + (matrix.to_3x3() @ V(math.cos(angle) * reach, 0.0, math.sin(angle) * reach))
        tail = tip + (n + V(rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), rng.uniform(-0.1, 0.2))).normalized() * 0.13
        rod(part, "rusty_metal", tip, tail, 0.004, 3)
        rod(part, "town_paint_red", tail - (tail - tip).normalized() * 0.035, tail, 0.011, 3)


def hanging_sign(part, anchor, normal, rng, region, width=0.8, height=1.0, reach=1.15, iron="town_paint_black", frame="town_paint_green"):
    n = normal.normalized()
    side = up.cross(n).normalized()
    rod(part, iron, anchor, anchor + n * reach, 0.022, 6)
    rod(part, iron, anchor - V(0.0, 0.0, 0.62), anchor + n * (reach * 0.55), 0.016, 5)
    lo, hi = kit.box_between(anchor - side * 0.06 - V(0.0, 0.0, 0.7), anchor + n * 0.015 + side * 0.06 + V(0.0, 0.0, 0.06))
    block(part, iron, lo, hi)
    curl = [anchor + n * (0.32 + 0.12 * math.cos(t * 0.5)) - V(0.0, 0.0, 0.2 + 0.12 * math.sin(t * 0.5)) for t in range(11)]
    emit(part, kit.geo_tube(curl, kit.circle(0.008, 4), True, side), iron, None, "given", True)
    for k in (0.18, 0.12 + width - 0.06):
        rod(part, iron, anchor + n * k, anchor + n * k - V(0.0, 0.0, 0.16), 0.007, 3)
    center = anchor + n * (0.12 + width * 0.5) - V(0.0, 0.0, 0.16 + height * 0.5)
    matrix = kit.place(center, n, up)
    local_block(part, frame, matrix, -width * 0.5 - 0.035, width * 0.5 + 0.035, -0.025, 0.025, -height * 0.5 - 0.035, height * 0.5 + 0.035, 0.004, "board")
    for sign in (-1.0, 1.0):
        tk.atlas_panel(part, "town_signs", center + side * (sign * 0.026), side * sign, width, height, region, 0.0, 0.0)
    return center


def lantern(b, part, anchor, normal, rng, iron="town_paint_black", kind="warm"):
    n = normal.normalized()
    arm = anchor + n * 0.42
    rod(part, iron, anchor, arm, 0.014, 5)
    rod(part, iron, anchor - V(0.0, 0.0, 0.28), anchor + n * 0.28, 0.01, 4)
    body = arm - V(0.0, 0.0, 0.42)
    rod(part, iron, arm, body + V(0.0, 0.0, 0.33), 0.006, 3)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.07, 0.0), (0.1, 0.22), (0.0, 0.225)], 4, math.pi * 0.25), "glass_dirty", kit.Matrix.Translation(body), "given", True)
    emit(part, kit.geo_lathe([(0.0, 0.22), (0.13, 0.22), (0.02, 0.33), (0.0, 0.34)], 4, math.pi * 0.25), iron, kit.Matrix.Translation(body), "given", True)
    emit(part, kit.geo_lathe([(0.0, -0.03), (0.08, -0.03), (0.08, 0.0), (0.0, 0.0)], 4, math.pi * 0.25), iron, kit.Matrix.Translation(body), "given", True)
    b.light(kind, body + V(0.0, 0.0, 0.12))


def cask_light(part, center, rng, radius=0.28, length=0.72, yaw=0.0, lying=True, wood="timber_planks_weathered", iron="rusty_metal", segments=10):
    profile = [(0.0, 0.0), (radius * 0.86, 0.0), (radius * 0.97, length * 0.2), (radius, length * 0.5), (radius * 0.97, length * 0.8), (radius * 0.86, length), (0.0, length)]
    if lying:
        matrix = kit.Matrix.Translation(center + V(0.0, 0.0, radius)) @ kit.Matrix.Rotation(yaw, 4, 'Z') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -length * 0.5))
    else:
        matrix = kit.Matrix.Translation(center) @ kit.Matrix.Rotation(yaw, 4, 'Z')
    emit(part, kit.geo_lathe(profile, segments), wood, matrix, "given", True)
    for z in (length * 0.15, length * 0.85):
        r = radius * (0.86 + 0.14 * math.sin(math.pi * z / length)) + 0.004
        emit(part, kit.geo_lathe([(r, z - 0.025), (r + 0.004, z), (r, z + 0.025)], segments), iron, matrix, "given", True)
    return matrix


def crate_light(part, center, size3, yaw, rng, name="timber_planks_weathered"):
    base = kit.turned(center, yaw)
    sx, sy, sz = size3
    local_block(part, name, base, -sx * 0.5, sx * 0.5, -sy * 0.5, sy * 0.5, 0.0, 0.015, 0.0, "board")
    for side in (-1.0, 1.0):
        local_block(part, name, base, -sx * 0.5, sx * 0.5, side * sy * 0.5 - 0.009, side * sy * 0.5 + 0.009, 0.0, sz - rng.uniform(0.0, 0.01), 0.0, "board")
        local_block(part, name, base, side * sx * 0.5 - 0.009, side * sx * 0.5 + 0.009, -sy * 0.5 + 0.009, sy * 0.5 - 0.009, 0.0, sz, 0.0, "board")
    return base


def bottle_crate(part, center, yaw, rng, label="ale", rows=2, cols=3, full=0.75):
    sx = cols * 0.09 + 0.03
    sy = rows * 0.09 + 0.03
    base = crate_light(part, center, (sx, sy, 0.2), yaw, rng)
    for r in range(rows):
        for c in range(cols):
            if rng.random() < full:
                p = base @ V(-sx * 0.5 + 0.06 + c * 0.09, -sy * 0.5 + 0.06 + r * 0.09, 0.0)
                emit(part, kit.geo_lathe([(0.034, 0.12), (0.034, 0.16), (0.011, 0.22), (0.012, 0.27), (0.0, 0.27)], 4, math.pi * 0.25), "glass_dirty", kit.Matrix.Translation(p), "given", True)
    return base


def stillage(b, part, x0, x1, y0, y1, rng, height=0.3, wood="timber_beam"):
    middle = (x0 + x1) * 0.5
    for x in (middle - 0.22, middle + 0.22):
        block(part, wood, V(x - 0.05, y0, height - 0.08), V(x + 0.05, y1, height), 0.004)
        for y in (y0 + 0.05, (y0 + y1) * 0.5, y1 - 0.05):
            block(part, wood, V(x - 0.05, y - 0.05, 0.0), V(x + 0.05, y + 0.05, height - 0.08), 0.004)


def urinal_trough(b, part, x0, x1, y_wall, inward, rng, name="ceramic"):
    def span(d0, d1):
        ya = y_wall + inward * d0
        yb = y_wall + inward * d1
        return min(ya, yb), max(ya, yb)
    s0, s1 = span(0.0, 0.035)
    block(part, name, V(x0, s0, 0.25), V(x1, s1, 1.3), 0.004)
    t0, t1 = span(0.0, 0.32)
    block(part, name, V(x0, t0, 0.0), V(x1, t1, 0.12), 0.006)
    g0, g1 = span(0.06, 0.27)
    block(part, "soot", V(x0 + 0.04, g0, 0.12), V(x1 - 0.04, g1, 0.125))
    count = max(2, int((x1 - x0) / 0.6))
    for index in range(1, count):
        x = x0 + (x1 - x0) * index / count
        d0, d1 = span(0.035, 0.4)
        block(part, name, V(x - 0.02, d0, 0.5), V(x + 0.02, d1, 1.25), 0.008)
    c0, c1 = span(0.0, 0.24)
    block(part, "rusty_metal", V(x0 + 0.1, c0, 2.05), V(x0 + 0.6, c1, 2.3), 0.01)
    p0, p1 = span(0.06, 0.06)
    rod(part, "rusty_metal", V(x0 + 0.35, p0, 2.05), V(x0 + 0.35, p0, 1.3), 0.02, 6)
    rod(part, "rusty_metal", V(x0 + 0.1, p0, 1.27), V(x1 - 0.1, p0, 1.27), 0.012, 6)
    tk.col(b, "rock", "urinal", x0, x1, t0, t1, 0.0, 1.3)


def bench_light(b, part, center, yaw, rng, length=1.4, wood="timber_planks_weathered", legs="timber_beam"):
    base = kit.turned(center, yaw)
    hl = length * 0.5
    for y0, y1 in ((-0.18, -0.02), (0.02, 0.18)):
        local_block(part, wood, base, -hl, hl, y0, y1, 0.42, 0.45, 0.0, "board")
    for sx in (-1.0, 1.0):
        local_block(part, legs, base, sx * (hl - 0.15) - 0.03, sx * (hl - 0.15) + 0.03, -0.17, 0.17, 0.0, 0.42)
    bd.footprint(b, "wood", "bench", base, hl, 0.2, 0.0, 0.45)


def drape_light(part, center, width, depth, drop, yaw, rng, name="fabric_worn", folds=5, hang_sides=(True, False), nx=8, ny=6):
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


def iron_bed_light(build, part, clutter, center, yaw, rng, length=1.95, width=1.25, frame="rusty_metal", bedding=True, blanket="fabric_tartan"):
    base = kit.turned(center, yaw)
    hx = length * 0.5
    hy = width * 0.5
    for sx in (-1.0, 1.0):
        top = 1.15 if sx < 0 else 0.85
        for sy in (-1.0, 1.0):
            rod(part, frame, base @ V(sx * hx, sy * hy, 0.0), base @ V(sx * hx, sy * hy, top), 0.022, 6)
            emit(part, kit.geo_lathe([(0.0, 0.0), (0.03, 0.0), (0.035, 0.03), (0.0, 0.06)], 6), frame, base @ kit.Matrix.Translation(V(sx * hx, sy * hy, top)), "given", True)
        for z in (0.36, top - 0.05):
            rod(part, frame, base @ V(sx * hx, -hy, z), base @ V(sx * hx, hy, z), 0.013, 4)
        bars = 5
        for index in range(1, bars):
            y = -hy + width * index / bars
            rod(part, frame, base @ V(sx * hx, y, 0.36), base @ V(sx * hx, y, top - 0.05), 0.007, 3)
    for sy in (-1.0, 1.0):
        local_block(part, frame, base, -hx, hx, sy * hy - 0.004, sy * hy + 0.004, 0.33, 0.37)
    local_block(part, frame, base, -hx + 0.05, hx - 0.05, -hy + 0.02, hy - 0.02, 0.362, 0.367)
    emit(clutter, bd.cushion_geo(length - 0.08, width - 0.06, 0.2, rng, 0.015, 0.06, 5, 3), "mattress", base @ kit.Matrix.Translation(V(0.0, 0.0, 0.47)), "box", True)
    if bedding:
        drape_light(clutter, base @ V(0.2, 0.0, 0.575), length * 0.7, width - 0.02, 0.3, yaw, rng, blanket, 6, (True, True))
        emit(clutter, bd.cushion_geo(0.36, 0.6, 0.12, rng, 0.04, 0.0, 3, 2), "mattress", base @ kit.turned(V(-hx + 0.28, 0.0, 0.63), 0.1), "box", True)
    bd.footprint(build, "metal", "bed", base, hx, hy, 0.33, 0.62)
    return base


def sink_light(b, part, clutter, center, yaw, rng, width=0.76, depth=0.48, drainer=0.5):
    base = kit.turned(center, yaw)
    hw = width * 0.5
    hd = depth * 0.5
    for sx in (-1.0, 1.0):
        local_block(part, "brick_red", base, sx * (hw - 0.08) - 0.07, sx * (hw - 0.08) + 0.07, -hd + 0.06, hd, 0.0, 0.62, 0.0, "box")
    local_block(part, "ceramic", base, -hw, hw, -hd, hd, 0.62, 0.67, 0.006)
    for x0, x1, y0, y1 in ((-hw, hw, -hd, -hd + 0.05), (-hw, hw, hd - 0.05, hd), (-hw, -hw + 0.05, -hd + 0.05, hd - 0.05), (hw - 0.05, hw, -hd + 0.05, hd - 0.05)):
        local_block(part, "ceramic", base, x0, x1, y0, y1, 0.67, 0.86, 0.004)
    local_block(part, "timber_planks_weathered", base, hw, hw + drainer, -hd + 0.03, hd, 0.84, 0.865, 0.0, "board")
    local_block(part, "timber_beam", base, hw + drainer - 0.05, hw + drainer, -hd + 0.03, hd, 0.0, 0.84)
    for sx in (-0.12, 0.12):
        rod(part, "town_brass", base @ V(sx, hd + 0.02, 1.05), base @ V(sx, hd - 0.1, 1.05), 0.012, 5)
        rod(part, "town_brass", base @ V(sx, hd - 0.1, 1.05), base @ V(sx, hd - 0.12, 0.95), 0.01, 5)
    bd.footprint(b, "rock", "sink", base @ kit.Matrix.Translation(V(drainer * 0.5, 0.0, 0.0)), hw + drainer * 0.5, hd, 0.0, 0.87)


def pew_light(b, part, center, yaw, rng, length=3.4, tilt=0.0, wood="timber_beam", seat="timber_planks_weathered"):
    base = kit.turned(center, yaw)
    if tilt:
        base = base @ kit.Matrix.Translation(V(0.0, 0.3, 0.0)) @ kit.Matrix.Rotation(tilt, 4, 'X') @ kit.Matrix.Translation(V(0.0, -0.3, 0.0))
    hl = length * 0.5
    local_block(part, seat, base, -hl + 0.03, hl - 0.03, -0.22, 0.2, 0.42, 0.46, 0.0, "board")
    back = base @ kit.Matrix.Translation(V(0.0, 0.2, 0.46)) @ kit.Matrix.Rotation(-0.14, 4, 'X')
    local_block(part, wood, back, -hl + 0.03, hl - 0.03, 0.0, 0.03, 0.0, 0.48, 0.0, "board")
    local_block(part, wood, base, -hl + 0.03, hl - 0.03, 0.27, 0.42, 0.76, 0.785, 0.0, "board")
    local_block(part, wood, base, -hl + 0.03, hl - 0.03, -0.2, -0.17, 0.08, 0.42, 0.0, "board")
    profile = [(-0.24, 0.0), (0.3, 0.0), (0.3, 0.92), (0.22, 1.0), (0.12, 1.0), (0.04, 0.6), (-0.24, 0.56)]
    for sx in (-1.0, 1.0):
        end = base @ kit.Matrix.Translation(V(sx * (hl - 0.015), 0.0, 0.0)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'Z')
        kit.prism(part, wood, end, profile, -0.02, 0.02)
    if tilt:
        corners = [base @ V(sx * hl, sy, sz) for sx in (-1.0, 1.0) for sy in (-0.24, 0.3) for sz in (0.0, 1.0)]
        lo = V(min(c.x for c in corners), min(c.y for c in corners), max(min(c.z for c in corners), center.z))
        hi = V(max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners))
        b.col("wood", "pew", lo, hi)
    else:
        bd.footprint(b, "wood", "pew", base, hl, 0.3, 0.0, 0.95)
    return base


def font_light(b, part, center, rng, stone="granite_ashlar", lid="timber_beam"):
    matrix = kit.Matrix.Translation(center)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.55, 0.0), (0.55, 0.15), (0.4, 0.15), (0.4, 0.25), (0.0, 0.25)], 8, math.pi / 8.0), stone, matrix, "given", True)
    emit(part, kit.geo_lathe([(0.0, 0.25), (0.18, 0.25), (0.15, 0.6), (0.2, 0.62), (0.42, 0.75), (0.45, 1.0), (0.38, 1.0), (0.35, 0.82), (0.0, 0.8)], 8, math.pi / 8.0), stone, matrix, "given", True)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.44, 0.0), (0.42, 0.05), (0.06, 0.55), (0.0, 0.58)], 8), lid, kit.Matrix.Translation(center + V(0.75, 0.25, 0.42)) @ kit.Matrix.Rotation(1.35, 4, 'Y') @ kit.Matrix.Translation(V(0.0, 0.0, -0.2)), "given", True)
    tk.col(b, "rock", "font", center.x - 0.5, center.x + 0.5, center.y - 0.5, center.y + 0.5, center.z, center.z + 1.0)


def pulpit_light(b, part, center, rng, wood="timber_beam", stone="granite_ashlar"):
    matrix = kit.Matrix.Translation(center)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.42, 0.0), (0.42, 0.12), (0.26, 0.2), (0.24, 0.85), (0.5, 1.0), (0.0, 1.0)], 8, math.pi / 8.0), stone, matrix, "given", True)
    emit(part, kit.geo_lathe([(0.0, 1.0), (0.62, 1.0), (0.64, 2.02), (0.68, 2.08), (0.6, 2.08), (0.58, 1.06), (0.0, 1.06)], 8, math.pi / 8.0), wood, matrix, "given", True)
    desk = kit.turned(center + V(0.0, 0.48, 2.0), 0.0) @ kit.Matrix.Rotation(-0.35, 4, 'X')
    local_block(part, wood, desk, -0.3, 0.3, -0.2, 0.2, 0.0, 0.025, 0.0, "board")
    tk.atlas_panel(part, "town_print", desk @ V(0.0, 0.0, 0.03), (desk.to_3x3() @ up).normalized(), 0.3, 0.3, pr("music", 2.0), 0.0, 0.0)
    for index in range(3):
        h = 0.27 * (index + 1)
        block(part, stone, V(center.x + 0.62 + index * 0.3, center.y - 0.35, center.z), V(center.x + 0.92 + index * 0.3, center.y + 0.35, center.z + 0.81 - h + 0.27), 0.006)
    tk.col(b, "wood", "pulpit", center.x - 0.66, center.x + 0.66, center.y - 0.66, center.y + 0.66, center.z, center.z + 2.08)


def lectern_light(b, part, clutter, center, yaw, rng):
    base = kit.turned(center, yaw)
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.25, 0.0), (0.22, 0.06), (0.06, 0.12), (0.0, 0.12)], 8), "town_brass", base, "given", True)
    rod(part, "town_brass", base @ V(0.0, 0.0, 0.1), base @ V(0.0, 0.0, 1.05), 0.03, 6)
    desk = base @ kit.Matrix.Translation(V(0.0, 0.0, 1.1)) @ kit.Matrix.Rotation(0.45, 4, 'X')
    local_block(part, "town_brass", desk, -0.28, 0.28, -0.2, 0.2, -0.02, 0.0)
    tk.atlas_panel(clutter, "town_print", desk @ V(0.0, 0.0, 0.004), (desk.to_3x3() @ up).normalized(), 0.34, 0.34, pr("music", 2.0), 0.0, 0.0)
    tk.col(b, "metal", "lectern", center.x - 0.3, center.x + 0.3, center.y - 0.3, center.y + 0.3, center.z, center.z + 1.2)


def organ_light(b, part, clutter, center, yaw, rng, wood="timber_beam", pipes="town_brass"):
    base = kit.turned(center, yaw)
    local_block(part, wood, base, -0.95, 0.95, -0.45, 0.45, 0.0, 1.55, 0.0, "board")
    local_block(part, wood, base, -0.95, 0.95, -0.05, 0.45, 1.55, 3.3, 0.0, "board")
    local_block(part, wood, base, -1.0, 1.0, -0.12, 0.5, 3.3, 3.42, 0.006, "board")
    for sx in (-1.0, 1.0):
        local_block(part, wood, base, sx * 0.95 - 0.06, sx * 0.95 + 0.06, -0.12, 0.45, 1.55, 3.3, 0.0, "board")
    heights = [1.25, 1.45, 1.6, 1.7, 1.6, 1.45, 1.25]
    for index, h in enumerate(heights):
        x = -0.72 + index * 0.24
        r = 0.055 + 0.012 * (1.0 - abs(index - 3) / 3.0)
        foot = base @ V(x, -0.11, 1.6)
        emit(part, kit.geo_lathe([(0.0, 0.0), (0.02, 0.0), (r, 0.18), (r, h), (r * 0.6, h + 0.01), (0.0, h + 0.01)], 6), pipes, kit.Matrix.Translation(foot), "given", True)
    local_block(part, wood, base, -0.75, 0.75, -0.75, -0.45, 0.72, 0.78, 0.0, "board")
    local_block(part, "ceramic", base, -0.65, 0.65, -0.7, -0.52, 0.78, 0.8)
    local_block(part, "soot", base, -0.65, 0.65, -0.6, -0.5, 0.8, 0.86)
    music = base @ kit.Matrix.Translation(V(0.0, -0.5, 0.95)) @ kit.Matrix.Rotation(0.25, 4, 'X')
    local_block(part, wood, music, -0.35, 0.35, -0.01, 0.01, 0.0, 0.32)
    bench_light(b, clutter, base @ V(0.0, -1.1, 0.0), yaw, rng, 1.1)
    bd.footprint(b, "wood", "organ", base, 0.95, 0.45, 0.0, 3.4)
    bd.footprint(b, "wood", "console", base @ kit.Matrix.Translation(V(0.0, -0.6, 0.0)), 0.75, 0.15, 0.0, 0.86)


def altar_light(b, part, clutter, center, yaw, rng, wood="timber_beam", cloth="fabric_worn"):
    base = kit.turned(center, yaw)
    local_block(part, wood, base, -0.95, 0.95, -0.38, 0.38, 0.0, 0.95, 0.0, "board")
    local_block(part, wood, base, -1.0, 1.0, -0.42, 0.42, 0.95, 1.0, 0.006, "board")
    local_block(part, cloth, base, -0.85, 0.85, -0.43, -0.4, 0.25, 0.97)
    local_block(part, cloth, base, -1.02, 1.02, -0.44, 0.44, 1.0, 1.012)
    for sx in (-0.7, 0.7):
        candlestick(clutter, base @ V(sx, 0.18, 1.012), rng)
    cross = base @ V(0.0, 0.25, 1.012)
    rod(clutter, "town_brass", cross, cross + V(0.0, 0.0, 0.55), 0.015, 5)
    rod(clutter, "town_brass", cross + V(0.0, 0.0, 0.38) - (base.to_3x3() @ V(0.14, 0.0, 0.0)), cross + V(0.0, 0.0, 0.38) + (base.to_3x3() @ V(0.14, 0.0, 0.0)), 0.015, 5)
    emit(clutter, kit.geo_lathe([(0.0, 0.0), (0.09, 0.0), (0.06, 0.04), (0.0, 0.05)], 6), "town_brass", kit.Matrix.Translation(cross), "given", True)
    bd.footprint(b, "wood", "altar", base, 1.0, 0.42, 0.0, 1.0)


def choir_stall(b, part, center, yaw, rng, length=1.8, wood="timber_beam"):
    base = kit.turned(center, yaw)
    hl = length * 0.5
    local_block(part, wood, base, -hl, hl, -0.2, 0.22, 0.42, 0.46, 0.0, "board")
    local_block(part, wood, base, -hl, hl, 0.22, 0.27, 0.0, 1.2, 0.0, "board")
    local_block(part, wood, base, -hl, hl, -0.2, -0.17, 0.05, 0.42, 0.0, "board")
    local_block(part, wood, base, -hl, hl, -0.75, -0.7, 0.0, 0.9, 0.0, "board")
    desk = base @ kit.Matrix.Translation(V(0.0, -0.66, 0.9)) @ kit.Matrix.Rotation(0.3, 4, 'X')
    local_block(part, wood, desk, -hl, hl, -0.12, 0.12, 0.0, 0.025, 0.0, "board")
    for sx in (-1.0, 1.0):
        local_block(part, wood, base, sx * hl - 0.025, sx * hl + 0.025, -0.75, 0.27, 0.0, 1.0, 0.0, "board")
    bd.footprint(b, "wood", "stall", base, hl, 0.25, 0.0, 1.2)
    bd.footprint(b, "wood", "stall", base @ kit.Matrix.Translation(V(0.0, -0.7, 0.0)), hl, 0.06, 0.0, 0.95)


def altar_rail(b, part, x0, x1, y, z, rng, wood="timber_beam"):
    count = max(2, int((x1 - x0) / 0.35))
    for index in range(count + 1):
        x = x0 + (x1 - x0) * index / count
        if rng.random() < 0.1 and 0 < index < count:
            continue
        local_block(part, wood, kit.Matrix.Translation(V(x, y, z)), -0.025, 0.025, -0.025, 0.025, 0.0, 0.82)
    block(part, wood, V(x0 - 0.04, y - 0.07, z + 0.82), V(x1 + 0.04, y + 0.07, z + 0.88), 0.006, "board")
    block(part, "fabric_worn", V(x0, y - 0.45, z), V(x1, y - 0.15, z + 0.1), 0.02)
    tk.col(b, "wood", "rail", x0 - 0.04, x1 + 0.04, y - 0.07, y + 0.07, z, z + 0.9)


def cellar_flap(part, x0, x1, y0, y1, z, rng, name="rusty_metal"):
    block(part, "granite_ashlar", V(x0 - 0.08, y0 - 0.08, z - 0.1), V(x1 + 0.08, y1 + 0.08, z + 0.01), 0.01)
    middle = (x0 + x1) * 0.5
    for a, c in ((x0, middle - 0.005), (middle + 0.005, x1)):
        block(part, name, V(a, y0, z + 0.01), V(c, y1, z + 0.028), 0.004)
        emit(part, kit.geo_lathe([(0.03, -0.004), (0.04, 0.0), (0.03, 0.004)], 6), name, kit.Matrix.Translation(V((a + c) * 0.5, (y0 + y1) * 0.5, z + 0.032)), "given", True)


def debris_field(parts, x0, x1, y0, y1, z, rng, plaster=20, glass=0, papers_count=3, leaves=0, slate=0):
    debris = parts["debris"]
    if plaster:
        tk.chips(debris, "plaster_interior", x0, x1, y0, y1, z, plaster, rng)
    if glass:
        tk.chips(debris, "glass_dirty", x0, x1, y0, y1, z, glass, rng, (0.02, 0.06), (0.003, 0.004))
    if papers_count:
        papers(debris, x0, x1, y0, y1, z, papers_count, rng)
    if leaves:
        tk.chips(debris, "foliage", x0, x1, y0, y1, z, leaves, rng, (0.02, 0.05), (0.002, 0.003), 0.5)
    if slate:
        tk.chips(debris, "slate_roof", x0, x1, y0, y1, z, slate, rng, (0.08, 0.17), (0.006, 0.008))
