import math
import numpy
import fauna_hoofed_coats as coats
import fauna_hoofed_field as fields
import fauna_hoofed_paint as paint
import fauna_hoofed_parts as parts
import fauna_hoofed_rig as rigs
import fauna_hoofed_species as species

point = species.point
head_point = species.head_point
smooth = fields.smoothstep
unit = fields.unit


crest_line = [(-0.05, 1.54), (-0.25, 1.555), (-0.4, 1.58), (-0.48, 1.6), (-0.6, 1.628), (-0.72, 1.645), (-0.84, 1.69), (-0.96, 1.755), (-1.08, 1.825), (-1.2, 1.885), (-1.3, 1.925), (-1.4, 1.955), (-1.55, 1.99)]
throat_line = [(-0.7, 0.8), (-0.82, 0.96), (-0.93, 1.13), (-1.01, 1.26), (-1.08, 1.38), (-1.13, 1.48), (-1.17, 1.57), (-1.2, 1.65), (-1.215, 1.72), (-1.235, 1.79), (-1.27, 1.87), (-1.31, 1.95), (-1.36, 2.04)]


def crossing(origin, direction, line):
    line = numpy.asarray(line, dtype=numpy.float64)
    best = None
    for index in range(len(line) - 1):
        a = line[index]
        e = line[index + 1] - a
        matrix = numpy.array([[direction[0], -e[0]], [direction[1], -e[1]]])
        if abs(numpy.linalg.det(matrix)) < 1e-12:
            continue
        w, t = numpy.linalg.solve(matrix, a - origin)
        if -1e-6 <= t <= 1.0 + 1e-6 and w > 0.0 and (best is None or w < best):
            best = float(w)
    return best


def neck_stations(top, base, widths):
    axis = unit(base - top)
    up = numpy.cross(fields.lateral, axis)
    stations = []
    for s, wide, n_up, n_down in widths:
        center = (top + axis * s)[1:]
        above = crossing(center, up[1:], crest_line)
        below = crossing(center, -up[1:], throat_line)
        if below is None:
            half = 0.075
            middle = above - half
        else:
            middle = 0.5 * (above - below)
            half = 0.5 * (above + below)
        stations.append((s, 0.0, middle, wide, half, half, n_up, n_down))
    return stations


