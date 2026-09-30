
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	probes_c probes;

	bool probes_c::bake(structures::vec3_s bounds_min, structures::vec3_s bounds_max, const std::vector<structures::light_s>& lights, const char* map_name)
	{
		destroy();

		origin = bounds_min;
		spacing = probe_spacing;
		count_x = static_cast<std::uint32_t>(std::floor((bounds_max.x - bounds_min.x) / spacing)) + 1u;
		count_y = static_cast<std::uint32_t>(std::floor((bounds_max.y - bounds_min.y) / spacing)) + 1u;
		count_z = static_cast<std::uint32_t>(std::floor((bounds_max.z - bounds_min.z) / spacing)) + 1u;
		bake_lights = lights;

		const auto total{ count_x * count_y * count_z };

		albedo.resize(materials.gpu_materials.size());
		emissive.resize(materials.gpu_materials.size());

		for (auto material{ 0u }; material < materials.gpu_materials.size(); material++)
		{
			const auto average{ materials.average_albedo(material) };

			albedo[material] = { std::min(average.x, 0.9f), std::min(average.y, 0.9f), std::min(average.z, 0.9f) };
			emissive[material] = materials.gpu_materials[material].emissive * 0.04f;
		}

		directions.resize(probe_rays);

		for (auto ray{ 0u }; ray < probe_rays; ray++)
		{
			const auto y{ 1.0f - (static_cast<std::float_t>(ray) + 0.5f) / static_cast<std::float_t>(probe_rays) * 2.0f };
			const auto radius{ std::sqrt(std::max(0.0f, 1.0f - y * y)) };
			const auto angle{ static_cast<std::float_t>(ray) * 2.39996323f };

			directions[ray] = { std::cos(angle) * radius, y, std::sin(angle) * radius };
		}

		const auto hash{ compute_hash(map_name) };
		const auto cache_directory{ functions::executable_directory() + "cache" };
		const auto cache_path{ cache_directory + "\\" + map_name + ".gi" };

		CreateDirectoryA(cache_directory.c_str(), nullptr);

		if (load_cache(cache_path.c_str(), hash))
		{
			logger.write("probes: loaded %u probes from cache", total);
		}

		else
		{
			const auto start{ platform.time() };

			tracer.build(builder.vertices, builder.indices);

			coefficients.assign(static_cast<std::size_t>(total) * 3u, {});
			previous.assign(static_cast<std::size_t>(total) * 3u, {});
			state.assign(static_cast<std::size_t>(total) * 2u, 0u);

			for (auto pass{ 0u }; pass < probe_bounces; pass++)
			{
				jobs.parallel_for(total, [&](std::uint32_t index) { bake_probe(index, pass); });

				previous = coefficients;
			}

			save_cache(cache_path.c_str(), hash);

			logger.write("probes: baked %ux%ux%u (%u probes, %u rays) in %.2f s", count_x, count_y, count_z, total, probe_rays, platform.time() - start);
		}

		upload();

		enabled = views[0] != nullptr;

		return enabled;
	}
	/*
	//=====================================================================================
	*/
	void probes_c::bake_probe(std::uint32_t index, std::uint32_t pass)
	{
		const auto x{ index % count_x };
		const auto y{ (index / count_x) % count_y };
		const auto z{ index / (count_x * count_y) };
		const auto position{ origin + structures::vec3_s{ static_cast<std::float_t>(x), static_cast<std::float_t>(y), static_cast<std::float_t>(z) } * spacing };

		structures::vec3_s sums[4]{};

		auto backfaces{ 0u };
		auto escaped{ 0u };

		for (const auto& direction : directions)
		{
			structures::ray_hit_s hit{};

			auto radiance{ structures::vec3_s{} };

			if (tracer.intersect(position, direction, 600.0f, hit))
			{
				if (hit.backface)
				{
					backfaces++;
				}

				else
				{
					const auto& triangle{ tracer.triangles[hit.triangle] };

					radiance = shade_hit(position + direction * hit.distance, triangle.normal, triangle.material, pass);
				}
			}

			else
			{
				escaped++;

				radiance = sky_radiance(direction);
			}

			sums[0] += radiance * 0.282095f;
			sums[1] += radiance * (0.488603f * direction.y);
			sums[2] += radiance * (0.488603f * direction.z);
			sums[3] += radiance * (0.488603f * direction.x);
		}

		const auto scale{ 4.0f * pi / static_cast<std::float_t>(directions.size()) };

		coefficients[static_cast<std::size_t>(index) * 3u + 0u] = { sums[0].x * scale, sums[1].x * scale, sums[2].x * scale, sums[3].x * scale };
		coefficients[static_cast<std::size_t>(index) * 3u + 1u] = { sums[0].y * scale, sums[1].y * scale, sums[2].y * scale, sums[3].y * scale };
		coefficients[static_cast<std::size_t>(index) * 3u + 2u] = { sums[0].z * scale, sums[1].z * scale, sums[2].z * scale, sums[3].z * scale };

		state[static_cast<std::size_t>(index) * 2u] = backfaces < directions.size() / 6u ? 255u : 0u;
		state[static_cast<std::size_t>(index) * 2u + 1u] = static_cast<std::uint8_t>(std::min(255.0f, static_cast<std::float_t>(escaped) / static_cast<std::float_t>(directions.size()) * 255.0f + 0.5f));
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s probes_c::shade_hit(structures::vec3_s position, structures::vec3_s normal, std::uint32_t material, std::uint32_t pass)
	{
		const auto surface{ material < albedo.size() ? albedo[material] : structures::vec3_s{ 0.3f, 0.3f, 0.3f } };
		const auto lift{ position + normal * 0.02f };

		structures::vec3_s irradiance{};

		if (const auto facing{ mathematics.dot(normal, sky.sun_direction) }; facing > 0.0f && tracer.occluded(lift, sky.sun_direction, 1000.0f) == false)
		{
			irradiance += sky.sun_color * (sky.sun_intensity * facing);
		}

		for (const auto& light : bake_lights)
		{
			auto offset{ light.position - position };

			if (const auto distance_squared{ mathematics.length_squared(offset) }; distance_squared < light.radius * light.radius)
			{
				const auto distance{ std::sqrt(distance_squared) };

				offset = offset / std::max(distance, 0.0001f);

				if (const auto facing{ mathematics.dot(normal, offset) }; facing > 0.0f)
				{
					const auto ratio{ distance / light.radius };
					const auto window{ std::max(0.0f, 1.0f - ratio * ratio * ratio * ratio) };

					auto attenuation{ window * window / std::max(distance_squared, 0.01f) };

					if (light.spot_cosine > -0.5f)
					{
						attenuation *= mathematics.smoothstep(light.spot_cosine, std::min(light.spot_cosine + 0.1f, 0.999f), mathematics.dot(-offset, light.direction));
					}

					if (attenuation * (light.color.x + light.color.y + light.color.z) > 0.002f && tracer.occluded(lift, offset, distance - 0.05f) == false)
					{
						irradiance += light.color * (attenuation * facing);
					}
				}
			}
		}

		if (pass > 0u)
		{
			irradiance += sample_irradiance(position + normal * 0.25f, normal);
		}

		return surface * irradiance * (1.0f / pi) + (material < emissive.size() ? emissive[material] : structures::vec3_s{});
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s probes_c::sample_irradiance(structures::vec3_s position, structures::vec3_s normal)
	{
		const auto grid{ (position - origin) / spacing };
		const auto base_x{ std::clamp(static_cast<std::int32_t>(std::floor(grid.x)), 0, static_cast<std::int32_t>(count_x) - 2) };
		const auto base_y{ std::clamp(static_cast<std::int32_t>(std::floor(grid.y)), 0, static_cast<std::int32_t>(count_y) - 2) };
		const auto base_z{ std::clamp(static_cast<std::int32_t>(std::floor(grid.z)), 0, static_cast<std::int32_t>(count_z) - 2) };
		const auto fx{ mathematics.saturate(grid.x - static_cast<std::float_t>(base_x)) };
		const auto fy{ mathematics.saturate(grid.y - static_cast<std::float_t>(base_y)) };
		const auto fz{ mathematics.saturate(grid.z - static_cast<std::float_t>(base_z)) };

		structures::vec4_s sum[3]{};

		auto weight_sum{ 0.0f };

		for (auto corner{ 0u }; corner < 8u; corner++)
		{
			const auto cx{ base_x + static_cast<std::int32_t>(corner & 1u) };
			const auto cy{ base_y + static_cast<std::int32_t>((corner >> 1u) & 1u) };
			const auto cz{ base_z + static_cast<std::int32_t>((corner >> 2u) & 1u) };
			const auto index{ (static_cast<std::size_t>(cz) * count_y + static_cast<std::size_t>(cy)) * count_x + static_cast<std::size_t>(cx) };

			if (state[index * 2u])
			{
				const auto probe_position{ origin + structures::vec3_s{ static_cast<std::float_t>(cx), static_cast<std::float_t>(cy), static_cast<std::float_t>(cz) } * spacing };
				const auto toward{ mathematics.normalize(probe_position - position) };
				const auto facing{ (mathematics.dot(toward, normal) + 1.0f) * 0.5f };
				const auto trilinear{ ((corner & 1u) ? fx : 1.0f - fx) * (((corner >> 1u) & 1u) ? fy : 1.0f - fy) * (((corner >> 2u) & 1u) ? fz : 1.0f - fz) };
				const auto weight{ trilinear * (facing * facing + 0.05f) };

				for (auto channel{ 0u }; channel < 3u; channel++)
				{
					sum[channel] += previous[index * 3u + channel] * weight;
				}

				weight_sum += weight;
			}
		}

		structures::vec3_s result{};

		if (weight_sum > 0.0001f)
		{
			for (auto channel{ 0u }; channel < 3u; channel++)
			{
				const auto c{ sum[channel] / weight_sum };

				result[channel] = std::max(0.0f, pi * 0.282095f * c.x + 2.094395f * 0.488603f * (c.y * normal.y + c.z * normal.z + c.w * normal.x));
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s probes_c::sky_radiance(structures::vec3_s direction)
	{
		const auto s{ std::sin(-sky.rotation) };
		const auto c{ std::cos(-sky.rotation) };
		const structures::vec3_s d{ direction.x * c + direction.z * s, direction.y, -direction.x * s + direction.z * c };
		const std::float_t basis[sky_sh_coefficients] = { 0.282095f, 0.488603f * d.y, 0.488603f * d.z, 0.488603f * d.x, 1.092548f * d.x * d.y, 1.092548f * d.y * d.z, 0.315392f * (3.0f * d.z * d.z - 1.0f), 1.092548f * d.x * d.z, 0.546274f * (d.x * d.x - d.y * d.y) };

		structures::vec3_s result{};

		for (auto coefficient{ 0u }; coefficient < sky_sh_coefficients; coefficient++)
		{
			result += sky.base_sh[coefficient].xyz() * basis[coefficient];
		}

		return mathematics.maximum(result * sky.intensity, { 0.0f, 0.0f, 0.0f });
	}
	/*
	//=====================================================================================
	*/
	std::uint64_t probes_c::compute_hash(const char* map_name)
	{
		auto value{ functions::hash(map_name) ^ (static_cast<std::uint64_t>(probe_cache_version) << 32u) };

		const auto mix = [&](const void* data, std::size_t size)
			{
				for (auto index{ 0u }; index < size; index++)
				{
					value = (value ^ static_cast<const std::uint8_t*>(data)[index]) * 0x100000001B3ull;
				}
			};

		for (auto index{ 0u }; index < builder.vertices.size(); index += 7u)
		{
			mix(&builder.vertices[index].position, sizeof(structures::vec3_s));
			mix(&builder.vertices[index].material, sizeof(std::uint32_t));
		}

		const auto sizes{ std::array<std::size_t, 2>{ builder.vertices.size(), builder.indices.size() } };

		mix(sizes.data(), sizeof(std::size_t) * 2u);
		mix(albedo.data(), albedo.size() * sizeof(structures::vec3_s));
		mix(emissive.data(), emissive.size() * sizeof(structures::vec3_s));
		mix(bake_lights.data(), bake_lights.size() * sizeof(structures::light_s));
		mix(&sky.sun_direction, sizeof(structures::vec3_s));
		mix(&sky.sun_color, sizeof(structures::vec3_s));
		mix(&sky.sun_intensity, sizeof(std::float_t));
		mix(&sky.intensity, sizeof(std::float_t));
		mix(&sky.rotation, sizeof(std::float_t));
		mix(sky.base_sh, sizeof(sky.base_sh));
		mix(&origin, sizeof(origin));
		mix(&count_x, sizeof(count_x));
		mix(&count_y, sizeof(count_y));
		mix(&count_z, sizeof(count_z));

		return value;
	}
	/*
	//=====================================================================================
	*/
	bool probes_c::load_cache(const char* path, std::uint64_t hash)
	{
		auto result{ false };

		if (auto file{ std::fopen(path, "rb") }; file)
		{
			structures::probe_cache_header_s header{};

			if (std::fread(&header, sizeof(header), 1u, file) == 1u && header.version == probe_cache_version && header.hash == hash && header.count_x == count_x && header.count_y == count_y && header.count_z == count_z)
			{
				const auto total{ static_cast<std::size_t>(count_x) * count_y * count_z };

				coefficients.resize(total * 3u);
				state.resize(total * 2u);

				result = std::fread(coefficients.data(), sizeof(structures::vec4_s), coefficients.size(), file) == coefficients.size() && std::fread(state.data(), 1u, state.size(), file) == state.size();

				previous = coefficients;
			}

			std::fclose(file);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void probes_c::save_cache(const char* path, std::uint64_t hash)
	{
		if (auto file{ std::fopen(path, "wb") }; file)
		{
			const structures::probe_cache_header_s header{ probe_cache_version, count_x, count_y, count_z, hash, origin, spacing };

			std::fwrite(&header, sizeof(header), 1u, file);
			std::fwrite(coefficients.data(), sizeof(structures::vec4_s), coefficients.size(), file);
			std::fwrite(state.data(), 1u, state.size(), file);

			std::fclose(file);
		}
	}
	/*
	//=====================================================================================
	*/
	void probes_c::upload()
	{
		const auto total{ static_cast<std::size_t>(count_x) * count_y * count_z };

		std::vector<structures::vec4_s> channel(total);

		for (auto index{ 0u }; index < 4u; index++)
		{
			D3D11_TEXTURE3D_DESC description{};

			description.Width = count_x;
			description.Height = count_y;
			description.Depth = count_z;
			description.MipLevels = 1u;
			description.Format = index < 3u ? DXGI_FORMAT_R32G32B32A32_FLOAT : DXGI_FORMAT_R8G8_UNORM;
			description.Usage = D3D11_USAGE_IMMUTABLE;
			description.BindFlags = D3D11_BIND_SHADER_RESOURCE;

			D3D11_SUBRESOURCE_DATA initial{};

			if (index < 3u)
			{
				for (auto probe{ 0u }; probe < total; probe++)
				{
					channel[probe] = coefficients[probe * 3u + index];
				}

				initial = { channel.data(), count_x * static_cast<UINT>(sizeof(structures::vec4_s)), count_x * count_y * static_cast<UINT>(sizeof(structures::vec4_s)) };
			}

			else
			{
				initial = { state.data(), count_x * 2u, count_x * count_y * 2u };
			}

			ID3D11Texture3D* texture{ nullptr };

			if (SUCCEEDED(gpu.device->CreateTexture3D(&description, &initial, &texture)))
			{
				gpu.device->CreateShaderResourceView(texture, nullptr, &views[index]);

				functions::release(texture);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void probes_c::destroy()
	{
		for (auto& view : views)
		{
			functions::release(view);
		}

		enabled = false;
	}
}

//=====================================================================================
