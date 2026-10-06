
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	hud_c hud;

	bool hud_c::create()
	{
		if (const auto table{ pak.find(item_icon_table) }; table && table->size >= structures::item_count)
		{
			icon_view = pak.create_texture(item_icon_atlas, 0u, false, false);
			icon_table = pak.data(table);
		}

		return true;
	}
	/*
	//=====================================================================================
	*/
	void hud_c::destroy()
	{
		functions::release(icon_view);

		icon_table = nullptr;
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw(std::float_t delta)
	{
		const auto s{ canvas.scale };
		const auto interactive{ survival.inventory_open || keypad_door >= 0 };
		const auto clear{ survival.inventory_open == false && chart.open == false };

		if (interactive)
		{
			kit.begin(delta);
		}

		track(delta);

		draw_wounds();

		if (survival.vitals.dead)
		{
			draw_death(s);
		}

		else if (story.ending)
		{
			draw_ending(s);
		}

		else
		{
			if (weapons.scoped)
			{
				draw_scope(s);
			}

			if (clear)
			{
				draw_crosshair(s);
			}

			if (clear && menu.user.prompts)
			{
				draw_prompt(s);
			}

			if (clear && menu.user.compass)
			{
				draw_compass(s);
			}

			if (clear && menu.user.hints && client.connected() == false)
			{
				draw_goal(s);
			}

			if (client.connected())
			{
				if (menu.user.name_tags)
				{
					draw_names(s);
				}

				if (menu.user.damage_direction)
				{
					draw_hurt(s);
				}

				draw_chat(s);
			}

			if (survival.inventory_open)
			{
				draw_inventory(s);
			}

			else
			{
				draw_vitals(s);
			}

			draw_queue(s);

			draw_notifications(s);

			draw_belt(s);

			if (survival.inventory_open)
			{
				draw_grab(s);
			}

			chart.draw(s);

			if (keypad_door >= 0)
			{
				draw_keypad(s);
			}
		}

		if (interactive)
		{
			kit.end();
		}

		prompt[0] = 0;
	}
	/*
	//=====================================================================================
	*/
	void hud_c::track(std::float_t delta)
	{
		const std::float_t values[3] = { survival.vitals.health, survival.vitals.hydration, survival.vitals.calories };
		const std::float_t maxima[3] = { maximum_health, maximum_hydration, maximum_calories };

		clock += delta;
		death_clock = survival.vitals.dead ? death_clock + delta : 0.0f;
		belt_clock = survival.active_slot != belt_slot ? hud_belt_hold : std::max(belt_clock - delta, 0.0f);
		belt_slot = survival.active_slot;
		belt_glow = mathematics.damp(belt_glow, survival.inventory_open || menu.user.hotbar == 1u || (menu.user.hotbar == 0u && belt_clock > 0.0f) ? 1.0f : 0.0f, hud_fade_speed, delta);

		for (auto vital{ 0u }; vital < 3u; vital++)
		{
			const auto rose{ values[vital] > vital_seen[vital] + hud_vital_step };
			const auto hurt{ vital == 0u && values[vital] < vital_seen[vital] - hud_vital_step };

			vital_clock[vital] = rose || hurt ? hud_vital_hold : std::max(vital_clock[vital] - delta, 0.0f);
			vital_seen[vital] = values[vital];
			vital_glow[vital] = mathematics.damp(vital_glow[vital], menu.user.vitals == 0u || values[vital] < maxima[vital] * hud_vital_low || vital_clock[vital] > 0.0f ? 1.0f : 0.0f, hud_fade_speed, delta);
		}

		vital_glow[3] = mathematics.damp(vital_glow[3], survival.vitals.breath < 0.999f ? 1.0f : 0.0f, hud_fade_speed, delta);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::update_chat(std::float_t delta)
	{
		hurt_timer = std::max(hurt_timer - delta, 0.0f);

		if (chatting)
		{
			auto length{ std::strlen(chat_text) };

			for (auto index{ 0u }; index < platform.input.text_length; index++)
			{
				const auto character{ platform.input.text[index] };

				if (character >= 32 && character < 127 && length + 1u < sizeof(chat_text))
				{
					chat_text[length++] = character;
					chat_text[length] = 0;
				}
			}

			if ((platform.input.pressed[VK_BACK] || platform.input.repeated[VK_BACK]) && length)
			{
				chat_text[length - 1u] = 0;
			}

			if (platform.input.pressed[VK_RETURN] || platform.input.pressed[VK_ESCAPE])
			{
				if (platform.input.pressed[VK_RETURN] && chat_text[0])
				{
					client.say(chat_text);
				}

				chatting = false;
				chat_text[0] = 0;
			}

			platform.input.text_length = 0u;

			std::fill(std::begin(platform.input.pressed), std::end(platform.input.pressed), false);
		}

		else if ((platform.input.pressed[VK_RETURN] || platform.tapped(structures::bind_chat)) && client.connected() && survival.inventory_open == false)
		{
			chatting = true;
			chat_text[0] = 0;

			platform.input.text_length = 0u;
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_wounds()
	{
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const auto weak{ survival.vitals.dead ? 0.0f : mathematics.saturate(1.0f - survival.vitals.health / (maximum_health * 0.3f)) };
		const auto beat{ 0.75f + 0.25f * std::sin(clock * 6.2f) };
		const auto amount{ std::max(std::min(1.0f, survival.vitals.damage_flash), weak * 0.55f * beat) };

		if (amount > 0.01f)
		{
			const auto edge{ functions::rgba(110u, 0u, 0u, static_cast<std::uint32_t>(amount * 130.0f)) };
			const auto none{ functions::rgba(110u, 0u, 0u, 0u) };

			canvas.gradient({ 0.0f, 0.0f, width, height * 0.3f }, edge, none);
			canvas.gradient({ 0.0f, height * 0.7f, width, height * 0.3f }, none, edge);
			canvas.gradient_horizontal({ 0.0f, 0.0f, width * 0.24f, height }, edge, none);
			canvas.gradient_horizontal({ width * 0.76f, 0.0f, width * 0.24f, height }, none, edge);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_crosshair(std::float_t s)
	{
		const structures::vec2_s center{ canvas.screen_width * 0.5f, canvas.screen_height * 0.5f };

		if ((menu.user.crosshair == 2u || (menu.user.crosshair == 1u && weapons.weapon == structures::weapon_none)) && weapons.aim < 0.5f)
		{
			canvas.circle(center, 2.6f * s, functions::rgba(0u, 0u, 0u, 130u));
			canvas.circle(center, 1.5f * s, functions::rgba(240u, 236u, 228u, 225u));
		}

		if (menu.user.hit_markers && combat.hit_marker > 0.01f)
		{
			const auto color{ functions::with_alpha(combat.kill_marker > 0.01f ? kit_danger : kit_text, combat.hit_marker * 0.92f) };

			for (auto corner{ 0u }; corner < 4u; corner++)
			{
				const structures::vec2_s direction{ corner & 1u ? 0.7071f : -0.7071f, corner & 2u ? 0.7071f : -0.7071f };

				canvas.line(center + direction * (7.0f * s), center + direction * (15.0f * s), 1.8f * s, color);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_prompt(std::float_t s)
	{
		if (prompt[0])
		{
			const auto size{ 19.0f * s };
			const auto width{ inline_keys({ 0.0f, 0.0f }, prompt, size, false, s) };

			inline_keys({ (canvas.screen_width - width) * 0.5f, canvas.screen_height * 0.5f + 72.0f * s }, prompt, size, true, s);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t hud_c::inline_keys(structures::vec2_s origin, const char* text, std::float_t size, bool draw, std::float_t s)
	{
		char piece[128]{};

		auto x{ origin.x };
		auto cursor{ text };

		while (*cursor)
		{
			const auto closing{ *cursor == '[' ? std::strchr(cursor, ']') : nullptr };

			auto length{ 0u };

			if (closing)
			{
				length = static_cast<std::uint32_t>(closing - cursor) + 1u;

				std::snprintf(piece, sizeof(piece), "%.*s", static_cast<std::int32_t>(length - 2u), cursor + 1);

				x += key_cap({ x, origin.y }, piece, size * 0.8f, draw, s) + 9.0f * s;
			}

			else
			{
				while (cursor[length] && (length == 0u || cursor[length] != '['))
				{
					length++;
				}

				std::snprintf(piece, sizeof(piece), "%.*s", static_cast<std::int32_t>(length), cursor);

				if (draw)
				{
					canvas.text_shadowed(structures::font_regular, { x, origin.y }, size, kit_text, piece, structures::align_left | structures::align_middle);
				}

				x += canvas.measure(structures::font_regular, size, piece);
			}

			cursor += length;
		}

		return x - origin.x;
	}
	/*
	//=====================================================================================
	*/
	std::float_t hud_c::key_cap(structures::vec2_s position, const char* label, std::float_t size, bool draw, std::float_t s)
	{
		const auto width{ std::max(kit.caps_width(structures::font_bold, size, label, 0.04f) + 14.0f * s, 26.0f * s) };

		if (draw)
		{
			const structures::rect_s box{ position.x, position.y - 13.0f * s, width, 26.0f * s };

			canvas.rect(box, functions::rgba(10u, 11u, 13u, 175u));
			canvas.border(box, s, functions::with_alpha(kit_text, 0.6f));

			kit.caps(structures::font_bold, { box.x + box.w * 0.5f, position.y - 0.5f * s }, size, kit_text, label, structures::align_center | structures::align_middle, 0.04f);
		}

		return width;
	}
	/*
	//=====================================================================================
	*/
	std::float_t hud_c::etched(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* text, std::uint32_t align, std::float_t spacing)
	{
		char shouted[256]{};

		kit.upper(text, shouted, sizeof(shouted));

		canvas.tracking = spacing;

		const auto width{ canvas.text_shadowed(font_index, position, size, color, shouted, align) };

		canvas.tracking = 0.0f;

		return width;
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_chat(std::float_t s)
	{
		const auto left{ 40.0f * s };
		const auto bottom{ canvas.screen_height - 236.0f * s };

		auto row{ 0.0f };

		if (chatting)
		{
			char line[net_chat_length + 8]{};

			const structures::rect_s field{ left - 12.0f * s, bottom - 18.0f * s, 580.0f * s, 36.0f * s };

			std::snprintf(line, sizeof(line), "%s%s", chat_text, std::fmod(client.clock, 1.0f) < 0.55f ? "|" : "");

			canvas.rect(field, functions::rgba(8u, 9u, 11u, 200u));
			canvas.border(field, s, functions::with_alpha(kit_accent, 0.55f));

			kit.caps(structures::font_condensed, { left, bottom }, 14.0f * s, kit_accent, "Say", structures::align_left | structures::align_middle, kit_wide);

			canvas.text(structures::font_regular, { left + 48.0f * s, bottom - s }, 18.0f * s, kit_text, line, structures::align_left | structures::align_middle);

			row += 1.5f;
		}

		for (auto index{ 0u }; index < net_chat_lines && (menu.user.chat || chatting); index++)
		{
			const auto shown{ chatting ? 1.0f : mathematics.saturate(client.chat_times[index] / 2.0f) };

			if (client.chat_lines[index][0] && shown > 0.0f)
			{
				canvas.text_shadowed(structures::font_regular, { left, bottom - row * 26.0f * s }, 18.0f * s, functions::with_alpha(kit_text, shown), client.chat_lines[index], structures::align_left | structures::align_middle);

				row += 1.0f;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_names(std::float_t s)
	{
		const structures::vec2_s size{ canvas.screen_width, canvas.screen_height };

		for (const auto& remote : client.remotes)
		{
			if (remote.actor >= 0 && remote.actor < static_cast<std::int32_t>(actors.list.size()) && remote.health > 0.0f)
			{
				const auto head{ actors.list[remote.actor].position + structures::vec3_s{ 0.0f, 2.05f, 0.0f } };
				const auto offset{ head - renderer.camera.position };
				const auto distance{ mathematics.length(offset) };
				const auto facing{ distance > 0.01f ? mathematics.dot(offset / distance, renderer.camera.forward) : 0.0f };

				structures::vec2_s point{};

				if (distance < net_name_range && facing > 0.985f && mathematics.project(head, renderer.camera.unjittered_view_projection, size, point) && world.trace(renderer.camera.position, head, { 0.01f, 0.01f, 0.01f }, structures::contents_solid).hit == false)
				{
					const auto fade{ mathematics.saturate((net_name_range - distance) / 8.0f) * mathematics.saturate((facing - 0.985f) / 0.008f) };

					canvas.text_shadowed(structures::font_bold, point, 17.0f * s, functions::with_alpha(kit_text, fade), remote.name, structures::align_center | structures::align_middle);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_hurt(std::float_t s)
	{
		if (hurt_timer > 0.0f)
		{
			const auto offset{ hurt_from - renderer.camera.position };
			const auto across_view{ mathematics.dot(offset, renderer.camera.right) };
			const auto ahead{ mathematics.dot(offset, renderer.camera.forward) };
			const auto angle{ std::atan2(across_view, ahead) };
			const auto alpha{ mathematics.saturate(hurt_timer / 0.6f) };
			const structures::vec2_s center{ canvas.screen_width * 0.5f, canvas.screen_height * 0.5f };
			const structures::vec2_s direction{ std::sin(angle), -std::cos(angle) };
			const structures::vec2_s across{ -direction.y, direction.x };

			for (auto segment{ -3 }; segment <= 3; segment++)
			{
				const auto spread{ static_cast<std::float_t>(segment) * 0.07f };
				const auto tangent{ direction * std::cos(spread) + across * std::sin(spread) };

				canvas.line(center + tangent * (120.0f * s), center + tangent * (136.0f * s), 4.0f * s, functions::with_alpha(hud_blood, alpha * (0.9f - std::fabs(static_cast<std::float_t>(segment)) * 0.12f)));
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_compass(std::float_t s)
	{
		const auto middle{ canvas.screen_width * 0.5f };
		const auto top{ 30.0f * s };
		const auto reach{ compass_width * 0.5f * s };
		const auto heading{ mathematics.wrap_angle(player.yaw) };
		const auto course{ std::fmod(heading / degrees_to_radians(1.0f) + 360.0f, 360.0f) };
		const structures::vec2_s feet{ player.state.position.x, player.state.position.z };

		char label[16]{};

		canvas.gradient_horizontal({ middle - reach, top - 16.0f * s, reach, 32.0f * s }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, 70u));
		canvas.gradient_horizontal({ middle, top - 16.0f * s, reach, 32.0f * s }, functions::rgba(0u, 0u, 0u, 70u), functions::rgba(0u, 0u, 0u, 0u));

		for (auto degree{ 0u }; degree < 360u; degree += 5u)
		{
			const auto offset{ mathematics.wrap_angle(degrees_to_radians(static_cast<std::float_t>(degree)) - heading) / degrees_to_radians(1.0f) };

			if (std::fabs(offset) < compass_span)
			{
				const auto x{ middle + offset / compass_span * reach };
				const auto fade{ 1.0f - std::pow(std::fabs(offset) / compass_span, 3.0f) };
				const auto major{ degree % 15u == 0u };

				if (degree % 45u == 0u)
				{
					etched(structures::font_condensed, { x, top }, (degree % 90u == 0u ? 21.0f : 15.0f) * s, functions::with_alpha(degree == 0u ? kit_accent : kit_text, fade), compass_points[degree / 45u], structures::align_center | structures::align_middle, 0.04f);
				}

				else
				{
					canvas.rect({ x - 0.75f * s, top - (major ? 6.0f : 3.0f) * s, 1.5f * s, (major ? 12.0f : 6.0f) * s }, functions::with_alpha(kit_text, fade * (major ? 0.75f : 0.4f)));
				}
			}
		}

		std::snprintf(label, sizeof(label), "%03u", static_cast<std::uint32_t>(course + 0.5f) % 360u);

		canvas.rect({ middle - s, top + 17.0f * s, 2.0f * s, 7.0f * s }, kit_accent);

		canvas.text_shadowed(structures::font_bold, { middle, top + 38.0f * s }, 14.0f * s, kit_text, label, structures::align_center | structures::align_middle);

		auto focus{ compass_focus };
		auto focused{ -2 };

		for (auto index{ 0u }; index < chart_pin_count; index++)
		{
			if (chart.pins[index].stamp && std::fabs(compass_bearing(chart.pins[index].position)) < focus)
			{
				focus = std::fabs(compass_bearing(chart.pins[index].position));
				focused = static_cast<std::int32_t>(index);
			}
		}

		if (chart.grave_marked && std::fabs(compass_bearing(chart.grave)) < focus)
		{
			focused = -1;
		}

		for (auto index{ 0u }; index < chart_pin_count; index++)
		{
			if (const auto bearing{ compass_bearing(chart.pins[index].position) }; chart.pins[index].stamp && std::fabs(bearing) < compass_span)
			{
				std::snprintf(label, sizeof(label), "%u", index + 1u);

				compass_mark({ middle + bearing / compass_span * reach, top + 66.0f * s }, 1.0f - std::pow(std::fabs(bearing) / compass_span, 3.0f), kit_cool, label, mathematics.length(chart.pins[index].position - feet), focused == static_cast<std::int32_t>(index), s);
			}
		}

		if (const auto bearing{ compass_bearing(chart.grave) }; chart.grave_marked && std::fabs(bearing) < compass_span)
		{
			compass_mark({ middle + bearing / compass_span * reach, top + 66.0f * s }, 1.0f - std::pow(std::fabs(bearing) / compass_span, 3.0f), hud_blood, "+", mathematics.length(chart.grave - feet), focused == -1, s);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t hud_c::compass_bearing(structures::vec2_s target)
	{
		return mathematics.wrap_angle(std::atan2(target.x - player.state.position.x, target.y - player.state.position.z) - player.yaw) / degrees_to_radians(1.0f);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::compass_mark(structures::vec2_s point, std::float_t fade, std::uint32_t color, const char* label, std::float_t distance, bool focused, std::float_t s)
	{
		char metres[16]{};

		std::snprintf(metres, sizeof(metres), "%.0f m", distance);

		canvas.circle(point, 10.0f * s, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(fade * 110.0f)));
		canvas.ring(point, 10.0f * s, 1.6f * s, -1.0f, 7.5f, functions::with_alpha(color, fade));
		canvas.text(structures::font_bold, { point.x, point.y - 0.5f * s }, 13.0f * s, functions::with_alpha(color, fade), label, structures::align_center | structures::align_middle);

		if (focused)
		{
			canvas.text_shadowed(structures::font_bold, point + structures::vec2_s{ 0.0f, 22.0f * s }, 13.0f * s, functions::with_alpha(kit_text, fade), metres, structures::align_center | structures::align_middle);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_death(std::float_t s)
	{
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const auto middle{ height * 0.44f };
		const auto cause{ std::min<std::uint32_t>(client.connected() ? client.death_cause : survival.harm, static_cast<std::uint32_t>(std::size(death_lines) - 1u)) };
		const auto dark{ mathematics.saturate(death_clock / 1.2f) };
		const auto words{ mathematics.saturate((death_clock - 0.5f) / 1.0f) };
		const auto bag{ building.bag >= 0 && building.placed[building.bag].destroyed == false };

		char key[32]{};
		char cause_line[96]{};

		menu.key_name(platform.bindings[structures::bind_jump], key, sizeof(key));

		std::snprintf(cause_line, sizeof(cause_line), client.connected() && client.death_killer[0] ? "Killed by %s." : "%s", client.connected() && client.death_killer[0] ? client.death_killer : death_lines[cause]);

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(6u, 3u, 3u, static_cast<std::uint32_t>(120.0f + dark * 110.0f)));
		canvas.gradient({ 0.0f, height * 0.6f, width, height * 0.4f }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(dark * 160.0f)));

		canvas.tracking = 0.14f;

		canvas.text_shadowed(structures::font_display, { width * 0.5f, middle }, 92.0f * s, functions::with_alpha(hud_blood, words), "YOU ARE DEAD", structures::align_center | structures::align_middle);

		canvas.tracking = 0.0f;

		canvas.rect({ width * 0.5f - 28.0f * s, middle + 60.0f * s, 56.0f * s, 2.0f * s }, functions::with_alpha(hud_blood, words));

		canvas.text(structures::font_regular, { width * 0.5f, middle + 96.0f * s }, 24.0f * s, functions::with_alpha(kit_text, words), cause_line, structures::align_center | structures::align_middle);
		canvas.text(structures::font_light, { width * 0.5f, middle + 134.0f * s }, 19.0f * s, functions::with_alpha(kit_dim, words), "Everything you carried is in a bag where you fell.", structures::align_center | structures::align_middle);

		if (death_clock > 1.5f)
		{
			kit.hint({ width * 0.5f, middle + 214.0f * s }, key, bag ? "Wake in your sleeping bag" : "Wake on the shore", structures::align_center);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_ending(std::float_t s)
	{
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const auto middle{ height * 0.44f };

		char key[32]{};
		char text[128]{};

		menu.key_name(platform.bindings[structures::bind_jump], key, sizeof(key));

		std::snprintf(text, sizeof(text), "The Morning Star took you off the island on day %u.", story.day);

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(6u, 7u, 9u, 190u));

		canvas.tracking = 0.14f;

		canvas.text_shadowed(structures::font_display, { width * 0.5f, middle }, 92.0f * s, kit_text, "RESCUED", structures::align_center | structures::align_middle);

		canvas.tracking = 0.0f;

		canvas.rect({ width * 0.5f - 28.0f * s, middle + 60.0f * s, 56.0f * s, 2.0f * s }, kit_accent);

		canvas.text(structures::font_regular, { width * 0.5f, middle + 96.0f * s }, 24.0f * s, kit_text, text, structures::align_center | structures::align_middle);

		kit.hint({ width * 0.5f, middle + 180.0f * s }, key, "Keep playing", structures::align_center);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_goal(std::float_t s)
	{
		if (story.step < goal_count)
		{
			const auto& goal{ goals[story.step] };
			const auto done{ mathematics.saturate(story.done_flash / 2.5f) };
			const auto width{ 380.0f * s };
			const auto left{ canvas.screen_width - 40.0f * s - width };
			const auto top{ 54.0f * s };

			char lines[4][160]{};
			char heading[48]{};
			char progress[64]{};

			const auto count{ kit.wrap(goal.hint, structures::font_regular, 17.0f * s, width, lines, 4u) };

			if (goal.kind == structures::goal_have)
			{
				std::snprintf(progress, sizeof(progress), "%s  %u / %u", item_definitions[goal.subject].name, story.progress(goal), goal.amount);
			}

			else if (goal.kind == structures::goal_parts)
			{
				std::snprintf(progress, sizeof(progress), "Radio parts  %u / %u", story.progress(goal), goal.amount);
			}

			else if (goal.kind == structures::goal_wait)
			{
				std::snprintf(progress, sizeof(progress), "Days waited  %u / %u", story.progress(goal), goal.amount);
			}

			else if (goal.kind == structures::goal_research)
			{
				std::snprintf(progress, sizeof(progress), "Researched  %u / %u", story.progress(goal), goal.amount);
			}

			std::snprintf(heading, sizeof(heading), "Day %u   \xB7   %s", story.day, done > 0.0f ? "New goal" : "Survival goal");

			const auto block{ 70.0f * s + static_cast<std::float_t>(count) * 24.0f * s + (progress[0] ? 36.0f * s : 0.0f) };

			canvas.gradient_horizontal({ left - 90.0f * s, top - 26.0f * s, width + 130.0f * s, block + 30.0f * s }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, 45u));

			etched(structures::font_condensed, { left, top }, 15.0f * s, done > 0.0f ? kit_accent : kit_dim, heading, structures::align_left | structures::align_middle, kit_wide);

			canvas.text_shadowed(structures::font_bold, { left, top + 28.0f * s }, 23.0f * s, functions::lerp_color(kit_text, kit_accent, done), goal.title, structures::align_left | structures::align_middle);

			for (auto line{ 0u }; line < count; line++)
			{
				canvas.text_shadowed(structures::font_regular, { left, top + 60.0f * s + static_cast<std::float_t>(line) * 24.0f * s }, 17.0f * s, kit_dim, lines[line], structures::align_left | structures::align_middle);
			}

			if (progress[0])
			{
				const auto y{ top + 66.0f * s + static_cast<std::float_t>(count) * 24.0f * s };
				const auto fraction{ mathematics.saturate(static_cast<std::float_t>(story.progress(goal)) / static_cast<std::float_t>(std::max(goal.amount, 1u))) };

				etched(structures::font_condensed, { left, y }, 15.0f * s, kit_accent, progress, structures::align_left | structures::align_middle, kit_caps);

				canvas.rect({ left, y + 14.0f * s, 180.0f * s, 2.0f * s }, functions::rgba(255u, 255u, 255u, 50u));
				canvas.rect({ left, y + 14.0f * s, 180.0f * s * fraction, 2.0f * s }, kit_accent);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_vitals(std::float_t s)
	{
		const std::float_t values[4] = { survival.vitals.health, survival.vitals.hydration, survival.vitals.calories, survival.vitals.breath * 100.0f };
		const std::float_t maxima[4] = { maximum_health, maximum_hydration, maximum_calories, 100.0f };
		const std::uint32_t colors[4] = { hud_health, kit_cool, kit_accent, hud_breath };
		const std::uint32_t order[4] = { 2u, 1u, 0u, 3u };
		const auto left{ 40.0f * s };

		auto y{ canvas.screen_height - 46.0f * s };

		for (const auto vital : order)
		{
			if (vital_glow[vital] > 0.01f)
			{
				draw_meter({ left, y }, vital, values[vital], maxima[vital], colors[vital], hud_meter_width * s, vital_glow[vital], s);
			}

			y -= 30.0f * s * vital_glow[vital];
		}

		draw_climate({ left, y - 8.0f * s }, false, s);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_meter(structures::vec2_s position, std::uint32_t label, std::float_t value, std::float_t maximum, std::uint32_t color, std::float_t width, std::float_t alpha, std::float_t s)
	{
		char text[16]{};

		const auto fraction{ std::clamp(value / maximum, 0.0f, 1.0f) };
		const auto low{ fraction < 0.25f };
		const auto pulse{ low ? 0.6f + 0.4f * (0.5f + 0.5f * std::sin(clock * 5.0f)) : 1.0f };
		const auto bar{ position.x + 76.0f * s };

		std::snprintf(text, sizeof(text), "%.0f", value);

		etched(structures::font_condensed, position, 15.0f * s, functions::with_alpha(low ? kit_danger : functions::lerp_color(kit_dim, kit_text, 0.5f), alpha), hud_vital_labels[label], structures::align_left | structures::align_middle, kit_caps);

		canvas.rect({ bar - s, position.y - 2.5f * s, width + 2.0f * s, 5.0f * s }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(alpha * 90.0f)));
		canvas.rect({ bar, position.y - 1.5f * s, width, 3.0f * s }, functions::rgba(255u, 255u, 255u, static_cast<std::uint32_t>(alpha * 46.0f)));
		canvas.rect({ bar, position.y - 1.5f * s, width * fraction, 3.0f * s }, functions::with_alpha(low ? kit_danger : color, alpha * pulse));

		canvas.text_shadowed(structures::font_bold, { bar + width + 12.0f * s, position.y - s }, 16.0f * s, functions::with_alpha(low ? kit_danger : kit_text, alpha), text, structures::align_left | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_climate(structures::vec2_s position, bool always, std::float_t s)
	{
		const auto cold{ survival.climate.temperature < climate_cold };
		const auto hot{ survival.climate.temperature > climate_hot };
		const auto wet{ survival.climate.wetness > 0.05f };

		char text[48]{};

		auto x{ position.x };

		if (always || cold || hot)
		{
			const auto tone{ cold ? kit_cool : (hot ? kit_danger : kit_dim) };

			std::snprintf(text, sizeof(text), "%s  %.0f\xB0" "C", cold ? (survival.climate.temperature < climate_freezing ? "Freezing" : "Cold") : (hot ? "Overheating" : "Comfortable"), survival.climate.temperature);

			canvas.circle({ x + 4.0f * s, position.y }, 3.5f * s, tone);

			x += etched(structures::font_condensed, { x + 14.0f * s, position.y }, 14.0f * s, tone, text, structures::align_left | structures::align_middle, kit_caps) + 36.0f * s;
		}

		if (always || wet)
		{
			std::snprintf(text, sizeof(text), "%s  %.0f%%", wet ? "Wet" : "Dry", survival.climate.wetness * 100.0f);

			canvas.circle({ x + 4.0f * s, position.y }, 3.5f * s, wet ? kit_cool : kit_dim);

			etched(structures::font_condensed, { x + 14.0f * s, position.y }, 14.0f * s, wet ? kit_cool : kit_dim, text, structures::align_left | structures::align_middle, kit_caps);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_scope(std::float_t s)
	{
		const structures::vec2_s center{ canvas.screen_width * 0.5f, canvas.screen_height * 0.5f };
		const auto radius{ canvas.screen_height * 0.46f };
		const auto outer{ mathematics.length(center) + 4.0f };
		const auto black{ functions::rgba(0u, 0u, 0u, 255u) };

		canvas.ring(center, outer, outer - radius, -1.0f, 7.5f, black);

		for (auto band{ 0u }; band < 8u; band++)
		{
			canvas.ring(center, radius + 1.0f, (3.0f + static_cast<std::float_t>(band) * 5.0f) * s, -1.0f, 7.5f, functions::rgba(0u, 0u, 0u, 34u));
		}

		canvas.line({ center.x - radius, center.y }, { center.x + radius, center.y }, 1.3f * s, functions::rgba(0u, 0u, 0u, 235u));
		canvas.line({ center.x, center.y - radius }, { center.x, center.y + radius }, 1.3f * s, functions::rgba(0u, 0u, 0u, 235u));

		for (auto edge{ 0u }; edge < 4u; edge++)
		{
			const structures::vec2_s direction{ edge < 2u ? (edge ? 1.0f : -1.0f) : 0.0f, edge < 2u ? 0.0f : (edge == 2u ? -1.0f : 1.0f) };

			canvas.line(center + direction * (radius * 0.3f), center + direction * radius, 5.0f * s, black);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_belt(std::float_t s)
	{
		if (belt_glow > 0.01f)
		{
			char number[4]{};

			for (auto index{ 0u }; index < hotbar_slots; index++)
			{
				const auto area{ slot_rect(inventory_slots + index, s) };

				draw_slot(area, inventory_slots + index, index == survival.active_slot, belt_glow, s);

				std::snprintf(number, sizeof(number), "%u", index + 1u);

				canvas.text(structures::font_condensed, { area.x + 7.0f * s, area.y + 12.0f * s }, 14.0f * s, functions::with_alpha(kit_dim, belt_glow), number, structures::align_left | structures::align_middle);
			}

			if (survival.inventory_open)
			{
				const auto first{ slot_rect(inventory_slots, s) };

				kit.caps(structures::font_condensed, { first.x, first.y - 18.0f * s }, 15.0f * s, kit_faint, "Belt", structures::align_left | structures::align_middle, kit_wide);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_notifications(std::float_t s)
	{
		const auto right{ canvas.screen_width - 40.0f * s };

		char amount[16]{};

		auto y{ canvas.screen_height - 52.0f * s - static_cast<std::float_t>(survival.queue_count) * 44.0f * s - (survival.queue_count ? 12.0f * s : 0.0f) };

		for (const auto& notification : survival.notifications)
		{
			if (notification.text[0] && notification.age < notification_time && (notification.amount <= 0 || menu.user.pickup_messages))
			{
				const auto enter{ mathematics.saturate(notification.age * 6.0f) };
				const auto fade{ std::clamp((notification_time - notification.age) * 2.0f, 0.0f, 1.0f) * enter };
				const auto x{ right + (1.0f - enter) * 40.0f * s };

				if (notification.amount > 0)
				{
					std::snprintf(amount, sizeof(amount), "+%d", notification.amount);

					const auto name_width{ canvas.text_shadowed(structures::font_regular, { x, y }, 18.0f * s, functions::with_alpha(kit_text, fade), notification.text, structures::align_right | structures::align_middle) };

					canvas.text_shadowed(structures::font_bold, { x - name_width - 10.0f * s, y }, 18.0f * s, functions::with_alpha(kit_accent, fade), amount, structures::align_right | structures::align_middle);
				}

				else
				{
					canvas.text_shadowed(structures::font_regular, { x, y }, 18.0f * s, functions::with_alpha(kit_text, fade), notification.text, structures::align_right | structures::align_middle);
				}

				y -= 30.0f * s;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_queue(std::float_t s)
	{
		const auto right{ canvas.screen_width - 40.0f * s };

		char text[32]{};

		for (auto index{ 0u }; index < survival.queue_count; index++)
		{
			const auto& job{ survival.queue[index] };
			const auto y{ canvas.screen_height - 52.0f * s - static_cast<std::float_t>(index) * 44.0f * s };
			const auto fraction{ index == 0u ? 1.0f - mathematics.saturate(job.remaining / std::max(recipes[job.recipe].time, 0.01f)) : 0.0f };

			std::snprintf(text, sizeof(text), "%.0f s", std::ceil(job.remaining));

			const auto time_width{ canvas.text_shadowed(structures::font_bold, { right, y }, 15.0f * s, kit_text, text, structures::align_right | structures::align_middle) };

			canvas.text_shadowed(structures::font_regular, { right - time_width - 12.0f * s, y }, 17.0f * s, index == 0u ? kit_text : kit_dim, item_definitions[recipes[job.recipe].result].name, structures::align_right | structures::align_middle);

			canvas.rect({ right - 220.0f * s, y + 14.0f * s, 220.0f * s, 2.0f * s }, functions::rgba(255u, 255u, 255u, 46u));
			canvas.rect({ right - 220.0f * s, y + 14.0f * s, 220.0f * s * fraction, 2.0f * s }, kit_accent);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_inventory(std::float_t s)
	{
		const auto area{ sheet(s) };
		const auto page{ page_rect(s) };
		const auto first{ slot_rect(0u, s) };
		const auto last{ slot_rect(inventory_slots - 1u, s) };
		const auto bottom{ canvas.screen_height - 44.0f * s };

		char carried[48]{};
		char key[32]{};

		auto used{ 0u };

		hover_slot = -1;
		hover_recipe = -1;

		for (auto index{ 0u }; index < inventory_slots; index++)
		{
			used += survival.slots[index].item ? 1u : 0u;
		}

		std::snprintf(carried, sizeof(carried), "%u of %u spaces used", used, inventory_slots);

		menu.key_name(platform.bindings[structures::bind_inventory], key, sizeof(key));

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(5u, 6u, 7u, 190u));
		canvas.gradient({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height * 0.3f }, functions::rgba(0u, 0u, 0u, 120u), functions::rgba(0u, 0u, 0u, 0u));
		canvas.gradient({ 0.0f, canvas.screen_height * 0.7f, canvas.screen_width, canvas.screen_height * 0.3f }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, 150u));

		draw_title({ area.x, area.y }, "Inventory", carried, s);

		for (auto index{ 0u }; index < inventory_slots; index++)
		{
			draw_slot(slot_rect(index, s), index, false, 1.0f, s);
		}

		draw_condition({ first.x, last.y + last.h + 56.0f * s }, last.x + last.w - first.x, s);

		if (survival.open_container >= 0)
		{
			draw_container(page, s);
		}

		else
		{
			draw_crafting(page, s);
		}

		auto x{ 40.0f * s };

		x += kit.hint({ x, bottom }, key, "Close", structures::align_left) + 30.0f * s;
		x += kit.hint({ x, bottom }, "Drag", "Move", structures::align_left) + 30.0f * s;
		x += kit.hint({ x, bottom }, "Shift click", "Quick move", structures::align_left) + 30.0f * s;

		kit.hint({ x, bottom }, "Right click", "Use", structures::align_left);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_title(structures::vec2_s position, const char* title, const char* subtitle, std::float_t s)
	{
		char shouted[96]{};

		kit.upper(title, shouted, sizeof(shouted));

		canvas.tracking = kit_title_spacing;

		canvas.text_shadowed(structures::font_display, { position.x, position.y + 20.0f * s }, 44.0f * s, kit_text, shouted, structures::align_left | structures::align_middle);

		canvas.tracking = 0.0f;

		kit.caps(structures::font_condensed, { position.x + 2.0f * s, position.y + 56.0f * s }, 15.0f * s, kit_faint, subtitle, structures::align_left | structures::align_middle, kit_wide);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_condition(structures::vec2_s position, std::float_t width, std::float_t s)
	{
		const std::float_t values[3] = { survival.vitals.health, survival.vitals.hydration, survival.vitals.calories };
		const std::float_t maxima[3] = { maximum_health, maximum_hydration, maximum_calories };
		const std::uint32_t colors[3] = { hud_health, kit_cool, kit_accent };

		kit.caps(structures::font_condensed, position, 15.0f * s, kit_accent, "Condition", structures::align_left | structures::align_middle, kit_wide);

		kit.rule({ position.x, position.y + 18.0f * s }, width, kit_line);

		for (auto vital{ 0u }; vital < 3u; vital++)
		{
			draw_meter({ position.x, position.y + 52.0f * s + static_cast<std::float_t>(vital) * 32.0f * s }, vital, values[vital], maxima[vital], colors[vital], width - 130.0f * s, 1.0f, s);
		}

		draw_climate({ position.x, position.y + 160.0f * s }, true, s);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_crafting(structures::rect_s page, std::float_t s)
	{
		const auto bench{ survival.station() };
		const auto lab{ building.research_nearby(player.state.position) };
		const auto mouse{ platform.input.mouse_position };
		const structures::rect_s list{ page.x, page.y + 90.0f * s, page.w, page.h - 110.0f * s - hud_detail_height * s };
		const structures::rect_s detail{ page.x, page.y + page.h - hud_detail_height * s, page.w - 24.0f * s, hud_detail_height * s };
		const auto row_height{ hud_recipe_row * s };
		const auto content{ static_cast<std::float_t>(recipe_count) * row_height };
		const auto limit{ std::max(content - list.h, 0.0f) };

		char status[96]{};

		std::snprintf(status, sizeof(status), "%s%s", bench ? tier_names[bench] : "No workbench nearby", lab ? "   \xB7   Research table" : "");

		draw_title({ page.x, page.y }, "Crafting", status, s);

		if (list.contains(mouse) && platform.input.wheel != 0.0f)
		{
			recipe_scroll -= platform.input.wheel * row_height * 3.0f;
		}

		recipe_scroll = std::clamp(recipe_scroll, 0.0f, limit);

		canvas.push_scissor(list);

		for (auto recipe{ 0u }; recipe < recipe_count; recipe++)
		{
			const structures::rect_s row{ list.x, list.y + static_cast<std::float_t>(recipe) * row_height - recipe_scroll, list.w - 24.0f * s, row_height };

			if (row.y + row.h > list.y && row.y < list.y + list.h)
			{
				const auto over{ row.contains(mouse) && list.contains(mouse) };

				draw_recipe(row, recipe, over, s);

				hover_recipe = over ? static_cast<std::int32_t>(recipe) : hover_recipe;
			}
		}

		canvas.pop_scissor();

		if (limit > 0.0f)
		{
			const auto thumb{ std::max(list.h * list.h / content, 40.0f * s) };

			canvas.rect({ list.x + list.w - 2.0f * s, list.y, 2.0f * s, list.h }, kit_line);
			canvas.rect({ list.x + list.w - 2.0f * s, list.y + (list.h - thumb) * recipe_scroll / limit, 2.0f * s, thumb }, kit_dim);
		}

		kit.panel(detail, functions::rgba(255u, 255u, 255u, 8u));

		if (hover_recipe >= 0)
		{
			draw_details(detail, static_cast<std::uint32_t>(hover_recipe), s);
		}

		else
		{
			canvas.text(structures::font_light, { detail.x + 24.0f * s, detail.y + detail.h * 0.5f }, 18.0f * s, kit_faint, "Point at a recipe to see what it needs.", structures::align_left | structures::align_middle);
		}

		if (platform.input.pressed[VK_LBUTTON] && hover_recipe >= 0)
		{
			const auto chosen{ static_cast<std::uint32_t>(hover_recipe) };
			const auto crafting{ survival.known[chosen] };

			if (crafting ? survival.craft(chosen) : survival.research(chosen))
			{
				if (crafting)
				{
					survival.post("Crafting started", 0);
				}

				kit.click(1.0f);
			}

			else
			{
				mixer.play_2d(structures::sound_ui_error, 0.4f * menu.user.interface_volume, 1.0f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_recipe(structures::rect_s area, std::uint32_t recipe, bool over, std::float_t s)
	{
		const auto& entry{ recipes[recipe] };
		const auto known{ survival.known[recipe] };
		const auto available{ survival.can_craft(recipe) };
		const auto bench{ survival.station() };
		const auto lab{ building.research_nearby(player.state.position) };
		const auto light{ kit.fade(430 + static_cast<std::int32_t>(recipe), over) };
		const auto middle{ area.y + area.h * 0.5f };
		const auto affordable{ survival.count(structures::item_scrap) >= research_costs[entry.tier] };

		char cost[128]{};
		char part[48]{};

		if (known && entry.tier > bench)
		{
			std::snprintf(cost, sizeof(cost), "Needs %s", tier_names[entry.tier]);
		}

		else if (known)
		{
			for (const auto& ingredient : entry.ingredients)
			{
				if (ingredient.item)
				{
					std::snprintf(part, sizeof(part), "%s%u %s", cost[0] ? ",  " : "", ingredient.amount, item_definitions[ingredient.item].name);
					std::strncat(cost, part, sizeof(cost) - std::strlen(cost) - 1u);
				}
			}
		}

		else
		{
			std::snprintf(cost, sizeof(cost), lab ? "Research  %u scrap" : "Blueprint needed", research_costs[entry.tier]);
		}

		canvas.rect(area, functions::rgba(255u, 255u, 255u, static_cast<std::uint32_t>(light * 16.0f)));
		canvas.rect({ area.x, area.y + area.h * 0.2f, 2.0f * s, area.h * 0.6f }, functions::with_alpha(kit_accent, light));

		if (available)
		{
			canvas.circle({ area.x + 16.0f * s, middle }, 3.0f * s, kit_good);
		}

		canvas.text(structures::font_condensed, { area.x + 40.0f * s, middle }, 14.0f * s, kit_faint, tier_marks[entry.tier], structures::align_center | structures::align_middle);
		canvas.text(structures::font_regular, { area.x + 62.0f * s, middle - s }, 18.0f * s, available ? kit_text : (known ? kit_dim : kit_faint), item_definitions[entry.result].name, structures::align_left | structures::align_middle);
		canvas.text(structures::font_regular, { area.x + area.w - 14.0f * s, middle - s }, 16.0f * s, known ? (entry.tier > bench ? functions::with_alpha(kit_danger, 0.8f) : (available ? kit_dim : kit_faint)) : (lab && affordable ? kit_accent : kit_faint), cost, structures::align_right | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_details(structures::rect_s area, std::uint32_t recipe, std::float_t s)
	{
		const auto& entry{ recipes[recipe] };
		const auto known{ survival.known[recipe] };
		const auto available{ survival.can_craft(recipe) };
		const auto bench{ survival.station() };
		const auto lab{ building.research_nearby(player.state.position) };
		const auto affordable{ survival.count(structures::item_scrap) >= research_costs[entry.tier] };
		const structures::vec2_s corner{ area.x + area.w - 24.0f * s, area.y + area.h - 30.0f * s };

		char line[96]{};

		auto x{ area.x + 24.0f * s };

		kit.caps(structures::font_condensed, { x, area.y + 32.0f * s }, 21.0f * s, kit_text, item_definitions[entry.result].name, structures::align_left | structures::align_middle, kit_caps);

		std::snprintf(line, sizeof(line), "Makes %u   \xB7   %.0f seconds   \xB7   %s", entry.amount, entry.time, tier_names[entry.tier]);

		kit.caps(structures::font_condensed, { x, area.y + 60.0f * s }, 15.0f * s, kit_faint, line, structures::align_left | structures::align_middle, kit_wide);

		for (const auto& ingredient : entry.ingredients)
		{
			if (ingredient.item)
			{
				const auto have{ survival.count(ingredient.item) };

				std::snprintf(line, sizeof(line), "%u %s", ingredient.amount, item_definitions[ingredient.item].name);

				x += canvas.text(structures::font_regular, { x, area.y + 96.0f * s }, 18.0f * s, have >= ingredient.amount ? kit_text : kit_danger, line, structures::align_left | structures::align_middle);

				std::snprintf(line, sizeof(line), "  (%u)", have);

				x += canvas.text(structures::font_regular, { x, area.y + 96.0f * s }, 16.0f * s, kit_faint, line, structures::align_left | structures::align_middle) + 26.0f * s;
			}
		}

		if (known && entry.tier > bench)
		{
			std::snprintf(line, sizeof(line), "Stand near a %s", tier_names[entry.tier]);

			canvas.text(structures::font_regular, corner, 17.0f * s, kit_danger, line, structures::align_right | structures::align_middle);
		}

		else if (known && available)
		{
			kit.hint(corner, "Click", "Craft", structures::align_right);
		}

		else if (known)
		{
			canvas.text(structures::font_regular, corner, 17.0f * s, kit_danger, "Missing materials", structures::align_right | structures::align_middle);
		}

		else if (lab && affordable)
		{
			std::snprintf(line, sizeof(line), "Research for %u scrap", research_costs[entry.tier]);

			kit.hint(corner, "Click", line, structures::align_right);
		}

		else
		{
			std::snprintf(line, sizeof(line), lab ? "Research needs %u scrap" : "Find a blueprint or a research table", research_costs[entry.tier]);

			canvas.text(structures::font_regular, corner, 17.0f * s, lab ? kit_danger : kit_faint, line, structures::align_right | structures::align_middle);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_container(structures::rect_s page, std::float_t s)
	{
		auto& container{ building.containers[survival.open_container] };

		const auto cooking{ container.kind == structures::container_campfire };
		const auto storage{ container.kind == structures::container_storage };

		draw_title({ page.x, page.y }, piece_definitions[building.placed[container.structure].piece].name, storage ? "Storage" : (container.burning ? (cooking ? "Burning   \xB7   cooking" : "Burning   \xB7   smelting") : "Not lit"), s);

		for (auto index{ 0u }; index < container_slots; index++)
		{
			draw_slot(slot_rect(container_address + index, s), container_address + index, false, 1.0f, s);
		}

		if (storage == false)
		{
			const auto fuel{ slot_rect(container_address + furnace_fuel_slot, s) };
			const auto input{ slot_rect(container_address + furnace_fuel_slot + 1u, s) };
			const auto output{ slot_rect(container_address + furnace_first_output, s) };
			const auto bottom{ slot_rect(container_address + container_slots - 1u, s) };
			const auto fueled{ container.slots[furnace_fuel_slot].item == structures::item_wood && container.slots[furnace_fuel_slot].amount > 0u };

			kit.caps(structures::font_condensed, { fuel.x, fuel.y - 15.0f * s }, 15.0f * s, kit_faint, "Fuel", structures::align_left | structures::align_middle, kit_wide);
			kit.caps(structures::font_condensed, { input.x, input.y - 15.0f * s }, 15.0f * s, kit_faint, cooking ? "Raw food" : "Ore", structures::align_left | structures::align_middle, kit_wide);
			kit.caps(structures::font_condensed, { output.x, output.y - 15.0f * s }, 15.0f * s, container.burning ? kit_accent : kit_faint, cooking ? "Cooked" : "Output", structures::align_left | structures::align_middle, kit_wide);

			if (kit.button(495, { page.x, bottom.y + bottom.h + 40.0f * s, 260.0f * s, 52.0f * s }, container.burning ? "Put it out" : "Light it", container.burning == false))
			{
				if (container.burning || fueled)
				{
					container.burning = container.burning == false;

					if (client.connected())
					{
						client.request(structures::request_light, static_cast<std::uint16_t>(survival.open_container), container.burning ? 1u : 0u);
					}
				}

				else
				{
					survival.post(cooking ? "The fire needs wood" : "The furnace needs wood", 0);

					mixer.play_2d(structures::sound_ui_error, 0.4f * menu.user.interface_volume, 1.0f);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_grab(std::float_t s)
	{
		const auto mouse{ platform.input.mouse_position };

		if (platform.input.pressed[VK_LBUTTON] && hover_slot >= 0 && survival.slot(static_cast<std::uint32_t>(hover_slot)).item)
		{
			if (platform.input.down[VK_SHIFT])
			{
				survival.transfer(static_cast<std::uint32_t>(hover_slot));

				mixer.play_2d(structures::sound_pickup, 0.35f, 1.1f);
			}

			else
			{
				drag_slot = hover_slot;
			}
		}

		if (platform.input.released[VK_LBUTTON] && drag_slot >= 0)
		{
			if (hover_slot >= 0)
			{
				survival.swap(static_cast<std::uint32_t>(drag_slot), static_cast<std::uint32_t>(hover_slot));

				mixer.play_2d(structures::sound_pickup, 0.3f, 1.2f);
			}

			drag_slot = -1;
		}

		if (platform.input.pressed[VK_RBUTTON] && hover_slot >= 0 && hover_slot < static_cast<std::int32_t>(total_slots))
		{
			survival.consume(static_cast<std::uint32_t>(hover_slot));
		}

		if (drag_slot >= 0 && survival.slot(static_cast<std::uint32_t>(drag_slot)).item)
		{
			const structures::rect_s ghost{ mouse.x - 38.0f * s, mouse.y - 38.0f * s, 76.0f * s, 76.0f * s };

			canvas.rect(ghost, functions::rgba(22u, 23u, 26u, 225u));
			canvas.border(ghost, s, functions::with_alpha(kit_accent, 0.8f));

			draw_item(ghost, survival.slot(static_cast<std::uint32_t>(drag_slot)).item, 1.0f, s);
		}

		else if (hover_slot >= 0 && survival.slot(static_cast<std::uint32_t>(hover_slot)).item)
		{
			draw_tooltip(survival.slot(static_cast<std::uint32_t>(hover_slot)), s);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_tooltip(const structures::item_stack_s& stack, std::float_t s)
	{
		const auto& definition{ item_definitions[stack.item] };
		const auto mouse{ platform.input.mouse_position };
		const auto width{ 340.0f * s };
		const auto worn{ definition.stack == 1u && definition.category != structures::item_category_construction };

		char lines[4][160]{};
		char detail[64]{};

		const auto count{ kit.wrap(definition.description, structures::font_regular, 16.0f * s, width - 40.0f * s, lines, 4u) };
		const auto height{ 74.0f * s + static_cast<std::float_t>(count) * 22.0f * s + (worn || stack.amount > 1u ? 30.0f * s : 0.0f) };
		const structures::rect_s area{ std::min(mouse.x + 20.0f * s, canvas.screen_width - width - 10.0f * s), std::min(mouse.y + 18.0f * s, canvas.screen_height - height - 10.0f * s), width, height };

		kit.panel(area, functions::rgba(12u, 13u, 15u, 246u));

		canvas.rect({ area.x, area.y, area.w, 2.0f * s }, kit_accent);

		kit.caps(structures::font_condensed, { area.x + 20.0f * s, area.y + 28.0f * s }, 19.0f * s, kit_text, definition.name, structures::align_left | structures::align_middle, kit_caps);
		kit.caps(structures::font_condensed, { area.x + 20.0f * s, area.y + 52.0f * s }, 14.0f * s, kit_faint, item_category_names[std::min(definition.category, static_cast<std::uint32_t>(structures::item_category_count) - 1u)], structures::align_left | structures::align_middle, kit_wide);

		for (auto line{ 0u }; line < count; line++)
		{
			canvas.text(structures::font_regular, { area.x + 20.0f * s, area.y + 80.0f * s + static_cast<std::float_t>(line) * 22.0f * s }, 16.0f * s, kit_dim, lines[line], structures::align_left | structures::align_middle);
		}

		if (worn || stack.amount > 1u)
		{
			std::snprintf(detail, sizeof(detail), worn ? "Condition  %.0f%%" : "Stack  %.0f", worn ? stack.condition * 100.0f : static_cast<std::float_t>(stack.amount));

			kit.caps(structures::font_condensed, { area.x + 20.0f * s, area.y + area.h - 22.0f * s }, 13.0f * s, worn && stack.condition < 0.25f ? kit_danger : kit_accent, detail, structures::align_left | structures::align_middle, kit_caps);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_slot(structures::rect_s area, std::uint32_t index, bool active, std::float_t alpha, std::float_t s)
	{
		const auto& slot{ survival.slot(index) };
		const auto hovered{ survival.inventory_open && area.contains(platform.input.mouse_position) };
		const auto light{ survival.inventory_open ? kit.fade(300 + static_cast<std::int32_t>(index), hovered) : 0.0f };

		canvas.rect(area, functions::rgba(14u, 15u, 17u, static_cast<std::uint32_t>(alpha * (survival.inventory_open ? 175.0f : 120.0f))));
		canvas.rect(area, functions::rgba(255u, 255u, 255u, static_cast<std::uint32_t>(alpha * light * 26.0f)));
		canvas.border(area, s, functions::with_alpha(active ? kit_accent : functions::lerp_color(kit_line, functions::with_alpha(kit_text, 0.5f), light), alpha));

		if (active)
		{
			canvas.rect({ area.x, area.y, area.w, 2.0f * s }, functions::with_alpha(kit_accent, alpha));
		}

		if (slot.item && static_cast<std::int32_t>(index) != drag_slot)
		{
			const auto& definition{ item_definitions[slot.item] };

			draw_item(area, slot.item, alpha, s);

			if (slot.amount > 1u)
			{
				char text[16]{};

				std::snprintf(text, sizeof(text), "%u", slot.amount);

				canvas.text(structures::font_bold, { area.x + area.w - 6.0f * s, area.y + area.h - 11.0f * s }, 14.0f * s, functions::with_alpha(kit_text, alpha), text, structures::align_right | structures::align_middle);
			}

			if (definition.stack == 1u && definition.category != structures::item_category_construction)
			{
				const structures::rect_s wear{ area.x + 6.0f * s, area.y + area.h - 6.0f * s, area.w - 12.0f * s, 2.0f * s };

				canvas.rect(wear, functions::rgba(255u, 255u, 255u, static_cast<std::uint32_t>(alpha * 30.0f)));
				canvas.rect({ wear.x, wear.y, wear.w * mathematics.saturate(slot.condition), wear.h }, functions::with_alpha(slot.condition < 0.25f ? kit_danger : kit_good, alpha * 0.85f));
			}
		}

		if (hovered)
		{
			hover_slot = static_cast<std::int32_t>(index);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_item(structures::rect_s area, std::uint32_t item, std::float_t alpha, std::float_t s)
	{
		if (icon_view && icon_table && item < structures::item_count && icon_table[item])
		{
			const auto cell{ 1.0f / static_cast<std::float_t>(item_icon_columns) };
			const auto side{ std::min(area.w, area.h) - 16.0f * s };
			const structures::vec2_s corner{ static_cast<std::float_t>(item % item_icon_columns) * cell, static_cast<std::float_t>(item / item_icon_columns) * cell };

			canvas.image(icon_view, { area.x + (area.w - side) * 0.5f, area.y + (area.h - side) * 0.5f, side, side }, corner, { corner.x + cell, corner.y + cell }, functions::with_alpha(0xFFFFFFFFu, alpha));
		}

		else
		{
			char name[64]{};
			char lines[3][160]{};

			kit.upper(item_definitions[std::min(item, static_cast<std::uint32_t>(structures::item_count) - 1u)].name, name, sizeof(name));

			const auto size{ std::clamp(area.w * 0.17f, 11.0f * s, 14.0f * s) };
			const auto count{ kit.wrap(name, structures::font_condensed, size, area.w - 12.0f * s, lines, 3u) };

			for (auto line{ 0u }; line < count; line++)
			{
				canvas.text(structures::font_condensed, { area.x + area.w * 0.5f, area.y + area.h * 0.5f + (static_cast<std::float_t>(line) - static_cast<std::float_t>(count - 1u) * 0.5f) * size * 1.15f - s }, size, functions::with_alpha(kit_dim, alpha), lines[line], structures::align_center | structures::align_middle);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::open_keypad(std::int32_t door, bool setting)
	{
		keypad_door = door;
		keypad_setting = setting;
		keypad_entry[0] = 0;

		platform.set_mouse_captured(false);

		mixer.play_2d(structures::sound_ui_open, 0.45f, 1.1f);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::close_keypad()
	{
		keypad_door = -1;
		keypad_entry[0] = 0;

		platform.set_mouse_captured(survival.inventory_open == false && chatting == false && application.options.capture[0] == 0);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::submit_keypad()
	{
		const auto door{ static_cast<std::uint32_t>(keypad_door) };
		const auto code{ static_cast<std::uint32_t>(std::atoi(keypad_entry)) };

		if (client.connected())
		{
			client.request(structures::request_code, static_cast<std::uint16_t>(door), static_cast<std::uint16_t>(code));
		}

		else if (const auto result{ building.enter_code(door, 0u, code) }; result >= 0)
		{
			survival.post(result == 2 ? "Code set" : (result == 1 ? "Code accepted" : "Wrong code"), 0);
		}

		close_keypad();
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_keypad(std::float_t s)
	{
		const structures::rect_s area{ (canvas.screen_width - 380.0f * s) * 0.5f, (canvas.screen_height - 560.0f * s) * 0.5f, 380.0f * s, 560.0f * s };
		const auto key_width{ 96.0f * s };
		const auto key_height{ 60.0f * s };
		const auto keys_left{ area.x + (area.w - key_width * 3.0f - 20.0f * s) * 0.5f };

		auto length{ std::strlen(keypad_entry) };
		auto pressed{ -1 };

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(0u, 0u, 0u, 130u));

		kit.panel(area, functions::rgba(13u, 14u, 16u, 248u));

		canvas.rect({ area.x, area.y, area.w, 3.0f * s }, kit_accent);

		kit.caps(structures::font_condensed, { area.x + 34.0f * s, area.y + 44.0f * s }, 26.0f * s, kit_text, keypad_setting ? "Set a code" : "Enter the code", structures::align_left | structures::align_middle, kit_caps);
		kit.caps(structures::font_condensed, { area.x + 34.0f * s, area.y + 74.0f * s }, 13.0f * s, kit_faint, "Code lock   \xB7   four digits", structures::align_left | structures::align_middle, kit_wide);

		for (auto digit{ 0u }; digit < 4u; digit++)
		{
			const structures::rect_s box{ area.x + (area.w - 292.0f * s) * 0.5f + static_cast<std::float_t>(digit) * 76.0f * s, area.y + 102.0f * s, 64.0f * s, 72.0f * s };
			const char shown[2] = { digit < length ? keypad_entry[digit] : '\0', '\0' };

			canvas.rect(box, functions::rgba(0u, 0u, 0u, 130u));
			canvas.border(box, s, digit == length ? kit_accent : kit_line);
			canvas.text(structures::font_bold, { box.x + box.w * 0.5f, box.y + box.h * 0.5f - s }, 36.0f * s, kit_text, shown, structures::align_center | structures::align_middle);
		}

		for (auto key{ 0u }; key < 12u; key++)
		{
			const structures::rect_s button{ keys_left + static_cast<std::float_t>(key % 3u) * (key_width + 10.0f * s), area.y + 204.0f * s + static_cast<std::float_t>(key / 3u) * (key_height + 10.0f * s), key_width, key_height };

			if (kit.button(470 + static_cast<std::int32_t>(key), button, keypad_labels[key], key == 11u))
			{
				pressed = static_cast<std::int32_t>(key);
			}
		}

		for (auto index{ 0u }; index < platform.input.text_length; index++)
		{
			if (const auto character{ platform.input.text[index] }; character >= '0' && character <= '9')
			{
				pressed = character == '0' ? 10 : character - '1';

				kit.click(1.3f);
			}
		}

		if (pressed >= 0 && pressed != 9 && pressed != 11 && length < 4u)
		{
			keypad_entry[length++] = pressed == 10 ? '0' : static_cast<char>('1' + pressed);
			keypad_entry[length] = 0;
		}

		if ((pressed == 9 || platform.input.pressed[VK_BACK]) && length)
		{
			keypad_entry[pressed == 9 ? 0u : length - 1u] = 0;
		}

		kit.hint({ area.x + area.w * 0.5f, area.y + area.h - 34.0f * s }, "Esc", "Close", structures::align_center);

		if (platform.input.pressed[VK_ESCAPE])
		{
			platform.input.pressed[VK_ESCAPE] = false;

			close_keypad();
		}

		else if (std::strlen(keypad_entry) == 4u && (pressed == 11 || platform.input.pressed[VK_RETURN] || keypad_setting == false))
		{
			submit_keypad();
		}
	}
	/*
	//=====================================================================================
	*/
	structures::rect_s hud_c::sheet(std::float_t s)
	{
		const auto width{ std::min(1480.0f * s, canvas.screen_width - 160.0f * s) };

		return { (canvas.screen_width - width) * 0.5f, 90.0f * s, width, canvas.screen_height - 250.0f * s };
	}
	/*
	//=====================================================================================
	*/
	structures::rect_s hud_c::page_rect(std::float_t s)
	{
		const auto area{ sheet(s) };
		const auto offset{ static_cast<std::float_t>(hud_grid_columns) * hud_grid_slot * s + static_cast<std::float_t>(hud_grid_columns - 1u) * hud_slot_gap * s + 90.0f * s };

		return { area.x + offset, area.y, area.w - offset, area.h };
	}
	/*
	//=====================================================================================
	*/
	structures::rect_s hud_c::slot_rect(std::uint32_t index, std::float_t s)
	{
		const auto area{ sheet(s) };
		const auto step{ (hud_grid_slot + hud_slot_gap) * s };

		if (index >= container_address)
		{
			const auto page{ page_rect(s) };
			const auto slot{ index - container_address };
			const auto split{ survival.open_container >= 0 && building.containers[survival.open_container].kind != structures::container_storage && slot >= furnace_first_output };

			return { page.x + static_cast<std::float_t>(slot % hud_box_columns) * step, page.y + 112.0f * s + static_cast<std::float_t>(slot / hud_box_columns) * step + (split ? 34.0f * s : 0.0f), hud_grid_slot * s, hud_grid_slot * s };
		}

		if (index >= inventory_slots)
		{
			const auto size{ hud_belt_slot * s };
			const auto row{ size * static_cast<std::float_t>(hotbar_slots) + hud_slot_gap * s * static_cast<std::float_t>(hotbar_slots - 1u) };

			return { (canvas.screen_width - row) * 0.5f + static_cast<std::float_t>(index - inventory_slots) * (size + hud_slot_gap * s), canvas.screen_height - 36.0f * s - size, size, size };
		}

		return { area.x + static_cast<std::float_t>(index % hud_grid_columns) * step, area.y + 90.0f * s + static_cast<std::float_t>(index / hud_grid_columns) * step, hud_grid_slot * s, hud_grid_slot * s };
	}
	/*
	//=====================================================================================
	*/
	void hud_c::set_prompt(const char* text)
	{
		const std::pair<const char*, std::uint32_t> tokens[2] = { { "[E]", structures::bind_use }, { "[R]", structures::bind_rotate } };

		auto result{ std::string(text) };

		for (const auto& token : tokens)
		{
			if (const auto found{ result.find(token.first) }; found != std::string::npos && platform.bindings[token.second] != default_user_settings.bindings[token.second])
			{
				char key[32]{};

				menu.key_name(platform.bindings[token.second], key, sizeof(key));

				result.replace(found, std::strlen(token.first), std::string("[") + key + "]");
			}
		}

		std::snprintf(prompt, sizeof(prompt), "%s", result.c_str());
	}
}

//=====================================================================================