def anatomy(f, k):
    rows = [
        (-0.91, 1.36, 1.1, 1.24, 0.05, 2.0, 2.0),
        (-0.88, 1.46, 1.02, 1.22, 0.12, 2.0, 2.0),
        (-0.82, 1.53, 0.96, 1.2, 0.17, 1.9, 2.0),
        (-0.74, 1.585, 0.92, 1.2, 0.2, 1.75, 2.0),
        (-0.64, 1.61, 0.895, 1.2, 0.215, 1.55, 2.05),
        (-0.54, 1.615, 0.885, 1.21, 0.235, 1.55, 2.1),
        (-0.42, 1.59, 0.88, 1.22, 0.255, 1.75, 2.2),
        (-0.28, 1.556, 0.875, 1.23, 0.27, 1.95, 2.3),
        (-0.12, 1.54, 0.872, 1.24, 0.282, 2.1, 2.35),
        (0.04, 1.54, 0.882, 1.25, 0.285, 2.15, 2.35),
        (0.18, 1.552, 0.915, 1.27, 0.278, 2.15, 2.3),
        (0.3, 1.57, 0.985, 1.3, 0.268, 2.15, 2.2),
        (0.42, 1.585, 1.045, 1.32, 0.258, 2.2, 2.1),
        (0.54, 1.58, 1.075, 1.33, 0.246, 2.2, 2.0),
        (0.64, 1.552, 1.095, 1.33, 0.218, 2.1, 2.0),
        (0.72, 1.5, 1.12, 1.32, 0.162, 2.0, 2.0),
        (0.78, 1.44, 1.16, 1.31, 0.096, 2.0, 2.0),
        (0.81, 1.38, 1.22, 1.3, 0.036, 2.0, 2.0),
    ]
    species.torso(f, rows)

    widths = [(-0.14, 0.052, 2.0, 2.0), (-0.07, 0.06, 2.0, 2.0), (0.0, 0.068, 2.0, 2.0), (0.1, 0.078, 2.0, 2.1), (0.18, 0.086, 2.0, 2.2), (0.28, 0.095, 2.0, 2.2), (0.38, 0.106, 2.0, 2.2), (0.48, 0.122, 2.0, 2.2), (0.58, 0.145, 2.0, 2.1), (0.68, 0.172, 1.9, 2.1), (0.78, 0.197, 1.8, 2.0), (0.86, 0.19, 1.8, 2.0)]
    f.loft(k["neck_top"], k["neck_base"] - k["neck_top"], neck_stations(k["neck_top"], k["neck_base"], widths), blend=0.1)
    axis = unit(k["neck_base"] - k["neck_top"])
    crest = numpy.cross(fields.lateral, axis)
    path = [numpy.array([0.0, y, z]) for y, z in crest_line[2:8]]
    f.ridge([p - numpy.array([0.0, 0.0, 0.03]) for p in path], 0.045, 0.008, taper=0.25)
    f.ridge([k["neck_top"] + axis * s - crest * (0.04 + 0.07 * s) + fields.lateral * (0.06 + 0.11 * s) for s in (0.1, 0.28, 0.46, 0.62)], 0.018, -0.0045, taper=0.25)
    f.ridge([k["neck_top"] + axis * s - crest * (0.01 + 0.04 * s) + fields.lateral * (0.066 + 0.12 * s) for s in (0.05, 0.25, 0.45, 0.62)], 0.03, 0.005, taper=0.25)

    skull = [
        (-0.014, 0.0, 0.0, 0.014, 0.012, 0.014, 2.0, 2.0),
        (-0.004, 0.0, 0.0, 0.034, 0.03, 0.034, 2.1, 2.1),
        (0.012, 0.0, 0.0, 0.048, 0.044, 0.048, 2.2, 2.2),
        (0.04, 0.0, 0.002, 0.06, 0.053, 0.06, 2.3, 2.1),
        (0.075, 0.0, 0.004, 0.064, 0.055, 0.062, 2.3, 2.1),
        (0.12, 0.0, 0.006, 0.059, 0.054, 0.06, 2.4, 2.0),
        (0.18, 0.0, 0.008, 0.052, 0.054, 0.062, 2.5, 2.0),
        (0.25, 0.0, 0.01, 0.055, 0.056, 0.074, 2.5, 1.9),
        (0.32, 0.0, 0.014, 0.066, 0.058, 0.085, 2.5, 1.8),
        (0.38, 0.0, 0.018, 0.08, 0.06, 0.102, 2.5, 1.7),
        (0.44, 0.0, 0.02, 0.094, 0.062, 0.125, 2.5, 1.7),
        (0.5, 0.0, 0.018, 0.1, 0.06, 0.155, 2.4, 1.7),
        (0.55, 0.0, 0.015, 0.098, 0.056, 0.16, 2.3, 1.8),
        (0.6, 0.0, 0.012, 0.09, 0.048, 0.14, 2.2, 2.0),
        (0.64, 0.0, 0.01, 0.075, 0.036, 0.1, 2.1, 2.0),
        (0.67, 0.0, 0.01, 0.05, 0.022, 0.05, 2.0, 2.0),
    ]
    f.loft(k["nose"], k["head_axis"], skull, blend=0.05)
    f.ellipsoid(head_point(k, 0.485, -0.085, 0.055), (0.04, 0.1, 0.078), axis=k["head_axis"], blend=0.06)
    f.ridge([head_point(k, 0.29, -0.012, 0.064), head_point(k, 0.36, -0.004, 0.08), head_point(k, 0.43, 0.004, 0.094)], 0.014, 0.006, taper=0.2)
    f.bump(head_point(k, 0.47, -0.085, 0.086), (0.03, 0.075, 0.065), 0.012, axis=k["head_axis"])
    f.bump(head_point(k, 0.455, 0.062, 0.084), (0.024, 0.034, 0.024), 0.009, axis=k["head_axis"])
    f.bump(head_point(k, 0.505, 0.06, 0.072), (0.02, 0.022, 0.02), -0.008, axis=k["head_axis"])
    f.bump(head_point(k, 0.06, 0.016, 0.05), (0.02, 0.032, 0.024), 0.008, axis=k["head_axis"])
    f.bump(head_point(k, 0.06, -0.058, 0.0), (0.03, 0.034, 0.032), 0.009, axis=k["head_axis"])
    f.bump(head_point(k, 0.125, -0.06, 0.0), (0.03, 0.022, 0.024), -0.007, axis=k["head_axis"])
    f.bump(head_point(k, 0.22, -0.045, 0.048), (0.022, 0.05, 0.022), -0.005, axis=k["head_axis"])
    f.ridge([head_point(k, 0.2, -0.07, 0.03), head_point(k, 0.36, -0.115, 0.045), head_point(k, 0.48, -0.16, 0.05)], 0.016, 0.004, taper=0.2)
    f.bump(head_point(k, 0.02, 0.008, 0.026), (0.016, 0.02, 0.016), 0.004, axis=k["head_axis"])

    f.ellipsoid((0.165, -0.68, 1.3), (0.058, 0.23, 0.12), axis=k["shoulder"] - k["scapula"], blend=0.13)
    f.ridge([point(0.2, -0.53, 1.45), point(0.222, -0.63, 1.35), point(0.224, -0.74, 1.25)], 0.035, 0.0025, taper=0.25)
    f.ellipsoid((0.16, -0.56, 1.1), (0.058, 0.15, 0.125), axis=k["elbow"] - k["shoulder"], blend=0.12)
    f.ellipsoid((0.175, -0.8, 1.2), (0.045, 0.05, 0.055), blend=0.07)
    f.ellipsoid((0.085, -0.85, 1.1), (0.08, 0.09, 0.14), blend=0.08, pair=0.07)
    f.ellipsoid((0.16, -0.52, 0.99), (0.05, 0.05, 0.07), blend=0.04)
    f.bump((0.22, -0.46, 1.0), (0.06, 0.06, 0.1), -0.008)
    f.ridge([point(0.0, -0.78, 1.57), point(0.0, -0.58, 1.625), point(0.0, -0.36, 1.585)], 0.06, 0.01, taper=0.3)

    def ribs(query):
        q = (query - numpy.array([0.27, -0.12, 1.2])[None, :]) / numpy.array([0.12, 0.34, 0.24])[None, :]
        mask = numpy.clip(1.0 - numpy.sum(q * q, axis=1), 0.0, 1.0) ** 2
        return 0.0005 * mask * numpy.cos(2.0 * math.pi * (query[:, 1] - 0.45 * (query[:, 2] - 1.2)) / 0.085)

    f.custom(ribs, (0.12, -0.48, 0.94), (0.42, 0.24, 1.46))

    f.ellipsoid((0.12, 0.47, 1.42), (0.14, 0.32, 0.17), blend=0.12)
    f.bump((0.26, 0.28, 1.43), (0.06, 0.1, 0.07), 0.0035)
    f.ellipsoid((0.17, 0.5, 1.16), (0.1, 0.26, 0.24), axis=(0.0, -0.25, -1.0), blend=0.14)
    f.ellipsoid((0.1, 0.73, 1.12), (0.085, 0.1, 0.24), blend=0.1, pair=0.04)
    f.ellipsoid((0.22, 0.38, 0.98), (0.055, 0.06, 0.07), blend=0.05)
    f.bump((0.26, 0.24, 1.36), (0.06, 0.09, 0.08), -0.01)
    f.ridge([point(0.19, 0.62, 1.4), point(0.215, 0.63, 1.2), point(0.2, 0.62, 1.02)], 0.02, -0.004, taper=0.25)

    top = point(0.152, -0.6, 1.07)
    length = float(numpy.linalg.norm(k["carpus"] - top))
    forearm = [
        (0.0, 0.0, 0.0, 0.03, 0.05, 0.04),
        (0.07, 0.0, 0.0, 0.07, 0.12, 0.09),
        (0.15, 0.0, 0.0, 0.077, 0.108, 0.088),
        (0.25, 0.0, 0.0, 0.067, 0.08, 0.072),
        (0.35, 0.0, 0.0, 0.056, 0.06, 0.058),
        (0.45, 0.0, 0.0, 0.047, 0.05, 0.047),
        (length - 0.03, 0.0, 0.0, 0.045, 0.047, 0.045),
        (length, 0.0, 0.0, 0.05, 0.05, 0.05),
        (length + 0.05, 0.0, 0.0, 0.03, 0.03, 0.03),
    ]
    f.loft(top, k["carpus"] - top, forearm, blend=0.05, group="fore")
    f.ellipsoid(k["carpus"] + point(0.0, 0.002, -0.004), (0.052, 0.054, 0.062), blend=0.025, group="fore")
    f.bump(k["carpus"] + point(0.0, 0.048, 0.012), (0.024, 0.024, 0.036), 0.008, group="fore")
    length = float(numpy.linalg.norm(k["fetlock_f"] - k["carpus"]))
    cannon = [
        (0.0, 0.0, 0.0, 0.045, 0.048, 0.042),
        (0.07, 0.0, 0.0, 0.037, 0.046, 0.031),
        (0.16, 0.0, 0.0, 0.034, 0.045, 0.029),
        (0.24, 0.0, 0.0, 0.036, 0.047, 0.03),
        (length, 0.0, 0.0, 0.046, 0.056, 0.038),
    ]
    f.loft(k["carpus"], k["fetlock_f"] - k["carpus"], cannon, blend=0.02, group="fore")
    for offset in (0.026, -0.026):
        f.ridge([k["carpus"] + point(offset, 0.016, -0.07), k["fetlock_f"] + point(offset, 0.016, 0.06)], 0.011, -0.0035, taper=0.2, group="fore")
    f.ellipsoid(k["fetlock_f"] + point(0.0, 0.008, 0.0), (0.046, 0.056, 0.05), blend=0.025, group="fore")
    f.cone(k["fetlock_f"], k["coffin_f"] + point(0.0, -0.004, 0.0), 0.042, 0.05, blend=0.015, group="fore")

    crown = point(0.18, 0.5, 1.12)
    length = float(numpy.linalg.norm(k["hock"] - crown))
    gaskin = [
        (0.0, 0.0, 0.0, 0.05, 0.08, 0.08),
        (0.1, 0.0, 0.0, 0.088, 0.17, 0.17),
        (0.19, 0.0, 0.0, 0.092, 0.17, 0.17),
        (0.28, 0.0, 0.0, 0.088, 0.145, 0.135),
        (0.37, 0.0, 0.0, 0.076, 0.11, 0.09),
        (0.47, 0.0, 0.0, 0.063, 0.08, 0.062),
        (length - 0.04, 0.0, 0.0, 0.056, 0.068, 0.052),
        (length, 0.0, 0.0, 0.056, 0.064, 0.05),
        (length + 0.05, 0.0, 0.0, 0.03, 0.035, 0.03),
    ]
    f.loft(crown, k["hock"] - crown, gaskin, blend=0.06, group="hind")
    f.ridge([point(0.15, 0.75, 0.86), point(0.15, 0.775, 0.72), k["hock_point"] + point(0.0, -0.01, 0.0)], 0.022, 0.008, taper=0.15, group="hind")
    f.ellipsoid(k["hock"] + point(0.0, 0.006, -0.004), (0.055, 0.066, 0.075), blend=0.03, group="hind")
    f.ellipsoid(k["hock_point"] + point(0.0, -0.022, -0.016), (0.022, 0.026, 0.036), blend=0.045, group="hind")
    length = float(numpy.linalg.norm(k["fetlock_h"] - k["hock"]))
    shank = [
        (0.0, 0.0, 0.0, 0.05, 0.06, 0.045),
        (0.08, 0.0, 0.0, 0.04, 0.05, 0.034),
        (0.2, 0.0, 0.0, 0.036, 0.048, 0.031),
        (0.3, 0.0, 0.0, 0.038, 0.049, 0.032),
        (length, 0.0, 0.0, 0.047, 0.057, 0.039),
    ]
    f.loft(k["hock"], k["fetlock_h"] - k["hock"], shank, blend=0.02, group="hind")
    for offset in (0.027, -0.027):
        f.ridge([k["hock"] + point(offset, 0.02, -0.09), k["fetlock_h"] + point(offset, 0.018, 0.06)], 0.011, -0.0035, taper=0.2, group="hind")
    f.ellipsoid(k["fetlock_h"] + point(0.0, 0.008, 0.0), (0.047, 0.057, 0.05), blend=0.025, group="hind")
    f.cone(k["fetlock_h"], k["coffin_h"] + point(0.0, 0.004, 0.0), 0.042, 0.05, blend=0.015, group="hind")

    f.cone(k["tail"], k["tail_tip"], 0.05, 0.03, blend=0.035, group="tail")


