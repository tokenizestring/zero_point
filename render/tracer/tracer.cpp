
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	tracer_c tracer;

	void tracer_c::build(const std::vector<structures::vertex_s>& vertices, const std::vector<std::uint32_t>& indices)
	{
		const auto count{ static_cast<std::uint32_t>(indices.size() / 3u) };

		triangles.resize(count);
		centroids.resize(count);
		triangle_min.resize(count);
		triangle_max.resize(count);
		nodes.clear();
		nodes.reserve(static_cast<std::size_t>(count) * 2u);

		structures::vec3_s root_min{ FLT_MAX, FLT_MAX, FLT_MAX };
		structures::vec3_s root_max{ -FLT_MAX, -FLT_MAX, -FLT_MAX };

		for (auto index{ 0u }; index < count; index++)
		{
			const auto& a{ vertices[indices[index * 3u]] };
			const auto& b{ vertices[indices[index * 3u + 1u]] };
			const auto& c{ vertices[indices[index * 3u + 2u]] };
			const auto edge1{ b.position - a.position };
			const auto edge2{ c.position - a.position };

			triangles[index] = { a.position, edge1, edge2, mathematics.normalize(mathematics.cross(edge1, edge2)), a.material };
			triangle_min[index] = mathematics.minimum(a.position, mathematics.minimum(b.position, c.position));
			triangle_max[index] = mathematics.maximum(a.position, mathematics.maximum(b.position, c.position));
			centroids[index] = (triangle_min[index] + triangle_max[index]) * 0.5f;

			root_min = mathematics.minimum(root_min, triangle_min[index]);
			root_max = mathematics.maximum(root_max, triangle_max[index]);
		}

		nodes.push_back({ root_min, 0u, root_max, count });

		std::vector<std::uint32_t> pending{ 0u };

		while (pending.size())
		{
			const auto node_index{ pending.back() };

			pending.pop_back();

			split(node_index, pending);
		}

		logger.write("tracer: %u triangles, %zu nodes", count, nodes.size());
	}
	/*
	//=====================================================================================
	*/
	void tracer_c::split(std::uint32_t node_index, std::vector<std::uint32_t>& pending)
	{
		const auto node{ nodes[node_index] };

		if (node.count > bvh_leaf_size)
		{
			structures::vec3_s centroid_min{ FLT_MAX, FLT_MAX, FLT_MAX };
			structures::vec3_s centroid_max{ -FLT_MAX, -FLT_MAX, -FLT_MAX };

			for (auto index{ node.first }; index < node.first + node.count; index++)
			{
				centroid_min = mathematics.minimum(centroid_min, centroids[index]);
				centroid_max = mathematics.maximum(centroid_max, centroids[index]);
			}

			const auto extent{ centroid_max - centroid_min };
			const auto axis{ extent.x > extent.y && extent.x > extent.z ? 0u : (extent.y > extent.z ? 1u : 2u) };

			if (extent[axis] > 1e-6f)
			{
				std::uint32_t bin_count[bvh_bins]{};
				structures::vec3_s bin_min[bvh_bins]{};
				structures::vec3_s bin_max[bvh_bins]{};

				for (auto bin{ 0u }; bin < bvh_bins; bin++)
				{
					bin_min[bin] = { FLT_MAX, FLT_MAX, FLT_MAX };
					bin_max[bin] = { -FLT_MAX, -FLT_MAX, -FLT_MAX };
				}

				const auto scale{ static_cast<std::float_t>(bvh_bins) / extent[axis] };

				for (auto index{ node.first }; index < node.first + node.count; index++)
				{
					const auto bin{ std::min(static_cast<std::uint32_t>((centroids[index][axis] - centroid_min[axis]) * scale), bvh_bins - 1u) };

					bin_count[bin]++;

					bin_min[bin] = mathematics.minimum(bin_min[bin], triangle_min[index]);
					bin_max[bin] = mathematics.maximum(bin_max[bin], triangle_max[index]);
				}

				auto best_cost{ FLT_MAX };
				auto best_split{ 0u };

				for (auto split_at{ 1u }; split_at < bvh_bins; split_at++)
				{
					structures::vec3_s left_min{ FLT_MAX, FLT_MAX, FLT_MAX }, left_max{ -FLT_MAX, -FLT_MAX, -FLT_MAX };
					structures::vec3_s right_min{ FLT_MAX, FLT_MAX, FLT_MAX }, right_max{ -FLT_MAX, -FLT_MAX, -FLT_MAX };

					auto left_count{ 0u };
					auto right_count{ 0u };

					for (auto bin{ 0u }; bin < bvh_bins; bin++)
					{
						if (bin_count[bin])
						{
							if (bin < split_at)
							{
								left_count += bin_count[bin];
								left_min = mathematics.minimum(left_min, bin_min[bin]);
								left_max = mathematics.maximum(left_max, bin_max[bin]);
							}

							else
							{
								right_count += bin_count[bin];
								right_min = mathematics.minimum(right_min, bin_min[bin]);
								right_max = mathematics.maximum(right_max, bin_max[bin]);
							}
						}
					}

					if (left_count && right_count)
					{
						if (const auto cost{ static_cast<std::float_t>(left_count) * area(left_min, left_max) + static_cast<std::float_t>(right_count) * area(right_min, right_max) }; cost < best_cost)
						{
							best_cost = cost;

							best_split = split_at;
						}
					}
				}

				if (best_split > 0u && (best_cost < static_cast<std::float_t>(node.count) * area(node.minimum, node.maximum) || node.count > 16u))
				{
					auto middle{ node.first };

					for (auto index{ node.first }; index < node.first + node.count; index++)
					{
						if (std::min(static_cast<std::uint32_t>((centroids[index][axis] - centroid_min[axis]) * scale), bvh_bins - 1u) < best_split)
						{
							swap_triangles(index, middle);

							middle++;
						}
					}

					if (middle > node.first && middle < node.first + node.count)
					{
						const auto left_index{ static_cast<std::uint32_t>(nodes.size()) };

						structures::bvh_node_s left{ { FLT_MAX, FLT_MAX, FLT_MAX }, node.first, { -FLT_MAX, -FLT_MAX, -FLT_MAX }, middle - node.first };
						structures::bvh_node_s right{ { FLT_MAX, FLT_MAX, FLT_MAX }, middle, { -FLT_MAX, -FLT_MAX, -FLT_MAX }, node.first + node.count - middle };

						for (auto index{ left.first }; index < left.first + left.count; index++)
						{
							left.minimum = mathematics.minimum(left.minimum, triangle_min[index]);
							left.maximum = mathematics.maximum(left.maximum, triangle_max[index]);
						}

						for (auto index{ right.first }; index < right.first + right.count; index++)
						{
							right.minimum = mathematics.minimum(right.minimum, triangle_min[index]);
							right.maximum = mathematics.maximum(right.maximum, triangle_max[index]);
						}

						nodes.push_back(left);
						nodes.push_back(right);

						nodes[node_index].first = left_index;
						nodes[node_index].count = 0u;

						pending.push_back(left_index);
						pending.push_back(left_index + 1u);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void tracer_c::swap_triangles(std::uint32_t a, std::uint32_t b)
	{
		std::swap(triangles[a], triangles[b]);
		std::swap(centroids[a], centroids[b]);
		std::swap(triangle_min[a], triangle_min[b]);
		std::swap(triangle_max[a], triangle_max[b]);
	}
	/*
	//=====================================================================================
	*/
	std::float_t tracer_c::area(structures::vec3_s minimum, structures::vec3_s maximum)
	{
		const auto size{ mathematics.maximum(maximum - minimum, { 0.0f, 0.0f, 0.0f }) };

		return size.x * size.y + size.y * size.z + size.z * size.x;
	}
	/*
	//=====================================================================================
	*/
	std::float_t tracer_c::box_entry(const structures::bvh_node_s& node, structures::vec3_s origin, structures::vec3_s inverse, std::float_t limit)
	{
		const auto tx0{ (node.minimum.x - origin.x) * inverse.x };
		const auto tx1{ (node.maximum.x - origin.x) * inverse.x };
		const auto ty0{ (node.minimum.y - origin.y) * inverse.y };
		const auto ty1{ (node.maximum.y - origin.y) * inverse.y };
		const auto tz0{ (node.minimum.z - origin.z) * inverse.z };
		const auto tz1{ (node.maximum.z - origin.z) * inverse.z };
		const auto entry{ std::max(std::max(std::min(tx0, tx1), std::min(ty0, ty1)), std::min(tz0, tz1)) };
		const auto exit{ std::min(std::min(std::max(tx0, tx1), std::max(ty0, ty1)), std::max(tz0, tz1)) };

		return (exit >= std::max(entry, 0.0f) && entry < limit) ? entry : FLT_MAX;
	}
	/*
	//=====================================================================================
	*/
	bool tracer_c::intersect(structures::vec3_s origin, structures::vec3_s direction, std::float_t maximum_distance, structures::ray_hit_s& hit)
	{
		const structures::vec3_s inverse{ 1.0f / (std::fabs(direction.x) > 1e-9f ? direction.x : 1e-9f), 1.0f / (std::fabs(direction.y) > 1e-9f ? direction.y : 1e-9f), 1.0f / (std::fabs(direction.z) > 1e-9f ? direction.z : 1e-9f) };

		std::uint32_t stack[64]{};

		auto depth{ 0u };
		auto node_index{ 0u };
		auto found{ false };
		auto active{ nodes.size() > 0u };

		hit.distance = maximum_distance;

		while (active)
		{
			const auto& node{ nodes[node_index] };

			if (node.count)
			{
				for (auto index{ node.first }; index < node.first + node.count; index++)
				{
					const auto& triangle{ triangles[index] };
					const auto p{ mathematics.cross(direction, triangle.edge2) };
					const auto determinant{ mathematics.dot(triangle.edge1, p) };

					if (std::fabs(determinant) > 1e-10f)
					{
						const auto inverse_determinant{ 1.0f / determinant };
						const auto offset{ origin - triangle.v0 };
						const auto u{ mathematics.dot(offset, p) * inverse_determinant };

						if (u >= 0.0f && u <= 1.0f)
						{
							const auto q{ mathematics.cross(offset, triangle.edge1) };
							const auto v{ mathematics.dot(direction, q) * inverse_determinant };

							if (v >= 0.0f && u + v <= 1.0f)
							{
								if (const auto distance{ mathematics.dot(triangle.edge2, q) * inverse_determinant }; distance > 0.0005f && distance < hit.distance)
								{
									hit.distance = distance;
									hit.triangle = index;
									hit.backface = determinant < 0.0f;

									found = true;
								}
							}
						}
					}
				}

				active = depth > 0u;

				if (active)
				{
					node_index = stack[--depth];
				}
			}

			else
			{
				auto near_index{ node.first };
				auto far_index{ node.first + 1u };
				auto near_entry{ box_entry(nodes[near_index], origin, inverse, hit.distance) };
				auto far_entry{ box_entry(nodes[far_index], origin, inverse, hit.distance) };

				if (far_entry < near_entry)
				{
					std::swap(near_index, far_index);
					std::swap(near_entry, far_entry);
				}

				if (near_entry < FLT_MAX)
				{
					if (far_entry < FLT_MAX && depth < 64u)
					{
						stack[depth++] = far_index;
					}

					node_index = near_index;
				}

				else
				{
					active = depth > 0u;

					if (active)
					{
						node_index = stack[--depth];
					}
				}
			}
		}

		return found;
	}
	/*
	//=====================================================================================
	*/
	bool tracer_c::occluded(structures::vec3_s origin, structures::vec3_s direction, std::float_t maximum_distance)
	{
		const structures::vec3_s inverse{ 1.0f / (std::fabs(direction.x) > 1e-9f ? direction.x : 1e-9f), 1.0f / (std::fabs(direction.y) > 1e-9f ? direction.y : 1e-9f), 1.0f / (std::fabs(direction.z) > 1e-9f ? direction.z : 1e-9f) };

		std::uint32_t stack[64]{};

		auto depth{ 0u };
		auto node_index{ 0u };
		auto blocked{ false };
		auto active{ nodes.size() > 0u };

		while (active && blocked == false)
		{
			const auto& node{ nodes[node_index] };

			if (node.count)
			{
				for (auto index{ node.first }; index < node.first + node.count && blocked == false; index++)
				{
					const auto& triangle{ triangles[index] };
					const auto p{ mathematics.cross(direction, triangle.edge2) };
					const auto determinant{ mathematics.dot(triangle.edge1, p) };

					if (std::fabs(determinant) > 1e-10f)
					{
						const auto inverse_determinant{ 1.0f / determinant };
						const auto offset{ origin - triangle.v0 };
						const auto u{ mathematics.dot(offset, p) * inverse_determinant };

						if (u >= 0.0f && u <= 1.0f)
						{
							const auto q{ mathematics.cross(offset, triangle.edge1) };
							const auto v{ mathematics.dot(direction, q) * inverse_determinant };
							const auto distance{ mathematics.dot(triangle.edge2, q) * inverse_determinant };

							blocked = v >= 0.0f && u + v <= 1.0f && distance > 0.0005f && distance < maximum_distance;
						}
					}
				}

				active = depth > 0u;

				if (active)
				{
					node_index = stack[--depth];
				}
			}

			else
			{
				const auto left_entry{ box_entry(nodes[node.first], origin, inverse, maximum_distance) };
				const auto right_entry{ box_entry(nodes[node.first + 1u], origin, inverse, maximum_distance) };

				if (left_entry < FLT_MAX && right_entry < FLT_MAX)
				{
					if (depth < 64u)
					{
						stack[depth++] = node.first + 1u;
					}

					node_index = node.first;
				}

				else if (left_entry < FLT_MAX)
				{
					node_index = node.first;
				}

				else if (right_entry < FLT_MAX)
				{
					node_index = node.first + 1u;
				}

				else
				{
					active = depth > 0u;

					if (active)
					{
						node_index = stack[--depth];
					}
				}
			}
		}

		return blocked;
	}
}

//=====================================================================================
