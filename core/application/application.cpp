
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	application_c application;

	std::int32_t application_c::run(HINSTANCE instance)
	{
		options.quality = -1;
		options.gather_kind = -1;
		options.start_hours = 8.5f;
		options.inspect_hands = -1.0f;
		options.showcase_angle = -1.0f;
		options.jam_progress = -1.0f;
		options.reload_progress = -1.0f;

		parse_arguments();

		logger.initialize(log_file_name, options.dedicated);

		CoInitializeEx(nullptr, COINIT_MULTITHREADED);

		jobs.start();

		logger.write("zero point starting (%u worker threads)", jobs.thread_count());

		running = startup(instance);

		while (running)
		{
			frame();
		}

		shutdown();

		jobs.stop();

		CoUninitialize();

		logger.write("zero point exited cleanly");

		return 0;
	}
	/*
	//=====================================================================================
	*/
	void application_c::parse_arguments()
	{
		auto count{ 0 };

		if (auto arguments{ CommandLineToArgvW(GetCommandLineW(), &count) }; arguments)
		{
			char current[512]{};
			char next[512]{};

			for (auto index{ 1 }; index < count; index++)
			{
				WideCharToMultiByte(CP_UTF8, 0u, arguments[index], -1, current, sizeof(current), nullptr, nullptr);

				next[0] = 0;

				if (index + 1 < count)
				{
					WideCharToMultiByte(CP_UTF8, 0u, arguments[index + 1], -1, next, sizeof(next), nullptr, nullptr);
				}

				if (std::strcmp(current, "--dedicated") == 0)
				{
					options.dedicated = true;
				}

				else if (std::strcmp(current, "--smoke") == 0)
				{
					options.smoke = true;

					options.frames = std::max(options.frames, 120u);
				}

				else if (std::strcmp(current, "--windowed") == 0)
				{
					options.windowed = true;
				}

				else if (std::strcmp(current, "--frames") == 0 && next[0])
				{
					options.frames = static_cast<std::uint32_t>(std::strtoul(next, nullptr, 10));

					index++;
				}

				else if (std::strcmp(current, "--capture") == 0 && next[0])
				{
					std::snprintf(options.capture, sizeof(options.capture), "%s", next);

					options.frames = std::max(options.frames, 60u);

					index++;
				}

				else if (std::strcmp(current, "--map") == 0 && next[0])
				{
					std::snprintf(options.map, sizeof(options.map), "%s", next);

					index++;
				}

				else if (std::strcmp(current, "--mode") == 0 && next[0])
				{
					std::snprintf(options.mode, sizeof(options.mode), "%s", next);

					index++;
				}

				else if (std::strcmp(current, "--connect") == 0 && next[0])
				{
					std::snprintf(options.connect, sizeof(options.connect), "%s", next);

					index++;
				}

				else if (std::strcmp(current, "--password") == 0 && next[0])
				{
					std::snprintf(options.password, sizeof(options.password), "%s", next);

					index++;
				}

				else if (std::strcmp(current, "--weather") == 0 && next[0])
				{
					options.weather_test = static_cast<std::uint32_t>(std::clamp(std::atoi(next), 0, 3)) + 1u;

					index++;
				}

				else if (std::strcmp(current, "--name") == 0 && next[0])
				{
					std::snprintf(options.player_name, sizeof(options.player_name), "%s", next);

					index++;
				}

				else if (std::strcmp(current, "--raid") == 0)
				{
					options.raid_test = true;
					options.net_test = true;
					options.walk_test = true;
				}

				else if (std::strcmp(current, "--sky") == 0 && next[0])
				{
					std::snprintf(options.sky, sizeof(options.sky), "%s", next);

					index++;
				}

				else if (std::strcmp(current, "--quality") == 0 && next[0])
				{
					options.quality = std::atoi(next);

					index++;
				}

				else if (std::strcmp(current, "--walk") == 0)
				{
					options.walk_test = true;
				}

				else if (std::strcmp(current, "--nettest") == 0)
				{
					options.net_test = true;
					options.walk_test = true;
				}

				else if (std::strcmp(current, "--third") == 0)
				{
					options.third_person = true;
				}

				else if (std::strcmp(current, "--ground") == 0)
				{
					options.camera_ground = true;
				}

				else if (std::strcmp(current, "--gather") == 0 && next[0])
				{
					options.gather_kind = std::atoi(next);

					index++;
				}

				else if (std::strcmp(current, "--fell") == 0)
				{
					options.fell_test = true;
				}

				else if (std::strcmp(current, "--marks") == 0)
				{
					options.marks_test = true;
				}

				else if (std::strcmp(current, "--keypad") == 0)
				{
					options.keypad_test = true;
					options.base_test = true;
				}

				else if (std::strcmp(current, "--dead") == 0)
				{
					options.dead_test = true;
				}

				else if (std::strcmp(current, "--inventory") == 0)
				{
					options.test_inventory = true;
				}

				else if (std::strcmp(current, "--fight") == 0)
				{
					options.fight_test = true;
				}

				else if (std::strcmp(current, "--base") == 0)
				{
					options.base_test = true;
				}

				else if (std::strcmp(current, "--aim") == 0)
				{
					options.aim_test = true;
				}

				else if (std::strcmp(current, "--fire") == 0)
				{
					options.fire_test = true;
				}

				else if (std::strcmp(current, "--chart") == 0)
				{
					options.chart_test = true;
				}

				else if (std::strcmp(current, "--farm") == 0)
				{
					options.farm_test = true;
				}

				else if (std::strcmp(current, "--spring") == 0)
				{
					options.spring_test = true;
				}

				else if (std::strcmp(current, "--title") == 0)
				{
					options.title_test = true;
				}

				else if (std::strcmp(current, "--wake") == 0)
				{
					options.title_test = true;
					options.wake_test = true;
				}

				else if (std::strcmp(current, "--pause") == 0)
				{
					options.pause_test = true;
				}

				else if (std::strcmp(current, "--loading") == 0)
				{
					options.loading_test = true;
				}

				else if (std::strcmp(current, "--page") == 0 && next[0])
				{
					options.menu_page = std::atoi(next);

					index++;
				}

				else if (std::strcmp(current, "--time") == 0 && next[0])
				{
					options.start_hours = static_cast<std::float_t>(std::atof(next));

					index++;
				}

				else if (std::strcmp(current, "--inspect") == 0 && next[0])
				{
					options.inspect_hands = static_cast<std::float_t>(std::atof(next));

					index++;
				}

				else if (std::strcmp(current, "--showcase") == 0 && next[0])
				{
					options.showcase_angle = static_cast<std::float_t>(std::atof(next));

					index++;
				}

				else if (std::strcmp(current, "--jam") == 0 && next[0])
				{
					options.jam_progress = std::clamp(static_cast<std::float_t>(std::atof(next)), 0.0f, 0.98f);

					index++;
				}

				else if (std::strcmp(current, "--dive") == 0)
				{
					options.dive_test = true;
				}

				else if (std::strcmp(current, "--save-test") == 0)
				{
					options.save_test = true;
				}

				else if (std::strcmp(current, "--ride") == 0)
				{
					options.ride_test = true;
				}

				else if (std::strcmp(current, "--goal") == 0 && next[0])
				{
					options.goal_step = static_cast<std::uint32_t>(std::atoi(next));

					index++;
				}

				else if (std::strcmp(current, "--pitch") == 0 && next[0])
				{
					options.spawn_pitch = static_cast<std::float_t>(std::atof(next));

					index++;
				}

				else if (std::strcmp(current, "--turn") == 0 && next[0])
				{
					options.spawn_turn = static_cast<std::float_t>(std::atof(next));

					index++;
				}

				else if (std::strcmp(current, "--advance") == 0 && next[0])
				{
					options.spawn_advance = static_cast<std::float_t>(std::atof(next));

					index++;
				}

				else if (std::strcmp(current, "--reload") == 0 && next[0])
				{
					options.reload_progress = std::clamp(static_cast<std::float_t>(std::atof(next)), 0.0f, 0.98f);

					index++;
				}

				else if (std::strcmp(current, "--item") == 0 && next[0])
				{
					options.test_item = static_cast<std::uint32_t>(std::atoi(next)) % structures::item_count;

					index++;
				}

				else if (std::strcmp(current, "--debug") == 0 && next[0])
				{
					renderer.debug_view = static_cast<std::uint32_t>(std::atoi(next));

					index++;
				}

				else if (std::strcmp(current, "--camera") == 0 && next[0])
				{
					options.camera_set = std::sscanf(next, "%f,%f,%f,%f,%f", &options.camera[0], &options.camera[1], &options.camera[2], &options.camera[3], &options.camera[4]) == 5;

					index++;
				}
			}

			LocalFree(arguments);
		}
	}
	/*
	//=====================================================================================
	*/
	bool application_c::startup(HINSTANCE instance)
	{
		if (platform.create(instance, options.dedicated == false))
		{
			if (options.dedicated)
			{
				state = structures::app_playing;

				return true;
			}

			platform.set_display_mode(options.windowed ? structures::display_mode_windowed : structures::display_mode_borderless);

			platform.pump();

			if (gpu.create(platform.window, static_cast<std::uint32_t>(platform.client_width), static_cast<std::uint32_t>(platform.client_height)) && pak.open((functions::executable_directory() + pak_file_name).c_str()))
			{
				gpu.vsync = false;

				if (font.create() && canvas.create() && hud.create() && menu.create())
				{
					testing = (options.capture[0] || options.walk_test || options.fight_test || options.gather_kind >= 0 || options.fell_test || options.marks_test || options.dead_test || options.base_test || options.farm_test || options.spring_test || options.camera_set || options.smoke || options.chart_test || options.test_inventory) && options.title_test == false && options.loading_test == false;

					menu.load_settings();

					platform.set_mouse_captured(false);

					previous_time = platform.time();

					DWORD length{ sizeof(client.name) };

					if (GetUserNameA(client.name, &length) == FALSE || client.name[0] == 0)
					{
						std::snprintf(client.name, sizeof(client.name), "%s", "Castaway");
					}

					if (options.player_name[0])
					{
						std::snprintf(client.name, sizeof(client.name), "%s", options.player_name);
					}

					std::snprintf(client.password, sizeof(client.password), "%s", options.password);

					client.load_identity();

					if (options.connect[0] && udp_socket_c::parse(options.connect, static_cast<std::uint16_t>(net_default_port), menu.join_address))
					{
						client.connect(menu.join_address);
					}

					return true;
				}
			}
		}

		logger.write("application: startup failed");

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool application_c::load_stage(std::uint32_t index)
	{
		const auto started{ platform.time() };

		auto result{ true };

		if (index == 0u)
		{
			result = materials.create(0u) && models.load() && characters.load();
		}

		else if (index == 1u)
		{
			result = materials.upload() && characters.upload();
		}

		else if (index == 2u)
		{
			result = sky.create() && renderer.create() && terrain.create() && foliage.create() && grass.create() && water.create();
		}

		else if (index == 3u)
		{
			if (actors.create() == false)
			{
				logger.write("application: character clips missing, actors disabled");
			}

			if (viewmodel.create() == false)
			{
				logger.write("application: first person arms unavailable");
			}

			if (atmosphere.create() == false)
			{
				logger.write("application: dynamic sky unavailable");
			}

			if (particles.create() == false)
			{
				logger.write("application: particles unavailable");
			}

			if (weather.create() == false)
			{
				logger.write("application: weather unavailable");
			}

			if (options.weather_test)
			{
				const auto& phase{ weather_phases[options.weather_test - 1u] };

				weather.forced = true;
				weather.cloud = weather.cloud_now = phase.cloud;
				weather.rain = weather.rain_now = phase.rain;
				weather.storm = weather.storm_now = phase.storm;
				weather.wetness = phase.rain > 0.0f ? 1.0f : 0.0f;
				weather.bolt_timer = 0.6f;
			}

			if (building.create() == false)
			{
				logger.write("application: building unavailable");
			}

			if (mixer.create() == false)
			{
				logger.write("application: audio unavailable");
			}

			else if (options.capture[0])
			{
				mixer.master->SetVolume(0.0f);
			}

			menu.apply_settings();

			if (options.quality >= 0)
			{
				renderer.default_settings(static_cast<std::uint32_t>(options.quality));
			}

			renderer.resize(gpu.width, gpu.height);

			renderer.apply_settings();
		}

		else if (index == 4u)
		{
			maps.load(options.map[0] ? options.map : "island");

			train.create();

			if (options.sky[0])
			{
				sky.select(options.sky);
			}

			else if (terrain.enabled)
			{
				atmosphere.enable(testing ? options.start_hours : title_hours);
			}
		}

		else if (index == 5u)
		{
			if (terrain.enabled && chart.create())
			{
				chart.open = options.chart_test;
			}
		}

		else
		{
			prepare_world();
		}

		logger.write("loading: stage %u %s %s in %.2f s", index, loading_stage_names[index], result ? "done" : "failed", platform.time() - started);

		return result;
	}
	/*
	//=====================================================================================
	*/
	void application_c::prepare_world()
	{
		spawn_seed ^= testing || options.walk_test ? 0u : static_cast<std::uint32_t>(GetTickCount64());
		viewmodel.inspect = options.inspect_hands;
		viewmodel.inspecting = options.showcase_angle >= 0.0f;
		viewmodel.inspect_yaw = degrees_to_radians(std::max(options.showcase_angle, 0.0f));
		viewmodel.inspect_idle = -1000.0f;

		survival.reset_knowledge();

		story.reset();

		story.step = std::min(options.goal_step, static_cast<std::uint32_t>(goal_count - 1u));

		respawn();

		if (options.gather_kind >= 0)
		{
			approach_node(static_cast<std::uint32_t>(options.gather_kind));
		}

		if (options.dead_test)
		{
			survival.harm = structures::death_frozen;

			survival.damage(maximum_health);
		}

		if (options.fell_test)
		{
			fell_node = approach_node(structures::node_tree);

			const auto back{ player.state.position - mathematics.flat_forward(player.yaw) * 11.0f };

			player.spawn({ back.x, terrain.height(back.x, back.z) + 0.05f, back.z }, player.yaw);

			player.pitch = 0.22f;
		}

		populate();

		if (options.base_test)
		{
			building.test_base(player.state.position + mathematics.flat_forward(player.yaw) * 1.5f, player.yaw);

			player.pitch = degrees_to_radians(options.spawn_pitch);

			if (options.keypad_test && building.locks.size())
			{
				hud.open_keypad(static_cast<std::int32_t>(building.locks.begin()->first), true);
			}
		}

		if (options.save_test)
		{
			const auto spot{ player.state.position + mathematics.flat_forward(player.yaw) * 2.5f };

			survival.slots[inventory_slots + survival.active_slot] = { structures::item_workbench_1, 1u, 1.0f, 0u };

			building.place({ { spot.x, terrain.height(spot.x, spot.z), spot.z }, player.yaw, structures::piece_workbench_1, -1, true, true });

			survival.give(structures::item_wood, 321u, false);

			story.step = 7u;
			story.day = 4u;

			const auto written{ save.write() };

			survival.reset();
			story.reset();
			building.clear();

			const auto loaded{ save.read() };

			logger.write("savetest: written %d loaded %d step %u day %u wood %u structures %zu bench %u", written ? 1 : 0, loaded ? 1 : 0, story.step, story.day, survival.count(structures::item_wood), building.placed.size(), building.workbench_tier(player.state.position));
		}

		if (options.spring_test && farming.springs.size())
		{
			auto nearest{ farming.springs[0] };

			for (const auto& spring : farming.springs)
			{
				nearest = mathematics.distance({ spring.x, spring.y, spring.z }, player.state.position) < mathematics.distance({ nearest.x, nearest.y, nearest.z }, player.state.position) ? spring : nearest;
			}

			player.spawn({ nearest.x + nearest.w + 1.6f, terrain.height(nearest.x + nearest.w + 1.6f, nearest.z) + 0.05f, nearest.z }, -half_pi);

			player.pitch = -0.5f;
		}

		if (options.farm_test)
		{
			const auto ahead{ mathematics.flat_forward(player.yaw) };
			const auto side{ mathematics.right_from_yaw(player.yaw) };
			const auto well{ player.state.position + ahead * 6.5f + side * 5.0f };

			survival.slots[inventory_slots + survival.active_slot] = { structures::item_well, 1u, 1.0f };

			building.place({ { well.x, terrain.height(well.x, well.z), well.z }, player.yaw, structures::piece_well, -1, true, true });

			for (auto index{ 0u }; index < 16u; index++)
			{
				const auto spot{ player.state.position + ahead * (3.0f + static_cast<std::float_t>(index / 4u) * 1.1f) + side * ((static_cast<std::float_t>(index % 4u) - 1.5f) * 1.1f) };

				farming.plant(1u + index % 4u, { spot.x, terrain.height(spot.x, spot.z), spot.z });

				farming.crops.back().growth = std::min(1.0f, 0.12f + static_cast<std::float_t>(index) / 12.0f);
				farming.crops.back().water = index == 5u ? 0.0f : 1.0f;
				farming.crops.back().dead = index == 6u;
			}

			survival.slots[inventory_slots + survival.active_slot] = { structures::item_potato, 6u, 1.0f };
			player.pitch = -0.42f;
		}

		if (options.fight_test && actors.list.size() > 1u)
		{
			const auto front{ player.state.position + mathematics.flat_forward(player.yaw) * 8.0f };

			actors.list[1].position = { front.x, terrain.height(front.x, front.z), front.z };
			actors.list[1].alerted = true;
		}

		if (options.camera_set)
		{
			fly_position = { options.camera[0], options.camera[1] + (options.camera_ground && terrain.enabled ? terrain.height(options.camera[0], options.camera[2]) : 0.0f), options.camera[2] };
			fly_yaw = degrees_to_radians(options.camera[3]);
			fly_pitch = degrees_to_radians(options.camera[4]);
		}

		if (testing || terrain.enabled == false)
		{
			pending = structures::app_playing;
			warmup = 0u;
			alive = true;
		}

		else
		{
			pending = structures::app_title;
			warmup = 48u;

			menu.plan_shots();

			menu.current_page = options.menu_page >= 1 && options.menu_page <= static_cast<std::int32_t>(structures::page_controls) ? static_cast<std::uint32_t>(options.menu_page) : structures::page_main;
			actors.passive = true;
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::shutdown()
	{
		if (alive && testing == false && survival.vitals.dead == false && state == structures::app_playing && client.connected() == false)
		{
			save.write();
		}

		client.close();

		mixer.destroy();

		building.destroy();

		viewmodel.destroy();

		train.clear();

		farming.destroy();

		chart.destroy();

		particles.destroy();

		weather.destroy();

		atmosphere.destroy();

		water.destroy();

		grass.destroy();

		foliage.destroy();

		terrain.destroy();

		renderer.destroy();

		sky.destroy();

		actors.clear();

		characters.destroy();

		models.destroy();

		materials.destroy();

		menu.destroy();

		hud.destroy();

		canvas.destroy();

		font.destroy();

		pak.close();

		gpu.destroy();

		platform.destroy();
	}
	/*
	//=====================================================================================
	*/
	void application_c::frame()
	{
		platform.pump();

		if (platform.resized && platform.minimized == false)
		{
			gpu.resize(static_cast<std::uint32_t>(platform.client_width), static_cast<std::uint32_t>(platform.client_height));

			renderer.resize(gpu.width, gpu.height);
		}

		const auto now{ platform.time() };

		const auto real_delta{ static_cast<std::float_t>(std::min(now - previous_time, 0.1)) };

		delta = options.capture[0] ? 1.0f / 60.0f : real_delta;

		previous_time = now;

		elapsed += delta;

		fps = mathematics.lerp(fps, real_delta > 0.0f ? 1.0f / real_delta : 0.0f, 0.05f);

		if (state == structures::app_loading && stage < std::size(loading_stage_names))
		{
			frame_loading();
		}

		else if (state == structures::app_loading && warmup == 0u && (pending == structures::app_playing || warm_clock >= loading_minimum))
		{
			state = pending;
			menu.shot = 0u;
			menu.shot_clock = 0.0f;

			platform.set_mouse_captured(state == structures::app_playing && options.capture[0] == 0);
		}

		else
		{
			frame_world();
		}

		if ((options.smoke || options.walk_test) && options.frames && frame_index >= options.frames)
		{
			running = false;
		}

		if (platform.quit_requested)
		{
			running = false;
		}

		if (frame_cap > 0.0f)
		{
			next_frame_time = std::max(next_frame_time + 1.0 / frame_cap, now);

			platform.sleep_until(next_frame_time);
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::frame_loading()
	{
		if (platform.minimized == false)
		{
			const FLOAT clear[4] = { 0.06f, 0.047f, 0.035f, 1.0f };

			gpu.wait_for_frame();

			gpu.context->ClearRenderTargetView(gpu.backbuffer_rtv, clear);

			canvas.begin(static_cast<std::float_t>(gpu.width), static_cast<std::float_t>(gpu.height));

			menu.draw_loading(stage, static_cast<std::uint32_t>(std::size(loading_stage_names)), chart.ready, delta);

			canvas.end(gpu.backbuffer_rtv);

			gpu.present();
		}

		if (load_stage(stage))
		{
			stage++;
		}

		else
		{
			running = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::frame_world()
	{
		client.update(delta);

		train.advance(delta);

		if (state == structures::app_title && client.connected() && client.synchronized && leaving <= 0.0f)
		{
			leaving = 0.001f;
		}

		if (testing && client.connected() && client.synchronized && client.placed == false)
		{
			player.spawn(client.authority.position, client.authority.yaw);

			client.placed = true;
		}

		if ((state == structures::app_playing || state == structures::app_waking) && client.state == structures::link_failed)
		{
			enter_title();

			menu.current_page = structures::page_servers;
		}

		const auto staging{ state == structures::app_loading };
		const auto overture{ state == structures::app_title || staging };

		if (state == structures::app_playing && platform.input.pressed[VK_ESCAPE] && paused == false && hud.chatting == false && hud.keypad_door < 0)
		{
			if (survival.inventory_open)
			{
				survival.inventory_open = false;

				platform.set_mouse_captured(options.capture[0] == 0);
			}

			else if (chart.open)
			{
				chart.open = false;

				platform.set_mouse_captured(options.capture[0] == 0);
			}

			else
			{
				paused = true;

				menu.current_page = structures::page_main;

				platform.set_mouse_captured(false);

				mixer.play_2d(structures::sound_ui_open, 0.45f, 0.8f);
			}

			platform.input.pressed[VK_ESCAPE] = false;
		}

		if (options.pause_test && state == structures::app_playing && frame_index == 30u)
		{
			paused = true;

			menu.current_page = options.menu_page >= 1 && options.menu_page <= static_cast<std::int32_t>(structures::page_controls) ? static_cast<std::uint32_t>(options.menu_page) : structures::page_main;
		}

		if (options.wake_test && state == structures::app_title && frame_index == 110u)
		{
			handle_action(structures::menu_wake);
		}

		const auto live{ state == structures::app_playing && paused == false };

		if (live && platform.input.pressed[VK_LBUTTON] && platform.mouse_captured == false && survival.inventory_open == false && chart.open == false && options.capture[0] == 0)
		{
			platform.set_mouse_captured(true);

			platform.input.pressed[VK_LBUTTON] = false;
		}

		if (live)
		{
			update_game();
		}

		client.flush(delta);

		if (overture)
		{
			menu.title_camera(delta, title_position, title_yaw, title_pitch);

			actors.passive = true;
			actors.focus = title_position;
		}

		if (state == structures::app_waking)
		{
			waking += delta;
		}

		if (paused == false)
		{
			update_player_actor();

			actors.update(delta);

			if (live)
			{
				projectiles.update(delta, platform.mouse_captured && survival.inventory_open == false && chart.open == false);

				if (client.connected())
				{
					loot.present(platform.mouse_captured && survival.inventory_open == false && chart.open == false && hud.chatting == false);
				}

				viewmodel.update(delta);
			}

			building.effects(delta);

			harvest.fell(delta);

			train.update(delta);

			particles.update(delta);

			weather.update(delta);

			atmosphere.update(delta);
		}

		mixer.update(delta);

		if (platform.minimized)
		{
			Sleep(16u);
		}

		else
		{
			gpu.wait_for_frame();

			if (overture)
			{
				renderer.begin_frame(title_position, title_yaw, title_pitch, 0.0f, delta);
			}

			else if (state == structures::app_waking)
			{
				const auto rise{ mathematics.smoothstep(2.1f, 4.4f, waking) };

				renderer.begin_frame(mathematics.lerp(player.state.position + structures::vec3_s{ 0.0f, 0.3f, 0.0f }, player.eye, rise), player.yaw + (1.0f - rise) * 0.55f, mathematics.lerp(1.0f, player.pitch, rise), (1.0f - rise) * 0.35f, delta);
			}

			else if (options.camera_set)
			{
				renderer.begin_frame(fly_position, fly_yaw, fly_pitch, 0.0f, delta);
			}

			else if (options.third_person)
			{
				renderer.begin_frame(third_person_camera(), player.yaw, player.pitch, 0.0f, delta);
			}

			else
			{
				renderer.begin_frame(player.eye, player.yaw + weapons.view_yaw, std::clamp(player.pitch + weapons.view_pitch, -1.55f, 1.55f), player.roll, delta);
			}

			actors.submit();

			building.submit();

			harvest.submit();

			farming.submit();

			projectiles.submit();

			train.submit();

			if (state == structures::app_playing && options.third_person == false && options.camera_set == false)
			{
				viewmodel.submit();
			}

			grass.constants.player = { player.state.position.x, player.state.position.y, player.state.position.z, state == structures::app_playing && options.camera_set == false ? grass_push_radius : 0.0f };

			renderer.render(gpu.backbuffer_rtv);

			canvas.begin(static_cast<std::float_t>(gpu.width), static_cast<std::float_t>(gpu.height));

			if (staging)
			{
				menu.draw_loading(stage, static_cast<std::uint32_t>(std::size(loading_stage_names)), chart.ready, delta);

				canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(mathematics.saturate((warm_clock - loading_minimum + loading_fade) / loading_fade) * 255.0f)));
			}

			else if (state == structures::app_title)
			{
				handle_action(menu.draw_title((alive && survival.vitals.dead == false) || (alive == false && save.exists()), delta));

				if (leaving > 0.0f)
				{
					canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(mathematics.saturate(leaving / wake_fade_time) * 255.0f)));
				}
			}

			else if (state == structures::app_waking)
			{
				menu.draw_waking(waking);
			}

			else
			{
				if (terrain.enabled && options.camera_set == false && options.inspect_hands < 0.0f)
				{
					hud.draw(delta);
				}

				if (paused)
				{
					handle_action(menu.draw_pause(delta));
				}
			}

			if (show_debug || options.camera_set || terrain.enabled == false)
			{
				draw_debug_overlay();
			}

			canvas.end(gpu.backbuffer_rtv);

			frame_index++;

			if (options.capture[0] && frame_index == options.frames)
			{
				gpu.capture(options.capture);

				logger.write("capture: camera %.2f,%.2f,%.2f,%.1f,%.1f", renderer.camera.position.x, renderer.camera.position.y, renderer.camera.position.z, player.yaw / degrees_to_radians(1.0f), player.pitch / degrees_to_radians(1.0f));

				running = false;
			}

			gpu.present();
		}

		if (leaving > 0.0f)
		{
			leaving += delta;

			if (leaving >= wake_fade_time)
			{
				begin_life();
			}
		}

		if (state == structures::app_waking && waking >= wake_time)
		{
			state = structures::app_playing;

			platform.set_mouse_captured(options.capture[0] == 0);
		}

		if (staging)
		{
			warmup = warmup > 0u ? warmup - 1u : 0u;
			warm_clock += delta;
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::update_game()
	{
		hud.update_chat(delta);

		if (platform.input.pressed[VK_F5])
		{
			options.third_person = options.third_person == false;
		}

		if (platform.input.pressed[VK_F1])
		{
			show_debug = show_debug == false;
		}

		if (platform.input.pressed[VK_F4] && survival.vitals.dead == false && client.connected() == false)
		{
			survival.give_kit();
		}

		update_survival();

		if (options.marks_test && frame_index == 5u)
		{
			const auto area{ chart.frame() };
			const auto scale{ area.w / static_cast<std::float_t>(chart_size) };
			const auto fell{ player.state.position + mathematics.flat_forward(player.yaw + 0.15f) * 60.0f };

			for (auto click{ 0u }; click < 5u; click++)
			{
				const auto index{ click < 3u ? click : 1u };
				const auto target{ player.state.position + mathematics.flat_forward(player.yaw - 0.35f + 0.33f * static_cast<std::float_t>(index)) * (90.0f + 115.0f * static_cast<std::float_t>(index)) };

				chart.pin(structures::vec2_s{ area.x, area.y } + chart.project(target.x, target.z) * scale);

				logger.write("marks: click %u at %.0f %.0f | pins %.0f,%.0f #%u  %.0f,%.0f #%u  %.0f,%.0f #%u", click, target.x, target.z, chart.pins[0].position.x, chart.pins[0].position.y, chart.pins[0].stamp, chart.pins[1].position.x, chart.pins[1].position.y, chart.pins[1].stamp, chart.pins[2].position.x, chart.pins[2].position.y, chart.pins[2].stamp);
			}

			chart.grave = { fell.x, fell.z };
			chart.grave_marked = true;
		}

		const auto charted{ chart.open };

		chart.update((platform.mouse_captured || chart.open) && survival.inventory_open == false);

		if (chart.open != charted)
		{
			platform.set_mouse_captured(chart.open == false && options.capture[0] == 0);
		}

		if (chart.open)
		{
			platform.input.mouse_delta = {};
			platform.input.down[VK_LBUTTON] = false;
			platform.input.down[VK_RBUTTON] = false;
			platform.input.pressed[VK_LBUTTON] = false;
			platform.input.pressed[VK_RBUTTON] = false;
		}

		if (options.camera_set)
		{
			update_fly_camera();
		}

		else if (options.net_test)
		{
			autotest.options_raid = options.raid_test;
			autotest.phase = options.ride_test && autotest.phase == structures::autotest_walk ? static_cast<std::uint32_t>(structures::autotest_ride) : autotest.phase;

			autotest.update(delta, frame_index);
		}

		else if (options.ride_test && train.ready)
		{
			if (frame_index == 5u)
			{
				const auto& kind{ train_vehicles[train_consist[1]] };

				train.clock = 40.0;

				train.place(train.clock);

				const auto seat{ train.pose(train.clock, 1u) };

				player.state.local = { 0.0f, kind.deck + 0.05f, -1.2f };
				player.state.position = mathematics.transform_point(player.state.local, seat);
				player.state.velocity = {};
				player.state.platform = 2u;
				player.state.flags |= structures::movement_on_ground | structures::movement_riding;
				player.previous = player.state;
				player.yaw = std::atan2(seat.row3(2u).x, seat.row3(2u).z) + degrees_to_radians(options.spawn_turn);
				player.pitch = degrees_to_radians(options.spawn_pitch);
			}

			platform.input.mouse_delta = {};
			platform.simulate(structures::bind_forward, frame_index > 400u && frame_index < 440u);
			platform.simulate(structures::bind_jump, frame_index == 600u);

			player.update(delta, true);

			if (frame_index % 60u == 0u)
			{
				logger.write("ride: frame %llu clock %.2f pos %.2f %.2f %.2f local %.3f %.3f %.3f platform %u flags %u train speed %.2f eye %.2f %.2f %.2f", frame_index, train.clock, player.state.position.x, player.state.position.y, player.state.position.z, player.state.local.x, player.state.local.y, player.state.local.z, player.state.platform, player.state.flags, train.speed, player.eye.x, player.eye.y, player.eye.z);
			}
		}

		else if (options.walk_test)
		{
			platform.simulate(structures::bind_forward, true);
			platform.simulate(structures::bind_sprint, (frame_index / 120u) % 2u == 1u);
			platform.simulate(structures::bind_jump, frame_index % 150u > 140u);
			platform.input.mouse_delta = { (frame_index / 200u) % 2u ? 3.0f : -2.0f, 0.0f };

			player.update(delta, true);

			if (frame_index % 30u == 0u)
			{
				logger.write("walk: frame %llu pos %.2f %.2f %.2f vel %.2f %.2f %.2f flags %u", frame_index, player.state.position.x, player.state.position.y, player.state.position.z, player.state.velocity.x, player.state.velocity.y, player.state.velocity.z, player.state.flags);
			}

		}

		else if (options.fight_test && actors.list.size() > 1u)
		{
			const auto& enemy{ actors.list[1] };
			const auto offset{ enemy.position + (enemy.dead ? mathematics.flat_forward(enemy.body_yaw) * -0.85f + structures::vec3_s{ 0.0f, 0.25f, 0.0f } : structures::vec3_s{ 0.0f, 1.25f, 0.0f }) - player.eye };

			player.yaw = std::atan2(offset.x, offset.z);
			player.pitch = std::atan2(offset.y, mathematics.length(structures::vec3_s{ offset.x, 0.0f, offset.z }));

			const auto bow{ weapons.weapon != structures::weapon_none && gun_models[weapons.weapon].action == structures::action_draw };

			platform.input.down[VK_LBUTTON] = bow ? frame_index > 40u && frame_index % 110u < 96u && enemy.dead == false : mathematics.length(offset) < 2.7f && enemy.dead == false;
			platform.input.down[VK_RBUTTON] = weapons.weapon != structures::weapon_none && bow == false && enemy.dead == false;
			platform.input.pressed[VK_LBUTTON] = weapons.weapon != structures::weapon_none && bow == false && enemy.dead == false && frame_index > 40u && frame_index % 12u == 0u;
			platform.simulate(structures::bind_use, enemy.dead && frame_index % 20u == 0u);
			platform.input.mouse_delta = {};

			player.update(delta, true);

			farming.update(delta, true);

			harvest.update(delta, true);

			combat.update(delta, true);

			building.update(delta, true);

			weapons.update(delta, true);

			if (frame_index % 30u == 0u)
			{
				logger.write("fight: frame %llu distance %.2f enemy health %.0f dead %d attack %.2f arms %.2f | player health %.1f dead %d | cloth %u", frame_index, mathematics.length(offset), enemy.health, enemy.dead ? 1 : 0, enemy.attack, enemy.arms, survival.vitals.health, survival.vitals.dead ? 1 : 0, survival.count(structures::item_cloth));
			}
		}

		else if (options.fell_test && frame_index == 30u && fell_node >= 0)
		{
			harvest.nodes[fell_node].fall = player.yaw + half_pi;

			harvest.topple(static_cast<std::uint32_t>(fell_node));
			harvest.deplete(static_cast<std::uint32_t>(fell_node));
		}

		else if (options.gather_kind >= 0)
		{
			platform.input.down[VK_LBUTTON] = frame_index > 20u && options.gather_kind != static_cast<std::int32_t>(structures::node_hemp) && options.gather_kind != static_cast<std::int32_t>(structures::node_berry);
			platform.input.down[VK_RBUTTON] = options.aim_test && frame_index > 50u;
			platform.simulate(structures::bind_use, frame_index % 40u == 30u);
			platform.input.mouse_delta = {};

			player.update(delta, true);

			farming.update(delta, true);

			harvest.update(delta, true);

			combat.update(delta, true);

			building.update(delta, true);

			weapons.update(delta, true);

			if (frame_index % 60u == 0u)
			{
				logger.write("gather: frame %llu wood %u stone %u metal %u sulfur %u cloth %u berries %u scrap %u", frame_index, survival.count(structures::item_wood), survival.count(structures::item_stone), survival.count(structures::item_metal_ore), survival.count(structures::item_sulfur_ore), survival.count(structures::item_cloth), survival.count(structures::item_berries), survival.count(structures::item_scrap));
			}
		}

		else
		{
			viewmodel.inspecting = viewmodel.inspecting || options.showcase_angle >= 0.0f;

			const auto hands_free{ (platform.mouse_captured || chart.open || options.capture[0] != 0) && survival.inventory_open == false && viewmodel.inspecting == false && story.ending == false && hud.chatting == false && hud.keypad_door < 0 };

			if (options.jam_progress >= 0.0f && weapons.weapon != structures::weapon_none)
			{
				weapons.state.flags |= structures::weapon_flag_jammed;
				weapons.state.clearing = options.jam_progress > 0.0f ? weapon_definitions[weapons.weapon].clear_time * (1.0f - options.jam_progress) + delta : 0.0f;
			}

			platform.input.down[VK_RBUTTON] = platform.input.down[VK_RBUTTON] || (options.aim_test && frame_index > 30u);
			platform.input.down[VK_LBUTTON] = platform.input.down[VK_LBUTTON] || (options.fire_test && frame_index > 60u);
			platform.input.down[platform.bindings[structures::bind_crouch]] = platform.held(structures::bind_crouch) || (options.dive_test && frame_index > 20u);

			if (options.reload_progress >= 0.0f && weapons.weapon != structures::weapon_none)
			{
				survival.slots[inventory_slots + survival.active_slot].loaded = 0u;
				weapons.state.reloading = weapon_definitions[weapons.weapon].reload * (1.0f - options.reload_progress) + delta;
			}

			player.update(delta, hands_free && survival.vitals.dead == false);

			const auto dry{ (player.state.flags & structures::movement_swimming) == 0u };

			story.update(delta);

			if (testing == false && alive && client.connected() == false)
			{
				save.tick(delta);
			}

			if (story.ending && platform.tapped(structures::bind_jump))
			{
				story.ending = false;
			}

			farming.update(delta, hands_free && chart.open == false && dry);

			harvest.update(delta, hands_free && dry);

			combat.update(delta, hands_free && dry);

			building.update(delta, hands_free && dry);

			weapons.update(delta, hands_free && dry);
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::enter_title()
	{
		state = structures::app_title;
		paused = false;
		leaving = 0.0f;

		survival.inventory_open = false;
		chart.open = false;
		menu.current_page = structures::page_main;
		actors.passive = true;

		chart.forget();

		menu.plan_shots();

		platform.set_mouse_captured(false);
	}
	/*
	//=====================================================================================
	*/
	void application_c::begin_life()
	{
		leaving = 0.0f;
		waking = 0.0f;
		state = structures::app_waking;
		alive = true;
		actors.passive = false;
		chart.open = false;
		survival.inventory_open = false;
		atmosphere.hours = atmosphere.enabled ? wake_hours : atmosphere.hours;

		survival.reset_knowledge();

		story.reset();

		respawn();

		if (client.connected())
		{
			player.spawn(client.authority.position, client.authority.yaw);
		}

		else
		{
			populate();
		}

		player.pitch = 0.0f;
		viewmodel.shown_item = structures::item_none;

		logger.write("application: a new castaway wakes at %.0f %.0f", player.state.position.x, player.state.position.z);
	}
	/*
	//=====================================================================================
	*/
	void application_c::resume_saved()
	{
		survival.reset_knowledge();

		story.reset();

		if (save.read())
		{
			alive = true;
			chart.open = false;
			survival.inventory_open = false;
			viewmodel.shown_item = structures::item_none;

			populate();

			if (survival.vitals.dead)
			{
				respawn();
			}

			logger.write("application: resumed day %u at %.0f %.0f", story.day, player.state.position.x, player.state.position.z);
		}

		else
		{
			begin_life();
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::handle_action(std::uint32_t action)
	{
		if (action == structures::menu_continue)
		{
			if (alive == false && save.exists())
			{
				resume_saved();
			}

			state = structures::app_playing;
			paused = false;
			actors.passive = false;

			platform.set_mouse_captured(options.capture[0] == 0);
		}

		else if (action == structures::menu_wake && leaving <= 0.0f)
		{
			leaving = 0.001f;
		}

		else if (action == structures::menu_resume)
		{
			paused = false;

			platform.set_mouse_captured(options.capture[0] == 0);

			mixer.play_2d(structures::sound_ui_close, 0.45f, 0.8f);
		}

		else if (action == structures::menu_title)
		{
			if (alive && testing == false && survival.vitals.dead == false && client.connected() == false)
			{
				save.write();
			}

			client.disconnect();

			enter_title();

			menu.current_page = structures::page_servers;
		}

		else if (action == structures::menu_quit)
		{
			running = false;
		}

		else if (action == structures::menu_play)
		{
			menu.current_page = structures::page_servers;
			menu.browse_clock = -100.0f;
		}

		else if (action == structures::menu_join)
		{
			client.connect(menu.join_address);
		}

		else if (action == structures::menu_host)
		{
			host_server();
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::host_server()
	{
		const auto path{ functions::executable_directory() + server_executable_name };
		const auto directory{ functions::executable_directory() };

		STARTUPINFOA startup{};
		PROCESS_INFORMATION process{};

		startup.cb = sizeof(startup);

		char command[MAX_PATH * 2]{};

		std::snprintf(command, sizeof(command), "\"%s\" --name \"%s's island\"", path.c_str(), client.name);

		if (CreateProcessA(path.c_str(), command, nullptr, nullptr, FALSE, CREATE_NEW_CONSOLE, nullptr, directory.c_str(), &startup, &process))
		{
			CloseHandle(process.hThread);
			CloseHandle(process.hProcess);

			std::snprintf(client.status, sizeof(client.status), "%s", "Starting a local server...");

			logger.write("application: started %s", path.c_str());
		}

		else
		{
			std::snprintf(client.status, sizeof(client.status), "Could not start %s", server_executable_name);

			logger.write("application: could not start %s (%lu)", path.c_str(), GetLastError());
		}

		menu.browse_clock = menu.clock - net_browse_interval + 1.5f;
	}
	/*
	//=====================================================================================
	*/
	void application_c::update_survival()
	{
		if (terrain.enabled && options.camera_set == false)
		{
			if (survival.vitals.dead)
			{
				survival.inventory_open = false;

				if (platform.tapped(structures::bind_jump) && client.connected())
				{
					client.request_respawn();
				}

				else if (platform.tapped(structures::bind_jump))
				{
					respawn();
				}
			}

			else
			{
				if (platform.tapped(structures::bind_inventory))
				{
					survival.inventory_open = survival.inventory_open == false;
					chart.open = false;

					mixer.play_2d(survival.inventory_open ? structures::sound_ui_open : structures::sound_ui_close, 0.5f, 1.0f);

					hud.drag_slot = -1;

					platform.set_mouse_captured(survival.inventory_open == false && options.capture[0] == 0);
				}

				for (auto key{ 0u }; key < hotbar_slots; key++)
				{
					if (platform.input.pressed['1' + key] && harvest.swinging == false)
					{
						survival.active_slot = key;
					}
				}

				if (platform.input.wheel != 0.0f && survival.inventory_open == false && harvest.swinging == false && viewmodel.inspecting == false)
				{
					survival.active_slot = (survival.active_slot + (platform.input.wheel < 0.0f ? 1u : hotbar_slots - 1u)) % hotbar_slots;
				}

				if (player.state.position.y < world.kill_height + 1.0f && client.connected() == false)
				{
					survival.damage(maximum_health);
				}
			}

			const auto speed{ mathematics.length(structures::vec3_s{ player.state.velocity.x, 0.0f, player.state.velocity.z }) };

			survival.remote = client.connected();
			survival.position = player.state.position;
			survival.underwater = (player.state.flags & structures::movement_underwater) != 0u;
			survival.climate.swimming = (player.state.flags & structures::movement_swimming) != 0u;
			survival.climate.air = survival.ambient(atmosphere.hours, weather.cloud_now, weather.rain_now, weather.storm_now);
			survival.climate.rain = weather.rain_now;

			survival.update(delta, 1.0f + std::clamp(speed / move_speed_run, 0.0f, 1.6f) * 0.6f);

			if (client.connected() && client.revived)
			{
				client.revived = false;

				respawn();
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::respawn()
	{
		if (client.connected())
		{
			player.spawn(client.authority.position, client.authority.yaw);
		}

		else if (building.bag >= 0 && building.placed[building.bag].destroyed == false)
		{
			const auto& bag{ building.placed[building.bag] };

			player.spawn(bag.position + structures::vec3_s{ 0.0f, 0.2f, 0.0f }, bag.yaw + pi);
		}

		else if (maps.spawns.size())
		{
			spawn_seed = mathematics.hash_u32(spawn_seed + 0x9E3779B9u);

			const auto& point{ maps.spawns[options.capture[0] ? 0u : spawn_seed % maps.spawns.size()] };
			const auto facing{ point.yaw + degrees_to_radians(options.spawn_turn) };
			const auto ahead{ point.position + mathematics.flat_forward(facing) * options.spawn_advance };

			player.spawn(options.spawn_advance > 0.0f ? structures::vec3_s{ ahead.x, std::max(terrain.height(ahead.x, ahead.z), sea_level - 1.4f), ahead.z } : point.position, facing);

			player.pitch = degrees_to_radians(options.spawn_pitch);
		}

		survival.reset();

		if (testing == false)
		{
			survival.give_kit();
		}

		if (options.test_item)
		{
			const auto gun{ item_definitions[options.test_item].weapon };

			survival.slots[inventory_slots] = { options.test_item, 1u, 1.0f, gun ? weapon_definitions[gun].capacity : 0u };

			if (gun)
			{
				survival.give(weapon_definitions[gun].ammo, 40u, false);
			}
		}

		if (options.test_inventory)
		{
			survival.give(structures::item_wood, 650u, false);
			survival.give(structures::item_stone, 240u, false);
			survival.give(structures::item_cloth, 45u, false);
			survival.give(structures::item_berries, 7u, false);
			survival.give(structures::item_metal_ore, 60u, false);
			survival.craft(0u);
			survival.craft(6u);

			survival.inventory_open = true;
		}

		harvest.swinging = false;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t application_c::approach_node(std::uint32_t kind)
	{
		auto best{ -1 };
		auto best_distance{ FLT_MAX };

		for (auto index{ 0u }; index < harvest.nodes.size(); index++)
		{
			if (const auto distance{ mathematics.distance(harvest.nodes[index].position, player.state.position) }; harvest.nodes[index].kind == kind && distance < best_distance)
			{
				best = static_cast<std::int32_t>(index);
				best_distance = distance;
			}
		}

		if (best >= 0)
		{
			const auto& node{ harvest.nodes[best] };
			const auto away{ mathematics.normalize(structures::vec3_s{ player.state.position.x - node.position.x, 0.0f, player.state.position.z - node.position.z }) };
			const auto stand{ node.position + away * (node.radius + 0.9f) };
			const auto target_height{ kind == structures::node_tree || kind == structures::node_dead_tree ? 1.1f : (kind == structures::node_hemp || kind == structures::node_berry ? 0.5f : 0.35f) };

			player.spawn({ stand.x, terrain.height(stand.x, stand.z) + 0.05f, stand.z }, std::atan2(-away.x, -away.z));

			player.pitch = -std::atan2(terrain.height(stand.x, stand.z) + player_eye_height - (node.position.y + target_height), node.radius + 0.9f);

			logger.write("gather: node %d kind %u at %.1f %.1f %.1f, %.0f m from spawn", best, kind, node.position.x, node.position.y, node.position.z, best_distance);
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	void application_c::populate()
	{
		actors.clear();

		player_actor = UINT32_MAX;

		if (actors.spawn(viewmodel_character, player.state.position, player.yaw, structures::actor_behavior_player))
		{
			player_actor = static_cast<std::uint32_t>(actors.list.size() - 1u);
		}

		if (terrain.enabled == false)
		{
			for (auto index{ 0u }; index < 8u; index++)
			{
				const auto angle{ static_cast<std::float_t>(index) / 8.0f * two_pi };

				actors.spawn(character_roster[index % std::size(character_roster)], { -5.0f + std::sin(angle) * 9.0f, 0.0f, std::cos(angle) * 12.0f }, angle + pi, structures::actor_behavior_wander);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::update_player_actor()
	{
		if (player_actor < actors.list.size())
		{
			auto& body{ actors.list[player_actor] };

			body.position = mathematics.lerp(player.previous.position, player.state.position, std::clamp(player.accumulator / tick_interval, 0.0f, 1.0f));
			body.velocity = player.state.velocity;
			body.look_yaw = player.yaw;
			body.look_pitch = player.pitch;
			body.crouched = (player.state.flags & structures::movement_crouched) != 0u;
			body.grounded = (player.state.flags & structures::movement_on_ground) != 0u;
			body.hidden = options.third_person == false && options.camera_set == false;
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s application_c::third_person_camera()
	{
		const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };
		const auto right{ mathematics.right_from_yaw(player.yaw) };
		const auto desired{ player.eye - forward * third_person_distance + right * third_person_side + structures::vec3_s{ 0.0f, third_person_height, 0.0f } };

		return world.trace(player.eye, desired, { 0.15f, 0.15f, 0.15f }, structures::contents_solid).end;
	}
	/*
	//=====================================================================================
	*/
	void application_c::update_fly_camera()
	{
		if (platform.mouse_captured)
		{
			fly_yaw += platform.input.mouse_delta.x * 0.0022f;
			fly_pitch = mathematics.clamp(fly_pitch - platform.input.mouse_delta.y * 0.0022f, -1.55f, 1.55f);

			const auto forward{ mathematics.forward_from_angles(fly_yaw, fly_pitch) };
			const auto right{ mathematics.right_from_yaw(fly_yaw) };
			const auto speed{ (platform.held(structures::bind_sprint) ? 16.0f : 5.0f) * delta };

			if (platform.held(structures::bind_forward))
			{
				fly_position += forward * speed;
			}

			if (platform.held(structures::bind_back))
			{
				fly_position -= forward * speed;
			}

			if (platform.held(structures::bind_right))
			{
				fly_position += right * speed;
			}

			if (platform.held(structures::bind_left))
			{
				fly_position -= right * speed;
			}

			if (platform.held(structures::bind_jump))
			{
				fly_position.y += speed;
			}

			if (platform.held(structures::bind_crouch))
			{
				fly_position.y -= speed;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void application_c::draw_debug_overlay()
	{
		const auto s{ canvas.scale };

		char line[256]{};

		std::snprintf(line, sizeof(line), "ZERO POINT  |  %s  |  %ux%u  |  %.0f fps  %.2f ms", gpu.adapter_name, renderer.width, renderer.height, fps, fps > 0.0f ? 1000.0f / fps : 0.0f);

		canvas.text_shadowed(structures::font_condensed, { 16.0f * s, 12.0f * s }, 22.0f * s, functions::rgba(230u, 240u, 250u, 230u), line, structures::align_left);

		std::snprintf(line, sizeof(line), "pos %.2f %.2f %.2f  speed %.2f  %s%s%s  yaw %.0f  pitch %.0f", player.state.position.x, player.state.position.y, player.state.position.z, mathematics.length(structures::vec3_s{ player.state.velocity.x, 0.0f, player.state.velocity.z }), (player.state.flags & structures::movement_on_ground) ? "ground " : "air ", (player.state.flags & structures::movement_crouched) ? "crouch " : "", (player.state.flags & structures::movement_noclip) ? "noclip" : "", radians_to_degrees(player.yaw), radians_to_degrees(player.pitch));

		canvas.text_shadowed(structures::font_mono, { 16.0f * s, 40.0f * s }, 18.0f * s, functions::rgba(150u, 220u, 170u, 220u), line, structures::align_left);
	}
}

//=====================================================================================