def extras(f, k):
    f.ellipsoid(k["eye"], (0.025, 0.025, 0.025), blend=0.0, group="extra")
    ear_axis = unit((0.32, -0.1, 0.94))
    f.ellipsoid(k["ear"] + ear_axis * 0.08, (0.04, 0.085, 0.012), axis=ear_axis, roll=30.0, blend=0.01, group="extra")
    for leg in ("f", "h"):
        f.cone(k["toe_" + leg] + point(0.0, 0.065, 0.0), k["coffin_" + leg] + point(0.0, 0.0, 0.01), 0.064, 0.05, blend=0.0, group="extra")


def build(kind):
    f = fields.field()
    k = {}
    k["withers"] = point(0.0, -0.56, 1.61)
    k["scapula"] = point(0.1, -0.5, 1.47)
    k["shoulder"] = point(0.19, -0.8, 1.19)
    k["elbow"] = point(0.17, -0.6, 0.98)
    k["carpus"] = point(0.152, -0.628, 0.5)
    k["fetlock_f"] = point(0.15, -0.64, 0.2)
    k["coffin_f"] = point(0.15, -0.725, 0.072)
    k["toe_f"] = point(0.15, -0.81, 0.0)
    k["hip"] = point(0.19, 0.5, 1.3)
    k["stifle"] = point(0.22, 0.36, 0.96)
    k["hock"] = point(0.155, 0.69, 0.55)
    k["hock_point"] = point(0.155, 0.78, 0.61)
    k["fetlock_h"] = point(0.15, 0.7, 0.2)
    k["coffin_h"] = point(0.15, 0.61, 0.072)
    k["toe_h"] = point(0.15, 0.53, 0.0)
    k["neck_top"] = point(0.0, -1.24, 1.8)
    k["neck_base"] = point(0.0, -0.74, 1.3)
    k["nose"] = point(0.0, -1.69, 1.39)
    k["occiput"] = point(0.0, -1.33, 1.88)
    k["head_axis"] = unit(k["occiput"] - k["nose"])
    k["head_up"] = numpy.cross(fields.lateral, k["head_axis"])
    k["eye"] = head_point(k, 0.43, 0.04, 0.1)
    k["ear"] = head_point(k, 0.585, 0.065, 0.055)
    k["jaw"] = head_point(k, 0.5, -0.03, 0.08)
    k["mouth"] = head_point(k, 0.125, -0.04, 0.042)
    k["tail"] = point(0.0, 0.8, 1.47)
    k["tail_tip"] = point(0.0, 0.892, 1.24)
    k["hips"] = point(0.0, 0.42, 1.5)
    k["spine_01"] = point(0.0, 0.18, 1.48)
    k["spine_02"] = point(0.0, -0.12, 1.45)
    k["spine_03"] = point(0.0, -0.45, 1.46)
    k["neck_01"] = point(0.0, -0.76, 1.25)
    k["skull"] = point(0.0, -1.3, 1.84)
    k["ribs"] = point(0.25, -0.15, 1.2)
    anatomy(f, k)
    extras(f, k)

    blueprint = {"name": "horse", "rig_name": "horse_rig", "field": f, "marks": k, "scale": 1.0, "zoom": 1.35}
    blueprint["bounds"] = (point(-0.5, -1.9, -0.02), point(0.5, 1.0, 2.2))
    blueprint["extent"] = {"length": 2.8, "height": 2.15, "center": -0.44, "body": 1.75}
    blueprint["islands"] = {"head": 1.6, "nose": 1.9, "chin": 1.6, "mane": 0.34, "forelock": 0.45, "tail_hair": 0.3, "chestnut": 0.6, "hoof_top": 0.15}
    skin = ("core", "fore", "hind", "tail")
    eye_axis = unit((0.88, -0.36, 0.3))
    eye_surface = f.project(numpy.array([head_point(k, 0.43, 0.04, 0.096)]), ("core",))[0]
    ear_root = f.project(numpy.array([head_point(k, 0.585, 0.065, 0.05)]), ("core",))[0]
    k["eye_center"] = eye_surface - eye_axis * (0.025 - 0.004)
    k["ear_root"] = ear_root
    top, found = f.cast(numpy.array([[0.0, -0.24, 1.3]]), numpy.array([[0.0, 0.0, 1.0]]), 0.6, ("core",), steps=240)
    k["saddle"] = point(0.0, -0.24, 1.3 + float(top[0]))
    cage = {"around": 32, "core": ("core",), "skin": skin, "head_station": 9}
    spine = [(0.75, 1.31, 0.0, 0.055), (0.45, 1.33, 0.0, 0.055), (0.1, 1.23, 0.0, 0.055), (-0.3, 1.23, 0.0, 0.055), (-0.6, 1.25, 6.0, 0.05), (-0.74, 1.33, 24.0, 0.045)]
    axis = unit(k["neck_base"] - k["neck_top"])
    up = numpy.cross(fields.lateral, axis)
    tilt = math.degrees(math.atan2(-axis[2], axis[1]))
    for s, spacing in ((0.52, 0.04), (0.38, 0.036), (0.24, 0.032)):
        middle = neck_stations(k["neck_top"], k["neck_base"], [(s, 0.1, 2.0, 2.0)])[0][2]
        center = k["neck_top"] + axis * s + up * middle
        spine.append((float(center[1]), float(center[2]), tilt, spacing))
    pivot = (-1.23, 1.6)
    for angle, spacing in ((34.0, 0.028), (10.0, 0.026), (-16.0, 0.025), (-42.0, 0.025)):
        spine.append((pivot[0] + 0.19 * math.sin(math.radians(angle)), pivot[1] + 0.19 * math.cos(math.radians(angle)), angle, spacing))
    face = math.degrees(math.atan2(-k["head_axis"][2], k["head_axis"][1]))
    for s, v, spacing in ((0.4, -0.04, 0.024), (0.27, -0.005, 0.024), (0.14, 0.0, 0.022), (0.04, 0.0, 0.02)):
        center = head_point(k, s, v)
        spine.append((float(center[1]), float(center[2]), face, spacing))
    cage["spine"] = spine
    cage["pivots"] = [(9, 12, pivot)]
    cage["legs"] = [
        {"name": "fore", "group": "fore", "around": 16, "limit": 1.02, "path": [((0.172, -0.598, 0.86), 3), ((0.165, -0.607, 0.73), 3), ((0.158, -0.617, 0.6), 2), ((0.154, -0.626, 0.53), 1), ((0.153, -0.628, 0.5), 1), ((0.152, -0.63, 0.46), 2), ((0.151, -0.634, 0.35), 2), ((0.15, -0.638, 0.25), 1), ((0.15, -0.64, 0.2), 1), ((0.15, -0.662, 0.15), 1), ((0.15, -0.688, 0.112), 1), ((0.15, -0.708, 0.086), 1), ((0.15, -0.722, 0.062), 0)]},
        {"name": "hind", "group": "hind", "around": 16, "limit": 1.1, "path": [((0.19, 0.53, 0.9), 3), ((0.18, 0.59, 0.78), 2), ((0.168, 0.645, 0.67), 2), ((0.158, 0.682, 0.59), 1), ((0.155, 0.69, 0.55), 1), ((0.153, 0.692, 0.5), 2), ((0.152, 0.695, 0.38), 2), ((0.15, 0.698, 0.26), 1), ((0.15, 0.7, 0.2), 1), ((0.15, 0.678, 0.15), 1), ((0.15, 0.652, 0.112), 1), ((0.15, 0.632, 0.086), 1), ((0.15, 0.618, 0.062), 0)]},
    ]
    cage["eye"] = {"center": k["eye_center"], "axis": eye_axis, "slit": k["head_axis"], "radius": 0.025, "open": (50.0, 30.0), "cells": 2}
    cage["ear"] = {"root": ear_root, "axis": unit((0.32, -0.1, 0.94)), "face": unit((0.5, -0.86, 0.05)), "length": 0.165, "width": 0.088, "around": 12, "cells": (1, 2), "thickness": 0.008, "point": 1.5, "curl": 0.012}
    cage["mouth"] = {"row": 5}
    cage["nostril"] = {"at": head_point(k, 0.072, 0.03, 0.05), "rows": 2, "cols": 2, "depth": 0.035, "round": 0.7, "dive": 0.75}
    cage["tail"] = {"cell": (1, 1), "rows": 2, "around": 8, "flat": 0.85, "path": [(0.0, 0.8, 1.47), (0.0, 0.84, 1.44), (0.0, 0.875, 1.36), (0.0, 0.892, 1.24)], "radii": [0.05, 0.046, 0.038, 0.03]}
    blueprint["cage"] = cage
    blueprint["hoof"] = {"length": 0.13, "width": 0.124, "toe_height": 0.088, "heel_height": 0.046, "slope": 0.78, "heel_slope": 0.55}
    dock = [numpy.array(p) for p in cage["tail"]["path"]]
    hang = [point(0.0, 0.9, 1.02), point(0.0, 0.905, 0.79)]
    blueprint["bones"] = rigs.quadruped(k, dock + hang, [("saddle", "spine_02", tuple(k["saddle"]))])
    blueprint["saddle"] = {"bone": "saddle", "parent": "spine_02", "position": k["saddle"]}
    chain = ["tail_%02d" % (index + 1) for index in range(6)]
    blueprint["rig"] = {
        "axial": ["hips", "spine_01", "spine_02", "spine_03", "neck_01", "neck_02", "neck_03", "head"],
        "axial_widths": [0.0, 0.16, 0.22, 0.22, 0.22, 0.16, 0.16, 0.12],
        "limbs": [
            {"name": "fore", "bones": ["scapula", "humerus", "radius", "cannon", "pastern_f", "hoof_f"], "tip": k["toe_f"], "widths": [0.0, 0.16, 0.12, 0.07, 0.05, 0.035], "reach": [0.25, 0.22, 0.16, 0.09, 0.07, 0.07], "grip": [0.55, 0.85, 1.0, 1.0, 1.0, 1.0]},
            {"name": "hind", "bones": ["femur", "tibia", "metatarsus", "pastern_h", "hoof_h"], "tip": k["toe_h"], "widths": [0.0, 0.18, 0.08, 0.05, 0.035], "reach": [0.28, 0.24, 0.11, 0.07, 0.07], "grip": [0.75, 1.0, 1.0, 1.0, 1.0], "mass": (1.12, 1.42, (0.18, 0.36), (0.82, 0.92), 0.82)},
        ],
        "ribs": {"center": (0.25, -0.1, 1.2), "radii": (0.2, 0.42, 0.3), "amount": 0.55},
        "tail": chain[:3],
        "tail_tip": dock[3],
        "tail_widths": [0.0, 0.05, 0.05],
        "extra": [hair_weights(chain, dock + hang + [point(0.0, 0.905, 0.48)])],
    }
    blueprint["facts"] = {"mass": 500.0, "hull": {"center": (0.0, -0.04, 1.24), "half_length": 0.54, "radius": 0.34}}
    blueprint["motion"] = {
        "prefix": "horse_",
        "nose": k["nose"],
        "skull": k["skull"],
        "breath": 0.012,
        "chew": 2.0,
        "joint_radius": (0.085, 0.05, 0.045, 0.042),
        "graze_height": 0.03,
        "graze_tilt": 6.0,
        "graze_drop": -0.04,
        "graze_head": 60.0,
        "graze_step": 0.22,
        "graze_chew": 6.0,
        "alert_neck": 16.0,
        "alert_tail": 8.0,
        "tail_hang": 3,
        "gaits": ("walk", "trot", "canter", "gallop"),
        "lies": False,
        "walk": {"kind": "walk", "frames": 32, "speed": 1.7, "duty": {"fore": 0.62, "hind": 0.62}, "phase": {"hind_l": 0.0, "fore_l": 0.25, "hind_r": 0.5, "fore_r": 0.75}, "center": {"fore": (0.0, 0.0, 0.0), "hind": (0.0, -0.02, 0.0)}, "narrow": 0.82, "lift": {"fore": 0.11, "hind": 0.09}, "toe": {"fore": 0.75, "hind": 0.55}, "curl": {"fore": 0.55, "hind": 0.42}, "swing_flex": {"fore": 0.95, "hind": 0.5}, "stance_flex": {"fore": 0.0, "hind": 0.06}, "sink": 0.14, "follow": 0.35, "bob": 0.016, "sway": 0.02, "roll": 1.8, "yaw": 2.6, "nod": 4.5, "tail": 5.0},
        "trot": {"kind": "trot", "frames": 20, "speed": 3.8, "duty": {"fore": 0.42, "hind": 0.42}, "phase": {"hind_l": 0.0, "fore_r": 0.0, "hind_r": 0.5, "fore_l": 0.5}, "center": {"fore": (0.0, -0.02, 0.0), "hind": (0.0, -0.04, 0.0)}, "narrow": 0.72, "lift": {"fore": 0.19, "hind": 0.15}, "toe": {"fore": 0.95, "hind": 0.7}, "curl": {"fore": 0.8, "hind": 0.6}, "swing_flex": {"fore": 1.45, "hind": 0.8}, "stance_flex": {"fore": 0.0, "hind": 0.1}, "sink": 0.22, "follow": 0.45, "bob": 0.035, "roll": 1.2, "yaw": 1.5, "nod": 1.8, "carry": -4.0},
        "canter": {"kind": "gallop", "frames": 17, "speed": 6.5, "duty": {"fore": 0.36, "hind": 0.36}, "phase": {"hind_l": 0.0, "hind_r": 0.2, "fore_l": 0.24, "fore_r": 0.44}, "center": {"fore": (0.0, -0.04, 0.0), "hind": (0.0, -0.1, 0.0)}, "narrow": 0.62, "lift": {"fore": 0.2, "hind": 0.17}, "toe": {"fore": 1.0, "hind": 0.75}, "curl": {"fore": 0.85, "hind": 0.65}, "swing_flex": {"fore": 1.7, "hind": 0.95}, "stance_flex": {"fore": 0.0, "hind": 0.14}, "sink": 0.26, "follow": 0.55, "bob": 0.05, "roll": 1.2, "flex": 7.0, "nod": 7.0, "hover": -0.02, "carry": -8.0, "flag": 22.0, "gather": 0.85},
        "gallop": {"kind": "gallop", "frames": 14, "speed": 13.0, "duty": {"fore": 0.22, "hind": 0.22}, "phase": {"hind_l": 0.0, "hind_r": 0.1, "fore_l": 0.36, "fore_r": 0.46}, "center": {"fore": (0.0, -0.06, 0.0), "hind": (0.0, -0.16, 0.0)}, "narrow": 0.55, "lift": {"fore": 0.26, "hind": 0.24}, "toe": {"fore": 1.0, "hind": 0.8}, "curl": {"fore": 0.95, "hind": 0.75}, "swing_flex": {"fore": 1.95, "hind": 1.1}, "stance_flex": {"fore": 0.0, "hind": 0.16}, "sink": 0.3, "follow": 0.62, "bob": 0.06, "roll": 1.2, "flex": 11.0, "nod": 6.0, "hover": -0.03, "carry": -12.0, "flag": 34.0},
        "rear": {"seconds": 3.0, "pitch": 40.0, "sink": -0.18, "back": 0.1, "hock": 0.45, "arch": 6.0, "peak": 1.1, "land": 2.45, "paw": 0.55, "tuck": (-8.0, -22.0, -42.0, 105.0, 35.0, 15.0), "neck": -34.0, "head": 18.0, "toss": 9.0, "jaw": 10.0, "ears": 22.0, "tail": 50.0, "land_flex": 0.25, "rise": [(0.0, 0.0), (0.35, 0.06), (0.8, 0.55), (1.1, 1.0), (1.55, 1.03), (1.9, 0.92), (2.3, 0.28), (2.45, 0.0), (2.62, -0.04), (3.0, 0.0)], "air": [(0.0, 0.0), (0.5, 0.0), (0.85, 1.0), (2.15, 1.0), (2.43, 0.0), (3.0, 0.0)]},
        "rest": {"hips": -0.66, "pitch": 4.5, "fore": (0.0, 0.0, -70.0, 155.0, 20.0, 0.0), "hind": (-46.0, 53.0, -91.0, 16.0, 0.0), "neck": -8.0, "head": 4.0},
        "death": {"side": 0.42, "drop": -1.2, "neck": -40.0, "head": 16.0, "neck_yaw": -12.0, "head_yaw": 0.0, "head_roll": -24.0, "droop": 18.0, "fore_upper": (0.0, 5.0, -12.0, 38.0, 20.0, 10.0), "fore_lower": (0.0, 0.0, -6.0, 24.0, 15.0, 8.0), "hind_upper": (-14.0, 24.0, -18.0, 15.0, 8.0), "hind_lower": (-8.0, 14.0, -10.0, 12.0, 6.0)},
    }
    return blueprint


