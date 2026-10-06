import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import railkit as rk
from buildkit import V, block, emit, local_block
from mathutils import Matrix

tau = math.pi * 2.0
X = V(1.0, 0.0, 0.0)
Y = V(0.0, 1.0, 0.0)
Z = V(0.0, 0.0, 1.0)
gauge = 1.435
wheel_radius = 0.48
buffer_height = 1.05
hook_height = 1.0
buffer_spread = 0.86
buffer_length = 0.5
coupling_gap = 0.4
step_out = 1.38
step_run = 0.28
neck = 0.54
manifest_path = os.path.join(kit.root, "assets", "source", "railway", "train.json")


def end_gear(b, part, y, direction, rng, body="loco_black", oval=1.0, stock=0.26, links=3, pipe=True):
    forward = V(0.0, direction, 0.0)
    for side in (-1.0, 1.0):
        rk.buffer(part, V(side * buffer_spread, y, buffer_height), forward, body, "rust_iron", stock, buffer_length, oval)
    rk.drawgear(part, V(0.0, y, hook_height), forward, rng, body, "rust_iron", links)
    if not pipe:
        return
    pipe_x = -0.34 * direction
    top = 1.13
    rk.pipe(part, body, [V(pipe_x, y - 0.06 * direction, 0.55), V(pipe_x, y + 0.035 * direction, 0.62), V(pipe_x, y + 0.035 * direction, top - 0.06), V(pipe_x, y + 0.13 * direction, top)], 0.022, 8, 0.05)
    hose = [V(pipe_x, y + 0.13 * direction, top), V(pipe_x - 0.02, y + 0.2 * direction, top - 0.1), V(pipe_x - 0.06, y + 0.17 * direction, 0.8), V(pipe_x - 0.1, y + 0.06 * direction, 0.7)]
    rk.pipe(part, "loco_black", hose, 0.03, 8, 0.08)
    rk.lathe(part, "rust_iron", hose[-1], V(0.0, -direction, -0.4), [(0.0, -0.02), (0.045, -0.02), (0.045, 0.02), (0.03, 0.03), (0.0, 0.03)], 10)


def wasp_face(part, y, direction, x_half, z0, z1):
    for side in (-1.0, 1.0):
        xa, xb = (0.0, x_half) if side > 0 else (-x_half, 0.0)
        corners = [V(xa, y, z0), V(xb, y, z0), V(xb, y, z1), V(xa, y, z1)]
        geo = rk.facing(kit.Geo(corners, [(0, 1, 2, 3)]), V(0.0, direction, 0.0))
        rk.planar(part, geo, "wasp_stripes", V(0.0, y, z0), V(side, 0.0, 0.0), Z)


def wasp_beam(part, y, direction, x_half, z0, z1, thickness=0.035):
    back_y = y - thickness * direction
    wasp_face(part, y, direction, x_half, z0, z1)
    block(part, "loco_black", V(-x_half, min(y, back_y), z0), V(x_half, max(y, back_y), z1), 0.0, "box", None, ("front",) if direction < 0 else ("back",))


def lamp_iron(part, position, direction):
    side = Z.cross(direction).normalized()
    rk.bar(part, "loco_black", [position, position + direction * 0.05, position + direction * 0.05 + Z * 0.16], 0.008, 0.04, side, 0.0)


def oil_lamp(part, position, direction):
    frame = kit.place(position, direction, Z)
    side = Z.cross(direction).normalized()
    local_block(part, "loco_black", frame, -0.07, 0.07, -0.075, 0.075, 0.0, 0.2, 0.008)
    emit(part, kit.geo_lathe([(0.0, 0.2), (0.06, 0.2), (0.045, 0.235), (0.03, 0.245), (0.03, 0.275), (0.0, 0.28)], 12), "loco_black", Matrix.Translation(position), "given", True)
    rk.lathe(part, "loco_black", position + direction * 0.07 + Z * 0.1, direction, [(0.062, 0.0), (0.062, 0.02), (0.05, 0.026)], 16)
    rk.atlas_disc(part, "lens_clear", position + direction * 0.095 + Z * 0.1, direction, Z, 0.05, 14)
    handle = [position + Z * 0.28 + side * 0.05, position + Z * 0.34 + side * 0.04, position + Z * 0.34 - side * 0.04, position + Z * 0.28 - side * 0.05]
    rk.pipe(part, "rust_iron", handle, 0.005, 6, 0.015)


def round_lamp(part, position, direction, radius=0.085, lens="lens_clear", body="loco_black", glow=None, segments=20):
    rk.lathe(part, body, position, direction, [(0.0, -0.09), (radius * 0.6, -0.085), (radius, -0.03), (radius, 0.03), (radius * 0.88, 0.04), (radius * 0.84, 0.02)], segments)
    rk.atlas_disc(part, lens, position + direction.normalized() * 0.02, direction, Z if abs(direction.z) < 0.9 else Y, radius * 0.84, segments - 2, glow or "rail_signs")


def brake_block(part, x, y, z, direction):
    frame = kit.place(V(x, y, z), V(0.0, direction, 0.0), Z)
    local_block(part, "rust_iron", frame, 0.0, 0.05, -0.05, 0.05, -0.13, 0.13, 0.008)
    rk.bar(part, "loco_black", [V(x, y + direction * 0.02, z + 0.1), V(x - math.copysign(0.1, x), y + direction * 0.02, z + 0.62)], 0.05, 0.015, Y)


def sandbox(part, rng, side, y0, y1, wheel_y):
    x0, x1 = sorted((side * 0.92, side * 1.22))
    block(part, "loco_black", V(x0, y0, 0.78), V(x1, y1, 1.24), 0.012)
    local_block(part, "loco_black", Matrix.Translation(V((x0 + x1) * 0.5, (y0 + y1) * 0.5, 1.24)), -0.1, 0.1, -0.1, 0.1, 0.0, 0.016, 0.005)
    toward = 1.0 if wheel_y > (y0 + y1) * 0.5 else -1.0
    start = V(side * 1.0, y1 if toward > 0 else y0, 0.8)
    rk.pipe(part, "rust_iron", [start, V(side * 0.86, start.y + toward * 0.04, 0.62), V(side * 0.76, wheel_y - toward * 0.56, 0.32), V(side * 0.755, wheel_y - toward * 0.36, 0.09)], 0.017, 8, 0.08)


def post(part, base, height, name="loco_black", radius=0.017):
    rk.pipe(part, name, [base, base + Z * height], radius, 8)
    rk.lathe(part, name, base + Z * height, Z, [(0.0, -0.02), (0.024, -0.012), (0.03, 0.01), (0.022, 0.03), (0.0, 0.036)], 10)
    rk.lathe(part, name, base, Z, [(0.04, 0.0), (0.04, 0.01), (0.02, 0.03)], 10)


def railing(part, a, b, height, name="loco_black", middle=True, radius=0.015):
    post(part, a, height, name)
    post(part, b, height, name)
    rk.pipe(part, name, [a + Z * (height - 0.03), b + Z * (height - 0.03)], radius, 8)
    if middle:
        rk.pipe(part, name, [a + Z * (height * 0.52), b + Z * (height * 0.52)], radius * 0.8, 6)


def stairwell(b, part, detail, side, y0, y1, deck, edge, tops, back=True, iron="loco_black"):
    risers = [step_out - step_run * index for index in range(3)]
    profile = [(step_out + 0.02, tops[0] - 0.1), (step_out + 0.02, tops[0] + 0.03), (risers[1] + 0.02, tops[0] + 0.03), (risers[1] + 0.02, tops[1] + 0.03), (risers[2] + 0.02, tops[1] + 0.03), (risers[2] + 0.02, tops[2] + 0.03), (neck, tops[2] + 0.03), (neck, tops[2] - 0.42), (step_out - 0.2, tops[0] - 0.1)]
    outline = [(side * x, z) for x, z in profile]
    for y in (y0, y1 - 0.012):
        emit(part, rk.geo_prism(outline, y, y + 0.012, 1), iron, None, "given", False)
    if back:
        block(part, iron, V(side * (neck - 0.012), y0, tops[2] - 0.3), V(side * neck, y1, deck - 0.05))
        rk.rivets(detail, iron, V(side * neck, y0 + 0.08, deck - 0.12), V(side * neck, y1 - 0.08, deck - 0.12), 0.12, V(side, 0.0, 0.0), 0.011)
    for top, out in zip(tops, risers):
        rk.slab(part, V(side * (out - step_run - 0.02), y0 + 0.012, top - 0.014), V(side * out, y1 - 0.012, top), "chequer_plate", iron, True, V(0.0, y0, 0.0))
        block(part, iron, V(side * (out - 0.014), y0 + 0.012, top - 0.055), V(side * out, y1 - 0.012, top - 0.014))
        for y in (y0 + 0.012, y1 - 0.052):
            block(detail, iron, V(side * (out - step_run), y, top - 0.055), V(side * (out - 0.03), y + 0.04, top - 0.014))
            for along in (0.07, 0.2):
                rk.prism_bolt(detail, "rust_iron", V(side * (out - along), y + 0.02, top), Z, 0.022, 0.008, 6)
    for y, normal in ((y0 + 0.012, 1.0), (y1 - 0.012, -1.0)):
        rk.rivets(detail, iron, V(side * (neck + 0.08), y, tops[2] - 0.32), V(side * (step_out - 0.24), y, tops[0] - 0.05), 0.13, V(0.0, normal, 0.0), 0.011)
    low = -0.1
    for top, out in zip(tops, risers):
        xa, xb = sorted((side * neck, side * out))
        b.col("metal", "step", V(xa, y0, low), V(xb, y1, top))
        low = top


def fall_plate(part, detail, y, direction, deck, half=0.5, reach=0.44, iron="loco_black"):
    rk.slab(part, V(-half, y, deck - 0.014), V(half, y + direction * reach, deck), "chequer_plate", iron, True, V(0.0, y, 0.0))
    for x in (-0.36, 0.36):
        outline = [(y, deck - 0.014), (y + direction * (reach - 0.05), deck - 0.014), (y + direction * (reach - 0.05), deck - 0.04), (y, deck - 0.22)]
        emit(part, rk.prism_x(outline, x - 0.006, x + 0.006), iron, None, "given", False)
    for x in (-0.38, 0.0, 0.38):
        rk.lathe(detail, iron, V(x - 0.06, y + direction * 0.006, deck - 0.004), X, [(0.0, 0.0), (0.013, 0.0), (0.013, 0.12), (0.0, 0.12)], 8)
    for x in (-half + 0.03, half - 0.03):
        rk.rivets(detail, iron, V(x, y + direction * 0.06, deck), V(x, y + direction * (reach - 0.04), deck), 0.11, Z, 0.009)


def wheelset():
    b = rk.Build("train_wheelset", 30)
    rk.wheelset(b, "wheelset", 0.0, wheel_radius, 8, "loco_black", False, False, 0.68, 0.065, 0.11, 0.045, 64, 0.93, 0.0)
    return b


def far_wheels(part, y, height=wheel_radius, body="loco_black", radius=wheel_radius):
    for side in (-1.0, 1.0):
        matrix = Matrix.Translation(V(side * 0.68, y, height)) @ Matrix.Rotation(side * math.pi * 0.5, 4, 'Y')
        emit(part, kit.geo_lathe([(0.0, 0.0), (radius + 0.028, 0.0), (radius + 0.028, 0.03), (radius, 0.04), (radius - 0.01, 0.135), (0.0, 0.135)], 14), body, matrix, "given", True)
    emit(part, kit.geo_lathe([(0.065, -0.68), (0.065, 0.68)], 6), body, Matrix.Translation(V(0.0, y, height)) @ Matrix.Rotation(math.pi * 0.5, 4, 'Y'), "given", True)


def wheelset_far():
    b = rk.Build("train_wheelset_far", 30)
    far_wheels(b.part("wheelset", 40.0), 0.0, 0.0)
    return b


def far_buffers(part, y, direction, body="loco_black"):
    for side in (-1.0, 1.0):
        rk.lathe(part, body, V(side * buffer_spread, y, buffer_height), V(0.0, direction, 0.0), [(0.11, 0.0), (0.085, 0.3), (0.06, 0.44), (0.19, 0.47), (0.19, 0.5), (0.0, 0.5)], 8)
    block(part, "rust_iron", V(-0.03, min(y, y + direction * 0.3), hook_height - 0.06), V(0.03, max(y, y + direction * 0.3), hook_height + 0.08))


def far_stairs(part, side, y0, y1, tops, iron="loco_black"):
    for index, top in enumerate(tops):
        out = step_out - step_run * index
        block(part, iron, V(side * (out - step_run), y0, top - 0.04), V(side * out, y1, top), 0.0, "box", None, ("bottom",))


loco_head = 3.5
loco_beam = 0.06
loco_deck = 1.3
loco_half = 1.3
loco_tops = (0.19, 0.56, 0.93)
loco_well = 2.56
loco_axles = (1.4, 0.0, -1.4)
bonnet_half = 0.7
bonnet_top = 2.72
bonnet_y0 = -0.68
bonnet_y1 = 2.56
cab_y0 = -2.56
cab_y1 = -0.68
cab_eaves = 3.37
cab_rise = 0.26
door_pitch = 0.79
door_width = 0.76
open_door = (1.0, 2)
stack_position = V(0.0, 2.0, bonnet_top + 0.01)
lamp_positions = [V(-0.4, bonnet_y1 + 0.085, 2.63), V(0.4, bonnet_y1 + 0.085, 2.63)]
horn_position = V(0.0, cab_y1 + 0.05, cab_eaves + cab_rise + 0.06)
tail_position = V(0.0, cab_y0 - 0.075, 3.48)


def loco_frames(b, rng):
    frame = b.part("frame", 40.0, 50)
    detail = b.part("detail", 40.0)
    inner = loco_head - loco_beam
    rk.slab(frame, V(-loco_half, -loco_well, 1.26), V(loco_half, loco_well, loco_deck), "chequer_plate", "loco_black")
    for side in (-1.0, 1.0):
        block(frame, "loco_black", V(side * 1.27, -loco_well, 1.14), V(side * 1.3, loco_well, 1.26))
        rk.rivets(detail, "loco_black", V(side * 1.3, -loco_well + 0.08, 1.2), V(side * 1.3, loco_well - 0.08, 1.2), 0.17, V(side, 0.0, 0.0), 0.011)
        block(frame, "loco_black", V(side * 0.5, -inner, 0.4), V(side * neck, inner, 1.26))
        rk.rivets(detail, "loco_black", V(side * neck, -2.4, 1.06), V(side * neck, 2.4, 1.06), 0.2, V(side, 0.0, 0.0), 0.013)
        for y in (-2.0, -0.7, 0.7, 2.0):
            outline = [(side * neck, 1.26), (side * 1.27, 1.26), (side * 1.27, 1.16), (side * neck, 0.9)]
            emit(frame, rk.geo_prism(outline, y - 0.008, y + 0.008, 1), "loco_black", None, "given", False)
        for end in (-1.0, 1.0):
            rk.bar(detail, "loco_black", [V(side * 0.755, end * 3.42, 0.74), V(side * 0.755, end * 3.36, 0.4), V(side * 0.755, end * 3.28, 0.085)], 0.022, 0.07, X)
    block(frame, "loco_black", V(-0.42, -3.0, 0.5), V(0.42, 3.0, 1.26))
    block(frame, "loco_black", V(-0.5, -0.4, 0.3), V(0.5, 0.45, 0.62), 0.03)
    for y in (-3.0, -2.2, -0.7, 0.7, 2.2, 3.0):
        block(frame, "loco_black", V(-0.5, y - 0.02, 0.62), V(0.5, y + 0.02, 1.2))
    for direction in (-1.0, 1.0):
        y = direction * loco_head
        wasp_beam(frame, y, direction, 1.28, 0.7, loco_deck, loco_beam)
        rk.slab(frame, V(-neck, direction * loco_well, 1.26), V(neck, direction * inner, loco_deck), "chequer_plate", "loco_black")
        for x in (-1.22, -0.62, 0.62, 1.22):
            rk.rivets(detail, "rust_iron", V(x, y, 0.76), V(x, y, 1.24), 0.12, V(0.0, direction, 0.0), 0.012)
        for z in (0.745, 1.255):
            rk.rivets(detail, "rust_iron", V(-1.15, y, z), V(1.15, y, z), 0.144, V(0.0, direction, 0.0), 0.012)
        end_gear(b, detail, y, direction, rng)
        fall_plate(frame, detail, y, direction, loco_deck)
        for x in (-0.95, 0.95):
            lamp_iron(detail, V(x, y - direction * 0.03, loco_deck), V(0.0, direction, 0.0))
        b.col("metal", "end", V(-1.06, direction * inner, 0.86), V(1.06, y + direction * buffer_length, loco_deck))
        b.col("metal", "neck", V(-neck, direction * loco_well, 0.45), V(neck, direction * inner, loco_deck))
        for side in (-1.0, 1.0):
            ya, yb = sorted((direction * loco_well, direction * inner))
            stairwell(b, frame, detail, side, ya, yb, loco_deck, loco_half, loco_tops, False)
            railing(detail, V(side * 0.6, y - direction * 0.03, loco_deck), V(side * 1.25, y - direction * 0.03, loco_deck), 0.95)
    oil_lamp(detail, V(0.95, loco_head - 0.025, 1.46), Y)
    oil_lamp(detail, V(-0.95, -loco_head + 0.025, 1.46), -Y)
    for side in (-1.0, 1.0):
        sandbox(frame, rng, side, 1.98, 2.36, loco_axles[0])
        sandbox(frame, rng, side, -2.36, -1.98, loco_axles[2])
        for axle in loco_axles:
            brake_block(detail, side * 0.755, axle - wheel_radius - 0.05, wheel_radius, 1.0)
            block(frame, "loco_black", V(side * neck, axle - 0.13, 0.35), V(side * 0.6, axle + 0.13, 0.62), 0.01)
            for offset in (-0.165, 0.165):
                block(frame, "loco_black", V(side * neck, axle + offset - 0.025, 0.3), V(side * 0.585, axle + offset + 0.025, 0.9))
                rk.prism_bolt(detail, "rust_iron", V(side * 0.562, axle + offset, 0.27), -Z, 0.03, 0.016, 6)
            block(frame, "rust_iron", V(side * neck, axle - 0.2, 0.27), V(side * 0.585, axle + 0.2, 0.305))
            rk.leaf_spring(frame, "rust_iron", V(side * 0.62, axle, 0.62 + 0.08), 0.78, 6, 0.07, 0.011, 0.06, Y)
        rk.pipe(detail, "loco_black", [V(side * 1.215, -1.95, 1.1), V(side * 1.215, 1.95, 1.1)], 0.018, 8)
        for index in range(5):
            y = -1.6 + index * 0.8
            block(detail, "loco_black", V(side * 1.215 - 0.012, y - 0.015, 1.1), V(side * 1.215 + 0.012, y + 0.015, 1.26))
            emit(detail, kit.geo_lathe([(0.021, -0.02), (0.026, -0.02), (0.026, 0.02), (0.021, 0.02)], 8), "rust_iron", Matrix.Translation(V(side * 1.215, y, 1.1)) @ Matrix.Rotation(-math.pi * 0.5, 4, 'X'), "given", True)
    tank = Matrix.Translation(V(-1.06, -0.4, 1.135)) @ Matrix.Rotation(-math.pi * 0.5, 4, 'X')
    emit(frame, kit.geo_lathe([(0.0, 0.0), (0.07, 0.0), (0.108, 0.04), (0.108, 0.76), (0.07, 0.8), (0.0, 0.8)], 20), "loco_black", tank, "given", True)
    for offset in (0.16, 0.64):
        emit(detail, kit.geo_lathe([(0.111, offset - 0.02), (0.117, offset - 0.02), (0.117, offset + 0.02), (0.111, offset + 0.02)], 20), "rust_iron", tank, "given", True)
    rk.pipe(detail, "rust_iron", [V(-1.06, -0.42, 1.135), V(-1.06, -0.5, 1.135), V(-1.06, -0.5, 0.8), V(-0.6, -0.5, 0.8)], 0.012, 6, 0.03)
    block(frame, "loco_black", V(0.9, 0.55, 0.74), V(1.18, 0.85, 1.2), 0.012)
    for z in (0.84, 1.1):
        block(detail, "rust_iron", V(1.18, 0.57, z - 0.015), V(1.187, 0.83, z + 0.015))
    rk.lathe(detail, "rust_iron", V(1.187, 0.7, 0.97), X, [(0.0, 0.0), (0.016, 0.0), (0.016, 0.03), (0.0, 0.03)], 8)
    block(frame, "loco_black", V(0.92, -0.85, 0.8), V(1.18, -0.55, 1.2), 0.02)
    rk.lathe(frame, "loco_black", V(-1.04, -0.7, 0.66), Z, [(0.0, 0.0), (0.14, 0.0), (0.15, 0.02), (0.15, 0.3), (0.11, 0.34), (0.0, 0.34)], 18)
    rk.pipe(detail, "rust_iron", [V(-1.04, -0.7, 1.0), V(-1.04, -0.7, 1.12), V(-0.7, -0.7, 1.12)], 0.014, 6, 0.03)
    b.col("metal", "deck", V(-loco_half, -loco_well, 0.45), V(loco_half, loco_well, loco_deck))
    return frame, detail


def bonnet_outline(half, base, top, radius, steps=6):
    points = [(half, base), (half, top - radius)]
    points += rk.arc_points(half - radius, top - radius, radius, 0.0, math.pi * 0.5, steps)[1:]
    return points


def cab_arc(x, half, eaves, rise):
    return eaves + rise * (1.0 - (x / half) ** 2)


