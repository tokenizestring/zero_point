import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import town_kit as tk
import oilrig_library as lib
from buildkit import V, Geo, emit, block

kit.preview_root = lib.preview_root
lib.register()

tau = math.pi * 2.0
up = V(0.0, 0.0, 1.0)
sea = 0.0
seabed = -28.0
cellar = 16.0
main = 24.0
deck_x = 25.0
deck_y = 20.0
leg_x = 15.0
leg_y = 12.0
batter = 0.1
leg_radius = 0.9
elevations = [-27.0, -16.0, -6.0, 5.5]
landing_z = 2.0
tower = (-4.0, 3.4, -17.6, -15.2)
tower_split = -16.4
tower_runs = (-2.8, 2.2)
tower_levels = [2.0, 5.5, 9.0, 12.5, 16.0]
cellar_stair = (5.5, 13.6, -19.6, -17.2)
cellar_stair_split = -18.4
cellar_stair_runs = (6.7, 12.4)
drill = (-10.5, -1.5, 0.0, 9.0)
drill_z = 28.5
drill_stair = (-1.5, 5.0, 6.9, 8.1)
wells = [(-7.3 + 1.3 * i, 3.3 + 2.4 * j) for j in range(2) for i in range(3)]
quarters = (12.0, 25.0, -12.0, 12.0)
floors = [24.05, 27.25, 30.45]
roof = 33.65
heli_center = (21.0, 4.0)
heli_half = 10.0
heli_z = 36.0
crane_at = (-15.0, -12.0)
flare_root = (-25.0, 17.5, 25.2)
vdoor = (-6.75, -5.25, 9.0, 18.0)
compressor = (-24.4, -17.0, -9.0, 0.0)
generator = (-24.4, -17.0, 2.0, 15.0)
workshop = (-10.0, -4.0, -19.4, -14.6)
store = (-3.0, 2.0, -19.4, -14.6)
davits = (0.0, 8.5)
boom_rest = (-15.0, 15.0)
grate_names = {"rig_grating"}


def leg_xy(sx, sy, z):
    return sx * (leg_x + (cellar - z) * batter), sy * (leg_y + (cellar - z) * batter)


def leg_point(sx, sy, z):
    x, y = leg_xy(sx, sy, z)
    return V(x, y, z)


def setup(b, keys):
    parts = {}
    for key, sharp in keys:
        parts[key] = b.part(key, sharp)
    return parts


fine = 2.6


def box(part, name, x0, x1, y0, y1, z0, z1, mapping="box", bevel=0.0, scale=1.0):
    low = V(min(x0, x1), min(y0, y1), min(z0, z1))
    high = V(max(x0, x1), max(y0, y1), max(z0, z1))
    size3 = high - low
    if size3.x < 1e-5 or size3.y < 1e-5 or size3.z < 1e-5:
        return
    geo = kit.geo_cbox(size3.x, size3.y, size3.z, bevel) if bevel > 0.0 else kit.geo_box(size3.x, size3.y, size3.z)
    emit(part, geo, name, kit.Matrix.Translation((low + high) * 0.5), mapping, False, None, scale)


def col(b, surface, tag, x0, x1, y0, y1, z0, z1):
    b.col(surface, tag, V(min(x0, x1), min(y0, y1), min(z0, z1)), V(max(x0, x1), max(y0, y1), max(z0, z1)))


def tube(part, name, a, b_point, radius, sides=12, caps=True, scale=1.0):
    if (b_point - a).length < 1e-4:
        return
    emit(part, kit.geo_tube([a, b_point], kit.circle(radius, sides), caps), name, None, "given", True, None, scale)


def path_tube(part, name, points, radius, sides=6, caps=True, scale=1.0, hint=None):
    emit(part, kit.geo_tube(points, kit.circle(radius, sides), caps, hint), name, None, "given", True, None, scale)


def bar(part, name, center, forward, length, width, height, hint=None, scale=1.0, mapping="box"):
    emit(part, kit.geo_box(length, width, height), name, kit.place(center, forward, hint if hint is not None else up), mapping, False, None, scale)


def pipe(part, name, points, radius, sides=10, bend=None, caps=True):
    rk.pipe(part, name, [p.copy() for p in points], radius, sides, radius * 3.0 if bend is None else bend, caps)


def member(part, name, a, b_point, width, height, roll_up=None, mapping="board"):
    kit.member(part, name, a, b_point, width, height, roll_up, 0.0, mapping)


def frame_of(a, b_point, hint=None):
    forward = (b_point - a).normalized()
    hint = hint if hint is not None else (up if abs(forward.z) < 0.9 else V(1.0, 0.0, 0.0))
    side = hint.cross(forward)
    if side.length < 1e-6:
        side = forward.orthogonal()
    side.normalize()
    upward = forward.cross(side).normalized()
    return forward, side, upward


