
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class story_c
	{
	public:

		std::uint32_t step = 0u;
		std::uint32_t day = 1u;
		std::uint32_t repaired_day = 0u;
		std::uint32_t researched = 0u;
		std::uint32_t searches[structures::landmark_count]{};
		std::float_t previous_hours = 0.0f;
		std::float_t done_flash = 0.0f;
		std::uint32_t seed = 0x51ED270Bu;
		bool parts[structures::landmark_count]{};
		bool rescued = false;
		bool ending = false;

		void reset();
		void update(std::float_t delta);
		bool complete(const structures::goal_s& goal);
		void advance();
		void searched(structures::vec3_s position);
		std::int32_t landmark_at(structures::vec3_s position);
		std::uint32_t parts_found();
		std::uint32_t progress(const structures::goal_s& goal);
		bool placed(std::uint32_t piece);
		bool near_radio();
		bool on_shore();
		std::float_t random();
	};

	extern story_c story;
}

//=====================================================================================
