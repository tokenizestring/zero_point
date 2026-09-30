
//=====================================================================================

#include "common.hlsli"

cbuffer ssao_constants : register(b8)
{
	float4 ssao_params;
	float4 ssao_screen;
};

Texture2D<float> depth_texture : register(t0);
Texture2D<float4> normal_texture : register(t1);
Texture2D<float> source_texture : register(t2);
RWTexture2D<float> ssao_output : register(u0);

//=====================================================================================

float3 view_position(float2 uv, float depth)
{
	float view_z = camera_position.w / max(depth, 1e-7);
	float2 ndc = float2(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0) - jitter.xy;

	return float3(ndc.x * view_z / projection[0][0], ndc.y * view_z / projection[1][1], view_z);
}
/*
//=====================================================================================
*/
float fast_acos(float value)
{
	float result = -0.156583 * abs(value) + 1.570796;

	result *= sqrt(1.0 - abs(value));

	return value >= 0.0 ? result : PI - result;
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_ssao(uint3 id : SV_DispatchThreadID)
{
	[branch] if (id.x < (uint)ssao_screen.x && id.y < (uint)ssao_screen.y)
	{
		float2 uv = (float2(id.xy) + 0.5) * ssao_screen.zw;
		int2 full_pixel = int2(uv * screen.xy);
		float depth = depth_texture[full_pixel];
		float visibility = 1.0;

		[branch] if (depth > 0.0 && depth < viewmodel_params.x)
		{
			float3 position = view_position(uv, depth);
			float3 normal = normalize(mul(normal_texture[full_pixel].xyz, (float3x3)view));
			float3 view_direction = normalize(-position);
			float radius = ssao_params.x;
			float screen_radius = radius * projection[1][1] / position.z * 0.5 * ssao_screen.y;
			uint slices = (uint)ssao_params.y;
			uint steps = (uint)ssao_params.z;
			float noise = interleaved_gradient_noise(float2(id.xy) + exposure_params.w * 7.0);
			float jitter_step = frac(noise * 1.618 + 0.35);
			float falloff_range = 0.62 * radius;
			float falloff_from = radius * (1.0 - 0.62);
			float falloff_mul = -1.0 / falloff_range;
			float falloff_add = falloff_from / falloff_range + 1.0;
			float total = 0.0;

			[branch] if (screen_radius > 1.0)
			{
				[loop] for (uint slice = 0; slice < slices; slice++)
				{
					float phi = ((float)slice + noise) / (float)slices * PI;
					float3 direction = float3(cos(phi), sin(phi), 0.0);
					float2 omega = float2(direction.x, -direction.y) * (screen_radius / (float)steps) * ssao_screen.zw;
					float3 ortho = direction - dot(direction, view_direction) * view_direction;
					float3 axis = normalize(cross(ortho, view_direction));
					float3 projected = normal - axis * dot(normal, axis);
					float projected_length = length(projected);
					float sign_normal = sign(dot(ortho, projected));
					float cos_normal = saturate(dot(projected, view_direction) / max(projected_length, 0.0001));
					float n = sign_normal * fast_acos(cos_normal);
					float horizon0 = cos(n + PI * 0.5);
					float horizon1 = cos(n - PI * 0.5);
					float low0 = horizon0;
					float low1 = horizon1;

					[loop] for (uint step = 0; step < steps; step++)
					{
						float scale = ((float)step + jitter_step) / (float)steps;
						float2 offset = omega * (float)steps * scale * scale + omega * 0.5;
						float2 uv0 = uv + offset;
						float2 uv1 = uv - offset;
						float depth0 = depth_texture[int2(saturate(uv0) * (screen.xy - 1.0))];
						float depth1 = depth_texture[int2(saturate(uv1) * (screen.xy - 1.0))];
						float3 delta0 = view_position(uv0, depth0) - position;
						float3 delta1 = view_position(uv1, depth1) - position;
						float distance0 = length(delta0);
						float distance1 = length(delta1);
						float weight0 = saturate(distance0 * falloff_mul + falloff_add);
						float weight1 = saturate(distance1 * falloff_mul + falloff_add);
						float cosine0 = lerp(low0, dot(delta0 / max(distance0, 0.0001), view_direction), weight0);
						float cosine1 = lerp(low1, dot(delta1 / max(distance1, 0.0001), view_direction), weight1);

						horizon0 = max(horizon0, cosine0);
						horizon1 = max(horizon1, cosine1);
					}

					float h0 = -fast_acos(horizon1);
					float h1 = fast_acos(horizon0);

					h0 = n + clamp(h0 - n, -PI * 0.5, PI * 0.5);
					h1 = n + clamp(h1 - n, -PI * 0.5, PI * 0.5);

					float arc0 = (cos_normal + 2.0 * h0 * sin(n) - cos(2.0 * h0 - n)) * 0.25;
					float arc1 = (cos_normal + 2.0 * h1 * sin(n) - cos(2.0 * h1 - n)) * 0.25;

					total += projected_length * (arc0 + arc1);
				}

				visibility = saturate(pow(saturate(total / (float)slices), ssao_params.w));
			}
		}

		ssao_output[id.xy] = visibility;
	}
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_blur(uint3 id : SV_DispatchThreadID)
{
	[branch] if (id.x < (uint)ssao_screen.x && id.y < (uint)ssao_screen.y)
	{
		float2 uv = (float2(id.xy) + 0.5) * ssao_screen.zw;
		float center_depth = camera_position.w / max(depth_texture[int2(uv * screen.xy)], 1e-7);
		int2 axis = ssao_params.y > 0.5 ? int2(0, 1) : int2(1, 0);
		int2 limit = int2(ssao_screen.xy) - 1;
		float sum = 0.0;
		float weights = 0.0;

		[unroll] for (int tap = -3; tap <= 3; tap++)
		{
			int2 location = clamp(int2(id.xy) + axis * tap, int2(0, 0), limit);
			float2 tap_uv = (float2(location) + 0.5) * ssao_screen.zw;
			float tap_depth = camera_position.w / max(depth_texture[int2(tap_uv * screen.xy)], 1e-7);
			float weight = exp(-abs(tap_depth - center_depth) / max(center_depth * 0.03, 0.02)) * (1.0 - abs((float)tap) / 4.0);

			sum += source_texture[location] * weight;
			weights += weight;
		}

		ssao_output[id.xy] = sum / max(weights, 0.0001);
	}
}

//=====================================================================================
