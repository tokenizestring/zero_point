
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class foliage_c
	{
	public:

		std::vector<structures::foliage_species_s> species;
		std::vector<structures::foliage_instance_s> instances;
		std::vector<structures::foliage_cell_s> cells;
		std::vector<structures::foliage_bucket_s> buckets;
		std::vector<std::vector<std::uint8_t>> bucket_alpha;
		std::vector<structures::foliage_gpu_s> staging;
		std::vector<std::uint32_t> species_near;
		std::vector<std::uint32_t> species_far;
		std::vector<std::uint32_t> species_impostor;
		std::vector<std::uint32_t> species_shadow;
		structures::vec3_s origin{};
		std::uint32_t cells_x = 0u;
		std::uint32_t cells_z = 0u;
		std::float_t reach = 0.0f;
		ID3D11Buffer* instance_buffer = nullptr;
		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11VertexShader* shadow_vertex_shader = nullptr;
		ID3D11VertexShader* shadow_alpha_vertex_shader = nullptr;
		ID3D11VertexShader* impostor_vertex_shader = nullptr;
		ID3D11PixelShader* impostor_pixel_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		ID3D11InputLayout* shadow_layout = nullptr;
		ID3D11InputLayout* shadow_alpha_layout = nullptr;
		ID3D11InputLayout* impostor_layout = nullptr;

		bool create();
		void destroy();
		void clear();
		std::uint32_t add_species(const char* near_model, const char* far_model, std::float_t near_distance, std::float_t far_distance, std::float_t shadow_distance, std::float_t sway);
		bool add_impostor(std::uint32_t species_index, const char* model_name, std::float_t distance);
		bool add_shadow(std::uint32_t species_index, const char* model_name);
		std::uint32_t bucket(const structures::model_s* model, bool impostor);
		void add(std::uint32_t species_index, structures::vec3_s position, std::float_t yaw, std::float_t scale);
		void build(structures::vec3_s minimum, structures::vec3_s maximum);
		void select(structures::vec3_s camera, const structures::vec4_s* planes, std::uint32_t plane_count, bool shadow_pass);
		void push(std::uint32_t bucket_index, std::uint32_t index, std::float_t fade);
		void report();
		void draw(bool shadow_pass);
	};

	extern foliage_c foliage;
}

//=====================================================================================
