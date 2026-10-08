import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import buildings as bd
import town_library as lib
from buildkit import V, block, emit, rod, lump, local_block, frame_block

tau = math.pi * 2.0
up = V(0.0, 0.0, 1.0)
kit.preview_root = os.path.join(kit.root, "assets", "previews", "town")
lib.register()


def facing(position, target):
    d = target - position
    return math.atan2(d.x, -d.y)


def side_frame(side, x0, x1, y0, y1):
    if side == "front":
        return (V(0.0, y0, 0.0), V(1.0, 0.0, 0.0), up, V(0.0, -1.0, 0.0))
    if side == "back":
        return (V(0.0, y1, 0.0), V(-1.0, 0.0, 0.0), up, V(0.0, 1.0, 0.0))
    if side == "left":
        return (V(x0, 0.0, 0.0), V(0.0, -1.0, 0.0), up, V(-1.0, 0.0, 0.0))
    return (V(x1, 0.0, 0.0), V(0.0, 1.0, 0.0), up, V(1.0, 0.0, 0.0))


def side_span(side, x0, x1, y0, y1):
    if side == "front":
        return x0, x1
    if side == "back":
        return -x1, -x0
    if side == "left":
        return -y1, -y0
    return y0, y1


def to_side(side, opening):
    a0, a1, z0, z1 = opening
    if side in ("back", "left"):
        return (-a1, -a0, z0, z1)
    return (a0, a1, z0, z1)


def atlas_uv(table, key, margin=1.0):
    return lib.region_uv(table, key, margin)


def quad_uv(region, flip=False):
    u0, u1, v0, v1 = region
    if flip:
        return [(u1, v0), (u0, v0), (u0, v1), (u1, v1)]
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def atlas_quad(part, name, corners, region, flip=False, smooth=False):
    geo = kit.Geo(list(corners), [(0, 1, 2, 3)], [quad_uv(region, flip)])
    emit(part, geo, name, None, "texture", smooth)


def atlas_panel(part, name, center, normal, width, height, region, roll=0.0, lift=0.002):
    n = normal.normalized()
    hint = up if abs(n.z) < 0.9 else V(0.0, 1.0, 0.0)
    upward = (hint - n * hint.dot(n)).normalized()
    right = upward.cross(n).normalized()
    if roll:
        c = math.cos(roll)
        s = math.sin(roll)
        right, upward = right * c + upward * s, upward * c - right * s
    origin = center + n * lift
    corners = [origin - right * (width * 0.5) - upward * (height * 0.5), origin + right * (width * 0.5) - upward * (height * 0.5), origin + right * (width * 0.5) + upward * (height * 0.5), origin - right * (width * 0.5) + upward * (height * 0.5)]
    atlas_quad(part, name, corners, region)


def atlas_box(part, name, matrix, x0, x1, y0, y1, z0, z1, front, other):
    points = [V(x0, y0, z0), V(x1, y0, z0), V(x1, y1, z0), V(x0, y1, z0), V(x0, y0, z1), V(x1, y0, z1), V(x1, y1, z1), V(x0, y1, z1)]
    faces = [((0, 3, 2, 1), other), ((4, 5, 6, 7), other), ((0, 1, 5, 4), front), ((2, 3, 7, 6), other), ((0, 4, 7, 3), other), ((1, 2, 6, 5), other)]
    uvs = []
    ordered = []
    for face, region in faces:
        u0, u1, v0, v1 = region
        ordered.append(face)
        uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    emit(part, kit.Geo(points, ordered, uvs), name, matrix, "texture")


def region_geo(geo, name, region_key, extent=None):
    region = kit.catalog[name]["regions"][region_key]
    reach = extent or max(max(abs(p.x), abs(p.y), abs(p.z)) for p in geo.points) * 2.0 + 1e-4
    span = (region[1] - region[0]) * 0.84
    offset = kit.rng.random()
    uvs = []
    for face in geo.faces:
        corners = [geo.points[i] for i in face]
        flat = kit.project(corners, kit.newell(corners), 1.0, (0.0, 0.0))
        uvs.append([(region[0] + (region[1] - region[0]) * 0.08 + min(max(u / reach + 0.5, 0.0), 1.0) * span, offset + v / reach * span) for u, v in flat])
    geo.uvs = uvs
    return geo


def painted_box(part, name, region_key, matrix, x0, x1, y0, y1, z0, z1, bevel=0.0):
    bd.region_box(part, name, region_key, matrix, x0, x1, y0, y1, z0, z1, bevel)


def col(b, surface, tag, x0, x1, y0, y1, z0, z1):
    b.col(surface, tag, V(min(x0, x1), min(y0, y1), min(z0, z1)), V(max(x0, x1), max(y0, y1), max(z0, z1)))


def slanted_cols(b, surface, tag, p0, p1, thickness, z0, z1, steps=3):
    for index in range(steps):
        a = p0.lerp(p1, index / steps)
        c = p0.lerp(p1, (index + 1) / steps)
        pad = thickness * 0.5
        b.col(surface, tag, V(min(a.x, c.x) - pad, min(a.y, c.y) - pad, z0), V(max(a.x, c.x) + pad, max(a.y, c.y) + pad, z1))


def opening_block(b, surface, tag, frame, opening, wall_t, t_out=0.0):
    a0, a1, z0, z1 = opening
    low, high = kit.box_between(kit.frame_point(frame, a0, z0, t_out - wall_t), kit.frame_point(frame, a1, z1, t_out))
    b.col(surface, tag, low, high)


def floor_cols(b, surface, tag, x0, x1, y0, y1, z0, z1, holes=()):
    pieces = [(x0, x1, y0, y1)]
    for hx0, hx1, hy0, hy1 in holes:
        cut = []
        for px0, px1, py0, py1 in pieces:
            if hx1 <= px0 or hx0 >= px1 or hy1 <= py0 or hy0 >= py1:
                cut.append((px0, px1, py0, py1))
                continue
            if hy0 > py0:
                cut.append((px0, px1, py0, hy0))
            if hy1 < py1:
                cut.append((px0, px1, hy1, py1))
            if hx0 > px0:
                cut.append((px0, hx0, max(py0, hy0), min(py1, hy1)))
            if hx1 < px1:
                cut.append((hx1, px1, max(py0, hy0), min(py1, hy1)))
        pieces = cut
    for px0, px1, py0, py1 in pieces:
        col(b, surface, tag, px0, px1, py0, py1, z0, z1)


def scatter_light(region, avoid, count, size_range, rng_local, aspect=(0.6, 1.2), bias=None, points=12, attempts=40, rough=0.34):
    a0, a1, b0, b1 = region
    patches = []
    taken = [kit.polygon_bounds(p) for p in avoid]
    for number in range(count):
        for attempt in range(attempts):
            rx = rng_local.uniform(*size_range)
            ry = rx * rng_local.uniform(*aspect)
            if a1 - a0 < rx * 2.9 or b1 - b0 < ry * 2.9:
                break
            cx = rng_local.uniform(a0 + rx * 1.4, a1 - rx * 1.4)
            cy = bias(rng_local) if bias is not None else rng_local.uniform(b0 + ry * 1.4, b1 - ry * 1.4)
            cy = min(max(cy, b0 + ry * 1.4), b1 - ry * 1.4)
            shape = kit.blob(cx, cy, rx, ry, rng_local, points, rough)
            bounds = kit.polygon_bounds(shape)
            if bounds[0] < a0 + 0.03 or bounds[1] > a1 - 0.03 or bounds[2] < b0 + 0.03 or bounds[3] > b1 - 0.03:
                continue
            if any(kit.overlaps(bounds, other, 0.06) for other in taken):
                continue
            patches.append(shape)
            taken.append(bounds)
            break
    return patches


def paper_skin(part, frame, a_low, a_high, z0, z1, openings, rng, patches=2, peels=1, name="wallpaper_faded", thickness=0.005, avoid=()):
    inward = (frame[0], -frame[1], frame[2], -frame[3])
    notches = [(-o[1], -o[0], o[3]) for o in openings if o[2] <= z0 + 1e-6]
    holes = [kit.rect(-o[1], -o[0], o[2], o[3]) for o in openings if o[2] > z0 + 1e-6]
    outline = kit.notched(-a_high, -a_low, z0, z1, notches)
    blocked = holes + [kit.rect(n0 - 0.05, n1 + 0.05, z0, top + 0.05) for n0, n1, top in notches] + [kit.rect(-r[1], -r[0], r[2], r[3]) for r in avoid]
    blobs = scatter_light((-a_high + 0.04, -a_low - 0.04, z0 + 0.3, z1 - 0.04), blocked, patches, (0.15, 0.45), rng, (0.8, 1.8), None, 11)
    kit.skin(part, name, inward, outline, holes + blobs, thickness, 0.0, False)
    for shape in blobs[:peels]:
        bounds = kit.polygon_bounds(shape)
        bd.paper_peel(part, (inward[0] + inward[3] * thickness, inward[1], inward[2], inward[3]), bounds[0] + 0.02, bounds[2] + 0.02, max(0.12, (bounds[1] - bounds[0]) * 0.7), min(0.7, bounds[3] - bounds[2] + 0.25), rng)


