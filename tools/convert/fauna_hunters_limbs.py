import math
import numpy as np
from fauna_hunters_mesh import *
from fauna_hunters_body import *


def limb_ring(center, front, side, df, db, hw, nf, nb, count):
    psi = np.arange(count) * (2.0 * math.pi / count)
    q = np.sin(psi)
    r = -np.cos(psi)
    exponent = np.where(q >= 0.0, nf, nb)
    depth = np.where(q >= 0.0, df, db)
    return center[None, :] + front[None, :] * (depth * power(q, 2.0 / exponent))[:, None] + side[None, :] * (hw * power(r, 2.0 / exponent))[:, None], psi


def align_loop(shell, loop, center, front, side):
    positions = np.array([shell.p[i] for i in loop]) - center[None, :]
    psi = np.arctan2(positions @ front, -(positions @ side))
    steps = np.diff(np.concatenate([psi, psi[:1]]))
    steps = (steps + math.pi) % (2.0 * math.pi) - math.pi
    if steps.sum() < 0.0:
        loop = loop[::-1]
        psi = psi[::-1]
    start = int(np.argmin(np.abs((psi + math.pi) % (2.0 * math.pi) - math.pi)))
    return loop[start:] + loop[:start]


class Limb:
    pass


def limb_frames(keys, side_sign, lateral=None):
    index = station_table(keys)
    kx = np.arange(len(keys), dtype=np.float64)
    centers = pchip(kx, np.array([key["p"] for key in keys], dtype=np.float64), index)
    values = {name: pchip(kx, key_values(keys, name, default), index) for name, default in (("df", 0.03), ("db", 0.03), ("hw", 0.03), ("nf", 2.0), ("nb", 2.0), ("fur", 1.0))}
    tangent = normalize(np.gradient(centers, axis=0))
    for k, key in enumerate(keys):
        if "dir" in key:
            ring_index = int(np.argmin(np.abs(index - k)))
            tangent[ring_index] = normalize(np.array(key["dir"], dtype=np.float64))
    lateral = np.array([side_sign, 0.0, 0.0]) if lateral is None else np.asarray(lateral, dtype=np.float64)
    front = normalize(np.cross(tangent, lateral[None, :]))
    side = normalize(np.cross(front, tangent))
    counts = []
    current = None
    for t in index:
        key = keys[int(min(math.floor(t + 1e-9), len(keys) - 1))]
        current = key.get("count", current)
        counts.append(current)
    return index, centers, tangent, front, side, values, counts


def build_limb(shell, loop, spec, region, side_sign=1.0):
    keys = spec["keys"]
    limb = Limb()
    index, centers, tangent, front, side, values, counts = limb_frames(keys, side_sign)
    if counts[0] is None:
        counts = [len(loop) if value is None else value for value in counts]
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(centers, axis=0), axis=1))])
    loop = align_loop(shell, loop, centers[0], front[0], side[0])
    first, psi = limb_ring(centers[0], front[0], side[0], values["df"][0], values["db"][0], values["hw"][0], values["nf"][0], values["nb"][0], len(loop))
    blend = int(spec.get("blend", 2))
    bulge = spec.get("bulge", 0.0)
    boundary = np.array([shell.p[i] for i in loop])
    outward = np.array([side_sign, 0.0, 0.0])
    rings = [loop]
    for step in range(1, blend):
        f = step / blend
        ease = f * f * (3.0 - 2.0 * f)
        ring = []
        for k in range(len(loop)):
            position = boundary[k] * (1.0 - ease) + first[k] * ease + outward * bulge * math.sin(math.pi * f)
            flow = normalize(tangent[0] * ease + np.array([0.0, 0.35, -0.9]) * (1.0 - ease))
            ring.append(shell.add(position, ZONE_FUR, region, -arc[1] * (1.0 - f) if len(arc) > 1 else 0.0, -math.cos(psi[k]), flow, values["fur"][0]))
        shell.strip(rings[-1], ring)
        rings.append(ring)
    limb.rings = []
    previous = rings[-1]
    for i in range(len(index)):
        count = counts[i]
        points, psi = limb_ring(centers[i], front[i], side[i], values["df"][i], values["db"][i], values["hw"][i], values["nf"][i], values["nb"][i], count)
        ring = [shell.add(points[k], ZONE_FUR, region, arc[i], -math.cos(psi[k]), tangent[i], values["fur"][i]) for k in range(count)]
        shell.strip(previous, ring)
        previous = ring
        rings.append(ring)
        limb.rings.append(ring)
    cap = spec.get("cap", 0.01)
    pole = shell.add(centers[-1] + tangent[-1] * cap, ZONE_FUR, region, arc[-1] + cap, 0.0, tangent[-1], values["fur"][-1])
    shell.fan(previous, pole)
    for a, b in zip(rings[:-1], rings[1:]):
        shell.seam(a[0], b[0])
    shell.seam(rings[-1][0], pole)
    shell.seam_loop(loop)
    limb.all_rings = rings
    limb.pole = pole
    limb.centers = centers
    limb.arc = arc
    limb.tangent = tangent
    limb.front = front
    limb.side = side
    limb.index = index
    limb.loop = loop
    limb.key_ring = {k: int(np.argmin(np.abs(index - k))) for k in range(len(keys))}
    return limb


