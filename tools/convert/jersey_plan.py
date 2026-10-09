import heapq
import json
import math
import os
import sys
import numpy
from PIL import Image, ImageDraw

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
terrain = os.path.join(root, "assets", "raw", "terrain")
previews = os.path.join(root, "assets", "previews", "terrain")

with open(os.path.join(terrain, "jersey_macro.json")) as handle:
	header = json.load(handle)

size = header["size"]
cell = header["cell"]
origin = header["origin"]
horizontal = header["horizontal_scale"]
centre_latitude, centre_longitude = header["centre"]
earth = 6371008.8
heights = numpy.fromfile(os.path.join(terrain, "jersey_macro.r32"), dtype=numpy.float32).reshape(size, size)

sites = [
	("town", "Saint Aubin", 49.1935, -2.1435, 150.0, 240.0),
	("outpost", "Signal Post", 49.2522, -2.0880, 35.0, 70.0),
	("yard", "Breaker's Yard", 49.1785, -2.0960, 90.0, 150.0),
	("harbour", "Gorey Harbour", 49.1995, -2.0225, 90.0, 150.0),
	("ouen", "Saint Ouen", 49.2310, -2.2070, 110.0, 180.0),
	("portelet", "Portelet", 49.1715, -2.1840, 80.0, 140.0),
	("battery", "Noirmont Battery", 49.1672, -2.1700, 70.0, 120.0),
	("institute", "The Institute", 49.2068, -2.1477, 90.0, 150.0),
	("quarry", "Ronez Quarry", 49.2540, -2.1460, 80.0, 140.0),
	("halt", "La Haule Halt", 49.1905, -2.1585, 60.0, 110.0),
	("rozel", "Rozel Farm", 49.2350, -2.0490, 70.0, 120.0),
	("landes", "Les Landes Farm", 49.2490, -2.2300, 70.0, 120.0),
	("trinity", "Trinity Farm", 49.2380, -2.0940, 70.0, 120.0),
	("helier", "Saint Helier", 49.1860, -2.1075, 240.0, 360.0),
	("brelade", "Saint Brelade's Bay", 49.1850, -2.2010, 90.0, 150.0),
	("quennevais", "Les Quennevais", 49.1905, -2.2125, 100.0, 160.0),
	("peter", "Saint Peter", 49.2135, -2.1865, 90.0, 150.0),
	("lawrence", "Saint Lawrence", 49.2200, -2.1330, 90.0, 150.0),
	("mary", "Saint Mary", 49.2380, -2.1730, 90.0, 150.0),
	("john", "Saint John", 49.2455, -2.1360, 90.0, 150.0),
	("martin", "Saint Martin", 49.2180, -2.0505, 90.0, 150.0),
	("grouville", "Grouville", 49.1815, -2.0520, 90.0, 150.0),
	("clement", "Saint Clement", 49.1725, -2.0820, 90.0, 150.0),
	("saviour", "Saint Saviour", 49.1950, -2.0880, 90.0, 150.0),
]

roads = [
	("helier", "halt", 7.0), ("halt", "town", 7.0), ("town", "portelet", 6.0), ("portelet", "battery", 5.6), ("town", "brelade", 6.4),
	("brelade", "quennevais", 6.4), ("quennevais", "peter", 6.4), ("peter", "ouen", 6.4), ("ouen", "landes", 5.6), ("peter", "lawrence", 6.4),
	("lawrence", "institute", 5.6), ("lawrence", "helier", 6.4), ("peter", "mary", 6.0), ("mary", "john", 6.0), ("john", "quarry", 5.6),
	("john", "trinity", 6.0), ("trinity", "outpost", 5.6), ("trinity", "rozel", 5.6), ("trinity", "helier", 6.4), ("rozel", "martin", 5.6),
	("martin", "harbour", 6.0), ("martin", "saviour", 6.0), ("saviour", "helier", 6.4), ("helier", "yard", 6.4), ("helier", "clement", 6.4),
	("clement", "grouville", 6.4), ("grouville", "harbour", 6.4), ("ouen", "mary", 5.6),
]

