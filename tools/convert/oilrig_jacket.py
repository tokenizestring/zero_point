import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
import oilrig_kit as ok
from buildkit import V, Geo, emit
from oilrig_kit import box, col, tube, up

bands = [(-99.0, 1.4, "rig_marine"), (1.4, 4.6, "rig_rust"), (4.6, 99.0, "rig_paint_yellow")]
top_z = 15.3
riser_xs = [9.0, 6.6]
caissons = [(-13.0, -4.2), (-13.0, -1.6)]


def band_of(z):
    for z0, z1, name in bands:
        if z0 <= z < z1:
            return name
    return bands[-1][2]


def banded_tube(part, a, c, radius, sides, caps=False, scale=None):
    if scale is None:
        scale = 0.55 if radius > 0.6 else 0.85
    low, high = (a, c) if a.z <= c.z else (c, a)
    cuts = [low.z]
    for z0, z1, name in bands:
        for z in (z0, z1):
            if low.z < z < high.z:
                cuts.append(z)
    cuts.append(high.z)
    cuts = sorted(set(cuts))
    span = high.z - low.z
    for z0, z1 in zip(cuts[:-1], cuts[1:]):
        if span > 1e-6:
            p = low.lerp(high, (z0 - low.z) / span)
            q = low.lerp(high, (z1 - low.z) / span)
        else:
            p, q = low, high
        if (q - p).length < 0.02:
            continue
        emit(part, kit.geo_tube([p, q], kit.circle(radius, sides), caps), band_of((z0 + z1) * 0.5), None, "given", True, None, scale)


def face_y(z):
    return ok.leg_y + (ok.cellar - z) * ok.batter


def face_x(z):
    return ok.leg_x + (ok.cellar - z) * ok.batter


def surface_point(center, toward, radius):
    d = (toward - center)
    d.z = 0.0
    if d.length < 1e-6:
        return center
    return center + d.normalized() * radius


def legs(b, parts, rng):
    structure = parts["structure"]
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            foot = ok.leg_point(sx, sy, -29.5)
            head = ok.leg_point(sx, sy, top_z + 0.7)
            banded_tube(structure, foot, head, ok.leg_radius, 20, True)
            for z in ok.elevations:
                a = ok.leg_point(sx, sy, z - 1.3)
                c = ok.leg_point(sx, sy, z + 1.3)
                banded_tube(structure, a, c, ok.leg_radius + 0.07, 20, True)
            for z0 in (-2.0, 1.0, 4.0, 7.0, 10.0, 13.0):
                z1 = z0 + 3.0
                p = ok.leg_point(sx, sy, (z0 + z1) * 0.5)
                col(b, "metal", "leg", p.x - 0.82, p.x + 0.82, p.y - 0.82, p.y + 0.82, z0, z1)
            for z0 in (-27.0, -21.0, -15.0, -9.0, -5.0):
                z1 = z0 + (6.0 if z0 < -9.0 else 3.0) + (1.0 if z0 == -9.0 else 0.0)
                p = ok.leg_point(sx, sy, (z0 + z1) * 0.5)
                col(b, "metal", "leg", p.x - 0.85, p.x + 0.85, p.y - 0.85, p.y + 0.85, z0, z1)


def growth_collar(part, center_fn, radius, z0, z1, rng, bulge=0.12, sides=18, rings=7):
    points = []
    faces = []
    uvs = []
    profile = []
    for i in range(rings + 1):
        t = i / rings
        z = z0 + (z1 - z0) * t
        swell = bulge * math.sin(math.pi * t) ** 0.6
        profile.append((z, swell))
    for i, (z, swell) in enumerate(profile):
        center = center_fn(z)
        for s in range(sides):
            angle = tau_of(s, sides)
            jitter = swell * rng.uniform(0.35, 1.25) if 0 < i < rings else 0.0
            r = radius + jitter
            points.append(V(center.x + math.cos(angle) * r, center.y + math.sin(angle) * r, z + (rng.uniform(-0.06, 0.06) if 0 < i < rings else 0.0)))
    reach = radius * math.pi * 2.0
    for i in range(rings):
        for s in range(sides):
            t = (s + 1) % sides
            a = i * sides + s
            c = i * sides + t
            d = (i + 1) * sides + t
            e = (i + 1) * sides + s
            faces.append((a, c, d, e))
            uvs.append([(reach * s / sides, profile[i][0]), (reach * (s + 1) / sides, profile[i][0]), (reach * (s + 1) / sides, profile[i + 1][0]), (reach * s / sides, profile[i + 1][0])])
    emit(part, Geo(points, faces, uvs), "rig_marine", None, "given", True)


def tau_of(s, sides):
    return math.pi * 2.0 * s / sides


