import os
import numpy

import ground_kit as kit

suffixes = (("diff", "diff", 3), ("normal", "nor_dx", 3), ("arm", "arm", 3), ("disp", "disp", 1))


def seam(plane, near=8):
    plane = plane.astype(numpy.float64)
    if plane.ndim == 3:
        plane = plane.mean(axis=2)
    overall = 0.0
    worst = None
    offsets = numpy.concatenate([numpy.arange(-near, 0), numpy.arange(1, near + 1)])
    for axis in (0, 1):
        moved = numpy.moveaxis(plane, axis, 0)
        size = moved.shape[0]
        diffs = numpy.abs(moved - numpy.roll(moved, -1, axis=0)).mean(axis=1)
        ratios = diffs / numpy.maximum(diffs[(numpy.arange(size)[:, None] + offsets[None, :]) % size].mean(axis=1), 1e-9)
        overall = max(overall, diffs[-1] / max(diffs[:-1].mean(), 1e-9))
        boundary = ratios[7:-1:8]
        found = (float(ratios[-1]), float(numpy.percentile(boundary, 99.0)))
        if worst is None or found[0] - found[1] > worst[0] - worst[1]:
            worst = found
    return overall, worst[0], worst[1]


def orientation(normal, height):
    best = (-1.0, -1.0)
    for sigma in (2.0, 8.0, 24.0):
        smooth = kit.blur(height.astype(numpy.float32), sigma)
        green = kit.blur((normal[..., 1] * 2.0 - 1.0).astype(numpy.float32), sigma)
        red = kit.blur((normal[..., 0] * 2.0 - 1.0).astype(numpy.float32), sigma)
        down = (numpy.roll(smooth, -1, axis=0) - numpy.roll(smooth, 1, axis=0)).ravel()
        right = (numpy.roll(smooth, -1, axis=1) - numpy.roll(smooth, 1, axis=1)).ravel()
        found = (float(numpy.corrcoef(red.ravel(), -right)[0, 1]), float(numpy.corrcoef(green.ravel(), -down)[0, 1]))
        if min(found) > min(best):
            best = found
    return best


def measure(directory, name):
    report = {"name": name, "missing": [], "sizes": {}}
    maps = {}
    for key, suffix, channels in suffixes:
        path = os.path.join(directory, name, "%s_%s_2k.jpg" % (name, suffix))
        if not os.path.exists(path):
            report["missing"].append(suffix)
            continue
        pixels = kit.read_image(path)
        report["sizes"][key] = pixels.shape
        maps[key] = pixels.astype(numpy.float32) / 255.0
    if report["missing"]:
        return report
    vector = maps["normal"][..., :3] * 2.0 - 1.0
    length = numpy.linalg.norm(vector, axis=-1)
    height = maps["disp"][..., 0]
    linear = kit.to_linear(maps["diff"][..., :3])
    report["seam"] = {key: seam(maps[key]) for key in maps}
    report["length_mean"] = float(length.mean())
    report["length_mid"] = float(numpy.median(numpy.abs(length - 1.0)))
    report["length_off"] = float(numpy.percentile(numpy.abs(length - 1.0), 99.0))
    report["up_mean"] = float(vector[..., 2].mean())
    report["up_low"] = float(vector[..., 2].min())
    report["orientation"] = orientation(maps["normal"], height)
    report["metal_mean"] = float(maps["arm"][..., 2].mean())
    report["metal_high"] = float(numpy.percentile(maps["arm"][..., 2], 99.9))
    report["metal_peak"] = float(maps["arm"][..., 2].max())
    report["rough"] = [float(v) for v in numpy.percentile(maps["arm"][..., 1], [1, 50, 99])] + [float(maps["arm"][..., 1].mean())]
    report["ao"] = [float(v) for v in numpy.percentile(maps["arm"][..., 0], [1, 50, 99])] + [float(maps["arm"][..., 0].mean())]
    report["height"] = [float(v) for v in numpy.percentile(height, [0.5, 50, 99.5])] + [float(height.mean()), float(height.min()), float(height.max())]
    report["albedo"] = [float(v) for v in linear.reshape(-1, 3).mean(axis=0)]
    report["luminance"] = float(kit.luminance(linear).mean())
    return report


