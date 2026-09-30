
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	survival_c survival;

	void survival_c::reset()
	{
		vitals = { maximum_health, starting_calories, starting_hydration, 0.0f, 1.0f, false };
		climate.wetness = 0.0f;
		climate.temperature = climate.air;
		climate.timer = 0.0f;

		for (auto& slot : slots)
		{
			slot = {};
		}

		for (auto& notification : notifications)
		{
			notification = {};
		}

		queue_count = 0u;
		active_slot = 0u;
		inventory_open = false;
	}
	/*
	//=====================================================================================
	*/
	void survival_c::reset_knowledge()
	{
		for (auto recipe{ 0u }; recipe < recipe_count; recipe++)
		{
			known[recipe] = recipes[recipe].starter;
		}
	}
	/*
	//=====================================================================================
	*/
	void survival_c::give_kit()
	{
		for (const auto& entry : test_kit)
		{
			give(entry.stack.item, entry.stack.amount, true);
		}

		for (auto& stack : slots)
		{
			if (const auto gun{ item_definitions[stack.item].weapon }; gun != structures::weapon_none && stack.loaded == 0u)
			{
				stack.loaded = weapon_definitions[gun].capacity;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::learn(std::uint32_t recipe)
	{
		if (recipe < recipe_count && known[recipe] == false)
		{
			char text[96]{};

			known[recipe] = true;

			std::snprintf(text, sizeof(text), "Learned: %s", item_definitions[recipes[recipe].result].name);

			notify(text, 0);

			cue(structures::sound_craft, 0.7f, 1.3f);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::learn_random(std::uint32_t highest_tier)
	{
		std::uint32_t choices[recipe_count]{};

		auto count_open{ 0u };

		for (auto recipe{ 0u }; recipe < recipe_count; recipe++)
		{
			if (known[recipe] == false && recipes[recipe].tier <= highest_tier)
			{
				choices[count_open++] = recipe;
			}
		}

		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return count_open && learn(choices[seed % count_open]);
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::research(std::uint32_t recipe)
	{
		auto result{ false };

		if (recipe < recipe_count && known[recipe] == false && building.research_nearby(position) && count(structures::item_scrap) >= research_costs[recipes[recipe].tier])
		{
			if (remote)
			{
				client.request(structures::request_research, static_cast<std::uint16_t>(recipe), 0u);

				result = true;
			}

			else
			{
				take(structures::item_scrap, research_costs[recipes[recipe].tier]);

				story.researched += owner < 0 ? 1u : 0u;

				result = learn(recipe);
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t survival_c::station()
	{
		return building.workbench_tier(position);
	}
	/*
	//=====================================================================================
	*/
	void survival_c::update(std::float_t delta, std::float_t exertion)
	{
		if (queue_count && remote)
		{
			queue[0].remaining = std::max(queue[0].remaining - delta, 0.0f);
		}

		else if (queue_count)
		{
			queue[0].remaining -= delta;

			if (queue[0].remaining <= 0.0f)
			{
				const auto& recipe{ recipes[queue[0].recipe] };

				give(recipe.result, recipe.amount, true);

				cue(structures::sound_craft, 0.6f, 1.0f);

				for (auto index{ 1u }; index < queue_count; index++)
				{
					queue[index - 1u] = queue[index];
				}

				queue_count--;
			}
		}

		for (auto& notification : notifications)
		{
			notification.age += delta;
		}

		vitals.damage_flash = std::max(0.0f, vitals.damage_flash - delta * 1.5f);

		if (vitals.dead == false && remote == false)
		{
			acclimate(delta);

			const auto chill{ std::max(0.0f, climate_cold - climate.temperature) };

			vitals.calories = std::max(0.0f, vitals.calories - calorie_burn * exertion * (1.0f + chill * climate_cold_hunger) * delta);
			vitals.hydration = std::max(0.0f, vitals.hydration - hydration_burn * exertion * (climate.temperature > climate_hot ? 2.0f : 1.0f) * delta);
			vitals.breath = underwater ? std::max(0.0f, vitals.breath - delta / breath_seconds) : std::min(1.0f, vitals.breath + delta * breath_recover);

			if (vitals.breath <= 0.0f)
			{
				harm = structures::death_drowned;

				damage(drown_damage * delta);
			}

			if (climate.temperature < climate_freezing)
			{
				harm = structures::death_frozen;

				damage((climate_freezing - climate.temperature) * climate_freeze_damage * delta);
			}

			if (vitals.calories <= 0.0f || vitals.hydration <= 0.0f)
			{
				harm = structures::death_starved;

				damage(starvation_damage * delta);
			}

			else if (vitals.calories > 150.0f && vitals.hydration > 100.0f && chill <= 0.0f)
			{
				vitals.health = std::min(maximum_health, vitals.health + natural_regeneration * delta);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void survival_c::acclimate(std::float_t delta)
	{
		const auto immersed{ climate.swimming || underwater };

		climate.timer -= delta;

		if (climate.timer <= 0.0f)
		{
			const auto head{ position + structures::vec3_s{ 0.0f, player_eye_height, 0.0f } };

			climate.timer = climate_interval;
			climate.sheltered = world.trace(head, head + structures::vec3_s{ 0.0f, climate_roof_reach, 0.0f }, {}, structures::contents_solid).fraction < 1.0f;
			climate.heat = building.warmth(position) + (held().item == structures::item_torch ? climate_torch : 0.0f);
		}

		const auto soaking{ climate.sheltered ? 0.0f : climate.rain };
		const auto target{ (immersed ? climate_sea : climate.air) + climate.heat - climate.wetness * climate_wet_chill };

		climate.wetness = immersed ? 1.0f : (soaking > 0.01f ? std::min(1.0f, climate.wetness + climate_soak * soaking * delta) : std::max(0.0f, climate.wetness - (climate_dry + climate.heat * climate_fire_dry) * delta));
		climate.temperature = mathematics.approach(climate.temperature, target, climate_adapt * delta);
	}
	/*
	//=====================================================================================
	*/
	std::float_t survival_c::ambient(std::float_t hours, std::float_t cloud, std::float_t rain, std::float_t storm)
	{
		return climate_mean + climate_swing * std::cos((hours - climate_peak_hour) / 24.0f * two_pi) - cloud * climate_cloud_chill - rain * climate_rain_chill - storm * climate_storm_chill;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t survival_c::give(std::uint32_t item, std::uint32_t amount, bool announce)
	{
		if (item == structures::item_blueprint)
		{
			for (auto index{ 0u }; index < amount; index++)
			{
				if (learn_random(3u) == false)
				{
					give(structures::item_scrap, blueprint_scrap, announce);
				}
			}

			return 0u;
		}

		const auto& definition{ item_definitions[item] };
		const auto hotbar_first{ definition.category != structures::item_category_resource && definition.category != structures::item_category_ammunition };

		auto remaining{ amount };

		remaining = place(item, remaining, hotbar_first ? inventory_slots : 0u, hotbar_first ? total_slots : inventory_slots);
		remaining = place(item, remaining, hotbar_first ? 0u : inventory_slots, hotbar_first ? inventory_slots : total_slots);

		if (announce && amount > remaining)
		{
			notify(definition.name, static_cast<std::int32_t>(amount - remaining));
		}

		return remaining;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t survival_c::receive(const structures::item_stack_s& stack)
	{
		const auto& definition{ item_definitions[stack.item] };

		auto remaining{ stack.amount };

		if (std::max(1u, definition.stack) > 1u)
		{
			remaining = give(stack.item, stack.amount, true);
		}

		else
		{
			const auto hotbar_first{ definition.category != structures::item_category_resource && definition.category != structures::item_category_ammunition };

			for (auto pass{ 0u }; pass < 2u && remaining; pass++)
			{
				const auto first{ (pass == 0u) == hotbar_first ? inventory_slots : 0u };
				const auto last{ (pass == 0u) == hotbar_first ? total_slots : inventory_slots };

				for (auto index{ first }; index < last && remaining; index++)
				{
					if (slots[index].item == structures::item_none)
					{
						slots[index] = stack;

						remaining = 0u;

						notify(definition.name, 1);
					}
				}
			}
		}

		return remaining;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t survival_c::place(std::uint32_t item, std::uint32_t amount, std::uint32_t first, std::uint32_t last)
	{
		const auto stack{ std::max(1u, item_definitions[item].stack) };

		auto remaining{ amount };

		for (auto index{ first }; index < last && remaining; index++)
		{
			if (slots[index].item == item && slots[index].amount < stack)
			{
				const auto moved{ std::min(stack - slots[index].amount, remaining) };

				slots[index].amount += moved;

				remaining -= moved;
			}
		}

		for (auto index{ first }; index < last && remaining; index++)
		{
			if (slots[index].item == structures::item_none)
			{
				const auto moved{ std::min(stack, remaining) };

				slots[index] = { item, moved, 1.0f };

				remaining -= moved;
			}
		}

		return remaining;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t survival_c::count(std::uint32_t item)
	{
		auto total{ 0u };

		for (const auto& slot : slots)
		{
			total += slot.item == item ? slot.amount : 0u;
		}

		return total;
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::take(std::uint32_t item, std::uint32_t amount)
	{
		if (count(item) >= amount)
		{
			auto remaining{ amount };

			for (auto index{ 0u }; index < total_slots && remaining; index++)
			{
				if (slots[index].item == item)
				{
					const auto removed{ std::min(slots[index].amount, remaining) };

					slots[index].amount -= removed;

					remaining -= removed;

					if (slots[index].amount == 0u)
					{
						slots[index] = {};
					}
				}
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::can_craft(std::uint32_t recipe)
	{
		auto result{ recipe < recipe_count && queue_count < crafting_queue_size && known[std::min<std::size_t>(recipe, recipe_count - 1u)] && recipes[std::min<std::size_t>(recipe, recipe_count - 1u)].tier <= station() };

		for (const auto& ingredient : recipes[std::min<std::size_t>(recipe, recipe_count - 1u)].ingredients)
		{
			result = result && (ingredient.item == structures::item_none || count(ingredient.item) >= ingredient.amount);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::craft(std::uint32_t recipe)
	{
		if (remote && can_craft(recipe))
		{
			client.request(structures::request_craft, static_cast<std::uint16_t>(recipe), 0u);
		}

		if (can_craft(recipe))
		{
			for (const auto& ingredient : recipes[recipe].ingredients)
			{
				if (ingredient.item != structures::item_none)
				{
					take(ingredient.item, ingredient.amount);
				}
			}

			queue[queue_count++] = { recipe, recipes[recipe].time };

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::consume(std::uint32_t slot)
	{
		const auto& definition{ item_definitions[slots[slot].item] };

		if (slots[slot].item && (definition.category == structures::item_category_food || definition.category == structures::item_category_medical) && remote)
		{
			client.request(structures::request_consume, static_cast<std::uint16_t>(slot), 0u);
		}

		if (slots[slot].item && (definition.category == structures::item_category_food || definition.category == structures::item_category_medical))
		{
			vitals.calories = std::min(maximum_calories, vitals.calories + definition.calories);
			vitals.hydration = std::min(maximum_hydration, vitals.hydration + definition.hydration);
			vitals.health = std::min(maximum_health, vitals.health + definition.healing);

			slots[slot].amount--;

			if (slots[slot].amount == 0u)
			{
				slots[slot] = {};
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void survival_c::damage(std::float_t amount)
	{
		if (vitals.dead == false && remote == false)
		{
			vitals.health = std::max(0.0f, vitals.health - amount);
			vitals.damage_flash = std::min(1.0f, vitals.damage_flash + amount / 25.0f);
			vitals.dead = vitals.health <= 0.0f;
		}
	}
	/*
	//=====================================================================================
	*/
	void survival_c::notify(const char* text, std::int32_t amount)
	{
		if (owner >= 0)
		{
			server.notify(owner, text, amount);
		}

		else if (remote == false)
		{
			post(text, amount);
		}
	}
	/*
	//=====================================================================================
	*/
	void survival_c::post(const char* text, std::int32_t amount)
	{
		for (auto index{ notification_count - 1u }; index > 0u; index--)
		{
			notifications[index] = notifications[index - 1u];
		}

		std::snprintf(notifications[0].text, sizeof(notifications[0].text), "%s", text);

		notifications[0].age = 0.0f;
		notifications[0].amount = amount;
	}
	/*
	//=====================================================================================
	*/
	void survival_c::cue(std::uint32_t sound, std::float_t volume, std::float_t pitch)
	{
		if (owner >= 0)
		{
			server.cue(owner, sound, volume, pitch);
		}

		else if (remote == false)
		{
			mixer.play_2d(sound, volume, pitch);
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint64_t survival_c::fingerprint()
	{
		auto hash{ 1469598103934665603ull };

		const auto mix{ [&](const void* data, std::size_t size)
		{
			const auto* bytes{ static_cast<const std::uint8_t*>(data) };

			for (auto index{ 0u }; index < size; index++)
			{
				hash = (hash ^ bytes[index]) * 1099511628211ull;
			}
		} };

		mix(slots, sizeof(slots));
		mix(&queue_count, sizeof(queue_count));
		mix(known, sizeof(known));

		for (auto index{ 0u }; index < queue_count; index++)
		{
			mix(&queue[index].recipe, sizeof(queue[index].recipe));
		}

		return hash;
	}
	/*
	//=====================================================================================
	*/
	void survival_c::swap(std::uint32_t from, std::uint32_t to)
	{
		if (remote && valid(from) && valid(to) && from != to)
		{
			client.request(structures::request_swap, static_cast<std::uint16_t>(from), static_cast<std::uint16_t>(to));
		}

		if (valid(from) && valid(to) && from != to)
		{
			auto& source{ slot(from) };
			auto& target{ slot(to) };

			if (source.item == target.item && target.item != structures::item_none)
			{
				const auto moved{ std::min(item_definitions[target.item].stack - target.amount, source.amount) };

				target.amount += moved;
				source.amount -= moved;

				if (source.amount == 0u)
				{
					source = {};
				}
			}

			else
			{
				std::swap(source, target);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void survival_c::transfer(std::uint32_t from)
	{
		if (remote && valid(from) && open_container >= 0 && slot(from).item)
		{
			client.request(structures::request_transfer, static_cast<std::uint16_t>(from), static_cast<std::uint16_t>(open_container));
		}

		if (valid(from) && open_container >= 0 && slot(from).item)
		{
			const auto into_container{ from < total_slots };
			const auto first{ into_container ? container_address : 0u };
			const auto last{ into_container ? container_address + container_slots : total_slots };

			for (auto pass{ 0u }; pass < 2u && slot(from).item; pass++)
			{
				for (auto target{ first }; target < last && slot(from).item; target++)
				{
					if ((pass == 0u && slot(target).item == slot(from).item) || (pass == 1u && slot(target).item == structures::item_none))
					{
						swap(from, target);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::item_stack_s& survival_c::slot(std::uint32_t address)
	{
		if (address < total_slots)
		{
			return slots[address];
		}

		if (open_container >= 0 && address >= container_address && address < container_address + container_slots)
		{
			return building.containers[open_container].slots[address - container_address];
		}

		scratch = {};

		return scratch;
	}
	/*
	//=====================================================================================
	*/
	bool survival_c::valid(std::uint32_t address)
	{
		return address < total_slots || (open_container >= 0 && address >= container_address && address < container_address + container_slots);
	}
	/*
	//=====================================================================================
	*/
	const structures::item_stack_s& survival_c::held()
	{
		return slots[inventory_slots + active_slot];
	}
}

//=====================================================================================
