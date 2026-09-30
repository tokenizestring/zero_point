import bpy
import bmesh
import math
import os
import numpy
from mathutils import Vector, Matrix

roots = {"source": "", "raw": ""}
looks = {}


def turntable_accelerate(scene):
    import turntable
    return turntable.accelerate(scene)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    looks.clear()


def v(x, y, z):
    return Vector((x, y, z))


def place(position, forward=None, up=None):
    matrix = Matrix.Identity(4)
    if forward is not None:
        x_axis = forward.normalized()
        z_axis = up if up is not None else v(0.0, 0.0, 1.0)
        z_axis = (z_axis - x_axis * z_axis.dot(x_axis)).normalized()
        y_axis = z_axis.cross(x_axis)
        matrix = Matrix((tuple(x_axis) + (0.0,), tuple(y_axis) + (0.0,), tuple(z_axis) + (0.0,), (0.0, 0.0, 0.0, 1.0))).transposed()
    matrix.translation = position
    return matrix


def turn(axis, degrees, position=None):
    matrix = Matrix.Rotation(math.radians(degrees), 4, axis)
    if position is not None:
        matrix.translation = position
    return matrix


def finish(bm, weld=True):
    if weld:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def revolve(loop, segments=32, start=0.0, closed=True):
    bm = bmesh.new()
    rings = []
    for r, z in loop:
        ring = []
        for s in range(segments):
            angle = start + math.pi * 2.0 * s / segments
            ring.append(bm.verts.new(v(z, r * math.cos(angle), r * math.sin(angle))))
        rings.append(ring)
    count = len(rings) if closed else len(rings) - 1
    for i in range(count):
        a = rings[i]
        b = rings[(i + 1) % len(rings)]
        for s in range(segments):
            n = (s + 1) % segments
            bm.faces.new((a[s], a[n], b[n], b[s]))
    return finish(bm)


def frames_along(path, up, closed):
    count = len(path)
    tangents = []
    for i in range(count):
        if closed:
            ahead = path[(i + 1) % count]
            behind = path[(i - 1) % count]
        else:
            ahead = path[min(i + 1, count - 1)]
            behind = path[max(i - 1, 0)]
        tangents.append((ahead - behind).normalized())
    normal = up - tangents[0] * up.dot(tangents[0])
    if normal.length < 1e-6:
        normal = tangents[0].orthogonal()
    normal.normalize()
    frames = []
    for i in range(count):
        if i > 0:
            normal = tangents[i - 1].rotation_difference(tangents[i]) @ normal
            normal = (normal - tangents[i] * normal.dot(tangents[i])).normalized()
        frames.append((tangents[i], normal.cross(tangents[i]).normalized(), normal))
    return frames


def planar_frames(path, axis, closed):
    count = len(path)
    frames = []
    for i in range(count):
        if closed:
            ahead = path[(i + 1) % count]
            behind = path[(i - 1) % count]
        else:
            ahead = path[min(i + 1, count - 1)]
            behind = path[max(i - 1, 0)]
        tangent = (ahead - behind).normalized()
        side = axis.cross(tangent).normalized()
        frames.append((tangent, side, tangent.cross(side).normalized()))
    return frames


def sweep(path, profile, closed=False, up=None, planar=None, scales=None, caps=True):
    bm = bmesh.new()
    frames = planar_frames(path, planar, closed) if planar is not None else frames_along(path, up if up is not None else v(0.0, 0.0, 1.0), closed)
    rings = []
    for i, point in enumerate(path):
        tangent, side, normal = frames[i]
        scale = scales[i] if scales is not None else 1.0
        sx, sy = scale if isinstance(scale, tuple) else (scale, scale)
        rings.append([bm.verts.new(point + side * p[0] * sx + normal * p[1] * sy) for p in profile])
    count = len(path) if closed else len(path) - 1
    n = len(profile)
    for i in range(count):
        a = rings[i]
        b = rings[(i + 1) % len(path)]
        for j in range(n):
            k = (j + 1) % n
            bm.faces.new((a[j], a[k], b[k], b[j]))
    if caps and not closed:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    return finish(bm)


def circle(radius, segments=12, start=0.0):
    return [(radius * math.cos(start + math.pi * 2.0 * s / segments), radius * math.sin(start + math.pi * 2.0 * s / segments)) for s in range(segments)]


def ellipse(a, b, segments=12):
    return [(a * math.cos(math.pi * 2.0 * s / segments), b * math.sin(math.pi * 2.0 * s / segments)) for s in range(segments)]


def rectangle(width, height):
    return [(-width * 0.5, -height * 0.5), (width * 0.5, -height * 0.5), (width * 0.5, height * 0.5), (-width * 0.5, height * 0.5)]


def fillet(points, radius, segments=4):
    result = []
    count = len(points)
    for i in range(count):
        p = Vector(points[i])
        before = Vector(points[i - 1])
        after = Vector(points[(i + 1) % count])
        r = radius[i] if isinstance(radius, (list, tuple)) else radius
        d1 = before - p
        d2 = after - p
        if r <= 0.0 or d1.length < 1e-9 or d2.length < 1e-9:
            result.append((p.x, p.y))
            continue
        span1 = d1.length
        span2 = d2.length
        d1.normalize()
        d2.normalize()
        cosine = max(-0.9999, min(0.9999, d1.dot(d2)))
        half = math.acos(cosine) * 0.5
        reach = min(r / math.tan(half), span1 * 0.49, span2 * 0.49)
        r = reach * math.tan(half)
        start = p + d1 * reach
        end = p + d2 * reach
        center = p + (d1 + d2).normalized() * (r / math.sin(half))
        a0 = math.atan2(start.y - center.y, start.x - center.x)
        a1 = math.atan2(end.y - center.y, end.x - center.x)
        delta = a1 - a0
        while delta > math.pi:
            delta -= math.pi * 2.0
        while delta < -math.pi:
            delta += math.pi * 2.0
        for s in range(segments + 1):
            angle = a0 + delta * s / segments
            result.append((center.x + math.cos(angle) * r, center.y + math.sin(angle) * r))
    return result