def window_trim(part, matrix, a0, a1, z0, z1, name="loco_black", width=0.025):
    for fx0, fx1, fz0, fz1 in ((a0 - width, a1 + width, z0 - width, z0), (a0 - width, a1 + width, z1, z1 + width), (a0 - width, a0, z0, z1), (a1, a1 + width, z0, z1)):
        local_block(part, name, matrix, fx0, fx1, -0.01, 0.004, fz0, fz1)


def slab_of(frame, outline, holes, t0, t1, sides=True):
    return kit.geo_slab(frame[0], frame[1], frame[2], frame[3], outline, holes, t0, t1, sides)


def ring_hole(cx, cz, radius, sides=18):
    return [(cx + radius * math.cos(tau * s / sides), cz + radius * math.sin(tau * s / sides)) for s in range(sides)]


def door_span(index):
    start = bonnet_y0 + 0.06 + index * door_pitch
    return start, start + door_width


def loco_bonnet(b, rng, detail):
    body = b.part("body", 40.0, 50)
    half = bonnet_half
    base = loco_deck
    top = bonnet_top
    radius = 0.16
    y0 = bonnet_y0
    y1 = bonnet_y1
    side_outline = bonnet_outline(half, base, top, radius, 10)
    for side in (-1.0, 1.0):
        frame = kit.plane(V(side * half, 0.0, 0.0), V(side, 0.0, 0.0))
        a_low, a_high = sorted((frame[1].y * y0, frame[1].y * y1))
        holes = []
        if side == open_door[0]:
            ya, yb = door_span(open_door[1])
            d0, d1 = sorted((frame[1].y * (ya + 0.02), frame[1].y * (yb - 0.02)))
            holes.append(kit.rect(d0, d1, 1.43, 2.47))
        shift = 0.13 if side > 0 else 0.57
        rk.zoned(body, slab_of(frame, kit.rect(a_low, a_high, base, top - radius), holes, -0.006, 0.0), "loco_green", base, None, False, shift)
        arc = rk.geo_sheet([(side * x, z) for x, z in side_outline[1:]], y0, y1, 6)
        rk.remap(arc, lambda s, y, shift=shift, side=side: (side * y / 2.0 + shift, (top - radius - base + s) / 2.0))
        emit(body, rk.away(arc, V(0.0, 1.0, 2.0)), "loco_green", None, "texture", True)
    crown = [(-half + radius, top), (-0.3, top + 0.012), (0.0, top + 0.016), (0.3, top + 0.012), (half - radius, top)]
    geo = rk.geo_sheet(crown, y0, y1, 6)
    rk.remap(geo, lambda s, y: (y / 2.0 + 0.31, 0.2 + s / 2.0))
    emit(body, rk.facing(geo, Z), "loco_green", None, "texture", True)
    closed = list(side_outline) + list(reversed(crown[1:-1])) + [(-x, z) for x, z in reversed(side_outline)]
    front = kit.geo_slab(V(0.0, y1, 0.0), X, Z, Y, closed, [kit.rect(-0.5, 0.5, 1.5, 2.5)], -0.02, 0.0)
    rk.zoned(body, front, "loco_green", base)
    core = kit.Geo([V(-0.62, y1 - 0.06, 1.38), V(0.62, y1 - 0.06, 1.38), V(0.62, y1 - 0.06, 2.62), V(-0.62, y1 - 0.06, 2.62)], [(0, 1, 2, 3)])
    emit(body, rk.facing(core, Y), "soot", None, "box", False)
    for index in range(34):
        x = -0.495 + index * 0.03
        block(detail, "loco_black", V(x - 0.005, y1 - 0.05, 1.5), V(x + 0.005, y1 - 0.02, 2.5))
    for z in (1.75, 2.0, 2.25):
        block(detail, "loco_black", V(-0.5, y1 - 0.03, z - 0.012), V(0.5, y1 - 0.012, z + 0.012))
    for x0, x1, z0, z1 in ((-0.54, 0.54, 1.46, 1.5), (-0.54, 0.54, 2.5, 2.54), (-0.54, -0.5, 1.5, 2.5), (0.5, 0.54, 1.5, 2.5)):
        block(detail, "loco_black", V(x0, y1 - 0.01, z0), V(x1, y1 + 0.025, z1), 0.006)
    for x in (-0.52, 0.52):
        for z in (1.48, 2.0, 2.52):
            rk.prism_bolt(detail, "rust_iron", V(x, y1 + 0.025, z), Y, 0.022, 0.01, 6)
    for x in (-0.63, 0.63):
        rk.rivets(detail, "loco_green", V(x, y1, 1.42), V(x, y1, 2.5), 0.12, Y, 0.009)
        stands = [(V(x, y1 + 0.06, z), V(0.0, 0.06, 0.0)) for z in (1.58, 2.38)]
        rk.handrail(detail, "loco_black", [V(x, y1 + 0.06, 1.54), V(x, y1 + 0.06, 2.42)], 0.013, stands)
    for position in lamp_positions:
        round_lamp(detail, position, Y, 0.072, "lens_clear", "loco_black", "lamp_glow_warm", 32)
        b.light("warm", position + Y * 0.08)
    for side in (-1.0, 1.0):
        normal = V(side, 0.0, 0.0)
        along = V(0.0, side, 0.0)
        for index in range(4):
            ya, yb = door_span(index)
            z0 = 1.4
            z1 = 2.5
            for hinge in (z0 + 0.15, (z0 + z1) * 0.5, z1 - 0.15):
                rk.lathe(detail, "loco_black", V(side * (half + 0.014), yb + 0.006, hinge - 0.05), Z, [(0.0, 0.0), (0.012, 0.0), (0.012, 0.1), (0.0, 0.1)], 8)
            if (side, index) == open_door:
                swing = Matrix.Translation(V(side * (half + 0.016), yb + 0.012, (z0 + z1) * 0.5)) @ Matrix.Rotation(-side * 0.035, 4, 'Z') @ Matrix.Translation(V(side * 0.006, door_width * 0.5, 0.0))
                leaf = rk.planar_uv(kit.geo_cbox(0.01, door_width, z1 - z0, 0.004), "loco_green", V(0.0, 0.0, -(z1 - z0) * 0.5), Y, Z, 1.0, (0.4, 0.0))
                emit(body, leaf, "loco_green", swing, "texture", False)
                for offset in (-0.22, 0.22):
                    local_block(detail, "loco_green", swing, side * 0.005, side * 0.02, offset - 0.015, offset + 0.015, -0.5, 0.5)
                continue
            if (side, index - 1) != open_door:
                matrix = Matrix.Translation(V(side * (half + 0.004), (ya + yb) * 0.5, (z0 + z1) * 0.5))
                rk.planar(body, kit.geo_cbox(0.01, door_width, z1 - z0, 0.004), "loco_green", V(0.0, 0.0, z0), Y, Z, matrix, False, 1.0, (rng.random(), 0.0))
                handle_y = ya + 0.1 + rng.uniform(-0.01, 0.01)
                rk.lathe(detail, "rust_iron", V(side * (half + 0.009), handle_y, z0 + 0.5), normal, [(0.0, 0.0), (0.014, 0.0), (0.014, 0.03), (0.0, 0.03)], 8)
                block(detail, "rust_iron", V(side * (half + 0.035) - 0.006, handle_y - 0.02, z0 + 0.44), V(side * (half + 0.035) + 0.006, handle_y + 0.02, z0 + 0.56))
                for corner_y in (ya + 0.035, yb - 0.035):
                    rk.rivets(detail, "loco_green", V(side * (half + 0.009), corner_y, z0 + 0.06), V(side * (half + 0.009), corner_y, z1 - 0.06), 0.16, normal, 0.007)
            if index in (0, 1):
                origin = V(side * (half + 0.009), ya + 0.13 if side > 0 else yb - 0.13, 1.92)
                rk.louvres(detail, "loco_green", origin, along, Z, normal, door_width - 0.26, 9, 0.055)
            elif (side, index - 1) != open_door:
                rk.rivets(detail, "loco_green", V(side * (half + 0.009), ya + 0.1, 2.2), V(side * (half + 0.009), yb - 0.1, 2.2), 0.14, normal, 0.008)
        rk.rivets(detail, "loco_green", V(side * half, y0 + 0.06, 1.35), V(side * half, y1 - 0.06, 1.35), 0.14, normal, 0.009)
        stands = [(V(side * (half + 0.075), y, 2.6), V(side * 0.075, 0.0, 0.0)) for y in (-0.5, 0.5, 1.5, 2.45)]
        rk.handrail(detail, "loco_black", [V(side * (half + 0.075), -0.6, 2.6), V(side * (half + 0.075), 2.5, 2.6)], 0.014, stands)
        block(body, "loco_green", V(side * half - 0.006, y0, 2.54), V(side * half + 0.014, y1, 2.56))
        for index in range(1, 4):
            y = door_span(index)[0] - 0.015
            rk.zoned(body, kit.geo_box(0.004, 0.03, 1.16), "loco_green", base, Matrix.Translation(V(side * (half + 0.002), y, 1.94)), False, 0.9)
        rk.rivets(detail, "loco_green", V(side * 0.56, y0 + 0.1, top + 0.002), V(side * 0.56, y1 - 0.1, top + 0.002), 0.2, Z, 0.008)
    for y in (0.25, 1.25):
        local_block(body, "loco_green", Matrix.Translation(V(0.0, y, top + 0.012)), -0.32, 0.32, -0.3, 0.3, 0.0, 0.014, 0.004)
        for sx in (-1.0, 1.0):
            rk.pipe(detail, "rust_iron", [V(sx * 0.2, y - 0.06, top + 0.026), V(sx * 0.2, y - 0.06, top + 0.06), V(sx * 0.2, y + 0.06, top + 0.06), V(sx * 0.2, y + 0.06, top + 0.026)], 0.007, 6, 0.02)
            for corner in (-0.26, 0.26):
                rk.prism_bolt(detail, "rust_iron", V(sx * 0.28, y + corner, top + 0.026), Z, 0.02, 0.008, 6)
    for sx in (-1.0, 1.0):
        for y in (-0.5, 2.36):
            rk.pipe(detail, "rust_iron", [V(sx * 0.42, y - 0.05, top + 0.005), V(sx * 0.42, y - 0.05, top + 0.07), V(sx * 0.42, y + 0.05, top + 0.07), V(sx * 0.42, y + 0.05, top + 0.005)], 0.011, 6, 0.03)
    rk.lathe(detail, "loco_black", stack_position, Z, [(0.19, 0.0), (0.19, 0.02), (0.11, 0.025), (0.1, 0.06), (0.115, 0.3), (0.13, 0.5), (0.155, 0.6), (0.175, 0.66), (0.182, 0.675), (0.18, 0.69), (0.165, 0.69)], 40)
    rk.lathe(detail, "soot", stack_position, Z, [(0.165, 0.69), (0.12, 0.5), (0.09, 0.2), (0.0, 0.2)], 40)
    for angle in range(6):
        rk.prism_bolt(detail, "rust_iron", stack_position + V(math.cos(angle * tau / 6.0) * 0.155, math.sin(angle * tau / 6.0) * 0.155, 0.02), Z, 0.024, 0.012, 6)
    rk.lathe(detail, "loco_black", V(0.0, -0.36, top + 0.01), Z, [(0.11, 0.0), (0.11, 0.1), (0.2, 0.12), (0.2, 0.15), (0.1, 0.2), (0.0, 0.21)], 20)
    rk.lathe(detail, "rust_iron", V(0.0, 2.38, top + 0.012), Z, [(0.07, 0.0), (0.07, 0.035), (0.085, 0.035), (0.085, 0.06), (0.03, 0.07), (0.0, 0.07)], 14)
    b.col("metal", "bonnet", V(-half, y0, base), V(half, y1 + 0.02, top))
    return body


def loco_cab(b, rng, body, detail):
    cab = b.part("cab", 40.0, 50)
    glass = b.part("glass", 30.0)
    half = loco_half
    y0 = cab_y0
    y1 = cab_y1
    floor = loco_deck
    eaves = cab_eaves
    rise = cab_rise
    skin = 0.02
    wall = 2.0 * skin
    split = 2.2
    steps = 24
    arc = [(half - 2.0 * half * s / steps, cab_arc(half - 2.0 * half * s / steps, half, eaves, rise)) for s in range(steps + 1)]
    inner_arc = [(max(min(x, half - skin), -half + skin), z - 0.02) for x, z in arc]
    door = (-0.47, 0.47, 3.35)
    side_window = (-2.2, -1.1, 2.3, 3.05)
    front_windows = [(0.78, 1.2, 2.3, 3.05, "shard"), (-1.2, -0.78, 2.3, 3.05, "whole"), (-0.5, 0.5, 2.86, 3.16, "shard")]
    ports = [(0.98, 2.72, 0.15, "whole"), (-0.98, 2.72, 0.15, "shard")]
    frame = kit.plane(V(0.0, y1, 0.0), Y)
    flip = frame[1].x
    holes = [kit.rect(min(flip * w[0], flip * w[1]), max(flip * w[0], flip * w[1]), w[2], w[3]) for w in front_windows]
    rk.zoned(body, slab_of(frame, [(-half, floor), (half, floor)] + arc, holes, -skin, 0.0), "loco_green", floor, None, False, 0.21)
    rk.zoned(cab, slab_of(frame, kit.rect(-half + skin, half - skin, floor, split), [], -wall, -skin, False), "loco_green", floor, None, False, 0.4)
    rk.planar(cab, slab_of(frame, [(-half + skin, split), (half - skin, split)] + inner_arc, holes, -wall, -skin, True), "coach_livery", V(0.0, 0.0, 0.74), X, Z, None, False, 0.685, (0.37, 0.0))
    matrix = kit.frame_matrix(frame)
    for w, hole in zip(front_windows, holes):
        kit.pane(glass, matrix, hole[0][0], hole[1][0], w[2], w[3], skin * 0.5, w[4], rng)
        window_trim(detail, matrix, hole[0][0], hole[1][0], w[2], w[3])
    frame = kit.plane(V(0.0, y0, 0.0), -Y)
    flip = frame[1].x
    port_holes = [ring_hole(flip * cx, cz, radius) for cx, cz, radius, state in ports]
    outline = [(-half, floor), (door[0], floor), (door[0], door[2]), (door[1], door[2]), (door[1], floor), (half, floor)] + arc
    rk.zoned(body, slab_of(frame, outline, port_holes, -skin, 0.0), "loco_green", floor, None, False, 0.63)
    for a0, a1 in ((-half + skin, door[0]), (door[1], half - skin)):
        rk.zoned(cab, slab_of(frame, kit.rect(a0, a1, floor, split), [], -wall, -skin, True), "loco_green", floor, None, False, 0.4)
    upper = [(-half + skin, split), (door[0], split), (door[0], door[2]), (door[1], door[2]), (door[1], split), (half - skin, split)] + inner_arc
    rk.planar(cab, slab_of(frame, upper, port_holes, -wall, -skin, True), "coach_livery", V(0.0, 0.0, 0.74), X, Z, None, False, 0.685, (0.61, 0.0))
    for cx, cz, radius, state in ports:
        if state == "whole":
            emit(glass, kit.geo_lathe([(0.0, 0.0), (radius, 0.0), (radius, 0.004), (0.0, 0.004)], 18), "glass_dirty", rk.frame_along(V(cx, y0 + skin - 0.002, cz), -Y), "box", False)
        else:
            shard = [(flip * cx + radius * math.cos(angle), cz + radius * math.sin(angle)) for angle in (3.4, 3.9, 4.4, 4.9, 5.4, 5.9)] + [(flip * cx + 0.06, cz - 0.04), (flip * cx - 0.03, cz - 0.09), (flip * cx - 0.08, cz - 0.02)]
            emit(glass, slab_of(frame, shard, [], -skin - 0.002, -skin + 0.002), "glass_dirty", None, "box", False)
        rim = [(radius - 0.004, 0.0), (radius + 0.018, 0.0), (radius + 0.018, 0.01), (radius + 0.008, 0.016), (radius - 0.004, 0.016)]
        rk.swatch(detail, kit.geo_lathe(rim, 18), "brass", rk.frame_along(V(cx, y0, cz), -Y))
        rk.swatch(detail, kit.geo_lathe(rim, 18), "brass", rk.frame_along(V(cx, y0 + wall, cz), Y))
        for angle in range(6):
            rk.prism_bolt(detail, "rust_iron", V(cx + math.cos(angle * tau / 6.0) * (radius + 0.018), y0 - 0.012, cz + math.sin(angle * tau / 6.0) * (radius + 0.018)), -Y, 0.014, 0.006, 6)
    for jamb in (door[0] - 0.03, door[1]):
        block(detail, "loco_black", V(jamb, y0 - 0.012, floor), V(jamb + 0.03, y0 + wall + 0.004, door[2]))
    block(detail, "loco_black", V(door[0] - 0.03, y0 - 0.012, door[2]), V(door[1] + 0.03, y0 + wall + 0.004, door[2] + 0.03))
    for side in (-1.0, 1.0):
        leaf = Matrix.Translation(V(side * (door[1] + 0.035), y0 - 0.03, 0.0)) @ Matrix.Rotation(math.radians(-7.0 if side > 0 else 187.0), 4, 'Z')
        width = door[1] - 0.012
        local_block(body, "loco_green", leaf, 0.0, width, -0.015, 0.015, floor + 0.03, 2.3, 0.004)
        for px0, px1, pz0, pz1 in ((0.0, 0.06, 2.3, 3.32), (width - 0.06, width, 2.3, 3.32), (0.06, width - 0.06, 3.24, 3.32)):
            local_block(body, "loco_green", leaf, px0, px1, -0.015, 0.015, pz0, pz1, 0.004)
        kit.pane(glass, leaf, 0.06, width - 0.06, 2.3, 3.24, -0.002, "whole" if side > 0 else "shard", rng)
        for z in (1.62, 2.34, 3.06):
            rk.lathe(detail, "loco_black", V(side * (door[1] + 0.035), y0 - 0.03, z - 0.05), Z, [(0.0, 0.0), (0.014, 0.0), (0.014, 0.1), (0.0, 0.1)], 8)
        local_block(detail, "rust_iron", leaf, width - 0.09, width - 0.03, -0.045, -0.015, 2.1, 2.12)
        rk.lathe(detail, "rust_iron", leaf @ V(width - 0.06, -0.015, 2.11), leaf.to_3x3() @ V(0.0, -1.0, 0.0), [(0.0, 0.0), (0.012, 0.0), (0.012, 0.04), (0.0, 0.04)], 8)
    for side in (-1.0, 1.0):
        stands = [(V(side * 1.2, y0 - 0.055, z), V(0.0, -0.055, 0.0)) for z in (1.64, 2.76)]
        rk.handrail(detail, "loco_black", [V(side * 1.2, y0 - 0.055, 1.6), V(side * 1.2, y0 - 0.055, 2.8)], 0.013, stands)
        for z in (2.19, 3.24):
            rk.rivets(detail, "loco_green", V(side * 0.6, y0, z), V(side * 1.22, y0, z), 0.11, -Y, 0.008)
    for sign, state in ((-1.0, "missing"), (1.0, "shard")):
        x = sign * half
        normal = V(sign, 0.0, 0.0)
        frame = kit.plane(V(x, 0.0, 0.0), normal)
        along = frame[1]
        a_low, a_high = sorted((along.y * y0, along.y * y1))
        w0, w1 = sorted((along.y * side_window[0], along.y * side_window[1]))
        hole = kit.rect(w0, w1, side_window[2], side_window[3])
        rk.zoned(body, slab_of(frame, kit.rect(a_low, a_high, floor, eaves), [hole], -skin, 0.0), "loco_green", floor, None, False, 0.05 if sign > 0 else 0.47)
        rk.zoned(cab, slab_of(frame, kit.rect(a_low + skin, a_high - skin, floor, split), [], -wall, -skin, False), "loco_green", floor, None, False, 0.71)
        rk.planar(cab, slab_of(frame, kit.rect(a_low + skin, a_high - skin, split, eaves - 0.02), [hole], -wall, -skin, True), "coach_livery", V(0.0, 0.0, 0.74), Y, Z, None, False, 0.685, (0.11, 0.0))
        matrix = kit.frame_matrix(frame)
        middle = (w0 + w1) * 0.5
        kit.pane(glass, matrix, w0, middle, side_window[2], side_window[3], skin * 0.5, "whole", rng)
        kit.pane(glass, matrix, middle, w1, side_window[2], side_window[3], skin * 0.5, state, rng)
        window_trim(detail, matrix, w0, w1, side_window[2], side_window[3])
        local_block(detail, "loco_black", matrix, middle - 0.014, middle + 0.014, -0.012, 0.004, side_window[2], side_window[3])
        local_block(detail, "loco_black", matrix, w0 - 0.06, w1 + 0.06, 0.004, 0.03, side_window[3] + 0.04, side_window[3] + 0.055)
        for a in (a_low + 0.035, a_high - 0.035):
            p = kit.frame_point(frame, a, 0.0, 0.003)
            rk.rivets(detail, "loco_green", V(p.x, p.y, floor + 0.08), V(p.x, p.y, eaves - 0.08), 0.13, normal, 0.009)
            rk.zoned(body, kit.geo_box(0.004, 0.07, eaves - floor), "loco_green", floor, Matrix.Translation(V(p.x - normal.x * 0.001, p.y, (floor + eaves) * 0.5)), False, 0.83)
        for z in (2.19, 3.24):
            rk.rivets(detail, "loco_green", kit.frame_point(frame, a_low + 0.1, z, 0.0), kit.frame_point(frame, a_high - 0.1, z, 0.0), 0.11, normal, 0.008)
        rk.rivets(detail, "loco_green", kit.frame_point(frame, a_low + 0.1, floor + 0.06, 0.0), kit.frame_point(frame, a_high - 0.1, floor + 0.06, 0.0), 0.11, normal, 0.008)
        rk.atlas_panel(detail, "number", kit.frame_point(frame, (w0 + w1) * 0.5, 2.02, 0.004), normal, Z, 0.5, 0.125)
        rk.atlas_panel(detail, "builder", kit.frame_point(frame, (w0 + w1) * 0.5, 1.72, 0.004), normal, Z, 0.22, 0.09)
    for side in (-1.0, 1.0):
        for y, normal_y in ((y1, 1.0), (y0, -1.0)):
            rk.zoned(body, kit.geo_box(0.07, 0.004, eaves - floor), "loco_green", floor, Matrix.Translation(V(side * (half - 0.035), y + normal_y * 0.002, (floor + eaves) * 0.5)), False, 0.29)
            rk.rivets(detail, "loco_green", V(side * (half - 0.035), y + normal_y * 0.004, floor + 0.08), V(side * (half - 0.035), y + normal_y * 0.004, eaves - 0.08), 0.13, V(0.0, normal_y, 0.0), 0.009)
        for z in (2.19, 3.24):
            rk.rivets(detail, "loco_green", V(side * 0.78, y1, z), V(side * 1.2, y1, z), 0.105, Y, 0.008)
        pivot = V(side * 0.99, y1 + 0.012, 3.1)
        tip = pivot + V(-side * 0.13, 0.004, -0.3)
        rk.lathe(detail, "loco_black", pivot, Y, [(0.0, 0.0), (0.018, 0.0), (0.018, 0.02), (0.0, 0.024)], 8)
        rk.bar(detail, "loco_black", [pivot + V(0.0, 0.012, 0.0), tip + V(0.0, 0.012, 0.0)], 0.01, 0.004, Y)
        rk.bar(detail, "loco_black", [tip + V(side * 0.06, 0.01, 0.13), tip + V(-side * 0.06, 0.01, -0.13)], 0.012, 0.008, Y)
    roof_half = half + 0.06
    ribs = 32
    top_arc = [(roof_half - 2.0 * roof_half * s / ribs, cab_arc(roof_half - 2.0 * roof_half * s / ribs, roof_half, eaves - 0.01, rise + 0.035)) for s in range(ribs + 1)]
    roof_outline = top_arc + [(x, z - 0.04) for x, z in reversed(top_arc)]
    emit(body, rk.geo_prism(roof_outline, y0 - 0.32, y1 + 0.09, 4), "loco_black", None, "given", True)
    inner = half - skin
    ceiling = rk.geo_sheet([(inner - 2.0 * inner * s / 12.0, cab_arc(inner - 2.0 * inner * s / 12.0, half, eaves, rise) - 0.022) for s in range(13)], y0 + skin, y1 - skin, 1)
    rk.planar(cab, rk.facing(ceiling, -Z), "coach_livery", V(-1.4, 0.0, 0.0), Y, X, None, True, 0.345, (0.0, 0.52))
    raised = [(x, z + 0.006) for x, z in top_arc]
    for y in (y0 - 0.22, (y0 + y1) * 0.5, y1 - 0.02):
        emit(body, rk.facing(rk.geo_sheet(raised, y - 0.03, y + 0.03, 1), Z), "loco_black", None, "given", True)
        for x, z in raised[1:-1:2]:
            rk.rivet(detail, "loco_black", V(x, y, z), Z, 0.009)
    for side in (-1.0, 1.0):
        block(detail, "loco_black", V(side * roof_half - 0.015, y0 - 0.32, eaves - 0.06), V(side * roof_half + 0.015, y1 + 0.09, eaves - 0.02))
        bracket = [(y0, eaves - 0.03), (y0 - 0.28, eaves - 0.03), (y0 - 0.28, eaves - 0.06), (y0, eaves - 0.2)]
        emit(detail, rk.prism_x(bracket, side * (half - 0.03) - 0.006, side * (half - 0.03) + 0.006), "loco_black", None, "given", False)
    rk.lathe(detail, "loco_black", V(0.0, (y0 + y1) * 0.5 - 0.3, eaves + rise + 0.02), Z, [(0.16, 0.0), (0.16, 0.035), (0.22, 0.05), (0.22, 0.065), (0.0, 0.085)], 28)
    for sx in (-0.35, 0.35):
        rk.lathe(detail, "rust_iron", V(sx, y1 - 0.02, cab_arc(sx, half, eaves, rise) + 0.04), V(0.0, 1.0, 0.12), [(0.02, 0.0), (0.022, 0.12), (0.035, 0.2), (0.05, 0.26), (0.06, 0.28), (0.045, 0.27)], 24)
    round_lamp(detail, tail_position, -Y, 0.07, "lens_red")
    kit.floor_boards(cab, "floorboards", -half + wall, half - wall, y0 + wall, y1 - wall, floor + 0.025, "y", rng, 0.025, 0.004, None, (0.14, 0.2), 0.0)
    block(cab, "chequer_plate", V(door[0], y0, floor), V(door[1], y0 + wall, floor + 0.026))
    b.col("metal", "cab_front", V(-half, y1 - wall, floor), V(half, y1, eaves))
    b.col("metal", "cab_rear", V(-half, y0, floor), V(door[0], y0 + wall, eaves))
    b.col("metal", "cab_rear", V(door[1], y0, floor), V(half, y0 + wall, eaves))
    for side in (-1.0, 1.0):
        b.col("metal", "cab_side", V(side * half, y0, floor), V(side * (half - wall), y1, eaves))
    b.col("metal", "cab_roof", V(-roof_half, y0 - 0.32, eaves), V(roof_half, y1 + 0.09, eaves + rise + 0.05))
    return cab, glass


