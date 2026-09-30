import aud
import numpy
import os
import wave

root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
source = os.path.join(root, "source", "audio")
output = os.path.join(root, "raw", "audio")
rate = 44100

impact = os.path.join(source, "kenney_impact-sounds", "Audio")
rpg = os.path.join(source, "kenney_rpg-audio", "Audio")
interface = os.path.join(source, "kenney_interface-sounds", "Audio")
zombies = os.path.join(source, "oga_zombies", "zombies")
moans = os.path.join(source, "oga_ghost_moans", "qubodup-GhostMoans", "wav")
loops = os.path.join(source, "oga_sfx_loops")

groups = [
	("step_grass", [os.path.join(impact, "footstep_grass_%03d.ogg" % i) for i in range(5)], 0.55),
	("step_concrete", [os.path.join(impact, "footstep_concrete_%03d.ogg" % i) for i in range(5)], 0.6),
	("step_wood", [os.path.join(impact, "footstep_wood_%03d.ogg" % i) for i in range(5)], 0.6),
	("step_soft", [os.path.join(impact, "footstep_snow_%03d.ogg" % i) for i in range(5)], 0.5),
	("step_gravel", [os.path.join(rpg, "footstep%02d.ogg" % i) for i in range(5)], 0.55),
	("hit_wood", [os.path.join(impact, "impactWood_heavy_%03d.ogg" % i) for i in range(5)], 0.9),
	("hit_rock", [os.path.join(impact, "impactMining_%03d.ogg" % i) for i in range(5)], 0.9),
	("hit_metal", [os.path.join(impact, "impactMetal_heavy_%03d.ogg" % i) for i in range(5)], 0.85),
	("hit_flesh", [os.path.join(impact, "impactPunch_heavy_%03d.ogg" % i) for i in range(5)], 0.9),
	("hit_soft", [os.path.join(impact, "impactSoft_heavy_%03d.ogg" % i) for i in range(5)], 0.8),
	("chop", [os.path.join(rpg, "chop.ogg")], 0.9),
	("pickup", [os.path.join(rpg, "cloth%d.ogg" % i) for i in range(1, 5)], 0.7),
	("container", [os.path.join(rpg, "metalLatch.ogg"), os.path.join(rpg, "creak1.ogg")], 0.75),
	("craft", [os.path.join(rpg, "metalClick.ogg")], 0.7),
	("equip", [os.path.join(rpg, "drawKnife%d.ogg" % i) for i in range(1, 3)], 0.6),
	("ui_click", [os.path.join(interface, "click_%03d.ogg" % i) for i in range(1, 4)], 0.5),
	("ui_open", [os.path.join(interface, "maximize_%03d.ogg" % i) for i in range(1, 3)], 0.5),
	("ui_close", [os.path.join(interface, "minimize_%03d.ogg" % i) for i in range(1, 3)], 0.5),
	("ui_error", [os.path.join(interface, "error_004.ogg")], 0.5),
	("zombie_groan", [os.path.join(zombies, "zombie-%d.wav" % i) for i in range(16, 22)], 0.95),
	("zombie_snarl", [os.path.join(zombies, "zombie-%d.wav" % i) for i in list(range(1, 16)) + [22, 23, 24]], 0.95),
	("ghost_moan", [os.path.join(moans, "qubodup-GhostMoan%02d.wav" % i) for i in range(1, 6)], 0.9),
	("player_hurt", [os.path.join(impact, "impactPunch_medium_%03d.ogg" % i) for i in range(3)], 0.8),
	("dry_fire", [os.path.join(rpg, "metalClick.ogg")], 0.75),
	("jam", [os.path.join(rpg, "metalLatch.ogg")] + [os.path.join(impact, "impactMetal_medium_%03d.ogg" % i) for i in range(3)], 0.8),
]

gunshots = os.path.join(source, "oga_gunshots", "sounds")

slices = [
	("shot_pistol", os.path.join(gunshots, "cz.wav"), 0.9, 4),
	("shot_rifle", os.path.join(gunshots, "mosin.wav"), 1.4, 4),
	("shot_assault", os.path.join(gunshots, "sks.wav"), 0.9, 4),
]

singles = [
	("reload_pistol", os.path.join(source, "oga_reload_pistol.wav"), 0.8),
	("reload_rifle", os.path.join(source, "oga_reload_rifle.wav"), 0.8),
	("bolt", os.path.join(source, "oga_shotgun_cock.wav"), 0.8),
]

