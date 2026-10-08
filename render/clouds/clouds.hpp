
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class clouds_c
	{
	public:

		structures::target_s march{};
		structures::target_s history[2]{};
		structures::target_s weather_map{};
		structures::target_s shadow_map{};
		ID3D11ShaderResourceView* shape_view = nullptr;
		ID3D11ShaderResourceView* detail_view = nullptr;
		ID3D11ComputeShader* shape_cs = nullptr;
		ID3D11ComputeShader* detail_cs = nullptr;
		ID3D11ComputeShader* weather_cs = nullptr;
		ID3D11ComputeShader* march_cs = nullptr;
		ID3D11ComputeShader* resolve_cs = nullptr;
		ID3D11ComputeShader* shadow_cs = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		structures::cloud_constants_s values{};
		std::uint32_t width = 0u;
		std::uint32_t height = 0u;
		std::uint32_t latest = 0u;
		bool ready = false;
		bool active = false;
		bool valid = false;

		bool create();
		void destroy();
		bool resize(std::uint32_t full_width, std::uint32_t full_height);
		ID3D11ShaderResourceView* volume(ID3D11ComputeShader* shader, std::uint32_t size);
		void generate();
		ID3D11ShaderResourceView* compute(std::uint32_t quality, std::uint64_t frame);
		void bind();
	};

	extern clouds_c clouds;
}

//=====================================================================================
