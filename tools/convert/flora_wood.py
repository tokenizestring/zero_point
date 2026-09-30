import bpy
import bmesh
import math
import random
import numpy
from mathutils import Matrix, Vector

import flora_kit as kit


class limb_c:
    def __init__(self, points, level, parent=None, anchor=0.0):
        self.points = points
        self.level = level
        self.parent = parent
        self.anchor = anchor
        self.children = []
        self.radii = None
        self.weight = 0.0
        self.own = 1.0
        self.zone = 0
        self.switch = None
        self.leafy = False
        self.broken = False
        self.shape = None
        self.crest = None
        self.bare = 0.0
        self.skip = False
        if parent is not None:
            parent.children.append(self)

    def marks(self):
        lengths = [0.0]
        for index in range(len(self.points) - 1):
            lengths.append(lengths[-1] + (self.points[index + 1] - self.points[index]).length)
        total = max(lengths[-1], 1e-9)
        return [length / total for length in lengths]

    def length(self):
        return kit.path_length(self.points)

    def at(self, s):
        marks = self.marks()
        s = kit.clamp(s, 0.0, 1.0)
        index = 0
        while index < len(marks) - 2 and marks[index + 1] < s:
            index += 1
        span = max(marks[index + 1] - marks[index], 1e-9)
        local = kit.clamp((s - marks[index]) / span, 0.0, 1.0)
        point = self.points[index].lerp(self.points[index + 1], local)
        heading = (self.points[index + 1] - self.points[index]).normalized()
        radius = kit.lerp(self.radii[index], self.radii[index + 1], local) if self.radii else 0.0
        return point, heading, radius


def walk(root):
    order = [root]
    index = 0
    while index < len(order):
        order.extend(order[index].children)
        index += 1
    return order


def assign_radii(root, trunk_radius, tip_radius, exponent=2.0, thin=0.45, thin_range=0.08):
    order = walk(root)
    for limb in reversed(order):
        limb.weight = limb.own + sum(child.weight for child in limb.children)
    total = max(root.weight, 1e-6)
    for limb in order:
        marks = limb.marks()
        last = max([child.anchor for child in limb.children], default=0.0)
        own_share = limb.own / total
        own_radius = trunk_radius * own_share ** (1.0 / exponent) * kit.lerp(thin, 1.0, kit.smooth(0.0, thin_range, own_share))
        radii = []
        for mark in marks:
            downstream = limb.own + sum(child.weight for child in limb.children if child.anchor > mark - 1e-4)
            share = downstream / total
            radius = trunk_radius * share ** (1.0 / exponent) * kit.lerp(thin, 1.0, kit.smooth(0.0, thin_range, share))
            if mark > last and limb.broken is False:
                radius = kit.lerp(own_radius, tip_radius, ((mark - last) / max(1.0 - last, 1e-6)) ** 0.85)
            radii.append(max(radius, tip_radius))
        if limb.parent is not None:
            limit = limb.parent.at(limb.anchor)[2] * 0.9
            if radii[0] > limit:
                factor = limit / radii[0]
                radii = [max(radius * factor, tip_radius) for radius in radii]
        for index in range(1, len(radii)):
            radii[index] = min(radii[index], radii[index - 1])
        limb.radii = radii


def simplify(points, radii, tolerance):
    if tolerance <= 0.0 or len(points) <= 2:
        return list(points), list(radii)
    keep = [False] * len(points)
    keep[0] = True
    keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        if last - first < 2:
            continue
        axis = points[last] - points[first]
        length = axis.length
        worst = 0.0
        worst_index = -1
        for index in range(first + 1, last):
            offset = points[index] - points[first]
            distance = (offset - axis * (offset.dot(axis) / (length * length))).length if length > 1e-9 else offset.length
            if distance > worst:
                worst = distance
                worst_index = index
        if worst > tolerance:
            keep[worst_index] = True
            stack.append((first, worst_index))
            stack.append((worst_index, last))
    return [points[index] for index in range(len(points)) if keep[index]], [radii[index] for index in range(len(points)) if keep[index]]


