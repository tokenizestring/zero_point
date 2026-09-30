
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class profiler_c
	{
	public:

		ID3D11Query* disjoint[profiler_latency]{};
		ID3D11Query* stamps[profiler_latency][structures::profile_count + 1u]{};
		std::double_t totals[structures::profile_count]{};
		std::double_t frame_total = 0.0;
		std::uint32_t samples = 0u;
		std::uint32_t seen = 0u;
		std::uint32_t current = 0u;
		std::uint32_t issued = 0u;
		bool ready = false;

		bool create();
		void destroy();
		void begin();
		void mark(std::uint32_t section);
		void end();
		void collect();
		void report();
	};

	extern profiler_c profiler;
}

//=====================================================================================