def ibeam(part, name, a, b_point, depth, width, hint=None, web=0.014, flange=0.022, scale=1.6):
    forward, side, upward = frame_of(a, b_point, hint)
    length = (b_point - a).length
    middle = (a + b_point) * 0.5
    for offset in (depth * 0.5 - flange * 0.5, -depth * 0.5 + flange * 0.5):
        center = middle + upward * offset
        emit(part, kit.geo_box(length, width, flange), name, kit.place(center, forward, upward), "box", False, None, scale)
    emit(part, kit.geo_box(length, web, depth - flange * 2.0), name, kit.place(middle, forward, upward), "box", False, None, scale)


def channel(part, name, a, b_point, depth, width, hint=None, web=0.01, flange=0.012, facing=1.0, scale=1.6):
    forward, side, upward = frame_of(a, b_point, hint)
    length = (b_point - a).length
    middle = (a + b_point) * 0.5
    emit(part, kit.geo_box(length, web, depth), name, kit.place(middle, forward, upward), "box", False, None, scale)
    for offset in (depth * 0.5 - flange * 0.5, -depth * 0.5 + flange * 0.5):
        center = middle + upward * offset + side * (facing * width * 0.5)
        emit(part, kit.geo_box(length, width, flange), name, kit.place(center, forward, upward), "box", False, None, scale)


def angle_bar(part, name, a, b_point, leg=0.08, thick=0.008, hint=None, turn=0.0, scale=2.0):
    forward, side, upward = frame_of(a, b_point, hint)
    if turn:
        c = math.cos(turn)
        s = math.sin(turn)
        side, upward = side * c + upward * s, upward * c - side * s
    length = (b_point - a).length
    middle = (a + b_point) * 0.5
    emit(part, kit.geo_box(length, leg, thick), name, kit.place(middle + side * (leg * 0.5), forward, upward), "box", False, None, scale)
    emit(part, kit.geo_box(length, thick, leg), name, kit.place(middle + upward * (leg * 0.5), forward, upward), "box", False, None, scale)


def ring(part, name, center, axis, radius, thickness, width, sides=16):
    axis = axis.normalized()
    profile = [(radius, -width * 0.5), (radius + thickness, -width * 0.5), (radius + thickness, width * 0.5), (radius, width * 0.5)]
    geo = kit.geo_lathe([(r, z) for r, z in profile] + [(radius, -width * 0.5)], sides)
    emit(part, geo, name, rk.axis_matrix(center, axis), "given", False)


def disc_geo(radius, thickness, sides=16):
    return kit.geo_lathe([(0.0, 0.0), (radius, 0.0), (radius, thickness), (0.0, thickness)], sides)


def lathe(part, name, center, axis, profile, sides=16, smooth=True, scale=1.0):
    emit(part, kit.geo_lathe(profile, sides), name, rk.axis_matrix(center, axis.normalized()), "given", smooth, None, scale)


def flange(part, name, center, axis, radius, sides=12, bolts=0):
    axis = axis.normalized()
    lathe(part, name, center - axis * 0.03, axis, [(0.0, 0.0), (radius * 1.75, 0.0), (radius * 1.75, 0.06), (0.0, 0.06)], sides, False)


def handwheel(part, name, center, axis, radius, sides=12):
    axis = axis.normalized()
    hint = up if abs(axis.z) < 0.9 else V(1.0, 0.0, 0.0)
    a1 = hint.cross(axis).normalized()
    a2 = axis.cross(a1).normalized()
    points = [center + (a1 * math.cos(tau * i / sides) + a2 * math.sin(tau * i / sides)) * radius for i in range(sides + 1)]
    emit(part, kit.geo_tube(points, kit.circle(radius * 0.08, 5), False, axis), name, None, "given", True)
    for k in range(3):
        angle = tau * k / 3.0
        tube(part, name, center, center + (a1 * math.cos(angle) + a2 * math.sin(angle)) * radius, radius * 0.05, 4, False)


def gate_valve(part, name, center, axis, radius, wheel=True, stem_up=None, wheel_name="rig_paint_yellow"):
    axis = axis.normalized()
    stem = stem_up if stem_up is not None else up
    body = radius * 1.6
    tube(part, name, center - axis * body, center + axis * body, radius * 1.25, 10)
    flange(part, name, center - axis * body, axis, radius, 10)
    flange(part, name, center + axis * body, axis, radius, 10)
    bonnet_top = center + stem * radius * 3.4
    tube(part, name, center, bonnet_top, radius * 0.75, 8)
    tube(part, name, bonnet_top, bonnet_top + stem * radius * 1.8, radius * 0.12, 6)
    if wheel:
        handwheel(part, wheel_name, bonnet_top + stem * radius * 1.6, stem, radius * 1.9)