def smooth_path(points, passes=1):
    result = list(points)
    for index in range(passes):
        refined = [result[0]]
        for step in range(len(result) - 1):
            refined.append(result[step].lerp(result[step + 1], 0.25))
            refined.append(result[step].lerp(result[step + 1], 0.75))
        refined.append(result[-1])
        result = refined
    return result


def bark_rows(points, radii, zones, metres, zone, switch, offset):
    rows = []
    value = zones[zone][0] + offset * (zones[zone][1] - zones[zone][0])
    rows.append((points[0], radii[0], value, value))
    travelled = 0.0
    limits = list(switch) if isinstance(switch, (list, tuple)) else ([switch] if switch is not None else [])
    passed = 0
    for index in range(len(points) - 1):
        first = points[index]
        second = points[index + 1]
        length = (second - first).length
        if length < 1e-7:
            continue
        cursor = 0.0
        guard = 0
        while guard < 64:
            guard += 1
            end = zones[zone][1]
            room = (end - value) * metres
            if room >= length - cursor - 1e-7:
                value += (length - cursor) / metres
                rows.append((second, radii[index + 1], value, value))
                break
            cursor += max(room, 0.0)
            if zone + 1 < len(zones) and passed < len(limits) and travelled + cursor >= limits[passed]:
                zone += 1
                passed += 1
                value = end
                continue
            local = cursor / length
            rows.append((first.lerp(second, local), kit.lerp(radii[index], radii[index + 1], local), end, zones[zone][0]))
            value = zones[zone][0]
        travelled += length
    return rows


def frame_of(forward, roll=0.0, hint=None):
    forward = forward.normalized()
    hint = Vector((0.0, 0.0, 1.0)) if hint is None else hint
    right = forward.cross(hint)
    if right.length < 1e-4:
        right = forward.cross(Vector((1.0, 0.0, 0.0)))
    right.normalize()
    up = right.cross(forward).normalized()
    if roll:
        rotation = Matrix.Rotation(roll, 3, forward)
        right = rotation @ right
        up = rotation @ up
    return forward, right, up


def random_unit(rng):
    z = rng.uniform(-1.0, 1.0)
    angle = rng.uniform(0.0, math.tau)
    radius = math.sqrt(max(0.0, 1.0 - z * z))
    return Vector((math.cos(angle) * radius, math.sin(angle) * radius, z))


def deflect(rng, heading, angle, toward=None, weight=0.0):
    lateral = random_unit(rng)
    lateral = lateral - heading * lateral.dot(heading)
    if toward is not None and weight > 0.0:
        target = toward - heading * toward.dot(heading)
        if target.length > 1e-4:
            lateral = lateral.normalized() * (1.0 - weight) + target.normalized() * weight
    if lateral.length < 1e-5:
        lateral = kit.any_perpendicular(heading)
    lateral.normalize()
    return (heading * math.cos(angle) + lateral * math.sin(angle)).normalized()


def grow(rng, start, heading, length, step, wander=0.0, pull=None, kink=0.0, kink_every=(1.0, 1.6), inside=None, kinks=None, plane=1.0):
    points = [start.copy()]
    heading = heading.normalized()
    travelled = 0.0
    next_kink = rng.uniform(kink_every[0], kink_every[1]) * 0.7 if kink else 1e9
    lateral = None
    entered = False
    while travelled < length - 1e-6:
        segment = min(step, length - travelled)
        if wander:
            heading = (heading + random_unit(rng) * wander * math.sqrt(segment)).normalized()
        if pull is not None:
            target, strength = pull(points[-1], travelled / max(length, 1e-6))
            heading = (heading + target * strength * segment).normalized()
        if travelled >= next_kink:
            lateral = random_unit(rng) if lateral is None else Matrix.Rotation(rng.uniform(-plane, plane), 3, heading) @ (-lateral)
            lateral = lateral - heading * lateral.dot(heading)
            if lateral.length < 1e-4:
                lateral = kit.any_perpendicular(heading)
            lateral.normalize()
            before = heading.copy()
            angle = kink * rng.uniform(0.6, 1.25)
            heading = (heading * math.cos(angle) + lateral * math.sin(angle)).normalized()
            if kinks is not None:
                kinks.append((len(points) - 1, before, lateral.copy()))
            next_kink = travelled + rng.uniform(kink_every[0], kink_every[1])
        point = points[-1] + heading * segment
        if inside is not None:
            within = inside(point)
            if entered and within is False and travelled > step * 2.0:
                break
            entered = entered or within
        points.append(point)
        travelled += segment
    return points