def hair_weights(names, joints):
    widths = [0.0] + [0.08] * (len(names) - 1)

    def apply(result, slot, points, part, coord, model):
        hair = part == "tail_hair"
        if not hair.any():
            return result
        weights, travel, distance = rigs.chain(points[hair], joints, widths)
        result[hair] = 0.0
        block = result[hair]
        for index, name in enumerate(names):
            block[:, slot[name]] = weights[:, index]
        result[hair] = block
        return result

    return apply


def drape(f, groups, start, heading, steps, step, gap, fall, rng, wander=0.0, cling=0.0, hold=1):
    p = numpy.asarray(start, dtype=numpy.float64).copy()
    points = [p.copy()]
    direction = unit(heading)
    for index in range(steps):
        direction = unit(direction + numpy.asarray(fall) + (rng.random(3) - 0.5) * wander)
        previous = p.copy()
        p = p + direction * step
        value, gradient = f.sample(p[None, :], groups)
        if value[0] < gap:
            p = p + unit(gradient[0]) * (gap - value[0])
        elif cling > 0.0 and index >= hold:
            p = p - unit(gradient[0]) * (value[0] - gap) * cling
        direction = unit(p - previous)
        points.append(p.copy())
    return numpy.array(points)


def strand(path, normals, widths, thick, tag, part, root=None, mark=0.0, follow=False):
    path = numpy.asarray(path, dtype=numpy.float64)
    count = len(path)
    tangent = numpy.gradient(path, axis=0)
    tangent /= numpy.maximum(numpy.linalg.norm(tangent, axis=1), 1e-9)[:, None]
    points = []
    shading = []
    coord = []
    for index in range(count):
        out = numpy.asarray(normals[index], dtype=numpy.float64)
        out = unit(out - tangent[index] * float(out @ tangent[index]))
        side = unit(numpy.cross(tangent[index], out))
        half = widths[index] * 0.5
        points.extend([path[index] + side * half - out * thick[index] * 0.3, path[index] - side * half - out * thick[index] * 0.3, path[index] + out * thick[index] * 0.7])
        shading.extend([unit(out + side * 0.5), unit(out - side * 0.5), out])
        t = index / (count - 1.0)
        coord.extend([(t, mark)] * 3)
    points.append(path[-1] + tangent[-1] * widths[-1])
    shading.append(unit(numpy.asarray(normals[-1], dtype=numpy.float64)))
    coord.append((1.0, mark))
    faces = []
    for index in range(count - 1):
        a = index * 3
        b = a + 3
        faces.extend([(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b, a)])
    last = (count - 1) * 3
    tip = len(points) - 1
    faces.extend([(last, tip, last + 1), (last + 1, tip, last + 2), (last + 2, tip, last), (0, 1, 2)])
    cuts = [(index * 3, index * 3 + 3) for index in range(count - 1)] + [(last, tip)]
    piece = parts.shell(points, faces, [tag] * len(faces), None, part, cuts, coord)
    piece["normal"] = numpy.array(shading)
    if follow:
        piece["root"] = piece["points"].copy()
    elif root is not None:
        piece["root"] = numpy.asarray(root, dtype=numpy.float64)
    return piece


