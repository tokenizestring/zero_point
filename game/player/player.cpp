
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	player_c player;

	void player_c::spawn(structures::vec3_s position, std::float_t spawn_yaw)
	{
		movement.reset(state, position, spawn_yaw);

		previous = state;

		yaw = spawn_yaw;
		pitch = 0.0f;
		roll = 0.0f;
		accumulator = 0.0f;
		step_offset = 0.0f;
		landing_offset = 0.0f;
		landing_velocity = 0.0f;
		crouch_latched = false;
		aim_latched = false;
		sprint_latched = false;
		active = true;

		eye = position + structures::vec3_s{ 0.0f, state.eye_height, 0.0f };

		weapons.reset(mathematics.hash_u32(static_cast<std::uint32_t>(client.id) * 0x9E3779B9u + weapon_seed_salt));
	}
	/*
	//=====================================================================================
	*/
	void player_c::update(std::float_t dt, bool input_enabled)
	{
		if (active)
		{
			if (input_enabled)
			{
				const auto look{ sensitivity * renderer.zoom * mathematics.lerp(1.0f, aim_sensitivity, mathematics.saturate(weapons.aim)) };

				yaw = mathematics.wrap_angle(yaw + platform.input.mouse_delta.x * look);
				pitch = mathematics.clamp(pitch - platform.input.mouse_delta.y * look * (invert ? -1.0f : 1.0f), degrees_to_radians(-88.0f), degrees_to_radians(88.0f));

				if (platform.input.pressed[VK_F3] && client.connected() == false)
				{
					state.flags ^= structures::movement_noclip;
				}
			}

			turn_with_ride();

			build_command(input_enabled);

			accumulator = std::min(accumulator + dt, tick_interval * static_cast<std::float_t>(maximum_ticks_per_frame));

			while (accumulator >= tick_interval)
			{
				tick();

				accumulator -= tick_interval;
			}

			update_camera(dt);
		}
	}
	/*
	//=====================================================================================
	*/
	void player_c::turn_with_ride()
	{
		const auto car{ (state.flags & structures::movement_seated) ? vehicles.find(state.vehicle) : nullptr };
		const auto driving{ car && vehicle_kinds[car->kind].mode != structures::vehicle_mode_rotor ? vehicle_ride_base + car->id : 0u };
		const auto riding{ driving ? driving : (train.ready && state.platform && state.platform <= std::size(train_consist) ? state.platform : 0u) };

		if (riding)
		{
			const auto forward{ driving ? mathematics.quat_rotate(car->shown_orientation, { 0.0f, 0.0f, 1.0f }) : train.pose(train.clock, riding - 1u).row3(2u) };
			const auto facing{ std::atan2(forward.x, forward.z) };

			yaw = ridden == riding ? mathematics.wrap_angle(yaw + mathematics.angle_difference(heading, facing)) : yaw;
			heading = facing;
		}

		ridden = riding;
	}
	/*
	//=====================================================================================
	*/
	void player_c::build_command(bool input_enabled)
	{
		const auto& keys{ platform.input.down };

		command = {};

		command.yaw = transport.decode_angle(transport.encode_angle(yaw));
		command.pitch = transport.decode_pitch(transport.encode_pitch(pitch));
		command.delta = tick_interval;
		command.weapon = survival.active_slot;
		command.time = transport.quantize_time(client.connected() ? client.server_clock : train.clock);

		if (input_enabled)
		{
			command.forward = (platform.held(structures::bind_forward) ? 1.0f : 0.0f) - (platform.held(structures::bind_back) ? 1.0f : 0.0f);
			command.side = (platform.held(structures::bind_right) ? 1.0f : 0.0f) - (platform.held(structures::bind_left) ? 1.0f : 0.0f);

			crouch_latched = crouch_toggle && (crouch_latched != platform.tapped(structures::bind_crouch));
			aim_latched = aim_toggle && (aim_latched != platform.input.pressed[VK_RBUTTON]);
			sprint_latched = sprint_toggle && command.forward > 0.0f && (sprint_latched || platform.tapped(structures::bind_sprint));

			command.buttons |= platform.held(structures::bind_jump) ? structures::button_jump : 0u;
			command.buttons |= (platform.held(structures::bind_crouch) || crouch_latched) ? structures::button_crouch : 0u;
			command.buttons |= (platform.held(structures::bind_sprint) || sprint_latched) ? structures::button_sprint : 0u;
			command.buttons |= (keys[VK_RBUTTON] || aim_latched) ? structures::button_aim : 0u;
			command.buttons |= keys[VK_LBUTTON] ? structures::button_fire : 0u;
			command.buttons |= platform.held(structures::bind_reload) ? structures::button_reload : 0u;
			command.buttons |= platform.held(structures::bind_use) ? structures::button_use : 0u;
			command.buttons |= platform.held(structures::bind_visor) ? structures::button_visor : 0u;
			command.buttons |= platform.held(structures::bind_melee) ? structures::button_melee : 0u;
			command.buttons |= platform.held(structures::bind_throw) ? structures::button_grenade : 0u;
			command.buttons |= platform.held(structures::bind_walk) ? structures::button_walk : 0u;
		}
	}
	/*
	//=====================================================================================
	*/
	void player_c::tick()
	{
		previous = state;

		command.sequence = ++sequence;

		vehicles.pilot(state, command);

		movement.simulate(state, command);

		if ((command.buttons & structures::button_use) && (harvest.tool.flags & structures::tool_flag_use_held) == 0u && client.connected() == false && survival.vitals.dead == false)
		{
			const auto seated{ (state.flags & structures::movement_seated) != 0u };

			if (seated || vehicles.board(state, 0, eye, mathematics.forward_from_angles(yaw, pitch)) || vehicles.tame(state, 0, eye, mathematics.forward_from_angles(yaw, pitch)))
			{
				if (seated)
				{
					vehicles.alight(state, 0);
				}

				previous = state;

				harvest.tool.flags |= structures::tool_flag_use_held;
			}
		}

		const auto usable{ survival.vitals.dead == false && (state.flags & (structures::movement_swimming | structures::movement_seated)) == 0u };
		const auto moving{ mathematics.length(structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z }) > 1.0f };

		weapons.tick(command, usable, moving);

		harvest.tick(command, usable);

		if (client.connected())
		{
			client.record(command, usable, moving);
		}

		else
		{
			marks.tread(state, tread);
		}

		if (std::fabs(state.step) > move_step_smooth)
		{
			step_offset = std::clamp(step_offset - state.step, -move_step_height, move_step_height);
		}

		if (state.flags & structures::movement_landed)
		{
			landing_velocity -= std::min(state.landing_speed * 0.045f, 0.55f);
		}

		if (state.position.y < world.kill_height && maps.spawns.size() && client.connected() == false)
		{
			logger.write("player: fell out of the world at %.1f %.1f %.1f", state.position.x, state.position.y, state.position.z);

			spawn(maps.spawns[0].position, maps.spawns[0].yaw);
		}
	}
	/*
	//=====================================================================================
	*/
	void player_c::update_camera(std::float_t dt)
	{
		const auto alpha{ accumulator / tick_interval };
		const auto aboard{ train.ready && state.platform && previous.platform == state.platform && state.platform <= std::size(train_consist) };
		const auto position{ aboard ? mathematics.transform_point(mathematics.lerp(previous.local, state.local, alpha), train.pose(train.clock, state.platform - 1u)) : mathematics.lerp(previous.position, state.position, alpha) };
		const auto eye_height{ mathematics.lerp(previous.eye_height, state.eye_height, alpha) };
		const auto velocity{ mathematics.lerp(previous.velocity, state.velocity, alpha) };
		const auto horizontal_speed{ mathematics.length(structures::vec3_s{ velocity.x, 0.0f, velocity.z }) };
		const auto on_ground{ (state.flags & structures::movement_on_ground) != 0u };

		step_offset = mathematics.damp(step_offset, 0.0f, 14.0f, dt);

		landing_velocity += (-landing_offset * 90.0f - landing_velocity * 12.0f) * dt;
		landing_offset += landing_velocity * dt;

		bob_weight = mathematics.damp(bob_weight, on_ground ? mathematics.saturate(horizontal_speed / move_speed_sprint) : 0.0f, 10.0f, dt);

		bob_phase += on_ground ? horizontal_speed * dt / (step_length_base + step_length_scale * horizontal_speed) : 0.0f;

		const auto bob{ -std::cos(bob_phase * two_pi) * 0.016f * bob_weight * bob_scale };
		const auto sway{ std::sin(bob_phase * pi) * 0.011f * bob_weight * bob_scale };
		const auto right{ mathematics.right_from_yaw(yaw) };

		roll = mathematics.damp(roll, -mathematics.dot(velocity, right) * 0.0035f * tilt_scale, 8.0f, dt);

		const auto afloat{ (state.flags & structures::movement_swimming) ? mathematics.saturate(1.0f - (state.water_surface - position.y - eye_height) / 1.5f) : 0.0f };

		swell = mathematics.damp(swell, (water.level(position.x, position.z) - state.water_surface) * afloat, 8.0f, dt);

		eye = position + client.error + structures::vec3_s{ 0.0f, eye_height + step_offset + bob + (landing_offset + swell) * motion_scale, 0.0f } + right * sway;
	}
}

//=====================================================================================
