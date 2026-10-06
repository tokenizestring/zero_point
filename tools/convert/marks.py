import concurrent.futures
import math
import os
import numpy
from PIL import Image, ImageDraw

root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
output = os.path.join(root, "raw", "marks")
sheets = os.path.join(root, "previews", "marks")

grid = 8
cell = 256
over = 3
side = cell * over
guard = 11
ramp = 7
steep = math.tan(math.radians(70.0))
turn = 2.0 * math.pi
real = numpy.float32


def tint(red, green, blue):
	return numpy.array([red, green, blue], dtype=real) / 255.0


blood_thick = tint(105, 8, 10)
blood_thin = tint(146, 20, 13)
blood_deep = tint(86, 6, 9)

outline = [(0.0, -145.0), (20.0, -142.0), (34.0, -131.0), (40.0, -112.0), (40.5, -88.0), (39.0, -64.0), (38.5, -42.0), (41.0, -18.0), (46.0, 8.0), (51.0, 36.0), (53.5, 62.0), (51.5, 88.0), (45.0, 110.0), (34.0, 128.0), (19.0, 140.0), (-3.0, 145.0), (-23.0, 141.0), (-38.0, 130.0), (-47.5, 113.0), (-51.5, 92.0), (-51.5, 70.0), (-48.5, 47.0), (-43.0, 23.0), (-37.0, -2.0), (-34.0, -28.0), (-34.5, -52.0), (-37.0, -76.0), (-39.5, -100.0), (-39.0, -120.0), (-32.0, -134.0), (-19.0, -142.0)]


def smooth(low, high, value):
	slide = numpy.clip((value - low) / (high - low), 0.0, 1.0)

	return slide * slide * (3.0 - 2.0 * slide)


def mix(first, second, amount):
	return first + (second - first) * amount


def linear(value):
	return numpy.where(value <= 0.04045, value / 12.92, ((numpy.maximum(value, 0.0) + 0.055) / 1.055) ** 2.4)


def encoded(value):
	return numpy.where(value <= 0.0031308, value * 12.92, 1.055 * numpy.maximum(value, 0.0) ** (1.0 / 2.4) - 0.055)


def grow(field, size):
	return numpy.asarray(Image.fromarray(numpy.ascontiguousarray(field, dtype=real)).resize((size, size), Image.BICUBIC), dtype=real)


def shrink(field, factor):
	rows = field.shape[0] // factor
	columns = field.shape[1] // factor

	return field.reshape(rows, factor, columns, factor).mean(axis=(1, 3))


def noise(rng, rows, columns, low, high, slope, wide=1.0, tall=1.0):
	across = (numpy.fft.rfftfreq(columns)[None, :] * (columns * wide)).astype(real)
	along = (numpy.fft.fftfreq(rows)[:, None] * (rows * tall)).astype(real)
	pitch = across * across + along * along
	pitch[0, 0] = 1.0
	gain = pitch ** real(-0.5 * slope) * numpy.exp(pitch * real(-1.0 / (high * high))) * (1.0 - numpy.exp(pitch * real(-1.0 / (low * low))))
	gain[0, 0] = 0.0
	field = numpy.fft.irfft2(numpy.fft.rfft2(rng.standard_normal((rows, columns), dtype=real)) * gain, s=(rows, columns))

	return (field / field.std()).astype(real)


def cloud(rng, low, high, slope, wide=1.0, tall=1.0):
	size = side

	while size > 96 and size >= 8.0 * high / min(wide, tall):
		size //= 2

	field = noise(rng, size, size, low, high, slope, wide, tall)

	return field if size == side else grow(field, side)


def loop(rng, low, high, slope, count=2048):
	wave = numpy.fft.rfftfreq(count) * count
	wave[0] = 1.0
	gain = wave ** -slope * numpy.exp(-(wave / high) ** 2) * (1.0 - numpy.exp(-(wave / low) ** 2))
	gain[0] = 0.0
	curve = numpy.fft.irfft(numpy.fft.rfft(rng.standard_normal(count)) * gain, n=count)

	return (curve / curve.std()).astype(real)


def around(curve, spin):
	place = (spin / turn % 1.0) * len(curve)
	left = numpy.floor(place).astype(numpy.intp)
	shift = (place - left).astype(real)
	left %= len(curve)

	return mix(curve[left], curve[(left + 1) % len(curve)], shift)


def haze(field, across, along):
	rows, columns = field.shape
	wave_x = (numpy.fft.rfftfreq(columns)[None, :] * across).astype(real)
	wave_y = (numpy.fft.fftfreq(rows)[:, None] * along).astype(real)
	gain = numpy.exp((wave_x * wave_x + wave_y * wave_y) * real(-2.0 * math.pi ** 2))

	return numpy.fft.irfft2(numpy.fft.rfft2(field) * gain, s=(rows, columns)).astype(real)


def blur(field, across, along=None):
	along = across if along is None else along
	factor = 1

	while factor < 8 and min(across, along) >= 5.0 * factor and field.shape[0] % (factor * 2) == 0 and field.shape[0] // (factor * 2) >= 64:
		factor *= 2

	if factor == 1:
		return haze(field, across, along)

	return grow(haze(shrink(field, factor), across / factor, along / factor), field.shape[0])


def plane(edge):
	step = edge * 1000.0 / side
	axis = ((numpy.arange(side) + 0.5 - side * 0.5) * step).astype(real)
	x, y = numpy.meshgrid(axis, axis)

	return x, y, step


def pin(x, y, step):
	return (x / step + side * 0.5 - 0.5, y / step + side * 0.5 - 0.5)


def pad():
	image = Image.new("L", (side, side), 0)

	return image, ImageDraw.Draw(image)


def taken(image):
	return numpy.asarray(image, dtype=real) / 255.0


def patch(x, y, reach, step, base=None):
	top = 0 if base is None else base[0].start
	left = 0 if base is None else base[1].start
	rows = side if base is None else base[0].stop - top
	columns = side if base is None else base[1].stop - left
	first = min(max(int((y - reach) / step + side * 0.5) - top, 0), rows)
	last = min(max(int((y + reach) / step + side * 0.5) + 1 - top, 0), rows)
	start = min(max(int((x - reach) / step + side * 0.5) - left, 0), columns)
	stop = min(max(int((x + reach) / step + side * 0.5) + 1 - left, 0), columns)

	return slice(first, last), slice(start, stop)


def coat(paint, alpha, color, cover):
	keep = 1.0 - cover
	paint *= keep[:, :, None]
	paint += color * cover[:, :, None]
	alpha *= keep
	alpha += cover


def blank():
	return numpy.zeros((side, side, 3), dtype=real), numpy.zeros((side, side), dtype=real)


def flat():
	return numpy.zeros((side, side), dtype=real)


def facets(rng, count, reach, spread, lean=0.0, toward=0.0):
	angles = (numpy.arange(count) + rng.uniform(-0.38, 0.38, count)) * turn / count + rng.uniform(0.0, turn)
	reaches = reach * rng.uniform(1.0 - spread, 1.0 + spread, count) * (1.0 + lean * numpy.cos(angles - toward))

	return angles, reaches


def gauge(x, y, angles, reaches):
	level = numpy.full(x.shape, -1e9, dtype=real)

	for angle, reach in zip(angles, reaches):
		numpy.maximum(level, (x * real(math.cos(angle) / reach) + y * real(math.sin(angle) / reach)), out=level)

	return level


def rim(angles, reaches, angle):
	return 1.0 / max(math.cos(angle - spoke) / reach for spoke, reach in zip(angles, reaches))


def spokes(rng, x, y, reach, low, high, slope, rings):
	rows = 64
	columns = 1024
	table = noise(rng, rows, columns, low, high, slope, 1.0, rings)
	column = (numpy.arctan2(y, x) / turn % 1.0) * columns
	row = numpy.clip(numpy.sqrt(x * x + y * y) / reach, 0.0, 1.0) * (rows - 1)
	left = numpy.floor(column).astype(numpy.intp)
	upper = numpy.floor(row).astype(numpy.intp)
	shift = (column - left).astype(real)
	drop = (row - upper).astype(real)
	left %= columns
	right = (left + 1) % columns
	lower = numpy.minimum(upper + 1, rows - 1)

	return mix(mix(table[upper, left], table[upper, right], shift), mix(table[lower, left], table[lower, right], shift), drop)


def shards(rng, u, v, step, reach, pitch, tilt, shift, base):
	near = numpy.full(u.shape, 1e9, dtype=real)
	level = numpy.zeros(u.shape, dtype=real)
	count = int(2.0 * reach / pitch) + 1

	for row in range(count):
		for column in range(count):
			x = (column - (count - 1) * 0.5 + rng.uniform(-0.75, 0.75)) * pitch
			y = (row - (count - 1) * 0.5 + rng.uniform(-0.75, 0.75)) * pitch
			area = patch(x, y, pitch * 3.0, step, base)
			across = u[area] - real(x)
			along = v[area] - real(y)
			far = across * across + along * along
			closer = far < near[area]
			level[area] = numpy.where(closer, real(rng.normal(0.0, shift)) + real(rng.normal(0.0, tilt)) * across + real(rng.normal(0.0, tilt)) * along, level[area])
			near[area] = numpy.where(closer, far, near[area])

	return level


def pebbles(rng, u, v, step, reach, count, palette, base):
	bump = numpy.zeros(u.shape, dtype=real)
	stain = numpy.zeros(u.shape + (3,), dtype=real)
	blend = numpy.zeros(u.shape, dtype=real)
	sizes = numpy.sort(numpy.clip(rng.lognormal(math.log(1.1), 0.62, count), 0.45, 5.5))[::-1]
	spots = numpy.zeros((count, 3))
	placed = 0

	for size in sizes:
		for attempt in range(10):
			x, y = rng.uniform(-reach, reach, 2)

			if placed == 0 or numpy.all(numpy.hypot(spots[:placed, 0] - x, spots[:placed, 1] - y) > 0.95 * (spots[:placed, 2] + size)):
				break
		else:
			continue

		spots[placed] = (x, y, size)
		placed += 1
		area = patch(x, y, size * 1.3 + 2.5, step, base)
		swing = rng.uniform(0.0, math.pi)
		squash = rng.uniform(0.6, 1.0)
		across = u[area] - real(x)
		along = v[area] - real(y)
		major = (across * real(math.cos(swing)) + along * real(math.sin(swing))) / real(size)
		minor = (along * real(math.cos(swing)) - across * real(math.sin(swing))) / real(size * squash)
		distance = numpy.sqrt(major * major + minor * minor)
		body = smooth(1.0, 0.8, distance)
		kind = rng.uniform()
		lift = size * rng.uniform(0.6, 1.0) * (0.34 if kind < 0.5 else (-0.24 if kind < 0.75 else 0.0))
		color = palette[int(rng.integers(len(palette)))] * rng.uniform(0.85, 1.12)
		strength = rng.uniform(0.35, 0.85)
		bump[area] += real(lift) * numpy.clip(1.0 - distance * distance, 0.0, 1.0) ** 0.75
		stain[area] += color * (body * real(strength) * (1.0 - 0.18 * smooth(0.55, 1.0, distance)))[:, :, None]
		blend[area] += body * real(strength)

	return bump, stain, blend


def fissure(rng, draw, step, x, y, heading, length, width, level=0):
	stride = 0.9
	drift = 0.0
	steps = max(int(length / stride), 2)

	for index in range(steps):
		along = index / steps
		drift = drift * 0.82 + rng.normal(0.0, 0.16)

		if rng.uniform() < 0.08:
			drift += rng.normal(0.0, 0.5)

		next_x = x + math.cos(heading + drift) * stride
		next_y = y + math.sin(heading + drift) * stride
		draw.line([pin(x, y, step), pin(next_x, next_y, step)], fill=int(255 * (1.0 - 0.8 * along ** 1.5)), width=max(1, int(round(width * (1.0 - along) ** 0.6 / step))))
		x = next_x
		y = next_y

		if level < 2 and index > 3 and rng.uniform() < 0.025:
			fissure(rng, draw, step, x, y, heading + drift + rng.choice([-1.0, 1.0]) * rng.uniform(0.4, 0.9), length * (1.0 - along) * rng.uniform(0.3, 0.7), width * (1.0 - along) ** 0.6 * 0.7, level + 1)


