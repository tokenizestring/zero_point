
//=====================================================================================

#include "common.hlsli"

Texture2DArray albedo_array : register(t0);
Texture2DArray normal_array : register(t1);
Texture2DArray rough_ao_array : register(t2);
Texture2DArray height_metal_array : register(t3);
StructuredBuffer<material_data> material_table : register(t4);
Texture2D<float4> terrain_shading : register(t5);
Texture2D<float4> terrain_splat0 : register(t6);
Texture2D<float4> terrain_splat1 : register(t7);
Texture2D<float4> terrain_splat2 : register(t8);
Texture2D<float4> terrain_splat3 : register(t9);
Texture2D<float> terrain_heights : register(t21);
SamplerState anisotropic_wrap : register(s0);
SamplerState terrain_clamp : register(s1);

cbuffer terrain_constants : register(b3)
{
	float4 terrain_params;
	float4 terrain_morph[8];
	uint4 terrain_layers[4];
	float4 terrain_camera;
};

//=====================================================================================

struct patch_input
{
	float2 grid : POSITION;
	float4 patch : INSTANCE;
};

struct terrain_vertex
{
	float4 position : SV_Position;
	float3 world_position : POSITION0;
	float4 current_clip : TEXCOORD1;
	float4 previous_clip : TEXCOORD2;
};

struct gbuffer_output
{
	float4 albedo : SV_Target0;
	float4 normal : SV_Target1;
	float4 surface : SV_Target2;
	float4 emissive : SV_Target3;
	float2 motion : SV_Target4;
};

struct layer_result
{
	float3 albedo;
	float3 normal;
	float roughness;
	float occlusion;
	float height;
};

//=====================================================================================

