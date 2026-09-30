
//=====================================================================================

#include "common.hlsli"

Texture2DArray albedo_array : register(t0);
StructuredBuffer<material_data> material_table : register(t4);
SamplerState anisotropic_wrap : register(s0);

//=====================================================================================

struct vertex_input
{
	float3 position : POSITION;
};

struct alpha_input
{
	float3 position : POSITION;
	float2 uv : TEXCOORD0;
	uint material : MATERIAL;
};

struct instanced_shadow_input
{
	float3 position : POSITION;
	float4 placement : INSTANCE0;
	float4 params : INSTANCE1;
};

struct instanced_alpha_input
{
	float3 position : POSITION;
	float2 uv : TEXCOORD0;
	uint material : MATERIAL;
	float4 placement : INSTANCE0;
	float4 params : INSTANCE1;
};

struct alpha_output
{
	float4 position : SV_Position;
	float2 uv : TEXCOORD0;
	nointerpolation uint material : MATERIAL;
};

//=====================================================================================

float4 vs_main(vertex_input input) : SV_Position
{
	return mul(mul(float4(input.position, 1.0), world), cascade_matrices[(uint)shadow_params.w]);
}
/*
//=====================================================================================
*/
float4 vs_skinned(skinned_input input) : SV_Position
{
	float3 position = skin_point(input.position, skin_rows(input.joints, input.weights, (uint)skin_params.x), skin_translation(input.joints, input.weights, (uint)skin_params.x));

	return mul(mul(float4(position, 1.0), world), cascade_matrices[(uint)shadow_params.w]);
}
/*
//=====================================================================================
*/
float4 vs_instanced(instanced_shadow_input input) : SV_Position
{
	return mul(float4(foliage_transform(input.position, input.placement, input.params, time_params.x), 1.0), cascade_matrices[(uint)shadow_params.w]);
}
/*
//=====================================================================================
*/
alpha_output vs_instanced_alpha(instanced_alpha_input input)
{
	alpha_output output;

	output.position = mul(float4(foliage_transform(input.position, input.placement, input.params, time_params.x), 1.0), cascade_matrices[(uint)shadow_params.w]);
	output.uv = input.uv;
	output.material = input.material;

	return output;
}
/*
//=====================================================================================
*/
alpha_output vs_alpha(alpha_input input)
{
	alpha_output output;

	output.position = mul(mul(float4(input.position, 1.0), world), cascade_matrices[(uint)shadow_params.w]);
	output.uv = input.uv;
	output.material = input.material;

	return output;
}
/*
//=====================================================================================
*/
void ps_alpha(alpha_output input)
{
	material_data material = material_table[input.material];

	clip(albedo_array.Sample(anisotropic_wrap, float3(input.uv * material.uv_scale * float2(1.0, material.aspect), material.layer)).a - 0.5);
}

//=====================================================================================
