import math
import numpy
import fauna_ambient_kit as kit
import fauna_hoofed_coats as coats
import fauna_hoofed_field as fields
import fauna_hoofed_paint as paint

unit = fields.unit
smooth = fields.smoothstep
tint = coats.tint
upper_chord = (0.0, 0.03, 0.1, 0.22, 0.4, 0.62, 0.82, 1.0)
lower_chord = (0.8, 0.55, 0.3, 0.12, 0.035)


def thickness(c):
    c = max(c, 0.0)
    return 1.12 * (2.969 * math.sqrt(c) - 1.26 * c - 3.516 * c * c + 2.843 * c ** 3 - 1.036 * c ** 4) / 1.0


def build(kind):
    if kind == "gull":
        return {
            "name": "bird_gull",
            "kind": kind,
            "budget": (1500, 4000),
            "body": [(-0.15, 0.006, 0.022, 0.015, 0.017, 2.0, 2.0), (-0.125, 0.004, 0.036, 0.027, 0.028, 2.0, 2.0), (-0.08, 0.002, 0.05, 0.04, 0.043, 2.1, 2.1), (-0.03, 0.0, 0.056, 0.047, 0.05, 2.2, 2.2), (0.02, 0.0, 0.056, 0.047, 0.049, 2.2, 2.2), (0.07, 0.003, 0.05, 0.043, 0.042, 2.1, 2.1), (0.11, 0.008, 0.04, 0.036, 0.032, 2.0, 2.0), (0.14, 0.013, 0.032, 0.031, 0.026, 2.0, 2.0), (0.165, 0.017, 0.029, 0.03, 0.024, 2.0, 2.0), (0.185, 0.019, 0.028, 0.029, 0.023, 2.0, 2.0), (0.203, 0.018, 0.021, 0.022, 0.019, 2.0, 2.0), (0.218, 0.015, 0.011, 0.012, 0.014, 2.0, 2.0), (0.235, 0.012, 0.008, 0.009, 0.0105, 2.0, 2.0), (0.252, 0.0105, 0.0065, 0.0075, 0.0098, 2.0, 2.0), (0.265, 0.0085, 0.0048, 0.0065, 0.0065, 2.0, 2.0), (0.273, 0.005, 0.0032, 0.005, 0.004, 2.0, 2.0)],
            "rings": [-0.15, -0.138, -0.125, -0.103, -0.08, -0.055, -0.03, -0.005, 0.02, 0.045, 0.07, 0.09, 0.11, 0.125, 0.14, 0.153, 0.165, 0.175, 0.185, 0.194, 0.203, 0.211, 0.218, 0.226, 0.235, 0.244, 0.252, 0.259, 0.265, 0.27, 0.273],
            "tips": ((0.0, -0.156, 0.006), (0.0, 0.279, 0.0015)),
            "around": 18,
            "head": 0.13,
            "bill": 0.214,
            "eye": ((0.0232, 0.188, 0.0305), (0.85, 0.38, 0.3), 0.006),
            "wing": [(0.035, 0.04, -0.1, 0.016, 0.022), (0.07, 0.045, -0.112, 0.018, 0.02), (0.12, 0.055, -0.118, 0.022, 0.018), (0.18, 0.068, -0.12, 0.027, 0.016), (0.24, 0.08, -0.118, 0.031, 0.015), (0.3, 0.092, -0.11, 0.034, 0.014), (0.34, 0.098, -0.1, 0.035, 0.013), (0.38, 0.094, -0.092, 0.034, 0.011), (0.44, 0.07, -0.09, 0.03, 0.009), (0.5, 0.042, -0.09, 0.024, 0.008), (0.56, 0.012, -0.092, 0.018, 0.006), (0.61, -0.02, -0.095, 0.012, 0.005), (0.655, -0.052, -0.1, 0.007, 0.004), (0.688, -0.08, -0.106, 0.004, 0.003), (0.703, -0.098, -0.11, 0.002, 0.0025)],
            "tip": (0.708, -0.112, 0.002),
            "wrist": 0.34,
            "tail": {"base": ((-0.024, -0.125, 0.006), (0.024, -0.125, 0.006)), "tips": [(x, -0.295 + 0.008 * (x / 0.065) ** 2, 0.002) for x in numpy.linspace(-0.065, 0.065, 11)], "thick": 0.007, "rows": 5},
            "fingers": [],
        }
    return {
        "name": "bird_crow",
        "kind": kind,
        "budget": (1500, 4000),
        "body": [(-0.115, 0.006, 0.02, 0.014, 0.015, 2.0, 2.0), (-0.095, 0.004, 0.032, 0.025, 0.025, 2.0, 2.0), (-0.06, 0.002, 0.043, 0.037, 0.039, 2.1, 2.1), (-0.02, 0.0, 0.048, 0.043, 0.046, 2.2, 2.2), (0.025, 0.001, 0.048, 0.043, 0.045, 2.2, 2.2), (0.065, 0.005, 0.042, 0.038, 0.036, 2.1, 2.1), (0.095, 0.01, 0.033, 0.031, 0.027, 2.0, 2.0), (0.12, 0.014, 0.028, 0.028, 0.023, 2.0, 2.0), (0.14, 0.017, 0.026, 0.027, 0.022, 2.0, 2.0), (0.157, 0.017, 0.024, 0.025, 0.021, 2.0, 2.0), (0.17, 0.016, 0.017, 0.018, 0.018, 2.0, 2.0), (0.18, 0.014, 0.011, 0.0125, 0.0135, 2.0, 2.0), (0.198, 0.012, 0.0085, 0.0098, 0.0105, 2.0, 2.0), (0.215, 0.0095, 0.0062, 0.0075, 0.0075, 2.0, 2.0), (0.227, 0.006, 0.0042, 0.0055, 0.005, 2.0, 2.0), (0.234, 0.003, 0.0028, 0.0038, 0.003, 2.0, 2.0)],
        "rings": [-0.115, -0.105, -0.095, -0.078, -0.06, -0.04, -0.02, 0.003, 0.025, 0.045, 0.065, 0.08, 0.095, 0.108, 0.12, 0.13, 0.14, 0.149, 0.157, 0.164, 0.17, 0.175, 0.18, 0.189, 0.198, 0.207, 0.215, 0.221, 0.227, 0.231, 0.234],
        "tips": ((0.0, -0.121, 0.006), (0.0, 0.239, 0.0005)),
        "around": 18,
        "head": 0.108,
        "bill": 0.177,
        "eye": ((0.0205, 0.153, 0.027), (0.85, 0.4, 0.3), 0.0052),
        "wing": [(0.035, 0.042, -0.1, 0.014, 0.024), (0.07, 0.048, -0.118, 0.017, 0.022), (0.11, 0.056, -0.128, 0.021, 0.02), (0.16, 0.064, -0.132, 0.025, 0.017), (0.21, 0.07, -0.13, 0.028, 0.015), (0.25, 0.072, -0.122, 0.029, 0.013), (0.29, 0.07, -0.11, 0.028, 0.012), (0.33, 0.065, -0.1, 0.027, 0.011), (0.36, 0.059, -0.093, 0.026, 0.0095), (0.38, 0.052, -0.086, 0.025, 0.009), (0.389, 0.043, -0.079, 0.025, 0.0085)],
        "tip": (0.393, -0.018, 0.025),
        "wrist": 0.25,
        "tail": {"base": ((-0.022, -0.095, 0.006), (0.022, -0.095, 0.006)), "tips": [(x, -0.24 + 0.03 * (x / 0.055) ** 2, 0.002) for x in numpy.linspace(-0.055, 0.055, 11)], "thick": 0.007, "rows": 5},
        "fingers": [((0.37, 0.041, 0.025), (0.96, 0.18, 0.0), 0.095), ((0.372, 0.017, 0.025), (0.99, 0.06, 0.0), 0.105), ((0.373, -0.008, 0.025), (0.99, -0.06, 0.0), 0.105), ((0.372, -0.033, 0.025), (0.97, -0.18, 0.0), 0.098), ((0.37, -0.057, 0.025), (0.94, -0.3, 0.0), 0.088)],
    }