def vessel(part, name, a, b_point, radius, sides=24, head=0.5):
    axis = (b_point - a)
    length = axis.length
    axis.normalize()
    steps = 4
    profile = [(0.0, -radius * head)] + [(radius * math.sin(math.pi * 0.5 * i / steps), -radius * head * math.cos(math.pi * 0.5 * i / steps)) for i in range(1, steps + 1)]
    profile += [(radius, length)]
    profile += [(radius * math.sin(math.pi * 0.5 * i / steps), length + radius * head * math.cos(math.pi * 0.5 * i / steps)) for i in range(steps - 1, 0, -1)]
    profile += [(0.0, length + radius * head)]
    lathe(part, name, a, axis, profile, sides, True)


def saddle(part, name, center, axis, radius, width=0.3, height=None):
    axis = axis.normalized()
    side = up.cross(axis).normalized()
    base = center.z - radius - (height if height is not None else 0.4)
    top = center.z - radius * 0.55
    for s in (-1.0, 1.0):
        p0 = center + side * (s * radius * 0.85)
        box(part, name, p0.x - 0.02 - abs(axis.x) * width * 0.5, p0.x + 0.02 + abs(axis.x) * width * 0.5, p0.y - 0.02 - abs(axis.y) * width * 0.5, p0.y + 0.02 + abs(axis.y) * width * 0.5, base, top)
    w = radius * 1.9
    c = center
    box(part, name, c.x - abs(side.x) * w * 0.5 - abs(axis.x) * width * 0.5, c.x + abs(side.x) * w * 0.5 + abs(axis.x) * width * 0.5, c.y - abs(side.y) * w * 0.5 - abs(axis.y) * width * 0.5, c.y + abs(side.y) * w * 0.5 + abs(axis.y) * width * 0.5, base, base + 0.03)
    box(part, name, c.x - abs(side.x) * w * 0.5 - abs(axis.x) * 0.012, c.x + abs(side.x) * w * 0.5 + abs(axis.x) * 0.012, c.y - abs(side.y) * w * 0.5 - abs(axis.y) * 0.012, c.y + abs(side.y) * w * 0.5 + abs(axis.y) * 0.012, base, top - radius * 0.3)


def grating(part, x0, x1, y0, y1, z, double=True):
    corners = [V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z)]
    emit(part, Geo(corners, [(0, 1, 2, 3)]), "rig_grating", None, "world")
    if double:
        lower = [V(x0, y0, z - 0.028), V(x1, y0, z - 0.028), V(x1, y1, z - 0.028), V(x0, y1, z - 0.028)]
        emit(part, Geo(lower, [(0, 1, 2, 3)]), "rig_grating", None, "world")


def grating_floor(b, parts, x0, x1, y0, y1, z, frame_name="rig_paint_grey", collide=True, tag="grate", holes=(), panel=1.0, edge=True):
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
        grating(parts["grating"], px0, px1, py0, py1, z)
        if collide:
            col(b, "grate", tag, px0, px1, py0, py1, z - 0.3, z)
    if edge:
        for px0, px1, py0, py1 in pieces:
            for ya in (py0, py1):
                box(parts["structure"], frame_name, px0, px1, ya - 0.025, ya + 0.025, z - 0.06, z - 0.002)
            for xa in (px0, px1):
                box(parts["structure"], frame_name, xa - 0.025, xa + 0.025, py0, py1, z - 0.06, z - 0.002)
    return pieces


def plate_floor(b, part, x0, x1, y0, y1, z, name="rig_deck_green", holes=(), thickness=0.03, surface="metal", tag="deck", collide=True):
    outline = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    loops = [[(hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1)] for hx0, hx1, hy0, hy1 in holes]
    geo = kit.geo_slab(V(0.0, 0.0, 0.0), V(1.0, 0.0, 0.0), V(0.0, 1.0, 0.0), V(0.0, 0.0, 1.0), outline, loops, z - thickness, z)
    emit(part, geo, name, None, "world")
    if collide:
        tk.floor_cols(b, surface, tag, x0, x1, y0, y1, z - 0.35, z, holes)


