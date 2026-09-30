
//=====================================================================================

#include "common.hlsli"

cbuffer exposure_constants : register(b5)
{
	float4 exposure_settings;
	float4 exposure_range;
	float4 exposure_limits;
};

Texture2D<float4> scene_texture : register(t0);
RWByteAddressBuffer histogram : register(u0);
RWStructuredBuffer<float4> exposure_state : register(u1);

groupshared uint local_bins[64];

//=====================================================================================

uint luminance_bin(float3 color)
{
	float value = luminance(color);
	uint result = 0;

	[branch] if (value > 0.00001)
	{
		result = (uint)clamp((log2(value) - exposure_range.x) * exposure_range.z * 62.0 + 1.0, 1.0, 63.0);
	}

	return result;
}
/*
//=====================================================================================
*/
[numthreads(16, 16, 1)]
void cs_histogram(uint3 id : SV_DispatchThreadID, uint index : SV_GroupIndex)
{
	[branch] if (index < 64)
	{
		local_bins[index] = 0;
	}

	GroupMemoryBarrierWithGroupSync();

	[branch] if (id.x < (uint)exposure_settings.x && id.y < (uint)exposure_settings.y)
	{
		float2 center = (float2(id.xy) + 0.5) / exposure_settings.xy - 0.5;
		uint weight = dot(center, center) < 0.09 ? 4 : 1;

		InterlockedAdd(local_bins[luminance_bin(scene_texture[id.xy].rgb)], weight);
	}

	GroupMemoryBarrierWithGroupSync();

	[branch] if (index < 64)
	{
		histogram.InterlockedAdd(index * 4, local_bins[index]);
	}
}
/*
//=====================================================================================
*/
[numthreads(64, 1, 1)]
void cs_average(uint index : SV_GroupIndex)
{
	local_bins[index] = histogram.Load(index * 4);

	GroupMemoryBarrierWithGroupSync();

	[branch] if (index == 0)
	{
		uint total = 0;

		[loop] for (uint bin = 1; bin < 64; bin++)
		{
			total += local_bins[bin];
		}

		float low_cut = (float)total * exposure_limits.z;
		float high_cut = (float)total * exposure_limits.w;
		float running = 0.0;
		float weighted = 0.0;
		float weights = 0.0;

		[loop] for (uint bucket = 1; bucket < 64; bucket++)
		{
			float amount = (float)local_bins[bucket];
			float taken = max(0.0, min(running + amount, high_cut) - max(running, low_cut));
			float log_luminance = ((float)bucket - 1.0) / (62.0 * exposure_range.z) + exposure_range.x;

			weighted += taken * log_luminance;
			weights += taken;
			running += amount;
		}

		float average = weights > 0.0 ? weighted / weights : -2.0;
		float target = clamp(exposure_settings.z - average + exposure_settings.w, exposure_limits.x, exposure_limits.y);
		float4 state = exposure_state[0];
		float rate = target > state.x ? 1.6 : 3.0;
		float blend = state.w > 0.5 ? (1.0 - exp(-exposure_range.y * rate)) : 1.0;

		state.x = lerp(state.x, target, blend);
		state.y = exp2(state.x);
		state.z = average;
		state.w = 1.0;

		exposure_state[0] = state;
	}

	GroupMemoryBarrierWithGroupSync();

	histogram.Store(index * 4, 0);
}

//=====================================================================================
