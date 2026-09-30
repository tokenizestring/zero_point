
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	shadows_c shadows;

	bool shadows_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u }
		};

		const D3D11_INPUT_ELEMENT_DESC alpha_elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::vertex_s, uv), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "MATERIAL", 0u, DXGI_FORMAT_R32_UINT, 0u, offsetof(structures::vertex_s, material), D3D11_INPUT_PER_VERTEX_DATA, 0u }
		};

		const D3D11_INPUT_ELEMENT_DESC skinned_elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::skinned_vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "NORMAL", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::skinned_vertex_s, normal), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TANGENT", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 0u, offsetof(structures::skinned_vertex_s, tangent), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::skinned_vertex_s, uv), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "MATERIAL", 0u, DXGI_FORMAT_R32_UINT, 0u, offsetof(structures::skinned_vertex_s, material), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "BLENDINDICES", 0u, DXGI_FORMAT_R8G8B8A8_UINT, 0u, offsetof(structures::skinned_vertex_s, joints), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "BLENDWEIGHT", 0u, DXGI_FORMAT_R8G8B8A8_UNORM, 0u, offsetof(structures::skinned_vertex_s, weights), D3D11_INPUT_PER_VERTEX_DATA, 0u }
		};

		vertex_shader = gpu.create_vertex_shader("shadow_vs", elements, 1u, &layout);
		alpha_vertex_shader = gpu.create_vertex_shader("shadow_alpha_vs", alpha_elements, 3u, &alpha_layout);
		alpha_pixel_shader = gpu.create_pixel_shader("shadow_alpha_ps");
		skinned_vertex_shader = gpu.create_vertex_shader("shadow_skinned_vs", skinned_elements, 7u, &skinned_layout);

		constant_buffer = gpu.create_constant_buffer(sizeof(structures::shadow_constants_s));

		return vertex_shader && layout && alpha_vertex_shader && alpha_pixel_shader && alpha_layout && skinned_vertex_shader && skinned_layout && constant_buffer;
	}
	/*
	//=====================================================================================
	*/
	void shadows_c::destroy()
	{
		destroy_maps();

		functions::release(layout);
		functions::release(vertex_shader);
		functions::release(alpha_layout);
		functions::release(alpha_vertex_shader);
		functions::release(alpha_pixel_shader);
		functions::release(skinned_layout);
		functions::release(skinned_vertex_shader);
		functions::release(constant_buffer);
	}
	/*
	//=====================================================================================
	*/
	bool shadows_c::configure(std::uint32_t quality)
	{
		const std::uint32_t resolutions[structures::quality_count] = { 512u, 1024u, 2048u, 2048u, 4096u };
		const std::uint32_t cascade_counts[structures::quality_count] = { 1u, 2u, 3u, 4u, 4u };
		const std::float_t distances[structures::quality_count] = { 1.0f, 50.0f, 80.0f, 120.0f, 160.0f };

		const auto level{ std::min(quality, static_cast<std::uint32_t>(structures::quality_ultra)) };

		distance = distances[level];

		if (resolution != resolutions[level] || cascades != cascade_counts[level] || texture == nullptr)
		{
			destroy_maps();

			resolution = resolutions[level];
			cascades = cascade_counts[level];

			D3D11_TEXTURE2D_DESC description{};

			description.Width = resolution;
			description.Height = resolution;
			description.MipLevels = 1u;
			description.ArraySize = cascades;
			description.Format = DXGI_FORMAT_R32_TYPELESS;
			description.SampleDesc.Count = 1u;
			description.Usage = D3D11_USAGE_DEFAULT;
			description.BindFlags = D3D11_BIND_DEPTH_STENCIL | D3D11_BIND_SHADER_RESOURCE;

			if (SUCCEEDED(gpu.device->CreateTexture2D(&description, nullptr, &texture)))
			{
				for (auto cascade{ 0u }; cascade < cascades; cascade++)
				{
					D3D11_DEPTH_STENCIL_VIEW_DESC view{};

					view.Format = DXGI_FORMAT_D32_FLOAT;
					view.ViewDimension = D3D11_DSV_DIMENSION_TEXTURE2DARRAY;
					view.Texture2DArray.FirstArraySlice = cascade;
					view.Texture2DArray.ArraySize = 1u;

					gpu.device->CreateDepthStencilView(texture, &view, &views[cascade]);
				}

				D3D11_SHADER_RESOURCE_VIEW_DESC resource_view{};

				resource_view.Format = DXGI_FORMAT_R32_FLOAT;
				resource_view.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2DARRAY;
				resource_view.Texture2DArray.MipLevels = 1u;
				resource_view.Texture2DArray.ArraySize = cascades;

				gpu.device->CreateShaderResourceView(texture, &resource_view, &resource);

				logger.write("shadows: %u cascades at %u, distance %.0f m", cascades, resolution, distance);
			}
		}

		return resource != nullptr;
	}
	/*
	//=====================================================================================
	*/
	void shadows_c::destroy_maps()
	{
		for (auto& view : views)
		{
			functions::release(view);
		}

		functions::release(resource);
		functions::release(texture);
	}
	/*
	//=====================================================================================
	*/
	void shadows_c::update(const structures::camera_s& camera, structures::vec3_s sun)
	{
		const auto light_forward{ -mathematics.normalize(sun) };
		const auto light_up{ std::fabs(light_forward.y) > 0.99f ? structures::vec3_s{ 0.0f, 0.0f, 1.0f } : structures::vec3_s{ 0.0f, 1.0f, 0.0f } };
		const auto light_view{ mathematics.look_to({ 0.0f, 0.0f, 0.0f }, light_forward, light_up) };
		const auto light_right{ structures::vec3_s{ light_view.m[0][0], light_view.m[1][0], light_view.m[2][0] } };
		const auto light_true_up{ structures::vec3_s{ light_view.m[0][1], light_view.m[1][1], light_view.m[2][1] } };
		const auto tan_y{ std::tan(camera.vertical_fov * 0.5f) };
		const auto tan_x{ tan_y * camera.aspect };

		auto split_near{ camera_near };

		for (auto cascade{ 0u }; cascade < shadow_cascade_count; cascade++)
		{
			const auto used{ std::min(cascade, cascades - 1u) };
			const auto fraction{ static_cast<std::float_t>(used + 1u) / static_cast<std::float_t>(cascades) };
			const auto split_far{ mathematics.lerp(camera_near + (distance - camera_near) * fraction, camera_near * std::pow(distance / camera_near, fraction), 0.86f) };

			if (cascade < cascades)
			{
				structures::vec3_s corners[8]{};

				for (auto corner{ 0u }; corner < 8u; corner++)
				{
					const auto depth{ (corner & 4u) ? split_far : split_near };
					const auto sx{ (corner & 1u) ? 1.0f : -1.0f };
					const auto sy{ (corner & 2u) ? 1.0f : -1.0f };

					corners[corner] = camera.position + camera.forward * depth + camera.right * (sx * tan_x * depth) + camera.up * (sy * tan_y * depth);
				}

				structures::vec3_s center{};

				for (const auto& corner : corners)
				{
					center += corner * 0.125f;
				}

				auto radius{ 0.0f };

				for (const auto& corner : corners)
				{
					radius = std::max(radius, mathematics.distance(corner, center));
				}

				radius = std::ceil(radius * 16.0f) / 16.0f;

				const auto shrink{ std::min(1.0f, (cascade > 0u ? shadow_reduced_resolution : shadow_near_resolution) / static_cast<std::float_t>(resolution)) };
				const auto texel{ radius * 2.0f / (static_cast<std::float_t>(resolution) * shrink) };
				const auto light_space{ mathematics.transform_point(center, light_view) };
				const auto snapped_x{ std::floor(light_space.x / texel) * texel };
				const auto snapped_y{ std::floor(light_space.y / texel) * texel };
				const auto snapped{ light_right * snapped_x + light_true_up * snapped_y + light_forward * light_space.z };
				const auto eye{ snapped - light_forward * (shadow_depth_range * 0.5f) };
				const auto matrix{ mathematics.multiply(mathematics.look_to(eye, light_forward, light_up), mathematics.orthographic(-radius, radius, -radius, radius, 0.0f, shadow_depth_range)) };
				const structures::mat4_s region{ { { shrink, 0.0f, 0.0f, 0.0f }, { 0.0f, shrink, 0.0f, 0.0f }, { 0.0f, 0.0f, 1.0f, 0.0f }, { shrink - 1.0f, 1.0f - shrink, 0.0f, 1.0f } } };

				constants.cascade_matrices[cascade] = mathematics.multiply(matrix, region);

				extents[cascade] = static_cast<std::uint32_t>(std::ceil(static_cast<std::float_t>(resolution) * shrink));

				constants.cascade_texel[cascade] = texel;

				mathematics.frustum(matrix, planes[cascade]);

				split_near = split_far;
			}

			constants.cascade_splits[cascade] = split_far;
		}

		constants.params = { static_cast<std::float_t>(resolution), shadow_depth_range, static_cast<std::float_t>(cascades), 0.0f };
	}
	/*
	//=====================================================================================
	*/
	void shadows_c::begin_cascade(std::uint32_t cascade)
	{
		constants.params.w = static_cast<std::float_t>(cascade);

		gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

		const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(resolution), static_cast<std::float_t>(resolution), 0.0f, 1.0f };
		const D3D11_RECT scissor{ 0, 0, static_cast<LONG>(extents[cascade]), static_cast<LONG>(extents[cascade]) };

		gpu.context->OMSetRenderTargets(0u, nullptr, views[cascade]);
		gpu.context->ClearDepthStencilView(views[cascade], D3D11_CLEAR_DEPTH, 1.0f, 0u);
		gpu.context->RSSetViewports(1u, &viewport);
		gpu.context->RSSetScissorRects(1u, &scissor);
		gpu.context->VSSetConstantBuffers(2u, 1u, &constant_buffer);
	}
	/*
	//=====================================================================================
	*/
	void shadows_c::bind(std::uint32_t slot)
	{
		gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

		gpu.context->CSSetConstantBuffers(slot, 1u, &constant_buffer);
	}
}

//=====================================================================================