def wing(m, sections, tip, part):
    rings = []
    for x, le, te, z, t in sections:
        chord = abs(le - te)
        ring = []
        for c in upper_chord:
            camber = 0.035 * chord * 4.0 * c * (1.0 - c)
            ring.append(m.vertex((x, le + (te - le) * c, z + camber + 0.62 * t * thickness(c) * 0.5), part, (x, c)))
        for c in lower_chord:
            camber = 0.035 * chord * 4.0 * c * (1.0 - c)
            ring.append(m.vertex((x, le + (te - le) * c, z + camber - 0.38 * t * thickness(c) * 0.5), part, (x, c)))
        rings.append(ring)
    count = len(rings[0])
    split = len(upper_chord) - 1
    for level in range(len(rings) - 1):
        for index in range(count):
            following = (index + 1) % count
            m.face((rings[level][index], rings[level][following], rings[level + 1][following], rings[level + 1][index]), "wing_upper" if index < split else "wing_lower")
    end = m.vertex(tip, part, (tip[0], 0.5))
    for index in range(count):
        m.face((rings[-1][index], rings[-1][(index + 1) % count], end), "wing_upper" if index < split else "wing_lower")
    root = m.vertex(numpy.mean([m.points[i] for i in rings[0]], axis=0) - numpy.array([0.01, 0.0, 0.0]), part, (0.0, 0.5))
    m.fan(rings[0][::-1], root, "wing_lower")
    m.seam([ring[0] for ring in rings] + [end])
    m.seam([ring[split] for ring in rings] + [end])
    return rings


