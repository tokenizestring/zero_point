
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class particles_c
	{
	public:

		std::vector<structures::particle_s> pool;
		std::vector<structures::particle_vertex_s> vertices;
		std::vector<std::pair<std::float_t, std::uint32_t>> order;
		ID3D11Buffer* vertex_buffer = nullptr;
		ID3D11Buffer* index_buffer = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11PixelShader* pixel_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		std::uint32_t seed = 0x3C6EF372u;
		std::float_t clock = 0.0f;
		std::float_t torch_budget = 0.0f;

		bool create();
		void destroy();
		void clear();
		void emit(std::uint32_t kind, structures::vec3_s position, structures::vec3_s velocity, std::float_t spread, std::uint32_t count, bool view_space);
		void torch(structures::vec3_s head, std::float_t delta);
		void impact(std::uint32_t surface, structures::vec3_s position, structures::vec3_s normal);
		void update(std::float_t delta);
		void render();
		std::uint32_t build(bool view_space);
		std::float_t random();
	};

	extern particles_c particles;
}

//=====================================================================================