def gauge_dial(part, detail, center, normal, up, radius, index):
    rk.atlas_disc(part, "gauge_%d" % index, center + normal * 0.012, normal, up, radius, 18, "rail_signs", 0.95)
    rk.lathe(detail, "loco_black", center, normal, [(radius * 1.02, 0.0), (radius * 1.02, 0.012)], 18)


def lever(part, base, direction, length, knob="red", radius=0.009, ball=0.022):
    tip = base + direction.normalized() * length
    emit(part, kit.geo_tube([base, tip], kit.circle(radius, 8), True), "loco_black", None, "given", True)
    rk.swatch(part, kit.geo_lathe([(0.0, -ball), (ball * 0.8, -ball * 0.6), (ball, 0.0), (ball * 0.8, ball * 0.6), (0.0, ball)], 10), knob, rk.frame_along(tip, direction))


def loco_interior(b, rng, cab, detail):
    floor = loco_deck + 0.025
    front = cab_y1 - 0.04
    rear = cab_y0 + 0.04
    eaves = cab_eaves
    desk = [(front, floor), (front - 0.48, floor), (front - 0.48, 2.06), (front - 0.32, 2.36), (front, 2.36)]
    rk.zoned(cab, rk.prism_x(desk, -0.56, 0.56), "loco_green", floor, None, False, 0.27)
    panel_up = V(0.0, 0.16, 0.3).normalized()
    panel_normal = V(0.0, -0.3, 0.16).normalized()
    origin = V(0.0, front - 0.4, 2.21)
    for index in range(6):
        center = origin + X * ((index % 3 - 1) * 0.17) + panel_up * ((index // 3 - 0.5) * 0.15) + panel_normal * 0.004
        gauge_dial(cab, detail, center, panel_normal, panel_up, 0.058, index)
    for index, name in enumerate(("fuel", "oil", "on_off", "horn")):
        rk.atlas_panel(detail, name, V(-0.42 + index * 0.28, front - 0.483, 1.95), -Y, Z, 0.12, 0.06)
    for region, x in (("lens_red", -0.48), ("lens_amber", -0.43), ("lens_green", 0.43), ("lens_red", 0.48)):
        rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.014, 0.0), (0.012, 0.01), (0.0, 0.014)], 8), region, rk.frame_along(origin + X * x + panel_up * 0.09 + panel_normal * 0.004, panel_normal))
    block(cab, "loco_black", V(-0.5, front - 0.32, 2.36), V(0.5, front, 2.375), 0.004)
    lever(detail, V(-0.3, front - 0.18, 2.375), V(0.0, -0.35, 1.0), 0.26, "red")
    lever(detail, V(-0.12, front - 0.18, 2.375), V(0.0, 0.25, 1.0), 0.2, "black")
    lever(detail, V(0.12, front - 0.21, 2.375), V(0.0, -0.1, 1.0), 0.17, "brass")
    for x in (-0.3, -0.12, 0.12):
        local_block(detail, "loco_black", Matrix.Translation(V(x, front - 0.19, 2.375)), -0.03, 0.03, -0.09, 0.09, 0.0, 0.012, 0.003)
    rk.lathe(detail, "loco_black", V(0.36, front - 0.21, 2.375), Z, [(0.0, 0.0), (0.06, 0.0), (0.06, 0.05), (0.045, 0.09), (0.0, 0.09)], 14)
    for angle, knob in ((0.5, "brass"), (2.4, "red")):
        lever(detail, V(0.36, front - 0.21, 2.445), V(math.cos(angle), math.sin(angle) * 0.6, 0.18), 0.19, knob, 0.008, 0.018)
    for index, x in enumerate((-0.2, -0.1, 0.0)):
        end = -0.56 - index * 0.07
        path = rk.fillet_path([V(x, front - 0.03, 2.375), V(x, front - 0.03, 2.6 + index * 0.045), V(end, front - 0.03, 2.6 + index * 0.045), V(end, front - 0.03, 3.2)], 0.04)
        rk.swatch(detail, kit.geo_tube(path, kit.circle(0.007, 6), True, Y), "copper", None, True)
    for position in (V(-0.8, front - 0.8, floor), V(0.8, front - 0.8, floor)):
        rk.lathe(detail, "loco_black", position, Z, [(0.0, 0.0), (0.13, 0.0), (0.12, 0.02), (0.035, 0.04), (0.035, 0.5), (0.1, 0.52), (0.1, 0.54), (0.0, 0.54)], 14)
        emit(cab, kit.geo_cbox(0.4, 0.38, 0.08, 0.03), "leather_brown", Matrix.Translation(position + V(0.0, 0.0, 0.58)), "box", True)
        emit(cab, kit.geo_cbox(0.36, 0.06, 0.26, 0.025), "leather_brown", Matrix.Translation(position + V(0.0, -0.2, 0.82)) @ Matrix.Rotation(-0.12, 4, 'X'), "box", True)
        rk.bar(detail, "loco_black", [position + V(0.0, -0.17, 0.54), position + V(0.0, -0.23, 0.7)], 0.012, 0.04, X)
        b.col("fabric", "seat", position + V(-0.2, -0.22, 0.0), position + V(0.2, 0.19, 0.62))
    column = V(1.04, rear + 0.3, floor)
    emit(detail, kit.geo_tube([column, column + V(0.0, 0.0, 0.95)], kit.circle(0.03, 10), True), "loco_black", None, "given", True)
    wheel_center = column + V(0.0, 0.0, 0.98)
    ring = [wheel_center + V(math.cos(tau * s / 20.0) * 0.19, math.sin(tau * s / 20.0) * 0.19, 0.0) for s in range(21)]
    emit(detail, kit.geo_tube(ring, kit.circle(0.013, 8), False, Z), "rust_iron", None, "given", True)
    for s in range(4):
        angle = tau * s / 4.0 + 0.4
        emit(detail, kit.geo_tube([wheel_center, wheel_center + V(math.cos(angle) * 0.19, math.sin(angle) * 0.19, 0.0)], kit.circle(0.009, 6), False), "rust_iron", None, "given", True)
    rk.lathe(detail, "loco_black", wheel_center - V(0.0, 0.0, 0.04), Z, [(0.0, 0.0), (0.04, 0.0), (0.04, 0.06), (0.0, 0.07)], 10)
    extinguisher = V(-0.84, rear + 0.085, 1.9)
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.065, 0.0), (0.07, 0.02), (0.07, 0.36), (0.045, 0.42), (0.02, 0.44), (0.02, 0.47), (0.0, 0.47)], 14), "red", Matrix.Translation(extinguisher - V(0.0, 0.0, 0.25)))
    rk.atlas_panel(detail, "fire", extinguisher + V(0.0, 0.072, -0.08), Y, Z, 0.09, 0.12)
    rk.pipe(detail, "loco_black", [extinguisher + V(0.0, 0.0, 0.2), extinguisher + V(0.07, 0.03, 0.22), extinguisher + V(0.1, 0.04, 0.05), extinguisher + V(0.09, 0.04, -0.12)], 0.009, 6, 0.03)
    for z0, z1 in ((-0.12, -0.08), (0.06, 0.1)):
        block(detail, "loco_black", extinguisher + V(-0.08, -0.085, z0), extinguisher + V(0.08, -0.06, z1))
    locker = (V(-1.24, front - 0.42, floor), V(-0.64, front, floor + 0.9))
    block(cab, "loco_green", locker[0], locker[1], 0.006)
    local_block(cab, "loco_green", Matrix.Translation(V(-0.66, front - 0.432, floor + 0.04)) @ Matrix.Rotation(math.radians(-145.0), 4, 'Z'), 0.0, 0.56, 0.0, 0.012, 0.0, 0.82, 0.003)
    b.col("metal", "locker", locker[0], locker[1])
    panel = V(0.635, front - 0.001, 2.62)
    block(cab, "loco_black", panel + V(-0.1, -0.05, -0.2), panel + V(0.1, 0.0, 0.2), 0.006)
    for index, name in enumerate(("engine_stop", "brake", "vacuum", "sand")):
        rk.atlas_panel(detail, name, panel + V(0.0, -0.052, 0.135 - 0.09 * index), -Y, Z, 0.15, 0.075)
    rk.pipe(detail, "loco_black", [panel + V(0.0, -0.025, 0.2), panel + V(0.0, -0.025, 0.72)], 0.012, 6)
    lamp = V(0.0, (cab_y0 + cab_y1) * 0.5, eaves + cab_rise - 0.06)
    rk.lathe(detail, "loco_black", lamp, -Z, [(0.0, -0.02), (0.085, -0.02), (0.085, 0.0), (0.07, 0.012)], 14)
    rk.swatch(detail, kit.geo_lathe([(0.07, 0.0), (0.06, 0.04), (0.03, 0.06), (0.0, 0.065)], 14), "lens_clear", rk.frame_along(lamp, -Z))
    b.light("warm", lamp - V(0.0, 0.0, 0.12))
    block(cab, "floorboards", V(-1.25, front - 0.018, 2.17), V(1.25, front, 2.23), 0.004, "board")
    for x0, x1 in ((-1.25, -0.5), (0.5, 1.25)):
        block(cab, "floorboards", V(x0, rear, 2.17), V(x1, rear + 0.018, 2.23), 0.004, "board")
    rk.atlas_panel(detail, "timetable", V(0.86, rear + 0.006, 1.85), Y, Z, 0.22, 0.32)
    b.col("metal", "desk", V(-0.56, front - 0.48, floor), V(0.56, front, 2.36))
    block(detail, "loco_black", V(-1.0 - 0.06, front - 0.07, 3.14), V(-1.0 + 0.06, front, 3.21), 0.006)
    block(detail, "loco_black", V(1.0 - 0.06, front - 0.07, 3.14), V(1.0 + 0.06, front, 3.21), 0.006)
    block(cab, "floorboards", V(-0.45, front - 0.13, 2.76), V(0.45, front, 2.785), 0.004, "board")
    for x in (-0.38, 0.38):
        rk.bar(detail, "rust_iron", [V(x, front - 0.12, 2.76), V(x, front - 0.005, 2.66)], 0.004, 0.02, X)
    rk.lathe(detail, "rust_iron", V(-0.27, front - 0.065, 2.785), Z, [(0.0, 0.0), (0.048, 0.0), (0.05, 0.11), (0.03, 0.125), (0.03, 0.135), (0.0, 0.135)], 14)
    rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.036, 0.0), (0.04, 0.08), (0.036, 0.08), (0.033, 0.008), (0.0, 0.008)], 12), "white", Matrix.Translation(V(0.08, front - 0.06, 2.785)))
    rk.lathe(detail, "rust_iron", V(0.3, front - 0.065, 2.785), Z, [(0.0, 0.0), (0.045, 0.0), (0.045, 0.06), (0.012, 0.1), (0.0, 0.1)], 12)
    rk.pipe(detail, "rust_iron", [V(0.3, front - 0.065, 2.87), V(0.36, front - 0.065, 2.93), V(0.42, front - 0.065, 2.95)], 0.005, 5)
    heater = (V(0.62, front - 0.28, floor), V(1.2, front, floor + 0.42))
    block(cab, "loco_black", heater[0], heater[1], 0.01)
    for index in range(9):
        x = 0.67 + index * 0.06
        block(detail, "rust_iron", V(x - 0.006, front - 0.305, floor + 0.05), V(x + 0.006, front - 0.28, floor + 0.38))
    b.col("metal", "heater", heater[0], heater[1])
    block(cab, "loco_black", V(-1.258, front - 1.2, 1.78), V(-1.2, front - 0.86, 2.12), 0.006)
    rk.pipe(detail, "loco_black", [V(-1.23, front - 1.03, 1.78), V(-1.23, front - 1.03, floor + 0.03), V(-1.23, front - 0.5, floor + 0.03)], 0.011, 6, 0.03)
    rk.swatch(detail, kit.geo_cbox(0.14, 0.2, 0.025, 0.004), "cream", Matrix.Translation(V(-0.43, front - 0.16, 2.3885)) @ Matrix.Rotation(0.2, 4, 'Z'), False)
    rk.atlas_panel(detail, "timetable", V(-0.43, front - 0.16, 2.402), Z, V(-math.sin(0.2), math.cos(0.2), 0.0), 0.12, 0.18)
    top = V(0.72, front - 0.7, cab_arc(0.72, loco_half, eaves, cab_rise) - 0.03)
    rk.chain(detail, "rust_iron", [top, top - V(0.0, 0.0, 0.42)], 0.03, 0.014, 0.0032, None, 4, 2)
    emit(detail, kit.geo_tube([top - V(0.05, 0.0, 0.44), top - V(-0.05, 0.0, 0.44)], kit.circle(0.012, 6), True), "timber_beam", None, "given", True)
    emit(detail, kit.geo_box(0.12, 0.26, 0.012), "chequer_plate", Matrix.Translation(V(-0.8, front - 0.54, floor + 0.04)) @ Matrix.Rotation(-0.3, 4, 'X'), "box")
    rk.atlas_panel(detail, "notice", V(1.2585, front - 0.95, 1.86), -X, Z, 0.2, 0.25)


def loco_engine(b, rng):
    engine = b.part("engine", 40.0, 50)
    half = bonnet_half
    rk.inside_box(engine, "soot", V(-half + 0.006, bonnet_y0 + 0.01, loco_deck), V(half - 0.0065, bonnet_y1 - 0.13, bonnet_top - 0.01), ("bottom", "right") if open_door[0] > 0 else ("bottom", "left"))
    for sx in (-1.0, 1.0):
        block(engine, "loco_black", V(sx * 0.27 - 0.04, -0.2, 1.3), V(sx * 0.27 + 0.04, 2.0, 1.42))
    block(engine, "loco_black", V(-0.3, -0.05, 1.42), V(0.3, 1.9, 1.98), 0.025)
    heads = [0.1 + index * 0.3 for index in range(6)]
    for y in heads:
        emit(engine, kit.geo_cbox(0.34, 0.24, 0.13, 0.04), "rust_iron", Matrix.Translation(V(0.0, y, 2.045)), "box", True)
        for sx in (-0.1, 0.1):
            rk.prism_bolt(engine, "rust_iron", V(sx, y, 2.11), Z, 0.022, 0.012, 6)
        rk.pipe(engine, "rust_iron", [V(0.16, y, 2.0), V(0.34, y, 2.0)], 0.03, 10)
    rk.pipe(engine, "rust_iron", [V(0.34, 0.0, 2.0), V(0.34, 1.75, 2.0), V(0.2, 2.0, 2.25), V(0.0, 2.0, 2.7)], 0.048, 12, 0.15)
    block(engine, "loco_black", V(0.32, 0.4, 1.55), V(0.5, 1.0, 1.8), 0.015)
    for index in range(6):
        start = V(0.41, 0.46 + index * 0.09, 1.8)
        path = rk.fillet_path([start, start + V(0.0, 0.0, 0.12 + index * 0.01), V(0.26, heads[index], 2.13 + index * 0.004), V(0.12, heads[index], 2.12)], 0.03, 3)
        rk.swatch(engine, kit.geo_tube(path, kit.circle(0.005, 6), False, Y), "copper", None, True)
    rk.lathe(engine, "loco_black", V(0.0, -0.05, 1.72), -Y, [(0.0, 0.0), (0.36, 0.0), (0.36, 0.22), (0.3, 0.26), (0.0, 0.26)], 24)
    rk.lathe(engine, "rust_iron", V(0.43, 1.2, 1.64), Y, [(0.0, 0.0), (0.085, 0.0), (0.09, 0.02), (0.09, 0.28), (0.06, 0.3), (0.0, 0.3)], 14)
    rk.lathe(engine, "loco_black", V(0.0, 2.1, 2.0), Y, [(0.0, 0.0), (0.09, 0.0), (0.09, 0.08), (0.0, 0.08)], 12)
    for blade in range(6):
        angle = tau * blade / 6.0
        out = V(math.cos(angle), 0.0, math.sin(angle))
        side = V(-out.z, 0.0, out.x)
        points = [V(0.0, 2.12, 2.0) + out * 0.08 - side * 0.04, V(0.0, 2.18, 2.0) + out * 0.08 + side * 0.04, V(0.0, 2.2, 2.0) + out * 0.42 + side * 0.09, V(0.0, 2.12, 2.0) + out * 0.42 - side * 0.09]
        emit(engine, kit.Geo(points, [(0, 1, 2, 3), (3, 2, 1, 0)]), "loco_black", None, "box", False)
    rk.lathe(engine, "rust_iron", V(-0.31, 0.8, 1.9), V(-1.0, 0.0, 0.6), [(0.0, 0.0), (0.035, 0.0), (0.035, 0.08), (0.05, 0.08), (0.05, 0.1), (0.0, 0.105)], 12)
    return engine


