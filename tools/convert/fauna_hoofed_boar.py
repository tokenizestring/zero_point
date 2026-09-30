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


def anatomy(f, k):
    rows = [
        (-0.47, 0.765, 0.54, 0.655, 0.1, 2.0, 2.0),
        (-0.42, 0.815, 0.472, 0.64, 0.134, 1.8, 2.1),
        (-0.36, 0.865, 0.418, 0.62, 0.151, 1.65, 2.15),
        (-0.3, 0.895, 0.37, 0.6, 0.162, 1.6, 2.2),
        (-0.24, 0.9, 0.352, 0.595, 0.168, 1.6, 2.2),
        (-0.16, 0.89, 0.345, 0.59, 0.172, 1.65, 2.25),
        (-0.04, 0.862, 0.35, 0.58, 0.174, 1.75, 2.3),
        (0.1, 0.83, 0.372, 0.575, 0.171, 1.85, 2.3),
        (0.24, 0.798, 0.406, 0.575, 0.162, 2.0, 2.2),
        (0.36, 0.77, 0.44, 0.58, 0.148, 2.0, 2.1),
        (0.46, 0.738, 0.46, 0.585, 0.128, 2.0, 2.0),
        (0.53, 0.702, 0.476, 0.585, 0.098, 2.0, 2.0),
        (0.575, 0.662, 0.5, 0.58, 0.06, 2.0, 2.0),
        (0.595, 0.632, 0.525, 0.58, 0.03, 2.0, 2.0),
    ]
    species.torso(f, rows)
    neck = [
        (-0.08, 0.0, 0.0, 0.05, 0.06, 0.06),
        (-0.03, 0.0, 0.0, 0.09, 0.095, 0.11),
        (0.0, 0.0, 0.0, 0.105, 0.108, 0.135),
        (0.08, 0.0, 0.0, 0.125, 0.15, 0.165),
        (0.16, 0.0, 0.0, 0.14, 0.2, 0.195),
        (0.22, 0.0, 0.0, 0.145, 0.22, 0.2),
    ]
    f.loft(k["neck_top"], k["neck_base"] - k["neck_top"], neck, blend=0.08)

    skull = [
        (0.0, 0.0, 0.0, 0.033, 0.034, 0.037, 2.3, 2.3),
        (0.006, 0.0, 0.0, 0.037, 0.038, 0.04, 2.4, 2.4),
        (0.03, 0.0, 0.001, 0.0365, 0.037, 0.043, 2.3, 2.2),
        (0.1, 0.0, 0.007, 0.048, 0.044, 0.068, 2.4, 2.1),
        (0.2, 0.0, 0.014, 0.063, 0.053, 0.1, 2.4, 2.0),
        (0.3, 0.0, 0.019, 0.08, 0.063, 0.13, 2.3, 1.9),
        (0.38, 0.0, 0.021, 0.097, 0.075, 0.165, 2.2, 1.8),
        (0.45, 0.0, 0.018, 0.108, 0.09, 0.2, 2.2, 1.8),
        (0.51, 0.0, 0.012, 0.11, 0.098, 0.2, 2.1, 1.9),
        (0.56, 0.0, 0.0, 0.095, 0.09, 0.16, 2.0, 2.0),
        (0.6, 0.0, 0.0, 0.055, 0.05, 0.08, 2.0, 2.0),
    ]
    f.loft(k["nose"], k["head_axis"], skull, blend=0.06)
    f.bump(head_point(k, 0.385, 0.08, 0.058), (0.022, 0.04, 0.014), 0.007, axis=k["head_axis"])
    f.bump(head_point(k, 0.43, -0.09, 0.088), (0.03, 0.08, 0.075), 0.012, axis=k["head_axis"])
    f.bump(head_point(k, 0.112, -0.006, 0.046), (0.016, 0.034, 0.022), 0.009, axis=k["head_axis"])
    f.bump(head_point(k, 0.47, 0.09, 0.082), (0.03, 0.035, 0.03), 0.01, axis=k["head_axis"])
    f.bump(head_point(k, 0.24, -0.11, 0.0), (0.024, 0.11, 0.024), -0.008, axis=k["head_axis"])

    f.ellipsoid((0.105, -0.3, 0.675), (0.05, 0.17, 0.115), axis=k["shoulder"] - k["scapula"], blend=0.09)
    f.ridge([point(0.12, -0.235, 0.81), point(0.146, -0.3, 0.7), point(0.145, -0.36, 0.6)], 0.03, 0.006, taper=0.2)
    f.ellipsoid((0.11, -0.3, 0.515), (0.055, 0.1, 0.095), axis=k["elbow"] - k["shoulder"], blend=0.07)
    f.ellipsoid((0.1, -0.365, 0.57), (0.044, 0.044, 0.055), blend=0.05)
    f.ellipsoid((0.055, -0.4, 0.54), (0.058, 0.058, 0.085), blend=0.07, pair=0.06)
    f.ellipsoid((0.095, -0.225, 0.445), (0.034, 0.038, 0.042), blend=0.03)

    f.ellipsoid((0.086, 0.32, 0.63), (0.08, 0.165, 0.118), blend=0.08)
    f.ellipsoid((0.1, 0.31, 0.525), (0.066, 0.15, 0.135), blend=0.08)
    f.ellipsoid((0.066, 0.475, 0.57), (0.056, 0.06, 0.115), blend=0.06, pair=0.03)
    f.ellipsoid((0.05, 0.36, 0.5), (0.045, 0.1, 0.065), blend=0.06, pair=0.04)
    f.bump((0.13, 0.17, 0.63), (0.05, 0.08, 0.1), -0.008)

    top = point(0.095, -0.26, 0.47)
    length = float(numpy.linalg.norm(k["carpus"] - top))
    forearm = [(0.0, 0.0, 0.0, 0.05, 0.072, 0.064), (0.08, 0.0, 0.0, 0.045, 0.06, 0.053), (0.16, 0.0, 0.0, 0.038, 0.043, 0.04), (length, 0.0, 0.0, 0.033, 0.033, 0.035), (length + 0.04, 0.0, 0.0, 0.018, 0.018, 0.018)]
    f.loft(top, k["carpus"] - top, forearm, blend=0.04, group="fore")
    f.ellipsoid(k["carpus"] + point(0.0, -0.002, -0.004), (0.032, 0.034, 0.04), blend=0.02, group="fore")
    length = float(numpy.linalg.norm(k["fetlock_f"] - k["carpus"]))
    f.loft(k["carpus"], k["fetlock_f"] - k["carpus"], [(0.0, 0.0, 0.0, 0.03, 0.03, 0.03), (0.06, 0.0, 0.0, 0.026, 0.029, 0.025), (length, 0.0, 0.0, 0.028, 0.033, 0.027)], blend=0.015, group="fore")
    f.ellipsoid(k["fetlock_f"], (0.029, 0.033, 0.03), blend=0.02, group="fore")
    f.cone(k["fetlock_f"], k["coffin_f"] + point(0.0, -0.003, -0.004), 0.027, 0.0275, blend=0.012, group="fore")

    crown = point(0.095, 0.3, 0.57)
    length = float(numpy.linalg.norm(k["hock"] - crown))
    gaskin = [(0.0, 0.0, 0.0, 0.064, 0.13, 0.125), (0.1, 0.0, 0.0, 0.058, 0.118, 0.138), (0.16, 0.0, 0.0, 0.051, 0.098, 0.128), (0.22, 0.0, 0.0, 0.043, 0.074, 0.09), (0.27, 0.0, 0.0, 0.036, 0.055, 0.05), (length, 0.0, 0.0, 0.033, 0.048, 0.04), (length + 0.04, 0.0, 0.0, 0.018, 0.024, 0.02)]
    f.loft(crown, k["hock"] - crown, gaskin, blend=0.05, group="hind")
    f.ridge([point(0.085, 0.435, 0.44), point(0.085, 0.447, 0.37), k["hock_point"]], 0.015, 0.005, taper=0.15, group="hind")
    f.ellipsoid(k["hock"] + point(0.0, 0.004, -0.004), (0.031, 0.04, 0.05), blend=0.03, group="hind")
    f.ellipsoid(k["hock_point"] + point(0.0, -0.005, -0.005), (0.018, 0.021, 0.032), blend=0.025, group="hind")
    length = float(numpy.linalg.norm(k["fetlock_h"] - k["hock"]))
    f.loft(k["hock"], k["fetlock_h"] - k["hock"], [(0.0, 0.0, 0.0, 0.031, 0.036, 0.03), (0.08, 0.0, 0.0, 0.026, 0.03, 0.025), (length, 0.0, 0.0, 0.028, 0.033, 0.027)], blend=0.02, group="hind")
    f.ellipsoid(k["fetlock_h"], (0.029, 0.033, 0.03), blend=0.02, group="hind")
    f.cone(k["fetlock_h"], k["coffin_h"] + point(0.0, 0.003, -0.004), 0.027, 0.0275, blend=0.012, group="hind")

    f.cone(k["tail"], k["tail_tip"], 0.02, 0.009, blend=0.025, group="tail")
    f.ellipsoid(k["eye"], (0.012, 0.012, 0.012), blend=0.0, group="extra")
    ear_axis = fields.unit((0.45, 0.35, 0.82))
    f.ellipsoid(k["ear"] + ear_axis * 0.06, (0.036, 0.065, 0.01), axis=ear_axis, roll=35.0, blend=0.01, group="extra")
    f.ellipsoid(k["coffin_f"] + point(0.0, -0.01, -0.022), (0.03, 0.036, 0.024), blend=0.0, group="extra")
    f.ellipsoid(k["coffin_h"] + point(0.0, -0.01, -0.022), (0.03, 0.036, 0.024), blend=0.0, group="extra")


