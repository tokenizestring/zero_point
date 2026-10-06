import numpy
import anatomy
import bodies
import texels


def smoothstep(low, high, value):
    t = numpy.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def segment_distance(points, a, b):
    ab = b - a
    t = numpy.clip((points - a) @ ab / max(float(ab @ ab), 1e-12), 0.0, 1.0)
    closest = a + t[:, None] * ab
    return numpy.linalg.norm(points - closest, axis=1), t, closest


def finger_chain(skeleton, index, side):
    names = ["Bip01 %s Finger%d%s" % (side, index, suffix) for suffix in ("", "1", "2")]
    points = [numpy.asarray(skeleton["joints"][name]) for name in names]
    tip = points[-1] + numpy.asarray(skeleton["axes"][names[-1]][0]) * bodies.nubs["Finger%d" % index] * skeleton.get("finger_scale", 1.0)
    return names, points + [tip]


def nail_fields(shapes, points):
    weight = numpy.zeros(len(points))
    along = numpy.zeros(len(points))
    lateral = numpy.zeros(len(points))
    for item in shapes:
        if item.kind != "custom" or "nail" not in item.data:
            continue
        inside = numpy.flatnonzero(numpy.all((points >= item.low) & (points <= item.high), axis=1))
        if not len(inside):
            continue
        subset = points[inside]
        region, position, spread = bodies.nail_region(subset, item.data["nail"])
        value = smoothstep(0.00012, -0.00012, region) * (numpy.abs(item.distance(subset)) < 0.0015)
        better = value > weight[inside]
        weight[inside] = numpy.where(better, value, weight[inside])
        along[inside] = numpy.where(better, position, along[inside])
        lateral[inside] = numpy.where(better, spread, lateral[inside])
    return weight, along, lateral


def vein_field(shapes, points):
    field = numpy.zeros(len(points))
    for item in shapes:
        if item.kind != "ridge" or not item.data.get("vein"):
            continue
        low = item.low - 0.004
        high = item.high + 0.004
        inside = numpy.flatnonzero(numpy.all((points >= low) & (points <= high), axis=1))
        if not len(inside):
            continue
        subset = points[inside]
        best = numpy.full(len(subset), numpy.inf)
        path = item.data["points"]
        for index in range(len(path) - 1):
            distance, t, closest = segment_distance(subset, path[index], path[index + 1])
            best = numpy.minimum(best, distance)
        radius = max(item.data["radii"])
        field[inside] = numpy.maximum(field[inside], smoothstep(radius * 3.0, radius * 0.2, best))
    return field


