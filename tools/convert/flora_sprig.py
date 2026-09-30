import bpy
import bmesh
import json
import math
import os
import random
import numpy
from contextlib import contextmanager
from mathutils import Matrix, Vector

import flora_kit as kit


def basis(origin, forward, hint=None, roll=0.0):
    forward = forward.normalized()
    hint = Vector((0.0, 0.0, 1.0)) if hint is None else hint
    right = forward.cross(hint)
    if right.length < 1e-4:
        right = forward.cross(Vector((1.0, 0.0, 0.0)))
        if right.length < 1e-4:
            right = forward.cross(Vector((0.0, 1.0, 0.0)))
    right.normalize()
    up = right.cross(forward).normalized()
    if roll:
        rotation = Matrix.Rotation(roll, 3, forward)
        right = rotation @ right
        up = rotation @ up
    return Matrix(((right.x, forward.x, up.x, origin.x), (right.y, forward.y, up.y, origin.y), (right.z, forward.z, up.z, origin.z), (0.0, 0.0, 0.0, 1.0)))


def leaf_style(**overrides):
    style = {
        "outline": lambda t, side: math.sin(math.pi * t) ** 0.6,
        "rows": 20,
        "columns": (-1.0, -0.62, -0.28, -0.07, 0.07, 0.28, 0.62, 1.0),
        "petiole": 0.08,
        "stalk": 0.03,
        "fold": 0.12,
        "cup": 0.0,
        "curl": 0.25,
        "twist": 0.0,
        "sweep": 0.0,
        "wave": 0.0,
        "wave_count": 3.0,
        "quilt": 0.006,
        "veins": 7.0,
        "slant": 1.6,
        "vein_width": 0.2,
        "vein_strength": 0.5,
        "midrib_width": 0.08,
        "front": ((0.05, 0.11, 0.028), (0.06, 0.13, 0.03)),
        "back": ((0.09, 0.15, 0.06), (0.10, 0.16, 0.065)),
        "vein": (0.14, 0.2, 0.07),
        "stem": (0.12, 0.16, 0.05),
        "edge": None,
        "edge_strength": 0.0,
        "rough": 0.55,
        "back_rough": 0.7,
    }
    style.update(overrides)
    return style