def finger(m, root, direction, length, part):
    direction = unit(direction)
    side = unit(numpy.cross(numpy.array([0.0, 0.0, 1.0]), direction))
    root = numpy.asarray(root, dtype=numpy.float64)
    tip = root + direction * length + numpy.array([0.0, 0.0, -0.004])
    base = [root - side * 0.02 - direction * 0.045, root + side * 0.02 - direction * 0.045]
    tips = [tip - side * 0.011 - direction * 0.012, tip + direction * 0.003, tip + side * 0.011 - direction * 0.012]

    def bend(s, t):
        return numpy.array([0.0, 0.0, 0.004 * s * (1.0 - s)])

    kit.plate(m, base, tips, numpy.array([0.0, 0.0, 1.0]), 0.004, 5, part, ("finger_upper", "finger_lower"), coord=lambda s, t: (s, t), bulge=bend)


def assemble(spec):
    m = kit.mesh()
    body = spec["body"]
    rings = spec["rings"]
    low = body[0][0]
    high = body[-1][0]
    picks = [(y - low) / (high - low) for y in rings]

    def tagger(y):
        if y >= spec["bill"]:
            return "bill"
        if y >= spec["head"]:
            return "head"
        return "body"

    kit.body(m, body, len(rings), spec["around"], "body", "body", tip_front=numpy.array(spec["tips"][1]), tip_back=numpy.array(spec["tips"][0]), tagger=tagger, spacing=picks)
    start = len(m.points)
    wing(m, spec["wing"], numpy.array(spec["tip"]), "wing")
    for root, direction, length in spec["fingers"]:
        finger(m, root, direction, length, "finger")
    center, axis, radius = spec["eye"]
    kit.eyeball(m, numpy.array(center), numpy.array(axis), radius)
    kit.mirror(m, start)
    tail = spec["tail"]

    def arch(s, t):
        return numpy.array([0.0, 0.0, 0.006 * math.sin(math.pi * t) * s])

    kit.plate(m, tail["base"], tail["tips"], numpy.array([0.0, 0.0, 1.0]), tail["thick"], tail["rows"], "tail", ("tail_upper", "tail_lower"), coord=lambda s, t: (s, t), bulge=arch)
    return m.model()


