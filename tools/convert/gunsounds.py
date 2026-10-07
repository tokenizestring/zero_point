import aud
import numpy
import os
import wave

root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
source = os.path.join(root, "source", "audio")
output = os.path.join(root, "raw", "audio")
rate = 44100
environments = ("plain", "forest", "mountains", "city", "room")
gunshots = os.path.join(source, "oga_gunshots", "sounds")
recordings = os.path.join(root, "source", "recordings")

takes = (
	("pistol", "ffl_1911_A_42P.wav", "ffl_1911_A_35.wav", 0.9, None),
	("bolt", "ffl_mosin_M_21P.wav", "ffl_mosin_M_21P.wav", 1.4, "ffl_mosin_M_26P.wav"),
	("auto", "ffl_ak_C_28P.wav", "ffl_ak_C_39.wav", 1.0, "ffl_ak_C_28P.wav"),
)

families = (
	("pistol", os.path.join(gunshots, "cz.wav"), 0.9, 0.36, 950.0, "slide", 0.0012, 95.0, 0.035),
	("bolt", os.path.join(gunshots, "mosin.wav"), 1.4, 0.5, 700.0, "striker", 0.0009, 70.0, 0.06),
	("auto", os.path.join(gunshots, "sks.wav"), 0.9, 0.42, 780.0, "carrier", 0.001, 80.0, 0.05),
)

mechanisms = {
	"slide": ((0.003, 0.7), (0.031, 0.9)),
	"striker": ((0.0, 0.8),),
	"carrier": ((0.004, 0.6), (0.056, 1.0)),
}

partials = {
	"slide": ((2900.0, 1.0), (4600.0, 0.6), (7200.0, 0.35)),
	"striker": ((3300.0, 1.0), (5100.0, 0.5), (1250.0, 0.3)),
	"carrier": ((2350.0, 1.0), (3870.0, 0.6), (5520.0, 0.4), (7900.0, 0.25)),
}


def load(path):
	sound = aud.Sound(path).resample(rate, False)
	data = sound.data().astype(numpy.float64)

	return data.mean(axis=1) if data.ndim > 1 else data


def write(name, samples):
	samples = numpy.clip(samples, -1.0, 1.0)
	channels = 1 if samples.ndim == 1 else samples.shape[1]
	pcm = (samples * 32767.0).astype(numpy.int16)

	with wave.open(os.path.join(output, name + ".wav"), "wb") as file:
		file.setnchannels(channels)
		file.setsampwidth(2)
		file.setframerate(rate)
		file.writeframes(pcm.tobytes())

	print("gunsounds: %-28s %5.2f s %d ch" % (name, len(samples) / rate, channels))


def normalize(samples, peak):
	top = numpy.abs(samples).max()

	return samples * (peak / top) if top > 0.0 else samples


def unit(samples):
	energy = numpy.sqrt((samples ** 2).sum())

	return samples / energy if energy > 0.0 else samples


def fade(samples, seconds_in, seconds_out):
	result = samples.copy()
	count_in = min(len(result), int(rate * seconds_in))
	count_out = min(len(result), int(rate * seconds_out))

	if count_in > 0:
		ramp = numpy.linspace(0.0, 1.0, count_in)
		result[:count_in] *= ramp[:, None] if result.ndim > 1 else ramp

	if count_out > 0:
		ramp = numpy.linspace(1.0, 0.0, count_out) ** 2
		result[-count_out:] *= ramp[:, None] if result.ndim > 1 else ramp

	return result


def shape(samples, gain):
	spectrum = numpy.fft.rfft(samples)
	frequency = numpy.fft.rfftfreq(len(samples), 1.0 / rate)

	return numpy.fft.irfft(spectrum * gain(frequency), len(samples))


def lowpass(samples, cutoff, order):
	return shape(samples, lambda frequency: 1.0 / numpy.sqrt(1.0 + (frequency / cutoff) ** (2 * order)))


def highpass(samples, cutoff, order):
	return shape(samples, lambda frequency: (frequency / cutoff) ** order / numpy.sqrt(1.0 + (frequency / cutoff) ** (2 * order)))


