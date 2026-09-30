
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class player_c
	{
	public:

		structures::movement_state_s state{};
		structures::movement_state_s previous{};
		structures::usercmd_s command{};
		std::float_t yaw = 0.0f;
		std::float_t pitch = 0.0f;
		std::float_t roll = 0.0f;
		std::float_t accumulator = 0.0f;
		std::float_t step_offset = 0.0f;
		std::float_t landing_offset = 0.0f;
		std::float_t landing_velocity = 0.0f;
		std::float_t bob_phase = 0.0f;
		std::float_t bob_weight = 0.0f;
		std::float_t swell = 0.0f;
		std::float_t sensitivity = default_mouse_sensitivity;
		std::float_t heading = 0.0f;
		std::uint32_t ridden = 0u;
		std::uint32_t sequence = 0u;
		structures::vec3_s eye{};
		bool active = false;
		bool invert = false;

		void spawn(structures::vec3_s position, std::float_t spawn_yaw);
		void update(std::float_t dt, bool input_enabled);
		void turn_with_ride();
		void build_command(bool input_enabled);
		void tick();
		void update_camera(std::float_t dt);
	};

	extern player_c player;
}

//=====================================================================================