def mane(blueprint):
    k = blueprint["marks"]
    f = blueprint["field"]
    groups = blueprint["cage"]["skin"]
    rng = numpy.random.default_rng(17)
    axis = unit(k["neck_base"] - k["neck_top"])
    crest = numpy.cross(fields.lateral, axis)
    result = []
    tops = []
    for s in numpy.linspace(-0.13, 0.6, 22):
        origin = k["neck_top"] + axis * s
        distance, found = f.cast(origin[None, :], crest[None, :], 0.5, groups, steps=200)
        if found[0]:
            tops.append(origin + crest * float(distance[0]))
    tops = numpy.array(tops)
    lift = f.normals(tops, groups)
    ridge = tops + lift * 0.004 - fields.lateral * 0.006
    span = numpy.linspace(0.0, 1.0, len(ridge))
    piece = parts.sweep(ridge, 0.016 + 0.014 * numpy.sin(math.pi * span) ** 0.6, 8, "mane", None, "mane", flat=0.6, up=lift[0], mark=0.5)
    piece["root"] = piece["points"].copy()
    result.append(piece)
    for layer, (gap, reach, count) in enumerate(((0.006, 0.82, 28), (0.016, 1.0, 28))):
        for index in range(count):
            u = (index + 0.5 * layer + 0.3 * rng.random()) / count
            origin = k["neck_top"] + axis * (-0.14 + 0.76 * u)
            ray = unit(crest + fields.lateral * (0.015 - 0.18 * layer))
            distance, found = f.cast(origin[None, :], ray[None, :], 0.5, groups, steps=200)
            if not found[0]:
                continue
            root = origin + ray * float(distance[0])
            normal = f.normals(root[None, :], groups)[0]
            body = math.sin(math.pi * min(max((u - 0.03) / 0.94, 0.0), 1.0)) ** 0.5
            length = (0.1 + 0.17 * body) * reach * (0.85 + 0.3 * rng.random())
            heading = unit(normal * (0.45 - 0.15 * layer) - fields.lateral * 0.85 + axis * 0.1)
            path = drape(f, groups, root - normal * 0.004, heading, 7, length / 7.0, gap, (0.0, 0.0, -0.4), rng, 0.05, 0.9, 1)
            shade = f.normals(path, groups)
            widths = numpy.linspace(0.054 - 0.008 * layer, 0.016, len(path)) * (0.85 + 0.3 * rng.random())
            thick = numpy.linspace(0.012, 0.004, len(path))
            result.append(strand(path, shade, widths, thick, "mane", "mane", root, rng.random(), True))
    for index in range(9):
        x = (index / 8.0 - 0.5) * 0.05
        origin = head_point(k, 0.585, 0.0, x)
        ray = unit(k["head_up"] * 0.85 + k["head_axis"] * 0.5)
        distance, found = f.cast(origin[None, :], ray[None, :], 0.3, groups, steps=200)
        if not found[0]:
            continue
        root = origin + ray * float(distance[0])
        normal = f.normals(root[None, :], groups)[0]
        length = (0.17 + 0.06 * rng.random()) * (1.0 - 0.25 * abs(x) / 0.025)
        heading = unit(-k["head_axis"] * 0.8 + normal * 0.35 - fields.lateral * x * 1.5)
        path = drape(f, groups, root - normal * 0.004, heading, 5, length / 5.0, 0.007, -k["head_axis"] * 0.06 + numpy.array([0.0, 0.0, -0.08]), rng, 0.04, 0.5)
        shade = f.normals(path, groups)
        widths = numpy.linspace(0.036, 0.012, len(path)) * (0.85 + 0.3 * rng.random())
        thick = numpy.linspace(0.01, 0.004, len(path))
        result.append(strand(path, shade, widths, thick, "forelock", "mane", root, rng.random(), True))
    return result


