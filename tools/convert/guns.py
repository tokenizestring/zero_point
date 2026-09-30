import bpy
import bmesh
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gunkit as k
import turntable
from gunkit import v

arguments = sys.argv[sys.argv.index("--") + 1:]
source_root = arguments[0]
output_root = arguments[1]
preview_root = arguments[2]
wanted = arguments[3].split(",")
mode = arguments[4] if len(arguments) > 4 else "preview"
views = arguments[5].split(",") if len(arguments) > 5 else ["side", "three", "close", "back", "other", "under"]
samples = int(arguments[6]) if len(arguments) > 6 else 48
hdri = os.path.join(os.path.dirname(output_root), "hdri", "kloofendal_overcast_puresky_4k.hdr")

k.roots["source"] = source_root
k.roots["raw"] = os.path.dirname(output_root)


def grip_point(t, top, bottom, bow):
    return v(top.x + (bottom.x - top.x) * t - bow * math.sin(math.pi * t), 0.0, top.z + (bottom.z - top.z) * t)


def wrap(center_of, t0, t1, turns, width, thickness, lift, tail, exponent=2.8):
    bm = bmesh.new()
    steps = int(turns * 40)
    rings = []
    for s in range(steps + tail + 1):
        u = min(s, steps) / steps
        t = t0 + (t1 - t0) * u
        angle = math.pi * 2.0 * turns * u
        center, side, normal, half_side, half_up, along, front, back, egg = center_of(t)
        c = math.cos(angle)
        sn = math.sin(angle)
        x = math.copysign(abs(c) ** (2.0 / exponent), c)
        y = math.copysign(abs(sn) ** (2.0 / exponent), sn)
        span = half_side * (1.0 - egg * y)
        depth = half_up * (front if y > 0.0 else back)
        outward = (side * x / max(span, 1e-6) + normal * y / max(depth, 1e-6)).normalized()
        base = center + side * x * span + normal * y * depth + outward * lift
        extra = max(s - steps, 0)
        if extra:
            base = base + outward * 0.0011 * extra + along * 0.0016 * extra - side * 0.0008 * extra * extra
        taper = 1.0 - 0.18 * extra
        rings.append([bm.verts.new(base + along * width * 0.5 * taper), bm.verts.new(base - along * width * 0.5 * taper), bm.verts.new(base - along * width * 0.5 * taper + outward * thickness), bm.verts.new(base + along * width * 0.5 * taper + outward * thickness)])
    for i in range(len(rings) - 1):
        for j in range(4):
            n = (j + 1) % 4
            bm.faces.new((rings[i][j], rings[i][n], rings[i + 1][n], rings[i + 1][j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    return k.finish(bm, False)


def clamp(target, x, hull, side, reach, height):
    target.add(k.band(x, hull, 0.0086, 0.0007), "zinc")
    target.add(k.box(0.0096, 0.0054, 0.0118), "zinc", k.place(v(x, side * (reach + 0.0034), height)), 0.0009, 3)
    target.add(k.box(0.0086, 0.0012, 0.0118), "zinc", k.place(v(x, side * (reach + 0.0063), height)), 0.0004, 2)
    k.hex_head(target, v(x, side * (reach + 0.0034), height + 0.0061), v(0.0, 0.0, -1.0), 0.0066, 0.0027, "zinc", False)
    target.add(k.cut(k.revolve([(0.0, 0.0), (0.0024, 0.0), (0.0024, 0.0008), (0.0, 0.0008)], 16), [k.shifted(k.box(0.0006, 0.006, 0.0006), 0.0008)]), "zinc", k.axis_frame(v(x, side * (reach + 0.0034), height + 0.0089), v(0.0, 0.0, 1.0)))


def crimped(radius, height, count=21, depth=0.08):
    outline = []
    for s in range(count * 2):
        angle = math.pi * 2.0 * s / (count * 2)
        r = radius * (1.0 if s % 2 == 0 else 1.0 - depth)
        outline.append((r * math.cos(angle), r * math.sin(angle)))
    return k.shifted(k.extrude(outline, height, "z"), 0.0, 0.0, height * 0.5)


def knurled(radius, start, end, ridges):
    loop = [(0.0, start), (radius * 0.9, start)]
    pitch = (end - start) / ridges
    for index in range(ridges):
        x = start + pitch * index
        loop += [(radius, x + pitch * 0.25), (radius * 0.94, x + pitch * 0.75)]
    loop += [(radius * 0.9, end), (0.0, end)]
    return k.revolve(loop, 28)


def rifle():
    body = k.assembly("scrap_rifle_body")
    bolt = k.assembly("scrap_rifle_bolt")
    axis = 0.036
    at = k.place(v(0.0, 0.0, axis))
    rb = 0.01
    rr = 0.0167
    rri = 0.0133
    body.add(k.revolve([(0.0052, -0.05), (rb, -0.05), (rb, 0.545), (0.0052, 0.545)], 40), "iron", at)
    brake = k.revolve([(rb + 0.0001, 0.53), (0.0137, 0.53), (0.0145, 0.5308), (0.0145, 0.5752), (0.0137, 0.576), (0.0063, 0.576), (0.0063, 0.5722), (0.0119, 0.5716), (0.0119, 0.5462), (rb + 0.0001, 0.5458)], 44)
    holes = [k.transformed(k.revolve([(0.0, -0.022), (0.0021, -0.022), (0.0021, 0.022), (0.0, 0.022)], 14), k.place(v(x, 0.0, 0.0), v(0.0, 1.0, 0.0))) for x in (0.5525, 0.5605, 0.5685)]
    body.add(k.cut(brake, holes), "zinc", at)
    body.add(k.shifted(k.hexagon(0.037, 0.011, "x"), -0.0455), "zinc", at, 0.0008, 2, 50.0)
    body.add(k.revolve([(rb + 0.0001, -0.052), (0.0136, -0.052), (0.0136, -0.04), (rb + 0.0001, -0.04)], 40), "zinc", at, 0.0004, 2)
    receiver = k.revolve([(rri, -0.262), (rr - 0.0007, -0.262), (rr, -0.2613), (rr, -0.0527), (rr - 0.0007, -0.052), (rri, -0.052)], 48)
    arc_center = math.radians(15.0)
    handle_arc = k.transformed(k.box(0.0098, 0.023, 0.02), k.place(v(-0.2365, -math.cos(arc_center) * 0.016, math.sin(arc_center) * 0.016), v(1.0, 0.0, 0.0), v(0.0, math.sin(arc_center), math.cos(arc_center))))
    slot_angle = math.radians(49.0)
    slot = k.transformed(k.box(0.05, 0.0086, 0.02), k.place(v(-0.262, -math.cos(slot_angle) * 0.016, math.sin(slot_angle) * 0.016), v(1.0, 0.0, 0.0), v(0.0, -math.cos(slot_angle), math.sin(slot_angle))))
    port_angle = math.radians(18.0)
    port = k.transformed(k.box(0.058, 0.0135, 0.02), k.place(v(-0.183, -math.cos(port_angle) * 0.016, math.sin(port_angle) * 0.016), v(1.0, 0.0, 0.0), v(0.0, -math.cos(port_angle), math.sin(port_angle))))
    body.add(k.cut(receiver, [handle_arc, slot, port]), "iron", at, 0.0004, 2)
    body.add(k.weld([v(-0.0535, rr * math.cos(a * math.pi / 8.0), axis + rr * math.sin(a * math.pi / 8.0)) for a in range(17)], 0.0016, 31, 0.14, 0.62, 0.75), "iron")
    rail_top = axis + rr
    body.add(k.box(0.132, 0.0082, 0.0042), "steel", k.place(v(-0.164, 0.0, rail_top + 0.0012)), 0.0006, 2)
    for side in (-1.0, 1.0):
        body.add(k.weld([v(-0.228, side * 0.0043, rail_top - 0.0002), v(-0.164, side * 0.0044, rail_top - 0.0001), v(-0.1, side * 0.0043, rail_top - 0.0002)], 0.0011, 41 + int(side * 3), 0.16, 0.6, 0.7), "iron")
    scope_z = rail_top + 0.0033 + 0.0105 + 0.0125
    for x in (-0.208, -0.119):
        body.add(k.box(0.012, 0.0092, 0.0105), "steel", k.place(v(x, 0.0, rail_top + 0.0033 + 0.0052)), 0.0007, 2)
        mount = k.outline_hull([(0.0, scope_z, 0.0125), (-0.0038, rail_top + 0.004, 0.0024), (0.0038, rail_top + 0.004, 0.0024)], 0.00012)
        clamp(body, x, mount, 1.0, 0.0125, scope_z)
    scope = k.place(v(0.0, 0.0, scope_z))
    body.add(k.revolve([(0.0112, -0.236), (0.0125, -0.236), (0.0125, -0.095), (0.0112, -0.095)], 44), "painted", scope, 0.0003, 2)
    body.add(k.revolve([(0.0126, -0.1), (0.0152, -0.1), (0.0159, -0.0993), (0.0159, -0.0718), (0.0152, -0.071), (0.0128, -0.071), (0.0128, -0.0755), (0.0126, -0.0755)], 44), "zinc", scope)
    body.add(k.revolve([(0.0, -0.075), (0.0128, -0.075), (0.0128, -0.0744), (0.0, -0.0744)], 36), "glass", scope)
    body.add(k.revolve([(0.0108, -0.262), (0.0149, -0.262), (0.0154, -0.2605), (0.0154, -0.2375), (0.0131, -0.2355), (0.0131, -0.2335), (0.0108, -0.2335)], 40), "rubber", scope, 0.0004, 2)
    body.add(k.revolve([(0.0, -0.2455), (0.0112, -0.2455), (0.0112, -0.2449), (0.0, -0.2449)], 36), "glass", scope)
    body.add(crimped(0.0092, 0.0068), "steel", k.place(v(-0.166, 0.0, scope_z + 0.0118)), 0.0003, 1)
    body.add(crimped(0.0092, 0.0068), "steel", k.place(v(-0.166, 0.0118, scope_z), v(1.0, 0.0, 0.0), v(0.0, 1.0, 0.0)), 0.0003, 1)
    stock = [(-0.112, 0.004, 0.011, 0.013, 1.0), (-0.118, 0.004, 0.0135, 0.0152, 1.0), (-0.14, 0.003, 0.0155, 0.0165, 1.0), (-0.2, 0.002, 0.0172, 0.0172, 1.0), (-0.255, 0.003, 0.0178, 0.0178, 1.0), (-0.28, 0.004, 0.0184, 0.0172, 1.06), (-0.3, 0.002, 0.018, 0.0162, 1.25), (-0.33, -0.001, 0.019, 0.0165, 1.55), (-0.36, -0.004, 0.024, 0.017, 1.45), (-0.4, -0.007, 0.03, 0.018, 1.22), (-0.46, -0.01, 0.037, 0.0192, 1.06), (-0.54, -0.013, 0.044, 0.0202, 1.0), (-0.62, -0.016, 0.049, 0.0208, 1.0), (-0.69, -0.018, 0.0525, 0.0212, 1.0), (-0.699, -0.018, 0.0524, 0.0211, 1.0)]
    stations = []
    for x, z, half_up, half_side, back in stock:
        stations.append((v(x, 0.0, z), half_side, half_up, 1.0, back, 0.06))
    body.add(k.loft(stations, 48, 3.0, v(0.0, 0.0, 1.0), 0.012, 51), "wood_long")
    pad = []
    for x in (-0.699, -0.7005, -0.713, -0.7155):
        shrink = 1.0 if x > -0.713 else 0.96
        pad.append((v(x, 0.0, -0.018), 0.0212 * shrink, 0.0526 * shrink, 1.0, 1.0, 0.06))
    treads = [k.transformed(k.box(0.006, 0.05, 0.0022), k.place(v(-0.7162, 0.0, -0.018 + offset))) for offset in (-0.036, -0.024, -0.012, 0.0, 0.012, 0.024, 0.036)]
    body.add(k.cut(k.loft(pad, 48, 3.0, v(0.0, 0.0, 1.0)), treads), "rubber", None, 0.0005, 2)
    for z in (-0.052, -0.018, 0.016):
        k.screw(body, v(-0.7142, 0.0, z), v(1.0, 0.0, 0.0), 0.0027, "steel", True)
    cheek_x = (-0.415, -0.565)
    cheek = []
    for index in range(9):
        t = index / 8.0
        x = cheek_x[0] + (cheek_x[1] - cheek_x[0]) * t
        round_end = math.sin(math.pi * t) ** 0.35
        cheek.append((v(x, 0.0203 + 0.0046 * round_end, 0.009 - 0.004 * t), 0.0028 * round_end + 0.0004, 0.0165 * round_end + 0.001))
    body.add(k.loft(cheek, 24, 2.2, v(0.0, 0.0, 1.0), 0.05, 61), "cloth")
    def section(x):
        for index in range(len(stock) - 1):
            a = stock[index]
            b = stock[index + 1]
            if b[0] <= x <= a[0]:
                t = (x - a[0]) / (b[0] - a[0])
                return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 5))
        return stock[-1][1:]

    def lace(x, clearance):
        z, half_up, half_side, back = section(x)
        pad_t = (x - cheek_x[0]) / (cheek_x[1] - cheek_x[0])
        pad_z = 0.009 - 0.004 * pad_t
        points = []
        for s in range(49):
            theta = math.pi * 2.0 * s / 48.0
            c = math.cos(theta)
            sn = math.sin(theta)
            xs = math.copysign(abs(c) ** (2.0 / 3.0), c)
            ys = math.copysign(abs(sn) ** (2.0 / 3.0), sn)
            width = half_side * (1.0 - 0.06 * ys)
            depth = half_up * (1.0 if ys > 0.0 else back)
            y = -xs * width
            height = z + ys * depth
            outward = v(0.0, -xs / max(width, 1e-6), ys / max(depth, 1e-6)).normalized()
            bump = 0.0056 * math.exp(-((height - pad_z) / 0.013) ** 2) if y > 0.0 else 0.0
            points.append(v(x, y, height) + outward * (clearance + bump))
        return points

    for x in (-0.43, -0.49, -0.55):
        body.add_many(k.rope(lace(x, 0.0021), 0.0019, 2, 3.2, 7), "rope")
    forend = []
    for index in range(12):
        t = index / 11.0
        x = -0.045 + 0.345 * t
        taper = 1.0 - 0.18 * t
        tip = 1.0 if t < 0.97 else 0.82
        forend.append((v(x, 0.0, 0.0155 + 0.0012 * t), 0.0138 * taper * tip, 0.0105 * taper * tip))
    forend.insert(0, (v(-0.0475, 0.0, 0.0155), 0.0125, 0.0094))
    body.add(k.loft(forend, 40, 3.2, v(0.0, 0.0, 1.0), 0.012, 71), "wood_long")
    for x in (0.068, 0.255):
        taper = 1.0 - 0.18 * (x + 0.045) / 0.345
        center = 0.0155 + 0.0012 * (x + 0.045) / 0.345
        hull = k.outline_hull([(0.0, axis, rb), (-0.0068 * taper, center - 0.0035 * taper, 0.0068 * taper), (0.0068 * taper, center - 0.0035 * taper, 0.0068 * taper)], 0.0002)
        clamp(body, x, hull, 1.0, 0.0136 * taper, center - 0.0035 * taper)

    def forend_frame(t):
        x = -0.03 + 0.085 * t
        taper = 1.0 - 0.18 * (x + 0.045) / 0.345
        return v(x, 0.0, 0.0155 + 0.0012 * (x + 0.045) / 0.345), v(0.0, 1.0, 0.0), v(0.0, 0.0, 1.0), 0.0138 * taper, 0.0105 * taper, v(1.0, 0.0, 0.0), 1.0, 1.0, 0.0

    body.add(wrap(forend_frame, 0.0, 1.0, 4.6, 0.0142, 0.0008, 0.0007, 4), "cloth")
    trigger = k.fillet([(-0.221, 0.006), (-0.211, 0.006), (-0.2105, -0.006), (-0.2092, -0.014), (-0.2105, -0.021), (-0.2145, -0.0268), (-0.2198, -0.0288), (-0.2202, -0.0268), (-0.2168, -0.0236), (-0.2146, -0.0172), (-0.2145, -0.0092), (-0.2165, -0.003)], [0.001, 0.001, 0.003, 0.004, 0.004, 0.003, 0.0012, 0.0012, 0.003, 0.004, 0.003, 0.002], 5)
    body.add(k.extrude(trigger, 0.0045, "y"), "blued", None, 0.0005, 2)
    guard = k.spline([v(-0.172, 0.0, -0.0149), v(-0.1765, 0.0, -0.022), v(-0.188, 0.0, -0.0335), v(-0.205, 0.0, -0.0385), v(-0.224, 0.0, -0.0372), v(-0.2415, 0.0, -0.0285), v(-0.257, 0.0, -0.0196), v(-0.272, 0.0, -0.0161)], 10)
    body.add(k.sweep(guard, k.rectangle(0.0022, 0.0105), up=v(0.0, 1.0, 0.0)), "blued", None, 0.0005, 2)
    k.screw(body, v(-0.1725, 0.0, -0.016), v(0.0, 0.0, 1.0), 0.0028, "steel", True)
    k.screw(body, v(-0.2715, 0.0, -0.0172), v(0.0, 0.0, 1.0), 0.0028, "steel", True)
    for x, z in ((-0.15, -0.013), (-0.232, -0.0148)):
        k.hex_head(body, v(x, 0.0, z), v(0.0, 0.0, 1.0), 0.0082, 0.0034, "zinc")
    for x, z in ((-0.62, -0.065), (0.205, 0.0073)):
        body.add(k.revolve([(0.0, 0.0), (0.0015, 0.0), (0.0015, 0.005), (0.0, 0.005)], 12), "steel", k.axis_frame(v(x, 0.0, z - 0.003), v(0.0, 0.0, 1.0)))
        k.ring(body, v(x, 0.0, z - 0.0062), v(0.0, 1.0, 0.0), 0.0034, 0.001, "steel")
        k.ring(body, v(x, 0.0, z - 0.0132), v(1.0, 0.0, 0.0), 0.0078, 0.0011, "steel")
    k.screw(body, v(-0.305, 0.0161, 0.004), v(0.0, -1.0, 0.0), 0.0026, "brass", True)
    k.screw(body, v(-0.162, 0.0168, 0.004), v(0.0, -1.0, 0.0), 0.0026, "brass", True)
    for x, lift, radius in ((-0.25, -0.0043, 0.0105), (-0.132, -0.003, 0.0087)):
        loop = k.outline_hull([(0.0, axis, rr), (-(0.0178 - radius), lift, radius), (0.0178 - radius, lift, radius)], 0.0003)
        body.add(k.band(x, loop, 0.0095, 0.0011), "blued", None, 0.0003, 1)
    bolt_at = k.place(v(0.0, 0.0, axis))
    bolt.add(k.revolve([(0.0, -0.262), (0.0127, -0.262), (0.0127, -0.128), (0.0118, -0.1272), (0.0, -0.1272)], 40), "blued", bolt_at)
    bolt.add(knurled(0.0118, -0.2885, -0.262, 9), "steel", bolt_at, 0.0002, 1)
    bolt.add(k.revolve([(0.0, -0.2912), (0.0065, -0.2912), (0.0078, -0.2885), (0.0, -0.2885)], 24), "steel", bolt_at)
    handle = k.spline([v(-0.2365, -0.0106, 0.0324), v(-0.2368, -0.0172, 0.0302), v(-0.2375, -0.0265, 0.0268), v(-0.2385, -0.0335, 0.0224), v(-0.2398, -0.0372, 0.0196)], 10)
    bolt.add(k.sweep(handle, k.circle(0.0034, 14), up=v(1.0, 0.0, 0.0)), "blued")
    bolt.add(k.weld([v(-0.2365 + 0.0046 * math.cos(a * math.pi / 6.0), -0.0122, 0.0318 + 0.0046 * math.sin(a * math.pi / 6.0)) for a in range(13)], 0.0012, 81, 0.12, 0.7, 0.8), "iron")
    bolt.add(k.sphere(0.0068, 22, 14), "blued", k.place(v(-0.2402, -0.0392, 0.0183)), 0.0, 1)
    return [body.build(), bolt.build()]


def pistol():
    barrels = k.assembly("pipe_pistol_barrels")
    frame = k.assembly("pipe_pistol_frame")
    ro = 0.0106
    ri = 0.0079
    upper = 0.058
    lower = 0.036
    rc = 0.0133
    for z, muzzle in ((upper, 0.153), (lower, 0.143)):
        at = k.place(v(0.0, 0.0, z))
        barrels.add(k.revolve([(ri, -0.022), (ro - 0.0008, -0.022), (ro, -0.0212), (ro, muzzle - 0.0009), (ro - 0.0009, muzzle), (ri + 0.0007, muzzle), (ri, muzzle - 0.0008)], 44), "iron", at)
        barrels.add(k.revolve([(ro + 0.0001, -0.0245), (rc - 0.0008, -0.0245), (rc, -0.0237), (rc, -0.0205), (rc - 0.0006, -0.0199), (rc - 0.0006, -0.0189), (rc, -0.0183), (rc, -0.0047), (rc - 0.0006, -0.0041), (rc - 0.0006, -0.0031), (rc, -0.0025), (rc, -0.0017), (rc - 0.0008, -0.0009), (ro + 0.0001, -0.0009)], 44), "zinc", at)
        barrels.add(k.revolve([(0.0, -0.0239), (0.0094, -0.0239), (0.0094, -0.0228), (0.0082, -0.0225), (0.0082, -0.019), (0.0, -0.019)], 36), "brass", at, 0.00015, 1)
        barrels.add(k.revolve([(0.0, -0.02415), (0.0027, -0.02415), (0.0027, -0.0236), (0.0, -0.0236)], 20), "brass", at, 0.0001, 1)
    for side in (-1.0, 1.0):
        for index, (start, end) in enumerate(((0.012, 0.031), (0.066, 0.088), (0.117, 0.136))):
            barrels.add(k.weld([v(start, side * 0.0066, 0.047), v((start + end) * 0.5, side * 0.0069, 0.0471), v(end, side * 0.0066, 0.047)], 0.0019, 11 + index + int(side * 5)), "iron")
    hull = k.outline_hull([(0.0, upper, ro), (0.0, lower, ro)], 0.00012)
    for x in (0.045, 0.106):
        clamp(barrels, x, hull, 1.0, ro, 0.047)
    top = upper + ro
    barrels.add(k.revolve([(0.0, 0.0), (0.0017, 0.0), (0.0017, 0.0046), (0.0012, 0.0062), (0.0, 0.0064)], 18), "steel", k.place(v(0.141, 0.0, top - 0.0006), v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)), 0.0002, 2)
    barrels.add(k.sphere(0.0019, 18, 12), "brass", k.place(v(0.141, 0.0, top + 0.0063)))
    barrels.add(k.weld([v(0.141 + 0.0024 * math.cos(a * math.pi / 6.0), 0.0024 * math.sin(a * math.pi / 6.0), top + 0.0002) for a in range(13)], 0.0011, 5, 0.1, 0.8, 0.8), "iron")
    lug = k.fillet([(0.035, 0.035), (0.069, 0.035), (0.069, 0.021), (0.0598, 0.0094), (0.051, 0.0083), (0.0422, 0.0094), (0.035, 0.021)], [0.0008, 0.0008, 0.004, 0.005, 0.006, 0.005, 0.004], 5)
    for side in (-1.0, 1.0):
        barrels.add(k.extrude(lug, 0.003, "y"), "iron", k.place(v(0.0, side * 0.0107, 0.0)), 0.0006, 3)
        barrels.add(k.weld([v(0.037, side * 0.0118, 0.0361), v(0.052, side * 0.0118, 0.0363), v(0.067, side * 0.0118, 0.0361)], 0.0014, 21 + int(side * 3)), "iron")
    plate = k.fillet([(-0.0148, 0.012), (0.0148, 0.012), (0.0148, 0.066), (0.0102, 0.0726), (-0.0102, 0.0726), (-0.0148, 0.066)], [0.0015, 0.0015, 0.004, 0.003, 0.003, 0.004], 5)
    frame.add(k.extrude(plate, 0.0065, "x"), "blued", k.place(v(-0.0279, 0.0, 0.0)), 0.0007, 3)
    for z in (upper, lower):
        frame.add(k.revolve([(0.0, -0.0247), (0.0011, -0.0247), (0.0011, -0.0239), (0.0006, -0.0237), (0.0, -0.0237)], 14), "steel", k.place(v(0.0, 0.0, z)))
    frame.add(k.box(0.004, 0.009, 0.006), "steel", k.place(v(-0.0331, 0.0, 0.047)), 0.0005, 2)
    side_plate = k.fillet([(-0.061, 0.006), (0.04, 0.006), (0.062, 0.012), (0.062, 0.022), (0.052, 0.0285), (0.03, 0.0285), (0.012, 0.0338), (-0.023, 0.0338), (-0.029, 0.047), (-0.045, 0.0515), (-0.058, 0.044), (-0.063, 0.028)], [0.003, 0.006, 0.006, 0.006, 0.004, 0.006, 0.004, 0.003, 0.006, 0.008, 0.006, 0.004], 5)
    for side in (-1.0, 1.0):
        frame.add(k.extrude(side_plate, 0.003, "y"), "painted", k.place(v(0.0, side * 0.014, 0.0)), 0.0006, 3)
    for x, z, across, radius in ((0.051, 0.0168, 0.0076, 0.0024), (-0.012, 0.0125, 0.0068, 0.0021), (0.021, 0.0125, 0.0068, 0.0021)):
        k.hex_head(frame, v(x, -0.0155, z), v(0.0, 1.0, 0.0), across, 0.0031, "zinc")
        k.nut(frame, v(x, 0.0155, z), v(0.0, 1.0, 0.0), across, 0.0034, radius, 0.0022, "zinc")
    for side in (-1.0, 1.0):
        k.screw(frame, v(-0.044, side * 0.0155, 0.041), v(0.0, -side, 0.0), 0.0026, "steel", False, 0.5)
        k.screw(frame, v(-0.0195, side * 0.0155, 0.0123), v(0.0, -side, 0.0), 0.0019, "steel", False, 0.45)
        k.screw(frame, v(-0.051, side * 0.0155, 0.015), v(0.0, -side, 0.0), 0.0029, "brass", True)
        k.screw(frame, v(-0.054, side * 0.0155, 0.035), v(0.0, -side, 0.0), 0.0027, "brass", True)
    frame.add(k.box(0.089, 0.025, 0.023), "wood_dark", k.place(v(-0.0125, 0.0, 0.0175)), 0.0012, 3)
    top_center = v(-0.042, 0.0, 0.026)
    bottom_center = v(-0.064, 0.0, -0.066)

    def grip_shape(t):
        swell = math.sin(math.pi * min(max((t - 0.15) / 0.8, 0.0), 1.0))
        half_side = 0.0121 if t < 0.2 else 0.0121 + 0.0024 * min((t - 0.2) / 0.1, 1.0) + 0.0011 * swell
        half_up = 0.0203 + 0.0006 * swell
        grooves = sum(math.exp(-((t - c) / 0.05) ** 2) for c in (0.47, 0.65, 0.83)) if t > 0.34 else 0.0
        front = 1.0 - 0.055 * grooves
        back = 1.0 + 0.075 * math.sin(math.pi * min(max((t - 0.22) / 0.62, 0.0), 1.0))
        egg = 0.0 if t < 0.2 else 0.13 * min((t - 0.2) / 0.1, 1.0)
        if t > 0.95:
            flare = 1.0 + (t - 0.95) * 1.4
            half_side *= flare
            half_up *= flare
        return half_side, half_up, front, back, egg

    stations = []
    for index in range(33):
        t = index / 32.0
        half_side, half_up, front, back, egg = grip_shape(t)
        stations.append((grip_point(t, top_center, bottom_center, 0.0015), half_side, half_up, front, back, egg))
    last = stations[-1]
    stations.append((grip_point(1.0, top_center, bottom_center, 0.0015) + v(-0.0003, 0.0, -0.0018), last[1] * 0.86, last[2] * 0.9, last[3], last[4], last[5]))
    frame.add(k.loft(stations, 40, 2.8, v(1.0, 0.0, 0.0), 0.014, 41), "wood")

    def grip_frame(t):
        center = grip_point(t, top_center, bottom_center, 0.0015)
        ahead = grip_point(min(t + 0.01, 1.0), top_center, bottom_center, 0.0015)
        behind = grip_point(max(t - 0.01, 0.0), top_center, bottom_center, 0.0015)
        along = (ahead - behind).normalized()
        normal = (v(1.0, 0.0, 0.0) - along * along.x).normalized()
        side = normal.cross(along).normalized()
        half_side, half_up, front, back, egg = grip_shape(t)
        return center, side, normal, half_side, half_up, along, front, back, egg

    frame.add(wrap(grip_frame, 0.4, 0.8, 3.4, 0.0125, 0.0008, 0.0002, 5), "cloth")
    hammer = k.fillet([(-0.0353, 0.051), (-0.0353, 0.0432), (-0.038, 0.0368), (-0.047, 0.0348), (-0.0512, 0.0402), (-0.0552, 0.0524), (-0.0618, 0.0662), (-0.0632, 0.0716), (-0.0568, 0.0738), (-0.049, 0.0622), (-0.0421, 0.0542), (-0.0358, 0.0532)], [0.0008, 0.0008, 0.002, 0.003, 0.003, 0.003, 0.0015, 0.0018, 0.0018, 0.003, 0.002, 0.0012], 4)
    grooves = []
    for index in range(6):
        t = (index + 0.5) / 6.0
        grooves.append(k.transformed(k.box(0.0007, 0.02, 0.0012), k.place(v(-0.0632 + 0.0064 * t, 0.0, 0.0716 + 0.0022 * t + 0.0004), v(0.94, 0.0, 0.33))))
    frame.add(k.cut(k.extrude(hammer, 0.0062, "y"), grooves), "blued", None, 0.0004, 2)
    trigger = k.fillet([(-0.0215, 0.013), (-0.0135, 0.013), (-0.013, 0.004), (-0.0117, -0.003), (-0.013, -0.0095), (-0.017, -0.0148), (-0.0223, -0.0168), (-0.0227, -0.0148), (-0.0193, -0.0118), (-0.0171, -0.0065), (-0.017, 0.0005), (-0.019, 0.006)], [0.001, 0.001, 0.003, 0.004, 0.004, 0.003, 0.0012, 0.0012, 0.003, 0.004, 0.003, 0.002], 5)
    frame.add(k.extrude(trigger, 0.0045, "y"), "blued", None, 0.0005, 2)
    guard = k.spline([v(0.006, 0.0, 0.0062), v(0.0045, 0.0, -0.004), v(-0.0035, 0.0, -0.0178), v(-0.015, 0.0, -0.0238), v(-0.0255, 0.0, -0.0218), v(-0.03, 0.0, -0.0128), v(-0.0293, 0.0, -0.0048)], 10)
    frame.add(k.sweep(guard, k.circle(0.0019, 14), up=v(0.0, 1.0, 0.0)), "iron")
    k.screw(frame, v(0.006, 0.0, 0.0062), v(0.0, 0.0, 1.0), 0.0024, "steel", True)
    k.screw(frame, v(-0.0293, 0.0, -0.0048), v(-1.0, 0.0, 0.2), 0.0024, "steel", True)
    latch = k.spline([v(-0.0305, 0.0, 0.0738), v(-0.021, 0.0, 0.0742), v(-0.0135, 0.0, 0.074), v(-0.0106, 0.0, 0.0718)], 8)
    frame.add(k.sweep(latch, k.rectangle(0.0062, 0.0018), up=v(0.0, 0.0, 1.0)), "steel", None, 0.0003, 2)
    k.screw(frame, v(-0.0275, 0.0, 0.0747), v(0.0, 0.0, -1.0), 0.0022, "steel", True)
    tubing = k.spline([v(-0.0635, 0.0048, 0.0655), v(-0.0653, 0.0, 0.0671), v(-0.0635, -0.0048, 0.0655), v(-0.065, -0.0048, 0.041), v(-0.0672, -0.0045, 0.016), v(-0.0722, -0.0038, 0.0), v(-0.0739, 0.0, -0.0068), v(-0.0722, 0.0038, 0.0), v(-0.0672, 0.0045, 0.016), v(-0.065, 0.0048, 0.041), v(-0.0635, 0.0048, 0.0655)], 8)
    frame.add(k.sweep(tubing, k.circle(0.0016, 12), up=v(1.0, 0.0, 0.0), caps=False), "rubber")
    k.screw(frame, v(-0.0718, 0.0, -0.004), v(1.0, 0.0, 0.0), 0.0026, "brass", True)
    butt = grip_point(1.0, top_center, bottom_center, 0.0015) + v(-0.0003, 0.0, -0.0016)
    frame.add(k.revolve([(0.0, 0.0), (0.0014, 0.0), (0.0014, 0.004), (0.0, 0.004)], 12), "steel", k.axis_frame(butt + v(0.0, 0.0, -0.003), v(0.0, 0.0, 1.0)))
    k.ring(frame, butt + v(0.0, 0.0, -0.0062), v(0.0, 1.0, 0.0), 0.0032, 0.0009, "steel")
    k.ring(frame, butt + v(0.001, 0.0, -0.0145), v(1.0, 0.0, 0.0), 0.0068, 0.00085, "steel")
    return [barrels.build(), frame.build()]


