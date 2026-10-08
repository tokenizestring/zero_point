
//=====================================================================================

#ifndef COMMON_HLSLI
#define COMMON_HLSLI

static const float PI = 3.14159265;
static const float TWO_PI = 6.28318531;

cbuffer frame_constants : register(b0)
{
	float4x4 view;
	float4x4 projection;
	float4x4 view_projection;
	float4x4 inverse_view_projection;
	float4x4 previous_view_projection;
	float4x4 unjittered_view_projection;
	float4x4 inverse_view;
	float4x4 inverse_projection;
	float4x4 viewmodel_projection;
	float4x4 inverse_viewmodel_projection;
	float4 camera_position;
	float4 screen;
	float4 jitter;
	float4 sun_direction;
	float4 sun_color;
	float4 sky_params;
	float4 exposure_params;
	float4 fog_params;
	float4 quality_params;
	float4 viewmodel_params;
	float4 sky_sh[9];
	float4 probe_origin;
	float4 probe_counts;
	float4 light_params;
	float4 time_params;
	float4 water_params;
	float4 water_extinction;
	float4 water_scatter;
	float4 weather_params;
	float4 wind_params;
	float4 wind_scroll;
};

static const float roof_cell = 0.75;
static const int roof_grid = 64;

float roof_height(Texture2D<float> roof_map, float3 position)
{
	int2 cell = int2(floor(position.xz / roof_cell));

	return roof_map.Load(int3(cell & (roof_grid - 1), 0));
}

float3 foliage_rotate(float3 direction, float yaw)
{
	float sine, cosine;

	sincos(yaw, sine, cosine);

	return float3(direction.x * cosine + direction.z * sine, direction.y, -direction.x * sine + direction.z * cosine);
}

float foliage_turn(float3 position, float4 params)
{
	return params.z < -0.5 ? params.y * position.z * params.x : 0.0;
}

float wind_gust(float2 spot, float2 scroll)
{
	float2 phase = (spot - scroll) * TWO_PI;
	float first = sin(phase.x / 96.0 + 1.7 * sin(phase.y / 160.0));
	float second = sin(phase.y / 64.0 + 1.3 * sin(phase.x / 120.0));

	return saturate(0.5 + 0.3 * (first + second) + 0.25 * first * second);
}

float3 tree_bend(float3 local, float gust, float4 params, float time_value)
{
	float strength = wind_params.z;
	float height = max(local.y, 0.0);
	float lean = strength * (0.35 + 0.65 * gust) + sin(time_value * (1.1 + saturate(params.z * 20.0) * 1.5) + params.y) * strength * (0.15 + 0.3 * gust);

	return float3(wind_params.x, 0.0, wind_params.y) * min(height * height * params.z * 3.5 * lean, height * 0.35);
}

float3 tree_flutter(float3 local, float gust, float4 params, float time_value)
{
	float strength = wind_params.z;
	float height = max(local.y, 0.0);
	float reach = length(local.xz);
	float leafy = saturate(params.z * 2500.0);
	float limb = reach * saturate(height * 0.5) * (0.3 + 0.7 * strength) * (0.5 + gust) * leafy;
	float wave = params.y + local.x * 0.31 + local.z * 0.23 + local.y * 0.17;
	float flutter = saturate(reach * 0.5) * saturate(height * 0.3) * (0.5 + strength) * (0.6 + 0.8 * gust) * 0.018 * leafy;
	float3 shimmer = float3(sin(time_value * 11.3 + local.x * 3.1 + local.z * 1.7), sin(time_value * 13.9 + local.y * 2.9 + local.x * 2.3), sin(time_value * 9.7 + local.z * 3.7 + local.y * 1.9));

	return float3(wind_params.x, 0.0, wind_params.y) * (sin(time_value * 1.6 + wave * 1.3) * limb * 0.02) + float3(0.0, sin(time_value * 2.2 + wave) * limb * 0.035, 0.0) + shimmer * flutter;
}

float3 foliage_transform(float3 position, float4 placement, float4 params, float time_value, float2 scroll)
{
	float3 local = position * params.x;
	float3 result;

	[branch] if (params.z < -0.5)
	{
		float sine, cosine;

		sincos(params.y * local.z, sine, cosine);

		float3 along = abs(params.y) > 0.00001 ? float3((1.0 - cosine) / params.y, 0.0, sine / params.y) : float3(0.0, 0.0, local.z);

		result = foliage_rotate(along + float3(local.x * cosine, local.y + (-2.0 - params.z) * local.z, -local.x * sine), placement.w) + placement.xyz;
	}

	else
	{
		float gust = wind_gust(placement.xz, scroll);
		float3 turned = foliage_rotate(local, placement.w);
		float3 bent = turned + tree_bend(local, gust, params, time_value);

		result = bent * (length(turned) / max(length(bent), 0.0001)) + tree_flutter(local, gust, params, time_value) + placement.xyz;
	}

	return result;
}

