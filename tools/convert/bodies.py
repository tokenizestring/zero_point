import math
import numpy
import anatomy
from anatomy import unit, ellipsoid, cone, loft, custom, tube, chain, mirrored, bump, ridge

nubs = {"Finger0": 0.02684, "Finger1": 0.021, "Finger2": 0.02019, "Finger3": 0.02058, "Finger4": 0.0163, "Toe0": 0.08381, "Head": 0.20767}


def joint(skeleton, name):
    return numpy.asarray(skeleton["joints"]["Bip01 " + name], dtype=numpy.float64)


def axes(skeleton, name):
    return numpy.asarray(skeleton["axes"]["Bip01 " + name], dtype=numpy.float64)


def frame(axis, front, lateral):
    w = unit(axis)
    front = numpy.asarray(front, dtype=numpy.float64)
    u = unit(front - w * numpy.dot(front, w))
    v = numpy.cross(w, u)
    if numpy.dot(v, lateral) < 0.0:
        v = -v
    return numpy.stack([u, v, w])


def local_to_world(origin, rows, point):
    return numpy.asarray(origin) + numpy.asarray(point) @ numpy.asarray(rows)


def tilted(rows, tilt):
    orientation = numpy.asarray(rows)
    for axis_index, degrees in (tilt or []):
        orientation = orientation @ anatomy.rotation(orientation[axis_index], degrees).T
    return orientation


def ordered(shapes):
    adds = [s for s in shapes if s.mode == "add"]
    cuts = [s for s in shapes if s.mode in ("cut", "clip")]
    bumps = [s for s in shapes if s.mode == "bump"]
    zones = [s for s in shapes if s.mode == "smooth"]
    return adds + cuts + bumps + zones


def build(skeleton, figure, head=None):
    shapes = []
    shapes += torso(skeleton, figure)
    left = []
    arm_shapes = arm(skeleton, figure)
    left += arm_shapes
    left += hand(skeleton, figure, arm_shapes[:1])
    left += leg(skeleton, figure)
    left += foot(skeleton, figure)
    shapes += left
    shapes += [mirrored(item) for item in left]
    shapes += neck(skeleton, figure, head is None)
    shapes += anchored(skeleton, figure)
    if head is not None:
        shapes.append(head)
        center, radii = figure["mouth_plug"]
        head_scale = figure.get("head_scale", figure["scale"])
        shapes.append(ellipsoid("Bip01 Head", joint(skeleton, "Head") + numpy.asarray(center) * head_scale, tuple(r * head_scale for r in radii), None, 0.002))
    shapes += surface_details(skeleton, figure, ordered(shapes))
    return ordered(shapes)


def anchored(skeleton, f):
    s = f["scale"]
    shapes = []
    for label, name, offset, radii, tilt, blend, mirror in f.get("forms", []):
        item = ellipsoid(label, joint(skeleton, name) + numpy.asarray(offset) * s, tuple(r * s for r in radii), tilted(numpy.eye(3), tilt), blend * s)
        shapes.append(item)
        if mirror:
            shapes.append(mirrored(item))
    for label, name, offset, radii, tilt, amount, power, mirror in f.get("bumps", []):
        item = bump(label, joint(skeleton, name) + numpy.asarray(offset) * s, tuple(r * s for r in radii), amount * s, tilted(numpy.eye(3), tilt), power)
        shapes.append(item)
        if mirror:
            shapes.append(mirrored(item))
    for label, name, points, radii, amount, power, mirror in f.get("ridges", []):
        item = ridge(label, [joint(skeleton, name) + numpy.asarray(p) * s for p in points], [r * s for r in radii], amount * s, power, False, 0.3)
        shapes.append(item)
        if mirror:
            shapes.append(mirrored(item))
    for name, offset, radius, blur in f.get("zones", []):
        item = anatomy.zone("zone", joint(skeleton, name) + numpy.asarray(offset) * s, radius * s, blur * s)
        shapes.append(item)
        shapes.append(mirrored(item))
    return shapes


def surface_frame(shapes, point):
    epsilon = 2e-5
    base = anatomy.evaluate(shapes, numpy.asarray([point]), 0.01)[0]
    gradient = numpy.array([(anatomy.evaluate(shapes, numpy.asarray([point + numpy.array(offset) * epsilon]), 0.01)[0] - base) / epsilon for offset in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))])
    normal = unit(gradient)
    up = numpy.array([0.0, 0.0, 1.0])
    u = unit(numpy.cross(up, normal))
    v = numpy.cross(normal, u)
    return numpy.stack([u, v, normal])


def nipple(label, shapes, guess, spec, rng):
    point = on_surface(shapes, [guess], 12)[0]
    rows = surface_frame(shapes, point)
    normal = rows[2]
    areola, height, tip, length = spec["areola"], spec["raise"], spec["tip"], spec["length"]
    result = [bump(label, point, (areola, areola, areola), height, rows, 5.0)]
    result.append(bump(label, point + normal * height, (tip * 1.35, tip * 1.35, tip * 2.0 + length), length, rows, 3.2))
    result.append(bump(label, point + normal * (height + length * 0.9), (tip * 0.55, tip * 0.55, tip), -length * 0.12, rows, 2.0))
    for index in range(spec["glands"]):
        angle = rng.uniform(0.0, 2.0 * math.pi)
        radius = areola * rng.uniform(0.45, 0.85)
        spot = point + rows[0] * math.cos(angle) * radius + rows[1] * math.sin(angle) * radius
        size = areola * rng.uniform(0.04, 0.065)
        result.append(bump(label, spot, (size, size, size * 2.0), size * 0.55, rows, 2.0))
    return result, point


def surface_details(skeleton, f, shapes):
    details = []
    spec = f.get("nipples")
    if spec:
        rng = numpy.random.default_rng(spec["seed"])
        for side in (1.0, -1.0):
            guess = joint(skeleton, "Spine2") + numpy.asarray(spec["guess"]) * numpy.array([side, 1.0, 1.0]) + numpy.asarray(spec.get("shift", (0.0, 0.0, 0.0))) * (1.0 if side > 0.0 else 0.0)
            items, point = nipple("Bip01 Spine2", shapes, guess, spec, rng)
            details += items
            f.setdefault("landmarks", {})["nipple_l" if side > 0.0 else "nipple_r"] = point
    return details


def torso_surface(skeleton, f):
    hip = joint(skeleton, "Pelvis")
    span = joint(skeleton, "Neck")[2] - hip[2]
    bottom = hip[2] + f["torso"][0][0] * span
    rows = numpy.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    stations = [(hip[2] + h * span - bottom, bf, bb, a, a, nf, nb, cu, 0.0) for h, bf, bb, a, nf, nb, cu in f["torso"]]
    body = loft("Bip01 Spine1", (0.0, hip[1], bottom), rows, stations, 0.0)
    knots = body.data["knots"]
    table = body.data["table"]

    def place(x, h, side, inset):
        z = hip[2] + h * span
        p = anatomy.hermite(knots, table, numpy.array([z - bottom]))[0]
        ratio = min(abs(x) / p[2], 0.999)
        if side == "front":
            depth = p[0] * (1.0 - ratio ** p[4]) ** (1.0 / p[4])
            return numpy.array([x, hip[1] - p[6] - depth + inset, z])
        if side == "back":
            depth = p[1] * (1.0 - ratio ** p[5]) ** (1.0 / p[5])
            return numpy.array([x, hip[1] - p[6] + depth - inset, z])
        return numpy.array([x, hip[1] + side, z])

    return body, place


def torso(skeleton, f):
    body, place = torso_surface(skeleton, f)
    shapes = [body]
    for label, x, h, side, inset, radii, tilt, blend in f["trunk_forms"]:
        item = ellipsoid(label, place(x, h, side, inset), radii, tilted(numpy.eye(3), tilt), blend)
        shapes.append(item)
        if abs(x) > 1e-6:
            shapes.append(mirrored(item))
    for label, x, h, side, inset, radii, tilt, amount, power in f["trunk_bumps"]:
        item = bump(label, place(x, h, side, inset), radii, amount, tilted(numpy.eye(3), tilt), power)
        shapes.append(item)
        if abs(x) > 1e-6:
            shapes.append(mirrored(item))
    for label, points, radii, amount, power in f["trunk_ridges"]:
        item = ridge(label, [place(*p) for p in points], radii, amount, power, False, 0.3)
        shapes.append(item)
        if any(abs(p[0]) > 1e-6 for p in points):
            shapes.append(mirrored(item))
    navel_h, navel_depth = f["navel"]
    s = f["scale"]
    shapes.append(ellipsoid("Bip01 Spine", place(0.0, navel_h, "front", navel_depth + 0.004 * s), (0.0062 * s, 0.011 * s, 0.0075 * s), None, 0.0035 * s, "cut"))
    shapes.append(bump("Bip01 Spine", place(0.0, navel_h + 0.018, "front", 0.0), (0.014 * s, 0.02 * s, 0.009 * s), 0.0016 * s, None, 2.0))
    shapes.append(bump("Bip01 Spine", place(0.0, navel_h, "front", 0.0), (0.022 * s, 0.03 * s, 0.024 * s), -0.0022 * s, None, 2.0))
    if "breast" in f:
        for side in (1.0, -1.0):
            shapes.append(breast(f, place, side))
    return shapes


