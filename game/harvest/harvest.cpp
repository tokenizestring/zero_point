
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	harvest_c harvest;

	void harvest_c::clear()
	{
		nodes.clear();
		changed.clear();
		waiting.clear();
		by_brush.clear();

		tool = {};
		swing_timer = 0.0f;
		swinging = false;
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::create_models()
	{
		models.clone("boulder_01", "node_metal", { 1.3f, 0.95f, 0.78f }, 0.35f);
		models.clone("boulder_01", "node_sulfur", { 1.55f, 1.35f, 0.55f }, 0.0f);
		models.clone("boulder_01_far", "node_metal_far", { 1.3f, 0.95f, 0.78f }, 0.35f);
		models.clone("boulder_01_far", "node_sulfur_far", { 1.55f, 1.35f, 0.55f }, 0.0f);

		if (models.existing("hemp_plant") == nullptr)
		{
			create_hemp("hemp_plant", 1.0f);
			create_hemp("hemp_plant_far", 0.3f);
		}

		if (models.existing("berry_bush") == nullptr)
		{
			create_berry_bush("berry_bush", 7u, 0.8f);
			create_berry_bush("berry_bush_far", 5u, 0.28f);
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::create_hemp(const char* name, std::float_t keep)
	{
		const auto source{ models.find("nettle_plant") };
		const auto tall_a{ source ? models.part(*source, "nettle_plant_tall_a_LOD0") : nullptr };
		const auto tall_b{ source ? models.part(*source, "nettle_plant_tall_b_LOD0") : nullptr };

		if (tall_a && tall_b)
		{
			const auto leaf{ models.variant(source->vertices[source->indices[tall_a->first_index]].material, { 1.08f, 1.18f, 0.72f }, 0.0f) };
			const auto center_a{ (tall_a->bounds_min + tall_a->bounds_max) * 0.5f };
			const auto center_b{ (tall_b->bounds_min + tall_b->bounds_max) * 0.5f };

			if (const auto model{ models.create(name) }; model)
			{
				models.begin_part(*model, "hemp_leaves");
				models.append(*model, *source, *tall_a, mathematics.multiply(mathematics.multiply(mathematics.translation({ -center_a.x, -tall_a->bounds_min.y, -center_a.z }), mathematics.scaling({ 6.5f, 6.5f, 6.5f })), mathematics.rotation_y(0.3f)), leaf, keep, 11u);
				models.append(*model, *source, *tall_b, mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation({ -center_b.x, -tall_b->bounds_min.y, -center_b.z }), mathematics.scaling({ 5.8f, 5.8f, 5.8f })), mathematics.rotation_y(2.1f)), mathematics.translation({ 0.16f, 0.0f, -0.1f })), leaf, keep, 23u);
				models.append(*model, *source, *tall_a, mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation({ -center_a.x, -tall_a->bounds_min.y, -center_a.z }), mathematics.scaling({ 4.6f, 4.6f, 4.6f })), mathematics.rotation_y(4.0f)), mathematics.translation({ -0.14f, 0.0f, 0.12f })), leaf, keep, 37u);
				models.seal(*model);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::create_berry_bush(const char* name, std::uint32_t branches, std::float_t keep)
	{
		const auto source{ models.find("shrub_04") };

		if (source && source->parts.size())
		{
			const auto& branch{ source->parts[0] };
			const auto leaf{ models.variant(source->vertices[source->indices[branch.first_index]].material, { 0.92f, 1.0f, 0.86f }, 0.0f) };

			if (const auto model{ models.create(name) }; model)
			{
				auto bush_seed{ 0x2545F491u };

				const auto next = [&]()
					{
						bush_seed ^= bush_seed << 13u;
						bush_seed ^= bush_seed >> 17u;
						bush_seed ^= bush_seed << 5u;

						return static_cast<std::float_t>(bush_seed & 0xFFFFFFu) / 16777216.0f;
					};

				models.begin_part(*model, "berry_leaves");

				for (auto index{ 0u }; index < branches; index++)
				{
					const auto azimuth{ (static_cast<std::float_t>(index) + next() * 0.6f) / static_cast<std::float_t>(branches) * two_pi };
					const auto elevation{ 0.45f + next() * 0.6f };
					const auto scale{ 2.1f + next() * 0.7f };
					const structures::vec3_s direction{ std::cos(azimuth) * std::cos(elevation), std::sin(elevation), std::sin(azimuth) * std::cos(elevation) };
					const structures::vec3_s side{ -std::sin(azimuth), 0.0f, std::cos(azimuth) };
					const auto up{ mathematics.cross(side, direction) };

					models.append(*model, *source, branch, mathematics.basis(direction * scale, up * scale, side * scale, { std::cos(azimuth) * 0.08f, next() * 0.12f, std::sin(azimuth) * 0.08f }), leaf, keep, index * 7919u);
				}

				const auto leaf_vertices{ static_cast<std::uint32_t>(model->vertices.size()) };

				models.begin_part(*model, "berry_fruit");

				for (auto cluster{ 0u }; cluster < 16u; cluster++)
				{
					const auto anchor{ model->vertices[static_cast<std::uint32_t>(next() * static_cast<std::float_t>(leaf_vertices - 1u))] };

					for (auto berry{ 0u }; berry < 3u; berry++)
					{
						const structures::vec3_s jitter{ (next() - 0.5f) * 0.1f, (next() - 0.5f) * 0.08f, (next() - 0.5f) * 0.1f };

						models.sphere(*model, anchor.position + anchor.normal * 0.03f + jitter, 0.032f + next() * 0.014f, structures::material_berry);
					}
				}

				models.seal(*model);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t harvest_c::add(std::uint32_t kind, structures::vec3_s position, std::float_t radius, std::uint32_t instance, std::int32_t brush)
	{
		const auto scale{ instance < foliage.instances.size() ? foliage.instances[instance].scale : 1.0f };
		const auto contents{ brush >= 0 && static_cast<std::size_t>(brush) < world.brushes.size() ? world.brushes[brush].contents : 0u };

		nodes.push_back({ position, node_health[kind], radius, kind, instance, brush, false, 0.0f, scale, contents });

		if (brush >= 0)
		{
			by_brush[brush] = static_cast<std::uint32_t>(nodes.size() - 1u);
		}

		return static_cast<std::uint32_t>(nodes.size() - 1u);
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::update(std::float_t delta, bool input_enabled)
	{
		if (client.connected() == false)
		{
			respawn(delta);
		}

		if (survival.vitals.dead == false && input_enabled && swinging == false)
		{
			const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };

			char text[96]{};

			auto seat{ 0u };
			auto gap{ 0.0f };

			if (player.state.flags & structures::movement_seated)
			{
				if (const auto vehicle{ vehicles.find(player.state.vehicle) }; vehicle)
				{
					std::snprintf(text, sizeof(text), "%s   [E] get out", vehicle_kinds[vehicle->kind].name);

					hud.set_prompt(text);
				}
			}

			else if (const auto vehicle{ vehicles.reach(player.eye, forward, seat) }; vehicle >= 0)
			{
				const auto mode{ vehicle_kinds[vehicles.list[vehicle].kind].mode };

				std::snprintf(text, sizeof(text), "%s   [E] %s", vehicle_kinds[vehicles.list[vehicle].kind].name, seat == 0u && mode == structures::vehicle_mode_wheels ? "drive" : (seat == 0u && mode == structures::vehicle_mode_rotor ? "fly" : "ride"));

				hud.set_prompt(text);
			}

			else if (const auto horse{ fauna.ray(player.eye, forward, vehicle_enter_reach, gap) }; horse >= 0 && fauna.animals[horse].alive && fauna.animals[horse].species == structures::species_horse)
			{
				hud.set_prompt("Wild horse   [E] ride");
			}

			else if (const auto target{ pickup_target(player.eye, forward) }; target >= 0)
			{
				const auto kind{ nodes[target].kind };

				if (lootable(kind) && nodes[target].depleted)
				{
					std::snprintf(text, sizeof(text), "%s (empty)", node_names[kind]);
				}

				else
				{
					std::snprintf(text, sizeof(text), "%s %s   [E]", lootable(kind) ? "Open" : "Pick up", node_names[kind]);
				}

				hud.set_prompt(text);
			}

			else if (const auto carcass{ fauna.carcass(player.eye, forward) }; carcass >= 0)
			{
				std::snprintf(text, sizeof(text), "%s carcass   [LMB] carve", species_table[fauna.animals[carcass].species].name);

				hud.set_prompt(text);
			}

			else
			{
				const auto result{ world.trace(player.eye, player.eye + forward * 2.4f, { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };

				if (const auto found{ result.hit ? by_brush.find(result.brush) : by_brush.end() }; found != by_brush.end() && nodes[found->second].depleted == false)
				{
					hud.set_prompt(node_names[nodes[found->second].kind]);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::tick(const structures::usercmd_s& command, bool usable)
	{
		step(tool, survival, command, usable);

		swinging = (tool.flags & structures::tool_flag_swinging) != 0u;
		swing_timer = tool.timer;
		swing_length = tool.length;

		const auto authoritative{ client.connected() == false };
		const auto forward{ mathematics.forward_from_angles(command.yaw, command.pitch) };
		const auto slot{ std::min(command.weapon, hotbar_slots - 1u) };

		if (tool.events & structures::tool_event_whoosh)
		{
			mixer.play_2d(structures::sound_swing, 0.35f, 0.85f + random() * 0.3f);
		}

		if (tool.events & structures::tool_event_strike)
		{
			auto& held{ survival.slots[inventory_slots + slot] };

			const auto& definition{ item_definitions[held.item] };

			if (authoritative && combat.melee(player.eye, forward, std::max(definition.reach, 1.6f) + 0.3f, std::max(definition.damage, 5.0f)))
			{
				held.condition -= held.item && held.item != structures::item_rock ? 0.006f : 0.0f;
			}

			else if (authoritative && fauna.melee(survival, player.eye, forward, std::max(definition.reach, 1.6f) + 0.3f, std::max(definition.damage, 5.0f), struck_point) > 0u)
			{
				particles.impact(structures::surface_flesh, struck_point, forward * -1.0f);

				marks.bleed(struck_point, forward);

				mixer.play(structures::sound_hit_flesh, struck_point, 1.0f, 0.9f + random() * 0.2f);

				combat.hit_marker = 1.0f;

				held.condition -= held.item && held.item != structures::item_rock ? 0.004f : 0.0f;
			}

			else
			{
				strike(survival, slot, player.eye, forward, authoritative);
			}
		}

		if (tool.events & structures::tool_event_eat)
		{
			const auto name{ item_definitions[survival.slots[inventory_slots + slot].item].name };

			if (authoritative && survival.consume(inventory_slots + slot))
			{
				survival.notify(name, -1);
			}

			mixer.play_2d(structures::sound_pickup, 0.4f, 0.8f);
		}

		if (tool.events & structures::tool_event_use)
		{
			interact(survival, player.eye, forward, authoritative);
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::step(structures::tool_state_s& state, survival_c& owner, const structures::usercmd_s& command, bool usable)
	{
		const auto dt{ std::clamp(command.delta, 0.0f, 0.1f) };
		const auto slot{ std::min(command.weapon, hotbar_slots - 1u) };
		const auto& definition{ item_definitions[owner.slots[inventory_slots + slot].item] };
		const auto fire_down{ (command.buttons & structures::button_fire) != 0u };
		const auto fire_pressed{ fire_down && (state.flags & structures::tool_flag_fire_held) == 0u };
		const auto use_pressed{ (command.buttons & structures::button_use) != 0u && (state.flags & structures::tool_flag_use_held) == 0u };
		const auto edible{ definition.category == structures::item_category_food || definition.category == structures::item_category_medical };
		const auto swingable{ definition.category != structures::item_category_construction && definition.category != structures::item_category_ammunition && definition.category != structures::item_category_farming && definition.weapon == structures::weapon_none && edible == false };

		state.events = 0u;

		if (slot != state.slot)
		{
			state.slot = slot;
			state.flags &= ~(structures::tool_flag_swinging | structures::tool_flag_whoosh | structures::tool_flag_struck);
		}

		if (usable && (state.flags & structures::tool_flag_swinging) == 0u)
		{
			state.events |= use_pressed ? structures::tool_event_use : 0u;

			if (fire_pressed && edible)
			{
				state.events |= structures::tool_event_eat;
			}

			else if (fire_down && swingable)
			{
				state.flags = (state.flags | structures::tool_flag_swinging) & ~(structures::tool_flag_whoosh | structures::tool_flag_struck);
				state.timer = 0.0f;
				state.length = std::max(definition.swing_time, 0.45f);
				state.events |= structures::tool_event_swing;
			}
		}

		if (state.flags & structures::tool_flag_swinging)
		{
			state.timer += dt;

			if ((state.flags & structures::tool_flag_whoosh) == 0u && state.timer >= state.length * 0.24f)
			{
				state.flags |= structures::tool_flag_whoosh;
				state.events |= structures::tool_event_whoosh;
			}

			if ((state.flags & structures::tool_flag_struck) == 0u && state.timer >= state.length * 0.42f)
			{
				state.flags |= structures::tool_flag_struck;
				state.events |= usable ? structures::tool_event_strike : 0u;
			}

			state.flags = state.timer >= state.length ? (state.flags & ~structures::tool_flag_swinging) : state.flags;
		}

		state.flags = fire_down ? (state.flags | structures::tool_flag_fire_held) : (state.flags & ~structures::tool_flag_fire_held);
		state.flags = (command.buttons & structures::button_use) ? (state.flags | structures::tool_flag_use_held) : (state.flags & ~structures::tool_flag_use_held);
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::respawn(std::float_t delta)
	{
		auto slot{ 0u };

		while (slot < waiting.size())
		{
			const auto index{ waiting[slot] };

			if (nodes[index].depleted)
			{
				nodes[index].timer -= delta;
			}

			if (nodes[index].depleted && nodes[index].timer <= 0.0f)
			{
				restore(index);
			}

			if (nodes[index].depleted)
			{
				slot++;
			}

			else
			{
				waiting[slot] = waiting.back();

				waiting.pop_back();
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t harvest_c::strike(survival_c& owner, std::uint32_t slot, structures::vec3_s eye, structures::vec3_s forward, bool authoritative)
	{
		auto& held{ owner.slots[inventory_slots + slot] };

		const auto& definition{ item_definitions[held.item] };
		const auto reach{ std::max(definition.reach, 1.6f) };
		const auto result{ world.trace(eye, eye + forward * reach, { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };
		const auto found{ result.hit ? by_brush.find(result.brush) : by_brush.end() };
		const auto index{ found != by_brush.end() ? static_cast<std::int32_t>(found->second) : -1 };
		const auto kind{ index >= 0 ? nodes[index].kind : static_cast<std::uint32_t>(structures::node_kind_count) };
		const auto audible{ owner.owner < 0 };

		auto touched{ -1 };

		if (index >= 0 && nodes[index].depleted == false && lootable(kind) == false)
		{
			auto& node{ nodes[index] };

			touched = index;
			struck_point = result.end;
			struck_sound = kind <= structures::node_dead_tree ? structures::sound_hit_wood : (kind == structures::node_barrel ? structures::sound_hit_metal : structures::sound_hit_rock);

			if (audible)
			{
				particles.impact(kind <= structures::node_dead_tree ? structures::surface_wood : (kind == structures::node_barrel ? structures::surface_metal : structures::surface_rock), result.end - forward * 0.05f, result.normal);

				mixer.play(struck_sound, result.end, 1.0f, 0.9f + random() * 0.2f);

				if (kind <= structures::node_dead_tree && random() < 0.4f)
				{
					mixer.play(structures::sound_chop, result.end, 0.6f, 0.9f + random() * 0.2f);
				}
			}

			if (authoritative)
			{
				const auto wood{ static_cast<std::uint32_t>(std::round(20.0f * definition.wood_yield * (node.kind == structures::node_dead_tree ? 0.7f : 1.0f))) };
				const auto stone{ static_cast<std::uint32_t>(std::round(16.0f * definition.stone_yield)) };

				if (node.kind == structures::node_barrel)
				{
					node.health -= std::max(definition.damage, 5.0f);

					if (node.health <= 0.0f)
					{
						roll(owner, node_loot[structures::node_barrel]);
					}
				}

				else if ((node.kind == structures::node_tree || node.kind == structures::node_dead_tree) && wood)
				{
					owner.give(structures::item_wood, wood, true);

					node.health -= static_cast<std::float_t>(wood);
				}

				else if (node.kind == structures::node_stone && stone)
				{
					owner.give(structures::item_stone, stone, true);

					node.health -= static_cast<std::float_t>(stone);
				}

				else if ((node.kind == structures::node_metal || node.kind == structures::node_sulfur) && stone)
				{
					owner.give(node.kind == structures::node_metal ? structures::item_metal_ore : structures::item_sulfur_ore, std::max(1u, stone * 2u / 3u), true);
					owner.give(structures::item_stone, std::max(1u, stone / 3u), false);

					node.health -= static_cast<std::float_t>(stone);
				}

				else
				{
					owner.notify("You need a better tool", 0);
				}

				if (node.health <= 0.0f && node.depleted == false)
				{
					node.fall = std::atan2(node.position.x - owner.position.x, node.position.z - owner.position.z);

					if (audible)
					{
						topple(static_cast<std::uint32_t>(index));
					}

					deplete(static_cast<std::uint32_t>(index));
				}

				held.condition -= held.item && held.item != structures::item_rock ? 0.012f : 0.0f;
			}

			else if (kind == structures::node_stone || kind == structures::node_metal || kind == structures::node_sulfur)
			{
				node.health -= std::round(16.0f * definition.stone_yield);
			}

			if ((kind == structures::node_stone || kind == structures::node_metal || kind == structures::node_sulfur) && node.depleted == false && node.instance < foliage.instances.size())
			{
				foliage.instances[node.instance].scale = node.scale * (0.7f + 0.3f * mathematics.saturate(node.health / node_health[kind]));
			}
		}

		else if (result.hit && audible)
		{
			particles.impact(result.surface, result.end - forward * 0.05f, result.normal);

			mixer.play(result.surface == structures::surface_metal ? structures::sound_hit_metal : (result.surface == structures::surface_wood ? structures::sound_hit_wood : (result.surface == structures::surface_concrete || result.surface == structures::surface_rock ? structures::sound_hit_rock : structures::sound_hit_soft)), result.end, 0.7f, 0.9f + random() * 0.2f);
		}

		if (authoritative && index < 0 && result.hit)
		{
			if (const auto found_piece{ building.by_brush.find(result.brush) }; found_piece != building.by_brush.end())
			{
				if (held.item == structures::item_hammer)
				{
					if (owner.count(structures::item_wood) >= hammer_repair_wood && building.repair(found_piece->second, hammer_repair))
					{
						owner.take(structures::item_wood, hammer_repair_wood);
					}
				}

				else
				{
					building.damage(result.brush, std::max(definition.damage, 5.0f), false);
				}
			}
		}

		if (authoritative && held.item && held.condition <= 0.0f)
		{
			owner.notify("Your tool broke", 0);

			held = {};
		}

		return touched;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t harvest_c::interact(survival_c& owner, structures::vec3_s eye, structures::vec3_s forward, bool authoritative)
	{
		const auto target{ pickup_target(eye, forward) };

		if (target >= 0 && nodes[target].depleted == false)
		{
			const auto kind{ nodes[target].kind };

			if (owner.owner < 0)
			{
				mixer.play(lootable(kind) ? structures::sound_container : structures::sound_pickup, nodes[target].position, lootable(kind) ? 0.8f : 0.55f, 0.95f + random() * 0.1f);
			}

			if (authoritative && lootable(kind))
			{
				roll(owner, node_loot[kind]);

				if (owner.owner < 0)
				{
					story.searched(nodes[target].position);
				}

				deplete(static_cast<std::uint32_t>(target));
			}

			else if (authoritative)
			{
				const auto extra{ static_cast<std::uint32_t>(random() * 1.99f) };

				if (kind == structures::node_hemp)
				{
					owner.give(structures::item_cloth, 10u, true);

					if (extra)
					{
						owner.give(structures::item_hemp_seeds, 1u + static_cast<std::uint32_t>(random() * 1.99f), true);
					}
				}

				else
				{
					owner.give(kind == structures::node_berry ? structures::item_berries : (kind == structures::node_potato ? structures::item_potato : (kind == structures::node_corn ? structures::item_corn : structures::item_pumpkin)), kind == structures::node_berry ? 3u + extra * 2u : (kind == structures::node_pumpkin ? 1u : 2u + extra), true);
				}

				deplete(static_cast<std::uint32_t>(target));
			}
		}

		return target;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t harvest_c::pickup_target(structures::vec3_s eye, structures::vec3_s forward)
	{
		auto best{ -1 };
		auto best_distance{ FLT_MAX };

		for (auto index{ 0u }; index < nodes.size(); index++)
		{
			const auto& node{ nodes[index] };

			if ((node.depleted == false && plucked(node.kind)) || lootable(node.kind))
			{
				const auto offset{ node.position + structures::vec3_s{ 0.0f, lootable(node.kind) ? 0.2f : 0.4f, 0.0f } - eye };
				const auto along{ mathematics.dot(offset, forward) };
				const auto away{ mathematics.length(offset - forward * along) };

				if (along > 0.0f && along < interact_range && away < node.radius + 0.25f && away < best_distance)
				{
					best = static_cast<std::int32_t>(index);
					best_distance = away;
				}
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	bool harvest_c::lootable(std::uint32_t kind)
	{
		return kind >= structures::node_toolbox && kind <= structures::node_medical;
	}
	/*
	//=====================================================================================
	*/
	bool harvest_c::plucked(std::uint32_t kind)
	{
		return kind == structures::node_hemp || kind == structures::node_berry || kind == structures::node_potato || kind == structures::node_corn || kind == structures::node_pumpkin;
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::deplete(std::uint32_t index)
	{
		if (index < nodes.size())
		{
			auto& node{ nodes[index] };

			if (node.depleted == false)
			{
				waiting.push_back(index);
			}

			node.depleted = true;
			node.timer = node_respawn[node.kind];

			if (lootable(node.kind) == false && node.instance < foliage.instances.size())
			{
				foliage.instances[node.instance].scale = 0.0f;
			}

			if (lootable(node.kind) == false && node.brush >= 0 && static_cast<std::size_t>(node.brush) < world.brushes.size())
			{
				world.brushes[node.brush].contents = 0u;
			}

			changed.push_back(index);
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::topple(std::uint32_t index)
	{
		if (gpu.device && index < nodes.size() && nodes[index].kind <= structures::node_dead_tree && nodes[index].instance < foliage.instances.size() && mathematics.distance(nodes[index].position, renderer.camera.position) < fell_range)
		{
			const auto& node{ nodes[index] };
			const auto& instance{ foliage.instances[node.instance] };
			const auto model{ instance.species < foliage.species.size() ? foliage.species[instance.species].near_model : nullptr };

			if (model && model->mesh.vertex_buffer && instance.scale > 0.0f)
			{
				felled.push_back({ model, instance.position, instance.yaw, instance.scale, node.fall, 0.03f, 0.0f, std::max((model->bounds_max.y - model->bounds_min.y) * instance.scale, 2.0f), 0.0f, false, {} });

				mixer.play(structures::sound_tree_creak, node.position + structures::vec3_s{ 0.0f, 2.5f, 0.0f }, 1.0f, 0.9f + random() * 0.2f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::fell(std::float_t delta)
	{
		for (auto& tree : felled)
		{
			if (tree.landed)
			{
				tree.timer += delta;
			}

			else
			{
				tree.speed += 1.5f * 9.81f / tree.height * std::sin(tree.angle) * delta;
				tree.angle = std::min(tree.angle + tree.speed * delta, fell_rest);

				if (tree.angle >= fell_rest)
				{
					const structures::vec3_s heading{ std::sin(tree.fall), 0.0f, std::cos(tree.fall) };

					tree.landed = true;

					mixer.play(structures::sound_tree_fall, tree.position + heading * (tree.height * 0.6f), 1.0f, 0.9f + random() * 0.15f);

					for (auto puff{ 0u }; puff < 8u; puff++)
					{
						const auto along{ (static_cast<std::float_t>(puff) + 0.5f) / 8.0f };

						particles.emit(structures::particle_dust, tree.position + heading * (tree.height * along) + structures::vec3_s{ 0.0f, 0.3f, 0.0f }, { 0.0f, 0.8f, 0.0f }, 0.8f, 3u, false);
					}
				}
			}
		}

		felled.erase(std::remove_if(felled.begin(), felled.end(), [](const structures::felled_s& tree) { return tree.timer > fell_linger + fell_sink; }), felled.end());
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::submit()
	{
		for (auto& tree : felled)
		{
			const structures::vec3_s axis{ std::cos(tree.fall), 0.0f, -std::sin(tree.fall) };
			const auto sink{ mathematics.saturate((tree.timer - fell_linger) / fell_sink) };
			const auto transform{ mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.scaling({ tree.scale, tree.scale, tree.scale }), mathematics.rotation_y(tree.yaw)), mathematics.rotation(mathematics.quat_axis_angle(axis, tree.angle))), mathematics.translation(tree.position - structures::vec3_s{ 0.0f, sink * 2.5f, 0.0f })) };

			renderer.submit(&tree.model->mesh, transform, tree.previous.m[3][3] != 0.0f ? tree.previous : transform, -1.0f, structures::draw_flag_alpha);

			tree.previous = transform;
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::restore(std::uint32_t index)
	{
		if (index < nodes.size())
		{
			auto& node{ nodes[index] };

			node.depleted = false;
			node.timer = 0.0f;
			node.health = node_health[node.kind];

			if (node.instance < foliage.instances.size())
			{
				foliage.instances[node.instance].scale = node.scale;
			}

			if (node.brush >= 0 && static_cast<std::size_t>(node.brush) < world.brushes.size())
			{
				world.brushes[node.brush].contents = node.contents;
			}

			changed.push_back(index);
		}
	}
	/*
	//=====================================================================================
	*/
	void harvest_c::roll(survival_c& owner, const structures::loot_table_s& table)
	{
		for (auto index{ 0u }; index < table.count; index++)
		{
			const auto& entry{ table.entries[index] };

			if (random() < entry.chance)
			{
				owner.give(entry.item, entry.minimum + static_cast<std::uint32_t>(random() * static_cast<std::float_t>(entry.maximum - entry.minimum + 1u) * 0.999f), true);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t harvest_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
