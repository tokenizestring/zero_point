import math
import numpy
import fauna_hoofed_field as fields
import fauna_hoofed_parts as parts
import fauna_hoofed_rig as rigs
import fauna_hoofed_species as species

point = species.point
head_point = species.head_point


def anatomy(f, k, stag):
    rows = [
        (-0.655, 0.99, 0.87, 0.93, 0.04, 2.0, 2.0),
        (-0.62, 1.04, 0.815, 0.93, 0.085, 2.0, 2.0),
        (-0.52, 1.165, 0.718, 0.92, 0.135, 1.8, 2.0),
        (-0.43, 1.208, 0.675, 0.9, 0.16, 1.6, 1.85),
        (-0.33, 1.205, 0.665, 0.89, 0.18, 1.7, 1.9),
        (-0.19, 1.185, 0.672, 0.89, 0.2, 1.95, 2.1),
        (-0.05, 1.172, 0.695, 0.9, 0.21 if stag else 0.215, 2.1, 2.25),
        (0.1, 1.172, 0.735 if stag else 0.725, 0.93, 0.205 if stag else 0.212, 2.15, 2.3),
        (0.24, 1.185, 0.785, 0.97, 0.185, 2.15, 2.2),
        (0.38, 1.195, 0.8, 1.0, 0.18, 2.2, 2.1),
        (0.5, 1.17, 0.79, 0.99, 0.165, 2.2, 2.0),
        (0.6, 1.115, 0.805, 0.97, 0.125, 2.1, 2.0),
        (0.655, 1.06, 0.85, 0.96, 0.08, 2.0, 2.0),
        (0.675, 1.015, 0.9, 0.96, 0.035, 2.0, 2.0),
    ]
    species.torso(f, rows)

    mane = 1.0 if stag else 0.0
    slim = 1.0 if stag else 0.83
    neck = [
        (-0.1, 0.0, 0.0, 0.015, 0.022, 0.015),
        (-0.065, 0.0, 0.0, 0.034, 0.062, 0.042),
        (-0.03, 0.0, 0.0, 0.05, 0.09, 0.064),
        (0.0, 0.0, 0.0, 0.06 * slim, 0.1, 0.078),
        (0.1, 0.0, 0.0, (0.066 + 0.01 * mane) * slim, 0.096 + 0.006 * mane, (0.088 + 0.028 * mane) * slim),
        (0.22, 0.0, 0.0, (0.076 + 0.018 * mane) * slim, 0.1 + 0.012 * mane, (0.105 + 0.055 * mane) * slim),
        (0.34, 0.0, 0.0, (0.092 + 0.02 * mane) * slim, 0.115 + 0.012 * mane, (0.135 + 0.06 * mane) * slim),
        (0.46, 0.0, 0.0, (0.115 + 0.014 * mane) * slim, 0.14 + 0.006 * mane, (0.18 + 0.04 * mane) * slim),
        (0.58, 0.0, 0.0, 0.145, 0.17, 0.24),
        (0.66, 0.0, 0.0, 0.15, 0.18, 0.24),
    ]
    f.loft(k["neck_top"], k["neck_base"] - k["neck_top"], neck, blend=0.085)
    f.ridge([point(0.07 * slim, -0.775, 1.375), point(0.105 * slim, -0.67, 1.16), point(0.125, -0.565, 0.92)], 0.05, 0.007, taper=0.15)
    f.ridge([point(0.05 * slim, -0.79, 1.28), point(0.075 * slim, -0.72, 1.13), point(0.085, -0.655, 0.98)], 0.028, -0.006, taper=0.2)

    fine = 1.0 if stag else 0.93
    skull = [
        (0.0, 0.0, 0.0, 0.021 * fine, 0.018, 0.02, 2.4, 2.2),
        (0.008, 0.0, 0.0, 0.028 * fine, 0.024, 0.027, 2.6, 2.3),
        (0.03, 0.0, 0.0, 0.0325 * fine, 0.031, 0.036, 2.7, 2.3),
        (0.09, 0.0, 0.0, 0.036 * fine, 0.037, 0.047, 2.5, 2.1),
        (0.16, 0.0, 0.004, 0.043 * fine, 0.044, 0.06, 2.4, 2.0),
        (0.23, 0.0, 0.014, 0.064, 0.047, 0.088, 2.3, 1.75),
        (0.3, 0.0, 0.022, 0.082, 0.051, 0.118, 2.3, 1.6),
        (0.36, 0.0, 0.02, 0.078, 0.05, 0.112, 2.2, 1.65),
        (0.41, 0.0, 0.008, 0.066, 0.041, 0.088, 2.0, 1.9),
        (0.445, 0.0, 0.0, 0.05, 0.028, 0.06, 2.0, 2.0),
        (0.47, 0.0, 0.0, 0.03, 0.016, 0.035, 2.0, 2.0),
    ]
    f.loft(k["nose"], k["head_axis"], skull, blend=0.06)
    f.bump(head_point(k, 0.262, 0.058, 0.05), (0.024, 0.042, 0.015), 0.01, axis=k["head_axis"])
    f.ridge([head_point(k, 0.19, 0.004, 0.05), head_point(k, 0.26, 0.002, 0.076), head_point(k, 0.34, 0.012, 0.078)], 0.02, 0.006, taper=0.25)
    f.bump(head_point(k, 0.305, -0.05, 0.058), (0.022, 0.055, 0.045), 0.007, axis=k["head_axis"])
    f.bump(head_point(k, 0.2, -0.082, 0.0), (0.02, 0.09, 0.02), -0.009, axis=k["head_axis"])
    f.bump(head_point(k, 0.04, -0.04, 0.0), (0.02, 0.03, 0.014), 0.004, axis=k["head_axis"])
    f.bump(head_point(k, 0.014, 0.008, 0.021), (0.014, 0.018, 0.014), 0.004, axis=k["head_axis"])
    f.ridge([head_point(k, 0.004, -0.014, 0.012), head_point(k, 0.05, -0.017, 0.031), head_point(k, 0.105, -0.018, 0.037)], 0.005, -0.0025, taper=0.08)
    f.ridge([head_point(k, 0.215, 0.018, 0.058), head_point(k, 0.185, 0.008, 0.049)], 0.009, -0.004, taper=0.2)
    f.bump(head_point(k, 0.39, 0.04, 0.052), (0.028, 0.03, 0.028), 0.01, axis=k["head_axis"])
    if stag:
        base = head_point(k, 0.335, 0.05, 0.043)
        f.cone(base, base + numpy.array([0.012, 0.012, 0.03]), 0.024, 0.022, blend=0.015)

    wide = 1.0 if stag else 0.93
    f.ellipsoid((0.118 * wide, -0.455, 0.985), (0.052 * wide, 0.215, 0.115), axis=k["shoulder"] - k["scapula"], blend=0.09)
    f.ridge([point(0.135 * wide, -0.375, 1.115), point(0.16 * wide, -0.455, 1.01), point(0.158 * wide, -0.535, 0.905)], 0.03, 0.006, taper=0.2)
    f.ellipsoid((0.115 * wide, -0.558, 0.875), (0.042, 0.042, 0.05), blend=0.05)
    f.ellipsoid((0.128 * wide, -0.425, 0.815), (0.062 * wide, 0.14, 0.115), axis=k["elbow"] - k["shoulder"], blend=0.07)
    f.bump((0.165 * wide, -0.385, 0.845), (0.05, 0.08, 0.09), 0.01)
    f.ellipsoid((0.105, -0.335, 0.725), (0.034, 0.04, 0.045), blend=0.03)
    f.ellipsoid((0.045, -0.6, 0.875), (0.045, 0.045, 0.075), blend=0.07, pair=0.06)

    def ribs(query):
        q = (query - numpy.array([0.19, -0.12, 0.92])[None, :]) / numpy.array([0.09, 0.25, 0.18])[None, :]
        mask = numpy.clip(1.0 - numpy.sum(q * q, axis=1), 0.0, 1.0) ** 2
        return 0.0008 * mask * numpy.cos(2.0 * math.pi * (query[:, 1] + 0.35 * (query[:, 2] - 0.92)) / 0.045)

    f.custom(ribs, (0.08, -0.4, 0.7), (0.3, 0.16, 1.14))

    f.ellipsoid((0.1, 0.42, 1.06), (0.09, 0.2, 0.125), blend=0.08)
    f.ellipsoid((0.125, 0.43, 0.9), (0.078, 0.195, 0.2), blend=0.08)
    f.bump((0.158, 0.27, 1.105), (0.035, 0.05, 0.04), 0.013)
    f.bump((0.175, 0.2, 1.0), (0.06, 0.09, 0.12), -0.012)
    f.ellipsoid((0.06, 0.635, 0.995), (0.038, 0.038, 0.048), blend=0.04, pair=0.03)
    f.ellipsoid((0.082, 0.585, 0.9), (0.062, 0.062, 0.15), blend=0.06, pair=0.03)
    f.ellipsoid((0.055, 0.46, 0.85), (0.05, 0.13, 0.09), blend=0.06, pair=0.04)

    top = point(0.105, -0.375, 0.76)
    forearm = [
        (0.0, 0.0, 0.0, 0.052, 0.095, 0.078),
        (0.07, 0.0, 0.0, 0.05, 0.082, 0.07),
        (0.15, 0.0, 0.0, 0.044, 0.062, 0.056),
        (0.25, 0.0, 0.0, 0.035, 0.042, 0.04),
        (0.32, 0.0, 0.0, 0.03, 0.033, 0.032),
        (float(numpy.linalg.norm(k["carpus"] - top)), 0.0, 0.0, 0.03, 0.03, 0.033),
        (float(numpy.linalg.norm(k["carpus"] - top)) + 0.045, 0.0, 0.0, 0.016, 0.018, 0.018),
    ]
    f.loft(top, k["carpus"] - top, forearm, blend=0.04, group="fore")
    f.ellipsoid(k["carpus"] + point(0.0, -0.002, -0.005), (0.03, 0.032, 0.044), blend=0.02, group="fore")
    f.bump(k["carpus"] + point(0.0, 0.03, 0.004), (0.018, 0.018, 0.026), 0.006, group="fore")
    cannon = [
        (0.0, 0.0, 0.0, 0.028, 0.03, 0.03),
        (0.06, 0.0, 0.0, 0.0215, 0.029, 0.0205),
        (0.17, 0.0, 0.0, 0.0195, 0.028, 0.0185),
        (0.25, 0.0, 0.0, 0.021, 0.029, 0.02),
        (float(numpy.linalg.norm(k["fetlock_f"] - k["carpus"])), 0.0, 0.0, 0.026, 0.034, 0.025),
    ]
    f.loft(k["carpus"], k["fetlock_f"] - k["carpus"], cannon, blend=0.015, group="fore")
    for offset in (0.019, -0.019):
        f.ridge([k["carpus"] + point(offset, 0.011, -0.05), k["fetlock_f"] + point(offset, 0.011, 0.045)], 0.009, -0.0028, taper=0.2, group="fore")
    f.ellipsoid(k["fetlock_f"], (0.027, 0.031, 0.032), blend=0.02, group="fore")
    f.cone(k["fetlock_f"], k["coffin_f"] + point(0.0, -0.004, -0.005), 0.026, 0.029, blend=0.012, group="fore")

    crown = point(0.11, 0.41, 0.92)
    gaskin = [
        (0.0, 0.0, 0.0, 0.075, 0.17, 0.17),
        (0.12, 0.0, 0.0, 0.07, 0.15, 0.2),
        (0.2, 0.0, 0.0, 0.062, 0.125, 0.2),
        (0.28, 0.0, 0.0, 0.054, 0.105, 0.15),
        (0.36, 0.0, 0.0, 0.044, 0.085, 0.095),
        (0.42, 0.0, 0.0, 0.035, 0.07, 0.06),
        (float(numpy.linalg.norm(k["hock"] - crown)), 0.0, 0.0, 0.033, 0.058, 0.044),
        (float(numpy.linalg.norm(k["hock"] - crown)) + 0.05, 0.0, 0.0, 0.018, 0.03, 0.02),
    ]
    f.loft(crown, k["hock"] - crown, gaskin, blend=0.05, group="hind")
    f.bump(k["stifle"] + point(0.012, 0.0, 0.012), (0.045, 0.05, 0.07), 0.008, group="hind")
    f.ridge([point(0.1, 0.578, 0.74), point(0.1, 0.59, 0.62), k["hock_point"]], 0.017, 0.006, taper=0.15, group="hind")
    for offset in (0.028, -0.028):
        f.bump(point(0.1 + offset, 0.553, 0.585), (0.02, 0.026, 0.065), -0.0065, group="hind")
    f.ellipsoid(k["hock"] + point(0.0, 0.004, -0.004), (0.031, 0.042, 0.06), blend=0.03, group="hind")
    f.ellipsoid(k["hock_point"] + point(0.0, -0.006, -0.006), (0.018, 0.022, 0.04), blend=0.025, group="hind")
    shank = [
        (0.0, 0.0, 0.0, 0.03, 0.04, 0.03),
        (0.08, 0.0, 0.0, 0.022, 0.032, 0.022),
        (0.2, 0.0, 0.0, 0.0195, 0.03, 0.019),
        (0.3, 0.0, 0.0, 0.021, 0.03, 0.021),
        (float(numpy.linalg.norm(k["fetlock_h"] - k["hock"])), 0.0, 0.0, 0.026, 0.035, 0.026),
    ]
    f.loft(k["hock"], k["fetlock_h"] - k["hock"], shank, blend=0.02, group="hind")
    for offset in (0.019, -0.019):
        f.ridge([k["hock"] + point(offset, 0.014, -0.07), k["fetlock_h"] + point(offset, 0.012, 0.045)], 0.009, -0.0028, taper=0.2, group="hind")
    f.ellipsoid(k["fetlock_h"], (0.027, 0.032, 0.032), blend=0.02, group="hind")
    f.cone(k["fetlock_h"], k["coffin_h"] + point(0.0, 0.004, -0.005), 0.026, 0.029, blend=0.012, group="hind")

    f.cone(k["tail"], k["tail_tip"], 0.03, 0.016, blend=0.03, group="tail")


