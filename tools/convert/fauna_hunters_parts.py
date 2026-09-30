import math
import numpy as np
from fauna_hunters_mesh import *
from fauna_hunters_body import *
from fauna_hunters_limbs import *


def ear_ring(center, across, facing, width, cup, thick, count):
    psi = np.arange(count) * (2.0 * math.pi / count)
    sine = np.sin(psi)
    depth = np.where(sine >= 0.0, -(cup - thick) * np.abs(sine), -cup * np.abs(sine) ** 0.75)
    return center[None, :] + across[None, :] * (width * np.cos(psi))[:, None] + facing[None, :] * depth[:, None], psi


def build_ear(shell, body, spec):
    base = np.asarray(spec["base"], dtype=np.float64)
    axis = normalize(np.asarray(spec["axis"], dtype=np.float64))
    facing = np.asarray(spec["facing"], dtype=np.float64)
    facing = normalize(facing - axis * float(facing @ axis))
    across = normalize(np.cross(axis, facing))
    if across[0] < 0.0:
        across = -across
    height = spec["height"]
    half_width = spec["width"]
    di, dj = spec.get("patch", (4, 3))
    i0, j0, ci, cj = patch_at(body, base, di, dj, spec.get("first", 0), body.corner, 1, body.lip - 1)
    loop, closed = hole(body, i0, i0 + di, j0, j0 + dj)
    loop = align_loop(shell, loop, base, facing, -across)
    count = len(loop)
    levels = spec.get("levels", (0.14, 0.3, 0.48, 0.66, 0.82, 0.93))
    lean = np.asarray(spec.get("lean", (0.0, 0.0, 0.0)), dtype=np.float64)
    rings = [loop]
    for vertex in loop:
        shell.pf[vertex]["ear"] = 0.0
    boundary = np.array([shell.p[i] for i in loop])
    for level, h in enumerate(levels):
        width = half_width * (1.0 - h ** spec.get("taper", 1.7)) ** spec.get("round", 0.8) * (1.0 + spec.get("flare", 0.25) * math.exp(-((h - 0.22) / 0.2) ** 2))
        cup = spec.get("cup", 0.02) * (1.0 - h) ** 0.8 + 0.0035
        thick = spec.get("thick", 0.006) * (1.0 - 0.5 * h)
        center = base + axis * height * h + lean * h * h + facing * (-spec.get("sweep", 0.0) * h * h)
        points, psi = ear_ring(center, across, facing, width, cup, thick, count)
        if level == 0:
            points = points * 0.72 + boundary * 0.28
        ring = []
        for k in range(count):
            inner = math.sin(psi[k]) > 0.15
            ring.append(shell.add(points[k], ZONE_EAR_IN if inner else ZONE_FUR, REG_EAR, height * h, -math.sin(psi[k]), axis, 0.6, None, 0, {"ear": float(smoothstep(0.05, 0.35, h)), "earin": 1.0 if inner else 0.0}))
        shell.strip(rings[-1], ring)
        rings.append(ring)
    tip = base + axis * height + lean + facing * (-spec.get("sweep", 0.0)) - facing * 0.002
    pole = shell.add(tip, ZONE_FUR, REG_EAR, height, 0.0, axis, 0.6, None, 0, {"ear": 1.0})
    shell.fan(rings[-1], pole)
    front = count // 2
    for a, b in zip(rings[:-1], rings[1:]):
        shell.seam(a[0], b[0])
        shell.seam(a[front], b[front])
    shell.seam(rings[-1][0], pole)
    shell.seam(rings[-1][front], pole)
    shell.seam_loop(loop)
    shell.marks.setdefault("ear_l", []).extend([v for ring in rings[1:] for v in ring] + [pole])
    return rings


def cone(shell, base, direction, length, radius, zone, weights, island, count=5, bend=None, flat=1.0, region=REG_HEAD, steps=(0.0, 0.45, 0.8), lateral=(1.0, 0.0, 0.0)):
    base = np.asarray(base, dtype=np.float64)
    direction = normalize(np.asarray(direction, dtype=np.float64))
    bend = np.zeros(3) if bend is None else np.asarray(bend, dtype=np.float64)
    keys = []
    for f in steps:
        r = radius * (1.0 - f) ** 0.8 + radius * 0.06
        keys.append({"p": base + direction * length * f + bend * f * f, "df": r, "db": r, "hw": r * flat, "n": 1})
    return build_tube(shell, keys, count, zone, region, weights, island, lateral, start_cap=0.0, end_cap=length * (1.0 - steps[-1]), fur=0.0)