ambience = [
	("amb_forest", os.path.join(source, "oga_forest_ambience.mp3"), 0.5),
	("amb_crickets", os.path.join(source, "oga_crickets.mp3"), 0.45),
	("amb_drone", os.path.join(loops, "ambient_01.ogg"), 0.4),
]


def load(path, channels):
	sound = aud.Sound(path).resample(rate, False)
	data = sound.data().astype(numpy.float64)

	if data.ndim == 1:
		data = data[:, None]

	if channels == 1:
		return data.mean(axis=1)

	if data.shape[1] == 1:
		return numpy.repeat(data, 2, axis=1)

	return data[:, :2]


def trim(samples):
	magnitude = numpy.abs(samples)
	threshold = magnitude.max() * 0.02
	active = numpy.nonzero(magnitude > threshold)[0]

	if len(active) == 0:
		return samples

	first = max(0, active[0] - int(rate * 0.004))
	last = min(len(samples), active[-1] + int(rate * 0.06))

	return samples[first:last]


def fade(samples, seconds_in, seconds_out):
	count_in = min(len(samples), int(rate * seconds_in))
	count_out = min(len(samples), int(rate * seconds_out))

	if count_in > 0:
		samples[:count_in] *= numpy.linspace(0.0, 1.0, count_in)[:, None] if samples.ndim > 1 else numpy.linspace(0.0, 1.0, count_in)

	if count_out > 0:
		samples[-count_out:] *= numpy.linspace(1.0, 0.0, count_out)[:, None] if samples.ndim > 1 else numpy.linspace(1.0, 0.0, count_out)

	return samples


def normalize(samples, peak):
	top = numpy.abs(samples).max()

	return samples * (peak / top) if top > 0.0 else samples