def flows(c, spec):
    p = c.position
    flow = numpy.tile(numpy.array([0.0, -1.0, 0.0]), (len(p), 1))
    wing = c.tagged("wing_upper", "wing_lower")
    hand = wing & (p[:, 0] ** 2 > spec["wrist"] ** 2)
    flow[hand] = numpy.column_stack([numpy.sign(p[hand, 0]) * 0.9, numpy.full(hand.sum(), -0.45), numpy.zeros(hand.sum())])
    fingers = c.tagged("finger_upper", "finger_lower")
    flow[fingers] = numpy.column_stack([numpy.sign(p[fingers, 0]), numpy.zeros(fingers.sum()), numpy.zeros(fingers.sum())])
    return flow


def feathers(c, spec):
    p = c.position
    coord = c.coord
    count = len(p)
    wing = c.tagged("wing_upper", "wing_lower")
    upper = c.tagged("wing_upper")
    span = numpy.abs(p[:, 0])
    chord = numpy.clip(coord[:, 1], 0.0, 1.0)
    wrist = spec["wrist"]
    sections = numpy.array(spec["wing"])
    le = numpy.interp(span, sections[:, 0], sections[:, 1])
    te = numpy.interp(span, sections[:, 0], sections[:, 2])
    depth = (le - p[:, 1])
    length = numpy.maximum(le - te, 0.02)
    arm = span < wrist
    flight = numpy.where(arm, smooth(0.5, 0.58, chord), smooth(0.36, 0.44, chord) * smooth(wrist - 0.02, wrist + 0.03, span))
    width = numpy.where(arm, 0.021, 0.017)
    lane = numpy.where(arm, span / width, (depth + (span - wrist) * 0.35) / width)
    index = numpy.floor(lane)
    across = lane - index - 0.5
    shaft = smooth(0.06, 0.0, numpy.abs(across)) * flight
    split = smooth(0.42, 0.5, numpy.abs(across)) * flight
    du, dv, distance, cell = kit.tiles(depth, span, 0.02, 0.9, 0.8, 5, 0.35)
    covert = (1.0 - flight) * wing
    rim = smooth(0.78, 0.99, distance) * covert * smooth(-0.1, 0.4, du)
    lift = numpy.where(flight > 0.5, 0.6 + 0.4 * chord - 0.5 * split, 0.45 + 0.35 * (1.0 - distance) ** 0.6)
    bu, bv, body_distance, body_cell = kit.tiles(-p[:, 1], coord[:, 1], 0.012, 0.75, 0.8, 9, 0.35)
    trunk = c.tagged("body", "head")
    lift = numpy.where(trunk, 0.5 + 0.2 * (1.0 - body_distance) ** 0.6, lift)
    tail = c.tagged("tail_upper", "tail_lower")
    tail_lane = coord[:, 1] * 12.0
    tail_index = numpy.floor(tail_lane)
    tail_across = tail_lane - tail_index - 0.5
    lift = numpy.where(tail, 0.6 + 0.4 * coord[:, 0] - 0.5 * smooth(0.42, 0.5, numpy.abs(tail_across)), lift)
    shaft = numpy.where(tail, smooth(0.06, 0.0, numpy.abs(tail_across)), shaft)
    fingers = c.tagged("finger_upper", "finger_lower")
    finger_shaft = smooth(0.08, 0.0, numpy.abs(coord[:, 1] - 0.5)) * smooth(0.95, 0.6, coord[:, 0])
    shaft = numpy.where(fingers, finger_shaft, shaft)
    lift = numpy.where(fingers, 0.7 - 0.3 * numpy.abs(coord[:, 1] - 0.5), lift)
    return {"upper": upper, "wing": wing, "arm": arm, "flight": flight, "index": index, "across": across, "shaft": shaft, "split": split, "rim": rim, "cell": cell, "lift": lift, "chord": chord, "span": span, "trunk": trunk, "body_rim": smooth(0.8, 0.99, body_distance) * trunk * smooth(-0.1, 0.4, bu), "body_cell": body_cell, "tail": tail, "tail_split": smooth(0.42, 0.5, numpy.abs(tail_across)) * tail, "fingers": fingers, "length": length}