def rounded(hy, hz, radius, segments=4):
    return k.fillet([(-hy, -hz), (hy, -hz), (hy, hz), (-hy, hz)], radius, segments)


def superellipse(half_side, half_up, top, bottom, center, exponent, grow, count=72):
    points = []
    for s in range(count):
        theta = math.pi * 2.0 * s / count
        c = math.cos(theta)
        sn = math.sin(theta)
        x = math.copysign(abs(c) ** (2.0 / exponent), c)
        y = math.copysign(abs(sn) ** (2.0 / exponent), sn)
        points.append((x * (half_side + grow), center + y * (half_up * (top if y > 0.0 else bottom) + grow)))
    return points


def assault():
    body = k.assembly("scrap_ar_body")
    bolt = k.assembly("scrap_ar_bolt")
    mag = k.assembly("scrap_ar_mag")
    axis = 0.036
    at = k.place(v(0.0, 0.0, axis))
    half = 0.016
    wall = 0.0016
    rear = -0.185
    front = 0.025
    roof = axis + half
    floor = axis - half
    middle = (front + rear) * 0.5
    tube = k.shifted(k.extrude(rounded(half, half, 0.0035), front - rear, "x"), middle, 0.0, axis)
    hollow = k.shifted(k.extrude(rounded(half - wall, half - wall, 0.002), front - rear + 0.02, "x"), middle, 0.0, axis)
    port = k.shifted(k.box(0.055, 0.008, 0.0165), -0.1025, -half, axis + 0.0005)
    slot = k.shifted(k.box(0.056, 0.008, 0.0062), -0.122, half, 0.04)
    opening = k.shifted(k.box(0.061, 0.0236, 0.008), -0.018, 0.0, floor)
    body.add(k.cut(tube, [hollow, port, slot, opening]), "primer", None, 0.0004, 2)

    def perimeter(x, grow):
        points = [v(x, a, axis + b) for a, b in rounded(half + grow, half + grow, 0.0035 + grow, 2)]
        return points + [points[0]]

    for x, seed in ((rear - 0.002, 91), (front + 0.002, 92)):
        body.add(k.shifted(k.extrude(rounded(half + 0.0008, half + 0.0008, 0.003), 0.004, "x"), x, 0.0, axis), "primer", None, 0.0006, 2)
    body.add(k.weld(perimeter(rear + 0.0008, 0.0002), 0.0014, 93, 0.15, 0.6, 0.75), "iron")
    body.add(k.weld(perimeter(front - 0.0008, 0.0002), 0.0014, 94, 0.15, 0.6, 0.75), "iron")
    body.add(k.shifted(k.hexagon(0.026, 0.012, "x"), front + 0.01, 0.0, axis), "zinc", None, 0.0008, 2, 50.0)
    body.add(k.revolve([(0.0038, front + 0.004), (0.0092, front + 0.004), (0.0092, 0.4), (0.0038, 0.4)], 40), "iron", at)
    guard_in = 0.0178
    guard_out = 0.0195
    shroud = k.revolve([(guard_in, 0.046), (guard_out, 0.046), (guard_out, 0.254), (guard_in, 0.254)], 48)
    holes = []
    for row in range(8):
        x = 0.07 + row * 0.023
        for column in range(3):
            angle = math.radians(column * 60.0 + (30.0 if row % 2 else 0.0) + 15.0)
            holes.append(k.transformed(k.revolve([(0.0, -0.03), (0.0033, -0.03), (0.0033, 0.03), (0.0, 0.03)], 14), k.place(v(x, 0.0, 0.0), v(0.0, math.cos(angle), math.sin(angle)), v(1.0, 0.0, 0.0))))
    body.add(k.cut(shroud, holes), "zinc", at, 0.0003, 1)
    for x0, x1 in ((0.041, 0.046), (0.254, 0.259)):
        body.add(k.revolve([(0.0093, x0), (0.0197, x0), (0.0197, x1), (0.0093, x1)], 48), "steel", at, 0.0004, 2)
    shroud_hull = k.outline_hull([(0.0, axis, guard_out)], 0.0002)
    for x in (0.058, 0.242):
        clamp(body, x, shroud_hull, 1.0, guard_out, axis)

    def shroud_frame(t):
        return v(0.1 + 0.062 * t, 0.0, axis), v(0.0, 1.0, 0.0), v(0.0, 0.0, 1.0), guard_out, guard_out, v(1.0, 0.0, 0.0), 1.0, 1.0, 0.0

    body.add(wrap(shroud_frame, 0.0, 1.0, 3.3, 0.0196, 0.0012, 0.0004, 4, 2.0), "rubber")
    sight_x = 0.3
    body.add(k.revolve([(0.0093, sight_x - 0.009), (0.0134, sight_x - 0.009), (0.014, sight_x - 0.0082), (0.014, sight_x + 0.0082), (0.0134, sight_x + 0.009), (0.0093, sight_x + 0.009)], 40), "steel", at, 0.0003, 2)
    body.add(k.box(0.012, 0.009, 0.008), "steel", k.place(v(sight_x, 0.0, axis - 0.0165)), 0.0006, 2)
    k.hex_head(body, v(sight_x, -0.0045, axis - 0.0175), v(0.0, 1.0, 0.0), 0.0068, 0.0028, "zinc")
    k.nut(body, v(sight_x, 0.0045, axis - 0.0175), v(0.0, 1.0, 0.0), 0.0068, 0.003, 0.0019, 0.0018, "zinc")
    body.add(k.box(0.012, 0.008, 0.006), "steel", k.place(v(sight_x, 0.0, axis + 0.016)), 0.0005, 2)
    body.add(k.revolve([(0.0, 0.0), (0.0013, 0.0), (0.0013, 0.0155), (0.0009, 0.0168), (0.0, 0.017)], 16), "steel", k.place(v(sight_x, 0.0, 0.055), v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)))
    ear = k.fillet([(-0.006, 0.0), (0.006, 0.0), (0.006, 0.027), (-0.006, 0.027)], [0.0, 0.0, 0.004, 0.004], 4)
    for side in (-1.0, 1.0):
        body.add(k.extrude(ear, 0.0018, "y"), "steel", k.place(v(sight_x, side * 0.0078, 0.046)), 0.0004, 2)
        body.add(k.weld([v(sight_x - 0.0058, side * 0.0066, 0.0515), v(sight_x, side * 0.0067, 0.0513), v(sight_x + 0.0058, side * 0.0066, 0.0515)], 0.0011, 131 + int(side)), "iron")
    muzzle_loop = [(0.0093, 0.392), (0.0118, 0.392), (0.0118, 0.4442), (0.0112, 0.445), (0.0085, 0.445), (0.0085, 0.4), (0.0093, 0.4)]
    slots = [k.transformed(k.shifted(k.box(0.03, 0.03, 0.0022), 0.4335, 0.0, 0.0), k.turn('X', angle)) for angle in (45.0, 135.0)]
    body.add(k.cut(k.revolve(muzzle_loop, 40), slots), "blued", at, 0.0003, 2)
    k.screw(body, v(0.396, 0.0119, axis), v(0.0, -1.0, 0.0), 0.0019, "steel", False, 0.45)
    rear_x = -0.165
    body.add(k.box(0.016, 0.013, 0.0025), "steel", k.place(v(rear_x - 0.003, 0.0, roof + 0.00125)), 0.0005, 2)
    aperture = k.fillet([(-0.0058, 0.0), (0.0058, 0.0), (0.0058, 0.0235), (-0.0058, 0.0235)], [0.0, 0.0, 0.0056, 0.0056], 6)
    peep = k.transformed(k.revolve([(0.0, -0.01), (0.003, -0.01), (0.003, 0.01), (0.0, 0.01)], 24), k.place(v(rear_x, 0.0, 0.072)))
    body.add(k.cut(k.shifted(k.extrude(aperture, 0.0025, "x"), rear_x, 0.0, roof + 0.0025), [peep]), "steel", None, 0.0004, 2)
    body.add(k.revolve([(0.003, -0.0011), (0.0052, -0.0011), (0.0052, 0.0011), (0.003, 0.0011)], 28), "steel", k.place(v(rear_x - 0.0024, 0.0, 0.072)), 0.0003, 1)
    for side in (-1.0, 1.0):
        body.add(k.weld([v(rear_x - 0.01, side * 0.0068, roof + 0.0004), v(rear_x - 0.003, side * 0.0069, roof + 0.0005), v(rear_x + 0.004, side * 0.0068, roof + 0.0004)], 0.001, 141 + int(side)), "iron")
    lower = k.shifted(k.box(0.085, 0.025, 0.021), -0.0925, 0.0, 0.0105)
    body.add(k.cut(lower, [k.shifted(k.box(0.013, 0.006, 0.01), -0.063, 0.0, 0.0)]), "primer", None, 0.0008, 3)
    for side in (-1.0, 1.0):
        body.add(k.weld([v(-0.133, side * 0.0128, 0.0198), v(-0.092, side * 0.0129, 0.0199), v(-0.052, side * 0.0128, 0.0198)], 0.0012, 151 + int(side)), "iron")
    for x, z in ((-0.064, 0.012), (-0.1, 0.014)):
        k.hex_head(body, v(x, -0.0125, z), v(0.0, 1.0, 0.0), 0.0068, 0.0028, "zinc")
        k.nut(body, v(x, 0.0125, z), v(0.0, 1.0, 0.0), 0.0068, 0.003, 0.002, 0.0018, "zinc")
    lever = k.fillet([(-0.004, 0.004), (0.003, 0.0035), (0.018, -0.004), (0.019, -0.0075), (0.016, -0.0085), (-0.004, -0.004)], [0.003, 0.001, 0.001, 0.0015, 0.0015, 0.003], 3)
    body.add(k.extrude(lever, 0.0016, "y"), "steel", k.place(v(-0.127, 0.0137, 0.013)), 0.0003, 1)
    k.screw(body, v(-0.127, 0.0146, 0.013), v(0.0, -1.0, 0.0), 0.0026, "brass", True)
    trigger = k.fillet([(x + 0.152, z) for x, z in ((-0.221, 0.006), (-0.211, 0.006), (-0.2105, -0.006), (-0.2092, -0.014), (-0.2105, -0.021), (-0.2145, -0.0268), (-0.2198, -0.0288), (-0.2202, -0.0268), (-0.2168, -0.0236), (-0.2146, -0.0172), (-0.2145, -0.0092), (-0.2165, -0.003))], [0.001, 0.001, 0.003, 0.004, 0.004, 0.003, 0.0012, 0.0012, 0.003, 0.004, 0.003, 0.002], 5)
    body.add(k.extrude(trigger, 0.0045, "y"), "blued", None, 0.0005, 2)
    guard = k.spline([v(-0.0505, 0.0, 0.0), v(-0.0508, 0.0, -0.013), v(-0.0545, 0.0, -0.026), v(-0.064, 0.0, -0.034), v(-0.077, 0.0, -0.0345), v(-0.0875, 0.0, -0.0302)], 10)
    body.add(k.sweep(guard, k.rectangle(0.0022, 0.0105), up=v(0.0, 1.0, 0.0)), "iron", None, 0.0005, 2)
    body.add(k.weld([v(-0.0515, -0.0048, -0.0004), v(-0.0505, 0.0, -0.0006), v(-0.0515, 0.0048, -0.0004)], 0.0011, 161), "iron")
    body.add(k.weld([v(-0.0868, -0.0046, -0.0296), v(-0.0876, 0.0, -0.0299), v(-0.0868, 0.0046, -0.0296)], 0.0011, 162), "iron")
    well_outer = k.fillet([(-0.05, -0.014), (0.014, -0.014), (0.014, 0.014), (-0.05, 0.014)], 0.002, 3)
    well_inner = k.fillet([(-0.0485, -0.0122), (0.0125, -0.0122), (0.0125, 0.0122), (-0.0485, 0.0122)], 0.001, 3)
    body.add(k.cut(k.shifted(k.extrude(well_outer, 0.029, "z"), 0.0, 0.0, 0.0065), [k.shifted(k.extrude(well_inner, 0.05, "z"), 0.0, 0.0, 0.0065)]), "primer", None, 0.0005, 2)
    for side in (-1.0, 1.0):
        body.add(k.weld([v(-0.049, side * 0.0143, 0.0205), v(-0.018, side * 0.0144, 0.0206), v(0.013, side * 0.0143, 0.0205)], 0.0012, 171 + int(side)), "iron")
    body.add(k.weld([v(0.0145, -0.0125, 0.0203), v(0.0147, 0.0, 0.0204), v(0.0145, 0.0125, 0.0203)], 0.0012, 175), "iron")
    catch = k.spline([v(0.0147, 0.0, 0.016), v(0.0149, 0.0, 0.0), v(0.017, 0.0, -0.009), v(0.02, 0.0, -0.012)], 8)
    body.add(k.sweep(catch, k.rectangle(0.0012, 0.007), up=v(0.0, 1.0, 0.0)), "steel", None, 0.0002, 1)
    k.screw(body, v(0.0155, 0.0, 0.014), v(-1.0, 0.0, 0.0), 0.0022, "steel", True)
    grip_top = v(-0.0928, 0.0, 0.012)
    grip_bottom = v(-0.1281, 0.0, -0.098)

    def grip_shape(t):
        swell = math.sin(math.pi * min(max((t - 0.1) / 0.85, 0.0), 1.0))
        half_side = 0.0128 + 0.0012 * swell
        half_up = 0.0192 + 0.0008 * swell
        grooves = sum(math.exp(-((t - c) / 0.045) ** 2) for c in (0.42, 0.6, 0.78)) if t > 0.32 else 0.0
        front_scale = 1.0 - 0.06 * grooves
        back_scale = 1.0 + 0.08 * math.sin(math.pi * min(max((t - 0.18) / 0.7, 0.0), 1.0))
        if t > 0.95:
            flare = 1.0 + (t - 0.95) * 1.6
            half_side *= flare
            half_up *= flare
        return half_side, half_up, front_scale, back_scale, 0.12

    stations = []
    for index in range(33):
        t = index / 32.0
        half_side, half_up, front_scale, back_scale, egg = grip_shape(t)
        stations.append((grip_point(t, grip_top, grip_bottom, 0.0015), half_side, half_up, front_scale, back_scale, egg))
    last = stations[-1]
    stations.append((grip_point(1.0, grip_top, grip_bottom, 0.0015) + v(-0.0003, 0.0, -0.0018), last[1] * 0.86, last[2] * 0.9, last[3], last[4], last[5]))
    body.add(k.loft(stations, 40, 2.8, v(1.0, 0.0, 0.0), 0.012, 111), "wood")

    def grip_frame(t):
        center = grip_point(t, grip_top, grip_bottom, 0.0015)
        ahead = grip_point(min(t + 0.01, 1.0), grip_top, grip_bottom, 0.0015)
        behind = grip_point(max(t - 0.01, 0.0), grip_top, grip_bottom, 0.0015)
        along = (ahead - behind).normalized()
        normal = (v(1.0, 0.0, 0.0) - along * along.x).normalized()
        side = normal.cross(along).normalized()
        half_side, half_up, front_scale, back_scale, egg = grip_shape(t)
        return center, side, normal, half_side, half_up, along, front_scale, back_scale, egg

    body.add(wrap(grip_frame, 0.34, 0.84, 3.2, 0.0165, 0.0011, 0.0003, 5), "rubber")
    grip_axis = (grip_top - grip_bottom).normalized()
    k.screw(body, grip_point(1.0, grip_top, grip_bottom, 0.0015) + v(-0.0003, 0.0, -0.0035), grip_axis, 0.0028, "steel", True)
    pipe = 0.0134
    body.add(k.shifted(k.hexagon(0.03, 0.014, "x"), rear - 0.011, 0.0, axis), "zinc", None, 0.0008, 2, 50.0)
    body.add(k.revolve([(pipe - 0.0025, rear - 0.016), (pipe, rear - 0.016), (pipe, -0.4), (pipe - 0.0025, -0.4)], 40), "zinc", at)
    body.add(k.helix(v(-0.296, 0.0, axis), v(-0.222, 0.0, axis), pipe + 0.0015, 0.0015, 21.0, 8), "rope")
    for x in (-0.2975, -0.2205):
        body.add(k.revolve([(pipe + 0.0002, x - 0.0022), (pipe + 0.0029, x - 0.0022), (pipe + 0.0032, x), (pipe + 0.0029, x + 0.0022), (pipe + 0.0002, x + 0.0022)], 28), "rope", at)
    butt = [(-0.325, 1.03, 0.0168), (-0.34, 1.25, 0.0172), (-0.37, 2.23, 0.0176), (-0.4, 3.5, 0.018), (-0.43, 4.72, 0.0184), (-0.455, 5.62, 0.0188), (-0.462, 5.72, 0.0188)]
    stock = [(v(x, 0.0, axis), half_side, 0.018, 1.0, back_scale, 0.06) for x, back_scale, half_side in butt]
    body.add(k.loft(stock, 44, 3.0, v(0.0, 0.0, 1.0), 0.012, 121), "wood_long")
    pad = []
    for x in (-0.4618, -0.4632, -0.4742, -0.4762):
        shrink = 1.0 if x > -0.474 else 0.965
        pad.append((v(x, 0.0, axis), 0.0189 * shrink, 0.0181 * shrink, 1.0, 5.72, 0.06))
    treads = [k.transformed(k.box(0.006, 0.05, 0.0022), k.place(v(-0.4768, 0.0, z))) for z in (-0.055, -0.043, -0.031, -0.019, -0.007, 0.005, 0.017, 0.029, 0.041)]
    body.add(k.cut(k.loft(pad, 44, 3.0, v(0.0, 0.0, 1.0)), treads), "rubber", None, 0.0005, 2)
    for z in (-0.044, -0.002, 0.04):
        k.screw(body, v(-0.4745, 0.0, z), v(1.0, 0.0, 0.0), 0.0027, "steel", True)
    k.hex_head(body, v(-0.346, -0.0173, axis), v(0.0, 1.0, 0.0), 0.0084, 0.0034, "zinc")
    k.nut(body, v(-0.346, 0.0173, axis), v(0.0, 1.0, 0.0), 0.0084, 0.0036, 0.0026, 0.0022, "zinc")
    clamp(body, -0.333, superellipse(0.017, 0.018, 1.0, 1.13, axis, 3.0, 0.0003), 1.0, 0.017, axis)
    body.add(k.revolve([(0.0, 0.0), (0.0015, 0.0), (0.0015, 0.005), (0.0, 0.005)], 12), "steel", k.axis_frame(v(-0.43, 0.0, -0.049 - 0.003), v(0.0, 0.0, 1.0)))
    k.ring(body, v(-0.43, 0.0, -0.049 - 0.0062), v(0.0, 1.0, 0.0), 0.0034, 0.001, "steel")
    k.ring(body, v(-0.43, 0.0, -0.049 - 0.0132), v(1.0, 0.0, 0.0), 0.0078, 0.0011, "steel")
    k.ring(body, v(0.242, 0.0, axis - guard_out - 0.0078), v(0.0, 1.0, 0.0), 0.0068, 0.0011, "steel")
    body.add(k.box(0.003, 0.007, 0.017), "steel", k.place(v(-0.1335, -0.0193, axis + 0.001), v(0.5, -0.87, 0.0)), 0.0004, 1)
    body.add(k.weld([v(-0.1318, -0.0163, axis - 0.007), v(-0.1318, -0.0164, axis + 0.001), v(-0.1318, -0.0163, axis + 0.009)], 0.001, 181), "iron")
    carrier_x = -0.1025
    bolt.add(k.box(0.065, 0.0226, 0.0226), "steel", k.place(v(carrier_x, 0.0, axis)), 0.0008, 2)
    bolt.add(k.revolve([(0.0, -0.07), (0.0082, -0.07), (0.0082, -0.0635), (0.0072, -0.063), (0.0012, -0.063), (0.0012, -0.0635), (0.0, -0.0635)], 32), "steel", at)
    bolt.add(k.revolve([(0.0, 0.0), (0.0026, 0.0), (0.0026, 0.0135), (0.0, 0.0135)], 16), "steel", k.place(v(-0.1, 0.0113, 0.04), v(0.0, 1.0, 0.0), v(0.0, 0.0, 1.0)))
    k.nut(bolt, v(-0.1, 0.0167, 0.04), v(0.0, 1.0, 0.0), 0.0085, 0.0034, 0.0026, 0.0, "zinc")
    knob = k.revolve([(0.0, 0.0), (0.0034, 0.0), (0.0037, 0.0018), (0.006, 0.0055), (0.0064, 0.0085), (0.0056, 0.0112), (0.0032, 0.0126), (0.0, 0.013)], 28)
    bolt.add(knob, "wood_dark", k.place(v(-0.1, 0.0209, 0.04), v(0.0, 1.0, 0.0), v(0.0, 0.0, 1.0)))
    radius = 0.3
    length = 0.18
    mag_top = v(-0.018, 0.0, 0.018)

    def along_mag(s):
        phi = s / radius
        return v(mag_top.x + radius * (1.0 - math.cos(phi)), 0.0, mag_top.z - radius * math.sin(phi)), v(math.sin(phi), 0.0, -math.cos(phi)), v(math.cos(phi), 0.0, math.sin(phi))

    def mag_size(s):
        return 0.0114 + 0.0003 * s / length, 0.0296 + 0.0014 * s / length

    stations = []
    for index in range(25):
        s = length * index / 24.0
        center, tangent, depth = along_mag(s)
        half_side, half_up = mag_size(s)
        stations.append((center, half_side, half_up, 1.0, 1.0, 0.0))
    mag.add(k.loft(stations, 40, 6.0, v(1.0, 0.0, 0.0)), "iron", None, 0.0004, 2)
    for side in (-1.0, 1.0):
        for offset in (-0.016, 0.0, 0.016):
            path = []
            scales = []
            for index in range(17):
                u = index / 16.0
                s = 0.022 + 0.14 * u
                center, tangent, depth = along_mag(s)
                half_side, half_up = mag_size(s)
                path.append(center + depth * offset + v(0.0, side * half_side, 0.0))
                taper = min(1.0, u * 5.0, (1.0 - u) * 5.0) ** 0.5
                scales.append((taper, taper))
            mag.add(k.sweep(path, k.ellipse(0.0024, 0.0007, 10), up=v(0.0, side, 0.0), scales=scales), "iron")
    center, tangent, depth = along_mag(length)
    plate = k.extrude(k.fillet([(-0.0128, -0.0322), (0.0128, -0.0322), (0.0128, 0.0332), (-0.0128, 0.0332)], 0.0045, 4), 0.0042, "x")
    mag.add(plate, "steel", k.place(center + tangent * 0.0019, tangent, depth), 0.0006, 2)
    k.screw(mag, center + tangent * 0.004 + depth * 0.012, -tangent, 0.0021, "steel", False, 0.45)

    def tape_frame(t):
        s = 0.128 + 0.018 * t
        center, tangent, depth = along_mag(s)
        half_side, half_up = mag_size(s)
        return center, v(0.0, 1.0, 0.0), depth, half_side, half_up, tangent, 1.0, 1.0, 0.0

    mag.add(wrap(tape_frame, 0.0, 1.0, 2.2, 0.012, 0.0005, 0.0002, 8, 6.0), "rubber")
    round_at = k.place(v(-0.047, 0.0028, mag_top.z + 0.0057), v(1.0, 0.0, 0.0), v(0.0, 0.0, 1.0))
    mag.add(k.revolve([(0.0, 0.0), (0.0057, 0.0), (0.0057, 0.0012), (0.0048, 0.0015), (0.0048, 0.0023), (0.0056, 0.0027), (0.0052, 0.03), (0.0043, 0.0335), (0.0043, 0.0387), (0.0, 0.0387)], 24), "brass", round_at, 0.0002, 1)
    mag.add(k.revolve([(0.0, 0.0385), (0.0039, 0.0385), (0.0039, 0.047), (0.0029, 0.053), (0.0011, 0.0556), (0.0, 0.056)], 24), "brass", round_at)
    for side in (-1.0, 1.0):
        lip = k.spline([v(-0.046, side * 0.0104, mag_top.z - 0.001), v(-0.02, side * 0.0106, mag_top.z - 0.001), v(0.006, side * 0.0104, mag_top.z - 0.001)], 6)
        mag.add(k.sweep(lip, k.ellipse(0.0012, 0.0024, 10), up=v(0.0, 0.0, 1.0)), "blued")
    return [body.build(), bolt.build(), mag.build()]


builders = {"pipe_pistol": pistol, "scrap_rifle": rifle, "scrap_ar": assault}

for name in wanted:
    k.reset()
    directory = os.path.join(output_root, name)
    os.makedirs(directory, exist_ok=True)
    objects = builders[name]()
    print("BUILT", name, sum(len(o.data.polygons) for o in objects), "faces")
    if mode == "preview":
        turntable.render_views(objects, preview_root, name, views, samples, hdri)
    else:
        for obj in objects:
            k.bake_part(obj, directory)
        k.export(os.path.join(directory, name + ".gltf"))
        k.export(os.path.join(preview_root, name + ".glb"), True)
        turntable.render_views(objects, preview_root, name + "_baked", views, samples, hdri)
