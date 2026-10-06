
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	projectiles_c projectiles;

	void projectiles_c::clear()
	{
		arrows.clear();

		shape = nullptr;
	}
	/*
	//=====================================================================================
	*/
	void projectiles_c::launch(structures::vec3_s origin, structures::vec3_s velocity, std::float_t damage, std::int32_t owner)
	{
		if (arrows.size() >= maximum_arrows)
		{
			arrows.erase(arrows.begin());
		}

		arrows.push_back({ origin, velocity, mathematics.normalize(velocity), damage, 0.0f, owner, true });
	}
	/*
	//=====================================================================================
	*/
	void projectiles_c::update(std::float_t delta, bool input_enabled)
	{
		shape = shape ? shape : models.find("wooden_arrow");

		advance(delta);

		if (input_enabled && survival.vitals.dead == false)
		{
			const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };

			if (const auto target{ pickup_target(player.eye, forward) }; target >= 0)
			{
				hud.set_prompt("Pick up the arrow   [E]");

				if (platform.tapped(structures::bind_use))
				{
					mixer.play_2d(structures::sound_pickup, 0.4f, 1.3f);

					if (client.connected())
					{
						client.act(structures::act_arrow, arrows[target].position);

						arrows.erase(arrows.begin() + target);
					}

					else
					{
						collect(survival, arrows[target].position);
					}

					platform.consume(structures::bind_use);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void projectiles_c::advance(std::float_t delta)
	{
		for (auto& arrow : arrows)
		{
			arrow.age += delta;

			if (arrow.flying)
			{
				fly(arrow, delta);
			}
		}

		arrows.erase(std::remove_if(arrows.begin(), arrows.end(), [](const structures::arrow_s& arrow) { return arrow.age > arrow_life || arrow.position.y < -40.0f || arrow.damage < 0.0f; }), arrows.end());
	}
	/*
	//=====================================================================================
	*/
	void projectiles_c::collect(survival_c& owner, structures::vec3_s position)
	{
		auto best{ -1 };
		auto best_distance{ 0.8f };

		for (auto index{ 0u }; index < arrows.size(); index++)
		{
			if (const auto distance{ mathematics.distance(arrows[index].position, position) }; arrows[index].flying == false && distance < best_distance)
			{
				best = static_cast<std::int32_t>(index);
				best_distance = distance;
			}
		}

		if (best >= 0)
		{
			if (random() < 0.8f)
			{
				owner.give(structures::item_wooden_arrow, 1u, true);
			}

			else
			{
				owner.notify("The arrow snapped", 0);
			}

			arrows.erase(arrows.begin() + best);
		}
	}
	/*
	//=====================================================================================
	*/
	void projectiles_c::fly(structures::arrow_s& arrow, std::float_t delta)
	{
		const auto start{ arrow.position };

		arrow.velocity.y -= arrow_gravity * delta;
		arrow.velocity = arrow.velocity * (1.0f - 0.015f * delta);

		const auto end{ start + arrow.velocity * delta };
		const auto length{ mathematics.distance(start, end) };
		const auto direction{ mathematics.normalize(end - start) };
		const auto hit{ world.trace(start, end, { 0.01f, 0.01f, 0.01f }, structures::contents_solid) };

		auto distance{ 0.0f };
		auto height{ 0.0f };
		auto top{ player_height };

		if (const auto victim{ server.running && arrow.damage > 0.0f ? server.ray_player(arrow.owner, start, direction, hit.hit ? hit.fraction * length : length, server.clock, 0.0f, distance, height, top) : -1 }; victim >= 0)
		{
			const auto headshot{ height > top - player_head_zone };
			const auto damage{ arrow.damage * (headshot ? weapon_headshot_scale : (height < player_leg_zone ? weapon_leg_scale : 1.0f)) * mathematics.saturate(mathematics.length(arrow.velocity) / (arrow_speed_maximum * 0.8f)) };

			server.hurt(victim, damage, structures::death_shot, arrow.owner);

			if (arrow.owner >= 0)
			{
				server.send_hit(arrow.owner, victim, damage, headshot, server.clients[victim].alive == false, start + direction * distance);
			}

			marks.bleed(start + direction * distance, direction);

			arrow.damage = -1.0f;
		}

		else if (const auto target{ server.running || client.connected() ? -1 : weapons.ray_actor(start, direction, hit.hit ? hit.fraction * length : length, distance, height) }; target >= 0)
		{
			auto& actor{ actors.list[target] };

			const auto headshot{ height > 1.5f };
			const auto point{ start + direction * distance };
			const auto speed{ mathematics.length(arrow.velocity) };

			actors.damage(actor, arrow.damage * (headshot ? 2.0f : 1.0f) * mathematics.saturate(speed / (arrow_speed_maximum * 0.8f)), direction);

			combat.hit_marker = 1.0f;
			combat.kill_marker = actor.dead ? 1.0f : combat.kill_marker;

			particles.impact(structures::surface_flesh, point, direction * -1.0f);

			marks.bleed(point, direction);

			mixer.play(structures::sound_hit_flesh, point, 1.0f, 1.0f + random() * 0.2f);

			if (actor.dead)
			{
				survival.notify(headshot ? "Headshot kill" : "Kill", 0);
			}

			arrow.damage = -1.0f;
		}

		else if (const auto animal{ client.connected() || arrow.damage <= 0.0f ? -1 : fauna.ray(start, direction, hit.hit ? hit.fraction * length : length, distance) }; animal >= 0)
		{
			const auto point{ start + direction * distance };
			const auto damage{ arrow.damage * mathematics.saturate(mathematics.length(arrow.velocity) / (arrow_speed_maximum * 0.8f)) };
			const auto killed{ fauna.damage(static_cast<std::uint32_t>(animal), damage, start) };

			if (server.running && arrow.owner >= 0)
			{
				server.send_hit(arrow.owner, fauna_victim, damage, false, killed, point);
			}

			else if (server.running == false)
			{
				combat.hit_marker = 1.0f;
				combat.kill_marker = killed ? 1.0f : combat.kill_marker;

				particles.impact(structures::surface_flesh, point, direction * -1.0f);

				mixer.play(structures::sound_hit_flesh, point, 1.0f, 1.0f + random() * 0.2f);
			}

			marks.bleed(point, direction);

			arrow.damage = -1.0f;
		}

		else if (hit.hit)
		{
			arrow.position = hit.end + direction * 0.05f;
			arrow.heading = direction;
			arrow.flying = false;

			if (gpu.device)
			{
				particles.impact(hit.surface, hit.end, hit.normal);

				mixer.play(hit.surface == structures::surface_wood ? structures::sound_hit_wood : (hit.surface == structures::surface_rock || hit.surface == structures::surface_concrete ? structures::sound_hit_rock : structures::sound_hit_soft), hit.end, 0.7f, 1.3f + random() * 0.2f);
			}

			if (hit.brush >= 0 && client.connected() == false)
			{
				building.damage(hit.brush, 2.0f, true);
			}
		}

		else
		{
			arrow.position = end;
			arrow.heading = direction;
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t projectiles_c::pickup_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		auto best{ -1 };
		auto best_away{ 0.3f };

		for (auto index{ 0u }; index < arrows.size(); index++)
		{
			if (const auto& arrow{ arrows[index] }; arrow.flying == false)
			{
				const auto middle{ arrow.position - arrow.heading * (arrow_length * 0.5f) };
				const auto along{ mathematics.dot(middle - origin, forward) };
				const auto away{ mathematics.length(middle - origin - forward * along) };

				if (along > 0.2f && along < interact_range + 0.4f && away < best_away)
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
	structures::mat4_s projectiles_c::placement(const structures::arrow_s& arrow)
	{
		const auto up{ mathematics.normalize(std::fabs(arrow.heading.y) > 0.95f ? structures::vec3_s{ 1.0f, 0.0f, 0.0f } - arrow.heading * arrow.heading.x : structures::vec3_s{ 0.0f, 1.0f, 0.0f } - arrow.heading * arrow.heading.y) };

		return mathematics.basis(arrow.heading, up, mathematics.cross(arrow.heading, up), arrow.position);
	}
	/*
	//=====================================================================================
	*/
	void projectiles_c::submit()
	{
		if (shape)
		{
			for (const auto& arrow : arrows)
			{
				const auto world_matrix{ placement(arrow) };

				renderer.submit(&shape->mesh, world_matrix, world_matrix, -1.0f, arrow.flying ? structures::draw_flag_no_shadow : 0u);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t projectiles_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
