
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class decals_c
	{
	public:

		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11PixelShader* pixel_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		ID3D11Buffer* vertex_buffer = nullptr;
		ID3D11Buffer* index_buffer = nullptr;
		ID3D11Buffer* instance_buffer = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11BlendState* blend = nullptr;
		ID3D11RasterizerState* raster = nullptr;
		ID3D11SamplerState* sampler = nullptr;
		ID3D11ShaderResourceView* color_view = nullptr;
		ID3D11ShaderResourceView* shape_view = nullptr;
		std::vector<structures::decal_gpu_s> rough;
		std::vector<structures::decal_gpu_s> gloss;
		std::uint32_t drawn = 0u;
		std::uint32_t peak = 0u;
		bool ready = false;

		bool create();
		void destroy();
		void gather();
		void render();
	};

	extern decals_c decals;
}

//=====================================================================================
