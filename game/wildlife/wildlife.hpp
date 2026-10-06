
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class wildlife_c
	{
	public:

		std::vector<structures::flock_s> flocks;
		std::vector<structures::creature_s> creatures;
		const structures::model_s* shapes[structures::wildlife_kind_count]{};
		std::uint32_t seed = 0x6A11F15Au;

		void create();
		void populate();
		bool home(std::uint32_t kind, structures::vec3_s& point);
		structures::vec3_s anchor(const structures::flock_s& flock) const;
		void update(std::float_t delta, structures::vec3_s viewer);
		void fly(structures::flock_s& flock, structures::creature_s& creature, std::float_t delta);
		void swim(structures::flock_s& flock, structures::creature_s& creature, std::float_t delta, structures::vec3_s viewer);
		void place(structures::creature_s& creature, structures::vec3_s heading, std::float_t bank, bool shown);
		void startle(structures::vec3_s origin, std::float_t loudness);
		void submit();
		std::float_t random();
	};

	extern wildlife_c wildlife;
}

//=====================================================================================
