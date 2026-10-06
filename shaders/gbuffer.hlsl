
//=====================================================================================

#include "common.hlsli"

Texture2DArray albedo_array : register(t0);
Texture2DArray normal_array : register(t1);
Texture2DArray rough_ao_array : register(t2);
Texture2DArray height_metal_array : register(t3);
StructuredBuffer<material_data> material_table : register(t4);
Texture2D<float> grass_heights : register(t21);
Texture2D<float4> grass_splat : register(t22);
Texture2D<float> grass_mask : register(t23);
SamplerState anisotropic_wrap : register(s0);
SamplerState grass_sampler : register(s1);

cbuffer grass_constants : register(b4)
{
	float4 grass_rings[2];
	float4 grass_sprites[4];
	float4 grass_terrain;
	float4 grass_player;
	uint4 grass_materials;
};

//=====================================================================================

struct vertex_input
{
	float3 position : POSITION;
	float3 normal : NORMAL;
	float4 tangent : TANGENT;
	float2 uv : TEXCOORD0;
	uint material : MATERIAL;
};

struct grass_input
{
	float3 position : POSITION;
	float3 normal : NORMAL;
	float2 uv : TEXCOORD0;
	uint instance : SV_InstanceID;
};

struct instanced_input
{
	float3 position : POSITION;
	float3 normal : NORMAL;
	float4 tangent : TANGENT;
	float2 uv : TEXCOORD0;
	uint material : MATERIAL;
	float4 placement : INSTANCE0;
	float4 params : INSTANCE1;
};

struct pixel_input
{
	float4 position : SV_Position;
	float3 world_position : POSITION0;
	float3 normal : NORMAL;
	float4 tangent : TANGENT;
	float2 uv : TEXCOORD0;
	nointerpolation uint material : MATERIAL;
	float4 current_clip : TEXCOORD1;
	float4 previous_clip : TEXCOORD2;
	nointerpolation float fade : TEXCOORD3;
};

struct impostor_input
{
	float4 position : SV_Position;
	float3 right : NORMAL0;
	float3 facing : NORMAL1;
	float4 uv : TEXCOORD0;
	nointerpolation uint material : MATERIAL;
	float4 current_clip : TEXCOORD1;
	float4 previous_clip : TEXCOORD2;
	nointerpolation float fade : TEXCOORD3;
	nointerpolation float blend : TEXCOORD4;
};

static const float impostor_frames = 8.0;
static const float2 impostor_grid = float2(4.0, 2.0);

struct gbuffer_output
{
	float4 albedo : SV_Target0;
	float4 normal : SV_Target1;
	float4 surface : SV_Target2;
	float4 emissive : SV_Target3;
	float2 motion : SV_Target4;
};

//=====================================================================================