def growth(b, parts, rng):
    part = parts["growth"]
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            growth_collar(part, lambda z, sx=sx, sy=sy: ok.leg_point(sx, sy, z), ok.leg_radius, -2.8, 1.2, rng, 0.16, 20, 7)
            for k in range(7):
                z = rng.uniform(-2.2, 0.9)
                center = ok.leg_point(sx, sy, z)
                angle = rng.uniform(0.0, math.pi * 2.0)
                n = V(math.cos(angle), math.sin(angle), 0.0)
                ok.lump(part, "rig_marine", center + n * (ok.leg_radius + 0.08), (rng.uniform(0.18, 0.32), rng.uniform(0.18, 0.32), rng.uniform(0.14, 0.26)), rng, 0.3, 1)
    for x, y in ok.wells:
        growth_collar(part, lambda z, x=x, y=y: V(x, y, z), 0.38, -2.5, 1.0, rng, 0.1, 12, 5)
    for x, y in caissons:
        growth_collar(part, lambda z, x=x, y=y: V(x, y, z), 0.45, -2.5, 1.0, rng, 0.1, 12, 5)
    for x in riser_xs:
        growth_collar(part, lambda z, x=x: V(x, face_y(z) + 0.9, z), 0.25, -2.5, 1.0, rng, 0.08, 10, 5)


def anode(part, center, along, rng, length=1.9, size=0.22, standoff=0.32, normal=None):
    along = along.normalized()
    normal = normal if normal is not None else V(0.0, 0.0, -1.0)
    body = center + normal * standoff
    emit(part, kit.geo_box(length, size, size), "rig_steel", kit.place(body, along, up if abs(along.z) < 0.9 else V(1.0, 0.0, 0.0)), "box")
    for s in (-0.42, 0.42):
        p = center + along * (length * s)
        tube(part, "rig_marine", p, p + normal * standoff, 0.03, 5, False)


def member_between(part, a, c, radius, sides, inset_a=0.0, inset_c=0.0):
    d = (c - a).normalized()
    banded_tube(part, a + d * inset_a, c - d * inset_c, radius, sides)


def frames(b, parts, rng):
    structure = parts["structure"]
    fittings = parts["fittings"]
    for z in ok.elevations:
        corners = {(sx, sy): ok.leg_point(sx, sy, z) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)}
        radius = 0.42 if z < 0.0 else 0.38
        for a_key, c_key in (((-1.0, -1.0), (1.0, -1.0)), ((-1.0, 1.0), (1.0, 1.0)), ((-1.0, -1.0), (-1.0, 1.0)), ((1.0, -1.0), (1.0, 1.0))):
            a = corners[a_key]
            c = corners[c_key]
            member_between(structure, a, c, radius, 14, ok.leg_radius * 0.92, ok.leg_radius * 0.92)
            if z > -9.0:
                col(b, "metal", "frame", min(a.x, c.x) - radius, max(a.x, c.x) + radius, min(a.y, c.y) - radius, max(a.y, c.y) + radius, z - radius, z + radius)
            if z < -1.0:
                d = (c - a)
                for t in (0.3, 0.7):
                    anode(fittings, a + d * t, d, rng, normal=V(0.0, 0.0, -1.0))
        fx = face_x(z)
        fy = face_y(z)
        guide = (-8.2, -3.8, 2.4, 6.6)
        for a, c in ((V(-fx, 4.5, z), V(guide[0], 4.5, z)), (V(guide[1], 4.5, z), V(fx, 4.5, z)), (V(-6.0, -fy, z), V(-6.0, guide[2], z)), (V(-6.0, guide[3], z), V(-6.0, fy, z))):
            member_between(structure, a, c, 0.3, 10, 0.3, 0.0)
        gx0, gx1, gy0, gy1 = guide
        for a, c in ((V(gx0, gy0, z), V(gx1, gy0, z)), (V(gx0, gy1, z), V(gx1, gy1, z)), (V(gx0, gy0, z), V(gx0, gy1, z)), (V(gx1, gy0, z), V(gx1, gy1, z))):
            emit(structure, kit.geo_box((c - a).length + 0.4, 0.4, 0.4), band_of(z), kit.place((a + c) * 0.5, (c - a).normalized(), up), "board")
        for x, y in ok.wells:
            ok.ring(structure, band_of(z), V(x, y, z - 0.25), up, 0.4, 0.06, 0.5, 12)
        for x, y in caissons:
            ok.ring(structure, band_of(z), V(x, y, z - 0.2), up, 0.47, 0.05, 0.4, 12)
            member_between(structure, V(x, y, z), V(-fx, y, z), 0.18, 8, 0.47, 0.0)
        for x in riser_xs:
            y = fy + 0.9
            ok.ring(structure, band_of(z), V(x, y, z - 0.18), up, 0.27, 0.05, 0.36, 10)
            emit(structure, kit.geo_box(0.22, 0.6, 0.22), band_of(z), kit.place(V(x, y - 0.55, z), V(1.0, 0.0, 0.0), up), "box")


