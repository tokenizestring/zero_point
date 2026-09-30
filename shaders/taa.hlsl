
//=====================================================================================

#include "common.hlsli"

cbuffer taa_constants : register(b6)
{
	float4 taa_params;
};

Texture2D<float4> current_texture : register(t0);
Texture2D<float4> history_texture : register(t1);
Texture2D<float2> motion_texture : register(t2);
Texture2D<float> depth_texture : register(t3);
RWTexture2D<float4> output : register(u0);
SamplerState linear_clamp : register(s0);

//=====================================================================================

float3 to_ycocg(float3 c)
{
	return float3(dot(c, float3(0.25, 0.5, 0.25)), dot(c, float3(0.5, 0.0, -0.5)), dot(c, float3(-0.25, 0.5, -0.25)));
}
/*
//=====================================================================================
*/
float3 from_ycocg(float3 c)
{
	return float3(c.x + c.y - c.z, c.x + c.z, c.x - c.y - c.z);
}
/*
//=====================================================================================
*/
float3 compress(float3 c)
{
	return c / (1.0 + luminance(c));
}
/*
//=====================================================================================
*/
float3 decompress(float3 c)
{
	return c / max(1.0 - luminance(c), 0.0001);
}
/*
//=====================================================================================
*/
float3 sample_catmull_rom(float2 uv)
{
	float2 position = uv * screen.xy;
	float2 center = floor(position - 0.5) + 0.5;
	float2 f = position - center;
	float2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f));
	float2 w1 = 1.0 + f * f * (-2.5 + 1.5 * f);
	float2 w2 = f * (0.5 + f * (2.0 - 1.5 * f));
	float2 w3 = f * f * (-0.5 + 0.5 * f);
	float2 w12 = w1 + w2;
	float2 offset12 = w2 / w12;
	float2 tc0 = (center - 1.0) * screen.zw;
	float2 tc3 = (center + 2.0) * screen.zw;
	float2 tc12 = (center + offset12) * screen.zw;

	float3 result = history_texture.SampleLevel(linear_clamp, float2(tc12.x, tc0.y), 0.0).rgb * (w12.x * w0.y);

	result += history_texture.SampleLevel(linear_clamp, float2(tc0.x, tc12.y), 0.0).rgb * (w0.x * w12.y);
	result += history_texture.SampleLevel(linear_clamp, float2(tc12.x, tc12.y), 0.0).rgb * (w12.x * w12.y);
	result += history_texture.SampleLevel(linear_clamp, float2(tc3.x, tc12.y), 0.0).rgb * (w3.x * w12.y);
	result += history_texture.SampleLevel(linear_clamp, float2(tc12.x, tc3.y), 0.0).rgb * (w12.x * w3.y);

	float weight = w12.x * w0.y + w0.x * w12.y + w12.x * w12.y + w3.x * w12.y + w12.x * w3.y;

	return max(result / weight, 0.0);
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_main(uint3 id : SV_DispatchThreadID)
{
	[branch] if (id.x < (uint)screen.x && id.y < (uint)screen.y)
	{
		int2 pixel = int2(id.xy);
		int2 limit = int2(screen.xy) - 1;
		float4 source = current_texture[pixel];
		float3 current = compress(source.rgb);
		float reactive = saturate(source.a * 4.0);
		float3 mean = 0.0;
		float3 square = 0.0;
		float closest = 0.0;
		int2 closest_pixel = pixel;

		[unroll] for (int y = -1; y <= 1; y++)
		{
			[unroll] for (int x = -1; x <= 1; x++)
			{
				int2 neighbour = clamp(pixel + int2(x, y), 0, limit);
				float3 value = to_ycocg(compress(current_texture[neighbour].rgb));
				float depth = depth_texture[neighbour];

				mean += value;
				square += value * value;

				if (depth > closest)
				{
					closest = depth;
					closest_pixel = neighbour;
				}
			}
		}

		mean /= 9.0;

		float3 deviation = sqrt(max(square / 9.0 - mean * mean, 0.0));
		float2 motion = motion_texture[closest_pixel];
		float2 uv = (float2(id.xy) + 0.5) * screen.zw;
		float2 history_uv = uv + motion;
		float3 result = current;

		[branch] if (taa_params.y > 0.5 && all(history_uv > 0.0) && all(history_uv < 1.0))
		{
			float3 history = to_ycocg(compress(sample_catmull_rom(history_uv)));
			float3 box_min = mean - deviation * 1.15;
			float3 box_max = mean + deviation * 1.15;
			float3 center = (box_min + box_max) * 0.5;
			float3 extent = max((box_max - box_min) * 0.5, 0.0001);
			float3 offset = history - center;
			float3 units = abs(offset / extent);
			float largest = max(units.x, max(units.y, units.z));

			if (largest > 1.0)
			{
				history = center + offset / largest;
			}

			float speed = length(motion * screen.xy);
			float blend = max(lerp(taa_params.x, 0.25, saturate(speed / 24.0)), reactive);

			result = lerp(from_ycocg(history), current, blend);
		}

		output[id.xy] = float4(decompress(max(result, 0.0)), 1.0);
	}
}

//=====================================================================================
