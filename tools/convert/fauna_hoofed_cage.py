import math
import numpy
import fauna_hoofed_field as fields

flip = numpy.array([-1.0, 1.0, 1.0])


def resample(poly, count, closed=False):
    poly = numpy.asarray(poly, dtype=numpy.float64)
    if closed:
        poly = numpy.vstack([poly, poly[:1]])
    seg = numpy.linalg.norm(numpy.diff(poly, axis=0), axis=1)
    cum = numpy.r_[0.0, numpy.cumsum(seg)]
    targets = numpy.linspace(0.0, cum[-1], count + 1)
    index = numpy.clip(numpy.searchsorted(cum, targets, side='right') - 1, 0, len(seg) - 1)
    t = (targets - cum[index]) / numpy.maximum(seg[index], 1e-12)
    result = poly[index] + (poly[index + 1] - poly[index]) * t[:, None]
    return result[:-1] if closed else result


def newell(points):
    rolled = numpy.roll(points, -1, axis=0)
    return numpy.array([numpy.sum((points[:, 1] - rolled[:, 1]) * (points[:, 2] + rolled[:, 2])), numpy.sum((points[:, 2] - rolled[:, 2]) * (points[:, 0] + rolled[:, 0])), numpy.sum((points[:, 0] - rolled[:, 0]) * (points[:, 1] + rolled[:, 1]))])


