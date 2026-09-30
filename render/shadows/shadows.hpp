
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class shadows_c
	{
	public:

		ID3D11Texture2D* texture = nullptr;
		ID3D11DepthStencilView* views[shadow_cascade_count]{};
		ID3D11ShaderResourceView* resource = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		ID3D11VertexShader* alpha_vertex_shader = nullptr;
		ID3D11PixelShader* alpha_pixel_shader = nullptr;
		ID3D11InputLayout* alpha_layout = nullptr;
		ID3D11VertexShader* skinned_vertex_shader = nullptr;
		ID3D11InputLayout* skinned_layout = nullptr;
		std::uint32_t resolution = 0u;
		std::uint32_t cascades = shadow_cascade_count;
		std::uint32_t extents[shadow_cascade_count]{};
		std::float_t distance = 120.0f;
		structures::shadow_constants_s constants{};
		structures::vec4_s planes[shadow_cascade_count][6]{};

		bool create();
		void destroy();
		bool configure(std::uint32_t quality);
		void destroy_maps();
		void update(const structures::camera_s& camera, structures::vec3_s sun);
		void begin_cascade(std::uint32_t cascade);
		void bind(std::uint32_t slot);
	};

	extern shadows_c shadows;
}

//=====================================================================================