def build_tail(shell, body, chain, spec):
    keys = spec["keys"]
    index = station_table(keys)
    kx = np.arange(len(keys), dtype=np.float64)
    centers = pchip(kx, np.array([[0.0, key["p"][0], key["p"][1]] for key in keys], dtype=np.float64), index)
    rt = pchip(kx, key_values(keys, "rt", 0.03), index)
    rb = pchip(kx, key_values(keys, "rb", 0.03), index)
    rw = pchip(kx, key_values(keys, "rw", 0.03), index)
    fur = pchip(kx, key_values(keys, "fur", 1.0), index)
    tangent = normalize(np.gradient(centers, axis=0))
    up = normalize(np.cross(np.array([[1.0, 0.0, 0.0]]), tangent))
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(centers, axis=0), axis=1))])
    chain = chain[::-1]
    count = len(chain)
    thetas = np.linspace(0.0, math.pi, count)
    rings = [chain]
    limb = Limb()
    limb.rings = []
    for i in range(len(index)):
        ring = []
        for k in range(count):
            z = math.cos(thetas[k])
            x = math.sin(thetas[k])
            position = centers[i] + up[i] * (rt[i] if z >= 0.0 else rb[i]) * z + np.array([1.0, 0.0, 0.0]) * rw[i] * x
            if k == 0 or k == count - 1:
                position[0] = 0.0
            ring.append(shell.add(position, ZONE_FUR, REG_TAIL, arc[i], z, tangent[i], fur[i]))
        shell.strip(rings[-1], ring, closed=False)
        rings.append(ring)
        limb.rings.append(ring)
    cap = spec.get("cap", 0.02)
    pole = shell.add(centers[-1] + tangent[-1] * cap, ZONE_FUR, REG_TAIL, arc[-1] + cap, 0.0, tangent[-1], fur[-1])
    pole_position = shell.p[pole]
    pole_position[0] = 0.0
    shell.fan(rings[-1], pole, closed=False)
    for a, b in zip(rings[:-1], rings[1:]):
        shell.seam(a[-1], b[-1])
    shell.seam(rings[-1][-1], pole)
    shell.seam_loop(chain, closed=False)
    limb.all_rings = rings
    limb.pole = pole
    limb.centers = centers
    limb.arc = arc
    limb.tangent = tangent
    limb.up = up
    limb.index = index
    return limb


def build_tube(shell, keys, count, zone, region, weights=None, island=0, lateral=(1.0, 0.0, 0.0), start_cap=0.0, end_cap=0.0, fur=0.0, pf=None, s=0.0, around=0.0, flow=None):
    index, centers, tangent, front, side, values, counts = limb_frames(keys, 1.0, lateral)
    rings = []
    previous = None
    created = []
    for i in range(len(index)):
        points, psi = limb_ring(centers[i], front[i], side[i], values["df"][i], values["db"][i], values["hw"][i], values["nf"][i], values["nb"][i], count)
        ring = [shell.add(points[k], zone, region, s, around, tangent[i] if flow is None else flow, fur, weights, island, pf) for k in range(count)]
        created.extend(ring)
        if previous is not None:
            shell.strip(previous, ring)
        previous = ring
        rings.append(ring)
    first = shell.add(centers[0] - tangent[0] * start_cap, zone, region, s, around, tangent[0] if flow is None else flow, fur, weights, island, pf)
    shell.fan(rings[0][::-1], first)
    last = shell.add(centers[-1] + tangent[-1] * end_cap, zone, region, s, around, tangent[-1] if flow is None else flow, fur, weights, island, pf)
    shell.fan(rings[-1], last)
    created.extend([first, last])
    shell.seam(first, rings[0][0])
    for a, b in zip(rings[:-1], rings[1:]):
        shell.seam(a[0], b[0])
    shell.seam(rings[-1][0], last)
    return rings, created
