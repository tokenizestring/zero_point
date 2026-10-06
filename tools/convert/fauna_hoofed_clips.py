import math
import numpy
import fauna_hoofed_motion as motion

rx = motion.rx
ry = motion.ry
rz = motion.rz
turn = motion.turn
legs = ("fore_l", "fore_r", "hind_l", "hind_r")
hooves = {"fore_l": "hoof_f_l", "fore_r": "hoof_f_r", "hind_l": "hoof_h_l", "hind_r": "hoof_h_r"}


def hermite(a, b, va, vb, t):
    t2 = t * t
    t3 = t2 * t
    return (2.0 * t3 - 3.0 * t2 + 1.0) * a + (t3 - 2.0 * t2 + t) * va + (3.0 * t2 - 2.0 * t3) * b + (t3 - t2) * vb


def bell(t, power=1.0):
    return math.sin(math.pi * min(max(t, 0.0), 1.0) ** power) ** 2


def keyed(time, keys):
    if time <= keys[0][0]:
        return numpy.asarray(keys[0][1], dtype=numpy.float64)
    for index in range(len(keys) - 1):
        t0, v0 = keys[index]
        t1, v1 = keys[index + 1]
        if time <= t1:
            return numpy.asarray(v0, dtype=numpy.float64) + (numpy.asarray(v1, dtype=numpy.float64) - numpy.asarray(v0, dtype=numpy.float64)) * motion.smoother((time - t0) / (t1 - t0))
    return numpy.asarray(keys[-1][1], dtype=numpy.float64)


def cycle(time, period, offset=0.0):
    return 0.5 - 0.5 * math.cos(2.0 * math.pi * (time / period - offset))


