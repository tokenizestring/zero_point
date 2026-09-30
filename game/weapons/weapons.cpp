
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	weapons_c weapons;

	void weapons_c::reset(std::uint32_t owner_seed)
	{
		state = {};
		state.seed = owner_seed;
		state.flags = structures::weapon_flag_cycled | structures::weapon_flag_worked;

		before = state;

		weapon = structures::weapon_none;
		reloading = 0.0f;
		clearing = 0.0f;
		cycle = 0.0f;
		draw = 0.0f;
		aim = 0.0f;
		kick = 0.0f;
		flash = 0.0f;
		view_pitch = 0.0f;
		view_yaw = 0.0f;
		jammed = false;
		cycled = true;
		scoped = false;
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::update(std::float_t delta, bool input_enabled)
	{
		const auto alpha{ std::clamp(player.accumulator / tick_interval, 0.0f, 1.0f) };
		const auto shaking{ drift(state, (static_cast<std::float_t>(player.sequence) + alpha) * tick_interval) };

		flash = std::max(0.0f, flash - delta);
		kick = mathematics.damp(kick, 0.0f, 10.0f, delta);
		aim = mathematics.lerp(before.aim, state.aim, alpha);
		draw = state.draw;
		scoped = weapon != structures::weapon_none && weapon_definitions[weapon].scope > 0.0f && aim > weapon_scope_threshold;
		view_pitch = mathematics.lerp(before.punch_pitch, state.punch_pitch, alpha) + shaking.y;
		view_yaw = mathematics.lerp(before.punch_yaw, state.punch_yaw, alpha) + shaking.x;

		renderer.zoom = scoped ? weapon_definitions[weapon].scope : mathematics.lerp(1.0f, weapon != structures::weapon_none ? weapon_definitions[weapon].zoom : 1.0f, std::max(aim, draw));

		if (weapon != structures::weapon_none && state.heat > weapon_smoke_heat && scoped == false && random() < delta * weapon_smoke_rate * state.heat)
		{
			particles.emit(structures::particle_smoke, muzzle, structures::vec3_s{ renderer.camera.right.y, renderer.camera.up.y, renderer.camera.forward.y } * weapon_smoke_rise, 0.03f, 1u, true);
		}

		if (jammed && clearing <= 0.0f && input_enabled)
		{
			hud.set_prompt("Jammed! Clear it   [R]");
		}
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::tick(const structures::usercmd_s& command, bool usable, bool moving)
	{
		before = state;

		step(state, survival, command, usable, moving);

		weapon = state.weapon;
		reloading = state.reloading;
		clearing = state.clearing;
		cycle = state.cycle;
		jammed = (state.flags & structures::weapon_flag_jammed) != 0u;
		cycled = (state.flags & structures::weapon_flag_cycled) != 0u;

		effects(command);
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::step(structures::weapon_state_s& weapon_state, survival_c& owner, const structures::usercmd_s& command, bool usable, bool moving)
	{
		const auto dt{ std::clamp(command.delta, 0.0f, 0.1f) };
		const auto slot{ std::min(command.weapon, hotbar_slots - 1u) };
		const auto fire_down{ (command.buttons & structures::button_fire) != 0u };
		const auto fire_pressed{ fire_down && (weapon_state.flags & structures::weapon_flag_fire_held) == 0u };
		const auto reload_pressed{ (command.buttons & structures::button_reload) != 0u && (weapon_state.flags & structures::weapon_flag_reload_held) == 0u };

		auto& held{ owner.slots[inventory_slots + slot] };

		const auto current{ item_definitions[held.item].weapon };

		weapon_state.events = 0u;
		weapon_state.rolls = 0u;

		if (current != weapon_state.weapon || slot != weapon_state.slot)
		{
			weapon_state.weapon = current;
			weapon_state.slot = slot;
			weapon_state.cooldown = weapon_equip_time;
			weapon_state.reloading = 0.0f;
			weapon_state.clearing = 0.0f;
			weapon_state.hangfire = 0.0f;
			weapon_state.heat = 0.0f;
			weapon_state.draw = 0.0f;
			weapon_state.burst = 0u;
			weapon_state.flags = (weapon_state.flags & (structures::weapon_flag_fire_held | structures::weapon_flag_reload_held)) | structures::weapon_flag_cycled | structures::weapon_flag_worked;
			weapon_state.events |= structures::weapon_event_equip;
		}

		const auto rise{ weapon_state.punch_rise * std::min(1.0f, dt * weapon_punch_rise) };

		weapon_state.cooldown = std::max(0.0f, weapon_state.cooldown - dt);
		weapon_state.heat = std::max(0.0f, weapon_state.heat - dt * weapon_heat_decay);
		weapon_state.since_shot += dt;
		weapon_state.burst = weapon_state.since_shot > weapon_burst_gap ? 0u : weapon_state.burst;
		weapon_state.punch_pitch += rise;
		weapon_state.punch_rise -= rise;

		if (weapon_state.since_shot > weapon_punch_hold)
		{
			const auto settle{ std::exp(-weapon_punch_recover * dt) };

			weapon_state.punch_pitch *= settle;
			weapon_state.punch_yaw *= settle;
		}

		if (weapon_state.weapon != structures::weapon_none && usable)
		{
			const auto& definition{ weapon_definitions[weapon_state.weapon] };
			const auto ready{ (weapon_state.flags & structures::weapon_flag_cycled) != 0u };
			const auto aiming{ (command.buttons & structures::button_aim) != 0u && weapon_state.reloading <= 0.0f && weapon_state.clearing <= 0.0f && ready };

			weapon_state.aim = mathematics.approach(weapon_state.aim, aiming ? 1.0f : 0.0f, dt * weapon_aim_rate);

			if (weapon_state.hangfire > 0.0f)
			{
				weapon_state.hangfire -= dt;

				if (weapon_state.hangfire <= 0.0f && held.loaded > 0u)
				{
					discharge(weapon_state, held, command, moving);
				}
			}

			else if (weapon_state.clearing > 0.0f)
			{
				weapon_state.clearing -= dt;

				if (weapon_state.clearing <= 0.0f)
				{
					weapon_state.flags &= ~structures::weapon_flag_jammed;
					weapon_state.events |= structures::weapon_event_cleared;

					held.loaded = held.loaded > 0u ? held.loaded - 1u : 0u;
				}
			}

			else if (weapon_state.reloading > 0.0f)
			{
				weapon_state.reloading -= dt;

				if (weapon_state.reloading <= 0.0f)
				{
					finish_reload(weapon_state, owner, held);
				}
			}

			else if (weapon_state.flags & structures::weapon_flag_jammed)
			{
				if (reload_pressed)
				{
					weapon_state.clearing = definition.clear_time;
					weapon_state.events |= structures::weapon_event_clearing;
				}

				else if (fire_pressed)
				{
					weapon_state.events |= structures::weapon_event_dry;
				}
			}

			else if (reload_pressed && held.loaded < definition.capacity && owner.count(definition.ammo) > 0u)
			{
				weapon_state.reloading = definition.reload * (held.loaded ? 0.85f : 1.0f);
				weapon_state.events |= structures::weapon_event_reload;
			}

			else if (gun_models[weapon_state.weapon].action == structures::action_draw)
			{
				if (fire_down && held.loaded > 0u && weapon_state.cooldown <= 0.0f)
				{
					weapon_state.events |= weapon_state.draw == 0.0f ? structures::weapon_event_drawing : 0u;
					weapon_state.draw = std::min(1.0f, weapon_state.draw + dt / bow_draw_time);
				}

				else if (weapon_state.draw > 0.0f)
				{
					if (weapon_state.draw > 0.2f && held.loaded > 0u)
					{
						loose(weapon_state, held, command, moving);
					}

					weapon_state.draw = 0.0f;
				}

				else if (held.loaded == 0u && weapon_state.cooldown <= 0.0f && owner.count(definition.ammo) > 0u)
				{
					weapon_state.reloading = definition.reload;
					weapon_state.events |= structures::weapon_event_reload;
				}
			}

			else if ((definition.automatic ? fire_down : fire_pressed) && weapon_state.cooldown <= 0.0f && ready)
			{
				if (held.loaded > 0u)
				{
					fire(weapon_state, held, command, moving);
				}

				else if (owner.count(definition.ammo) > 0u)
				{
					weapon_state.reloading = definition.reload;
					weapon_state.events |= structures::weapon_event_reload;
				}

				else
				{
					weapon_state.cooldown = weapon_dry_delay;
					weapon_state.events |= structures::weapon_event_dry;
				}
			}

			if ((weapon_state.flags & structures::weapon_flag_cycled) == 0u)
			{
				weapon_state.cycle += dt;

				if ((weapon_state.flags & structures::weapon_flag_worked) == 0u && weapon_state.cycle > weapon_bolt_delay)
				{
					weapon_state.flags |= structures::weapon_flag_worked;
					weapon_state.events |= structures::weapon_event_bolt;
				}

				weapon_state.flags = weapon_state.cycle > weapon_cycle_time ? (weapon_state.flags | structures::weapon_flag_cycled) : weapon_state.flags;
			}
		}

		else
		{
			weapon_state.aim = mathematics.approach(weapon_state.aim, 0.0f, dt * weapon_aim_rate);
			weapon_state.draw = 0.0f;
		}

		weapon_state.flags = fire_down ? (weapon_state.flags | structures::weapon_flag_fire_held) : (weapon_state.flags & ~structures::weapon_flag_fire_held);
		weapon_state.flags = (command.buttons & structures::button_reload) ? (weapon_state.flags | structures::weapon_flag_reload_held) : (weapon_state.flags & ~structures::weapon_flag_reload_held);
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::fire(structures::weapon_state_s& weapon_state, structures::item_stack_s& held, const structures::usercmd_s& command, bool moving)
	{
		const auto& definition{ weapon_definitions[weapon_state.weapon] };

		if (roll(weapon_state, command.sequence) < definition.misfire_chance * (1.0f + (1.0f - held.condition) * weapon_misfire_wear))
		{
			weapon_state.cooldown = weapon_misfire_delay;
			weapon_state.burst = 0u;
			weapon_state.events |= structures::weapon_event_misfire;

			if (roll(weapon_state, command.sequence) < weapon_hangfire_share)
			{
				weapon_state.hangfire = weapon_hangfire_minimum + roll(weapon_state, command.sequence) * weapon_hangfire_spread;
				weapon_state.cooldown += weapon_state.hangfire;
			}

			else
			{
				held.loaded--;

				weapon_state.cycle = 0.0f;
				weapon_state.flags = gun_models[weapon_state.weapon].action != structures::action_bolt ? (weapon_state.flags | structures::weapon_flag_cycled | structures::weapon_flag_worked) : (weapon_state.flags & ~(structures::weapon_flag_cycled | structures::weapon_flag_worked));
				weapon_state.events |= structures::weapon_event_dud;
			}
		}

		else
		{
			discharge(weapon_state, held, command, moving);
		}
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::discharge(structures::weapon_state_s& weapon_state, structures::item_stack_s& held, const structures::usercmd_s& command, bool moving)
	{
		const auto& definition{ weapon_definitions[weapon_state.weapon] };
		const auto wear{ 1.0f - held.condition };
		const auto spread{ mathematics.lerp(definition.spread, definition.aim_spread, weapon_state.aim) * (moving ? 1.6f : 1.0f) * (1.0f + weapon_state.heat * weapon_heat_spread) + std::min(static_cast<std::float_t>(weapon_state.burst), weapon_bloom_shots) * definition.bloom };

		weapon_state.shot = scatter(weapon_state, aim_direction(weapon_state, command.yaw, command.pitch, command.sequence), spread, command.sequence);

		held.loaded--;
		held.condition = std::max(0.05f, held.condition - weapon_wear_per_shot);

		const auto jitter{ roll(weapon_state, command.sequence) };
		const auto stutter{ roll(weapon_state, command.sequence) };
		const auto lift{ roll(weapon_state, command.sequence) };
		const auto swing{ roll(weapon_state, command.sequence) };

		weapon_state.cooldown = definition.interval * (1.0f + (jitter * 2.0f - 1.0f) * definition.rate_jitter) + (definition.rate_jitter > 0.0f && stutter < weapon_stutter_chance ? weapon_stutter_time : 0.0f);
		weapon_state.cycle = 0.0f;
		weapon_state.flags = gun_models[weapon_state.weapon].action != structures::action_bolt ? (weapon_state.flags | structures::weapon_flag_cycled | structures::weapon_flag_worked) : (weapon_state.flags & ~(structures::weapon_flag_cycled | structures::weapon_flag_worked));
		weapon_state.heat = std::min(1.0f, weapon_state.heat + definition.heat_per_shot);
		weapon_state.since_shot = 0.0f;
		weapon_state.burst++;
		weapon_state.punch_rise = std::min(weapon_state.punch_rise + definition.recoil * (1.0f - weapon_state.aim * 0.35f) * (0.75f + lift * 0.6f), std::max(weapon_punch_limit - weapon_state.punch_pitch, 0.0f));
		weapon_state.punch_yaw = std::clamp(weapon_state.punch_yaw + (swing - 0.5f) * definition.recoil * definition.kick_jitter, -weapon_punch_limit, weapon_punch_limit);
		weapon_state.events |= structures::weapon_event_fired;

		if (roll(weapon_state, command.sequence) < definition.jam_chance * (1.0f + weapon_state.heat * weapon_heat_jam) * (1.0f + wear * weapon_wear_jam))
		{
			weapon_state.flags |= structures::weapon_flag_jammed | structures::weapon_flag_cycled | structures::weapon_flag_worked;
			weapon_state.events |= structures::weapon_event_jam;
		}
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::loose(structures::weapon_state_s& weapon_state, structures::item_stack_s& held, const structures::usercmd_s& command, bool moving)
	{
		const auto& definition{ weapon_definitions[weapon_state.weapon] };
		const auto spread{ mathematics.lerp(definition.spread, definition.aim_spread, weapon_state.draw) * (moving ? 1.8f : 1.0f) };

		weapon_state.shot = scatter(weapon_state, aim_direction(weapon_state, command.yaw, command.pitch, command.sequence), spread, command.sequence);
		weapon_state.power = weapon_state.draw;
		weapon_state.cooldown = definition.interval;
		weapon_state.events |= structures::weapon_event_loosed;

		held.loaded--;
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::finish_reload(structures::weapon_state_s& weapon_state, survival_c& owner, structures::item_stack_s& held)
	{
		const auto& definition{ weapon_definitions[weapon_state.weapon] };
		const auto moved{ std::min(definition.capacity - std::min(held.loaded, definition.capacity), owner.count(definition.ammo)) };

		if (owner.take(definition.ammo, moved))
		{
			held.loaded += moved;
		}

		weapon_state.flags |= structures::weapon_flag_cycled | structures::weapon_flag_worked;
		weapon_state.events |= structures::weapon_event_reloaded;
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::effects(const structures::usercmd_s& command)
	{
		const auto events{ state.events };

		if (state.weapon != structures::weapon_none && events)
		{
			const auto& definition{ weapon_definitions[state.weapon] };
			const auto& held{ survival.slots[inventory_slots + state.slot] };

			if (events & structures::weapon_event_fired)
			{
				kick = 1.0f;
				flash = 0.06f;

				if (scoped == false)
				{
					particles.emit(structures::particle_flame, muzzle, { 0.0f, 0.0f, 1.2f }, 0.25f, 4u, true);
					particles.emit(structures::particle_smoke, muzzle, { 0.0f, 0.1f, 0.6f }, 0.1f, 2u, true);
				}

				renderer.add_light(renderer.camera.position + renderer.camera.forward * 0.8f, 6.0f, { 6.0f, 4.0f, 2.0f });

				mixer.gunshot(player.eye, definition.shot_sound, definition.far_sound, definition.loudness, true);

				strike(player.eye, state.shot, definition, held.item);
			}

			if (events & structures::weapon_event_loosed)
			{
				const auto forward{ mathematics.forward_from_angles(command.yaw, command.pitch) };
				const auto up{ mathematics.cross(forward, mathematics.normalize(mathematics.cross({ 0.0f, 1.0f, 0.0f }, forward))) };

				kick = 0.35f;

				projectiles.launch(player.eye + forward * 0.35f - up * 0.05f, state.shot * (arrow_speed_minimum + (arrow_speed_maximum - arrow_speed_minimum) * state.power * state.power), item_definitions[held.item].damage * (0.3f + 0.7f * state.power), -1);

				mixer.play_2d(definition.shot_sound, 0.75f, 1.45f + random() * 0.15f);
			}

			if (events & (structures::weapon_event_dry | structures::weapon_event_misfire))
			{
				mixer.play_2d(structures::sound_dry_fire, 0.6f, 0.9f + random() * 0.2f);
			}

			if (events & structures::weapon_event_dud)
			{
				survival.post("Dud round", 0);
			}

			if (events & structures::weapon_event_jam)
			{
				mixer.play_2d(structures::sound_jam, 0.7f, 0.9f + random() * 0.15f);

				survival.post("Jammed", 0);
			}

			if (events & structures::weapon_event_reload)
			{
				mixer.play_2d(definition.reload_sound, 0.8f, 1.0f);
			}

			if (events & structures::weapon_event_bolt)
			{
				mixer.play_2d(structures::sound_bolt, 0.7f, 1.0f);
			}

			if (events & structures::weapon_event_clearing)
			{
				mixer.play_2d(structures::sound_bolt, 0.8f, 0.8f);
			}

			if (events & structures::weapon_event_cleared)
			{
				mixer.play_2d(structures::sound_bolt, 0.8f, 1.05f);
			}

			if (events & structures::weapon_event_drawing)
			{
				mixer.play_2d(structures::sound_equip, 0.35f, 0.7f);
			}

			if (events & (structures::weapon_event_fired | structures::weapon_event_loosed))
			{
				for (auto& actor : actors.list)
				{
					if (actor.behavior == structures::actor_behavior_hostile && actor.dead == false && mathematics.distance(actor.position, player.state.position) < definition.noise)
					{
						actor.alerted = true;
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void weapons_c::strike(structures::vec3_s origin, structures::vec3_s direction, const structures::weapon_definition_s& definition, std::uint32_t item)
	{
		const auto hit{ world.trace(origin, origin + direction * definition.range, { 0.01f, 0.01f, 0.01f }, structures::contents_solid) };
		const auto limit{ hit.hit ? hit.fraction * definition.range : definition.range };

		auto distance{ 0.0f };
		auto height{ 0.0f };

		if (const auto target{ client.connected() ? -1 : ray_actor(origin, direction, limit, distance, height) }; target >= 0)
		{
			auto& actor{ actors.list[target] };

			const auto headshot{ height > 1.5f };
			const auto point{ origin + direction * distance };

			actors.damage(actor, item_definitions[item].damage * (headshot ? weapon_headshot_scale : 1.0f), direction);

			combat.hit_marker = 1.0f;
			combat.kill_marker = actor.dead ? 1.0f : combat.kill_marker;

			particles.impact(structures::surface_flesh, point, direction * -1.0f);

			mixer.play(structures::sound_hit_flesh, point, 1.0f, 0.9f + random() * 0.2f);

			if (actor.dead)
			{
				survival.post(headshot ? "Headshot kill" : "Kill", 0);
			}
		}

		else if (hit.hit)
		{
			particles.impact(hit.surface, hit.end - direction * 0.03f, hit.normal);

			mixer.play(hit.surface == structures::surface_metal ? structures::sound_hit_metal : (hit.surface == structures::surface_wood ? structures::sound_hit_wood : (hit.surface == structures::surface_concrete || hit.surface == structures::surface_rock ? structures::sound_hit_rock : structures::sound_hit_soft)), hit.end, 0.7f, 1.1f + random() * 0.2f);

			if (hit.brush >= 0 && client.connected() == false)
			{
				building.damage(hit.brush, item_definitions[item].damage * 0.25f, true);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s weapons_c::aim_direction(const structures::weapon_state_s& weapon_state, std::float_t yaw, std::float_t pitch, std::uint32_t sequence)
	{
		const auto shaking{ drift(weapon_state, static_cast<std::float_t>(sequence) * tick_interval) };

		return mathematics.forward_from_angles(yaw + weapon_state.punch_yaw + shaking.x, std::clamp(pitch + weapon_state.punch_pitch + shaking.y, -1.55f, 1.55f));
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s weapons_c::scatter(structures::weapon_state_s& weapon_state, structures::vec3_s forward, std::float_t spread, std::uint32_t sequence)
	{
		const auto right{ mathematics.normalize(mathematics.cross({ 0.0f, 1.0f, 0.0f }, forward)) };
		const auto up{ mathematics.cross(forward, right) };
		const auto angle{ roll(weapon_state, sequence) * two_pi };
		const auto radius{ std::sqrt(roll(weapon_state, sequence)) * spread };

		return mathematics.normalize(forward + right * (std::cos(angle) * radius) + up * (std::sin(angle) * radius));
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s weapons_c::drift(const structures::weapon_state_s& weapon_state, std::float_t time)
	{
		if (weapon_state.weapon != structures::weapon_none && weapon_definitions[weapon_state.weapon].scope > 0.0f && weapon_state.aim > weapon_scope_threshold)
		{
			return { std::sin(time * 0.63f) * 0.0022f + std::sin(time * 1.71f) * 0.0007f, std::sin(time * 0.91f + 1.0f) * 0.0016f };
		}

		return { 0.0f, 0.0f };
	}
	/*
	//=====================================================================================
	*/
	std::int32_t weapons_c::ray_actor(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance, std::float_t& height)
	{
		auto best{ -1 };

		distance = range;

		for (auto index{ 0u }; index < actors.list.size(); index++)
		{
			const auto& actor{ actors.list[index] };

			if (actor.behavior == structures::actor_behavior_hostile && actor.dead == false && actor.dormant == false)
			{
				const auto bottom{ actor.position + structures::vec3_s{ 0.0f, actor_radius, 0.0f } };
				const auto axis_length{ actor_height - actor_radius * 2.0f };
				const auto offset{ origin - bottom };
				const auto bend{ direction.y };
				const auto denominator{ 1.0f - bend * bend };
				const auto first{ denominator > 0.000001f ? std::clamp((bend * offset.y - mathematics.dot(direction, offset)) / denominator, 0.0f, range) : 0.0f };
				const auto along{ std::clamp(bend * first + offset.y, 0.0f, axis_length) };
				const auto closest{ std::clamp(mathematics.dot(bottom + structures::vec3_s{ 0.0f, along, 0.0f } - origin, direction), 0.0f, range) };
				const auto gap{ mathematics.distance(origin + direction * closest, bottom + structures::vec3_s{ 0.0f, along, 0.0f }) };

				if (gap < actor_radius + 0.06f && closest < distance)
				{
					best = static_cast<std::int32_t>(index);
					distance = closest;
					height = origin.y + direction.y * closest - actor.position.y;
				}
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	std::float_t weapons_c::roll(structures::weapon_state_s& weapon_state, std::uint32_t sequence)
	{
		weapon_state.rolls++;

		return static_cast<std::float_t>(mathematics.hash_u32(weapon_state.seed ^ (sequence * 0x9E3779B9u) ^ (weapon_state.rolls * 0x85EBCA6Bu)) & 0xFFFFFFu) / 16777216.0f;
	}
	/*
	//=====================================================================================
	*/
	std::float_t weapons_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