def braces(b, parts, rng):
    structure = parts["structure"]
    fittings = parts["fittings"]
    levels = ok.elevations + [top_z]
    for index in range(len(levels) - 1):
        z0 = levels[index]
        z1 = levels[index + 1]
        radius = 0.36 if z0 < 0.0 else 0.32
        for face in ("-y", "+y", "-x", "+x"):
            if face in ("-y", "+y"):
                sy = -1.0 if face == "-y" else 1.0
                pairs = ((ok.leg_point(-1.0, sy, z0), ok.leg_point(1.0, sy, z1)), (ok.leg_point(1.0, sy, z0), ok.leg_point(-1.0, sy, z1)))
            else:
                sx = -1.0 if face == "-x" else 1.0
                pairs = ((ok.leg_point(sx, -1.0, z0), ok.leg_point(sx, 1.0, z1)), (ok.leg_point(sx, 1.0, z0), ok.leg_point(sx, -1.0, z1)))
            for a, c in pairs:
                member_between(structure, a, c, radius, 12, ok.leg_radius * 1.1, ok.leg_radius * 1.1)
                d = c - a
                if z1 <= 0.5:
                    anode(fittings, a + d * 0.3, d, rng, normal=V(0.0, 0.0, -1.0))
                if z0 < 2.0 < z1 or z0 < -2.0 < z1:
                    for k in range(6):
                        t0 = 0.08 + k * 0.14
                        t1 = t0 + 0.14
                        p = a.lerp(c, t0)
                        q = a.lerp(c, t1)
                        if max(p.z, q.z) < -3.0 or min(p.z, q.z) > 6.0:
                            continue
                        col(b, "metal", "brace", min(p.x, q.x) - radius, max(p.x, q.x) + radius, min(p.y, q.y) - radius, max(p.y, q.y) + radius, min(p.z, q.z) - radius * 0.6, max(p.z, q.z) + radius * 0.6)
            middle = (pairs[0][0] + pairs[0][1]) * 0.5
            ok.ring(structure, band_of(middle.z), middle, (pairs[0][1] - pairs[0][0]), radius, 0.05, 1.2, 12)


def verticals(b, parts, rng):
    structure = parts["structure"]
    fittings = parts["fittings"]
    for x, y in ok.wells:
        banded_tube(structure, V(x, y, -29.5), V(x, y, top_z + 0.4), 0.38, 14, True)
        col(b, "metal", "conductor", x - 0.38, x + 0.38, y - 0.38, y + 0.38, -6.0, top_z)
    for x, y in caissons:
        banded_tube(structure, V(x, y, -20.0), V(x, y, top_z + 0.7), 0.45, 14, False)
        ok.ring(structure, "rig_marine", V(x, y, -20.3), up, 0.45, 0.12, 0.35, 14)
        col(b, "metal", "caisson", x - 0.45, x + 0.45, y - 0.45, y + 0.45, -6.0, top_z)
    for index, x in enumerate(riser_xs):
        points = [V(x, face_y(-27.6) + 0.9 + 12.0, -27.6), V(x, face_y(-27.6) + 0.9, -27.6), V(x, face_y(top_z + 0.6) + 0.9, top_z + 0.6)]
        path = rk.fillet_path(points, 3.0, 6)
        lower = [p for p in path if p.z < 1.4]
        upper = [p for p in path if p.z >= 1.4]
        if lower and upper:
            lower.append(upper[0].copy())
        emit(structure, kit.geo_tube(lower, kit.circle(0.25, 10), True), "rig_marine", None, "given", True)
        emit(structure, kit.geo_tube(upper, kit.circle(0.25, 10), True), "rig_paint_grey", None, "given", True)
        for z in (-21.0, -11.0, 0.0, 10.0):
            y = face_y(z) + 0.9
            ok.ring(structure, band_of(z), V(x, y, z - 0.2), up, 0.26, 0.05, 0.4, 10)
        top = V(x, face_y(top_z + 0.6) + 0.9, top_z + 0.6)
        ok.flange(structure, "rig_paint_grey", top, up, 0.25, 12)
        col(b, "metal", "riser", x - 0.27, x + 0.27, face_y(0.0) + 0.6, face_y(0.0) + 1.2, -6.0, top_z)


landing_x = (-7.0, 7.0)
landing_y = (-20.6, -17.6)
sea_stair = (7.0, 13.3, -20.5, -19.3)
sea_stair_z = (-2.4, 2.0)


