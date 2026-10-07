import numpy
import os
import wave

root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
output = os.path.join(root, "raw", "audio")
rate = 44100


def write(name, samples):
	samples = numpy.clip(samples, -1.0, 1.0)
	pcm = (samples * 32767.0).astype(numpy.int16)

	with wave.open(os.path.join(output, name + ".wav"), "wb") as file:
		file.setnchannels(1)
		file.setsampwidth(2)
		file.setframerate(rate)
		file.writeframes(pcm.tobytes())

	print("audio: %-18s %6.2f s" % (name, len(samples) / rate))


def normalize(samples, peak):
	top = numpy.abs(samples).max()

	return samples * (peak / top) if top > 0.0 else samples


def unit(samples):
	return normalize(samples, 1.0)


def colored(count, generator, low, high):
	spectrum = numpy.fft.rfft(generator.standard_normal(count))
	frequency = numpy.fft.rfftfreq(count, 1.0 / rate)
	shape = 1.0 / numpy.sqrt(1.0 + (low / numpy.maximum(frequency, 1.0)) ** 4) / numpy.sqrt(1.0 + (frequency / high) ** 4)

	return unit(numpy.fft.irfft(spectrum * shape, count))


def lowpass(samples, cutoff):
	spectrum = numpy.fft.rfft(samples)
	frequency = numpy.fft.rfftfreq(len(samples), 1.0 / rate)

	return numpy.fft.irfft(spectrum / numpy.sqrt(1.0 + (frequency / cutoff) ** 4), len(samples))


def pulses(count, period, shape, strengths):
	track = numpy.zeros(count)

	for index in range(count // period):
		span = (index * period + numpy.arange(len(shape))) % count
		track[span] += shape * strengths[index % len(strengths)]

	return track


def engine(generator):
	count = rate * 2
	period = 1260
	local = numpy.arange(period * 3) / rate
	time = numpy.arange(count) / rate
	thump = numpy.sin(2.0 * numpy.pi * 78.0 * local) * numpy.exp(-local * 38.0) + generator.standard_normal(len(local)) * numpy.exp(-local * 90.0) * 0.45
	exhaust = unit(lowpass(pulses(count, period, thump, (1.0, 0.7, 0.92, 0.6, 0.97, 0.66, 0.85, 0.58)), 900.0))
	clatter = colored(count, generator, 1200.0, 4200.0) * unit(pulses(count, period // 2, numpy.exp(-local * 140.0), (1.0, 0.8)))
	rumble = colored(count, generator, 25.0, 160.0)
	whine = numpy.sin(2.0 * numpy.pi * 140.0 * time) * 0.5 + numpy.sin(2.0 * numpy.pi * 1050.0 * time) * 0.12
	hiss = colored(count, generator, 2000.0, 7000.0) * 0.05

	write("vehicle_engine", normalize(exhaust + rumble * 0.3 + clatter * 0.22 + whine * 0.06 + hiss, 0.82))


def rotor(generator):
	count = rate * 2
	period = 2940
	tail_period = 490
	local = numpy.arange(period) / rate
	tail_local = numpy.arange(tail_period) / rate
	time = numpy.arange(count) / rate
	whop = colored(period, generator, 120.0, 900.0) * (1.0 - numpy.exp(-local * 900.0)) * numpy.exp(-local * 42.0)
	thump = numpy.sin(2.0 * numpy.pi * 46.0 * local) * numpy.exp(-local * 30.0)
	blades = pulses(count, period, whop + thump * 0.8, (1.0, 0.86))
	tail = lowpass(pulses(count, tail_period, numpy.exp(-tail_local * 160.0) * numpy.sin(2.0 * numpy.pi * 180.0 * tail_local), (1.0,)), 600.0)
	turbine = numpy.sin(2.0 * numpy.pi * 3920.0 * time * (1.0 + 0.0015 * numpy.sin(2.0 * numpy.pi * 2.5 * time))) + 0.35 * numpy.sin(2.0 * numpy.pi * 7840.0 * time)
	growl = colored(count, generator, 140.0, 650.0)
	air = colored(count, generator, 300.0, 5000.0)

	write("vehicle_rotor", normalize(unit(blades) + unit(tail) * 0.18 + turbine * 0.035 + growl * 0.2 + air * 0.12, 0.85))


def main():
	generator = numpy.random.default_rng(7177)

	engine(generator)
	rotor(generator)


main()
