import math
import numpy as np
from fauna_hunters_mesh import *


def box_mask(points, low, high, soft):
    low = np.asarray(low, dtype=np.float64)
    high = np.asarray(high, dtype=np.float64)
    soft = np.maximum(np.asarray(soft, dtype=np.float64) * np.ones(3), 1e-6)
    inside = smoothstep(0.0, 1.0, (points - low[None, :]) / soft[None, :] + 0.5) * smoothstep(0.0, 1.0, (high[None, :] - points) / soft[None, :] + 0.5)
    return inside.prod(axis=1)


def ball_mask(points, center, radii):
    d = (points - np.asarray(center, dtype=np.float64)[None, :]) / np.asarray(radii, dtype=np.float64)[None, :]
    return np.clip(1.0 - (d * d).sum(axis=1), 0.0, 1.0) ** 0.5


def face_data(positions, faces):
    centers = np.zeros((len(faces), 3))
    normals = np.zeros((len(faces), 3))
    areas = np.zeros(len(faces))
    for index, face in enumerate(faces):
        points = positions[list(face)]
        centers[index] = points.mean(axis=0)
        normal = np.zeros(3)
        for k in range(1, len(face) - 1):
            normal += np.cross(points[k] - points[0], points[k + 1] - points[0])
        length = np.linalg.norm(normal)
        areas[index] = 0.5 * length
        normals[index] = normal / max(length, 1e-12)
    return centers, normals, areas


def uv_direction(points, uvs, direction):
    e1 = points[1] - points[0]
    e2 = points[2] - points[0]
    gram = np.array([[e1 @ e1, e1 @ e2], [e1 @ e2, e2 @ e2]])
    rhs = np.array([direction @ e1, direction @ e2])
    if abs(np.linalg.det(gram)) < 1e-18:
        return np.array([1.0, 0.0])
    alpha, beta = np.linalg.solve(gram, rhs)
    step = (uvs[1] - uvs[0]) * alpha + (uvs[2] - uvs[0]) * beta
    length = np.linalg.norm(step)
    return step / length if length > 1e-12 else np.array([1.0, 0.0])


class Tufts:
    def __init__(self):
        self.positions = []
        self.normals = []
        self.faces = []
        self.uvs = []
        self.corners = []
        self.bary = []
        self.count = 0


def grow_tufts(data, fields, seed=7):
    positions = data["p"]
    faces = data["faces"]
    face_uvs = data["face_uvs"]
    vertex_normals = data["normals"]
    flow = data["flow"]
    allowed = data["allowed"]
    rng = np.random.default_rng(seed)
    centers, face_normals, areas = face_data(positions, faces)
    tufts = Tufts()
    for field in fields:
        mask = field["mask"](data)
        stations = field.get("stations", (0.0, 0.5))
        profile = field.get("profile", (0.8, 1.0))
        for index, face in enumerate(faces):
            if not allowed[index]:
                continue
            strength = float(mask[list(face)].mean())
            if strength <= 0.02:
                continue
            expected = areas[index] * field["density"] * strength
            count = int(math.floor(expected + rng.random()))
            for _ in range(count):
                order = list(face)
                if len(order) == 4 and rng.random() < 0.5:
                    local = [0, 2, 3]
                else:
                    local = [0, 1, 2]
                corners = [order[k] for k in local]
                a, b = rng.random(), rng.random()
                if a + b > 1.0:
                    a, b = 1.0 - a, 1.0 - b
                bary = np.array([1.0 - a - b, a, b])
                root = (positions[corners] * bary[:, None]).sum(axis=0)
                normal = normalize((vertex_normals[corners] * bary[:, None]).sum(axis=0))
                along = (flow[corners] * bary[:, None]).sum(axis=0)
                if "direction" in field:
                    extra = np.asarray(field["direction"], dtype=np.float64) * np.array([1.0 if root[0] >= 0.0 else -1.0, 1.0, 1.0])
                    steer = field.get("steer", 0.7)
                    along = normalize(along) * (1.0 - steer) + normalize(extra) * steer
                along = along - normal * float(along @ normal)
                if np.linalg.norm(along) < 1e-6:
                    continue
                along = normalize(along)
                side = np.cross(normal, along)
                along = normalize(along + side * rng.normal(0.0, field.get("jitter", 0.18)))
                side = normalize(np.cross(normal, along))
                lift = math.radians(field.get("lift", 20.0) * (0.7 + 0.6 * rng.random()))
                direction = along * math.cos(lift) + normal * math.sin(lift)
                up = normalize(np.cross(direction, side))
                length = field["length"] * (0.7 + 0.6 * rng.random()) * (0.55 + 0.45 * strength)
                width = field["width"] * (0.75 + 0.5 * rng.random())
                thick = width * field.get("thick", 0.45)
                bend = (-normal * field.get("hug", 0.15) + np.array([0.0, 0.0, -1.0]) * field.get("droop", 0.1)) * length
                start = root - normal * field.get("sink", 0.004) - along * length * 0.12
                uv_corner = np.array([face_uvs[index][k] for k in local])
                uv_root = (uv_corner * bary[:, None]).sum(axis=0)
                uv_along = uv_direction(positions[corners], uv_corner, along)
                uv_side = np.array([-uv_along[1], uv_along[0]])
                uv_length = field.get("uv_length", 0.004)
                uv_width = field.get("uv_width", 0.0012)
                base = len(tufts.positions)
                blend = field.get("normal_blend", 0.55)
                for t, scale in zip(stations, profile):
                    center = start + direction * length * t + bend * t * t
                    for offset, rise in ((-1.0, 0.0), (0.0, 1.0), (1.0, 0.0)):
                        tufts.positions.append(center + side * offset * width * scale + up * rise * thick * scale)
                        tufts.uvs.append(uv_root + uv_along * uv_length * t + uv_side * uv_width * offset)
                        tufts.normals.append(normalize(normal * blend + (side * offset * 0.6 + up * (0.35 + 0.65 * rise)) * (1.0 - blend)))
                tufts.positions.append(start + direction * length + bend)
                tufts.uvs.append(uv_root + uv_along * uv_length)
                tufts.normals.append(normalize(normal * blend + (up * 0.6 + direction * 0.5) * (1.0 - blend)))
                rings = len(stations)
                for r in range(rings - 1):
                    a0 = base + r * 3
                    b0 = base + (r + 1) * 3
                    tufts.faces.append((a0, b0, b0 + 1, a0 + 1))
                    tufts.faces.append((a0 + 1, b0 + 1, b0 + 2, a0 + 2))
                    tufts.faces.append((a0 + 2, b0 + 2, b0, a0))
                last = base + (rings - 1) * 3
                apex = base + rings * 3
                tufts.faces.append((last, apex, last + 1))
                tufts.faces.append((last + 1, apex, last + 2))
                tufts.faces.append((last + 2, apex, last))
                for _ in range(rings * 3 + 1):
                    tufts.corners.append(corners)
                    tufts.bary.append(bary)
                tufts.count += 1
    return tufts
