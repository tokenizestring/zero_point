import math
import numpy as np
from fauna_hunters_mesh import *


class HeadFrame:
    def __init__(self, origin, pitch):
        self.origin = np.array([0.0, origin[0], origin[1]])
        angle = math.radians(pitch)
        self.axis = np.array([0.0, -math.cos(angle), -math.sin(angle)])
        self.up = np.array([0.0, -math.sin(angle), math.cos(angle)])
        self.side = np.array([1.0, 0.0, 0.0])

    def point(self, u, v, x=0.0):
        return self.origin + self.axis * u + self.up * v + self.side * x

    def yz(self, u, v):
        p = self.point(u, v)
        return (p[1], p[2])

    def vector(self, forward, up, side=0.0):
        return self.axis * forward + self.up * up + self.side * side

    def local(self, points):
        d = np.asarray(points, dtype=np.float64) - self.origin[None, :]
        return d @ self.axis, d @ self.up, d[:, 0]


def wolf():
    head = HeadFrame((-0.590, 0.850), 13.0)
    half = 18
    keys = [
        {"name": "rump", "top": (0.478, 0.702), "bot": (0.470, 0.575), "w": 0.042, "c": 0.5, "n": 2},
        {"name": "croup", "top": (0.450, 0.738), "bot": (0.440, 0.500), "w": 0.080, "c": 0.55, "n": 3},
        {"name": "hip", "top": (0.360, 0.768), "bot": (0.335, 0.480), "w": 0.098, "c": 0.56, "n": 6},
        {"name": "loin", "top": (0.170, 0.778), "bot": (0.165, 0.530), "w": 0.088, "c": 0.56, "e": 0.08, "n": 5},
        {"name": "ribs", "top": (0.000, 0.782), "bot": (0.000, 0.470), "w": 0.106, "c": 0.56, "e": 0.14, "nb": 1.9, "n": 6},
        {"name": "chest", "top": (-0.200, 0.790), "bot": (-0.200, 0.428), "w": 0.110, "c": 0.57, "e": 0.2, "nb": 1.75, "n": 5},
        {"name": "withers", "top": (-0.335, 0.806), "bot": (-0.385, 0.447), "w": 0.104, "c": 0.57, "e": 0.18, "nb": 1.75, "n": 3},
        {"name": "neckbase", "top": (-0.405, 0.828), "bot": (-0.478, 0.540), "w": 0.098, "c": 0.5, "e": 0.05, "n": 3, "region": REG_NECK},
        {"name": "neck", "top": (-0.492, 0.882), "bot": (-0.576, 0.655), "w": 0.090, "c": 0.5, "n": 3, "region": REG_NECK},
        {"name": "occiput", "top": head.yz(-0.020, 0.078), "bot": head.yz(0.035, -0.098), "w": 0.080, "c": 0.5, "nt": 2.4, "n": 4, "region": REG_HEAD},
        {"name": "cranium", "top": head.yz(0.036, 0.090), "bot": head.yz(0.070, -0.096), "w": 0.088, "c": 0.46, "nt": 2.8, "e": 0.10, "n": 4, "region": REG_HEAD},
        {"name": "brow", "top": head.yz(0.088, 0.087), "bot": head.yz(0.104, -0.088), "w": 0.080, "c": 0.44, "nt": 3.0, "e": 0.12, "n": 3, "region": REG_HEAD},
        {"name": "eye", "top": head.yz(0.124, 0.072), "bot": head.yz(0.130, -0.076), "w": 0.066, "c": 0.44, "nt": 3.0, "e": 0.10, "n": 3, "region": REG_HEAD},
        {"name": "corner", "top": head.yz(0.156, 0.053), "bot": head.yz(0.156, -0.066), "w": 0.050, "c": 0.54, "nt": 2.6, "n": 3, "region": REG_HEAD},
        {"name": "muzzle1", "top": head.yz(0.188, 0.045), "bot": head.yz(0.188, -0.055), "w": 0.0445, "c": 0.55, "nt": 2.8, "n": 3, "region": REG_HEAD},
        {"name": "muzzle2", "top": head.yz(0.230, 0.041), "bot": head.yz(0.230, -0.046), "w": 0.041, "c": 0.52, "nt": 2.8, "n": 3, "region": REG_HEAD},
        {"name": "chin", "top": head.yz(0.270, 0.038), "bot": head.yz(0.266, -0.037), "w": 0.036, "c": 0.5, "nt": 2.8, "n": 1, "region": REG_HEAD},
        {"name": "nose", "top": head.yz(0.284, 0.035), "bot": head.yz(0.277, -0.028), "w": 0.030, "c": 0.45, "nt": 2.8, "n": 1, "region": REG_HEAD},
        {"name": "nosetip", "top": head.yz(0.294, 0.029), "bot": head.yz(0.283, -0.026), "w": 0.022, "c": 0.45, "nt": 2.6, "region": REG_HEAD},
    ]
    body = {"keys": keys, "half": half, "rear_cap": 0.018, "head_seam": "occiput", "mouth": {"corner": "corner", "chin": "nose", "lip": 11, "rows": 3, "depth": 0.014, "gum": 0.008, "arch": 0.007, "gum_low": 0.006, "dip": 0.004, "nose_cap": 0.006, "nose_lift": 0.007, "chin_cap": 0.006, "ramp": 3.0, "jaw_back": 5.0, "inset": 0.0008}}
    eye = {"center": head.point(0.128, 0.030, 0.037), "radius": 0.0165, "gaze": head.vector(0.72, 0.26, 0.64), "slant": -18.0, "width": 0.0125, "upper": 0.0072, "lower": 0.0054, "patch": (3, 3)}
    ear = {"base": head.point(0.030, 0.074, 0.062), "axis": head.vector(-0.12, 0.90, 0.42), "facing": head.vector(0.82, 0.05, 0.57), "height": 0.118, "width": 0.036, "patch": (4, 3), "cup": 0.020, "thick": 0.006, "flare": 0.08}
    fore = {
        "patch": {"center": (0.082, -0.338, 0.515), "size": (5, 4)},
        "blend": 2, "bulge": 0.006, "cap": 0.008,
        "keys": [
            {"p": (0.082, -0.338, 0.478), "df": 0.062, "db": 0.066, "hw": 0.038, "n": 2},
            {"p": (0.084, -0.328, 0.428), "df": 0.044, "db": 0.058, "hw": 0.033, "n": 2},
            {"p": (0.084, -0.330, 0.385), "df": 0.036, "db": 0.042, "hw": 0.029, "n": 2},
            {"p": (0.084, -0.332, 0.335), "df": 0.031, "db": 0.033, "hw": 0.026, "n": 3, "count": 12},
            {"p": (0.084, -0.334, 0.255), "df": 0.025, "db": 0.025, "hw": 0.0225, "n": 3},
            {"p": (0.084, -0.337, 0.185), "df": 0.022, "db": 0.022, "hw": 0.0215, "n": 1},
            {"p": (0.084, -0.340, 0.152), "df": 0.0235, "db": 0.027, "hw": 0.024, "n": 2},
            {"p": (0.084, -0.346, 0.100), "df": 0.020, "db": 0.021, "hw": 0.024, "n": 2},
            {"p": (0.084, -0.354, 0.054), "df": 0.024, "db": 0.026, "hw": 0.030, "n": 1},
            {"p": (0.084, -0.364, 0.036), "dir": (0.0, -0.75, -0.66), "df": 0.026, "db": 0.030, "hw": 0.038, "n": 1},
            {"p": (0.084, -0.387, 0.027), "dir": (0.0, -1.0, -0.1), "df": 0.024, "db": 0.027, "hw": 0.043, "nb": 3.0, "n": 1},
            {"p": (0.084, -0.410, 0.022), "dir": (0.0, -1.0, -0.15), "df": 0.020, "db": 0.022, "hw": 0.040, "nb": 3.0},
        ],
        "paw": {"bone": "forepaw_l", "claw": 0.017, "toes": [
            {"x": -0.030, "len": 0.034, "rad": 0.0118, "back": -0.026, "splay": -0.2},
            {"x": -0.0108, "len": 0.044, "rad": 0.0128, "back": -0.013, "splay": -0.05},
            {"x": 0.0108, "len": 0.044, "rad": 0.0128, "back": -0.013, "splay": 0.05},
            {"x": 0.030, "len": 0.034, "rad": 0.0118, "back": -0.026, "splay": 0.2},
        ]},
    }
    hind = {
        "patch": {"center": (0.090, 0.360, 0.570), "size": (7, 4)},
        "blend": 2, "bulge": 0.008, "cap": 0.008,
        "keys": [
            {"p": (0.090, 0.362, 0.575), "df": 0.105, "db": 0.092, "hw": 0.040, "n": 2},
            {"p": (0.094, 0.345, 0.515), "df": 0.100, "db": 0.090, "hw": 0.043, "n": 2},
            {"p": (0.096, 0.320, 0.455), "df": 0.082, "db": 0.082, "hw": 0.040, "n": 2},
            {"p": (0.095, 0.322, 0.405), "df": 0.062, "db": 0.068, "hw": 0.034, "n": 2},
            {"p": (0.093, 0.345, 0.355), "df": 0.042, "db": 0.052, "hw": 0.028, "n": 2, "count": 12},
            {"p": (0.090, 0.385, 0.290), "df": 0.028, "db": 0.038, "hw": 0.023, "n": 2},
            {"p": (0.088, 0.415, 0.240), "df": 0.021, "db": 0.032, "hw": 0.019, "n": 1},
            {"p": (0.087, 0.431, 0.207), "df": 0.021, "db": 0.034, "hw": 0.021, "n": 2},
            {"p": (0.086, 0.429, 0.170), "df": 0.020, "db": 0.025, "hw": 0.020, "n": 2},
            {"p": (0.085, 0.419, 0.100), "df": 0.0185, "db": 0.020, "hw": 0.021, "n": 2},
            {"p": (0.085, 0.409, 0.054), "df": 0.021, "db": 0.024, "hw": 0.027, "n": 1},
            {"p": (0.085, 0.399, 0.035), "dir": (0.0, -0.75, -0.66), "df": 0.024, "db": 0.028, "hw": 0.034, "n": 1},
            {"p": (0.085, 0.377, 0.026), "dir": (0.0, -1.0, -0.1), "df": 0.022, "db": 0.026, "hw": 0.039, "nb": 3.0, "n": 1},
            {"p": (0.085, 0.356, 0.021), "dir": (0.0, -1.0, -0.15), "df": 0.019, "db": 0.021, "hw": 0.036, "nb": 3.0},
        ],
        "paw": {"bone": "hindpaw_l", "claw": 0.015, "toes": [
            {"x": -0.027, "len": 0.032, "rad": 0.0108, "back": -0.024, "splay": -0.18},
            {"x": -0.0098, "len": 0.041, "rad": 0.0118, "back": -0.012, "splay": -0.05},
            {"x": 0.0098, "len": 0.041, "rad": 0.0118, "back": -0.012, "splay": 0.05},
            {"x": 0.027, "len": 0.032, "rad": 0.0108, "back": -0.024, "splay": 0.18},
        ]},
    }
    tail = {
        "patch": {"center": (0.0, 0.462, 0.728), "size": (3, 3)},
        "cap": 0.014,
        "keys": [
            {"p": (0.492, 0.705), "rt": 0.040, "rb": 0.040, "rw": 0.040, "n": 2},
            {"p": (0.525, 0.655), "rt": 0.050, "rb": 0.050, "rw": 0.048, "n": 3},
            {"p": (0.556, 0.575), "rt": 0.058, "rb": 0.058, "rw": 0.055, "n": 3},
            {"p": (0.574, 0.475), "rt": 0.058, "rb": 0.062, "rw": 0.056, "n": 3},
            {"p": (0.580, 0.385), "rt": 0.050, "rb": 0.054, "rw": 0.050, "n": 2},
            {"p": (0.580, 0.315), "rt": 0.035, "rb": 0.037, "rw": 0.035, "n": 1},
            {"p": (0.579, 0.275), "rt": 0.016, "rb": 0.016, "rw": 0.016},
        ],
    }
    teeth = {
        "inset": 0.002,
        "upper": [
            {"at": 0.10, "len": 0.007, "rad": 0.0042, "flat": 0.6},
            {"at": 0.20, "len": 0.011, "rad": 0.0062, "flat": 0.55},
            {"at": 0.32, "len": 0.008, "rad": 0.0042, "flat": 0.55},
            {"at": 0.42, "len": 0.007, "rad": 0.0036, "flat": 0.55},
            {"at": 0.52, "len": 0.006, "rad": 0.0030, "flat": 0.6},
            {"at": 0.70, "len": 0.022, "rad": 0.0050, "rake": -0.12, "hook": -0.004, "sides": 6, "in": 0.003, "splay": -0.14},
            {"at": 0.80, "x": 0.0135, "len": 0.009, "rad": 0.0026, "sides": 4},
            {"at": 0.82, "x": 0.0082, "len": 0.008, "rad": 0.0023, "sides": 4},
            {"at": 0.835, "x": 0.0030, "len": 0.008, "rad": 0.0023, "sides": 4},
        ],
        "lower": [
            {"at": 0.12, "len": 0.006, "rad": 0.0042, "flat": 0.6},
            {"at": 0.25, "len": 0.010, "rad": 0.0060, "flat": 0.55},
            {"at": 0.39, "len": 0.007, "rad": 0.0040, "flat": 0.55},
            {"at": 0.51, "len": 0.006, "rad": 0.0034, "flat": 0.55},
            {"at": 0.62, "len": 0.005, "rad": 0.0028, "flat": 0.6},
            {"at": 0.80, "len": 0.019, "rad": 0.0046, "rake": -0.1, "hook": -0.003, "sides": 6, "in": 0.003, "splay": -0.1},
            {"at": 0.91, "x": 0.0115, "len": 0.007, "rad": 0.0023, "sides": 4},
            {"at": 0.93, "x": 0.0070, "len": 0.006, "rad": 0.0021, "sides": 4},
            {"at": 0.94, "x": 0.0026, "len": 0.006, "rad": 0.0021, "sides": 4},
        ],
    }
    tongue = {"width": 0.0135, "thick": 0.004, "lift": 0.003, "reach": 0.88, "sides": 8}
    bumps = [
        {"center": (0.100, -0.360, 0.610), "radii": (0.06, 0.085, 0.13), "amount": 0.013},
        {"center": (0.085, -0.445, 0.585), "radii": (0.05, 0.05, 0.06), "amount": 0.010},
        {"center": (0.095, -0.275, 0.505), "radii": (0.05, 0.06, 0.07), "amount": 0.008},
        {"center": (0.110, -0.215, 0.610), "radii": (0.05, 0.045, 0.10), "amount": -0.005},
        {"center": (0.105, 0.385, 0.560), "radii": (0.06, 0.10, 0.12), "amount": 0.014},
        {"center": (0.060, 0.300, 0.745), "radii": (0.04, 0.05, 0.03), "amount": 0.005},
        {"center": (0.090, 0.200, 0.630), "radii": (0.05, 0.06, 0.07), "amount": -0.007},
        {"center": (0.0, -0.330, 0.805), "radii": (0.05, 0.08, 0.03), "amount": 0.007},
        {"center": (0.0, -0.475, 0.560), "radii": (0.05, 0.04, 0.06), "amount": 0.010},
        {"center": head.point(0.118, 0.056, 0.032), "radii": (0.020, 0.026, 0.012), "amount": 0.004},
        {"center": head.point(0.088, -0.004, 0.074), "radii": (0.02, 0.04, 0.018), "amount": 0.005},
        {"center": head.point(0.070, -0.045, 0.072), "radii": (0.025, 0.035, 0.03), "amount": 0.004},
        {"center": head.point(0.128, 0.064, 0.0), "radii": (0.012, 0.03, 0.02), "amount": -0.003},
        {"center": head.point(0.238, -0.002, 0.032), "radii": (0.014, 0.025, 0.016), "amount": 0.003},
    ]
    def in_region(data, *regions):
        return np.isin(data["region"], regions).astype(np.float64)

    def band(values, low, high, soft):
        return smoothstep(low - soft, low + soft, values) * (1.0 - smoothstep(high - soft, high + soft, values))

    def cheek(data):
        u, v, x = head.local(data["p"])
        return in_region(data, REG_HEAD) * band(u, 0.0, 0.105, 0.015) * band(v, -0.10, 0.02, 0.015) * smoothstep(0.035, 0.06, np.abs(x))

    def mane(data):
        p = data["p"]
        return in_region(data, REG_NECK, REG_BODY) * band(p[:, 1], -0.60, -0.20, 0.04) * smoothstep(-0.2, 0.2, data["around"])

    def throat(data):
        p = data["p"]
        return in_region(data, REG_NECK, REG_BODY) * band(p[:, 1], -0.62, -0.33, 0.03) * (1.0 - smoothstep(-0.3, 0.1, data["around"]))

    def crest(data):
        p = data["p"]
        return in_region(data, REG_BODY) * band(p[:, 1], -0.22, 0.40, 0.05) * smoothstep(0.55, 0.9, data["around"])

    def belly(data):
        p = data["p"]
        return in_region(data, REG_BODY) * band(p[:, 1], -0.30, 0.28, 0.04) * (1.0 - smoothstep(-0.9, -0.6, data["around"]))

    def feather(data):
        p = data["p"]
        return in_region(data, REG_FORE) * smoothstep(-0.335, -0.315, p[:, 1]) * band(p[:, 2], 0.17, 0.46, 0.03)

    def trousers(data):
        p = data["p"]
        return in_region(data, REG_HIND, REG_BODY) * smoothstep(0.37, 0.41, p[:, 1]) * band(p[:, 2], 0.30, 0.66, 0.04)

    def brush(data):
        return in_region(data, REG_TAIL) * smoothstep(0.02, 0.08, data["s"])

    fur = [
        {"mask": cheek, "density": 1100.0, "length": 0.062, "width": 0.017, "lift": 30.0, "direction": (0.55, 0.75, -0.4), "steer": 0.75, "hug": 0.1, "droop": 0.1},
        {"mask": mane, "density": 420.0, "length": 0.060, "width": 0.020, "lift": 17.0, "hug": 0.18, "droop": 0.08},
        {"mask": throat, "density": 480.0, "length": 0.055, "width": 0.019, "lift": 20.0, "direction": (0.0, 0.45, -0.9), "steer": 0.6, "hug": 0.1, "droop": 0.25},
        {"mask": crest, "density": 230.0, "length": 0.045, "width": 0.017, "lift": 11.0, "hug": 0.15, "droop": 0.0},
        {"mask": belly, "density": 380.0, "length": 0.040, "width": 0.016, "lift": 24.0, "direction": (0.0, 0.8, -0.6), "steer": 0.5, "hug": 0.0, "droop": 0.3},
        {"mask": feather, "density": 520.0, "length": 0.034, "width": 0.012, "lift": 24.0, "direction": (0.0, 0.5, -0.87), "steer": 0.6, "hug": 0.1, "droop": 0.2},
        {"mask": trousers, "density": 520.0, "length": 0.055, "width": 0.018, "lift": 22.0, "direction": (0.0, 0.5, -0.87), "steer": 0.6, "hug": 0.1, "droop": 0.2},
        {"mask": brush, "density": 620.0, "length": 0.085, "width": 0.024, "lift": 24.0, "hug": 0.12, "droop": 0.05},
    ]
    return {"name": "wolf", "head": {"frame": head, "forward": head.axis}, "body": body, "eyes": [eye], "ears": [ear], "legs": {"fore": fore, "hind": hind}, "tail": tail, "teeth": teeth, "tongue": tongue, "bumps": bumps, "fur": fur}


species = {"wolf": wolf}
