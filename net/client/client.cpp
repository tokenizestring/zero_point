
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	client_c client;

	bool client_c::open()
	{
		if (opened == false)
		{
			opened = socket.open(0u, true);

			seed ^= static_cast<std::uint32_t>(GetTickCount64()) * 2654435761u;

			delivered.reserve(64u);
			remotes.reserve(net_maximum_players);

			logger.write(opened ? "client: udp socket ready on port %u" : "client: could not open a udp socket (%u)", socket.port);
		}

		return opened;
	}
	/*
	//=====================================================================================
	*/
	void client_c::close()
	{
		disconnect();

		socket.close();

		opened = false;
	}
	/*
	//=====================================================================================
	*/
	void client_c::connect(const structures::address_s& address)
	{
		if (open())
		{
			disconnect();

			server = address;
			state = structures::link_connecting;
			attempts = 0u;
			attempt_timer = 0.0f;
			salt = static_cast<std::uint32_t>(random() * 4294967040.0f) | 1u;
			synchronized = false;
			placed = false;
			latency = 0.0f;
			latest_snapshot = -1.0;
			acknowledged = 0u;
			error = {};

			char text[32]{};

			udp_socket_c::format(address, text, sizeof(text));

			std::snprintf(status, sizeof(status), "Connecting to %s", text);

			logger.write("client: connecting to %s", text);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::disconnect()
	{
		if (state == structures::link_connected)
		{
			stream_writer_c writer{};

			writer.reset(packet, sizeof(packet));

			writer.u32(net_protocol_id);
			writer.u8(structures::packet_disconnect);

			socket.send(server, packet, writer.size);
			socket.send(server, packet, writer.size);

			logger.write("client: disconnected from %s", server_name);
		}

		state = structures::link_idle;
		synchronized = false;

		clear_remotes();
	}
	/*
	//=====================================================================================
	*/
	void client_c::refresh()
	{
		if (open())
		{
			stream_writer_c writer{};

			nonce = static_cast<std::uint32_t>(random() * 4294967040.0f);

			writer.reset(packet, sizeof(packet));

			writer.u32(net_protocol_id);
			writer.u8(structures::packet_query);
			writer.u32(nonce);

			for (auto offset{ 0u }; offset < net_browse_ports; offset++)
			{
				const structures::address_s local{ htonl(INADDR_LOOPBACK), static_cast<std::uint16_t>(net_default_port + offset) };
				const structures::address_s everyone{ htonl(INADDR_BROADCAST), static_cast<std::uint16_t>(net_default_port + offset) };

				if (std::none_of(servers.begin(), servers.end(), [&](const structures::server_entry_s& entry) { return entry.address == local; }))
				{
					servers.push_back({ local, {}, {}, 0u, 0u, 0.0f, clock, false });
				}

				socket.send(everyone, packet, writer.size);
			}

			for (auto& entry : servers)
			{
				entry.queried = clock;
				entry.responded = false;

				socket.send(entry.address, packet, writer.size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::update(std::float_t delta)
	{
		clock += static_cast<std::double_t>(delta);

		if (opened)
		{
			receive();

			if (state == structures::link_connecting)
			{
				attempt_timer -= delta;

				if (attempt_timer <= 0.0f && attempts >= net_connect_attempts)
				{
					state = structures::link_failed;

					std::snprintf(status, sizeof(status), "%s", "No answer from that server");
				}

				else if (attempt_timer <= 0.0f)
				{
					send_connect();

					attempts++;
					attempt_timer = net_connect_interval;
				}
			}

			if (state == structures::link_connected)
			{
				server_clock += static_cast<std::double_t>(delta);
				renderer.time = static_cast<std::float_t>(std::fmod(server_clock, shader_time_wrap));
				error = error * std::exp(-net_error_decay * delta);
				report_timer += delta;

				update_remotes(delta);

				if (report_timer >= net_report_interval)
				{
					report_timer = 0.0f;

					logger.write("client: ping %.1f ms, %zu players nearby, %zu reliable pending, correction %.3f m, worst miss %.4f m (%u of %u snapshots), health %.0f", latency * 1000.0f, remotes.size(), connection.outgoing.size(), mathematics.length(error), worst_miss, misses, reconciles, health);

					worst_miss = 0.0f;
					misses = 0u;
					reconciles = 0u;
				}

				if (clock - connection.last_received > net_timeout)
				{
					clear_remotes();

					state = structures::link_failed;
					synchronized = false;

					std::snprintf(status, sizeof(status), "%s", "Lost connection to the server");

					logger.write("client: connection to %s timed out", server_name);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::flush(std::float_t delta)
	{
		input_timer += delta;

		if (state == structures::link_connected && input_timer >= 1.0f / net_input_rate)
		{
			input_timer = std::fmod(input_timer, 1.0f / net_input_rate);

			send_input();
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::receive()
	{
		structures::address_s address{};

		auto more{ true };

		for (auto count{ 0u }; more && count < 4096u; count++)
		{
			const auto received{ socket.receive(address, buffer, sizeof(buffer)) };

			more = received != SOCKET_ERROR || WSAGetLastError() == WSAEMSGSIZE;

			if (received >= 5)
			{
				stream_reader_c reader{};

				reader.reset(buffer, static_cast<std::uint32_t>(received));

				if (reader.u32() == net_protocol_id)
				{
					const auto type{ reader.u8() };
					const auto from_server{ address == server };

					if (type == structures::packet_info)
					{
						handle_info(address, reader);
					}

					else if (type == structures::packet_accept && from_server && state == structures::link_connecting)
					{
						handle_accept(reader);
					}

					else if (type == structures::packet_reject && from_server && state == structures::link_connecting)
					{
						handle_reject(reader);
					}

					else if (type == structures::packet_data && from_server && state == structures::link_connected)
					{
						handle_data(reader);
					}

					else if (type == structures::packet_disconnect && from_server && state == structures::link_connected)
					{
						clear_remotes();

						state = structures::link_failed;
						synchronized = false;

						std::snprintf(status, sizeof(status), "%s", "The server closed the connection");

						logger.write("client: %s closed the connection", server_name);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::handle_info(const structures::address_s& address, stream_reader_c& reader)
	{
		structures::server_entry_s entry{};

		const auto answer{ reader.u32() };
		const auto version{ reader.u32() };

		entry.address = address;
		entry.instance = reader.u32();
		entry.locked = reader.u8() != 0u;
		entry.players = reader.u16();
		entry.maximum = reader.u16();

		reader.text(entry.name, sizeof(entry.name));
		reader.text(entry.map, sizeof(entry.map));

		const auto hold{ static_cast<std::double_t>(reader.f32()) };

		if (reader.overflow == false && answer == nonce && version == net_protocol_version)
		{
			auto found{ std::find_if(servers.begin(), servers.end(), [&](const structures::server_entry_s& known) { return known.address == address || known.instance == entry.instance; }) };

			if (found == servers.end())
			{
				entry.queried = clock;

				servers.push_back(entry);

				found = servers.end() - 1;
			}

			std::snprintf(found->name, sizeof(found->name), "%s", entry.name);
			std::snprintf(found->map, sizeof(found->map), "%s", entry.map);

			found->players = entry.players;
			found->maximum = entry.maximum;
			found->instance = entry.instance;
			found->locked = entry.locked;
			found->ping = static_cast<std::float_t>(std::max(clock - found->queried - hold, 0.001));
			found->responded = true;

			const auto kept{ found->address };

			servers.erase(std::remove_if(servers.begin(), servers.end(), [&](const structures::server_entry_s& other) { return other.instance == entry.instance && (other.address == kept) == false; }), servers.end());
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::handle_accept(stream_reader_c& reader)
	{
		const auto answer{ reader.u32() };
		const auto index{ reader.u16() };
		const auto time{ reader.f64() };
		const auto slots{ reader.u16() };

		char assigned[net_name_length]{};

		reader.text(server_name, sizeof(server_name));
		reader.text(map_name, sizeof(map_name));
		reader.text(assigned, sizeof(assigned));

		if (reader.overflow == false && answer == salt)
		{
			if (assigned[0] && std::strcmp(assigned, name) != 0)
			{
				logger.write("client: the server named us %s because %s is taken", assigned, name);

				std::snprintf(name, sizeof(name), "%s", assigned);
			}

			id = index;
			maximum = slots;
			server_clock = time;
			state = structures::link_connected;
			synchronized = false;
			alive = true;
			health = maximum_health;

			transport.reset(connection, server, clock);

			clear_remotes();

			std::snprintf(status, sizeof(status), "Connected to %s", server_name);

			logger.write("client: joined \"%s\" as player %u (map %s)", server_name, id, map_name);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::handle_reject(stream_reader_c& reader)
	{
		const auto reason{ reader.u8() };

		state = structures::link_failed;

		std::snprintf(status, sizeof(status), "%s", reject_texts[std::min<std::uint32_t>(reason, structures::reject_count - 1u)]);

		logger.write("client: rejected (%u)", reason);
	}
	/*
	//=====================================================================================
	*/
	void client_c::handle_data(stream_reader_c& reader)
	{
		delivered.clear();

		transport.receive(connection, reader, delivered, clock);

		for (const auto& message : delivered)
		{
			handle_message(message);
		}

		if (reader.overflow == false && reader.u8() == structures::payload_snapshot)
		{
			apply_snapshot(reader);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::handle_message(const structures::reliable_s& message)
	{
		stream_reader_c reader{};

		reader.reset(message.data, message.size);

		if (message.type == structures::message_join)
		{
			const auto remote_id{ reader.u16() };

			char remote_name[net_name_length]{};

			reader.text(remote_name, sizeof(remote_name));

			if (reader.overflow == false && remote_id != id)
			{
				auto index{ find_remote(remote_id) };

				if (index < 0)
				{
					remotes.push_back({});

					index = static_cast<std::int32_t>(remotes.size()) - 1;

					remotes.back().id = remote_id;
					remotes.back().actor = -1;
					remotes.back().last_seen = clock;
				}

				std::snprintf(remotes[index].name, sizeof(remotes[index].name), "%s", remote_name);
			}
		}

		else if (message.type == structures::message_leave)
		{
			const auto remote_id{ reader.u16() };

			if (const auto index{ find_remote(remote_id) }; index >= 0 && reader.overflow == false)
			{
				remotes[index].last_seen = -1000.0;
			}
		}

		else if (message.type == structures::message_chat)
		{
			const auto remote_id{ reader.u16() };

			char text[net_chat_length]{};
			char line[160]{};

			reader.text(text, sizeof(text));

			const auto index{ find_remote(remote_id) };

			std::snprintf(line, sizeof(line), "%s: %s", remote_id == 0xFFFFu ? "Server" : (remote_id == id ? name : (index >= 0 ? remotes[index].name : "Someone")), text);

			add_chat(line);
		}

		else if (message.type == structures::message_death)
		{
			const auto victim{ reader.u16() };
			const auto killer{ reader.u16() };
			const auto cause{ std::min<std::uint8_t>(reader.u8(), static_cast<std::uint8_t>(std::size(death_texts) - 1u)) };

			if (reader.overflow == false)
			{
				const auto victim_index{ find_remote(victim) };
				const auto killer_index{ find_remote(killer) };

				char line[160]{};

				if (killer != 0xFFFFu && killer != victim)
				{
					std::snprintf(line, sizeof(line), "%s was killed by %s", victim == id ? "You" : (victim_index >= 0 ? remotes[victim_index].name : "Someone"), killer == id ? "you" : (killer_index >= 0 ? remotes[killer_index].name : "someone"));
				}

				else
				{
					std::snprintf(line, sizeof(line), "%s died (%s)", victim == id ? "You" : (victim_index >= 0 ? remotes[victim_index].name : "Someone"), death_texts[cause]);
				}

				add_chat(line);

				if (victim == id)
				{
					alive = false;
					death_cause = cause;

					std::snprintf(death_killer, sizeof(death_killer), "%s", killer != 0xFFFFu && killer != victim && killer_index >= 0 ? remotes[killer_index].name : "");

					survival.vitals.dead = true;
				}
			}
		}

		else if (message.type == structures::message_inventory)
		{
			structures::item_stack_s slots[total_slots]{};
			structures::craft_job_s queue[crafting_queue_size]{};
			structures::weapon_state_s weapon_read{};

			bool known[recipe_count]{};

			const auto last{ reader.u32() };

			reader.bytes(&weapon_read, sizeof(weapon_read));

			for (auto& slot : slots)
			{
				slot.item = std::min<std::uint32_t>(reader.u16(), static_cast<std::uint32_t>(std::size(item_definitions) - 1u));
				slot.amount = reader.u16();
				slot.condition = std::clamp(reader.f32(), 0.0f, 1.0f);
				slot.loaded = reader.u8();
			}

			const auto queued{ std::min<std::uint32_t>(reader.u8(), crafting_queue_size) };

			for (auto entry{ 0u }; entry < queued; entry++)
			{
				queue[entry].recipe = std::min<std::uint32_t>(reader.u8(), static_cast<std::uint32_t>(recipe_count - 1u));
				queue[entry].remaining = reader.f32();
			}

			for (auto recipe{ 0u }; recipe < recipe_count; recipe += 8u)
			{
				const auto bits{ reader.u8() };

				for (auto bit{ 0u }; bit < 8u && recipe + bit < recipe_count; bit++)
				{
					known[recipe + bit] = (bits & (1u << bit)) != 0u;
				}
			}

			if (reader.overflow == false)
			{
				std::memcpy(survival.slots, slots, sizeof(slots));
				std::memcpy(survival.queue, queue, sizeof(queue));
				std::memcpy(survival.known, known, sizeof(known));

				survival.queue_count = queued;

				weapon_read.weapon = std::min<std::uint32_t>(weapon_read.weapon, structures::weapon_count - 1u);
				weapon_read.slot = std::min(weapon_read.slot, hotbar_slots - 1u);

				if (alive && last <= player.sequence)
				{
					replay_weapon(last, weapon_read);
				}
			}
		}

		else if (message.type == structures::message_hit)
		{
			const auto victim{ reader.u16() };
			const auto damage{ reader.u8() };
			const auto flags{ reader.u8() };
			const auto point{ structures::vec3_s{ reader.f32(), reader.f32(), reader.f32() } };

			if (reader.overflow == false && std::isfinite(point.x) && std::isfinite(point.y) && std::isfinite(point.z))
			{
				combat.hit_marker = 1.0f;
				combat.kill_marker = (flags & 2u) ? 1.0f : combat.kill_marker;

				particles.impact(structures::surface_flesh, point, mathematics.normalize(player.eye - point));

				mixer.play_2d(structures::sound_hit_flesh, (flags & 1u) ? 0.9f : 0.6f, (flags & 1u) ? 1.3f : 1.0f);

				hits_confirmed++;

				damage_dealt += damage;

				if ((flags & 2u) && victim != fauna_victim)
				{
					const auto index{ find_remote(victim) };

					char line[96]{};

					std::snprintf(line, sizeof(line), "%s %s", (flags & 1u) ? "Headshot kill:" : "Kill:", index >= 0 ? remotes[index].name : "castaway");

					survival.post(line, 0);
				}
			}
		}

		else if (message.type == structures::message_node)
		{
			const auto index{ reader.u32() };
			const auto depleted{ reader.u8() != 0u };
			const auto fall{ static_cast<std::float_t>(reader.u8()) / 256.0f * two_pi };

			if (reader.overflow == false && index < harvest.nodes.size())
			{
				harvest.nodes[index].fall = fall;

				if (depleted && harvest.nodes[index].depleted == false)
				{
					harvest.topple(index);
				}

				set_node(index, depleted);
			}
		}

		else if (message.type == structures::message_nodes)
		{
			const auto first{ reader.u32() };
			const auto span{ static_cast<std::uint32_t>(reader.u16()) };

			for (auto offset{ 0u }; offset < span && reader.overflow == false; offset += 8u)
			{
				const auto bits{ reader.u8() };

				for (auto bit{ 0u }; bit < 8u && offset + bit < span && reader.overflow == false; bit++)
				{
					set_node(first + offset + bit, (bits & (1u << bit)) != 0u);
				}
			}
		}

		else if (message.type == structures::message_structures)
		{
			const auto count{ reader.u16() };

			for (auto entry{ 0u }; entry < count && reader.overflow == false; entry++)
			{
				structures::structure_s structure{};

				const auto index{ reader.u32() };

				structure.piece = std::min<std::uint32_t>(reader.u8(), structures::piece_count - 1u);
				structure.position = { reader.f32(), reader.f32(), reader.f32() };
				structure.yaw = reader.f32();
				structure.anchor = static_cast<std::int32_t>(reader.u32());
				structure.owner = reader.u32();
				structure.health = reader.f32();
				structure.tier = std::min<std::uint32_t>(reader.u8(), building_tier_count - 1u);

				const auto flags{ reader.u8() };

				structure.open = (flags & 1u) != 0u;
				structure.destroyed = (flags & 2u) != 0u;

				if (reader.overflow == false)
				{
					apply_structure(index, structure, (flags & 4u) != 0u);

					if ((flags & 8u) != 0u && structure.destroyed == false)
					{
						building.locks[index] = {};
					}

					else
					{
						building.locks.erase(index);
					}
				}
			}
		}

		else if (message.type == structures::message_keypad)
		{
			const auto door{ reader.u32() };
			const auto setting{ reader.u8() != 0u };

			if (reader.overflow == false && door < building.placed.size())
			{
				hud.open_keypad(static_cast<std::int32_t>(door), setting);
			}
		}

		else if (message.type == structures::message_crops)
		{
			const auto total{ std::min<std::uint32_t>(reader.u16(), maximum_crops) };
			const auto first{ static_cast<std::uint32_t>(reader.u16()) };
			const auto count{ static_cast<std::uint32_t>(reader.u8()) };

			if (reader.overflow == false && first == 0u)
			{
				farming.crops.resize(total);
			}

			for (auto entry{ 0u }; entry < count && reader.overflow == false; entry++)
			{
				structures::crop_s crop{};

				crop.position = { reader.f32(), reader.f32(), reader.f32() };
				crop.yaw = (static_cast<std::float_t>(reader.u8()) / 255.0f - 0.5f) * two_pi;
				crop.growth = static_cast<std::float_t>(reader.u8()) / 255.0f;
				crop.water = static_cast<std::float_t>(reader.u8()) / 255.0f;
				crop.health = static_cast<std::float_t>(reader.u8()) / 255.0f;
				crop.ripe_time = static_cast<std::float_t>(reader.u16());
				crop.kind = std::min<std::uint32_t>(reader.u8(), structures::crop_count - 1u);
				crop.dead = reader.u8() != 0u;

				if (reader.overflow == false && first + entry < farming.crops.size())
				{
					farming.crops[first + entry] = crop;
				}
			}
		}

		else if (message.type == structures::message_container)
		{
			const auto index{ reader.u32() };
			const auto burning{ reader.u8() != 0u };

			structures::item_stack_s slots[container_slots]{};

			for (auto& slot : slots)
			{
				slot.item = std::min<std::uint32_t>(reader.u16(), static_cast<std::uint32_t>(std::size(item_definitions) - 1u));
				slot.amount = reader.u16();
				slot.condition = std::clamp(reader.f32(), 0.0f, 1.0f);
				slot.loaded = reader.u8();
			}

			if (reader.overflow == false && index < building.containers.size())
			{
				std::memcpy(building.containers[index].slots, slots, sizeof(slots));

				building.containers[index].burning = burning;
			}
		}

		else if (message.type == structures::message_bags)
		{
			const auto total{ std::min<std::uint32_t>(reader.u16(), maximum_bags) };
			const auto first{ static_cast<std::uint32_t>(reader.u16()) };
			const auto count{ static_cast<std::uint32_t>(reader.u8()) };

			if (reader.overflow == false && first == 0u)
			{
				for (auto index{ total }; index < loot.bags.size(); index++)
				{
					loot.release(loot.bags[index]);
				}

				loot.bags.resize(total, structures::loot_bag_s{ {}, 0.0f, 0.0f, {}, {}, -1, 0u, 0u, 0.0f, false });
			}

			for (auto entry{ 0u }; entry < count && reader.overflow == false; entry++)
			{
				const auto flags{ reader.u8() };
				const auto active{ (flags & 1u) != 0u };
				const auto position{ structures::vec3_s{ reader.f32(), reader.f32(), reader.f32() } };
				const auto yaw{ reader.f32() };
				const auto items{ static_cast<std::uint32_t>(reader.u8()) };

				char owner[net_name_length]{};

				reader.text(owner, sizeof(owner));

				if (reader.overflow == false && first + entry < loot.bags.size())
				{
					auto& bag{ loot.bags[first + entry] };

					if (bag.actor >= 0 && (active == false || mathematics.distance(bag.position, position) > 0.5f))
					{
						loot.release(bag);
					}

					bag.active = active;
					bag.sleeper = (flags & 2u) ? 1u : 0u;
					bag.position = position;
					bag.yaw = yaw;
					bag.items = items;

					std::snprintf(bag.name, sizeof(bag.name), "%s", owner);
				}
			}
		}

		else if (message.type == structures::message_hurt)
		{
			const auto from{ structures::vec3_s{ reader.f32(), reader.f32(), reader.f32() } };

			if (reader.overflow == false && std::isfinite(from.x) && std::isfinite(from.y) && std::isfinite(from.z))
			{
				hud.hurt_from = from;
				hud.hurt_timer = 1.6f;

				mixer.play_2d(structures::sound_player_hurt, 0.7f, 0.95f + random() * 0.1f);
			}
		}

		else if (message.type == structures::message_notice)
		{
			char text[96]{};

			reader.text(text, sizeof(text));

			const auto amount{ reader.i16() };

			if (reader.overflow == false)
			{
				survival.post(text, amount);
			}
		}

		else if (message.type == structures::message_cue)
		{
			const auto sound{ reader.u16() };
			const auto volume{ reader.f32() };
			const auto pitch{ reader.f32() };

			if (reader.overflow == false && sound < structures::sound_count)
			{
				mixer.play_2d(sound, std::clamp(volume, 0.0f, 1.0f), std::clamp(pitch, 0.25f, 4.0f));
			}
		}

		else if (message.type == structures::message_sound)
		{
			const auto sound{ reader.u16() };
			const auto x{ reader.f32() };
			const auto y{ reader.f32() };
			const auto z{ reader.f32() };
			const auto volume{ static_cast<std::float_t>(reader.u8()) / 255.0f };
			const auto pitch{ static_cast<std::float_t>(reader.u8()) / 64.0f };

			if (reader.overflow == false && sound < structures::sound_count && std::isfinite(x) && std::isfinite(y) && std::isfinite(z))
			{
				mixer.play(sound, { x, y, z }, volume, pitch * (0.94f + mixer.random() * 0.12f));
			}
		}

		else if (message.type == structures::message_marks)
		{
			marks.receive(reader);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::apply_snapshot(stream_reader_c& reader)
	{
		const auto time{ reader.f64() };
		const auto echo{ reader.u32() };
		const auto hold{ reader.f32() };
		const auto last{ reader.u32() };

		if (reader.overflow == false && echo != 0u)
		{
			latency = mathematics.lerp(latency, std::max(static_cast<std::float_t>(static_cast<std::int32_t>(transport.stamp(clock) - echo)) * 0.001f - hold, 0.0f), 0.2f);
		}

		structures::movement_state_s state_read{};

		reader.bytes(&state_read, sizeof(state_read));

		const auto health_value{ static_cast<std::float_t>(reader.u16()) / 100.0f };
		const auto calories_value{ static_cast<std::float_t>(reader.u16()) / 10.0f };
		const auto hydration_value{ static_cast<std::float_t>(reader.u16()) / 10.0f };
		const auto breath_value{ static_cast<std::float_t>(reader.u8()) / 255.0f };
		const auto wetness_value{ static_cast<std::float_t>(reader.u8()) / 255.0f };
		const auto temperature_value{ static_cast<std::float_t>(reader.i8()) };
		const auto alive_value{ reader.u8() };
		const auto world_hours{ reader.f32() };
		const auto cloud_value{ static_cast<std::float_t>(reader.u8()) / 255.0f };
		const auto rain_value{ static_cast<std::float_t>(reader.u8()) / 255.0f };
		const auto storm_value{ static_cast<std::float_t>(reader.u8()) / 255.0f };
		const auto steering{ reader.u8() != 0u };

		structures::vehicle_s steered{};

		if (steering)
		{
			vehicles.read_state(reader, steered);
		}

		vehicles.read(reader, time);

		const auto count{ reader.u8() };

		if (reader.overflow == false)
		{
			weather.set(cloud_value, rain_value, storm_value);
		}

		if (reader.overflow == false && std::isfinite(world_hours) && atmosphere.enabled && std::fabs(mathematics.angle_difference(atmosphere.hours / 24.0f * two_pi, world_hours / 24.0f * two_pi)) > 0.002f)
		{
			atmosphere.hours = std::fmod(std::max(world_hours, 0.0f), 24.0f);
		}

		if (reader.overflow == false && time > latest_snapshot)
		{
			latest_snapshot = time;
			server_clock = std::fabs(server_clock - time) > net_clock_snap ? time : server_clock + (time - server_clock) * net_clock_pull;
			revived = revived || (alive == false && alive_value != 0u);
			alive = alive_value != 0u;

			if (health_value < health - 0.5f && alive)
			{
				survival.vitals.damage_flash = std::min(1.0f, survival.vitals.damage_flash + (health - health_value) / 25.0f);
			}

			health = health_value;

			survival.vitals.health = health_value;
			survival.vitals.calories = calories_value;
			survival.vitals.hydration = hydration_value;
			survival.vitals.breath = breath_value;
			survival.vitals.dead = alive == false;
			survival.climate.wetness = wetness_value;
			survival.climate.temperature = temperature_value;
			authority = state_read;
			driven = steered;
			driving = steering && reader.overflow == false;

			reconcile(last);

			for (auto entry{ 0u }; entry < count && reader.overflow == false; entry++)
			{
				const auto remote_id{ reader.u16() };
				const auto px{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto py{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto pz{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto vx{ static_cast<std::float_t>(reader.i8()) / net_velocity_scale };
				const auto vy{ static_cast<std::float_t>(reader.i8()) / net_velocity_scale };
				const auto vz{ static_cast<std::float_t>(reader.i8()) / net_velocity_scale };
				const auto yaw{ transport.decode_angle(reader.u16()) };
				const auto pitch{ static_cast<std::float_t>(reader.i8()) / 127.0f * half_pi };
				const auto flags{ static_cast<std::uint32_t>(reader.u16()) };
				const auto remote_health{ static_cast<std::float_t>(reader.u8()) };
				const auto item{ static_cast<std::uint32_t>(reader.u8()) };

				if (reader.overflow == false && remote_id != id)
				{
					auto index{ find_remote(remote_id) };

					if (index < 0)
					{
						remotes.push_back({});

						index = static_cast<std::int32_t>(remotes.size()) - 1;

						remotes.back().id = remote_id;
						remotes.back().actor = -1;

						std::snprintf(remotes.back().name, sizeof(remotes.back().name), "Castaway %u", remote_id);
					}

					auto& remote{ remotes[index] };

					if (remote.count == 0u || time > remote.samples[(remote.count - 1u) % std::size(remote.samples)].time)
					{
						structures::vec3_s seat{};

						const auto carrier{ (flags & structures::movement_riding) ? train.aboard({ px, py, pz }, time, seat) : 0u };

						remote.samples[remote.count % std::size(remote.samples)] = { time, { px, py, pz }, { vx, vy, vz }, yaw, pitch, flags, carrier, seat };

						remote.count++;
					}

					remote.last_seen = clock;
					remote.health = remote_health;
					remote.item = item;
				}
			}

			const auto shot_count{ reader.u8() };

			for (auto entry{ 0u }; entry < shot_count && reader.overflow == false; entry++)
			{
				const auto shooter{ reader.u16() };
				const auto weapon_id{ reader.u8() };
				const auto result{ reader.u8() };
				const auto ox{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto oy{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto oz{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto ex{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto ey{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
				const auto ez{ static_cast<std::float_t>(reader.i16()) / net_position_scale };

				if (reader.overflow == false && shooter != id && weapon_id > structures::weapon_none && weapon_id < structures::weapon_count)
				{
					hear_shot(shooter, weapon_id, result, { ox, oy, oz }, { ex, ey, ez });
				}
			}

			fauna.read(reader, time);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::apply_structure(std::uint32_t index, const structures::structure_s& structure, bool burning)
	{
		if (index == building.placed.size())
		{
			building.attach(structure);
		}

		else if (index < building.placed.size())
		{
			auto& existing{ building.placed[index] };

			if (existing.piece == structures::piece_door && existing.open != structure.open)
			{
				mixer.play(structures::sound_container, existing.position + structures::vec3_s{ 0.0f, 1.2f, 0.0f }, 0.8f, structure.open ? 1.05f : 0.85f);
			}

			if (existing.tier != structure.tier)
			{
				const auto& tier{ building_tiers[std::min(structure.tier, building_tier_count - 1u)] };

				mixer.play(tier.sound, existing.position + structures::vec3_s{ 0.0f, 1.2f, 0.0f }, 0.9f, 0.75f);

				particles.impact(tier.surface, existing.position + structures::vec3_s{ 0.0f, 1.2f, 0.0f }, { 0.0f, 1.0f, 0.0f });

				building.retier(index, structure.tier);
			}

			existing.health = structure.health;

			building.refresh(index, structure.open, structure.destroyed);
		}

		if (index < building.placed.size())
		{
			const auto& current{ building.placed[index] };

			if (current.container >= 0)
			{
				building.containers[current.container].burning = burning;
			}

			if (current.piece == structures::piece_sleeping_bag && current.owner == mathematics.hash_text(name))
			{
				building.bag = current.destroyed ? -1 : static_cast<std::int32_t>(index);
			}
		}

		building.dirty.clear();
	}
	/*
	//=====================================================================================
	*/
	void client_c::set_node(std::uint32_t index, bool depleted)
	{
		if (index < harvest.nodes.size() && harvest.nodes[index].depleted != depleted)
		{
			if (depleted)
			{
				const auto& node{ harvest.nodes[index] };

				if (node.kind <= structures::node_dead_tree && mathematics.distance(node.position, player.eye) < 60.0f)
				{
					mixer.play(structures::sound_chop, node.position + structures::vec3_s{ 0.0f, 2.0f, 0.0f }, 1.0f, 0.6f);
				}

				harvest.deplete(index);
			}

			else
			{
				harvest.restore(index);
			}

			harvest.changed.clear();
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::hear_shot(std::uint16_t shooter, std::uint32_t weapon_id, std::uint32_t result, structures::vec3_s origin, structures::vec3_s end)
	{
		const auto& definition{ weapon_definitions[weapon_id] };
		const auto direction{ mathematics.normalize(end - origin) };

		shots_heard++;

		if (result == 253u)
		{
			projectiles.launch(origin, end - origin, 0.0f, shooter);

			mixer.play(definition.shot_sound, origin, 0.6f, 1.45f);
		}

		else
		{
			mixer.gunshot(origin, weapon_id, false);

			mixer.bullet(origin, end, result);

			wildlife.startle(origin, weapon_definitions[weapon_id].loudness);
		}

		if (mathematics.distance(origin, player.eye) < net_tracer_range && result != 253u)
		{
			particles.emit(structures::particle_smoke, origin + direction * 0.6f, direction * 0.4f + structures::vec3_s{ 0.0f, 0.3f, 0.0f }, 0.1f, 2u, false);

			renderer.add_light(origin + direction * 0.5f, 5.0f, { 6.0f, 4.0f, 2.0f });
		}

		if (mathematics.distance(end, player.eye) < net_tracer_range && result < 253u)
		{
			particles.impact(result == 255u ? structures::surface_flesh : std::min<std::uint32_t>(result, structures::surface_count - 1u), end - direction * 0.03f, direction * -1.0f);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::reconcile(std::uint32_t last)
	{
		if (synchronized == false || last >= acknowledged)
		{
			auto replay{ authority };
			auto vehicle{ driving && replay.vehicle == driven.id ? vehicles.find(driven.id) : nullptr };

			if (driving && replay.vehicle == driven.id && vehicle == nullptr)
			{
				vehicles.spawn(driven.kind, driven.position, 0.0f);

				vehicle = &vehicles.list.back();
				vehicle->id = driven.id;
			}

			const auto shown{ vehicle ? vehicle->position : structures::vec3_s{} };

			if (vehicle)
			{
				vehicles.adopt(*vehicle, driven);
			}

			for (auto sequence{ last + 1u }; sequence <= player.sequence; sequence++)
			{
				const auto& entry{ history[sequence % net_history_size] };

				if (entry.used && entry.command.sequence == sequence)
				{
					vehicles.pilot(replay, entry.command);

					movement.simulate(replay, entry.command);
				}
			}

			if (vehicle)
			{
				const auto miss{ shown - vehicle->position };

				vehicle->error = synchronized && mathematics.length(miss) < net_snap_distance ? vehicle->error + miss : structures::vec3_s{};
			}

			const auto offset{ player.state.position - replay.position };

			if (replay.platform && replay.platform == player.state.platform && replay.platform == player.previous.platform)
			{
				player.previous.local = player.previous.local - (player.state.local - replay.local);
			}

			worst_miss = std::max(worst_miss, mathematics.length(offset));
			misses += mathematics.length(offset) > 0.001f ? 1u : 0u;
			reconciles++;

			if (synchronized && mathematics.length(offset) < net_snap_distance)
			{
				error += offset;
			}

			else
			{
				error = {};
			}

			player.previous.position = player.previous.position - offset;
			player.state = replay;

			acknowledged = last;
			synchronized = true;
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::record(const structures::usercmd_s& command, bool usable, bool moving)
	{
		history[command.sequence % net_history_size] = { command, usable, moving, true };
	}
	/*
	//=====================================================================================
	*/
	void client_c::replay_weapon(std::uint32_t last, const structures::weapon_state_s& authority_weapon)
	{
		auto replay{ authority_weapon };

		for (auto sequence{ last + 1u }; sequence <= player.sequence; sequence++)
		{
			const auto& entry{ history[sequence % net_history_size] };

			if (entry.used && entry.command.sequence == sequence)
			{
				weapons.step(replay, survival, entry.command, entry.usable, entry.moving);
			}
		}

		replay.events = 0u;

		weapons.state = replay;
	}
	/*
	//=====================================================================================
	*/
	void client_c::send_input()
	{
		stream_writer_c writer{};

		writer.reset(packet, sizeof(packet));

		transport.begin(connection, writer, clock);

		writer.u8(structures::payload_input);
		writer.u32(std::max(transport.stamp(clock), 1u));

		const auto newest{ player.sequence };
		const auto count{ std::min(net_input_redundancy, newest) };

		auto written{ 0u };

		const auto count_at{ writer.size };

		writer.u8(0u);

		for (auto sequence{ newest - count + 1u }; count && sequence <= newest; sequence++)
		{
			const auto& entry{ history[sequence % net_history_size] };

			if (entry.used && entry.command.sequence == sequence)
			{
				writer.u32(sequence);
				writer.i8(static_cast<std::int8_t>(std::clamp(entry.command.forward, -1.0f, 1.0f) * 127.0f));
				writer.i8(static_cast<std::int8_t>(std::clamp(entry.command.side, -1.0f, 1.0f) * 127.0f));
				writer.u16(transport.encode_angle(entry.command.yaw));
				writer.i16(transport.encode_pitch(entry.command.pitch));
				writer.u16(static_cast<std::uint16_t>(entry.command.buttons & 0xFFFFu));
				writer.u8(static_cast<std::uint8_t>(std::min(entry.command.weapon, 255u)));
				writer.u32(transport.encode_time(entry.command.time));

				written++;
			}
		}

		if (writer.overflow == false)
		{
			writer.data[count_at] = static_cast<std::uint8_t>(written);

			socket.send(server, packet, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::send_connect()
	{
		stream_writer_c writer{};

		writer.reset(packet, sizeof(packet));

		writer.u32(net_protocol_id);
		writer.u8(structures::packet_connect);
		writer.u32(net_protocol_version);
		writer.u32(salt);
		writer.text(name[0] ? name : "Castaway", net_name_length);
		writer.u32(static_cast<std::uint32_t>(identity & 0xFFFFFFFFu));
		writer.u32(static_cast<std::uint32_t>(identity >> 32u));
		writer.text(password, net_password_length);

		socket.send(server, packet, writer.size);
	}
	/*
	//=====================================================================================
	*/
	void client_c::load_identity()
	{
		const auto path{ functions::executable_directory() + identity_file_name };

		std::vector<std::uint8_t> stored;

		if (functions::read_file(path.c_str(), stored) && stored.size() == sizeof(identity))
		{
			std::memcpy(&identity, stored.data(), sizeof(identity));
		}

		if (identity == 0u)
		{
			std::random_device device{};

			identity = (static_cast<std::uint64_t>(device()) << 32u | device()) | 1u;

			functions::write_file(path.c_str(), &identity, sizeof(identity));

			logger.write("client: created a new identity key");
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::update_remotes(std::float_t delta)
	{
		const auto render_time{ server_clock - net_interpolation_delay };

		for (auto index{ 0u }; index < remotes.size();)
		{
			auto& remote{ remotes[index] };

			if (clock - remote.last_seen > net_remote_timeout)
			{
				if (remote.actor >= 0 && remote.actor < static_cast<std::int32_t>(actors.list.size()))
				{
					actors.list[remote.actor].hidden = true;

					free_actors.push_back(remote.actor);
				}

				remotes[index] = remotes.back();

				remotes.pop_back();
			}

			else
			{
				if (remote.count)
				{
					const auto capacity{ static_cast<std::uint32_t>(std::size(remote.samples)) };
					const auto first{ remote.count > capacity ? remote.count - capacity : 0u };

					auto older{ remote.samples[(remote.count - 1u) % capacity] };
					auto newer{ older };

					for (auto sample{ first }; sample < remote.count; sample++)
					{
						const auto& candidate{ remote.samples[sample % capacity] };

						if (candidate.time <= render_time)
						{
							older = candidate;
							newer = sample + 1u < remote.count ? remote.samples[(sample + 1u) % capacity] : candidate;
						}
					}

					const auto span{ newer.time - older.time };
					const auto t{ span > 0.0001 ? mathematics.saturate(static_cast<std::float_t>((render_time - older.time) / span)) : 1.0f };
					const auto riding{ train.ready && older.platform && older.platform == newer.platform };

					if (remote.actor < 0)
					{
						remote.actor = take_actor(older.position, older.yaw);
					}

					if (remote.actor >= 0)
					{
						auto& actor{ actors.list[remote.actor] };

						actor.position = riding ? mathematics.transform_point(mathematics.lerp(older.local, newer.local, t), train.pose(server_clock, older.platform - 1u)) : mathematics.lerp(older.position, newer.position, t);
						actor.velocity = mathematics.lerp(older.velocity, newer.velocity, t);
						actor.look_yaw = older.yaw + mathematics.angle_difference(older.yaw, newer.yaw) * t;
						actor.look_pitch = mathematics.lerp(older.pitch, newer.pitch, t);
						actor.crouched = (newer.flags & structures::movement_crouched) != 0u;
						actor.grounded = (newer.flags & structures::movement_on_ground) != 0u || (newer.flags & structures::movement_swimming) != 0u;
						actor.dead = (newer.flags & 0x8000u) != 0u;
						actor.death = actor.dead ? actor.death + delta : 0.0f;
						actor.hidden = (actor.dead && loot.nearest(actor.position) >= 0) || (newer.flags & structures::movement_seated) != 0u;
						actor.held = remote.item < structures::item_count ? remote.item : 0u;

						const auto speed{ mathematics.length(structures::vec3_s{ actor.velocity.x, 0.0f, actor.velocity.z }) };

						if (actor.grounded && actor.dead == false && speed > 0.6f && mathematics.distance(actor.position, player.eye) < net_footstep_range)
						{
							remote.stride += speed * delta;

							if (remote.stride > step_length_base + step_length_scale * speed)
							{
								remote.stride = 0.0f;

								mixer.play((newer.flags & structures::movement_swimming) ? structures::sound_swim : mixer.surface_sound(actor.position), actor.position + structures::vec3_s{ 0.0f, 0.1f, 0.0f }, std::clamp(0.25f + speed * 0.1f, 0.25f, 0.95f) * (actor.crouched ? 0.35f : 1.0f), 0.9f + random() * 0.2f);
							}
						}
					}
				}

				index++;
			}
		}

		for (auto& line_time : chat_times)
		{
			line_time = std::max(line_time - delta, 0.0f);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::act(std::uint8_t action, structures::vec3_s position)
	{
		if (state == structures::link_connected)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u8(action);
			writer.f32(position.x);
			writer.f32(position.y);
			writer.f32(position.z);

			transport.queue(connection, structures::message_act, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::build(const structures::placement_s& placement)
	{
		if (state == structures::link_connected)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u8(static_cast<std::uint8_t>(placement.piece));
			writer.f32(placement.position.x);
			writer.f32(placement.position.y);
			writer.f32(placement.position.z);
			writer.f32(placement.yaw);
			writer.u32(static_cast<std::uint32_t>(placement.anchor));

			transport.queue(connection, structures::message_build, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::say(const char* text)
	{
		if (state == structures::link_connected && text[0])
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.text(text, net_chat_length);

			transport.queue(connection, structures::message_chat, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::request(std::uint8_t type, std::uint16_t first, std::uint16_t second)
	{
		if (state == structures::link_connected)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u8(type);
			writer.u16(first);
			writer.u16(second);

			transport.queue(connection, structures::message_request, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::request_respawn()
	{
		if (state == structures::link_connected && alive == false && clock - respawn_asked > 1.0f)
		{
			respawn_asked = clock;

			transport.queue(connection, structures::message_respawn, scratch, 0u);
		}
	}
	/*
	//=====================================================================================
	*/
	void client_c::add_chat(const char* text)
	{
		for (auto line{ net_chat_lines - 1u }; line > 0u; line--)
		{
			std::memcpy(chat_lines[line], chat_lines[line - 1u], sizeof(chat_lines[line]));

			chat_times[line] = chat_times[line - 1u];
		}

		std::snprintf(chat_lines[0], sizeof(chat_lines[0]), "%s", text);

		chat_times[0] = net_chat_time;
	}
	/*
	//=====================================================================================
	*/
	void client_c::clear_remotes()
	{
		for (const auto& remote : remotes)
		{
			if (remote.actor >= 0 && remote.actor < static_cast<std::int32_t>(actors.list.size()))
			{
				actors.list[remote.actor].hidden = true;

				free_actors.push_back(remote.actor);
			}
		}

		remotes.clear();

		marks.clear();
	}
	/*
	//=====================================================================================
	*/
	bool client_c::connected()
	{
		return state == structures::link_connected;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t client_c::find_remote(std::uint16_t remote_id)
	{
		auto found{ -1 };

		for (auto index{ 0u }; found < 0 && index < remotes.size(); index++)
		{
			found = remotes[index].id == remote_id ? static_cast<std::int32_t>(index) : -1;
		}

		return found;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t client_c::take_actor(structures::vec3_s position, std::float_t yaw)
	{
		auto index{ -1 };

		if (free_actors.size())
		{
			index = free_actors.back();

			free_actors.pop_back();

			auto& actor{ actors.list[index] };

			actor.position = position;
			actor.velocity = {};
			actor.look_yaw = yaw;
			actor.body_yaw = yaw;
			actor.frames = 0u;
			actor.dead = false;
			actor.death = 0.0f;
			actor.hidden = false;
		}

		else if (const auto actor{ actors.spawn(actors.survivor(), position, yaw, structures::actor_behavior_remote) }; actor)
		{
			index = static_cast<std::int32_t>(actors.list.size()) - 1;
		}

		return index;
	}
	/*
	//=====================================================================================
	*/
	std::float_t client_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / static_cast<std::float_t>(0x1000000u);
	}
}

//=====================================================================================
