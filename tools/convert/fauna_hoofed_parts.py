import math
import numpy
import fauna_hoofed_field as fields
import fauna_hoofed_cage as cages

flip = numpy.array([-1.0, 1.0, 1.0])
claw_outline = numpy.array([(0.1, 1.0), (0.45, 0.88), (0.8, 0.68), (1.0, 0.42), (0.97, 0.18), (0.72, 0.02), (0.3, 0.0), (0.02, 0.12), (0.0, 0.45), (0.0, 0.8)])


def shell(points, faces, tags, bone, part, cuts=(), coord=None):
    points = numpy.asarray(points, dtype=numpy.float64)
    return {"points": points, "faces": [tuple(face) for face in faces], "tags": list(tags), "bone": bone, "part": part, "cuts": list(cuts), "coord": numpy.zeros((len(points), 2)) if coord is None else numpy.asarray(coord, dtype=numpy.float64)}


def mirrored(piece, bone=None):
    result = {"points": piece["points"] * flip[None, :], "faces": [tuple(reversed(face)) for face in piece["faces"]], "tags": list(piece["tags"]), "bone": bone or piece["bone"], "part": piece["part"], "cuts": list(piece["cuts"]), "coord": piece["coord"].copy()}
    if "normal" in piece:
        result["normal"] = piece["normal"] * flip[None, :]
        result["root"] = piece["root"] * flip
    return result


def lock(root, normal, direction, length, width, thick, lift, droop=(0.0, 0.0, 0.0), tag="lock"):
    root = numpy.asarray(root, dtype=numpy.float64)
    n = fields.unit(normal)
    d = fields.unit(direction)
    side = fields.unit(numpy.cross(n, d))
    base = root - n * 0.006
    middle = root + d * (length * 0.55) + n * lift
    tip = root + d * length + n * (lift * 0.4) + numpy.asarray(droop, dtype=numpy.float64)
    points = [base + side * (width * 0.5), base - side * (width * 0.5), base + n * thick - d * 0.008, middle + side * (width * 0.3), middle - side * (width * 0.3), middle + n * (thick * 0.55), tip]
    faces = [(0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0), (3, 6, 4), (4, 6, 5), (5, 6, 3)]
    piece = shell(points, faces, [tag] * len(faces), None, "lock", [(0, 3), (3, 6)], [(0.0, 1.0)] * 3 + [(0.55, 1.0)] * 3 + [(1.0, 1.0)])
    piece["normal"] = numpy.array([fields.unit(n + side * 0.45), fields.unit(n - side * 0.45), fields.unit(n - d * 0.2), fields.unit(n + side * 0.45 + d * 0.2), fields.unit(n - side * 0.45 + d * 0.2), fields.unit(n + d * 0.1), fields.unit(n * 0.7 + d * 0.7)])
    piece["root"] = root
    return piece


def tufts(f, groups, seeds, seed=7):
    rng = numpy.random.default_rng(seed)
    pieces = []
    for entry in seeds:
        if "root" in entry:
            root = numpy.asarray(entry["root"], dtype=numpy.float64)
            normal = fields.unit(entry["normal"])
        else:
            origin = numpy.asarray(entry["origin"], dtype=numpy.float64)
            ray = fields.unit(entry["ray"])
            distance, found = f.cast(origin[None, :], ray[None, :], entry.get("reach", 0.5), groups, steps=200)
            if not found[0]:
                continue
            root = origin + ray * float(distance[0])
            normal = f.normals(root[None, :], groups)[0]
        flow = numpy.asarray(entry["flow"], dtype=numpy.float64)
        if "lean" in entry:
            along = fields.unit(flow - normal * float(flow @ normal))
            flow = along * math.cos(math.radians(entry["lean"])) + normal * math.sin(math.radians(entry["lean"]))
        if "facing" in entry:
            normal = fields.unit(entry["facing"])
        flow = fields.rotation(normal, (rng.random() - 0.5) * 2.0 * entry.get("spread", 12.0)) @ (flow - normal * float(flow @ normal))
        direction = fields.unit(fields.unit(flow) + normal * entry.get("rise", 0.35))
        jitter = 0.75 + 0.5 * rng.random()
        piece = lock(root, normal, direction, entry["length"] * jitter, entry["width"] * (0.85 + 0.3 * rng.random()), entry.get("thick", 0.012), entry.get("lift", 0.004), numpy.array([0.0, 0.0, -entry.get("sag", 0.2) * entry["length"] * jitter]), entry.get("tag", "lock"))
        pieces.append(piece)
        if abs(root[0]) > 1e-4:
            pieces.append(mirrored(piece))
    return pieces


