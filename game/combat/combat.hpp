
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class combat_c
	{
	public:

		std::float_t hit_marker = 0.0f;
		std::float_t kill_marker = 0.0f;

		bool melee(structures::vec3_s origin, structures::vec3_s direction, std::float_t reach, std::float_t damage);
		std::int32_t corpse_target();
		void update(std::float_t delta, bool input_enabled);
		void loot(structures::actor_s& actor);
	};

	extern combat_c combat;
}

//=====================================================================================