def extrude(outline, thickness, axis="y"):
    bm = bmesh.new()

    def point(a, b, c):
        if axis == "y":
            return v(a, c, b)
        if axis == "x":
            return v(c, a, b)
        return v(a, b, c)

    low = [bm.verts.new(point(a, b, -thickness * 0.5)) for a, b in outline]
    high = [bm.verts.new(point(a, b, thickness * 0.5)) for a, b in outline]
    bm.faces.new(low)
    bm.faces.new(list(reversed(high)))
    count = len(outline)
    for i in range(count):
        n = (i + 1) % count
        bm.faces.new((low[i], low[n], high[n], high[i]))
    return finish(bm, False)


def box(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=v(sx, sy, sz), verts=bm.verts)
    return finish(bm, False)


def hexagon(across, height, axis="z"):
    radius = across * 0.5 / math.cos(math.pi / 6.0)
    outline = [(radius * math.cos(math.pi / 3.0 * s), radius * math.sin(math.pi / 3.0 * s)) for s in range(6)]
    return extrude(outline, height, axis)


def sphere(radius, u=16, w=10):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=w, radius=radius)
    return finish(bm, False)


def smooth_noise(count, seed, passes=3):
    rng = numpy.random.default_rng(seed)
    field = rng.normal(0.0, 1.0, count)
    for index in range(passes):
        field = (numpy.roll(field, 1) + field * 2.0 + numpy.roll(field, -1)) * 0.25
    return field / max(numpy.abs(field).max(), 1e-6)


def loft(stations, segments=24, exponent=2.0, up=None, noise=0.0, seed=0, caps=True):
    bm = bmesh.new()
    path = [station[0] for station in stations]
    frames = frames_along(path, up if up is not None else v(0.0, 0.0, 1.0), False)
    field = numpy.array([smooth_noise(segments, seed + s * 7, 2) for s in range(len(stations))]) if noise > 0.0 else numpy.zeros((len(stations), segments))
    if noise > 0.0 and len(stations) > 2:
        for index in range(2):
            field[1:-1] = (field[:-2] + field[1:-1] * 2.0 + field[2:]) * 0.25
    rings = []
    for i, station in enumerate(stations):
        center, half_side, half_up = station[0], station[1], station[2]
        front = station[3] if len(station) > 3 else 1.0
        back = station[4] if len(station) > 4 else 1.0
        egg = station[5] if len(station) > 5 else 0.0
        tangent, side, normal = frames[i]
        ring = []
        for s in range(segments):
            theta = math.pi * 2.0 * s / segments + math.pi * 0.25
            c = math.cos(theta)
            sn = math.sin(theta)
            x = math.copysign(abs(c) ** (2.0 / exponent), c)
            y = math.copysign(abs(sn) ** (2.0 / exponent), sn)
            width = half_side * (1.0 - egg * y)
            depth = half_up * (front if y > 0.0 else back)
            ring.append(bm.verts.new(center + (side * x * width + normal * y * depth) * (1.0 + noise * field[i, s])))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segments):
            n = (s + 1) % segments
            bm.faces.new((rings[i][s], rings[i][n], rings[i + 1][n], rings[i + 1][s]))
    if caps:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    return finish(bm, False)


def spline(points, steps=8):
    result = []
    count = len(points)
    for i in range(count - 1):
        p0 = points[max(i - 1, 0)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(i + 2, count - 1)]
        for s in range(steps):
            t = s / steps
            t2 = t * t
            t3 = t2 * t
            result.append(0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3))
    result.append(points[-1].copy())
    return result


def resample(path, spacing):
    length = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
    samples = max(int(length / spacing), 2)
    dense = []
    for s in range(samples + 1):
        target = length * s / samples
        walked = 0.0
        for i in range(len(path) - 1):
            step = (path[i + 1] - path[i]).length
            if walked + step >= target or i == len(path) - 2:
                t = 0.0 if step < 1e-9 else min(max((target - walked) / step, 0.0), 1.0)
                dense.append(path[i].lerp(path[i + 1], t))
                break
            walked += step
    return dense, length


def weld(points, radius, seed, ripple=0.16, pitch=0.62, flat=0.7):
    dense, length = resample(spline(points, 12), radius * 0.2)
    wobble = smooth_noise(len(dense), seed, 4)
    scales = []
    for i in range(len(dense)):
        along = length * i / max(len(dense) - 1, 1)
        taper = min(1.0, along / (radius * 1.2), (length - along) / (radius * 1.2))
        taper = math.sqrt(max(taper, 0.03))
        bump = 1.0 + ripple * (0.5 + 0.5 * math.cos(math.pi * 2.0 * along / (radius * pitch * 2.0))) + 0.1 * wobble[i]
        scales.append((taper * bump, taper * bump * flat))
    return sweep(dense, circle(radius, 12), up=v(0.0, 0.0, 1.0), scales=scales)


def helix(start, end, coil, wire, turns, segments=10):
    axis = end - start
    length = axis.length
    forward = axis.normalized()
    side = forward.orthogonal().normalized()
    other = forward.cross(side)
    steps = int(turns * 20)
    path = [start + forward * length * s / steps + (side * math.cos(math.pi * 2.0 * turns * s / steps) + other * math.sin(math.pi * 2.0 * turns * s / steps)) * coil for s in range(steps + 1)]
    return sweep(path, circle(wire, segments), up=forward)


def rope(path, radius, plies=2, pitch=3.2, segments=7, spacing=None):
    dense, length = resample(spline(path, 10), spacing if spacing is not None else radius * 0.35)
    frames = frames_along(dense, v(0.0, 0.0, 1.0), False)
    pieces = []
    for ply in range(plies):
        strand = []
        along = 0.0
        for i, point in enumerate(dense):
            if i > 0:
                along += (point - dense[i - 1]).length
            tangent, side, normal = frames[i]
            angle = along / (radius * pitch) * math.pi * 2.0 + ply * math.pi * 2.0 / plies
            strand.append(point + (side * math.cos(angle) + normal * math.sin(angle)) * radius * 0.46)
        pieces.append(sweep(strand, circle(radius * 0.58, segments), up=v(0.0, 0.0, 1.0)))
    return pieces


def outline_hull(circles, extra, segments=72):
    points = []
    for s in range(segments):
        phi = math.pi * 2.0 * s / segments
        dy = math.cos(phi)
        dz = math.sin(phi)
        best = max(circles, key=lambda c: c[0] * dy + c[1] * dz + c[2])
        points.append((best[0] + dy * (best[2] + extra), best[1] + dz * (best[2] + extra)))
    return points


