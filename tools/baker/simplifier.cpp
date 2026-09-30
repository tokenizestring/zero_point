
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_simplifier_c baker_simplifier;

	std::uint32_t baker_simplifier_c::simplify(std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts)
	{
		structures::vec3_s minimum{ FLT_MAX, FLT_MAX, FLT_MAX };
		structures::vec3_s maximum{ -FLT_MAX, -FLT_MAX, -FLT_MAX };

		for (const auto& part : parts)
		{
			minimum = mathematics.minimum(minimum, part.bounds_min);
			maximum = mathematics.maximum(maximum, part.bounds_max);
		}

		const auto budget{ static_cast<std::uint32_t>(std::clamp(mathematics.length(maximum - minimum) * baker::simplify_budget_per_meter, baker::simplify_budget_minimum, baker::simplify_budget_maximum)) };

		setup(vertices, indices, parts);

		run(vertices, 1.0, 0u);

		if (alive_count > budget)
		{
			run(vertices, baker::simplify_relaxed_error, budget);
		}

		rebuild(vertices, indices, parts);

		return alive_count;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t baker_simplifier_c::reduce(std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts, std::uint32_t budget)
	{
		setup(vertices, indices, parts);

		run(vertices, baker::simplify_lod_error, budget);

		rebuild(vertices, indices, parts);

		return alive_count;
	}
	/*
	//=====================================================================================
	*/
	void baker_simplifier_c::setup(const std::vector<baker::model_vertex_s>& vertices, const std::vector<std::uint32_t>& indices, const std::vector<structures::model_part_s>& parts)
	{
		const auto triangle_count{ indices.size() / 3u };

		triangles = indices;
		alive.assign(triangle_count, 1u);
		alive_count = static_cast<std::uint32_t>(triangle_count);
		quadrics.assign(vertices.size(), {});
		fans.assign(vertices.size(), {});
		stamps.assign(vertices.size(), 0u);
		locked.assign(vertices.size(), 0u);
		limits.assign(vertices.size(), 0.0);
		heap.clear();

		for (const auto& part : parts)
		{
			const auto limit{ static_cast<std::double_t>(std::max(baker::simplify_minimum_error, mathematics.length(part.bounds_max - part.bounds_min) * baker::simplify_error_fraction)) };

			for (auto index{ part.first_index }; index < part.first_index + part.index_count; index++)
			{
				limits[triangles[index]] = limit * limit;
			}
		}

		std::unordered_map<std::uint64_t, std::uint32_t> edges;

		edges.reserve(triangle_count * 3u);

		for (auto triangle{ 0u }; triangle < triangle_count; triangle++)
		{
			const auto a{ triangles[triangle * 3u] };
			const auto b{ triangles[triangle * 3u + 1u] };
			const auto c{ triangles[triangle * 3u + 2u] };
			const auto normal{ mathematics.cross(vertices[b].position - vertices[a].position, vertices[c].position - vertices[a].position) };
			const auto length{ mathematics.length(normal) };

			if (length > 1e-12f)
			{
				const auto weight{ static_cast<std::double_t>(length) * 0.5 };
				const auto nx{ static_cast<std::double_t>(normal.x / length) };
				const auto ny{ static_cast<std::double_t>(normal.y / length) };
				const auto nz{ static_cast<std::double_t>(normal.z / length) };
				const auto d{ -(nx * vertices[a].position.x + ny * vertices[a].position.y + nz * vertices[a].position.z) };
				const baker::quadric_s plane{ nx * nx * weight, nx * ny * weight, nx * nz * weight, nx * d * weight, ny * ny * weight, ny * nz * weight, ny * d * weight, nz * nz * weight, nz * d * weight, d * d * weight, weight };

				quadrics[a] = combine(quadrics[a], plane);
				quadrics[b] = combine(quadrics[b], plane);
				quadrics[c] = combine(quadrics[c], plane);
			}

			for (auto corner{ 0u }; corner < 3u; corner++)
			{
				const auto from{ triangles[triangle * 3u + corner] };
				const auto to{ triangles[triangle * 3u + (corner + 1u) % 3u] };

				fans[from].push_back(triangle);

				edges[(static_cast<std::uint64_t>(std::min(from, to)) << 32u) | std::max(from, to)]++;
			}
		}

		for (const auto& [key, count] : edges)
		{
			if (count == 1u || count > 2u)
			{
				locked[static_cast<std::uint32_t>(key >> 32u)] = 1u;
				locked[static_cast<std::uint32_t>(key & 0xFFFFFFFFull)] = 1u;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_simplifier_c::run(const std::vector<baker::model_vertex_s>& vertices, std::double_t limit_scale, std::uint32_t budget)
	{
		heap.clear();

		for (auto vertex{ 0u }; vertex < vertices.size(); vertex++)
		{
			if (baker::collapse_s entry{}; best(vertices, vertex, entry))
			{
				push(entry);
			}
		}

		while (heap.size() && alive_count > budget)
		{
			std::pop_heap(heap.begin(), heap.end(), [](const baker::collapse_s& a, const baker::collapse_s& b) { return a.cost > b.cost; });

			const auto entry{ heap.back() };

			heap.pop_back();

			if (entry.stamp == stamps[entry.from] && entry.cost <= limits[entry.from] * limit_scale * limit_scale)
			{
				if (valid(vertices, entry.from, entry.to))
				{
					collapse(entry.from, entry.to);

					gather(entry.to, ring_update);

					for (const auto vertex : ring_update)
					{
						stamps[vertex]++;

						if (baker::collapse_s next{}; best(vertices, vertex, next))
						{
							push(next);
						}
					}
				}

				else if (baker::collapse_s retry{}; best(vertices, entry.from, retry))
				{
					push(retry);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_simplifier_c::best(const std::vector<baker::model_vertex_s>& vertices, std::uint32_t from, baker::collapse_s& out)
	{
		auto found{ false };

		out = { DBL_MAX, from, from, stamps[from] };

		if (locked[from] == 0u)
		{
			for (const auto triangle : fans[from])
			{
				for (auto corner{ 0u }; alive[triangle] && corner < 3u; corner++)
				{
					const auto to{ triangles[triangle * 3u + corner] };
					const auto merged{ combine(quadrics[from], quadrics[to]) };
					const auto cost{ evaluate(merged, vertices[to].position) / std::max(merged.area, 1e-30) };

					if (to != from && cost < out.cost && valid(vertices, from, to))
					{
						out = { cost, from, to, stamps[from] };

						found = true;
					}
				}
			}
		}

		return found;
	}
	/*
	//=====================================================================================
	*/
	bool baker_simplifier_c::valid(const std::vector<baker::model_vertex_s>& vertices, std::uint32_t from, std::uint32_t to)
	{
		gather(from, ring_from);
		gather(to, ring_to);

		auto shared{ 0u };
		auto left{ 0u };
		auto right{ 0u };

		while (left < ring_from.size() && right < ring_to.size())
		{
			if (ring_from[left] == ring_to[right])
			{
				shared++;
				left++;
				right++;
			}

			else if (ring_from[left] < ring_to[right])
			{
				left++;
			}

			else
			{
				right++;
			}
		}

		auto result{ shared <= 4u };

		for (const auto triangle : fans[from])
		{
			const auto a{ triangles[triangle * 3u] };
			const auto b{ triangles[triangle * 3u + 1u] };
			const auto c{ triangles[triangle * 3u + 2u] };

			if (result && alive[triangle] && a != to && b != to && c != to)
			{
				const auto pa{ vertices[a].position };
				const auto pb{ vertices[b].position };
				const auto pc{ vertices[c].position };
				const auto moved_a{ a == from ? vertices[to].position : pa };
				const auto moved_b{ b == from ? vertices[to].position : pb };
				const auto moved_c{ c == from ? vertices[to].position : pc };
				const auto before{ mathematics.cross(pb - pa, pc - pa) };
				const auto after{ mathematics.cross(moved_b - moved_a, moved_c - moved_a) };
				const auto before_length{ mathematics.length(before) };
				const auto after_length{ mathematics.length(after) };

				result = after_length > before_length * 0.001f && (before_length < 1e-12f || mathematics.dot(before, after) > baker::simplify_flip_limit * before_length * after_length);
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_simplifier_c::collapse(std::uint32_t from, std::uint32_t to)
	{
		quadrics[to] = combine(quadrics[to], quadrics[from]);

		for (const auto triangle : fans[from])
		{
			if (alive[triangle])
			{
				const auto corners{ triangles.data() + static_cast<std::size_t>(triangle) * 3u };

				if (corners[0] == to || corners[1] == to || corners[2] == to)
				{
					alive[triangle] = 0u;

					alive_count--;
				}

				else
				{
					for (auto corner{ 0u }; corner < 3u; corner++)
					{
						corners[corner] = corners[corner] == from ? to : corners[corner];
					}

					fans[to].push_back(triangle);
				}
			}
		}

		fans[from].clear();

		locked[from] = 1u;
	}
	/*
	//=====================================================================================
	*/
	void baker_simplifier_c::gather(std::uint32_t vertex, std::vector<std::uint32_t>& ring)
	{
		ring.clear();

		for (const auto triangle : fans[vertex])
		{
			if (alive[triangle])
			{
				ring.insert(ring.end(), triangles.begin() + static_cast<std::ptrdiff_t>(triangle) * 3, triangles.begin() + static_cast<std::ptrdiff_t>(triangle) * 3 + 3);
			}
		}

		std::sort(ring.begin(), ring.end());

		ring.erase(std::unique(ring.begin(), ring.end()), ring.end());
	}
	/*
	//=====================================================================================
	*/
	void baker_simplifier_c::push(baker::collapse_s entry)
	{
		heap.push_back(entry);

		std::push_heap(heap.begin(), heap.end(), [](const baker::collapse_s& a, const baker::collapse_s& b) { return a.cost > b.cost; });
	}
	/*
	//=====================================================================================
	*/
	baker::quadric_s baker_simplifier_c::combine(const baker::quadric_s& a, const baker::quadric_s& b)
	{
		return { a.xx + b.xx, a.xy + b.xy, a.xz + b.xz, a.xw + b.xw, a.yy + b.yy, a.yz + b.yz, a.yw + b.yw, a.zz + b.zz, a.zw + b.zw, a.ww + b.ww, a.area + b.area };
	}
	/*
	//=====================================================================================
	*/
	std::double_t baker_simplifier_c::evaluate(const baker::quadric_s& quadric, structures::vec3_s point)
	{
		const auto x{ static_cast<std::double_t>(point.x) };
		const auto y{ static_cast<std::double_t>(point.y) };
		const auto z{ static_cast<std::double_t>(point.z) };

		return std::max(0.0, quadric.xx * x * x + 2.0 * quadric.xy * x * y + 2.0 * quadric.xz * x * z + 2.0 * quadric.xw * x + quadric.yy * y * y + 2.0 * quadric.yz * y * z + 2.0 * quadric.yw * y + quadric.zz * z * z + 2.0 * quadric.zw * z + quadric.ww);
	}
	/*
	//=====================================================================================
	*/
	void baker_simplifier_c::rebuild(std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts)
	{
		std::vector<std::uint32_t> remap(vertices.size(), UINT32_MAX);
		std::vector<baker::model_vertex_s> compacted;

		compacted.reserve(vertices.size());

		indices.clear();

		for (auto& part : parts)
		{
			const auto first{ part.first_index / 3u };
			const auto last{ (part.first_index + part.index_count) / 3u };

			part.first_index = static_cast<std::uint32_t>(indices.size());

			for (auto triangle{ first }; triangle < last; triangle++)
			{
				for (auto corner{ 0u }; alive[triangle] && corner < 3u; corner++)
				{
					const auto vertex{ triangles[triangle * 3u + corner] };

					if (remap[vertex] == UINT32_MAX)
					{
						remap[vertex] = static_cast<std::uint32_t>(compacted.size());

						compacted.push_back(vertices[vertex]);
					}

					indices.push_back(remap[vertex]);
				}
			}

			part.index_count = static_cast<std::uint32_t>(indices.size()) - part.first_index;
		}

		vertices = std::move(compacted);
	}
}

//=====================================================================================
