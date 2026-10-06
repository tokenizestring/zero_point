
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	persist_c persist;

	std::string persist_c::path()
	{
		return functions::executable_directory() + world_save_name;
	}
	/*
	//=====================================================================================
	*/
	void persist_c::put(const void* data, std::size_t size)
	{
		const auto bytes{ static_cast<const std::uint8_t*>(data) };

		buffer.insert(buffer.end(), bytes, bytes + size);
	}
	/*
	//=====================================================================================
	*/
	void persist_c::get(void* data, std::size_t size)
	{
		if (cursor + size <= buffer.size())
		{
			std::memcpy(data, buffer.data() + cursor, size);

			cursor += size;
		}

		else
		{
			healthy = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void persist_c::tick(std::float_t delta)
	{
		timer += delta;

		if (timer >= world_save_interval)
		{
			timer = 0.0f;

			write();
		}
	}
	/*
	//=====================================================================================
	*/
	void persist_c::remember(std::int32_t index)
	{
		const auto& peer{ server.clients[index] };
		const auto& survivor{ server.survivors[index] };

		structures::player_record_s record{};

		std::snprintf(record.name, sizeof(record.name), "%s", peer.name);

		record.position = peer.state.position;
		record.yaw = peer.yaw;
		record.vitals = survivor.vitals;
		record.queue_count = survivor.queue_count;
		record.alive = peer.alive;

		std::memcpy(record.slots, survivor.slots, sizeof(record.slots));
		std::memcpy(record.queue, survivor.queue, sizeof(record.queue));
		std::memcpy(record.known, survivor.known, sizeof(record.known));

		records[mathematics.hash_text(peer.name)] = record;
	}
	/*
	//=====================================================================================
	*/
	bool persist_c::recall(std::int32_t index)
	{
		auto& peer{ server.clients[index] };
		auto& survivor{ server.survivors[index] };

		auto restored{ false };

		if (const auto found{ records.find(mathematics.hash_text(peer.name)) }; found != records.end())
		{
			const auto& record{ found->second };

			std::memcpy(survivor.known, record.known, sizeof(survivor.known));

			for (auto recipe{ 0u }; recipe < recipe_count; recipe++)
			{
				survivor.known[recipe] = survivor.known[recipe] || recipes[recipe].starter;
			}

			if (record.alive && record.vitals.dead == false)
			{
				survivor.vitals = record.vitals;
				survivor.queue_count = std::min(record.queue_count, crafting_queue_size);

				std::memcpy(survivor.slots, record.slots, sizeof(survivor.slots));
				std::memcpy(survivor.queue, record.queue, sizeof(survivor.queue));

				movement.reset(peer.state, record.position, record.yaw);

				peer.yaw = record.yaw;

				restored = true;
			}

			logger.write("persist: welcome back %s (%s)", peer.name, restored ? "restored where they slept" : "starting over");
		}

		return restored;
	}
	/*
	//=====================================================================================
	*/
	bool persist_c::write()
	{
		for (auto index{ 0 }; index < static_cast<std::int32_t>(server.clients.size()); index++)
		{
			if (server.clients[index].active && server.clients[index].bot == false)
			{
				remember(index);
			}
		}

		buffer.clear();

		put_value(world_save_magic);
		put_value(world_save_version);
		put_value(server.hours);
		put_value(static_cast<std::uint32_t>(building.placed.size()));

		for (const auto& structure : building.placed)
		{
			put_value(structure);
		}

		put_value(static_cast<std::uint32_t>(building.containers.size()));

		for (const auto& container : building.containers)
		{
			put_value(container);
		}

		put_value(static_cast<std::uint32_t>(farming.crops.size()));

		for (const auto& crop : farming.crops)
		{
			put_value(crop);
		}

		put_value(static_cast<std::uint32_t>(harvest.nodes.size()));
		put_value(static_cast<std::uint32_t>(std::count_if(harvest.nodes.begin(), harvest.nodes.end(), [](const structures::resource_node_s& node) { return node.depleted; })));

		for (auto index{ 0u }; index < harvest.nodes.size(); index++)
		{
			if (harvest.nodes[index].depleted)
			{
				put_value(index);
				put_value(harvest.nodes[index].timer);
			}
		}

		put_value(static_cast<std::uint32_t>(records.size()));

		for (const auto& entry : records)
		{
			put_value(entry.second);
		}

		put_value(static_cast<std::uint32_t>(loot.bags.size()));

		for (const auto& bag : loot.bags)
		{
			put_value(bag);
		}

		put_value(static_cast<std::uint32_t>(building.authorized.size()));

		for (const auto& entry : building.authorized)
		{
			put_value(entry.first);
			put_value(static_cast<std::uint32_t>(entry.second.size()));

			for (const auto identity : entry.second)
			{
				put_value(identity);
			}
		}

		put_value(static_cast<std::uint32_t>(identities.size()));

		for (const auto& claim : identities)
		{
			put_value(claim.first);
			put_value(claim.second);
		}

		put_value(static_cast<std::uint32_t>(building.locks.size()));

		for (const auto& entry : building.locks)
		{
			put_value(entry.first);
			put_value(entry.second.owner);
			put_value(entry.second.code);
			put_value(entry.second.coded);
			put_value(static_cast<std::uint32_t>(entry.second.authorized.size()));

			for (const auto identity : entry.second.authorized)
			{
				put_value(identity);
			}
		}

		const auto lasting{ std::min(static_cast<std::uint32_t>(std::count_if(marks.ring.begin(), marks.ring.end(), [](const structures::mark_s& mark) { return mark.live && mark_definitions[mark.kind].life <= 0.0f; })), mark_save_limit) };

		put_value(lasting);

		for (auto step{ 0u }, kept{ 0u }; step < marks.ring.size() && kept < lasting; step++)
		{
			if (const auto& mark{ marks.ring[(marks.cursor + marks.ring.size() - 1u - step) % marks.ring.size()] }; mark.live && mark_definitions[mark.kind].life <= 0.0f)
			{
				put_value(mark.position);
				put_value(marks.pack(mark.normal));
				put_value(mark.kind);
				put_value(mark.variant);
				put_value(mark.spin);
				put_value(mark.scale);

				kept++;
			}
		}

		const auto written{ functions::write_file(path().c_str(), buffer.data(), buffer.size()) };

		logger.write("persist: world %s (%zu KB, %zu structures, %zu crops, %zu survivors)", written ? "saved" : "save failed", buffer.size() / 1024u, building.placed.size(), farming.crops.size(), records.size());

		return written;
	}
	/*
	//=====================================================================================
	*/
	structures::player_record_s persist_c::upgrade(const structures::legacy_record_s& legacy)
	{
		structures::player_record_s record{};

		std::memcpy(record.name, legacy.name, sizeof(record.name));
		std::memcpy(record.slots, legacy.slots, sizeof(record.slots));
		std::memcpy(record.queue, legacy.queue, sizeof(record.queue));
		std::memcpy(record.known, legacy.known, sizeof(legacy.known));

		record.position = legacy.position;
		record.yaw = legacy.yaw;
		record.vitals = legacy.vitals;
		record.queue_count = legacy.queue_count;
		record.alive = legacy.alive;

		return record;
	}
	/*
	//=====================================================================================
	*/
	bool persist_c::claim(std::uint32_t name_hash, std::uint64_t identity)
	{
		const auto found{ identities.find(name_hash) };
		const auto granted{ identity != 0u && (found == identities.end() || found->second == identity) };

		if (granted)
		{
			identities[name_hash] = identity;
		}

		return granted;
	}
	/*
	//=====================================================================================
	*/
	bool persist_c::read()
	{
		cursor = 0u;
		healthy = functions::read_file(path().c_str(), buffer) && buffer.size() > 12u;

		const auto magic{ healthy ? get_value<std::uint32_t>() : 0u };
		const auto version{ healthy ? get_value<std::uint32_t>() : 0u };

		if (healthy && magic == world_save_magic && version >= world_save_oldest && version <= world_save_version)
		{
			server.hours = std::fmod(std::max(get_value<std::float_t>(), 0.0f), 24.0f);

			const auto structure_count{ get_value<std::uint32_t>() };

			if (version < world_save_version)
			{
				logger.write("persist: upgrading a version %u world save", version);
			}

			for (auto entry{ 0u }; entry < structure_count && healthy && entry < maximum_structures; entry++)
			{
				auto structure{ get_value<structures::structure_s>() };

				if (version < world_save_tiers)
				{
					building.migrate(structure);
				}

				structure.piece = std::min<std::uint32_t>(structure.piece, structures::piece_count - 1u);

				building.attach(structure);
			}

			const auto container_count{ get_value<std::uint32_t>() };

			for (auto entry{ 0u }; entry < container_count && healthy; entry++)
			{
				const auto container{ get_value<structures::container_s>() };

				if (entry < building.containers.size())
				{
					std::memcpy(building.containers[entry].slots, container.slots, sizeof(container.slots));

					building.containers[entry].smelt_timer = container.smelt_timer;
					building.containers[entry].fuel_timer = container.fuel_timer;
					building.containers[entry].burning = container.burning;
				}
			}

			const auto crop_count{ get_value<std::uint32_t>() };

			for (auto entry{ 0u }; entry < crop_count && healthy && entry < maximum_crops; entry++)
			{
				farming.crops.push_back(get_value<structures::crop_s>());
			}

			const auto layout{ version >= world_save_layout ? get_value<std::uint32_t>() : 0u };
			const auto depleted{ get_value<std::uint32_t>() };

			if (layout != harvest.nodes.size())
			{
				logger.write("persist: the island layout changed (%u nodes saved, %zu now), cut nodes regrow", layout, harvest.nodes.size());
			}

			for (auto entry{ 0u }; entry < depleted && healthy; entry++)
			{
				const auto index{ get_value<std::uint32_t>() };
				const auto remaining{ get_value<std::float_t>() };

				if (index < harvest.nodes.size() && layout == harvest.nodes.size())
				{
					harvest.deplete(index);

					harvest.nodes[index].timer = remaining;
				}
			}

			const auto record_count{ get_value<std::uint32_t>() };

			for (auto entry{ 0u }; entry < record_count && healthy; entry++)
			{
				auto record{ version < world_save_locks ? upgrade(get_value<structures::legacy_record_s>()) : get_value<structures::player_record_s>() };

				record.name[sizeof(record.name) - 1u] = 0;

				records[mathematics.hash_text(record.name)] = record;
			}

			const auto bag_count{ get_value<std::uint32_t>() };

			for (auto entry{ 0u }; entry < bag_count && healthy && entry < maximum_bags; entry++)
			{
				auto bag{ get_value<structures::loot_bag_s>() };

				bag.actor = -1;
				bag.name[sizeof(bag.name) - 1u] = 0;

				loot.bags.push_back(bag);
			}

			loot.revision++;

			const auto cupboards{ get_value<std::uint32_t>() };

			for (auto entry{ 0u }; entry < cupboards && healthy; entry++)
			{
				const auto index{ get_value<std::uint32_t>() };
				const auto count{ get_value<std::uint32_t>() };

				for (auto member{ 0u }; member < count && healthy && member < 256u; member++)
				{
					building.authorize(index, get_value<std::uint32_t>());
				}
			}

			const auto claims{ version >= world_save_claims ? get_value<std::uint32_t>() : 0u };

			for (auto entry{ 0u }; entry < claims && healthy; entry++)
			{
				const auto name_hash{ get_value<std::uint32_t>() };

				identities[name_hash] = get_value<std::uint64_t>();
			}

			const auto locked{ version >= world_save_locks ? get_value<std::uint32_t>() : 0u };

			for (auto entry{ 0u }; entry < locked && healthy; entry++)
			{
				const auto door{ get_value<std::uint32_t>() };

				structures::lock_s lock{};

				lock.owner = get_value<std::uint32_t>();
				lock.code = get_value<std::uint32_t>();
				lock.coded = get_value<bool>();

				const auto members{ get_value<std::uint32_t>() };

				for (auto member{ 0u }; member < members && healthy && member < 256u; member++)
				{
					lock.authorized.push_back(get_value<std::uint32_t>());
				}

				if (door < building.placed.size() && building.placed[door].piece == structures::piece_door && building.placed[door].destroyed == false)
				{
					building.locks[door] = lock;
				}
			}

			const auto lasting{ version >= world_save_marks ? std::min(get_value<std::uint32_t>(), mark_save_limit) : 0u };

			std::vector<structures::mark_s> saved(lasting);

			for (auto entry{ 0u }; entry < lasting && healthy; entry++)
			{
				saved[entry].position = get_value<structures::vec3_s>();
				saved[entry].normal = marks.unpack(get_value<std::uint16_t>());
				saved[entry].kind = get_value<std::uint8_t>();
				saved[entry].variant = get_value<std::uint8_t>();
				saved[entry].spin = get_value<std::uint8_t>();
				saved[entry].scale = get_value<std::uint8_t>();
			}

			for (auto entry{ lasting }; entry > 0u && healthy; entry--)
			{
				marks.add(saved[entry - 1u].kind, saved[entry - 1u].variant, saved[entry - 1u].position, saved[entry - 1u].normal, saved[entry - 1u].spin, saved[entry - 1u].scale, 0.0, false);
			}

			building.dirty.clear();
			building.stirred.clear();
			harvest.changed.clear();

			logger.write("persist: world loaded (%zu structures, %zu crops, %u cut nodes, %zu survivors, %.1f h)", building.placed.size(), farming.crops.size(), depleted, records.size(), server.hours);
		}

		else
		{
			logger.write("persist: no saved world, starting fresh");

			healthy = false;
		}

		return healthy;
	}
}

//=====================================================================================