def tail_hair(blueprint):
    f = blueprint["field"]
    groups = blueprint["cage"]["skin"]
    dock = numpy.array(blueprint["cage"]["tail"]["path"], dtype=numpy.float64)
    radii = blueprint["cage"]["tail"]["radii"]
    rng = numpy.random.default_rng(23)
    lengths = numpy.r_[0.0, numpy.cumsum(numpy.linalg.norm(numpy.diff(dock, axis=0), axis=1))]
    core = numpy.vstack([dock, [(0.0, 0.902, 1.1), (0.0, 0.908, 0.92), (0.0, 0.908, 0.74), (0.0, 0.905, 0.6)]])
    result = [parts.sweep(core, [0.046, 0.048, 0.046, 0.046, 0.054, 0.06, 0.058, 0.042], 10, "tail_hair", None, "tail_hair", flat=0.72, up=(0.0, 1.0, 0.0), mark=0.5)]
    for row in range(8):
        u = (0.03 + 0.9 * row / 7.0) * lengths[-1]
        segment = min(int(numpy.searchsorted(lengths, u, side='right')) - 1, len(dock) - 2)
        t = (u - lengths[segment]) / (lengths[segment + 1] - lengths[segment])
        center = dock[segment] + (dock[segment + 1] - dock[segment]) * t
        radius = radii[segment] + (radii[segment + 1] - radii[segment]) * t
        along = unit(dock[segment + 1] - dock[segment])
        back = unit(numpy.cross(fields.lateral, along))
        for column in range(8):
            angle = math.radians(-120.0 + 240.0 * (column + 0.5 * (row % 2) + 0.25 * rng.random()) / 8.0)
            out = back * math.cos(angle) + fields.lateral * math.sin(angle)
            root = center + out * radius * 0.8
            bottom = 0.42 + 0.16 * rng.random() * (0.5 + 0.5 * abs(math.sin(angle)))
            length = (root[2] - bottom) * 1.04
            heading = unit(along + out * 0.2)
            spread = fields.lateral * math.sin(angle) * 0.004 + numpy.array([0.0, 0.004, -0.24])
            path = drape(f, groups, root, heading, 8, length / 8.0, 0.008, spread, rng, 0.05)
            axis_y = 0.9 + 0.01 * smooth(1.2, 0.6, path[:, 2])
            shade = numpy.column_stack([path[:, 0] * 1.3, path[:, 1] - axis_y, numpy.zeros(len(path))]) + out[None, :] * 0.015
            widths = numpy.linspace(0.052, 0.012, len(path)) * (0.85 + 0.3 * rng.random())
            thick = numpy.linspace(0.012, 0.005, len(path))
            result.append(strand(path, shade, widths, thick, "tail_hair", "tail_hair", None, rng.random()))
    return result