def extras(f, k, stag):
    f.ellipsoid(k["eye"], (0.021, 0.021, 0.021), blend=0.0, group="extra")
    ear_axis = fields.unit((0.55, 0.3, 0.78))
    f.ellipsoid(k["ear"] + ear_axis * 0.085, (0.04, 0.095, 0.012), axis=ear_axis, roll=35.0, blend=0.01, group="extra")
    f.ellipsoid(k["coffin_f"] + point(0.0, -0.015, -0.028), (0.034, 0.048, 0.03), blend=0.0, group="extra")
    f.ellipsoid(k["coffin_h"] + point(0.0, -0.015, -0.028), (0.034, 0.048, 0.03), blend=0.0, group="extra")


def build(kind):
    stag = kind == "stag"
    f = fields.field()
    k = {}
    k["withers"] = point(0.0, -0.375, 1.208)
    k["scapula"] = point(0.055, -0.345, 1.11)
    k["shoulder"] = point(0.115, -0.55, 0.875)
    k["elbow"] = point(0.105, -0.36, 0.705)
    k["carpus"] = point(0.088, -0.42, 0.405)
    k["fetlock_f"] = point(0.088, -0.427, 0.125)
    k["coffin_f"] = point(0.088, -0.453, 0.055)
    k["toe_f"] = point(0.088, -0.51, 0.0)
    k["hip"] = point(0.1, 0.43, 1.015)
    k["stifle"] = point(0.125, 0.26, 0.72)
    k["hock"] = point(0.1, 0.53, 0.465)
    k["hock_point"] = point(0.1, 0.59, 0.515)
    k["fetlock_h"] = point(0.095, 0.515, 0.125)
    k["coffin_h"] = point(0.095, 0.487, 0.055)
    k["toe_h"] = point(0.095, 0.43, 0.0)
    k["neck_top"] = point(0.0, -0.79, 1.44)
    k["neck_base"] = point(0.0, -0.45, 0.97)
    k["nose"] = point(0.0, -1.155, 1.315)
    k["occiput"] = point(0.0, -0.77, 1.515)
    k["head_axis"] = fields.unit(k["occiput"] - k["nose"])
    k["head_up"] = numpy.cross(fields.lateral, k["head_axis"])
    k["eye"] = head_point(k, 0.245, 0.035, 0.064)
    k["ear"] = head_point(k, 0.39, 0.05, 0.058)
    k["jaw"] = head_point(k, 0.35, -0.01, 0.06)
    k["mouth"] = head_point(k, 0.105, -0.018, 0.036)
    k["tail"] = point(0.0, 0.655, 1.06)
    k["tail_tip"] = point(0.0, 0.705, 0.92)
    k["hips"] = point(0.0, 0.27, 1.105)
    k["spine_01"] = point(0.0, 0.2, 1.1)
    k["spine_02"] = point(0.0, 0.02, 1.085)
    k["spine_03"] = point(0.0, -0.2, 1.07)
    k["neck_01"] = point(0.0, -0.5, 0.93)
    k["skull"] = point(0.0, -0.79, 1.45)
    k["ribs"] = point(0.16, -0.1, 0.92)
    anatomy(f, k, stag)
    extras(f, k, stag)

    scale = 1.0 if stag else 0.875
    blueprint = {"name": "deer_" + kind, "rig_name": "deer_rig", "field": f, "marks": k, "scale": scale}
    blueprint["bounds"] = (point(-0.55, -1.35, -0.02), point(0.55, 0.8, 1.75))
    blueprint["extent"] = {"length": 2.1, "height": 2.3 if stag else 1.7, "center": -0.25, "body": 1.6}
    skin = ("core", "fore", "hind", "tail")
    eye_axis = fields.unit((0.9, -0.3, 0.12))
    eye_surface = f.project(numpy.array([head_point(k, 0.245, 0.035, 0.06)]), ("core",))[0]
    ear_root = f.project(numpy.array([head_point(k, 0.39, 0.05, 0.05)]), ("core",))[0]
    k["eye_center"] = eye_surface - eye_axis * (0.0235 - 0.0035)
    k["ear_root"] = ear_root
    cage = {"around": 32, "core": ("core",), "skin": skin, "head_station": 9}
    cage["spine"] = [(0.59, 0.965, 0.0, 0.045), (0.3, 0.985, 0.0, 0.045), (-0.05, 0.935, 0.0, 0.045), (-0.34, 0.93, 0.0, 0.04), (-0.47, 0.965, 15.0, 0.03), (-0.546, 1.048, 40.0, 0.026), (-0.611, 1.15, 54.0, 0.03), (-0.673, 1.253, 54.0, 0.028), (-0.735, 1.356, 46.0, 0.02), (-0.79, 1.425, 18.0, 0.013), (-0.85, 1.462, -15.0, 0.012), (-0.889, 1.447, -27.5, 0.014), (-1.011, 1.385, -27.5, 0.013), (-1.122, 1.329, -27.5, 0.011)]
    cage["pivots"] = [(9, 11, (-0.84, 1.33))]
    cage["legs"] = [
        {"name": "fore", "group": "fore", "around": 16, "limit": 0.74, "path": [((0.1, -0.392, 0.63), 3), ((0.095, -0.405, 0.52), 2), ((0.088, -0.418, 0.44), 1), ((0.088, -0.42, 0.405), 1), ((0.088, -0.421, 0.37), 2), ((0.088, -0.424, 0.26), 2), ((0.088, -0.427, 0.16), 1), ((0.088, -0.427, 0.125), 1), ((0.088, -0.44, 0.09), 1), ((0.088, -0.456, 0.044), 0)]},
        {"name": "hind", "group": "hind", "around": 16, "limit": 0.82, "path": [((0.106, 0.459, 0.735), 3), ((0.1034, 0.489, 0.62), 2), ((0.1014, 0.513, 0.53), 1), ((0.1, 0.535, 0.47), 1), ((0.098, 0.528, 0.41), 2), ((0.097, 0.522, 0.28), 2), ((0.095, 0.517, 0.16), 1), ((0.095, 0.515, 0.125), 1), ((0.095, 0.5, 0.09), 1), ((0.095, 0.484, 0.044), 0)]},
    ]
    cage["eye"] = {"center": k["eye_center"], "axis": eye_axis, "slit": k["head_axis"], "radius": 0.0235, "open": (46.0, 29.0), "cells": 2}
    cage["ear"] = {"root": ear_root, "axis": fields.unit((0.6, 0.32, 0.73)), "face": fields.unit((0.72, -0.66, -0.12)), "length": 0.19, "width": 0.1, "around": 12, "cells": (1, 2)}
    cage["mouth"] = {"row": 5}
    cage["nostril"] = {"cell": (1, 1), "rows": 2, "cols": 2, "depth": 0.012}
    cage["tail"] = {"cell": (1, 1), "rows": 2, "around": 8, "flat": 0.5, "path": [(0.0, 0.655, 1.06), (0.0, 0.684, 1.045), (0.0, 0.699, 0.985), (0.0, 0.697, 0.915)], "radii": [0.032, 0.033, 0.028, 0.017]}
    blueprint["cage"] = cage
    blueprint["hoof"] = {"length": 0.08, "width": 0.028, "toe_height": 0.058, "heel_height": 0.034, "dew_offset": 0.013, "dew_back": 0.026, "dew_drop": 0.022, "dew_length": 0.02, "dew_radius": 0.0075}
    tail_path = [numpy.array(p) for p in cage["tail"]["path"]]
    blueprint["bones"] = rigs.quadruped(k, tail_path[:3])
    blueprint["rig"] = {
        "axial": ["hips", "spine_01", "spine_02", "spine_03", "neck_01", "neck_02", "neck_03", "head"],
        "axial_widths": [0.0, 0.12, 0.16, 0.16, 0.16, 0.12, 0.12, 0.09],
        "limbs": [
            {"name": "fore", "bones": ["scapula", "humerus", "radius", "cannon", "pastern_f", "hoof_f"], "tip": k["toe_f"], "widths": [0.0, 0.12, 0.1, 0.05, 0.04, 0.025], "reach": [0.17, 0.16, 0.11, 0.06, 0.05, 0.05], "grip": [0.55, 0.85, 1.0, 1.0, 1.0, 1.0]},
            {"name": "hind", "bones": ["femur", "tibia", "metatarsus", "pastern_h", "hoof_h"], "tip": k["toe_h"], "widths": [0.0, 0.14, 0.06, 0.04, 0.025], "reach": [0.2, 0.17, 0.08, 0.05, 0.05], "grip": [0.75, 1.0, 1.0, 1.0, 1.0], "mass": (0.82, 1.04, (0.16, 0.3), (0.64, 0.72), 0.82)},
        ],
        "ribs": {"center": (0.17, -0.06, 0.93), "radii": (0.14, 0.3, 0.22), "amount": 0.55},
        "tail": ["tail_01", "tail_02", "tail_03"],
        "tail_tip": tail_path[3],
        "tail_widths": [0.0, 0.04, 0.04],
    }
    blueprint["facts"] = {"mass": 190.0 if stag else 110.0, "hull": {"center": (0.0, 0.03, 0.93), "half_length": 0.4, "radius": 0.24}}
    pace = 1.0 if stag else 0.935
    blueprint["motion"] = {
        "prefix": "deer_" if stag else "deer_hind_",
        "nose": k["nose"],
        "skull": k["skull"],
        "breath": 0.008,
        "walk": {"kind": "walk", "frames": 28, "speed": 1.3 * pace, "duty": {"fore": 0.63, "hind": 0.63}, "phase": {"hind_l": 0.0, "fore_l": 0.25, "hind_r": 0.5, "fore_r": 0.75}, "center": {"fore": (0.0, 0.0, 0.0), "hind": (0.0, -0.02, 0.0)}, "narrow": 0.8, "lift": {"fore": 0.085, "hind": 0.07}, "toe": {"fore": 0.75, "hind": 0.55}, "curl": {"fore": 0.5, "hind": 0.4}, "swing_flex": {"fore": 0.95, "hind": 0.5}, "stance_flex": {"fore": 0.0, "hind": 0.06}, "sink": 0.12, "follow": 0.35, "bob": 0.012, "sway": 0.014, "roll": 2.2, "yaw": 3.5, "nod": 3.6},
        "trot": {"kind": "trot", "frames": 18, "speed": 3.5 * pace, "duty": {"fore": 0.4, "hind": 0.4}, "phase": {"hind_l": 0.0, "fore_r": 0.0, "hind_r": 0.5, "fore_l": 0.5}, "center": {"fore": (0.0, -0.02, 0.0), "hind": (0.0, -0.05, 0.0)}, "narrow": 0.65, "lift": {"fore": 0.14, "hind": 0.11}, "toe": {"fore": 0.9, "hind": 0.7}, "curl": {"fore": 0.7, "hind": 0.55}, "swing_flex": {"fore": 1.35, "hind": 0.75}, "stance_flex": {"fore": 0.0, "hind": 0.1}, "sink": 0.2, "follow": 0.45, "bob": 0.028, "roll": 1.5, "yaw": 2.0, "nod": 1.5},
        "run": {"kind": "gallop", "frames": 13, "speed": 11.0 * pace, "duty": {"fore": 0.21, "hind": 0.21}, "phase": {"hind_l": 0.0, "hind_r": 0.08, "fore_r": 0.45, "fore_l": 0.55}, "center": {"fore": (0.0, -0.04, 0.0), "hind": (0.0, -0.14, 0.0)}, "narrow": 0.5, "lift": {"fore": 0.22, "hind": 0.2}, "toe": {"fore": 1.0, "hind": 0.8}, "curl": {"fore": 0.9, "hind": 0.7}, "swing_flex": {"fore": 1.9, "hind": 1.05}, "stance_flex": {"fore": 0.0, "hind": 0.15}, "sink": 0.3, "follow": 0.62, "bob": 0.055, "roll": 1.5, "flex": 15.0, "nod": 3.0, "hover": -0.03},
        "attack": {"hit": 0.42, "reach": 0.16, "crouch": -0.035, "dip": 5.0, "neck_down": -58.0, "neck_up": 26.0, "head_down": -32.0, "head_up": 24.0},
        "rest": {"hips": -0.66, "pitch": 4.5, "fore": (0.0, 0.0, -70.0, 155.0, 20.0, 0.0), "hind": (-46.0, 53.0, -91.0, 16.0, 0.0), "neck": -8.0, "head": 4.0},
        "death": {"side": 0.36, "drop": -0.925, "neck": -48.0, "head": 18.0, "neck_yaw": -18.0 if stag else -4.0, "head_yaw": 0.0, "head_roll": -40.0 if stag else 0.0, "droop": -12.0, "fore_upper": (0.0, 5.0, -12.0, 38.0, 20.0, 10.0), "fore_lower": (0.0, 0.0, -6.0, 24.0, 15.0, 8.0), "hind_upper": (-14.0, 24.0, -18.0, 15.0, 8.0), "hind_lower": (-8.0, 14.0, -10.0, 12.0, 6.0)},
    }
    if stag:
        k["pedicle"] = f.project(numpy.array([head_point(k, 0.335, 0.062, 0.045)]), ("core",))[0]
        size = 0.88
        tines = [
            {"path": [(0.01, 0.0, 0.03), (0.035, -0.08, 0.05), (0.06, -0.17, 0.09), (0.075, -0.22, 0.17), (0.08, -0.23, 0.25)], "radii": [0.015, 0.0135, 0.011, 0.008, 0.0035], "rings": 9},
            {"path": [(0.035, 0.035, 0.085), (0.075, -0.03, 0.115), (0.11, -0.1, 0.16), (0.125, -0.13, 0.23)], "radii": [0.014, 0.012, 0.009, 0.0035], "rings": 8},
            {"path": [(0.15, 0.17, 0.31), (0.19, 0.1, 0.34), (0.225, 0.03, 0.39), (0.24, 0.0, 0.46)], "radii": [0.014, 0.012, 0.009, 0.0035], "rings": 8},
            {"path": [(0.255, 0.245, 0.68), (0.25, 0.19, 0.76), (0.235, 0.15, 0.86)], "radii": [0.015, 0.011, 0.0035], "rings": 6},
            {"path": [(0.255, 0.245, 0.68), (0.27, 0.28, 0.78), (0.27, 0.3, 0.89)], "radii": [0.015, 0.011, 0.0035], "rings": 6},
            {"path": [(0.255, 0.245, 0.68), (0.31, 0.26, 0.75), (0.36, 0.265, 0.83)], "radii": [0.015, 0.011, 0.0035], "rings": 6},
        ]
        for tine in tines:
            tine["path"] = [tuple(v * size for v in p) for p in tine["path"]]
        beam = [(0.0, 0.0, -0.012), (0.02, 0.02, 0.05), (0.06, 0.07, 0.13), (0.13, 0.15, 0.27), (0.2, 0.22, 0.42), (0.245, 0.25, 0.56), (0.255, 0.245, 0.68)]
        blueprint["antler"] = {"beam": [tuple(v * size for v in p) for p in beam], "beam_radii": [0.024, 0.023, 0.022, 0.021, 0.02, 0.0185, 0.017], "tines": tines, "rings": 22}
        blueprint["bounds"] = (point(-0.55, -1.35, -0.02), point(0.55, 0.8, 1.75))
    return blueprint


