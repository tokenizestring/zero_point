
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class terrain_c
	{
	public:

		structures::terrain_header_s header{};
		structures::terrain_constants_s constants{};
		const std::float_t* heights = nullptr;
		const std::uint8_t* biome_data = nullptr;
		const std::uint8_t* ground_data = nullptr;
		std::vector<std::uint8_t> grass_mask;
		ID3D11ShaderResourceView* mask_view = nullptr;
		std::vector<std::vector<structures::vec2_s>> bounds;
		std::vector<structures::vec4_s> instances;
		ID3D11ShaderResourceView* height_view = nullptr;
		ID3D11ShaderResourceView* shading_view = nullptr;
		ID3D11ShaderResourceView* grass_view = nullptr;
		ID3D11ShaderResourceView* splat_views[terrain_splat_count]{};
		ID3D11Buffer* vertex_buffer = nullptr;
		ID3D11Buffer* index_buffer = nullptr;
		ID3D11Buffer* instance_buffer = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;
		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11VertexShader* shadow_vertex_shader = nullptr;
		ID3D11PixelShader* pixel_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		ID3D11InputLayout* shadow_layout = nullptr;
		std::uint32_t index_count = 0u;
		structures::vec3_s camera{};
		bool enabled = false;

		bool create();
		void destroy();
		bool load();
		void unload();
		std::uint64_t strip();
		std::float_t height(std::float_t x, std::float_t z);
		structures::vec3_s normal(std::float_t x, std::float_t z);
		std::uint32_t ground(std::float_t x, std::float_t z);
		std::uint32_t biome(std::float_t x, std::float_t z);
		void mask_rectangle(structures::vec3_s center, std::float_t half_x, std::float_t half_z, std::float_t yaw);
		bool upload_mask();
		std::float_t sample(std::int32_t x, std::int32_t z);
		std::float_t range(std::uint32_t level);
		void select(const structures::vec4_s* planes, std::uint32_t plane_count);
		bool select_node(std::uint32_t x, std::uint32_t z, std::uint32_t level, const structures::vec4_s* planes, std::uint32_t plane_count);
		void add(std::uint32_t x, std::uint32_t z, std::uint32_t level, const structures::vec4_s* planes, std::uint32_t plane_count);
		void node_box(std::uint32_t x, std::uint32_t z, std::uint32_t level, structures::vec3_s& minimum, structures::vec3_s& maximum);
		void draw(bool shadow_pass);
		void clip(structures::vec3_s start, structures::vec3_s end, structures::vec3_s extents, structures::trace_s& result);
	};

	extern terrain_c terrain;
}

//=====================================================================================