def concrete(rng, variant):
	edge = 0.16
	x, y, step = plane(edge)
	reach = (19.0, 22.5, 26.0, 29.5)[variant] * rng.uniform(0.96, 1.04)
	toward = rng.uniform(0.0, turn)
	area = patch(0.0, 0.0, reach * 1.8, step)
	u = (x + cloud(rng, 5.0, 24.0, 1.5) * 0.7 + cloud(rng, 24.0, 80.0, 1.2) * 0.24 + cloud(rng, 80.0, 190.0, 1.0) * 0.1)[area]
	v = (y + cloud(rng, 5.0, 24.0, 1.5) * 0.7 + cloud(rng, 24.0, 80.0, 1.2) * 0.24 + cloud(rng, 80.0, 190.0, 1.0) * 0.1)[area]
	far = numpy.sqrt(u * u + v * v)
	spin = numpy.arctan2(v, u)
	angles, reaches = facets(rng, 11, reach, 0.22, rng.uniform(0.15, 0.3), toward)
	main = gauge(u, v, angles, reaches)
	drop = rng.uniform(0.9, 1.5) * numpy.clip(0.75 + 0.5 * around(loop(rng, 1.0, 5.0, 1.0), spin), 0.15, 1.5)
	depth = drop * smooth(0.0, 0.55 / reach, 1.0 - main) + rng.uniform(0.2, 0.26) * reach * numpy.clip(1.0 - main, 0.0, 1.0) ** 1.1

	for scab in range(int(rng.integers(3, 7))):
		angle = rng.uniform(0.0, turn)
		span = reach * rng.uniform(0.22, 0.5)
		middle = rim(angles, reaches, angle) * rng.uniform(0.8, 1.05)
		spot = patch(middle * math.cos(angle), middle * math.sin(angle), span * 1.5 + 3.0, step, area)
		sides, spans = facets(rng, int(rng.integers(5, 8)), span, 0.4)
		level = gauge(u[spot] - real(middle * math.cos(angle)), v[spot] - real(middle * math.sin(angle)), sides, spans)
		scar = smooth(0.0, 0.5 / span, 1.0 - level) * numpy.maximum(0.35, rng.uniform(0.6, 1.8) + rng.uniform(0.08, 0.2) * (middle - far[spot]))
		depth[spot] = numpy.maximum(depth[spot], scar)

	cover = smooth(0.0, 0.2, depth)
	facet = haze(shards(rng, u, v, step, reach * 1.7, rng.uniform(3.6, 5.2), 0.2, 0.1, area), 0.35 / step, 0.35 / step)
	depth += facet * smooth(0.3, 1.8, depth)
	depth += (0.3 * spokes(rng, u, v, reach * 1.6, 5.0, 45.0, 1.0, 5.0) + 0.22 * cloud(rng, 10.0, 45.0, 1.3)[area]) * smooth(0.5, 2.5, depth)
	palette = [tint(112, 110, 106), tint(150, 132, 106), tint(74, 76, 82), tint(212, 208, 200), tint(124, 94, 70), tint(104, 112, 100), tint(140, 138, 134), tint(92, 84, 76)]
	bump, stain, blend = pebbles(rng, u, v, step, reach * 1.6, int(reach * reach * 0.5), palette, area)
	depth -= bump * smooth(0.4, 1.4, depth)
	bore = rng.uniform(2.7, 3.7)
	pit = far / (bore * (1.0 + 0.13 * numpy.cos(2.0 * spin + rng.uniform(0.0, turn)) + 0.08 * numpy.cos(3.0 * spin + rng.uniform(0.0, turn)) + 0.05 * numpy.cos(5.0 * spin + rng.uniform(0.0, turn))))
	depth += rng.uniform(2.0, 3.0) * smooth(3.6, 0.9, pit) * cover
	depth += rng.uniform(7.0, 9.0) * smooth(1.15, 0.2, pit)
	depth += (cloud(rng, 22.0, 90.0, 1.0)[area] * 0.1 + cloud(rng, 90.0, 300.0, 0.6)[area] * 0.03) * cover
	height = flat()
	height[area] = -depth
	spread = flat()
	spread[area] = cover

	image, draw = pad()
	count = int(rng.integers(4, 8))

	for crack in range(count):
		angle = (crack + rng.uniform(-0.35, 0.35)) * turn / count + toward
		start = rim(angles, reaches, angle) * 0.85
		fissure(rng, draw, step, start * math.cos(angle), start * math.sin(angle), angle, min(66.0 - start, reach * (0.3 + 2.4 * rng.uniform() ** 2.0)), rng.uniform(0.25, 0.5))

	crack = taken(image) * (1.0 - spread)
	height -= blur(crack, 0.32 / step) * 0.9
	chips = flat()

	for pock in range(int(rng.integers(3, 7))):
		angle = rng.uniform(0.0, turn)
		middle = rim(angles, reaches, angle) * rng.uniform(1.12, 1.9)
		span = rng.uniform(0.5, 1.5)
		spot = patch(middle * math.cos(angle), middle * math.sin(angle), span * 1.6 + 1.0, step)
		sides, spans = facets(rng, int(rng.integers(4, 7)), span, 0.35)
		level = gauge(x[spot] - real(middle * math.cos(angle)), y[spot] - real(middle * math.sin(angle)), sides, spans)
		scar = smooth(0.0, 0.45, 1.0 - level)
		height[spot] -= scar * rng.uniform(0.25, 0.6) * (1.0 - spread[spot])
		chips[spot] = numpy.maximum(chips[spot], scar * (1.0 - spread[spot]))

	paint, alpha = blank()
	near = blur(spread, 1.6 / step)
	wide = blur(spread, 7.0 / step)
	patchy = numpy.clip(0.5 + 0.6 * cloud(rng, 2.0, 9.0, 1.6) + 0.25 * grow(spokes(rng, x[::4, ::4], y[::4, ::4], 80.0, 4.0, 40.0, 1.0, 6.0), side), 0.0, 1.3)
	dust = numpy.clip((0.16 * near + 0.34 * wide * patchy) * (0.7 + 0.3 * cloud(rng, 20.0, 160.0, 0.8)), 0.0, 0.5)
	coat(paint, alpha, tint(192, 187, 177), dust)
	coat(paint, alpha, tint(50, 46, 42), numpy.clip(crack * 0.85, 0.0, 1.0))
	coat(paint, alpha, tint(156, 152, 144), smooth(0.2, 0.7, chips) * 0.85)

	color = tint(166, 162, 154) * (1.0 + 0.07 * cloud(rng, 4.0, 30.0, 1.4)[area] + 0.04 * cloud(rng, 30.0, 120.0, 1.0)[area])[:, :, None]
	color = color * (1.0 - numpy.clip(blend, 0.0, 1.0))[:, :, None] + stain
	grain = cloud(rng, 100.0, 380.0, 0.2)[area]
	color *= (1.0 + 0.025 * grain + 0.1 * numpy.clip(facet, -1.0, 1.0))[:, :, None]
	color = mix(color, tint(70, 66, 62), (0.35 * smooth(2.0, 2.6, grain))[:, :, None])
	color = mix(color, tint(226, 223, 216), (0.3 * smooth(2.1, 2.7, -grain))[:, :, None])
	color = mix(color, tint(200, 197, 190), (0.45 * smooth(3.6, 1.2, pit))[:, :, None])
	color *= (1.0 - 0.22 * numpy.exp(-(far / (0.5 * reach)) ** 2) - 0.1 * smooth(0.5, 6.0, depth))[:, :, None]
	smear = smooth(0.7, 1.0, pit) * smooth(2.0, 1.2, pit) * smooth(0.1, 0.9, numpy.cos(spin - rng.uniform(0.0, turn))) * (0.6 + 0.4 * cloud(rng, 20.0, 90.0, 1.0)[area])
	color = mix(color, tint(104, 105, 110), numpy.clip(0.7 * smear, 0.0, 1.0)[:, :, None])
	color = mix(color, tint(36, 34, 33), smooth(1.05, 0.7, pit)[:, :, None])
	coat(paint[area], alpha[area], numpy.clip(color, 0.0, 1.0), cover)
	weight = numpy.maximum(smooth(0.02, 0.3, blur(numpy.maximum(spread, chips), 0.45 / step)), numpy.clip(blur(crack, 0.3 / step) * 1.6, 0.0, 0.6))

	return paint, alpha, height, weight, edge


def jagged(rng, knots, low, high, power, count):
	anchor = numpy.sort(rng.uniform(0.0, turn, knots))
	value = low + (high - low) * rng.uniform(0.0, 1.0, knots) ** power
	angle = numpy.arange(count) * turn / count

	return angle, numpy.interp(angle, anchor, value, period=turn)


def flake(rng, draw, step, x, y, reach, shade):
	count = int(rng.integers(4, 8))
	angle = (numpy.arange(count) + rng.uniform(-0.42, 0.42, count)) * turn / count + rng.uniform(0.0, turn)
	radius = reach * rng.uniform(0.4, 1.3, count)
	draw.polygon([pin(x + radius[index] * math.cos(angle[index]), y + radius[index] * math.sin(angle[index]), step) for index in range(count)], fill=shade)


