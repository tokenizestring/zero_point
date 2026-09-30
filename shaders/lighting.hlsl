
//=====================================================================================

#include "common.hlsli"

struct light_data
{
	float3 position;
	float radius;
	float3 color;
	float spot_outer;
	float3 direction;
	float spot_inner;
};

Texture2D<float4> gbuffer_albedo : register(t0);
Texture2D<float4> gbuffer_normal : register(t1);
Texture2D<float4> gbuffer_surface : register(t2);
Texture2D<float4> gbuffer_emissive : register(t3);
Texture2D<float> depth_texture : register(t4);
Texture2DArray<float> shadow_map : register(t5);
TextureCube<float4> sky_prefiltered : register(t6);
Texture2D<float2> brdf_lut : register(t7);
Texture2D<float4> sky_equirect : register(t8);
Texture2D<float> occlusion_texture : register(t9);
Texture2D<float4> reflection_texture : register(t10);
StructuredBuffer<light_data> lights : register(t11);
Texture3D<float4> probe_red : register(t12);
Texture3D<float4> probe_green : register(t13);
Texture3D<float4> probe_blue : register(t14);
Texture3D<float2> probe_state : register(t15);
Texture2D<float4> water_normal_map : register(t16);
Texture2D<float> roof_map : register(t17);
RWTexture2D<float4> output : register(u0);
SamplerState linear_clamp : register(s0);
SamplerComparisonState shadow_sampler : register(s1);
SamplerState linear_wrap : register(s2);
SamplerState point_clamp : register(s3);

static const float2 poisson[16] =
{
	float2(-0.94201624, -0.39906216), float2(0.94558609, -0.76890725), float2(-0.09418410, -0.92938870), float2(0.34495938, 0.29387760),
	float2(-0.91588581, 0.45771432), float2(-0.81544232, -0.87912464), float2(-0.38277543, 0.27676845), float2(0.97484398, 0.75648379),
	float2(0.44323325, -0.97511554), float2(0.53742981, -0.47373420), float2(-0.26496911, -0.41893023), float2(0.79197514, 0.19090188),
	float2(-0.24188840, 0.99706507), float2(-0.81409955, 0.91437590), float2(0.19984126, 0.78641367), float2(0.14383161, -0.14100790)
};

groupshared uint tile_depth_near;
groupshared uint tile_depth_far;
groupshared uint tile_light_count;
groupshared uint tile_lights[128];

//=====================================================================================

