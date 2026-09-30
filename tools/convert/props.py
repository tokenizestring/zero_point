import bpy
import bmesh
import math
import os
import random
import sys
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gunkit as k
import turntable
from gunkit import v

arguments = sys.argv[sys.argv.index("--") + 1:]
source_root = arguments[0]
output_root = arguments[1]
preview_root = arguments[2]
wanted = arguments[3].split(",")
mode = arguments[4] if len(arguments) > 4 else "preview"
views = arguments[5].split(",") if len(arguments) > 5 else ["three", "front", "back"]
samples = int(arguments[6]) if len(arguments) > 6 else 48
only = arguments[7].split(",") if len(arguments) > 7 else []
hdri = os.path.join(os.path.dirname(output_root), "hdri", "kloofendal_overcast_puresky_4k.hdr")

k.roots["source"] = source_root
k.roots["raw"] = os.path.dirname(output_root)


def turned(center, yaw=0.0, pitch=0.0, roll=0.0):
    return Matrix.Translation(center) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'Y') @ Matrix.Rotation(roll, 4, 'X')


def block(target, look, center, size, yaw=0.0, pitch=0.0, roll=0.0, bevel=0.004, segments=2):
    target.add(k.box(*size), look, turned(center, yaw, pitch, roll), bevel, segments, 40.0)


def rod(target, look, start, end, radius, sides=16, bevel=0.0):
    axis = end - start
    target.add(k.revolve([(0.0, 0.0), (radius, 0.0), (radius, axis.length), (0.0, axis.length)], sides), look, k.axis_frame(start, axis), bevel, 1)


def ball(target, look, center, radius):
    target.add(k.sphere(radius, 16, 10), look, k.place(center))


def nail(target, center):
    k.screw(target, center, v(0.0, 0.0, -1.0), 0.0045, "iron", False, 0.35)


def bolt_through(target, start, end, across, look="zinc"):
    direction = (end - start).normalized()
    k.hex_head(target, start, direction, across, across * 0.42, look)
    k.nut(target, end, direction, across, across * 0.48, across * 0.3, across * 0.25, look)


def angle_iron(target, look, center, length, axis, turn, size=0.05, wall=0.005):
    outline = [(0.0, 0.0), (size, 0.0), (size, wall), (wall, wall), (wall, size), (0.0, size)]
    piece = k.extrude(outline, length, "z")
    k.shifted(piece, -size * 0.5, -size * 0.5, 0.0)
    rotation = Matrix.Rotation(turn, 4, 'Z')
    if axis == "x":
        rotation = Matrix.Rotation(math.pi * 0.5, 4, 'Y') @ Matrix.Rotation(turn, 4, 'Z')
    elif axis == "y":
        rotation = Matrix.Rotation(-math.pi * 0.5, 4, 'X') @ Matrix.Rotation(turn, 4, 'Z')
    target.add(piece, look, Matrix.Translation(center) @ rotation, 0.001, 1)


def saw(target, center, yaw):
    blade = k.extrude([(0.0, 0.0), (0.46, 0.016), (0.46, 0.085), (0.0, 0.118)], 0.0012, "z")
    target.add(blade, "steel", turned(center, yaw), 0.0004, 1)
    grip = k.fillet([(-0.14, -0.01), (0.02, 0.0), (0.02, 0.13), (-0.14, 0.13), (-0.16, 0.06)], [0.01, 0.008, 0.008, 0.02, 0.03], 4)
    hole = [k.shifted(k.extrude(k.fillet([(-0.1, 0.035), (-0.02, 0.035), (-0.02, 0.095), (-0.1, 0.095)], 0.018, 4), 0.06, "z"), 0.0, 0.0, 0.0)]
    target.add(k.cut(k.extrude(grip, 0.022, "z"), hole), "wood", turned(center + Matrix.Rotation(yaw, 3, 'Z') @ v(0.0, 0.0, 0.0105), yaw), 0.003, 2)
    for offset in (0.03, 0.09):
        k.screw(target, center + Matrix.Rotation(yaw, 3, 'Z') @ v(-0.03, offset, 0.022), v(0.0, 0.0, -1.0), 0.005, "brass", True)