def bandpass(samples, low, high):
	return highpass(lowpass(samples, high, 2), low, 2)


def convolve(signal, response):
	count = len(signal) + len(response) - 1
	size = 1 << (count - 1).bit_length()

	return numpy.fft.irfft(numpy.fft.rfft(signal, size) * numpy.fft.rfft(response, size), size)[:count]


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


def diffuse(generator, seconds, decays, attack, bright):
	length = int(rate * seconds)
	time = numpy.arange(length) / rate
	result = numpy.zeros((length, 2))
	edges = ((20.0, 350.0), (350.0, 2200.0), (2200.0, bright))

	for channel in range(2):
		noise = generator.standard_normal(length)

		for (low, high), decay in zip(edges, decays):
			result[:, channel] += bandpass(noise, low, high) * numpy.exp(-6.91 * time / decay)

	return result * (1.0 - numpy.exp(-time / attack))[:, None]


def taps(generator, seconds, reflections):
	length = int(rate * seconds)
	result = numpy.zeros((length, 2))
	pulse = numpy.concatenate([numpy.hanning(int(rate * 0.0015) + 2), numpy.zeros(320)])

	for delay, gain, cutoff in reflections:
		shaped = lowpass(pulse, cutoff, 2)
		pan = generator.uniform(-0.8, 0.8)
		skew = int(rate * generator.uniform(0.0, 0.0006))
		start = int(rate * delay)

		for channel, weight in ((0, 1.0 - pan), (1, 1.0 + pan)):
			offset = start + (skew if channel == 1 else 0)
			end = min(length, offset + len(shaped))

			if offset < length:
				result[offset:end, channel] += shaped[:end - offset] * gain * weight

	return result


def rolls(generator, seconds, echoes):
	length = int(rate * seconds)
	result = numpy.zeros((length, 2))

	for delay, gain, cutoff, spread in echoes:
		count = int(rate * spread)
		time = numpy.arange(count) / rate

		for channel in range(2):
			burst = lowpass(generator.standard_normal(count), cutoff, 2) * numpy.exp(-time / (spread * 0.35)) * (1.0 - numpy.exp(-time / 0.004))
			start = int(rate * (delay + generator.uniform(0.0, 0.004)))
			end = min(length, start + count)

			if start < length:
				result[start:end, channel] += unit(burst)[:end - start] * gain

	return result


def blend(parts):
	return sum(unit(part) * numpy.sqrt(share) for part, share in parts)


def rumble(generator, seconds, count, low, high):
	echoes = []

	for _ in range(count):
		delay = generator.uniform(0.04, seconds * 0.7)
		echoes.append((delay, numpy.exp(-delay / (seconds * 0.3)), generator.uniform(low, high), generator.uniform(0.25, 0.6)))

	return rolls(generator, seconds, echoes)


def response(generator, name):
	if name == "plain":
		return blend([(rumble(generator, 2.6, 40, 450.0, 1300.0), 0.45), (diffuse(generator, 2.6, (2.2, 1.0, 0.25), 0.06, 4500.0), 0.55)])

	if name == "forest":
		early = [(0.006 + index * 0.0045 + generator.uniform(0.0, 0.003), 0.93 ** index, 6500.0) for index in range(26)]

		return blend([(diffuse(generator, 3.0, (2.4, 1.8, 0.8), 0.012, 9000.0), 0.85), (taps(generator, 3.0, early), 0.15)])

	if name == "mountains":
		echoes = [(0.42 + index * 0.37 + generator.uniform(-0.06, 0.06), 0.82 ** index, 1500.0 - index * 80.0, 0.15 + index * 0.025) for index in range(9)]

		return blend([(rolls(generator, 4.2, echoes), 0.7), (diffuse(generator, 4.2, (3.2, 1.8, 0.5), 0.05, 6000.0), 0.3)])

	if name == "city":
		slaps = [(0.016 + index * 0.017 + generator.uniform(0.0, 0.006), 0.86 ** index, 7000.0 - index * 300.0) for index in range(8)]
		flutter = [(0.05 + index * 0.047, 0.6 * 0.72 ** index, 5000.0) for index in range(10)]

		return blend([(taps(generator, 2.4, slaps + flutter), 0.55), (diffuse(generator, 2.4, (1.7, 1.4, 0.6), 0.008, 10000.0), 0.45)])

	early = [(0.002 + index * 0.0009 + generator.uniform(0.0, 0.0008), 0.92 ** index, 11000.0) for index in range(36)]

	return blend([(taps(generator, 1.3, early), 0.4), (diffuse(generator, 1.3, (0.75, 0.62, 0.38), 0.003, 12000.0), 0.6)])