cbuffer object_constants : register(b1)
{
	float4x4 world;
	float4x4 previous_world;
	float4 object_params;
	float4 skin_params;
	float4 motion_params;
};

float3 creature_motion(float3 position, inout float3 normal)
{
	[branch] if (motion_params.x > 1.5)
	{
		float along = saturate((motion_params.w * 0.5 - position.z) / motion_params.w);
		float wave = motion_params.y - along * 5.0;
		float sway = motion_params.z * along * along;

		position.x += sin(wave) * sway;
		normal = normalize(float3(normal.x - cos(wave) * sway * 5.0 / motion_params.w * normal.z, normal.y, normal.z));
	}

	else if (motion_params.x > 0.5)
	{
		float reach = max(abs(position.x) - motion_params.w, 0.0);

		[branch] if (reach > 0.0)
		{
			float side = position.x < 0.0 ? -1.0 : 1.0;
			float angle = motion_params.z * sin(motion_params.y - reach * 2.0) * smoothstep(0.0, 0.05, reach);
			float sine, cosine;

			sincos(angle, sine, cosine);

			float across = side * normal.x;

			position = float3(side * (motion_params.w + reach * cosine - position.y * sine), reach * sine + position.y * cosine, position.z);
			normal = float3(side * (across * cosine - normal.y * sine), across * sine + normal.y * cosine, normal.z);
		}
	}

	return position;
}

StructuredBuffer<float4> bone_rows : register(t20);

struct skinned_input
{
	float3 position : POSITION;
	float3 normal : NORMAL;
	float4 tangent : TANGENT;
	float2 uv : TEXCOORD0;
	uint material : MATERIAL;
	uint4 joints : BLENDINDICES;
	float4 weights : BLENDWEIGHT;
};

float3x4 skin_rows(uint4 joints, float4 weights, uint offset)
{
	float3x4 rows = 0;

	[unroll] for (uint slot = 0; slot < 4; slot++)
	{
		uint base = (offset + joints[slot]) * 4;

		rows[0] += bone_rows[base + 0] * weights[slot];
		rows[1] += bone_rows[base + 1] * weights[slot];
		rows[2] += bone_rows[base + 2] * weights[slot];
	}

	return rows;
}

float3 skin_translation(uint4 joints, float4 weights, uint offset)
{
	float3 translation = 0;

	[unroll] for (uint slot = 0; slot < 4; slot++)
	{
		translation += bone_rows[(offset + joints[slot]) * 4 + 3].xyz * weights[slot];
	}

	return translation;
}

float3 skin_point(float3 position, float3x4 rows, float3 translation)
{
	return position.x * rows[0].xyz + position.y * rows[1].xyz + position.z * rows[2].xyz + translation;
}

float3 skin_vector(float3 direction, float3x4 rows)
{
	return direction.x * rows[0].xyz + direction.y * rows[1].xyz + direction.z * rows[2].xyz;
}

cbuffer shadow_constants : register(b2)
{
	float4x4 cascade_matrices[4];
	float4 cascade_splits;
	float4 cascade_texel;
	float4 shadow_params;
};

struct material_data
{
	float4 tint;
	uint layer;
	float uv_scale;
	float normal_strength;
	float height_scale;
	float roughness_scale;
	float roughness_bias;
	float metal_scale;
	float metal_bias;
	float3 emissive;
	float aspect;
	uint flags;
	float ao_strength;
	float specular;
	float reserved;
};

//=====================================================================================

