import math
import numpy

lateral = numpy.array([1.0, 0.0, 0.0])
identity = numpy.eye(3)


def unit(vector):
    return vector / max(float(numpy.linalg.norm(vector)), 1e-12)


def rx(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return numpy.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def ry(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return numpy.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rz(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return numpy.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def turn(pitch=0.0, yaw=0.0, roll=0.0):
    return rz(math.radians(yaw)) @ rx(-math.radians(pitch)) @ ry(math.radians(roll))


def axis_angle(matrix):
    angle = math.acos(max(-1.0, min(1.0, (float(numpy.trace(matrix)) - 1.0) * 0.5)))
    if angle < 1e-9:
        return numpy.zeros(3)
    axis = numpy.array([matrix[2, 1] - matrix[1, 2], matrix[0, 2] - matrix[2, 0], matrix[1, 0] - matrix[0, 1]])
    return unit(axis) * angle


def from_vector(vector):
    angle = float(numpy.linalg.norm(vector))
    if angle < 1e-12:
        return numpy.eye(3)
    x, y, z = vector / angle
    c = math.cos(angle)
    s = math.sin(angle)
    return numpy.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s], [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s], [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def quaternion(matrix):
    m = matrix
    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        q = numpy.array([0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s])
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        q = numpy.array([(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s])
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        q = numpy.array([(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s])
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        q = numpy.array([(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s])
    return q / numpy.linalg.norm(q)


def matrix_of(q):
    w, x, y, z = q
    return numpy.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def slerp(a, b, t):
    dot = float(a @ b)
    if dot < 0.0:
        b = -b
        dot = -dot
    if dot > 0.9995:
        q = a + (b - a) * t
        return q / numpy.linalg.norm(q)
    angle = math.acos(dot)
    return (math.sin((1.0 - t) * angle) * a + math.sin(t * angle) * b) / math.sin(angle)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoother(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def pulse(time, start, length):
    t = (time - start) / length
    return math.sin(math.pi * t) ** 2 if 0.0 < t < 1.0 else 0.0


def wave(time, period, offset=0.0):
    return math.sin(2.0 * math.pi * (time / period - offset))


def frame_of(direction, side):
    y = unit(direction)
    x = unit(side - y * float(side @ y))
    return numpy.column_stack([x, y, numpy.cross(x, y)])


def aim(rest, posed, side, rest_side=lateral):
    return frame_of(posed, side) @ frame_of(rest, rest_side).T


def two_bone(root, target, first, second, normal, side):
    span = target - root
    distance = float(numpy.linalg.norm(span))
    reach = min(max(distance, abs(first - second) + 1e-5), first + second - 1e-6)
    along = span / max(distance, 1e-9)
    a = (first * first - second * second + reach * reach) / (2.0 * reach)
    h = math.sqrt(max(first * first - a * a, 0.0))
    return root + along * a + numpy.cross(normal, along) * (h * side)


def reach_of(first, second, bend):
    return math.sqrt(max(first * first + second * second + 2.0 * first * second * math.cos(bend), 0.0))


class limb:
    def __init__(self, rig, names, suffix, root, fold, unit_side, toe, heel):
        self.names = [name + suffix for name in names]
        self.rig = rig
        self.root = root
        self.fold = fold
        self.unit_side = unit_side
        rest = [rig.rest[rig.slot[name]] for name in self.names]
        self.rest = rest
        self.vectors = [rest[i + 1] - rest[i] for i in range(len(rest) - 1)]
        self.lengths = [float(numpy.linalg.norm(v)) for v in self.vectors]
        self.toe = toe - rest[-1]
        self.heel = heel - rest[-1]
        self.sign = 1.0 if suffix == "_l" else -1.0
        upper = rest[-4]
        middle = rest[-3]
        lower = rest[-2]
        normal = self.plane(rest[-5], lower)
        self.normal = normal
        back = numpy.cross(normal, unit(lower - upper))
        angle = math.acos(max(-1.0, min(1.0, float(unit(middle - upper) @ unit(lower - middle)))))
        self.bend = angle * (1.0 if float((middle - upper) @ back) * unit_side >= 0.0 else -1.0)
        self.lean = math.atan2(-(lower[1] - rest[0][1]), rest[0][2] - lower[2])

    def plane(self, top, bottom):
        along = unit(bottom - top)
        return unit(lateral - along * float(lateral @ along))


class rig:
    def __init__(self, blueprint, scale=None):
        self.scale = blueprint["scale"] if scale is None else scale
        bones = blueprint["bones"]
        self.names = [bone[0] for bone in bones]
        self.slot = {name: index for index, name in enumerate(self.names)}
        self.parent = [self.slot[bone[1]] if bone[1] is not None else -1 for bone in bones]
        self.rest = numpy.array([bone[2] for bone in bones], dtype=numpy.float64) * self.scale
        self.offset = numpy.array([self.rest[i] - (self.rest[p] if p >= 0 else 0.0) for i, p in enumerate(self.parent)])
        marks = blueprint["marks"]
        hoof = blueprint["hoof"]
        self.limbs = {}
        for suffix, sign in (("_l", 1.0), ("_r", -1.0)):
            flipped = numpy.array([sign, 1.0, 1.0]) * self.scale
            toe = marks["toe_f"] * flipped
            self.limbs["fore" + suffix] = limb(self, ["scapula", "humerus", "radius", "cannon", "pastern_f", "hoof_f"], suffix, "spine_03", 1.0, -1.0, toe, toe + numpy.array([0.0, hoof["length"] * self.scale, 0.0]))
            toe = marks["toe_h"] * flipped
            self.limbs["hind" + suffix] = limb(self, ["femur", "tibia", "metatarsus", "pastern_h", "hoof_h"], suffix, "hips", -1.0, 1.0, toe, toe + numpy.array([0.0, hoof["length"] * self.scale, 0.0]))
        self.tail = [name for name in self.names if name.startswith("tail_")]

    def blank(self):
        return {"rotation": {}, "location": {}, "feet": {}, "free": {}}

    def solve(self, controls):
        count = len(self.names)
        local = numpy.tile(numpy.eye(3), (count, 1, 1))
        shift = numpy.zeros((count, 3))
        for name, matrix in controls["rotation"].items():
            local[self.slot[name]] = matrix
        for name, vector in controls["location"].items():
            shift[self.slot[name]] = numpy.asarray(vector, dtype=numpy.float64)
        world = numpy.tile(numpy.eye(3), (count, 1, 1))
        place = numpy.zeros((count, 3))
        solved = numpy.zeros(count, dtype=bool)
        info = {"short": {}}

        def forward(index):
            parent = self.parent[index]
            if parent < 0:
                world[index] = local[index]
                place[index] = self.offset[index] + shift[index]
            else:
                world[index] = world[parent] @ local[index]
                place[index] = place[parent] + world[parent] @ (self.offset[index] + shift[index])
            solved[index] = True

        chains = {}
        for key, leg in self.limbs.items():
            for name in leg.names:
                chains[self.slot[name]] = key
        done = set()
        for index in range(count):
            key = chains.get(index)
            if key is None:
                forward(index)
                continue
            if key in done:
                continue
            done.add(key)
            leg = self.limbs[key]
            slots = [self.slot[name] for name in leg.names]
            if key in controls["feet"]:
                self.plant(leg, slots, controls["feet"][key], world, place, local, info)
            else:
                angles = controls["free"].get(key, {})
                for order, slot in enumerate(slots):
                    local[slot] = angles.get(order, numpy.eye(3))
                    forward(slot)
        return local, shift, world, place, info

    def plant(self, leg, slots, foot, world, place, local, info):
        parent = self.parent[slots[0]]
        top = place[parent] + world[parent] @ self.offset[slots[0]]
        hoof = rx(foot.get("pitch", 0.0))
        pastern = rx(foot.get("pastern", 0.0)) @ leg.vectors[-1]
        ankle = numpy.asarray(foot["position"], dtype=numpy.float64) - pastern
        vectors = leg.vectors
        lengths = leg.lengths
        if len(slots) == 6:
            swing = foot.get("swing", 0.0) + foot.get("follow", 0.0) * (math.atan2(-(ankle[1] - top[1]), max(top[2] - ankle[2], 1e-6)) - leg.lean)
            blade = world[parent] @ rx(-swing) @ vectors[0]
            start = top + blade
            rotations = [aim(vectors[0], blade, world[parent] @ lateral)]
            first = 1
        else:
            start = top
            rotations = []
            first = 0
        upper = lengths[first]
        middle = lengths[first + 1]
        lower = lengths[first + 2]
        distance = float(numpy.linalg.norm(ankle - start))
        bend = leg.bend + foot.get("flex", 0.0)
        floor = foot.get("straight", 0.02)
        if upper * 0.999 + reach_of(middle, lower, bend) < distance:
            needed = min(max(distance - upper * 0.999, abs(middle - lower)), middle + lower)
            cosine = (needed * needed - middle * middle - lower * lower) / (2.0 * middle * lower)
            bend = max(math.acos(max(-1.0, min(1.0, cosine))), floor) * (1.0 if bend >= 0.0 else -1.0)
            bend = bend if abs(bend) < abs(leg.bend + foot.get("flex", 0.0)) else leg.bend + foot.get("flex", 0.0)
        span = reach_of(middle, lower, bend)
        info["short"][leg.names[-1]] = max(distance - (upper + span - 1e-6), 0.0)
        normal = leg.plane(start, ankle)
        knee = two_bone(start, ankle, upper, span, normal, leg.fold)
        target = ankle if distance <= upper + span else knee + unit(ankle - knee) * span
        joint = two_bone(knee, target, middle, lower, normal, leg.unit_side * (1.0 if bend >= 0.0 else -1.0))
        rotations.append(aim(vectors[first], knee - start, normal, leg.normal))
        rotations.append(aim(vectors[first + 1], joint - knee, normal, leg.normal))
        rotations.append(aim(vectors[first + 2], target - joint, normal, leg.normal))
        rotations.append(aim(vectors[first + 3], pastern, normal, leg.normal))
        rotations.append(hoof)
        above = world[parent]
        position = top
        for order, slot in enumerate(slots):
            local[slot] = above.T @ rotations[order]
            world[slot] = rotations[order]
            place[slot] = position
            if order < len(slots) - 1:
                position = position + rotations[order] @ vectors[order]
            above = rotations[order]

    def points(self, key, world, place):
        leg = self.limbs[key]
        slot = self.slot[leg.names[-1]]
        return place[slot] + world[slot] @ leg.toe, place[slot] + world[slot] @ leg.heel
