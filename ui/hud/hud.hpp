
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
		ID3D11ShaderResourceView* icon_view = nullptr;
		const std::uint8_t* icon_table = nullptr;
		structures::vec3_s hurt_from{};
		std::float_t hurt_timer = 0.0f;
		std::float_t clock = 0.0f;
		std::float_t death_clock = 0.0f;
		std::float_t belt_clock = 0.0f;
		std::float_t belt_glow = 0.0f;
		std::float_t vital_clock[3]{};
		std::float_t vital_seen[3]{};
		std::float_t vital_glow[4]{};
		std::float_t recipe_scroll = 0.0f;
		std::uint32_t belt_slot = UINT32_MAX;
		std::int32_t drag_slot = -1;
		std::int32_t hover_slot = -1;
		std::int32_t hover_recipe = -1;
		bool chatting = false;
		bool keypad_setting = false;
		std::int32_t keypad_door = -1;
		char keypad_entry[8]{};

		bool create();
		void destroy();
		void draw(std::float_t delta);
		void track(std::float_t delta);
		void update_chat(std::float_t delta);
		void draw_wounds();
		void draw_crosshair(std::float_t s);
		void draw_prompt(std::float_t s);
		std::float_t inline_keys(structures::vec2_s origin, const char* text, std::float_t size, bool draw, std::float_t s);
		std::float_t key_cap(structures::vec2_s position, const char* label, std::float_t size, bool draw, std::float_t s);
		std::float_t etched(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* text, std::uint32_t align, std::float_t spacing);
		void draw_chat(std::float_t s);
		void draw_names(std::float_t s);
		void draw_hurt(std::float_t s);
		void draw_compass(std::float_t s);
		std::float_t compass_bearing(structures::vec2_s target);
		void compass_mark(structures::vec2_s point, std::float_t fade, std::uint32_t color, const char* label, std::float_t distance, bool focused, std::float_t s);
		void draw_death(std::float_t s);
		void draw_ending(std::float_t s);
		void draw_goal(std::float_t s);
		void draw_vitals(std::float_t s);
		void draw_meter(structures::vec2_s position, std::uint32_t label, std::float_t value, std::float_t maximum, std::uint32_t color, std::float_t width, std::float_t alpha, std::float_t s);
		void draw_climate(structures::vec2_s position, bool always, std::float_t s);
		void draw_scope(std::float_t s);
		void draw_belt(std::float_t s);
		void draw_notifications(std::float_t s);
		void draw_queue(std::float_t s);
		void draw_inventory(std::float_t s);
		void draw_condition(structures::vec2_s position, std::float_t width, std::float_t s);
		void draw_crafting(structures::rect_s page, std::float_t s);
		void draw_recipe(structures::rect_s area, std::uint32_t recipe, bool over, std::float_t s);
		void draw_details(structures::rect_s area, std::uint32_t recipe, std::float_t s);
		void draw_container(structures::rect_s page, std::float_t s);
		void draw_grab(std::float_t s);
		void draw_tooltip(const structures::item_stack_s& stack, std::float_t s);
		void draw_slot(structures::rect_s area, std::uint32_t index, bool active, std::float_t alpha, std::float_t s);
		void draw_item(structures::rect_s area, std::uint32_t item, std::float_t alpha, std::float_t s);
		void draw_title(structures::vec2_s position, const char* title, const char* subtitle, std::float_t s);
		void open_keypad(std::int32_t door, bool setting);
		void close_keypad();
		void submit_keypad();
		void draw_keypad(std::float_t s);
		structures::rect_s sheet(std::float_t s);
		structures::rect_s page_rect(std::float_t s);
		structures::rect_s slot_rect(std::uint32_t index, std::float_t s);
		void set_prompt(const char* text);
	};

	extern hud_c hud;
}

//=====================================================================================