class model_c:
    def __init__(self, zones=((0.0, 1.0),), metres=2.0, girth=1.6):
        self.wood = bmesh.new()
        self.wood_uv = self.wood.loops.layers.uv.new("UVMap")
        self.leaf = bmesh.new()
        self.leaf_uv = self.leaf.loops.layers.uv.new("UVMap")
        self.normals = {}
        self.zones = zones
        self.metres = metres
        self.girth = girth

    def tube(self, points, radii, sides, crest=None, zone=0, switch=None, offset=0.0, repeats=None, shape=None, jag=None, rng=None):
        rows = bark_rows(points, radii, self.zones, self.metres, zone, switch, offset)
        path = [row[0] for row in rows]
        frames = kit.frames(path, Vector((0.0, 0.0, 1.0)) if crest is None else crest)
        if repeats is None:
            repeats = max(1, int(round(math.tau * radii[0] / self.girth)))
        rings = []
        for index, (point, radius, below, above) in enumerate(rows):
            tangent, side, normal = frames[index]
            ring = []
            for step_index in range(sides):
                angle = math.tau * step_index / sides
                scale = shape(point, angle, index / max(len(rows) - 1, 1)) if shape else 1.0
                lift = tangent * jag[step_index] if jag is not None and index == len(rows) - 1 else Vector((0.0, 0.0, 0.0))
                ring.append(self.wood.verts.new(point + (side * math.cos(angle) + normal * math.sin(angle)) * radius * scale + lift))
            rings.append(ring)
        for index in range(len(rows) - 1):
            low = rows[index][3]
            high = rows[index + 1][2]
            for step_index in range(sides):
                following = (step_index + 1) % sides
                face = self.wood.faces.new((rings[index][step_index], rings[index][following], rings[index + 1][following], rings[index + 1][step_index]))
                left = step_index / sides * repeats
                right = (step_index + 1) / sides * repeats
                for loop, uv in zip(face.loops, ((left, low), (right, low), (right, high), (left, high))):
                    loop[self.wood_uv].uv = uv
        if jag is not None:
            tangent = frames[-1][0]
            center = self.wood.verts.new(path[-1] - tangent * radii[-1] * 0.6)
            top = rows[-1][2]
            for step_index in range(sides):
                following = (step_index + 1) % sides
                face = self.wood.faces.new((rings[-1][step_index], rings[-1][following], center))
                for loop, uv in zip(face.loops, ((step_index / sides * repeats, top), ((step_index + 1) / sides * repeats, top), ((step_index + 0.5) / sides * repeats, top + radii[-1] / self.metres))):
                    loop[self.wood_uv].uv = uv

    def card(self, cell, origin, forward, right, up, scale=1.0, bend=0.0, fold=0.0, rows=2, columns=1, mirror=False, shade=None, twist=0.0):
        u0, v0, u1, v1 = cell["rect"]
        width, height = cell["size"]
        anchor_x, anchor_y = cell["anchor"]
        if mirror:
            anchor_x = width - anchor_x
        middle = (0.5 * width - anchor_x) * scale
        grid = []
        for row in range(rows + 1):
            t = row / rows
            y = (t * height - anchor_y) * scale
            sag = bend * height * scale * max(t, 0.0) ** 1.7
            across = right
            lifted = up
            if twist:
                rotation = Matrix.Rotation(twist * t, 3, forward)
                across = rotation @ right
                lifted = rotation @ up
            line = []
            for column in range(columns + 1):
                s = column / columns
                x = (s * width - anchor_x) * scale
                point = origin + forward * y + across * x - lifted * (sag + fold * abs(x - middle))
                vert = self.leaf.verts.new(point)
                self.normals[vert] = shade(point, lifted) if shade else lifted
                line.append((vert, (u0 + (u1 - u0) * ((1.0 - s) if mirror else s), v0 + (v1 - v0) * t)))
            grid.append(line)
        for row in range(rows):
            for column in range(columns):
                corners = (grid[row][column], grid[row][column + 1], grid[row + 1][column + 1], grid[row + 1][column])
                face = self.leaf.faces.new([corner[0] for corner in corners])
                for loop, corner in zip(face.loops, corners):
                    loop[self.leaf_uv].uv = corner[1]

    def stem(self, cell, points, radii, sides, period=0.35, inset=0.06):
        u0, v0, u1, v1 = cell["rect"]
        du = (u1 - u0) * inset
        dv = (v1 - v0) * inset
        u0, v0, u1, v1 = u0 + du, v0 + dv, u1 - du, v1 - dv
        frames = kit.frames(points, Vector((0.0, 0.0, 1.0)))
        rings = []
        travelled = 0.0
        marks = []
        for index, point in enumerate(points):
            if index:
                travelled += (point - points[index - 1]).length
            wave = (travelled / period) % 2.0
            marks.append(v0 + (v1 - v0) * (wave if wave <= 1.0 else 2.0 - wave))
            tangent, side, normal = frames[index]
            ring = []
            for step_index in range(sides):
                angle = math.tau * step_index / sides
                outward = side * math.cos(angle) + normal * math.sin(angle)
                vert = self.leaf.verts.new(point + outward * radii[index])
                self.normals[vert] = outward
                ring.append(vert)
            rings.append(ring)
        for index in range(len(points) - 1):
            for step_index in range(sides):
                following = (step_index + 1) % sides
                face = self.leaf.faces.new((rings[index][step_index], rings[index][following], rings[index + 1][following], rings[index + 1][step_index]))
                left = u0 + (u1 - u0) * (1.0 - abs(1.0 - 2.0 * step_index / sides))
                right = u0 + (u1 - u0) * (1.0 - abs(1.0 - 2.0 * (step_index + 1) / sides))
                for loop, uv in zip(face.loops, ((left, marks[index]), (right, marks[index]), (right, marks[index + 1]), (left, marks[index + 1]))):
                    loop[self.leaf_uv].uv = uv

    def hull(self, cell, center, radii, segments=8, rings=4, floor=0.0, shade=None, inset=0.08, tiles=2.0):
        u0, v0, u1, v1 = cell["rect"]
        du = (u1 - u0) * inset
        dv = (v1 - v0) * inset
        u0, v0, u1, v1 = u0 + du, v0 + dv, u1 - du, v1 - dv
        lines = []
        for ring in range(rings + 1):
            polar = math.pi * 0.62 * ring / rings
            line = []
            for segment in range(segments):
                azimuth = math.tau * segment / segments
                point = Vector((center.x + math.sin(polar) * math.cos(azimuth) * radii[0], center.y + math.sin(polar) * math.sin(azimuth) * radii[1], max(floor, center.z + math.cos(polar) * radii[2])))
                vert = self.leaf.verts.new(point)
                outward = Vector(((point.x - center.x) / (radii[0] ** 2), (point.y - center.y) / (radii[1] ** 2), (point.z - center.z) / (radii[2] ** 2)))
                self.normals[vert] = shade(point, outward.normalized() if outward.length > 1e-6 else Vector((0.0, 0.0, 1.0))) if shade else (outward.normalized() if outward.length > 1e-6 else Vector((0.0, 0.0, 1.0)))
                line.append(vert)
            lines.append(line)

        def mirrored(value):
            wave = value % 2.0
            return wave if wave <= 1.0 else 2.0 - wave

        for ring in range(rings):
            for segment in range(segments):
                following = (segment + 1) % segments
                face = self.leaf.faces.new((lines[ring][segment], lines[ring + 1][segment], lines[ring + 1][following], lines[ring][following]))
                left = u0 + (u1 - u0) * mirrored(segment / segments * tiles * 2.0)
                right = u0 + (u1 - u0) * mirrored((segment + 1) / segments * tiles * 2.0)
                top = v0 + (v1 - v0) * mirrored(ring / rings * tiles)
                bottom = v0 + (v1 - v0) * mirrored((ring + 1) / rings * tiles)
                for loop, uv in zip(face.loops, ((left, top), (left, bottom), (right, bottom), (right, top))):
                    loop[self.leaf_uv].uv = uv

    def finish(self, name, wood_material, leaf_material):
        objects = []
        if len(self.wood.faces):
            mesh = bpy.data.meshes.new(name + "_bark")
            self.wood.to_mesh(mesh)
            mesh.materials.append(wood_material)
            for polygon in mesh.polygons:
                polygon.use_smooth = True
            obj = bpy.data.objects.new("trunk", mesh)
            bpy.context.scene.collection.objects.link(obj)
            objects.append(obj)
        if len(self.leaf.faces):
            self.leaf.verts.index_update()
            normals = [self.normals.get(vert, Vector((0.0, 0.0, 1.0))) for vert in self.leaf.verts]
            mesh = bpy.data.meshes.new(name + "_foliage")
            self.leaf.to_mesh(mesh)
            mesh.materials.append(leaf_material)
            for polygon in mesh.polygons:
                polygon.use_smooth = True
            mesh.normals_split_custom_set_from_vertices(normals)
            obj = bpy.data.objects.new("foliage", mesh)
            bpy.context.scene.collection.objects.link(obj)
            objects.append(obj)
        self.wood.free()
        self.leaf.free()
        return objects


