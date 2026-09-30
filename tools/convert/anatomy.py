import math
import numpy
import openvdb


def unit(vector):
    vector = numpy.asarray(vector, dtype=numpy.float64)
    return vector / max(float(numpy.linalg.norm(vector)), 1e-12)


def basis(axis, front):
    w = unit(axis)
    front = numpy.asarray(front, dtype=numpy.float64)
    u = unit(front - w * numpy.dot(front, w))
    v = numpy.cross(w, u)
    return numpy.stack([u, v, w])


def rotation(axis, degrees):
    axis = unit(axis)
    angle = math.radians(degrees)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = axis
    return numpy.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s], [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s], [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def smin(a, b, k):
    if numpy.isscalar(k) and k <= 0.0:
        return numpy.minimum(a, b)
    h = numpy.maximum(k - numpy.abs(a - b), 0.0) / k
    return numpy.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def hermite(knots, values, t):
    count = len(knots)
    slopes = numpy.empty_like(values)
    if count > 2:
        slopes[1:-1] = (values[2:] - values[:-2]) / (knots[2:] - knots[:-2])[:, None]
    slopes[0] = (values[1] - values[0]) / (knots[1] - knots[0])
    slopes[-1] = (values[-1] - values[-2]) / (knots[-1] - knots[-2])
    t = numpy.clip(t, knots[0], knots[-1])
    index = numpy.clip(numpy.searchsorted(knots, t, side='right') - 1, 0, count - 2)
    span = knots[index + 1] - knots[index]
    s = ((t - knots[index]) / span)[:, None]
    s2 = s * s
    s3 = s2 * s
    span = span[:, None]
    return (2.0 * s3 - 3.0 * s2 + 1.0) * values[index] + (s3 - 2.0 * s2 + s) * span * slopes[index] + (-2.0 * s3 + 3.0 * s2) * values[index + 1] + (s3 - s2) * span * slopes[index + 1]


def section_radius(c, s, params):
    twist = params[:, 8]
    ct = numpy.cos(twist)
    st = numpy.sin(twist)
    c, s = c * ct + s * st, s * ct - c * st
    front = numpy.where(c >= 0.0, params[:, 0], params[:, 1])
    side = numpy.where(s >= 0.0, params[:, 2], params[:, 3])
    power = numpy.where(c >= 0.0, params[:, 4], params[:, 5])
    return (numpy.abs(c / front) ** power + numpy.abs(s / side) ** power) ** (-1.0 / power)


class shape:
    def __init__(self, kind, label, blend=0.0, mode="add", **data):
        self.kind = kind
        self.label = label
        self.blend = blend
        self.mode = mode
        self.data = data
        self.low, self.high = self.bounds()

    def bounds(self):
        d = self.data
        if self.kind == "ellipsoid":
            extent = numpy.abs(d["frame"].T) @ d["radii"]
            return d["center"] - extent, d["center"] + extent
        if self.kind == "cone":
            r = max(d["r1"], d["r2"])
            return numpy.minimum(d["a"], d["b"]) - r, numpy.maximum(d["a"], d["b"]) + r
        if self.kind == "loft":
            table = d["table"]
            reach = float(numpy.max(numpy.abs(table[:, :4])) + numpy.max(numpy.abs(table[:, 6:8])))
            corners = []
            for along in (d["knots"][0], d["knots"][-1]):
                for su in (-reach, reach):
                    for sv in (-reach, reach):
                        corners.append(d["origin"] + d["frame"][2] * along + d["frame"][0] * su + d["frame"][1] * sv)
            corners = numpy.array(corners)
            return corners.min(axis=0), corners.max(axis=0)
        if self.kind == "custom":
            return numpy.asarray(d["low"], dtype=numpy.float64), numpy.asarray(d["high"], dtype=numpy.float64)
        if self.kind == "zone":
            return d["center"] - d["radius"], d["center"] + d["radius"]
        if self.kind == "plane":
            return numpy.asarray(d["low"], dtype=numpy.float64), numpy.asarray(d["high"], dtype=numpy.float64)
        if self.kind == "bump":
            extent = numpy.abs(d["frame"].T) @ d["radii"]
            return d["center"] - extent, d["center"] + extent
        if self.kind == "ridge":
            stack = numpy.array(d["points"])
            reach = max(d["radii"])
            return stack.min(axis=0) - reach, stack.max(axis=0) + reach
        if self.kind == "groove":
            flat = numpy.array(d["points"])
            corners = []
            for a in (flat[:, 0].min() - d["radius"], flat[:, 0].max() + d["radius"]):
                for b in (flat[:, 1].min() - d["radius"], flat[:, 1].max() + d["radius"]):
                    for n in (d["span"][0], d["span"][1]):
                        corners.append(d["origin"] + d["frame"][0] * a + d["frame"][1] * n + d["frame"][2] * b)
            corners = numpy.array(corners)
            return corners.min(axis=0), corners.max(axis=0)
        raise ValueError(self.kind)

    def distance(self, points):
        d = self.data
        if self.kind == "ellipsoid":
            q = (points - d["center"]) @ d["frame"].T
            r = d["radii"]
            k0 = numpy.linalg.norm(q / r, axis=1)
            k1 = numpy.maximum(numpy.linalg.norm(q / (r * r), axis=1), 1e-9)
            return k0 * (k0 - 1.0) / k1
        if self.kind == "cone":
            return round_cone(points, d["a"], d["b"], d["r1"], d["r2"])
        if self.kind == "loft":
            return loft_distance((points - d["origin"]) @ d["frame"].T, d["knots"], d["table"])
        if self.kind == "custom":
            return d["function"](points)
        if self.kind == "plane":
            return (points - d["point"]) @ d["normal"]
        if self.kind == "bump":
            q = (points - d["center"]) @ d["frame"].T / d["radii"]
            rho = numpy.sqrt(numpy.sum(q * q, axis=1))
            t = numpy.clip(1.0 - rho ** d["power"], 0.0, 1.0)
            return t * t * d["amount"]
        if self.kind == "ridge":
            rho = numpy.full(len(points), numpy.inf)
            position = numpy.zeros(len(points))
            pts = d["points"]
            radii = d["radii"]
            total = sum(float(numpy.linalg.norm(pts[i + 1] - pts[i])) for i in range(len(pts) - 1))
            walked = 0.0
            for index in range(len(pts) - 1):
                a = pts[index]
                b = pts[index + 1]
                ab = b - a
                length2 = max(float(ab @ ab), 1e-12)
                t = numpy.clip((points - a) @ ab / length2, 0.0, 1.0)
                closest = a + t[:, None] * ab
                radius = radii[index] + (radii[index + 1] - radii[index]) * t
                value = numpy.linalg.norm(points - closest, axis=1) / radius
                closer = value < rho
                rho = numpy.where(closer, value, rho)
                position = numpy.where(closer, (walked + t * math.sqrt(length2)) / max(total, 1e-9), position)
                walked += math.sqrt(length2)
            t = numpy.clip(1.0 - rho ** d["power"], 0.0, 1.0)
            taper = d.get("taper", 0.0)
            ends = numpy.clip(position / taper, 0.0, 1.0) * numpy.clip((1.0 - position) / taper, 0.0, 1.0) if taper > 0.0 else 1.0
            ends = ends * ends * (3.0 - 2.0 * ends) if taper > 0.0 else 1.0
            return t * t * d["amount"] * ends
        if self.kind == "groove":
            q = (points - d["origin"]) @ d["frame"].T
            flat = d["points"]
            best = numpy.full(len(points), numpy.inf)
            position = numpy.zeros(len(points))
            total = sum(float(numpy.linalg.norm(flat[i + 1] - flat[i])) for i in range(len(flat) - 1))
            walked = 0.0
            for index in range(len(flat) - 1):
                a = flat[index]
                b = flat[index + 1]
                ab = b - a
                length2 = max(float(ab @ ab), 1e-12)
                t = numpy.clip(((q[:, 0] - a[0]) * ab[0] + (q[:, 2] - a[1]) * ab[1]) / length2, 0.0, 1.0)
                dx = q[:, 0] - (a[0] + t * ab[0])
                dy = q[:, 2] - (a[1] + t * ab[1])
                distance = numpy.sqrt(dx * dx + dy * dy)
                closer = distance < best
                best = numpy.where(closer, distance, best)
                position = numpy.where(closer, (walked + t * math.sqrt(length2)) / max(total, 1e-9), position)
                walked += math.sqrt(length2)
            rho = best / d["radius"]
            t = numpy.clip(1.0 - rho ** d["power"], 0.0, 1.0)
            low, high = d["span"]
            soft = (high - low) * 0.25
            mask = numpy.clip((q[:, 1] - low) / soft, 0.0, 1.0) * numpy.clip((high - q[:, 1]) / soft, 0.0, 1.0)
            ends = numpy.clip(position / d["taper"], 0.0, 1.0) * numpy.clip((1.0 - position) / d["taper"], 0.0, 1.0) if d["taper"] > 0.0 else 1.0
            return t * t * mask * d["amount"] * ends
        raise ValueError(self.kind)


def round_cone(points, a, b, r1, r2):
    ba = b - a
    l2 = float(ba @ ba)
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = points - a
    y = pa @ ba
    z = y - l2
    x2 = numpy.sum((pa * l2 - numpy.outer(y, ba)) ** 2, axis=1)
    y2 = y * y * l2
    z2 = z * z * l2
    k = math.copysign(1.0, rr) * rr * rr * x2
    first = numpy.sign(z) * a2 * z2 > k
    second = numpy.sign(y) * a2 * y2 < k
    result = (numpy.sqrt(x2 * a2 * il2) + y * rr) * il2 - r1
    result = numpy.where(second, numpy.sqrt(x2 + y2) * il2 - r1, result)
    return numpy.where(first, numpy.sqrt(x2 + z2) * il2 - r2, result)


def loft_distance(q, knots, table):
    along = q[:, 2]
    params = hermite(knots, table, along)
    du = q[:, 0] - params[:, 6]
    dv = q[:, 1] - params[:, 7]
    r = numpy.sqrt(du * du + dv * dv) + 1e-9
    c = du / r
    s = dv / r
    radius = section_radius(c, s, params)
    step = 1e-3
    ahead = section_radius(c, s, hermite(knots, table, along + step))
    behind = section_radius(c, s, hermite(knots, table, along - step))
    slope_along = (ahead - behind) / (2.0 * step)
    turn = 0.02
    ct = math.cos(turn)
    st = math.sin(turn)
    left = section_radius(c * ct - s * st, s * ct + c * st, params)
    right = section_radius(c * ct + s * st, s * ct - c * st, params)
    slope_around = (left - right) / (2.0 * turn) / numpy.maximum(r, 1e-3)
    radial = (r - radius) / numpy.sqrt(1.0 + slope_along * slope_along + slope_around * slope_around)
    over = numpy.maximum(knots[0] - along, along - knots[-1])
    outside = numpy.where(radial > 0.0, numpy.sqrt(numpy.maximum(radial, 0.0) ** 2 + over * over), over)
    return numpy.where(over > 0.0, outside, numpy.maximum(radial, over))


def ellipsoid(label, center, radii, frame=None, blend=0.0, mode="add"):
    return shape("ellipsoid", label, blend, mode, center=numpy.asarray(center, dtype=numpy.float64), radii=numpy.asarray(radii, dtype=numpy.float64), frame=numpy.eye(3) if frame is None else numpy.asarray(frame, dtype=numpy.float64))


def cone(label, a, b, r1, r2, blend=0.0, mode="add"):
    return shape("cone", label, blend, mode, a=numpy.asarray(a, dtype=numpy.float64), b=numpy.asarray(b, dtype=numpy.float64), r1=float(r1), r2=float(r2))


def loft(label, origin, frame, stations, blend=0.0, mode="add"):
    stations = sorted(stations, key=lambda s: s[0])
    knots = numpy.array([s[0] for s in stations], dtype=numpy.float64)
    table = numpy.array([list(s[1:]) + [0.0] * (10 - len(s)) for s in stations], dtype=numpy.float64)
    table[:, 8] = numpy.radians(table[:, 8])
    return shape("loft", label, blend, mode, origin=numpy.asarray(origin, dtype=numpy.float64), frame=numpy.asarray(frame, dtype=numpy.float64), knots=knots, table=table)


def custom(label, function, low, high, blend=0.0, mode="add"):
    return shape("custom", label, blend, mode, function=function, low=low, high=high)


def bump(label, center, radii, amount, frame=None, power=2.0):
    return shape("bump", label, 0.0, "bump", center=numpy.asarray(center, dtype=numpy.float64), radii=numpy.asarray(radii, dtype=numpy.float64), frame=numpy.eye(3) if frame is None else numpy.asarray(frame, dtype=numpy.float64), amount=float(amount), power=float(power))


def ridge(label, points, radii, amount, power=2.0, vein=False, taper=0.0):
    return shape("ridge", label, 0.0, "bump", points=[numpy.asarray(p, dtype=numpy.float64) for p in points], radii=[float(r) for r in radii], amount=float(amount), power=float(power), vein=vein, taper=float(taper))


def groove(label, origin, frame, points, radius, amount, span, power=2.0, taper=0.0):
    return shape("groove", label, 0.0, "bump", origin=numpy.asarray(origin, dtype=numpy.float64), frame=numpy.asarray(frame, dtype=numpy.float64), points=[numpy.asarray(p, dtype=numpy.float64) for p in points], radius=float(radius), amount=float(amount), span=(float(span[0]), float(span[1])), power=float(power), taper=float(taper))


def tube(label, points, radii, blend=0.0, mode="add"):
    points = [numpy.asarray(p, dtype=numpy.float64) for p in points]
    radii = [float(r) for r in radii]

    def distance(query):
        result = numpy.full(len(query), numpy.inf)
        for index in range(len(points) - 1):
            if numpy.linalg.norm(points[index + 1] - points[index]) < 1e-9:
                value = numpy.linalg.norm(query - points[index], axis=1) - radii[index]
            else:
                value = round_cone(query, points[index], points[index + 1], radii[index], radii[index + 1])
            result = numpy.minimum(result, value)
        return result

    stack = numpy.array(points)
    reach = max(radii)
    return custom(label, distance, stack.min(axis=0) - reach, stack.max(axis=0) + reach, blend, mode)


def chain(label, joints, front, lateral, stations, blend=0.0, mode="add"):
    joints = [numpy.asarray(p, dtype=numpy.float64) for p in joints]
    start = joints[0]
    axis = joints[-1] - joints[0]
    w = unit(axis)
    front = numpy.asarray(front, dtype=numpy.float64)
    u = unit(front - w * numpy.dot(front, w))
    v = numpy.cross(w, u)
    if numpy.dot(v, lateral) < 0.0:
        v = -v
    rows = numpy.stack([u, v, w])
    result = []
    for station in stations:
        segment, fraction = station[0], station[1]
        a = joints[segment]
        b = joints[segment + 1]
        point = a + (b - a) * fraction
        offset = point - start
        along = float(offset @ w)
        du = float(offset @ u) + (station[8] if len(station) > 8 else 0.0)
        dv = float(offset @ v) + (station[9] if len(station) > 9 else 0.0)
        twist = station[10] if len(station) > 10 else 0.0
        result.append((along,) + tuple(station[2:8]) + (du, dv, twist))
    return loft(label, start, rows, result, blend, mode)


def zone(label, center, radius, blur):
    return shape("zone", label, 0.0, "smooth", center=numpy.asarray(center, dtype=numpy.float64), radius=float(radius), blur=float(blur))


def plane(label, point, normal, low, high, blend=0.0, mode="clip"):
    return shape("plane", label, blend, mode, point=numpy.asarray(point, dtype=numpy.float64), normal=unit(normal), low=low, high=high)


flip = numpy.array([-1.0, 1.0, 1.0])


def mirror_label(label):
    return label.replace(" L ", " R ").replace("_l_", "_r_") if " L " in label or "_l_" in label else label.replace(" R ", " L ").replace("_r_", "_l_")


def mirrored(item):
    d = dict(item.data)
    if item.kind == "ellipsoid":
        d["center"] = d["center"] * flip
        d["frame"] = d["frame"] * flip
    elif item.kind == "cone":
        d["a"] = d["a"] * flip
        d["b"] = d["b"] * flip
    elif item.kind == "loft":
        d["origin"] = d["origin"] * flip
        d["frame"] = d["frame"] * flip
    elif item.kind == "bump":
        d["center"] = d["center"] * flip
        d["frame"] = d["frame"] * flip
    elif item.kind == "ridge":
        d["points"] = [p * flip for p in d["points"]]
    elif item.kind == "groove":
        d["origin"] = d["origin"] * flip
        d["frame"] = d["frame"] * flip
    elif item.kind == "custom":
        source = d["function"]
        d["function"] = lambda points, source=source: source(points * flip)
        if "blend_field" in d:
            field = d["blend_field"]
            d["blend_field"] = lambda points, field=field: field(points * flip)
        low = numpy.asarray(d["low"]) * flip
        high = numpy.asarray(d["high"]) * flip
        d["low"] = numpy.minimum(low, high)
        d["high"] = numpy.maximum(low, high)
        if "nail" in d:
            origin, rows, start, end, half, level = d["nail"]
            d["nail"] = (origin * flip, rows * flip, start, end, half, level)
    elif item.kind == "zone":
        d["center"] = d["center"] * flip
    elif item.kind == "plane":
        d["point"] = d["point"] * flip
        d["normal"] = d["normal"] * flip
        low = numpy.asarray(d["low"]) * flip
        high = numpy.asarray(d["high"]) * flip
        d["low"] = numpy.minimum(low, high)
        d["high"] = numpy.maximum(low, high)
    return shape(item.kind, mirror_label(item.label), item.blend, item.mode, **d)


def cells_of(points, size):
    keys = numpy.floor(points / size).astype(numpy.int64)
    keys -= keys.min(axis=0)
    span = keys.max(axis=0) + 1
    flat = (keys[:, 0] * span[1] + keys[:, 1]) * span[2] + keys[:, 2]
    order = numpy.argsort(flat, kind='stable')
    flat = flat[order]
    starts = numpy.flatnonzero(numpy.r_[True, flat[1:] != flat[:-1]])
    ends = numpy.r_[starts[1:], len(flat)]
    sorted_points = points[order]
    low = numpy.minimum.reduceat(sorted_points, starts, axis=0)
    high = numpy.maximum.reduceat(sorted_points, starts, axis=0)
    return order, starts, ends, low, high


def gather(starts, ends):
    lengths = ends - starts
    total = int(lengths.sum())
    if total == 0:
        return numpy.zeros(0, dtype=numpy.int64)
    offsets = numpy.repeat(starts - numpy.r_[0, numpy.cumsum(lengths)[:-1]], lengths)
    return numpy.arange(total, dtype=numpy.int64) + offsets


stencil = numpy.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])


