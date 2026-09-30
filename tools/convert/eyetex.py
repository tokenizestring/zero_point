import math
import os
import numpy

import texels
import headtex

irises = {
    "hazel": {"pupil": (0.035, 0.03, 0.028), "inner": (0.36, 0.23, 0.1), "outer": (0.23, 0.17, 0.1), "fibre": (0.41, 0.3, 0.16), "dark": (0.1, 0.07, 0.045), "limbus": (0.075, 0.058, 0.048), "flecks": (0.38, 0.34, 0.17)},
    "green": {"pupil": (0.035, 0.033, 0.033), "inner": (0.4, 0.35, 0.17), "outer": (0.26, 0.31, 0.27), "fibre": (0.45, 0.5, 0.45), "dark": (0.12, 0.14, 0.13), "limbus": (0.08, 0.09, 0.09), "flecks": (0.46, 0.4, 0.2)},
}

iris_fraction = 0.38
uv_equator = 0.47


def polar_noise(angle, radius, frequency, radial_frequency, seed, octaves=3):
    points = numpy.stack([numpy.cos(angle) * frequency, numpy.sin(angle) * frequency, radius * radial_frequency], axis=1)
    return texels.noise(points, 1.0, seed, octaves)


def eye_maps(kind, directory, prefix, size=1024, seed=21):
    rng = numpy.random.default_rng(seed)
    palette = {key: texels.to_linear(numpy.asarray(value)) for key, value in irises[kind].items()}
    coordinates = (numpy.arange(size) + 0.5) / size
    u, v = numpy.meshgrid(coordinates, coordinates)
    du = (u - 0.5).ravel()
    dv = (v - 0.5).ravel()
    radius = numpy.hypot(du, dv) / uv_equator
    angle = numpy.arctan2(dv, du)
    iris_r = iris_fraction
    pupil_r = iris_r * 0.34
    rho = numpy.clip((radius - pupil_r) / (iris_r - pupil_r), 0.0, 1.0)
    fibres = polar_noise(angle, rho, 34.0, 3.0, seed, 3)
    fine = polar_noise(angle, rho, 120.0, 6.0, seed + 1, 2)
    streak = numpy.clip((fibres - 0.5) * 2.2 + (fine - 0.5) * 1.4, -1.0, 1.0)
    collarette_r = 0.36 + 0.05 * polar_noise(angle, numpy.zeros_like(rho), 9.0, 1.0, seed + 2, 2)
    inner = texels.smoothstep(collarette_r + 0.05, collarette_r - 0.04, rho)
    collarette = numpy.exp(-((rho - collarette_r) / 0.035) ** 2)
    crypts = texels.smoothstep(0.72, 0.8, polar_noise(angle, rho, 16.0, 7.0, seed + 3, 2)) * texels.smoothstep(0.25, 0.4, rho) * texels.smoothstep(0.9, 0.75, rho)
    furrows = (0.5 + 0.5 * numpy.cos(rho * 2.0 * math.pi * 5.0 + 2.0 * polar_noise(angle, rho, 6.0, 1.0, seed + 4, 1))) * texels.smoothstep(0.6, 0.85, rho)
    flecks = texels.smoothstep(0.78, 0.86, polar_noise(angle, rho, 40.0, 9.0, seed + 5, 1)) * texels.smoothstep(0.15, 0.35, rho) * texels.smoothstep(0.7, 0.5, rho)
    base = palette["outer"][None, :] * (1.0 - inner[:, None]) + palette["inner"][None, :] * inner[:, None]
    iris = base * (1.0 + 0.45 * streak[:, None])
    iris = iris + (palette["fibre"][None, :] - iris) * (numpy.clip(streak, 0.0, 1.0) * 0.35)[:, None]
    iris = iris + (palette["fibre"][None, :] * 1.1 - iris) * (collarette * 0.35)[:, None]
    iris = iris * (1.0 - crypts[:, None] * 0.45) * (1.0 - furrows[:, None] * 0.06)
    iris = iris + (palette["flecks"][None, :] - iris) * (flecks * 0.5)[:, None]
    limbal = texels.smoothstep(0.78, 1.0, rho)
    iris = iris + (palette["limbus"][None, :] - iris) * (limbal ** 1.5 * 0.85)[:, None]
    ruff = texels.smoothstep(0.08, 0.0, rho) * (0.6 + 0.4 * fine)
    iris = iris + (palette["dark"][None, :] - iris) * (ruff * 0.7)[:, None]
    pupil = texels.smoothstep(pupil_r + 0.004, pupil_r - 0.004, radius)
    iris = iris * (1.0 - pupil[:, None]) + palette["pupil"][None, :] * pupil[:, None]
    sclera_base = texels.to_linear(numpy.array([0.71, 0.68, 0.645]))
    horizontal = numpy.abs(du) / uv_equator
    corner = texels.smoothstep(0.45, 0.95, horizontal) * texels.smoothstep(0.7, 0.2, numpy.abs(dv) / uv_equator)
    blotch = texels.noise(numpy.stack([du * 40.0, dv * 40.0, numpy.zeros_like(du)], axis=1), 1.0, seed + 6, 3)
    sclera = sclera_base[None, :] * (0.95 + 0.08 * blotch[:, None])
    sclera = sclera * (1.0 + corner[:, None] * numpy.array([0.02, -0.08, -0.1]))
    edge = texels.smoothstep(iris_r * 1.12, iris_r * 1.0, radius)
    sclera = sclera * (1.0 - edge[:, None] * numpy.array([0.18, 0.15, 0.1]))
    image_size = size
    veins = numpy.zeros((image_size, image_size))
    points = []
    values = []
    for vessel in range(110):
        side = 1.0 if vessel % 2 == 0 else -1.0
        start_angle = rng.normal(0.0, 0.42) + (0.0 if side > 0 else math.pi)
        start = numpy.array([math.cos(start_angle), math.sin(start_angle)]) * uv_equator * rng.uniform(0.8, 1.0)
        heading = math.atan2(-start[1], -start[0]) + rng.normal(0.0, 0.35)
        position = start.copy()
        width = rng.uniform(0.6, 1.2)
        strength = rng.uniform(0.3, 1.0)
        length = rng.uniform(0.16, 0.36)
        steps = int(length * image_size * 1.4)
        for step in range(steps):
            t = step / max(steps - 1, 1)
            heading += rng.normal(0.0, 0.08)
            position = position + numpy.array([math.cos(heading), math.sin(heading)]) / (image_size * 1.4)
            if numpy.hypot(position[0], position[1]) < iris_r * uv_equator * 1.15:
                break
            points.append((position[0] + 0.5) * image_size)
            points.append((position[1] + 0.5) * image_size)
            values.append(strength * (1.0 - t) ** 0.8)
            if rng.random() < 0.012:
                branch = position.copy()
                branch_heading = heading + rng.choice([-1.0, 1.0]) * rng.uniform(0.5, 1.1)
                for b in range(int(steps * 0.3)):
                    branch_heading += rng.normal(0.0, 0.1)
                    branch = branch + numpy.array([math.cos(branch_heading), math.sin(branch_heading)]) / (image_size * 1.4)
                    points.append((branch[0] + 0.5) * image_size)
                    points.append((branch[1] + 0.5) * image_size)
                    values.append(strength * 0.6 * (1.0 - b / max(steps * 0.3, 1)))
    if values:
        points = numpy.array(points).reshape(-1, 2)
        weight, accumulation = headtex.splat(image_size, points, numpy.array(values)[:, None], 1.7)
        veins = 1.0 - numpy.exp(-weight * 0.5)
        veins = texels.blur(veins, 1) * 0.4 + veins * 0.6
    vein_flat = veins.ravel()
    vein_color = texels.to_linear(numpy.array([0.62, 0.2, 0.17]))
    flush = corner * (0.5 + 0.5 * blotch)
    sclera = sclera * (1.0 - flush[:, None] * numpy.array([0.0, 0.1, 0.12]))
    sclera = sclera + (vein_color[None, :] - sclera) * (vein_flat * 0.72)[:, None]
    iris_weight = texels.smoothstep(iris_r * 1.0, iris_r * 0.97, radius)
    albedo = sclera * (1.0 - iris_weight[:, None]) + iris * iris_weight[:, None]
    upward = dv / uv_equator
    lid = texels.smoothstep(0.12, 0.62, upward) * 0.42 + texels.smoothstep(-0.3, -0.75, upward) * 0.2 + texels.smoothstep(0.55, 1.0, numpy.abs(du) / uv_equator) * 0.25
    albedo = albedo * (1.0 - numpy.clip(lid, 0.0, 0.6)[:, None] * numpy.array([0.85, 1.0, 1.0]))
    caruncle_zone = (u.ravel() < 0.1) & (v.ravel() < 0.1)
    albedo[caruncle_zone] = texels.to_linear(numpy.array([0.72, 0.4, 0.38]))
    roughness = numpy.where(radius < iris_r * 1.02, 0.04, 0.1) + 0.02 * vein_flat
    roughness[caruncle_zone] = 0.22
    orm = numpy.stack([numpy.ones(size * size), roughness, numpy.zeros(size * size)], axis=1)
    height = (-vein_flat * 0.3 + (blotch - 0.5) * 0.2) * (1.0 - iris_weight)
    height_image = height.reshape(size, size)
    gx = numpy.zeros_like(height_image)
    gy = numpy.zeros_like(height_image)
    gx[:, 1:-1] = (height_image[:, 2:] - height_image[:, :-2]) * 0.5
    gy[1:-1, :] = (height_image[2:, :] - height_image[:-2, :]) * 0.5
    normal = numpy.stack([-gx * 0.6, -gy * 0.6, numpy.ones_like(gx)], axis=2)
    normal /= numpy.linalg.norm(normal, axis=2)[:, :, None]
    print("EYE", kind, "sclera", texels.to_srgb(sclera_base).round(3), "iris mean", texels.to_srgb(iris[iris_weight > 0.5].mean(axis=0)).round(3))
    headtex.save_image(os.path.join(directory, prefix + "_eye_albedo.png"), texels.to_srgb(albedo).reshape(size, size, 3), 'sRGB')
    headtex.save_image(os.path.join(directory, prefix + "_eye_orm.png"), orm.reshape(size, size, 3), 'Non-Color')
    headtex.save_image(os.path.join(directory, prefix + "_eye_nor_gl.png"), headtex.encode_normal(normal), 'Non-Color')