rail = ["helier", "halt", "peter", "ouen", "mary", "john", "trinity", "martin", "harbour", (49.1885, -2.0290), "clement"]
rail_offsets = {"helier": (0.0, 260.0)}
town_ends = [(0.0, 125.0), (0.0, -145.0), (-135.0, 0.0), (140.0, 0.0)]


def game(latitude, longitude):
	east = math.radians(longitude - centre_longitude) * earth * math.cos(math.radians(centre_latitude)) * horizontal
	north = math.radians(latitude - centre_latitude) * earth * horizontal

	return east, north


def grid(x, z):
	return int(round((z - origin) / cell - 0.5)), int(round((x - origin) / cell - 0.5))


def world(row, column):
	return origin + (column + 0.5) * cell, origin + (row + 0.5) * cell


def height(x, z):
	row, column = grid(x, z)

	return float(heights[min(max(row, 0), size - 1), min(max(column, 0), size - 1)])


def plan(start, goal, limit, steep, used, reuse):
	start_cell = grid(*start)
	goal_cell = grid(*goal)
	steps = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142)]
	best = {start_cell: 0.0}
	came = {}
	frontier = [(0.0, 0.0, start_cell)]
	low = min(start_cell[0], goal_cell[0]) - 260
	high = max(start_cell[0], goal_cell[0]) + 260
	left = min(start_cell[1], goal_cell[1]) - 260
	right = max(start_cell[1], goal_cell[1]) + 260

	while frontier:
		estimate, spent, current = heapq.heappop(frontier)

		if current == goal_cell:
			break

		if spent > best.get(current, 1e18) + 1e-6:
			continue

		here = heights[current]

		for d_row, d_column, length in steps:
			row = current[0] + d_row
			column = current[1] + d_column

			if row < low or row > high or column < left or column > right or row < 1 or column < 1 or row >= size - 1 or column >= size - 1:
				continue

			there = heights[row, column]
			wet = there < 0.8 and max(abs(row - goal_cell[0]), abs(column - goal_cell[1])) > 12 and max(abs(row - start_cell[0]), abs(column - start_cell[1])) > 12

			if wet:
				continue

			run = length * cell
			grade = abs(float(there - here)) / run
			penalty = 1.0 + steep * grade * grade + (600.0 * (grade - limit) if grade > limit else 0.0)
			step = run * penalty * (reuse if used[row, column] else 1.0)
			total = best[current] + step

			if total < best.get((row, column), 1e18):
				best[(row, column)] = total
				came[(row, column)] = current
				guess = math.hypot(row - goal_cell[0], column - goal_cell[1]) * cell * reuse
				heapq.heappush(frontier, (total + guess, total, (row, column)))

	path = [goal_cell]

	while path[-1] != start_cell and path[-1] in came:
		path.append(came[path[-1]])

	return [world(row, column) for row, column in reversed(path)]


def simplify(points, tolerance):
	if len(points) < 3:
		return points

	first = numpy.array(points[0])
	last = numpy.array(points[-1])
	span = last - first
	length = numpy.hypot(*span) or 1.0
	distances = [abs(span[0] * (first[1] - p[1]) - (first[0] - p[0]) * span[1]) / length for p in points[1:-1]]
	index = int(numpy.argmax(distances)) + 1

	if distances[index - 1] > tolerance:
		return simplify(points[:index + 1], tolerance)[:-1] + simplify(points[index:], tolerance)

	return [points[0], points[-1]]


def resample(points, spacing):
	result = [points[0]]

	for index in range(1, len(points)):
		a = numpy.array(points[index - 1])
		b = numpy.array(points[index])
		pieces = max(1, int(math.ceil(numpy.hypot(*(b - a)) / spacing)))

		for piece in range(1, pieces + 1):
			result.append(tuple(a + (b - a) * piece / pieces))

	return result


def roughness(radius):
	reach = max(1, int(radius / cell))
	padded = numpy.pad(heights.astype(numpy.float64), reach, mode="edge")
	table = padded.cumsum(axis=0).cumsum(axis=1)
	squares = (padded * padded).cumsum(axis=0).cumsum(axis=1)
	span = reach * 2 + 1

	def box(source):
		total = numpy.zeros((size, size))
		total += source[span - 1:span - 1 + size, span - 1:span - 1 + size]
		total[:, 1:] -= source[span - 1:span - 1 + size, :size - 1]
		total[1:, :] -= source[:size - 1, span - 1:span - 1 + size]
		total[1:, 1:] += source[:size - 1, :size - 1]
		return total

	count = span * span
	mean = box(table) / count

	return numpy.sqrt(numpy.maximum(box(squares) / count - mean * mean, 0.0))


