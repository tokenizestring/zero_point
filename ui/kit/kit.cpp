
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	kit_c kit;

	void kit_c::begin(std::float_t frame_delta)
	{
		delta = frame_delta;
		clock += frame_delta;
		previous_hot = hot;
		hot = -1;
		clicked = false;
	}
	/*
	//=====================================================================================
	*/
	void kit_c::end()
	{
		if (hot >= 0 && hot != previous_hot)
		{
			mixer.play_2d(structures::sound_ui_click, kit_hover_volume * menu.user.interface_volume, 1.9f);
		}
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::inside(structures::rect_s area)
	{
		return blocked == false && area.contains(platform.input.mouse_position);
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::press(structures::rect_s area)
	{
		if (blocked == false && clicked == false && platform.input.pressed[VK_LBUTTON] && area.contains(platform.input.mouse_position))
		{
			clicked = true;

			platform.input.pressed[VK_LBUTTON] = false;

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	std::float_t kit_c::fade(std::int32_t id, bool on)
	{
		auto& value{ glow[static_cast<std::uint32_t>(id) % kit_slots] };

		value = mathematics.damp(value, on ? 1.0f : 0.0f, kit_fade_speed, delta);

		return value;
	}
	/*
	//=====================================================================================
	*/
	void kit_c::click(std::float_t pitch)
	{
		mixer.play_2d(structures::sound_ui_click, kit_click_volume * menu.user.interface_volume, pitch);
	}
	/*
	//=====================================================================================
	*/
	void kit_c::upper(const char* text, char* out, std::size_t capacity)
	{
		auto length{ 0u };

		for (; text[length] && length + 1u < capacity; length++)
		{
			out[length] = text[length] >= 'a' && text[length] <= 'z' ? static_cast<char>(text[length] - 32) : text[length];
		}

		out[length] = 0;
	}
	/*
	//=====================================================================================
	*/
	void kit_c::shade(std::float_t strength)
	{
		const auto width{ canvas.screen_width };
		const auto height{ canvas.screen_height };
		const auto amount{ mathematics.saturate(strength) };

		canvas.rect({ 0.0f, 0.0f, width, height }, functions::rgba(4u, 5u, 6u, static_cast<std::uint32_t>(amount * 70.0f)));
		canvas.gradient_horizontal({ 0.0f, 0.0f, width * 0.6f, height }, functions::rgba(3u, 4u, 5u, static_cast<std::uint32_t>(amount * 225.0f)), functions::rgba(3u, 4u, 5u, 0u));
		canvas.gradient({ 0.0f, 0.0f, width, height * 0.24f }, functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(amount * 170.0f)), functions::rgba(0u, 0u, 0u, 0u));
		canvas.gradient({ 0.0f, height * 0.7f, width, height * 0.3f }, functions::rgba(0u, 0u, 0u, 0u), functions::rgba(0u, 0u, 0u, static_cast<std::uint32_t>(amount * 210.0f)));
	}
	/*
	//=====================================================================================
	*/
	void kit_c::panel(structures::rect_s area, std::uint32_t color)
	{
		canvas.rect(area, color);
		canvas.rect({ area.x, area.y, area.w, canvas.scale }, kit_line);
	}
	/*
	//=====================================================================================
	*/
	void kit_c::outline(structures::rect_s area, std::float_t thickness, std::uint32_t color)
	{
		canvas.border(area, thickness, color);
	}
	/*
	//=====================================================================================
	*/
	std::float_t kit_c::caps(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* text, std::uint32_t align, std::float_t spacing)
	{
		char shouted[256]{};

		upper(text, shouted, sizeof(shouted));

		return canvas.text_spaced(font_index, position, size, color, shouted, align, spacing);
	}
	/*
	//=====================================================================================
	*/
	std::float_t kit_c::caps_width(structures::font_e font_index, std::float_t size, const char* text, std::float_t spacing)
	{
		char shouted[256]{};

		upper(text, shouted, sizeof(shouted));

		canvas.tracking = spacing;

		const auto width{ canvas.measure(font_index, size, shouted) };

		canvas.tracking = 0.0f;

		return width;
	}
	/*
	//=====================================================================================
	*/
	std::float_t kit_c::hint(structures::vec2_s position, const char* key, const char* action, std::uint32_t align)
	{
		const auto s{ canvas.scale };
		const auto size{ 15.0f * s };
		const auto key_width{ std::max(caps_width(structures::font_bold, size, key, 0.04f) + 16.0f * s, 28.0f * s) };
		const auto action_width{ caps_width(structures::font_condensed, size, action, kit_caps) };
		const auto total{ key_width + 10.0f * s + action_width };
		const auto left{ (align & structures::align_right) ? position.x - total : ((align & structures::align_center) ? position.x - total * 0.5f : position.x) };
		const structures::rect_s box{ left, position.y - 13.0f * s, key_width, 26.0f * s };

		canvas.rect(box, functions::rgba(255u, 255u, 255u, 20u));
		canvas.border(box, s, kit_line);

		caps(structures::font_bold, { box.x + box.w * 0.5f, position.y }, size, kit_text, key, structures::align_center | structures::align_middle, 0.04f);
		caps(structures::font_condensed, { box.x + box.w + 10.0f * s, position.y }, size, kit_dim, action, structures::align_left | structures::align_middle, kit_caps);

		return total;
	}
	/*
	//=====================================================================================
	*/
	void kit_c::rule(structures::vec2_s from, std::float_t length, std::uint32_t color)
	{
		canvas.rect({ from.x, from.y, length, canvas.scale }, color);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t kit_c::wrap(const char* text, structures::font_e font_index, std::float_t size, std::float_t limit, char (*lines)[160], std::uint32_t capacity)
	{
		char word[64]{};
		char trial[160]{};

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

			if (canvas.measure(font_index, size, trial) > limit && lines[count][0] && count + 1u < capacity)
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
	std::float_t kit_c::paragraph(structures::vec2_s position, std::float_t width, std::float_t size, std::uint32_t color, const char* text)
	{
		char lines[8][160]{};

		const auto count{ wrap(text, structures::font_regular, size, width, lines, 8u) };

		for (auto line{ 0u }; line < count; line++)
		{
			canvas.text(structures::font_regular, { position.x, position.y + static_cast<std::float_t>(line) * size * 1.5f }, size, color, lines[line], structures::align_left | structures::align_middle);
		}

		return static_cast<std::float_t>(count) * size * 1.5f;
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::entry(std::int32_t id, structures::vec2_s position, const char* label, const char* detail)
	{
		const auto s{ canvas.scale };
		const auto size{ 38.0f * s };
		const auto width{ caps_width(structures::font_condensed, size, label, kit_caps) };
		const structures::rect_s area{ position.x - 30.0f * s, position.y - size * 0.62f, std::max(width + 140.0f * s, 460.0f * s), size * 1.24f };
		const auto over{ inside(area) };
		const auto light{ fade(id, over) };

		hot = over ? id : hot;

		canvas.gradient_horizontal(area, functions::with_alpha(kit_accent, light * 0.14f), functions::with_alpha(kit_accent, 0.0f));
		canvas.rect({ area.x, area.y + area.h * (0.5f - 0.32f * light), 3.0f * s, area.h * 0.64f * light }, functions::with_alpha(kit_accent, light));

		caps(structures::font_condensed, { position.x + light * 14.0f * s, position.y }, size, functions::lerp_color(kit_dim, kit_text, light), label, structures::align_left | structures::align_middle, kit_caps);

		if (detail && detail[0] && light > 0.01f)
		{
			canvas.text(structures::font_light, { position.x + light * 14.0f * s + width + 26.0f * s, position.y + 3.0f * s }, 18.0f * s, functions::with_alpha(kit_dim, light), detail, structures::align_left | structures::align_middle);
		}

		if (press(area))
		{
			click(0.9f);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::button(std::int32_t id, structures::rect_s area, const char* label, bool primary)
	{
		const auto s{ canvas.scale };
		const auto over{ inside(area) };
		const auto light{ fade(id, over) };
		const structures::vec2_s middle{ area.x + area.w * 0.5f, area.y + area.h * 0.5f };

		hot = over ? id : hot;

		if (primary)
		{
			canvas.rect(area, functions::lerp_color(functions::with_alpha(kit_accent, 0.82f), kit_accent, light));

			caps(structures::font_condensed, middle, 20.0f * s, functions::rgba(18u, 15u, 10u, 255u), label, structures::align_center | structures::align_middle, kit_caps);
		}

		else
		{
			canvas.rect(area, functions::with_alpha(kit_text, 0.05f + light * 0.08f));
			canvas.border(area, s, functions::lerp_color(kit_line, functions::with_alpha(kit_text, 0.55f), light));

			caps(structures::font_condensed, middle, 20.0f * s, functions::lerp_color(kit_dim, kit_text, light), label, structures::align_center | structures::align_middle, kit_caps);
		}

		if (press(area))
		{
			click(0.9f);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::tab(std::int32_t id, structures::rect_s area, const char* label, bool selected)
	{
		const auto s{ canvas.scale };
		const auto over{ inside(area) };
		const auto light{ fade(id, over || selected) };

		hot = over ? id : hot;

		caps(structures::font_condensed, { area.x + area.w * 0.5f, area.y + area.h * 0.5f }, 19.0f * s, selected ? kit_text : functions::lerp_color(kit_faint, kit_dim, light), label, structures::align_center | structures::align_middle, kit_caps);

		if (selected)
		{
			canvas.rect({ area.x + area.w * 0.12f, area.y + area.h - 3.0f * s, area.w * 0.76f, 2.0f * s }, kit_accent);
		}

		if (press(area) && selected == false)
		{
			click(1.05f);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::choice(std::int32_t id, structures::rect_s area, std::uint32_t& value, const char* const* names, std::uint32_t count)
	{
		const auto s{ canvas.scale };
		const auto arrow{ 34.0f * s };
		const structures::rect_s left{ area.x, area.y, arrow, area.h };
		const structures::rect_s right{ area.x + area.w - arrow, area.y, arrow, area.h };
		const structures::rect_s middle{ area.x + arrow, area.y, area.w - arrow * 2.0f, area.h };
		const auto over{ inside(area) };
		const auto y{ area.y + area.h * 0.5f };
		const auto previous{ value };

		hot = over ? id : hot;

		if (count > 0u)
		{
			if (press(left) || (over && platform.input.pressed[VK_LEFT]))
			{
				value = (value + count - 1u) % count;
			}

			else if (press(right) || press(middle) || (over && platform.input.pressed[VK_RIGHT]))
			{
				value = (value + 1u) % count;
			}

			value = std::min(value, count - 1u);

			const auto left_color{ inside(left) ? kit_accent : (over ? kit_dim : kit_faint) };
			const auto right_color{ inside(right) ? kit_accent : (over ? kit_dim : kit_faint) };

			canvas.line({ left.x + 21.0f * s, y - 7.0f * s }, { left.x + 14.0f * s, y }, 2.0f * s, left_color);
			canvas.line({ left.x + 14.0f * s, y }, { left.x + 21.0f * s, y + 7.0f * s }, 2.0f * s, left_color);
			canvas.line({ right.x + right.w - 21.0f * s, y - 7.0f * s }, { right.x + right.w - 14.0f * s, y }, 2.0f * s, right_color);
			canvas.line({ right.x + right.w - 14.0f * s, y }, { right.x + right.w - 21.0f * s, y + 7.0f * s }, 2.0f * s, right_color);

			canvas.text(structures::font_bold, { middle.x + middle.w * 0.5f, y - 2.0f * s }, 20.0f * s, kit_text, names[value], structures::align_center | structures::align_middle);

			if (count <= 8u)
			{
				const auto pip{ std::min(28.0f * s, middle.w * 0.6f / static_cast<std::float_t>(count)) };
				const auto start{ middle.x + middle.w * 0.5f - pip * static_cast<std::float_t>(count) * 0.5f };

				for (auto index{ 0u }; index < count; index++)
				{
					canvas.rect({ start + static_cast<std::float_t>(index) * pip + 1.5f * s, y + 14.0f * s, pip - 3.0f * s, 2.0f * s }, index == value ? kit_accent : kit_line);
				}
			}
		}

		if (value != previous)
		{
			click(1.1f);
		}

		return value != previous;
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::slider(std::int32_t id, structures::rect_s area, std::float_t& value, std::float_t low, std::float_t high, std::float_t step, const char* format, std::float_t display)
	{
		const auto s{ canvas.scale };
		const auto start{ area.x + 14.0f * s };
		const auto end{ area.x + area.w - 96.0f * s };
		const auto y{ area.y + area.h * 0.5f };
		const auto over{ inside(area) };
		const auto previous{ value };

		char text[32]{};

		hot = over || dragging == id ? id : hot;

		if (press({ start - 10.0f * s, area.y, end - start + 20.0f * s, area.h }))
		{
			dragging = id;
		}

		if (dragging == id)
		{
			if (platform.input.down[VK_LBUTTON])
			{
				const auto raw{ low + mathematics.saturate((platform.input.mouse_position.x - start) / std::max(end - start, 1.0f)) * (high - low) };

				value = step > 0.0f ? low + std::round((raw - low) / step) * step : raw;
			}

			else
			{
				dragging = -1;
			}
		}

		if (over && dragging < 0 && (platform.input.pressed[VK_LEFT] || platform.input.pressed[VK_RIGHT]))
		{
			value += platform.input.pressed[VK_LEFT] ? -step : step;
		}

		value = std::clamp(value, low, high);

		const auto knob{ start + (end - start) * mathematics.saturate((value - low) / std::max(high - low, 0.0001f)) };

		canvas.rect({ start, y - s, end - start, 2.0f * s }, kit_line);
		canvas.rect({ start, y - s, knob - start, 2.0f * s }, kit_accent);
		canvas.rect({ knob - 5.0f * s, y - 10.0f * s, 10.0f * s, 20.0f * s }, over || dragging == id ? kit_text : kit_dim);

		std::snprintf(text, sizeof(text), format, value * display);

		canvas.text(structures::font_bold, { area.x + area.w - 6.0f * s, y - 2.0f * s }, 20.0f * s, kit_text, text, structures::align_right | structures::align_middle);

		return value != previous;
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::toggle(std::int32_t id, structures::rect_s area, bool& value)
	{
		auto index{ value ? 1u : 0u };

		const auto changed{ choice(id, area, index, option_off_on, 2u) };

		value = index == 1u;

		return changed;
	}
	/*
	//=====================================================================================
	*/
	bool kit_c::field(std::int32_t id, structures::rect_s area, const char* text, bool focused, bool secret)
	{
		const auto s{ canvas.scale };
		const auto over{ inside(area) };

		char masked[64]{};
		char shown[96]{};

		hot = over ? id : hot;

		for (auto index{ 0u }; index < std::min<std::size_t>(std::strlen(text), sizeof(masked) - 1u); index++)
		{
			masked[index] = '*';
		}

		std::snprintf(shown, sizeof(shown), "%s%s", secret ? masked : text, focused && std::fmod(clock, 1.0f) < 0.55f ? "|" : "");

		canvas.rect(area, functions::rgba(0u, 0u, 0u, 120u));
		canvas.border(area, s, focused ? kit_accent : (over ? functions::with_alpha(kit_text, 0.4f) : kit_line));
		canvas.text(structures::font_regular, { area.x + 14.0f * s, area.y + area.h * 0.5f }, 20.0f * s, kit_text, shown, structures::align_left | structures::align_middle);

		return press(area);
	}
	/*
	//=====================================================================================
	*/
	void kit_c::meter(structures::rect_s area, std::float_t fraction, std::uint32_t color)
	{
		canvas.rect(area, functions::rgba(255u, 255u, 255u, 26u));
		canvas.rect({ area.x, area.y, area.w * mathematics.saturate(fraction), area.h }, color);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t kit_c::dialog(const char* title, const char* text, const char* confirm, const char* cancel)
	{
		const auto s{ canvas.scale };
		const auto width{ 700.0f * s };
		const auto height{ 280.0f * s };
		const structures::rect_s area{ (canvas.screen_width - width) * 0.5f, (canvas.screen_height - height) * 0.5f, width, height };
		const structures::rect_s yes{ area.x + area.w - 44.0f * s - 210.0f * s, area.y + area.h - 80.0f * s, 210.0f * s, 48.0f * s };
		const structures::rect_s no{ yes.x - 20.0f * s - 210.0f * s, yes.y, 210.0f * s, 48.0f * s };

		auto result{ 0u };

		canvas.rect({ 0.0f, 0.0f, canvas.screen_width, canvas.screen_height }, functions::rgba(0u, 0u, 0u, 160u));

		panel(area, functions::rgba(13u, 14u, 16u, 248u));

		canvas.rect({ area.x, area.y, area.w, 3.0f * s }, kit_accent);

		caps(structures::font_condensed, { area.x + 44.0f * s, area.y + 56.0f * s }, 30.0f * s, kit_text, title, structures::align_left | structures::align_middle, kit_caps);

		paragraph({ area.x + 44.0f * s, area.y + 104.0f * s }, area.w - 88.0f * s, 19.0f * s, kit_dim, text);

		if (button(static_cast<std::int32_t>(kit_slots) - 2, yes, confirm, true) || platform.input.pressed[VK_RETURN])
		{
			result = 1u;
		}

		if (cancel && (button(static_cast<std::int32_t>(kit_slots) - 3, no, cancel, false) || platform.input.pressed[VK_ESCAPE]))
		{
			result = 2u;
		}

		if (result)
		{
			platform.input.pressed[VK_RETURN] = false;
			platform.input.pressed[VK_ESCAPE] = false;
		}

		return result;
	}
}

//=====================================================================================
