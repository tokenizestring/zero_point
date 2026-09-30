
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	chart_c chart;

	bool chart_c::create()
	{
		destroy();

		const auto started{ platform.time() };

		survey();
		relief();
		forests();
		works();
		furniture();
		compose();

		ready = upload();

		logger.write("chart: %u px at %.2f m/px, origin %.0f %.0f, %zu roads %zu footprints, %s in %.2f s", chart_size, meters, origin.x, origin.y, maps.roads.size(), maps.footprints.size(), ready ? "ready" : "failed", platform.time() - started);

		heights = {};
		coverage = {};
		pixels = {};

		return ready;
	}
	/*
	//=====================================================================================
	*/
	void chart_c::destroy()
	{
		functions::release(view);

		open = false;
		ready = false;
	}
	/*
	//=====================================================================================
	*/
	void chart_c::forget()
	{
		std::fill(std::begin(pins), std::end(pins), structures::chart_pin_s{});

		pin_clock = 0u;
		grave_marked = false;
		was_dead = false;
	}
	/*
	//=====================================================================================
	*/
	void chart_c::update(bool input_enabled)
	{
		if (survival.vitals.dead && was_dead == false)
		{
			grave = { player.state.position.x, player.state.position.z };
			grave_marked = true;
			open = false;
		}

		was_dead = survival.vitals.dead;

		if (ready && input_enabled && platform.tapped(structures::bind_map))
		{
			open = open == false;

			mixer.play_2d(open ? structures::sound_ui_open : structures::sound_ui_close, 0.45f, 0.8f + mixer.random() * 0.1f);
		}

		else if (open && input_enabled && platform.input.pressed[VK_RBUTTON])
		{
			pin(platform.input.mouse_position);
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::pin(structures::vec2_s point)
	{
		const auto area{ frame() };
		const auto scale{ area.w / static_cast<std::float_t>(chart_size) };
		const structures::vec2_s corner{ area.x, area.y };
		const auto spot{ (point - corner) / scale };

		auto nearest{ -1 };
		auto slot{ 0u };

		for (auto index{ 0u }; index < chart_pin_count; index++)
		{
			if (pins[index].stamp && mathematics.length(corner + project(pins[index].position.x, pins[index].position.y) * scale - point) < chart_pin_reach * canvas.scale)
			{
				nearest = static_cast<std::int32_t>(index);
			}

			slot = pins[index].stamp < pins[slot].stamp ? index : slot;
		}

		if (nearest >= 0)
		{
			pins[nearest] = {};

			mixer.play_2d(structures::sound_ui_close, 0.4f, 1.1f + mixer.random() * 0.1f);
		}

		else if (area.contains(point))
		{
			pins[slot] = { { origin.x + spot.x * meters, origin.y - spot.y * meters }, ++pin_clock };

			mixer.play_2d(structures::sound_ui_click, 0.45f, 0.9f + mixer.random() * 0.1f);
		}
	}
	/*
	//=====================================================================================
	*/
	structures::rect_s chart_c::frame()
	{
		const auto size{ std::min(canvas.screen_height * 0.94f, canvas.screen_width * 0.94f) };

		return { (canvas.screen_width - size) * 0.5f, (canvas.screen_height - size) * 0.5f, size, size };
	}
	/*
	//=====================================================================================
	*/
	void chart_c::survey()
	{
		structures::vec2_s low{ FLT_MAX, FLT_MAX };
		structures::vec2_s high{ -FLT_MAX, -FLT_MAX };

		for (auto z{ terrain_origin }; z < terrain_origin + terrain_size; z += 4.0f)
		{
			for (auto x{ terrain_origin }; x < terrain_origin + terrain_size; x += 4.0f)
			{
				if (terrain.height(x, z) > sea_level)
				{
					low = { std::min(low.x, x), std::min(low.y, z) };
					high = { std::max(high.x, x), std::max(high.y, z) };
				}
			}
		}

		const auto found{ high.x > low.x };
		const auto side{ found ? std::min(std::max(high.x - low.x, high.y - low.y) * chart_margin, terrain_size) : terrain_size };
		const structures::vec2_s middle{ found ? (low + high) * 0.5f : structures::vec2_s{ terrain_origin + terrain_size * 0.5f, terrain_origin + terrain_size * 0.5f } };

		meters = side / static_cast<std::float_t>(chart_size);
		origin = { middle.x - side * 0.5f, middle.y + side * 0.5f };

		heights.resize(static_cast<std::size_t>(chart_size) * chart_size);
		coverage.assign(static_cast<std::size_t>(chart_size) * chart_size, 0.0f);

		jobs.parallel_for(chart_size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < chart_size; column++)
				{
					heights[static_cast<std::size_t>(row) * chart_size + column] = terrain.height(origin.x + (static_cast<std::float_t>(column) + 0.5f) * meters, origin.y - (static_cast<std::float_t>(row) + 0.5f) * meters);
				}
			});
	}
	/*
	//=====================================================================================
	*/
	void chart_c::relief()
	{
		const auto size{ static_cast<std::int32_t>(chart_size) };
		const auto light{ mathematics.normalize({ -0.62f, 0.7f, 0.48f }) };

		std::vector<std::float_t> distance(heights.size(), 0.0f);

		for (auto index{ 0u }; index < distance.size(); index++)
		{
			distance[index] = heights[index] > sea_level ? 0.0f : 1.0e6f;
		}

		for (auto y{ 0 }; y < size; y++)
		{
			for (auto x{ 0 }; x < size; x++)
			{
				auto& cell{ distance[static_cast<std::size_t>(y) * size + x] };

				cell = x > 0 ? std::min(cell, distance[static_cast<std::size_t>(y) * size + x - 1] + 1.0f) : cell;
				cell = y > 0 ? std::min(cell, distance[static_cast<std::size_t>(y - 1) * size + x] + 1.0f) : cell;
				cell = x > 0 && y > 0 ? std::min(cell, distance[static_cast<std::size_t>(y - 1) * size + x - 1] + 1.4142f) : cell;
				cell = x + 1 < size && y > 0 ? std::min(cell, distance[static_cast<std::size_t>(y - 1) * size + x + 1] + 1.4142f) : cell;
			}
		}

		for (auto y{ size - 1 }; y >= 0; y--)
		{
			for (auto x{ size - 1 }; x >= 0; x--)
			{
				auto& cell{ distance[static_cast<std::size_t>(y) * size + x] };

				cell = x + 1 < size ? std::min(cell, distance[static_cast<std::size_t>(y) * size + x + 1] + 1.0f) : cell;
				cell = y + 1 < size ? std::min(cell, distance[static_cast<std::size_t>(y + 1) * size + x] + 1.0f) : cell;
				cell = x + 1 < size && y + 1 < size ? std::min(cell, distance[static_cast<std::size_t>(y + 1) * size + x + 1] + 1.4142f) : cell;
				cell = x > 0 && y + 1 < size ? std::min(cell, distance[static_cast<std::size_t>(y + 1) * size + x - 1] + 1.4142f) : cell;
			}
		}

		jobs.parallel_for(chart_size, [&](std::uint32_t row)
			{
				for (auto column{ 0 }; column < size; column++)
				{
					const auto y{ static_cast<std::int32_t>(row) };
					const auto index{ static_cast<std::size_t>(y) * size + column };
					const auto height{ heights[index] };
					const auto gx{ (heights[static_cast<std::size_t>(y) * size + std::min(column + 1, size - 1)] - heights[static_cast<std::size_t>(y) * size + std::max(column - 1, 0)]) * 0.5f };
					const auto gy{ (heights[static_cast<std::size_t>(std::min(y + 1, size - 1)) * size + column] - heights[static_cast<std::size_t>(std::max(y - 1, 0)) * size + column]) * 0.5f };
					const auto slope{ std::max(std::sqrt(gx * gx + gy * gy), 0.0001f) };
					const auto coast{ mathematics.saturate(2.1f - std::fabs(height - sea_level) / slope) * 0.95f };

					auto ink{ coast };

					if (height > sea_level)
					{
						const auto level{ std::round(height / chart_contour_interval) };
						const auto major{ std::fmod(level, 5.0f) == 0.0f };
						const auto gap{ std::fabs(height - level * chart_contour_interval) / slope };
						const auto normal{ mathematics.normalize({ -gx / meters, 1.0f, gy / meters }) };
						const auto darkness{ mathematics.saturate((0.9f - mathematics.dot(normal, light)) * 2.6f) };
						const auto phase{ std::fmod(static_cast<std::float_t>(column - y + 4 * size), 5.0f) / 5.0f };

						ink = level > 0.0f ? std::max(ink, mathematics.saturate((major ? 1.25f : 0.8f) - gap) * (major ? 0.6f : 0.34f)) : ink;
						ink = std::max(ink, mathematics.saturate((darkness * 0.46f - std::fabs(phase - 0.5f)) * 5.0f) * 0.4f);
					}

					else
					{
						for (auto ring{ 0u }; ring < 7u; ring++)
						{
							const auto offset{ 5.0f + static_cast<std::float_t>(ring) * (4.5f + static_cast<std::float_t>(ring) * 1.4f) };

							ink = std::max(ink, mathematics.saturate(1.0f - std::fabs(distance[index] - offset) * 1.25f) * (0.52f - static_cast<std::float_t>(ring) * 0.06f));
						}
					}

					coverage[index] = std::max(coverage[index], ink);
				}
			});
	}
	/*
	//=====================================================================================
	*/
	void chart_c::forests()
	{
		const auto cells{ static_cast<std::int32_t>(chart_size) / chart_forest_cell };

		std::vector<std::uint16_t> pines(static_cast<std::size_t>(cells) * cells, 0u);
		std::vector<std::uint16_t> deads(static_cast<std::size_t>(cells) * cells, 0u);

		for (const auto& instance : foliage.instances)
		{
			const auto model{ instance.species < foliage.species.size() ? foliage.species[instance.species].near_model : nullptr };

			if (model && std::strstr(model->name, "tree_"))
			{
				const auto point{ project(instance.position.x, instance.position.z) };
				const auto cx{ static_cast<std::int32_t>(point.x) / chart_forest_cell };
				const auto cy{ static_cast<std::int32_t>(point.y) / chart_forest_cell };

				if (point.x >= 0.0f && point.y >= 0.0f && cx < cells && cy < cells)
				{
					auto& counter{ std::strstr(model->name, "dead") ? deads[static_cast<std::size_t>(cy) * cells + cx] : pines[static_cast<std::size_t>(cy) * cells + cx] };

					counter++;
				}
			}
		}

		for (auto cy{ 0 }; cy < cells; cy++)
		{
			for (auto cx{ 0 }; cx < cells; cx++)
			{
				const auto cell{ static_cast<std::size_t>(cy) * cells + cx };
				const auto total{ static_cast<std::uint32_t>(pines[cell]) + deads[cell] };
				const auto seed{ static_cast<std::uint32_t>(cell) * 2654435761u };
				const structures::vec2_s center{ (static_cast<std::float_t>(cx) + 0.5f + (mathematics.hash_float(seed) - 0.5f) * 0.6f) * chart_forest_cell, (static_cast<std::float_t>(cy) + 0.5f + (mathematics.hash_float(seed + 1u) - 0.5f) * 0.6f) * chart_forest_cell };
				const auto k{ 0.85f + mathematics.hash_float(seed + 2u) * 0.3f };

				if (total >= 2u && deads[cell] > pines[cell])
				{
					stroke(center + structures::vec2_s{ 0.0f, 4.0f * k }, center + structures::vec2_s{ 0.0f, -1.5f * k }, 0.9f, 0.85f);
					stroke(center + structures::vec2_s{ 0.0f, -1.0f * k }, center + structures::vec2_s{ -2.6f * k, -4.6f * k }, 0.8f, 0.8f);
					stroke(center + structures::vec2_s{ 0.0f, 0.3f * k }, center + structures::vec2_s{ 2.4f * k, -3.6f * k }, 0.8f, 0.8f);
				}

				else if (total >= 2u)
				{
					const structures::vec2_s glyph[3] = { center + structures::vec2_s{ 0.0f, -5.6f * k }, center + structures::vec2_s{ 2.9f * k, 1.9f * k }, center + structures::vec2_s{ -2.9f * k, 1.9f * k } };

					polygon(glyph, 3u, 0.82f);
					stroke(center + structures::vec2_s{ 0.0f, 1.9f * k }, center + structures::vec2_s{ 0.0f, 4.2f * k }, 0.9f, 0.85f);
				}

				else if (total == 1u)
				{
					dab(center, 0.9f, 0.6f);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::works()
	{
		for (const auto& spring : farming.springs)
		{
			const auto center{ project(spring.x, spring.z) };
			const auto radius{ std::max(spring.w / meters, 4.0f) };

			circle(center, radius, 1.4f, 0.9f);

			for (auto ripple{ 0u }; ripple < 3u; ripple++)
			{
				const auto offset{ (static_cast<std::float_t>(ripple) - 1.0f) * radius * 0.45f };

				stroke(center + structures::vec2_s{ -radius * 0.55f, offset }, center + structures::vec2_s{ -radius * 0.1f, offset - 1.2f }, 0.9f, 0.7f);
				stroke(center + structures::vec2_s{ -radius * 0.1f, offset - 1.2f }, center + structures::vec2_s{ radius * 0.5f, offset }, 0.9f, 0.7f);
			}
		}

		for (const auto& road : maps.roads)
		{
			const auto from{ project(road.from.x, road.from.y) };
			const auto to{ project(road.to.x, road.to.y) };
			const auto direction{ mathematics.normalize(to - from) };
			const structures::vec2_s side{ -direction.y * road.width * 0.5f / meters, direction.x * road.width * 0.5f / meters };

			stroke(from + side, to + side, 1.0f, 0.85f);
			stroke(from - side, to - side, 1.0f, 0.85f);
		}

		for (const auto& path : maps.paths)
		{
			for (auto index{ chart_rail_step }; path.kind == structures::route_rail && index < path.points.size(); index += chart_rail_step)
			{
				const auto from{ project(path.points[index - chart_rail_step].x, path.points[index - chart_rail_step].z) };
				const auto to{ project(path.points[index].x, path.points[index].z) };
				const auto direction{ mathematics.normalize(to - from) };
				const structures::vec2_s side{ -direction.y * 2.6f, direction.x * 2.6f };

				stroke(from, to, 1.7f, 0.95f);

				if ((index / chart_rail_step) % 3u == 0u)
				{
					stroke(to - side, to + side, 1.1f, 0.85f);
				}
			}
		}

		for (const auto& footprint : maps.footprints)
		{
			structures::vec2_s corners[4]{};

			for (auto corner{ 0u }; corner < 4u; corner++)
			{
				const auto local{ maps.rotate_yaw({ (corner == 1u || corner == 2u ? 1.0f : -1.0f) * footprint.half.x, 0.0f, (corner >= 2u ? 1.0f : -1.0f) * footprint.half.y }, footprint.yaw) };

				corners[corner] = project(footprint.center.x + local.x, footprint.center.y + local.z);
			}

			polygon(corners, 4u, 0.5f);

			for (auto edge{ 0u }; edge < 4u; edge++)
			{
				stroke(corners[edge], corners[(edge + 1u) % 4u], 1.0f, 0.95f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::furniture()
	{
		const auto size{ static_cast<std::float_t>(chart_size) };
		const auto step{ size / static_cast<std::float_t>(chart_grid_cells) };
		const structures::vec2_s rose{ size - 210.0f, 210.0f };
		const auto segment{ 100.0f / meters };

		for (auto line{ 1u }; line < chart_grid_cells; line++)
		{
			const auto at{ step * static_cast<std::float_t>(line) };

			stroke({ at, 58.0f }, { at, size - 58.0f }, 0.8f, 0.13f);
			stroke({ 58.0f, at }, { size - 58.0f, at }, 0.8f, 0.13f);
		}

		for (const auto& frame : { structures::vec3_s{ 40.0f, 2.8f, 0.92f }, structures::vec3_s{ 53.0f, 1.0f, 0.8f } })
		{
			stroke({ frame.x, frame.x }, { size - frame.x, frame.x }, frame.y, frame.z);
			stroke({ size - frame.x, frame.x }, { size - frame.x, size - frame.x }, frame.y, frame.z);
			stroke({ size - frame.x, size - frame.x }, { frame.x, size - frame.x }, frame.y, frame.z);
			stroke({ frame.x, size - frame.x }, { frame.x, frame.x }, frame.y, frame.z);
		}

		circle(rose, 78.0f, 1.2f, 0.85f);
		circle(rose, 68.0f, 0.8f, 0.7f);

		for (auto point{ 0u }; point < 8u; point++)
		{
			const auto angle{ static_cast<std::float_t>(point) * pi * 0.25f };
			const structures::vec2_s along{ std::sin(angle), -std::cos(angle) };
			const structures::vec2_s across{ -along.y, along.x };
			const auto length{ point % 2u ? 46.0f : 104.0f };
			const auto breadth{ point % 2u ? 7.0f : 12.0f };
			const structures::vec2_s filled[3] = { rose, rose + along * length, rose + across * breadth };

			polygon(filled, 3u, 0.88f);
			stroke(rose - across * breadth, rose + along * length, 1.0f, 0.9f);
			stroke(rose + across * breadth, rose + along * length, 1.0f, 0.9f);
		}

		dab(rose, 4.0f, 0.9f);

		for (auto block{ 0u }; block < 5u; block++)
		{
			const auto left{ 110.0f + segment * static_cast<std::float_t>(block) };
			const structures::vec2_s corners[4] = { { left, size - 132.0f }, { left + segment, size - 132.0f }, { left + segment, size - 122.0f }, { left, size - 122.0f } };

			if (block % 2u == 0u)
			{
				polygon(corners, 4u, 0.88f);
			}

			for (auto edge{ 0u }; edge < 4u; edge++)
			{
				stroke(corners[edge], corners[(edge + 1u) % 4u], 1.0f, 0.9f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::compose()
	{
		const auto size{ static_cast<std::float_t>(chart_size) };

		pixels.resize(heights.size());

		jobs.parallel_for(chart_size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < chart_size; column++)
				{
					const auto index{ static_cast<std::size_t>(row) * chart_size + column };
					const auto x{ static_cast<std::float_t>(column) };
					const auto y{ static_cast<std::float_t>(row) };
					const auto stain{ mathematics.saturate(fractal(x / 380.0f, y / 380.0f, 4u, 11u) * 1.7f - 0.68f) };
					const auto fibre{ fractal(x / 2.5f, y / 42.0f, 3u, 23u) - 0.5f };
					const auto grain{ noise(x * 0.8f, y * 0.8f, 31u) - 0.5f };
					const auto spot{ mathematics.saturate((fractal(x / 7.0f, y / 7.0f, 2u, 53u) - 0.8f) * 8.0f) * 0.35f };
					const auto edge{ std::min(std::min(x, y), std::min(size - 1.0f - x, size - 1.0f - y)) / size };
					const auto burn{ mathematics.saturate(1.0f - edge / 0.05f + (fractal(x / 55.0f, y / 55.0f, 3u, 41u) - 0.5f) * 1.2f) };
					const auto fold{ std::min(std::fabs(x - size * 0.5f), std::fabs(y - size * 0.5f)) };
					const auto crease{ fold < 1.3f ? 0.88f : (fold < 3.5f ? 1.04f : 1.0f) };
					const auto sea{ heights[index] > sea_level ? structures::vec3_s{ 1.0f, 1.0f, 1.0f } : structures::vec3_s{ 0.955f, 0.965f, 0.975f } };
					const auto ink{ mathematics.saturate(coverage[index] * (0.84f + noise(x * 0.3f, y * 0.3f, 61u) * 0.3f)) };

					auto paper{ chart_paper * (1.0f + fibre * 0.06f + grain * 0.035f) * crease };

					paper = { paper.x * sea.x, paper.y * sea.y, paper.z * sea.z };
					paper = mathematics.lerp(paper, structures::vec3_s{ paper.x * 0.8f, paper.y * 0.71f, paper.z * 0.56f }, mathematics.saturate(stain * 0.6f + spot));
					paper = mathematics.lerp(paper, chart_burn, burn * 0.88f);

					const auto color{ mathematics.lerp(paper, chart_ink, ink) };

					pixels[index] = functions::rgba(static_cast<std::uint32_t>(mathematics.saturate(color.x) * 255.0f + 0.5f), static_cast<std::uint32_t>(mathematics.saturate(color.y) * 255.0f + 0.5f), static_cast<std::uint32_t>(mathematics.saturate(color.z) * 255.0f + 0.5f), 255u);
				}
			});
	}
	/*
	//=====================================================================================
	*/
	bool chart_c::upload()
	{
		D3D11_TEXTURE2D_DESC description{};

		description.Width = chart_size;
		description.Height = chart_size;
		description.MipLevels = 0u;
		description.ArraySize = 1u;
		description.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
		description.SampleDesc.Count = 1u;
		description.Usage = D3D11_USAGE_DEFAULT;
		description.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_RENDER_TARGET;
		description.MiscFlags = D3D11_RESOURCE_MISC_GENERATE_MIPS;

		ID3D11Texture2D* texture{ nullptr };

		if (SUCCEEDED(gpu.device->CreateTexture2D(&description, nullptr, &texture)))
		{
			gpu.context->UpdateSubresource(texture, 0u, nullptr, pixels.data(), chart_size * 4u, 0u);

			if (SUCCEEDED(gpu.device->CreateShaderResourceView(texture, nullptr, &view)))
			{
				gpu.context->GenerateMips(view);
			}

			functions::release(texture);
		}

		return view != nullptr;
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s chart_c::project(std::float_t x, std::float_t z)
	{
		return { (x - origin.x) / meters, (origin.y - z) / meters };
	}
	/*
	//=====================================================================================
	*/
	void chart_c::stroke(structures::vec2_s from, structures::vec2_s to, std::float_t width, std::float_t alpha)
	{
		const auto reach{ width * 0.5f + 1.0f };
		const auto delta{ to - from };
		const auto span{ std::max(mathematics.dot(delta, delta), 1.0e-6f) };

		for (auto y{ static_cast<std::int32_t>(std::floor(std::min(from.y, to.y) - reach)) }; y <= static_cast<std::int32_t>(std::ceil(std::max(from.y, to.y) + reach)); y++)
		{
			for (auto x{ static_cast<std::int32_t>(std::floor(std::min(from.x, to.x) - reach)) }; x <= static_cast<std::int32_t>(std::ceil(std::max(from.x, to.x) + reach)); x++)
			{
				const structures::vec2_s point{ static_cast<std::float_t>(x) + 0.5f, static_cast<std::float_t>(y) + 0.5f };
				const auto t{ mathematics.saturate(mathematics.dot(point - from, delta) / span) };

				deposit(x, y, mathematics.saturate(width * 0.5f + 0.5f - mathematics.length(point - (from + delta * t))) * alpha);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::polygon(const structures::vec2_s* corners, std::uint32_t count, std::float_t alpha)
	{
		auto low{ corners[0] };
		auto high{ corners[0] };
		auto area{ 0.0f };

		for (auto index{ 0u }; index < count; index++)
		{
			const auto& a{ corners[index] };
			const auto& b{ corners[(index + 1u) % count] };

			low = { std::min(low.x, a.x), std::min(low.y, a.y) };
			high = { std::max(high.x, a.x), std::max(high.y, a.y) };
			area += a.x * b.y - b.x * a.y;
		}

		const auto orientation{ area >= 0.0f ? 1.0f : -1.0f };

		for (auto y{ static_cast<std::int32_t>(std::floor(low.y - 1.0f)) }; y <= static_cast<std::int32_t>(std::ceil(high.y + 1.0f)); y++)
		{
			for (auto x{ static_cast<std::int32_t>(std::floor(low.x - 1.0f)) }; x <= static_cast<std::int32_t>(std::ceil(high.x + 1.0f)); x++)
			{
				const structures::vec2_s point{ static_cast<std::float_t>(x) + 0.5f, static_cast<std::float_t>(y) + 0.5f };

				auto outside{ -FLT_MAX };

				for (auto index{ 0u }; index < count; index++)
				{
					const auto& a{ corners[index] };
					const auto edge{ mathematics.normalize(corners[(index + 1u) % count] - a) };
					const structures::vec2_s outward{ edge.y * orientation, -edge.x * orientation };

					outside = std::max(outside, mathematics.dot(point - a, outward));
				}

				deposit(x, y, mathematics.saturate(0.5f - outside) * alpha);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::dab(structures::vec2_s center, std::float_t radius, std::float_t alpha)
	{
		for (auto y{ static_cast<std::int32_t>(std::floor(center.y - radius - 1.0f)) }; y <= static_cast<std::int32_t>(std::ceil(center.y + radius + 1.0f)); y++)
		{
			for (auto x{ static_cast<std::int32_t>(std::floor(center.x - radius - 1.0f)) }; x <= static_cast<std::int32_t>(std::ceil(center.x + radius + 1.0f)); x++)
			{
				deposit(x, y, mathematics.saturate(radius + 0.5f - mathematics.length(structures::vec2_s{ static_cast<std::float_t>(x) + 0.5f, static_cast<std::float_t>(y) + 0.5f } - center)) * alpha);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::circle(structures::vec2_s center, std::float_t radius, std::float_t width, std::float_t alpha)
	{
		for (auto y{ static_cast<std::int32_t>(std::floor(center.y - radius - width - 1.0f)) }; y <= static_cast<std::int32_t>(std::ceil(center.y + radius + width + 1.0f)); y++)
		{
			for (auto x{ static_cast<std::int32_t>(std::floor(center.x - radius - width - 1.0f)) }; x <= static_cast<std::int32_t>(std::ceil(center.x + radius + width + 1.0f)); x++)
			{
				const auto gap{ std::fabs(mathematics.length(structures::vec2_s{ static_cast<std::float_t>(x) + 0.5f, static_cast<std::float_t>(y) + 0.5f } - center) - radius) };

				deposit(x, y, mathematics.saturate(width * 0.5f + 0.5f - gap) * alpha);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void chart_c::deposit(std::int32_t x, std::int32_t y, std::float_t alpha)
	{
		if (x >= 0 && y >= 0 && x < static_cast<std::int32_t>(chart_size) && y < static_cast<std::int32_t>(chart_size) && alpha > 0.0f)
		{
			auto& cell{ coverage[static_cast<std::size_t>(y) * chart_size + x] };

			cell = std::max(cell, alpha);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t chart_c::noise(std::float_t x, std::float_t y, std::uint32_t seed)
	{
		const auto ix{ static_cast<std::int32_t>(std::floor(x)) };
		const auto iy{ static_cast<std::int32_t>(std::floor(y)) };
		const auto fx{ x - static_cast<std::float_t>(ix) };
		const auto fy{ y - static_cast<std::float_t>(iy) };
		const auto sx{ fx * fx * (3.0f - 2.0f * fx) };
		const auto sy{ fy * fy * (3.0f - 2.0f * fy) };
		const auto corner = [&](std::int32_t cx, std::int32_t cy)
			{
				return mathematics.hash_float(static_cast<std::uint32_t>(cx) * 73856093u ^ static_cast<std::uint32_t>(cy) * 19349663u ^ seed * 83492791u);
			};

		return mathematics.lerp(mathematics.lerp(corner(ix, iy), corner(ix + 1, iy), sx), mathematics.lerp(corner(ix, iy + 1), corner(ix + 1, iy + 1), sx), sy);
	}
	/*
	//=====================================================================================
	*/
	std::float_t chart_c::fractal(std::float_t x, std::float_t y, std::uint32_t octaves, std::uint32_t seed)
	{
		auto total{ 0.0f };
		auto amplitude{ 1.0f };
		auto weight{ 0.0f };

		for (auto octave{ 0u }; octave < octaves; octave++)
		{
			total += noise(x, y, seed + octave * 1013u) * amplitude;
			weight += amplitude;
			amplitude *= 0.5f;
			x *= 2.03f;
			y *= 2.03f;
		}

		return total / weight;
	}
	/*
	//=====================================================================================
	*/
	void chart_c::triangle(structures::vec2_s a, structures::vec2_s b, structures::vec2_s c, std::uint32_t color)
	{
		const structures::vec4_s params{ static_cast<std::float_t>(structures::canvas_mode_solid), 0.0f, 0.0f, 0.0f };

		const structures::canvas_vertex_s quad[4] =
		{
			{ a, {}, color, params, {} },
			{ b, {}, color, params, {} },
			{ c, {}, color, params, {} },
			{ c, {}, color, params, {} }
		};

		canvas.push(nullptr, quad);
	}
	/*
	//=====================================================================================
	*/
	void chart_c::draw(std::float_t s)
	{
		if (open && ready)
		{
			const auto width{ canvas.screen_width };
			const auto height{ canvas.screen_height };
			const auto area{ frame() };
			const auto size{ area.w };
			const auto scale{ size / static_cast<std::float_t>(chart_size) };
			const auto ink{ functions::rgba(30u, 23u, 17u, 238u) };
			const auto faded{ functions::rgba(30u, 23u, 17u, 170u) };
			const auto blood{ functions::rgba(128u, 28u, 16u, 240u) };
			const auto pen{ functions::rgba(28u, 46u, 92u, 235u) };
			const structures::vec2_s corner{ area.x, area.y };
			const auto step{ static_cast<std::float_t>(chart_size) / static_cast<std::float_t>(chart_grid_cells) * scale };
			const auto here{ corner + project(player.state.position.x, player.state.position.z) * scale };
			const structures::vec2_s facing{ std::sin(player.yaw), -std::cos(player.yaw) };
			const structures::vec2_s across{ -facing.y, facing.x };
			const auto mouse{ platform.input.mouse_position };

			char label[8]{};
			char note[96]{};
			char key[32]{};

			canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(6u, 5u, 4u, 160u));
			canvas.rect({ area.x + 9.0f * s, area.y + 13.0f * s, size, size }, functions::rgba(0u, 0u, 0u, 110u));
			canvas.image(view, area, { 0.0f, 0.0f }, { 1.0f, 1.0f }, functions::rgba(255u, 255u, 255u, 255u));

			canvas.text(structures::font_serif_caps, { area.x + 92.0f * scale, area.y + 118.0f * scale }, 64.0f * scale, ink, "Zero Point", structures::align_left | structures::align_middle);
			canvas.text(structures::font_serif, { area.x + 96.0f * scale, area.y + 176.0f * scale }, 30.0f * scale, faded, "An island, charted by an unsteady hand", structures::align_left | structures::align_middle);
			canvas.text(structures::font_serif_caps, { area.x + (static_cast<std::float_t>(chart_size) - 210.0f) * scale, area.y + 72.0f * scale }, 40.0f * scale, ink, "N", structures::align_center | structures::align_middle);
			canvas.text(structures::font_serif, { area.x + 110.0f * scale, area.y + (static_cast<std::float_t>(chart_size) - 150.0f) * scale }, 26.0f * scale, ink, "0", structures::align_center | structures::align_middle);
			canvas.text(structures::font_serif, { area.x + (110.0f + 500.0f / meters) * scale, area.y + (static_cast<std::float_t>(chart_size) - 150.0f) * scale }, 26.0f * scale, ink, "500 metres", structures::align_center | structures::align_middle);

			for (auto cell{ 0u }; cell < chart_grid_cells; cell++)
			{
				std::snprintf(label, sizeof(label), "%c", static_cast<char>('A' + cell));

				canvas.text(structures::font_serif_caps, { area.x + (static_cast<std::float_t>(cell) + 0.5f) * step, area.y + 30.0f * scale }, 30.0f * scale, faded, label, structures::align_center | structures::align_middle);

				std::snprintf(label, sizeof(label), "%u", cell + 1u);

				canvas.text(structures::font_serif_caps, { area.x + 26.0f * scale, area.y + (static_cast<std::float_t>(cell) + 0.5f) * step }, 30.0f * scale, faded, label, structures::align_center | structures::align_middle);
			}

			for (const auto& landmark : maps.landmarks)
			{
				const auto point{ corner + project(landmark.position.x, landmark.position.y) * scale };

				canvas.text(structures::font_serif_caps, { point.x, point.y + (landmark_below[landmark.kind] ? landmark.radius / meters + 30.0f : -(landmark.radius / meters + 34.0f)) * scale }, (landmark_minor[landmark.kind] ? 31.0f : 42.0f) * scale, ink, landmark_names[landmark.kind], structures::align_center | structures::align_middle);
			}

			if (building.bag >= 0 && building.placed[building.bag].destroyed == false)
			{
				const auto camp{ corner + project(building.placed[building.bag].position.x, building.placed[building.bag].position.z) * scale };

				canvas.line(camp + structures::vec2_s{ -7.0f, -7.0f } * s, camp + structures::vec2_s{ 7.0f, 7.0f } * s, 2.6f * s, blood);
				canvas.line(camp + structures::vec2_s{ 7.0f, -7.0f } * s, camp + structures::vec2_s{ -7.0f, 7.0f } * s, 2.6f * s, blood);
				canvas.text(structures::font_hand, camp + structures::vec2_s{ 12.0f, -14.0f } * s, 22.0f * s, blood, "camp", structures::align_left | structures::align_middle);
			}

			if (grave_marked)
			{
				const auto fell{ corner + project(grave.x, grave.y) * scale };

				canvas.line(fell + structures::vec2_s{ 0.0f, -12.0f } * s, fell + structures::vec2_s{ 0.0f, 11.0f } * s, 2.6f * s, blood);
				canvas.line(fell + structures::vec2_s{ -7.0f, -4.0f } * s, fell + structures::vec2_s{ 7.0f, -4.0f } * s, 2.6f * s, blood);
				canvas.text(structures::font_hand, fell + structures::vec2_s{ 12.0f, 14.0f } * s, 22.0f * s, blood, "died here", structures::align_left | structures::align_middle);
			}

			for (auto index{ 0u }; index < chart_pin_count; index++)
			{
				if (pins[index].stamp)
				{
					const auto point{ corner + project(pins[index].position.x, pins[index].position.y) * scale };
					const auto distance{ mathematics.length(pins[index].position - structures::vec2_s{ player.state.position.x, player.state.position.z }) };

					std::snprintf(label, sizeof(label), "%u", index + 1u);
					std::snprintf(note, sizeof(note), "%.0f m", distance);

					canvas.ring(point, 11.0f * s, 2.2f * s, -1.0f, 7.5f, pen);
					canvas.text(structures::font_hand, point, 19.0f * s, pen, label, structures::align_center | structures::align_middle);
					canvas.text(structures::font_hand, point + structures::vec2_s{ 16.0f, -13.0f } * s, 20.0f * s, pen, note, structures::align_left | structures::align_middle);
				}
			}

			triangle(here + facing * (15.0f * s), here - facing * (8.0f * s) + across * (8.0f * s), here - facing * (8.0f * s) - across * (8.0f * s), blood);
			canvas.text(structures::font_hand, here + structures::vec2_s{ 14.0f, -16.0f } * s, 24.0f * s, blood, "you", structures::align_left | structures::align_middle);

			if (area.contains(mouse))
			{
				std::snprintf(label, sizeof(label), "%c%u", static_cast<char>('A' + std::min(static_cast<std::uint32_t>((mouse.x - area.x) / step), chart_grid_cells - 1u)), std::min(static_cast<std::uint32_t>((mouse.y - area.y) / step), chart_grid_cells - 1u) + 1u);

				canvas.text(structures::font_hand, mouse + structures::vec2_s{ 18.0f, 20.0f } * s, 24.0f * s, pen, label, structures::align_left | structures::align_middle);
			}

			menu.key_name(platform.bindings[structures::bind_map], key, sizeof(key));

			std::snprintf(note, sizeof(note), "%s to fold the map away, right click to mark a spot", key);

			canvas.text(structures::font_hand, { width * 0.5f, area.y + size + 26.0f * s > height ? height - 20.0f * s : area.y + size + 26.0f * s }, 22.0f * s, functions::rgba(235u, 225u, 205u, 210u), note, structures::align_center | structures::align_middle);
		}
	}
}

//=====================================================================================
