
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	movement_c movement;

	void movement_c::reset(structures::movement_state_s& state, structures::vec3_s position, std::float_t yaw)
	{
		state = {};

		state.position = position + structures::vec3_s{ 0.0f, 0.02f, 0.0f };
		state.yaw = yaw;
		state.height = player_height;
		state.eye_height = player_eye_height;
		state.speed_scale = 1.0f;
		state.fall_peak = position.y;
		state.ground_normal = { 0.0f, 1.0f, 0.0f };
		state.ground = -1;
		state.water_surface = water.still();
		state.water_depth = state.water_surface - state.position.y;

		unstick(state);

		categorize(state);
	}
	/*
	//=====================================================================================
	*/
	void movement_c::simulate(structures::movement_state_s& state, const structures::usercmd_s& command)
	{
		const auto dt{ std::clamp(command.delta, 0.0f, 0.1f) };

		state.yaw = command.yaw;
		state.pitch = command.pitch;
		state.step = 0.0f;
		state.jump_timer = std::max(state.jump_timer - dt, 0.0f);
		state.flags &= ~structures::movement_landed;

		board(state, command.time);

		if (state.flags & structures::movement_noclip)
		{
			noclip(state, command);
		}

		else
		{
			unstick(state);

			if (state.water_depth > ((state.flags & structures::movement_swimming) ? water_swim_exit : water_swim_depth))
			{
				swim(state, command, dt);
			}

			else
			{
				walk(state, command, dt);
			}
		}

		ride(state, command.time);

		state.eye_height = mathematics.approach(state.eye_height, (state.flags & structures::movement_crouched) ? player_crouch_eye_height : player_eye_height, dt * move_crouch_rate);
		state.water_surface = water.still();
		state.water_depth = state.water_surface - state.position.y;
		state.flags = state.position.y + state.eye_height < state.water_surface - 0.02f ? (state.flags | structures::movement_underwater) : (state.flags & ~structures::movement_underwater);
	}
	/*
	//=====================================================================================
	*/
	void movement_c::board(structures::movement_state_s& state, std::double_t time)
	{
		beside = train.ready && (state.platform != 0u || train.close(state.position, time));
		anchored = 0u;

		if (beside)
		{
			train.place(time);
		}

		if (beside && state.platform && state.platform <= std::size(train_consist))
		{
			const auto target{ mathematics.transform_point(state.local, train.posed[state.platform - 1u]) };
			const auto lift{ structures::vec3_s{ 0.0f, state.height * 0.5f, 0.0f } };

			anchor = target;
			anchored = state.platform;

			if (mathematics.distance(target, state.position) < train_carry_limit)
			{
				world.carrying = true;

				state.position = trace_hull(state, center(state), target + lift).end - lift;

				world.carrying = false;
			}

			else
			{
				state.position = target;
			}
		}

		else
		{
			state.platform = 0u;
		}
	}
	/*
	//=====================================================================================
	*/
	void movement_c::ride(structures::movement_state_s& state, std::double_t time)
	{
		const auto grounded{ (state.flags & structures::movement_on_ground) != 0u };
		const auto settled{ grounded || (state.flags & (structures::movement_swimming | structures::movement_noclip)) != 0u };
		const auto mover{ state.ground - mover_brush_base };
		const auto standing{ beside && grounded && mover >= 0 && mover < static_cast<std::int32_t>(world.movers.size()) ? world.movers[mover].owner + 1u : 0u };
		const auto next{ settled ? standing : state.platform };

		if (next != state.platform)
		{
			const auto leaving{ state.platform ? train.velocity(state.platform - 1u, state.position, time) : structures::vec3_s{} };
			const auto joining{ next ? train.velocity(next - 1u, state.position, time) : structures::vec3_s{} };

			state.velocity += leaving - joining;

			if (const auto rush{ mathematics.length(structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z }) }; grounded && rush > train_tumble_speed)
			{
				state.landing_speed = std::max((state.flags & structures::movement_landed) ? state.landing_speed : 0.0f, rush * train_tumble_scale);
				state.flags |= structures::movement_landed;
			}

			state.platform = next;
		}

		if (state.platform)
		{
			const auto& seat{ train.posed[state.platform - 1u] };
			const auto moved{ state.position - anchor };

			state.local = anchored == state.platform ? state.local + structures::vec3_s{ mathematics.dot(moved, seat.row3(0u)), mathematics.dot(moved, seat.row3(1u)), mathematics.dot(moved, seat.row3(2u)) } : mathematics.transform_point(state.position, mathematics.inverse(seat));
			state.flags |= structures::movement_riding;
		}

		else
		{
			state.flags &= ~structures::movement_riding;
		}
	}
	/*
	//=====================================================================================
	*/
	void movement_c::walk(structures::movement_state_s& state, const structures::usercmd_s& command, std::float_t dt)
	{
		update_crouch(state, (command.buttons & structures::button_crouch) != 0u);

		categorize(state);

		const auto wading{ mathematics.saturate((state.water_depth - water_wade_depth) / (water_swim_depth - water_wade_depth)) };
		const auto crouched{ (state.flags & structures::movement_crouched) != 0u };
		const auto aiming{ (command.buttons & structures::button_aim) != 0u };
		const auto sprinting{ (command.buttons & structures::button_sprint) && command.forward > 0.5f && crouched == false && aiming == false && wading < 0.6f };
		const auto forward{ mathematics.flat_forward(state.yaw) };
		const auto right{ mathematics.right_from_yaw(state.yaw) };
		const auto horizontal{ structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z } };
		const auto start{ state.position };

		auto wish{ forward * std::clamp(command.forward, -1.0f, 1.0f) + right * (std::clamp(command.side, -1.0f, 1.0f) * (sprinting ? move_sprint_side : 1.0f)) };

		if (const auto wish_length{ mathematics.length(wish) }; wish_length > 1.0f)
		{
			wish = wish / wish_length;
		}

		auto top_speed{ crouched ? move_speed_crouch : (sprinting ? move_speed_sprint : move_speed_run) };

		if (aiming)
		{
			top_speed *= move_speed_aim;
		}

		if (command.buttons & structures::button_walk)
		{
			top_speed *= move_speed_walk;
		}

		top_speed *= state.speed_scale * mathematics.lerp(1.0f, water_wade_slow, wading);

		state.flags = sprinting ? (state.flags | structures::movement_sprinting) : (state.flags & ~structures::movement_sprinting);
		state.flags &= ~structures::movement_swimming;

		if ((command.buttons & structures::button_jump) && (state.flags & structures::movement_jump_held) == 0u && (state.flags & (structures::movement_on_ground | structures::movement_wedged)) && crouched == false && state.jump_timer <= 0.0f)
		{
			const auto speed{ mathematics.length(horizontal) };
			const auto kept{ speed > top_speed ? horizontal * (top_speed / speed) : horizontal };

			state.velocity = { kept.x, move_jump_velocity * (1.0f - wading * water_wade_jump), kept.z };
			state.flags &= ~(structures::movement_on_ground | structures::movement_wedged);
			state.flags |= structures::movement_jump_held;
			state.jump_timer = move_jump_cooldown;
			state.stuck_time = 0.0f;
		}

		else if (state.flags & structures::movement_on_ground)
		{
			const auto downhill{ mathematics.normalize(structures::vec3_s{ state.ground_normal.x, 0.0f, state.ground_normal.z }) };
			const auto steepness{ mathematics.saturate((1.0f - state.ground_normal.y) / (1.0f - move_walkable)) };
			const auto climbing{ mathematics.saturate(-mathematics.dot(mathematics.normalize(wish), downhill)) };
			const auto target{ wish * (top_speed * (1.0f - move_uphill_slow * steepness * climbing)) };
			const auto moved{ mathematics.approach(horizontal, target, (mathematics.length(wish) > 0.01f ? move_accelerate : move_decelerate) * dt) };

			state.velocity = { moved.x, 0.0f, moved.z };
		}

		else
		{
			if (mathematics.length(wish) > 0.01f)
			{
				const auto steered{ mathematics.approach(horizontal, wish * top_speed, move_air_control * dt) };

				state.velocity.x = steered.x;
				state.velocity.z = steered.z;
			}

			state.velocity.y = std::max(state.velocity.y - move_gravity * dt, -move_terminal_speed);
		}

		if ((command.buttons & structures::button_jump) == 0u)
		{
			state.flags &= ~structures::movement_jump_held;
		}

		const auto was_on_ground{ (state.flags & structures::movement_on_ground) != 0u };
		const auto impact{ -state.velocity.y };

		auto touching{ false };

		if (was_on_ground)
		{
			ground_move(state, dt);
		}

		else
		{
			slide_move(state, dt);

			touching = categorize(state);
		}

		if (state.flags & structures::movement_on_ground)
		{
			if (was_on_ground == false)
			{
				land(state, impact);
			}

			state.fall_peak = state.position.y;
			state.air_time = 0.0f;
			state.stuck_time = 0.0f;
			state.flags &= ~structures::movement_wedged;
			state.stride += mathematics.length(structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z }) * dt;
		}

		else
		{
			state.fall_peak = std::max(state.fall_peak, state.position.y);
			state.air_time += dt;
			state.stuck_time = touching && mathematics.length(state.position - start) < move_stuck_distance ? state.stuck_time + dt : 0.0f;
			state.flags = state.stuck_time >= move_stuck_time ? (state.flags | structures::movement_wedged) : (state.flags & ~structures::movement_wedged);
		}
	}
	/*
	//=====================================================================================
	*/
	void movement_c::swim(structures::movement_state_s& state, const structures::usercmd_s& command, std::float_t dt)
	{
		update_crouch(state, false);

		const auto look{ mathematics.forward_from_angles(state.yaw, state.pitch) };
		const auto surfaced{ (state.flags & structures::movement_underwater) == 0u };
		const auto forward{ surfaced && look.y > -swim_dive_pitch ? mathematics.flat_forward(state.yaw) : look };
		const auto right{ mathematics.right_from_yaw(state.yaw) };
		const auto rise{ ((command.buttons & structures::button_jump) ? 1.0f : 0.0f) - ((command.buttons & structures::button_crouch) ? 1.0f : 0.0f) };
		const auto sprinting{ (command.buttons & structures::button_sprint) && command.forward > 0.5f };

		auto wish{ forward * std::clamp(command.forward, -1.0f, 1.0f) + right * std::clamp(command.side, -1.0f, 1.0f) + structures::vec3_s{ 0.0f, rise, 0.0f } };

		if (const auto wish_length{ mathematics.length(wish) }; wish_length > 1.0f)
		{
			wish = wish / wish_length;
		}

		const auto wish_speed{ mathematics.length(wish) * (sprinting ? swim_speed_sprint : swim_speed) * state.speed_scale };
		const auto below{ state.water_surface - state.eye_height + water_float_eye - state.position.y };

		state.velocity = state.velocity * std::exp(-swim_drag * dt);

		accelerate(state, mathematics.normalize(wish), wish_speed, swim_accelerate, dt);

		state.velocity.y += (below > 0.0f ? std::min(below * swim_spring, swim_buoyancy) : std::max(below * swim_spring * 1.5f, -move_gravity)) * dt;

		state.flags |= structures::movement_swimming;
		state.flags &= ~(structures::movement_on_ground | structures::movement_sprinting | structures::movement_wedged);
		state.ground_normal = { 0.0f, 1.0f, 0.0f };

		if ((command.buttons & structures::button_jump) == 0u)
		{
			state.flags &= ~structures::movement_jump_held;
		}

		slide_move(state, dt);

		state.fall_peak = state.position.y;
		state.air_time = 0.0f;
		state.stuck_time = 0.0f;
		state.stride += mathematics.length(state.velocity) * dt;
	}
	/*
	//=====================================================================================
	*/
	void movement_c::noclip(structures::movement_state_s& state, const structures::usercmd_s& command)
	{
		const auto forward{ mathematics.forward_from_angles(state.yaw, state.pitch) };
		const auto right{ mathematics.right_from_yaw(state.yaw) };
		const auto speed{ (command.buttons & structures::button_sprint) ? 22.0f : 8.0f };
		const auto up{ ((command.buttons & structures::button_jump) ? 1.0f : 0.0f) - ((command.buttons & structures::button_crouch) ? 1.0f : 0.0f) };

		state.velocity = (forward * command.forward + right * command.side + structures::vec3_s{ 0.0f, up, 0.0f }) * speed;

		state.position += state.velocity * command.delta;

		state.flags &= ~(structures::movement_on_ground | structures::movement_crouched | structures::movement_wedged);

		state.height = player_height;

		state.fall_peak = state.position.y;
	}
	/*
	//=====================================================================================
	*/
	void movement_c::ground_move(structures::movement_state_s& state, std::float_t dt)
	{
		const auto normal{ state.ground_normal };

		state.velocity.y = -(state.velocity.x * normal.x + state.velocity.z * normal.z) / std::max(normal.y, move_walkable) + move_ground_lift;

		step_slide_move(state, dt);

		if (snap_to_ground(state))
		{
			state.velocity.y = 0.0f;
		}

		else
		{
			state.flags &= ~structures::movement_on_ground;
			state.ground_normal = { 0.0f, 1.0f, 0.0f };
			state.velocity.y = std::min(state.velocity.y, 0.0f);
		}
	}
	/*
	//=====================================================================================
	*/
	void movement_c::land(structures::movement_state_s& state, std::float_t impact)
	{
		const auto slow{ 1.0f - move_land_slow * mathematics.saturate((impact - move_land_soft) / (move_land_hard - move_land_soft)) };

		state.flags |= structures::movement_landed;
		state.landing_speed = impact;
		state.fall_distance = std::max(state.fall_peak - state.position.y, 0.0f);
		state.velocity.x *= slow;
		state.velocity.z *= slow;
		state.jump_timer = std::max(state.jump_timer, move_land_delay);
	}
	/*
	//=====================================================================================
	*/
	void movement_c::accelerate(structures::movement_state_s& state, structures::vec3_s direction, std::float_t speed, std::float_t rate, std::float_t dt)
	{
		const auto current{ mathematics.dot(state.velocity, direction) };

		if (const auto add{ speed - current }; add > 0.0f)
		{
			state.velocity += direction * std::min(rate * dt * speed, add);
		}
	}
	/*
	//=====================================================================================
	*/
	void movement_c::update_crouch(structures::movement_state_s& state, bool wants_crouch)
	{
		const auto difference{ player_height - player_crouch_height };
		const auto airborne{ (state.flags & structures::movement_on_ground) == 0u };

		if (wants_crouch)
		{
			if ((state.flags & structures::movement_crouched) == 0u)
			{
				state.flags |= structures::movement_crouched;

				if (airborne)
				{
					state.position.y += difference;

					state.eye_height -= difference;
				}

				state.height = player_crouch_height;
			}
		}

		else if (state.flags & structures::movement_crouched)
		{
			auto standing{ state };

			standing.height = player_height;
			standing.position.y -= airborne ? difference : 0.0f;

			if (airborne && solid(standing))
			{
				standing.position.y = state.position.y;
			}

			if (solid(standing) == false)
			{
				state.flags &= ~structures::movement_crouched;
				state.eye_height += state.position.y - standing.position.y;
				state.position = standing.position;
				state.height = player_height;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void movement_c::unstick(structures::movement_state_s& state)
	{
		if (solid(state))
		{
			auto freed{ false };

			if ((state.flags & structures::movement_crouched) == 0u)
			{
				auto crouched{ state };

				crouched.height = player_crouch_height;

				if (solid(crouched) == false)
				{
					state.flags |= structures::movement_crouched;
					state.height = player_crouch_height;

					freed = true;
				}
			}

			for (auto index{ 0u }; index < std::size(movement_unstick) && freed == false; index++)
			{
				auto moved{ state };

				moved.position += movement_unstick[index];

				if (solid(moved) == false)
				{
					state.position = moved.position;

					freed = true;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void movement_c::step_slide_move(structures::movement_state_s& state, std::float_t dt)
	{
		const auto start{ state };

		if (slide_move(state, dt))
		{
			const auto direct{ state };
			const auto start_center{ center(start) };
			const auto up{ trace_hull(start, start_center, start_center + structures::vec3_s{ 0.0f, move_step_height, 0.0f }) };

			if (up.all_solid == false && up.start_solid == false)
			{
				auto stepped{ start };

				stepped.position = up.end - structures::vec3_s{ 0.0f, start.height * 0.5f, 0.0f };

				slide_move(stepped, dt);

				const auto stepped_center{ center(stepped) };
				const auto down{ trace_hull(stepped, stepped_center, stepped_center - structures::vec3_s{ 0.0f, up.end.y - start_center.y + move_ground_probe, 0.0f }) };

				if (down.hit && down.start_solid == false && down.normal.y >= move_walkable)
				{
					stepped.position = down.end - structures::vec3_s{ 0.0f, stepped.height * 0.5f, 0.0f };

					const auto direct_distance{ mathematics.length(structures::vec3_s{ direct.position.x - start.position.x, 0.0f, direct.position.z - start.position.z }) };
					const auto stepped_distance{ mathematics.length(structures::vec3_s{ stepped.position.x - start.position.x, 0.0f, stepped.position.z - start.position.z }) };

					if (stepped_distance > direct_distance + 0.001f)
					{
						stepped.step += stepped.position.y - direct.position.y;
						stepped.ground_normal = down.normal;
						stepped.ground_surface = down.surface;
						stepped.ground = down.brush;

						state = stepped;
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool movement_c::slide_move(structures::movement_state_s& state, std::float_t dt)
	{
		structures::vec3_s planes[move_clip_planes]{};

		const auto grounded{ (state.flags & structures::movement_on_ground) != 0u };

		auto plane_count{ 0u };
		auto time_left{ dt };
		auto position{ center(state) };
		auto velocity{ state.velocity };
		auto blocked{ false };
		auto active{ true };

		if (grounded)
		{
			planes[plane_count++] = state.ground_normal;
		}

		planes[plane_count++] = mathematics.normalize(velocity);

		for (auto bump{ 0u }; bump < trace_bumps && active; bump++)
		{
			const auto result{ trace_hull(state, position, position + velocity * time_left) };

			if (result.all_solid)
			{
				velocity.y = std::max(velocity.y, 0.0f);

				active = false;

				blocked = true;
			}

			else
			{
				position = result.end;

				if (result.fraction < 1.0f)
				{
					blocked = true;

					last_block = result;

					time_left -= time_left * result.fraction;

					if (plane_count < move_clip_planes)
					{
						const auto wall{ grounded && result.normal.y > 0.0f && result.normal.y < move_walkable };

						planes[plane_count++] = wall ? mathematics.normalize(structures::vec3_s{ result.normal.x, 0.0f, result.normal.z }) : result.normal;

						auto resolved{ false };

						for (auto i{ 0u }; i < plane_count && resolved == false; i++)
						{
							if (mathematics.dot(velocity, planes[i]) < 0.1f)
							{
								auto clipped{ clip_velocity(velocity, planes[i], move_overclip) };
								auto valid{ true };

								for (auto j{ 0u }; j < plane_count && valid; j++)
								{
									if (j != i && mathematics.dot(clipped, planes[j]) < 0.1f)
									{
										clipped = clip_velocity(clipped, planes[j], move_overclip);

										if (mathematics.dot(clipped, planes[i]) < 0.0f)
										{
											const auto crease{ mathematics.normalize(mathematics.cross(planes[i], planes[j])) };

											clipped = crease * mathematics.dot(crease, velocity);

											for (auto k{ 0u }; k < plane_count && valid; k++)
											{
												if (k != i && k != j && mathematics.dot(clipped, planes[k]) < 0.1f)
												{
													clipped = { 0.0f, 0.0f, 0.0f };

													valid = false;
												}
											}
										}
									}
								}

								velocity = clipped;

								resolved = true;
							}
						}
					}

					else
					{
						velocity = { 0.0f, 0.0f, 0.0f };

						active = false;
					}
				}

				else
				{
					active = false;
				}
			}
		}

		state.position = position - structures::vec3_s{ 0.0f, state.height * 0.5f, 0.0f };
		state.velocity = velocity;

		return blocked;
	}
	/*
	//=====================================================================================
	*/
	bool movement_c::snap_to_ground(structures::movement_state_s& state)
	{
		const auto from{ center(state) };
		const auto result{ trace_hull(state, from, from - structures::vec3_s{ 0.0f, move_step_height + move_ground_probe, 0.0f }) };

		if (result.hit && result.start_solid == false && result.normal.y >= move_walkable)
		{
			state.step += result.end.y - from.y;
			state.position = result.end - structures::vec3_s{ 0.0f, state.height * 0.5f, 0.0f };
			state.ground_normal = result.normal;
			state.ground_surface = result.surface;
			state.ground = result.brush;
			state.flags |= structures::movement_on_ground;

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool movement_c::categorize(structures::movement_state_s& state)
	{
		const auto from{ center(state) };
		const auto result{ trace_hull(state, from, from - structures::vec3_s{ 0.0f, move_ground_probe, 0.0f }) };

		if (result.hit && result.start_solid == false && result.normal.y >= move_walkable && state.velocity.y <= move_ground_leave)
		{
			state.flags |= structures::movement_on_ground;
			state.ground_normal = result.normal;
			state.ground_surface = result.surface;
			state.ground = result.brush;
		}

		else
		{
			state.flags &= ~structures::movement_on_ground;
			state.ground_normal = { 0.0f, 1.0f, 0.0f };
		}

		return result.hit;
	}
	/*
	//=====================================================================================
	*/
	bool movement_c::solid(const structures::movement_state_s& state)
	{
		return world.box_solid(center(state), extents(state), structures::contents_solid | structures::contents_player_clip);
	}
	/*
	//=====================================================================================
	*/
	std::float_t movement_c::fall_damage(const structures::movement_state_s& state)
	{
		auto damage{ 0.0f };

		if (state.flags & structures::movement_landed)
		{
			damage = maximum_health * mathematics.saturate((state.landing_speed - fall_damage_start) / (fall_damage_lethal - fall_damage_start));
		}

		return damage;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s movement_c::clip_velocity(structures::vec3_s velocity, structures::vec3_s normal, std::float_t overbounce)
	{
		const auto backoff{ mathematics.dot(velocity, normal) };

		return velocity - normal * (backoff < 0.0f ? backoff * overbounce : backoff / overbounce);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s movement_c::extents(const structures::movement_state_s& state)
	{
		return { player_half_width, state.height * 0.5f, player_half_width };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s movement_c::center(const structures::movement_state_s& state)
	{
		return state.position + structures::vec3_s{ 0.0f, state.height * 0.5f, 0.0f };
	}
	/*
	//=====================================================================================
	*/
	structures::trace_s movement_c::trace_hull(const structures::movement_state_s& state, structures::vec3_s from_center, structures::vec3_s to_center)
	{
		return world.trace(from_center, to_center, extents(state), structures::contents_solid | structures::contents_player_clip);
	}
}

//=====================================================================================
