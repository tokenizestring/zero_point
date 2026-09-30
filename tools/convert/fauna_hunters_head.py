import math
import numpy as np
from fauna_hunters_mesh import *
from fauna_hunters_body import *
from fauna_hunters_limbs import *


def mouth_row(shell, start, offset_axis, gum, arch, rows, zone, region, s, jaw, gum_in=0.0025, fur=0.0):
    lip = shell.p[start].copy()
    ids = [start]
    for k in range(1, rows + 1):
        f = (k - 1) / max(rows - 1, 1)
        position = lip.copy()
        position[0] = max(lip[0] - gum_in, lip[0] * 0.6) * (1.0 - f)
        position = position + offset_axis * (gum + arch * (1.0 - (1.0 - f) ** 2))
        if k == rows:
            position[0] = 0.0
        ids.append(shell.add(position, zone, region, s, 0.0, (0.0, 0.0, 0.0), fur, None, 0, {"jaw": jaw, "inside": 1.0, "gum": 1.0 if k == 1 else 0.0}))
    return ids


def build_mouth(shell, body, spec):
    grid = body.grid
    half = body.half
    lip = spec["lip"]
    rows = spec.get("rows", 3)
    corner = body.corner
    chin = body.key_ring[spec["chin"]]
    last = body.count - 1
    span = float(spec.get("ramp", 3.0))
    jaw_back = float(spec.get("jaw_back", span))
    inset = spec.get("inset", 0.0015)

    def ramp(i):
        return float(smoothstep(corner - jaw_back, corner + span, i))

    for i in range(body.count):
        for j in range(half + 1):
            vertex = grid[i][j]
            if j > lip:
                shell.pf[vertex]["jaw"] = ramp(i)
            elif j == lip:
                shell.pf[vertex]["jaw"] = 0.5 * ramp(i) if i <= corner else 0.0
    upper_lip = {corner: grid[corner][lip]}
    lower_lip = {corner: grid[corner][lip]}
    shell.pf[grid[corner][lip]]["lip"] = 1.0
    for i in range(corner + 1, last + 1):
        upper_lip[i] = grid[i][lip]
        shell.pf[grid[i][lip]]["lip"] = 1.0
        if i <= chin:
            position = shell.p[grid[i][lip]].copy()
            position[0] = max(position[0] - inset * ramp(i), 0.0)
            position = position + body.ups[i] * 0.0008 * ramp(i)
            lower_lip[i] = shell.add(position, ZONE_FUR, REG_JAW, body.arc[i], math.cos(body.thetas[lip]), -body.tangent[i], body.fur[i], None, 0, {"jaw": ramp(i), "lip": 1.0})
            for j in range(lip + 1, half + 1):
                shell.region[grid[i][j]] = REG_JAW

    def lower(i, j):
        return lower_lip[i] if j == lip else grid[i][j]

    depth = spec.get("depth", 0.012)
    back = mouth_row(shell, grid[corner][lip], -body.tangent[corner], depth * 0.6, depth * 0.4, rows, ZONE_MOUTH, REG_HEAD, body.arc[corner], 0.5)
    palate = {corner: back}
    floor = {corner: back}
    for i in range(corner + 1, last + 1):
        fade = min(1.0, (last - i) / 2.0) * min(1.0, (i - corner) / 1.5)
        palate[i] = mouth_row(shell, upper_lip[i], body.ups[i], spec.get("gum", 0.008) * fade, spec.get("arch", 0.008) * fade, rows, ZONE_MOUTH, REG_HEAD, body.arc[i], 0.0)
        if i <= chin:
            fade = min(1.0, (chin - i) / 2.0) * min(1.0, (i - corner) / 1.5)
            floor[i] = mouth_row(shell, lower_lip[i], -body.ups[i], spec.get("gum_low", 0.006) * fade, spec.get("dip", 0.004) * fade, rows, ZONE_MOUTH, REG_JAW, body.arc[i], ramp(i))
    for row, index, bulge in ((palate[last], last, spec.get("lip_front", 0.003)), (floor[chin], chin, spec.get("lip_front_low", 0.002))):
        for k, vertex in enumerate(row[1:]):
            f = (k + 1) / rows
            shell.p[vertex] = shell.p[vertex] + body.tangent[index] * bulge * (1.0 - (1.0 - f) ** 2)
            shell.pf[vertex]["lip"] = 1.0
            shell.pf[vertex]["inside"] = 0.5
            shell.zone[vertex] = ZONE_FUR
    for i in range(corner, last):
        for j in range(lip):
            if body.alive[i, j]:
                shell.face(grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
        shell.strip(palate[i], palate[i + 1], closed=False)
        shell.seam(upper_lip[i], upper_lip[i + 1])
        shell.crease(upper_lip[i], upper_lip[i + 1])
    for i in range(corner, chin):
        for j in range(lip, half):
            shell.face(lower(i, j), lower(i, j + 1), lower(i + 1, j + 1), lower(i + 1, j))
        shell.strip(floor[i], floor[i + 1], closed=False)
        shell.seam(lower_lip[i], lower_lip[i + 1])
        shell.crease(lower_lip[i], lower_lip[i + 1])
        shell.seam(grid[i][half], grid[i + 1][half])
    nose_position = body.centers[last] + body.tangent[last] * spec.get("nose_cap", 0.006) + body.ups[last] * spec.get("nose_lift", 0.0)
    nose_position[0] = 0.0
    nose = shell.add(nose_position, ZONE_FUR, REG_HEAD, body.arc[last], 0.0, -body.tangent[last], 0.0, None, 0, {"lip": 0.0})
    shell.fan(grid[last][:lip + 1], nose, closed=False)
    shell.fan(palate[last], nose, closed=False)
    for k in range(rows):
        shell.seam(palate[last][k], palate[last][k + 1])
        shell.seam(floor[chin][k], floor[chin][k + 1])
        shell.crease(palate[last][k], palate[last][k + 1])
        shell.crease(floor[chin][k], floor[chin][k + 1])
    outer = [lower(chin, j) for j in range(lip, half + 1)]
    middle = (shell.p[outer[0]] + shell.p[outer[-1]]) * 0.5
    chin_position = np.array([0.0, middle[1], middle[2]]) + body.tangent[chin] * spec.get("chin_cap", 0.008)
    chin_pole = shell.add(chin_position, ZONE_FUR, REG_JAW, body.arc[chin], -1.0, -body.tangent[chin], body.fur[chin], None, 0, {"jaw": 1.0, "lip": 0.6})
    shell.fan(outer, chin_pole, closed=False)
    shell.fan(floor[chin], chin_pole, closed=False)
    shell.seam(grid[chin][half], chin_pole)
    body.upper_lip = upper_lip
    body.lower_lip = lower_lip
    body.palate = palate
    body.floor = floor
    body.chin = chin
    body.nose_pole = nose
    body.chin_pole = chin_pole
    body.lip = lip
    return body


def eye_frame(center, gaze, forward, slant):
    gaze = normalize(np.asarray(gaze, dtype=np.float64))
    forward = np.asarray(forward, dtype=np.float64)
    e1 = normalize(forward - gaze * float(forward @ gaze))
    e2 = np.cross(gaze, e1)
    if e2[2] < 0.0:
        e2 = -e2
    angle = math.radians(slant)
    a1 = e1 * math.cos(angle) + e2 * math.sin(angle)
    a2 = e2 * math.cos(angle) - e1 * math.sin(angle)
    return gaze, a1, a2


def lid_curve(phi, a, upper, lower, sharp):
    x = a * np.cos(phi)
    sine = np.sin(phi)
    y = np.where(sine >= 0.0, upper, lower) * power(sine, sharp)
    return x, y


def build_eye(shell, body, spec, forward):
    center = np.asarray(spec["center"], dtype=np.float64)
    radius = spec["radius"]
    gaze, e1, e2 = eye_frame(center, spec["gaze"], forward, spec.get("slant", 0.0))
    surface = center + gaze * radius
    di, dj = spec.get("patch", (3, 3))
    i0, j0, ci, cj = patch_at(body, surface, di, dj, spec.get("first", 0), body.corner, 1, body.lip - 1)
    loop, closed = hole(body, i0, i0 + di, j0, j0 + dj)
    loop = align_loop(shell, loop, surface, e2, -e1)
    count = len(loop)
    phi = np.arange(count) * (2.0 * math.pi / count)
    a = spec["width"]
    upper = spec["upper"]
    lower = spec["lower"]
    sharp = spec.get("sharp", 1.35)
    outer_scale = spec.get("outer", 2.1)
    for k, vertex in enumerate(loop):
        d = shell.p[vertex] - center
        depth = float(d @ gaze)
        x, y = lid_curve(phi[k], a * outer_scale, upper * outer_scale * 1.15, lower * outer_scale * 1.15, 1.0)
        target = center + e1 * x + e2 * y + gaze * depth
        shell.p[vertex] = shell.p[vertex] * 0.35 + target * 0.65
        shell.pf[vertex]["lid"] = 0.0
    rings = [loop]

    def on_ball(scale, lift, k, exponent):
        x, y = lid_curve(phi[k], a * scale, upper * scale, lower * scale, exponent)
        rho = math.hypot(x, y) / radius
        omega = math.atan2(y, x)
        direction = gaze * math.cos(rho) + (e1 * math.cos(omega) + e2 * math.sin(omega)) * math.sin(rho)
        return center + direction * (radius + lift)

    middle = []
    for k in range(count):
        position = (on_ball(1.0, 0.0006, k, sharp) * 0.55 + shell.p[loop[k]] * 0.45) + gaze * spec.get("brow", 0.0022)
        middle.append(shell.add(position, ZONE_FUR, REG_HEAD, body.arc[ci], 0.5, -body.tangent[ci], 0.3, None, 0, {"lid": 0.4}))
    shell.strip(rings[-1], middle)
    rings.append(middle)
    for scale, lift in ((1.0, 0.0007), (0.84, -0.0014)):
        ring = [shell.add(on_ball(scale, lift, k, sharp), ZONE_LID, REG_HEAD, body.arc[ci], 0.5, -body.tangent[ci], 0.3, None, 0, {"lid": 1.0}) for k in range(count)]
        shell.strip(rings[-1], ring)
        rings.append(ring)
    shell.crease_loop(rings[2])
    ball = []
    pole = shell.add(center + gaze * radius, ZONE_EYE, REG_HEAD, 0.0, 0.0, (0.0, 0.0, 0.0), 0.0, {"head": 1.0}, 1, {"eu": 0.0, "ev": 0.0})
    ball.append(pole)
    segments = spec.get("segments", 10)
    previous = None
    for polar in (18.0, 38.0, 60.0, 82.0, 104.0):
        ring = []
        for k in range(segments):
            angle = 2.0 * math.pi * k / segments
            sine = math.sin(math.radians(polar))
            direction = gaze * math.cos(math.radians(polar)) + (e1 * math.cos(angle) + e2 * math.sin(angle)) * sine
            ring.append(shell.add(center + direction * radius, ZONE_EYE, REG_HEAD, 0.0, 0.0, (0.0, 0.0, 0.0), 0.0, {"head": 1.0}, 1, {"eu": sine * math.cos(angle), "ev": sine * math.sin(angle)}))
        if previous is None:
            shell.fan(ring, pole)
        else:
            shell.strip(previous, ring)
        previous = ring
        ball.extend(ring)
    shell.marks.setdefault("eyeball_l", []).extend(ball)
    shell.marks.setdefault("eyelid_l", []).extend(rings[2])
    return rings