def rail_segment(part, a, c, height, rng, name="rig_paint_yellow", mid=True, kick=True, post_step=1.6, start_post=True, end_post=True, sag=0.0, bent=0.0):
    length = (c - a).length
    if length < 0.05:
        return
    direction = (c - a).normalized()
    count = max(1, int(math.ceil(length / post_step)))
    for index in range(count + 1):
        if (index == 0 and not start_post) or (index == count and not end_post):
            continue
        p = a + direction * (length * index / count)
        lean = V(rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), 0.0) * (bent * rng.random())
        tube(part, name, p, p + V(0.0, 0.0, height) + lean, 0.024, 6, True, fine)
    top = [a + V(0.0, 0.0, height), c + V(0.0, 0.0, height)]
    if sag > 0.0:
        top = [a + V(0.0, 0.0, height) + (c - a) * t - V(0.0, 0.0, sag * math.sin(math.pi * t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    path_tube(part, name, top, 0.025, 6, True, fine)
    if mid:
        tube(part, name, a + V(0.0, 0.0, height * 0.52), c + V(0.0, 0.0, height * 0.52), 0.019, 6, True, fine)
    if kick:
        middle = (a + c) * 0.5 + V(0.0, 0.0, 0.055)
        bar(part, name, middle, direction, length, 0.006, 0.1, up, fine)


def railing(b, part, points, z, rng, height=1.1, name="rig_paint_yellow", collide=True, closed=False, tag="rail", sag=0.0, bent=0.0, mid=True, kick=True):
    pts = [V(p[0], p[1], z) for p in points]
    if closed:
        pts.append(pts[0].copy())
    for index in range(len(pts) - 1):
        a = pts[index]
        c = pts[index + 1]
        rail_segment(part, a, c, height, rng, name, mid, kick, 1.6, True, index == len(pts) - 2, sag, bent)
        if collide:
            pad = 0.05
            col(b, "metal", tag, min(a.x, c.x) - pad, max(a.x, c.x) + pad, min(a.y, c.y) - pad, max(a.y, c.y) + pad, z, z + height)


def stair_flight(b, parts, x0, x1, y0, y1, z0, z1, direction, rng, stringer="rig_paint_yellow", rail_name="rig_paint_yellow", rails=(True, True), collide_rails=(True, True), tag="stair", tread_name="rig_grating", rail_height=1.0):
    along_x = direction in ("px", "nx")
    sign = 1.0 if direction in ("px", "py") else -1.0
    if along_x:
        start = x0 if sign > 0 else x1
        length = x1 - x0
        width = y1 - y0
    else:
        start = y0 if sign > 0 else y1
        length = y1 - y0
        width = x1 - x0
    rise = z1 - z0
    steps = max(2, int(round(rise / 0.19)))
    going = length / steps
    step_rise = rise / steps

    def point(a_value, c_value, z):
        return V(a_value, c_value, z) if along_x else V(c_value, a_value, z)

    across0 = y0 if along_x else x0
    across1 = y1 if along_x else x1
    for index in range(steps):
        top = z0 + step_rise * (index + 1)
        f0 = start + sign * going * index
        f1 = start + sign * going * (index + 1)
        a_lo = min(f0, f1) - 0.01
        a_hi = max(f0, f1) + 0.01
        if along_x:
            corners = [V(a_lo, across0 + 0.03, top), V(a_hi, across0 + 0.03, top), V(a_hi, across1 - 0.03, top), V(a_lo, across1 - 0.03, top)]
        else:
            corners = [V(across0 + 0.03, a_lo, top), V(across1 - 0.03, a_lo, top), V(across1 - 0.03, a_hi, top), V(across0 + 0.03, a_hi, top)]
        emit(parts["grating"], Geo(corners, [(0, 1, 2, 3)]), tread_name, None, "world")
        lower = [V(c.x, c.y, c.z - 0.028) for c in corners]
        emit(parts["grating"], Geo(lower, [(0, 1, 2, 3)]), tread_name, None, "world")
        nose_a = f0 + sign * 0.0
        if along_x:
            box(parts["structure"], "rig_paint_yellow", min(nose_a, nose_a + sign * 0.035), max(nose_a, nose_a + sign * 0.035), across0 + 0.03, across1 - 0.03, top - 0.03, top, "box", 0.0, fine)
        else:
            box(parts["structure"], "rig_paint_yellow", across0 + 0.03, across1 - 0.03, min(nose_a, nose_a + sign * 0.035), max(nose_a, nose_a + sign * 0.035), top - 0.03, top, "box", 0.0, fine)
    end = start + sign * length
    for edge, outward in ((across0, -1.0), (across1, 1.0)):
        a = point(start, edge + outward * 0.02, z0 - 0.12)
        c = point(end, edge + outward * 0.02, z1 - 0.12)
        forward = (c - a).normalized()
        upward = up - forward * up.dot(forward)
        bar(parts["structure"], stringer, (a + c) * 0.5, forward, (c - a).length + 0.15, 0.012, 0.24, upward.normalized(), 1.8)
    for side_index, (edge, outward) in enumerate(((across0, -1.0), (across1, 1.0))):
        if not rails[side_index]:
            continue
        offset = edge + outward * 0.05
        foot = point(start, offset, z0)
        head = point(end, offset, z1)
        count = max(2, int(math.ceil(length / 1.5)))
        for k in range(count + 1):
            t = k / count
            p = foot.lerp(head, t)
            tube(parts["structure"], rail_name, p - V(0.0, 0.0, 0.05), p + V(0.0, 0.0, rail_height), 0.022, 6, True, fine)
        tube(parts["structure"], rail_name, foot + V(0.0, 0.0, rail_height), head + V(0.0, 0.0, rail_height), 0.025, 6, True, fine)
        tube(parts["structure"], rail_name, foot + V(0.0, 0.0, rail_height * 0.5), head + V(0.0, 0.0, rail_height * 0.5), 0.019, 6, True, fine)
        if collide_rails[side_index]:
            c0 = offset - 0.05
            c1 = offset + 0.05
            if along_x:
                col(b, "metal", tag + "_rail", x0, x1, c0, c1, z0, z1 + 1.1)
            else:
                col(b, "metal", tag + "_rail", c0, c1, y0, y1, z0, z1 + 1.1)
    pieces = 4
    for k in range(pieces):
        za = z0 + rise * k / pieces
        zb = z0 + rise * (k + 1) / pieces
        a = start + sign * length * k / pieces
        c = start + sign * length * (k + 1) / pieces
        if along_x:
            b.ramp(direction, "grate", tag, V(min(a, c), y0, za), V(max(a, c), y1, zb))
        else:
            b.ramp(direction, "grate", tag, V(x0, min(a, c), za), V(x1, max(a, c), zb))


def ladder(part, foot, top_z, facing, width=0.45, name="rig_paint_yellow", cage=False, cage_from=2.4):
    facing = facing.normalized()
    side = V(-facing.y, facing.x, 0.0)
    for s in (-0.5, 0.5):
        a = foot + side * (width * s)
        tube(part, name, a, V(a.x, a.y, top_z + 1.0), 0.025, 6, True, fine)
    z = foot.z + 0.3
    while z < top_z:
        tube(part, name, foot + side * (-width * 0.5) + V(0.0, 0.0, z - foot.z), foot + side * (width * 0.5) + V(0.0, 0.0, z - foot.z), 0.012, 5, False, fine)
        z += 0.3
    if cage:
        radius = 0.38
        center = foot + facing * (-0.38)
        z = foot.z + cage_from
        while z < top_z + 1.0:
            points = []
            for k in range(9):
                angle = math.pi * (0.0 + k / 8.0)
                direction = side * math.cos(angle) - facing * math.sin(angle)
                points.append(center + direction * radius + V(0.0, 0.0, z - foot.z))
            path_tube(part, name, points, 0.012, 4, False, fine, up)
            z += 0.9
        for k in range(5):
            angle = math.pi * (0.1 + 0.8 * k / 4.0)
            direction = side * math.cos(angle) - facing * math.sin(angle)
            p = center + direction * radius
            tube(part, name, p + V(0.0, 0.0, cage_from), p + V(0.0, 0.0, top_z + 1.0 - foot.z), 0.01, 4, False, fine)


def floodlight(b, part, lamp_part, position, aim, kind="cold", lit=True, broken=False, rng=None, mount=None):
    aim = aim.normalized()
    hint = up if abs(aim.z) < 0.9 else V(1.0, 0.0, 0.0)
    head = position
    if mount is not None:
        tube(part, "rig_paint_grey", mount, position, 0.02, 6)
    if broken and rng is not None:
        aim = (aim + V(rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), -0.9)).normalized()
    matrix = kit.place(head, aim, hint)
    emit(part, kit.geo_cbox(0.22, 0.36, 0.3, 0.02), "rig_paint_grey", matrix, "box")
    emit(part, kit.geo_box(0.04, 0.42, 0.06), "rig_paint_grey", matrix @ kit.Matrix.Translation(V(-0.05, 0.0, 0.17)), "box")
    lens = "glass_dirty" if (broken or not lit) else ("rig_lamp_cold" if kind == "cold" else "rig_lamp_warm")
    emit(lamp_part, kit.geo_box(0.02, 0.3, 0.24), lens, matrix @ kit.Matrix.Translation(V(0.115, 0.0, 0.0)), "box")
    if lit and not broken:
        b.light(kind, head + aim * 0.6)


def bulkhead_light(b, part, position, normal, kind="warm", lit=True, broken=False):
    normal = normal.normalized()
    hint = up if abs(normal.z) < 0.9 else V(0.0, 1.0, 0.0)
    matrix = kit.place(position + normal * 0.05, normal, hint)
    emit(part, kit.geo_cbox(0.1, 0.32, 0.2, 0.02), "rig_paint_grey", matrix, "box")
    lens = "glass_dirty" if (broken or not lit) else ("rig_lamp_cold" if kind == "cold" else "rig_lamp_warm")
    emit(part, kit.geo_box(0.03, 0.24, 0.13), lens, matrix @ kit.Matrix.Translation(V(0.055, 0.0, 0.0)), "box")
    if lit and not broken:
        b.light(kind, position + normal * 0.35)


def strip_light(b, part, center, length, along_x=True, kind="cold", lit=True, hanging=0.0, tilt=0.0):
    hx = length * 0.5 if along_x else 0.09
    hy = 0.09 if along_x else length * 0.5
    z = center.z - hanging
    if hanging > 0.0:
        for s in (-0.4, 0.4):
            p = center + (V(length * s, 0.0, 0.0) if along_x else V(0.0, length * s, 0.0))
            drop = hanging + (tilt * s * 2.0)
            rk.pipe(part, "rig_rubber", [p, p - V(0.0, 0.0, drop)], 0.004, 4, 0.0, False)
    low_end = tilt * length * 0.5
    box(part, "rig_paint_white", center.x - hx, center.x + hx, center.y - hy, center.y + hy, z - 0.06, z)
    box(part, "rig_lamp_cold" if (lit and kind == "cold") else ("rig_lamp_warm" if lit else "glass_dirty"), center.x - hx + 0.03, center.x + hx - 0.03, center.y - hy + 0.02, center.y + hy - 0.02, z - 0.075, z - 0.06)
    if lit:
        b.light(kind, V(center.x, center.y, z - 0.35))


def sign(part, key, center, normal, width, height, roll=0.0, backing="rig_paint_grey", lift=0.012):
    n = normal.normalized()
    tk.atlas_panel(part, "rig_signs", center + n * lift, n, width, height, lib.region_uv(lib.signs, key), roll, 0.002)
    hint = up if abs(n.z) < 0.9 else V(0.0, 1.0, 0.0)
    emit(part, kit.geo_box(lift, width + 0.03, height + 0.03), backing, kit.place(center + n * (lift * 0.5), n, hint), "box")


def decal(part, key, center, normal, width, height, roll=0.0, lift=0.004):
    n = normal.normalized()
    tk.atlas_panel(part, "rig_decals", center, n, width, height, lib.region_uv(lib.decals, key, 2.0), roll, lift)


def floor_decal(part, key, x, y, z, width, height, roll=0.0):
    decal(part, key, V(x, y, z), up, width, height, roll, 0.004)


def catenary(a, c, sag, steps=8):
    return [a.lerp(c, t) - V(0.0, 0.0, sag * 4.0 * t * (1.0 - t)) for t in [i / steps for i in range(steps + 1)]]


def cable(part, a, c, sag, radius=0.012, name="rig_rubber", steps=8):
    emit(part, kit.geo_tube(catenary(a, c, sag, steps), kit.circle(radius, 5), True), name, None, "given", True)


def hanging_cable(part, start, length, rng, radius=0.014, name="rig_rubber", sway=0.25, steps=6):
    points = [start.copy()]
    drift = V(rng.uniform(-sway, sway), rng.uniform(-sway, sway), 0.0)
    for i in range(1, steps + 1):
        t = i / steps
        points.append(start + drift * (t * t) - V(0.0, 0.0, length * t))
    end = points[-1]
    curl = V(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0.05)
    points.append(end + curl)
    emit(part, kit.geo_tube(points, kit.circle(radius, 5), True), name, None, "given", True)


def cable_tray(part, a, c, width, rng, name="rig_paint_grey", cables=5, droop=0.0, cable_name="rig_rubber"):
    direction = (c - a).normalized()
    side = up.cross(direction).normalized()
    length = (c - a).length
    for s in (-0.5, 0.5):
        p0 = a + side * (width * s)
        p1 = c + side * (width * s)
        emit(part, kit.geo_box(length, 0.012, 0.08), name, kit.place((p0 + p1) * 0.5, direction, up), "board")
    rungs = int(length / 0.3)
    for k in range(rungs + 1):
        p = a + direction * (length * k / max(rungs, 1))
        emit(part, kit.geo_box(0.025, width, 0.012), name, kit.place(p - V(0.0, 0.0, 0.035), direction, up), "box")
    for k in range(cables):
        offset = side * (width * (-0.4 + 0.8 * k / max(cables - 1, 1))) + V(0.0, 0.0, -0.01)
        tube(part, cable_name, a + offset, c + offset, 0.018 + 0.006 * (k % 2), 5)
    if droop > 0.0:
        k = rng.uniform(0.2, 0.8)
        p = a + direction * (length * k)
        hanging_cable(part, p + side * (width * 0.3), droop, rng)


def drum(part, center, rng, name="rig_paint_grey", lying=False, yaw=0.0, dented=0.0):
    radius = 0.29
    height = 0.88
    profile = [(0.0, 0.0), (radius - 0.01, 0.0), (radius, 0.02), (radius, height * 0.33), (radius + 0.012, height * 0.34), (radius, height * 0.36), (radius, height * 0.66), (radius + 0.012, height * 0.67), (radius, height * 0.69), (radius, height - 0.02), (radius - 0.01, height), (0.0, height)]
    if lying:
        axis = V(math.cos(yaw), math.sin(yaw), 0.0)
        lathe(part, name, center + V(0.0, 0.0, radius) - axis * (height * 0.5), axis, profile, 14)
    else:
        lathe(part, name, center, up, profile, 14)


def gas_cylinder(part, center, rng, name="rig_paint_grey", lying=False, yaw=0.0, height=1.4, radius=0.11, cap="rig_paint_white"):
    profile = [(0.0, 0.0), (radius, 0.0), (radius, height - radius), (radius * 0.6, height - radius * 0.25), (radius * 0.32, height), (0.0, height)]
    axis = up if not lying else V(math.cos(yaw), math.sin(yaw), 0.0)
    base = center if not lying else center + V(0.0, 0.0, radius) - axis * (height * 0.5)
    lathe(part, name, base, axis, profile, 10)
    lathe(part, cap, base + axis * height, axis, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.1), (0.0, 0.1)], 8, False)


