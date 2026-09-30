
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	water_c water;

	bool water_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, 0u, D3D11_INPUT_PER_VERTEX_DATA, 0u }
		};

		std::vector<structures::vec2_s> grid;
		std::vector<std::uint32_t> indices;

		for (auto row{ 0u }; row < water_grid; row++)
		{
			for (auto column{ 0u }; column < water_grid; column++)
			{
				grid.push_back({ static_cast<std::float_t>(column) / static_cast<std::float_t>(water_grid - 1u) * 2.0f - 1.0f, static_cast<std::float_t>(row) / static_cast<std::float_t>(water_grid - 1u) * 2.0f - 1.0f });
			}
		}

		for (auto row{ 0u }; row + 1u < water_grid; row++)
		{
			for (auto column{ 0u }; column + 1u < water_grid; column++)
			{
				const auto a{ row * water_grid + column };
				const auto b{ a + 1u };
				const auto c{ a + water_grid };
				const auto d{ c + 1u };

				indices.insert(indices.end(), { a, c, b, b, c, d });
			}
		}

		index_count = static_cast<std::uint32_t>(indices.size());
		vertex_buffer = gpu.create_buffer(static_cast<std::uint32_t>(grid.size() * sizeof(structures::vec2_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, grid.data(), 0u, 0u);
		index_buffer = gpu.create_buffer(static_cast<std::uint32_t>(indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, indices.data(), 0u, 0u);
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::water_constants_s));
		vertex_shader = gpu.create_vertex_shader("water_vs", elements, 1u, &layout);
		pixel_shader = gpu.create_pixel_shader("water_ps");
		underwater_shader = gpu.create_pixel_shader("underwater_ps");
		normal_view = pak.create_texture("water_normal", 0u, false, false);

		for (auto wave{ 0u }; wave < 8u; wave++)
		{
			constants.waves[wave] = water_waves[wave];
		}

		constants.params = { water_steepness, water_extent, water_warp, water_snap };
		constants.shallow = water_shallow_tint;
		constants.deep = water_scatter;
		constants.absorption = { water_extinction.x, water_extinction.y, water_extinction.z, water_foam.x };

		return vertex_buffer && index_buffer && constant_buffer && vertex_shader && pixel_shader && underwater_shader && layout && normal_view;
	}
	/*
	//=====================================================================================
	*/
	void water_c::destroy()
	{
		gpu.destroy_target(scene_copy);

		functions::release(vertex_buffer);
		functions::release(index_buffer);
		functions::release(constant_buffer);
		functions::release(vertex_shader);
		functions::release(pixel_shader);
		functions::release(underwater_shader);
		functions::release(layout);
		functions::release(normal_view);
	}
	/*
	//=====================================================================================
	*/
	bool water_c::resize(std::uint32_t width, std::uint32_t height_pixels)
	{
		gpu.destroy_target(scene_copy);

		return gpu.create_target(scene_copy, width, height_pixels, DXGI_FORMAT_R16G16B16A16_FLOAT, structures::target_srv);
	}
	/*
	//=====================================================================================
	*/
	void water_c::render()
	{
		if (enabled && scene_copy.texture)
		{
			const auto stride{ static_cast<UINT>(sizeof(structures::vec2_s)) };
			const auto offset{ 0u };
			const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(renderer.width), static_cast<std::float_t>(renderer.height), 0.0f, 1.0f };

			ID3D11RenderTargetView* targets[2] = { renderer.hdr.rtv, renderer.gbuffer[4].rtv };
			ID3D11ShaderResourceView* resources[4] = { scene_copy.srv, renderer.depth.srv, normal_view, sky.prefiltered };
			ID3D11ShaderResourceView* unbound[4]{};
			ID3D11ShaderResourceView* height_view{ terrain.enabled ? terrain.height_view : nullptr };
			ID3D11SamplerState* samplers[2] = { gpu.sampler_linear_clamp, gpu.sampler_linear_wrap };

			constants.shallow.w = height;
			constants.terrain = { terrain.header.origin, terrain.header.world_size, static_cast<std::float_t>(terrain.header.resolution), terrain.enabled ? 1.0f : 0.0f };

			gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

			gpu.context->CopyResource(scene_copy.texture, renderer.hdr.texture);

			gpu.context->OMSetRenderTargets(2u, targets, renderer.depth.dsv_read_only);
			gpu.context->OMSetDepthStencilState(gpu.depth_read, 0u);
			gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);
			gpu.context->RSSetState(gpu.raster_none);
			gpu.context->RSSetViewports(1u, &viewport);
			gpu.context->IASetInputLayout(layout);
			gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
			gpu.context->IASetVertexBuffers(0u, 1u, &vertex_buffer, &stride, &offset);
			gpu.context->IASetIndexBuffer(index_buffer, DXGI_FORMAT_R32_UINT, 0u);
			gpu.context->VSSetShader(vertex_shader, nullptr, 0u);
			gpu.context->VSSetConstantBuffers(3u, 1u, &constant_buffer);
			gpu.context->VSSetShaderResources(terrain_height_slot, 1u, &height_view);
			gpu.context->VSSetSamplers(0u, 2u, samplers);
			gpu.context->PSSetShader(pixel_shader, nullptr, 0u);
			gpu.context->PSSetConstantBuffers(3u, 1u, &constant_buffer);
			gpu.context->PSSetShaderResources(0u, 4u, resources);
			gpu.context->PSSetSamplers(0u, 2u, samplers);

			gpu.context->DrawIndexed(index_count, 0u, 0);

			gpu.context->PSSetShaderResources(0u, 4u, unbound);
			gpu.context->VSSetShaderResources(terrain_height_slot, 1u, unbound);
			gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);
		}
	}
	/*
	//=====================================================================================
	*/
	void water_c::render_underwater()
	{
		if (enabled && scene_copy.texture && renderer.camera.position.y < level(renderer.camera.position.x, renderer.camera.position.z) + water_underwater_margin)
		{
			const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(renderer.width), static_cast<std::float_t>(renderer.height), 0.0f, 1.0f };

			ID3D11ShaderResourceView* resources[4] = { scene_copy.srv, renderer.depth.srv, normal_view, sky.prefiltered };
			ID3D11ShaderResourceView* unbound[4]{};
			ID3D11SamplerState* samplers[2] = { gpu.sampler_linear_clamp, gpu.sampler_linear_wrap };
			ID3D11ShaderResourceView* height_view{ terrain.enabled ? terrain.height_view : nullptr };

			gpu.context->CopyResource(scene_copy.texture, renderer.hdr.texture);

			gpu.context->OMSetRenderTargets(1u, &renderer.hdr.rtv, nullptr);
			gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);
			gpu.context->OMSetDepthStencilState(gpu.depth_none, 0u);
			gpu.context->RSSetState(gpu.raster_none);
			gpu.context->RSSetViewports(1u, &viewport);
			gpu.context->IASetInputLayout(nullptr);
			gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
			gpu.context->VSSetShader(renderer.fullscreen_vs, nullptr, 0u);
			gpu.context->PSSetShader(underwater_shader, nullptr, 0u);
			gpu.context->PSSetConstantBuffers(3u, 1u, &constant_buffer);
			gpu.context->PSSetShaderResources(0u, 4u, resources);
			gpu.context->PSSetShaderResources(terrain_height_slot, 1u, &height_view);
			gpu.context->PSSetSamplers(0u, 2u, samplers);

			gpu.context->Draw(3u, 0u);

			gpu.context->PSSetShaderResources(0u, 4u, unbound);
			gpu.context->PSSetShaderResources(terrain_height_slot, 1u, unbound);
			gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t water_c::level(std::float_t x, std::float_t z)
	{
		if (enabled)
		{
			const auto depth{ terrain.enabled ? std::max(height - terrain.height(x, z), 0.0f) : 40.0f };
			const auto calm{ water_calm_floor + (1.0f - water_calm_floor) * mathematics.saturate(depth / water_calm_depth) };

			auto offset{ 0.0f };

			for (const auto& wave : water_waves)
			{
				const auto length{ std::sqrt(wave.x * wave.x + wave.y * wave.y) };
				const auto k{ two_pi / wave.z };

				offset += wave.w * calm * std::sin(k * (wave.x * x + wave.y * z) / length - std::sqrt(9.81f * k) * renderer.time);
			}

			return height + offset;
		}

		return -100000.0f;
	}
	/*
	//=====================================================================================
	*/
	std::float_t water_c::still()
	{
		if (enabled)
		{
			return height;
		}

		return -100000.0f;
	}
}

//=====================================================================================
