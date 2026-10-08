
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class atmosphere_c
	{
	public:

		ID3D11Texture2D* texture = nullptr;
		ID3D11ShaderResourceView* view = nullptr;
		ID3D11UnorderedAccessView* access = nullptr;
		ID3D11Texture2D* clear_texture = nullptr;
		ID3D11ShaderResourceView* clear_view = nullptr;
		ID3D11UnorderedAccessView* clear_access = nullptr;
		ID3D11ComputeShader* sky_shader = nullptr;
		ID3D11ComputeShader* sh_shader = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11Buffer* sh_buffer = nullptr;
		ID3D11UnorderedAccessView* sh_access = nullptr;
		ID3D11Buffer* sh_staging = nullptr;
		structures::atmosphere_constants_s constants{};
		structures::vec3_s sun{};
		structures::vec3_s moon{};
		std::float_t hours = 8.5f;
		std::float_t refresh = 0.0f;
		std::float_t drift = 0.0f;
		std::uint32_t strip = 0u;
		bool enabled = false;
		bool updating = false;
		bool sh_pending = false;

		bool create();
		void destroy();
		void enable(std::float_t start_hours);
		void update(std::float_t delta);
		std::float_t advance(std::float_t current, std::float_t delta);
		void place_bodies();
		void begin_refresh();
		void render_strip();
		void finish();
		void read_sh(bool wait);
		structures::vec3_s light_depth(structures::vec3_s position, structures::vec3_s light);
		structures::vec3_s extinction(structures::vec3_s depth);
		structures::vec3_s scatter(structures::vec3_s direction, structures::vec3_s light, std::float_t intensity);
	};

	extern atmosphere_c atmosphere;
}

//=====================================================================================
