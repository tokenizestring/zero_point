
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	ssao_c ssao;

	bool ssao_c::create()
	{
		ssao_cs = gpu.create_compute_shader("ssao_cs");
		blur_cs = gpu.create_compute_shader("ssao_blur_cs");
		constants = gpu.create_constant_buffer(sizeof(structures::double_constants_s));

		return ssao_cs && blur_cs && constants;
	}
	/*
	//=====================================================================================
	*/
	void ssao_c::destroy()
	{
		gpu.destroy_target(raw);
		gpu.destroy_target(blurred);

		functions::release(ssao_cs);
		functions::release(blur_cs);
		functions::release(constants);
	}
	/*
	//=====================================================================================
	*/
	bool ssao_c::resize(std::uint32_t full_width, std::uint32_t full_height)
	{
		width = std::max(1u, full_width / 2u);
		height = std::max(1u, full_height / 2u);

		return gpu.create_target(raw, width, height, DXGI_FORMAT_R8_UNORM, structures::target_srv | structures::target_uav) && gpu.create_target(blurred, width, height, DXGI_FORMAT_R8_UNORM, structures::target_srv | structures::target_uav);
	}
	/*
	//=====================================================================================
	*/
	ID3D11ShaderResourceView* ssao_c::compute(ID3D11ShaderResourceView* depth_view, ID3D11ShaderResourceView* normal_view, std::uint32_t quality)
	{
		ID3D11ShaderResourceView* result{ nullptr };

		if (quality > 0u && raw.uav)
		{
			const std::float_t slices[structures::quality_count] = { 0.0f, 2.0f, 2.0f, 3.0f, 4.0f };
			const std::float_t steps[structures::quality_count] = { 0.0f, 3.0f, 4.0f, 5.0f, 6.0f };
			const auto level{ std::min(quality, static_cast<std::uint32_t>(structures::quality_ultra)) };

			ID3D11ShaderResourceView* inputs[2] = { depth_view, normal_view };

			gpu.context->CSSetShaderResources(0u, 2u, inputs);

			pass(ssao_cs, nullptr, raw.uav, { 1.0f, slices[level], steps[level], 1.35f });
			pass(blur_cs, raw.srv, blurred.uav, { 0.0f, 0.0f, 0.0f, 0.0f });
			pass(blur_cs, blurred.srv, raw.uav, { 0.0f, 1.0f, 0.0f, 0.0f });

			ID3D11ShaderResourceView* unbound[3]{};

			gpu.context->CSSetShaderResources(0u, 3u, unbound);

			result = raw.srv;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void ssao_c::pass(ID3D11ComputeShader* shader, ID3D11ShaderResourceView* source, ID3D11UnorderedAccessView* target, structures::vec4_s params)
	{
		const structures::double_constants_s values{ params, { static_cast<std::float_t>(width), static_cast<std::float_t>(height), 1.0f / static_cast<std::float_t>(width), 1.0f / static_cast<std::float_t>(height) } };

		ID3D11UnorderedAccessView* none{ nullptr };

		gpu.update_buffer(constants, &values, sizeof(values));

		gpu.context->CSSetConstantBuffers(8u, 1u, &constants);
		gpu.context->CSSetShaderResources(2u, 1u, &source);
		gpu.context->CSSetUnorderedAccessViews(0u, 1u, &target, nullptr);
		gpu.context->CSSetShader(shader, nullptr, 0u);

		gpu.context->Dispatch((width + compute_group_size - 1u) / compute_group_size, (height + compute_group_size - 1u) / compute_group_size, 1u);

		gpu.context->CSSetUnorderedAccessViews(0u, 1u, &none, nullptr);
	}
}

//=====================================================================================
