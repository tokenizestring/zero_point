import importlib
import numpy
import fauna_hoofed_field as fields

names = {"deer_stag": ("fauna_hoofed_deer", "stag"), "deer_hind": ("fauna_hoofed_deer", "hind"), "boar": ("fauna_hoofed_boar", "boar"), "cow": ("fauna_hoofed_cow", "cow"), "sheep": ("fauna_hoofed_sheep", "sheep")}


def point(x, y, z):
    return numpy.array([x, y, z], dtype=numpy.float64)


def torso(f, rows, blend=0.0, group="core"):
    stations = [(y, 0.0, wide, w, top - wide, wide - bottom, nu, nd) for y, top, bottom, wide, w, nu, nd in rows]
    return f.loft((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), stations, blend=blend, group=group)


def head_point(k, s, v, x=0.0):
    return k["nose"] + k["head_axis"] * s + k["head_up"] * v + numpy.array([x, 0.0, 0.0])


def build(name):
    module, kind = names[name]
    return importlib.import_module(module).build(kind)


def pieces(name, blueprint):
    module, kind = names[name]
    return importlib.import_module(module).pieces(blueprint)