def evaluate(shapes, points, margin, cell=0.02, labels=False, empty=1.0):
    points = numpy.asarray(points, dtype=numpy.float64)
    zones = [item for item in shapes if item.mode == "smooth"]
    if zones:
        solid = [item for item in shapes if item.mode != "smooth"]
        result = evaluate(solid, points, margin, cell, labels, empty)
        distance = result[0] if labels else result
        for zone in zones:
            reach = numpy.linalg.norm(points - zone.data["center"], axis=1) / zone.data["radius"]
            weight = numpy.clip((1.0 - reach) / 0.4, 0.0, 1.0)
            chosen = numpy.flatnonzero(weight > 0.0)
            if not len(chosen):
                continue
            weight = weight[chosen] * weight[chosen] * (3.0 - 2.0 * weight[chosen])
            total = distance[chosen].copy()
            norm = 1.0
            for ring, share in ((1.0, 1.0), (2.0, 0.5)):
                for offset in stencil:
                    total += share * evaluate(solid, points[chosen] + offset * (zone.data["blur"] * ring), margin + zone.data["blur"] * 2.0, cell, False, empty)
                    norm += share
            distance[chosen] = distance[chosen] * (1.0 - weight) + total / norm * weight
        return (distance, result[1]) if labels else distance
    order, starts, ends, low, high = cells_of(points, cell)
    sorted_points = points[order]
    distance = numpy.full(len(points), empty, dtype=numpy.float64)
    best = numpy.full(len(points), numpy.inf) if labels else None
    owner = numpy.full(len(points), -1, dtype=numpy.int32) if labels else None
    for index, item in enumerate(shapes):
        reach = margin + item.blend
        hit = numpy.all(high >= item.low - reach, axis=1) & numpy.all(low <= item.high + reach, axis=1)
        if not hit.any():
            continue
        chosen = gather(starts[hit], ends[hit])
        value = item.distance(sorted_points[chosen])
        if item.mode == "add":
            field = item.data.get("blend_field") if item.kind == "custom" else None
            distance[chosen] = smin(distance[chosen], value, item.blend if field is None else field(sorted_points[chosen]))
            if labels:
                closer = value < best[chosen]
                best[chosen] = numpy.where(closer, value, best[chosen])
                owner[chosen] = numpy.where(closer, index, owner[chosen])
        elif item.mode == "cut":
            distance[chosen] = smax(distance[chosen], -value, item.blend)
        elif item.mode == "clip":
            distance[chosen] = smax(distance[chosen], value, item.blend)
        elif item.mode == "bump":
            distance[chosen] = distance[chosen] - value
        elif item.mode == "graft":
            weight = item.data["weight"](sorted_points[chosen])
            distance[chosen] = distance[chosen] * (1.0 - weight) + value * weight
        elif item.mode == "seal":
            distance[chosen] = smin(distance[chosen], value, item.blend)
    result = numpy.empty_like(distance)
    result[order] = distance
    if labels:
        owners = numpy.empty_like(owner)
        owners[order] = owner
        return result, owners
    return result


