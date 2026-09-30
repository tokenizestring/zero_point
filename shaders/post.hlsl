
//=====================================================================================

#include "common.hlsli"

cbuffer post_constants : register(b4)
{
	float4 post_params;
	float4 post_grade;
	float4 post_effects;
	float4 post_screen;
};

Texture2D<float4> hdr_texture : register(t0);
Texture2D<float4> bloom_texture : register(t1);
StructuredBuffer<float4> exposure_state : register(t2);
SamplerState linear_clamp : register(s0);

struct fullscreen_output
{
	float4 position : SV_Position;
	float2 uv : TEXCOORD0;
};

//=====================================================================================

fullscreen_output vs_fullscreen(uint id : SV_VertexID)
{
	fullscreen_output output;

	float2 uv = float2((id << 1) & 2, id & 2);

	output.position = float4(uv * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
	output.uv = uv;

	return output;
}
/*
//=====================================================================================
*/
float3 agx_contrast(float3 x)
{
	float3 x2 = x * x;
	float3 x4 = x2 * x2;

	return 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232;
}
/*
//=====================================================================================
*/
float3 agx(float3 color, float saturation, float punch)
{
	static const float3x3 inset = { { 0.842479062253094, 0.0784335999999992, 0.0792237451477643 }, { 0.0423282422610123, 0.878468636469772, 0.0791661274605434 }, { 0.0423756549057051, 0.0784336, 0.879142973793104 } };
	static const float3x3 outset = { { 1.19687900512017, -0.0980208811401368, -0.0990297440797205 }, { -0.0528968517574562, 1.15190312990417, -0.0989611768448433 }, { -0.0529716355144438, -0.0980434501171241, 1.15107367264116 } };
	static const float minimum_ev = -12.47393;
	static const float maximum_ev = 4.026069;

	color = mul(inset, max(color, 1e-10));

	color = clamp(log2(color), minimum_ev, maximum_ev);

	color = (color - minimum_ev) / (maximum_ev - minimum_ev);

	color = saturate(agx_contrast(color));

	color = pow(color, punch);

	float grey = luminance(color);

	color = grey + saturation * (color - grey);

	return saturate(mul(outset, color));
}
/*
//=====================================================================================
*/
float4 ps_tonemap(fullscreen_output input) : SV_Target
{
	float2 uv = input.uv;
	float2 centered = uv - 0.5;
	float2 texel = post_screen.zw;
	float3 color;

	[branch] if (post_effects.x > 0.0)
	{
		float2 shift = centered * post_effects.x;

		color.r = hdr_texture.SampleLevel(linear_clamp, uv - shift, 0.0).r;
		color.g = hdr_texture.SampleLevel(linear_clamp, uv, 0.0).g;
		color.b = hdr_texture.SampleLevel(linear_clamp, uv + shift, 0.0).b;
	}

	else
	{
		color = hdr_texture.SampleLevel(linear_clamp, uv, 0.0).rgb;
	}

	[branch] if (post_grade.w > 0.0)
	{
		float3 neighbours = hdr_texture.SampleLevel(linear_clamp, uv + float2(texel.x, 0.0), 0.0).rgb + hdr_texture.SampleLevel(linear_clamp, uv - float2(texel.x, 0.0), 0.0).rgb + hdr_texture.SampleLevel(linear_clamp, uv + float2(0.0, texel.y), 0.0).rgb + hdr_texture.SampleLevel(linear_clamp, uv - float2(0.0, texel.y), 0.0).rgb;
		float center_luma = luminance(color);
		float sharpened_luma = max(center_luma + (center_luma - luminance(neighbours) * 0.25) * post_grade.w, 0.0);

		color *= sharpened_luma / max(center_luma, 0.0001);
	}

	float3 bloom = bloom_texture.SampleLevel(linear_clamp, uv, 0.0).rgb;

	color = lerp(color, bloom, post_params.y);

	color *= exposure_state[0].y * post_params.x;

	color *= saturate(1.0 - post_effects.y * dot(centered, centered) * 1.5);

	color = agx(color, post_grade.x, post_grade.y);

	color = pow(saturate(color), post_grade.z);

	float noise = interleaved_gradient_noise(input.position.xy + post_params.w * 17.0);
	float grey = luminance(color);

	color += (noise - 0.5) * (1.0 / 255.0 + post_effects.z * 0.05 * (1.0 - grey));

	return float4(color, 1.0);
}

//=====================================================================================
