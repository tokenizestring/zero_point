
//=====================================================================================

#pragma once

#include "../engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class platform_c
	{
	public:

		HINSTANCE instance = nullptr;
		HWND window = nullptr;
		std::int32_t client_width = 0;
		std::int32_t client_height = 0;
		RECT windowed_rect{};
		structures::display_mode_e display_mode = structures::display_mode_windowed;
		bool focused = true;
		bool minimized = false;
		bool resized = false;
		bool quit_requested = false;
		bool mouse_captured = false;
		bool headless = false;

		structures::input_state_s input{};
		std::uint8_t bindings[structures::bind_count]{};

		LARGE_INTEGER frequency{};
		LARGE_INTEGER start_counter{};
		HANDLE frame_timer = nullptr;

		std::vector<std::uint8_t> raw_buffer;

		bool create(HINSTANCE module_instance, bool create_window);
		void destroy();
		void pump();
		void set_display_mode(structures::display_mode_e mode);
		void set_window_size(std::uint32_t width, std::uint32_t height);
		void set_mouse_captured(bool captured);
		void apply_cursor_clip();
		void set_title(const char* text);
		void release_all_keys();
		bool held(std::uint32_t action);
		bool tapped(std::uint32_t action);
		void consume(std::uint32_t action);
		void simulate(std::uint32_t action, bool down);
		void sleep_until(std::double_t target_seconds);

		std::double_t time();

		bool copy_to_clipboard(const char* text);
		bool paste_from_clipboard(char* out, std::uint32_t capacity);

		void on_key(std::uint32_t key, bool down, bool repeat);
		void on_raw_input(LPARAM handle);

		static LRESULT CALLBACK window_procedure(HWND handle, UINT message, WPARAM wparam, LPARAM lparam);
	};

	extern platform_c platform;
}

//=====================================================================================
