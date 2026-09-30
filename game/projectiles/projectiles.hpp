
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class projectiles_c
	{
	public:

		std::vector<structures::arrow_s> arrows;
		const structures::model_s* shape = nullptr;
		std::uint32_t seed = 0x3C6EF372u;

		void clear();
		void launch(structures::vec3_s origin, structures::vec3_s velocity, std::float_t damage, std::int32_t owner);
		void update(std::float_t delta, bool input_enabled);
		void advance(std::float_t delta);
		void fly(structures::arrow_s& arrow, std::float_t delta);
		void collect(survival_c& owner, structures::vec3_s position);
		std::int32_t pickup_target(structures::vec3_s origin, structures::vec3_s forward);
		structures::mat4_s placement(const structures::arrow_s& arrow);
		void submit();
		std::float_t random();
	};

	extern projectiles_c projectiles;
}

//=====================================================================================