def hammer(target, center, yaw):
    handle = k.revolve([(0.0, 0.0), (0.014, 0.0), (0.016, 0.1), (0.013, 0.26), (0.011, 0.3), (0.0, 0.3)], 14)
    target.add(handle, "wood", turned(center, yaw))
    head = k.fillet([(-0.012, -0.055), (0.012, -0.055), (0.014, 0.03), (0.02, 0.055), (-0.02, 0.055), (-0.014, 0.03)], [0.002, 0.002, 0.004, 0.003, 0.003, 0.004], 3)
    tip = center + Matrix.Rotation(yaw, 3, 'Z') @ v(0.31, 0.0, -0.003)
    target.add(k.extrude(head, 0.026, "z"), "iron", turned(tip, yaw), 0.002, 2)


def tin_of_nails(target, center, rng, count=18, radius=0.045, height=0.11):
    target.add(k.revolve([(0.0, 0.0), (radius, 0.0), (radius, height), (radius - 0.002, height), (radius - 0.002, 0.004), (0.0, 0.004)], 32), "zinc", k.place(center, v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)), 0.0008, 1)
    target.add(k.revolve([(radius - 0.0005, height - 0.012), (radius + 0.0012, height - 0.012), (radius + 0.0012, height - 0.004), (radius - 0.0005, height - 0.004)], 32), "zinc", k.place(center, v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)))
    for index in range(count):
        angle = rng.uniform(0.0, math.tau)
        spread = rng.uniform(0.0, radius * 0.7)
        base = center + v(math.cos(angle) * spread, math.sin(angle) * spread, height * 0.45)
        lean = v(rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35), 1.0).normalized()
        rod(target, "iron", base, base + lean * rng.uniform(0.07, 0.1), 0.0018, 6)
        target.add(k.revolve([(0.0, 0.0), (0.0042, 0.0), (0.0042, 0.0012), (0.0, 0.0012)], 10), "iron", k.axis_frame(base + lean * 0.1, lean))


def rope_coil(target, center, radius, turns, height):
    target.add(k.helix(center, center + v(0.0, 0.0, height), radius, 0.011, turns, 8), "rope")
    target.add(k.helix(center + v(0.0, 0.0, 0.004), center + v(0.0, 0.0, height - 0.004), radius - 0.022, 0.011, turns - 0.5, 8), "rope")


def crate(target, center, size, rng):
    boards = 3
    for side in (-1.0, 1.0):
        for index in range(boards):
            z = center.z - size.z * 0.5 + (index + 0.5) * size.z / boards
            block(target, "wood_long", v(center.x, center.y + side * (size.y * 0.5 - 0.008), z), (size.x, 0.016, size.z / boards - 0.006), rng.uniform(-0.004, 0.004), 0.0, 0.0, 0.002)
            block(target, "wood_y", v(center.x + side * (size.x * 0.5 - 0.008), center.y, z), (0.016, size.y - 0.032, size.z / boards - 0.006), 0.0, 0.0, 0.0, 0.002)
    block(target, "wood_dark_long", v(center.x, center.y, center.z - size.z * 0.5 + 0.008), (size.x - 0.03, size.y - 0.03, 0.016), 0.0, 0.0, 0.0, 0.002)


