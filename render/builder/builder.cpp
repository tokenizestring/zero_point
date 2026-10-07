
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	builder_c builder;

	void builder_c::clear()
	{
		vertices.clear();
		indices.clear();

		material = 0u;
		world_uv = true;
		uv_offset = {};
	}
	/*
	//=====================================================================================
	*/
	std::uint64_t builder_c::strip()
	{
		const auto freed{ vertices.capacity() * sizeof(structures::vertex_s) + indices.capacity() * sizeof(std::uint32_t) };

		clear();

		vertices.shrink_to_fit();
		indices.shrink_to_fit();

		return freed;
	}
	/*
	//=====================================================================================
	*/
	void builder_c::set_material(std::uint32_t id)
	{
		material = id;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t builder_c::add_vertex(structures::vec3_s position, structures::vec3_s normal, structures::vec2_s uv)
	{
		vertices.push_back({ position, normal, { 1.0f, 0.0f, 0.0f, 1.0f }, uv, material });

		return static_cast<std::uint32_t>(vertices.size() - 1u);
	}
	/*
	//=====================================================================================
	*/
	void builder_c::add_triangle(std::uint32_t a, std::uint32_t b, std::uint32_t c)
	{
		const auto facing{ vertices[a].normal + vertices[b].normal + vertices[c].normal };
		const auto winding{ mathematics.cross(vertices[b].position - vertices[a].position, vertices[c].position - vertices[a].position) };

		indices.push_back(a);

		if (mathematics.dot(winding, facing) >= 0.0f)
		{
			indices.push_back(b);
			indices.push_back(c);
		}

		else
		{
			indices.push_back(c);
			indices.push_back(b);
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s builder_c::project_uv(structures::vec3_s position, structures::vec3_s normal)
	{
		auto tangent{ structures::vec3_s{ 1.0f, 0.0f, 0.0f } };

		if (std::fabs(normal.y) > 0.7f)
		{
			tangent = mathematics.normalize(tangent - normal * normal.x);
		}

		else
		{
			tangent = mathematics.normalize(mathematics.cross({ 0.0f, 1.0f, 0.0f }, -normal));
		}

		const auto bitangent{ mathematics.cross(normal, tangent) };

		return structures::vec2_s{ mathematics.dot(position, tangent), mathematics.dot(position, bitangent) } + uv_offset;
	}
	/*
	//=====================================================================================
	*/
	void builder_c::quad(structures::vec3_s p0, structures::vec3_s p1, structures::vec3_s p2, structures::vec3_s p3, structures::vec3_s normal)
	{
		const auto first_vertex{ static_cast<std::uint32_t>(vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(indices.size()) };

		const auto a{ add_vertex(p0, normal, project_uv(p0, normal)) };
		const auto b{ add_vertex(p1, normal, project_uv(p1, normal)) };
		const auto c{ add_vertex(p2, normal, project_uv(p2, normal)) };
		const auto d{ add_vertex(p3, normal, project_uv(p3, normal)) };

		add_triangle(a, b, c);
		add_triangle(a, c, d);

		compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void builder_c::box(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation)
	{
		box_faces(center, size, rotation, 0x3Fu);
	}
	/*
	//=====================================================================================
	*/
	void builder_c::box_faces(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation, std::uint32_t face_mask)
	{
		const structures::vec3_s units[3] = { mathematics.quat_rotate(rotation, { 1.0f, 0.0f, 0.0f }), mathematics.quat_rotate(rotation, { 0.0f, 1.0f, 0.0f }), mathematics.quat_rotate(rotation, { 0.0f, 0.0f, 1.0f }) };
		const structures::vec3_s halves[3] = { units[0] * (size.x * 0.5f), units[1] * (size.y * 0.5f), units[2] * (size.z * 0.5f) };

		for (auto face{ 0u }; face < 6u; face++)
		{
			if (face_mask & (1u << face))
			{
				const auto axis{ face / 2u };
				const auto side{ (face % 2u) ? -1.0f : 1.0f };
				const auto normal{ units[axis] * side };
				const auto face_center{ center + halves[axis] * side };
				const auto first{ halves[(axis + 1u) % 3u] };
				const auto second{ halves[(axis + 2u) % 3u] };

				quad(face_center - first - second, face_center + first - second, face_center + first + second, face_center - first + second, normal);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void builder_c::cylinder(structures::vec3_s base, structures::vec3_s axis, std::float_t radius, std::float_t length, std::uint32_t segments, bool caps)
	{
		cone(base, axis, radius, radius, length, segments, caps);
	}
	/*
	//=====================================================================================
	*/
	void builder_c::cone(structures::vec3_s base, structures::vec3_s axis, std::float_t radius_base, std::float_t radius_top, std::float_t length, std::uint32_t segments, bool caps)
	{
		const auto first_vertex{ static_cast<std::uint32_t>(vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(indices.size()) };
		const auto direction{ mathematics.normalize(axis) };
		const auto u_axis{ mathematics.any_perpendicular(direction) };
		const auto v_axis{ mathematics.cross(direction, u_axis) };
		const auto slope{ (radius_base - radius_top) / std::max(length, 0.0001f) };
		const auto circumference_scale{ std::max(radius_base, radius_top) };

		for (auto segment{ 0u }; segment <= segments; segment++)
		{
			const auto angle{ static_cast<std::float_t>(segment) / static_cast<std::float_t>(segments) * two_pi };
			const auto around{ u_axis * std::cos(angle) + v_axis * std::sin(angle) };
			const auto normal{ mathematics.normalize(around + direction * slope) };

			add_vertex(base + around * radius_base, normal, { angle * circumference_scale, 0.0f });
			add_vertex(base + direction * length + around * radius_top, normal, { angle * circumference_scale, -length });
		}

		for (auto segment{ 0u }; segment < segments; segment++)
		{
			const auto a{ first_vertex + segment * 2u };

			add_triangle(a, a + 1u, a + 3u);
			add_triangle(a, a + 3u, a + 2u);
		}

		if (caps)
		{
			for (auto end{ 0u }; end < 2u; end++)
			{
				const auto normal{ end ? direction : -direction };
				const auto center{ end ? base + direction * length : base };
				const auto radius{ end ? radius_top : radius_base };

				if (radius > 0.0001f)
				{
					const auto hub{ add_vertex(center, normal, project_uv(center, normal)) };

					for (auto segment{ 0u }; segment < segments; segment++)
					{
						const auto angle0{ static_cast<std::float_t>(segment) / static_cast<std::float_t>(segments) * two_pi };
						const auto angle1{ static_cast<std::float_t>(segment + 1u) / static_cast<std::float_t>(segments) * two_pi };
						const auto p0{ center + (u_axis * std::cos(angle0) + v_axis * std::sin(angle0)) * radius };
						const auto p1{ center + (u_axis * std::cos(angle1) + v_axis * std::sin(angle1)) * radius };

						add_triangle(hub, add_vertex(p0, normal, project_uv(p0, normal)), add_vertex(p1, normal, project_uv(p1, normal)));
					}
				}
			}
		}

		compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void builder_c::sphere(structures::vec3_s center, std::float_t radius, std::uint32_t segments, std::uint32_t rings)
	{
		const auto first_vertex{ static_cast<std::uint32_t>(vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(indices.size()) };

		for (auto ring{ 0u }; ring <= rings; ring++)
		{
			const auto theta{ static_cast<std::float_t>(ring) / static_cast<std::float_t>(rings) * pi };

			for (auto segment{ 0u }; segment <= segments; segment++)
			{
				const auto phi{ static_cast<std::float_t>(segment) / static_cast<std::float_t>(segments) * two_pi };
				const structures::vec3_s normal{ std::sin(theta) * std::cos(phi), std::cos(theta), std::sin(theta) * std::sin(phi) };

				add_vertex(center + normal * radius, normal, { phi * radius, theta * radius });
			}
		}

		for (auto ring{ 0u }; ring < rings; ring++)
		{
			for (auto segment{ 0u }; segment < segments; segment++)
			{
				const auto a{ first_vertex + ring * (segments + 1u) + segment };
				const auto b{ a + segments + 1u };

				if (ring > 0u)
				{
					add_triangle(a, a + 1u, b);
				}

				if (ring + 1u < rings)
				{
					add_triangle(a + 1u, b + 1u, b);
				}
			}
		}

		compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void builder_c::ramp(structures::vec3_s center, structures::vec3_s size, std::float_t yaw)
	{
		const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };
		const auto half{ size * 0.5f };

		const auto corner = [&](std::float_t x, std::float_t y, std::float_t z)
			{
				return center + mathematics.quat_rotate(rotation, { x, y, z });
			};

		const auto a{ corner(-half.x, -half.y, -half.z) };
		const auto b{ corner(half.x, -half.y, -half.z) };
		const auto c{ corner(half.x, -half.y, half.z) };
		const auto d{ corner(-half.x, -half.y, half.z) };
		const auto e{ corner(half.x, half.y, half.z) };
		const auto f{ corner(-half.x, half.y, half.z) };
		const auto slope_normal{ mathematics.normalize(mathematics.quat_rotate(rotation, { 0.0f, size.z, -size.y })) };
		const auto back_normal{ mathematics.quat_rotate(rotation, { 0.0f, 0.0f, 1.0f }) };
		const auto right_normal{ mathematics.quat_rotate(rotation, { 1.0f, 0.0f, 0.0f }) };

		quad(a, b, c, d, { 0.0f, -1.0f, 0.0f });
		quad(a, b, e, f, slope_normal);
		quad(d, c, e, f, back_normal);

		const auto first_vertex{ static_cast<std::uint32_t>(vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(indices.size()) };

		add_triangle(add_vertex(b, right_normal, project_uv(b, right_normal)), add_vertex(c, right_normal, project_uv(c, right_normal)), add_vertex(e, right_normal, project_uv(e, right_normal)));
		add_triangle(add_vertex(a, -right_normal, project_uv(a, -right_normal)), add_vertex(d, -right_normal, project_uv(d, -right_normal)), add_vertex(f, -right_normal, project_uv(f, -right_normal)));

		compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void builder_c::prism(const structures::vec2_s* outline, std::uint32_t count, std::float_t length, const structures::mat4_s& placement)
	{
		std::vector<structures::vec3_s> front(count);
		std::vector<structures::vec3_s> back(count);

		structures::vec2_s centroid{};

		for (auto index{ 0u }; index < count; index++)
		{
			front[index] = mathematics.transform_point({ outline[index].x, outline[index].y, -length * 0.5f }, placement);
			back[index] = mathematics.transform_point({ outline[index].x, outline[index].y, length * 0.5f }, placement);

			centroid += outline[index] * (1.0f / static_cast<std::float_t>(count));
		}

		for (auto index{ 0u }; index < count; index++)
		{
			const auto next{ (index + 1u) % count };
			const auto edge{ outline[next] - outline[index] };
			const auto midpoint{ (outline[next] + outline[index]) * 0.5f };

			auto local_normal{ structures::vec3_s{ edge.y, -edge.x, 0.0f } };

			if (mathematics.dot(structures::vec2_s{ local_normal.x, local_normal.y }, midpoint - centroid) < 0.0f)
			{
				local_normal = -local_normal;
			}

			quad(front[index], front[next], back[next], back[index], mathematics.normalize(mathematics.transform_vector(local_normal, placement)));
		}

		for (auto side{ 0u }; side < 2u; side++)
		{
			const auto first_vertex{ static_cast<std::uint32_t>(vertices.size()) };
			const auto first_index{ static_cast<std::uint32_t>(indices.size()) };
			const auto& ring{ side ? back : front };
			const auto normal{ mathematics.normalize(mathematics.transform_vector({ 0.0f, 0.0f, side ? 1.0f : -1.0f }, placement)) };

			for (auto index{ 0u }; index < count; index++)
			{
				add_vertex(ring[index], normal, project_uv(ring[index], normal));
			}

			for (auto index{ 1u }; index + 1u < count; index++)
			{
				add_triangle(first_vertex, first_vertex + index, first_vertex + index + 1u);
			}

			compute_tangents(first_vertex, first_index);
		}
	}
	/*
	//=====================================================================================
	*/
	void builder_c::append(const structures::model_s& model, std::uint32_t first_index, std::uint32_t index_count, const structures::mat4_s& placement)
	{
		std::vector<std::uint32_t> remap(model.vertices.size(), 0xFFFFFFFFu);

		const auto end{ std::min(first_index + index_count, static_cast<std::uint32_t>(model.indices.size())) };

		for (auto index{ first_index }; index < end; index++)
		{
			const auto source{ model.indices[index] };

			if (remap[source] == 0xFFFFFFFFu)
			{
				const auto& vertex{ model.vertices[source] };
				const auto tangent{ mathematics.normalize(mathematics.transform_vector(vertex.tangent.xyz(), placement)) };

				vertices.push_back({ mathematics.transform_point(vertex.position, placement), mathematics.normalize(mathematics.transform_vector(vertex.normal, placement)), { tangent.x, tangent.y, tangent.z, vertex.tangent.w }, vertex.uv, vertex.material });

				remap[source] = static_cast<std::uint32_t>(vertices.size() - 1u);
			}

			indices.push_back(remap[source]);
		}
	}
	/*
	//=====================================================================================
	*/
	void builder_c::compute_tangents(std::uint32_t first_vertex, std::uint32_t first_index)
	{
		const auto vertex_count{ vertices.size() - first_vertex };

		std::vector<structures::vec3_s> tangents(vertex_count);
		std::vector<structures::vec3_s> bitangents(vertex_count);

		for (auto index{ first_index }; index + 2u < indices.size(); index += 3u)
		{
			const auto& v0{ vertices[indices[index]] };
			const auto& v1{ vertices[indices[index + 1u]] };
			const auto& v2{ vertices[indices[index + 2u]] };
			const auto edge1{ v1.position - v0.position };
			const auto edge2{ v2.position - v0.position };
			const auto du1{ v1.uv.x - v0.uv.x };
			const auto dv1{ v1.uv.y - v0.uv.y };
			const auto du2{ v2.uv.x - v0.uv.x };
			const auto dv2{ v2.uv.y - v0.uv.y };

			if (const auto determinant{ du1 * dv2 - du2 * dv1 }; std::fabs(determinant) > 1e-12f)
			{
				const auto tangent{ (edge1 * dv2 - edge2 * dv1) / determinant };
				const auto bitangent{ (edge2 * du1 - edge1 * du2) / determinant };

				for (auto corner{ 0u }; corner < 3u; corner++)
				{
					if (indices[index + corner] >= first_vertex)
					{
						tangents[indices[index + corner] - first_vertex] += tangent;
						bitangents[indices[index + corner] - first_vertex] += bitangent;
					}
				}
			}
		}

		for (auto index{ 0u }; index < vertex_count; index++)
		{
			auto& vertex{ vertices[first_vertex + index] };

			auto tangent{ mathematics.normalize(tangents[index] - vertex.normal * mathematics.dot(vertex.normal, tangents[index])) };

			if (mathematics.length_squared(tangent) < 0.5f)
			{
				tangent = mathematics.any_perpendicular(vertex.normal);
			}

			const auto handedness{ mathematics.dot(mathematics.cross(vertex.normal, tangent), bitangents[index]) < 0.0f ? -1.0f : 1.0f };

			vertex.tangent = { tangent.x, tangent.y, tangent.z, handedness };
		}
	}
	/*
	//=====================================================================================
	*/
	void builder_c::transform(std::uint32_t first_vertex, const structures::mat4_s& matrix)
	{
		for (auto index{ first_vertex }; index < vertices.size(); index++)
		{
			auto& vertex{ vertices[index] };

			const auto tangent{ mathematics.normalize(mathematics.transform_vector(vertex.tangent.xyz(), matrix)) };

			vertex.position = mathematics.transform_point(vertex.position, matrix);
			vertex.normal = mathematics.normalize(mathematics.transform_vector(vertex.normal, matrix));
			vertex.tangent = { tangent.x, tangent.y, tangent.z, vertex.tangent.w };
		}
	}
	/*
	//=====================================================================================
	*/
	void builder_c::bounds(structures::vec3_s& minimum, structures::vec3_s& maximum)
	{
		minimum = { FLT_MAX, FLT_MAX, FLT_MAX };
		maximum = { -FLT_MAX, -FLT_MAX, -FLT_MAX };

		for (const auto& vertex : vertices)
		{
			minimum = mathematics.minimum(minimum, vertex.position);
			maximum = mathematics.maximum(maximum, vertex.position);
		}
	}
	/*
	//=====================================================================================
	*/
	void builder_c::build_clusters(std::float_t cell_size, std::vector<structures::draw_range_s>& ranges)
	{
		const auto triangle_count{ indices.size() / 3u };

		std::vector<std::pair<std::uint64_t, std::uint32_t>> keys(triangle_count);

		for (auto triangle{ 0u }; triangle < triangle_count; triangle++)
		{
			const auto centroid{ (vertices[indices[triangle * 3u]].position + vertices[indices[triangle * 3u + 1u]].position + vertices[indices[triangle * 3u + 2u]].position) / 3.0f };
			const auto cx{ static_cast<std::int64_t>(std::floor(centroid.x / cell_size)) + 32768 };
			const auto cy{ static_cast<std::int64_t>(std::floor(centroid.y / (cell_size * 2.0f))) + 32768 };
			const auto cz{ static_cast<std::int64_t>(std::floor(centroid.z / cell_size)) + 32768 };
			const auto triangle_material{ vertices[indices[triangle * 3u]].material };
			const auto alpha{ triangle_material < materials.gpu_materials.size() && (materials.gpu_materials[triangle_material].flags & structures::material_flag_alpha_test) };

			keys[triangle] = { static_cast<std::uint64_t>((cx << 40) | (cy << 20) | cz) | (alpha ? (1ull << 62u) : 0ull), triangle };
		}

		std::stable_sort(keys.begin(), keys.end(), [](const auto& a, const auto& b) { return a.first < b.first; });

		std::vector<std::uint32_t> sorted(indices.size());

		ranges.clear();

		for (auto index{ 0u }; index < triangle_count; index++)
		{
			for (auto corner{ 0u }; corner < 3u; corner++)
			{
				sorted[index * 3u + corner] = indices[keys[index].second * 3u + corner];
			}

			if (ranges.empty() || keys[index].first != keys[index - 1u].first)
			{
				ranges.push_back({ index * 3u, 0u, { FLT_MAX, FLT_MAX, FLT_MAX }, { -FLT_MAX, -FLT_MAX, -FLT_MAX }, (keys[index].first >> 62u) != 0u });
			}

			auto& range{ ranges.back() };

			range.index_count += 3u;

			for (auto corner{ 0u }; corner < 3u; corner++)
			{
				range.bounds_min = mathematics.minimum(range.bounds_min, vertices[sorted[index * 3u + corner]].position);
				range.bounds_max = mathematics.maximum(range.bounds_max, vertices[sorted[index * 3u + corner]].position);
			}
		}

		indices = std::move(sorted);
	}
	/*
	//=====================================================================================
	*/
	bool builder_c::upload(structures::mesh_s& mesh)
	{
		functions::release(mesh.vertex_buffer);
		functions::release(mesh.index_buffer);

		if (vertices.size() && indices.size())
		{
			mesh.vertex_buffer = gpu.create_buffer(static_cast<std::uint32_t>(vertices.size() * sizeof(structures::vertex_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, vertices.data(), 0u, 0u);
			mesh.index_buffer = gpu.create_buffer(static_cast<std::uint32_t>(indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, indices.data(), 0u, 0u);
			mesh.vertex_count = static_cast<std::uint32_t>(vertices.size());
			mesh.index_count = static_cast<std::uint32_t>(indices.size());

			bounds(mesh.bounds_min, mesh.bounds_max);

			return mesh.vertex_buffer && mesh.index_buffer;
		}

		return false;
	}
}

//=====================================================================================
