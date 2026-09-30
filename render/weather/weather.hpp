
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class weather_c
	{
	public:

		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11PixelShader* pixel_shader = nullptr;
		ID3D11VertexShader* splash_vertex = nullptr;
		ID3D11PixelShader* splash_pixel = nullptr;
		ID3D11VertexShader* bolt_vertex = nullptr;
		ID3D11PixelShader* bolt_pixel = nullptr;
		ID3D11Buffer* bolt_buffer = nullptr;
		structures::bolt_constants_s bolt{};
		std::float_t bolt_life = 0.0f;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11Texture2D* roof_texture = nullptr;
		ID3D11ShaderResourceView* roof_view = nullptr;
		std::vector<std::float_t> roofs;
		std::vector<std::int64_t> roof_cells;
		std::uint32_t roof_cursor = 0u;
		bool roof_dirty = false;
		structures::vec3_s wind{};
		std::float_t cloud = 0.08f;
		std::float_t rain = 0.0f;
		std::float_t storm = 0.0f;
		std::float_t cloud_now = 0.08f;
		std::float_t rain_now = 0.0f;
		std::float_t storm_now = 0.0f;
		std::float_t wetness = 0.0f;
		std::float_t flash = 0.0f;
		std::float_t bolt_timer = 5.0f;
		std::float_t thunder_timer = -1.0f;
		std::float_t thunder_volume = 0.0f;
		std::float_t clock = 0.0f;
		std::uint32_t seed = 0x6D2B79F5u;
		bool forced = false;

		bool create();
		void destroy();
		void set(std::float_t next_cloud, std::float_t next_rain, std::float_t next_storm);
		void update(std::float_t delta);
		void survey();
		void strike(std::float_t distance);
		void channel(structures::vec3_s from, structures::vec3_s to, std::uint32_t steps, std::float_t wander, std::float_t width, std::float_t intensity);
		void render();
		structures::vec4_s params();
		std::float_t random();
	};

	extern weather_c weather;
}

//=====================================================================================