def metal(rng, variant):
	edge = 0.1
	x, y, step = plane(edge)
	far = numpy.sqrt(x * x + y * y)
	spin = numpy.arctan2(y, x)
	lead = rng.uniform(0.0, turn)
	bore = (3.3, 4.1, 3.7, 3.05)[variant]
	skew = (0.03, 0.12, 0.07, 0.05)[variant]
	ring = numpy.arange(2048) * turn / 2048
	curve = 1.0 + skew * numpy.cos(2.0 * (ring - lead)) + 0.03 * loop(rng, 2.0, 9.0, 1.0)

	for nick in range(int(rng.integers(1, 4))):
		curve += rng.uniform(0.07, 0.18) * numpy.exp(-(((ring - rng.uniform(0.0, turn) + math.pi) % turn - math.pi) / rng.uniform(0.05, 0.11)) ** 2)

	curve = (curve * bore).astype(real)
	gap = far - around(curve, spin)
	span = gap / ((11.5, 13.0, 12.0, 10.5)[variant] * (1.0 + 0.2 * numpy.cos(spin - lead) + 0.07 * around(loop(rng, 1.0, 4.0, 1.0), spin)))
	sink = rng.uniform(2.6, 3.8)
	height = -sink * numpy.clip(1.0 - span, 0.0, 1.0) ** 1.8 + 0.1 * numpy.exp(-((span - 1.02) / 0.13) ** 2)
	height += rng.uniform(0.4, 0.6) * numpy.clip(0.6 + 0.5 * around(loop(rng, 6.0, 40.0, 0.8), spin), 0.15, 1.4) * numpy.exp(-((gap - 0.28) / 0.24) ** 2)
	height -= numpy.minimum(numpy.clip(-gap, 0.0, None) * 2.4, 3.0)

	angle, bare = jagged(rng, 11, 1.8, 5.0, 1.3, 120)
	extra = jagged(rng, 16, 0.1, (3.2, 4.5, 7.0, 3.0)[variant], 2.4, 120)[1]
	bare = bare + rng.normal(0.0, 0.1, 120)
	prime = bare + extra + rng.normal(0.0, 0.1, 120)
	edge_at = around(curve, angle)
	stripped, draw = pad()
	draw.polygon([pin((edge_at[index] + prime[index]) * math.cos(angle[index]), (edge_at[index] + prime[index]) * math.sin(angle[index]), step) for index in range(120)], fill=255)

	for chip in range(int(rng.integers(10, 26))):
		where = int(rng.integers(120))
		away = edge_at[where] + prime[where] + 0.3 + 6.0 * rng.uniform() ** 2.6
		flake(rng, draw, step, away * math.cos(angle[where] + rng.uniform(-0.03, 0.03)), away * math.sin(angle[where] + rng.uniform(-0.03, 0.03)), rng.uniform(0.18, 0.42) + 1.0 * rng.uniform() ** 3.0, 255)

	shiny, draw = pad()
	draw.polygon([pin((edge_at[index] + bare[index]) * math.cos(angle[index]), (edge_at[index] + bare[index]) * math.sin(angle[index]), step) for index in range(120)], fill=255)
	stripped = taken(stripped) * smooth(-0.3, -0.1, gap)
	shiny = taken(shiny) * smooth(-0.3, -0.1, gap)
	split, draw = pad()

	for crack in range(int(rng.integers(2, 6))):
		where = int(rng.integers(120))
		start = edge_at[where] + prime[where] - 0.3
		fissure(rng, draw, step, start * math.cos(angle[where]), start * math.sin(angle[where]), angle[where] + rng.uniform(-0.4, 0.4), rng.uniform(2.0, 8.0), step * 1.1, 2)

	split = taken(split) * (1.0 - stripped)
	height -= 0.1 * stripped + 0.05 * shiny + 0.06 * split

	paint, alpha = blank()
	smear = rng.uniform(0.0, turn)
	soot = (0.18 * numpy.exp(-numpy.clip(gap, 0.0, None) / 2.0) + 0.32 * numpy.exp(-numpy.clip(gap, 0.0, None) / (1.2 + 5.0 * numpy.clip(numpy.cos(spin - smear), 0.0, 1.0) ** 3.0))) * (0.6 + 0.4 * cloud(rng, 6.0, 50.0, 1.2))
	coat(paint, alpha, tint(34, 34, 36), numpy.clip(soot, 0.0, 0.45))
	coat(paint, alpha, tint(30, 30, 32), split * 0.6)
	coat(paint, alpha, tint(126, 128, 126) * (1.0 + 0.06 * cloud(rng, 6.0, 60.0, 1.0))[:, :, None] * (1.0 - 0.6 * numpy.clip(soot, 0.0, 0.5))[:, :, None], stripped)
	area = patch(0.0, 0.0, bore + 8.0, step)
	streak = spokes(rng, x[area], y[area], 14.0, 8.0, 60.0, 0.6, 2.0)
	wipe = numpy.exp(-numpy.clip(gap[area], 0.0, None) / 0.5) * numpy.clip(0.55 + 0.5 * around(loop(rng, 2.0, 12.0, 1.0), spin[area]), 0.0, 1.0)
	steel = tint(166, 168, 173) * ((1.0 + 0.14 * streak + 0.04 * cloud(rng, 20.0, 120.0, 1.0)[area]) * (1.0 - 0.62 * wipe))[:, :, None]
	coat(paint[area], alpha[area], numpy.clip(steel, 0.0, 1.0), shiny[area])
	coat(paint, alpha, tint(9, 9, 10), smooth(0.0, -0.22, gap))
	weight = numpy.maximum(smooth(1.12, 0.5, span), numpy.maximum(stripped, split * 0.5))

	return paint, alpha, height, weight, edge


def staves(rng, step, low, high):
	bounds = [0.0]

	while bounds[-1] < side:
		bounds.append(bounds[-1] + rng.uniform(low, high) / step)

	bounds = numpy.array(bounds)
	place = numpy.arange(side) + 0.5
	strand = numpy.clip(numpy.searchsorted(bounds, place) - 1, 0, len(bounds) - 2)
	lateral = ((place - bounds[strand]) / (bounds[strand + 1] - bounds[strand]) * 2.0 - 1.0).astype(real)
	middle = ((bounds[:-1] + bounds[1:]) * 0.5 - side * 0.5) * step

	return strand, len(bounds) - 1, lateral, middle


def tear(rng, reach, start, coarse, fine, splay, longest, deepest):
	chunk, chunks, middle = coarse[0], coarse[1], coarse[3]
	strand, strands, lateral = fine[0], fine[1], fine[2]
	length = (longest * numpy.clip(1.0 - ((middle - rng.uniform(-0.3, 0.3) * splay) / splay) ** 2, 0.0, 1.0) ** 0.8 * (0.3 + 0.7 * rng.uniform(0.0, 1.0, chunks) ** 0.8))[chunk] * ((0.7 + 0.3 * rng.uniform(0.0, 1.0, strands)) * numpy.where(rng.uniform(0.0, 1.0, strands) < 0.07, 1.6, 1.0))[strand]
	bottom = (deepest * rng.uniform(0.35, 1.0, chunks))[chunk] + rng.normal(0.0, 0.24, strands)[strand]
	kind = rng.integers(0, 4, strands)[strand]
	raised = (rng.uniform(0.0, 1.0, strands) < 0.13)[strand]
	run = (reach - start[None, :]) / numpy.maximum(length, 1e-3)[None, :].astype(real)
	tail = numpy.clip((run - 0.6) / 0.4, 0.0, 1.0)
	upper = 1.0 - tail * numpy.array([0.0, 1.0, 2.0, 0.0])[kind][None, :].astype(real)
	lower = -1.0 + tail * numpy.array([0.0, 1.0, 0.0, 2.0])[kind][None, :].astype(real)
	mask = smooth(0.0, 0.03, run) * smooth(1.0, 0.97, run) * smooth(0.0, 0.16, upper - lateral[None, :]) * smooth(0.0, 0.16, lateral[None, :] - lower) * (length > 0.3)[None, :]
	slope = numpy.clip(1.0 - run, 0.0, 1.0)
	relief = numpy.where(raised[None, :], 1.3 * slope ** 1.2, -slope ** 0.8) * numpy.clip(bottom, 0.2, None)[None, :].astype(real) * mask

	return mask, relief, run * length[None, :].astype(real), length


def timber(rng, variant):
	edge = 0.12
	x, y, step = plane(edge)
	area = (slice(0, side), patch(0.0, 0.0, 24.0, step)[1])
	x = x[area]
	y = y[area]
	axis = x[0]
	far = numpy.sqrt(x * x + y * y)
	bore = (3.4, 3.8, 3.1, 3.6)[variant]
	coarse = staves(rng, step, 1.0, 2.6)
	fine = staves(rng, step, 0.3, 0.8)
	coarse = (coarse[0][area[1]], coarse[1], coarse[2][area[1]], coarse[3])
	fine = (fine[0][area[1]], fine[1], fine[2][area[1]], fine[3])
	strand = fine[0]
	chord = bore * numpy.sqrt(numpy.clip(1.0 - (axis / bore) ** 2, 0.0, 1.0))
	ragged = numpy.clip(1.0 - (axis / bore) ** 2, 0.0, 1.0) ** 0.25
	above = chord + ((rng.uniform(0.0, 1.0, fine[1]) ** 2.0 * 1.3 - 0.22) * bore * 0.5)[strand] * ragged
	below = chord + ((rng.uniform(0.0, 1.0, fine[1]) ** 2.0 * 1.3 - 0.22) * bore * 0.5)[strand] * ragged
	hole = smooth(0.0, 1.5 * step, above[None, :] + y) * smooth(0.0, 1.5 * step, below[None, :] - y) * (numpy.abs(axis) < bore)[None, :]
	splay = bore * rng.uniform(1.25, 1.6)
	high, rise, climb, top = tear(rng, -y, numpy.clip(above, 0.0, None), coarse, fine, splay, (16.0, 30.0, 8.0, 13.0)[variant], 1.8)
	low, fall, descent, base = tear(rng, y, numpy.clip(below, 0.0, None), coarse, fine, splay, (10.0, 9.0, 24.0, 22.0)[variant], 1.8)
	torn = numpy.maximum(high, low) * (1.0 - hole)
	height = (rise + fall) * (1.0 - hole)
	away = numpy.where(y < 0.0, climb, descent)
	fibre = cloud(rng, 40.0, 300.0, 0.4, 1.0, 22.0)[area]
	band = cloud(rng, 8.0, 40.0, 1.2, 1.0, 30.0)[area]
	height += 0.07 * fibre * torn
	height -= 0.9 * numpy.exp(-(far / (2.2 * bore)) ** 2)
	height -= 6.0 * haze(hole, 0.35 / step, 0.35 / step)

	split, draw = pad()

	for crack in range(int(rng.integers(1, 4))):
		place = rng.uniform(-0.9, 0.9) * bore
		heading = rng.choice([-1.0, 1.0])
		reach = bore * 0.8
		length = rng.uniform(12.0, 46.0)
		steps = int(length / 1.2)

		for index in range(steps):
			shift = place + rng.normal(0.0, 0.05) + (rng.choice([-1.0, 1.0]) * rng.uniform(0.25, 0.5) if rng.uniform() < 0.06 else 0.0)
			draw.line([pin(place, heading * reach, step), pin(shift, heading * (reach + 1.2), step)], fill=int(255 * (1.0 - 0.85 * (index / steps) ** 1.5)), width=2 if index < steps * 0.3 else 1)
			place = shift
			reach += 1.2

	split = taken(split)[area] * (1.0 - torn) * (1.0 - hole)
	hairs, draw = pad()

	for hair in range(int(rng.integers(8, 17))):
		column = int(rng.integers(len(axis)))
		heading = rng.choice([-1.0, 1.0])
		limit = (top if heading < 0.0 else base)[column]

		if limit < 1.0 or abs(axis[column]) > splay:
			continue

		reach = chord[column] + limit * rng.uniform(0.55, 1.0)
		lean = rng.normal(0.0, 0.14)
		length = rng.uniform(1.0, 4.5)
		draw.line([pin(axis[column], heading * reach, step), pin(axis[column] + math.sin(lean) * length, heading * (reach + math.cos(lean) * length), step)], fill=int(rng.uniform(150, 255)), width=1)

	hairs = taken(hairs)[area] * (1.0 - hole)
	height += 0.45 * haze(hairs, 0.12 / step, 0.12 / step)
	height -= 0.35 * haze(split, 0.2 / step, 0.2 / step)

	paint, alpha = blank()
	full = flat()
	weight = flat()
	coat(paint[area], alpha[area], tint(44, 38, 33), numpy.clip(0.45 * numpy.exp(-numpy.clip(far - bore, 0.0, None) / 0.9) * (0.6 + 0.4 * cloud(rng, 10.0, 80.0, 1.0)[area]), 0.0, 1.0))
	coat(paint[area], alpha[area], tint(46, 33, 23), numpy.clip(split * 0.8, 0.0, 1.0))
	shade = rng.uniform(0.9, 1.1, fine[1])[strand][None, :].astype(real)
	color = mix(tint(216, 186, 134), tint(176, 128, 76), (0.75 * smooth(0.4, 1.3, band))[:, :, None]) * ((1.0 + 0.07 * fibre) * shade * (1.0 - 0.3 * numpy.exp(-away / 1.8)) * (1.0 - 0.06 * numpy.clip(-height, 0.0, 2.0)))[:, :, None]
	coat(paint[area], alpha[area], numpy.clip(color, 0.0, 1.0), torn)
	coat(paint[area], alpha[area], tint(230, 206, 162), hairs * 0.85)
	coat(paint[area], alpha[area], tint(22, 16, 12), hole)
	full[area] = height
	weight[area] = numpy.maximum(numpy.maximum(torn, hole), numpy.maximum(0.95 * numpy.exp(-(far / (2.9 * bore)) ** 2), numpy.maximum(split * 0.55, hairs * 0.7)))

	return paint, alpha, full, weight, edge


