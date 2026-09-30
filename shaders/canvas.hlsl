
//=====================================================================================

cbuffer canvas_constants : register(b0)
{
	float2 screen_size;
	float2 inverse_screen_size;
};

Texture2D canvas_texture : register(t0);
SamplerState canvas_sampler : register(s0);

//=====================================================================================

struct vertex_input
{
	float2 position : POSITION;
	float2 uv : TEXCOORD0;
	float4 color : COLOR0;
	float4 params : TEXCOORD1;
	float4 extra : TEXCOORD2;
};

struct pixel_input
{
	float4 position : SV_Position;
	float2 uv : TEXCOORD0;
	float4 color : COLOR0;
	float4 params : TEXCOORD1;
	float4 extra : TEXCOORD2;
};

//=====================================================================================

pixel_input vs_main(vertex_input input)
{
	pixel_input output;

	output.position = float4(input.position.x * inverse_screen_size.x * 2.0 - 1.0, 1.0 - input.position.y * inverse_screen_size.y * 2.0, 0.0, 1.0);
	output.uv = input.uv;
	output.color = input.color;
	output.params = input.params;
	output.extra = input.extra;

	return output;
}
/*
//=====================================================================================
*/
float4 ps_main(pixel_input input) : SV_Target
{
	float4 color = input.color;

	uint mode = (uint)(input.params.x + 0.5);

	if (mode == 1)
	{
		color *= canvas_texture.Sample(canvas_sampler, input.uv);
	}

	else if (mode == 2)
	{
		float distance = canvas_texture.Sample(canvas_sampler, input.uv).r;
		float width = max(fwidth(distance), 0.0001) * (0.7 + input.params.y);

		color.a *= smoothstep(0.5 - width - input.params.z, 0.5 + width - input.params.z, distance);
	}

	else if (mode == 3)
	{
		float2 q = abs(input.uv) - input.extra.xy + input.extra.z;
		float distance = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - input.extra.z;

		if (input.extra.w > 0.0)
		{
			distance = abs(distance + input.extra.w * 0.5) - input.extra.w * 0.5;
		}

		color.a *= saturate(0.5 - distance / max(input.params.y, 0.5));
	}

	else if (mode == 4)
	{
		float radius = length(input.uv);
		float distance = abs(radius - (input.extra.x - input.extra.y * 0.5)) - input.extra.y * 0.5;
		float angle = atan2(input.uv.x, -input.uv.y);

		if (angle < 0.0)
		{
			angle += 6.28318530718;
		}

		float arc = min(angle - input.extra.z, input.extra.w - angle) * radius;

		color.a *= saturate(0.5 - distance) * saturate(0.5 + arc);
	}

	return color;
}

//=====================================================================================