class builder:
    def __init__(self):
        self.points = []
        self.part = []
        self.pinned = []
        self.coord = []
        self.faces = []
        self.tags = []
        self.welds = []
        self.cuts = []
        self.seeds = []
        self.meta = {}

    def vertex(self, point, part, pinned=False, coord=(0.0, 0.0)):
        self.points.append(numpy.array(point, dtype=numpy.float64))
        self.part.append(part)
        self.pinned.append(pinned)
        self.coord.append(coord)
        return len(self.points) - 1

    def face(self, ids, tag):
        clean = []
        for index in ids:
            index = int(index)
            if not clean or clean[-1] != index:
                clean.append(index)
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        if len(clean) >= 3:
            self.faces.append(tuple(clean))
            self.tags.append(tag)

    def at(self, ids):
        return numpy.array([self.points[int(i)] for i in ids])

    def ring(self, points, part, pinned=False, level=0.0):
        return [self.vertex(p, part, pinned, (level, index / len(points))) for index, p in enumerate(points)]

    def band(self, first, second, tag):
        count = len(first)
        for index in range(count):
            self.face((first[index], first[(index + 1) % count], second[(index + 1) % count], second[index]), tag)

    def fan(self, loop, point, part, tag, pinned=False):
        center = self.vertex(point, part, pinned)
        for index in range(len(loop)):
            self.face((loop[index], loop[(index + 1) % len(loop)], center), tag)
        return center

    def stitch(self, first, second, tag):
        pa = self.at(first)
        pb = self.at(second)
        if float(newell(pa) @ newell(pb)) < 0.0:
            first = first[::-1]
            pa = pa[::-1]
        best = None
        for start in range(len(first)):
            rolled = numpy.roll(pa, -start, axis=0)
            picks = rolled[(numpy.arange(len(second)) * len(first)) // len(second)]
            cost = float(numpy.sum(numpy.linalg.norm(pb - picks, axis=1)))
            if best is None or cost < best[0]:
                best = (cost, start)
        first = list(first[best[1]:]) + list(first[:best[1]])
        na = len(first)
        nb = len(second)
        if na == nb:
            self.band(first, second, tag)
            return first
        tolerance = 0.45 * min(1.0 / na, 1.0 / nb)
        i = 0
        j = 0
        while i < na or j < nb:
            ta = (i + 1) / na if i < na else 9.0
            tb = (j + 1) / nb if j < nb else 9.0
            if i < na and j < nb and abs(ta - tb) < tolerance:
                self.face((first[i], first[(i + 1) % na], second[(j + 1) % nb], second[j]), tag)
                i += 1
                j += 1
            elif ta < tb:
                self.face((first[i], first[(i + 1) % na], second[j % nb]), tag)
                i += 1
            else:
                self.face((first[i % na], second[(j + 1) % nb], second[j]), tag)
                j += 1
        return first


class patch:
    def __init__(self, ids, tags):
        self.ids = numpy.array(ids, dtype=numpy.int64)
        self.alt = self.ids.copy()
        rows, cols = self.ids.shape
        self.removed = numpy.zeros((rows - 1, cols - 1), dtype=bool)
        self.lower = numpy.zeros((rows - 1, cols - 1), dtype=bool)
        self.tags = tags

    def hole(self, r0, r1, c0, c1):
        self.removed[r0:r1, c0:c1] = True
        ids = self.ids
        return [int(ids[r0, c]) for c in range(c0, c1)] + [int(ids[r, c1]) for r in range(r0, r1)] + [int(ids[r1, c]) for c in range(c1, c0, -1)] + [int(ids[r, c0]) for r in range(r1, r0, -1)]

    def emit(self, b):
        rows, cols = self.removed.shape
        for r in range(rows):
            for c in range(cols):
                if not self.removed[r, c]:
                    ids = self.alt if self.lower[r, c] else self.ids
                    tag = self.tags(r, c) if callable(self.tags) else self.tags
                    b.face((ids[r, c], ids[r + 1, c], ids[r + 1, c + 1], ids[r, c + 1]), tag)


def spine_frames(stations, pivots=()):
    stations = [list(s) for s in stations]
    for first, last, pivot in pivots:
        for index in range(first, last + 1):
            stations[index][2] = math.degrees(math.atan2(stations[index][0] - pivot[0], stations[index][1] - pivot[1]))
    points = numpy.array([(s[0], s[1]) for s in stations], dtype=numpy.float64)
    centers = []
    angles = []
    starts = []
    for i in range(len(stations) - 1):
        starts.append(len(centers))
        length = float(numpy.linalg.norm(points[i + 1] - points[i]))
        count = max(1, int(round(length / (0.5 * (stations[i][3] + stations[i + 1][3])))))
        p0 = points[max(i - 1, 0)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        for step in range(count):
            t = step / count
            centers.append(0.5 * (2.0 * p1 + (p2 - p0) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t * t * t))
            angles.append(stations[i][2] + (stations[i + 1][2] - stations[i][2]) * t)
    starts.append(len(centers))
    centers.append(points[-1])
    angles.append(stations[-1][2])
    for first, last, pivot in pivots:
        for index in range(starts[first], starts[last] + 1):
            angles[index] = math.degrees(math.atan2(centers[index][0] - pivot[0], centers[index][1] - pivot[1]))
    return numpy.array(centers), numpy.array(angles), starts


def ring_frame(angle):
    a = math.radians(angle)
    return numpy.array([0.0, -math.cos(a), math.sin(a)]), numpy.array([0.0, math.sin(a), math.cos(a)])


def cast_spine(f, centers, angles, half, groups, reach=0.9, rays=129):
    theta = numpy.linspace(0.0, math.pi, rays)
    origins = []
    directions = []
    for center, angle in zip(centers, angles):
        forward, up = ring_frame(angle)
        origins.append(numpy.tile(numpy.array([0.0, center[0], center[1]]), (rays, 1)))
        directions.append(numpy.cos(theta)[:, None] * up[None, :] + numpy.sin(theta)[:, None] * fields.lateral[None, :])
    origins = numpy.concatenate(origins)
    directions = numpy.concatenate(directions)
    distance, found = f.cast(origins, directions, reach, groups, steps=220)
    if not found.all():
        print("CAGE spine rays missed", int((~found).sum()))
    outline = (origins + directions * distance[:, None]).reshape(len(centers), rays, 3)
    rings = []
    for index in range(len(centers)):
        ring = resample(outline[index], half)
        ring[0, 0] = 0.0
        ring[-1, 0] = 0.0
        rings.append(ring)
    return rings


def cap_points(f, ring, axis, n, m, groups, depth=0.3):
    grid = numpy.zeros((n + 1, m + 1, 3))
    top_right = ring[m]
    bottom_right = ring[m + n]
    top_left = top_right * flip
    bottom_left = bottom_right * flip
    for j in range(n + 1):
        v = j / n
        right = ring[m + j]
        left = right * flip
        for c in range(m + 1):
            a = (c / m + 1.0) * 0.5
            top = ring[c]
            bottom = ring[m + n + (m - c)]
            grid[j, c] = (1.0 - v) * top + v * bottom + (1.0 - a) * left + a * right - ((1.0 - a) * (1.0 - v) * top_left + a * (1.0 - v) * top_right + (1.0 - a) * v * bottom_left + a * v * bottom_right)
    inner = grid[1:n, 0:m].reshape(-1, 3)
    origins = inner - axis[None, :] * 0.03
    distance, found = f.cast(origins, numpy.tile(axis, (len(origins), 1)), depth, groups, steps=160)
    hit = origins + axis[None, :] * distance[:, None]
    grid[1:n, 0:m] = numpy.where(found[:, None], hit, inner).reshape(n - 1, m, 3)
    grid[:, 0, 0] = 0.0
    return grid


def add_cap(b, f, ring_ids, axis, n, m, part, groups):
    ring = b.at(ring_ids)
    grid = cap_points(f, ring, axis, n, m, groups)
    ids = numpy.full((n + 1, m + 1), -1, dtype=numpy.int64)
    for c in range(m + 1):
        ids[0, c] = ring_ids[c]
        ids[n, c] = ring_ids[m + n + (m - c)]
    for j in range(n + 1):
        ids[j, m] = ring_ids[m + j]
    for j in range(1, n):
        for c in range(m):
            ids[j, c] = b.vertex(grid[j, c], part, coord=(j / n, c / m))
    return ids


def limb_frames(path):
    points = []
    for index in range(len(path) - 1):
        a = numpy.asarray(path[index][0], dtype=numpy.float64)
        c = numpy.asarray(path[index + 1][0], dtype=numpy.float64)
        count = path[index][1]
        for step in range(count):
            points.append(a + (c - a) * (step / count))
    points.append(numpy.asarray(path[-1][0], dtype=numpy.float64))
    points = numpy.array(points)
    tangents = numpy.gradient(points, axis=0)
    tangents /= numpy.linalg.norm(tangents, axis=1)[:, None]
    return points, tangents


def cast_limb(f, points, tangents, around, groups, reach=0.4, rays=144):
    phi = numpy.linspace(0.0, 2.0 * math.pi, rays, endpoint=False)
    origins = []
    directions = []
    for center, axis in zip(points, tangents):
        front = fields.unit(numpy.array([0.0, -1.0, 0.0]) - axis * (-axis[1]))
        side = numpy.cross(front, axis)
        origins.append(numpy.tile(center, (rays, 1)))
        directions.append(numpy.cos(phi)[:, None] * front[None, :] + numpy.sin(phi)[:, None] * side[None, :])
    origins = numpy.concatenate(origins)
    directions = numpy.concatenate(directions)
    distance, found = f.cast(origins, directions, reach, groups, steps=160)
    if not found.all():
        print("CAGE limb rays missed", int((~found).sum()))
    outline = (origins + directions * distance[:, None]).reshape(len(points), rays, 3)
    return [resample(outline[index], around, closed=True) for index in range(len(points))]


def bury(f, b, grid, group, limit, grow, bounds):
    rows, cols = grid.shape
    points = b.at(grid.reshape(-1))
    inside = (f.evaluate(points, (group,)) < -0.002) & (points[:, 2] < limit)
    inside = inside.reshape(rows, cols)
    inside[:, :bounds[0]] = False
    inside[:, bounds[1] + 1:] = False
    found = numpy.argwhere(inside)
    if not len(found):
        raise RuntimeError("no footprint for " + group)
    r0 = max(int(found[:, 0].min()) - grow, 1)
    r1 = min(int(found[:, 0].max()) + grow, rows - 2)
    c0 = max(int(found[:, 1].min()) - grow, bounds[0])
    c1 = min(int(found[:, 1].max()) + grow, bounds[1])
    return r0, r1, c0, c1


def nearest_cell(b, grid, target):
    points = b.at(grid.reshape(-1))
    index = int(numpy.argmin(numpy.linalg.norm(points - numpy.asarray(target)[None, :], axis=1)))
    return index // grid.shape[1], index % grid.shape[1]


def eye_rings(eye, count=16):
    center = numpy.asarray(eye["center"], dtype=numpy.float64)
    axis = fields.unit(eye["axis"])
    slit = fields.unit(numpy.asarray(eye["slit"], dtype=numpy.float64) - axis * float(numpy.asarray(eye["slit"]) @ axis))
    up = numpy.cross(axis, slit)
    if up[2] < 0.0:
        up = -up
    radius = eye["radius"]
    wide, tall = [math.radians(a) for a in eye["open"]]
    rings = []
    for scale, lift in ((1.42, 0.0045), (1.0, 0.003), (0.97, 0.0006), (1.16, 0.0006)):
        ring = []
        for index in range(count):
            psi = 2.0 * math.pi * index / count
            a = wide * math.cos(psi) * scale
            e = tall * math.sin(psi) * abs(math.sin(psi)) ** 0.25 * scale
            direction = fields.unit(axis + math.tan(a) * slit + math.tan(e) * up)
            ring.append(center + direction * (radius + lift))
        rings.append(numpy.array(ring))
    return rings


def eyeball(eye, segments=12):
    center = numpy.asarray(eye["center"], dtype=numpy.float64)
    axis = fields.unit(eye["axis"])
    slit = fields.unit(numpy.asarray(eye["slit"], dtype=numpy.float64) - axis * float(numpy.asarray(eye["slit"]) @ axis))
    up = numpy.cross(axis, slit)
    radius = eye["radius"]
    points = [center + axis * radius]
    faces = []
    levels = (24.0, 47.0, 70.0)
    for level, angle in enumerate(levels):
        a = math.radians(angle)
        for index in range(segments):
            psi = 2.0 * math.pi * index / segments
            points.append(center + radius * (math.cos(a) * axis + math.sin(a) * (math.cos(psi) * slit + math.sin(psi) * up)))
    for index in range(segments):
        faces.append((0, 1 + index, 1 + (index + 1) % segments))
    for level in range(len(levels) - 1):
        base = 1 + level * segments
        for index in range(segments):
            faces.append((base + index, base + segments + index, base + segments + (index + 1) % segments, base + (index + 1) % segments))
    return numpy.array(points), faces


def ear_rings(ear, around=12):
    root = numpy.asarray(ear["root"], dtype=numpy.float64)
    axis = fields.unit(ear["axis"])
    face = numpy.asarray(ear["face"], dtype=numpy.float64)
    face = fields.unit(face - axis * float(face @ axis))
    across = numpy.cross(axis, face)
    length = ear["length"]
    width = ear["width"]
    back = around // 2 + 1
    front = around - back
    rings = []
    levels = ear.get("levels", (0.06, 0.16, 0.28, 0.42, 0.56, 0.7, 0.82, 0.92, 0.98))
    for t in levels:
        profile = (0.62 + 0.38 * math.sin(math.pi * min(t / 0.45, 1.0) * 0.5)) * (1.0 if t < 0.45 else math.cos(math.pi * 0.5 * ((t - 0.45) / 0.57) ** ear.get("point", 1.6)))
        half = 0.5 * width * max(profile, 0.05)
        roll = 1.0 - float(fields.smoothstep(0.0, 0.3, t))
        cup = half * (0.55 + 0.5 * roll)
        thick = ear.get("thickness", 0.006) * (1.0 - 0.6 * t) + 0.01 * roll
        center = root + axis * (length * t) - face * (ear.get("curl", 0.02) * t * t)
        ring = []
        for index in range(back):
            a = -1.0 + 2.0 * index / (back - 1)
            bend = 1.0 - a * a
            ring.append(center + across * (a * half) + face * (cup * (0.35 - bend) - 0.5 * thick * bend))
        for index in range(front):
            a = 1.0 - 2.0 * (index + 1) / (front + 1)
            bend = 1.0 - a * a
            ring.append(center + across * (a * half * 0.92) + face * (cup * (0.35 - bend) + 0.5 * thick * bend + roll * cup * 1.6 * bend))
        rings.append(numpy.array(ring))
    tip = root + axis * (length * 1.005) - face * ear.get("curl", 0.02)
    return rings, tip


def tube_rings(path, radii, around, flat=1.0, up=(0.0, 1.0, 0.0)):
    path = numpy.asarray(path, dtype=numpy.float64)
    tangents = numpy.gradient(path, axis=0)
    tangents /= numpy.linalg.norm(tangents, axis=1)[:, None]
    rings = []
    normal = None
    for index in range(len(path)):
        axis = tangents[index]
        hint = numpy.asarray(up, dtype=numpy.float64) if normal is None else normal
        normal = fields.unit(hint - axis * float(hint @ axis))
        side = numpy.cross(axis, normal)
        phi = 2.0 * math.pi * numpy.arange(around) / around
        rings.append(path[index][None, :] + radii[index] * (numpy.cos(phi)[:, None] * normal[None, :] * flat + numpy.sin(phi)[:, None] * side[None, :]))
    return rings


def build_skin(blueprint):
    f = blueprint["field"]
    spec = blueprint["cage"]
    marks = blueprint["marks"]
    core = spec["core"]
    b = builder()
    around = spec["around"]
    half = around // 2
    n = around // 4
    m = n // 2
    centers, angles, starts = spine_frames(spec["spine"], spec.get("pivots", ()))
    rings = cast_spine(f, centers, angles, half, core)
    count = len(rings)
    head_ring = starts[spec["head_station"]]
    tube = numpy.zeros((count, half + 1), dtype=numpy.int64)
    for r in range(count):
        for s in range(half + 1):
            tube[r, s] = b.vertex(rings[r][s], "head" if r >= head_ring else "body", coord=(float(r), s / around))
    b.meta["tube"] = tube
    b.meta["head_ring"] = head_ring
    b.meta["centers"] = centers
    b.meta["angles"] = angles

    rear_axis = -ring_frame(angles[0])[0]
    front_axis = ring_frame(angles[-1])[0]
    rear = add_cap(b, f, [int(i) for i in tube[0]], rear_axis, n, m, "rump", core)
    front = add_cap(b, f, [int(i) for i in tube[-1]], front_axis, n, m, "nose", core)
    body = patch(tube, lambda r, c: "head" if r >= head_ring else "body")
    rear_patch = patch(rear, "rump")
    mouth = spec["mouth"]
    row = mouth["row"]
    column = m + row
    front_patch = patch(front, lambda r, c: "nose" if r < row else "chin")

    corner_ring = nearest_cell(b, tube[:, column:column + 1], marks["mouth"])[0]
    upper = [int(tube[corner_ring, column])]
    lower = [int(tube[corner_ring, column])]
    for r in range(corner_ring + 1, count):
        upper.append(int(tube[r, column]))
        lower.append(b.vertex(b.points[int(tube[r, column])], "lip", coord=(float(r), column / around)))
        body.alt[r, column] = lower[-1]
        b.welds.append((upper[-1], lower[-1]))
    body.lower[corner_ring:, column:] = True
    front_patch.alt[row, m] = lower[-1]
    for c in range(m - 1, -1, -1):
        upper.append(int(front[row, c]))
        lower.append(b.vertex(b.points[int(front[row, c])], "lip", coord=(float(count), c / m)))
        front_patch.alt[row, c] = lower[-1]
        b.welds.append((upper[-1], lower[-1]))
    front_patch.lower[row:, :] = True
    b.meta["lip_upper"] = upper
    b.meta["lip_lower"] = lower
    b.meta["mouth_column"] = column
    b.meta["corner_ring"] = corner_ring
    b.meta["below"] = sorted(set([int(tube[r, s]) for r in range(corner_ring + 1, count) for s in range(column + 1, half + 1)] + [int(front[j, c]) for j in range(row + 1, n + 1) for c in range(0, m + 1)]))

    for leg in spec["legs"]:
        r0, r1, c0, c1 = bury(f, b, tube, leg["group"], leg["limit"], leg.get("grow", 1), (1, half - 1))
        leg["rect"] = (r0, r1, c0, c1)
        leg["loop"] = body.hole(r0, r1, c0, c1)
        print("CAGE hole", leg["name"], (r0, r1, c0, c1), len(leg["loop"]))

    eye = spec["eye"]
    surface = numpy.asarray(eye["center"]) + fields.unit(eye["axis"]) * eye["radius"]
    er, ec = nearest_cell(b, tube, surface)
    size = eye.get("cells", 2)
    eye_loop = body.hole(er - size, er + size, ec - size, ec + size)

    ear = spec["ear"]
    rr, rc = nearest_cell(b, tube, ear["root"])
    span = ear.get("cells", (1, 2))
    ear_loop = body.hole(rr - span[0], rr + span[1], rc - span[0], rc + span[1])

    tail = spec["tail"]
    tr, tc = tail["cell"]
    tail_loop_half = [int(rear[tr, c]) for c in range(0, tc)] + [int(rear[r, tc]) for r in range(tr, tr + tail["rows"])] + [int(rear[tr + tail["rows"], c]) for c in range(tc, -1, -1)]
    rear_patch.removed[tr:tr + tail["rows"], 0:tc] = True

    nostril = spec["nostril"]
    nr, nc = nostril["cell"]
    nostril_loop = front_patch.hole(nr, nr + nostril.get("rows", 2), nc, nc + nostril.get("cols", 2))

    body.emit(b)
    rear_patch.emit(b)
    front_patch.emit(b)
    for r in range(count - 1):
        b.cuts.append((int(tube[r, half]), int(tube[r + 1, half])))
    for j in range(n):
        b.cuts.append((int(rear[j, 0]), int(rear[j + 1, 0])))

    for leg in spec["legs"]:
        points, tangents = limb_frames(leg["path"])
        sections = cast_limb(f, points, tangents, leg["around"], (leg["group"],))
        ids = [b.ring(section, leg["name"], level=float(level)) for level, section in enumerate(sections)]
        loop = leg["loop"]
        loop_points = b.at(loop)
        first = sections[0]
        if float(newell(loop_points) @ newell(first)) < 0.0:
            loop = loop[::-1]
            loop_points = loop_points[::-1]
        picks = []
        dense = resample(loop_points, 256, closed=True)
        for point in first:
            direction = point - points[0]
            offsets = dense - points[0][None, :]
            flat = offsets - numpy.outer(offsets @ tangents[0], tangents[0])
            flat /= numpy.maximum(numpy.linalg.norm(flat, axis=1), 1e-9)[:, None]
            picks.append(dense[int(numpy.argmax(flat @ fields.unit(direction - tangents[0] * float(direction @ tangents[0]))))])
        bridge = b.ring(0.5 * (first + numpy.array(picks)), leg["name"], level=-1.0)
        b.stitch(loop, bridge, leg["name"])
        b.band(bridge, ids[0], leg["name"])
        for level in range(len(ids) - 1):
            b.band(ids[level], ids[level + 1], leg["name"])
        b.fan(ids[-1], points[-1] + tangents[-1] * 0.004, leg["name"], leg["name"])
        seam = int(round(leg["around"] * 0.75)) % leg["around"]
        chain = [bridge[seam]] + [ring[seam] for ring in ids]
        for index in range(len(chain) - 1):
            b.cuts.append((chain[index], chain[index + 1]))
        b.meta[leg["name"]] = {"rings": [bridge] + ids, "points": points}
        b.seeds.extend(loop)

    shapes = eye_rings(eye)
    lid = [b.ring(shape, "eye", pinned=True, level=float(level)) for level, shape in enumerate(shapes)]
    b.stitch(eye_loop, lid[0], "head")
    for level in range(1, len(lid)):
        b.band(lid[level - 1], lid[level], "head")
    b.meta["eye"] = lid
    b.seeds.extend(eye_loop)

    sections, tip = ear_rings(ear, ear["around"])
    ear_ids = [b.ring(section, "ear", pinned=True, level=float(level)) for level, section in enumerate(sections)]
    b.stitch(ear_loop, ear_ids[0], "ear")
    for level in range(1, len(ear_ids)):
        b.band(ear_ids[level - 1], ear_ids[level], "ear")
    b.fan(ear_ids[-1], tip, "ear", "ear", pinned=True)
    for level in range(len(ear_ids) - 1):
        b.cuts.append((ear_ids[level][0], ear_ids[level + 1][0]))
    b.meta["ear"] = ear_ids
    b.seeds.extend(ear_loop)

    path = numpy.asarray(tail["path"], dtype=numpy.float64)
    tail_sections = tube_rings(path, tail["radii"], tail["around"], tail.get("flat", 1.0), up=(0.0, 0.0, 1.0))
    tail_ids = []
    for level, section in enumerate(tail_sections):
        ring = []
        for index in range(tail["around"] // 2 + 1):
            point = section[index].copy()
            if index == 0 or index == tail["around"] // 2:
                point[0] = 0.0
            ring.append(b.vertex(point, "tail", pinned=True, coord=(float(level), index / tail["around"])))
        tail_ids.append(ring)
    loop_points = b.at(tail_loop_half)
    first = b.at(tail_ids[0])
    if float(numpy.linalg.norm(loop_points[0] - first[0])) > float(numpy.linalg.norm(loop_points[0] - first[-1])):
        tail_ids = [ring[::-1] for ring in tail_ids]
    open_stitch(b, tail_loop_half, tail_ids[0], "tail")
    b.cuts.append((tail_loop_half[-1], tail_ids[0][-1]))
    for level in range(len(tail_ids) - 1):
        for index in range(len(tail_ids[level]) - 1):
            b.face((tail_ids[level][index], tail_ids[level][index + 1], tail_ids[level + 1][index + 1], tail_ids[level + 1][index]), "tail")
    tip = b.vertex(path[-1] + (path[-1] - path[-2]) * 0.35, "tail", pinned=True)
    for index in range(len(tail_ids[-1]) - 1):
        b.face((tail_ids[-1][index], tail_ids[-1][index + 1], tip), "tail")
    for level in range(len(tail_ids) - 1):
        b.cuts.append((tail_ids[level][-1], tail_ids[level + 1][-1]))
    b.cuts.append((tail_ids[-1][-1], tip))
    b.meta["tail"] = tail_ids
    b.seeds.extend(tail_loop_half)

    loop_points = b.at(nostril_loop)
    middle = loop_points.mean(axis=0)
    inward = -front_axis
    spokes = loop_points - middle[None, :]
    reach = numpy.linalg.norm(spokes, axis=1)
    spokes = spokes * ((1.0 - nostril.get("round", 0.85)) + nostril.get("round", 0.85) * float(reach.mean()) / reach)[:, None]
    rim = b.ring(middle[None, :] + spokes * 0.62 + inward[None, :] * 0.002, "nostril", pinned=True)
    deep = b.ring(middle[None, :] + spokes * 0.4 + inward[None, :] * nostril.get("depth", 0.012) + numpy.array(nostril.get("drift", (0.0, 0.0, 0.0)))[None, :], "nostril", pinned=True)
    b.band(nostril_loop, rim, "nose")
    b.band(rim, deep, "nostril")
    b.fan(deep, middle + inward * (nostril.get("depth", 0.012) * 1.3) + numpy.array(nostril.get("drift", (0.0, 0.0, 0.0))), "nostril", "nostril", pinned=True)
    b.meta["nostril"] = [rim, deep]

    axis = blueprint["marks"]["head_axis"]
    up = blueprint["marks"]["head_up"]
    levels = mouth.get("levels", ((0.3, 0.0025), (1.0, 0.006)))
    previous_upper = upper
    previous_lower = lower
    for depth, gap in levels:
        next_upper = []
        next_lower = []
        for index in range(len(upper)):
            point = b.points[upper[index]]
            target = point * numpy.array([0.35, 1.0, 1.0]) + axis * 0.012
            inner = point + (target - point) * depth
            if index == 0:
                shared = b.vertex(inner + axis * 0.004 * depth, "mouth", pinned=True)
                next_upper.append(shared)
                next_lower.append(shared)
            else:
                next_upper.append(b.vertex(inner + up * gap, "mouth_upper", pinned=True))
                next_lower.append(b.vertex(inner - up * gap, "mouth_lower", pinned=True))
        for index in range(len(upper) - 1):
            b.face((previous_upper[index], previous_upper[index + 1], next_upper[index + 1], next_upper[index]), "mouth")
            b.face((previous_lower[index + 1], previous_lower[index], next_lower[index], next_lower[index + 1]), "mouth")
        previous_upper = next_upper
        previous_lower = next_lower
    for index in range(len(upper) - 1):
        b.face((previous_upper[index], previous_upper[index + 1], previous_lower[index + 1], previous_lower[index]), "mouth")
    return b


def open_stitch(b, first, second, tag):
    na = len(first) - 1
    nb = len(second) - 1
    i = 0
    j = 0
    tolerance = 0.45 * min(1.0 / na, 1.0 / nb)
    while i < na or j < nb:
        ta = (i + 1) / na if i < na else 9.0
        tb = (j + 1) / nb if j < nb else 9.0
        if i < na and j < nb and abs(ta - tb) < tolerance:
            b.face((first[i], first[i + 1], second[j + 1], second[j]), tag)
            i += 1
            j += 1
        elif ta < tb:
            b.face((first[i], first[i + 1], second[j]), tag)
            i += 1
        else:
            b.face((first[i], second[j + 1], second[j]), tag)
            j += 1


def finish(b, sided=("fore", "hind", "ear")):
    points = numpy.array(b.points)
    count = len(points)
    left = numpy.abs(points[:, 0]) > 1e-7
    mapping = numpy.arange(count)
    mapping[left] = count + numpy.arange(int(left.sum()))
    mirrored = points[left] * flip[None, :]
    data = {"points": numpy.vstack([points, mirrored])}
    data["mirror"] = numpy.concatenate([mapping, numpy.flatnonzero(left)])
    data["side"] = numpy.concatenate([numpy.where(left, 1, 0), numpy.full(int(left.sum()), -1)])
    data["part"] = list(b.part) + [b.part[i] for i in numpy.flatnonzero(left)]
    data["pinned"] = numpy.concatenate([numpy.array(b.pinned, dtype=bool), numpy.array(b.pinned, dtype=bool)[left]])
    coords = numpy.array(b.coord, dtype=numpy.float64)
    data["coord"] = numpy.vstack([coords, coords[left]])
    faces = []
    tags = []
    for face, tag in zip(b.faces, b.tags):
        faces.append(face)
        tags.append(tag + "_l" if tag in sided else tag)
        faces.append(tuple(int(mapping[i]) for i in reversed(face)))
        tags.append(tag + "_r" if tag in sided else tag)
    data["faces"] = faces
    data["tags"] = tags
    data["welds"] = [(a, c) for a, c in b.welds] + [(int(mapping[a]), int(mapping[c])) for a, c in b.welds if mapping[a] != a]
    data["cuts"] = [(a, c) for a, c in b.cuts] + [(int(mapping[a]), int(mapping[c])) for a, c in b.cuts if mapping[a] != a or mapping[c] != c]
    data["seeds"] = sorted(set(int(i) for i in b.seeds) | set(int(mapping[i]) for i in b.seeds))
    data["mapping"] = mapping
    return data


def audit(f, data, groups):
    points = data["points"]
    centers = []
    normals = []
    chosen = []
    for index, face in enumerate(data["faces"]):
        ids = list(face)
        if not data["pinned"][ids].any():
            corners = points[ids]
            centers.append(corners.mean(axis=0))
            normals.append(numpy.cross(corners[1] - corners[0], corners[2] - corners[0]))
            chosen.append(index)
    gradient = f.normals(numpy.array(centers), groups)
    against = numpy.sum(numpy.array(normals) * gradient, axis=1) < 0.0
    if against.mean() > 0.5:
        data["faces"] = [tuple(reversed(face)) for face in data["faces"]]
        against = ~against
    bad = [chosen[i] for i in numpy.flatnonzero(against)]
    print("CAGE audit", len(bad), "of", len(chosen), "faces against the surface", sorted(set(data["tags"][i] for i in bad)))
    for index in bad[:12]:
        print("   ", data["tags"][index], numpy.round(points[list(data["faces"][index])].mean(axis=0), 3))
    return bad


def neighbours(count, faces):
    pairs = set()
    for face in faces:
        for index in range(len(face)):
            a = face[index]
            c = face[(index + 1) % len(face)]
            pairs.add((min(a, c), max(a, c)))
    pairs = numpy.array(sorted(pairs), dtype=numpy.int64)
    return pairs


def relax(f, data, groups, rounds=24, reach=5):
    points = data["points"].copy()
    count = len(points)
    pairs = neighbours(count, data["faces"])
    free = ~data["pinned"]
    depth = numpy.full(count, 99)
    depth[data["seeds"]] = 0
    for step in range(reach):
        near = numpy.minimum(depth[pairs[:, 0]], depth[pairs[:, 1]]) + 1
        numpy.minimum.at(depth, pairs[:, 0], near)
        numpy.minimum.at(depth, pairs[:, 1], near)
    weight = numpy.clip(1.0 - depth / float(reach), 0.0, 1.0) * 0.6 + 0.12
    weight[~free] = 0.0
    mirror = data["mirror"]
    degree = numpy.zeros(count)
    numpy.add.at(degree, pairs[:, 0], 1.0)
    numpy.add.at(degree, pairs[:, 1], 1.0)
    points[free] = f.project(points[free], groups, iterations=6)
    for iteration in range(rounds):
        total = numpy.zeros_like(points)
        numpy.add.at(total, pairs[:, 0], points[pairs[:, 1]])
        numpy.add.at(total, pairs[:, 1], points[pairs[:, 0]])
        average = total / numpy.maximum(degree, 1.0)[:, None]
        normal = f.normals(points, groups)
        move = average - points
        move -= normal * numpy.sum(move * normal, axis=1)[:, None]
        points += move * weight[:, None]
        points[free] = f.project(points[free], groups, iterations=2)
        for a, c in data["welds"]:
            middle = 0.5 * (points[a] + points[c])
            points[a] = middle
            points[c] = middle
        points = 0.5 * (points + points[mirror] * flip[None, :])
    data["points"] = points
    return data