def earth(rng, variant):
	edge = 0.22
	x, y, step = plane(edge)
	u = x + cloud(rng, 3.0, 14.0, 1.6) * 2.2 + cloud(rng, 14.0, 60.0, 1.3) * 0.6
	v = y + cloud(rng, 3.0, 14.0, 1.6) * 2.2 + cloud(rng, 14.0, 60.0, 1.3) * 0.6
	lead = rng.uniform(0.0, turn)
	major = u * real(math.cos(lead)) + v * real(math.sin(lead))
	minor = v * real(math.cos(lead)) - u * real(math.sin(lead))
	spin = numpy.arctan2(minor, major)
	reach = (23.0, 29.0)[variant]
	level = numpy.sqrt((major / rng.uniform(1.15, 1.4)) ** 2 + minor * minor) / (reach * (1.0 + 0.16 * around(loop(rng, 1.5, 6.0, 1.0), spin)))
	forward = numpy.clip(numpy.cos(spin), 0.0, 1.0) ** 1.5
	clumps = 1.0 - numpy.abs(cloud(rng, 9.0, 32.0, 1.0)) * 1.25
	lumps = 1.0 - numpy.abs(cloud(rng, 32.0, 110.0, 0.9)) * 1.25
	grit = cloud(rng, 110.0, 300.0, 0.4)
	depth = (12.0, 14.0)[variant] * numpy.clip(1.0 - level * level, 0.0, 1.0) ** 1.3
	crest = numpy.clip(2.2 + 3.4 * forward + 1.4 * around(loop(rng, 2.0, 8.0, 1.0), spin), 0.5, None) * numpy.exp(-((level - 1.12) / 0.2) ** 2)
	apron = numpy.exp(-numpy.clip(level - 1.0, 0.0, None) / 0.55) * (0.35 + 0.9 * forward) * numpy.clip(0.6 + 0.5 * cloud(rng, 3.0, 12.0, 1.4), 0.0, 1.5)
	loose = numpy.clip(0.55 * smooth(1.3, 0.9, level) + apron * 1.3, 0.0, 1.0)
	height = -depth + crest * (0.8 + 0.2 * clumps) + loose * (0.7 * clumps + 0.25 * lumps + 0.06 * grit) + 1.0 * apron
	ring = numpy.exp(-((level - 1.3) / 0.35) ** 2) * numpy.clip(0.6 + 0.6 * cloud(rng, 4.0, 20.0, 1.3), 0.0, 1.2)
	stain = numpy.clip(0.5 * smooth(1.25, 0.4, level) + 0.34 * apron * (0.6 + 0.4 * clumps) + 0.16 * ring, 0.0, 0.58) * (0.88 + 0.12 * lumps)
	weight = smooth(2.5, 1.4, level)
	paint, alpha = blank()
	shade = numpy.clip(0.45 + 0.25 * lumps + 0.2 * clumps + 0.1 * grit - 0.55 * smooth(0.95, 0.15, level), 0.0, 1.0)
	coat(paint, alpha, mix(tint(40, 31, 23), tint(74, 59, 44), shade[:, :, None]), numpy.clip(stain, 0.0, 1.0))

	for clod in range(int(rng.integers(5, 9))):
		angle = lead + rng.normal(0.0, 0.9)
		away = reach * rng.uniform(1.45, 2.6)
		size = rng.uniform(2.4, 4.4) + 3.0 * rng.uniform() ** 3.0
		spot = patch(away * math.cos(angle), away * math.sin(angle), size * 1.5 + 5.0, step)
		sides, spans = facets(rng, int(rng.integers(5, 8)), size, 0.3)
		body = gauge(u[spot] - real(away * math.cos(angle)), v[spot] - real(away * math.sin(angle)), sides, spans)
		mound = numpy.clip(1.0 - body ** 2.0, 0.0, 1.0) ** 0.9
		height[spot] += size * rng.uniform(0.45, 0.65) * mound * (0.8 + 0.2 * lumps[spot]) + 1.0 * numpy.exp(-(body / 1.5) ** 2) * (0.5 + 0.5 * lumps[spot])
		coat(paint[spot], alpha[spot], mix(tint(46, 36, 26), tint(80, 64, 47), (0.35 + 0.35 * lumps[spot])[:, :, None]), smooth(1.25, 0.6, body) * 0.45)
		weight[spot] = numpy.maximum(weight[spot], smooth(1.9, 1.1, body))

	return paint, alpha, height, weight, edge


def sand(rng, variant):
	edge = 0.26
	x, y, step = plane(edge)
	u = x + cloud(rng, 2.0, 9.0, 1.6) * 1.6
	v = y + cloud(rng, 2.0, 9.0, 1.6) * 1.6
	lead = rng.uniform(0.0, turn)
	major = u * real(math.cos(lead)) + v * real(math.sin(lead))
	minor = v * real(math.cos(lead)) - u * real(math.sin(lead))
	spin = numpy.arctan2(minor, major)
	reach = (24.0, 29.0)[variant]
	level = numpy.sqrt((major / rng.uniform(1.04, 1.16)) ** 2 + minor * minor) / (reach * (1.0 + 0.06 * around(loop(rng, 1.5, 5.0, 1.2), spin)))
	forward = numpy.clip(numpy.cos(spin), 0.0, 1.0)
	bowl = -0.36 * reach * numpy.clip(1.0 - level * level, 0.0, 1.0)
	crest = numpy.clip(2.3 + 1.2 * forward + 0.9 * around(loop(rng, 1.0, 5.0, 1.0), spin), 0.8, None) * numpy.exp(-((level - 1.13) / 0.2) ** 2)
	height = blur(bowl + crest, 1.3 / step)
	outer = numpy.clip(level - 1.0, 0.0, None)
	rays = spokes(rng, major, minor, reach * 3.6, 9.0, 80.0, 0.8, 5.0)
	spray = numpy.exp(-outer / 0.7) * smooth(0.95, 1.2, level) * (0.5 + 0.7 * forward)
	grit = cloud(rng, 60.0, 300.0, 0.3)
	height += 0.7 * rays * spray + 0.5 * smooth(0.6, 1.8, cloud(rng, 25.0, 100.0, 0.8)) * spray + 0.08 * grit * smooth(3.0, 1.5, level)
	paint, alpha = blank()
	damp = 0.32 * smooth(1.05, 0.25, level) * (0.85 + 0.15 * cloud(rng, 6.0, 40.0, 1.0)) + 0.14 * spray * numpy.clip(0.5 + 0.6 * rays + 0.3 * grit, 0.0, 1.5)
	coat(paint, alpha, tint(100, 80, 56), numpy.clip(damp, 0.0, 0.4))
	weight = smooth(3.1, 1.7, level)

	return paint, alpha, height, weight, edge


def rounded(points, rounds):
	points = numpy.asarray(points, dtype=numpy.float64)

	for cycle in range(rounds):
		ahead = numpy.roll(points, -1, axis=0)
		points = numpy.stack([points * 0.75 + ahead * 0.25, points * 0.25 + ahead * 0.75], axis=1).reshape(-1, 2)

	return points


def inset(points, distance):
	ahead = numpy.roll(points, -1, axis=0) - numpy.roll(points, 1, axis=0)
	normal = numpy.stack([ahead[:, 1], -ahead[:, 0]], axis=1)
	normal /= numpy.linalg.norm(normal, axis=1)[:, None]
	area = 0.5 * numpy.sum(points[:, 0] * numpy.roll(points[:, 1], -1) - numpy.roll(points[:, 0], -1) * points[:, 1])

	return points - normal * distance * numpy.sign(area)


def trace(points, travel, distance):
	count = len(points)
	place = numpy.interp(numpy.asarray(distance) % travel[-1], travel, numpy.arange(count + 1))
	low = numpy.floor(place).astype(numpy.intp) % count
	part = (place - numpy.floor(place))[:, None]

	return points[low] * (1.0 - part) + points[(low + 1) % count] * part


def boot(rng, step, flip):
	ring = rounded(outline, 3)
	ring = inset(ring, 0.5 * loop(rng, 2.0, 9.0, 1.2, len(ring)).astype(numpy.float64)[:, None])
	travel = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.roll(ring, -1, axis=0) - ring, axis=1))])
	outer = inset(ring, 2.5)
	inner = inset(ring, 16.5)
	core = inset(ring, 22.5)
	sole, draw = pad()
	draw.polygon([pin(x * flip, -y, step) for x, y in ring], fill=255)
	tread, draw = pad()
	pitch = 21.5
	count = int(travel[-1] / pitch)
	pitch = travel[-1] / count
	phase = rng.uniform(0.0, pitch)

	for lug in range(count):
		start = phase + lug * pitch + rng.normal(0.0, 0.5)
		edge_line = trace(outer, travel, numpy.linspace(start, start + pitch - 6.5 + rng.normal(0.0, 0.5), 6))
		back = trace(inner, travel, numpy.linspace(start + pitch - 8.0, start + 1.5, 6))
		draw.polygon([pin(x * flip, -y, step) for x, y in numpy.concatenate([edge_line, back]) + rng.normal(0.0, 0.3, (12, 2))], fill=255)

	middle, brush = pad()
	brush.polygon([pin(x * flip, -y, step) for x, y in core], fill=255)
	bars, brush = pad()

	for bar in range(9):
		peak = -2.0 + 17.0 * bar
		brush.polygon([pin(x * flip, -y, step) for x, y in numpy.array([(-48.0, peak - 16.0), (0.5, peak - 5.0), (49.0, peak - 16.0), (49.0, peak - 5.5), (0.5, peak + 5.5), (-48.0, peak - 5.5)]) + rng.normal(0.0, 0.35, (6, 2))], fill=255)

	for bar in range(5):
		peak = -74.0 - 16.0 * bar
		brush.polygon([pin(x * flip, -y, step) for x, y in numpy.array([(-42.0, peak + 13.0), (0.5, peak + 4.5), (42.0, peak + 13.0), (42.0, peak + 3.5), (0.5, peak - 5.0), (-42.0, peak + 3.5)]) + rng.normal(0.0, 0.35, (6, 2))], fill=255)

	return taken(sole), numpy.maximum(taken(tread), taken(middle) * taken(bars))


def stance(y):
	fore = smooth(-10.0, -4.0, -y)
	heel = smooth(-64.0, -70.0, -y)

	return fore, heel, (1.0 - fore - heel) * smooth(-62.0, -14.0, -y)


def mud(rng, variant):
	edge = 0.36
	x, y, step = plane(edge)
	sole, tread = boot(rng, step, 1.0 if variant else -1.0)
	fore, heel, arch = stance(y)
	press = 1.0 + 0.2 * cloud(rng, 1.5, 6.0, 1.5)
	pressed = sole * (fore + heel + arch)
	plate = sole * (fore * (3.2 + 0.6 * smooth(60.0, 140.0, -y)) + heel * 4.4 + arch * 2.4) * press
	stuck = smooth(0.5, 1.3, cloud(rng, 5.0, 22.0, 1.2))
	studs = tread * (fore * 4.2 + heel * 4.8) * numpy.clip(0.85 + 0.3 * cloud(rng, 4.0, 20.0, 1.2), 0.3, 1.2) * (1.0 - 0.85 * stuck)
	depth = blur(plate, 1.0 / step) + blur(studs, 0.6 / step)
	depth = numpy.maximum(depth, 0.45 * numpy.roll(depth, int(rng.uniform(4.0, 7.0) / step), axis=0) * heel)
	soft = blur(pressed, 0.8 / step)
	squeeze = blur(pressed, 4.5 / step)
	lumps = cloud(rng, 20.0, 120.0, 1.0)
	ridge = 6.0 * squeeze * (1.0 - soft) * numpy.clip(0.7 + 0.55 * cloud(rng, 3.0, 16.0, 1.3), 0.15, 1.6)
	height = -depth + ridge + lumps * (0.06 + 0.3 * squeeze * (1.0 - soft) + 0.35 * stuck * soft) + 0.5 * stuck * soft * cloud(rng, 8.0, 40.0, 1.2)
	paint, alpha = blank()
	stain = numpy.clip(0.42 * soft + 0.16 * blur(tread, 0.8 / step) * (fore + heel) + 0.5 * squeeze * (1.0 - soft), 0.0, 0.62) * (0.88 + 0.12 * cloud(rng, 5.0, 40.0, 1.0))
	coat(paint, alpha, tint(46, 36, 26), numpy.clip(stain, 0.0, 1.0))
	weight = smooth(0.02, 0.22, blur(pressed, 6.0 / step))

	return paint, alpha, height, weight, edge