def pallet(part, center, yaw, rng, name="timber_planks_weathered", load=None):
    matrix = kit.turned(center, yaw)
    for x in (-0.5, 0.0, 0.5):
        emit(part, kit.geo_box(0.1, 1.2, 0.1), "timber_beam", matrix @ kit.Matrix.Translation(V(x, 0.0, 0.05)), "board")
    for k in range(7):
        if rng.random() < 0.12:
            continue
        y = -0.55 + k * 0.183
        emit(part, kit.geo_box(1.2, 0.13, 0.022), name, matrix @ kit.Matrix.Translation(V(0.0, y, 0.111)), "board")


def crate(part, center, size3, yaw, rng, name="timber_planks_weathered"):
    rk.crate(part, rng, center, size3, yaw, name, "timber_beam")


def sack(part, center, rng, scale=1.0, name="fabric_worn"):
    kit.lump(part, name, center + V(0.0, 0.0, 0.14 * scale), (0.32 * scale, 0.22 * scale, 0.15 * scale), rng, 0.18, 2, -0.14 * scale)


def hose(part, center, rng, radius=0.38, turns=3, thickness=0.03, name="rig_rubber"):
    points = []
    steps = 14 * turns
    for i in range(steps + 1):
        t = i / steps
        angle = tau * turns * t
        r = radius * (0.75 + 0.25 * t)
        points.append(center + V(math.cos(angle) * r, math.sin(angle) * r, thickness + (i % 14 == 0) * 0.0 + t * thickness * 2.0))
    emit(part, kit.geo_tube(points, kit.circle(thickness, 6), True), name, None, "given", True)


