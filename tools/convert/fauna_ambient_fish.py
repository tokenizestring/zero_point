import math
import numpy
import fauna_ambient_kit as kit
import fauna_hoofed_coats as coats
import fauna_hoofed_field as fields
import fauna_hoofed_paint as paint

unit = fields.unit
smooth = fields.smoothstep
tint = coats.tint


def surface(stations, y):
    profile, along = kit.table(stations, 256)
    index = numpy.clip(numpy.rint((numpy.asarray(y) - along[0]) / (along[-1] - along[0]) * 255).astype(numpy.int64), 0, 255)
    return profile[index]


def ridge(stations, y, side=1.0, lift=0.0):
    row = surface(stations, [y])[0]
    return numpy.array([0.0, y, row[0] + (row[2] - lift if side > 0 else lift - row[3])])


def spines(stations, front, back, heights, notch, count, side=1.0, inset=0.0015):
    tips = []
    base = []
    for index in range(count):
        t = index / (count - 1.0)
        y = front + (back - front) * t
        rim = ridge(stations, y, side, inset)
        height = float(numpy.interp(t, numpy.linspace(0.0, 1.0, len(heights)), heights))
        lean = numpy.array([0.0, -0.35 * height, 0.0])
        drop = height * (notch if index % 2 == 1 else 1.0)
        tips.append(rim + numpy.array([0.0, 0.0, drop * side]) + lean * (drop / max(height, 1e-6)))
        base.append(rim)
    return base, tips


