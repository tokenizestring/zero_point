
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class weapons_c
	{
	public:

		structures::weapon_state_s state{};
		structures::weapon_state_s before{};
		structures::vec3_s muzzle{};
		std::uint32_t weapon = structures::weapon_none;
		std::uint32_t seed = 0x1F83D9ABu;
		std::float_t reloading = 0.0f;
		std::float_t clearing = 0.0f;
		std::float_t cycle = 0.0f;
		std::float_t draw = 0.0f;
		std::float_t aim = 0.0f;
		std::float_t kick = 0.0f;
		std::float_t flash = 0.0f;
		std::float_t view_pitch = 0.0f;
		std::float_t view_yaw = 0.0f;
		bool jammed = false;
		bool cycled = true;
		bool scoped = false;

		void reset(std::uint32_t owner_seed);
		void update(std::float_t delta, bool input_enabled);
		void tick(const structures::usercmd_s& command, bool usable, bool moving);
		void step(structures::weapon_state_s& weapon_state, survival_c& owner, const structures::usercmd_s& command, bool usable, bool moving);
		void fire(structures::weapon_state_s& weapon_state, structures::item_stack_s& held, const structures::usercmd_s& command, bool moving);
		void discharge(structures::weapon_state_s& weapon_state, structures::item_stack_s& held, const structures::usercmd_s& command, bool moving);
		void loose(structures::weapon_state_s& weapon_state, structures::item_stack_s& held, const structures::usercmd_s& command, bool moving);
		void finish_reload(structures::weapon_state_s& weapon_state, survival_c& owner, structures::item_stack_s& held);
		void effects(const structures::usercmd_s& command);
		void strike(structures::vec3_s origin, structures::vec3_s direction, const structures::weapon_definition_s& definition, std::uint32_t item);
		structures::vec3_s aim_direction(const structures::weapon_state_s& weapon_state, std::float_t yaw, std::float_t pitch, std::uint32_t sequence);
		structures::vec3_s scatter(structures::weapon_state_s& weapon_state, structures::vec3_s forward, std::float_t spread, std::uint32_t sequence);
		structures::vec2_s drift(const structures::weapon_state_s& weapon_state, std::float_t time);
		std::int32_t ray_actor(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance, std::float_t& height);
		std::float_t roll(structures::weapon_state_s& weapon_state, std::uint32_t sequence);
		std::float_t random();
	};

	extern weapons_c weapons;
}

//=====================================================================================