def boat_landing(b, parts, rng):
    structure = parts["structure"]
    fittings = parts["fittings"]
    z = ok.landing_z
    x0, x1 = landing_x
    y0, y1 = landing_y
    tx0, tx1, ty0, ty1 = ok.tower
    run0, run1 = ok.tower_runs
    face = -face_y(z - 0.3)
    for gx in (-6.5, 0.0, 6.5):
        ok.ibeam(structure, "rig_paint_yellow", V(gx, face + 0.6, z - 0.26), V(gx, y0 - 0.3, z - 0.26), 0.45, 0.22)
        brace_foot = V(gx, -face_y(-2.6) + 0.3, -2.6)
        tube(structure, "rig_rust", brace_foot, V(gx, -18.4, z - 0.48), 0.13, 8)
        col(b, "metal", "landing_beam", gx - 0.11, gx + 0.11, y0 - 0.3, face + 0.6, z - 0.5, z - 0.06)
    for gy in (y0 - 0.1, y1, ty1):
        ok.ibeam(structure, "rig_paint_yellow", V(x0 - 0.3, gy, z - 0.25), V(x1 + 0.3, gy, z - 0.25), 0.4, 0.2)
    ok.grating_floor(b, parts, x0, x1, y0, y1, z, "rig_paint_yellow", True, "landing")
    ok.grating_floor(b, parts, tx0, tx1, y1, ty1, z, "rig_paint_yellow", True, "landing")
    bumper_y = y0 - 0.38
    posts = [-6.5, -3.25, 0.0, 3.25, 6.5]
    for px in posts:
        banded_tube(structure, V(px, bumper_y, -3.6), V(px, bumper_y, z + 2.4), 0.2, 10, True)
        tube(structure, "rig_rust", V(px, bumper_y, z - 0.25), V(px, y0 + 0.05, z - 0.25), 0.12, 8)
        lathe_fender(fittings, V(px, bumper_y - 0.33, -0.7), 1.7, 0.3, rng)
        col(b, "metal", "bumper", px - 0.35, px + 0.35, bumper_y - 0.65, bumper_y + 0.2, -3.6, z + 2.4)
    for hz in (-1.8, 0.4, z + 2.2):
        banded_tube(structure, V(posts[0], bumper_y, hz), V(posts[-1], bumper_y, hz), 0.14, 8, True)
    for k in range(4):
        cx = rng.uniform(-6.0, 6.0)
        tyre_at(fittings, V(cx, bumper_y - 0.45, z - 0.9 - rng.uniform(0.0, 0.6)), rng)
    gap = (-1.0, 1.0)
    rail = parts["rails"]
    ok.railing(b, rail, [(gap[1], y0), (x1, y0)], z, rng, 1.1, "rig_paint_yellow", True, False, "landing_rail")
    ok.railing(b, rail, [(x1, sea_stair[3] + 0.05), (x1, y1), (tx1 + 0.05, y1)], z, rng, 1.1, "rig_paint_yellow", True, False, "landing_rail")
    sea_steps(b, parts, rng)
    ok.railing(b, rail, [(gap[0], y0), (x0, y0), (x0, y1), (tx0, y1)], z, rng, 1.1, "rig_paint_yellow", True, False, "landing_rail", bent=0.15)
    ok.railing(b, rail, [(tx1, y1), (tx1, ty1)], z, rng, 1.1, "rig_paint_yellow", False, False, "landing_rail")
    chain_points = ok.catenary(V(gap[0], y0, z + 0.95), V(gap[1], y0, z + 0.95), 0.25, 8)
    rk.chain(fittings, "rig_rust", chain_points, 0.13, 0.06, 0.01, rng, 4, 2)
    for lx in (-0.22, 0.22):
        tube(structure, "rig_paint_yellow", V(lx, y0 - 0.12, -2.8), V(lx, y0 - 0.12, z + 1.0), 0.022, 6)
    rung_z = -2.6
    while rung_z < z:
        tube(structure, "rig_paint_yellow", V(-0.22, y0 - 0.12, rung_z), V(0.22, y0 - 0.12, rung_z), 0.014, 5, False)
        rung_z += 0.3
    for bx in (-4.8, 4.8):
        for dx in (-0.3, 0.3):
            ok.lathe(fittings, "rig_rust", V(bx + dx, y0 + 0.45, z), up, [(0.0, 0.0), (0.16, 0.0), (0.14, 0.05), (0.13, 0.42), (0.19, 0.46), (0.19, 0.52), (0.0, 0.52)], 12)
        box(fittings, "rig_rust", bx - 0.55, bx + 0.55, y0 + 0.2, y0 + 0.7, z, z + 0.04)
    rk.chain(fittings, "rig_rust", [V(4.5, y0 + 0.45, z + 0.3), V(4.2, y0 + 0.1, z + 0.05), V(3.6, y0 + 0.3, z + 0.03), V(3.4, y0 + 0.9, z + 0.03)], 0.13, 0.06, 0.01, rng, 4, 2)
    ok.hose(fittings, V(-3.2, -19.0, z), rng, 0.34, 3, 0.022, "rope_net")
    b.loot("box", V(-5.6, -18.6, z))
    for gx, gy in ((-2.0, -19.4), (4.5, -18.3), (-6.2, -20.0)):
        ok.floor_decal(parts["decals"], "guano_a" if gx < 0 else "guano_b", gx, gy, z + 0.006, 1.1, 1.1, rng.uniform(0.0, 6.0))
    ok.floor_decal(parts["decals"], "salt", 1.5, -19.0, z + 0.006, 1.6, 1.6, 0.4)
    lifebuoy(fittings, V(x1 - 0.05, -19.1, z + 0.85), V(1.0, 0.0, 0.0))


def sea_steps(b, parts, rng):
    sx0, sx1, sy0, sy1 = sea_stair
    z0, z1 = sea_stair_z
    ok.stair_flight(b, parts, sx0, sx1, sy0, sy1, z0, z1, "nx", rng, "rig_rust", "rig_paint_yellow", (True, True), (True, True), "sea_stair")
    structure = parts["structure"]
    growth = parts["growth"]
    run = sx1 - sx0
    rise = z1 - z0
    wet = (0.4 - z0) / rise
    for edge, outward in ((sy0, -1.0), (sy1, 1.0)):
        a = V(sx1, edge + outward * 0.02, z0 - 0.12)
        c = V(sx1 - run * wet, edge + outward * 0.02, 0.4 - 0.12)
        forward = (c - a).normalized()
        ok.bar(growth, "rig_marine", (a + c) * 0.5, forward, (c - a).length + 0.1, 0.05, 0.3, (up - forward * up.dot(forward)).normalized(), 1.2)
    middle = (sy0 + sy1) * 0.5
    for t in (0.1, 0.55):
        x = sx1 - run * t
        zs = z0 + rise * t
        banded_tube(structure, V(x, -face_y(-6.0) - 0.3, -6.0), V(x, middle, zs - 0.35), 0.12, 8, False)
        tube(structure, "rig_rust", V(x, sy0 - 0.05, zs - 0.3), V(x, sy1 + 0.05, zs - 0.3), 0.08, 6, True)