def tones(points, normals, setup, nails, palette, veins=None, zones=None):
    skeleton = setup["skeleton"]
    joints = skeleton["joints"]
    axes = skeleton["axes"]
    count = len(points)
    figure = setup["figure"]["scale"]
    vary = palette.get("variation", 1.0)
    broad = texels.noise(points, 6.5, 5, 2) - 0.5
    mottle = smoothstep(0.34, 0.66, texels.noise(points, 21.0, 3, 3)) - 0.5
    blotch = smoothstep(0.32, 0.68, texels.noise(points, 58.0, 7, 3)) - 0.5
    patch = smoothstep(0.3, 0.7, texels.noise(points, 170.0, 13, 2)) - 0.5
    speckle = texels.noise(points, 850.0, 11, 2) - 0.5
    color = numpy.tile(numpy.array(palette["base"], dtype=numpy.float64), (count, 1))
    color = color * (1.0 + broad[:, None] * numpy.array([0.1, 0.02, -0.06]) * vary)
    color = color * (1.0 + mottle[:, None] * numpy.array([0.13, 0.085, 0.02]) * vary)
    color = color * (1.0 + blotch[:, None] * numpy.array([0.12, -0.07, -0.11]) * vary)
    color = color * (1.0 + patch[:, None] * numpy.array([0.07, 0.035, 0.015]) * vary)
    color = color * (1.0 + speckle[:, None] * 0.08)
    near, far, identity = texels.cells(points, 620.0, 19)
    pore = smoothstep(0.24, 0.07, near) * (0.4 + 0.6 * identity)
    color = color * (1.0 - pore[:, None] * numpy.array([0.04, 0.07, 0.075]))
    roughness = numpy.full(count, palette["roughness"]) + mottle * 0.08 + patch * 0.07 + speckle * 0.05
    detail = numpy.ones(count)
    redness = numpy.zeros(count)
    lighten = numpy.zeros(count)
    darken = numpy.zeros(count)
    hands = numpy.zeros(count)
    for side in ("L", "R"):
        wrist = joints["Bip01 %s Hand" % side]
        hand_axes = axes["Bip01 %s Hand" % side]
        q = points - wrist
        along = q @ hand_axes[0]
        near_hand = smoothstep(0.095, 0.08, numpy.linalg.norm(q - numpy.outer(along, hand_axes[0]), axis=1)) * smoothstep(-0.035, -0.012, along) * (along < 0.22)
        redness = numpy.maximum(redness, smoothstep(0.03, 0.18, along) * near_hand * 0.5)
        palm = near_hand * smoothstep(0.002, 0.011, q @ hand_axes[1]) * smoothstep(0.115, 0.095, along)
        best = numpy.full(count, numpy.inf)
        dorsal = numpy.zeros(count)
        knuckles = numpy.zeros(count)
        tips = numpy.zeros(count)
        for index in range(5):
            names, chain = finger_chain(skeleton, index, side)
            finger_best = numpy.full(count, numpy.inf)
            finger_dorsal = numpy.zeros(count)
            for segment in range(3):
                bone = axes[names[segment]]
                end = chain[segment + 1] if segment < 2 else chain[3] + (chain[3] - chain[2]) * 0.12
                distance, t, closest = segment_distance(points, chain[segment], end)
                closer = distance < finger_best
                finger_best = numpy.where(closer, distance, finger_best)
                finger_dorsal = numpy.where(closer, (points - closest) @ (-bone[1]), finger_dorsal)
            finger_knuckle = numpy.zeros(count)
            for segment in range(0 if index > 0 else 1, 3):
                joint_near = numpy.linalg.norm(points - chain[segment], axis=1)
                finger_knuckle = numpy.maximum(finger_knuckle, smoothstep(0.012, 0.004, joint_near))
            distance, t, closest = segment_distance(points, chain[2], chain[3] + (chain[3] - chain[2]) * 0.15)
            finger_tip = smoothstep(0.55, 1.05, t) * (distance < 0.014)
            closer = finger_best < best
            best = numpy.where(closer, finger_best, best)
            dorsal = numpy.where(closer, finger_dorsal, dorsal)
            knuckles = numpy.where(closer, finger_knuckle, knuckles)
            tips = numpy.where(closer, finger_tip, tips)
        on_finger = best < 0.016
        palmar_side = on_finger * smoothstep(0.001, -0.004, dorsal)
        dorsal_side = on_finger * smoothstep(-0.001, 0.005, dorsal)
        darken = numpy.maximum(darken, knuckles * dorsal_side * 0.25)
        redness = numpy.maximum(redness, knuckles * dorsal_side * 0.6)
        hands = numpy.maximum(hands, near_hand)
        redness = numpy.maximum(redness, tips * 0.8)
        lighten = numpy.maximum(lighten, numpy.maximum(palm, palmar_side))
        ankle = joints["Bip01 %s Foot" % side]
        toe = joints["Bip01 %s Toe0" % side]
        foot = (points[:, 2] < ankle[2] + 0.015) & (numpy.abs(points[:, 0] - ankle[0]) < 0.1)
        sole = foot * smoothstep(-0.1, -0.45, normals[:, 2])
        lighten = numpy.maximum(lighten, sole * 0.85)
        forward = anatomy.unit((toe - ankle) * numpy.array([1.0, 1.0, 0.0]))
        reach = (points - ankle) @ forward
        redness = numpy.maximum(redness, foot * (0.25 + 0.5 * smoothstep(0.09, 0.15, reach)))
        heel = foot & (reach < -0.02)
        redness = numpy.maximum(redness, heel * 0.4)
        knee = joints["Bip01 %s Calf" % side]
        knee_front = numpy.linalg.norm((points - (knee + numpy.array([0.0, -0.047, 0.012]) * figure)) / (numpy.array([0.055, 0.04, 0.07]) * figure), axis=1)
        redness = numpy.maximum(redness, smoothstep(1.0, 0.2, knee_front) * 0.7)
        darken = numpy.maximum(darken, smoothstep(1.0, 0.3, knee_front) * 0.45)
        elbow = joints["Bip01 %s Forearm" % side]
        elbow_back = numpy.linalg.norm((points - (elbow + numpy.array([0.0, 0.038, 0.0]) * figure)) / (numpy.array([0.04, 0.034, 0.04]) * figure), axis=1)
        darken = numpy.maximum(darken, smoothstep(1.0, 0.2, elbow_back) * 0.5)
        redness = numpy.maximum(redness, smoothstep(1.0, 0.2, elbow_back) * 0.7)
    shoulders = smoothstep(joints["Bip01 Spine2"][2], joints["Bip01 Neck"][2] - 0.02, points[:, 2]) * smoothstep(0.2, 0.7, normals[:, 2] + 0.25 * normals[:, 1])
    underside = smoothstep(-0.25, -0.7, normals[:, 2]) * (points[:, 2] > 0.3)
    color = color * (1.0 - shoulders[:, None] * numpy.array([0.02, 0.06, 0.09]))
    color = color * (1.0 + underside[:, None] * numpy.array([0.03, 0.04, 0.04]))
    sunny = numpy.clip(shoulders + 0.35 * smoothstep(joints["Bip01 Spine1"][2], joints["Bip01 Neck"][2], points[:, 2]), 0.0, 1.0)
    if zones is not None:
        sunny = numpy.clip(sunny + 0.5 * zones["forearm"] + 0.3 * zones["upper_arm"] + 0.2 * zones["shin"], 0.0, 1.0)
    flush = smoothstep(0.5, 1.0, sunny) * smoothstep(0.35, 0.7, texels.noise(points, 14.0, 25, 2))
    color = color * (1.0 + flush[:, None] * numpy.array([0.05, -0.04, -0.05]))
    near, far, identity = texels.cells(points, 240.0, 21)
    size = 0.14 + 0.2 * numpy.modf(identity * 977.0)[0]
    freckles = smoothstep(size, size * 0.5, near) * (identity < sunny * 0.5 * palette.get("freckles", 0.0)) * (0.4 + 0.6 * numpy.modf(identity * 3571.0)[0])
    near, far, identity = texels.cells(points, 95.0, 23)
    size = 0.07 + 0.11 * numpy.modf(identity * 1291.0)[0]
    spots = smoothstep(size, size * 0.45, near) * (identity < (0.05 + 0.28 * sunny) * palette.get("freckles", 0.0)) * (0.45 + 0.55 * numpy.modf(identity * 2713.0)[0]) * (1.0 - hands * 0.6)
    near, far, identity = texels.cells(points, 27.0, 29)
    size = 0.024 + 0.05 * numpy.modf(identity * 977.0)[0]
    moles = smoothstep(size, size * 0.6, near) * (identity < 0.04 * palette.get("moles", 0.0)) * (1.0 - hands)
    color = color * (1.0 - freckles[:, None] * numpy.array([0.15, 0.24, 0.3]))
    color = color * (1.0 - spots[:, None] * numpy.array([0.15, 0.24, 0.3]))
    color = color * (1.0 - moles[:, None] * numpy.array([0.5, 0.62, 0.68]))
    redness = numpy.clip(redness * (0.72 + 0.56 * texels.noise(points, 75.0, 27, 2)), 0.0, 1.0)
    color = color + (numpy.array(palette["red"]) - color) * redness[:, None] * 0.35
    color = color * (1.0 + redness[:, None] * numpy.array([0.04, -0.13, -0.1]))
    color = color + (numpy.array(palette["palm"]) - color) * lighten[:, None] * 0.6
    color = color * (1.0 - darken[:, None] * 0.2)
    vein = numpy.zeros(count) if veins is None else veins
    color = color * (1.0 - vein[:, None] * numpy.array([0.06, 0.03, -0.01]) * palette.get("veins", 1.0))
    nail_weight, nail_along, nail_lateral = nails
    lunula = smoothstep(1.0, 0.7, numpy.hypot(nail_along / 0.2, nail_lateral / 0.6))
    edge = smoothstep(0.88, 0.97, nail_along)
    sides = smoothstep(0.55, 1.0, nail_lateral)
    grit = smoothstep(0.78, 0.86, nail_along) * smoothstep(0.95, 0.88, nail_along)
    ridges = 0.5 + 0.5 * numpy.sin(nail_lateral * 38.0 + mottle * 6.0)
    plate = numpy.tile(numpy.array(palette["nail"], dtype=numpy.float64), (count, 1))
    plate = plate * (0.95 + 0.06 * ridges[:, None] + 0.08 * speckle[:, None])
    plate = plate + (numpy.array(palette["lunula"]) - plate) * lunula[:, None] * 0.45
    plate = plate + (numpy.array(palette["lunula"]) - plate) * sides[:, None] * 0.12
    plate = plate + (numpy.array(palette["edge"]) - plate) * edge[:, None] * 0.8
    plate = plate * (1.0 - grit[:, None] * numpy.array([0.4, 0.45, 0.5]) * palette.get("grit", 0.6))
    color = color + (plate - color) * nail_weight[:, None]
    roughness = roughness + lighten * 0.05 + darken * 0.06 + moles * 0.05 + redness * 0.02
    roughness = roughness + (0.34 + 0.12 * edge + 0.06 * ridges - roughness) * nail_weight
    detail = detail * (1.0 - nail_weight * 0.92) * (1.0 - lighten * 0.45)
    return numpy.clip(color, 0.0, 1.0), numpy.clip(roughness, 0.05, 1.0), numpy.clip(detail, 0.0, 1.0), nail_weight