def plaster_skin(part, frame, a_low, a_high, z0, z1, openings, rng, patches=2, avoid=(), name="plaster_interior", thickness=0.015):
    inward = (frame[0], -frame[1], frame[2], -frame[3])
    notches = [(-o[1], -o[0], o[3]) for o in openings if o[2] <= z0 + 1e-6]
    holes = [kit.rect(-o[1], -o[0], o[2], o[3]) for o in openings if o[2] > z0 + 1e-6]
    outline = kit.notched(-a_high, -a_low, z0, z1, notches)
    blocked = holes + [kit.rect(n0 - 0.05, n1 + 0.05, z0, top + 0.05) for n0, n1, top in notches] + [kit.rect(-r[1], -r[0], r[2], r[3]) for r in avoid]
    blobs = scatter_light((-a_high + 0.04, -a_low - 0.04, z0 + 0.06, z1 - 0.06), blocked, patches, (0.15, 0.42), rng, (0.6, 1.3), None, 10)
    kit.skin(part, name, inward, outline, holes + blobs, thickness)


def ceiling_skin(part, z, x0, x1, y0, y1, rng, patches=1, holes=(), name="plaster_interior", thickness=0.02):
    frame = bd.ceiling_frame(z)
    blocked = [kit.rect(h[0], h[1], -h[3], -h[2]) for h in holes]
    blobs = scatter_light((x0 + 0.1, x1 - 0.1, -y1 + 0.1, -y0 - 0.1), blocked, patches, (0.18, 0.42), rng, (0.6, 1.4), None, 12, 40, 0.55)
    kit.skin(part, name, frame, kit.rect(x0, x1, -y1, -y0), blocked + blobs, thickness)
    for shape in blobs:
        a0, a1, b0, b1 = kit.polygon_bounds(shape)
        bd.laths(part, V(0.0, 0.0, z + 0.008), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), a0 - 0.05, a1 + 0.05, -b1 - 0.02, -b0 + 0.02, rng, "timber_planks_weathered", 0.032, 0.03, 0.008, 0.3)


def render_skin(part, frame, a0, a1, z_top, openings, rng, patches, name="render_white", thickness=0.02, big=1, low=(0.35, 0.6), top_loss=0.0):
    doors = sorted(o for o in openings if o[2] <= low[1] + 0.05)
    holes = [kit.rect(o[0], o[1], o[2], o[3]) for o in openings if o[2] > low[1] + 0.05]
    bottom = [(a0, rng.uniform(*low), 0)]
    a = a0 + rng.uniform(0.3, 0.7)
    while a < a1 - 0.3:
        if not any(d[0] - 0.2 < a < d[1] + 0.2 for d in doors):
            bottom.append((a, rng.uniform(*low), 0))
        a += rng.uniform(0.3, 0.7)
    bottom.append((a1, rng.uniform(*low), 0))
    for d in doors:
        bottom += [(d[0], low[0], 0), (d[0], d[3], 1), (d[1], d[3], 2), (d[1], low[0], 3)]
    bottom.sort(key=lambda p: (p[0], p[2]))
    outline = [(p[0], p[1]) for p in bottom] + [(a1, z_top)]
    if top_loss > 0.0:
        edge = kit.wander(rng)
        a = a1 - rng.uniform(0.15, 0.35)
        while a > a0 + 0.2:
            dip = z_top - top_loss * edge(a * 1.7) + rng.uniform(-0.03, 0.03)
            heads = [o[3] + 0.12 for o in openings if o[0] - 0.45 < a < o[1] + 0.45]
            outline.append((a, min(z_top, max([dip] + heads))))
            a -= rng.uniform(0.15, 0.35)
    outline.append((a0, z_top))
    blocked = holes + [kit.rect(d[0] - 0.08, d[1] + 0.08, low[0], d[3] + 0.08) for d in doors]
    region = (a0 + 0.06, a1 - 0.06, low[1] + 0.1, z_top - top_loss - 0.1)
    sink = lambda r: region[2] + (region[3] - region[2]) * r.random() ** 1.9
    blobs = scatter_light(region, blocked, big, (0.5, 1.0), rng, (0.5, 0.9), sink, 14)
    blobs += scatter_light(region, blocked + blobs, patches, (0.12, 0.45), rng, (0.45, 1.5), sink, 11)
    kit.skin(part, name, frame, outline, holes + blobs, thickness)
    return blobs


def chips(part, name, x0, x1, y0, y1, z, count, rng, size_range=(0.03, 0.12), thick=(0.006, 0.02), tilt=0.25):
    for index in range(count):
        s = rng.uniform(*size_range)
        position = V(rng.uniform(x0, x1), rng.uniform(y0, y1), z)
        polygon = kit.blob(0.0, 0.0, s, s * rng.uniform(0.5, 1.0), rng, 5, 0.3)
        t = rng.uniform(*thick)
        matrix = kit.Matrix.Translation(position + V(0.0, 0.0, t * 0.5)) @ kit.Matrix.Rotation(rng.uniform(0.0, tau), 4, 'Z') @ kit.Matrix.Rotation(rng.uniform(-tilt, tilt), 4, 'X') @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X')
        kit.prism(part, name, matrix, polygon, -t * 0.5, t * 0.5)


def bands(a_low, a_high, z0, z1, openings, pad=0.0):
    cuts = sorted(set([a_low, a_high] + [c for o in openings for c in (o[0] - pad, o[1] + pad) if a_low < c < a_high]))
    pieces = []
    for c0, c1 in zip(cuts[:-1], cuts[1:]):
        middle = (c0 + c1) * 0.5
        blocked = sorted((o[2] - pad, o[3] + pad) for o in openings if o[0] - pad <= middle <= o[1] + pad)
        start = z0
        for lo, hi in blocked:
            if lo > start + 0.01:
                pieces.append((c0, c1, start, min(lo, z1)))
            start = max(start, hi)
        if start < z1 - 0.01:
            pieces.append((c0, c1, start, z1))
    return [p for p in pieces if p[1] - p[0] > 0.02 and p[3] - p[2] > 0.02]


def wall_finish(part, side, finish, x0, x1, y0, y1, z0, z1, openings, rng, avoid=()):
    frame = side_frame(side, x0, x1, y0, y1)
    a_low, a_high = side_span(side, x0, x1, y0, y1)
    local = [to_side(side, o) for o in openings]
    local_avoid = [to_side(side, (r[0], r[1], r[2], r[3])) for r in avoid]
    kind = finish[0]
    if kind == "bare":
        return
    if kind == "plaster":
        plaster_skin(part, frame, a_low, a_high, z0, z1, local, rng, finish[1] if len(finish) > 1 else 2, local_avoid, finish[2] if len(finish) > 2 else "plaster_interior")
    elif kind == "paper":
        paper_skin(part, frame, a_low, a_high, z0, z1, local, rng, finish[2] if len(finish) > 2 else 2, finish[3] if len(finish) > 3 else 1, finish[1], 0.005, local_avoid)
    elif kind in ("tiles", "panel"):
        height = finish[1]
        name = finish[2]
        for c0, c1, b0, b1 in bands(a_low, a_high, z0, z0 + height, local):
            if kind == "tiles":
                frame_block(part, name, frame, c0, c1, b0, b1, 0.0, 0.012, 0.0, "world")
            else:
                frame_block(part, name, frame, c0, c1, b0, b1, 0.0, 0.016, 0.0, "board")
                if b1 >= z0 + height - 0.01:
                    frame_block(part, name, frame, c0, c1, b1 - 0.05, b1, 0.016, 0.036, 0.004, "board")
        above = finish[3] if len(finish) > 3 else ("plaster",)
        wall_finish(part, side, above, x0, x1, y0, y1, z0 + height, z1, [(o[0], o[1], max(o[2], z0 + height), o[3]) for o in openings if o[3] > z0 + height + 0.02], rng, avoid)


def skirting(part, side, x0, x1, y0, y1, z0, openings, name="painted_wood_white", height=0.2, depth=0.022, lift=0.012, bevel=0.003):
    frame = side_frame(side, x0, x1, y0, y1)
    a_low, a_high = side_span(side, x0, x1, y0, y1)
    doors = sorted(to_side(side, o) for o in openings if o[2] <= z0 + 0.05)
    for c0, c1, b0, b1 in bands(a_low, a_high, z0, z0 + height, doors, 0.05):
        frame_block(part, name, frame, c0, c1, b0, b1, lift, lift + depth, bevel, "board")


def rail(part, side, x0, x1, y0, y1, z, openings, name="timber_beam", height=0.05, depth=0.03, lift=0.012):
    frame = side_frame(side, x0, x1, y0, y1)
    a_low, a_high = side_span(side, x0, x1, y0, y1)
    blocked = sorted(to_side(side, o) for o in openings if o[2] <= z + 0.02 <= o[3])
    for c0, c1, b0, b1 in bands(a_low, a_high, z - height * 0.5, z + height * 0.5, blocked, 0.04):
        frame_block(part, name, frame, c0, c1, b0, b1, lift, lift + depth, 0.004)


