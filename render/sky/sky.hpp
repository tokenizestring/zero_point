
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class sky_c
	{
	public:

		std::vector<structures::sky_record_s> records;
		std::int32_t current = -1;

		ID3D11ShaderResourceView* equirect = nullptr;
		ID3D11Texture2D* base_texture = nullptr;
		ID3D11ShaderResourceView* base = nullptr;
		ID3D11UnorderedAccessView* base_uav = nullptr;
		ID3D11Texture2D* prefiltered_texture = nullptr;
		ID3D11ShaderResourceView* prefiltered = nullptr;
		ID3D11UnorderedAccessView* prefiltered_uavs[sky_prefilter_mips]{};
		ID3D11Texture2D* lut_texture = nullptr;
		ID3D11ShaderResourceView* lut = nullptr;
		ID3D11UnorderedAccessView* lut_uav = nullptr;
		ID3D11ComputeShader* equirect_shader = nullptr;
		ID3D11ComputeShader* prefilter_shader = nullptr;
		ID3D11ComputeShader* lut_shader = nullptr;
		ID3D11Buffer* constants = nullptr;

		std::float_t rotation = 0.0f;
		std::float_t intensity = 1.0f;
		std::float_t sun_intensity = 1.0f;
		std::float_t stars = 0.0f;
		structures::vec3_s sun_direction{ 0.0f, 1.0f, 0.0f };
		structures::vec3_s sun_color{};
		std::float_t sun_radius = 0.0093f;
		std::float_t ground_albedo = 0.16f;
		structures::vec4_s sh[sky_sh_coefficients]{};
		structures::vec4_s base_sh[sky_sh_coefficients]{};

		void add_ground_bounce();

		bool create();
		void destroy();
		bool select(const char* name);
		void build();
		void set_rotation(std::float_t radians);
		void dispatch(ID3D11ComputeShader* shader, std::uint32_t size, std::uint32_t depth, structures::sky_constants_s parameters);
	};

	extern sky_c sky;
}

//=====================================================================================