def blast(generator, duration, length):
	time = numpy.arange(length) / rate
	pulse = (1.0 - time / duration) * numpy.exp(-1.8 * time / duration)
	pulse = numpy.where(time < duration * 6.0, pulse, 0.0)
	bounce = numpy.zeros(length)
	offset = int(rate * generator.uniform(0.003, 0.0045))
	bounce[offset:] = lowpass(pulse, 6000.0, 1)[:length - offset] * 0.6

	return pulse + bounce


def thump(generator, frequency, decay, length):
	time = numpy.arange(length) / rate
	sweep = 2.0 * numpy.pi * frequency * (time - 0.35 * time * time / max(decay * 4.0, 1e-3))

	return numpy.sin(sweep + generator.uniform(0.0, 0.4)) * numpy.exp(-time / decay) * (1.0 - numpy.exp(-time / 0.0015))


def close_layer(piece, keep, crack, weight):
	piece = highpass(piece, 28.0, 2)[:int(rate * keep)]
	piece = normalize(fade(piece, 0.0005, keep * 0.55), 1.0)

	return normalize(piece * 0.72 + crack[:len(piece)] * 0.85 + weight[:len(piece)] * 0.55, 0.97)


def far_layer(piece, generator, cutoff, weight):
	source = piece[:int(rate * 0.4)].copy()
	source = normalize(source, 1.0) + weight[:len(source)] * 0.9
	body = lowpass(numpy.concatenate([source, numpy.zeros(int(rate * 0.05))]), cutoff, 2)
	body = shape(body, lambda frequency: 1.0 + 1.6 * numpy.exp(-((frequency - 90.0) / 60.0) ** 2))
	length = int(rate * 3.0)
	time = numpy.arange(length) / rate
	rolling = rumble(generator, 3.0, 36, 350.0, 900.0).mean(axis=1)
	tail = lowpass(generator.standard_normal(length), 700.0, 2) * numpy.exp(-6.91 * time / 2.6) * (1.0 - numpy.exp(-time / 0.08))
	impulse = unit(rolling) * 0.45 + unit(tail) * 0.55
	impulse[0] = 1.0

	return normalize(fade(convolve(body, impulse)[:length], 0.0005, 1.2), 0.9)


def clack(generator, length, notes, decay, thunk):
	time = numpy.arange(length) / rate
	burst = bandpass(generator.standard_normal(length), 1500.0, 9500.0) * numpy.exp(-time / 0.0022)
	ring = numpy.zeros(length)

	for index, (frequency, amplitude) in enumerate(notes):
		ring += amplitude * numpy.sin(2.0 * numpy.pi * frequency * (1.0 + generator.uniform(-0.02, 0.02)) * time + generator.uniform(0.0, 6.28)) * numpy.exp(-time / (decay * (1.0 - 0.12 * index)))

	low = numpy.sin(2.0 * numpy.pi * thunk * time) * numpy.exp(-time / 0.012) * (0.6 if thunk > 0.0 else 0.0)

	return burst + ring * 0.5 + low


def mechanism(generator, kind):
	length = int(rate * 0.3)
	result = numpy.zeros(length)

	for start, gain in mechanisms[kind]:
		offset = int(rate * (start + generator.uniform(0.0, 0.003)))
		part = clack(generator, length - offset, partials[kind], 0.03 if kind == "carrier" else 0.02, 160.0 if kind == "carrier" else (220.0 if kind == "slide" else 0.0))
		result[offset:] += part * gain

	return normalize(fade(result, 0.0, 0.08), 0.85)