class actor:
    def __init__(self, blueprint):
        self.rig = motion.rig(blueprint)
        self.k = self.rig.scale
        self.style = blueprint["motion"]
        self.prefix = blueprint["motion"]["prefix"]
        r = self.rig
        self.home = {key: r.rest[r.slot[r.limbs[key].names[-1]]].copy() for key in legs}
        self.trunk = float(numpy.linalg.norm((r.rest[r.slot["scapula_l"]] - r.rest[r.slot["hips"]])[1:]))
        self.worst = 0.0
        self.girth = {}
        for name in ("hips", "spine_02", "spine_03"):
            origin = r.rest[r.slot[name]][None, :] / self.k
            down, found = blueprint["field"].cast(origin, numpy.array([[0.0, 0.0, -1.0]]), 0.9, ("core",), steps=240)
            wide, found = blueprint["field"].cast(origin, numpy.array([[1.0, 0.0, 0.0]]), 0.6, ("core",), steps=240)
            self.girth[name] = (float(down[0]) * self.k, float(wide[0]) * self.k)

    def body_low(self, world, place):
        low = 9.0
        for name, (depth, width) in self.girth.items():
            slot = self.rig.slot[name]
            reach = math.sqrt((depth * world[slot][2, 2]) ** 2 + (width * world[slot][2, 0]) ** 2)
            low = min(low, place[slot][2] - reach)
        return low

    def legs_low(self, world, place, keys):
        low = 9.0
        radii = self.style.get("joint_radius", (0.06, 0.036, 0.03, 0.03))
        for key in keys:
            leg = self.rig.limbs[key]
            for name, radius in zip(leg.names[-4:], radii):
                low = min(low, place[self.rig.slot[name]][2] - radius * self.k)
            low = min(low, min(point[2] for point in self.rig.points(key, world, place)))
        return low

    def settle(self, c, keys=(), body=True, lift=0.0):
        for attempt in range(6):
            local, shift, world, place, info = self.rig.solve(c)
            low = self.legs_low(world, place, keys) if keys else 9.0
            if body:
                low = min(low, self.body_low(world, place))
            if abs(low - lift) < 2e-4:
                break
            c["location"]["hips"] = c["location"].get("hips", numpy.zeros(3)) - numpy.array([0.0, 0.0, low - lift])
        return self.rig.solve(c)

    def lay(self, c, key, limit, lowest=0.0):
        index = 1 if key.startswith("fore") else 0
        leg = self.rig.limbs[key]
        span = sum(leg.lengths[index:])
        base = c["free"][key][index]
        angle = 0.0
        for attempt in range(10):
            c["free"][key][index] = ry(angle) @ base
            local, shift, world, place, info = self.rig.solve(c)
            low = self.legs_low(world, place, (key,))
            if abs(low - lowest) < 0.003:
                break
            angle = min(max(angle - (low - lowest) / span * 0.85, -math.radians(limit)), math.radians(limit))
        c["free"][key][index] = ry(angle) @ base
        return angle

    def stand(self, offsets=None):
        c = self.rig.blank()
        for key in legs:
            c["feet"][key] = {"position": self.home[key] + numpy.asarray((offsets or {}).get(key, (0.0, 0.0, 0.0))) * self.k}
        return c

    def trunk_pose(self, c, shift=(0.0, 0.0, 0.0), hips=(0.0, 0.0, 0.0), chest=None, flex=0.0):
        hips_matrix = turn(*hips)
        c["rotation"]["hips"] = hips_matrix
        c["location"]["hips"] = numpy.asarray(shift, dtype=numpy.float64) * self.k
        chest_matrix = turn(*chest) if chest is not None else hips_matrix
        step = motion.from_vector(motion.axis_angle(hips_matrix.T @ chest_matrix) / 3.0)
        for name, share in (("spine_01", 0.4), ("spine_02", 0.35), ("spine_03", 0.25)):
            c["rotation"][name] = step @ rx(math.radians(flex) * share)

    def neck_pose(self, c, pitch=0.0, yaw=0.0, roll=0.0, head=(0.0, 0.0, 0.0), jaw=0.0, shares=((0.5, 0.25), (0.3, 0.35), (0.2, 0.4))):
        for name, (lift, swing) in zip(("neck_01", "neck_02", "neck_03"), shares):
            c["rotation"][name] = turn(pitch * lift, yaw * swing, roll / 3.0)
        c["rotation"]["head"] = turn(*head)
        c["rotation"]["jaw"] = rx(math.radians(jaw))

    def ears(self, c, left=(0.0, 0.0), right=(0.0, 0.0)):
        c["rotation"]["ear_l"] = turn(left[0], left[1], 0.0)
        c["rotation"]["ear_r"] = turn(right[0], -right[1], 0.0)

    def tail_pose(self, c, lift=0.0, sway=0.0, curl=0.0):
        hang = self.style.get("tail_hang", len(self.rig.tail))
        for index, name in enumerate(self.rig.tail):
            swing = rz(math.radians(sway) * (0.6 + 0.4 * index)) if index < hang else ry(-math.radians(sway) * (0.6 + 0.4 * index))
            c["rotation"][name] = swing @ rx(math.radians(lift if index == 0 else curl))

    def breathe(self, c, amount):
        depth = amount * self.style.get("breath", 0.008) * self.k
        c["location"]["ribs_l"] = numpy.array([depth, 0.0, depth * 0.35])
        c["location"]["ribs_r"] = numpy.array([-depth, 0.0, depth * 0.35])

    def finish(self, c):
        rig = self.rig
        for attempt in range(12):
            local, shift, world, place, info = rig.solve(c)
            short = {hooves[key]: info["short"].get(hooves[key], 0.0) for key in legs if key in c["feet"] and c["feet"][key].get("planted", True)}
            fore = max(short.get("hoof_f_l", 0.0), short.get("hoof_f_r", 0.0))
            hind = max(short.get("hoof_h_l", 0.0), short.get("hoof_h_r", 0.0))
            if fore < 2e-5 and hind < 2e-5:
                break
            self.worst = max(self.worst, fore, hind)
            if hind > 0.0:
                c["location"]["hips"] = c["location"].get("hips", numpy.zeros(3)) + numpy.array([0.0, 0.0, -(hind * 1.2 + 0.0005)])
            if fore > 0.0:
                c["rotation"]["hips"] = c["rotation"].get("hips", numpy.eye(3)) @ rx((fore * 1.2 + 0.0005) / self.trunk)
        return local, shift, world, place

    def lowest(self, world, place):
        return min(min(point[2] for point in self.rig.points(key, world, place)) for key in legs)

    def pack(self, name, frames, loop, speed=0.0, events=(), contacts=None):
        local = numpy.array([frame[0] for frame in frames])
        shift = numpy.array([frame[1] for frame in frames])
        return {"name": self.prefix + name, "local": local, "shift": shift, "loop": loop, "speed": speed, "events": list(events), "contacts": contacts or {}, "frames": len(frames), "duration": (len(frames) - 1) / 30.0}

    def stride(self, name, spec):
        k = self.k
        count = spec["frames"]
        period = count / 30.0
        speed = spec["speed"]
        frames = []
        for f in range(count):
            p = f / count
            c = self.rig.blank()
            getattr(self, "body_" + spec["kind"])(c, p, spec)
            for key in legs:
                group = key[:4]
                duty = spec["duty"][group]
                phi = (p - spec["phase"][key]) % 1.0
                length = speed * duty * period
                center = self.home[key] + numpy.asarray(spec["center"][group]) * k
                center[0] = self.home[key][0] * spec["narrow"]
                front = center[1] - length * 0.5
                back = center[1] + length * 0.5
                foot = {"follow": spec.get("follow", 0.4)}
                if phi < duty:
                    s = phi / duty
                    foot["position"] = numpy.array([center[0], front + length * s, center[2]])
                    foot["pastern"] = -spec["sink"] * math.sin(math.pi * s)
                    foot["flex"] = spec["stance_flex"][group] * math.sin(math.pi * s)
                else:
                    t = (phi - duty) / (1.0 - duty)
                    pace = length * (1.0 - duty) / duty
                    lift = spec["lift"][group] * k
                    foot["planted"] = False
                    pitch = spec["toe"][group] * bell(t, 0.5) - spec.get("reach_toe", 0.15) * bell(min(max((t - 0.6) / 0.4, 0.0), 1.0))
                    foot["position"] = numpy.array([center[0], hermite(back, front, pace, pace, t), center[2] + lift * bell(t, spec.get("lift_skew", 0.8))])
                    foot["pitch"] = pitch
                    foot["pastern"] = spec["curl"][group] * bell(t, 0.55)
                    foot["flex"] = spec["swing_flex"][group] * bell(t, spec.get("flex_skew", 0.85))
                c["feet"][key] = foot
            for attempt in range(4):
                local, shift, world, place = self.finish(c)
                dip = 0.0
                for key in legs:
                    phi = (p - spec["phase"][key]) % 1.0
                    if phi >= spec["duty"][key[:4]]:
                        low = min(point[2] for point in self.rig.points(key, world, place))
                        if low < 0.004 * k:
                            c["feet"][key]["position"] = c["feet"][key]["position"] + numpy.array([0.0, 0.0, 0.004 * k - low])
                            dip = max(dip, 0.004 * k - low)
                if dip < 1e-5:
                    break
            frames.append((local, shift))
        frames.append(frames[0])
        contacts = {hooves[key]: [[spec["phase"][key] * period, (spec["phase"][key] + spec["duty"][key[:4]]) * period]] for key in legs}
        events = sorted([{"name": "foot", "time": round(spec["phase"][key] * period, 4)} for key in legs], key=lambda e: e["time"])
        return self.pack(name, frames, True, speed, events, contacts)

    def body_walk(self, c, p, spec):
        phase = spec["phase"]
        duty = spec["duty"]
        hind_mid = phase["hind_l"] + duty["hind"] * 0.5
        fore_mid = phase["fore_l"] + duty["fore"] * 0.5
        rise = spec["bob"]
        z_hips = rise * math.cos(4.0 * math.pi * (p - hind_mid))
        z_chest = rise * math.cos(4.0 * math.pi * (p - fore_mid))
        sway = spec["sway"] * math.cos(2.0 * math.pi * (p - 0.5 * (hind_mid + fore_mid)))
        pitch = math.degrees((z_chest - z_hips) * self.k / self.trunk)
        hips_roll = spec["roll"] * math.cos(2.0 * math.pi * (p - (phase["hind_l"] + duty["hind"] + (1.0 - duty["hind"]) * 0.5)))
        chest_roll = spec["roll"] * 0.6 * math.cos(2.0 * math.pi * (p - (phase["fore_l"] + duty["fore"] + (1.0 - duty["fore"]) * 0.5)))
        hips_yaw = -spec["yaw"] * math.cos(2.0 * math.pi * (p - phase["hind_l"]))
        chest_yaw = -spec["yaw"] * 0.7 * math.cos(2.0 * math.pi * (p - phase["fore_l"]))
        self.trunk_pose(c, (sway, 0.0, z_hips), (pitch, hips_yaw, hips_roll), (pitch, chest_yaw, chest_roll))
        nod = spec["nod"] * math.cos(4.0 * math.pi * (p - fore_mid - 0.06))
        self.neck_pose(c, -nod - pitch * 0.5, -chest_yaw * 0.9, -chest_roll * 0.5, (nod * 0.55 - pitch * 0.5, -chest_yaw * 0.1, -chest_roll * 0.5))
        self.ears(c, (2.0 * math.sin(4.0 * math.pi * p), 0.0), (2.0 * math.sin(4.0 * math.pi * p + 1.0), 0.0))
        self.tail_pose(c, 0.0, spec.get("tail", 7.0) * math.sin(2.0 * math.pi * (p - 0.12)), 0.0)
        self.breathe(c, cycle(p, 0.5))

    def body_trot(self, c, p, spec):
        duty = spec["duty"]["hind"]
        drop = -spec["bob"] * math.cos(4.0 * math.pi * (p - spec["phase"]["hind_l"] - duty * 0.5))
        pitch = spec.get("pitch", 0.8) * math.sin(4.0 * math.pi * (p - 0.05))
        roll = spec["roll"] * math.sin(2.0 * math.pi * (p - 0.1))
        yaw = spec["yaw"] * math.sin(2.0 * math.pi * p)
        self.trunk_pose(c, (0.0, 0.0, drop), (pitch, -yaw, roll), (pitch, yaw, -roll * 0.6))
        nod = spec["nod"] * math.cos(4.0 * math.pi * (p - spec["phase"]["hind_l"] - duty * 0.5 - 0.1))
        self.neck_pose(c, spec.get("carry", -6.0) + nod - pitch * 0.6, -yaw * 0.9, roll * 0.3, (-nod * 0.7 - pitch * 0.4 - spec.get("carry", -6.0) * 0.5, 0.0, roll * 0.3))
        self.ears(c, (6.0 + 3.0 * math.sin(4.0 * math.pi * p), 4.0), (6.0 + 3.0 * math.sin(4.0 * math.pi * p + 0.8), 4.0))
        self.tail_pose(c, 8.0 + 6.0 * math.sin(4.0 * math.pi * (p - 0.2)), 5.0 * math.sin(2.0 * math.pi * (p - 0.15)), 3.0)
        self.breathe(c, cycle(p, 0.5))

    def body_gallop(self, c, p, spec):
        phase = spec["phase"]
        duty = spec["duty"]
        hind_mid = 0.5 * (phase["hind_l"] + phase["hind_r"]) + duty["hind"] * 0.5
        fore_mid = 0.5 * (phase["fore_l"] + phase["fore_r"]) + duty["fore"] * 0.5
        z_hips = -spec["bob"] * math.cos(2.0 * math.pi * (p - hind_mid)) + spec.get("hover", 0.0)
        z_chest = -spec["bob"] * math.cos(2.0 * math.pi * (p - fore_mid)) + spec.get("hover", 0.0)
        pitch = math.degrees((z_chest - z_hips) * self.k / self.trunk)
        flex = spec["flex"] * math.cos(2.0 * math.pi * (p - spec.get("gather", 0.89)))
        roll = spec["roll"] * math.sin(2.0 * math.pi * (p - 0.2))
        self.trunk_pose(c, (0.0, spec.get("surge", 0.0) * math.sin(2.0 * math.pi * (p - hind_mid)), z_hips), (pitch + flex * 0.45, 0.0, roll), (pitch - flex * 0.55, 0.0, -roll * 0.5))
        chest_pitch = pitch - flex * 0.55
        nod = spec["nod"] * math.cos(2.0 * math.pi * (p - fore_mid - 0.08))
        self.neck_pose(c, spec.get("carry", -14.0) - chest_pitch * 0.7 + nod, 0.0, roll * 0.3, (-spec.get("carry", -14.0) * 0.55 - chest_pitch * 0.25 - nod * 0.6, 0.0, 0.0))
        self.ears(c, (22.0 + 5.0 * math.sin(2.0 * math.pi * p), 12.0), (22.0 + 5.0 * math.sin(2.0 * math.pi * p + 0.6), 12.0))
        self.tail_pose(c, spec.get("flag", 50.0) + 14.0 * math.sin(2.0 * math.pi * (p - hind_mid - 0.2)), 6.0 * math.sin(2.0 * math.pi * p), 10.0 * math.sin(2.0 * math.pi * (p - hind_mid - 0.3)))
        self.breathe(c, cycle(p, 1.0, 0.3))

    def idle(self, seconds=5.0):
        style = self.style
        count = int(round(seconds * 30))
        frames = []
        for f in range(count):
            t = f / 30.0
            c = self.stand()
            breath = cycle(t, seconds / 2.0)
            lean = math.sin(2.0 * math.pi * t / seconds)
            self.trunk_pose(c, (0.014 * lean, 0.0, 0.002 * breath - 0.004 * lean * lean), (0.25 * breath, 0.6 * lean, 0.9 * lean), (0.25 * breath, -0.4 * lean, 0.5 * lean))
            glance = math.sin(2.0 * math.pi * t / seconds) * cycle(t, seconds)
            self.neck_pose(c, 1.2 * cycle(t, seconds) - 0.6 * breath, 5.0 * glance, 0.0, (-0.8 * cycle(t, seconds), 3.0 * glance, 0.0), style.get("chew", 0.0) * cycle(t, 0.8) * bell((t % seconds) / seconds, 1.0))
            left = motion.pulse(t, 1.1, 0.3) + 0.7 * motion.pulse(t, 1.45, 0.25)
            right = motion.pulse(t, 3.3, 0.32) + 0.5 * motion.pulse(t, 4.1, 0.3)
            self.ears(c, (-14.0 * left, -26.0 * left), (-10.0 * right, -24.0 * right))
            flick = motion.pulse(t, 2.2, 0.7)
            self.tail_pose(c, 10.0 * flick, 26.0 * flick * math.sin(2.0 * math.pi * (t - 2.2) / 0.35), 6.0 * flick)
            self.breathe(c, breath)
            frames.append(self.finish(c)[:2])
        frames.append(frames[0])
        return self.pack("idle", frames, True)

    def idle_look(self, seconds=4.0):
        count = int(round(seconds * 30))
        frames = []
        for f in range(count):
            t = f / 30.0
            c = self.stand()
            yaw = float(keyed(t, [(0.0, 0.0), (0.25, 0.0), (0.95, 58.0), (1.6, 60.0), (2.5, -52.0), (3.1, -55.0), (3.8, 0.0), (4.0, 0.0)]))
            lift = float(keyed(t, [(0.0, 0.0), (0.9, 5.0), (1.6, 5.0), (2.1, 1.0), (2.6, 6.0), (3.1, 6.0), (3.8, 0.0), (4.0, 0.0)]))
            breath = cycle(t, 2.0)
            lean = yaw / 60.0
            self.trunk_pose(c, (0.008 * lean, 0.0, 0.002 * breath), (0.2 * breath, 1.0 * lean, 0.4 * lean), (0.2 * breath + 0.3 * abs(lean), 3.0 * lean, 0.0))
            self.neck_pose(c, lift, yaw * 0.62, 0.0, (-lift * 0.4, yaw * 0.34, -4.0 * lean))
            perk = abs(lean)
            self.ears(c, (-10.0 * perk - 10.0 * motion.pulse(t, 1.9, 0.3), -16.0 * perk), (-10.0 * perk - 12.0 * motion.pulse(t, 3.4, 0.3), -16.0 * perk))
            self.tail_pose(c, 4.0 * perk, 6.0 * math.sin(2.0 * math.pi * t / 2.0) * perk, 0.0)
            self.breathe(c, breath)
            frames.append(self.finish(c)[:2])
        frames.append(frames[0])
        return self.pack("idle_look", frames, True)

    def alert(self, seconds=2.0):
        style = self.style
        count = int(round(seconds * 30))
        frames = []
        for f in range(count):
            t = f / 30.0
            c = self.stand()
            breath = cycle(t, 1.0)
            quiver = math.sin(2.0 * math.pi * t * 3.0) * cycle(t, seconds)
            self.trunk_pose(c, (0.0, 0.012, 0.012 + 0.0015 * breath), (1.2, 0.0, 0.0), (2.2 + 0.2 * breath, 0.0, 0.0))
            self.neck_pose(c, style.get("alert_neck", 11.0) + 0.4 * breath, 1.2 * math.sin(2.0 * math.pi * t / seconds), 0.0, (-style.get("alert_neck", 11.0) * 0.55, 0.8 * math.sin(2.0 * math.pi * t / seconds), 0.0))
            swivel = math.sin(2.0 * math.pi * t / seconds)
            self.ears(c, (-16.0 + 1.5 * quiver, -24.0 + 7.0 * swivel), (-16.0 - 1.5 * quiver, -24.0 - 7.0 * swivel))
            self.tail_pose(c, style.get("alert_tail", 22.0) + 3.0 * quiver, 0.0, 6.0)
            self.breathe(c, 0.6 * breath)
            frames.append(self.finish(c)[:2])
        frames.append(frames[0])
        return self.pack("alert", frames, True)

    def muzzle(self, c):
        local, shift, world, place = self.finish(c)
        slot = self.rig.slot["head"]
        return place[slot] + world[slot] @ self.nose

    def feed(self, name, seconds=4.0, rooting=False):
        style = self.style
        k = self.k
        self.nose = (self.style["nose"] - self.style["skull"]) * k
        count = int(round(seconds * 30))
        offsets = {"fore_l": (0.0, -style.get("graze_step", 0.16), 0.0), "fore_r": (0.0, style.get("graze_step", 0.16) * 0.5, 0.0)}
        target = style.get("graze_height", 0.035) * k

        def height(pitch):
            c = self.stand(offsets)
            self.trunk_pose(c, (0.0, -0.02, style.get("graze_drop", -0.02)), (-1.0, 0.0, 0.0), (-style.get("graze_tilt", 9.0), 0.0, 0.0))
            self.neck_pose(c, pitch, 0.0, 0.0, (style.get("graze_head", 66.0), 0.0, 0.0), 0.0, ((0.78, 0.25), (0.13, 0.35), (0.09, 0.4)))
            return self.muzzle(c)[2]

        scan = [(-20.0 - 2.5 * index) for index in range(53)]
        heights = [height(pitch) for pitch in scan]
        reached = next((index for index, value in enumerate(heights) if value <= target), None)
        if reached is None:
            base = scan[int(numpy.argmin(heights))]
            print("CLIPS muzzle stays", round(min(heights), 3), "above the ground")
        else:
            high = scan[reached - 1]
            low = scan[reached]
            for attempt in range(16):
                pitch = 0.5 * (low + high)
                if height(pitch) > target:
                    high = pitch
                else:
                    low = pitch
            base = 0.5 * (low + high)
        frames = []
        for f in range(count):
            t = f / 30.0
            c = self.stand(offsets)
            breath = cycle(t, 2.0)
            sweep = math.sin(2.0 * math.pi * t / seconds)
            tug = motion.pulse(t, 0.55, 0.3) + motion.pulse(t, 1.85, 0.3) + motion.pulse(t, 3.1, 0.3)
            shove = (motion.pulse(t, 0.4, 0.5) + motion.pulse(t, 1.5, 0.45) + motion.pulse(t, 2.7, 0.55)) if rooting else 0.0
            self.trunk_pose(c, (0.006 * sweep, -0.02 - 0.03 * shove, style.get("graze_drop", -0.02) + 0.002 * breath), (-1.0 + 1.5 * shove, 0.8 * sweep, 0.0), (-style.get("graze_tilt", 9.0) - 2.0 * shove, 2.0 * sweep, 0.0))
            chew = style.get("graze_chew", 5.0) * (0.35 + 0.65 * cycle(t, seconds / 7.0)) * (1.0 - 0.8 * tug)
            self.neck_pose(c, base + 2.5 * tug - 3.0 * shove + 1.5 * cycle(t, seconds / 2.0), 9.0 * sweep + (6.0 * shove * math.sin(2.0 * math.pi * t * 2.0) if rooting else 0.0), 0.0, (style.get("graze_head", 66.0) + 9.0 * tug + 14.0 * shove, 5.0 * sweep, 3.0 * math.sin(2.0 * math.pi * t / seconds * 7.0) * (1.0 - tug)), chew, ((0.78, 0.25), (0.13, 0.35), (0.09, 0.4)))
            if "snout" in self.rig.slot:
                c["rotation"]["snout"] = turn(10.0 * shove + 5.0 * math.sin(2.0 * math.pi * t * 2.5) * cycle(t, seconds), 6.0 * math.sin(2.0 * math.pi * t * 1.75), 0.0)
            left = motion.pulse(t, 1.0, 0.35)
            right = motion.pulse(t, 2.6, 0.35)
            self.ears(c, (8.0 - 16.0 * left, 10.0 - 22.0 * left), (8.0 - 16.0 * right, 10.0 - 22.0 * right))
            flick = motion.pulse(t, 2.9, 0.6)
            self.tail_pose(c, 8.0 * flick, 24.0 * flick * math.sin(2.0 * math.pi * (t - 2.9) / 0.3), 5.0 * flick)
            self.breathe(c, breath)
            frames.append(self.finish(c)[:2])
        frames.append(frames[0])
        events = [{"name": "bite", "time": time} for time in (0.7, 2.0, 3.25)]
        return self.pack(name, frames, True, 0.0, events)

    def attack(self, seconds=1.0):
        style = self.style["attack"]
        count = int(round(seconds * 30))
        frames = []
        hit = style["hit"]
        for f in range(count + 1):
            t = f / 30.0
            c = self.stand()
            wind = float(keyed(t, [(0.0, 0.0), (hit - 0.16, 1.0), (hit + 0.02, 0.15), (hit + 0.2, 0.0), (seconds, 0.0)]))
            lunge = float(keyed(t, [(0.0, 0.0), (hit - 0.18, -0.25), (hit, 1.0), (hit + 0.12, 0.85), (seconds - 0.1, 0.0), (seconds, 0.0)]))
            slash = float(keyed(t, [(0.0, 0.0), (hit - 0.12, 0.0), (hit + 0.04, 1.0), (hit + 0.2, 0.7), (seconds - 0.12, 0.0), (seconds, 0.0)]))
            self.trunk_pose(c, (0.0, -style["reach"] * lunge, style["crouch"] * wind - 0.02 * max(lunge, 0.0) + style.get("rise", 0.02) * slash), (-style["dip"] * wind * 0.4 + 2.0 * slash, 0.0, 0.0), (-style["dip"] * wind + style.get("rear", 3.0) * slash, 0.0, 0.0), 4.0 * wind)
            self.neck_pose(c, style["neck_down"] * wind + style["neck_up"] * slash, 0.0, 0.0, (style["head_down"] * wind + style["head_up"] * slash, style.get("twist", 0.0) * slash, style.get("roll", 0.0) * slash), style.get("jaw", 0.0) * slash)
            back = max(wind, slash)
            self.ears(c, (30.0 * back, 25.0 * back), (30.0 * back, 25.0 * back))
            self.tail_pose(c, 25.0 * back, 8.0 * math.sin(2.0 * math.pi * t * 3.0) * back, 8.0 * back)
            if "snout" in self.rig.slot:
                c["rotation"]["snout"] = turn(14.0 * slash, 0.0, 0.0)
            self.breathe(c, 0.5 * back)
            frames.append(self.finish(c)[:2])
        return self.pack("attack", frames, False, 0.0, [{"name": "hit", "time": hit}])

    def hit(self, seconds=0.4):
        count = int(round(seconds * 30))
        frames = []
        for f in range(count + 1):
            t = f / 30.0
            c = self.stand()
            jolt = float(keyed(t, [(0.0, 0.0), (0.09, 1.0), (0.22, -0.18), (0.32, 0.05), (seconds, 0.0)]))
            self.trunk_pose(c, (-0.012 * jolt, 0.035 * jolt, -0.045 * jolt), (2.5 * jolt, -1.5 * jolt, 3.0 * jolt), (-2.0 * jolt, 2.5 * jolt, -2.0 * jolt), -3.0 * jolt)
            self.neck_pose(c, 9.0 * jolt, 8.0 * jolt, 0.0, (-10.0 * jolt, 7.0 * jolt, 5.0 * jolt), 5.0 * max(jolt, 0.0))
            self.ears(c, (34.0 * abs(jolt), 22.0 * abs(jolt)), (34.0 * abs(jolt), 22.0 * abs(jolt)))
            self.tail_pose(c, -12.0 * jolt, 10.0 * jolt, -8.0 * jolt)
            self.breathe(c, 0.8 * abs(jolt))
            frames.append(self.finish(c)[:2])
        return self.pack("hit", frames, False)

    def rear(self, spec):
        seconds = spec["seconds"]
        count = int(round(seconds * 30))
        tuck = spec["tuck"]
        frames = []
        for f in range(count + 1):
            t = f / 30.0
            rise = float(keyed(t, spec["rise"]))
            air = float(keyed(t, spec["air"]))
            up = max(rise, 0.0)
            c = self.rig.blank()
            for key in ("hind_l", "hind_r"):
                c["feet"][key] = {"position": self.home[key].copy(), "flex": spec["hock"] * up}
            pitch = spec["pitch"] * rise
            self.trunk_pose(c, (0.0, spec["back"] * up, spec["sink"] * up), (pitch * 0.9, 0.0, 0.0), (pitch, 0.0, 0.0), -spec["arch"] * up)
            paw = math.sin(2.0 * math.pi * (t - spec["peak"]) / spec["paw"]) * air
            for key in ("fore_l", "fore_r"):
                beat = paw * (1.0 if key.endswith("_l") else -1.0)
                c["free"][key] = {0: rx(math.radians(tuck[0] * air)), 1: rx(math.radians(tuck[1] * air)), 2: rx(math.radians(tuck[2] * air + 20.0 * beat)), 3: rx(math.radians(tuck[3] * air - 30.0 * beat)), 4: rx(math.radians(tuck[4] * air)), 5: rx(math.radians(tuck[5] * air))}
            toss = math.sin(math.pi * min(max((t - 0.15) / 0.55, 0.0), 1.0))
            self.neck_pose(c, spec["neck"] * up + spec["toss"] * toss, 5.0 * math.sin(2.0 * math.pi * t / seconds) * up, 0.0, (spec["head"] * up - 0.5 * spec["toss"] * toss, 0.0, 0.0), spec["jaw"] * up)
            self.ears(c, (spec["ears"] * up, 16.0 * up), (spec["ears"] * up, 16.0 * up))
            self.tail_pose(c, spec["tail"] * up, 7.0 * math.sin(2.0 * math.pi * t / 0.9) * up, -4.0 * up)
            self.breathe(c, 0.7 * up)
            local, shift, world, place = self.finish(c)
            planted = self.rig.blank()
            planted["rotation"] = dict(c["rotation"])
            planted["location"] = dict(c["location"])
            planted["feet"] = dict(c["feet"])
            for key in ("fore_l", "fore_r"):
                planted["feet"][key] = {"position": self.home[key].copy(), "flex": spec["land_flex"] * max(-rise, 0.0) / 0.05}
            grounded = self.rig.solve(planted)[0]
            for key in ("fore_l", "fore_r"):
                for name in self.rig.limbs[key].names:
                    slot = self.rig.slot[name]
                    local[slot] = motion.matrix_of(motion.slerp(motion.quaternion(grounded[slot]), motion.quaternion(local[slot]), air))
            frames.append((local, shift))
        return self.pack("rear", frames, False, 0.0, [{"name": "rear", "time": spec["peak"]}, {"name": "land", "time": spec["land"]}])

    def folded(self, c, side=0.0):
        style = self.style["rest"]
        for key in legs:
            sign = 1.0 if key.endswith("_l") else -1.0
            if key.startswith("fore"):
                angles = style["fore"]
                c["free"][key] = {0: rx(math.radians(angles[0])), 1: ry(-sign * math.radians(style.get("fore_spread", 4.0))) @ rx(math.radians(angles[1])), 2: rx(math.radians(angles[2])), 3: rx(math.radians(angles[3])), 4: rx(math.radians(angles[4])), 5: rx(math.radians(angles[5]))}
            else:
                angles = style["hind"]
                c["free"][key] = {0: ry(-sign * math.radians(style.get("hind_spread", 12.0))) @ rx(math.radians(angles[0])), 1: rx(math.radians(angles[1])), 2: rx(math.radians(angles[2])), 3: rx(math.radians(angles[3])), 4: rx(math.radians(angles[4]))}

    def tuck(self, c, key, index, lowest=0.0):
        base = c["free"][key][index]
        angle = 0.0
        for attempt in range(8):
            values = []
            for offset in (0.0, 0.02):
                c["free"][key][index] = base @ rx(angle + offset)
                local, shift, world, place, info = self.rig.solve(c)
                values.append(self.legs_low(world, place, (key,)))
            if abs(values[0] - lowest) < 0.002:
                break
            slope = (values[1] - values[0]) / 0.02
            if abs(slope) < 1e-4:
                break
            angle = angle - max(min((values[0] - lowest) / slope, 0.2), -0.2)
        c["free"][key][index] = base @ rx(angle)
        return angle

    def repose(self):
        style = self.style["rest"]
        c = self.rig.blank()
        self.folded(c)
        self.trunk_pose(c, (0.0, 0.0, style["hips"]), (style["pitch"], 0.0, style.get("roll", 0.0)), (style["pitch"] + style.get("chest", 0.0), 0.0, style.get("roll", 0.0) * 0.4))
        self.settle(c, (), True)
        turned = {key: round(math.degrees(self.tuck(c, key, 3 if key.startswith("fore") else 0)), 1) for key in legs}
        print("CLIPS rest hips", round(float(c["location"]["hips"][2]) / self.k, 3), "tuck", turned)
        return c["free"], float(c["location"]["hips"][2]) / self.k

    def rest(self, seconds=4.0):
        style = self.style["rest"]
        count = int(round(seconds * 30))
        frames = []
        free, height = self.repose()
        for f in range(count):
            t = f / 30.0
            c = self.rig.blank()
            c["free"] = {key: dict(value) for key, value in free.items()}
            breath = cycle(t, 2.0)
            drift = math.sin(2.0 * math.pi * t / seconds)
            self.trunk_pose(c, (0.0, 0.0, height + 0.003 * breath), (style["pitch"], 0.0, style.get("roll", 0.0)), (style["pitch"] + style.get("chest", 0.0) + 0.3 * breath, 0.0, style.get("roll", 0.0) * 0.4))
            chew = self.style.get("rest_chew", 0.0) * cycle(t, seconds / 5.0)
            self.neck_pose(c, style["neck"] + 0.8 * breath, 7.0 * drift, 0.0, (style["head"] - 0.5 * breath, 5.0 * drift, 2.0 * math.sin(2.0 * math.pi * t / seconds * 5.0) * (1.0 if chew else 0.0)), chew)
            left = motion.pulse(t, 0.9, 0.32)
            right = motion.pulse(t, 2.7, 0.32) + 0.6 * motion.pulse(t, 3.1, 0.25)
            self.ears(c, (-12.0 * left, -24.0 * left), (-12.0 * right, -24.0 * right))
            flick = motion.pulse(t, 1.8, 0.5)
            self.tail_pose(c, 6.0 * flick, 20.0 * flick * math.sin(2.0 * math.pi * (t - 1.8) / 0.3), 4.0 * flick)
            self.breathe(c, breath)
            solved = self.rig.solve(c)
            if f == 0:
                print("CLIPS rest body", round(self.body_low(solved[2], solved[3]), 3), "legs", {key: round(self.legs_low(solved[2], solved[3], (key,)), 3) for key in legs})
            frames.append(solved[:2])
        frames.append(frames[0])
        return self.pack("rest", frames, True)

    def sprawl(self, c, amount, twitch=0.0):
        style = self.style["death"]
        for key in legs:
            upper = key.endswith("_r")
            if key.startswith("fore"):
                angles = [a * amount for a in (style["fore_upper"] if upper else style["fore_lower"])]
                c["free"][key] = {0: rx(math.radians(angles[0])), 1: rx(math.radians(angles[1])), 2: rx(math.radians(angles[2] - twitch * 8.0)), 3: rx(math.radians(angles[3] + twitch * 14.0)), 4: rx(math.radians(angles[4])), 5: rx(math.radians(angles[5]))}
            else:
                angles = [a * amount for a in (style["hind_upper"] if upper else style["hind_lower"])]
                c["free"][key] = {0: rx(math.radians(angles[0] - twitch * 6.0)), 1: rx(math.radians(angles[1] + twitch * 12.0)), 2: rx(math.radians(angles[2])), 3: rx(math.radians(angles[3])), 4: rx(math.radians(angles[4]))}

    def recline(self, c, lift=0.0):
        style = self.style["death"]
        self.settle(c, (), True, lift)
        for key in legs:
            self.lay(c, key, abs(style.get("droop", 18.0)) if key.endswith("_r") else 55.0)
        return self.rig.solve(c)[:2]

    def kneel(self, pitch):
        c = self.rig.blank()
        for key in ("hind_l", "hind_r"):
            c["feet"][key] = {"position": self.home[key].copy(), "flex": 0.2}
        for key in ("fore_l", "fore_r"):
            c["free"][key] = {1: rx(-math.radians(pitch)), 2: rx(math.radians(-8.0)), 3: rx(math.radians(103.0)), 4: rx(math.radians(25.0))}
        self.trunk_pose(c, (0.03, -0.04, 0.0), (-0.55 * pitch, 3.0, 5.0), (-pitch, -2.0, 8.0), 3.0)
        local, shift, world, place, info = self.settle(c, ("fore_l", "fore_r"), False)
        return c, float(c["location"]["hips"][2])

    def death(self, seconds=1.8):
        style = self.style["death"]
        fold = self.style["rest"]["fore"]
        count = int(round(seconds * 30))
        keys = []
        c = self.stand()
        self.trunk_pose(c)
        self.neck_pose(c)
        keys.append((0.0, self.finish(c)[:2]))
        c = self.stand()
        for key in ("fore_l", "fore_r"):
            c["feet"][key]["flex"] = 0.45
        self.trunk_pose(c, (0.012, 0.02, -0.055), (2.5, 1.0, 3.0), (-5.0, -2.0, 5.0), 5.0)
        self.neck_pose(c, -5.0, -6.0, 0.0, (-10.0, -5.0, 5.0), 5.0)
        self.ears(c, (20.0, 12.0), (20.0, 12.0))
        self.tail_pose(c, -6.0, 8.0, 0.0)
        keys.append((0.2, self.finish(c)[:2]))
        height = float(self.rig.rest[self.rig.slot["femur_l"]][2])
        best = None
        for pitch in range(14, 42, 2):
            c, drop = self.kneel(float(pitch))
            if best is None or abs(drop + 0.1 * height) < abs(best[1] + 0.1 * height):
                best = (float(pitch), drop)
        c, drop = self.kneel(best[0])
        self.neck_pose(c, 0.45 * best[0], -6.0, 0.0, (-6.0, -4.0, 6.0), 8.0)
        self.ears(c, (25.0, 10.0), (25.0, 10.0))
        self.tail_pose(c, 6.0, -8.0, 3.0)
        solved = self.rig.solve(c)
        print("CLIPS kneel pitch", best[0], "hips", round(drop, 3), "short", {name: round(value, 3) for name, value in solved[4]["short"].items() if value > 1e-4})
        keys.append((0.5, solved[:2]))
        c = self.rig.blank()
        for key in ("hind_l", "hind_r"):
            c["feet"][key] = {"position": self.home[key].copy(), "flex": 0.9}
        for key in ("fore_l", "fore_r"):
            sign = 1.0 if key.endswith("_l") else -1.0
            c["free"][key] = {0: rx(math.radians(fold[0])), 1: ry(-sign * math.radians(4.0)) @ rx(math.radians(fold[1])), 2: rx(math.radians(fold[2])), 3: rx(math.radians(fold[3])), 4: rx(math.radians(fold[4])), 5: rx(math.radians(fold[5]))}
        self.trunk_pose(c, (style["side"] * 0.42, 0.0, 0.0), (-14.0, 3.0, 50.0), (-8.0, -1.0, 30.0), 4.0)
        self.neck_pose(c, style["neck"] * 0.3 + 6.0, -10.0, 0.0, (style["head"] * 0.3, -8.0, 10.0), 8.0)
        self.ears(c, (25.0, 10.0), (25.0, 10.0))
        self.tail_pose(c, 10.0, -10.0, 5.0)
        keys.append((0.82, self.settle(c, ("fore_l", "fore_r"), True)[:2]))
        c = self.rig.blank()
        self.sprawl(c, 1.0, 0.25)
        self.trunk_pose(c, (style["side"], 0.03, 0.0), (0.0, 3.0, 91.0), (-1.0, 0.0, 92.0), 2.0)
        self.neck_pose(c, style["neck"] * 1.08, style["neck_yaw"], 0.0, (style["head"], style["head_yaw"], style["head_roll"]), 7.0)
        self.ears(c, (12.0, 4.0), (12.0, 4.0))
        self.tail_pose(c, 18.0, -6.0, 8.0)
        keys.append((1.08, self.recline(c, -0.006 * self.k)))
        c = self.rig.blank()
        self.sprawl(c, 0.94, -0.35)
        self.trunk_pose(c, (style["side"] * 0.99, 0.03, 0.0), (0.5, 3.0, 87.0), (0.0, 1.0, 88.0), 0.0)
        self.neck_pose(c, style["neck"] * 0.9, style["neck_yaw"] * 0.85, 0.0, (style["head"] * 0.85, style["head_yaw"], style["head_roll"] * 0.8), 4.0)
        self.ears(c, (6.0, 2.0), (6.0, 2.0))
        self.tail_pose(c, 8.0, -3.0, 4.0)
        keys.append((1.24, self.recline(c, 0.02 * self.k)))
        c = self.rig.blank()
        self.sprawl(c, 1.0, 0.0)
        self.trunk_pose(c, (style["side"], 0.03, 0.0), (0.0, 3.0, 90.0), (0.0, 0.5, 90.0), 0.0)
        self.neck_pose(c, style["neck"], style["neck_yaw"], 0.0, (style["head"], style["head_yaw"], style["head_roll"]), 3.0)
        self.ears(c, (4.0, 0.0), (4.0, 0.0))
        self.tail_pose(c, 12.0, -4.0, 6.0)
        keys.append((1.44, self.recline(c)))
        print("CLIPS death hips", round(float(c["location"]["hips"][2]), 3), "girth", {name: (round(value[0], 3), round(value[1], 3)) for name, value in self.girth.items()})
        frames = []
        late = [self.rig.slot[name] for name in ("neck_01", "neck_02", "neck_03", "head", "jaw", "ear_l", "ear_r") + tuple(self.rig.tail)]
        for f in range(count + 1):
            t = f / 30.0
            frames.append(self.sample(keys, t, late, 0.07))
        return self.pack("death", frames, False, 0.0, [{"name": "fall", "time": 1.08}])

    def sample(self, keys, time, late, lag):
        def at(moment):
            if moment <= keys[0][0]:
                return keys[0][1], keys[0][1], 0.0
            for index in range(len(keys) - 1):
                if moment <= keys[index + 1][0]:
                    return keys[index][1], keys[index + 1][1], motion.ease((moment - keys[index][0]) / (keys[index + 1][0] - keys[index][0]))
            return keys[-1][1], keys[-1][1], 0.0

        first, second, amount = at(time)
        local = numpy.empty_like(first[0])
        shift = first[1] + (second[1] - first[1]) * amount
        delayed = at(time - lag)
        for index in range(len(local)):
            a, b, w = (delayed[0][0][index], delayed[1][0][index], delayed[2]) if index in late and time - lag > 0.3 else (first[0][index], second[0][index], amount)
            local[index] = motion.matrix_of(motion.slerp(motion.quaternion(a), motion.quaternion(b), w))
        return local, shift


def build(blueprint):
    a = actor(blueprint)
    style = blueprint["motion"]
    clips = [a.idle(), a.idle_look(), a.feed(style.get("feed", "graze"), 4.0, style.get("feed", "graze") == "root"), a.alert()]
    for name in style.get("gaits", ("walk", "trot", "run")):
        clips.append(a.stride(name, style[name]))
    if "attack" in style:
        clips.append(a.attack(style["attack"].get("seconds", 1.0)))
    if "rear" in style:
        clips.append(a.rear(style["rear"]))
    clips.append(a.hit())
    clips.append(a.death())
    if style.get("lies", True):
        clips.append(a.rest())
    print("CLIPS", blueprint["name"], len(clips), "worst reach correction", round(a.worst, 4))
    return a, clips
