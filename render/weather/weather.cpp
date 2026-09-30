
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	weather_c weather;

	bool weather_c::create()
	{
		vertex_shader = gpu.create_vertex_shader("rain_vs", nullptr, 0u, nullptr);
		pixel_shader = gpu.create_pixel_shader("rain_ps");
		splash_vertex = gpu.create_vertex_shader("splash_vs", nullptr, 0u, nullptr);
		splash_pixel = gpu.create_pixel_shader("splash_ps");
		bolt_vertex = gpu.create_vertex_shader("bolt_vs", nullptr, 0u, nullptr);
		bolt_pixel = gpu.create_pixel_shader("bolt_ps");
		bolt_buffer = gpu.create_constant_buffer(sizeof(structures::bolt_constants_s));
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::rain_constants_s));

		roofs.assign(roof_grid * roof_grid, roof_open);
		roof_cells.assign(roof_grid * roof_grid, INT64_MIN);

		if (gpu.device)
		{
			const D3D11_TEXTURE2D_DESC description{ roof_grid, roof_grid, 1u, 1u, DXGI_FORMAT_R32_FLOAT, { 1u, 0u }, D3D11_USAGE_DEFAULT, D3D11_BIND_SHADER_RESOURCE, 0u, 0u };
			const D3D11_SUBRESOURCE_DATA initial{ roofs.data(), roof_grid * sizeof(std::float_t), 0u };

			if (SUCCEEDED(gpu.device->CreateTexture2D(&description, &initial, &roof_texture)))
			{
				gpu.device->CreateShaderResourceView(roof_texture, nullptr, &roof_view);
			}
		}

		return vertex_shader && pixel_shader && splash_vertex && splash_pixel && bolt_vertex && bolt_pixel && bolt_buffer && constant_buffer && roof_view;
	}
	/*
	//=====================================================================================
	*/
	void weather_c::destroy()
	{
		functions::release(vertex_shader);
		functions::release(pixel_shader);
		functions::release(splash_vertex);
		functions::release(splash_pixel);
		functions::release(bolt_vertex);
		functions::release(bolt_pixel);
		functions::release(bolt_buffer);
		functions::release(constant_buffer);
		functions::release(roof_view);
		functions::release(roof_texture);
	}
	/*
	//=====================================================================================
	*/
	void weather_c::survey()
	{
		const auto camera{ renderer.camera.position };
		const auto center_x{ static_cast<std::int64_t>(std::floor(camera.x / roof_cell)) };
		const auto center_z{ static_cast<std::int64_t>(std::floor(camera.z / roof_cell)) };
		const auto half{ static_cast<std::int64_t>(roof_grid / 2u) };
		const auto size{ static_cast<std::int64_t>(roof_grid) };

		for (auto step{ 0u }; step < roof_budget; step++)
		{
			const auto texel{ roof_cursor++ % (roof_grid * roof_grid) };
			const auto texel_x{ static_cast<std::int64_t>(texel % roof_grid) };
			const auto texel_z{ static_cast<std::int64_t>(texel / roof_grid) };
			const auto first_x{ center_x - half };
			const auto first_z{ center_z - half };
			const auto cell_x{ first_x + (((texel_x - first_x) % size) + size) % size };
			const auto cell_z{ first_z + (((texel_z - first_z) % size) + size) % size };
			const auto key{ (cell_x << 32) ^ (cell_z & 0xFFFFFFFF) };
			const auto middle{ structures::vec3_s{ (static_cast<std::float_t>(cell_x) + 0.5f) * roof_cell, camera.y, (static_cast<std::float_t>(cell_z) + 0.5f) * roof_cell } };
			const auto hit{ world.trace(middle + structures::vec3_s{ 0.0f, roof_reach, 0.0f }, middle - structures::vec3_s{ 0.0f, roof_reach, 0.0f }, { 0.05f, 0.05f, 0.05f }, structures::contents_solid) };
			const auto height{ hit.hit && hit.brush >= 0 && hit.start_solid == false ? hit.end.y : roof_open };

			if (roof_cells[texel] != key || roofs[texel] != height)
			{
				roof_cells[texel] = key;
				roofs[texel] = height;

				roof_dirty = true;
			}
		}

		if (roof_dirty && roof_texture)
		{
			gpu.context->UpdateSubresource(roof_texture, 0u, nullptr, roofs.data(), roof_grid * sizeof(std::float_t), 0u);

			roof_dirty = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void weather_c::strike(std::float_t distance)
	{
		const auto heading{ mathematics.flat_forward(random() * two_pi) };
		const auto camera{ renderer.camera.position };
		const auto x{ camera.x + heading.x * distance };
		const auto z{ camera.z + heading.z * distance };
		const structures::vec3_s ground{ x, terrain.enabled ? std::max(terrain.height(x, z), sea_level) : 0.0f, z };
		const auto top{ ground + structures::vec3_s{ (random() - 0.5f) * 400.0f, 1300.0f + random() * 500.0f, (random() - 0.5f) * 400.0f } };

		bolt.params.x = 0.0f;

		channel(top, ground, 16u, 70.0f, 4.0f, 1.0f);

		const auto trunk{ static_cast<std::uint32_t>(bolt.params.x) };

		for (auto branch{ 0u }; branch < 3u && trunk > 5u; branch++)
		{
			const auto fork{ 1u + static_cast<std::uint32_t>(random() * static_cast<std::float_t>(trunk - 5u)) };
			const structures::vec3_s from{ bolt.points[fork * 2u + 1u].x, bolt.points[fork * 2u + 1u].y, bolt.points[fork * 2u + 1u].z };
			const auto drop{ 150.0f + random() * 350.0f };

			channel(from, from + mathematics.flat_forward(random() * two_pi) * (drop * 0.7f) - structures::vec3_s{ 0.0f, drop, 0.0f }, 6u, 35.0f, 2.0f, 0.45f);
		}

		bolt_life = weather_bolt_life;
	}
	/*
	//=====================================================================================
	*/
	void weather_c::channel(structures::vec3_s from, structures::vec3_s to, std::uint32_t steps, std::float_t wander, std::float_t width, std::float_t intensity)
	{
		auto previous{ from };

		for (auto step{ 1u }; step <= steps && static_cast<std::uint32_t>(bolt.params.x) < weather_bolt_segments; step++)
		{
			const auto along{ static_cast<std::float_t>(step) / static_cast<std::float_t>(steps) };
			const auto offset{ step == steps ? structures::vec3_s{} : structures::vec3_s{ (random() - 0.5f) * wander, (random() - 0.5f) * wander * 0.3f, (random() - 0.5f) * wander } };
			const auto next{ mathematics.lerp(from, to, along) + offset };
			const auto index{ static_cast<std::uint32_t>(bolt.params.x) };

			bolt.points[index * 2u] = { previous.x, previous.y, previous.z, width };
			bolt.points[index * 2u + 1u] = { next.x, next.y, next.z, intensity * (1.0f - along * 0.35f) };
			bolt.params.x += 1.0f;

			previous = next;
		}
	}
	/*
	//=====================================================================================
	*/
	void weather_c::set(std::float_t next_cloud, std::float_t next_rain, std::float_t next_storm)
	{
		if (forced == false)
		{
			cloud = mathematics.saturate(next_cloud);
			rain = mathematics.saturate(next_rain);
			storm = mathematics.saturate(next_storm);
		}
	}
	/*
	//=====================================================================================
	*/
	void weather_c::update(std::float_t delta)
	{
		clock += delta;

		cloud_now = mathematics.approach(cloud_now, cloud, weather_blend_rate * delta);
		rain_now = mathematics.approach(rain_now, rain, weather_blend_rate * delta);
		storm_now = mathematics.approach(storm_now, storm, weather_blend_rate * delta);
		wetness = rain_now > 0.05f ? std::min(1.0f, wetness + weather_wet_rate * rain_now * delta) : std::max(0.0f, wetness - weather_dry_rate * delta);
		flash = std::max(0.0f, flash - delta * 5.0f);
		wind = mathematics.flat_forward(0.6f + std::sin(clock * 0.03f) * 0.4f) * (1.0f + storm_now * 5.0f + rain_now * 1.5f);
		bolt_timer -= delta * storm_now;

		if (bolt_timer <= 0.0f)
		{
			const auto distance{ 400.0f + random() * 5200.0f };

			bolt_timer = 3.0f + random() * 12.0f;
			flash = mathematics.saturate(1.4f - distance / 4000.0f);
			thunder_timer = distance / audio_speed_of_sound;
			thunder_volume = mathematics.saturate(1.1f - distance / 6500.0f);

			if (distance < weather_bolt_visible && renderer.camera_valid)
			{
				strike(distance);
			}
		}

		bolt_life = std::max(0.0f, bolt_life - delta);

		if (thunder_timer >= 0.0f)
		{
			thunder_timer -= delta;

			if (thunder_timer < 0.0f)
			{
				mixer.play_2d(structures::sound_thunder, thunder_volume, 0.85f + random() * 0.25f);
			}
		}

		if ((rain_now > 0.01f || wetness > 0.01f) && renderer.camera_valid)
		{
			survey();
		}
	}
	/*
	//=====================================================================================
	*/
	void weather_c::render()
	{
		if (vertex_shader && pixel_shader && rain_now > 0.01f)
		{
			const structures::rain_constants_s constants{ { rain_now, clock, flash, 0.0f }, { wind.x, 0.0f, wind.z, 0.0f }, { terrain.constants.params.x, terrain.constants.params.w, terrain.enabled && terrain.height_view ? 1.0f : 0.0f, water.enabled ? water.height : -100000.0f } };
			const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(renderer.width), static_cast<std::float_t>(renderer.height), 0.0f, 1.0f };

			gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

			gpu.context->OMSetRenderTargets(1u, &renderer.hdr.rtv, renderer.depth.dsv_read_only);
			gpu.context->OMSetDepthStencilState(gpu.depth_read, 0u);
			gpu.context->OMSetBlendState(gpu.blend_reactive, nullptr, 0xFFFFFFFFu);
			gpu.context->RSSetState(gpu.raster_none);
			gpu.context->RSSetViewports(1u, &viewport);
			gpu.context->IASetInputLayout(nullptr);
			gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
			gpu.context->VSSetShader(vertex_shader, nullptr, 0u);
			gpu.context->PSSetShader(pixel_shader, nullptr, 0u);
			gpu.context->VSSetConstantBuffers(3u, 1u, &constant_buffer);
			gpu.context->PSSetConstantBuffers(3u, 1u, &constant_buffer);
			gpu.context->VSSetShaderResources(0u, 1u, &roof_view);

			gpu.context->DrawInstanced(6u, static_cast<UINT>(static_cast<std::float_t>(weather_drop_count) * rain_now), 0u, 0u);

			ID3D11ShaderResourceView* unbound{ nullptr };
			ID3D11ShaderResourceView* heights{ terrain.enabled ? terrain.height_view : nullptr };

			gpu.context->VSSetShaderResources(terrain_height_slot, 1u, &heights);
			gpu.context->VSSetSamplers(0u, 1u, &gpu.sampler_linear_clamp);
			gpu.context->VSSetShader(splash_vertex, nullptr, 0u);
			gpu.context->PSSetShader(splash_pixel, nullptr, 0u);

			gpu.context->DrawInstanced(6u, weather_splash_grid * weather_splash_grid, 0u, 0u);

			if (bolt_life > 0.0f && bolt.params.x > 0.0f)
			{
				const auto age{ weather_bolt_life - bolt_life };

				bolt.params.y = std::max({ std::exp(-age * 14.0f), 0.8f * std::exp(-std::fabs(age - 0.14f) * 30.0f), 0.6f * std::exp(-std::fabs(age - 0.28f) * 30.0f) }) * weather_bolt_brightness;

				gpu.update_buffer(bolt_buffer, &bolt, sizeof(bolt));

				gpu.context->VSSetConstantBuffers(4u, 1u, &bolt_buffer);
				gpu.context->OMSetBlendState(gpu.blend_additive, nullptr, 0xFFFFFFFFu);
				gpu.context->VSSetShader(bolt_vertex, nullptr, 0u);
				gpu.context->PSSetShader(bolt_pixel, nullptr, 0u);

				gpu.context->DrawInstanced(6u, static_cast<UINT>(bolt.params.x), 0u, 0u);
			}

			gpu.context->VSSetShaderResources(0u, 1u, &unbound);
			gpu.context->VSSetShaderResources(terrain_height_slot, 1u, &unbound);
			gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);
			gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec4_s weather_c::params()
	{
		return { wetness, rain_now, flash, cloud_now };
	}
	/*
	//=====================================================================================
	*/
	std::float_t weather_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