def breast(f, place, side):
    spec = f["breast"]
    grow = 1.0 + spec["asymmetry"] * (1.0 if side > 0.0 else -1.0)
    base = place(spec["x"] * side, spec["h"], "front", 0.0) + numpy.array([0.0, 0.0, -spec["drop"] * (1.0 if side > 0.0 else 0.0)])
    forward = numpy.array([0.0, -1.0, 0.0])
    lateral = numpy.array([side, 0.0, 0.0])
    up = numpy.array([0.0, 0.0, 1.0])
    outward = unit(forward + lateral * spec["splay"])
    lower_center = base + outward * spec["lower"][0] + up * spec["lower"][1]
    across = unit(numpy.cross(up, outward))
    lower = ellipsoid("breast", lower_center, tuple(r * grow for r in spec["lower"][2]), numpy.stack([across, outward, numpy.cross(outward, across)]))
    slope_rows = numpy.stack([lateral, forward, up]) @ anatomy.rotation(lateral, spec["upper"][3] * side).T
    upper = ellipsoid("breast", base + forward * spec["upper"][0] + up * spec["upper"][1], tuple(r * grow for r in spec["upper"][2]), slope_rows)
    tail = ellipsoid("breast", base + lateral * spec["tail"][0] + up * spec["tail"][1] + forward * spec["tail"][2], spec["tail"][3])
    fold_z = lower_center[2] - spec["lower"][2][2] * grow

    def distance(points):
        value = anatomy.smin(lower.distance(points), upper.distance(points), spec["merge"])
        return anatomy.smin(value, tail.distance(points), spec["merge"])

    def blend_field(points):
        t = numpy.clip((points[:, 2] - fold_z - spec["fold"][2]) / spec["fold"][3], 0.0, 1.0)
        t = t * t * (3.0 - 2.0 * t)
        inner = numpy.clip(1.0 - (points[:, 0] * side) / (spec["x"] * 0.75), 0.0, 1.0)
        return spec["fold"][0] + (spec["fold"][1] - spec["fold"][0]) * t * (1.0 - 0.45 * inner)

    reach = 0.12
    center = base + forward * 0.02
    result = anatomy.shape("custom", "Bip01 Spine2", spec["fold"][1], "add", function=distance, low=center - reach, high=center + reach, blend_field=blend_field)
    f.setdefault("landmarks", {})["breast_l" if side > 0.0 else "breast_r"] = (lower_center, outward, tuple(r * grow for r in spec["lower"][2]))
    return result