def room(parts, rng, x0, x1, y0, y1, z0, z1, walls, openings=None, skirt="painted_wood_white", picture_rail=None, ceiling=True, ceiling_patches=2, ceiling_holes=(), avoid=None, chip_count=14, skirt_bevel=0.003):
    interior = parts["interior"]
    openings = openings or {}
    avoid = avoid or {}
    for side in ("front", "back", "left", "right"):
        finish = walls.get(side)
        if finish is None:
            continue
        holes = openings.get(side, [])
        wall_finish(interior, side, finish, x0, x1, y0, y1, z0, z1, holes, rng, avoid.get(side, ()))
        if skirt:
            skirting(interior, side, x0, x1, y0, y1, z0, holes, skirt, 0.2, 0.022, 0.012, skirt_bevel)
        if picture_rail:
            rail(interior, side, x0, x1, y0, y1, picture_rail, holes)
    if ceiling:
        ceiling_skin(interior, z1 + 0.02, x0, x1, y0, y1, rng, ceiling_patches, ceiling_holes)
    if chip_count and "debris" in parts:
        chips(parts["debris"], "plaster_interior", x0 + 0.05, x1 - 0.05, y0 + 0.05, y0 + 0.4, z0, chip_count // 2, rng)
        chips(parts["debris"], "plaster_interior", x0 + 0.05, x0 + 0.4, y0 + 0.4, y1 - 0.05, z0, chip_count // 2, rng)


def tile_floor(part, name, x0, x1, y0, y1, z, thickness=0.03):
    block(part, name, V(x0, y0, z - thickness), V(x1, y1, z), 0.0, "world")


def board_floor(part, x0, x1, y0, y1, z, rng, along="y", holes=(), name="floorboards", warp=0.03, ragged=0.1, width_range=(0.13, 0.19), splits=(0.4, 0.7)):
    kit.floor_boards(part, name, x0, x1, y0, y1, z, along, rng, width_range=width_range, joints=[x0 + (x1 - x0) * t for t in splits] if along == "x" else [y0 + (y1 - y0) * t for t in splits], holes=holes, ragged=ragged, warp=warp)


def door_frame_light(part, paint, frame, a0, a1, b0, b1, depth, fw=0.07, fd=0.11):
    frame_block(part, paint, frame, a0, a0 + fw, b0, b1, depth, depth + fd, 0.0, "board")
    frame_block(part, paint, frame, a1 - fw, a1, b0, b1, depth, depth + fd, 0.0, "board")
    frame_block(part, paint, frame, a0, a1, b1 - fw, b1, depth, depth + fd, 0.0, "board")
    return a0 + fw, a1 - fw, b1 - fw


def door_leaf_light(part, paint, frame, hinge_a, direction, d_axis, b0, height, width, angle, rng, style="panel", hang=0.0, iron="rusty_metal"):
    thick = 0.045
    base = kit.frame_matrix(frame) @ kit.Matrix.Translation(V(hinge_a, d_axis, 0.0))
    swing = kit.Matrix.Rotation(direction * math.radians(angle), 4, 'Z')
    pivot = V(0.0, 0.0, b0 + height - 0.2)
    sag = kit.Matrix.Translation(pivot) @ kit.Matrix.Rotation(-direction * math.radians(hang), 4, 'Y') @ kit.Matrix.Translation(-pivot)
    matrix = base @ swing @ sag
    x0, x1 = (0.0, width) if direction > 0 else (-width, 0.0)
    b1 = b0 + height
    if style == "ledged":
        count = max(4, int(round(width / 0.15)))
        for index in range(count):
            a = x0 + width * index / count + 0.002
            b = x0 + width * (index + 1) / count - 0.002
            local_block(part, paint, matrix, a, b, 0.0, 0.028, b0 + rng.uniform(0.0, 0.02), b1 - rng.uniform(0.0, 0.01), 0.0, "board")
        levels = (b0 + 0.18, (b0 + b1) * 0.5, b1 - 0.18)
        for z in levels:
            local_block(part, paint, matrix, x0 + 0.04, x1 - 0.04, 0.028, thick, z - 0.07, z + 0.07, 0.0, "board")
        for z_low, z_high in ((levels[0], levels[1]), (levels[1], levels[2])):
            start = V(x0 + 0.08 if direction > 0 else x1 - 0.08, 0.0, z_low + 0.07)
            end = V(x1 - 0.08 if direction > 0 else x0 + 0.08, 0.0, z_high - 0.07)
            forward = (end - start).normalized()
            emit(part, kit.geo_box((end - start).length, 0.11, 0.017), paint, matrix @ kit.place((start + end) * 0.5 + V(0.0, 0.0365, 0.0), forward, V(0.0, 1.0, 0.0)), "board")
        for z in (levels[0], levels[2]):
            local_block(part, iron, matrix, x0 + (0.0 if direction > 0 else width * 0.45), x0 + (width * 0.55 if direction > 0 else width), -0.005, 0.0, z - 0.022, z + 0.022)
        local_block(part, iron, matrix, (x1 - 0.1) if direction > 0 else (x0 + 0.05), (x1 - 0.05) if direction > 0 else (x0 + 0.1), -0.02, 0.0, b0 + 1.0, b0 + 1.05)
        return
    stile = 0.11
    local_block(part, paint, matrix, x0, x0 + stile, 0.0, thick, b0, b1, 0.0, "board")
    local_block(part, paint, matrix, x1 - stile, x1, 0.0, thick, b0, b1, 0.0, "board")
    rails = [(b0, b0 + 0.22), (b0 + 0.95, b0 + 1.12), (b1 - 0.13, b1)]
    for z0, z1 in rails:
        local_block(part, paint, matrix, x0 + stile, x1 - stile, 0.0, thick, z0, z1, 0.0, "board")
    muntin = (x0 + x1) * 0.5
    local_block(part, paint, matrix, muntin - 0.05, muntin + 0.05, 0.0, thick, rails[0][1], rails[2][0], 0.0, "board")
    for (z0, z1), (z2, z3) in zip(rails[:-1], rails[1:]):
        for px0, px1 in ((x0 + stile, muntin - 0.05), (muntin + 0.05, x1 - stile)):
            if rng.random() < 0.12:
                continue
            local_block(part, paint, matrix, px0, px1, thick * 0.3, thick * 0.7, z1, z2, 0.0, "board")
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.02, 0.0), (0.022, 0.012), (0.0, 0.022)], 8), "town_brass", matrix @ kit.Matrix.Translation(V(x1 - 0.12 if direction > 0 else x0 + 0.12, 0.0, b0 + 1.0)) @ kit.Matrix.Rotation(math.pi * 0.5, 4, 'X'), "given", True)


def door_unit(joinery, frame, a0, a1, z0, height, wall_t, paint, rng, hinge="low", angle=90.0, style="panel", leaf=True, depth=0.0, jamb=0.06, hang=0.0, frame_paint=None):
    frame_paint = frame_paint or paint
    ja0, ja1, jtop = door_frame_light(joinery, frame_paint, frame, a0, a1, z0, z0 + height, depth, jamb, wall_t)
    if not leaf:
        return ja0, ja1, jtop
    width = ja1 - ja0 - 0.01
    d_axis = depth + wall_t * 0.5 - 0.0225
    if hinge == "low":
        door_leaf_light(joinery, paint, frame, ja0 + 0.005, 1.0, d_axis, z0 + 0.012, jtop - z0 - 0.02, width, angle, rng, style, hang)
    else:
        door_leaf_light(joinery, paint, frame, ja1 - 0.005, -1.0, d_axis, z0 + 0.012, jtop - z0 - 0.02, width, angle, rng, style, hang)
    return ja0, ja1, jtop


def window_frame_light(part, paint, frame, a0, a1, b0, b1, depth, fw=0.065, fd=0.085):
    frame_block(part, paint, frame, a0, a0 + fw, b0, b1, depth, depth + fd, 0.0, "board")
    frame_block(part, paint, frame, a1 - fw, a1, b0, b1, depth, depth + fd, 0.0, "board")
    frame_block(part, paint, frame, a0 + fw, a1 - fw, b1 - fw, b1, depth, depth + fd, 0.0, "board")
    frame_block(part, paint, frame, a0 + fw, a1 - fw, b0, b0 + 0.07, depth - 0.035, depth + fd, 0.0, "board")
    return a0 + fw, a1 - fw, b0 + 0.07, b1 - fw


def leaf_light(part, paint, matrix, x0, x1, z0, z1, depth, cols, rows, rng, states, stile=0.045, bottom=0.06, bar=0.018):
    local_block(part, paint, matrix, x0, x0 + stile, 0.0, depth, z0, z1, 0.0, "board")
    local_block(part, paint, matrix, x1 - stile, x1, 0.0, depth, z0, z1, 0.0, "board")
    local_block(part, paint, matrix, x0 + stile, x1 - stile, 0.0, depth, z0, z0 + bottom, 0.0, "board")
    local_block(part, paint, matrix, x0 + stile, x1 - stile, 0.0, depth, z1 - stile, z1, 0.0, "board")
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
            kit.pane(part, matrix, px0, px1, pz0, pz1, depth * 0.45, states(), rng)


def sash_light(part, paint, frame, a0, a1, b0, b1, depth, rng, lift=0.0, whole=0.3, shard=0.3, cols=2, rows=2):
    ia0, ia1, ib0, ib1 = window_frame_light(part, paint, frame, a0, a1, b0, b1, depth, 0.07, 0.11)
    base = kit.frame_matrix(frame)
    choose = kit.glass_chooser(rng, whole, shard)
    middle = (ib0 + ib1) * 0.5
    upper = base @ kit.Matrix.Translation(V(0.0, depth + 0.012, 0.0))
    leaf_light(part, paint, upper, ia0 + 0.003, ia1 - 0.003, middle - 0.02, ib1 - 0.003, 0.04, cols, rows, rng, choose, 0.045, 0.035, 0.016)
    lower = base @ kit.Matrix.Translation(V(0.0, depth + 0.055, min(lift, middle - ib0 - 0.05)))
    leaf_light(part, paint, lower, ia0 + 0.003, ia1 - 0.003, ib0 + 0.003, middle + 0.02, 0.04, cols, rows, rng, choose, 0.045, 0.06, 0.016)