def mesh_limbs(model, root, lod, table, rng, scale=1.0):
    for limb in walk(root):
        base = limb.radii[0]
        sides = 0
        slack = 0.0
        for threshold, counts, slacks in table:
            if base >= threshold * scale:
                sides = counts[lod]
                slack = slacks[lod]
                break
        if sides < 3 or len(limb.points) < 2 or (limb.skip and lod == 0):
            continue
        points, radii = simplify(limb.points, limb.radii, slack)
        if lod > 0 and len(points) > 2:
            kept = [0]
            for index in range(1, len(points) - 1):
                if (points[index] - points[kept[-1]]).length > radii[index] * 1.6 and (points[-1] - points[index]).length > radii[index] * 1.6:
                    kept.append(index)
            kept.append(len(points) - 1)
            points = [points[index] for index in kept]
            radii = [radii[index] for index in kept]
        tangent = (points[1] - points[0]).normalized()
        crest = limb.crest if limb.crest is not None else (Vector((0.0, 1.0, 0.0)) if abs(tangent.z) > 0.9 else Vector((0.0, 0.0, 1.0)))
        jag = None
        if limb.broken:
            jag = [rng.uniform(-0.5, 1.4) * radii[-1] for step_index in range(sides)]
        model.tube(points, radii, sides, crest, limb.zone, limb.switch, rng.random() if limb.parent is not None else 0.0, None, limb.shape, jag, rng)