def hoof(toe, spec, bone):
    count = 20
    levels = (0.0, 0.3, 0.65, 1.0)
    length = spec["length"]
    width = spec["width"]
    middle = float(toe[1]) + length * 0.5
    points = []
    for level in levels:
        for index in range(count):
            phi = 2.0 * math.pi * index / count
            front = 0.5 + 0.5 * math.cos(phi)
            height = level * (spec["heel_height"] + (spec["toe_height"] - spec["heel_height"]) * front)
            x = float(toe[0]) + math.sin(phi) * width * 0.5 * (1.0 - 0.18 * level) * (1.0 - 0.14 * (1.0 - front) ** 2)
            y = middle - math.cos(phi) * length * 0.5 * (1.0 - 0.06 * level) + height * (spec["slope"] * front + spec["heel_slope"] * (1.0 - front))
            points.append((x, y, height))
    faces = []
    tags = []
    for level in range(len(levels) - 1):
        for index in range(count):
            a = level * count + index
            c = level * count + (index + 1) % count
            faces.append((a, c, c + count, a + count))
            tags.append("hoof")
    base = numpy.array(points[:count]).mean(axis=0)
    points.append((base[0], base[1], 0.005))
    for index in range(count):
        faces.append((index, (index + 1) % count, len(points) - 1))
        tags.append("hoof_sole")
    rim = (len(levels) - 1) * count
    crown = numpy.array(points[rim:rim + count]).mean(axis=0)
    points.append((crown[0], crown[1], crown[2] + 0.02))
    for index in range(count):
        faces.append((rim + index, rim + (index + 1) % count, len(points) - 1))
        tags.append("hoof_top")
    cuts = [(level * count + count // 2, (level + 1) * count + count // 2) for level in range(len(levels) - 1)]
    return parts.shell(points, faces, tags, bone, "hoof", cuts)


def pad(f, groups, guess, size, height, bone):
    center = f.project(numpy.array([guess]), groups)[0]
    normal = f.normals(center[None, :], groups)[0]
    up = unit(numpy.array([0.0, 0.0, 1.0]) - normal * normal[2])
    side = numpy.cross(normal, up)
    ring = 10
    points = []
    for scale, lift in ((1.0, -0.003), (0.78, height * 0.7), (0.4, height)):
        for index in range(ring):
            a = 2.0 * math.pi * index / ring
            points.append(center + up * (math.cos(a) * size[0] * scale) + side * (math.sin(a) * size[1] * scale) + normal * lift)
    points.append(center + normal * height * 1.08)
    faces = []
    for level in range(2):
        for index in range(ring):
            a = level * ring + index
            c = level * ring + (index + 1) % ring
            faces.append((a, c, c + ring, a + ring))
    for index in range(ring):
        faces.append((2 * ring + index, 2 * ring + (index + 1) % ring, len(points) - 1))
    return parts.shell(points, faces, ["chestnut"] * len(faces), bone, "chestnut", [(0, ring), (ring, 2 * ring)])


def pieces(blueprint):
    k = blueprint["marks"]
    f = blueprint["field"]
    result = [parts.eyeball(blueprint["cage"]["eye"])]
    result.append(parts.mirrored(result[0]))
    for leg, bone in (("f", "hoof_f"), ("h", "hoof_h")):
        piece = hoof(k["toe_" + leg], blueprint["hoof"], bone + "_l")
        result.extend([piece, parts.mirrored(piece, bone + "_r")])
    horn = [
        (("fore",), k["carpus"] + point(-0.05, 0.004, 0.12), (0.026, 0.017), 0.007, "radius"),
        (("hind",), k["hock"] + point(-0.052, -0.012, -0.075), (0.022, 0.014), 0.006, "metatarsus"),
        (("fore",), k["fetlock_f"] + point(0.0, 0.05, -0.03), (0.01, 0.01), 0.007, "pastern_f"),
        (("hind",), k["fetlock_h"] + point(0.0, 0.05, -0.03), (0.01, 0.01), 0.007, "pastern_h"),
    ]
    for groups, guess, size, height, bone in horn:
        piece = pad(f, groups, guess, size, height, bone + "_l")
        result.extend([piece, parts.mirrored(piece, bone + "_r")])
    result.extend(mane(blueprint))
    result.extend(tail_hair(blueprint))
    return result


def coat(c, m):
    k = m.k
    p = m.p
    n = m.n
    count = m.count
    hair = c.tagged("mane", "forelock", "tail_hair")
    forelock = c.tagged("forelock")
    horn = c.tagged("chestnut")
    flow = m.flow(body=(0.0, 1.0, -0.22), legs=(0.0, 0.04, -1.0), neck_start=-0.62, neck_end=-0.8)
    flow[hair] = numpy.array([0.0, 0.08, -1.0])
    flow[forelock] = -k["head_axis"]
    fine = c.fur(flow, 0.0024, 0.001, 12, 1)
    coarse = c.fur(flow, 0.0065, 0.0022, 14, 2)
    fibre = c.fur(flow, 0.0012, 0.003, 18, 3)
    fur = fine * 0.6 + coarse * 0.4
    mottle = paint.fbm(p, 0.14, 3, 11)
    patch = paint.fbm(p, 0.035, 3, 12)
    coated = (m.furry & ~hair & ~horn).astype(numpy.float64)

    color = numpy.tile(numpy.array([0.37, 0.175, 0.085]), (count, 1))
    color = coats.tint(color, (0.43, 0.215, 0.105), smooth(0.4, 0.78, mottle) * 0.45)
    up = n[:, 2]
    trunk = (m.body | m.rump | m.tail).astype(numpy.float64) * coated
    dorsal = numpy.exp(-(p[:, 0] / 0.11) ** 2) * smooth(0.25, 0.9, up) * trunk
    color = coats.tint(color, (0.2, 0.09, 0.045), dorsal * 0.5)
    color = coats.tint(color, (0.29, 0.135, 0.065), smooth(0.2, 0.9, up) * trunk * 0.25)
    under = smooth(-0.15, -0.85, up + (mottle - 0.5) * 0.3) * (m.body | m.rump)
    color = coats.tint(color, (0.45, 0.255, 0.145), under * 0.3)
    rings = paint.fbm(p, 0.06, 2, 31)
    dapple = smooth(0.52, 0.6, rings) * smooth(0.72, 0.62, rings) * smooth(1.2, 1.4, p[:, 2]) * trunk
    color = coats.tint(color, color * 1.14, dapple * 0.5)

    black = numpy.array([0.042, 0.036, 0.034])
    edge = (patch - 0.5) * 0.07
    back = smooth(-0.2, 0.7, n[:, 1])
    fore_points = m.fore * smooth(0.68, 0.52, p[:, 2] - 0.06 * back + edge)
    hind_points = m.hind * smooth(0.78, 0.6, p[:, 2] - 0.07 * back + edge)
    points = numpy.maximum(fore_points, hind_points)
    color = coats.tint(color, black, points)

    face = m.head.astype(numpy.float64)
    muzzle = smooth(0.165, 0.06, m.along + (patch - 0.5) * 0.02) * face
    color = coats.tint(color, (0.075, 0.05, 0.042), muzzle * 0.85)
    lips = smooth(0.08, 0.02, m.along) * face
    color = coats.tint(color, (0.05, 0.042, 0.04), lips * 0.6)
    front = smooth(0.2, 0.8, n @ k["head_up"]) * face * smooth(0.12, 0.3, m.along)
    color = coats.tint(color, (0.25, 0.115, 0.055), front * 0.35)
    eye_ring = smooth(0.045, 0.028, m.eye_distance) * face
    color = coats.tint(color, (0.16, 0.08, 0.045), eye_ring * 0.4)
    star = smooth(0.03, 0.019, numpy.linalg.norm(m.mirrored - head_point(k, 0.47, 0.08, 0.0)[None, :], axis=1) + (patch - 0.5) * 0.016) * face
    color = coats.tint(color, (0.86, 0.84, 0.8), star)

    color[m.ears] = color[m.ears] * 0.82
    rim = m.ears * smooth(0.5, 0.92, m.ear_along)
    color = coats.tint(color, black, rim * 0.85)
    color = coats.tint(color, (0.22, 0.2, 0.19), m.ear_inner * smooth(0.12, 0.4, m.ear_along) * 0.55)

    color = coats.tint(color, black, m.tail * 0.9)
    line = numpy.asarray(crest_line[3:10], dtype=numpy.float64)
    reach = numpy.full(count, 9.0)
    for index in range(len(line) - 1):
        a = line[index]
        e = line[index + 1] - a
        t = numpy.clip(((p[:, 1:] - a[None, :]) @ e) / float(e @ e), 0.0, 1.0)
        reach = numpy.minimum(reach, numpy.linalg.norm(p[:, 1:] - a[None, :] - t[:, None] * e[None, :], axis=1))
    neckline = smooth(-0.55, -0.7, p[:, 1]) * smooth(-1.42, -1.3, p[:, 1]) * coated
    crown = smooth(0.05, 0.025, reach + (patch - 0.5) * 0.02) * neckline
    curtain = smooth(0.17, 0.1, reach + (patch - 0.5) * 0.04) * smooth(0.02, -0.03, p[:, 0]) * neckline
    color = coats.tint(color, black, numpy.maximum(crown, curtain) * 0.92)

    shade = 0.84 + 0.28 * fur + (mottle - 0.5) * 0.08
    color = numpy.where(coated[:, None] > 0.5, color * shade[:, None], color)
    gleam = smooth(0.6, 0.9, fine) * coated * (1.0 - points) * (1.0 - muzzle)
    color = coats.tint(color, color * 1.18 + 0.01, gleam * 0.3)

    sun = smooth(0.35, 1.0, c.coord[:, 0]) * (0.25 + 0.75 * c.coord[:, 1])
    strands = numpy.array([0.03, 0.026, 0.025])[None, :] + numpy.array([0.075, 0.045, 0.028])[None, :] * sun[:, None]
    strands = strands * (0.5 + 0.95 * fibre)[:, None]
    color[hair] = strands[hair]

    rough = numpy.full(count, 0.62)
    rough[coated > 0.5] = (0.53 + 0.17 * (1.0 - fur))[coated > 0.5]
    rough = rough + 0.04 * points
    rough = rough + (0.55 - rough) * muzzle
    rough[hair] = (0.36 + 0.24 * (1.0 - fibre))[hair]
    relief = numpy.full(count, 0.0009)
    relief[m.head] = 0.0006
    relief[m.legs] = 0.0007
    relief[m.ears] = 0.0005
    relief = relief * (1.0 - 0.6 * muzzle)
    relief[hair] = 0.0018
    height = numpy.where(hair, fibre, fur)

    m.cavity(color, rough, relief, flesh=(0.32, 0.15, 0.14), dark=(0.025, 0.018, 0.018), lip=(0.055, 0.042, 0.04))
    m.keratin(color, rough, relief, wall=(0.065, 0.06, 0.055), wear=(0.17, 0.155, 0.135), under=(0.2, 0.18, 0.15))
    cap = c.tagged("hoof_top")
    color[cap] = black * 0.9
    rough[cap] = 0.85
    relief[cap] = 0.0
    grain = paint.fbm(p * numpy.array([1.0, 1.0, 5.0])[None, :], 0.01, 3, 41)
    color[horn] = (numpy.array([0.11, 0.1, 0.092])[None, :] * (0.75 + 0.5 * grain)[:, None])[horn]
    rough[horn] = 0.66
    relief[horn] = 0.0004
    m.eyes(color, rough, relief, iris=(0.09, 0.055, 0.03), wide=0.62, tall=0.32, skin=(0.04, 0.035, 0.034))
    return {"color": numpy.clip(color, 0.0, 1.0), "rough": numpy.clip(rough, 0.04, 1.0), "height": height, "relief": relief}
