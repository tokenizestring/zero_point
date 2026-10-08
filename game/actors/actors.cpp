
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	actors_c actors;

	bool actors_c::create()
	{
		const char* names[5] = { clip_idle, clip_walk, clip_run, clip_sprint, clip_crouch };

		list.reserve(maximum_actors);

		for (auto index{ 0u }; index < 5u; index++)
		{
			clips[index] = characters.clip(names[index]);
		}

		for (auto index{ 1u }; index < 4u; index++)
		{
			const auto measured{ clips[index] < characters.clips.size() ? mathematics.length(characters.clips[clips[index]].header.root_velocity) : 0.0f };

			speeds[index] = std::max(measured, speeds[index - 1u] + 0.75f);
		}

		logger.write("actors: locomotion speeds walk %.2f run %.2f sprint %.2f m/s", speeds[1], speeds[2], speeds[3]);

		clothed = characters.find(remote_character);
		bare = clothed ? characters.find(nude_character) : nullptr;

		return std::all_of(std::begin(clips), std::end(clips), [](std::uint32_t clip_index) { return clip_index < characters.clips.size(); });
	}
	/*
	//=====================================================================================
	*/
	void actors_c::clear()
	{
		list.clear();
	}
	/*
	//=====================================================================================
	*/
	const char* actors_c::survivor() const
	{
		return bare && censored == false ? nude_character : (clothed ? remote_character : viewmodel_character);
	}
	/*
	//=====================================================================================
	*/
	void actors_c::dress(bool censor)
	{
		censored = censor;

		if (const auto body{ bare && censored == false ? bare : clothed }; body)
		{
			for (auto& actor : list)
			{
				if ((actor.behavior == structures::actor_behavior_player || actor.behavior == structures::actor_behavior_remote || actor.behavior == structures::actor_behavior_corpse) && (actor.character == bare || actor.character == clothed))
				{
					actor.character = body;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::actor_s* actors_c::spawn(const char* character_name, structures::vec3_s position, std::float_t yaw, std::uint32_t behavior)
	{
		if (const auto character{ characters.find(character_name) }; character && list.size() < maximum_actors)
		{
			structures::actor_s actor{};

			actor.character = character;
			actor.position = position;
			actor.home = position;
			actor.target = position;
			actor.look_yaw = yaw;
			actor.body_yaw = yaw;
			actor.behavior = behavior;
			actor.seed = mathematics.hash_u32(static_cast<std::uint32_t>(list.size()) * 7919u + 17u);
			actor.direction = 1.0f;
			actor.grounded = true;
			actor.world = mathematics.identity();
			actor.previous_world = mathematics.identity();
			actor.palette.resize(character->bones.size());
			actor.previous_palette.resize(character->bones.size());
			actor.health = hostile_health;
			actor.pallor = behavior == structures::actor_behavior_hostile ? hostile_pallor : 0.0f;

			for (auto index{ 0u }; index < structures::actor_rig_count; index++)
			{
				actor.rig[index] = characters.bone(*character, actor_rig_bones[index]);
			}

			if (behavior == structures::actor_behavior_player)
			{
				mask(actor);
			}

			list.push_back(std::move(actor));

			return &list.back();
		}

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	void actors_c::mask(structures::actor_s& actor)
	{
		const auto& character{ *actor.character };

		actor.view_world = mathematics.identity();
		actor.previous_view_world = mathematics.identity();
		actor.view_palette.resize(character.bones.size());
		actor.previous_view_palette.resize(character.bones.size());
		actor.collapse.assign(character.bones.size(), -1);

		for (const auto hidden : first_person_hidden_bones)
		{
			if (const auto root{ characters.bone(character, hidden) }; root >= 0)
			{
				for (auto index{ 0u }; index < character.bones.size(); index++)
				{
					for (auto walk{ static_cast<std::int32_t>(index) }; walk >= 0 && actor.collapse[index] < 0; walk = character.bones[walk].parent)
					{
						actor.collapse[index] = walk == root ? root : -1;
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void actors_c::update(std::float_t delta)
	{
		for (auto& actor : list)
		{
			actor.previous_world = actor.world;
			actor.previous_view_world = actor.view_world;
			actor.previous_held_world = actor.held_world;

			std::swap(actor.palette, actor.previous_palette);
			std::swap(actor.view_palette, actor.previous_view_palette);

			actor.dormant = actor.behavior == structures::actor_behavior_hostile && mathematics.distance(actor.position, passive ? focus : player.state.position) > hostile_active_range;

			if (actor.dormant)
			{
				actor.frames = 0u;
			}

			else if (actor.hidden == false || (actor.behavior != structures::actor_behavior_remote && actor.behavior != structures::actor_behavior_corpse))
			{
				if (actor.behavior == structures::actor_behavior_wander)
				{
					think(actor, delta);

					steer(actor, delta);
				}

				else if (actor.behavior == structures::actor_behavior_hostile)
				{
					hunt(actor, delta);

					if (actor.dead == false)
					{
						steer(actor, delta);
					}
				}

				else if (actor.behavior == structures::actor_behavior_corpse)
				{
					actor.death = std::min(actor.death + delta, 4.0f);
				}

				animate(actor, delta);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void actors_c::hunt(structures::actor_s& actor, std::float_t delta)
	{
		const structures::vec3_s offset{ player.state.position.x - actor.position.x, 0.0f, player.state.position.z - actor.position.z };
		const auto distance{ mathematics.length(offset) };

		actor.clock += delta;
		actor.hurt = std::max(0.0f, actor.hurt - delta * 2.2f);

		if (actor.dead)
		{
			actor.death += delta;
			actor.velocity = {};

			if (actor.death > corpse_time && distance > 60.0f)
			{
				recycle(actor, player.state.position, 90.0f, 700.0f);
			}
		}

		else
		{
			actor.sight_timer -= delta;

			if (actor.alerted == false && actor.sight_timer <= 0.0f && survival.vitals.dead == false && passive == false)
			{
				actor.sight_timer = 0.25f + random(actor) * 0.15f;

				if (distance < hostile_hearing || (distance < hostile_sight && mathematics.dot(mathematics.flat_forward(actor.look_yaw), offset / std::max(distance, 0.01f)) > -0.2f && sees_player(actor)))
				{
					actor.alerted = true;
					actor.forget_timer = 0.0f;
					actor.voice_timer = 2.0f + random(actor) * 3.0f;

					mixer.play(structures::sound_zombie_snarl, actor.position + structures::vec3_s{ 0.0f, 1.6f, 0.0f }, 1.0f, 0.85f + random(actor) * 0.25f);
				}
			}

			if (actor.alerted && (distance > hostile_forget || survival.vitals.dead || passive))
			{
				actor.alerted = false;
				actor.home = actor.position;
				actor.timer = 0.0f;
				actor.attack = 0.0f;
			}

			if (actor.alerted)
			{
				actor.target = player.state.position;
				actor.crouched = false;
				actor.look_pitch = mathematics.damp(actor.look_pitch, -0.28f, 4.0f, delta);
				actor.desired_speed = distance > hostile_attack_range ? (distance > 9.0f ? speeds[3] * 0.9f : speeds[2]) * (0.9f + 0.2f * mathematics.hash_float(actor.seed)) * (1.0f - actor.hurt * 0.6f) : 0.0f;

				if (distance < 3.0f)
				{
					actor.look_yaw += mathematics.angle_difference(actor.look_yaw, std::atan2(offset.x, offset.z)) * (1.0f - std::exp(-8.0f * delta));
				}

				strike(actor, distance, delta);
			}

			else
			{
				actor.look_pitch = mathematics.damp(actor.look_pitch, -0.12f, 2.0f, delta);

				think(actor, delta);
			}

			actor.voice_timer -= delta;

			if (actor.voice_timer <= 0.0f)
			{
				actor.voice_timer = actor.alerted ? 3.0f + random(actor) * 4.0f : 9.0f + random(actor) * 16.0f;

				if (actor.alerted || distance < 45.0f)
				{
					mixer.play(actor.alerted ? structures::sound_zombie_groan : (random(actor) < 0.5f ? structures::sound_ghost_moan : structures::sound_zombie_groan), actor.position + structures::vec3_s{ 0.0f, 1.6f, 0.0f }, actor.alerted ? 0.9f : 0.55f, 0.82f + random(actor) * 0.3f);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void actors_c::strike(structures::actor_s& actor, std::float_t distance, std::float_t delta)
	{
		const auto chest{ actor.position + structures::vec3_s{ 0.0f, 1.3f, 0.0f } };
		const auto reachable{ distance < hostile_attack_reach && std::fabs(player.state.position.y - actor.position.y) < 1.6f && world.trace(chest, player.eye - structures::vec3_s{ 0.0f, 0.3f, 0.0f }, { 0.02f, 0.02f, 0.02f }, structures::contents_solid).fraction >= 0.98f };
		const auto siege{ reachable == false && actor.blocker >= 0 && building.by_brush.find(actor.blocker) != building.by_brush.end() && distance < 16.0f };

		actor.attack_timer -= delta;

		if (actor.attack > 0.0f)
		{
			actor.attack += delta / hostile_attack_time;

			if (actor.struck == false && actor.attack >= 0.45f)
			{
				actor.struck = true;

				if (reachable && survival.vitals.dead == false)
				{
					survival.damage(hostile_attack_damage * (0.85f + 0.3f * random(actor)));

					player.landing_velocity -= 2.5f;

					mixer.play_2d(structures::sound_player_hurt, 0.9f, 0.85f + random(actor) * 0.2f);
				}

				else if (siege)
				{
					building.damage(actor.blocker, hostile_structure_damage * (0.8f + 0.4f * random(actor)), false);
				}
			}

			actor.attack = actor.attack >= 1.0f ? 0.0f : actor.attack;
		}

		else if (actor.attack_timer <= 0.0f && ((reachable && distance < hostile_attack_range + 0.35f) || siege) && actor.hurt < 0.5f)
		{
			actor.attack = 0.001f;
			actor.struck = false;
			actor.attack_timer = hostile_attack_cooldown + random(actor) * 0.6f;

			mixer.play(structures::sound_zombie_snarl, actor.position + structures::vec3_s{ 0.0f, 1.6f, 0.0f }, 1.0f, 0.9f + random(actor) * 0.2f);
		}
	}
	/*
	//=====================================================================================
	*/
	bool actors_c::sees_player(const structures::actor_s& actor)
	{
		return world.trace(actor.position + structures::vec3_s{ 0.0f, 1.6f, 0.0f }, player.eye, { 0.02f, 0.02f, 0.02f }, structures::contents_solid).fraction >= 0.999f;
	}
	/*
	//=====================================================================================
	*/
	void actors_c::damage(structures::actor_s& actor, std::float_t amount, structures::vec3_s direction)
	{
		if (actor.dead == false)
		{
			actor.health -= amount;
			actor.hurt = 1.0f;
			actor.alerted = true;
			actor.attack = actor.attack < 0.25f ? 0.0f : actor.attack;
			actor.velocity += structures::vec3_s{ direction.x, 0.0f, direction.z } * 2.2f;

			if (actor.health <= 0.0f)
			{
				actor.dead = true;
				actor.death = 0.0f;
				actor.attack = 0.0f;
				actor.looted = false;
				actor.fall_roll = (random(actor) - 0.5f) * 0.5f;
				actor.velocity = {};
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool actors_c::recycle(structures::actor_s& actor, structures::vec3_s origin, std::float_t minimum_distance, std::float_t maximum_distance)
	{
		for (auto attempt{ 0u }; attempt < 96u; attempt++)
		{
			const auto angle{ random(actor) * two_pi };
			const auto radius{ minimum_distance + random(actor) * (maximum_distance - minimum_distance) };
			const auto x{ origin.x + std::sin(angle) * radius };
			const auto z{ origin.z + std::cos(angle) * radius };

			if (std::fabs(x) < terrain_size * 0.48f && std::fabs(z) < terrain_size * 0.48f && terrain.height(x, z) > 2.5f && terrain.normal(x, z).y > 0.8f && world.box_solid({ x, terrain.height(x, z) + 1.0f, z }, { 0.3f, 0.8f, 0.3f }, structures::contents_solid) == false)
			{
				actor.position = { x, terrain.height(x, z), z };
				actor.home = actor.position;
				actor.target = actor.position;
				actor.velocity = {};
				actor.health = hostile_health;
				actor.dead = false;
				actor.alerted = false;
				actor.looted = false;
				actor.death = 0.0f;
				actor.attack = 0.0f;
				actor.hurt = 0.0f;
				actor.timer = 0.0f;
				actor.frames = 0u;
				actor.look_yaw = random(actor) * two_pi;
				actor.body_yaw = actor.look_yaw;

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void actors_c::think(structures::actor_s& actor, std::float_t delta)
	{
		const auto remaining{ mathematics.length(structures::vec3_s{ actor.target.x - actor.position.x, 0.0f, actor.target.z - actor.position.z }) };

		actor.timer -= delta;

		if (actor.timer <= 0.0f || (actor.desired_speed > 0.0f && remaining < 0.6f))
		{
			if (random(actor) < 0.3f)
			{
				actor.desired_speed = 0.0f;
				actor.crouched = random(actor) < 0.25f;
				actor.timer = 2.0f + random(actor) * 4.0f;
				actor.look_yaw += (random(actor) - 0.5f) * 2.0f;
			}

			else
			{
				const auto angle{ random(actor) * two_pi };
				const auto radius{ 3.0f + random(actor) * 9.0f };
				const auto pace{ random(actor) };

				actor.target = actor.home + structures::vec3_s{ std::sin(angle) * radius, 0.0f, std::cos(angle) * radius };
				actor.crouched = pace < 0.12f;
				actor.desired_speed = actor.crouched ? speeds[1] * 0.8f : (pace < 0.55f ? speeds[1] * 1.1f : (pace < 0.85f ? speeds[2] : speeds[3]));
				actor.timer = 14.0f;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void actors_c::steer(structures::actor_s& actor, std::float_t delta)
	{
		const structures::vec3_s offset{ actor.target.x - actor.position.x, 0.0f, actor.target.z - actor.position.z };
		const auto chest{ actor.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f } };

		const auto base{ mathematics.length(offset) > 0.3f && actor.desired_speed > 0.0f ? mathematics.normalize(offset) : structures::vec3_s{} };

		auto direction{ base };

		for (auto attempt{ 0u }; attempt < std::size(actor_avoid_angles) && actor.behavior == structures::actor_behavior_hostile && mathematics.length(direction) > 0.5f && world.trace(chest, chest + direction * 0.9f, { 0.22f, 0.3f, 0.22f }, structures::contents_solid).hit; attempt++)
		{
			direction = mathematics.quat_rotate(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, actor_avoid_angles[attempt]), base);
		}

		const auto desired{ direction * actor.desired_speed };

		actor.velocity = mathematics.damp(actor.velocity, desired, 4.0f, delta);

		const auto stride{ actor.velocity * delta };
		const auto blocked{ actor.behavior == structures::actor_behavior_hostile ? world.trace(chest, chest + stride, { 0.26f, 0.5f, 0.26f }, structures::contents_solid) : structures::trace_s{ 1.0f } };

		const auto travel{ blocked.hit && blocked.start_solid == false ? std::max(blocked.fraction - 0.05f, 0.0f) : 1.0f };

		actor.blocker = blocked.hit && blocked.start_solid == false ? blocked.brush : -1;
		actor.position += stride * travel;
		actor.velocity = travel < 1.0f ? actor.velocity * travel : actor.velocity;
		actor.position.y = terrain.enabled ? terrain.height(actor.position.x, actor.position.z) : actor.position.y;

		if (mathematics.length(actor.velocity) > 0.3f)
		{
			actor.look_yaw += mathematics.angle_difference(actor.look_yaw, std::atan2(actor.velocity.x, actor.velocity.z)) * (1.0f - std::exp(-5.0f * delta));
		}
	}
	/*
	//=====================================================================================
	*/
	void actors_c::animate(structures::actor_s& actor, std::float_t delta)
	{
		const auto& character{ *actor.character };
		const structures::vec3_s horizontal{ actor.seated ? 0.0f : actor.velocity.x, 0.0f, actor.seated ? 0.0f : actor.velocity.z };
		const auto speed{ mathematics.length(horizontal) };

		actor.speed = mathematics.damp(actor.speed, speed, character_blend_sharpness, delta);
		actor.crouch = mathematics.damp(actor.crouch, actor.crouched && actor.seated == false ? 1.0f : 0.0f, 8.0f, delta);
		actor.air = mathematics.damp(actor.air, actor.grounded || actor.seated ? 0.0f : 1.0f, 10.0f, delta);

		if (actor.seated)
		{
			actor.turning = false;
		}

		else if (speed > 0.25f)
		{
			const auto move_yaw{ std::atan2(horizontal.x, horizontal.z) };
			const auto backwards{ std::fabs(mathematics.angle_difference(actor.look_yaw, move_yaw)) > character_backpedal_angle };
			const auto legs{ std::clamp(mathematics.angle_difference(actor.look_yaw, backwards ? move_yaw + pi : move_yaw), -character_strafe_limit, character_strafe_limit) };

			actor.body_yaw += mathematics.angle_difference(actor.body_yaw, actor.look_yaw + legs) * (1.0f - std::exp(-character_turn_rate * delta));
			actor.direction = mathematics.damp(actor.direction, backwards ? -1.0f : 1.0f, 8.0f, delta);
			actor.turning = false;
		}

		else
		{
			const auto deviation{ mathematics.angle_difference(actor.body_yaw, actor.look_yaw) };

			actor.turning = actor.turning ? std::fabs(deviation) > 0.05f : std::fabs(deviation) > character_turn_threshold;

			if (actor.turning)
			{
				actor.body_yaw += deviation * (1.0f - std::exp(-character_turn_rate * delta));
			}
		}

		const auto clamped{ std::min(actor.speed, speeds[3]) };

		auto segment{ 0u };

		while (segment < 2u && clamped > speeds[segment + 1u])
		{
			segment++;
		}

		const auto weight{ mathematics.saturate((clamped - speeds[segment]) / std::max(speeds[segment + 1u] - speeds[segment], 0.01f)) };
		const auto low{ std::max(segment, 1u) };
		const auto high{ segment ? segment + 1u : 1u };
		const auto cycle_weight{ segment ? weight : 0.0f };
		const auto& low_clip{ characters.clips[clips[low]] };
		const auto& high_clip{ characters.clips[clips[high]] };
		const auto& idle_clip{ characters.clips[clips[0]] };
		const auto& crouch_clip{ characters.clips[clips[4]] };
		const auto duration{ mathematics.lerp(low_clip.header.duration, high_clip.header.duration, cycle_weight) };
		const auto rate{ actor.speed / std::max(mathematics.lerp(speeds[low], speeds[high], cycle_weight), 0.1f) };

		actor.phase += delta * rate / std::max(duration, 0.1f) * (actor.direction >= 0.0f ? 1.0f : -1.0f);
		actor.phase -= std::floor(actor.phase);
		actor.idle_time = actor.dead ? actor.idle_time : std::fmod(actor.idle_time + delta, std::max(idle_clip.header.duration, 0.1f));
		actor.arms = mathematics.damp(actor.arms, actor.alerted && actor.dead == false ? 1.0f : 0.0f, 5.0f, delta);

		characters.sample(character, clips[low], actor.phase * low_clip.header.duration, locomotion);

		if (high != low)
		{
			characters.sample(character, clips[high], actor.phase * high_clip.header.duration, secondary);

			characters.blend(character, locomotion, secondary, cycle_weight, locomotion);
		}

		if (segment == 0u)
		{
			characters.sample(character, clips[0], actor.idle_time, secondary);

			characters.blend(character, secondary, locomotion, weight, locomotion);
		}

		if (actor.crouch > 0.01f || actor.air > 0.01f)
		{
			characters.sample(character, clips[0], 0.0f, reference);

			characters.sample(character, clips[4], std::fmod(actor.idle_time, std::max(crouch_clip.header.duration, 0.1f)), crouching);
		}

		if (actor.crouch > 0.01f)
		{
			characters.add(character, locomotion, reference, crouching, actor.crouch, locomotion);
		}

		if (actor.air > 0.01f)
		{
			characters.sample(character, clips[2], actor_air_phase * characters.clips[clips[2]].header.duration, airborne);

			characters.add(character, airborne, reference, crouching, actor_air_crouch, airborne);

			characters.blend(character, locomotion, airborne, actor.air, locomotion);
		}

		if (actor.behavior == structures::actor_behavior_hostile && actor.arms > 0.01f)
		{
			pose_arms(actor);
		}

		const auto was_holding{ actor.holding };

		actor.holding = actor.held && actor.dead == false && actor.seated == false && hold(actor);

		const auto twist_yaw{ std::clamp(mathematics.angle_difference(actor.body_yaw, actor.look_yaw), -actor_twist_yaw_limit, actor_twist_yaw_limit) };
		const auto twist_pitch{ std::clamp(actor.look_pitch + actor.hurt * 0.4f, -actor_twist_pitch_limit, actor_twist_pitch_limit) };
		const auto fallen{ actor.dead ? std::min(1.0f, actor.death * actor.death * 2.6f) : 0.0f };

		characters.palette(character, locomotion, twist_yaw, twist_pitch, actor.palette.data(), actor.holding ? actor.blade : 0.0f, actor.seated ? 1.0f : 0.0f);

		if (actor.holding)
		{
			actor.held_world = mathematics.multiply(actor.held_offset, characters.globals[actor.held_bone]);
		}

		if (actor.collapse.size())
		{
			characters.palette(character, locomotion, twist_yaw, 0.0f, actor.view_palette.data());

			for (auto bone{ 0u }; bone < actor.collapse.size(); bone++)
			{
				if (actor.collapse[bone] >= 0)
				{
					actor.view_palette[bone] = mathematics.multiply(mathematics.scaling({ first_person_collapse, first_person_collapse, first_person_collapse }), mathematics.translation(characters.globals[actor.collapse[bone]].row3(3u)));
				}
			}
		}

		actor.world = mathematics.multiply(mathematics.multiply(mathematics.rotation_x(fallen * half_pi * 0.97f), mathematics.rotation_z(fallen * actor.fall_roll)), mathematics.multiply(mathematics.rotation_y(actor.body_yaw + character_facing_offset), mathematics.translation(actor.position + structures::vec3_s{ 0.0f, fallen * 0.11f, 0.0f })));
		actor.view_world = mathematics.multiply(actor.world, mathematics.translation(mathematics.flat_forward(actor.look_yaw) * -first_person_body_back));

		if (actor.holding)
		{
			actor.held_world = mathematics.multiply(actor.held_world, actor.world);
		}

		if (actor.frames == 0u)
		{
			actor.previous_world = actor.world;
			actor.previous_palette = actor.palette;
			actor.previous_view_world = actor.view_world;
			actor.previous_view_palette = actor.view_palette;
		}

		if (actor.frames == 0u || was_holding == false)
		{
			actor.previous_held_world = actor.held_world;
		}

		actor.frames++;
	}
	/*
	//=====================================================================================
	*/
	void actors_c::pose_arms(structures::actor_s& actor)
	{
		const auto sway{ std::sin(actor.clock * 6.5f + mathematics.hash_float(actor.seed) * 6.0f) };
		const auto raise{ mathematics.smoothstep(0.0f, 0.35f, actor.attack) * (1.0f - mathematics.smoothstep(0.35f, 0.55f, actor.attack)) };
		const auto slash{ mathematics.smoothstep(0.35f, 0.55f, actor.attack) * (1.0f - mathematics.smoothstep(0.62f, 1.0f, actor.attack)) };
		const structures::vec3_s reach_right{ -0.2f, 1.52f + sway * 0.04f, -0.58f };
		const structures::vec3_s reach_left{ 0.21f, 1.54f - sway * 0.04f, -0.55f };
		const auto right{ reach_right + (structures::vec3_s{ -0.34f, 1.86f, -0.12f } - reach_right) * raise + (structures::vec3_s{ 0.12f, 1.02f, -0.66f } - reach_right) * slash };

		characters.reach(*actor.character, locomotion, actor.rig[structures::actor_rig_right_upper], actor.rig[structures::actor_rig_right_lower], actor.rig[structures::actor_rig_right_hand], right, { -1.0f, -0.5f, 0.35f }, actor.arms * 0.96f);
		characters.reach(*actor.character, locomotion, actor.rig[structures::actor_rig_left_upper], actor.rig[structures::actor_rig_left_lower], actor.rig[structures::actor_rig_left_hand], reach_left, { 1.0f, -0.5f, 0.35f }, actor.arms * 0.93f);
	}
	/*
	//=====================================================================================
	*/
	bool actors_c::hold(structures::actor_s& actor)
	{
		const auto weapon{ item_definitions[actor.held].weapon };
		const auto style{ weapon == structures::weapon_rifle || weapon == structures::weapon_assault ? structures::hold_long : (weapon == structures::weapon_pistol ? structures::hold_pistol : (weapon == structures::weapon_bow ? structures::hold_bow : structures::hold_tool)) };
		const auto& pose{ hold_poses[style] };
		const auto& gun{ gun_models[weapon] };
		const structures::vec3_s forward{ std::sin(pose.blade) * std::cos(pose.pitch), std::sin(pose.pitch), -std::cos(pose.blade) * std::cos(pose.pitch) };
		const structures::vec3_s up{ -std::sin(pose.blade) * std::sin(pose.pitch), std::cos(pose.pitch), std::cos(pose.blade) * std::sin(pose.pitch) };
		const structures::vec3_s outward{ -1.0f, 0.0f, 0.0f };
		const auto aligned{ mathematics.basis(forward, up, mathematics.cross(forward, up), pose.anchor) };
		const auto frame{ style == structures::hold_tool ? mathematics.basis(outward, forward, mathematics.cross(outward, forward), pose.anchor) : mathematics.multiply(mathematics.rotation_z(-gun.tilt), aligned) };
		const auto holder{ actor.rig[pose.left ? structures::actor_rig_left_hand : structures::actor_rig_right_hand] };

		if (viewmodel.tools[actor.held].index_count && holder >= 0)
		{
			if (pose.left)
			{
				characters.reach(*actor.character, locomotion, actor.rig[structures::actor_rig_left_upper], actor.rig[structures::actor_rig_left_lower], holder, pose.anchor + pose.wrist, hold_left_pole, 1.0f);
			}

			else
			{
				characters.reach(*actor.character, locomotion, actor.rig[structures::actor_rig_right_upper], actor.rig[structures::actor_rig_right_lower], holder, pose.anchor + pose.wrist, hold_right_pole, 1.0f);
			}

			if (style == structures::hold_long || style == structures::hold_pistol)
			{
				const auto support{ style == structures::hold_long ? mathematics.transform_point(gun.support - gun.grip, aligned) + pose.support : pose.anchor + pose.support };

				characters.reach(*actor.character, locomotion, actor.rig[structures::actor_rig_left_upper], actor.rig[structures::actor_rig_left_lower], actor.rig[structures::actor_rig_left_hand], support, hold_left_pole, 1.0f);
			}

			characters.compute_globals(*actor.character, locomotion);

			actor.held_offset = mathematics.multiply(frame, mathematics.inverse(characters.globals[holder]));
			actor.held_bone = holder;
			actor.blade = pose.blade;

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void actors_c::submit()
	{
		for (const auto& actor : list)
		{
			if (actor.hidden == false && actor.dormant == false && actor.frames)
			{
				const auto masked{ actor.first_person && actor.collapse.size() };

				if (masked)
				{
					renderer.submit_skinned(actor.character, actor.view_world, actor.previous_view_world, actor.view_palette.data(), actor.previous_view_palette.data(), structures::draw_flag_character | structures::draw_flag_no_shadow, actor.pallor, first_person_clearance);
				}

				renderer.submit_skinned(actor.character, actor.world, actor.previous_world, actor.palette.data(), actor.previous_palette.data(), structures::draw_flag_character | (masked ? structures::draw_flag_shadow_only : 0u), actor.pallor);

				if (actor.holding)
				{
					renderer.submit(&viewmodel.tools[actor.held], actor.held_world, actor.previous_held_world, -1.0f, masked ? structures::draw_flag_shadow_only : 0u);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t actors_c::random(structures::actor_s& actor)
	{
		actor.seed ^= actor.seed << 13u;
		actor.seed ^= actor.seed >> 17u;
		actor.seed ^= actor.seed << 5u;

		return static_cast<std::float_t>(actor.seed & 0xFFFFFFu) / static_cast<std::float_t>(0x1000000u);
	}
}

//=====================================================================================