def snap(position, rule, inner, rough):
	row, column = grid(*position)
	reach = int(rule["search"] / cell)
	rows = slice(max(row - reach, 0), min(row + reach + 1, size))
	columns = slice(max(column - reach, 0), min(column + reach + 1, size))
	local_rows, local_columns = numpy.mgrid[rows, columns]
	distance = numpy.hypot(local_rows - row, local_columns - column) * cell
	level = heights[rows, columns]
	score = distance / rule["search"] + rough[rows, columns] * rule["flat"] - level * rule["high"] + numpy.where(level < rule["floor"], 1e6, 0.0) + numpy.where(distance > rule["search"], 1e6, 0.0)
	pick = numpy.unravel_index(numpy.argmin(score), score.shape)

	return world(local_rows[pick], local_columns[pick])


rules = {
	"town": {"search": 1400.0, "flat": 0.9, "high": 0.0, "floor": 4.0},
	"outpost": {"search": 1600.0, "flat": 0.0, "high": 1.0, "floor": 20.0},
	"halt": {"search": 700.0, "flat": 0.3, "high": 0.0, "floor": 3.0},
	"harbour": {"search": 700.0, "flat": 0.6, "high": -0.02, "floor": 4.5},
	"brelade": {"search": 700.0, "flat": 0.2, "high": -0.08, "floor": 2.5},
	"clement": {"search": 600.0, "flat": 0.2, "high": -0.05, "floor": 2.5},
	"default": {"search": 500.0, "flat": 0.25, "high": 0.0, "floor": 3.0},
}


def prune(points, reach, skip, window):
	result = []

	for point in points:
		for index in range(len(result) - skip - 1, max(len(result) - window, 0) - 1, -1):
			if math.hypot(result[index][0] - point[0], result[index][1] - point[1]) < reach:
				del result[index + 1:]
				break

		result.append(point)

	return result


def thin(points, spacing):
	result = [points[0]]

	for point in points[1:-1]:
		if math.hypot(point[0] - result[-1][0], point[1] - result[-1][1]) >= spacing:
			result.append(point)

	if len(points) > 1:
		if len(result) > 1 and math.hypot(points[-1][0] - result[-1][0], points[-1][1] - result[-1][1]) < spacing * 0.5:
			result[-1] = points[-1]
		else:
			result.append(points[-1])

	return result


def split(path, used):
	runs = []
	current = []

	for index, point in enumerate(path):
		if used[grid(*point)]:
			if current:
				current.append(point)
				runs.append(current)
				current = []
		else:
			if not current and index:
				current.append(path[index - 1])
			current.append(point)

	if current:
		runs.append(current)

	return [run for run in runs if len(run) > 4]


def mark(used, points, reach):
	for x, z in points:
		row, column = grid(x, z)
		used[max(row - reach, 0):row + reach + 1, max(column - reach, 0):column + reach + 1] = True