float3 reconstruct_position(float2 uv, float depth, bool viewmodel)
{
	float2 ndc = float2(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0);
	float3 result;

	[branch] if (viewmodel)
	{
		float4 view_position = mul(float4(ndc, (depth - viewmodel_params.x) / (1.0 - viewmodel_params.x), 1.0), inverse_viewmodel_projection);

		result = mul(float4(view_position.xyz / view_position.w, 1.0), inverse_view).xyz;
	}

	else
	{
		float4 world_position = mul(float4(ndc, depth, 1.0), inverse_view_projection);

		result = world_position.xyz / world_position.w;
	}

	return result;
}
/*
//=====================================================================================
*/
float3 corner_ray(float2 pixel)
{
	float2 ndc = float2(pixel.x * screen.z * 2.0 - 1.0, 1.0 - pixel.y * screen.w * 2.0);
	float4 near_point = mul(float4(ndc, 1.0, 1.0), inverse_view_projection);

	return normalize(near_point.xyz / near_point.w - camera_position.xyz);
}
/*
//=====================================================================================
*/
float cascade_shadow(uint cascade, float3 world_position, float3 normal, float2 rotation)
{
	float texel = cascade_texel[cascade];
	float3 offset_position = world_position + normal * (texel * 1.6) + sun_direction.xyz * (texel * 0.8);
	float4 shadow_position = mul(float4(offset_position, 1.0), cascade_matrices[cascade]);
	float2 shadow_uv = shadow_position.xy * float2(0.5, -0.5) + 0.5;
	float receiver = shadow_position.z;
	float inverse_resolution = 1.0 / shadow_params.x;
	float radius = 1.25;
	float result = 1.0;

	[branch] if (all(shadow_uv > 0.0) && all(shadow_uv < 1.0) && receiver < 1.0)
	{
		[branch] if (quality_params.x > 3.5)
		{
			float blocker_sum = 0.0;
			float blocker_count = 0.0;

			[unroll] for (int search = 0; search < 16; search++)
			{
				float2 offset = float2(poisson[search].x * rotation.x - poisson[search].y * rotation.y, poisson[search].x * rotation.y + poisson[search].y * rotation.x);
				float stored = shadow_map.SampleLevel(point_clamp, float3(shadow_uv + offset * (6.0 * inverse_resolution), cascade), 0.0);

				if (stored < receiver)
				{
					blocker_sum += stored;
					blocker_count += 1.0;
				}
			}

			if (blocker_count > 0.0)
			{
				radius = clamp((receiver - blocker_sum / blocker_count) * shadow_params.y * 0.0186 / texel, 1.0, 10.0);
			}
		}

		uint taps = quality_params.x > 2.5 ? 16u : (quality_params.x > 1.5 ? 8u : 4u);
		float sum = 0.0;

		[loop] for (uint tap = 0; tap < taps; tap++)
		{
			float2 offset = float2(poisson[tap].x * rotation.x - poisson[tap].y * rotation.y, poisson[tap].x * rotation.y + poisson[tap].y * rotation.x);

			sum += shadow_map.SampleCmpLevelZero(shadow_sampler, float3(shadow_uv + offset * (radius * inverse_resolution), cascade), receiver);
		}

		result = sum / (float)taps;
	}

	return result;
}
/*
//=====================================================================================
*/
float sun_shadow(float3 world_position, float3 normal, float view_depth, float2 pixel)
{
	float result = 1.0;

	[branch] if (quality_params.x > 0.5)
	{
		uint cascade = 0;

		[unroll] for (uint index = 0; index < 3; index++)
		{
			if (view_depth > cascade_splits[index])
			{
				cascade = index + 1;
			}
		}

		[branch] if (view_depth < cascade_splits[3])
		{
			float angle = interleaved_gradient_noise(pixel + exposure_params.w * 5.588238) * TWO_PI;
			float2 rotation = float2(cos(angle), sin(angle));
			float cascade_start = cascade > 0 ? cascade_splits[cascade - 1] : 0.0;
			float blend = saturate((view_depth - lerp(cascade_start, cascade_splits[cascade], 0.88)) / max((cascade_splits[cascade] - cascade_start) * 0.12, 0.001));

			result = cascade_shadow(cascade, world_position, normal, rotation);

			[branch] if (blend > 0.0 && cascade < 3 && view_depth < cascade_splits[cascade + 1] && cascade + 1 < (uint)shadow_params.z)
			{
				result = lerp(result, cascade_shadow(cascade + 1, world_position, normal, rotation), blend);
			}

			[branch] if (cascade + 1 >= (uint)shadow_params.z)
			{
				result = lerp(result, 1.0, blend);
			}
		}
	}

	return result;
}
/*
//=====================================================================================
*/
float3 sky_radiance(float3 direction)
{
	float3 radiance = sky_equirect.SampleLevel(linear_wrap, direction_to_equirect(sky_space(direction)), 0.0).rgb * sky_params.x;
	float cosine = dot(direction, sun_direction.xyz);
	float disc = cos(sun_direction.w);

	[branch] if (cosine > disc - 0.00002)
	{
		float solid_angle = PI * sun_direction.w * sun_direction.w;
		float edge = smoothstep(disc - 0.00002, disc + 0.00002, cosine);
		float limb = 0.6 + 0.4 * sqrt(saturate((cosine - disc) / (1.0 - disc)));

		radiance += sun_color.rgb / solid_angle * edge * limb;
	}

	[branch] if (sky_params.z > 0.001 && direction.y > 0.0)
	{
		float3 scaled = direction * 420.0;
		float3 cell = floor(scaled);
		float seed = frac(sin(dot(cell, float3(12.9898, 78.233, 37.719))) * 43758.5453);

		[branch] if (seed > 0.9962)
		{
			float3 jitter = frac(seed * float3(97.13, 57.31, 23.77)) * 0.6 + 0.2;
			float falloff = saturate(1.0 - length(scaled - cell - jitter) * 2.6);
			float brightness = pow(frac(seed * 131.7), 3.0) * 0.9 + 0.08;
			float3 tint = lerp(float3(0.75, 0.85, 1.0), float3(1.0, 0.9, 0.75), frac(seed * 71.3));

			radiance += tint * brightness * falloff * falloff * sky_params.z * saturate(direction.y * 6.0) * 1.6;
		}
	}

	return radiance;
}
/*
//=====================================================================================
*/
float slope_divergence(float2 uv, float tile)
{
	float texel = 1.0 / 256.0;
	float dx = water_normal_map.SampleLevel(linear_wrap, uv + float2(texel, 0.0), 0.0).r - water_normal_map.SampleLevel(linear_wrap, uv - float2(texel, 0.0), 0.0).r;
	float dz = water_normal_map.SampleLevel(linear_wrap, uv + float2(0.0, texel), 0.0).g - water_normal_map.SampleLevel(linear_wrap, uv - float2(0.0, texel), 0.0).g;

	return (dx + dz) * 2.0 / (2.0 * texel * tile);
}
/*
//=====================================================================================
*/
float water_caustics(float3 position, float depth)
{
	float2 surface = position.xz + sun_direction.xz / max(sun_direction.y, 0.25) * depth;
	float divergence = slope_divergence(surface / 13.0 + time_params.x * float2(0.02, 0.011), 13.0) * 0.7 + slope_divergence(surface / 21.0 - time_params.x * float2(0.012, 0.017), 21.0) * 0.5;
	float focus = clamp(1.0 / max(1.0 + divergence * min(depth, 5.0) * 0.12, 0.3), 0.35, 2.6);

	return lerp(1.0, pow(focus, 1.25), saturate(depth * 1.2) * saturate(1.2 - depth / 14.0));
}
/*
//=====================================================================================
*/
float3 probe_irradiance(float3 position, float3 normal, out float sky_visibility)
{
	float3 grid = (position + normal * 0.3 - probe_origin.xyz) / probe_origin.w;
	int3 limit = int3(probe_counts.xyz) - 2;
	int3 base = clamp(int3(floor(grid)), int3(0, 0, 0), limit);
	float3 fraction = saturate(grid - float3(base));
	float4 red = 0.0;
	float4 green = 0.0;
	float4 blue = 0.0;
	float visibility = 0.0;
	float weights = 0.0;

	[unroll] for (uint corner = 0; corner < 8; corner++)
	{
		int3 offset = int3(corner & 1u, (corner >> 1u) & 1u, (corner >> 2u) & 1u);
		int4 location = int4(base + offset, 0);
		float2 state = probe_state.Load(location);
		float3 probe_position = probe_origin.xyz + float3(base + offset) * probe_origin.w;
		float facing = (dot(normalize(probe_position - position), normal) + 1.0) * 0.5;
		float3 trilinear = lerp(1.0 - fraction, fraction, float3(offset));
		float weight = trilinear.x * trilinear.y * trilinear.z * (facing * facing + 0.05) * state.x;

		red += probe_red.Load(location) * weight;
		green += probe_green.Load(location) * weight;
		blue += probe_blue.Load(location) * weight;
		visibility += state.y * weight;
		weights += weight;
	}

	float3 result = sh_irradiance(normal);

	sky_visibility = 1.0;

	[branch] if (weights > 0.0001)
	{
		red /= weights;
		green /= weights;
		blue /= weights;

		float3 band = float3(normal.y, normal.z, normal.x) * (0.488603 * 2.094395);

		result = overcast(max(float3(red.x, green.x, blue.x) * (0.282095 * PI) + float3(dot(red.yzw, band), dot(green.yzw, band), dot(blue.yzw, band)), 0.0), 1.0);

		sky_visibility = visibility / weights;
	}

	return result;
}
/*
//=====================================================================================
*/
[numthreads(16, 16, 1)]
void cs_main(uint3 id : SV_DispatchThreadID, uint3 group : SV_GroupID, uint thread_index : SV_GroupIndex)
{
	[branch] if (thread_index == 0)
	{
		tile_depth_near = 0;
		tile_depth_far = 0x7F7FFFFF;
		tile_light_count = 0;
	}

	GroupMemoryBarrierWithGroupSync();

	bool inside = id.x < (uint)screen.x && id.y < (uint)screen.y;
	float depth = inside ? depth_texture[id.xy] : 0.0;

	[branch] if (depth > 0.0)
	{
		InterlockedMax(tile_depth_near, asuint(depth));
		InterlockedMin(tile_depth_far, asuint(depth));
	}

	GroupMemoryBarrierWithGroupSync();

	[branch] if (tile_depth_near > 0 && light_params.x > 0.5)
	{
		float view_near = camera_position.w / asfloat(tile_depth_near);
		float view_far = camera_position.w / asfloat(tile_depth_far);
		float2 tile_min = float2(group.xy * 16);
		float2 tile_max = tile_min + 16.0;
		float3 forward = inverse_view[2].xyz;
		float3 ray_a = corner_ray(tile_min);
		float3 ray_b = corner_ray(float2(tile_max.x, tile_min.y));
		float3 ray_c = corner_ray(tile_max);
		float3 ray_d = corner_ray(float2(tile_min.x, tile_max.y));
		float3 center_ray = normalize(ray_a + ray_b + ray_c + ray_d);
		float3 planes[4] = { normalize(cross(ray_a, ray_b)), normalize(cross(ray_b, ray_c)), normalize(cross(ray_c, ray_d)), normalize(cross(ray_d, ray_a)) };

		[unroll] for (uint side = 0; side < 4; side++)
		{
			if (dot(planes[side], center_ray) < 0.0)
			{
				planes[side] = -planes[side];
			}
		}

		[loop] for (uint light_index = thread_index; light_index < (uint)light_params.x; light_index += 256)
		{
			light_data light = lights[light_index];
			float3 relative = light.position - camera_position.xyz;
			float light_depth = dot(relative, forward);
			bool visible = light_depth + light.radius > view_near && light_depth - light.radius < view_far;

			[unroll] for (uint plane = 0; plane < 4; plane++)
			{
				visible = visible && dot(planes[plane], relative) > -light.radius;
			}

			[branch] if (visible)
			{
				uint slot;

				InterlockedAdd(tile_light_count, 1, slot);

				if (slot < 128)
				{
					tile_lights[slot] = light_index;
				}
			}
		}
	}

	GroupMemoryBarrierWithGroupSync();

	[branch] if (inside)
	{
		float2 uv = (float2(id.xy) + 0.5) * screen.zw;
		float3 color;

		[branch] if (depth <= 0.0)
		{
			float3 far_point = reconstruct_position(uv, 0.0001, false);
			float3 direction = normalize(far_point - camera_position.xyz);
			float3 radiance = overcast(sky_radiance(direction), 0.55 + 0.25 * saturate(direction.y * 2.0)) + weather_params.z * float3(1.6, 1.7, 2.0) * saturate(direction.y + 0.3);

			color = apply_fog(radiance, camera_position.xyz + direction * 6000.0);
		}

		else
		{
			float4 albedo = gbuffer_albedo[id.xy];
			float4 normal_roughness = gbuffer_normal[id.xy];
			float4 surface = gbuffer_surface[id.xy];
			float3 emissive = gbuffer_emissive[id.xy].rgb;
			uint flags = (uint)(surface.b * 255.0 + 0.5);
			bool viewmodel = (flags & 1u) != 0u;
			float3 world_position = reconstruct_position(uv, depth, viewmodel);
			float3 n = normalize(normal_roughness.xyz);
			float3 v = normalize(camera_position.xyz - world_position);
			float roughness = max(normal_roughness.w, 0.03);
			float metal = surface.r;
			float specular = surface.a;
			float view_depth = dot(world_position - camera_position.xyz, inverse_view[2].xyz);
			float screen_occlusion = occlusion_texture.SampleLevel(linear_clamp, uv, 0.0);
			float occlusion = surface.g * (viewmodel ? 1.0 : screen_occlusion);
			float n_dot_v = saturate(dot(n, v));

			float sheen = (flags & 8u) ? saturate(n_dot_v * 3.0) * 0.6 : 1.0;

			color = emissive;

			float3 sun_passage = 1.0;
			float3 ambient_passage = 1.0;

			[branch] if (water_params.x > 0.5 && viewmodel == false && world_position.y < water_params.y + 0.2)
			{
				float submerged = max(water_params.y - world_position.y, 0.0);
				float blend = saturate((water_params.y + 0.2 - world_position.y) / 0.45);

				sun_passage = lerp(1.0, exp(-water_extinction.rgb * submerged / max(sun_direction.y, 0.2)) * water_caustics(world_position, submerged), blend);
				ambient_passage = lerp(1.0, exp(-water_extinction.rgb * submerged * 1.3), blend);
			}

			[branch] if ((flags & 2u) == 0u)
			{
				float shadow = sun_shadow(world_position, n, view_depth, float2(id.xy));
				float sky_visibility = 1.0;
				float3 irradiance = probe_counts.w > 0.5 ? probe_irradiance(world_position, n, sky_visibility) : sh_irradiance(n);

				[branch] if (weather_params.x > 0.001 && viewmodel == false)
				{
					float exposed = smoothstep(0.35, 0.8, sky_visibility) * saturate(n.y * 0.6 + 0.4) * (world_position.y < roof_height(roof_map, world_position) - 0.25 ? 0.0 : 1.0);
					float wet = weather_params.x * exposed;

					albedo.rgb *= lerp(1.0, 0.58, wet * (1.0 - metal));
					roughness = lerp(roughness, 0.07, wet * 0.8);
					specular = lerp(specular, 1.0, wet * 0.5);
					color += albedo.rgb * weather_params.z * exposed * 1.6;
				}

				color += evaluate_light(n, v, sun_direction.xyz, albedo.rgb, roughness, metal, specular, sheen, sun_color.rgb * shadow * sun_passage);

				[branch] if (flags & 8u)
				{
					float behind = saturate(dot(-n, sun_direction.xyz));
					float toward = pow(saturate(dot(-v, sun_direction.xyz)), 5.0);

					color += albedo.rgb * float3(0.9, 1.0, 0.55) * sun_color.rgb * shadow * sun_passage * (behind * 0.45 + toward * 1.1) * surface.g * (1.0 - metal) / PI;
				}

				uint count = min(tile_light_count, 128u);

				[loop] for (uint index = 0; index < count; index++)
				{
					light_data light = lights[tile_lights[index]];
					float3 offset = light.position - world_position;
					float distance_squared = dot(offset, offset);

					[branch] if (distance_squared < light.radius * light.radius)
					{
						float distance = sqrt(distance_squared);
						float3 direction = offset / max(distance, 0.0001);
						float ratio = distance / light.radius;
						float window = saturate(1.0 - ratio * ratio * ratio * ratio);
						float attenuation = window * window / max(distance_squared, 0.01);

						if (light.spot_outer > -0.5)
						{
							attenuation *= smoothstep(light.spot_outer, light.spot_inner, dot(-direction, light.direction));
						}

						color += evaluate_light(n, v, direction, albedo.rgb, roughness, metal, specular, sheen, light.color * attenuation);
					}
				}

				float3 f0 = lerp(0.08 * specular.xxx, albedo.rgb, metal);
				float2 environment = brdf_lut.SampleLevel(linear_clamp, float2(n_dot_v, roughness), 0.0);
				float3 reflected = reflect(-v, n);
				float3 prefiltered = overcast(sky_prefiltered.SampleLevel(linear_clamp, sky_space(reflected), roughness * 6.0).rgb * sky_params.x, 0.55 + 0.25 * saturate(reflected.y * 2.0));
				float openness = smoothstep(0.0, 0.6, sky_visibility);
				float3 surroundings = lerp(irradiance / PI, prefiltered, openness);
				float4 screen_reflection = reflection_texture.SampleLevel(linear_clamp, uv, 0.0);
				float specular_occlusion = saturate(pow(max(n_dot_v + occlusion, 0.0001), exp2(-16.0 * roughness - 1.0)) - 1.0 + occlusion);
				float3 ambient_specular = lerp(surroundings, screen_reflection.rgb, screen_reflection.a) * (f0 * environment.x + environment.y) * specular_occlusion * sheen;
				float3 ambient_diffuse = irradiance * albedo.rgb * (1.0 - metal) / PI * occlusion;

				color += (ambient_diffuse + ambient_specular) * ambient_passage;

				uint debug_view = (uint)exposure_params.y;

				[branch] if (debug_view > 0)
				{
					float3 views[11] = { color, albedo.rgb, n * 0.5 + 0.5, roughness.xxx, metal.xxx, occlusion.xxx, ambient_diffuse * 4.0, ambient_specular * 4.0, shadow.xxx, irradiance * 0.25, sky_visibility.xxx };

					color = views[min(debug_view, 10u)];
				}
			}

			[branch] if (viewmodel == false)
			{
				color = apply_fog(color, world_position);
			}
		}

		output[id.xy] = float4(color, 0.0);
	}
}

//=====================================================================================