def lathe_fender(part, center, length, radius, rng):
    profile = [(0.0, 0.0), (radius * 0.7, 0.0), (radius, length * 0.08), (radius, length * 0.92), (radius * 0.7, length), (0.0, length)]
    ok.lathe(part, "rig_rubber", center, up, profile, 14)
    tube(part, "rig_rust", center + V(0.0, 0.0, length), center + V(0.0, 0.33, length + 0.25), 0.03, 5)


def tyre_at(part, center, rng):
    axis = V(0.0, 1.0, 0.0)
    profile = []
    for k in range(9):
        a = math.pi * 2.0 * k / 8.0
        profile.append((0.36 + 0.11 * math.cos(a), 0.11 * math.sin(a)))
    ok.lathe(part, "rig_rubber", center, axis, profile, 14)
    ok.path_tube(part, "rope_net", [center + V(0.0, 0.0, 0.46), center + V(0.0, 0.2, 1.0), center + V(0.0, 0.38, 1.5)], 0.014, 5, True, 3.0)


def lifebuoy(part, center, normal):
    profile = []
    for k in range(9):
        a = math.pi * 2.0 * k / 8.0
        profile.append((0.3 + 0.06 * math.cos(a), 0.06 * math.sin(a)))
    ok.lathe(part, "rig_lifeboat", center, normal, profile, 16)


def tower(b, parts, rng):
    structure = parts["structure"]
    rails = parts["rails"]
    x0, x1, y0, y1 = ok.tower
    split = ok.tower_split
    run0, run1 = ok.tower_runs
    levels = ok.tower_levels
    lane_a = (y0 + 0.05, split - 0.05)
    lane_b = (split + 0.05, y1 - 0.05)
    base = ok.landing_z - 0.5
    for cx in (x0, run0, run1, x1):
        for cy in (y0, y1):
            ok.ibeam(structure, "rig_paint_grey", V(cx, cy, base), V(cx, cy, top_z), 0.22, 0.22, V(1.0, 0.0, 0.0))
    for lz in levels[1:-1]:
        for a, c in ((V(x0, y0, lz - 0.15), V(x1, y0, lz - 0.15)), (V(x0, y1, lz - 0.15), V(x1, y1, lz - 0.15)), (V(x0, y0, lz - 0.15), V(x0, y1, lz - 0.15)), (V(x1, y0, lz - 0.15), V(x1, y1, lz - 0.15))):
            ok.channel(structure, "rig_paint_grey", a, c, 0.2, 0.07, up)
    flights = [(lane_a, levels[0], levels[1], "nx"), (lane_b, levels[1], levels[2], "px"), (lane_a, levels[2], levels[3], "nx"), (lane_b, levels[3], levels[4], "px")]
    for index, (lane, z0, z1, direction) in enumerate(flights):
        ok.stair_flight(b, parts, run0, run1, lane[0], lane[1], z0, z1, direction, rng, "rig_paint_yellow", "rig_paint_yellow", (True, True), (False, False), "tower")
    for index, lz in enumerate(levels[1:-1]):
        if index % 2 == 0:
            ok.grating_floor(b, parts, x0, run0, y0, y1, lz, "rig_paint_grey", True, "tower_landing")
        else:
            ok.grating_floor(b, parts, run1, x1, y0, y1, lz, "rig_paint_grey", True, "tower_landing")
    top = top_z + 0.2
    col(b, "metal", "tower_wall", x0, run1, y0 - 0.06, y0 + 0.04, ok.landing_z, top)
    col(b, "metal", "tower_wall", run1, x1, y0 - 0.06, y0 + 0.04, ok.landing_z + 2.3, top)
    col(b, "metal", "tower_wall", x0, x1, y1 - 0.04, y1 + 0.06, ok.landing_z, top)
    col(b, "metal", "tower_wall", x0 - 0.06, x0 + 0.04, y0, y1, ok.landing_z, top)
    col(b, "metal", "tower_wall", x1 - 0.04, x1 + 0.06, y0, y1, ok.landing_z, top)
    col(b, "metal", "tower_divider", run0, run1, split - 0.05, split + 0.05, ok.landing_z, ok.cellar + 1.1)
    cage(structure, rng)


def cage(part, rng):
    x0, x1, y0, y1 = ok.tower
    run0, run1 = ok.tower_runs
    z_top = top_z - 0.1
    sides = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    for (ax, ay), (cx, cy) in sides:
        a = V(ax, ay, 0.0)
        c = V(cx, cy, 0.0)
        length = (c - a).length
        direction = (c - a).normalized()
        outward = V(direction.y, -direction.x, 0.0)
        count = int(length / 0.3)
        for k in range(1, count):
            p = a + direction * (length * k / count) + outward * 0.06
            z_low = ok.landing_z + 0.1
            if ay == y0 and cy == y0 and p.x > run1 - 0.05:
                z_low = ok.landing_z + 2.3
            if rng.random() < 0.05:
                continue
            bend = V(rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 0.0) if rng.random() < 0.15 else V(0.0, 0.0, 0.0)
            ok.bar(part, "rig_paint_grey", V(p.x, p.y, (z_low + z_top) * 0.5) + bend, up, z_top - z_low, 0.05, 0.008, direction, ok.fine)
        hoop = ok.landing_z + 1.2
        while hoop < z_top:
            ok.bar(part, "rig_paint_grey", (a + c) * 0.5 + outward * 0.07 + V(0.0, 0.0, hoop), direction, length, 0.008, 0.06, up, ok.fine)
            hoop += 1.75


