
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_terrain_c baker_terrain;

	bool baker_terrain_c::bake(const std::string& cache_path, const std::string& preview_path, bool use_cache)
	{
		const auto start{ GetTickCount64() };

		if (use_cache && load_cache(cache_path))
		{
			logger.write("baker: terrain heights loaded from cache");
		}

		else
		{
			shape();

			erode();

			refine();

			save_cache(cache_path);
		}

		settle();

		grade();

		shade();

		classify();

		paint();

		std::vector<std::uint8_t> height_bytes(heights.size() * sizeof(std::float_t));

		std::memcpy(height_bytes.data(), heights.data(), height_bytes.size());

		add_texture("terrain_height", DXGI_FORMAT_R32_FLOAT, terrain_resolution, height_bytes, false);
		add_texture("terrain_shading", DXGI_FORMAT_R8G8B8A8_UNORM, terrain_texture_size, shading, true);
		add_texture("terrain_grass", DXGI_FORMAT_R8G8B8A8_UNORM, ground_size, control, false);

		for (auto splat{ 0u }; splat < terrain_splat_count; splat++)
		{
			char name[32]{};

			std::snprintf(name, sizeof(name), "terrain_splat%u", splat);

			add_compressed(name, terrain_texture_size, splats[splat]);
		}

		add_blob("terrain_biome", biomes);
		add_blob("terrain_ground", ground);

		structures::terrain_header_s header{ terrain_resolution, terrain_texture_size, terrain_size, terrain_origin, *std::min_element(heights.begin(), heights.end()), *std::max_element(heights.begin(), heights.end()), sea_level, baker::terrain_seed };

		baker::pak_item_s info{};

		std::snprintf(info.entry.name, sizeof(info.entry.name), "%s", "terrain_info");

		info.entry.type = structures::pak_type_blob;

		baker_models.append(info, &header, sizeof(header));

		items.push_back(std::move(info));

		write_routes();

		water_normals();

		preview(preview_path);

		preview_biomes(preview_path.substr(0u, preview_path.rfind('.')) + "_biomes.png");

		logger.write("baker: terrain %ux%u heights %.1f..%.1f m in %.1f s", terrain_resolution, terrain_resolution, header.minimum_height, header.maximum_height, static_cast<std::double_t>(GetTickCount64() - start) / 1000.0);

		return true;
	}
	/*
	//=====================================================================================
	*/
	bool baker_terrain_c::load_cache(const std::string& path)
	{
		auto result{ false };

		if (auto file{ std::fopen(path.c_str(), "rb") }; file)
		{
			std::uint32_t header[3]{};

			heights.resize(static_cast<std::size_t>(terrain_resolution) * terrain_resolution);
			flow.resize(heights.size());

			if (std::fread(header, sizeof(header), 1u, file) == 1u && header[0] == baker::terrain_cache_version && header[1] == baker::terrain_seed && header[2] == terrain_resolution)
			{
				result = std::fread(heights.data(), sizeof(std::float_t), heights.size(), file) == heights.size() && std::fread(flow.data(), sizeof(std::float_t), flow.size(), file) == flow.size();
			}

			std::fclose(file);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::save_cache(const std::string& path)
	{
		if (auto file{ std::fopen(path.c_str(), "wb") }; file)
		{
			const std::uint32_t header[3] = { baker::terrain_cache_version, baker::terrain_seed, terrain_resolution };

			std::fwrite(header, sizeof(header), 1u, file);
			std::fwrite(heights.data(), sizeof(std::float_t), heights.size(), file);
			std::fwrite(flow.data(), sizeof(std::float_t), flow.size(), file);

			std::fclose(file);
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::shape()
	{
		const auto size{ baker::terrain_erosion_size };

		coarse.assign(static_cast<std::size_t>(size) * size, 0.0f);
		coarse_flow.assign(coarse.size(), 0.0f);

		jobs.parallel_for(size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < size; column++)
				{
					const auto x{ terrain_origin + static_cast<std::float_t>(column) * baker::terrain_erosion_cell };
					const auto z{ terrain_origin + static_cast<std::float_t>(row) * baker::terrain_erosion_cell };

					coarse[static_cast<std::size_t>(row) * size + column] = elevation(x, z) / baker::terrain_height_scale;
				}
			});
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::clearance(std::float_t x, std::float_t z)
	{
		auto nearest{ FLT_MAX };

		for (const auto& site : world_sites)
		{
			nearest = std::min(nearest, mathematics.length(structures::vec2_s{ x - site.position.x, z - site.position.y }) - site.outer);
		}

		for (const auto& route : world_routes)
		{
			for (auto index{ 0u }; index + (route.closed ? 0u : 1u) < route.count; index++)
			{
				const auto from{ route.points[index] };
				const auto span{ route.points[(index + 1u) % route.count] - from };
				const auto along{ std::clamp(((x - from.x) * span.x + (z - from.y) * span.y) / std::max(span.x * span.x + span.y * span.y, 0.001f), 0.0f, 1.0f) };

				nearest = std::min(nearest, mathematics.length(structures::vec2_s{ x - from.x - span.x * along, z - from.y - span.y * along }));
			}
		}

		return nearest;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::elevation(std::float_t x, std::float_t z)
	{
		const auto seed{ baker::terrain_seed };
		const auto half{ terrain_size * 0.5f };
		const auto u{ x / half };
		const auto v{ z / half };
		const auto hu{ x / 1024.0f };
		const auto hv{ z / 1024.0f };
		const auto wu{ u + 0.42f * fbm(u * 1.1f + 11.3f, v * 1.1f - 4.1f, 4u, seed + 1u) + 0.1f * fbm(u * 3.2f, v * 3.2f, 3u, seed + 11u) + 0.035f * fbm(hu * 4.0f, hv * 4.0f, 3u, seed + 13u) };
		const auto wv{ v + 0.42f * fbm(u * 1.1f - 7.7f, v * 1.1f + 2.9f, 4u, seed + 2u) + 0.1f * fbm(u * 3.2f + 3.3f, v * 3.2f, 3u, seed + 12u) + 0.035f * fbm(hu * 4.0f + 5.1f, hv * 4.0f - 2.3f, 3u, seed + 14u) };
		const auto radius{ std::sqrt(wu * wu * 1.12f + wv * wv * 0.92f) };
		const auto inland{ (0.74f - radius) * half };
		const auto northern{ mathematics.smoothstep(-0.2f, 0.45f, v + 0.3f * fbm(u * 1.6f, v * 1.6f, 3u, seed + 6u)) };
		const auto bluff{ mathematics.smoothstep(0.0f, 0.16f, fbm(wu * 2.2f - 5.0f, wv * 2.2f + 3.0f, 3u, seed + 18u)) * mathematics.smoothstep(baker::bluff_guard, baker::bluff_guard + 120.0f, clearance(x, z)) };
		const auto crest{ (baker::bluff_height + baker::bluff_northern * northern) * (0.65f + 0.7f * fbm(hu * 5.0f + 9.0f, hv * 5.0f - 3.0f, 3u, seed + 19u)) };
		const auto rampart{ bluff * crest * mathematics.smoothstep(3.0f, 3.0f + baker::bluff_face, inland) * (1.0f - mathematics.smoothstep(baker::bluff_reach * 0.25f, baker::bluff_reach, inland)) };
		const auto cliff{ mathematics.smoothstep(0.1f, 0.34f, fbm(wu * 3.0f + 3.0f, wv * 3.0f - 8.0f, 3u, seed + 4u)) * (1.0f - bluff) };
		const auto plains{ 1.8f * mathematics.smoothstep(0.0f, 22.0f, inland) + 5.0f * mathematics.smoothstep(18.0f, 150.0f, inland) + 7.0f * mathematics.smoothstep(220.0f, 950.0f, inland) };
		const auto rolling{ 0.55f + 0.45f * fbm(u * 1.7f + 4.4f, v * 1.7f - 1.9f, 3u, seed + 17u) };
		const auto hills{ (13.0f + 16.0f * fbm(hu * 3.1f, hv * 3.1f, 5u, seed + 5u) + 7.0f * ridged(hu * 5.5f, hv * 5.5f, 3u, seed + 8u)) * mathematics.smoothstep(40.0f, 380.0f, inland) * rolling };
		const auto mountains{ 190.0f * std::pow(std::max(ridged(u * 3.4f + 0.7f, v * 3.4f - 0.4f, 6u, seed + 7u), 0.0f), 1.7f) * northern * mathematics.smoothstep(200.0f, 820.0f, inland) };
		const auto western{ mathematics.smoothstep(0.0f, 0.4f, -u + 0.3f * fbm(u * 1.4f + 2.0f, v * 1.4f, 3u, seed + 15u)) * (1.0f - northern * 0.7f) };
		const auto highlands{ 120.0f * std::pow(std::max(ridged(hu * 1.6f + 3.1f, hv * 1.6f + 1.7f, 5u, seed + 16u), 0.0f), 1.3f) * western * mathematics.smoothstep(120.0f, 560.0f, inland) };
		const auto land{ plains + std::max(hills, 0.0f) + mountains + highlands + rampart };
		const auto shelf{ inland > 0.0f ? land : -2.6f * mathematics.smoothstep(0.0f, 45.0f, -inland) + inland * 0.075f };
		const auto cliff_top{ 14.0f + 7.0f * fbm(hu * 6.0f, hv * 6.0f, 3u, seed + 9u) };
		const auto cliff_land{ inland > 6.0f ? std::max(land, cliff_top * mathematics.smoothstep(6.0f, 11.0f, inland) + land * 0.6f) : (inland > 0.0f ? 0.6f * mathematics.smoothstep(0.0f, 6.0f, inland) : shelf) };
		const auto height{ mathematics.lerp(shelf, cliff_land, cliff) };

		return std::max(height, baker::terrain_sea_floor + 4.0f * fbm(u * 5.0f, v * 5.0f, 3u, seed + 10u));
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::erode()
	{
		const auto size{ static_cast<std::int32_t>(baker::terrain_erosion_size) };
		const auto radius{ baker::terrain_erosion_radius };

		std::vector<std::pair<std::int32_t, std::float_t>> brush;

		auto brush_total{ 0.0f };

		for (auto dz{ -radius }; dz <= radius; dz++)
		{
			for (auto dx{ -radius }; dx <= radius; dx++)
			{
				if (const auto distance{ std::sqrt(static_cast<std::float_t>(dx * dx + dz * dz)) }; distance < static_cast<std::float_t>(radius))
				{
					brush.push_back({ dz * size + dx, static_cast<std::float_t>(radius) - distance });

					brush_total += static_cast<std::float_t>(radius) - distance;
				}
			}
		}

		for (auto& entry : brush)
		{
			entry.second /= brush_total;
		}

		auto state{ baker::terrain_seed * 747796405u + 2891336453u };

		const auto random = [&]()
			{
				state ^= state << 13u;
				state ^= state >> 17u;
				state ^= state << 5u;

				return static_cast<std::float_t>(state & 0xFFFFFFu) / static_cast<std::float_t>(0x1000000u);
			};

		const auto gradient = [&](std::float_t x, std::float_t z, std::float_t& height, std::float_t& gx, std::float_t& gz)
			{
				const auto cx{ static_cast<std::int32_t>(x) };
				const auto cz{ static_cast<std::int32_t>(z) };
				const auto fx{ x - static_cast<std::float_t>(cx) };
				const auto fz{ z - static_cast<std::float_t>(cz) };
				const auto index{ static_cast<std::size_t>(cz) * size + cx };
				const auto h00{ coarse[index] };
				const auto h10{ coarse[index + 1u] };
				const auto h01{ coarse[index + size] };
				const auto h11{ coarse[index + size + 1u] };

				gx = (h10 - h00) * (1.0f - fz) + (h11 - h01) * fz;
				gz = (h01 - h00) * (1.0f - fx) + (h11 - h10) * fx;
				height = h00 * (1.0f - fx) * (1.0f - fz) + h10 * fx * (1.0f - fz) + h01 * (1.0f - fx) * fz + h11 * fx * fz;
			};

		for (auto droplet{ 0u }; droplet < baker::terrain_erosion_droplets; droplet++)
		{
			auto x{ static_cast<std::float_t>(radius + 1) + random() * static_cast<std::float_t>(size - 2 * radius - 3) };
			auto z{ static_cast<std::float_t>(radius + 1) + random() * static_cast<std::float_t>(size - 2 * radius - 3) };
			auto dx{ 0.0f };
			auto dz{ 0.0f };
			auto speed{ 1.0f };
			auto water{ 1.0f };
			auto sediment{ 0.0f };

			for (auto step{ 0u }; step < baker::terrain_erosion_steps; step++)
			{
				const auto cx{ static_cast<std::int32_t>(x) };
				const auto cz{ static_cast<std::int32_t>(z) };
				const auto fx{ x - static_cast<std::float_t>(cx) };
				const auto fz{ z - static_cast<std::float_t>(cz) };
				const auto index{ static_cast<std::size_t>(cz) * size + cx };

				auto height{ 0.0f }, gx{ 0.0f }, gz{ 0.0f };

				gradient(x, z, height, gx, gz);

				if (height < 0.0f)
				{
					break;
				}

				dx = dx * 0.05f - gx * 0.95f;
				dz = dz * 0.05f - gz * 0.95f;

				const auto length{ std::sqrt(dx * dx + dz * dz) };

				if (length < 1e-9f)
				{
					break;
				}

				dx /= length;
				dz /= length;
				x += dx;
				z += dz;

				if (x < static_cast<std::float_t>(radius + 1) || z < static_cast<std::float_t>(radius + 1) || x > static_cast<std::float_t>(size - radius - 2) || z > static_cast<std::float_t>(size - radius - 2))
				{
					break;
				}

				auto new_height{ 0.0f }, ignore_x{ 0.0f }, ignore_z{ 0.0f };

				gradient(x, z, new_height, ignore_x, ignore_z);

				const auto delta{ new_height - height };
				const auto capacity{ std::max(-delta * speed * water * 4.0f, 0.0001f) };

				coarse_flow[index] += water;

				if (sediment > capacity || delta > 0.0f)
				{
					const auto deposit{ delta > 0.0f ? std::min(delta, sediment) : (sediment - capacity) * 0.3f };

					sediment -= deposit;

					coarse[index] += deposit * (1.0f - fx) * (1.0f - fz);
					coarse[index + 1u] += deposit * fx * (1.0f - fz);
					coarse[index + size] += deposit * (1.0f - fx) * fz;
					coarse[index + size + 1u] += deposit * fx * fz;
				}

				else
				{
					const auto amount{ std::min((capacity - sediment) * 0.3f, -delta) };

					for (const auto& [offset, weight] : brush)
					{
						const auto target{ static_cast<std::size_t>(static_cast<std::int64_t>(index) + offset) };

						coarse[target] -= amount * weight;

						sediment += amount * weight;
					}
				}

				speed = std::sqrt(std::max(0.0f, speed * speed + delta * 4.0f));
				water *= 0.99f;
			}
		}

		std::vector<std::float_t> smoothed{ coarse };

		for (auto row{ 1 }; row < size - 1; row++)
		{
			for (auto column{ 1 }; column < size - 1; column++)
			{
				auto sum{ 0.0f };

				for (auto dz{ -1 }; dz <= 1; dz++)
				{
					for (auto dx{ -1 }; dx <= 1; dx++)
					{
						sum += coarse[static_cast<std::size_t>(row + dz) * size + column + dx];
					}
				}

				smoothed[static_cast<std::size_t>(row) * size + column] = mathematics.lerp(coarse[static_cast<std::size_t>(row) * size + column], sum / 9.0f, 0.5f);
			}
		}

		coarse = std::move(smoothed);
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::refine()
	{
		const auto size{ terrain_resolution };
		const auto scale{ static_cast<std::float_t>(baker::terrain_erosion_size - 1u) / static_cast<std::float_t>(size - 1u) };

		heights.assign(static_cast<std::size_t>(size) * size, 0.0f);
		flow.assign(heights.size(), 0.0f);

		jobs.parallel_for(size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < size; column++)
				{
					const auto x{ terrain_origin + static_cast<std::float_t>(column) };
					const auto z{ terrain_origin + static_cast<std::float_t>(row) };
					const auto base{ bicubic(coarse, baker::terrain_erosion_size, static_cast<std::float_t>(column) * scale, static_cast<std::float_t>(row) * scale) * baker::terrain_height_scale };
					const auto detail{ 0.25f * fbm(x / 9.0f, z / 9.0f, 3u, baker::terrain_seed + 20u) * mathematics.saturate(base / 2.0f) + 0.9f * ridged(x / 38.0f, z / 38.0f, 3u, baker::terrain_seed + 21u) * mathematics.saturate((base - 2.5f) / 6.0f) };

					heights[static_cast<std::size_t>(row) * size + column] = base + detail;
					flow[static_cast<std::size_t>(row) * size + column] = bilinear(coarse_flow, baker::terrain_erosion_size, static_cast<std::float_t>(column) * scale, static_cast<std::float_t>(row) * scale);
				}
			});
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::settle()
	{
		const auto size{ terrain_resolution };

		for (const auto& site : world_sites)
		{
			auto sum{ 0.0 };
			auto samples{ 0u };

			for (auto angle{ 0u }; angle < 32u; angle++)
			{
				for (auto ring{ 0u }; ring <= 4u; ring++)
				{
					const auto distance{ site.inner * static_cast<std::float_t>(ring) / 4.0f };
					const auto theta{ static_cast<std::float_t>(angle) / 32.0f * two_pi };

					sum += height_at(site.position.x + std::sin(theta) * distance, site.position.y + std::cos(theta) * distance);

					samples++;
				}
			}

			const auto target{ std::max(static_cast<std::float_t>(sum / static_cast<std::double_t>(samples)), 3.5f) };
			const auto first_row{ static_cast<std::uint32_t>(std::clamp(site.position.y - site.outer - terrain_origin, 0.0f, static_cast<std::float_t>(size - 1u))) };
			const auto last_row{ static_cast<std::uint32_t>(std::clamp(site.position.y + site.outer - terrain_origin + 1.0f, 0.0f, static_cast<std::float_t>(size - 1u))) };
			const auto first_column{ static_cast<std::uint32_t>(std::clamp(site.position.x - site.outer - terrain_origin, 0.0f, static_cast<std::float_t>(size - 1u))) };
			const auto last_column{ static_cast<std::uint32_t>(std::clamp(site.position.x + site.outer - terrain_origin + 1.0f, 0.0f, static_cast<std::float_t>(size - 1u))) };

			for (auto row{ first_row }; row <= last_row; row++)
			{
				for (auto column{ first_column }; column <= last_column; column++)
				{
					const auto x{ terrain_origin + static_cast<std::float_t>(column) };
					const auto z{ terrain_origin + static_cast<std::float_t>(row) };
					const auto distance{ std::sqrt((x - site.position.x) * (x - site.position.x) + (z - site.position.y) * (z - site.position.y)) };

					if (distance < site.outer)
					{
						auto& height{ heights[static_cast<std::size_t>(row) * size + column] };

						height = mathematics.lerp(height, target + (height - target) * 0.08f, mathematics.smoothstep(site.outer, site.inner, distance));
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::route_path(const structures::world_route_s& route, std::vector<structures::vec2_s>& path)
	{
		const auto count{ static_cast<std::int32_t>(route.count) };
		const auto segments{ route.closed ? count : count - 1 };

		const auto point = [&](std::int32_t index)
			{
				return route.closed ? route.points[(index % count + count) % count] : (index < 0 ? route.points[0] * 2.0f - route.points[1] : (index >= count ? route.points[count - 1] * 2.0f - route.points[count - 2] : route.points[index]));
			};

		path.clear();

		for (auto segment{ 0 }; segment < segments; segment++)
		{
			const auto p0{ point(segment - 1) };
			const auto p1{ point(segment) };
			const auto p2{ point(segment + 1) };
			const auto p3{ point(segment + 2) };
			const auto steps{ std::max(2, static_cast<std::int32_t>(mathematics.length(p2 - p1) / baker::route_spacing)) };

			for (auto step{ 0 }; step < steps; step++)
			{
				const auto t{ static_cast<std::float_t>(step) / static_cast<std::float_t>(steps) };
				const auto t2{ t * t };
				const auto t3{ t2 * t };

				path.push_back((p1 * 2.0f + (p2 - p0) * t + (p0 * 2.0f - p1 * 5.0f + p2 * 4.0f - p3) * t2 + (p1 * 3.0f - p0 - p2 * 3.0f + p3) * t3) * 0.5f);
			}
		}

		if (route.closed == false)
		{
			path.push_back(route.points[count - 1]);
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::grade()
	{
		const auto size{ static_cast<std::int32_t>(terrain_resolution) };

		route_near.assign(heights.size(), 0.0f);
		route_kind.assign(heights.size(), 0u);
		routes.clear();

		std::vector<std::float_t> nearest(heights.size(), FLT_MAX);
		std::vector<std::float_t> target(heights.size(), 0.0f);
		std::vector<std::uint8_t> bedded(heights.size(), 0u);
		std::vector<std::size_t> touched;

		for (const auto& route : world_routes)
		{
			std::vector<structures::vec2_s> path;

			route_path(route, path);

			const auto count{ static_cast<std::int32_t>(path.size()) };
			const auto window{ std::max(1, static_cast<std::int32_t>(route.smoothing / baker::route_spacing * 0.5f)) };
			const auto half{ route.width * 0.5f };
			const auto reach{ half + baker::route_shoulder };
			const auto segments{ route.closed ? count : count - 1 };

			std::vector<std::float_t> level(path.size());
			std::vector<std::float_t> smoothed(path.size());
			std::vector<std::float_t> spans(path.size());
			std::vector<std::float_t> lowest(path.size(), -FLT_MAX);
			std::vector<std::float_t> highest(path.size(), FLT_MAX);
			std::vector<std::uint8_t> pinned(path.size(), 0u);

			for (auto index{ 0 }; index < count; index++)
			{
				level[index] = std::max(height_at(path[index].x, path[index].y), baker::route_floor);
				spans[index] = mathematics.length(path[(index + 1) % count] - path[index]) * route.grade;
			}

			for (auto pass{ 0u }; pass < baker::route_passes; pass++)
			{
				for (auto index{ 0 }; index < count; index++)
				{
					auto sum{ 0.0f };

					for (auto offset{ -window }; offset <= window; offset++)
					{
						sum += level[route.closed ? ((index + offset) % count + count) % count : std::clamp(index + offset, 0, count - 1)];
					}

					smoothed[index] = sum / static_cast<std::float_t>(window * 2 + 1);
				}

				level = smoothed;

				for (auto index{ 1 }; index < count; index++)
				{
					level[index] = std::clamp(level[index], level[index - 1] - spans[index - 1], level[index - 1] + spans[index - 1]);
				}

				for (auto index{ count - 2 }; index >= 0; index--)
				{
					level[index] = std::max(std::clamp(level[index], level[index + 1] - spans[index], level[index + 1] + spans[index]), baker::route_floor);
				}
			}

			for (auto index{ 0 }; index < count; index++)
			{
				for (const auto& other : routes)
				{
					const auto rail{ other.kind == structures::route_rail };
					const auto limit{ other.width * 0.5f + (rail ? crossing_reach : junction_reach) };

					auto best{ limit * limit };

					for (const auto& point : other.points)
					{
						if (const auto gap{ (point.x - path[index].x) * (point.x - path[index].x) + (point.z - path[index].y) * (point.z - path[index].y) }; gap < best && (rail || pinned[index] != 2u))
						{
							best = gap;
							lowest[index] = point.y + (rail ? rail_head - road_lift - crossing_inset : 0.0f);
							pinned[index] = static_cast<std::uint8_t>(rail ? 2u : 1u);
						}
					}
				}

				highest[index] = pinned[index] ? lowest[index] : FLT_MAX;
			}

			for (auto index{ 1 }; index < count; index++)
			{
				const auto step{ mathematics.length(path[index] - path[index - 1]) * crossing_grade };

				lowest[index] = std::max(lowest[index], lowest[index - 1] - step);
				highest[index] = std::min(highest[index], highest[index - 1] + step);
			}

			for (auto index{ count - 2 }; index >= 0; index--)
			{
				const auto step{ mathematics.length(path[index + 1] - path[index]) * crossing_grade };

				lowest[index] = std::max(lowest[index], lowest[index + 1] - step);
				highest[index] = std::min(highest[index], highest[index + 1] + step);
			}

			for (auto index{ 0 }; index < count; index++)
			{
				level[index] = std::min(std::max(level[index], lowest[index]), highest[index]);
			}

			touched.clear();

			for (auto index{ 0 }; index < segments; index++)
			{
				const auto next{ (index + 1) % count };
				const auto& from{ path[index] };
				const auto& to{ path[next] };
				const auto span{ to - from };
				const auto squared{ std::max(span.x * span.x + span.y * span.y, 0.0001f) };
				const auto joined{ pinned[index] != 0u && pinned[next] != 0u };
				const auto first_column{ std::max(static_cast<std::int32_t>(std::min(from.x, to.x) - reach - terrain_origin), 0) };
				const auto last_column{ std::min(static_cast<std::int32_t>(std::max(from.x, to.x) + reach - terrain_origin) + 1, size - 1) };
				const auto first_row{ std::max(static_cast<std::int32_t>(std::min(from.y, to.y) - reach - terrain_origin), 0) };
				const auto last_row{ std::min(static_cast<std::int32_t>(std::max(from.y, to.y) + reach - terrain_origin) + 1, size - 1) };

				for (auto row{ first_row }; row <= last_row; row++)
				{
					for (auto column{ first_column }; column <= last_column; column++)
					{
						const auto cell{ static_cast<std::size_t>(row) * static_cast<std::size_t>(size) + static_cast<std::size_t>(column) };
						const structures::vec2_s spot{ terrain_origin + static_cast<std::float_t>(column), terrain_origin + static_cast<std::float_t>(row) };
						const auto along{ mathematics.saturate(((spot.x - from.x) * span.x + (spot.y - from.y) * span.y) / squared) };

						if (const auto distance{ mathematics.length(spot - (from + span * along)) }; distance < reach && distance < nearest[cell])
						{
							if (nearest[cell] == FLT_MAX)
							{
								touched.push_back(cell);
							}

							nearest[cell] = distance;
							target[cell] = mathematics.lerp(level[index], level[next], along);
							bedded[cell] = static_cast<std::uint8_t>((bedded[cell] & 1u) | (joined ? 2u : 0u));
						}
					}
				}
			}

			for (const auto cell : touched)
			{
				const auto distance{ nearest[cell] };
				const auto margin{ std::max(distance - half, 0.0f) * route.slope };
				const auto closeness{ 1.0f - mathematics.smoothstep(half, half + baker::route_paint_band, distance) };

				if ((bedded[cell] & 1u) == 0u || (bedded[cell] & 2u) != 0u)
				{
					heights[cell] = std::clamp(heights[cell], target[cell] - margin, target[cell] + margin);
				}

				if (closeness > route_near[cell])
				{
					route_near[cell] = closeness;
					route_kind[cell] = static_cast<std::uint8_t>(route.kind + 1u);
				}

				bedded[cell] = static_cast<std::uint8_t>(distance < half ? 1u : (bedded[cell] & 1u));
				nearest[cell] = FLT_MAX;
			}

			structures::route_path_s entry{ route.kind, route.width, route.closed, {} };

			for (auto index{ 0 }; index < count; index++)
			{
				entry.points.push_back({ path[index].x, level[index], path[index].y });
			}

			routes.push_back(std::move(entry));
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::write_routes()
	{
		baker::pak_item_s item{};

		std::snprintf(item.entry.name, sizeof(item.entry.name), "%s", "world_routes");

		item.entry.type = structures::pak_type_blob;

		const auto route_count{ static_cast<std::uint32_t>(routes.size()) };

		baker_models.append(item, &route_count, sizeof(route_count));

		for (const auto& route : routes)
		{
			const auto point_count{ static_cast<std::uint32_t>(route.points.size()) };
			const std::uint32_t flags{ route.closed ? 1u : 0u };

			baker_models.append(item, &route.kind, sizeof(route.kind));
			baker_models.append(item, &flags, sizeof(flags));
			baker_models.append(item, &route.width, sizeof(route.width));
			baker_models.append(item, &point_count, sizeof(point_count));
			baker_models.append(item, route.points.data(), route.points.size() * sizeof(structures::vec3_s));
		}

		items.push_back(std::move(item));

		logger.write("baker: %u routes written", route_count);
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::shade()
	{
		const auto size{ terrain_resolution };

		normals.resize(heights.size());
		occlusion.resize(heights.size());

		jobs.parallel_for(size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < size; column++)
				{
					const auto left{ heights[static_cast<std::size_t>(row) * size + (column ? column - 1u : 0u)] };
					const auto right{ heights[static_cast<std::size_t>(row) * size + std::min(column + 1u, size - 1u)] };
					const auto down{ heights[static_cast<std::size_t>(row ? row - 1u : 0u) * size + column] };
					const auto up{ heights[static_cast<std::size_t>(std::min(row + 1u, size - 1u)) * size + column] };

					normals[static_cast<std::size_t>(row) * size + column] = mathematics.normalize({ left - right, 2.0f, down - up });
				}
			});

		jobs.parallel_for(size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < size; column++)
				{
					const auto x{ static_cast<std::float_t>(column) };
					const auto z{ static_cast<std::float_t>(row) };
					const auto base{ heights[static_cast<std::size_t>(row) * size + column] + 0.3f };

					auto visibility{ 0.0f };

					for (auto direction{ 0u }; direction < baker::terrain_ao_directions; direction++)
					{
						const auto angle{ (static_cast<std::float_t>(direction) + 0.5f) / static_cast<std::float_t>(baker::terrain_ao_directions) * two_pi };
						const auto sx{ std::sin(angle) };
						const auto sz{ std::cos(angle) };

						auto horizon{ 0.0f };
						auto distance{ 1.0f };

						for (auto step{ 0u }; step < baker::terrain_ao_steps; step++)
						{
							const auto px{ std::clamp(x + sx * distance, 0.0f, static_cast<std::float_t>(size - 1u)) };
							const auto pz{ std::clamp(z + sz * distance, 0.0f, static_cast<std::float_t>(size - 1u)) };

							horizon = std::max(horizon, (bilinear(heights, size, px, pz) - base) / distance);

							distance *= 1.36f;
						}

						visibility += 1.0f - horizon / std::sqrt(1.0f + horizon * horizon);
					}

					occlusion[static_cast<std::size_t>(row) * size + column] = visibility / static_cast<std::float_t>(baker::terrain_ao_directions);
				}
			});
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::classify()
	{
		const auto size{ static_cast<std::int32_t>(biome_size) };
		const auto count{ static_cast<std::size_t>(size) * size };
		const auto half{ terrain_size * 0.5f };
		const auto radius{ baker::biome_relief_radius };

		std::vector<std::float_t> level(count), steep(count), damp(count), coast(count), relief(count), exposure(count), moist(count);
		std::vector<std::double_t> table(static_cast<std::size_t>(size + 1) * static_cast<std::size_t>(size + 1), 0.0);
		std::vector<std::double_t> seep(table.size(), 0.0);

		jobs.parallel_for(biome_size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < biome_size; column++)
				{
					const auto cell{ static_cast<std::size_t>(row) * biome_size + column };
					const auto x{ terrain_origin + (static_cast<std::float_t>(column) + 0.5f) * biome_cell };
					const auto z{ terrain_origin + (static_cast<std::float_t>(row) + 0.5f) * biome_cell };
					const auto source{ static_cast<std::size_t>(z - terrain_origin) * terrain_resolution + static_cast<std::size_t>(x - terrain_origin) };

					auto water{ 0.0f };

					for (auto offset{ 0u }; offset < 16u; offset++)
					{
						water = std::max(water, flow[(static_cast<std::size_t>(row) * 4u + offset / 4u) * terrain_resolution + column * 4u + offset % 4u]);
					}

					level[cell] = height_at(x, z);
					steep[cell] = 1.0f - normals[source].y;
					damp[cell] = mathematics.saturate(std::log2(1.0f + water / 80.0f) / 4.0f);
					coast[cell] = level[cell] < sea_level ? 0.0f : 1e6f;
				}
			});

		for (auto pass{ 0 }; pass < 2; pass++)
		{
			const auto sign{ pass ? 1 : -1 };
			const std::int32_t offsets[4][2] = { { sign, 0 }, { 0, sign }, { sign, sign }, { -sign, sign } };
			const std::float_t costs[4] = { 1.0f, 1.0f, 1.41421f, 1.41421f };

			for (auto step{ 0 }; step < size * size; step++)
			{
				const auto index{ pass ? size * size - 1 - step : step };
				const auto row{ index / size };
				const auto column{ index % size };

				for (auto neighbour{ 0u }; neighbour < 4u; neighbour++)
				{
					const auto nx{ column + offsets[neighbour][0] };
					const auto nz{ row + offsets[neighbour][1] };

					if (nx >= 0 && nz >= 0 && nx < size && nz < size)
					{
						coast[index] = std::min(coast[index], coast[static_cast<std::size_t>(nz) * size + nx] + costs[neighbour] * biome_cell);
					}
				}
			}
		}

		for (auto row{ 0 }; row < size; row++)
		{
			for (auto column{ 0 }; column < size; column++)
			{
				table[static_cast<std::size_t>(row + 1) * (size + 1) + column + 1] = static_cast<std::double_t>(level[static_cast<std::size_t>(row) * size + column]) + table[static_cast<std::size_t>(row) * (size + 1) + column + 1] + table[static_cast<std::size_t>(row + 1) * (size + 1) + column] - table[static_cast<std::size_t>(row) * (size + 1) + column];
				seep[static_cast<std::size_t>(row + 1) * (size + 1) + column + 1] = static_cast<std::double_t>(damp[static_cast<std::size_t>(row) * size + column]) + seep[static_cast<std::size_t>(row) * (size + 1) + column + 1] + seep[static_cast<std::size_t>(row + 1) * (size + 1) + column] - seep[static_cast<std::size_t>(row) * (size + 1) + column];
			}
		}

		jobs.parallel_for(biome_size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < biome_size; column++)
				{
					const auto cell{ static_cast<std::size_t>(row) * biome_size + column };
					const auto x{ terrain_origin + (static_cast<std::float_t>(column) + 0.5f) * biome_cell };
					const auto z{ terrain_origin + (static_cast<std::float_t>(row) + 0.5f) * biome_cell };
					const auto x0{ std::max(static_cast<std::int32_t>(column) - radius, 0) };
					const auto z0{ std::max(static_cast<std::int32_t>(row) - radius, 0) };
					const auto x1{ std::min(static_cast<std::int32_t>(column) + radius + 1, size) };
					const auto z1{ std::min(static_cast<std::int32_t>(row) + radius + 1, size) };
					const auto sum{ table[static_cast<std::size_t>(z1) * (size + 1) + x1] - table[static_cast<std::size_t>(z0) * (size + 1) + x1] - table[static_cast<std::size_t>(z1) * (size + 1) + x0] + table[static_cast<std::size_t>(z0) * (size + 1) + x0] };
					const auto soak{ seep[static_cast<std::size_t>(z1) * (size + 1) + x1] - seep[static_cast<std::size_t>(z0) * (size + 1) + x1] - seep[static_cast<std::size_t>(z1) * (size + 1) + x0] + seep[static_cast<std::size_t>(z0) * (size + 1) + x0] };

					auto shelter{ 0.0f };
					auto open{ 1200.0f };

					for (auto step{ 1u }; step <= baker::biome_wind_steps; step++)
					{
						const auto reach{ static_cast<std::float_t>(step) * baker::biome_wind_stride };
						const auto rise{ height_at(x + baker::biome_upwind.x * reach, z + baker::biome_upwind.y * reach) };

						shelter = std::max(shelter, (rise - level[cell]) / reach);
						open = rise < sea_level && open > reach ? reach : open;
					}

					relief[cell] = level[cell] - static_cast<std::float_t>(sum / static_cast<std::double_t>((x1 - x0) * (z1 - z0)));
					moist[cell] = static_cast<std::float_t>(soak / static_cast<std::double_t>((x1 - x0) * (z1 - z0)));
					exposure[cell] = mathematics.saturate(mathematics.saturate(1.0f - shelter * 9.0f) * (0.3f + 0.7f * mathematics.saturate(1.0f - open / 800.0f)) + 0.5f * mathematics.saturate((level[cell] - 60.0f) / 120.0f));
				}
			});

		biomes.assign(count, static_cast<std::uint8_t>(structures::biome_sea));

		jobs.parallel_for(biome_size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < biome_size; column++)
				{
					const auto cell{ static_cast<std::size_t>(row) * biome_size + column };
					const auto x{ terrain_origin + (static_cast<std::float_t>(column) + 0.5f) * biome_cell };
					const auto z{ terrain_origin + (static_cast<std::float_t>(row) + 0.5f) * biome_cell };
					const auto tall{ level[cell] };
					const auto tilt{ steep[cell] };
					const auto edge{ fbm(x / 140.0f, z / 140.0f, 3u, baker::terrain_seed + 50u) };
					const auto drift{ fbm(x / 210.0f, z / 210.0f, 3u, baker::terrain_seed + 51u) };
					const auto region{ fbm(x / 620.0f, z / 620.0f, 3u, baker::terrain_seed + 36u) };
					const auto forest{ 0.5f + 0.3f * fbm(x / 90.0f, z / 90.0f, 4u, baker::terrain_seed + 32u) + 0.42f * region + 0.1f * mathematics.saturate(-relief[cell] / 5.0f) - 0.22f * exposure[cell] - 0.08f * mathematics.saturate(relief[cell] / 6.0f) };
					const auto shoreline{ 1.6f + 1.2f * fbm(x / 25.0f, z / 25.0f, 2u, baker::terrain_seed + 33u) };

					auto farmed{ false };

					for (const auto& site : world_sites)
					{
						const auto gap{ mathematics.length(structures::vec2_s{ x - site.position.x, z - site.position.y }) };

						farmed = farmed || (std::find(std::begin(baker::farm_sites), std::end(baker::farm_sites), static_cast<std::uint32_t>(site.landmark)) != std::end(baker::farm_sites) && gap < std::min(site.outer * 2.1f, baker::biome_farm_reach) * (1.0f + 0.9f * edge + 0.5f * drift) && gap > site.inner * 0.55f);
					}

					const auto wooded{ forest > 0.535f ? (tall > 48.0f + 28.0f * edge || z / half > 0.12f + 0.5f * drift ? structures::biome_pinewood : structures::biome_woodland) : (relief[cell] < -2.5f && tilt > 0.06f && coast[cell] > 120.0f ? structures::biome_woodland : (farmed && tilt < 0.09f && tall > 4.0f ? structures::biome_farmland : structures::biome_meadow)) };
					const auto windswept{ (exposure[cell] > 0.62f && coast[cell] < 300.0f + 160.0f * drift && tall > 7.0f) || (relief[cell] > 3.5f && exposure[cell] > 0.45f && tall > 30.0f) || (coast[cell] < 150.0f + 260.0f * edge && tall > 11.0f && drift > -0.12f) };
					const auto upland{ tall > 148.0f + 44.0f * edge ? structures::biome_summit : (tall > 86.0f + 40.0f * edge ? structures::biome_moor : (windswept ? structures::biome_heath : wooded)) };
					const auto soaked{ (moist[cell] > 0.17f + 0.06f * edge && tilt < 0.05f && tall < 30.0f) || (tall < 4.4f + 1.5f * drift && tilt < 0.022f && coast[cell] > 50.0f && edge > 0.08f) };
					const auto sandy{ coast[cell] < 190.0f + 120.0f * edge && tall < 12.0f && tilt < 0.16f && exposure[cell] > 0.5f };
					const auto inland{ sandy ? structures::biome_dunes : (soaked ? structures::biome_marsh : upland) };
					const auto coastal{ tall < shoreline + 1.4f ? (tilt > 0.14f ? structures::biome_shore : structures::biome_beach) : (coast[cell] < 60.0f && tilt > 0.22f ? structures::biome_shore : inland) };

					biomes[cell] = static_cast<std::uint8_t>(tall < sea_level + 0.05f ? structures::biome_sea : coastal);
				}
			});

		for (auto pass{ 0u }; pass < 2u; pass++)
		{
			const auto before{ biomes };

			jobs.parallel_for(biome_size - 2u, [&](std::uint32_t line)
				{
					const auto row{ line + 1u };

					for (auto column{ 1u }; column + 1u < biome_size; column++)
					{
						std::uint32_t votes[structures::biome_count]{};

						for (auto offset{ 0u }; offset < 9u; offset++)
						{
							votes[before[static_cast<std::size_t>(row + offset / 3u - 1u) * biome_size + column + offset % 3u - 1u]]++;
						}

						const auto own{ before[static_cast<std::size_t>(row) * biome_size + column] };
						const auto winner{ static_cast<std::uint8_t>(std::max_element(std::begin(votes), std::end(votes)) - std::begin(votes)) };

						biomes[static_cast<std::size_t>(row) * biome_size + column] = votes[winner] > votes[own] + 1u && own != structures::biome_sea && own != structures::biome_shore && winner != structures::biome_sea ? winner : own;
					}
				});
		}

		std::uint32_t tally[structures::biome_count]{};

		for (const auto biome : biomes)
		{
			tally[biome]++;
		}

		for (auto biome{ 1u }; biome < structures::biome_count; biome++)
		{
			logger.write("baker: biome %-20s %6.2f km2", biome_names[biome], static_cast<std::float_t>(tally[biome]) * biome_cell * biome_cell / 1000000.0f);
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::blend(std::float_t x, std::float_t z, std::float_t* weights)
	{
		const auto wx{ x + baker::biome_warp * fbm(x / 23.0f, z / 23.0f, 2u, baker::terrain_seed + 60u) + 2.5f * fbm(x / 5.0f, z / 5.0f, 2u, baker::terrain_seed + 62u) };
		const auto wz{ z + baker::biome_warp * fbm(x / 23.0f + 31.0f, z / 23.0f - 17.0f, 2u, baker::terrain_seed + 61u) + 2.5f * fbm(x / 5.0f - 9.0f, z / 5.0f + 4.0f, 2u, baker::terrain_seed + 63u) };
		const auto fx{ std::clamp((wx - terrain_origin) / biome_cell - 0.5f, 0.0f, static_cast<std::float_t>(biome_size) - 1.001f) };
		const auto fz{ std::clamp((wz - terrain_origin) / biome_cell - 0.5f, 0.0f, static_cast<std::float_t>(biome_size) - 1.001f) };
		const auto cx{ static_cast<std::uint32_t>(fx) };
		const auto cz{ static_cast<std::uint32_t>(fz) };
		const auto tx{ fx - static_cast<std::float_t>(cx) };
		const auto tz{ fz - static_cast<std::float_t>(cz) };
		const auto cell{ static_cast<std::size_t>(cz) * biome_size + cx };

		weights[biomes[cell]] += (1.0f - tx) * (1.0f - tz);
		weights[biomes[cell + 1u]] += tx * (1.0f - tz);
		weights[biomes[cell + biome_size]] += (1.0f - tx) * tz;
		weights[biomes[cell + biome_size + 1u]] += tx * tz;
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::paint()
	{
		const auto size{ terrain_texture_size };
		const auto count{ static_cast<std::size_t>(size) * size };

		shading.resize(count * 4u);
		ground.assign(static_cast<std::size_t>(ground_size) * ground_size, 0u);
		control.assign(static_cast<std::size_t>(ground_size) * ground_size * 4u, 0u);

		for (auto& splat : splats)
		{
			splat.assign(count * 4u, 0u);
		}

		jobs.parallel_for(size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < size; column++)
				{
					const auto source{ static_cast<std::size_t>(row) * terrain_resolution + column };
					const auto texel{ static_cast<std::size_t>(row) * size + column };
					const auto x{ terrain_origin + static_cast<std::float_t>(column) + 0.5f };
					const auto z{ terrain_origin + static_cast<std::float_t>(row) + 0.5f };
					const auto height{ (heights[source] + heights[source + 1u] + heights[source + terrain_resolution] + heights[source + terrain_resolution + 1u]) * 0.25f };
					const auto normal{ mathematics.normalize(normals[source] + normals[source + 1u] + normals[source + terrain_resolution] + normals[source + terrain_resolution + 1u]) };
					const auto slope{ 1.0f - normal.y };
					const auto wetness{ mathematics.saturate(std::log2(1.0f + flow[source] / 80.0f) / 4.0f) };
					const auto patches{ 0.5f + 0.5f * fbm(x / 34.0f, z / 34.0f, 4u, baker::terrain_seed + 30u) };
					const auto dryness{ 0.5f + 0.32f * fbm(x / 120.0f, z / 120.0f, 3u, baker::terrain_seed + 31u) + 0.28f * fbm(x / 700.0f, z / 700.0f, 2u, baker::terrain_seed + 37u) };
					const auto shore{ 1.6f + 1.2f * fbm(x / 25.0f, z / 25.0f, 2u, baker::terrain_seed + 33u) };
					const auto macro{ 0.5f + 0.5f * fbm(x / 60.0f, z / 60.0f, 4u, baker::terrain_seed + 34u) };
					const auto grit{ 0.5f + 0.5f * fbm(x / 11.0f, z / 11.0f, 3u, baker::terrain_seed + 35u) };

					std::float_t weight[terrain_layer_count]{};
					std::float_t share[structures::biome_count]{};

					blend(x, z, share);

					auto border{ 0.0f };

					const auto plot{ mathematics.field(x, z, field_spacing, border) };
					const auto crop{ border < field_bank ? static_cast<std::uint32_t>(structures::field_kind_count) : field_kinds[plot % std::size(field_kinds)] };
					const auto cliff{ mathematics.smoothstep(0.34f, 0.5f, slope) };
					const auto rocky{ mathematics.smoothstep(0.16f, 0.3f, slope + (height > 95.0f ? 0.1f : 0.0f)) * (1.0f - cliff) };
					const auto earth{ std::max(0.0f, 1.0f - cliff - rocky) };
					const auto stream{ earth * mathematics.smoothstep(0.55f, 0.95f, wetness) * 0.7f * (1.0f - share[structures::biome_marsh]) * (1.0f - share[structures::biome_sea]) };
					const auto soil{ earth - stream };
					const auto dry{ mathematics.smoothstep(0.4f, 0.65f, dryness) };
					const auto bare{ mathematics.smoothstep(0.7f, 0.86f, patches) * 0.3f };
					const auto tuft{ mathematics.smoothstep(0.45f, 0.7f, patches) };
					const auto glade{ mathematics.smoothstep(0.62f, 0.8f, patches) };
					const auto stony{ mathematics.smoothstep(0.55f, 0.8f, grit) };
					const auto cropped{ mathematics.smoothstep(0.45f, 0.7f, macro) * 0.28f };
					const auto upper{ mathematics.smoothstep(shore + 0.5f, shore + 1.5f, height) * mathematics.smoothstep(0.5f, 0.66f, macro) * 0.8f };
					const auto strand{ soil * (share[structures::biome_sea] + share[structures::biome_beach]) };
					const auto reef{ soil * share[structures::biome_shore] };
					const auto dunes{ soil * share[structures::biome_dunes] };
					const auto fen{ soil * share[structures::biome_marsh] };
					const auto sward{ soil * share[structures::biome_meadow] * (1.0f - bare) };
					const auto farm{ soil * share[structures::biome_farmland] };
					const auto wood{ soil * share[structures::biome_woodland] };
					const auto pines{ soil * share[structures::biome_pinewood] };
					const auto heath{ soil * share[structures::biome_heath] };
					const auto moor{ soil * share[structures::biome_moor] };
					const auto peak{ soil * share[structures::biome_summit] };
					const auto pasture{ crop == structures::field_pasture ? farm : 0.0f };
					const auto hay{ crop == structures::field_hay ? farm : 0.0f };
					const auto ploughed{ crop == structures::field_ploughed ? farm : 0.0f };
					const auto stubble{ crop == structures::field_stubble ? farm : 0.0f };
					const auto bank{ crop == structures::field_kind_count ? farm : 0.0f };

					weight[structures::layer_cliff] = cliff;
					weight[structures::layer_rock] = rocky + reef * 0.45f + heath * (0.12f + 0.18f * stony) + peak * (0.4f + 0.3f * stony);
					weight[structures::layer_gravel] = stream + reef * 0.2f;
					weight[structures::layer_sand] = strand * (1.0f - upper);
					weight[structures::layer_shingle] = strand * upper + reef * 0.35f;
					weight[structures::layer_dune] = dunes * (1.0f - 0.3f * tuft);
					weight[structures::layer_marsh] = fen * (0.45f + 0.4f * tuft) + moor * 0.1f * mathematics.smoothstep(0.3f, 0.8f, wetness);
					weight[structures::layer_dirt] = soil * share[structures::biome_meadow] * bare + wood * 0.04f;
					weight[structures::layer_turf] = sward * cropped + pasture * 0.85f;
					weight[structures::layer_grass] = sward * (1.0f - cropped) * (1.0f - dry) + fen * (0.55f - 0.4f * tuft) + pasture * 0.15f + hay * (1.0f - dry * 0.5f) + bank + wood * (0.16f + 0.25f * glade) + pines * 0.1f;
					weight[structures::layer_dry] = sward * (1.0f - cropped) * dry + dunes * 0.3f * tuft + hay * dry * 0.5f + stubble * 0.75f + heath * 0.22f;
					weight[structures::layer_soil] = ploughed + stubble * 0.25f;
					weight[structures::layer_litter] = wood * (0.8f - 0.25f * glade);
					weight[structures::layer_needles] = pines * 0.9f;
					weight[structures::layer_heath] = heath * (0.66f - 0.18f * stony) + moor * 0.18f + peak * (0.26f - 0.15f * stony);
					weight[structures::layer_moor] = moor * (0.82f - 0.1f * mathematics.smoothstep(0.3f, 0.8f, wetness)) + peak * (0.34f - 0.15f * stony);

					const std::float_t covers[structures::biome_count] = { 0.0f, 0.0f, 0.0f, 0.3f * tuft, 0.85f, 1.0f - bare * 1.5f, crop == structures::field_ploughed ? 0.0f : (crop == structures::field_stubble ? 0.45f : 1.0f), 0.32f, 0.1f, 0.4f, 0.9f, 0.15f };
					const std::float_t droughts[structures::biome_count] = { 0.0f, 0.0f, 0.0f, 0.95f, 0.1f, dry, crop == structures::field_stubble ? 0.62f : (crop == structures::field_hay ? 0.3f + 0.4f * dry : 0.12f), 0.2f, 0.3f, 0.85f, 0.9f, 0.9f };
					const std::float_t statures[structures::biome_count] = { 0.0f, 0.0f, 0.0f, 1.2f, 1.35f, 1.0f - cropped, crop == structures::field_pasture ? 0.5f : (crop == structures::field_stubble ? 0.4f : 1.3f), 0.8f, 0.7f, 0.6f, 0.9f, 0.5f };

					auto lawn{ 0.0f };
					auto parched{ 0.0f };
					auto blades{ 0.0f };

					for (auto biome{ 0u }; biome < structures::biome_count; biome++)
					{
						lawn += share[biome] * covers[biome];
						parched += share[biome] * covers[biome] * droughts[biome];
						blades += share[biome] * covers[biome] * statures[biome];
					}

					parched /= std::max(lawn, 0.001f);
					blades /= std::max(lawn, 0.001f);
					lawn *= soil;

					for (const auto& site : world_sites)
					{
						if (const auto reach{ site.inner * 0.58f }; (x - site.position.x) * (x - site.position.x) + (z - site.position.y) * (z - site.position.y) < reach * reach)
						{
							const auto settle{ mathematics.smoothstep(reach, site.inner * 0.22f, std::sqrt((x - site.position.x) * (x - site.position.x) + (z - site.position.y) * (z - site.position.y))) * (0.55f + 0.45f * mathematics.smoothstep(0.35f, 0.65f, patches)) };

							for (auto& value : weight)
							{
								value *= 1.0f - settle * 0.9f;
							}

							weight[structures::layer_dirt] += settle * (0.35f + 0.65f * grit);
							weight[structures::layer_gravel] += settle * (1.0f - grit) * 0.9f;
							weight[structures::layer_dry] += settle * 0.1f * mathematics.smoothstep(0.62f, 0.8f, grit);

							lawn *= 1.0f - settle * 0.85f;
						}
					}

					if (const auto closeness{ std::max({ route_near[source], route_near[source + 1u], route_near[source + terrain_resolution], route_near[source + terrain_resolution + 1u] }) }; closeness > 0.0f)
					{
						const auto rail{ std::max({ route_kind[source], route_kind[source + 1u], route_kind[source + terrain_resolution], route_kind[source + terrain_resolution + 1u] }) == structures::route_rail + 1u };

						for (auto& value : weight)
						{
							value *= 1.0f - closeness * 0.94f;
						}

						weight[structures::layer_gravel] += closeness * (rail ? 0.85f + 0.15f * grit : 0.45f * (1.0f - grit));
						weight[structures::layer_dirt] += closeness * (rail ? 0.15f * grit : 0.55f + 0.3f * grit);

						lawn *= 1.0f - closeness;
					}

					auto total{ 0.0f };
					auto heaviest{ 0u };

					for (auto layer{ 0u }; layer < terrain_layer_count; layer++)
					{
						total += weight[layer];
						heaviest = weight[layer] > weight[heaviest] ? layer : heaviest;
					}

					for (auto layer{ 0u }; layer < terrain_layer_count; layer++)
					{
						splats[layer / 4u][texel * 4u + layer % 4u] = static_cast<std::uint8_t>(std::clamp(weight[layer] / std::max(total, 1e-4f) * 255.0f + 0.5f, 0.0f, 255.0f));
					}

					if (row % 2u == 0u && column % 2u == 0u)
					{
						const auto cell{ static_cast<std::size_t>(row / 2u) * ground_size + column / 2u };

						ground[cell] = static_cast<std::uint8_t>(heaviest);
						control[cell * 4u + 0u] = static_cast<std::uint8_t>(std::clamp(lawn * 255.0f + 0.5f, 0.0f, 255.0f));
						control[cell * 4u + 1u] = static_cast<std::uint8_t>(std::clamp(parched * 255.0f + 0.5f, 0.0f, 255.0f));
						control[cell * 4u + 2u] = static_cast<std::uint8_t>(std::clamp(blades * 127.5f + 0.5f, 0.0f, 255.0f));
						control[cell * 4u + 3u] = 255u;
					}

					shading[texel * 4u + 0u] = static_cast<std::uint8_t>(std::clamp(normal.x * 127.5f + 127.5f, 0.0f, 255.0f));
					shading[texel * 4u + 1u] = static_cast<std::uint8_t>(std::clamp(normal.z * 127.5f + 127.5f, 0.0f, 255.0f));
					shading[texel * 4u + 2u] = static_cast<std::uint8_t>(std::clamp(occlusion[source] * 255.0f + 0.5f, 0.0f, 255.0f));
					shading[texel * 4u + 3u] = static_cast<std::uint8_t>(std::clamp(macro * 255.0f + 0.5f, 0.0f, 255.0f));
				}
			});
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::add_compressed(const char* name, std::uint32_t size, const std::vector<std::uint8_t>& base)
	{
		baker::pak_item_s item{};

		std::snprintf(item.entry.name, sizeof(item.entry.name), "%s", name);

		item.entry.type = structures::pak_type_texture;
		item.entry.format = static_cast<std::uint32_t>(DXGI_FORMAT_BC7_UNORM);
		item.entry.width = size;
		item.entry.height = size;
		item.entry.layers = 1u;
		item.entry.mips = 0u;

		std::vector<std::uint8_t> level{ base };

		for (auto width{ size }; width >= 1u; width /= 2u)
		{
			const auto blocks{ std::max(1u, (width + 3u) / 4u) };

			std::vector<std::uint8_t> packed(static_cast<std::size_t>(blocks) * blocks * 16u);

			jobs.parallel_for(blocks, [&](std::uint32_t by)
				{
					std::uint8_t block[64]{};

					for (auto bx{ 0u }; bx < blocks; bx++)
					{
						for (auto pixel{ 0u }; pixel < 16u; pixel++)
						{
							const auto px{ std::min(bx * 4u + (pixel & 3u), width - 1u) };
							const auto py{ std::min(by * 4u + (pixel >> 2u), width - 1u) };

							std::memcpy(&block[pixel * 4u], &level[(static_cast<std::size_t>(py) * width + px) * 4u], 4u);
						}

						baker_compressor.bc7_block(block, &packed[(static_cast<std::size_t>(by) * blocks + bx) * 16u]);
					}
				});

			item.data.insert(item.data.end(), packed.begin(), packed.end());

			item.entry.mips++;

			if (width > 1u)
			{
				const auto half{ width / 2u };

				std::vector<std::uint8_t> next(static_cast<std::size_t>(half) * half * 4u);

				for (auto row{ 0u }; row < half; row++)
				{
					for (auto column{ 0u }; column < half; column++)
					{
						for (auto channel{ 0u }; channel < 4u; channel++)
						{
							const auto a{ level[(static_cast<std::size_t>(row * 2u) * width + column * 2u) * 4u + channel] };
							const auto b{ level[(static_cast<std::size_t>(row * 2u) * width + column * 2u + 1u) * 4u + channel] };
							const auto c{ level[(static_cast<std::size_t>(row * 2u + 1u) * width + column * 2u) * 4u + channel] };
							const auto d{ level[(static_cast<std::size_t>(row * 2u + 1u) * width + column * 2u + 1u) * 4u + channel] };

							next[(static_cast<std::size_t>(row) * half + column) * 4u + channel] = static_cast<std::uint8_t>((a + b + c + d + 2u) / 4u);
						}
					}
				}

				level = std::move(next);
			}
		}

		items.push_back(std::move(item));
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::add_blob(const char* name, const std::vector<std::uint8_t>& bytes)
	{
		baker::pak_item_s item{};

		std::snprintf(item.entry.name, sizeof(item.entry.name), "%s", name);

		item.entry.type = structures::pak_type_blob;

		baker_models.append(item, bytes.data(), bytes.size());

		items.push_back(std::move(item));
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::water_normals()
	{
		const auto size{ water_normal_size };
		const auto count{ static_cast<std::size_t>(size) * size };

		std::vector<std::float_t> field(count, 0.0f);
		std::vector<std::uint8_t> bytes(count * 4u);

		auto seed{ baker::terrain_seed * 2654435761u };

		const auto random = [&]()
			{
				seed ^= seed << 13u;
				seed ^= seed >> 17u;
				seed ^= seed << 5u;

				return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
			};

		for (auto wave{ 0u }; wave < 56u; wave++)
		{
			const auto angle{ random() * two_pi };
			const auto radius{ 3.0f + std::pow(random(), 1.6f) * 44.0f };
			const auto kx{ std::round(std::cos(angle) * radius) };
			const auto kz{ std::round(std::sin(angle) * radius) };
			const auto amplitude{ 1.0f / std::pow(std::max(std::sqrt(kx * kx + kz * kz), 1.0f), 1.35f) };
			const auto phase{ random() * two_pi };

			for (auto row{ 0u }; row < size; row++)
			{
				for (auto column{ 0u }; column < size; column++)
				{
					field[static_cast<std::size_t>(row) * size + column] += amplitude * std::sin(two_pi * (kx * static_cast<std::float_t>(column) + kz * static_cast<std::float_t>(row)) / static_cast<std::float_t>(size) + phase);
				}
			}
		}

		for (auto row{ 0u }; row < size; row++)
		{
			for (auto column{ 0u }; column < size; column++)
			{
				const auto left{ field[static_cast<std::size_t>(row) * size + (column + size - 1u) % size] };
				const auto right{ field[static_cast<std::size_t>(row) * size + (column + 1u) % size] };
				const auto down{ field[static_cast<std::size_t>((row + size - 1u) % size) * size + column] };
				const auto up{ field[static_cast<std::size_t>((row + 1u) % size) * size + column] };
				const auto normal{ mathematics.normalize({ (left - right) * 2.2f, 1.0f, (down - up) * 2.2f }) };
				const auto foam{ 0.5f + 0.5f * baker_images.fbm(static_cast<std::float_t>(column) / static_cast<std::float_t>(size) * 8.0f, static_cast<std::float_t>(row) / static_cast<std::float_t>(size) * 8.0f, 8, 4u, 0.55f, baker::terrain_seed + 91u) };
				const auto index{ (static_cast<std::size_t>(row) * size + column) * 4u };

				bytes[index + 0u] = static_cast<std::uint8_t>(std::clamp(normal.x * 127.5f + 127.5f, 0.0f, 255.0f));
				bytes[index + 1u] = static_cast<std::uint8_t>(std::clamp(normal.z * 127.5f + 127.5f, 0.0f, 255.0f));
				bytes[index + 2u] = static_cast<std::uint8_t>(std::clamp(foam * 255.0f, 0.0f, 255.0f));
				bytes[index + 3u] = 255u;
			}
		}

		add_texture("water_normal", DXGI_FORMAT_R8G8B8A8_UNORM, size, bytes, true);
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::add_texture(const char* name, DXGI_FORMAT format, std::uint32_t size, const std::vector<std::uint8_t>& base, bool mips)
	{
		baker::pak_item_s item{};

		std::snprintf(item.entry.name, sizeof(item.entry.name), "%s", name);

		item.entry.type = structures::pak_type_texture;
		item.entry.format = static_cast<std::uint32_t>(format);
		item.entry.width = size;
		item.entry.height = size;
		item.entry.layers = 1u;
		item.entry.mips = 1u;
		item.data = base;

		if (mips)
		{
			std::vector<std::uint8_t> level{ base };

			for (auto width{ size / 2u }; width >= 1u; width /= 2u)
			{
				std::vector<std::uint8_t> next(static_cast<std::size_t>(width) * width * 4u);

				for (auto row{ 0u }; row < width; row++)
				{
					for (auto column{ 0u }; column < width; column++)
					{
						for (auto channel{ 0u }; channel < 4u; channel++)
						{
							const auto a{ level[(static_cast<std::size_t>(row * 2u) * width * 2u + column * 2u) * 4u + channel] };
							const auto b{ level[(static_cast<std::size_t>(row * 2u) * width * 2u + column * 2u + 1u) * 4u + channel] };
							const auto c{ level[(static_cast<std::size_t>(row * 2u + 1u) * width * 2u + column * 2u) * 4u + channel] };
							const auto d{ level[(static_cast<std::size_t>(row * 2u + 1u) * width * 2u + column * 2u + 1u) * 4u + channel] };

							next[(static_cast<std::size_t>(row) * width + column) * 4u + channel] = static_cast<std::uint8_t>((a + b + c + d + 2u) / 4u);
						}
					}
				}

				item.data.insert(item.data.end(), next.begin(), next.end());

				item.entry.mips++;

				level = std::move(next);
			}
		}

		items.push_back(std::move(item));
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::preview_biomes(const std::string& path)
	{
		const auto size{ biome_size };
		const auto light{ mathematics.normalize({ -0.6f, 0.7f, 0.4f }) };

		std::vector<std::uint8_t> rgba(static_cast<std::size_t>(size) * size * 4u);

		for (auto row{ 0u }; row < size; row++)
		{
			for (auto column{ 0u }; column < size; column++)
			{
				const auto cell{ static_cast<std::size_t>(size - 1u - row) * size + column };
				const auto source{ (static_cast<std::size_t>(size - 1u - row) * 4u + 2u) * terrain_resolution + column * 4u + 2u };
				const auto color{ baker::biome_colors[biomes[cell]] * (0.45f + 0.65f * std::max(0.0f, mathematics.dot(normals[source], light))) };

				for (auto channel{ 0u }; channel < 3u; channel++)
				{
					rgba[(static_cast<std::size_t>(row) * size + column) * 4u + channel] = static_cast<std::uint8_t>(std::clamp(std::pow(std::max(color[channel], 0.0f), 1.0f / 2.2f) * 255.0f, 0.0f, 255.0f));
				}

				rgba[(static_cast<std::size_t>(row) * size + column) * 4u + 3u] = 255u;
			}
		}

		baker_images.save_png(path.c_str(), rgba.data(), size, size, nullptr);
	}
	/*
	//=====================================================================================
	*/
	void baker_terrain_c::preview(const std::string& path)
	{
		const auto size{ terrain_texture_size / 2u };
		const auto light{ mathematics.normalize({ -0.6f, 0.7f, 0.4f }) };

		std::vector<std::uint8_t> rgba(static_cast<std::size_t>(size) * size * 4u);

		for (auto row{ 0u }; row < size; row++)
		{
			for (auto column{ 0u }; column < size; column++)
			{
				const auto texel{ static_cast<std::size_t>(size - 1u - row) * 2u * terrain_texture_size + column * 2u };
				const auto source{ static_cast<std::size_t>(size - 1u - row) * 2u * terrain_resolution + column * 2u };
				const auto height{ heights[source] };

				structures::vec3_s color{};

				for (auto layer{ 0u }; layer < terrain_layer_count; layer++)
				{
					color += baker::layer_colors[layer] * (static_cast<std::float_t>(splats[layer / 4u][texel * 4u + layer % 4u]) / 255.0f);
				}

				color = color * (0.35f + 0.75f * std::max(0.0f, mathematics.dot(normals[source], light))) * (0.4f + 0.6f * occlusion[source]);

				if (height < sea_level)
				{
					color = mathematics.lerp(structures::vec3_s{ 0.12f, 0.36f, 0.4f }, structures::vec3_s{ 0.02f, 0.07f, 0.14f }, mathematics.saturate(-height / 22.0f));
				}

				for (auto channel{ 0u }; channel < 3u; channel++)
				{
					rgba[(static_cast<std::size_t>(row) * size + column) * 4u + channel] = static_cast<std::uint8_t>(std::clamp(std::pow(std::max(color[channel], 0.0f), 1.0f / 2.2f) * 255.0f, 0.0f, 255.0f));
				}

				rgba[(static_cast<std::size_t>(row) * size + column) * 4u + 3u] = 255u;
			}
		}

		baker_images.save_png(path.c_str(), rgba.data(), size, size, nullptr);
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::height_at(std::float_t x, std::float_t z)
	{
		return bilinear(heights, terrain_resolution, std::clamp(x - terrain_origin, 0.0f, terrain_size), std::clamp(z - terrain_origin, 0.0f, terrain_size));
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::noise(std::float_t x, std::float_t z, std::uint32_t seed)
	{
		const auto ix{ static_cast<std::int32_t>(std::floor(x)) };
		const auto iz{ static_cast<std::int32_t>(std::floor(z)) };
		const auto fx{ x - std::floor(x) };
		const auto fz{ z - std::floor(z) };

		const auto corner = [&](std::int32_t cx, std::int32_t cz, std::float_t ox, std::float_t oz)
			{
				const auto hash{ mathematics.hash_u32(static_cast<std::uint32_t>(cx) * 73856093u ^ static_cast<std::uint32_t>(cz) * 19349663u ^ seed * 83492791u) };
				const auto angle{ static_cast<std::float_t>(hash & 0xFFFFu) / 65536.0f * two_pi };

				return std::cos(angle) * ox + std::sin(angle) * oz;
			};

		const auto ux{ fx * fx * fx * (fx * (fx * 6.0f - 15.0f) + 10.0f) };
		const auto uz{ fz * fz * fz * (fz * (fz * 6.0f - 15.0f) + 10.0f) };

		return 1.4f * mathematics.lerp(mathematics.lerp(corner(ix, iz, fx, fz), corner(ix + 1, iz, fx - 1.0f, fz), ux), mathematics.lerp(corner(ix, iz + 1, fx, fz - 1.0f), corner(ix + 1, iz + 1, fx - 1.0f, fz - 1.0f), ux), uz);
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::fbm(std::float_t x, std::float_t z, std::uint32_t octaves, std::uint32_t seed)
	{
		auto total{ 0.0f };
		auto amplitude{ 0.5f };
		auto frequency{ 1.0f };

		for (auto octave{ 0u }; octave < octaves; octave++)
		{
			total += noise(x * frequency, z * frequency, seed + octave * 131u) * amplitude;

			amplitude *= 0.5f;
			frequency *= 2.03f;
		}

		return total;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::ridged(std::float_t x, std::float_t z, std::uint32_t octaves, std::uint32_t seed)
	{
		auto total{ 0.0f };
		auto amplitude{ 0.5f };
		auto frequency{ 1.0f };
		auto weight{ 1.0f };

		for (auto octave{ 0u }; octave < octaves; octave++)
		{
			const auto ridge{ 1.0f - std::fabs(noise(x * frequency, z * frequency, seed + octave * 197u)) };
			const auto shaped{ ridge * ridge * weight };

			total += shaped * amplitude;

			weight = mathematics.saturate(shaped * 1.6f);
			amplitude *= 0.5f;
			frequency *= 2.01f;
		}

		return total;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::bilinear(const std::vector<std::float_t>& grid, std::uint32_t size, std::float_t x, std::float_t z)
	{
		const auto cx{ std::min(static_cast<std::uint32_t>(std::max(x, 0.0f)), size - 2u) };
		const auto cz{ std::min(static_cast<std::uint32_t>(std::max(z, 0.0f)), size - 2u) };
		const auto fx{ std::clamp(x - static_cast<std::float_t>(cx), 0.0f, 1.0f) };
		const auto fz{ std::clamp(z - static_cast<std::float_t>(cz), 0.0f, 1.0f) };
		const auto index{ static_cast<std::size_t>(cz) * size + cx };

		return mathematics.lerp(mathematics.lerp(grid[index], grid[index + 1u], fx), mathematics.lerp(grid[index + size], grid[index + size + 1u], fx), fz);
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_terrain_c::bicubic(const std::vector<std::float_t>& grid, std::uint32_t size, std::float_t x, std::float_t z)
	{
		const auto cx{ static_cast<std::int32_t>(std::floor(x)) };
		const auto cz{ static_cast<std::int32_t>(std::floor(z)) };
		const auto fx{ x - static_cast<std::float_t>(cx) };
		const auto fz{ z - static_cast<std::float_t>(cz) };

		const auto fetch = [&](std::int32_t px, std::int32_t pz)
			{
				return grid[static_cast<std::size_t>(std::clamp(pz, 0, static_cast<std::int32_t>(size) - 1)) * size + std::clamp(px, 0, static_cast<std::int32_t>(size) - 1)];
			};

		const auto spline = [](std::float_t a, std::float_t b, std::float_t c, std::float_t d, std::float_t t)
			{
				return b + 0.5f * t * (c - a + t * (2.0f * a - 5.0f * b + 4.0f * c - d + t * (3.0f * (b - c) + d - a)));
			};

		std::float_t rows[4]{};

		for (auto row{ 0 }; row < 4; row++)
		{
			rows[row] = spline(fetch(cx - 1, cz + row - 1), fetch(cx, cz + row - 1), fetch(cx + 1, cz + row - 1), fetch(cx + 2, cz + row - 1), fx);
		}

		return spline(rows[0], rows[1], rows[2], rows[3], fz);
	}
}

//=====================================================================================