def level_set(shapes, low, high, voxel, band=None):
    leaf = voxel * 8.0
    band = voxel * 3.0 if band is None else band
    first = numpy.floor(numpy.asarray(low) / leaf).astype(numpy.int64) - 1
    last = numpy.ceil(numpy.asarray(high) / leaf).astype(numpy.int64) + 1
    axes = [numpy.arange(first[i], last[i] + 1) for i in range(3)]
    grid = numpy.stack(numpy.meshgrid(*axes, indexing='ij'), axis=-1).reshape(-1, 3)
    centers = (grid * 8 + 3.5) * voxel
    coarse = evaluate(shapes, centers, leaf * 2.0, cell=leaf * 4.0, empty=1.0)
    active = numpy.abs(coarse) < leaf * 1.6
    shape_of = numpy.array([len(a) for a in axes])
    mask = active.reshape(shape_of)
    grown = mask.copy()
    for axis in range(3):
        for offset in (-1, 1):
            grown |= numpy.roll(mask, offset, axis=axis)
    mask = grown
    grown = mask.copy()
    for axis in range(3):
        for offset in (-1, 1):
            grown |= numpy.roll(mask, offset, axis=axis)
    leaves = grid[grown.reshape(-1)]
    print("LEVEL SET leaves", len(leaves), "voxel", voxel)
    result = openvdb.FloatGrid(band)
    result.transform = openvdb.createLinearTransform(voxelSize=voxel)
    result.gridClass = openvdb.GridClass.LEVEL_SET
    local = numpy.stack(numpy.meshgrid(numpy.arange(8), numpy.arange(8), numpy.arange(8), indexing='ij'), axis=-1).reshape(-1, 3)
    chunk = 4096
    for begin in range(0, len(leaves), chunk):
        block = leaves[begin:begin + chunk]
        voxels = (block[:, None, :] * 8 + local[None, :, :]).reshape(-1, 3)
        values = evaluate(shapes, voxels * voxel, band * 2.0, cell=leaf, empty=1.0)
        values = numpy.clip(values, -band, band).astype(numpy.float32).reshape(len(block), 8, 8, 8)
        for index in range(len(block)):
            origin = block[index] * 8
            result.copyFromArray(values[index], ijk=(int(origin[0]), int(origin[1]), int(origin[2])), tolerance=0.0)
    result.signedFloodFill()
    return result