def bench_one(rng):
    bench = k.assembly("workbench_1")
    top_z = 0.9
    widths = (0.26, 0.255, 0.25)
    y = -0.39
    for index, width in enumerate(widths):
        length = 1.6 + rng.uniform(-0.01, 0.05)
        center = v(rng.uniform(-0.02, 0.02), y + width * 0.5, top_z - 0.025 + rng.uniform(-0.002, 0.002))
        block(bench, "wood_long", center, (length, width, 0.05), rng.uniform(-0.006, 0.006), 0.0, rng.uniform(-0.004, 0.004), 0.006, 3)
        for x in (-0.72, 0.72):
            for dy in (-0.07, 0.07):
                nail(bench, v(x + rng.uniform(-0.01, 0.01), center.y + dy, top_z + 0.0005))
        y += width + 0.006
    for side in (-1.0, 1.0):
        block(bench, "wood_long", v(0.0, side * 0.34, top_z - 0.11), (1.5, 0.026, 0.12), 0.0, 0.0, 0.0, 0.004)
        block(bench, "wood_y", v(side * 0.72, 0.0, top_z - 0.11), (0.026, 0.62, 0.12), 0.0, 0.0, 0.0, 0.004)
        block(bench, "wood_long", v(0.0, side * 0.3, 0.2), (1.46, 0.03, 0.08), 0.0, 0.0, 0.0, 0.004)
        block(bench, "wood_y", v(side * 0.72, 0.0, 0.2), (0.03, 0.56, 0.08), 0.0, 0.0, 0.0, 0.004)
    for x in (-0.72, 0.72):
        for y_side in (-0.3, 0.3):
            block(bench, "wood", v(x, y_side, (top_z - 0.05) * 0.5), (0.09, 0.09, top_z - 0.05), 0.0, rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012), 0.008, 3)
        for slope in (-1.0, 1.0):
            angle = math.atan2(0.5, 0.52) * slope
            block(bench, "wood_y", v(x + (0.06 if x > 0 else -0.06), 0.0, 0.5), (0.022, 0.72, 0.065), 0.0, 0.0, angle, 0.003)
        bolt_through(bench, v(x + (0.075 if x > 0 else -0.075), 0.0, 0.5), v(x + (0.03 if x > 0 else -0.03), 0.0, 0.5), 0.017)
    for index, y_shelf in enumerate((-0.2, 0.0, 0.2)):
        block(bench, "wood_dark_long", v(rng.uniform(-0.01, 0.01), y_shelf, 0.255), (1.44, 0.19, 0.024), rng.uniform(-0.01, 0.01), 0.0, 0.0, 0.003)
    jaw = v(-0.52, -0.425, top_z - 0.085)
    block(bench, "wood_long", jaw, (0.3, 0.05, 0.17), 0.0, 0.0, 0.0, 0.006, 3)
    rod(bench, "iron", jaw + v(0.0, -0.18, 0.02), jaw + v(0.0, 0.16, 0.02), 0.012, 18)
    for offset in (-0.09, 0.09):
        rod(bench, "steel", jaw + v(offset, -0.02, -0.05), jaw + v(offset, 0.18, -0.05), 0.008, 12)
    hub = jaw + v(0.0, -0.19, 0.02)
    ball(bench, "iron", hub, 0.02)
    rod(bench, "steel", hub + v(-0.14, 0.0, 0.0), hub + v(0.14, 0.0, 0.0), 0.007, 12)
    for side in (-1.0, 1.0):
        ball(bench, "wood_dark", hub + v(side * 0.15, 0.0, 0.0), 0.017)
    saw(bench, v(0.05, -0.02, top_z), 0.35)
    hammer(bench, v(0.45, -0.25, top_z + 0.016), 2.7)
    tin_of_nails(bench, v(0.62, 0.22, top_z), rng)
    block(bench, "wood_long", v(-0.18, 0.24, top_z + 0.035), (0.34, 0.09, 0.07), 0.25, 0.0, 0.0, 0.004)
    block(bench, "wood", v(-0.42, 0.18, top_z + 0.06), (0.1, 0.1, 0.12), 0.6, 0.0, 0.0, 0.006)
    rope_coil(bench, v(-0.4, 0.05, 0.268), 0.13, 3.5, 0.07)
    crate(bench, v(0.38, 0.02, 0.37), v(0.4, 0.3, 0.2), rng)
    return bench.build()


