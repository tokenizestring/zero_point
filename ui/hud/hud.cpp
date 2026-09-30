
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	hud_c hud;

	bool hud_c::create()
	{
		std::vector<std::uint32_t> texels(static_cast<std::size_t>(paper_size) * paper_size);

		const auto size{ static_cast<std::float_t>(paper_size) };

		for (auto row{ 0u }; row < paper_size; row++)
		{
			for (auto column{ 0u }; column < paper_size; column++)
			{
				const auto x{ static_cast<std::float_t>(column) };
				const auto y{ static_cast<std::float_t>(row) };
				const auto edge{ std::min(std::min(x, y), std::min(size - 1.0f - x, size - 1.0f - y)) };
				const auto tear{ edge - 3.0f - chart.fractal(x / 7.0f, y / 7.0f, 3u, 71u) * 13.0f };
				const auto fibre{ chart.fractal(x / 2.0f, y / 30.0f, 3u, 23u) - 0.5f };
				const auto stain{ mathematics.saturate(chart.fractal(x / 110.0f, y / 110.0f, 4u, 11u) * 1.6f - 0.62f) };
				const auto rim{ mathematics.saturate(1.0f - tear / 16.0f) };
				const auto base{ chart_paper * (1.0f + fibre * 0.07f) };
				const auto color{ mathematics.lerp(base, structures::vec3_s{ base.x * 0.78f, base.y * 0.66f, base.z * 0.5f }, mathematics.saturate(stain * 0.45f + rim * 0.55f)) };

				texels[static_cast<std::size_t>(row) * paper_size + column] = functions::rgba(static_cast<std::uint32_t>(mathematics.saturate(color.x) * 255.0f), static_cast<std::uint32_t>(mathematics.saturate(color.y) * 255.0f), static_cast<std::uint32_t>(mathematics.saturate(color.z) * 255.0f), static_cast<std::uint32_t>(mathematics.saturate(tear * 0.7f) * 255.0f));
			}
		}

		D3D11_TEXTURE2D_DESC description{};

		description.Width = paper_size;
		description.Height = paper_size;
		description.MipLevels = 0u;
		description.ArraySize = 1u;
		description.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
		description.SampleDesc.Count = 1u;
		description.Usage = D3D11_USAGE_DEFAULT;
		description.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_RENDER_TARGET;
		description.MiscFlags = D3D11_RESOURCE_MISC_GENERATE_MIPS;

		ID3D11Texture2D* texture{ nullptr };

		if (SUCCEEDED(gpu.device->CreateTexture2D(&description, nullptr, &texture)))
		{
			gpu.context->UpdateSubresource(texture, 0u, nullptr, texels.data(), paper_size * 4u, 0u);

			if (SUCCEEDED(gpu.device->CreateShaderResourceView(texture, nullptr, &paper)))
			{
				gpu.context->GenerateMips(paper);
			}

			functions::release(texture);
		}

		if (const auto table{ pak.find(item_icon_table) }; table && table->size >= structures::item_count)
		{
			icon_view = pak.create_texture(item_icon_atlas, 0u, false, false);
			icon_table = pak.data(table);
		}

		return paper != nullptr;
	}
	/*
	//=====================================================================================
	*/
	void hud_c::destroy()
	{
		functions::release(paper);
		functions::release(icon_view);

		icon_table = nullptr;
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
		const auto mouse{ platform.input.mouse_position };
		const structures::rect_s area{ (canvas.screen_width - 360.0f * s) * 0.5f, (canvas.screen_height - 500.0f * s) * 0.5f, 360.0f * s, 500.0f * s };
		const auto key_width{ 92.0f * s };
		const auto key_height{ 64.0f * s };

		auto length{ std::strlen(keypad_entry) };
		auto pressed{ -1 };

		card({ area.x + 10.0f * s, area.y + 14.0f * s, area.w, area.h }, functions::rgba(0u, 0u, 0u, 140u), 9u);
		card(area, ui_paper, 9u);

		canvas.text(structures::font_serif_caps, { area.x + area.w * 0.5f, area.y + 44.0f * s }, 30.0f * s, ui_ink, keypad_setting ? "Set a code" : "Enter the code", structures::align_center | structures::align_middle);

		for (auto digit{ 0u }; digit < 4u; digit++)
		{
			const structures::rect_s box{ area.x + 48.0f * s + static_cast<std::float_t>(digit) * 68.0f * s, area.y + 78.0f * s, 56.0f * s, 64.0f * s };
			const char shown[2] = { digit < length ? keypad_entry[digit] : '\0', '\0' };

			sketch(box, 1.4f * s, digit == length ? ui_red : ui_ink, 90u + digit);

			canvas.text(structures::font_hand_bold, { box.x + box.w * 0.5f, box.y + box.h * 0.5f }, 34.0f * s, ui_ink, shown, structures::align_center | structures::align_middle);
		}

		for (auto key{ 0u }; key < 12u; key++)
		{
			const structures::rect_s button{ area.x + 36.0f * s + static_cast<std::float_t>(key % 3u) * (key_width + 8.0f * s), area.y + 166.0f * s + static_cast<std::float_t>(key / 3u) * (key_height + 8.0f * s), key_width, key_height };
			const auto inside{ button.contains(mouse) };
			const char* labels[12] = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "clear", "0", "ok" };

			if (inside)
			{
				hatch(button, 1.0f, functions::rgba(36u, 27u, 20u, 46u), s);
			}

			sketch(button, 1.3f * s, inside ? ui_red : ui_ink, 100u + key);

			canvas.text(structures::font_hand_bold, { button.x + button.w * 0.5f, button.y + button.h * 0.5f }, (key == 9u || key == 11u ? 22.0f : 30.0f) * s, inside ? ui_red : ui_ink, labels[key], structures::align_center | structures::align_middle);

			pressed = inside && platform.input.pressed[VK_LBUTTON] ? static_cast<std::int32_t>(key) : pressed;
		}

		for (auto index{ 0u }; index < platform.input.text_length; index++)
		{
			const auto character{ platform.input.text[index] };

			pressed = character >= '1' && character <= '9' ? character - '1' : (character == '0' ? 10 : pressed);
		}

		if (pressed >= 0 && pressed != 9 && pressed != 11 && length < 4u)
		{
			keypad_entry[length++] = pressed == 10 ? '0' : static_cast<char>('1' + pressed);
			keypad_entry[length] = 0;

			mixer.play_2d(structures::sound_ui_click, 0.35f, 1.3f);
		}

		if ((pressed == 9 || platform.input.pressed[VK_BACK]) && length)
		{
			keypad_entry[pressed == 9 ? 0u : length - 1u] = 0;
		}

		canvas.text(structures::font_hand, { area.x + area.w * 0.5f, area.y + area.h - 26.0f * s }, 17.0f * s, ui_faded, "type or click   Esc to close", structures::align_center | structures::align_middle);

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
	void hud_c::draw_item(structures::rect_s area, std::uint32_t item, std::float_t s)
	{
		if (icon_view && icon_table && item < structures::item_count && icon_table[item])
		{
			const auto cell{ 1.0f / static_cast<std::float_t>(item_icon_columns) };
			const auto side{ std::min(area.w, area.h) - 10.0f * s };
			const structures::vec2_s corner{ static_cast<std::float_t>(item % item_icon_columns) * cell, static_cast<std::float_t>(item / item_icon_columns) * cell };

			canvas.image(icon_view, { area.x + (area.w - side) * 0.5f, area.y + (area.h - side) * 0.5f, side, side }, corner, { corner.x + cell, corner.y + cell }, 0xFFFFFFFFu);
		}

		else
		{
			const auto name{ item_definitions[std::min(item, static_cast<std::uint32_t>(structures::item_count) - 1u)].name };

			canvas.text(structures::font_hand, { area.x + area.w * 0.5f, area.y + area.h * 0.46f }, (std::strlen(name) > 11u ? 14.0f : 17.0f) * s, ui_ink, name, structures::align_center | structures::align_middle);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw(std::float_t delta)
	{
		const auto s{ canvas.scale };
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };

		if (survival.vitals.damage_flash > 0.01f)
		{
			const auto alpha{ static_cast<std::uint32_t>(std::min(1.0f, survival.vitals.damage_flash) * 110.0f) };

			canvas.gradient({ 0.0f, 0.0f, width, height * 0.25f }, functions::rgba(120u, 0u, 0u, alpha), functions::rgba(120u, 0u, 0u, 0u));
			canvas.gradient({ 0.0f, height * 0.75f, width, height * 0.25f }, functions::rgba(120u, 0u, 0u, 0u), functions::rgba(120u, 0u, 0u, alpha));
		}

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

			if (survival.inventory_open == false && chart.open == false)
			{
				if (weapons.aim < 0.5f)
				{
					canvas.circle({ width * 0.5f, height * 0.5f }, 2.6f * s, functions::rgba(0u, 0u, 0u, 150u));
					canvas.circle({ width * 0.5f, height * 0.5f }, 1.6f * s, functions::rgba(240u, 232u, 214u, 230u));
				}

				if (combat.hit_marker > 0.01f)
				{
					const auto alpha{ static_cast<std::uint32_t>(combat.hit_marker * 235.0f) };
					const auto color{ combat.kill_marker > 0.01f ? functions::rgba(200u, 44u, 30u, alpha) : functions::rgba(245u, 238u, 222u, alpha) };

					for (auto corner{ 0u }; corner < 4u; corner++)
					{
						const structures::vec2_s direction{ corner & 1u ? 1.0f : -1.0f, corner & 2u ? 1.0f : -1.0f };

						canvas.line(structures::vec2_s{ width * 0.5f, height * 0.5f } + direction * (6.0f * s), structures::vec2_s{ width * 0.5f, height * 0.5f } + direction * (14.0f * s), 2.0f * s, color);
					}
				}

				if (prompt[0])
				{
					canvas.text_shadowed(structures::font_hand, { width * 0.5f, height * 0.5f + 46.0f * s }, 26.0f * s, ui_cream, prompt, structures::align_center | structures::align_middle);
				}

				draw_compass(s);
			}

			draw_vitals(s);

			if (survival.inventory_open == false && chart.open == false && client.connected() == false)
			{
				draw_goal(s);
			}

			if (client.connected())
			{
				draw_names(s);

				draw_hurt(s);

				draw_chat(s);
			}

			draw_ammo(s);

			draw_queue(s);

			draw_notifications(s);

			if (survival.inventory_open)
			{
				draw_inventory(s);
			}

			draw_hotbar(s);

			chart.draw(s);

			if (keypad_door >= 0)
			{
				draw_keypad(s);
			}
		}

		prompt[0] = 0;
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
	void hud_c::draw_chat(std::float_t s)
	{
		const auto left{ 24.0f * s };
		const auto bottom{ canvas.screen_height - 24.0f * s - 136.0f * s - 28.0f * s };

		auto row{ 0.0f };

		if (chatting)
		{
			char line[net_chat_length + 16]{};

			std::snprintf(line, sizeof(line), "Say: %s%s", chat_text, std::fmod(client.clock, 1.0f) < 0.55f ? "|" : "");

			canvas.rect({ left - 8.0f * s, bottom - 16.0f * s, 520.0f * s, 32.0f * s }, functions::rgba(20u, 14u, 10u, 150u));

			canvas.text_shadowed(structures::font_hand, { left, bottom }, 22.0f * s, ui_cream, line, structures::align_left | structures::align_middle);

			row += 1.0f;
		}

		for (auto index{ 0u }; index < net_chat_lines; index++)
		{
			const auto shown{ chatting ? 1.0f : mathematics.saturate(client.chat_times[index] / 2.0f) };

			if (client.chat_lines[index][0] && shown > 0.0f)
			{
				canvas.text_shadowed(structures::font_hand, { left, bottom - row * 26.0f * s }, 21.0f * s, functions::with_alpha(ui_cream, shown), client.chat_lines[index], structures::align_left | structures::align_middle);

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

					canvas.text_shadowed(structures::font_hand, point, 20.0f * s, functions::with_alpha(ui_cream, fade), remote.name, structures::align_center | structures::align_middle);
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
			const auto side{ mathematics.dot(offset, renderer.camera.right) };
			const auto ahead{ mathematics.dot(offset, renderer.camera.forward) };
			const auto angle{ std::atan2(side, ahead) };
			const auto alpha{ mathematics.saturate(hurt_timer / 0.6f) };
			const structures::vec2_s center{ canvas.screen_width * 0.5f, canvas.screen_height * 0.5f };
			const structures::vec2_s direction{ std::sin(angle), -std::cos(angle) };
			const structures::vec2_s across{ -direction.y, direction.x };

			for (auto segment{ -3 }; segment <= 3; segment++)
			{
				const auto spread{ static_cast<std::float_t>(segment) * 0.07f };
				const auto tangent{ direction * std::cos(spread) + across * std::sin(spread) };

				canvas.line(center + tangent * (120.0f * s), center + tangent * (138.0f * s), 5.0f * s, functions::rgba(190u, 30u, 20u, static_cast<std::uint32_t>(alpha * (220.0f - std::fabs(static_cast<std::float_t>(segment)) * 40.0f))));
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_compass(std::float_t s)
	{
		const auto middle{ canvas.screen_width * 0.5f };
		const auto top{ 12.0f * s };
		const auto reach{ compass_width * 0.5f * s };
		const auto heading{ mathematics.wrap_angle(player.yaw) };
		const structures::vec2_s feet{ player.state.position.x, player.state.position.z };
		const auto shadow{ functions::rgba(0u, 0u, 0u, 255u) };

		char label[16]{};

		canvas.gradient_horizontal({ middle - reach, top, reach, 52.0f * s }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, 60u));
		canvas.gradient_horizontal({ middle, top, reach, 52.0f * s }, functions::rgba(0u, 0u, 0u, 60u), functions::rgba(0u, 0u, 0u, 0u));

		for (auto degree{ 0u }; degree < 360u; degree += 5u)
		{
			const auto offset{ mathematics.wrap_angle(degrees_to_radians(static_cast<std::float_t>(degree)) - heading) / degrees_to_radians(1.0f) };

			if (std::fabs(offset) < compass_span)
			{
				const auto x{ middle + offset / compass_span * reach };
				const auto fade{ 1.0f - std::pow(std::fabs(offset) / compass_span, 3.0f) };
				const auto length{ degree % 45u == 0u ? 10.0f : (degree % 15u == 0u ? 6.0f : 3.5f) };

				canvas.line({ x + s, top + 35.0f * s }, { x + s, top + (35.0f + length) * s }, 1.8f * s, functions::with_alpha(shadow, fade * 0.5f));
				canvas.line({ x, top + 34.0f * s }, { x, top + (34.0f + length) * s }, 1.8f * s, functions::with_alpha(ui_cream, fade));

				if (degree % 45u == 0u)
				{
					canvas.text_shadowed(structures::font_serif_caps, { x, top + 17.0f * s }, (degree % 90u == 0u ? 28.0f : 20.0f) * s, functions::with_alpha(degree == 0u ? functions::rgba(226u, 80u, 58u, 255u) : ui_cream, fade), compass_points[degree / 45u], structures::align_center | structures::align_middle);
				}

				else if (degree % 15u == 0u)
				{
					std::snprintf(label, sizeof(label), "%u", degree);

					canvas.text_shadowed(structures::font_serif, { x, top + 19.0f * s }, 15.0f * s, functions::with_alpha(ui_cream, fade * 0.8f), label, structures::align_center | structures::align_middle);
				}
			}
		}

		canvas.line({ middle - 6.0f * s, top + 55.0f * s }, { middle, top + 49.0f * s }, 2.0f * s, ui_cream);
		canvas.line({ middle, top + 49.0f * s }, { middle + 6.0f * s, top + 55.0f * s }, 2.0f * s, ui_cream);

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

				compass_mark({ middle + bearing / compass_span * reach, top + 72.0f * s }, 1.0f - std::pow(std::fabs(bearing) / compass_span, 3.0f), functions::rgba(168u, 202u, 244u, 245u), label, mathematics.length(chart.pins[index].position - feet), focused == static_cast<std::int32_t>(index), s);
			}
		}

		if (const auto bearing{ compass_bearing(chart.grave) }; chart.grave_marked && std::fabs(bearing) < compass_span)
		{
			compass_mark({ middle + bearing / compass_span * reach, top + 72.0f * s }, 1.0f - std::pow(std::fabs(bearing) / compass_span, 3.0f), functions::rgba(228u, 84u, 60u, 245u), "+", mathematics.length(chart.grave - feet), focused == -1, s);
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

		std::snprintf(metres, sizeof(metres), "%.0fm", distance);

		canvas.circle(point, 11.0f * s, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(fade * 90.0f)));
		canvas.ring(point, 11.0f * s, 2.0f * s, -1.0f, 7.5f, functions::with_alpha(color, fade));
		canvas.text_shadowed(structures::font_hand, point, 18.0f * s, functions::with_alpha(color, fade), label, structures::align_center | structures::align_middle);

		if (focused)
		{
			canvas.text_shadowed(structures::font_hand, point + structures::vec2_s{ 0.0f, 23.0f * s }, 17.0f * s, functions::with_alpha(ui_cream, fade), metres, structures::align_center | structures::align_middle);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_death(std::float_t s)
	{
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const structures::rect_s note{ width * 0.5f - 330.0f * s, height * 0.42f - 150.0f * s, 660.0f * s, 300.0f * s };
		const auto cause{ std::min<std::uint32_t>(client.connected() ? client.death_cause : survival.harm, static_cast<std::uint32_t>(std::size(death_lines) - 1u)) };

		char key[32]{};
		char cause_line[96]{};
		char wake_line[128]{};

		menu.key_name(platform.bindings[structures::bind_jump], key, sizeof(key));

		std::snprintf(cause_line, sizeof(cause_line), client.connected() && client.death_killer[0] ? "Killed by %s." : "%s", client.connected() && client.death_killer[0] ? client.death_killer : death_lines[cause]);
		std::snprintf(wake_line, sizeof(wake_line), building.bag >= 0 && building.placed[building.bag].destroyed == false ? "Press %s to wake in your sleeping bag" : "Press %s to wake on the shore", key);

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(12u, 5u, 4u, 205u));

		card(note, ui_paper, 1u);

		canvas.text(structures::font_serif_caps, { note.x + note.w * 0.5f, note.y + 74.0f * s }, 58.0f * s, ui_red, "You are dead", structures::align_center | structures::align_middle);
		canvas.text(structures::font_hand_bold, { note.x + note.w * 0.5f, note.y + 140.0f * s }, 26.0f * s, ui_ink, cause_line, structures::align_center | structures::align_middle);
		canvas.text(structures::font_hand, { note.x + note.w * 0.5f, note.y + 184.0f * s }, 22.0f * s, ui_faded, "Everything you carried is in a bag where you fell.", structures::align_center | structures::align_middle);
		canvas.text(structures::font_hand, { note.x + note.w * 0.5f, note.y + 240.0f * s }, 22.0f * s, ui_ink, wake_line, structures::align_center | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_ending(std::float_t s)
	{
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const structures::rect_s note{ width * 0.5f - 360.0f * s, height * 0.42f - 140.0f * s, 720.0f * s, 280.0f * s };

		char text[128]{};

		std::snprintf(text, sizeof(text), "The Morning Star took you off the island on day %u.", story.day);

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(10u, 12u, 14u, 170u));

		card(note, ui_paper, 6u);

		canvas.text(structures::font_serif_caps, { note.x + note.w * 0.5f, note.y + 78.0f * s }, 60.0f * s, ui_ink, "Rescued", structures::align_center | structures::align_middle);
		canvas.text(structures::font_hand, { note.x + note.w * 0.5f, note.y + 148.0f * s }, 26.0f * s, ui_ink, text, structures::align_center | structures::align_middle);
		canvas.text(structures::font_hand, { note.x + note.w * 0.5f, note.y + 208.0f * s }, 22.0f * s, ui_faded, "Press space to keep playing", structures::align_center | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_goal(std::float_t s)
	{
		if (story.step < goal_count)
		{
			const auto& goal{ goals[story.step] };
			const auto flash{ mathematics.saturate(story.done_flash / 2.5f) };
			const auto width{ canvas.screen_width };

			char lines[4][128]{};
			char day[32]{};
			char progress[64]{};

			const auto count{ wrap(goal.hint, structures::font_hand, 19.0f * s, 318.0f * s, lines, 4u) };

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

			std::snprintf(day, sizeof(day), "Day %u", story.day);

			const structures::rect_s area{ width - 24.0f * s - 370.0f * s, 24.0f * s, 370.0f * s, 76.0f * s + static_cast<std::float_t>(count) * 23.0f * s + (progress[0] ? 26.0f * s : 0.0f) };

			card(area, ui_paper, 5u);

			canvas.text(structures::font_serif_caps, { area.x + area.w - 20.0f * s, area.y + 28.0f * s }, 18.0f * s, ui_faded, day, structures::align_right | structures::align_middle);
			canvas.text(structures::font_hand_bold, { area.x + 20.0f * s, area.y + 30.0f * s }, 25.0f * s, flash > 0.0f ? functions::with_alpha(ui_red, 0.6f + 0.4f * flash) : ui_ink, goal.title, structures::align_left | structures::align_middle);

			for (auto line{ 0u }; line < count; line++)
			{
				canvas.text(structures::font_hand, { area.x + 20.0f * s, area.y + 62.0f * s + static_cast<std::float_t>(line) * 23.0f * s }, 19.0f * s, ui_ink, lines[line], structures::align_left | structures::align_middle);
			}

			if (progress[0])
			{
				canvas.text(structures::font_hand_bold, { area.x + 20.0f * s, area.y + 66.0f * s + static_cast<std::float_t>(count) * 23.0f * s }, 18.0f * s, ui_blue, progress, structures::align_left | structures::align_middle);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t hud_c::wrap(const char* text, structures::font_e font_index, std::float_t size, std::float_t limit, char (*lines)[128], std::uint32_t capacity)
	{
		char word[64]{};
		char trial[128]{};

		auto count{ 0u };
		auto cursor{ text };

		lines[0][0] = 0;

		while (*cursor && count < capacity)
		{
			auto length{ 0u };

			while (cursor[length] && cursor[length] != ' ' && length < sizeof(word) - 1u)
			{
				word[length] = cursor[length];
				length++;
			}

			word[length] = 0;

			std::snprintf(trial, sizeof(trial), "%s%s%s", lines[count], lines[count][0] ? " " : "", word);

			if (font.measure(font_index, size, trial) > limit && lines[count][0] && count + 1u < capacity)
			{
				count++;

				std::snprintf(lines[count], sizeof(lines[count]), "%s", word);
			}

			else
			{
				std::snprintf(lines[count], sizeof(lines[count]), "%s", trial);
			}

			cursor += length;

			while (*cursor == ' ')
			{
				cursor++;
			}
		}

		return lines[0][0] ? count + 1u : 0u;
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_vitals(std::float_t s)
	{
		const structures::rect_s area{ 24.0f * s, canvas.screen_height - 24.0f * s - 136.0f * s, 330.0f * s, 136.0f * s };
		const std::float_t values[3] = { survival.vitals.health, survival.vitals.hydration, survival.vitals.calories };
		const std::float_t maxima[3] = { maximum_health, maximum_hydration, maximum_calories };
		const std::uint32_t colors[3] = { ui_red, ui_blue, ui_ochre };

		card(area, ui_paper, 2u);

		for (auto vital{ 0u }; vital < 3u; vital++)
		{
			draw_bar({ area.x + 22.0f * s, area.y + 26.0f * s + static_cast<std::float_t>(vital) * 34.0f * s, area.w - 44.0f * s, 22.0f * s }, vital, values[vital], maxima[vital], colors[vital], s);
		}

		if (survival.vitals.breath < 0.999f)
		{
			const structures::rect_s air{ area.x, area.y - 56.0f * s, area.w, 46.0f * s };

			card(air, ui_paper, 4u);

			draw_bar({ air.x + 22.0f * s, air.y + 12.0f * s, air.w - 44.0f * s, 22.0f * s }, 3u, survival.vitals.breath * 100.0f, 100.0f, ui_blue, s);
		}

		draw_climate(area, s);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_climate(structures::rect_s vitals_area, std::float_t s)
	{
		const auto cold{ survival.climate.temperature < climate_cold };
		const auto hot{ survival.climate.temperature > climate_hot };
		const auto wet{ survival.climate.wetness > 0.05f };

		if (survival.vitals.dead == false && (cold || hot || wet))
		{
			char degrees[24]{};
			char soaked[24]{};

			const auto rows{ static_cast<std::float_t>((cold || hot ? 1u : 0u) + (wet ? 1u : 0u)) };
			const auto lift{ survival.vitals.breath < 0.999f ? 56.0f * s : 0.0f };
			const auto height{ (14.0f + rows * 32.0f) * s };
			const structures::rect_s area{ vitals_area.x, vitals_area.y - lift - height - 10.0f * s, vitals_area.w, height };

			std::snprintf(degrees, sizeof(degrees), "%.0f\xB0" "C", survival.climate.temperature);
			std::snprintf(soaked, sizeof(soaked), "%.0f%%", survival.climate.wetness * 100.0f);

			card(area, ui_paper, 5u);

			auto row{ area.y + 23.0f * s };

			if (cold || hot)
			{
				const auto tone{ cold ? ui_blue : ui_red };

				canvas.text(structures::font_hand, { area.x + 22.0f * s, row }, 21.0f * s, tone, cold ? (survival.climate.temperature < climate_freezing ? "Freezing" : "Cold") : "Overheating", structures::align_left | structures::align_middle);
				canvas.text(structures::font_hand_bold, { area.x + area.w - 22.0f * s, row }, 21.0f * s, tone, degrees, structures::align_right | structures::align_middle);

				row += 32.0f * s;
			}

			if (wet)
			{
				canvas.text(structures::font_hand, { area.x + 22.0f * s, row }, 21.0f * s, ui_ink, "Wet", structures::align_left | structures::align_middle);
				canvas.text(structures::font_hand_bold, { area.x + area.w - 22.0f * s, row }, 21.0f * s, ui_ink, soaked, structures::align_right | structures::align_middle);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_bar(structures::rect_s area, std::uint32_t label, std::float_t value, std::float_t maximum, std::uint32_t color, std::float_t s)
	{
		char text[32]{};

		const auto fraction{ std::clamp(value / maximum, 0.0f, 1.0f) };
		const auto low{ fraction < 0.25f };
		const structures::rect_s bar{ area.x + 84.0f * s, area.y + 3.0f * s, area.w - 140.0f * s, area.h - 6.0f * s };

		std::snprintf(text, sizeof(text), "%.0f", value);

		canvas.text(structures::font_hand, { area.x, area.y + area.h * 0.5f }, 21.0f * s, low ? ui_red : ui_ink, ui_vital_labels[label], structures::align_left | structures::align_middle);

		hatch(bar, fraction, color, s);
		sketch(bar, 1.3f * s, ui_ink, label * 7u + 3u);

		canvas.text(structures::font_hand_bold, { area.x + area.w, area.y + area.h * 0.5f }, 21.0f * s, low ? ui_red : ui_ink, text, structures::align_right | structures::align_middle);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_ammo(std::float_t s)
	{
		if (weapons.weapon != structures::weapon_none)
		{
			char loaded[16]{};
			char spare[24]{};

			const auto& held{ survival.held() };
			const structures::rect_s area{ canvas.screen_width - 24.0f * s - 270.0f * s, canvas.screen_height - 24.0f * s - 100.0f * s, 270.0f * s, 100.0f * s };

			std::snprintf(loaded, sizeof(loaded), "%u", held.loaded);
			std::snprintf(spare, sizeof(spare), "/ %u", survival.count(weapon_definitions[weapons.weapon].ammo));

			card(area, ui_paper, 3u);

			canvas.text(structures::font_serif_caps, { area.x + 22.0f * s, area.y + 28.0f * s }, 24.0f * s, ui_ink, item_definitions[held.item].name, structures::align_left | structures::align_middle);

			if (weapons.reloading > 0.0f)
			{
				canvas.text(structures::font_hand, { area.x + 22.0f * s, area.y + 66.0f * s }, 26.0f * s, ui_red, "reloading...", structures::align_left | structures::align_middle);
			}

			else
			{
				const auto right{ canvas.text(structures::font_hand_bold, { area.x + 22.0f * s, area.y + 64.0f * s }, 42.0f * s, held.loaded ? ui_ink : ui_red, loaded, structures::align_left | structures::align_middle) };

				canvas.text(structures::font_hand, { area.x + 30.0f * s + right, area.y + 68.0f * s }, 24.0f * s, ui_faded, spare, structures::align_left | structures::align_middle);
				canvas.text(structures::font_hand, { area.x + area.w - 22.0f * s, area.y + 68.0f * s }, 19.0f * s, ui_faded, item_definitions[weapon_definitions[weapons.weapon].ammo].name, structures::align_right | structures::align_middle);
			}
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

		for (auto side{ 0u }; side < 4u; side++)
		{
			const structures::vec2_s direction{ side < 2u ? (side ? 1.0f : -1.0f) : 0.0f, side < 2u ? 0.0f : (side == 2u ? -1.0f : 1.0f) };

			canvas.line(center + direction * (radius * 0.3f), center + direction * radius, 5.0f * s, black);
		}
	}
	/*
	//=====================================================================================
	*/
	structures::rect_s hud_c::journal(std::float_t s)
	{
		const auto width{ std::min(1240.0f * s, canvas.screen_width - 60.0f * s) };
		const auto height{ std::min(660.0f * s, canvas.screen_height - 150.0f * s) };

		return { (canvas.screen_width - width) * 0.5f, std::max(20.0f * s, canvas.screen_height - 128.0f * s - height), width, height };
	}
	/*
	//=====================================================================================
	*/
	structures::rect_s hud_c::slot_rect(std::uint32_t index, std::float_t s)
	{
		const auto width{ 86.0f * s };
		const auto height{ 72.0f * s };
		const auto gap{ 9.0f * s };

		if (index >= container_address)
		{
			const auto book{ journal(s) };
			const auto slot{ index - container_address };

			return { book.x + book.w * 0.5f + 44.0f * s + static_cast<std::float_t>(slot % 4u) * (width + gap), book.y + 118.0f * s + static_cast<std::float_t>(slot / 4u) * (height + gap) + (building.containers[survival.open_container].kind != structures::container_storage && slot >= furnace_first_output ? 30.0f * s : 0.0f), width, height };
		}

		if (index >= inventory_slots)
		{
			const auto row_width{ width * static_cast<std::float_t>(hotbar_slots) + gap * static_cast<std::float_t>(hotbar_slots - 1u) };

			return { canvas.screen_width * 0.5f - row_width * 0.5f + static_cast<std::float_t>(index - inventory_slots) * (width + gap), canvas.screen_height - 22.0f * s - height, width, height };
		}

		const auto book{ journal(s) };

		return { book.x + 40.0f * s + static_cast<std::float_t>(index % 6u) * (width + gap), book.y + 104.0f * s + static_cast<std::float_t>(index / 6u) * (height + gap), width, height };
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_slot(structures::rect_s area, std::uint32_t index, bool active, std::float_t s)
	{
		const auto& slot{ survival.slot(index) };
		const auto hovered{ area.contains(platform.input.mouse_position) && survival.inventory_open };

		card(area, hovered ? functions::rgba(255u, 250u, 236u, 250u) : ui_paper, index);

		sketch({ area.x + 3.0f * s, area.y + 3.0f * s, area.w - 6.0f * s, area.h - 6.0f * s }, 1.0f * s, ui_faded, index * 13u + 5u);

		if (slot.item && static_cast<std::int32_t>(index) != drag_slot)
		{
			char text[32]{};

			const auto& definition{ item_definitions[slot.item] };

			draw_item(area, slot.item, s);

			if (slot.amount > 1u)
			{
				std::snprintf(text, sizeof(text), "x%u", slot.amount);

				canvas.text(structures::font_hand_bold, { area.x + area.w - 7.0f * s, area.y + area.h - 6.0f * s }, 17.0f * s, ui_ink, text, structures::align_right | structures::align_bottom);
			}

			if (definition.stack == 1u && definition.category != structures::item_category_construction)
			{
				canvas.line({ area.x + 9.0f * s, area.y + area.h - 9.0f * s }, { area.x + 9.0f * s + (area.w - 18.0f * s) * slot.condition, area.y + area.h - 9.0f * s }, 2.0f * s, slot.condition < 0.25f ? ui_red : ui_faded);
			}
		}

		if (active)
		{
			loop(area, ui_red, s);
		}

		if (hovered)
		{
			hover_slot = static_cast<std::int32_t>(index);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_hotbar(std::float_t s)
	{
		char number[4]{};

		for (auto index{ 0u }; index < hotbar_slots; index++)
		{
			const auto active{ index == survival.active_slot };
			const auto base{ slot_rect(inventory_slots + index, s) };
			const structures::rect_s area{ base.x, base.y - (active ? 7.0f * s : 0.0f), base.w, base.h };

			draw_slot(area, inventory_slots + index, active, s);

			std::snprintf(number, sizeof(number), "%u", index + 1u);

			canvas.text(structures::font_hand, { area.x + 9.0f * s, area.y + 12.0f * s }, 15.0f * s, ui_faded, number, structures::align_left | structures::align_middle);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_notifications(std::float_t s)
	{
		char text[96]{};

		auto y{ canvas.screen_height - 186.0f * s };

		for (const auto& notification : survival.notifications)
		{
			if (notification.text[0] && notification.age < notification_time)
			{
				const auto fade{ std::clamp((notification_time - notification.age) * 2.0f, 0.0f, 1.0f) };

				if (notification.amount > 0)
				{
					std::snprintf(text, sizeof(text), "+%d  %s", notification.amount, notification.text);
				}

				else
				{
					std::snprintf(text, sizeof(text), "%s", notification.text);
				}

				canvas.text_shadowed(structures::font_hand, { 34.0f * s, y }, 23.0f * s, functions::with_alpha(ui_cream, fade), text, structures::align_left | structures::align_middle);

				y -= 32.0f * s;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_queue(std::float_t s)
	{
		char text[96]{};

		for (auto index{ 0u }; index < survival.queue_count; index++)
		{
			const auto& job{ survival.queue[index] };
			const auto y{ canvas.screen_height - 150.0f * s - static_cast<std::float_t>(index) * 30.0f * s };

			std::snprintf(text, sizeof(text), "making %s  %.0fs", item_definitions[recipes[job.recipe].result].name, std::ceil(job.remaining));

			canvas.text_shadowed(structures::font_hand, { canvas.screen_width - 34.0f * s, y - (weapons.weapon != structures::weapon_none ? 20.0f * s : 0.0f) }, 22.0f * s, ui_cream, text, structures::align_right | structures::align_middle);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_inventory(std::float_t s)
	{
		const auto mouse{ platform.input.mouse_position };
		const auto book{ journal(s) };
		const structures::rect_s left{ book.x, book.y, book.w * 0.5f, book.h };
		const structures::rect_s right{ book.x + book.w * 0.5f, book.y, book.w * 0.5f, book.h };

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(0u, 0u, 0u, 120u));
		card({ left.x + 10.0f * s, left.y + 14.0f * s, left.w, left.h }, functions::rgba(0u, 0u, 0u, 140u), 0u);
		card({ right.x + 10.0f * s, right.y + 14.0f * s, right.w, right.h }, functions::rgba(0u, 0u, 0u, 140u), 1u);
		card(left, ui_paper, 0u);
		card(right, ui_paper, 1u);

		canvas.gradient_horizontal({ right.x - 26.0f * s, book.y + 10.0f * s, 26.0f * s, book.h - 20.0f * s }, functions::rgba(60u, 40u, 20u, 0u), functions::rgba(60u, 40u, 20u, 110u));
		canvas.gradient_horizontal({ right.x, book.y + 10.0f * s, 26.0f * s, book.h - 20.0f * s }, functions::rgba(60u, 40u, 20u, 110u), functions::rgba(60u, 40u, 20u, 0u));

		canvas.text(structures::font_serif_caps, { left.x + 42.0f * s, left.y + 56.0f * s }, 38.0f * s, ui_ink, "Satchel", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand, { left.x + left.w - 42.0f * s, left.y + 58.0f * s }, 19.0f * s, ui_faded, "drag to move - right-click to use", structures::align_right | structures::align_middle);

		hover_slot = -1;
		hover_recipe = -1;

		for (auto index{ 0u }; index < inventory_slots; index++)
		{
			draw_slot(slot_rect(index, s), index, false, s);
		}

		for (auto index{ inventory_slots }; index < total_slots; index++)
		{
			hover_slot = slot_rect(index, s).contains(mouse) ? static_cast<std::int32_t>(index) : hover_slot;
		}

		canvas.text(structures::font_hand, { left.x + 42.0f * s, left.y + left.h - 44.0f * s }, 21.0f * s, ui_faded, "Keep what you can carry. Leave the rest to the tide.", structures::align_left | structures::align_middle);

		if (survival.open_container >= 0)
		{
			draw_container(right, s);
		}

		else
		{
			draw_crafting(right, s);
		}

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
			const structures::rect_s ghost{ mouse.x - 43.0f * s, mouse.y - 36.0f * s, 86.0f * s, 72.0f * s };

			card(ghost, functions::rgba(255u, 250u, 236u, 235u), 3u);

			draw_item(ghost, survival.slot(static_cast<std::uint32_t>(drag_slot)).item, s);
		}

		else if (hover_slot >= 0 && survival.slot(static_cast<std::uint32_t>(hover_slot)).item)
		{
			const auto& definition{ item_definitions[survival.slot(static_cast<std::uint32_t>(hover_slot)).item] };
			const structures::rect_s tip{ mouse.x + 18.0f * s, mouse.y + 14.0f * s, 360.0f * s, 78.0f * s };

			card(tip, functions::rgba(255u, 252u, 242u, 250u), 2u);

			canvas.text(structures::font_serif_caps, { tip.x + 18.0f * s, tip.y + 26.0f * s }, 22.0f * s, ui_ink, definition.name, structures::align_left | structures::align_middle);
			canvas.text(structures::font_hand, { tip.x + 18.0f * s, tip.y + 54.0f * s }, 18.0f * s, ui_faded, definition.description, structures::align_left | structures::align_middle);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_crafting(structures::rect_s page, std::float_t s)
	{
		const auto mouse{ platform.input.mouse_position };
		const auto rows{ static_cast<std::float_t>(recipe_count) };
		const auto line_height{ std::min(28.0f * s, (page.h - 150.0f * s) / rows) };
		const auto bench{ survival.station() };
		const auto lab{ building.research_nearby(player.state.position) };

		char status[96]{};

		std::snprintf(status, sizeof(status), "%s%s", bench ? tier_names[bench] : "No workbench", lab ? "   research table" : "");

		canvas.text(structures::font_serif_caps, { page.x + 44.0f * s, page.y + 56.0f * s }, 38.0f * s, ui_ink, "Crafting", structures::align_left | structures::align_middle);
		canvas.text(structures::font_hand, { page.x + page.w - 44.0f * s, page.y + 58.0f * s }, 19.0f * s, bench ? ui_blue : ui_faded, status, structures::align_right | structures::align_middle);

		for (auto recipe{ 0u }; recipe < recipe_count; recipe++)
		{
			const structures::rect_s row{ page.x + 40.0f * s, page.y + 108.0f * s + static_cast<std::float_t>(recipe) * line_height, page.w - 80.0f * s, line_height };
			const auto& entry{ recipes[recipe] };
			const auto known{ survival.known[recipe] };
			const auto available{ survival.can_craft(recipe) };
			const auto hovered{ row.contains(mouse) };
			const auto affordable{ survival.count(structures::item_scrap) >= research_costs[entry.tier] };

			char cost[128]{};
			char part[48]{};

			if (known && entry.tier > bench)
			{
				std::snprintf(cost, sizeof(cost), "needs %s", tier_names[entry.tier]);
			}

			else if (known)
			{
				for (const auto& ingredient : entry.ingredients)
				{
					if (ingredient.item)
					{
						std::snprintf(part, sizeof(part), "%s%u %s", cost[0] ? ", " : "", ingredient.amount, item_definitions[ingredient.item].name);
						std::strncat(cost, part, sizeof(cost) - std::strlen(cost) - 1u);
					}
				}
			}

			else
			{
				std::snprintf(cost, sizeof(cost), lab ? "research for %u scrap" : "blueprint needed", research_costs[entry.tier]);
			}

			if (hovered)
			{
				hatch({ row.x - 6.0f * s, row.y + 2.0f * s, row.w + 12.0f * s, row.h - 4.0f * s }, 1.0f, functions::rgba(36u, 27u, 20u, 34u), s);

				canvas.line({ row.x - 24.0f * s, row.y + row.h * 0.5f }, { row.x - 10.0f * s, row.y + row.h * 0.5f }, 2.0f * s, ui_red);
				canvas.line({ row.x - 15.0f * s, row.y + row.h * 0.5f - 5.0f * s }, { row.x - 10.0f * s, row.y + row.h * 0.5f }, 2.0f * s, ui_red);
				canvas.line({ row.x - 15.0f * s, row.y + row.h * 0.5f + 5.0f * s }, { row.x - 10.0f * s, row.y + row.h * 0.5f }, 2.0f * s, ui_red);

				hover_recipe = static_cast<std::int32_t>(recipe);
			}

			canvas.text(structures::font_hand_bold, { row.x - 2.0f * s, row.y + row.h * 0.5f }, 15.0f * s, ui_faded, tier_marks[entry.tier], structures::align_right | structures::align_middle);
			canvas.text(structures::font_hand, { row.x + 6.0f * s, row.y + row.h * 0.5f }, 20.0f * s, available ? ui_ink : ui_faded, item_definitions[entry.result].name, structures::align_left | structures::align_middle);
			canvas.text(structures::font_hand, { row.x + row.w, row.y + row.h * 0.5f }, 17.0f * s, known ? (available ? ui_blue : functions::with_alpha(ui_red, 0.7f)) : (lab && affordable ? ui_ochre : ui_faded), cost, structures::align_right | structures::align_middle);
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

				mixer.play_2d(structures::sound_ui_click, 0.5f, 1.0f);
			}

			else
			{
				mixer.play_2d(structures::sound_ui_error, 0.4f, 1.0f);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::draw_container(structures::rect_s page, std::float_t s)
	{
		auto& container{ building.containers[survival.open_container] };

		const auto cooking{ container.kind == structures::container_campfire };

		canvas.text(structures::font_serif_caps, { page.x + 44.0f * s, page.y + 56.0f * s }, 38.0f * s, ui_ink, piece_definitions[building.placed[container.structure].piece].name, structures::align_left | structures::align_middle);

		for (auto index{ 0u }; index < container_slots; index++)
		{
			draw_slot(slot_rect(container_address + index, s), container_address + index, false, s);
		}

		if (container.kind != structures::container_storage)
		{
			const auto first{ slot_rect(container_address, s) };
			const auto output{ slot_rect(container_address + furnace_first_output, s) };
			const structures::rect_s button{ page.x + 44.0f * s, page.y + page.h - 96.0f * s, 220.0f * s, 52.0f * s };
			const auto hovered{ button.contains(platform.input.mouse_position) };
			const auto fueled{ container.slots[furnace_fuel_slot].item == structures::item_wood && container.slots[furnace_fuel_slot].amount > 0u };

			canvas.text(structures::font_hand, { first.x, first.y - 14.0f * s }, 18.0f * s, ui_faded, "wood", structures::align_left | structures::align_middle);
			canvas.text(structures::font_hand, { first.x + first.w + 9.0f * s, first.y - 14.0f * s }, 18.0f * s, ui_faded, cooking ? "raw food" : "ore", structures::align_left | structures::align_middle);
			canvas.text(structures::font_hand, { output.x, output.y - 14.0f * s }, 18.0f * s, container.burning ? ui_red : ui_faded, container.burning ? (cooking ? "cooked (cooking...)" : "output (smelting...)") : (cooking ? "cooked" : "output"), structures::align_left | structures::align_middle);

			if (hovered)
			{
				hatch(button, 1.0f, functions::rgba(36u, 27u, 20u, 40u), s);
			}

			sketch(button, 1.6f * s, container.burning ? ui_red : ui_ink, 91u);

			canvas.text(structures::font_hand_bold, { button.x + button.w * 0.5f, button.y + button.h * 0.5f }, 24.0f * s, container.burning ? ui_red : ui_ink, container.burning ? "Put it out" : "Light it", structures::align_center | structures::align_middle);

			if (hovered && platform.input.pressed[VK_LBUTTON])
			{
				if (container.burning || fueled)
				{
					container.burning = container.burning == false;

					mixer.play_2d(structures::sound_ui_click, 0.5f, container.burning ? 1.0f : 0.8f);

					if (client.connected())
					{
						client.request(structures::request_light, static_cast<std::uint16_t>(survival.open_container), container.burning ? 1u : 0u);
					}
				}

				else
				{
					survival.post(cooking ? "The fire needs wood" : "The furnace needs wood", 0);

					mixer.play_2d(structures::sound_ui_error, 0.4f, 1.0f);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::card(structures::rect_s area, std::uint32_t tint, std::uint32_t variant)
	{
		const auto flip_x{ (variant & 1u) != 0u };
		const auto flip_y{ (variant & 2u) != 0u };

		canvas.image(paper, area, { flip_x ? 1.0f : 0.0f, flip_y ? 1.0f : 0.0f }, { flip_x ? 0.0f : 1.0f, flip_y ? 0.0f : 1.0f }, tint);
	}
	/*
	//=====================================================================================
	*/
	void hud_c::sketch(structures::rect_s area, std::float_t thickness, std::uint32_t color, std::uint32_t seed)
	{
		const structures::vec2_s corners[4] = { { area.x, area.y }, { area.x + area.w, area.y }, { area.x + area.w, area.y + area.h }, { area.x, area.y + area.h } };

		for (auto edge{ 0u }; edge < 4u; edge++)
		{
			const auto& a{ corners[edge] };
			const auto& b{ corners[(edge + 1u) % 4u] };
			const auto direction{ mathematics.normalize(b - a) };
			const structures::vec2_s normal{ -direction.y, direction.x };
			const auto start{ a - direction * (1.5f + mathematics.hash_float(seed * 31u + edge) * 3.0f) * thickness };
			const auto end{ b + direction * (1.5f + mathematics.hash_float(seed * 37u + edge) * 3.0f) * thickness };
			const auto middle{ (start + end) * 0.5f + normal * ((mathematics.hash_float(seed * 41u + edge) - 0.5f) * 2.4f * thickness) };

			canvas.line(start, middle, thickness, color);
			canvas.line(middle, end, thickness, color);
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::hatch(structures::rect_s area, std::float_t fraction, std::uint32_t color, std::float_t s)
	{
		const auto filled{ area.w * std::clamp(fraction, 0.0f, 1.0f) };
		const auto spacing{ 4.0f * s };

		for (auto offset{ -area.h }; offset < filled; offset += spacing)
		{
			structures::vec2_s start{ area.x + offset, area.y + area.h };
			structures::vec2_s end{ area.x + offset + area.h, area.y };

			if (start.x < area.x)
			{
				start = { area.x, area.y + area.h - (area.x - start.x) };
			}

			if (end.x > area.x + filled)
			{
				end = { area.x + filled, area.y + (end.x - area.x - filled) };
			}

			if (end.x > start.x)
			{
				canvas.line(start, end, 1.5f * s, color);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void hud_c::loop(structures::rect_s area, std::uint32_t color, std::float_t s)
	{
		const structures::vec2_s center{ area.x + area.w * 0.5f, area.y + area.h * 0.5f };
		const structures::vec2_s radius{ area.w * 0.5f + 9.0f * s, area.h * 0.5f + 8.0f * s };

		auto previous{ center + structures::vec2_s{ std::cos(-2.4f) * radius.x, std::sin(-2.4f) * radius.y } };

		for (auto step{ 1u }; step <= 40u; step++)
		{
			const auto angle{ -2.4f + static_cast<std::float_t>(step) / 40.0f * (two_pi + 0.55f) };
			const auto grow{ 1.0f + static_cast<std::float_t>(step) / 40.0f * 0.07f };
			const structures::vec2_s point{ center.x + std::cos(angle) * radius.x * grow, center.y + std::sin(angle) * radius.y * grow };

			canvas.line(previous, point, 2.2f * s, color);

			previous = point;
		}
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