def casement_light(part, paint, frame, a0, a1, b0, b1, depth, rng, leaf_angles=None, whole=0.35, shard=0.3, rows=3):
    ia0, ia1, ib0, ib1 = window_frame_light(part, paint, frame, a0, a1, b0, b1, depth)
    base = kit.frame_matrix(frame)
    choose = kit.glass_chooser(rng, whole, shard)
    if ia1 - ia0 > 0.55:
        middle = (ia0 + ia1) * 0.5
        frame_block(part, paint, frame, middle - 0.028, middle + 0.028, ib0, ib1, depth, depth + 0.085, 0.0, "board")
        spans = [(ia0, middle - 0.028, True), (middle + 0.028, ia1, False)]
    else:
        spans = [(ia0, ia1, True)]
    angles = leaf_angles or [0.0] * len(spans)
    for (x0, x1, hinge_left), angle in zip(spans, angles):
        if angle is None:
            continue
        w = x1 - x0 - 0.006
        if hinge_left:
            matrix = base @ kit.Matrix.Translation(V(x0 + 0.003, depth + 0.012, 0.0)) @ kit.Matrix.Rotation(-math.radians(angle), 4, 'Z')
            leaf_light(part, paint, matrix, 0.0, w, ib0 + 0.004, ib1 - 0.004, 0.042, 1, rows, rng, choose)
        else:
            matrix = base @ kit.Matrix.Translation(V(x1 - 0.003, depth + 0.012, 0.0)) @ kit.Matrix.Rotation(math.radians(angle), 4, 'Z')
            leaf_light(part, paint, matrix, -w, 0.0, ib0 + 0.004, ib1 - 0.004, 0.042, 1, rows, rng, choose)


def fireplace_light(build, part, face_center, normal, rng, width=1.3, paint="painted_wood_white", tiles="kitchen_tiles", lit=False, grate=True):
    matrix = kit.frame_matrix(kit.plane(face_center, normal))
    hw = width * 0.5
    for sx in (-1.0, 1.0):
        local_block(part, paint, matrix, sx * hw, sx * (hw - 0.14), -0.05, 0.0, 0.0, 0.98, 0.0, "board")
        local_block(part, tiles, matrix, sx * (hw - 0.14), sx * 0.23, -0.018, 0.0, 0.0, 0.98)
    local_block(part, paint, matrix, -hw, hw, -0.06, 0.0, 0.98, 1.12, 0.0, "board")
    local_block(part, paint, matrix, -hw - 0.07, hw + 0.07, -0.18, 0.0, 1.12, 1.16, 0.006, "board")
    local_block(part, "rusty_metal", matrix, -0.23, 0.23, -0.03, 0.0, 0.64, 0.98)
    local_block(part, "rusty_metal", matrix, -0.23, -0.19, -0.03, 0.0, 0.0, 0.64)
    local_block(part, "rusty_metal", matrix, 0.19, 0.23, -0.03, 0.0, 0.0, 0.64)
    local_block(part, "soot", matrix, -0.19, 0.19, 0.26, 0.28, 0.0, 0.64)
    local_block(part, "soot", matrix, -0.19, 0.19, 0.0, 0.28, 0.64, 0.66)
    if grate:
        for index in range(3):
            x = -0.12 + index * 0.12
            rod(part, "rusty_metal", matrix @ V(x, -0.02, 0.1), matrix @ V(x, -0.02, 0.3), 0.007, 4)
        local_block(part, "rusty_metal", matrix, -0.19, 0.19, -0.03, 0.2, 0.08, 0.1)
        lump(part, "soot", matrix @ V(0.0, 0.1, 0.12), (0.14, 0.08, 0.03), rng, 0.3, 1)
    local_block(part, tiles, matrix, -hw, hw, -0.45, 0.0, 0.0, 0.02)
    if lit:
        build.light("fire", matrix @ V(0.0, 0.1, 0.25))
    return matrix


def gutter_light(part, gable, side, x0, x1, rng, sag=0.02, name="rusty_metal", radius=0.06, drop=0.05, broken_at=None):
    y = gable.origin_y + side * (gable.edge - 0.02)
    z = gable.eave_top - drop - radius
    profile = [(radius * math.cos(math.pi + math.pi * step / 4), radius * math.sin(math.pi + math.pi * step / 4)) for step in range(5)]
    profile += [((radius - 0.005) * math.cos(math.pi + math.pi * step / 4), (radius - 0.005) * math.sin(math.pi + math.pi * step / 4)) for step in range(4, -1, -1)]
    segments = [(x0, x1, 0.0)] if broken_at is None else [(x0, broken_at - 0.05, 0.0), (broken_at + 0.05, x1, 0.35)]
    for s0, s1, droop in segments:
        steps = max(2, int((s1 - s0) / 1.0))
        path = []
        for index in range(steps + 1):
            t = index / steps
            x = s0 + (s1 - s0) * t
            path.append(V(x, y + side * radius, z - sag * math.sin(math.pi * (x - x0) / max(x1 - x0, 1e-3)) - droop * t * t))
        emit(part, kit.geo_tube(path, profile, True, V(0.0, 0.0, 1.0)), name, None, "given", True)
        for p in path:
            bx = min(max(p.x, x0 + 0.02), x1 - 0.02)
            block(part, name, V(bx - 0.015, p.y - radius - 0.012, p.z - radius - 0.008), V(bx + 0.015, p.y + radius + 0.012, p.z - radius))
    return z


def chimney_light(part, name, cx, cy, sx, sy, z0, z1, rng, pots=2, pot_name="terracotta", flaunch="concrete"):
    z = z0
    course = 0
    long_x = sx >= sy
    while z < z1 - 0.12:
        h = rng.uniform(0.24, 0.32)
        if z + h > z1 - 0.12:
            h = z1 - z
        span = sx if long_x else sy
        split = (rng.uniform(-0.25, -0.1) if course % 2 == 0 else rng.uniform(0.1, 0.25)) * span
        for low, high in ((-span * 0.5, split), (split, span * 0.5)):
            if long_x:
                block(part, name, V(cx + low + 0.005, cy - sy * 0.5 - rng.uniform(0.0, 0.01), z + 0.006), V(cx + high - 0.005, cy + sy * 0.5 + rng.uniform(0.0, 0.01), z + h - 0.006))
            else:
                block(part, name, V(cx - sx * 0.5 - rng.uniform(0.0, 0.01), cy + low + 0.005, z + 0.006), V(cx + sx * 0.5 + rng.uniform(0.0, 0.01), cy + high - 0.005, z + h - 0.006))
        z += h
        course += 1
    block(part, name, V(cx - sx * 0.5 - 0.06, cy - sy * 0.5 - 0.06, z1), V(cx + sx * 0.5 + 0.06, cy + sy * 0.5 + 0.06, z1 + 0.12), 0.015)
    top = z1 + 0.12
    emit(part, kit.geo_frustum(sx * 0.5 + 0.02, sy * 0.5 + 0.02, sx * 0.3, sy * 0.3, 0.1), flaunch, kit.Matrix.Translation(V(cx, cy, top)), "box")
    for index in range(pots):
        f = (index + 0.5) / pots - 0.5
        position = V(cx + (sx * f * 0.9 if long_x else 0.0), cy + (0.0 if long_x else sy * f * 0.9), top + 0.04)
        height = rng.uniform(0.45, 0.65) * (0.45 if index == pots - 1 else 1.0)
        profile = [(0.11, 0.0), (0.1, height * 0.5), (0.085, height - 0.05), (0.1, height), (0.08, height), (0.075, 0.02)]
        emit(part, kit.geo_lathe(profile, 8, rng.uniform(0.0, tau)), pot_name, kit.Matrix.Translation(position), "given", True)
    return top


def stair_light(part, name, start, forward, width, rise, run, steps, rng, stringer=None, tread_thick=0.035, broken=()):
    side = V(-forward.y, forward.x, 0.0)
    going = run / steps
    step_rise = rise / steps
    for index in range(steps):
        top = start.z + step_rise * (index + 1)
        front = start + forward * (going * index)
        center = front + forward * (going * 0.5 + 0.015) + V(0.0, 0.0, top - start.z - tread_thick * 0.5)
        if index not in broken:
            emit(part, kit.geo_box(width, going + 0.03, tread_thick), name, kit.place(center, side, up), "board")
        riser_center = front + V(0.0, 0.0, top - start.z - step_rise * 0.5 - tread_thick * 0.5) + forward * 0.012
        emit(part, kit.geo_box(width - 0.02, 0.02, step_rise - tread_thick), name, kit.place(riser_center, side, up), "board")
    rail = stringer or name
    for sign in (-1.0, 1.0):
        a = start + side * (sign * (width * 0.5 + 0.02)) + V(0.0, 0.0, 0.05)
        b = a + forward * run + V(0.0, 0.0, rise)
        direction = (b - a).normalized()
        emit(part, kit.geo_box((b - a).length + 0.1, 0.04, 0.22), rail, kit.place((a + b) * 0.5, direction, up - direction * up.dot(direction)), "board")