def build(kind):
    if kind == "mackerel":
        body = [(-0.128, 0.0, 0.0042, 0.0055, 0.0055, 2.0, 2.0), (-0.115, 0.0, 0.0046, 0.0063, 0.0063, 2.0, 2.0), (-0.095, 0.0, 0.0066, 0.0105, 0.0105, 2.0, 2.0), (-0.07, 0.0, 0.0105, 0.017, 0.016, 2.0, 2.0), (-0.04, 0.0, 0.0155, 0.024, 0.022, 2.05, 2.05), (-0.005, 0.001, 0.019, 0.029, 0.027, 2.1, 2.1), (0.03, 0.001, 0.021, 0.031, 0.029, 2.1, 2.1), (0.065, 0.001, 0.021, 0.03, 0.029, 2.1, 2.1), (0.095, 0.0, 0.019, 0.027, 0.027, 2.1, 2.1), (0.12, -0.001, 0.0165, 0.023, 0.024, 2.05, 2.05), (0.14, -0.002, 0.013, 0.018, 0.019, 2.0, 2.0), (0.155, -0.003, 0.0095, 0.012, 0.013, 2.0, 2.0), (0.167, -0.003, 0.0055, 0.0068, 0.0078, 2.0, 2.0), (0.173, -0.003, 0.003, 0.0038, 0.0045, 2.0, 2.0)]
        rings = [-0.128, -0.12, -0.11, -0.1, -0.09, -0.08, -0.07, -0.055, -0.04, -0.022, -0.005, 0.013, 0.03, 0.048, 0.065, 0.08, 0.095, 0.108, 0.12, 0.13, 0.14, 0.148, 0.155, 0.161, 0.167, 0.173]
        spec = {"name": "fish_mackerel", "kind": kind, "budget": (800, 2500), "body": body, "rings": rings, "tips": ((0.0, -0.131, 0.0), (0.0, 0.177, -0.003)), "around": 16, "gill": 0.123, "eye": ((0.0072, 0.143, 0.004), (0.92, 0.3, 0.12), 0.0068), "mouth": (0.158, -0.0045, 0.06)}
        caudal = {"base": ((0.0, -0.124, -0.0062), (0.0, -0.124, 0.0062)), "tips": [(0.0, -0.177, -0.045), (0.0, -0.167, -0.033), (0.0, -0.157, -0.02), (0.0, -0.148, -0.007), (0.0, -0.147, 0.0), (0.0, -0.148, 0.007), (0.0, -0.157, 0.02), (0.0, -0.167, 0.033), (0.0, -0.177, 0.045)], "normal": (1.0, 0.0, 0.0), "thick": 0.0026, "rows": 4, "tag": "caudal"}
        first_base, first_tips = spines(body, 0.062, 0.018, [0.014, 0.02, 0.019, 0.015, 0.011, 0.007, 0.004], 0.72, 11)
        fins = [caudal, {"base": first_base, "tips": first_tips, "normal": (1.0, 0.0, 0.0), "thick": 0.0018, "rows": 3, "tag": "fin"}]
        second_base, second_tips = spines(body, -0.03, -0.058, [0.011, 0.012, 0.008, 0.004], 0.95, 6)
        fins.append({"base": second_base, "tips": second_tips, "normal": (1.0, 0.0, 0.0), "thick": 0.0018, "rows": 3, "tag": "fin"})
        anal_base, anal_tips = spines(body, -0.03, -0.058, [0.009, 0.01, 0.007, 0.004], 0.95, 6, -1.0)
        fins.append({"base": anal_base, "tips": anal_tips, "normal": (1.0, 0.0, 0.0), "thick": 0.0018, "rows": 3, "tag": "fin"})
        for index in range(5):
            y = -0.066 - index * 0.0105
            for side in (1.0, -1.0):
                base, tips = spines(body, y + 0.004, y - 0.004, [0.0045, 0.002], 1.0, 3, side, 0.001)
                fins.append({"base": base, "tips": tips, "normal": (1.0, 0.0, 0.0), "thick": 0.0014, "rows": 2, "tag": "fin"})
        spec["pectoral"] = {"root": (0.0155, 0.115, 0.002), "tips": [(0.0215, 0.086, 0.007), (0.0225, 0.082, 0.002), (0.0215, 0.086, -0.004)], "width": 0.006, "thick": 0.0016}
        spec["pelvic"] = {"root": (0.0045, 0.104, -0.0245), "tips": [(0.008, 0.083, -0.027), (0.009, 0.081, -0.029), (0.0065, 0.083, -0.03)], "width": 0.004, "thick": 0.0014}
        spec["fins"] = fins
        spec["tags"] = {"caudal": "fin"}
        return spec
    body = [(-0.21, 0.0, 0.007, 0.016, 0.016, 2.0, 2.0), (-0.19, 0.0, 0.0095, 0.02, 0.02, 2.0, 2.0), (-0.15, 0.001, 0.016, 0.033, 0.031, 2.0, 2.0), (-0.1, 0.002, 0.026, 0.05, 0.046, 2.05, 2.05), (-0.04, 0.004, 0.036, 0.066, 0.06, 2.1, 2.1), (0.02, 0.005, 0.042, 0.075, 0.068, 2.15, 2.15), (0.08, 0.006, 0.043, 0.074, 0.07, 2.15, 2.15), (0.14, 0.006, 0.04, 0.066, 0.064, 2.1, 2.1), (0.19, 0.006, 0.034, 0.054, 0.056, 2.05, 2.05), (0.23, 0.006, 0.027, 0.043, 0.045, 2.0, 2.0), (0.26, 0.005, 0.02, 0.031, 0.034, 2.0, 2.0), (0.28, 0.003, 0.014, 0.02, 0.024, 2.0, 2.0), (0.294, 0.002, 0.008, 0.01, 0.0135, 2.0, 2.0)]
    rings = [-0.21, -0.2, -0.19, -0.175, -0.16, -0.14, -0.12, -0.1, -0.075, -0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.1, 0.12, 0.14, 0.155, 0.17, 0.19, 0.205, 0.22, 0.235, 0.248, 0.26, 0.27, 0.28, 0.288, 0.294]
    spec = {"name": "fish_bass", "kind": kind, "budget": (800, 2500), "body": body, "rings": rings, "tips": ((0.0, -0.214, 0.0), (0.0, 0.301, 0.0)), "around": 18, "gill": 0.165, "eye": ((0.0162, 0.239, 0.022), (0.9, 0.32, 0.14), 0.0098), "mouth": (0.262, -0.009, 0.16)}
    caudal = {"base": ((0.0, -0.205, -0.016), (0.0, -0.205, 0.016)), "tips": [(0.0, -0.302, -0.074), (0.0, -0.291, -0.054), (0.0, -0.279, -0.033), (0.0, -0.271, -0.013), (0.0, -0.269, 0.0), (0.0, -0.271, 0.013), (0.0, -0.279, 0.033), (0.0, -0.291, 0.054), (0.0, -0.302, 0.074)], "normal": (1.0, 0.0, 0.0), "thick": 0.0036, "rows": 4, "tag": "caudal"}
    first_base, first_tips = spines(body, 0.125, 0.03, [0.028, 0.05, 0.057, 0.055, 0.049, 0.041, 0.032, 0.024, 0.016], 0.66, 17)
    second_base, second_tips = spines(body, 0.018, -0.105, [0.03, 0.044, 0.043, 0.037, 0.03, 0.022], 0.97, 9)
    anal_base, anal_tips = spines(body, -0.04, -0.125, [0.02, 0.036, 0.037, 0.032, 0.024, 0.016], 0.88, 9, -1.0)
    spec["fins"] = [caudal, {"base": first_base, "tips": first_tips, "normal": (1.0, 0.0, 0.0), "thick": 0.0022, "rows": 3, "tag": "spiny"}, {"base": second_base, "tips": second_tips, "normal": (1.0, 0.0, 0.0), "thick": 0.0022, "rows": 3, "tag": "fin"}, {"base": anal_base, "tips": anal_tips, "normal": (1.0, 0.0, 0.0), "thick": 0.0022, "rows": 3, "tag": "fin"}]
    spec["pectoral"] = {"root": (0.0335, 0.152, -0.008), "tips": [(0.054, 0.1, 0.004), (0.057, 0.093, -0.008), (0.053, 0.099, -0.02)], "width": 0.011, "thick": 0.0022}
    spec["pelvic"] = {"root": (0.0105, 0.132, -0.06), "tips": [(0.017, 0.082, -0.066), (0.019, 0.078, -0.07), (0.014, 0.084, -0.073)], "width": 0.007, "thick": 0.002}
    spec["tags"] = {"caudal": "fin"}
    return spec


