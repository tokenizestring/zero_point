
//=====================================================================================

#include "common.hlsli"

cbuffer atmosphere_constants : register(b3)
{
	float4 atmosphere_sun;
	float4 atmosphere_moon;
	float4 atmosphere_size;
	float4 atmosphere_clouds;
	float4 atmosphere_zenith;
};

Texture2D<float4> sky_input : register(t0);
RWTexture2D<float4> sky_output : register(u0);
RWStructuredBuffer<float4> sh_output : register(u1);
SamplerState linear_wrap : register(s0);

static const float planet_radius = 6360000.0;
static const float atmosphere_radius = 6420000.0;
static const float3 rayleigh_beta = float3(5.802e-6, 13.558e-6, 33.1e-6);
static const float mie_scatter = 3.996e-6;
static const float mie_absorb = 0.44e-6;
static const float3 ozone_beta = float3(0.65e-6, 1.881e-6, 0.085e-6);
static const float rayleigh_height = 8000.0;
static const float mie_height = 1200.0;
static const float cloud_height = 1900.0;

groupshared float3 sh_partial[64][9];

//=====================================================================================

float2 ray_sphere(float3 origin, float3 direction, float radius)
{
	float b = dot(origin, direction);
	float c = dot(origin, origin) - radius * radius;
	float d = b * b - c;
	float2 result = float2(1e20, -1e20);

	[branch] if (d >= 0.0)
	{
		result = float2(-b - sqrt(d), -b + sqrt(d));
	}

	return result;
}
/*
//=====================================================================================
*/
float3 densities(float height)
{
	return float3(exp(-height / rayleigh_height), exp(-height / mie_height), max(0.0, 1.0 - abs(height - 25000.0) / 15000.0));
}
/*
//=====================================================================================
*/
float3 extinction(float3 depth)
{
	return depth.x * rayleigh_beta + depth.y * (mie_scatter + mie_absorb) + depth.z * ozone_beta;
}
/*
//=====================================================================================
*/
float3 light_depth(float3 position, float3 light)
{
	float2 hit = ray_sphere(position, light, atmosphere_radius);
	float step = max(hit.y, 0.0) / 8.0;
	float3 depth = 0.0;

	[unroll] for (uint index = 0; index < 8; index++)
	{
		float3 sample_position = position + light * (step * (index + 0.5));

		depth += densities(length(sample_position) - planet_radius) * step;
	}

	return depth;
}
/*
//=====================================================================================
*/
float3 scatter(float3 direction, float3 light, float intensity, out float3 bounce_sum)
{
	float3 origin = float3(0.0, planet_radius + 250.0, 0.0);
	float2 outer = ray_sphere(origin, direction, atmosphere_radius);
	float2 ground = ray_sphere(origin, direction, planet_radius);
	float distance = ground.x > 0.0 ? min(outer.y, ground.x) : outer.y;
	float step = distance / 24.0;
	float3 view_depth = 0.0;
	float3 rayleigh_sum = 0.0;
	float3 mie_sum = 0.0;

	bounce_sum = 0.0;

	[loop] for (uint index = 0; index < 24; index++)
	{
		float3 sample_position = origin + direction * (step * (index + 0.5));
		float3 density = densities(length(sample_position) - planet_radius) * step;

		view_depth += density;
		bounce_sum += (density.x * rayleigh_beta + density.y * mie_scatter) * exp(-extinction(view_depth));

		[branch] if (ray_sphere(sample_position, light, planet_radius).x < 0.0)
		{
			float3 transmittance = exp(-extinction(view_depth + light_depth(sample_position, light)));

			rayleigh_sum += density.x * transmittance;
			mie_sum += density.y * transmittance;
		}
	}

	float mu = dot(direction, light);
	float rayleigh_phase = 3.0 / (16.0 * PI) * (1.0 + mu * mu);
	float g = 0.78;
	float mie_phase = 3.0 / (8.0 * PI) * ((1.0 - g * g) * (1.0 + mu * mu)) / ((2.0 + g * g) * pow(max(1.0 + g * g - 2.0 * g * mu, 0.0001), 1.5));

	return intensity * (rayleigh_sum * rayleigh_beta * rayleigh_phase + mie_sum * mie_scatter * mie_phase);
}
/*
//=====================================================================================
*/
float hash(float2 p)
{
	p = frac(p * float2(123.34, 456.21));
	p += dot(p, p + 45.32);

	return frac(p.x * p.y);
}
/*
//=====================================================================================
*/
float noise(float2 p)
{
	float2 cell = floor(p);
	float2 f = frac(p);
	float2 u = f * f * (3.0 - 2.0 * f);

	return lerp(lerp(hash(cell), hash(cell + float2(1.0, 0.0)), u.x), lerp(hash(cell + float2(0.0, 1.0)), hash(cell + float2(1.0, 1.0)), u.x), u.y);
}
/*
//=====================================================================================
*/
float fbm(float2 p)
{
	float sum = 0.0;
	float amplitude = 0.5;

	[unroll] for (uint octave = 0; octave < 6; octave++)
	{
		sum += noise(p) * amplitude;
		p = float2(p.x * 1.62 - p.y * 1.18, p.x * 1.18 + p.y * 1.62) + 7.3;
		amplitude *= 0.5;
	}

	return sum;
}
/*
//=====================================================================================
*/
float3 sky_color(float3 direction)
{
	float3 horizontal = normalize(float3(direction.x, max(direction.y, 0.002), direction.z));
	float3 bounce;
	float3 unused;
	float3 color = scatter(horizontal, atmosphere_sun.xyz, atmosphere_sun.w, bounce);

	[branch] if (atmosphere_moon.w > 0.0)
	{
		color += scatter(horizontal, atmosphere_moon.xyz, atmosphere_moon.w, unused);
	}

	color += bounce * max(sky_sh[0].rgb, 0.0) * (0.282095 * atmosphere_zenith.w);

	color += float3(0.0009, 0.0013, 0.0026) * atmosphere_clouds.w;

	[branch] if (direction.y > 0.004 && atmosphere_clouds.y > 0.0)
	{
		float travel = cloud_height / direction.y;
		float2 position = direction.xz * travel + atmosphere_clouds.x * float2(9.0, 4.0);
		float shape = fbm(position / 2600.0);
		float detail = fbm(position / 700.0 + 3.1);
		float coverage = atmosphere_clouds.y;
		float density = saturate((shape * 0.75 + detail * 0.35 - (1.02 - coverage)) * 2.4);
		float fade = saturate(1.0 - travel / 42000.0);
		float alpha = saturate(density * 1.6) * fade;

		[branch] if (alpha > 0.001)
		{
			float3 cloud_position = float3(position.x, planet_radius + cloud_height, position.y);
			float3 sun_light = exp(-extinction(light_depth(cloud_position, atmosphere_sun.xyz))) * atmosphere_sun.w * saturate(atmosphere_sun.y * 8.0 + 0.3);
			float3 moon_light = exp(-extinction(light_depth(cloud_position, atmosphere_moon.xyz))) * atmosphere_moon.w * saturate(atmosphere_moon.y * 8.0);
			float mu = dot(direction, atmosphere_sun.xyz);
			float forward = (1.0 - 0.36) / (4.0 * PI * pow(max(1.36 - 1.2 * mu, 0.0001), 1.5));
			float3 lit = (sun_light * (0.08 + forward * 0.35) + moon_light * 0.06) * (1.0 - density * 0.55) * atmosphere_clouds.z + atmosphere_zenith.rgb * 1.6;

			color = lerp(color, lit, alpha);
		}
	}

	[branch] if (direction.y < 0.0)
	{
		color *= lerp(1.0, 0.3, saturate(-direction.y * 5.0));
	}

	return color;
}
/*
//=====================================================================================
*/
[numthreads(8, 8, 1)]
void cs_atmosphere(uint3 id : SV_DispatchThreadID)
{
	uint2 size = uint2(atmosphere_size.xy);
	uint2 texel = uint2(id.x, id.y + (uint)atmosphere_size.z);

	[branch] if (texel.x < size.x && texel.y < size.y)
	{
		float phi = ((texel.x + 0.5) / size.x - 0.5) * TWO_PI;
		float theta = (texel.y + 0.5) / size.y * PI;
		float3 direction = float3(sin(theta) * sin(phi), cos(theta), sin(theta) * cos(phi));

		sky_output[texel] = float4(min(sky_color(direction), 60000.0), 1.0);
	}
}
/*
//=====================================================================================
*/
[numthreads(64, 1, 1)]
void cs_sh(uint3 id : SV_GroupThreadID)
{
	float3 sums[9];

	[unroll] for (uint clear = 0; clear < 9; clear++)
	{
		sums[clear] = 0.0;
	}

	[loop] for (uint row = 0; row < 32; row++)
	{
		float phi = ((id.x + 0.5) / 64.0 - 0.5) * TWO_PI;
		float theta = (row + 0.5) / 32.0 * PI;
		float3 d = float3(sin(theta) * sin(phi), cos(theta), sin(theta) * cos(phi));
		float weight = sin(theta) * (PI / 32.0) * (TWO_PI / 64.0);
		float3 radiance = sky_input.SampleLevel(linear_wrap, float2((id.x + 0.5) / 64.0, (row + 0.5) / 32.0), 3.0).rgb * weight;

		sums[0] += radiance * 0.282095;
		sums[1] += radiance * (0.488603 * d.y);
		sums[2] += radiance * (0.488603 * d.z);
		sums[3] += radiance * (0.488603 * d.x);
		sums[4] += radiance * (1.092548 * d.x * d.y);
		sums[5] += radiance * (1.092548 * d.y * d.z);
		sums[6] += radiance * (0.315392 * (3.0 * d.z * d.z - 1.0));
		sums[7] += radiance * (1.092548 * d.x * d.z);
		sums[8] += radiance * (0.546274 * (d.x * d.x - d.y * d.y));
	}

	[unroll] for (uint coefficient = 0; coefficient < 9; coefficient++)
	{
		sh_partial[id.x][coefficient] = sums[coefficient];
	}

	GroupMemoryBarrierWithGroupSync();

	[branch] if (id.x < 9)
	{
		float3 total = 0.0;

		[loop] for (uint column = 0; column < 64; column++)
		{
			total += sh_partial[column][id.x];
		}

		sh_output[id.x] = float4(total, 0.0);
	}
}

//=====================================================================================