def tower_dressing(b, parts, rng):
    x0, x1, y0, y1 = ok.tower
    run0, run1 = ok.tower_runs
    signs = parts["fittings"]
    ok.sign(signs, "cellar_level", V(x1 + 0.08, -16.4, 3.4), V(1.0, 0.0, 0.0), 0.75, 0.15)
    ok.sign(signs, "no_smoking", V(1.2, y0 - 0.1, 3.3), V(0.0, -1.0, 0.0), 0.5, 0.19)
    ok.floodlight(b, signs, parts["lamps"], V(x1 + 0.35, y0 - 0.35, 5.2), V(-0.2, -0.6, -0.6), "cold", True, False, rng, V(x1, y0, 5.2))
    ok.floodlight(b, signs, parts["lamps"], V(x0 - 0.35, y0 - 0.35, 12.0), V(0.3, -0.5, -0.7), "cold", False, True, rng, V(x0, y0, 12.0))
    ok.bulkhead_light(b, signs, V(x0 + 0.05, -16.0, 9.0 + 1.9), V(1.0, 0.0, 0.0), "cold", True)
    ok.hanging_cable(signs, V(x0 + 0.1, -16.8, 14.8), 2.4, rng)
    for z in (6.0, 10.0, 13.5):
        ok.decal(parts["decals"], "run_b", V(x1 + 0.12, -15.6, z), V(1.0, 0.0, 0.0), 0.25, 1.0)
    for lz in (5.5, 12.5):
        ok.floor_decal(parts["decals"], "guano_a", x0 + 0.6, -16.4, lz + 0.006, 0.9, 0.9, rng.uniform(0.0, 6.0))


def leg_dressing(b, parts, rng):
    fittings = parts["fittings"]
    decals = parts["decals"]
    for sx, sy, key in ((-1.0, -1.0, "leg_a1"), (1.0, -1.0, "leg_a2"), (-1.0, 1.0, "leg_b1"), (1.0, 1.0, "leg_b2")):
        z = 8.5
        center = ok.leg_point(sx, sy, z)
        outward = V(sx, sy, 0.0).normalized()
        ok.sign(fittings, key, center + outward * (ok.leg_radius + 0.02), outward, 0.9, 0.45, 0.0, "rig_paint_yellow", 0.015)
        for k in range(3):
            angle = math.atan2(sy, sx) + rng.uniform(-0.9, 0.9)
            n = V(math.cos(angle), math.sin(angle), 0.0)
            zz = rng.choice([5.5 - 1.5, 5.5 + 1.0, 12.0, 14.2])
            ok.decal(decals, rng.choice(["run_a", "run_c", "run_d"]), ok.leg_point(sx, sy, zz) + n * (ok.leg_radius + 0.012), n, 0.3, 1.4)
    for z in (5.5,):
        for sx in (-1.0, 1.0):
            a = ok.leg_point(sx, -1.0, z)
            c = ok.leg_point(sx, 1.0, z)
            for t in (0.3, 0.55, 0.8):
                p = a.lerp(c, t)
                ok.decal(decals, rng.choice(["guano_a", "guano_b"]), p + V(0.0, 0.0, 0.39), up, 0.32, 0.9, 0.0, 0.002)
                ok.decal(decals, "guano_runs", p + V(-sx * 0.4, 0.0, -0.2), V(-sx, 0.0, 0.0), 0.5, 0.6)


def kelp(b, parts, rng):
    part = parts["growth"]
    ribbon = [(-0.035, -0.003), (0.035, -0.003), (0.035, 0.003), (-0.035, 0.003)]
    anchors = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            anchors.append((lambda z, sx=sx, sy=sy: ok.leg_point(sx, sy, z), ok.leg_radius + 0.12, 14))
    for x, y in ok.wells[:3]:
        anchors.append((lambda z, x=x, y=y: V(x, y, z), 0.45, 5))
    for center_fn, radius, count in anchors:
        for k in range(count):
            angle = rng.uniform(0.0, math.pi * 2.0)
            n = V(math.cos(angle), math.sin(angle), 0.0)
            top = rng.uniform(0.2, 1.1)
            length = rng.uniform(0.8, 2.2)
            points = []
            drift = V(rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.0)
            for s in range(6):
                t = s / 5.0
                zz = top - length * t
                base = center_fn(zz)
                points.append(base + n * (radius + 0.03 + 0.12 * t) + drift * t * t)
            emit(part, kit.geo_tube(points, ribbon, True, n), "rig_marine", None, "given", True, None, 3.0)


def capsized(b, parts, rng):
    import buildings as bd
    bd.dinghy(b, parts["fittings"], V(4.2, -23.4, -0.18), 0.35, rng, 2.9, 1.3, 0.48, "painted_wood_blue", "timber_beam", 10, 8, False)
    rope = [V(3.25, landing_y[0] - 0.4, ok.landing_z - 0.6), V(3.4, -22.2, -0.1), V(3.1, -22.9, 0.2)]
    ok.path_tube(parts["fittings"], "rope_net", rope, 0.016, 5, True, 3.0)
    decals = parts["decals"]
    for gx in (-6.5, 0.0, 6.5):
        ok.decal(decals, "runs_wide", V(gx + 0.015, -16.0, ok.landing_z - 0.26), V(1.0, 0.0, 0.0), 1.6, 0.38)
    for px in (-6.5, 0.0, 6.5):
        ok.decal(decals, rng.choice(["run_a", "run_c"]), V(px, landing_y[0] - 0.59, 3.2), V(0.0, -1.0, 0.0), 0.3, 1.4)