def loco_extras(b, rng, body, detail):
    for side in (-1.0, 1.0):
        edge = side * 1.265
        posts = [V(edge, y, loco_deck) for y in (-0.56, 0.47, 1.5, 2.5)]
        for base in posts:
            post(detail, base, 0.95)
            for angle in range(4):
                rk.prism_bolt(detail, "rust_iron", base + V(math.cos(angle * tau / 4.0 + 0.78) * 0.03, math.sin(angle * tau / 4.0 + 0.78) * 0.03, 0.0), Z, 0.012, 0.006, 6)
        rk.pipe(detail, "loco_black", [posts[0] + Z * 0.92, posts[-1] + Z * 0.92], 0.015, 8)
        rk.pipe(detail, "loco_black", [posts[0] + Z * 0.5, posts[-1] + Z * 0.5], 0.012, 6)
    emit(detail, kit.geo_tube([V(-1.12, -0.5, 1.322), V(-1.03, 2.2, 1.322)], kit.circle(0.02, 8), True), "timber_beam", None, "given", True)
    rk.pipe(detail, "rust_iron", [V(-1.03, 2.2, 1.322), V(-1.027, 2.32, 1.322), V(-1.0, 2.37, 1.322), V(-0.97, 2.33, 1.322)], 0.009, 6, 0.02)
    bucket = V(0.98, 2.3, loco_deck)
    rk.lathe(detail, "rust_iron", bucket, Z, [(0.0, 0.0), (0.1, 0.0), (0.125, 0.26), (0.118, 0.26), (0.094, 0.008), (0.0, 0.008)], 16)
    rk.pipe(detail, "rust_iron", [bucket + V(-0.123, 0.0, 0.25), bucket + V(-0.1, 0.09, 0.255), bucket + V(0.0, 0.135, 0.262), bucket + V(0.1, 0.09, 0.255), bucket + V(0.123, 0.0, 0.25)], 0.004, 5, 0.03)
    rk.pipe(detail, "loco_black", [V(0.09, (cab_y0 + cab_y1) * 0.5, cab_eaves + cab_rise - 0.04), V(0.09, cab_y1 - 0.08, cab_eaves + cab_rise - 0.04), V(0.635, cab_y1 - 0.07, cab_arc(0.635, loco_half, cab_eaves, cab_rise) - 0.045), V(0.635, cab_y1 - 0.07, 3.34)], 0.011, 6, 0.04)


def loco_radiator(detail):
    y1 = bonnet_y1
    for index in range(62):
        z = 1.515 + index * 0.0158
        block(detail, "loco_black", V(-0.5, y1 - 0.062, z - 0.0016), V(0.5, y1 - 0.051, z + 0.0016), 0.0, "box", None, ("bottom", "back", "left", "right"))
    block(detail, "loco_black", V(-0.235, y1, 2.567), V(0.235, y1 + 0.012, 2.683), 0.003)
    rk.atlas_panel(detail, "number", V(0.0, y1 + 0.0125, 2.625), Y, Z, 0.44, 0.11)
    for x in (-0.212, 0.212):
        rk.prism_bolt(detail, "rust_iron", V(x, y1 + 0.0125, 2.625), Y, 0.014, 0.005, 6)
    for side in (-1.0, 1.0):
        x = side * bonnet_half
        block(detail, "loco_green", V(min(x, x - side * 0.035), y1 - 0.035, loco_deck), V(max(x, x + side * 0.004), y1 + 0.004, 2.54), 0.003)
        rk.rivets(detail, "loco_green", V(x + side * 0.004, y1 - 0.018, loco_deck + 0.08), V(x + side * 0.004, y1 - 0.018, 2.48), 0.12, V(side, 0.0, 0.0), 0.008)


def loco_stack_flap(detail):
    hinge = stack_position + V(0.0, -0.176, 0.705)
    turn = math.radians(40.0)
    center = hinge + V(0.0, 0.18 * math.cos(turn), 0.18 * math.sin(turn))
    normal = V(0.0, -math.sin(turn), math.cos(turn))
    rk.lathe(detail, "loco_black", center, normal, [(0.0, 0.0), (0.19, 0.0), (0.19, 0.008), (0.17, 0.012), (0.0, 0.012)], 32, False)
    block(detail, "loco_black", hinge + V(-0.05, -0.012, -0.03), hinge + V(0.05, 0.012, 0.01), 0.003)
    rk.pipe(detail, "rust_iron", [hinge + V(-0.065, 0.0, 0.0), hinge + V(0.065, 0.0, 0.0)], 0.008, 8)
    arm = hinge + V(0.0, -0.11, -0.04)
    rk.bar(detail, "loco_black", [hinge, arm], 0.02, 0.008, X)
    rk.lathe(detail, "loco_black", arm, V(0.0, -1.0, -0.3), [(0.0, 0.0), (0.03, 0.0), (0.03, 0.05), (0.0, 0.05)], 12, False)


def loco_brakes(detail):
    beams = [axle - 0.55 for axle in loco_axles]
    for y in beams:
        rk.pipe(detail, "rust_iron", [V(-0.8, y, 0.36), V(0.8, y, 0.36)], 0.02, 10)
        for side in (-1.0, 1.0):
            block(detail, "rust_iron", V(side * 0.755 - 0.035, y - 0.03, 0.33), V(side * 0.755 + 0.035, y + 0.07, 0.39), 0.004)
            rk.bar(detail, "rust_iron", [V(side * 0.6, y, 0.375), V(side * 0.6, y + 0.02, 0.215)], 0.05, 0.018, X)
            rk.lathe(detail, "rust_iron", V(side * 0.586, y + 0.018, 0.23), X, [(0.0, 0.0), (0.013, 0.0), (0.013, 0.028), (0.0, 0.028)], 8)
            rk.lathe(detail, "rust_iron", V(side * 0.586, y, 0.36), X, [(0.0, 0.0), (0.016, 0.0), (0.016, 0.028), (0.0, 0.028)], 8)
    for side in (-1.0, 1.0):
        rk.bar(detail, "rust_iron", [V(side * 0.6, beams[0] + 0.02, 0.23), V(side * 0.6, beams[2] - 0.05, 0.23)], 0.045, 0.014, X)
        block(detail, "rust_iron", V(side * 0.6 - 0.012, beams[2] - 0.07, 0.205), V(side * 0.6 + 0.012, beams[2] - 0.03, 0.27), 0.002)
    lever_y = beams[2] - 0.05
    rk.bar(detail, "rust_iron", [V(-0.62, lever_y, 0.245), V(0.62, lever_y, 0.245)], 0.06, 0.016, Y)
    cylinder = V(0.0, -2.52, 0.38)
    rk.lathe(detail, "loco_black", cylinder, Y, [(0.0, 0.0), (0.09, 0.0), (0.112, 0.012), (0.112, 0.35), (0.095, 0.37), (0.0, 0.37)], 28)
    for y in (cylinder.y + 0.012, cylinder.y + 0.358):
        for angle in range(8):
            a = angle * tau / 8.0 + 0.2
            rk.prism_bolt(detail, "rust_iron", V(math.cos(a) * 0.1, y, cylinder.z + math.sin(a) * 0.1), V(0.0, 1.0 if y > cylinder.y + 0.1 else -1.0, 0.0), 0.016, 0.007, 6)
    for y in (cylinder.y + 0.09, cylinder.y + 0.28):
        block(detail, "rust_iron", V(-0.125, y - 0.02, 0.4), V(0.125, y + 0.02, 0.505), 0.003)
    rk.pipe(detail, "rust_iron", [V(0.0, cylinder.y + 0.37, cylinder.z), V(0.0, lever_y - 0.03, cylinder.z)], 0.022, 10)
    rk.bar(detail, "rust_iron", [V(0.0, lever_y - 0.02, cylinder.z + 0.03), V(0.0, lever_y, 0.22)], 0.05, 0.018, X)
    rk.pipe(detail, "loco_black", [V(0.06, cylinder.y + 0.05, cylinder.z + 0.1), V(0.06, cylinder.y + 0.05, 0.47), V(0.3, cylinder.y + 0.05, 0.47), V(0.46, cylinder.y + 0.2, 0.56), V(0.46, -1.75, 0.56)], 0.012, 6, 0.05)


def loco_drives(frame, detail):
    for axle, toward in ((loco_axles[0], -1.0), (loco_axles[2], 1.0)):
        rk.lathe(frame, "loco_black", V(-0.24, axle, wheel_radius), X, [(0.085, 0.0), (0.19, 0.0), (0.2, 0.012), (0.2, 0.04), (0.17, 0.06), (0.17, 0.42), (0.2, 0.44), (0.2, 0.468), (0.19, 0.48), (0.085, 0.48)], 28)
        for end in (-1.0, 1.0):
            for angle in range(10):
                a = angle * tau / 10.0
                rk.prism_bolt(detail, "rust_iron", V(end * 0.24, axle + math.cos(a) * 0.185, wheel_radius + math.sin(a) * 0.185), V(end, 0.0, 0.0), 0.018, 0.008, 6)
        nose = V(0.0, axle + toward * 0.15, 0.46)
        rk.lathe(frame, "loco_black", nose, V(0.0, toward, 0.0), [(0.13, 0.0), (0.13, 0.04), (0.1, 0.07), (0.09, 0.13), (0.11, 0.135), (0.11, 0.16), (0.0, 0.165)], 24)
        a = V(0.0, axle + toward * 0.34, 0.46)
        c = V(0.0, (0.45 if toward < 0 else -0.4) - toward * 0.11, 0.46)
        rk.pipe(frame, "loco_black", [a, c], 0.032, 14)
        for end, sign in ((a, toward), (c, -toward)):
            rk.lathe(detail, "rust_iron", end - V(0.0, sign * 0.035, 0.0), V(0.0, sign, 0.0), [(0.0, 0.0), (0.075, 0.0), (0.075, 0.025), (0.04, 0.035), (0.0, 0.035)], 18)
            block(detail, "rust_iron", end + V(-0.06, -0.012, -0.012), end + V(0.06, 0.012, 0.012), 0.003)
            block(detail, "rust_iron", end + V(-0.012, -0.012, -0.06), end + V(0.012, 0.012, 0.06), 0.003)
    for y, direction in ((0.45, 1.0), (-0.4, -1.0)):
        rk.lathe(frame, "loco_black", V(0.0, y, 0.46), V(0.0, direction, 0.0), [(0.0, 0.0), (0.11, 0.0), (0.11, 0.03), (0.085, 0.045), (0.085, 0.07), (0.0, 0.075)], 20)
    for x in (-0.38, -0.13, 0.13, 0.38):
        for y in (-0.4, 0.45):
            rk.prism_bolt(detail, "rust_iron", V(x, y, 0.58), Y if y > 0 else -Y, 0.022, 0.01, 6)
    rk.lathe(detail, "rust_iron", V(0.46, 0.1, 0.6), Z, [(0.0, 0.0), (0.02, 0.0), (0.02, 0.03), (0.014, 0.05), (0.0, 0.05)], 10)
    rk.lathe(detail, "rust_iron", V(-0.5, -0.1, 0.36), -X, [(0.0, 0.0), (0.025, 0.0), (0.025, 0.02), (0.0, 0.02)], 6)


def loco_underdeck(frame, detail):
    block(frame, "loco_black", V(0.86, -0.45, 0.78), V(1.18, 0.45, 1.22), 0.03)
    for y in (-0.3, 0.0, 0.3):
        block(detail, "rust_iron", V(0.85, y - 0.02, 0.77), V(1.19, y + 0.02, 1.23), 0.004)
        block(detail, "rust_iron", V(1.08, y - 0.02, 1.23), V(1.13, y + 0.02, 1.27), 0.003)
    rk.lathe(detail, "loco_black", V(1.18, 0.16, 0.96), X, [(0.0, 0.0), (0.045, 0.0), (0.045, 0.05), (0.058, 0.055), (0.058, 0.08), (0.03, 0.088), (0.0, 0.09)], 16)
    rk.chain(detail, "rust_iron", [V(1.262, 0.17, 0.95), V(1.24, 0.22, 0.88), V(1.2, 0.26, 0.92)], 0.026, 0.012, 0.003, None, 4, 2)
    rk.pipe(detail, "glass_dirty", [V(1.195, -0.15, 0.84), V(1.195, -0.15, 1.05)], 0.011, 8)
    for z in (0.83, 1.06):
        rk.lathe(detail, "rust_iron", V(1.18, -0.15, z), X, [(0.0, 0.0), (0.02, 0.0), (0.02, 0.03), (0.0, 0.03)], 8)
    rk.lathe(detail, "rust_iron", V(1.02, 0.1, 0.78), -Z, [(0.0, 0.0), (0.028, 0.0), (0.028, 0.02), (0.0, 0.025)], 6)
    box = (V(-1.18, 0.55, 0.84), V(-0.86, 1.3, 1.2))
    block(frame, "loco_black", box[0], box[1], 0.012)
    block(detail, "loco_black", V(-1.192, 0.6, 0.88), V(-1.18, 1.25, 1.16), 0.003)
    for z in (0.93, 1.11):
        rk.lathe(detail, "rust_iron", V(-1.196, 0.6, z - 0.03), Z, [(0.0, 0.0), (0.011, 0.0), (0.011, 0.06), (0.0, 0.06)], 8)
    block(detail, "rust_iron", V(-1.2, 1.17, 1.0), V(-1.192, 1.23, 1.05), 0.002)
    block(detail, "rust_iron", V(-1.215, 1.19, 0.93), V(-1.199, 1.23, 0.98), 0.004)
    rk.pipe(detail, "rust_iron", [V(-1.207, 1.196, 0.98), V(-1.207, 1.196, 1.0), V(-1.207, 1.224, 1.0), V(-1.207, 1.224, 0.98)], 0.003, 5, 0.006)
    cells = (V(-1.18, -1.75, 0.82), V(-0.86, -1.05, 1.2))
    block(frame, "loco_black", cells[0], cells[1], 0.012)
    for y in (-1.6, -1.2):
        rk.pipe(detail, "rust_iron", [V(-1.18, y - 0.06, 1.0), V(-1.215, y - 0.05, 1.0), V(-1.215, y + 0.05, 1.0), V(-1.18, y + 0.06, 1.0)], 0.006, 6, 0.01)
    for y in (-1.68, -1.12):
        for z in (0.88, 1.14):
            rk.prism_bolt(detail, "rust_iron", V(-1.18, y, z), -X, 0.02, 0.008, 6)
    rk.louvres(detail, "loco_black", V(-1.181, -1.62, 0.9), V(0.0, 1.0, 0.0), Z, -X, 0.44, 4, 0.04, 0.01, 0.02)
    for low, high in (box, cells):
        for y in (low.y + 0.08, high.y - 0.08):
            block(detail, "loco_black", V(-1.0, y - 0.025, high.z), V(-0.95, y + 0.025, 1.26), 0.002)


def loco_engine_details(engine, detail):
    for y in (0.15, 0.55, 0.95, 1.35):
        outline = rk.rounded_rect(y - 0.13, 1.5, y + 0.13, 1.84, 0.05, 3)
        emit(engine, kit.geo_slab(V(0.3, 0.0, 0.0), Y, Z, X, outline, [], 0.0, 0.012), "loco_black", None, "box", False)
        for dy, dz in ((-0.1, 1.53), (0.1, 1.53), (-0.1, 1.81), (0.1, 1.81), (-0.11, 1.67), (0.11, 1.67), (0.0, 1.525), (0.0, 1.815)):
            rk.prism_bolt(detail, "rust_iron", V(0.312, y + dy, dz), X, 0.016, 0.007, 6)
    for y in [0.1 + index * 0.3 for index in range(6)]:
        emit(engine, kit.geo_cbox(0.3, 0.2, 0.05, 0.014), "loco_black", Matrix.Translation(V(0.0, y, 2.135)), "box", True)
        for sx in (-0.09, 0.09):
            rk.prism_bolt(detail, "rust_iron", V(sx, y, 2.16), Z, 0.018, 0.01, 6)
        rk.lathe(detail, "rust_iron", V(0.2, y, 2.0), X, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.016), (0.0, 0.016)], 12)
    dynamo = V(0.5, 1.55, 1.78)
    rk.lathe(engine, "loco_black", dynamo, Y, [(0.0, 0.0), (0.09, 0.0), (0.1, 0.015), (0.1, 0.27), (0.09, 0.29), (0.0, 0.29)], 24)
    for index in range(10):
        a = index * tau / 10.0
        block(detail, "loco_black", dynamo + V(math.cos(a) * 0.1 - 0.006, 0.05, math.sin(a) * 0.1 - 0.006), dynamo + V(math.cos(a) * 0.1 + 0.006, 0.24, math.sin(a) * 0.1 + 0.006))
    block(engine, "loco_black", V(0.3, 1.6, 1.68), V(0.43, 1.78, 1.72), 0.004)
    rk.lathe(engine, "loco_black", V(0.5, 1.84, 1.78), Y, [(0.0, 0.0), (0.02, 0.0), (0.02, 0.1), (0.065, 0.1), (0.065, 0.14), (0.0, 0.14)], 20)
    rk.lathe(engine, "loco_black", V(0.0, 1.9, 1.55), Y, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.04), (0.1, 0.04), (0.1, 0.08), (0.0, 0.08)], 24)
    rk.lathe(engine, "loco_black", V(0.0, 1.94, 2.0), Y, [(0.0, 0.0), (0.07, 0.0), (0.07, 0.04), (0.04, 0.05), (0.04, 0.16), (0.0, 0.16)], 20)
    for a, c in (((0.02, 1.65), (0.5, 1.845)), ((0.04, 1.455), (0.52, 1.716)), ((-0.1, 1.55), (-0.07, 2.0)), ((0.1, 1.55), (0.07, 2.0))):
        kit.member(engine, "loco_black", V(a[0], 1.96, a[1]), V(c[0], 1.96, c[1]), 0.008, 0.024, Y, 0.0, "box")
    for path in ([V(0.15, 1.9, 1.9), V(0.45, 1.95, 1.91), V(0.5, 2.2, 2.0), V(0.45, 2.38, 2.2)], [V(-0.15, 1.9, 1.5), V(-0.2, 2.1, 1.48), V(-0.35, 2.36, 1.55)]):
        rk.pipe(engine, "loco_black", path, 0.03, 10, 0.08)
        for start, toward in ((path[0], path[1]), (path[-1], path[-2])):
            direction = (toward - start).normalized()
            rk.lathe(detail, "rust_iron", start + direction * 0.03, direction, [(0.034, 0.0), (0.038, 0.0), (0.038, 0.02), (0.034, 0.02)], 10)
    rk.pipe(engine, "rust_iron", [V(0.32, 1.28, 1.44), V(0.33, 1.28, 1.9)], 0.006, 6)
    rk.pipe(engine, "rust_iron", [V(0.33, 1.255, 1.9), V(0.33, 1.255, 1.935), V(0.33, 1.305, 1.935), V(0.33, 1.305, 1.9)], 0.004, 5, 0.008)
    rk.pipe(engine, "loco_black", [V(0.31, 0.05, 1.94), V(0.31, 1.75, 1.94)], 0.008, 6)
    for y in (0.3, 0.75, 1.2, 1.65):
        block(detail, "rust_iron", V(0.3, y - 0.01, 1.925), V(0.322, y + 0.01, 1.955))
    for path in ([V(0.47, 1.2, 1.6), V(0.47, 1.1, 1.6), V(0.46, 1.0, 1.62)], [V(0.39, 1.2, 1.58), V(0.38, 1.1, 1.56), V(0.37, 1.0, 1.58)]):
        rk.swatch(engine, kit.geo_tube(rk.fillet_path(path, 0.03, 3), kit.circle(0.006, 6), False, X), "copper", None, True)
    for index in range(1, 4):
        y = door_span(index)[0] - 0.015
        block(engine, "loco_black", V(0.64, y - 0.03, loco_deck), V(0.694, y + 0.03, 2.56))
        block(engine, "loco_black", V(-0.694, y - 0.03, loco_deck), V(-0.64, y + 0.03, 2.56))
    for z0, z1 in ((loco_deck + 0.05, loco_deck + 0.1), (2.47, 2.52)):
        block(engine, "loco_black", V(0.65, bonnet_y0 + 0.02, z0), V(0.694, bonnet_y1 - 0.14, z1))


