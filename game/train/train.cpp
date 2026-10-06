
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	train_c train;

	void train_c::create()
	{
		clear();

		for (auto index{ 0u }; index < maps.paths.size() && line < 0; index++)
		{
			line = maps.paths[index].kind == structures::route_rail && maps.paths[index].closed ? static_cast<std::int32_t>(index) : -1;
		}

		if (line >= 0)
		{
			const auto& points{ maps.paths[line].points };

			auto behind{ 0.0f };
			auto movers{ 0u };

			reach.assign(points.size() + 1u, 0.0f);

			for (auto index{ 0u }; index < points.size(); index++)
			{
				reach[index + 1u] = reach[index] + mathematics.distance(points[index], points[(index + 1u) % points.size()]);
			}

			length = reach.back();

			timetable();

			if (gpu.device)
			{
				wheels();
			}

			for (auto vehicle{ 0u }; vehicle < structures::train_vehicle_count; vehicle++)
			{
				shape(vehicle);

				if (gpu.device)
				{
					build(vehicle);
				}
			}

			for (auto index{ 0u }; index < std::size(train_consist); index++)
			{
				const auto& kind{ train_vehicles[train_consist[index]] };

				offsets[index] = behind + kind.length * 0.5f;
				first_mover[index] = movers;

				behind += kind.length + train_coupling;
				movers += static_cast<std::uint32_t>(boxes[train_consist[index]].size());
			}

			extent = behind;
			ready = legs.size() > 0u && length > 1.0f;

			place(0.0);

			logger.write("train: %.0f m line, %zu stops, lap %.0f s, %u collision boxes", length, legs.size(), cycle, movers);

			for (const auto& leg : legs)
			{
				const auto stop{ point(leg.start_distance) };

				logger.write("train: stop at %.0f m (%.0f %.1f %.0f), departs %.0f s, next leg %.0f m in %.0f s", leg.start_distance, stop.x, stop.y, stop.z, leg.start_time, leg.length, leg.travel_time);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void train_c::clear()
	{
		for (auto vehicle{ 0u }; vehicle < structures::train_vehicle_count; vehicle++)
		{
			functions::release(bodies[vehicle].vertex_buffer);
			functions::release(bodies[vehicle].index_buffer);
			functions::release(distant[vehicle].vertex_buffer);
			functions::release(distant[vehicle].index_buffer);

			bodies[vehicle] = {};
			distant[vehicle] = {};

			boxes[vehicle].clear();
			lamps[vehicle].clear();
		}

		functions::release(wheel.vertex_buffer);
		functions::release(wheel.index_buffer);
		functions::release(wheel_far.vertex_buffer);
		functions::release(wheel_far.index_buffer);

		wheel = {};
		wheel_far = {};

		reach.clear();
		legs.clear();

		line = -1;
		length = 0.0f;
		extent = 0.0f;
		cycle = 0.0f;
		throttle = 0.0f;
		placed = -1.0;
		ready = false;
		history = false;
		squealed = false;
		halted = true;
	}
	/*
	//=====================================================================================
	*/
	void train_c::timetable()
	{
		std::vector<std::float_t> stops;

		for (const auto& station : maps.stations)
		{
			stops.push_back(reach[std::min(static_cast<std::size_t>(station.index), reach.size() - 2u)]);
		}

		std::sort(stops.begin(), stops.end());

		auto time{ 0.0f };

		for (auto index{ 0u }; index < stops.size(); index++)
		{
			const auto span{ (index + 1u < stops.size() ? stops[index + 1u] : stops[0] + length) - stops[index] };
			const auto ramp_length{ std::min(train_cruise * train_cruise / (2.0f * train_acceleration), span * 0.5f) };
			const auto peak{ std::sqrt(2.0f * train_acceleration * ramp_length) };
			const auto ramp_time{ peak / train_acceleration };
			const auto travel_time{ ramp_time * 2.0f + (span - ramp_length * 2.0f) / std::max(peak, 0.1f) };

			legs.push_back({ time, stops[index], span, travel_time, ramp_time, ramp_length, peak });

			time += travel_time + train_dwell;
		}

		cycle = time;
	}
	/*
	//=====================================================================================
	*/
	void train_c::shape(std::uint32_t vehicle)
	{
		const auto& kind{ train_vehicles[vehicle] };
		const auto half{ kind.length * 0.5f };
		const auto side{ kind.width * 0.5f };
		const auto metal{ static_cast<std::uint32_t>(structures::surface_metal) };

		boxes[vehicle].clear();
		lamps[vehicle].clear();

		if (const auto model{ models.find(kind.model) }; model)
		{
			for (const auto& part : model->parts)
			{
				if (std::strncmp(part.name, "col_", 4u) == 0)
				{
					boxes[vehicle].push_back({ (part.bounds_min + part.bounds_max) * 0.5f, (part.bounds_max - part.bounds_min) * 0.5f, maps.surface_named(part.name + 4) });
				}

				else if (std::strncmp(part.name, "light_", 6u) == 0)
				{
					lamps[vehicle].push_back((part.bounds_min + part.bounds_max) * 0.5f);
				}
			}
		}

		if (boxes[vehicle].empty())
		{
			boxes[vehicle].push_back({ { 0.0f, kind.deck * 0.5f, 0.0f }, { side, kind.deck * 0.5f, half - 0.15f }, vehicle == structures::train_vehicle_flat ? static_cast<std::uint32_t>(structures::surface_wood) : metal });

			if (vehicle == structures::train_vehicle_locomotive)
			{
				boxes[vehicle].push_back({ { 0.0f, 1.75f, half * 0.28f }, { side * 0.72f, 0.8f, kind.length * 0.28f }, metal });
				boxes[vehicle].push_back({ { 0.0f, 2.2f, -half * 0.55f }, { side, 1.25f, kind.length * 0.15f }, metal });
			}

			else if (vehicle == structures::train_vehicle_open)
			{
				boxes[vehicle].push_back({ { -side + 0.04f, kind.deck + 0.5f, 0.0f }, { 0.04f, 0.5f, half - 0.15f }, metal });
				boxes[vehicle].push_back({ { side - 0.04f, kind.deck + 0.5f, 0.0f }, { 0.04f, 0.5f, half - 0.15f }, metal });
				boxes[vehicle].push_back({ { 0.0f, kind.deck + 0.5f, half - 0.19f }, { side, 0.5f, 0.04f }, metal });
				boxes[vehicle].push_back({ { 0.0f, kind.deck + 0.5f, -half + 0.19f }, { side, 0.5f, 0.04f }, metal });
			}

			else if (vehicle != structures::train_vehicle_flat)
			{
				boxes[vehicle].push_back({ { 0.0f, (kind.deck + kind.height) * 0.5f, 0.0f }, { side, (kind.height - kind.deck) * 0.5f, half - 0.15f }, metal });
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void train_c::build(std::uint32_t vehicle)
	{
		char far_name[64]{};

		std::snprintf(far_name, sizeof(far_name), "%s_far", train_vehicles[vehicle].model);

		if (const auto model{ models.find(train_vehicles[vehicle].model) }; model)
		{
			shop.clear();
			shop.append(*model, 0u, static_cast<std::uint32_t>(model->indices.size()), mathematics.identity());
			shop.upload(bodies[vehicle]);

			if (const auto far_model{ models.find(far_name) }; far_model)
			{
				shop.clear();
				shop.append(*far_model, 0u, static_cast<std::uint32_t>(far_model->indices.size()), mathematics.identity());
				shop.upload(distant[vehicle]);
			}
		}

		else
		{
			mock(vehicle);
		}
	}
	/*
	//=====================================================================================
	*/
	void train_c::wheels()
	{
		char far_name[64]{};

		std::snprintf(far_name, sizeof(far_name), "%s_far", train_wheelset_model);

		if (const auto model{ models.find(train_wheelset_model) }; model)
		{
			shop.clear();
			shop.append(*model, 0u, static_cast<std::uint32_t>(model->indices.size()), mathematics.identity());
			shop.upload(wheel);

			if (const auto far_model{ models.find(far_name) }; far_model)
			{
				shop.clear();
				shop.append(*far_model, 0u, static_cast<std::uint32_t>(far_model->indices.size()), mathematics.identity());
				shop.upload(wheel_far);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void train_c::mock(std::uint32_t vehicle)
	{
		const auto& kind{ train_vehicles[vehicle] };
		const auto identity{ mathematics.quat_identity() };
		const auto half{ kind.length * 0.5f };

		shop.clear();
		shop.set_material(structures::material_metal_rust);
		shop.box({ 0.0f, 0.78f, 0.0f }, { kind.width * 0.86f, 0.32f, kind.length - 0.5f }, identity);

		for (auto axle{ 0u }; axle < kind.axles && wheel.index_count == 0u; axle++)
		{
			shop.set_material(structures::material_steel);
			shop.cylinder({ -0.86f, train_wheel_radius, kind.axle_offsets[axle] }, { 1.0f, 0.0f, 0.0f }, train_wheel_radius, 0.13f, 20u, true);
			shop.cylinder({ 0.73f, train_wheel_radius, kind.axle_offsets[axle] }, { 1.0f, 0.0f, 0.0f }, train_wheel_radius, 0.13f, 20u, true);
			shop.cylinder({ -0.8f, train_wheel_radius, kind.axle_offsets[axle] }, { 1.0f, 0.0f, 0.0f }, 0.07f, 1.6f, 10u, false);
		}

		for (auto end{ -1.0f }; end <= 1.0f; end += 2.0f)
		{
			shop.set_material(structures::material_metal_rust);
			shop.cylinder({ -0.62f, 1.05f, end * (half - 0.25f) }, { 0.0f, 0.0f, end }, 0.17f, 0.4f, 12u, true);
			shop.cylinder({ 0.62f, 1.05f, end * (half - 0.25f) }, { 0.0f, 0.0f, end }, 0.17f, 0.4f, 12u, true);
		}

		shop.set_material(kind.material);

		if (vehicle == structures::train_vehicle_locomotive)
		{
			shop.box({ 0.0f, 1.75f, half * 0.28f }, { kind.width * 0.72f, 1.6f, kind.length * 0.56f }, identity);
			shop.box({ 0.0f, 2.2f, -half * 0.55f }, { kind.width, 2.5f, kind.length * 0.3f }, identity);
			shop.set_material(structures::material_steel);
			shop.cylinder({ 0.0f, 2.55f, half * 0.6f }, { 0.0f, 1.0f, 0.0f }, 0.13f, 0.6f, 12u, true);
		}

		else if (vehicle == structures::train_vehicle_flat)
		{
			shop.set_material(structures::material_plywood);
			shop.box({ 0.0f, kind.deck - 0.06f, 0.0f }, { kind.width, 0.12f, kind.length - 0.3f }, identity);
		}

		else if (vehicle == structures::train_vehicle_open)
		{
			shop.box({ 0.0f, kind.deck - 0.06f, 0.0f }, { kind.width, 0.12f, kind.length - 0.3f }, identity);
			shop.box({ -kind.width * 0.5f + 0.04f, kind.deck + 0.5f, 0.0f }, { 0.08f, 1.0f, kind.length - 0.3f }, identity);
			shop.box({ kind.width * 0.5f - 0.04f, kind.deck + 0.5f, 0.0f }, { 0.08f, 1.0f, kind.length - 0.3f }, identity);
			shop.box({ 0.0f, kind.deck + 0.5f, half - 0.19f }, { kind.width, 1.0f, 0.08f }, identity);
			shop.box({ 0.0f, kind.deck + 0.5f, -half + 0.19f }, { kind.width, 1.0f, 0.08f }, identity);
		}

		else
		{
			shop.box({ 0.0f, (kind.deck + kind.height) * 0.5f, 0.0f }, { kind.width, kind.height - kind.deck, kind.length - 0.3f }, identity);
		}

		shop.compute_tangents(0u, 0u);
		shop.upload(bodies[vehicle]);
	}
	/*
	//=====================================================================================
	*/
	std::double_t train_c::travel(std::double_t time, std::float_t& rate)
	{
		const auto lap{ static_cast<std::double_t>(std::max(cycle, 1.0f)) };
		const auto local{ std::fmod(std::fmod(time, lap) + lap, lap) };
		const auto pull{ static_cast<std::double_t>(train_acceleration) };

		auto result{ 0.0 };

		rate = 0.0f;

		for (const auto& leg : legs)
		{
			if (local >= leg.start_time)
			{
				const auto elapsed{ local - leg.start_time };
				const auto remaining{ leg.travel_time - elapsed };

				rate = static_cast<std::float_t>(elapsed < leg.ramp_time ? pull * elapsed : (remaining > leg.ramp_time ? leg.peak : (remaining > 0.0 ? pull * remaining : 0.0)));
				result = leg.start_distance + (elapsed < leg.ramp_time ? 0.5 * pull * elapsed * elapsed : (remaining > leg.ramp_time ? leg.ramp_length + leg.peak * (elapsed - leg.ramp_time) : (remaining > 0.0 ? leg.length - 0.5 * pull * remaining * remaining : leg.length)));
			}
		}

		return std::fmod(result, static_cast<std::double_t>(std::max(length, 1.0f)));
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s train_c::point(std::double_t along)
	{
		const auto& points{ maps.paths[line].points };
		const auto lap{ static_cast<std::double_t>(length) };
		const auto wrapped{ std::fmod(std::fmod(along, lap) + lap, lap) };
		const auto upper{ std::upper_bound(reach.begin(), reach.end(), static_cast<std::float_t>(wrapped)) };
		const auto index{ static_cast<std::size_t>(std::clamp<std::ptrdiff_t>(upper - reach.begin() - 1, 0, static_cast<std::ptrdiff_t>(points.size()) - 1)) };
		const auto span{ static_cast<std::double_t>(reach[index + 1u] - reach[index]) };

		return mathematics.lerp(points[index], points[(index + 1u) % points.size()], span > 0.0001 ? static_cast<std::float_t>(std::clamp((wrapped - reach[index]) / span, 0.0, 1.0)) : 0.0f);
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s train_c::pose(std::double_t time, std::uint32_t index)
	{
		auto rate{ 0.0f };

		const auto& kind{ train_vehicles[train_consist[index]] };
		const auto middle{ travel(time, rate) - offsets[index] };
		const auto front{ point(middle + kind.wheelbase * 0.5f) };
		const auto rear{ point(middle - kind.wheelbase * 0.5f) };
		const auto forward{ mathematics.normalize(front - rear) };
		const auto right{ mathematics.normalize(mathematics.cross({ 0.0f, 1.0f, 0.0f }, forward)) };

		return mathematics.basis(right, mathematics.cross(forward, right), forward, (front + rear) * 0.5f + structures::vec3_s{ 0.0f, rail_head, 0.0f });
	}
	/*
	//=====================================================================================
	*/
	void train_c::place(std::double_t time)
	{
		if (ready && time != placed)
		{
			for (auto index{ 0u }; index < std::size(train_consist); index++)
			{
				const auto& shapes{ boxes[train_consist[index]] };

				posed[index] = pose(time, index);

				for (auto box{ 0u }; box < shapes.size(); box++)
				{
					world.set_mover(first_mover[index] + box, posed[index], shapes[box].center, shapes[box].half, shapes[box].surface, index);
				}
			}

			placed = time;
		}
	}
	/*
	//=====================================================================================
	*/
	bool train_c::close(structures::vec3_s position, std::double_t time)
	{
		auto rate{ 0.0f };

		return ready && mathematics.distance(point(travel(time, rate) - offsets[std::size(train_consist) / 2u]), position) < train_reach;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s train_c::velocity(std::uint32_t index, structures::vec3_s position, std::double_t time)
	{
		const auto local{ mathematics.transform_point(position, mathematics.inverse(pose(time, index))) };

		return (mathematics.transform_point(local, pose(time + train_velocity_step, index)) - mathematics.transform_point(local, pose(time - train_velocity_step, index))) / static_cast<std::float_t>(train_velocity_step * 2.0);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t train_c::aboard(structures::vec3_s position, std::double_t time, structures::vec3_s& local)
	{
		auto result{ 0u };

		for (auto index{ 0u }; index < std::size(train_consist) && ready && result == 0u; index++)
		{
			const auto& kind{ train_vehicles[train_consist[index]] };
			const auto spot{ mathematics.transform_point(position, mathematics.inverse(pose(time, index))) };

			if (std::fabs(spot.x) < kind.width * 0.5f + train_ride_margin && spot.y > -0.5f && spot.y < kind.height + train_ride_headroom && std::fabs(spot.z) < kind.length * 0.5f + train_ride_margin)
			{
				local = spot;
				result = index + 1u;
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::float_t train_c::strike(const structures::movement_state_s& state, std::double_t time, structures::vec3_s& shove)
	{
		auto rate{ 0.0f };
		auto blow{ 0.0f };

		if (ready && state.platform == 0u)
		{
			travel(time, rate);

			if (rate > train_strike_safe)
			{
				const auto& kind{ train_vehicles[train_consist[0]] };
				const auto lead{ pose(time, 0u) };
				const auto spot{ mathematics.transform_point(state.position + structures::vec3_s{ 0.0f, state.height * 0.5f, 0.0f }, mathematics.inverse(lead)) };

				if (std::fabs(spot.x) < kind.width * 0.5f + player_half_width && spot.y > -0.4f && spot.y < kind.height + state.height * 0.5f && spot.z > kind.length * 0.5f - 0.6f && spot.z < kind.length * 0.5f + train_strike_reach)
				{
					blow = maximum_health * mathematics.saturate((rate - train_strike_safe) / (train_strike_lethal - train_strike_safe));
					shove = lead.row3(2u) * (rate * 1.25f) + structures::vec3_s{ 0.0f, 3.5f, 0.0f };
				}
			}
		}

		return blow;
	}
	/*
	//=====================================================================================
	*/
	void train_c::advance(std::float_t delta)
	{
		clock = client.connected() ? client.server_clock : clock + static_cast<std::double_t>(delta);

		place(clock);
	}
	/*
	//=====================================================================================
	*/
	void train_c::update(std::float_t delta)
	{
		if (ready)
		{
			trailing = head;
			head = travel(clock, speed);

			std::copy(std::begin(placements), std::end(placements), std::begin(previous));

			for (auto index{ 0u }; index < std::size(train_consist); index++)
			{
				placements[index] = pose(clock, index);
			}

			if (history == false)
			{
				std::copy(std::begin(placements), std::end(placements), std::begin(previous));

				trailing = head;
				history = true;
			}

			place(clock);

			sounds(delta);
		}
	}
	/*
	//=====================================================================================
	*/
	void train_c::sounds(std::float_t delta)
	{
		auto coming{ 0.0f };

		travel(clock + 0.25, coming);

		const auto lap{ static_cast<std::double_t>(std::max(cycle, 1.0f)) };
		const auto local{ static_cast<std::float_t>(std::fmod(std::fmod(clock, lap) + lap, lap)) };
		const auto steady{ std::fabs(clock - heard) < 1.0 };
		const auto rate{ speed / train_cruise };
		const auto pulling{ coming > speed + 0.02f };
		const auto braking{ coming < speed - 0.02f };
		const auto motion{ placements[0].row3(2u) * speed };
		const auto cab{ placements[0].row3(3u) + structures::vec3_s{ 0.0f, 1.7f, 0.0f } };
		const auto ear{ mixer.listener_position };

		auto nearest{ cab };

		throttle = mathematics.damp(throttle, pulling ? 1.0f : (speed > 0.5f && braking == false ? 0.5f : 0.0f), 1.4f, delta);

		for (auto index{ 0u }; index < std::size(train_consist); index++)
		{
			const auto& kind{ train_vehicles[train_consist[index]] };
			const auto center{ placements[index].row3(3u) };
			const auto axis{ placements[index].row3(2u) };
			const auto spot{ center + axis * std::clamp(mathematics.dot(ear - center, axis), -kind.length * 0.5f, kind.length * 0.5f) + structures::vec3_s{ 0.0f, 0.5f, 0.0f } };
			const auto middle{ head - offsets[index] };

			nearest = index == 0u || mathematics.distance(spot, ear) < mathematics.distance(nearest, ear) ? spot : nearest;

			for (auto axle{ 0u }; axle < kind.axles; axle++)
			{
				const auto along{ middle + kind.axle_offsets[axle] };
				const auto joint{ static_cast<std::int32_t>(std::fmod(std::fmod(along, static_cast<std::double_t>(length)) + length, static_cast<std::double_t>(length)) / train_joint_spacing) };

				if (joint != joints[index][axle] && steady && speed > 0.4f)
				{
					if (const auto contact{ point(along) + structures::vec3_s{ 0.0f, rail_head, 0.0f } }; mathematics.distance(contact, ear) < train_clack_range)
					{
						mixer.play(structures::sound_train_clack, contact, 0.3f + 0.55f * rate, 0.9f + mixer.random() * 0.2f);
					}
				}

				joints[index][axle] = joint;
			}
		}

		mixer.drone(structures::drone_engine, cab, motion, 0.45f + 0.55f * throttle, 0.8f + 0.4f * throttle + 0.2f * rate, train_engine_reference);
		mixer.drone(structures::drone_roll, nearest, motion, std::pow(mathematics.saturate(rate), 1.3f), 0.6f + 0.55f * rate, train_roll_reference);
		mixer.drone(structures::drone_horn, cab + placements[0].row3(2u) * 2.5f, motion, 1.0f, 1.0f, train_horn_reference);
		mixer.drone(structures::drone_brake, nearest, motion, 0.8f, 0.9f + 0.2f * mathematics.saturate(speed / train_brake_speed), train_brake_reference);

		for (const auto& leg : legs)
		{
			if (steady && crossed(std::fmod(leg.start_time - train_horn_lead + cycle, cycle), phase, local))
			{
				mixer.blast(structures::drone_horn, structures::sound_train_horn);
				mixer.play(structures::sound_train_hiss, cab, 0.7f, 1.1f);
			}

			if (steady && leg.travel_time > train_horn_approach * 2.0f && crossed(std::fmod(leg.start_time + leg.travel_time - train_horn_approach, cycle), phase, local))
			{
				mixer.blast(structures::drone_horn, structures::sound_train_horn);
			}
		}

		for (const auto& crossing : maps.crossings)
		{
			if (steady && speed > train_horn_moving && crossed(std::fmod(crossing.along - train_horn_crossing + length, length), static_cast<std::float_t>(trailing), static_cast<std::float_t>(head)))
			{
				mixer.blast(structures::drone_horn, structures::sound_train_horn);
			}
		}

		if (braking && speed < train_brake_speed && speed > 1.2f && squealed == false)
		{
			mixer.blast(structures::drone_brake, structures::sound_train_brake);

			squealed = true;
		}

		if (speed > train_brake_speed + 1.0f)
		{
			squealed = false;
		}

		if (speed < train_hiss_speed && halted == false && steady)
		{
			mixer.play(structures::sound_train_hiss, cab, 0.85f, 0.95f);
		}

		halted = speed < train_hiss_speed;
		phase = local;
		heard = clock;
	}
	/*
	//=====================================================================================
	*/
	bool train_c::crossed(std::float_t moment, std::float_t from, std::float_t to)
	{
		return from <= to ? (moment > from && moment <= to) : (moment > from || moment <= to);
	}
	/*
	//=====================================================================================
	*/
	void train_c::submit()
	{
		const auto dusk{ atmosphere.enabled ? mathematics.smoothstep(train_dusk_start, train_dusk_end, atmosphere.sun.y) : 0.0f };

		for (auto index{ 0u }; index < std::size(train_consist) && ready; index++)
		{
			const auto vehicle{ train_consist[index] };
			const auto& kind{ train_vehicles[vehicle] };
			const auto gap{ mathematics.distance(placements[index].row3(3u), renderer.camera.position) };
			const auto flags{ gap > train_shadow_distance ? static_cast<std::uint32_t>(structures::draw_flag_no_shadow) : 0u };

			if (gap < train_view_distance)
			{
				renderer.submit(gap > train_detail_distance && distant[vehicle].index_count ? &distant[vehicle] : &bodies[vehicle], placements[index], previous[index], -1.0f, flags);
			}

			for (auto axle{ 0u }; axle < kind.axles && gap < train_wheel_distance && wheel.index_count; axle++)
			{
				const auto seat{ mathematics.translation({ 0.0f, train_wheel_radius, kind.axle_offsets[axle] }) };

				renderer.submit(gap > train_detail_distance && wheel_far.index_count ? &wheel_far : &wheel, mathematics.multiply(mathematics.multiply(mathematics.rotation_x(roll(head - offsets[index])), seat), placements[index]), mathematics.multiply(mathematics.multiply(mathematics.rotation_x(roll(trailing - offsets[index])), seat), previous[index]), -1.0f, flags);
			}

			if (gap < train_light_distance)
			{
				glow(index, train_lights_day + (1.0f - train_lights_day) * dusk);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void train_c::glow(std::uint32_t index, std::float_t shine)
	{
		const auto vehicle{ train_consist[index] };
		const auto& kind{ train_vehicles[vehicle] };
		const auto& placement{ placements[index] };

		for (const auto& lamp : lamps[vehicle])
		{
			const auto spot{ mathematics.transform_point(lamp, placement) };

			if (index == 0u && lamp.z > kind.length * 0.25f)
			{
				renderer.add_spot(spot, train_headlight_radius, train_headlight_color * shine, mathematics.normalize(placement.row3(2u) - placement.row3(1u) * train_headlight_tilt), train_headlight_cosine);
			}

			else
			{
				renderer.add_light(spot, train_lamp_radius, train_lamp_color * shine);
			}
		}

		if (index + 1u == static_cast<std::uint32_t>(std::size(train_consist)))
		{
			renderer.add_light(mathematics.transform_point({ 0.0f, train_tail_height, -kind.length * 0.5f - 0.1f }, placement), train_tail_radius, train_tail_color * shine);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t train_c::roll(std::double_t along)
	{
		return static_cast<std::float_t>(std::fmod(along / static_cast<std::double_t>(train_wheel_radius), static_cast<std::double_t>(two_pi)));
	}
}

//=====================================================================================
