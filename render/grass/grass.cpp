
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	grass_c grass;

	bool grass_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::grass_vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "NORMAL", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::grass_vertex_s, normal), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::grass_vertex_s, uv), D3D11_INPUT_PER_VERTEX_DATA, 0u }
		};

		std::vector<structures::grass_vertex_s> vertices;
		std::vector<std::uint32_t> indices;

		for (auto card{ 0u }; card < grass_cards; card++)
		{
			const auto angle{ static_cast<std::float_t>(card) * two_pi / static_cast<std::float_t>(grass_cards) };
			const structures::vec3_s outward{ std::sin(angle), 0.0f, std::cos(angle) };
			const structures::vec3_s axis{ std::cos(angle) * 0.5f, 0.0f, -std::sin(angle) * 0.5f };
			const auto center{ outward * grass_card_offset };
			const auto first{ static_cast<std::uint32_t>(vertices.size()) };

			for (auto row{ 0u }; row < grass_card_rows; row++)
			{
				const auto height{ static_cast<std::float_t>(row) / static_cast<std::float_t>(grass_card_rows - 1u) };

				vertices.push_back({ center - axis + structures::vec3_s{ 0.0f, height, 0.0f }, outward, { 0.0f, 1.0f - height } });
				vertices.push_back({ center + axis + structures::vec3_s{ 0.0f, height, 0.0f }, outward, { 1.0f, 1.0f - height } });
			}

			for (auto row{ 0u }; row + 1u < grass_card_rows; row++)
			{
				const auto base{ first + row * 2u };

				indices.insert(indices.end(), { base, base + 1u, base + 3u, base, base + 3u, base + 2u });
			}
		}

		const auto near_count{ static_cast<std::uint32_t>(std::ceil(2.0f * grass_near_radius / grass_near_spacing)) + 1u };
		const auto far_count{ static_cast<std::uint32_t>(std::ceil(2.0f * grass_far_radius / grass_far_spacing)) + 1u };

		index_count = static_cast<std::uint32_t>(indices.size());
		instance_count = near_count * near_count + far_count * far_count;
		vertex_buffer = gpu.create_buffer(static_cast<std::uint32_t>(vertices.size() * sizeof(structures::grass_vertex_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, vertices.data(), 0u, 0u);
		index_buffer = gpu.create_buffer(static_cast<std::uint32_t>(indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, indices.data(), 0u, 0u);
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::grass_constants_s));
		vertex_shader = gpu.create_vertex_shader("gbuffer_grass_vs", elements, 3u, &layout);

		constants.rings[0] = { grass_near_spacing, grass_near_radius, 0.0f, static_cast<std::float_t>(near_count) };
		constants.rings[1] = { grass_far_spacing, grass_far_radius, grass_far_inner, static_cast<std::float_t>(far_count) };

		for (auto sprite{ 0u }; sprite < grass_sprite_count; sprite++)
		{
			constants.sprites[sprite] = grass_sprites[sprite];
		}

		if (const auto model{ models.find("grass_clumps") }; model && model->materials.size())
		{
			constants.materials[0] = variant(model->materials[0], { 1.0f, 1.0f, 1.0f });
			constants.materials[1] = variant(model->materials[0], { 0.9f, 1.04f, 0.9f });
			constants.materials[2] = variant(model->materials[0], { 1.1f, 1.04f, 0.84f });
			constants.materials[3] = variant(model->materials[0], { 1.14f, 1.02f, 0.78f });

			ready = materials.upload();
		}

		logger.write("grass: %u instances per frame, %s", instance_count, ready ? "ready" : "unavailable");

		return vertex_buffer && index_buffer && constant_buffer && vertex_shader && layout;
	}
	/*
	//=====================================================================================
	*/
	void grass_c::destroy()
	{
		functions::release(vertex_buffer);
		functions::release(index_buffer);
		functions::release(constant_buffer);
		functions::release(vertex_shader);
		functions::release(layout);

		ready = false;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t grass_c::variant(std::uint32_t source, structures::vec3_s tint)
	{
		auto material{ materials.gpu_materials[source] };

		material.tint = { tint.x, tint.y, tint.z, 1.0f };
		material.flags |= structures::material_flag_alpha_test | structures::material_flag_two_sided;
		material.roughness_bias = std::max(material.roughness_bias, 0.35f);
		material.specular = 0.3f;
		material.normal_strength = 0.0f;

		materials.gpu_materials.push_back(material);

		return static_cast<std::uint32_t>(materials.gpu_materials.size() - 1u);
	}
	/*
	//=====================================================================================
	*/
	void grass_c::draw()
	{
		if (ready && terrain.enabled)
		{
			const auto stride{ static_cast<UINT>(sizeof(structures::grass_vertex_s)) };
			const auto offset{ 0u };

			ID3D11ShaderResourceView* views[3] = { terrain.height_view, terrain.grass_view, terrain.mask_view };
			ID3D11ShaderResourceView* unbound[3]{};

			const auto reach{ std::max(renderer.settings.grass, 0.2f) };
			const auto near_count{ static_cast<std::uint32_t>(std::ceil(2.0f * grass_near_radius * reach / grass_near_spacing)) + 1u };
			const auto far_count{ static_cast<std::uint32_t>(std::ceil(2.0f * grass_far_radius * reach / grass_far_spacing)) + 1u };

			instance_count = near_count * near_count + far_count * far_count;

			constants.rings[0] = { grass_near_spacing, grass_near_radius * reach, 0.0f, static_cast<std::float_t>(near_count) };
			constants.rings[1] = { grass_far_spacing, grass_far_radius * reach, grass_far_inner * reach, static_cast<std::float_t>(far_count) };
			constants.terrain = { terrain.header.origin, terrain.header.world_size, static_cast<std::float_t>(terrain.header.resolution), grass_size };

			gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

			renderer.set_object(mathematics.identity(), mathematics.identity(), -1.0f, 0u);

			gpu.context->IASetInputLayout(layout);
			gpu.context->IASetVertexBuffers(0u, 1u, &vertex_buffer, &stride, &offset);
			gpu.context->IASetIndexBuffer(index_buffer, DXGI_FORMAT_R32_UINT, 0u);
			gpu.context->VSSetShader(vertex_shader, nullptr, 0u);
			gpu.context->VSSetShaderResources(terrain_height_slot, 3u, views);
			gpu.context->VSSetSamplers(1u, 1u, &gpu.sampler_linear_clamp);
			gpu.context->VSSetConstantBuffers(4u, 1u, &constant_buffer);
			gpu.context->PSSetShader(renderer.gbuffer_alpha_ps, nullptr, 0u);
			gpu.context->RSSetState(gpu.raster_none);

			gpu.context->DrawIndexedInstanced(index_count, instance_count, 0u, 0, 0u);

			gpu.context->VSSetShaderResources(terrain_height_slot, 3u, unbound);
		}
	}
}

//=====================================================================================
