
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class autotest_c
	{
	public:

		std::vector<std::int32_t> skipped;
		structures::vec3_s anchor{};
		std::uint32_t phase = structures::autotest_walk;
		std::uint32_t frames = 0u;
		std::uint32_t built = 0u;
		std::uint32_t settled = 0u;
		std::int32_t target = -1;
		bool swinging_before = false;
		bool options_raid = false;

		void update(std::float_t delta, std::uint64_t frame);
		void walk(std::uint64_t frame);
		void gather(std::uint64_t frame, std::uint32_t kind);
		void build(std::uint64_t frame);
		void plant(std::uint64_t frame);
		void shoot(std::uint64_t frame);
		void die();
		void raid(std::uint64_t frame);
		void ride();
		void report(std::uint64_t frame);
		void advance(std::uint32_t next);
		std::int32_t nearest_node(std::uint32_t kind);
	};

	extern autotest_c autotest;
}

//=====================================================================================