def build_teeth(shell, body, spec, head_bone="head", jaw_bone="jaw"):
    corner = body.corner
    last = body.count - 1
    chin = body.chin
    inset = spec.get("inset", 0.004)
    created = []
    for table, lips, end, sign, bone, row in ((spec["upper"], body.upper_lip, last, -1.0, head_bone, body.palate), (spec["lower"], body.lower_lip, chin, 1.0, jaw_bone, body.floor)):
        total = end - corner
        for entry in table:
            at = corner + entry["at"] * total
            i = int(math.floor(at))
            f = at - i
            i2 = min(i + 1, end)
            lip = shell.p[row[i][1]] * (1.0 - f) + shell.p[row[i2][1]] * f
            up = normalize(body.ups[i] * (1.0 - f) + body.ups[i2] * f)
            forward = normalize(body.tangent[i] * (1.0 - f) + body.tangent[i2] * f)
            root = lip.copy()
            root[0] = entry["x"] if "x" in entry else max(lip[0] - inset - entry.get("in", 0.0), 0.002)
            root = root - up * sign * entry.get("sink", 0.0015) + forward * entry.get("ahead", 0.0)
            direction = up * sign + forward * entry.get("rake", 0.0) + np.array([entry.get("splay", 0.0), 0.0, 0.0])
            bend = forward * entry.get("hook", 0.0)
            rings, ids = cone(shell, root, direction, entry["len"], entry["rad"], ZONE_TEETH, {bone: 1.0}, 2, entry.get("sides", 5), bend, entry.get("flat", 1.0), REG_HEAD if bone == head_bone else REG_JAW)
            for vertex in ids:
                shell.pf[vertex]["tooth"] = 1.0
            created.extend(ids)
    shell.marks.setdefault("teeth_l", []).extend(created)
    return created


def tongue_keys(shell, body, spec):
    corner = body.corner
    chin = body.chin
    keys = []
    count = chin - corner
    for step in range(count + 1):
        f = step / count
        i = corner + step
        row = body.floor[i]
        middle = shell.p[row[-1]].copy()
        lift = spec.get("lift", 0.004)
        if step == 0:
            middle = middle - body.tangent[i] * 0.004
        width = spec.get("width", 0.014) * (1.0 - 0.35 * f ** 2) * min(1.0, shell.p[row[0]][0] / max(spec.get("width", 0.014) * 1.25, 1e-6))
        keys.append({"p": middle + body.ups[i] * lift, "df": spec.get("thick", 0.004), "db": spec.get("thick", 0.004), "hw": max(width, 0.003), "nf": 2.0, "nb": 2.6, "n": 1})
    return keys[:max(2, int(round(len(keys) * spec.get("reach", 0.85))))]


def build_tongue(shell, keys, spec, jaw_bone="jaw"):
    rings, ids = build_tube(shell, keys, spec.get("sides", 8), ZONE_TONGUE, REG_JAW, {jaw_bone: 1.0}, 3, (1.0, 0.0, 0.0), start_cap=0.0, end_cap=0.006, fur=0.0)
    for vertex in ids:
        shell.pf[vertex]["jaw"] = 1.0
    shell.marks["tongue"] = ids
    return ids


def build_toes(shell, limb, spec, bone, region):
    center = limb.centers[-1]
    forward = limb.tangent[-1]
    side = limb.side[-1]
    up = limb.front[-1]
    created = []
    claws = []
    for toe in spec["toes"]:
        root = center + side * toe["x"] + forward * toe.get("back", -0.012) + up * toe.get("z", 0.0)
        length = toe["len"]
        direction = normalize(forward + side * toe.get("splay", 0.0) + up * toe.get("pitch", -0.05))
        keys = []
        for f, r, lift in ((0.0, 0.85, 0.0), (0.4, 1.0, 0.18), (0.78, 0.92, 0.1), (1.0, 0.6, -0.25)):
            radius = toe["rad"] * r
            keys.append({"p": root + direction * length * f + up * radius * lift, "df": radius * toe.get("tall", 0.95), "db": radius * 0.8, "hw": radius, "nf": 2.0, "nb": 2.6, "n": 1})
        rings, ids = build_tube(shell, keys, spec.get("sides", 7), ZONE_FUR, region, {bone: 1.0}, 0, side, start_cap=0.0, end_cap=toe["rad"] * 0.45, fur=0.4, s=limb.arc[-1], flow=direction)
        for vertex in ids:
            shell.pf[vertex]["toe"] = 1.0
        created.extend(ids)
        tip = root + direction * length * 1.0 + up * toe["rad"] * 0.12
        claw_direction = normalize(direction + up * -0.45)
        rings, ids = cone(shell, tip - direction * toe["rad"] * 0.35, claw_direction, spec.get("claw", 0.016), toe["rad"] * 0.42, ZONE_CLAW, {bone: 1.0}, 4, 5, up * -0.006, 0.8, region, lateral=side)
        for vertex in ids:
            shell.pf[vertex]["claw"] = 1.0
        claws.extend(ids)
    return created, claws
