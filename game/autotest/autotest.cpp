
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	autotest_c autotest;

	void autotest_c::update(std::float_t delta, std::uint64_t frame)
	{
		platform.simulate(structures::bind_forward, false);
		platform.simulate(structures::bind_sprint, false);
		platform.simulate(structures::bind_jump, false);
		platform.input.down[VK_LBUTTON] = false;
		platform.input.down[VK_RBUTTON] = false;
		platform.simulate(structures::bind_use, false);
		platform.simulate(structures::bind_reload, false);
		platform.input.mouse_delta = {};

		frames++;

		if (phase == structures::autotest_walk)
		{
			walk(frame);
		}

		else if (phase == structures::autotest_gather)
		{
			gather(frame, structures::node_tree);
		}

		else if (phase == structures::autotest_build)
		{
			build(frame);
		}

		else if (phase == structures::autotest_pluck)
		{
			gather(frame, structures::node_hemp);
		}

		else if (phase == structures::autotest_plant)
		{
			plant(frame);
		}

		else if (phase == structures::autotest_shoot)
		{
			shoot(frame);
		}

		else if (phase == structures::autotest_die)
		{
			die();
		}

		else if (phase == structures::autotest_raid)
		{
			raid(frame);
		}

		else if (phase == structures::autotest_ride)
		{
			ride();
		}

		player.update(delta, true);

		farming.update(delta, true);

		harvest.update(delta, true);

		combat.update(delta, true);

		building.update(delta, true);

		weapons.update(delta, true);

		if (frame % 60u == 0u)
		{
			report(frame);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::walk(std::uint64_t frame)
	{
		platform.simulate(structures::bind_forward, true);
		platform.simulate(structures::bind_sprint, (frame / 120u) % 2u == 1u);
		platform.simulate(structures::bind_jump, frame % 150u > 140u);
		platform.input.mouse_delta = { (frame / 200u) % 2u ? 3.0f : -2.0f, 0.0f };

		if (frames == 330u)
		{
			survival.swap(inventory_slots, inventory_slots + 1u);
		}

		if (frames >= 600u)
		{
			advance(options_raid ? structures::autotest_raid : structures::autotest_gather);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::raid(std::uint64_t frame)
	{
		auto best{ -1 };
		auto nearest{ 5000.0f };

		for (auto index{ 0 }; index < static_cast<std::int32_t>(loot.bags.size()); index++)
		{
			if (loot.bags[index].active && mathematics.distance(loot.bags[index].position, player.state.position) < nearest)
			{
				best = index;
				nearest = mathematics.distance(loot.bags[index].position, player.state.position);
			}
		}

		if (best >= 0)
		{
			const auto& bag{ loot.bags[best] };
			const auto chest{ bag.position + mathematics.flat_forward(bag.yaw) * -0.7f + structures::vec3_s{ 0.0f, 0.25f, 0.0f } };
			const auto offset{ chest - player.eye };

			player.yaw = std::atan2(offset.x, offset.z);
			player.pitch = std::atan2(offset.y, mathematics.length(structures::vec3_s{ offset.x, 0.0f, offset.z }));

			platform.simulate(structures::bind_forward, nearest > 2.2f);

			if (bag.sleeper)
			{
				survival.active_slot = 2u;

				platform.input.down[VK_LBUTTON] = nearest < 12.0f && player.sequence % 20u < 2u;
				platform.simulate(structures::bind_reload, weapons.jammed && frame % 30u < 3u);
			}

			else if (nearest < 2.6f && frames % 60u == 0u)
			{
				client.act(structures::act_loot, bag.position);
			}

			if (frames % 120u == 0u)
			{
				logger.write("autotest: raid target %s at %.1f m, sleeper %u, items %u, hits %u, my items %u", bag.name, nearest, bag.sleeper, bag.items, client.hits_confirmed, static_cast<std::uint32_t>(std::count_if(std::begin(survival.slots), std::end(survival.slots), [](const structures::item_stack_s& slot) { return slot.item != structures::item_none; })));
			}
		}

		settled = best < 0 ? settled + 1u : 0u;

		if (frames > 5000u || (settled > 180u && frames > 600u))
		{
			logger.write("autotest: raid finished after %u frames (bags left %zd, my items %u, guns %u)", frames, std::count_if(loot.bags.begin(), loot.bags.end(), [](const structures::loot_bag_s& bag) { return bag.active; }), static_cast<std::uint32_t>(std::count_if(std::begin(survival.slots), std::end(survival.slots), [](const structures::item_stack_s& slot) { return slot.item != structures::item_none; })), static_cast<std::uint32_t>(std::count_if(std::begin(survival.slots), std::end(survival.slots), [](const structures::item_stack_s& slot) { return item_definitions[slot.item].weapon != structures::weapon_none; })));

			advance(structures::autotest_done);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::ride()
	{
		platform.simulate(structures::bind_forward, frames > 1500u && frames < 1530u);
		platform.simulate(structures::bind_jump, frames == 2100u);

		if (frames % 120u == 0u)
		{
			logger.write("autotest: ride frame %u clock %.2f platform %u flags %u local %.3f %.3f %.3f pos %.1f %.1f %.1f | train speed %.2f | worst miss %.4f m (%u of %u) correction %.3f m | remotes %zu", frames, client.server_clock, player.state.platform, player.state.flags, player.state.local.x, player.state.local.y, player.state.local.z, player.state.position.x, player.state.position.y, player.state.position.z, train.speed, client.worst_miss, client.misses, client.reconciles, mathematics.length(client.error), client.remotes.size());
		}

		for (const auto& remote : client.remotes)
		{
			if (frames % 240u == 0u && remote.count && remote.actor >= 0)
			{
				const auto& sample{ remote.samples[(remote.count - 1u) % std::size(remote.samples)] };
				const auto seat{ mathematics.transform_point(actors.list[remote.actor].position, mathematics.inverse(train.pose(client.server_clock, 1u))) };

				logger.write("autotest: ride sees %s flags %u platform %u local %.2f %.2f %.2f | drawn at %.1f %.1f %.1f which is %.3f %.3f %.3f on the wagon", remote.name, sample.flags, sample.platform, sample.local.x, sample.local.y, sample.local.z, actors.list[remote.actor].position.x, actors.list[remote.actor].position.y, actors.list[remote.actor].position.z, seat.x, seat.y, seat.z);
			}
		}

		if (frames > 3000u)
		{
			advance(structures::autotest_done);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::gather(std::uint64_t frame, std::uint32_t kind)
	{
		const auto plucking{ kind != structures::node_tree };

		if (frames % 240u == 0u)
		{
			if (target >= 0 && mathematics.distance(player.state.position, anchor) < 0.2f && swinging_before == false)
			{
				skipped.push_back(target);

				target = -1;
			}

			anchor = player.state.position;
			swinging_before = harvest.swinging || platform.held(structures::bind_use);
		}

		if (target < 0 || harvest.nodes[target].depleted || harvest.nodes[target].kind != kind)
		{
			target = nearest_node(kind);
		}

		if (target >= 0)
		{
			const auto offset{ harvest.nodes[target].position - player.state.position };
			const auto distance{ mathematics.length(structures::vec3_s{ offset.x, 0.0f, offset.z }) };

			if (frames % 300u == 0u)
			{
				const auto forward{ mathematics.forward_from_angles(player.yaw, player.pitch) };
				const auto probe{ world.trace(player.eye, player.eye + forward * 2.0f, { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };

				logger.write("autotest: target %d kind %u at %.2f m (dy %.2f) swinging %d | probe hit %d brush %d fraction %.2f node %d", target, harvest.nodes[target].kind, distance, offset.y, harvest.swinging ? 1 : 0, probe.hit ? 1 : 0, probe.brush, probe.fraction, probe.hit && harvest.by_brush.count(probe.brush) ? static_cast<std::int32_t>(harvest.by_brush[probe.brush]) : -1);
			}

			player.yaw = std::atan2(offset.x, offset.z);
			player.pitch = plucking ? -std::atan2(player_eye_height - 0.4f, std::max(distance, 0.3f)) : -0.15f;

			survival.active_slot = 3u;

			platform.simulate(structures::bind_forward, distance > (plucking ? 1.0f : 1.25f));
			platform.input.down[VK_LBUTTON] = distance <= 1.7f && plucking == false;
			platform.simulate(structures::bind_use, plucking && distance <= 1.6f && frame % 20u < 2u);
		}

		if (plucking == false && (survival.count(structures::item_wood) >= piece_definitions[structures::piece_foundation].cost.amount || frames > 9000u))
		{
			advance(structures::autotest_build);
		}

		else if (plucking && ((survival.count(structures::item_cloth) >= 10u && survival.count(structures::item_hemp_seeds) > 0u) || frames > 3000u))
		{
			advance(structures::autotest_plant);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::plant(std::uint64_t frame)
	{
		if (frames == 1u)
		{
			built = static_cast<std::uint32_t>(farming.crops.size());
		}

		for (auto slot{ 0u }; slot < hotbar_slots; slot++)
		{
			survival.active_slot = survival.slots[inventory_slots + slot].item == structures::item_hemp_seeds ? slot : survival.active_slot;
		}

		player.pitch = -0.75f;
		player.yaw += frames % 90u == 0u ? 0.9f : 0.0f;

		platform.input.pressed[VK_LBUTTON] = frames > 30u && frame % 45u == 0u;

		if (farming.crops.size() > built || frames > 1500u)
		{
			logger.write("autotest: plant %s (%zu crops, seeds %u, hours %.2f)", farming.crops.size() > built ? "done" : "failed", farming.crops.size(), survival.count(structures::item_hemp_seeds), atmosphere.hours);

			advance(structures::autotest_shoot);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::build(std::uint64_t frame)
	{
		if (frames == 1u)
		{
			built = static_cast<std::uint32_t>(building.placed.size());
		}

		survival.active_slot = 4u;
		building.selected = structures::piece_foundation;

		player.pitch = -0.55f;
		player.yaw += frames % 120u == 0u ? 0.7f : 0.0f;

		platform.input.down[VK_LBUTTON] = frames > 30u && frame % 60u < 2u;
		platform.input.pressed[VK_LBUTTON] = frames > 30u && frame % 60u == 0u;

		if (frames % 60u == 30u)
		{
			logger.write("autotest: preview active %d valid %d piece %u at %.1f %.1f %.1f", building.preview.active ? 1 : 0, building.preview.valid ? 1 : 0, building.preview.piece, building.preview.position.x, building.preview.position.y, building.preview.position.z);
		}

		if (building.placed.size() > built || frames > 1500u)
		{
			logger.write("autotest: build %s (%zu structures, wood %u)", building.placed.size() > built ? "placed" : "failed", building.placed.size(), survival.count(structures::item_wood));

			advance(structures::autotest_pluck);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::shoot(std::uint64_t frame)
	{
		auto best{ -1 };
		auto nearest{ 1000.0f };

		for (const auto& remote : client.remotes)
		{
			if (remote.actor >= 0 && remote.actor < static_cast<std::int32_t>(actors.list.size()) && remote.health > 0.0f && mathematics.distance(actors.list[remote.actor].position, player.eye) < nearest)
			{
				best = remote.actor;
				nearest = mathematics.distance(actors.list[remote.actor].position, player.eye);
			}
		}

		if (best >= 0)
		{
			const auto offset{ actors.list[best].position + structures::vec3_s{ 0.0f, 1.2f, 0.0f } - player.eye };

			player.yaw = std::atan2(offset.x, offset.z);
			player.pitch = std::atan2(offset.y, mathematics.length(structures::vec3_s{ offset.x, 0.0f, offset.z }));
		}

		survival.active_slot = 2u;

		platform.input.down[VK_RBUTTON] = true;
		platform.input.down[VK_LBUTTON] = frames > 60u && best >= 0 && player.sequence % 30u < 2u;
		platform.simulate(structures::bind_reload, weapons.jammed && frame % 30u < 3u);

		if (frames > 1500u)
		{
			advance(structures::autotest_die);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::die()
	{
		if (frames == 10u)
		{
			client.say("/kill");
		}

		if (frames == 400u)
		{
			const auto active{ std::count_if(loot.bags.begin(), loot.bags.end(), [](const structures::loot_bag_s& bag) { return bag.active; }) };
			const auto body{ std::find_if(loot.bags.begin(), loot.bags.end(), [](const structures::loot_bag_s& bag) { return bag.active; }) };

			logger.write("autotest: dead %d, bags %zd, first bag %s items %u actor %d at %.1f %.1f %.1f (player at %.1f %.1f %.1f), inventory items %u", survival.vitals.dead ? 1 : 0, active, body != loot.bags.end() ? body->name : "-", body != loot.bags.end() ? body->items : 0u, body != loot.bags.end() ? body->actor : -1, body != loot.bags.end() ? body->position.x : 0.0f, body != loot.bags.end() ? body->position.y : 0.0f, body != loot.bags.end() ? body->position.z : 0.0f, player.state.position.x, player.state.position.y, player.state.position.z, static_cast<std::uint32_t>(std::count_if(std::begin(survival.slots), std::end(survival.slots), [](const structures::item_stack_s& slot) { return slot.item != structures::item_none; })));
		}

		if (frames > 420u && survival.vitals.dead && frames % 60u == 0u)
		{
			client.request_respawn();
		}

		if (frames == 900u)
		{
			logger.write("autotest: after respawn dead %d at %.1f %.1f %.1f, inventory items %u", survival.vitals.dead ? 1 : 0, player.state.position.x, player.state.position.y, player.state.position.z, static_cast<std::uint32_t>(std::count_if(std::begin(survival.slots), std::end(survival.slots), [](const structures::item_stack_s& slot) { return slot.item != structures::item_none; })));

			advance(structures::autotest_done);
		}
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::report(std::uint64_t frame)
	{
		char line[512]{};
		char part[64]{};

		for (auto index{ 0u }; index < total_slots; index++)
		{
			if (survival.slots[index].item)
			{
				std::snprintf(part, sizeof(part), " %s x%u", item_definitions[survival.slots[index].item].name, survival.slots[index].amount);
				std::strncat(line, part, sizeof(line) - std::strlen(line) - 1u);
			}
		}

		logger.write("autotest: frame %llu phase %u pos %.0f %.0f %.0f | health %.0f food %.0f water %.0f | structures %zu | hits %u damage %u heard %u |%s", frame, phase, player.state.position.x, player.state.position.y, player.state.position.z, survival.vitals.health, survival.vitals.calories, survival.vitals.hydration, building.placed.size(), client.hits_confirmed, client.damage_dealt, client.shots_heard, line);
	}
	/*
	//=====================================================================================
	*/
	void autotest_c::advance(std::uint32_t next)
	{
		logger.write("autotest: phase %u -> %u after %u frames", phase, next, frames);

		phase = next;
		frames = 0u;
		target = -1;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t autotest_c::nearest_node(std::uint32_t kind)
	{
		auto best{ -1 };
		auto nearest{ 1000.0f };

		for (auto index{ 0 }; index < static_cast<std::int32_t>(harvest.nodes.size()); index++)
		{
			if (harvest.nodes[index].kind == kind && harvest.nodes[index].depleted == false && mathematics.distance(harvest.nodes[index].position, player.state.position) < nearest && std::find(skipped.begin(), skipped.end(), index) == skipped.end())
			{
				best = index;
				nearest = mathematics.distance(harvest.nodes[index].position, player.state.position);
			}
		}

		return best;
	}
}

//=====================================================================================
