
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	materials_c materials;

	bool materials_c::create(std::uint32_t skip_mips)
	{
		albedo = pak.create_texture("materials_albedo", skip_mips, false, false);
		normal = pak.create_texture("materials_normal", skip_mips, false, false);
		rough_ao = pak.create_texture("materials_rough_ao", skip_mips, false, false);
		height_metal = pak.create_texture("materials_height_metal", skip_mips, false, false);

		if (const auto entry{ pak.find("materials_table") }; entry && entry->layers)
		{
			sets.resize(entry->layers);

			std::memcpy(sets.data(), pak.data(entry), sets.size() * sizeof(structures::material_record_s));
		}

		gpu_materials.clear();

		for (const auto& definition : material_definitions)
		{
			gpu_materials.push_back(build(definition));
		}

		logger.write("materials: %zu texture sets, %zu materials", sets.size(), gpu_materials.size());

		return albedo && normal && rough_ao && height_metal && sets.size();
	}
	/*
	//=====================================================================================
	*/
	bool materials_c::upload()
	{
		functions::release(table);
		functions::release(table_buffer);

		table_buffer = gpu.create_buffer(static_cast<std::uint32_t>(gpu_materials.size() * sizeof(structures::material_gpu_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_SHADER_RESOURCE, 0u, gpu_materials.data(), D3D11_RESOURCE_MISC_BUFFER_STRUCTURED, sizeof(structures::material_gpu_s));

		if (table_buffer)
		{
			gpu.device->CreateShaderResourceView(table_buffer, nullptr, &table);
		}

		return table != nullptr || gpu.device == nullptr;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t materials_c::register_model_material(const structures::model_material_s& record)
	{
		structures::material_gpu_s material{};

		material.tint = { 1.0f, 1.0f, 1.0f, 1.0f };
		material.layer = set_index(record.set_name);
		material.uv_scale = 1.0f;
		material.normal_strength = 1.0f;
		material.height_scale = 0.0f;
		material.roughness_scale = record.roughness_scale;
		material.roughness_bias = 0.0f;
		material.metal_scale = record.metal_scale;
		material.metal_bias = 0.0f;
		material.emissive = record.emissive * 8.0f;
		material.aspect = 1.0f;
		material.flags = record.flags;
		material.ao_strength = 1.0f;
		material.specular = 0.5f;

		if (record.flags & structures::material_flag_glass)
		{
			material.tint = { 0.06f, 0.065f, 0.07f, 1.0f };
			material.roughness_scale = 0.0f;
			material.roughness_bias = 0.06f;
			material.metal_scale = 0.0f;
		}

		gpu_materials.push_back(material);

		return static_cast<std::uint32_t>(gpu_materials.size() - 1u);
	}
	/*
	//=====================================================================================
	*/
	void materials_c::destroy()
	{
		functions::release(table);
		functions::release(table_buffer);
		functions::release(height_metal);
		functions::release(rough_ao);
		functions::release(normal);
		functions::release(albedo);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t materials_c::set_index(const char* texture_set)
	{
		for (auto index{ 0u }; index < sets.size(); index++)
		{
			if (std::strcmp(sets[index].name, texture_set) == 0)
			{
				return index;
			}
		}

		logger.write("materials: unknown texture set %s", texture_set);

		return 0u;
	}
	/*
	//=====================================================================================
	*/
	structures::material_gpu_s materials_c::build(const structures::material_definition_s& definition)
	{
		structures::material_gpu_s material{};

		const auto layer{ set_index(definition.texture_set) };

		material.tint = { definition.tint.x, definition.tint.y, definition.tint.z, 1.0f };
		material.layer = layer;
		material.uv_scale = definition.uv_scale;
		material.normal_strength = definition.normal_strength;
		material.height_scale = layer < sets.size() ? sets[layer].height_scale : 0.0f;
		material.roughness_scale = definition.roughness_scale;
		material.roughness_bias = definition.roughness_bias;
		material.metal_scale = definition.metal_scale;
		material.metal_bias = definition.metal_bias;
		material.emissive = definition.emissive;
		material.aspect = layer < sets.size() ? sets[layer].aspect : 1.0f;
		material.flags = definition.flags;
		material.ao_strength = 1.0f;
		material.specular = 0.5f;

		return material;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s materials_c::average_albedo(std::uint32_t material)
	{
		if (material < gpu_materials.size() && gpu_materials[material].layer < sets.size())
		{
			return sets[gpu_materials[material].layer].average_albedo * gpu_materials[material].tint.xyz();
		}

		return { 0.3f, 0.3f, 0.3f };
	}
	/*
	//=====================================================================================
	*/
	void materials_c::bind(std::uint32_t first_slot)
	{
		ID3D11ShaderResourceView* views[5] = { albedo, normal, rough_ao, height_metal, table };

		gpu.context->PSSetShaderResources(first_slot, 5u, views);
	}
}

//=====================================================================================
