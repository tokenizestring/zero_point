
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	clouds_c clouds;

	bool clouds_c::create()
	{
		shape_cs = gpu.create_compute_shader("clouds_shape_cs");
		detail_cs = gpu.create_compute_shader("clouds_detail_cs");
		weather_cs = gpu.create_compute_shader("clouds_weather_cs");
		march_cs = gpu.create_compute_shader("clouds_march_cs");
		resolve_cs = gpu.create_compute_shader("clouds_resolve_cs");
		shadow_cs = gpu.create_compute_shader("clouds_shadow_cs");
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::cloud_constants_s));

		if (shape_cs && detail_cs && weather_cs && march_cs && resolve_cs && constant_buffer && gpu.create_target(weather_map, cloud_weather_size, cloud_weather_size, DXGI_FORMAT_R8G8B8A8_UNORM, structures::target_srv | structures::target_uav))
		{
			generate();
		}

		ready = shape_view && detail_view && weather_map.srv && march_cs && resolve_cs && shadow_cs && constant_buffer && gpu.create_target(shadow_map, cloud_shadow_size, cloud_shadow_size, DXGI_FORMAT_R16_FLOAT, structures::target_srv | structures::target_uav);

		logger.write("clouds: %s", ready ? "ready" : "unavailable");

		return ready;
	}
	/*
	//=====================================================================================
	*/
	void clouds_c::destroy()
	{
		gpu.destroy_target(march);
		gpu.destroy_target(history[0]);
		gpu.destroy_target(history[1]);
		gpu.destroy_target(weather_map);
		gpu.destroy_target(shadow_map);

		functions::release(shape_view);
		functions::release(detail_view);
		functions::release(shape_cs);
		functions::release(detail_cs);
		functions::release(weather_cs);
		functions::release(march_cs);
		functions::release(resolve_cs);
		functions::release(shadow_cs);
		functions::release(constant_buffer);

		ready = false;
		active = false;
		valid = false;
	}
	/*
	//=====================================================================================
	*/
	bool clouds_c::resize(std::uint32_t full_width, std::uint32_t full_height)
	{
		width = std::max(1u, (full_width + 1u) / 2u);
		height = std::max(1u, (full_height + 1u) / 2u);
		valid = false;

		return gpu.create_target(march, width, height, DXGI_FORMAT_R16G16B16A16_FLOAT, structures::target_srv | structures::target_uav) && gpu.create_target(history[0], width, height, DXGI_FORMAT_R16G16B16A16_FLOAT, structures::target_srv | structures::target_uav) && gpu.create_target(history[1], width, height, DXGI_FORMAT_R16G16B16A16_FLOAT, structures::target_srv | structures::target_uav);
	}
	/*
	//=====================================================================================
	*/
	ID3D11ShaderResourceView* clouds_c::volume(ID3D11ComputeShader* shader, std::uint32_t size)
	{
		D3D11_TEXTURE3D_DESC description{};

		description.Width = size;
		description.Height = size;
		description.Depth = size;
		description.MipLevels = 1u;
		description.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
		description.Usage = D3D11_USAGE_DEFAULT;
		description.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_UNORDERED_ACCESS;

		ID3D11Texture3D* texture{ nullptr };
		ID3D11ShaderResourceView* result{ nullptr };

		if (SUCCEEDED(gpu.device->CreateTexture3D(&description, nullptr, &texture)))
		{
			ID3D11UnorderedAccessView* access{ nullptr };
			ID3D11UnorderedAccessView* unbound{ nullptr };

			gpu.device->CreateShaderResourceView(texture, nullptr, &result);
			gpu.device->CreateUnorderedAccessView(texture, nullptr, &access);

			values.target = { static_cast<std::float_t>(size), 0.0f, 0.0f, 0.0f };

			gpu.update_buffer(constant_buffer, &values, sizeof(values));

			gpu.context->CSSetConstantBuffers(5u, 1u, &constant_buffer);
			gpu.context->CSSetUnorderedAccessViews(0u, 1u, &access, nullptr);
			gpu.context->CSSetShader(shader, nullptr, 0u);

			gpu.context->Dispatch(size / cloud_noise_group, size / cloud_noise_group, size / cloud_noise_group);

			gpu.context->CSSetUnorderedAccessViews(0u, 1u, &unbound, nullptr);

			functions::release(access);
			functions::release(texture);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void clouds_c::generate()
	{
		ID3D11UnorderedAccessView* unbound{ nullptr };

		shape_view = volume(shape_cs, cloud_shape_size);
		detail_view = volume(detail_cs, cloud_detail_size);

		values.target = { static_cast<std::float_t>(cloud_weather_size), 0.0f, 0.0f, 0.0f };

		gpu.update_buffer(constant_buffer, &values, sizeof(values));

		gpu.context->CSSetConstantBuffers(5u, 1u, &constant_buffer);
		gpu.context->CSSetUnorderedAccessViews(1u, 1u, &weather_map.uav, nullptr);
		gpu.context->CSSetShader(weather_cs, nullptr, 0u);

		gpu.context->Dispatch(cloud_weather_size / compute_group_size, cloud_weather_size / compute_group_size, 1u);

		gpu.context->CSSetUnorderedAccessViews(1u, 1u, &unbound, nullptr);
	}
	/*
	//=====================================================================================
	*/
	ID3D11ShaderResourceView* clouds_c::compute(std::uint32_t quality, std::uint64_t frame)
	{
		const auto storm{ weather.storm_now };
		const auto coverage{ atmosphere_coverage + weather.cloud_now * (1.0f - atmosphere_coverage) };
		const auto texel{ cloud_shadow_extent / static_cast<std::float_t>(cloud_shadow_size) };

		ID3D11ShaderResourceView* result{ nullptr };

		active = ready && quality > 0u && atmosphere.enabled && march.uav && history[0].uav && history[1].uav;

		values.layer = { mathematics.lerp(cloud_bottom, cloud_storm_bottom, storm), cloud_top, mathematics.lerp(-0.75f, 0.45f, coverage), cloud_extinction * (1.0f + storm * 0.6f) };
		values.wind = { atmosphere.drift * cloud_wind_x, atmosphere.drift * cloud_wind_z, atmosphere.drift * cloud_evolve, atmosphere.drift * cloud_evolve * 2.6f };
		values.shade = { cloud_shadow_floor, cloud_light * (1.0f - storm * 0.55f), cloud_ambient * (1.0f - storm * 0.35f), 0.0f };
		values.target = { static_cast<std::float_t>(width), static_cast<std::float_t>(height), 1.0f / static_cast<std::float_t>(std::max(width, 1u)), 1.0f / static_cast<std::float_t>(std::max(height, 1u)) };
		values.state = { active ? 1.0f : 0.0f, valid ? 1.0f : 0.0f, static_cast<std::float_t>(frame % 1024u), cloud_steps[std::min(quality, 4u)] };
		values.area = { std::floor((renderer.camera.position.x - cloud_shadow_extent * 0.5f) / texel) * texel, std::floor((renderer.camera.position.z - cloud_shadow_extent * 0.5f) / texel) * texel, cloud_shadow_extent, texel };

		gpu.update_buffer(constant_buffer, &values, sizeof(values));

		if (active)
		{
			const auto current{ latest ^ 1u };

			ID3D11ShaderResourceView* inputs[5] = { shape_view, detail_view, weather_map.srv, nullptr, nullptr };
			ID3D11ShaderResourceView* unbound[5]{};
			ID3D11SamplerState* samplers[2] = { gpu.sampler_linear_wrap, gpu.sampler_linear_clamp };
			ID3D11UnorderedAccessView* none{ nullptr };

			gpu.context->CSSetConstantBuffers(5u, 1u, &constant_buffer);
			gpu.context->CSSetSamplers(0u, 2u, samplers);
			gpu.context->CSSetShaderResources(1u, 5u, inputs);
			gpu.context->CSSetUnorderedAccessViews(2u, 1u, &march.uav, nullptr);
			gpu.context->CSSetShader(march_cs, nullptr, 0u);

			gpu.context->Dispatch((width + compute_group_size - 1u) / compute_group_size, (height + compute_group_size - 1u) / compute_group_size, 1u);

			gpu.context->CSSetUnorderedAccessViews(2u, 1u, &none, nullptr);

			inputs[3] = march.srv;
			inputs[4] = history[latest].srv;

			gpu.context->CSSetShaderResources(1u, 5u, inputs);
			gpu.context->CSSetUnorderedAccessViews(2u, 1u, &history[current].uav, nullptr);
			gpu.context->CSSetShader(resolve_cs, nullptr, 0u);

			gpu.context->Dispatch((width + compute_group_size - 1u) / compute_group_size, (height + compute_group_size - 1u) / compute_group_size, 1u);

			gpu.context->CSSetUnorderedAccessViews(2u, 1u, &none, nullptr);
			gpu.context->CSSetUnorderedAccessViews(3u, 1u, &shadow_map.uav, nullptr);
			gpu.context->CSSetShader(shadow_cs, nullptr, 0u);

			gpu.context->Dispatch(cloud_shadow_size / compute_group_size, cloud_shadow_size / compute_group_size, 1u);

			gpu.context->CSSetUnorderedAccessViews(3u, 1u, &none, nullptr);
			gpu.context->CSSetShaderResources(1u, 5u, unbound);

			latest = current;
			valid = true;
			result = history[current].srv;
		}

		else
		{
			valid = false;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void clouds_c::bind()
	{
		gpu.context->CSSetConstantBuffers(5u, 1u, &constant_buffer);
	}
}

//=====================================================================================