def lump(part, name, center, radii, rng, rough=0.25, subdivisions=1, floor=None):
    kit.lump(part, name, center, radii, rng, rough, subdivisions, floor)


def nest(part, center, rng):
    for k in range(10):
        a = rng.uniform(0.0, tau)
        r = rng.uniform(0.15, 0.3)
        p = center + V(math.cos(a) * r, math.sin(a) * r, rng.uniform(0.0, 0.12))
        q = center + V(math.cos(a + 2.0) * r, math.sin(a + 2.0) * r, rng.uniform(0.0, 0.12))
        tube(part, "hay", p, q, 0.012, 4, False)
    kit.lump(part, "hay", center + V(0.0, 0.0, 0.04), (0.28, 0.28, 0.07), rng, 0.3, 1, 0.0)


def far_tube(part, name, a, c, radius, sides=4, scale=1.0):
    if (c - a).length < 1e-4:
        return
    emit(part, kit.geo_tube([a, c], kit.circle(radius, sides, math.pi / sides), False), name, None, "given", sides > 4, None, scale)


def far_path(part, name, points, radius, sides=4, scale=1.0, hint=None):
    emit(part, kit.geo_tube(points, kit.circle(radius, sides, math.pi / sides), False, hint), name, None, "given", sides > 4, None, scale)


