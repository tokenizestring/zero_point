
//=====================================================================================

#include "common.hlsli"
#include "clouds.hlsli"

Texture3D<float4> shape_texture : register(t1);
Texture3D<float4> detail_texture : register(t2);
Texture2D<float4> weather_texture : register(t3);
Texture2D<float4> march_input : register(t4);
Texture2D<float4> history_input : register(t5);
RWTexture3D<unorm float4> volume_output : register(u0);
RWTexture2D<unorm float4> weather_output : register(u1);
RWTexture2D<float4> cloud_output : register(u2);
RWTexture2D<float> shadow_output : register(u3);
SamplerState linear_wrap : register(s0);
SamplerState linear_clamp : register(s1);

static const float light_strides[5] = { 45.0, 90.0, 180.0, 360.0, 720.0 };

//=====================================================================================

float3 cloud_hash(float3 cell)
{
	uint3 v = uint3(cell);

	v = v * 1664525u + 1013904223u;
	v.x += v.y * v.z;
	v.y += v.z * v.x;
	v.z += v.x * v.y;
	v ^= v >> 16u;
	v.x += v.y * v.z;
	v.y += v.z * v.x;
	v.z += v.x * v.y;

	return float3(v & 0x00FFFFFFu) / 16777216.0;
}
/*
//=====================================================================================
*/
float worley(float3 p, float period, float seed)
{
	float3 cell = floor(p);
	float3 local = p - cell;
	float nearest = 1.0;

	[loop] for (int z = -1; z <= 1; z++)
	{
		[loop] for (int y = -1; y <= 1; y++)
		{
			[loop] for (int x = -1; x <= 1; x++)
			{
				float3 offset = float3(x, y, z);
				float3 feature = offset + cloud_hash(fmod(cell + offset + period, period) + seed) - local;

				nearest = min(nearest, dot(feature, feature));
			}
		}
	}

	return 1.0 - saturate(sqrt(nearest));
}
/*
//=====================================================================================
*/
float lattice(float3 cell, float3 corner, float3 local, float period, float seed)
{
	return dot(cloud_hash(fmod(cell + corner, period) + seed) * 2.0 - 1.0, local - corner);
}
/*
//=====================================================================================
*/
float perlin(float3 p, float period, float seed)
{
	float3 cell = floor(p);
	float3 local = p - cell;
	float3 fade = local * local * local * (local * (local * 6.0 - 15.0) + 10.0);
	float near_low = lerp(lattice(cell, float3(0.0, 0.0, 0.0), local, period, seed), lattice(cell, float3(1.0, 0.0, 0.0), local, period, seed), fade.x);
	float near_high = lerp(lattice(cell, float3(0.0, 1.0, 0.0), local, period, seed), lattice(cell, float3(1.0, 1.0, 0.0), local, period, seed), fade.x);
	float far_low = lerp(lattice(cell, float3(0.0, 0.0, 1.0), local, period, seed), lattice(cell, float3(1.0, 0.0, 1.0), local, period, seed), fade.x);
	float far_high = lerp(lattice(cell, float3(0.0, 1.0, 1.0), local, period, seed), lattice(cell, float3(1.0, 1.0, 1.0), local, period, seed), fade.x);

	return lerp(lerp(near_low, near_high, fade.y), lerp(far_low, far_high, fade.y), fade.z);
}
/*
//=====================================================================================
*/
float perlin_fbm(float3 p, float period, uint octaves, float seed)
{
	float sum = 0.0;
	float amplitude = 1.0;
	float total = 0.0;

	[loop] for (uint octave = 0; octave < octaves; octave++)
	{
		sum += perlin(p, period, seed + octave * 17.0) * amplitude;
		total += amplitude;
		p *= 2.0;
		period *= 2.0;
		amplitude *= 0.5;
	}

	return saturate(sum / total * 0.85 + 0.5);
}
/*
//=====================================================================================
*/
[numthreads(4, 4, 4)]
void cs_shape(uint3 id : SV_DispatchThreadID)
{
	float3 p = (float3(id) + 0.5) / cloud_target.x;
	float billow = perlin_fbm(p * 4.0, 4.0, 5, 3.0);
	float w4 = worley(p * 4.0, 4.0, 11.0);
	float w8 = worley(p * 8.0, 8.0, 23.0);
	float w16 = worley(p * 16.0, 16.0, 37.0);
	float w32 = worley(p * 32.0, 32.0, 53.0);
	float w64 = worley(p * 64.0, 64.0, 71.0);
	float cells = w4 * 0.625 + w8 * 0.25 + w16 * 0.125;

	volume_output[id] = float4(saturate(cloud_remap(billow, 0.0, 1.0, cells, 1.0)), cells, w8 * 0.625 + w16 * 0.25 + w32 * 0.125, w16 * 0.625 + w32 * 0.25 + w64 * 0.125);
}
/*
//=====================================================================================
*/
[numthreads(4, 4, 4)]
void cs_detail(uint3 id : SV_DispatchThreadID)
{
	float3 p = (float3(id) + 0.5) / cloud_target.x;
	float w2 = worley(p * 2.0, 2.0, 5.0);
	float w4 = worley(p * 4.0, 4.0, 13.0);
	float w8 = worley(p * 8.0, 8.0, 29.0);
	float w16 = worley(p * 16.0, 16.0, 41.0);
	float w32 = worley(p * 32.0, 32.0, 59.0);

	volume_output[id] = float4(w2 * 0.625 + w4 * 0.25 + w8 * 0.125, w4 * 0.625 + w8 * 0.25 + w16 * 0.125, w8 * 0.625 + w16 * 0.25 + w32 * 0.125, 1.0);
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_weather(uint3 id : SV_DispatchThreadID)
{
	float2 p = (float2(id.xy) + 0.5) / cloud_target.x;
	float cover = perlin_fbm(float3(p * 6.0, 0.37), 6.0, 5, 7.0);
	float clumps = worley(float3(p * 12.0, 0.5), 12.0, 19.0);
	float kind = perlin_fbm(float3(p * 3.0, 0.71), 3.0, 3, 43.0);

	weather_output[id.xy] = float4(saturate(cover * 0.8 + clumps * 0.32 - 0.12), saturate((kind - 0.32) * 2.2), 0.0, 1.0);
}
/*
//=====================================================================================
*/
float cloud_density(float3 position, float altitude, bool detailed)
{
	float fraction = (altitude - cloud_layer.x) / (cloud_layer.y - cloud_layer.x);
	float result = 0.0;

	[branch] if (fraction > 0.0 && fraction < 1.0)
	{
		float4 weather = weather_texture.SampleLevel(linear_wrap, (position.xz - cloud_wind.xy) / cloud_weather_extent, 0.0);
		float coverage = cloud_cover(weather);
		float profile = smoothstep(0.0, lerp(0.12, 0.07, weather.g), fraction) * (1.0 - smoothstep(lerp(0.16, 0.5, weather.g), lerp(0.38, 1.0, weather.g), fraction));

		[branch] if (coverage * profile > 0.0)
		{
			float4 low = shape_texture.SampleLevel(linear_wrap, float3(position.x - cloud_wind.x, altitude + cloud_wind.z, position.z - cloud_wind.y) / cloud_shape_extent, 0.0);
			float cells = low.g * 0.625 + low.b * 0.25 + low.a * 0.125;
			float base = saturate(cloud_remap(low.r, cells - 1.0, 1.0, 0.0, 1.0)) * profile;

			result = saturate(cloud_remap(base, 1.0 - coverage, 1.0, 0.0, 1.0)) * coverage;

			[branch] if (detailed && result > 0.0)
			{
				float3 high = detail_texture.SampleLevel(linear_wrap, float3(position.x - cloud_wind.x * 1.15, altitude + cloud_wind.w, position.z - cloud_wind.y * 1.15) / cloud_detail_extent, 0.0).rgb;
				float fine = high.r * 0.625 + high.g * 0.25 + high.b * 0.125;
				float erosion = lerp(fine, 1.0 - fine, saturate(fraction * 5.0));

				result = saturate(cloud_remap(result, erosion * 0.32, 1.0, 0.0, 1.0));
			}
		}
	}

	return result;
}
/*
//=====================================================================================
*/
float cloud_shadowing(float3 position, float altitude)
{
	float depth = 0.0;
	float travel = 0.0;

	[unroll] for (uint index = 0; index < 5; index++)
	{
		float reach = travel + light_strides[index] * 0.5;

		depth += cloud_density(position + sun_direction.xyz * reach, altitude + sun_direction.y * reach, index < 2) * light_strides[index];
		travel += light_strides[index];
	}

	return depth * cloud_layer.w;
}
/*
//=====================================================================================
*/
float henyey(float cosine, float g)
{
	float g2 = g * g;

	return (1.0 - g2) / (4.0 * PI * pow(max(1.0 + g2 - 2.0 * g * cosine, 0.0001), 1.5));
}
/*
//=====================================================================================
*/
float cloud_scatter(float optical, float cosine)
{
	float result = 0.0;
	float energy = 1.0;
	float thinning = 1.0;
	float focus = 1.0;

	[unroll] for (uint octave = 0; octave < 3; octave++)
	{
		result += energy * exp(-optical * thinning) * lerp(henyey(cosine, -0.2 * focus), henyey(cosine, 0.75 * focus), 0.7);
		energy *= 0.55;
		thinning *= 0.35;
		focus *= 0.5;
	}

	return result;
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_march(uint3 id : SV_DispatchThreadID)
{
	[branch] if (id.x < (uint)cloud_target.x && id.y < (uint)cloud_target.y)
	{
		float3 direction = cloud_ray((float2(id.xy) + 0.5) * cloud_target.zw);
		float2 span = cloud_interval(camera_position.y, direction.y);
		float3 scattered = 0.0;
		float transmittance = 1.0;

		[branch] if (span.y > span.x)
		{
			float steps = clamp((span.y - span.x) / 90.0, 12.0, cloud_state.w);
			float stride = (span.y - span.x) / steps;
			float jitter = interleaved_gradient_noise(float2(id.xy) + cloud_state.z * 5.588238);
			float cosine = dot(direction, sun_direction.xyz);
			float3 sunlight = sun_color.rgb * cloud_shade.y;
			float3 above = max(sh_irradiance(float3(0.0, 1.0, 0.0)), 0.0) / PI * cloud_shade.z;
			float3 below = max(sh_irradiance(float3(0.0, -1.0, 0.0)), 0.0) / PI * cloud_shade.z;
			float weighted = 0.0;
			float weights = 0.0;

			[loop] for (float index = 0.0; index < steps; index += 1.0)
			{
				float travel = span.x + stride * (index + jitter);
				float3 position = camera_position.xyz + direction * travel;
				float altitude = cloud_altitude(camera_position.y, direction, travel);
				float density = cloud_density(position, altitude, true);

				[branch] if (density > 0.0005)
				{
					float fraction = saturate((altitude - cloud_layer.x) / (cloud_layer.y - cloud_layer.x));
					float passage = exp(-density * cloud_layer.w * stride);
					float absorbed = transmittance * (1.0 - passage);
					float3 light = sunlight * cloud_scatter(cloud_shadowing(position, altitude), cosine) + lerp(below, above, fraction);

					scattered += light * absorbed;
					weighted += travel * absorbed;
					weights += absorbed;
					transmittance *= passage;

					[branch] if (transmittance < 0.015)
					{
						break;
					}
				}
			}

			float fade = exp(-max((weights > 0.0 ? weighted / weights : span.x) - cloud_haze_start, 0.0) / cloud_haze);

			scattered *= fade;
			transmittance = lerp(1.0, transmittance, fade);
		}

		cloud_output[id.xy] = float4(scattered, transmittance);
	}
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_shadow(uint3 id : SV_DispatchThreadID)
{
	float2 ground = cloud_area.xy + (float2(id.xy) + 0.5) * cloud_area.w;
	float rise = max(sun_direction.y, 0.08);
	float3 slope = float3(sun_direction.x / rise, 1.0, sun_direction.z / rise);
	float depth = 0.0;

	[loop] for (uint index = 0; index < 12; index++)
	{
		float altitude = lerp(cloud_layer.x, cloud_layer.y, (index + 0.5) / 12.0);

		depth += cloud_density(float3(ground.x, 0.0, ground.y) + slope * altitude, altitude, false);
	}

	shadow_output[id.xy] = exp(-depth * (cloud_layer.y - cloud_layer.x) / (rise * 12.0) * cloud_layer.w);
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_resolve(uint3 id : SV_DispatchThreadID)
{
	int2 size = int2(cloud_target.xy);

	[branch] if ((int)id.x < size.x && (int)id.y < size.y)
	{
		float4 current = march_input[id.xy];
		float4 low = current;
		float4 high = current;

		[unroll] for (int y = -1; y <= 1; y++)
		{
			[unroll] for (int x = -1; x <= 1; x++)
			{
				float4 neighbour = march_input[clamp(int2(id.xy) + int2(x, y), int2(0, 0), size - 1)];

				low = min(low, neighbour);
				high = max(high, neighbour);
			}
		}

		float4 clip = mul(float4(cloud_ray((float2(id.xy) + 0.5) * cloud_target.zw), 0.0), previous_view_projection);
		float2 previous = float2(clip.x, -clip.y) / max(clip.w, 0.0001) * 0.5 + 0.5;
		bool valid = cloud_state.y > 0.5 && clip.w > 0.0 && all(previous > 0.0) && all(previous < 1.0);
		float4 history = valid ? clamp(history_input.SampleLevel(linear_clamp, previous, 0.0), low, high) : current;

		cloud_output[id.xy] = lerp(current, history, valid ? 0.9 : 0.0);
	}
}

//=====================================================================================
