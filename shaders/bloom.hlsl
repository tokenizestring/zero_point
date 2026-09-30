
//=====================================================================================

#include "common.hlsli"

cbuffer bloom_constants : register(b7)
{
	float4 bloom_params;
};

Texture2D<float4> source_texture : register(t0);
SamplerState linear_clamp : register(s0);

struct fullscreen_output
{
	float4 position : SV_Position;
	float2 uv : TEXCOORD0;
};

//=====================================================================================

float3 fetch(float2 uv, float2 offset)
{
	return source_texture.SampleLevel(linear_clamp, uv + offset * bloom_params.xy, 0.0).rgb;
}
/*
//=====================================================================================
*/
float karis_weight(float3 c)
{
	return 1.0 / (1.0 + luminance(c));
}
/*
//=====================================================================================
*/
float4 ps_down(fullscreen_output input) : SV_Target
{
	float2 uv = input.uv;

	float3 a = fetch(uv, float2(-2.0, -2.0));
	float3 b = fetch(uv, float2(0.0, -2.0));
	float3 c = fetch(uv, float2(2.0, -2.0));
	float3 d = fetch(uv, float2(-2.0, 0.0));
	float3 e = fetch(uv, float2(0.0, 0.0));
	float3 f = fetch(uv, float2(2.0, 0.0));
	float3 g = fetch(uv, float2(-2.0, 2.0));
	float3 h = fetch(uv, float2(0.0, 2.0));
	float3 i = fetch(uv, float2(2.0, 2.0));
	float3 j = fetch(uv, float2(-1.0, -1.0));
	float3 k = fetch(uv, float2(1.0, -1.0));
	float3 l = fetch(uv, float2(-1.0, 1.0));
	float3 m = fetch(uv, float2(1.0, 1.0));

	float3 result;

	[branch] if (bloom_params.z > 0.5)
	{
		float3 group0 = (a + b + d + e) * 0.25;
		float3 group1 = (b + c + e + f) * 0.25;
		float3 group2 = (d + e + g + h) * 0.25;
		float3 group3 = (e + f + h + i) * 0.25;
		float3 group4 = (j + k + l + m) * 0.25;
		float w0 = karis_weight(group0) * 0.125;
		float w1 = karis_weight(group1) * 0.125;
		float w2 = karis_weight(group2) * 0.125;
		float w3 = karis_weight(group3) * 0.125;
		float w4 = karis_weight(group4) * 0.5;

		result = (group0 * w0 + group1 * w1 + group2 * w2 + group3 * w3 + group4 * w4) / (w0 + w1 + w2 + w3 + w4);
	}

	else
	{
		result = e * 0.125 + (a + c + g + i) * 0.03125 + (b + d + f + h) * 0.0625 + (j + k + l + m) * 0.125;
	}

	return float4(min(result, 65000.0), 1.0);
}
/*
//=====================================================================================
*/
float4 ps_up(fullscreen_output input) : SV_Target
{
	float2 uv = input.uv;

	float3 result = fetch(uv, float2(0.0, 0.0)) * 4.0;

	result += (fetch(uv, float2(-1.0, 0.0)) + fetch(uv, float2(1.0, 0.0)) + fetch(uv, float2(0.0, -1.0)) + fetch(uv, float2(0.0, 1.0))) * 2.0;
	result += fetch(uv, float2(-1.0, -1.0)) + fetch(uv, float2(1.0, -1.0)) + fetch(uv, float2(-1.0, 1.0)) + fetch(uv, float2(1.0, 1.0));

	return float4(result / 16.0 * bloom_params.w, 1.0);
}

//=====================================================================================