def mesh_of(grid, adaptivity=0.0):
    if adaptivity > 0.0:
        points, triangles, quads = grid.convertToPolygons(isovalue=0.0, adaptivity=adaptivity)
        return numpy.asarray(points, dtype=numpy.float64), numpy.asarray(triangles, dtype=numpy.int64), numpy.asarray(quads, dtype=numpy.int64)
    points, quads = grid.convertToQuads(isovalue=0.0)
    return numpy.asarray(points, dtype=numpy.float64), numpy.zeros((0, 3), dtype=numpy.int64), numpy.asarray(quads, dtype=numpy.int64)[:, ::-1].copy()


def project(shapes, points, iterations=2, step=None):
    points = numpy.array(points, dtype=numpy.float64)
    for iteration in range(iterations):
        epsilon = 2e-5
        value = evaluate(shapes, points, 0.01)
        gradient = numpy.stack([(evaluate(shapes, points + numpy.array(offset) * epsilon, 0.01) - value) / epsilon for offset in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], axis=1)
        length2 = numpy.maximum(numpy.sum(gradient * gradient, axis=1), 1e-6)
        move = (value / length2)[:, None] * gradient
        limit = step if step is not None else 0.002
        size = numpy.linalg.norm(move, axis=1)
        move *= numpy.minimum(1.0, limit / numpy.maximum(size, 1e-12))[:, None]
        points -= move
    return points


