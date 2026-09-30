
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	farming_c farming;

	void farming_c::clear()
	{
		crops.clear();
		springs.clear();

		ghosting = false;
	}
	/*
	//=====================================================================================
	*/
	void farming_c::destroy()
	{
		functions::release(pool.vertex_buffer);
		functions::release(pool.index_buffer);

		pool = {};
	}
	/*
	//=====================================================================================
	*/
	void farming_c::create_models()
	{
		if (models.existing("potato_plant") == nullptr)
		{
			create_potato("potato_plant");
			create_corn("corn_stalk");
			create_pumpkin("pumpkin_patch");
			create_mound("soil_mound");
		}

		for (auto kind{ 1u }; kind < structures::crop_count; kind++)
		{
			shapes[kind] = models.find(crop_definitions[kind].model);
		}

		mound = models.find("soil_mound");
		withered = models.variant(structures::material_terrain_grass_dry, { 0.62f, 0.46f, 0.3f }, 0.0f);

		if (pool.index_count == 0u)
		{
			pool_builder.clear();
			pool_builder.set_material(structures::material_pond);
			pool_builder.cylinder({ 0.0f, -0.02f, 0.0f }, { 0.0f, 1.0f, 0.0f }, 1.0f, 0.04f, 32u, true);
			pool_builder.compute_tangents(0u, 0u);
			pool_builder.upload(pool);
		}
	}
	/*
	//=====================================================================================
	*/
	void farming_c::create_potato(const char* name)
	{
		const auto source{ models.find("shrub_04") };

		if (source && source->parts.size())
		{
			const auto& branch{ source->parts[0] };
			const auto leaf{ models.variant(source->vertices[source->indices[branch.first_index]].material, { 0.7f, 0.95f, 0.52f }, 0.0f) };
			const auto flower{ models.variant(structures::material_paint_white, { 0.92f, 0.86f, 1.0f }, 0.0f) };

			if (const auto model{ models.create(name) }; model)
			{
				models.begin_part(*model, "potato_leaves");

				for (auto index{ 0u }; index < 6u; index++)
				{
					const auto azimuth{ (static_cast<std::float_t>(index) + random() * 0.6f) / 6.0f * two_pi };
					const auto elevation{ 0.25f + random() * 0.45f };
					const auto scale{ 1.35f + random() * 0.45f };
					const structures::vec3_s direction{ std::cos(azimuth) * std::cos(elevation), std::sin(elevation), std::sin(azimuth) * std::cos(elevation) };
					const structures::vec3_s side{ -std::sin(azimuth), 0.0f, std::cos(azimuth) };
					const auto up{ mathematics.cross(side, direction) };

					models.append(*model, *source, branch, mathematics.basis(direction * scale, up * scale, side * scale, { std::cos(azimuth) * 0.05f, random() * 0.05f, std::sin(azimuth) * 0.05f }), leaf, 0.8f, index * 6151u);
				}

				const auto leaves{ static_cast<std::uint32_t>(model->vertices.size()) };

				models.begin_part(*model, "potato_flowers");

				for (auto index{ 0u }; index < 7u; index++)
				{
					auto top{ model->vertices[static_cast<std::uint32_t>(random() * static_cast<std::float_t>(leaves - 1u))] };

					for (auto probe{ 0u }; probe < 8u; probe++)
					{
						const auto& other{ model->vertices[static_cast<std::uint32_t>(random() * static_cast<std::float_t>(leaves - 1u))] };

						top = other.position.y > top.position.y ? other : top;
					}

					models.sphere(*model, top.position + structures::vec3_s{ 0.0f, 0.02f, 0.0f }, 0.016f, flower);
				}

				models.seal(*model);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void farming_c::create_corn(const char* name)
	{
		const auto source{ models.find("nettle_plant") };
		const auto tall_a{ source ? models.part(*source, "nettle_plant_tall_a_LOD0") : nullptr };
		const auto tall_b{ source ? models.part(*source, "nettle_plant_tall_b_LOD0") : nullptr };

		if (tall_a && tall_b)
		{
			const auto leaf{ models.variant(source->vertices[source->indices[tall_a->first_index]].material, { 1.12f, 1.12f, 0.56f }, 0.0f) };
			const auto kernel{ models.variant(structures::material_paint_white, { 1.0f, 0.78f, 0.24f }, 0.0f) };

			if (const auto model{ models.create(name) }; model)
			{
				models.begin_part(*model, "corn_stalks");

				for (auto stalk{ 0u }; stalk < 3u; stalk++)
				{
					const auto& part{ stalk % 2u ? *tall_b : *tall_a };
					const auto center{ (part.bounds_min + part.bounds_max) * 0.5f };
					const auto angle{ static_cast<std::float_t>(stalk) * 2.1f + 0.4f };
					const auto height{ 7.8f + static_cast<std::float_t>(stalk) * 0.6f };

					models.append(*model, *source, part, mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation({ -center.x, -part.bounds_min.y, -center.z }), mathematics.scaling({ 3.4f, height, 3.4f })), mathematics.rotation_y(angle)), mathematics.translation({ std::sin(angle) * 0.07f, 0.0f, std::cos(angle) * 0.07f })), leaf, 0.85f, stalk * 7919u + 3u);
				}

				models.begin_part(*model, "corn_cobs");

				for (auto cob{ 0u }; cob < 2u; cob++)
				{
					const auto angle{ static_cast<std::float_t>(cob) * pi + 0.7f };
					const structures::vec3_s base{ std::sin(angle) * 0.06f, 0.92f + static_cast<std::float_t>(cob) * 0.18f, std::cos(angle) * 0.06f };
					const structures::vec3_s lean{ std::sin(angle) * 0.35f, 0.94f, std::cos(angle) * 0.35f };

					for (auto kernel_row{ 0u }; kernel_row < 6u; kernel_row++)
					{
						const auto along{ static_cast<std::float_t>(kernel_row) * 0.032f };

						models.sphere(*model, base + lean * along, 0.026f - static_cast<std::float_t>(kernel_row) * 0.0022f, kernel);
					}
				}

				models.seal(*model);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void farming_c::create_pumpkin(const char* name)
	{
		const auto source{ models.find("fern_02") };
		const auto fronds{ source ? models.part(*source, "fern_02_b") : nullptr };

		if (fronds)
		{
			const auto leaf{ models.variant(source->vertices[source->indices[fronds->first_index]].material, { 0.82f, 1.0f, 0.56f }, 0.0f) };
			const auto rind{ models.variant(structures::material_paint_white, { 0.95f, 0.42f, 0.07f }, 0.0f) };
			const auto stem{ models.variant(structures::material_paint_white, { 0.32f, 0.36f, 0.14f }, 0.0f) };
			const auto center{ (fronds->bounds_min + fronds->bounds_max) * 0.5f };

			if (const auto model{ models.create(name) }; model)
			{
				models.begin_part(*model, "pumpkin_leaves");
				models.append(*model, *source, *fronds, mathematics.multiply(mathematics.translation({ -center.x, -fronds->bounds_min.y, -center.z }), mathematics.scaling({ 1.0f, 0.62f, 1.0f })), leaf, 0.85f, 17u);
				models.append(*model, *source, *fronds, mathematics.multiply(mathematics.multiply(mathematics.translation({ -center.x, -fronds->bounds_min.y, -center.z }), mathematics.scaling({ 0.8f, 0.5f, 0.8f })), mathematics.rotation_y(2.4f)), leaf, 0.85f, 29u);

				models.begin_part(*model, "pumpkin_fruit");

				for (const auto& fruit : { structures::vec4_s{ 0.22f, 0.0f, 0.12f, 0.17f }, structures::vec4_s{ -0.2f, 0.0f, -0.16f, 0.12f } })
				{
					for (auto lobe{ 0u }; lobe < 7u; lobe++)
					{
						const auto angle{ static_cast<std::float_t>(lobe) / 7.0f * two_pi };

						models.sphere(*model, { fruit.x + std::cos(angle) * fruit.w * 0.38f, fruit.w * 0.72f, fruit.z + std::sin(angle) * fruit.w * 0.38f }, fruit.w * 0.7f, rind);
					}

					models.sphere(*model, { fruit.x, fruit.w * 1.38f, fruit.z }, fruit.w * 0.14f, stem);
				}

				models.seal(*model);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void farming_c::create_mound(const char* name)
	{
		const auto dirt{ models.variant(structures::material_terrain_dirt, { 0.55f, 0.46f, 0.38f }, 0.0f) };

		if (const auto model{ models.create(name) }; model)
		{
			models.begin_part(*model, "mound");
			models.sphere(*model, { 0.0f, -0.31f, 0.0f }, 0.37f, dirt);
			models.seal(*model);
		}
	}
	/*
	//=====================================================================================
	*/
	void farming_c::update(std::float_t delta, bool input_enabled)
	{
		const auto online{ client.connected() };

		if (online == false)
		{
			grow(delta);
		}

		ghosting = false;

		if (input_enabled && survival.vitals.dead == false && survival.inventory_open == false)
		{
			const auto origin{ player.eye };
			const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };
			const auto& held{ survival.held() };
			const auto& definition{ item_definitions[held.item] };

			char text[128]{};

			structures::vec3_s spot{};

			if (const auto target{ crop_target(origin, forward) }; target >= 0)
			{
				auto& crop{ crops[target] };

				const auto& kind{ crop_definitions[crop.kind] };

				if (crop.dead)
				{
					std::snprintf(text, sizeof(text), "Pull up the dead %s   [E]", kind.name);
				}

				else if (crop.growth >= 1.0f)
				{
					std::snprintf(text, sizeof(text), crop.ripe_time > farm_rot_time * 0.5f ? "Harvest the %s (going bad)   [E]" : "Harvest the %s   [E]", kind.name);
				}

				else if (held.item == structures::item_water_bottle)
				{
					std::snprintf(text, sizeof(text), "Water the %s   [LMB]", kind.name);
				}

				else
				{
					std::snprintf(text, sizeof(text), "%s  %.0f%%  %s", kind.name, crop.growth * 100.0f, irrigated(crop.position) ? "(irrigated)" : (crop.water <= 0.0f ? "(parched, dying)" : (crop.water < 0.3f ? "(thirsty)" : "(watered)")));
				}

				hud.set_prompt(text);

				if (platform.tapped(structures::bind_use) && (crop.dead || crop.growth >= 1.0f))
				{
					if (online)
					{
						client.act(structures::act_reap, crop.position);

						mixer.play_2d(structures::sound_pickup, 0.55f, 0.9f + random() * 0.1f);
					}

					else
					{
						reap(static_cast<std::uint32_t>(target), survival);
					}

					platform.consume(structures::bind_use);
				}

				else if (platform.input.pressed[VK_LBUTTON] && held.item == structures::item_water_bottle && crop.dead == false)
				{
					mixer.play(structures::sound_hit_soft, crop.position, 0.6f, 1.3f);

					if (online)
					{
						client.act(structures::act_water, crop.position);
					}

					else
					{
						water(static_cast<std::uint32_t>(target), survival, survival.active_slot);
					}

					platform.input.pressed[VK_LBUTTON] = false;
				}
			}

			else if (definition.crop != structures::crop_none && soil(origin, forward, spot))
			{
				ghosting = true;
				ghost = spot;
				ghost_kind = definition.crop;

				std::snprintf(text, sizeof(text), "Plant %s   [LMB]", definition.name);

				hud.set_prompt(text);

				if (platform.input.pressed[VK_LBUTTON] && online)
				{
					client.act(structures::act_plant, spot);

					platform.input.pressed[VK_LBUTTON] = false;
				}

				else if (platform.input.pressed[VK_LBUTTON] && sow(survival, survival.active_slot, spot))
				{
					platform.input.pressed[VK_LBUTTON] = false;
				}
			}

			else if (well_target(origin, forward) >= 0 || spring_target(origin, forward) >= 0 || sea_target(origin, forward))
			{
				hud.set_prompt(well_target(origin, forward) >= 0 ? "Drink from the well   [E]" : (spring_target(origin, forward) >= 0 ? "Drink from the spring   [E]" : "Drink the sea water   [E]"));

				if (platform.tapped(structures::bind_use))
				{
					mixer.play_2d(structures::sound_pickup, 0.45f, 0.6f);

					if (online)
					{
						client.act(structures::act_drink, origin);
					}

					else
					{
						drink(survival, origin, forward);
					}

					platform.consume(structures::bind_use);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool farming_c::sow(survival_c& owner, std::uint32_t slot, structures::vec3_s spot)
	{
		auto& seeds{ owner.slots[inventory_slots + std::min(slot, hotbar_slots - 1u)] };

		const auto kind{ item_definitions[seeds.item].crop };

		if (kind != structures::crop_none && seeds.amount && plant(kind, spot))
		{
			seeds.amount--;

			if (seeds.amount == 0u)
			{
				seeds = {};
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void farming_c::water(std::uint32_t index, survival_c& owner, std::uint32_t slot)
	{
		auto& bottle{ owner.slots[inventory_slots + std::min(slot, hotbar_slots - 1u)] };

		if (index < crops.size() && bottle.item == structures::item_water_bottle && bottle.amount && crops[index].dead == false)
		{
			crops[index].water = 1.0f;

			bottle.amount--;

			if (bottle.amount == 0u)
			{
				bottle = {};
			}

			revision++;
		}
	}
	/*
	//=====================================================================================
	*/
	void farming_c::drink(survival_c& owner, structures::vec3_s origin, structures::vec3_s forward)
	{
		if (well_target(origin, forward) >= 0 || spring_target(origin, forward) >= 0)
		{
			const auto from_well{ well_target(origin, forward) >= 0 };

			owner.vitals.hydration = std::min(maximum_hydration, owner.vitals.hydration + (from_well ? well_drink : spring_drink));
			owner.notify(from_well ? "Cold, clean water" : "Fresh water. It tastes of stone.", 0);
		}

		else if (sea_target(origin, forward))
		{
			owner.vitals.hydration = std::min(maximum_hydration, owner.vitals.hydration + sea_drink);
			owner.notify("Salt water. It burns.", 0);
			owner.damage(sea_sickness);
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t farming_c::crop_near(structures::vec3_s position)
	{
		auto best{ -1 };
		auto best_distance{ 0.5f };

		for (auto index{ 0u }; index < crops.size(); index++)
		{
			if (const auto distance{ mathematics.length(structures::vec3_s{ crops[index].position.x - position.x, 0.0f, crops[index].position.z - position.z }) }; distance < best_distance)
			{
				best = static_cast<std::int32_t>(index);
				best_distance = distance;
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	void farming_c::grow(std::float_t delta)
	{
		const auto daylight{ mathematics.saturate((atmosphere.hours - 5.5f) * 0.8f) * mathematics.saturate((19.5f - atmosphere.hours) * 0.8f) };

		for (auto& crop : crops)
		{
			if (crop.dead == false)
			{
				const auto& definition{ crop_definitions[crop.kind] };

				crop.water = irrigated(crop.position) ? 1.0f : std::max(0.0f, crop.water - delta / farm_water_time);
				crop.growth = crop.water > 0.0f ? std::min(1.0f, crop.growth + delta / definition.grow_time * (0.35f + 0.65f * daylight)) : crop.growth;
				crop.ripe_time = crop.growth >= 1.0f ? crop.ripe_time + delta : 0.0f;
				crop.health = crop.water <= 0.0f || crop.ripe_time > farm_rot_time ? crop.health - delta / farm_wither_time : std::min(1.0f, crop.health + delta / (farm_wither_time * 2.0f));
				crop.dead = crop.health <= 0.0f;

				revision += crop.dead ? 1u : 0u;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool farming_c::plant(std::uint32_t kind, structures::vec3_s position)
	{
		if (crops.size() < maximum_crops)
		{
			crops.push_back({ position, random() * two_pi, 0.0f, 0.35f, 1.0f, 0.0f, kind, false });

			revision++;

			if (gpu.device)
			{
				mixer.play(structures::sound_hit_soft, position, 0.7f, 0.8f + random() * 0.15f);

				particles.impact(structures::surface_dirt, position + structures::vec3_s{ 0.0f, 0.05f, 0.0f }, { 0.0f, 1.0f, 0.0f });
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void farming_c::reap(std::uint32_t index, survival_c& owner)
	{
		if (index < crops.size())
		{
			const auto crop{ crops[index] };

			if (crop.dead == false && crop.growth >= 1.0f)
			{
				const auto& definition{ crop_definitions[crop.kind] };
				const auto amount{ definition.minimum + static_cast<std::uint32_t>(random() * static_cast<std::float_t>(definition.maximum - definition.minimum + 1u) * 0.999f) };

				owner.give(definition.yield, std::max(1u, static_cast<std::uint32_t>(static_cast<std::float_t>(amount) * (0.4f + 0.6f * crop.health) + 0.5f)), true);

				if (definition.bonus != structures::item_none)
				{
					owner.give(definition.bonus, definition.bonus_minimum + static_cast<std::uint32_t>(random() * static_cast<std::float_t>(definition.bonus_maximum - definition.bonus_minimum + 1u) * 0.999f), true);
				}
			}

			if (crop.dead || crop.growth >= 1.0f)
			{
				if (gpu.device)
				{
					mixer.play_2d(structures::sound_pickup, 0.55f, 0.9f + random() * 0.1f);

					particles.impact(structures::surface_dirt, crop.position + structures::vec3_s{ 0.0f, 0.1f, 0.0f }, { 0.0f, 1.0f, 0.0f });
				}

				crops.erase(crops.begin() + index);

				revision++;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool farming_c::soil(structures::vec3_s origin, structures::vec3_s forward, structures::vec3_s& out)
	{
		const auto hit{ world.trace(origin, origin + forward * farm_reach, { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };

		if (hit.hit && hit.normal.y > 0.82f && fertile(hit.end))
		{
			out = { hit.end.x, terrain.height(hit.end.x, hit.end.z), hit.end.z };

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool farming_c::fertile(structures::vec3_s point)
	{
		auto result{ false };

		if (terrain.enabled)
		{
			const auto ground{ terrain.height(point.x, point.z) };
			const auto rocky{ layer_barren[std::min(terrain.ground(point.x, point.z), terrain_layer_count - 1u)] ? 1.0f : 0.0f };

			auto crowded{ false };

			for (const auto& crop : crops)
			{
				crowded = crowded || mathematics.length(structures::vec3_s{ crop.position.x - point.x, 0.0f, crop.position.z - point.z }) < farm_spacing;
			}

			result = std::fabs(point.y - ground) < 0.25f && ground > sea_level + 0.6f && rocky < 0.5f && crowded == false && maps.cleared(point.x, point.z) == false;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t farming_c::crop_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		auto best{ -1 };
		auto best_away{ FLT_MAX };

		for (auto index{ 0u }; index < crops.size(); index++)
		{
			const auto& crop{ crops[index] };
			const auto size{ 0.16f + 0.84f * crop.growth };
			const auto middle{ crop.position + structures::vec3_s{ 0.0f, 0.25f * size + 0.05f, 0.0f } };
			const auto along{ mathematics.dot(middle - origin, forward) };
			const auto away{ mathematics.length(middle - origin - forward * along) };

			if (along > 0.2f && along < farm_reach + 0.4f && away < 0.3f + 0.25f * size && away < best_away)
			{
				best = static_cast<std::int32_t>(index);
				best_away = away;
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t farming_c::well_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		auto best{ -1 };

		for (auto index{ 0u }; index < building.placed.size(); index++)
		{
			if (const auto& well{ building.placed[index] }; well.piece == structures::piece_well && well.destroyed == false)
			{
				const auto middle{ well.position + structures::vec3_s{ 0.0f, 0.7f, 0.0f } };
				const auto along{ mathematics.dot(middle - origin, forward) };
				const auto away{ mathematics.length(middle - origin - forward * along) };

				best = along > 0.2f && along < interact_range + 0.8f && away < 1.0f ? static_cast<std::int32_t>(index) : best;
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t farming_c::spring_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		auto best{ -1 };

		if (forward.y < -0.1f)
		{
			for (auto index{ 0u }; index < springs.size(); index++)
			{
				const auto& spring{ springs[index] };
				const auto distance{ (spring.y - origin.y) / forward.y };
				const auto point{ origin + forward * distance };

				best = distance > 0.2f && distance < interact_range + 0.8f && mathematics.length(structures::vec3_s{ point.x - spring.x, 0.0f, point.z - spring.z }) < spring.w ? static_cast<std::int32_t>(index) : best;
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	bool farming_c::sea_target(structures::vec3_s origin, structures::vec3_s forward)
	{
		if (forward.y < -0.05f && terrain.enabled)
		{
			const auto distance{ (sea_level - origin.y) / forward.y };
			const auto point{ origin + forward * distance };

			return distance > 0.2f && distance < interact_range + 0.6f && terrain.height(point.x, point.z) < sea_level - 0.05f && world.trace(origin, point, { 0.05f, 0.05f, 0.05f }, structures::contents_solid).hit == false;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool farming_c::irrigated(structures::vec3_s position)
	{
		for (const auto& structure : building.placed)
		{
			if (structure.piece == structures::piece_well && structure.destroyed == false && mathematics.length(structures::vec3_s{ structure.position.x - position.x, 0.0f, structure.position.z - position.z }) < well_irrigation)
			{
				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void farming_c::submit()
	{
		for (const auto& spring : springs)
		{
			const auto placement{ mathematics.multiply(mathematics.scaling({ spring.w, 1.0f, spring.w }), mathematics.translation({ spring.x, spring.y, spring.z })) };

			renderer.submit(&pool, placement, placement, -1.0f, structures::draw_flag_no_shadow);
		}

		for (const auto& crop : crops)
		{
			const auto size{ (crop.dead ? 0.7f : 0.16f + 0.84f * mathematics.smoothstep(0.0f, 1.0f, crop.growth)) * crop_definitions[crop.kind].scale };
			const auto base{ mathematics.multiply(mathematics.rotation_y(crop.yaw), mathematics.translation(crop.position)) };
			const auto plant{ mathematics.multiply(mathematics.multiply(mathematics.scaling({ size, size * (crop.dead ? 0.55f : 1.0f), size }), mathematics.rotation_y(crop.yaw)), mathematics.translation(crop.position - structures::vec3_s{ 0.0f, 0.03f, 0.0f })) };

			if (const auto shape{ shapes[crop.kind] }; shape)
			{
				renderer.submit(&shape->mesh, plant, plant, crop.dead || crop.health < 0.4f ? static_cast<std::float_t>(withered) : -1.0f, 0u);
			}

			if (mound)
			{
				renderer.submit(&mound->mesh, base, base, -1.0f, structures::draw_flag_no_shadow);
			}
		}

		if (ghosting && mound && shapes[ghost_kind])
		{
			const auto base{ mathematics.translation(ghost) };
			const auto sprout{ mathematics.multiply(mathematics.scaling({ 0.3f, 0.3f, 0.3f }), mathematics.translation(ghost)) };

			renderer.submit(&mound->mesh, base, base, static_cast<std::float_t>(building.ghost_valid), structures::draw_flag_no_shadow);
			renderer.submit(&shapes[ghost_kind]->mesh, sprout, sprout, static_cast<std::float_t>(building.ghost_valid), structures::draw_flag_no_shadow);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t farming_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
