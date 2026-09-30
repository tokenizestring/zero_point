import math
import numpy
import fauna_hoofed_field as fields
import fauna_hoofed_parts as parts


def torso(f, rows, blend=0.0, group="core"):
    stations = [(y, 0.0, wide, w, top - wide, wide - bottom, nu, nd) for y, top, bottom, wide, w, nu, nd in rows]
    return f.loft((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), stations, blend=blend, group=group)


def along(a, b, t):
    a = numpy.asarray(a, dtype=numpy.float64)
    b = numpy.asarray(b, dtype=numpy.float64)
    return a + (b - a) * t


def head_point(k, s, v, x=0.0):
    return k["nose"] + k["head_axis"] * s + k["head_up"] * v + numpy.array([x, 0.0, 0.0])


def deer(kind):
    stag = kind == "stag"
    f = fields.field()
    k = {}
    k["withers"] = numpy.array([0.0, -0.375, 1.2])
    k["scapula"] = numpy.array([0.055, -0.345, 1.11])
    k["shoulder"] = numpy.array([0.115, -0.55, 0.875])
    k["elbow"] = numpy.array([0.105, -0.36, 0.705])
    k["carpus"] = numpy.array([0.088, -0.42, 0.405])
    k["fetlock_f"] = numpy.array([0.088, -0.427, 0.125])
    k["coffin_f"] = numpy.array([0.088, -0.453, 0.055])
    k["toe_f"] = numpy.array([0.088, -0.51, 0.0])
    k["hip"] = numpy.array([0.1, 0.43, 1.015])
    k["stifle"] = numpy.array([0.125, 0.26, 0.72])
    k["hock"] = numpy.array([0.1, 0.53, 0.465])
    k["hock_point"] = numpy.array([0.1, 0.59, 0.515])
    k["fetlock_h"] = numpy.array([0.095, 0.515, 0.125])
    k["coffin_h"] = numpy.array([0.095, 0.487, 0.055])
    k["toe_h"] = numpy.array([0.095, 0.43, 0.0])
    k["neck_top"] = numpy.array([0.0, -0.79, 1.44])
    k["neck_base"] = numpy.array([0.0, -0.45, 0.97])
    k["nose"] = numpy.array([0.0, -1.155, 1.315])
    k["occiput"] = numpy.array([0.0, -0.77, 1.515])
    k["head_axis"] = fields.unit(k["occiput"] - k["nose"])
    k["head_up"] = numpy.cross(fields.lateral, k["head_axis"])
    k["eye"] = head_point(k, 0.245, 0.035, 0.07)
    k["ear"] = head_point(k, 0.385, 0.055, 0.062)
    k["pedicle"] = head_point(k, 0.33, 0.068, 0.045)
    k["jaw"] = head_point(k, 0.35, -0.01, 0.06)
    k["mouth"] = head_point(k, 0.105, -0.018, 0.036)
    k["nostril"] = head_point(k, 0.012, 0.004, 0.017)
    k["tail"] = numpy.array([0.0, 0.655, 1.07])
    k["tail_tip"] = numpy.array([0.0, 0.705, 0.92])

    rows = [
        (-0.6, 1.06, 0.86, 0.95, 0.075, 2.0, 2.0),
        (-0.52, 1.16, 0.74, 0.92, 0.125, 1.9, 2.0),
        (-0.43, 1.205, 0.675, 0.9, 0.155, 1.7, 1.9),
        (-0.33, 1.2, 0.665, 0.9, 0.175, 1.8, 2.0),
        (-0.19, 1.18, 0.675, 0.9, 0.2, 2.0, 2.2),
        (-0.05, 1.168, 0.7, 0.91, 0.208, 2.1, 2.3),
        (0.1, 1.175, 0.735, 0.93, 0.2, 2.1, 2.3),
        (0.24, 1.2, 0.78, 0.97, 0.185, 2.1, 2.2),
        (0.38, 1.22, 0.79, 1.0, 0.185, 2.2, 2.1),
        (0.5, 1.19, 0.78, 0.99, 0.17, 2.2, 2.0),
        (0.6, 1.13, 0.8, 0.97, 0.13, 2.1, 2.0),
        (0.655, 1.07, 0.85, 0.96, 0.08, 2.0, 2.0),
        (0.675, 1.02, 0.9, 0.96, 0.035, 2.0, 2.0),
    ]
    torso(f, rows)

    mane = 1.0 if stag else 0.0
    slim = 1.0 if stag else 0.84
    neck = [
        (0.0, 0.0, 0.0, 0.062, 0.085, 0.08),
        (0.1, 0.0, 0.0, (0.066 + 0.006 * mane) * slim, 0.09, (0.088 + 0.012 * mane) * slim),
        (0.22, 0.0, 0.0, (0.076 + 0.012 * mane) * slim, 0.1, (0.105 + 0.025 * mane) * slim),
        (0.34, 0.0, 0.0, (0.092 + 0.013 * mane) * slim, 0.115, (0.135 + 0.03 * mane) * slim),
        (0.46, 0.0, 0.0, (0.115 + 0.01 * mane) * slim, 0.14, (0.18 + 0.025 * mane) * slim),
        (0.58, 0.0, 0.0, 0.145, 0.17, 0.24),
        (0.66, 0.0, 0.0, 0.15, 0.18, 0.24),
    ]
    f.loft(k["neck_top"], k["neck_base"] - k["neck_top"], neck, blend=0.08)

    skull = [
        (0.0, 0.0, 0.0, 0.014, 0.014, 0.014, 2.0, 2.0),
        (0.008, 0.0, 0.0, 0.025, 0.022, 0.024, 2.3, 2.0),
        (0.03, 0.0, 0.0, 0.031, 0.03, 0.034, 2.5, 2.1),
        (0.09, 0.0, 0.0, 0.036, 0.04, 0.045, 2.5, 2.0),
        (0.16, 0.0, 0.0, 0.044, 0.05, 0.058, 2.4, 2.0),
        (0.23, 0.0, 0.0, 0.064, 0.063, 0.078, 2.3, 2.0),
        (0.3, 0.0, 0.0, 0.081, 0.075, 0.1, 2.3, 1.9),
        (0.36, 0.0, 0.0, 0.078, 0.076, 0.095, 2.2, 1.9),
        (0.41, 0.0, 0.0, 0.066, 0.068, 0.078, 2.0, 2.0),
        (0.434, 0.0, 0.0, 0.056, 0.058, 0.066, 2.0, 2.0),
    ]
    f.loft(k["nose"], k["head_axis"], skull, blend=0.04)
    f.ellipsoid(head_point(k, 0.29, -0.045, 0.06), (0.03, 0.06, 0.055), axis=k["head_axis"], blend=0.03)

    f.ellipsoid((0.12, -0.45, 0.98), (0.055, 0.21, 0.12), axis=k["shoulder"] - k["scapula"], blend=0.09)
    f.ellipsoid((0.125, -0.44, 0.8), (0.06, 0.13, 0.11), axis=k["elbow"] - k["shoulder"], blend=0.07)
    f.ellipsoid((0.113, -0.553, 0.875), (0.045, 0.045, 0.055), blend=0.05)
    f.ellipsoid((0.055, -0.585, 0.82), (0.055, 0.06, 0.09), blend=0.06, pair=0.04)
    f.ellipsoid((0.105, -0.335, 0.725), (0.035, 0.04, 0.045), blend=0.03)

    f.ellipsoid((0.1, 0.43, 1.07), (0.095, 0.2, 0.13), blend=0.08)
    f.ellipsoid((0.125, 0.42, 0.9), (0.08, 0.2, 0.2), blend=0.08)
    f.ellipsoid((0.06, 0.635, 1.0), (0.04, 0.04, 0.05), blend=0.04, pair=0.03)
    f.ellipsoid((0.08, 0.59, 0.92), (0.065, 0.065, 0.15), blend=0.06, pair=0.03)

    top = numpy.array([0.105, -0.38, 0.76])
    forearm = [
        (0.0, 0.0, 0.0, 0.05, 0.09, 0.075),
        (0.07, 0.0, 0.0, 0.046, 0.075, 0.065),
        (0.15, 0.0, 0.0, 0.04, 0.055, 0.05),
        (0.25, 0.0, 0.0, 0.032, 0.038, 0.036),
        (0.32, 0.0, 0.0, 0.028, 0.03, 0.03),
        (float(numpy.linalg.norm(k["carpus"] - top)), 0.0, 0.0, 0.031, 0.031, 0.034),
    ]
    f.loft(top, k["carpus"] - top, forearm, blend=0.04, group="fore")
    f.ellipsoid(k["carpus"] + numpy.array([0.0, -0.002, -0.005]), (0.032, 0.035, 0.04), blend=0.015, group="fore")
    cannon = [
        (0.0, 0.0, 0.0, 0.029, 0.03, 0.03),
        (0.06, 0.0, 0.0, 0.022, 0.03, 0.021),
        (0.17, 0.0, 0.0, 0.02, 0.029, 0.019),
        (0.25, 0.0, 0.0, 0.022, 0.03, 0.021),
        (float(numpy.linalg.norm(k["fetlock_f"] - k["carpus"])), 0.0, 0.0, 0.027, 0.035, 0.026),
    ]
    f.loft(k["carpus"], k["fetlock_f"] - k["carpus"], cannon, blend=0.015, group="fore")
    f.ellipsoid(k["fetlock_f"], (0.028, 0.034, 0.034), blend=0.015, group="fore")
    f.cone(k["fetlock_f"], k["coffin_f"] + numpy.array([0.0, -0.004, -0.005]), 0.027, 0.03, blend=0.012, group="fore")

    crown = numpy.array([0.11, 0.41, 0.92])
    gaskin = [
        (0.0, 0.0, 0.0, 0.075, 0.17, 0.17),
        (0.12, 0.0, 0.0, 0.07, 0.15, 0.2),
        (0.2, 0.0, 0.0, 0.062, 0.125, 0.2),
        (0.28, 0.0, 0.0, 0.054, 0.105, 0.15),
        (0.36, 0.0, 0.0, 0.044, 0.085, 0.095),
        (0.42, 0.0, 0.0, 0.035, 0.07, 0.06),
        (float(numpy.linalg.norm(k["hock"] - crown)), 0.0, 0.0, 0.034, 0.06, 0.046),
    ]
    f.loft(crown, k["hock"] - crown, gaskin, blend=0.05, group="hind")
    f.ellipsoid(k["hock"] + numpy.array([0.0, 0.005, 0.0]), (0.034, 0.05, 0.055), blend=0.02, group="hind")
    f.ellipsoid(k["hock_point"] + numpy.array([0.0, -0.005, -0.005]), (0.02, 0.025, 0.035), blend=0.02, group="hind")
    shank = [
        (0.0, 0.0, 0.0, 0.03, 0.04, 0.03),
        (0.08, 0.0, 0.0, 0.022, 0.032, 0.022),
        (0.2, 0.0, 0.0, 0.019, 0.03, 0.019),
        (0.3, 0.0, 0.0, 0.021, 0.03, 0.021),
        (float(numpy.linalg.norm(k["fetlock_h"] - k["hock"])), 0.0, 0.0, 0.026, 0.035, 0.026),
    ]
    f.loft(k["hock"], k["fetlock_h"] - k["hock"], shank, blend=0.02, group="hind")
    f.ellipsoid(k["fetlock_h"], (0.029, 0.036, 0.035), blend=0.015, group="hind")
    f.cone(k["fetlock_h"], k["coffin_h"] + numpy.array([0.0, 0.004, -0.005]), 0.027, 0.03, blend=0.012, group="hind")

    f.cone(k["tail"], k["tail_tip"], 0.032, 0.018, blend=0.03, group="tail")

    f.ellipsoid(k["eye"], (0.021, 0.021, 0.021), blend=0.0, group="extra")
    ear_axis = fields.unit((0.55, 0.3, 0.78))
    f.ellipsoid(k["ear"] + ear_axis * 0.085, (0.04, 0.095, 0.012), axis=ear_axis, roll=35.0, blend=0.01, group="extra")
    f.ellipsoid(k["coffin_f"] + numpy.array([0.0, -0.015, -0.028]), (0.034, 0.048, 0.03), blend=0.0, group="extra")
    f.ellipsoid(k["coffin_h"] + numpy.array([0.0, -0.015, -0.028]), (0.034, 0.048, 0.03), blend=0.0, group="extra")
    if stag:
        beam = [numpy.array(p) for p in ((0.0, 0.0, 0.0), (0.06, 0.04, 0.1), (0.17, 0.14, 0.3), (0.25, 0.24, 0.5), (0.27, 0.27, 0.66), (0.22, 0.26, 0.78))]
        for index in range(len(beam) - 1):
            f.cone(k["pedicle"] + beam[index], k["pedicle"] + beam[index + 1], 0.024 - index * 0.002, 0.022 - index * 0.002, blend=0.01, group="extra")
        for base, reach in (((0.015, 0.01, 0.025), (0.04, -0.22, 0.12)), ((0.04, 0.025, 0.07), (0.07, -0.18, 0.12)), ((0.2, 0.18, 0.38), (0.05, -0.2, 0.1)), ((0.27, 0.27, 0.66), (0.05, -0.1, 0.17)), ((0.27, 0.27, 0.66), (0.08, 0.1, 0.16))):
            f.cone(k["pedicle"] + numpy.array(base), k["pedicle"] + numpy.array(base) + numpy.array(reach), 0.015, 0.004, blend=0.01, group="extra")

    blueprint = {"name": "deer_" + kind, "field": f, "marks": k, "scale": 1.0 if stag else 0.875}
    blueprint["bounds"] = (numpy.array([-0.55, -1.35, -0.02]), numpy.array([0.55, 0.8, 2.4 if stag else 1.8]))
    blueprint["extent"] = {"length": 2.1, "height": 2.3 if stag else 1.7, "center": -0.25, "body": 1.6}
    skin = ("core", "fore", "hind", "tail")
    eye_axis = fields.unit((0.9, -0.3, 0.12))
    eye_surface = f.project(numpy.array([head_point(k, 0.245, 0.035, 0.06)]), ("core",))[0]
    ear_root = f.project(numpy.array([head_point(k, 0.385, 0.05, 0.05)]), ("core",))[0]
    k["eye_center"] = eye_surface - eye_axis * (0.021 - 0.005)
    k["ear_root"] = ear_root
    cage = {"around": 32, "core": ("core",), "skin": skin, "head_station": 9}
    cage["spine"] = [(0.59, 0.965, 0.0, 0.045), (0.3, 0.985, 0.0, 0.045), (-0.05, 0.935, 0.0, 0.045), (-0.34, 0.93, 0.0, 0.042), (-0.47, 0.965, 15.0, 0.038), (-0.546, 1.048, 40.0, 0.034), (-0.611, 1.15, 54.0, 0.032), (-0.673, 1.253, 54.0, 0.03), (-0.735, 1.356, 46.0, 0.026), (-0.79, 1.425, 18.0, 0.02), (-0.85, 1.462, -15.0, 0.017), (-0.889, 1.447, -27.5, 0.015), (-1.011, 1.385, -27.5, 0.013), (-1.122, 1.329, -27.5, 0.011)]
    cage["pivots"] = [(9, 11, (-0.84, 1.33))]
    cage["legs"] = [
        {"name": "fore", "group": "fore", "around": 16, "limit": 0.74, "path": [((0.1, -0.392, 0.63), 3), ((0.095, -0.405, 0.52), 2), ((0.088, -0.418, 0.44), 1), ((0.088, -0.42, 0.405), 1), ((0.088, -0.421, 0.37), 2), ((0.088, -0.424, 0.26), 2), ((0.088, -0.427, 0.16), 1), ((0.088, -0.427, 0.125), 1), ((0.088, -0.44, 0.09), 1), ((0.088, -0.456, 0.044), 0)]},
        {"name": "hind", "group": "hind", "around": 16, "limit": 0.82, "path": [((0.106, 0.459, 0.735), 3), ((0.1034, 0.489, 0.62), 2), ((0.1014, 0.513, 0.53), 1), ((0.1, 0.535, 0.47), 1), ((0.098, 0.528, 0.41), 2), ((0.097, 0.522, 0.28), 2), ((0.095, 0.517, 0.16), 1), ((0.095, 0.515, 0.125), 1), ((0.095, 0.5, 0.09), 1), ((0.095, 0.484, 0.044), 0)]},
    ]
    cage["eye"] = {"center": k["eye_center"], "axis": eye_axis, "slit": k["head_axis"], "radius": 0.021, "open": (42.0, 26.0), "cells": 2}
    cage["ear"] = {"root": ear_root, "axis": fields.unit((0.55, 0.3, 0.78)), "face": fields.unit((0.75, -0.62, -0.1)), "length": 0.17, "width": 0.085, "around": 12, "cells": (1, 2)}
    cage["mouth"] = {"row": 5}
    cage["nostril"] = {"cell": (1, 1), "rows": 2, "cols": 2, "depth": 0.012}
    cage["tail"] = {"cell": (1, 1), "rows": 2, "around": 8, "flat": 0.6, "path": [(0.0, 0.655, 1.07), (0.0, 0.69, 1.05), (0.0, 0.71, 0.99), (0.0, 0.712, 0.93)], "radii": [0.032, 0.03, 0.026, 0.018]}
    blueprint["cage"] = cage
    blueprint["hoof"] = {"length": 0.08, "width": 0.028, "toe_height": 0.058, "heel_height": 0.034, "dew_offset": 0.014, "dew_back": 0.028, "dew_drop": 0.02, "dew_length": 0.024, "dew_radius": 0.009}
    if stag:
        k["pedicle"] = f.project(numpy.array([head_point(k, 0.33, 0.06, 0.042)]), ("core",))[0]
        tines = [
            {"path": [(0.012, 0.008, 0.035), (0.03, -0.07, 0.075), (0.045, -0.15, 0.13), (0.05, -0.19, 0.2)], "radii": [0.016, 0.014, 0.011, 0.005]},
            {"path": [(0.04, 0.035, 0.085), (0.07, -0.03, 0.13), (0.09, -0.09, 0.185), (0.095, -0.115, 0.24)], "radii": [0.015, 0.013, 0.01, 0.005]},
            {"path": [(0.155, 0.135, 0.29), (0.19, 0.075, 0.33), (0.215, 0.02, 0.385), (0.225, 0.0, 0.44)], "radii": [0.015, 0.013, 0.01, 0.005]},
            {"path": [(0.262, 0.27, 0.66), (0.29, 0.22, 0.73), (0.3, 0.19, 0.81)], "radii": [0.016, 0.012, 0.005], "rings": 5},
            {"path": [(0.262, 0.27, 0.66), (0.23, 0.29, 0.75), (0.2, 0.3, 0.84)], "radii": [0.016, 0.012, 0.005], "rings": 5},
            {"path": [(0.262, 0.27, 0.66), (0.3, 0.31, 0.74), (0.33, 0.34, 0.81)], "radii": [0.016, 0.012, 0.005], "rings": 5},
        ]
        blueprint["antler"] = {"beam": [(0.0, 0.0, -0.01), (0.03, 0.025, 0.05), (0.075, 0.06, 0.13), (0.14, 0.12, 0.26), (0.205, 0.19, 0.4), (0.25, 0.245, 0.54), (0.262, 0.27, 0.66)], "beam_radii": [0.024, 0.023, 0.022, 0.021, 0.02, 0.019, 0.018], "tines": tines}
    return blueprint


def pieces(blueprint):
    marks = blueprint["marks"]
    result = [parts.eyeball(blueprint["cage"]["eye"])]
    result.append(parts.mirrored(result[0]))
    result.extend(parts.hooves(marks, blueprint["hoof"]))
    if "antler" in blueprint:
        result.extend(parts.antlers(marks["pedicle"], blueprint["antler"]))
    return result


def build(name):
    if name == "deer_stag":
        return deer("stag")
    if name == "deer_hind":
        return deer("hind")
    raise ValueError(name)