def snout_weights(k):
    def apply(result, slot, points, part, coord, model):
        along = (points - k["nose"][None, :]) @ k["head_axis"]
        amount = smooth(0.12, 0.03, along) * numpy.isin(part, ["head", "nose", "nostril", "mouth_upper"]) * (1.0 - result[:, slot["jaw"]])
        result = result * (1.0 - amount)[:, None]
        result[:, slot["snout"]] += amount
        return result

    return apply


def build(kind):
    f = fields.field()
    k = {}
    k["withers"] = point(0.0, -0.24, 0.9)
    k["scapula"] = point(0.05, -0.215, 0.81)
    k["shoulder"] = point(0.1, -0.365, 0.57)
    k["elbow"] = point(0.095, -0.245, 0.435)
    k["carpus"] = point(0.085, -0.31, 0.225)
    k["fetlock_f"] = point(0.085, -0.315, 0.09)
    k["coffin_f"] = point(0.085, -0.335, 0.04)
    k["toe_f"] = point(0.085, -0.378, 0.0)
    k["hip"] = point(0.085, 0.31, 0.635)
    k["stifle"] = point(0.105, 0.205, 0.44)
    k["hock"] = point(0.085, 0.405, 0.275)
    k["hock_point"] = point(0.085, 0.45, 0.305)
    k["fetlock_h"] = point(0.085, 0.385, 0.09)
    k["coffin_h"] = point(0.085, 0.365, 0.04)
    k["toe_h"] = point(0.085, 0.322, 0.0)
    k["neck_top"] = point(0.0, -0.47, 0.64)
    k["neck_base"] = point(0.0, -0.28, 0.62)
    k["nose"] = point(0.0, -0.9, 0.45)
    k["occiput"] = point(0.0, -0.42, 0.665)
    k["head_axis"] = fields.unit(k["occiput"] - k["nose"])
    k["head_up"] = numpy.cross(fields.lateral, k["head_axis"])
    k["eye"] = head_point(k, 0.37, 0.058, 0.066)
    k["ear"] = head_point(k, 0.455, 0.085, 0.078)
    k["jaw"] = head_point(k, 0.43, -0.04, 0.07)
    k["mouth"] = head_point(k, 0.2, -0.03, 0.05)
    k["tail"] = point(0.0, 0.592, 0.66)
    k["tail_tip"] = point(0.0, 0.64, 0.455)
    k["hips"] = point(0.0, 0.2, 0.7)
    k["spine_01"] = point(0.0, 0.13, 0.71)
    k["spine_02"] = point(0.0, -0.01, 0.73)
    k["spine_03"] = point(0.0, -0.15, 0.735)
    k["neck_01"] = point(0.0, -0.31, 0.66)
    k["skull"] = head_point(k, 0.47, 0.0, 0.0)
    k["ribs"] = point(0.14, -0.05, 0.59)
    anatomy(f, k)

    blueprint = {"name": "boar", "rig_name": "boar_rig", "field": f, "marks": k, "scale": 1.0}
    blueprint["bounds"] = (point(-0.4, -1.0, -0.02), point(0.4, 0.75, 1.05))
    blueprint["extent"] = {"length": 1.68, "height": 1.04, "center": -0.13, "body": 1.0}
    blueprint["islands"] = {"head": 1.25, "nose": 1.7, "chin": 1.4, "tusk": 1.2}
    skin = ("core", "fore", "hind", "tail")
    eye_axis = fields.unit((0.85, -0.45, 0.28))
    eye_surface = f.project(numpy.array([head_point(k, 0.37, 0.058, 0.064)]), ("core",))[0]
    ear_root = f.project(numpy.array([head_point(k, 0.455, 0.08, 0.074)]), ("core",))[0]
    k["eye_center"] = eye_surface - eye_axis * (0.012 - 0.002)
    k["ear_root"] = ear_root
    angle = -math.degrees(math.atan2(k["head_axis"][2], k["head_axis"][1]))
    first = head_point(k, 0.35, 0.0)
    second = head_point(k, 0.19, 0.0)
    third = head_point(k, 0.03, 0.0)
    cage = {"around": 32, "core": ("core",), "skin": skin, "head_station": 5}
    cage["spine"] = [(0.52, 0.59, 0.0, 0.04), (0.25, 0.6, 0.0, 0.04), (-0.05, 0.61, 0.0, 0.04), (-0.24, 0.625, 0.0, 0.034), (-0.36, 0.64, -8.5, 0.028), (-0.46, 0.64, -15.2, 0.022), (float(first[1]), float(first[2]), angle, 0.02), (float(second[1]), float(second[2]), angle, 0.017), (float(third[1]), float(third[2]), angle, 0.013)]
    cage["pivots"] = [(3, 6, (-0.24, float(first[2]) - (float(first[1]) + 0.24) / math.tan(math.radians(angle))))]
    cage["legs"] = [
        {"name": "fore", "group": "fore", "around": 16, "limit": 0.41, "path": [((0.09, -0.292, 0.31), 2), ((0.086, -0.305, 0.25), 1), ((0.085, -0.31, 0.225), 1), ((0.085, -0.312, 0.19), 1), ((0.085, -0.314, 0.12), 1), ((0.085, -0.315, 0.09), 1), ((0.085, -0.325, 0.065), 1), ((0.085, -0.338, 0.036), 0)]},
        {"name": "hind", "group": "hind", "around": 16, "limit": 0.48, "path": [((0.088, 0.371, 0.37), 2), ((0.086, 0.392, 0.31), 1), ((0.085, 0.407, 0.275), 1), ((0.085, 0.402, 0.235), 1), ((0.085, 0.393, 0.15), 1), ((0.085, 0.385, 0.09), 1), ((0.085, 0.376, 0.065), 1), ((0.085, 0.368, 0.036), 0)]},
    ]
    cage["eye"] = {"center": k["eye_center"], "axis": eye_axis, "slit": k["head_axis"], "radius": 0.012, "open": (42.0, 27.0), "cells": 1}
    cage["ear"] = {"root": ear_root, "axis": fields.unit((0.45, 0.35, 0.82)), "face": fields.unit((0.62, -0.76, 0.12)), "length": 0.13, "width": 0.092, "around": 12, "cells": (1, 2), "thickness": 0.008, "point": 1.05}
    cage["mouth"] = {"row": 6}
    cage["nostril"] = {"cell": (2, 1), "rows": 2, "cols": 2, "depth": 0.012}
    cage["tail"] = {"cell": (1, 1), "rows": 2, "around": 8, "flat": 0.9, "path": [(0.0, 0.592, 0.66), (0.0, 0.617, 0.638), (0.0, 0.634, 0.565), (0.0, 0.64, 0.455)], "radii": [0.019, 0.017, 0.013, 0.0095]}
    blueprint["cage"] = cage
    blueprint["hoof"] = {"length": 0.062, "width": 0.027, "toe_height": 0.046, "heel_height": 0.03, "dew_offset": 0.019, "dew_back": 0.025, "dew_drop": 0.024, "dew_length": 0.028, "dew_radius": 0.0095}
    tail_path = [numpy.array(p) for p in cage["tail"]["path"]]
    k["snout"] = head_point(k, 0.1, 0.0, 0.0)
    blueprint["bones"] = rigs.quadruped(k, tail_path[:3], [("snout", "head", tuple(k["snout"]))])
    blueprint["rig"] = {
        "axial": ["hips", "spine_01", "spine_02", "spine_03", "neck_01", "neck_02", "neck_03", "head"],
        "axial_widths": [0.0, 0.1, 0.13, 0.13, 0.13, 0.07, 0.07, 0.08],
        "limbs": [
            {"name": "fore", "bones": ["scapula", "humerus", "radius", "cannon", "pastern_f", "hoof_f"], "tip": k["toe_f"], "widths": [0.0, 0.1, 0.08, 0.04, 0.035, 0.02], "reach": [0.15, 0.14, 0.09, 0.055, 0.045, 0.045], "grip": [0.55, 0.85, 1.0, 1.0, 1.0, 1.0]},
            {"name": "hind", "bones": ["femur", "tibia", "metatarsus", "pastern_h", "hoof_h"], "tip": k["toe_h"], "widths": [0.0, 0.11, 0.05, 0.035, 0.02], "reach": [0.17, 0.14, 0.07, 0.045, 0.045], "grip": [0.75, 1.0, 1.0, 1.0, 1.0], "mass": (0.48, 0.66, (0.1, 0.22), (0.5, 0.58), 0.82)},
        ],
        "ribs": {"center": (0.15, -0.04, 0.59), "radii": (0.12, 0.26, 0.2), "amount": 0.55},
        "tail": ["tail_01", "tail_02", "tail_03"],
        "tail_tip": tail_path[3],
        "tail_widths": [0.0, 0.04, 0.05],
        "extra": [snout_weights(k)],
    }
    blueprint["facts"] = {"mass": 95.0, "hull": {"center": (0.0, 0.05, 0.6), "half_length": 0.38, "radius": 0.22}}
    blueprint["motion"] = {
        "prefix": "boar_",
        "nose": k["nose"],
        "skull": k["skull"],
        "breath": 0.009,
        "feed": "root",
        "graze_height": 0.012,
        "graze_tilt": 8.0,
        "graze_drop": -0.03,
        "graze_head": 30.0,
        "graze_step": 0.07,
        "graze_chew": 6.0,
        "alert_neck": 14.0,
        "alert_tail": 55.0,
        "walk": {"kind": "walk", "frames": 20, "speed": 1.2, "duty": {"fore": 0.62, "hind": 0.62}, "phase": {"hind_l": 0.0, "fore_l": 0.25, "hind_r": 0.5, "fore_r": 0.75}, "center": {"fore": (0.0, 0.0, 0.0), "hind": (0.0, -0.01, 0.0)}, "narrow": 0.85, "lift": {"fore": 0.055, "hind": 0.045}, "toe": {"fore": 0.6, "hind": 0.45}, "curl": {"fore": 0.4, "hind": 0.3}, "swing_flex": {"fore": 0.8, "hind": 0.45}, "stance_flex": {"fore": 0.0, "hind": 0.05}, "sink": 0.1, "follow": 0.35, "bob": 0.008, "sway": 0.012, "roll": 2.0, "yaw": 3.0, "nod": 2.2, "tail": 12.0},
        "trot": {"kind": "trot", "frames": 12, "speed": 3.2, "duty": {"fore": 0.4, "hind": 0.4}, "phase": {"hind_l": 0.0, "fore_r": 0.0, "hind_r": 0.5, "fore_l": 0.5}, "center": {"fore": (0.0, -0.01, 0.0), "hind": (0.0, -0.03, 0.0)}, "narrow": 0.75, "lift": {"fore": 0.08, "hind": 0.07}, "toe": {"fore": 0.75, "hind": 0.6}, "curl": {"fore": 0.6, "hind": 0.45}, "swing_flex": {"fore": 1.15, "hind": 0.65}, "stance_flex": {"fore": 0.0, "hind": 0.08}, "sink": 0.16, "follow": 0.45, "bob": 0.016, "roll": 1.5, "yaw": 2.0, "nod": 1.2, "carry": -2.0},
        "run": {"kind": "gallop", "frames": 8, "speed": 9.0, "duty": {"fore": 0.24, "hind": 0.24}, "phase": {"hind_l": 0.0, "hind_r": 0.1, "fore_l": 0.44, "fore_r": 0.56}, "center": {"fore": (0.0, -0.02, 0.0), "hind": (0.0, -0.08, 0.0)}, "narrow": 0.65, "lift": {"fore": 0.12, "hind": 0.11}, "toe": {"fore": 0.9, "hind": 0.7}, "curl": {"fore": 0.8, "hind": 0.6}, "swing_flex": {"fore": 1.6, "hind": 0.9}, "stance_flex": {"fore": 0.0, "hind": 0.12}, "sink": 0.25, "follow": 0.6, "bob": 0.035, "roll": 1.5, "flex": 10.0, "nod": 3.0, "hover": -0.015, "carry": -4.0, "flag": 70.0},
        "attack": {"seconds": 0.8, "hit": 0.36, "reach": 0.2, "crouch": -0.03, "dip": 6.0, "neck_down": -12.0, "neck_up": 24.0, "head_down": -14.0, "head_up": 34.0, "twist": 14.0, "roll": 16.0, "jaw": 12.0, "rear": 6.0, "rise": 0.04},
        "rest": {"hips": -0.33, "pitch": 1.5, "fore": (0.0, 0.0, -78.0, 150.0, 20.0, 0.0), "hind": (-52.0, 70.0, -95.0, 16.0, 0.0), "neck": -4.0, "head": 6.0, "hind_spread": 16.0},
        "death": {"side": 0.26, "drop": -0.52, "neck": -6.0, "head": 8.0, "neck_yaw": -4.0, "head_yaw": 0.0, "head_roll": 0.0, "droop": -14.0, "fore_upper": (0.0, 5.0, -14.0, 36.0, 18.0, 8.0), "fore_lower": (0.0, 0.0, -6.0, 22.0, 12.0, 6.0), "hind_upper": (-14.0, 24.0, -18.0, 14.0, 8.0), "hind_lower": (-8.0, 14.0, -10.0, 10.0, 6.0)},
    }
    return blueprint