def ellipsoid(center, radius, up, down):
    def inside(point):
        rise = point.z - center.z
        vertical = up if rise > 0.0 else down
        return ((point.x - center.x) ** 2 + (point.y - center.y) ** 2) / (radius * radius) + (rise / vertical) ** 2 <= 1.0
    return inside


def reach(inside, start, direction, limit=40.0, step=0.2):
    distance = 0.0
    farthest = 0.0
    entered = False
    while distance < limit:
        distance += step
        if inside(start + direction * distance):
            farthest = distance
            entered = True
        elif entered:
            break
    return farthest


def crown_shade(center, radius, up, down, weights=(0.62, 0.22, 0.2)):
    def shade(point, lifted):
        rise = point.z - center.z
        vertical = up if rise > 0.0 else down
        outward = Vector(((point.x - center.x) / (radius * radius), (point.y - center.y) / (radius * radius), rise / (vertical * vertical)))
        if outward.length < 1e-6:
            outward = Vector((0.0, 0.0, 1.0))
        outward.normalize()
        facing = lifted if lifted.dot(outward) >= 0.0 else -lifted
        return (outward * weights[0] + facing * weights[1] + Vector((0.0, 0.0, weights[2]))).normalized()
    return shade


def crown_points(rng, count, center, radius, up, down, inner=0.45, power=0.6, floor=None, squash=None):
    result = []
    guard = 0
    while len(result) < count and guard < count * 50:
        guard += 1
        direction = random_unit(rng)
        rho = inner + (1.0 - inner) * rng.random() ** power
        point = Vector((center.x + direction.x * radius[0] * rho, center.y + direction.y * radius[1] * rho, center.z + direction.z * (up if direction.z > 0.0 else down) * rho))
        if floor is not None and point.z < floor:
            continue
        if squash is not None and squash(point) is False:
            continue
        result.append(point)
    return result