def dune(rng, variant):
	edge = 0.36
	x, y, step = plane(edge)
	sole, tread = boot(rng, step, 1.0 if variant else -1.0)
	fore, heel, arch = stance(y)
	press = 1.0 + 0.15 * cloud(rng, 1.5, 6.0, 1.5)
	pressed = sole * (fore + heel + arch)
	plate = sole * (fore * (2.8 + 1.8 * smooth(95.0, 140.0, -y)) + heel * (4.0 + 1.2 * smooth(-110.0, -140.0, -y)) + arch * 1.6) * press
	hint = numpy.clip(0.5 + 0.6 * cloud(rng, 3.0, 12.0, 1.3), 0.0, 1.0)
	depth = blur(plate, 3.2 / step) + 0.75 * blur(tread * (fore + heel), 1.7 / step) * hint
	wide = blur(pressed, 7.0 / step)
	near = blur(pressed, 2.5 / step)
	ridge = 2.4 * wide * (1.0 - near) * numpy.clip(0.8 + 0.4 * cloud(rng, 2.0, 10.0, 1.3), 0.3, 1.4)
	mound = 0.9 * numpy.exp(-((-y - 86.0) / 9.0) ** 2) * near
	wall = numpy.clip(near * (1.0 - near) * 4.0, 0.0, 1.0)
	height = -depth + ridge + mound + 0.22 * cloud(rng, 15.0, 60.0, 1.0) * wall + 0.09 * cloud(rng, 60.0, 300.0, 0.3) * smooth(0.02, 0.3, wide)
	paint, alpha = blank()
	stain = (0.27 * near + 0.05 * blur(tread, 1.5 / step) * hint) * (0.85 + 0.15 * cloud(rng, 5.0, 40.0, 1.0))
	coat(paint, alpha, tint(108, 88, 62), numpy.clip(stain, 0.0, 0.34))
	weight = smooth(0.02, 0.22, blur(pressed, 8.0 / step))

	return paint, alpha, height, weight, edge


def damp(rng, variant):
	edge = 0.36
	x, y, step = plane(edge)
	flip = 1.0 if variant else -1.0
	sole, tread = boot(rng, step, flip)
	fore = smooth(-10.0, -4.0, -y)
	heel = smooth(-64.0, -70.0, -y)
	press = heel * (0.72 + 0.28 * numpy.exp(-((-y + 112.0) / 26.0) ** 2)) + fore * (0.5 + 0.5 * numpy.exp(-((-y - 46.0) / 34.0) ** 2) + 0.12 * numpy.exp(-((-y - 120.0) / 16.0) ** 2) - 0.12 * smooth(-10.0, 45.0, x * flip) * smooth(40.0, 0.0, -y))
	film = blur(tread * press, 0.55 / step)
	near = smooth(0.02, 0.3, blur(film, 1.5 / step))
	level = film * (0.85 + 0.5 * cloud(rng, 3.0, 14.0, 1.4)) - (0.2, 0.26)[variant] - near * (0.16 * cloud(rng, 14.0, 70.0, 1.1) + 0.07 * cloud(rng, 70.0, 250.0, 0.6))
	wet = smooth(0.0, 0.3, level) * (0.72 + 0.28 * numpy.clip(0.5 + 0.5 * cloud(rng, 10.0, 60.0, 1.0) + film * (1.0 - film) * 3.0, 0.0, 1.0))
	drops, draw = pad()

	for drop in range(int(rng.integers(6, 14))):
		place = (rng.normal(0.0, 30.0), rng.choice([-1.0, 1.0]) * rng.uniform(95.0, 150.0) if rng.uniform() < 0.7 else rng.uniform(-140.0, 140.0))
		size = rng.uniform(0.8, 2.6)
		draw.ellipse([pin(place[0] - size, place[1] - size * rng.uniform(0.8, 1.5), step), pin(place[0] + size, place[1] + size * rng.uniform(0.8, 1.5), step)], fill=int(rng.uniform(120, 255)))

	wet = numpy.clip(wet + blur(taken(drops), 0.4 / step) * 0.8, 0.0, 1.0)
	paint, alpha = blank()
	coat(paint, alpha, tint(16, 17, 19), wet * 0.37)

	return paint, alpha, flat(), flat(), edge


def teardrop(rng, draw, step, x, y, heading, width, aspect, tail, shade, count=13):
	along = numpy.linspace(-1.0, 1.0 + tail, count)
	half = numpy.maximum(numpy.sqrt(numpy.clip(1.0 - along * along, 0.0, 1.0)), 0.34 * numpy.clip(1.0 - (along - 0.2) / (0.8 + tail), 0.0, 1.0) ** 0.8 * (along > 0.2) * (tail > 0.0)) * rng.uniform(0.92, 1.08, count)
	forward = numpy.concatenate([along, along[::-1]]) * width * 0.5 * aspect
	lateral = numpy.concatenate([half, -half[::-1]]) * width * 0.5
	draw.polygon([pin(x + forward[index] * math.cos(heading) - lateral[index] * math.sin(heading), y + forward[index] * math.sin(heading) + lateral[index] * math.cos(heading), step) for index in range(count * 2)], fill=shade)


def spatter(rng, variant):
	edge = 0.5
	x, y, step = plane(edge)
	origin = (rng.uniform(-30.0, 30.0), rng.uniform(80.0, 100.0))
	lean = (0.0, -0.22, 0.12, 0.3)[variant] + rng.normal(0.0, 0.05)
	fan = (0.5, 0.32, 0.72, 0.45)[variant]
	body, draw = pad()
	middle = (origin[0] + 42.0 * math.sin(lean), origin[1] - 42.0 * math.cos(lean))

	for blob in range((11, 8, 14, 6)[variant]):
		place = (middle[0] + rng.normal(0.0, 19.0), middle[1] + rng.normal(0.0, 15.0))
		teardrop(rng, draw, step, place[0], place[1], math.atan2(place[1] - origin[1], place[0] - origin[0]) + rng.normal(0.0, 0.4), rng.uniform(16.0, 40.0), rng.uniform(1.0, 1.5), 0.0, 255)

	for blob in range((80, 50, 110, 40)[variant]):
		place = (middle[0] + rng.normal(0.0, 40.0), middle[1] + rng.normal(0.0, 30.0))
		teardrop(rng, draw, step, place[0], place[1], math.atan2(place[1] - origin[1], place[0] - origin[0]) + rng.normal(0.0, 0.3), min(15.0, 3.2 * rng.uniform() ** -0.6), rng.uniform(1.0, 1.7), 0.0, 255)

	for finger in range(int(rng.integers(5, 10))):
		angle = lean + rng.normal(0.0, fan) - math.pi * 0.5
		reach = rng.uniform(45.0, 95.0)
		teardrop(rng, draw, step, origin[0] + reach * math.cos(angle), origin[1] + reach * math.sin(angle), angle, rng.uniform(5.0, 10.0), rng.uniform(2.5, 5.0), rng.uniform(0.3, 1.0), 255)

	rays = lean + rng.normal(0.0, fan, int(rng.integers(5, 9)))

	for drop in range((120, 95, 180, 75)[variant]):
		angle = (rays[int(rng.integers(len(rays)))] + rng.normal(0.0, 0.05) if rng.uniform() < 0.55 else lean + rng.normal(0.0, fan * 1.2)) - math.pi * 0.5
		reach = 60.0 + 280.0 * rng.uniform() ** 1.3
		place = (origin[0] + reach * math.cos(angle), origin[1] + reach * math.sin(angle))

		if abs(place[0]) > 208.0 or abs(place[1]) > 208.0:
			continue

		width = min(12.0, 1.6 * rng.uniform() ** -0.62) * (1.0 - 0.4 * reach / 340.0)
		aspect = min(5.5, 1.0 + (reach / 130.0) ** 1.3 * rng.uniform(0.5, 1.3))
		heading = angle + rng.normal(0.0, 0.06)
		tail = rng.uniform(0.3, 1.0) * min(1.0, aspect - 1.0)
		teardrop(rng, draw, step, place[0], place[1], heading, width, aspect, tail, 255)

		if aspect > 2.0 and rng.uniform() < 0.6:
			ahead = width * 0.5 * aspect * (1.0 + tail) + width * rng.uniform(0.5, 1.6)
			teardrop(rng, draw, step, place[0] + ahead * math.cos(heading), place[1] + ahead * math.sin(heading), heading, width * rng.uniform(0.22, 0.4), rng.uniform(1.0, 1.8), 0.0, 255, 7)

	mist, brush = pad()

	for speck in range((2200, 1500, 3200, 1100)[variant]):
		angle = lean + rng.normal(0.0, fan * 1.5) - math.pi * 0.5
		reach = 25.0 + 300.0 * rng.uniform() ** 2.0
		place = (origin[0] + reach * math.cos(angle), origin[1] + reach * math.sin(angle))

		if abs(place[0]) > 214.0 or abs(place[1]) > 214.0:
			continue

		teardrop(rng, brush, step, place[0], place[1], angle + rng.normal(0.0, 0.15), min(3.4, 0.6 * rng.uniform() ** -0.5), 1.0 + rng.uniform(0.0, 1.0) * min(2.2, reach / 130.0), 0.0, int(rng.uniform(110, 255)), 5)

	body = taken(body)
	body = smooth(0.42, 0.58, haze(body, 1.0 / step, 1.0 / step) + 0.05 * cloud(rng, 20.0, 120.0, 1.0) * (body > 0.0))
	mist = haze(taken(mist), 0.3 / step, 0.3 / step)
	depth = blur(body, 2.2 / step) * body
	pooled = smooth(0.8, 1.0, blur(body, 8.0 / step))
	color = mix(mix(blood_thin, blood_thick, smooth(0.25, 0.8, depth)[:, :, None]), blood_deep, (pooled * (0.7 + 0.3 * cloud(rng, 6.0, 40.0, 1.0)))[:, :, None].clip(0.0, 1.0))
	paint, alpha = blank()
	coat(paint, alpha, blood_thin, numpy.clip(mist * 0.78, 0.0, 0.85))
	coat(paint, alpha, color, body * (0.84 + 0.11 * smooth(0.2, 0.7, depth)))

	return paint, alpha, flat(), flat(), edge