class sprig_c:
    def __init__(self):
        self.bm = bmesh.new()
        self.layer = self.bm.verts.layers.float_color.new("tint")
        self.matrix = Matrix.Identity(4)
        self.lite = False

    @contextmanager
    def place(self, matrix):
        saved = self.matrix
        self.matrix = saved @ matrix
        try:
            yield
        finally:
            self.matrix = saved

    def vert(self, point, color):
        vert = self.bm.verts.new(self.matrix @ point)
        vert[self.layer] = color
        return vert

    def tube(self, points, radius_start, radius_end, color_start, color_end=None, rough=0.85, sides=6, crest=None, power=1.0):
        color_end = color_start if color_end is None else color_end
        points = [self.matrix @ point for point in points]
        scale = self.matrix.to_scale().x
        count = len(points)
        frames = kit.frames(points, Vector((0.0, 0.0, 1.0)) if crest is None else crest)
        rings = []
        for index, point in enumerate(points):
            t = index / max(count - 1, 1)
            radius = (radius_start + (radius_end - radius_start) * t ** power) * scale
            tangent, side, normal = frames[index]
            color = kit.mix(color_start, color_end, t) + (rough,)
            ring = []
            for step in range(sides):
                angle = math.tau * step / sides
                vert = self.bm.verts.new(point + (side * math.cos(angle) + normal * math.sin(angle)) * radius)
                vert[self.layer] = color
                ring.append(vert)
            rings.append(ring)
        for index in range(count - 1):
            for step in range(sides):
                self.bm.faces.new((rings[index][step], rings[index][(step + 1) % sides], rings[index + 1][(step + 1) % sides], rings[index + 1][step]))
        tip = self.bm.verts.new(points[-1] + frames[-1][0] * radius_end * scale * 1.5)
        tip[self.layer] = kit.mix(color_start, color_end, 1.0) + (rough,)
        for step in range(sides):
            self.bm.faces.new((rings[-1][step], rings[-1][(step + 1) % sides], tip))

    def leaf(self, style, length, width, tone=(1.0, 1.0, 1.0), wash=None, curl=None, fold=None, twist=None):
        rows = max(6, style["rows"] // 3) if self.lite else style["rows"]
        columns = (-1.0, -0.4, 0.4, 1.0) if self.lite else style["columns"]
        outline = style["outline"]
        facing = (self.matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))).z >= 0.0
        base, tip = style["front"] if facing else style["back"]
        rough = style["rough"] if facing else style["back_rough"]
        vein_color = style["vein"]
        curl = style["curl"] if curl is None else curl
        fold = style["fold"] if fold is None else fold
        twist = style["twist"] if twist is None else twist
        petiole = style["petiole"] * length
        half = width * 0.5
        if petiole > 0.0:
            stem = tuple(style["stem"][index] * tone[index] for index in range(3))
            self.tube([Vector((0.0, 0.0, 0.0)), Vector((0.0, petiole * 0.5, petiole * 0.04)), Vector((0.0, petiole, 0.0))], style["stalk"] * width, style["stalk"] * width * 0.7, stem, stem, 0.7, 4)
        y = petiole
        z = 0.0
        grid = []
        fold_tangent = math.tan(fold)
        wave_phase = random.random() * math.tau
        for row in range(rows + 1):
            t = row / rows
            theta = curl * t ** 1.5
            if row:
                middle = curl * ((row - 0.5) / rows) ** 1.5
                y += math.cos(middle) * length / rows
                z -= math.sin(middle) * length / rows
            shade = kit.mix(base, tip, t ** 1.4)
            line = []
            for u in columns:
                side = -1.0 if u < 0.0 else 1.0
                reach = max(outline(t, side), 0.015) * half
                x = u * reach
                lift = abs(x) * fold_tangent - style["cup"] * x * x / max(half, 1e-6)
                if style["wave"]:
                    lift += style["wave"] * width * math.sin(math.tau * style["wave_count"] * t + wave_phase + (0.0 if side < 0.0 else 2.1)) * abs(u) ** 1.5
                phase = t * style["veins"] - abs(u) * style["slant"] * reach / max(half, 1e-6)
                distance = abs(phase - math.floor(phase + 0.5))
                vein = kit.smooth(style["vein_width"], 0.0, distance) * (1.0 - t ** 3) if abs(u) > style["midrib_width"] + 1e-6 else 1.0
                lift += style["quilt"] * width * (math.cos(distance * math.tau) * -0.5) * min(1.0, abs(u) * 3.0)
                ahead = style["sweep"] * abs(x)
                if twist:
                    angle = twist * t
                    x, lift = x * math.cos(angle) - lift * math.sin(angle), x * math.sin(angle) + lift * math.cos(angle)
                point = Vector((x, y + ahead * math.cos(theta) + lift * math.sin(theta), z - ahead * math.sin(theta) + lift * math.cos(theta)))
                color = kit.mix(shade, vein_color, vein * style["vein_strength"])
                if style["edge"] is not None:
                    color = kit.mix(color, style["edge"], kit.smooth(0.6, 1.0, abs(u)) * style["edge_strength"])
                color = tuple(color[index] * tone[index] for index in range(3))
                if wash is not None:
                    color = kit.mix(color, wash[0], wash[1])
                line.append(self.vert(point, color + (rough,)))
            grid.append(line)
        for row in range(rows):
            for column in range(len(columns) - 1):
                self.bm.faces.new((grid[row][column], grid[row][column + 1], grid[row + 1][column + 1], grid[row + 1][column]))

    def blob(self, center, radii, color_top, color_bottom=None, rough=0.5, segments=10, rings=6, axis=None):
        color_bottom = color_top if color_bottom is None else color_bottom
        frame = basis(center, Vector((0.0, 0.0, 1.0)) if axis is None else axis)
        matrix = self.matrix @ frame
        lines = []
        for ring in range(rings + 1):
            polar = math.pi * ring / rings
            color = kit.mix(color_top, color_bottom, ring / rings) + (rough,)
            line = []
            for segment in range(segments):
                azimuth = math.tau * segment / segments
                vert = self.bm.verts.new(matrix @ Vector((math.sin(polar) * math.cos(azimuth) * radii[0], math.cos(polar) * radii[2], math.sin(polar) * math.sin(azimuth) * radii[1])))
                vert[self.layer] = color
                line.append(vert)
            lines.append(line)
        for ring in range(rings):
            for segment in range(segments):
                self.bm.faces.new((lines[ring][segment], lines[ring][(segment + 1) % segments], lines[ring + 1][(segment + 1) % segments], lines[ring + 1][segment]))

    def lathe(self, profile, segments=10, rough=0.6, squash=1.0):
        lines = []
        for radius, height, color in profile:
            line = []
            for segment in range(segments):
                azimuth = math.tau * segment / segments
                line.append(self.vert(Vector((math.cos(azimuth) * radius, height, math.sin(azimuth) * radius * squash)), tuple(color) + (rough,)))
            lines.append(line)
        for ring in range(len(lines) - 1):
            for segment in range(segments):
                self.bm.faces.new((lines[ring][segment], lines[ring + 1][segment], lines[ring + 1][(segment + 1) % segments], lines[ring][(segment + 1) % segments]))

    def fan(self, points, color, rough=0.6):
        verts = [self.vert(point, tuple(color) + (rough,)) for point in points]
        if len(verts) >= 3:
            self.bm.faces.new(verts)

    def strip(self, points, widths, colors, rough=0.6, normal=None, fold=0.0):
        count = len(points)
        rows = []
        for index in range(count):
            tangent = (points[min(index + 1, count - 1)] - points[max(index - 1, 0)]).normalized()
            hint = Vector((0.0, 0.0, 1.0)) if normal is None else normal
            side = tangent.cross(hint)
            if side.length < 1e-4:
                side = tangent.cross(Vector((1.0, 0.0, 0.0)))
            side.normalize()
            up = side.cross(tangent).normalized()
            color = tuple(colors[index]) + (rough,)
            half = widths[index] * 0.5
            rows.append((self.vert(points[index] - side * half + up * half * fold, color), self.vert(points[index], color), self.vert(points[index] + side * half + up * half * fold, color)))
        for index in range(count - 1):
            self.bm.faces.new((rows[index][0], rows[index][1], rows[index + 1][1], rows[index + 1][0]))
            self.bm.faces.new((rows[index][1], rows[index][2], rows[index + 1][2], rows[index + 1][1]))

    def bounds(self):
        xs = [vert.co.x for vert in self.bm.verts]
        ys = [vert.co.y for vert in self.bm.verts]
        return min(xs), min(ys), max(xs), max(ys)

    def finish(self, name):
        bmesh.ops.triangulate(self.bm, faces=[face for face in self.bm.faces if len(face.verts) > 4])
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