def neck(skeleton, f, placeholder=True):
    base = joint(skeleton, "Neck")
    head = joint(skeleton, "Head")
    s = f["scale"]
    top = head + numpy.array([0.0, 0.0, 0.045 * s])
    start = base + numpy.array([0.0, 0.005 * s, -0.045 * s])
    rows = frame(top - start, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
    length = float(numpy.linalg.norm(top - start))
    stations = [(t * length, bf * s, bb * s, a * s, a * s, 2.2, 2.3, cu * s, 0.0) for t, bf, bb, a, cu in f["neck"]]
    shapes = [loft("Bip01 Neck", start, rows, stations, f["blends"]["neck"] * s)]
    if placeholder:
        shapes.append(ellipsoid("Bip01 Head", head + numpy.array([0.0, -0.022, 0.1]) * s, (0.074 * s, 0.096 * s, 0.108 * s), None, 0.02 * s))
        shapes.append(ellipsoid("Bip01 Head", head + numpy.array([0.0, -0.075, 0.02]) * s, (0.05 * s, 0.05 * s, 0.05 * s), None, 0.03 * s))
    for label, points, radii, amount in f["neck_ridges"]:
        item = ridge(label, [base + numpy.asarray(p) * s for p in points], [r * s for r in radii], amount * s, 2.0, False, 0.25)
        shapes.append(item)
        if any(abs(p[0]) > 1e-6 for p in points):
            shapes.append(mirrored(item))
    return shapes


def scaled_stations(stations, s, twist=0.0, girth=None):
    result = []
    for station in stations:
        segment, fraction = station[0], station[1]
        factor = 1.0
        if girth:
            low, high = girth[min(segment, len(girth) - 1)]
            factor = low + (high - low) * min(max(fraction, 0.0), 1.0)
        dims = tuple(x * s * factor for x in station[2:6])
        powers = tuple(station[6:8])
        offsets = tuple(x * s for x in station[8:10])
        extra = (station[10] * twist,) if len(station) > 10 else ()
        result.append((segment, fraction) + dims + powers + offsets + extra)
    return result


def segment_parts(label, origin, rows, length, s, forms, bumps):
    shapes = []
    for t, offset, radii, tilt, blend in forms:
        center = local_to_world(origin, rows, (offset[0] * s, offset[1] * s, t * length))
        shapes.append(ellipsoid(label, center, tuple(r * s for r in radii), tilted(rows, tilt), blend * s))
    for t, offset, radii, amount, power in bumps:
        center = local_to_world(origin, rows, (offset[0] * s, offset[1] * s, t * length))
        shapes.append(bump(label, center, tuple(r * s for r in radii), amount * s, rows, power))
    return shapes


def arm(skeleton, f):
    s = f["scale"]
    shoulder = joint(skeleton, "L UpperArm")
    elbow = joint(skeleton, "L Forearm")
    wrist = joint(skeleton, "L Hand")
    hand_axes = axes(skeleton, "L Hand")
    palmar = hand_axes[1]
    radial = -hand_axes[2]
    lateral = numpy.array([1.0, 0.0, 0.4])
    hs = f["hand_scale"]
    knuckles = wrist + hand_axes[0] * 0.1 * hs
    whole = frame(knuckles - shoulder, (0.0, -1.0, 0.0), lateral)
    twist = math.degrees(math.atan2(float(palmar @ whole[1]), float(palmar @ whole[0])))
    stations = scaled_stations(f["arm"], s, twist, f["arm_girth"])
    for index, station in enumerate(f["palm"]):
        frac, bf, bb, ap, an, nf, nb, dp, dr = station
        offset = palmar * dp * hs + radial * dr * hs
        stations.append((2, frac, bf * hs, bb * hs, ap * hs, an * hs, nf, nb, float(offset @ whole[0]), float(offset @ whole[1]), twist))
    shapes = [chain("Bip01 L UpperArm", [shoulder, elbow, wrist, knuckles], (0.0, -1.0, 0.0), lateral, stations, f["blends"]["arm"] * s)]
    upper_rows = frame(elbow - shoulder, (0.0, -1.0, 0.0), lateral)
    shapes += segment_parts("Bip01 L UpperArm", shoulder, upper_rows, float(numpy.linalg.norm(elbow - shoulder)), s, f["upper_arm_forms"], f["upper_arm_bumps"])
    fore_rows = frame(wrist - elbow, palmar, radial)
    fore_length = float(numpy.linalg.norm(wrist - elbow))
    shapes += segment_parts("Bip01 L Forearm", elbow, fore_rows, fore_length, s, f["forearm_forms"], f["forearm_bumps"])
    for points, radius, amount in f["forearm_veins"]:
        guesses = [local_to_world(elbow, fore_rows, (u * s * 1.4, v * s * 1.4, t * fore_length)) for t, u, v in points]
        path = on_surface(shapes[:1], guesses)
        shapes.append(ridge("Bip01 L Forearm", path, [radius * s] * len(path), amount * s, 2.0, True, 0.2))
    return shapes


def leg(skeleton, f):
    s = f["scale"]
    hip = joint(skeleton, "L Thigh")
    knee = joint(skeleton, "L Calf")
    ankle = joint(skeleton, "L Foot")
    shapes = [chain("Bip01 L Thigh", [hip, knee, ankle], (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), scaled_stations(f["leg"], s, 0.0, f["leg_girth"]), f["blends"]["leg"] * s)]
    thigh_rows = frame(knee - hip, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
    shapes += segment_parts("Bip01 L Thigh", hip, thigh_rows, float(numpy.linalg.norm(knee - hip)), s, f["thigh_forms"], f["thigh_bumps"])
    calf_rows = frame(ankle - knee, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
    shapes += segment_parts("Bip01 L Calf", knee, calf_rows, float(numpy.linalg.norm(ankle - knee)), s, f["calf_forms"], f["calf_bumps"])
    return shapes


def foot_frame(skeleton):
    ankle = joint(skeleton, "L Foot")
    ball = joint(skeleton, "L Toe0")
    forward = ball - ankle
    forward[2] = 0.0
    forward = unit(forward)
    up = numpy.array([0.0, 0.0, 1.0])
    lateral = numpy.cross(forward, up)
    if lateral[0] < 0.0:
        lateral = -lateral
    origin = numpy.array([ankle[0], ankle[1], 0.0])
    return origin, numpy.stack([up, lateral, forward])


def foot_point(origin, rows, s, point):
    forward, lateral, up = point
    return local_to_world(origin, rows, (up * s, lateral * s, forward * s))


def foot(skeleton, f):
    s = f["foot_scale"]
    origin, rows = foot_frame(skeleton)
    shapes = [loft("Bip01 L Foot", origin, rows, [(w * s, bf * s, bb * s, ap * s, an * s, nf, nb, cu * s, cv * s) for w, bf, bb, ap, an, nf, nb, cu, cv in f["foot"]], f["blends"]["foot"] * s)]
    for label, point, radii, blend in f["foot_forms"]:
        shapes.append(ellipsoid(label, foot_point(origin, rows, s, point), tuple(r * s for r in (radii[2], radii[1], radii[0])), rows, blend * s))
    for label, point, radii, amount, power in f["foot_bumps"]:
        shapes.append(bump(label, foot_point(origin, rows, s, point), tuple(r * s for r in (radii[2], radii[1], radii[0])), amount * s, rows, power))
    for label, points, radii, amount in f["foot_ridges"]:
        shapes.append(ridge(label, [foot_point(origin, rows, s, p) for p in points], [r * s for r in radii], amount * s))
    for points, width, height, nail in f["toes"]:
        shapes += digit("Bip01 L Toe0", [foot_point(origin, rows, s, p) for p in points], rows[0], rows[1], width * s, height * s, nail, s, f["toe_profile"], f["toe_blend"])
    return shapes


def profile_reach(profile, count):
    table = profile[count] if isinstance(profile, dict) else profile
    return max(station[1] for station in table if station[0] == count - 1)


def on_surface(shapes, points, iterations=8):
    return anatomy.project(shapes, numpy.asarray(points, dtype=numpy.float64), iterations, 0.004)


def digit(label, points, dorsal, radial, width, height, nail, s, profile, blend, knuckles=(0.00045, 0.0006), creases=0.0002):
    count = len(points) - 1
    stations = []
    for segment, fraction, bf, bb, ap, an, nf, nb, du in (profile[count] if isinstance(profile, dict) else profile):
        stations.append((segment, fraction, bf * height, bb * height, ap * width, an * width, nf, nb, du * height, 0.0))
    item = chain(label, points, dorsal, radial, stations, blend * s)
    shapes = [item]
    last = points[-1] - points[-2]
    rows = frame(last, dorsal, radial)
    length = float(numpy.linalg.norm(last))
    fraction, span, lift, level = nail
    reach = profile_reach(profile, count)
    end = length * (reach - 0.1)
    start = end - length * fraction
    half = width * span
    origin = points[-2]
    shapes.append(nail_plate(label, item, origin, rows, start, end, half, lift * s, height * level))
    side = [(start + (end - start) * a, half * 1.05 * float(nail_width(a))) for a in (0.97, 0.8, 0.6, 0.42, 0.28, 0.17, 0.08, 0.02)]
    outline = side + [(start - 0.00035 * s, 0.0)] + [(w, -v) for w, v in side[::-1]]
    path = settle(item, origin, rows, outline, height * level, height * 1.6)
    shapes.append(ridge(label, path, [0.0007 * s] * len(path), -lift * 0.9 * s, 2.0))
    fold = [(start - 0.0011 * s + (end - start) * a, half * 0.98 * float(nail_width(a))) for a in (0.26, 0.14, 0.05)]
    fold = fold + [(start - 0.0012 * s, 0.0)] + [(w, -v) for w, v in fold[::-1]]
    cuticle = settle(item, origin, rows, fold, height * level, height * 1.6)
    shapes.append(ridge(label, cuticle, [0.0011 * s] * len(cuticle), 0.0002 * s, 2.0))
    for index in range(1, count):
        joint_point = points[index]
        seg_rows = frame(points[index + 1] - points[index - 1], dorsal, radial)
        top = on_surface([item], [joint_point + seg_rows[0] * height * 1.2])[0]
        shapes.append(bump(label, top, (0.0045 * s, width * 0.75, 0.005 * s), knuckles[0] * s, seg_rows, 2.0))
        crease_rows = numpy.stack([seg_rows[2], -seg_rows[0], seg_rows[1]])
        offsets = (-0.0009, 0.0009) if index == 1 and count == 3 else (0.0,)
        for offset in offsets:
            line = [(offset * s + abs(v) * 0.0012 * s, v * width * 1.1) for v in (-1.0, -0.5, 0.0, 0.5, 1.0)]
            shapes.append(anatomy.groove(label, joint_point, crease_rows, line, 0.001 * s, -creases * s, (height * 0.3, height * 1.6), 2.0, 0.18))
        wrinkle_rows = numpy.stack([seg_rows[2], seg_rows[0], seg_rows[1]])
        for offset, extent, depth in (((-0.0021, 0.36, 0.14), (-0.0005, 0.46, 0.2), (0.0011, 0.4, 0.16)) if index == 1 and count == 3 else ((-0.0011, 0.36, 0.14), (0.0005, 0.3, 0.1))):
            line = [(offset * s - v * v * 0.0016 * s, v * width * extent) for v in (-1.0, -0.5, 0.0, 0.5, 1.0)]
            shapes.append(anatomy.groove(label, joint_point, wrinkle_rows, line, 0.0004 * s, -knuckles[1] * depth * s, (height * 0.3, height * 1.5), 2.0, 0.3))
    return shapes


def nail_width(along):
    rounding = numpy.clip((0.34 - numpy.asarray(along, dtype=numpy.float64)) / 0.34, 0.0, 1.0)
    return numpy.sqrt(numpy.clip(1.0 - rounding * rounding, 0.0, 1.0))


def nail_region(points, frame):
    origin, rows, start, end, half, level = frame
    q = (points - origin) @ rows.T
    along = (q[:, 2] - start) / (end - start)
    side = numpy.abs(q[:, 1]) - half * nail_width(along)
    front = numpy.maximum(start - q[:, 2], q[:, 2] - end)
    return numpy.maximum(numpy.maximum(side, front), level - q[:, 0]), along, numpy.abs(q[:, 1]) / half


def nail_plate(label, finger, origin, rows, start, end, half, lift, level):
    frame = (numpy.asarray(origin, dtype=numpy.float64), numpy.asarray(rows, dtype=numpy.float64), start, end, half, level)

    def plate(points):
        return anatomy.smax(finger.distance(points) - lift, nail_region(points, frame)[0], lift * 0.8)

    center = frame[0] + frame[1][2] * (start + end) * 0.5
    reach = (end - start) + half + 0.01
    return anatomy.shape("custom", label, lift * 0.6, "add", function=plate, low=center - reach, high=center + reach, nail=frame)


def settle(item, origin, rows, samples, low, high):
    samples = numpy.asarray(samples, dtype=numpy.float64)
    base = origin + samples[:, :1] * rows[2] + samples[:, 1:2] * rows[1]
    bottom = numpy.full(len(samples), low)
    top = numpy.full(len(samples), high)
    for step in range(26):
        middle = (bottom + top) * 0.5
        inside = item.distance(base + middle[:, None] * rows[0]) < 0.0
        bottom = numpy.where(inside, middle, bottom)
        top = numpy.where(inside, top, middle)
    return on_surface([item], base + ((bottom + top) * 0.5)[:, None] * rows[0], 3)


def finger_points(skeleton, index):
    names = ["L Finger%d" % index, "L Finger%d1" % index, "L Finger%d2" % index]
    points = [joint(skeleton, n) for n in names]
    tip = points[-1] + axes(skeleton, names[-1])[0] * nubs["Finger%d" % index] * skeleton.get("finger_scale", 1.0)
    return names, points + [tip]


def hand(skeleton, f, base):
    s = f["hand_scale"]
    wrist = joint(skeleton, "L Hand")
    hand_axes = axes(skeleton, "L Hand")
    along = hand_axes[0]
    palmar = hand_axes[1]
    ulnar = hand_axes[2]
    hand_rows = numpy.stack([along, palmar, ulnar])

    def at(point):
        return local_to_world(wrist, hand_rows, tuple(c * s for c in point))

    def direction(vector):
        return unit(numpy.asarray(vector) @ hand_rows)

    palm = list(base)
    for center, axis, normal, radii, blend in f["hand_forms"]:
        rows = frame(direction(axis), direction(normal), numpy.cross(direction(axis), direction(normal)))
        palm.append(ellipsoid("Bip01 L Hand", at(center), (radii[0] * s, radii[1] * s, radii[2] * s), rows, blend * s))
    shapes = palm[len(base):]
    for index in range(5):
        names, points = finger_points(skeleton, index)
        dims = f["fingers"][index]
        bone = axes(skeleton, names[0])
        shapes += digit("Bip01 " + names[0], points, -bone[1], -bone[2], dims[0] * s, dims[1] * s, dims[2], s, f["finger_profile"][0 if index == 0 else 1], f["thumb_blend"] if index == 0 else f["finger_blend"])
        if index > 0:
            top = points[0] - palmar * 0.0105 * s - along * 0.002 * s
            shapes.append(bump("Bip01 L Hand", top, (0.0065 * s, 0.011 * s, 0.013 * s), dims[4] * 0.65 * s, numpy.stack([-palmar, ulnar, along]), 2.0))
            start = on_surface(palm, [at(f["ray_bases"][index - 1]) - palmar * 0.03 * s])[0]
            middle = on_surface(palm, [(start + top) * 0.5 - palmar * 0.02 * s])[0]
            shapes.append(ridge("Bip01 L Hand", [start, middle, top], [0.0035 * s, 0.004 * s, 0.0045 * s], f["tendon"] * s, 2.0, False, 0.2))
    for center, radii, amount, power in f["hand_bumps"]:
        shapes.append(bump("Bip01 L Hand", at(center), tuple(r * s for r in radii), amount * s, hand_rows, power))
    for points, radius, amount in f["hand_veins"]:
        path = on_surface(palm, [at(p) for p in points])
        shapes.append(ridge("Bip01 L Hand", path, [radius * s] * len(path), amount * s, 2.0, True, 0.2))
    for points, radius, amount in f["palm_lines"]:
        shapes.append(anatomy.groove("Bip01 L Hand", wrist, hand_rows, [(p[0] * s, p[2] * s) for p in points], radius * s, amount * s, (0.004 * s, 0.045 * s), 2.0, 0.22))
    return shapes


finger_profile_long = [
    (0, -0.55, 0.85, 1.05, 0.95, 0.95, 2.4, 2.3, -0.1),
    (0, -0.3, 0.92, 1.18, 1.03, 1.03, 2.4, 2.3, -0.15),
    (0, 0.0, 0.85, 1.15, 1.03, 1.03, 2.5, 2.3, -0.18),
    (0, 0.3, 0.72, 1.1, 0.97, 0.97, 2.6, 2.3, -0.2),
    (0, 0.6, 0.7, 1.06, 0.94, 0.94, 2.6, 2.3, -0.2),
    (0, 0.88, 0.72, 0.97, 0.95, 0.95, 2.6, 2.4, -0.18),
    (1, 0.0, 0.74, 0.92, 0.96, 0.96, 2.6, 2.4, -0.16),
    (1, 0.15, 0.7, 0.93, 0.92, 0.92, 2.6, 2.4, -0.16),
    (1, 0.5, 0.64, 0.95, 0.88, 0.88, 2.6, 2.3, -0.18),
    (1, 0.85, 0.63, 0.88, 0.86, 0.86, 2.6, 2.4, -0.16),
    (2, 0.0, 0.64, 0.84, 0.86, 0.86, 2.6, 2.4, -0.14),
    (2, 0.25, 0.6, 0.9, 0.85, 0.85, 2.6, 2.3, -0.16),
    (2, 0.55, 0.56, 0.95, 0.84, 0.84, 2.6, 2.2, -0.19),
    (2, 0.82, 0.52, 0.9, 0.8, 0.8, 2.5, 2.2, -0.21),
    (2, 0.95, 0.46, 0.8, 0.74, 0.74, 2.4, 2.1, -0.22),
    (2, 1.03, 0.38, 0.66, 0.64, 0.64, 2.3, 2.1, -0.22),
    (2, 1.08, 0.28, 0.52, 0.5, 0.5, 2.2, 2.0, -0.2),
    (2, 1.115, 0.17, 0.32, 0.32, 0.32, 2.1, 2.0, -0.2),
    (2, 1.135, 0.07, 0.13, 0.14, 0.14, 2.0, 2.0, -0.2),
    (2, 1.145, 0.005, 0.008, 0.008, 0.008, 2.0, 2.0, -0.2),
]

finger_profile_thumb = [
    (0, -0.3, 0.8, 1.12, 0.95, 0.95, 2.3, 2.2, -0.1),
    (0, 0.0, 0.82, 1.22, 1.0, 1.0, 2.3, 2.2, -0.12),
    (0, 0.5, 0.82, 1.14, 0.98, 0.98, 2.4, 2.3, -0.15),
    (1, 0.0, 0.8, 1.0, 0.97, 0.96, 2.5, 2.4, -0.15),
    (1, 0.5, 0.72, 0.98, 0.91, 0.9, 2.6, 2.3, -0.17),
    (2, 0.0, 0.72, 0.9, 0.93, 0.92, 2.6, 2.4, -0.15),
    (2, 0.3, 0.66, 0.95, 0.92, 0.91, 2.6, 2.3, -0.17),
    (2, 0.62, 0.58, 0.98, 0.88, 0.87, 2.6, 2.2, -0.2),
    (2, 0.88, 0.52, 0.9, 0.82, 0.81, 2.5, 2.2, -0.21),
    (2, 1.0, 0.44, 0.82, 0.72, 0.71, 2.4, 2.1, -0.22),
    (2, 1.06, 0.34, 0.62, 0.58, 0.57, 2.3, 2.0, -0.21),
    (2, 1.1, 0.22, 0.4, 0.4, 0.4, 2.2, 2.0, -0.21),
    (2, 1.13, 0.1, 0.18, 0.18, 0.18, 2.0, 2.0, -0.21),
    (2, 1.145, 0.006, 0.008, 0.008, 0.008, 2.0, 2.0, -0.21),
]

toe_profile = {
    2: [
        (0, -0.5, 0.9, 0.9, 0.95, 0.95, 2.3, 2.4, 0.0),
        (0, 0.0, 1.0, 1.0, 1.02, 1.04, 2.4, 2.5, 0.0),
        (0, 0.5, 0.9, 0.98, 0.98, 1.0, 2.5, 2.5, -0.03),
        (1, 0.0, 0.86, 0.95, 0.97, 0.98, 2.5, 2.5, -0.04),
        (1, 0.35, 0.8, 1.02, 0.98, 0.98, 2.5, 2.3, -0.08),
        (1, 0.7, 0.7, 1.0, 0.95, 0.95, 2.5, 2.3, -0.12),
        (1, 0.9, 0.56, 0.84, 0.84, 0.84, 2.3, 2.2, -0.14),
        (1, 1.0, 0.42, 0.62, 0.66, 0.66, 2.2, 2.1, -0.14),
        (1, 1.06, 0.24, 0.36, 0.4, 0.4, 2.1, 2.0, -0.14),
        (1, 1.09, 0.05, 0.07, 0.08, 0.08, 2.0, 2.0, -0.13),
    ],
    3: [
        (0, -0.5, 0.9, 0.9, 0.95, 0.95, 2.3, 2.4, 0.0),
        (0, 0.0, 1.0, 1.0, 1.02, 1.02, 2.4, 2.5, 0.0),
        (0, 0.55, 0.88, 0.9, 0.93, 0.93, 2.5, 2.5, 0.0),
        (1, 0.0, 0.94, 0.86, 0.96, 0.96, 2.5, 2.5, 0.02),
        (1, 0.6, 0.84, 0.86, 0.9, 0.9, 2.5, 2.4, -0.02),
        (2, 0.0, 0.8, 0.88, 0.9, 0.9, 2.5, 2.4, -0.04),
        (2, 0.45, 0.7, 0.98, 0.9, 0.9, 2.5, 2.3, -0.1),
        (2, 0.8, 0.54, 0.88, 0.82, 0.82, 2.4, 2.2, -0.14),
        (2, 0.95, 0.38, 0.6, 0.62, 0.62, 2.2, 2.1, -0.14),
        (2, 1.03, 0.2, 0.3, 0.32, 0.32, 2.1, 2.0, -0.13),
        (2, 1.07, 0.04, 0.06, 0.07, 0.07, 2.0, 2.0, -0.12),
    ],
}


def leg_stations(outer):
    return [
        (0, -0.24, 0.03, 0.035, 0.035, 0.03, 2.0, 2.0, 0.0, 0.0),
        (0, -0.12, 0.058, 0.07, outer[0], 0.05, 2.1, 2.2, 0.0, 0.004),
        (0, -0.03, 0.069, 0.083, outer[1], 0.061, 2.2, 2.3, 0.0, 0.004),
        (0, 0.05, 0.074, 0.084, outer[2], 0.07, 2.2, 2.3, 0.002, 0.0),
        (0, 0.15, 0.077, 0.082, outer[3], 0.074, 2.2, 2.25, 0.004, -0.002),
        (0, 0.3, 0.077, 0.078, outer[4], 0.074, 2.2, 2.2, 0.006, -0.003),
        (0, 0.5, 0.072, 0.07, outer[5], 0.07, 2.2, 2.2, 0.006, -0.004),
        (0, 0.7, 0.063, 0.06, outer[6], 0.063, 2.25, 2.2, 0.005, -0.004),
        (0, 0.85, 0.055, 0.052, 0.057, 0.058, 2.3, 2.3, 0.003, -0.002),
        (0, 0.96, 0.052, 0.05, 0.055, 0.056, 2.4, 2.4, 0.0, 0.0),
        (1, 0.06, 0.047, 0.052, 0.052, 0.054, 2.4, 2.3, 0.0, 0.0),
        (1, 0.14, 0.042, 0.065, 0.052, 0.056, 2.3, 2.15, 0.0, 0.0),
        (1, 0.24, 0.039, 0.076, 0.053, 0.058, 2.3, 2.1, 0.0, 0.0),
        (1, 0.36, 0.036, 0.073, 0.05, 0.055, 2.3, 2.1, 0.0, 0.0),
        (1, 0.5, 0.034, 0.058, 0.044, 0.047, 2.3, 2.1, 0.0, 0.0),
        (1, 0.65, 0.03, 0.042, 0.036, 0.037, 2.3, 2.2, 0.0, 0.0),
        (1, 0.8, 0.028, 0.034, 0.031, 0.032, 2.3, 2.3, 0.0, 0.0),
        (1, 0.92, 0.029, 0.034, 0.031, 0.032, 2.3, 2.3, 0.0, 0.0),
        (1, 1.0, 0.029, 0.033, 0.03, 0.031, 2.3, 2.3, 0.0, 0.0),
        (1, 1.08, 0.021, 0.024, 0.022, 0.022, 2.2, 2.2, 0.0, 0.0),
        (1, 1.16, 0.006, 0.006, 0.006, 0.006, 2.0, 2.0, 0.0, 0.0),
    ]


male = {
    "scale": 1.0,
    "hand_scale": 1.0,
    "foot_scale": 1.0,
    "placeholder_head": True,
    "blends": {"neck": 0.02, "arm": 0.03, "leg": 0.016, "foot": 0.014, "carpus": 0.005, "ray": 0.006},
    "arm_girth": [(1.14, 1.12), (1.1, 1.0), (1.0, 1.0)],
    "leg_girth": [(1.2, 1.1), (1.08, 1.0)],
    "torso": [
        (-0.128, 0.035, 0.05, 0.04, 2.0, 2.0, 0.0),
        (-0.08, 0.06, 0.088, 0.082, 2.1, 2.2, 0.0),
        (-0.024, 0.079, 0.1, 0.122, 2.2, 2.3, 0.0),
        (0.056, 0.09, 0.1, 0.143, 2.2, 2.4, 0.0),
        (0.152, 0.097, 0.094, 0.147, 2.2, 2.35, 0.0),
        (0.232, 0.103, 0.089, 0.147, 2.15, 2.3, 0.0),
        (0.312, 0.106, 0.087, 0.146, 2.1, 2.3, 0.0),
        (0.392, 0.108, 0.091, 0.149, 2.1, 2.3, 0.0),
        (0.472, 0.112, 0.099, 0.155, 2.15, 2.3, 0.0),
        (0.551, 0.115, 0.107, 0.163, 2.2, 2.3, 0.0),
        (0.631, 0.118, 0.113, 0.169, 2.25, 2.3, 0.0),
        (0.711, 0.118, 0.117, 0.173, 2.25, 2.3, 0.0),
        (0.791, 0.113, 0.117, 0.177, 2.2, 2.25, 0.0),
        (0.855, 0.1, 0.111, 0.186, 2.1, 2.2, 0.0),
        (0.903, 0.086, 0.102, 0.188, 2.0, 2.1, 0.0),
        (0.935, 0.073, 0.092, 0.168, 2.0, 2.0, 0.0),
        (0.967, 0.063, 0.084, 0.134, 2.0, 2.0, 0.0),
        (0.999, 0.057, 0.076, 0.098, 2.0, 2.0, 0.0),
        (1.023, 0.053, 0.069, 0.08, 2.0, 2.0, 0.0),
        (1.047, 0.05, 0.064, 0.07, 2.0, 2.0, 0.0),
    ],
    "trunk_forms": [
        ("Bip01 Pelvis", 0.078, -0.03, 0.058, 0.0, (0.082, 0.052, 0.088), [(1, 8.0)], 0.035),
        ("Bip01 Pelvis", 0.112, 0.09, 0.03, 0.0, (0.036, 0.045, 0.05), [], 0.035),
        ("Bip01 Spine2", 0.166, 0.795, "front", 0.024, (0.06, 0.034, 0.046), [(1, -38.0)], 0.035),
        ("Bip01 Spine2", 0.138, 0.6, "back", 0.022, (0.055, 0.04, 0.13), [(1, 12.0)], 0.05),
        ("Bip01 Spine2", 0.165, 0.8, "back", 0.022, (0.06, 0.036, 0.05), [(1, 30.0)], 0.04),
    ],
    "forms": [
        ("Bip01 Neck", "Neck", (0.085, 0.032, -0.03), (0.095, 0.05, 0.03), [(1, 24.0)], 0.045, True),
        ("Bip01 L Clavicle", "L UpperArm", (-0.02, 0.0, 0.02), (0.06, 0.055, 0.035), [(1, 25.0)], 0.04, True),
    ],
    "zones": [("L UpperArm", (-0.02, 0.0, 0.005), 0.125, 0.011)],
    "trunk_bumps": [
        ("Bip01 Spine2", 0.084, 0.748, "front", 0.0, (0.082, 0.06, 0.078), [(1, -12.0)], 0.0105, 2.0),
        ("Bip01 Spine2", 0.108, 0.688, "front", 0.0, (0.058, 0.06, 0.042), [(1, -22.0)], 0.0055, 2.0),
        ("Bip01 Spine1", 0.033, 0.555, "front", 0.0, (0.03, 0.03, 0.04), [], 0.003, 2.6),
        ("Bip01 Spine1", 0.033, 0.465, "front", 0.0, (0.03, 0.03, 0.04), [], 0.003, 2.6),
        ("Bip01 Spine", 0.033, 0.378, "front", 0.0, (0.03, 0.03, 0.038), [], 0.0026, 2.6),
        ("Bip01 Spine", 0.031, 0.19, "front", 0.0, (0.031, 0.03, 0.1), [], 0.0024, 2.6),
        ("Bip01 Spine", 0.138, 0.22, -0.02, 0.0, (0.035, 0.07, 0.07), [], 0.0065, 2.0),
        ("Bip01 Spine1", 0.036, 0.26, "back", 0.0, (0.03, 0.04, 0.17), [], 0.0075, 2.2),
        ("Bip01 Spine2", 0.088, 0.76, "back", 0.0, (0.05, 0.04, 0.08), [(1, -10.0)], 0.006, 2.0),
        ("Bip01 Spine2", 0.12, 0.77, "back", 0.0, (0.045, 0.04, 0.045), [(1, 20.0)], 0.0065, 2.0),
        ("Bip01 Spine2", 0.148, 0.71, "back", 0.0, (0.035, 0.04, 0.03), [(1, 30.0)], 0.006, 2.0),
        ("Bip01 Spine2", 0.0, 0.78, "back", 0.0, (0.075, 0.03, 0.17), [], 0.003, 2.0),
        ("Bip01 Spine2", 0.0, 1.015, "back", 0.0, (0.014, 0.02, 0.014), [], 0.003, 2.0),
        ("Bip01 Pelvis", 0.118, 0.155, "front", 0.0, (0.02, 0.03, 0.022), [], 0.0022, 2.0),
        ("Bip01 Spine2", 0.15, 0.545, -0.042, 0.0, (0.032, 0.03, 0.014), [(1, 35.0)], 0.0014, 2.0),
        ("Bip01 Spine2", 0.154, 0.6, -0.046, 0.0, (0.032, 0.03, 0.014), [(1, 35.0)], 0.0015, 2.0),
        ("Bip01 Spine2", 0.157, 0.655, -0.05, 0.0, (0.03, 0.03, 0.014), [(1, 35.0)], 0.0014, 2.0),
        ("Bip01 Spine2", 0.0, 0.94, "front", 0.0, (0.03, 0.03, 0.024), [], -0.005, 2.0),
        ("Bip01 Spine2", 0.085, 0.975, "front", 0.0, (0.05, 0.03, 0.024), [(1, -8.0)], -0.005, 2.0),
        ("Bip01 Pelvis", 0.042, 0.105, "back", 0.0, (0.018, 0.02, 0.018), [], -0.002, 2.0),
        ("Bip01 Pelvis", 0.0, 0.06, "back", 0.0, (0.035, 0.03, 0.045), [], -0.003, 2.0),
    ],
    "trunk_ridges": [
        ("Bip01 Spine2", [(0.015, 0.915, "front", 0.0), (0.06, 0.912, "front", 0.0), (0.11, 0.92, "front", 0.0), (0.165, 0.936, "front", 0.004), (0.2, 0.948, "front", 0.014)], [0.011, 0.012, 0.012, 0.012, 0.012], 0.0038, 2.0),
        ("Bip01 Spine2", [(0.026, 0.622, "front", 0.0), (0.075, 0.6, "front", 0.0), (0.122, 0.606, "front", 0.0), (0.16, 0.648, "front", 0.0)], [0.016, 0.018, 0.018, 0.015], -0.0018, 2.0),
        ("Bip01 Spine1", [(0.0, 0.02, "back", 0.0), (0.0, 0.2, "back", 0.0), (0.0, 0.32, "back", 0.0), (0.0, 0.5, "back", 0.0)], [0.02, 0.023, 0.024, 0.022], -0.0038, 2.0),
        ("Bip01 Spine2", [(0.0, 0.4, "back", 0.0), (0.0, 0.6, "back", 0.0), (0.0, 0.78, "back", 0.0), (0.0, 1.0, "back", 0.0)], [0.02, 0.02, 0.02, 0.016], -0.002, 2.0),
        ("Bip01 Spine", [(0.0, 0.3, "front", 0.0), (0.0, 0.45, "front", 0.0), (0.0, 0.55, "front", 0.0), (0.0, 0.66, "front", 0.0)], [0.014, 0.015, 0.015, 0.014], -0.0022, 2.0),
        ("Bip01 Spine2", [(0.0, 0.6, "front", 0.0), (0.0, 0.74, "front", 0.0), (0.0, 0.84, "front", 0.0), (0.0, 0.95, "front", 0.0)], [0.018, 0.02, 0.02, 0.016], -0.0024, 2.0),
        ("Bip01 Spine", [(0.07, 0.24, "front", 0.0), (0.072, 0.42, "front", 0.0), (0.074, 0.52, "front", 0.0), (0.082, 0.64, "front", 0.0)], [0.016, 0.018, 0.018, 0.016], -0.0016, 2.0),
        ("Bip01 Spine", [(0.02, 0.64, "front", 0.0), (0.075, 0.6, "front", 0.0), (0.115, 0.545, "front", 0.0), (0.145, 0.44, "front", 0.0)], [0.02, 0.022, 0.022, 0.02], 0.0018, 2.0),
        ("Bip01 Pelvis", [(0.135, 0.19, "front", 0.0), (0.085, 0.07, "front", 0.0), (0.05, 0.005, "front", 0.0), (0.02, -0.05, "front", 0.0)], [0.02, 0.022, 0.022, 0.018], -0.0022, 2.0),
        ("Bip01 Pelvis", [(0.105, 0.14, "front", 0.0), (0.135, 0.21, -0.045, 0.0), (0.147, 0.25, 0.0, 0.0), (0.117, 0.245, 0.06, 0.0), (0.07, 0.2, "back", 0.0)], [0.02, 0.022, 0.022, 0.022, 0.02], 0.0022, 2.0),
        ("Bip01 Pelvis", [(0.0, 0.07, "back", 0.008), (0.0, 0.02, "back", -0.002), (0.0, -0.04, "back", -0.012), (0.0, -0.1, "back", -0.018), (0.0, -0.17, "back", -0.012)], [0.01, 0.012, 0.014, 0.014, 0.01], -0.013, 2.0),
        ("Bip01 Spine2", [(0.082, 0.62, "back", 0.0), (0.074, 0.76, "back", 0.0), (0.08, 0.9, "back", 0.0)], [0.022, 0.024, 0.022], 0.003, 2.0),
        ("Bip01 Spine2", [(0.06, 0.86, "back", 0.0), (0.13, 0.9, "back", 0.0), (0.2, 0.94, "back", 0.004)], [0.02, 0.022, 0.02], 0.0034, 2.0),
    ],
    "nipples": {"guess": (0.102, -0.125, -0.02), "areola": 0.0125, "raise": 0.0005, "tip": 0.0027, "length": 0.0022, "glands": 7, "seed": 11},
    "navel": (0.3, 0.003),
    "mouth_plug": ((0.0, -0.105, 0.025), (0.022, 0.012, 0.0065)),
    "lip_seam": (0.16, 0.07, 0.06),
    "neck": [
        (0.0, 0.075, 0.066, 0.082, 0.0),
        (0.2, 0.072, 0.063, 0.064, 0.0),
        (0.4, 0.077, 0.063, 0.06, 0.0),
        (0.55, 0.075, 0.064, 0.061, 0.0),
        (0.75, 0.06, 0.066, 0.06, 0.0),
        (1.0, 0.045, 0.055, 0.05, 0.0),
    ],
    "neck_ridges": [
        ("Bip01 Neck", [(0.055, 0.018, 0.11), (0.042, -0.03, 0.035), (0.018, -0.07, -0.045)], [0.015, 0.014, 0.012], 0.0042),
        ("Bip01 Neck", [(0.0, -0.069, 0.012), (0.0, -0.073, 0.022), (0.0, -0.07, 0.032)], [0.011, 0.011, 0.009], 0.0048),
    ],
    "arm": [
        (0, -0.14, 0.022, 0.022, 0.022, 0.022, 2.0, 2.0, 0.0, 0.0, 0.0),
        (0, -0.06, 0.042, 0.045, 0.043, 0.04, 2.0, 2.0, 0.0, 0.0, 0.0),
        (0, 0.05, 0.05, 0.052, 0.05, 0.047, 2.1, 2.1, 0.0, 0.0, 0.0),
        (0, 0.2, 0.047, 0.05, 0.046, 0.043, 2.1, 2.1, 0.0, 0.0, 0.0),
        (0, 0.4, 0.045, 0.048, 0.043, 0.041, 2.15, 2.1, 0.0, 0.0, 0.0),
        (0, 0.6, 0.043, 0.046, 0.041, 0.04, 2.2, 2.15, 0.0, 0.0, 0.0),
        (0, 0.8, 0.038, 0.042, 0.04, 0.04, 2.2, 2.2, 0.0, 0.0, 0.0),
        (0, 0.95, 0.034, 0.039, 0.042, 0.042, 2.3, 2.3, 0.0, 0.0, 0.0),
        (1, 0.08, 0.037, 0.038, 0.044, 0.044, 2.2, 2.2, 0.0, 0.0, 0.1),
        (1, 0.2, 0.04, 0.036, 0.045, 0.043, 2.2, 2.2, 0.0, 0.0, 0.25),
        (1, 0.4, 0.034, 0.031, 0.039, 0.037, 2.2, 2.2, 0.0, 0.0, 0.5),
        (1, 0.6, 0.028, 0.026, 0.034, 0.032, 2.3, 2.3, 0.0, 0.0, 0.76),
        (1, 0.8, 0.022, 0.021, 0.03, 0.029, 2.5, 2.5, 0.0, 0.0, 0.94),
        (1, 0.96, 0.02, 0.019, 0.029, 0.028, 2.6, 2.6, 0.0, 0.0, 1.0),
    ],
    "palm": [
        (0.0, 0.0195, 0.018, 0.028, 0.027, 2.5, 2.5, 0.0, 0.0),
        (0.12, 0.0195, 0.0168, 0.027, 0.028, 2.45, 2.6, 0.0, -0.001),
        (0.3, 0.0172, 0.0145, 0.03, 0.032, 2.45, 2.8, 0.0, -0.004),
        (0.5, 0.0158, 0.0126, 0.033, 0.036, 2.5, 3.0, 0.0, -0.007),
        (0.68, 0.015, 0.0116, 0.034, 0.038, 2.5, 3.1, 0.0, -0.009),
        (0.8, 0.0138, 0.0112, 0.034, 0.035, 2.5, 3.0, 0.0, -0.009),
        (0.88, 0.0132, 0.0102, 0.032, 0.03, 2.45, 2.9, 0.0, -0.009),
        (0.95, 0.0118, 0.0075, 0.029, 0.024, 2.5, 2.6, 0.0, -0.009),
        (1.02, 0.0095, 0.0052, 0.025, 0.018, 2.4, 2.4, 0.0, -0.009),
        (1.1, 0.006, 0.003, 0.018, 0.01, 2.2, 2.2, 0.001, -0.008),
        (1.15, 0.0015, 0.001, 0.006, 0.004, 2.0, 2.0, 0.001, -0.008),
    ],
    "upper_arm_forms": [
        (0.16, (-0.002, 0.014), (0.057, 0.047, 0.088), None, 0.03),
    ],
    "upper_arm_bumps": [
        (0.1, (0.0, 0.05), (0.035, 0.032, 0.085), 0.005, 2.0),
        (0.08, (0.044, 0.02), (0.03, 0.03, 0.075), 0.006, 2.0),
        (0.08, (-0.044, 0.022), (0.03, 0.03, 0.075), 0.006, 2.0),
        (0.56, (0.046, -0.004), (0.03, 0.032, 0.09), 0.009, 2.4),
        (0.4, (-0.048, -0.008), (0.03, 0.034, 0.105), 0.008, 2.0),
        (0.33, (-0.036, 0.03), (0.028, 0.028, 0.08), 0.006, 2.0),
        (0.72, (0.012, 0.042), (0.02, 0.025, 0.05), 0.004, 2.0),
        (1.0, (-0.04, 0.0), (0.02, 0.02, 0.023), 0.0045, 2.0),
        (0.98, (0.002, -0.044), (0.016, 0.016, 0.017), 0.0035, 2.0),
        (0.98, (0.036, 0.0), (0.024, 0.034, 0.016), -0.002, 2.0),
    ],
    "forearm_forms": [],
    "forearm_bumps": [
        (0.18, (0.014, 0.044), (0.025, 0.025, 0.085), 0.007, 2.0),
        (0.25, (0.04, -0.02), (0.028, 0.03, 0.09), 0.006, 2.0),
        (0.27, (-0.036, 0.012), (0.025, 0.03, 0.085), 0.005, 2.0),
        (0.6, (-0.03, -0.012), (0.008, 0.01, 0.1), 0.0016, 2.0),
        (0.95, (-0.014, -0.027), (0.008, 0.008, 0.009), 0.0035, 2.0),
        (0.97, (-0.004, 0.031), (0.008, 0.008, 0.01), 0.0028, 2.0),
        (0.9, (0.022, 0.004), (0.004, 0.006, 0.035), 0.0014, 2.0),
        (0.9, (0.021, -0.01), (0.004, 0.006, 0.035), 0.0012, 2.0),
    ],
    "leg": leg_stations((0.06, 0.069, 0.071, 0.071, 0.07, 0.066, 0.06)),
    "thigh_forms": [],
    "thigh_bumps": [
        (0.22, (0.005, -0.062), (0.035, 0.035, 0.13), 0.006, 2.0),
        (0.45, (0.07, 0.004), (0.03, 0.035, 0.14), 0.0062, 2.0),
        (0.52, (0.02, 0.075), (0.035, 0.03, 0.16), 0.0072, 2.0),
        (0.84, (0.038, -0.052), (0.03, 0.03, 0.06), 0.0082, 2.0),
        (0.2, (0.0, -0.06), (0.04, 0.035, 0.1), 0.004, 2.0),
        (0.5, (-0.065, 0.0), (0.03, 0.045, 0.14), 0.006, 2.0),
        (0.55, (-0.005, 0.078), (0.01, 0.012, 0.14), -0.002, 2.0),
        (1.0, (0.049, 0.0), (0.032, 0.036, 0.04), 0.0052, 2.4),
        (1.09, (0.045, 0.0), (0.016, 0.014, 0.028), 0.003, 2.0),
        (1.0, (0.036, 0.034), (0.014, 0.014, 0.025), -0.0025, 2.0),
        (1.0, (0.036, -0.034), (0.014, 0.014, 0.025), -0.0025, 2.0),
        (1.0, (-0.05, 0.0), (0.02, 0.028, 0.035), -0.004, 2.0),
        (0.95, (-0.046, 0.03), (0.01, 0.012, 0.05), 0.003, 2.0),
        (0.95, (-0.046, -0.03), (0.01, 0.012, 0.05), 0.003, 2.0),
    ],
    "calf_forms": [],
    "calf_bumps": [
        (0.26, (-0.066, -0.025), (0.032, 0.036, 0.1), 0.009, 2.0),
        (0.23, (-0.064, 0.022), (0.03, 0.032, 0.085), 0.0075, 2.0),
        (0.3, (0.035, 0.02), (0.018, 0.02, 0.11), 0.005, 2.0),
        (0.45, (0.036, -0.004), (0.008, 0.01, 0.16), 0.002, 2.0),
        (0.52, (-0.02, 0.045), (0.02, 0.018, 0.08), 0.003, 2.0),
        (0.52, (-0.02, -0.045), (0.02, 0.018, 0.08), 0.003, 2.0),
        (0.83, (-0.036, 0.0), (0.012, 0.014, 0.07), 0.004, 2.0),
        (0.9, (-0.026, 0.022), (0.012, 0.012, 0.04), -0.003, 2.0),
        (0.9, (-0.026, -0.022), (0.012, 0.012, 0.04), -0.003, 2.0),
        (0.99, (0.004, -0.032), (0.02, 0.018, 0.028), 0.0045, 2.0),
        (1.03, (-0.006, 0.033), (0.02, 0.018, 0.028), 0.0045, 2.0),
    ],
    "foot": [
        (-0.071, 0.002, 0.002, 0.003, 0.003, 2.0, 2.0, 0.027, 0.0),
        (-0.067, 0.013, 0.015, 0.013, 0.013, 2.0, 2.0, 0.027, 0.0),
        (-0.061, 0.021, 0.024, 0.019, 0.019, 2.0, 2.2, 0.027, 0.0),
        (-0.05, 0.031, 0.03, 0.025, 0.025, 2.0, 2.5, 0.03, 0.0),
        (-0.03, 0.044, 0.035, 0.029, 0.029, 2.0, 2.8, 0.035, 0.0),
        (0.0, 0.053, 0.037, 0.031, 0.031, 2.0, 2.9, 0.038, 0.0),
        (0.03, 0.048, 0.035, 0.034, 0.033, 2.1, 3.0, 0.036, 0.001),
        (0.06, 0.04, 0.031, 0.038, 0.035, 2.2, 3.2, 0.032, 0.002),
        (0.09, 0.031, 0.026, 0.042, 0.039, 2.3, 3.3, 0.027, 0.002),
        (0.115, 0.023, 0.022, 0.046, 0.043, 2.4, 3.2, 0.022, 0.002),
        (0.135, 0.013, 0.018, 0.047, 0.045, 2.4, 3.0, 0.018, 0.001),
        (0.15, 0.009, 0.014, 0.043, 0.042, 2.3, 2.6, 0.014, 0.0),
        (0.16, 0.004, 0.009, 0.03, 0.03, 2.0, 2.0, 0.01, 0.0),
    ],
    "foot_forms": [],
    "foot_bumps": [
        ("Bip01 L Foot", (0.045, -0.04, -0.002), (0.06, 0.026, 0.022), -0.014, 2.0),
        ("Bip01 L Foot", (0.128, -0.005, 0.0), (0.018, 0.045, 0.01), 0.0015, 2.0),
        ("Bip01 L Foot", (0.125, -0.042, 0.02), (0.014, 0.01, 0.014), 0.002, 2.0),
        ("Bip01 L Foot", (0.095, 0.047, 0.012), (0.02, 0.01, 0.01), 0.0015, 2.0),
        ("Bip01 L Foot", (0.04, -0.012, 0.075), (0.03, 0.025, 0.015), 0.002, 2.0),
    ],
    "foot_ridges": [
        ("Bip01 L Foot", [(0.03, -0.014, 0.085), (0.08, -0.024, 0.06), (0.122, -0.028, 0.04)], [0.005, 0.005, 0.005], 0.001),
        ("Bip01 L Foot", [(0.035, 0.006, 0.085), (0.085, 0.01, 0.056), (0.125, 0.012, 0.036)], [0.005, 0.005, 0.005], 0.0006),
    ],
    "toe_profile": toe_profile,
    "toe_blend": 0.003,
    "toes": [
        ([(0.128, -0.028, 0.019), (0.165, -0.029, 0.018), (0.196, -0.029, 0.0105)], 0.0125, 0.0105, (0.6, 0.74, 0.0004, -0.06)),
        ([(0.138, -0.006, 0.017), (0.157, -0.005, 0.02), (0.173, -0.004, 0.015), (0.188, -0.004, 0.0085)], 0.0078, 0.0072, (0.55, 0.66, 0.0003, -0.05)),
        ([(0.133, 0.01, 0.016), (0.151, 0.011, 0.019), (0.166, 0.012, 0.014), (0.179, 0.012, 0.008)], 0.0074, 0.0069, (0.55, 0.66, 0.0003, -0.05)),
        ([(0.124, 0.025, 0.015), (0.141, 0.026, 0.017), (0.155, 0.027, 0.013), (0.167, 0.027, 0.0077)], 0.0071, 0.0066, (0.55, 0.65, 0.0003, -0.05)),
        ([(0.112, 0.038, 0.014), (0.128, 0.04, 0.015), (0.141, 0.041, 0.011), (0.152, 0.041, 0.0073)], 0.0068, 0.0062, (0.55, 0.64, 0.0003, -0.05)),
    ],
    "ray_bases": [(0.02, 0.0, -0.012), (0.018, 0.0, -0.002), (0.02, 0.002, 0.009), (0.024, 0.004, 0.019)],
    "tendon": 0.0006,
    "hand_veins": [
        ([(0.086, -0.03, -0.014), (0.076, -0.03, -0.015), (0.066, -0.03, -0.018), (0.056, -0.03, -0.019), (0.047, -0.03, -0.021), (0.037, -0.03, -0.022), (0.028, -0.03, -0.026), (0.018, -0.03, -0.028), (0.008, -0.03, -0.031)], 0.0017, 0.0005),
        ([(0.086, -0.03, 0.008), (0.077, -0.03, 0.008), (0.068, -0.03, 0.005), (0.06, -0.03, 0.003), (0.052, -0.03, -0.002), (0.048, -0.03, -0.008), (0.045, -0.03, -0.014)], 0.0015, 0.0004),
        ([(0.082, -0.03, 0.024), (0.072, -0.03, 0.023), (0.062, -0.03, 0.021), (0.052, -0.03, 0.022), (0.042, -0.03, 0.023), (0.031, -0.03, 0.024), (0.02, -0.03, 0.027), (0.01, -0.03, 0.028), (0.0, -0.03, 0.029)], 0.0016, 0.0004),
        ([(0.053, -0.03, -0.001), (0.05, -0.03, 0.006), (0.048, -0.03, 0.013), (0.044, -0.03, 0.019), (0.04, -0.03, 0.023)], 0.0014, 0.0003),
    ],
    "forearm_veins": [
        ([(0.97, -0.005, 0.03), (0.86, -0.003, 0.034), (0.74, 0.001, 0.035), (0.62, 0.003, 0.039), (0.5, 0.008, 0.04), (0.38, 0.01, 0.043), (0.25, 0.015, 0.041), (0.1, 0.02, 0.037)], 0.0024, 0.0003),
        ([(0.95, -0.004, -0.03), (0.82, 0.0, -0.034), (0.7, 0.004, -0.035), (0.57, 0.007, -0.039), (0.45, 0.012, -0.04), (0.32, 0.016, -0.041), (0.2, 0.02, -0.04)], 0.0022, 0.00025),
    ],
    "hand_forms": [
        ((0.034, 0.018, -0.03), (0.7, 0.45, -0.55), (0.0, 0.75, -0.66), (0.012, 0.016, 0.027), 0.012),
        ((0.048, 0.012, 0.031), (1.0, 0.0, 0.1), (0.0, 0.8, 0.6), (0.009, 0.011, 0.032), 0.012),
        ((0.066, 0.009, -0.041), (0.84, -0.41, 0.33), (0.0, 0.58, 0.81), (0.008, 0.014, 0.026), 0.008),
        ((0.062, -0.002, -0.034), (1.0, 0.0, -0.35), (0.0, -0.6, -0.8), (0.0065, 0.011, 0.022), 0.009),
    ],
    "hand_bumps": [
        ((0.088, 0.016, -0.012), (0.014, 0.008, 0.014), 0.0018, 2.0),
        ((0.087, 0.017, 0.012), (0.014, 0.008, 0.016), 0.0016, 2.0),
        ((0.084, 0.016, 0.03), (0.013, 0.008, 0.013), 0.0014, 2.0),
        ((0.058, 0.022, 0.003), (0.025, 0.015, 0.022), -0.003, 2.0),
    ],
    "palm_lines": [
        ([(0.07, 0.02, 0.045), (0.073, 0.022, 0.034), (0.077, 0.022, 0.022), (0.081, 0.022, 0.01), (0.085, 0.021, -0.002), (0.09, 0.02, -0.011)], 0.0016, -0.0005),
        ([(0.067, 0.021, -0.032), (0.064, 0.023, -0.02), (0.061, 0.023, -0.008), (0.058, 0.023, 0.005), (0.054, 0.022, 0.018)], 0.0016, -0.00045),
        ([(0.066, 0.021, -0.031), (0.056, 0.025, -0.024), (0.045, 0.028, -0.018), (0.033, 0.029, -0.013), (0.021, 0.027, -0.009), (0.01, 0.024, -0.006)], 0.0016, -0.0005),
        ([(0.004, 0.024, -0.017), (0.002, 0.025, -0.006), (0.0015, 0.025, 0.004), (0.003, 0.024, 0.016)], 0.0012, -0.0003),
        ([(-0.007, 0.024, -0.016), (-0.008, 0.025, 0.0), (-0.007, 0.024, 0.015)], 0.0011, -0.0002),
    ],
    "finger_profile": [finger_profile_thumb, finger_profile_long],
    "finger_blend": 0.005,
    "thumb_blend": 0.011,
    "fingers": [
        (0.0106, 0.0098, (0.6, 0.63, 0.00045, -0.12), 0.0, 0.0),
        (0.0103, 0.0093, (0.62, 0.61, 0.0004, -0.12), 0.0, 0.0019),
        (0.0106, 0.0096, (0.62, 0.61, 0.0004, -0.12), 0.0, 0.0021),
        (0.0101, 0.0091, (0.62, 0.61, 0.0004, -0.12), 0.0, 0.0019),
        (0.0088, 0.0081, (0.62, 0.6, 0.00035, -0.12), 0.0, 0.0016),
    ],
}


def softened(entries, factor):
    return [entry[:3] + (entry[3] * factor,) + entry[4:] for entry in entries]


female = {
    **male,
    "scale": 0.925,
    "head_scale": 0.9,
    "hand_scale": 0.9,
    "foot_scale": 0.9,
    "lash_scale": 1.2,
    "lip_seam": (0.2, 0.075, 0.07),
    "hair": {
        "center": (0.0, 0.005, 0.09),
        "bun": ((0.0, 0.122, 0.04), (0.036, 0.046, 0.034)),
        "tie": (0.024, 0.017),
        "thickness": 0.009,
        "groove": 0.00018,
        "line": [(0.0, 0.147), (30.0, 0.142), (55.0, 0.128), (75.0, 0.118), (95.0, 0.112), (112.0, 0.085), (130.0, 0.05), (155.0, 0.025), (180.0, 0.02)],
        "color": (0.03, 0.017, 0.01),
        "light": (0.1, 0.06, 0.035),
    },
    "rig": {
        "default": 0.925,
        "root_height": 0.828,
        "head": 0.9,
        "bones": [
            ("Clavicle", (0.85, 0.925, 0.925)),
            ("UpperArm", (0.88, 0.925, 0.9)),
            ("Forearm", (0.915, 0.915, 0.915)),
            ("Hand", (0.915, 0.915, 0.915)),
            ("Finger", (0.9, 0.9, 0.9)),
            ("Thigh", (0.98, 0.925, 0.925)),
            ("Toe", (0.89, 0.89, 0.89)),
            ("Neck", (0.93, 0.93, 0.93)),
            ("Head", (0.93, 0.93, 0.93)),
        ],
    },
    "face": [
        ((0.0, -0.06, 1.575), (0.09, 0.09, 0.065), (0.0, 0.0, 0.0), (0.88, 1.0, 1.0)),
        ((0.058, -0.04, 1.575), (0.045, 0.06, 0.05), (-0.008, 0.0, 0.006), (1.0, 1.0, 1.0)),
        ((-0.058, -0.04, 1.575), (0.045, 0.06, 0.05), (0.008, 0.0, 0.006), (1.0, 1.0, 1.0)),
        ((0.0, -0.12, 1.6), (0.07, 0.08, 0.06), (0.0, 0.0, 0.0), (1.0, 1.0, 0.9)),
        ((0.0, -0.112, 1.565), (0.03, 0.03, 0.025), (0.0, 0.005, 0.004), (0.75, 0.95, 0.85)),
        ((0.0, -0.005, 1.54), (0.085, 0.09, 0.06), (0.0, 0.0, 0.0), (0.8, 0.85, 1.0)),
        ((0.045, -0.1, 1.645), (0.03, 0.03, 0.025), (0.002, -0.003, 0.0), (1.0, 1.0, 1.0)),
        ((-0.045, -0.1, 1.645), (0.03, 0.03, 0.025), (-0.002, -0.003, 0.0), (1.0, 1.0, 1.0)),
        ((0.052, -0.085, 1.655), (0.025, 0.03, 0.022), (0.004, -0.001, 0.001), (1.0, 1.0, 1.0)),
        ((-0.052, -0.085, 1.655), (0.025, 0.03, 0.022), (-0.004, -0.001, 0.001), (1.0, 1.0, 1.0)),
        ((0.03, -0.118, 1.7), (0.028, 0.02, 0.016), (0.0, 0.0035, 0.001), (1.0, 1.0, 1.0)),
        ((-0.03, -0.118, 1.7), (0.028, 0.02, 0.016), (0.0, 0.0035, 0.001), (1.0, 1.0, 1.0)),
        ((0.0, -0.126, 1.697), (0.016, 0.015, 0.015), (0.0, 0.0025, 0.0), (1.0, 1.0, 1.0)),
        ((0.032, -0.1, 1.686), (0.022, 0.018, 0.016), (0.0, 0.0, 0.0), (1.06, 1.0, 1.08)),
        ((-0.032, -0.1, 1.686), (0.022, 0.018, 0.016), (0.0, 0.0, 0.0), (1.06, 1.0, 1.08)),
        ((0.0, -0.145, 1.648), (0.02, 0.025, 0.035), (0.0, 0.003, 0.001), (0.85, 0.88, 0.88)),
        ((0.0, -0.131, 1.613), (0.032, 0.016, 0.014), (0.0, -0.0012, 0.0), (0.97, 1.05, 1.18)),
        ((0.048, -0.1, 1.662), (0.025, 0.025, 0.02), (0.0015, -0.002, 0.002), (1.0, 1.0, 1.0)),
        ((-0.048, -0.1, 1.662), (0.025, 0.025, 0.02), (-0.0015, -0.002, 0.002), (1.0, 1.0, 1.0)),
        ((0.0, -0.105, 1.75), (0.065, 0.035, 0.045), (0.0, -0.003, 0.002), (1.0, 1.0, 1.0)),
    ],
    "arm_girth": [(0.92, 0.95), (0.96, 0.95)],
    "leg_girth": [(1.22, 1.06), (1.04, 0.97)],
    "leg": leg_stations((0.072, 0.085, 0.088, 0.086, 0.082, 0.074, 0.064)),
    "blends": {"neck": 0.02, "arm": 0.03, "leg": 0.02, "foot": 0.014, "carpus": 0.005, "ray": 0.006},
    "torso": [
        (-0.128, 0.032, 0.046, 0.037, 2.0, 2.0, 0.0),
        (-0.08, 0.056, 0.085, 0.08, 2.1, 2.2, 0.0),
        (-0.024, 0.074, 0.102, 0.125, 2.2, 2.3, 0.0),
        (0.056, 0.08, 0.1, 0.145, 2.2, 2.4, 0.0),
        (0.152, 0.083, 0.09, 0.143, 2.2, 2.35, 0.0),
        (0.232, 0.085, 0.082, 0.132, 2.15, 2.3, 0.0),
        (0.312, 0.086, 0.078, 0.122, 2.1, 2.3, 0.0),
        (0.392, 0.087, 0.078, 0.12, 2.1, 2.3, 0.0),
        (0.472, 0.089, 0.082, 0.125, 2.15, 2.3, 0.0),
        (0.551, 0.092, 0.088, 0.132, 2.2, 2.3, 0.0),
        (0.631, 0.094, 0.093, 0.139, 2.25, 2.3, 0.0),
        (0.711, 0.094, 0.097, 0.143, 2.25, 2.3, 0.0),
        (0.791, 0.092, 0.098, 0.146, 2.2, 2.25, 0.0),
        (0.855, 0.085, 0.095, 0.158, 2.1, 2.2, 0.0),
        (0.903, 0.074, 0.088, 0.16, 2.0, 2.1, 0.0),
        (0.935, 0.064, 0.08, 0.134, 2.0, 2.0, 0.0),
        (0.967, 0.054, 0.07, 0.102, 2.0, 2.0, 0.0),
        (0.999, 0.047, 0.062, 0.07, 2.0, 2.0, 0.0),
        (1.023, 0.043, 0.055, 0.058, 2.0, 2.0, 0.0),
        (1.047, 0.04, 0.05, 0.045, 2.0, 2.0, 0.0),
    ],
    "trunk_forms": [
        ("Bip01 Pelvis", 0.072, -0.04, 0.06, 0.0, (0.08, 0.058, 0.092), [(1, 6.0)], 0.035),
        ("Bip01 Pelvis", 0.125, 0.02, 0.012, 0.0, (0.045, 0.055, 0.075), [], 0.04),
        ("Bip01 Spine2", 0.14, 0.79, "front", 0.022, (0.045, 0.028, 0.04), [(1, -38.0)], 0.035),
        ("Bip01 Spine2", 0.14, 0.8, "back", 0.022, (0.05, 0.032, 0.045), [(1, 30.0)], 0.04),
    ],
    "forms": [
        ("Bip01 Neck", "Neck", (0.08, 0.03, -0.03), (0.09, 0.045, 0.026), [(1, 24.0)], 0.045, True),
        ("Bip01 L Clavicle", "L UpperArm", (-0.02, 0.0, 0.02), (0.058, 0.052, 0.033), [(1, 25.0)], 0.04, True),
    ],
    "breast": {"x": 0.073, "h": 0.672, "drop": 0.003, "asymmetry": 0.02, "splay": 0.16, "lower": (0.004, -0.013, (0.053, 0.039, 0.047)), "upper": (-0.006, 0.038, (0.049, 0.028, 0.07), -18.0), "tail": (0.044, 0.028, -0.014, (0.036, 0.024, 0.036)), "merge": 0.035, "fold": (0.004, 0.04, 0.012, 0.06)},
    "nipples": {"guess": (0.085, -0.15, -0.02), "shift": (0.0, 0.0, -0.003), "areola": 0.019, "raise": 0.0012, "tip": 0.0052, "length": 0.0045, "glands": 10, "seed": 17},
    "trunk_bumps": [
        ("Bip01 Spine2", 0.06, 0.8, "front", 0.0, (0.06, 0.04, 0.05), [], 0.003, 2.0),
        ("Bip01 Spine", 0.0, 0.17, "front", 0.0, (0.08, 0.04, 0.075), [], 0.006, 2.0),
        ("Bip01 Pelvis", 0.0, -0.035, "front", 0.0, (0.042, 0.035, 0.04), [], 0.005, 2.0),
        ("Bip01 Spine", 0.03, 0.47, "front", 0.0, (0.03, 0.03, 0.09), [], 0.0014, 2.4),
        ("Bip01 Spine", 0.125, 0.24, -0.015, 0.0, (0.035, 0.06, 0.06), [], 0.003, 2.0),
        ("Bip01 Spine1", 0.028, 0.28, "back", 0.0, (0.026, 0.04, 0.16), [], 0.005, 2.5),
        ("Bip01 Spine2", 0.082, 0.76, "back", 0.0, (0.045, 0.04, 0.07), [(1, -10.0)], 0.003, 2.0),
        ("Bip01 Spine2", 0.0, 1.015, "back", 0.0, (0.013, 0.02, 0.013), [], 0.002, 2.0),
        ("Bip01 Pelvis", 0.036, 0.1, "back", 0.0, (0.017, 0.03, 0.017), [], -0.0022, 2.0),
        ("Bip01 Spine2", 0.0, 0.94, "front", 0.0, (0.026, 0.03, 0.022), [], -0.004, 2.0),
        ("Bip01 Spine2", 0.075, 0.975, "front", 0.0, (0.045, 0.03, 0.022), [(1, -8.0)], -0.0045, 2.0),
        ("Bip01 Pelvis", 0.108, 0.15, "front", 0.0, (0.02, 0.03, 0.022), [], 0.0016, 2.0),
    ],
    "trunk_ridges": [
        ("Bip01 Spine2", [(0.014, 0.915, "front", 0.0), (0.055, 0.912, "front", 0.0), (0.1, 0.92, "front", 0.0), (0.145, 0.934, "front", 0.004), (0.172, 0.946, "front", 0.012)], [0.009, 0.01, 0.01, 0.01, 0.01], 0.0034, 2.0),
        ("Bip01 Spine1", [(0.0, 0.02, "back", 0.0), (0.0, 0.2, "back", 0.0), (0.0, 0.32, "back", 0.0), (0.0, 0.5, "back", 0.0)], [0.018, 0.021, 0.022, 0.02], -0.0034, 2.0),
        ("Bip01 Spine2", [(0.0, 0.4, "back", 0.0), (0.0, 0.6, "back", 0.0), (0.0, 0.78, "back", 0.0), (0.0, 1.0, "back", 0.0)], [0.018, 0.018, 0.018, 0.014], -0.0016, 2.0),
        ("Bip01 Spine", [(0.0, 0.36, "front", 0.0), (0.0, 0.46, "front", 0.0), (0.0, 0.56, "front", 0.0)], [0.014, 0.015, 0.014], -0.0012, 2.0),
        ("Bip01 Pelvis", [(0.12, 0.17, "front", 0.0), (0.078, 0.06, "front", 0.0), (0.045, 0.0, "front", 0.0), (0.018, -0.06, "front", 0.0)], [0.018, 0.02, 0.02, 0.016], -0.0016, 2.0),
        ("Bip01 Pelvis", [(0.1, 0.14, "front", 0.0), (0.128, 0.2, -0.04, 0.0), (0.14, 0.24, 0.0, 0.0), (0.112, 0.235, 0.055, 0.0)], [0.02, 0.022, 0.022, 0.022], 0.0014, 2.0),
        ("Bip01 Pelvis", [(0.0, 0.07, "back", 0.008), (0.0, 0.02, "back", -0.002), (0.0, -0.04, "back", -0.014), (0.0, -0.1, "back", -0.02), (0.0, -0.17, "back", -0.014)], [0.01, 0.012, 0.015, 0.015, 0.011], -0.013, 2.0),
        ("Bip01 Spine2", [(0.072, 0.63, "back", 0.0), (0.066, 0.76, "back", 0.0), (0.07, 0.89, "back", 0.0)], [0.02, 0.022, 0.02], 0.002, 2.0),
    ],
    "navel": (0.33, 0.003),
    "neck": [
        (0.0, 0.068, 0.058, 0.066, 0.0),
        (0.2, 0.063, 0.055, 0.052, 0.0),
        (0.4, 0.066, 0.055, 0.05, 0.0),
        (0.55, 0.065, 0.056, 0.051, 0.0),
        (0.75, 0.054, 0.058, 0.052, 0.0),
        (1.0, 0.042, 0.05, 0.046, 0.0),
    ],
    "neck_ridges": [
        ("Bip01 Neck", [(0.055, 0.018, 0.11), (0.042, -0.03, 0.035), (0.018, -0.07, -0.045)], [0.014, 0.013, 0.011], 0.0018),
    ],
    "upper_arm_forms": [
        (0.15, (0.0, 0.012), (0.049, 0.039, 0.078), None, 0.034),
    ],
    "upper_arm_bumps": softened(male["upper_arm_bumps"], 0.5),
    "forearm_bumps": softened(male["forearm_bumps"], 0.6),
    "thigh_bumps": softened(male["thigh_bumps"], 0.5) + [(0.12, (0.0, 0.07), (0.04, 0.045, 0.12), 0.008, 2.0), (0.2, (0.0, -0.06), (0.035, 0.035, 0.12), 0.006, 2.0)],
    "calf_bumps": softened(male["calf_bumps"], 0.6),
    "tendon": 0.0003,
    "hand_veins": [],
    "forearm_veins": [],
    "fingers": [
        (0.0102, 0.0094, (0.62, 0.62, 0.0004, -0.12), 0.0, 0.0),
        (0.0098, 0.0089, (0.64, 0.6, 0.00036, -0.12), 0.0, 0.0012),
        (0.0101, 0.0092, (0.64, 0.6, 0.00036, -0.12), 0.0, 0.0013),
        (0.0096, 0.0087, (0.64, 0.6, 0.00036, -0.12), 0.0, 0.0012),
        (0.0084, 0.0077, (0.64, 0.59, 0.0003, -0.12), 0.0, 0.001),
    ],
}