def far_box(part, name, x0, x1, y0, y1, z0, z1, skip=(), scale=1.0, mapping="box"):
    low = V(min(x0, x1), min(y0, y1), min(z0, z1))
    high = V(max(x0, x1), max(y0, y1), max(z0, z1))
    size3 = high - low
    if size3.x < 1e-5 or size3.y < 1e-5 or size3.z < 1e-5:
        return
    emit(part, kit.geo_box(size3.x, size3.y, size3.z, skip), name, kit.Matrix.Translation((low + high) * 0.5), mapping, False, None, scale)


def far_bar(part, name, a, c, width, height, hint=None, scale=1.0):
    if (c - a).length < 1e-4:
        return
    emit(part, kit.geo_box((c - a).length, width, height, ("left", "right")), name, kit.place((a + c) * 0.5, c - a, hint if hint is not None else up), "box", False, None, scale)


def far_post(part, name, x, y, z0, z1, half=0.05, scale=1.0):
    far_box(part, name, x - half, x + half, y - half, y + half, z0, z1, ("top", "bottom"), scale)


def flat_quad(part, name, x0, x1, y0, y1, z, mapping="world"):
    corners = [V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z)]
    emit(part, Geo(corners, [kit.orient((0, 1, 2, 3), corners, up)]), name, None, mapping)


def far_panel(part, name, a, c, z0, z1, normal, mapping="box"):
    corners = [V(a[0], a[1], z0), V(c[0], c[1], z0), V(c[0], c[1], z1), V(a[0], a[1], z1)]
    emit(part, Geo(corners, [kit.orient((0, 1, 2, 3), corners, normal)]), name, None, mapping)