def casing(generator, surface):
	length = int(rate * 0.75)
	time = numpy.arange(length) / rate
	result = numpy.zeros(length)
	spins = {
		"hard": ([0.0, 0.13, 0.22, 0.28, 0.31], [1.0, 0.55, 0.32, 0.18, 0.1], 0.09, 1.0),
		"wood": ([0.0, 0.1, 0.17], [1.0, 0.45, 0.2], 0.025, 0.55),
		"soft": ([0.0, 0.07], [1.0, 0.3], 0.006, 0.15),
	}
	times, gains, decay, shine = spins[surface]
	notes = [frequency * (1.0 + generator.uniform(-0.03, 0.03)) for frequency in (3150.0, 5420.0, 7980.0, 10900.0)]

	for moment, gain in zip(times, gains):
		offset = int(rate * (moment + generator.uniform(-0.012, 0.012)))

		if offset < 0 or offset >= length:
			continue

		local = time[:length - offset]
		click = bandpass(generator.standard_normal(len(local)), 2000.0, 10000.0) * numpy.exp(-local / 0.0009)
		ring = sum(numpy.sin(2.0 * numpy.pi * note * local + generator.uniform(0.0, 6.28)) * numpy.exp(-local / (decay * (1.0 - 0.15 * index))) * (0.7 ** index) for index, note in enumerate(notes))
		knock = numpy.sin(2.0 * numpy.pi * (520.0 if surface == "wood" else 180.0) * local) * numpy.exp(-local / (0.02 if surface == "wood" else 0.015))
		result[offset:] += gain * (click * 0.6 + ring * shine * 0.5 + knock * (0.8 if surface != "hard" else 0.05))

	if surface == "hard":
		roll = times[-1] + 0.02

		for index in range(10):
			offset = int(rate * (roll + index * generator.uniform(0.014, 0.026)))

			if offset < length:
				local = time[:length - offset]
				result[offset:] += 0.08 * (0.82 ** index) * numpy.sin(2.0 * numpy.pi * notes[0] * local) * numpy.exp(-local / 0.02)

	return normalize(fade(result, 0.0, 0.1), 0.8)


def recording(name):
	return load(os.path.join(recordings, name))


def stereo(name):
	data = aud.Sound(os.path.join(recordings, name)).resample(rate, False).data().astype(numpy.float64)

	return data if data.ndim > 1 else numpy.stack([data, data], axis=1)


def events(samples, spacing, share):
	frame = int(rate * 0.005)
	count = len(samples) // frame
	energy = numpy.abs(samples[:count * frame]).reshape(count, frame).max(axis=1)
	threshold = energy.max() * share
	found = []
	last = -spacing * 1000.0

	for index in range(1, count):
		time = index * 0.005

		if energy[index] > threshold and energy[index] > energy[index - 1] * 2.5 and time - last > spacing:
			found.append(max(0, index * frame - int(rate * 0.006)))
			last = time

	return found


def clip(samples, start, seconds, tail):
	piece = samples[start:start + int(rate * seconds)].copy()

	return fade(highpass(piece, 25.0, 2), 0.0005, seconds * tail)


def single(name, seconds, share=0.3):
	samples = recording(name)
	found = events(samples, 0.2, share)
	start = found[0] if found else max(0, int(numpy.argmax(numpy.abs(samples))) - int(rate * 0.006))

	return clip(samples, start, seconds, 0.4)


def peaks(samples, share, spacing, count):
	frame = int(rate * 0.005)
	total = len(samples) // frame
	energy = numpy.abs(samples[:total * frame]).reshape(total, frame).max(axis=1)
	threshold = energy.max() * share
	found = []

	for index in range(1, total - 1):
		if energy[index] > threshold and energy[index] >= energy[index - 1] and energy[index] > energy[index + 1] and (not found or index * frame - found[-1] > spacing * rate):
			found.append(index * frame)

	return [max(0, start - int(rate * 0.004)) for start in found[:count]]