def seamless(samples, seconds):
	count = min(len(samples) // 3, int(rate * seconds))
	head = samples[:count].copy()
	tail = samples[-count:].copy()
	ramp = numpy.linspace(0.0, 1.0, count)
	ramp = ramp[:, None] if samples.ndim > 1 else ramp
	blended = tail * (1.0 - ramp) + head * ramp
	result = samples[count:].copy()
	result[-count:] = blended

	return result


def write(name, samples):
	samples = numpy.clip(samples, -1.0, 1.0)
	channels = 1 if samples.ndim == 1 else samples.shape[1]
	pcm = (samples * 32767.0).astype(numpy.int16)

	with wave.open(os.path.join(output, name + ".wav"), "wb") as file:
		file.setnchannels(channels)
		file.setsampwidth(2)
		file.setframerate(rate)
		file.writeframes(pcm.tobytes())

	print("audio: %-18s %6.2f s %d ch" % (name, len(samples) / rate, channels))


def colored(count, generator, low, high, tilt):
	spectrum = numpy.fft.rfft(generator.standard_normal(count))
	frequency = numpy.fft.rfftfreq(count, 1.0 / rate)
	shape = numpy.where((frequency >= low) & (frequency <= high), 1.0, 0.0) / numpy.maximum(frequency, 1.0) ** tilt
	band = numpy.fft.irfft(spectrum * shape, count)

	return band / numpy.abs(band).max()


def periodic(count, generator, cycles):
	spectrum = numpy.zeros(count // 2 + 1, dtype=numpy.complex128)
	spectrum[1:cycles + 1] = generator.standard_normal(cycles) + 1j * generator.standard_normal(cycles)
	curve = numpy.fft.irfft(spectrum, count)

	return curve / numpy.abs(curve).max()


def synthesize():
	generator = numpy.random.default_rng(20260928)
	length = rate * 32
	time = numpy.arange(length) / rate

	gust = 0.55 + 0.45 * periodic(length, generator, 14)
	howl = 0.5 + 0.5 * periodic(length, generator, 6)
	wind = numpy.stack([colored(length, generator, 40.0, 1400.0, 0.9) * gust + colored(length, generator, 300.0, 2400.0, 0.5) * howl * 0.25, colored(length, generator, 40.0, 1400.0, 0.9) * gust + colored(length, generator, 300.0, 2400.0, 0.5) * howl * 0.25], axis=1)

	write("amb_wind", normalize(wind, 0.5))

	waves = numpy.zeros(length)

	for start in numpy.arange(0.0, 32.0, 6.4):
		offset = (time - start) % 32.0
		waves += numpy.where(offset < 6.4, numpy.exp(-offset * 0.55) * numpy.clip(offset * 3.0, 0.0, 1.0), 0.0)

	surf = numpy.stack([colored(length, generator, 30.0, 3500.0, 0.75), colored(length, generator, 30.0, 3500.0, 0.75)], axis=1)
	wash = numpy.stack([colored(length, generator, 800.0, 7000.0, 0.3), colored(length, generator, 800.0, 7000.0, 0.3)], axis=1)
	ocean = surf * (0.25 + 0.75 * waves[:, None]) + wash * (waves[:, None] ** 2) * 0.35

	write("amb_ocean", normalize(ocean, 0.55))

	fire_length = rate * 8
	rumble = colored(fire_length, generator, 20.0, 260.0, 0.6) * 0.35
	crackle = numpy.zeros(fire_length)

	for _ in range(220):
		position = int(generator.integers(0, fire_length - 2000))
		size = int(generator.integers(60, 900))
		strength = generator.uniform(0.15, 1.0) ** 2
		burst = generator.standard_normal(size) * numpy.exp(-numpy.arange(size) / (size * 0.18)) * strength
		crackle[position:position + size] += burst

	hiss = colored(fire_length, generator, 2000.0, 9000.0, 0.2) * 0.06

	write("fire", normalize(seamless(rumble + crackle + hiss, 0.3), 0.7))

	for index in range(4):
		duration = 0.3 + 0.08 * index
		count = int(rate * duration)
		progress = numpy.linspace(0.0, 1.0, count)
		noise = generator.standard_normal(count)
		spectrum = numpy.fft.rfft(noise)
		frequency = numpy.fft.rfftfreq(count, 1.0 / rate)
		low = numpy.fft.irfft(spectrum * numpy.exp(-((frequency - 450.0) / 350.0) ** 2), count)
		high = numpy.fft.irfft(spectrum * numpy.exp(-((frequency - 1500.0) / 900.0) ** 2), count)
		sweep = numpy.sin(numpy.pi * progress) ** 2
		mix = low * (1.0 - sweep) + high * sweep
		envelope = numpy.sin(numpy.pi * progress ** (0.7 + 0.1 * index)) ** 3

		write("swing_%d" % index, normalize(mix * envelope, 0.6))

	beat_length = int(rate * 1.0)
	beat_time = numpy.arange(beat_length) / rate
	thump = numpy.zeros(beat_length)

	for start, strength in ((0.0, 1.0), (0.22, 0.7)):
		local = numpy.clip(beat_time - start, 0.0, None)
		thump += numpy.where(beat_time >= start, numpy.sin(2.0 * numpy.pi * 52.0 * local) * numpy.exp(-local * 22.0) * strength, 0.0)

	write("heartbeat", normalize(thump, 0.9))

	def band(count, center, width):
		spectrum = numpy.fft.rfft(generator.standard_normal(count))
		frequency = numpy.fft.rfftfreq(count, 1.0 / rate)

		return numpy.fft.irfft(spectrum * numpy.exp(-((frequency - center) / width) ** 2), count)

	def bubbles(count, amount, low, high, start, end, loudness):
		result = numpy.zeros(count)

		for _ in range(amount):
			first = int(generator.uniform(start, end) * count)
			length = min(int(rate * generator.uniform(0.02, 0.06)), count - first)
			local = numpy.arange(length) / rate
			pitch = generator.uniform(low, high)
			sweep = pitch * (1.0 + 2.2 * local / max(local[-1], 1e-6)) if length > 1 else pitch
			result[first:first + length] += numpy.sin(2.0 * numpy.pi * numpy.cumsum(sweep) / rate) * numpy.exp(-local * generator.uniform(60.0, 140.0)) * generator.uniform(0.3, 1.0) * loudness

		return result

	for index in range(3):
		duration = 1.1 + 0.15 * index
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		rush = band(count, 700.0, 900.0) * 1.2 + band(count, 3200.0, 2600.0) * 0.5
		thud = band(count, 120.0, 90.0) * numpy.exp(-time * 16.0) * 2.5
		envelope = (1.0 - numpy.exp(-time * 120.0)) * (numpy.exp(-time * 5.5) + 0.25 * numpy.exp(-time * 1.8))

		write("splash_%d" % index, normalize(rush * envelope + thud + bubbles(count, 26, 500.0, 1600.0, 0.05, 0.85, 0.7), 0.85))

	for index in range(4):
		duration = 0.5 + 0.05 * index
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		slosh = band(count, 850.0, 1100.0) + band(count, 4000.0, 2400.0) * 0.35
		envelope = (1.0 - numpy.exp(-time * 60.0)) * numpy.exp(-time * (8.0 + index))

		write("wade_%d" % index, normalize(slosh * envelope + bubbles(count, 7, 700.0, 1900.0, 0.1, 0.7, 0.45), 0.6))

	for index in range(4):
		duration = 0.9 + 0.08 * index
		count = int(rate * duration)
		progress = numpy.linspace(0.0, 1.0, count)
		swirl = band(count, 420.0, 520.0) + band(count, 1600.0, 1100.0) * 0.4
		envelope = numpy.sin(numpy.pi * progress ** 0.6) ** 2

		write("swim_%d" % index, normalize(swirl * envelope + bubbles(count, 5, 400.0, 1100.0, 0.2, 0.8, 0.3), 0.45))

	deep_length = rate * 12
	hum = colored(deep_length, generator, 25.0, 320.0, 0.8) * (0.8 + 0.2 * periodic(deep_length, generator, 5))
	drift = numpy.zeros(deep_length)

	for _ in range(90):
		first = int(generator.integers(0, deep_length - rate))
		length = int(rate * generator.uniform(0.03, 0.09))
		local = numpy.arange(length) / rate
		pitch = generator.uniform(250.0, 900.0)
		drift[first:first + length] += numpy.sin(2.0 * numpy.pi * pitch * (1.0 + 1.8 * local / local[-1]) * local) * numpy.exp(-local * 45.0) * generator.uniform(0.05, 0.25)

	write("underwater", normalize(seamless(hum + drift, 0.4), 0.6))

	rain_length = rate * 16
	hiss = numpy.stack([colored(rain_length, generator, 900.0, 11000.0, 0.35), colored(rain_length, generator, 900.0, 11000.0, 0.35)], axis=1) * 0.45
	patter = numpy.zeros((rain_length, 2))

	for _ in range(12000):
		first = int(generator.integers(0, rain_length - 400))
		size = int(generator.integers(30, 240))
		channel = int(generator.integers(0, 2))
		patter[first:first + size, channel] += generator.standard_normal(size) * numpy.exp(-numpy.arange(size) / (size * 0.18)) * generator.uniform(0.04, 0.35)

	drumming = numpy.stack([colored(rain_length, generator, 120.0, 900.0, 0.8), colored(rain_length, generator, 120.0, 900.0, 0.8)], axis=1) * 0.22

	write("amb_rain", normalize(seamless(hiss + patter + drumming, 1.0), 0.55))

	for index in range(3):
		count = int(rate * (5.5 + index))
		time = numpy.arange(count) / rate
		crack = colored(count, generator, 1500.0, 9000.0, 0.2) * numpy.exp(-time * (16.0 + index * 5.0)) * (1.0 - numpy.exp(-time * 400.0))
		rumble = colored(count, generator, 18.0, 220.0, 1.1) * (0.6 + 0.4 * periodic(count, generator, 9 + index * 3)) * numpy.exp(-time * (0.55 + 0.1 * index)) * (1.0 - numpy.exp(-time * 6.0))

		write("thunder_%d" % index, normalize(crack * 0.5 + rumble, 0.95))

	for index in range(3):
		duration = 1.8 + 0.3 * index
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		creak = numpy.zeros(count)
		moment = 0.05

		while moment < duration - 0.05:
			progress = moment / duration
			first = int(moment * rate)
			length = min(int(rate * 0.018), count - first)
			local = numpy.arange(length) / rate
			pitch = generator.uniform(380.0, 620.0) * (1.0 + 0.3 * progress)
			creak[first:first + length] += numpy.sin(2.0 * numpy.pi * pitch * local) * numpy.exp(-local * 260.0) * generator.uniform(0.4, 1.0) * (0.35 + 0.65 * progress)
			moment += generator.uniform(0.7, 1.3) / (14.0 + 70.0 * progress ** 1.6)

		groan = band(count, 170.0, 70.0) * (0.3 + 0.7 * time / duration) * 0.6
		snaps = numpy.zeros(count)

		for _ in range(6 + index * 2):
			first = int(generator.uniform(0.55, 0.98) * count)
			length = min(int(rate * generator.uniform(0.004, 0.02)), count - first)
			snaps[first:first + length] += generator.standard_normal(length) * numpy.exp(-numpy.arange(length) / (length * 0.2)) * generator.uniform(0.4, 1.0)

		write("tree_creak_%d" % index, normalize((creak + groan + snaps * 0.8) * numpy.clip(time * 4.0, 0.0, 1.0), 0.8))

	for index in range(3):
		duration = 3.2 + 0.3 * index
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		thud = band(count, 60.0 + 8.0 * index, 35.0) * numpy.exp(-time * 3.5) * 3.0 * (1.0 - numpy.exp(-time * 200.0))
		body = band(count, 220.0, 160.0) * numpy.exp(-time * 5.0) * 1.2
		rustle = colored(count, generator, 1200.0, 9000.0, 0.3) * numpy.exp(-time * 1.6) * 0.35 * (1.0 - numpy.exp(-time * 30.0))
		cracks = numpy.zeros(count)

		for _ in range(40):
			first = int(generator.uniform(0.0, 0.45) * count)
			length = min(int(rate * generator.uniform(0.005, 0.04)), count - first)
			cracks[first:first + length] += generator.standard_normal(length) * numpy.exp(-numpy.arange(length) / (length * 0.25)) * generator.uniform(0.2, 1.0)

		write("tree_fall_%d" % index, normalize(thud + body + rustle + cracks * 0.6, 0.95))

	def unit(samples):
		return samples / max(numpy.abs(samples).max(), 1e-9)

	for index in range(3):
		duration = 0.3
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		width = 0.00042 + 0.00016 * index
		wave = lowpass(numpy.where(time < width, 1.0 - 2.0 * time / width, 0.0), 15000.0 - 1500.0 * index, 2)
		ring = colored(count, generator, 2500.0, 12000.0, 0.15) * numpy.exp(-time * (70.0 + 15.0 * index)) * 0.22
		thump = unit(band(count, 170.0 + 45.0 * index, 90.0)) * numpy.exp(-time * 45.0) * (1.0 - numpy.exp(-time * 900.0)) * 0.2

		write("bullet_crack_%d" % index, normalize(unit(wave) + ring + thump, 0.95))

	for index in range(3):
		duration = 0.42
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		center = 0.15 + 0.03 * index
		sweep = 1.0 / (1.0 + numpy.exp(-(time - center) / (0.016 + 0.004 * index)))
		air = unit(band(count, 3300.0 - 200.0 * index, 1300.0)) * (1.0 - sweep) + unit(band(count, 1250.0 + 100.0 * index, 550.0)) * sweep
		pitch = 2400.0 - 1250.0 * sweep
		tone = numpy.sin(2.0 * numpy.pi * numpy.cumsum(pitch) / rate) * 0.25
		envelope = numpy.exp(-((time - center) / (0.05 + 0.012 * index)) ** 2)

		write("bullet_whiz_%d" % index, normalize((air + tone) * envelope, 0.8))

	for index in range(3):
		duration = 0.62
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		pitch = (4100.0 + 450.0 * index) * numpy.exp(-time * (2.0 + 0.4 * index)) + 850.0
		vibrato = 1.0 + 0.014 * numpy.sin(2.0 * numpy.pi * (30.0 + 6.0 * index) * time)
		tone = numpy.sin(2.0 * numpy.pi * numpy.cumsum(pitch * vibrato) / rate)
		envelope = (1.0 - numpy.exp(-time * 320.0)) * numpy.exp(-time * (4.5 + index))
		strike = colored(count, generator, 1500.0, 10000.0, 0.2) * numpy.exp(-time * 85.0)

		write("ricochet_%d" % index, normalize(tone * envelope * 0.7 + strike * 0.5, 0.85))

	pulse = 1575
	engine_length = rate * 4
	engine_time = numpy.arange(engine_length) / rate
	firing = numpy.zeros(engine_length)
	clatter_envelope = numpy.zeros(engine_length)
	strengths = (1.0, 0.62, 0.84, 0.55, 0.93, 0.68, 0.78, 0.5)

	for index in range(engine_length // pulse):
		length = pulse * 3
		local = numpy.arange(length) / rate
		span = (index * pulse + numpy.arange(length)) % engine_length
		strength = strengths[index % 8]

		firing[span] += (numpy.sin(2.0 * numpy.pi * (92.0 + 16.0 * (index % 3)) * local) * numpy.exp(-local * 44.0) + generator.standard_normal(length) * numpy.exp(-local * 85.0) * 0.6) * strength
		clatter_envelope[span] += numpy.exp(-local * 95.0) * strength

	exhaust = unit(lowpass(firing, 1300.0, 2))
	rumble = colored(engine_length, generator, 30.0, 190.0, 0.5) * (0.8 + 0.2 * periodic(engine_length, generator, 6))
	clatter = colored(engine_length, generator, 900.0, 3400.0, 0.3) * unit(clatter_envelope)
	whine = numpy.sin(2.0 * numpy.pi * 640.0 * engine_time) * (0.6 + 0.4 * periodic(engine_length, generator, 4)) + 0.5 * numpy.sin(2.0 * numpy.pi * 1285.0 * engine_time)
	fan = colored(engine_length, generator, 180.0, 1400.0, 0.4) * 0.2

	write("train_engine", normalize(exhaust + rumble * 0.22 + clatter * 0.3 + whine * 0.03 + fan, 0.8))

	roll_length = rate * 4
	roar = colored(roll_length, generator, 90.0, 2600.0, 0.55) * (0.75 + 0.25 * periodic(roll_length, generator, 9))
	sing = colored(roll_length, generator, 1800.0, 5200.0, 0.2) * (0.5 + 0.5 * periodic(roll_length, generator, 5)) * 0.16
	ground = colored(roll_length, generator, 28.0, 110.0, 0.4) * 0.6

	write("train_roll", normalize(roar + sing + ground, 0.75))

	for index in range(4):
		count = int(rate * 0.34)
		time = numpy.arange(count) / rate
		thud = unit(band(count, 95.0 + 12.0 * index, 60.0)) * numpy.exp(-time * 34.0) * (1.0 - numpy.exp(-time * 700.0)) * 1.1
		ring = numpy.zeros(count)

		for pitch, decay, level in ((640.0 + 35.0 * index, 26.0, 0.5), (1430.0 - 40.0 * index, 38.0, 0.34), (2710.0 + 90.0 * index, 60.0, 0.2), (3980.0, 85.0, 0.1)):
			ring += numpy.sin(2.0 * numpy.pi * pitch * time + generator.uniform(0.0, 6.28)) * numpy.exp(-time * decay) * level

		click = colored(count, generator, 700.0, 7000.0, 0.25) * numpy.exp(-time * 150.0) * 0.55

		write("train_clack_%d" % index, normalize(fade(thud + ring * (1.0 - numpy.exp(-time * 1500.0)) + click, 0.0005, 0.05), 0.9))

	def horn(pitch, duration):
		count = int(rate * duration)
		time = numpy.arange(count) / rate
		scoop = 1.0 - 0.035 * numpy.exp(-time * 22.0)
		phase = 2.0 * numpy.pi * numpy.cumsum(pitch * scoop) / rate
		tone = numpy.zeros(count)

		for harmonic in range(1, 22):
			tone += numpy.sin(phase * harmonic + generator.uniform(0.0, 6.28)) / harmonic ** 0.85 * numpy.exp(-((harmonic * pitch - 1500.0) / 2200.0) ** 2 * 0.6)

		air = colored(count, generator, 600.0, 6000.0, 0.4) * 0.07
		envelope = (1.0 - numpy.exp(-time * 45.0)) * numpy.clip((duration - time) * 14.0, 0.0, 1.0)

		return (unit(tone) + air) * envelope

	gap = numpy.zeros(int(rate * 0.07))

	write("train_horn_0", normalize(numpy.concatenate([horn(370.0, 0.95), gap, horn(311.0, 1.55)]), 0.9))
	write("train_horn_1", normalize(numpy.concatenate([horn(311.0, 0.7), gap, horn(370.0, 0.7), gap, horn(311.0, 1.3)]), 0.9))

	squeal_length = int(rate * 3.6)
	squeal_time = numpy.arange(squeal_length) / rate
	squeal = numpy.zeros(squeal_length)

	for pitch, level in ((2350.0, 1.0), (3120.0, 0.6), (4700.0, 0.3), (1180.0, 0.25)):
		wander = 1.0 + 0.012 * periodic(squeal_length, generator, 7) + 0.004 * periodic(squeal_length, generator, 40)
		squeal += numpy.sin(2.0 * numpy.pi * numpy.cumsum(pitch * wander) / rate) * level * (0.55 + 0.45 * periodic(squeal_length, generator, 11))

	grind = colored(squeal_length, generator, 300.0, 5000.0, 0.5) * 0.5
	squeal_envelope = numpy.clip(squeal_time * 1.6, 0.0, 1.0) * numpy.clip((3.6 - squeal_time) * 1.2, 0.0, 1.0)

	write("train_brake", normalize((unit(squeal) * 0.75 + grind) * squeal_envelope, 0.7))

	release_length = int(rate * 1.8)
	release_time = numpy.arange(release_length) / rate

	write("train_hiss", normalize(colored(release_length, generator, 1400.0, 9500.0, 0.25) * (1.0 - numpy.exp(-release_time * 90.0)) * numpy.exp(-release_time * 2.6) * numpy.clip((1.8 - release_time) * 6.0, 0.0, 1.0), 0.6))


def convolve(signal, response):
	count = len(signal) + len(response) - 1
	size = 1 << (count - 1).bit_length()

	return numpy.fft.irfft(numpy.fft.rfft(signal, size) * numpy.fft.rfft(response, size), size)[:count]


def lowpass(samples, cutoff, order):
	spectrum = numpy.fft.rfft(samples)
	frequency = numpy.fft.rfftfreq(len(samples), 1.0 / rate)

	return numpy.fft.irfft(spectrum / numpy.sqrt(1.0 + (frequency / cutoff) ** (2 * order)), len(samples))


def distant(samples, generator, cutoff, seconds):
	body = lowpass(numpy.concatenate([samples, numpy.zeros(int(rate * 0.05))]), cutoff, 2)
	spectrum = numpy.fft.rfft(body)
	frequency = numpy.fft.rfftfreq(len(body), 1.0 / rate)
	body = numpy.fft.irfft(spectrum * (1.0 + 1.4 * numpy.exp(-((frequency - 85.0) / 60.0) ** 2)), len(body))
	length = int(rate * seconds)
	time = numpy.arange(length) / rate
	response = lowpass(generator.standard_normal(length), 1100.0, 2) * numpy.exp(-time * 2.6) * (1.0 - numpy.exp(-time * 40.0)) * 0.18
	response[0] = 1.0

	for delay, gain in ((0.09, 0.42), (0.21, 0.28), (0.37, 0.2), (0.62, 0.13), (0.94, 0.08)):
		index = int(rate * (delay + generator.uniform(-0.02, 0.02)))
		response[index:index + 3] += gain * numpy.array([0.5, 1.0, 0.5])

	return fade(normalize(convolve(body, response), 0.9), 0.0005, seconds * 0.5)


def onsets(samples, spacing):
	frame = int(rate * 0.005)
	count = len(samples) // frame
	energy = numpy.sqrt((samples[:count * frame].reshape(count, frame) ** 2).mean(axis=1))
	threshold = energy.max() * 0.35
	found = []
	last = -spacing * 1000.0

	for index in range(1, count):
		time = index * 0.005

		if energy[index] > threshold and energy[index] > energy[index - 1] * 3.0 and time - last > spacing:
			found.append(max(0, index * frame - int(rate * 0.004)))
			last = time

	return found


def main():
	os.makedirs(output, exist_ok=True)

	generator = numpy.random.default_rng(343)

	for name, path, length, limit in slices:
		samples = load(path, 1)
		starts = onsets(samples, length * 0.8)

		print("audio: %s onsets at %s" % (name, ", ".join("%.2f" % (start / rate) for start in starts)))

		for index, start in enumerate(starts[:limit]):
			piece = samples[start:start + int(rate * length)].copy()
			piece = fade(piece, 0.001, length * 0.4)

			write("%s_%d" % (name, index), normalize(piece, 0.97))
			write("%s_far_%d" % (name, index), distant(piece[:int(rate * min(length, 0.5))], generator, 700.0 if name != "shot_pistol" else 900.0, 2.6))

	for name, path, peak in singles:
		samples = trim(load(path, 1))

		write(name + "_0", normalize(fade(samples, 0.002, 0.04), peak))

	for name, paths, peak in groups:
		for index, path in enumerate(paths):
			samples = trim(load(path, 1))
			samples = fade(samples, 0.002, 0.03)

			write("%s_%d" % (name, index), normalize(samples, peak))

	for name, path, peak in ambience:
		samples = load(path, 2)

		write(name, normalize(seamless(samples, 1.5), peak))

	synthesize()


main()
