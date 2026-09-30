
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	story_c story;

	void story_c::reset()
	{
		step = 0u;
		day = 1u;
		repaired_day = 0u;
		researched = 0u;
		previous_hours = atmosphere.hours;
		done_flash = 0.0f;
		rescued = false;
		ending = false;

		for (auto site{ 0u }; site < structures::landmark_count; site++)
		{
			searches[site] = 0u;
			parts[site] = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void story_c::update(std::float_t delta)
	{
		char text[96]{};

		done_flash = std::max(0.0f, done_flash - delta);

		if (atmosphere.enabled && previous_hours < dawn_hour && atmosphere.hours >= dawn_hour)
		{
			day++;

			std::snprintf(text, sizeof(text), "Day %u", day);

			survival.notify(text, 0);
		}

		previous_hours = atmosphere.hours;

		if (step < goal_count && survival.vitals.dead == false && ending == false)
		{
			const auto& goal{ goals[step] };

			if (goal.kind == structures::goal_repair && near_radio())
			{
				hud.set_prompt(parts_found() == 3u ? "Repair the radio   [E]" : "The radio is missing parts");

				if (platform.tapped(structures::bind_use) && parts_found() == 3u)
				{
					for (const auto part : radio_parts)
					{
						survival.take(part, 1u);
					}

					repaired_day = day;

					mixer.play(structures::sound_bolt, maps.radio, 0.9f, 0.6f);

					survival.notify("\"...Morning Star to the island. We hear you.\"", 0);

					advance();
				}
			}

			else if (goal.kind == structures::goal_rescue && on_shore() && atmosphere.hours > rescue_dawn && atmosphere.hours < rescue_dusk)
			{
				hud.set_prompt("Wave the boat in   [E]");

				if (platform.tapped(structures::bind_use))
				{
					rescued = true;
					ending = true;

					advance();
				}
			}

			else if (complete(goal))
			{
				advance();
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool story_c::complete(const structures::goal_s& goal)
	{
		if (goal.kind == structures::goal_have)
		{
			return survival.count(goal.subject) >= goal.amount;
		}

		if (goal.kind == structures::goal_place)
		{
			return placed(goal.subject);
		}

		if (goal.kind == structures::goal_research)
		{
			return researched >= goal.amount;
		}

		if (goal.kind == structures::goal_reach)
		{
			return std::any_of(maps.landmarks.begin(), maps.landmarks.end(), [&](const structures::landmark_s& landmark) { return landmark.kind == goal.subject && mathematics.length(structures::vec3_s{ landmark.position.x - player.state.position.x, 0.0f, landmark.position.y - player.state.position.z }) < landmark.radius; });
		}

		if (goal.kind == structures::goal_parts)
		{
			return parts_found() >= goal.amount;
		}

		if (goal.kind == structures::goal_wait)
		{
			return day >= repaired_day + goal.amount;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void story_c::advance()
	{
		char text[96]{};

		const auto& goal{ goals[step] };

		std::snprintf(text, sizeof(text), "Done: %s", goal.title);

		survival.notify(text, 0);

		mixer.play_2d(structures::sound_craft, 0.8f, 0.75f);

		if (goal.reward != structures::item_none)
		{
			survival.give(goal.reward, goal.reward_amount, true);
		}

		done_flash = 2.5f;
		step = std::min(step + 1u, static_cast<std::uint32_t>(goal_count - 1u));
	}
	/*
	//=====================================================================================
	*/
	void story_c::searched(structures::vec3_s position)
	{
		if (step < goal_count && goals[step].kind == structures::goal_parts)
		{
			if (const auto site{ landmark_at(position) }; site >= 0 && site < static_cast<std::int32_t>(std::size(radio_parts)) && parts[site] == false)
			{
				searches[site]++;

				if (random() < radio_part_chance || searches[site] >= radio_part_pity)
				{
					parts[site] = true;

					survival.give(radio_parts[site], 1u, true);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t story_c::landmark_at(structures::vec3_s position)
	{
		for (const auto& landmark : maps.landmarks)
		{
			if (mathematics.length(structures::vec3_s{ landmark.position.x - position.x, 0.0f, landmark.position.y - position.z }) < landmark.radius + 12.0f)
			{
				return static_cast<std::int32_t>(landmark.kind);
			}
		}

		return -1;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t story_c::parts_found()
	{
		return static_cast<std::uint32_t>(std::count_if(std::begin(radio_parts), std::end(radio_parts), [](std::uint32_t part) { return survival.count(part) > 0u; }));
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t story_c::progress(const structures::goal_s& goal)
	{
		if (goal.kind == structures::goal_have)
		{
			return std::min(survival.count(goal.subject), goal.amount);
		}

		if (goal.kind == structures::goal_parts)
		{
			return parts_found();
		}

		if (goal.kind == structures::goal_wait)
		{
			return std::min(day - std::min(day, repaired_day), goal.amount);
		}

		if (goal.kind == structures::goal_research)
		{
			return std::min(researched, goal.amount);
		}

		return 0u;
	}
	/*
	//=====================================================================================
	*/
	bool story_c::placed(std::uint32_t piece)
	{
		return std::any_of(building.placed.begin(), building.placed.end(), [&](const structures::structure_s& structure) { return structure.piece == piece && structure.destroyed == false; });
	}
	/*
	//=====================================================================================
	*/
	bool story_c::near_radio()
	{
		return maps.radio_ready && mathematics.distance(player.eye, maps.radio) < radio_reach;
	}
	/*
	//=====================================================================================
	*/
	bool story_c::on_shore()
	{
		return terrain.enabled && terrain.height(player.state.position.x, player.state.position.z) < sea_level + rescue_shore;
	}
	/*
	//=====================================================================================
	*/
	std::float_t story_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