def micro_height(points, detail, hair, fold=None, direction=None, pitch=None, texel=0.00045):
    coarse = max(1.0, texel / 0.00045)
    a, b, identity = texels.cells(points, 300.0 / coarse, 9)
    creases = -numpy.exp(-((b - a) / 0.17) ** 2) * 0.00004 * coarse
    a2, b2, identity2 = texels.cells(points, 120.0 / coarse, 13)
    folds = -numpy.exp(-((b2 - a2) / 0.09) ** 2) * 0.00004 * coarse
    a3, b3, identity3 = texels.cells(points, 520.0 / coarse, 15)
    pits = -smoothstep(0.3, 0.08, a3) * (0.3 + 0.7 * identity3) * 0.000026 * coarse
    uneven = (texels.noise(points, 90.0, 17, 3) - 0.5) * 0.00014
    broad = (texels.noise(points, 36.0, 15, 2) - 0.5) * 0.00034
    total = creases + folds + pits + uneven + broad
    if fold is not None and direction is not None:
        spacing = numpy.maximum(numpy.full(len(points), 0.0027) if pitch is None else pitch.astype(numpy.float64), 3.2 * texel)
        along = numpy.sum(points * direction.astype(numpy.float64), axis=1)
        warp = texels.noise(points, 55.0, 19, 2) * 9.0
        lines = (0.5 + 0.5 * numpy.sin(along / spacing * 2.0 * numpy.pi + warp)) ** 4
        broken = 0.35 + 0.65 * texels.noise(points, 240.0, 21, 2)
        total = total - lines * broken * fold.astype(numpy.float64) * spacing * 0.03
    return total * detail


