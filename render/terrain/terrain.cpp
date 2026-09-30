
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	terrain_c terrain;

	bool terrain_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, 0u, D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "INSTANCE", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, 0u, D3D11_INPUT_PER_INSTANCE_DATA, 1u }
		};

		vertex_shader = gpu.create_vertex_shader("terrain_vs", elements, 2u, &layout);
		shadow_vertex_shader = gpu.create_vertex_shader("terrain_shadow_vs", elements, 2u, &shadow_layout);
		pixel_shader = gpu.create_pixel_shader("terrain_ps");

		std::vector<structures::vec2_s> grid;
		std::vector<std::uint32_t> indices;

		for (auto row{ 0u }; row <= terrain_patch_cells; row++)
		{
			for (auto column{ 0u }; column <= terrain_patch_cells; column++)
			{
				grid.push_back({ static_cast<std::float_t>(column), static_cast<std::float_t>(row) });
			}
		}

		for (auto row{ 0u }; row < terrain_patch_cells; row++)
		{
			for (auto column{ 0u }; column < terrain_patch_cells; column++)
			{
				const auto a{ row * (terrain_patch_cells + 1u) + column };
				const auto b{ a + 1u };
				const auto c{ a + terrain_patch_cells + 1u };
				const auto d{ c + 1u };

				indices.insert(indices.end(), { a, c, b, b, c, d });
			}
		}

		index_count = static_cast<std::uint32_t>(indices.size());
		vertex_buffer = gpu.create_buffer(static_cast<std::uint32_t>(grid.size() * sizeof(structures::vec2_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, grid.data(), 0u, 0u);
		index_buffer = gpu.create_buffer(static_cast<std::uint32_t>(indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, indices.data(), 0u, 0u);
		instance_buffer = gpu.create_buffer(terrain_maximum_patches * sizeof(structures::vec4_s), D3D11_USAGE_DYNAMIC, D3D11_BIND_VERTEX_BUFFER, D3D11_CPU_ACCESS_WRITE, nullptr, 0u, 0u);
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::terrain_constants_s));

		return vertex_shader && shadow_vertex_shader && pixel_shader && layout && shadow_layout && vertex_buffer && index_buffer && instance_buffer && constant_buffer;
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::destroy()
	{
		unload();

		functions::release(vertex_buffer);
		functions::release(index_buffer);
		functions::release(instance_buffer);
		functions::release(constant_buffer);
		functions::release(layout);
		functions::release(shadow_layout);
		functions::release(vertex_shader);
		functions::release(shadow_vertex_shader);
		functions::release(pixel_shader);
	}
	/*
	//=====================================================================================
	*/
	bool terrain_c::load()
	{
		unload();

		if (const auto info{ pak.find("terrain_info") }; info && info->size >= sizeof(header) && pak.find("terrain_height"))
		{
			std::memcpy(&header, pak.data(info), sizeof(header));

			const auto biome_entry{ pak.find("terrain_biome") };
			const auto ground_entry{ pak.find("terrain_ground") };

			heights = reinterpret_cast<const std::float_t*>(pak.data(pak.find("terrain_height")));
			biome_data = biome_entry && biome_entry->size >= static_cast<std::uint64_t>(biome_size) * biome_size ? pak.data(biome_entry) : nullptr;
			ground_data = ground_entry && ground_entry->size >= static_cast<std::uint64_t>(ground_size) * ground_size ? pak.data(ground_entry) : nullptr;
			height_view = pak.create_texture("terrain_height", 0u, false, false);
			shading_view = pak.create_texture("terrain_shading", 0u, false, false);
			grass_view = pak.create_texture("terrain_grass", 0u, false, false);

			auto painted{ true };

			for (auto splat{ 0u }; splat < terrain_splat_count; splat++)
			{
				char name[32]{};

				std::snprintf(name, sizeof(name), "terrain_splat%u", splat);

				splat_views[splat] = pak.create_texture(name, 0u, false, false);

				painted = painted && splat_views[splat];
			}

			bounds.assign(terrain_lod_levels, {});

			for (auto level{ 0u }; level < terrain_lod_levels; level++)
			{
				const auto count{ (header.resolution - 1u) / (terrain_patch_cells << level) };

				bounds[level].assign(static_cast<std::size_t>(count) * count, { FLT_MAX, -FLT_MAX });

				for (auto z{ 0u }; z < count; z++)
				{
					for (auto x{ 0u }; x < count; x++)
					{
						auto& entry{ bounds[level][static_cast<std::size_t>(z) * count + x] };

						if (level == 0u)
						{
							for (auto j{ 0u }; j <= terrain_patch_cells; j++)
							{
								for (auto i{ 0u }; i <= terrain_patch_cells; i++)
								{
									const auto value{ sample(static_cast<std::int32_t>(x * terrain_patch_cells + i), static_cast<std::int32_t>(z * terrain_patch_cells + j)) };

									entry = { std::min(entry.x, value), std::max(entry.y, value) };
								}
							}
						}

						else
						{
							for (auto child{ 0u }; child < 4u; child++)
							{
								const auto& lower{ bounds[level - 1u][static_cast<std::size_t>(z * 2u + (child >> 1u)) * (count * 2u) + x * 2u + (child & 1u)] };

								entry = { std::min(entry.x, lower.x), std::max(entry.y, lower.y) };
							}
						}
					}
				}
			}

			constants.params = { header.origin, header.world_size, 1.0f / header.world_size, static_cast<std::float_t>(header.resolution) };

			for (auto level{ 0u }; level < terrain_lod_levels; level++)
			{
				constants.morph[level] = { range(level) * terrain_morph_start, 1.0f / (range(level) * (1.0f - terrain_morph_start)), 0.0f, 0.0f };
			}

			for (auto layer{ 0u }; layer < terrain_layer_count; layer++)
			{
				constants.layers[layer] = structures::material_terrain_grass + layer;
			}

			enabled = heights && biome_data && ground_data && ((height_view && shading_view && grass_view && painted) || gpu.device == nullptr);

			grass_mask.assign(static_cast<std::size_t>(header.texture_size) * header.texture_size, 0u);

			logger.write("terrain: %ux%u heights %.1f..%.1f m, %s", header.resolution, header.resolution, header.minimum_height, header.maximum_height, enabled ? "ready" : "incomplete");
		}

		return enabled;
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::unload()
	{
		functions::release(height_view);
		functions::release(shading_view);
		functions::release(grass_view);
		functions::release(mask_view);

		for (auto& view : splat_views)
		{
			functions::release(view);
		}

		grass_mask.clear();

		heights = nullptr;
		biome_data = nullptr;
		ground_data = nullptr;
		enabled = false;

		bounds.clear();
		instances.clear();
	}
	/*
	//=====================================================================================
	*/
	std::float_t terrain_c::sample(std::int32_t x, std::int32_t z)
	{
		const auto limit{ static_cast<std::int32_t>(header.resolution) - 1 };

		return heights[static_cast<std::size_t>(std::clamp(z, 0, limit)) * header.resolution + std::clamp(x, 0, limit)];
	}
	/*
	//=====================================================================================
	*/
	std::float_t terrain_c::height(std::float_t x, std::float_t z)
	{
		if (enabled)
		{
			const auto fx{ x - header.origin };
			const auto fz{ z - header.origin };
			const auto ix{ static_cast<std::int32_t>(std::floor(fx)) };
			const auto iz{ static_cast<std::int32_t>(std::floor(fz)) };
			const auto tx{ fx - static_cast<std::float_t>(ix) };
			const auto tz{ fz - static_cast<std::float_t>(iz) };

			return mathematics.lerp(mathematics.lerp(sample(ix, iz), sample(ix + 1, iz), tx), mathematics.lerp(sample(ix, iz + 1), sample(ix + 1, iz + 1), tx), tz);
		}

		return 0.0f;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s terrain_c::normal(std::float_t x, std::float_t z)
	{
		return mathematics.normalize({ height(x - 1.0f, z) - height(x + 1.0f, z), 2.0f, height(x, z - 1.0f) - height(x, z + 1.0f) });
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t terrain_c::ground(std::float_t x, std::float_t z)
	{
		if (enabled && ground_data)
		{
			const auto limit{ static_cast<std::int32_t>(ground_size) - 1 };
			const auto tx{ std::clamp(static_cast<std::int32_t>((x - header.origin) / ground_cell), 0, limit) };
			const auto tz{ std::clamp(static_cast<std::int32_t>((z - header.origin) / ground_cell), 0, limit) };

			return ground_data[static_cast<std::size_t>(tz) * ground_size + tx];
		}

		return structures::layer_grass;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t terrain_c::biome(std::float_t x, std::float_t z)
	{
		if (enabled && biome_data)
		{
			const auto limit{ static_cast<std::int32_t>(biome_size) - 1 };
			const auto tx{ std::clamp(static_cast<std::int32_t>((x - header.origin) / biome_cell), 0, limit) };
			const auto tz{ std::clamp(static_cast<std::int32_t>((z - header.origin) / biome_cell), 0, limit) };

			return std::min<std::uint32_t>(biome_data[static_cast<std::size_t>(tz) * biome_size + tx], structures::biome_count - 1u);
		}

		return structures::biome_meadow;
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::mask_rectangle(structures::vec3_s center, std::float_t half_x, std::float_t half_z, std::float_t yaw)
	{
		if (enabled && grass_mask.size() == static_cast<std::size_t>(header.texture_size) * header.texture_size)
		{
			const auto axis_x{ structures::vec3_s{ std::cos(yaw), 0.0f, -std::sin(yaw) } };
			const auto axis_z{ structures::vec3_s{ std::sin(yaw), 0.0f, std::cos(yaw) } };
			const auto reach{ std::sqrt(half_x * half_x + half_z * half_z) + 1.0f };
			const auto limit{ static_cast<std::int32_t>(header.texture_size) - 1 };
			const auto first_x{ std::clamp(static_cast<std::int32_t>(center.x - reach - header.origin), 0, limit) };
			const auto last_x{ std::clamp(static_cast<std::int32_t>(center.x + reach - header.origin), 0, limit) };
			const auto first_z{ std::clamp(static_cast<std::int32_t>(center.z - reach - header.origin), 0, limit) };
			const auto last_z{ std::clamp(static_cast<std::int32_t>(center.z + reach - header.origin), 0, limit) };

			for (auto tz{ first_z }; tz <= last_z; tz++)
			{
				for (auto tx{ first_x }; tx <= last_x; tx++)
				{
					const structures::vec3_s offset{ header.origin + static_cast<std::float_t>(tx) + 0.5f - center.x, 0.0f, header.origin + static_cast<std::float_t>(tz) + 0.5f - center.z };
					const auto inside{ std::min(half_x + 0.5f - std::fabs(mathematics.dot(offset, axis_x)), half_z + 0.5f - std::fabs(mathematics.dot(offset, axis_z))) };

					if (inside > 0.0f)
					{
						auto& texel{ grass_mask[static_cast<std::size_t>(tz) * header.texture_size + tx] };

						texel = std::max(texel, static_cast<std::uint8_t>(std::min(inside, 1.0f) * 255.0f));
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool terrain_c::upload_mask()
	{
		functions::release(mask_view);

		if (grass_mask.size() && gpu.device)
		{
			D3D11_TEXTURE2D_DESC description{};

			description.Width = header.texture_size;
			description.Height = header.texture_size;
			description.MipLevels = 1u;
			description.ArraySize = 1u;
			description.Format = DXGI_FORMAT_R8_UNORM;
			description.SampleDesc.Count = 1u;
			description.Usage = D3D11_USAGE_IMMUTABLE;
			description.BindFlags = D3D11_BIND_SHADER_RESOURCE;

			const D3D11_SUBRESOURCE_DATA data{ grass_mask.data(), header.texture_size, 0u };

			ID3D11Texture2D* texture{ nullptr };

			if (SUCCEEDED(gpu.device->CreateTexture2D(&description, &data, &texture)))
			{
				gpu.device->CreateShaderResourceView(texture, nullptr, &mask_view);

				functions::release(texture);
			}
		}

		return mask_view != nullptr;
	}
	/*
	//=====================================================================================
	*/
	std::float_t terrain_c::range(std::uint32_t level)
	{
		return terrain_lod_base_range * static_cast<std::float_t>(1u << level);
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::node_box(std::uint32_t x, std::uint32_t z, std::uint32_t level, structures::vec3_s& minimum, structures::vec3_s& maximum)
	{
		const auto count{ (header.resolution - 1u) / (terrain_patch_cells << level) };
		const auto size{ static_cast<std::float_t>(terrain_patch_cells << level) };
		const auto& entry{ bounds[level][static_cast<std::size_t>(z) * count + x] };

		minimum = { header.origin + static_cast<std::float_t>(x) * size, entry.x, header.origin + static_cast<std::float_t>(z) * size };
		maximum = { minimum.x + size, entry.y, minimum.z + size };
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::select(const structures::vec4_s* planes, std::uint32_t plane_count)
	{
		instances.clear();

		if (enabled)
		{
			select_node(0u, 0u, terrain_lod_levels - 1u, planes, plane_count);
		}
	}
	/*
	//=====================================================================================
	*/
	bool terrain_c::select_node(std::uint32_t x, std::uint32_t z, std::uint32_t level, const structures::vec4_s* planes, std::uint32_t plane_count)
	{
		structures::vec3_s minimum{}, maximum{};

		node_box(x, z, level, minimum, maximum);

		const auto distance{ mathematics.length(mathematics.maximum(mathematics.maximum(minimum - camera, camera - maximum), { 0.0f, 0.0f, 0.0f })) };

		if (distance <= range(level))
		{
			if (mathematics.box_visible(planes, plane_count, minimum, maximum))
			{
				if (level == 0u || distance > range(level - 1u))
				{
					add(x, z, level, planes, plane_count);
				}

				else
				{
					for (auto child{ 0u }; child < 4u; child++)
					{
						if (select_node(x * 2u + (child & 1u), z * 2u + (child >> 1u), level - 1u, planes, plane_count) == false)
						{
							add(x * 2u + (child & 1u), z * 2u + (child >> 1u), level - 1u, planes, plane_count);
						}
					}
				}
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::add(std::uint32_t x, std::uint32_t z, std::uint32_t level, const structures::vec4_s* planes, std::uint32_t plane_count)
	{
		structures::vec3_s minimum{}, maximum{};

		node_box(x, z, level, minimum, maximum);

		if (instances.size() < terrain_maximum_patches && mathematics.box_visible(planes, plane_count, minimum, maximum))
		{
			instances.push_back({ minimum.x, minimum.z, (maximum.x - minimum.x) / static_cast<std::float_t>(terrain_patch_cells), static_cast<std::float_t>(level) });
		}
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::draw(bool shadow_pass)
	{
		if (enabled && instances.size())
		{
			const UINT strides[2] = { sizeof(structures::vec2_s), sizeof(structures::vec4_s) };
			const UINT offsets[2] = { 0u, 0u };

			ID3D11Buffer* buffers[2] = { vertex_buffer, instance_buffer };
			ID3D11ShaderResourceView* unbound{ nullptr };

			constants.camera = { camera.x, camera.y, camera.z, 0.0f };

			gpu.update_buffer(instance_buffer, instances.data(), static_cast<std::uint32_t>(instances.size() * sizeof(structures::vec4_s)));
			gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

			gpu.context->IASetVertexBuffers(0u, 2u, buffers, strides, offsets);
			gpu.context->IASetIndexBuffer(index_buffer, DXGI_FORMAT_R32_UINT, 0u);
			gpu.context->IASetInputLayout(shadow_pass ? shadow_layout : layout);
			gpu.context->VSSetShader(shadow_pass ? shadow_vertex_shader : vertex_shader, nullptr, 0u);
			gpu.context->VSSetShaderResources(terrain_height_slot, 1u, &height_view);
			gpu.context->VSSetSamplers(1u, 1u, &gpu.sampler_linear_clamp);
			gpu.context->VSSetConstantBuffers(3u, 1u, &constant_buffer);

			if (shadow_pass == false)
			{
				ID3D11ShaderResourceView* views[1u + terrain_splat_count] = { shading_view, splat_views[0], splat_views[1], splat_views[2], splat_views[3] };

				gpu.context->PSSetShader(pixel_shader, nullptr, 0u);
				gpu.context->PSSetShaderResources(5u, 1u + terrain_splat_count, views);
				gpu.context->PSSetSamplers(1u, 1u, &gpu.sampler_linear_clamp);
				gpu.context->PSSetConstantBuffers(3u, 1u, &constant_buffer);
			}

			gpu.context->DrawIndexedInstanced(index_count, static_cast<UINT>(instances.size()), 0u, 0, 0u);

			gpu.context->VSSetShaderResources(terrain_height_slot, 1u, &unbound);
		}
	}
	/*
	//=====================================================================================
	*/
	void terrain_c::clip(structures::vec3_s start, structures::vec3_s end, structures::vec3_s extents, structures::trace_s& result)
	{
		const auto minimum{ mathematics.minimum(start, end) - extents - structures::vec3_s{ 0.01f, 0.01f, 0.01f } };
		const auto maximum{ mathematics.maximum(start, end) + extents + structures::vec3_s{ 0.01f, 0.01f, 0.01f } };
		const auto limit{ static_cast<std::int32_t>(header.resolution) - 2 };
		const auto x0{ std::clamp(static_cast<std::int32_t>(std::floor(minimum.x - header.origin)), 0, limit) };
		const auto x1{ std::clamp(static_cast<std::int32_t>(std::floor(maximum.x - header.origin)), 0, limit) };
		const auto z0{ std::clamp(static_cast<std::int32_t>(std::floor(minimum.z - header.origin)), 0, limit) };
		const auto z1{ std::clamp(static_cast<std::int32_t>(std::floor(maximum.z - header.origin)), 0, limit) };

		structures::plane_s planes[terrain_clip_planes]{};

		for (auto z{ z0 }; z <= z1; z++)
		{
			for (auto x{ x0 }; x <= x1; x++)
			{
				const structures::vec3_s corners[4] = { { header.origin + static_cast<std::float_t>(x), sample(x, z), header.origin + static_cast<std::float_t>(z) }, { header.origin + static_cast<std::float_t>(x + 1), sample(x + 1, z), header.origin + static_cast<std::float_t>(z) }, { header.origin + static_cast<std::float_t>(x), sample(x, z + 1), header.origin + static_cast<std::float_t>(z + 1) }, { header.origin + static_cast<std::float_t>(x + 1), sample(x + 1, z + 1), header.origin + static_cast<std::float_t>(z + 1) } };
				const auto top{ std::max(std::max(corners[0].y, corners[1].y), std::max(corners[2].y, corners[3].y)) };

				if (minimum.y <= top)
				{
					const std::uint32_t triangles[2][3] = { { 0u, 2u, 1u }, { 1u, 2u, 3u } };

					for (const auto& triangle : triangles)
					{
						const auto& a{ corners[triangle[0]] };
						const auto& b{ corners[triangle[1]] };
						const auto& c{ corners[triangle[2]] };
						const auto low{ std::min(std::min(a.y, b.y), c.y) };
						const auto high{ std::max(std::max(a.y, b.y), c.y) };
						const auto up{ mathematics.normalize(mathematics.cross(b - a, c - a)) };
						const auto face{ up.y < 0.0f ? -up : up };

						planes[0] = { face, mathematics.dot(face, a) };

						for (auto edge{ 0u }; edge < 3u; edge++)
						{
							const auto& from{ corners[triangle[edge]] };
							const auto& to{ corners[triangle[(edge + 1u) % 3u]] };
							const auto& other{ corners[triangle[(edge + 2u) % 3u]] };
							const auto side{ mathematics.normalize(structures::vec3_s{ to.z - from.z, 0.0f, from.x - to.x }) };
							const auto outward{ mathematics.dot(side, other - from) > 0.0f ? -side : side };

							planes[1u + edge] = { outward, mathematics.dot(outward, from) };
						}

						planes[4] = { { 0.0f, -1.0f, 0.0f }, -(low - 2.0f) };
						planes[5] = { { 0.0f, 1.0f, 0.0f }, high };
						planes[6] = { { -1.0f, 0.0f, 0.0f }, -std::min(std::min(a.x, b.x), c.x) };
						planes[7] = { { 1.0f, 0.0f, 0.0f }, std::max(std::max(a.x, b.x), c.x) };
						planes[8] = { { 0.0f, 0.0f, -1.0f }, -std::min(std::min(a.z, b.z), c.z) };
						planes[9] = { { 0.0f, 0.0f, 1.0f }, std::max(std::max(a.z, b.z), c.z) };

						auto count{ 10u };

						for (auto edge{ 0u }; edge < 3u; edge++)
						{
							const auto direction{ corners[triangle[(edge + 1u) % 3u]] - corners[triangle[edge]] };
							const structures::vec3_s crossed[2] = { { 0.0f, direction.z, -direction.y }, { direction.y, -direction.x, 0.0f } };

							for (const auto& axis : crossed)
							{
								if (std::fabs(axis.y) > 0.0001f && (std::fabs(axis.x) > 0.0001f || std::fabs(axis.z) > 0.0001f))
								{
									const auto bevel{ mathematics.normalize(axis.y < 0.0f ? -axis : axis) };

									planes[count++] = { bevel, std::max(std::max(mathematics.dot(bevel, a), mathematics.dot(bevel, b)), mathematics.dot(bevel, c)) };
								}
							}
						}

						world.clip_planes(planes, count, -1, structures::surface_grass, start, end, extents, result);
					}
				}
			}
		}
	}
}

//=====================================================================================
