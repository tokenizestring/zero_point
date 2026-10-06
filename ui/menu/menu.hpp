
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
		structures::user_settings_s kept{ default_user_settings };
		structures::title_shot_s shots[4]{};
		std::uint32_t current_page = structures::page_main;
		std::uint32_t tab = structures::tab_display;
		std::uint32_t dialog = structures::dialog_none;
		std::uint32_t shot = 0u;
		std::uint32_t shot_count = 0u;
		std::uint32_t tip = 0u;
		std::int32_t focus_row = -1;
		std::int32_t selected_server = -1;
		std::int32_t capturing = -1;
		std::float_t clock = 0.0f;
		std::float_t shot_clock = 0.0f;
		std::float_t tip_clock = 0.0f;
		std::float_t reveal = 0.0f;
		std::float_t browse_clock = -100.0f;
		std::float_t pick_clock = -100.0f;
		std::float_t dialog_clock = 0.0f;
		std::float_t scroll = 0.0f;
		std::float_t scroll_limit = 0.0f;
		std::float_t fps_clock = 0.0f;
		std::uint32_t fps_frames = 0u;
		std::float_t fps = 0.0f;
		std::float_t frame_time = 0.0f;
		structures::address_s join_address{};
		char address_text[64]{ "127.0.0.1:28015" };
		bool typing = false;
		bool typing_secret = false;
		bool heavy = false;
		bool heard = true;

		bool create();
		void destroy();
		void load_settings();
		void save_settings();
		void apply_settings();
		void apply_display();
		void listen();
		void preset(std::uint32_t level);
		void plan_shots();
		void title_camera(std::float_t delta, structures::vec3_s& position, std::float_t& yaw, std::float_t& pitch);
		std::float_t shot_fade();
		void draw_loading(std::uint32_t stage, std::uint32_t stages, bool map_ready, std::float_t delta);
		std::uint32_t draw_title(bool alive, std::float_t delta);
		std::uint32_t draw_pause(std::float_t delta);
		std::uint32_t draw_main(const structures::menu_entry_s* entries, const char* const* details, std::uint32_t count, bool paused);
		void draw_brand(structures::vec2_s origin, std::float_t size, const char* tagline);
		void draw_footer(bool paused);
		bool draw_subpage();
		bool draw_settings();
		void draw_rows(structures::rect_s area);
		void draw_keys(structures::rect_s area);
		void draw_detail(structures::rect_s area);
		bool draw_notes();
		bool draw_credits();
		std::uint32_t draw_servers();
		std::uint32_t draw_dialog(std::uint32_t action);
		void draw_page_title(const char* title, const char* subtitle);
		void draw_fps(std::float_t delta);
		void key_name(std::uint32_t key, char* out, std::size_t capacity);
		void type_into(char* buffer, std::size_t capacity);
		void draw_waking(std::float_t time);
	};

	extern menu_c menu;
}

//=====================================================================================
