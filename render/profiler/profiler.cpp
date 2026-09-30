
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	profiler_c profiler;

	bool profiler_c::create()
	{
		const D3D11_QUERY_DESC disjoint_desc{ D3D11_QUERY_TIMESTAMP_DISJOINT, 0u };
		const D3D11_QUERY_DESC stamp_desc{ D3D11_QUERY_TIMESTAMP, 0u };

		ready = true;

		for (auto frame{ 0u }; frame < profiler_latency; frame++)
		{
			ready = SUCCEEDED(gpu.device->CreateQuery(&disjoint_desc, &disjoint[frame])) && ready;

			for (auto stamp{ 0u }; stamp <= structures::profile_count; stamp++)
			{
				ready = SUCCEEDED(gpu.device->CreateQuery(&stamp_desc, &stamps[frame][stamp])) && ready;
			}
		}

		return ready;
	}
	/*
	//=====================================================================================
	*/
	void profiler_c::destroy()
	{
		for (auto frame{ 0u }; frame < profiler_latency; frame++)
		{
			functions::release(disjoint[frame]);

			for (auto stamp{ 0u }; stamp <= structures::profile_count; stamp++)
			{
				functions::release(stamps[frame][stamp]);
			}
		}

		ready = false;
	}
	/*
	//=====================================================================================
	*/
	void profiler_c::begin()
	{
		if (ready)
		{
			collect();

			gpu.context->Begin(disjoint[current]);
			gpu.context->End(stamps[current][0]);
		}
	}
	/*
	//=====================================================================================
	*/
	void profiler_c::mark(std::uint32_t section)
	{
		if (ready)
		{
			gpu.context->End(stamps[current][section + 1u]);
		}
	}
	/*
	//=====================================================================================
	*/
	void profiler_c::end()
	{
		if (ready)
		{
			gpu.context->End(disjoint[current]);

			current = (current + 1u) % profiler_latency;

			issued++;
		}
	}
	/*
	//=====================================================================================
	*/
	void profiler_c::collect()
	{
		D3D11_QUERY_DATA_TIMESTAMP_DISJOINT timing{};

		std::uint64_t values[structures::profile_count + 1u]{};

		auto complete{ issued >= profiler_latency && gpu.context->GetData(disjoint[current], &timing, sizeof(timing), 0u) == S_OK && timing.Disjoint == FALSE && timing.Frequency > 0u };

		for (auto stamp{ 0u }; complete && stamp <= structures::profile_count; stamp++)
		{
			complete = gpu.context->GetData(stamps[current][stamp], &values[stamp], sizeof(std::uint64_t), 0u) == S_OK;
		}

		if (complete && ++seen > profiler_warmup)
		{
			const auto scale{ 1000.0 / static_cast<std::double_t>(timing.Frequency) };

			for (auto section{ 0u }; section < structures::profile_count; section++)
			{
				totals[section] += static_cast<std::double_t>(values[section + 1u] - values[section]) * scale;
			}

			frame_total += static_cast<std::double_t>(values[structures::profile_count] - values[0]) * scale;

			samples++;
		}
	}
	/*
	//=====================================================================================
	*/
	void profiler_c::report()
	{
		if (samples)
		{
			char line[512]{};

			auto length{ std::snprintf(line, sizeof(line), "profile: %u frames, gpu %.2f ms |", samples, frame_total / samples) };

			for (auto section{ 0u }; section < structures::profile_count && length > 0 && static_cast<std::size_t>(length) < sizeof(line); section++)
			{
				length += std::snprintf(line + length, sizeof(line) - static_cast<std::size_t>(length), " %s %.2f", profile_names[section], totals[section] / samples);
			}

			logger.write("%s", line);
		}
	}
}

//=====================================================================================
