import math
import numpy
import openvdb

far = 1.0
lateral = numpy.array([1.0, 0.0, 0.0])
flip = numpy.array([-1.0, 1.0, 1.0])


def unit(vector):
    vector = numpy.asarray(vector, dtype=numpy.float64)
    return vector / max(float(numpy.linalg.norm(vector)), 1e-12)


def smoothstep(low, high, value):
    t = numpy.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smin(a, b, k):
    if k <= 0.0:
        return numpy.minimum(a, b)
    h = numpy.maximum(k - numpy.abs(a - b), 0.0) / k
    return numpy.minimum(a, b) - h * h * h * k / 6.0


def smax(a, b, k):
    return -smin(-a, -b, k)


def rotation(axis, degrees):
    x, y, z = unit(axis)
    angle = math.radians(degrees)
    c = math.cos(angle)
    s = math.sin(angle)
    return numpy.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s], [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s], [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def frame_of(axis, roll=0.0):
    a = unit(axis)
    side = lateral - a * float(lateral @ a)
    if float(numpy.linalg.norm(side)) < 1e-6:
        side = numpy.array([0.0, 1.0, 0.0]) - a * a[1]
    u = unit(side)
    w = numpy.cross(u, a)
    if roll != 0.0:
        turn = rotation(a, roll)
        u = turn @ u
        w = turn @ w
    return numpy.stack([u, a, w])


def monotone_table(knots, values, count=128):
    knots = numpy.asarray(knots, dtype=numpy.float64)
    values = numpy.asarray(values, dtype=numpy.float64)
    h = numpy.diff(knots)
    delta = numpy.diff(values, axis=0) / h[:, None]
    slopes = numpy.zeros_like(values)
    slopes[0] = delta[0]
    slopes[-1] = delta[-1]
    for i in range(1, len(knots) - 1):
        same = delta[i - 1] * delta[i] > 0.0
        w1 = 2.0 * h[i] + h[i - 1]
        w2 = h[i] + 2.0 * h[i - 1]
        harmonic = (w1 + w2) / (w1 / numpy.where(same, delta[i - 1], 1.0) + w2 / numpy.where(same, delta[i], 1.0))
        slopes[i] = numpy.where(same, harmonic, 0.0)
    t = numpy.linspace(knots[0], knots[-1], count)
    index = numpy.clip(numpy.searchsorted(knots, t, side='right') - 1, 0, len(knots) - 2)
    span = h[index][:, None]
    x = ((t - knots[index]) / h[index])[:, None]
    x2 = x * x
    x3 = x2 * x
    return (2.0 * x3 - 3.0 * x2 + 1.0) * values[index] + (x3 - 2.0 * x2 + x) * span * slopes[index] + (-2.0 * x3 + 3.0 * x2) * values[index + 1] + (x3 - x2) * span * slopes[index + 1]


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


def gather(starts, ends):
    lengths = ends - starts
    total = int(lengths.sum())
    offsets = numpy.repeat(starts - numpy.r_[0, numpy.cumsum(lengths)[:-1]], lengths)
    return numpy.arange(total, dtype=numpy.int64) + offsets


class item:
    def __init__(self, distance, low, high, blend, mode, group, pair):
        self.distance = distance
        self.low = numpy.asarray(low, dtype=numpy.float64)
        self.high = numpy.asarray(high, dtype=numpy.float64)
        self.blend = blend
        self.mode = mode
        self.group = group
        self.pair = pair


class field:
    def __init__(self):
        self.items = []
        self.scale = 1.0

    def add(self, distance, low, high, blend=0.0, mode="add", group="core", pair=0.0):
        low = numpy.asarray(low, dtype=numpy.float64).copy()
        high = numpy.asarray(high, dtype=numpy.float64).copy()
        if pair:
            low[0] = min(low[0], 0.0)
        self.items.append(item(distance, low, high, blend, mode, group, pair))
        return self.items[-1]

    def ellipsoid(self, center, radii, axis=(0.0, 1.0, 0.0), roll=0.0, blend=0.03, mode="add", group="core", pair=0.0):
        center = numpy.asarray(center, dtype=numpy.float64)
        radii = numpy.asarray(radii, dtype=numpy.float64)
        frame = frame_of(axis, roll)

        def distance(points):
            q = (points - center) @ frame.T
            k0 = numpy.sqrt(numpy.sum((q / radii) ** 2, axis=1))
            k1 = numpy.sqrt(numpy.sum((q / (radii * radii)) ** 2, axis=1))
            return numpy.where(k1 > 1e-9, k0 * (k0 - 1.0) / numpy.maximum(k1, 1e-9), -float(radii.min()))

        reach = numpy.abs(frame.T) @ radii
        return self.add(distance, center - reach, center + reach, blend, mode, group, pair)

    def cone(self, a, b, r1, r2, blend=0.02, mode="add", group="core", pair=0.0):
        a = numpy.asarray(a, dtype=numpy.float64)
        b = numpy.asarray(b, dtype=numpy.float64)

        def distance(points):
            return round_cone(points, a, b, r1, r2)

        return self.add(distance, numpy.minimum(a - r1, b - r2), numpy.maximum(a + r1, b + r2), blend, mode, group, pair)

    def loft(self, origin, axis, stations, blend=0.03, mode="add", group="core", pair=0.0):
        origin = numpy.asarray(origin, dtype=numpy.float64)
        a = unit(axis)
        u = unit(lateral - a * float(lateral @ a))
        v = numpy.cross(u, a)
        rows = sorted([tuple(s) + (2.0,) * (8 - len(s)) for s in stations], key=lambda s: s[0])
        knots = numpy.array([s[0] for s in rows])
        table = monotone_table(knots, numpy.array([s[1:] for s in rows]))
        s0 = float(knots[0])
        s1 = float(knots[-1])
        count = len(table) - 1

        def distance(points):
            rel = points - origin
            s = rel @ a
            f = numpy.clip((s - s0) / (s1 - s0), 0.0, 1.0) * count
            i = numpy.minimum(f.astype(numpy.int64), count - 1)
            t = (f - i)[:, None]
            params = table[i] * (1.0 - t) + table[i + 1] * t
            x = rel @ u - params[:, 0]
            y = rel @ v - params[:, 1]
            upper = y >= 0.0
            ru = params[:, 2]
            rv = numpy.where(upper, params[:, 3], params[:, 4])
            n = numpy.where(upper, params[:, 5], params[:, 6])
            X = numpy.abs(x) / ru + 1e-9
            Y = numpy.abs(y) / rv + 1e-9
            r = (X ** n + Y ** n) ** (1.0 / n)
            slope = r ** (1.0 - n) * numpy.sqrt((X ** (n - 1.0) / ru) ** 2 + (Y ** (n - 1.0) / rv) ** 2)
            radial = numpy.maximum((r - 1.0) / numpy.maximum(slope, 1e-9), -numpy.minimum(ru, rv))
            over = numpy.maximum(s0 - s, s - s1)
            return numpy.where(over > 0.0, numpy.sqrt(numpy.maximum(radial, 0.0) ** 2 + over * over), numpy.maximum(radial, over))

        along = numpy.linspace(s0, s1, count + 1)
        centers = origin[None, :] + along[:, None] * a[None, :] + table[:, 0:1] * u[None, :] + table[:, 1:2] * v[None, :]
        corners = []
        for side in (-1.0, 1.0):
            corners.append(centers + side * table[:, 2:3] * u[None, :] + table[:, 3:4] * v[None, :])
            corners.append(centers + side * table[:, 2:3] * u[None, :] - table[:, 4:5] * v[None, :])
        corners = numpy.concatenate(corners)
        return self.add(distance, corners.min(axis=0), corners.max(axis=0), blend, mode, group, pair)

    def bump(self, center, radii, amount, axis=(0.0, 1.0, 0.0), roll=0.0, group="core", pair=False):
        center = numpy.asarray(center, dtype=numpy.float64)
        radii = numpy.asarray(radii, dtype=numpy.float64)
        frame = frame_of(axis, roll)

        def displacement(points):
            q = (points - center) @ frame.T / radii
            w = numpy.clip(1.0 - numpy.sum(q * q, axis=1), 0.0, 1.0)
            return amount * w * w

        reach = numpy.abs(frame.T) @ radii
        return self.add(displacement, center - reach, center + reach, 0.0, "bump", group, 1.0 if pair else 0.0)

    def ridge(self, points, radius, amount, taper=0.2, group="core", pair=False):
        path = numpy.asarray(points, dtype=numpy.float64)
        radii = numpy.full(len(path), radius, dtype=numpy.float64) if numpy.isscalar(radius) else numpy.asarray(radius, dtype=numpy.float64)
        lengths = numpy.linalg.norm(numpy.diff(path, axis=0), axis=1)
        travel = numpy.r_[0.0, numpy.cumsum(lengths)] / max(float(lengths.sum()), 1e-9)

        def displacement(query):
            best = numpy.zeros(len(query))
            for index in range(len(path) - 1):
                a = path[index]
                ab = path[index + 1] - a
                t = numpy.clip(((query - a) @ ab) / float(ab @ ab), 0.0, 1.0)
                d = numpy.linalg.norm(query - a - t[:, None] * ab, axis=1)
                r = radii[index] + (radii[index + 1] - radii[index]) * t
                w = numpy.clip(1.0 - (d / r) ** 2, 0.0, 1.0) ** 2
                if taper > 0.0:
                    position = travel[index] + (travel[index + 1] - travel[index]) * t
                    w = w * numpy.clip(position / taper, 0.0, 1.0) * numpy.clip((1.0 - position) / taper, 0.0, 1.0)
                best = numpy.maximum(best, w)
            return amount * best

        reach = float(radii.max())
        return self.add(displacement, path.min(axis=0) - reach, path.max(axis=0) + reach, 0.0, "bump", group, 1.0 if pair else 0.0)

    def custom(self, function, low, high, blend=0.0, mode="bump", group="core", pair=0.0):
        return self.add(function, low, high, blend, mode, group, pair)

    def combine(self, entry, current, points):
        value = entry.distance(points)
        if entry.mode == "bump":
            if entry.pair:
                value = value + entry.distance(points * flip)
            return current - value
        if entry.pair:
            value = smin(value, entry.distance(points * flip), entry.pair)
        if entry.mode == "add":
            return smin(current, value, entry.blend)
        if entry.mode == "cut":
            return smax(current, -value, entry.blend)
        return smax(current, value, entry.blend)

    def chosen(self, groups):
        return [entry for entry in self.items if groups is None or entry.group in groups]

    def evaluate(self, points, groups=None, margin=0.05):
        points = numpy.asarray(points, dtype=numpy.float64) / self.scale
        folded = points.copy()
        folded[:, 0] = numpy.abs(folded[:, 0])
        entries = self.chosen(groups)
        distance = numpy.full(len(folded), far)
        if len(folded) > 40000:
            cell = 0.06
            keys = numpy.floor(folded / cell).astype(numpy.int64)
            keys -= keys.min(axis=0)
            size = keys.max(axis=0) + 1
            flat = (keys[:, 0] * size[1] + keys[:, 1]) * size[2] + keys[:, 2]
            order = numpy.argsort(flat, kind='stable')
            ordered = folded[order]
            unique, starts = numpy.unique(flat[order], return_index=True)
            ends = numpy.r_[starts[1:], len(ordered)]
            low = numpy.minimum.reduceat(ordered, starts, axis=0)
            high = numpy.maximum.reduceat(ordered, starts, axis=0)
            for entry in entries:
                reach = margin + entry.blend
                hit = numpy.all(high >= entry.low - reach, axis=1) & numpy.all(low <= entry.high + reach, axis=1)
                if hit.any():
                    picked = gather(starts[hit], ends[hit])
                    distance[picked] = self.combine(entry, distance[picked], ordered[picked])
            result = numpy.empty_like(distance)
            result[order] = distance
            return result * self.scale
        for entry in entries:
            reach = margin + entry.blend
            hit = numpy.all(folded >= entry.low - reach, axis=1) & numpy.all(folded <= entry.high + reach, axis=1)
            if hit.any():
                distance[hit] = self.combine(entry, distance[hit], folded[hit])
        return distance * self.scale

    def sample(self, points, groups=None, step=0.0015):
        points = numpy.asarray(points, dtype=numpy.float64)
        corners = numpy.array([[1.0, -1.0, -1.0], [-1.0, -1.0, 1.0], [-1.0, 1.0, -1.0], [1.0, 1.0, 1.0]])
        stacked = (points[None, :, :] + corners[:, None, :] * step).reshape(-1, 3)
        values = self.evaluate(stacked, groups).reshape(4, len(points))
        gradient = (corners[:, None, :] * values[:, :, None]).sum(axis=0) / (4.0 * step)
        return values.mean(axis=0), gradient

    def normals(self, points, groups=None, step=0.0015):
        value, gradient = self.sample(points, groups, step)
        return gradient / numpy.maximum(numpy.linalg.norm(gradient, axis=1), 1e-9)[:, None]

    def project(self, points, groups=None, iterations=8, limit=0.012):
        points = numpy.array(points, dtype=numpy.float64)
        for iteration in range(iterations):
            value, gradient = self.sample(points, groups)
            length2 = numpy.maximum(numpy.sum(gradient * gradient, axis=1), 0.04)
            move = (value / length2)[:, None] * gradient
            size = numpy.linalg.norm(move, axis=1)
            move *= numpy.minimum(1.0, limit / numpy.maximum(size, 1e-12))[:, None]
            points -= move
        return points

    def cast(self, origins, directions, reach, groups=None, steps=96, refine=14, last=False):
        origins = numpy.asarray(origins, dtype=numpy.float64)
        directions = numpy.asarray(directions, dtype=numpy.float64)
        t = numpy.linspace(0.0, reach, steps)
        points = origins[:, None, :] + directions[:, None, :] * t[None, :, None]
        inside = self.evaluate(points.reshape(-1, 3), groups).reshape(len(origins), steps) < 0.0
        crossing = inside[:, :-1] & ~inside[:, 1:]
        found = crossing.any(axis=1)
        index = (steps - 2 - crossing[:, ::-1].argmax(axis=1)) if last else crossing.argmax(axis=1)
        index = numpy.where(found, index, 0)
        low = t[index]
        high = t[index + 1]
        for iteration in range(refine):
            middle = 0.5 * (low + high)
            negative = self.evaluate(origins + directions * middle[:, None], groups) < 0.0
            low = numpy.where(negative, middle, low)
            high = numpy.where(negative, high, middle)
        return 0.5 * (low + high), found

    def polygonize(self, low, high, voxel, groups=None):
        leaf = voxel * 8.0
        first = numpy.floor(numpy.asarray(low) / leaf).astype(numpy.int64) - 1
        last = numpy.ceil(numpy.asarray(high) / leaf).astype(numpy.int64) + 1
        axes = [numpy.arange(first[i], last[i] + 1) for i in range(3)]
        lattice = numpy.stack(numpy.meshgrid(*axes, indexing='ij'), axis=-1).reshape(-1, 3)
        coarse = self.evaluate((lattice * 8 + 3.5) * voxel, groups, leaf * 2.5)
        mask = (numpy.abs(coarse) < leaf * 1.6).reshape([len(a) for a in axes])
        grown = mask.copy()
        for axis in range(3):
            for offset in (-1, 1):
                grown |= numpy.roll(mask, offset, axis=axis)
        leaves = lattice[grown.reshape(-1)]
        band = voxel * 3.0
        grid = openvdb.FloatGrid(band)
        grid.transform = openvdb.createLinearTransform(voxelSize=voxel)
        grid.gridClass = openvdb.GridClass.LEVEL_SET
        local = numpy.stack(numpy.meshgrid(numpy.arange(8), numpy.arange(8), numpy.arange(8), indexing='ij'), axis=-1).reshape(-1, 3)
        for begin in range(0, len(leaves), 2048):
            block = leaves[begin:begin + 2048]
            voxels = (block[:, None, :] * 8 + local[None, :, :]).reshape(-1, 3)
            values = numpy.clip(self.evaluate(voxels * voxel, groups, band * 3.0), -band, band).astype(numpy.float32).reshape(len(block), 8, 8, 8)
            for index in range(len(block)):
                origin = block[index] * 8
                grid.copyFromArray(values[index], ijk=(int(origin[0]), int(origin[1]), int(origin[2])), tolerance=0.0)
        grid.signedFloodFill()
        points, quads = grid.convertToQuads(isovalue=0.0)
        return numpy.asarray(points, dtype=numpy.float64), numpy.asarray(quads, dtype=numpy.int64)[:, ::-1].copy()
