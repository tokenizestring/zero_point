
//=====================================================================================

#include "common.hlsli"

cbuffer sky_build_constants : register(b3)
{
	float4 build_params;
	float4 build_face;
};

Texture2D<float4> equirect_source : register(t0);
TextureCube<float4> cube_source : register(t1);
RWTexture2DArray<float4> cube_output : register(u0);
RWTexture2D<float2> lut_output : register(u1);
SamplerState linear_wrap : register(s0);
SamplerState linear_clamp : register(s1);

//=====================================================================================

float3 cube_direction(uint face, float2 uv)
{
	float2 p = uv * 2.0 - 1.0;
	float3 direction = float3(p.x, -p.y, 1.0);

	if (face == 0)
	{
		direction = float3(1.0, -p.y, -p.x);
	}

	else if (face == 1)
	{
		direction = float3(-1.0, -p.y, p.x);
	}

	else if (face == 2)
	{
		direction = float3(p.x, 1.0, p.y);
	}

	else if (face == 3)
	{
		direction = float3(p.x, -1.0, -p.y);
	}

	else if (face == 5)
	{
		direction = float3(-p.x, -p.y, -1.0);
	}

	return normalize(direction);
}
/*
//=====================================================================================
*/
float radical_inverse(uint bits)
{
	bits = (bits << 16u) | (bits >> 16u);
	bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
	bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
	bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
	bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);

	return float(bits) * 2.3283064365386963e-10;
}
/*
//=====================================================================================
*/
float3 importance_sample_ggx(float2 xi, float3 n, float alpha)
{
	float phi = TWO_PI * xi.x;
	float cos_theta = sqrt((1.0 - xi.y) / (1.0 + (alpha * alpha - 1.0) * xi.y));
	float sin_theta = sqrt(1.0 - cos_theta * cos_theta);
	float3 h = float3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);
	float3 up = abs(n.z) < 0.999 ? float3(0.0, 0.0, 1.0) : float3(1.0, 0.0, 0.0);
	float3 tangent = normalize(cross(up, n));
	float3 bitangent = cross(n, tangent);

	return normalize(tangent * h.x + bitangent * h.y + n * h.z);
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_equirect(uint3 id : SV_DispatchThreadID)
{
	uint size = (uint)build_params.x;

	[branch] if (id.x < size && id.y < size)
	{
		float3 sum = 0.0;

		[unroll] for (uint sample = 0; sample < 4; sample++)
		{
			float2 offset = float2((sample & 1u) ? 0.75 : 0.25, (sample & 2u) ? 0.75 : 0.25);
			float3 direction = cube_direction(id.z, (float2(id.xy) + offset) / (float)size);

			sum += equirect_source.SampleLevel(linear_wrap, direction_to_equirect(direction), 0.0).rgb;
		}

		cube_output[id] = float4(min(sum * 0.25, 60000.0), 1.0);
	}
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_prefilter(uint3 id : SV_DispatchThreadID)
{
	uint size = (uint)build_params.x;

	[branch] if (id.x < size && id.y < size)
	{
		float roughness = build_params.y;
		uint samples = (uint)build_params.z;
		float3 n = cube_direction(id.z, (float2(id.xy) + 0.5) / (float)size);
		float3 color = cube_source.SampleLevel(linear_clamp, n, build_params.w).rgb;

		[branch] if (roughness > 0.01)
		{
			float alpha = roughness * roughness;
			float texel_solid_angle = 4.0 * PI / (6.0 * build_face.x * build_face.x);
			float3 total = 0.0;
			float weight = 0.0;

			[loop] for (uint index = 0; index < samples; index++)
			{
				float3 h = importance_sample_ggx(float2((float)index / (float)samples, radical_inverse(index)), n, alpha);
				float3 l = normalize(2.0 * dot(n, h) * h - n);
				float n_dot_l = dot(n, l);

				[branch] if (n_dot_l > 0.0)
				{
					float n_dot_h = saturate(dot(n, h));
					float pdf = distribution_ggx(n_dot_h, alpha) * 0.25 + 0.0001;
					float sample_solid_angle = 1.0 / ((float)samples * pdf);
					float mip = clamp(0.5 * log2(sample_solid_angle / texel_solid_angle) + 1.0, 0.0, build_face.y);

					total += cube_source.SampleLevel(linear_clamp, l, mip).rgb * n_dot_l;
					weight += n_dot_l;
				}
			}

			color = total / max(weight, 0.0001);
		}

		cube_output[id] = float4(color, 1.0);
	}
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_brdf_lut(uint3 id : SV_DispatchThreadID)
{
	uint size = (uint)build_params.x;

	[branch] if (id.x < size && id.y < size)
	{
		float n_dot_v = ((float)id.x + 0.5) / (float)size;
		float roughness = ((float)id.y + 0.5) / (float)size;
		float alpha = roughness * roughness;
		float3 v = float3(sqrt(1.0 - n_dot_v * n_dot_v), 0.0, n_dot_v);
		float3 n = float3(0.0, 0.0, 1.0);
		float scale = 0.0;
		float bias = 0.0;

		[loop] for (uint index = 0; index < 512; index++)
		{
			float3 h = importance_sample_ggx(float2((float)index / 512.0, radical_inverse(index)), n, alpha);
			float3 l = normalize(2.0 * dot(v, h) * h - v);
			float n_dot_l = saturate(l.z);

			[branch] if (n_dot_l > 0.0)
			{
				float n_dot_h = saturate(h.z);
				float v_dot_h = saturate(dot(v, h));
				float visibility = visibility_smith(n_dot_v, n_dot_l, alpha) * 4.0 * n_dot_l * v_dot_h / max(n_dot_h, 0.0001);
				float fresnel = pow(1.0 - v_dot_h, 5.0);

				scale += (1.0 - fresnel) * visibility;
				bias += fresnel * visibility;
			}
		}

		lut_output[id.xy] = float2(scale, bias) / 512.0;
	}
}

//=====================================================================================