def band(x, outline, width, thickness):
    path = [v(x, a, b) for a, b in outline]
    profile = [(0.0, -width * 0.5), (0.0, width * 0.5), (-thickness, width * 0.5), (-thickness, -width * 0.5)]
    return sweep(path, profile, closed=True, planar=v(1.0, 0.0, 0.0))


def cut(target, cutters):
    target_mesh = bpy.data.meshes.new("target")
    target.to_mesh(target_mesh)
    target.free()
    subject = bpy.data.objects.new("target", target_mesh)
    bpy.context.scene.collection.objects.link(subject)
    tools = []
    for index, cutter in enumerate(cutters):
        cutter_mesh = bpy.data.meshes.new("cutter")
        cutter.to_mesh(cutter_mesh)
        cutter.free()
        tool = bpy.data.objects.new("cutter", cutter_mesh)
        bpy.context.scene.collection.objects.link(tool)
        tools.append(tool)
        modifier = subject.modifiers.new("cut%d" % index, 'BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.solver = 'EXACT'
        modifier.object = tool
    bpy.context.view_layer.update()
    result = bpy.data.meshes.new_from_object(subject.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(subject)
    bpy.data.meshes.remove(target_mesh)
    for tool in tools:
        mesh = tool.data
        bpy.data.objects.remove(tool)
        bpy.data.meshes.remove(mesh)
    bm = bmesh.new()
    bm.from_mesh(result)
    bpy.data.meshes.remove(result)
    return bm


def transformed(bm, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return bm


def axis_frame(position, direction):
    forward = direction.normalized()
    up = v(0.0, 0.0, 1.0) if abs(forward.z) < 0.95 else v(1.0, 0.0, 0.0)
    return place(position, forward, up)


def shifted(bm, x=0.0, y=0.0, z=0.0):
    bmesh.ops.translate(bm, vec=v(x, y, z), verts=bm.verts)
    return bm


def threads(radius, length, pitch=0.0009):
    loop = [(0.0, 0.0), (radius, 0.0)]
    x = pitch * 0.5
    while x < length - pitch:
        loop += [(radius, x), (radius * 0.84, x + pitch * 0.5)]
        x += pitch
    loop += [(radius * 0.92, length - pitch * 0.4), (radius * 0.72, length), (0.0, length)]
    return revolve(loop, 18)


def hex_head(target, position, direction, across, height, look, washer=True):
    frame = axis_frame(position, direction)
    offset = 0.0
    if washer:
        target.add(revolve([(across * 0.3, -0.0007), (across * 0.66, -0.0007), (across * 0.66, 0.0), (across * 0.3, 0.0)], 28), look, frame, 0.00012, 1)
        offset = 0.0007
    target.add(shifted(hexagon(across, height, "x"), -offset - height * 0.5), look, frame, height * 0.16, 2, 50.0)


def nut(target, position, direction, across, height, radius, protrude, look):
    frame = axis_frame(position, direction)
    target.add(revolve([(radius * 1.05, 0.0), (across * 0.66, 0.0), (across * 0.66, 0.0007), (radius * 1.05, 0.0007)], 28), look, frame, 0.00012, 1)
    target.add(shifted(hexagon(across, height, "x"), 0.0007 + height * 0.5), look, frame, height * 0.16, 2, 50.0)
    target.add(threads(radius, 0.0007 + height + protrude), look, frame)


def screw(target, position, direction, radius, look, slot=True, dome=0.68):
    frame = axis_frame(position, direction)
    head = revolve([(0.0, 0.0), (radius, 0.0), (radius * 0.96, -radius * dome * 0.3), (radius * 0.8, -radius * dome * 0.66), (radius * 0.48, -radius * dome * 0.92), (0.0, -radius * dome)], 22)
    if slot:
        head = cut(head, [shifted(box(radius * 0.8, radius * 2.8, radius * 0.24), -radius * dome)])
    target.add(head, look, frame, radius * 0.04, 1)


def ring(target, center, axis, radius, wire, look, segments=40):
    forward = axis.normalized()
    side = forward.orthogonal().normalized()
    other = forward.cross(side)
    path = [center + (side * math.cos(math.pi * 2.0 * s / segments) + other * math.sin(math.pi * 2.0 * s / segments)) * radius for s in range(segments)]
    target.add(sweep(path, circle(wire, 12), closed=True, planar=forward), look)


def material(name):
    if name not in looks:
        looks[name] = build_look(name)
    return looks[name]


class assembly:
    def __init__(self, name):
        self.name = name
        self.slots = []
        self.meshes = []

    def add(self, bm, look, matrix=None, bevel=0.0, segments=3, angle=40.0, profile=0.6):
        if matrix is not None:
            bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
        mesh = bpy.data.meshes.new("piece")
        bm.to_mesh(mesh)
        bm.free()
        if bevel > 0.0:
            obj = bpy.data.objects.new("piece", mesh)
            bpy.context.scene.collection.objects.link(obj)
            modifier = obj.modifiers.new("bevel", 'BEVEL')
            modifier.width = bevel
            modifier.segments = segments
            modifier.limit_method = 'ANGLE'
            modifier.angle_limit = math.radians(angle)
            modifier.profile = profile
            modifier.use_clamp_overlap = True
            bpy.context.view_layer.update()
            final = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
            bpy.data.objects.remove(obj)
            bpy.data.meshes.remove(mesh)
            mesh = final
        if look not in self.slots:
            self.slots.append(look)
        self.meshes.append((mesh, self.slots.index(look)))

    def add_many(self, pieces, look, matrix=None, bevel=0.0):
        for piece in pieces:
            self.add(piece, look, matrix, bevel)

    def build(self, sharp=32.0):
        bm = bmesh.new()
        for mesh, index in self.meshes:
            before = len(bm.faces)
            bm.from_mesh(mesh)
            bm.faces.ensure_lookup_table()
            for face in bm.faces[before:]:
                face.material_index = index
            bpy.data.meshes.remove(mesh)
        mesh = bpy.data.meshes.new(self.name)
        bm.to_mesh(mesh)
        bm.free()
        for look in self.slots:
            mesh.materials.append(material(look))
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        mesh.set_sharp_from_angle(angle=math.radians(sharp))
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        modifier = obj.modifiers.new("weighted", 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
        modifier.weight = 50
        bpy.context.view_layer.update()
        final = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        obj.modifiers.clear()
        obj.data = final
        bpy.data.meshes.remove(mesh)
        final.name = self.name
        return obj


def image(path, colorspace):
    result = bpy.data.images.load(path, check_existing=True)
    result.colorspace_settings.name = colorspace
    return result


def math_node(tree, operation, a, b=None, clamp=False):
    result = tree.nodes.new('ShaderNodeMath')
    result.operation = operation
    result.use_clamp = clamp
    for index, value in enumerate((a, b)):
        if value is None:
            continue
        if isinstance(value, (int, float)):
            result.inputs[index].default_value = value
        else:
            tree.links.new(value, result.inputs[index])
    return result.outputs[0]


def mix_color(tree, factor, a, b, blend='MIX'):
    result = tree.nodes.new('ShaderNodeMix')
    result.data_type = 'RGBA'
    result.blend_type = blend
    for socket, value in ((result.inputs[0], factor), (result.inputs[6], a), (result.inputs[7], b)):
        if isinstance(value, (int, float)):
            socket.default_value = value
        elif isinstance(value, tuple):
            socket.default_value = value
        else:
            tree.links.new(value, socket)
    return result.outputs[2]


def mix_value(tree, factor, a, b):
    difference = math_node(tree, 'SUBTRACT', b, a)
    return math_node(tree, 'ADD', a, math_node(tree, 'MULTIPLY', difference, factor))


def ramp(tree, value, low, high):
    result = tree.nodes.new('ShaderNodeMapRange')
    result.clamp = True
    result.interpolation_type = 'SMOOTHSTEP'
    result.inputs['From Min'].default_value = low
    result.inputs['From Max'].default_value = high
    if isinstance(value, (int, float)):
        result.inputs['Value'].default_value = value
    else:
        tree.links.new(value, result.inputs['Value'])
    return result.outputs['Result']


def photo(tree, coordinates, path, scale, colorspace):
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale, scale, scale)
    tree.links.new(coordinates, mapping.inputs['Vector'])
    texture = tree.nodes.new('ShaderNodeTexImage')
    texture.image = image(path, colorspace)
    texture.projection = 'BOX'
    texture.projection_blend = 0.3
    tree.links.new(mapping.outputs['Vector'], texture.inputs['Vector'])
    return texture.outputs['Color']


def channel(tree, color, which):
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(color, split.inputs['Color'])
    return split.outputs[which]


def noise(tree, coordinates, scale, detail=6.0, roughness=0.6, distortion=0.0):
    result = tree.nodes.new('ShaderNodeTexNoise')
    result.inputs['Scale'].default_value = scale
    result.inputs['Detail'].default_value = detail
    result.inputs['Roughness'].default_value = roughness
    result.inputs['Distortion'].default_value = distortion
    tree.links.new(coordinates, result.inputs['Vector'])
    return result.outputs['Fac']


def masks(tree, edge_radius=0.0011, cavity_distance=0.006):
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    bevel = tree.nodes.new('ShaderNodeBevel')
    bevel.samples = 8
    bevel.inputs['Radius'].default_value = edge_radius
    dot = tree.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    tree.links.new(bevel.outputs['Normal'], dot.inputs[0])
    tree.links.new(geometry.outputs['Normal'], dot.inputs[1])
    edge = ramp(tree, math_node(tree, 'SUBTRACT', 1.0, dot.outputs['Value']), 0.004, 0.06)
    occlusion = tree.nodes.new('ShaderNodeAmbientOcclusion')
    occlusion.samples = 16
    occlusion.only_local = True
    occlusion.inputs['Distance'].default_value = cavity_distance
    cavity = ramp(tree, math_node(tree, 'SUBTRACT', 1.0, occlusion.outputs['AO']), 0.08, 0.7)
    return edge, cavity


def surface(tree, shader, height, strength, distance):
    bump = tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = distance
    if height is not None:
        tree.links.new(height, bump.inputs['Height'])
    bevel = tree.nodes.new('ShaderNodeBevel')
    bevel.samples = 8
    bevel.inputs['Radius'].default_value = 0.00035
    tree.links.new(bump.outputs['Normal'], bevel.inputs['Normal'])
    tree.links.new(bevel.outputs['Normal'], shader.inputs['Normal'])


def scaled(color, factor):
    return (color[0] * factor, color[1] * factor, color[2] * factor, 1.0)


def rust_photo(tree, coordinates, scale=7.0):
    return photo(tree, coordinates, os.path.join(roots["source"], "textures", "rusty_metal_04", "rusty_metal_04_diff_2k.jpg"), scale, 'sRGB')


def stretched_noise(tree, coordinates, scale, detail=5.0):
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = scale
    tree.links.new(coordinates, mapping.inputs['Vector'])
    return noise(tree, mapping.outputs['Vector'], 1.0, detail, 0.6)


def scratches(tree, coordinates, scale, width, offset, rotation=(0.0, 0.0, 0.0), stretch=0.07):
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Location'].default_value = (offset, offset * 0.7, offset * 1.3)
    mapping.inputs['Rotation'].default_value = rotation
    mapping.inputs['Scale'].default_value = (scale * stretch, scale, scale)
    tree.links.new(coordinates, mapping.inputs['Vector'])
    cells = tree.nodes.new('ShaderNodeTexVoronoi')
    cells.feature = 'DISTANCE_TO_EDGE'
    tree.links.new(mapping.outputs['Vector'], cells.inputs['Vector'])
    return math_node(tree, 'MULTIPLY', ramp(tree, cells.outputs['Distance'], width, 0.0), ramp(tree, noise(tree, coordinates, 7.0, 3.0, 0.5), 0.52, 0.64), True)


def spangle_cells(tree, coordinates, scale):
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale, scale, scale)
    tree.links.new(coordinates, mapping.inputs['Vector'])
    cells = tree.nodes.new('ShaderNodeTexVoronoi')
    cells.feature = 'F1'
    tree.links.new(mapping.outputs['Vector'], cells.inputs['Vector'])
    return channel(tree, cells.outputs['Color'], 'Red')


def wood_grain(tree, coordinates, scale, offset, warp_amount=3.0, distortion=1.4, direction='Z'):
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Location'].default_value = offset
    mapping.inputs['Scale'].default_value = {'Z': (scale, scale, scale * 0.08), 'Y': (scale, scale * 0.08, scale)}.get(direction, (scale * 0.08, scale, scale))
    tree.links.new(coordinates, mapping.inputs['Vector'])
    warp = tree.nodes.new('ShaderNodeTexNoise')
    warp.inputs['Scale'].default_value = 0.06
    warp.inputs['Detail'].default_value = 3.0
    tree.links.new(mapping.outputs['Vector'], warp.inputs['Vector'])
    centered = tree.nodes.new('ShaderNodeVectorMath')
    centered.operation = 'SUBTRACT'
    tree.links.new(warp.outputs['Color'], centered.inputs[0])
    centered.inputs[1].default_value = (0.5, 0.5, 0.5)
    amount = tree.nodes.new('ShaderNodeVectorMath')
    amount.operation = 'SCALE'
    tree.links.new(centered.outputs['Vector'], amount.inputs[0])
    amount.inputs['Scale'].default_value = warp_amount
    moved = tree.nodes.new('ShaderNodeVectorMath')
    moved.operation = 'ADD'
    tree.links.new(mapping.outputs['Vector'], moved.inputs[0])
    tree.links.new(amount.outputs['Vector'], moved.inputs[1])
    rings = tree.nodes.new('ShaderNodeTexWave')
    rings.wave_type = 'RINGS'
    rings.rings_direction = direction
    rings.wave_profile = 'SAW'
    rings.inputs['Scale'].default_value = 1.0
    rings.inputs['Distortion'].default_value = distortion
    rings.inputs['Detail'].default_value = 3.0
    rings.inputs['Detail Scale'].default_value = 1.4
    tree.links.new(moved.outputs['Vector'], rings.inputs['Vector'])
    return rings.outputs['Fac']


def metal_look(tree, shader, coordinates, edge, cavity, chips, blotch, base, metallic, rough_low, rough_high, rust_amount, bump):
    acg = os.path.join(roots["raw"], "textures_acg", "Metal027")
    grain = photo(tree, coordinates, os.path.join(acg, "Metal027_2K-JPG_Roughness.jpg"), 9.0, 'Non-Color')
    height = photo(tree, coordinates, os.path.join(acg, "Metal027_2K-JPG_Displacement.jpg"), 9.0, 'Non-Color')
    mottle = noise(tree, coordinates, 30.0, 5.0, 0.6)
    fine = noise(tree, coordinates, 140.0, 4.0, 0.6)
    color = mix_color(tree, mottle, scaled(base, 0.7), (base[0] * 1.35, base[1] * 1.15, base[2] * 1.0, 1.0))
    color = mix_color(tree, math_node(tree, 'MULTIPLY', ramp(tree, noise(tree, coordinates, 12.0, 4.0, 0.5), 0.45, 0.75), 0.6), color, (base[0] * 0.85, base[1] * 0.95, base[2] * 1.25, 1.0))
    color = mix_color(tree, math_node(tree, 'MULTIPLY', fine, 0.35), color, scaled(base, 0.55))
    rust = rust_photo(tree, coordinates)
    patches = math_node(tree, 'MULTIPLY', ramp(tree, noise(tree, coordinates, 8.0, 6.0, 0.6), 0.52, 0.7), ramp(tree, noise(tree, coordinates, 60.0, 6.0, 0.6), 0.32, 0.6))
    rust_mask = math_node(tree, 'MULTIPLY', math_node(tree, 'ADD', math_node(tree, 'ADD', math_node(tree, 'MULTIPLY', cavity, 1.3), math_node(tree, 'MULTIPLY', patches, 0.9)), math_node(tree, 'MULTIPLY', edge, 0.25)), rust_amount, True)
    rust_mask = math_node(tree, 'MULTIPLY', rust_mask, ramp(tree, chips, 0.3, 0.58), True)
    pits = math_node(tree, 'MULTIPLY', ramp(tree, noise(tree, coordinates, 520.0, 2.0, 0.5), 0.66, 0.74), rust_amount * 0.9, True)
    color = mix_color(tree, rust_mask, color, rust)
    color = mix_color(tree, pits, color, (0.045, 0.022, 0.01, 1.0))
    wear = math_node(tree, 'MULTIPLY', edge, ramp(tree, chips, 0.45, 0.62), True)
    color = mix_color(tree, wear, color, (0.52, 0.51, 0.49, 1.0))
    tree.links.new(color, shader.inputs['Base Color'])
    roughness = mix_value(tree, grain, rough_low, rough_high)
    roughness = mix_value(tree, math_node(tree, 'MAXIMUM', rust_mask, pits), roughness, 0.88)
    roughness = mix_value(tree, wear, roughness, 0.22)
    tree.links.new(roughness, shader.inputs['Roughness'])
    metal = mix_value(tree, math_node(tree, 'MAXIMUM', rust_mask, pits), metallic, 0.1)
    metal = mix_value(tree, wear, metal, 1.0)
    tree.links.new(metal, shader.inputs['Metallic'])
    relief = math_node(tree, 'SUBTRACT', math_node(tree, 'ADD', math_node(tree, 'MULTIPLY', height, 0.4), math_node(tree, 'MULTIPLY', rust_mask, 0.6)), math_node(tree, 'MULTIPLY', pits, 0.4))
    surface(tree, shader, relief, bump, 0.0004)


def build_look(name):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    tree = result.node_tree
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    coordinates = tree.nodes.new('ShaderNodeTexCoord').outputs['Object']
    raw = os.path.join(roots["raw"], "textures")
    edge, cavity = masks(tree)
    chips = noise(tree, coordinates, 180.0, 8.0, 0.65)
    blotch = noise(tree, coordinates, 22.0, 5.0, 0.55)
    if name == "steel":
        metal_look(tree, shader, coordinates, edge, cavity, chips, blotch, (0.42, 0.41, 0.39), 1.0, 0.28, 0.45, 0.4, 0.1)
    elif name == "iron":
        metal_look(tree, shader, coordinates, edge, cavity, chips, blotch, (0.05, 0.043, 0.037), 0.75, 0.4, 0.6, 0.85, 0.15)
    elif name == "blued":
        metal_look(tree, shader, coordinates, edge, cavity, chips, blotch, (0.05, 0.055, 0.065), 1.0, 0.22, 0.38, 0.2, 0.08)
    elif name in ("painted", "primer"):
        red = name == "primer"
        streaks = stretched_noise(tree, coordinates, (4.0, 70.0, 70.0))
        color = mix_color(tree, streaks, (0.082, 0.02, 0.011, 1.0) if red else (0.036, 0.042, 0.024, 1.0), (0.11, 0.03, 0.016, 1.0) if red else (0.052, 0.058, 0.034, 1.0))
        fade = math_node(tree, 'MULTIPLY', ramp(tree, noise(tree, coordinates, 6.0, 4.0, 0.5), 0.4, 0.8), 0.55)
        color = mix_color(tree, fade, color, (0.15, 0.066, 0.046, 1.0) if red else (0.085, 0.088, 0.062, 1.0))
        zone = ramp(tree, channel(tree, coordinates, 'Red'), -0.005, -0.06)
        flakes = math_node(tree, 'ADD', ramp(tree, noise(tree, coordinates, 14.0, 8.0, 0.65), 0.57, 0.68), math_node(tree, 'MULTIPLY', zone, 0.55))
        coverage = math_node(tree, 'ADD', math_node(tree, 'MULTIPLY', edge, 2.2), flakes)
        chip = math_node(tree, 'MULTIPLY', coverage, ramp(tree, noise(tree, coordinates, 120.0, 8.0, 0.7), 0.4, 0.55), True)
        rim = math_node(tree, 'MULTIPLY', math_node(tree, 'SUBTRACT', math_node(tree, 'MULTIPLY', coverage, ramp(tree, noise(tree, coordinates, 120.0, 8.0, 0.7), 0.32, 0.47), True), chip), 1.0, True)
        under = mix_color(tree, ramp(tree, noise(tree, coordinates, 60.0, 4.0, 0.6), 0.4, 0.62), (0.03, 0.028, 0.026, 1.0), rust_photo(tree, coordinates))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', rim, 0.8), color, (0.11, 0.045, 0.028, 1.0))
        color = mix_color(tree, chip, color, under)
        scratch = math_node(tree, 'MAXIMUM', scratches(tree, coordinates, 34.0, 0.02, 3.0, (0.0, 0.35, 0.0)), scratches(tree, coordinates, 26.0, 0.02, 7.0, (0.0, -0.9, 0.0)))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', scratch, 0.85), color, (0.32, 0.31, 0.3, 1.0))
        geometry = tree.nodes.new('ShaderNodeNewGeometry')
        dust = math_node(tree, 'MULTIPLY', ramp(tree, channel(tree, geometry.outputs['Normal'], 'Blue'), 0.4, 0.95), 0.3)
        color = mix_color(tree, dust, color, (0.14, 0.13, 0.11, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', cavity, 0.75), color, (0.018, 0.016, 0.011, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        roughness = mix_value(tree, chip, mix_value(tree, fade, 0.62 if red else 0.52, 0.8 if red else 0.72), 0.8)
        roughness = mix_value(tree, dust, roughness, 0.85)
        tree.links.new(mix_value(tree, scratch, roughness, 0.3), shader.inputs['Roughness'])
        tree.links.new(mix_value(tree, scratch, mix_value(tree, chip, 0.0, 0.15), 0.9), shader.inputs['Metallic'])
        peel = noise(tree, coordinates, 420.0, 2.0, 0.5)
        surface(tree, shader, math_node(tree, 'ADD', math_node(tree, 'SUBTRACT', 1.0, math_node(tree, 'MAXIMUM', chip, scratch)), math_node(tree, 'MULTIPLY', peel, 0.06)), 0.5, 0.0003)
    elif name in ("wood", "wood_long", "wood_dark", "wood_y", "wood_dark_long"):
        along = {"wood": 'Z', "wood_dark": 'Z', "wood_y": 'Y'}.get(name, 'X')
        grain = wood_grain(tree, coordinates, 330.0 if along == 'Z' else 150.0, {'Z': (19.0, 11.0, 0.0), 'Y': (5.0, 0.0, 7.0)}.get(along, (0.0, 5.0, 7.0)), 5.0 if along == 'Z' else 9.0, 2.2 if along == 'Z' else 3.2, along)
        pores = ramp(tree, stretched_noise(tree, coordinates, {'Z': (1400.0, 1400.0, 70.0), 'Y': (1400.0, 70.0, 1400.0)}.get(along, (70.0, 1400.0, 1400.0)), 3.0), 0.6, 0.74)
        figure = noise(tree, coordinates, 7.0 if along == 'Z' else 4.0, 5.0, 0.55)
        light, dark = ((0.1, 0.053, 0.027, 1.0), (0.042, 0.021, 0.011, 1.0)) if name == "wood" else (((0.078, 0.041, 0.02, 1.0), (0.032, 0.016, 0.008, 1.0)) if name in ("wood_long", "wood_y") else ((0.075, 0.042, 0.024, 1.0), (0.04, 0.022, 0.013, 1.0)))
        color = mix_color(tree, ramp(tree, grain, 0.2, 0.95), light, dark)
        color = mix_color(tree, math_node(tree, 'MULTIPLY', ramp(tree, figure, 0.3, 0.7), 0.6), color, scaled(light, 1.18))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', pores, 0.55), color, scaled(dark, 0.5))
        handled = ramp(tree, noise(tree, coordinates, 12.0, 4.0, 0.5), 0.35, 0.7)
        color = mix_color(tree, math_node(tree, 'MULTIPLY', handled, 0.3), color, scaled(dark, 0.7))
        grime = math_node(tree, 'MULTIPLY', math_node(tree, 'ADD', cavity, math_node(tree, 'MULTIPLY', ramp(tree, blotch, 0.55, 0.8), 0.3)), 0.8, True)
        color = mix_color(tree, grime, color, (0.022, 0.014, 0.009, 1.0))
        worn = math_node(tree, 'MULTIPLY', edge, ramp(tree, chips, 0.3, 0.6), True)
        color = mix_color(tree, math_node(tree, 'MULTIPLY', worn, 0.6), color, (0.3, 0.19, 0.11, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        roughness = mix_value(tree, handled, 0.58, 0.38)
        roughness = mix_value(tree, pores, roughness, 0.75)
        tree.links.new(mix_value(tree, grime, roughness, 0.8), shader.inputs['Roughness'])
        shader.inputs['Metallic'].default_value = 0.0
        surface(tree, shader, math_node(tree, 'SUBTRACT', math_node(tree, 'MULTIPLY', grain, 0.3), math_node(tree, 'MULTIPLY', pores, 0.5)), 0.3, 0.0004)
    elif name == "cloth":
        folder = os.path.join(raw, "hessian_230")
        base = photo(tree, coordinates, os.path.join(folder, "hessian_230_diff_2k.jpg"), 9.0, 'sRGB')
        height = photo(tree, coordinates, os.path.join(folder, "hessian_230_disp_2k.jpg"), 9.0, 'Non-Color')
        color = mix_color(tree, 1.0, base, (0.72, 0.64, 0.52, 1.0), 'MULTIPLY')
        grime = math_node(tree, 'MULTIPLY', math_node(tree, 'ADD', cavity, ramp(tree, blotch, 0.4, 0.8)), 0.7, True)
        color = mix_color(tree, grime, color, (0.08, 0.065, 0.048, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        shader.inputs['Roughness'].default_value = 0.93
        surface(tree, shader, height, 0.8, 0.0007)
    elif name == "rope":
        fibers = noise(tree, coordinates, 900.0, 4.0, 0.7)
        patches = noise(tree, coordinates, 40.0, 4.0, 0.5)
        color = mix_color(tree, fibers, (0.12, 0.08, 0.04, 1.0), (0.38, 0.28, 0.15, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', ramp(tree, patches, 0.45, 0.75), 0.5), color, (0.2, 0.17, 0.09, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', cavity, 0.8), color, (0.04, 0.028, 0.016, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        shader.inputs['Roughness'].default_value = 0.92
        surface(tree, shader, fibers, 0.5, 0.0004)
    elif name == "rubber":
        grain = noise(tree, coordinates, 300.0, 3.0, 0.5)
        color = mix_color(tree, grain, (0.016, 0.015, 0.014, 1.0), (0.028, 0.026, 0.024, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', edge, 0.5), color, (0.065, 0.06, 0.055, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        tree.links.new(mix_value(tree, edge, 0.7, 0.5), shader.inputs['Roughness'])
        surface(tree, shader, grain, 0.15, 0.0003)
    elif name == "paper":
        fibers = noise(tree, coordinates, 260.0, 4.0, 0.6)
        stains = ramp(tree, noise(tree, coordinates, 9.0, 5.0, 0.6), 0.52, 0.8)
        color = mix_color(tree, fibers, (0.62, 0.57, 0.46, 1.0), (0.7, 0.66, 0.55, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', stains, 0.7), color, (0.42, 0.32, 0.2, 1.0))
        lines = ramp(tree, stretched_noise(tree, coordinates, (6.0, 900.0, 6.0), 1.0), 0.62, 0.7)
        color = mix_color(tree, math_node(tree, 'MULTIPLY', lines, 0.55), color, (0.08, 0.07, 0.08, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', cavity, 0.6), color, (0.2, 0.16, 0.1, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        shader.inputs['Roughness'].default_value = 0.9
        shader.inputs['Metallic'].default_value = 0.0
        surface(tree, shader, fibers, 0.1, 0.0002)
    elif name == "copper":
        color = mix_color(tree, math_node(tree, 'MULTIPLY', ramp(tree, blotch, 0.45, 0.75), 0.7), (0.62, 0.3, 0.16, 1.0), (0.2, 0.26, 0.2, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', cavity, 0.8), color, (0.05, 0.04, 0.03, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        tree.links.new(mix_value(tree, ramp(tree, blotch, 0.4, 0.7), 0.3, 0.55), shader.inputs['Roughness'])
        shader.inputs['Metallic'].default_value = 1.0
        surface(tree, shader, None, 0.0, 0.0)
    elif name == "brass":
        color = mix_color(tree, math_node(tree, 'MULTIPLY', cavity, 0.8), (0.7, 0.5, 0.22, 1.0), (0.16, 0.1, 0.04, 1.0))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', ramp(tree, blotch, 0.5, 0.75), 0.5), color, (0.34, 0.26, 0.12, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        tree.links.new(mix_value(tree, ramp(tree, blotch, 0.4, 0.7), 0.24, 0.5), shader.inputs['Roughness'])
        shader.inputs['Metallic'].default_value = 1.0
        surface(tree, shader, None, 0.0, 0.0)
    elif name == "glass":
        color = mix_color(tree, math_node(tree, 'MULTIPLY', ramp(tree, blotch, 0.5, 0.8), 0.6), (0.006, 0.009, 0.012, 1.0), (0.03, 0.028, 0.024, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        tree.links.new(mix_value(tree, ramp(tree, blotch, 0.45, 0.8), 0.03, 0.35), shader.inputs['Roughness'])
        shader.inputs['Metallic'].default_value = 0.0
        surface(tree, shader, None, 0.0, 0.0)
    elif name == "zinc":
        crystals = spangle_cells(tree, coordinates, 80.0)
        color = mix_color(tree, crystals, (0.19, 0.195, 0.2, 1.0), (0.225, 0.23, 0.235, 1.0))
        tarnish = ramp(tree, noise(tree, coordinates, 20.0, 5.0, 0.6), 0.4, 0.75)
        color = mix_color(tree, math_node(tree, 'MULTIPLY', tarnish, 0.6), color, (0.07, 0.068, 0.066, 1.0))
        oxide = math_node(tree, 'MULTIPLY', ramp(tree, noise(tree, coordinates, 25.0, 6.0, 0.65), 0.55, 0.68), ramp(tree, chips, 0.25, 0.55), True)
        color = mix_color(tree, math_node(tree, 'MULTIPLY', oxide, 0.85), color, (0.4, 0.4, 0.37, 1.0))
        stain = math_node(tree, 'MULTIPLY', math_node(tree, 'ADD', math_node(tree, 'MULTIPLY', cavity, 1.1), math_node(tree, 'MULTIPLY', ramp(tree, blotch, 0.62, 0.8), 0.8)), ramp(tree, chips, 0.3, 0.55), True)
        color = mix_color(tree, stain, color, rust_photo(tree, coordinates))
        color = mix_color(tree, math_node(tree, 'MULTIPLY', cavity, 0.7), color, (0.02, 0.019, 0.017, 1.0))
        tree.links.new(color, shader.inputs['Base Color'])
        roughness = mix_value(tree, crystals, 0.36, 0.5)
        roughness = mix_value(tree, tarnish, roughness, 0.64)
        tree.links.new(mix_value(tree, math_node(tree, 'MAXIMUM', oxide, stain), roughness, 0.85), shader.inputs['Roughness'])
        tree.links.new(mix_value(tree, math_node(tree, 'MAXIMUM', oxide, stain), 1.0, 0.15), shader.inputs['Metallic'])
        surface(tree, shader, math_node(tree, 'ADD', math_node(tree, 'MULTIPLY', crystals, 0.05), math_node(tree, 'MULTIPLY', math_node(tree, 'MAXIMUM', oxide, stain), 0.5)), 0.25, 0.0003)
    return result


def gltf_group():
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
        group.interface.new_socket(name="Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
        group.interface.new_socket(name="Thickness", in_out='INPUT', socket_type='NodeSocketFloat')
    return group


def unwrap(obj, margin=0.003):
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.view_layer.objects:
        other.select_set(other == obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(52.0), island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def pixels_of(img):
    data = numpy.empty(img.size[0] * img.size[1] * 4, dtype=numpy.float32)
    img.pixels.foreach_get(data)
    return data.reshape(img.size[1], img.size[0], 4)


def save(name, data, directory, colorspace):
    height, width = data.shape[:2]
    result = bpy.data.images.new(name, width, height, alpha=False)
    result.pixels.foreach_set(numpy.ascontiguousarray(numpy.clip(data, 0.0, 1.0), dtype=numpy.float32).ravel())
    result.filepath_raw = os.path.join(directory, name + ".png")
    result.file_format = 'PNG'
    result.save()
    result.colorspace_settings.name = colorspace
    return result


def bake(obj, directory, size=2048, samples=24):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    turntable_accelerate(scene)
    scene.cycles.samples = samples
    scene.render.bake.margin = 12
    scene.render.bake.use_clear = True
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.view_layer.objects:
        other.select_set(other == obj)
    targets = {}
    for key in ("color", "rough", "metal", "normal", "ao"):
        target = bpy.data.images.new(obj.name + "_" + key, size, size, alpha=False, float_buffer=True)
        target.colorspace_settings.name = 'Non-Color'
        targets[key] = target
    for slot in obj.data.materials:
        holder = slot.node_tree.nodes.new('ShaderNodeTexImage')
        holder.name = "bake_target"

    def aim(target):
        for slot in obj.data.materials:
            holder = slot.node_tree.nodes["bake_target"]
            holder.image = target
            slot.node_tree.nodes.active = holder

    def emit(input_name, target):
        saved = {}
        for slot in obj.data.materials:
            tree = slot.node_tree
            shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
            output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
            emission = tree.nodes.new('ShaderNodeEmission')
            emission.name = "bake_emit"
            socket = shader.inputs[input_name]
            if socket.links:
                tree.links.new(socket.links[0].from_socket, emission.inputs['Color'])
            else:
                value = socket.default_value
                emission.inputs['Color'].default_value = tuple(value) if hasattr(value, '__len__') else (value, value, value, 1.0)
            saved[slot.name] = output.inputs['Surface'].links[0].from_socket
            tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        aim(target)
        bpy.ops.object.bake(type='EMIT', margin=12)
        for slot in obj.data.materials:
            tree = slot.node_tree
            output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
            tree.links.new(saved[slot.name], output.inputs['Surface'])
            tree.nodes.remove(tree.nodes["bake_emit"])

    emit('Base Color', targets["color"])
    emit('Metallic', targets["metal"])
    aim(targets["rough"])
    bpy.ops.object.bake(type='ROUGHNESS', margin=12)
    aim(targets["normal"])
    bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=12)
    scene.cycles.samples = max(samples, 48)
    aim(targets["ao"])
    bpy.ops.object.bake(type='AO', margin=12)
    scene.cycles.samples = samples
    color = pixels_of(targets["color"])
    linear = numpy.clip(color[:, :, :3], 0.0, 1.0)
    color[:, :, :3] = numpy.where(linear <= 0.0031308, linear * 12.92, 1.055 * numpy.power(numpy.maximum(linear, 0.0031308), 1.0 / 2.4) - 0.055)
    color[:, :, 3] = 1.0
    orm = numpy.ones((size, size, 4), dtype=numpy.float32)
    orm[:, :, 0] = numpy.clip(pixels_of(targets["ao"])[:, :, 0] * 0.75 + 0.25, 0.0, 1.0)
    orm[:, :, 1] = pixels_of(targets["rough"])[:, :, 0]
    orm[:, :, 2] = pixels_of(targets["metal"])[:, :, 0]
    normal = pixels_of(targets["normal"])
    normal[:, :, 3] = 1.0
    return (save(obj.name + "_albedo", color, directory, 'sRGB'), save(obj.name + "_orm", orm, directory, 'Non-Color'), save(obj.name + "_normal", normal, directory, 'Non-Color'))


def baked_material(name, images):
    albedo, orm, normal = images
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    tree = result.node_tree
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    color = tree.nodes.new('ShaderNodeTexImage')
    color.image = albedo
    tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    packed = tree.nodes.new('ShaderNodeTexImage')
    packed.image = orm
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(packed.outputs['Color'], split.inputs['Color'])
    tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
    tree.links.new(split.outputs['Blue'], shader.inputs['Metallic'])
    settings = tree.nodes.new('ShaderNodeGroup')
    settings.node_tree = gltf_group()
    tree.links.new(split.outputs['Red'], settings.inputs['Occlusion'])
    bumps = tree.nodes.new('ShaderNodeTexImage')
    bumps.image = normal
    mapping = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(bumps.outputs['Color'], mapping.inputs['Color'])
    tree.links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    return result


def bake_part(obj, directory, size=2048, samples=24):
    unwrap(obj)
    images = bake(obj, directory, size, samples)
    obj.data.materials.clear()
    obj.data.materials.append(baked_material(obj.name + "_baked", images))
    for polygon in obj.data.polygons:
        polygon.material_index = 0


def export(path, glb=False):
    if glb:
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_image_format='WEBP', export_image_quality=90, export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_skins=False, export_animations=False, export_morph=False, export_yup=True, export_apply=True, use_selection=False, export_extras=False, export_cameras=False, export_lights=False)
    else:
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', export_image_format='AUTO', export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT', export_skins=False, export_animations=False, export_morph=False, export_yup=True, export_apply=True, use_selection=False, export_extras=False, export_cameras=False, export_lights=False)
