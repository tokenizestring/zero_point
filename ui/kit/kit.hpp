
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class kit_c
	{
	public:

		std::float_t glow[kit_slots]{};
		std::float_t clock = 0.0f;
		std::float_t delta = 0.0f;
		std::int32_t hot = -1;
		std::int32_t previous_hot = -1;
		std::int32_t dragging = -1;
		bool clicked = false;
		bool blocked = false;

		void begin(std::float_t frame_delta);
		void end();
		bool inside(structures::rect_s area);
		bool press(structures::rect_s area);
		std::float_t fade(std::int32_t id, bool on);
		void click(std::float_t pitch);
		void upper(const char* text, char* out, std::size_t capacity);

		void shade(std::float_t strength);
		void panel(structures::rect_s area, std::uint32_t color);
		void outline(structures::rect_s area, std::float_t thickness, std::uint32_t color);
		std::float_t caps(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* text, std::uint32_t align, std::float_t spacing);
		std::float_t caps_width(structures::font_e font_index, std::float_t size, const char* text, std::float_t spacing);
		std::float_t hint(structures::vec2_s position, const char* key, const char* action, std::uint32_t align);
		void rule(structures::vec2_s from, std::float_t length, std::uint32_t color);
		std::uint32_t wrap(const char* text, structures::font_e font_index, std::float_t size, std::float_t limit, char (*lines)[160], std::uint32_t capacity);
		std::float_t paragraph(structures::vec2_s position, std::float_t width, std::float_t size, std::uint32_t color, const char* text);

		bool entry(std::int32_t id, structures::vec2_s position, const char* label, const char* detail);
		bool button(std::int32_t id, structures::rect_s area, const char* label, bool primary);
		bool tab(std::int32_t id, structures::rect_s area, const char* label, bool selected);
		bool choice(std::int32_t id, structures::rect_s area, std::uint32_t& value, const char* const* names, std::uint32_t count);
		bool slider(std::int32_t id, structures::rect_s area, std::float_t& value, std::float_t low, std::float_t high, std::float_t step, const char* format, std::float_t display);
		bool toggle(std::int32_t id, structures::rect_s area, bool& value);
		bool field(std::int32_t id, structures::rect_s area, const char* text, bool focused, bool secret);
		void meter(structures::rect_s area, std::float_t fraction, std::uint32_t color);
		std::uint32_t dialog(const char* title, const char* text, const char* confirm, const char* cancel);
	};

	extern kit_c kit;
}

//=====================================================================================