def dense_sampler(grid, low, high, voxel):
    first = numpy.floor(numpy.asarray(low) / voxel).astype(numpy.int64)
    last = numpy.ceil(numpy.asarray(high) / voxel).astype(numpy.int64)
    size = last - first + 1
    array = numpy.zeros(tuple(int(s) for s in size), dtype=numpy.float32)
    grid.copyToArray(array, ijk=(int(first[0]), int(first[1]), int(first[2])))
    background = float(grid.background)

    def sample(points):
        f = numpy.asarray(points, dtype=numpy.float64) / voxel - first
        i = numpy.floor(f).astype(numpy.int64)
        t = f - i
        inside = numpy.all((i >= 0) & (i < size - 1), axis=1)
        result = numpy.full(len(points), background, dtype=numpy.float64)
        if inside.any():
            j = i[inside]
            u = t[inside]
            total = numpy.zeros(len(j))
            for dx in (0, 1):
                for dy in (0, 1):
                    for dz in (0, 1):
                        weight = (u[:, 0] if dx else 1.0 - u[:, 0]) * (u[:, 1] if dy else 1.0 - u[:, 1]) * (u[:, 2] if dz else 1.0 - u[:, 2])
                        total += weight * array[j[:, 0] + dx, j[:, 1] + dy, j[:, 2] + dz]
            result[inside] = total
        return result

    return sample