def ellipsoid_mask(points, center, radii, power=1.0):
    q = (points - numpy.asarray(center)) / numpy.asarray(radii)
    return numpy.exp(-numpy.sum(q * q, axis=1) * power)


def regions(points, normals, setup, shapes=None):
    joints = setup["skeleton"]["joints"]
    s = setup["figure"]["scale"]
    result = {}
    count = len(points)
    fold = numpy.zeros(count)
    veined = numpy.zeros(count)
    forearm = numpy.zeros(count)
    shin = numpy.zeros(count)
    thigh = numpy.zeros(count)
    upper_arm = numpy.zeros(count)
    knee = numpy.zeros(count)
    elbow = numpy.zeros(count)
    armpit = numpy.zeros(count)
    fuzz = numpy.zeros(count)
    pitch = numpy.full(count, 0.0027 * s)
    direction = numpy.tile(numpy.array([0.0, 0.0, -1.0]), (count, 1))
    for side, flip in (("L", 1.0), ("R", -1.0)):
        shoulder = joints["Bip01 %s UpperArm" % side]
        bend = joints["Bip01 %s Forearm" % side]
        wrist = joints["Bip01 %s Hand" % side]
        distance, t, closest = segment_distance(points, bend, wrist)
        near = (distance < 0.062 * s) * smoothstep(0.02, 0.2, t) * smoothstep(1.04, 0.9, t)
        forearm = numpy.maximum(forearm, near)
        direction[near > 0.0] = anatomy.unit(wrist - bend)
        palmar = numpy.asarray(setup["skeleton"]["axes"]["Bip01 %s Hand" % side][1])
        dorsal = smoothstep(0.35, -0.2, normals @ palmar)
        reach = (points - bend) @ anatomy.unit(wrist - bend) / float(numpy.linalg.norm(wrist - bend))
        sleeve = (numpy.linalg.norm(points - wrist, axis=1) < 0.075 * s) * smoothstep(1.3, 1.02, reach) * smoothstep(0.95, 1.0, reach) * 0.45
        fuzz = numpy.maximum(fuzz, numpy.maximum(near, sleeve) * dorsal)
        direction[(sleeve > 0.0) & (near <= 0.0)] = anatomy.unit(wrist - bend)
        away = numpy.linalg.norm(points - wrist, axis=1)
        fold = numpy.maximum(fold, smoothstep(0.034 * s, 0.014 * s, away) * 0.8)
        reachable = numpy.flatnonzero(away < 0.24 * s)
        if len(reachable):
            digits = setup["skeleton"].get("finger_scale", 1.0)
            for index in range(5):
                names, chain = finger_chain(setup["skeleton"], index, side)
                for segment in range(0 if index > 0 else 1, 3):
                    crease = smoothstep(0.0125 * digits, 0.0045 * digits, numpy.linalg.norm(points[reachable] - chain[segment], axis=1))
                    stronger = crease > fold[reachable]
                    target = reachable[stronger]
                    fold[target] = crease[stronger]
                    direction[target] = anatomy.unit(chain[segment + 1] - chain[segment])
                    pitch[target] = 0.0017 * digits
        veined = numpy.maximum(veined, smoothstep(0.125 * s, 0.085 * s, away) * smoothstep(0.85, 1.05, reach) * dorsal)
        veined = numpy.maximum(veined, near * smoothstep(0.1, 0.6, normals @ palmar) * smoothstep(0.35, 0.8, t) * 0.8)
        distance, t, closest = segment_distance(points, shoulder, bend)
        near = (distance < 0.075 * s) * smoothstep(0.35, 0.8, t)
        upper_arm = numpy.maximum(upper_arm, near)
        direction[(near > 0.0) & (forearm <= 0.0)] = anatomy.unit(bend - shoulder)
        elbow = numpy.maximum(elbow, ellipsoid_mask(points, bend + numpy.array([0.0, 0.035, 0.0]) * s, numpy.array([0.035, 0.03, 0.035]) * s))
        hip = joints["Bip01 %s Thigh" % side]
        bend = joints["Bip01 %s Calf" % side]
        ankle = joints["Bip01 %s Foot" % side]
        distance, t, closest = segment_distance(points, bend, ankle)
        shin = numpy.maximum(shin, (distance < 0.085 * s) * smoothstep(0.03, 0.2, t) * smoothstep(1.0, 0.85, t))
        distance, t, closest = segment_distance(points, hip, bend)
        thigh = numpy.maximum(thigh, (distance < 0.12 * s) * smoothstep(0.15, 0.4, t) * smoothstep(1.02, 0.9, t))
        knee = numpy.maximum(knee, ellipsoid_mask(points, bend + numpy.array([0.0, -0.047, 0.012]) * s, numpy.array([0.045, 0.035, 0.055]) * s))
        pit = shoulder + numpy.array([-0.038 * flip, 0.002, -0.082]) * s
        armpit = numpy.maximum(armpit, ellipsoid_mask(points, pit, numpy.array([0.03, 0.045, 0.04]) * s))
        fold = numpy.maximum(fold, ellipsoid_mask(points, bend + numpy.array([0.0, 0.04, 0.0]) * s, numpy.array([0.04, 0.03, 0.05]) * s) * 0.7)
        veined = numpy.maximum(veined, (points[:, 2] < ankle[2] + 0.01 * s) * (numpy.abs(points[:, 0] - ankle[0]) < 0.09 * s) * smoothstep(0.2, 0.7, normals[:, 2]) * 0.9)
    pelvis = joints["Bip01 Pelvis"]
    spine = joints["Bip01 Spine"]
    chest_joint = joints["Bip01 Spine2"]
    armpit = armpit * smoothstep(0.8, 0.45, numpy.abs(normals[:, 1]))
    front = smoothstep(0.1, 0.5, -normals[:, 1])
    top = pelvis[2] + (0.004 if setup["name"] == "male" else -0.006) * s
    bottom = pelvis[2] - 0.088 * s
    t = numpy.clip((points[:, 2] - bottom) / (top - bottom), 0.0, 1.0)
    half = (0.012 + 0.046 * t ** 0.8) * s
    pubic = smoothstep(half, half * 0.5, numpy.abs(points[:, 0])) * smoothstep(bottom - 0.01 * s, bottom + 0.01 * s, points[:, 2]) * smoothstep(top + 0.012 * s, top - 0.014 * s, points[:, 2]) * (points[:, 1] < pelvis[1] - 0.02 * s)
    pubic = numpy.clip(pubic * (0.45 + 1.1 * texels.noise(points, 130.0, 77, 2)), 0.0, 1.0)
    trail = smoothstep(0.016 * s, 0.006 * s, numpy.abs(points[:, 0])) * smoothstep(top - 0.01 * s, top + 0.02 * s, points[:, 2]) * smoothstep(spine[2] + 0.085 * s, spine[2] + 0.04 * s, points[:, 2]) * front
    chest = ellipsoid_mask(points, chest_joint + numpy.array([0.0, -0.1, 0.035]) * s, numpy.array([0.1, 0.09, 0.075]) * s) * front
    result.update({"forearm": forearm, "forearm_hair": fuzz, "shin": shin, "thigh": thigh, "upper_arm": upper_arm, "knee": knee, "elbow": elbow, "armpit": armpit, "pubic": pubic, "trail": trail, "chest": chest, "direction": direction, "pitch": pitch})
    result["exposure"] = numpy.clip(normals[:, 2] * 0.85 + 0.15, 0.0, 1.0) * smoothstep(joints["Bip01 Spine1"][2], joints["Bip01 Spine2"][2] + 0.05 * s, points[:, 2])
    result["shorts"] = smoothstep(pelvis[2] - 0.2 * s, pelvis[2] - 0.14 * s, points[:, 2]) * smoothstep(pelvis[2] + 0.1 * s, pelvis[2] + 0.06 * s, points[:, 2])
    landmarks = setup["figure"].get("landmarks", {})
    result["top"] = numpy.zeros(count)
    if setup["name"] == "female" and "nipple_l" in landmarks:
        level = landmarks["nipple_l"][2]
        result["top"] = smoothstep(level - 0.1 * s, level - 0.06 * s, points[:, 2]) * smoothstep(level + 0.08 * s, level + 0.04 * s, points[:, 2]) * smoothstep(0.2 * s, 0.17 * s, numpy.abs(points[:, 0]))
    areola = numpy.zeros(count)
    tip = numpy.zeros(count)
    spec = setup["figure"].get("nipples")
    if spec:
        ragged = (texels.noise(points, 900.0, 5, 2) - 0.5) * spec["areola"] * 0.22
        for key in ("nipple_l", "nipple_r"):
            if key in landmarks:
                distance = numpy.linalg.norm(points - landmarks[key], axis=1)
                areola = numpy.maximum(areola, smoothstep(spec["areola"] * 1.04, spec["areola"] * 0.8, distance + ragged))
                tip = numpy.maximum(tip, smoothstep(spec["tip"] * 1.9, spec["tip"] * 0.9, distance))
    result["areola"] = areola
    result["nipple"] = tip
    neck = joints["Bip01 Neck"]
    collar = smoothstep(0.075 * s, 0.03 * s, numpy.linalg.norm(points - (neck + numpy.array([0.0, -0.02, 0.025]) * s), axis=1)) * smoothstep(0.3, -0.4, normals[:, 1])
    result["fold"] = numpy.clip(numpy.maximum(numpy.maximum(fold, numpy.maximum(elbow, knee) * 0.9), collar * 0.5), 0.0, 1.0)
    result["veined"] = numpy.clip(veined, 0.0, 1.0)
    intimate = numpy.zeros(count)
    if shapes is not None and "groin" in landmarks:
        center, radii = landmarks["groin"]
        near = numpy.flatnonzero(numpy.linalg.norm((points - center) / (numpy.asarray(radii) * 1.7), axis=1) < 1.0)
        if len(near):
            if "shaft" in setup["figure"]["groin"]:
                intimate[near] = smoothstep(0.0015, 0.007, bodies.protrusion(shapes, points[near]))
            else:
                intimate[near] = smoothstep(1.0, 0.35, numpy.linalg.norm((points[near] - center) / (numpy.asarray(radii) * numpy.array([0.6, 1.0, 1.0])), axis=1))
    result["intimate"] = intimate
    result["pubic"] = result["pubic"] * (1.0 - intimate if "shaft" in setup["figure"].get("groin", {}) else 1.0)
    return result