def main():
	positions = {}
	report = []
	rough = roughness(90.0)

	for key, name, latitude, longitude, inner, outer in sites:
		start = game(latitude, longitude)
		x, z = snap(start, rules.get(key, rules["default"]), inner, rough)
		positions[key] = (x, z)
		report.append("%-12s %-22s %8.0f %8.0f  height %6.1f  moved %5.0f m  roughness %4.1f" % (key, name, x, z, height(x, z), math.hypot(x - start[0], z - start[1]), rough[grid(x, z)]))

	used = numpy.zeros((size, size), dtype=bool)
	road_paths = []

	def endpoint(key, other):
		if key != "town":
			return positions[key]

		centre = positions[key]
		far = positions[other]

		return min(((centre[0] + dx, centre[1] + dz) for dx, dz in town_ends), key=lambda end: math.hypot(end[0] - far[0], end[1] - far[1]))

	for start, goal, width in roads:
		path = plan(endpoint(start, goal), endpoint(goal, start), 0.09, 400.0, used, 0.6)

		for part, run in enumerate(split(path, used)):
			points = resample(thin(simplify(run, 9.0), 28.0), 100.0)
			road_paths.append(("%s_%s%s" % (start, goal, "_%d" % part if part else ""), width, points))

		mark(used, path, 1)

	rail_used = numpy.zeros((size, size), dtype=bool)
	rail_path = []

	def waypoint(entry):
		if isinstance(entry, tuple):
			return snap(game(*entry), rules["harbour"], 0.0, rough)

		offset = rail_offsets.get(entry, (0.0, 0.0))

		return positions[entry][0] + offset[0], positions[entry][1] + offset[1]

	for index, entry in enumerate(rail):
		rail_path += plan(waypoint(entry), waypoint(rail[(index + 1) % len(rail)]), 0.022, 9000.0, rail_used, 1.0)[:-1]

	rail_points = resample(simplify(prune(rail_path, 40.0, 12, 200), 24.0), 140.0)[:-1]

	shade = numpy.clip((heights + 36.0) / 150.0, 0.0, 1.0)
	land = heights > 0.6
	picture = numpy.stack([shade * 255.0 * numpy.where(land, 0.75, 0.25), shade * 255.0 * numpy.where(land, 0.85, 0.45), shade * 255.0 * numpy.where(land, 0.6, 0.9)], axis=2)
	image = Image.fromarray(numpy.clip(picture[::-1, :], 0, 255).astype(numpy.uint8))
	draw = ImageDraw.Draw(image)
	pixel = lambda x, z: ((x - origin) / cell, size - 1 - (z - origin) / cell)

	for name, width, points in road_paths:
		draw.line([pixel(x, z) for x, z in points], fill=(240, 220, 120), width=3)

	draw.line([pixel(x, z) for x, z in rail_points + rail_points[:1]], fill=(220, 60, 60), width=3)

	for key, name, latitude, longitude, inner, outer in sites:
		x, z = positions[key]
		px, pz = pixel(x, z)
		draw.ellipse([px - inner / cell, pz - inner / cell, px + inner / cell, pz + inner / cell], outline=(255, 255, 255), width=2)
		draw.text((px + 8, pz - 8), name, fill=(255, 255, 255))

	image.save(os.path.join(previews, "jersey_plan.png"))
	lines = []
	lines.append("\tconstexpr structures::world_site_s world_sites[] =\n\t{")
	lines += ["\t\t{ { %.1ff, %.1ff }, %.1ff, %.1ff, 0.0f, structures::landmark_%s }," % (positions[key][0], positions[key][1], inner, outer, key) for key, name, latitude, longitude, inner, outer in sites]
	lines[-1] = lines[-1].rstrip(",")
	lines.append("\t};")
	lines.append("\tconstexpr structures::vec2_s railway_points[] = { %s };" % ", ".join("{ %.0f.0f, %.0f.0f }" % point for point in rail_points))

	for name, width, points in road_paths:
		lines.append("\tconstexpr structures::vec2_s road_%s_points[] = { %s };" % (name, ", ".join("{ %.0f.0f, %.0f.0f }" % point for point in points)))

	lines.append("\tconstexpr structures::world_route_s world_routes[] =\n\t{")
	lines.append("\t\t{ railway_points, static_cast<std::uint32_t>(std::size(railway_points)), structures::route_rail, 5.2f, 0.025f, 100.0f, 0.65f, true },")
	lines += ["\t\t{ road_%s_points, static_cast<std::uint32_t>(std::size(road_%s_points)), structures::route_road, %.1ff, 0.1f, 20.0f, 0.5f, false }," % (name, name, width) for name, width, points in road_paths]
	lines[-1] = lines[-1].rstrip(",")
	lines.append("\t};")

	with open(sys.argv[1], "w") as handle:
		handle.write("\n".join(lines) + "\n")

	print("\n".join(report))
	print("roads %d, road points %d, rail points %d, rail length %.0f m" % (len(road_paths), sum(len(p) for _, _, p in road_paths), len(rail_points), sum(math.hypot(rail_points[i][0] - rail_points[i - 1][0], rail_points[i][1] - rail_points[i - 1][1]) for i in range(len(rail_points)))))


if __name__ == "__main__":
	main()
