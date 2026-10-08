
//=====================================================================================

#pragma once

#include "../engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class application_c
	{
	public:

		structures::launch_options_s options{};
		std::double_t previous_time = 0.0;
		std::double_t next_frame_time = 0.0;
		std::float_t delta = 0.0f;
		std::float_t elapsed = 0.0f;
		std::float_t fps = 0.0f;
		std::float_t frame_cap = 0.0f;
		std::uint64_t frame_index = 0u;
		std::uint64_t seated_frame = UINT64_MAX;
		bool running = false;

		structures::vec3_s fly_position{ 0.0f, 1.7f, -6.0f };
		std::float_t fly_yaw = 0.0f;
		std::float_t fly_pitch = 0.0f;
		std::uint32_t player_actor = UINT32_MAX;
		std::uint32_t spawn_seed = 0x6A09E667u;
		std::int32_t fell_node = -1;
		std::uint32_t state = structures::app_loading;
		std::uint32_t pending = structures::app_title;
		std::uint32_t stage = 0u;
		std::uint32_t warmup = 0u;
		structures::vec3_s title_position{};
		std::float_t title_yaw = 0.0f;
		std::float_t title_pitch = 0.0f;
		std::float_t waking = 0.0f;
		std::float_t leaving = 0.0f;
		std::float_t warm_clock = 0.0f;
		std::double_t trace_clock = 0.0;
		std::double_t trace_last = 0.0;
		std::double_t trace_worst = 0.0;
		std::double_t trace_spent[4]{};
		std::double_t trace_parts[6]{};
		std::uint32_t trace_frames = 0u;
		bool show_debug = false;
		bool paused = false;
		bool alive = false;
		bool testing = false;
		bool fauna_mirrored = false;
		bool vehicles_mirrored = false;
		bool herd_framed = false;

		std::int32_t run(HINSTANCE instance);
		void parse_arguments();
		bool startup(HINSTANCE instance);
		bool load_stage(std::uint32_t index);
		void prepare_world();
		void shutdown();
		void frame();
		void frame_loading();
		void frame_world();
		void update_game();
		void enter_title();
		void host_server();
		void begin_life();
		void resume_saved();
		void handle_action(std::uint32_t action);
		void update_survival();
		void respawn();
		std::int32_t approach_node(std::uint32_t kind);
		void populate();
		void update_fauna();
		void update_vehicles();
		void update_player_actor();
		structures::vec3_s third_person_camera();
		void update_fly_camera();
		void stage_marks();
		void trace(std::double_t began, std::double_t updated, std::double_t waited, std::double_t drawn);
		void draw_debug_overlay();
	};

	extern application_c application;
}

//=====================================================================================