def ridge_light(part, gable, x0, x1, rng, name="terracotta", bed="concrete", radius=0.13, length=0.6):
    profile = [(radius * math.cos(math.pi * step / 4), radius * math.sin(math.pi * step / 4)) for step in range(5)]
    profile += [((radius - 0.018) * math.cos(math.pi * step / 4), (radius - 0.018) * math.sin(math.pi * step / 4)) for step in range(4, -1, -1)]
    x = x0
    while x < x1 - 0.05:
        end = min(x + length, x1)
        base = V(0.0, gable.origin_y, gable.ridge_top - 0.035 + rng.uniform(-0.004, 0.006))
        emit(part, kit.geo_tube([V(x, 0.0, 0.0) + base, V(min(end + 0.02, x1), 0.0, 0.0) + base], profile, True, up), name, None, "given", True)
        x = end
    kit.segmented(part, bed, V(x0, gable.origin_y, gable.ridge_top - 0.035), V(x1, gable.origin_y, gable.ridge_top - 0.035), 0.2, 0.03, up, 2.0, "box")


def downpipe_light(part, x, y_top, y_wall, z_top, z_bottom, rng, name="rusty_metal", radius=0.035, broken=0.0, lean=0.0):
    out = 1.0 if y_top > y_wall else -1.0
    y_pipe = y_wall + out * (radius + 0.03)
    bottom = z_bottom + broken
    path = [V(x, y_top, z_top), V(x, y_top, z_top - 0.12), V(x, y_pipe, z_top - 0.45), V(x, y_pipe, z_top - 0.6), V(x + lean, y_pipe, bottom)]
    emit(part, kit.geo_tube(path, kit.circle(radius, 6), True, V(1.0, 0.0, 0.0)), name, None, "given", True)
    z = z_top - 0.8
    while z > bottom + 0.3:
        block(part, name, V(x - 0.045, min(y_wall, y_pipe + out * radius), z), V(x + 0.045, max(y_wall, y_pipe + out * radius), z + 0.03))
        z -= rng.uniform(1.5, 1.9)
    if broken <= 0.0:
        emit(part, kit.geo_tube([V(x, y_pipe, bottom + 0.14), V(x, y_pipe, bottom + 0.05), V(x, y_pipe + out * 0.14, bottom + 0.02)], kit.circle(radius * 1.05, 6), True, V(1.0, 0.0, 0.0)), name, None, "given", True)


def ivy_light(part, start, wall_normal, rng, height, spread=0.6, branches=3, density=16.0, stem="timber_beam", leaf="foliage"):
    n = wall_normal.normalized()
    tangent = up.cross(n).normalized()
    for branch in range(branches):
        direction_x = rng.uniform(-spread, spread)
        reach = height * rng.uniform(0.5, 1.0)
        steps = max(3, int(reach / 0.35))
        path = [start + tangent * rng.uniform(-0.1, 0.1)]
        for index in range(1, steps + 1):
            t = index / steps
            path.append(start + V(0.0, 0.0, reach * t) + tangent * (direction_x * t + math.sin(t * 7.0 + branch) * 0.05) + n * 0.012)
        emit(part, kit.geo_tube(path, kit.circle(0.008 * rng.uniform(0.7, 1.3), 3), True, n), stem, None, "given", True)
        for index in range(int(reach * density)):
            t = rng.random()
            position = path[min(int(t * steps), steps - 1)].lerp(path[min(int(t * steps) + 1, steps)], (t * steps) % 1.0)
            position = position + tangent * rng.uniform(-0.08, 0.08) + V(0.0, 0.0, rng.uniform(-0.05, 0.05)) + n * rng.uniform(0.01, 0.06)
            kit.leaf_quad(part, position, n + V(0.0, 0.0, rng.uniform(0.2, 0.9)) + tangent * rng.uniform(-0.5, 0.5), up, rng.uniform(0.05, 0.1), rng, leaf)


def sarking(part, gable, side, x0, x1, holes=(), name="timber_planks_weathered", depth=0.025):
    spans = [(x0, x1, 0.0, gable.run)]
    for hx0, hx1, hd0, hd1, hs in holes:
        if hs != side:
            continue
        cut = []
        for sx0, sx1, sd0, sd1 in spans:
            if hx1 <= sx0 or hx0 >= sx1 or hd1 <= sd0 or hd0 >= sd1:
                cut.append((sx0, sx1, sd0, sd1))
                continue
            if hd0 > sd0:
                cut.append((sx0, sx1, sd0, hd0))
            if hd1 < sd1:
                cut.append((sx0, sx1, hd1, sd1))
            if hx0 > sx0:
                cut.append((sx0, hx0, max(sd0, hd0), min(sd1, hd1)))
            if hx1 < sx1:
                cut.append((hx1, sx1, max(sd0, hd0), min(sd1, hd1)))
        spans = cut
    for sx0, sx1, sd0, sd1 in spans:
        kit.roof_slab(part, gable, side, sx0, sx1, name, depth, sd0, sd1)


def boards_over(joinery, frame, opening, rng, name="timber_planks_weathered", count=None, outward=0.025, gaps=0.3):
    a0, a1, z0, z1 = opening
    count = count or max(3, int((z1 - z0) / 0.22))
    for index in range(count):
        if rng.random() < gaps * 0.3:
            continue
        z = z0 + 0.1 + (z1 - z0 - 0.2) * index / max(count - 1, 1) + rng.uniform(-0.03, 0.03)
        center = kit.frame_point(frame, (a0 + a1) * 0.5 + rng.uniform(-0.04, 0.04), z, outward)
        along = frame[1]
        tilt = rng.uniform(-0.1, 0.1)
        direction = (along + up * tilt).normalized()
        emit(joinery, kit.geo_box(a1 - a0 + 0.24, 0.15 + rng.uniform(-0.02, 0.03), 0.022), name, kit.place(center, direction, frame[3]), "board")
        for end in (-1.0, 1.0):
            nail = center + direction * (end * ((a1 - a0) * 0.5 + 0.06)) + frame[3] * 0.012
            rod(joinery, "rusty_metal", nail, nail + frame[3] * 0.012, 0.006, 4)


def sash(b, parts, frame, opening, wall_t, rng, paint="painted_wood_white", depth=0.1, lift=0.0, whole=0.3, shard=0.3, cols=2, rows=2, render=None, sill="granite_ashlar", board=None, climbable=False, boarded=False, surface="glass", tag="window", lintel=None, inside_board="painted_wood_white"):
    shell = parts["shell"]
    joinery = parts["joinery"]
    a0, a1, z0, z1 = opening
    sash_light(joinery, paint, frame, a0, a1, z0, z1, depth, rng, lift, whole, shard, cols, rows)
    if sill:
        kit.sill_stone(shell, sill, frame, a0, a1, z0, min(depth + 0.04, wall_t), 0.05, 0.07, 0.06)
    if inside_board:
        frame_block(joinery, inside_board, frame, a0 - 0.04, a1 + 0.04, z0 - 0.03, z0 + 0.004, depth + 0.11, wall_t + 0.03, 0.004, "board")
    if render:
        bd.reveal_skin(shell, render, frame, opening, depth)
        frame_block(shell, render, frame, a0, a1, z0 - 0.002, z0 + 0.002, depth + 0.11, wall_t, 0.0)
    if lintel:
        kit.lintel_stone(shell, lintel, frame, a0, a1, z1, 0.2, 0.25, 0.015, 0.12)
    if boarded:
        boards_over(joinery, frame, opening, rng)
    if not climbable:
        opening_block(b, "wood" if boarded else surface, tag, frame, opening, wall_t)


def casement(b, parts, frame, opening, wall_t, rng, paint="painted_wood_white", depth=0.1, leaves=None, whole=0.35, shard=0.3, rows=2, sill="granite_ashlar", climbable=False, boarded=False, tag="window"):
    a0, a1, z0, z1 = opening
    casement_light(parts["joinery"], paint, frame, a0, a1, z0, z1, depth, rng, leaves, whole, shard, rows)
    if sill:
        kit.sill_stone(parts["shell"], sill, frame, a0, a1, z0, min(depth + 0.04, wall_t), 0.05, 0.07, 0.06)
    if boarded:
        boards_over(parts["joinery"], frame, opening, rng)
    if not climbable:
        opening_block(b, "wood" if boarded else "glass", tag, frame, opening, wall_t)


def architrave(shell, frame, opening, name="render_white", width=0.12, proud=0.025, head=0.16, keystone=False):
    a0, a1, z0, z1 = opening
    frame_block(shell, name, frame, a0 - width, a0, z0, z1 + head, -proud, 0.0, 0.006)
    frame_block(shell, name, frame, a1, a1 + width, z0, z1 + head, -proud, 0.0, 0.006)
    frame_block(shell, name, frame, a0 - width - 0.03, a1 + width + 0.03, z1, z1 + head, -proud - 0.015, 0.0, 0.006)
    frame_block(shell, name, frame, a0 - width - 0.06, a1 + width + 0.06, z1 + head, z1 + head + 0.05, -proud - 0.04, 0.0, 0.008)
    if keystone:
        middle = (a0 + a1) * 0.5
        frame_block(shell, name, frame, middle - 0.07, middle + 0.07, z1 - 0.02, z1 + head + 0.03, -proud - 0.03, 0.0, 0.006)


