
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class ssao_c
	{
	public:

		structures::target_s raw{};
		structures::target_s blurred{};
		ID3D11ComputeShader* ssao_cs = nullptr;
		ID3D11ComputeShader* blur_cs = nullptr;
		ID3D11Buffer* constants = nullptr;
		std::uint32_t width = 0u;
		std::uint32_t height = 0u;

		bool create();
		void destroy();
		bool resize(std::uint32_t full_width, std::uint32_t full_height);
		ID3D11ShaderResourceView* compute(ID3D11ShaderResourceView* depth_view, ID3D11ShaderResourceView* normal_view, std::uint32_t quality);
		void pass(ID3D11ComputeShader* shader, ID3D11ShaderResourceView* source, ID3D11UnorderedAccessView* target, structures::vec4_s params);
	};

	extern ssao_c ssao;
}

//=====================================================================================
