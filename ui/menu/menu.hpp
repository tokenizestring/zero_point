
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class menu_c
	{
	public:

		structures::user_settings_s user{ default_user_settings };
		structures::title_shot_s shots[4]{};
		ID3D11ShaderResourceView* page = nullptr;
		std::float_t glow[8]{};
		std::uint32_t current_page = structures::page_main;
		std::uint32_t shot = 0u;
		std::uint32_t shot_count = 0u;
		std::uint32_t tip = 0u;
		std::int32_t hovered = -1;
		std::int32_t dragging = -1;
		std::float_t clock = 0.0f;
		std::float_t shot_clock = 0.0f;
		std::float_t tip_clock = 0.0f;
		std::float_t reveal = 0.0f;
		std::int32_t selected_server = -1;
		std::int32_t capturing = -1;
		std::float_t browse_clock = -100.0f;
		std::float_t pick_clock = -100.0f;
		structures::address_s join_address{};
		char address_text[64]{ "127.0.0.1:28015" };
		bool typing = false;
		bool typing_secret = false;
		bool heavy = false;
		bool clicked = false;

		bool create();
		void destroy();
		void load_settings();
		void save_settings();
		void apply_settings();
		void plan_shots();
		void title_camera(std::float_t delta, structures::vec3_s& position, std::float_t& yaw, std::float_t& pitch);
		std::float_t shot_fade();
		void draw_loading(std::uint32_t stage, std::uint32_t stages, bool map_ready, std::float_t delta);
		std::uint32_t draw_title(bool alive, std::float_t delta);
		std::uint32_t draw_pause(std::float_t delta);
		std::uint32_t draw_entries(const structures::menu_entry_s* entries, std::uint32_t count, std::uint32_t skip, structures::vec2_s origin, std::float_t delta, std::float_t s);
		void draw_heading(const char* title, const char* tagline, std::float_t size, structures::vec2_s origin, std::float_t s);
		bool draw_subpage(std::float_t s);
		bool draw_settings(std::float_t s);
		bool draw_controls(std::float_t s);
		void key_name(std::uint32_t key, char* out, std::size_t capacity);
		bool draw_notes(std::float_t s);
		std::uint32_t draw_servers(std::float_t s);
		void type_into(char* buffer, std::size_t capacity);
		void draw_waking(std::float_t time);
		void footprint(structures::vec2_s center, bool left, std::float_t size, std::uint32_t color);
		void rule(structures::vec2_s from, std::float_t length, std::float_t thickness, std::uint32_t color, std::uint32_t seed);
		bool slider(structures::rect_s row, const char* label, std::float_t& value, std::float_t low, std::float_t high, const char* format, std::float_t display, std::int32_t id, std::float_t s);
		bool toggle(structures::rect_s row, const char* label, bool& value, std::float_t s);
		bool choice(structures::rect_s row, const char* label, std::uint32_t& value, const char* const* names, std::uint32_t count, std::float_t s);
		bool button(structures::rect_s area, const char* label, std::float_t s);
		bool press(structures::rect_s area);
	};

	extern menu_c menu;
}

//=====================================================================================