class atlas_c:
    def __init__(self, species, part="leaf", size=kit.atlas_size):
        self.species = species
        self.part = part
        self.size = size
        self.cells = []

    def cell(self, name, rect, builder, seed=1, margin=0.02, gain=1.0, occlusion=0.035, pin=None):
        self.cells.append({"name": name, "rect": rect, "builder": builder, "seed": seed, "margin": margin, "gain": gain, "occlusion": occlusion, "pin": pin})

    def render(self, shade_floor=0.2, shade_mix=0.5):
        kit.reset()
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        kit.accelerate(scene)
        scene.render.resolution_x = self.size
        scene.render.resolution_y = self.size
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        scene.cycles.use_denoising = False
        scene.cycles.filter_width = 1.0
        scene.cycles.max_bounces = 0
        scene.display_settings.display_device = 'sRGB'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
        world = bpy.data.worlds.new("black")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.0
        scene.world = world
        camera_data = bpy.data.cameras.new("atlas")
        camera_data.type = 'ORTHO'
        camera_data.ortho_scale = 1.0
        camera_data.clip_start = 0.1
        camera_data.clip_end = 200.0
        camera = bpy.data.objects.new("atlas", camera_data)
        camera.location = Vector((0.5, 0.5, 100.0))
        scene.collection.objects.link(camera)
        scene.camera = camera
        objects = []
        records = {}
        pad = 3.0 / self.size
        for cell in self.cells:
            random.seed(cell["seed"])
            sprig = sprig_c()
            cell["builder"](sprig, random.Random(cell["seed"]))
            low_x, low_y, high_x, high_y = sprig.bounds()
            if cell["pin"] is not None:
                low_x, low_y, high_x, high_y = cell["pin"]
            x0, y0, x1, y1 = cell["rect"]
            margin = cell["margin"] * max(high_x - low_x, high_y - low_y)
            width = high_x - low_x + margin * 2.0
            height = high_y - low_y + margin * 2.0
            scale = min((x1 - x0 - pad * 2.0) / width, (y1 - y0 - pad * 2.0) / height)
            offset_x = (x0 + x1) * 0.5 - (low_x + high_x) * 0.5 * scale
            offset_y = (y0 + y1) * 0.5 - (low_y + high_y) * 0.5 * scale
            obj = sprig.finish(cell["name"])
            obj.scale = (scale, scale, scale)
            obj.location = Vector((offset_x, offset_y, 0.0))
            objects.append((obj, cell, scale))
            left = offset_x + (low_x - margin) * scale
            bottom = offset_y + (low_y - margin) * scale
            records[cell["name"]] = {"rect": [left, bottom, left + width * scale, bottom + height * scale], "size": [width, height], "anchor": [margin - low_x, margin - low_y], "scale": scale}
            print("CELL", cell["name"], len(obj.data.polygons), round(width, 3), round(height, 3))
        directory = kit.texture_directory(self.species)
        os.makedirs(directory, exist_ok=True)
        scratch = os.path.join(kit.species_directory(self.species), "render_pass.png")
        passes = {}
        for name, builder, transform, samples in (("albedo", kit.tint_color, 'Standard', 48), ("normal", kit.normal_color, 'Raw', 32), ("rough", kit.tint_alpha, 'Raw', 16), ("occlusion", None, 'Raw', 96)):
            for obj, cell, scale in objects:
                material = kit.emission_material(name + "_" + cell["name"], builder if builder else kit.occlusion_color(cell["occlusion"] * scale))
                obj.data.materials.clear()
                obj.data.materials.append(material)
            scene.view_settings.view_transform = transform
            scene.cycles.samples = samples
            scene.render.filepath = scratch
            bpy.ops.render.render(write_still=True)
            passes[name] = kit.load_pixels(scratch)
        os.remove(scratch)
        alpha = passes["albedo"][:, :, 3].copy()
        for obj, cell, scale in objects:
            if cell["gain"] != 1.0:
                x0, y0, x1, y1 = cell["rect"]
                rows = slice(int(y0 * self.size), int(y1 * self.size))
                columns = slice(int(x0 * self.size), int(x1 * self.size))
                alpha[rows, columns] = numpy.clip(alpha[rows, columns] * cell["gain"], 0.0, 1.0)
        shade = numpy.clip(kit.flood(passes["occlusion"][:, :, :1], passes["occlusion"][:, :, 3])[:, :, 0], 0.0, 1.0)
        color = kit.flood(passes["albedo"][:, :, :3], passes["albedo"][:, :, 3])
        color = color * (shade[:, :, None] * (1.0 - shade_floor) + shade_floor) ** shade_mix
        normal = kit.flood(passes["normal"][:, :, :3], passes["normal"][:, :, 3]) * 2.0 - 1.0
        normal[:, :, 2] = numpy.maximum(normal[:, :, 2], 0.05)
        normal = normal / numpy.maximum(numpy.linalg.norm(normal, axis=2, keepdims=True), 1e-6)
        rough = numpy.clip(kit.flood(passes["rough"][:, :, :1], passes["rough"][:, :, 3])[:, :, 0], 0.05, 1.0)
        textures = kit.texture_set(self.species, self.part)
        kit.write_png(textures["diff"], numpy.concatenate([color, alpha[:, :, None]], axis=2))
        kit.write_png(textures["alpha"], numpy.repeat(alpha[:, :, None], 3, axis=2))
        kit.write_png(textures["nor_gl"], normal * 0.5 + 0.5)
        kit.write_png(textures["arm"], numpy.stack([shade * 0.75 + 0.25, rough, numpy.zeros_like(rough)], axis=2))
        with open(os.path.join(kit.species_directory(self.species), "flora_%s_%s.json" % (self.species, self.part)), "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=1)
        cut = (alpha > 0.5).astype(numpy.float32)[:, :, None]
        checker = ((numpy.indices(alpha.shape).sum(axis=0) // 64) % 2).astype(numpy.float32)[:, :, None] * 0.05 + 0.2
        preview = color * cut + checker * (1.0 - cut)
        os.makedirs(kit.preview_root, exist_ok=True)
        kit.write_png(os.path.join(kit.preview_root, "%s_atlas.png" % self.species if self.part == "leaf" else "%s_%s_atlas.png" % (self.species, self.part)), preview[::2, ::2])
        print("ATLAS", self.species, self.part, float((alpha > 0.5).mean()))
        return records


def load_cells(species, part="leaf"):
    with open(os.path.join(kit.species_directory(species), "flora_%s_%s.json" % (species, part)), "r", encoding="utf-8") as handle:
        return json.load(handle)
