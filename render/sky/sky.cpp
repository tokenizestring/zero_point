
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	sky_c sky;

	bool sky_c::create()
	{
		if (const auto entry{ pak.find("sky_table") }; entry && entry->layers)
		{
			records.resize(entry->layers);

			std::memcpy(records.data(), pak.data(entry), records.size() * sizeof(structures::sky_record_s));
		}

		equirect_shader = gpu.create_compute_shader("sky_equirect_cs");
		prefilter_shader = gpu.create_compute_shader("sky_prefilter_cs");
		lut_shader = gpu.create_compute_shader("sky_lut_cs");
		constants = gpu.create_constant_buffer(sizeof(structures::sky_constants_s));

		D3D11_TEXTURE2D_DESC description{};

		description.Width = sky_base_cube_size;
		description.Height = sky_base_cube_size;
		description.MipLevels = 0u;
		description.ArraySize = 6u;
		description.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
		description.SampleDesc.Count = 1u;
		description.Usage = D3D11_USAGE_DEFAULT;
		description.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_UNORDERED_ACCESS | D3D11_BIND_RENDER_TARGET;
		description.MiscFlags = D3D11_RESOURCE_MISC_TEXTURECUBE | D3D11_RESOURCE_MISC_GENERATE_MIPS;

		gpu.device->CreateTexture2D(&description, nullptr, &base_texture);

		description.Width = sky_prefilter_size;
		description.Height = sky_prefilter_size;
		description.MipLevels = sky_prefilter_mips;
		description.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_UNORDERED_ACCESS;
		description.MiscFlags = D3D11_RESOURCE_MISC_TEXTURECUBE;

		gpu.device->CreateTexture2D(&description, nullptr, &prefiltered_texture);

		description.Width = brdf_lut_size;
		description.Height = brdf_lut_size;
		description.MipLevels = 1u;
		description.ArraySize = 1u;
		description.Format = DXGI_FORMAT_R16G16_FLOAT;
		description.MiscFlags = 0u;

		gpu.device->CreateTexture2D(&description, nullptr, &lut_texture);

		if (base_texture && prefiltered_texture && lut_texture)
		{
			D3D11_SHADER_RESOURCE_VIEW_DESC resource{};

			resource.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
			resource.ViewDimension = D3D11_SRV_DIMENSION_TEXTURECUBE;
			resource.TextureCube.MipLevels = static_cast<UINT>(-1);

			gpu.device->CreateShaderResourceView(base_texture, &resource, &base);
			gpu.device->CreateShaderResourceView(prefiltered_texture, &resource, &prefiltered);

			D3D11_UNORDERED_ACCESS_VIEW_DESC access{};

			access.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
			access.ViewDimension = D3D11_UAV_DIMENSION_TEXTURE2DARRAY;
			access.Texture2DArray.ArraySize = 6u;

			gpu.device->CreateUnorderedAccessView(base_texture, &access, &base_uav);

			for (auto mip{ 0u }; mip < sky_prefilter_mips; mip++)
			{
				access.Texture2DArray.MipSlice = mip;

				gpu.device->CreateUnorderedAccessView(prefiltered_texture, &access, &prefiltered_uavs[mip]);
			}

			gpu.device->CreateShaderResourceView(lut_texture, nullptr, &lut);
			gpu.device->CreateUnorderedAccessView(lut_texture, nullptr, &lut_uav);

			ID3D11UnorderedAccessView* views[2] = { nullptr, lut_uav };

			gpu.context->CSSetUnorderedAccessViews(0u, 2u, views, nullptr);

			dispatch(lut_shader, brdf_lut_size, 1u, { { static_cast<std::float_t>(brdf_lut_size), 0.0f, 0.0f, 0.0f }, {} });

			ID3D11UnorderedAccessView* cleared[2]{};

			gpu.context->CSSetUnorderedAccessViews(0u, 2u, cleared, nullptr);
		}

		logger.write("sky: %zu skies available", records.size());

		return records.size() && equirect_shader && prefilter_shader && lut_shader && base && prefiltered && lut;
	}
	/*
	//=====================================================================================
	*/
	void sky_c::destroy()
	{
		functions::release(equirect);
		functions::release(base_uav);
		functions::release(base);
		functions::release(base_texture);

		for (auto& view : prefiltered_uavs)
		{
			functions::release(view);
		}

		functions::release(prefiltered);
		functions::release(prefiltered_texture);
		functions::release(lut_uav);
		functions::release(lut);
		functions::release(lut_texture);
		functions::release(equirect_shader);
		functions::release(prefilter_shader);
		functions::release(lut_shader);
		functions::release(constants);
	}
	/*
	//=====================================================================================
	*/
	bool sky_c::select(const char* name)
	{
		for (auto index{ 0u }; index < records.size(); index++)
		{
			if (std::strcmp(records[index].name, name) == 0)
			{
				if (static_cast<std::int32_t>(index) != current)
				{
					char entry_name[pak_name_length]{};

					std::snprintf(entry_name, sizeof(entry_name), "sky_%s", name);

					functions::release(equirect);

					equirect = pak.create_texture(entry_name, 0u, false, false);

					current = static_cast<std::int32_t>(index);

					std::memcpy(sh, records[index].sh, sizeof(sh));
					std::memcpy(base_sh, records[index].sh, sizeof(base_sh));

					sun_color = records[index].sun_irradiance;
					sun_radius = std::max(records[index].sun_angular_radius, 0.0047f);

					build();

					set_rotation(rotation);

					add_ground_bounce();

					logger.write("sky: selected %s sun %.2f %.2f %.2f sh0 %.3f %.3f %.3f sh1 %.3f sh2 %.3f sh3 %.3f", name, sun_color.x, sun_color.y, sun_color.z, sh[0].x, sh[0].y, sh[0].z, sh[1].x, sh[2].x, sh[3].x);
				}

				return equirect != nullptr;
			}
		}

		logger.write("sky: unknown sky %s", name);

		return false;
	}
	/*
	//=====================================================================================
	*/
	void sky_c::build()
	{
		ID3D11UnorderedAccessView* none[2]{};

		gpu.context->CSSetShaderResources(0u, 1u, &equirect);
		gpu.context->CSSetSamplers(0u, 1u, &gpu.sampler_linear_wrap);
		gpu.context->CSSetSamplers(1u, 1u, &gpu.sampler_linear_clamp);
		gpu.context->CSSetUnorderedAccessViews(0u, 1u, &base_uav, nullptr);

		dispatch(equirect_shader, sky_base_cube_size, 6u, { { static_cast<std::float_t>(sky_base_cube_size), 0.0f, 0.0f, 0.0f }, {} });

		gpu.context->CSSetUnorderedAccessViews(0u, 2u, none, nullptr);

		gpu.context->GenerateMips(base);

		gpu.context->CSSetShaderResources(1u, 1u, &base);

		auto base_mips{ 0u };

		for (auto size{ sky_base_cube_size }; size >= 1u; size /= 2u)
		{
			base_mips++;
		}

		for (auto mip{ 0u }; mip < sky_prefilter_mips; mip++)
		{
			const auto size{ std::max(1u, sky_prefilter_size >> mip) };
			const auto roughness{ static_cast<std::float_t>(mip) / static_cast<std::float_t>(sky_prefilter_mips - 1u) };

			gpu.context->CSSetUnorderedAccessViews(0u, 1u, &prefiltered_uavs[mip], nullptr);

			dispatch(prefilter_shader, size, 6u, { { static_cast<std::float_t>(size), roughness, mip < 3u ? 256.0f : 512.0f, std::log2(static_cast<std::float_t>(sky_base_cube_size) / static_cast<std::float_t>(size)) }, { static_cast<std::float_t>(sky_base_cube_size), static_cast<std::float_t>(base_mips - 1u), 0.0f, 0.0f } });
		}

		ID3D11ShaderResourceView* unbound[2]{};

		gpu.context->CSSetUnorderedAccessViews(0u, 2u, none, nullptr);
		gpu.context->CSSetShaderResources(0u, 2u, unbound);
	}
	/*
	//=====================================================================================
	*/
	void sky_c::set_rotation(std::float_t radians)
	{
		rotation = radians;

		if (current >= 0)
		{
			const auto source{ records[static_cast<std::size_t>(current)].sun_direction };

			sun_direction = mathematics.normalize({ source.x * std::cos(radians) + source.z * std::sin(radians), source.y, -source.x * std::sin(radians) + source.z * std::cos(radians) });
		}
	}
	/*
	//=====================================================================================
	*/
	void sky_c::add_ground_bounce()
	{
		const auto sky_up{ sh[0].xyz() * (0.282095f * pi) + sh[1].xyz() * (0.488603f * 2.094395f) + sh[6].xyz() * (-0.315392f * 0.785398f) + sh[8].xyz() * (-0.546274f * 0.785398f) };
		const auto ground_irradiance{ sky_up + sun_color * std::max(sun_direction.y, 0.0f) };
		const auto ground_radiance{ ground_irradiance * (ground_albedo / pi) };

		sh[0] += structures::vec4_s{ ground_radiance.x, ground_radiance.y, ground_radiance.z, 0.0f } * 1.77245f;
		sh[1] += structures::vec4_s{ ground_radiance.x, ground_radiance.y, ground_radiance.z, 0.0f } * -1.53499f;
	}
	/*
	//=====================================================================================
	*/
	void sky_c::dispatch(ID3D11ComputeShader* shader, std::uint32_t size, std::uint32_t depth, structures::sky_constants_s parameters)
	{
		gpu.update_buffer(constants, &parameters, sizeof(parameters));

		gpu.context->CSSetConstantBuffers(3u, 1u, &constants);

		gpu.context->CSSetShader(shader, nullptr, 0u);

		gpu.context->Dispatch((size + compute_group_size - 1u) / compute_group_size, (size + compute_group_size - 1u) / compute_group_size, depth);
	}
}

//=====================================================================================