def bench_two(rng):
    bench = k.assembly("workbench_2")
    top_z = 0.9
    for x in (-0.76, 0.76):
        for y in (-0.36, 0.36):
            turn = (0.0 if x < 0 else math.pi * 0.5) + (0.0 if y < 0 else (math.pi * 0.5 if x < 0 else -math.pi * 0.5))
            angle_iron(bench, "primer", v(x, y, (top_z - 0.05) * 0.5), top_z - 0.05, "z", turn)
            block(bench, "steel", v(x, y, 0.004), (0.08, 0.08, 0.008), 0.0, 0.0, 0.0, 0.002)
    for z in (top_z - 0.075, 0.18):
        for y in (-0.36, 0.36):
            angle_iron(bench, "primer", v(0.0, y, z), 1.48, "x", 0.0 if y < 0 else math.pi * 0.5)
        for x in (-0.76, 0.76):
            angle_iron(bench, "primer", v(x, 0.0, z), 0.68, "y", 0.0 if x < 0 else math.pi)
    for x in (-0.76, 0.76):
        for y in (-0.36, 0.36):
            for z in (top_z - 0.075, 0.18):
                bench.add(k.weld([v(x - 0.03 * math.copysign(1.0, x), y, z - 0.028), v(x - 0.035 * math.copysign(1.0, x), y - 0.005 * math.copysign(1.0, y), z), v(x - 0.03 * math.copysign(1.0, x), y, z + 0.028)], 0.004, int(abs(x * 100 + y * 10 + z * 7))), "iron")
    block(bench, "wood_long", v(0.0, 0.0, top_z - 0.03), (1.62, 0.8, 0.036), 0.0, 0.0, 0.0, 0.004)
    block(bench, "steel", v(0.0, 0.0, top_z - 0.006), (1.6, 0.78, 0.012), 0.0, 0.0, 0.0, 0.003, 2)
    for x in (-0.7, -0.2, 0.3, 0.7):
        for y in (-0.33, 0.33):
            k.screw(bench, v(x, y, top_z), v(0.0, 0.0, -1.0), 0.006, "steel", True, 0.45)
    for index in range(4):
        block(bench, "wood_dark_long", v(0.0, -0.27 + index * 0.18, 0.2), (1.46, 0.17, 0.022), 0.0, 0.0, 0.0, 0.003)
    drawers = v(0.5, 0.02, 0.45)
    block(bench, "painted", drawers, (0.44, 0.62, 0.5), 0.0, 0.0, 0.0, 0.008, 3)
    for row in range(2):
        face = drawers + v(0.0, -0.315, -0.12 + row * 0.24)
        block(bench, "painted", face, (0.4, 0.02, 0.21), 0.0, 0.0, 0.0, 0.004)
        rod(bench, "steel", face + v(-0.08, -0.03, 0.04), face + v(0.08, -0.03, 0.04), 0.006, 10)
        for side in (-1.0, 1.0):
            rod(bench, "steel", face + v(side * 0.08, -0.012, 0.04), face + v(side * 0.08, -0.03, 0.04), 0.005, 8)
    vise = v(0.62, -0.36, top_z)
    block(bench, "painted", vise + v(0.0, 0.08, 0.02), (0.16, 0.2, 0.04), 0.0, 0.0, 0.0, 0.006)
    block(bench, "painted", vise + v(0.0, 0.1, 0.1), (0.13, 0.12, 0.13), 0.0, 0.0, 0.0, 0.012, 3)
    block(bench, "painted", vise + v(0.0, -0.08, 0.1), (0.13, 0.1, 0.12), 0.0, 0.0, 0.0, 0.012, 3)
    for side in (-1.0, 1.0):
        block(bench, "steel", vise + v(0.0, 0.03 * side - 0.015, 0.14), (0.14, 0.012, 0.05), 0.0, 0.0, 0.0, 0.002)
    rod(bench, "steel", vise + v(0.0, -0.3, 0.09), vise + v(0.0, 0.16, 0.09), 0.013, 16)
    rod(bench, "steel", vise + v(-0.13, -0.3, 0.09), vise + v(0.13, -0.3, 0.09), 0.008, 12)
    for side in (-1.0, 1.0):
        ball(bench, "steel", vise + v(side * 0.135, -0.3, 0.09), 0.016)
    bolt_through(bench, vise + v(0.06, 0.1, top_z * 0.0 + 0.045), vise + v(0.06, 0.1, -0.02), 0.018)
    board = v(0.0, 0.37, top_z + 0.34)
    holes = []
    for row in range(6):
        for column in range(16):
            holes.append(k.transformed(k.revolve([(0.0, -0.03), (0.0035, -0.03), (0.0035, 0.03), (0.0, 0.03)], 8), k.place(board + v(-0.66 + column * 0.088, 0.0, -0.22 + row * 0.088), v(0.0, 1.0, 0.0))))
    bench.add(k.cut(k.shifted(k.box(1.46, 0.012, 0.56), board.x, board.y, board.z), holes), "wood_dark_long", None, 0.002, 1)
    for x in (-0.76, 0.76):
        angle_iron(bench, "primer", v(x, 0.4, top_z + 0.32), 0.64, "z", math.pi if x > 0 else math.pi * 0.5)
    for index in range(4):
        size = 0.18 + index * 0.03
        wrench = k.fillet([(-0.012, -size * 0.5), (0.012, -size * 0.5), (0.012, size * 0.5), (-0.012, size * 0.5)], 0.006, 3)
        spot = board + v(-0.6 + index * 0.08, -0.012, 0.03)
        bench.add(k.extrude(wrench, 0.005, "y"), "steel", turned(spot, 0.0, 0.0, 0.0), 0.0015, 1)
        for end in (-1.0, 1.0):
            jaw = k.cut(k.revolve([(0.0, -0.0025), (0.02, -0.0025), (0.02, 0.0025), (0.0, 0.0025)], 16), [k.shifted(k.box(0.05, 0.03, 0.022), 0.0, 0.0, 0.016)])
            bench.add(jaw, "steel", k.place(spot + v(0.0, 0.0, end * size * 0.5), v(0.0, 1.0, 0.0), v(0.0, 0.0, end)))
    hammer(bench, board + v(0.25, -0.03, -0.1), 0.0)
    grinder = v(-0.55, 0.12, top_z)
    block(bench, "painted", grinder + v(0.0, 0.0, 0.03), (0.2, 0.14, 0.06), 0.0, 0.0, 0.0, 0.008)
    bench.add(k.revolve([(0.0, -0.1), (0.055, -0.1), (0.06, -0.09), (0.06, 0.09), (0.055, 0.1), (0.0, 0.1)], 28), "painted", k.place(grinder + v(0.0, 0.0, 0.12)), 0.003, 2)
    for side in (-1.0, 1.0):
        center = grinder + v(side * 0.16, 0.0, 0.12)
        bench.add(k.revolve([(0.012, -0.012), (0.075, -0.012), (0.075, 0.012), (0.012, 0.012)], 36), "iron", k.place(center), 0.002, 1)
        guard = k.cut(k.revolve([(0.0, -0.025), (0.085, -0.025), (0.085, 0.025), (0.0, 0.025)], 36), [k.shifted(k.box(0.3, 0.3, 0.3), 0.0, -0.12, -0.05), k.shifted(k.revolve([(0.0, -0.02), (0.079, -0.02), (0.079, 0.02), (0.0, 0.02)], 36), 0.0, 0.0, 0.0)])
        bench.add(guard, "painted", k.place(center), 0.002, 1)
    oil = v(-0.2, 0.25, top_z)
    bench.add(k.revolve([(0.0, 0.0), (0.05, 0.0), (0.05, 0.07), (0.02, 0.1), (0.008, 0.12), (0.0, 0.12)], 28), "zinc", k.place(oil, v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)), 0.001, 1)
    rod(bench, "brass", oil + v(0.0, 0.0, 0.1), oil + v(0.14, 0.0, 0.19), 0.004, 8)
    tin_of_nails(bench, v(-0.02, 0.26, top_z), rng, 12)
    return bench.build()