def verdict(report):
    failures = []
    if report["missing"]:
        return ["missing " + ",".join(report["missing"])]
    for key, suffix, channels in suffixes:
        shape = report["sizes"][key]
        if shape[0] != 2048 or shape[1] != 2048 or shape[2] != channels:
            failures.append("%s is %s" % (suffix, "x".join(str(v) for v in shape)))
    for key, (overall, local, limit) in report["seam"].items():
        if local > max(limit, 1.05) or overall > 1.5:
            failures.append("%s seam %.2f adjacent %.2f limit %.2f" % (key, overall, local, limit))
    if abs(report["length_mean"] - 1.0) > 0.01 or report["length_mid"] > 0.03 or report["length_off"] > 0.15:
        failures.append("normal length %.3f mid %.3f off %.3f" % (report["length_mean"], report["length_mid"], report["length_off"]))
    if report["up_low"] <= 0.0:
        failures.append("normal points down")
    if min(report["orientation"]) < 0.25:
        failures.append("normal orientation %.2f %.2f" % report["orientation"])
    if report["metal_mean"] > 0.012 or report["metal_high"] > 0.08:
        failures.append("metal %.4f high %.3f" % (report["metal_mean"], report["metal_high"]))
    if not (0.15 <= report["rough"][3] <= 0.98 and report["rough"][0] >= 0.02):
        failures.append("roughness range")
    if not (0.4 <= report["ao"][3] <= 0.995 and report["ao"][2] >= 0.85 and report["ao"][0] < report["ao"][2]):
        failures.append("occlusion range")
    if report["height"][2] - report["height"][0] < 0.6 or abs(report["height"][3] - 0.5) > 0.06:
        failures.append("height span %.2f mean %.2f" % (report["height"][2] - report["height"][0], report["height"][3]))
    if not 0.015 <= report["luminance"] <= 0.7:
        failures.append("albedo %.3f" % report["luminance"])
    return failures


def describe(report, failures):
    lines = ["CHECK %-16s %s" % (report["name"], "PASS" if not failures else "FAIL " + "; ".join(failures))]
    if not report["missing"]:
        lines.append("  seam: wrap vs mean row step / wrap vs adjacent rows (p99 of interior 8x8-block-boundary rows) " + "  ".join("%s %.3f / %.3f (%.3f)" % (key, value[0], value[1], value[2]) for key, value in report["seam"].items()))
        lines.append("  normal length %.4f median off %.4f p99 off %.4f up mean %.3f min %.3f  orientation red %.2f green %.2f" % (report["length_mean"], report["length_mid"], report["length_off"], report["up_mean"], report["up_low"], report["orientation"][0], report["orientation"][1]))
        lines.append("  metal mean %.4f p99.9 %.3f peak %.3f  rough p1 %.2f p50 %.2f p99 %.2f mean %.3f  ao p1 %.2f p50 %.2f p99 %.2f mean %.3f" % tuple([report["metal_mean"], report["metal_high"], report["metal_peak"]] + report["rough"] + report["ao"]))
        lines.append("  height p0.5 %.3f p50 %.3f p99.5 %.3f mean %.3f min %.3f max %.3f  albedo %.3f %.3f %.3f lum %.3f" % tuple(report["height"] + report["albedo"] + [report["luminance"]]))
    return "\n".join(lines)


def run(directory, names, reference="forest_leaves_02"):
    path = os.path.join(directory, reference)
    if os.path.isdir(path):
        normal = kit.read_image(os.path.join(path, reference + "_nor_dx_2k.jpg")).astype(numpy.float32) / 255.0
        height = kit.read_image(os.path.join(path, reference + "_disp_2k.jpg")).astype(numpy.float32)[..., 0] / 255.0
        print("CHECK reference %s orientation red %.2f green %.2f" % ((reference,) + orientation(normal, height)), flush=True)
    failed = []
    for name in names:
        report = measure(directory, name)
        failures = verdict(report)
        print(describe(report, failures), flush=True)
        if failures:
            failed.append(name)
    return failed
