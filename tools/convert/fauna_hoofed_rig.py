import math
import numpy
import fauna_hoofed_field as fields

smooth = fields.smoothstep


def quadruped(k, tail, extra=()):
    bones = [("root", None, (0.0, 0.0, 0.0))]

    def add(name, parent, position):
        bones.append((name, parent, tuple(float(v) for v in position)))

    def pair(name, parent, position, sided_parent=True):
        for suffix, sign in (("_l", 1.0), ("_r", -1.0)):
            add(name + suffix, parent + suffix if sided_parent else parent, (position[0] * sign, position[1], position[2]))

    add("hips", "root", k["hips"])
    add("spine_01", "hips", k["spine_01"])
    add("spine_02", "spine_01", k["spine_02"])
    add("spine_03", "spine_02", k["spine_03"])
    add("neck_01", "spine_03", k["neck_01"])
    add("neck_02", "neck_01", k["neck_01"] + (k["skull"] - k["neck_01"]) * 0.36)
    add("neck_03", "neck_02", k["neck_01"] + (k["skull"] - k["neck_01"]) * 0.7)
    add("head", "neck_03", k["skull"])
    add("jaw", "head", (0.0, k["jaw"][1], k["jaw"][2]))
    pair("ear", "head", k["ear_root"], False)
    for name, parent, position in extra:
        if parent == "head":
            add(name, parent, position)
    for suffix, sign in (("_l", 1.0), ("_r", -1.0)):
        flipped = numpy.array([sign, 1.0, 1.0])
        add("scapula" + suffix, "spine_03", k["scapula"] * flipped)
        add("humerus" + suffix, "scapula" + suffix, k["shoulder"] * flipped)
        add("radius" + suffix, "humerus" + suffix, k["elbow"] * flipped)
        add("cannon" + suffix, "radius" + suffix, k["carpus"] * flipped)
        add("pastern_f" + suffix, "cannon" + suffix, k["fetlock_f"] * flipped)
        add("hoof_f" + suffix, "pastern_f" + suffix, k["coffin_f"] * flipped)
    pair("ribs", "spine_02", k["ribs"], False)
    for name, parent, position in extra:
        if parent != "head":
            add(name, parent, position)
    for suffix, sign in (("_l", 1.0), ("_r", -1.0)):
        flipped = numpy.array([sign, 1.0, 1.0])
        add("femur" + suffix, "hips", k["hip"] * flipped)
        add("tibia" + suffix, "femur" + suffix, k["stifle"] * flipped)
        add("metatarsus" + suffix, "tibia" + suffix, k["hock"] * flipped)
        add("pastern_h" + suffix, "metatarsus" + suffix, k["fetlock_h"] * flipped)
        add("hoof_h" + suffix, "pastern_h" + suffix, k["coffin_h"] * flipped)
    previous = "hips"
    for index, point in enumerate(tail):
        add("tail_%02d" % (index + 1), previous, point)
        previous = "tail_%02d" % (index + 1)
    return bones


def project(points, joints):
    joints = numpy.asarray(joints, dtype=numpy.float64)
    best = numpy.full(len(points), numpy.inf)
    travel = numpy.zeros(len(points))
    start = 0.0
    for index in range(len(joints) - 1):
        a = joints[index]
        ab = joints[index + 1] - a
        length = float(numpy.linalg.norm(ab))
        t = numpy.clip(((points - a) @ ab) / max(length * length, 1e-12), 0.0, 1.0)
        d = numpy.linalg.norm(points - a - t[:, None] * ab, axis=1)
        closer = d < best
        best = numpy.where(closer, d, best)
        travel = numpy.where(closer, start + t * length, travel)
        start += length
    return travel, best


def chain(points, joints, widths):
    joints = numpy.asarray(joints, dtype=numpy.float64)
    travel, distance = project(points, joints)
    marks = numpy.r_[0.0, numpy.cumsum(numpy.linalg.norm(numpy.diff(joints, axis=0), axis=1))]
    count = len(joints) - 1
    steps = [numpy.ones(len(points))] + [smooth(marks[i] - widths[i] * 0.5, marks[i] + widths[i] * 0.5, travel) for i in range(1, count)] + [numpy.zeros(len(points))]
    return numpy.column_stack([steps[i] - steps[i + 1] for i in range(count)]), travel, distance