def jacket():
    b = kit.Build("rig_jacket", 7101)
    rng = b.rng
    parts = ok.setup(b, (("structure", 50.0), ("growth", 70.0), ("fittings", 45.0), ("rails", 50.0), ("lamps", 30.0), ("grating", 30.0), ("decals", 30.0)))
    legs(b, parts, rng)
    frames(b, parts, rng)
    braces(b, parts, rng)
    verticals(b, parts, rng)
    growth(b, parts, rng)
    boat_landing(b, parts, rng)
    tower(b, parts, rng)
    tower_dressing(b, parts, rng)
    leg_dressing(b, parts, rng)
    kelp(b, parts, rng)
    capsized(b, parts, rng)
    return b


def jacket_far():
    b = kit.Build("rig_jacket_far", 7102)
    part = b.part("shell", 50.0)
    grate = b.part("grating", 30.0)
    floor_z = -16.0
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            foot = ok.leg_point(sx, sy, floor_z)
            head = ok.leg_point(sx, sy, top_z + 0.7)
            banded_tube(part, foot, head, ok.leg_radius, 10, False)
            low = ok.leg_point(sx, sy, -2.8)
            r = ok.leg_radius
            ok.lathe(part, "rig_marine", low, head - foot, [(r, 0.0), (r + 0.13, 0.6), (r + 0.15, 3.3), (r, 4.0)], 8, True, 0.55)
    for z in ok.elevations[1:]:
        corners = {(sx, sy): ok.leg_point(sx, sy, z) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)}
        for a_key, c_key in (((-1.0, -1.0), (1.0, -1.0)), ((-1.0, 1.0), (1.0, 1.0)), ((-1.0, -1.0), (-1.0, 1.0)), ((1.0, -1.0), (1.0, 1.0))):
            banded_tube(part, corners[a_key], corners[c_key], 0.4, 6)
    levels = ok.elevations[1:] + [top_z]
    for index in range(len(levels) - 1):
        z0 = levels[index]
        z1 = levels[index + 1]
        for sy in (-1.0, 1.0):
            banded_tube(part, ok.leg_point(-1.0, sy, z0), ok.leg_point(1.0, sy, z1), 0.34, 6)
            banded_tube(part, ok.leg_point(1.0, sy, z0), ok.leg_point(-1.0, sy, z1), 0.34, 6)
        for sx in (-1.0, 1.0):
            banded_tube(part, ok.leg_point(sx, -1.0, z0), ok.leg_point(sx, 1.0, z1), 0.34, 6)
            banded_tube(part, ok.leg_point(sx, 1.0, z0), ok.leg_point(sx, -1.0, z1), 0.34, 6)
    for x, y in ok.wells:
        banded_tube(part, V(x, y, floor_z), V(x, y, top_z + 0.4), 0.38, 6)
    for x, y in caissons:
        banded_tube(part, V(x, y, floor_z), V(x, y, top_z + 0.7), 0.45, 6)
    for x in riser_xs:
        banded_tube(part, V(x, face_y(floor_z) + 0.9, floor_z), V(x, face_y(top_z + 0.6) + 0.9, top_z + 0.6), 0.25, 6)
    gz = ok.elevations[-1]
    fx = face_x(gz)
    fy = face_y(gz)
    guide = (-8.2, -3.8, 2.4, 6.6)
    for a, c in ((V(-fx, 4.5, gz), V(guide[0], 4.5, gz)), (V(guide[1], 4.5, gz), V(fx, 4.5, gz)), (V(-6.0, -fy, gz), V(-6.0, guide[2], gz)), (V(-6.0, guide[3], gz), V(-6.0, fy, gz))):
        ok.far_tube(part, "rig_paint_yellow", a, c, 0.3, 6)
    gx0, gx1, gy0, gy1 = guide
    for a, c in ((V(gx0, gy0, gz), V(gx1, gy0, gz)), (V(gx0, gy1, gz), V(gx1, gy1, gz)), (V(gx0, gy0, gz), V(gx0, gy1, gz)), (V(gx1, gy0, gz), V(gx1, gy1, gz))):
        ok.far_bar(part, "rig_paint_yellow", a, c, 0.4, 0.4)
    for x, y in caissons:
        ok.far_tube(part, "rig_paint_yellow", V(x, y, gz), V(-fx, y, gz), 0.18, 4)
    landing_far(part, grate)
    tower_far(part, grate)
    emit(part, kit.geo_box(2.9, 1.3, 0.34), "painted_wood_blue", kit.turned(V(4.2, -23.4, -0.02), 0.35), "box")
    return b