def loco_cab_details(b, rng, cab, detail):
    wall = 0.04
    front = kit.frame_matrix(kit.plane(V(0.0, cab_y1 - wall, 0.0), -Y))
    for x0, x1, z0, z1 in ((0.78, 1.2, 2.3, 3.05), (-1.2, -0.78, 2.3, 3.05), (-0.5, 0.5, 2.86, 3.16)):
        window_trim(detail, front, x0, x1, z0, z1, "loco_black", 0.02)
    for x0, x1 in ((0.78, 1.2), (-1.2, -0.78)):
        local_block(detail, "loco_black", front, x0 - 0.02, x1 + 0.02, -0.16, -0.01, 3.075, 3.085, 0.002)
    for sign in (-1.0, 1.0):
        inner = kit.frame_matrix(kit.plane(V(sign * (loco_half - wall), 0.0, 0.0), V(-sign, 0.0, 0.0)))
        a0, a1 = sorted((-sign * -2.2, -sign * -1.1))
        window_trim(detail, inner, a0, a1, 2.3, 3.05, "loco_black", 0.02)
        local_block(detail, "loco_black", inner, a0 - 0.05, a1 + 0.05, -0.03, 0.0, 2.24, 2.27, 0.002)
        for z in (2.255, 3.075):
            local_block(detail, "rust_iron", inner, a0 - 0.02, a1 + 0.02, -0.012, 0.0, z - 0.006, z + 0.006)
    rear = cab_y0 + wall
    for x in (-0.56, 0.56):
        stands = [(V(x, rear + 0.05, z), V(0.0, 0.05, 0.0)) for z in (1.66, 2.34)]
        rk.handrail(detail, "loco_black", [V(x, rear + 0.05, 1.62), V(x, rear + 0.05, 2.38)], 0.012, stands)
    oil_lamp(detail, V(-0.98, rear + 0.16, loco_deck + 0.025), V(0.4, 1.0, 0.0).normalized())
    can = V(1.0, cab_y1 - 0.62, loco_deck + 0.025)
    rk.lathe(detail, "rust_iron", can, Z, [(0.0, 0.0), (0.075, 0.0), (0.078, 0.01), (0.078, 0.11), (0.03, 0.15), (0.012, 0.16), (0.012, 0.19), (0.0, 0.19)], 16)
    rk.pipe(detail, "rust_iron", [can + V(0.05, 0.0, 0.1), can + V(0.15, 0.0, 0.2), can + V(0.24, 0.0, 0.23)], 0.006, 6, 0.04)
    rk.pipe(detail, "rust_iron", [can + V(-0.06, 0.0, 0.12), can + V(-0.1, 0.0, 0.2), can + V(-0.03, 0.0, 0.25), can + V(0.0, 0.0, 0.17)], 0.005, 5, 0.02)
    bag = Matrix.Translation(V(0.72, rear + 0.3, loco_deck + 0.025)) @ Matrix.Rotation(0.35, 4, 'Z')
    emit(cab, kit.geo_cbox(0.42, 0.2, 0.22, 0.05), "leather_brown", bag @ Matrix.Translation(V(0.0, 0.0, 0.11)), "box", True)
    rk.pipe(detail, "leather_brown", [bag @ V(-0.12, 0.0, 0.22), bag @ V(-0.08, 0.0, 0.3), bag @ V(0.08, 0.0, 0.3), bag @ V(0.12, 0.0, 0.22)], 0.012, 6, 0.04)
    for x in (-0.13, 0.13):
        local_block(detail, "rust_iron", bag, x - 0.02, x + 0.02, -0.105, -0.098, 0.12, 0.2)
    rk.pipe(detail, "loco_black", [V(-1.2, cab_y1 - 0.06, 3.3), V(-1.2, rear + 0.06, 3.3)], 0.01, 6)
    for y in (cab_y1 - 0.4, -1.6, rear + 0.3):
        block(detail, "rust_iron", V(-1.215, y - 0.012, 3.28), V(-1.185, y + 0.012, 3.32))
    rk.swatch(detail, kit.geo_cbox(0.2, 0.012, 0.15, 0.003), "white", Matrix.Translation(V(0.6, rear + 0.006, 2.6)), False)
    rk.swatch(detail, kit.geo_cbox(0.12, 0.004, 0.025, 0.001), "red", Matrix.Translation(V(0.6, rear + 0.014, 2.6)), False)
    rk.swatch(detail, kit.geo_cbox(0.025, 0.004, 0.12, 0.001), "red", Matrix.Translation(V(0.6, rear + 0.0145, 2.6)), False)


def locomotive():
    rk.quality = 2
    b = rk.Build("train_locomotive", 31)
    rng = b.rng
    frame, detail = loco_frames(b, rng)
    body = loco_bonnet(b, rng, detail)
    cab, glass = loco_cab(b, rng, body, detail)
    loco_interior(b, rng, cab, detail)
    engine = loco_engine(b, rng)
    loco_extras(b, rng, body, detail)
    loco_radiator(detail)
    loco_stack_flap(detail)
    loco_brakes(detail)
    loco_drives(frame, detail)
    loco_underdeck(frame, detail)
    loco_engine_details(engine, detail)
    loco_cab_details(b, rng, cab, detail)
    rk.quality = 1
    return b


def locomotive_far():
    b = rk.Build("train_locomotive_far", 32)
    part = b.part("body", 40.0)
    inner = loco_head - loco_beam
    rk.slab(part, V(-loco_half, -loco_well, 1.16), V(loco_half, loco_well, loco_deck), "chequer_plate", "loco_black")
    block(part, "loco_black", V(-neck, -inner, 0.4), V(neck, inner, 1.16), 0.0, "box", None, ("bottom", "top"))
    for direction in (-1.0, 1.0):
        rk.slab(part, V(-neck, direction * loco_well, 1.16), V(neck, direction * inner, loco_deck), "chequer_plate", "loco_black", False)
    for side in (-1.0, 1.0):
        for y0, y1 in ((-inner, -loco_well), (loco_well, inner)):
            far_stairs(part, side, y0, y1, loco_tops)
        for y0, y1 in ((1.98, 2.36), (-2.36, -1.98)):
            block(part, "loco_black", V(side * 0.92, y0, 0.78), V(side * 1.22, y1, 1.16), 0.0, "box", None, ("top",))
    for direction in (-1.0, 1.0):
        wasp_face(part, direction * loco_head, direction, 1.28, 0.7, loco_deck)
        block(part, "loco_black", V(-1.28, direction * inner, 0.7), V(1.28, direction * loco_head, loco_deck), 0.0, "box", None, ("front",) if direction < 0 else ("back",))
        far_buffers(part, direction * loco_head, direction)
    half = bonnet_half
    outline = [(half, loco_deck), (half, 2.58), (half - 0.14, bonnet_top), (-half + 0.14, bonnet_top), (-half, 2.58), (-half, loco_deck)]
    shell = rk.geo_sheet(outline, bonnet_y0, bonnet_y1, 1)
    rk.zoned(part, rk.away(shell, V(0.0, 1.0, 1.8)), "loco_green", loco_deck, None, True)
    front = kit.geo_slab(V(0.0, bonnet_y1, 0.0), X, Z, Y, outline, [], -0.01, 0.0, False)
    rk.zoned(part, front, "loco_green", loco_deck)
    grille = kit.Geo([V(-0.5, bonnet_y1 + 0.002, 1.5), V(0.5, bonnet_y1 + 0.002, 1.5), V(0.5, bonnet_y1 + 0.002, 2.5), V(-0.5, bonnet_y1 + 0.002, 2.5)], [(0, 1, 2, 3)])
    emit(part, rk.facing(grille, Y), "soot", None, "box", False)
    rk.lathe(part, "loco_black", stack_position, Z, [(0.11, 0.0), (0.13, 0.5), (0.18, 0.69), (0.0, 0.69)], 8)
    arc = [(loco_half - 2.0 * loco_half * s / 4.0, cab_arc(loco_half - 2.0 * loco_half * s / 4.0, loco_half, cab_eaves, cab_rise)) for s in range(5)]
    for y, normal, windows in ((cab_y1, Y, [(0.78, 1.2, 2.3, 3.05), (-1.2, -0.78, 2.3, 3.05)]), (cab_y0, -Y, [(-0.47, 0.47, loco_deck, 3.35)])):
        frame = kit.plane(V(0.0, y, 0.0), normal)
        rk.zoned(part, slab_of(frame, [(-loco_half, loco_deck), (loco_half, loco_deck)] + arc, [], -0.01, 0.0, False), "loco_green", loco_deck, None, False, 0.3)
        for w in windows:
            pane = kit.Geo([V(w[0], y + normal.y * 0.004, w[2]), V(w[1], y + normal.y * 0.004, w[2]), V(w[1], y + normal.y * 0.004, w[3]), V(w[0], y + normal.y * 0.004, w[3])], [(0, 1, 2, 3)])
            emit(part, rk.facing(pane, normal), "glass_dirty" if normal.y > 0 else "soot", None, "box", False)
    for sign in (-1.0, 1.0):
        frame = kit.plane(V(sign * loco_half, 0.0, 0.0), V(sign, 0.0, 0.0))
        a_low, a_high = sorted((frame[1].y * cab_y0, frame[1].y * cab_y1))
        rk.zoned(part, slab_of(frame, kit.rect(a_low, a_high, loco_deck, cab_eaves), [], -0.01, 0.0, False), "loco_green", loco_deck, None, False, 0.6)
        x = sign * (loco_half + 0.004)
        pane = kit.Geo([V(x, -2.2, 2.3), V(x, -1.1, 2.3), V(x, -1.1, 3.05), V(x, -2.2, 3.05)], [(0, 1, 2, 3)])
        emit(part, rk.facing(pane, V(sign, 0.0, 0.0)), "glass_dirty", None, "box", False)
    roof_half = loco_half + 0.06
    top_arc = [(roof_half - 2.0 * roof_half * s / 4.0, cab_arc(roof_half - 2.0 * roof_half * s / 4.0, roof_half, cab_eaves, cab_rise + 0.03)) for s in range(5)]
    emit(part, rk.geo_prism(top_arc + [(-roof_half, cab_eaves - 0.04), (roof_half, cab_eaves - 0.04)], cab_y0 - 0.32, cab_y1 + 0.09, 1), "loco_black", None, "given", True)
    return b


wagon_head = 3.0
wagon_body = 2.03
wagon_half = 1.25
wagon_axles = (1.55, -1.55)
wagon_tops = (0.18, 0.54, 0.9)
underframe_top = 1.2
deck_top = 1.27


def w_iron(part, detail, rng, side, axle):
    outline = [(-0.4, 0.95), (0.4, 0.95), (0.4, 0.88), (0.16, 0.33), (-0.16, 0.33), (-0.4, 0.88)]
    holes = [[(-0.085, 0.37), (0.085, 0.37), (0.085, 0.84), (-0.085, 0.84)], [(-0.33, 0.85), (-0.14, 0.85), (-0.14, 0.45)], [(0.33, 0.85), (0.14, 0.45), (0.14, 0.85)]]
    emit(part, kit.geo_slab(V(side * 0.948, axle, 0.0), Y, Z, V(side, 0.0, 0.0), outline, holes, 0.0, 0.014), "loco_black", None, "box")
    for offset in (-0.32, -0.2, 0.2, 0.32):
        rk.prism_bolt(detail, "rust_iron", V(side * 0.962, axle + offset, 0.915), V(side, 0.0, 0.0), 0.026, 0.013, 6)
    emit(part, kit.geo_cbox(0.17, 0.17, 0.2, 0.02), "loco_black", Matrix.Translation(V(side * 1.015, axle, wheel_radius)), "box")
    emit(part, kit.geo_cbox(0.014, 0.13, 0.15, 0.004), "rust_iron", Matrix.Translation(V(side * 1.106, axle, wheel_radius)), "box")
    rk.lathe(part, "loco_black", V(side * 0.895, axle, wheel_radius), V(side, 0.0, 0.0), [(0.076, 0.0), (0.076, 0.04)], 14)
    for offset in (-0.045, 0.045):
        rk.prism_bolt(detail, "rust_iron", V(side * 1.113, axle + offset, wheel_radius + 0.05), V(side, 0.0, 0.0), 0.022, 0.011, 6)
    leaves = 6
    ends = rk.leaf_spring(part, "rust_iron", V(side * 1.0, axle, wheel_radius + 0.1 + leaves * 0.011 + 0.004), 0.84, leaves, 0.085, 0.011, 0.075, Y)
    for end in ends:
        block(part, "loco_black", V(side * 1.0 - 0.05, end.y - 0.03, end.z - 0.02), V(side * 1.0 + 0.05, end.y + 0.03, 0.95), 0.006)


def wagon_brakes(part, detail, rng, side, full=True):
    x = side * 0.975
    for direction in (-1.0, 1.0):
        rk.bar(part, "loco_black", [V(x, direction * 0.22, 0.95), V(x, 0.0, 0.47)], 0.05, 0.012, X)
    rk.lathe(detail, "rust_iron", V(x - side * 0.01, 0.0, 0.48), V(side, 0.0, 0.0), [(0.0, 0.0), (0.05, 0.0), (0.05, 0.03), (0.0, 0.03)], 10)
    lever_x = side * 1.06
    rk.bar(part, "loco_black", [V(lever_x, 0.0, 0.48), V(lever_x, 0.9, 0.57), V(lever_x, 1.72, 0.87), V(lever_x, 1.96, 0.89)], 0.05, 0.014, X, 0.12)
    rk.lathe(detail, "rust_iron", V(lever_x, 1.85, 0.885), Y, [(0.0, 0.0), (0.018, 0.0), (0.022, 0.06), (0.018, 0.12), (0.0, 0.125)], 8)
    guard_x = side * 1.095
    rk.bar(part, "loco_black", [V(guard_x, 1.7, 0.96), V(guard_x, 1.7, 0.56), V(guard_x, 1.78, 0.56), V(guard_x, 1.78, 0.96)], 0.03, 0.008, X, 0.02)
    for index in range(7):
        rk.prism_bolt(detail, "rust_iron", V(guard_x + side * 0.004, 1.7, 0.6 + index * 0.05), V(side, 0.0, 0.0), 0.014, 0.008, 4)
    if full:
        rk.pipe(part, "rust_iron", [V(side * 0.25, 0.0, 0.48), V(side * 1.07, 0.0, 0.48)], 0.025, 8)
        for axle in wagon_axles:
            toward = 1.0 if axle > 0.0 else -1.0
            y = axle - toward * (wheel_radius + 0.05)
            brake_block(detail, side * 0.755, y, wheel_radius, toward)
            rk.bar(detail, "rust_iron", [V(side * 0.755, toward * 0.06, 0.48), V(side * 0.755, y, wheel_radius + 0.02)], 0.035, 0.012, X)
        rk.bar(detail, "rust_iron", [V(side * 0.755, -0.07, 0.48), V(side * 0.755, 0.07, 0.48)], 0.06, 0.02, X)


def wagon_underframe(b, rng, fitted=False, brake_side=1.0, plate="wagon_a", body_half=wagon_half, rails=True):
    frame = b.part("frame", 40.0, 50)
    detail = b.part("detail", 40.0)
    inner = wagon_head - 0.09
    for side in (-1.0, 1.0):
        outline = [(side * 0.935, 0.95), (side * 1.03, 0.95), (side * 1.03, 0.965), (side * 0.95, 0.965), (side * 0.95, 1.185), (side * 1.03, 1.185), (side * 1.03, 1.2), (side * 0.935, 1.2)]
        emit(frame, rk.geo_prism(outline, -wagon_body, wagon_body, 1), "loco_black", None, "given", False)
        rk.rivets(detail, "loco_black", V(side * 0.95, -1.9, 1.13), V(side * 0.95, 1.9, 1.13), 0.25, V(side, 0.0, 0.0), 0.011)
        for axle in wagon_axles:
            w_iron(frame, detail, rng, side, axle)
        block(frame, "loco_black", V(side * 0.3 - 0.04, -inner, 0.98), V(side * 0.3 + 0.04, inner, 1.2))
        block(frame, "loco_black", V(side * (neck - 0.07), -inner, 0.98), V(side * (neck - 0.012), inner, 1.2))
        rk.atlas_panel(detail, plate, V(side * 0.952, -0.62 * side, 1.06), V(side, 0.0, 0.0), Z, 0.26, 0.105)
        block(detail, "rust_iron", V(side * 0.95, 0.38 * side - 0.06, 1.0), V(side * 0.957, 0.38 * side + 0.06, 1.1))
    for y in (-1.0, 0.0, 1.0):
        block(frame, "loco_black", V(-0.935, y - 0.04, 1.0), V(0.935, y + 0.04, 1.2))
    for direction in (-1.0, 1.0):
        y = direction * wagon_head
        block(frame, "loco_black", V(-1.22, direction * inner, 0.9), V(1.22, y, underframe_top))
        for x in (-1.12, -0.6, 0.6, 1.12):
            rk.rivets(detail, "rust_iron", V(x, y, 0.95), V(x, y, 1.15), 0.1, V(0.0, direction, 0.0), 0.012)
        end_gear(b, detail, y, direction, rng, "loco_black", 1.0, 0.3, 3, fitted)
        fall_plate(frame, detail, y, direction, deck_top)
        rk.slab(frame, V(-neck, direction * wagon_body, underframe_top), V(neck, y, deck_top), "chequer_plate", "loco_black")
        b.col("metal", "end", V(-1.06, direction * inner, 0.86), V(1.06, y + direction * buffer_length, deck_top))
        b.col("metal", "neck", V(-neck, direction * wagon_body, 0.45), V(neck, direction * inner, deck_top))
        for side in (-1.0, 1.0):
            ya, yb = sorted((direction * wagon_body, direction * inner))
            stairwell(b, frame, detail, side, ya, yb, deck_top, body_half, wagon_tops)
            lamp_iron(detail, V(side * 1.05, y, underframe_top), V(0.0, direction, 0.0))
            if rails:
                railing(detail, V(side * 0.6, y - direction * 0.045, underframe_top), V(side * 1.17, y - direction * 0.045, underframe_top), 1.02)
    wagon_brakes(frame, detail, rng, brake_side, True)
    wagon_brakes(frame, detail, rng, -brake_side, False)
    return frame, detail


def wagon_flat():
    b = rk.Build("train_wagon_flat", 41)
    rng = b.rng
    frame, detail = wagon_underframe(b, rng)
    deck = b.part("deck", 40.0, 50)
    load = b.part("load", 40.0)
    kit.floor_boards(deck, "timber_planks_weathered", -wagon_half, wagon_half, -wagon_body, wagon_body, deck_top, "x", rng, 0.07, 0.006, None, (0.17, 0.23), 0.03)
    for side in (-1.0, 1.0):
        block(frame, "loco_black", V(side * 1.2, -wagon_body, underframe_top), V(side * 1.26, wagon_body, 1.36), 0.006)
        for end in (-1.0, 1.0):
            block(frame, "loco_black", V(side * (neck + 0.03), end * (wagon_body - 0.06), underframe_top), V(side * 1.2, end * wagon_body, 1.36), 0.006)
        for index, y in enumerate((-1.35, 0.0, 1.35)):
            block(detail, "loco_black", V(side * 1.26, y - 0.07, 1.0), V(side * 1.34, y + 0.07, 1.2), 0.006)
            rk.rivets(detail, "rust_iron", V(side * 1.342, y, 1.05), V(side * 1.342, y, 1.15), 0.1, V(side, 0.0, 0.0), 0.011)
            if side > 0 and index == 1:
                continue
            lean = rng.uniform(-0.02, 0.04)
            rk.bar(detail, "rust_iron", [V(side * 1.3, y, 1.0), V(side * (1.3 + lean), y + rng.uniform(-0.02, 0.02), 2.15)], 0.07, 0.05, Y)
    base = deck_top + 0.13
    for y in (-1.2, 1.2):
        block(deck, "timber_beam", V(-1.16, y - 0.1, deck_top), V(-0.16, y + 0.1, base), 0.01)
    upper = base + rk.rail_height + 0.025
    for y in (-1.2, 0.0, 1.2):
        block(load, "timber_beam", V(-1.12, y - 0.04, base + rk.rail_height), V(-0.22, y + 0.04, upper), 0.004)
    for count, start, level in ((5, -1.0, base), (4, -0.92, upper)):
        for index in range(count):
            shift = rng.uniform(-0.1, 0.1)
            geo = rk.rail_geo(-1.8 + shift, 1.8 + shift, 2, rng.random() < 0.5, "dull")
            matrix = Matrix.Translation(V(start + index * 0.165 + rng.uniform(-0.008, 0.008), 0.0, level)) @ Matrix.Rotation(rng.uniform(-0.004, 0.004), 4, 'Z')
            emit(load, geo, "rail_steel", matrix, "texture", True)
    rail_level = upper + rk.rail_height
    for y in (-0.75, 0.8):
        path = [V(-1.29, y, 1.13), V(-1.16, y, base + 0.05), V(-1.08, y, rail_level + 0.014), V(-0.26, y, rail_level + 0.014), V(-0.13, y, base + 0.03), V(-0.1, y, deck_top + 0.02)]
        rk.chain(load, "rust_iron", path, 0.075, 0.036, 0.0075, rng, 6, 3)
        rk.lathe(detail, "rust_iron", V(-1.27, y, 1.13), V(-1.0, 0.0, 0.0), [(0.0, 0.0), (0.03, 0.0), (0.03, 0.012), (0.012, 0.02), (0.012, 0.04), (0.0, 0.04)], 8)
        rk.lathe(detail, "rust_iron", V(-0.08, y, deck_top), Z, [(0.0, 0.0), (0.035, 0.0), (0.035, 0.008), (0.014, 0.016), (0.014, 0.03), (0.0, 0.03)], 8)
    quarter = Matrix.Rotation(math.pi * 0.5, 4, 'Z')
    stack_top = deck_top
    for layer in range(2):
        stack_top += 0.13
        for across in range(2 - layer):
            geo = rk.sleeper_geo(rng, rng.randrange(rk.strip_count), (rng.randrange(8), rng.randrange(8)), 2.6, 0.25, 0.13, rng.uniform(0.8, 1.6), (rng.uniform(0.15, 0.4) if rng.random() < 0.5 else 0.0, 0.0), rng.random() < 0.5)
            position = V(0.79 + across * 0.262 + layer * 0.12 + rng.uniform(-0.01, 0.01), 0.35 + rng.uniform(-0.06, 0.06), stack_top + rng.uniform(0.0, 0.004))
            emit(load, geo, "sleeper_timber", Matrix.Translation(position) @ Matrix.Rotation(rng.uniform(-0.03, 0.03) * (2.0 if layer else 1.0), 4, 'Z') @ quarter, "texture", True)
    rk.bar(load, "rust_iron", [V(0.72, -1.55, deck_top + 0.028), V(1.12, -0.95, deck_top + 0.028)], 0.07, 0.05, Z)
    b.col("wood", "deck", V(-wagon_half, -wagon_body, 0.45), V(wagon_half, wagon_body, deck_top))
    b.col("metal", "rails", V(-1.12, -1.92, deck_top), V(-0.2, 1.92, rail_level))
    b.col("wood", "sleepers", V(0.66, -0.98, deck_top), V(1.19, 1.68, deck_top + 0.26))
    return b


