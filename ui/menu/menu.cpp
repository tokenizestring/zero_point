
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	menu_c menu;

	bool menu_c::create()
	{
		std::vector<std::uint32_t> texels(static_cast<std::size_t>(page_width) * page_height);

		const auto width{ static_cast<std::float_t>(page_width) };
		const auto height{ static_cast<std::float_t>(page_height) };

		jobs.parallel_for(page_height, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < page_width; column++)
				{
					const auto x{ static_cast<std::float_t>(column) };
					const auto y{ static_cast<std::float_t>(row) };
					const auto edge{ std::min(std::min(x, y), std::min(width - 1.0f - x, height - 1.0f - y)) };
					const auto tear{ edge - 4.0f - chart.fractal(x / 9.0f, y / 9.0f, 3u, 171u) * 20.0f };
					const auto fibre{ chart.fractal(x / 2.2f, y / 34.0f, 3u, 23u) - 0.5f };
					const auto grain{ chart.noise(x * 0.9f, y * 0.9f, 31u) - 0.5f };
					const auto stain{ mathematics.saturate(chart.fractal(x / 260.0f, y / 260.0f, 4u, 11u) * 1.7f - 0.66f) };
					const auto cup{ mathematics.length(structures::vec2_s{ x - width * 0.83f, y - height * 0.24f }) };
					const auto ring{ mathematics.saturate(1.0f - std::fabs(cup - 92.0f) / 5.0f) * mathematics.saturate(chart.fractal(x / 30.0f, y / 30.0f, 2u, 77u) * 2.0f - 0.35f) * 0.35f };
					const auto rim{ mathematics.saturate(1.0f - tear / 46.0f) };
					const auto base{ chart_paper * (1.0f + fibre * 0.07f + grain * 0.03f) };
					const auto color{ mathematics.lerp(base, structures::vec3_s{ base.x * 0.78f, base.y * 0.66f, base.z * 0.5f }, mathematics.saturate(stain * 0.5f + rim * 0.62f + ring)) };

					texels[static_cast<std::size_t>(row) * page_width + column] = functions::rgba(static_cast<std::uint32_t>(mathematics.saturate(color.x) * 255.0f), static_cast<std::uint32_t>(mathematics.saturate(color.y) * 255.0f), static_cast<std::uint32_t>(mathematics.saturate(color.z) * 255.0f), static_cast<std::uint32_t>(mathematics.saturate(tear * 0.6f) * 255.0f));
				}
			});

		D3D11_TEXTURE2D_DESC description{};

		description.Width = page_width;
		description.Height = page_height;
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
			gpu.context->UpdateSubresource(texture, 0u, nullptr, texels.data(), page_width * 4u, 0u);

			if (SUCCEEDED(gpu.device->CreateShaderResourceView(texture, nullptr, &page)))
			{
				gpu.context->GenerateMips(page);
			}

			functions::release(texture);
		}

		tip = static_cast<std::uint32_t>(GetTickCount64() / 1000u) % static_cast<std::uint32_t>(std::size(loading_tips));

		return page != nullptr;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::destroy()
	{
		functions::release(page);
	}
	/*
	//=====================================================================================
	*/
	void menu_c::load_settings()
	{
		std::vector<std::uint8_t> bytes;

		user = default_user_settings;

		if (functions::read_file((functions::executable_directory() + settings_file_name).c_str(), bytes))
		{
			bytes.push_back(0u);

			const auto text{ reinterpret_cast<const char*>(bytes.data()) };
			const auto number = [&](const char* key, std::float_t fallback)
				{
					auto value{ fallback };

					if (const auto found{ std::strstr(text, key) }; found)
					{
						value = std::sscanf(found + std::strlen(key), "%f", &value) == 1 ? value : fallback;
					}

					return value;
				};

			user.quality = static_cast<std::uint32_t>(std::clamp(number("quality=", static_cast<std::float_t>(user.quality)), static_cast<std::float_t>(structures::quality_low), static_cast<std::float_t>(structures::quality_ultra)));
			user.render_scale = std::clamp(number("render_scale=", user.render_scale), 0.5f, 1.0f);
			user.field_of_view = std::clamp(number("field_of_view=", user.field_of_view), 70.0f, 110.0f);
			user.brightness = std::clamp(number("brightness=", user.brightness), 0.7f, 1.3f);
			user.volume = std::clamp(number("\nvolume=", user.volume), 0.0f, 1.0f);
			user.effects_volume = std::clamp(number("effects_volume=", user.effects_volume), 0.0f, 1.0f);
			user.ambience_volume = std::clamp(number("ambience_volume=", user.ambience_volume), 0.0f, 1.0f);
			user.sensitivity = std::clamp(number("sensitivity=", user.sensitivity), 0.3f, 3.0f);
			user.film_grain = number("film_grain=", user.film_grain ? 1.0f : 0.0f) > 0.5f;
			user.vignette = number("vignette=", user.vignette ? 1.0f : 0.0f) > 0.5f;
			user.vsync = number("vsync=", user.vsync ? 1.0f : 0.0f) > 0.5f;
			user.invert = number("invert=", user.invert ? 1.0f : 0.0f) > 0.5f;

			for (auto action{ 0u }; action < structures::bind_count; action++)
			{
				char key[16]{};

				std::snprintf(key, sizeof(key), "\nbind%u=", action);

				user.bindings[action] = static_cast<std::uint8_t>(std::clamp(number(key, static_cast<std::float_t>(user.bindings[action])), 3.0f, 254.0f));
			}

			logger.write("menu: settings loaded (quality %u, scale %.2f, fov %.0f)", user.quality, user.render_scale, user.field_of_view);
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::save_settings()
	{
		char text[512]{};

		const auto length{ std::snprintf(text, sizeof(text), "quality=%u\nrender_scale=%.2f\nfield_of_view=%.0f\nbrightness=%.2f\nvolume=%.2f\neffects_volume=%.2f\nambience_volume=%.2f\nsensitivity=%.2f\nfilm_grain=%d\nvignette=%d\nvsync=%d\ninvert=%d\n", user.quality, user.render_scale, user.field_of_view, user.brightness, user.volume, user.effects_volume, user.ambience_volume, user.sensitivity, user.film_grain ? 1 : 0, user.vignette ? 1 : 0, user.vsync ? 1 : 0, user.invert ? 1 : 0) };

		auto contents{ std::string(text, static_cast<std::size_t>(std::max(length, 0))) };

		for (auto action{ 0u }; action < structures::bind_count; action++)
		{
			contents += "bind" + std::to_string(action) + "=" + std::to_string(user.bindings[action]) + "\n";
		}

		if (length > 0 && functions::write_file((functions::executable_directory() + settings_file_name).c_str(), contents.data(), contents.size()))
		{
			logger.write("menu: settings saved");
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::apply_settings()
	{
		if (renderer.settings.preset != user.quality)
		{
			renderer.default_settings(user.quality);

			heavy = true;
		}

		heavy = heavy || renderer.settings.render_scale != user.render_scale;

		renderer.settings.render_scale = user.render_scale;
		renderer.settings.field_of_view = user.field_of_view;
		renderer.settings.brightness = user.brightness;
		renderer.settings.film_grain = user.film_grain;
		renderer.settings.vignette = user.vignette;
		gpu.vsync = user.vsync;
		player.sensitivity = default_mouse_sensitivity * user.sensitivity;
		player.invert = user.invert;

		std::memcpy(platform.bindings, user.bindings, sizeof(platform.bindings));

		mixer.effects_level = user.effects_volume;
		mixer.ambience_level = user.ambience_volume;

		if (mixer.master && application.options.capture[0] == 0)
		{
			mixer.master->SetVolume(user.volume);
		}

		if (heavy && renderer.output_width)
		{
			renderer.apply_settings();
		}

		heavy = false;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::plan_shots()
	{
		shot_count = 0u;
		shot = 0u;
		shot_clock = 0.0f;

		structures::vec3_s middle{};

		for (const auto& spawn : maps.spawns)
		{
			middle = middle + spawn.position / static_cast<std::float_t>(maps.spawns.size());
		}

		if (maps.spawns.size())
		{
			const auto& spawn{ maps.spawns[maps.spawns.size() / 3u] };
			const auto forward{ mathematics.flat_forward(spawn.yaw) };

			shots[shot_count++] = { spawn.position - forward * 10.0f + structures::vec3_s{ 0.0f, 2.3f, 0.0f }, spawn.position - forward * 2.0f + structures::vec3_s{ 0.0f, 1.9f, 0.0f }, spawn.position + forward * 70.0f + structures::vec3_s{ 0.0f, 9.0f, 0.0f }, 0.0f, 0.0f, false };
		}

		for (const auto& landmark : maps.landmarks)
		{
			if (landmark.kind == structures::landmark_town && shot_count < std::size(shots))
			{
				const structures::vec3_s center{ landmark.position.x, terrain.height(landmark.position.x, landmark.position.y), landmark.position.y };

				shots[shot_count++] = { center + structures::vec3_s{ 0.0f, 24.0f, 0.0f }, {}, center + structures::vec3_s{ 0.0f, 2.0f, 0.0f }, 0.035f, landmark.radius * 0.72f, true };
			}
		}

		if (farming.springs.size() && shot_count < std::size(shots))
		{
			const auto& spring{ farming.springs[farming.springs.size() / 2u] };
			const structures::vec3_s pool{ spring.x, spring.y, spring.z };

			shots[shot_count++] = { pool + structures::vec3_s{ 5.0f, 2.6f, 2.0f }, pool + structures::vec3_s{ 3.6f, 2.2f, -2.6f }, pool + structures::vec3_s{ 0.0f, 0.4f, 0.0f }, 0.0f, 0.0f, false };
		}

		if (maps.spawns.size() && shot_count < std::size(shots))
		{
			shots[shot_count++] = { structures::vec3_s{ middle.x, 420.0f, middle.z }, {}, structures::vec3_s{ middle.x, 20.0f, middle.z }, 0.02f, terrain_size * 0.56f, true };
		}

		logger.write("menu: %u title shots planned", shot_count);
	}
	/*
	//=====================================================================================
	*/
	void menu_c::title_camera(std::float_t delta, structures::vec3_s& position, std::float_t& yaw, std::float_t& pitch)
	{
		shot_clock += delta;

		if (shot_clock > title_shot_time)
		{
			shot_clock -= title_shot_time;
			shot = (shot + 1u) % std::max(shot_count, 1u);
		}

		if (shot_count)
		{
			const auto& current{ shots[shot] };
			const auto angle{ static_cast<std::float_t>(shot) * 1.7f + current.orbit * shot_clock };

			position = current.orbiting ? structures::vec3_s{ current.focus.x + std::sin(angle) * current.radius, current.from.y, current.focus.z + std::cos(angle) * current.radius } : mathematics.lerp(current.from, current.to, mathematics.smoothstep(0.0f, 1.0f, shot_clock / title_shot_time));

			const auto look{ current.focus - position };

			yaw = std::atan2(look.x, look.z);
			pitch = std::atan2(look.y, std::max(mathematics.length(structures::vec3_s{ look.x, 0.0f, look.z }), 0.01f));
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t menu_c::shot_fade()
	{
		return 1.0f - mathematics.saturate(std::min(shot_clock, title_shot_time - shot_clock) / title_fade_time);
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_loading(std::uint32_t stage, std::uint32_t stages, bool map_ready, std::float_t delta)
	{
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const auto page_tall{ std::min(height * 0.9f, width * 0.94f * static_cast<std::float_t>(page_height) / static_cast<std::float_t>(page_width)) };
		const auto page_wide{ page_tall * static_cast<std::float_t>(page_width) / static_cast<std::float_t>(page_height) };
		const structures::rect_s area{ (width - page_wide) * 0.5f, (height - page_tall) * 0.5f, page_wide, page_tall };
		const auto k{ page_tall / static_cast<std::float_t>(page_height) };
		const auto middle{ area.x + area.w * 0.5f };
		const auto progress{ static_cast<std::float_t>(stage) / static_cast<std::float_t>(std::max(stages, 1u)) };
		const auto steps{ static_cast<std::uint32_t>(progress * static_cast<std::float_t>(loading_footprints) + 0.5f) };
		const auto trail{ area.w * 0.7f };
		const auto first{ area.x + area.w * 0.15f };
		const auto walk{ area.y + area.h * 0.81f };
		const structures::vec2_s centre{ middle, area.y + area.h * 0.5f };

		char label[96]{};

		clock += delta;
		tip_clock += delta;
		reveal = map_ready ? std::min(1.0f, reveal + delta * 0.9f) : 0.0f;

		if (tip_clock > loading_tip_time)
		{
			tip_clock = 0.0f;
			tip = (tip + 1u) % static_cast<std::uint32_t>(std::size(loading_tips));
		}

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(16u, 12u, 9u, 255u));
		canvas.gradient({ 0.0f, 0.0f, width, height * 0.35f }, functions::rgba(0u, 0u, 0u, 150u), functions::rgba(0u, 0u, 0u, 0u));
		canvas.gradient({ 0.0f, height * 0.65f, width, height * 0.35f }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, 170u));
		canvas.image(page, { area.x + 16.0f * k, area.y + 22.0f * k, area.w, area.h }, { 0.0f, 0.0f }, { 1.0f, 1.0f }, functions::rgba(0u, 0u, 0u, 170u));
		canvas.image(page, area, { 0.0f, 0.0f }, { 1.0f, 1.0f }, functions::rgba(255u, 255u, 255u, 255u));

		canvas.text(structures::font_serif_caps, { middle, area.y + area.h * 0.12f }, 92.0f * k, ui_ink, "Zero Point", structures::align_center | structures::align_middle);

		rule({ middle - 170.0f * k, area.y + area.h * 0.175f }, 140.0f * k, 1.6f * k, ui_faded, 3u);
		rule({ middle + 30.0f * k, area.y + area.h * 0.175f }, 140.0f * k, 1.6f * k, ui_faded, 5u);

		canvas.line({ middle - 9.0f * k, area.y + area.h * 0.175f }, { middle, area.y + area.h * 0.175f - 9.0f * k }, 1.6f * k, ui_ink);
		canvas.line({ middle, area.y + area.h * 0.175f - 9.0f * k }, { middle + 9.0f * k, area.y + area.h * 0.175f }, 1.6f * k, ui_ink);
		canvas.line({ middle + 9.0f * k, area.y + area.h * 0.175f }, { middle, area.y + area.h * 0.175f + 9.0f * k }, 1.6f * k, ui_ink);
		canvas.line({ middle, area.y + area.h * 0.175f + 9.0f * k }, { middle - 9.0f * k, area.y + area.h * 0.175f }, 1.6f * k, ui_ink);

		canvas.text(structures::font_hand, { middle, area.y + area.h * 0.225f }, 26.0f * k, ui_faded, "an island, a castaway, and nothing else", structures::align_center | structures::align_middle);

		if (map_ready && chart.view)
		{
			const auto side{ area.h * 0.44f };
			const structures::rect_s sheet{ centre.x - side * 0.5f, centre.y - side * 0.47f, side, side };

			canvas.rect({ sheet.x + 8.0f * k, sheet.y + 10.0f * k, side, side }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(reveal * 70.0f)));
			canvas.image(chart.view, sheet, { 0.0f, 0.0f }, { 1.0f, 1.0f }, functions::rgba(255u, 255u, 255u, static_cast<std::uint32_t>(reveal * 255.0f)));
			canvas.circle({ centre.x, sheet.y + 14.0f * k }, 6.5f * k, functions::rgba(40u, 30u, 24u, static_cast<std::uint32_t>(reveal * 255.0f)));
			canvas.circle({ centre.x - 1.8f * k, sheet.y + 12.2f * k }, 2.0f * k, functions::rgba(150u, 120u, 96u, static_cast<std::uint32_t>(reveal * 200.0f)));
		}

		else
		{
			const auto swing{ std::sin(clock * 1.3f) * 0.28f + std::sin(clock * 3.1f) * 0.06f };

			canvas.ring({ centre.x, centre.y }, 92.0f * k, 2.0f * k, -1.0f, 7.5f, ui_faded);
			canvas.ring({ centre.x, centre.y }, 80.0f * k, 1.2f * k, -1.0f, 7.5f, ui_faded);

			for (auto point{ 0u }; point < 16u; point++)
			{
				const auto angle{ static_cast<std::float_t>(point) * pi * 0.125f };
				const structures::vec2_s direction{ std::sin(angle), -std::cos(angle) };

				canvas.line(centre + direction * (80.0f * k), centre + direction * ((point % 4u ? 86.0f : 96.0f) * k), 1.4f * k, ui_faded);
			}

			for (const auto& needle : { structures::vec2_s{ 0.0f, 1.0f }, structures::vec2_s{ pi, 0.55f } })
			{
				const auto angle{ swing + needle.x };
				const structures::vec2_s along{ std::sin(angle), -std::cos(angle) };
				const structures::vec2_s across{ -along.y, along.x };

				canvas.line(centre + across * (7.0f * k), centre + along * (72.0f * k), 1.6f * k, needle.y > 0.9f ? ui_red : ui_ink);
				canvas.line(centre - across * (7.0f * k), centre + along * (72.0f * k), 1.6f * k, needle.y > 0.9f ? ui_red : ui_ink);
			}

			canvas.circle(centre, 5.0f * k, ui_ink);
			canvas.text(structures::font_serif_caps, { centre.x, centre.y - 118.0f * k }, 30.0f * k, ui_ink, "N", structures::align_center | structures::align_middle);
		}

		for (auto index{ 0u }; index < std::min(steps, loading_footprints); index++)
		{
			const auto x{ first + trail * static_cast<std::float_t>(index) / static_cast<std::float_t>(loading_footprints - 1u) };

			footprint({ x, walk + (index % 2u ? 11.0f : -11.0f) * k }, index % 2u == 0u, 1.45f * k, functions::rgba(40u, 30u, 22u, 190u));
		}

		std::snprintf(label, sizeof(label), "%s%s", loading_stage_names[std::min(stage, static_cast<std::uint32_t>(std::size(loading_stage_names)) - 1u)], &"..."[3u - static_cast<std::uint32_t>(clock * 2.5f) % 4u]);

		canvas.text(structures::font_hand, { middle, walk + 52.0f * k }, 27.0f * k, ui_ink, label, structures::align_center | structures::align_middle);
		canvas.text(structures::font_hand, { middle, area.y + area.h * 0.925f }, 21.0f * k, functions::with_alpha(ui_faded, mathematics.saturate(std::min(tip_clock, loading_tip_time - tip_clock) * 1.5f)), loading_tips[tip], structures::align_center | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_title(bool alive, std::float_t delta)
	{
		const auto s{ canvas.scale };
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };

		auto action{ static_cast<std::uint32_t>(structures::menu_none) };

		clock += delta;
		clicked = false;

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(shot_fade() * 255.0f)));
		canvas.gradient_horizontal({ 0.0f, 0.0f, width * 0.58f, height }, functions::rgba(8u, 6u, 5u, 225u), functions::rgba(8u, 6u, 5u, 0u));
		canvas.gradient({ 0.0f, height * 0.7f, width, height * 0.3f }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, 160u));

		if (current_page == structures::page_main)
		{
			draw_heading("Zero Point", "You woke up with nothing.", 118.0f, { width * 0.075f, height * 0.25f }, s);

			action = draw_entries(title_entries, static_cast<std::uint32_t>(std::size(title_entries)), 0u, { width * 0.078f, height * 0.47f }, delta, s);

			canvas.text_shadowed(structures::font_hand, { width * 0.075f, height - 38.0f * s }, 18.0f * s, functions::with_alpha(ui_cream, 0.6f), "v0.2   -   online only", structures::align_left | structures::align_middle);
		}

		else if (current_page == structures::page_servers)
		{
			action = draw_servers(s);
		}

		else if (draw_subpage(s))
		{
			current_page = structures::page_main;
		}

		action = action == structures::menu_settings || action == structures::menu_notes ? structures::menu_none : action;

		return action;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_pause(std::float_t delta)
	{
		const auto s{ canvas.scale };
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };

		auto action{ static_cast<std::uint32_t>(structures::menu_none) };

		clock += delta;
		clicked = false;

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(4u, 3u, 2u, 120u));
		canvas.gradient_horizontal({ 0.0f, 0.0f, width * 0.55f, height }, functions::rgba(8u, 6u, 5u, 225u), functions::rgba(8u, 6u, 5u, 0u));

		if (current_page == structures::page_main)
		{
			draw_heading("Paused", "The island waits. It is patient.", 92.0f, { width * 0.075f, height * 0.27f }, s);

			action = draw_entries(pause_entries, static_cast<std::uint32_t>(std::size(pause_entries)), 0u, { width * 0.078f, height * 0.45f }, delta, s);

			if (platform.input.pressed[VK_ESCAPE])
			{
				action = structures::menu_resume;
			}
		}

		else if (draw_subpage(s))
		{
			current_page = structures::page_main;
		}

		action = action == structures::menu_settings || action == structures::menu_notes ? structures::menu_none : action;

		return action;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_heading(const char* title, const char* tagline, std::float_t size, structures::vec2_s origin, std::float_t s)
	{
		const auto wide{ canvas.text_shadowed(structures::font_serif_caps, origin, size * s, ui_cream_bright, title, structures::align_left | structures::align_middle) };

		rule({ origin.x, origin.y + size * 0.52f * s }, wide * 0.92f, 2.2f * s, functions::with_alpha(ui_cream, 0.75f), 9u);

		canvas.text_shadowed(structures::font_hand, { origin.x + 4.0f * s, origin.y + size * 0.52f * s + 34.0f * s }, 27.0f * s, functions::with_alpha(ui_cream, 0.82f), tagline, structures::align_left | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_entries(const structures::menu_entry_s* entries, std::uint32_t count, std::uint32_t skip, structures::vec2_s origin, std::float_t delta, std::float_t s)
	{
		const auto mouse{ platform.input.mouse_position };

		auto action{ static_cast<std::uint32_t>(structures::menu_none) };
		auto y{ origin.y };
		auto over{ -1 };

		for (auto index{ 0u }; index < count; index++)
		{
			if ((skip & (1u << index)) == 0u)
			{
				const structures::rect_s area{ origin.x - 40.0f * s, y - 27.0f * s, 470.0f * s, 54.0f * s };
				const auto inside{ area.contains(mouse) };

				glow[index] = mathematics.damp(glow[index], inside ? 1.0f : 0.0f, 14.0f, delta);

				const auto x{ origin.x + glow[index] * 16.0f * s };
				const auto wide{ canvas.text_shadowed(structures::font_serif, { x, y }, 42.0f * s, functions::lerp_color(functions::with_alpha(ui_cream, 0.72f), ui_cream_bright, glow[index]), entries[index].label, structures::align_left | structures::align_middle) };

				if (glow[index] > 0.02f)
				{
					canvas.line({ x - 2.0f * s, y + 23.0f * s }, { x + wide * glow[index], y + 20.0f * s }, 2.6f * s, functions::with_alpha(ui_red, glow[index]));
					canvas.line({ x + 6.0f * s, y + 26.5f * s }, { x + wide * glow[index] * 0.8f, y + 24.0f * s }, 1.4f * s, functions::with_alpha(ui_red, glow[index] * 0.7f));
					canvas.line({ origin.x - 34.0f * s, y + 1.0f * s }, { origin.x - 34.0f * s + 20.0f * s * glow[index], y - 1.0f * s }, 2.6f * s, functions::with_alpha(ui_red, glow[index]));
				}

				if (inside)
				{
					over = static_cast<std::int32_t>(index);
				}

				if (inside && press(area))
				{
					action = entries[index].action;

					mixer.play_2d(structures::sound_ui_click, 0.55f, 0.9f);
				}

				y += 62.0f * s;
			}
		}

		if (over >= 0 && over != hovered)
		{
			mixer.play_2d(structures::sound_ui_click, 0.16f, 1.9f);
		}

		hovered = over;

		current_page = action == structures::menu_settings ? structures::page_settings : (action == structures::menu_notes ? structures::page_notes : current_page);

		return action;
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_subpage(std::float_t s)
	{
		const auto controls{ current_page == structures::page_controls };

		auto done{ controls ? draw_controls(s) : (current_page == structures::page_settings ? draw_settings(s) : draw_notes(s)) };

		if (platform.input.pressed[VK_ESCAPE])
		{
			platform.input.pressed[VK_ESCAPE] = false;

			done = true;
		}

		if (done && (current_page == structures::page_settings || controls))
		{
			save_settings();
		}

		if (done && controls)
		{
			current_page = structures::page_settings;
			done = false;
		}

		return done;
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_settings(std::float_t s)
	{
		const auto width{ std::min(900.0f * s, canvas.screen_width * 0.9f) };
		const auto height{ std::min(760.0f * s, canvas.screen_height * 0.92f) };
		const structures::rect_s area{ (canvas.screen_width - width) * 0.5f, (canvas.screen_height - height) * 0.5f, width, height };
		const auto row_height{ (height - 200.0f * s) / 12.0f };
		const auto row = [&](std::uint32_t index)
			{
				return structures::rect_s{ area.x + 56.0f * s, area.y + 112.0f * s + static_cast<std::float_t>(index) * row_height, area.w - 112.0f * s, row_height };
			};

		hud.card({ area.x + 12.0f * s, area.y + 16.0f * s, area.w, area.h }, functions::rgba(0u, 0u, 0u, 150u), 1u);
		hud.card(area, ui_paper, 1u);

		canvas.text(structures::font_serif_caps, { area.x + 56.0f * s, area.y + 62.0f * s }, 46.0f * s, ui_ink, "Settings", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand, { area.x + area.w - 56.0f * s, area.y + 64.0f * s }, 19.0f * s, ui_faded, "kept for next time", structures::align_right | structures::align_middle);

		auto changed{ false };

		changed = choice(row(0u), "Picture", user.quality, quality_names, static_cast<std::uint32_t>(std::size(quality_names)), s) || changed;
		changed = slider(row(1u), "Render scale", user.render_scale, 0.5f, 1.0f, "%.0f%%", 100.0f, 1, s) || changed;
		changed = slider(row(2u), "Field of view", user.field_of_view, 70.0f, 110.0f, "%.0f\xB0", 1.0f, 2, s) || changed;
		changed = slider(row(3u), "Brightness", user.brightness, 0.7f, 1.3f, "%.0f%%", 100.0f, 3, s) || changed;
		changed = toggle(row(4u), "Film grain", user.film_grain, s) || changed;
		changed = toggle(row(5u), "Vignette", user.vignette, s) || changed;
		changed = toggle(row(6u), "Vertical sync", user.vsync, s) || changed;
		changed = slider(row(7u), "Volume", user.volume, 0.0f, 1.0f, "%.0f%%", 100.0f, 7, s) || changed;
		changed = slider(row(8u), "Effects", user.effects_volume, 0.0f, 1.0f, "%.0f%%", 100.0f, 9, s) || changed;
		changed = slider(row(9u), "Ambience", user.ambience_volume, 0.0f, 1.0f, "%.0f%%", 100.0f, 10, s) || changed;
		changed = slider(row(10u), "Mouse speed", user.sensitivity, 0.3f, 3.0f, "%.1fx", 1.0f, 8, s) || changed;
		changed = toggle(row(11u), "Invert mouse", user.invert, s) || changed;

		if (changed || heavy)
		{
			apply_settings();
		}

		canvas.text(structures::font_hand, { area.x + 56.0f * s, area.y + area.h - 52.0f * s }, 19.0f * s, ui_faded, "Esc to go back", structures::align_left | structures::align_middle);

		if (button({ area.x + area.w - 456.0f * s, area.y + area.h - 80.0f * s, 200.0f * s, 54.0f * s }, "Controls", s))
		{
			current_page = structures::page_controls;
			capturing = -1;
		}

		return button({ area.x + area.w - 236.0f * s, area.y + area.h - 80.0f * s, 180.0f * s, 54.0f * s }, "Done", s);
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_controls(std::float_t s)
	{
		const auto width{ std::min(1080.0f * s, canvas.screen_width * 0.92f) };
		const auto height{ std::min(760.0f * s, canvas.screen_height * 0.92f) };
		const structures::rect_s area{ (canvas.screen_width - width) * 0.5f, (canvas.screen_height - height) * 0.5f, width, height };
		const auto per_column{ (static_cast<std::uint32_t>(structures::bind_count) + 1u) / 2u };
		const auto row_height{ (height - 230.0f * s) / static_cast<std::float_t>(per_column) };
		const auto column_width{ (width - 112.0f * s) * 0.5f };

		hud.card({ area.x + 12.0f * s, area.y + 16.0f * s, area.w, area.h }, functions::rgba(0u, 0u, 0u, 150u), 4u);
		hud.card(area, ui_paper, 4u);

		canvas.text(structures::font_serif_caps, { area.x + 56.0f * s, area.y + 62.0f * s }, 46.0f * s, ui_ink, "Controls", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand, { area.x + area.w - 56.0f * s, area.y + 64.0f * s }, 19.0f * s, ui_faded, "click a key to change it", structures::align_right | structures::align_middle);

		if (capturing >= 0)
		{
			for (auto key{ 3u }; key < key_count && capturing >= 0; key++)
			{
				if (platform.input.pressed[key] && key != VK_ESCAPE)
				{
					user.bindings[capturing] = static_cast<std::uint8_t>(key);
					capturing = -1;

					std::memcpy(platform.bindings, user.bindings, sizeof(platform.bindings));

					mixer.play_2d(structures::sound_ui_click, 0.45f, 1.2f);
				}
			}

			if (platform.input.pressed[VK_ESCAPE])
			{
				platform.input.pressed[VK_ESCAPE] = false;

				capturing = -1;
			}
		}

		for (auto action{ 0u }; action < structures::bind_count; action++)
		{
			char label[48]{};

			const auto column{ static_cast<std::float_t>(action / per_column) };
			const auto y{ area.y + 120.0f * s + static_cast<std::float_t>(action % per_column) * row_height + row_height * 0.5f };
			const auto x{ area.x + 56.0f * s + column * column_width };
			const structures::rect_s field{ x + 250.0f * s, y - 20.0f * s, column_width - 290.0f * s, 40.0f * s };
			const auto waiting{ capturing == static_cast<std::int32_t>(action) };

			key_name(user.bindings[action], label, sizeof(label));

			canvas.text(structures::font_hand, { x, y }, 21.0f * s, ui_ink, bind_names[action], structures::align_left | structures::align_middle);

			hud.sketch(field, 1.4f * s, waiting ? ui_red : ui_ink, 70u + action);

			canvas.text(waiting ? structures::font_hand : structures::font_hand_bold, { field.x + field.w * 0.5f, y }, 20.0f * s, waiting ? ui_red : ui_ink, waiting ? "press a key..." : label, structures::align_center | structures::align_middle);

			if (capturing < 0 && press(field))
			{
				capturing = static_cast<std::int32_t>(action);

				mixer.play_2d(structures::sound_ui_click, 0.4f, 1.0f);
			}
		}

		canvas.text(structures::font_hand, { area.x + 56.0f * s, area.y + area.h - 52.0f * s }, 19.0f * s, ui_faded, capturing >= 0 ? "Esc to cancel" : "Esc to go back", structures::align_left | structures::align_middle);

		if (button({ area.x + area.w - 496.0f * s, area.y + area.h - 80.0f * s, 240.0f * s, 54.0f * s }, "Defaults", s))
		{
			std::memcpy(user.bindings, default_user_settings.bindings, sizeof(user.bindings));
			std::memcpy(platform.bindings, user.bindings, sizeof(platform.bindings));

			capturing = -1;
		}

		return capturing < 0 && button({ area.x + area.w - 236.0f * s, area.y + area.h - 80.0f * s, 180.0f * s, 54.0f * s }, "Done", s);
	}
	/*
	//=====================================================================================
	*/
	void menu_c::key_name(std::uint32_t key, char* out, std::size_t capacity)
	{
		const auto extended{ key == VK_LEFT || key == VK_UP || key == VK_RIGHT || key == VK_DOWN || key == VK_INSERT || key == VK_DELETE || key == VK_HOME || key == VK_END || key == VK_PRIOR || key == VK_NEXT };
		const auto scan{ MapVirtualKeyA(key, MAPVK_VK_TO_VSC) };

		if (key == VK_MBUTTON || key == VK_XBUTTON1 || key == VK_XBUTTON2 || scan == 0u || GetKeyNameTextA(static_cast<LONG>((scan << 16u) | (extended ? 1u << 24u : 0u)), out, static_cast<std::int32_t>(capacity)) == 0)
		{
			std::snprintf(out, capacity, "%s", key == VK_MBUTTON ? "Middle mouse" : (key == VK_XBUTTON1 ? "Mouse 4" : (key == VK_XBUTTON2 ? "Mouse 5" : "Unbound")));
		}
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_notes(std::float_t s)
	{
		const auto width{ std::min(1180.0f * s, canvas.screen_width * 0.94f) };
		const auto height{ std::min(760.0f * s, canvas.screen_height * 0.92f) };
		const structures::rect_s area{ (canvas.screen_width - width) * 0.5f, (canvas.screen_height - height) * 0.5f, width, height };
		const auto column{ area.x + area.w * 0.47f };
		const auto line{ (height - 230.0f * s) / static_cast<std::float_t>(std::size(notes_controls)) };

		hud.card({ area.x + 12.0f * s, area.y + 16.0f * s, area.w, area.h }, functions::rgba(0u, 0u, 0u, 150u), 2u);
		hud.card(area, ui_paper, 2u);

		canvas.text(structures::font_serif_caps, { area.x + 56.0f * s, area.y + 62.0f * s }, 46.0f * s, ui_ink, "Field notes", structures::align_left | structures::align_middle);
		canvas.text(structures::font_serif_caps, { area.x + 56.0f * s, area.y + 124.0f * s }, 26.0f * s, ui_red, "How to move", structures::align_left | structures::align_middle);
		canvas.text(structures::font_serif_caps, { column, area.y + 124.0f * s }, 26.0f * s, ui_red, "How to live", structures::align_left | structures::align_middle);

		for (auto index{ 0u }; index < std::size(notes_controls); index++)
		{
			const auto y{ area.y + 170.0f * s + static_cast<std::float_t>(index) * line };

			canvas.text(structures::font_hand_bold, { area.x + 56.0f * s, y }, 20.0f * s, ui_ink, notes_controls[index][0], structures::align_left | structures::align_middle);
			canvas.text(structures::font_hand, { area.x + 250.0f * s, y }, 20.0f * s, ui_faded, notes_controls[index][1], structures::align_left | structures::align_middle);
		}

		auto written{ area.y + 170.0f * s };

		for (const auto text : notes_survival)
		{
			canvas.text(structures::font_hand, { column, written }, 21.0f * s, ui_ink, text, structures::align_left | structures::align_middle);

			written += (text[0] ? 36.0f : 18.0f) * s;
		}

		canvas.line({ column - 34.0f * s, area.y + 108.0f * s }, { column - 31.0f * s, area.y + area.h - 110.0f * s }, 1.2f * s, ui_faded);

		return button({ area.x + area.w - 236.0f * s, area.y + area.h - 80.0f * s, 180.0f * s, 54.0f * s }, "Done", s);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_servers(std::float_t s)
	{
		const auto width{ std::min(1180.0f * s, canvas.screen_width * 0.94f) };
		const auto height{ std::min(780.0f * s, canvas.screen_height * 0.92f) };
		const structures::rect_s area{ (canvas.screen_width - width) * 0.5f, (canvas.screen_height - height) * 0.5f, width, height };
		const auto left{ area.x + 56.0f * s };
		const auto right{ area.x + area.w - 56.0f * s };
		const auto top{ area.y + 168.0f * s };
		const auto row_height{ 46.0f * s };
		const auto rows{ static_cast<std::uint32_t>(std::max(1.0f, (area.h - 400.0f * s) / row_height)) };
		const auto players_x{ right - 470.0f * s };
		const auto ping_x{ right - 300.0f * s };
		const auto map_x{ right - 170.0f * s };
		const structures::rect_s field{ left + 120.0f * s, area.y + area.h - 196.0f * s, 420.0f * s, 46.0f * s };

		auto action{ static_cast<std::uint32_t>(structures::menu_none) };

		if (clock - browse_clock > net_browse_interval)
		{
			browse_clock = clock;

			client.refresh();
		}

		hud.card({ area.x + 12.0f * s, area.y + 16.0f * s, area.w, area.h }, functions::rgba(0u, 0u, 0u, 150u), 3u);
		hud.card(area, ui_paper, 3u);

		canvas.text(structures::font_serif_caps, { left, area.y + 62.0f * s }, 46.0f * s, ui_ink, "Servers", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand, { right, area.y + 64.0f * s }, 19.0f * s, ui_faded, "every island is somebody's", structures::align_right | structures::align_middle);

		canvas.text(structures::font_hand_bold, { left, top - 34.0f * s }, 20.0f * s, ui_red, "Name", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand_bold, { players_x, top - 34.0f * s }, 20.0f * s, ui_red, "Players", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand_bold, { ping_x, top - 34.0f * s }, 20.0f * s, ui_red, "Ping", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand_bold, { map_x, top - 34.0f * s }, 20.0f * s, ui_red, "Map", structures::align_left | structures::align_middle);

		canvas.line({ left - 8.0f * s, top - 12.0f * s }, { right + 8.0f * s, top - 14.0f * s }, 1.4f * s, ui_faded);

		auto shown{ 0u };

		for (auto index{ 0u }; index < client.servers.size() && shown < rows; index++)
		{
			const auto& entry{ client.servers[index] };

			if (entry.responded)
			{
				const structures::rect_s row{ left - 14.0f * s, top + static_cast<std::float_t>(shown) * row_height, right - left + 28.0f * s, row_height - 6.0f * s };
				const auto chosen{ static_cast<std::int32_t>(index) == selected_server };

				char players[32]{};
				char ping[32]{};

				std::snprintf(players, sizeof(players), "%u / %u", entry.players, entry.maximum);
				std::snprintf(ping, sizeof(ping), "%.0f ms", entry.ping * 1000.0f);

				if (chosen || row.contains(platform.input.mouse_position))
				{
					hud.hatch(row, 1.0f, functions::rgba(36u, 27u, 20u, chosen ? 70u : 36u), s);
				}

				char title[96]{};

				std::snprintf(title, sizeof(title), entry.locked ? "%s  (password)" : "%s", entry.name);

				canvas.text(structures::font_hand_bold, { left, row.y + row.h * 0.5f }, 22.0f * s, chosen ? ui_red : ui_ink, title, structures::align_left | structures::align_middle);
				canvas.text(structures::font_hand, { players_x, row.y + row.h * 0.5f }, 21.0f * s, ui_ink, players, structures::align_left | structures::align_middle);
				canvas.text(structures::font_hand, { ping_x, row.y + row.h * 0.5f }, 21.0f * s, ui_ink, ping, structures::align_left | structures::align_middle);
				canvas.text(structures::font_hand, { map_x, row.y + row.h * 0.5f }, 21.0f * s, ui_ink, entry.map, structures::align_left | structures::align_middle);

				if (press(row))
				{
					action = chosen && clock - pick_clock < 0.4f ? static_cast<std::uint32_t>(structures::menu_join) : action;
					join_address = entry.address;
					selected_server = static_cast<std::int32_t>(index);
					pick_clock = clock;
					typing = false;

					mixer.play_2d(structures::sound_ui_click, 0.4f, 1.1f);
				}

				shown++;
			}
		}

		if (shown == 0u)
		{
			canvas.text(structures::font_hand, { left, top + 30.0f * s }, 22.0f * s, ui_faded, "No islands answered yet. Host one below, or type an address.", structures::align_left | structures::align_middle);
		}

		canvas.text(structures::font_hand_bold, { left, field.y + field.h * 0.5f }, 21.0f * s, ui_ink, "Address", structures::align_left | structures::align_middle);

		hud.sketch(field, 1.6f * s, typing ? ui_red : ui_ink, 57u);

		char shown_address[80]{};

		std::snprintf(shown_address, sizeof(shown_address), "%s%s", address_text, typing && std::fmod(clock, 1.0f) < 0.55f ? "|" : "");

		canvas.text(structures::font_hand, { field.x + 14.0f * s, field.y + field.h * 0.5f }, 21.0f * s, ui_ink, shown_address, structures::align_left | structures::align_middle);

		const structures::rect_s secret{ right - 230.0f * s, field.y, 230.0f * s, field.h };
		const auto masked{ std::string(std::strlen(client.password), '\xB7') };

		canvas.text(structures::font_hand_bold, { secret.x - 118.0f * s, secret.y + secret.h * 0.5f }, 21.0f * s, ui_ink, "Password", structures::align_left | structures::align_middle);

		hud.sketch(secret, 1.6f * s, typing_secret ? ui_red : ui_ink, 61u);

		canvas.text(structures::font_hand, { secret.x + 14.0f * s, secret.y + secret.h * 0.5f }, 21.0f * s, ui_ink, (masked + (typing_secret && std::fmod(clock, 1.0f) < 0.55f ? "|" : "")).c_str(), structures::align_left | structures::align_middle);

		if (press(field))
		{
			typing = true;
			typing_secret = false;
			selected_server = -1;
		}

		if (press(secret))
		{
			typing = false;
			typing_secret = true;
		}

		if (typing)
		{
			type_into(address_text, sizeof(address_text));
		}

		if (typing_secret)
		{
			type_into(client.password, sizeof(client.password));
		}

		if ((typing || typing_secret) && platform.input.pressed[VK_RETURN])
		{
			const auto listed{ selected_server >= 0 && selected_server < static_cast<std::int32_t>(client.servers.size()) };

			action = listed || udp_socket_c::parse(address_text, static_cast<std::uint16_t>(net_default_port), join_address) ? static_cast<std::uint32_t>(structures::menu_join) : action;
			join_address = listed ? client.servers[selected_server].address : join_address;
		}

		if (client.status[0])
		{
			canvas.text(structures::font_hand, { left, area.y + area.h - 130.0f * s }, 20.0f * s, client.state == structures::link_failed ? ui_red : ui_faded, client.status, structures::align_left | structures::align_middle);
		}

		if (button({ left - 10.0f * s, area.y + area.h - 90.0f * s, 150.0f * s, 54.0f * s }, "Back", s) || (platform.input.pressed[VK_ESCAPE] && typing == false && typing_secret == false))
		{
			platform.input.pressed[VK_ESCAPE] = false;

			current_page = structures::page_main;
			typing = false;
			typing_secret = false;
		}

		if (button({ right - 700.0f * s, area.y + area.h - 90.0f * s, 170.0f * s, 54.0f * s }, "Refresh", s))
		{
			browse_clock = clock;

			client.refresh();
		}

		if (button({ right - 510.0f * s, area.y + area.h - 90.0f * s, 300.0f * s, 54.0f * s }, "Host a local server", s))
		{
			action = structures::menu_host;
		}

		if (button({ right - 190.0f * s, area.y + area.h - 90.0f * s, 190.0f * s, 54.0f * s }, "Join", s))
		{
			const auto listed{ selected_server >= 0 && selected_server < static_cast<std::int32_t>(client.servers.size()) };

			action = listed || udp_socket_c::parse(address_text, static_cast<std::uint16_t>(net_default_port), join_address) ? static_cast<std::uint32_t>(structures::menu_join) : action;
			join_address = listed ? client.servers[selected_server].address : join_address;
		}

		if ((typing || typing_secret) && platform.input.pressed[VK_ESCAPE])
		{
			platform.input.pressed[VK_ESCAPE] = false;

			typing = false;
			typing_secret = false;
		}

		return action;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::type_into(char* buffer, std::size_t capacity)
	{
		auto length{ std::strlen(buffer) };

		for (auto index{ 0u }; index < platform.input.text_length; index++)
		{
			const auto character{ platform.input.text[index] };

			if (character > 32 && character < 127 && length + 1u < capacity)
			{
				buffer[length++] = character;
				buffer[length] = 0;
			}
		}

		if ((platform.input.pressed[VK_BACK] || platform.input.repeated[VK_BACK]) && length)
		{
			buffer[length - 1u] = 0;
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_waking(std::float_t time)
	{
		const auto s{ canvas.scale };
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const auto first{ mathematics.smoothstep(0.8f, 1.5f, time) * 0.34f };
		const auto blink{ mathematics.smoothstep(1.5f, 1.9f, time) };
		const auto open{ mathematics.smoothstep(2.0f, 3.9f, time) };
		const auto openness{ std::max(first * (1.0f - blink), open) };
		const auto lid{ (1.0f - openness) * height * 0.5f };
		const auto soft{ 170.0f * s * (1.0f - open * 0.6f) };
		const auto day{ mathematics.saturate(std::min((time - 0.3f) * 2.0f, (2.9f - time) * 1.6f)) };
		const auto memory{ mathematics.saturate(std::min((time - 0.8f) * 2.0f, (3.3f - time) * 1.6f)) };
		const auto black{ functions::rgba(0u, 0u, 0u, 255u) };

		canvas.rect({ 0.0f, 0.0f, width, lid }, black);
		canvas.gradient({ 0.0f, lid, width, soft }, black, functions::rgba(0u, 0u, 0u, 0u));
		canvas.rect({ 0.0f, height - lid, width, lid }, black);
		canvas.gradient({ 0.0f, height - lid - soft, width, soft }, functions::rgba(0u, 0u, 0u, 0u), black);
		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(mathematics.saturate(1.0f - openness * 3.0f) * 255.0f)));

		canvas.text_shadowed(structures::font_hand, { width * 0.5f, height * 0.5f - 16.0f * s }, 46.0f * s, functions::with_alpha(ui_cream_bright, day), "Day 1", structures::align_center | structures::align_middle);
		canvas.text_shadowed(structures::font_hand, { width * 0.5f, height * 0.5f + 36.0f * s }, 25.0f * s, functions::with_alpha(ui_cream, memory * 0.85f), "You don't remember how you got here.", structures::align_center | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	void menu_c::footprint(structures::vec2_s center, bool left, std::float_t size, std::uint32_t color)
	{
		const auto inner{ left ? 1.0f : -1.0f };
		const auto turn{ -0.17f * inner };
		const structures::vec3_s pads[11] = { { -10.5f, 0.2f, 4.4f }, { -6.8f, -1.4f, 3.7f }, { -3.2f, -2.3f, 3.5f }, { 0.6f, -2.0f, 4.2f }, { 3.8f, -0.6f, 5.2f }, { 4.6f, 2.2f, 4.2f }, { 11.4f, 3.6f, 2.5f }, { 12.9f, 0.6f, 1.9f }, { 12.6f, -1.8f, 1.7f }, { 11.6f, -3.9f, 1.5f }, { 10.1f, -5.6f, 1.3f } };

		for (const auto& pad : pads)
		{
			const structures::vec2_s local{ pad.x, pad.y * inner };

			canvas.circle(center + structures::vec2_s{ local.x * std::cos(turn) - local.y * std::sin(turn), local.x * std::sin(turn) + local.y * std::cos(turn) } * size, pad.z * size, color);
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::rule(structures::vec2_s from, std::float_t length, std::float_t thickness, std::uint32_t color, std::uint32_t seed)
	{
		auto previous{ from };

		for (auto step{ 1u }; step <= 4u && length > 0.0f; step++)
		{
			const structures::vec2_s next{ from.x + length * static_cast<std::float_t>(step) / 4.0f, from.y + (mathematics.hash_float(seed * 97u + step) - 0.5f) * thickness * 1.6f };

			canvas.line(previous, next, thickness * (step == 4u ? 0.7f : 1.0f), color);

			previous = next;
		}
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::slider(structures::rect_s row, const char* label, std::float_t& value, std::float_t low, std::float_t high, const char* format, std::float_t display, std::int32_t id, std::float_t s)
	{
		const auto start{ row.x + 290.0f * s };
		const auto end{ row.x + row.w - 110.0f * s };
		const auto y{ row.y + row.h * 0.5f };
		const auto fraction{ mathematics.saturate((value - low) / (high - low)) };
		const auto knob{ start + (end - start) * fraction };
		const structures::rect_s track{ start - 14.0f * s, row.y, end - start + 28.0f * s, row.h };
		const auto previous{ value };

		char text[32]{};

		canvas.text(structures::font_hand, { row.x, y }, 22.0f * s, ui_ink, label, structures::align_left | structures::align_middle);

		rule({ start, y }, end - start, 1.6f * s, ui_faded, static_cast<std::uint32_t>(id) + 11u);

		canvas.line({ start, y }, { knob, y - 0.5f * s }, 3.2f * s, ui_ink);
		canvas.circle({ knob, y }, (dragging == id ? 9.0f : 7.5f) * s, ui_ink);
		canvas.circle({ knob - 2.0f * s, y - 2.0f * s }, 2.2f * s, functions::rgba(120u, 100u, 84u, 200u));

		if (press(track))
		{
			dragging = id;
		}

		if (dragging == id)
		{
			if (platform.input.down[VK_LBUTTON])
			{
				value = low + mathematics.saturate((platform.input.mouse_position.x - start) / (end - start)) * (high - low);
			}

			else
			{
				dragging = -1;
				heavy = id == 1 || heavy;
			}
		}

		std::snprintf(text, sizeof(text), format, value * display);

		canvas.text(structures::font_hand_bold, { row.x + row.w, y }, 21.0f * s, ui_ink, text, structures::align_right | structures::align_middle);

		return value != previous && id != 1;
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::toggle(structures::rect_s row, const char* label, bool& value, std::float_t s)
	{
		const auto y{ row.y + row.h * 0.5f };
		const structures::rect_s box{ row.x + 290.0f * s, y - 12.0f * s, 24.0f * s, 24.0f * s };
		const structures::rect_s hit{ box.x - 10.0f * s, row.y, 140.0f * s, row.h };

		canvas.text(structures::font_hand, { row.x, y }, 22.0f * s, ui_ink, label, structures::align_left | structures::align_middle);

		hud.sketch(box, 1.5f * s, ui_ink, static_cast<std::uint32_t>(box.y));

		if (value)
		{
			canvas.line({ box.x + 3.0f * s, box.y + 12.0f * s }, { box.x + 10.0f * s, box.y + 21.0f * s }, 3.0f * s, ui_red);
			canvas.line({ box.x + 10.0f * s, box.y + 21.0f * s }, { box.x + 28.0f * s, box.y - 5.0f * s }, 3.0f * s, ui_red);
		}

		canvas.text(structures::font_hand, { box.x + 44.0f * s, y }, 20.0f * s, value ? ui_ink : ui_faded, value ? "on" : "off", structures::align_left | structures::align_middle);

		if (press(hit))
		{
			value = value == false;

			mixer.play_2d(structures::sound_ui_click, 0.4f, 1.2f);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::choice(structures::rect_s row, const char* label, std::uint32_t& value, const char* const* names, std::uint32_t count, std::float_t s)
	{
		const auto y{ row.y + row.h * 0.5f };
		const auto start{ row.x + 290.0f * s };
		const auto spacing{ (row.w - 290.0f * s) / static_cast<std::float_t>(count) };

		auto result{ false };

		canvas.text(structures::font_hand, { row.x, y }, 22.0f * s, ui_ink, label, structures::align_left | structures::align_middle);

		for (auto index{ 0u }; index < count; index++)
		{
			const auto level{ index + static_cast<std::uint32_t>(structures::quality_low) };
			const structures::rect_s spot{ start + static_cast<std::float_t>(index) * spacing, row.y + 4.0f * s, spacing - 10.0f * s, row.h - 8.0f * s };
			const auto inside{ spot.contains(platform.input.mouse_position) };
			const auto wide{ canvas.text(structures::font_hand, { spot.x + 6.0f * s, y }, 21.0f * s, value == level || inside ? ui_ink : ui_faded, names[index], structures::align_left | structures::align_middle) };

			if (value == level)
			{
				hud.loop({ spot.x + 6.0f * s, y - 12.0f * s, wide, 24.0f * s }, ui_red, s * 0.7f);
			}

			if (press(spot) && value != level)
			{
				value = level;
				result = true;

				mixer.play_2d(structures::sound_ui_click, 0.45f, 1.1f);
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::button(structures::rect_s area, const char* label, std::float_t s)
	{
		const auto inside{ area.contains(platform.input.mouse_position) };

		if (inside)
		{
			hud.hatch(area, 1.0f, functions::rgba(36u, 27u, 20u, 46u), s);
		}

		hud.sketch(area, 1.8f * s, inside ? ui_red : ui_ink, 41u);

		canvas.text(structures::font_hand_bold, { area.x + area.w * 0.5f, area.y + area.h * 0.5f }, 26.0f * s, inside ? ui_red : ui_ink, label, structures::align_center | structures::align_middle);

		if (press(area))
		{
			mixer.play_2d(structures::sound_ui_click, 0.5f, 0.9f);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::press(structures::rect_s area)
	{
		if (clicked == false && platform.input.pressed[VK_LBUTTON] && area.contains(platform.input.mouse_position))
		{
			clicked = true;

			platform.input.pressed[VK_LBUTTON] = false;

			return true;
		}

		return false;
	}
}

//=====================================================================================
