import numpy


def rasterize(uv, size, block=2000000):
    corners = numpy.asarray(uv, dtype=numpy.float64) * size - 0.5
    low = numpy.floor(corners.min(axis=1)).astype(numpy.int64)
    high = numpy.ceil(corners.max(axis=1)).astype(numpy.int64)
    low = numpy.clip(low, 0, size - 1)
    high = numpy.clip(high, 0, size - 1)
    spans = high - low + 1
    reach = spans.max(axis=1)
    owner = numpy.full(size * size, -1, dtype=numpy.int32)
    weights = numpy.zeros((size * size, 3), dtype=numpy.float32)
    a = corners[:, 0]
    b = corners[:, 1]
    c = corners[:, 2]
    denominator = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    usable = numpy.abs(denominator) > 1e-12
    order = numpy.argsort(reach, kind='stable')
    start = 0
    while start < len(order):
        stop = start
        while stop < len(order):
            side = int(reach[order[stop]])
            if (stop - start + 1) * side * side > block and stop > start:
                break
            stop += 1
        chosen = order[start:stop]
        chosen = chosen[usable[chosen]]
        start = stop
        if not len(chosen):
            continue
        bw = int(spans[chosen, 0].max())
        bh = int(spans[chosen, 1].max())
        dx, dy = numpy.meshgrid(numpy.arange(bw), numpy.arange(bh))
        dx = dx.ravel()
        dy = dy.ravel()
        px = low[chosen, 0][:, None] + dx[None, :]
        py = low[chosen, 1][:, None] + dy[None, :]
        inside_box = (px <= high[chosen, 0][:, None]) & (py <= high[chosen, 1][:, None])
        ta = a[chosen]
        tb = b[chosen]
        tc = c[chosen]
        d = denominator[chosen][:, None]
        w0 = ((tb[:, 1] - tc[:, 1])[:, None] * (px - tc[:, 0][:, None]) + (tc[:, 0] - tb[:, 0])[:, None] * (py - tc[:, 1][:, None])) / d
        w1 = ((tc[:, 1] - ta[:, 1])[:, None] * (px - tc[:, 0][:, None]) + (ta[:, 0] - tc[:, 0])[:, None] * (py - tc[:, 1][:, None])) / d
        w2 = 1.0 - w0 - w1
        inside = inside_box & (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        rows, columns = numpy.nonzero(inside)
        flat = py[rows, columns] * size + px[rows, columns]
        owner[flat] = chosen[rows].astype(numpy.int32)
        weights[flat, 0] = w0[rows, columns]
        weights[flat, 1] = w1[rows, columns]
        weights[flat, 2] = w2[rows, columns]
    covered = numpy.flatnonzero(owner >= 0)
    return covered, owner[covered], numpy.clip(weights[covered], 0.0, 1.0)


def conservative(uv, size, covered, owner, weights, reach=1.0):
    corners = numpy.asarray(uv, dtype=numpy.float64) * size - 0.5
    mask = numpy.zeros(size * size, dtype=bool)
    mask[covered] = True
    grid = mask.reshape(size, size)
    border = numpy.zeros_like(grid)
    for shift_y in (-1, 0, 1):
        for shift_x in (-1, 0, 1):
            border |= numpy.roll(numpy.roll(grid, shift_y, axis=0), shift_x, axis=1)
    border &= ~grid
    candidates = numpy.flatnonzero(border.ravel())
    if not len(candidates):
        return covered, owner, weights
    cy = candidates // size
    cx = candidates % size
    best = numpy.full(len(candidates), numpy.inf)
    best_owner = numpy.full(len(candidates), -1, dtype=numpy.int32)
    best_weights = numpy.zeros((len(candidates), 3), dtype=numpy.float32)
    lookup = numpy.full(size * size, -1, dtype=numpy.int64)
    lookup[covered] = numpy.arange(len(covered))
    for shift_y in (-1, 0, 1):
        for shift_x in (-1, 0, 1):
            ny = numpy.clip(cy + shift_y, 0, size - 1)
            nx = numpy.clip(cx + shift_x, 0, size - 1)
            index = lookup[ny * size + nx]
            valid = index >= 0
            if not valid.any():
                continue
            triangle = owner[index[valid]]
            tri = corners[triangle]
            point = numpy.stack([cx[valid], cy[valid]], axis=1).astype(numpy.float64)
            projected, bary = closest_on_triangles(point, tri)
            distance = numpy.linalg.norm(projected - point, axis=1)
            better = distance < best[valid]
            positions = numpy.flatnonzero(valid)[better]
            best[positions] = distance[better]
            best_owner[positions] = triangle[better]
            best_weights[positions] = bary[better]
    keep = best <= reach
    return numpy.concatenate([covered, candidates[keep]]), numpy.concatenate([owner, best_owner[keep]]), numpy.concatenate([weights, best_weights[keep]])


def closest_on_triangles(point, tri):
    a = tri[:, 0]
    b = tri[:, 1]
    c = tri[:, 2]
    best = None
    best_bary = None
    best_distance = numpy.full(len(point), numpy.inf)
    denominator = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    denominator = numpy.where(numpy.abs(denominator) < 1e-12, 1e-12, denominator)
    w0 = ((b[:, 1] - c[:, 1]) * (point[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (point[:, 1] - c[:, 1])) / denominator
    w1 = ((c[:, 1] - a[:, 1]) * (point[:, 0] - c[:, 0]) + (a[:, 0] - c[:, 0]) * (point[:, 1] - c[:, 1])) / denominator
    w2 = 1.0 - w0 - w1
    inside = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
    best = numpy.where(inside[:, None], point, 0.0)
    best_bary = numpy.where(inside[:, None], numpy.stack([w0, w1, w2], axis=1), 0.0)
    best_distance = numpy.where(inside, 0.0, numpy.inf)
    for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        p = tri[:, i]
        q = tri[:, j]
        edge = q - p
        t = numpy.clip(numpy.sum((point - p) * edge, axis=1) / numpy.maximum(numpy.sum(edge * edge, axis=1), 1e-12), 0.0, 1.0)
        candidate = p + edge * t[:, None]
        distance = numpy.linalg.norm(candidate - point, axis=1)
        better = distance < best_distance
        bary = numpy.zeros((len(point), 3))
        bary[:, i] = 1.0 - t
        bary[:, j] = t
        best = numpy.where(better[:, None], candidate, best)
        best_bary = numpy.where(better[:, None], bary, best_bary)
        best_distance = numpy.where(better, distance, best_distance)
    return best, best_bary.astype(numpy.float32)


def interpolate(values, owner, weights):
    corner = numpy.asarray(values)
    picked = corner[owner]
    return numpy.einsum('nk,nk...->n...', weights.astype(numpy.float64), picked.astype(numpy.float64))


def fill(image, mask):
    height, width = mask.shape
    channels = image.shape[2]
    levels = [(image * mask[:, :, None], mask.astype(numpy.float64))]
    while min(levels[-1][1].shape) > 1:
        color, weight = levels[-1]
        h, w = weight.shape
        h2 = (h + 1) // 2
        w2 = (w + 1) // 2
        padded_color = numpy.zeros((h2 * 2, w2 * 2, channels))
        padded_weight = numpy.zeros((h2 * 2, w2 * 2))
        padded_color[:h, :w] = color
        padded_weight[:h, :w] = weight
        color = padded_color.reshape(h2, 2, w2, 2, channels).sum(axis=(1, 3))
        weight = padded_weight.reshape(h2, 2, w2, 2).sum(axis=(1, 3))
        levels.append((color, weight))
    color, weight = levels[-1]
    result = color / numpy.maximum(weight, 1e-12)[:, :, None]
    for color, weight in reversed(levels[:-1]):
        h, w = weight.shape
        upsampled = numpy.repeat(numpy.repeat(result, 2, axis=0), 2, axis=1)[:h, :w]
        known = weight > 1e-9
        own = color / numpy.maximum(weight, 1e-12)[:, :, None]
        blend = numpy.clip(weight, 0.0, 1.0)[:, :, None]
        result = numpy.where(known[:, :, None], own * blend + upsampled * (1.0 - blend), upsampled)
    return numpy.where(mask[:, :, None], image, result)


def blur(field, radius):
    result = numpy.asarray(field, dtype=numpy.float64).copy()
    if radius <= 0:
        return result
    for axis in (0, 1):
        pad = [(radius + 1, radius) if a == axis else (0, 0) for a in range(result.ndim)]
        integral = numpy.cumsum(numpy.pad(result, pad, mode='edge'), axis=axis)
        upper = numpy.take(integral, numpy.arange(2 * radius + 1, integral.shape[axis]), axis=axis)
        lower = numpy.take(integral, numpy.arange(0, integral.shape[axis] - 2 * radius - 1), axis=axis)
        result = (upper - lower) / (2 * radius + 1)
    return result


def blur3(grid, radius):
    result = grid
    for axis in range(3):
        pad = [(radius + 1, radius) if a == axis else (0, 0) for a in range(grid.ndim)]
        integral = numpy.cumsum(numpy.pad(result, pad, mode='constant'), axis=axis)
        upper = numpy.take(integral, numpy.arange(2 * radius + 1, integral.shape[axis]), axis=axis)
        lower = numpy.take(integral, numpy.arange(0, integral.shape[axis] - 2 * radius - 1), axis=axis)
        result = upper - lower
    return result


def grid_fill(positions, values, known, cell, radii=(0, 1, 2, 4, 8, 16), threshold=0.3, query=None):
    positions = numpy.asarray(positions, dtype=numpy.float64)
    values = numpy.asarray(values, dtype=numpy.float64)
    if values.ndim == 1:
        values = values[:, None]
    channels = values.shape[1]
    targets = positions if query is None else numpy.asarray(query, dtype=numpy.float64)
    low = numpy.minimum(positions.min(axis=0), targets.min(axis=0)) - cell * 2.0
    scaled = (positions - low) / cell
    index = numpy.floor(scaled).astype(numpy.int64)
    dims = tuple(int(d) for d in numpy.maximum(index.max(axis=0), numpy.floor((targets - low) / cell).max(axis=0).astype(numpy.int64)) + 3)
    total = numpy.zeros(dims + (channels,), dtype=numpy.float32)
    weight = numpy.zeros(dims, dtype=numpy.float32)
    w = numpy.asarray(known, dtype=numpy.float64)
    numpy.add.at(total, (index[:, 0], index[:, 1], index[:, 2]), (values * w[:, None]).astype(numpy.float32))
    numpy.add.at(weight, (index[:, 0], index[:, 1], index[:, 2]), w.astype(numpy.float32))
    filled = numpy.zeros(dims + (channels,), dtype=numpy.float32)
    filled[:] = total.reshape(-1, channels).sum(axis=0) / max(float(weight.sum()), 1e-9)
    for radius in sorted(radii, reverse=True):
        blurred_total = blur3(total, radius) if radius else total
        blurred_weight = blur3(weight, radius) if radius else weight
        present = blurred_weight > 1e-6
        if not present.any():
            continue
        typical = float(numpy.median(blurred_weight[present]))
        confidence = numpy.clip(blurred_weight / max(typical * max(threshold, 1e-6), 1e-9), 0.0, 1.0)
        confidence = confidence * confidence * (3.0 - 2.0 * confidence)
        average = blurred_total / numpy.maximum(blurred_weight, 1e-6)[..., None]
        filled = filled * (1.0 - confidence[..., None]) + average * confidence[..., None]
    centered = (targets - low) / cell - 0.5
    base = numpy.floor(centered).astype(numpy.int64)
    fraction = centered - base
    result = numpy.zeros((len(targets), channels))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                corner = numpy.clip(base + numpy.array([dx, dy, dz]), 0, numpy.array(dims) - 1)
                factor = (fraction[:, 0] if dx else 1.0 - fraction[:, 0]) * (fraction[:, 1] if dy else 1.0 - fraction[:, 1]) * (fraction[:, 2] if dz else 1.0 - fraction[:, 2])
                result += filled[corner[:, 0], corner[:, 1], corner[:, 2]] * factor[:, None]
    return result


def gaussian(field, radius):
    result = field
    for step in range(3):
        result = blur(result, max(1, int(round(radius / 1.7))))
    return result


def upscale(image, factor=2):
    source = numpy.asarray(image, dtype=numpy.float64)
    height, width = source.shape[:2]
    rows = cubic_axis(height, height * factor)
    columns = cubic_axis(width, width * factor)
    stage = numpy.zeros((height * factor,) + source.shape[1:])
    for tap in range(4):
        stage += source[rows[0][:, tap]] * rows[1][:, tap].reshape((-1,) + (1,) * (source.ndim - 1))
    result = numpy.zeros((height * factor, width * factor) + source.shape[2:])
    for tap in range(4):
        result += stage[:, columns[0][:, tap]] * columns[1][:, tap].reshape((1, -1) + (1,) * (source.ndim - 2))
    return result


def cubic_axis(count, target):
    position = (numpy.arange(target) + 0.5) * count / target - 0.5
    base = numpy.floor(position).astype(numpy.int64)
    t = position - base
    indices = numpy.stack([base - 1, base, base + 1, base + 2], axis=1)
    indices = numpy.clip(indices, 0, count - 1)
    a = -0.5
    def kernel(x):
        x = numpy.abs(x)
        return numpy.where(x <= 1.0, (a + 2.0) * x ** 3 - (a + 3.0) * x ** 2 + 1.0, numpy.where(x < 2.0, a * x ** 3 - 5.0 * a * x ** 2 + 8.0 * a * x - 4.0 * a, 0.0))
    weights = numpy.stack([kernel(t + 1.0), kernel(t), kernel(t - 1.0), kernel(t - 2.0)], axis=1)
    weights /= weights.sum(axis=1, keepdims=True)
    return indices, weights


def downsample(image, factor=2):
    height, width = image.shape[:2]
    return image[:height - height % factor, :width - width % factor].reshape(height // factor, factor, width // factor, factor, *image.shape[2:]).mean(axis=(1, 3))


def to_srgb(linear):
    linear = numpy.clip(linear, 0.0, 1.0)
    return numpy.where(linear <= 0.0031308, linear * 12.92, 1.055 * numpy.power(numpy.maximum(linear, 0.0031308), 1.0 / 2.4) - 0.055)


def to_linear(srgb):
    srgb = numpy.clip(srgb, 0.0, 1.0)
    return numpy.where(srgb <= 0.04045, srgb / 12.92, numpy.power((srgb + 0.055) / 1.055, 2.4))


def smoothstep(low, high, value):
    t = numpy.clip((numpy.asarray(value, dtype=numpy.float64) - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def hash_points(cells, seed):
    cells = cells.astype(numpy.int64)
    value = (cells[..., 0] * 73856093) ^ (cells[..., 1] * 19349663) ^ (cells[..., 2] * 83492791) ^ (seed * 2654435761)
    value = (value ^ (value >> 13)) * 1274126177
    value = value ^ (value >> 16)
    return (value & 0xFFFFFF).astype(numpy.float64) / float(0xFFFFFF)


def noise(points, scale, seed, octaves=1, gain=0.5):
    total = numpy.zeros(len(points))
    amplitude = 1.0
    norm = 0.0
    frequency = scale
    for octave in range(octaves):
        q = points * frequency + octave * 17.31
        base = numpy.floor(q)
        f = q - base
        f = f * f * f * (f * (f * 6.0 - 15.0) + 10.0)
        result = numpy.zeros(len(points))
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    corner = base + numpy.array([dx, dy, dz])
                    weight = (f[:, 0] if dx else 1.0 - f[:, 0]) * (f[:, 1] if dy else 1.0 - f[:, 1]) * (f[:, 2] if dz else 1.0 - f[:, 2])
                    result += weight * hash_points(corner, seed + octave * 101)
        total += result * amplitude
        norm += amplitude
        amplitude *= gain
        frequency *= 2.0
    return total / norm


def cells(points, scale, seed, jitter=0.9):
    q = points * scale
    base = numpy.floor(q)
    nearest = numpy.full(len(points), numpy.inf)
    second = numpy.full(len(points), numpy.inf)
    identity = numpy.zeros(len(points))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cell = base + numpy.array([dx, dy, dz])
                offset = numpy.stack([hash_points(cell, seed + k * 7) for k in range(3)], axis=1) * jitter + (1.0 - jitter) * 0.5
                distance = numpy.linalg.norm(cell + offset - q, axis=1)
                closer = distance < nearest
                second = numpy.where(closer, nearest, numpy.minimum(second, distance))
                identity = numpy.where(closer, hash_points(cell, seed + 31), identity)
                nearest = numpy.where(closer, distance, nearest)
    return nearest, second, identity
