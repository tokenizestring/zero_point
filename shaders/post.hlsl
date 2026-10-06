
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
Texture2D<float2> motion_texture : register(t3);
Texture2D<float> depth_texture : register(t4);
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
float3 daltonize(float3 color, float mode)
{
	static const float3x3 to_cones = { { 17.8824, 43.5161, 4.11935 }, { 3.45565, 27.1554, 3.86714 }, { 0.0299566, 0.184309, 1.46709 } };
	static const float3x3 from_cones = { { 0.0809444479, -0.130504409, 0.116721066 }, { -0.0102485335, 0.0540193266, -0.113614708 }, { -0.000365296938, -0.00412161469, 0.693511405 } };

	float3 cones = mul(to_cones, color);
	float3 seen = mode < 1.5 ? float3(2.02344 * cones.y - 2.52581 * cones.z, cones.y, cones.z) : (mode < 2.5 ? float3(cones.x, 0.494207 * cones.x + 1.24827 * cones.z, cones.z) : float3(cones.x, cones.y, -0.395913 * cones.x + 0.801109 * cones.y));
	float3 error = color - mul(from_cones, seen);

	return saturate(color + float3(0.0, error.r * 0.7 + error.g, error.r * 0.7 + error.b));
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

	[branch] if (post_params.z > 0.0)
	{
		float2 motion = motion_texture.SampleLevel(linear_clamp, uv, 0.0);

		[branch] if (depth_texture.SampleLevel(linear_clamp, uv, 0.0) <= 0.0)
		{
			float2 ndc = uv * float2(2.0, -2.0) + float2(-1.0, 1.0);
			float4 far_point = mul(float4(ndc, 0.000001, 1.0), inverse_view_projection);
			float4 previous = mul(far_point, previous_view_projection);

			motion = (previous.xy / previous.w - ndc) * float2(0.5, -0.5);
		}

		float2 streak = motion * post_params.z;
		float span = length(streak * post_screen.xy);

		[branch] if (span > 1.0)
		{
			streak *= min(1.0, 48.0 / span);

			float3 total = color;

			[unroll] for (int tap = 0; tap < 6; tap++)
			{
				float along = (float(tap) + 0.5) / 6.0 - 0.5;

				total += hdr_texture.SampleLevel(linear_clamp, uv + streak * along, 0.0).rgb;
			}

			color = total / 7.0;
		}
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

	[branch] if (post_effects.w > 0.5)
	{
		color = daltonize(color, post_effects.w);
	}

	float noise = interleaved_gradient_noise(input.position.xy + post_params.w * 17.0);
	float grey = luminance(color);

	color += (noise - 0.5) * (1.0 / 255.0 + post_effects.z * 0.05 * (1.0 - grey));

	return float4(color, 1.0);
}

//=====================================================================================