def wagon_far_base(part):
    inner = wagon_head - 0.09
    for side in (-1.0, 1.0):
        block(part, "loco_black", V(side * 0.935, -wagon_body, 0.95), V(side * 1.03, wagon_body, underframe_top), 0.0, "box", None, ("top",))
        for axle in wagon_axles:
            block(part, "loco_black", V(side * 0.93, axle - 0.085, wheel_radius - 0.1), V(side * 1.1, axle + 0.085, wheel_radius + 0.1))
            block(part, "rust_iron", V(side * 0.96, axle - 0.42, wheel_radius + 0.12), V(side * 1.04, axle + 0.42, wheel_radius + 0.19), 0.0, "box", None, ("bottom",))
        for y0, y1 in ((-inner, -wagon_body), (wagon_body, inner)):
            far_stairs(part, side, y0, y1, wagon_tops)
    for direction in (-1.0, 1.0):
        y = direction * wagon_head
        rk.slab(part, V(-neck, direction * wagon_body, 0.6), V(neck, y, deck_top), "chequer_plate", "loco_black", False)
        block(part, "loco_black", V(-1.22, direction * inner, 0.9), V(1.22, y, underframe_top), 0.0, "box", None, ("bottom",))
        far_buffers(part, y, direction)


def wagon_flat_far():
    b = rk.Build("train_wagon_flat_far", 42)
    part = b.part("body", 40.0)
    wagon_far_base(part)
    block(part, "timber_planks_weathered", V(-wagon_half, -wagon_body, underframe_top), V(wagon_half, wagon_body, deck_top), 0.0, "box", None, ("bottom",))
    block(part, "rust_iron", V(-1.1, -1.85, deck_top + 0.13), V(-0.22, 1.85, deck_top + 0.43), 0.0, "box", None, ("bottom",))
    block(part, "timber_beam", V(0.66, -0.98, deck_top), V(1.19, 1.68, deck_top + 0.26), 0.0, "box", None, ("bottom",))
    for side in (-1.0, 1.0):
        for y in (-1.35, 0.0, 1.35):
            if not (side > 0 and y == 0.0):
                block(part, "rust_iron", V(side * 1.3 - 0.035, y - 0.025, 1.0), V(side * 1.3 + 0.035, y + 0.025, 2.15), 0.0, "box", None, ("bottom",))
    return b


side_gate = 0.6
end_gate = 0.48
open_wall = 1.25


def wagon_open():
    b = rk.Build("train_wagon_open", 51)
    rng = b.rng
    frame, detail = wagon_underframe(b, rng, False, 1.0, "wagon_b")
    body = b.part("body", 40.0, 50)
    load = b.part("load", 40.0)
    floor = deck_top
    top = floor + open_wall
    skin = 0.03
    kit.floor_boards(body, "timber_planks_weathered", -wagon_half + skin, wagon_half - skin, -wagon_body + skin, wagon_body - skin, floor, "x", rng, 0.07, 0.006, None, (0.17, 0.23), 0.03)
    block(body, "rust_iron", V(-wagon_half, -side_gate, underframe_top), V(-wagon_half + skin, side_gate, floor + 0.002))
    for direction in (-1.0, 1.0):
        block(body, "rust_iron", V(-end_gate, direction * (wagon_body - skin), underframe_top), V(end_gate, direction * wagon_body, floor + 0.002))
    for sign in (-1.0, 1.0):
        side = kit.plane(V(sign * wagon_half, 0.0, 0.0), V(sign, 0.0, 0.0))
        normal = V(sign, 0.0, 0.0)
        opened = sign < 0.0
        outline = kit.rect(-wagon_body, wagon_body, underframe_top, top)
        spans = ((-wagon_body, wagon_body),)
        if opened:
            outline = [(-wagon_body, underframe_top), (wagon_body, underframe_top), (wagon_body, top), (side_gate, top), (side_gate, floor), (-side_gate, floor), (-side_gate, top), (-wagon_body, top)]
            spans = ((-wagon_body, -side_gate), (side_gate, wagon_body))
        rk.zoned(body, slab_of(side, outline, [], -skin * 0.5, 0.0), "wagon_grey", underframe_top, None, False, 0.11 if sign > 0 else 0.53)
        emit(body, slab_of(side, outline, [], -skin, -skin * 0.5), "rust_iron", None, "world", False)
        for a in (-1.99, -1.32, -0.64, 0.64, 1.32, 1.99):
            rk.frame_zoned(body, "wagon_grey", side, a - 0.035, a + 0.035, underframe_top, top, -0.05, 0.0, underframe_top, 0.3)
            rk.rivets(detail, "wagon_grey", kit.frame_point(side, a, floor + 0.1, 0.05), kit.frame_point(side, a, top - 0.1, 0.05), 0.15, normal, 0.009)
            rk.rivets(detail, "rust_iron", kit.frame_point(side, a, floor + 0.12, -skin), kit.frame_point(side, a, top - 0.12, -skin), 0.2, -normal, 0.011)
        for a0, a1 in spans:
            kit.frame_block(body, "loco_black", side, a0, a1, top - 0.012, top + 0.012, -0.06, skin + 0.02)
            rk.rivets(detail, "loco_black", kit.frame_point(side, a0 + 0.08, top + 0.012, 0.03), kit.frame_point(side, a1 - 0.08, top + 0.012, 0.03), 0.17, Z, 0.009)
        rk.atlas_panel(detail, "wagon_b", kit.frame_point(side, -1.64, floor + 0.34, 0.004), normal, Z, 0.34, 0.14)
        if opened:
            leaf = Matrix.Translation(V(sign * (wagon_half + 0.032), 0.0, floor - 0.02)) @ Matrix.Rotation(-sign * math.radians(2.0), 4, 'Y')
            local_block(body, "rust_iron", leaf, -0.012, 0.012, -side_gate + 0.012, side_gate - 0.012, -open_wall + 0.03, 0.0)
            for y in (-0.4, 0.0, 0.4):
                local_block(detail, "loco_black", leaf, -sign * 0.012, -sign * 0.045, y - 0.03, y + 0.03, -open_wall + 0.06, 0.04)
                rk.lathe(detail, "loco_black", V(sign * (wagon_half + 0.032), y - 0.05, floor - 0.02), Y, [(0.0, 0.0), (0.02, 0.0), (0.02, 0.1), (0.0, 0.1)], 8)
            for z in (-0.35, -0.85):
                local_block(detail, "loco_black", leaf, -sign * 0.012, -sign * 0.04, -side_gate + 0.03, side_gate - 0.03, z - 0.025, z + 0.025)
        else:
            rk.frame_zoned(body, "wagon_grey", side, -side_gate, side_gate, floor + 0.56, floor + 0.62, -0.04, 0.0, underframe_top, 0.6)
            for a in (-0.4, 0.0, 0.4):
                kit.frame_block(detail, "loco_black", side, a - 0.03, a + 0.03, underframe_top - 0.04, floor + 0.4, -0.014, 0.0)
                rk.lathe(detail, "loco_black", kit.frame_point(side, a - 0.05, underframe_top + 0.01, 0.02), side[1], [(0.0, 0.0), (0.02, 0.0), (0.02, 0.1), (0.0, 0.1)], 8)
            for a in (-side_gate + 0.035, side_gate - 0.035):
                rk.pipe(detail, "rust_iron", [kit.frame_point(side, a, top - 0.26, 0.065), kit.frame_point(side, a, top - 0.04, 0.065)], 0.012, 6)
    for direction in (-1.0, 1.0):
        end = kit.plane(V(0.0, direction * wagon_body, 0.0), V(0.0, direction, 0.0))
        normal = V(0.0, direction, 0.0)
        outline = [(-wagon_half, underframe_top), (wagon_half, underframe_top), (wagon_half, top), (end_gate, top), (end_gate, floor), (-end_gate, floor), (-end_gate, top), (-wagon_half, top)]
        rk.zoned(body, slab_of(end, outline, [], -skin * 0.5, 0.0), "wagon_grey", underframe_top, None, False, 0.71)
        emit(body, slab_of(end, outline, [], -skin, -skin * 0.5), "rust_iron", None, "world", False)
        for a in (-1.215, -0.515, 0.515, 1.215):
            rk.frame_zoned(body, "wagon_grey", end, a - 0.035, a + 0.035, underframe_top, top, -0.05, 0.0, underframe_top, 0.3)
            rk.rivets(detail, "wagon_grey", kit.frame_point(end, a, floor + 0.1, 0.05), kit.frame_point(end, a, top - 0.1, 0.05), 0.15, normal, 0.009)
        for a0, a1 in ((-wagon_half, -end_gate), (end_gate, wagon_half)):
            kit.frame_block(body, "loco_black", end, a0, a1, top - 0.012, top + 0.012, -0.06, skin + 0.02)
        for side in (-1.0, 1.0):
            hinge = V(side * (end_gate + 0.014), direction * (wagon_body - skin - 0.016), 0.0)
            leaf = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(direction * (-6.0 if side > 0 else 186.0)), 4, 'Z')
            width = end_gate - 0.03
            rk.zoned(body, kit.geo_box(width, 0.02, open_wall - 0.06), "wagon_grey", underframe_top, leaf @ Matrix.Translation(V(width * 0.5, 0.0, floor + 0.03 + (open_wall - 0.06) * 0.5)), False, 0.37)
            for z in (floor + 0.3, floor + 0.9):
                local_block(detail, "loco_black", leaf, 0.0, width, -0.022, 0.022, z - 0.025, z + 0.025)
            for z in (floor + 0.3, floor + 0.9):
                rk.lathe(detail, "loco_black", V(hinge.x, hinge.y, z - 0.05), Z, [(0.0, 0.0), (0.016, 0.0), (0.016, 0.1), (0.0, 0.1)], 8)
            b.col("metal", "end_wall", V(side * end_gate, direction * wagon_body, floor), V(side * wagon_half, direction * (wagon_body - 0.06), top))
    prototypes = rk.stone_prototypes(rng, 10)
    heap = V(0.68, 1.42, floor)
    kit.lump(load, "soot", heap, (0.5, 0.55, 0.2), rng, 0.3, 2, floor)
    for index in range(54):
        angle = rng.uniform(0.0, tau)
        distance = 0.6 * math.sqrt(rng.random())
        x = min(heap.x + math.cos(angle) * distance, 1.12)
        y = min(heap.y + math.sin(angle) * distance, 1.9)
        z = floor + 0.2 * max(0.0, 1.0 - (distance / 0.6) ** 2) ** 0.5 + rng.uniform(-0.01, 0.03)
        rk.stone(load, prototypes, rng, V(x, y, z), rng.uniform(0.04, 0.085), "soot", 1.0)
    for index in range(70):
        spread = rng.uniform(0.0, 1.0) ** 2
        x = max(-1.12, min(heap.x + rng.uniform(-1.0, 0.5) * (0.5 + 1.4 * spread), 1.12))
        y = max(-1.9, min(heap.y + rng.uniform(-1.0, 0.5) * (0.5 + 2.8 * spread), 1.9))
        rk.stone(load, prototypes, rng, V(x, y, floor + 0.012), rng.uniform(0.015, 0.04), "soot", 1.0)
    rk.crate(load, rng, V(-0.78, -1.48, floor), (0.7, 0.5, 0.45), 0.1)
    rk.crate(load, rng, V(-0.84, -0.9, floor), (0.5, 0.42, 0.34), -0.25)
    rk.drum(load, V(0.84, -1.58, floor), 0.28, 0.86)
    emit(load, kit.geo_tube([V(-1.1, 1.9, floor + 0.02), V(-1.17, 1.96, floor + 1.12)], kit.circle(0.017, 8), True), "timber_beam", None, "given", True)
    local_block(load, "rust_iron", Matrix.Translation(V(-1.1, 1.9, floor + 0.02)) @ Matrix.Rotation(-0.06, 4, 'X'), -0.11, 0.11, -0.004, 0.004, -0.0, 0.3)
    b.loot("box", V(-0.78, -1.48, floor + 0.47))
    b.loot("toolbox", V(-0.15, -1.75, floor))
    b.col("metal", "deck", V(-wagon_half, -wagon_body, 0.45), V(wagon_half, wagon_body, floor))
    b.col("metal", "side_wall", V(wagon_half - 0.06, -wagon_body, floor), V(wagon_half, wagon_body, top))
    b.col("metal", "side_wall", V(-wagon_half, -wagon_body, floor), V(-wagon_half + 0.06, -side_gate, top))
    b.col("metal", "side_wall", V(-wagon_half, side_gate, floor), V(-wagon_half + 0.06, wagon_body, top))
    b.col("wood", "crates", V(-1.16, -1.76, floor), V(-0.4, -0.66, floor + 0.46))
    b.col("metal", "drum", V(0.56, -1.86, floor), V(1.12, -1.3, floor + 0.86))
    b.col("concrete", "coal", V(0.2, 0.9, floor), V(1.16, 1.94, floor + 0.2))
    return b


def wagon_open_far():
    b = rk.Build("train_wagon_open_far", 52)
    part = b.part("body", 40.0)
    wagon_far_base(part)
    floor = deck_top
    top = floor + open_wall
    block(part, "rust_iron", V(-wagon_half, -wagon_body, underframe_top), V(wagon_half, wagon_body, floor), 0.0, "box", None, ("bottom",))
    for sign in (-1.0, 1.0):
        side = kit.plane(V(sign * wagon_half, 0.0, 0.0), V(sign, 0.0, 0.0))
        outline = kit.rect(-wagon_body, wagon_body, underframe_top, top)
        if sign < 0.0:
            outline = [(-wagon_body, underframe_top), (wagon_body, underframe_top), (wagon_body, top), (side_gate, top), (side_gate, floor), (-side_gate, floor), (-side_gate, top), (-wagon_body, top)]
            block(part, "rust_iron", V(-wagon_half - 0.05, -side_gate, 0.1), V(-wagon_half - 0.025, side_gate, floor), 0.0, "box", None, ("top", "bottom"))
        rk.zoned(part, slab_of(side, outline, [], -0.03, 0.0), "wagon_grey", underframe_top, None, False, 0.11)
    for direction in (-1.0, 1.0):
        end = kit.plane(V(0.0, direction * wagon_body, 0.0), V(0.0, direction, 0.0))
        outline = [(-wagon_half, underframe_top), (wagon_half, underframe_top), (wagon_half, top), (end_gate, top), (end_gate, floor), (-end_gate, floor), (-end_gate, top), (-wagon_half, top)]
        rk.zoned(part, slab_of(end, outline, [], -0.03, 0.0), "wagon_grey", underframe_top, None, False, 0.71)
    return b


van_eaves = 3.34
van_rise = 0.27
van_top = 3.28


def van_arc(x):
    return van_eaves - 0.02 + van_rise * (1.0 - (x / (wagon_half + 0.06)) ** 2)


def arc_band(x0, x1, curve, lift, depth, steps=16):
    upper = [(x0 + (x1 - x0) * s / steps, curve(x0 + (x1 - x0) * s / steps) + lift) for s in range(steps + 1)]
    return upper + [(x, z - depth) for x, z in reversed(upper)]


def wagon_box():
    b = rk.Build("train_wagon_box", 61)
    rng = b.rng
    frame, detail = wagon_underframe(b, rng, True, -1.0, "wagon_a")
    body = b.part("body", 40.0, 50)
    inside = b.part("inside", 40.0, 50)
    load = b.part("load", 40.0)
    floor = deck_top
    paint = "painted_wood_bauxite"
    iron = "loco_black"
    kit.floor_boards(inside, "floorboards", -wagon_half + 0.05, wagon_half - 0.05, -wagon_body + 0.05, wagon_body - 0.05, floor, "x", rng, 0.07, 0.004, None, (0.15, 0.2), 0.02)
    post = 0.07
    for sign in (-1.0, 1.0):
        side = kit.plane(V(sign * wagon_half, 0.0, 0.0), V(sign, 0.0, 0.0))
        normal = V(sign, 0.0, 0.0)
        rk.plank_wall(body, paint, side, -wagon_body + post, wagon_body - post, underframe_top + post, van_eaves - 0.06, 0.0, 0.03, 0.15, [(-side_gate - post, side_gate + post, underframe_top, van_eaves)])
        rk.plank_wall(inside, "timber_planks_weathered", side, -wagon_body + 0.05, wagon_body - 0.05, floor, van_eaves - 0.02, 0.03, 0.048, 0.18, [(-side_gate, side_gate, floor, van_eaves)], 0.004, False)
        for a0, a1 in ((-wagon_body, -wagon_body + post), (wagon_body - post, wagon_body), (-side_gate - post, -side_gate), (side_gate, side_gate + post)):
            kit.frame_block(body, iron, side, a0, a1, underframe_top, van_eaves + 0.012, -0.014, 0.048)
            rk.rivets(detail, iron, kit.frame_point(side, (a0 + a1) * 0.5, underframe_top + 0.12, 0.014), kit.frame_point(side, (a0 + a1) * 0.5, van_eaves - 0.12, 0.014), 0.2, normal, 0.01)
        for a0, a1 in ((-wagon_body + post, -side_gate - post), (side_gate + post, wagon_body - post)):
            kit.frame_block(body, iron, side, a0, a1, underframe_top, underframe_top + post, -0.014, 0.03)
            low = kit.frame_point(side, a0 + 0.04 if a0 > 0 else a1 - 0.04, underframe_top + 0.1, 0.006)
            high = kit.frame_point(side, a1 - 0.04 if a0 > 0 else a0 + 0.04, van_eaves - 0.1, 0.006)
            rk.bar(body, iron, [low, high], 0.06, 0.012, normal)
            rk.rivets(detail, iron, low + normal * 0.006, high + normal * 0.006, 0.22, normal, 0.01, False)
        kit.frame_block(body, iron, side, -wagon_body + post, wagon_body - post, van_eaves - 0.06, van_eaves + 0.012, -0.014, 0.048)
        kit.frame_block(inside, iron, side, -side_gate, side_gate, underframe_top, floor + 0.004, -0.014, 0.048)
        l0 = side_gate + 0.03
        l1 = l0 + 2.0 * side_gate + 0.06
        z0 = floor - 0.04
        z1 = van_top - 0.03
        rk.plank_wall(body, paint, side, l0 + 0.06, l1 - 0.06, z0 + 0.06, z1 - 0.06, -0.05, -0.028, 0.14)
        for a0, a1, b0, b1 in ((l0, l0 + 0.06, z0, z1), (l1 - 0.06, l1, z0, z1), (l0 + 0.06, l1 - 0.06, z0, z0 + 0.06), (l0 + 0.06, l1 - 0.06, z1 - 0.06, z1), (l0 + 0.06, l1 - 0.06, (z0 + z1) * 0.5 - 0.03, (z0 + z1) * 0.5 + 0.03)):
            kit.frame_block(body, iron, side, a0, a1, b0, b1, -0.062, -0.024)
        for b0, b1 in ((z0 + 0.06, (z0 + z1) * 0.5 - 0.03), ((z0 + z1) * 0.5 + 0.03, z1 - 0.06)):
            rk.bar(body, iron, [kit.frame_point(side, l0 + 0.08, b0 + 0.02, 0.055), kit.frame_point(side, l1 - 0.08, b1 - 0.02, 0.055)], 0.05, 0.012, normal)
        kit.frame_block(body, "rust_iron", side, -side_gate - 0.1, l1 + 0.06, z1 + 0.005, z1 + 0.04, -0.085, -0.014)
        kit.frame_block(body, "rust_iron", side, -side_gate - 0.1, l1 + 0.06, underframe_top - 0.005, underframe_top + 0.025, -0.08, -0.014)
        for a in (l0 + 0.2, l1 - 0.2):
            kit.frame_block(detail, "rust_iron", side, a - 0.04, a + 0.04, z1 - 0.04, z1 + 0.06, -0.095, -0.062)
            rk.lathe(detail, "rust_iron", kit.frame_point(side, a, z1 + 0.045, 0.095), normal, [(0.0, 0.0), (0.035, 0.0), (0.035, 0.012), (0.0, 0.012)], 12)
        rk.pipe(detail, "rust_iron", [kit.frame_point(side, l0 + 0.13, floor + 0.85, 0.064), kit.frame_point(side, l0 + 0.13, floor + 0.85, 0.11), kit.frame_point(side, l0 + 0.13, floor + 1.2, 0.11), kit.frame_point(side, l0 + 0.13, floor + 1.2, 0.064)], 0.011, 6, 0.03)
        for a in (-side_gate - 0.12, l1 + 0.03):
            kit.frame_block(detail, "rust_iron", side, a - 0.025, a + 0.025, z1 - 0.02, z1 + 0.06, -0.1, -0.014)
        for ya, yb in ((-wagon_body, -side_gate), (side_gate, wagon_body)):
            b.col("wood", "side_wall", V(sign * wagon_half, ya, floor), V(sign * (wagon_half - 0.06), yb, van_eaves))
    for direction in (-1.0, 1.0):
        end = kit.plane(V(0.0, direction * wagon_body, 0.0), V(0.0, direction, 0.0))
        normal = V(0.0, direction, 0.0)
        crest = van_eaves + van_rise
        rk.plank_wall(body, paint, end, -wagon_half + post, wagon_half - post, underframe_top + post, crest, 0.0, 0.03, 0.15, [(-end_gate - post, end_gate + post, underframe_top, van_top + post)], 0.004, True, lambda a: van_arc(a) - 0.03)
        rk.plank_wall(inside, "timber_planks_weathered", end, -wagon_half + 0.05, wagon_half - 0.05, floor, crest, 0.03, 0.048, 0.18, [(-end_gate, end_gate, floor, van_top)], 0.004, True, lambda a: van_arc(a) - 0.04)
        for a0, a1 in ((-wagon_half, -wagon_half + post), (wagon_half - post, wagon_half)):
            kit.frame_block(body, iron, end, a0, a1, underframe_top, van_eaves + 0.03, -0.014, 0.048)
        for a0, a1 in ((-end_gate - post, -end_gate), (end_gate, end_gate + post)):
            kit.frame_block(body, iron, end, a0, a1, underframe_top, van_top + post, -0.014, 0.048)
            rk.rivets(detail, iron, kit.frame_point(end, (a0 + a1) * 0.5, underframe_top + 0.12, 0.014), kit.frame_point(end, (a0 + a1) * 0.5, van_top - 0.05, 0.014), 0.2, normal, 0.01)
        kit.frame_block(body, iron, end, -end_gate, end_gate, van_top, van_top + post, -0.014, 0.048)
        for a0, a1 in ((-wagon_half + post, -end_gate - post), (end_gate + post, wagon_half - post)):
            kit.frame_block(body, iron, end, a0, a1, underframe_top, underframe_top + post, -0.014, 0.03)
        ya, yb = sorted((direction * (wagon_body - 0.03), direction * (wagon_body + 0.014)))
        emit(body, rk.geo_prism(arc_band(-wagon_half, wagon_half, van_arc, 0.0, 0.07), ya, yb, 1), iron, None, "given", False)
        for side in (-1.0, 1.0):
            hinge = V(side * (end_gate + 0.035), direction * (wagon_body + 0.034), 0.0)
            leaf = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(direction * (7.0 if side > 0 else 173.0)), 4, 'Z')
            width = end_gate - 0.012
            for index in range(3):
                local_block(body, paint, leaf, width * index / 3.0 + 0.002, width * (index + 1) / 3.0 - 0.002, -0.014, 0.014, floor + 0.03, van_top - 0.02, 0.0, "board")
            for z in (floor + 0.3, floor + 1.05, van_top - 0.3):
                local_block(detail, iron, leaf, 0.0, width, -0.022, 0.022, z - 0.03, z + 0.03)
                rk.lathe(detail, iron, V(hinge.x, hinge.y, z - 0.05), Z, [(0.0, 0.0), (0.016, 0.0), (0.016, 0.1), (0.0, 0.1)], 8)
            stands = [(V(side * 1.17, direction * (wagon_body + 0.07), z), V(0.0, direction * 0.056, 0.0)) for z in (1.74, 2.66)]
            rk.handrail(detail, iron, [V(side * 1.17, direction * (wagon_body + 0.07), 1.7), V(side * 1.17, direction * (wagon_body + 0.07), 2.7)], 0.013, stands)
            b.col("wood", "end_wall", V(side * end_gate, direction * wagon_body, floor), V(side * wagon_half, direction * (wagon_body - 0.06), van_eaves))
    roof_half = wagon_half + 0.06
    emit(body, rk.geo_prism(arc_band(-roof_half, roof_half, van_arc, 0.04, 0.04, 20), -wagon_body - 0.1, wagon_body + 0.1, 3), iron, None, "given", True)
    for y in (-1.35, -0.675, 0.0, 0.675, 1.35):
        emit(inside, rk.geo_prism(arc_band(-wagon_half + 0.05, wagon_half - 0.05, van_arc, 0.0, 0.05, 14), y - 0.025, y + 0.025, 1), "timber_beam", None, "given", False)
    for y in (-0.95, 0.95):
        rk.lathe(detail, iron, V(0.0, y, van_arc(0.0) + 0.04), Z, [(0.05, 0.0), (0.05, 0.06), (0.11, 0.08), (0.11, 0.1), (0.0, 0.13)], 16)
    for side in (-1.0, 1.0):
        x = side * (roof_half - 0.14)
        rk.bar(detail, iron, [V(x, -1.0, van_arc(x) + 0.046), V(x, 1.0, van_arc(x) + 0.046)], 0.02, 0.012, Z)
    rk.crate(load, rng, V(-0.86, 1.5, floor), (0.62, 0.78, 0.5), 0.04)
    rk.crate(load, rng, V(-0.88, 1.56, floor + 0.535), (0.45, 0.5, 0.34), -0.2)
    rk.crate(load, rng, V(0.85, -1.48, floor), (0.62, 0.62, 0.56), -0.06)
    rk.drum(load, V(0.88, -0.98, floor), 0.26, 0.8, "timber_beam", 18)
    for z in (0.1, 0.4, 0.7):
        emit(load, kit.geo_lathe([(0.262, z - 0.02), (0.27, z - 0.02), (0.27, z + 0.02), (0.262, z + 0.02)], 18), "rust_iron", Matrix.Translation(V(0.88, -0.98, floor)), "given", True)
    for index, (x, y, z, yaw) in enumerate(((0.8, 1.62, 0.13, 0.2), (0.86, 1.2, 0.13, 1.4), (0.82, 1.42, 0.37, 0.7), (-0.86, -1.5, 0.13, 0.4), (-0.84, -1.12, 0.12, 1.2))):
        kit.lump(load, "fabric_worn", V(x, y, floor + z), (0.36, 0.22, 0.14), rng, 0.16, 2, floor, yaw)
    b.loot("box", V(-0.86, 1.5, floor + 0.9))
    b.loot("food", V(0.82, 1.42, floor + 0.52))
    b.loot("toolbox", V(0.25, -1.8, floor))
    b.col("wood", "deck", V(-wagon_half, -wagon_body, 0.45), V(wagon_half, wagon_body, floor))
    b.col("wood", "roof", V(-roof_half, -wagon_body - 0.1, van_eaves), V(roof_half, wagon_body + 0.1, van_eaves + van_rise + 0.05))
    b.col("wood", "crates", V(-1.18, 1.1, floor), V(-0.54, 1.9, floor + 0.88))
    b.col("wood", "cargo", V(0.54, -1.8, floor), V(1.17, -0.7, floor + 0.62))
    b.col("fabric", "sacks", V(0.44, 0.95, floor), V(1.17, 1.85, floor + 0.34))
    b.col("fabric", "sacks", V(-1.17, -1.75, floor), V(-0.5, -0.85, floor + 0.26))
    return b