def paired(m, fin):
    root = numpy.asarray(fin["root"], dtype=numpy.float64)
    tips = [numpy.asarray(t, dtype=numpy.float64) for t in fin["tips"]]
    direction = unit(tips[1] - root)
    across = unit(tips[0] - tips[-1])
    normal = unit(numpy.cross(direction, across))
    if normal[0] < 0.0:
        normal = -normal
    base = [root + across * fin["width"] * 0.5, root - across * fin["width"] * 0.5]
    kit.plate(m, base, tips, normal, fin["thick"], 3, "fin", ("pectoral", "pectoral"), coord=lambda s, t: (s, t))


def assemble(spec):
    m = kit.mesh()
    body = spec["body"]
    rings = spec["rings"]
    low = body[0][0]
    high = body[-1][0]
    gill = spec["gill"]

    def tagger(y):
        return "head" if y >= gill else "body"

    kit.body(m, body, len(rings), spec["around"], "body", "body", tip_front=numpy.array(spec["tips"][1]), tip_back=numpy.array(spec["tips"][0]), tagger=tagger, spacing=[(y - low) / (high - low) for y in rings])
    for fin in spec["fins"]:
        tag = spec["tags"].get(fin["tag"], fin["tag"])
        kit.plate(m, fin["base"], fin["tips"], numpy.array(fin["normal"]), fin["thick"], fin["rows"], fin["tag"], (tag, tag), coord=lambda s, t: (s, t))
    start = len(m.points)
    paired(m, spec["pectoral"])
    paired(m, spec["pelvic"])
    center, axis, radius = spec["eye"]
    kit.eyeball(m, numpy.array(center), numpy.array(axis), radius, segments=12)
    kit.mirror(m, start)
    return m.model()


