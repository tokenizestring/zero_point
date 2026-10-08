import json
import math
import os
import sys
import numpy
from PIL import Image

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
source = os.path.join(root, "assets", "source", "terrain", "copernicus", "Copernicus_DSM_COG_10_N49_00_W003_00_DEM.tif")
output = os.path.join(root, "assets", "raw", "terrain")
previews = os.path.join(root, "assets", "previews", "terrain")

world_size = 12288.0
macro_cell = 8.0
macro_size = int(world_size / macro_cell)
horizontal = 0.62
vertical = 0.8
centre_latitude = 49.214
centre_longitude = -2.131
crop = (49.13, 49.30, -2.30, -1.96)
earth = 6371008.8
shelf_depth = -34.0
shelf_reach = 900.0
reef_depth = -3.0


def load():
	image = Image.open(source)
	data = numpy.asarray(image, dtype=numpy.float32)
	rows, columns = data.shape
	tags = image.tag_v2
	scale = tags[33550]
	tie = tags[33922]

	return data, rows, columns, tie[3], tie[4], scale[0], scale[1]


def sample(data, row, column):
	rows, columns = data.shape
	row = numpy.clip(row, 0.0, rows - 1.001)
	column = numpy.clip(column, 0.0, columns - 1.001)
	top = numpy.floor(row).astype(numpy.intp)
	left = numpy.floor(column).astype(numpy.intp)
	down = (row - top).astype(numpy.float32)
	across = (column - left).astype(numpy.float32)
	upper = data[top, left] * (1.0 - across) + data[top, left + 1] * across
	lower = data[top + 1, left] * (1.0 - across) + data[top + 1, left + 1] * across

	return upper * (1.0 - down) + lower * down


def blur(field, sigma):
	rows, columns = field.shape
	wave_x = numpy.fft.rfftfreq(columns)[None, :]
	wave_y = numpy.fft.fftfreq(rows)[:, None]
	gain = numpy.exp((wave_x * wave_x + wave_y * wave_y) * (-2.0 * math.pi ** 2 * sigma * sigma))

	return numpy.fft.irfft2(numpy.fft.rfft2(field) * gain, s=(rows, columns)).astype(numpy.float32)


def distance_to(mask, cell):
	far = numpy.where(mask, 0.0, 1e9).astype(numpy.float32)

	for sweep in range(2):
		for axis in (0, 1):
			for direction in (1, -1):
				line = numpy.moveaxis(far, axis, 0)

				for index in range(1, line.shape[0]) if direction > 0 else range(line.shape[0] - 2, -1, -1):
					numpy.minimum(line[index], line[index - direction] + cell, out=line[index])

	return far


def main():
	os.makedirs(output, exist_ok=True)
	os.makedirs(previews, exist_ok=True)
	data, rows, columns, west, north, step_x, step_y = load()
	axis = (numpy.arange(macro_size, dtype=numpy.float64) + 0.5) * macro_cell - world_size * 0.5
	east_m, north_m = numpy.meshgrid(axis, axis[::-1])
	latitude = centre_latitude + numpy.degrees(north_m / horizontal / earth)
	longitude = centre_longitude + numpy.degrees(east_m / horizontal / (earth * math.cos(math.radians(centre_latitude))))
	row = (north - latitude) / step_y - 0.5
	column = (longitude - west) / step_x - 0.5
	inside = (latitude > crop[0]) & (latitude < crop[1]) & (longitude > crop[2]) & (longitude < crop[3])
	surface = numpy.where(inside, sample(data, row, column), 0.0).astype(numpy.float32)
	land = surface > 0.6
	coast = distance_to(land, macro_cell)
	inland = distance_to(~land, macro_cell)
	opened = numpy.minimum(surface, blur(surface, 1.2) + 2.0)
	height = numpy.where(land, opened * vertical, 0.0)
	seabed = shelf_depth * numpy.clip(coast / shelf_reach, 0.0, 1.0) ** 0.7 + reef_depth * numpy.exp(-coast / 120.0)
	height = numpy.where(land, height, numpy.minimum(seabed, -0.8))
	height = blur(height, 0.6)
	height[land & (height < 0.4)] = 0.4
	height = height[::-1, :].copy()
	header = {"size": macro_size, "cell": macro_cell, "origin": -world_size * 0.5, "horizontal_scale": horizontal, "vertical_scale": vertical, "centre": [centre_latitude, centre_longitude], "rows_north_to_south": False, "minimum": float(height.min()), "maximum": float(height.max()), "land_km2": float(land.sum() * macro_cell * macro_cell / 1e6), "source": "Copernicus DEM GLO-30, produced using Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA"}
	height.astype(numpy.float32).tofile(os.path.join(output, "jersey_macro.r32"))

	with open(os.path.join(output, "jersey_macro.json"), "w") as handle:
		json.dump(header, handle, indent=1)

	shade = numpy.clip((height[::-1, :] + 36.0) / 150.0, 0.0, 1.0)
	picture = numpy.stack([shade * 255.0 * numpy.where(land, 0.75, 0.25), shade * 255.0 * numpy.where(land, 0.85, 0.45), shade * 255.0 * numpy.where(land, 0.6, 0.9)], axis=2)
	Image.fromarray(numpy.clip(picture, 0, 255).astype(numpy.uint8)).save(os.path.join(previews, "jersey_macro.png"))
	print(json.dumps({key: value for key, value in header.items() if key != "source"}))


if __name__ == "__main__":
	main()