float3 rotate_y(float3 v, float angle)
{
	float s = sin(angle);
	float c = cos(angle);

	return float3(v.x * c + v.z * s, v.y, -v.x * s + v.z * c);
}
/*
//=====================================================================================
*/
float2 direction_to_equirect(float3 d)
{
	return float2(atan2(d.x, d.z) / TWO_PI + 0.5, acos(clamp(d.y, -1.0, 1.0)) / PI);
}
/*
//=====================================================================================
*/
float3 sky_space(float3 world_direction)
{
	return rotate_y(world_direction, -sky_params.y);
}
/*
//=====================================================================================
*/
float luminance(float3 c)
{
	return dot(c, float3(0.2126, 0.7152, 0.0722));
}
/*
//=====================================================================================
*/
float3 overcast(float3 radiance, float shade)
{
	return lerp(radiance, luminance(radiance) * shade * float3(0.92, 0.95, 1.0), weather_params.w * 0.85);
}
/*
//=====================================================================================
*/
float3 sh_irradiance(float3 world_normal)
{
	float3 n = sky_space(world_normal);

	float3 result = sky_sh[0].rgb * (0.282095 * PI);

	result += (sky_sh[1].rgb * n.y + sky_sh[2].rgb * n.z + sky_sh[3].rgb * n.x) * (0.488603 * 2.094395);
	result += (sky_sh[4].rgb * (1.092548 * n.x * n.y) + sky_sh[5].rgb * (1.092548 * n.y * n.z) + sky_sh[6].rgb * (0.315392 * (3.0 * n.z * n.z - 1.0)) + sky_sh[7].rgb * (1.092548 * n.x * n.z) + sky_sh[8].rgb * (0.546274 * (n.x * n.x - n.y * n.y))) * 0.785398;

	return overcast(max(result, 0.0) * sky_params.x, 1.0);
}
/*
//=====================================================================================
*/
float fog_transmittance(float3 target)
{
	float result = 1.0;

	[branch] if (fog_params.x > 0.0)
	{
		float3 ray = target - camera_position.xyz;
		float distance = length(ray);
		float3 direction = ray / max(distance, 0.0001);
		float exponent = fog_params.y * direction.y * distance;
		float factor = abs(exponent) > 0.0001 ? (1.0 - exp(-exponent)) / exponent : 1.0;
		float optical = fog_params.x * exp(-fog_params.y * (camera_position.y - fog_params.z)) * distance * factor;

		result = exp(-max(optical, 0.0));
	}

	return result;
}
/*
//=====================================================================================
*/
float3 apply_fog(float3 color, float3 target)
{
	float3 result = color;

	[branch] if (fog_params.x > 0.0)
	{
		float3 direction = normalize(target - camera_position.xyz);
		float cosine = dot(direction, sun_direction.xyz);
		float phase = (1.0 - 0.49) / (4.0 * PI * pow(max(1.49 - 1.4 * cosine, 0.0001), 1.5));
		float3 inscatter = max(sh_irradiance(float3(0.0, 1.0, 0.0)), 0.0) / PI + sun_color.rgb * phase * fog_params.w;

		result = lerp(inscatter, color, fog_transmittance(target));
	}

	return result;
}
/*
//=====================================================================================
*/
float interleaved_gradient_noise(float2 pixel)
{
	return frac(52.9829189 * frac(dot(pixel, float2(0.06711056, 0.00583715))));
}
/*
//=====================================================================================
*/
float3 fresnel_schlick(float3 f0, float cosine)
{
	return f0 + (1.0 - f0) * pow(1.0 - saturate(cosine), 5.0);
}
/*
//=====================================================================================
*/
float distribution_ggx(float n_dot_h, float alpha)
{
	float a2 = alpha * alpha;
	float d = n_dot_h * n_dot_h * (a2 - 1.0) + 1.0;

	return a2 / (PI * d * d + 1e-7);
}
/*
//=====================================================================================
*/
float visibility_smith(float n_dot_v, float n_dot_l, float alpha)
{
	float a2 = alpha * alpha;
	float view_term = n_dot_l * sqrt(n_dot_v * n_dot_v * (1.0 - a2) + a2);
	float light_term = n_dot_v * sqrt(n_dot_l * n_dot_l * (1.0 - a2) + a2);

	return 0.5 / (view_term + light_term + 1e-6);
}
/*
//=====================================================================================
*/
float3 evaluate_light(float3 n, float3 v, float3 l, float3 albedo, float roughness, float metal, float specular, float gloss, float3 radiance)
{
	float n_dot_l = saturate(dot(n, l));
	float3 result = 0.0;

	[branch] if (n_dot_l > 0.0)
	{
		float3 h = normalize(v + l);
		float n_dot_v = max(dot(n, v), 1e-4);
		float n_dot_h = saturate(dot(n, h));
		float v_dot_h = saturate(dot(v, h));
		float alpha = max(roughness * roughness, 0.002);
		float3 f0 = lerp(0.08 * specular.xxx, albedo, metal);
		float3 fresnel = fresnel_schlick(f0, v_dot_h);
		float3 specular_term = distribution_ggx(n_dot_h, alpha) * visibility_smith(n_dot_v, n_dot_l, alpha) * fresnel;
		float3 diffuse_term = albedo * (1.0 - metal) * (1.0 - fresnel) / PI;

		result = (diffuse_term + specular_term * gloss) * radiance * n_dot_l;
	}

	return result;
}

#endif

//=====================================================================================
