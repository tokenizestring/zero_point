
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	vehicles_c vehicles;

	void vehicles_c::create()
	{
		const auto last{ static_cast<std::uint32_t>(std::size(train_consist) - 1u) };

		movers = std::max(static_cast<std::uint32_t>(world.movers.size()), train.first_mover[last] + static_cast<std::uint32_t>(train.boxes[train_consist[last]].size()));
		burnt = models.variant(structures::material_metal_rust, { 0.17f, 0.15f, 0.14f }, 0.15f);

		for (auto kind{ 0u }; kind < structures::vehicle_kind_count; kind++)
		{
			shape(kind);

			if (gpu.device && vehicle_kinds[kind].mode != structures::vehicle_mode_hooves)
			{
				build(kind);
			}
		}

		ready = true;
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::shape(std::uint32_t kind)
	{
		const auto& definition{ vehicle_kinds[kind] };

		boxes[kind].clear();
		corners[kind].clear();

		if (const auto model{ models.find(definition.model) }; model)
		{
			for (const auto& part : model->parts)
			{
				if (std::strncmp(part.name, "col_", 4u) == 0)
				{
					boxes[kind].push_back({ turned((part.bounds_min + part.bounds_max) * 0.5f), (part.bounds_max - part.bounds_min) * 0.5f, maps.surface_named(part.name + 4) });
				}
			}
		}

		if (boxes[kind].empty())
		{
			boxes[kind].push_back({ definition.hull_center, definition.hull_half, structures::surface_metal });

			if (kind == structures::vehicle_heli)
			{
				boxes[kind].push_back({ { 0.0f, 1.55f, -3.1f }, { 0.22f, 0.25f, 2.1f }, structures::surface_metal });
				boxes[kind].push_back({ { -0.95f, 0.08f, 0.6f }, { 0.07f, 0.08f, 1.5f }, structures::surface_metal });
				boxes[kind].push_back({ { 0.95f, 0.08f, 0.6f }, { 0.07f, 0.08f, 1.5f }, structures::surface_metal });
			}
		}

		auto low{ structures::vec3_s{ FLT_MAX, FLT_MAX, FLT_MAX } };
		auto high{ structures::vec3_s{ -FLT_MAX, -FLT_MAX, -FLT_MAX } };

		for (const auto& box : boxes[kind])
		{
			low = mathematics.minimum(low, box.center - box.half);
			high = mathematics.maximum(high, box.center + box.half);

			for (auto corner{ 0u }; corner < 8u; corner++)
			{
				corners[kind].push_back(box.center + structures::vec3_s{ corner & 1u ? box.half.x : -box.half.x, corner & 2u ? box.half.y : -box.half.y, corner & 4u ? box.half.z : -box.half.z });
			}
		}

		const auto half{ (high - low) * 0.5f };

		inertia[kind] = structures::vec3_s{ half.y * half.y + half.z * half.z, half.x * half.x + half.z * half.z, half.x * half.x + half.y * half.y } * (definition.mass / 3.0f);
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::build(std::uint32_t kind)
	{
		const auto& definition{ vehicle_kinds[kind] };

		char far_name[64]{};

		std::snprintf(far_name, sizeof(far_name), "%s_far", definition.model);

		if (const auto model{ models.find(definition.model) }; model)
		{
			const char* wheel_names[4] = { "wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr" };
			const char* rotor_names[2] = { "rotor_main", "rotor_tail" };

			const auto flip{ mathematics.rotation_y(pi) };

			shop.clear();

			for (const auto& part : model->parts)
			{
				const auto moving{ std::strncmp(part.name, "wheel_", 6u) == 0 || std::strncmp(part.name, "rotor_", 6u) == 0 || std::strncmp(part.name, "steering", 8u) == 0 };

				if (part.index_count && moving == false)
				{
					shop.append(*model, part.first_index, part.index_count, flip);
				}
			}

			shop.upload(bodies[kind]);

			for (auto wheel{ 0u }; wheel < 4u; wheel++)
			{
				if (const auto part{ models.part(*model, wheel_names[wheel]) }; part && part->index_count)
				{
					shop.clear();
					shop.append(*model, part->first_index, part->index_count, flip);
					shop.upload(wheels[kind][wheel]);

					pivots[kind][wheel] = turned((part->bounds_min + part->bounds_max) * 0.5f);
				}
			}

			for (auto rotor{ 0u }; kind == structures::vehicle_heli && rotor < 2u; rotor++)
			{
				if (const auto part{ models.part(*model, rotor_names[rotor]) }; part && part->index_count)
				{
					shop.clear();
					shop.append(*model, part->first_index, part->index_count, flip);
					shop.upload(rotors[kind][rotor]);

					hubs[kind][rotor] = rotor == 0u ? definition.rotor_hub : definition.tail_hub;
				}
			}

			if (kind == structures::vehicle_rover)
			{
				if (const auto part{ models.part(*model, "steering") }; part && part->index_count)
				{
					shop.clear();
					shop.append(*model, part->first_index, part->index_count, flip);
					shop.upload(steering[kind]);

					wheel_hub[kind] = rover_steering_hub;
				}
			}

			if (const auto far_model{ models.find(far_name) }; far_model)
			{
				shop.clear();
				shop.append(*far_model, 0u, static_cast<std::uint32_t>(far_model->indices.size()), flip);
				shop.upload(distant[kind]);
			}
		}

		else
		{
			mock(kind);
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s vehicles_c::turned(structures::vec3_s point)
	{
		return { -point.x, point.y, -point.z };
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::mock(std::uint32_t kind)
	{
		const auto& definition{ vehicle_kinds[kind] };
		const auto identity{ mathematics.quat_identity() };

		shop.clear();

		if (kind == structures::vehicle_rover)
		{
			shop.set_material(structures::material_metal_rust);
			shop.box(definition.hull_center + structures::vec3_s{ 0.0f, -0.15f, 0.0f }, { definition.hull_half.x * 2.0f, 0.75f, definition.hull_half.z * 2.0f }, identity);
			shop.set_material(structures::material_metal_green);
			shop.box({ 0.0f, 1.72f, -0.2f }, { 1.8f, 0.7f, 2.2f }, identity);
			shop.set_material(structures::material_steel);
			shop.box({ 0.0f, 1.0f, 2.3f }, { 1.9f, 0.3f, 0.12f }, identity);
			shop.upload(bodies[kind]);

			for (auto wheel{ 0u }; wheel < 4u; wheel++)
			{
				const auto center{ definition.wheels[wheel] };

				shop.clear();
				shop.set_material(structures::material_tire);
				shop.cylinder(center - structures::vec3_s{ 0.15f, 0.0f, 0.0f }, { 1.0f, 0.0f, 0.0f }, definition.wheel_radius, 0.3f, 18u, true);
				shop.set_material(structures::material_steel);
				shop.box(center, { 0.32f, definition.wheel_radius * 0.9f, 0.12f }, identity);
				shop.upload(wheels[kind][wheel]);

				pivots[kind][wheel] = center;
			}
		}

		else
		{
			shop.set_material(structures::material_metal_green);
			shop.box(definition.hull_center, definition.hull_half * 2.0f, identity);
			shop.set_material(structures::material_metal_rust);
			shop.box({ 0.0f, 1.55f, -3.1f }, { 0.44f, 0.5f, 4.2f }, identity);
			shop.box({ 0.0f, 2.35f, 0.4f }, { 0.25f, 0.6f, 0.25f }, identity);
			shop.set_material(structures::material_steel);
			shop.box({ -0.95f, 0.08f, 0.6f }, { 0.14f, 0.16f, 3.0f }, identity);
			shop.box({ 0.95f, 0.08f, 0.6f }, { 0.14f, 0.16f, 3.0f }, identity);
			shop.box({ -0.95f, 0.45f, 1.4f }, { 0.08f, 0.7f, 0.08f }, identity);
			shop.box({ 0.95f, 0.45f, 1.4f }, { 0.08f, 0.7f, 0.08f }, identity);
			shop.box({ -0.95f, 0.45f, -0.2f }, { 0.08f, 0.7f, 0.08f }, identity);
			shop.box({ 0.95f, 0.45f, -0.2f }, { 0.08f, 0.7f, 0.08f }, identity);
			shop.upload(bodies[kind]);

			shop.clear();
			shop.set_material(structures::material_paint_gunmetal);
			shop.box(definition.rotor_hub, { definition.rotor_radius * 2.0f, 0.05f, 0.28f }, identity);
			shop.box(definition.rotor_hub, { 0.28f, 0.05f, definition.rotor_radius * 2.0f }, identity);
			shop.upload(rotors[kind][0]);

			shop.clear();
			shop.box(definition.tail_hub, { 0.04f, 1.3f, 0.16f }, identity);
			shop.upload(rotors[kind][1]);

			hubs[kind][0] = definition.rotor_hub;
			hubs[kind][1] = definition.tail_hub;
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::clear()
	{
		list.clear();

		next_id = 1u;
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::populate()
	{
		clear();

		for (const auto& entry : vehicle_spawns)
		{
			spawn(entry.kind, { entry.position.x, terrain.height(entry.position.x, entry.position.y), entry.position.y }, entry.yaw);

			list.back().home = static_cast<std::uint32_t>(&entry - vehicle_spawns);
		}

		update_movers();

		logger.write("vehicles: %zu vehicles parked", list.size());
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::spawn(std::uint32_t kind, structures::vec3_s position, std::float_t yaw)
	{
		structures::vehicle_s vehicle{};

		vehicle.kind = kind;
		vehicle.id = next_id++;
		vehicle.home = UINT32_MAX;

		reset(vehicle, position, yaw);

		list.push_back(vehicle);
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::reset(structures::vehicle_s& vehicle, structures::vec3_s position, std::float_t yaw)
	{
		const auto kind{ vehicle.kind };

		vehicle.velocity = {};
		vehicle.spin = {};
		vehicle.steer = 0.0f;
		vehicle.engine = 0.0f;
		vehicle.rotor_speed = 0.0f;
		vehicle.wreck_time = 0.0f;
		vehicle.still = 0.0f;
		vehicle.asleep = false;
		vehicle.position = position + structures::vec3_s{ 0.0f, 0.25f, 0.0f };
		vehicle.orientation = mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw);
		vehicle.health = vehicle_kinds[kind].health;
		vehicle.riders[0] = -1;
		vehicle.riders[1] = -1;
		vehicle.shown_position = vehicle.position;
		vehicle.shown_orientation = vehicle.orientation;
		vehicle.from_position = vehicle.position;
		vehicle.to_position = vehicle.position;
		vehicle.from_orientation = vehicle.orientation;
		vehicle.to_orientation = vehicle.orientation;
		vehicle.tick_position = vehicle.position;
		vehicle.tick_orientation = vehicle.orientation;

		for (auto& wheel : vehicle.compression)
		{
			wheel = vehicle_kinds[kind].travel * 0.5f;
		}

		vehicle.world = pose(vehicle.position, vehicle.orientation);
		vehicle.previous_world = vehicle.world;
	}
	/*
	//=====================================================================================
	*/
	structures::vehicle_s* vehicles_c::find(std::uint32_t id)
	{
		const auto found{ std::find_if(list.begin(), list.end(), [&](const structures::vehicle_s& vehicle) { return vehicle.id == id; }) };

		return found != list.end() ? &*found : nullptr;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t vehicles_c::index_of(std::uint32_t id)
	{
		const auto found{ std::find_if(list.begin(), list.end(), [&](const structures::vehicle_s& vehicle) { return vehicle.id == id; }) };

		return found != list.end() ? static_cast<std::int32_t>(found - list.begin()) : -1;
	}
	/*
	//=====================================================================================
	*/
	structures::vehicle_controls_s vehicles_c::controls(const structures::vehicle_s& vehicle, const structures::usercmd_s& command)
	{
		structures::vehicle_controls_s result{};

		result.engine = vehicle.health > 0.0f;
		result.throttle = vehicle.health > 0.0f ? command.forward : 0.0f;
		result.steer = command.side;
		result.brake = (command.buttons & structures::button_jump) != 0u;
		result.lift = vehicle.health > 0.0f ? ((command.buttons & structures::button_jump) ? 1.0f : 0.0f) - ((command.buttons & structures::button_crouch) ? 1.0f : 0.0f) : -1.0f;
		result.pitch = command.forward;
		result.roll = command.side;
		result.heading = command.yaw;
		result.sprint = (command.buttons & structures::button_sprint) != 0u;

		return result;
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::pilot(structures::movement_state_s& state, const structures::usercmd_s& command)
	{
		if (const auto vehicle{ state.vehicle && state.seat == 0u ? find(state.vehicle) : nullptr }; vehicle)
		{
			vehicle->asleep = false;
			vehicle->still = 0.0f;
			vehicle->tick_position = vehicle->position;
			vehicle->tick_orientation = vehicle->orientation;

			advance(*vehicle, controls(*vehicle, command), command.delta);
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::advance(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t delta)
	{
		const auto steps{ std::max(1u, static_cast<std::uint32_t>(std::round(std::clamp(delta, 0.0f, 0.1f) / vehicle_substep))) };
		const auto dt{ std::clamp(delta, 0.0f, 0.1f) / static_cast<std::float_t>(steps) };
		const auto slot{ index_of(vehicle.id) };

		world.ignored = slot >= 0 ? vehicle_owner_base + static_cast<std::uint32_t>(slot) : UINT32_MAX;

		for (auto step_index{ 0u }; step_index < steps && dt > 0.0f; step_index++)
		{
			step(vehicle, controls, dt);
		}

		world.ignored = UINT32_MAX;
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::step(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt)
	{
		const auto& definition{ vehicle_kinds[vehicle.kind] };

		if (definition.mode == structures::vehicle_mode_hooves)
		{
			stride(vehicle, controls, dt);

			return;
		}

		structures::vec3_s force{ 0.0f, -vehicle_gravity * definition.mass, 0.0f };
		structures::vec3_s torque{};

		vehicle.rotor_speed = mathematics.approach(vehicle.rotor_speed, controls.engine && definition.mode == structures::vehicle_mode_rotor ? 1.0f : 0.0f, dt / vehicle_spool_time);
		vehicle.rotor = std::fmod(vehicle.rotor + vehicle.rotor_speed * vehicle_rotor_turns * two_pi * dt, two_pi * 64.0f);

		if (definition.wheel_count)
		{
			suspend(vehicle, controls, dt, force, torque);
		}

		else
		{
			hover(vehicle, controls, dt, force, torque);
		}

		const auto mass_point{ vehicle.position + mathematics.quat_rotate(vehicle.orientation, definition.mass_center) };
		const auto speed{ mathematics.length(vehicle.velocity) };

		force = force - vehicle.velocity * (definition.mass * (vehicle_linear_drag + vehicle_air_drag * speed));

		vehicle.velocity = vehicle.velocity + force * (dt / definition.mass);
		vehicle.spin = (vehicle.spin + solve(vehicle, torque) * dt) * std::max(0.0f, 1.0f - (definition.wheel_count ? vehicle_angular_drag * 0.25f : 0.0f) * dt);

		const auto moved{ mass_point + vehicle.velocity * dt };
		const auto turn{ mathematics.length(vehicle.spin) };

		if (turn > 0.00001f)
		{
			vehicle.orientation = mathematics.quat_normalize(mathematics.quat_multiply(mathematics.quat_axis_angle(vehicle.spin / turn, turn * dt), vehicle.orientation));
		}

		vehicle.position = moved - mathematics.quat_rotate(vehicle.orientation, definition.mass_center);

		collide(vehicle, dt);
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::suspend(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt, structures::vec3_s& force, structures::vec3_s& torque)
	{
		const auto& definition{ vehicle_kinds[vehicle.kind] };
		const auto up{ mathematics.quat_rotate(vehicle.orientation, { 0.0f, 1.0f, 0.0f }) };
		const auto ahead{ mathematics.quat_rotate(vehicle.orientation, { 0.0f, 0.0f, 1.0f }) };
		const auto mass_point{ vehicle.position + mathematics.quat_rotate(vehicle.orientation, definition.mass_center) };
		const auto length{ definition.travel + definition.wheel_radius };
		const auto share{ definition.mass / static_cast<std::float_t>(definition.wheel_count) };
		const auto forward_speed{ mathematics.dot(vehicle.velocity, ahead) };
		const auto fade{ 1.0f - vehicle_steer_fade * mathematics.saturate(std::fabs(forward_speed) / std::max(definition.top_speed, 1.0f)) };
		const auto opposing{ controls.throttle * forward_speed < 0.0f && std::fabs(forward_speed) > 1.0f };

		vehicle.steer = mathematics.approach(vehicle.steer, controls.steer * definition.steer * fade, vehicle_steer_rate * dt);
		vehicle.engine = mathematics.damp(vehicle.engine, controls.engine ? mathematics.saturate(0.25f + std::fabs(forward_speed) / std::max(definition.top_speed, 1.0f) * 0.6f + std::fabs(controls.throttle) * 0.25f) : 0.0f, 3.0f, dt);

		std::float_t squeezed[4]{};

		for (auto wheel{ 0u }; wheel < definition.wheel_count && wheel < 4u; wheel++)
		{
			const auto mount{ vehicle.position + mathematics.quat_rotate(vehicle.orientation, definition.wheels[wheel] + structures::vec3_s{ 0.0f, definition.travel * 0.5f, 0.0f }) };
			const auto hit{ world.trace(mount, mount - up * length, { 0.1f, 0.04f, 0.1f }, structures::contents_solid) };

			if (hit.hit && hit.start_solid == false)
			{
				const auto distance{ hit.fraction * length };
				const auto squeeze{ length - distance };
				const auto contact_point{ mount - up * distance };
				const auto arm{ contact_point - mass_point };
				const auto point_velocity{ vehicle.velocity + mathematics.cross(vehicle.spin, arm) };
				const auto load{ std::max(0.0f, definition.spring * std::min(squeeze, definition.travel) + definition.spring * 6.0f * std::max(squeeze - definition.travel, 0.0f) - definition.damper * mathematics.dot(point_velocity, up)) };
				const auto steered{ wheel < 2u ? mathematics.quat_rotate(mathematics.quat_axis_angle(up, vehicle.steer), ahead) : ahead };
				const auto rolling_direction{ mathematics.normalize(steered - hit.normal * mathematics.dot(steered, hit.normal)) };
				const auto side_direction{ mathematics.normalize(mathematics.cross(hit.normal, rolling_direction)) };
				const auto along{ mathematics.dot(point_velocity, rolling_direction) };
				const auto across{ mathematics.dot(point_velocity, side_direction) };
				const auto locked{ controls.brake && wheel >= 2u };
				const auto limit{ controls.throttle > 0.0f ? definition.top_speed : definition.reverse_speed };
				const auto power{ opposing ? 0.0f : controls.throttle * definition.drive * mathematics.saturate(1.0f - std::fabs(along) / std::max(limit, 1.0f)) };
				const auto stopping{ opposing || locked ? -std::copysign(std::min(definition.brake, std::fabs(along) * share / dt), along) : 0.0f };
				const auto coasting{ controls.throttle == 0.0f && locked == false ? -along * share * 0.12f : 0.0f };
				const auto rolling{ -std::copysign(std::min(load * vehicle_rolling, std::fabs(along) * share / dt), along) };

				auto lateral{ -across * share * vehicle_grip_response / dt * (locked ? 0.3f : 1.0f) };
				auto longitudinal{ power + stopping + coasting + rolling };

				const auto grip_limit{ definition.grip * load * (locked ? 0.75f : 1.0f) };
				const auto total{ std::sqrt(lateral * lateral + longitudinal * longitudinal) };

				if (total > grip_limit && total > 0.0f)
				{
					lateral *= grip_limit / total;
					longitudinal *= grip_limit / total;
				}

				const auto applied{ up * load + rolling_direction * longitudinal + side_direction * lateral };

				force = force + applied;
				torque = torque + mathematics.cross(arm, applied);

				vehicle.compression[wheel] = std::min(squeeze, definition.travel);
				vehicle.spun[wheel] = std::fmod(vehicle.spun[wheel] + (locked ? 0.0f : along / definition.wheel_radius * dt), two_pi);

				squeezed[wheel] = std::min(squeeze, definition.travel);
			}

			else
			{
				vehicle.compression[wheel] = mathematics.approach(vehicle.compression[wheel], 0.0f, dt * 2.0f);
				vehicle.spun[wheel] = std::fmod(vehicle.spun[wheel] + controls.throttle * 12.0f * dt, two_pi);
			}
		}

		for (auto axle{ 0u }; axle + 1u < definition.wheel_count && axle < 4u; axle += 2u)
		{
			const auto difference{ (squeezed[axle] - squeezed[axle + 1u]) * definition.spring * 0.6f };

			for (auto side{ 0u }; side < 2u; side++)
			{
				const auto point{ vehicle.position + mathematics.quat_rotate(vehicle.orientation, definition.wheels[axle + side]) };
				const auto push{ up * (side == 0u ? difference : -difference) };

				force = force + push;
				torque = torque + mathematics.cross(point - mass_point, push);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::hover(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt, structures::vec3_s& force, structures::vec3_s& torque)
	{
		const auto& definition{ vehicle_kinds[vehicle.kind] };
		const auto up{ mathematics.quat_rotate(vehicle.orientation, { 0.0f, 1.0f, 0.0f }) };
		const auto ahead{ mathematics.quat_rotate(vehicle.orientation, { 0.0f, 0.0f, 1.0f }) };
		const auto right{ mathematics.quat_rotate(vehicle.orientation, { 1.0f, 0.0f, 0.0f }) };
		const auto spool{ vehicle.rotor_speed * vehicle.rotor_speed };
		const auto level{ mathematics.lerp(1.0f, std::max(up.y, 0.5f), 0.7f) };
		const auto thrust{ definition.mass * vehicle_gravity / level * spool };
		const auto climb{ controls.lift * (controls.lift > 0.0f ? vehicle_climb_rate : vehicle_sink_rate) };
		const auto hold{ std::clamp((climb - vehicle.velocity.y) * definition.mass * vehicle_hold, -definition.mass * vehicle_gravity * 0.9f, definition.mass * vehicle_gravity * definition.lift) * spool };
		const auto local_spin{ mathematics.quat_rotate(mathematics.quat_conjugate(vehicle.orientation), vehicle.spin) };
		const auto pitch_now{ std::asin(std::clamp(ahead.y, -1.0f, 1.0f)) };
		const auto roll_now{ std::asin(std::clamp(right.y, -1.0f, 1.0f)) };
		const auto heading_now{ std::atan2(ahead.x, ahead.z) };
		const auto authority{ mathematics.saturate(spool * 1.4f) };
		const structures::vec3_s wanted{ -(-controls.pitch * definition.tilt - pitch_now) * 2.4f * authority, std::clamp(mathematics.angle_difference(heading_now, controls.heading) * 2.2f, -definition.turn, definition.turn) * authority, (-controls.roll * definition.tilt - roll_now) * 2.4f * authority };
		const auto correction{ (wanted - local_spin) * 5.0f };

		vehicle.engine = mathematics.damp(vehicle.engine, vehicle.rotor_speed * (0.55f + 0.45f * mathematics.saturate(std::fabs(controls.lift) + std::fabs(controls.pitch) * 0.5f)), 2.0f, dt);

		force = force + up * thrust + structures::vec3_s{ 0.0f, hold, 0.0f };
		torque = torque + mathematics.quat_rotate(vehicle.orientation, { correction.x * inertia[vehicle.kind].x, correction.y * inertia[vehicle.kind].y, correction.z * inertia[vehicle.kind].z });
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::stride(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt)
	{
		const auto& definition{ vehicle_kinds[vehicle.kind] };
		const auto ahead{ mathematics.quat_rotate(vehicle.orientation, { 0.0f, 0.0f, 1.0f }) };
		const auto heading{ std::atan2(ahead.x, ahead.z) };
		const auto pace{ mathematics.dot(structures::vec3_s{ vehicle.velocity.x, 0.0f, vehicle.velocity.z }, mathematics.flat_forward(heading)) };
		const auto wanted{ controls.engine == false ? 0.0f : (controls.throttle > 0.0f ? (controls.sprint ? definition.top_speed : horse_trot_speed) * controls.throttle : (controls.throttle < 0.0f ? -definition.reverse_speed : 0.0f)) };
		const auto speed{ mathematics.approach(pace, wanted, (std::fabs(wanted) > std::fabs(pace) ? definition.drive : definition.brake) * dt) };
		const auto course{ mathematics.flat_forward(heading + controls.steer * mathematics.lerp(definition.steer, definition.turn, mathematics.saturate(std::fabs(speed) / definition.top_speed)) * dt) };
		const auto reach{ course * ((speed >= 0.0f ? definition.hull_half.z : -definition.hull_half.z) * 0.6f) };
		const auto chest{ vehicle.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f } + reach };
		const auto next{ vehicle.position + course * (speed * dt) };
		const auto deep{ terrain.enabled && terrain.height(next.x + reach.x, next.z + reach.z) < sea_level - horse_wade };
		const auto blocked{ deep || world.trace(chest, chest + course * (speed * dt), { 0.28f, 0.55f, 0.28f }, structures::contents_solid).hit };
		const auto pace_now{ blocked ? 0.0f : speed };

		auto moved{ blocked ? vehicle.position : next };

		vehicle.velocity.y -= horse_gravity * dt;
		moved.y += vehicle.velocity.y * dt;

		const auto floor{ footing(moved, moved.y - 1.0f) };
		const auto settled{ vehicle.compression[0] > 0.5f && vehicle.velocity.y <= 0.0f && moved.y - floor < horse_step };

		if (moved.y <= floor || settled)
		{
			moved.y = floor;
			vehicle.velocity.y = controls.brake && controls.engine ? definition.lift : 0.0f;
			vehicle.compression[0] = vehicle.velocity.y > 0.0f ? 0.0f : 1.0f;
		}

		else
		{
			vehicle.compression[0] = 0.0f;
		}

		const auto front{ footing(moved + course * horse_probe, moved.y) };
		const auto back{ footing(moved - course * horse_probe, moved.y) };
		const auto forward{ mathematics.normalize(course + structures::vec3_s{ 0.0f, std::clamp((front - back) / (horse_probe * 2.0f), -0.6f, 0.6f), 0.0f }) };
		const auto right{ mathematics.normalize(mathematics.cross({ 0.0f, 1.0f, 0.0f }, forward)) };

		vehicle.orientation = mathematics.quat_from_basis(right, mathematics.cross(forward, right), forward);
		vehicle.velocity = { course.x * pace_now, vehicle.velocity.y, course.z * pace_now };
		vehicle.position = moved;
		vehicle.spin = {};
		vehicle.steer = controls.steer;
		vehicle.engine = 0.0f;
		vehicle.rotor_speed = 0.0f;
	}
	/*
	//=====================================================================================
	*/
	std::float_t vehicles_c::footing(structures::vec3_s point, std::float_t fallback)
	{
		const auto hit{ world.trace(point + structures::vec3_s{ 0.0f, horse_step, 0.0f }, point - structures::vec3_s{ 0.0f, 3.0f, 0.0f }, { 0.2f, 0.02f, 0.2f }, structures::contents_solid) };

		return hit.hit && hit.start_solid == false ? hit.end.y - 0.02f : fallback;
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::collide(structures::vehicle_s& vehicle, std::float_t dt)
	{
		const auto& definition{ vehicle_kinds[vehicle.kind] };
		const auto mass_point{ vehicle.position + mathematics.quat_rotate(vehicle.orientation, definition.mass_center) };

		auto deepest{ 0.0f };
		auto push{ structures::vec3_s{} };
		auto impact{ 0.0f };

		for (const auto& corner : corners[vehicle.kind])
		{
			const auto point{ vehicle.position + mathematics.quat_rotate(vehicle.orientation, corner) };
			const auto hit{ world.trace(mass_point, point, { 0.02f, 0.02f, 0.02f }, structures::contents_solid) };

			if (hit.hit && hit.start_solid == false)
			{
				const auto depth{ mathematics.distance(hit.end, point) };
				const auto arm{ point - mass_point };
				const auto point_velocity{ vehicle.velocity + mathematics.cross(vehicle.spin, arm) };
				const auto approach{ mathematics.dot(point_velocity, hit.normal) };

				if (approach < 0.0f)
				{
					const auto turning{ mathematics.cross(solve(vehicle, mathematics.cross(arm, hit.normal)), arm) };
					const auto resistance{ 1.0f / definition.mass + mathematics.dot(hit.normal, turning) };
					const auto impulse{ -(1.0f + vehicle_restitution) * approach / std::max(resistance, 0.000001f) };
					const auto sliding{ point_velocity - hit.normal * approach };
					const auto slide{ mathematics.length(sliding) };
					const auto friction{ slide > 0.01f ? std::min(slide / std::max(resistance, 0.000001f), vehicle_contact_friction * impulse) : 0.0f };
					const auto total{ hit.normal * impulse - (slide > 0.01f ? sliding * (friction / slide) : structures::vec3_s{}) };

					vehicle.velocity = vehicle.velocity + total * (1.0f / definition.mass);
					vehicle.spin = vehicle.spin + solve(vehicle, mathematics.cross(arm, total));

					impact = std::max(impact, -approach);
				}

				if (depth > deepest)
				{
					deepest = depth;
					push = hit.normal;
				}
			}
		}

		vehicle.position = vehicle.position + push * (std::max(deepest - 0.02f, 0.0f) * 0.6f);
		vehicle.scrape = std::max(vehicle.scrape, impact);

		if (impact > vehicle_crash_speed)
		{
			vehicle.health = std::max(0.0f, vehicle.health - (impact - vehicle_crash_speed) * vehicle_crash_damage);
		}

		static_cast<void>(dt);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s vehicles_c::solve(const structures::vehicle_s& vehicle, structures::vec3_s torque)
	{
		const auto local{ mathematics.quat_rotate(mathematics.quat_conjugate(vehicle.orientation), torque) };
		const auto& moment{ inertia[vehicle.kind] };

		return mathematics.quat_rotate(vehicle.orientation, { local.x / std::max(moment.x, 1.0f), local.y / std::max(moment.y, 1.0f), local.z / std::max(moment.z, 1.0f) });
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::simulate(std::float_t delta)
	{
		for (auto& vehicle : list)
		{
			vehicle.wreck_time = vehicle.health <= 0.0f && vehicle.riders[0] < 0 && vehicle.riders[1] < 0 ? vehicle.wreck_time + delta : 0.0f;

			if (vehicle.wreck_time > vehicle_respawn_time && vehicle.home < std::size(vehicle_spawns))
			{
				const auto& entry{ vehicle_spawns[vehicle.home] };

				reset(vehicle, { entry.position.x, terrain.height(entry.position.x, entry.position.y), entry.position.y }, entry.yaw);
			}

			if (vehicle.riders[0] < 0)
			{
				const auto moving{ mathematics.length(vehicle.velocity) > vehicle_sleep_speed || mathematics.length(vehicle.spin) > vehicle_sleep_speed || vehicle.rotor_speed > 0.0f };

				vehicle.still = moving ? 0.0f : vehicle.still + delta;
				vehicle.asleep = vehicle.still > vehicle_sleep_time;

				if (vehicle.asleep == false)
				{
					advance(vehicle, { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, true, false }, delta);
				}

				else
				{
					vehicle.velocity = {};
					vehicle.spin = {};
				}
			}
		}

		bury();

		update_movers();
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::bury()
	{
		for (const auto& vehicle : list)
		{
			if (vehicle_kinds[vehicle.kind].mode == structures::vehicle_mode_hooves && vehicle.health <= 0.0f)
			{
				const auto ahead{ mathematics.quat_rotate(vehicle.orientation, { 0.0f, 0.0f, 1.0f }) };

				fauna.fall(structures::species_horse, vehicle.position, std::atan2(ahead.x, ahead.z));
			}
		}

		list.erase(std::remove_if(list.begin(), list.end(), [](const structures::vehicle_s& vehicle) { return vehicle_kinds[vehicle.kind].mode == structures::vehicle_mode_hooves && vehicle.health <= 0.0f; }), list.end());
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::place(const structures::vehicle_s& vehicle, std::uint32_t slot)
	{
		const auto placement{ pose(vehicle.position, vehicle.orientation) };
		const auto& shapes{ boxes[vehicle.kind] };

		for (auto box{ 0u }; box < shapes.size() && box < vehicle_mover_stride; box++)
		{
			world.set_mover(movers + slot * vehicle_mover_stride + box, placement, shapes[box].center, shapes[box].half, shapes[box].surface, vehicle_owner_base + slot);
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::update_movers()
	{
		for (auto slot{ 0u }; slot < list.size(); slot++)
		{
			place(list[slot], slot);
		}

		for (auto slot{ static_cast<std::uint32_t>(list.size()) }; slot < placed; slot++)
		{
			for (auto box{ 0u }; box < vehicle_mover_stride; box++)
			{
				world.set_mover(movers + slot * vehicle_mover_stride + box, mathematics.translation({ 0.0f, -10000.0f, 0.0f }), {}, { 0.01f, 0.01f, 0.01f }, structures::surface_metal, UINT32_MAX - 1u);
			}
		}

		placed = static_cast<std::uint32_t>(list.size());
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s vehicles_c::pose(structures::vec3_s position, structures::quat_s orientation)
	{
		return mathematics.multiply(mathematics.rotation(orientation), mathematics.translation(position));
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s vehicles_c::seat_point(const structures::vehicle_s& vehicle, std::uint32_t seat)
	{
		return vehicle.position + mathematics.quat_rotate(vehicle.orientation, vehicle_kinds[vehicle.kind].seats[std::min(seat, 1u)]);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s vehicles_c::exit_point(const structures::vehicle_s& vehicle, std::uint32_t seat)
	{
		return vehicle.position + mathematics.quat_rotate(vehicle.orientation, vehicle_kinds[vehicle.kind].exits[std::min(seat, 1u)]);
	}
	/*
	//=====================================================================================
	*/
	std::int32_t vehicles_c::reach(structures::vec3_s eye, structures::vec3_s forward, std::uint32_t& seat)
	{
		auto distance{ vehicle_enter_reach };
		auto chosen{ -1 };

		if (const auto hit{ ray(eye, forward, vehicle_enter_reach, distance) }; hit >= 0)
		{
			const auto& vehicle{ list[hit] };
			const auto& definition{ vehicle_kinds[vehicle.kind] };

			auto nearest{ FLT_MAX };

			for (auto candidate{ 0u }; candidate < definition.seat_count; candidate++)
			{
				if (const auto gap{ mathematics.distance(seat_point(vehicle, candidate), eye) }; vehicle.riders[candidate] < 0 && gap < nearest)
				{
					nearest = gap;
					seat = candidate;
					chosen = hit;
				}
			}
		}

		return chosen;
	}
	/*
	//=====================================================================================
	*/
	bool vehicles_c::board(structures::movement_state_s& state, std::int32_t rider, structures::vec3_s eye, structures::vec3_s forward)
	{
		auto seat{ 0u };

		if (const auto index{ state.vehicle == 0u ? reach(eye, forward, seat) : -1 }; index >= 0)
		{
			mount(state, rider, static_cast<std::uint32_t>(index), seat);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool vehicles_c::tame(structures::movement_state_s& state, std::int32_t rider, structures::vec3_s eye, structures::vec3_s forward)
	{
		auto distance{ 0.0f };

		if (const auto target{ state.vehicle == 0u ? fauna.ray(eye, forward, vehicle_enter_reach, distance) : -1 }; target >= 0 && fauna.animals[target].alive && fauna.animals[target].species == structures::species_horse)
		{
			auto& animal{ fauna.animals[target] };

			animal.alive = false;
			animal.yields = 0u;
			animal.state = structures::animal_dead;

			spawn(structures::vehicle_horse, animal.position, animal.yaw);

			mount(state, rider, static_cast<std::uint32_t>(list.size() - 1u), 0u);

			update_movers();

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::mount(structures::movement_state_s& state, std::int32_t rider, std::uint32_t index, std::uint32_t seat)
	{
		auto& vehicle{ list[index] };

		vehicle.riders[seat] = rider;
		vehicle.asleep = false;
		vehicle.still = 0.0f;

		state.vehicle = vehicle.id;
		state.seat = seat;
		state.flags = (state.flags | structures::movement_seated) & ~(structures::movement_crouched | structures::movement_sprinting | structures::movement_swimming | structures::movement_underwater);
		state.platform = 0u;
		state.velocity = vehicle.velocity;
		state.position = seat_point(vehicle, seat) - structures::vec3_s{ 0.0f, player_eye_height, 0.0f };
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::alight(structures::movement_state_s& state, std::int32_t rider)
	{
		if (auto vehicle{ find(state.vehicle) }; vehicle)
		{
			const auto seat{ std::min(state.seat, 1u) };
			const auto half{ structures::vec3_s{ player_half_width, player_height * 0.5f, player_half_width } };
			const auto lift{ structures::vec3_s{ 0.0f, player_height * 0.5f + 0.05f, 0.0f } };
			const structures::vec3_s choices[3] = { exit_point(*vehicle, seat), exit_point(*vehicle, 1u - seat), vehicle->position + structures::vec3_s{ 0.0f, 2.6f, 0.0f } };

			auto landing{ choices[0] };

			for (auto index{ 2 }; index >= 0; index--)
			{
				landing = world.box_solid(choices[index] + lift, half, structures::contents_solid | structures::contents_player_clip) == false ? choices[index] : landing;
			}

			vehicle->riders[seat] = vehicle->riders[seat] == rider ? -1 : vehicle->riders[seat];

			state.position = landing;
			state.velocity = vehicle->velocity;
		}

		state.vehicle = 0u;
		state.seat = 0u;
		state.flags &= ~structures::movement_seated;
	}
	/*
	//=====================================================================================
	*/
	std::float_t vehicles_c::damage(std::uint32_t index, std::float_t amount)
	{
		if (index < list.size())
		{
			auto& vehicle{ list[index] };

			vehicle.health = std::max(0.0f, vehicle.health - amount);
			vehicle.asleep = false;
			vehicle.still = 0.0f;

			return vehicle.health;
		}

		return 0.0f;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t vehicles_c::ray(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance)
	{
		auto best{ -1 };

		distance = range;

		for (auto index{ 0u }; index < list.size(); index++)
		{
			const auto& vehicle{ list[index] };

			if (mathematics.distance(vehicle.position, origin) < range + 12.0f)
			{
				const auto inverse{ mathematics.quat_conjugate(vehicle.orientation) };
				const auto local_origin{ mathematics.quat_rotate(inverse, origin - vehicle.position) };
				const auto local_direction{ mathematics.quat_rotate(inverse, direction) };

				for (const auto& box : boxes[vehicle.kind])
				{
					auto enter{ 0.0f };
					auto leave{ distance };
					auto inside{ true };

					for (auto axis{ 0u }; axis < 3u && inside; axis++)
					{
						const auto start{ local_origin[axis] - box.center[axis] };
						const auto heading{ local_direction[axis] };

						if (std::fabs(heading) < 0.000001f)
						{
							inside = std::fabs(start) <= box.half[axis];
						}

						else
						{
							const auto first{ (-box.half[axis] - start) / heading };
							const auto second{ (box.half[axis] - start) / heading };

							enter = std::max(enter, std::min(first, second));
							leave = std::min(leave, std::max(first, second));
							inside = enter <= leave;
						}
					}

					if (inside && enter < distance)
					{
						distance = enter;
						best = static_cast<std::int32_t>(index);
					}
				}
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::write_state(stream_writer_c& writer, const structures::vehicle_s& vehicle)
	{
		writer.u32(vehicle.id);
		writer.u8(static_cast<std::uint8_t>(vehicle.kind));
		writer.f32(vehicle.position.x);
		writer.f32(vehicle.position.y);
		writer.f32(vehicle.position.z);
		writer.f32(vehicle.orientation.x);
		writer.f32(vehicle.orientation.y);
		writer.f32(vehicle.orientation.z);
		writer.f32(vehicle.orientation.w);
		writer.f32(vehicle.velocity.x);
		writer.f32(vehicle.velocity.y);
		writer.f32(vehicle.velocity.z);
		writer.f32(vehicle.spin.x);
		writer.f32(vehicle.spin.y);
		writer.f32(vehicle.spin.z);

		for (const auto compressed : vehicle.compression)
		{
			writer.f32(compressed);
		}

		writer.f32(vehicle.steer);
		writer.f32(vehicle.rotor_speed);
		writer.f32(vehicle.engine);
		writer.f32(vehicle.health);
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::read_state(stream_reader_c& reader, structures::vehicle_s& vehicle)
	{
		vehicle.id = reader.u32();
		vehicle.kind = std::min<std::uint32_t>(reader.u8(), structures::vehicle_kind_count - 1u);
		vehicle.position = { reader.f32(), reader.f32(), reader.f32() };
		vehicle.orientation = { reader.f32(), reader.f32(), reader.f32(), reader.f32() };
		vehicle.velocity = { reader.f32(), reader.f32(), reader.f32() };
		vehicle.spin = { reader.f32(), reader.f32(), reader.f32() };

		for (auto& compressed : vehicle.compression)
		{
			compressed = reader.f32();
		}

		vehicle.steer = reader.f32();
		vehicle.rotor_speed = reader.f32();
		vehicle.engine = reader.f32();
		vehicle.health = reader.f32();
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::adopt(structures::vehicle_s& vehicle, const structures::vehicle_s& source)
	{
		vehicle.kind = source.kind;
		vehicle.position = source.position;
		vehicle.orientation = source.orientation;
		vehicle.velocity = source.velocity;
		vehicle.spin = source.spin;
		vehicle.steer = source.steer;
		vehicle.rotor_speed = source.rotor_speed;
		vehicle.engine = source.engine;
		vehicle.health = source.health;
		vehicle.asleep = false;
		vehicle.still = 0.0f;

		std::copy(std::begin(source.compression), std::end(source.compression), std::begin(vehicle.compression));
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::write(stream_writer_c& writer, structures::vec3_s viewer, std::uint32_t driven)
	{
		thread_local std::vector<std::pair<std::float_t, std::uint32_t>> nearby;

		nearby.clear();

		for (auto index{ 0u }; index < list.size(); index++)
		{
			if (const auto gap{ mathematics.distance(list[index].position, viewer) }; gap < vehicle_sync_range && list[index].id != driven)
			{
				nearby.push_back({ gap, index });
			}
		}

		std::sort(nearby.begin(), nearby.end());

		const auto count{ std::min<std::size_t>({ nearby.size(), static_cast<std::size_t>(vehicle_snapshot_count), writer.remaining() > 1u ? static_cast<std::size_t>((writer.remaining() - 1u) / vehicle_bytes) : 0u }) };

		writer.u8(static_cast<std::uint8_t>(count));

		for (auto entry{ 0u }; entry < count; entry++)
		{
			const auto& vehicle{ list[nearby[entry].second] };
			const auto quat{ vehicle.orientation.w < 0.0f ? structures::quat_s{ -vehicle.orientation.x, -vehicle.orientation.y, -vehicle.orientation.z, -vehicle.orientation.w } : vehicle.orientation };

			writer.u16(static_cast<std::uint16_t>(vehicle.id));
			writer.u8(static_cast<std::uint8_t>(vehicle.kind | (vehicle.asleep ? 0x80u : 0u) | (vehicle.health <= 0.0f ? 0x40u : 0u)));
			writer.f32(vehicle.position.x);
			writer.f32(vehicle.position.y);
			writer.f32(vehicle.position.z);
			writer.i16(static_cast<std::int16_t>(std::clamp(quat.x, -1.0f, 1.0f) * 32767.0f));
			writer.i16(static_cast<std::int16_t>(std::clamp(quat.y, -1.0f, 1.0f) * 32767.0f));
			writer.i16(static_cast<std::int16_t>(std::clamp(quat.z, -1.0f, 1.0f) * 32767.0f));
			writer.i16(static_cast<std::int16_t>(std::clamp(vehicle.velocity.x * 100.0f, -32767.0f, 32767.0f)));
			writer.i16(static_cast<std::int16_t>(std::clamp(vehicle.velocity.y * 100.0f, -32767.0f, 32767.0f)));
			writer.i16(static_cast<std::int16_t>(std::clamp(vehicle.velocity.z * 100.0f, -32767.0f, 32767.0f)));
			writer.i8(static_cast<std::int8_t>(std::clamp(vehicle.steer * 127.0f, -127.0f, 127.0f)));
			writer.u8(static_cast<std::uint8_t>(mathematics.saturate(vehicle.rotor_speed) * 255.0f));
			writer.u8(static_cast<std::uint8_t>(mathematics.saturate(vehicle.engine) * 255.0f));
			writer.u8(static_cast<std::uint8_t>(std::clamp(vehicle.health / std::max(vehicle_kinds[vehicle.kind].health, 1.0f) * 255.0f, 0.0f, 255.0f)));
			writer.u16(static_cast<std::uint16_t>(vehicle.riders[0] >= 0 ? vehicle.riders[0] : 0xFFFF));
			writer.u16(static_cast<std::uint16_t>(vehicle.riders[1] >= 0 ? vehicle.riders[1] : 0xFFFF));
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::read(stream_reader_c& reader, std::double_t time)
	{
		const auto count{ reader.u8() };

		for (auto entry{ 0u }; entry < count && reader.overflow == false; entry++)
		{
			const auto id{ static_cast<std::uint32_t>(reader.u16()) };
			const auto packed{ reader.u8() };
			const structures::vec3_s position{ reader.f32(), reader.f32(), reader.f32() };
			const auto qx{ static_cast<std::float_t>(reader.i16()) / 32767.0f };
			const auto qy{ static_cast<std::float_t>(reader.i16()) / 32767.0f };
			const auto qz{ static_cast<std::float_t>(reader.i16()) / 32767.0f };
			const structures::vec3_s velocity{ static_cast<std::float_t>(reader.i16()) / 100.0f, static_cast<std::float_t>(reader.i16()) / 100.0f, static_cast<std::float_t>(reader.i16()) / 100.0f };
			const auto steer{ static_cast<std::float_t>(reader.i8()) / 127.0f };
			const auto rotor_speed{ static_cast<std::float_t>(reader.u8()) / 255.0f };
			const auto engine{ static_cast<std::float_t>(reader.u8()) / 255.0f };
			const auto health{ static_cast<std::float_t>(reader.u8()) / 255.0f };
			const auto first{ reader.u16() };
			const auto second{ reader.u16() };
			const auto kind{ std::min<std::uint32_t>(packed & 0x3Fu, structures::vehicle_kind_count - 1u) };

			if (reader.overflow == false)
			{
				auto vehicle{ find(id) };

				if (vehicle == nullptr)
				{
					spawn(kind, position, 0.0f);

					next_id = std::max(next_id, id + 1u);

					vehicle = &list.back();
					vehicle->id = id;
					vehicle->position = position;
					vehicle->shown_position = position;
					vehicle->from_position = position;
					vehicle->to_position = position;
					vehicle->from_time = time - 1.0;
					vehicle->to_time = time - 1.0;
				}

				const auto orientation{ mathematics.quat_normalize({ qx, qy, qz, std::sqrt(std::max(0.0f, 1.0f - qx * qx - qy * qy - qz * qz)) }) };

				vehicle->kind = kind;
				vehicle->asleep = (packed & 0x80u) != 0u;
				vehicle->health = health * vehicle_kinds[kind].health;
				vehicle->riders[0] = first == 0xFFFF ? -1 : static_cast<std::int32_t>(first);
				vehicle->riders[1] = second == 0xFFFF ? -1 : static_cast<std::int32_t>(second);
				vehicle->seen = time;

				if (vehicle->predicted == false && time > vehicle->to_time)
				{
					vehicle->from_position = vehicle->to_position;
					vehicle->from_orientation = vehicle->to_orientation;
					vehicle->from_time = vehicle->to_time;
					vehicle->to_position = position;
					vehicle->to_orientation = orientation;
					vehicle->to_time = time;
					vehicle->velocity = velocity;
					vehicle->shown_velocity = velocity;
					vehicle->steer = steer;
					vehicle->rotor_speed = rotor_speed;
					vehicle->engine = engine;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::update(std::float_t delta, std::double_t render_time, bool mirrored)
	{
		const auto alpha{ mathematics.saturate(player.accumulator / tick_interval) };
		const auto riding{ (player.state.flags & structures::movement_seated) ? player.state.vehicle : 0u };

		if (mirrored)
		{
			list.erase(std::remove_if(list.begin(), list.end(), [&](const structures::vehicle_s& vehicle) { return vehicle.id != riding && render_time - vehicle.seen > vehicle_stale_time; }), list.end());
		}

		for (auto& vehicle : list)
		{
			vehicle.predicted = riding == vehicle.id && player.state.seat == 0u;

			if (mirrored && vehicle.predicted == false)
			{
				const auto span{ vehicle.to_time - vehicle.from_time };
				const auto blend{ span > 0.0001 ? static_cast<std::float_t>(std::clamp((render_time - vehicle.from_time) / span, 0.0, 1.5)) : 1.0f };

				vehicle.shown_position = mathematics.lerp(vehicle.from_position, vehicle.to_position, blend);
				vehicle.shown_orientation = mathematics.quat_nlerp(vehicle.from_orientation, vehicle.to_orientation, std::min(blend, 1.0f));
				vehicle.position = vehicle.shown_position;
				vehicle.orientation = vehicle.shown_orientation;
				vehicle.rotor = std::fmod(vehicle.rotor + vehicle.rotor_speed * vehicle_rotor_turns * two_pi * delta, two_pi * 64.0f);

				for (auto wheel{ 0u }; wheel < 4u; wheel++)
				{
					vehicle.spun[wheel] = std::fmod(vehicle.spun[wheel] + mathematics.dot(vehicle.shown_velocity, mathematics.quat_rotate(vehicle.orientation, { 0.0f, 0.0f, 1.0f })) / std::max(vehicle_kinds[vehicle.kind].wheel_radius, 0.1f) * delta, two_pi);
					vehicle.compression[wheel] = vehicle_kinds[vehicle.kind].travel * 0.5f;
				}
			}

			else if (vehicle.predicted)
			{
				vehicle.error = vehicle.error * std::max(0.0f, 1.0f - delta * 8.0f);
				vehicle.shown_position = mathematics.lerp(vehicle.tick_position, vehicle.position, alpha) + vehicle.error;
				vehicle.shown_orientation = mathematics.quat_nlerp(vehicle.tick_orientation, vehicle.orientation, alpha);
				vehicle.shown_velocity = vehicle.velocity;
			}

			else
			{
				vehicle.shown_position = vehicle.position;
				vehicle.shown_orientation = vehicle.orientation;
				vehicle.shown_velocity = vehicle.velocity;
			}

			present(vehicle, delta);

			if (vehicle_kinds[vehicle.kind].mode == structures::vehicle_mode_hooves)
			{
				gait(vehicle, delta);
			}
		}

		std::erase_if(mounts, [&](const std::pair<const std::uint32_t, structures::animal_s>& entry) { return find(entry.first) == nullptr; });

		update_movers();

		sounds(delta);
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::gait(structures::vehicle_s& vehicle, std::float_t delta)
	{
		const auto ahead{ mathematics.quat_rotate(vehicle.shown_orientation, { 0.0f, 0.0f, 1.0f }) };

		auto& proxy{ mounts[vehicle.id] };

		proxy.species = structures::species_horse;
		proxy.id = static_cast<std::uint16_t>(vehicle.id);
		proxy.alive = true;
		proxy.state = structures::animal_idle;
		proxy.shown = vehicle.shown_position;
		proxy.shown_yaw = std::atan2(ahead.x, ahead.z);
		proxy.shown_speed = mathematics.damp(proxy.shown_speed, mathematics.length(structures::vec3_s{ vehicle.shown_velocity.x, 0.0f, vehicle.shown_velocity.z }), 8.0f, delta);
		proxy.position = proxy.shown;
		proxy.yaw = proxy.shown_yaw;

		if (fauna.bodies[structures::species_horse] && mathematics.distance(proxy.shown, renderer.camera.position) < fauna_draw_distance)
		{
			fauna.animate(proxy, delta);

			proxy.world = mathematics.multiply(mathematics.rotation_y(species_table[structures::species_horse].facing), vehicle.world);
			proxy.previous_world = mathematics.multiply(mathematics.rotation_y(species_table[structures::species_horse].facing), vehicle.previous_world);
		}

		else
		{
			proxy.frames = 0u;
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::present(structures::vehicle_s& vehicle, std::float_t delta)
	{
		const auto& definition{ vehicle_kinds[vehicle.kind] };

		vehicle.previous_world = vehicle.world;
		vehicle.world = pose(vehicle.shown_position, vehicle.shown_orientation);
		vehicle.previous_world = vehicle.previous_world.m[3][3] != 0.0f ? vehicle.previous_world : vehicle.world;
		vehicle.puff -= delta;

		if (vehicle.puff <= 0.0f && mathematics.distance(vehicle.shown_position, renderer.camera.position) < vehicle_effect_range)
		{
			const auto up{ vehicle.world.row3(1u) };
			const auto behind{ vehicle.world.row3(2u) * -1.0f };
			const auto speed{ mathematics.length(vehicle.shown_velocity) };
			const auto damaged{ vehicle.health < definition.health * vehicle_smoke_health && definition.mode != structures::vehicle_mode_hooves };

			vehicle.puff = mathematics.lerp(0.32f, 0.07f, mathematics.saturate(vehicle.engine)) * (0.8f + random() * 0.4f);

			if (vehicle.engine > 0.05f && vehicle.health > 0.0f)
			{
				particles.emit(structures::particle_smoke, mathematics.transform_point(definition.exhaust, vehicle.world), up * 0.9f + behind * 0.4f + vehicle.shown_velocity * 0.5f, 0.12f, 1u, false);
			}

			if (damaged)
			{
				particles.emit(structures::particle_smoke, mathematics.transform_point(definition.hull_center + structures::vec3_s{ 0.0f, definition.hull_half.y, definition.hull_half.z * 0.5f }, vehicle.world), { 0.3f, 1.6f, 0.2f }, 0.35f, vehicle.health <= 0.0f ? 3u : 1u, false);
			}

			if (vehicle.health <= 0.0f && definition.mode != structures::vehicle_mode_hooves)
			{
				particles.emit(structures::particle_fire, mathematics.transform_point(definition.hull_center, vehicle.world), { 0.0f, 1.2f, 0.0f }, 0.6f, 2u, false);
			}

			if (definition.wheel_count && speed > vehicle_dust_speed)
			{
				for (auto wheel{ 2u }; wheel < 4u && wheel < definition.wheel_count; wheel++)
				{
					if (vehicle.compression[wheel] > 0.01f)
					{
						particles.emit(structures::particle_dust, mathematics.transform_point(definition.wheels[wheel] - structures::vec3_s{ 0.0f, definition.wheel_radius * 0.8f, 0.0f }, vehicle.world), behind * (speed * 0.15f) + structures::vec3_s{ 0.0f, 0.6f, 0.0f }, 0.5f, 1u, false);
					}
				}
			}

			if (definition.mode == structures::vehicle_mode_rotor && vehicle.rotor_speed > 0.5f)
			{
				const auto hub{ mathematics.transform_point(definition.rotor_hub, vehicle.world) };
				const auto slot{ index_of(vehicle.id) };

				world.ignored = slot >= 0 ? vehicle_owner_base + static_cast<std::uint32_t>(slot) : UINT32_MAX;

				const auto below{ world.trace(hub, hub - structures::vec3_s{ 0.0f, vehicle_wash_height, 0.0f }, { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };

				world.ignored = UINT32_MAX;

				if (below.hit && below.start_solid == false)
				{
					const auto angle{ random() * two_pi };
					const structures::vec3_s outward{ std::sin(angle), 0.0f, std::cos(angle) };

					particles.emit(structures::particle_dust, below.end + outward * (definition.rotor_radius * (0.4f + random() * 0.5f)) + structures::vec3_s{ 0.0f, 0.2f, 0.0f }, outward * (5.0f * (1.0f - below.fraction)) + structures::vec3_s{ 0.0f, 0.5f, 0.0f }, 0.6f, 2u, false);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::sounds(std::float_t delta)
	{
		const auto ear{ mixer.listener_position };

		auto engine_index{ -1 };
		auto rotor_index{ -1 };

		for (auto index{ 0u }; index < list.size(); index++)
		{
			const auto& vehicle{ list[index] };
			const auto close{ mathematics.distance(vehicle.shown_position, ear) };

			if (vehicle_kinds[vehicle.kind].mode == structures::vehicle_mode_wheels && vehicle.engine > 0.05f && (engine_index < 0 || close < mathematics.distance(list[engine_index].shown_position, ear)))
			{
				engine_index = static_cast<std::int32_t>(index);
			}

			if (vehicle_kinds[vehicle.kind].mode == structures::vehicle_mode_rotor && vehicle.rotor_speed > 0.02f && (rotor_index < 0 || close < mathematics.distance(list[rotor_index].shown_position, ear)))
			{
				rotor_index = static_cast<std::int32_t>(index);
			}
		}

		if (engine_index >= 0)
		{
			const auto& vehicle{ list[engine_index] };

			mixer.drone(structures::drone_vehicle_engine, mathematics.transform_point(vehicle_kinds[vehicle.kind].exhaust, vehicle.world), vehicle.shown_velocity, 0.35f + 0.65f * vehicle.engine, 0.7f + 0.9f * vehicle.engine, vehicle_engine_reference);
		}

		if (rotor_index >= 0)
		{
			const auto& vehicle{ list[rotor_index] };

			mixer.drone(structures::drone_vehicle_rotor, mathematics.transform_point(vehicle_kinds[vehicle.kind].rotor_hub, vehicle.world), vehicle.shown_velocity, vehicle.rotor_speed, 0.45f + 0.65f * vehicle.rotor_speed + 0.12f * vehicle.engine, vehicle_rotor_reference);
		}

		static_cast<void>(delta);
	}
	/*
	//=====================================================================================
	*/
	void vehicles_c::submit()
	{
		const auto camera{ renderer.camera.position };
		const auto dusk{ atmosphere.enabled ? mathematics.smoothstep(train_dusk_start, train_dusk_end, atmosphere.sun.y) : 0.0f };

		for (const auto& vehicle : list)
		{
			const auto& definition{ vehicle_kinds[vehicle.kind] };
			const auto gap{ mathematics.distance(vehicle.shown_position, camera) };
			const auto flags{ gap > vehicle_shadow_distance ? static_cast<std::uint32_t>(structures::draw_flag_no_shadow) : 0u };
			const auto detailed{ gap < vehicle_detail_distance || distant[vehicle.kind].index_count == 0u };
			const auto skin{ vehicle.health <= 0.0f ? static_cast<std::float_t>(burnt) : -1.0f };

			if (definition.mode == structures::vehicle_mode_hooves)
			{
				if (const auto proxy{ mounts.find(vehicle.id) }; proxy != mounts.end() && proxy->second.frames && fauna.bodies[structures::species_horse])
				{
					const auto* character{ gap > fauna_lod_distance && fauna.distant[structures::species_horse] ? fauna.distant[structures::species_horse] : fauna.bodies[structures::species_horse] };

					renderer.submit_skinned(character, proxy->second.world, proxy->second.previous_world, proxy->second.palette.data(), proxy->second.previous_palette.data(), structures::draw_flag_character, 0.0f);
				}

				continue;
			}

			if (vehicle.riders[0] >= 0 && vehicle.health > 0.0f && dusk > 0.01f)
			{
				for (const auto& lamp : definition.lights)
				{
					renderer.add_spot(mathematics.transform_point(lamp, vehicle.world), vehicle_headlight_radius, vehicle_headlight_color * dusk, mathematics.normalize(vehicle.world.row3(2u) - vehicle.world.row3(1u) * vehicle_headlight_tilt), vehicle_headlight_cosine);
				}
			}

			if (detailed == false)
			{
				renderer.submit(&distant[vehicle.kind], vehicle.world, vehicle.previous_world, skin, flags);

				continue;
			}

			renderer.submit(&bodies[vehicle.kind], vehicle.world, vehicle.previous_world, skin, flags);

			for (auto wheel{ 0u }; wheel < definition.wheel_count && wheel < 4u; wheel++)
			{
				if (wheels[vehicle.kind][wheel].index_count)
				{
					const auto pivot{ pivots[vehicle.kind][wheel] };
					const auto lift{ vehicle.compression[wheel] - definition.travel * 0.5f };
					const auto local{ mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-pivot), mathematics.rotation_x(vehicle.spun[wheel])), mathematics.rotation_y(wheel < 2u ? vehicle.steer : 0.0f)), mathematics.translation(pivot + structures::vec3_s{ 0.0f, lift, 0.0f })) };

					renderer.submit(&wheels[vehicle.kind][wheel], mathematics.multiply(local, vehicle.world), mathematics.multiply(local, vehicle.previous_world), skin, flags);
				}
			}

			if (steering[vehicle.kind].index_count)
			{
				const auto hub{ wheel_hub[vehicle.kind] };
				const auto local{ mathematics.multiply(mathematics.multiply(mathematics.translation(-hub), mathematics.rotation(mathematics.quat_axis_angle(rover_steering_axis, vehicle.steer * 2.6f))), mathematics.translation(hub)) };

				renderer.submit(&steering[vehicle.kind], mathematics.multiply(local, vehicle.world), mathematics.multiply(local, vehicle.previous_world), -1.0f, flags);
			}

			for (auto rotor{ 0u }; rotor < 2u; rotor++)
			{
				if (rotors[vehicle.kind][rotor].index_count)
				{
					const auto hub{ hubs[vehicle.kind][rotor] };
					const auto spin{ rotor == 0u ? mathematics.rotation_y(vehicle.rotor) : mathematics.rotation_x(vehicle.rotor * vehicle_tail_ratio) };
					const auto local{ mathematics.multiply(mathematics.multiply(mathematics.translation(-hub), spin), mathematics.translation(hub)) };

					renderer.submit(&rotors[vehicle.kind][rotor], mathematics.multiply(local, vehicle.world), mathematics.multiply(local, vehicle.previous_world), skin, flags);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t vehicles_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