def coat(c, spec, occlusion):
    p = c.position
    n = c.normal
    count = len(p)
    f = feathers(c, spec)
    flow = flows(c, spec)
    barbs = c.fur(flow, 0.0011, 0.0009, 10, 1)
    soft = c.fur(flow, 0.003, 0.0016, 10, 2)
    mottle = paint.fbm(p, 0.03, 3, 7)
    bill = c.tagged("bill")
    ball = c.tagged("eyeball")
    head = c.tagged("head")
    if spec["kind"] == "gull":
        grey = numpy.array([0.6, 0.645, 0.69])
        white = numpy.array([0.9, 0.9, 0.885])
        color = numpy.tile(white, (count, 1))
        mantle = f["trunk"] * smooth(0.25, 0.6, n[:, 2]) * smooth(-0.12, -0.06, p[:, 1]) * smooth(0.17, 0.11, p[:, 1])
        color = tint(color, grey, mantle)
        color = numpy.where(f["upper"][:, None], grey[None, :] * (0.96 + 0.08 * (f["cell"] - 0.5))[:, None], color)
        tipband = f["upper"] * f["flight"] * f["arm"] * smooth(0.86, 0.95, f["chord"])
        color = tint(color, white, tipband)
        hand = f["upper"] * smooth(spec["wrist"], spec["wrist"] + 0.04, f["span"])
        black = hand * smooth(0.5, 0.58, f["span"] + 0.12 * (f["chord"] - 0.5)) * numpy.maximum(f["flight"], smooth(0.56, 0.62, f["span"]))
        color = tint(color, numpy.array([0.035, 0.035, 0.04]), black)
        mirror = smooth(0.016, 0.009, numpy.hypot(f["span"] - 0.64, (p[:, 1] - (-0.035)) * 0.8)) * f["upper"]
        mirror = numpy.maximum(mirror, smooth(0.012, 0.006, numpy.hypot(f["span"] - 0.6, (p[:, 1] - (-0.05)) * 0.9)) * f["upper"])
        apical = black * smooth(0.93, 0.985, f["chord"])
        color = tint(color, white, numpy.maximum(mirror, apical * 0.85))
        under_tip = f["wing"] * (1.0 - f["upper"]) * smooth(0.55, 0.64, f["span"]) * smooth(0.3, 0.7, f["chord"] + (f["span"] - 0.55) * 2.0)
        color = tint(color, numpy.array([0.32, 0.32, 0.34]), under_tip * 0.8)
        color = tint(color, color * 0.82, f["split"] * 0.45 + f["rim"] * 0.12 + f["body_rim"] * 0.035 + f["tail_split"] * 0.25)
        yellow = numpy.array([0.93, 0.76, 0.22])
        beak = tint(numpy.tile(yellow, (count, 1)), (0.97, 0.88, 0.5), smooth(0.263, 0.274, p[:, 1]))
        gonys = smooth(0.0075, 0.003, numpy.hypot(p[:, 1] - 0.254, (p[:, 2] - 0.003) * 1.4)) * (p[:, 2] < 0.008)
        beak = tint(beak, numpy.array([0.78, 0.13, 0.06]), gonys)
        gape = smooth(0.0016, 0.0004, numpy.abs(p[:, 2] - (0.0135 - (p[:, 1] - 0.214) * 0.12)))
        beak = tint(beak, numpy.array([0.25, 0.2, 0.08]), gape * 0.8)
        color[bill] = beak[bill]
        folded = p.copy()
        folded[:, 0] = numpy.abs(folded[:, 0])
        reach = numpy.linalg.norm(folded - numpy.array(spec["eye"][0])[None, :], axis=1)
        ring = smooth(0.0078, 0.0071, reach) * smooth(0.0058, 0.0064, reach) * head
        color = tint(color, numpy.array([0.88, 0.42, 0.16]), ring * 0.9)
        iris = (0.9, 0.86, 0.62)
        rough = numpy.full(count, 0.72)
        rough[bill] = 0.38
    else:
        black = numpy.array([0.028, 0.028, 0.034])
        color = numpy.tile(black, (count, 1)) * (0.85 + 0.3 * f["cell"])[:, None]
        sheen = smooth(0.2, 0.8, n[:, 2]) * (f["trunk"] + f["upper"] * (1.0 - f["flight"]))
        color = tint(color, numpy.array([0.045, 0.045, 0.085]), numpy.clip(sheen, 0.0, 1.0) * 0.6)
        color = tint(color, numpy.array([0.04, 0.036, 0.032]), f["flight"] * f["wing"] * 0.6 + f["fingers"] * 0.6)
        color = tint(color, color * 0.6, f["split"] * 0.5 + f["rim"] * 0.3 + f["tail_split"] * 0.4)
        beak = numpy.tile(numpy.array([0.06, 0.06, 0.068]), (count, 1))
        bristle = smooth(0.197, 0.181, p[:, 1]) * smooth(0.011, 0.019, p[:, 2])
        beak = tint(beak, black, bristle)
        gape = smooth(0.0016, 0.0004, numpy.abs(p[:, 2] - (0.0118 - (p[:, 1] - 0.177) * 0.16)))
        beak = tint(beak, numpy.array([0.015, 0.015, 0.018]), gape)
        color[bill] = beak[bill]
        iris = (0.13, 0.08, 0.05)
        rough = numpy.full(count, 0.5)
        rough = rough - 0.12 * sheen
        rough[bill] = 0.32
    shade = numpy.where(f["trunk"], 0.93 + 0.1 * barbs, 0.88 + 0.2 * barbs) + (mottle - 0.5) * 0.05
    feathered = ~bill & ~ball
    color = numpy.where(feathered[:, None], color * shade[:, None], color)
    color = color * (0.8 + 0.2 * occlusion)[:, None]
    rough = numpy.where(feathered, rough + 0.12 * (1.0 - soft) - 0.08 * f["shaft"], rough)
    height = numpy.where(feathered, 0.55 * f["lift"] + 0.3 * barbs + 0.25 * f["shaft"], 0.5)
    relief = numpy.where(feathered, 0.0011, 0.0002)
    eye = numpy.array(spec["eye"][0])
    axis = unit(numpy.array(spec["eye"][1]))
    mirrored = p.copy()
    mirrored[:, 0] = numpy.abs(mirrored[:, 0])
    direction = mirrored - eye[None, :]
    direction = direction / numpy.maximum(numpy.linalg.norm(direction, axis=1), 1e-9)[:, None]
    facing = direction @ axis
    pupil = smooth(0.93, 0.95, facing)
    iris_mask = smooth(0.6, 0.68, facing)
    eye_color = tint(numpy.tile(numpy.array([0.05, 0.04, 0.035]), (count, 1)), iris, iris_mask)
    eye_color = tint(eye_color, (0.01, 0.01, 0.012), pupil)
    color[ball] = eye_color[ball]
    rough[ball] = 0.06
    relief[ball] = 0.0
    return {"color": color, "rough": rough, "height": height, "relief": relief}
