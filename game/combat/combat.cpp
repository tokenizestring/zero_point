
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	combat_c combat;

	bool combat_c::melee(structures::vec3_s origin, structures::vec3_s direction, std::float_t reach, std::float_t damage)
	{
		auto best{ -1 };
		auto best_along{ reach };
		auto best_height{ 0.0f };

		for (auto index{ 0u }; index < actors.list.size(); index++)
		{
			const auto& actor{ actors.list[index] };

			if (actor.behavior == structures::actor_behavior_hostile && actor.dead == false && actor.dormant == false)
			{
				const auto bottom{ actor.position + structures::vec3_s{ 0.0f, actor_radius, 0.0f } };
				const auto axis_length{ actor_height - actor_radius * 2.0f };

				for (auto step{ 0u }; step <= 24u; step++)
				{
					const auto along{ reach * static_cast<std::float_t>(step) / 24.0f };
					const auto point{ origin + direction * along };
					const auto height{ std::clamp(point.y - bottom.y, 0.0f, axis_length) };
					const auto closest{ bottom + structures::vec3_s{ 0.0f, height, 0.0f } };

					if (along < best_along && mathematics.distance(point, closest) < actor_radius + 0.08f)
					{
						best = static_cast<std::int32_t>(index);
						best_along = along;
						best_height = point.y - actor.position.y;
					}
				}
			}
		}

		if (best >= 0 && world.trace(origin, origin + direction * best_along, { 0.02f, 0.02f, 0.02f }, structures::contents_solid).fraction >= 0.99f)
		{
			auto& actor{ actors.list[best] };

			const auto headshot{ best_height > 1.5f };

			actors.damage(actor, damage * (headshot ? 2.0f : 1.0f), direction);

			particles.impact(structures::surface_flesh, origin + direction * (best_along - 0.1f), direction * -1.0f);

			mixer.play(structures::sound_hit_flesh, origin + direction * best_along, 1.0f, 0.9f + mixer.random() * 0.2f);
			mixer.play(actor.dead ? structures::sound_zombie_groan : structures::sound_zombie_snarl, actor.position + structures::vec3_s{ 0.0f, 1.6f, 0.0f }, 0.95f, actor.dead ? 0.8f : 0.95f + mixer.random() * 0.15f);

			hit_marker = 1.0f;
			kill_marker = actor.dead ? 1.0f : kill_marker;

			if (actor.dead)
			{
				survival.notify(headshot ? "Headshot kill" : "Kill", 0);
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t combat_c::corpse_target()
	{
		const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };

		auto best{ -1 };
		auto best_away{ 0.75f };

		for (auto index{ 0u }; index < actors.list.size(); index++)
		{
			const auto& actor{ actors.list[index] };

			if (actor.dead && actor.looted == false && actor.death > 0.8f && actor.dormant == false)
			{
				const auto back{ mathematics.flat_forward(actor.body_yaw) * -0.85f };
				const auto offset{ actor.position + back + structures::vec3_s{ 0.0f, 0.25f, 0.0f } - player.eye };
				const auto along{ mathematics.dot(offset, forward) };
				const auto away{ mathematics.length(offset - forward * along) };

				if (along > 0.0f && along < interact_range + 0.4f && away < best_away)
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
	void combat_c::update(std::float_t delta, bool input_enabled)
	{
		hit_marker = std::max(0.0f, hit_marker - delta * 5.0f);
		kill_marker = std::max(0.0f, kill_marker - delta * 1.6f);

		if (input_enabled && survival.vitals.dead == false && harvest.swinging == false)
		{
			if (const auto target{ corpse_target() }; target >= 0)
			{
				hud.set_prompt("Search body   [E]");

				if (platform.tapped(structures::bind_use))
				{
					loot(actors.list[target]);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void combat_c::loot(structures::actor_s& actor)
	{
		actor.looted = true;

		harvest.roll(survival, corpse_loot);
	}
}

//=====================================================================================
