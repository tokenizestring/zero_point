
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	atmosphere_c atmosphere;

	bool atmosphere_c::create()
	{
		D3D11_TEXTURE2D_DESC description{};

		description.Width = atmosphere_width;
		description.Height = atmosphere_height;
		description.MipLevels = 0u;
		description.ArraySize = 1u;
		description.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
		description.SampleDesc.Count = 1u;
		description.Usage = D3D11_USAGE_DEFAULT;
		description.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_UNORDERED_ACCESS | D3D11_BIND_RENDER_TARGET;
		description.MiscFlags = D3D11_RESOURCE_MISC_GENERATE_MIPS;

		if (SUCCEEDED(gpu.device->CreateTexture2D(&description, nullptr, &texture)))
		{
			D3D11_UNORDERED_ACCESS_VIEW_DESC output{};

			output.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
			output.ViewDimension = D3D11_UAV_DIMENSION_TEXTURE2D;

			gpu.device->CreateShaderResourceView(texture, nullptr, &view);
			gpu.device->CreateUnorderedAccessView(texture, &output, &access);
		}

		description.MipLevels = 1u;
		description.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_UNORDERED_ACCESS;
		description.MiscFlags = 0u;

		if (SUCCEEDED(gpu.device->CreateTexture2D(&description, nullptr, &clear_texture)))
		{
			gpu.device->CreateShaderResourceView(clear_texture, nullptr, &clear_view);
			gpu.device->CreateUnorderedAccessView(clear_texture, nullptr, &clear_access);
		}

		sky_shader = gpu.create_compute_shader("atmosphere_cs");
		sh_shader = gpu.create_compute_shader("atmosphere_sh_cs");
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::atmosphere_constants_s));
		sh_buffer = gpu.create_buffer(sky_sh_coefficients * sizeof(structures::vec4_s), D3D11_USAGE_DEFAULT, D3D11_BIND_UNORDERED_ACCESS, 0u, nullptr, D3D11_RESOURCE_MISC_BUFFER_STRUCTURED, sizeof(structures::vec4_s));
		sh_staging = gpu.create_buffer(sky_sh_coefficients * sizeof(structures::vec4_s), D3D11_USAGE_STAGING, 0u, D3D11_CPU_ACCESS_READ, nullptr, D3D11_RESOURCE_MISC_BUFFER_STRUCTURED, sizeof(structures::vec4_s));

		if (sh_buffer)
		{
			D3D11_UNORDERED_ACCESS_VIEW_DESC output{};

			output.Format = DXGI_FORMAT_UNKNOWN;
			output.ViewDimension = D3D11_UAV_DIMENSION_BUFFER;
			output.Buffer.NumElements = sky_sh_coefficients;

			gpu.device->CreateUnorderedAccessView(sh_buffer, &output, &sh_access);
		}

		logger.write("atmosphere: %s", view && access && sky_shader && sh_shader && sh_access && sh_staging ? "ready" : "unavailable");

		return view && access && sky_shader && sh_shader && constant_buffer && sh_access && sh_staging;
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::destroy()
	{
		functions::release(access);
		functions::release(view);
		functions::release(texture);
		functions::release(clear_access);
		functions::release(clear_view);
		functions::release(clear_texture);
		functions::release(sky_shader);
		functions::release(sh_shader);
		functions::release(constant_buffer);
		functions::release(sh_access);
		functions::release(sh_buffer);
		functions::release(sh_staging);

		enabled = false;
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::enable(std::float_t start_hours)
	{
		if (view && sky_shader && sh_shader)
		{
			hours = std::fmod(std::max(start_hours, 0.0f), 24.0f);
			enabled = true;

			view->AddRef();

			functions::release(sky.equirect);

			sky.equirect = view;
			sky.current = -1;
			sky.rotation = 0.0f;
			sky.intensity = 1.0f;

			place_bodies();

			begin_refresh();

			while (updating)
			{
				render_strip();
			}

			read_sh(true);

			logger.write("atmosphere: enabled at %.2f h, sun %.2f %.2f %.2f, light %.2f %.2f %.2f", hours, sun.x, sun.y, sun.z, sky.sun_color.x, sky.sun_color.y, sky.sun_color.z);
		}
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::update(std::float_t delta)
	{
		if (enabled)
		{
			hours = advance(hours, delta);
			drift += delta;
			refresh -= delta;

			place_bodies();

			if (updating)
			{
				render_strip();
			}

			else if (refresh <= 0.0f)
			{
				begin_refresh();
			}

			if (sh_pending)
			{
				read_sh(false);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t atmosphere_c::advance(std::float_t current, std::float_t delta)
	{
		const auto daytime{ current >= sunrise_hours && current < sunset_hours };
		const auto span{ sunset_hours - sunrise_hours };

		return std::fmod(current + delta * (daytime ? span / day_length : (24.0f - span) / night_length), 24.0f);
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::place_bodies()
	{
		const auto angle{ (hours - 6.0f) / 24.0f * two_pi };
		const auto moon_angle{ angle + pi + 0.4f };
		const auto origin{ structures::vec3_s{ 0.0f, atmosphere_planet + 250.0f, 0.0f } };

		sun = mathematics.normalize({ std::cos(angle), std::sin(angle) * std::cos(sun_tilt), -std::sin(angle) * std::sin(sun_tilt) });
		moon = mathematics.normalize({ std::cos(moon_angle), std::sin(moon_angle) * std::cos(moon_tilt), -std::sin(moon_angle) * std::sin(moon_tilt) });

		const auto day{ mathematics.smoothstep(-0.04f, 0.06f, sun.y) };
		const auto night{ mathematics.smoothstep(-0.02f, -0.12f, sun.y) * mathematics.smoothstep(0.0f, 0.12f, moon.y) };

		if (day > 0.0f || night <= 0.0f)
		{
			const auto depth{ extinction(light_depth(origin, sun)) };

			sky.sun_direction = sun;
			sky.sun_color = structures::vec3_s{ std::exp(-depth.x), std::exp(-depth.y), std::exp(-depth.z) } * (sun_irradiance * day);
			sky.sun_radius = 0.00465f;
		}

		else
		{
			const auto depth{ extinction(light_depth(origin, moon)) };

			sky.sun_direction = moon;
			sky.sun_color = structures::vec3_s{ std::exp(-depth.x) * moon_tint.x, std::exp(-depth.y) * moon_tint.y, std::exp(-depth.z) * moon_tint.z } * (moon_irradiance * night);
			sky.sun_radius = 0.0045f;
		}

		sky.sun_intensity = 1.0f;
		sky.stars = mathematics.smoothstep(-0.06f, -0.2f, sun.y);
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::begin_refresh()
	{
		const auto moon_active{ sun.y < 0.05f && moon.y > -0.1f };
		const auto zenith{ scatter({ 0.0f, 1.0f, 0.0f }, sun, sun_irradiance) + (moon_active ? scatter({ 0.0f, 1.0f, 0.0f }, moon, moon_irradiance) : structures::vec3_s{}) };

		constants.sun = { sun.x, sun.y, sun.z, sun_irradiance };
		constants.moon = { moon.x, moon.y, moon.z, moon_active ? moon_irradiance : 0.0f };
		constants.size = { static_cast<std::float_t>(atmosphere_width), static_cast<std::float_t>(atmosphere_height), 0.0f, 0.0f };
		constants.clouds = { drift, atmosphere_coverage + weather.cloud_now * (1.0f - atmosphere_coverage), (1.0f - weather.storm_now * 0.55f) * (1.0f - weather.rain_now * 0.2f), mathematics.smoothstep(-0.05f, -0.25f, sun.y) };
		constants.zenith = { zenith.x, zenith.y, zenith.z, atmosphere_bounce };

		updating = true;
		strip = 0u;
		refresh = atmosphere_refresh;
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::render_strip()
	{
		const auto rows{ atmosphere_height / atmosphere_strips };

		ID3D11UnorderedAccessView* outputs[3] = { access, nullptr, clear_access };
		ID3D11UnorderedAccessView* unbound[3]{};

		constants.size.z = static_cast<std::float_t>(strip * rows);

		gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

		gpu.context->CSSetConstantBuffers(3u, 1u, &constant_buffer);
		gpu.context->CSSetUnorderedAccessViews(0u, 3u, outputs, nullptr);
		gpu.context->CSSetShader(sky_shader, nullptr, 0u);

		gpu.context->Dispatch(atmosphere_width / compute_group_size, (rows + compute_group_size - 1u) / compute_group_size, 1u);

		gpu.context->CSSetUnorderedAccessViews(0u, 3u, unbound, nullptr);

		strip++;

		if (strip >= atmosphere_strips)
		{
			updating = false;

			finish();
		}
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::finish()
	{
		ID3D11ShaderResourceView* unbound{ nullptr };
		ID3D11UnorderedAccessView* cleared{ nullptr };

		gpu.context->GenerateMips(view);

		sky.build();

		gpu.context->CSSetShaderResources(0u, 1u, &view);
		gpu.context->CSSetSamplers(0u, 1u, &gpu.sampler_linear_wrap);
		gpu.context->CSSetUnorderedAccessViews(1u, 1u, &sh_access, nullptr);
		gpu.context->CSSetShader(sh_shader, nullptr, 0u);

		gpu.context->Dispatch(1u, 1u, 1u);

		gpu.context->CSSetUnorderedAccessViews(1u, 1u, &cleared, nullptr);
		gpu.context->CSSetShaderResources(0u, 1u, &unbound);

		gpu.context->CopyResource(sh_staging, sh_buffer);

		sh_pending = true;
	}
	/*
	//=====================================================================================
	*/
	void atmosphere_c::read_sh(bool wait)
	{
		D3D11_MAPPED_SUBRESOURCE mapped{};

		if (SUCCEEDED(gpu.context->Map(sh_staging, 0u, D3D11_MAP_READ, wait ? 0u : D3D11_MAP_FLAG_DO_NOT_WAIT, &mapped)))
		{
			std::memcpy(sky.sh, mapped.pData, sizeof(sky.sh));
			std::memcpy(sky.base_sh, mapped.pData, sizeof(sky.base_sh));

			gpu.context->Unmap(sh_staging, 0u);

			sky.add_ground_bounce();

			sh_pending = false;
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s atmosphere_c::light_depth(structures::vec3_s position, structures::vec3_s light)
	{
		const auto b{ static_cast<std::double_t>(mathematics.dot(position, light)) };
		const auto c{ static_cast<std::double_t>(position.x) * position.x + static_cast<std::double_t>(position.y) * position.y + static_cast<std::double_t>(position.z) * position.z - static_cast<std::double_t>(atmosphere_top) * atmosphere_top };
		const auto reach{ static_cast<std::float_t>(-b + std::sqrt(std::max(b * b - c, 0.0))) };
		const auto step{ std::max(reach, 0.0f) / 8.0f };

		structures::vec3_s depth{};

		for (auto index{ 0u }; index < 8u; index++)
		{
			const auto height{ mathematics.length(position + light * (step * (static_cast<std::float_t>(index) + 0.5f))) - atmosphere_planet };

			depth += structures::vec3_s{ std::exp(-height / atmosphere_rayleigh_height), std::exp(-height / atmosphere_mie_height), std::max(0.0f, 1.0f - std::fabs(height - 25000.0f) / 15000.0f) } * step;
		}

		return depth;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s atmosphere_c::extinction(structures::vec3_s depth)
	{
		return atmosphere_rayleigh * depth.x + structures::vec3_s{ 1.0f, 1.0f, 1.0f } * ((atmosphere_mie_scatter + atmosphere_mie_absorb) * depth.y) + atmosphere_ozone * depth.z;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s atmosphere_c::scatter(structures::vec3_s direction, structures::vec3_s light, std::float_t intensity)
	{
		const auto origin{ structures::vec3_s{ 0.0f, atmosphere_planet + 250.0f, 0.0f } };
		const auto distance{ atmosphere_top - atmosphere_planet - 250.0f };
		const auto step{ distance / 24.0f };
		const auto mu{ mathematics.dot(direction, light) };
		const auto rayleigh_phase{ 3.0f / (16.0f * pi) * (1.0f + mu * mu) };
		const auto mie_phase{ 3.0f / (8.0f * pi) * ((1.0f - 0.78f * 0.78f) * (1.0f + mu * mu)) / ((2.0f + 0.78f * 0.78f) * std::pow(std::max(1.0f + 0.78f * 0.78f - 2.0f * 0.78f * mu, 0.0001f), 1.5f)) };

		structures::vec3_s view_depth{};
		structures::vec3_s rayleigh_sum{};
		structures::vec3_s mie_sum{};

		for (auto index{ 0u }; index < 24u; index++)
		{
			const auto position{ origin + direction * (step * (static_cast<std::float_t>(index) + 0.5f)) };
			const auto height{ mathematics.length(position) - atmosphere_planet };
			const auto density{ structures::vec3_s{ std::exp(-height / atmosphere_rayleigh_height), std::exp(-height / atmosphere_mie_height), std::max(0.0f, 1.0f - std::fabs(height - 25000.0f) / 15000.0f) } * step };

			view_depth += density;

			const auto total{ extinction(view_depth + light_depth(position, light)) };
			const structures::vec3_s transmittance{ std::exp(-total.x), std::exp(-total.y), std::exp(-total.z) };

			rayleigh_sum += transmittance * density.x;
			mie_sum += transmittance * density.y;
		}

		return (structures::vec3_s{ rayleigh_sum.x * atmosphere_rayleigh.x, rayleigh_sum.y * atmosphere_rayleigh.y, rayleigh_sum.z * atmosphere_rayleigh.z } * rayleigh_phase + mie_sum * (atmosphere_mie_scatter * mie_phase)) * (light.y > -0.3f ? intensity : 0.0f);
	}
}

//=====================================================================================