def weights(model, blueprint):
    names = [bone[0] for bone in blueprint["bones"]]
    slot = {name: index for index, name in enumerate(names)}
    joint = {bone[0]: numpy.array(bone[2]) for bone in blueprint["bones"]}
    rig = blueprint["rig"]
    k = blueprint["marks"]
    points = model["points"] / model["scale"]
    count = len(points)
    part = numpy.array(model["part"])
    coord = model["coord"]
    meta = model["meta"]
    mapping = model["mapping"]
    result = numpy.zeros((count, len(names)))

    axial = rig["axial"]
    centers = meta["centers"]
    ring_points = numpy.column_stack([numpy.zeros(len(centers)), centers[:, 0], centers[:, 1]])
    ring_weights, ring_travel, ring_distance = chain(ring_points, [joint[name] for name in axial] + [k["nose"]], rig["axial_widths"])
    tube = numpy.isin(part, ["body", "head", "lip"])
    ring = numpy.clip(numpy.rint(coord[:, 0]).astype(numpy.int64), 0, len(centers) - 1)
    for index, name in enumerate(axial):
        result[tube, slot[name]] = ring_weights[ring[tube], index]
    result[part == "rump", slot["hips"]] = 1.0
    for label in ("nose", "eye", "nostril", "mouth_upper", "mouth_lower", "mouth"):
        result[part == label, slot["head"]] = 1.0

    head = numpy.isin(part, ["head", "lip", "nose", "nostril", "mouth_upper", "mouth_lower", "mouth"])
    along = (points - k["nose"][None, :]) @ k["head_axis"]
    height = (points - k["nose"][None, :]) @ k["head_up"]
    corner = float((k["mouth"] - k["nose"]) @ k["head_axis"])
    corner_height = float((k["mouth"] - k["nose"]) @ k["head_up"])
    hinge = float((k["jaw"] - k["nose"]) @ k["head_axis"])
    hinge_height = float((k["jaw"] - k["nose"]) @ k["head_up"])
    line = corner_height + (hinge_height - corner_height) * numpy.clip((along - corner) / (hinge - corner), 0.0, 1.0)
    jaw = smooth(-0.004, -0.04, height - line) * smooth(hinge + 0.01, hinge - 0.09, along) * head
    below = numpy.zeros(count, dtype=bool)
    ids = numpy.array(meta["below"], dtype=numpy.int64)
    below[ids] = True
    below[mapping[ids]] = True
    jaw = numpy.where(below | (part == "mouth_lower") | (part == "lip"), 1.0, jaw)
    jaw = numpy.where(part == "mouth_upper", 0.0, jaw)
    jaw = numpy.where(part == "mouth", 0.5, jaw)
    shared = numpy.array([meta["lip_upper"][0], mapping[meta["lip_upper"][0]]])
    jaw[shared] = 0.5
    upper = numpy.array(meta["lip_upper"][1:], dtype=numpy.int64)
    jaw[upper] = 0.0
    jaw[mapping[upper]] = 0.0
    result *= (1.0 - jaw)[:, None]
    result[:, slot["jaw"]] += jaw

    for suffix, sign in (("_l", 1.0), ("_r", -1.0)):
        flipped = numpy.array([sign, 1.0, 1.0])
        local = points * flipped[None, :]
        here = numpy.sign(points[:, 0]) == sign
        ear = (part == "ear") & here
        level = coord[:, 0]
        amount = numpy.where(ear, smooth(-0.5, 2.5, level), 0.0)
        near = smooth(0.06, 0.02, numpy.linalg.norm(local - k["ear_root"][None, :], axis=1)) * 0.35 * here * numpy.isin(part, ["head"])
        amount = numpy.maximum(amount, near)
        result *= (1.0 - amount)[:, None]
        result[:, slot["ear" + suffix]] += amount
        result[ear, slot["head"]] += (1.0 - amount)[ear] * (result[ear].sum(axis=1) < 0.999)

        for limb in rig["limbs"]:
            bones = [name + suffix for name in limb["bones"]]
            joints = [joint[name + "_l"] for name in limb["bones"]] + [numpy.asarray(limb["tip"])]
            limb_weights, travel, distance = chain(local, joints, limb["widths"])
            marks = numpy.r_[0.0, numpy.cumsum(numpy.linalg.norm(numpy.diff(numpy.array(joints), axis=0), axis=1))]
            radius = numpy.interp(travel, marks[:len(limb["reach"])], limb["reach"])
            strength = numpy.interp(travel, marks[:len(limb["grip"])], limb["grip"])
            body = numpy.isin(part, ["body", "rump"]) & here
            pull = strength * smooth(1.0, 0.35, distance / radius) * smooth(0.015, 0.07, numpy.abs(points[:, 0])) * body
            leg = (part == limb["name"]) & here
            ramp = smooth(-1.5, 2.0, level)
            pull = numpy.where(leg, numpy.maximum(strength * smooth(1.0, 0.35, distance / radius), ramp), pull)
            result *= (1.0 - pull)[:, None]
            for index, name in enumerate(bones):
                result[:, slot[name]] += pull * limb_weights[:, index]

        region = rig["ribs"]
        q = (local - numpy.asarray(region["center"])[None, :]) / numpy.asarray(region["radii"])[None, :]
        swell = numpy.clip(1.0 - numpy.sum(q * q, axis=1), 0.0, 1.0) ** 2 * region["amount"] * (part == "body") * here
        result *= (1.0 - swell)[:, None]
        result[:, slot["ribs" + suffix]] += swell

    tail_names = rig["tail"]
    tail_joints = [joint[name] for name in tail_names] + [numpy.asarray(rig["tail_tip"])]
    tail_weights, travel, distance = chain(points, tail_joints, rig["tail_widths"])
    tail = part == "tail"
    grip = numpy.where(tail, smooth(-0.8, 1.2, coord[:, 0]), smooth(0.07, 0.02, distance) * 0.5 * (part == "rump"))
    result *= (1.0 - grip)[:, None]
    for index, name in enumerate(tail_names):
        result[:, slot[name]] += grip * tail_weights[:, index]
    result[tail, slot["hips"]] += (1.0 - grip)[tail] * (result[tail].sum(axis=1) < 0.999)

    for index in range(count):
        bone = model["bone"][index]
        if bone is not None:
            result[index] = 0.0
            result[index, slot[bone]] = 1.0
    for extra in rig.get("extra", ()):
        result = extra(result, slot, points, part, coord, model)
    total = result.sum(axis=1)
    if (total < 1e-6).any():
        missing = numpy.flatnonzero(total < 1e-6)
        print("RIG unweighted vertices", len(missing), sorted(set(part[missing])))
        result[missing, slot["root"]] = 1.0
    order = numpy.argsort(-result, axis=1)[:, :4]
    kept = numpy.take_along_axis(result, order, axis=1)
    kept[kept < 0.004] = 0.0
    kept /= kept.sum(axis=1)[:, None]
    return names, order, kept


def dense(order, kept, count):
    result = numpy.zeros((len(order), count))
    numpy.put_along_axis(result, order, kept, axis=1)
    return result
