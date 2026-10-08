
//=====================================================================================

#include "common.hlsli"
#include "clouds.hlsli"

Texture2D<float4> scene_color : register(t0);
Texture2D<float> scene_depth : register(t1);
Texture2D<float4> water_normal_map : register(t2);
TextureCube<float4> sky_prefiltered : register(t3);
Texture2D<float> cloud_shadows : register(t4);
Texture2D<float> water_terrain : register(t21);
SamplerState linear_clamp : register(s0);
SamplerState linear_wrap : register(s1);

cbuffer water_constants : register(b3)
{
	float4 water_waves[8];
	float4 water_shape;
	float4 water_shallow;
	float4 water_deep;
	float4 water_absorption;
	float4 water_terrain_params;
};

//=====================================================================================

struct water_vertex
{
	float4 position : SV_Position;
	float3 world_position : POSITION0;
	float2 base_xz : TEXCOORD0;
	float4 current_clip : TEXCOORD1;
	float4 previous_clip : TEXCOORD2;
	float calm : TEXCOORD3;
	float depth : TEXCOORD4;
};

struct water_output
{
	float4 color : SV_Target0;
	float2 motion : SV_Target1;
};

struct fullscreen_input
{
	float4 position : SV_Position;
	float2 uv : TEXCOORD0;
};

//=====================================================================================

