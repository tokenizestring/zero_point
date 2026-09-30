
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class grass_c
	{
	public:

		structures::grass_constants_s constants{};
		ID3D11Buffer* vertex_buffer = nullptr;
		ID3D11Buffer* index_buffer = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		std::uint32_t index_count = 0u;
		std::uint32_t instance_count = 0u;
		bool ready = false;

		bool create();
		void destroy();
		std::uint32_t variant(std::uint32_t source, structures::vec3_s tint);
		void draw();
	};

	extern grass_c grass;
}

//=====================================================================================