def claw(center, heel, length, width, toe_height, heel_height, side, gap=0.004, spread=0.004, retreat=0.42, bone="hoof"):
    levels = (0.0, 0.5, 1.0)
    count = len(claw_outline)
    points = []
    for level in levels:
        for x, y in claw_outline:
            reach = y * (1.0 - retreat * level)
            points.append((center + side * (gap * 0.5 + spread * reach + x * width * (1.0 - 0.14 * level)), heel - reach * length, level * (heel_height + (toe_height - heel_height) * y)))
    faces = []
    tags = []
    for level in range(len(levels) - 1):
        for index in range(count):
            a = level * count + index
            c = level * count + (index + 1) % count
            faces.append((a, c, c + count, a + count))
            tags.append("hoof")
    middle = numpy.array(points[:count]).mean(axis=0)
    points.append((middle[0], middle[1], 0.004))
    for index in range(count):
        faces.append((index, (index + 1) % count, len(points) - 1))
        tags.append("hoof_sole")
    top = numpy.array(points[(len(levels) - 1) * count:len(levels) * count]).mean(axis=0)
    points.append((top[0], top[1], top[2] + 0.003))
    base = (len(levels) - 1) * count
    for index in range(count):
        faces.append((base + index, base + (index + 1) % count, len(points) - 1))
        tags.append("hoof_top")
    cuts = [(level * count + 7, (level + 1) * count + 7) for level in range(len(levels) - 1)]
    return shell(points, faces, tags, bone, "hoof", cuts)


def sweep(path, radii, sides, tag, bone, part, flat=1.0, up=(0.0, 0.0, 1.0), pointed=True, smooth=0, mark=0.0):
    path = numpy.asarray(path, dtype=numpy.float64)
    radii = numpy.asarray(radii, dtype=numpy.float64)
    if smooth:
        travel = numpy.r_[0.0, numpy.cumsum(numpy.linalg.norm(numpy.diff(path, axis=0), axis=1))]
        dense = numpy.linspace(0.0, travel[-1], smooth)
        table = fields.monotone_table(travel, numpy.column_stack([path, radii]), 96)
        grid = numpy.linspace(0.0, travel[-1], 96)
        path = numpy.column_stack([numpy.interp(dense, grid, table[:, axis]) for axis in range(3)])
        radii = numpy.interp(dense, grid, table[:, 3])
    rings = cages.tube_rings(path, radii, sides, flat, up)
    points = [point for ring in rings for point in ring]
    faces = []
    for level in range(len(rings) - 1):
        for index in range(sides):
            a = level * sides + index
            c = level * sides + (index + 1) % sides
            faces.append((a, c, c + sides, a + sides))
    last = (len(rings) - 1) * sides
    if pointed:
        points.append(path[-1] + (path[-1] - path[-2]) * 0.5)
        for index in range(sides):
            faces.append((last + index, last + (index + 1) % sides, len(points) - 1))
    cuts = [(level * sides, (level + 1) * sides) for level in range(len(rings) - 1)]
    if pointed:
        cuts.append((last, len(points) - 1))
    coord = [(level / (len(rings) - 1.0), mark) for level in range(len(rings)) for index in range(sides)] + ([(1.0, mark)] if pointed else [])
    return shell(points, faces, [tag] * len(faces), bone, part, cuts, coord)


def eyeball(eye, bone="head"):
    points, faces = cages.eyeball(eye)
    return shell(points, faces, ["eyeball"] * len(faces), bone, "eyeball")


