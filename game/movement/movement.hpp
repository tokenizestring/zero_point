
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class movement_c
	{
	public:

		structures::trace_s last_block{};
		structures::vec3_s anchor{};
		std::uint32_t anchored = 0u;
		bool beside = false;

		void reset(structures::movement_state_s& state, structures::vec3_s position, std::float_t yaw);
		void simulate(structures::movement_state_s& state, const structures::usercmd_s& command);
		void seat(structures::movement_state_s& state);
		void board(structures::movement_state_s& state, std::double_t time);
		void ride(structures::movement_state_s& state, std::double_t time);
		void walk(structures::movement_state_s& state, const structures::usercmd_s& command, std::float_t dt);
		void swim(structures::movement_state_s& state, const structures::usercmd_s& command, std::float_t dt);
		void noclip(structures::movement_state_s& state, const structures::usercmd_s& command);
		void ground_move(structures::movement_state_s& state, std::float_t dt);
		void land(structures::movement_state_s& state, std::float_t impact);
		void accelerate(structures::movement_state_s& state, structures::vec3_s direction, std::float_t speed, std::float_t rate, std::float_t dt);
		void update_crouch(structures::movement_state_s& state, bool wants_crouch);
		void unstick(structures::movement_state_s& state);
		void step_slide_move(structures::movement_state_s& state, std::float_t dt);
		bool slide_move(structures::movement_state_s& state, std::float_t dt);
		bool snap_to_ground(structures::movement_state_s& state);
		bool categorize(structures::movement_state_s& state);
		bool solid(const structures::movement_state_s& state);
		std::float_t fall_damage(const structures::movement_state_s& state);
		structures::vec3_s clip_velocity(structures::vec3_s velocity, structures::vec3_s normal, std::float_t overbounce);
		structures::vec3_s extents(const structures::movement_state_s& state);
		structures::vec3_s center(const structures::movement_state_s& state);
		structures::trace_s trace_hull(const structures::movement_state_s& state, structures::vec3_s from_center, structures::vec3_s to_center);
	};

	extern movement_c movement;
}

//=====================================================================================