pixel_input vs_main(vertex_input input)
{
	pixel_input output;

	float3 moved_normal = input.normal;
	float4 local = float4(creature_motion(input.position, moved_normal), 1.0);
	float4 placed = mul(local, world);
	float4 previous_placed = mul(local, previous_world);
	float3 placed_normal = mul(moved_normal, (float3x3)world);
	float3 placed_tangent = mul(input.tangent.xyz, (float3x3)world);

	[branch] if (object_params.y > 0.5)
	{
		output.position = mul(placed, viewmodel_projection);
		output.current_clip = output.position;
		output.previous_clip = mul(previous_placed, viewmodel_projection);
		output.world_position = mul(placed, inverse_view).xyz;
		output.normal = normalize(mul(placed_normal, (float3x3)inverse_view));
		output.tangent = float4(normalize(mul(placed_tangent, (float3x3)inverse_view)), input.tangent.w);
	}

	else
	{
		output.position = mul(placed, view_projection);
		output.current_clip = output.position;
		output.previous_clip = mul(previous_placed, previous_view_projection);
		output.world_position = placed.xyz;
		output.normal = normalize(placed_normal);
		output.tangent = float4(normalize(placed_tangent), input.tangent.w);
	}

	output.uv = input.uv;
	output.material = object_params.x >= 0.0 ? (uint)object_params.x : input.material;
	output.fade = 0.0;

	return output;
}
/*
//=====================================================================================
*/
pixel_input vs_skinned(skinned_input input)
{
	float3x4 current_rows = skin_rows(input.joints, input.weights, (uint)skin_params.x);
	float3x4 previous_rows = skin_rows(input.joints, input.weights, (uint)skin_params.y);
	float3 current_position = skin_point(input.position, current_rows, skin_translation(input.joints, input.weights, (uint)skin_params.x));
	float3 previous_position = skin_point(input.position, previous_rows, skin_translation(input.joints, input.weights, (uint)skin_params.y));

	vertex_input skinned;

	skinned.position = current_position;
	skinned.normal = normalize(skin_vector(input.normal, current_rows));
	skinned.tangent = float4(normalize(skin_vector(input.tangent.xyz, current_rows)), input.tangent.w);
	skinned.uv = input.uv;
	skinned.material = input.material;

	pixel_input output = vs_main(skinned);

	[branch] if (object_params.y < 0.5)
	{
		output.previous_clip = mul(mul(float4(previous_position, 1.0), previous_world), previous_view_projection);
	}

	else
	{
		output.previous_clip = mul(mul(float4(previous_position, 1.0), previous_world), viewmodel_projection);
	}

	return output;
}
/*
//=====================================================================================
*/
pixel_input vs_instanced(instanced_input input)
{
	pixel_input output;

	float3 world_position = foliage_transform(input.position, input.placement, input.params, time_params.x);
	float3 previous_position = foliage_transform(input.position, input.placement, input.params, time_params.y);

	output.position = mul(float4(world_position, 1.0), view_projection);
	output.current_clip = output.position;
	output.previous_clip = mul(float4(previous_position, 1.0), previous_view_projection);
	output.world_position = world_position;
	output.normal = normalize(foliage_rotate(input.normal, input.placement.w + foliage_turn(input.position, input.params)));
	output.tangent = float4(normalize(foliage_rotate(input.tangent.xyz, input.placement.w + foliage_turn(input.position, input.params))), input.tangent.w);
	output.uv = input.uv;
	output.material = input.material;
	output.fade = input.params.w;

	return output;
}
/*
//=====================================================================================
*/
float2 impostor_cell(float frame, float2 uv)
{
	return (float2(fmod(frame, impostor_grid.x), floor(frame / impostor_grid.x)) + uv) / impostor_grid;
}
/*
//=====================================================================================
*/
impostor_input vs_impostor(instanced_input input)
{
	impostor_input output;

	float3 base = input.placement.xyz;
	float2 toward = camera_position.xz - base.xz;
	float3 facing = normalize(float3(toward.x, 0.0, toward.y + 1e-4));
	float3 right = float3(-facing.z, 0.0, facing.x);
	float3 local = foliage_rotate(facing, -input.placement.w);
	float frame = frac(atan2(local.x, local.z) / TWO_PI + 1.0) * impostor_frames;
	float first = floor(frame);
	float3 world_position = base + (right * input.position.x + float3(0.0, input.position.y, 0.0)) * input.params.x;

	output.position = mul(float4(world_position, 1.0), view_projection);
	output.current_clip = output.position;
	output.previous_clip = mul(float4(world_position, 1.0), previous_view_projection);
	output.right = right;
	output.facing = facing;
	output.uv = float4(impostor_cell(first, input.uv), impostor_cell(fmod(first + 1.0, impostor_frames), input.uv));
	output.material = input.material;
	output.fade = input.params.w;
	output.blend = frame - first;

	return output;
}
/*
//=====================================================================================
*/
float grass_hash(float2 value)
{
	return frac(sin(dot(value, float2(127.1, 311.7))) * 43758.5453);
}
/*
//=====================================================================================
*/
float3 grass_wind(float height, float2 world_xz, float seed, float scale, float time_value)
{
	float2 direction = float2(0.8, 0.6);
	float gust = sin(dot(world_xz, direction) * 0.16 - time_value * 1.5) * 0.5 + 0.5;
	float flutter = sin(time_value * 5.3 + seed * 17.0 + world_xz.x * 0.7) * 0.6 + sin(time_value * 3.4 + seed * 9.0 + world_xz.y * 0.9) * 0.4;
	float sway = (0.06 + 0.22 * gust * gust + 0.04 * flutter) * height * height * scale;

	return float3(direction.x * sway, 0.0, direction.y * sway);
}
/*
//=====================================================================================
*/
float3 grass_push(float3 base, float height, float tall)
{
	float2 away = base.xz - grass_player.xz;
	float reach = length(away);
	float strength = grass_player.w > 0.0 && abs(base.y - grass_player.y) < 1.5 ? saturate(1.0 - reach / grass_player.w) : 0.0;
	float bend = strength * strength * height * height * tall;

	return float3(away.x / max(reach, 0.05) * bend * 0.8, -bend * 0.55, away.y / max(reach, 0.05) * bend * 0.8);
}
/*
//=====================================================================================
*/
pixel_input vs_grass(grass_input input)
{
	pixel_input output;

	uint near_count = (uint)(grass_rings[0].w * grass_rings[0].w);
	uint ring = input.instance >= near_count ? 1 : 0;
	uint local = input.instance - ring * near_count;
	float4 params = grass_rings[ring];
	uint count = (uint)params.w;
	float2 cell = floor(camera_position.xz / params.x) + float2(local % count, local / count) - floor(params.w * 0.5);
	float2 seed_cell = cell + ring * 173.0;
	float seed = grass_hash(seed_cell);
	float2 world_xz = (cell + float2(grass_hash(seed_cell + 3.1), grass_hash(seed_cell + 7.7))) * params.x;
	float distance = length(world_xz - camera_position.xz);
	float height = grass_heights.SampleLevel(grass_sampler, (world_xz - grass_terrain.x + 0.5) / grass_terrain.z, 0.0);
	float4 splat = grass_splat.SampleLevel(grass_sampler, (world_xz - grass_terrain.x) / grass_terrain.y, 0.0);
	float density = splat.r * (1.0 - grass_mask.SampleLevel(grass_sampler, (world_xz - grass_terrain.x) / grass_terrain.y, 0.0));
	float fade = saturate((params.y - distance) / (params.y * 0.25)) * (ring == 1 ? saturate((distance - params.z) / 5.0) : 1.0);
	float dryness = splat.g;
	float pick = grass_hash(seed_cell + 23.0);
	uint sprite = pick < dryness * 0.7 ? 2 : (pick < dryness * 0.7 + 0.22 ? 1 : (grass_hash(seed_cell + 29.0) < 0.55 ? 0 : 3));
	float4 rect = grass_sprites[sprite];
	float size = (0.75 + 0.5 * grass_hash(seed_cell + 11.0)) * fade * (seed < density ? 1.0 : 0.0) * (height > 0.8 ? 1.0 : 0.0) * grass_terrain.w * (ring == 1 ? 1.45 : 1.0) * max(splat.b * 2.0, 0.35);
	float yaw = grass_hash(seed_cell + 19.0) * 6.2831853;
	float2 extent = float2(rect.z - rect.x, rect.w - rect.y) * 2.0 * size;
	float3 local_position = input.position * float3(extent.x, extent.y * 0.94, extent.x) + input.normal * (input.position.y * extent.y * 0.36);
	float3 base = float3(world_xz.x, height - 0.03, world_xz.y);
	float3 pushed = grass_push(base, input.position.y, extent.y);
	float3 world_position = base + foliage_rotate(local_position, yaw) + grass_wind(input.position.y, world_xz, seed, extent.y, time_params.x) + pushed;
	float3 previous_position = base + foliage_rotate(local_position, yaw) + grass_wind(input.position.y, world_xz, seed, extent.y, time_params.y) + pushed;
	float3 outward = foliage_rotate(input.normal, yaw);

	output.position = mul(float4(world_position, 1.0), view_projection);
	output.current_clip = output.position;
	output.previous_clip = mul(float4(previous_position, 1.0), previous_view_projection);
	output.world_position = world_position;
	output.normal = normalize(outward * 0.45 + float3(0.0, 0.89, 0.0));
	output.tangent = float4(normalize(cross(float3(0.0, 1.0, 0.0), outward)), 1.0);
	output.uv = float2(lerp(rect.x, rect.z, input.uv.x), lerp(rect.y, rect.w, input.uv.y));
	output.material = sprite == 2 ? grass_materials.w : (dryness > 0.5 ? grass_materials.z : grass_materials[(uint)(grass_hash(seed_cell + 31.0) * 1.99)]);
	output.fade = 0.0;

	return output;
}
/*
//=====================================================================================
*/
void lod_dither(float fade, float2 pixel)
{
	[branch] if (fade != 0.0)
	{
		float noise = interleaved_gradient_noise(pixel + 5.588238 * fmod(exposure_params.w, 64.0));

		clip(fade > 0.0 ? noise - fade : -fade - noise);
	}
}
/*
//=====================================================================================
*/
float2 parallax(float2 uv, float2 dx, float2 dy, float3 view_tangent, uint layer, float2 amount)
{
	float steps = lerp(28.0, 10.0, saturate(view_tangent.z));
	float step_depth = 1.0 / steps;
	float2 shift = (view_tangent.xy / max(view_tangent.z, 0.2)) * amount / steps;
	float2 current = uv;
	float depth = 0.0;
	float surface = 1.0 - height_metal_array.SampleGrad(anisotropic_wrap, float3(current, layer), dx, dy).r;
	float previous_surface = surface;

	[loop] for (int index = 0; index < 32 && depth < surface; index++)
	{
		previous_surface = surface;

		current -= shift;

		depth += step_depth;

		surface = 1.0 - height_metal_array.SampleGrad(anisotropic_wrap, float3(current, layer), dx, dy).r;
	}

	float after = surface - depth;
	float before = previous_surface - (depth - step_depth);
	float weight = after / (after - before + 1e-5);

	return lerp(current, current + shift, saturate(weight));
}
/*
//=====================================================================================
*/
gbuffer_output shade(pixel_input input, bool front, bool alpha_test)
{
	gbuffer_output output;

	material_data material = material_table[input.material];

	float3 geometric = normalize(input.normal);
	float3 tangent = normalize(input.tangent.xyz - geometric * dot(geometric, input.tangent.xyz));
	float3 bitangent = cross(geometric, tangent) * input.tangent.w;
	float2 uv_scale = float2(1.0, material.aspect) * material.uv_scale;
	float2 uv = input.uv * uv_scale;
	float2 dx = ddx(uv);
	float2 dy = ddy(uv);
	float3 geometric_dx = ddx(geometric);
	float3 geometric_dy = ddy(geometric);
	float curvature = min(2.0 * 0.25 * (dot(geometric_dx, geometric_dx) + dot(geometric_dy, geometric_dy)), 0.2);

	[branch] if ((material.flags & 1u) && quality_params.w > 0.5 && material.height_scale > 0.0)
	{
		float3 view_direction = normalize(camera_position.xyz - input.world_position);
		float3 view_tangent = float3(dot(view_direction, tangent), dot(view_direction, bitangent), dot(view_direction, geometric));

		uv = parallax(uv, dx, dy, view_tangent, material.layer, uv_scale * material.height_scale);
	}

	float4 albedo = albedo_array.SampleGrad(anisotropic_wrap, float3(uv, material.layer), dx, dy);

	[branch] if (skin_params.w > 0.0)
	{
		float closeness = saturate((skin_params.w - length(input.world_position - camera_position.xyz)) / 0.12);

		clip(interleaved_gradient_noise(input.position.xy + 5.588238 * fmod(exposure_params.w, 64.0)) - closeness);
	}

	if (alpha_test)
	{
		clip(albedo.a - 0.5);

		lod_dither(input.fade, input.position.xy);
	}

	float2 normal_xy = (normal_array.SampleGrad(anisotropic_wrap, float3(uv, material.layer), dx, dy).rg * 2.0 - 1.0) * material.normal_strength;
	float2 rough_ao = rough_ao_array.SampleGrad(anisotropic_wrap, float3(uv, material.layer), dx, dy).rg;
	float2 height_metal = height_metal_array.SampleGrad(anisotropic_wrap, float3(uv, material.layer), dx, dy).rg;

	float3 normal_tangent = normalize(float3(normal_xy, sqrt(saturate(1.0 - dot(normal_xy, normal_xy)))));
	float3 normal = normalize(tangent * normal_tangent.x + bitangent * normal_tangent.y + geometric * normal_tangent.z);

	if (front == false && (material.flags & 4u) == 0u)
	{
		normal = -normal;
	}

	float roughness = saturate(rough_ao.x * material.roughness_scale + material.roughness_bias);

	roughness = sqrt(saturate(roughness * roughness + curvature));

	float metal = saturate(height_metal.y * material.metal_scale + material.metal_bias);
	float occlusion = lerp(1.0, rough_ao.y, material.ao_strength);
	uint flags = (object_params.y > 0.5 ? 1u : 0u) | ((material.flags & 16u) ? 2u : 0u) | (object_params.z > 0.5 ? 4u : 0u) | ((material.flags & 32u) ? 8u : 0u);
	float3 emissive = material.emissive;

	if (material.flags & 16u)
	{
		emissive *= 0.35 + 0.65 * luminance(albedo.rgb) * 2.0;

		albedo.rgb = 0.0;
	}

	float2 current_ndc = input.current_clip.xy / input.current_clip.w - jitter.xy;
	float2 previous_ndc = input.previous_clip.xy / input.previous_clip.w - (object_params.y > 0.5 ? jitter.xy : 0.0);

	float3 surface_color = saturate(albedo.rgb * material.tint.rgb);

	[branch] if (skin_params.z > 0.0)
	{
		float grey = luminance(surface_color);
		float3 pale = float3(0.58, 0.63, 0.64) * (0.16 + 0.84 * pow(grey, 0.75));

		surface_color = lerp(surface_color, pale, skin_params.z) * lerp(1.0, float3(0.86, 0.9, 0.9), skin_params.z);
		roughness = lerp(roughness, max(roughness, 0.55), skin_params.z);
	}

	output.albedo = float4(surface_color, 1.0);
	output.normal = float4(normal, roughness);
	output.surface = float4(metal, occlusion, (float)flags / 255.0, material.specular);
	output.emissive = float4(emissive, 0.0);
	output.motion = (previous_ndc - current_ndc) * float2(0.5, -0.5);

	return output;
}
/*
//=====================================================================================
*/
gbuffer_output ps_main(pixel_input input, bool front : SV_IsFrontFace)
{
	return shade(input, front, false);
}
/*
//=====================================================================================
*/
gbuffer_output ps_alpha(pixel_input input, bool front : SV_IsFrontFace)
{
	return shade(input, front, true);
}
/*
//=====================================================================================
*/
gbuffer_output ps_impostor(impostor_input input)
{
	gbuffer_output output;

	material_data material = material_table[input.material];

	float4 albedo = lerp(albedo_array.Sample(anisotropic_wrap, float3(input.uv.xy, material.layer)), albedo_array.Sample(anisotropic_wrap, float3(input.uv.zw, material.layer)), input.blend);

	clip(albedo.a - 0.5);

	lod_dither(input.fade, input.position.xy);

	float2 normal_xy = lerp(normal_array.Sample(anisotropic_wrap, float3(input.uv.xy, material.layer)).rg, normal_array.Sample(anisotropic_wrap, float3(input.uv.zw, material.layer)).rg, input.blend) * 2.0 - 1.0;
	float2 rough_ao = lerp(rough_ao_array.Sample(anisotropic_wrap, float3(input.uv.xy, material.layer)).rg, rough_ao_array.Sample(anisotropic_wrap, float3(input.uv.zw, material.layer)).rg, input.blend);
	float3 normal = normalize(input.right * normal_xy.x - float3(0.0, normal_xy.y, 0.0) + input.facing * sqrt(saturate(1.0 - dot(normal_xy, normal_xy))));
	float2 current_ndc = input.current_clip.xy / input.current_clip.w - jitter.xy;
	float2 previous_ndc = input.previous_clip.xy / input.previous_clip.w;

	output.albedo = float4(saturate(albedo.rgb * material.tint.rgb), 1.0);
	output.normal = float4(normal, saturate(rough_ao.x * material.roughness_scale + material.roughness_bias));
	output.surface = float4(0.0, lerp(1.0, rough_ao.y, material.ao_strength), 8.0 / 255.0, material.specular);
	output.emissive = 0.0;
	output.motion = (previous_ndc - current_ndc) * float2(0.5, -0.5);

	return output;
}

//=====================================================================================
