
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	wildlife_c wildlife;

	void wildlife_c::create()
	{
		for (auto kind{ 0u }; kind < structures::wildlife_kind_count; kind++)
		{
			const auto shape{ models.find(wildlife_kinds[kind].model) };

			shapes[kind] = shape && models.upload(*shape) ? shape : nullptr;
		}
	}
	/*
	//=====================================================================================
	*/
	void wildlife_c::populate()
	{
		flocks.clear();
		creatures.clear();

		for (auto kind{ 0u }; terrain.enabled && kind < structures::wildlife_kind_count; kind++)
		{
			const auto& type{ wildlife_kinds[kind] };

			for (auto group{ 0u }; shapes[kind] && group < type.groups; group++)
			{
				if (structures::vec3_s point{}; home(kind, point))
				{
					const auto room{ wildlife_maximum - std::min(static_cast<std::uint32_t>(creatures.size()), wildlife_maximum) };
					const auto count{ std::min({ type.minimum + static_cast<std::uint32_t>(random() * static_cast<std::float_t>(type.maximum - type.minimum + 1u)), type.maximum, room }) };
					const auto turn{ random() < 0.5f ? 1.0f : -1.0f };

					flocks.push_back({ point, point, { 0.0f, 0.0f, 1.0f }, random() * 1000.0f, 0.0f, 0.0f, kind, static_cast<std::uint32_t>(creatures.size()), count });

					for (auto member{ 0u }; member < count; member++)
					{
						structures::creature_s creature{};

						creature.position = point;
						creature.offset = { (random() * 2.0f - 1.0f) * type.radius, (random() * 2.0f - 1.0f) * type.spread, (random() * 2.0f - 1.0f) * type.radius };
						creature.heading = { 0.0f, 0.0f, 1.0f };
						creature.angle = random() * two_pi;
						creature.radius = type.radius * (0.5f + random());
						creature.phase = random() * two_pi;
						creature.bob = random() * two_pi;
						creature.flap = 1.0f;
						creature.beat = 1.0f;
						creature.timer = random() * 4.0f;
						creature.turn = turn;

						creatures.push_back(creature);
					}
				}
			}
		}

		logger.write("wildlife: %zu creatures in %zu flocks and schools", creatures.size(), flocks.size());
	}
	/*
	//=====================================================================================
	*/
	bool wildlife_c::home(std::uint32_t kind, structures::vec3_s& point)
	{
		const auto& type{ wildlife_kinds[kind] };
		const auto swimming{ type.motion == structures::creature_swim };

		for (auto attempt{ 0u }; attempt < 300u; attempt++)
		{
			const auto x{ terrain_origin + 60.0f + random() * (terrain_size - 120.0f) };
			const auto z{ terrain_origin + 60.0f + random() * (terrain_size - 120.0f) };
			const auto ground{ terrain.height(x, z) };
			const auto depth{ sea_level - ground };

			if ((type.habitat & (1u << terrain.biome(x, z))) != 0u && (swimming ? depth > type.floor_low && depth < type.floor_high : ground > sea_level - 1.0f))
			{
				point = { x, swimming ? sea_level - type.height : std::max(ground, sea_level), z };

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s wildlife_c::anchor(const structures::flock_s& flock) const
	{
		const auto& type{ wildlife_kinds[flock.kind] };

		return flock.home + structures::vec3_s{ std::sin(flock.drift * 0.031f) * type.roam, type.motion == structures::creature_swim ? std::sin(flock.drift * 0.05f) * 0.8f : 0.0f, std::cos(flock.drift * 0.023f) * type.roam };
	}
	/*
	//=====================================================================================
	*/
	void wildlife_c::update(std::float_t delta, structures::vec3_s viewer)
	{
		for (auto& flock : flocks)
		{
			const auto& type{ wildlife_kinds[flock.kind] };
			const auto swimming{ type.motion == structures::creature_swim };
			const auto range{ swimming ? wildlife_fish_range : wildlife_bird_range };
			const auto previous{ flock.center };

			flock.startle = std::max(flock.startle - delta, 0.0f);
			flock.lift = mathematics.damp(flock.lift, flock.startle > 0.0f ? wildlife_startle_lift : 0.0f, 0.6f, delta);

			if (mathematics.distance(flock.home, viewer) < range + wildlife_active_margin + type.roam)
			{
				flock.drift += delta * (swimming ? type.speed : 1.0f) * (flock.startle > 0.0f ? 2.0f : 1.0f);
				flock.center = anchor(flock);
				flock.heading = mathematics.distance(previous, flock.center) > 0.0001f ? mathematics.normalize(flock.center - previous) : flock.heading;

				for (auto member{ flock.first }; member < flock.first + flock.count; member++)
				{
					auto& creature{ creatures[member] };

					if (swimming)
					{
						swim(flock, creature, delta, viewer);
					}

					else
					{
						fly(flock, creature, delta);
					}

					creature.drawn = mathematics.distance(creature.position, viewer) < range;
				}
			}

			else
			{
				for (auto member{ flock.first }; member < flock.first + flock.count; member++)
				{
					creatures[member].drawn = false;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void wildlife_c::fly(structures::flock_s& flock, structures::creature_s& creature, std::float_t delta)
	{
		const auto& type{ wildlife_kinds[flock.kind] };
		const auto hurry{ flock.startle > 0.0f ? 1.7f : 1.0f };
		const auto previous{ creature.position };
		const auto ground{ std::max(terrain.height(previous.x, previous.z), sea_level) };
		const auto base{ std::max(flock.home.y + type.height, ground + wildlife_ground_clearance) };

		creature.angle += type.speed * hurry / std::max(creature.radius, 1.0f) * creature.turn * delta;
		creature.bob += delta * 0.4f;
		creature.timer -= delta;

		if (creature.timer <= 0.0f)
		{
			creature.beat = creature.beat > 0.5f && random() < type.glide ? 0.0f : 1.0f;
			creature.timer = creature.beat > 0.5f ? 1.2f + random() * 2.5f : 2.0f + random() * 4.0f;
		}

		creature.flap = mathematics.damp(creature.flap, flock.startle > 0.0f ? 1.0f : creature.beat, 3.0f, delta);
		creature.phase += two_pi * type.beat * (0.8f + 0.2f * hurry) * delta;
		creature.phase -= std::floor(creature.phase / two_pi) * two_pi;
		creature.position = flock.center + structures::vec3_s{ std::sin(creature.angle) * creature.radius, 0.0f, std::cos(creature.angle) * creature.radius };
		creature.position.y = base + flock.lift + creature.offset.y + std::sin(creature.bob) * type.spread * 0.5f;
		creature.bank = mathematics.damp(creature.bank, creature.turn * std::min(type.speed * hurry * type.speed * hurry / (9.81f * std::max(creature.radius, 1.0f)), 0.7f), 2.0f, delta);

		place(creature, creature.position - previous, creature.bank, creature.drawn);
	}
	/*
	//=====================================================================================
	*/
	void wildlife_c::swim(structures::flock_s& flock, structures::creature_s& creature, std::float_t delta, structures::vec3_s viewer)
	{
		const auto& type{ wildlife_kinds[flock.kind] };
		const auto previous{ creature.position };
		const auto gap{ mathematics.distance(previous, viewer) };
		const auto away{ gap > 0.01f ? (previous - viewer) / gap : structures::vec3_s{} };

		creature.scare = mathematics.damp(creature.scare, gap < wildlife_fish_scare ? 1.0f : 0.0f, gap < wildlife_fish_scare ? 6.0f : 0.8f, delta);
		creature.bob += delta * (0.7f + creature.scare);
		creature.phase += two_pi * type.beat * (1.0f + creature.scare * 1.5f) * delta;
		creature.phase -= std::floor(creature.phase / two_pi) * two_pi;

		const auto wobble{ structures::vec3_s{ std::sin(creature.bob * 1.3f + creature.angle), std::sin(creature.bob * 0.9f) * 0.3f, std::cos(creature.bob * 1.1f + creature.angle) } * 0.4f };
		const auto target{ flock.center + creature.offset + wobble + away * (creature.scare * 3.0f) };
		const auto bed{ terrain.height(target.x, target.z) + wildlife_bed_clearance };

		creature.position = mathematics.lerp(previous, { target.x, std::min(std::max(target.y, bed), sea_level - wildlife_surface_clearance), target.z }, mathematics.saturate(delta * (1.5f + creature.scare * 4.0f)));

		const auto moved{ creature.position - previous };
		const auto own{ mathematics.length(moved) > 0.0005f ? mathematics.normalize(structures::vec3_s{ moved.x, moved.y * 0.3f, moved.z }) : flock.heading };
		const auto steer{ mathematics.normalize(flock.heading * 1.5f + own + away * (creature.scare * 3.0f)) };

		creature.heading = mathematics.normalize(mathematics.lerp(creature.heading, steer, mathematics.saturate(delta * 3.0f)));

		place(creature, creature.heading, 0.0f, creature.drawn);
	}
	/*
	//=====================================================================================
	*/
	void wildlife_c::place(structures::creature_s& creature, structures::vec3_s heading, std::float_t bank, bool shown)
	{
		const auto forward{ mathematics.length(heading) > 0.0001f ? mathematics.normalize(heading) : structures::vec3_s{ 0.0f, 0.0f, 1.0f } };
		const auto level{ mathematics.normalize(mathematics.cross({ 0.0f, 1.0f, 0.0f }, forward)) };
		const auto lifted{ mathematics.cross(forward, level) };
		const auto right{ level * std::cos(bank) - lifted * std::sin(bank) };
		const auto placement{ mathematics.basis(right, mathematics.cross(forward, right), forward, creature.position) };

		creature.previous_world = shown ? creature.world : placement;
		creature.world = placement;
	}
	/*
	//=====================================================================================
	*/
	void wildlife_c::startle(structures::vec3_s origin, std::float_t loudness)
	{
		for (auto& flock : flocks)
		{
			if (wildlife_kinds[flock.kind].motion == structures::creature_flap && mathematics.distance(flock.center, origin) < wildlife_startle_range * loudness)
			{
				flock.startle = wildlife_startle_time;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void wildlife_c::submit()
	{
		for (const auto& flock : flocks)
		{
			const auto& type{ wildlife_kinds[flock.kind] };

			for (auto member{ flock.first }; shapes[flock.kind] && member < flock.first + flock.count; member++)
			{
				if (const auto& creature{ creatures[member] }; creature.drawn)
				{
					renderer.submit(&shapes[flock.kind]->mesh, creature.world, creature.previous_world, -1.0f, type.motion == structures::creature_swim ? static_cast<std::uint32_t>(structures::draw_flag_no_shadow) : 0u, { static_cast<std::float_t>(type.motion), creature.phase, type.amplitude * (type.motion == structures::creature_flap ? 0.12f + 0.88f * creature.flap : 1.0f + creature.scare), type.span });
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t wildlife_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
