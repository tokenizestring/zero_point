
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class water_c
	{
	public:

		structures::water_constants_s constants{};
		structures::target_s scene_copy{};
		ID3D11Buffer* vertex_buffer = nullptr;
		ID3D11Buffer* index_buffer = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11PixelShader* pixel_shader = nullptr;
		ID3D11PixelShader* underwater_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		ID3D11ShaderResourceView* normal_view = nullptr;
		std::uint32_t index_count = 0u;
		std::float_t height = 0.0f;
		bool enabled = false;

		bool create();
		void destroy();
		bool resize(std::uint32_t width, std::uint32_t height_pixels);
		void render();
		void render_underwater();
		std::float_t level(std::float_t x, std::float_t z);
		std::float_t still();
	};

	extern water_c water;
}

//=====================================================================================