def compose(parts, seconds):
	result = numpy.zeros(int(rate * seconds))

	for piece, offset in parts:
		begin = int(rate * offset)
		end = min(len(result), begin + len(piece))
		result[begin:end] += piece[:end - begin]

	return result


def clear(prefix):
	for name in os.listdir(output):
		stem = name[:-4]

		if name.endswith(".wav") and stem.startswith(prefix + "_") and stem[len(prefix) + 1:].isdigit():
			os.remove(os.path.join(output, name))


def series(prefix, pieces):
	clear(prefix)

	for index, piece in enumerate(pieces):
		write("%s_%d" % (prefix, index), piece)


def crest(piece):
	head = piece[:int(rate * 0.05)]

	return numpy.abs(head).max() / max(numpy.sqrt((head ** 2).mean()), 1e-9)


def shooter(piece):
	return lowpass(shape(piece, lambda frequency: 1.0 + 0.8 * numpy.exp(-((frequency - 110.0) / 90.0) ** 2)), 9000.0, 1)


def recorded(generator):
	rooms = {"city": (stereo("ir_rome_apartment_alley.wav"), stereo("ir_rome_apartment_alley.wav")), "room": (stereo("ir_bunker_rear_center.wav"), stereo("ir_basement.wav"))}

	for family, near_name, own_name, keep, far_name in takes:
		near = recording(near_name)
		own = recording(own_name)
		near_pieces = [clip(near, start, keep, 0.5) for start in events(near, 0.8, 0.3)[:4]]
		own_pieces = [clip(own, start, keep, 0.5) for start in events(own, 0.8, 0.3)[:5]]

		if near_name == own_name:
			own_pieces = [shooter(piece) for piece in own_pieces]

		series("gun_%s_close" % family, [normalize(piece, 0.97) for piece in near_pieces])
		series("gun_%s_self" % family, [normalize(piece, 0.97) for piece in own_pieces])

		if far_name:
			distant = recording(far_name)
			pieces = [distant[start:start + int(rate * 1.5)] for start in events(distant, 0.8, 0.3)[:4]]
			weight = thump(generator, 70.0, 0.06, int(rate * 1.5))
			far = [far_layer(piece, generator, 700.0, weight) for piece in pieces]

			if family == "bolt":
				rolling = recording("sse_distant_rifle_long_reverb.wav")
				far.append(normalize(fade(lowpass(rolling[events(rolling, 0.3, 0.3)[0]:], 3500.0, 2), 0.0005, 1.5), 0.9))

		else:
			distant = recording("sse_pistol_medium_distance.wav")
			far = [normalize(fade(lowpass(distant[start:start + int(rate * 1.8)], 5000.0, 2), 0.0005, 0.9), 0.9) for start in events(distant, 0.3, 0.3)[:4]]

		series("gun_%s_far" % family, far)

		for name, impulses in rooms.items():
			for index, impulse in enumerate(impulses):
				dry = fade(near_pieces[min(index, len(near_pieces) - 1)][:int(rate * 0.09)], 0.0, 0.03)
				wet = numpy.stack([convolve(dry, impulse[:, 0]), convolve(dry, impulse[:, 1])], axis=1)[:len(impulse) + int(rate * 0.09)]

				write("gun_%s_tail_%s_%d" % (family, name, index), normalize(fade(wet, 0.0, len(wet) / rate * 0.3), 0.9))

	series("bolt", [normalize(compose([(single("ffl_mosin_M_2.wav", 0.3), 0.0), (single("ffl_mosin_M_3.wav", 0.3), 0.13), (single("ffl_mosin_M_5.wav", 0.35), 0.33), (single("ffl_mosin_M_7.wav", 0.3), 0.48)], 0.95), 0.85)])
	series("dry_fire", [normalize(single(name, 0.35), 0.8) for name in ("ffl_ak_C_7.wav", "ffl_1911_A_19.wav", "ffl_mosin_M_10.wav")])
	series("reload_pistol", [normalize(compose([(single("ffl_1911_A_5.wav", 0.5), 0.25), (single("ffl_1911_A_4.wav", 0.7), 1.2), (single("ffl_1911_A_15.wav", 0.6), 1.95)], 2.6), 0.85)])
	series("reload_rifle", [normalize(compose([(single("ffl_ak_C_11.wav", 0.55), 0.35), (single("ffl_ak_C_10.wav", 0.55), 1.35), (single("ffl_ak_C_0.wav", 0.45), 2.0), (single("ffl_ak_C_1.wav", 0.45), 2.3)], 2.9), 0.85)])

	brass = recording("ffl_sw642_V_3.wav")
	for index, start in enumerate(peaks(brass, 0.12, 0.06, 4)):
		write("casing_hard_%d" % (6 + index), normalize(clip(brass, start, 0.35, 0.5), 0.8))

	passing = recording("sse_rifle_receiving_end.wav")
	cracks = sorted((clip(passing, start, 0.5, 0.5) for start in events(passing, 0.15, 0.3)[:16]), key=crest, reverse=True)[:4]
	series("bullet_crack", [normalize(piece, 0.9) for piece in cracks])

	splats = sorted(os.listdir(os.path.join(recordings, "wet_squish", "impsplat")))
	series("hit_flesh", [normalize(single(os.path.join("wet_squish", "impsplat", name), 0.45, 0.2), 0.85) for name in splats])


