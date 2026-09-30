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
		round_ = numpy.sqrt(major * major + minor * minor)
		body = smooth(1.0, 0.8, round_)
		kind = rng.uniform()
		lift = size * rng.uniform(0.6, 1.0) * (0.34 if kind < 0.5 else (-0.24 if kind < 0.75 else 0.0))
		color = palette[int(rng.integers(len(palette)))] * rng.uniform(0.85, 1.12)
		strength = rng.uniform(0.35, 0.85)
		bump[area] += real(lift) * numpy.clip(1.0 - round_ * round_, 0.0, 1.0) ** 0.75
		stain[area] += color * (body * real(strength) * (1.0 - 0.18 * smooth(0.55, 1.0, round_)))[:, :, None]
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

	for flake in range(int(rng.integers(3, 7))):
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
	height = numpy.zeros((side, side), dtype=real)
	height[area] = -depth
	spread = numpy.zeros((side, side), dtype=real)
	spread[area] = cover

	image, draw = pad()
	count = int(rng.integers(4, 8))

	for crack in range(count):
		angle = (crack + rng.uniform(-0.35, 0.35)) * turn / count + toward
		start = rim(angles, reaches, angle) * 0.85
		fissure(rng, draw, step, start * math.cos(angle), start * math.sin(angle), angle, min(66.0 - start, reach * (0.3 + 2.4 * rng.uniform() ** 2.0)), rng.uniform(0.25, 0.5))

	crack = taken(image) * (1.0 - spread)
	height -= blur(crack, 0.32 / step) * 0.9
	chips = numpy.zeros((side, side), dtype=real)

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
	weight = numpy.maximum(smooth(1.18, 0.92, span), numpy.maximum(stripped, split * 0.5))

	return paint, alpha, height, weight, edge


def staves(rng, step, low, high):
	bounds = [0.0]

	while bounds[-1] < side:
		bounds.append(bounds[-1] + rng.uniform(low, high) / step)

	bounds = numpy.array(bounds)
	place = numpy.arange(side) + 0.5
	strand = numpy.clip(numpy.searchsorted(bounds, place) - 1, 0, len(bounds) - 2)
	lateral = ((place - bounds[strand]) / (bounds[strand + 1] - bounds[strand]) * 2.0 - 1.0).astype(real)
	middle = (((bounds[:-1] + bounds[1:]) * 0.5 - side * 0.5) * step)

	return strand, len(bounds) - 1, lateral, middle


def tear(rng, axis, reach, start, strand, count, lateral, middle, splay, longest, deepest):
	length = longest * numpy.clip(1.0 - (middle / splay) ** 2, 0.0, 1.0) ** 0.6 * rng.uniform(0.0, 1.0, count) ** 1.5 * (rng.uniform(0.0, 1.0, count) > 0.15)
	bottom = deepest * rng.uniform(0.35, 1.0, count)
	kind = rng.integers(0, 4, count)
	raised = rng.uniform(0.0, 1.0, count) < 0.14
	run = (reach - start[None, :]) / numpy.maximum(length[strand], 1e-3)[None, :].astype(real)
	tail = numpy.clip((run - 0.55) / 0.45, 0.0, 1.0)
	upper = 1.0 - tail * numpy.array([0.0, 1.0, 2.0, 0.0])[kind][strand][None, :].astype(real)
	lower = -1.0 + tail * numpy.array([0.0, 1.0, 0.0, 2.0])[kind][strand][None, :].astype(real)
	mask = smooth(0.0, 0.03, run) * smooth(1.0, 0.97, run) * smooth(0.0, 0.16, upper - lateral[None, :]) * smooth(0.0, 0.16, lateral[None, :] - lower) * (length[strand] > 0.3)[None, :]
	slope = numpy.clip(1.0 - run, 0.0, 1.0)
	relief = numpy.where(raised[strand][None, :], 1.3 * slope ** 1.2, -slope ** 0.8) * bottom[strand][None, :].astype(real) * mask

	return mask, relief, run * length[strand][None, :].astype(real)