def coat(c, spec, occlusion):
    p = c.position
    n = c.normal
    count = len(p)
    body = c.tagged("body", "head")
    head = c.tagged("head")
    fin = c.tagged("fin", "spiny", "pectoral")
    pectoral = c.tagged("pectoral")
    ball = c.tagged("eyeball")
    profile = surface(spec["body"], p[:, 1])
    middle = profile[:, 0]
    level = numpy.where(p[:, 2] >= middle, (p[:, 2] - middle) / numpy.maximum(profile[:, 2], 1e-4), (p[:, 2] - middle) / numpy.maximum(profile[:, 3], 1e-4))
    arc = numpy.abs(c.coord[:, 1])
    noise = paint.fbm(p, 0.02, 3, 3)
    fine = paint.fbm(p, 0.004, 2, 4)
    length = spec["body"][-1][0] - spec["body"][0][0]
    gill = spec["gill"]
    gill_line = gill + 0.012 * (1.0 - level ** 2) * (length / 0.3)
    cover = smooth(0.0035, 0.0008, numpy.abs(p[:, 1] - gill_line)) * body * smooth(0.9, 0.6, numpy.abs(level))
    rays = numpy.zeros(count)
    rays[fin] = (0.5 + 0.5 * numpy.cos(2.0 * math.pi * c.coord[fin, 1] * 10.0)) ** 6
    if spec["kind"] == "mackerel":
        size = 0.0024
        du, dv, distance, cell = kit.tiles(-p[:, 1], arc, size, 0.8, 0.8, 11)
        back = numpy.array([0.1, 0.31, 0.34])
        color = numpy.tile(back, (count, 1))
        color = tint(color, numpy.array([0.12, 0.25, 0.4]), smooth(0.35, 0.75, noise) * 0.6)
        phase = -p[:, 1] / 0.0118 + (1.0 - level) * 1.9 + 0.45 * numpy.sin((1.0 - level) * 7.0 + p[:, 1] * 40.0) + (noise - 0.5) * 1.6
        bars = smooth(0.25, 0.55, numpy.sin(2.0 * math.pi * phase)) * smooth(0.12, 0.3, level) * body * smooth(0.165, 0.12, p[:, 1]) * smooth(-0.124, -0.1, p[:, 1])
        color = tint(color, numpy.array([0.02, 0.035, 0.045]), bars * 0.92)
        sheen = smooth(0.25, -0.05, level) * smooth(-0.45, -0.1, level)
        color = tint(color, numpy.array([0.72, 0.66, 0.5]), sheen * 0.5)
        belly = smooth(0.1, -0.25, level + (noise - 0.5) * 0.15)
        color = tint(color, numpy.array([0.8, 0.82, 0.83]), belly)
        color = tint(color, numpy.array([0.9, 0.82, 0.78]), smooth(-0.55, -0.9, level) * 0.35)
        top = smooth(0.0, 0.5, level) * head
        color = tint(color, numpy.array([0.06, 0.12, 0.14]), top * 0.7)
        cheek = head * smooth(0.25, -0.2, level)
        color = tint(color, numpy.array([0.75, 0.77, 0.76]), cheek * 0.8)
        fin_color = numpy.array([0.16, 0.2, 0.22])
        rough_body = 0.24
    else:
        size = 0.0068
        du, dv, distance, cell = kit.tiles(-p[:, 1], arc, size, 0.82, 0.8, 13)
        color = numpy.tile(numpy.array([0.62, 0.65, 0.67]), (count, 1))
        color = tint(color, numpy.array([0.2, 0.25, 0.28]), smooth(0.05, 0.75, level + (noise - 0.5) * 0.2))
        color = tint(color, numpy.array([0.13, 0.17, 0.19]), smooth(0.65, 0.95, level))
        color = tint(color, numpy.array([0.88, 0.89, 0.89]), smooth(-0.35, -0.75, level))
        lateral = smooth(0.0028, 0.001, numpy.abs(level - (0.42 - 0.12 * smooth(-0.2, 0.1, -p[:, 1]))) * numpy.maximum(profile[:, 2], 1e-3)) * body * smooth(gill + 0.004, gill - 0.01, p[:, 1]) * smooth(-0.2, -0.17, p[:, 1])
        color = tint(color, numpy.array([0.12, 0.13, 0.14]), lateral * 0.8)
        spot = smooth(0.015, 0.004, numpy.hypot(p[:, 1] - (gill + 0.006), (p[:, 2] - (middle + profile[:, 2] * 0.32)) * 0.85)) * body
        color = tint(color, numpy.array([0.09, 0.09, 0.1]), spot * 0.65)
        cheek = head * smooth(0.4, -0.1, level)
        color = tint(color, numpy.array([0.72, 0.74, 0.74]), cheek * 0.5)
        fin_color = numpy.array([0.34, 0.37, 0.39])
        rough_body = 0.28
    bass = spec["kind"] == "bass"
    pocket = smooth(0.62, 0.95, distance) * body * smooth(gill + 0.005, gill - 0.01, p[:, 1])
    color = tint(color, color * 0.62, pocket * (0.5 if bass else 0.07))
    color = tint(color, color * 1.18 + 0.02, smooth(0.5, 0.0, distance) * smooth(0.3, -0.3, du) * body * (0.25 if bass else 0.08))
    color = color * (1.0 + (0.12 if bass else 0.05) * (cell - 0.5) * body)[:, None]
    color = tint(color, color * 0.5, cover * 0.45)
    gape, drop, slant = spec["mouth"]
    mouth = smooth(0.0013, 0.0004, numpy.abs(p[:, 2] - (drop + (p[:, 1] - gape) * slant))) * head * smooth(gape - 0.004, gape + 0.002, p[:, 1])
    color = tint(color, numpy.array([0.04, 0.04, 0.045]), mouth * 0.85)
    spiny = c.tagged("spiny")
    fins = numpy.tile(fin_color, (count, 1)) * (0.75 + 0.5 * fine)[:, None]
    fins = tint(fins, fin_color * 0.45, rays * 0.7)
    fins = tint(fins, fin_color * 1.4, spiny * rays * 0.5)
    fins = tint(fins, fin_color * 0.7, smooth(0.3, 1.0, c.coord[:, 0]) * 0.3)
    fins = numpy.where(pectoral[:, None], fins * 1.45 + 0.03, fins)
    color[fin] = fins[fin]
    color = color * (0.8 + 0.2 * occlusion)[:, None]
    rough = numpy.full(count, rough_body)
    rough = rough + 0.08 * pocket
    rough[fin] = 0.36
    height = numpy.where(body, (1.0 - distance) ** 0.5 * 0.8 - 0.6 * cover - 0.4 * mouth, 0.5 + 0.4 * rays)
    relief = numpy.where(body, 0.0009 if bass else 0.00022, 0.0005)
    mirrored = p.copy()
    mirrored[:, 0] = numpy.abs(mirrored[:, 0])
    eye = numpy.array(spec["eye"][0])
    axis = unit(numpy.array(spec["eye"][1]))
    direction = mirrored - eye[None, :]
    direction = direction / numpy.maximum(numpy.linalg.norm(direction, axis=1), 1e-9)[:, None]
    facing = direction @ axis
    eye_color = tint(numpy.tile(numpy.array([0.7, 0.66, 0.5]), (count, 1)), numpy.array([0.02, 0.02, 0.025]), smooth(0.86, 0.9, facing))
    eye_color = tint(eye_color, numpy.array([0.3, 0.28, 0.22]), smooth(0.55, 0.3, facing))
    color[ball] = eye_color[ball]
    rough[ball] = 0.05
    relief[ball] = 0.0
    return {"color": color, "rough": rough, "height": height, "relief": relief}
