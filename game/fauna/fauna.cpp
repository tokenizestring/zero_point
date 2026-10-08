
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	fauna_c fauna;

	void fauna_c::create()
	{
		for (auto kind{ 0u }; kind < structures::species_count; kind++)
		{
			const auto& species{ species_table[kind] };

			bodies[kind] = species.enabled ? characters.find(species.character) : nullptr;
			distant[kind] = bodies[kind] ? characters.find(species.lod) : nullptr;

			for (auto slot{ 0u }; slot < structures::animal_clip_count; slot++)
			{
				clips[kind][slot] = bodies[kind] ? characters.clip(species.clips[slot]) : UINT32_MAX;
			}
		}

		ready = std::any_of(std::begin(bodies), std::end(bodies), [](const structures::character_s* body) { return body != nullptr; });

		logger.write("fauna: %s", ready ? "animal models ready" : "no animal models");
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::clear()
	{
		animals.clear();
		herds.clear();
		bites.clear();

		next_id = 1u;
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::populate()
	{
		clear();

		if (terrain.enabled)
		{
			for (auto kind{ 0u }; kind < std::size(herd_kinds); kind++)
			{
				for (auto count{ 0u }; species_table[herd_kinds[kind].leader].enabled && count < herd_kinds[kind].count; count++)
				{
					if (structures::vec3_s home{}; habitat(kind, home, false))
					{
						spawn_herd(kind, home);
					}
				}
			}
		}

		logger.write("fauna: %zu animals in %zu herds", animals.size(), herds.size());
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::spawn_herd(std::uint32_t kind, structures::vec3_s home)
	{
		const auto& herd_kind{ herd_kinds[kind] };
		const auto size{ std::min(herd_kind.minimum + static_cast<std::uint32_t>(random() * static_cast<std::float_t>(herd_kind.maximum - herd_kind.minimum + 1u)), herd_kind.maximum) };
		const auto first{ static_cast<std::uint32_t>(animals.size()) };
		const auto count{ std::min(size, fauna_maximum - std::min(first, fauna_maximum)) };

		if (count)
		{
			herds.push_back({ home, home, 20.0f + random() * 60.0f, 0.0f, kind, first, count });

			animals.resize(animals.size() + count);

			for (auto member{ 0u }; member < count; member++)
			{
				place(first + member, member == 0u ? herd_kind.leader : herd_kind.member, static_cast<std::uint32_t>(herds.size() - 1u), home, member == 0u);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool fauna_c::relocate(std::uint32_t index, structures::vec3_s near_point, std::float_t yaw)
	{
		for (auto attempt{ 0u }; attempt < 16u && index < herds.size(); attempt++)
		{
			if (const auto spot{ near_point + mathematics.flat_forward(yaw + static_cast<std::float_t>(attempt) * 0.4f) * 40.0f }; walkable(spot))
			{
				auto& herd{ herds[index] };

				herd.home = { spot.x, terrain.height(spot.x, spot.z), spot.z };
				herd.goal = herd.home;
				herd.empty = 0.0f;

				for (auto member{ 0u }; member < herd.count; member++)
				{
					place(herd.first + member, member == 0u ? herd_kinds[herd.kind].leader : herd_kinds[herd.kind].member, index, herd.home, member == 0u);
				}

				logger.write("fauna: herd %u moved to %.0f %.0f", index, spot.x, spot.z);

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::place(std::uint32_t index, std::uint32_t species, std::uint32_t herd, structures::vec3_s home, bool leader)
	{
		const auto angle{ random() * two_pi };
		const auto reach{ leader ? 0.0f : 2.0f + random() * fauna_herd_spread };
		const auto x{ home.x + std::sin(angle) * reach };
		const auto z{ home.z + std::cos(angle) * reach };

		auto& animal{ animals[index] };

		animal = {};
		animal.position = { x, terrain.height(x, z), z };
		animal.goal = animal.position;
		animal.yaw = random() * two_pi;
		animal.health = species_table[species].health;
		animal.timer = random() * 8.0f;
		animal.think = random() * fauna_think_interval;
		animal.species = species;
		animal.state = random() < 0.6f ? structures::animal_graze : structures::animal_idle;
		animal.herd = herd;
		animal.id = next_id++;
		animal.alive = true;

		next_id = next_id ? next_id : 1u;
	}
	/*
	//=====================================================================================
	*/
	bool fauna_c::habitat(std::uint32_t kind, structures::vec3_s& home, bool far_from_watchers)
	{
		for (auto attempt{ 0u }; attempt < 160u; attempt++)
		{
			const auto x{ terrain_origin + random() * terrain_size };
			const auto z{ terrain_origin + random() * terrain_size };
			const structures::vec3_s point{ x, terrain.height(x, z), z };
			const auto crowded{ far_from_watchers && std::any_of(watchers.begin(), watchers.end(), [&](const structures::watcher_s& watcher) { return mathematics.distance(watcher.position, point) < fauna_respawn_clearance; }) };

			if ((herd_kinds[kind].habitat & (1u << terrain.biome(x, z))) != 0u && walkable(point) && crowded == false)
			{
				home = point;

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool fauna_c::walkable(structures::vec3_s point)
	{
		const auto inside{ point.x > terrain_origin + 40.0f && point.x < terrain_origin + terrain_size - 40.0f && point.z > terrain_origin + 40.0f && point.z < terrain_origin + terrain_size - 40.0f };

		return inside && terrain.height(point.x, point.z) > sea_level + fauna_shore && terrain.normal(point.x, point.z).y > fauna_steep;
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::simulate(std::float_t delta)
	{
		clock += delta;

		for (auto index{ 0u }; index < herds.size(); index++)
		{
			auto& herd{ herds[index] };

			auto living{ 0u };
			auto remains{ 0u };

			for (auto member{ herd.first }; member < herd.first + herd.count; member++)
			{
				living += animals[member].alive ? 1u : 0u;
				remains += animals[member].alive == false && animals[member].yields ? 1u : 0u;
			}

			herd.timer -= delta;
			herd.empty = living ? 0.0f : herd.empty + delta;

			if (living && herd.timer <= 0.0f)
			{
				auto found{ false };

				for (auto attempt{ 0u }; attempt < 12u && found == false; attempt++)
				{
					const auto angle{ random() * two_pi };
					const auto reach{ 20.0f + random() * fauna_roam };
					const auto x{ herd.home.x + std::sin(angle) * reach };
					const auto z{ herd.home.z + std::cos(angle) * reach };
					const structures::vec3_s point{ x, terrain.height(x, z), z };

					found = walkable(point) && (herd_kinds[herd.kind].habitat & (1u << terrain.biome(x, z))) != 0u;
					herd.goal = found ? point : herd.goal;
				}

				herd.timer = 60.0f + random() * 120.0f;
			}

			if ((herd.empty > fauna_respawn_time && remains == 0u) || herd.empty > fauna_carcass_time)
			{
				if (structures::vec3_s home{}; habitat(herd.kind, home, true))
				{
					herd.home = home;
					herd.goal = home;
					herd.empty = 0.0f;

					for (auto member{ 0u }; member < herd.count; member++)
					{
						place(herd.first + member, member == 0u ? herd_kinds[herd.kind].leader : herd_kinds[herd.kind].member, index, home, member == 0u);
					}
				}

				else
				{
					herd.empty = fauna_respawn_time * 0.5f;
				}
			}

			herd.rest += delta;

			if (herd.rest >= fauna_dormant_step || watched(animals[herd.first].position))
			{
				for (auto member{ herd.first }; member < herd.first + herd.count; member++)
				{
					live(animals[member], herd.rest);
				}

				herd.rest = 0.0f;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::live(structures::animal_s& animal, std::float_t delta)
	{
		if (animal.alive)
		{
			animal.think -= delta;
			animal.timer -= delta;
			animal.hurt = std::max(animal.hurt - delta * 0.5f, 0.0f);
			animal.fear = std::max(animal.fear - fauna_calm_rate * delta, 0.0f);

			if (animal.think <= 0.0f)
			{
				animal.think = std::max(animal.think + fauna_think_interval, 0.0f);

				think(animal);
			}

			steer(animal, delta);

			if (animal.bleed > 0.0f)
			{
				animal.health -= animal.bleed * delta;
				animal.bleed = std::max(animal.bleed - animal.bleed * fauna_clot * delta - 0.002f * delta, 0.0f);
				animal.drip -= delta;

				if (animal.drip <= 0.0f && animal.bleed > fauna_drip_threshold)
				{
					animal.drip = fauna_drip * (0.6f + random() * 0.8f);

					marks.bleed(animal.position + structures::vec3_s{ 0.0f, 0.35f, 0.0f }, { 0.0f, -1.0f, 0.0f });
				}

				if (animal.health <= 0.0f)
				{
					die(animal);
				}
			}
		}

		else if (animal.yields)
		{
			animal.dead_time += delta;
			animal.speed = 0.0f;
			animal.yields = animal.dead_time > fauna_carcass_time ? 0u : animal.yields;
		}
	}
	/*
	//=====================================================================================
	*/
	bool fauna_c::watched(structures::vec3_s position)
	{
		return std::any_of(watchers.begin(), watchers.end(), [&](const structures::watcher_s& watcher) { return mathematics.distance(watcher.position, position) < fauna_wake_range; });
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::think(structures::animal_s& animal)
	{
		const auto& species{ species_table[animal.species] };
		const auto& herd{ herds[animal.herd] };
		const auto& leader{ animals[herd.first] };
		const auto leading{ &animal == &leader };

		auto alarm{ 0.0f };
		auto spotted{ animal.threat };

		for (const auto& watcher : watchers)
		{
			if (const auto fright{ mathematics.saturate(fauna_fright - mathematics.distance(watcher.position, animal.position) / (species.sight * watcher.noise * 0.75f)) }; fright > alarm)
			{
				alarm = fright;
				spotted = watcher.position;
			}
		}

		if (alarm > 0.0f)
		{
			animal.fear = std::max(animal.fear, alarm);
			animal.threat = spotted;
		}

		const auto close{ mathematics.distance(animal.threat, animal.position) };
		const auto calm{ animal.state == structures::animal_graze || animal.state == structures::animal_idle || animal.state == structures::animal_rest || animal.state == structures::animal_walk };

		if (animal.state == structures::animal_charge)
		{
			if (animal.timer <= 0.0f || close > species.sight)
			{
				animal.state = structures::animal_flee;
				animal.timer = fauna_flee_time * 0.6f;
			}
		}

		else if (animal.fear > 0.55f && animal.state != structures::animal_flee)
		{
			const auto bold{ species.courage > 0.0f && close < 14.0f && (animal.hurt > 0.0f || random() < species.courage * 0.3f) };

			animal.state = bold ? structures::animal_charge : structures::animal_flee;
			animal.timer = bold ? 6.0f : fauna_flee_time * (0.8f + random() * 0.5f);
		}

		else if (animal.fear > 0.25f && calm)
		{
			animal.state = structures::animal_alert;
			animal.timer = 2.0f + random() * 3.0f;
		}

		else if (animal.state == structures::animal_flee && animal.timer <= 0.0f)
		{
			animal.state = structures::animal_walk;
			animal.goal = herd.goal;
			animal.timer = 25.0f;
		}

		else if (animal.state == structures::animal_alert && animal.timer <= 0.0f)
		{
			animal.state = random() < 0.5f ? structures::animal_graze : structures::animal_idle;
			animal.timer = 4.0f + random() * 6.0f;
		}

		else if (animal.state == structures::animal_walk && (mathematics.distance(structures::vec3_s{ animal.position.x, 0.0f, animal.position.z }, structures::vec3_s{ animal.goal.x, 0.0f, animal.goal.z }) < 2.0f || animal.timer <= 0.0f))
		{
			animal.state = random() < 0.65f ? structures::animal_graze : structures::animal_idle;
			animal.timer = 5.0f + random() * 10.0f;
		}

		else if ((animal.state == structures::animal_graze || animal.state == structures::animal_idle || animal.state == structures::animal_rest) && animal.timer <= 0.0f)
		{
			const auto roll{ random() };
			const auto angle{ random() * two_pi };
			const auto straying{ leading == false && mathematics.distance(animal.position, leader.position) > fauna_herd_spread * 1.6f };
			const auto wandering{ leading && mathematics.distance(animal.position, herd.goal) > 6.0f };
			const auto anchor{ leading ? animal.position : leader.position };
			const auto reach{ leading ? 4.0f + random() * 8.0f : 2.0f + random() * fauna_herd_spread };

			animal.state = straying || wandering || roll < 0.15f ? structures::animal_walk : (roll < 0.62f ? structures::animal_graze : (roll < 0.92f ? structures::animal_idle : structures::animal_rest));
			animal.goal = wandering ? herd.goal : structures::vec3_s{ anchor.x + std::sin(angle) * reach, anchor.y, anchor.z + std::cos(angle) * reach };
			animal.timer = animal.state == structures::animal_walk ? 30.0f : (animal.state == structures::animal_rest ? 25.0f + random() * 30.0f : 5.0f + random() * 10.0f);
		}
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::steer(structures::animal_s& animal, std::float_t delta)
	{
		const auto& species{ species_table[animal.species] };
		const auto spread{ (static_cast<std::float_t>((static_cast<std::uint32_t>(animal.id) * 2654435761u) >> 24u) / 255.0f - 0.5f) * 0.9f };

		auto target{ 0.0f };
		auto heading{ animal.yaw };

		if (animal.state == structures::animal_walk)
		{
			target = species.walk;
			heading = std::atan2(animal.goal.x - animal.position.x, animal.goal.z - animal.position.z);
		}

		else if (animal.state == structures::animal_flee)
		{
			target = animal.timer < fauna_flee_time * 0.3f ? species.trot : species.run;
			heading = std::atan2(animal.position.x - animal.threat.x, animal.position.z - animal.threat.z) + spread;
		}

		else if (animal.state == structures::animal_charge)
		{
			target = species.run;
			heading = std::atan2(animal.threat.x - animal.position.x, animal.threat.z - animal.position.z);

			if (mathematics.distance(animal.threat, animal.position) < fauna_charge_reach)
			{
				bites.push_back(animal.threat);

				animal.state = structures::animal_flee;
				animal.timer = 2.0f;
				animal.fear = 1.0f;
			}
		}

		else if (animal.state == structures::animal_alert)
		{
			heading = std::atan2(animal.threat.x - animal.position.x, animal.threat.z - animal.position.z);
		}

		if (target > 0.0f)
		{
			auto clear{ false };
			auto bend{ 0.0f };

			for (auto attempt{ 0u }; attempt < 7u && clear == false; attempt++)
			{
				const auto side{ attempt % 2u ? 1.0f : -1.0f };

				bend = attempt ? side * 0.5f * static_cast<std::float_t>((attempt + 1u) / 2u) : 0.0f;

				const auto probe{ animal.position + mathematics.flat_forward(heading + bend) * (2.5f + target * 0.5f) };
				const auto chest{ animal.position + structures::vec3_s{ 0.0f, species.center, 0.0f } };
				const auto blocked{ world.trace(chest, structures::vec3_s{ probe.x, chest.y, probe.z }, {}, structures::contents_solid) };

				clear = walkable(probe) && (blocked.hit == false || blocked.brush < 0);
			}

			heading = clear ? heading + bend : heading + pi * 0.5f;
			target = clear ? target : target * 0.4f;
		}

		const auto turn{ fauna_turn_rate * (target > species.trot ? 1.6f : 1.0f) * delta };

		animal.yaw = mathematics.wrap_angle(animal.yaw + std::clamp(mathematics.angle_difference(animal.yaw, heading), -turn, turn));
		animal.speed = mathematics.approach(animal.speed, target, fauna_acceleration * delta * (target > animal.speed ? 1.0f : 1.8f));

		const auto step{ mathematics.flat_forward(animal.yaw) * (animal.speed * delta) };
		const auto next{ animal.position + step };

		if (walkable(next))
		{
			animal.position = { next.x, terrain.height(next.x, next.z), next.z };
		}

		else
		{
			animal.speed *= 0.5f;
		}

		animal.velocity = delta > 0.0f ? step / delta : structures::vec3_s{};
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::alarm(structures::vec3_s origin, std::float_t loudness)
	{
		for (auto& animal : animals)
		{
			if (animal.alive)
			{
				const auto hearing{ species_table[animal.species].hearing * loudness };

				if (const auto distance{ mathematics.distance(animal.position, origin) }; distance < hearing)
				{
					animal.fear = std::max(animal.fear, distance < hearing * 0.6f ? 1.0f : 0.6f);
					animal.threat = origin;
					animal.think = std::min(animal.think, random() * 0.25f);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t fauna_c::ray(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance)
	{
		auto best{ -1 };

		distance = range;

		for (auto index{ 0u }; index < animals.size(); index++)
		{
			if (const auto& animal{ animals[index] }; animal.alive || animal.yields)
			{
				const auto& species{ species_table[animal.species] };
				const auto ahead{ mathematics.flat_forward(animal.yaw) };
				const auto center{ animal.position + structures::vec3_s{ 0.0f, animal.alive ? species.center : fauna_dead_center, 0.0f } };
				const auto tail{ center - ahead * species.half };
				const auto body{ ahead * (species.half * 2.0f) };
				const auto line{ direction * range };
				const auto offset{ origin - tail };
				const auto a{ mathematics.dot(line, line) };
				const auto b{ mathematics.dot(line, body) };
				const auto c{ mathematics.dot(line, offset) };
				const auto e{ mathematics.dot(body, body) };
				const auto f{ mathematics.dot(body, offset) };
				const auto denominator{ a * e - b * b };
				const auto first{ denominator > 0.000001f ? mathematics.saturate((b * f - c * e) / denominator) : 0.0f };
				const auto second{ (b * first + f) / e };
				const auto s{ second < 0.0f ? mathematics.saturate(-c / a) : (second > 1.0f ? mathematics.saturate((b - c) / a) : first) };
				const auto t{ mathematics.saturate(second) };
				const auto gap{ mathematics.distance(origin + line * s, tail + body * t) };
				const auto radius{ species.radius * (animal.alive ? 1.0f : 1.25f) };

				if (gap < radius && s * range < distance)
				{
					best = static_cast<std::int32_t>(index);
					distance = s * range;
					struck = t;
				}
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	bool fauna_c::damage(std::uint32_t index, std::float_t amount, structures::vec3_s origin)
	{
		auto& animal{ animals[index] };

		if (animal.alive)
		{
			const auto zone{ struck > fauna_head_zone ? 0u : (struck > fauna_heart_zone ? 1u : (struck > fauna_gut_zone ? 2u : 3u)) };

			animal.health -= amount * fauna_zone_damage[zone];
			animal.bleed += amount * fauna_zone_bleed[zone];
			animal.hurt = 1.0f;
			animal.fear = 1.0f;
			animal.threat = origin;
			animal.think = 0.0f;

			if (animal.health <= 0.0f)
			{
				die(animal);

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::die(structures::animal_s& animal)
	{
		animal.alive = false;
		animal.state = structures::animal_dead;
		animal.speed = 0.0f;
		animal.dead_time = 0.0f;
		animal.bleed = 0.0f;
		animal.yields = fauna_carve_strikes;

		marks.pool(animal.position);

		alarm(animal.position, 0.35f);
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::fall(std::uint32_t species, structures::vec3_s position, std::float_t yaw)
	{
		if (animals.size() < fauna_maximum)
		{
			structures::animal_s animal{};

			animal.position = position;
			animal.goal = position;
			animal.yaw = yaw;
			animal.species = species;
			animal.herd = UINT32_MAX;
			animal.id = next_id++;

			next_id = next_id ? next_id : 1u;

			die(animal);

			animals.push_back(std::move(animal));
		}
	}
	/*
	//=====================================================================================
	*/
	bool fauna_c::carve(survival_c& owner, std::uint32_t index)
	{
		auto& animal{ animals[index] };

		if (animal.alive == false && animal.yields)
		{
			const auto& species{ species_table[animal.species] };
			const auto done{ fauna_carve_strikes - animal.yields };
			const auto share = [&](std::uint32_t total)
				{
					return total * (done + 1u) / fauna_carve_strikes - total * done / fauna_carve_strikes;
				};

			const auto meat{ share(species.meat_amount) };
			const auto hide{ share(species.hide_amount) };
			const auto fat{ share(species.fat_amount) };
			const auto bone{ share(species.bone_amount) };

			owner.give(species.meat, meat, true);
			owner.give(structures::item_hide, hide, true);
			owner.give(structures::item_animal_fat, fat, true);
			owner.give(structures::item_bone, bone, true);

			animal.yields--;

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t fauna_c::melee(survival_c& owner, structures::vec3_s eye, structures::vec3_s forward, std::float_t reach, std::float_t strength, structures::vec3_s& point)
	{
		auto distance{ 0.0f };

		if (const auto target{ ray(eye, forward, reach, distance) }; target >= 0)
		{
			point = eye + forward * distance;

			if (animals[target].alive)
			{
				return damage(static_cast<std::uint32_t>(target), strength, eye) ? 2u : 1u;
			}

			return carve(owner, static_cast<std::uint32_t>(target)) ? 3u : 0u;
		}

		return 0u;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t fauna_c::carcass(structures::vec3_s eye, structures::vec3_s forward)
	{
		auto distance{ 0.0f };

		if (const auto target{ ray(eye, forward, fauna_carve_reach, distance) }; target >= 0 && animals[target].alive == false)
		{
			return target;
		}

		return -1;
	}
	/*
	//=====================================================================================
	*/
	std::float_t fauna_c::noise(const structures::movement_state_s& state)
	{
		const auto speed{ mathematics.length(structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z }) };

		return (state.flags & structures::movement_crouched) ? 0.45f : (speed > move_speed_run ? 1.2f : (speed > 1.0f ? 0.85f : 0.55f));
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::write(stream_writer_c& writer, structures::vec3_s viewer)
	{
		nearby.clear();

		for (auto index{ 0u }; index < animals.size(); index++)
		{
			if (const auto& animal{ animals[index] }; animal.alive || animal.yields)
			{
				if (const auto distance{ mathematics.distance(animal.position, viewer) }; distance < fauna_sync_range)
				{
					nearby.push_back({ distance, index });
				}
			}
		}

		std::sort(nearby.begin(), nearby.end(), [](const std::pair<std::float_t, std::uint32_t>& a, const std::pair<std::float_t, std::uint32_t>& b) { return a.first < b.first; });

		const auto room{ writer.remaining() > 1u ? (writer.remaining() - 1u) / fauna_animal_bytes : 0u };
		const auto count{ static_cast<std::uint32_t>(std::min<std::size_t>({ nearby.size(), static_cast<std::size_t>(fauna_snapshot_animals), static_cast<std::size_t>(room) })) };

		writer.u8(static_cast<std::uint8_t>(count));

		for (auto entry{ 0u }; entry < count; entry++)
		{
			const auto& animal{ animals[nearby[entry].second] };

			writer.u16(animal.id);
			writer.u8(static_cast<std::uint8_t>(animal.species));
			writer.u8(static_cast<std::uint8_t>(animal.state));
			writer.i32(static_cast<std::int32_t>(std::round(animal.position.x * net_position_scale)));
			writer.i16(static_cast<std::int16_t>(std::clamp(animal.position.y * net_position_scale, -32767.0f, 32767.0f)));
			writer.i32(static_cast<std::int32_t>(std::round(animal.position.z * net_position_scale)));
			writer.u8(static_cast<std::uint8_t>(static_cast<std::int32_t>(std::round(animal.yaw / two_pi * 256.0f)) & 255));
			writer.u8(static_cast<std::uint8_t>(std::clamp(animal.speed * 10.0f, 0.0f, 255.0f)));
			writer.u8(static_cast<std::uint8_t>(animal.alive ? std::clamp(animal.health / species_table[animal.species].health * 255.0f, 1.0f, 255.0f) : 0.0f));
		}
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::read(stream_reader_c& reader, std::double_t time)
	{
		const auto count{ reader.u8() };

		for (auto entry{ 0u }; entry < count && reader.overflow == false; entry++)
		{
			const auto id{ reader.u16() };
			const auto species{ static_cast<std::uint32_t>(reader.u8()) };
			const auto state{ static_cast<std::uint32_t>(reader.u8()) };
			const auto x{ static_cast<std::float_t>(reader.i32()) / net_position_scale };
			const auto y{ static_cast<std::float_t>(reader.i16()) / net_position_scale };
			const auto z{ static_cast<std::float_t>(reader.i32()) / net_position_scale };
			const auto yaw{ static_cast<std::float_t>(reader.u8()) / 256.0f * two_pi };
			const auto speed{ static_cast<std::float_t>(reader.u8()) / 10.0f };
			const auto health{ static_cast<std::float_t>(reader.u8()) / 255.0f };

			if (reader.overflow == false && species < structures::species_count)
			{
				auto index{ find(id) };

				if (index < 0 && animals.size() < fauna_maximum)
				{
					structures::animal_s animal{};

					animal.id = id;
					animal.species = species;
					animal.from = { x, y, z };
					animal.to = animal.from;
					animal.shown = animal.from;
					animal.position = animal.from;
					animal.from_yaw = yaw;
					animal.to_yaw = yaw;
					animal.shown_yaw = yaw;
					animal.yaw = yaw;
					animal.from_time = time - 1.0;
					animal.to_time = time - 1.0;

					animals.push_back(std::move(animal));

					index = static_cast<std::int32_t>(animals.size()) - 1;
				}

				if (index >= 0 && time > animals[index].to_time)
				{
					auto& animal{ animals[index] };

					animal.from = animal.to;
					animal.from_yaw = animal.to_yaw;
					animal.from_time = animal.to_time;
					animal.to = { x, y, z };
					animal.to_yaw = yaw;
					animal.to_time = time;
					animal.species = species;
					animal.state = state;
					animal.speed = speed;
					animal.alive = state != structures::animal_dead;
					animal.health = health * species_table[species].health;
					animal.yields = animal.alive ? 0u : 1u;
					animal.seen = time;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t fauna_c::find(std::uint16_t id)
	{
		for (auto index{ 0u }; index < animals.size(); index++)
		{
			if (animals[index].id == id)
			{
				return static_cast<std::int32_t>(index);
			}
		}

		return -1;
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::update(std::float_t delta, std::double_t render_time, bool mirrored)
	{
		if (mirrored)
		{
			animals.erase(std::remove_if(animals.begin(), animals.end(), [&](const structures::animal_s& animal) { return animal.seen + fauna_stale < render_time; }), animals.end());
		}

		for (auto& animal : animals)
		{
			if (mirrored)
			{
				const auto span{ animal.to_time - animal.from_time };
				const auto fraction{ static_cast<std::float_t>(span > 0.0001 ? std::clamp((render_time - animal.from_time) / span, 0.0, 1.25) : 1.0) };

				animal.shown = mathematics.lerp(animal.from, animal.to, fraction);
				animal.shown_yaw = mathematics.wrap_angle(animal.from_yaw + mathematics.angle_difference(animal.from_yaw, animal.to_yaw) * fraction);
				animal.shown_speed = mathematics.damp(animal.shown_speed, animal.speed, 8.0f, delta);
				animal.position = animal.shown;
				animal.yaw = animal.shown_yaw;
			}

			else
			{
				animal.shown = animal.position;
				animal.shown_yaw = animal.yaw;
				animal.shown_speed = animal.speed;
			}

			const auto present{ (animal.alive || animal.yields) && bodies[animal.species] && mathematics.distance(animal.shown, renderer.camera.position) < fauna_draw_distance };

			if (present)
			{
				animate(animal, delta);
			}

			else
			{
				animal.frames = 0u;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::animate(structures::animal_s& animal, std::float_t delta)
	{
		const auto& species{ species_table[animal.species] };
		const auto range{ mathematics.distance(animal.shown, renderer.camera.position) };
		const auto& character{ range > fauna_lod_distance && distant[animal.species] ? *distant[animal.species] : *bodies[animal.species] };
		const auto dead{ animal.alive == false };
		const auto moving{ animal.shown_speed > 0.25f && dead == false };
		const auto resting{ animal.state == structures::animal_rest ? structures::animal_clip_rest : (animal.state == structures::animal_alert ? structures::animal_clip_alert : ((animal.id + static_cast<std::uint32_t>(clock * 0.1)) % 4u == 0u ? structures::animal_clip_look : structures::animal_clip_idle)) };
		const auto mode{ dead ? static_cast<std::uint32_t>(structures::animal_clip_death) : (moving ? static_cast<std::uint32_t>(structures::animal_clip_count) : (animal.state == structures::animal_graze ? static_cast<std::uint32_t>(structures::animal_clip_graze) : static_cast<std::uint32_t>(resting))) };
		const std::float_t speeds[3] = { species.walk, species.trot, species.run };
		const std::uint32_t gaits[3] = { clips[animal.species][structures::animal_clip_walk], clips[animal.species][structures::animal_clip_trot], clips[animal.species][structures::animal_clip_run] };
		const auto speed{ std::clamp(animal.shown_speed, speeds[0], speeds[2]) };
		const auto upper{ speed > speeds[1] ? 2u : 1u };
		const auto weight{ mathematics.saturate((speed - speeds[upper - 1u]) / std::max(speeds[upper] - speeds[upper - 1u], 0.01f)) };
		const auto low_duration{ gaits[upper - 1u] < characters.clips.size() ? characters.clips[gaits[upper - 1u]].header.duration : 1.0f };
		const auto high_duration{ gaits[upper] < characters.clips.size() ? characters.clips[gaits[upper]].header.duration : 1.0f };
		const auto duration{ mathematics.lerp(low_duration, high_duration, weight) };
		const auto rate{ animal.shown_speed / std::max(mathematics.lerp(speeds[upper - 1u], speeds[upper], weight), 0.1f) };

		if (animal.palette.size() < character.bones.size())
		{
			animal.palette.resize(maximum_bones);
			animal.previous_palette.resize(maximum_bones);
		}

		if (animal.frames == 0u)
		{
			animal.mode = mode;
			animal.previous_mode = mode;
			animal.blend = 1.0f;
			animal.clip_time = dead ? 10.0f : random() * 4.0f;
		}

		if (mode != animal.mode)
		{
			animal.previous_mode = animal.mode;
			animal.previous_time = animal.clip_time;
			animal.mode = mode;
			animal.clip_time = 0.0f;
			animal.blend = 0.0f;
		}

		const auto stride{ animal.phase };
		const auto beats{ animal.shown_speed > species.trot ? 1.0f : 2.0f };

		animal.blend = std::min(animal.blend + delta * fauna_blend_speed, 1.0f);
		animal.clip_time += delta;
		animal.previous_time += delta;
		animal.phase += delta * rate / std::max(duration, 0.1f);
		animal.phase -= std::floor(animal.phase);

		if (moving && range < fauna_hoof_range && std::floor(stride * beats) != std::floor(animal.phase * beats))
		{
			mixer.play(mixer.surface_sound(animal.shown), animal.shown, std::min(fauna_hoof_volume * (1.0f + animal.shown_speed), 0.8f), species.hoof * (0.92f + random() * 0.16f));
		}

		sample(animal, character, animal.mode, animal.clip_time, current);

		if (animal.blend < 1.0f)
		{
			sample(animal, character, animal.previous_mode, animal.previous_time, previous);

			characters.blend(character, previous, current, animal.blend, current);
		}

		std::swap(animal.palette, animal.previous_palette);

		if (animal.palette.size() < character.bones.size())
		{
			animal.palette.resize(maximum_bones);
		}

		characters.palette(character, current, 0.0f, 0.0f, animal.palette.data());

		const auto normal{ terrain.normal(animal.shown.x, animal.shown.z) };
		const auto up{ mathematics.normalize(mathematics.lerp(structures::vec3_s{ 0.0f, 1.0f, 0.0f }, normal, dead ? 1.0f : fauna_slope_follow)) };
		const auto ahead{ mathematics.flat_forward(animal.shown_yaw) };
		const auto forward{ mathematics.normalize(ahead - up * mathematics.dot(ahead, up)) };
		const auto right{ mathematics.cross(up, forward) };

		animal.previous_world = animal.world;
		animal.world = mathematics.multiply(mathematics.rotation_y(species.facing), mathematics.basis(right, up, forward, animal.shown));

		if (animal.frames == 0u)
		{
			animal.previous_world = animal.world;
			animal.previous_palette = animal.palette;
		}

		animal.frames++;
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::sample(structures::animal_s& animal, const structures::character_s& character, std::uint32_t mode, std::float_t time, structures::pose_s& pose)
	{
		const auto& species{ species_table[animal.species] };
		const auto* set{ clips[animal.species] };

		if (mode == structures::animal_clip_count)
		{
			const std::float_t speeds[3] = { species.walk, species.trot, species.run };
			const std::uint32_t gaits[3] = { set[structures::animal_clip_walk], set[structures::animal_clip_trot], set[structures::animal_clip_run] };
			const auto speed{ std::clamp(animal.shown_speed, speeds[0], speeds[2]) };
			const auto upper{ speed > speeds[1] ? 2u : 1u };
			const auto weight{ mathematics.saturate((speed - speeds[upper - 1u]) / std::max(speeds[upper] - speeds[upper - 1u], 0.01f)) };
			const auto low_duration{ gaits[upper - 1u] < characters.clips.size() ? characters.clips[gaits[upper - 1u]].header.duration : 1.0f };
			const auto high_duration{ gaits[upper] < characters.clips.size() ? characters.clips[gaits[upper]].header.duration : 1.0f };

			characters.sample(character, gaits[upper - 1u], animal.phase * low_duration, pose);
			characters.sample(character, gaits[upper], animal.phase * high_duration, scratch);
			characters.blend(character, pose, scratch, weight, pose);
		}

		else
		{
			const auto clip{ set[std::min(mode, static_cast<std::uint32_t>(structures::animal_clip_count) - 1u)] };
			const auto duration{ clip < characters.clips.size() ? std::max(characters.clips[clip].header.duration, 0.01f) : 1.0f };

			characters.sample(character, clip, mode == structures::animal_clip_death ? std::min(time, duration) : std::fmod(time, duration), pose);
		}
	}
	/*
	//=====================================================================================
	*/
	void fauna_c::submit()
	{
		for (const auto& animal : animals)
		{
			if (animal.frames && (animal.alive || animal.yields) && bodies[animal.species])
			{
				const auto range{ mathematics.distance(animal.shown, renderer.camera.position) };
				const auto* character{ range > fauna_lod_distance && distant[animal.species] ? distant[animal.species] : bodies[animal.species] };

				renderer.submit_skinned(character, animal.world, animal.previous_world, animal.palette.data(), animal.previous_palette.data(), structures::draw_flag_character, 0.0f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t fauna_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