def stair_flight(b, parts, x0, x1, y_foot, z_foot, run, rise, steps, rng, direction=1.0, tread="floorboards", stringer="painted_wood_white", runner="town_carpet", rods="town_brass", surface="wood", tag="stair", broken=()):
    floors = parts["floors"]
    width = x1 - x0 - 0.08
    center_x = (x0 + x1) * 0.5
    start = V(center_x, y_foot, z_foot)
    forward = V(0.0, direction, 0.0)
    stair_light(floors, tread, start, forward, width, rise, run, steps, rng, stringer, 0.035, broken)
    going = run / steps
    step_rise = rise / steps
    if runner:
        for index in range(steps):
            if index in broken:
                continue
            top = z_foot + step_rise * (index + 1)
            front = y_foot + direction * going * index
            y_a = front + direction * 0.0
            y_b = front + direction * (going + 0.01)
            block(floors, runner, V(center_x - width * 0.32, min(y_a, y_b), top - 0.002), V(center_x + width * 0.32, max(y_a, y_b), top + 0.008), 0.0, "world")
            riser_y = front + direction * 0.002
            block(floors, runner, V(center_x - width * 0.32, riser_y - 0.006, top - step_rise + 0.008), V(center_x + width * 0.32, riser_y + 0.006, top), 0.0, "world")
            if rods and index > 0 and rng.random() > 0.2:
                rod(floors, rods, V(center_x - width * 0.36, front - direction * 0.014, top - step_rise + 0.016), V(center_x + width * 0.36, front - direction * 0.014, top - step_rise + 0.016), 0.006, 6)
    y_head = y_foot + direction * run
    low = V(x0, min(y_foot, y_head), z_foot)
    high = V(x1, max(y_foot, y_head), z_foot + rise)
    b.ramp("py" if direction > 0 else "ny", surface, tag, low, high)


def under_stair_panel(part, x, y_foot, z_foot, run, rise, direction, rng, paint="painted_wood_white", door=None, thickness=0.03, normal_sign=-1.0):
    frame = kit.plane(V(x, 0.0, 0.0), V(normal_sign, 0.0, 0.0))
    along = frame[1]
    y_head = y_foot + direction * run
    a_foot = (V(0.0, y_foot, 0.0)).dot(along)
    a_head = (V(0.0, y_head, 0.0)).dot(along)
    outline = [(a_foot, z_foot), (a_head, z_foot), (a_head, z_foot + rise - 0.18)]
    if rise > 0.5:
        outline = [(a_foot, z_foot), (a_head, z_foot), (a_head, z_foot + rise - 0.2), (a_foot, z_foot + 0.02)]
    holes = []
    kit.wall(part, paint, frame, outline, holes, thickness)
    if door:
        d0, d1, dz = door
        center_a = ((V(0.0, d0, 0.0)).dot(along) + (V(0.0, d1, 0.0)).dot(along)) * 0.5
        width = abs(d1 - d0)
        frame_block(part, paint, frame, center_a - width * 0.5, center_a + width * 0.5, z_foot + 0.05, z_foot + dz, -0.015, 0.0, 0.004, "board")
        frame_block(part, "town_brass", frame, center_a + width * 0.5 - 0.09, center_a + width * 0.5 - 0.06, z_foot + dz * 0.55, z_foot + dz * 0.55 + 0.04, -0.03, -0.015)


def chimney_breast(b, part, x_wall, inward, y0, y1, z0, z1, opening_width, opening_height, rng, name="plaster_interior", surface="rock", tag="breast", depth=0.4):
    x_face = x_wall + inward * depth
    xa = min(x_wall, x_face)
    xb = max(x_wall, x_face)
    middle = (y0 + y1) * 0.5
    half = opening_width * 0.5
    block(part, name, V(xa, y0, z0), V(xb, middle - half, z1), 0.0, "world")
    block(part, name, V(xa, middle + half, z0), V(xb, y1, z1), 0.0, "world")
    block(part, name, V(xa, middle - half, z0 + opening_height), V(xb, middle + half, z1), 0.0, "world")
    back = x_wall + inward * 0.06
    block(part, "soot", V(min(back, x_wall), middle - half, z0), V(max(back, x_wall), middle + half, z0 + opening_height), 0.0, "world")
    block(part, "soot", V(xa, middle - half - 0.01, z0), V(xb, middle - half, z0 + opening_height), 0.0, "world")
    block(part, "soot", V(xa, middle + half, z0), V(xb, middle + half + 0.01, z0 + opening_height), 0.0, "world")
    block(part, "soot", V(xa, middle - half, z0 + opening_height - 0.01), V(xb, middle + half, z0 + opening_height), 0.0, "world")
    col(b, surface, tag, xa, xb, y0, y1, z0, z1)
    return x_face


def slate_geo_light(gable, side, xa, xb, d0, length, thick, lift_butt, cell, tile, rng_local, broken=False, spin=0.0):
    cu0, cu1, cv0, cv1 = cell
    cx = (xa + xb) * 0.5
    cd = d0 + length * 0.5
    cosine = math.cos(spin)
    sine = math.sin(spin)
    upward = gable.upslope(side)

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
    face, face_uv = kit.oriented_face(tuple(range(count, 2 * count)), [uv(x, d) for x, d in outline], points, gable.normal(side))
    faces.append(face)
    uvs.append(face_uv)
    sliver = thick / tile
    for i in range(count):
        j = (i + 1) % count
        (xi, di), (xj, dj) = outline[i], outline[j]
        if abs(xj - xi) < 1e-4 or (di > d0 + length - 1e-6 and dj > d0 + length - 1e-6):
            continue
        expected = V(dj - di, 0.0, 0.0) + upward * (xi - xj)
        base = [uv(xi, di), uv(xj, dj), (uv(xj, dj)[0], uv(xj, dj)[1] + sliver), (uv(xi, di)[0], uv(xi, di)[1] + sliver)]
        face, face_uv = kit.oriented_face((i, j, count + j, count + i), base, points, expected)
        faces.append(face)
        uvs.append(face_uv)
    return kit.Geo(points, faces, uvs)


def slate_roof_light(part, gable, side, rng_local, moss=None, missing=None, slipped=None, name="slate_roof", moss_name="roof_moss", gauge=0.27, length=0.58, width=0.34, thick=0.008, gap=0.004, x0=None, x1=None, d_end=None):
    x0 = gable.x0 if x0 is None else x0
    x1 = gable.x1 if x1 is None else x1
    tile = kit.tile_of(name)
    cells = kit.catalog[name]["cells"]
    end = gable.run if d_end is None else d_end
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
            mid = (xa + xb) * 0.5
            if missing is not None and missing(mid, d):
                continue
            slip = slipped(mid, d) if slipped is not None else 0.0
            lift_butt = thick * (1.0 if course == 0 else 2.0) + rng_local.uniform(-0.0015, 0.0015)
            spin = rng_local.uniform(-0.012, 0.012) + (rng_local.uniform(-0.12, 0.12) if slip > 0.0 else 0.0)
            broken = rng_local.random() < 0.05
            cell = rng_local.choice(cells)
            chosen = moss_name if moss is not None and moss(mid, d) else name
            geo = slate_geo_light(gable, side, xa + gap * 0.5, xb - gap * 0.5, d - slip + rng_local.uniform(-0.004, 0.004), span, thick, lift_butt + (0.006 if slip > 0.0 else 0.0), cell, tile, rng_local, broken, spin)
            emit(part, geo, chosen, None, "texture")
            count += 1
        d += gauge
        course += 1
    return count


def terrace_roof(b, parts, x0, x1, gable, rng, moss=0.3, missing=0.01, holes=(), slipped=0.02, boards=True, surface="rock", gutters=True, broken_gutter=None, verge=True, sides=(-1.0, 1.0), gauge=0.27, length=0.58, width=0.34):
    roof = parts["roof"]
    moss_field = kit.smooth_noise(random.Random(int(rng.random() * 1000)), 5, 1.2)
    for side in sides:
        def lost(x, d, side=side):
            for hx0, hx1, hd0, hd1, hs in holes:
                if hs == side and hx0 < x < hx1 and hd0 < d < hd1:
                    return True
            return rng.random() < missing
        threshold = 0.55 - moss
        slate_roof_light(roof, gable, side, rng, lambda x, d, side=side: moss_field(V(x * 0.5, d * 0.7, 2.0 * side)) > threshold or (d < 0.5 and rng.random() < moss), lost, lambda x, d: rng.uniform(0.05, 0.15) if rng.random() < slipped else 0.0, gauge=gauge, length=length, width=width, x0=x0 + 0.03, x1=x1 - 0.03)
        if boards:
            sarking(roof, gable, side, x0, x1, holes)
            for hx0, hx1, hd0, hd1, hs in holes:
                if hs == side:
                    kit.roof_rafters(roof, gable, side, [hx0 + (hx1 - hx0) * t for t in (0.25, 0.8)], max(hd0 - 0.5, 0.0), min(hd1 + 0.5, gable.run), -0.03)
        if gutters:
            gutter_light(roof, gable, side, x0, x1, rng, 0.02, broken_at=broken_gutter if side > 0 else None)
    ridge_light(roof, gable, x0, x1, rng)
    if verge:
        for x_edge, sign in ((x0, 1.0), (x1, -1.0)):
            for side in sides:
                a = gable.point(side, x_edge + sign * 0.03, -0.02, 0.012)
                c = gable.point(side, x_edge + sign * 0.03, gable.run, 0.012)
                kit.member(roof, "concrete", a, c, 0.06, 0.03, gable.normal(side), 0.0, "box")
    for side in sides:
        if side < 0:
            b.ramp("py", surface, "roof", V(x0, gable.origin_y - gable.edge, gable.eave_top), V(x1, gable.origin_y, gable.ridge_top))
        else:
            b.ramp("ny", surface, "roof", V(x0, gable.origin_y, gable.eave_top), V(x1, gable.origin_y + gable.edge, gable.ridge_top))


def gable_cols_x(b, tag, x0, x1, gable, base, steps=4, surface="rock"):
    for index in range(steps):
        z0 = base + (gable.ridge_top - base) * index / steps
        z1 = base + (gable.ridge_top - base) * (index + 1) / steps
        reach = min(gable.half, (gable.ridge_top - z0) / gable.tan)
        if reach > 0.05:
            b.col(surface, tag, V(x0, gable.origin_y - reach, z0), V(x1, gable.origin_y + reach, z1))