float terrain_height(float2 world_xz)
{
	return terrain_heights.SampleLevel(terrain_clamp, (world_xz - terrain_params.x + 0.5) / terrain_params.w, 0.0);
}
/*
//=====================================================================================
*/
float3 terrain_position(patch_input input)
{
	uint level = (uint)input.patch.w;
	float2 world_xz = input.patch.xy + input.grid * input.patch.z;
	float height = terrain_height(world_xz);
	float distance = length(float3(world_xz.x, height, world_xz.y) - terrain_camera.xyz);
	float morph = saturate((distance - terrain_morph[level].x) * terrain_morph[level].y);
	float2 grid = input.grid - frac(input.grid * 0.5) * 2.0 * morph;

	world_xz = input.patch.xy + grid * input.patch.z;

	return float3(world_xz.x, terrain_height(world_xz), world_xz.y);
}
/*
//=====================================================================================
*/
terrain_vertex vs_main(patch_input input)
{
	terrain_vertex output;

	float3 world_position = terrain_position(input);

	output.position = mul(float4(world_position, 1.0), view_projection);
	output.current_clip = output.position;
	output.previous_clip = mul(float4(world_position, 1.0), previous_view_projection);
	output.world_position = world_position;

	return output;
}
/*
//=====================================================================================
*/
float4 vs_shadow(patch_input input) : SV_Position
{
	return mul(float4(terrain_position(input), 1.0), cascade_matrices[(uint)shadow_params.w]);
}
/*
//=====================================================================================
*/
layer_result sample_projection(material_data material, float2 uv, float3 tangent, float3 bitangent, float3 normal)
{
	layer_result result;

	float3 coordinate = float3(uv, material.layer);
	float2 normal_xy = (normal_array.Sample(anisotropic_wrap, coordinate).rg * 2.0 - 1.0) * material.normal_strength;
	float2 rough_ao = rough_ao_array.Sample(anisotropic_wrap, coordinate).rg;
	float3 local = float3(normal_xy, sqrt(saturate(1.0 - dot(normal_xy, normal_xy))));

	result.albedo = albedo_array.Sample(anisotropic_wrap, coordinate).rgb;
	result.normal = tangent * local.x + bitangent * local.y + normal * local.z;
	result.roughness = rough_ao.x;
	result.occlusion = rough_ao.y;
	result.height = height_metal_array.Sample(anisotropic_wrap, coordinate).r;

	return result;
}
/*
//=====================================================================================
*/
layer_result sample_layer(uint index, float3 world_position, float3 normal, float distance)
{
	material_data material = material_table[index];

	float3 tangent = normalize(float3(1.0, 0.0, 0.0) - normal * normal.x);
	float3 bitangent = -cross(normal, tangent);
	float scale = material.uv_scale;

	layer_result result;

	[branch] if (material.flags & 2u)
	{
		float3 blend = pow(abs(normal), 4.0);

		blend /= dot(blend, 1.0);

		layer_result top = sample_projection(material, world_position.xz * scale, tangent, bitangent, normal);
		layer_result front = sample_projection(material, float2(world_position.x, -world_position.y) * scale, float3(1.0, 0.0, 0.0), float3(0.0, -1.0, 0.0), normal);
		layer_result side = sample_projection(material, float2(world_position.z, -world_position.y) * scale, float3(0.0, 0.0, 1.0), float3(0.0, -1.0, 0.0), normal);

		result.albedo = top.albedo * blend.y + front.albedo * blend.z + side.albedo * blend.x;
		result.normal = top.normal * blend.y + front.normal * blend.z + side.normal * blend.x;
		result.roughness = top.roughness * blend.y + front.roughness * blend.z + side.roughness * blend.x;
		result.occlusion = top.occlusion * blend.y + front.occlusion * blend.z + side.occlusion * blend.x;
		result.height = top.height * blend.y + front.height * blend.z + side.height * blend.x;
	}

	else
	{
		result = sample_projection(material, world_position.xz * scale, tangent, bitangent, normal);

		float far_weight = saturate((distance - 18.0) / 70.0) * 0.55;

		[branch] if (far_weight > 0.01)
		{
			layer_result far = sample_projection(material, world_position.xz * scale * 0.19, tangent, bitangent, normal);

			result.albedo = lerp(result.albedo, far.albedo, far_weight);
			result.normal = lerp(result.normal, far.normal, far_weight);
			result.roughness = lerp(result.roughness, far.roughness, far_weight);
		}
	}

	result.albedo *= material.tint.rgb;
	result.roughness = saturate(result.roughness * material.roughness_scale + material.roughness_bias);

	return result;
}
/*
//=====================================================================================
*/
gbuffer_output ps_main(terrain_vertex input)
{
	gbuffer_output output;

	float2 uv = (input.world_position.xz - terrain_params.x) * terrain_params.z;
	float4 shading = terrain_shading.Sample(terrain_clamp, uv);
	float4 splat0 = terrain_splat0.Sample(terrain_clamp, uv);
	float4 splat1 = terrain_splat1.Sample(terrain_clamp, uv);
	float4 splat2 = terrain_splat2.Sample(terrain_clamp, uv);
	float4 splat3 = terrain_splat3.Sample(terrain_clamp, uv);
	float2 normal_xz = shading.rg * 2.0 - 1.0;
	float3 geometric = normalize(float3(normal_xz.x, sqrt(saturate(1.0 - dot(normal_xz, normal_xz))), normal_xz.y));
	float distance = length(input.world_position - camera_position.xyz);
	float weights[16] = { splat0.r, splat0.g, splat0.b, splat0.a, splat1.r, splat1.g, splat1.b, splat1.a, splat2.r, splat2.g, splat2.b, splat2.a, splat3.r, splat3.g, splat3.b, splat3.a };
	float blended[16];
	float highest = 0.0;

	float3 albedo = 0.0;
	float3 normal = 0.0;
	float roughness = 0.0;
	float occlusion = 0.0;
	float total = 0.0;

	layer_result layers[16];

	[unroll] for (uint index = 0; index < 16; index++)
	{
		blended[index] = 0.0;

		layers[index] = (layer_result)0;

		[branch] if (weights[index] > 0.02)
		{
			layers[index] = sample_layer(terrain_layers[index / 4][index % 4], input.world_position, geometric, distance);

			blended[index] = weights[index] + layers[index].height * 0.6;

			highest = max(highest, blended[index]);
		}
	}

	[unroll] for (uint layer = 0; layer < 16; layer++)
	{
		float weight = weights[layer] > 0.02 ? max(blended[layer] - highest + 0.25, 0.0) : 0.0;

		albedo += layers[layer].albedo * weight;
		normal += layers[layer].normal * weight;
		roughness += layers[layer].roughness * weight;
		occlusion += layers[layer].occlusion * weight;
		total += weight;
	}

	total = max(total, 0.0001);
	albedo = albedo / total * lerp(0.78, 1.18, shading.a);
	normal = normalize(total > 0.001 ? normal : geometric);
	roughness /= total;
	occlusion = occlusion / total * lerp(0.35, 1.0, shading.b);

	[branch] if (water_params.x > 0.5)
	{
		float ripple = sin(input.world_position.x * 0.9 + input.world_position.z * 0.6) * 0.12 + sin(input.world_position.z * 1.7 - input.world_position.x * 0.4) * 0.08;
		float wet = saturate((water_params.y + 0.55 + ripple - input.world_position.y) / 0.35);

		albedo *= lerp(1.0, 0.52, wet);
		roughness = lerp(roughness, 0.16, wet * 0.9);
		normal = normalize(lerp(normal, geometric, wet * 0.55));
	}

	float2 current_ndc = input.current_clip.xy / input.current_clip.w - jitter.xy;
	float2 previous_ndc = input.previous_clip.xy / input.previous_clip.w;

	output.albedo = float4(saturate(albedo), 1.0);
	output.normal = float4(normal, roughness);
	output.surface = float4(0.0, occlusion, 0.0, 0.5);
	output.emissive = 0.0;
	output.motion = (previous_ndc - current_ndc) * float2(0.5, -0.5);

	return output;
}

//=====================================================================================