def drips(rng, variant):
	edge = 0.2
	x, y, step = plane(edge)
	paint, alpha = blank()
	course = rng.uniform(0.0, turn)
	sizes = ((6.6, 4.3, 2.4, 1.7), (5.4, 6.9, 3.1, 1.9, 1.5))[variant]
	spots = []
	ring = numpy.arange(2048) * turn / 2048

	for size in sizes:
		for attempt in range(40):
			along = rng.uniform(-45.0, 45.0)
			aside = rng.normal(0.0, 12.0)
			place = (along * math.cos(course) - aside * math.sin(course), along * math.sin(course) + aside * math.cos(course))

			if abs(place[0]) < 50.0 and abs(place[1]) < 50.0 and all(math.hypot(place[0] - other[0], place[1] - other[1]) > (size + other[2]) * 2.3 + 6.0 for other in spots):
				break

		spots.append((place[0], place[1], size))

	mass = sum(size * size for spot_x, spot_y, size in spots)
	middle = (sum(spot_x * size * size for spot_x, spot_y, size in spots) / mass, sum(spot_y * size * size for spot_x, spot_y, size in spots) / mass)

	for spot_x, spot_y, size in spots:
		place = (spot_x - middle[0], spot_y - middle[1])
		area = patch(place[0], place[1], size * 2.0 + 2.0, step)
		across = x[area] - real(place[0])
		along = y[area] - real(place[1])
		spin = numpy.arctan2(along, across)
		far = numpy.sqrt(across * across + along * along)
		lobes = rng.uniform(9.0, 13.0) + size * 1.2
		front = 0.5 + 0.5 * numpy.cos(ring - course)
		curve = 1.0 + 0.06 * numpy.cos(2.0 * (ring - course)) + rng.uniform(0.05, 0.1) * numpy.clip(loop(rng, lobes * 0.6, lobes * 1.4, 0.3), 0.0, None) ** 1.3 * (0.5 + front) + 0.02 * loop(rng, 2.0, 6.0, 1.0)

		for spine in range(int(rng.integers(1, 6))):
			where = course + rng.normal(0.0, 1.3)
			curve += rng.uniform(0.18, 0.5) * numpy.exp(-(((ring - where + math.pi) % turn - math.pi) / rng.uniform(0.035, 0.07)) ** 2)

		level = far / (size * around(curve.astype(real), spin))
		cover = smooth(1.0 + 0.6 * step / size, 1.0 - 0.6 * step / size, level)
		coat(paint[area], alpha[area], mix(mix(blood_thick, blood_deep, smooth(0.7, 0.0, level)[:, :, None] * 0.6), blood_thin, smooth(0.72, 1.0, level)[:, :, None] * 0.75), cover * 0.95)

		for speck in range(int(rng.integers(7, 20))):
			angle = course + rng.normal(0.0, 1.5)
			away = size * rng.uniform(1.25, 2.6)
			dot = rng.uniform(0.15, 0.55)
			spot = patch(place[0] + away * math.cos(angle), place[1] + away * math.sin(angle), dot * 3.0 + 1.0, step)
			major = (x[spot] - real(place[0] + away * math.cos(angle))) * real(math.cos(angle)) + (y[spot] - real(place[1] + away * math.sin(angle))) * real(math.sin(angle))
			minor = (y[spot] - real(place[1] + away * math.sin(angle))) * real(math.cos(angle)) - (x[spot] - real(place[0] + away * math.cos(angle))) * real(math.sin(angle))
			coat(paint[spot], alpha[spot], blood_thin, smooth(1.2, 0.8, numpy.sqrt((major / (dot * rng.uniform(1.0, 2.2))) ** 2 + (minor / dot) ** 2)) * 0.88)

	return paint, alpha, flat(), flat(), edge


def pool(rng, variant):
	edge = 1.0
	x, y, step = plane(edge)
	u = x + cloud(rng, 1.5, 5.0, 1.6) * 26.0
	v = y + cloud(rng, 1.5, 5.0, 1.6) * 26.0
	lead = rng.uniform(0.0, turn)
	major = u * real(math.cos(lead)) + v * real(math.sin(lead))
	minor = v * real(math.cos(lead)) - u * real(math.sin(lead))
	spin = numpy.arctan2(minor, major)
	reach = (225.0, 255.0)[variant]
	ring = 1.0 + 0.2 * loop(rng, 1.5, 4.0, 1.0) + 0.06 * loop(rng, 4.0, 9.0, 1.0)
	level = numpy.sqrt((major / rng.uniform(1.1, 1.3)) ** 2 + minor * minor) / (reach * around(ring, spin))
	runs, draw = pad()

	for runnel in range((2, 1)[variant]):
		angle = rng.uniform(0.0, turn)
		start = reach * 0.7
		place = (start * math.cos(angle + lead), start * math.sin(angle + lead))
		width = rng.uniform(44.0, 70.0)
		heading = angle + lead + rng.normal(0.0, 0.3)

		for piece in range(int(rng.uniform(6.0, 12.0))):
			heading += rng.normal(0.0, 0.09)
			ahead = (place[0] + 12.0 * math.cos(heading), place[1] + 12.0 * math.sin(heading))

			if max(abs(ahead[0]), abs(ahead[1])) > 395.0:
				break

			draw.line([pin(place[0], place[1], step), pin(ahead[0], ahead[1], step)], fill=255, width=int(width / step))
			draw.ellipse([pin(ahead[0] - width * 0.5, ahead[1] - width * 0.5, step), pin(ahead[0] + width * 0.5, ahead[1] + width * 0.5, step)], fill=255)
			place = ahead
			width = max(24.0, width * rng.uniform(0.9, 0.99))

		draw.ellipse([pin(place[0] - width * 0.7, place[1] - width * 0.7, step), pin(place[0] + width * 0.7, place[1] + width * 0.7, step)], fill=255)

	for puddle in range(int(rng.integers(2, 6))):
		angle = rng.uniform(0.0, turn)
		away = reach * rng.uniform(1.25, 1.55)
		size = rng.uniform(5.0, 20.0)

		if max(abs(away * math.cos(angle)), abs(away * math.sin(angle))) < 395.0:
			draw.ellipse([pin(away * math.cos(angle) - size, away * math.sin(angle) - size * rng.uniform(0.7, 1.0), step), pin(away * math.cos(angle) + size, away * math.sin(angle) + size * rng.uniform(0.7, 1.0), step)], fill=255)

	body = smooth(0.45, 0.55, blur(numpy.maximum(smooth(1.02, 0.98, level), taken(runs)), 7.0 / step))
	index = numpy.arange(side) - (side - 1) * 0.5
	shift = (int(round((body.sum(axis=1) * index).sum() / body.sum())), int(round((body.sum(axis=0) * index).sum() / body.sum())))
	body = numpy.roll(body, (-shift[0], -shift[1]), axis=(0, 1))
	level = numpy.roll(level, (-shift[0], -shift[1]), axis=(0, 1))
	inner = blur(body, 5.0 / step)
	thick = blur(body, 7.0 / step)
	height = 2.2 * smooth(0.5, 0.97, inner) ** 0.7
	centre = smooth(0.6, 1.0, blur(body, 40.0 / step)) * numpy.clip(1.1 - level * 0.45, 0.0, 1.0)
	color = mix(mix(blood_thin, blood_thick, smooth(0.5, 0.9, thick)[:, :, None]), blood_deep, (centre * (0.85 + 0.15 * cloud(rng, 3.0, 20.0, 1.2)))[:, :, None].clip(0.0, 1.0))
	paint, alpha = blank()
	coat(paint, alpha, color, body * (0.8 + 0.15 * smooth(0.5, 0.92, thick)))

	return paint, alpha, height, body, edge


def glass(rng, variant):
	edge = 0.24
	x, y, step = plane(edge)
	far = numpy.sqrt(x * x + y * y)
	spin = numpy.arctan2(y, x)
	bore = (3.4, 4.2)[variant]
	count = (12, 17)[variant]
	lead = rng.uniform(0.0, turn)
	angles = numpy.sort((numpy.arange(count) + rng.uniform(-0.4, 0.4, count)) * turn / count + rng.uniform(0.0, turn))
	lengths = (20.0 + 85.0 * rng.uniform(0.0, 1.0, count) ** 2.2) * (1.0 + (0.0, 0.45)[variant] * numpy.cos(angles - lead))
	lengths = numpy.minimum(lengths, 102.0 / numpy.maximum(numpy.abs(numpy.cos(angles)), numpy.abs(numpy.sin(angles))))
	rings = numpy.array([8.0, 15.0, 25.0, 38.0, 55.0, 76.0]) * rng.uniform(0.9, 1.15)
	radius = rings[None, :] * rng.uniform(0.84, 1.18, (count, len(rings)))
	bend = angles[:, None] + numpy.cumsum(rng.normal(0.0, 0.018, (count, len(rings))), axis=1)
	lines, draw = pad()
	frost, brush = pad()

	for index in range(count):
		reach = [bore * 0.8] + [radius[index, ring] for ring in range(len(rings)) if radius[index, ring] < lengths[index]] + [lengths[index]]
		turnings = [angles[index]] + [bend[index, ring] for ring in range(len(rings)) if radius[index, ring] < lengths[index]]
		turnings.append(turnings[-1] + rng.normal(0.0, 0.02))

		for piece in range(len(reach) - 1):
			draw.line([pin(reach[piece] * math.cos(turnings[piece]), reach[piece] * math.sin(turnings[piece]), step), pin(reach[piece + 1] * math.cos(turnings[piece + 1]), reach[piece + 1] * math.sin(turnings[piece + 1]), step)], fill=int(255 * (1.0 - 0.55 * reach[piece] / lengths[index])), width=2 if reach[piece] < 14.0 else 1)

		other = (index + 1) % count

		for ring in range(len(rings)):
			if radius[index, ring] < lengths[index] and radius[other, ring] < lengths[other] and rng.uniform() < (0.95, 0.8, 0.55, 0.35, 0.2, 0.1)[ring]:
				draw.line([pin(radius[index, ring] * math.cos(bend[index, ring]), radius[index, ring] * math.sin(bend[index, ring]), step), pin(radius[other, ring] * math.cos(bend[other, ring]), radius[other, ring] * math.sin(bend[other, ring]), step)], fill=int(rng.uniform(150, 255)), width=1)

		if rng.uniform() < 0.5:
			brush.polygon([pin(bore * 0.9 * math.cos(bend[index, 0]), bore * 0.9 * math.sin(bend[index, 0]), step), pin(radius[index, 0] * math.cos(bend[index, 0]), radius[index, 0] * math.sin(bend[index, 0]), step), pin(radius[other, 0] * math.cos(bend[other, 0]), radius[other, 0] * math.sin(bend[other, 0]), step), pin(bore * 0.9 * math.cos(bend[other, 0]), bore * 0.9 * math.sin(bend[other, 0]), step)], fill=int(rng.uniform(60, 140)))

		for chip in range(int(rng.integers(0, 4))):
			away = rng.uniform(bore * 1.5, lengths[index] * 0.8)
			flake(rng, draw, step, away * math.cos(angles[index]), away * math.sin(angles[index]), rng.uniform(0.3, 0.8), int(rng.uniform(120, 230)))

	lines = taken(lines)
	grit = cloud(rng, 80.0, 300.0, 0.3)
	cone = smooth(1.0, 0.85, far / (bore * (2.0 + 0.5 * around(loop(rng, 3.0, 12.0, 0.8), spin))))
	crush = numpy.clip(cone * (0.6 + 0.4 * grit) + taken(frost) * (0.6 + 0.4 * grit), 0.0, 1.0)
	hole = smooth(1.02, 0.94, far / (bore * (1.0 + 0.16 * around(loop(rng, 2.0, 9.0, 0.8), spin))))
	paint, alpha = blank()
	coat(paint, alpha, tint(232, 238, 240), numpy.clip(crush * 0.8, 0.0, 0.85))
	coat(paint, alpha, tint(228, 236, 238), numpy.clip(lines * 0.9, 0.0, 1.0))
	coat(paint, alpha, tint(14, 16, 18), hole * 0.92)
	height = -0.3 * blur(lines, 0.25 / step) + 0.22 * grit * crush - 1.4 * smooth(bore * 2.2, bore * 0.9, far) * (0.8 + 0.2 * grit)
	weight = numpy.maximum(numpy.clip(blur(lines, 0.3 / step) * 1.4, 0.0, 0.6), numpy.maximum(crush * 0.9, smooth(bore * 2.4, bore * 1.8, far)))

	return paint, alpha, height, weight, edge


