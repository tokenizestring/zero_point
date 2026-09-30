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
    return {"points": piece["points"] * flip[None, :], "faces": [tuple(reversed(face)) for face in piece["faces"]], "tags": list(piece["tags"]), "bone": bone or piece["bone"], "part": piece["part"], "cuts": list(piece["cuts"]), "coord": piece["coord"].copy()}


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
    offset = len(skin["points"])
    for piece in pieces:
        count = len(piece["points"])
        points.append(piece["points"])
        faces.extend(tuple(index + offset for index in face) for face in piece["faces"])
        tags.extend(piece["tags"])
        part.extend([piece["part"]] * count)
        bone.extend([piece["bone"]] * count)
        cuts.extend((a + offset, c + offset) for a, c in piece["cuts"])
        side.append(numpy.sign(piece["points"][:, 0]).astype(numpy.int64))
        coord.append(piece["coord"])
        detail.append(numpy.zeros(count, dtype=bool))
        offset += count
    return {"points": numpy.vstack(points), "faces": faces, "tags": tags, "part": part, "bone": bone, "cuts": cuts, "side": numpy.concatenate(side), "coord": numpy.vstack(coord), "detail": numpy.concatenate(detail), "skin_count": len(skin["points"])}
