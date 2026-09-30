import math
import numpy as np
from fauna_hunters_mesh import *
from fauna_hunters_body import *
from fauna_hunters_limbs import *
from fauna_hunters_head import *
from fauna_hunters_parts import *


class Animal:
    pass


def build_animal(spec):
    shell = Shell()
    animal = Animal()
    body = build_body(shell, spec["body"])
    rear_cap(shell, body, spec["body"].get("rear_cap", 0.02))
    animal.body = body
    animal.limbs = {}
    relax = []
    forward = np.asarray(spec["head"]["forward"], dtype=np.float64)
    for eye in spec.get("eyes", []):
        rings = build_eye(shell, body, eye, forward)
        relax.extend(rings[0])
    for ear in spec.get("ears", []):
        rings = build_ear(shell, body, ear)
        relax.extend(rings[0])
    for name, leg in spec["legs"].items():
        region = REG_FORE if name == "fore" else REG_HIND
        di, dj = leg["patch"]["size"]
        i0, j0, ci, cj = patch_at(body, leg["patch"]["center"], di, dj, 1, body.corner - 1, 1, body.half - 1)
        loop, closed = hole(body, i0, i0 + di, j0, j0 + dj)
        limb = build_limb(shell, loop, leg, region, 1.0)
        for ring in limb.all_rings[:int(leg.get("blend", 2)) + int(leg.get("relax", 2))]:
            relax.extend(ring)
        if "paw" in leg:
            build_toes(shell, limb, leg["paw"], leg["paw"]["bone"], region)
        animal.limbs[name] = limb
    tail = spec.get("tail")
    if tail:
        di, dj = tail["patch"]["size"]
        i0, j0, ci, cj = patch_at(body, tail["patch"]["center"], di, dj, tail["patch"].get("first", 0), body.corner - 1, 0, body.half - 1)
        chain, closed = hole(body, i0, i0 + di, 0, dj)
        limb = build_tail(shell, body, chain, tail)
        relax.extend(chain)
        relax.extend(limb.all_rings[1])
        animal.limbs["tail"] = limb
    body_faces(shell, body, 0, body.corner)
    build_mouth(shell, body, spec["body"]["mouth"])
    belly_seam(shell, body, 0, body.corner)
    if "head_seam" in spec["body"]:
        ring_seam(shell, body, body.key_ring[spec["body"]["head_seam"]])
    if "teeth" in spec:
        build_teeth(shell, body, spec["teeth"])
    tongue = tongue_keys(shell, body, spec["tongue"]) if "tongue" in spec else None
    shell.marks["relax_l"] = relax
    full = shell.mirrored()
    if tongue:
        build_tongue(full, tongue, spec["tongue"])
    full.compact()
    animal.shell = full
    return animal


def adjacency(count, faces):
    neighbours = [set() for _ in range(count)]
    for face in faces:
        for k in range(len(face)):
            a = face[k]
            b = face[(k + 1) % len(face)]
            neighbours[a].add(b)
            neighbours[b].add(a)
    return neighbours


def relax(shell, names=("relax_l", "relax_r"), iterations=8, amount=0.5, grow=1):
    positions = shell.positions()
    neighbours = adjacency(len(positions), shell.faces)
    selected = set()
    for name in names:
        selected.update(shell.marks.get(name, []))
    for _ in range(grow):
        grown = set(selected)
        for vertex in selected:
            grown.update(neighbours[vertex])
        selected = grown
    selected = [v for v in selected if shell.zone[v] in (ZONE_FUR,) and "lid" not in shell.pf[v] and shell.region[v] != REG_EAR and "toe" not in shell.pf[v] and "inside" not in shell.pf[v]]
    lists = [np.array(sorted(neighbours[v]), dtype=np.int64) for v in selected]
    index = np.array(selected, dtype=np.int64)
    for _ in range(iterations):
        average = np.array([positions[near].mean(axis=0) for near in lists])
        positions[index] = positions[index] * (1.0 - amount) + average * amount
    symmetrize(shell, positions)
    shell.p = [p for p in positions]
    return positions


def symmetrize(shell, positions):
    twin = getattr(shell, "twin", None)
    if twin is None:
        return
    count = min(len(twin), len(positions))


def vertex_normals(positions, faces):
    normals = np.zeros_like(positions)
    for face in faces:
        a = positions[face[0]]
        for k in range(1, len(face) - 1):
            n = np.cross(positions[face[k]] - a, positions[face[k + 1]] - a)
            for index in (face[0], face[k], face[k + 1]):
                normals[index] += n
    return normalize(normals)


def bump(positions, normals, center, radii, amount, mask=None, rotation=None):
    center = np.asarray(center, dtype=np.float64)
    d = positions - center[None, :]
    if rotation is not None:
        d = d @ np.asarray(rotation, dtype=np.float64)
    q = (d / np.asarray(radii, dtype=np.float64)[None, :]) ** 2
    falloff = np.exp(-q.sum(axis=1) * 1.6)
    if mask is not None:
        falloff = falloff * mask
    return normals * (falloff * amount)[:, None]


def sculpt(shell, bumps):
    positions = shell.positions()
    normals = vertex_normals(positions, shell.faces)
    skin = np.array([1.0 if (zone == ZONE_FUR or zone == ZONE_EAR_IN) and "lid" not in pf and "toe" not in pf else 0.0 for zone, pf in zip(shell.zone, shell.pf)])
    regions = np.array(shell.region)
    total = np.zeros_like(positions)
    for entry in bumps:
        mask = skin.copy()
        if "regions" in entry:
            mask = mask * np.isin(regions, entry["regions"])
        for sign in ((1.0, -1.0) if entry.get("mirror", True) and abs(entry["center"][0]) > 1e-6 else (1.0,)):
            center = np.array(entry["center"], dtype=np.float64) * np.array([sign, 1.0, 1.0])
            total += bump(positions, normals, center, entry["radii"], entry["amount"], mask)
    positions = positions + total
    shell.p = [p for p in positions]
    return positions