def hooves(marks, spec):
    pieces = []
    for leg, bone in (("f", "hoof_f"), ("h", "hoof_h")):
        toe = marks["toe_" + leg]
        length = spec["length"]
        heel = float(toe[1]) + length
        for side in (1.0, -1.0):
            piece = claw(float(toe[0]), heel, length, spec["width"], spec["toe_height"], spec["heel_height"], side, bone=bone + "_l")
            pieces.append(piece)
            pieces.append(mirrored(piece, bone + "_r"))
        fetlock = marks["fetlock_" + leg]
        for side in (1.0, -1.0):
            base = fetlock + numpy.array([side * spec["dew_offset"], spec["dew_back"], -spec["dew_drop"]])
            tip = base + numpy.array([side * 0.004, 0.012, -spec["dew_length"]])
            piece = sweep([base + (base - tip) * 0.4, base, base + (tip - base) * 0.6], [spec["dew_radius"] * 0.8, spec["dew_radius"], spec["dew_radius"] * 0.6], 6, "hoof", ("pastern_f" if leg == "f" else "pastern_h") + "_l", "hoof", up=(0.0, 1.0, 0.0))
            pieces.append(piece)
            pieces.append(mirrored(piece, ("pastern_f" if leg == "f" else "pastern_h") + "_r"))
    return pieces


def antlers(root, spec):
    pieces = []
    beam = numpy.array(spec["beam"], dtype=numpy.float64) + root[None, :]
    pieces.append(sweep(beam, spec["beam_radii"], 8, "antler", "head", "antler", smooth=spec.get("rings", 18)))
    burr = [beam[0] - (beam[1] - beam[0]) * 0.12, beam[0], beam[0] + (beam[1] - beam[0]) * 0.1]
    pieces.append(sweep(burr, [spec["beam_radii"][0] * 1.0, spec["beam_radii"][0] * 1.45, spec["beam_radii"][0] * 1.05], 8, "antler", "head", "antler", pointed=False))
    for tine in spec["tines"]:
        path = numpy.array(tine["path"], dtype=numpy.float64) + root[None, :]
        pieces.append(sweep(path, tine["radii"], 6, "antler", "head", "antler", smooth=tine.get("rings", 7), mark=1.0))
    return pieces + [mirrored(piece) for piece in pieces]


def combine(skin, pieces):
    points = [skin["points"]]
    faces = list(skin["faces"])
    tags = list(skin["tags"])
    part = list(skin["part"])
    bone = [None] * len(skin["points"])
    cuts = list(skin["cuts"])
    side = [skin["side"]]
    coord = [skin["coord"]]
    detail = [~skin["pinned"]]
    normal = [numpy.full((len(skin["points"]), 3), numpy.nan)]
    root = [numpy.full((len(skin["points"]), 3), numpy.nan)]
    offset = len(skin["points"])
    for piece in pieces:
        count = len(piece["points"])
        points.append(piece["points"])
        normal.append(piece["normal"] if "normal" in piece else numpy.full((count, 3), numpy.nan))
        root.append(numpy.tile(piece["root"], (count, 1)) if "root" in piece else numpy.full((count, 3), numpy.nan))
        faces.extend(tuple(index + offset for index in face) for face in piece["faces"])
        tags.extend(piece["tags"])
        part.extend([piece["part"]] * count)
        bone.extend([piece["bone"]] * count)
        cuts.extend((a + offset, c + offset) for a, c in piece["cuts"])
        side.append(numpy.sign(piece["points"][:, 0]).astype(numpy.int64))
        coord.append(piece["coord"])
        detail.append(numpy.zeros(count, dtype=bool))
        offset += count
    result = {"points": numpy.vstack(points), "faces": faces, "tags": tags, "part": part, "bone": bone, "cuts": cuts, "side": numpy.concatenate(side), "coord": numpy.vstack(coord), "detail": numpy.concatenate(detail), "skin_count": len(skin["points"])}
    result["normal"] = numpy.vstack(normal)
    roots = numpy.vstack(root)
    anchor = numpy.full(len(roots), -1, dtype=numpy.int64)
    for index in numpy.flatnonzero(~numpy.isnan(roots[:, 0])):
        anchor[index] = int(numpy.argmin(numpy.linalg.norm(skin["points"] - roots[index][None, :], axis=1)))
    result["anchor"] = anchor
    return result