marks = {
    "male": {"scratches": [("forearm", 0.045), ("shin", 0.05), ("upper_arm", 0.03), ("thigh", 0.04), ("shin", 0.025), ("forearm", 0.02)], "bruises": [("shin", 0.02), ("thigh", 0.026), ("forearm", 0.014)], "stretch": 0.25},
    "female": {"scratches": [("forearm", 0.035), ("shin", 0.04), ("thigh", 0.03), ("shin", 0.02)], "bruises": [("shin", 0.018), ("thigh", 0.02)], "stretch": 0.7},
}

hair_layers = {
    "male": [
        {"zone": "forearm_hair", "count": 4600, "length": (0.007, 0.015), "opacity": (0.16, 0.42), "bend": 0.25, "tone": (0.075, 0.055, 0.042), "field": "limb"},
        {"zone": "shin", "count": 9000, "length": (0.007, 0.015), "opacity": (0.16, 0.42), "bend": 0.25, "tone": (0.075, 0.055, 0.042), "field": "limb"},
        {"zone": "thigh", "count": 4200, "length": (0.006, 0.012), "opacity": (0.1, 0.26), "bend": 0.25, "tone": (0.08, 0.058, 0.044), "field": "limb"},
        {"zone": "chest", "count": 2000, "length": (0.008, 0.017), "opacity": (0.14, 0.38), "bend": 0.5, "tone": (0.075, 0.055, 0.042), "field": "inward"},
        {"zone": "trail", "count": 600, "length": (0.006, 0.013), "opacity": (0.18, 0.42), "bend": 0.4, "tone": (0.075, 0.055, 0.042), "field": "down"},
        {"zone": "pubic", "count": 5200, "length": (0.006, 0.014), "opacity": (0.3, 0.7), "bend": 0.9, "tone": (0.09, 0.066, 0.05), "field": "inward"},
        {"zone": "armpit", "count": 2000, "length": (0.006, 0.013), "opacity": (0.35, 0.75), "bend": 0.8, "tone": (0.06, 0.044, 0.034), "field": "down"},
    ],
    "female": [
        {"zone": "pubic", "count": 4200, "length": (0.006, 0.013), "opacity": (0.3, 0.7), "bend": 0.9, "tone": (0.1, 0.072, 0.052), "field": "inward"},
        {"zone": "armpit", "count": 1500, "length": (0.0008, 0.002), "opacity": (0.25, 0.55), "bend": 0.2, "tone": (0.1, 0.075, 0.06), "field": "down"},
        {"zone": "forearm_hair", "count": 2600, "length": (0.004, 0.008), "opacity": (0.05, 0.14), "bend": 0.3, "tone": (0.55, 0.42, 0.3), "field": "limb"},
        {"zone": "shin", "count": 2600, "length": (0.001, 0.003), "opacity": (0.08, 0.2), "bend": 0.2, "tone": (0.2, 0.15, 0.11), "field": "limb"},
    ],
}


