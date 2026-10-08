
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	decals_c decals;

	bool decals_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, 0u, D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "INSTANCE", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::decal_gpu_s, center), D3D11_INPUT_PER_INSTANCE_DATA, 1u },
			{ "INSTANCE", 1u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::decal_gpu_s, normal), D3D11_INPUT_PER_INSTANCE_DATA, 1u },
			{ "INSTANCE", 2u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::decal_gpu_s, axis), D3D11_INPUT_PER_INSTANCE_DATA, 1u },
			{ "INSTANCE", 3u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::decal_gpu_s, tint), D3D11_INPUT_PER_INSTANCE_DATA, 1u }
		};

		const structures::vec3_s corners[8] = { { -1.0f, 1.0f, -1.0f }, { 1.0f, 1.0f, -1.0f }, { 1.0f, 1.0f, 1.0f }, { -1.0f, 1.0f, 1.0f }, { -1.0f, -1.0f, -1.0f }, { 1.0f, -1.0f, -1.0f }, { 1.0f, -1.0f, 1.0f }, { -1.0f, -1.0f, 1.0f } };
		const std::uint16_t faces[36] = { 3u, 1u, 0u, 2u, 1u, 3u, 0u, 5u, 4u, 1u, 5u, 0u, 3u, 4u, 7u, 0u, 4u, 3u, 1u, 6u, 5u, 2u, 6u, 1u, 2u, 7u, 6u, 3u, 7u, 2u, 6u, 4u, 5u, 7u, 4u, 6u };

		D3D11_BLEND_DESC blending{};

		blending.IndependentBlendEnable = TRUE;
		blending.RenderTarget[0].BlendEnable = TRUE;
		blending.RenderTarget[0].SrcBlend = D3D11_BLEND_SRC_ALPHA;
		blending.RenderTarget[0].DestBlend = D3D11_BLEND_INV_SRC_ALPHA;
		blending.RenderTarget[0].BlendOp = D3D11_BLEND_OP_ADD;
		blending.RenderTarget[0].SrcBlendAlpha = D3D11_BLEND_ZERO;
		blending.RenderTarget[0].DestBlendAlpha = D3D11_BLEND_ONE;
		blending.RenderTarget[0].BlendOpAlpha = D3D11_BLEND_OP_ADD;
		blending.RenderTarget[0].RenderTargetWriteMask = D3D11_COLOR_WRITE_ENABLE_ALL;
		blending.RenderTarget[1] = blending.RenderTarget[0];
		blending.RenderTarget[1].SrcBlendAlpha = D3D11_BLEND_BLEND_FACTOR;
		blending.RenderTarget[1].DestBlendAlpha = D3D11_BLEND_INV_SRC_ALPHA;

		D3D11_RASTERIZER_DESC rasterizer{};

		rasterizer.FillMode = D3D11_FILL_SOLID;
		rasterizer.CullMode = D3D11_CULL_FRONT;

		D3D11_SAMPLER_DESC sampling{};

		sampling.Filter = D3D11_FILTER_ANISOTROPIC;
		sampling.AddressU = D3D11_TEXTURE_ADDRESS_CLAMP;
		sampling.AddressV = D3D11_TEXTURE_ADDRESS_CLAMP;
		sampling.AddressW = D3D11_TEXTURE_ADDRESS_CLAMP;
		sampling.MaxAnisotropy = 8u;
		sampling.ComparisonFunc = D3D11_COMPARISON_NEVER;
		sampling.MaxLOD = 4.0f;

		vertex_shader = gpu.create_vertex_shader("decals_vs", elements, 5u, &layout);
		pixel_shader = gpu.create_pixel_shader("decals_ps");
		vertex_buffer = gpu.create_buffer(sizeof(corners), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, corners, 0u, 0u);
		index_buffer = gpu.create_buffer(sizeof(faces), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, faces, 0u, 0u);
		instance_buffer = gpu.create_buffer(maximum_decals * sizeof(structures::decal_gpu_s), D3D11_USAGE_DYNAMIC, D3D11_BIND_VERTEX_BUFFER, D3D11_CPU_ACCESS_WRITE, nullptr, 0u, 0u);
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::decal_constants_s));
		color_view = pak.create_texture("marks_color", 0u, false, false);
		shape_view = pak.create_texture("marks_shape", 0u, false, false);

		gpu.device->CreateBlendState(&blending, &blend);
		gpu.device->CreateRasterizerState(&rasterizer, &raster);
		gpu.device->CreateSamplerState(&sampling, &sampler);

		rough.reserve(maximum_decals);
		gloss.reserve(maximum_decals);

		ready = vertex_shader && pixel_shader && layout && vertex_buffer && index_buffer && instance_buffer && constant_buffer && color_view && shape_view && blend && raster && sampler;

		return ready;
	}
	/*
	//=====================================================================================
	*/
	void decals_c::destroy()
	{
		if (peak)
		{
			logger.write("decals: peak %u on screen", peak);
		}

		functions::release(sampler);
		functions::release(raster);
		functions::release(blend);
		functions::release(shape_view);
		functions::release(color_view);
		functions::release(constant_buffer);
		functions::release(instance_buffer);
		functions::release(index_buffer);
		functions::release(vertex_buffer);
		functions::release(layout);
		functions::release(pixel_shader);
		functions::release(vertex_shader);

		ready = false;
	}
	/*
	//=====================================================================================
	*/
	void decals_c::gather()
	{
		rough.clear();
		gloss.clear();

		for (const auto& stain : maps.stains)
		{
			const structures::vec3_s spot{ stain.decal.center.x, stain.decal.center.y, stain.decal.center.z };
			const auto distance{ mathematics.distance(spot, renderer.camera.position) };
			const auto reach{ stain.decal.center.w + stain.decal.normal.w };

			if (distance < street_mark_reach && rough.size() + gloss.size() < maximum_decals && mathematics.box_visible(renderer.view_planes, 6u, spot - structures::vec3_s{ reach, reach, reach }, spot + structures::vec3_s{ reach, reach, reach }))
			{
				auto instance{ stain.decal };

				instance.tint.w = mathematics.saturate((street_mark_reach - distance) / (street_mark_reach * decal_distance_fade));

				(stain.wet ? gloss : rough).push_back(instance);
			}
		}

		if (marks.count && marks.heads.size())
		{
			const auto clock{ marks.now() };
			const auto eye{ renderer.camera.position };
			const auto span{ static_cast<std::int32_t>(mark_cells) };
			const auto center{ static_cast<std::int32_t>(marks.cell_of(eye)) };
			const auto column{ center % span };
			const auto row{ center / span };

			for (auto z{ std::max(row - mark_interest, 0) }; z <= std::min(row + mark_interest, span - 1); z++)
			{
				for (auto x{ std::max(column - mark_interest, 0) }; x <= std::min(column + mark_interest, span - 1); x++)
				{
					for (auto index{ marks.heads[static_cast<std::size_t>(z) * mark_cells + static_cast<std::size_t>(x)] }; index >= 0 && rough.size() + gloss.size() < maximum_decals; index = marks.ring[index].next)
					{
						const auto& mark{ marks.ring[index] };
						const auto& definition{ mark_definitions[mark.kind] };
						const auto distance{ mathematics.distance(mark.position, eye) };
						const auto reach{ mark.size + definition.depth };

						if (distance < definition.reach && mathematics.box_visible(renderer.view_planes, 6u, mark.position - structures::vec3_s{ reach, reach, reach }, mark.position + structures::vec3_s{ reach, reach, reach }))
						{
							const auto age{ static_cast<std::float_t>(std::max(clock - mark.born, 0.0)) };
							const auto ending{ definition.life > 0.0f ? mathematics.saturate((definition.life - age) / std::max(definition.fade, 0.001f)) : 1.0f };
							const auto nearness{ mathematics.saturate((definition.reach - distance) / (definition.reach * decal_distance_fade)) };
							const auto dried{ definition.dry > 0.0f ? mathematics.saturate(age / definition.dry) : 0.0f };
							const auto grown{ definition.grow > 0.0f ? mathematics.lerp(0.3f, 1.0f, mathematics.smoothstep(0.0f, definition.grow, age)) : 1.0f };
							const auto tint{ mathematics.lerp(structures::vec3_s{ 1.0f, 1.0f, 1.0f }, mark_blood_dried, dried) };
							const structures::decal_gpu_s instance{ { mark.position.x, mark.position.y, mark.position.z, mark.size * grown }, { mark.normal.x, mark.normal.y, mark.normal.z, definition.depth }, { mark.axis.x, mark.axis.y, mark.axis.z, static_cast<std::float_t>(definition.cell + mark.variant) }, { tint.x, tint.y, tint.z, ending * nearness } };

							if (definition.wet && dried < 0.85f)
							{
								gloss.push_back(instance);
							}

							else
							{
								rough.push_back(instance);
							}
						}
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void decals_c::render()
	{
		if (ready)
		{
			gather();

			const auto dry{ static_cast<std::uint32_t>(rough.size()) };
			const auto wet{ static_cast<std::uint32_t>(gloss.size()) };

			drawn = dry + wet;
			peak = std::max(peak, drawn);

			if (drawn)
			{
				ID3D11RenderTargetView* targets[2] = { renderer.gbuffer[0].rtv, renderer.gbuffer[1].rtv };
				ID3D11ShaderResourceView* resources[4] = { renderer.depth.srv, renderer.gbuffer[2].srv, color_view, shape_view };
				ID3D11ShaderResourceView* unbound[4]{};
				ID3D11Buffer* streams[2] = { vertex_buffer, instance_buffer };

				const UINT strides[2] = { sizeof(structures::vec3_s), sizeof(structures::decal_gpu_s) };
				const UINT offsets[2] = { 0u, 0u };
				const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(renderer.width), static_cast<std::float_t>(renderer.height), 0.0f, 1.0f };

				rough.insert(rough.end(), gloss.begin(), gloss.end());

				gpu.update_buffer(instance_buffer, rough.data(), static_cast<std::uint32_t>(rough.size() * sizeof(structures::decal_gpu_s)));

				gpu.context->OMSetRenderTargets(2u, targets, nullptr);
				gpu.context->OMSetDepthStencilState(gpu.depth_none, 0u);
				gpu.context->RSSetState(raster);
				gpu.context->RSSetViewports(1u, &viewport);
				gpu.context->IASetInputLayout(layout);
				gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
				gpu.context->IASetVertexBuffers(0u, 2u, streams, strides, offsets);
				gpu.context->IASetIndexBuffer(index_buffer, DXGI_FORMAT_R16_UINT, 0u);
				gpu.context->VSSetShader(vertex_shader, nullptr, 0u);
				gpu.context->PSSetShader(pixel_shader, nullptr, 0u);
				gpu.context->PSSetShaderResources(0u, 4u, resources);
				gpu.context->PSSetSamplers(0u, 1u, &sampler);
				gpu.context->PSSetConstantBuffers(3u, 1u, &constant_buffer);

				for (auto pass{ 0u }; pass < 2u; pass++)
				{
					const auto amount{ pass ? wet : dry };
					const auto level{ pass ? decal_gloss : decal_rough };
					const std::float_t factor[4] = { level, level, level, level };
					const structures::decal_constants_s constants{ { pass ? 1.0f : 0.0f, 0.0f, 0.0f, 0.0f } };

					if (amount)
					{
						gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

						gpu.context->OMSetBlendState(blend, factor, 0xFFFFFFFFu);

						gpu.context->DrawIndexedInstanced(36u, amount, 0u, 0, pass ? dry : 0u);
					}
				}

				gpu.context->PSSetShaderResources(0u, 4u, unbound);
				gpu.context->PSSetSamplers(0u, 1u, &gpu.sampler_anisotropic_wrap);
				gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);
				gpu.context->RSSetState(gpu.raster_back);
				gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);
			}
		}
	}
}

//=====================================================================================
