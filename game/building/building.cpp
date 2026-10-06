
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	building_c building;

	bool building_c::create()
	{
		auto ghost{ materials.gpu_materials[structures::material_light_white] };

		ghost.emissive = { 0.12f, 0.5f, 1.5f };

		materials.gpu_materials.push_back(ghost);

		ghost_valid = static_cast<std::uint32_t>(materials.gpu_materials.size() - 1u);

		ghost.emissive = { 1.5f, 0.18f, 0.1f };

		materials.gpu_materials.push_back(ghost);

		ghost_invalid = static_cast<std::uint32_t>(materials.gpu_materials.size() - 1u);
		wood = models.variant(structures::material_plywood, { 0.78f, 0.62f, 0.46f }, 0.0f);

		materials.upload();

		build_meshes();

		ready = std::all_of(std::begin(meshes), std::end(meshes), [](const structures::mesh_s& mesh) { return mesh.vertex_buffer != nullptr; });

		logger.write("building: %s", ready ? "ready" : "incomplete");

		return ready;
	}
	/*
	//=====================================================================================
	*/
	void building_c::destroy()
	{
		for (auto& mesh : meshes)
		{
			functions::release(mesh.vertex_buffer);
			functions::release(mesh.index_buffer);

			mesh = {};
		}

		for (auto& row : tier_meshes)
		{
			for (auto& mesh : row)
			{
				functions::release(mesh.vertex_buffer);
				functions::release(mesh.index_buffer);

				mesh = {};
			}
		}

		functions::release(keypad_mesh.vertex_buffer);
		functions::release(keypad_mesh.index_buffer);

		keypad_mesh = {};

		clear();

		ready = false;
	}
	/*
	//=====================================================================================
	*/
	void building_c::clear()
	{
		placed.clear();
		containers.clear();
		by_brush.clear();
		authorized.clear();
		locks.clear();

		bag = -1;
		preview = {};
	}
	/*
	//=====================================================================================
	*/
	void building_c::panel(std::uint32_t material, structures::vec3_s minimum, structures::vec3_s maximum)
	{
		const auto first_vertex{ static_cast<std::uint32_t>(piece_builder.vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(piece_builder.indices.size()) };

		piece_builder.set_material(material);
		piece_builder.box((minimum + maximum) * 0.5f, maximum - minimum, mathematics.quat_identity());
		piece_builder.compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void building_c::build_meshes()
	{
		const auto dark{ models.variant(structures::material_plywood, { 0.42f, 0.32f, 0.23f }, 0.0f) };
		const auto rock{ models.find("rock_09") };
		const auto snag{ models.find("tree_dead_0") };

		bark = snag && snag->parts.size() && snag->indices.size() ? snag->vertices[snag->indices[snag->parts[0].first_index]].material : dark;

		tier_materials[0] = -1.0f;
		tier_materials[1] = -1.0f;
		tier_materials[2] = static_cast<std::float_t>(models.variant(structures::material_wall_slab, { 0.86f, 0.84f, 0.8f }, 0.0f));
		tier_materials[3] = static_cast<std::float_t>(models.variant(structures::material_metal_sheet, { 0.9f, 0.9f, 0.92f }, 0.0f));

		piece_builder.clear();
		panel(wood, { -1.5f, -1.6f, -1.5f }, { 1.5f, 0.0f, 1.5f });
		panel(dark, { -1.55f, -0.18f, -1.55f }, { 1.55f, 0.02f, 1.55f });
		piece_builder.upload(meshes[structures::piece_foundation]);

		piece_builder.clear();
		panel(wood, { -1.5f, 0.0f, -0.1f }, { 1.5f, 3.0f, 0.1f });
		panel(dark, { -1.5f, 0.0f, -0.13f }, { 1.5f, 0.2f, 0.13f });
		panel(dark, { -1.5f, 2.8f, -0.13f }, { 1.5f, 3.0f, 0.13f });
		piece_builder.upload(meshes[structures::piece_wall]);

		piece_builder.clear();
		panel(wood, { -1.5f, 0.0f, -0.1f }, { -0.55f, 3.0f, 0.1f });
		panel(wood, { 0.55f, 0.0f, -0.1f }, { 1.5f, 3.0f, 0.1f });
		panel(wood, { -0.55f, 2.2f, -0.1f }, { 0.55f, 3.0f, 0.1f });
		panel(dark, { -0.62f, 2.12f, -0.13f }, { 0.62f, 2.24f, 0.13f });
		piece_builder.upload(meshes[structures::piece_doorway]);

		piece_builder.clear();
		panel(wood, { -1.5f, 0.0f, -0.1f }, { -0.55f, 3.0f, 0.1f });
		panel(wood, { 0.55f, 0.0f, -0.1f }, { 1.5f, 3.0f, 0.1f });
		panel(wood, { -0.55f, 0.0f, -0.1f }, { 0.55f, 1.1f, 0.1f });
		panel(wood, { -0.55f, 2.1f, -0.1f }, { 0.55f, 3.0f, 0.1f });
		panel(dark, { -0.05f, 1.1f, -0.06f }, { 0.05f, 2.1f, 0.06f });
		piece_builder.upload(meshes[structures::piece_window]);

		piece_builder.clear();
		panel(wood, { -1.5f, -0.15f, -1.5f }, { 1.5f, 0.0f, 1.5f });
		panel(dark, { -1.5f, -0.3f, -0.1f }, { 1.5f, -0.15f, 0.1f });
		piece_builder.upload(meshes[structures::piece_floor]);

		piece_builder.clear();

		for (auto step{ 0u }; step < 12u; step++)
		{
			panel(step % 2u ? wood : dark, { -1.2f, 0.0f, -1.5f + static_cast<std::float_t>(step) * 0.25f }, { 1.2f, static_cast<std::float_t>(step + 1u) * 0.25f, -1.5f + static_cast<std::float_t>(step + 1u) * 0.25f });
		}

		piece_builder.upload(meshes[structures::piece_stairs]);

		build_roof(dark);

		piece_builder.clear();
		panel(dark, { 0.0f, 0.0f, -0.035f }, { 1.08f, 2.18f, 0.035f });
		panel(wood, { 0.05f, 0.35f, -0.05f }, { 1.03f, 0.5f, 0.05f });
		panel(wood, { 0.05f, 1.68f, -0.05f }, { 1.03f, 1.83f, 0.05f });
		panel(structures::material_metal_rust, { 0.9f, 1.02f, -0.08f }, { 0.98f, 1.12f, 0.08f });
		piece_builder.upload(meshes[structures::piece_door]);

		piece_builder.clear();
		panel(structures::material_paint_gunmetal, { 0.86f, 1.18f, -0.078f }, { 0.98f, 1.36f, -0.036f });
		panel(structures::material_paint_gunmetal, { 0.86f, 1.18f, 0.036f }, { 0.98f, 1.36f, 0.078f });
		panel(structures::material_light_warm, { 0.9f, 1.315f, -0.081f }, { 0.94f, 1.335f, 0.081f });
		piece_builder.upload(keypad_mesh);

		piece_builder.clear();

		if (rock)
		{
			const auto extent{ rock->bounds_max - rock->bounds_min };
			const auto middle{ (rock->bounds_min + rock->bounds_max) * 0.5f };

			for (auto stone{ 0u }; stone < 9u; stone++)
			{
				const auto angle{ static_cast<std::float_t>(stone) / 9.0f * two_pi };
				const auto size{ 0.16f + random() * 0.07f };

				for (const auto& part : rock->parts)
				{
					piece_builder.append(*rock, part.first_index, part.index_count, mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-middle), mathematics.scaling({ size / extent.x, size * 0.8f / extent.y, size / extent.z })), mathematics.rotation_y(angle * 2.3f)), mathematics.translation({ std::sin(angle) * 0.46f, size * 0.25f, std::cos(angle) * 0.46f })));
				}
			}
		}

		for (auto log{ 0u }; log < 4u; log++)
		{
			const auto angle{ static_cast<std::float_t>(log) * half_pi + 0.4f };
			const auto first_vertex{ static_cast<std::uint32_t>(piece_builder.vertices.size()) };
			const auto first_index{ static_cast<std::uint32_t>(piece_builder.indices.size()) };
			const structures::vec3_s base{ std::sin(angle) * 0.34f, 0.02f, std::cos(angle) * 0.34f };

			piece_builder.set_material(dark);
			piece_builder.cylinder(base, mathematics.normalize(structures::vec3_s{ -base.x, 0.62f, -base.z }), 0.045f, 0.62f, 8u, true);
			piece_builder.compute_tangents(first_vertex, first_index);
		}

		panel(structures::material_asphalt, { -0.28f, 0.0f, -0.28f }, { 0.28f, 0.05f, 0.28f });
		piece_builder.upload(meshes[structures::piece_campfire]);

		piece_builder.clear();
		panel(structures::material_fabric_olive, { -0.42f, 0.0f, -1.0f }, { 0.42f, 0.12f, 1.0f });
		panel(structures::material_fabric_dark, { -0.42f, 0.121f, -0.35f }, { 0.42f, 0.14f, 1.0f });
		panel(structures::material_burlap, { -0.3f, 0.05f, -0.98f }, { 0.3f, 0.2f, -0.66f });
		piece_builder.upload(meshes[structures::piece_sleeping_bag]);

		piece_builder.clear();
		panel(wood, { -0.45f, 0.0f, -0.28f }, { 0.45f, 0.5f, 0.28f });
		panel(dark, { -0.47f, 0.5f, -0.3f }, { 0.47f, 0.58f, 0.3f });
		panel(structures::material_metal_rust, { -0.06f, 0.36f, -0.31f }, { 0.06f, 0.5f, -0.28f });
		piece_builder.upload(meshes[structures::piece_storage_box]);

		const auto masonry{ models.variant(structures::material_concrete_rough, { 0.5f, 0.47f, 0.44f }, 0.0f) };

		piece_builder.clear();
		panel(masonry, { -0.52f, 0.0f, -0.52f }, { 0.52f, 1.05f, 0.52f });
		panel(structures::material_asphalt, { -0.24f, 0.14f, -0.56f }, { 0.24f, 0.52f, -0.5f });
		panel(masonry, { -0.36f, 1.05f, -0.36f }, { 0.36f, 1.25f, 0.36f });
		panel(structures::material_metal_rust, { -0.12f, 1.25f, -0.12f }, { 0.12f, 1.7f, 0.12f });

		if (rock)
		{
			const auto extent{ rock->bounds_max - rock->bounds_min };
			const auto middle{ (rock->bounds_min + rock->bounds_max) * 0.5f };

			for (auto stone{ 0u }; stone < 20u; stone++)
			{
				const auto side{ stone % 4u };
				const auto height{ 0.12f + static_cast<std::float_t>(stone / 4u) * 0.2f };
				const auto along{ random() * 0.8f - 0.4f };
				const structures::vec3_s spot{ side == 0u ? along : (side == 1u ? 0.53f : (side == 2u ? -along : -0.53f)), height, side == 0u ? 0.53f : (side == 1u ? along : (side == 2u ? -0.53f : -along)) };

				if (side != 2u || std::fabs(along) > 0.3f || height > 0.6f)
				{
					for (const auto& part : rock->parts)
					{
						piece_builder.append(*rock, part.first_index, part.index_count, mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-middle), mathematics.scaling({ 0.26f / extent.x, 0.16f / extent.y, 0.22f / extent.z })), mathematics.rotation_y(random() * two_pi)), mathematics.translation(spot)));
					}
				}
			}
		}

		piece_builder.upload(meshes[structures::piece_furnace]);

		piece_builder.clear();

		if (rock)
		{
			const auto extent{ rock->bounds_max - rock->bounds_min };
			const auto middle{ (rock->bounds_min + rock->bounds_max) * 0.5f };

			for (auto course{ 0u }; course < 3u; course++)
			{
				for (auto stone{ 0u }; stone < 11u; stone++)
				{
					const auto angle{ (static_cast<std::float_t>(stone) + static_cast<std::float_t>(course) * 0.5f) / 11.0f * two_pi };

					for (const auto& part : rock->parts)
					{
						piece_builder.append(*rock, part.first_index, part.index_count, mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-middle), mathematics.scaling({ 0.34f / extent.x, 0.24f / extent.y, 0.26f / extent.z })), mathematics.rotation_y(-angle + half_pi + random() * 0.3f)), mathematics.translation({ std::sin(angle) * 0.72f, 0.1f + static_cast<std::float_t>(course) * 0.2f, std::cos(angle) * 0.72f })));
					}
				}
			}
		}

		panel(structures::material_asphalt, { -0.58f, 0.0f, -0.58f }, { 0.58f, 0.62f, 0.58f });

		for (auto post{ 0u }; post < 2u; post++)
		{
			const auto first_vertex{ static_cast<std::uint32_t>(piece_builder.vertices.size()) };
			const auto first_index{ static_cast<std::uint32_t>(piece_builder.indices.size()) };

			piece_builder.set_material(dark);
			piece_builder.cylinder({ post ? 0.82f : -0.82f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f }, 0.06f, 1.75f, 8u, true);
			piece_builder.compute_tangents(first_vertex, first_index);
		}

		const auto beam_vertex{ static_cast<std::uint32_t>(piece_builder.vertices.size()) };
		const auto beam_index{ static_cast<std::uint32_t>(piece_builder.indices.size()) };

		piece_builder.set_material(wood);
		piece_builder.cylinder({ -0.92f, 1.62f, 0.0f }, { 1.0f, 0.0f, 0.0f }, 0.07f, 1.84f, 10u, true);
		piece_builder.cylinder({ 0.0f, 0.98f, 0.0f }, { 0.0f, 1.0f, 0.0f }, 0.012f, 0.62f, 6u, false);
		piece_builder.set_material(structures::material_metal_rust);
		piece_builder.cylinder({ 0.0f, 0.78f, 0.0f }, { 0.0f, 1.0f, 0.0f }, 0.12f, 0.22f, 12u, true);
		piece_builder.compute_tangents(beam_vertex, beam_index);
		piece_builder.upload(meshes[structures::piece_well]);

		build_benches(dark);

		build_twigs();

		load_kit();
	}
	/*
	//=====================================================================================
	*/
	void building_c::build_roof(std::uint32_t dark)
	{
		const auto pitch{ std::atan2(roof_rise, 1.5f) };
		const auto span{ std::sqrt(1.5f * 1.5f + roof_rise * roof_rise) + 0.2f };
		const structures::vec2_s gable[3] = { { -1.5f, 0.0f }, { 1.5f, 0.0f }, { 0.0f, roof_rise } };

		piece_builder.clear();

		for (auto side{ 0u }; side < 2u; side++)
		{
			const auto sign{ side ? 1.0f : -1.0f };
			const auto first_vertex{ static_cast<std::uint32_t>(piece_builder.vertices.size()) };
			const auto first_index{ static_cast<std::uint32_t>(piece_builder.indices.size()) };

			piece_builder.set_material(wood);
			piece_builder.box({ 0.0f, roof_rise * 0.5f + 0.06f, sign * 0.75f }, { 3.1f, 0.1f, span }, mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, sign * pitch));
			piece_builder.set_material(dark);
			piece_builder.prism(gable, 3u, 0.1f, mathematics.multiply(mathematics.rotation_y(half_pi), mathematics.translation({ sign * 1.45f, 0.0f, 0.0f })));
			piece_builder.compute_tangents(first_vertex, first_index);
		}

		panel(dark, { -1.58f, roof_rise - 0.02f, -0.09f }, { 1.58f, roof_rise + 0.14f, 0.09f });
		piece_builder.upload(meshes[structures::piece_roof]);
	}
	/*
	//=====================================================================================
	*/
	void building_c::stick(structures::vec3_s from, structures::vec3_s to, std::float_t radius)
	{
		const auto first_vertex{ static_cast<std::uint32_t>(piece_builder.vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(piece_builder.indices.size()) };
		const auto length{ mathematics.distance(from, to) };

		piece_builder.set_material(bark);
		piece_builder.cylinder(from, (to - from) * (1.0f / std::max(length, 0.001f)), radius * (0.85f + random() * 0.3f), length, 6u, true);
		piece_builder.compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void building_c::lattice(std::float_t left, std::float_t right, std::float_t bottom, std::float_t top, std::float_t spacing)
	{
		for (auto direction{ 0u }; direction < 2u; direction++)
		{
			const auto slope{ direction ? -1.0f : 1.0f };
			const auto depth{ direction ? 0.035f : -0.035f };
			const auto last{ direction ? top + right : top - left };

			for (auto offset{ (direction ? bottom + left : bottom - right) + spacing * 0.5f }; offset < last; offset += spacing)
			{
				const auto start{ direction ? std::max(left, offset - top) : std::max(left, bottom - offset) };
				const auto end{ direction ? std::min(right, offset - bottom) : std::min(right, top - offset) };

				if (end - start > 0.05f)
				{
					stick({ start, offset + slope * start, depth }, { end, offset + slope * end, depth }, 0.022f);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void building_c::build_twigs()
	{
		auto& twig{ tier_meshes[0] };

		piece_builder.clear();

		const structures::vec3_s posts[4] = { { -1.38f, 0.0f, -1.38f }, { 1.38f, 0.0f, -1.38f }, { 1.38f, 0.0f, 1.38f }, { -1.38f, 0.0f, 1.38f } };

		for (auto corner{ 0u }; corner < 4u; corner++)
		{
			const auto& post{ posts[corner] };
			const auto& next{ posts[(corner + 1u) % 4u] };
			const auto outward{ mathematics.normalize(post + next) * 0.07f };
			const auto along{ mathematics.normalize(next - post) * 0.12f };

			stick(post + structures::vec3_s{ 0.0f, -1.6f, 0.0f }, post, 0.075f);
			stick(post + outward - along + structures::vec3_s{ 0.0f, -0.1f, 0.0f }, next + outward + along + structures::vec3_s{ 0.0f, -0.1f, 0.0f }, 0.06f);
			stick(post + outward + structures::vec3_s{ 0.0f, -1.45f, 0.0f }, next + outward + structures::vec3_s{ 0.0f, -0.22f, 0.0f }, 0.035f);
			stick(next + outward + structures::vec3_s{ 0.0f, -1.45f, 0.0f }, post + outward + structures::vec3_s{ 0.0f, -0.22f, 0.0f }, 0.035f);
		}

		for (auto slat{ 0u }; slat < 24u; slat++)
		{
			const auto z{ -1.44f + static_cast<std::float_t>(slat) * 0.125f };

			stick({ -1.5f, -0.035f, z + (random() - 0.5f) * 0.02f }, { 1.5f, -0.035f, z + (random() - 0.5f) * 0.02f }, 0.035f);
		}

		piece_builder.upload(twig[structures::piece_foundation]);

		for (auto piece{ static_cast<std::uint32_t>(structures::piece_wall) }; piece <= structures::piece_window; piece++)
		{
			const auto opening{ piece != structures::piece_wall };
			const auto sill{ piece == structures::piece_window ? 1.1f : 0.0f };
			const auto lintel{ piece == structures::piece_window ? 2.1f : 2.2f };

			piece_builder.clear();

			stick({ -1.45f, 0.0f, 0.0f }, { -1.45f, 3.0f, 0.0f }, 0.065f);
			stick({ 1.45f, 0.0f, 0.0f }, { 1.45f, 3.0f, 0.0f }, 0.065f);
			stick({ -1.5f, 0.12f, 0.0f }, { 1.5f, 0.12f, 0.0f }, 0.05f);
			stick({ -1.5f, 2.9f, 0.0f }, { 1.5f, 2.9f, 0.0f }, 0.05f);

			if (opening)
			{
				stick({ -0.6f, 0.0f, 0.0f }, { -0.6f, 3.0f, 0.0f }, 0.055f);
				stick({ 0.6f, 0.0f, 0.0f }, { 0.6f, 3.0f, 0.0f }, 0.055f);
				stick({ -0.65f, lintel, 0.0f }, { 0.65f, lintel, 0.0f }, 0.05f);

				lattice(-1.4f, -0.64f, 0.15f, 2.87f, 0.3f);
				lattice(0.64f, 1.4f, 0.15f, 2.87f, 0.3f);
				lattice(-0.56f, 0.56f, lintel + 0.04f, 2.87f, 0.3f);

				if (sill > 0.0f)
				{
					stick({ -0.65f, sill, 0.0f }, { 0.65f, sill, 0.0f }, 0.05f);

					lattice(-0.56f, 0.56f, 0.15f, sill - 0.04f, 0.3f);
				}
			}

			else
			{
				stick({ -1.5f, 1.5f, 0.0f }, { 1.5f, 1.5f, 0.0f }, 0.04f);

				lattice(-1.4f, 1.4f, 0.15f, 2.87f, 0.3f);
			}

			piece_builder.upload(twig[piece]);
		}

		piece_builder.clear();

		for (auto slat{ 0u }; slat < 24u; slat++)
		{
			const auto x{ -1.44f + static_cast<std::float_t>(slat) * 0.125f };

			stick({ x + (random() - 0.5f) * 0.02f, -0.04f, -1.5f }, { x + (random() - 0.5f) * 0.02f, -0.04f, 1.5f }, 0.035f);
		}

		for (auto beam{ 0u }; beam < 3u; beam++)
		{
			const auto z{ -1.2f + static_cast<std::float_t>(beam) * 1.2f };

			stick({ -1.5f, -0.13f, z }, { 1.5f, -0.13f, z }, 0.06f);
		}

		piece_builder.upload(twig[structures::piece_floor]);

		piece_builder.clear();

		for (auto step{ 0u }; step < 12u; step++)
		{
			const auto height{ static_cast<std::float_t>(step + 1u) * 0.25f - 0.04f };
			const auto depth{ -1.5f + static_cast<std::float_t>(step) * 0.25f };

			stick({ -1.2f, height, depth + 0.07f }, { 1.2f, height, depth + 0.07f }, 0.04f);
			stick({ -1.2f, height, depth + 0.18f }, { 1.2f, height, depth + 0.18f }, 0.04f);
		}

		stick({ -1.15f, 0.0f, -1.5f }, { -1.15f, 3.0f, 1.5f }, 0.065f);
		stick({ 1.15f, 0.0f, -1.5f }, { 1.15f, 3.0f, 1.5f }, 0.065f);
		stick({ -1.15f, 0.0f, 1.45f }, { -1.15f, 3.0f, 1.45f }, 0.06f);
		stick({ 1.15f, 0.0f, 1.45f }, { 1.15f, 3.0f, 1.45f }, 0.06f);
		piece_builder.upload(twig[structures::piece_stairs]);

		piece_builder.clear();

		for (auto side{ 0u }; side < 2u; side++)
		{
			const auto sign{ side ? 1.0f : -1.0f };

			for (auto rafter{ 0u }; rafter < 5u; rafter++)
			{
				const auto x{ -1.4f + static_cast<std::float_t>(rafter) * 0.7f };

				stick({ x, 0.02f, sign * 1.58f }, { x, roof_rise, 0.0f }, 0.05f);
			}

			for (auto purlin{ 0u }; purlin < 8u; purlin++)
			{
				const auto along{ (static_cast<std::float_t>(purlin) + 0.5f) / 8.0f };

				stick({ -1.52f, 0.08f + along * (roof_rise - 0.05f), sign * 1.55f * (1.0f - along) }, { 1.52f, 0.08f + along * (roof_rise - 0.05f), sign * 1.55f * (1.0f - along) }, 0.035f);
			}
		}

		stick({ -1.58f, roof_rise + 0.03f, 0.0f }, { 1.58f, roof_rise + 0.03f, 0.0f }, 0.06f);
		piece_builder.upload(twig[structures::piece_roof]);
	}
	/*
	//=====================================================================================
	*/
	void building_c::build_benches(std::uint32_t dark)
	{
		for (auto tier{ 0u }; tier < 3u; tier++)
		{
			const auto top_material{ tier ? static_cast<std::uint32_t>(structures::material_metal_rust) : wood };

			piece_builder.clear();
			panel(top_material, { -0.8f, 0.84f, -0.4f }, { 0.8f, 0.92f, 0.4f });
			panel(dark, { -0.72f, 0.22f, -0.34f }, { 0.72f, 0.26f, 0.34f });

			for (auto leg{ 0u }; leg < 4u; leg++)
			{
				const structures::vec3_s corner{ leg & 1u ? 0.72f : -0.72f, 0.0f, leg & 2u ? 0.32f : -0.32f };

				panel(dark, corner - structures::vec3_s{ 0.05f, 0.0f, 0.05f }, corner + structures::vec3_s{ 0.05f, 0.84f, 0.05f });
			}

			if (tier > 0u)
			{
				panel(structures::material_metal_rust, { 0.55f, 0.92f, -0.36f }, { 0.75f, 1.08f, -0.2f });
			}

			if (tier > 1u)
			{
				panel(structures::material_metal_rust, { -0.7f, 0.92f, 0.12f }, { -0.5f, 1.7f, 0.32f });
				panel(structures::material_metal_rust, { -0.72f, 1.5f, -0.2f }, { -0.48f, 1.62f, 0.32f });
			}

			piece_builder.upload(meshes[structures::piece_workbench_1 + tier]);
		}

		piece_builder.clear();
		panel(wood, { -0.6f, 0.72f, -0.38f }, { 0.6f, 0.78f, 0.38f });
		panel(dark, { -0.58f, 0.0f, -0.36f }, { -0.46f, 0.72f, 0.36f });
		panel(dark, { 0.46f, 0.0f, -0.36f }, { 0.58f, 0.72f, 0.36f });
		panel(structures::material_burlap, { -0.3f, 0.78f, -0.2f }, { 0.1f, 0.79f, 0.12f });
		panel(structures::material_metal_rust, { 0.35f, 0.78f, 0.1f }, { 0.42f, 1.2f, 0.17f });
		piece_builder.upload(meshes[structures::piece_research_table]);

		piece_builder.clear();
		panel(dark, { -0.45f, 0.0f, -0.25f }, { 0.45f, 1.9f, 0.25f });
		panel(wood, { -0.41f, 0.08f, -0.27f }, { -0.02f, 1.82f, -0.25f });
		panel(wood, { 0.02f, 0.08f, -0.27f }, { 0.41f, 1.82f, -0.25f });
		panel(dark, { -0.47f, 1.9f, -0.27f }, { 0.47f, 1.96f, 0.27f });
		panel(structures::material_metal_rust, { -0.07f, 0.9f, -0.3f }, { -0.03f, 1.1f, -0.27f });
		panel(structures::material_metal_rust, { 0.03f, 0.9f, -0.3f }, { 0.07f, 1.1f, -0.27f });
		panel(structures::material_metal_rust, { -0.44f, 1.2f, -0.28f }, { 0.44f, 1.24f, -0.26f });
		piece_builder.upload(meshes[structures::piece_cupboard]);
	}
	/*
	//=====================================================================================
	*/
	void building_c::load_kit()
	{
		if (const auto deployables{ models.find(deployable_kit) }; deployables)
		{
			for (auto piece{ 0u }; piece < structures::piece_count; piece++)
			{
				if (const auto part{ deployable_parts[piece] ? models.part(*deployables, deployable_parts[piece]) : nullptr }; part)
				{
					piece_builder.clear();
					piece_builder.append(*deployables, part->first_index, part->index_count, mathematics.identity());
					piece_builder.upload(meshes[piece]);
				}
			}
		}

		if (const auto structures_model{ models.find(structure_kit) }; structures_model)
		{
			for (auto tier{ 0u }; tier < building_tier_count; tier++)
			{
				for (auto piece{ 0u }; piece < structures::piece_door; piece++)
				{
					if (const auto part{ models.part(*structures_model, structure_parts[tier][piece]) }; part)
					{
						functions::release(tier_meshes[tier][piece].vertex_buffer);
						functions::release(tier_meshes[tier][piece].index_buffer);

						piece_builder.clear();
						piece_builder.append(*structures_model, part->first_index, part->index_count, mathematics.identity());
						piece_builder.upload(tier_meshes[tier][piece]);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void building_c::migrate(structures::structure_s& structure)
	{
		structure.piece += structure.piece >= structures::piece_roof ? 1u : 0u;
		structure.tier += structure.piece < structures::piece_door ? 1u : 0u;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t building_c::workbench_tier(structures::vec3_s position)
	{
		auto tier{ 0u };

		for (const auto& structure : placed)
		{
			if (structure.destroyed == false && structure.piece >= structures::piece_workbench_1 && structure.piece <= structures::piece_workbench_3 && mathematics.distance(structure.position, position) < workbench_range)
			{
				tier = std::max(tier, structure.piece - structures::piece_workbench_1 + 1u);
			}
		}

		return tier;
	}
	/*
	//=====================================================================================
	*/
	std::float_t building_c::warmth(structures::vec3_s position)
	{
		auto result{ 0.0f };

		for (const auto& container : containers)
		{
			if (container.burning && container.kind != structures::container_storage && container.structure < placed.size() && placed[container.structure].destroyed == false)
			{
				const auto distance{ mathematics.distance(placed[container.structure].position, position) };
				const auto strength{ container.kind == structures::container_campfire ? climate_campfire : climate_furnace };

				result = std::max(result, strength * std::max(0.0f, 1.0f - distance / climate_fire_range));
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::research_nearby(structures::vec3_s position)
	{
		return std::any_of(placed.begin(), placed.end(), [&](const structures::structure_s& structure) { return structure.destroyed == false && structure.piece == structures::piece_research_table && mathematics.distance(structure.position, position) < workbench_range; });
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t building_c::active_piece()
	{
		const auto item{ survival.held().item };

		for (auto piece{ static_cast<std::uint32_t>(structures::piece_door) }; piece < structures::piece_count; piece++)
		{
			if (piece_definitions[piece].item == item)
			{
				return piece;
			}
		}

		return item == structures::item_building_plan ? selected : static_cast<std::uint32_t>(structures::piece_count);
	}
	/*
	//=====================================================================================
	*/
	void building_c::update(std::float_t delta, bool input_enabled)
	{
		const auto origin{ player.eye };
		const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };
		const auto piece{ active_piece() };

		char text[128]{};

		clock += delta;

		preview.active = false;

		for (auto& structure : placed)
		{
			if (structure.piece == structures::piece_door)
			{
				structure.swing = mathematics.approach(structure.swing, structure.open ? 1.0f : 0.0f, delta * 3.0f);
			}
		}

		if (ready && input_enabled && survival.vitals.dead == false)
		{
			if (piece < structures::piece_count)
			{
				plan(piece);

				if (platform.tapped(structures::bind_rotate))
				{
					selected = survival.held().item == structures::item_building_plan ? (selected + 1u) % structures::piece_door : selected;
					turn += survival.held().item == structures::item_building_plan ? 0.0f : half_pi;
				}

				if (piece_definitions[piece].item == structures::item_building_plan)
				{
					std::snprintf(text, sizeof(text), "%s  (%u %s)   [LMB] build   [R] next", piece_definitions[piece].name, piece_definitions[piece].cost.amount, item_definitions[piece_definitions[piece].cost.item].name);
				}

				else
				{
					std::snprintf(text, sizeof(text), "Place %s   [LMB]   [R] rotate", piece_definitions[piece].name);
				}

				hud.set_prompt(preview.active ? text : "Nothing to build on here");

				if (platform.input.pressed[VK_LBUTTON] && preview.active && client.connected())
				{
					client.build(preview);
				}

				else if (platform.input.pressed[VK_LBUTTON] && preview.active && place(preview) == false)
				{
					mixer.play_2d(structures::sound_ui_error, 0.4f, 1.0f);
				}
			}

			else if (const auto piece_index{ survival.held().item == structures::item_hammer ? structure_target(origin, forward, 3.2f) : -1 }; piece_index >= 0 && placed[piece_index].piece < structures::piece_door)
			{
				const auto& target{ placed[piece_index] };
				const auto next{ target.tier + 1u };

				if (next < building_tier_count)
				{
					std::snprintf(text, sizeof(text), "%s (%s, %.0f / %.0f)   [RMB] upgrade to %s: %u %s   [LMB] repair", piece_definitions[target.piece].name, building_tiers[target.tier].name, target.health, durability(static_cast<std::uint32_t>(piece_index)), building_tiers[next].name, building_tiers[next].cost, item_definitions[building_tiers[next].item].name);
				}

				else
				{
					std::snprintf(text, sizeof(text), "%s (%s, %.0f / %.0f)   [LMB] repair", piece_definitions[target.piece].name, building_tiers[target.tier].name, target.health, durability(static_cast<std::uint32_t>(piece_index)));
				}

				hud.set_prompt(text);

				if (platform.input.pressed[VK_RBUTTON] && next < building_tier_count)
				{
					if (client.connected())
					{
						client.request(structures::request_upgrade, static_cast<std::uint16_t>(piece_index), 0u);
					}

					else if (survival.take(building_tiers[next].item, building_tiers[next].cost))
					{
						upgrade(static_cast<std::uint32_t>(piece_index));
					}

					mixer.play(building_tiers[next].sound, target.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f }, 0.8f, 0.8f);
				}
			}

			else if (const auto fitting{ survival.held().item == structures::item_code_lock ? door_target(origin, forward) : -1 }; fitting >= 0)
			{
				const auto door{ static_cast<std::uint32_t>(fitting) };

				hud.set_prompt(locks.count(door) ? "This door already has a lock" : "Fit the code lock   [LMB]");

				if (platform.input.pressed[VK_LBUTTON] && locks.count(door) == 0u && client.connected())
				{
					client.request(structures::request_lock, static_cast<std::uint16_t>(door), 0u);
				}

				else if (platform.input.pressed[VK_LBUTTON] && attach_lock(door, 0u))
				{
					survival.take(structures::item_code_lock, 1u);

					hud.open_keypad(fitting, true);
				}
			}

			else if (const auto cupboard{ cupboard_target(origin, forward) }; cupboard >= 0)
			{
				hud.set_prompt("Tool cupboard   [E] authorize yourself");

				if (platform.tapped(structures::bind_use) && client.connected())
				{
					client.request(structures::request_authorize, static_cast<std::uint16_t>(cupboard), 0u);
				}

				else if (platform.tapped(structures::bind_use))
				{
					authorize(static_cast<std::uint32_t>(cupboard), 0u);

					survival.post("You are authorized on this cupboard", 0);
				}
			}

			else if (const auto door{ door_target(origin, forward) }; door >= 0)
			{
				const auto locked{ locks.count(static_cast<std::uint32_t>(door)) != 0u };
				const auto rekey{ locked && platform.held(structures::bind_sprint) };

				hud.set_prompt(locked ? (placed[door].open ? "Close door   [E]   hold sprint to change the code" : "Locked door   [E] open or enter the code") : (placed[door].open ? "Close door   [E]" : "Open door   [E]"));

				if (platform.tapped(structures::bind_use) && client.connected())
				{
					client.request(rekey ? structures::request_rekey : structures::request_door, static_cast<std::uint16_t>(door), 0u);
				}

				else if (platform.tapped(structures::bind_use) && rekey && accessible(static_cast<std::uint32_t>(door), 0u))
				{
					hud.open_keypad(door, true);
				}

				else if (platform.tapped(structures::bind_use))
				{
					toggle_door(static_cast<std::uint32_t>(door));
				}
			}

			else if (const auto box{ container_target(origin, forward) }; box >= 0)
			{
				std::snprintf(text, sizeof(text), "Open %s   [E]", piece_definitions[placed[containers[box].structure].piece].name);

				hud.set_prompt(text);

				if (platform.tapped(structures::bind_use))
				{
					survival.open_container = box;
					survival.inventory_open = true;

					platform.set_mouse_captured(false);

					mixer.play(structures::sound_container, placed[containers[box].structure].position, 0.8f, 1.0f);

					if (client.connected())
					{
						client.request(structures::request_open, static_cast<std::uint16_t>(box), 0u);
					}
				}
			}
		}

		if (survival.open_container >= 0 && (survival.inventory_open == false || mathematics.distance(placed[containers[survival.open_container].structure].position, player.state.position) > 4.0f))
		{
			survival.open_container = -1;

			if (client.connected())
			{
				client.request(structures::request_close, 0u, 0u);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t building_c::container_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		auto best{ -1 };
		auto best_away{ 0.8f };

		for (auto index{ 0u }; index < containers.size(); index++)
		{
			if (const auto& structure{ placed[containers[index].structure] }; structure.destroyed == false)
			{
				const auto middle{ structure.position + structures::vec3_s{ 0.0f, containers[index].kind == structures::container_furnace ? 0.6f : (containers[index].kind == structures::container_campfire ? 0.15f : 0.3f), 0.0f } };
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
	void building_c::smelt(std::float_t delta)
	{
		for (auto index{ 0u }; index < containers.size(); index++)
		{
			auto& container{ containers[index] };

			if (container.kind != structures::container_storage && container.burning)
			{
				const auto cooking{ container.kind == structures::container_campfire };
				const auto fuel_time{ cooking ? campfire_fuel_time : furnace_fuel_time };
				const auto work_time{ cooking ? campfire_cook_time : furnace_smelt_time };

				auto& fuel{ container.slots[furnace_fuel_slot] };

				if (fuel.item != structures::item_wood || fuel.amount == 0u)
				{
					container.burning = false;

					stirred.push_back(index);
				}

				else
				{
					container.fuel_timer += delta;
					container.smelt_timer += delta;

					if (container.fuel_timer >= fuel_time)
					{
						container.fuel_timer -= fuel_time;

						fuel.amount--;

						if (fuel.amount == 0u)
						{
							fuel = {};
						}

						deposit(container, structures::item_charcoal);

						stirred.push_back(index);
					}

					if (container.smelt_timer >= work_time)
					{
						container.smelt_timer -= work_time;

						stirred.push_back(index);

						for (auto input{ furnace_first_input }; input <= furnace_last_input; input++)
						{
							auto& source{ container.slots[input] };

							auto result{ static_cast<std::uint32_t>(structures::item_none) };

							for (const auto& conversion : cooking ? std::span<const structures::conversion_s>{ cook_conversions } : std::span<const structures::conversion_s>{ smelt_conversions })
							{
								result = conversion.input == source.item ? conversion.output : result;
							}

							if (result != structures::item_none && deposit(container, result))
							{
								source.amount--;

								if (source.amount == 0u)
								{
									source = {};
								}

								input = furnace_last_input;
							}
						}
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool building_c::deposit(structures::container_s& container, std::uint32_t item)
	{
		for (auto pass{ 0u }; pass < 2u; pass++)
		{
			for (auto output{ furnace_first_output }; output < container_slots; output++)
			{
				if (auto& slot{ container.slots[output] }; (pass == 0u && slot.item == item && slot.amount < item_definitions[item].stack) || (pass == 1u && slot.item == structures::item_none))
				{
					slot = { item, slot.amount + 1u, 1.0f };

					return true;
				}
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void building_c::plan(std::uint32_t piece)
	{
		const auto origin{ player.eye };
		const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };

		structures::placement_s candidate{};

		candidate.piece = piece;
		candidate.anchor = -1;

		auto found{ false };

		if (piece == structures::piece_foundation)
		{
			found = snap_foundation(origin, forward, candidate);
		}

		else if (piece == structures::piece_wall || piece == structures::piece_doorway || piece == structures::piece_window)
		{
			found = snap_edge(origin, forward, candidate);
		}

		else if (piece == structures::piece_floor || piece == structures::piece_stairs || piece == structures::piece_roof)
		{
			found = snap_cell(origin, forward, candidate);
		}

		else if (piece == structures::piece_door)
		{
			found = snap_door(origin, forward, candidate);
		}

		else
		{
			found = snap_ground(origin, forward, candidate);
		}

		if (found)
		{
			candidate.piece = piece;
			candidate.active = true;
			candidate.valid = candidate.valid && affordable(piece) && occupied(candidate.position, piece) == false;

			preview = candidate;
		}
	}
	/*
	//=====================================================================================
	*/
	bool building_c::snap_foundation(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out)
	{
		const auto hit{ world.trace(origin, origin + forward * building_range, { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };
		const auto aim{ hit.hit ? hit.end : origin + forward * building_range };

		auto best{ 2.1f };

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (const auto& foundation{ placed[index] }; foundation.piece == structures::piece_foundation && foundation.destroyed == false)
			{
				for (auto side{ 0u }; side < 4u; side++)
				{
					const auto candidate{ foundation.position + maps.rotate_yaw(side % 2u ? structures::vec3_s{ side == 1u ? building_cell : -building_cell, 0.0f, 0.0f } : structures::vec3_s{ 0.0f, 0.0f, side == 0u ? -building_cell : building_cell }, foundation.yaw) };
					const auto distance{ mathematics.length(structures::vec3_s{ aim.x - candidate.x, 0.0f, aim.z - candidate.z }) };

					if (distance < best && occupied(candidate, structures::piece_foundation) == false)
					{
						best = distance;

						out.position = candidate;
						out.yaw = foundation.yaw;
						out.anchor = static_cast<std::int32_t>(index);
						out.valid = true;
					}
				}
			}
		}

		if (out.anchor < 0 && hit.hit && hit.normal.y > 0.6f && terrain.enabled)
		{
			auto highest{ terrain.height(hit.end.x, hit.end.z) };
			auto lowest{ highest };

			for (auto corner{ 0u }; corner < 4u; corner++)
			{
				const auto point{ hit.end + maps.rotate_yaw({ corner & 1u ? 1.5f : -1.5f, 0.0f, corner & 2u ? 1.5f : -1.5f }, player.yaw) };
				const auto height{ terrain.height(point.x, point.z) };

				highest = std::max(highest, height);
				lowest = std::min(lowest, height);
			}

			out.position = { hit.end.x, highest + 0.15f, hit.end.z };
			out.yaw = player.yaw;
			out.valid = highest - lowest < 1.35f && world.box_solid(out.position + structures::vec3_s{ 0.0f, 0.9f, 0.0f }, { 1.45f, 0.8f, 1.45f }, structures::contents_solid) == false;

			return true;
		}

		return out.anchor >= 0;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::snap_edge(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out)
	{
		auto best{ 2.2f };

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (const auto& base{ placed[index] }; (base.piece == structures::piece_foundation || base.piece == structures::piece_floor) && base.destroyed == false)
			{
				for (auto side{ 0u }; side < 4u; side++)
				{
					const auto edge{ base.position + maps.rotate_yaw(side % 2u ? structures::vec3_s{ side == 1u ? 1.5f : -1.5f, 0.0f, 0.0f } : structures::vec3_s{ 0.0f, 0.0f, side == 0u ? -1.5f : 1.5f }, base.yaw) };
					const auto middle{ edge + structures::vec3_s{ 0.0f, building_height * 0.5f, 0.0f } };
					const auto along{ mathematics.dot(middle - origin, forward) };
					const auto away{ mathematics.length(middle - origin - forward * along) };

					if (along > 0.3f && along < building_range + 1.0f && away < best && occupied(edge, structures::piece_wall) == false)
					{
						best = away;

						out.position = edge;
						out.yaw = base.yaw + static_cast<std::float_t>(side) * half_pi;
						out.anchor = static_cast<std::int32_t>(index);
						out.valid = true;
					}
				}
			}
		}

		return out.anchor >= 0;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::snap_cell(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out)
	{
		const auto stairs{ out.piece == structures::piece_stairs };
		const auto roof{ out.piece == structures::piece_roof };

		auto best{ 2.4f };

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (const auto& base{ placed[index] }; (base.piece == structures::piece_foundation || base.piece == structures::piece_floor) && base.destroyed == false)
			{
				for (auto option{ 0u }; option < (stairs || roof ? 1u : 5u); option++)
				{
					const auto lateral{ option == 0u ? structures::vec3_s{} : maps.rotate_yaw(option % 2u ? structures::vec3_s{ option == 1u ? building_cell : -building_cell, 0.0f, 0.0f } : structures::vec3_s{ 0.0f, 0.0f, option == 2u ? -building_cell : building_cell }, base.yaw) };
					const auto lift{ stairs ? 0.0f : (base.piece == structures::piece_floor && option ? 0.0f : building_height) };
					const auto candidate{ base.position + lateral + structures::vec3_s{ 0.0f, lift, 0.0f } };
					const auto target{ candidate + structures::vec3_s{ 0.0f, stairs ? 1.0f : (roof ? roof_rise * 0.5f : 0.0f), 0.0f } };
					const auto along{ mathematics.dot(target - origin, forward) };
					const auto away{ mathematics.length(target - origin - forward * along) };

					if ((option == 0u || base.piece == structures::piece_floor) && along > 0.3f && along < building_range + 1.5f && away < best && occupied(candidate, out.piece) == false)
					{
						best = away;

						out.position = candidate;
						out.yaw = stairs || roof ? base.yaw + std::round(mathematics.angle_difference(base.yaw, player.yaw) / half_pi) * half_pi : base.yaw;
						out.anchor = static_cast<std::int32_t>(index);
						out.valid = true;
					}
				}
			}
		}

		return out.anchor >= 0;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::snap_door(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out)
	{
		auto best{ 1.6f };

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (const auto& doorway{ placed[index] }; doorway.piece == structures::piece_doorway && doorway.destroyed == false)
			{
				const auto middle{ doorway.position + structures::vec3_s{ 0.0f, 1.1f, 0.0f } };
				const auto along{ mathematics.dot(middle - origin, forward) };
				const auto away{ mathematics.length(middle - origin - forward * along) };

				auto taken{ false };

				for (const auto& other : placed)
				{
					taken = taken || (other.piece == structures::piece_door && other.anchor == static_cast<std::int32_t>(index) && other.destroyed == false);
				}

				if (taken == false && along > 0.3f && along < building_range && away < best)
				{
					best = away;

					out.position = doorway.position;
					out.yaw = doorway.yaw;
					out.anchor = static_cast<std::int32_t>(index);
					out.valid = true;
				}
			}
		}

		return out.anchor >= 0;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::snap_ground(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out)
	{
		const auto hit{ world.trace(origin, origin + forward * (building_range - 1.5f), { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };

		if (hit.hit && hit.normal.y > 0.7f)
		{
			out.position = hit.end;
			out.yaw = player.yaw + pi + turn;
			out.valid = world.box_solid(hit.end + structures::vec3_s{ 0.0f, 0.45f, 0.0f }, { 0.35f, 0.3f, 0.35f }, structures::contents_solid) == false;

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::occupied(structures::vec3_s position, std::uint32_t piece)
	{
		const auto wall_like{ piece == structures::piece_wall || piece == structures::piece_doorway || piece == structures::piece_window };
		const auto cap_like{ piece == structures::piece_floor || piece == structures::piece_roof };

		for (const auto& other : placed)
		{
			const auto other_wall{ other.piece == structures::piece_wall || other.piece == structures::piece_doorway || other.piece == structures::piece_window };
			const auto other_cap{ other.piece == structures::piece_floor || other.piece == structures::piece_roof };
			const auto same_class{ wall_like ? other_wall : (cap_like ? other_cap : other.piece == piece) };

			if (other.destroyed == false && same_class && piece < structures::piece_door && mathematics.distance(other.position, position) < (wall_like ? 0.4f : 1.0f))
			{
				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::affordable(std::uint32_t piece)
	{
		const auto& definition{ piece_definitions[piece] };

		return definition.item != structures::item_building_plan || survival.count(definition.cost.item) >= definition.cost.amount;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::place(const structures::placement_s& placement)
	{
		return place(placement, survival, survival.active_slot, 0u);
	}
	/*
	//=====================================================================================
	*/
	bool building_c::permitted(const structures::placement_s& placement, structures::vec3_s eye)
	{
		auto result{ placement.piece < structures::piece_count && std::isfinite(placement.position.x) && std::isfinite(placement.position.y) && std::isfinite(placement.position.z) && std::isfinite(placement.yaw) && mathematics.distance(placement.position, eye) < building_range + 2.5f && occupied(placement.position, placement.piece) == false };

		if (result && placement.anchor >= 0)
		{
			result = static_cast<std::size_t>(placement.anchor) < placed.size() && placed[placement.anchor].destroyed == false && mathematics.distance(placed[placement.anchor].position, placement.position) < 4.4f;
		}

		else if (result)
		{
			result = placement.piece != structures::piece_door && world.box_solid(placement.position + structures::vec3_s{ 0.0f, 0.9f, 0.0f }, { 0.3f, 0.3f, 0.3f }, structures::contents_solid) == false;
		}

		if (result && placement.piece == structures::piece_door)
		{
			result = placed[placement.anchor].piece == structures::piece_doorway && std::none_of(placed.begin(), placed.end(), [&](const structures::structure_s& other) { return other.piece == structures::piece_door && other.anchor == placement.anchor && other.destroyed == false; });
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::place(const structures::placement_s& placement, survival_c& payer, std::uint32_t slot, std::uint32_t owner)
	{
		if (placement.valid && placed.size() < maximum_structures && placement.piece < structures::piece_count)
		{
			const auto& definition{ piece_definitions[placement.piece] };

			if (definition.item == structures::item_building_plan)
			{
				payer.take(definition.cost.item, definition.cost.amount);
			}

			else
			{
				auto& held{ payer.slots[inventory_slots + std::min(slot, hotbar_slots - 1u)] };

				held.amount--;

				if (held.amount == 0u)
				{
					held = {};
				}
			}

			attach({ placement.position, placement.yaw, definition.health * (placement.piece < structures::piece_door ? building_tiers[0].health : 1.0f), 0.0f, random() * 10.0f, placement.piece, -1, 0u, placement.anchor, -1, owner, 0u, false, false });

			if (placement.piece == structures::piece_cupboard)
			{
				authorize(static_cast<std::uint32_t>(placed.size() - 1u), owner);

				payer.notify("Tool cupboard placed: this land is yours", 0);
			}

			if (placement.piece == structures::piece_sleeping_bag)
			{
				bag = payer.owner < 0 ? static_cast<std::int32_t>(placed.size() - 1u) : bag;

				payer.notify("Respawn point set", 0);
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void building_c::attach(const structures::structure_s& structure)
	{
		placed.push_back(structure);

		const auto index{ static_cast<std::uint32_t>(placed.size() - 1u) };

		auto& added{ placed.back() };

		added.first_brush = -1;
		added.brush_count = 0u;
		added.container = -1;

		add_collision(index);

		if (added.piece == structures::piece_storage_box || added.piece == structures::piece_furnace || added.piece == structures::piece_campfire)
		{
			containers.push_back({ {}, 0.0f, 0.0f, index, added.piece == structures::piece_furnace ? static_cast<std::uint32_t>(structures::container_furnace) : (added.piece == structures::piece_campfire ? static_cast<std::uint32_t>(structures::container_campfire) : static_cast<std::uint32_t>(structures::container_storage)), false });

			added.container = static_cast<std::int32_t>(containers.size() - 1u);
		}

		refresh(index, added.open, added.destroyed);

		dirty.push_back(index);

		if (gpu.device && added.destroyed == false)
		{
			mixer.play(structures::sound_hit_wood, added.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f }, 0.9f, 0.8f + random() * 0.15f);

			particles.impact(structures::surface_wood, added.position + structures::vec3_s{ 0.0f, 0.4f, 0.0f }, { 0.0f, 1.0f, 0.0f });
		}
	}
	/*
	//=====================================================================================
	*/
	void building_c::refresh(std::uint32_t index, bool open, bool destroyed)
	{
		if (index < placed.size())
		{
			auto& structure{ placed[index] };

			structure.open = open;
			structure.destroyed = destroyed;

			for (auto brush{ 0u }; brush < structure.brush_count && structure.first_brush >= 0; brush++)
			{
				world.brushes[structure.first_brush + static_cast<std::int32_t>(brush)].contents = destroyed || (open && structure.piece == structures::piece_door) ? 0u : static_cast<std::uint32_t>(structures::contents_solid);
			}

			if (destroyed)
			{
				locks.erase(index);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void building_c::add_collision(std::uint32_t index)
	{
		const auto piece{ placed[index].piece };

		const auto surface{ building_tiers[std::min(placed[index].tier, building_tier_count - 1u)].surface };

		if (piece == structures::piece_foundation)
		{
			box(index, { 0.0f, -0.8f, 0.0f }, { 3.0f, 1.6f, 3.0f }, surface);
		}

		else if (piece == structures::piece_wall)
		{
			box(index, { 0.0f, 1.5f, 0.0f }, { 3.0f, 3.0f, 0.2f }, surface);
		}

		else if (piece == structures::piece_doorway)
		{
			box(index, { -1.025f, 1.5f, 0.0f }, { 0.95f, 3.0f, 0.2f }, surface);
			box(index, { 1.025f, 1.5f, 0.0f }, { 0.95f, 3.0f, 0.2f }, surface);
			box(index, { 0.0f, 2.6f, 0.0f }, { 1.1f, 0.8f, 0.2f }, surface);
		}

		else if (piece == structures::piece_window)
		{
			box(index, { -1.025f, 1.5f, 0.0f }, { 0.95f, 3.0f, 0.2f }, surface);
			box(index, { 1.025f, 1.5f, 0.0f }, { 0.95f, 3.0f, 0.2f }, surface);
			box(index, { 0.0f, 0.55f, 0.0f }, { 1.1f, 1.1f, 0.2f }, surface);
			box(index, { 0.0f, 2.55f, 0.0f }, { 1.1f, 0.9f, 0.2f }, surface);
		}

		else if (piece == structures::piece_floor)
		{
			box(index, { 0.0f, -0.075f, 0.0f }, { 3.0f, 0.15f, 3.0f }, surface);
		}

		else if (piece == structures::piece_stairs)
		{
			ramp(index, { 0.0f, 1.5f, 0.0f }, { 2.4f, 3.0f, 3.0f }, 0.0f, surface);
		}

		else if (piece == structures::piece_roof)
		{
			ramp(index, { 0.0f, roof_rise * 0.5f, -0.75f }, { 3.0f, roof_rise, 1.5f }, 0.0f, surface);
			ramp(index, { 0.0f, roof_rise * 0.5f, 0.75f }, { 3.0f, roof_rise, 1.5f }, pi, surface);
		}

		else if (piece == structures::piece_door)
		{
			box(index, { 0.0f, 1.09f, 0.0f }, { 1.08f, 2.18f, 0.08f }, structures::surface_wood);
		}

		else if (piece == structures::piece_campfire)
		{
			box(index, { 0.0f, 0.15f, 0.0f }, { 0.9f, 0.3f, 0.9f }, structures::surface_rock);
		}

		else if (piece == structures::piece_storage_box)
		{
			box(index, { 0.0f, 0.29f, 0.0f }, { 0.92f, 0.58f, 0.58f }, structures::surface_wood);
		}

		else if (piece == structures::piece_furnace)
		{
			box(index, { 0.0f, 0.62f, 0.0f }, { 1.1f, 1.24f, 1.1f }, structures::surface_rock);
		}

		else if (piece == structures::piece_well)
		{
			box(index, { 0.0f, 0.36f, 0.0f }, { 1.75f, 0.72f, 1.75f }, structures::surface_rock);
		}

		else if (piece >= structures::piece_workbench_1 && piece <= structures::piece_workbench_3)
		{
			box(index, { 0.0f, 0.46f, 0.0f }, { 1.6f, 0.92f, 0.8f }, piece == structures::piece_workbench_1 ? structures::surface_wood : structures::surface_metal);
		}

		else if (piece == structures::piece_research_table)
		{
			box(index, { 0.0f, 0.39f, 0.0f }, { 1.2f, 0.78f, 0.76f }, structures::surface_wood);
		}

		else if (piece == structures::piece_cupboard)
		{
			box(index, { 0.0f, 0.98f, 0.0f }, { 0.94f, 1.96f, 0.54f }, structures::surface_wood);
		}
	}
	/*
	//=====================================================================================
	*/
	bool building_c::privileged(structures::vec3_s position, std::uint32_t identity)
	{
		auto blocked{ false };

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (const auto& cupboard{ placed[index] }; cupboard.piece == structures::piece_cupboard && cupboard.destroyed == false && mathematics.distance(cupboard.position, position) < cupboard_range)
			{
				const auto found{ authorized.find(index) };

				blocked = blocked || found == authorized.end() || std::find(found->second.begin(), found->second.end(), identity) == found->second.end();
			}
		}

		return blocked == false;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::accessible(std::uint32_t index, std::uint32_t identity)
	{
		if (const auto lock{ locks.find(index) }; lock != locks.end())
		{
			return std::find(lock->second.authorized.begin(), lock->second.authorized.end(), identity) != lock->second.authorized.end();
		}

		auto granted{ index < placed.size() && placed[index].owner == identity };

		for (auto cupboard{ 0u }; cupboard < placed.size() && index < placed.size() && granted == false; cupboard++)
		{
			if (placed[cupboard].piece == structures::piece_cupboard && placed[cupboard].destroyed == false && mathematics.distance(placed[cupboard].position, placed[index].position) < cupboard_range)
			{
				const auto found{ authorized.find(cupboard) };

				granted = found != authorized.end() && std::find(found->second.begin(), found->second.end(), identity) != found->second.end();
			}
		}

		return granted;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::attach_lock(std::uint32_t door, std::uint32_t identity)
	{
		auto attached{ false };

		if (door < placed.size() && placed[door].piece == structures::piece_door && placed[door].destroyed == false && locks.count(door) == 0u && accessible(door, identity))
		{
			locks[door] = { identity, 0u, false, { identity } };

			dirty.push_back(door);

			attached = true;
		}

		return attached;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t building_c::enter_code(std::uint32_t door, std::uint32_t identity, std::uint32_t code)
	{
		auto result{ -1 };

		if (const auto found{ locks.find(door) }; found != locks.end() && code <= 9999u)
		{
			auto& lock{ found->second };

			if (std::find(lock.authorized.begin(), lock.authorized.end(), identity) != lock.authorized.end())
			{
				lock.code = code;
				lock.coded = true;
				lock.authorized = { identity };

				result = 2;
			}

			else if (lock.coded && lock.code == code)
			{
				lock.authorized.push_back(identity);

				result = 1;
			}

			else
			{
				result = 0;
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void building_c::authorize(std::uint32_t index, std::uint32_t identity)
	{
		if (index < placed.size() && placed[index].piece == structures::piece_cupboard && placed[index].destroyed == false)
		{
			auto& list{ authorized[index] };

			if (std::find(list.begin(), list.end(), identity) == list.end())
			{
				list.push_back(identity);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t building_c::cupboard_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		auto best{ -1 };
		auto best_away{ 0.7f };

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (const auto& cupboard{ placed[index] }; cupboard.piece == structures::piece_cupboard && cupboard.destroyed == false)
			{
				const auto middle{ cupboard.position + structures::vec3_s{ 0.0f, 1.0f, 0.0f } };
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
	void building_c::box(std::uint32_t index, structures::vec3_s center, structures::vec3_s size, std::uint32_t surface)
	{
		auto& structure{ placed[index] };

		world.add_box(structure.position + maps.rotate_yaw(center, structure.yaw), size, mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, structure.yaw), surface, structures::contents_solid);
		world.insert(static_cast<std::uint32_t>(world.brushes.size() - 1u));

		by_brush[static_cast<std::int32_t>(world.brushes.size() - 1u)] = index;

		structure.first_brush = structure.first_brush < 0 ? static_cast<std::int32_t>(world.brushes.size() - 1u) : structure.first_brush;
		structure.brush_count++;
	}
	/*
	//=====================================================================================
	*/
	void building_c::ramp(std::uint32_t index, structures::vec3_s center, structures::vec3_s size, std::float_t spin, std::uint32_t surface)
	{
		auto& structure{ placed[index] };

		world.add_ramp(structure.position + maps.rotate_yaw(center, structure.yaw), size, structure.yaw + spin, surface, structures::contents_solid);
		world.insert(static_cast<std::uint32_t>(world.brushes.size() - 1u));

		by_brush[static_cast<std::int32_t>(world.brushes.size() - 1u)] = index;

		structure.first_brush = structure.first_brush < 0 ? static_cast<std::int32_t>(world.brushes.size() - 1u) : structure.first_brush;
		structure.brush_count++;
	}
	/*
	//=====================================================================================
	*/
	void building_c::toggle_door(std::uint32_t index)
	{
		if (index < placed.size() && placed[index].piece == structures::piece_door && placed[index].destroyed == false)
		{
			refresh(index, placed[index].open == false, false);

			dirty.push_back(index);

			if (gpu.device)
			{
				mixer.play(structures::sound_container, placed[index].position + structures::vec3_s{ 0.0f, 1.2f, 0.0f }, 0.8f, placed[index].open ? 1.05f : 0.85f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t building_c::door_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		auto best{ -1 };
		auto best_away{ 0.9f };

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (const auto& door{ placed[index] }; door.piece == structures::piece_door && door.destroyed == false)
			{
				const auto middle{ door.position + structures::vec3_s{ 0.0f, 1.1f, 0.0f } };
				const auto along{ mathematics.dot(middle - origin, forward) };
				const auto away{ mathematics.length(middle - origin - forward * along) };

				if (along > 0.2f && along < interact_range + 0.5f && away < best_away)
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
	void building_c::decay(std::float_t elapsed)
	{
		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (auto& structure{ placed[index] }; structure.destroyed == false)
			{
				auto covered{ false };

				for (const auto& cupboard : placed)
				{
					covered = covered || (cupboard.piece == structures::piece_cupboard && cupboard.destroyed == false && mathematics.distance(cupboard.position, structure.position) < cupboard_range);
				}

				if (covered == false)
				{
					const auto tier{ std::min(structure.tier, building_tier_count - 1u) };

					structure.health -= durability(index) * elapsed / (building_decay_hours[tier] * 3600.0f);

					if (structure.health <= 0.0f)
					{
						refresh(index, structure.open, true);

						dirty.push_back(index);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t building_c::durability(std::uint32_t index)
	{
		return piece_definitions[placed[index].piece].health * building_tiers[std::min(placed[index].tier, building_tier_count - 1u)].health;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::upgrade(std::uint32_t index)
	{
		auto upgraded{ false };

		if (index < placed.size() && placed[index].piece < structures::piece_door && placed[index].destroyed == false && placed[index].tier + 1u < building_tier_count)
		{
			retier(index, placed[index].tier + 1u);

			placed[index].health = durability(index);

			dirty.push_back(index);

			upgraded = true;
		}

		return upgraded;
	}
	/*
	//=====================================================================================
	*/
	void building_c::retier(std::uint32_t index, std::uint32_t tier)
	{
		auto& structure{ placed[index] };

		structure.tier = std::min(tier, building_tier_count - 1u);

		for (auto brush{ 0u }; brush < structure.brush_count && structure.first_brush >= 0; brush++)
		{
			world.brushes[static_cast<std::uint32_t>(structure.first_brush) + brush].surface = building_tiers[structure.tier].surface;
		}
	}
	/*
	//=====================================================================================
	*/
	bool building_c::repair(std::uint32_t index, std::float_t amount)
	{
		auto repaired{ false };

		if (index < placed.size() && placed[index].destroyed == false && placed[index].health < durability(index) - 0.5f)
		{
			placed[index].health = std::min(durability(index), placed[index].health + amount);

			dirty.push_back(index);

			repaired = true;
		}

		return repaired;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t building_c::structure_target(structures::vec3_s origin, structures::vec3_s forward, std::float_t reach)
	{
		const auto result{ world.trace(origin, origin + forward * reach, { 0.02f, 0.02f, 0.02f }, structures::contents_solid) };
		const auto found{ result.hit ? by_brush.find(result.brush) : by_brush.end() };

		return found != by_brush.end() && placed[found->second].destroyed == false ? static_cast<std::int32_t>(found->second) : -1;
	}
	/*
	//=====================================================================================
	*/
	bool building_c::damage(std::int32_t brush, std::float_t amount, bool bullet)
	{
		if (const auto found{ by_brush.find(brush) }; found != by_brush.end() && placed[found->second].destroyed == false)
		{
			auto& structure{ placed[found->second] };

			const auto& tier{ building_tiers[std::min(structure.tier, building_tier_count - 1u)] };

			structure.health -= amount * (bullet ? tier.bullets : tier.blows);

			dirty.push_back(found->second);

			if (gpu.device)
			{
				particles.impact(world.brushes[brush].surface, world.brushes[brush].bounds_min * 0.5f + world.brushes[brush].bounds_max * 0.5f, { 0.0f, 1.0f, 0.0f });

				mixer.play(structure.piece < structures::piece_door ? tier.sound : structures::sound_hit_wood, structure.position + structures::vec3_s{ 0.0f, 1.2f, 0.0f }, 1.0f, 0.75f + random() * 0.2f);
			}

			if (structure.health <= 0.0f)
			{
				refresh(found->second, structure.open, true);

				dirty.push_back(found->second);

				if (gpu.device && client.connected() == false)
				{
					survival.post("A structure was destroyed", 0);
				}
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s building_c::matrix(const structures::structure_s& piece)
	{
		const auto placement{ mathematics.multiply(mathematics.rotation_y(piece.yaw), mathematics.translation(piece.position)) };

		if (piece.piece == structures::piece_door)
		{
			return mathematics.multiply(mathematics.multiply(mathematics.rotation_y(-mathematics.ease_in_out_cubic(piece.swing) * 1.75f), mathematics.translation({ -0.54f, 0.01f, 0.0f })), placement);
		}

		return placement;
	}
	/*
	//=====================================================================================
	*/
	void building_c::effects(std::float_t delta)
	{
		if (client.connected() == false)
		{
			smelt(delta);

			stirred.clear();
			dirty.clear();
		}

		for (const auto& container : containers)
		{
			if (auto& structure{ placed[container.structure] }; container.burning && container.kind == structures::container_furnace && structure.destroyed == false && mathematics.distance(structure.position, renderer.camera.position) < 90.0f)
			{
				const auto mouth{ structure.position + maps.rotate_yaw({ 0.0f, 0.3f, -0.6f }, structure.yaw) };
				const auto flicker{ 0.8f + 0.2f * std::sin(clock * 17.0f + structure.flicker) };

				structure.swing += delta;

				while (structure.swing > 0.05f)
				{
					structure.swing -= 0.05f;

					particles.emit(structures::particle_fire, mouth + structures::vec3_s{ random() - 0.5f, 0.0f, random() - 0.5f } * 0.2f, { 0.0f, 0.3f, 0.0f }, 0.06f, 1u, false);

					if (random() < 0.3f)
					{
						particles.emit(structures::particle_smoke, structure.position + structures::vec3_s{ 0.0f, 1.75f, 0.0f }, { 0.2f, 0.9f, 0.1f }, 0.12f, 1u, false);
					}
				}

				renderer.add_light(mouth + maps.rotate_yaw({ 0.0f, 0.1f, -0.4f }, structure.yaw), 7.0f, structures::vec3_s{ 3.2f, 1.5f, 0.5f } * flicker);
			}
		}

		for (auto& structure : placed)
		{
			if (structure.piece == structures::piece_campfire && structure.destroyed == false && structure.container >= 0 && containers[structure.container].burning && mathematics.distance(structure.position, renderer.camera.position) < 90.0f)
			{
				const auto flame{ structure.position + structures::vec3_s{ 0.0f, 0.12f, 0.0f } };
				const auto flicker{ 0.82f + 0.18f * std::sin(clock * 21.0f + structure.flicker) * std::sin(clock * 6.7f + structure.flicker * 2.0f) };

				structure.swing += delta;

				while (structure.swing > 0.03f)
				{
					structure.swing -= 0.03f;

					particles.emit(structures::particle_fire, flame + structures::vec3_s{ random() - 0.5f, 0.0f, random() - 0.5f } * 0.3f, { 0.0f, 0.45f, 0.0f }, 0.1f, 1u, false);

					if (random() < 0.08f)
					{
						particles.emit(structures::particle_smoke, flame + structures::vec3_s{ 0.0f, 0.6f, 0.0f }, { 0.25f, 0.7f, 0.1f }, 0.15f, 1u, false);
					}

					if (random() < 0.05f)
					{
						particles.emit(structures::particle_ember, flame + structures::vec3_s{ 0.0f, 0.2f, 0.0f }, { 0.0f, 1.4f, 0.0f }, 0.5f, 1u, false);
					}
				}

				renderer.add_light(flame + structures::vec3_s{ 0.0f, 0.55f, 0.0f }, 12.0f, structures::vec3_s{ 3.6f, 1.9f, 0.7f } * flicker);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void building_c::submit()
	{
		for (const auto& entry : locks)
		{
			if (entry.first < placed.size() && placed[entry.first].destroyed == false && keypad_mesh.vertex_buffer)
			{
				const auto transform{ matrix(placed[entry.first]) };

				renderer.submit(&keypad_mesh, transform, transform, -1.0f, 0u);
			}
		}

		for (const auto& structure : placed)
		{
			if (structure.destroyed == false)
			{
				const auto transform{ matrix(structure) };
				const auto structural{ structure.piece < structures::piece_door };
				const auto tier{ std::min(structure.tier, building_tier_count - 1u) };
				const auto shaped{ structural && tier_meshes[tier][structure.piece].vertex_buffer };

				renderer.submit(shaped ? &tier_meshes[tier][structure.piece] : &meshes[structure.piece], transform, transform, structural && shaped == false ? tier_materials[tier] : -1.0f, 0u);
			}
		}

		if (preview.active)
		{
			structures::structure_s ghost{};

			ghost.position = preview.position;
			ghost.yaw = preview.yaw;
			ghost.piece = preview.piece;

			const auto transform{ matrix(ghost) };
			const auto twig{ preview.piece < structures::piece_door && tier_meshes[0][preview.piece].vertex_buffer };

			renderer.submit(twig ? &tier_meshes[0][preview.piece] : &meshes[preview.piece], transform, transform, static_cast<std::float_t>(preview.valid ? ghost_valid : ghost_invalid), structures::draw_flag_no_shadow);
		}
	}
	/*
	//=====================================================================================
	*/
	void building_c::test_base(structures::vec3_s origin, std::float_t yaw)
	{
		const structures::vec3_s cells[4] = { { -1.5f, 0.0f, -1.5f }, { 1.5f, 0.0f, -1.5f }, { -1.5f, 0.0f, 1.5f }, { 1.5f, 0.0f, 1.5f } };

		auto top{ -FLT_MAX };

		for (const auto& cell : cells)
		{
			for (auto corner{ 0u }; corner < 4u; corner++)
			{
				const auto point{ origin + maps.rotate_yaw(cell + structures::vec3_s{ corner & 1u ? 1.5f : -1.5f, 0.0f, corner & 2u ? 1.5f : -1.5f }, yaw) };

				top = std::max(top, terrain.height(point.x, point.z));
			}
		}

		survival.give(structures::item_wood, 4000u, false);

		for (const auto& cell : cells)
		{
			const auto position{ origin + maps.rotate_yaw(cell, yaw) };

			place({ { position.x, top + 0.15f, position.z }, yaw, structures::piece_foundation, -1, true, true });
		}

		for (auto index{ 0u }; index < 4u; index++)
		{
			const auto base{ placed[index] };

			for (auto side{ 0u }; side < 4u; side++)
			{
				const auto edge{ base.position + maps.rotate_yaw(side % 2u ? structures::vec3_s{ side == 1u ? 1.5f : -1.5f, 0.0f, 0.0f } : structures::vec3_s{ 0.0f, 0.0f, side == 0u ? -1.5f : 1.5f }, base.yaw) };
				const auto neighbor{ base.position + (edge - base.position) * 2.0f };

				auto inside{ false };

				for (auto other{ 0u }; other < 4u; other++)
				{
					inside = inside || mathematics.distance(placed[other].position, neighbor) < 0.5f;
				}

				if (inside == false)
				{
					place({ edge, base.yaw + static_cast<std::float_t>(side) * half_pi, index == 0u && side == 0u ? structures::piece_doorway : (index == 1u && side == 1u ? structures::piece_window : structures::piece_wall), static_cast<std::int32_t>(index), true, true });
				}
			}
		}

		for (auto index{ 0u }; index < 2u; index++)
		{
			place({ placed[index].position + structures::vec3_s{ 0.0f, building_height, 0.0f }, placed[index].yaw, structures::piece_roof, static_cast<std::int32_t>(index), true, true });
		}

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			if (placed[index].piece == structures::piece_doorway)
			{
				survival.slots[inventory_slots + survival.active_slot] = { structures::item_wooden_door, 1u, 1.0f };

				place({ placed[index].position, placed[index].yaw, structures::piece_door, static_cast<std::int32_t>(index), true, true });

				attach_lock(static_cast<std::uint32_t>(placed.size() - 1u), 0u);
			}
		}

		const auto fire{ origin + maps.rotate_yaw({ -1.5f, 0.0f, -6.0f }, yaw) };
		const auto sleep{ origin + maps.rotate_yaw({ 1.2f, 0.0f, 1.5f }, yaw) };

		survival.slots[inventory_slots + survival.active_slot] = { structures::item_campfire, 1u, 1.0f };

		place({ { fire.x, terrain.height(fire.x, fire.z), fire.z }, yaw, structures::piece_campfire, -1, true, true });

		survival.slots[inventory_slots + survival.active_slot] = { structures::item_sleeping_bag, 1u, 1.0f };

		place({ { sleep.x, top + 0.15f, sleep.z }, yaw + half_pi, structures::piece_sleeping_bag, -1, true, true });

		const auto oven{ origin + maps.rotate_yaw({ 2.2f, 0.0f, -5.5f }, yaw) };
		const auto chest{ origin + maps.rotate_yaw({ -2.2f, 0.0f, 2.2f }, yaw) };

		survival.slots[inventory_slots + survival.active_slot] = { structures::item_furnace, 1u, 1.0f };

		place({ { oven.x, terrain.height(oven.x, oven.z), oven.z }, yaw, structures::piece_furnace, -1, true, true });

		survival.slots[inventory_slots + survival.active_slot] = { structures::item_storage_box, 1u, 1.0f };

		place({ { chest.x, top + 0.15f, chest.z }, yaw + pi, structures::piece_storage_box, -1, true, true });

		auto furnace{ -1 };

		for (auto index{ 0u }; index < containers.size(); index++)
		{
			auto& container{ containers[index] };

			if (container.kind == structures::container_furnace)
			{
				container.slots[furnace_fuel_slot] = { structures::item_wood, 120u, 1.0f };
				container.slots[furnace_first_input] = { structures::item_metal_ore, 60u, 1.0f };
				container.slots[furnace_first_input + 1u] = { structures::item_sulfur_ore, 40u, 1.0f };
				container.burning = true;

				furnace = static_cast<std::int32_t>(index);
			}

			else if (container.kind == structures::container_campfire)
			{
				container.slots[furnace_fuel_slot] = { structures::item_wood, 60u, 1.0f };
				container.slots[furnace_first_input] = { structures::item_potato, 6u, 1.0f };
				container.slots[furnace_first_input + 1u] = { structures::item_corn, 4u, 1.0f };
				container.burning = true;
			}

			else
			{
				container.slots[0] = { structures::item_canned_beans, 3u, 1.0f };
				container.slots[1] = { structures::item_bandage, 2u, 1.0f };
				container.slots[5] = { structures::item_stone, 400u, 1.0f };
			}
		}

		const auto stand{ survival.inventory_open ? oven + maps.rotate_yaw({ 0.0f, 0.0f, 1.8f }, yaw) : origin };
		const auto well{ origin + maps.rotate_yaw({ -5.5f, 0.0f, -2.0f }, yaw) };

		survival.slots[inventory_slots + survival.active_slot] = { structures::item_well, 1u, 1.0f };

		place({ { well.x, terrain.height(well.x, well.z), well.z }, yaw, structures::piece_well, -1, true, true });

		survival.slots[inventory_slots + survival.active_slot] = { structures::item_building_plan, 1u, 1.0f };
		survival.open_container = survival.inventory_open ? furnace : -1;

		for (auto index{ 0u }; index < placed.size(); index++)
		{
			const auto walled{ placed[index].piece == structures::piece_wall || placed[index].piece == structures::piece_window };

			for (auto step{ 0u }; step < (walled ? 2u + index % 2u : 1u); step++)
			{
				upgrade(index);
			}
		}

		const auto showcase{ origin + maps.rotate_yaw({ 7.5f, 0.0f, -1.5f }, yaw) };
		const auto twig{ static_cast<std::int32_t>(placed.size()) };

		place({ { showcase.x, top + 0.15f, showcase.z }, yaw, structures::piece_foundation, -1, true, true });
		place({ placed[twig].position + maps.rotate_yaw({ 0.0f, 0.0f, -1.5f }, yaw), yaw, structures::piece_window, twig, true, true });
		place({ placed[twig].position + maps.rotate_yaw({ 1.5f, 0.0f, 0.0f }, yaw), yaw + half_pi, structures::piece_wall, twig, true, true });
		place({ placed[twig].position + structures::vec3_s{ 0.0f, building_height, 0.0f }, yaw, structures::piece_roof, twig, true, true });

		dirty.clear();

		player.spawn({ stand.x, (survival.inventory_open ? terrain.height(stand.x, stand.z) : top) + 0.2f, stand.z }, yaw + pi);

		logger.write("building: test base with %zu pieces, %zu brushes", placed.size(), world.brushes.size());
	}
	/*
	//=====================================================================================
	*/
	std::float_t building_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