def valley_outline(front, back, half_y, depth=0.05):
    return [(-half_y, -1.5), (half_y, -1.5), (half_y, back.under(half_y, depth)), (back.origin_y, back.under(back.origin_y, depth)), (0.0, front.under(0.0, depth)), (front.origin_y, front.under(front.origin_y, depth)), (-half_y, front.under(-half_y, depth))]


class YGable(kit.Gable):
    def __init__(self, y0, y1, half, overhang, eave_top, pitch_degrees, origin_x=0.0):
        kit.Gable.__init__(self, y0, y1, half, overhang, eave_top, pitch_degrees, 0.0)
        self.origin_x = origin_x

    def point(self, side, x, d, lift=0.0):
        native = V(x, side * (self.edge - d * self.cos), self.eave_top + d * self.sin) + V(0.0, side * self.sin, self.cos) * lift
        return V(self.origin_x - native.y, native.x, native.z)

    def normal(self, side):
        return V(-side * self.sin, 0.0, self.cos)

    def upslope(self, side):
        return V(side * self.cos, 0.0, self.sin)

    def height(self, x, depth=0.0):
        return self.ridge_top - abs(x - self.origin_x) * self.tan - depth / self.cos


def roof_slab_y(part, gable, side, x0, x1, name, depth=0.2, d0=0.0, d1=None):
    d1 = gable.run if d1 is None else d1
    tile = kit.tile_of(name)
    top = [gable.point(side, x0, d0), gable.point(side, x1, d0), gable.point(side, x1, d1), gable.point(side, x0, d1)]
    points = top + [p - gable.normal(side) * depth for p in top]
    flat_uv = [(x0 / tile, d0 / tile), (x1 / tile, d0 / tile), (x1 / tile, d1 / tile), (x0 / tile, d1 / tile)]
    along = V(0.0, 1.0, 0.0)
    faces = []
    uvs = []
    for face, face_uv, expected in (((0, 1, 2, 3), flat_uv, gable.normal(side)), ((4, 5, 6, 7), flat_uv, -gable.normal(side)), ((0, 1, 5, 4), [flat_uv[0], flat_uv[1], (flat_uv[1][0], flat_uv[1][1] - depth / tile), (flat_uv[0][0], flat_uv[0][1] - depth / tile)], -gable.upslope(side)), ((3, 2, 6, 7), [flat_uv[3], flat_uv[2], (flat_uv[2][0], flat_uv[2][1] + depth / tile), (flat_uv[3][0], flat_uv[3][1] + depth / tile)], gable.upslope(side)), ((0, 3, 7, 4), [flat_uv[0], flat_uv[3], (flat_uv[3][0] - depth / tile, flat_uv[3][1]), (flat_uv[0][0] - depth / tile, flat_uv[0][1])], -along), ((1, 2, 6, 5), [flat_uv[1], flat_uv[2], (flat_uv[2][0] + depth / tile, flat_uv[2][1]), (flat_uv[1][0] + depth / tile, flat_uv[1][1])], along)):
        oriented, oriented_uv = kit.oriented_face(face, face_uv, points, expected)
        faces.append(oriented)
        uvs.append(oriented_uv)
    emit(part, kit.Geo(points, faces, uvs), name, None, "texture")


def sarking_y(part, gable, side, x0, x1, holes=(), name="timber_planks_weathered", depth=0.025):
    spans = [(x0, x1, 0.0, gable.run)]
    for hx0, hx1, hd0, hd1, hs in holes:
        if hs != side:
            continue
        cut = []
        for sx0, sx1, sd0, sd1 in spans:
            if hx1 <= sx0 or hx0 >= sx1 or hd1 <= sd0 or hd0 >= sd1:
                cut.append((sx0, sx1, sd0, sd1))
                continue
            if hd0 > sd0:
                cut.append((sx0, sx1, sd0, hd0))
            if hd1 < sd1:
                cut.append((sx0, sx1, hd1, sd1))
            if hx0 > sx0:
                cut.append((sx0, hx0, max(sd0, hd0), min(sd1, hd1)))
            if hx1 < sx1:
                cut.append((hx1, sx1, max(sd0, hd0), min(sd1, hd1)))
        spans = cut
    for sx0, sx1, sd0, sd1 in spans:
        roof_slab_y(part, gable, side, sx0, sx1, name, depth, sd0, sd1)