def tinnitus():
	length = rate * 4
	time = numpy.arange(length) / rate
	generator = numpy.random.default_rng(4100)
	tone = 0.6 * numpy.sin(2.0 * numpy.pi * 4100.0 * time) + 0.4 * numpy.sin(2.0 * numpy.pi * 4102.5 * time)
	hiss = bandpass(generator.standard_normal(length), 3800.0, 4400.0)

	return normalize(tone + hiss / numpy.abs(hiss).max() * 0.05, 0.5)


def main():
	os.makedirs(output, exist_ok=True)

	generator = numpy.random.default_rng(1911)
	impulses = {name: response(generator, name) for name in environments}

	for family, path, spacing, keep, cutoff, kind, sharpness, low, ring in families:
		samples = load(path)
		starts = onsets(samples, spacing * 0.8)[:4]

		print("gunsounds: %s onsets at %s" % (family, ", ".join("%.2f" % (start / rate) for start in starts)))

		for index, start in enumerate(starts):
			piece = samples[start:start + int(rate * 1.5)].copy()
			crack = blast(generator, sharpness * generator.uniform(0.9, 1.1), len(piece))
			weight = thump(generator, low * generator.uniform(0.94, 1.06), ring, len(piece))
			close = close_layer(piece, keep, crack, weight)

			write("gun_%s_close_%d" % (family, index), close)
			write("gun_%s_far_%d" % (family, index), far_layer(piece, generator, cutoff, weight))
			write("gun_%s_mech_%d" % (family, index), mechanism(generator, kind))

			if index < 2:
				dry = fade(close[:int(rate * 0.09)], 0.0, 0.03)

				for name in environments:
					impulse = impulses[name]
					wet = numpy.stack([convolve(dry, impulse[:, 0]), convolve(dry, impulse[:, 1])], axis=1)[:len(impulse)]

					write("gun_%s_tail_%s_%d" % (family, name, index), normalize(fade(wet, 0.0, len(impulse) / rate * 0.3), 0.9))

	for surface in ("hard", "wood", "soft"):
		for index in range(6):
			write("casing_%s_%d" % (surface, index), casing(generator, surface))

	write("tinnitus", tinnitus())

	if os.path.isdir(recordings):
		recorded(generator)

	else:
		for family in ("pistol", "bolt", "auto"):
			for index in range(4):
				source_name = os.path.join(output, "gun_%s_close_%d.wav" % (family, index))

				if os.path.exists(source_name):
					with open(source_name, "rb") as reader, open(os.path.join(output, "gun_%s_self_%d.wav" % (family, index)), "wb") as writer:
						writer.write(reader.read())


main()
