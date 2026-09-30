
//=====================================================================================

#include "common.hlsli"

cbuffer shaft_constants : register(b7)
{
	float4 shaft_sun;
	float4 shaft_params;
};

Texture2D<float4> source_texture : register(t0);
Texture2D<float> depth_texture : register(t1);
SamplerState linear_clamp : register(s0);

static const int shaft_samples = 48;

struct fullscreen_output
{
	float4 position : SV_Position;
	float2 uv : TEXCOORD0;
};

//=====================================================================================

float4 ps_mask(fullscreen_output input) : SV_Target
{
	float sky = 0.0;

	[unroll] for (int tap = 0; tap < 4; tap++)
	{
		float2 offset = (float2(tap & 1, tap >> 1) - 0.5) * screen.zw * 2.0;

		sky += depth_texture.SampleLevel(linear_clamp, input.uv + offset, 0.0) <= 0.0 ? 0.25 : 0.0;
	}

	float2 delta = (input.uv - shaft_sun.xy) * float2(screen.x * screen.w, 1.0);
	float glow = exp(-dot(delta, delta) * shaft_params.w);

	return float4(sky * (0.2 + glow), 0.0, 0.0, 0.0);
}
/*
//=====================================================================================
*/
float4 ps_blur(fullscreen_output input) : SV_Target
{
	float2 step = (shaft_sun.xy - input.uv) * shaft_params.y / float(shaft_samples);
	float2 uv = input.uv + step * interleaved_gradient_noise(input.position.xy + frac(time_params.x * 7.31) * 64.0);
	float weight = 1.0;
	float total = 0.0;
	float sum = 0.0;

	[loop] for (int index = 0; index < shaft_samples; index++)
	{
		sum += source_texture.SampleLevel(linear_clamp, uv, 0.0).r * weight;
		total += weight;
		weight *= shaft_params.x;
		uv += step;
	}

	return float4(sun_color.rgb * (sum / total) * shaft_sun.z, 0.0);
}
/*
//=====================================================================================
*/
float4 ps_apply(fullscreen_output input) : SV_Target
{
	return float4(source_texture.SampleLevel(linear_clamp, input.uv, 0.0).rgb, 0.0);
}

//=====================================================================================
