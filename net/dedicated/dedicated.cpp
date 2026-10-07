
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	dedicated_c dedicated;

	std::int32_t dedicated_c::run(std::int32_t count, char** arguments)
	{
		parse(count, arguments);

		logger.initialize(server_log_file_name, true);

		SetConsoleTitleA("Zero Point dedicated server");

		SetConsoleCtrlHandler(control, TRUE);

		timer = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS);
		precise = timer != nullptr;
		timer = precise ? timer : CreateWaitableTimerExW(nullptr, nullptr, 0u, TIMER_ALL_ACCESS);
		nudge = CreateEventW(nullptr, FALSE, FALSE, nullptr);

		if (precise == false)
		{
			timeBeginPeriod(1u);
		}

		jobs.start();

		auto result{ 1 };

		logger.write("zero point dedicated server starting (%u worker threads)", jobs.thread_count());

		if (load())
		{
			if (testing)
			{
				test_movement();

				result = 0;
			}

			else if (server.start(port, name, map, maximum))
			{
				logger.write("server: %s", server.socket.watch() ? "sleeping until a packet arrives or a tick is due" : "polling the network every millisecond");

				admin.load();

				if (forced_weather >= 0)
				{
					server.set_weather(static_cast<std::uint32_t>(forced_weather), weather_forced_duration);
				}

				server.add_bots(bots);

				running = true;

				std::thread(&dedicated_c::read_console, this).detach();

				loop();

				server.stop();

				result = 0;
			}
		}

		logger.write("zero point dedicated server stopped");

		jobs.stop();

		if (precise == false)
		{
			timeEndPeriod(1u);
		}

		for (const auto handle : { timer, nudge })
		{
			if (handle)
			{
				CloseHandle(handle);
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::parse(std::int32_t count, char** arguments)
	{
		for (auto index{ 1 }; index < count; index++)
		{
			const auto has_next{ index + 1 < count };

			if (std::strcmp(arguments[index], "--port") == 0 && has_next)
			{
				port = static_cast<std::uint16_t>(std::clamp(std::atoi(arguments[++index]), 1, 65535));
			}

			else if (std::strcmp(arguments[index], "--name") == 0 && has_next)
			{
				std::snprintf(name, sizeof(name), "%s", arguments[++index]);
			}

			else if (std::strcmp(arguments[index], "--map") == 0 && has_next)
			{
				std::snprintf(map, sizeof(map), "%s", arguments[++index]);
			}

			else if (std::strcmp(arguments[index], "--max") == 0 && has_next)
			{
				maximum = static_cast<std::uint32_t>(std::clamp(std::atoi(arguments[++index]), 1, static_cast<std::int32_t>(net_maximum_players)));
			}

			else if (std::strcmp(arguments[index], "--bots") == 0 && has_next)
			{
				bots = static_cast<std::uint32_t>(std::clamp(std::atoi(arguments[++index]), 0, static_cast<std::int32_t>(net_maximum_players)));
			}

			else if (std::strcmp(arguments[index], "--movetest") == 0)
			{
				testing = true;
			}

			else if (std::strcmp(arguments[index], "--spawn") == 0 && has_next)
			{
				server.forced_spawn = std::atoi(arguments[++index]);
			}

			else if (std::strcmp(arguments[index], "--ride") == 0)
			{
				server.forced_ride = true;
			}

			else if (std::strcmp(arguments[index], "--herd-near") == 0)
			{
				server.forced_herd = true;
			}

			else if (std::strcmp(arguments[index], "--weather") == 0 && has_next)
			{
				forced_weather = std::clamp(std::atoi(arguments[++index]), 0, static_cast<std::int32_t>(std::size(weather_phases)) - 1);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool dedicated_c::load()
	{
		const auto started{ std::chrono::steady_clock::now() };

		auto result{ false };

		if (pak.open((functions::executable_directory() + pak_file_name).c_str()))
		{
			materials.create(0u);

			if (models.load() && maps.load(map))
			{
				result = true;

				train.create();

				vehicles.create();

				vehicles.populate();

				fauna.populate();

				if (testing == false)
				{
					persist.read();
				}

				const auto freed{ models.strip() + builder.strip() + terrain.strip() };

				logger.write("server: world \"%s\" ready in %.1f s (%zu spawns, %zu brushes), %.0f MB of render data released", map, std::chrono::duration<std::double_t>(std::chrono::steady_clock::now() - started).count(), maps.spawns.size(), world.brushes.size(), static_cast<std::double_t>(freed) / 1048576.0);
			}
		}

		if (result == false)
		{
			logger.write("server: could not load the world (is %s next to the server?)", pak_file_name);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::loop()
	{
		auto previous{ std::chrono::steady_clock::now() };

		while (running)
		{
			const auto now{ std::chrono::steady_clock::now() };
			const auto delta{ std::min(std::chrono::duration<std::float_t>(now - previous).count(), net_delta_limit) };

			previous = now;

			server.update(delta);

			std::vector<std::string> lines;

			{
				std::lock_guard<std::mutex> guard{ console_mutex };

				lines.swap(console_lines);
			}

			for (const auto& line : lines)
			{
				execute(line);
			}

			pause(server.due());
		}
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::pause(std::float_t seconds)
	{
		const HANDLE handles[3]{ timer, nudge, server.socket.signal };

		LARGE_INTEGER due{};

		due.QuadPart = -static_cast<LONGLONG>(static_cast<std::double_t>(seconds) * 10000000.0);

		if (due.QuadPart < 0)
		{
			if (SetWaitableTimer(timer, &due, 0, nullptr, nullptr, FALSE) == FALSE || WaitForMultipleObjects(server.dormant ? 3u : 2u, handles, FALSE, INFINITE) == WAIT_FAILED)
			{
				Sleep(1u);
			}

			WSAResetEvent(server.socket.signal);
		}
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::read_console()
	{
		char line[256]{};

		while (running && std::fgets(line, sizeof(line), stdin))
		{
			line[std::strcspn(line, "\r\n")] = 0;

			{
				std::lock_guard<std::mutex> guard{ console_mutex };

				console_lines.emplace_back(line);
			}

			SetEvent(nudge);
		}
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::execute(const std::string& line)
	{
		const auto space{ line.find(' ') };
		const auto word{ line.substr(0u, space) };
		const auto rest{ space == std::string::npos ? std::string{} : line.substr(space + 1u) };

		if (word == "quit" || word == "exit" || word == "stop")
		{
			running = false;
		}

		else if (word == "status")
		{
			status();
		}

		else if (word == "say" && rest.size())
		{
			server.chat(-1, rest.c_str());
		}

		else if (word == "bots")
		{
			server.add_bots(static_cast<std::uint32_t>(std::max(std::atoi(rest.c_str()), 0)));
		}

		else if (admin.command(line, -1) == false && word.size())
		{
			logger.write("commands: status, say <text>, bots <count>, kick <name|id>, ban <name|id>, unban <name>, bans, admin <name>, unadmin <name>, whitelist <on|off>, allow <name>, disallow <name>, password <text|off>, forget <name>, weather <clear|overcast|rainy|stormy>, time <hours>, quit");
		}
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::status()
	{
		logger.write("server: \"%s\" on udp %u, %u/%u players, uptime %.0f s, tick %.2f ms", server.name, server.socket.port, server.player_count, server.maximum, server.clock, server.tick_cost * 1000.0f);

		for (auto index{ 0 }; index < static_cast<std::int32_t>(server.clients.size()); index++)
		{
			const auto& peer{ server.clients[index] };

			if (peer.active && peer.bot == false)
			{
				char text[32]{};

				udp_socket_c::format(peer.connection.address, text, sizeof(text));

				logger.write("  %3d  %-24s %-22s ping %4.0f ms  at %.0f %.0f %.0f", index, peer.name, text, peer.connection.rtt * 1000.0f, peer.state.position.x, peer.state.position.y, peer.state.position.z);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_movement()
	{
		logger.write("movetest: run %.2f sprint %.2f crouch %.2f jump %.2f gravity %.1f walkable %.2f step %.2f", move_speed_run, move_speed_sprint, move_speed_crouch, move_jump_velocity, move_gravity, move_walkable, move_step_height);

		test_terrain();

		test_bhop();

		test_crouch();

		test_slopes();

		test_privilege();

		test_climate();

		test_train();
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_train()
	{
		if (train.ready)
		{
			const auto wagon{ 1u };
			const auto& kind{ train_vehicles[train_consist[wagon]] };
			const auto deck{ structures::vec3_s{ 0.0f, kind.deck + 0.05f, 0.0f } };

			structures::movement_state_s state{};
			structures::movement_state_s twin{};

			auto time{ 4.0 };
			auto rate{ 0.0f };
			auto drift{ 0.0f };
			auto rest{ structures::vec3_s{} };

			train.place(time);

			movement.reset(state, mathematics.transform_point(deck, train.pose(time, wagon)), 0.0f);

			twin = state;

			const auto origin{ state.position };

			for (auto tick{ 0u }; tick < 2400u; tick++)
			{
				time += tick_interval;

				movement.simulate(state, timed_command(time, 0.0f, 0.0f, 0u));

				train.place(time - 0.37);

				movement.simulate(twin, timed_command(time, 0.0f, 0.0f, 0u));

				rest = tick == 30u ? state.local : rest;
				drift = tick > 30u ? std::max(drift, mathematics.length(structures::vec3_s{ state.local.x - rest.x, 0.0f, state.local.z - rest.z })) : drift;
			}

			train.travel(time, rate);

			logger.write("movetest train: idle ride 40 s | platform %u flags %u | carried %.1f m, train speed %.2f m/s | seat drift %.4f m | twin offset %.6f m", state.platform, state.flags, mathematics.distance(state.position, origin), rate, drift, mathematics.distance(state.position, twin.position));

			const auto seat{ state.local };

			auto apex{ 0.0f };

			for (auto tick{ 0u }; tick < 120u; tick++)
			{
				time += tick_interval;

				movement.simulate(state, timed_command(time, 0.0f, 0.0f, tick == 0u ? structures::button_jump : 0u));

				apex = std::max(apex, state.local.y - seat.y);
			}

			logger.write("movetest train: jump at speed | apex %.2f m | landed %.4f m from the take-off spot | platform %u on ground %d", apex, mathematics.length(state.local - seat), state.platform, (state.flags & structures::movement_on_ground) ? 1 : 0);

			const auto heading{ std::atan2(train.posed[wagon].row3(2u).x, train.posed[wagon].row3(2u).z) };

			for (auto tick{ 0u }; tick < 30u; tick++)
			{
				time += tick_interval;

				movement.simulate(state, timed_command(time, heading, 1.0f, 0u));
			}

			logger.write("movetest train: walked along the deck | moved %.2f m forward on the wagon | relative speed %.2f m/s | platform %u", state.local.z - seat.z, mathematics.length(state.velocity), state.platform);

			auto left{ 0u };
			auto damage{ 0.0f };
			auto landing{ 0.0f };

			for (auto tick{ 0u }; tick < 240u && damage <= 0.0f; tick++)
			{
				time += tick_interval;

				movement.simulate(state, timed_command(time, heading + half_pi, 1.0f, 0u));

				left = state.platform == 0u && left == 0u ? tick : left;
				damage = state.platform == 0u ? movement.fall_damage(state) : damage;
				landing = state.platform == 0u && (state.flags & structures::movement_landed) ? state.landing_speed : landing;
			}

			logger.write("movetest train: stepped off at speed | left the wagon after %u ticks | ground speed %.2f m/s | tumble speed %.2f | damage %.0f", left, mathematics.length(structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z }), landing, damage);

			const auto ahead{ train.point(train.travel(time, rate) + 40.0) };

			structures::vec3_s shove{};

			auto blow{ 0.0f };
			auto waited{ 0u };

			movement.reset(state, ahead + structures::vec3_s{ 0.0f, rail_head + 0.1f, 0.0f }, 0.0f);

			for (auto tick{ 0u }; tick < 600u && blow <= 0.0f; tick++)
			{
				time += tick_interval;

				movement.simulate(state, timed_command(time, 0.0f, 0.0f, 0u));

				blow = train.strike(state, time, shove);
				waited = tick;
			}

			logger.write("movetest train: stood on the track 40 m ahead | struck after %.1f s | blow %.0f | shoved at %.1f m/s | pushed %.2f m before the hit", static_cast<std::float_t>(waited) * tick_interval, blow, mathematics.length(shove), mathematics.distance(state.position, ahead));
		}

		else
		{
			logger.write("movetest train: no railway on this map");
		}
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_climate()
	{
		auto position{ structures::vec3_s{} };
		auto found{ false };

		for (auto attempt{ 0u }; attempt < 20000u && found == false; attempt++)
		{
			found = find_ground(0.97f, position);
		}

		survival_c supplier{};

		supplier.slots[inventory_slots] = { structures::item_campfire, 1u, 1.0f, 0u };
		supplier.slots[inventory_slots + 1u] = { structures::item_building_plan, 1u, 1.0f, 0u };
		supplier.slots[0] = { structures::item_wood, 1000u, 1.0f, 0u };

		const auto fire_spot{ position + structures::vec3_s{ 12.0f, 0.0f, 0.0f } };
		const auto roof_spot{ position + structures::vec3_s{ 0.0f, 0.0f, 12.0f } };

		building.place({ fire_spot, 0.0f, structures::piece_campfire, -1, true, true }, supplier, 0u, 0u);

		building.containers.back().burning = true;

		building.place({ roof_spot + structures::vec3_s{ 0.0f, building_height, 0.0f }, 0.0f, structures::piece_floor, -1, true, true }, supplier, 1u, 0u);

		const structures::vec3_s spots[4] = { position, fire_spot + structures::vec3_s{ 1.0f, 0.0f, 0.0f }, roof_spot, position };
		const char* names[4] = { "storm night, open", "storm night, by a campfire", "storm night, under a roof", "clear afternoon, open" };

		for (auto scene{ 0u }; scene < 4u; scene++)
		{
			survival_c subject{};

			const auto stormy{ scene < 3u };

			subject.position = spots[scene];
			subject.climate.air = subject.ambient(stormy ? 3.0f : 14.0f, stormy ? 1.0f : 0.08f, stormy ? 1.0f : 0.0f, stormy ? 1.0f : 0.0f);
			subject.climate.rain = stormy ? 1.0f : 0.0f;

			subject.reset();

			auto minute{ subject.climate };

			for (auto tick{ 0u }; tick < 300u * 30u && subject.vitals.dead == false; tick++)
			{
				subject.update(1.0f / 30.0f, 1.0f);

				minute = tick == 60u * 30u ? subject.climate : minute;
			}

			logger.write("movetest climate: %s | air %.1f C | after 1 min wet %.0f%% felt %.1f C | after 5 min wet %.0f%% felt %.1f C health %.0f calories %.0f%s", names[scene], subject.climate.air, minute.wetness * 100.0f, minute.temperature, subject.climate.wetness * 100.0f, subject.climate.temperature, subject.vitals.health, subject.vitals.calories, subject.vitals.dead ? " (died of the cold)" : "");
		}
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_privilege()
	{
		auto position{ structures::vec3_s{} };
		auto found{ false };

		for (auto attempt{ 0u }; attempt < 20000u && found == false; attempt++)
		{
			found = find_ground(0.97f, position);
		}

		survival_c owner{};

		owner.slots[inventory_slots] = { structures::item_cupboard, 1u, 1.0f, 0u };
		owner.slots[inventory_slots + 1u] = { structures::item_wooden_door, 1u, 1.0f, 0u };

		const auto alpha{ mathematics.hash_text("alpha") };
		const auto bravo{ mathematics.hash_text("bravo") };
		const auto first{ static_cast<std::uint32_t>(building.placed.size()) };

		building.place({ position, 0.0f, structures::piece_cupboard, -1, true, true }, owner, 0u, alpha);
		building.place({ position + structures::vec3_s{ 3.0f, 0.0f, 0.0f }, 0.0f, structures::piece_storage_box, -1, true, true }, owner, 1u, alpha);

		const auto close_spot{ position + structures::vec3_s{ 6.0f, 0.0f, 0.0f } };
		const auto distant_spot{ position + structures::vec3_s{ cupboard_range + 5.0f, 0.0f, 0.0f } };
		const auto box{ first + 1u };

		logger.write("movetest privilege: owner builds near %d, stranger near %d, stranger far %d | owner opens %d, stranger opens %d", building.privileged(close_spot, alpha) ? 1 : 0, building.privileged(close_spot, bravo) ? 1 : 0, building.privileged(distant_spot, bravo) ? 1 : 0, building.accessible(box, alpha) ? 1 : 0, building.accessible(box, bravo) ? 1 : 0);

		building.authorize(first, bravo);

		logger.write("movetest privilege: after authorizing bravo: stranger near %d, stranger opens %d", building.privileged(close_spot, bravo) ? 1 : 0, building.accessible(box, bravo) ? 1 : 0);

		owner.slots[inventory_slots + 2u] = { structures::item_building_plan, 1u, 1.0f, 0u };
		owner.slots[0] = { structures::item_wood, 1000u, 1.0f, 0u };

		auto foundation{ 0u };

		for (auto tier{ 0u }; tier < building_tier_count; tier++)
		{
			building.place({ position + structures::vec3_s{ static_cast<std::float_t>(tier) * 3.0f, 0.2f, 6.0f }, 0.0f, structures::piece_foundation, -1, true, true }, owner, 2u, alpha);

			foundation = static_cast<std::uint32_t>(building.placed.size() - 1u);

			for (auto step{ 0u }; step < tier; step++)
			{
				building.upgrade(foundation);
			}

			const auto before{ building.placed[foundation].health };

			building.damage(building.placed[foundation].first_brush, 20.0f, true);

			logger.write("movetest tiers: %s foundation health %.0f / %.0f, 20 bullet damage took %.1f, surface %u", building_tiers[building.placed[foundation].tier].name, before, building.durability(foundation), before - building.placed[foundation].health, world.brushes[building.placed[foundation].first_brush].surface);
		}

		building.place({ position + structures::vec3_s{ 0.0f, 0.2f, cupboard_range + 15.0f }, 0.0f, structures::piece_foundation, -1, true, true }, owner, 2u, alpha);

		const auto exposed{ static_cast<std::uint32_t>(building.placed.size() - 1u) };
		const auto sheltered_before{ building.placed[foundation].health };

		building.decay(3600.0f);

		logger.write("movetest decay: one hour without a cupboard left %.0f / %.0f, under a cupboard %.0f -> %.0f", building.placed[exposed].health, building.durability(exposed), sheltered_before, building.placed[foundation].health);

		building.place({ position + structures::vec3_s{ 0.0f, 0.2f, -6.0f }, 0.0f, structures::piece_foundation, -1, true, true }, owner, 2u, alpha);

		const auto base{ static_cast<std::uint32_t>(building.placed.size() - 1u) };

		building.place({ building.placed[base].position + structures::vec3_s{ 0.0f, 0.0f, -1.5f }, 0.0f, structures::piece_doorway, static_cast<std::int32_t>(base), true, true }, owner, 2u, alpha);

		const auto frame{ static_cast<std::uint32_t>(building.placed.size() - 1u) };

		owner.slots[inventory_slots + 3u] = { structures::item_wooden_door, 1u, 1.0f, 0u };

		building.place({ building.placed[frame].position, building.placed[frame].yaw, structures::piece_door, static_cast<std::int32_t>(frame), true, true }, owner, 3u, alpha);

		const auto door{ static_cast<std::uint32_t>(building.placed.size() - 1u) };
		const auto attached{ building.attach_lock(door, alpha) };
		const auto uncoded{ building.accessible(door, bravo) };
		const auto set{ building.enter_code(door, alpha, 1234u) };
		const auto wrong{ building.enter_code(door, bravo, 1111u) };
		const auto right{ building.enter_code(door, bravo, 1234u) };
		const auto guest{ building.accessible(door, bravo) };
		const auto rekey{ building.enter_code(door, alpha, 4321u) };

		logger.write("movetest locks: attached %d | stranger opens %d | set %d wrong %d right %d | stranger after the code %d | owner rekeys %d, stranger after rekey %d", attached ? 1 : 0, uncoded ? 1 : 0, set, wrong, right, guest ? 1 : 0, rekey, building.accessible(door, bravo) ? 1 : 0);
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_slopes()
	{
		auto idle_runs{ 0u };
		auto steep_runs{ 0u };
		auto drift{ 0.0f };
		auto climbed{ 0.0f };
		auto slid{ 0.0f };

		for (auto attempt{ 0u }; attempt < 200000u && (idle_runs < 40u || steep_runs < 40u); attempt++)
		{
			const auto size{ static_cast<std::float_t>(terrain.header.resolution - 1u) };
			const auto x{ terrain.header.origin + random() * size };
			const auto z{ terrain.header.origin + random() * size };
			const auto ground{ terrain.height(x, z) };
			const auto normal{ terrain.normal(x, z) };

			if (terrain.enabled && ground > sea_level + 1.5f)
			{
				structures::movement_state_s state{};

				if (normal.y > move_walkable + 0.03f && normal.y < 0.9f && idle_runs < 40u)
				{
					movement.reset(state, { x, ground + 0.05f, z }, 0.0f);

					for (auto tick{ 0u }; tick < 30u; tick++)
					{
						movement.simulate(state, test_command(0.0f, 0.0f, 0.0f, 0u));
					}

					const auto rest{ state.position };

					for (auto tick{ 0u }; tick < 600u; tick++)
					{
						movement.simulate(state, test_command(0.0f, 0.0f, 0.0f, 0u));
					}

					drift = std::max(drift, mathematics.length(state.position - rest));

					idle_runs++;
				}

				else if (normal.y > 0.25f && normal.y < move_walkable - 0.06f && steep_runs < 40u)
				{
					const auto uphill{ std::atan2(-normal.x, -normal.z) };

					movement.reset(state, { x, ground + 0.05f, z }, uphill);

					const auto start{ state.position.y };

					auto peak{ start };
					auto summit{ state.position };
					auto steepest{ 1.0f };

					for (auto tick{ 0u }; tick < 180u; tick++)
					{
						movement.simulate(state, test_command(uphill, 1.0f, 0.0f, structures::button_sprint));

						if (state.position.y > peak)
						{
							peak = state.position.y;
							summit = state.position;
							steepest = std::min(steepest, state.flags & structures::movement_on_ground ? state.ground_normal.y : 1.0f);
						}
					}

					if (peak - start > 1.0f)
					{
						logger.write("movetest climb: from %.1f %.1f %.1f (normal y %.2f) up %.2f m to %.1f %.1f %.1f (terrain normal y %.2f, steepest ground %.2f)", x, ground, z, normal.y, peak - start, summit.x, summit.y, summit.z, terrain.normal(summit.x, summit.z).y, steepest);
					}

					climbed = std::max(climbed, peak - start);

					slid += start - state.position.y;

					steep_runs++;
				}
			}
		}

		logger.write("movetest slopes: idle drift %.4f m over 10 s (%u runs) | steep: max climb %.2f m, average slide %.2f m (%u runs)", drift, idle_runs, climbed, slid / static_cast<std::float_t>(std::max(steep_runs, 1u)), steep_runs);
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_terrain()
	{
		auto samples{ 0u };
		auto ticks{ 0u };
		auto airborne{ 0u };
		auto launches{ 0u };
		auto measured{ 0u };
		auto deflected{ 0u };
		auto blocked{ 0u };
		auto terrain_hits{ 0u };
		auto brush_hits{ 0u };
		auto reported{ 0u };
		auto highest{ 0.0f };
		auto rising{ 0.0f };
		auto speed{ 0.0f };
		auto worst{ 0.0f };
		auto worst_at{ structures::vec3_s{} };

		for (auto attempt{ 0u }; attempt < 20000u && samples < 400u; attempt++)
		{
			auto position{ structures::vec3_s{} };

			if (find_ground(0.8f, position))
			{
				const auto yaw{ random() * two_pi };
				const auto heading{ samples % 8u };
				const auto input_forward{ heading == 0u || heading == 1u || heading == 7u ? 1.0f : (heading >= 3u && heading <= 5u ? -1.0f : 0.0f) };
				const auto input_side{ heading >= 1u && heading <= 3u ? 1.0f : (heading >= 5u && heading <= 7u ? -1.0f : 0.0f) };
				const auto buttons{ heading == 0u ? structures::button_sprint : 0u };
				const auto forward{ mathematics.normalize(mathematics.flat_forward(yaw) * input_forward + mathematics.right_from_yaw(yaw) * input_side) };
				const auto top{ heading == 0u ? move_speed_sprint : move_speed_run };

				structures::movement_state_s state{};

				movement.reset(state, position, yaw);

				for (auto tick{ 0u }; tick < 30u; tick++)
				{
					movement.simulate(state, test_command(yaw, 0.0f, 0.0f, 0u));
				}

				auto episode{ 0.0f };

				for (auto tick{ 0u }; tick < 180u; tick++)
				{
					const auto before{ state.position };
					const auto grounded{ (state.flags & structures::movement_on_ground) != 0u };

					movement.last_block = {};

					movement.simulate(state, test_command(yaw, input_forward, input_side, buttons));

					const auto moved{ structures::vec3_s{ state.position.x - before.x, 0.0f, state.position.z - before.z } };
					const auto distance{ mathematics.length(moved) };

					ticks++;

					rising = std::max(rising, state.velocity.y);

					if ((state.flags & structures::movement_on_ground) == 0u)
					{
						const auto clearance{ state.position.y - terrain.height(state.position.x, state.position.z) };

						airborne++;

						launches += grounded ? 1u : 0u;

						highest = std::max(highest, clearance);

						episode = std::max(episode, clearance);
					}

					if (tick >= 20u)
					{
						const auto obstacle{ movement.last_block };
						const auto off_course{ distance > top * tick_interval * 0.5f && mathematics.dot(moved / distance, forward) < 0.94f };

						if (distance > top * tick_interval * 0.5f)
						{
							measured++;

							speed += distance / (tick_interval * top);

							deflected += off_course ? 1u : 0u;
						}

						else
						{
							blocked++;
						}

						if (off_course || distance <= top * tick_interval * 0.5f)
						{
							terrain_hits += obstacle.hit && obstacle.brush < 0 ? 1u : 0u;
							brush_hits += obstacle.hit && obstacle.brush >= 0 ? 1u : 0u;

							if (obstacle.hit && obstacle.brush < 0 && reported < 12u)
							{
								reported++;

								logger.write("movetest terrain block: at %.2f %.2f %.2f yaw %.0f heading %u moved %.3f normal %.3f %.3f %.3f ground %.2f %.2f %.2f flags %u", before.x, before.y, before.z, yaw * 57.2958f, heading, distance, obstacle.normal.x, obstacle.normal.y, obstacle.normal.z, state.ground_normal.x, state.ground_normal.y, state.ground_normal.z, state.flags);
							}
						}
					}
				}

				if (episode > worst)
				{
					worst = episode;
					worst_at = position;
				}

				samples++;
			}
		}

		const auto total{ static_cast<std::float_t>(std::max(ticks, 1u)) };
		const auto moving{ static_cast<std::float_t>(std::max(measured, 1u)) };
		const auto judged{ static_cast<std::float_t>(std::max(measured + blocked, 1u)) };

		logger.write("movetest terrain: %u runs %u ticks | airborne %.2f%% (%u take-offs) highest %.2f m (at %.0f %.0f %.0f) | max rise %.2f m/s | speed %.0f%% of top | off course %.2f%% | blocked %.2f%% (terrain %u, props %u)", samples, ticks, 100.0f * static_cast<std::float_t>(airborne) / total, launches, highest, worst_at.x, worst_at.y, worst_at.z, rising, 100.0f * speed / moving, 100.0f * static_cast<std::float_t>(deflected) / moving, 100.0f * static_cast<std::float_t>(blocked) / judged, terrain_hits, brush_hits);
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_bhop()
	{
		auto runs{ 0u };
		auto plain{ 0.0f };
		auto hopping{ 0.0f };
		auto fastest{ 0.0f };
		auto jumps{ 0u };

		for (auto attempt{ 0u }; attempt < 20000u && runs < 20u; attempt++)
		{
			auto position{ structures::vec3_s{} };

			if (find_ground(0.97f, position))
			{
				const auto yaw{ random() * two_pi };

				structures::movement_state_s state{};

				movement.reset(state, position, yaw);

				for (auto tick{ 0u }; tick < 600u; tick++)
				{
					movement.simulate(state, test_command(yaw, 1.0f, 0.0f, structures::button_sprint));
				}

				plain += mathematics.length(structures::vec3_s{ state.position.x - position.x, 0.0f, state.position.z - position.z });

				movement.reset(state, position, yaw);

				auto held{ false };

				for (auto tick{ 0u }; tick < 600u; tick++)
				{
					const auto steer{ std::sin(static_cast<std::float_t>(tick) * tick_interval * 3.0f) };
					const auto press{ (state.flags & structures::movement_on_ground) != 0u && held == false };

					held = press;

					movement.simulate(state, test_command(yaw + steer * 0.6f, 1.0f, steer > 0.0f ? 1.0f : -1.0f, structures::button_sprint | (press ? structures::button_jump : 0u)));

					jumps += state.velocity.y > move_jump_velocity * 0.9f ? 1u : 0u;

					fastest = std::max(fastest, mathematics.length(structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z }));
				}

				hopping += mathematics.length(structures::vec3_s{ state.position.x - position.x, 0.0f, state.position.z - position.z });

				runs++;
			}
		}

		logger.write("movetest bhop: %u runs | sprint %.1f m | hop+strafe %.1f m (%.0f%%, %u jumps) | top speed %.2f m/s", runs, plain / static_cast<std::float_t>(std::max(runs, 1u)), hopping / static_cast<std::float_t>(std::max(runs, 1u)), plain > 0.0f ? 100.0f * hopping / plain : 0.0f, jumps, fastest);
	}
	/*
	//=====================================================================================
	*/
	void dedicated_c::test_crouch()
	{
		auto runs{ 0u };
		auto apex{ 0.0f };
		auto spam{ 0.0f };
		auto settle{ 0.0f };

		for (auto attempt{ 0u }; attempt < 20000u && runs < 20u; attempt++)
		{
			auto position{ structures::vec3_s{} };

			if (find_ground(0.97f, position))
			{
				structures::movement_state_s state{};

				movement.reset(state, position, 0.0f);

				for (auto tick{ 0u }; tick < 10u; tick++)
				{
					movement.simulate(state, test_command(0.0f, 0.0f, 0.0f, 0u));
				}

				const auto floor{ state.position.y };

				for (auto tick{ 0u }; tick < 90u; tick++)
				{
					movement.simulate(state, test_command(0.0f, 0.0f, 0.0f, tick == 0u ? structures::button_jump : 0u));

					apex = std::max(apex, state.position.y - floor);
				}

				for (auto tick{ 0u }; tick < 600u; tick++)
				{
					const auto buttons{ ((tick / 2u) % 2u ? structures::button_crouch : 0u) | (tick % 50u == 0u ? structures::button_jump : 0u) };

					movement.simulate(state, test_command(0.0f, 0.0f, 0.0f, buttons));

					spam = std::max(spam, state.position.y - floor);
				}

				for (auto tick{ 0u }; tick < 90u; tick++)
				{
					movement.simulate(state, test_command(0.0f, 0.0f, 0.0f, 0u));
				}

				settle = std::max(settle, std::fabs(state.position.y - floor));

				runs++;
			}
		}

		logger.write("movetest crouch: %u runs | jump apex %.2f m | crouch-spam peak %.2f m (limit %.2f) | rest error %.3f m", runs, apex, spam, apex + player_height - player_crouch_height + 0.01f, settle);
	}
	/*
	//=====================================================================================
	*/
	bool dedicated_c::find_ground(std::float_t flatness, structures::vec3_s& position)
	{
		const auto size{ static_cast<std::float_t>(terrain.header.resolution - 1u) };
		const auto x{ terrain.header.origin + random() * size };
		const auto z{ terrain.header.origin + random() * size };
		const auto ground{ terrain.height(x, z) };

		position = { x, ground + 0.05f, z };

		return terrain.enabled && ground > sea_level + 1.5f && terrain.normal(x, z).y > flatness && world.box_solid(position + structures::vec3_s{ 0.0f, player_height * 0.5f + 0.1f, 0.0f }, { player_half_width, player_height * 0.5f, player_half_width }, structures::contents_solid | structures::contents_player_clip) == false;
	}
	/*
	//=====================================================================================
	*/
	structures::usercmd_s dedicated_c::test_command(std::float_t yaw, std::float_t forward, std::float_t side, std::uint32_t buttons)
	{
		structures::usercmd_s command{};

		command.yaw = yaw;
		command.forward = forward;
		command.side = side;
		command.buttons = buttons;
		command.delta = tick_interval;

		return command;
	}
	/*
	//=====================================================================================
	*/
	structures::usercmd_s dedicated_c::timed_command(std::double_t time, std::float_t yaw, std::float_t forward, std::uint32_t buttons)
	{
		auto command{ test_command(yaw, forward, 0.0f, buttons) };

		command.time = transport.quantize_time(time);

		return command;
	}
	/*
	//=====================================================================================
	*/
	std::float_t dedicated_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
	/*
	//=====================================================================================
	*/
	BOOL WINAPI dedicated_c::control(DWORD type)
	{
		dedicated.running = false;

		SetEvent(dedicated.nudge);

		return type == CTRL_C_EVENT || type == CTRL_BREAK_EVENT || type == CTRL_CLOSE_EVENT ? TRUE : FALSE;
	}
}

//=====================================================================================