def bench_three(rng):
    bench = k.assembly("workbench_3")
    top_z = 0.9
    for x in (-0.76, 0.76):
        for y in (-0.35, 0.35):
            outline = k.fillet([(-0.035, -0.035), (0.035, -0.035), (0.035, 0.035), (-0.035, 0.035)], 0.006, 3)
            bench.add(k.shifted(k.extrude(outline, top_z - 0.04, "z"), x, y, (top_z - 0.04) * 0.5), "primer", None, 0.002, 1)
            block(bench, "steel", v(x, y, 0.006), (0.12, 0.12, 0.012), 0.0, 0.0, 0.0, 0.002)
            for bolt in ((-0.04, -0.04), (0.04, 0.04)):
                k.hex_head(bench, v(x + bolt[0], y + bolt[1], 0.012), v(0.0, 0.0, -1.0), 0.016, 0.008, "zinc")
    for z in (top_z - 0.06, 0.22):
        for y in (-0.35, 0.35):
            bench.add(k.shifted(k.extrude(k.fillet([(-0.03, -0.03), (0.03, -0.03), (0.03, 0.03), (-0.03, 0.03)], 0.005, 3), 1.45, "x"), 0.0, y, z), "primer", None, 0.002, 1)
        for x in (-0.76, 0.76):
            bench.add(k.shifted(k.extrude(k.fillet([(-0.03, -0.03), (0.03, -0.03), (0.03, 0.03), (-0.03, 0.03)], 0.005, 3), 0.64, "y"), x, 0.0, z), "primer", None, 0.002, 1)
    block(bench, "steel", v(0.0, 0.0, top_z - 0.012), (1.64, 0.82, 0.024), 0.0, 0.0, 0.0, 0.004, 2)
    block(bench, "steel", v(0.0, 0.0, 0.24), (1.5, 0.66, 0.008), 0.0, 0.0, 0.0, 0.002)
    press = v(-0.5, 0.12, top_z)
    block(bench, "iron", press + v(0.0, 0.0, 0.02), (0.3, 0.36, 0.04), 0.0, 0.0, 0.0, 0.006, 2)
    rod(bench, "steel", press + v(0.0, 0.1, 0.04), press + v(0.0, 0.1, 0.78), 0.036, 28)
    head = press + v(0.0, 0.0, 0.8)
    block(bench, "painted", head, (0.2, 0.36, 0.2), 0.0, 0.0, 0.0, 0.03, 4)
    bench.add(k.revolve([(0.0, -0.12), (0.075, -0.12), (0.08, -0.1), (0.08, 0.1), (0.075, 0.12), (0.0, 0.12)], 28), "painted", k.place(head + v(0.0, 0.25, 0.02), v(0.0, 1.0, 0.0)), 0.004, 2)
    block(bench, "painted", head + v(0.0, 0.05, 0.13), (0.16, 0.28, 0.06), 0.0, 0.0, 0.0, 0.01, 3)
    rod(bench, "steel", head + v(0.0, -0.12, -0.1), head + v(0.0, -0.12, -0.2), 0.022, 20)
    bench.add(k.revolve([(0.0, 0.0), (0.02, 0.0), (0.022, 0.03), (0.012, 0.055), (0.0, 0.058)], 20), "steel", k.place(head + v(0.0, -0.12, -0.2), v(0.0, 0.0, -1.0), v(1.0, 0.0, 0.0)))
    rod(bench, "steel", head + v(0.0, -0.12, -0.255), head + v(0.0, -0.12, -0.33), 0.004, 8)
    for index in range(3):
        angle = index * math.tau / 3.0 + 0.4
        spoke = head + v(0.105, -0.02, -0.02)
        tip = spoke + v(0.0, math.cos(angle) * 0.17, math.sin(angle) * 0.17)
        rod(bench, "steel", spoke, tip, 0.006, 10)
        ball(bench, "rubber", tip, 0.016)
    bench.add(k.revolve([(0.0, -0.012), (0.1, -0.012), (0.1, 0.012), (0.0, 0.012)], 36), "iron", k.place(press + v(0.0, -0.08, 0.36), v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)), 0.003, 1)
    rod(bench, "iron", press + v(0.0, 0.1, 0.36), press + v(0.0, -0.02, 0.36), 0.03, 16)
    for index, (x, look) in enumerate(((0.86, "painted"), (1.02, "primer"))):
        base = v(x, 0.18, 0.0)
        bench.add(k.revolve([(0.0, 0.0), (0.085, 0.0), (0.09, 0.02), (0.09, 0.95), (0.075, 1.02), (0.03, 1.05), (0.0, 1.05)], 32), look, k.place(base, v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)), 0.004, 2)
        valve = base + v(0.0, 0.0, 1.05)
        rod(bench, "brass", valve, valve + v(0.0, 0.0, 0.06), 0.014, 14)
        ball(bench, "brass", valve + v(0.0, -0.035, 0.05), 0.025)
        bench.add(k.revolve([(0.0, 0.0), (0.024, 0.0), (0.024, 0.012), (0.0, 0.012)], 20), "glass", k.place(valve + v(0.0, -0.058, 0.05), v(0.0, -1.0, 0.0)))
        hose = k.spline([valve + v(0.0, 0.03, 0.06), valve + v(0.0, 0.12, 0.1), v(0.5, 0.28, top_z + 0.25), v(0.25, 0.05, top_z + 0.02), v(0.1, -0.12, top_z + 0.015)], 10)
        bench.add(k.sweep(hose, k.circle(0.007, 10), up=v(0.0, 0.0, 1.0)), "rubber")
    rod(bench, "brass", v(0.1, -0.12, top_z + 0.015), v(-0.12, -0.2, top_z + 0.015), 0.01, 14)
    rod(bench, "steel", v(-0.12, -0.2, top_z + 0.015), v(-0.2, -0.24, top_z + 0.03), 0.004, 8)
    lamp = v(0.3, 0.36, top_z)
    block(bench, "iron", lamp + v(0.0, 0.0, 0.015), (0.1, 0.1, 0.03), 0.0, 0.0, 0.0, 0.004)
    elbow = lamp + v(0.05, -0.06, 0.45)
    rod(bench, "steel", lamp + v(0.0, 0.0, 0.03), elbow, 0.008, 10)
    ball(bench, "steel", elbow, 0.016)
    shade = elbow + v(-0.15, -0.2, -0.05)
    rod(bench, "steel", elbow, shade, 0.007, 10)
    bench.add(k.revolve([(0.0, 0.0), (0.03, 0.0), (0.075, 0.09), (0.072, 0.092), (0.028, 0.004), (0.0, 0.004)], 28), "painted", k.axis_frame(shade, v(-0.2, -0.3, -1.0)), 0.001, 1)
    chest = v(-0.25, 0.0, 0.25)
    block(bench, "primer", chest + v(0.0, 0.0, 0.14), (0.6, 0.36, 0.28), 0.0, 0.0, 0.0, 0.01, 3)
    for row in range(3):
        rod(bench, "steel", chest + v(-0.2, -0.19, 0.06 + row * 0.085), chest + v(0.2, -0.19, 0.06 + row * 0.085), 0.005, 8)
    return bench.build()


