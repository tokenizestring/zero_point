import math
import numpy as np
from fauna_hunters_mesh import *


def ring_points(top, bot, w, c, e, nt, nb, thetas):
    top = np.asarray(top, dtype=np.float64)
    bot = np.asarray(bot, dtype=np.float64)
    up = top - bot
    height = np.linalg.norm(up)
    unit = up / max(height, 1e-9)
    center = bot + up * c
    zn = np.cos(thetas)
    xn = np.sin(thetas)
    n = np.where(zn >= 0.0, nt, nb)
    zz = power(zn, 2.0 / n)
    xx = power(xn, 2.0 / n)
    x = w * xx * (1.0 + e * zz)
    z = np.where(zz >= 0.0, (1.0 - c) * height * zz, c * height * zz)
    return center[None, :] + x[:, None] * np.array([1.0, 0.0, 0.0]) + z[:, None] * unit[None, :], center, unit


class Body:
    pass


def station_table(keys):
    index = []
    for k, key in enumerate(keys[:-1]):
        count = int(key.get("n", 1))
        for m in range(count):
            index.append(k + m / count)
    index.append(float(len(keys) - 1))
    return np.array(index)


def key_values(keys, name, default=None):
    return np.array([key.get(name, default) for key in keys], dtype=np.float64)


def build_body(shell, spec):
    keys = spec["keys"]
    half = spec["half"]
    body = Body()
    stations = station_table(keys)
    kx = np.arange(len(keys), dtype=np.float64)
    top = pchip(kx, np.array([[0.0, key["top"][0], key["top"][1]] for key in keys]), stations)
    bot = pchip(kx, np.array([[0.0, key["bot"][0], key["bot"][1]] for key in keys]), stations)
    w = pchip(kx, key_values(keys, "w"), stations)
    c = pchip(kx, key_values(keys, "c", 0.5), stations)
    e = pchip(kx, key_values(keys, "e", 0.0), stations)
    nt = pchip(kx, key_values(keys, "nt", 2.0), stations)
    nb = pchip(kx, key_values(keys, "nb", 2.0), stations)
    fur = pchip(kx, key_values(keys, "fur", 1.0), stations)
    regions = [keys[int(min(math.floor(t + 1e-9), len(keys) - 1))].get("region", REG_BODY) for t in stations]
    thetas = np.asarray(spec.get("angles", np.linspace(0.0, math.pi, half + 1)), dtype=np.float64)
    count = len(stations)
    centers = np.zeros((count, 3))
    ups = np.zeros((count, 3))
    points = []
    for i in range(count):
        ring, centers[i], ups[i] = ring_points(top[i], bot[i], w[i], c[i], e[i], nt[i], nb[i], thetas)
        ring[0, 0] = 0.0
        ring[-1, 0] = 0.0
        points.append(ring)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(centers, axis=0), axis=1))])
    tangent = np.gradient(centers, axis=0)
    tangent = normalize(tangent)
    body.stations = stations
    body.centers = centers
    body.ups = ups
    body.arc = arc
    body.tangent = tangent
    body.top = top
    body.bot = bot
    body.w = w
    body.thetas = thetas
    body.half = half
    body.count = count
    body.points = points
    body.regions = regions
    body.key_ring = {}
    for k, key in enumerate(keys):
        ring_index = int(np.argmin(np.abs(stations - k)))
        body.key_ring[k] = ring_index
        if "name" in key:
            body.key_ring[key["name"]] = ring_index
    corner = body.key_ring[spec["mouth"]["corner"]] if "mouth" in spec else count - 1
    body.corner = corner
    body.lip = spec["mouth"]["lip"] if "mouth" in spec else half
    grid = []
    for i in range(count):
        ring = []
        for j in range(half + 1):
            side = math.sin(thetas[j])
            flow = -tangent[i] + np.array([0.0, 0.0, -0.45 * side])
            ring.append(shell.add(points[i][j], ZONE_FUR, regions[i], arc[i], math.cos(thetas[j]), normalize(flow), fur[i]))
        grid.append(ring)
    body.grid = grid
    body.alive = np.ones((count - 1, half), dtype=bool)
    body.fur = fur
    return body


def body_faces(shell, body, first=0, last=None, columns=None):
    last = body.count - 1 if last is None else last
    for i in range(first, last):
        for j in range(body.half):
            if body.alive[i, j] and (columns is None or columns(i, j)):
                shell.face(body.grid[i][j], body.grid[i][j + 1], body.grid[i + 1][j + 1], body.grid[i + 1][j])


def rear_cap(shell, body, offset):
    ring = body.grid[0]
    position = body.centers[0] - body.tangent[0] * offset
    position[0] = 0.0
    pole = shell.add(position, ZONE_FUR, body.regions[0], body.arc[0] - offset, 0.0, (0.0, 0.0, -1.0), body.fur[0])
    shell.fan(ring, pole, closed=False)
    shell.seam(ring[-1], pole)
    body.rear_pole = pole
    return pole


def belly_seam(shell, body, first=0, last=None):
    last = body.count - 1 if last is None else last
    for i in range(first, last):
        shell.seam(body.grid[i][-1], body.grid[i + 1][-1])


def ring_seam(shell, body, index):
    for j in range(body.half):
        shell.seam(body.grid[index][j], body.grid[index][j + 1])


def hole(body, i0, i1, j0, j1):
    body.alive[i0:i1, j0:j1] = False
    grid = body.grid
    loop = []
    for j in range(j0, j1):
        loop.append(grid[i0][j])
    for i in range(i0, i1):
        loop.append(grid[i][j1])
    if j0 > 0:
        for j in range(j1, j0, -1):
            loop.append(grid[i1][j])
        for i in range(i1, i0, -1):
            loop.append(grid[i][j0])
        return loop, True
    for j in range(j1, -1, -1):
        loop.append(grid[i1][j])
    return loop, False


def nearest_cell(body, target, region=None, first=0, last=None):
    last = body.count if last is None else last
    best = None
    target = np.asarray(target, dtype=np.float64)
    for i in range(first, last):
        distance = np.linalg.norm(body.points[i] - target[None, :], axis=1)
        j = int(np.argmin(distance))
        if best is None or distance[j] < best[0]:
            best = (distance[j], i, j)
    return best[1], best[2]


def patch_at(body, target, di, dj, i_min=0, i_max=None, j_min=1, j_max=None):
    i_max = body.count - 1 if i_max is None else i_max
    j_max = body.half if j_max is None else j_max
    target = np.asarray(target, dtype=np.float64)
    ci, cj = nearest_cell(body, target, first=i_min, last=i_max + 1)
    here = body.points[ci][cj]
    along = body.points[min(ci + 1, body.count - 1)][cj] - body.points[max(ci - 1, 0)][cj]
    around = body.points[ci][min(cj + 1, body.half)] - body.points[ci][max(cj - 1, 0)]
    fi = float((target - here) @ along) / max(float(along @ along), 1e-12) * (min(ci + 1, body.count - 1) - max(ci - 1, 0))
    fj = float((target - here) @ around) / max(float(around @ around), 1e-12) * (min(cj + 1, body.half) - max(cj - 1, 0))
    i0 = int(round(ci + fi - di * 0.5))
    j0 = int(round(cj + fj - dj * 0.5))
    i0 = max(i_min, min(i0, i_max - di))
    j0 = max(j_min, min(j0, j_max - dj))
    return i0, j0, ci, cj