float3 gerstner(float2 xz, float time_value, float scale, out float3 normal)
{
	float3 offset = 0.0;
	float3 accumulated = float3(0.0, 1.0, 0.0);

	[unroll] for (uint index = 0; index < 8; index++)
	{
		float2 direction = normalize(water_waves[index].xy);
		float k = TWO_PI / water_waves[index].z;
		float amplitude = water_waves[index].w * scale;
		float omega = sqrt(9.81 * k);
		float q = water_shape.x / (k * water_waves[index].w * 8.0);
		float sine, cosine;

		sincos(k * dot(direction, xz) - omega * time_value, sine, cosine);

		offset += float3(q * amplitude * direction.x * cosine, amplitude * sine, q * amplitude * direction.y * cosine);
		accumulated -= float3(direction.x * k * amplitude * cosine, q * k * amplitude * sine, direction.y * k * amplitude * cosine);
	}

	normal = normalize(accumulated);

	return offset;
}
/*
//=====================================================================================
*/
float seabed_depth(float2 xz)
{
	float depth = 40.0;

	[branch] if (water_terrain_params.w > 0.5)
	{
		depth = max(water_shallow.w - water_terrain.SampleLevel(linear_clamp, (xz - water_terrain_params.x + 0.5) / water_terrain_params.z, 0.0), 0.0);
	}

	return depth;
}
/*
//=====================================================================================
*/
float water_calm(float depth)
{
	return 0.12 + 0.88 * saturate(depth / 9.0);
}
/*
//=====================================================================================
*/
float water_level(float2 xz, float time_value)
{
	float calm = water_calm(seabed_depth(xz));
	float offset = 0.0;

	[unroll] for (uint index = 0; index < 8; index++)
	{
		float2 direction = normalize(water_waves[index].xy);
		float k = TWO_PI / water_waves[index].z;

		offset += water_waves[index].w * calm * sin(k * dot(direction, xz) - sqrt(9.81 * k) * time_value);
	}

	return water_shallow.w + offset;
}
/*
//=====================================================================================
*/
float2 detail_slope(float2 xz, float fade)
{
	float2 a = water_normal_map.Sample(linear_wrap, xz / 13.0 + time_params.x * float2(0.02, 0.011)).rg * 2.0 - 1.0;
	float2 b = water_normal_map.Sample(linear_wrap, xz / 5.1 + time_params.x * float2(-0.016, 0.027)).rg * 2.0 - 1.0;
	float2 c = water_normal_map.Sample(linear_wrap, xz / 1.9 + time_params.x * float2(0.034, -0.021)).rg * 2.0 - 1.0;

	return a * 0.55 + b * 0.45 + c * 0.35 * fade;
}
/*
//=====================================================================================
*/
float3 ambient_light()
{
	return max(sh_irradiance(float3(0.0, 1.0, 0.0)), 0.0) / PI + sun_color.rgb * saturate(sun_direction.y) * 0.3;
}
/*
//=====================================================================================
*/
float4 trace_reflection(float3 origin, float3 direction)
{
	float4 result = 0.0;
	float travel = 0.4;
	float span = 0.6;
	bool searching = true;

	[loop] for (uint step = 0; step < 28 && searching; step++)
	{
		float3 point_world = origin + direction * travel;
		float4 clip = mul(float4(point_world, 1.0), view_projection);

		[branch] if (clip.w <= 0.01)
		{
			searching = false;
		}

		else
		{
			float2 ndc = clip.xy / clip.w;
			float2 sample_uv = float2(ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5);

			[branch] if (any(sample_uv < 0.0) || any(sample_uv > 1.0))
			{
				searching = false;
			}

			else
			{
				float scene = scene_depth.SampleLevel(linear_clamp, sample_uv, 0.0);
				float ray_distance = camera_position.w / max(clip.z / clip.w, 0.0000001);
				float scene_distance = scene > 0.0 ? camera_position.w / scene : 100000.0;

				[branch] if (scene > 0.0 && scene < viewmodel_params.x && ray_distance > scene_distance && ray_distance - scene_distance < 1.2 + ray_distance * 0.06)
				{
					float2 edge = saturate(min(sample_uv, 1.0 - sample_uv) * 9.0);

					result = float4(scene_color.SampleLevel(linear_clamp, sample_uv, 0.0).rgb, edge.x * edge.y * saturate(1.0 - (float)step / 28.0) * saturate(direction.y * 6.0 + 0.4));
					searching = false;
				}
			}
		}

		travel += span;
		span *= 1.22;
	}

	return result;
}
/*
//=====================================================================================
*/
water_vertex vs_main(float2 grid : POSITION)
{
	water_vertex output;

	float2 center = floor(camera_position.xz / water_shape.w) * water_shape.w;
	float2 xz = center + sign(grid) * pow(abs(grid), water_shape.z) * water_shape.y;
	float depth = seabed_depth(xz);
	float calm = water_calm(depth) * saturate(1.6 - length(xz - camera_position.xz) / 1600.0);
	float3 normal;
	float3 offset = gerstner(xz, time_params.x, calm, normal);
	float3 previous_offset = gerstner(xz, time_params.y, calm, normal);
	float3 world_position = float3(xz.x, water_shallow.w, xz.y) + offset;

	output.position = mul(float4(world_position, 1.0), view_projection);
	output.current_clip = output.position;
	output.previous_clip = mul(float4(float3(xz.x, water_shallow.w, xz.y) + previous_offset, 1.0), previous_view_projection);
	output.world_position = world_position;
	output.base_xz = xz;
	output.calm = calm;
	output.depth = depth;

	return output;
}
/*
//=====================================================================================
*/
water_output ps_main(water_vertex input)
{
	water_output output;

	float3 wave_normal;
	float3 offset = gerstner(input.base_xz, time_params.x, input.calm, wave_normal);
	float3 view_vector = camera_position.xyz - input.world_position;
	float surface_distance = length(view_vector);
	float3 v = view_vector / surface_distance;
	float near_detail = saturate(1.0 - surface_distance / 60.0);
	float2 slope = detail_slope(input.base_xz, near_detail) * (0.32 * input.calm + 0.06) * lerp(0.35, 1.0, saturate(1.0 - surface_distance / 400.0));
	float3 normal = normalize(wave_normal + float3(slope.x, 0.0, slope.y));
	float2 uv = input.position.xy * screen.zw;
	float lace = water_normal_map.Sample(linear_wrap, input.base_xz / 2.3 + time_params.x * float2(0.03, 0.045)).b * water_normal_map.Sample(linear_wrap, input.base_xz / 0.9 - time_params.x * float2(0.021, 0.013)).b;
	float3 ambient = ambient_light();
	float3 color;

	[branch] if (camera_position.y >= water_params.z - 0.03)
	{
		float behind_depth = scene_depth.SampleLevel(linear_clamp, uv, 0.0);
		float4 behind_point = mul(float4(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0, max(behind_depth, 0.000001), 1.0), inverse_view_projection);
		float thickness = behind_depth > 0.0 ? max(length(behind_point.xyz / behind_point.w - camera_position.xyz) - surface_distance, 0.0) : 400.0;
		float2 refracted_uv = uv + normal.xz * 0.03 * saturate(thickness / 3.0) * near_detail;
		float refracted_depth = scene_depth.SampleLevel(linear_clamp, refracted_uv, 0.0);
		float2 sample_uv = refracted_depth < behind_depth + 0.00001 || behind_depth <= 0.0 ? refracted_uv : uv;
		float3 behind = scene_color.SampleLevel(linear_clamp, sample_uv, 0.0).rgb;
		float3 transmittance = exp(-water_extinction.rgb * thickness);
		float shallow = saturate(1.0 - input.depth / 6.0);
		float3 body = lerp(water_scatter.rgb, water_shallow.rgb * 0.22, shallow * 0.6) * ambient;
		float3 refracted = behind * transmittance + body * (1.0 - transmittance);
		float3 flat_sun = normalize(float3(sun_direction.x, 0.0, sun_direction.z) + 0.0001);
		float backlit = pow(saturate(dot(-v, flat_sun) * 0.5 + 0.5), 3.0) * saturate(sun_direction.y * 4.0);
		float crest_height = saturate(offset.y / max(input.calm * 0.9, 0.05) * 0.5 + 0.5);
		float3 glow = water_shallow.rgb * sun_color.rgb * backlit * crest_height * crest_height * 0.055 * input.calm;
		float cosine = max(abs(dot(normal, v)), 0.06 + 0.25 * saturate(1.0 - (camera_position.y - water_params.z) / 1.5) * saturate(1.0 - surface_distance / 250.0));
		float far = saturate(surface_distance / 300.0);
		float fresnel = (0.02 + 0.98 * pow(1.0 - cosine, 5.0)) * lerp(1.0, 0.72, far);
		float3 reflected_direction = reflect(-v, normal);
		float3 sky_direction = normalize(float3(reflected_direction.x, max(reflected_direction.y, 0.02) + far * 0.12, reflected_direction.z));
		float3 sky_reflection = overcast(sky_prefiltered.SampleLevel(linear_clamp, sky_space(sky_direction), 0.8 + (1.0 - near_detail) * 1.2).rgb * sky_params.x, 0.55 + 0.25 * saturate(sky_direction.y * 2.0));
		float4 screen_reflection = quality_params.z > 0.5 && surface_distance < 450.0 ? trace_reflection(input.world_position + normal * 0.05, normalize(sky_direction)) : 0.0;
		float3 reflection = lerp(sky_reflection, screen_reflection.rgb, screen_reflection.a);
		float3 half_vector = normalize(v + sun_direction.xyz);
		float n_dot_h = saturate(dot(normal, half_vector));
		float roughness = lerp(0.045, 0.14, 1.0 - near_detail);
		float alpha = roughness * roughness;
		float lobe = alpha / (PI * pow(n_dot_h * n_dot_h * (alpha - 1.0) + 1.0, 2.0));
		float specular = min(lobe * 0.25 * fresnel / max(cosine, 0.1), 60.0) * saturate(sun_direction.y * 8.0);
		float drift = water_normal_map.Sample(linear_wrap, input.base_xz / 97.0).b;
		float cycle = frac(time_params.x / 7.5 + drift * 0.8);
		float front = lerp(2.4, -0.05, cycle);
		float roller = saturate(1.0 - abs(input.depth - front) / (0.22 + 0.35 * cycle)) * (1.0 - cycle * 0.55) * saturate(1.0 - input.depth / 2.6);
		float wake = saturate(1.0 - (input.depth - front) / 1.4) * step(front, input.depth) * (1.0 - cycle) * 0.45 * saturate(1.0 - input.depth / 2.6);
		float film = saturate(1.0 - input.depth / 0.28);
		float crest = saturate((offset.y - 0.95 * input.calm) * 2.0) * input.calm * saturate(1.0 - surface_distance / 140.0);
		float foam = saturate((smoothstep(0.3, 0.55, lace + roller * 0.25) * (roller + wake * 0.4) + smoothstep(0.34, 0.6, lace) * (film * 0.5 + crest)) * water_absorption.w);

		color = lerp(refracted + glow, reflection, saturate(fresnel)) + sun_color.rgb * specular * (1.0 - foam) * cloud_sunlight(cloud_shadows, linear_clamp, input.world_position);
		color = lerp(color, ambient * 0.85, foam);
		output.color = float4(apply_fog(color, input.world_position), 0.0);
	}

	else
	{
		float3 down = -normal;
		float3 transmitted = refract(-v, down, 1.333);
		float cosine = saturate(dot(v, down));
		float3 inside = water_scatter.rgb * ambient * 0.9;

		[branch] if (dot(transmitted, transmitted) > 0.0001)
		{
			float fresnel = 0.02 + 0.98 * pow(1.0 - cosine, 5.0);
			float3 sky = overcast(sky_prefiltered.SampleLevel(linear_clamp, sky_space(transmitted), 0.6).rgb * sky_params.x, 0.55 + 0.25 * saturate(transmitted.y * 2.0));
			float sun_disc = pow(saturate(dot(transmitted, sun_direction.xyz)), 600.0) * 40.0 + pow(saturate(dot(transmitted, sun_direction.xyz)), 12.0) * 0.4;

			color = lerp(sky + sun_color.rgb * sun_disc, inside, fresnel);
		}

		else
		{
			color = inside;
		}

		output.color = float4(color, 0.0);
	}

	output.motion = (input.previous_clip.xy / input.previous_clip.w - (input.current_clip.xy / input.current_clip.w - jitter.xy)) * float2(0.5, -0.5);

	return output;
}
/*
//=====================================================================================
*/
float4 underwater_ps(fullscreen_input input) : SV_Target
{
	float2 ndc = float2(input.uv.x * 2.0 - 1.0, 1.0 - input.uv.y * 2.0);
	float4 near_point = mul(float4(ndc, 1.0, 1.0), inverse_view_projection);
	float3 start = camera_position.xyz + normalize(near_point.xyz / near_point.w - camera_position.xyz) * 0.3;
	float surface = water_level(start.xz, time_params.x);
	float2 wobble = float2(sin(input.uv.y * 23.0 + time_params.x * 1.7), cos(input.uv.x * 19.0 + time_params.x * 1.3)) * 0.0016;
	float3 color = scene_color.SampleLevel(linear_clamp, input.uv, 0.0).rgb;

	[branch] if (start.y < surface)
	{
		float3 direction = normalize(start - camera_position.xyz);
		float2 wobbled = input.uv + wobble;
		float depth = scene_depth.SampleLevel(linear_clamp, wobbled, 0.0);
		float scene_distance = 100000.0;

		[branch] if (depth >= viewmodel_params.x)
		{
			scene_distance = 0.35;
		}

		else if (depth > 0.0)
		{
			float4 scene_point = mul(float4(wobbled.x * 2.0 - 1.0, 1.0 - wobbled.y * 2.0, depth, 1.0), inverse_view_projection);

			scene_distance = length(scene_point.xyz / scene_point.w - camera_position.xyz);
		}

		float submerged = max(surface - camera_position.y, 0.0);
		float surface_distance = direction.y > 0.0005 ? submerged / direction.y : 100000.0;
		float travel = min(scene_distance, surface_distance);
		float3 transmittance = exp(-water_extinction.rgb * 1.6 * travel);
		float3 light = ambient_light() * exp(-water_extinction.rgb * submerged * 0.8);
		float upward = saturate(direction.y * 0.6 + 0.5);
		float3 sun_way = normalize(float3(sun_direction.x * 0.75, sun_direction.y, sun_direction.z * 0.75));
		float shafts = pow(saturate(dot(direction, sun_way)), 6.0) * saturate(sun_direction.y * 3.0) * 0.6;
		float3 fog = water_scatter.rgb * light * (lerp(0.3, 1.25, upward) + shafts) * 1.6;
		float line_band = saturate(1.0 - (surface - start.y) / 0.02);

		color = scene_color.SampleLevel(linear_clamp, wobbled, 0.0).rgb;
		color = color * transmittance + fog * (1.0 - transmittance);
		color *= 1.0 - line_band * 0.35;
	}

	return float4(color, 0.0);
}

//=====================================================================================