def fabric(rng, variant):
	edge = 0.08
	x, y, step = plane(edge)
	far = numpy.sqrt(x * x + y * y)
	spin = numpy.arctan2(y, x)
	bore = (2.6, 3.2)[variant]
	weave = rng.uniform(-0.2, 0.2)
	ring = numpy.arange(2048) * turn / 2048
	curve = 1.0 + 0.16 * loop(rng, 2.0, 6.0, 1.0) + 0.08 * loop(rng, 6.0, 22.0, 0.8)

	for axis in range(4):
		curve += rng.uniform(0.1, 0.65) * numpy.exp(-(((ring - weave - axis * math.pi * 0.5 + math.pi) % turn - math.pi) / rng.uniform(0.07, 0.16)) ** 2)

	curve = (curve * bore).astype(real)
	gap = far - around(curve, spin)
	hole = smooth(0.0, -0.12, gap)
	yarn, draw = pad()
	fuzz, brush = pad()

	for thread in range(int(rng.integers(18, 30))):
		angle = rng.uniform(0.0, turn)
		start = float(around(curve, numpy.array(angle))) * rng.uniform(0.95, 1.2)
		place = (start * math.cos(angle), start * math.sin(angle))
		axis = weave + round((angle + math.pi - weave) / (math.pi * 0.5)) * math.pi * 0.5 + rng.normal(0.0, 0.3)
		heading = axis if rng.uniform() < 0.75 else axis + math.pi
		width = rng.uniform(0.22, 0.42)

		for piece in range(int(rng.uniform(4.0, 12.0))):
			heading += rng.normal(0.0, 0.18)
			ahead = (place[0] + 0.28 * math.cos(heading), place[1] + 0.28 * math.sin(heading))
			draw.line([pin(place[0], place[1], step), pin(ahead[0], ahead[1], step)], fill=255, width=max(1, int(round(width / step))))
			place = ahead
			width *= 0.93

	for hair in range(int(rng.integers(60, 100))):
		angle = rng.uniform(0.0, turn)
		start = float(around(curve, numpy.array(angle))) * rng.uniform(0.8, 1.35)
		place = (start * math.cos(angle), start * math.sin(angle))
		heading = rng.uniform(0.0, turn)

		for piece in range(int(rng.uniform(3.0, 10.0))):
			heading += rng.normal(0.0, 0.35)
			ahead = (place[0] + 0.22 * math.cos(heading), place[1] + 0.22 * math.sin(heading))
			brush.line([pin(place[0], place[1], step), pin(ahead[0], ahead[1], step)], fill=int(rng.uniform(90, 200)), width=1)
			place = ahead

	yarn = taken(yarn)
	fuzz = taken(fuzz)
	pulls = flat()

	for run in range(int(rng.integers(1, 4))):
		axis = weave + int(rng.integers(4)) * math.pi * 0.5
		shift = rng.uniform(-0.8, 0.8) * bore
		along = x * real(math.cos(axis)) + y * real(math.sin(axis))
		aside = y * real(math.cos(axis)) - x * real(math.sin(axis)) - real(shift) - 0.08 * cloud(rng, 4.0, 30.0, 1.2)
		pulls += numpy.exp(-(aside / 0.16) ** 2) * smooth(bore * 0.7, bore * 1.1, along) * smooth(rng.uniform(8.0, 18.0), bore * 1.5, along)

	outside = numpy.clip(gap, 0.0, None)
	wrinkle = spokes(rng, x, y, 14.0, 5.0, 28.0, 1.0, 3.0)
	singe = numpy.exp(-outside / rng.uniform(0.9, 1.4)) * numpy.clip(0.65 + 0.45 * cloud(rng, 6.0, 50.0, 1.1), 0.0, 1.2) * (1.0 - hole)
	height = 0.4 * numpy.exp(-(outside / 1.3) ** 2) * (1.0 + 0.4 * wrinkle) * (1.0 - hole) + 0.1 * wrinkle * numpy.exp(-outside / 3.5) + 0.12 * pulls - 1.6 * blur(hole, 0.3 / step) + 0.16 * blur(yarn, 0.12 / step) + 0.06 * blur(fuzz, 0.1 / step)
	paint, alpha = blank()
	coat(paint, alpha, tint(60, 42, 28), numpy.clip(singe * 0.38, 0.0, 0.5))
	coat(paint, alpha, tint(28, 22, 18), numpy.clip(singe ** 3.0 * 0.45, 0.0, 0.6))
	coat(paint, alpha, tint(196, 188, 174), pulls * 0.1)
	coat(paint, alpha, tint(15, 13, 13), hole * 0.96)
	coat(paint, alpha, tint(150, 140, 126), numpy.clip(fuzz * 0.55, 0.0, 1.0))
	coat(paint, alpha, mix(tint(178, 168, 152), tint(70, 50, 34), (0.6 * smooth(1.2, 0.0, outside) * (1.0 - hole))[:, :, None]) * (1.0 - 0.45 * hole)[:, :, None], numpy.clip(yarn * 0.85, 0.0, 1.0))
	weight = numpy.clip(numpy.maximum(numpy.exp(-(outside / 2.6) ** 2), 0.4 * pulls), 0.0, 1.0)

	return paint, alpha, height, weight, edge


def scorch(rng, variant):
	edge = 0.8
	x, y, step = plane(edge)
	u = x + cloud(rng, 1.5, 5.0, 1.5) * 9.0
	v = y + cloud(rng, 1.5, 5.0, 1.5) * 9.0
	lead = rng.uniform(0.0, turn)
	major = u * real(math.cos(lead)) + v * real(math.sin(lead))
	minor = v * real(math.cos(lead)) - u * real(math.sin(lead))
	far = numpy.sqrt((major / rng.uniform(1.05, 1.25)) ** 2 + minor * minor)
	spin = numpy.arctan2(minor, major)
	jets = around(loop(rng, 10.0, 70.0, 0.5), spin)
	reach = far / ((132.0, 146.0)[variant] * numpy.exp(0.16 * jets + 0.1 * around(loop(rng, 1.0, 4.0, 1.0), spin)))
	streak = spokes(rng, major, minor, 380.0, 14.0, 110.0, 0.6, 9.0)
	mottle = cloud(rng, 6.0, 40.0, 1.1)
	core = numpy.exp(-reach ** 3.0)
	veil = numpy.exp(-(reach / 1.6) ** 2) * numpy.clip(0.5 + 0.45 * streak + 0.3 * jets, 0.0, 1.5) * smooth(0.45, 1.0, reach)
	soot = numpy.clip(0.94 * (1.0 - numpy.exp(-3.4 * core * (0.95 + 0.1 * mottle))) + 0.42 * veil * (1.0 - core), 0.0, 0.95)
	ash = smooth(1.0, 1.8, cloud(rng, 6.0, 34.0, 1.1)) * smooth(0.75, 0.25, reach)
	scoured = smooth(0.32, 0.0, reach) * (0.25, 0.4)[variant] * numpy.clip(0.6 + 0.5 * mottle, 0.0, 1.0)
	color = mix(mix(tint(70, 56, 44), tint(18, 16, 15), smooth(0.1, 0.6, soot)[:, :, None]), tint(100, 97, 93), numpy.clip(0.35 * ash + scoured, 0.0, 0.7)[:, :, None])
	paint, alpha = blank()
	coat(paint, alpha, color, soot)
	crust = smooth(1.05, 0.35, reach)
	height = (0.25 * cloud(rng, 10.0, 60.0, 1.2) + 0.3 * ash) * crust
	weight = 0.4 * crust

	return paint, alpha, height, weight, edge


def gash(rng, x, y, step, middle, angle, length, width, deep, parts):
	depth, torn, keel_line, chips = parts
	along = (x - real(middle[0])) * real(math.cos(angle)) + (y - real(middle[1])) * real(math.sin(angle))
	across = (y - real(middle[1])) * real(math.cos(angle)) - (x - real(middle[0])) * real(math.sin(angle))
	offset = rng.uniform(-0.15, 0.15) * length
	half = width * 0.5 * numpy.clip(1.0 - ((along - offset) / (length * 0.5 + numpy.sign(along - offset) * offset)) ** 2, 0.0, 1.0) ** 0.75
	middle_line = 0.18 * cloud(rng, 4.0, 40.0, 1.2) + rng.uniform(-0.01, 0.01) * along
	skew = rng.choice([-1.0, 1.0]) * rng.uniform(0.2, 0.42)
	keel = middle_line + skew * half
	span = numpy.where(across < keel, keel - (middle_line - half), (middle_line + half) - keel)
	inside = smooth(0.0, 1.2 * step, half - numpy.abs(across - middle_line)) * (half > 0.02)
	sink = numpy.clip(1.0 - numpy.abs(across - keel) / numpy.maximum(span, 1e-3), 0.0, 1.0)
	cut_depth = half * deep * sink * inside
	nick = rng.choice([-1.0, 1.0])
	spot = rng.uniform(-0.3, 0.3) * length
	reach = rng.uniform(0.1, 0.18) * length
	shelf = rng.uniform(2.2, 4.0) * numpy.clip(1.0 - numpy.abs(along - spot) / reach, 0.0, 1.0) ** 0.8
	beside = (across - middle_line) * nick - half
	chip = smooth(0.0, 1.2 * step, shelf - beside) * (beside > -0.3) * (shelf > 0.05) * (1.0 - inside)
	cut_depth = cut_depth + chip * rng.uniform(0.8, 1.3) * (1.0 - 0.5 * beside / numpy.maximum(shelf, 0.05))
	numpy.maximum(depth, cut_depth, out=depth)
	numpy.maximum(torn, numpy.clip(inside + chip, 0.0, 1.0), out=torn)
	numpy.maximum(keel_line, smooth(0.45, 0.0, numpy.abs(across - keel)) * inside, out=keel_line)
	numpy.maximum(chips, sink ** 2.0 * inside, out=chips)

	return [(middle[0] + math.cos(angle) * (length * 0.5 + offset * tip) * tip, middle[1] + math.sin(angle) * (length * 0.5 + offset * tip) * tip) for tip in (-1.0, 1.0)]


def cut(rng, variant):
	edge = 0.24
	x, y, step = plane(edge)
	depth = flat()
	torn = flat()
	keel = flat()
	shade = flat()
	parts = (depth, torn, keel, shade)
	ends = []

	if variant == 0:
		tilt = rng.uniform(-0.35, -0.2)

		for chop in range(3):
			shift = (chop - 1) * rng.uniform(19.0, 24.0)
			ends += gash(rng, x, y, step, (-math.sin(tilt) * shift + rng.normal(0.0, 4.0), math.cos(tilt) * shift), tilt + rng.normal(0.0, 0.05), rng.uniform(72.0, 98.0), rng.uniform(6.5, 9.0), 1.8, parts)
	else:
		ends += gash(rng, x, y, step, (rng.normal(0.0, 4.0), rng.normal(0.0, 4.0)), math.pi * 0.5 + rng.uniform(0.55, 0.75), rng.uniform(92.0, 108.0), rng.uniform(5.5, 7.0), 1.9, parts)
		ends += gash(rng, x, y, step, (rng.normal(0.0, 4.0), rng.normal(0.0, 4.0)), math.pi * 0.5 - rng.uniform(0.6, 0.8), rng.uniform(86.0, 104.0), rng.uniform(5.0, 6.5), 1.9, parts)
		ends += gash(rng, x, y, step, (rng.uniform(18.0, 26.0), rng.uniform(-30.0, -20.0)), rng.uniform(-0.3, 0.3), rng.uniform(26.0, 38.0), rng.uniform(3.5, 4.5), 1.7, parts)

	strips, draw = pad()
	split, brush = pad()

	for end in ends:
		for tip in (-1.0, 1.0):
			if rng.uniform() < 0.55:
				place = end[0] + rng.normal(0.0, 0.8)
				start = end[1] - tip * rng.uniform(0.5, 4.0)
				draw.line([pin(place, start, step), pin(place + rng.normal(0.0, 0.2), start + tip * rng.uniform(3.0, 10.0), step)], fill=int(rng.uniform(140, 255)), width=int(rng.integers(1, 3)))

		if rng.uniform() < 0.7:
			tip = rng.choice([-1.0, 1.0])
			place = end[0]
			reach = end[1]

			for piece in range(int(rng.uniform(6.0, 18.0))):
				shift = place + rng.normal(0.0, 0.06)
				brush.line([pin(place, reach, step), pin(shift, reach + tip * 1.2, step)], fill=int(255 * (1.0 - 0.045 * piece)), width=1)
				place = shift
				reach += tip * 1.2

	strips = taken(strips) * (1.0 - torn)
	split = taken(split) * (1.0 - torn) * (1.0 - strips)
	fibre = cloud(rng, 40.0, 300.0, 0.4, 1.0, 22.0)
	band = cloud(rng, 8.0, 40.0, 1.2, 1.0, 30.0)
	depth += 0.5 * strips + 0.3 * blur(split, 0.2 / step) - 0.05 * fibre * numpy.clip(torn + strips, 0.0, 1.0)
	cover = numpy.clip(torn + strips, 0.0, 1.0)
	color = mix(tint(216, 186, 134), tint(178, 130, 78), (0.75 * smooth(0.4, 1.3, band))[:, :, None]) * ((1.0 + 0.06 * fibre) * (1.0 - 0.4 * shade))[:, :, None]
	color = mix(color, tint(62, 42, 27), (keel * 0.8)[:, :, None])
	paint, alpha = blank()
	coat(paint, alpha, tint(46, 33, 23), numpy.clip(split * 0.8, 0.0, 1.0))
	coat(paint, alpha, numpy.clip(color, 0.0, 1.0), cover)
	weight = numpy.maximum(smooth(0.0, 0.5, blur(cover, 0.4 / step)), split * 0.55)

	return paint, alpha, -depth, weight, edge