def clump_points(rng, count, center, radius, up, down, clumps, size, shell=(0.55, 0.86), floor=None, lumps=None, keep=None):
    centres = []
    for index in range(clumps):
        best = None
        best_gap = -1.0
        for attempt in range(24):
            direction = random_unit(rng)
            rho = rng.uniform(shell[0], shell[1])
            candidate = Vector((center.x + direction.x * radius[0] * rho, center.y + direction.y * radius[1] * rho, center.z + direction.z * (up if direction.z > 0.0 else down) * rho))
            if floor is not None and candidate.z < floor:
                continue
            if keep is not None and keep(candidate) is False:
                continue
            gap = min([(candidate - other).length for other in centres], default=1e9)
            if gap > best_gap:
                best_gap = gap
                best = candidate
        if best is not None:
            centres.append(best)
    result = []
    guard = 0
    while len(result) < count and guard < count * 60:
        guard += 1
        anchor = centres[rng.randrange(len(centres))]
        offset = random_unit(rng) * size * rng.random() ** 0.45
        point = anchor + Vector((offset.x, offset.y, offset.z * 0.8))
        rise = point.z - center.z
        vertical = up if rise > 0.0 else down
        if ((point.x - center.x) / radius[0]) ** 2 + ((point.y - center.y) / radius[1]) ** 2 + (rise / vertical) ** 2 > 1.0:
            continue
        if floor is not None and point.z < floor:
            continue
        if keep is not None and keep(point) is False:
            continue
        result.append(point)
    if lumps is not None:
        lumps.extend(centres)
    return result