def research(rng):
    desk = k.assembly("research_table")
    top_z = 0.76
    y = -0.36
    for index in range(3):
        width = 0.24 + rng.uniform(-0.005, 0.005)
        block(desk, "wood_long", v(rng.uniform(-0.01, 0.01), y + width * 0.5, top_z - 0.02), (1.2 + rng.uniform(0.0, 0.03), width, 0.04), rng.uniform(-0.004, 0.004), 0.0, 0.0, 0.005, 3)
        y += width + 0.004
    for x in (-0.54, 0.54):
        for y_side in (-0.3, 0.3):
            block(desk, "wood", v(x, y_side, (top_z - 0.04) * 0.5), (0.06, 0.06, top_z - 0.04), 0.0, 0.0, 0.0, 0.006, 3)
    for side in (-1.0, 1.0):
        block(desk, "wood_long", v(0.0, side * 0.31, top_z - 0.09), (1.02, 0.022, 0.1), 0.0, 0.0, 0.0, 0.004)
        block(desk, "wood_y", v(side * 0.54, 0.0, top_z - 0.09), (0.022, 0.56, 0.1), 0.0, 0.0, 0.0, 0.004)
    block(desk, "wood_long", v(0.18, -0.335, top_z - 0.09), (0.42, 0.024, 0.085), 0.0, 0.0, 0.0, 0.004)
    ball(desk, "brass", v(0.18, -0.352, top_z - 0.09), 0.012)
    chassis = v(-0.18, 0.05, top_z)
    body = k.cut(k.shifted(k.box(0.34, 0.22, 0.13), 0.0, 0.0, 0.065), [k.shifted(k.box(0.32, 0.2, 0.2), 0.0, 0.0, 0.14)])
    desk.add(body, "painted", Matrix.Translation(chassis), 0.002, 1)
    block(desk, "steel", chassis + v(0.0, 0.0, 0.1), (0.3, 0.19, 0.004), 0.0, 0.0, 0.0, 0.001)
    for index in range(4):
        socket = chassis + v(-0.1 + index * 0.065, 0.04, 0.102)
        desk.add(k.revolve([(0.0, 0.0), (0.016, 0.0), (0.016, 0.012), (0.0, 0.012)], 16), "brass", k.place(socket, v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)))
        desk.add(k.revolve([(0.0, 0.012), (0.013, 0.012), (0.014, 0.05), (0.011, 0.07), (0.005, 0.078), (0.0, 0.08)], 18), "glass", k.place(socket, v(0.0, 0.0, 1.0), v(1.0, 0.0, 0.0)))
    for index in range(2):
        start = chassis + v(-0.08 + index * 0.13, -0.05, 0.105)
        desk.add(k.helix(start, start + v(0.0, 0.0, 0.05), 0.018, 0.0022, 9.0, 8), "copper")
        rod(desk, "paper", start + v(0.0, 0.0, 0.0), start + v(0.0, 0.0, 0.055), 0.014, 14)
    block(desk, "iron", chassis + v(0.12, -0.04, 0.13), (0.06, 0.05, 0.05), 0.0, 0.0, 0.0, 0.004)
    wire = k.spline([chassis + v(0.17, 0.0, 0.07), chassis + v(0.28, -0.02, 0.02), chassis + v(0.36, -0.12, 0.004), chassis + v(0.45, -0.2, 0.004)], 10)
    desk.add(k.sweep(wire, k.circle(0.0035, 8), up=v(0.0, 0.0, 1.0)), "rubber")
    for index in range(4):
        sheet = v(0.28 + rng.uniform(-0.05, 0.08), -0.08 + rng.uniform(-0.12, 0.12), top_z + 0.0006 + index * 0.0012)
        block(desk, "paper", sheet, (0.21, 0.297, 0.0012), rng.uniform(-0.5, 0.5), 0.0, 0.0, 0.0002, 1)
    block(desk, "cloth", v(0.42, 0.2, top_z + 0.012), (0.16, 0.22, 0.024), 0.3, 0.0, 0.0, 0.003)
    rod(desk, "wood", v(0.2, -0.22, top_z + 0.004), v(0.36, -0.2, top_z + 0.004), 0.0038, 6)
    clamp_at = v(-0.5, 0.3, top_z)
    block(desk, "iron", clamp_at + v(0.0, 0.0, 0.015), (0.08, 0.06, 0.03), 0.0, 0.0, 0.0, 0.003)
    knee = clamp_at + v(0.04, -0.05, 0.36)
    rod(desk, "steel", clamp_at + v(0.0, 0.0, 0.03), knee, 0.007, 10)
    ball(desk, "steel", knee, 0.014)
    lens = knee + v(0.14, -0.2, -0.16)
    rod(desk, "steel", knee, lens + v(-0.04, 0.05, 0.03), 0.006, 10)
    k.ring(desk, lens, v(0.2, 0.3, 1.0), 0.055, 0.008, "steel")
    desk.add(k.revolve([(0.0, -0.002), (0.052, -0.002), (0.052, 0.002), (0.0, 0.002)], 32), "glass", k.axis_frame(lens, v(0.2, 0.3, 1.0)))
    tin_of_nails(desk, v(0.02, 0.26, top_z), rng, 10, 0.04, 0.08)
    return desk.build()


def deployables():
    rng = random.Random(4471)
    return [bench_one(rng), bench_two(rng), bench_three(rng), research(rng)]


builders = {"deployables": deployables}

for name in wanted:
    k.reset()
    directory = os.path.join(output_root, name)
    os.makedirs(directory, exist_ok=True)
    objects = builders[name]()
    print("BUILT", name, [(o.name, len(o.data.polygons)) for o in objects])
    if mode == "preview":
        for obj in objects:
            if not only or obj.name in only:
                hidden = [other for other in objects if other != obj]
                for other in hidden:
                    other.hide_render = True
                turntable.render_views([obj], preview_root, obj.name, views, samples, hdri)
                for other in hidden:
                    other.hide_render = False
    else:
        for obj in objects:
            k.bake_part(obj, directory)
        k.export(os.path.join(directory, name + ".gltf"))
        for obj in objects:
            if not only or obj.name in only:
                hidden = [other for other in objects if other != obj]
                for other in hidden:
                    other.hide_render = True
                turntable.render_views([obj], preview_root, obj.name + "_baked", views, samples, hdri)
                for other in hidden:
                    other.hide_render = False