def wagon_box_far():
    b = rk.Build("train_wagon_box_far", 62)
    part = b.part("body", 40.0)
    wagon_far_base(part)
    for sign in (-1.0, 1.0):
        side = kit.plane(V(sign * wagon_half, 0.0, 0.0), V(sign, 0.0, 0.0))
        emit(part, slab_of(side, kit.rect(-wagon_body, wagon_body, underframe_top, van_eaves), [kit.rect(-side_gate, side_gate, deck_top, van_top)], -0.03, 0.0), "painted_wood_bauxite", None, "box", False)
        kit.frame_block(part, "painted_wood_bauxite", side, side_gate + 0.03, 3.0 * side_gate + 0.09, deck_top - 0.04, van_top - 0.03, -0.06, -0.025)
    for direction in (-1.0, 1.0):
        end = kit.plane(V(0.0, direction * wagon_body, 0.0), V(0.0, direction, 0.0))
        outline = [(-wagon_half, underframe_top), (-end_gate, underframe_top), (-end_gate, van_top), (end_gate, van_top), (end_gate, underframe_top), (wagon_half, underframe_top)] + [(wagon_half - 2.0 * wagon_half * s / 4.0, van_arc(wagon_half - 2.0 * wagon_half * s / 4.0)) for s in range(5)]
        emit(part, slab_of(end, outline, [], -0.03, 0.0), "painted_wood_bauxite", None, "box", False)
    block(part, "floorboards", V(-wagon_half, -wagon_body, underframe_top), V(wagon_half, wagon_body, deck_top), 0.0, "box", None, ("bottom",))
    roof_half = wagon_half + 0.06
    emit(part, rk.geo_prism(arc_band(-roof_half, roof_half, van_arc, 0.04, 0.04, 4), -wagon_body - 0.1, wagon_body + 0.1, 1), "loco_black", None, "given", True)
    return b


coach_head = 5.5
coach_body = 4.53
coach_half = 1.3
coach_axles = (4.0, 2.0, -2.0, -4.0)
coach_bogies = (3.0, -3.0)
coach_eaves = 3.33
coach_rise = 0.29
coach_waist = 2.2
coach_door = 3.3
coach_bays = (-3.616, -1.808, 0.0, 1.808, 3.616)
coach_units = (-2.712, -0.904, 0.904, 2.712)
coach_window = (0.65, 2.24, 3.1)


def coach_arc(x):
    return coach_eaves - 0.02 + coach_rise * (1.0 - (x / (coach_half + 0.06)) ** 2)


def livery(part, geo, u_axis, shift=0.0):
    rk.planar(part, geo, "coach_livery", V(0.0, 0.0, 1.023), u_axis, Z, None, False, 0.8496, (shift, 0.0))


def bogie(b, frame, detail, rng, center):
    outline = [(-1.3, 0.8), (1.3, 0.8), (1.3, 0.6), (1.2, 0.4), (1.09, 0.4), (1.09, 0.64), (0.91, 0.64), (0.91, 0.4), (0.8, 0.4), (0.62, 0.56), (-0.62, 0.56), (-0.8, 0.4), (-0.91, 0.4), (-0.91, 0.64), (-1.09, 0.64), (-1.09, 0.4), (-1.2, 0.4), (-1.3, 0.6)]
    for side in (-1.0, 1.0):
        emit(frame, kit.geo_slab(V(side * 0.948, center, 0.0), Y, Z, V(side, 0.0, 0.0), outline, [], 0.0, 0.016), "loco_black", None, "box")
        rk.rivets(detail, "loco_black", V(side * 0.964, center - 1.22, 0.74), V(side * 0.964, center + 1.22, 0.74), 0.16, V(side, 0.0, 0.0), 0.011)
        for offset in (-1.0, 1.0):
            axle = center + offset
            emit(frame, kit.geo_cbox(0.16, 0.17, 0.2, 0.02), "loco_black", Matrix.Translation(V(side * 1.02, axle, wheel_radius)), "box")
            emit(frame, kit.geo_cbox(0.014, 0.13, 0.15, 0.004), "rust_iron", Matrix.Translation(V(side * 1.106, axle, wheel_radius)), "box")
            rk.lathe(frame, "loco_black", V(side * 0.895, axle, wheel_radius), V(side, 0.0, 0.0), [(0.076, 0.0), (0.076, 0.05)], 14)
            for bolt in (-0.045, 0.045):
                rk.prism_bolt(detail, "rust_iron", V(side * 1.113, axle + bolt, wheel_radius + 0.05), V(side, 0.0, 0.0), 0.022, 0.011, 6)
            ends = rk.leaf_spring(frame, "rust_iron", V(side * 1.02, axle, wheel_radius + 0.1 + 5 * 0.011 + 0.004), 0.62, 5, 0.08, 0.011, 0.05, Y)
            for end in ends:
                block(frame, "loco_black", V(side * 1.02 - 0.045, end.y - 0.025, end.z - 0.02), V(side * 1.02 + 0.045, end.y + 0.025, 0.8), 0.005)
            for guide in (-0.105, 0.105):
                block(frame, "loco_black", V(side * 0.964, axle + guide - 0.015, 0.4), V(side * 0.99, axle + guide + 0.015, 0.66))
            toward = -offset
            brake_block(detail, side * 0.755, axle + toward * (wheel_radius + 0.05), wheel_radius, -toward)
        block(frame, "loco_black", V(side * 0.964, center - 0.3, 0.56), V(side * 1.06, center + 0.3, 0.62))
        for spring in (-0.17, 0.17):
            rk.lathe(frame, "rust_iron", V(side * 1.01, center + spring, 0.62), Z, [(0.0, 0.0), (0.06, 0.0), (0.06, 0.02), (0.05, 0.03), (0.06, 0.04), (0.05, 0.05), (0.06, 0.06), (0.05, 0.07), (0.06, 0.08), (0.05, 0.09), (0.06, 0.1), (0.05, 0.11), (0.06, 0.12), (0.06, 0.14), (0.0, 0.14)], 12)
        block(frame, "loco_black", V(side * 0.93, center - 0.3, 0.76), V(side * 1.08, center + 0.3, 0.84), 0.01)
    block(frame, "loco_black", V(-1.0, center - 0.14, 0.78), V(1.0, center + 0.14, 0.94), 0.01)
    rk.lathe(frame, "loco_black", V(0.0, center, 0.94), Z, [(0.0, 0.0), (0.2, 0.0), (0.2, 0.04), (0.0, 0.04)], 16)
    for offset in (-1.27, 1.27):
        block(frame, "loco_black", V(-0.948, center + offset - 0.03, 0.62), V(0.948, center + offset + 0.03, 0.78))
    for offset in (-0.45, 0.45):
        rk.pipe(detail, "rust_iron", [V(-0.76, center + offset, wheel_radius + 0.02), V(0.76, center + offset, wheel_radius + 0.02)], 0.02, 8)


def coach_underframe(b, rng):
    frame = b.part("frame", 40.0, 50)
    detail = b.part("detail", 40.0)
    inner = coach_head - 0.09
    for side in (-1.0, 1.0):
        outline = [(side * 1.05, 0.93), (side * 1.15, 0.93), (side * 1.15, 0.945), (side * 1.065, 0.945), (side * 1.065, 1.185), (side * 1.15, 1.185), (side * 1.15, 1.2), (side * 1.05, 1.2)]
        emit(frame, rk.geo_prism(outline, -coach_body, coach_body, 1), "loco_black", None, "given", False)
        rk.rivets(detail, "loco_black", V(side * 1.065, -4.4, 1.12), V(side * 1.065, 4.4, 1.12), 0.25, V(side, 0.0, 0.0), 0.011)
        block(frame, "loco_black", V(side * 0.3 - 0.05, -inner, 0.95), V(side * 0.3 + 0.05, inner, 1.2))
        block(frame, "loco_black", V(side * (neck - 0.07), -inner, 0.98), V(side * (neck - 0.012), inner, 1.2))
        for y in (-0.7, 0.7):
            block(frame, "loco_black", V(side * 0.8 - 0.03, y - 0.03, 0.6), V(side * 0.8 + 0.03, y + 0.03, 0.98))
        rk.pipe(frame, "loco_black", [V(side * 0.8, -1.75, 0.96), V(side * 0.8, -0.7, 0.6), V(side * 0.8, 0.7, 0.6), V(side * 0.8, 1.75, 0.96)], 0.018, 8, 0.05)
        rk.lathe(detail, "rust_iron", V(side * 0.8, -0.1, 0.6), Y, [(0.0, 0.0), (0.03, 0.0), (0.03, 0.2), (0.0, 0.2)], 8)
        rk.atlas_panel(detail, "wagon_a", V(side * 1.067, -0.9 * side, 1.06), V(side, 0.0, 0.0), Z, 0.26, 0.105)
    for index in range(7):
        y = -4.2 + index * 1.4
        block(frame, "loco_black", V(-1.05, y - 0.04, 1.0), V(1.05, y + 0.04, 1.2))
    block(frame, "loco_black", V(0.62, -0.5, 0.58), V(1.12, 0.5, 0.92), 0.012)
    for y in (-0.25, 0.25):
        block(detail, "rust_iron", V(1.12, y - 0.015, 0.6), V(1.127, y + 0.015, 0.9))
        block(frame, "loco_black", V(0.85, y - 0.02, 0.92), V(0.89, y + 0.02, 1.0))
    rk.lathe(frame, "loco_black", V(-0.85, 0.3, 0.56), Z, [(0.0, 0.0), (0.2, 0.0), (0.22, 0.03), (0.22, 0.34), (0.2, 0.37), (0.0, 0.37)], 18)
    tank = Matrix.Translation(V(-0.86, -0.75, 0.78)) @ Matrix.Rotation(-math.pi * 0.5, 4, 'X')
    emit(frame, kit.geo_lathe([(0.0, 0.0), (0.1, 0.0), (0.15, 0.04), (0.15, 0.66), (0.1, 0.7), (0.0, 0.7)], 18), "loco_black", tank, "given", True)
    for direction in (-1.0, 1.0):
        y = direction * coach_head
        block(frame, "loco_black", V(-1.22, direction * inner, 0.9), V(1.22, y, underframe_top))
        for x in (-1.12, -0.6, 0.6, 1.12):
            rk.rivets(detail, "rust_iron", V(x, y, 0.95), V(x, y, 1.15), 0.1, V(0.0, direction, 0.0), 0.012)
        end_gear(b, detail, y, direction, rng, "loco_black", 1.18, 0.3, 3, True)
        fall_plate(frame, detail, y, direction, deck_top)
        kit.floor_boards(frame, "floorboards", -neck, neck, min(direction * coach_body, y), max(direction * coach_body, y), deck_top, "x", rng, 0.07, 0.004, None, (0.14, 0.19), 0.02)
        b.col("metal", "end", V(-1.06, direction * inner, 0.86), V(1.06, y + direction * buffer_length, deck_top))
        b.col("wood", "neck", V(-neck, direction * coach_body, 0.45), V(neck, direction * inner, deck_top))
        for side in (-1.0, 1.0):
            ya, yb = sorted((direction * coach_body, direction * inner))
            stairwell(b, frame, detail, side, ya, yb, deck_top, coach_half, wagon_tops)
            lamp_iron(detail, V(side * 1.05, y, underframe_top), V(0.0, direction, 0.0))
    for center in coach_bogies:
        bogie(b, frame, detail, rng, center)
    return frame, detail


def bench(part, detail, side, y, facing, floor, seat="leather_brown"):
    x0 = side * 0.51
    x1 = side * 1.255
    width = abs(x1 - x0)
    middle = (x0 + x1) * 0.5
    front = y + facing * 0.5
    block(part, "timber_beam", V(x0, y + facing * 0.03, floor), V(x1, front - facing * 0.04, floor + 0.36), 0.0, "box", None, ("bottom",))
    emit(part, kit.geo_cbox(width - 0.04, 0.47, 0.1, 0.03), seat, Matrix.Translation(V(middle, y + facing * 0.265, floor + 0.41)), "box", True)
    emit(part, kit.geo_cbox(width - 0.04, 0.08, 0.5, 0.03), seat, Matrix.Translation(V(middle, y + facing * 0.075, floor + 0.78)) @ Matrix.Rotation(facing * 0.1, 4, 'X'), "box", True)
    for index in range(3):
        for row in range(2):
            rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.012, 0.0), (0.009, 0.006), (0.0, 0.008)], 6), "brass", rk.frame_along(V(middle + (index - 1) * width * 0.28, y + facing * (0.118 + 0.015 * (1 - row)), floor + 0.68 + row * 0.2), V(0.0, facing, 0.12)))


def coach_seats(b, part, detail, floor):
    end_outline = [(-0.53, 0.0), (0.53, 0.0), (0.53, 0.46), (0.5, 0.52), (0.13, 0.56), (0.06, 1.08), (-0.06, 1.08), (-0.13, 0.56), (-0.5, 0.52), (-0.53, 0.46)]
    half_outline = [(0.0, 0.0), (0.53, 0.0), (0.53, 0.46), (0.5, 0.52), (0.13, 0.56), (0.06, 1.08), (0.0, 1.08)]
    for side in (-1.0, 1.0):
        for center in coach_units:
            block(part, "timber_beam", V(side * 0.51, center - 0.03, floor), V(side * 1.255, center + 0.03, floor + 1.06), 0.0, "board")
            block(part, "timber_beam", V(side * 0.49, center - 0.05, floor + 1.06), V(side * 1.255, center + 0.05, floor + 1.09), 0.004, "board")
            for facing in (-1.0, 1.0):
                bench(part, detail, side, center, facing, floor)
            emit(part, kit.geo_slab(V(side * 0.48, center, floor), Y, Z, V(side, 0.0, 0.0), end_outline, [], 0.0, 0.03), "timber_beam", None, "box")
            rk.pipe(detail, "loco_black", [V(side * 0.495, center, floor + 1.08), V(side * 0.495, center, floor + 1.2)], 0.012, 8)
            rk.swatch(detail, kit.geo_lathe([(0.0, -0.022), (0.018, -0.014), (0.022, 0.0), (0.018, 0.014), (0.0, 0.022)], 8), "brass", Matrix.Translation(V(side * 0.495, center, floor + 1.21)))
            b.col("fabric", "seat", V(side * 0.5, center - 0.53, floor), V(side * 1.26, center + 0.53, floor + 1.06))
        for direction in (-1.0, 1.0):
            wall = direction * (coach_body - 0.04)
            bench(part, detail, side, wall, -direction, floor)
            outline = half_outline if direction < 0 else [(-y, z) for y, z in reversed(half_outline)]
            emit(part, kit.geo_slab(V(side * 0.48, wall, floor), Y, Z, V(side, 0.0, 0.0), outline, [], 0.0, 0.03), "timber_beam", None, "box")
        for bay in coach_bays[1:4]:
            block(part, "timber_beam", V(side * 0.84, bay - 0.19, floor + 0.7), V(side * 1.255, bay + 0.19, floor + 0.73), 0.006, "board")
            rk.bar(detail, "loco_black", [V(side * 0.9, bay, floor + 0.7), V(side * 1.24, bay, floor + 0.42)], 0.03, 0.012, Y)


def suitcase(part, detail, center, length, width, height, yaw):
    matrix = Matrix.Translation(center + V(0.0, 0.0, height * 0.5)) @ Matrix.Rotation(yaw, 4, 'Z')
    emit(part, kit.geo_cbox(width, length, height, 0.02), "leather_brown", matrix, "box", True)
    for strap in (-0.3, 0.3):
        local_block(detail, "loco_black", matrix, -width * 0.5 - 0.004, width * 0.5 + 0.004, strap * length - 0.012, strap * length + 0.012, -height * 0.5 - 0.004, height * 0.5 + 0.004)
    rk.pipe(detail, "loco_black", [matrix @ V(width * 0.5, -0.06, 0.0), matrix @ V(width * 0.5 + 0.03, -0.04, 0.0), matrix @ V(width * 0.5 + 0.03, 0.04, 0.0), matrix @ V(width * 0.5, 0.06, 0.0)], 0.006, 6, 0.015)