def colonize(rng, root, targets, step, influence, kill, inertia=0.35, lift=0.1, rounds=90, fan=3, floor=-1e9, jitter=0.15, skip=None, zone=0):
    limbs = [limb for limb in walk(root) if limb.broken is False and (skip is None or limb not in skip)]
    positions = []
    parents = []
    headings = []
    sources = []
    for limb in limbs:
        marks = limb.marks()
        for index, point in enumerate(limb.points):
            if point.z < floor:
                continue
            ahead = limb.points[min(index + 1, len(limb.points) - 1)] - limb.points[max(index - 1, 0)]
            positions.append((point.x, point.y, point.z))
            parents.append(-1)
            headings.append(ahead.normalized() if ahead.length > 1e-9 else Vector((0.0, 0.0, 1.0)))
            sources.append((limb, marks[index]))
    seeds = len(positions)
    offspring = [[] for index in range(seeds)]
    cloud = numpy.array([(point.x, point.y, point.z) for point in targets], dtype=numpy.float32)
    for round_index in range(rounds):
        if len(cloud) == 0:
            break
        nodes = numpy.array(positions, dtype=numpy.float32)
        delta = cloud[:, None, :] - nodes[None, :, :]
        distance = numpy.sqrt((delta * delta).sum(axis=2))
        nearest = distance.argmin(axis=1)
        reach_distance = distance[numpy.arange(len(cloud)), nearest]
        active = reach_distance < influence
        if not active.any():
            break
        pull = numpy.zeros((len(positions), 3), dtype=numpy.float32)
        count = numpy.zeros(len(positions), dtype=numpy.int32)
        unit = delta[numpy.arange(len(cloud)), nearest] / numpy.maximum(reach_distance, 1e-6)[:, None]
        numpy.add.at(pull, nearest[active], unit[active])
        numpy.add.at(count, nearest[active], 1)
        grown = []
        for node in numpy.nonzero(count)[0]:
            if len(offspring[node]) >= fan:
                continue
            aim = Vector((float(pull[node][0]), float(pull[node][1]), float(pull[node][2])))
            if aim.length < 1e-6:
                continue
            direction = (aim.normalized() + headings[node] * inertia + (lift if isinstance(lift, Vector) else Vector((0.0, 0.0, lift))) + random_unit(rng) * jitter).normalized()
            if any(direction.dot(headings[child]) > 0.93 for child in offspring[node]):
                continue
            base = Vector(positions[node])
            fresh = base + direction * step
            positions.append((fresh.x, fresh.y, fresh.z))
            parents.append(int(node))
            headings.append(direction)
            sources.append(None)
            offspring.append([])
            offspring[node].append(len(positions) - 1)
            grown.append(len(positions) - 1)
        if not grown:
            break
        fresh_nodes = numpy.array([positions[index] for index in grown], dtype=numpy.float32)
        gap = cloud[:, None, :] - fresh_nodes[None, :, :]
        cloud = cloud[numpy.sqrt((gap * gap).sum(axis=2)).min(axis=1) > kill]
    size = [1] * len(positions)
    for node in range(len(positions) - 1, seeds - 1, -1):
        size[parents[node]] += size[node]
    created = []

    def trace(start, parent_limb, anchor, level):
        chain = [start]
        pending = []
        current = start
        while offspring[current]:
            ranked = sorted(offspring[current], key=lambda child: -size[child])
            for other in ranked[1:]:
                pending.append((other, len(chain)))
            current = ranked[0]
            chain.append(current)
        points = [Vector(positions[parents[start]])] + [Vector(positions[node]) for node in chain]
        limb = limb_c(points, min(level, 3), parent_limb, anchor)
        limb.zone = zone
        created.append(limb)
        marks = limb.marks()
        for other, index in pending:
            trace(other, limb, marks[index], level + 1)

    for node in range(seeds):
        for child in offspring[node]:
            trace(child, sources[node][0], sources[node][1], sources[node][0].level + 1)
    return created


def tail(points, start):
    if len(points) < 2:
        return [points[0], points[0] + Vector((0.0, 0.0, 0.3))]
    lengths = [0.0]
    for index in range(len(points) - 1):
        lengths.append(lengths[-1] + (points[index + 1] - points[index]).length)
    total = max(lengths[-1], 1e-9)
    target = total * kit.clamp(start, 0.0, 0.999)
    result = []
    for index in range(len(points) - 1):
        if lengths[index + 1] < target:
            continue
        if not result:
            span = max(lengths[index + 1] - lengths[index], 1e-9)
            result.append(points[index].lerp(points[index + 1], kit.clamp((target - lengths[index]) / span, 0.0, 1.0)))
        result.append(points[index + 1])
    return result if len(result) >= 2 else [points[-2], points[-1]]


def bounds(objects):
    radius = 0.0
    low = 1e9
    high = -1e9
    for obj in objects:
        for vert in obj.data.vertices:
            radius = max(radius, math.hypot(vert.co.x, vert.co.y))
            low = min(low, vert.co.z)
            high = max(high, vert.co.z)
    return radius, low, high
