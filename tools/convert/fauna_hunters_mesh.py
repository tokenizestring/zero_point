import math
import numpy as np

ZONE_FUR = 0
ZONE_NOSE = 1
ZONE_LID = 2
ZONE_EYE = 3
ZONE_MOUTH = 4
ZONE_TONGUE = 5
ZONE_TEETH = 6
ZONE_CLAW = 7
ZONE_PAD = 8
ZONE_EAR_IN = 9
ZONE_LIP = 10

REG_BODY = 0
REG_NECK = 1
REG_HEAD = 2
REG_FORE = 3
REG_HIND = 4
REG_TAIL = 5
REG_EAR = 6
REG_JAW = 7


def smoothstep(low, high, value):
    t = np.clip((np.asarray(value, dtype=np.float64) - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def normalize(vector):
    vector = np.asarray(vector, dtype=np.float64)
    length = np.linalg.norm(vector, axis=-1, keepdims=True)
    return vector / np.maximum(length, 1e-12)


def pchip(xk, yk, x):
    xk = np.asarray(xk, dtype=np.float64)
    yk = np.asarray(yk, dtype=np.float64)
    flat = yk.ndim == 1
    if flat:
        yk = yk[:, None]
    x = np.atleast_1d(np.asarray(x, dtype=np.float64))
    count = len(xk)
    if count == 1:
        result = np.repeat(yk, len(x), axis=0)
        return result[:, 0] if flat else result
    h = np.diff(xk)
    delta = np.diff(yk, axis=0) / h[:, None]
    slope = np.zeros_like(yk)
    if count == 2:
        slope[:] = delta[0]
    else:
        for k in range(1, count - 1):
            w1 = 2.0 * h[k] + h[k - 1]
            w2 = h[k] + 2.0 * h[k - 1]
            same = delta[k - 1] * delta[k] > 0.0
            safe_a = np.where(same, delta[k - 1], 1.0)
            safe_b = np.where(same, delta[k], 1.0)
            slope[k] = np.where(same, (w1 + w2) / (w1 / safe_a + w2 / safe_b), 0.0)
        for end, first, second, ha, hb in ((0, delta[0], delta[1], h[0], h[1]), (count - 1, delta[-1], delta[-2], h[-1], h[-2])):
            value = ((2.0 * ha + hb) * first - ha * second) / (ha + hb)
            value = np.where(np.sign(value) != np.sign(first), 0.0, value)
            value = np.where((np.sign(first) != np.sign(second)) & (np.abs(value) > 3.0 * np.abs(first)), 3.0 * first, value)
            slope[end] = value
    index = np.clip(np.searchsorted(xk, x, side='right') - 1, 0, count - 2)
    t = (x - xk[index]) / h[index]
    t = np.clip(t, 0.0, 1.0)[:, None]
    hh = h[index][:, None]
    h00 = 2 * t ** 3 - 3 * t ** 2 + 1
    h10 = t ** 3 - 2 * t ** 2 + t
    h01 = -2 * t ** 3 + 3 * t ** 2
    h11 = t ** 3 - t ** 2
    result = h00 * yk[index] + h10 * hh * slope[index] + h01 * yk[index + 1] + h11 * hh * slope[index + 1]
    return result[:, 0] if flat else result


def power(value, exponent):
    return np.sign(value) * np.abs(value) ** exponent


class Shell:
    def __init__(self):
        self.p = []
        self.faces = []
        self.zone = []
        self.region = []
        self.s = []
        self.around = []
        self.flow = []
        self.fur = []
        self.w = []
        self.pf = []
        self.island = []
        self.seams = set()
        self.sharp = set()
        self.marks = {}

    def add(self, position, zone=ZONE_FUR, region=REG_BODY, s=0.0, around=0.0, flow=(0.0, 0.0, 0.0), fur=1.0, w=None, island=0, pf=None):
        self.p.append(np.asarray(position, dtype=np.float64))
        self.pf.append(dict(pf) if pf else {})
        self.zone.append(zone)
        self.region.append(region)
        self.s.append(float(s))
        self.around.append(float(around))
        self.flow.append(np.asarray(flow, dtype=np.float64))
        self.fur.append(float(fur))
        self.w.append(dict(w) if w else {})
        self.island.append(island)
        return len(self.p) - 1

    def face(self, *indices):
        unique = []
        for index in indices:
            if index not in unique:
                unique.append(index)
        if len(unique) >= 3:
            self.faces.append(tuple(unique))

    def seam(self, a, b):
        if a != b:
            self.seams.add((min(a, b), max(a, b)))

    def crease(self, a, b):
        if a != b:
            self.sharp.add((min(a, b), max(a, b)))

    def crease_loop(self, ring, closed=True):
        for k in range(len(ring) - (0 if closed else 1)):
            self.crease(ring[k], ring[(k + 1) % len(ring)])

    def seam_loop(self, ring, closed=True):
        for k in range(len(ring) - (0 if closed else 1)):
            self.seam(ring[k], ring[(k + 1) % len(ring)])

    def strip(self, ring_a, ring_b, closed=True):
        count_a = len(ring_a)
        count_b = len(ring_b)
        if count_a == count_b:
            for k in range(count_a - (0 if closed else 1)):
                n = (k + 1) % count_a
                self.face(ring_a[k], ring_a[n], ring_b[n], ring_b[k])
            return
        steps_a = count_a if closed else count_a - 1
        steps_b = count_b if closed else count_b - 1
        a = 0
        b = 0
        while a < steps_a or b < steps_b:
            next_a = (a + 1) / steps_a if a < steps_a else 2.0
            next_b = (b + 1) / steps_b if b < steps_b else 2.0
            if next_a <= next_b:
                self.face(ring_a[a % count_a], ring_a[(a + 1) % count_a], ring_b[b % count_b])
                a += 1
            else:
                self.face(ring_a[a % count_a], ring_b[(b + 1) % count_b], ring_b[b % count_b])
                b += 1

    def fan(self, ring, center, closed=True):
        for k in range(len(ring) - (0 if closed else 1)):
            self.face(ring[k], ring[(k + 1) % len(ring)], center)

    def positions(self):
        return np.array(self.p, dtype=np.float64).reshape(-1, 3)

    def compact(self):
        used = np.zeros(len(self.p), dtype=bool)
        for face in self.faces:
            for index in face:
                used[index] = True
        remap = -np.ones(len(self.p), dtype=np.int64)
        remap[used] = np.arange(int(used.sum()))
        keep = np.nonzero(used)[0]
        for name in ("p", "zone", "region", "s", "around", "flow", "fur", "w", "island", "pf"):
            values = getattr(self, name)
            setattr(self, name, [values[k] for k in keep])
        self.faces = [tuple(int(remap[i]) for i in face) for face in self.faces]
        self.seams = {(int(min(remap[a], remap[b])), int(max(remap[a], remap[b]))) for a, b in self.seams if remap[a] >= 0 and remap[b] >= 0}
        self.sharp = {(int(min(remap[a], remap[b])), int(max(remap[a], remap[b]))) for a, b in self.sharp if remap[a] >= 0 and remap[b] >= 0}
        self.marks ={key: [int(remap[i]) for i in value if remap[i] >= 0] for key, value in self.marks.items()}
        return remap

    def mirrored(self, eps=1e-7):
        full = Shell()
        count = len(self.p)
        twin = np.arange(count)
        for name in ("zone", "region", "s", "around", "fur", "island"):
            setattr(full, name, list(getattr(self, name)))
        full.p = [p.copy() for p in self.p]
        full.flow = [f.copy() for f in self.flow]
        full.w = [dict(w) for w in self.w]
        full.pf = [dict(f) for f in self.pf]
        for index in range(count):
            if abs(self.p[index][0]) <= eps:
                full.p[index][0] = 0.0
                full.flow[index][0] = 0.0
                merged = {}
                for bone, weight in self.w[index].items():
                    merged[bone] = merged.get(bone, 0.0) + weight * 0.5
                    other = mirror_name(bone)
                    merged[other] = merged.get(other, 0.0) + weight * 0.5
                full.w[index] = merged
            else:
                position = self.p[index] * np.array([-1.0, 1.0, 1.0])
                flow = self.flow[index] * np.array([-1.0, 1.0, 1.0])
                weights = {mirror_name(bone): weight for bone, weight in self.w[index].items()}
                twin[index] = full.add(position, self.zone[index], self.region[index], self.s[index], self.around[index], flow, self.fur[index], weights, self.island[index], self.pf[index])
        full.faces = list(self.faces)
        for face in self.faces:
            full.faces.append(tuple(int(twin[i]) for i in reversed(face)))
        full.seams = set(self.seams)
        for a, b in self.seams:
            full.seam(int(twin[a]), int(twin[b]))
        full.sharp = set(self.sharp)
        for a, b in self.sharp:
            full.crease(int(twin[a]), int(twin[b]))
        for key, value in self.marks.items():
            full.marks.setdefault(key, []).extend(value)
            full.marks.setdefault(mirror_name(key), []).extend(int(twin[i]) for i in value if mirror_name(key) != key or twin[i] != i)
        full.twin = np.concatenate([twin, np.arange(count)[twin != np.arange(count)]])
        return full


def mirror_name(name):
    if name.endswith("_l"):
        return name[:-2] + "_r"
    if name.endswith("_r"):
        return name[:-2] + "_l"
    return name
