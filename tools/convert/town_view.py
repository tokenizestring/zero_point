import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildkit as kit
import town_kit as tk
import town_library as lib
from buildkit import V


def material_triangles(build):
    totals = {}
    for part in build.parts.values():
        for face, slot in zip(part.faces, part.face_slots):
            name = part.slots[slot]
            totals[name] = totals.get(name, 0) + len(face) - 2
    return sorted(totals.items(), key=lambda item: -item[1])


def export(name, maker, far_maker, hero=None):
    kit.load_catalog()
    lib.register()
    if hero is not None:
        hero()
    kit.reset_scene()
    started = time.time()
    b = maker()
    objects = b.finish()
    path, document = kit.export_building("bld_" + name, objects)
    triangles, markers, materials, problems = kit.audit(path, document)
    print("BUILD", name, "tris", triangles, "parts", len(b.parts), "boxes", len(b.boxes), round(time.time() - started, 1), "s", flush=True)
    for key, part in sorted(b.parts.items(), key=lambda item: -item[1].triangles()):
        print("  PART", part.name, part.triangles(), "tris", len(part.slots), "materials", flush=True)
    print("  MATERIALS", " ".join("%s:%d" % item for item in material_triangles(b)), flush=True)
    kit.reset_scene()
    far = far_maker()
    objects = far.finish()
    path, document = kit.export_building("bld_" + name + "_far", objects)
    kit.audit(path, document)
    return triangles, markers


def remove(obj):
    kit.bpy.data.objects.remove(obj)


def preview(name, spec, which, samples):
    kit.reset_scene()
    kit.load_catalog()
    lib.register()
    objects = kit.import_building("bld_" + name)
    visual = [obj for obj in objects if obj.type == 'MESH' and not kit.is_marker(obj.name)]
    boxes = []
    for obj in objects:
        if obj.type == 'MESH' and kit.is_marker(obj.name):
            obj.hide_render = True
            low, high = kit.world_bounds([obj])
            boxes.append((obj.name, low, high))
    low, high = kit.world_bounds(visual)
    os.makedirs(kit.preview_root, exist_ok=True)
    kit.daylight(1.0, 3.4, spec.get("sun", (0.5, 0.62, -0.6)))
    kit.ground(-0.15, 400.0)
    prefix = os.path.join(kit.preview_root, "bld_" + name + "_")
    shots = spec.get("shots", {})
    rooms = spec.get("rooms", {})
    todo = which or (["front", "back"] + list(shots) + list(rooms) + ["plan", "far"])
    core_low, core_high = kit.world_bounds([obj for obj in visual if obj.name.endswith(("_shell", "_roof"))] or visual)
    target = V((core_low.x + core_high.x) * 0.5, (core_low.y + core_high.y) * 0.5, (core_high.z - 0.12) * 0.5)
    corners = [V(x, y, z) for x in (core_low.x, core_high.x) for y in (core_low.y, core_high.y) for z in (-0.12, core_high.z)]
    front_view = None
    kit.render_settings(samples, (1600, 900), spec.get("outside", 0.0))
    for key, direction in (("front", spec.get("front_dir", V(0.62, -0.9, 0.22))), ("back", spec.get("back_dir", V(-0.7, 0.85, 0.3)))):
        if key in todo or (key == "front" and "far" in todo):
            cam = kit.camera(target + direction.normalized() * 4.0, target, 35.0)
            kit.fit_camera(cam, corners, spec.get("margin", 0.05))
            if key in todo:
                kit.shoot(prefix + key + ".png")
            if key == "front":
                front_view = cam.location.copy()
            remove(cam)
    for key, (position, aim, lens) in shots.items():
        if key not in todo:
            continue
        cam = kit.camera(V(*position), V(*aim), lens)
        kit.shoot(prefix + key + ".png")
        remove(cam)
    for key, entry in rooms.items():
        if key not in todo:
            continue
        position, aim, lens = entry[:3]
        fill = entry[3] if len(entry) > 3 else spec.get("fill", 16.0)
        position = V(*position)
        kit.render_settings(samples, (1280, 720), spec.get("exposure", 2.6))
        cam = kit.camera(position, V(*aim), lens, None, 0.03)
        light = kit.point_light(position + V(0.0, 0.0, 0.3), fill, 0.4, (1.0, 0.93, 0.85))
        kit.shoot(prefix + key + ".png")
        remove(cam)
        remove(light)
        kit.render_settings(samples, (1600, 900), spec.get("outside", 0.0))
    if "plan" in todo:
        kit.plan_sheet(name, spec["levels"], boxes, low, high, max(24, samples // 2), prefix + "plan.png")
    if "far" in todo and front_view is not None:
        for obj in visual:
            obj.hide_render = True
        kit.import_building("bld_" + name + "_far")
        kit.render_settings(samples, (1600, 900), spec.get("outside", 0.0))
        cam = kit.camera(front_view, target, 35.0)
        kit.shoot(prefix + "far.png")
        remove(cam)


def sheet(names, views):
    rows = []
    for name in names:
        prefix = os.path.join(kit.preview_root, "bld_" + name + "_")
        rows.append((name, [(label, prefix + label + ".png") for label in views.get(name, ("front", "back", "plan", "far"))]))
    kit.contact_sheet(rows, os.path.join(kit.preview_root, "town_sheet.png"))