def pieces(blueprint):
    k = blueprint["marks"]
    f = blueprint["field"]
    result = [parts.eyeball(blueprint["cage"]["eye"])]
    result.append(parts.mirrored(result[0]))
    result.extend(parts.hooves(k, blueprint["hoof"]))
    lower = parts.sweep([head_point(k, 0.114, -0.04, 0.024), head_point(k, 0.105, -0.018, 0.044), head_point(k, 0.105, 0.004, 0.057), head_point(k, 0.115, 0.022, 0.063), head_point(k, 0.133, 0.034, 0.063)], [0.0105, 0.0105, 0.009, 0.0062, 0.0025], 6, "tusk", "jaw", "tusk", smooth=8, mark=1.0)
    upper = parts.sweep([head_point(k, 0.13, -0.014, 0.034), head_point(k, 0.125, -0.008, 0.054), head_point(k, 0.127, 0.006, 0.065), head_point(k, 0.132, 0.02, 0.068)], [0.009, 0.0088, 0.007, 0.0028], 6, "tusk", "head", "tusk", smooth=6, mark=1.0)
    result.extend([lower, parts.mirrored(lower), upper, parts.mirrored(upper)])
    seeds = []
    for row, y in enumerate(numpy.linspace(-0.5, 0.52, 58)):
        crest = min(math.exp(-((y + 0.26) / 0.2) ** 2) + 0.35 * math.exp(-((y + 0.02) / 0.25) ** 2), 1.0)
        seeds.append({"origin": (0.004, float(y), 0.64), "ray": (0.0, 0.0, 1.0), "facing": (1.0, 0.0, 0.12), "flow": (0.0, 1.0, 0.0), "lean": 24.0 + 12.0 * crest, "length": 0.06 + 0.085 * crest, "width": 0.042, "thick": 0.011, "rise": 0.14, "lift": 0.003, "sag": 0.0, "spread": 8.0})
    result.extend(parts.tufts(f, blueprint["cage"]["skin"], seeds, 11))
    tip = numpy.array(blueprint["cage"]["tail"]["path"][-1])
    brush = []
    for angle in (-90.0, -45.0, 0.0, 45.0, 90.0):
        out = numpy.array([math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0.0])
        brush.append({"root": tip + out * 0.006 + numpy.array([0.0, 0.0, 0.03]), "normal": out, "flow": (0.0, 0.0, -1.0), "length": 0.1, "width": 0.02, "thick": 0.009, "rise": 0.14, "sag": 0.0, "spread": 8.0})
    result.extend(parts.tufts(f, blueprint["cage"]["skin"], brush, 12))
    return result