def frame():
	reach = (numpy.minimum(numpy.arange(side), side - 1 - numpy.arange(side)) + 0.5) / over
	fade = smooth(guard, guard + ramp, reach).astype(real)

	return fade[:, None] * fade[None, :]


def bleed(color, alpha):
	result = color.copy()
	known = alpha > 0.004
	mass = numpy.where(known, alpha, 0.0).astype(real)

	if not known.any():
		return numpy.zeros_like(color)

	for sigma in (1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0):
		spread = haze(mass, sigma, sigma)
		take = ~known & (spread > 1e-4)

		for channel in range(3):
			result[:, :, channel] = numpy.where(take, haze(color[:, :, channel] * mass, sigma, sigma) / numpy.maximum(spread, 1e-6), result[:, :, channel])

		known = known | take

	return numpy.where(known[:, :, None], result, (color * mass[:, :, None]).sum(axis=(0, 1)) / mass.sum())


def finish(paint, alpha, height, weight, edge):
	fade = frame()
	color = linear(paint / numpy.maximum(alpha, 1e-6)[:, :, None])
	alpha = numpy.clip(alpha, 0.0, 1.0) * fade
	weight = numpy.clip(weight, 0.0, 1.0) * fade
	along, across = numpy.gradient(height * fade * real(0.001), edge / side)
	limit = numpy.minimum(1.0, steep / numpy.maximum(numpy.sqrt(across * across + along * along), 1e-6))
	across *= limit
	along *= limit
	scale = 1.0 / numpy.sqrt(1.0 + across * across + along * along)
	normal = numpy.stack([shrink(-across * scale, over), shrink(-along * scale, over), shrink(scale, over)], axis=2)
	normal /= numpy.linalg.norm(normal, axis=2)[:, :, None]
	small = shrink(alpha, over)
	heavy = shrink(weight, over)
	color = numpy.stack([shrink(color[:, :, channel] * alpha, over) for channel in range(3)], axis=2) / numpy.maximum(small, 1e-6)[:, :, None]
	color = bleed(numpy.clip(encoded(color), 0.0, 1.0), small)
	normal[:, :, :2] *= smooth(0.0, 0.03, heavy)[:, :, None]
	surface = numpy.zeros((cell, cell, 4), dtype=numpy.uint8)
	surface[:, :, :3] = numpy.clip(numpy.round(color * 255.0), 0, 255).astype(numpy.uint8)
	surface[:, :, 3] = numpy.clip(numpy.round(small * 255.0), 0, 255).astype(numpy.uint8)
	shape = numpy.zeros((cell, cell, 4), dtype=numpy.uint8)
	shape[:, :, 0] = numpy.clip(numpy.floor(normal[:, :, 0] * 127.5 + 128.0), 0, 255).astype(numpy.uint8)
	shape[:, :, 1] = numpy.clip(numpy.floor(normal[:, :, 1] * 127.5 + 128.0), 0, 255).astype(numpy.uint8)
	shape[:, :, 2] = numpy.clip(numpy.round(heavy * 255.0), 0, 255).astype(numpy.uint8)
	shape[:, :, 3] = 255

	return surface, shape


plan = {
	0: (concrete, 0, "concrete"),
	1: (concrete, 1, "concrete"),
	2: (concrete, 2, "concrete"),
	3: (concrete, 3, "concrete"),
	4: (metal, 0, "paint"),
	5: (metal, 1, "paint"),
	6: (metal, 2, "paint"),
	7: (metal, 3, "paint"),
	8: (timber, 0, "wood"),
	9: (timber, 1, "wood"),
	10: (timber, 2, "wood"),
	11: (timber, 3, "wood"),
	12: (earth, 0, "earth"),
	13: (earth, 1, "earth"),
	14: (sand, 0, "sand"),
	15: (sand, 1, "sand"),
	16: (mud, 0, "mud"),
	17: (mud, 1, "mud"),
	18: (dune, 0, "sand"),
	19: (dune, 1, "sand"),
	20: (damp, 0, "floor"),
	21: (damp, 1, "floor"),
	24: (spatter, 0, "floor"),
	25: (spatter, 1, "floor"),
	26: (spatter, 2, "floor"),
	27: (spatter, 3, "floor"),
	28: (drips, 0, "floor"),
	29: (drips, 1, "floor"),
	30: (pool, 0, "floor"),
	31: (pool, 1, "floor"),
	32: (glass, 0, "glass"),
	33: (glass, 1, "glass"),
	34: (fabric, 0, "cloth"),
	35: (fabric, 1, "cloth"),
	36: (scorch, 0, "concrete"),
	37: (scorch, 1, "concrete"),
	38: (cut, 0, "wood"),
	39: (cut, 1, "wood"),
}

grounds = {
	"concrete": tint(122, 117, 108),
	"paint": tint(52, 80, 94),
	"wood": tint(116, 98, 74),
	"earth": tint(98, 84, 62),
	"sand": tint(152, 122, 88),
	"mud": tint(92, 76, 56),
	"floor": tint(132, 124, 112),
	"glass": tint(46, 60, 64),
	"cloth": tint(86, 90, 72),
}

groups = [
	("lit_00_concrete", [0, 1, 2, 3]),
	("lit_04_metal", [4, 5, 6, 7]),
	("lit_08_wood", [8, 9, 10, 11]),
	("lit_12_earth_sand", [12, 13, 14, 15]),
	("lit_16_prints", [16, 17, 18, 19, 20, 21]),
	("lit_24_spatter", [24, 25, 26, 27]),
	("lit_28_drips_pools", [28, 29, 30, 31]),
	("lit_32_glass_fabric", [32, 33, 34, 35]),
	("lit_36_scorch_cuts", [36, 37, 38, 39]),
]


def build(index):
	maker, variant, ground = plan[index]

	return finish(*maker(numpy.random.default_rng(7000 + index * 131), variant))


def lit(surface, shape, ground, light):
	alpha = surface[:, :, 3:].astype(real) / 255.0
	albedo = mix(linear(ground)[None, None, :], linear(surface[:, :, :3].astype(real) / 255.0), alpha)
	weight = shape[:, :, 2].astype(real) / 255.0
	across = (shape[:, :, 0].astype(real) - 128.0) / 127.5 * weight
	along = (shape[:, :, 1].astype(real) - 128.0) / 127.5 * weight
	upward = numpy.sqrt(numpy.clip(1.0 - across * across - along * along, 0.0, 1.0))
	shine = numpy.clip(across * light[0] + along * light[1] + upward * light[2], 0.0, None) / light[2]

	return numpy.clip(numpy.round(encoded(numpy.clip(albedo * (0.3 + 0.7 * shine)[:, :, None], 0.0, 1.0)) * 255.0), 0, 255).astype(numpy.uint8)


def sheet(name, indices, tiles):
	lights = [(-math.cos(math.radians(30.0)) * math.sqrt(0.5), -math.cos(math.radians(30.0)) * math.sqrt(0.5), math.sin(math.radians(30.0))), (math.cos(math.radians(30.0)) * math.sqrt(0.5), math.cos(math.radians(30.0)) * math.sqrt(0.5), math.sin(math.radians(30.0)))]
	rows = [numpy.concatenate([lit(tiles[index][0], tiles[index][1], grounds[plan[index][2]], light) for index in indices], axis=1) for light in lights]
	image = Image.fromarray(numpy.concatenate(rows, axis=0)).resize((len(indices) * cell * 2, cell * 4), Image.BILINEAR)
	draw = ImageDraw.Draw(image)

	for column, index in enumerate(indices):
		draw.text((column * cell * 2 + 6, 4), str(index), fill=(255, 255, 255))

	image.save(os.path.join(sheets, name + ".png"))


def check(surface, shape):
	band = numpy.ones((cell, cell), dtype=bool)
	band[10:-10, 10:-10] = False

	for index in range(grid * grid):
		area = (slice(index // grid * cell, index // grid * cell + cell), slice(index % grid * cell, index % grid * cell + cell))
		color = surface[area]
		relief = shape[area]
		edge = color[band][:, 3].any() or relief[band][:, 2].any() or (relief[band][:, :2] != 128).any() or (relief[:, :, 3] != 255).any()
		empty = index not in plan and (color.any() or relief[:, :, 2].any() or (relief[:, :, :2] != 128).any())

		if edge or empty:
			raise SystemExit("cell %d breaks the layout contract" % index)


def main():
	os.makedirs(output, exist_ok=True)
	os.makedirs(sheets, exist_ok=True)
	order = sorted(plan)

	with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, min(6, (os.cpu_count() or 2) - 1))) as workers:
		tiles = dict(zip(order, workers.map(build, order)))

	surface = numpy.zeros((grid * cell, grid * cell, 4), dtype=numpy.uint8)
	shape = numpy.zeros((grid * cell, grid * cell, 4), dtype=numpy.uint8)
	shape[:, :, 0] = 128
	shape[:, :, 1] = 128
	shape[:, :, 3] = 255

	for index in order:
		area = (slice(index // grid * cell, index // grid * cell + cell), slice(index % grid * cell, index % grid * cell + cell))
		surface[area] = tiles[index][0]
		shape[area] = tiles[index][1]

	check(surface, shape)
	Image.fromarray(surface).save(os.path.join(output, "marks_color.png"))
	Image.fromarray(shape).save(os.path.join(output, "marks_shape.png"))

	for name, indices in groups:
		sheet(name, indices, tiles)

	rows = (max(order) // grid + 1) * cell
	across = (shape[:rows, :, 0].astype(real) - 128.0) / 127.5
	along = (shape[:rows, :, 1].astype(real) - 128.0) / 127.5
	normal = numpy.stack([shape[:rows, :, 0], shape[:rows, :, 1], numpy.clip(numpy.round(numpy.sqrt(numpy.clip(1.0 - across * across - along * along, 0.0, 1.0)) * 127.5 + 127.5), 0, 255).astype(numpy.uint8)], axis=2)
	upper = numpy.concatenate([surface[:rows, :, :3], numpy.repeat(surface[:rows, :, 3:], 3, axis=2)], axis=1)
	lower = numpy.concatenate([normal, numpy.repeat(shape[:rows, :, 2:3], 3, axis=2)], axis=1)
	Image.fromarray(numpy.concatenate([upper, lower], axis=0)).save(os.path.join(sheets, "raw.png"))

	for index in order:
		color = tiles[index][0].astype(numpy.float64)
		mean = (color[:, :, :3] * color[:, :, 3:]).sum(axis=(0, 1)) / max(color[:, :, 3].sum(), 1.0)
		print("%2d  rgb %3d %3d %3d  alpha %.3f" % (index, round(mean[0]), round(mean[1]), round(mean[2]), color[:, :, 3].mean() / 255.0))


if __name__ == "__main__":
	main()
