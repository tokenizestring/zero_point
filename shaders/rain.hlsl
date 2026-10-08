
//=====================================================================================

#include "common.hlsli"

cbuffer rain_constants : register(b3)
{
	float4 rain_params;
	float4 rain_wind;
	float4 rain_ground;
};

cbuffer bolt_constants : register(b4)
{
	float4 bolt_points[80];
	float4 bolt_params;
};

Texture2D<float> roof_map : register(t0);
Texture2D<float> terrain_heights : register(t21);
SamplerState linear_clamp : register(s0);

static const float splash_cell = 0.9;
static const uint splash_grid = 32u;
static const float splash_reach = 16.0;

struct rain_output
{
	float4 position : SV_Position;
	float2 corner : TEXCOORD0;
	float fade : TEXCOORD1;
	float3 light : TEXCOORD2;
};

struct bolt_output
{
	float4 position : SV_Position;
	float2 corner : TEXCOORD0;
	float intensity : TEXCOORD1;
};

struct splash_output
{
	float4 position : SV_Position;
	float2 corner : TEXCOORD0;
	float age : TEXCOORD1;
	float fade : TEXCOORD2;
	float3 light : TEXCOORD3;
	nointerpolation uint seed : TEXCOORD4;
};

//=====================================================================================

float3 rain_hash(uint n)
{
	n = (n ^ 61u) ^ (n >> 16u);
	n *= 9u;
	n = n ^ (n >> 4u);
	n *= 0x27D4EB2Du;
	n = n ^ (n >> 15u);

	uint a = n * 0x9E3779B9u;
	uint b = a * 0x85EBCA6Bu + 0xC2B2AE35u;
	uint c = b * 0x27D4EB2Fu + 0x165667B1u;

	return float3(a & 0xFFFFFFu, b & 0xFFFFFFu, c & 0xFFFFFFu) / 16777216.0;
}
/*
//=====================================================================================
*/
float3 rain_light()
{
	return max(sh_irradiance(float3(0.0, 1.0, 0.0)), 0.0) / PI * 1.4 + sun_color.rgb * 0.03 + rain_params.z * 3.0;
}
/*
//=====================================================================================
*/
float impact_height(float3 position)
{
	float land = rain_ground.z > 0.5 ? terrain_heights.SampleLevel(linear_clamp, ((position.xz - rain_ground.x) / rain_params.w + 0.5) / rain_ground.y, 0.0) : -100000.0;

	return max(max(land, rain_ground.w), roof_height(roof_map, position));
}
/*
//=====================================================================================
*/
rain_output vs_main(uint vertex : SV_VertexID, uint instance : SV_InstanceID)
{
	static const float2 corners[6] = { float2(-1.0, 0.0), float2(1.0, 0.0), float2(1.0, 1.0), float2(-1.0, 0.0), float2(1.0, 1.0), float2(-1.0, 1.0) };

	rain_output output;

	float2 corner = corners[vertex];
	float3 box = float3(34.0, 22.0, 34.0);
	float3 seed = rain_hash(instance);
	float speed = 8.0 + seed.x * 3.0;
	float3 velocity = float3(rain_wind.x, -speed, rain_wind.z);
	float3 origin = camera_position.xyz - box * 0.5;
	float3 drifting = seed * box + velocity * rain_params.y;
	float3 drop = origin + frac((drifting - origin) / box) * box;
	float3 along = normalize(velocity);
	float distance = length(drop - camera_position.xyz);
	float3 facing = (camera_position.xyz - drop) / max(distance, 0.001);
	float3 sideways = cross(along, facing);
	float3 across = length(sideways) > 0.0001 ? sideways / length(sideways) : float3(1.0, 0.0, 0.0);
	float streak = (0.32 + seed.y * 0.3) * (1.0 + distance * 0.02);
	float width = 0.0045 + distance * 0.0009;
	float3 world = drop - along * (corner.y * streak) + across * (corner.x * width);

	output.position = drop.y < roof_height(roof_map, drop) || drop.y < rain_ground.w ? float4(0.0, 0.0, -1.0, 1.0) : mul(float4(world, 1.0), view_projection);
	output.corner = corner;
	output.fade = saturate(1.0 - distance / 17.0) * saturate((distance - 0.35) / 1.2) * rain_params.x;
	output.light = rain_light();

	return output;
}
/*
//=====================================================================================
*/
splash_output splash_vs(uint vertex : SV_VertexID, uint instance : SV_InstanceID)
{
	static const float2 corners[6] = { float2(-1.0, 0.0), float2(1.0, 0.0), float2(1.0, 1.0), float2(-1.0, 0.0), float2(1.0, 1.0), float2(-1.0, 1.0) };

	splash_output output;

	float2 corner = corners[vertex];
	int2 first = int2(floor(camera_position.xz / splash_cell)) - int(splash_grid / 2u);
	int2 cell = first + int2(instance % splash_grid, instance / splash_grid);
	uint key = (uint)cell.x * 73856093u ^ (uint)cell.y * 19349663u;
	float3 identity = rain_hash(key);
	float cycle = rain_params.y * 3.0 + identity.x;
	float3 spot = rain_hash(key ^ ((uint)floor(cycle) * 83492791u));
	float2 xz = (float2(cell) + spot.xy) * splash_cell;
	float3 ground = float3(xz.x, 0.0, xz.y);

	ground.y = impact_height(ground);

	float distance = length(ground - camera_position.xyz);
	float3 flat_facing = float3(camera_position.x - ground.x, 0.0, camera_position.z - ground.z);
	float3 facing = length(flat_facing) > 0.0001 ? normalize(flat_facing) : float3(0.0, 0.0, 1.0);
	float3 across = float3(facing.z, 0.0, -facing.x);
	float size = 0.11 + spot.z * 0.06;
	float3 world = ground + across * (corner.x * size * 1.5) + float3(0.0, corner.y * size, 0.0);
	bool active = identity.y < rain_params.x && distance < splash_reach && ground.y > -1000.0;

	output.position = active ? mul(float4(world, 1.0), view_projection) : float4(0.0, 0.0, -1.0, 1.0);
	output.corner = corner;
	output.age = frac(cycle);
	output.fade = saturate(1.0 - distance / splash_reach) * saturate(distance - 0.5) * saturate(rain_params.x * 1.5);
	output.light = rain_light();
	output.seed = key ^ ((uint)floor(cycle) * 2654435761u);

	return output;
}
/*
//=====================================================================================
*/
bolt_output bolt_vs(uint vertex : SV_VertexID, uint instance : SV_InstanceID)
{
	static const float2 corners[6] = { float2(0.0, -1.0), float2(1.0, -1.0), float2(1.0, 1.0), float2(0.0, -1.0), float2(1.0, 1.0), float2(0.0, 1.0) };

	bolt_output output;

	float2 corner = corners[vertex];
	float4 start = bolt_points[instance * 2u];
	float4 finish = bolt_points[instance * 2u + 1u];
	float3 center = lerp(start.xyz, finish.xyz, corner.x);
	float3 facing = camera_position.xyz - center;
	float distance = length(facing);
	float3 sideways = cross(finish.xyz - start.xyz, facing);
	float3 across = length(sideways) > 0.0001 ? normalize(sideways) : float3(1.0, 0.0, 0.0);
	float width = max(start.w, distance * 0.0014) * 4.0;

	output.position = instance < (uint)bolt_params.x ? mul(float4(center + across * (corner.y * width), 1.0), view_projection) : float4(0.0, 0.0, -1.0, 1.0);
	output.corner = corner;
	output.intensity = finish.w * bolt_params.y * sqrt(fog_transmittance(center));

	return output;
}
/*
//=====================================================================================
*/
float4 ps_main(rain_output input) : SV_Target
{
	float edge = saturate(1.0 - abs(input.corner.x));
	float taper = 1.0 - input.corner.y * 0.7;
	float alpha = edge * edge * taper * input.fade * 0.42;

	return float4(input.light * alpha, alpha);
}
/*
//=====================================================================================
*/
float4 bolt_ps(bolt_output input) : SV_Target
{
	float across = abs(input.corner.y);
	float core = saturate(1.0 - across * 4.0);
	float halo = exp(-across * 5.0) * 0.06;

	return float4(float3(0.78, 0.84, 1.0) * (core * core + halo) * input.intensity, 1.0);
}
/*
//=====================================================================================
*/
float4 splash_ps(splash_output input) : SV_Target
{
	float age = input.age;
	float2 local = input.corner * float2(1.5, 1.0);
	float crown = 0.0;

	[unroll] for (uint index = 0u; index < 5u; index++)
	{
		float3 random = rain_hash(input.seed + index * 7919u);
		float height = 4.0 * age * (1.0 - age) * (0.3 + 0.65 * random.y);
		float2 droplet = float2((random.x * 2.0 - 1.0) * (0.2 + age * 1.1), height);
		float radius = (0.07 + 0.08 * random.z) * (1.0 - age * 0.4);

		crown += saturate(1.5 - length((local - droplet) * float2(1.0, 0.65)) / radius * 1.5);
	}

	float puff = exp(-(local.x * local.x / (0.08 + age * 0.5) + local.y * local.y / (0.02 + age * 0.05)));
	float alpha = saturate(crown * 0.9 + puff * 0.5) * (1.0 - age * age) * input.fade * 0.8;

	return float4(input.light * 1.3 * alpha, alpha);
}

//=====================================================================================
