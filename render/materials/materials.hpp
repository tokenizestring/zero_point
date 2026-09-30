
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class materials_c
	{
	public:

		ID3D11ShaderResourceView* albedo = nullptr;
		ID3D11ShaderResourceView* normal = nullptr;
		ID3D11ShaderResourceView* rough_ao = nullptr;
		ID3D11ShaderResourceView* height_metal = nullptr;
		ID3D11Buffer* table_buffer = nullptr;
		ID3D11ShaderResourceView* table = nullptr;

		std::vector<structures::material_record_s> sets;
		std::vector<structures::material_gpu_s> gpu_materials;

		bool create(std::uint32_t skip_mips);
		bool upload();
		void destroy();
		std::uint32_t register_model_material(const structures::model_material_s& record);
		std::uint32_t set_index(const char* texture_set);
		structures::material_gpu_s build(const structures::material_definition_s& definition);
		structures::vec3_s average_albedo(std::uint32_t material);
		void bind(std::uint32_t first_slot);
	};

	extern materials_c materials;
}

//=====================================================================================
