
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	menu_c menu;

	bool menu_c::create()
	{
		tip = static_cast<std::uint32_t>(GetTickCount64() / 1000u) % static_cast<std::uint32_t>(std::size(loading_tips));

		return true;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::destroy()
	{
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
			const auto text{ std::string("\n") + std::string(reinterpret_cast<const char*>(bytes.data()), bytes.size()) };
			const auto number = [&](const char* key, std::float_t fallback)
				{
					const auto pattern{ std::string("\n") + key + "=" };

					auto value{ fallback };

					if (const auto found{ text.find(pattern) }; found != std::string::npos)
					{
						value = std::sscanf(text.c_str() + found + pattern.size(), "%f", &value) == 1 ? value : fallback;
					}

					return value;
				};

			user.quality = static_cast<std::uint32_t>(std::clamp(number("quality", static_cast<std::float_t>(user.quality)), static_cast<std::float_t>(structures::quality_low), static_cast<std::float_t>(preset_custom)));

			if (user.quality <= structures::quality_ultra)
			{
				preset(user.quality);
			}

			for (const auto& row : setting_rows)
			{
				if (row.kind == structures::row_choice)
				{
					user.*row.choice = static_cast<std::uint32_t>(std::clamp(number(row.key, static_cast<std::float_t>(user.*row.choice)), 0.0f, static_cast<std::float_t>(row.count - 1u)));
				}

				else if (row.kind == structures::row_slider)
				{
					user.*row.number = std::clamp(number(row.key, user.*row.number), row.low, row.high);
				}

				else if (row.kind == structures::row_toggle)
				{
					user.*row.flag = number(row.key, user.*row.flag ? 1.0f : 0.0f) > 0.5f;
				}
			}

			for (auto action{ 0u }; action < structures::bind_count; action++)
			{
				char key[16]{};

				std::snprintf(key, sizeof(key), "bind%u", action);

				user.bindings[action] = static_cast<std::uint8_t>(std::clamp(number(key, static_cast<std::float_t>(user.bindings[action])), 3.0f, 254.0f));
			}

			logger.write("menu: settings loaded (preset %u, scale %.2f, fov %.0f, display %u)", user.quality, user.render_scale, user.field_of_view, user.display);
		}

		kept = user;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::save_settings()
	{
		char line[96]{};

		auto contents{ std::string("quality=") + std::to_string(user.quality) + "\n" };

		for (const auto& row : setting_rows)
		{
			line[0] = 0;

			if (row.kind == structures::row_choice)
			{
				std::snprintf(line, sizeof(line), "%s=%u\n", row.key, user.*row.choice);
			}

			else if (row.kind == structures::row_slider)
			{
				std::snprintf(line, sizeof(line), "%s=%.3f\n", row.key, user.*row.number);
			}

			else if (row.kind == structures::row_toggle)
			{
				std::snprintf(line, sizeof(line), "%s=%d\n", row.key, user.*row.flag ? 1 : 0);
			}

			contents += line;
		}

		for (auto action{ 0u }; action < structures::bind_count; action++)
		{
			contents += "bind" + std::to_string(action) + "=" + std::to_string(user.bindings[action]) + "\n";
		}

		if (functions::write_file((functions::executable_directory() + settings_file_name).c_str(), contents.data(), contents.size()))
		{
			logger.write("menu: settings saved");
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::apply_settings()
	{
		const auto previous{ renderer.settings };

		renderer.settings.preset = user.quality <= structures::quality_ultra ? user.quality : renderer.settings.preset;
		renderer.settings.render_scale = user.render_scale;
		renderer.settings.field_of_view = user.field_of_view;
		renderer.settings.brightness = user.brightness;
		renderer.settings.anti_aliasing = user.anti_aliasing ? 2u : 1u;
		renderer.settings.shadows = std::min(user.shadows, static_cast<std::uint32_t>(structures::quality_ultra));
		renderer.settings.ambient_occlusion = occlusion_levels[std::min(user.ambient_occlusion, static_cast<std::uint32_t>(std::size(occlusion_levels)) - 1u)];
		renderer.settings.reflections = user.reflections ? static_cast<std::uint32_t>(structures::quality_high) : 0u;
		renderer.settings.volumetrics = user.light_shafts ? static_cast<std::uint32_t>(structures::quality_high) : 0u;
		renderer.settings.anisotropy = 2u << std::min(user.texture_filter, 3u);
		renderer.settings.bloom = user.bloom;
		renderer.settings.motion_blur = user.motion_blur;
		renderer.settings.film_grain = user.film_grain;
		renderer.settings.vignette = user.vignette;
		renderer.settings.chromatic_aberration = user.chromatic_aberration;
		renderer.settings.sharpening = user.sharpening;
		renderer.settings.colour_filter = user.colour_filter;
		renderer.settings.vegetation = vegetation_scales[std::min(user.vegetation, static_cast<std::uint32_t>(std::size(vegetation_scales)) - 1u)];
		renderer.settings.grass = grass_scales[std::min(user.grass, static_cast<std::uint32_t>(std::size(grass_scales)) - 1u)];
		renderer.settings.marks = user.marks != 0u;
		renderer.settings.flashes = user.reduce_flashing ? reduced_flash_scale : 1.0f;

		gpu.vsync = user.vsync;
		application.frame_cap = frame_limits[std::min(user.frame_limit, static_cast<std::uint32_t>(std::size(frame_limits)) - 1u)];
		player.sensitivity = default_mouse_sensitivity * user.sensitivity;
		player.aim_sensitivity = user.aim_sensitivity;
		player.invert = user.invert;
		player.bob_scale = bob_scales[std::min(user.head_bob, static_cast<std::uint32_t>(std::size(bob_scales)) - 1u)];
		player.crouch_toggle = user.crouch_mode != 0u;
		player.aim_toggle = user.aim_mode != 0u;
		player.sprint_toggle = user.sprint_mode != 0u;
		player.tilt_scale = user.strafe_tilt ? 1.0f : 0.0f;
		player.motion_scale = user.calm_camera ? calm_camera_scale : 1.0f;
		canvas.zoom = user.interface_scale;

		actors.dress(user.censor);

		std::memcpy(platform.bindings, user.bindings, sizeof(platform.bindings));

		mixer.effects_level = user.effects_volume;
		mixer.ambience_level = user.ambience_volume;

		if (mixer.master && application.options.capture[0] == 0)
		{
			mixer.master->SetVolume(user.mute_unfocused && platform.focused == false ? 0.0f : user.volume);
		}

		if (previous.anisotropy != renderer.settings.anisotropy && gpu.device)
		{
			gpu.set_anisotropy(renderer.settings.anisotropy);
		}

		heavy = heavy || previous.render_scale != renderer.settings.render_scale || previous.shadows != renderer.settings.shadows || previous.anti_aliasing != renderer.settings.anti_aliasing;

		if (heavy && kit.dragging < 0 && renderer.output_width)
		{
			renderer.apply_settings();

			heavy = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::apply_display()
	{
		if (application.testing == false && application.options.windowed == false)
		{
			platform.set_display_mode(user.display == 0u ? structures::display_mode_windowed : structures::display_mode_borderless);

			if (user.display == 0u)
			{
				const auto size{ std::min(user.window_size, static_cast<std::uint32_t>(std::size(window_sizes)) - 1u) };

				platform.set_window_size(window_sizes[size][0], window_sizes[size][1]);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::listen()
	{
		const auto audible{ user.mute_unfocused == false || platform.focused };

		if (audible != heard && mixer.master && application.options.capture[0] == 0)
		{
			mixer.master->SetVolume(audible ? user.volume : 0.0f);
		}

		heard = audible;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::preset(std::uint32_t level)
	{
		const auto quality{ std::clamp(level, static_cast<std::uint32_t>(structures::quality_low), static_cast<std::uint32_t>(structures::quality_ultra)) };
		const auto step{ quality - static_cast<std::uint32_t>(structures::quality_low) };

		user.quality = quality;
		user.shadows = quality;
		user.ambient_occlusion = std::min(step, 3u);
		user.reflections = step >= 2u ? 1u : 0u;
		user.light_shafts = step >= 2u ? 1u : 0u;
		user.texture_filter = std::min(step + 1u, 3u);
		user.vegetation = step;
		user.grass = step;
		user.anti_aliasing = step >= 1u ? 1u : 0u;
		user.marks = 1u;
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
		const auto s{ canvas.scale };
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const auto progress{ static_cast<std::float_t>(stage) / static_cast<std::float_t>(std::max(stages, 1u)) };
		const auto left{ 120.0f * s };

		char label[96]{};
		char percent[16]{};

		clock += delta;
		tip_clock += delta;
		reveal = map_ready ? std::min(1.0f, reveal + delta * 0.6f) : 0.0f;

		if (tip_clock > loading_tip_time)
		{
			tip_clock = 0.0f;
			tip = (tip + 1u) % static_cast<std::uint32_t>(std::size(loading_tips));
		}

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(6u, 7u, 8u, 255u));

		if (map_ready && chart.view)
		{
			const auto side{ height * 0.86f };
			const structures::rect_s sheet{ width - side - 60.0f * s, (height - side) * 0.5f, side, side };

			canvas.image(chart.view, sheet, { 0.0f, 0.0f }, { 1.0f, 1.0f }, functions::rgba(150u, 140u, 124u, static_cast<std::uint32_t>(reveal * 60.0f)));
			canvas.gradient_horizontal({ sheet.x, 0.0f, sheet.w * 0.5f, height }, functions::rgba(6u, 7u, 8u, 255u), functions::rgba(6u, 7u, 8u, 0u));
		}

		canvas.gradient({ 0.0f, height * 0.55f, width, height * 0.45f }, functions::rgba(6u, 7u, 8u, 0u), functions::rgba(6u, 7u, 8u, 255u));

		draw_brand({ left, height * 0.36f }, 92.0f * s, "Survival   \xB7   Early development");

		std::snprintf(label, sizeof(label), "%s", loading_stage_names[std::min(stage, static_cast<std::uint32_t>(std::size(loading_stage_names)) - 1u)]);
		std::snprintf(percent, sizeof(percent), "%.0f%%", progress * 100.0f);

		kit.caps(structures::font_condensed, { left, height - 150.0f * s }, 18.0f * s, kit_text, label, structures::align_left | structures::align_middle, kit_wide);

		canvas.text(structures::font_bold, { width - left, height - 150.0f * s }, 18.0f * s, kit_dim, percent, structures::align_right | structures::align_middle);

		kit.meter({ left, height - 126.0f * s, width - left * 2.0f, 3.0f * s }, progress, kit_accent);

		kit.caps(structures::font_condensed, { left, height - 84.0f * s }, 14.0f * s, kit_accent, "Tip", structures::align_left | structures::align_middle, kit_wide);

		canvas.text(structures::font_light, { left + 52.0f * s, height - 84.0f * s }, 19.0f * s, functions::with_alpha(kit_dim, mathematics.saturate(std::min(tip_clock, loading_tip_time - tip_clock) * 1.5f)), loading_tips[tip], structures::align_left | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_title(bool alive, std::float_t delta)
	{
		auto action{ static_cast<std::uint32_t>(structures::menu_none) };

		static_cast<void>(alive);

		clock += delta;

		kit.begin(delta);

		kit.blocked = dialog != structures::dialog_none;

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(shot_fade() * 255.0f)));

		kit.shade(current_page == structures::page_main ? 0.8f : 1.0f);

		if (current_page == structures::page_main)
		{
			action = draw_main(title_entries, title_details, static_cast<std::uint32_t>(std::size(title_entries)), false);
		}

		else if (current_page == structures::page_servers)
		{
			action = draw_servers();
		}

		else if (draw_subpage())
		{
			current_page = structures::page_main;
		}

		kit.blocked = false;

		action = draw_dialog(action);

		kit.end();

		return action;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_pause(std::float_t delta)
	{
		auto action{ static_cast<std::uint32_t>(structures::menu_none) };

		clock += delta;

		kit.begin(delta);

		kit.blocked = dialog != structures::dialog_none;

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(3u, 4u, 5u, 110u));

		kit.shade(1.0f);

		if (current_page == structures::page_main)
		{
			action = draw_main(pause_entries, pause_details, static_cast<std::uint32_t>(std::size(pause_entries)), true);

			if (dialog == structures::dialog_none && platform.input.pressed[VK_ESCAPE])
			{
				platform.input.pressed[VK_ESCAPE] = false;

				action = structures::menu_resume;
			}
		}

		else if (draw_subpage())
		{
			current_page = structures::page_main;
		}

		kit.blocked = false;

		action = draw_dialog(action);

		kit.end();

		return action;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_main(const structures::menu_entry_s* entries, const char* const* details, std::uint32_t count, bool paused)
	{
		const auto s{ canvas.scale };
		const auto left{ 120.0f * s };

		auto action{ static_cast<std::uint32_t>(structures::menu_none) };
		auto y{ canvas.screen_height * 0.5f };

		draw_brand({ left, canvas.screen_height * 0.27f }, (paused ? 76.0f : 104.0f) * s, paused ? "Paused" : "Survival   \xB7   Early development");

		for (auto index{ 0u }; index < count; index++)
		{
			if (kit.entry(static_cast<std::int32_t>(index), { left, y }, entries[index].label, details[index]))
			{
				action = entries[index].action;
			}

			y += 66.0f * s;
		}

		draw_footer(paused);

		if (action == structures::menu_settings)
		{
			current_page = structures::page_settings;
			tab = structures::tab_display;
			scroll = 0.0f;
			focus_row = -1;
			action = structures::menu_none;
		}

		else if (action == structures::menu_notes)
		{
			current_page = structures::page_notes;
			action = structures::menu_none;
		}

		else if (action == structures::menu_credits)
		{
			current_page = structures::page_credits;
			action = structures::menu_none;
		}

		else if (action == structures::menu_quit)
		{
			dialog = structures::dialog_quit;
			action = structures::menu_none;
		}

		else if (action == structures::menu_title)
		{
			dialog = structures::dialog_leave;
			action = structures::menu_none;
		}

		return action;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_brand(structures::vec2_s origin, std::float_t size, const char* tagline)
	{
		const auto s{ canvas.scale };

		canvas.tracking = kit_title_spacing;

		canvas.text_shadowed(structures::font_display, origin, size, kit_text, "ZERO POINT", structures::align_left | structures::align_middle);

		canvas.tracking = 0.0f;

		canvas.rect({ origin.x + 2.0f * s, origin.y + size * 0.56f, 56.0f * s, 3.0f * s }, kit_accent);
		canvas.rect({ origin.x + 66.0f * s, origin.y + size * 0.56f + s, 220.0f * s, s }, kit_line);

		kit.caps(structures::font_condensed, { origin.x + 2.0f * s, origin.y + size * 0.56f + 34.0f * s }, 17.0f * s, kit_dim, tagline, structures::align_left | structures::align_middle, kit_wide);
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_footer(bool paused)
	{
		const auto s{ canvas.scale };
		const auto bottom{ canvas.screen_height - 56.0f * s };
		const auto right{ canvas.screen_width - 120.0f * s };

		kit.caps(structures::font_condensed, { 120.0f * s, bottom }, 14.0f * s, kit_faint, "Version 0.2   \xB7   Early development   \xB7   Online only", structures::align_left | structures::align_middle, kit_wide);

		const auto back{ paused ? kit.hint({ right, bottom }, "Esc", "Resume", structures::align_right) + 30.0f * s : 0.0f };

		kit.hint({ right - back, bottom }, "Click", "Select", structures::align_right);

		kit.caps(structures::font_condensed, { right, 70.0f * s }, 14.0f * s, kit_faint, "Survivor", structures::align_right | structures::align_middle, kit_wide);

		canvas.text(structures::font_bold, { right, 98.0f * s }, 22.0f * s, kit_text, client.name[0] ? client.name : "Unknown", structures::align_right | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_subpage()
	{
		auto done{ false };

		if (current_page == structures::page_settings || current_page == structures::page_controls)
		{
			done = draw_settings();
		}

		else if (current_page == structures::page_notes)
		{
			done = draw_notes();
		}

		else if (current_page == structures::page_credits)
		{
			done = draw_credits();
		}

		else
		{
			done = true;
		}

		if (dialog == structures::dialog_none && capturing < 0 && platform.input.pressed[VK_ESCAPE])
		{
			platform.input.pressed[VK_ESCAPE] = false;

			done = true;
		}

		if (done && (current_page == structures::page_settings || current_page == structures::page_controls))
		{
			save_settings();
		}

		return done;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_page_title(const char* title, const char* subtitle)
	{
		const auto s{ canvas.scale };
		const auto left{ 120.0f * s };

		canvas.tracking = kit_title_spacing;

		canvas.text_shadowed(structures::font_display, { left, 104.0f * s }, 64.0f * s, kit_text, title, structures::align_left | structures::align_middle);

		canvas.tracking = 0.0f;

		kit.caps(structures::font_condensed, { left + 2.0f * s, 150.0f * s }, 15.0f * s, kit_dim, subtitle, structures::align_left | structures::align_middle, kit_wide);
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_settings()
	{
		const auto s{ canvas.scale };
		const auto left{ 120.0f * s };
		const auto width{ std::min(1040.0f * s, canvas.screen_width * 0.56f) };
		const auto top{ 250.0f * s };
		const structures::rect_s area{ left, top, width, canvas.screen_height - top - 120.0f * s };
		const structures::rect_s side{ left + width + 70.0f * s, top, std::max(canvas.screen_width - left * 2.0f - width - 70.0f * s, 200.0f * s), area.h };
		const auto bottom{ canvas.screen_height - 56.0f * s };
		const auto right{ canvas.screen_width - 120.0f * s };

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(4u, 5u, 6u, 150u));

		draw_page_title("SETTINGS", "Everything is saved the moment you change it");

		auto x{ left };

		for (auto index{ 0u }; index < structures::tab_count; index++)
		{
			const auto wide{ kit.caps_width(structures::font_condensed, 19.0f * s, settings_tab_names[index], kit_caps) + 40.0f * s };

			if (kit.tab(static_cast<std::int32_t>(200u + index), { x, 182.0f * s, wide, 46.0f * s }, settings_tab_names[index], tab == index))
			{
				tab = index;
				scroll = 0.0f;
				focus_row = -1;
				capturing = -1;
			}

			x += wide;
		}

		kit.rule({ left, 228.0f * s }, canvas.screen_width - left * 2.0f, kit_line);

		if (dialog == structures::dialog_none && capturing < 0 && (platform.input.pressed['Q'] || platform.input.pressed['E']))
		{
			tab = (tab + (platform.input.pressed['Q'] ? structures::tab_count - 1u : 1u)) % structures::tab_count;
			scroll = 0.0f;
			focus_row = -1;

			kit.click(1.05f);
		}

		if (tab == structures::tab_keys)
		{
			draw_keys(area);

			kit.caps(structures::font_condensed, { side.x, side.y + 30.0f * s }, 30.0f * s, kit_text, "Key bindings", structures::align_left | structures::align_middle, kit_caps);

			canvas.rect({ side.x, side.y + 60.0f * s, 48.0f * s, 3.0f * s }, kit_accent);

			const auto written{ kit.paragraph({ side.x, side.y + 104.0f * s }, side.w, 20.0f * s, kit_dim, "Click a box, then press the key you want for that action. Mouse buttons 4 and 5 and the middle button work too. Esc cancels.") };

			kit.paragraph({ side.x, side.y + 104.0f * s + written + 20.0f * s }, side.w, 20.0f * s, kit_faint, "The left and right mouse buttons always fire and aim. Reload and rotate share a key on purpose, because you never need both at once.");
		}

		else
		{
			draw_rows(area);

			draw_detail(side);
		}

		const auto back{ kit.hint({ right, bottom }, "Esc", "Back", structures::align_right) };
		const auto reset{ kit.hint({ right - back - 30.0f * s, bottom }, "R", "Reset page", structures::align_right) };

		kit.hint({ right - back - reset - 60.0f * s, bottom }, "Q  E", "Switch page", structures::align_right);

		if (dialog == structures::dialog_none && capturing < 0 && platform.input.pressed['R'])
		{
			dialog = structures::dialog_defaults;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_rows(structures::rect_s area)
	{
		const auto s{ canvas.scale };
		const auto control{ std::min(400.0f * s, area.w * 0.5f) };
		const auto row_height{ kit_row * s };

		auto content{ 0.0f };
		auto first{ true };

		for (const auto& row : setting_rows)
		{
			if (row.tab == tab)
			{
				content += row.kind == structures::row_header ? (first ? 52.0f : 74.0f) * s : row_height;
				first = false;
			}
		}

		scroll_limit = std::max(content - area.h, 0.0f);

		if (kit.inside(area) && platform.input.wheel != 0.0f)
		{
			scroll = std::clamp(scroll - platform.input.wheel * 70.0f * s, 0.0f, scroll_limit);
		}

		scroll = std::min(scroll, scroll_limit);

		canvas.push_scissor(area);

		auto y{ area.y - scroll };

		first = true;

		for (auto index{ 0u }; index < std::size(setting_rows); index++)
		{
			const auto& row{ setting_rows[index] };

			if (row.tab == tab && row.kind == structures::row_header)
			{
				y += first ? 8.0f * s : 30.0f * s;

				kit.caps(structures::font_condensed, { area.x, y + 14.0f * s }, 15.0f * s, kit_accent, row.label, structures::align_left | structures::align_middle, kit_wide);

				kit.rule({ area.x, y + 32.0f * s }, area.w, kit_line);

				y += 44.0f * s;
				first = false;
			}

			else if (row.tab == tab)
			{
				const structures::rect_s line{ area.x, y, area.w, row_height };
				const structures::rect_s box{ area.x + area.w - control, y + 5.0f * s, control, row_height - 10.0f * s };
				const auto over{ kit.inside(line) && kit.inside(area) };
				const auto id{ static_cast<std::int32_t>(index) + 16 };

				auto changed{ false };

				if (over)
				{
					focus_row = static_cast<std::int32_t>(index);

					canvas.rect(line, kit_raise);
					canvas.rect({ line.x, line.y, 2.0f * s, line.h }, kit_accent);
				}

				canvas.text(structures::font_regular, { area.x + 20.0f * s, y + row_height * 0.5f - s }, 21.0f * s, over ? kit_text : kit_dim, row.label, structures::align_left | structures::align_middle);

				if (row.kind == structures::row_choice)
				{
					changed = kit.choice(id, box, user.*row.choice, row.names, row.count);
				}

				else if (row.kind == structures::row_slider)
				{
					changed = kit.slider(id, box, user.*row.number, row.low, row.high, row.step, row.format, row.display);
				}

				else if (row.kind == structures::row_toggle)
				{
					changed = kit.toggle(id, box, user.*row.flag);
				}

				else if (row.kind == structures::row_preset)
				{
					auto level{ user.quality >= structures::quality_low && user.quality <= structures::quality_ultra ? user.quality - static_cast<std::uint32_t>(structures::quality_low) : 4u };

					if (kit.choice(id, box, level, option_presets, 5u))
					{
						if (level < 4u)
						{
							preset(level + static_cast<std::uint32_t>(structures::quality_low));
						}

						else
						{
							user.quality = preset_custom;
						}

						changed = true;
					}
				}

				if (changed && row.graphics)
				{
					user.quality = preset_custom;
				}

				if (changed && (row.choice == &structures::user_settings_s::display || row.choice == &structures::user_settings_s::window_size) && dialog == structures::dialog_none)
				{
					apply_display();

					dialog = structures::dialog_display;
					dialog_clock = kit_dialog_seconds;
				}

				if (changed)
				{
					apply_settings();
				}

				y += row_height;
			}
		}

		canvas.pop_scissor();

		if (scroll_limit > 0.0f)
		{
			const auto track{ area.h };
			const auto thumb{ std::max(track * area.h / (area.h + scroll_limit), 40.0f * s) };

			canvas.rect({ area.x + area.w + 18.0f * s, area.y, 2.0f * s, track }, kit_line);
			canvas.rect({ area.x + area.w + 18.0f * s, area.y + (track - thumb) * scroll / scroll_limit, 2.0f * s, thumb }, kit_dim);
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_keys(structures::rect_s area)
	{
		const auto s{ canvas.scale };
		const auto per_column{ (static_cast<std::uint32_t>(structures::bind_count) + 1u) / 2u };
		const auto column_width{ (area.w - 40.0f * s) * 0.5f };
		const auto row_height{ std::min(kit_row * s, area.h / static_cast<std::float_t>(per_column)) };

		if (capturing >= 0)
		{
			for (auto key{ 3u }; key < key_count && capturing >= 0; key++)
			{
				if (platform.input.pressed[key] && key != VK_ESCAPE)
				{
					user.bindings[capturing] = static_cast<std::uint8_t>(key);
					capturing = -1;

					std::memcpy(platform.bindings, user.bindings, sizeof(platform.bindings));

					platform.input.pressed[key] = false;

					kit.click(1.2f);
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
			const auto x{ area.x + column * (column_width + 40.0f * s) };
			const auto y{ area.y + static_cast<std::float_t>(action % per_column) * row_height };
			const structures::rect_s line{ x, y, column_width, row_height };
			const structures::rect_s box{ x + column_width - 220.0f * s, y + 6.0f * s, 220.0f * s, row_height - 12.0f * s };
			const auto waiting{ capturing == static_cast<std::int32_t>(action) };
			const auto over{ kit.inside(line) };

			key_name(user.bindings[action], label, sizeof(label));

			if (over || waiting)
			{
				canvas.rect(line, kit_raise);
				canvas.rect({ line.x, line.y, 2.0f * s, line.h }, kit_accent);
			}

			canvas.text(structures::font_regular, { x + 20.0f * s, y + row_height * 0.5f - s }, 21.0f * s, over ? kit_text : kit_dim, bind_names[action], structures::align_left | structures::align_middle);

			canvas.rect(box, functions::rgba(0u, 0u, 0u, 110u));
			canvas.border(box, s, waiting ? kit_accent : (kit.inside(box) ? functions::with_alpha(kit_text, 0.45f) : kit_line));

			if (waiting)
			{
				kit.caps(structures::font_condensed, { box.x + box.w * 0.5f, box.y + box.h * 0.5f }, 16.0f * s, functions::with_alpha(kit_accent, 0.6f + 0.4f * std::sin(clock * 6.0f)), "Press a key", structures::align_center | structures::align_middle, kit_caps);
			}

			else
			{
				kit.caps(structures::font_bold, { box.x + box.w * 0.5f, box.y + box.h * 0.5f - s }, 18.0f * s, kit_text, label, structures::align_center | structures::align_middle, 0.04f);
			}

			if (capturing < 0 && kit.press(box))
			{
				capturing = static_cast<std::int32_t>(action);

				kit.click(1.0f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_detail(structures::rect_s area)
	{
		const auto s{ canvas.scale };

		if (focus_row >= 0 && focus_row < static_cast<std::int32_t>(std::size(setting_rows)) && setting_rows[focus_row].tab == tab && setting_rows[focus_row].kind != structures::row_header)
		{
			const auto& row{ setting_rows[focus_row] };

			auto y{ area.y + 30.0f * s };

			kit.caps(structures::font_condensed, { area.x, y }, 30.0f * s, kit_text, row.label, structures::align_left | structures::align_middle, kit_caps);

			canvas.rect({ area.x, y + 30.0f * s, 48.0f * s, 3.0f * s }, kit_accent);

			kit.paragraph({ area.x, y + 74.0f * s }, area.w, 20.0f * s, kit_dim, row.description);

			y += 290.0f * s;

			if (row.impact > 0u || tab == structures::tab_graphics)
			{
				kit.caps(structures::font_condensed, { area.x, y }, 14.0f * s, kit_faint, "Performance impact", structures::align_left | structures::align_middle, kit_wide);

				for (auto segment{ 0u }; segment < 3u; segment++)
				{
					canvas.rect({ area.x + static_cast<std::float_t>(segment) * 46.0f * s, y + 22.0f * s, 40.0f * s, 4.0f * s }, segment < row.impact ? (row.impact >= 3u ? kit_danger : kit_accent) : kit_line);
				}

				canvas.text(structures::font_bold, { area.x + 150.0f * s, y + 23.0f * s }, 17.0f * s, row.impact >= 3u ? kit_danger : kit_text, impact_names[std::min(row.impact, 3u)], structures::align_left | structures::align_middle);

				y += 70.0f * s;
			}

			if (tab == structures::tab_graphics || tab == structures::tab_display)
			{
				char live[64]{};

				std::snprintf(live, sizeof(live), "%.0f fps   \xB7   %.1f ms", fps, frame_time * 1000.0f);

				kit.caps(structures::font_condensed, { area.x, y }, 14.0f * s, kit_faint, "Right now", structures::align_left | structures::align_middle, kit_wide);

				canvas.text(structures::font_bold, { area.x, y + 28.0f * s }, 22.0f * s, kit_text, live, structures::align_left | structures::align_middle);
			}
		}

		else
		{
			kit.caps(structures::font_condensed, { area.x, area.y + 30.0f * s }, 30.0f * s, kit_faint, settings_tab_names[tab], structures::align_left | structures::align_middle, kit_caps);

			kit.paragraph({ area.x, area.y + 74.0f * s }, area.w, 20.0f * s, kit_faint, "Point at an option to read what it does.");
		}
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_notes()
	{
		const auto s{ canvas.scale };
		const auto left{ 120.0f * s };
		const auto top{ 250.0f * s };
		const auto column{ left + std::min(760.0f * s, canvas.screen_width * 0.42f) };
		const auto right{ canvas.screen_width - 120.0f * s };

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(4u, 5u, 6u, 150u));

		draw_page_title("FIELD GUIDE", "How to move and how to stay alive");

		kit.caps(structures::font_condensed, { left, top }, 15.0f * s, kit_accent, "Controls", structures::align_left | structures::align_middle, kit_wide);
		kit.caps(structures::font_condensed, { column, top }, 15.0f * s, kit_accent, "Staying alive", structures::align_left | structures::align_middle, kit_wide);

		kit.rule({ left, top + 18.0f * s }, column - left - 60.0f * s, kit_line);
		kit.rule({ column, top + 18.0f * s }, right - column, kit_line);

		for (auto index{ 0u }; index < std::size(guide_keys); index++)
		{
			const auto& line{ guide_keys[index] };
			const auto y{ top + 52.0f * s + static_cast<std::float_t>(index) * 36.0f * s };

			char key[96]{};

			if (line.bind == guide_movement)
			{
				char keys[4][24]{};

				key_name(user.bindings[structures::bind_forward], keys[0], sizeof(keys[0]));
				key_name(user.bindings[structures::bind_left], keys[1], sizeof(keys[1]));
				key_name(user.bindings[structures::bind_back], keys[2], sizeof(keys[2]));
				key_name(user.bindings[structures::bind_right], keys[3], sizeof(keys[3]));

				std::snprintf(key, sizeof(key), "%s %s %s %s", keys[0], keys[1], keys[2], keys[3]);
			}

			else if (line.bind >= 0)
			{
				key_name(user.bindings[line.bind], key, sizeof(key));
			}

			else
			{
				std::snprintf(key, sizeof(key), "%s", line.key);
			}

			kit.caps(structures::font_bold, { left, y }, 18.0f * s, kit_text, key, structures::align_left | structures::align_middle, 0.04f);

			canvas.text(structures::font_regular, { left + 200.0f * s, y }, 19.0f * s, kit_dim, line.action, structures::align_left | structures::align_middle);
		}

		auto written{ top + 52.0f * s };

		for (const auto text : notes_survival)
		{
			canvas.text(structures::font_regular, { column, written }, 20.0f * s, kit_dim, text, structures::align_left | structures::align_middle);

			written += (text[0] ? 34.0f : 16.0f) * s;
		}

		kit.hint({ right, canvas.screen_height - 56.0f * s }, "Esc", "Back", structures::align_right);

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool menu_c::draw_credits()
	{
		const auto s{ canvas.scale };
		const auto left{ 120.0f * s };
		const auto top{ 270.0f * s };

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(4u, 5u, 6u, 150u));

		draw_page_title("CREDITS", "Who made what");

		for (auto index{ 0u }; index < std::size(credit_lines); index++)
		{
			const auto y{ top + static_cast<std::float_t>(index) * 74.0f * s };

			kit.caps(structures::font_condensed, { left, y }, 14.0f * s, kit_accent, credit_lines[index][0], structures::align_left | structures::align_middle, kit_wide);

			canvas.text(structures::font_regular, { left, y + 28.0f * s }, 22.0f * s, kit_text, credit_lines[index][1], structures::align_left | structures::align_middle);
		}

		kit.hint({ canvas.screen_width - 120.0f * s, canvas.screen_height - 56.0f * s }, "Esc", "Back", structures::align_right);

		return false;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_servers()
	{
		const auto s{ canvas.scale };
		const auto left{ 120.0f * s };
		const auto right{ canvas.screen_width - 120.0f * s };
		const auto top{ 300.0f * s };
		const auto row_height{ 52.0f * s };
		const auto list_right{ right - 520.0f * s };
		const auto rows{ static_cast<std::uint32_t>(std::max(1.0f, (canvas.screen_height - top - 180.0f * s) / row_height)) };
		const auto players_x{ list_right - 330.0f * s };
		const auto ping_x{ list_right - 170.0f * s };
		const auto map_x{ left + (players_x - left) * 0.62f };
		const auto panel_x{ list_right + 70.0f * s };
		const auto bottom{ canvas.screen_height - 56.0f * s };

		auto action{ static_cast<std::uint32_t>(structures::menu_none) };

		if (clock - browse_clock > net_browse_interval)
		{
			browse_clock = clock;

			client.refresh();
		}

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(4u, 5u, 6u, 150u));

		draw_page_title("PLAY ONLINE", "Every island here is somebody's");

		kit.caps(structures::font_condensed, { left + 20.0f * s, top - 40.0f * s }, 14.0f * s, kit_faint, "Server", structures::align_left | structures::align_middle, kit_wide);
		kit.caps(structures::font_condensed, { map_x, top - 40.0f * s }, 14.0f * s, kit_faint, "Map", structures::align_left | structures::align_middle, kit_wide);
		kit.caps(structures::font_condensed, { players_x, top - 40.0f * s }, 14.0f * s, kit_faint, "Players", structures::align_left | structures::align_middle, kit_wide);
		kit.caps(structures::font_condensed, { ping_x, top - 40.0f * s }, 14.0f * s, kit_faint, "Ping", structures::align_left | structures::align_middle, kit_wide);

		kit.rule({ left, top - 18.0f * s }, list_right - left, kit_line);

		auto shown{ 0u };

		for (auto index{ 0u }; index < client.servers.size() && shown < rows; index++)
		{
			const auto& entry{ client.servers[index] };

			if (entry.responded)
			{
				const structures::rect_s row{ left, top + static_cast<std::float_t>(shown) * row_height, list_right - left, row_height - 4.0f * s };
				const auto chosen{ static_cast<std::int32_t>(index) == selected_server };
				const auto over{ kit.inside(row) };
				const auto y{ row.y + row.h * 0.5f };

				char players[32]{};
				char ping[32]{};

				std::snprintf(players, sizeof(players), "%u / %u", entry.players, entry.maximum);
				std::snprintf(ping, sizeof(ping), "%.0f ms", entry.ping * 1000.0f);

				canvas.rect(row, chosen ? functions::with_alpha(kit_accent, 0.12f) : (over ? kit_raise : functions::rgba(255u, 255u, 255u, 6u)));

				if (chosen)
				{
					canvas.rect({ row.x, row.y, 3.0f * s, row.h }, kit_accent);
				}

				const auto name_width{ canvas.text(structures::font_bold, { left + 20.0f * s, y - s }, 20.0f * s, kit_text, entry.name, structures::align_left | structures::align_middle) };

				if (entry.locked)
				{
					kit.caps(structures::font_condensed, { left + 34.0f * s + name_width, y }, 13.0f * s, kit_accent, "Password", structures::align_left | structures::align_middle, kit_wide);
				}

				canvas.text(structures::font_regular, { map_x, y - s }, 19.0f * s, kit_dim, entry.map, structures::align_left | structures::align_middle);
				canvas.text(structures::font_regular, { players_x, y - s }, 19.0f * s, entry.players >= entry.maximum ? kit_danger : kit_dim, players, structures::align_left | structures::align_middle);
				canvas.text(structures::font_regular, { ping_x, y - s }, 19.0f * s, entry.ping > 0.15f ? kit_danger : (entry.ping > 0.08f ? kit_accent : kit_good), ping, structures::align_left | structures::align_middle);

				if (kit.press(row))
				{
					action = chosen && clock - pick_clock < 0.4f ? static_cast<std::uint32_t>(structures::menu_join) : action;
					join_address = entry.address;
					selected_server = static_cast<std::int32_t>(index);
					pick_clock = clock;
					typing = false;
					typing_secret = false;

					kit.click(1.1f);
				}

				shown++;
			}
		}

		if (shown == 0u)
		{
			kit.caps(structures::font_condensed, { left + 20.0f * s, top + 30.0f * s }, 18.0f * s, kit_dim, "Searching for servers", structures::align_left | structures::align_middle, kit_caps);

			canvas.text(structures::font_light, { left + 20.0f * s, top + 66.0f * s }, 19.0f * s, kit_faint, "No island has answered yet. Host your own, or connect to an address on the right.", structures::align_left | structures::align_middle);
		}

		kit.caps(structures::font_condensed, { panel_x, top - 40.0f * s }, 14.0f * s, kit_faint, "Direct connect", structures::align_left | structures::align_middle, kit_wide);

		kit.rule({ panel_x, top - 18.0f * s }, right - panel_x, kit_line);

		kit.caps(structures::font_condensed, { panel_x, top + 16.0f * s }, 13.0f * s, kit_faint, "Address", structures::align_left | structures::align_middle, kit_wide);

		if (kit.field(900, { panel_x, top + 32.0f * s, right - panel_x, 48.0f * s }, address_text, typing, false))
		{
			typing = true;
			typing_secret = false;
			selected_server = -1;
		}

		kit.caps(structures::font_condensed, { panel_x, top + 112.0f * s }, 13.0f * s, kit_faint, "Password", structures::align_left | structures::align_middle, kit_wide);

		if (kit.field(901, { panel_x, top + 128.0f * s, right - panel_x, 48.0f * s }, client.password, typing_secret, true))
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

		const auto listed{ selected_server >= 0 && selected_server < static_cast<std::int32_t>(client.servers.size()) };

		if (kit.button(902, { panel_x, top + 206.0f * s, right - panel_x, 52.0f * s }, listed ? "Join server" : "Connect", true) || ((typing || typing_secret) && platform.input.pressed[VK_RETURN]))
		{
			action = listed || udp_socket_c::parse(address_text, static_cast<std::uint16_t>(net_default_port), join_address) ? static_cast<std::uint32_t>(structures::menu_join) : action;
			join_address = listed ? client.servers[selected_server].address : join_address;
		}

		if (kit.button(903, { panel_x, top + 272.0f * s, (right - panel_x - 14.0f * s) * 0.5f, 48.0f * s }, "Refresh", false))
		{
			browse_clock = clock;

			client.refresh();
		}

		if (kit.button(904, { panel_x + (right - panel_x + 14.0f * s) * 0.5f, top + 272.0f * s, (right - panel_x - 14.0f * s) * 0.5f, 48.0f * s }, "Host locally", false))
		{
			action = structures::menu_host;
		}

		if (client.status[0])
		{
			kit.paragraph({ panel_x, top + 360.0f * s }, right - panel_x, 18.0f * s, client.state == structures::link_failed ? kit_danger : kit_dim, client.status);
		}

		kit.hint({ right, bottom }, "Esc", "Back", structures::align_right);

		if (dialog == structures::dialog_none && platform.input.pressed[VK_ESCAPE])
		{
			platform.input.pressed[VK_ESCAPE] = false;

			if (typing || typing_secret)
			{
				typing = false;
				typing_secret = false;
			}

			else
			{
				current_page = structures::page_main;
			}
		}

		return action;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t menu_c::draw_dialog(std::uint32_t action)
	{
		auto result{ action };

		if (dialog == structures::dialog_display)
		{
			char text[160]{};

			dialog_clock -= kit.delta;

			std::snprintf(text, sizeof(text), "The screen switches back in %.0f seconds unless you keep the new settings.", std::ceil(std::max(dialog_clock, 0.0f)));

			const auto answer{ kit.dialog("Keep these display settings?", text, "Keep", "Revert") };

			if (answer == 1u)
			{
				kept.display = user.display;
				kept.window_size = user.window_size;
				dialog = structures::dialog_none;

				save_settings();
			}

			else if (answer == 2u || dialog_clock <= 0.0f)
			{
				user.display = kept.display;
				user.window_size = kept.window_size;
				dialog = structures::dialog_none;

				apply_display();

				save_settings();
			}
		}

		else if (dialog == structures::dialog_quit)
		{
			const auto answer{ kit.dialog("Quit to desktop?", "Your character stays where you left them. On a server they sleep where they stand and can be found.", "Quit", "Cancel") };

			result = answer == 1u ? static_cast<std::uint32_t>(structures::menu_quit) : result;
			dialog = answer ? static_cast<std::uint32_t>(structures::dialog_none) : dialog;
		}

		else if (dialog == structures::dialog_leave)
		{
			const auto answer{ kit.dialog("Leave this server?", "You go back to the server list. Your character falls asleep where you are standing.", "Leave", "Stay") };

			result = answer == 1u ? static_cast<std::uint32_t>(structures::menu_title) : result;
			dialog = answer ? static_cast<std::uint32_t>(structures::dialog_none) : dialog;
		}

		else if (dialog == structures::dialog_defaults)
		{
			char text[160]{};

			std::snprintf(text, sizeof(text), "Every option on the %s page goes back to how the game came.", settings_tab_names[tab]);

			const auto answer{ kit.dialog("Reset this page?", text, "Reset", "Cancel") };

			if (answer == 1u)
			{
				for (const auto& row : setting_rows)
				{
					if (row.tab == tab && row.kind == structures::row_choice)
					{
						user.*row.choice = default_user_settings.*row.choice;
					}

					else if (row.tab == tab && row.kind == structures::row_slider)
					{
						user.*row.number = default_user_settings.*row.number;
					}

					else if (row.tab == tab && row.kind == structures::row_toggle)
					{
						user.*row.flag = default_user_settings.*row.flag;
					}
				}

				if (tab == structures::tab_graphics)
				{
					preset(default_user_settings.quality);
				}

				if (tab == structures::tab_keys)
				{
					std::memcpy(user.bindings, default_user_settings.bindings, sizeof(user.bindings));
				}

				if (tab == structures::tab_display)
				{
					apply_display();

					kept.display = user.display;
					kept.window_size = user.window_size;
				}

				apply_settings();

				save_settings();
			}

			dialog = answer ? static_cast<std::uint32_t>(structures::dialog_none) : dialog;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void menu_c::draw_fps(std::float_t delta)
	{
		const auto s{ canvas.scale };

		fps_clock += delta;
		fps_frames++;

		if (fps_clock >= kit_fps_window)
		{
			fps = static_cast<std::float_t>(fps_frames) / fps_clock;
			frame_time = fps_clock / static_cast<std::float_t>(fps_frames);
			fps_clock = 0.0f;
			fps_frames = 0u;
		}

		if (user.show_fps)
		{
			char text[48]{};

			std::snprintf(text, sizeof(text), "%.0f FPS   %.1f MS", fps, frame_time * 1000.0f);

			canvas.text_shadowed(structures::font_bold, { canvas.screen_width - 24.0f * s, 22.0f * s }, 16.0f * s, fps < 30.0f ? kit_danger : (fps < 55.0f ? kit_accent : kit_text), text, structures::align_right | structures::align_middle);
		}
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

		canvas.tracking = 0.18f;

		canvas.text_shadowed(structures::font_display, { width * 0.5f, height * 0.5f - 18.0f * s }, 64.0f * s, functions::with_alpha(kit_text, day), "DAY 1", structures::align_center | structures::align_middle);

		canvas.tracking = 0.0f;

		canvas.text_shadowed(structures::font_light, { width * 0.5f, height * 0.5f + 38.0f * s }, 23.0f * s, functions::with_alpha(kit_dim, memory), "You don't remember how you got here.", structures::align_center | structures::align_middle);
	}
}

//=====================================================================================