def ygable_roof(b, parts, gable, rng, sides=(-1.0, 1.0), moss=0.35, missing=0.012, holes=(), slipped=0.03, gauge=0.33, length=0.7, width=0.48, ridge=True, verges=(True, True), surface="rock", gutters=True):
    roof = parts["roof"]
    moss_field = kit.smooth_noise(random.Random(int(rng.random() * 1000)), 5, 1.2)
    threshold = 0.55 - moss
    for side in sides:
        def lost(x, d, side=side):
            for hx0, hx1, hd0, hd1, hs in holes:
                if hs == side and hx0 < x < hx1 and hd0 < d < hd1:
                    return True
            return rng.random() < missing
        slate_roof_light(roof, gable, side, rng, lambda x, d, side=side: moss_field(V(x * 0.5, d * 0.7, 2.0 * side)) > threshold or (d < 0.5 and rng.random() < moss), lost, lambda x, d: rng.uniform(0.05, 0.15) if rng.random() < slipped else 0.0, gauge=gauge, length=length, width=width, x0=gable.x0 + 0.03, x1=gable.x1 - 0.03)
        sarking_y(roof, gable, side, gable.x0, gable.x1, holes)
        for hx0, hx1, hd0, hd1, hs in holes:
            if hs == side:
                kit.roof_rafters(roof, gable, side, [hx0 + (hx1 - hx0) * t for t in (0.25, 0.8)], max(hd0 - 0.5, 0.0), min(hd1 + 0.5, gable.run), -0.03)
        if gutters:
            radius = 0.06
            x = gable.origin_x - side * (gable.edge - 0.02 + radius)
            z = gable.eave_top - 0.05 - radius
            profile = [(radius * math.cos(math.pi + math.pi * step / 4), radius * math.sin(math.pi + math.pi * step / 4)) for step in range(5)]
            profile += [((radius - 0.005) * math.cos(math.pi + math.pi * step / 4), (radius - 0.005) * math.sin(math.pi + math.pi * step / 4)) for step in range(4, -1, -1)]
            path = [V(x, gable.x0 + (gable.x1 - gable.x0) * t, z - 0.02 * math.sin(math.pi * t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
            emit(roof, kit.geo_tube(path, profile, True, up), "rusty_metal", None, "given", True)
            y = gable.x0 + 0.3
            while y < gable.x1 - 0.2:
                block(roof, "rusty_metal", V(x - radius - 0.012, y - 0.015, z - radius - 0.008), V(x + radius + 0.012, y + 0.015, z - radius))
                y += rng.uniform(0.9, 1.2)
    if ridge:
        radius = 0.13
        profile = [(radius * math.cos(math.pi * step / 4), radius * math.sin(math.pi * step / 4)) for step in range(5)]
        profile += [((radius - 0.018) * math.cos(math.pi * step / 4), (radius - 0.018) * math.sin(math.pi * step / 4)) for step in range(4, -1, -1)]
        y = gable.x0
        while y < gable.x1 - 0.05:
            end = min(y + 0.6, gable.x1)
            z = gable.ridge_top - 0.035 + rng.uniform(-0.004, 0.006)
            emit(roof, kit.geo_tube([V(gable.origin_x, y, z), V(gable.origin_x, min(end + 0.02, gable.x1), z)], profile, True, up), "terracotta", None, "given", True)
            y = end
    for flag, x_edge, sign in ((verges[0], gable.x0, 1.0), (verges[1], gable.x1, -1.0)):
        if flag:
            for side in sides:
                kit.member(roof, "concrete", gable.point(side, x_edge + sign * 0.03, -0.02, 0.012), gable.point(side, x_edge + sign * 0.03, gable.run, 0.012), 0.06, 0.03, gable.normal(side), 0.0, "box")
    for side in sides:
        if side > 0:
            b.ramp("px", surface, "roof", V(gable.origin_x - gable.edge, gable.x0, gable.eave_top), V(gable.origin_x, gable.x1, gable.ridge_top))
        else:
            b.ramp("nx", surface, "roof", V(gable.origin_x, gable.x0, gable.eave_top), V(gable.origin_x + gable.edge, gable.x1, gable.ridge_top))


def lancet(a0, a1, z0, spring, apex, steps=4):
    middle = (a0 + a1) * 0.5
    width = a1 - a0
    rise = apex - spring
    points = [(a0, z0), (a1, z0), (a1, spring)]
    for k in range(1, steps):
        theta = math.radians(60.0) * k / steps
        points.append((a0 + width * math.cos(theta), spring + rise * math.sin(theta) / math.sin(math.radians(60.0))))
    points.append((middle, apex))
    for k in range(steps - 1, 0, -1):
        theta = math.radians(60.0) * k / steps
        points.append((a1 - width * math.cos(theta), spring + rise * math.sin(theta) / math.sin(math.radians(60.0))))
    points.append((a0, spring))
    return points


def offset_lancet(a0, a1, z0, spring, apex, pad, steps=4):
    return lancet(a0 - pad, a1 + pad, z0 - pad, spring, apex + pad * 1.6, steps)


def inner_skin(part, frame, wall_t, outline, holes, rng, patches=2, name="plaster_interior", thickness=0.015, region=None):
    origin = frame[0] - frame[3] * wall_t
    inner = kit.plane(origin, -frame[3])
    flip = lambda polygon: [(-a, z) for a, z in reversed(polygon)]
    inner_outline = flip(outline)
    inner_holes = [flip(h) for h in holes]
    blobs = []
    if patches:
        bounds = kit.polygon_bounds(inner_outline)
        area = region or (bounds[0] + 0.1, bounds[1] - 0.1, bounds[2] + 0.3, bounds[3] - 0.3)
        blobs = scatter_light(area, inner_holes, patches, (0.2, 0.55), rng, (0.6, 1.3), None, 10)
    kit.skin(part, name, inner, inner_outline, inner_holes + blobs, thickness)
    return inner


def stack(b, part, cx, cy, sx, sy, z0, z1, rng, pots=2, name="granite_ashlar"):
    top = chimney_light(part, name, cx, cy, sx, sy, z0, z1, rng, pots)
    b.col("rock", "chimney", V(cx - sx * 0.5, cy - sy * 0.5, z0), V(cx + sx * 0.5, cy + sy * 0.5, z1 + 0.12))
    return top


def weeds_line(part, a, b_point, rng, count, height=(0.15, 0.45)):
    for index in range(count):
        p = a.lerp(b_point, rng.random()) + V(rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0.0)
        if rng.random() < 0.15:
            kit.nettle(part, p, rng, (0.3, 0.7))
        else:
            kit.grass_tuft(part, p, rng, height, (4, 9), 0.06)


def partition(b, parts, origin, normal, a0, a1, z0, z1, thickness, doors, tag, surface="wood", name="plaster_interior"):
    frame = kit.plane(origin, normal)
    notches = sorted((d[0], d[1], d[3]) for d in doors)
    kit.wall(parts["interior"], name, frame, kit.notched(a0, a1, z0, z1, notches) if notches else kit.rect(a0, a1, z0, z1), [], thickness)
    kit.wall_boxes(b, surface, tag, frame, a0, a1, z0, z1, thickness, doors)
    return frame


def quoins_light(part, name, corner, ua, ub, z0, z1, rng, protrude=0.04, joint=0.012):
    z = z0
    course = 0
    while z < z1 - 0.1:
        h = rng.uniform(0.26, 0.34)
        if z + h > z1 - 0.12:
            h = z1 - z
        la = rng.uniform(0.42, 0.6) if course % 2 == 0 else rng.uniform(0.2, 0.3)
        lb = rng.uniform(0.2, 0.3) if course % 2 == 0 else rng.uniform(0.42, 0.6)
        p = protrude * rng.uniform(0.75, 1.2)
        corners = [corner + ua * s + ub * t for s in (-p, la) for t in (-p, lb)]
        block(part, name, V(min(q.x for q in corners), min(q.y for q in corners), z + joint * 0.5), V(max(q.x for q in corners), max(q.y for q in corners), z + h - joint * 0.5))
        z += h
        course += 1


def corrugated_slope(part, gable, side, y0, y1, rng, sheet=0.9, missing=0.05, glazed=(), name="corrugated_rusty", waves=6.0, overhang=0.12, glass="glass_dirty"):
    across = V(0.0, -side, 0.0)
    along = gable.upslope(side)
    length = gable.run + overhang
    y = y0
    while y < y1 - 0.05:
        w = min(sheet, y1 - y)
        middle = y + w * 0.5
        if any(g0 < middle < g1 for g0, g1 in glazed):
            center = gable.point(side, middle, length * 0.5 - overhang, 0.014)
            emit(part, kit.geo_box(w + 0.04, length, 0.006), glass, kit.place(center, V(0.0, 1.0, 0.0), gable.normal(side)), "box")
            y += w
            continue
        if rng.random() < missing:
            y += w
            continue
        start = y if across.y > 0.0 else y + w + 0.04
        origin = gable.point(side, start, -overhang, 0.012 + rng.uniform(0.0, 0.006))
        kit.corrugated_sheet(part, origin, across, along, w + 0.04, length, rng, name, 0.012, waves, 4, 0.0015, rng.uniform(0.0, 0.03), 1, rng.uniform(0.0, 0.1), rng.uniform(-0.02, 0.02))
        y += w


def corrugated_ygable(b, parts, gable, rng, sides=(-1.0, 1.0), sheet=0.9, missing=0.05, glazed=None, surface="metal", purlins=3, name="corrugated_rusty"):
    roof = parts["roof"]
    for side in sides:
        corrugated_slope(roof, gable, side, gable.x0, gable.x1, rng, sheet, missing, (glazed or {}).get(side, ()), name)
        for k in range(purlins):
            d = gable.run * (k + 0.5) / purlins
            kit.member(roof, "rusty_metal", gable.point(side, gable.x0 + 0.05, d, -0.06), gable.point(side, gable.x1 - 0.05, d, -0.06), 0.06, 0.1, gable.normal(side), 0.0, "box")
        if side > 0:
            b.ramp("px", surface, "roof", V(gable.origin_x - gable.edge, gable.x0, gable.eave_top), V(gable.origin_x, gable.x1, gable.ridge_top))
        else:
            b.ramp("nx", surface, "roof", V(gable.origin_x, gable.x0, gable.eave_top), V(gable.origin_x + gable.edge, gable.x1, gable.ridge_top))
    for side in sides:
        kit.member(roof, name, gable.point(side, gable.x0, gable.run - 0.12, 0.035), gable.point(side, gable.x1, gable.run - 0.12, 0.035), 0.3, 0.02, gable.normal(side), 0.0, "box")


def gable_skin_y(part, frame, gable, a0, a1, z_low, openings, rng, patches=4, name="render_white", thickness=0.02, depth=0.08, flip=False):
    top = lambda a: gable.height(-a if flip else a, depth)
    doors = sorted(o for o in openings if o[2] <= z_low + 0.05)
    holes = [kit.rect(*o) for o in openings if o[2] > z_low + 0.05]
    outline = [(a0, z_low)]
    for d in doors:
        outline += [(d[0], z_low), (d[0], d[3]), (d[1], d[3]), (d[1], z_low)]
    apex = -gable.origin_x if flip else gable.origin_x
    outline += [(a1, z_low), (a1, top(a1))]
    if a0 < apex < a1:
        outline.append((apex, top(apex)))
    outline.append((a0, top(a0)))
    blocked = holes + [kit.rect(d[0] - 0.08, d[1] + 0.08, z_low, d[3] + 0.08) for d in doors]
    blobs = scatter_light((a0 + 0.1, a1 - 0.1, z_low + 0.2, min(top(a0), top(a1)) - 0.1), blocked, patches, (0.12, 0.42), rng, (0.5, 1.3), None, 11)
    kit.skin(part, name, frame, outline, holes + blobs, thickness)


def gable_cols_y(b, tag, y0, y1, gable, base, steps=4, surface="rock"):
    for index in range(steps):
        z0 = base + (gable.ridge_top - base) * index / steps
        z1 = base + (gable.ridge_top - base) * (index + 1) / steps
        half = (gable.ridge_top - z1 - 0.05) / gable.tan
        if half > 0.05:
            b.col(surface, tag, V(gable.origin_x - half, y0, z0), V(gable.origin_x + half, y1, z1))


def gable_wall_y(gable, half, depth=0.05):
    return [(-half, -1.5), (half, -1.5), (half, gable.height(half, depth)), (0.0, gable.height(0.0, depth)), (-half, gable.height(-half, depth))]


def well_rail(b, part, well, z, rng, sides, wood="timber_beam", paint="painted_wood_white", height=0.92, spacing=0.12):
    x0, x1, y0, y1 = well
    edges = {"left": (V(x0, y0, z), V(x0, y1, z)), "right": (V(x1, y0, z), V(x1, y1, z)), "front": (V(x0, y0, z), V(x1, y0, z)), "back": (V(x0, y1, z), V(x1, y1, z))}
    for side in sides:
        a, c = edges[side]
        bd.balustrade(b, part, a, c, rng, height, spacing, wood, paint, 0.1, (True, True), True, "well")


def pendant(b, part, position, rng, shade="town_metal", drop=0.45, kind="warm", segments=10):
    rose = position
    emit(part, kit.geo_lathe([(0.0, 0.0), (0.07, 0.0), (0.03, -0.03), (0.0, -0.035)], max(6, segments - 2)), "plaster_interior", kit.Matrix.Translation(rose), "given", True)
    bottom = rose - V(rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), drop)
    rod(part, "soot", rose - V(0.0, 0.0, 0.03), bottom + V(0.0, 0.0, 0.06), 0.004, 3)
    profile = [(0.02, 0.07), (0.05, 0.06), (0.16, -0.045), (0.15, -0.05), (0.045, 0.045)]
    geo = kit.geo_lathe(profile, segments)
    if shade == "town_metal":
        geo = region_geo(geo, "town_metal", "cream", 0.4)
        emit(part, geo, shade, kit.Matrix.Translation(bottom), "texture", True)
    else:
        emit(part, geo, shade, kit.Matrix.Translation(bottom), "given", True)
    emit(part, kit.geo_lathe([(0.0, 0.03), (0.025, 0.0), (0.02, -0.05), (0.0, -0.06)], 6), "glass_dirty", kit.Matrix.Translation(bottom), "given", True)
    b.light(kind, bottom - V(0.0, 0.0, 0.1))