def timber(rng, variant):
	edge = 0.12
	x, y, step = plane(edge)
	axis = x[0]
	far = numpy.sqrt(x * x + y * y)
	bore = (3.4, 3.8, 3.1, 3.6)[variant]
	strand, count, lateral, middle = staves(rng, step, 0.35, 1.1)
	chord = bore * numpy.sqrt(numpy.clip(1.0 - (axis / bore) ** 2, 0.0, 1.0))
	ragged = numpy.clip(1.0 - (axis / bore) ** 2, 0.0, 1.0) ** 0.25
	above = chord + ((rng.uniform(0.0, 1.0, count) ** 2.0 * 1.3 - 0.22) * bore * 0.5)[strand] * ragged
	below = chord + ((rng.uniform(0.0, 1.0, count) ** 2.0 * 1.3 - 0.22) * bore * 0.5)[strand] * ragged
	hole = smooth(0.0, 1.5 * step, above[None, :] + y) * smooth(0.0, 1.5 * step, below[None, :] - y) * (numpy.abs(axis) < bore)[None, :]
	splay = bore * rng.uniform(1.15, 1.45)
	high, rise, climb = tear(rng, axis, -y, numpy.clip(above, 0.0, None), strand, count, lateral, middle, splay, (16.0, 30.0, 8.0, 13.0)[variant], 2.0)
	low, fall, descent = tear(rng, axis, y, numpy.clip(below, 0.0, None), strand, count, lateral, middle, splay, (10.0, 9.0, 24.0, 22.0)[variant], 2.0)
	torn = numpy.maximum(high, low) * (1.0 - hole)
	height = (rise + fall) * (1.0 - hole)
	away = numpy.where(y < 0.0, climb, descent)
	fibre = cloud(rng, 40.0, 300.0, 0.4, 1.0, 22.0)
	band = cloud(rng, 8.0, 40.0, 1.2, 1.0, 30.0)
	height += 0.07 * fibre * torn
	height -= 0.8 * numpy.exp(-(far / (2.2 * bore)) ** 2)
	height -= 6.0 * blur(hole, 0.35 / step)

	split, draw = pad()

	for crack in range(int(rng.integers(2, 5))):
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

	split = taken(split) * (1.0 - torn) * (1.0 - hole)
	hairs, draw = pad()

	for hair in range(int(rng.integers(14, 30))):
		heading = rng.choice([-1.0, 1.0])
		place = rng.uniform(-1.0, 1.0) * splay
		reach = bore * 0.7 + rng.uniform(0.0, 1.0) ** 1.5 * (16.0, 30.0, 8.0, 13.0)[variant] * 0.6
		lean = rng.normal(0.0, 0.16)
		length = rng.uniform(1.5, 6.0)
		draw.line([pin(place, heading * reach, step), pin(place + math.sin(lean) * length, heading * (reach + math.cos(lean) * length), step)], fill=int(rng.uniform(150, 255)), width=1)

	hairs = taken(hairs) * (1.0 - hole)
	height += 0.45 * blur(hairs, 0.12 / step)
	height -= 0.35 * blur(split, 0.2 / step)

	paint, alpha = blank()
	coat(paint, alpha, tint(44, 38, 33), numpy.clip(0.45 * numpy.exp(-numpy.clip(far - bore, 0.0, None) / 0.9) * (0.6 + 0.4 * cloud(rng, 10.0, 80.0, 1.0)), 0.0, 1.0))
	coat(paint, alpha, tint(46, 33, 23), numpy.clip(split * 0.8, 0.0, 1.0))
	shade = rng.uniform(0.92, 1.08, count)[strand][None, :].astype(real)
	color = mix(tint(216, 186, 134), tint(176, 128, 76), (0.75 * smooth(0.4, 1.3, band))[:, :, None]) * ((1.0 + 0.07 * fibre) * shade * (1.0 - 0.3 * numpy.exp(-away / 1.8)) * (1.0 - 0.06 * numpy.clip(-height, 0.0, 2.0)))[:, :, None]
	coat(paint, alpha, numpy.clip(color, 0.0, 1.0), torn)
	coat(paint, alpha, tint(230, 206, 162), hairs * 0.85)
	coat(paint, alpha, tint(22, 16, 12), hole)
	weight = numpy.maximum(numpy.maximum(torn, hole), numpy.maximum(0.95 * numpy.exp(-(far / (2.9 * bore)) ** 2), numpy.maximum(split * 0.55, hairs * 0.7)))

	return paint, alpha, height, weight, edge


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
}

grounds = {
	"concrete": tint(122, 117, 108),
	"paint": tint(52, 80, 94),
	"wood": tint(116, 98, 74),
}


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


def main():
	os.makedirs(output, exist_ok=True)
	os.makedirs(sheets, exist_ok=True)


if __name__ == "__main__":
	main()