def weathering(points, normals, setup, color, roughness, ambient, zones, palette=None):
    name = setup["name"]
    joints = setup["skeleton"]["joints"]
    s = setup["figure"]["scale"]
    spec = marks[name]
    palette = palette or {}
    exposure = zones["exposure"]
    sun = palette.get("sun", 1.0)
    ragged = (texels.noise(points, 38.0, 45, 2) - 0.5) * 0.5
    color = color * (1.0 - exposure[:, None] * numpy.array([0.06, 0.095, 0.115]) * sun)
    pale = numpy.clip(numpy.maximum(zones["shorts"], zones.get("top", 0.0)) * (1.0 + ragged), 0.0, 1.0)
    color = color * (1.0 + pale[:, None] * numpy.array([0.055, 0.08, 0.095]) * sun)
    sheltered = smoothstep(0.25, -0.35, normals[:, 2]) * numpy.maximum(zones["forearm"], zones["upper_arm"])
    below = smoothstep(joints["Bip01 Pelvis"][2] - 0.085 * s, joints["Bip01 Pelvis"][2] - 0.14 * s, points[:, 2])
    sheltered = numpy.maximum(sheltered, zones["thigh"] * below * smoothstep(0.075 * s, 0.02 * s, numpy.abs(points[:, 0]) - 0.02 * s) * 0.8)
    color = color * (1.0 + sheltered[:, None] * numpy.array([0.04, 0.055, 0.065]))
    warped = points + (numpy.stack([texels.noise(points, 35.0, 41 + k, 2) for k in range(3)], axis=1) - 0.5) * 0.02
    near, far, identity = texels.cells(warped, 46.0, 37)
    network = smoothstep(0.1, 0.02, far - near) * (0.35 + 0.65 * texels.noise(points, 30.0, 43, 2))
    veined = numpy.clip(numpy.maximum(sheltered * 1.2, zones.get("veined", 0.0)), 0.0, 1.0) * palette.get("veins", 1.0)
    color = color * (1.0 - (network * veined)[:, None] * numpy.array([0.17, 0.08, 0.0]))
    inner = smoothstep(0.35, 0.9, 1.0 - ambient)
    dirt = numpy.array([0.5, 0.42, 0.34])
    grime = inner * (0.35 + 0.65 * texels.noise(points, 140.0, 61, 3))
    color = color * (1.0 - grime[:, None] * (1.0 - dirt) * 0.3)
    outdoors = numpy.clip(zones["forearm"] * 0.85 + zones["upper_arm"] * 0.4 + zones["shin"] * 0.5 + zones["thigh"] * (1.0 - zones["shorts"]) * 0.3, 0.0, 1.0) * (0.6 + 0.4 * texels.noise(points, 12.0, 63, 2)) * smoothstep(-0.75, -0.1, normals[:, 2])
    color = color * (1.0 - outdoors[:, None] * numpy.array([0.055, 0.09, 0.11]) * sun)
    ground = smoothstep(0.16 * s, 0.02 * s, points[:, 2])
    limbs = numpy.maximum(zones["shin"] * 0.45, numpy.maximum(zones["knee"] * 0.7, numpy.maximum(zones["elbow"] * 0.6, zones["forearm"] * 0.3)))
    cloud = smoothstep(0.42, 0.72, texels.noise(points, 26.0, 67, 3)) * (0.55 + 0.45 * texels.noise(points, 300.0, 69, 2))
    soil = numpy.clip(numpy.maximum(ground * (0.55 + 0.45 * cloud), limbs * cloud), 0.0, 1.0) * palette.get("dirt", 0.6)
    earth = numpy.asarray(palette.get("earth", (0.15, 0.11, 0.08)))
    color = color * (1.0 - soil[:, None] * 0.68) + earth[None, :] * (soil[:, None] * 0.68)
    bone = numpy.maximum(zones["knee"], zones["elbow"])
    color = color * (1.0 + bone[:, None] * numpy.array([0.0, -0.03, -0.06]))
    roughness = roughness + bone * 0.08 + grime * 0.08 - exposure * 0.03 + soil * 0.14
    pelvis = joints["Bip01 Pelvis"]
    hips = smoothstep(0.07 * s, 0.13 * s, numpy.abs(points[:, 0])) * smoothstep(pelvis[2] - 0.2 * s, pelvis[2] - 0.08 * s, points[:, 2]) * smoothstep(pelvis[2] + 0.12 * s, pelvis[2] + 0.02 * s, points[:, 2])
    streak = texels.noise(points * numpy.array([60.0, 60.0, 900.0]), 1.0, 91, 2)
    lines = smoothstep(0.62, 0.72, streak) * hips * spec["stretch"]
    color = color * (1.0 + lines[:, None] * numpy.array([0.06, 0.07, 0.08]))
    roughness = roughness - lines * 0.05
    return numpy.clip(color, 0.0, 1.0), numpy.clip(roughness, 0.05, 1.0), lines


def pigment(color, roughness, zones, palette):
    dark = numpy.asarray(palette.get("areola", (0.6, 0.45, 0.44)))
    tipped = numpy.asarray(palette.get("nipple", (0.85, 0.78, 0.78)))
    color = color * (1.0 + (dark[None, :] - 1.0) * zones["areola"][:, None])
    color = color * (1.0 + (tipped[None, :] - 1.0) * zones["nipple"][:, None])
    fold = numpy.asarray(palette.get("fold", (0.88, 0.82, 0.8)))
    shade = numpy.clip(zones["pubic"] * 0.7 + zones["armpit"] * 0.8, 0.0, 1.0)
    color = color * (1.0 + (fold[None, :] - 1.0) * shade[:, None])
    roughness = roughness + 0.04 * zones["areola"]
    intimate = zones.get("intimate")
    if intimate is not None:
        color = color * (1.0 + (numpy.array([0.9, 0.78, 0.76])[None, :] - 1.0) * intimate[:, None])
        roughness = roughness + 0.03 * intimate
    return color, roughness