def coat(c, m):
    k = m.k
    p = m.p
    n = m.n
    count = m.count
    skin = m.body | m.head
    headness = smooth(-0.34, -0.54, p[:, 1])
    flow = m.flow(body=(0.0, 1.0, -0.35), neck_start=-8.0, neck_end=-9.0)
    forward = k["head_axis"] + numpy.array([0.0, 0.0, -0.2])
    flow[skin] = numpy.array([0.0, 1.0, -0.35])[None, :] * (1.0 - headness[skin])[:, None] + forward[None, :] * headness[skin][:, None]
    crest = m.lock & (p[:, 2] > 0.56)
    flow[crest] = numpy.array([0.0, 0.87, 0.49])
    flow[m.lock & ~crest] = numpy.array([0.0, 0.0, -1.0])
    fine = c.fur(flow, 0.0045, 0.0016, 12, 1)
    coarse = c.fur(flow, 0.011, 0.0032, 15, 2)
    fur = fine * 0.5 + coarse * 0.5
    mottle = paint.fbm(p, 0.12, 3, 11)
    color = numpy.tile(numpy.array([0.185, 0.152, 0.125]), (count, 1))
    color = coats.tint(color, (0.3, 0.25, 0.195), smooth(0.35, 0.7, mottle) * 0.55)
    up = n[:, 2]
    trunk = (m.body | m.rump | m.tail | m.head).astype(numpy.float64)
    dorsal = numpy.exp(-(p[:, 0] / 0.06) ** 2) * smooth(0.3, 0.85, up) * trunk * smooth(-0.62, -0.5, p[:, 1])
    color = coats.tint(color, (0.085, 0.07, 0.06), dorsal * 0.75)
    flank = smooth(0.25, -0.45, up) * trunk * smooth(-0.4, -0.1, p[:, 1]) * smooth(0.62, 0.45, p[:, 1])
    color = coats.tint(color, (0.37, 0.315, 0.25), flank * 0.4)
    under = smooth(-0.3, -0.85, up + (mottle - 0.5) * 0.3) * smooth(0.26, 0.36, p[:, 2])
    color = coats.tint(color, (0.33, 0.28, 0.23), under * 0.55)
    lower = smooth(0.34, 0.1, p[:, 2])
    color = coats.tint(color, (0.075, 0.065, 0.06), lower * 0.85)
    cheek = smooth(0.18, 0.36, m.along) * smooth(0.6, 0.44, m.along) * smooth(0.35, -0.35, n @ k["head_up"]) * smooth(0.0, 0.05, numpy.abs(p[:, 0]))
    color = coats.tint(color, (0.4, 0.345, 0.28), cheek * 0.5)
    snout = smooth(0.17, 0.03, m.along)
    color = coats.tint(color, (0.1, 0.082, 0.075), snout * 0.85)
    disc = numpy.maximum(c.tagged("nose").astype(numpy.float64), smooth(0.012, 0.004, m.along))
    color = coats.tint(color, (0.13, 0.095, 0.09), disc * 0.92)
    blush = smooth(0.03, 0.012, numpy.linalg.norm(m.mirrored - head_point(k, 0.0, 0.002, 0.014)[None, :], axis=1)) * disc
    color = coats.tint(color, (0.24, 0.15, 0.14), blush * 0.55)
    dried = smooth(0.48, 0.72, paint.fbm(p, 0.05, 4, 21))
    mud = dried * numpy.maximum(smooth(0.4, 0.08, p[:, 2]), smooth(0.2, 0.04, m.along) * 0.8) * (1.0 - disc)
    color = coats.tint(color, (0.3, 0.245, 0.18), mud * 0.6)
    rim = m.ears * smooth(0.02, 0.24, m.ear_along)
    color = coats.tint(color, (0.13, 0.108, 0.095), rim * 0.9)
    color = coats.tint(color, (0.33, 0.235, 0.205), m.ear_inner * smooth(0.06, 0.3, m.ear_along) * smooth(1.0, 0.6, m.ear_along) * 0.6)
    color = coats.tint(color, (0.09, 0.075, 0.07), m.tail * smooth(0.56, 0.3, p[:, 2]) * 0.7)
    bristle = numpy.array([0.075, 0.062, 0.055])[None, :] + numpy.array([0.33, 0.285, 0.22])[None, :] * smooth(0.25, 1.0, c.coord[:, 0])[:, None]
    color[m.lock] = bristle[m.lock]
    shade = 0.66 + 0.6 * fur + (mottle - 0.5) * 0.12
    color = numpy.where(m.furry[:, None], color * shade[:, None], color)
    tips = smooth(0.5, 0.82, fine) * m.furry * (1.0 - disc) * (1.0 - snout * 0.7) * (1.0 - lower * 0.6)
    color = coats.tint(color, (0.47, 0.41, 0.33), tips * 0.24)

    rough = numpy.full(count, 0.82)
    rough[m.furry] = 0.74 + 0.18 * (1.0 - fur[m.furry])
    rough = rough + (0.3 - rough) * disc
    rough = rough + 0.06 * mud
    relief = 0.0011 + 0.0011 * smooth(0.25, 0.46, p[:, 2]) * (1.0 - 0.45 * headness)
    relief = relief * (1.0 - 0.5 * rim)
    relief = relief * (1.0 - disc)
    m.cavity(color, rough, relief, flesh=(0.42, 0.2, 0.19), dark=(0.04, 0.025, 0.025), lip=(0.12, 0.08, 0.075))
    m.keratin(color, rough, relief, wall=(0.085, 0.075, 0.068), wear=(0.27, 0.22, 0.17), under=(0.2, 0.17, 0.14))
    tusk = c.tagged("tusk")
    if tusk.any():
        stain = numpy.array([0.46, 0.36, 0.22])[None, :] * (0.8 + 0.3 * coarse)[:, None]
        ivory = coats.tint(stain, (0.8, 0.75, 0.6), smooth(0.2, 0.8, c.coord[:, 0]))
        color[tusk] = ivory[tusk]
        rough[tusk] = 0.34
        relief[tusk] = 0.0003
    m.eyes(color, rough, relief, iris=(0.16, 0.09, 0.045), wide=0.45, tall=0.45, skin=(0.08, 0.06, 0.055))
    return {"color": numpy.clip(color, 0.0, 1.0), "rough": numpy.clip(rough, 0.04, 1.0), "height": fur, "relief": relief}
