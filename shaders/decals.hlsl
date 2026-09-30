
//=====================================================================================

#include "common.hlsli"

cbuffer decal_constants : register(b3)
{
	float4 decal_params;
};

Texture2D<float> scene_depth : register(t0);
Texture2D<float4> scene_surface : register(t1);
Texture2D<float4> mark_color : register(t2);
Texture2D<float4> mark_shape : register(t3);
SamplerState mark_sampler : register(s0);

struct decal_input
{
	float3 position : POSITION;
	float4 center : INSTANCE0;
	float4 normal : INSTANCE1;
	float4 axis : INSTANCE2;
	float4 tint : INSTANCE3;
};

struct decal_output
{
	float4 position : SV_Position;
	nointerpolation float4 center : TEXCOORD0;
	nointerpolation float4 normal : TEXCOORD1;
	nointerpolation float4 axis : TEXCOORD2;
	nointerpolation float4 tint : TEXCOORD3;
};

struct decal_targets
{
	float4 albedo : SV_Target0;
	float4 normal : SV_Target1;
};

//=====================================================================================

decal_output vs_main(decal_input input)
{
	decal_output output;

	float3 side = cross(input.axis.xyz, input.normal.xyz);
	float3 world_position = input.center.xyz + (side * input.position.x + input.axis.xyz * input.position.y) * input.center.w + input.normal.xyz * (input.position.z * input.normal.w);

	output.position = mul(float4(world_position, 1.0), view_projection);
	output.center = input.center;
	output.normal = input.normal;
	output.axis = input.axis;
	output.tint = input.tint;

	return output;
}
/*
//=====================================================================================
*/
decal_targets ps_main(decal_output input)
{
	decal_targets output;

	int3 pixel = int3(input.position.xy, 0);
	float depth = scene_depth.Load(pixel);
	uint flags = (uint)(scene_surface.Load(pixel).b * 255.0 + 0.5);
	float2 uv = input.position.xy * screen.zw;
	float4 clip_position = mul(float4(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0, depth, 1.0), inverse_view_projection);
	float3 world_position = clip_position.xyz / clip_position.w;
	float3 across = ddx(world_position);
	float3 down = ddy(world_position);
	float3 side = cross(input.axis.xyz, input.normal.xyz);
	float3 offset = world_position - input.center.xyz;
	float3 local = float3(dot(offset, side), dot(offset, input.axis.xyz), dot(offset, input.normal.xyz)) / float3(input.center.w, input.center.w, input.normal.w);

	clip(depth <= 0.0 || (flags & 13u) != 0u ? -1.0 : 1.0 - max(abs(local.x), max(abs(local.y), abs(local.z))));

	float cell = input.axis.w;
	float2 corner = float2(fmod(cell, 8.0), floor(cell / 8.0)) / 8.0;
	float2 atlas = corner + (local.xy * 0.5 + 0.5) / 8.0;
	float2 atlas_dx = float2(dot(across, side), dot(across, input.axis.xyz)) / (input.center.w * 16.0);
	float2 atlas_dy = float2(dot(down, side), dot(down, input.axis.xyz)) / (input.center.w * 16.0);
	float4 color = mark_color.SampleGrad(mark_sampler, atlas, atlas_dx, atlas_dy);
	float4 shape = mark_shape.SampleGrad(mark_sampler, atlas, atlas_dx, atlas_dy);
	float3 facet = cross(across, down);
	float facing = abs(dot(facet / max(length(facet), 1e-12), input.normal.xyz));
	float fade = input.tint.a * smoothstep(0.2, 0.5, facing) * saturate((1.0 - abs(local.z)) * 3.0);
	float2 tilt = shape.rg * 2.0 - 1.0;
	float3 bumped = normalize(side * tilt.x + input.axis.xyz * tilt.y + input.normal.xyz * sqrt(saturate(1.0 - dot(tilt, tilt))));
	float weight = lerp(shape.b, max(shape.b, color.a), decal_params.x);

	output.albedo = float4(color.rgb * input.tint.rgb, color.a * fade);
	output.normal = float4(bumped, weight * fade);

	return output;
}

//=====================================================================================