def far_rail(part, points, z, height=1.1, name="rig_paint_yellow", post_step=4.8, mid=True):
    for index in range(len(points) - 1):
        a = V(points[index][0], points[index][1], z)
        c = V(points[index + 1][0], points[index + 1][1], z)
        length = (c - a).length
        if length < 0.05:
            continue
        far_bar(part, name, a + V(0.0, 0.0, height - 0.03), c + V(0.0, 0.0, height - 0.03), 0.06, 0.06, None, fine)
        if mid:
            far_bar(part, name, a + V(0.0, 0.0, height * 0.52), c + V(0.0, 0.0, height * 0.52), 0.05, 0.05, None, fine)
        count = max(1, int(math.ceil(length / post_step)))
        for k in range(count + 1):
            if k == count and index < len(points) - 2:
                continue
            p = a.lerp(c, k / count)
            far_post(part, name, p.x, p.y, z, z + height, 0.03, fine)


def slope_ends(x0, x1, y0, y1, z0, z1, direction):
    if direction in ("px", "nx"):
        lo, hi = (x0, x1) if direction == "px" else (x1, x0)
        return [(V(lo, y, z0), V(hi, y, z1)) for y in (y0, y1)]
    lo, hi = (y0, y1) if direction == "py" else (y1, y0)
    return [(V(x, lo, z0), V(x, hi, z1)) for x in (x0, x1)]


def slope_box(part, name, x0, x1, y0, y1, z0, z1, direction, thickness=0.25):
    edges = slope_ends(x0, x1, y0, y1, z0, z1, direction)
    a = (edges[0][0] + edges[1][0]) * 0.5
    c = (edges[0][1] + edges[1][1]) * 0.5
    width = (edges[1][0] - edges[0][0]).length
    forward = (c - a).normalized()
    upward = (up - forward * up.dot(forward)).normalized()
    emit(part, kit.geo_box((c - a).length, width, thickness), name, kit.place((a + c) * 0.5 - upward * (thickness * 0.5), forward, upward), "box")


def far_stair(part, grate, x0, x1, y0, y1, z0, z1, direction, name="rig_paint_yellow", rails=(True, True), rail_name="rig_paint_yellow"):
    edges = slope_ends(x0, x1, y0, y1, z0, z1, direction)
    corners = [edges[0][0], edges[0][1], edges[1][1], edges[1][0]]
    emit(grate, Geo(corners, [kit.orient((0, 1, 2, 3), corners, up)]), "rig_grating", None, "world")
    for (a, c), rail in zip(edges, rails):
        far_bar(part, name, a - V(0.0, 0.0, 0.13), c - V(0.0, 0.0, 0.13), 0.05, 0.25, None, fine)
        if rail:
            far_bar(part, rail_name, a + V(0.0, 0.0, 0.97), c + V(0.0, 0.0, 0.97), 0.05, 0.05, None, fine)
            far_post(part, rail_name, c.x, c.y, c.z, c.z + 1.0, 0.03, fine)


def shipping_container(b, part, x0, y0, z, along_x, rng, paint="rig_paint_orange", length=6.06, width=2.44, height=2.59, open_door=False, tag="container"):
    if along_x:
        x1 = x0 + length
        y1 = y0 + width
    else:
        x1 = x0 + width
        y1 = y0 + length
    box(part, paint, x0 + 0.04, x1 - 0.04, y0 + 0.04, y1 - 0.04, z + 0.1, z + height - 0.08, "box")
    for cx in (x0, x1 - 0.16):
        for cy in (y0, y1 - 0.16):
            box(part, "rig_rust", cx, cx + 0.16, cy, cy + 0.16, z, z + height, "box")
    for zz in (z, z + height - 0.12):
        box(part, paint, x0, x1, y0, y0 + 0.12, zz, zz + 0.12)
        box(part, paint, x0, x1, y1 - 0.12, y1, zz, zz + 0.12)
        box(part, paint, x0, x0 + 0.12, y0, y1, zz, zz + 0.12)
        box(part, paint, x1 - 0.12, x1, y0, y1, zz, zz + 0.12)
    pitch = 0.28
    if along_x:
        count = int((length - 0.4) / pitch)
        for k in range(count):
            x = x0 + 0.25 + k * pitch
            for yy, sgn in ((y0 + 0.04, -1.0), (y1 - 0.04, 1.0)):
                box(part, paint, x, x + 0.1, yy - (0.035 if sgn < 0 else 0.0), yy + (0.035 if sgn > 0 else 0.0), z + 0.12, z + height - 0.12)
    else:
        count = int((length - 0.4) / pitch)
        for k in range(count):
            y = y0 + 0.25 + k * pitch
            for xx, sgn in ((x0 + 0.04, -1.0), (x1 - 0.04, 1.0)):
                box(part, paint, xx - (0.035 if sgn < 0 else 0.0), xx + (0.035 if sgn > 0 else 0.0), y, y + 0.1, z + 0.12, z + height - 0.12)
    col(b, "metal", tag, x0, x1, y0, y1, z, z + height)
