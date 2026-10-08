
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	maps_c maps;

	void maps_c::clear()
	{
		builder.clear();

		world.clear();

		foliage.clear();

		harvest.clear();

		building.clear();

		farming.clear();

		projectiles.clear();

		particles.clear();

		marks.clear();

		spawns.clear();
		depots.clear();
		objectives.clear();
		lights.clear();
		clearings.clear();
		hotspots.clear();
		landmarks.clear();
		roads.clear();
		footprints.clear();
		stations.clear();
		crossings.clear();
		building_species.clear();

		std::fill(std::begin(crates), std::end(crates), UINT32_MAX);

		info = {};
		radio_ready = false;
	}
	/*
	//=====================================================================================
	*/
	bool maps_c::load(const char* name)
	{
		clear();

		if (std::strcmp(name, "test") == 0)
		{
			build_test_scene();
		}

		else if (std::strcmp(name, "island") == 0)
		{
			build_island();
		}

		else
		{
			build_deck_zero();
		}

		finish();

		return spawns.size() > 0u;
	}
	/*
	//=====================================================================================
	*/
	void maps_c::finish()
	{
		world.kill_height = info.kill_height;

		world.build();

		materials.upload();

		renderer.set_world();

		renderer.set_lights(lights);

		renderer.fog = info.fog;

		water.enabled = info.water;
		water.height = info.water_height;

		sky.select(info.sky);

		sky.set_rotation(info.sky_rotation);

		if (info.terrain && terrain.enabled == false)
		{
			terrain.load();
		}

		else if (info.terrain == false)
		{
			terrain.unload();
		}

		if (info.probes)
		{
			probes.bake(info.probe_min, info.probe_max, lights, info.name);
		}

		else
		{
			probes.destroy();
		}

		logger.write("maps: %s ready (%zu spawns, %zu depots, %zu objectives, %zu lights)", info.name, spawns.size(), depots.size(), objectives.size(), lights.size());
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s maps_c::rotate_yaw(structures::vec3_s offset, std::float_t yaw)
	{
		return { offset.x * std::cos(yaw) + offset.z * std::sin(yaw), offset.y, -offset.x * std::sin(yaw) + offset.z * std::cos(yaw) };
	}
	/*
	//=====================================================================================
	*/
	void maps_c::solid(structures::vec3_s center, structures::vec3_s size, std::uint32_t material, std::uint32_t surface)
	{
		builder.set_material(material);

		builder.box(center, size, mathematics.quat_identity());

		world.add_box(center, size, mathematics.quat_identity(), surface, structures::contents_solid);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::solid_yaw(structures::vec3_s center, structures::vec3_s size, std::float_t yaw, std::uint32_t material, std::uint32_t surface)
	{
		const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };

		builder.set_material(material);

		builder.box(center, size, rotation);

		world.add_box(center, size, rotation, surface, structures::contents_solid);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::detail(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation, std::uint32_t material)
	{
		builder.set_material(material);

		builder.box(center, size, rotation);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::clip(structures::vec3_s center, structures::vec3_s size)
	{
		world.add_box(center, size, mathematics.quat_identity(), structures::surface_metal, structures::contents_player_clip);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::slab(structures::vec3_s minimum, structures::vec3_s maximum, std::uint32_t material, std::uint32_t surface)
	{
		solid((minimum + maximum) * 0.5f, maximum - minimum, material, surface);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::wall(structures::vec3_s minimum, structures::vec3_s maximum, std::uint32_t material)
	{
		slab(minimum, maximum, material, structures::surface_concrete);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::stairs(structures::vec3_s bottom, std::float_t width, std::float_t rise, std::float_t run, std::float_t yaw, std::uint32_t material)
	{
		const auto steps{ std::max(2u, static_cast<std::uint32_t>(std::round(rise / 0.19f))) };
		const auto step_height{ rise / static_cast<std::float_t>(steps) };
		const auto step_depth{ run / static_cast<std::float_t>(steps) };

		for (auto step{ 0u }; step < steps; step++)
		{
			const auto top{ step_height * static_cast<std::float_t>(step + 1u) };
			const auto offset{ rotate_yaw({ 0.0f, top * 0.5f, step_depth * (static_cast<std::float_t>(step) + 0.5f) }, yaw) };

			solid_yaw(bottom + offset, { width, top, step_depth }, yaw, material, structures::surface_metal);
		}

		for (auto side{ -1.0f }; side <= 1.0f; side += 2.0f)
		{
			const auto stringer{ bottom + rotate_yaw({ side * (width * 0.5f + 0.04f), rise * 0.5f, run * 0.5f }, yaw) };
			const auto slope{ std::atan2(rise, run) };

			detail(stringer, { 0.06f, 0.35f, std::sqrt(rise * rise + run * run) + 0.2f }, mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, -slope)), structures::material_paint_gunmetal);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::railing(structures::vec3_s from, structures::vec3_s to, std::uint32_t material)
	{
		const auto span{ to - from };
		const auto length{ mathematics.length(span) };
		const auto flat{ mathematics.normalize(structures::vec3_s{ span.x, 0.0f, span.z }) };
		const auto yaw{ std::atan2(flat.x, flat.z) };
		const auto slope{ std::atan2(span.y, mathematics.length(structures::vec3_s{ span.x, 0.0f, span.z })) };
		const auto rotation{ mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, -slope)) };
		const auto posts{ std::max(1u, static_cast<std::uint32_t>(std::ceil(length / 1.6f))) };

		for (auto post{ 0u }; post <= posts; post++)
		{
			const auto point{ from + span * (static_cast<std::float_t>(post) / static_cast<std::float_t>(posts)) };

			detail(point + structures::vec3_s{ 0.0f, 0.55f, 0.0f }, { 0.06f, 1.1f, 0.06f }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), material);
		}

		detail((from + to) * 0.5f + structures::vec3_s{ 0.0f, 1.1f, 0.0f }, { 0.07f, 0.07f, length + 0.06f }, rotation, material);
		detail((from + to) * 0.5f + structures::vec3_s{ 0.0f, 0.58f, 0.0f }, { 0.04f, 0.04f, length }, rotation, material);
		detail((from + to) * 0.5f + structures::vec3_s{ 0.0f, 0.06f, 0.0f }, { 0.02f, 0.12f, length }, rotation, material);

		const auto minimum{ mathematics.minimum(from, to) };
		const auto maximum{ mathematics.maximum(from, to) };

		clip({ (minimum.x + maximum.x) * 0.5f, (minimum.y + maximum.y) * 0.5f + 0.9f, (minimum.z + maximum.z) * 0.5f }, { std::max(maximum.x - minimum.x, 0.12f), maximum.y - minimum.y + 1.8f, std::max(maximum.z - minimum.z, 0.12f) });
	}
	/*
	//=====================================================================================
	*/
	void maps_c::column(structures::vec3_s base, std::float_t height, std::uint32_t material)
	{
		const auto center{ base + structures::vec3_s{ 0.0f, height * 0.5f, 0.0f } };

		detail(center + structures::vec3_s{ -0.17f, 0.0f, 0.0f }, { 0.03f, height, 0.36f }, mathematics.quat_identity(), material);
		detail(center + structures::vec3_s{ 0.17f, 0.0f, 0.0f }, { 0.03f, height, 0.36f }, mathematics.quat_identity(), material);

		builder.set_material(material);
		builder.box(center, { 0.34f, height, 0.03f }, mathematics.quat_identity());

		world.add_box(center, { 0.38f, height, 0.38f }, mathematics.quat_identity(), structures::surface_metal, structures::contents_solid);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::beam(structures::vec3_s from, structures::vec3_s to, std::float_t depth, std::uint32_t material)
	{
		const auto span{ to - from };
		const auto length{ mathematics.length(span) };
		const auto yaw{ std::atan2(span.x, span.z) };
		const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };
		const auto center{ (from + to) * 0.5f };

		detail(center + structures::vec3_s{ 0.0f, depth * 0.5f - 0.015f, 0.0f }, { depth * 0.55f, 0.03f, length }, rotation, material);
		detail(center - structures::vec3_s{ 0.0f, depth * 0.5f - 0.015f, 0.0f }, { depth * 0.55f, 0.03f, length }, rotation, material);
		detail(center, { 0.025f, depth, length }, rotation, material);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::grating(structures::vec3_s minimum, structures::vec3_s maximum)
	{
		const auto size{ maximum - minimum };
		const auto center{ (minimum + maximum) * 0.5f };
		const auto along_x{ size.x > size.z };
		const auto joists{ std::max(1u, static_cast<std::uint32_t>(std::ceil((along_x ? size.x : size.z) / 1.5f))) };

		detail({ center.x, maximum.y - 0.015f, center.z }, { size.x, 0.03f, size.z }, mathematics.quat_identity(), structures::material_grating);

		detail({ center.x, maximum.y - 0.11f, minimum.z + 0.04f }, { size.x, 0.2f, 0.08f }, mathematics.quat_identity(), structures::material_paint_gunmetal);
		detail({ center.x, maximum.y - 0.11f, maximum.z - 0.04f }, { size.x, 0.2f, 0.08f }, mathematics.quat_identity(), structures::material_paint_gunmetal);
		detail({ minimum.x + 0.04f, maximum.y - 0.11f, center.z }, { 0.08f, 0.2f, size.z }, mathematics.quat_identity(), structures::material_paint_gunmetal);
		detail({ maximum.x - 0.04f, maximum.y - 0.11f, center.z }, { 0.08f, 0.2f, size.z }, mathematics.quat_identity(), structures::material_paint_gunmetal);

		for (auto joist{ 1u }; joist < joists; joist++)
		{
			const auto fraction{ static_cast<std::float_t>(joist) / static_cast<std::float_t>(joists) };

			if (along_x)
			{
				detail({ minimum.x + size.x * fraction, maximum.y - 0.1f, center.z }, { 0.06f, 0.17f, size.z - 0.16f }, mathematics.quat_identity(), structures::material_paint_gunmetal);
			}

			else
			{
				detail({ center.x, maximum.y - 0.1f, minimum.z + size.z * fraction }, { size.x - 0.16f, 0.17f, 0.06f }, mathematics.quat_identity(), structures::material_paint_gunmetal);
			}
		}

		world.add_box(center, size, mathematics.quat_identity(), structures::surface_grate, structures::contents_solid);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::container(structures::vec3_s base, std::float_t yaw, std::uint32_t material, bool long_container)
	{
		const auto length{ long_container ? 12.19f : 6.06f };
		const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };
		const auto center{ base + structures::vec3_s{ 0.0f, 1.295f, 0.0f } };

		footprints.push_back({ { base.x, base.z }, { 1.2f, length * 0.5f }, yaw });

		detail(center, { 2.36f, 2.5f, length - 0.1f }, rotation, material);

		for (auto corner{ 0u }; corner < 4u; corner++)
		{
			const auto sx{ (corner & 1u) ? 1.0f : -1.0f };
			const auto sz{ (corner & 2u) ? 1.0f : -1.0f };

			detail(center + rotate_yaw({ sx * 1.13f, 0.0f, sz * (length * 0.5f - 0.08f) }, yaw), { 0.18f, 2.59f, 0.16f }, rotation, structures::material_paint_gunmetal);
			detail(center + rotate_yaw({ sx * 1.14f, sz * 1.22f, 0.0f }, yaw), { 0.16f, 0.15f, length }, rotation, structures::material_paint_gunmetal);
		}

		for (auto end{ 0u }; end < 2u; end++)
		{
			const auto sz{ end ? 1.0f : -1.0f };

			detail(center + rotate_yaw({ 0.0f, 1.22f, sz * (length * 0.5f - 0.08f) }, yaw), { 2.44f, 0.15f, 0.16f }, rotation, structures::material_paint_gunmetal);
			detail(center + rotate_yaw({ 0.0f, -1.22f, sz * (length * 0.5f - 0.08f) }, yaw), { 2.44f, 0.15f, 0.16f }, rotation, structures::material_paint_gunmetal);

			for (auto bar{ 0u }; bar < 4u; bar++)
			{
				detail(center + rotate_yaw({ -0.85f + static_cast<std::float_t>(bar) * 0.56f, 0.0f, sz * (length * 0.5f - 0.02f) }, yaw), { 0.035f, 2.3f, 0.035f }, rotation, structures::material_steel);
			}
		}

		world.add_box(center, { 2.44f, 2.59f, length }, rotation, structures::surface_metal, structures::contents_solid);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::lamp(structures::vec3_s position, structures::vec3_s size, std::uint32_t material, structures::vec3_s color, std::float_t radius)
	{
		detail(position + structures::vec3_s{ 0.0f, 0.06f, 0.0f }, size + structures::vec3_s{ 0.08f, 0.1f, 0.08f }, mathematics.quat_identity(), structures::material_paint_gunmetal);
		detail(position - structures::vec3_s{ 0.0f, 0.01f, 0.0f }, { size.x, 0.02f, size.z }, mathematics.quat_identity(), material);

		lights.push_back({ position - structures::vec3_s{ 0.0f, 0.08f, 0.0f }, radius, color, 0.05f, { 0.0f, -1.0f, 0.0f }, 0u });
	}
	/*
	//=====================================================================================
	*/
	void maps_c::terminal(structures::vec3_s base, std::float_t yaw)
	{
		const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };

		detail(base + rotate_yaw({ 0.0f, 0.9f, 0.0f }, yaw), { 1.1f, 1.8f, 0.35f }, rotation, structures::material_panel_dark);
		detail(base + rotate_yaw({ 0.0f, 1.3f, 0.18f }, yaw), { 0.82f, 0.55f, 0.02f }, rotation, structures::material_screen);
		detail(base + rotate_yaw({ 0.0f, 0.95f, 0.26f }, yaw), { 0.9f, 0.06f, 0.2f }, rotation, structures::material_paint_gunmetal);
		detail(base + rotate_yaw({ 0.0f, 1.83f, 0.05f }, yaw), { 1.14f, 0.05f, 0.42f }, rotation, structures::material_neon_orange);

		world.add_box(base + rotate_yaw({ 0.0f, 0.9f, 0.0f }, yaw), { 1.1f, 1.8f, 0.4f }, rotation, structures::surface_metal, structures::contents_solid);

		depots.push_back({ base + rotate_yaw({ 0.0f, 0.0f, 0.9f }, yaw), rotate_yaw({ 0.0f, 0.0f, 1.0f }, yaw) });

		lights.push_back({ base + rotate_yaw({ 0.0f, 1.4f, 0.6f }, yaw), 4.0f, { 1.2f, 0.45f, 0.1f }, -1.0f, rotate_yaw({ 0.0f, 0.0f, 1.0f }, yaw), 0u });
	}
	/*
	//=====================================================================================
	*/
	void maps_c::deck_line(structures::vec3_s from, structures::vec3_s to, std::float_t width, std::uint32_t material)
	{
		const auto span{ to - from };

		detail((from + to) * 0.5f + structures::vec3_s{ 0.0f, 0.004f, 0.0f }, { width, 0.008f, mathematics.length(span) }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, std::atan2(span.x, span.z)), material);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::prop(const char* model_name, structures::vec3_s position, std::float_t yaw, std::float_t scale, std::uint32_t collision, std::uint32_t surface)
	{
		prop_rotated(model_name, position, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), scale, collision, surface);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::prop_rotated(const char* model_name, structures::vec3_s position, structures::quat_s rotation, std::float_t scale, std::uint32_t collision, std::uint32_t surface)
	{
		if (const auto model{ models.find(model_name) }; model)
		{
			const structures::vec3_s pivot{ (model->bounds_min.x + model->bounds_max.x) * 0.5f, model->bounds_min.y, (model->bounds_min.z + model->bounds_max.z) * 0.5f };
			const auto placement{ mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-pivot), mathematics.scaling({ scale, scale, scale })), mathematics.rotation(rotation)), mathematics.translation(position)) };

			builder.append(*model, 0u, static_cast<std::uint32_t>(model->indices.size()), placement);

			if (collision == structures::prop_collision_parts)
			{
				for (const auto& part : model->parts)
				{
					place_collision(part.bounds_min, part.bounds_max, placement, rotation, scale, collision, surface);
				}
			}

			else
			{
				place_collision(model->bounds_min, model->bounds_max, placement, rotation, scale, collision, surface);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::prop_part(const char* model_name, const char* part_name, structures::vec3_s position, structures::quat_s rotation, std::float_t scale, std::uint32_t collision, std::uint32_t surface)
	{
		if (const auto model{ models.find(model_name) }; model)
		{
			if (const auto part{ models.part(*model, part_name) }; part)
			{
				const structures::vec3_s pivot{ (part->bounds_min.x + part->bounds_max.x) * 0.5f, part->bounds_min.y, (part->bounds_min.z + part->bounds_max.z) * 0.5f };
				const auto placement{ mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-pivot), mathematics.scaling({ scale, scale, scale })), mathematics.rotation(rotation)), mathematics.translation(position)) };

				builder.append(*model, part->first_index, part->index_count, placement);

				place_collision(part->bounds_min, part->bounds_max, placement, rotation, scale, collision, surface);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::place_collision(structures::vec3_s local_min, structures::vec3_s local_max, const structures::mat4_s& placement, structures::quat_s rotation, std::float_t scale, std::uint32_t collision, std::uint32_t surface)
	{
		if (collision != structures::prop_collision_none)
		{
			const auto center{ mathematics.transform_point((local_min + local_max) * 0.5f, placement) };
			const auto size{ (local_max - local_min) * scale };

			world.add_box(center, mathematics.maximum(size, { 0.05f, 0.05f, 0.05f }), rotation, surface, collision == structures::prop_collision_clip ? structures::contents_player_clip : structures::contents_solid);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::spawn(structures::vec3_s position, std::float_t yaw, std::uint32_t team)
	{
		spawns.push_back({ position, yaw, team, 0u });
	}
	/*
	//=====================================================================================
	*/
	void maps_c::objective(structures::vec3_s position, std::float_t radius, std::uint32_t kind, std::uint32_t team, const char* name)
	{
		structures::objective_s entry{ position, radius, kind, team, {} };

		std::snprintf(entry.name, sizeof(entry.name), "%s", name);

		objectives.push_back(entry);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_deck_zero()
	{
		std::snprintf(info.name, sizeof(info.name), "%s", "Deck Zero");
		std::snprintf(info.sky, sizeof(info.sky), "%s", "qwantani_late_afternoon_puresky");

		info.sky_rotation = degrees_to_radians(205.0f);
		info.kill_height = -8.0f;
		info.bounds_min = { -33.0f, -20.0f, -49.0f };
		info.bounds_max = { 33.0f, 20.0f, 49.0f };
		info.probe_min = { -32.5f, 0.25f, -48.5f };
		info.probe_max = { 32.5f, 12.5f, 48.5f };
		info.probes = true;
		info.fog = { 0.0004f, 0.02f, 0.0f, 0.3f };

		build_flight_deck();

		build_hangar(-1.0f);
		build_hangar(1.0f);

		build_corridor(-1.0f);
		build_corridor(1.0f);

		build_tower();

		build_surroundings();

		objective({ -9.0f, 0.0f, -30.0f }, 4.0f, structures::objective_domination, structures::team_none, "A");
		objective({ 2.5f, 0.0f, 0.0f }, 4.5f, structures::objective_domination, structures::team_none, "B");
		objective({ -9.0f, 0.0f, 30.0f }, 4.0f, structures::objective_domination, structures::team_none, "C");
		objective({ 0.0f, 0.0f, -43.0f }, 1.5f, structures::objective_flag, structures::team_alpha, "alpha flag");
		objective({ 0.0f, 0.0f, 43.0f }, 1.5f, structures::objective_flag, structures::team_bravo, "bravo flag");
		objective({ 2.5f, 0.0f, 0.0f }, 5.0f, structures::objective_hill, structures::team_none, "helipad");
		objective({ 17.0f, 8.0f, 0.0f }, 4.0f, structures::objective_hill, structures::team_none, "tower");
		objective({ -9.0f, 0.0f, -30.0f }, 4.5f, structures::objective_hill, structures::team_none, "south hangar");
		objective({ -9.0f, 0.0f, 30.0f }, 4.5f, structures::objective_hill, structures::team_none, "north hangar");
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_flight_deck()
	{
		slab({ -22.5f, -0.5f, -23.5f }, { 22.5f, 0.0f, 23.5f }, structures::material_deck, structures::surface_concrete);

		for (auto segment{ 0u }; segment < 48u; segment++)
		{
			const auto a0{ static_cast<std::float_t>(segment) / 48.0f * two_pi };
			const auto a1{ static_cast<std::float_t>(segment + 1u) / 48.0f * two_pi };

			deck_line({ -6.0f + std::sin(a0) * 7.5f, 0.0f, std::cos(a0) * 7.5f }, { -6.0f + std::sin(a1) * 7.5f, 0.0f, std::cos(a1) * 7.5f }, 0.3f, structures::material_deck_line_white);
		}

		deck_line({ -7.6f, 0.0f, -2.2f }, { -7.6f, 0.0f, 2.2f }, 0.55f, structures::material_deck_line_white);
		deck_line({ -4.4f, 0.0f, -2.2f }, { -4.4f, 0.0f, 2.2f }, 0.55f, structures::material_deck_line_white);
		deck_line({ -7.3f, 0.0f, 0.0f }, { -4.7f, 0.0f, 0.0f }, 0.55f, structures::material_deck_line_white);

		for (auto dash{ 0 }; dash < 12; dash++)
		{
			const auto z{ -22.0f + static_cast<std::float_t>(dash) * 4.0f };

			if (std::fabs(z) > 8.5f)
			{
				deck_line({ -6.0f, 0.0f, z }, { -6.0f, 0.0f, z + 2.2f }, 0.25f, structures::material_deck_line_yellow);
			}
		}

		deck_line({ -22.0f, 0.0f, -23.0f }, { -22.0f, 0.0f, 23.0f }, 0.2f, structures::material_deck_line_white);
		deck_line({ 11.0f, 0.0f, -23.0f }, { 11.0f, 0.0f, -8.0f }, 0.2f, structures::material_deck_line_yellow);
		deck_line({ 11.0f, 0.0f, 8.0f }, { 11.0f, 0.0f, 23.0f }, 0.2f, structures::material_deck_line_yellow);
		deck_line({ -12.0f, 0.0f, -23.2f }, { 12.0f, 0.0f, -23.2f }, 0.25f, structures::material_deck_line_yellow);
		deck_line({ -12.0f, 0.0f, 23.2f }, { 12.0f, 0.0f, 23.2f }, 0.25f, structures::material_deck_line_yellow);

		container({ -17.5f, 0.0f, -13.0f }, 0.0f, structures::material_container_green, true);
		container({ -17.5f, 0.0f, 13.0f }, 0.0f, structures::material_container_red, true);
		container({ -17.5f, 2.59f, 15.5f }, 0.0f, structures::material_container_blue, false);
		container({ -14.5f, 0.0f, -17.0f }, 0.0f, structures::material_container_blue, false);
		container({ 5.5f, 0.0f, -15.5f }, half_pi, structures::material_container_red, false);
		container({ 5.5f, 0.0f, 15.5f }, half_pi, structures::material_container_green, false);

		for (auto end{ -1.0f }; end <= 1.0f; end += 2.0f)
		{
			prop("concrete_road_barrier_02", { -3.5f, 0.0f, end * 19.0f }, 0.0f, 1.0f, structures::prop_collision_bounds, structures::surface_concrete);
			prop("concrete_road_barrier_02", { -1.9f, 0.0f, end * 19.1f }, 0.08f, 1.0f, structures::prop_collision_bounds, structures::surface_concrete);
			prop("concrete_road_barrier", { -10.5f, 0.0f, end * 8.5f }, half_pi, 1.0f, structures::prop_collision_bounds, structures::surface_concrete);
			prop("concrete_road_barrier", { -10.6f, 0.0f, end * 10.1f }, half_pi + 0.1f, 1.0f, structures::prop_collision_bounds, structures::surface_concrete);
			prop("concrete_road_barrier_02", { 8.0f, 0.0f, end * 4.0f }, half_pi - end * 0.2f, 1.0f, structures::prop_collision_bounds, structures::surface_concrete);
			prop("concrete_road_barrier_02", { 7.7f, 0.0f, end * 5.6f }, half_pi - end * 0.3f, 1.0f, structures::prop_collision_bounds, structures::surface_concrete);

			for (auto layer{ 0u }; layer < 4u; layer++)
			{
				prop("old_military_crate", { 0.6f, static_cast<std::float_t>(layer) * 0.3f, end * 9.5f }, half_pi + (layer & 1u ? 0.05f : -0.03f), 1.0f, structures::prop_collision_bounds, structures::surface_wood);
				prop("old_military_crate", { -0.6f, static_cast<std::float_t>(layer) * 0.3f, end * 9.4f }, half_pi + (layer & 1u ? -0.04f : 0.02f), 1.0f, structures::prop_collision_bounds, structures::surface_wood);
			}

			prop("ammo_box", { 0.4f, 1.2f, end * 9.3f }, 0.4f, 1.0f, structures::prop_collision_none, structures::surface_metal);
			prop("ammo_box", { 0.7f, 1.2f, end * 9.6f }, 0.1f, 1.0f, structures::prop_collision_none, structures::surface_metal);

			prop("barrel_01", { -20.0f, 0.0f, end * 2.5f }, 0.3f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
			prop("barrel_01", { -19.4f, 0.0f, end * 2.7f }, 1.3f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
			prop("barrel_03", { -20.3f, 0.0f, end * 3.2f }, 2.1f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
			prop("old_tyre", { -14.0f, 0.3f, end * 20.5f }, 0.0f, 1.0f, structures::prop_collision_none, structures::surface_fabric);

			prop("plastic_crate_03", { -12.4f, 0.0f, end * 20.0f }, 0.3f, 1.0f, structures::prop_collision_bounds, structures::surface_wood);
			prop("plastic_crate_03", { -12.4f, 0.27f, end * 20.02f }, 0.2f, 1.0f, structures::prop_collision_bounds, structures::surface_wood);
			prop("cardboard_box_01", { -11.7f, 0.0f, end * 20.5f }, 0.7f, 1.0f, structures::prop_collision_bounds, structures::surface_wood);
			prop("metal_jerrycan_green", { -11.2f, 0.0f, end * 19.8f }, 1.2f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);

			prop("water_manhole_cover", { 2.0f, 0.0f, end * 15.0f }, 0.3f, 1.0f, structures::prop_collision_none, structures::surface_metal);
			prop("water_manhole_cover", { -15.0f, 0.0f, end * 5.0f }, 0.9f, 1.0f, structures::prop_collision_none, structures::surface_metal);
		}

		prop("covered_car", { -6.0f, 0.0f, 0.0f }, half_pi + 0.12f, 1.0f, structures::prop_collision_bounds, structures::surface_fabric);
		prop("portable_generator", { -2.4f, 0.0f, 1.5f }, 0.4f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("metal_tool_chest", { -9.3f, 0.0f, -1.2f }, 1.2f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);

		for (auto corner{ 0u }; corner < 4u; corner++)
		{
			const auto x{ (corner & 1u) ? 21.4f : -21.4f };
			const auto z{ (corner & 2u) ? 22.0f : -22.0f };

			prop("street_lamp_01", { x, 0.0f, z }, std::atan2(-x, -z), 1.0f, structures::prop_collision_bounds, structures::surface_metal);

			lights.push_back({ { x * 0.96f, 3.7f, z * 0.96f }, 16.0f, { 6.0f, 5.4f, 4.4f }, -1.0f, { 0.0f, -1.0f, 0.0f }, 0u });
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_hangar(std::float_t side)
	{
		const auto z = [&](std::float_t value)
			{
				return value * side;
			};

		const auto box = [&](std::float_t x0, std::float_t y0, std::float_t z0, std::float_t x1, std::float_t y1, std::float_t z1, std::uint32_t material, std::uint32_t surface)
			{
				slab({ x0, y0, std::min(z(z0), z(z1)) }, { x1, y1, std::max(z(z0), z(z1)) }, material, surface);
			};

		const auto team{ side < 0.0f ? structures::team_alpha : structures::team_bravo };
		const auto facing{ side < 0.0f ? 0.0f : pi };

		box(-20.5f, -0.5f, 23.5f, 20.5f, 0.0f, 46.5f, structures::material_floor_painted, structures::surface_concrete);
		box(-6.0f, -0.5f, 46.5f, 6.0f, 0.0f, 48.5f, structures::material_metal_tread, structures::surface_metal);

		box(-20.5f, 0.0f, 46.0f, -6.0f, 11.0f, 46.5f, structures::material_bulkhead, structures::surface_metal);
		box(6.0f, 0.0f, 46.0f, 20.5f, 11.0f, 46.5f, structures::material_bulkhead, structures::surface_metal);
		box(-6.0f, 7.0f, 46.0f, 6.0f, 11.0f, 46.5f, structures::material_bulkhead, structures::surface_metal);

		for (auto wall_side{ -1.0f }; wall_side <= 1.0f; wall_side += 2.0f)
		{
			const auto inner{ wall_side * 20.0f };
			const auto outer{ wall_side * 20.5f };

			box(std::min(inner, outer), 0.0f, 23.5f, std::max(inner, outer), 11.0f, 35.0f, structures::material_bulkhead, structures::surface_metal);
			box(std::min(inner, outer), 0.0f, 38.0f, std::max(inner, outer), 11.0f, 46.5f, structures::material_bulkhead, structures::surface_metal);
			box(std::min(inner, outer), 3.0f, 35.0f, std::max(inner, outer), 11.0f, 38.0f, structures::material_bulkhead, structures::surface_metal);

			for (auto column_z : { 24.3f, 33.5f, 41.0f, 45.6f })
			{
				column({ wall_side * 19.75f, 0.0f, z(column_z) }, 11.0f, structures::material_paint_gunmetal);
			}

			detail({ wall_side * 19.95f, 0.6f, z(29.5f) }, { 0.12f, 1.2f, 11.0f }, mathematics.quat_identity(), structures::material_metal_sheet);
			detail({ wall_side * 19.95f, 0.6f, z(42.0f) }, { 0.12f, 1.2f, 8.0f }, mathematics.quat_identity(), structures::material_metal_sheet);
		}

		box(-20.5f, 0.0f, 23.5f, -11.0f, 11.0f, 24.0f, structures::material_hull, structures::surface_metal);
		box(11.0f, 0.0f, 23.5f, 20.5f, 11.0f, 24.0f, structures::material_hull, structures::surface_metal);
		box(-11.0f, 8.0f, 23.5f, 11.0f, 11.0f, 24.0f, structures::material_hull, structures::surface_metal);

		for (auto panel{ 0u }; panel < 3u; panel++)
		{
			const auto offset{ static_cast<std::float_t>(panel) * 0.28f };

			detail({ -15.2f - offset, 4.0f, z(24.25f + offset) }, { 8.0f, 8.0f, 0.18f }, mathematics.quat_identity(), structures::material_shutter);
			detail({ 15.2f + offset, 4.0f, z(24.25f + offset) }, { 8.0f, 8.0f, 0.18f }, mathematics.quat_identity(), structures::material_shutter);
		}

		detail({ 0.0f, 8.15f, z(24.35f) }, { 22.4f, 0.3f, 0.5f }, mathematics.quat_identity(), structures::material_paint_yellow);
		detail({ -11.15f, 4.0f, z(24.3f) }, { 0.3f, 8.0f, 0.5f }, mathematics.quat_identity(), structures::material_paint_yellow);
		detail({ 11.15f, 4.0f, z(24.3f) }, { 0.3f, 8.0f, 0.5f }, mathematics.quat_identity(), structures::material_paint_yellow);

		box(-20.5f, 11.0f, 23.5f, -12.0f, 11.5f, 46.5f, structures::material_corrugated_steel, structures::surface_metal);
		box(-6.0f, 11.0f, 23.5f, 6.0f, 11.5f, 46.5f, structures::material_corrugated_steel, structures::surface_metal);
		box(12.0f, 11.0f, 23.5f, 20.5f, 11.5f, 46.5f, structures::material_corrugated_steel, structures::surface_metal);
		box(-12.0f, 11.0f, 23.5f, -6.0f, 11.5f, 31.0f, structures::material_corrugated_steel, structures::surface_metal);
		box(-12.0f, 11.0f, 39.0f, -6.0f, 11.5f, 46.5f, structures::material_corrugated_steel, structures::surface_metal);
		box(6.0f, 11.0f, 23.5f, 12.0f, 11.5f, 31.0f, structures::material_corrugated_steel, structures::surface_metal);
		box(6.0f, 11.0f, 39.0f, 12.0f, 11.5f, 46.5f, structures::material_corrugated_steel, structures::surface_metal);

		for (auto truss_z : { 29.0f, 35.0f, 41.0f })
		{
			beam({ -20.0f, 10.4f, z(truss_z) }, { 20.0f, 10.4f, z(truss_z) }, 0.8f, structures::material_paint_gunmetal);

			for (auto lamp_x : { -13.0f, -2.5f, 2.5f, 13.0f })
			{
				prop("caged_hanging_light", { lamp_x, 9.25f, z(truss_z) }, half_pi, 1.0f, structures::prop_collision_none, structures::surface_metal);

				lights.push_back({ { lamp_x, 9.3f, z(truss_z) }, 15.0f, { 5.2f, 4.9f, 4.3f }, -1.0f, { 0.0f, -1.0f, 0.0f }, 0u });
			}
		}

		for (auto runway{ -1.0f }; runway <= 1.0f; runway += 2.0f)
		{
			beam({ runway * 6.25f, 9.75f, z(24.2f) }, { runway * 6.25f, 9.75f, z(45.8f) }, 0.5f, structures::material_paint_yellow);
		}

		prop("overhead_crane", { 0.0f, 4.72f, z(34.5f) }, 0.0f, 1.0f, structures::prop_collision_none, structures::surface_metal);

		for (auto duct{ 0u }; duct < 11u; duct++)
		{
			prop_part("modular_airduct_rectangular_01", "modular_airduct_rectangular_01_tripple_01", { -18.9f, 9.2f, z(25.0f + static_cast<std::float_t>(duct) * 1.8f + 0.9f) }, mathematics.quat_identity(), 1.0f, structures::prop_collision_none, structures::surface_metal);
		}

		for (auto pipe{ 0u }; pipe < 10u; pipe++)
		{
			const auto along{ z(25.0f + static_cast<std::float_t>(pipe) * 2.0f + 1.0f) };

			prop_part("modular_pipes", "pipe_200cm_metal", { 19.55f, 8.35f, along - 1.0f }, mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, half_pi), 1.0f, structures::prop_collision_none, structures::surface_metal);
			prop_part("modular_pipes", "pipe_200cm_metal", { 19.55f, 8.65f, along - 1.0f }, mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, half_pi), 1.0f, structures::prop_collision_none, structures::surface_metal);
		}

		for (auto purlin_x : { -14.0f, -3.0f, 3.0f, 14.0f })
		{
			beam({ purlin_x, 10.8f, z(23.8f) }, { purlin_x, 10.8f, z(46.2f) }, 0.35f, structures::material_paint_gunmetal);
		}

		grating({ -13.0f, 4.25f, std::min(z(40.0f), z(46.0f)) }, { 13.0f, 4.5f, std::max(z(40.0f), z(46.0f)) });
		grating({ -20.0f, 4.25f, std::min(z(32.0f), z(40.0f)) }, { -17.0f, 4.5f, std::max(z(32.0f), z(40.0f)) });
		grating({ 17.0f, 4.25f, std::min(z(32.0f), z(40.0f)) }, { 20.0f, 4.5f, std::max(z(32.0f), z(40.0f)) });

		box(-20.0f, 4.25f, 40.0f, -13.0f, 4.5f, 46.0f, structures::material_tread_plate, structures::surface_metal);
		box(13.0f, 4.25f, 40.0f, 20.0f, 4.5f, 46.0f, structures::material_tread_plate, structures::surface_metal);

		for (auto support_x : { -13.0f, -6.5f, 6.5f, 13.0f })
		{
			box(support_x - 0.15f, 0.0f, 40.0f, support_x + 0.15f, 4.25f, 40.3f, structures::material_paint_gunmetal, structures::surface_metal);
		}

		for (auto support_side{ -1.0f }; support_side <= 1.0f; support_side += 2.0f)
		{
			box(support_side * 17.0f - 0.15f, 0.0f, 32.0f, support_side * 17.0f + 0.15f, 4.25f, 32.3f, structures::material_paint_gunmetal, structures::surface_metal);
			box(support_side * 17.0f - 0.15f, 0.0f, 36.0f, support_side * 17.0f + 0.15f, 4.25f, 36.3f, structures::material_paint_gunmetal, structures::surface_metal);

			stairs({ support_side * 19.25f, 0.0f, z(24.6f) }, 1.4f, 4.5f, 7.4f, side > 0.0f ? 0.0f : pi, structures::material_tread_plate);

			railing({ support_side * 18.5f, 0.0f, z(24.6f) }, { support_side * 18.5f, 4.5f, z(32.0f) }, structures::material_paint_yellow);
			railing({ support_side * 18.5f, 4.5f, z(32.0f) }, { support_side * 17.0f, 4.5f, z(32.0f) }, structures::material_paint_yellow);
			railing({ support_side * 17.0f, 4.5f, z(32.0f) }, { support_side * 17.0f, 4.5f, z(40.0f) }, structures::material_paint_yellow);

			const auto room = [&](std::float_t x0, std::float_t y0, std::float_t z0, std::float_t x1, std::float_t y1, std::float_t z1)
				{
					box(std::min(support_side * x0, support_side * x1), y0, z0, std::max(support_side * x0, support_side * x1), y1, z1, structures::material_bulkhead_light, structures::surface_metal);
				};

			room(13.0f, 4.5f, 40.3f, 13.3f, 7.8f, 41.0f);
			room(13.0f, 4.5f, 42.2f, 13.3f, 7.8f, 46.0f);
			room(13.0f, 6.7f, 41.0f, 13.3f, 7.8f, 42.2f);

			room(19.6f, 4.5f, 40.0f, 20.0f, 7.8f, 40.3f);
			room(17.6f, 6.7f, 40.0f, 19.6f, 7.8f, 40.3f);
			room(17.2f, 4.5f, 40.0f, 17.6f, 7.8f, 40.3f);
			room(13.8f, 4.5f, 40.0f, 17.2f, 5.6f, 40.3f);
			room(13.8f, 7.2f, 40.0f, 17.2f, 7.8f, 40.3f);
			room(13.0f, 4.5f, 40.0f, 13.8f, 7.8f, 40.3f);

			box(std::min(support_side * 13.0f, support_side * 20.0f), 7.8f, 40.0f, std::max(support_side * 13.0f, support_side * 20.0f), 8.05f, 46.0f, structures::material_metal_sheet, structures::surface_metal);

			detail({ support_side * 16.5f, 5.0f, z(45.3f) }, { 3.0f, 1.0f, 0.9f }, mathematics.quat_identity(), structures::material_paint_gunmetal);
			detail({ support_side * 16.5f, 5.9f, z(45.6f) }, { 2.4f, 0.8f, 0.05f }, mathematics.quat_identity(), structures::material_screen);

			world.add_box({ support_side * 16.5f, 5.0f, z(45.3f) }, { 3.0f, 1.0f, 0.9f }, mathematics.quat_identity(), structures::surface_metal, structures::contents_solid);

			prop("vintage_radio_transceiver", { support_side * 15.6f, 5.5f, z(45.25f) }, side > 0.0f ? pi : 0.0f, 1.0f, structures::prop_collision_none, structures::surface_metal);

			prop_part("mounted_fluorescent_lights", "mounted_fluorescent_lights_a", { support_side * 16.5f, 7.76f, z(43.0f) }, mathematics.quat_identity(), 1.0f, structures::prop_collision_none, structures::surface_metal);

			lights.push_back({ { support_side * 16.5f, 7.7f, z(43.0f) }, 8.0f, { 3.2f, 3.2f, 3.1f }, 0.05f, { 0.0f, -1.0f, 0.0f }, 0u });

			terminal({ support_side * 19.8f, 0.0f, z(28.0f) }, support_side > 0.0f ? -half_pi : half_pi);

			for (auto wall_lamp_z : { 27.0f, 38.5f, 44.0f })
			{
				prop("industrial_wall_lamp", { support_side * 19.93f, 3.3f, z(wall_lamp_z) }, support_side > 0.0f ? -half_pi : half_pi, 1.0f, structures::prop_collision_none, structures::surface_metal);

				lights.push_back({ { support_side * 19.55f, 3.25f, z(wall_lamp_z) }, 10.0f, { 3.4f, 2.5f, 1.4f }, 0.3f, { -support_side * 0.6f, -0.8f, 0.0f }, 0u });
			}

			prop("power_box_01", { support_side * 19.8f, 1.2f, z(30.0f) }, support_side > 0.0f ? -half_pi : half_pi, 1.0f, structures::prop_collision_none, structures::surface_metal);
			prop("korean_fire_extinguisher_01", { support_side * 19.6f, 0.0f, z(31.2f) }, support_side > 0.0f ? -half_pi : half_pi, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
			prop("security_camera_01", { support_side * 19.6f, 7.2f, z(24.6f) }, support_side > 0.0f ? -2.4f : 2.4f, 1.0f, structures::prop_collision_none, structures::surface_metal);
		}

		railing({ -13.0f, 4.5f, z(40.0f) }, { 13.0f, 4.5f, z(40.0f) }, structures::material_paint_yellow);
		railing({ -6.0f, 0.0f, z(48.3f) }, { 6.0f, 0.0f, z(48.3f) }, structures::material_paint_yellow);
		railing({ -6.0f, 0.0f, z(46.6f) }, { -6.0f, 0.0f, z(48.3f) }, structures::material_paint_yellow);
		railing({ 6.0f, 0.0f, z(46.6f) }, { 6.0f, 0.0f, z(48.3f) }, structures::material_paint_yellow);

		prop("lifebuoy", { 0.0f, 0.62f, z(48.25f) }, side > 0.0f ? pi : 0.0f, 1.0f, structures::prop_collision_none, structures::surface_fabric);

		prop("covered_car", { 5.5f, 0.0f, z(33.5f) }, 0.18f, 1.0f, structures::prop_collision_bounds, structures::surface_fabric);
		prop("covered_car", { -9.5f, 0.0f, z(31.0f) }, -0.35f, 1.0f, structures::prop_collision_bounds, structures::surface_fabric);

		for (auto layer{ 0u }; layer < 5u; layer++)
		{
			const auto wobble{ (layer & 1u) ? 0.04f : -0.03f };

			prop("old_military_crate", { -13.8f, static_cast<std::float_t>(layer) * 0.3f, z(27.4f) }, wobble, 1.0f, structures::prop_collision_bounds, structures::surface_wood);
			prop("old_military_crate", { -13.6f, static_cast<std::float_t>(layer) * 0.3f, z(28.5f) }, -wobble, 1.0f, structures::prop_collision_bounds, structures::surface_wood);

			if (layer < 3u)
			{
				prop("old_military_crate", { 11.5f, static_cast<std::float_t>(layer) * 0.3f, z(27.0f) }, half_pi + wobble, 1.0f, structures::prop_collision_bounds, structures::surface_wood);
			}
		}

		prop("ammo_box", { -14.2f, 1.5f, z(27.3f) }, 0.3f, 1.0f, structures::prop_collision_none, structures::surface_metal);
		prop("ammo_box", { -13.9f, 1.5f, z(27.5f) }, 0.1f, 1.0f, structures::prop_collision_none, structures::surface_metal);
		prop("medical_box", { 11.5f, 0.9f, z(27.0f) }, 0.4f, 1.0f, structures::prop_collision_none, structures::surface_metal);

		prop("portable_generator", { 2.0f, 0.0f, z(39.2f) }, 0.3f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("portable_welding_cart", { 3.4f, 0.0f, z(39.4f) }, -0.4f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("propane_tank", { 4.2f, 0.0f, z(39.0f) }, 0.0f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("small_lpg_tank", { 4.6f, 0.0f, z(39.5f) }, 0.5f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("old_military_compressor", { -4.5f, 0.0f, z(27.8f) }, 1.9f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("hand_truck", { 14.2f, 0.0f, z(29.0f) }, -0.6f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);

		prop("tool_cart", { -15.8f, 0.0f, z(38.8f) }, 0.25f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("metal_toolbox", { -15.9f, 0.96f, z(38.7f) }, 0.6f, 1.0f, structures::prop_collision_none, structures::surface_metal);
		prop("metal_tool_chest", { -14.5f, 0.0f, z(39.3f) }, -0.3f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("industrial_storage_cart", { 12.0f, 0.0f, z(37.5f) }, half_pi, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("plastic_crate_02", { 12.0f, 1.38f, z(37.3f) }, 0.2f, 1.0f, structures::prop_collision_none, structures::surface_wood);

		for (auto shelf{ 0u }; shelf < 4u; shelf++)
		{
			const auto x{ (shelf < 2u ? -10.0f : 7.8f) + static_cast<std::float_t>(shelf % 2u) * 1.12f };

			prop("steel_frame_shelves_01", { x, 0.0f, z(45.6f) }, side > 0.0f ? pi : 0.0f, 0.1f, structures::prop_collision_bounds, structures::surface_metal);
			prop("cardboard_box_01", { x, 0.53f, z(45.55f) }, 0.1f * static_cast<std::float_t>(shelf), 1.0f, structures::prop_collision_none, structures::surface_wood);
			prop("plastic_crate_03", { x - 0.2f, 1.25f, z(45.6f) }, 0.0f, 1.0f, structures::prop_collision_none, structures::surface_wood);
		}

		prop("barrel_01", { -17.6f, 0.0f, z(26.4f) }, 0.4f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("barrel_01", { -17.0f, 0.0f, z(25.9f) }, 1.9f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("barrel_03", { -17.3f, 0.0f, z(27.1f) }, 2.8f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("barrel_02", { -18.6f, 0.0f, z(44.9f) }, 0.2f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("barrel_02", { -18.0f, 0.0f, z(45.4f) }, 1.1f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("barrel_02", { -18.9f, 0.0f, z(45.5f) }, 2.4f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("propane_tank", { -16.0f, 0.0f, z(45.6f) }, 0.0f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("propane_tank", { -15.6f, 0.0f, z(45.5f) }, 0.9f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("metal_jerrycan", { -16.2f, 0.0f, z(25.6f) }, 0.9f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("utility_box_02", { 19.5f, 0.0f, z(42.0f) }, -half_pi, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop_part("ladder_sectioned_01", "ladder_section_01", { -6.0f, 0.0f, z(45.4f) }, mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, side * 0.22f), 1.0f, structures::prop_collision_none, structures::surface_metal);

		const auto fence = [&](std::float_t x, std::float_t along, std::float_t yaw)
			{
				prop_part("modular_chainlink_fence", "modular_chainlink_fence_double", { x, 0.0f, along }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), 1.0f, structures::prop_collision_clip, structures::surface_metal);
			};

		const auto post = [&](std::float_t x, std::float_t along)
			{
				prop_part("modular_chainlink_fence", "modular_chainlink_fence_post", { x, 0.0f, along }, mathematics.quat_identity(), 1.0f, structures::prop_collision_bounds, structures::surface_metal);
			};

		fence(-14.0f, z(42.02f), half_pi);
		fence(-14.0f, z(43.98f), half_pi);
		fence(-15.02f, z(41.0f), 0.0f);
		fence(-16.98f, z(41.0f), 0.0f);
		post(-14.0f, z(41.0f));
		post(-14.0f, z(43.0f));
		post(-14.0f, z(44.96f));
		post(-16.0f, z(41.0f));
		post(-17.96f, z(41.0f));

		container({ 17.8f, 0.0f, z(28.5f) }, 0.0f, side < 0.0f ? structures::material_container_red : structures::material_container_blue, false);

		for (auto spawn_index{ 0u }; spawn_index < 8u; spawn_index++)
		{
			const auto x{ -10.5f + static_cast<std::float_t>(spawn_index % 4u) * 7.0f };
			const auto depth{ 42.5f + static_cast<std::float_t>(spawn_index / 4u) * 2.2f };

			spawn({ x, 0.0f, z(depth) }, facing, team);
		}

		spawn({ -18.5f, 4.5f, z(35.0f) }, facing, team);
		spawn({ 18.5f, 4.5f, z(35.0f) }, facing, team);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_corridor(std::float_t side)
	{
		const auto x = [&](std::float_t value)
			{
				return value * side;
			};

		const auto box = [&](std::float_t x0, std::float_t y0, std::float_t z0, std::float_t x1, std::float_t y1, std::float_t z1, std::uint32_t material, std::uint32_t surface)
			{
				slab({ std::min(x(x0), x(x1)), y0, z0 }, { std::max(x(x0), x(x1)), y1, z1 }, material, surface);
			};

		box(22.5f, -0.5f, -46.5f, 32.0f, 0.0f, 46.5f, structures::material_tread_plate, structures::surface_metal);
		box(20.5f, -0.5f, 35.0f, 22.5f, 0.0f, 38.0f, structures::material_metal_tread, structures::surface_metal);
		box(20.5f, -0.5f, -38.0f, 22.5f, 0.0f, -35.0f, structures::material_metal_tread, structures::surface_metal);

		box(20.5f, 0.0f, 23.5f, 22.5f, 11.0f, 35.0f, structures::material_hull, structures::surface_metal);
		box(20.5f, 0.0f, 38.0f, 22.5f, 11.0f, 46.5f, structures::material_hull, structures::surface_metal);
		box(20.5f, 3.2f, 35.0f, 22.5f, 11.0f, 38.0f, structures::material_hull, structures::surface_metal);
		box(20.5f, 0.0f, -35.0f, 22.5f, 11.0f, -23.5f, structures::material_hull, structures::surface_metal);
		box(20.5f, 0.0f, -46.5f, 22.5f, 11.0f, -38.0f, structures::material_hull, structures::surface_metal);
		box(20.5f, 3.2f, -38.0f, 22.5f, 11.0f, -35.0f, structures::material_hull, structures::surface_metal);

		const std::float_t inner_openings[4][2] = { { -38.0f, -35.0f }, { -12.0f, -9.5f }, { 9.5f, 12.0f }, { 35.0f, 38.0f } };

		auto cursor{ -38.5f };

		for (const auto& opening : inner_openings)
		{
			if (opening[0] > cursor)
			{
				box(22.5f, 0.0f, cursor, 23.0f, 3.2f, opening[0], structures::material_bulkhead_light, structures::surface_metal);
			}

			box(22.5f, 2.7f, opening[0], 23.0f, 3.2f, opening[1], structures::material_bulkhead_light, structures::surface_metal);

			cursor = opening[1];
		}

		box(22.5f, 0.0f, cursor, 23.0f, 3.2f, 38.5f, structures::material_bulkhead_light, structures::surface_metal);

		auto outer_cursor{ -38.5f };

		for (auto window{ 0 }; window < 6; window++)
		{
			const auto center{ -30.0f + static_cast<std::float_t>(window) * 12.0f };

			box(27.0f, 0.0f, outer_cursor, 27.5f, 3.2f, center - 1.0f, structures::material_bulkhead_light, structures::surface_metal);
			box(27.0f, 0.0f, center - 1.0f, 27.5f, 1.1f, center + 1.0f, structures::material_bulkhead_light, structures::surface_metal);
			box(27.0f, 2.3f, center - 1.0f, 27.5f, 3.2f, center + 1.0f, structures::material_bulkhead_light, structures::surface_metal);

			outer_cursor = center + 1.0f;
		}

		box(27.0f, 0.0f, outer_cursor, 27.5f, 3.2f, 38.5f, structures::material_bulkhead_light, structures::surface_metal);

		box(22.5f, 3.2f, -38.5f, 27.5f, 3.6f, 38.5f, structures::material_metal_sheet, structures::surface_metal);
		box(22.5f, 0.0f, 38.0f, 27.5f, 3.2f, 38.5f, structures::material_bulkhead_light, structures::surface_metal);
		box(22.5f, 0.0f, -38.5f, 27.5f, 3.2f, -38.0f, structures::material_bulkhead_light, structures::surface_metal);
		box(20.5f, 3.0f, 35.0f, 22.5f, 3.2f, 38.0f, structures::material_metal_sheet, structures::surface_metal);
		box(20.5f, 3.0f, -38.0f, 22.5f, 3.2f, -35.0f, structures::material_metal_sheet, structures::surface_metal);

		for (auto lamp_index{ 0 }; lamp_index < 12; lamp_index++)
		{
			const auto lamp_z{ -33.0f + static_cast<std::float_t>(lamp_index) * 6.0f };

			lamp({ x(25.0f), 3.14f, lamp_z }, { 0.25f, 0.05f, 1.4f }, structures::material_light_white, { 2.2f, 2.3f, 2.5f }, 6.5f);
		}

		builder.set_material(structures::material_steel);
		builder.cylinder({ x(26.6f), 2.9f, -38.0f }, { 0.0f, 0.0f, 1.0f }, 0.09f, 76.0f, 12u, true);
		builder.cylinder({ x(26.3f), 2.95f, -38.0f }, { 0.0f, 0.0f, 1.0f }, 0.06f, 76.0f, 12u, true);

		builder.set_material(structures::material_paint_red);
		builder.cylinder({ x(23.4f), 2.9f, -38.0f }, { 0.0f, 0.0f, 1.0f }, 0.07f, 76.0f, 12u, true);

		railing({ x(31.8f), 0.0f, -46.3f }, { x(31.8f), 0.0f, 46.3f }, structures::material_paint_yellow);
		railing({ x(27.6f), 0.0f, 46.3f }, { x(31.8f), 0.0f, 46.3f }, structures::material_paint_yellow);
		railing({ x(27.6f), 0.0f, -46.3f }, { x(31.8f), 0.0f, -46.3f }, structures::material_paint_yellow);

		box(22.5f, 0.0f, 38.5f, 27.5f, 11.0f, 46.5f, structures::material_hull, structures::surface_metal);
		box(22.5f, 0.0f, -46.5f, 27.5f, 11.0f, -38.5f, structures::material_hull, structures::surface_metal);

		for (auto layer{ 0u }; layer < 3u; layer++)
		{
			prop("old_military_crate", { x(29.6f), static_cast<std::float_t>(layer) * 0.3f, -8.0f }, 0.1f + (layer & 1u ? 0.06f : 0.0f), 1.0f, structures::prop_collision_bounds, structures::surface_wood);
			prop("old_military_crate", { x(29.9f), static_cast<std::float_t>(layer) * 0.3f, 20.0f }, 0.4f - (layer & 1u ? 0.05f : 0.0f), 1.0f, structures::prop_collision_bounds, structures::surface_wood);
		}

		prop("barrel_02", { x(30.8f), 0.0f, 6.0f }, 0.7f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("barrel_01", { x(31.1f), 0.0f, 6.7f }, 2.2f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
		prop("oil_tin", { x(30.5f), 0.0f, 6.9f }, 0.3f, 1.0f, structures::prop_collision_none, structures::surface_metal);
		prop("lifebuoy", { x(27.56f), 1.4f, 0.0f }, side > 0.0f ? half_pi : -half_pi, 1.0f, structures::prop_collision_none, structures::surface_fabric);
		prop("exterior_aircon_unit", { x(28.0f), 0.0f, -24.0f }, side > 0.0f ? half_pi : -half_pi, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_tower()
	{
		slab({ 12.0f, 0.0f, -7.0f }, { 12.4f, 1.1f, 7.0f }, structures::material_hull, structures::surface_metal);
		slab({ 12.0f, 2.6f, -7.0f }, { 12.4f, 4.0f, 7.0f }, structures::material_hull, structures::surface_metal);
		slab({ 12.0f, 1.1f, -7.0f }, { 12.4f, 2.6f, -5.0f }, structures::material_hull, structures::surface_metal);
		slab({ 12.0f, 1.1f, -1.0f }, { 12.4f, 2.6f, 1.0f }, structures::material_hull, structures::surface_metal);
		slab({ 12.0f, 1.1f, 5.0f }, { 12.4f, 2.6f, 7.0f }, structures::material_hull, structures::surface_metal);

		for (auto end{ -1.0f }; end <= 1.0f; end += 2.0f)
		{
			const auto face_min{ end > 0.0f ? 6.6f : -7.0f };
			const auto face_max{ end > 0.0f ? 7.0f : -6.6f };

			slab({ 12.4f, 0.0f, face_min }, { 15.0f, 4.0f, face_max }, structures::material_hull, structures::surface_metal);
			slab({ 17.5f, 0.0f, face_min }, { 22.5f, 4.0f, face_max }, structures::material_hull, structures::surface_metal);
			slab({ 15.0f, 2.7f, face_min }, { 17.5f, 4.0f, face_max }, structures::material_hull, structures::surface_metal);

			slab({ 12.0f, 4.0f, face_min }, { 13.5f, 8.0f, face_max }, structures::material_hull, structures::surface_metal);
			slab({ 15.5f, 4.0f, face_min }, { 22.5f, 8.0f, face_max }, structures::material_hull, structures::surface_metal);
			slab({ 13.5f, 6.7f, face_min }, { 15.5f, 8.0f, face_max }, structures::material_hull, structures::surface_metal);

			grating({ 12.0f, 3.75f, end > 0.0f ? 7.0f : -8.3f }, { 16.2f, 4.0f, end > 0.0f ? 8.3f : -7.0f });

			stairs({ 13.2f, 0.0f, end * 15.4f }, 1.4f, 4.0f, 7.1f, end > 0.0f ? pi : 0.0f, structures::material_tread_plate);

			railing({ 12.5f, 0.0f, end * 15.4f }, { 12.5f, 4.0f, end * 8.3f }, structures::material_paint_yellow);
			railing({ 13.9f, 0.0f, end * 15.4f }, { 13.9f, 4.0f, end * 8.3f }, structures::material_paint_yellow);
			railing({ 13.9f, 4.0f, end * 8.3f }, { 16.2f, 4.0f, end * 8.3f }, structures::material_paint_yellow);
			railing({ 16.2f, 4.0f, end * 8.3f }, { 16.2f, 4.0f, end * 7.0f }, structures::material_paint_yellow);
		}

		slab({ 22.1f, 0.0f, -6.6f }, { 22.5f, 8.0f, 6.6f }, structures::material_hull, structures::surface_metal);
		slab({ 12.4f, 0.0f, -6.6f }, { 22.1f, 0.02f, 6.6f }, structures::material_floor_worn, structures::surface_concrete);
		slab({ 12.0f, 3.75f, -6.6f }, { 22.5f, 3.98f, 6.6f }, structures::material_metal_sheet, structures::surface_metal);
		slab({ 12.0f, 3.98f, -6.6f }, { 22.5f, 4.0f, 6.6f }, structures::material_rubber_mat, structures::surface_concrete);

		slab({ 12.0f, 4.0f, -6.6f }, { 12.4f, 5.0f, 6.6f }, structures::material_hull, structures::surface_metal);
		slab({ 12.0f, 7.2f, -6.6f }, { 12.4f, 8.0f, 6.6f }, structures::material_hull, structures::surface_metal);

		for (auto mullion{ -1 }; mullion <= 1; mullion++)
		{
			detail({ 12.2f, 6.1f, static_cast<std::float_t>(mullion) * 3.3f }, { 0.12f, 2.2f, 0.12f }, mathematics.quat_identity(), structures::material_paint_gunmetal);
		}

		slab({ 12.0f, 7.75f, -7.0f }, { 22.5f, 8.0f, -2.0f }, structures::material_metal_sheet, structures::surface_metal);
		slab({ 12.0f, 7.75f, -2.0f }, { 20.4f, 8.0f, 7.0f }, structures::material_metal_sheet, structures::surface_metal);
		slab({ 20.4f, 7.75f, 2.2f }, { 22.5f, 8.0f, 7.0f }, structures::material_metal_sheet, structures::surface_metal);

		stairs({ 21.3f, 4.0f, -4.5f }, 1.3f, 3.85f, 6.1f, 0.0f, structures::material_tread_plate);

		railing({ 20.55f, 4.0f, -4.5f }, { 20.55f, 7.85f, 1.6f }, structures::material_paint_yellow);
		railing({ 20.4f, 8.0f, -2.0f }, { 20.4f, 8.0f, 2.2f }, structures::material_paint_yellow);
		railing({ 20.4f, 8.0f, -2.0f }, { 22.1f, 8.0f, -2.0f }, structures::material_paint_yellow);

		detail({ 14.2f, 4.5f, 0.0f }, { 1.2f, 1.0f, 8.0f }, mathematics.quat_identity(), structures::material_panel_dark);
		detail({ 13.7f, 5.25f, 0.0f }, { 0.05f, 0.5f, 7.6f }, mathematics.quat_identity(), structures::material_screen);

		world.add_box({ 14.2f, 4.5f, 0.0f }, { 1.2f, 1.0f, 8.0f }, mathematics.quat_identity(), structures::surface_metal, structures::contents_solid);

		lamp({ 17.0f, 3.7f, -3.0f }, { 1.4f, 0.05f, 0.3f }, structures::material_light_white, { 3.2f, 3.1f, 2.9f }, 8.0f);
		lamp({ 17.0f, 3.7f, 3.0f }, { 1.4f, 0.05f, 0.3f }, structures::material_light_white, { 3.2f, 3.1f, 2.9f }, 8.0f);
		lamp({ 17.0f, 7.7f, 0.0f }, { 1.4f, 0.05f, 0.3f }, structures::material_light_warm, { 2.6f, 2.1f, 1.5f }, 8.0f);

		terminal({ 18.0f, 4.0f, -6.3f }, 0.0f);

		slab({ 12.0f, 8.0f, -7.0f }, { 12.3f, 9.1f, 7.0f }, structures::material_hull, structures::surface_metal);
		slab({ 12.3f, 8.0f, -7.0f }, { 22.5f, 9.1f, -6.7f }, structures::material_hull, structures::surface_metal);
		slab({ 12.3f, 8.0f, 6.7f }, { 22.5f, 9.1f, 7.0f }, structures::material_hull, structures::surface_metal);
		slab({ 22.2f, 8.0f, -6.7f }, { 22.5f, 9.1f, 6.7f }, structures::material_hull, structures::surface_metal);

		builder.set_material(structures::material_paint_gunmetal);
		builder.cylinder({ 19.5f, 8.0f, -3.0f }, { 0.0f, 1.0f, 0.0f }, 0.25f, 9.0f, 16u, true);
		builder.cylinder({ 19.5f, 16.8f, -3.0f }, { 0.0f, 1.0f, 0.0f }, 0.05f, 4.0f, 8u, true);

		world.add_box({ 19.5f, 12.5f, -3.0f }, { 0.5f, 9.0f, 0.5f }, mathematics.quat_identity(), structures::surface_metal, structures::contents_solid);

		detail({ 19.5f, 14.0f, -3.0f }, { 3.6f, 0.4f, 0.4f }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, 0.7f), structures::material_paint_white);

		builder.set_material(structures::material_paint_white);
		builder.sphere({ 15.0f, 9.2f, 3.5f }, 1.2f, 24u, 12u);

		builder.set_material(structures::material_paint_gunmetal);
		builder.cylinder({ 15.0f, 8.0f, 3.5f }, { 0.0f, 1.0f, 0.0f }, 0.5f, 0.6f, 16u, true);

		world.add_box({ 15.0f, 9.0f, 3.5f }, { 2.2f, 2.0f, 2.2f }, mathematics.quat_identity(), structures::surface_metal, structures::contents_solid);

		detail({ 22.2f, 3.3f, 0.0f }, { 0.05f, 0.18f, 12.0f }, mathematics.quat_identity(), structures::material_neon_cyan);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_surroundings()
	{
		slab({ -32.5f, -18.0f, -48.5f }, { -32.0f, 0.0f, 48.5f }, structures::material_hull, structures::surface_metal);
		slab({ 32.0f, -18.0f, -48.5f }, { 32.5f, 0.0f, 48.5f }, structures::material_hull, structures::surface_metal);
		slab({ -32.0f, -18.0f, 48.5f }, { 32.0f, 0.0f, 49.0f }, structures::material_hull, structures::surface_metal);
		slab({ -32.0f, -18.0f, -49.0f }, { 32.0f, 0.0f, -48.5f }, structures::material_hull, structures::surface_metal);
		slab({ -20.5f, -0.5f, 46.5f }, { -6.0f, 0.0f, 48.5f }, structures::material_hull, structures::surface_metal);
		slab({ 6.0f, -0.5f, 46.5f }, { 20.5f, 0.0f, 48.5f }, structures::material_hull, structures::surface_metal);
		slab({ -20.5f, -0.5f, -48.5f }, { -6.0f, 0.0f, -46.5f }, structures::material_hull, structures::surface_metal);
		slab({ 6.0f, -0.5f, -48.5f }, { 20.5f, 0.0f, -46.5f }, structures::material_hull, structures::surface_metal);

		info.water = true;
		info.water_height = -18.0f;

		for (auto ship{ 0u }; ship < 2u; ship++)
		{
			const auto center{ ship ? structures::vec3_s{ -520.0f, -18.0f, 260.0f } : structures::vec3_s{ 460.0f, -18.0f, -340.0f } };
			const auto yaw{ ship ? 0.4f : -0.3f };

			detail(center + rotate_yaw({ 0.0f, 6.0f, 0.0f }, yaw), { 26.0f, 12.0f, 150.0f }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), structures::material_hull);
			detail(center + rotate_yaw({ 6.0f, 18.0f, -10.0f }, yaw), { 10.0f, 16.0f, 22.0f }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), structures::material_hull);
			detail(center + rotate_yaw({ 6.0f, 30.0f, -10.0f }, yaw), { 2.0f, 10.0f, 2.0f }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), structures::material_paint_gunmetal);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_island()
	{
		std::snprintf(info.name, sizeof(info.name), "%s", "Island");
		std::snprintf(info.sky, sizeof(info.sky), "%s", "qwantani_late_afternoon_puresky");

		info.sky_rotation = degrees_to_radians(140.0f);
		info.kill_height = -60.0f;
		info.bounds_min = { terrain_origin, -60.0f, terrain_origin };
		info.bounds_max = { terrain_origin + terrain_size, 300.0f, terrain_origin + terrain_size };
		info.terrain = true;
		info.probes = false;
		info.fog = { 0.0012f, 0.012f, 0.0f, 0.35f };
		info.water = true;
		info.water_height = sea_level;

		terrain.load();

		load_routes();

		build_routes();

		plant_island();

		terrain.upload_mask();

		for (auto index{ 0u }; index < island_spawn_rays; index++)
		{
			const auto angle{ static_cast<std::float_t>(index) / static_cast<std::float_t>(island_spawn_rays) * two_pi };
			const structures::vec3_s direction{ std::sin(angle), 0.0f, std::cos(angle) };

			for (auto distance{ terrain_size * 0.49f }; distance > 20.0f; distance -= 2.0f)
			{
				const auto point{ direction * distance };

				if (terrain.height(point.x, point.z) > 1.2f)
				{
					spawn({ point.x, terrain.height(point.x, point.z) + 0.05f, point.z }, std::atan2(-direction.x, -direction.z), structures::team_none);

					break;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::plant_island()
	{
		std::uint32_t trees[structures::tree_kind_count][fir_variant_count]{};
		std::uint32_t gorse[gorse_variants]{};
		std::uint32_t hedges[fir_variant_count]{};
		std::uint32_t deads[dead_tree_variant_count]{};
		std::uint32_t planted[structures::tree_kind_count]{};

		char name[64]{};
		char far_name[64]{};
		char impostor_name[64]{};
		char shadow_name[64]{};

		for (auto kind{ 0u }; kind < structures::tree_kind_count; kind++)
		{
			const auto& species{ tree_species[kind] };

			for (auto variant{ 0u }; variant < fir_variant_count; variant++)
			{
				std::snprintf(name, sizeof(name), "%s_%u", species.prefix, variant);
				std::snprintf(far_name, sizeof(far_name), "%s_%u_far", species.prefix, variant);
				std::snprintf(impostor_name, sizeof(impostor_name), "%s_%u_impostor", species.prefix, variant);
				std::snprintf(shadow_name, sizeof(shadow_name), "%s_%u_shadow", species.prefix, variant);

				trees[kind][variant] = variant < species.variants ? foliage.add_species(name, models.find(far_name) ? far_name : nullptr, fir_near_distance, tree_far_distance, fir_shadow_distance, species.sway) : UINT32_MAX;

				if (trees[kind][variant] != UINT32_MAX)
				{
					foliage.add_impostor(trees[kind][variant], impostor_name, fir_impostor_distance);

					foliage.add_shadow(trees[kind][variant], shadow_name);
				}
			}
		}

		for (auto variant{ 0u }; variant < gorse_variants; variant++)
		{
			std::snprintf(name, sizeof(name), "flora_gorse_%u", variant);
			std::snprintf(far_name, sizeof(far_name), "flora_gorse_%u_far", variant);

			gorse[variant] = foliage.add_species(name, models.find(far_name) ? far_name : nullptr, gorse_near_distance, gorse_far_distance, gorse_shadow_distance, gorse_sway);
		}

		for (auto variant{ 0u }; variant < tree_species[structures::tree_hawthorn].variants && variant < fir_variant_count; variant++)
		{
			std::snprintf(name, sizeof(name), "%s_%u", tree_species[structures::tree_hawthorn].prefix, variant);
			std::snprintf(far_name, sizeof(far_name), "%s_%u_far", tree_species[structures::tree_hawthorn].prefix, variant);
			std::snprintf(impostor_name, sizeof(impostor_name), "%s_%u_impostor", tree_species[structures::tree_hawthorn].prefix, variant);
			std::snprintf(shadow_name, sizeof(shadow_name), "%s_%u_shadow", tree_species[structures::tree_hawthorn].prefix, variant);

			hedges[variant] = foliage.add_species(name, models.find(far_name) ? far_name : nullptr, hedge_near_distance, tree_far_distance, hedge_shadow_distance, tree_species[structures::tree_hawthorn].sway);

			if (hedges[variant] != UINT32_MAX)
			{
				foliage.add_impostor(hedges[variant], impostor_name, fir_impostor_distance);

				foliage.add_shadow(hedges[variant], shadow_name);
			}
		}

		for (auto variant{ 0u }; variant < dead_tree_variant_count; variant++)
		{
			std::snprintf(name, sizeof(name), "tree_dead_%u", variant);
			std::snprintf(far_name, sizeof(far_name), "tree_dead_%u_far", variant);

			deads[variant] = foliage.add_species(name, far_name, snag_near_distance, 900.0f, fir_shadow_distance, 0.0001f);
		}

		harvest.create_models();

		farming.create_models();

		const auto boulder{ foliage.add_species("boulder_01", "boulder_01_far", boulder_near_distance, 500.0f, 120.0f, 0.0f) };
		const std::uint32_t stones[2] = { foliage.add_species("rock_moss_set_01", "rock_moss_set_01_far", rock_near_distance, 450.0f, 90.0f, 0.0f), foliage.add_species("rock_moss_set_02", "rock_moss_set_02_far", rock_near_distance, 450.0f, 90.0f, 0.0f) };
		const std::uint32_t plants[3] = { foliage.add_species("fern_02", nullptr, 1000.0f, 70.0f, 25.0f, 0.15f), foliage.add_species("shrub_04", nullptr, 1000.0f, 90.0f, 30.0f, 0.08f), foliage.add_species("nettle_plant", nullptr, 1000.0f, 60.0f, 20.0f, 0.2f) };
		const std::uint32_t debris[2] = { foliage.add_species("tree_stump_01", nullptr, 1000.0f, 250.0f, 60.0f, 0.0f), foliage.add_species("dead_tree_trunk", nullptr, 1000.0f, 400.0f, 90.0f, 0.0f) };
		const std::uint32_t ores[2] = { foliage.add_species("node_metal", "node_metal_far", boulder_near_distance, 500.0f, 120.0f, 0.0f), foliage.add_species("node_sulfur", "node_sulfur_far", boulder_near_distance, 500.0f, 120.0f, 0.0f) };
		barrels[0] = foliage.add_species("barrel_01", nullptr, 1000.0f, 220.0f, 50.0f, 0.0f);
		barrels[1] = foliage.add_species("barrel_02", nullptr, 1000.0f, 220.0f, 50.0f, 0.0f);
		barrels[2] = foliage.add_species("barrel_03", nullptr, 1000.0f, 220.0f, 50.0f, 0.0f);
		const auto hemp{ foliage.add_species("hemp_plant", "hemp_plant_far", 22.0f, 150.0f, 40.0f, 0.12f) };
		const auto berry{ foliage.add_species("berry_bush", "berry_bush_far", 25.0f, 140.0f, 45.0f, 0.05f) };
		const std::uint32_t wild[3] = { foliage.add_species("potato_plant", nullptr, 1000.0f, 110.0f, 30.0f, 0.08f), foliage.add_species("corn_stalk", nullptr, 1000.0f, 160.0f, 45.0f, 0.12f), foliage.add_species("pumpkin_patch", nullptr, 1000.0f, 110.0f, 30.0f, 0.05f) };
		const auto shore_rocks{ foliage.add_species("coast_land_rocks_02", "coast_land_rocks_02_far", shore_rock_near_distance, 900.0f, fir_shadow_distance, 0.0f) };

		build_monuments();

		for (auto z{ terrain_origin + 60.0f }; z < terrain_origin + terrain_size - 60.0f; z += 13.0f)
		{
			for (auto x{ terrain_origin + 60.0f }; x < terrain_origin + terrain_size - 60.0f; x += 13.0f)
			{
				const auto radius{ 1.2f + chance() * 0.8f };
				const auto height{ terrain.height(x, z) };

				auto lowest{ height };
				auto highest{ height };
				auto spaced{ true };

				for (auto step{ 0u }; step < 12u; step++)
				{
					const auto angle{ static_cast<std::float_t>(step) / 12.0f * two_pi };
					const auto rim{ terrain.height(x + std::sin(angle) * radius, z + std::cos(angle) * radius) };

					lowest = std::min(lowest, rim);
					highest = std::max(highest, rim);
				}

				for (const auto& spring : farming.springs)
				{
					spaced = spaced && (spring.x - x) * (spring.x - x) + (spring.z - z) * (spring.z - z) > spring_spacing * spring_spacing;
				}

				if (spaced && height > 4.0f && height < 45.0f && highest - lowest < 0.1f && cleared(x, z) == false && layer_barren[std::min(terrain.ground(x, z), terrain_layer_count - 1u)] == false)
				{
					farming.springs.push_back({ x, highest + 0.025f, z, radius });
					clearings.push_back({ x, 0.0f, z, radius + 2.5f });

					terrain.mask_rectangle({ x, height, z }, radius + 0.3f, radius + 0.3f, 0.0f);

					for (auto stone{ 0u }; stone < 7u; stone++)
					{
						const auto angle{ (static_cast<std::float_t>(stone) + chance() * 0.5f) / 7.0f * two_pi };
						const auto sx{ x + std::sin(angle) * (radius + 0.15f) };
						const auto sz{ z + std::cos(angle) * (radius + 0.15f) };

						foliage.add(stones[stone % 2u], { sx, terrain.height(sx, sz) - 0.05f, sz }, chance() * two_pi, 0.18f + chance() * 0.14f);
					}
				}
			}
		}

		logger.write("maps: %zu fresh springs", farming.springs.size());

		scatter_roadside();

		auto seed{ 0x9E3779B9u };

		const auto random = [&]()
			{
				seed ^= seed << 13u;
				seed ^= seed >> 17u;
				seed ^= seed << 5u;

				return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
			};

		const auto blocker = [&](std::uint32_t species_index, structures::vec3_s position, std::float_t yaw, std::float_t scale, std::uint32_t surface)
			{
				if (species_index < foliage.species.size())
				{
					const auto& model{ *foliage.species[species_index].near_model };
					const auto size{ (model.bounds_max - model.bounds_min) * scale };

					world.add_box(position + structures::vec3_s{ 0.0f, size.y * 0.45f, 0.0f }, size * 0.8f, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), surface, structures::contents_solid);
				}
			};

		const auto stand_cells{ static_cast<std::int32_t>(std::ceil(terrain_size / tree_stand_cell)) };

		std::vector<std::vector<structures::vec3_s>> stands(static_cast<std::size_t>(stand_cells) * static_cast<std::size_t>(stand_cells));

		const auto stand_of = [&](std::float_t value)
			{
				return std::clamp(static_cast<std::int32_t>((value - terrain_origin) / tree_stand_cell), 0, stand_cells - 1);
			};

		const auto crowded = [&](std::float_t x, std::float_t z, std::float_t radius)
			{
				for (auto row{ std::max(stand_of(z) - 1, 0) }; row <= std::min(stand_of(z) + 1, stand_cells - 1); row++)
				{
					for (auto column{ std::max(stand_of(x) - 1, 0) }; column <= std::min(stand_of(x) + 1, stand_cells - 1); column++)
					{
						for (const auto& other : stands[static_cast<std::size_t>(row) * static_cast<std::size_t>(stand_cells) + static_cast<std::size_t>(column)])
						{
							if ((other.x - x) * (other.x - x) + (other.y - z) * (other.y - z) < (radius + other.z) * (radius + other.z) * tree_crowding * tree_crowding)
							{
								return true;
							}
						}
					}
				}

				return false;
			};

		const auto pick = [&](std::uint32_t biome)
			{
				auto total{ 0.0f };

				for (const auto weight : biome_trees[biome])
				{
					total += weight;
				}

				auto left{ random() * total };

				for (auto kind{ 0u }; kind < structures::tree_kind_count; kind++)
				{
					if (left < biome_trees[biome][kind])
					{
						return kind;
					}

					left -= biome_trees[biome][kind];
				}

				return static_cast<std::uint32_t>(structures::tree_fir);
			};

		const auto plant = [&](std::uint32_t kind, structures::vec3_s spot, std::float_t size, std::float_t yaw, std::float_t variety)
			{
				const auto& species{ tree_species[kind] };
				const auto chosen{ trees[kind][std::min(static_cast<std::uint32_t>(variety * static_cast<std::float_t>(species.variants)), species.variants - 1u)] };

				if (chosen != UINT32_MAX && crowded(spot.x, spot.z, species.spread * size) == false)
				{
					foliage.add(chosen, { spot.x, spot.y - 0.15f, spot.z }, yaw, size);

					world.add_box({ spot.x, spot.y + species.height * size * 0.5f, spot.z }, { species.trunk * size, species.height * size, species.trunk * size }, mathematics.quat_identity(), structures::surface_wood, structures::contents_solid);

					harvest.add(structures::node_tree, spot, species.girth * size, static_cast<std::uint32_t>(foliage.instances.size() - 1u), static_cast<std::int32_t>(world.brushes.size() - 1u));

					stands[static_cast<std::size_t>(stand_of(spot.z)) * static_cast<std::size_t>(stand_cells) + static_cast<std::size_t>(stand_of(spot.x))].push_back({ spot.x, spot.z, species.spread * size });

					planted[kind]++;
				}
			};

		for (const auto& site : world_sites)
		{
			for (auto index{ 0u }; site.landmark == structures::landmark_town && index < std::size(town_planters) + std::size(town_trees); index++)
			{
				const auto potted{ index < std::size(town_planters) };
				const auto local{ potted ? town_planters[index] : town_trees[index - std::size(town_planters)] };
				const auto x{ site.position.x + local.x };
				const auto z{ site.position.y + local.y };

				plant(structures::tree_oak, { x, terrain.height(x, z) + (potted ? town_pavings[structures::town_square].top + town_planter_soil : 0.0f), z }, mathematics.lerp(tree_species[structures::tree_oak].smallest, tree_species[structures::tree_oak].largest, potted ? 0.25f : 0.6f), chance() * two_pi, chance());
			}
		}

		for (auto z{ terrain_origin + 3.0f }; z < terrain_origin + terrain_size - 3.0f; z += 5.0f)
		{
			for (auto x{ terrain_origin + 3.0f }; x < terrain_origin + terrain_size - 3.0f; x += 5.0f)
			{
				const auto px{ x + (random() - 0.5f) * 4.5f };
				const auto pz{ z + (random() - 0.5f) * 4.5f };
				const auto height{ terrain.height(px, pz) };
				const auto slope{ 1.0f - terrain.normal(px, pz).y };
				const auto biome{ terrain.biome(px + (random() - 0.5f) * biome_scatter, pz + (random() - 0.5f) * biome_scatter) };
				const auto& flora{ biome_flora[biome] };
				const auto rocky{ mathematics.smoothstep(0.14f, 0.3f, slope) };
				const auto roll{ random() };
				const auto node_roll{ random() };
				const auto yaw{ random() * two_pi };
				const auto scale{ 0.7f + random() * 0.6f };
				const auto tree_chance{ flora.trees };
				const auto snag_chance{ tree_chance + flora.snags };
				const auto rock_chance{ snag_chance + flora.rocks + rocky * 0.05f };
				const auto plant_chance{ rock_chance + flora.plants };
				const auto debris_chance{ plant_chance + flora.debris };
				const auto open{ cleared(px, pz) == false };

				if (open && height > 2.5f && slope < 0.32f && roll < tree_chance)
				{
					const auto kind{ pick(biome) };

					plant(kind, { px, height, pz }, mathematics.lerp(tree_species[kind].smallest, tree_species[kind].largest, (scale - 0.7f) / 0.6f), yaw, random());
				}

				else if (open && height > 2.5f && slope < 0.3f && roll < snag_chance)
				{
					foliage.add(deads[static_cast<std::uint32_t>(random() * 2.99f)], { px, height - 0.2f, pz }, yaw, scale);

					world.add_box({ px, height + 2.5f, pz }, { 0.4f * scale, 5.0f, 0.4f * scale }, mathematics.quat_identity(), structures::surface_wood, structures::contents_solid);

					harvest.add(structures::node_dead_tree, { px, height, pz }, 0.25f * scale, static_cast<std::uint32_t>(foliage.instances.size() - 1u), static_cast<std::int32_t>(world.brushes.size() - 1u));
				}

				else if (open && height > 1.0f && roll < rock_chance)
				{
					const auto harvestable{ random() < 0.6f };
					const auto stone{ harvestable ? boulder : stones[static_cast<std::uint32_t>(random() * 1.99f)] };
					const auto size{ harvestable ? 0.6f + random() * 0.45f : 0.5f + random() * 1.1f };
					const structures::vec3_s position{ px, height - 0.25f * size, pz };

					foliage.add(stone, position, yaw, size);

					blocker(stone, position, yaw, size, structures::surface_rock);

					if (harvestable)
					{
						harvest.add(structures::node_stone, position, 0.8f * size, static_cast<std::uint32_t>(foliage.instances.size() - 1u), static_cast<std::int32_t>(world.brushes.size() - 1u));
					}
				}

				else if (open && height > 3.0f && slope < 0.28f && node_roll < flora.ores + rocky * 0.04f)
				{
					const auto metal{ random() < 0.6f };
					const auto size{ 0.62f + random() * 0.3f };
					const structures::vec3_s position{ px, height - 0.22f * size, pz };

					foliage.add(ores[metal ? 0u : 1u], position, yaw, size);

					blocker(ores[metal ? 0u : 1u], position, yaw, size, structures::surface_rock);

					harvest.add(metal ? structures::node_metal : structures::node_sulfur, position, 0.8f * size, static_cast<std::uint32_t>(foliage.instances.size() - 1u), static_cast<std::int32_t>(world.brushes.size() - 1u));
				}

				else if (open && height > 2.5f && slope < 0.3f && node_roll > 0.2f && node_roll < 0.2f + flora.hemp)
				{
					foliage.add(hemp, { px, height - 0.05f, pz }, yaw, 0.85f + random() * 0.3f);

					harvest.add(structures::node_hemp, { px, height, pz }, 0.35f, static_cast<std::uint32_t>(foliage.instances.size() - 1u), -1);
				}

				else if (open && height > 2.5f && slope < 0.3f && node_roll > 0.4f && node_roll < 0.4f + flora.berries)
				{
					foliage.add(berry, { px, height - 0.08f, pz }, yaw, 0.8f + random() * 0.35f);

					harvest.add(structures::node_berry, { px, height, pz }, 0.6f, static_cast<std::uint32_t>(foliage.instances.size() - 1u), -1);
				}

				else if (open && height > 2.5f && slope < 0.25f && node_roll > 0.6f && node_roll < 0.6f + flora.crops)
				{
					const auto crop{ static_cast<std::uint32_t>(random() * 2.99f) };

					foliage.add(wild[crop], { px, height - 0.04f, pz }, yaw, 0.75f + random() * 0.3f);

					harvest.add(crop == 0u ? structures::node_potato : (crop == 1u ? structures::node_corn : structures::node_pumpkin), { px, height, pz }, crop == 1u ? 0.4f : 0.5f, static_cast<std::uint32_t>(foliage.instances.size() - 1u), -1);
				}

				else if (open && height > 3.0f && slope < 0.12f && node_roll > 0.9982f)
				{
					for (auto count{ 1u + static_cast<std::uint32_t>(random() * 2.99f) }; count > 0u; count--)
					{
						const auto kind{ barrels[static_cast<std::uint32_t>(random() * 2.99f)] };
						const auto bx{ px + (random() - 0.5f) * 2.4f };
						const auto bz{ pz + (random() - 0.5f) * 2.4f };
						const structures::vec3_s position{ bx, terrain.height(bx, bz) - 0.02f, bz };

						foliage.add(kind, position, random() * two_pi, 1.0f);

						blocker(kind, position, 0.0f, 1.0f, structures::surface_metal);

						harvest.add(structures::node_barrel, position, 0.35f, static_cast<std::uint32_t>(foliage.instances.size() - 1u), static_cast<std::int32_t>(world.brushes.size() - 1u));
					}
				}

				else if (open && height > 2.0f && slope < 0.45f && node_roll > 0.8f && node_roll < 0.8f + flora.gorse)
				{
					foliage.add(gorse[std::min(static_cast<std::uint32_t>(random() * static_cast<std::float_t>(gorse_variants)), gorse_variants - 1u)], { px, height - 0.1f, pz }, yaw, 0.75f + random() * 0.5f);
				}

				else if (open && height > 2.5f && roll < plant_chance)
				{
					foliage.add(plants[static_cast<std::uint32_t>(random() * 2.99f)], { px, height - 0.05f, pz }, yaw, 0.8f + random() * 0.5f);
				}

				else if (open && height > 2.5f && roll < debris_chance)
				{
					const auto piece{ debris[static_cast<std::uint32_t>(random() * 1.99f)] };
					const structures::vec3_s position{ px, height - 0.1f, pz };

					foliage.add(piece, position, yaw, 0.9f + random() * 0.3f);

					blocker(piece, position, yaw, 1.0f, structures::surface_wood);
				}

				if (open && height > -0.8f && height < 1.4f && random() < 0.012f)
				{
					const auto size{ 0.6f + random() * 0.9f };
					const structures::vec3_s position{ px, height - 0.4f * size, pz };

					foliage.add(shore_rocks, position, yaw, size);

					blocker(shore_rocks, position, yaw, size, structures::surface_rock);
				}
			}
		}

		auto hedged{ 0u };

		for (auto z{ terrain_origin + hedge_step * 0.5f }; z < terrain_origin + terrain_size; z += hedge_step)
		{
			for (auto x{ terrain_origin + hedge_step * 0.5f }; x < terrain_origin + terrain_size; x += hedge_step)
			{
				if (terrain.biome(x, z) == structures::biome_farmland)
				{
					auto border{ FLT_MAX };

					const auto plot{ mathematics.field(x, z, field_spacing, border) };
					const auto hashed{ mathematics.hash_u32(static_cast<std::uint32_t>(static_cast<std::int32_t>(x * 2.0f)) * 73856093u ^ static_cast<std::uint32_t>(static_cast<std::int32_t>(z * 2.0f)) * 19349663u ^ hedge_salt) };
					const auto keep{ mathematics.hash_float(hashed) };
					const auto px{ x + (mathematics.hash_float(hashed ^ 0x9E3779B9u) - 0.5f) * hedge_step * 0.5f };
					const auto pz{ z + (mathematics.hash_float(hashed ^ 0x85EBCA6Bu) - 0.5f) * hedge_step * 0.5f };
					const auto ground{ terrain.height(px, pz) };
					const auto yaw{ mathematics.hash_float(hashed ^ 0xC2B2AE35u) * two_pi };
					const auto size{ mathematics.lerp(hedge_smallest, hedge_largest, mathematics.hash_float(hashed ^ 0x27D4EB2Fu)) };

					if (border < hedge_band && keep < hedge_keep && ground > 2.5f && cleared(px, pz) == false)
					{
						if (keep < hedge_keep * hedge_standard)
						{
							plant(structures::tree_oak, { px, ground, pz }, tree_species[structures::tree_oak].largest, yaw, keep / (hedge_keep * hedge_standard));
						}

						else if ((plot & hedge_gorse_mask) == 0u)
						{
							foliage.add(gorse[(hashed >> 8u) % gorse_variants], { px, ground - 0.1f, pz }, yaw, size * hedge_gorse_scale);
						}

						else
						{
							foliage.add(hedges[(hashed >> 8u) % tree_species[structures::tree_hawthorn].variants], { px, ground - 0.1f, pz }, yaw, size);
						}

						hedged++;
					}
				}
			}
		}

		logger.write("maps: planted %u firs, %u pines, %u birches, %u oaks, %u hawthorns, %u willows, %u hedge bushes", planted[structures::tree_fir], planted[structures::tree_pine], planted[structures::tree_birch], planted[structures::tree_oak], planted[structures::tree_hawthorn], planted[structures::tree_willow], hedged);

		foliage.build({ terrain_origin, -60.0f, terrain_origin }, { terrain_origin + terrain_size, 300.0f, terrain_origin + terrain_size });
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_monuments()
	{
		for (const auto& site : world_sites)
		{
			const structures::vec3_s center{ site.position.x, 0.0f, site.position.y };

			if (site.landmark == structures::landmark_town)
			{
				build_town(center, site.inner);
			}

			else if (site.landmark == structures::landmark_outpost)
			{
				build_outpost(center);
			}

			else if (site.landmark == structures::landmark_yard)
			{
				build_yard(center);
			}

			else
			{
				build_hamlet(site);
			}
		}

		raise_rig();

		logger.write("maps: monuments built, %zu clearings, %zu nodes, %zu brushes", clearings.size(), harvest.nodes.size(), world.brushes.size());
	}
	/*
	//=====================================================================================
	*/
	void maps_c::raise_rig()
	{
		auto raised{ 0u };

		for (const auto name : rig_parts)
		{
			raised += place_building(name, { rig_site.x, sea_level, rig_site.y }, rig_yaw) ? 1u : 0u;
		}

		if (raised)
		{
			clearings.push_back({ rig_site.x, 0.0f, rig_site.y, rig_clearance });

			logger.write("maps: oil rig raised from %u parts at %.0f %.0f", raised, rig_site.x, rig_site.y);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::glow(const char* kind, structures::vec3_s position, bool powered)
	{
		const auto fire{ std::strncmp(kind, "fire", 4u) == 0 };
		const auto cold{ std::strncmp(kind, "cold", 4u) == 0 };
		const auto luck{ mathematics.hash_float(static_cast<std::uint32_t>(static_cast<std::int32_t>(position.x * 7.0f)) * 73856093u ^ static_cast<std::uint32_t>(static_cast<std::int32_t>(position.z * 7.0f)) * 19349663u ^ static_cast<std::uint32_t>(static_cast<std::int32_t>(position.y * 7.0f)) * 83492791u) };

		if (powered || fire || (cold == false && luck < building_lamp_chance))
		{
			lights.push_back({ position, fire ? building_fire_radius : (cold ? building_cold_radius : building_warm_radius), fire ? building_fire_light : (cold ? building_cold_light : building_warm_light), -1.0f, { 0.0f, -1.0f, 0.0f }, 0u });
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_hamlet(const structures::world_site_s& site)
	{
		const structures::vec3_s center{ site.position.x, 0.0f, site.position.y };
		const auto village{ site.landmark == structures::landmark_ouen };
		const auto hamlet{ site.landmark == structures::landmark_portelet };
		const auto farm{ site.landmark == structures::landmark_rozel || site.landmark == structures::landmark_landes || site.landmark == structures::landmark_trinity };
		const auto count{ village ? 8u : (hamlet ? 4u : (farm ? 3u : 2u)) };

		clearings.push_back({ center.x, 0.0f, center.z, site.inner + 8.0f });
		landmarks.push_back({ site.position, site.inner * 0.8f, site.landmark });

		if (village || hamlet)
		{
			hotspots.push_back({ center.x, 0.0f, center.z, site.inner * 0.6f });
		}

		for (auto index{ 0u }; index < count; index++)
		{
			const auto radius{ site.inner * (0.38f + chance() * 0.2f) };
			const auto damage{ 0.25f + chance() * 0.6f };
			const auto model{ village ? village_models[index % std::size(village_models)] : (farm ? farm_models[index % std::size(farm_models)] : (hamlet ? hamlet_models[index % std::size(hamlet_models)] : outlier_models[index % std::size(outlier_models)])) };

			auto angle{ site.yaw + static_cast<std::float_t>(index) / static_cast<std::float_t>(count) * two_pi + (chance() - 0.5f) * 0.3f };

			structures::vec3_s spot{ center.x + std::sin(angle) * radius, 0.0f, center.z + std::cos(angle) * radius };

			for (auto attempt{ 0u }; attempt < hamlet_attempts && route_gap(spot.x, spot.z) < route_building_gap; attempt++)
			{
				angle += hamlet_turn * (attempt % 2u ? -1.0f : 1.0f) * static_cast<std::float_t>(attempt + 1u);
				spot = { center.x + std::sin(angle) * radius, 0.0f, center.z + std::cos(angle) * radius };
			}

			if (route_gap(spot.x, spot.z) >= route_building_gap)
			{
				raise(model, spot, angle, 9.0f, 7.0f, std::strcmp(model, "bld_house") == 0 ? 2u : 1u, damage);
			}
		}

		for (auto index{ 0u }; index < count + 2u; index++)
		{
			const auto angle{ chance() * two_pi };
			const auto radius{ site.inner * (0.1f + chance() * 0.25f) };
			const structures::vec3_s spot{ center.x + std::sin(angle) * radius, 0.0f, center.z + std::cos(angle) * radius };

			if (route_gap(spot.x, spot.z) >= route_prop_gap)
			{
				chance() < 0.5f ? barrel_node({ spot.x, terrain.height(spot.x, spot.z), spot.z }) : container_node(farm ? structures::node_toolbox : structures::node_box, { spot.x, terrain.height(spot.x, spot.z), spot.z }, angle);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::raise(const char* model_name, structures::vec3_s position, std::float_t yaw, std::float_t width, std::float_t depth, std::uint32_t floors, std::float_t damage)
	{
		if (place_building(model_name, { position.x, terrain.height(position.x, position.z), position.z }, yaw) == false)
		{
			build_house(position, yaw, width, depth, floors, damage);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_town(structures::vec3_s center, std::float_t radius)
	{
		clearings.push_back({ center.x, 0.0f, center.z, town_clear_radius });
		hotspots.push_back({ center.x, 0.0f, center.z, radius * 0.75f });
		landmarks.push_back({ { center.x, center.z }, radius, structures::landmark_town });

		for (auto surface{ 0u }; surface < structures::town_surface_count; surface++)
		{
			town_materials[surface] = models.variant(town_pavings[surface].material, town_pavings[surface].tint, 0.0f);
		}

		kerb_material = models.variant(structures::material_concrete_rough, { 0.62f, 0.61f, 0.59f }, 0.0f);
		dash_material = models.variant(structures::material_paint_white, { 0.8f, 0.78f, 0.72f }, 0.0f);
		granite_material = models.variant(structures::material_concrete_rough, { 0.86f, 0.85f, 0.83f }, 0.0f);
		iron_material = models.variant(structures::material_paint_gunmetal, { 0.35f, 0.35f, 0.36f }, 0.6f);
		soil_material = models.variant(structures::material_terrain_soil, { 0.8f, 0.78f, 0.75f }, 0.0f);

		for (const auto& patch : town_patches)
		{
			pave(center, patch);
		}

		dress_square(center);

		for (const auto& row : town_rows)
		{
			line_up(center, row);
		}

		for (const auto& site : town_sites)
		{
			const auto spot{ center + structures::vec3_s{ site.position.x, 0.0f, site.position.y } };

			erect(site.building, spot, site.yaw, terrain.height(spot.x, spot.z));
		}

		light_streets(center);

		litter_town(center);

		logger.write("maps: Saint Aubin laid out with %zu streets and squares, %zu building rows", std::size(town_patches), std::size(town_rows));
	}
	/*
	//=====================================================================================
	*/
	void maps_c::pave(structures::vec3_s center, const structures::town_patch_s& patch)
	{
		const auto& paving{ town_pavings[patch.paving] };
		const structures::vec2_s low{ center.x + patch.minimum.x, center.z + patch.minimum.y };
		const structures::vec2_s high{ center.x + patch.maximum.x, center.z + patch.maximum.y };
		const auto columns{ std::max(1u, static_cast<std::uint32_t>(std::ceil((high.x - low.x) / town_grid))) };
		const auto rows{ std::max(1u, static_cast<std::uint32_t>(std::ceil((high.y - low.y) / town_grid))) };
		const auto first_vertex{ static_cast<std::uint32_t>(builder.vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(builder.indices.size()) };
		const auto lengthwise{ high.y - low.y > high.x - low.x };

		builder.set_material(town_materials[patch.paving]);

		for (auto row{ 0u }; row <= rows; row++)
		{
			for (auto column{ 0u }; column <= columns; column++)
			{
				const auto x{ mathematics.lerp(low.x, high.x, static_cast<std::float_t>(column) / static_cast<std::float_t>(columns)) };
				const auto z{ mathematics.lerp(low.y, high.y, static_cast<std::float_t>(row) / static_cast<std::float_t>(rows)) };
				const auto corner{ builder.add_vertex({ x, terrain.height(x, z) + paving.top, z }, { 0.0f, 1.0f, 0.0f }, { x / paving.tile, -z / paving.tile }) };

				if (row && column)
				{
					builder.add_triangle(corner - columns - 2u, corner - columns - 1u, corner);
					builder.add_triangle(corner - columns - 2u, corner, corner - 1u);
				}
			}
		}

		builder.compute_tangents(first_vertex, first_index);

		if (paving.raised)
		{
			kerb({ low.x, low.y }, { high.x, low.y }, paving.top, { 0.0f, 0.0f, -1.0f });
			kerb({ high.x, low.y }, { high.x, high.y }, paving.top, { 1.0f, 0.0f, 0.0f });
			kerb({ high.x, high.y }, { low.x, high.y }, paving.top, { 0.0f, 0.0f, 1.0f });
			kerb({ low.x, high.y }, { low.x, low.y }, paving.top, { -1.0f, 0.0f, 0.0f });

			const auto across{ std::max(1u, static_cast<std::uint32_t>(std::ceil((high.x - low.x) / town_tile))) };
			const auto down{ std::max(1u, static_cast<std::uint32_t>(std::ceil((high.y - low.y) / town_tile))) };

			for (auto row{ 0u }; row < down; row++)
			{
				for (auto column{ 0u }; column < across; column++)
				{
					const auto x0{ mathematics.lerp(low.x, high.x, static_cast<std::float_t>(column) / static_cast<std::float_t>(across)) };
					const auto x1{ mathematics.lerp(low.x, high.x, static_cast<std::float_t>(column + 1u) / static_cast<std::float_t>(across)) };
					const auto z0{ mathematics.lerp(low.y, high.y, static_cast<std::float_t>(row) / static_cast<std::float_t>(down)) };
					const auto z1{ mathematics.lerp(low.y, high.y, static_cast<std::float_t>(row + 1u) / static_cast<std::float_t>(down)) };
					const structures::vec4_s grounds{ terrain.height(x0, z0), terrain.height(x1, z0), terrain.height(x0, z1), terrain.height(x1, z1) };
					const auto top{ (grounds.x + grounds.y + grounds.z + grounds.w) * 0.25f + paving.top };
					const auto bottom{ std::min({ grounds.x, grounds.y, grounds.z, grounds.w }) - town_footing };

					world.add_box({ (x0 + x1) * 0.5f, (top + bottom) * 0.5f, (z0 + z1) * 0.5f }, { x1 - x0, top - bottom, z1 - z0 }, mathematics.quat_identity(), structures::surface_concrete, structures::contents_solid);
				}
			}
		}

		if (patch.paving == structures::town_road || patch.paving == structures::town_lane)
		{
			roads.push_back({ lengthwise ? structures::vec2_s{ (low.x + high.x) * 0.5f, low.y } : structures::vec2_s{ low.x, (low.y + high.y) * 0.5f }, lengthwise ? structures::vec2_s{ (low.x + high.x) * 0.5f, high.y } : structures::vec2_s{ high.x, (low.y + high.y) * 0.5f }, lengthwise ? high.x - low.x : high.y - low.y });
		}

		if (patch.paving == structures::town_road)
		{
			mark_centre(center, patch);
		}

		terrain.mask_rectangle({ (low.x + high.x) * 0.5f, 0.0f, (low.y + high.y) * 0.5f }, (high.x - low.x) * 0.5f + 0.3f, (high.y - low.y) * 0.5f + 0.3f, 0.0f);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::kerb(structures::vec2_s from, structures::vec2_s to, std::float_t top, structures::vec3_s outward)
	{
		const auto length{ std::sqrt((to.x - from.x) * (to.x - from.x) + (to.y - from.y) * (to.y - from.y)) };
		const auto pieces{ std::max(1u, static_cast<std::uint32_t>(std::ceil(length / town_grid))) };
		const auto first_vertex{ static_cast<std::uint32_t>(builder.vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(builder.indices.size()) };

		builder.set_material(kerb_material);

		for (auto piece{ 0u }; piece <= pieces; piece++)
		{
			const auto x{ mathematics.lerp(from.x, to.x, static_cast<std::float_t>(piece) / static_cast<std::float_t>(pieces)) };
			const auto z{ mathematics.lerp(from.y, to.y, static_cast<std::float_t>(piece) / static_cast<std::float_t>(pieces)) };
			const auto ground{ terrain.height(x, z) };
			const structures::vec3_s upper_point{ x, ground + top, z };
			const structures::vec3_s lower_point{ x, ground - town_kerb_drop, z };
			const auto upper{ builder.add_vertex(upper_point, outward, builder.project_uv(upper_point, outward)) };
			const auto lower{ builder.add_vertex(lower_point, outward, builder.project_uv(lower_point, outward)) };

			if (piece)
			{
				builder.add_triangle(upper - 2u, upper, lower);
				builder.add_triangle(upper - 2u, lower, lower - 2u);
			}
		}

		builder.compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::mark_centre(structures::vec3_s center, const structures::town_patch_s& patch)
	{
		const auto lengthwise{ patch.maximum.y - patch.minimum.y > patch.maximum.x - patch.minimum.x };
		const auto low{ lengthwise ? patch.minimum.y : patch.minimum.x };
		const auto high{ lengthwise ? patch.maximum.y : patch.maximum.x };
		const auto middle{ lengthwise ? (patch.minimum.x + patch.maximum.x) * 0.5f : (patch.minimum.y + patch.maximum.y) * 0.5f };
		const auto lift{ town_pavings[patch.paving].top + town_dash_lift };

		builder.set_material(dash_material);

		for (auto along{ low + town_dash_spacing * 0.5f }; high - low > town_dash_minimum && along + town_dash_length < high; along += town_dash_spacing)
		{
			const structures::vec2_s spot{ lengthwise ? middle : along + town_dash_length * 0.5f, lengthwise ? along + town_dash_length * 0.5f : middle };

			if (chance() > town_dash_worn && junction(spot, &patch) == false)
			{
				const auto half{ lengthwise ? structures::vec2_s{ town_dash_width * 0.5f, town_dash_length * 0.5f } : structures::vec2_s{ town_dash_length * 0.5f, town_dash_width * 0.5f } };
				const auto point = [&](std::float_t x, std::float_t z)
					{
						const structures::vec2_s at{ center.x + spot.x + x, center.z + spot.y + z };

						return structures::vec3_s{ at.x, terrain.height(at.x, at.y) + lift, at.y };
					};

				builder.quad(point(-half.x, -half.y), point(half.x, -half.y), point(half.x, half.y), point(-half.x, half.y), { 0.0f, 1.0f, 0.0f });
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool maps_c::junction(structures::vec2_s spot, const structures::town_patch_s* skip)
	{
		const auto reach{ town_junction_clear * 0.5f };

		for (const auto& patch : town_patches)
		{
			if (&patch != skip && (patch.paving == structures::town_road || patch.paving == structures::town_lane) && spot.x > patch.minimum.x - reach && spot.x < patch.maximum.x + reach && spot.y > patch.minimum.y - reach && spot.y < patch.maximum.y + reach)
			{
				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void maps_c::line_up(structures::vec3_s center, const structures::town_row_s& row)
	{
		const structures::vec2_s span{ row.to.x - row.from.x, row.to.y - row.from.y };
		const auto length{ std::sqrt(span.x * span.x + span.y * span.y) };
		const structures::vec2_s along{ span.x / length, span.y / length };
		const structures::vec2_s facing{ -along.y, along.x };
		const auto yaw{ std::atan2(-facing.x, -facing.y) };

		auto cursor{ 0.0f };
		auto previous{ static_cast<std::uint32_t>(structures::town_building_count) };

		for (auto index{ 0u }; index < row.count; index++)
		{
			const auto kind{ row.buildings[index] };
			const auto& plan{ town_buildings[kind] };
			const auto model{ models.find(plan.model) };
			const auto left{ model ? model->bounds_min.x : plan.size.x * -0.5f };
			const auto right{ model ? model->bounds_max.x : plan.size.x * 0.5f };
			const auto front{ model ? model->bounds_min.z : plan.size.y * -0.5f };
			const auto back{ model ? model->bounds_max.z : plan.size.y * 0.5f };
			const auto start{ cursor + (index == 0u || (kind == structures::town_terrace && previous == structures::town_terrace) ? 0.0f : row.gap) };
			const auto width{ right - left };

			if (start + width <= length)
			{
				const structures::vec2_s door{ center.x + row.from.x + along.x * (start + width * 0.5f), center.z + row.from.y + along.y * (start + width * 0.5f) };
				const structures::vec3_s origin{ center.x + row.from.x + along.x * (start + right) + facing.x * front, 0.0f, center.z + row.from.y + along.y * (start + right) + facing.y * front };

				if (route_gap(origin.x, origin.z) > std::max(width, back - front) * 0.5f + town_route_margin)
				{
					erect(kind, origin, yaw, terrain.height(door.x, door.y));
				}

				cursor = start + width;
				previous = kind;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::erect(std::uint32_t kind, structures::vec3_s origin, std::float_t yaw, std::float_t ground)
	{
		const auto& plan{ town_buildings[kind] };

		if (place_building(plan.model, { origin.x, ground + town_pavings[structures::town_walk].top, origin.z }, yaw) == false)
		{
			build_house(origin, yaw, plan.size.x, plan.size.y, plan.floors, kind == structures::town_ruin ? 0.85f : 0.2f + chance() * 0.35f);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::fixture(const char* model_name, structures::vec3_s position, std::float_t yaw, std::uint32_t surface)
	{
		if (const auto model{ models.find(model_name) }; model)
		{
			const structures::vec3_s pivot{ (model->bounds_min.x + model->bounds_max.x) * 0.5f, model->bounds_min.y, (model->bounds_min.z + model->bounds_max.z) * 0.5f };
			const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };
			const auto placement{ mathematics.multiply(mathematics.multiply(mathematics.translation(-pivot), mathematics.rotation(rotation)), mathematics.translation(position)) };
			const auto marked{ std::any_of(model->parts.begin(), model->parts.end(), [](const structures::model_part_s& part) { return std::strncmp(part.name, "col_", 4u) == 0; }) };

			if (building_species.count(model_name) == 0u)
			{
				char far_name[64]{};

				std::snprintf(far_name, sizeof(far_name), "%s_far", model_name);

				building_species[model_name] = foliage.add_species(model_name, models.find(far_name) ? far_name : nullptr, town_prop_near, town_prop_far, town_prop_shadow, 0.0f);
			}

			foliage.add(building_species[model_name], position - rotate_yaw(pivot, yaw), yaw, 1.0f);

			for (const auto& part : model->parts)
			{
				if (std::strncmp(part.name, "col_", 4u) == 0)
				{
					place_collision(part.bounds_min, part.bounds_max, placement, rotation, 1.0f, structures::prop_collision_bounds, surface_named(part.name + 4));
				}

				else if (std::strncmp(part.name, "loot_", 5u) == 0 && chance() < town_loot_chance)
				{
					const structures::vec3_s spot{ (part.bounds_min.x + part.bounds_max.x) * 0.5f, part.bounds_min.y, (part.bounds_min.z + part.bounds_max.z) * 0.5f };
					const auto buried{ std::any_of(model->parts.begin(), model->parts.end(), [&](const structures::model_part_s& other) { return std::strncmp(other.name, "col_", 4u) == 0 && spot.x > other.bounds_min.x && spot.x < other.bounds_max.x && spot.y + 0.05f > other.bounds_min.y && spot.y + 0.05f < other.bounds_max.y && spot.z > other.bounds_min.z && spot.z < other.bounds_max.z; }) };

					if (buried == false)
					{
						container_node(loot_named(part.name + 5), mathematics.transform_point(spot, placement), yaw);
					}
				}
			}

			if (marked == false)
			{
				place_collision(model->bounds_min, model->bounds_max, placement, rotation, 1.0f, structures::prop_collision_bounds, surface);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::light_streets(structures::vec3_s center)
	{
		for (const auto& patch : town_patches)
		{
			if (patch.paving == structures::town_walk)
			{
				const auto lengthwise{ patch.maximum.y - patch.minimum.y > patch.maximum.x - patch.minimum.x };
				const auto low{ lengthwise ? patch.minimum.y : patch.minimum.x };
				const auto high{ lengthwise ? patch.maximum.y : patch.maximum.x };
				const auto near_edge{ lengthwise ? patch.minimum.x : patch.minimum.y };
				const auto far_edge{ lengthwise ? patch.maximum.x : patch.maximum.y };
				const auto edge{ std::fabs(near_edge) < std::fabs(far_edge) ? near_edge : far_edge };
				const auto side{ edge > 0.0f ? 1.0f : -1.0f };
				const auto line{ edge + side * town_lamp_inset };
				const auto yaw{ lengthwise ? (side > 0.0f ? -half_pi : half_pi) : (side > 0.0f ? pi : 0.0f) };

				for (auto along{ low + (side > 0.0f ? town_lamp_spacing * 0.2f : town_lamp_spacing * 0.7f) }; along < high - 1.5f; along += town_lamp_spacing)
				{
					const structures::vec2_s spot{ center.x + (lengthwise ? line : along), center.z + (lengthwise ? along : line) };

					fixture(town_lamp_model, { spot.x, terrain.height(spot.x, spot.y) + town_pavings[structures::town_walk].top, spot.y }, yaw, structures::surface_metal);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::litter_town(structures::vec3_s center)
	{
		for (const auto& barrier : town_barriers)
		{
			const structures::vec2_s spot{ center.x + barrier.x, center.z + barrier.y };

			fixture(town_barrier_models[static_cast<std::uint32_t>(chance() * 1.99f)], { spot.x, terrain.height(spot.x, spot.y) + town_pavings[structures::town_road].top, spot.y }, barrier.z, structures::surface_concrete);
		}

		auto wrecked{ 0u };

		for (auto attempt{ 0u }; attempt < town_wrecks * 12u && wrecked < town_wrecks; attempt++)
		{
			const auto& patch{ town_patches[std::min(static_cast<std::size_t>(chance() * static_cast<std::float_t>(std::size(town_patches))), std::size(town_patches) - 1u)] };
			const auto lengthwise{ patch.maximum.y - patch.minimum.y > patch.maximum.x - patch.minimum.x };
			const structures::vec2_s spot{ mathematics.lerp(patch.minimum.x + 1.2f, patch.maximum.x - 1.2f, chance()), mathematics.lerp(patch.minimum.y + 1.2f, patch.maximum.y - 1.2f, chance()) };

			if ((patch.paving == structures::town_road || patch.paving == structures::town_lane) && junction(spot, &patch) == false)
			{
				const auto yaw{ (lengthwise ? 0.0f : half_pi) + (chance() - 0.5f) * 0.7f + (chance() < 0.5f ? pi : 0.0f) };
				const structures::vec2_s world_spot{ center.x + spot.x, center.z + spot.y };

				fixture(town_wreck_models[std::min(static_cast<std::size_t>(chance() * static_cast<std::float_t>(std::size(town_wreck_models))), std::size(town_wreck_models) - 1u)], { world_spot.x, terrain.height(world_spot.x, world_spot.y) + town_pavings[patch.paving].top, world_spot.y }, yaw, structures::surface_metal);

				wrecked++;
			}
		}

		for (const auto& yard : town_yards)
		{
			for (auto item{ 0u }; item < yard.clutter; item++)
			{
				const auto x{ center.x + mathematics.lerp(yard.minimum.x, yard.maximum.x, chance()) };
				const auto z{ center.z + mathematics.lerp(yard.minimum.y, yard.maximum.y, chance()) };
				const structures::vec3_s ground{ x, terrain.height(x, z), z };
				const auto pick{ chance() };

				if (pick < 0.3f)
				{
					barrel_node(ground);
				}

				else if (pick < 0.5f)
				{
					container_node(chance() < 0.6f ? structures::node_box : structures::node_toolbox, ground, chance() * two_pi);
				}

				else if (pick < 0.68f)
				{
					fixture("old_tyre", ground, chance() * two_pi, structures::surface_fabric);
				}

				else if (pick < 0.84f)
				{
					fixture("metal_trash_can", ground, chance() * two_pi, structures::surface_metal);
				}

				else
				{
					fixture(chance() < 0.5f ? "utility_box_01" : "power_box_01", ground, chance() * two_pi, structures::surface_metal);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::scatter_roadside()
	{
		auto placed{ 0u };

		for (const auto& path : paths)
		{
			auto travelled{ 0.0f };
			auto next{ mathematics.lerp(roadside_gap_min, roadside_gap_max, chance()) };

			for (auto index{ 1u }; path.kind == structures::route_road && index < path.points.size(); index++)
			{
				const auto& from{ path.points[index - 1u] };
				const auto& to{ path.points[index] };
				const structures::vec3_s span{ to.x - from.x, 0.0f, to.z - from.z };

				travelled += mathematics.length(span);

				if (travelled >= next)
				{
					const auto along{ mathematics.normalize(span) };
					const auto side{ chance() < 0.5f ? 1.0f : -1.0f };
					const auto offset{ (path.width * 0.5f + roadside_shoulder + chance() * roadside_spread) * side };
					const structures::vec3_s spot{ to.x + along.z * offset, 0.0f, to.z - along.x * offset };
					const auto open{ std::none_of(clearings.begin(), clearings.end(), [&](const structures::vec4_s& clearing) { return mathematics.length(structures::vec2_s{ spot.x - clearing.x, spot.z - clearing.z }) < clearing.w + roadside_clearance; }) && std::none_of(crossings.begin(), crossings.end(), [&](const structures::crossing_s& crossing) { return mathematics.length(structures::vec2_s{ spot.x - crossing.position.x, spot.z - crossing.position.z }) < roadside_clearance; }) };

					travelled = 0.0f;
					next = mathematics.lerp(roadside_gap_min, roadside_gap_max, chance());

					if (open && terrain.height(spot.x, spot.z) > sea_level + 1.0f && terrain.normal(spot.x, spot.z).y > roadside_steep)
					{
						const auto yaw{ std::atan2(along.x, along.z) + (chance() - 0.5f) * 0.8f + (chance() < 0.5f ? pi : 0.0f) };
						const auto pick{ std::min(static_cast<std::size_t>(chance() * static_cast<std::float_t>(std::size(roadside_wrecks))), std::size(roadside_wrecks) - 1u) };

						fixture(roadside_wrecks[pick], { spot.x, terrain.height(spot.x, spot.z), spot.z }, yaw, structures::surface_metal);

						clearings.push_back({ spot.x, 0.0f, spot.z, roadside_room });

						terrain.mask_rectangle({ spot.x, terrain.height(spot.x, spot.z), spot.z }, 1.3f, 2.4f, yaw);

						if (placed < 3u)
						{
							logger.write("maps: roadside %s at %.1f %.1f %.1f facing %.2f", roadside_wrecks[pick], spot.x, terrain.height(spot.x, spot.z), spot.z, yaw);
						}

						if (chance() < roadside_barrel_chance)
						{
							const auto drum{ spot + mathematics.flat_forward(yaw + half_pi) * (2.4f + chance()) };

							barrel_node({ drum.x, terrain.height(drum.x, drum.z), drum.z });
						}

						if (chance() < roadside_crate_chance)
						{
							const auto crate{ spot - mathematics.flat_forward(yaw) * (3.0f + chance()) };

							container_node(chance() < 0.7f ? structures::node_box : structures::node_toolbox, { crate.x, terrain.height(crate.x, crate.z), crate.z }, yaw + chance());
						}

						placed++;
					}
				}
			}
		}

		logger.write("maps: %u roadside wrecks", placed);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::dress_square(structures::vec3_s center)
	{
		const auto on_road = [&](structures::vec2_s spot)
			{
				return std::any_of(std::begin(town_patches), std::end(town_patches), [&](const structures::town_patch_s& patch) { return (patch.paving == structures::town_road || patch.paving == structures::town_lane) && spot.x > patch.minimum.x && spot.x < patch.maximum.x && spot.y > patch.minimum.y && spot.y < patch.maximum.y; });
			};
		const auto cast_bollard{ models.find("prop_bollard") != nullptr };

		for (const auto& patch : town_patches)
		{
			if (patch.paving == structures::town_square)
			{
				const structures::vec2_s corners[4] = { patch.minimum, { patch.maximum.x, patch.minimum.y }, patch.maximum, { patch.minimum.x, patch.maximum.y } };

				for (auto edge{ 0u }; edge < 4u; edge++)
				{
					const auto from{ corners[edge] };
					const auto to{ corners[(edge + 1u) % 4u] };
					const auto length{ std::sqrt((to.x - from.x) * (to.x - from.x) + (to.y - from.y) * (to.y - from.y)) };
					const structures::vec2_s along{ (to.x - from.x) / length, (to.y - from.y) / length };
					const structures::vec2_s outward{ along.y, -along.x };

					for (auto distance{ town_bollard_spacing * 0.5f }; distance < length; distance += town_bollard_spacing)
					{
						const structures::vec2_s spot{ from.x + along.x * distance - outward.x * town_bollard_inset, from.y + along.y * distance - outward.y * town_bollard_inset };

						if (on_road({ spot.x + outward.x * (town_bollard_inset + 1.0f), spot.y + outward.y * (town_bollard_inset + 1.0f) }))
						{
							const auto x{ center.x + spot.x };
							const auto z{ center.z + spot.y };
							const auto ground{ terrain.height(x, z) + town_pavings[structures::town_square].top };

							if (cast_bollard)
							{
								fixture("prop_bollard", { x, ground, z }, std::atan2(-outward.x, -outward.y), structures::surface_metal);
							}

							else
							{
								solid({ x, ground + 0.45f, z }, { 0.2f, 0.9f, 0.2f }, iron_material, structures::surface_metal);

								detail({ x, ground + 0.93f, z }, { 0.26f, 0.07f, 0.26f }, mathematics.quat_identity(), iron_material);
							}
						}
					}
				}
			}
		}

		for (const auto& spot : town_planters)
		{
			const auto x{ center.x + spot.x };
			const auto z{ center.z + spot.y };
			const auto ground{ terrain.height(x, z) + town_pavings[structures::town_square].top };
			const auto reach{ (town_planter_size - town_planter_rim) * 0.5f };
			const auto inner{ town_planter_size - town_planter_rim * 2.0f };

			solid({ x - reach, ground + town_planter_height * 0.5f, z }, { town_planter_rim, town_planter_height, town_planter_size }, kerb_material, structures::surface_concrete);
			solid({ x + reach, ground + town_planter_height * 0.5f, z }, { town_planter_rim, town_planter_height, town_planter_size }, kerb_material, structures::surface_concrete);
			solid({ x, ground + town_planter_height * 0.5f, z - reach }, { inner, town_planter_height, town_planter_rim }, kerb_material, structures::surface_concrete);
			solid({ x, ground + town_planter_height * 0.5f, z + reach }, { inner, town_planter_height, town_planter_rim }, kerb_material, structures::surface_concrete);
			solid({ x, ground + town_planter_soil * 0.5f, z }, { inner, town_planter_soil, inner }, soil_material, structures::surface_dirt);
		}

		if (const structures::vec3_s spot{ center.x + town_memorial.x, 0.0f, center.z + town_memorial.y }; models.find(town_memorial_model))
		{
			fixture(town_memorial_model, { spot.x, terrain.height(spot.x, spot.z) + town_pavings[structures::town_square].top, spot.z }, 0.0f, structures::surface_rock);
		}

		else
		{
			build_memorial(spot);
		}

		for (const auto& run : town_runs)
		{
			const structures::vec2_s span{ run.to.x - run.from.x, run.to.y - run.from.y };
			const auto length{ std::sqrt(span.x * span.x + span.y * span.y) };
			const auto pieces{ std::max(1u, static_cast<std::uint32_t>(std::round(length / run.piece))) };
			const auto yaw{ std::atan2(-span.y, span.x) };

			for (auto piece{ 0u }; piece < pieces; piece++)
			{
				const auto along{ (static_cast<std::float_t>(piece) + 0.5f) / static_cast<std::float_t>(pieces) };
				const structures::vec2_s spot{ run.from.x + span.x * along, run.from.y + span.y * along };
				const auto x{ center.x + spot.x };
				const auto z{ center.z + spot.y };

				fixture(run.model, { x, terrain.height(x, z) + paving_top(spot), z }, yaw, run.surface);
			}
		}

		for (const auto& entry : town_props)
		{
			const auto x{ center.x + entry.position.x };
			const auto z{ center.z + entry.position.y };

			fixture(entry.model, { x, terrain.height(x, z) + paving_top(entry.position), z }, entry.yaw, entry.surface);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t maps_c::paving_top(structures::vec2_s spot)
	{
		auto top{ 0.0f };

		for (const auto& patch : town_patches)
		{
			top = spot.x >= patch.minimum.x && spot.x <= patch.maximum.x && spot.y >= patch.minimum.y && spot.y <= patch.maximum.y ? std::max(top, town_pavings[patch.paving].top) : top;
		}

		return top;
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_memorial(structures::vec3_s spot)
	{
		const auto ground{ terrain.height(spot.x, spot.z) + town_pavings[structures::town_square].top };
		const auto steps{ static_cast<std::float_t>(std::size(town_memorial_steps)) * town_memorial_rise };
		const auto plinth_top{ ground + steps + town_memorial_plinth };
		const auto bottom{ 0.48f };
		const auto top{ 0.3f };
		const structures::vec3_s low_center{ spot.x, plinth_top, spot.z };
		const structures::vec3_s high_center{ spot.x, plinth_top + town_memorial_needle, spot.z };

		for (auto tier{ 0u }; tier < std::size(town_memorial_steps); tier++)
		{
			solid({ spot.x, ground + town_memorial_rise * (static_cast<std::float_t>(tier) + 0.5f), spot.z }, { town_memorial_steps[tier], town_memorial_rise, town_memorial_steps[tier] }, granite_material, structures::surface_rock);
		}

		solid({ spot.x, ground + steps + town_memorial_plinth * 0.5f, spot.z }, { 1.6f, town_memorial_plinth, 1.6f }, granite_material, structures::surface_rock);

		detail({ spot.x, ground + steps + 0.12f, spot.z }, { 1.85f, 0.24f, 1.85f }, mathematics.quat_identity(), granite_material);
		detail({ spot.x, plinth_top - 0.08f, spot.z }, { 1.85f, 0.16f, 1.85f }, mathematics.quat_identity(), granite_material);

		world.add_box({ spot.x, plinth_top + town_memorial_needle * 0.5f, spot.z }, { bottom * 1.8f, town_memorial_needle, bottom * 1.8f }, mathematics.quat_identity(), structures::surface_rock, structures::contents_solid);

		builder.set_material(granite_material);

		for (auto side{ 0u }; side < 4u; side++)
		{
			const auto angle{ static_cast<std::float_t>(side) * half_pi };
			const structures::vec3_s normal{ std::sin(angle), 0.0f, std::cos(angle) };
			const structures::vec3_s across{ normal.z, 0.0f, -normal.x };
			const auto face{ mathematics.normalize(normal * town_memorial_needle + structures::vec3_s{ 0.0f, bottom - top, 0.0f }) };
			const auto slope{ mathematics.normalize(normal * 0.45f + structures::vec3_s{ 0.0f, top, 0.0f }) };
			const auto left{ high_center + normal * top - across * top };
			const auto right{ high_center + normal * top + across * top };
			const auto peak{ high_center + structures::vec3_s{ 0.0f, 0.45f, 0.0f } };

			builder.quad(low_center + normal * bottom - across * bottom, low_center + normal * bottom + across * bottom, right, left, face);

			const auto first_vertex{ static_cast<std::uint32_t>(builder.vertices.size()) };
			const auto first_index{ static_cast<std::uint32_t>(builder.indices.size()) };

			builder.add_triangle(builder.add_vertex(left, slope, builder.project_uv(left, slope)), builder.add_vertex(right, slope, builder.project_uv(right, slope)), builder.add_vertex(peak, slope, builder.project_uv(peak, slope)));

			builder.compute_tangents(first_vertex, first_index);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_house(structures::vec3_s origin, std::float_t yaw, std::float_t width, std::float_t depth, std::uint32_t floors, std::float_t damage)
	{
		const auto point = [&](std::float_t x, std::float_t z)
			{
				return structures::vec3_s{ origin.x, 0.0f, origin.z } + rotate_yaw({ x, 0.0f, z }, yaw);
			};

		footprints.push_back({ { origin.x, origin.z }, { width * 0.5f, depth * 0.5f }, yaw });

		auto ground{ terrain.height(origin.x, origin.z) };

		for (auto corner{ 0u }; corner < 4u; corner++)
		{
			const auto sample{ point((corner & 1u ? 0.5f : -0.5f) * width, (corner & 2u ? 0.5f : -0.5f) * depth) };

			ground = std::max(ground, terrain.height(sample.x, sample.z));
		}

		const auto level{ ground + 0.3f };
		const auto material{ chance() < 0.4f ? structures::material_wall_concrete : (chance() < 0.5f ? structures::material_concrete_rough : structures::material_wall_slab) };
		const auto half_width{ width * 0.5f };
		const auto half_depth{ depth * 0.5f };
		const auto thickness{ 0.22f };

		solid_yaw({ origin.x, level - 0.8f, origin.z }, { width + 0.3f, 1.6f, depth + 0.3f }, yaw, structures::material_floor_worn, structures::surface_concrete);

		terrain.mask_rectangle(origin, width * 0.5f + 0.4f, depth * 0.5f + 0.4f, yaw);

		for (auto floor{ 0u }; floor < floors; floor++)
		{
			const auto base{ level + static_cast<std::float_t>(floor) * 3.1f };
			const auto top_floor{ floor + 1u == floors };
			const auto wall_damage{ top_floor ? damage : damage * 0.3f };
			const auto door_bottom{ floor ? 0.9f : 0.0f };
			const auto door_top{ floor ? 2.1f : 2.25f };
			const structures::vec4_s front[3] = { { width * 0.2f - 0.55f, width * 0.2f + 0.55f, 0.9f, 2.1f }, { width * 0.5f - 0.55f, width * 0.5f + 0.55f, door_bottom, door_top }, { width * 0.8f - 0.55f, width * 0.8f + 0.55f, 0.9f, 2.1f } };
			const structures::vec4_s back[2] = { { width * 0.3f - 0.5f, width * 0.3f + 0.5f, 0.9f, 2.1f }, { width * 0.7f - 0.5f, width * 0.7f + 0.5f, door_bottom, door_top } };
			const structures::vec4_s side[1] = { { depth * 0.5f - 0.55f, depth * 0.5f + 0.55f, 0.9f, 2.1f } };

			build_wall(point(-half_width, -half_depth + thickness * 0.5f), yaw, width, base, 2.95f, front, 3u, wall_damage, material);
			build_wall(point(half_width, half_depth - thickness * 0.5f), yaw + pi, width, base, 2.95f, back, 2u, wall_damage, material);
			build_wall(point(half_width - thickness * 0.5f, -half_depth + thickness), yaw - half_pi, depth - thickness * 2.0f, base, 2.95f, side, 1u, wall_damage, material);
			build_wall(point(-half_width + thickness * 0.5f, half_depth - thickness), yaw + half_pi, depth - thickness * 2.0f, base, 2.95f, side, 1u, wall_damage, material);

			if (top_floor == false)
			{
				const auto slab_center{ point(0.75f, 0.0f) };
				const auto landing{ point(-half_width + 0.75f, half_depth - 1.0f) };

				solid_yaw({ slab_center.x, base + 3.02f, slab_center.z }, { width - 1.5f, 0.16f, depth }, yaw, structures::material_concrete_rough, structures::surface_concrete);
				solid_yaw({ landing.x, base + 3.02f, landing.z }, { 1.5f, 0.16f, 2.0f }, yaw, structures::material_concrete_rough, structures::surface_concrete);

				stairs(point(-half_width + 0.75f, -half_depth + 0.9f) + structures::vec3_s{ 0.0f, base, 0.0f }, 1.1f, 3.1f, 4.2f, yaw, structures::material_concrete_rough);
			}

			else if (damage < 0.4f)
			{
				solid_yaw({ origin.x, base + 3.05f, origin.z }, { width + 0.3f, 0.2f, depth + 0.3f }, yaw, structures::material_concrete_rough, structures::surface_concrete);
			}

			else if (damage < 0.7f)
			{
				const auto fallen{ point((chance() - 0.5f) * width * 0.4f, (chance() - 0.5f) * depth * 0.4f) };

				detail({ fallen.x, base + 0.9f, fallen.z }, { width * 0.6f, 0.18f, depth * 0.45f }, mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, 0.45f + chance() * 0.3f)), structures::material_concrete_rough);
			}
		}

		if (chance() < 0.75f)
		{
			const auto spot{ point((chance() - 0.5f) * (width - 2.5f) + 0.6f, (chance() - 0.5f) * (depth - 2.5f)) };
			const auto pick{ chance() };

			container_node(pick < 0.45f ? structures::node_toolbox : (pick < 0.8f ? structures::node_box : structures::node_medical), { spot.x, level, spot.z }, yaw + (chance() - 0.5f) * 1.2f);
		}

		if (chance() < 0.35f)
		{
			const auto spot{ point((chance() - 0.5f) * (width - 2.5f) + 0.6f, (chance() - 0.5f) * (depth - 2.5f)) };

			barrel_node({ spot.x, level, spot.z });
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_wall(structures::vec3_s start, std::float_t yaw, std::float_t length, std::float_t base, std::float_t height, const structures::vec4_s* holes, std::uint32_t hole_count, std::float_t damage, std::uint32_t material)
	{
		auto cursor{ 0.0f };

		for (auto index{ 0u }; index <= hole_count; index++)
		{
			const auto limit{ index < hole_count ? holes[index].x : length };

			for (auto from{ cursor }; from < limit - 0.02f;)
			{
				const auto to{ std::min(limit, from + 0.8f + chance() * 0.6f) };
				const auto top{ chance() < damage * 0.85f ? height * (1.0f - chance() * damage * 0.8f) : height };

				wall_piece(start, yaw, from, to, base, base + top, material);

				from = to;
			}

			if (index < hole_count)
			{
				const auto& hole{ holes[index] };

				if (hole.z > 0.01f)
				{
					wall_piece(start, yaw, hole.x, hole.y, base, base + hole.z, material);
				}

				if (chance() > damage * 0.55f)
				{
					wall_piece(start, yaw, hole.x, hole.y, base + hole.w, base + height, material);
				}

				cursor = hole.y;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::wall_piece(structures::vec3_s start, std::float_t yaw, std::float_t from, std::float_t to, std::float_t bottom, std::float_t top, std::uint32_t material)
	{
		if (to - from > 0.02f && top - bottom > 0.05f)
		{
			const auto middle{ start + rotate_yaw({ (from + to) * 0.5f, 0.0f, 0.0f }, yaw) };

			solid_yaw({ middle.x, (bottom + top) * 0.5f, middle.z }, { to - from, top - bottom, 0.22f }, yaw, material, structures::surface_concrete);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_outpost(structures::vec3_s center)
	{
		const auto ground{ terrain.height(center.x, center.z) };

		clearings.push_back({ center.x, 0.0f, center.z, 42.0f });
		hotspots.push_back({ center.x, 0.0f, center.z, 26.0f });
		landmarks.push_back({ { center.x, center.z }, 30.0f, structures::landmark_outpost });

		for (auto index{ 0u }; index < 30u; index++)
		{
			const auto angle{ static_cast<std::float_t>(index) / 30.0f * two_pi };

			if (index % 15u != 0u && chance() < 0.88f)
			{
				ground_prop(index % 3u ? "concrete_road_barrier" : "concrete_road_barrier_02", { center.x + std::sin(angle) * 27.0f, 0.0f, center.z + std::cos(angle) * 27.0f }, angle + half_pi + (chance() - 0.5f) * 0.25f, 1.0f, structures::surface_concrete);
			}
		}

		for (auto index{ 0u }; index < 5u; index++)
		{
			const auto angle{ 0.8f + static_cast<std::float_t>(index) * 1.15f };
			const auto spot{ center + structures::vec3_s{ std::sin(angle) * 15.0f, 0.0f, std::cos(angle) * 15.0f } };
			const auto base{ terrain.height(spot.x, spot.z) - 0.05f };
			const auto yaw{ angle + half_pi + (chance() - 0.5f) * 0.3f };

			container({ spot.x, base, spot.z }, yaw, index % 2u ? structures::material_container_green : structures::material_container_red, index % 3u == 0u);

			terrain.mask_rectangle(spot, 1.4f, index % 3u == 0u ? 6.2f : 3.2f, yaw);
		}

		const auto tower{ center + structures::vec3_s{ 6.0f, 0.0f, -6.0f } };
		const auto tower_base{ terrain.height(tower.x, tower.z) };

		for (auto leg{ 0u }; leg < 4u; leg++)
		{
			solid({ tower.x + (leg & 1u ? 1.4f : -1.4f), tower_base + 3.0f, tower.z + (leg & 2u ? 1.4f : -1.4f) }, { 0.24f, 6.0f, 0.24f }, structures::material_metal_rust, structures::surface_metal);
		}

		solid({ tower.x, tower_base + 6.05f, tower.z }, { 3.4f, 0.14f, 3.4f }, structures::material_plywood, structures::surface_wood);

		for (auto rail{ 0u }; rail < 4u; rail++)
		{
			const auto along_x{ rail < 2u };
			const auto sign{ rail % 2u ? 1.0f : -1.0f };

			if (rail != 1u)
			{
				solid({ tower.x + (along_x ? 0.0f : sign * 1.65f), tower_base + 6.6f, tower.z + (along_x ? sign * 1.65f : 0.0f) }, { along_x ? 3.4f : 0.08f, 1.0f, along_x ? 0.08f : 3.4f }, structures::material_plywood, structures::surface_wood);
			}
		}

		stairs({ tower.x - 1.0f, tower_base, tower.z + 1.8f + 7.2f }, 1.0f, 6.05f, 7.4f, pi, structures::material_metal_rust);

		solid({ tower.x + 0.9f, tower_base + 6.52f, tower.z - 0.95f }, { 1.1f, 0.8f, 0.55f }, structures::material_plywood, structures::surface_wood);
		prop("vintage_radio_transceiver", { tower.x + 0.9f, tower_base + 6.92f, tower.z - 0.95f }, pi, 1.0f, structures::prop_collision_none, structures::surface_metal);

		radio = { tower.x + 0.9f, tower_base + 7.1f, tower.z - 0.95f };
		radio_ready = true;

		solid({ tower.x + 1.4f, tower_base + 6.12f + outpost_mast * 0.5f, tower.z + 1.4f }, { 0.12f, outpost_mast, 0.12f }, structures::material_metal_rust, structures::surface_metal);

		for (auto rung{ 0u }; rung < 4u; rung++)
		{
			const auto height{ tower_base + 9.0f + static_cast<std::float_t>(rung) * 3.2f };

			solid({ tower.x + 1.4f, height, tower.z + 1.4f }, { 1.6f - static_cast<std::float_t>(rung) * 0.3f, 0.06f, 0.06f }, structures::material_metal_rust, structures::surface_metal);
		}

		for (auto index{ 0u }; index < 6u; index++)
		{
			const auto angle{ static_cast<std::float_t>(index) * 1.05f + 0.4f };
			const auto spot{ center + structures::vec3_s{ std::sin(angle) * (6.0f + chance() * 12.0f), 0.0f, std::cos(angle) * (6.0f + chance() * 12.0f) } };

			container_node(index < 3u ? structures::node_military : (index < 5u ? structures::node_toolbox : structures::node_medical), { spot.x, terrain.height(spot.x, spot.z), spot.z }, chance() * two_pi);
		}

		for (auto index{ 0u }; index < 8u; index++)
		{
			const auto angle{ chance() * two_pi };
			const auto spot{ center + structures::vec3_s{ std::sin(angle) * (4.0f + chance() * 18.0f), 0.0f, std::cos(angle) * (4.0f + chance() * 18.0f) } };

			if (index < 4u)
			{
				barrel_node({ spot.x, terrain.height(spot.x, spot.z), spot.z });
			}

			else
			{
				ground_prop(index % 2u ? "old_military_compressor" : "portable_generator", spot, chance() * two_pi, 1.0f, structures::surface_metal);
			}
		}

		for (auto index{ 0u }; index < 3u; index++)
		{
			const auto angle{ 2.6f + static_cast<std::float_t>(index) * 0.35f };
			const auto spot{ center + structures::vec3_s{ std::sin(angle) * 9.0f, 0.0f, std::cos(angle) * 9.0f } };

			solid_yaw({ spot.x, terrain.height(spot.x, spot.z) + 0.45f, spot.z }, { 2.6f, 0.9f, 0.6f }, angle + half_pi, structures::material_burlap, structures::surface_dirt);
		}

		logger.write("maps: outpost at %.0f %.0f ground %.1f", center.x, center.z, ground);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_yard(structures::vec3_s center)
	{
		clearings.push_back({ center.x, 0.0f, center.z, 52.0f });
		hotspots.push_back({ center.x, 0.0f, center.z, 30.0f });
		landmarks.push_back({ { center.x, center.z }, 40.0f, structures::landmark_yard });

		const auto yaw{ 0.35f };
		const auto base{ terrain.height(center.x, center.z) + 0.2f };
		const auto half_width{ 12.0f };
		const auto half_depth{ 8.0f };

		footprints.push_back({ { center.x, center.z }, { half_width, half_depth }, yaw });
		const auto corner = [&](std::float_t x, std::float_t z)
			{
				return structures::vec3_s{ center.x, 0.0f, center.z } + rotate_yaw({ x, 0.0f, z }, yaw);
			};

		solid_yaw({ center.x, base - 0.8f, center.z }, { half_width * 2.0f + 0.4f, 1.6f, half_depth * 2.0f + 0.4f }, yaw, structures::material_floor_garage, structures::surface_concrete);

		terrain.mask_rectangle(center, half_width + 0.5f, half_depth + 0.5f, yaw);

		const structures::vec4_s front[2] = { { 3.0f, 9.0f, 0.0f, 4.6f }, { 15.0f, 21.0f, 0.0f, 4.6f } };
		const structures::vec4_s back[1] = { { 10.5f, 13.5f, 0.0f, 3.0f } };
		const structures::vec4_s side[1] = { { 6.8f, 9.2f, 1.4f, 2.6f } };

		build_wall(corner(-half_width, -half_depth), yaw, half_width * 2.0f, base, 6.0f, front, 2u, 0.35f, structures::material_corrugated_steel);
		build_wall(corner(half_width, half_depth), yaw + pi, half_width * 2.0f, base, 6.0f, back, 1u, 0.45f, structures::material_corrugated_steel);
		build_wall(corner(half_width, -half_depth), yaw - half_pi, half_depth * 2.0f, base, 6.0f, side, 1u, 0.3f, structures::material_corrugated_steel);
		build_wall(corner(-half_width, half_depth), yaw + half_pi, half_depth * 2.0f, base, 6.0f, side, 1u, 0.6f, structures::material_corrugated_steel);

		for (auto beam{ 0u }; beam < 5u; beam++)
		{
			const auto spot{ corner(-half_width + 2.0f + static_cast<std::float_t>(beam) * 5.0f, 0.0f) };

			detail({ spot.x, base + 6.1f, spot.z }, { 0.3f, 0.3f, half_depth * 2.0f }, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), structures::material_metal_rust);
		}

		for (auto sheet{ 0u }; sheet < 4u; sheet++)
		{
			if (sheet != 2u)
			{
				const auto spot{ corner(-half_width + 3.0f + static_cast<std::float_t>(sheet) * 6.0f, 0.0f) };

				solid_yaw({ spot.x, base + 6.3f, spot.z }, { 5.8f, 0.08f, half_depth * 2.0f + 0.6f }, yaw, structures::material_corrugated, structures::surface_metal);
			}
		}

		const auto collapse{ corner(3.5f, 1.0f) };

		detail({ collapse.x, base + 2.4f, collapse.z }, { 5.6f, 0.08f, 11.0f }, mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, 0.55f)), structures::material_corrugated);

		for (auto index{ 0u }; index < 3u; index++)
		{
			const auto spot{ corner(-6.0f + static_cast<std::float_t>(index) * 6.0f, 18.0f + chance() * 4.0f) };

			ground_prop("propane_tank", spot, chance() * two_pi, 3.2f, structures::surface_metal);
		}

		for (auto index{ 0u }; index < 7u; index++)
		{
			const auto spot{ corner((chance() - 0.5f) * 20.0f, (chance() - 0.5f) * 12.0f) };
			const auto pick{ chance() };

			if (pick < 0.3f)
			{
				container_node(structures::node_toolbox, { spot.x, base, spot.z }, chance() * two_pi);
			}

			else if (pick < 0.55f)
			{
				barrel_node({ spot.x, base, spot.z });
			}

			else
			{
				prop(pick < 0.7f ? "tool_cart" : (pick < 0.85f ? "hand_truck" : "industrial_storage_cart"), { spot.x, base, spot.z }, chance() * two_pi, 1.0f, structures::prop_collision_bounds, structures::surface_metal);
			}
		}

		for (auto index{ 0u }; index < 10u; index++)
		{
			const auto angle{ chance() * two_pi };
			const auto spot{ center + structures::vec3_s{ std::sin(angle) * (18.0f + chance() * 22.0f), 0.0f, std::cos(angle) * (18.0f + chance() * 22.0f) } };

			if (index < 5u)
			{
				barrel_node({ spot.x, terrain.height(spot.x, spot.z), spot.z });
			}

			else
			{
				ground_prop(index % 2u ? "old_tyre" : "metal_jerrycan", spot, chance() * two_pi, 1.0f, structures::surface_metal);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::road(structures::vec3_s from, structures::vec3_s to, std::float_t width)
	{
		roads.push_back({ { from.x, from.z }, { to.x, to.z }, width });

		const auto direction{ mathematics.normalize(structures::vec3_s{ to.x - from.x, 0.0f, to.z - from.z }) };
		const auto total{ mathematics.length(structures::vec3_s{ to.x - from.x, 0.0f, to.z - from.z }) };
		const auto yaw{ std::atan2(direction.z, direction.x) * -1.0f };
		const auto segments{ std::max(1u, static_cast<std::uint32_t>(std::ceil(total / 6.0f))) };
		const auto step{ total / static_cast<std::float_t>(segments) };

		for (auto index{ 0u }; index < segments; index++)
		{
			const auto middle{ from + direction * (step * (static_cast<std::float_t>(index) + 0.5f)) };
			const auto height{ std::max(terrain.height(middle.x, middle.z), std::max(terrain.height(middle.x - direction.x * step * 0.5f, middle.z - direction.z * step * 0.5f), terrain.height(middle.x + direction.x * step * 0.5f, middle.z + direction.z * step * 0.5f))) };

			solid_yaw({ middle.x, height - 0.12f, middle.z }, { step + 0.05f, 0.3f, width }, yaw, structures::material_asphalt, structures::surface_concrete);

			terrain.mask_rectangle(middle, step * 0.5f + 0.2f, width * 0.5f + 0.4f, yaw);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::container_node(std::uint32_t kind, structures::vec3_s position, std::float_t yaw)
	{
		if (const auto model{ kind < structures::node_kind_count && node_models[kind][0] ? models.find(node_models[kind]) : nullptr }; model)
		{
			const structures::vec3_s pivot{ (model->bounds_min.x + model->bounds_max.x) * 0.5f, model->bounds_min.y, (model->bounds_min.z + model->bounds_max.z) * 0.5f };
			const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };

			if (crates[kind] == UINT32_MAX)
			{
				crates[kind] = foliage.add_species(node_models[kind], nullptr, crate_far_distance, crate_far_distance, crate_shadow_distance, 0.0f);
			}

			foliage.add(crates[kind], position - rotate_yaw(pivot, yaw), yaw, 1.0f);

			place_collision(model->bounds_min, model->bounds_max, mathematics.multiply(mathematics.multiply(mathematics.translation(-pivot), mathematics.rotation(rotation)), mathematics.translation(position)), rotation, 1.0f, structures::prop_collision_bounds, structures::surface_metal);

			harvest.add(kind, position, 0.55f, UINT32_MAX, -1);
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::barrel_node(structures::vec3_s position)
	{
		const auto kind{ barrels[static_cast<std::uint32_t>(chance() * 2.99f)] };

		if (kind < foliage.species.size())
		{
			foliage.add(kind, position, chance() * two_pi, 1.0f);

			world.add_box(position + structures::vec3_s{ 0.0f, 0.4f, 0.0f }, { 0.48f, 0.8f, 0.48f }, mathematics.quat_identity(), structures::surface_metal, structures::contents_solid);

			harvest.add(structures::node_barrel, position, 0.35f, static_cast<std::uint32_t>(foliage.instances.size() - 1u), static_cast<std::int32_t>(world.brushes.size() - 1u));
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::ground_prop(const char* model_name, structures::vec3_s position, std::float_t yaw, std::float_t scale, std::uint32_t surface)
	{
		prop(model_name, { position.x, terrain.height(position.x, position.z), position.z }, yaw, scale, structures::prop_collision_bounds, surface);
	}
	/*
	//=====================================================================================
	*/
	bool maps_c::place_building(const char* model_name, structures::vec3_s position, std::float_t yaw)
	{
		char far_name[64]{};

		std::snprintf(far_name, sizeof(far_name), "%s_far", model_name);

		if (const auto model{ models.find(model_name) }; model)
		{
			if (building_species.count(model_name) == 0u)
			{
				building_species[model_name] = foliage.add_species(model_name, models.find(far_name) ? far_name : nullptr, building_near_distance, building_far_distance, building_shadow_distance, 0.0f);

				logger.write("maps: first %s at %.1f %.1f %.1f yaw %.2f, %zu parts", model_name, position.x, position.y, position.z, yaw, model->parts.size());
			}

			const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };
			const auto placement{ mathematics.multiply(mathematics.rotation(rotation), mathematics.translation(position)) };

			structures::vec3_s low{ FLT_MAX, FLT_MAX, FLT_MAX };
			structures::vec3_s high{ -FLT_MAX, -FLT_MAX, -FLT_MAX };

			foliage.add(building_species[model_name], position, yaw, 1.0f);

			for (const auto& part : model->parts)
			{
				const auto center{ (part.bounds_min + part.bounds_max) * 0.5f };
				const auto size{ part.bounds_max - part.bounds_min };

				if (std::strncmp(part.name, "col_", 4u) == 0)
				{
					place_collision(part.bounds_min, part.bounds_max, placement, rotation, 1.0f, structures::prop_collision_bounds, surface_named(part.name + 4));
				}

				else if (std::strncmp(part.name, "ramp_", 5u) == 0 && std::strlen(part.name) > 8u)
				{
					const auto along_x{ part.name[6] == 'x' };
					const auto rising{ part.name[5] == 'p' ? (along_x ? half_pi : 0.0f) : (along_x ? -half_pi : pi) };

					world.add_ramp(mathematics.transform_point(center, placement), along_x ? structures::vec3_s{ size.z, size.y, size.x } : size, yaw + rising, surface_named(part.name + 8), structures::contents_solid);
				}

				else if (std::strncmp(part.name, "loot_", 5u) == 0)
				{
					container_node(loot_named(part.name + 5), mathematics.transform_point({ center.x, part.bounds_min.y, center.z }, placement), yaw);
				}

				else if (std::strncmp(part.name, "light_", 6u) == 0)
				{
					glow(part.name + 6, mathematics.transform_point(center, placement), std::strncmp(model_name, rig_prefix, std::strlen(rig_prefix)) == 0);
				}

				else if (part.index_count)
				{
					low = mathematics.minimum(low, part.bounds_min);
					high = mathematics.maximum(high, part.bounds_max);
				}
			}

			const auto middle{ mathematics.transform_point((low + high) * 0.5f, placement) };

			footprints.push_back({ { middle.x, middle.z }, { (high.x - low.x) * 0.5f, (high.z - low.z) * 0.5f }, yaw });

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t maps_c::surface_named(const char* text)
	{
		for (auto index{ 0u }; index < structures::surface_count; index++)
		{
			if (const auto length{ std::strlen(surface_names[index]) }; std::strncmp(text, surface_names[index], length) == 0 && (text[length] == '_' || text[length] == 0))
			{
				return index;
			}
		}

		return structures::surface_concrete;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t maps_c::loot_named(const char* text)
	{
		for (auto index{ 0u }; index < std::size(loot_marker_names); index++)
		{
			if (const auto length{ std::strlen(loot_marker_names[index]) }; std::strncmp(text, loot_marker_names[index], length) == 0 && (text[length] == '_' || text[length] == 0))
			{
				return loot_marker_nodes[index];
			}
		}

		return structures::node_box;
	}
	/*
	//=====================================================================================
	*/
	void maps_c::load_routes()
	{
		paths.clear();
		stations.clear();
		corridor.assign(static_cast<std::size_t>(route_cells) * route_cells, 0u);

		if (const auto entry{ pak.find("world_stations") }; entry && entry->size >= sizeof(std::uint32_t))
		{
			stream_reader_c reader{};

			reader.reset(pak.data(entry), static_cast<std::uint32_t>(entry->size));

			stations.resize(std::min(reader.u32(), station_limit));

			reader.bytes(stations.data(), static_cast<std::uint32_t>(stations.size() * sizeof(structures::station_s)));

			if (reader.overflow)
			{
				stations.clear();
			}
		}

		if (const auto entry{ pak.find("world_routes") }; entry && entry->size >= sizeof(std::uint32_t))
		{
			stream_reader_c reader{};

			reader.reset(pak.data(entry), static_cast<std::uint32_t>(entry->size));

			const auto count{ reader.u32() };

			for (auto route{ 0u }; route < count && reader.overflow == false; route++)
			{
				structures::route_path_s path{};

				path.kind = reader.u32();
				path.closed = reader.u32() != 0u;
				path.width = reader.f32();
				path.points.resize(std::min(reader.u32(), 1000000u));

				reader.bytes(path.points.data(), static_cast<std::uint32_t>(path.points.size() * sizeof(structures::vec3_s)));

				if (reader.overflow == false && path.points.size() > 1u)
				{
					paths.push_back(std::move(path));
				}
			}
		}

		for (const auto& path : paths)
		{
			const auto reach{ path.width * 0.5f + route_clear_margin + route_cell * 0.5f };
			const auto span{ static_cast<std::int32_t>(std::ceil(reach / route_cell)) };

			for (const auto& point : path.points)
			{
				const auto column{ static_cast<std::int32_t>((point.x - terrain_origin) / route_cell) };
				const auto row{ static_cast<std::int32_t>((point.z - terrain_origin) / route_cell) };

				for (auto dz{ -span }; dz <= span; dz++)
				{
					for (auto dx{ -span }; dx <= span; dx++)
					{
						const auto cx{ column + dx };
						const auto cz{ row + dz };
						const auto x{ terrain_origin + (static_cast<std::float_t>(cx) + 0.5f) * route_cell };
						const auto z{ terrain_origin + (static_cast<std::float_t>(cz) + 0.5f) * route_cell };

						if (cx >= 0 && cz >= 0 && cx < static_cast<std::int32_t>(route_cells) && cz < static_cast<std::int32_t>(route_cells) && (x - point.x) * (x - point.x) + (z - point.z) * (z - point.z) < reach * reach)
						{
							corridor[static_cast<std::size_t>(cz) * route_cells + static_cast<std::size_t>(cx)] = static_cast<std::uint8_t>(path.kind + 1u);
						}
					}
				}
			}
		}

		logger.write("maps: %zu routes and %zu stations loaded", paths.size(), stations.size());
	}
	/*
	//=====================================================================================
	*/
	bool maps_c::on_route(std::float_t x, std::float_t z)
	{
		const auto column{ static_cast<std::int32_t>(std::floor((x - terrain_origin) / route_cell)) };
		const auto row{ static_cast<std::int32_t>(std::floor((z - terrain_origin) / route_cell)) };

		return corridor.size() && column >= 0 && row >= 0 && column < static_cast<std::int32_t>(route_cells) && row < static_cast<std::int32_t>(route_cells) && corridor[static_cast<std::size_t>(row) * route_cells + static_cast<std::size_t>(column)] != 0u;
	}
	/*
	//=====================================================================================
	*/
	std::float_t maps_c::route_gap(std::float_t x, std::float_t z)
	{
		auto result{ FLT_MAX };

		for (const auto& path : paths)
		{
			for (const auto& point : path.points)
			{
				result = std::min(result, mathematics.length(structures::vec2_s{ point.x - x, point.z - z }) - path.width * 0.5f);
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_routes()
	{
		track_materials[structures::track_material_asphalt] = models.variant(structures::material_asphalt, { 0.52f, 0.5f, 0.48f }, 0.0f);
		track_materials[structures::track_material_dirt] = models.variant(structures::material_terrain_dirt, { 0.9f, 0.85f, 0.8f }, 0.0f);
		track_materials[structures::track_material_ballast] = models.variant(structures::material_terrain_gravel, { 0.62f, 0.58f, 0.54f }, 0.0f);
		track_materials[structures::track_material_sleeper] = models.variant(structures::material_plywood, { 0.36f, 0.29f, 0.23f }, 0.0f);
		track_materials[structures::track_material_rail] = models.variant(structures::material_metal_rust, { 0.46f, 0.4f, 0.37f }, 0.35f);

		for (const auto& path : paths)
		{
			if (path.kind == structures::route_rail)
			{
				build_rail(path);

				find_crossings(path);

				build_stations(path);

				build_crossings();
			}

			else
			{
				build_road(path, static_cast<std::uint32_t>(&path - paths.data()));
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_road(const structures::route_path_s& path, std::uint32_t order)
	{
		const auto half{ path.width * 0.5f };
		const auto count{ static_cast<std::uint32_t>(path.points.size()) };
		const auto lift{ road_lift + static_cast<std::float_t>(order) * road_lift_step };
		const auto first_vertex{ static_cast<std::uint32_t>(builder.vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(builder.indices.size()) };
		const std::float_t offsets[4] = { half + road_skirt, half, -half, -half - road_skirt };
		const std::float_t drops[4] = { road_skirt_drop, 0.0f, 0.0f, road_skirt_drop };
		const std::float_t leans[4] = { 0.35f, 0.0f, 0.0f, -0.35f };

		auto travelled{ 0.0f };

		std::uint32_t previous_ring[4]{};

		builder.set_material(track_materials[path.width >= 6.0f ? structures::track_material_asphalt : structures::track_material_dirt]);

		for (auto index{ 0u }; index < count; index++)
		{
			const auto& point{ path.points[index] };
			const auto& previous{ path.points[index ? index - 1u : 0u] };
			const auto& next{ path.points[std::min(index + 1u, count - 1u)] };
			const auto along{ mathematics.normalize(structures::vec3_s{ next.x - previous.x, 0.0f, next.z - previous.z }) };
			const structures::vec3_s side{ along.z, 0.0f, -along.x };
			const structures::vec3_s surface{ point.x, point.y + lift, point.z };

			std::uint32_t ring[4]{};

			travelled += mathematics.length(structures::vec3_s{ point.x - previous.x, 0.0f, point.z - previous.z });

			for (auto corner{ 0u }; corner < 4u; corner++)
			{
				ring[corner] = builder.add_vertex(surface + side * offsets[corner] - structures::vec3_s{ 0.0f, drops[corner], 0.0f }, mathematics.normalize(structures::vec3_s{ 0.0f, 1.0f, 0.0f } + side * leans[corner]), { offsets[corner] / road_tile, travelled / road_tile });
			}

			for (auto strip{ 0u }; strip < 3u && index; strip++)
			{
				builder.add_triangle(previous_ring[strip], previous_ring[strip + 1u], ring[strip + 1u]);
				builder.add_triangle(previous_ring[strip], ring[strip + 1u], ring[strip]);
			}

			if (index % 4u == 0u && index + 4u < count)
			{
				const auto& ahead{ path.points[index + 4u] };

				roads.push_back({ { point.x, point.z }, { ahead.x, ahead.z }, path.width });

				terrain.mask_rectangle({ (point.x + ahead.x) * 0.5f, 0.0f, (point.z + ahead.z) * 0.5f }, half + 0.6f, mathematics.length(structures::vec3_s{ ahead.x - point.x, 0.0f, ahead.z - point.z }) * 0.5f + 0.5f, std::atan2(ahead.x - point.x, ahead.z - point.z));
			}

			std::copy(std::begin(ring), std::end(ring), std::begin(previous_ring));
		}

		builder.compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	bool maps_c::on_crossing(structures::vec3_s point)
	{
		for (const auto& path : paths)
		{
			if (path.kind == structures::route_road)
			{
				const auto reach{ path.width * 0.5f + crossing_overhang };

				for (auto index{ 0u }; index + 1u < path.points.size(); index++)
				{
					const auto& from{ path.points[index] };
					const structures::vec2_s span{ path.points[index + 1u].x - from.x, path.points[index + 1u].z - from.z };

					if (std::fabs(point.x - from.x) < crossing_search && std::fabs(point.z - from.z) < crossing_search)
					{
						const auto along{ mathematics.saturate(((point.x - from.x) * span.x + (point.z - from.z) * span.y) / std::max(span.x * span.x + span.y * span.y, 0.0001f)) };

						if (mathematics.length(structures::vec2_s{ point.x - from.x - span.x * along, point.z - from.z - span.y * along }) < reach)
						{
							return true;
						}
					}
				}
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool maps_c::lay_panels(const structures::route_path_s& path)
	{
		const auto panel{ models.find("rail_track") };
		const auto plain{ panel ? foliage.add_species("rail_track", "rail_track_far", rail_panel_near, rail_panel_far, rail_panel_shadow, rail_panel_sway) : UINT32_MAX };
		const auto weedy{ plain != UINT32_MAX && models.find("rail_track_weeds") ? foliage.add_species("rail_track_weeds", "rail_track_weeds_far", rail_panel_near, rail_panel_far, rail_panel_shadow, rail_panel_sway) : plain };

		if (plain != UINT32_MAX && path.points.size() > 2u)
		{
			const auto count{ static_cast<std::uint32_t>(path.points.size()) };
			const auto segments{ path.closed ? count : count - 1u };

			std::vector<std::float_t> reach(static_cast<std::size_t>(segments) + 1u, 0.0f);

			for (auto index{ 0u }; index < segments; index++)
			{
				reach[index + 1u] = reach[index] + mathematics.distance(path.points[index], path.points[(index + 1u) % count]);
			}

			const auto total{ reach.back() };
			const auto span{ panel->bounds_max.z - panel->bounds_min.z };
			const auto pieces{ std::max(1u, static_cast<std::uint32_t>(std::round(total / std::max(span, 1.0f)))) };
			const auto scale{ total / (static_cast<std::float_t>(pieces) * std::max(span, 1.0f)) };
			const auto length{ span * scale };

			const auto sample = [&](std::float_t along)
				{
					const auto wrapped{ path.closed ? std::fmod(std::fmod(along, total) + total, total) : std::clamp(along, 0.0f, total) };
					const auto upper{ std::upper_bound(reach.begin(), reach.end(), wrapped) };
					const auto index{ static_cast<std::size_t>(std::clamp<std::ptrdiff_t>(upper - reach.begin() - 1, 0, static_cast<std::ptrdiff_t>(segments) - 1)) };
					const auto gap{ reach[index + 1u] - reach[index] };

					return mathematics.lerp(path.points[index], path.points[(index + 1u) % count], gap > 0.0001f ? (wrapped - reach[index]) / gap : 0.0f);
				};

			for (auto piece{ 0u }; piece < pieces; piece++)
			{
				const auto start{ static_cast<std::float_t>(piece) * length };
				const auto first{ sample(start) };
				const auto last{ sample(start + length) };
				const auto head{ sample(start + 1.0f) - first };
				const auto tail{ last - sample(start + length - 1.0f) };
				const auto chord{ last - first };
				const auto turn{ mathematics.angle_difference(std::atan2(head.x, head.z), std::atan2(tail.x, tail.z)) };
				const auto bend{ turn / length };
				const auto reached{ -panel->bounds_min.z * scale };
				const auto heading{ std::atan2(chord.x, chord.z) - turn * 0.5f };
				const auto slope{ (last.y - first.y) / length };
				const auto arc{ std::fabs(bend) > 0.00001f ? structures::vec3_s{ (1.0f - std::cos(bend * reached)) / bend, 0.0f, std::sin(bend * reached) / bend } : structures::vec3_s{ 0.0f, 0.0f, reached } };
				const auto origin{ first + rotate_yaw(arc, heading) + structures::vec3_s{ 0.0f, slope * reached + rail_head - panel->bounds_max.y * scale, 0.0f } };

				foliage.add_bent(mathematics.hash_float(piece * 7919u + 13u) < rail_panel_weeds ? weedy : plain, origin, heading + bend * reached, scale, bend, slope);
			}

			logger.write("maps: %u track panels of %.2f m on a %.0f m line", pieces, length, total);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_stations(const structures::route_path_s& path)
	{
		std::vector<std::float_t> reach;

		measure(path, reach);

		for (const auto& station : stations)
		{
			const auto head{ reach[std::min(static_cast<std::size_t>(station.index), reach.size() - 1u)] };
			const auto side{ station.side };
			const auto front{ head + platform_lead };
			const auto back{ front - platform_module * static_cast<std::float_t>(platform_modules) };

			for (auto piece{ 0u }; piece < platform_modules; piece++)
			{
				railside("rail_platform", path, reach, front - platform_module * (static_cast<std::float_t>(piece) + 0.5f), side * platform_offset, 0.0f, { side, 0.0f });
			}

			railside("rail_platform_end", path, reach, front + platform_ramp, side * platform_offset, 0.0f, { -1.0f, 0.0f });
			railside("rail_platform_end", path, reach, back - platform_ramp, side * platform_offset, 0.0f, { 1.0f, 0.0f });
			railside("rail_signal", path, reach, back - signal_back, -signal_offset, 0.0f, { 0.0f, 1.0f });

			for (const auto& fittings : station_kits)
			{
				if (fittings.landmark == station.landmark && fittings.building)
				{
					railside("bld_station", path, reach, (front + back) * 0.5f, side * station_offset, station_floor, { side, 0.0f });
				}

				if (fittings.landmark == station.landmark && fittings.signal_box)
				{
					railside("rail_signal_box", path, reach, head - signal_box_back, -side * signal_box_offset, 0.0f, { -side, 0.0f });
				}

				if (fittings.landmark == station.landmark && fittings.water_tower)
				{
					railside("rail_water_tower", path, reach, head - water_tower_back, -side * water_tower_offset, 0.0f, { -side, 0.0f });
				}
			}

			for (auto along{ back - platform_ramp }; along < front + platform_ramp + station_clearing_step; along += station_clearing_step)
			{
				const auto spot{ line_at(path, reach, along) };

				clearings.push_back({ spot.x, 0.0f, spot.z, station_clearing });
			}

			const auto stop{ line_at(path, reach, head) };

			logger.write("maps: station %u at %.0f %.1f %.0f, %.0f m along, platforms on the %s", station.landmark, stop.x, stop.y, stop.z, head, side > 0.0f ? "right" : "left");
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::find_crossings(const structures::route_path_s& rail)
	{
		std::vector<std::float_t> reach;

		measure(rail, reach);

		const auto count{ static_cast<std::uint32_t>(rail.points.size()) };
		const auto segments{ static_cast<std::uint32_t>(reach.size()) - 1u };

		crossings.clear();

		for (const auto& path : paths)
		{
			for (auto step{ 0u }; path.kind == structures::route_road && step + 1u < path.points.size(); step++)
			{
				const auto& start{ path.points[step] };
				const structures::vec2_s run{ path.points[step + 1u].x - start.x, path.points[step + 1u].z - start.z };

				for (auto index{ 0u }; index < segments; index++)
				{
					const auto& from{ rail.points[index] };
					const auto& to{ rail.points[(index + 1u) % count] };
					const structures::vec2_s span{ to.x - from.x, to.z - from.z };
					const structures::vec2_s gap{ from.x - start.x, from.z - start.z };
					const auto denominator{ run.x * span.y - run.y * span.x };

					if (std::fabs(gap.x) < crossing_search && std::fabs(gap.y) < crossing_search && std::fabs(denominator) > 0.0001f)
					{
						const auto road_part{ (gap.x * span.y - gap.y * span.x) / denominator };
						const auto rail_part{ (gap.x * run.y - gap.y * run.x) / denominator };

						if (road_part >= 0.0f && road_part < 1.0f && rail_part >= 0.0f && rail_part < 1.0f)
						{
							crossings.push_back({ mathematics.lerp(from, to, rail_part), mathematics.normalize(structures::vec3_s{ span.x, 0.0f, span.y }), mathematics.normalize(structures::vec3_s{ run.x, 0.0f, run.y }), mathematics.lerp(reach[index], reach[index + 1u], rail_part), path.width });
						}
					}
				}
			}
		}

		for (const auto& crossing : crossings)
		{
			logger.write("maps: level crossing at %.0f %.1f %.0f, %.0f m along the line, %.0f degrees", crossing.position.x, crossing.position.y, crossing.position.z, crossing.along, radians_to_degrees(std::acos(std::fabs(mathematics.dot(crossing.rail, crossing.road)))));
		}
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_crossings()
	{
		for (const auto& crossing : crossings)
		{
			const structures::vec3_s verge{ crossing.road.z, 0.0f, -crossing.road.x };

			for (auto side{ -1.0f }; side <= 1.0f; side += 2.0f)
			{
				const auto away{ verge_away(crossing, side) };
				const auto left{ mathematics.dot(away, crossing.road) >= 0.0f ? 1.0f : -1.0f };
				const auto board{ gate_hinge(crossing, side, left) + away * crossing_sign_back + verge * (left * crossing_sign_margin) };

				for (auto edge{ -1.0f }; edge <= 1.0f; edge += 2.0f)
				{
					place_building(crossing_post_model, post_spot(crossing, side, edge), post_yaw(crossing, side, edge));
				}

				place_building(crossing_sign_model, { board.x, terrain.height(board.x, board.z), board.z }, verge_yaw(crossing, side) + crossing_sign_turn);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s maps_c::gate_hinge(const structures::crossing_s& crossing, std::float_t side, std::float_t edge)
	{
		const structures::vec3_s across{ crossing.rail.z, 0.0f, -crossing.rail.x };
		const structures::vec3_s verge{ crossing.road.z, 0.0f, -crossing.road.x };
		const auto reach{ crossing.width * 0.5f + crossing_gate_margin };
		const auto slant{ mathematics.dot(crossing.road, across) };
		const auto steady{ std::fabs(slant) > crossing_slant_floor ? slant : (slant >= 0.0f ? crossing_slant_floor : -crossing_slant_floor) };
		const auto spot{ crossing.position + verge * (edge * reach) + crossing.road * ((side * crossing_gate_clear - edge * reach * mathematics.dot(verge, across)) / steady) };

		return { spot.x, terrain.height(spot.x, spot.z), spot.z };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s maps_c::gate_toward(const structures::crossing_s& crossing, std::float_t side, std::float_t edge)
	{
		const auto other{ gate_hinge(crossing, side, -edge) - gate_hinge(crossing, side, edge) };

		return mathematics.normalize(structures::vec3_s{ other.x, 0.0f, other.z });
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s maps_c::post_spot(const structures::crossing_s& crossing, std::float_t side, std::float_t edge)
	{
		const auto spot{ gate_hinge(crossing, side, edge) - gate_toward(crossing, side, edge) * crossing_pivot_offset };

		return { spot.x, terrain.height(spot.x, spot.z), spot.z };
	}
	/*
	//=====================================================================================
	*/
	std::float_t maps_c::post_yaw(const structures::crossing_s& crossing, std::float_t side, std::float_t edge)
	{
		const auto toward{ gate_toward(crossing, side, edge) };

		return std::atan2(-toward.z, toward.x) + crossing_post_turn;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s maps_c::verge_away(const structures::crossing_s& crossing, std::float_t side)
	{
		const structures::vec3_s across{ crossing.rail.z, 0.0f, -crossing.rail.x };

		return crossing.road * (mathematics.dot(crossing.road, across) * side >= 0.0f ? 1.0f : -1.0f);
	}
	/*
	//=====================================================================================
	*/
	std::float_t maps_c::verge_yaw(const structures::crossing_s& crossing, std::float_t side)
	{
		const auto away{ verge_away(crossing, side) };

		return std::atan2(-away.x, -away.z);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::railside(const char* model_name, const structures::route_path_s& path, const std::vector<std::float_t>& reach, std::float_t along, std::float_t offset, std::float_t lift, structures::vec2_s facing)
	{
		const auto point{ line_at(path, reach, along) };
		const auto chord{ line_at(path, reach, along + 1.0f) - line_at(path, reach, along - 1.0f) };
		const auto forward{ mathematics.normalize(structures::vec3_s{ chord.x, 0.0f, chord.z }) };
		const structures::vec3_s right{ forward.z, 0.0f, -forward.x };
		const auto toward{ right * facing.x + forward * facing.y };

		place_building(model_name, point + right * offset + structures::vec3_s{ 0.0f, lift, 0.0f }, std::atan2(toward.x, toward.z));
	}
	/*
	//=====================================================================================
	*/
	void maps_c::measure(const structures::route_path_s& path, std::vector<std::float_t>& reach)
	{
		const auto count{ static_cast<std::uint32_t>(path.points.size()) };
		const auto segments{ path.closed ? count : count - 1u };

		reach.assign(static_cast<std::size_t>(segments) + 1u, 0.0f);

		for (auto index{ 0u }; index < segments; index++)
		{
			reach[index + 1u] = reach[index] + mathematics.distance(path.points[index], path.points[(index + 1u) % count]);
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s maps_c::line_at(const structures::route_path_s& path, const std::vector<std::float_t>& reach, std::float_t along)
	{
		const auto count{ static_cast<std::uint32_t>(path.points.size()) };
		const auto segments{ static_cast<std::ptrdiff_t>(reach.size()) - 1 };
		const auto total{ reach.back() };
		const auto wrapped{ path.closed ? std::fmod(std::fmod(along, total) + total, total) : std::clamp(along, 0.0f, total) };
		const auto upper{ std::upper_bound(reach.begin(), reach.end(), wrapped) };
		const auto index{ static_cast<std::size_t>(std::clamp<std::ptrdiff_t>(upper - reach.begin() - 1, 0, segments - 1)) };
		const auto gap{ reach[index + 1u] - reach[index] };

		return mathematics.lerp(path.points[index], path.points[(index + 1u) % count], gap > 0.0001f ? (wrapped - reach[index]) / gap : 0.0f);
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_rail(const structures::route_path_s& path)
	{
		const auto count{ static_cast<std::uint32_t>(path.points.size()) };
		const auto limit{ path.closed ? count + 1u : count };
		const auto paneled{ lay_panels(path) };

		auto travelled{ 0.0f };
		auto next_sleeper{ 0.0f };

		std::uint32_t previous_ring[4]{};

		for (auto step{ 0u }; step < limit; step++)
		{
			const auto index{ step % count };
			const auto& point{ path.points[index] };
			const auto& before{ path.points[(index + count - 1u) % count] };
			const auto& after{ path.points[(index + 1u) % count] };
			const auto along{ mathematics.normalize(structures::vec3_s{ after.x - before.x, 0.0f, after.z - before.z }) };
			const structures::vec3_s side{ along.z, 0.0f, -along.x };
			const structures::vec3_s up{ 0.0f, 1.0f, 0.0f };
			const std::float_t offsets[4] = { -2.5f, -1.55f, 1.55f, 2.5f };
			const std::float_t lifts[4] = { -0.08f, rail_ballast_top, rail_ballast_top, -0.08f };

			std::uint32_t ring[4]{};

			builder.set_material(track_materials[structures::track_material_ballast]);

			for (auto corner{ 0u }; corner < 4u && paneled == false; corner++)
			{
				ring[corner] = builder.add_vertex(point + side * offsets[corner] + up * lifts[corner], mathematics.normalize(up + side * (corner == 0u ? -0.35f : (corner == 3u ? 0.35f : 0.0f))), { 0.0f, 0.0f });
			}

			if (step)
			{
				for (auto strip{ 0u }; strip < 3u && paneled == false; strip++)
				{
					builder.add_triangle(previous_ring[strip], previous_ring[strip + 1u], ring[strip + 1u]);
					builder.add_triangle(previous_ring[strip], ring[strip + 1u], ring[strip]);
				}

				const auto& from{ path.points[(step - 1u) % count] };
				const auto span{ point - from };
				const auto length{ mathematics.length(span) };
				const auto forward{ span / std::max(length, 0.001f) };
				const auto across{ mathematics.normalize(mathematics.cross(up, forward)) };
				const auto rotation{ mathematics.quat_from_basis(across, mathematics.cross(forward, across), forward) };
				const auto middle{ (point + from) * 0.5f };

				builder.set_material(track_materials[structures::track_material_rail]);

				for (auto rail{ -1.0f }; rail <= 1.0f && paneled == false; rail += 2.0f)
				{
					builder.box_faces(middle + across * (rail * rail_gauge * 0.5f) + up * (rail_head - 0.075f), { 0.07f, 0.15f, length + 0.02f }, rotation, 0x07u);
				}

				builder.set_material(track_materials[structures::track_material_sleeper]);

				for (; next_sleeper < travelled + length && paneled == false; next_sleeper += rail_sleeper_spacing)
				{
					builder.box_faces(from + forward * (next_sleeper - travelled) + up * (rail_head - 0.22f), { 2.6f, 0.14f, 0.24f }, rotation, 0x37u);
				}

				if (on_crossing(middle))
				{
					for (const auto offset : crossing_boards)
					{
						builder.box_faces(middle + across * offset + up * (rail_head - crossing_board_sink - crossing_board_depth * 0.5f), { crossing_board_width, crossing_board_depth, length + 0.02f }, rotation, 0x37u);
					}
				}

				if (step % 2u == 0u)
				{
					world.add_box(middle + up * (rail_ballast_top - 0.3f), { 3.1f, 0.6f, length * 2.0f + 0.4f }, rotation, structures::surface_gravel, structures::contents_solid);
				}

				travelled += length;
			}

			if (step % 4u == 0u)
			{
				const auto& ahead{ path.points[(index + 4u) % count] };

				terrain.mask_rectangle({ (point.x + ahead.x) * 0.5f, 0.0f, (point.z + ahead.z) * 0.5f }, 3.2f, mathematics.length(structures::vec3_s{ ahead.x - point.x, 0.0f, ahead.z - point.z }) * 0.5f + 0.5f, std::atan2(ahead.x - point.x, ahead.z - point.z));
			}

			std::copy(std::begin(ring), std::end(ring), std::begin(previous_ring));
		}
	}
	/*
	//=====================================================================================
	*/
	bool maps_c::cleared(std::float_t x, std::float_t z)
	{
		if (on_route(x, z))
		{
			return true;
		}

		for (const auto& clearing : clearings)
		{
			if ((x - clearing.x) * (x - clearing.x) + (z - clearing.z) * (z - clearing.z) < clearing.w * clearing.w)
			{
				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	std::float_t maps_c::chance()
	{
		layout_seed ^= layout_seed << 13u;
		layout_seed ^= layout_seed >> 17u;
		layout_seed ^= layout_seed << 5u;

		return static_cast<std::float_t>(layout_seed & 0xFFFFFFu) / 16777216.0f;
	}
	/*
	//=====================================================================================
	*/
	void maps_c::build_test_scene()
	{
		std::snprintf(info.name, sizeof(info.name), "%s", "Test");
		std::snprintf(info.sky, sizeof(info.sky), "%s", "qwantani_late_afternoon_puresky");

		info.sky_rotation = degrees_to_radians(35.0f);
		info.kill_height = -20.0f;
		info.probe_min = { -20.0f, 0.25f, -20.0f };
		info.probe_max = { 20.0f, 8.25f, 30.0f };
		info.probes = true;

		slab({ -60.0f, -0.5f, -60.0f }, { 60.0f, 0.0f, 60.0f }, structures::material_floor_hangar, structures::surface_concrete);

		for (auto index{ 0u }; index < structures::material_count; index++)
		{
			const auto column_index{ static_cast<std::float_t>(index % 12u) };
			const auto row{ static_cast<std::float_t>(index / 12u) };

			solid({ -13.0f + column_index * 2.4f, 0.7f, 8.0f + row * 3.0f }, { 1.4f, 1.4f, 1.4f }, index, structures::surface_concrete);

			builder.set_material(index);
			builder.sphere({ -13.0f + column_index * 2.4f, 2.1f, 8.0f + row * 3.0f }, 0.55f, 32u, 16u);
		}

		stairs({ 0.0f, 0.0f, -6.0f }, 1.5f, 3.0f, 5.0f, 0.0f, structures::material_tread_plate);

		grating({ -1.0f, 2.8f, -1.0f }, { 1.0f, 3.0f, 3.0f });

		prop("old_military_crate", { 4.0f, 0.0f, -4.0f }, 0.3f, 1.0f, structures::prop_collision_bounds, structures::surface_wood);
		container({ 9.0f, 0.0f, 0.0f }, 0.2f, structures::material_container_red, true);
		prop("concrete_road_barrier", { -5.0f, 0.0f, -4.0f }, 0.5f, 1.0f, structures::prop_collision_bounds, structures::surface_concrete);
		prop("barrel_01", { -3.0f, 0.0f, -8.0f }, 0.0f, 1.0f, structures::prop_collision_bounds, structures::surface_metal);

		spawn({ 0.0f, 0.0f, -10.0f }, 0.0f, structures::team_alpha);
		spawn({ 0.0f, 0.0f, 10.0f }, pi, structures::team_bravo);
	}
}

//=====================================================================================
