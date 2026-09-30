
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	save_c save;

	std::string save_c::path()
	{
		return functions::executable_directory() + save_file_name;
	}
	/*
	//=====================================================================================
	*/
	bool save_c::exists()
	{
		return GetFileAttributesA(path().c_str()) != INVALID_FILE_ATTRIBUTES;
	}
	/*
	//=====================================================================================
	*/
	void save_c::put(const void* data, std::size_t size)
	{
		const auto bytes{ static_cast<const std::uint8_t*>(data) };

		buffer.insert(buffer.end(), bytes, bytes + size);
	}
	/*
	//=====================================================================================
	*/
	void save_c::get(void* data, std::size_t size)
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
	bool save_c::write()
	{
		auto depleted{ 0u };

		buffer.clear();

		put_value(save_magic);
		put_value(save_version);
		put_value(atmosphere.hours);
		put_value(player.state.position);
		put_value(player.yaw);
		put_value(player.pitch);
		put_value(survival.vitals);
		put_value(survival.active_slot);
		put(survival.slots, sizeof(survival.slots));
		put(survival.known, sizeof(survival.known));
		put_value(survival.queue_count);
		put(survival.queue, sizeof(survival.queue));
		put_value(story.step);
		put_value(story.day);
		put_value(story.repaired_day);
		put_value(story.researched);
		put(story.searches, sizeof(story.searches));
		put(story.parts, sizeof(story.parts));
		put_value(story.rescued);
		put_value(building.bag);
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

		for (const auto& node : harvest.nodes)
		{
			depleted += node.depleted ? 1u : 0u;
		}

		put_value(depleted);

		for (auto index{ 0u }; index < harvest.nodes.size(); index++)
		{
			if (harvest.nodes[index].depleted)
			{
				put_value(index);
				put_value(harvest.nodes[index].timer);
			}
		}

		const auto written{ functions::write_file(path().c_str(), buffer.data(), buffer.size()) };

		logger.write("save: %s, %zu bytes, %zu structures, day %u", written ? "written" : "failed", buffer.size(), building.placed.size(), story.day);

		return written;
	}
	/*
	//=====================================================================================
	*/
	bool save_c::read()
	{
		cursor = 0u;
		healthy = functions::read_file(path().c_str(), buffer) && buffer.size() > 8u;

		const auto magic{ healthy ? get_value<std::uint32_t>() : 0u };
		const auto version{ healthy ? get_value<std::uint32_t>() : 0u };

		if (healthy && magic == save_magic && version >= save_oldest && version <= save_version)
		{
			atmosphere.hours = get_value<std::float_t>();

			const auto position{ get_value<structures::vec3_s>() };
			const auto yaw{ get_value<std::float_t>() };
			const auto pitch{ get_value<std::float_t>() };

			player.spawn(position, yaw);

			player.pitch = pitch;

			survival.reset();

			survival.vitals = get_value<structures::vitals_s>();
			survival.active_slot = get_value<std::uint32_t>();

			get(survival.slots, sizeof(survival.slots));
			get(survival.known, version < save_recipes ? legacy_recipe_count : sizeof(survival.known));

			for (auto recipe{ 0u }; recipe < recipe_count; recipe++)
			{
				survival.known[recipe] = survival.known[recipe] || recipes[recipe].starter;
			}

			survival.queue_count = std::min(get_value<std::uint32_t>(), crafting_queue_size);

			get(survival.queue, sizeof(survival.queue));

			story.step = std::min(get_value<std::uint32_t>(), static_cast<std::uint32_t>(goal_count - 1u));
			story.day = get_value<std::uint32_t>();
			story.repaired_day = get_value<std::uint32_t>();
			story.researched = get_value<std::uint32_t>();

			get(story.searches, sizeof(story.searches));
			get(story.parts, sizeof(story.parts));

			story.rescued = get_value<bool>();
			story.previous_hours = atmosphere.hours;

			building.clear();

			building.bag = get_value<std::int32_t>();

			const auto first{ static_cast<std::uint32_t>(building.placed.size()) };
			const auto structure_count{ get_value<std::uint32_t>() };

			for (auto index{ 0u }; index < structure_count && healthy; index++)
			{
				auto structure{ get_value<structures::structure_s>() };

				if (version < save_tiers)
				{
					building.migrate(structure);
				}

				structure.first_brush = -1;
				structure.brush_count = 0u;

				building.placed.push_back(structure);
			}

			const auto container_count{ get_value<std::uint32_t>() };

			for (auto index{ 0u }; index < container_count && healthy; index++)
			{
				building.containers.push_back(get_value<structures::container_s>());
			}

			farming.crops.clear();

			const auto crop_count{ get_value<std::uint32_t>() };

			for (auto index{ 0u }; index < crop_count && healthy; index++)
			{
				farming.crops.push_back(get_value<structures::crop_s>());
			}

			const auto depleted{ get_value<std::uint32_t>() };

			for (auto entry{ 0u }; entry < depleted && healthy; entry++)
			{
				const auto index{ get_value<std::uint32_t>() };
				const auto timer_value{ get_value<std::float_t>() };

				if (index < harvest.nodes.size())
				{
					harvest.deplete(index);

					harvest.nodes[index].timer = timer_value;
				}
			}

			apply_structures(first);
		}

		else
		{
			healthy = false;
		}

		logger.write("save: %s, %zu structures, day %u", healthy ? "loaded" : "unreadable", building.placed.size(), story.day);

		return healthy;
	}
	/*
	//=====================================================================================
	*/
	void save_c::apply_structures(std::uint32_t first)
	{
		for (auto index{ first }; index < building.placed.size(); index++)
		{
			if (building.placed[index].destroyed == false)
			{
				building.add_collision(index);

				if (building.placed[index].piece == structures::piece_door && building.placed[index].open && building.placed[index].first_brush >= 0)
				{
					world.brushes[building.placed[index].first_brush].contents = 0u;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void save_c::tick(std::float_t delta)
	{
		timer += delta;

		if (timer > save_interval && survival.vitals.dead == false)
		{
			timer = 0.0f;

			write();
		}
	}
}

//=====================================================================================