def coach_racks(part, detail, floor, rng, b):
    for side in (-1.0, 1.0):
        for y in (-4.4, -2.712, -0.904, 0.904, 2.712, 4.4):
            rk.bar(detail, "loco_black", [V(side * 1.255, y, 3.14), V(side * 0.95, y, 3.16), V(side * 0.93, y, 3.21)], 0.025, 0.01, Y, 0.03)
            rk.bar(detail, "loco_black", [V(side * 1.255, y, 3.02), V(side * 1.02, y, 3.15)], 0.02, 0.008, Y)
        for offset in (0.95, 1.05, 1.15, 1.24):
            rk.swatch(detail, kit.geo_tube([V(side * offset, -4.4, 3.175 - (1.24 - offset) * 0.05), V(side * offset, 4.4, 3.175 - (1.24 - offset) * 0.05)], kit.circle(0.008, 6), True, Z), "brass", None, True)
    for x, y, length, width, height, yaw in ((-1.08, -2.9, 0.5, 0.3, 0.16, 0.1), (1.08, 1.2, 0.46, 0.28, 0.17, -0.15), (-1.08, 2.4, 0.4, 0.26, 0.15, 0.3)):
        suitcase(part, detail, V(x, y, 3.185), length, width, height, yaw)
    suitcase(part, detail, V(-0.9, -3.616, floor), 0.62, 0.4, 0.2, 0.2)
    suitcase(part, detail, V(0.9, 0.2, floor + 0.73), 0.3, 0.22, 0.1, 0.5)
    b.loot("box", V(-0.9, -3.616, floor + 0.2))
    b.loot("food", V(0.95, -0.2, floor + 0.73))
    b.loot("medical", V(0.9, 3.5, floor))


def coach():
    b = rk.Build("train_coach", 71)
    rng = b.rng
    frame, detail = coach_underframe(b, rng)
    body = b.part("body", 40.0, 50)
    inside = b.part("inside", 40.0, 50)
    glass = b.part("glass", 30.0)
    floor = deck_top
    half = coach_half
    skin = 0.02
    wall = 0.05
    width, sill, head = coach_window
    states = ("missing", "shard", "whole", "missing", "missing", "shard", "whole", "missing", "shard")
    lights_above = ("whole", "whole", "shard", "whole", "missing")
    kit.floor_boards(inside, "floorboards", -half + wall, half - wall, -coach_body + wall, coach_body - wall, floor, "y", rng, 0.07, 0.004, None, (0.14, 0.19), 0.02, [-2.2, 0.0, 2.2])
    number = 0
    for sign in (-1.0, 1.0):
        side = kit.plane(V(sign * half, 0.0, 0.0), V(sign, 0.0, 0.0))
        normal = V(sign, 0.0, 0.0)
        holes = [kit.rect(bay - width, bay + width, sill, head) for bay in coach_bays]
        livery(body, slab_of(side, kit.rect(-coach_body, coach_body, underframe_top, coach_eaves), holes, -skin, 0.0), Y, 0.13 if sign > 0 else 0.57)
        emit(inside, slab_of(side, kit.rect(-coach_body + skin, coach_body - skin, floor, coach_waist), [], -wall, -skin, False), "timber_beam", None, "world", False)
        livery(inside, slab_of(side, kit.rect(-coach_body + skin, coach_body - skin, coach_waist, coach_eaves - 0.01), holes, -wall, -skin, True), Y, 0.31 if sign > 0 else 0.77)
        matrix = kit.frame_matrix(side)
        for bay in coach_bays:
            kit.frame_block(detail, "timber_beam", side, bay - width, bay + width, 2.86, 2.89, -0.004, wall)
            kit.frame_block(detail, "timber_beam", side, bay - 0.016, bay + 0.016, sill, 2.86, -0.004, wall)
            for a0, a1 in ((bay - width, bay - 0.016), (bay + 0.016, bay + width)):
                kit.pane(glass, matrix, a0, a1, sill, 2.86, skin * 0.6, states[number % len(states)], rng)
                kit.pane(glass, matrix, a0, a1, 2.89, head, skin * 0.6, lights_above[number % len(lights_above)], rng)
                number += 1
            kit.frame_block(detail, "timber_beam", side, bay - 0.012, bay + 0.012, 2.89, head, -0.004, wall)
            window_trim(detail, matrix, bay - width, bay + width, sill, head, "timber_beam", 0.03)
            kit.frame_block(inside, "timber_beam", side, bay - width - 0.04, bay + width + 0.04, sill - 0.035, sill, wall, wall + 0.05, 0.004)
        for z, depth in ((coach_waist, 0.035), (underframe_top + 0.06, 0.03), (coach_eaves - 0.09, 0.03)):
            kit.frame_block(detail, "loco_black", side, -coach_body, coach_body, z - depth * 0.5, z + depth * 0.5, -0.012, 0.0)
        for a in (-coach_body + 0.03, coach_body - 0.03):
            kit.frame_block(detail, "loco_black", side, a - 0.03, a + 0.03, underframe_top, coach_eaves, -0.012, 0.0)
        for center in coach_units:
            kit.frame_block(detail, "loco_black", side, center - 0.012, center + 0.012, underframe_top + 0.075, coach_waist - 0.018, -0.01, 0.0)
        kit.frame_block(inside, "timber_beam", side, -coach_body + skin, coach_body - skin, coach_waist - 0.03, coach_waist + 0.03, wall, wall + 0.015)
        b.col("metal", "side_wall", V(sign * half, -coach_body, floor), V(sign * (half - 0.06), coach_body, coach_eaves))
    arc = [(half - 2.0 * half * s / 16.0, coach_arc(half - 2.0 * half * s / 16.0)) for s in range(17)]
    inner_arc = [(max(min(x, half - skin), -half + skin), z - 0.02) for x, z in arc]
    lights = [(0.62, 1.1, sill, head, "whole"), (-1.1, -0.62, sill, head, "shard")]
    for direction in (-1.0, 1.0):
        end = kit.plane(V(0.0, direction * coach_body, 0.0), V(0.0, direction, 0.0))
        flip = end[1].x
        normal = V(0.0, direction, 0.0)
        holes = [kit.rect(min(flip * w[0], flip * w[1]), max(flip * w[0], flip * w[1]), w[2], w[3]) for w in lights]
        outline = [(-half, underframe_top), (-end_gate, underframe_top), (-end_gate, coach_door), (end_gate, coach_door), (end_gate, underframe_top), (half, underframe_top)] + arc
        livery(body, slab_of(end, outline, holes, -skin, 0.0), X, 0.71)
        for a0, a1 in ((-half + skin, -end_gate), (end_gate, half - skin)):
            emit(inside, slab_of(end, kit.rect(a0, a1, floor, coach_waist), [], -wall, -skin, True), "timber_beam", None, "world", False)
        upper = [(-half + skin, coach_waist), (-end_gate, coach_waist), (-end_gate, coach_door), (end_gate, coach_door), (end_gate, coach_waist), (half - skin, coach_waist)] + inner_arc
        livery(inside, slab_of(end, upper, holes, -wall, -skin, True), X, 0.43)
        matrix = kit.frame_matrix(end)
        for w, hole in zip(lights, holes):
            kit.pane(glass, matrix, hole[0][0], hole[1][0], w[2], w[3], skin * 0.6, w[4], rng)
            window_trim(detail, matrix, hole[0][0], hole[1][0], w[2], w[3], "timber_beam", 0.03)
        for jamb in (-end_gate - 0.035, end_gate):
            kit.frame_block(detail, "timber_beam", end, jamb, jamb + 0.035, underframe_top, coach_door, -0.012, wall + 0.004)
        kit.frame_block(detail, "timber_beam", end, -end_gate - 0.035, end_gate + 0.035, coach_door, coach_door + 0.035, -0.012, wall + 0.004)
        for z, depth in ((coach_waist, 0.035), (underframe_top + 0.06, 0.03)):
            for a0, a1 in ((-half, -end_gate - 0.035), (end_gate + 0.035, half)):
                kit.frame_block(detail, "loco_black", end, a0, a1, z - depth * 0.5, z + depth * 0.5, -0.012, 0.0)
        leaf = Matrix.Translation(V(end_gate - 0.04, direction * (coach_body - wall - 0.02), 0.0)) @ Matrix.Rotation(math.radians(-direction * 88.5), 4, 'Z')
        span = 2.0 * end_gate - 0.03
        local_block(inside, "timber_beam", leaf, 0.0, span, -0.02, 0.02, floor + 0.02, coach_waist, 0.004)
        for px0, px1, pz0, pz1 in ((0.0, 0.08, coach_waist, coach_door - 0.02), (span - 0.08, span, coach_waist, coach_door - 0.02), (0.08, span - 0.08, coach_door - 0.1, coach_door - 0.02)):
            local_block(inside, "timber_beam", leaf, px0, px1, -0.02, 0.02, pz0, pz1, 0.004)
        kit.pane(glass, leaf, 0.08, span - 0.08, coach_waist, coach_door - 0.1, -0.002, "shard" if direction > 0 else "whole", rng)
        rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.014, 0.0), (0.014, 0.05), (0.028, 0.06), (0.028, 0.075), (0.0, 0.08)], 10), "brass", rk.frame_along(leaf @ V(span - 0.07, 0.02, floor + 1.0), leaf.to_3x3() @ V(0.0, 1.0, 0.0)))
        rk.swatch(detail, kit.geo_lathe([(0.0, 0.0), (0.014, 0.0), (0.014, 0.05), (0.028, 0.06), (0.028, 0.075), (0.0, 0.08)], 10), "brass", rk.frame_along(leaf @ V(span - 0.07, -0.02, floor + 1.0), leaf.to_3x3() @ V(0.0, -1.0, 0.0)))
        rk.atlas_panel(detail, "chain", V(0.0, direction * (coach_body - wall - 0.004), 3.45), V(0.0, -direction, 0.0), Z, 0.2, 0.2)
        rk.atlas_panel(detail, "advert", V(-direction * 0.86, direction * (coach_body - wall - 0.004), 3.25), V(0.0, -direction, 0.0), Z, 0.36, 0.2)
        for side in (-1.0, 1.0):
            stands = [(V(side * 1.2, direction * (coach_body + 0.056), z), V(0.0, direction * 0.056, 0.0)) for z in (1.64, 2.56)]
            rk.handrail(detail, "loco_black", [V(side * 1.2, direction * (coach_body + 0.056), 1.6), V(side * 1.2, direction * (coach_body + 0.056), 2.6)], 0.013, stands)
            corner = V(side * 1.2, direction * (coach_head - 0.05), underframe_top)
            rk.pipe(detail, "loco_black", [corner, V(corner.x, corner.y, coach_arc(1.2) - 0.01)], 0.024, 10)
            rk.lathe(detail, "loco_black", corner, Z, [(0.05, 0.0), (0.05, 0.015), (0.03, 0.05), (0.024, 0.06)], 10)
            gate = V(side * 0.58, direction * (coach_head - 0.05), underframe_top)
            post(detail, gate, 1.1, "loco_black", 0.02)
            for z in (1.06, 0.62, 0.2):
                rk.pipe(detail, "loco_black", [gate + Z * z, corner + Z * z], 0.014, 8)
            panel = kit.geo_box(abs(corner.x - gate.x) - 0.05, 0.008, 0.4)
            rk.planar(body, panel, "coach_livery", V(0.0, 0.0, 1.023), X, Z, Matrix.Translation(V((corner.x + gate.x) * 0.5, corner.y, underframe_top + 0.41)), False, 0.8496, (0.85, 0.0))
            for index in range(7):
                x = gate.x + (corner.x - gate.x) * (index + 0.5) / 7.0
                rk.pipe(detail, "loco_black", [V(x, corner.y, underframe_top + 0.62), V(x, corner.y, underframe_top + 1.06)], 0.008, 6)
            b.col("metal", "end_wall", V(side * end_gate, direction * coach_body, floor), V(side * half, direction * (coach_body - 0.56), coach_eaves))
        ya, yb = sorted((direction * (coach_head - 0.02), direction * (coach_head + 0.02)))
        emit(body, rk.geo_prism(arc_band(-half - 0.06, half + 0.06, coach_arc, 0.0, 0.1, 18), ya, yb, 1), "loco_black", None, "given", False)
    roof_half = half + 0.06
    emit(body, rk.geo_prism(arc_band(-roof_half, roof_half, coach_arc, 0.04, 0.04, 24), -coach_head - 0.04, coach_head + 0.04, 6), "loco_black", None, "given", True)
    inner = half - wall
    ceiling = rk.geo_sheet([(inner - 2.0 * inner * s / 14.0, coach_arc(inner - 2.0 * inner * s / 14.0) - 0.004) for s in range(15)], -coach_body + skin, coach_body - skin, 1)
    rk.planar(inside, rk.facing(ceiling, -Z), "coach_livery", V(-1.4, 0.0, 0.0), Y, X, None, True, 0.333, (0.0, 0.52))
    for index in range(7):
        y = -4.2 + index * 1.4
        emit(inside, rk.geo_prism(arc_band(-inner, inner, coach_arc, -0.004, 0.035, 14), y - 0.02, y + 0.02, 1), "timber_beam", None, "given", False)
    for y in (-3.0, 0.0, 3.0):
        lamp = V(0.0, y, coach_arc(0.0) - 0.04)
        rk.swatch(detail, kit.geo_lathe([(0.0, -0.02), (0.11, -0.02), (0.11, 0.0), (0.09, 0.012)], 16), "brass", rk.frame_along(lamp, -Z))
        rk.swatch(detail, kit.geo_lathe([(0.085, 0.0), (0.095, 0.05), (0.07, 0.1), (0.03, 0.125), (0.0, 0.13)], 16), "lens_clear", rk.frame_along(lamp, -Z), True, "lamp_glow_dim")
        rk.lathe(detail, "loco_black", V(0.0, y, coach_arc(0.0) + 0.04), Z, [(0.09, 0.0), (0.09, 0.05), (0.14, 0.07), (0.14, 0.09), (0.0, 0.13)], 16)
        b.light("warm", lamp - V(0.0, 0.0, 0.2))
    for side in (-1.0, 1.0):
        block(detail, "loco_black", V(side * roof_half - 0.015, -coach_head - 0.04, coach_eaves - 0.05), V(side * roof_half + 0.015, coach_head + 0.04, coach_eaves - 0.01))
    coach_seats(b, inside, detail, floor)
    coach_racks(inside, detail, floor, rng, b)
    b.col("wood", "deck", V(-half, -coach_body, 0.45), V(half, coach_body, floor))
    b.col("metal", "roof", V(-roof_half, -coach_head, coach_eaves), V(roof_half, coach_head, coach_eaves + coach_rise + 0.06))
    return b


def coach_far():
    b = rk.Build("train_coach_far", 72)
    part = b.part("body", 40.0)
    inner = coach_head - 0.09
    half = coach_half
    width, sill, head = coach_window
    for sign in (-1.0, 1.0):
        side = kit.plane(V(sign * half, 0.0, 0.0), V(sign, 0.0, 0.0))
        livery(part, slab_of(side, kit.rect(-coach_body, coach_body, underframe_top, coach_eaves), [], -0.02, 0.0, False), Y, 0.13)
        for bay in coach_bays:
            x = sign * (half + 0.004)
            pane = kit.Geo([V(x, bay - width, sill), V(x, bay + width, sill), V(x, bay + width, head), V(x, bay - width, head)], [(0, 1, 2, 3)])
            emit(part, rk.facing(pane, V(sign, 0.0, 0.0)), "glass_dirty", None, "box", False)
        block(part, "loco_black", V(sign * 1.05, -coach_body, 0.93), V(sign * 1.15, coach_body, underframe_top), 0.0, "box", None, ("top",))
        for y0, y1 in ((-inner, -coach_body), (coach_body, inner)):
            far_stairs(part, sign, y0, y1, wagon_tops)
        for center in coach_bogies:
            block(part, "loco_black", V(sign * 0.948, center - 1.3, 0.4), V(sign * 1.06, center + 1.3, 0.8))
    arc = [(half - 2.0 * half * s / 4.0, coach_arc(half - 2.0 * half * s / 4.0)) for s in range(5)]
    for direction in (-1.0, 1.0):
        end = kit.plane(V(0.0, direction * coach_body, 0.0), V(0.0, direction, 0.0))
        livery(part, slab_of(end, [(-half, underframe_top), (half, underframe_top)] + arc, [], -0.02, 0.0, False), X, 0.71)
        y = direction * (coach_body + 0.004)
        pane = kit.Geo([V(-end_gate, y, deck_top), V(end_gate, y, deck_top), V(end_gate, y, coach_door), V(-end_gate, y, coach_door)], [(0, 1, 2, 3)])
        emit(part, rk.facing(pane, V(0.0, direction, 0.0)), "soot", None, "box", False)
        rk.slab(part, V(-neck, direction * coach_body, 0.6), V(neck, direction * coach_head, deck_top), "floorboards", "loco_black", False)
        block(part, "loco_black", V(-1.22, direction * inner, 0.9), V(1.22, direction * coach_head, underframe_top), 0.0, "box", None, ("bottom",))
        far_buffers(part, direction * coach_head, direction)
    block(part, "loco_black", V(-1.05, -coach_body, 1.0), V(1.05, coach_body, underframe_top), 0.0, "box", None, ("top",))
    roof_half = half + 0.06
    emit(part, rk.geo_prism(arc_band(-roof_half, roof_half, coach_arc, 0.04, 0.04, 4), -coach_head - 0.04, coach_head + 0.04, 1), "loco_black", None, "given", True)
    return b


specs = {
    "train_locomotive": {"length_over_buffers": 2.0 * (loco_head + buffer_length), "wheelbase": loco_axles[0] - loco_axles[-1], "width": 2.0 * loco_half, "roof_height": round(cab_eaves + cab_rise + 0.065, 3), "deck_height": loco_deck, "axles": list(loco_axles), "horn": horn_position, "exhaust": stack_position + V(0.0, 0.0, 0.69), "headlights": lamp_positions, "tail_lamp": tail_position},
    "train_wagon_flat": {"length_over_buffers": 2.0 * (wagon_head + buffer_length), "wheelbase": wagon_axles[0] - wagon_axles[-1], "width": 2.0 * wagon_half, "roof_height": 1.71, "deck_height": deck_top, "axles": list(wagon_axles)},
    "train_wagon_open": {"length_over_buffers": 2.0 * (wagon_head + buffer_length), "wheelbase": wagon_axles[0] - wagon_axles[-1], "width": 2.0 * wagon_half, "roof_height": deck_top + open_wall, "deck_height": deck_top, "axles": list(wagon_axles)},
    "train_wagon_box": {"length_over_buffers": 2.0 * (wagon_head + buffer_length), "wheelbase": wagon_axles[0] - wagon_axles[-1], "width": 2.0 * wagon_half, "roof_height": van_eaves + van_rise + 0.02, "deck_height": deck_top, "axles": list(wagon_axles)},
    "train_coach": {"length_over_buffers": 2.0 * (coach_head + buffer_length), "wheelbase": coach_bogies[0] - coach_bogies[-1], "width": 2.0 * coach_half, "roof_height": coach_eaves + coach_rise + 0.02, "deck_height": deck_top, "axles": list(coach_axles), "bogie_centres": list(coach_bogies), "bogie_wheelbase": coach_axles[0] - coach_axles[1]},
}

models = {
    "train_wheelset": (wheelset, wheelset_far, 6000, 400),
    "train_locomotive": (locomotive, locomotive_far, 200000, 3000),
    "train_wagon_flat": (wagon_flat, wagon_flat_far, 120000, 2000),
    "train_wagon_open": (wagon_open, wagon_open_far, 120000, 2000),
    "train_wagon_box": (wagon_box, wagon_box_far, 120000, 2000),
    "train_coach": (coach, coach_far, 120000, 2000),
}


def triple(vector):
    return [round(vector.x, 3), round(vector.y, 3), round(vector.z, 3)]


def record(name, triangles, far_triangles, low, high):
    document = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    document["space"] = "model space in metres: X right, Y forward (vehicle front), Z up, origin on the rail top under the vehicle middle"
    document["gauge"] = gauge
    document["coupling_gap"] = coupling_gap
    document["buffer_height"] = buffer_height
    document["coupler_height"] = hook_height
    document["buffer_spacing"] = buffer_spread * 2.0
    document["step_treads"] = {"rise_max": 0.43, "run": step_run, "outer_edge_from_centre": step_out}
    vehicles = document.setdefault("vehicles", {})
    if name == "train_wheelset":
        document["wheelset"] = {"model": name, "far_model": name + "_far", "origin": "axle centre, axle along X", "wheel_radius": wheel_radius, "flange_radius": wheel_radius + 0.028, "back_to_back": 1.36, "triangles": triangles, "triangles_far": far_triangles}
    elif name in specs:
        spec = specs[name]
        entry = {"model": name, "far_model": name + "_far"}
        for key in ("length_over_buffers", "wheelbase", "width", "roof_height", "deck_height"):
            entry[key] = round(spec[key], 3)
        entry["width_over_steps"] = round(step_out * 2.0, 3)
        entry["buffer_height"] = buffer_height
        entry["coupler_height"] = hook_height
        entry["axles"] = [{"y": round(y, 3), "height": wheel_radius, "radius": wheel_radius} for y in spec["axles"]]
        entry["triangles"] = triangles
        entry["triangles_far"] = far_triangles
        entry["bounds_min"] = [round(value, 3) for value in low]
        entry["bounds_max"] = [round(value, 3) for value in high]
        for key in ("bogie_centres", "bogie_wheelbase"):
            if key in spec:
                entry[key] = spec[key]
        for key in ("horn", "exhaust", "tail_lamp"):
            if key in spec:
                entry[key] = triple(spec[key])
        if "headlights" in spec:
            entry["headlights"] = [triple(position) for position in spec["headlights"]]
        vehicles[name] = entry
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=1)
