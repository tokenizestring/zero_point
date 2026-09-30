
//=====================================================================================

#include "common.hlsli"

cbuffer particle_constants : register(b3)
{
	float4 particle_params;
};

Texture2D<float> scene_depth : register(t0);

struct particle_input
{
	float3 position : POSITION;
	float2 uv : TEXCOORD0;
	float4 color : COLOR0;
	float4 params : TEXCOORD1;
};

struct particle_output
{
	float4 position : SV_Position;
	float2 uv : TEXCOORD0;
	float4 color : COLOR0;
	float4 params : TEXCOORD1;
	float3 light : TEXCOORD2;
	float view_depth : TEXCOORD3;
};

//=====================================================================================

float particle_hash(float2 p)
{
	p = frac(p * float2(233.34, 851.73));
	p += dot(p, p + 23.45);

	return frac(p.x * p.y);
}
/*
//=====================================================================================
*/
float particle_noise(float2 p)
{
	float2 cell = floor(p);
	float2 f = frac(p);
	float2 u = f * f * (3.0 - 2.0 * f);

	return lerp(lerp(particle_hash(cell), particle_hash(cell + float2(1.0, 0.0)), u.x), lerp(particle_hash(cell + float2(0.0, 1.0)), particle_hash(cell + float2(1.0, 1.0)), u.x), u.y);
}
/*
//=====================================================================================
*/
particle_output vs_main(particle_input input)
{
	particle_output output;

	float4 clip = particle_params.x > 0.5 ? mul(float4(input.position, 1.0), viewmodel_projection) : mul(float4(input.position, 1.0), view_projection);

	output.position = clip;
	output.uv = input.uv;
	output.color = input.color;
	output.params = input.params;
	output.light = max(sh_irradiance(float3(0.0, 1.0, 0.0)), 0.0) / PI * 0.8 + sun_color.rgb * saturate(sun_direction.y + 0.2) * 0.12;
	output.view_depth = clip.w;

	return output;
}
/*
//=====================================================================================
*/
float4 ps_main(particle_output input) : SV_Target
{
	float2 centered = input.uv * 2.0 - 1.0;
	float radius = length(centered);
	uint kind = (uint)(input.params.x + 0.5);
	float age = input.params.y;
	float seed = input.params.w;
	float soft = 1.0;

	[branch] if (particle_params.x < 0.5)
	{
		float depth = scene_depth.Load(int3(input.position.xy, 0));
		float scene_w = particle_params.z / max(depth, 1e-7);

		soft = saturate((scene_w - input.view_depth) / max(input.params.z, 0.001));
	}

	float4 result = 0.0;

	[branch] if (kind == 0 || kind == 7)
	{
		float warp = particle_noise(centered * 2.2 + float2(seed * 13.0, -particle_params.y * 4.0 - seed * 5.0));
		float shape = saturate(1.0 - length(float2(centered.x * 1.35, centered.y * 0.85 + 0.15)) + (warp - 0.5) * 0.6);
		float heat = shape * saturate(1.0 - age * 1.1);
		float3 flame = lerp(float3(1.0, 0.14, 0.01), float3(1.0, 0.55, 0.16), saturate(heat * 1.7)) * input.color.rgb;

		result = float4(flame * heat * heat * 1.7 * soft, 0.0);
	}

	else if (kind == 1 || kind == 6)
	{
		float glow = pow(saturate(1.0 - radius), 2.5) * saturate(1.0 - age);

		result = float4(input.color.rgb * glow * soft, 0.0);
	}

	else
	{
		float edge = kind == 4 ? saturate((0.85 - max(abs(centered.x), abs(centered.y))) * 8.0) : saturate(1.0 - radius);
		float wisps = kind == 4 ? 1.0 : 0.55 + 0.45 * particle_noise(centered * 3.0 + seed * 17.0 + particle_params.y * 0.3);
		float fade = kind == 4 ? saturate((1.0 - age) * 4.0) : saturate(1.0 - age) * saturate(age * 6.0);
		float alpha = saturate(edge * edge * wisps * fade * input.color.a * soft);
		float3 lit = input.color.rgb * input.light;

		result = float4(lit * alpha, alpha);
	}

	return result;
}

//=====================================================================================
