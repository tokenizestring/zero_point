
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	server_c server;

	bool server_c::start(std::uint16_t port, const char* server_name, const char* map_name, std::uint32_t maximum_players)
	{
		std::snprintf(name, sizeof(name), "%s", server_name);
		std::snprintf(map, sizeof(map), "%s", map_name);

		maximum = std::clamp(maximum_players, 1u, net_maximum_players);
		running = socket.open(port, false);
		instance = std::random_device{}() | 1u;

		clients.assign(net_maximum_players, {});
		survivors.assign(net_maximum_players, {});
		links.assign(net_maximum_players, -1);
		cells.assign(static_cast<std::size_t>(net_grid_size) * net_grid_size, -1);
		nearby.reserve(net_maximum_players);
		delivered.reserve(64u);
		lookup.clear();

		if (running)
		{
			logger.write("server: \"%s\" listening on udp %u, %u slots, map %s", name, socket.port, maximum, map);
		}

		else
		{
			logger.write("server: could not open udp port %u", port);
		}

		return running;
	}
	/*
	//=====================================================================================
	*/
	void server_c::stop()
	{
		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			if (clients[index].active)
			{
				drop(index, true);
			}
		}

		persist.write();

		socket.close();

		running = false;
	}
	/*
	//=====================================================================================
	*/
	void server_c::set_weather(std::uint32_t phase, std::float_t duration)
	{
		weather_phase = std::min(phase, static_cast<std::uint32_t>(std::size(weather_phases) - 1u));
		weather_timer = duration;

		logger.write("server: weather turns %s for %.0f minutes", weather_names[weather_phase], weather_timer / 60.0f);
	}
	/*
	//=====================================================================================
	*/
	void server_c::update(std::float_t delta)
	{
		const auto snapshot_step{ 1.0f / net_snapshot_rate };

		clock += static_cast<std::double_t>(delta);
		renderer.time = static_cast<std::float_t>(std::fmod(clock, shader_time_wrap));
		hours = atmosphere.advance(hours, delta);
		atmosphere.hours = hours;
		weather_timer -= delta;

		if (weather_timer <= 0.0f)
		{
			const auto roll{ random() };

			auto total{ 0.0f };
			auto chosen{ 0u };

			for (auto phase{ 0u }; phase < std::size(weather_phases); phase++)
			{
				chosen = roll >= total ? phase : chosen;
				total += weather_phases[phase].chance;
			}

			set_weather(chosen, mathematics.lerp(weather_phases[chosen].shortest, weather_phases[chosen].longest, random()));
		}

		arrival = clock - (dormant ? 0.0 : static_cast<std::double_t>(delta) * 0.5);

		receive();

		if (dormant != (player_count == 0u))
		{
			dormant = player_count == 0u;
			tick_accumulator = 0.0f;
			snapshot_accumulator = 0.0f;

			logger.write(dormant ? "server: nobody online, resting at %.0f ticks a second" : "server: player online, back to %.0f ticks a second", dormant ? 1.0f / net_hibernate_step : net_server_tick_rate);
		}

		const auto step{ dormant ? net_hibernate_step : 1.0f / net_server_tick_rate };

		tick_accumulator = std::min(tick_accumulator + delta, step * 8.0f);

		while (tick_accumulator >= step)
		{
			simulate(step);

			tick_accumulator -= step;

			tick_count++;
		}

		snapshot_accumulator += dormant ? 0.0f : delta;

		if (snapshot_accumulator >= snapshot_step)
		{
			snapshot_accumulator = std::fmod(snapshot_accumulator, snapshot_step);

			send_snapshots();
		}

		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			if (clients[index].active && clients[index].bot == false && clock - clients[index].connection.last_received > net_timeout)
			{
				logger.write("server: %s timed out", clients[index].name);

				drop(index, false);
			}
		}

		persist.tick(delta);

		status_timer += delta;

		if (status_timer >= net_status_interval || (status_timer >= 10.0f && clock < net_early_status_time))
		{
			const auto bots{ std::count_if(clients.begin(), clients.end(), [](const structures::server_client_s& peer) { return peer.active && peer.bot; }) };

			logger.write("server: %u/%u players (%zd bots), tick %.2f ms, up %.1f KB/s, down %.1f KB/s, %u marks", player_count, maximum, bots, tick_cost * 1000.0f, static_cast<std::double_t>(bytes_sent) / 1024.0 / status_timer, static_cast<std::double_t>(bytes_received) / 1024.0 / status_timer, marks.count);

			status_timer = 0.0f;
			bytes_sent = 0u;
			bytes_received = 0u;
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t server_c::due()
	{
		const auto step{ dormant ? net_hibernate_step : 1.0f / net_server_tick_rate };
		const auto snapshot{ dormant ? step : 1.0f / net_snapshot_rate - snapshot_accumulator };

		return std::clamp(std::min(step - tick_accumulator, snapshot), 0.0f, step);
	}
	/*
	//=====================================================================================
	*/
	void server_c::receive()
	{
		structures::address_s address{};

		auto more{ true };

		for (auto count{ 0u }; more && count < 16384u; count++)
		{
			const auto received{ socket.receive(address, buffer, sizeof(buffer)) };

			more = received != SOCKET_ERROR || WSAGetLastError() == WSAEMSGSIZE;

			if (received >= 5)
			{
				stream_reader_c reader{};

				reader.reset(buffer, static_cast<std::uint32_t>(received));

				bytes_received += static_cast<std::uint64_t>(received);

				if (reader.u32() == net_protocol_id)
				{
					const auto type{ reader.u8() };
					const auto index{ find(address) };

					if (type == structures::packet_query)
					{
						handle_query(address, reader);
					}

					else if (type == structures::packet_connect)
					{
						handle_connect(address, reader);
					}

					else if (type == structures::packet_data && index >= 0)
					{
						handle_data(index, reader);
					}

					else if (type == structures::packet_disconnect && index >= 0)
					{
						logger.write("server: %s left", clients[index].name);

						drop(index, false);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::handle_query(const structures::address_s& address, stream_reader_c& reader)
	{
		const auto nonce{ reader.u32() };

		stream_writer_c writer{};

		writer.reset(packet, sizeof(packet));

		writer.u32(net_protocol_id);
		writer.u8(structures::packet_info);
		writer.u32(nonce);
		writer.u32(net_protocol_version);
		writer.u32(instance);
		writer.u8(admin.password.size() ? 1u : 0u);
		writer.u16(static_cast<std::uint16_t>(player_count));
		writer.u16(static_cast<std::uint16_t>(maximum));
		writer.text(name, net_server_name_length);
		writer.text(map, 32u);
		writer.f32(static_cast<std::float_t>(clock - arrival));

		if (reader.overflow == false)
		{
			send_raw(address, packet, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::handle_connect(const structures::address_s& address, stream_reader_c& reader)
	{
		char player_name[net_name_length]{};
		char offered[net_password_length]{};

		const auto version{ reader.u32() };
		const auto salt{ reader.u32() };

		reader.text(player_name, sizeof(player_name));

		if (player_name[0] == 0)
		{
			std::snprintf(player_name, sizeof(player_name), "%s", "Castaway");
		}

		const auto identity_low{ reader.u32() };
		const auto identity_high{ reader.u32() };

		reader.text(offered, sizeof(offered));

		const auto identity{ static_cast<std::uint64_t>(identity_high) << 32u | identity_low };
		const auto existing{ find(address) };
		const auto verdict{ admin.screen(player_name, offered) };

		if (reader.overflow == false)
		{
			if (version != net_protocol_version)
			{
				send_reject(address, structures::reject_version);
			}

			else if (existing >= 0)
			{
				send_accept(existing, salt);
			}

			else if (verdict >= 0)
			{
				logger.write("server: refused %s (%s)", player_name, reject_texts[verdict]);

				send_reject(address, static_cast<std::uint8_t>(verdict));
			}

			else if (settle_name(player_name, sizeof(player_name), identity) == false)
			{
				logger.write("server: refused %s (no free name left)", player_name);

				send_reject(address, structures::reject_identity);
			}

			else if (player_count >= maximum)
			{
				send_reject(address, structures::reject_full);
			}

			else
			{
				auto slot{ -1 };

				for (auto index{ 0 }; slot < 0 && index < static_cast<std::int32_t>(clients.size()); index++)
				{
					slot = clients[index].active ? -1 : index;
				}

				if (slot >= 0)
				{
					auto& peer{ clients[slot] };

					peer = {};

					survivors[slot] = {};
					survivors[slot].owner = slot;

					survivors[slot].reset_knowledge();

					transport.reset(peer.connection, address, clock);

					std::snprintf(peer.name, sizeof(peer.name), "%s", player_name);

					peer.active = true;
					peer.mark_center = -1;
					peer.commands.reserve(net_command_queue);

					lookup[key(address)] = slot;

					player_count++;

					spawn(slot);

					persist.recall(slot);

					if (forced_seat >= 0 && vehicles.list.size())
					{
						auto& vehicle{ vehicles.list[static_cast<std::size_t>(forced_seat) % vehicles.list.size()] };

						if (vehicle.riders[0] < 0)
						{
							vehicle.riders[0] = slot;
							vehicle.asleep = false;

							peer.state.vehicle = vehicle.id;
							peer.state.seat = 0u;
							peer.state.flags |= structures::movement_seated;
						}
					}

					loot.wake(peer.name);

					send_accept(slot, salt);

					send_nodes(slot);

					send_structures(slot);

					send_crops(slot);

					send_bags(slot);

					for (auto other{ 0 }; other < static_cast<std::int32_t>(clients.size()); other++)
					{
						if (other != slot && clients[other].active)
						{
							announce(other, slot);
							announce(slot, other);
						}
					}

					char text[32]{};

					udp_socket_c::format(address, text, sizeof(text));

					logger.write("server: %s joined from %s (%u/%u)", peer.name, text, player_count, maximum);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool server_c::settle_name(char* player_name, std::size_t capacity, std::uint64_t identity)
	{
		char wanted[net_name_length]{};
		char candidate[net_name_length]{};

		std::snprintf(wanted, sizeof(wanted), "%s", player_name);
		std::snprintf(candidate, sizeof(candidate), "%s", player_name);

		auto copy{ 1u };

		while (copy <= net_name_copies && (admin.player(candidate) >= 0 || persist.claim(mathematics.hash_text(candidate), identity) == false))
		{
			copy++;

			std::snprintf(candidate, sizeof(candidate), "%.*s (%u)", static_cast<std::int32_t>(net_name_length - 8u), wanted, copy);
		}

		if (copy <= net_name_copies)
		{
			if (copy > 1u)
			{
				logger.write("server: %s is taken, joining as %s", wanted, candidate);
			}

			std::snprintf(player_name, capacity, "%s", candidate);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void server_c::handle_data(std::int32_t index, stream_reader_c& reader)
	{
		auto& peer{ clients[index] };

		delivered.clear();

		transport.receive(peer.connection, reader, delivered, clock);

		for (const auto& message : delivered)
		{
			handle_message(index, message);
		}

		if (reader.overflow == false && reader.u8() == structures::payload_input)
		{
			read_input(index, reader);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::handle_message(std::int32_t index, const structures::reliable_s& message)
	{
		stream_reader_c reader{};

		reader.reset(message.data, message.size);

		if (message.type == structures::message_chat)
		{
			char text[net_chat_length]{};

			reader.text(text, sizeof(text));

			if (reader.overflow == false && std::strcmp(text, "/kill") == 0)
			{
				kill(index, structures::death_suicide, -1);
			}

			else if (reader.overflow == false && text[0] == '/' && admin.listed(admin.admins, clients[index].name))
			{
				admin.command(text + 1, index);
			}

			else if (reader.overflow == false && text[0] && text[0] != '/')
			{
				chat(index, text);
			}
		}

		else if (message.type == structures::message_respawn && clients[index].alive == false)
		{
			spawn(index);
		}

		else if (message.type == structures::message_request && clients[index].alive)
		{
			handle_request(index, reader);
		}

		else if (message.type == structures::message_build && clients[index].alive)
		{
			handle_build(index, reader);
		}

		else if (message.type == structures::message_act && clients[index].alive)
		{
			handle_act(index, reader);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::handle_act(std::int32_t index, stream_reader_c& reader)
	{
		auto& peer{ clients[index] };
		auto& survivor{ survivors[index] };

		const auto action{ reader.u8() };
		const auto position{ structures::vec3_s{ reader.f32(), reader.f32(), reader.f32() } };
		const auto eye{ peer.state.position + structures::vec3_s{ 0.0f, peer.state.eye_height, 0.0f } };
		const auto slot{ std::min(peer.item, hotbar_slots - 1u) };

		survivor.position = peer.state.position;

		if (reader.overflow == false && std::isfinite(position.x) && std::isfinite(position.y) && std::isfinite(position.z))
		{
			const auto reachable{ mathematics.distance(position, eye) < farm_reach + 1.0f };

			if (action == structures::act_plant && reachable && farming.fertile(position))
			{
				farming.sow(survivor, slot, { position.x, terrain.height(position.x, position.z), position.z });
			}

			else if (action == structures::act_water && reachable)
			{
				if (const auto crop{ farming.crop_near(position) }; crop >= 0)
				{
					farming.water(static_cast<std::uint32_t>(crop), survivor, slot);
				}
			}

			else if (action == structures::act_reap && reachable)
			{
				if (const auto crop{ farming.crop_near(position) }; crop >= 0)
				{
					farming.reap(static_cast<std::uint32_t>(crop), survivor);
				}
			}

			else if (action == structures::act_drink)
			{
				farming.drink(survivor, eye, mathematics.forward_from_angles(peer.yaw, peer.pitch));
			}

			else if (action == structures::act_arrow && reachable)
			{
				projectiles.collect(survivor, position);
			}

			else if (action == structures::act_loot && reachable)
			{
				if (const auto bag{ loot.nearest(position) }; bag >= 0)
				{
					loot.take(static_cast<std::uint32_t>(bag), survivor);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_bags(std::int32_t index)
	{
		const auto total{ static_cast<std::uint32_t>(loot.bags.size()) };

		for (auto first{ 0u }; first < std::max(total, 1u); first += net_bags_per_message)
		{
			const auto span{ std::min(net_bags_per_message, total - std::min(first, total)) };

			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(total));
			writer.u16(static_cast<std::uint16_t>(first));
			writer.u8(static_cast<std::uint8_t>(span));

			for (auto entry{ 0u }; entry < span; entry++)
			{
				const auto& bag{ loot.bags[first + entry] };

				writer.u8(static_cast<std::uint8_t>((bag.active ? 1u : 0u) | (bag.sleeper ? 2u : 0u)));
				writer.f32(bag.position.x);
				writer.f32(bag.position.y);
				writer.f32(bag.position.z);
				writer.f32(bag.yaw);
				writer.u8(static_cast<std::uint8_t>(std::min(bag.items, 255u)));
				writer.text(bag.name, net_name_length);
			}

			if (writer.overflow == false)
			{
				transport.queue(clients[index].connection, structures::message_bags, scratch, writer.size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_crops(std::int32_t index)
	{
		const auto total{ static_cast<std::uint32_t>(farming.crops.size()) };

		for (auto first{ 0u }; first < std::max(total, 1u); first += net_crops_per_message)
		{
			const auto span{ std::min(net_crops_per_message, total - std::min(first, total)) };

			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(total));
			writer.u16(static_cast<std::uint16_t>(first));
			writer.u8(static_cast<std::uint8_t>(span));

			for (auto entry{ 0u }; entry < span; entry++)
			{
				const auto& crop{ farming.crops[first + entry] };

				writer.f32(crop.position.x);
				writer.f32(crop.position.y);
				writer.f32(crop.position.z);
				writer.u8(static_cast<std::uint8_t>(std::clamp(mathematics.wrap_angle(crop.yaw) / two_pi + 0.5f, 0.0f, 1.0f) * 255.0f));
				writer.u8(static_cast<std::uint8_t>(std::clamp(crop.growth, 0.0f, 1.0f) * 255.0f));
				writer.u8(static_cast<std::uint8_t>(std::clamp(crop.water, 0.0f, 1.0f) * 255.0f));
				writer.u8(static_cast<std::uint8_t>(std::clamp(crop.health, 0.0f, 1.0f) * 255.0f));
				writer.u16(static_cast<std::uint16_t>(std::clamp(crop.ripe_time, 0.0f, 65535.0f)));
				writer.u8(static_cast<std::uint8_t>(crop.kind));
				writer.u8(crop.dead ? 1u : 0u);
			}

			if (writer.overflow == false)
			{
				transport.queue(clients[index].connection, structures::message_crops, scratch, writer.size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::handle_build(std::int32_t index, stream_reader_c& reader)
	{
		auto& peer{ clients[index] };
		auto& survivor{ survivors[index] };

		structures::placement_s placement{};

		placement.piece = reader.u8();
		placement.position = { reader.f32(), reader.f32(), reader.f32() };
		placement.yaw = reader.f32();
		placement.anchor = static_cast<std::int32_t>(reader.u32());
		placement.valid = true;
		placement.active = true;

		const auto slot{ std::min(peer.item, hotbar_slots - 1u) };
		const auto held{ survivor.slots[inventory_slots + slot].item };
		const auto eye{ peer.state.position + structures::vec3_s{ 0.0f, peer.state.eye_height, 0.0f } };

		if (reader.overflow == false && placement.piece < structures::piece_count)
		{
			const auto& definition{ piece_definitions[placement.piece] };
			const auto holding{ definition.item == structures::item_building_plan ? held == structures::item_building_plan && placement.piece < structures::piece_door : held == definition.item };
			const auto affordable{ definition.item != structures::item_building_plan || survivor.count(definition.cost.item) >= definition.cost.amount };

			if (holding && affordable && building.permitted(placement, eye) && building.privileged(placement.position, mathematics.hash_text(peer.name)))
			{
				building.place(placement, survivor, slot, mathematics.hash_text(peer.name));
			}

			else if (building.privileged(placement.position, mathematics.hash_text(peer.name)) == false)
			{
				survivor.notify("Building blocked: someone else's tool cupboard", 0);
			}

			else
			{
				survivor.notify("Can't build there", 0);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::handle_request(std::int32_t index, stream_reader_c& reader)
	{
		auto& survivor{ survivors[index] };

		const auto type{ reader.u8() };
		const auto first{ static_cast<std::uint32_t>(reader.u16()) };
		const auto second{ static_cast<std::uint32_t>(reader.u16()) };

		survivor.position = clients[index].state.position;

		const auto reachable = [&](std::uint32_t structure)
			{
				return structure < building.placed.size() && building.placed[structure].destroyed == false && mathematics.distance(building.placed[structure].position, clients[index].state.position) < interact_range + 2.5f;
			};

		if (reader.overflow == false)
		{
			if (type == structures::request_swap && survivor.valid(first) && survivor.valid(second))
			{
				survivor.swap(first, second);

				if ((first >= container_address || second >= container_address) && survivor.open_container >= 0)
				{
					building.stirred.push_back(static_cast<std::uint32_t>(survivor.open_container));
				}
			}

			else if (type == structures::request_transfer && survivor.open_container >= 0 && second == static_cast<std::uint32_t>(survivor.open_container) && survivor.valid(first))
			{
				survivor.transfer(first);

				building.stirred.push_back(second);
			}

			else if (type == structures::request_door && reachable(first) && building.accessible(first, mathematics.hash_text(clients[index].name)))
			{
				building.toggle_door(first);
			}

			else if (const auto lock{ building.locks.find(first) }; type == structures::request_door && reachable(first) && lock != building.locks.end() && lock->second.coded)
			{
				send_keypad(index, first, false);
			}

			else if (type == structures::request_door && reachable(first))
			{
				survivor.notify("It's locked", 0);
			}

			else if (type == structures::request_lock && reachable(first) && survivor.slots[inventory_slots + std::min(clients[index].item, hotbar_slots - 1u)].item == structures::item_code_lock && building.attach_lock(first, mathematics.hash_text(clients[index].name)))
			{
				survivor.take(structures::item_code_lock, 1u);

				send_keypad(index, first, true);
			}

			else if (type == structures::request_lock && reachable(first))
			{
				survivor.notify("You can't put a lock on that door", 0);
			}

			else if (type == structures::request_rekey && reachable(first) && building.locks.count(first) && building.accessible(first, mathematics.hash_text(clients[index].name)))
			{
				send_keypad(index, first, true);
			}

			else if (type == structures::request_code && reachable(first) && clock - clients[index].keypad_clock >= lock_cooldown)
			{
				const auto result{ building.enter_code(first, mathematics.hash_text(clients[index].name), second) };

				clients[index].keypad_clock = clock;

				if (result == 2)
				{
					survivor.notify("Code set", 0);
				}

				else if (result == 1)
				{
					survivor.notify("Code accepted", 0);

					building.toggle_door(first);
				}

				else if (result == 0)
				{
					survivor.notify("Wrong code", 0);

					cue(index, structures::sound_hit_metal, 0.8f, 1.4f);

					hurt(index, lock_shock, structures::death_beaten, -1);
				}
			}

			else if (type == structures::request_upgrade && reachable(first) && building.placed[first].piece < structures::piece_door && building.placed[first].tier + 1u < building_tier_count)
			{
				const auto& next{ building_tiers[building.placed[first].tier + 1u] };
				const auto hammer{ survivor.slots[inventory_slots + std::min(clients[index].item, hotbar_slots - 1u)].item == structures::item_hammer };

				if (hammer && building.privileged(building.placed[first].position, mathematics.hash_text(clients[index].name)) && survivor.take(next.item, next.cost))
				{
					building.upgrade(first);
				}

				else
				{
					survivor.notify(hammer ? "You can't upgrade that" : "You need a hammer", 0);
				}
			}

			else if (type == structures::request_authorize && reachable(first))
			{
				building.authorize(first, mathematics.hash_text(clients[index].name));

				survivor.notify("You are authorized on this cupboard", 0);
			}

			else if (type == structures::request_open && first < building.containers.size() && reachable(building.containers[first].structure))
			{
				survivor.open_container = static_cast<std::int32_t>(first);

				send_container(index, first);
			}

			else if (type == structures::request_close)
			{
				survivor.open_container = -1;
			}

			else if (type == structures::request_light && survivor.open_container >= 0 && first == static_cast<std::uint32_t>(survivor.open_container))
			{
				auto& container{ building.containers[first] };

				const auto fueled{ container.slots[furnace_fuel_slot].item == structures::item_wood && container.slots[furnace_fuel_slot].amount > 0u };

				if (container.kind != structures::container_storage && (second == 0u || fueled))
				{
					container.burning = second != 0u;

					building.stirred.push_back(first);
					building.dirty.push_back(container.structure);
				}
			}

			else if (type == structures::request_craft && first < recipe_count)
			{
				survivor.craft(first);
			}

			else if (type == structures::request_consume && first < total_slots)
			{
				survivor.consume(first);
			}

			else if (type == structures::request_research && first < recipe_count)
			{
				survivor.research(first);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::read_input(std::int32_t index, stream_reader_c& reader)
	{
		auto& peer{ clients[index] };

		const auto sent{ reader.u32() };
		const auto count{ std::min<std::uint32_t>(reader.u8(), net_input_redundancy) };

		if (reader.overflow == false && static_cast<std::int32_t>(sent - peer.echo_stamp) > 0)
		{
			peer.echo_stamp = sent;
			peer.echo_received = arrival;
		}

		for (auto entry{ 0u }; entry < count; entry++)
		{
			structures::net_command_s command{};

			command.sequence = reader.u32();
			command.forward = reader.i8();
			command.side = reader.i8();
			command.yaw = reader.u16();
			command.pitch = reader.i16();
			command.buttons = reader.u16();
			command.slot = reader.u8();
			command.time = reader.u32();

			if (reader.overflow == false && command.sequence > peer.last_command && std::none_of(peer.commands.begin(), peer.commands.end(), [&](const structures::net_command_s& queued) { return queued.sequence == command.sequence; }))
			{
				const auto place{ std::find_if(peer.commands.begin(), peer.commands.end(), [&](const structures::net_command_s& queued) { return queued.sequence > command.sequence; }) };

				peer.commands.insert(place, command);
			}
		}

		while (peer.commands.size() > net_command_queue)
		{
			peer.commands.erase(peer.commands.begin());
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::simulate(std::float_t delta)
	{
		const auto started{ std::chrono::steady_clock::now() };

		train.place(clock);

		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			auto& peer{ clients[index] };

			if (peer.active)
			{
				if (peer.bot)
				{
					think_bot(index, delta);
				}

				peer.budget = std::min(peer.budget + delta, net_command_budget);

				if (peer.alive)
				{
					run_commands(index);

					if (peer.alive && peer.bot == false)
					{
						auto& survivor{ survivors[index] };

						const auto speed{ mathematics.length(structures::vec3_s{ peer.state.velocity.x, 0.0f, peer.state.velocity.z }) };

						survivor.position = peer.state.position;
						survivor.underwater = (peer.state.flags & structures::movement_underwater) != 0u;
						survivor.climate.swimming = (peer.state.flags & structures::movement_swimming) != 0u;
						survivor.climate.air = survivor.ambient(hours, weather_phases[weather_phase].cloud, weather_phases[weather_phase].rain, weather_phases[weather_phase].storm);
						survivor.climate.rain = weather_phases[weather_phase].rain;

						survivor.update(delta, 1.0f + std::clamp(speed / move_speed_run, 0.0f, 1.6f) * 0.6f);

						if (survivor.vitals.dead)
						{
							kill(index, survivor.harm, -1);
						}
					}
				}

				else
				{
					peer.respawn_timer -= delta;

					if (peer.respawn_timer <= 0.0f)
					{
						spawn(index);
					}
				}
			}
		}

		train.place(clock);

		record_trails();

		fauna.watchers.clear();

		for (const auto& peer : clients)
		{
			if (peer.active && peer.alive)
			{
				fauna.watchers.push_back({ peer.state.position, fauna.noise(peer.state) });
			}
		}

		fauna.simulate(delta);

		vehicles.simulate(delta);

		for (auto& vehicle : vehicles.list)
		{
			if (vehicle.scrape > vehicle_bang_speed)
			{
				sound_at(-1, structures::sound_hit_metal, vehicle.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f }, std::min(1.0f, vehicle.scrape / 12.0f), 0.7f + random() * 0.2f, audio_event_mid);
			}

			for (auto seat{ 0u }; seat < 2u; seat++)
			{
				if (const auto rider{ vehicle.riders[seat] }; rider >= 0 && (rider >= static_cast<std::int32_t>(clients.size()) || clients[rider].active == false || clients[rider].state.vehicle != vehicle.id || clients[rider].state.seat != seat))
				{
					vehicle.riders[seat] = -1;
				}

				else if (rider >= 0 && clients[rider].alive)
				{
					if (vehicle.health <= 0.0f)
					{
						vehicles.alight(clients[rider].state, rider);

						hurt(rider, vehicle_wreck_damage, structures::death_vehicle, -1);
					}

					else if (vehicle.scrape > vehicle_crash_speed)
					{
						hurt(rider, (vehicle.scrape - vehicle_crash_speed) * vehicle_bruise_scale, structures::death_vehicle, -1);
					}
				}
			}

			vehicle.scrape = 0.0f;
		}

		for (const auto& bite : fauna.bites)
		{
			for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
			{
				if (clients[index].active && clients[index].alive && mathematics.distance(bite, clients[index].state.position) < 2.5f)
				{
					hurt(index, fauna_charge_damage, structures::death_beaten, -1);
				}
			}
		}

		fauna.bites.clear();

		harvest.respawn(delta);

		building.smelt(delta);

		decay_timer += delta;

		if (decay_timer >= building_decay_interval)
		{
			building.decay(decay_timer);

			decay_timer = 0.0f;
		}

		farming.grow(delta);

		projectiles.advance(delta);

		loot.update(delta);

		if (loot.revision != bag_revision)
		{
			bag_revision = loot.revision;

			for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
			{
				if (clients[index].active && clients[index].bot == false)
				{
					send_bags(index);
				}
			}
		}

		crop_timer += delta;

		if (farming.revision != crop_revision || crop_timer >= net_crop_refresh)
		{
			crop_revision = farming.revision;
			crop_timer = 0.0f;

			for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
			{
				if (clients[index].active && clients[index].bot == false)
				{
					send_crops(index);
				}
			}
		}

		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			if (auto& survivor{ survivors[index] }; clients[index].active && survivor.open_container >= 0 && (static_cast<std::size_t>(survivor.open_container) >= building.containers.size() || mathematics.distance(building.placed[building.containers[survivor.open_container].structure].position, clients[index].state.position) > interact_range + 3.0f || building.placed[building.containers[survivor.open_container].structure].destroyed))
			{
				survivor.open_container = -1;
			}
		}

		broadcast_nodes();

		broadcast_structures();

		tick_cost = mathematics.lerp(tick_cost, std::chrono::duration<std::float_t>(std::chrono::steady_clock::now() - started).count(), 0.05f);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s server_c::present(const structures::movement_state_s& state)
	{
		return train.ready && state.platform && state.platform <= std::size(train_consist) ? mathematics.transform_point(state.local, train.pose(clock, state.platform - 1u)) : state.position;
	}
	/*
	//=====================================================================================
	*/
	void server_c::record_trails()
	{
		for (auto& peer : clients)
		{
			if (peer.active)
			{
				peer.trail[peer.trail_head % net_rewind_samples] = { clock, present(peer.state), peer.state.height, peer.alive };

				peer.trail_head++;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::trail_s server_c::rewound(std::int32_t index, std::double_t when)
	{
		const auto& peer{ clients[index] };
		const auto stored{ std::min(peer.trail_head, net_rewind_samples) };

		auto result{ structures::trail_s{ clock, present(peer.state), peer.state.height, peer.alive } };
		auto found{ false };

		for (auto step{ 1u }; step < stored && found == false; step++)
		{
			const auto& newer{ peer.trail[(peer.trail_head - step) % net_rewind_samples] };
			const auto& older{ peer.trail[(peer.trail_head - step - 1u) % net_rewind_samples] };

			if (older.time <= when && newer.time >= when)
			{
				const auto span{ newer.time - older.time };
				const auto t{ span > 0.0001 ? static_cast<std::float_t>((when - older.time) / span) : 1.0f };

				result = { when, mathematics.lerp(older.position, newer.position, t), t < 0.5f ? older.height : newer.height, older.alive && newer.alive };

				found = true;
			}

			else if (step + 1u == stored && older.time > when)
			{
				result = older;
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t server_c::ray_player(std::int32_t shooter, structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::double_t when, std::float_t lead, std::float_t& distance, std::float_t& height, std::float_t& top)
	{
		auto best{ -1 };

		distance = range;

		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			if (index != shooter && clients[index].active && clients[index].alive && mathematics.distance(present(clients[index].state), origin) < range + 8.0f)
			{
				auto sample{ rewound(index, when) };

				if (const auto carrier{ clients[index].state.platform }; lead > 0.0f && train.ready && carrier && carrier <= std::size(train_consist))
				{
					sample.position = mathematics.transform_point(mathematics.transform_point(sample.position, mathematics.inverse(train.pose(when, carrier - 1u))), train.pose(when + lead, carrier - 1u));
				}

				if (sample.alive)
				{
					const auto bottom{ sample.position + structures::vec3_s{ 0.0f, player_hit_radius, 0.0f } };
					const auto axis_length{ std::max(sample.height - player_hit_radius * 2.0f, 0.0f) };
					const auto offset{ origin - bottom };
					const auto bend{ direction.y };
					const auto denominator{ 1.0f - bend * bend };
					const auto first{ denominator > 0.000001f ? std::clamp((bend * offset.y - mathematics.dot(direction, offset)) / denominator, 0.0f, range) : 0.0f };
					const auto along{ std::clamp(bend * first + offset.y, 0.0f, axis_length) };
					const auto closest{ std::clamp(mathematics.dot(bottom + structures::vec3_s{ 0.0f, along, 0.0f } - origin, direction), 0.0f, range) };
					const auto gap{ mathematics.distance(origin + direction * closest, bottom + structures::vec3_s{ 0.0f, along, 0.0f }) };

					if (gap < player_hit_radius && closest < distance)
					{
						best = index;
						distance = closest;
						height = origin.y + direction.y * closest - sample.position.y;
						top = sample.height;
					}
				}
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	void server_c::shoot(std::int32_t index, const structures::usercmd_s& command)
	{
		const auto& peer{ clients[index] };
		const auto& definition{ weapon_definitions[peer.weapon.weapon] };
		const auto item{ survivors[index].slots[inventory_slots + peer.weapon.slot].item };
		const auto origin{ peer.state.position + structures::vec3_s{ 0.0f, peer.state.eye_height, 0.0f } };
		const auto direction{ mathematics.normalize(peer.weapon.shot) };
		const auto hit{ world.trace(origin, origin + direction * definition.range, { 0.01f, 0.01f, 0.01f }, structures::contents_solid) };
		const auto limit{ hit.hit ? hit.fraction * definition.range : definition.range };
		const auto when{ std::clamp(command.time - net_interpolation_delay, clock - net_rewind_limit, clock) };

		auto distance{ limit };
		auto height{ 0.0f };
		auto top{ player_height };
		auto slumber{ limit };

		const auto victim{ ray_player(index, origin, direction, limit, when, net_interpolation_delay, distance, height, top) };
		const auto sleeper{ loot.ray_sleeper(origin, direction, victim >= 0 ? distance : limit, slumber) };

		auto prey{ sleeper >= 0 ? slumber : (victim >= 0 ? distance : limit) };

		const auto animal{ fauna.ray(origin, direction, prey, prey) };

		fauna.alarm(origin, definition.loudness);

		if (animal >= 0)
		{
			const auto killed{ fauna.damage(static_cast<std::uint32_t>(animal), item_definitions[item].damage, origin) };

			send_hit(index, fauna_victim, item_definitions[item].damage, false, killed, origin + direction * prey);

			marks.bleed(origin + direction * prey, direction);
		}

		else if (sleeper >= 0)
		{
			const auto killed{ loot.strike(static_cast<std::uint32_t>(sleeper), item_definitions[item].damage) };

			send_hit(index, 0xFFFF, item_definitions[item].damage, false, killed, origin + direction * slumber);

			marks.bleed(origin + direction * slumber, direction);
		}

		else if (victim >= 0)
		{
			const auto headshot{ height > top - player_head_zone };
			const auto legs{ height < player_leg_zone };
			const auto damage{ item_definitions[item].damage * (headshot ? weapon_headshot_scale : (legs ? weapon_leg_scale : 1.0f)) };

			hurt(victim, damage, structures::death_shot, index);

			send_hit(index, victim, damage, headshot, clients[victim].alive == false, origin + direction * distance);

			marks.bleed(origin + direction * distance, direction);
		}

		else if (hit.hit)
		{
			marks.impact(hit, direction, item_definitions[item].damage, false);

			if (const auto mover{ hit.brush - mover_brush_base }; mover >= 0 && mover < static_cast<std::int32_t>(world.movers.size()) && world.movers[mover].owner >= vehicle_owner_base && world.movers[mover].owner < vehicle_owner_base + vehicles.list.size())
			{
				vehicles.damage(world.movers[mover].owner - vehicle_owner_base, item_definitions[item].damage * vehicle_bullet_scale);
			}

			else if (hit.brush >= 0)
			{
				building.damage(hit.brush, item_definitions[item].damage * 0.25f, true);
			}
		}

		shots.push_back({ static_cast<std::uint16_t>(index), static_cast<std::uint8_t>(peer.weapon.weapon), static_cast<std::uint8_t>(animal >= 0 || victim >= 0 || sleeper >= 0 ? 255u : (hit.hit ? std::min(hit.surface, 252u) : 254u)), origin, origin + direction * (animal >= 0 ? prey : (sleeper >= 0 ? slumber : (victim >= 0 ? distance : limit))) });
	}
	/*
	//=====================================================================================
	*/
	void server_c::use_tool(std::int32_t index, const structures::usercmd_s& command)
	{
		auto& peer{ clients[index] };
		auto& survivor{ survivors[index] };

		const auto slot{ std::min(command.weapon, hotbar_slots - 1u) };
		const auto eye{ peer.state.position + structures::vec3_s{ 0.0f, peer.state.eye_height, 0.0f } };
		const auto forward{ mathematics.forward_from_angles(command.yaw, command.pitch) };

		survivor.position = peer.state.position;

		if (peer.tool.events & structures::tool_event_strike)
		{
			auto& held{ survivor.slots[inventory_slots + slot] };

			const auto& definition{ item_definitions[held.item] };
			const auto reach{ std::max(definition.reach, 1.6f) + 0.3f };
			const auto when{ std::clamp(command.time - net_interpolation_delay, clock - net_rewind_limit, clock) };
			const auto blocked{ world.trace(eye, eye + forward * reach, { 0.02f, 0.02f, 0.02f }, structures::contents_solid) };

			auto distance{ reach };
			auto height{ 0.0f };
			auto top{ player_height };

			auto slumber{ reach };

			structures::vec3_s carved{};

			if (const auto sleeper{ loot.ray_sleeper(eye, forward, blocked.hit ? blocked.fraction * reach : reach, slumber) }; sleeper >= 0)
			{
				const auto damage{ std::max(definition.damage, 5.0f) };

				send_hit(index, 0xFFFF, damage, false, loot.strike(static_cast<std::uint32_t>(sleeper), damage), eye + forward * slumber);

				sound_at(index, structures::sound_hit_flesh, eye + forward * slumber, 0.9f, 1.0f, audio_event_mid);
			}

			else if (const auto victim{ ray_player(index, eye, forward, blocked.hit ? blocked.fraction * reach : reach, when, net_interpolation_delay, distance, height, top) }; victim >= 0)
			{
				const auto headshot{ height > top - player_head_zone };
				const auto damage{ std::max(definition.damage, 5.0f) * (headshot ? weapon_headshot_scale : 1.0f) };

				hurt(victim, damage, structures::death_beaten, index);

				send_hit(index, victim, damage, headshot, clients[victim].alive == false, eye + forward * distance);

				marks.bleed(eye + forward * distance, forward);

				sound_at(index, structures::sound_hit_flesh, eye + forward * distance, 0.9f, 1.0f, audio_event_mid);

				held.condition -= held.item && held.item != structures::item_rock ? 0.006f : 0.0f;
			}

			else if (const auto outcome{ fauna.melee(survivor, eye, forward, blocked.hit ? blocked.fraction * reach : reach, std::max(definition.damage, 5.0f), carved) }; outcome > 0u)
			{
				if (outcome < 3u)
				{
					send_hit(index, fauna_victim, std::max(definition.damage, 5.0f), false, outcome == 2u, carved);
				}

				sound_at(index, structures::sound_hit_flesh, carved, 0.9f, 1.0f, audio_event_mid);

				marks.bleed(carved, forward);

				held.condition -= held.item && held.item != structures::item_rock ? 0.004f : 0.0f;
			}

			else if (harvest.strike(survivor, slot, eye, forward, true) >= 0)
			{
				sound_at(index, harvest.struck_sound, harvest.struck_point, 1.0f, 1.0f, audio_event_far);

				if (harvest.struck_sound == structures::sound_hit_wood && harvest.random() < 0.4f)
				{
					sound_at(index, structures::sound_chop, harvest.struck_point, 0.6f, 1.0f, audio_event_far);
				}
			}
		}

		if (peer.tool.events & structures::tool_event_eat)
		{
			const auto eaten{ item_definitions[survivor.slots[inventory_slots + slot].item].name };

			if (survivor.consume(inventory_slots + slot))
			{
				survivor.notify(eaten, -1);
			}

			sound_at(index, structures::sound_pickup, eye, 0.4f, 0.8f, audio_event_near);
		}

		if (peer.tool.events & structures::tool_event_use)
		{
			harvest.interact(survivor, eye, forward, true);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::sound_events(std::int32_t index)
	{
		const auto& peer{ clients[index] };
		const auto& definition{ weapon_definitions[std::min<std::uint32_t>(peer.weapon.weapon, structures::weapon_count - 1u)] };
		const auto eye{ peer.state.position + structures::vec3_s{ 0.0f, peer.state.eye_height, 0.0f } };
		const auto events{ peer.weapon.events };

		if ((events & structures::weapon_event_reload) && peer.weapon.weapon != structures::weapon_none)
		{
			sound_at(index, definition.reload_sound, eye, 0.8f, 1.0f, audio_event_mid);
		}

		if (events & (structures::weapon_event_bolt | structures::weapon_event_clearing | structures::weapon_event_cleared))
		{
			sound_at(index, structures::sound_bolt, eye, 0.75f, (events & structures::weapon_event_clearing) ? 0.8f : 1.0f, audio_event_mid);
		}

		if (events & structures::weapon_event_jam)
		{
			sound_at(index, structures::sound_jam, eye, 0.7f, 1.0f, audio_event_mid);
		}

		if (events & (structures::weapon_event_dry | structures::weapon_event_misfire))
		{
			sound_at(index, structures::sound_dry_fire, eye, 0.6f, 1.0f, audio_event_near);
		}

		if (events & structures::weapon_event_drawing)
		{
			sound_at(index, structures::sound_equip, eye, 0.35f, 0.7f, audio_event_near);
		}

		if (peer.tool.events & structures::tool_event_whoosh)
		{
			sound_at(index, structures::sound_swing, eye, 0.35f, 1.0f, audio_event_near);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::broadcast_nodes()
	{
		for (const auto index : harvest.changed)
		{
			if (index < harvest.nodes.size())
			{
				stream_writer_c writer{};

				writer.reset(scratch, sizeof(scratch));

				writer.u32(index);
				writer.u8(harvest.nodes[index].depleted ? 1u : 0u);
				writer.u8(static_cast<std::uint8_t>(static_cast<std::int32_t>(std::floor(harvest.nodes[index].fall / two_pi * 256.0f)) & 255));

				broadcast(structures::message_node, scratch, writer.size, -1);
			}
		}

		harvest.changed.clear();
	}
	/*
	//=====================================================================================
	*/
	void server_c::write_structure(stream_writer_c& writer, std::uint32_t structure)
	{
		const auto& piece{ building.placed[structure] };
		const auto burning{ piece.container >= 0 && building.containers[piece.container].burning };

		writer.u32(structure);
		writer.u8(static_cast<std::uint8_t>(piece.piece));
		writer.f32(piece.position.x);
		writer.f32(piece.position.y);
		writer.f32(piece.position.z);
		writer.f32(piece.yaw);
		writer.u32(static_cast<std::uint32_t>(piece.anchor));
		writer.u32(piece.owner);
		writer.f32(piece.health);
		writer.u8(static_cast<std::uint8_t>(piece.tier));
		writer.u8(static_cast<std::uint8_t>((piece.open ? 1u : 0u) | (piece.destroyed ? 2u : 0u) | (burning ? 4u : 0u) | (building.locks.count(structure) ? 8u : 0u)));
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_keypad(std::int32_t index, std::uint32_t door, bool setting)
	{
		stream_writer_c writer{};

		writer.reset(scratch, sizeof(scratch));

		writer.u32(door);
		writer.u8(setting ? 1u : 0u);

		transport.queue(clients[index].connection, structures::message_keypad, scratch, writer.size);
	}
	/*
	//=====================================================================================
	*/
	void server_c::broadcast_structures()
	{
		std::sort(building.dirty.begin(), building.dirty.end());

		building.dirty.erase(std::unique(building.dirty.begin(), building.dirty.end()), building.dirty.end());

		for (auto first{ 0u }; first < building.dirty.size(); first += net_structures_per_message)
		{
			const auto span{ std::min<std::uint32_t>(net_structures_per_message, static_cast<std::uint32_t>(building.dirty.size()) - first) };

			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(span));

			for (auto entry{ 0u }; entry < span; entry++)
			{
				write_structure(writer, building.dirty[first + entry]);
			}

			if (writer.overflow == false)
			{
				broadcast(structures::message_structures, scratch, writer.size, -1);
			}
		}

		building.dirty.clear();

		std::sort(building.stirred.begin(), building.stirred.end());

		building.stirred.erase(std::unique(building.stirred.begin(), building.stirred.end()), building.stirred.end());

		for (const auto container : building.stirred)
		{
			for (auto viewer{ 0 }; viewer < static_cast<std::int32_t>(clients.size()); viewer++)
			{
				if (clients[viewer].active && clients[viewer].bot == false && survivors[viewer].open_container == static_cast<std::int32_t>(container))
				{
					send_container(viewer, container);
				}
			}
		}

		building.stirred.clear();
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_structures(std::int32_t index)
	{
		const auto count{ static_cast<std::uint32_t>(building.placed.size()) };

		for (auto first{ 0u }; first < count; first += net_structures_per_message)
		{
			const auto span{ std::min(net_structures_per_message, count - first) };

			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(span));

			for (auto entry{ 0u }; entry < span; entry++)
			{
				write_structure(writer, first + entry);
			}

			if (writer.overflow == false)
			{
				transport.queue(clients[index].connection, structures::message_structures, scratch, writer.size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_container(std::int32_t index, std::uint32_t container)
	{
		if (container < building.containers.size() && clients[index].bot == false)
		{
			const auto& box{ building.containers[container] };

			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u32(container);
			writer.u8(box.burning ? 1u : 0u);

			for (const auto& slot : box.slots)
			{
				writer.u16(static_cast<std::uint16_t>(slot.item));
				writer.u16(static_cast<std::uint16_t>(std::min(slot.amount, 65535u)));
				writer.f32(slot.condition);
				writer.u8(static_cast<std::uint8_t>(std::min(slot.loaded, 255u)));
			}

			transport.queue(clients[index].connection, structures::message_container, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_nodes(std::int32_t index)
	{
		const auto count{ static_cast<std::uint32_t>(harvest.nodes.size()) };
		const auto per_message{ (net_reliable_bytes - 8u) * 8u };

		for (auto first{ 0u }; first < count; first += per_message)
		{
			const auto span{ std::min(per_message, count - first) };

			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u32(first);
			writer.u16(static_cast<std::uint16_t>(span));

			for (auto offset{ 0u }; offset < span; offset += 8u)
			{
				auto bits{ 0u };

				for (auto bit{ 0u }; bit < 8u && offset + bit < span; bit++)
				{
					bits |= harvest.nodes[first + offset + bit].depleted ? 1u << bit : 0u;
				}

				writer.u8(static_cast<std::uint8_t>(bits));
			}

			if (writer.overflow == false)
			{
				transport.queue(clients[index].connection, structures::message_nodes, scratch, writer.size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_hit(std::int32_t shooter, std::int32_t victim, std::float_t damage, bool headshot, bool killed, structures::vec3_s point)
	{
		if (clients[shooter].bot == false)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(victim));
			writer.u8(static_cast<std::uint8_t>(std::clamp(damage, 0.0f, 255.0f)));
			writer.u8(static_cast<std::uint8_t>((headshot ? 1u : 0u) | (killed ? 2u : 0u)));
			writer.f32(point.x);
			writer.f32(point.y);
			writer.f32(point.z);

			transport.queue(clients[shooter].connection, structures::message_hit, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::run_commands(std::int32_t index)
	{
		auto& peer{ clients[index] };

		auto executed{ 0u };

		while (peer.commands.size() && executed < net_commands_per_tick && peer.budget >= tick_interval && peer.alive)
		{
			const auto net{ peer.commands.front() };

			peer.commands.erase(peer.commands.begin());

			structures::usercmd_s command{};

			command.sequence = net.sequence;
			command.forward = std::clamp(static_cast<std::float_t>(net.forward) / 127.0f, -1.0f, 1.0f);
			command.side = std::clamp(static_cast<std::float_t>(net.side) / 127.0f, -1.0f, 1.0f);
			command.yaw = transport.decode_angle(net.yaw);
			command.pitch = transport.decode_pitch(net.pitch);
			command.buttons = net.buttons;
			command.weapon = std::min<std::uint32_t>(net.slot, hotbar_slots - 1u);
			command.delta = tick_interval;
			command.time = peer.bot ? transport.quantize_time(clock) : std::clamp(transport.decode_time(net.time, clock), clock - net_time_window, clock + net_time_lead);

			peer.command_time = command.time;

			vehicles.pilot(peer.state, command);

			movement.simulate(peer.state, command);

			marks.tread(peer.state, peer.tread);

			if ((command.buttons & structures::button_use) && (peer.tool.flags & structures::tool_flag_use_held) == 0u)
			{
				const auto seated{ (peer.state.flags & structures::movement_seated) != 0u };

				if (seated || vehicles.board(peer.state, index, peer.state.position + structures::vec3_s{ 0.0f, peer.state.eye_height, 0.0f }, mathematics.forward_from_angles(command.yaw, command.pitch)))
				{
					if (seated)
					{
						vehicles.alight(peer.state, index);
					}

					peer.tool.flags |= structures::tool_flag_use_held;
				}
			}

			const auto usable{ peer.alive && (peer.state.flags & (structures::movement_swimming | structures::movement_seated)) == 0u };

			weapons.step(peer.weapon, survivors[index], command, usable, mathematics.length(structures::vec3_s{ peer.state.velocity.x, 0.0f, peer.state.velocity.z }) > 1.0f);

			if (peer.weapon.events & structures::weapon_event_fired)
			{
				shoot(index, command);
			}

			if (peer.weapon.events & structures::weapon_event_loosed)
			{
				const auto forward{ mathematics.forward_from_angles(command.yaw, command.pitch) };
				const auto up{ mathematics.cross(forward, mathematics.normalize(mathematics.cross({ 0.0f, 1.0f, 0.0f }, forward))) };
				const auto origin{ peer.state.position + structures::vec3_s{ 0.0f, peer.state.eye_height, 0.0f } + forward * 0.35f - up * 0.05f };
				const auto velocity{ peer.weapon.shot * (arrow_speed_minimum + (arrow_speed_maximum - arrow_speed_minimum) * peer.weapon.power * peer.weapon.power) };

				projectiles.launch(origin, velocity, item_definitions[survivors[index].slots[inventory_slots + peer.weapon.slot].item].damage * (0.3f + 0.7f * peer.weapon.power), index);

				shots.push_back({ static_cast<std::uint16_t>(index), static_cast<std::uint8_t>(peer.weapon.weapon), 253u, origin, origin + velocity });
			}

			harvest.step(peer.tool, survivors[index], command, usable);

			sound_events(index);

			if (peer.tool.events & (structures::tool_event_strike | structures::tool_event_eat | structures::tool_event_use))
			{
				use_tool(index, command);
			}

			peer.budget -= tick_interval;
			peer.last_command = net.sequence;
			peer.yaw = command.yaw;
			peer.pitch = command.pitch;
			peer.item = command.weapon;

			if (peer.state.flags & structures::movement_landed)
			{
				hurt(index, movement.fall_damage(peer.state), structures::death_fall, -1);
			}

			structures::vec3_s shove{};

			if (const auto blow{ train.strike(peer.state, command.time, shove) }; blow > 0.0f && clock - peer.struck > train_strike_cooldown)
			{
				peer.struck = clock;
				peer.state.velocity = shove;
				peer.state.flags &= ~structures::movement_on_ground;

				sound_at(-1, structures::sound_hit_flesh, peer.state.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f }, 1.0f, 0.8f, audio_event_far);

				marks.bleed(peer.state.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f }, mathematics.normalize(structures::vec3_s{ shove.x, -0.4f, shove.z }));

				hurt(index, blow, structures::death_train, -1);
			}

			if (peer.state.position.y < world.kill_height)
			{
				hurt(index, maximum_health * 10.0f, structures::death_world, -1);
			}

			executed++;
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::hurt(std::int32_t index, std::float_t amount, std::uint8_t cause, std::int32_t attacker)
	{
		if (clients[index].alive && amount > 0.5f)
		{
			if (attacker >= 0 && attacker != index && clients[index].bot == false)
			{
				stream_writer_c writer{};

				writer.reset(scratch, sizeof(scratch));

				writer.f32(clients[attacker].state.position.x);
				writer.f32(clients[attacker].state.position.y + clients[attacker].state.eye_height);
				writer.f32(clients[attacker].state.position.z);

				transport.queue(clients[index].connection, structures::message_hurt, scratch, writer.size);
			}

			survivors[index].damage(amount);

			if (survivors[index].vitals.dead)
			{
				kill(index, cause, attacker);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::kill(std::int32_t index, std::uint8_t cause, std::int32_t attacker)
	{
		auto& peer{ clients[index] };

		if (peer.alive)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(index));
			writer.u16(static_cast<std::uint16_t>(attacker < 0 ? 0xFFFF : attacker));
			writer.u8(cause);

			survivors[index].vitals.health = 0.0f;
			survivors[index].vitals.dead = true;

			if (peer.state.flags & structures::movement_seated)
			{
				vehicles.alight(peer.state, index);
			}

			if (peer.bot == false)
			{
				loot.drop(survivors[index], peer.state.position, peer.yaw, peer.name);
			}

			if (peer.state.water_depth < 0.1f && (cause == structures::death_shot || cause == structures::death_beaten || cause == structures::death_fall || cause == structures::death_train))
			{
				marks.pool(peer.state.position);
			}

			peer.alive = false;
			peer.respawn_timer = peer.bot ? net_bot_respawn : net_player_respawn;
			peer.state.velocity = {};

			peer.commands.clear();

			broadcast(structures::message_death, scratch, writer.size, -1);

			logger.write("server: %s died (%u)", peer.name, cause);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::think_bot(std::int32_t index, std::float_t delta)
	{
		auto& peer{ clients[index] };

		peer.bot_timer -= delta;

		if (peer.bot_timer <= 0.0f)
		{
			peer.bot_timer = net_bot_think * (0.5f + random());
			peer.bot_yaw = peer.state.water_depth > 0.8f ? std::atan2(-peer.state.position.x, -peer.state.position.z) : mathematics.wrap_angle(peer.bot_yaw + (random() - 0.5f) * 2.4f);
		}

		const auto count{ static_cast<std::uint32_t>(delta / tick_interval + 0.5f) };

		for (auto step{ 0u }; step < count; step++)
		{
			structures::net_command_s command{};

			command.sequence = peer.last_command + static_cast<std::uint32_t>(peer.commands.size()) + 1u;
			command.forward = 127;
			command.yaw = transport.encode_angle(peer.bot_yaw);
			command.buttons = static_cast<std::uint16_t>((index % 3 == 0 ? structures::button_sprint : 0u) | (random() < 0.004f ? structures::button_jump : 0u));

			peer.commands.push_back(command);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::spawn(std::int32_t index)
	{
		auto& peer{ clients[index] };

		const auto identity{ mathematics.hash_text(peer.name) };
		const auto bag{ std::find_if(building.placed.begin(), building.placed.end(), [&](const structures::structure_s& structure) { return structure.piece == structures::piece_sleeping_bag && structure.destroyed == false && structure.owner == identity; }) };

		if (bag != building.placed.end() && peer.bot == false)
		{
			movement.reset(peer.state, bag->position + structures::vec3_s{ 0.0f, 0.2f, 0.0f }, bag->yaw + pi);

			peer.yaw = bag->yaw + pi;
		}

		else if (maps.spawns.size())
		{
			const auto& point{ maps.spawns[forced_spawn >= 0 && peer.bot == false ? static_cast<std::size_t>(forced_spawn) % maps.spawns.size() : static_cast<std::size_t>(random() * static_cast<std::float_t>(maps.spawns.size())) % maps.spawns.size()] };
			const auto angle{ random() * two_pi };
			const auto spread{ std::sqrt(random()) * net_spawn_spread };
			const auto x{ point.position.x + std::sin(angle) * spread };
			const auto z{ point.position.z + std::cos(angle) * spread };
			const auto ground{ terrain.enabled ? std::max(terrain.height(x, z), sea_level - 1.2f) : point.position.y };

			movement.reset(peer.state, { x, ground + 0.05f, z }, point.yaw);

			peer.yaw = point.yaw;
			peer.bot_yaw = point.yaw;
		}

		if (forced_herd && peer.bot == false)
		{
			fauna.relocate(0u, peer.state.position, peer.yaw);
		}


		if (forced_ride && train.ready && peer.bot == false)
		{
			const auto& kind{ train_vehicles[train_consist[1]] };
			const auto seat{ train.pose(clock, 1u) };

			train.place(clock);

			peer.state.local = { (static_cast<std::float_t>(index % 3) - 1.0f) * 0.7f, kind.deck + 0.05f, -1.2f + static_cast<std::float_t>(index % 4) * 0.8f };
			peer.state.position = mathematics.transform_point(peer.state.local, seat);
			peer.state.velocity = {};
			peer.state.platform = 2u;
			peer.state.flags |= structures::movement_on_ground | structures::movement_riding;
			peer.yaw = std::atan2(seat.row3(2u).x, seat.row3(2u).z);
		}

		peer.alive = true;
		peer.respawn_timer = 0.0f;
		peer.inventory_timer = 0.0f;
		peer.weapon = {};
		peer.weapon.seed = mathematics.hash_u32(static_cast<std::uint32_t>(index) * 0x9E3779B9u + weapon_seed_salt);
		peer.weapon.flags = structures::weapon_flag_cycled | structures::weapon_flag_worked;
		peer.trail_head = 0u;

		for (auto& sample : peer.trail)
		{
			sample = {};
		}

		peer.commands.clear();

		survivors[index].reset();

		survivors[index].position = peer.state.position;

		if (peer.bot == false)
		{
			survivors[index].give_kit();
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_snapshots()
	{
		build_grid();

		share_marks();

		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			auto& peer{ clients[index] };

			if (peer.active && peer.bot == false)
			{
				gather(index);

				send_marks(index);

				const auto armed{ peer.weapon.weapon | (peer.weapon.slot << 8u) | ((peer.weapon.flags & structures::weapon_flag_jammed) << 16u) | (peer.weapon.reloading > 0.0f ? 1u << 20u : 0u) | (peer.weapon.clearing > 0.0f ? 1u << 21u : 0u) | (peer.weapon.hangfire > 0.0f ? 1u << 22u : 0u) };

				if (const auto hash{ survivors[index].fingerprint() * 31u + armed }; hash != peer.inventory_hash || clock - peer.inventory_timer >= net_inventory_refresh)
				{
					send_inventory(index);

					peer.inventory_hash = hash;
					peer.inventory_timer = clock;
				}

				stream_writer_c writer{};

				writer.reset(packet, sizeof(packet));

				transport.begin(peer.connection, writer, clock);

				writer.u8(structures::payload_snapshot);
				writer.f64(clock);
				writer.u32(peer.echo_stamp);
				writer.f32(static_cast<std::float_t>(clock - peer.echo_received));
				writer.u32(peer.last_command);
				writer.bytes(&peer.state, sizeof(peer.state));
				writer.u16(static_cast<std::uint16_t>(std::clamp(survivors[index].vitals.health * 100.0f, 0.0f, 65535.0f)));
				writer.u16(static_cast<std::uint16_t>(std::clamp(survivors[index].vitals.calories * 10.0f, 0.0f, 65535.0f)));
				writer.u16(static_cast<std::uint16_t>(std::clamp(survivors[index].vitals.hydration * 10.0f, 0.0f, 65535.0f)));
				writer.u8(static_cast<std::uint8_t>(std::clamp(survivors[index].vitals.breath * 255.0f, 0.0f, 255.0f)));
				writer.u8(static_cast<std::uint8_t>(std::clamp(survivors[index].climate.wetness * 255.0f, 0.0f, 255.0f)));
				writer.i8(static_cast<std::int8_t>(std::clamp(std::round(survivors[index].climate.temperature), -99.0f, 99.0f)));
				writer.u8(peer.alive ? 1u : 0u);
				writer.f32(hours);
				writer.u8(static_cast<std::uint8_t>(weather_phases[weather_phase].cloud * 255.0f));
				writer.u8(static_cast<std::uint8_t>(weather_phases[weather_phase].rain * 255.0f));
				writer.u8(static_cast<std::uint8_t>(weather_phases[weather_phase].storm * 255.0f));

				const auto driven{ (peer.state.flags & structures::movement_seated) && peer.state.seat == 0u ? vehicles.find(peer.state.vehicle) : nullptr };

				writer.u8(driven ? 1u : 0u);

				if (driven)
				{
					vehicles.write_state(writer, *driven);
				}

				vehicles.write(writer, peer.state.position, driven ? driven->id : 0u);

				heard.clear();

				for (auto shot{ 0u }; shot < shots.size() && heard.size() < net_snapshot_shots; shot++)
				{
					if (shots[shot].shooter != index && mathematics.distance(shots[shot].origin, peer.state.position) < (shots[shot].result == 253u ? net_tracer_range : net_shot_range * weapon_definitions[shots[shot].weapon].loudness))
					{
						heard.push_back(shot);
					}
				}

				const auto reserved{ 3u + static_cast<std::uint32_t>(heard.size()) * net_shot_bytes + fauna_snapshot_reserve * fauna_animal_bytes };
				const auto room{ writer.remaining() > reserved ? (writer.remaining() - reserved) / net_player_bytes : 0u };
				const auto count{ static_cast<std::uint32_t>(std::min<std::size_t>({ nearby.size(), static_cast<std::size_t>(net_snapshot_players), static_cast<std::size_t>(room) })) };

				writer.u8(static_cast<std::uint8_t>(count));

				for (auto entry{ 0u }; entry < count; entry++)
				{
					write_player(writer, nearby[entry].second);
				}

				writer.u8(static_cast<std::uint8_t>(heard.size()));

				for (const auto shot : heard)
				{
					const auto& event{ shots[shot] };

					writer.u16(event.shooter);
					writer.u8(event.weapon);
					writer.u8(event.result);
					writer.i16(static_cast<std::int16_t>(std::clamp(event.origin.x * net_position_scale, -32767.0f, 32767.0f)));
					writer.i16(static_cast<std::int16_t>(std::clamp(event.origin.y * net_position_scale, -32767.0f, 32767.0f)));
					writer.i16(static_cast<std::int16_t>(std::clamp(event.origin.z * net_position_scale, -32767.0f, 32767.0f)));
					writer.i16(static_cast<std::int16_t>(std::clamp(event.end.x * net_position_scale, -32767.0f, 32767.0f)));
					writer.i16(static_cast<std::int16_t>(std::clamp(event.end.y * net_position_scale, -32767.0f, 32767.0f)));
					writer.i16(static_cast<std::int16_t>(std::clamp(event.end.z * net_position_scale, -32767.0f, 32767.0f)));
				}

				fauna.write(writer, peer.state.position);

				if (writer.overflow == false)
				{
					send_raw(peer.connection.address, packet, writer.size);
				}
			}
		}

		shots.clear();
	}
	/*
	//=====================================================================================
	*/
	void server_c::share_marks()
	{
		const auto span{ static_cast<std::int32_t>(mark_cells) };

		for (const auto slot : marks.fresh)
		{
			if (marks.ring[slot].live)
			{
				const auto cell{ marks.ring[slot].cell };
				const auto column{ static_cast<std::int32_t>(cell) % span };
				const auto row{ static_cast<std::int32_t>(cell) / span };

				for (auto& peer : clients)
				{
					if (peer.active && peer.bot == false && peer.mark_center >= 0 && std::abs(peer.mark_center % span - column) <= mark_interest && std::abs(peer.mark_center / span - row) <= mark_interest && peer.mark_fresh.size() < mark_backlog && std::find(peer.mark_sync.begin(), peer.mark_sync.end(), cell) == peer.mark_sync.end())
					{
						peer.mark_fresh.push_back(slot);
					}
				}
			}
		}

		marks.fresh.clear();

		marks.expire();
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_marks(std::int32_t index)
	{
		auto& peer{ clients[index] };

		const auto span{ static_cast<std::int32_t>(mark_cells) };
		const auto center{ static_cast<std::int32_t>(marks.cell_of(peer.state.position)) };
		const auto column{ center % span };
		const auto row{ center / span };

		if (center != peer.mark_center)
		{
			const auto before{ peer.mark_center };

			peer.mark_sync.erase(std::remove_if(peer.mark_sync.begin(), peer.mark_sync.end(), [&](std::uint16_t cell) { return std::abs(static_cast<std::int32_t>(cell) % span - column) > mark_interest || std::abs(static_cast<std::int32_t>(cell) / span - row) > mark_interest; }), peer.mark_sync.end());

			for (auto z{ std::max(row - mark_interest, 0) }; z <= std::min(row + mark_interest, span - 1); z++)
			{
				for (auto x{ std::max(column - mark_interest, 0) }; x <= std::min(column + mark_interest, span - 1); x++)
				{
					const auto known{ before >= 0 && std::abs(before % span - x) <= mark_interest && std::abs(before / span - z) <= mark_interest };
					const auto cell{ static_cast<std::uint16_t>(z * span + x) };

					if (known == false && std::find(peer.mark_sync.begin(), peer.mark_sync.end(), cell) == peer.mark_sync.end())
					{
						peer.mark_sync.push_back(cell);
					}
				}
			}

			peer.mark_center = center;
		}

		for (auto synced{ 0u }; synced < mark_cells_per_flush && peer.mark_sync.size() && peer.connection.outgoing.size() < mark_queue_room; synced++)
		{
			const auto cell{ peer.mark_sync.front() };

			auto cursor{ marks.heads[cell] };
			auto replace{ true };

			peer.mark_sync.erase(peer.mark_sync.begin());

			while ((cursor >= 0 || replace) && peer.connection.outgoing.size() + 4u < net_reliable_capacity)
			{
				stream_writer_c writer{};

				writer.reset(scratch, sizeof(scratch));

				writer.u8(replace ? 1u : 0u);
				writer.u16(cell);
				writer.u8(0u);

				auto written{ 0u };

				for (; cursor >= 0 && written < marks_per_message; cursor = marks.ring[cursor].next)
				{
					marks.write(writer, marks.ring[cursor]);

					written++;
				}

				scratch[3] = static_cast<std::uint8_t>(written);

				transport.queue(peer.connection, structures::message_marks, scratch, writer.size);

				replace = false;
			}
		}

		while (peer.mark_fresh.size() && peer.connection.outgoing.size() < mark_queue_room)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u8(0u);
			writer.u16(0u);
			writer.u8(0u);

			auto written{ 0u };
			auto taken{ 0u };

			for (; taken < peer.mark_fresh.size() && written < marks_per_message; taken++)
			{
				if (const auto& mark{ marks.ring[peer.mark_fresh[taken]] }; mark.live)
				{
					marks.write(writer, mark);

					written++;
				}
			}

			scratch[3] = static_cast<std::uint8_t>(written);

			peer.mark_fresh.erase(peer.mark_fresh.begin(), peer.mark_fresh.begin() + static_cast<std::ptrdiff_t>(taken));

			if (written)
			{
				transport.queue(peer.connection, structures::message_marks, scratch, writer.size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::build_grid()
	{
		std::fill(cells.begin(), cells.end(), -1);

		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			auto& peer{ clients[index] };

			links[index] = -1;
			peer.cell = peer.active ? cell_of(peer.state.position) : -1;

			if (peer.cell >= 0)
			{
				links[index] = cells[peer.cell];
				cells[peer.cell] = index;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::gather(std::int32_t index)
	{
		const auto center{ clients[index].state.position };
		const auto reach{ static_cast<std::int32_t>(std::ceil(net_interest_radius / net_grid_cell)) };
		const auto origin{ -net_grid_cell * static_cast<std::float_t>(net_grid_size) * 0.5f };
		const auto column{ static_cast<std::int32_t>(std::floor((center.x - origin) / net_grid_cell)) };
		const auto row{ static_cast<std::int32_t>(std::floor((center.z - origin) / net_grid_cell)) };
		const auto size{ static_cast<std::int32_t>(net_grid_size) };

		auto& priority{ clients[index].priority };

		nearby.clear();

		if (priority.size() != clients.size())
		{
			priority.assign(clients.size(), 0.0f);
		}

		for (auto z{ std::max(row - reach, 0) }; z <= std::min(row + reach, size - 1); z++)
		{
			for (auto x{ std::max(column - reach, 0) }; x <= std::min(column + reach, size - 1); x++)
			{
				for (auto other{ cells[static_cast<std::size_t>(z) * net_grid_size + x] }; other >= 0; other = links[other])
				{
					const auto distance{ mathematics.distance(center, clients[other].state.position) };

					if (other != index && distance < net_interest_radius)
					{
						priority[other] += 1.0f + net_priority_near * (1.0f - distance / net_interest_radius) * (1.0f - distance / net_interest_radius);

						nearby.push_back({ -priority[other], other });
					}
				}
			}
		}

		const auto keep{ std::min<std::size_t>(nearby.size(), net_snapshot_players) };

		std::partial_sort(nearby.begin(), nearby.begin() + static_cast<std::ptrdiff_t>(keep), nearby.end());

		for (auto entry{ 0u }; entry < keep; entry++)
		{
			priority[nearby[entry].second] = 0.0f;
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::write_player(stream_writer_c& writer, std::int32_t index)
	{
		const auto& peer{ clients[index] };
		const auto& state{ peer.state };
		const auto position{ present(state) };

		writer.u16(static_cast<std::uint16_t>(index));
		writer.i16(static_cast<std::int16_t>(std::clamp(position.x * net_position_scale, -32767.0f, 32767.0f)));
		writer.i16(static_cast<std::int16_t>(std::clamp(position.y * net_position_scale, -32767.0f, 32767.0f)));
		writer.i16(static_cast<std::int16_t>(std::clamp(position.z * net_position_scale, -32767.0f, 32767.0f)));
		writer.i8(static_cast<std::int8_t>(std::clamp(state.velocity.x * net_velocity_scale, -127.0f, 127.0f)));
		writer.i8(static_cast<std::int8_t>(std::clamp(state.velocity.y * net_velocity_scale, -127.0f, 127.0f)));
		writer.i8(static_cast<std::int8_t>(std::clamp(state.velocity.z * net_velocity_scale, -127.0f, 127.0f)));
		writer.u16(transport.encode_angle(peer.yaw));
		writer.i8(static_cast<std::int8_t>(std::clamp(peer.pitch / half_pi * 127.0f, -127.0f, 127.0f)));
		writer.u16(static_cast<std::uint16_t>((state.flags & 0x7FFFu) | (peer.alive ? 0u : 0x8000u)));
		writer.u8(static_cast<std::uint8_t>(std::clamp(survivors[index].vitals.health, 0.0f, 255.0f)));
		writer.u8(static_cast<std::uint8_t>(std::min(survivors[index].slots[inventory_slots + std::min(peer.item, hotbar_slots - 1u)].item, 255u)));
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_inventory(std::int32_t index)
	{
		const auto& survivor{ survivors[index] };

		stream_writer_c writer{};

		writer.reset(scratch, sizeof(scratch));

		writer.u32(clients[index].last_command);
		writer.bytes(&clients[index].weapon, sizeof(clients[index].weapon));

		for (const auto& slot : survivor.slots)
		{
			writer.u16(static_cast<std::uint16_t>(slot.item));
			writer.u16(static_cast<std::uint16_t>(std::min(slot.amount, 65535u)));
			writer.f32(slot.condition);
			writer.u8(static_cast<std::uint8_t>(std::min(slot.loaded, 255u)));
		}

		writer.u8(static_cast<std::uint8_t>(survivor.queue_count));

		for (auto entry{ 0u }; entry < survivor.queue_count; entry++)
		{
			writer.u8(static_cast<std::uint8_t>(survivor.queue[entry].recipe));
			writer.f32(survivor.queue[entry].remaining);
		}

		for (auto recipe{ 0u }; recipe < recipe_count; recipe += 8u)
		{
			auto bits{ 0u };

			for (auto bit{ 0u }; bit < 8u && recipe + bit < recipe_count; bit++)
			{
				bits |= survivor.known[recipe + bit] ? 1u << bit : 0u;
			}

			writer.u8(static_cast<std::uint8_t>(bits));
		}

		if (writer.overflow == false)
		{
			transport.queue(clients[index].connection, structures::message_inventory, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::notify(std::int32_t index, const char* text, std::int32_t amount)
	{
		if (clients[index].active && clients[index].bot == false)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.text(text, 96u);
			writer.i16(static_cast<std::int16_t>(std::clamp(amount, -32767, 32767)));

			transport.queue(clients[index].connection, structures::message_notice, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::cue(std::int32_t index, std::uint32_t sound, std::float_t volume, std::float_t pitch)
	{
		if (clients[index].active && clients[index].bot == false)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(sound));
			writer.f32(volume);
			writer.f32(pitch);

			transport.queue(clients[index].connection, structures::message_cue, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_accept(std::int32_t index, std::uint32_t salt)
	{
		stream_writer_c writer{};

		writer.reset(packet, sizeof(packet));

		writer.u32(net_protocol_id);
		writer.u8(structures::packet_accept);
		writer.u32(salt);
		writer.u16(static_cast<std::uint16_t>(index));
		writer.f64(clock);
		writer.u16(static_cast<std::uint16_t>(maximum));
		writer.text(name, net_server_name_length);
		writer.text(map, 32u);
		writer.text(clients[index].name, net_name_length);

		send_raw(clients[index].connection.address, packet, writer.size);
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_reject(const structures::address_s& address, std::uint8_t reason)
	{
		stream_writer_c writer{};

		writer.reset(packet, sizeof(packet));

		writer.u32(net_protocol_id);
		writer.u8(structures::packet_reject);
		writer.u8(reason);

		send_raw(address, packet, writer.size);
	}
	/*
	//=====================================================================================
	*/
	void server_c::broadcast(std::uint8_t type, const void* data, std::uint32_t size, std::int32_t except)
	{
		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			if (index != except && clients[index].active && clients[index].bot == false)
			{
				transport.queue(clients[index].connection, type, data, size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::sound_at(std::int32_t source, std::uint32_t sound, structures::vec3_s position, std::float_t volume, std::float_t pitch, std::float_t range)
	{
		stream_writer_c writer{};

		writer.reset(scratch, sizeof(scratch));

		writer.u16(static_cast<std::uint16_t>(sound));
		writer.f32(position.x);
		writer.f32(position.y);
		writer.f32(position.z);
		writer.u8(static_cast<std::uint8_t>(std::clamp(volume, 0.0f, 1.0f) * 255.0f));
		writer.u8(static_cast<std::uint8_t>(std::clamp(pitch, 0.25f, 3.9f) * 64.0f));

		for (auto index{ 0 }; index < static_cast<std::int32_t>(clients.size()); index++)
		{
			if (index != source && clients[index].active && clients[index].bot == false && mathematics.distance(clients[index].state.position, position) < range)
			{
				transport.queue(clients[index].connection, structures::message_sound, scratch, writer.size);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::announce(std::int32_t index, std::int32_t target)
	{
		if (clients[target].active && clients[target].bot == false)
		{
			stream_writer_c writer{};

			writer.reset(scratch, sizeof(scratch));

			writer.u16(static_cast<std::uint16_t>(index));
			writer.text(clients[index].name, net_name_length);

			transport.queue(clients[target].connection, structures::message_join, scratch, writer.size);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::chat(std::int32_t index, const char* text)
	{
		stream_writer_c writer{};

		writer.reset(scratch, sizeof(scratch));

		writer.u16(static_cast<std::uint16_t>(index));
		writer.text(text, net_chat_length);

		broadcast(structures::message_chat, scratch, writer.size, -1);

		logger.write("chat: %s: %s", index >= 0 ? clients[index].name : "server", text);
	}
	/*
	//=====================================================================================
	*/
	void server_c::drop(std::int32_t index, bool notify)
	{
		auto& peer{ clients[index] };

		if (peer.active)
		{
			if (notify && peer.bot == false)
			{
				stream_writer_c writer{};

				writer.reset(packet, sizeof(packet));

				writer.u32(net_protocol_id);
				writer.u8(structures::packet_disconnect);

				send_raw(peer.connection.address, packet, writer.size);
			}

			if (peer.state.flags & structures::movement_seated)
			{
				vehicles.alight(peer.state, index);
			}

			if (peer.bot == false)
			{
				persist.remember(index);

				if (peer.alive)
				{
					const auto spot{ present(peer.state) };

					loot.sleep(survivors[index], peer.state.platform && terrain.enabled ? structures::vec3_s{ spot.x, terrain.height(spot.x, spot.z), spot.z } : spot, peer.yaw, peer.name);
				}

				lookup.erase(key(peer.connection.address));
			}

			peer.active = false;
			peer.commands.clear();

			player_count--;

			const auto id{ static_cast<std::uint16_t>(index) };

			broadcast(structures::message_leave, &id, sizeof(id), index);
		}
	}
	/*
	//=====================================================================================
	*/
	void server_c::add_bots(std::uint32_t count)
	{
		auto added{ 0u };

		for (auto index{ 0 }; added < count && player_count < maximum && index < static_cast<std::int32_t>(clients.size()); index++)
		{
			if (clients[index].active == false)
			{
				auto& peer{ clients[index] };

				peer = {};
				peer.active = true;
				peer.bot = true;

				survivors[index] = {};

				survivors[index].reset_knowledge();
				peer.bot_timer = random() * net_bot_think;

				std::snprintf(peer.name, sizeof(peer.name), "Castaway %d", index);

				player_count++;

				spawn(index);

				for (auto other{ 0 }; other < static_cast<std::int32_t>(clients.size()); other++)
				{
					if (other != index && clients[other].active)
					{
						announce(index, other);
					}
				}

				added++;
			}
		}

		logger.write("server: added %u bots (%u/%u)", added, player_count, maximum);
	}
	/*
	//=====================================================================================
	*/
	void server_c::send_raw(const structures::address_s& address, const std::uint8_t* data, std::uint32_t size)
	{
		if (socket.send(address, data, size))
		{
			bytes_sent += size;
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t server_c::find(const structures::address_s& address)
	{
		const auto found{ lookup.find(key(address)) };

		return found != lookup.end() ? found->second : -1;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t server_c::cell_of(structures::vec3_s position)
	{
		const auto origin{ -net_grid_cell * static_cast<std::float_t>(net_grid_size) * 0.5f };
		const auto column{ static_cast<std::int32_t>(std::floor((position.x - origin) / net_grid_cell)) };
		const auto row{ static_cast<std::int32_t>(std::floor((position.z - origin) / net_grid_cell)) };
		const auto size{ static_cast<std::int32_t>(net_grid_size) };

		return column >= 0 && row >= 0 && column < size && row < size ? row * size + column : -1;
	}
	/*
	//=====================================================================================
	*/
	std::uint64_t server_c::key(const structures::address_s& address)
	{
		return (static_cast<std::uint64_t>(address.ip) << 16u) | address.port;
	}
	/*
	//=====================================================================================
	*/
	std::float_t server_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / static_cast<std::float_t>(0x1000000u);
	}
}

//=====================================================================================