def landing_far(part, grate):
    z = ok.landing_z
    x0, x1 = landing_x
    y0, y1 = landing_y
    tx0, tx1, ty0, ty1 = ok.tower
    ok.flat_quad(grate, "rig_grating", x0, x1, y0, y1, z)
    ok.flat_quad(grate, "rig_grating", tx0, tx1, y1, ty1, z)
    face = -face_y(z - 0.3)
    for gx in (-6.5, 0.0, 6.5):
        ok.far_bar(part, "rig_paint_yellow", V(gx, face + 0.6, z - 0.26), V(gx, y0 - 0.3, z - 0.26), 0.22, 0.45)
        ok.far_tube(part, "rig_rust", V(gx, -face_y(-2.6) + 0.3, -2.6), V(gx, -18.4, z - 0.48), 0.13, 4)
    for gy in (y0 - 0.1, y1, ty1):
        ok.far_bar(part, "rig_paint_yellow", V(x0 - 0.3, gy, z - 0.25), V(x1 + 0.3, gy, z - 0.25), 0.2, 0.4)
    for xa in (x0, x1):
        ok.far_bar(part, "rig_paint_yellow", V(xa, y0, z - 0.04), V(xa, y1, z - 0.04), 0.06, 0.08)
    bumper_y = y0 - 0.38
    posts = [-6.5, -3.25, 0.0, 3.25, 6.5]
    for px in posts:
        banded_tube(part, V(px, bumper_y, -3.6), V(px, bumper_y, z + 2.4), 0.2, 6)
        ok.far_tube(part, "rig_rust", V(px, bumper_y, z - 0.25), V(px, y0 + 0.05, z - 0.25), 0.12, 4)
        tube(part, "rig_rubber", V(px, bumper_y - 0.33, -0.7), V(px, bumper_y - 0.33, 1.0), 0.3, 6, True)
    for hz in (-1.8, 0.4, z + 2.2):
        banded_tube(part, V(posts[0], bumper_y, hz), V(posts[-1], bumper_y, hz), 0.14, 4)
    ok.far_rail(part, [(1.0, y0), (x1, y0)], z)
    ok.far_rail(part, [(x1, sea_stair[3] + 0.05), (x1, y1), (tx1 + 0.05, y1)], z)
    ok.far_rail(part, [(-1.0, y0), (x0, y0), (x0, y1), (tx0, y1)], z)
    sx0, sx1, sy0, sy1 = sea_stair
    s0, s1 = sea_stair_z
    ok.far_stair(part, grate, sx0, sx1, sy0, sy1, s0, s1, "nx", "rig_rust")
    for t in (0.1, 0.55):
        x = sx1 - (sx1 - sx0) * t
        banded_tube(part, V(x, -face_y(-6.0) - 0.3, -6.0), V(x, (sy0 + sy1) * 0.5, s0 + (s1 - s0) * t - 0.35), 0.12, 4)


def tower_far(part, grate):
    x0, x1, y0, y1 = ok.tower
    split = ok.tower_split
    run0, run1 = ok.tower_runs
    levels = ok.tower_levels
    base = ok.landing_z - 0.5
    for cx in (x0, run0, run1, x1):
        for cy in (y0, y1):
            ok.far_post(part, "rig_paint_grey", cx, cy, base, top_z, 0.11)
    for lz in levels[1:-1]:
        for a, c in ((V(x0, y0, lz - 0.15), V(x1, y0, lz - 0.15)), (V(x0, y1, lz - 0.15), V(x1, y1, lz - 0.15)), (V(x0, y0, lz - 0.15), V(x0, y1, lz - 0.15)), (V(x1, y0, lz - 0.15), V(x1, y1, lz - 0.15))):
            ok.far_bar(part, "rig_paint_grey", a, c, 0.08, 0.2)
    lane_a = (y0 + 0.05, split - 0.05)
    lane_b = (split + 0.05, y1 - 0.05)
    flights = [(lane_a, levels[0], levels[1], "nx"), (lane_b, levels[1], levels[2], "px"), (lane_a, levels[2], levels[3], "nx"), (lane_b, levels[3], levels[4], "px")]
    for lane, z0, z1, direction in flights:
        ok.far_stair(part, grate, run0, run1, lane[0], lane[1], z0, z1, direction)
    for index, lz in enumerate(levels[1:-1]):
        if index % 2 == 0:
            ok.flat_quad(grate, "rig_grating", x0, run0, y0, y1, lz)
        else:
            ok.flat_quad(grate, "rig_grating", run1, x1, y0, y1, lz)
    z_top = top_z - 0.1
    sides = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    for (ax, ay), (cx, cy) in sides:
        a = V(ax, ay, 0.0)
        c = V(cx, cy, 0.0)
        length = (c - a).length
        direction = (c - a).normalized()
        outward = V(direction.y, -direction.x, 0.0)
        count = int(length / 0.6)
        for k in range(1, count):
            p = a + direction * (length * k / count) + outward * 0.06
            z_low = ok.landing_z + 0.1
            if ay == y0 and cy == y0 and p.x > run1 - 0.05:
                z_low = ok.landing_z + 2.3
            ok.far_box(part, "rig_paint_grey", p.x - abs(direction.x) * 0.04 - abs(outward.x) * 0.01, p.x + abs(direction.x) * 0.04 + abs(outward.x) * 0.01, p.y - abs(direction.y) * 0.04 - abs(outward.y) * 0.01, p.y + abs(direction.y) * 0.04 + abs(outward.y) * 0.01, z_low, z_top, ("top", "bottom"), ok.fine)
