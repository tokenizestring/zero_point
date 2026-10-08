
//=====================================================================================

#ifndef CLOUDS_HLSLI
#define CLOUDS_HLSLI

cbuffer cloud_constants : register(b5)
{
	float4 cloud_layer;
	float4 cloud_wind;
	float4 cloud_shade;
	float4 cloud_target;
	float4 cloud_state;
	float4 cloud_area;
};

static const float cloud_planet = 6360000.0;
static const float cloud_weather_extent = 40960.0;
static const float cloud_shape_extent = 7200.0;
static const float cloud_detail_extent = 960.0;
static const float cloud_reach = 52000.0;
static const float cloud_haze_start = 9000.0;
static const float cloud_haze = 30000.0;

//=====================================================================================

float cloud_remap(float value, float low, float high, float target_low, float target_high)
{
	return target_low + (value - low) * (target_high - target_low) / max(high - low, 0.0001);
}
/*
//=====================================================================================
*/
float cloud_cover(float4 weather)
{
	return saturate(weather.r * 1.35 + cloud_layer.z);
}
/*
//=====================================================================================
*/
float cloud_altitude(float height, float3 direction, float travel)
{
	return height + travel * direction.y + travel * travel * (1.0 - direction.y * direction.y) / (2.0 * cloud_planet);
}
/*
//=====================================================================================
*/
float2 cloud_roots(float height, float rise, float altitude)
{
	float bend = max((1.0 - rise * rise) / (2.0 * cloud_planet), 1e-12);
	float offset = height - altitude;
	float discriminant = rise * rise - 4.0 * bend * offset;
	float2 result = float2(-1.0, -1.0);

	[branch] if (discriminant >= 0.0)
	{
		float q = -0.5 * (rise + (rise >= 0.0 ? 1.0 : -1.0) * sqrt(discriminant));
		float first = q / bend;
		float second = abs(q) > 1e-9 ? offset / q : first;

		result = float2(min(first, second), max(first, second));
	}

	return result;
}
/*
//=====================================================================================
*/
float2 cloud_interval(float height, float rise)
{
	float2 low = cloud_roots(height, rise, cloud_layer.x);
	float2 high = cloud_roots(height, rise, cloud_layer.y);
	float2 result = float2(0.0, high.y);

	[branch] if (height < cloud_layer.x)
	{
		result = float2(low.y, high.y);
	}

	else if (height > cloud_layer.y)
	{
		result = float2(high.x, low.x > 0.0 ? low.x : high.y);
	}

	else if (low.x > 0.0)
	{
		result.y = min(result.y, low.x);
	}

	return float2(max(result.x, 0.0), min(result.y, cloud_reach));
}
/*
//=====================================================================================
*/
float3 cloud_ray(float2 uv)
{
	float4 far_point = mul(float4(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0, 0.0001, 1.0), inverse_view_projection);

	return normalize(far_point.xyz / far_point.w - camera_position.xyz);
}
/*
//=====================================================================================
*/
float cloud_sunlight(Texture2D<float> shadows, SamplerState clamp_sampler, float3 position)
{
	float result = 1.0;

	[branch] if (cloud_state.x > 0.5 && sun_direction.y > 0.0)
	{
		float2 uv = (position.xz - sun_direction.xz * (position.y / max(sun_direction.y, 0.08)) - cloud_area.xy) / cloud_area.z;
		float2 edge = saturate(min(uv, 1.0 - uv) * 12.0);
		float passage = lerp(cloud_shade.x, 1.0, shadows.SampleLevel(clamp_sampler, uv, 0.0));

		result = lerp(1.0, passage, edge.x * edge.y * saturate(sun_direction.y * 6.0));
	}

	return result;
}

#endif

//=====================================================================================
