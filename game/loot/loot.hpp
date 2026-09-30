
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class loot_c
	{
	public:

		std::vector<structures::loot_bag_s> bags;
		std::vector<std::int32_t> spare;
		std::uint32_t revision = 0u;

		void clear();
		void drop(survival_c& victim, structures::vec3_s position, std::float_t yaw, const char* name);
		void sleep(const survival_c& sleeper, structures::vec3_s position, std::float_t yaw, const char* name);
		void wake(const char* name);
		void store(const structures::loot_bag_s& bag);
		bool strike(std::uint32_t index, std::float_t amount);
		std::int32_t ray_sleeper(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance);
		void update(std::float_t delta);
		void present(bool input_enabled);
		void take(std::uint32_t index, survival_c& looter);
		void release(structures::loot_bag_s& bag);
		std::int32_t target(structures::vec3_s eye, structures::vec3_s forward);
		std::int32_t nearest(structures::vec3_s position);
	};

	extern loot_c loot;
}

//=====================================================================================
