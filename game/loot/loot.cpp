
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	loot_c loot;

	void loot_c::clear()
	{
		for (auto& bag : bags)
		{
			release(bag);
		}

		bags.clear();

		revision++;
	}
	/*
	//=====================================================================================
	*/
	void loot_c::drop(survival_c& victim, structures::vec3_s position, std::float_t yaw, const char* name)
	{
		structures::loot_bag_s bag{};

		bag.position = position;
		bag.yaw = yaw;
		bag.timer = loot_bag_life;
		bag.actor = -1;
		bag.active = true;

		std::snprintf(bag.name, sizeof(bag.name), "%s", name);

		for (auto index{ 0u }; index < total_slots; index++)
		{
			if (victim.slots[index].item && victim.slots[index].amount)
			{
				bag.slots[index] = victim.slots[index];

				bag.items++;
			}

			victim.slots[index] = {};
		}

		store(bag);
	}
	/*
	//=====================================================================================
	*/
	void loot_c::sleep(const survival_c& sleeper, structures::vec3_s position, std::float_t yaw, const char* name)
	{
		structures::loot_bag_s bag{};

		bag.position = position;
		bag.yaw = yaw;
		bag.timer = FLT_MAX;
		bag.actor = -1;
		bag.sleeper = mathematics.hash_text(name);
		bag.health = maximum_health;
		bag.active = true;

		std::snprintf(bag.name, sizeof(bag.name), "%s", name);

		for (auto index{ 0u }; index < total_slots; index++)
		{
			bag.slots[index] = sleeper.slots[index];
			bag.items += sleeper.slots[index].item ? 1u : 0u;
		}

		bag.items = std::max(bag.items, 1u);

		store(bag);
	}
	/*
	//=====================================================================================
	*/
	void loot_c::wake(const char* name)
	{
		const auto identity{ mathematics.hash_text(name) };

		for (auto& bag : bags)
		{
			if (bag.active && bag.sleeper == identity)
			{
				bag.active = false;
				bag.sleeper = 0u;

				revision++;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool loot_c::strike(std::uint32_t index, std::float_t amount)
	{
		auto killed{ false };

		if (index < bags.size() && bags[index].active && bags[index].sleeper)
		{
			auto& bag{ bags[index] };

			bag.health -= amount;

			if (bag.health <= 0.0f)
			{
				if (const auto record{ persist.records.find(bag.sleeper) }; record != persist.records.end())
				{
					record->second.alive = false;
					record->second.vitals.dead = true;

					for (auto& slot : record->second.slots)
					{
						slot = {};
					}
				}

				logger.write("loot: %s was killed in their sleep", bag.name);

				bag.sleeper = 0u;
				bag.timer = loot_bag_life;
				bag.items = 0u;

				for (const auto& slot : bag.slots)
				{
					bag.items += slot.item ? 1u : 0u;
				}

				bag.active = bag.items > 0u;

				killed = true;
			}

			revision++;
		}

		return killed;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t loot_c::ray_sleeper(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance)
	{
		auto best{ -1 };

		distance = range;

		for (auto index{ 0u }; index < bags.size(); index++)
		{
			if (const auto& bag{ bags[index] }; bag.active && bag.sleeper)
			{
				const auto feet{ bag.position + structures::vec3_s{ 0.0f, 0.22f, 0.0f } };
				const auto body{ mathematics.flat_forward(bag.yaw) * -1.55f };
				const auto ray{ direction * range };
				const auto offset{ origin - feet };
				const auto a{ mathematics.dot(ray, ray) };
				const auto b{ mathematics.dot(ray, body) };
				const auto c{ mathematics.dot(ray, offset) };
				const auto e{ mathematics.dot(body, body) };
				const auto f{ mathematics.dot(body, offset) };
				const auto denominator{ a * e - b * b };
				const auto first{ denominator > 0.000001f ? mathematics.saturate((b * f - c * e) / denominator) : 0.0f };
				const auto second{ (b * first + f) / e };
				const auto s{ second < 0.0f ? mathematics.saturate(-c / a) : (second > 1.0f ? mathematics.saturate((b - c) / a) : first) };
				const auto t{ mathematics.saturate(second) };
				const auto gap{ mathematics.distance(origin + ray * s, feet + body * t) };

				if (gap < 0.32f && s * range < distance)
				{
					best = static_cast<std::int32_t>(index);
					distance = s * range;
				}
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	void loot_c::store(const structures::loot_bag_s& bag)
	{
		if (bag.items)
		{
			const auto vacant{ std::find_if(bags.begin(), bags.end(), [](const structures::loot_bag_s& other) { return other.active == false && other.actor < 0; }) };

			if (vacant != bags.end())
			{
				*vacant = bag;
			}

			else if (bags.size() < maximum_bags)
			{
				bags.push_back(bag);
			}

			else
			{
				*std::min_element(bags.begin(), bags.end(), [](const structures::loot_bag_s& a, const structures::loot_bag_s& b) { return a.timer < b.timer; }) = bag;
			}

			revision++;
		}
	}
	/*
	//=====================================================================================
	*/
	void loot_c::update(std::float_t delta)
	{
		for (auto& bag : bags)
		{
			if (bag.active)
			{
				bag.timer -= delta;

				if (bag.timer <= 0.0f)
				{
					bag.active = false;

					revision++;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void loot_c::present(bool input_enabled)
	{
		for (auto& bag : bags)
		{
			if (bag.active && bag.actor < 0)
			{
				if (spare.size())
				{
					bag.actor = spare.back();

					spare.pop_back();

					auto& actor{ actors.list[bag.actor] };

					actor.position = bag.position;
					actor.body_yaw = bag.yaw;
					actor.look_yaw = bag.yaw;
					actor.velocity = {};
					actor.frames = 0u;
					actor.hidden = false;
				}

				else if (const auto actor{ actors.spawn(remote_character, bag.position, bag.yaw, structures::actor_behavior_corpse) }; actor)
				{
					bag.actor = static_cast<std::int32_t>(actors.list.size()) - 1;
				}

				if (bag.actor >= 0)
				{
					auto& body{ actors.list[bag.actor] };

					body.dead = true;
					body.death = 0.0f;
					body.fall_roll = std::sin(bag.position.x * 1.7f + bag.position.z) * 0.25f;
				}
			}

			else if (bag.active == false && bag.actor >= 0)
			{
				release(bag);
			}
		}

		if (input_enabled && survival.vitals.dead == false)
		{
			if (const auto index{ target(player.eye, mathematics.forward_from_angles(player.yaw, player.pitch)) }; index >= 0)
			{
				char text[128]{};

				if (bags[index].sleeper)
				{
					std::snprintf(text, sizeof(text), "%s is sleeping", bags[index].name);
				}

				else
				{
					std::snprintf(text, sizeof(text), "Search %s's body (%u items)   [E]", bags[index].name, bags[index].items);
				}

				hud.set_prompt(text);

				if (platform.tapped(structures::bind_use) && bags[index].sleeper == 0u)
				{
					client.act(structures::act_loot, bags[index].position);

					mixer.play_2d(structures::sound_container, 0.6f, 0.9f);

					platform.consume(structures::bind_use);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void loot_c::take(std::uint32_t index, survival_c& looter)
	{
		if (index < bags.size() && bags[index].active && bags[index].sleeper == 0u)
		{
			auto& bag{ bags[index] };

			bag.items = 0u;

			for (auto& slot : bag.slots)
			{
				if (slot.item && slot.amount)
				{
					slot.amount = looter.receive(slot);

					slot = slot.amount ? slot : structures::item_stack_s{};
				}

				bag.items += slot.item ? 1u : 0u;
			}

			bag.active = bag.items > 0u;

			revision++;
		}
	}
	/*
	//=====================================================================================
	*/
	void loot_c::release(structures::loot_bag_s& bag)
	{
		if (bag.actor >= 0 && bag.actor < static_cast<std::int32_t>(actors.list.size()))
		{
			actors.list[bag.actor].hidden = true;

			spare.push_back(bag.actor);
		}

		bag.actor = -1;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t loot_c::target(structures::vec3_s eye, structures::vec3_s forward)
	{
		auto best{ -1 };
		auto best_away{ 0.9f };

		for (auto index{ 0u }; index < bags.size(); index++)
		{
			if (const auto& bag{ bags[index] }; bag.active)
			{
				const auto middle{ bag.position + structures::vec3_s{ 0.0f, 0.2f, 0.0f } };
				const auto along{ mathematics.dot(middle - eye, forward) };
				const auto away{ mathematics.length(middle - eye - forward * along) };

				if (along > 0.2f && along < interact_range + 0.6f && away < best_away)
				{
					best = static_cast<std::int32_t>(index);
					best_away = away;
				}
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t loot_c::nearest(structures::vec3_s position)
	{
		auto best{ -1 };
		auto best_distance{ 1.2f };

		for (auto index{ 0u }; index < bags.size(); index++)
		{
			if (const auto distance{ mathematics.distance(bags[index].position, position) }; bags[index].active && distance < best_distance)
			{
				best = static_cast<std::int32_t>(index);
				best_distance = distance;
			}
		}

		return best;
	}
}

//=====================================================================================
