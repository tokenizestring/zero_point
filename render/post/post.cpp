
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	post_c post_process;

	bool post_c::create()
	{
		taa_cs = gpu.create_compute_shader("taa_cs");
		histogram_cs = gpu.create_compute_shader("histogram_cs");
		average_cs = gpu.create_compute_shader("exposure_cs");
		bloom_down_ps = gpu.create_pixel_shader("bloom_down_ps");
		bloom_up_ps = gpu.create_pixel_shader("bloom_up_ps");
		shaft_mask_ps = gpu.create_pixel_shader("shaft_mask_ps");
		shaft_blur_ps = gpu.create_pixel_shader("shaft_blur_ps");
		shaft_apply_ps = gpu.create_pixel_shader("shaft_apply_ps");

		taa_buffer = gpu.create_constant_buffer(sizeof(structures::single_constants_s));
		exposure_constants = gpu.create_constant_buffer(sizeof(structures::exposure_constants_s));
		bloom_buffer = gpu.create_constant_buffer(sizeof(structures::single_constants_s));
		shaft_buffer = gpu.create_constant_buffer(sizeof(structures::shaft_constants_s));

		const std::uint32_t zeros[histogram_bins]{};

		histogram_buffer = gpu.create_buffer(sizeof(zeros), D3D11_USAGE_DEFAULT, D3D11_BIND_UNORDERED_ACCESS, 0u, zeros, D3D11_RESOURCE_MISC_BUFFER_ALLOW_RAW_VIEWS, 0u);

		if (histogram_buffer)
		{
			D3D11_UNORDERED_ACCESS_VIEW_DESC access{};

			access.Format = DXGI_FORMAT_R32_TYPELESS;
			access.ViewDimension = D3D11_UAV_DIMENSION_BUFFER;
			access.Buffer.NumElements = histogram_bins;
			access.Buffer.Flags = D3D11_BUFFER_UAV_FLAG_RAW;

			gpu.device->CreateUnorderedAccessView(histogram_buffer, &access, &histogram_uav);
		}

		const structures::vec4_s initial{ 0.0f, 1.0f, 0.0f, 0.0f };

		exposure_buffer = gpu.create_buffer(sizeof(initial), D3D11_USAGE_DEFAULT, D3D11_BIND_UNORDERED_ACCESS | D3D11_BIND_SHADER_RESOURCE, 0u, &initial, D3D11_RESOURCE_MISC_BUFFER_STRUCTURED, sizeof(initial));

		if (exposure_buffer)
		{
			gpu.device->CreateUnorderedAccessView(exposure_buffer, nullptr, &exposure_uav);
			gpu.device->CreateShaderResourceView(exposure_buffer, nullptr, &exposure_srv);
		}

		return taa_cs && histogram_cs && average_cs && bloom_down_ps && bloom_up_ps && shaft_mask_ps && shaft_blur_ps && shaft_apply_ps && shaft_buffer && histogram_uav && exposure_uav && exposure_srv;
	}
	/*
	//=====================================================================================
	*/
	void post_c::destroy()
	{
		destroy_targets();

		functions::release(histogram_uav);
		functions::release(histogram_buffer);
		functions::release(exposure_srv);
		functions::release(exposure_uav);
		functions::release(exposure_buffer);
		functions::release(taa_cs);
		functions::release(histogram_cs);
		functions::release(average_cs);
		functions::release(bloom_down_ps);
		functions::release(bloom_up_ps);
		functions::release(shaft_mask_ps);
		functions::release(shaft_blur_ps);
		functions::release(shaft_apply_ps);
		functions::release(taa_buffer);
		functions::release(exposure_constants);
		functions::release(bloom_buffer);
		functions::release(shaft_buffer);
	}
	/*
	//=====================================================================================
	*/
	bool post_c::resize(std::uint32_t new_width, std::uint32_t new_height)
	{
		destroy_targets();

		width = new_width;
		height = new_height;

		auto result{ gpu.create_target(history[0], width, height, DXGI_FORMAT_R16G16B16A16_FLOAT, structures::target_srv | structures::target_uav) && gpu.create_target(history[1], width, height, DXGI_FORMAT_R16G16B16A16_FLOAT, structures::target_srv | structures::target_uav) };

		for (auto level{ 0u }; level < bloom_levels; level++)
		{
			result = gpu.create_target(bloom[level], std::max(1u, width >> (level + 1u)), std::max(1u, height >> (level + 1u)), DXGI_FORMAT_R11G11B10_FLOAT, structures::target_rtv | structures::target_srv) && result;
		}

		for (auto& target : shafts)
		{
			result = gpu.create_target(target, std::max(1u, width / 4u), std::max(1u, height / 4u), DXGI_FORMAT_R11G11B10_FLOAT, structures::target_rtv | structures::target_srv) && result;
		}

		history_valid = false;

		return result;
	}
	/*
	//=====================================================================================
	*/
	void post_c::destroy_targets()
	{
		for (auto& target : history)
		{
			gpu.destroy_target(target);
		}

		for (auto& target : bloom)
		{
			gpu.destroy_target(target);
		}

		for (auto& target : shafts)
		{
			gpu.destroy_target(target);
		}
	}
	/*
	//=====================================================================================
	*/
	ID3D11ShaderResourceView* post_c::resolve(ID3D11ShaderResourceView* current, ID3D11ShaderResourceView* motion, ID3D11ShaderResourceView* depth_view, bool enabled)
	{
		auto result{ current };

		if (enabled && history[0].uav)
		{
			history_index ^= 1u;

			const structures::single_constants_s constants{ { 0.08f, history_valid ? 1.0f : 0.0f, 0.0f, 0.0f } };

			gpu.update_buffer(taa_buffer, &constants, sizeof(constants));

			ID3D11ShaderResourceView* resources[4] = { current, history[history_index ^ 1u].srv, motion, depth_view };
			ID3D11ShaderResourceView* unbound[4]{};
			ID3D11UnorderedAccessView* none{ nullptr };

			gpu.context->CSSetShader(taa_cs, nullptr, 0u);
			gpu.context->CSSetConstantBuffers(6u, 1u, &taa_buffer);
			gpu.context->CSSetShaderResources(0u, 4u, resources);
			gpu.context->CSSetSamplers(0u, 1u, &gpu.sampler_linear_clamp);
			gpu.context->CSSetUnorderedAccessViews(0u, 1u, &history[history_index].uav, nullptr);

			gpu.context->Dispatch((width + compute_group_size - 1u) / compute_group_size, (height + compute_group_size - 1u) / compute_group_size, 1u);

			gpu.context->CSSetUnorderedAccessViews(0u, 1u, &none, nullptr);
			gpu.context->CSSetShaderResources(0u, 4u, unbound);

			history_valid = true;

			result = history[history_index].srv;
		}

		else
		{
			history_valid = false;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void post_c::expose(ID3D11ShaderResourceView* scene, std::float_t delta)
	{
		const structures::exposure_constants_s constants{ { static_cast<std::float_t>(width), static_cast<std::float_t>(height), exposure_key, compensation }, { exposure_minimum_log, delta, 1.0f / exposure_log_range, 0.0f }, { exposure_lowest, exposure_highest, 0.5f, 0.97f } };

		gpu.update_buffer(exposure_constants, &constants, sizeof(constants));

		ID3D11UnorderedAccessView* views[2] = { histogram_uav, exposure_uav };
		ID3D11UnorderedAccessView* none[2]{};
		ID3D11ShaderResourceView* unbound{ nullptr };

		gpu.context->CSSetConstantBuffers(5u, 1u, &exposure_constants);
		gpu.context->CSSetShaderResources(0u, 1u, &scene);
		gpu.context->CSSetUnorderedAccessViews(0u, 2u, views, nullptr);

		gpu.context->CSSetShader(histogram_cs, nullptr, 0u);
		gpu.context->Dispatch((width + 15u) / 16u, (height + 15u) / 16u, 1u);

		gpu.context->CSSetShader(average_cs, nullptr, 0u);
		gpu.context->Dispatch(1u, 1u, 1u);

		gpu.context->CSSetUnorderedAccessViews(0u, 2u, none, nullptr);
		gpu.context->CSSetShaderResources(0u, 1u, &unbound);
	}
	/*
	//=====================================================================================
	*/
	ID3D11ShaderResourceView* post_c::bloom_chain(ID3D11ShaderResourceView* scene, ID3D11VertexShader* fullscreen)
	{
		gpu.context->IASetInputLayout(nullptr);
		gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
		gpu.context->VSSetShader(fullscreen, nullptr, 0u);
		gpu.context->RSSetState(gpu.raster_none);
		gpu.context->OMSetDepthStencilState(gpu.depth_none, 0u);
		gpu.context->PSSetSamplers(0u, 1u, &gpu.sampler_linear_clamp);
		gpu.context->PSSetConstantBuffers(7u, 1u, &bloom_buffer);

		for (auto level{ 0u }; level < bloom_levels; level++)
		{
			const auto source_width{ level ? bloom[level - 1u].width : width };
			const auto source_height{ level ? bloom[level - 1u].height : height };
			const structures::single_constants_s constants{ { 1.0f / static_cast<std::float_t>(source_width), 1.0f / static_cast<std::float_t>(source_height), level ? 0.0f : 1.0f, 1.0f } };

			gpu.update_buffer(bloom_buffer, &constants, sizeof(constants));

			fullscreen_pass(bloom[level].rtv, bloom[level].width, bloom[level].height, level ? bloom[level - 1u].srv : scene, bloom_down_ps, gpu.blend_opaque);
		}

		for (auto level{ bloom_levels - 1u }; level > 0u; level--)
		{
			const structures::single_constants_s constants{ { 1.0f / static_cast<std::float_t>(bloom[level].width), 1.0f / static_cast<std::float_t>(bloom[level].height), 0.0f, bloom_upsample_weight } };

			gpu.update_buffer(bloom_buffer, &constants, sizeof(constants));

			fullscreen_pass(bloom[level - 1u].rtv, bloom[level - 1u].width, bloom[level - 1u].height, bloom[level].srv, bloom_up_ps, gpu.blend_additive);
		}

		return bloom[0].srv;
	}
	/*
	//=====================================================================================
	*/
	void post_c::light_shafts(ID3D11RenderTargetView* scene, ID3D11ShaderResourceView* depth_view, ID3D11VertexShader* fullscreen, structures::vec2_s sun, std::float_t strength)
	{
		const structures::shaft_constants_s constants{ { sun.x, sun.y, strength, 0.0f }, { shaft_decay, shaft_reach, 0.0f, shaft_focus } };

		ID3D11ShaderResourceView* unbound{ nullptr };

		gpu.update_buffer(shaft_buffer, &constants, sizeof(constants));

		gpu.context->IASetInputLayout(nullptr);
		gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
		gpu.context->VSSetShader(fullscreen, nullptr, 0u);
		gpu.context->RSSetState(gpu.raster_none);
		gpu.context->OMSetDepthStencilState(gpu.depth_none, 0u);
		gpu.context->PSSetSamplers(0u, 1u, &gpu.sampler_linear_clamp);
		gpu.context->PSSetConstantBuffers(7u, 1u, &shaft_buffer);
		gpu.context->PSSetShaderResources(1u, 1u, &depth_view);

		fullscreen_pass(shafts[0].rtv, shafts[0].width, shafts[0].height, nullptr, shaft_mask_ps, gpu.blend_opaque);

		gpu.context->PSSetShaderResources(1u, 1u, &unbound);

		fullscreen_pass(shafts[1].rtv, shafts[1].width, shafts[1].height, shafts[0].srv, shaft_blur_ps, gpu.blend_opaque);
		fullscreen_pass(scene, width, height, shafts[1].srv, shaft_apply_ps, gpu.blend_additive);
	}
	/*
	//=====================================================================================
	*/
	void post_c::fullscreen_pass(ID3D11RenderTargetView* target, std::uint32_t target_width, std::uint32_t target_height, ID3D11ShaderResourceView* source, ID3D11PixelShader* shader, ID3D11BlendState* blend)
	{
		const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(target_width), static_cast<std::float_t>(target_height), 0.0f, 1.0f };

		ID3D11ShaderResourceView* unbound{ nullptr };

		gpu.context->OMSetRenderTargets(1u, &target, nullptr);
		gpu.context->OMSetBlendState(blend, nullptr, 0xFFFFFFFFu);
		gpu.context->RSSetViewports(1u, &viewport);
		gpu.context->PSSetShader(shader, nullptr, 0u);
		gpu.context->PSSetShaderResources(0u, 1u, &source);

		gpu.context->Draw(3u, 0u);

		gpu.context->PSSetShaderResources(0u, 1u, &unbound);
		gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);
	}
}

//=====================================================================================
