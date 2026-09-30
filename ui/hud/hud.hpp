
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class hud_c
	{
	public:

		char prompt[128]{};
		char chat_text[net_chat_length]{};
		ID3D11ShaderResourceView* paper = nullptr;
		ID3D11ShaderResourceView* icon_view = nullptr;
		const std::uint8_t* icon_table = nullptr;
		structures::vec3_s hurt_from{};
		std::float_t hurt_timer = 0.0f;
		std::int32_t drag_slot = -1;
		std::int32_t hover_slot = -1;
		std::int32_t hover_recipe = -1;
		bool chatting = false;
		bool keypad_setting = false;
		std::int32_t keypad_door = -1;
		char keypad_entry[8]{};

		bool create();
		void update_chat(std::float_t delta);
		void draw_chat(std::float_t s);
		void draw_names(std::float_t s);
		void draw_hurt(std::float_t s);
		void draw_compass(std::float_t s);
		std::float_t compass_bearing(structures::vec2_s target);
		void compass_mark(structures::vec2_s point, std::float_t fade, std::uint32_t color, const char* label, std::float_t distance, bool focused, std::float_t s);
		void destroy();
		void draw(std::float_t delta);
		void draw_death(std::float_t s);
		void draw_ending(std::float_t s);
		void draw_goal(std::float_t s);
		std::uint32_t wrap(const char* text, structures::font_e font_index, std::float_t size, std::float_t limit, char (*lines)[128], std::uint32_t capacity);
		void draw_vitals(std::float_t s);
		void draw_climate(structures::rect_s vitals_area, std::float_t s);
		void draw_ammo(std::float_t s);
		void draw_scope(std::float_t s);
		void draw_hotbar(std::float_t s);
		void draw_notifications(std::float_t s);
		void draw_queue(std::float_t s);
		void draw_inventory(std::float_t s);
		void draw_crafting(structures::rect_s page, std::float_t s);
		void draw_container(structures::rect_s page, std::float_t s);
		void draw_slot(structures::rect_s area, std::uint32_t index, bool active, std::float_t s);
		void draw_item(structures::rect_s area, std::uint32_t item, std::float_t s);
		void open_keypad(std::int32_t door, bool setting);
		void close_keypad();
		void submit_keypad();
		void draw_keypad(std::float_t s);
		void draw_bar(structures::rect_s area, std::uint32_t label, std::float_t value, std::float_t maximum, std::uint32_t color, std::float_t s);
		structures::rect_s journal(std::float_t s);
		structures::rect_s slot_rect(std::uint32_t index, std::float_t s);
		void card(structures::rect_s area, std::uint32_t tint, std::uint32_t variant);
		void sketch(structures::rect_s area, std::float_t thickness, std::uint32_t color, std::uint32_t seed);
		void hatch(structures::rect_s area, std::float_t fraction, std::uint32_t color, std::float_t s);
		void loop(structures::rect_s area, std::uint32_t color, std::float_t s);
		void set_prompt(const char* text);
	};

	extern hud_c hud;
}

//=====================================================================================