def mane(blueprint):
    k = blueprint["marks"]
    axis = fields.unit(k["neck_base"] - k["neck_top"])
    ventral = -numpy.cross(fields.lateral, axis)
    seeds = []
    for row, travel in enumerate(numpy.linspace(0.06, 0.53, 14)):
        center = k["neck_top"] + axis * travel
        swell = math.sin(math.pi * row / 13.0)
        for angle in ((0.0, 23.0, 46.0, 69.0) if row % 2 == 0 else (11.5, 34.5, 57.5)):
            ray = ventral * math.cos(math.radians(angle)) + fields.lateral * math.sin(math.radians(angle))
            seeds.append({"origin": center, "ray": ray, "flow": axis + numpy.array([0.0, 0.0, -0.55]), "length": (0.075 + 0.05 * swell) * (1.0 - 0.25 * angle / 69.0), "width": 0.03, "thick": 0.011, "rise": 0.3, "sag": 0.2})
    return parts.tufts(blueprint["field"], blueprint["cage"]["skin"], seeds)


def pieces(blueprint):
    marks = blueprint["marks"]
    result = [parts.eyeball(blueprint["cage"]["eye"])]
    result.append(parts.mirrored(result[0]))
    result.extend(parts.hooves(marks, blueprint["hoof"]))
    if "antler" in blueprint:
        result.extend(parts.antlers(marks["pedicle"], blueprint["antler"]))
        result.extend(mane(blueprint))
    return result
