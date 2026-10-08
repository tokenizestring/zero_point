
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	renderer_c renderer;

	bool renderer_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "NORMAL", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, normal), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TANGENT", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 0u, offsetof(structures::vertex_s, tangent), D3D11_INPUT_PER_VERTEX_DATA, 0u },
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

		gbuffer_vs = gpu.create_vertex_shader("gbuffer_vs", elements, 5u, &gbuffer_layout);
		gbuffer_skinned_vs = gpu.create_vertex_shader("gbuffer_skinned_vs", skinned_elements, 7u, &skinned_layout);
		gbuffer_ps = gpu.create_pixel_shader("gbuffer_ps");
		gbuffer_alpha_ps = gpu.create_pixel_shader("gbuffer_alpha_ps");
		lighting_cs = gpu.create_compute_shader("lighting_cs");
		fullscreen_vs = gpu.create_vertex_shader("fullscreen_vs", nullptr, 0u, nullptr);
		tonemap_ps = gpu.create_pixel_shader("tonemap_ps");

		frame_buffer = gpu.create_constant_buffer(sizeof(structures::frame_constants_s));
		object_buffer = gpu.create_constant_buffer(sizeof(structures::object_constants_s));
		post_buffer = gpu.create_constant_buffer(sizeof(structures::post_constants_s));
		light_buffer = gpu.create_buffer(maximum_lights * sizeof(structures::light_gpu_s), D3D11_USAGE_DYNAMIC, D3D11_BIND_SHADER_RESOURCE, D3D11_CPU_ACCESS_WRITE, nullptr, D3D11_RESOURCE_MISC_BUFFER_STRUCTURED, sizeof(structures::light_gpu_s));

		if (light_buffer)
		{
			gpu.device->CreateShaderResourceView(light_buffer, nullptr, &light_view);
		}

		palette_buffer = gpu.create_buffer(maximum_palette_bones * 4u * sizeof(structures::vec4_s), D3D11_USAGE_DYNAMIC, D3D11_BIND_SHADER_RESOURCE, D3D11_CPU_ACCESS_WRITE, nullptr, D3D11_RESOURCE_MISC_BUFFER_STRUCTURED, sizeof(structures::vec4_s));

		if (palette_buffer)
		{
			gpu.device->CreateShaderResourceView(palette_buffer, nullptr, &palette_view);
		}

		gpu.create_target(white, 1u, 1u, DXGI_FORMAT_R8G8B8A8_UNORM, structures::target_rtv | structures::target_srv);
		gpu.create_target(black, 1u, 1u, DXGI_FORMAT_R8G8B8A8_UNORM, structures::target_rtv | structures::target_srv);

		const std::float_t one[4] = { 1.0f, 1.0f, 1.0f, 1.0f };
		const std::float_t zero[4] = { 0.0f, 0.0f, 0.0f, 0.0f };

		gpu.context->ClearRenderTargetView(white.rtv, one);
		gpu.context->ClearRenderTargetView(black.rtv, zero);

		default_settings(structures::quality_high);

		profiler.create();

		clouds.create();

		return gbuffer_vs && gbuffer_ps && gbuffer_layout && gbuffer_skinned_vs && skinned_layout && palette_view && lighting_cs && fullscreen_vs && tonemap_ps && frame_buffer && object_buffer && post_buffer && shadows.create() && post_process.create() && ssao.create();
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::destroy()
	{
		destroy_targets();

		gpu.destroy_target(white);
		gpu.destroy_target(black);

		functions::release(world.vertex_buffer);
		functions::release(world.index_buffer);
		functions::release(light_view);
		functions::release(light_buffer);
		functions::release(palette_view);
		functions::release(palette_buffer);
		functions::release(skinned_layout);
		functions::release(gbuffer_skinned_vs);
		functions::release(frame_buffer);
		functions::release(object_buffer);
		functions::release(post_buffer);
		functions::release(gbuffer_layout);
		functions::release(gbuffer_vs);
		functions::release(gbuffer_ps);
		functions::release(gbuffer_alpha_ps);
		functions::release(lighting_cs);
		functions::release(fullscreen_vs);
		functions::release(tonemap_ps);

		shadows.destroy();

		post_process.destroy();

		ssao.destroy();

		clouds.destroy();

		profiler.report();

		profiler.destroy();
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::default_settings(std::uint32_t preset)
	{
		const auto level{ std::clamp(preset, static_cast<std::uint32_t>(structures::quality_low), static_cast<std::uint32_t>(structures::quality_ultra)) };

		settings.preset = level;
		settings.render_scale = 1.0f;
		settings.anti_aliasing = level >= structures::quality_medium ? 2u : 1u;
		settings.shadows = level;
		settings.ambient_occlusion = level >= structures::quality_medium ? level : 0u;
		settings.reflections = level >= structures::quality_high ? level : 0u;
		settings.volumetrics = level >= structures::quality_high ? level : 0u;
		settings.clouds = level >= structures::quality_medium ? level : 0u;
		settings.textures = level >= structures::quality_medium ? 2u : 1u;
		settings.anisotropy = level >= structures::quality_high ? 16u : 4u;
		settings.effects = level;
		settings.motion_blur = level >= structures::quality_high;
		settings.depth_of_field = level >= structures::quality_high;
		settings.bloom = true;
		settings.film_grain = true;
		settings.chromatic_aberration = true;
		settings.vignette = true;
		settings.lens_flares = level >= structures::quality_high;
		settings.sharpening = 0.35f;
		settings.brightness = 1.0f;
		settings.colour_filter = 0u;
		settings.vegetation = 1.0f;
		settings.grass = 1.0f;
		settings.marks = true;
		settings.flashes = 1.0f;
		settings.field_of_view = settings.field_of_view > 0.0f ? settings.field_of_view : 95.0f;
		settings.viewmodel_field_of_view = settings.viewmodel_field_of_view > 0.0f ? settings.viewmodel_field_of_view : 68.0f;
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::apply_settings()
	{
		shadows.configure(settings.shadows);

		if (output_width && output_height)
		{
			const auto previous_width{ output_width };
			const auto previous_height{ output_height };

			output_width = 0u;

			resize(previous_width, previous_height);
		}
	}
	/*
	//=====================================================================================
	*/
	bool renderer_c::resize(std::uint32_t new_width, std::uint32_t new_height)
	{
		auto result{ true };

		if (new_width && new_height && (new_width != output_width || new_height != output_height))
		{
			destroy_targets();

			output_width = new_width;
			output_height = new_height;

			width = std::max(64u, static_cast<std::uint32_t>(static_cast<std::float_t>(new_width) * settings.render_scale));
			height = std::max(64u, static_cast<std::uint32_t>(static_cast<std::float_t>(new_height) * settings.render_scale));

			const DXGI_FORMAT formats[gbuffer_count] = { DXGI_FORMAT_R8G8B8A8_UNORM_SRGB, DXGI_FORMAT_R16G16B16A16_FLOAT, DXGI_FORMAT_R8G8B8A8_UNORM, DXGI_FORMAT_R11G11B10_FLOAT, DXGI_FORMAT_R16G16_FLOAT };

			for (auto index{ 0u }; index < gbuffer_count; index++)
			{
				result = gpu.create_target(gbuffer[index], width, height, formats[index], structures::target_rtv | structures::target_srv) && result;
			}

			result = gpu.create_depth(depth, width, height) && result;
			result = gpu.create_target(hdr, width, height, DXGI_FORMAT_R16G16B16A16_FLOAT, structures::target_rtv | structures::target_srv | structures::target_uav) && result;
			result = post_process.resize(width, height) && result;
			result = ssao.resize(width, height) && result;
			result = clouds.resize(width, height) && result;
			result = water.resize(width, height) && result;

			camera_valid = false;

			logger.write("renderer: targets %ux%u (output %ux%u)", width, height, output_width, output_height);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::destroy_targets()
	{
		for (auto& target : gbuffer)
		{
			gpu.destroy_target(target);
		}

		gpu.destroy_depth(depth);
		gpu.destroy_target(hdr);
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::set_world()
	{
		builder.build_clusters(10.0f, world_ranges);

		builder.upload(world);

		logger.write("renderer: world %u vertices, %u triangles, %zu clusters", world.vertex_count, world.index_count / 3u, world_ranges.size());
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::set_lights(const std::vector<structures::light_s>& lights)
	{
		static_lights.clear();

		for (const auto& light : lights)
		{
			static_lights.push_back(convert_light(light));
		}

		frame_lights = static_lights;
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::add_light(structures::vec3_s position, std::float_t radius, structures::vec3_s color)
	{
		if (frame_lights.size() < maximum_lights)
		{
			frame_lights.push_back({ position, radius, color, -1.0f, { 0.0f, -1.0f, 0.0f }, 0.0f });
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::add_spot(structures::vec3_s position, std::float_t radius, structures::vec3_s color, structures::vec3_s direction, std::float_t cosine)
	{
		if (frame_lights.size() < maximum_lights)
		{
			frame_lights.push_back(convert_light({ position, radius, color, cosine, direction, 0u }));
		}
	}
	/*
	//=====================================================================================
	*/
	structures::light_gpu_s renderer_c::convert_light(const structures::light_s& light)
	{
		return { light.position, light.radius, light.color, light.spot_cosine > -0.5f ? light.spot_cosine : -1.0f, mathematics.normalize(light.direction), std::min(light.spot_cosine + 0.1f, 0.999f) };
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::begin_frame(structures::vec3_s position, std::float_t yaw, std::float_t pitch, std::float_t roll, std::float_t delta)
	{
		time += delta;

		frame_delta = delta;

		const auto orientation{ mathematics.quat_euler(yaw, pitch, roll) };
		const auto aspect{ static_cast<std::float_t>(width) / static_cast<std::float_t>(height) };

		camera.position = position;
		camera.yaw = yaw;
		camera.pitch = pitch;
		camera.roll = roll;
		camera.aspect = aspect;
		camera.vertical_fov = 2.0f * std::atan(std::tan(degrees_to_radians(settings.field_of_view) * 0.5f) * (9.0f / 16.0f) * zoom);
		camera.viewmodel_fov = 2.0f * std::atan(std::tan(degrees_to_radians(settings.viewmodel_field_of_view) * 0.5f) * (9.0f / 16.0f));
		camera.forward = mathematics.quat_rotate(orientation, { 0.0f, 0.0f, 1.0f });
		camera.right = mathematics.quat_rotate(orientation, { 1.0f, 0.0f, 0.0f });
		camera.up = mathematics.quat_rotate(orientation, { 0.0f, 1.0f, 0.0f });
		camera.previous_jitter = camera.jitter;

		if (settings.anti_aliasing == 2u)
		{
			const auto sample{ static_cast<std::uint32_t>(frame_index % halton_length) + 1u };

			camera.jitter = { (mathematics.halton(sample, 2u) - 0.5f) * 2.0f / static_cast<std::float_t>(width), (mathematics.halton(sample, 3u) - 0.5f) * 2.0f / static_cast<std::float_t>(height) };
		}

		else
		{
			camera.jitter = { 0.0f, 0.0f };
		}

		camera.previous_view_projection = camera_valid ? camera.unjittered_view_projection : mathematics.multiply(mathematics.look_to(position, camera.forward, camera.up), mathematics.perspective(camera.vertical_fov, aspect, camera_near, { 0.0f, 0.0f }));
		camera.view = mathematics.look_to(position, camera.forward, camera.up);
		camera.projection = mathematics.perspective(camera.vertical_fov, aspect, camera_near, camera.jitter);
		camera.unjittered_projection = mathematics.perspective(camera.vertical_fov, aspect, camera_near, { 0.0f, 0.0f });
		camera.viewmodel_projection = mathematics.perspective(camera.viewmodel_fov, aspect, viewmodel_near, camera.jitter);
		camera.view_projection = mathematics.multiply(camera.view, camera.projection);
		camera.unjittered_view_projection = mathematics.multiply(camera.view, camera.unjittered_projection);

		camera_valid = true;

		mathematics.frustum(camera.unjittered_view_projection, view_planes);

		frame.view = camera.view;
		frame.projection = camera.projection;
		frame.view_projection = camera.view_projection;
		frame.inverse_view_projection = mathematics.inverse(camera.view_projection);
		frame.previous_view_projection = camera.previous_view_projection;
		frame.unjittered_view_projection = camera.unjittered_view_projection;
		frame.inverse_view = mathematics.inverse(camera.view);
		frame.inverse_projection = mathematics.inverse(camera.projection);
		frame.viewmodel_projection = camera.viewmodel_projection;
		frame.inverse_viewmodel_projection = mathematics.inverse(camera.viewmodel_projection);
		frame.camera_position = { position.x, position.y, position.z, camera_near };
		frame.screen = { static_cast<std::float_t>(width), static_cast<std::float_t>(height), 1.0f / static_cast<std::float_t>(width), 1.0f / static_cast<std::float_t>(height) };
		frame.jitter = { camera.jitter.x, camera.jitter.y, camera.previous_jitter.x, camera.previous_jitter.y };
		frame.sun_direction = { sky.sun_direction.x, sky.sun_direction.y, sky.sun_direction.z, sky.sun_radius };
		const auto overcast{ 1.0f - weather.cloud_now * 0.78f };

		frame.sun_color = { sky.sun_color.x * sky.sun_intensity * overcast, sky.sun_color.y * sky.sun_intensity * overcast, sky.sun_color.z * sky.sun_intensity * overcast, 0.0f };
		frame.sky_params = { sky.intensity * (1.0f - weather.cloud_now * 0.4f), sky.rotation, sky.stars * (1.0f - weather.cloud_now), 0.0f };
		frame.exposure_params = { exposure, static_cast<std::float_t>(debug_view), time, static_cast<std::float_t>(frame_index % 1024u) };
		frame.fog_params = { fog.x * (1.0f + weather.cloud_now * 1.5f + weather.rain_now * 3.5f), fog.y, fog.z, fog.w * overcast };
		frame.weather_params = weather.params();
		post_process.compensation = -(weather.cloud_now * weather_exposure_cloud + weather.storm_now * weather_exposure_storm);
		frame.quality_params = { static_cast<std::float_t>(settings.shadows), static_cast<std::float_t>(settings.ambient_occlusion), static_cast<std::float_t>(settings.reflections), settings.textures >= 2u ? 1.0f : 0.0f };
		frame.viewmodel_params = { viewmodel_depth_min, viewmodel_near, 0.0f, 0.0f };

		std::memcpy(frame.sky_sh, sky.sh, sizeof(frame.sky_sh));

		frame.probe_origin = { probes.origin.x, probes.origin.y, probes.origin.z, probes.spacing };
		frame.probe_counts = { static_cast<std::float_t>(probes.count_x), static_cast<std::float_t>(probes.count_y), static_cast<std::float_t>(probes.count_z), probes.enabled ? 1.0f : 0.0f };
		frame.light_params = { 0.0f, 0.0f, 0.0f, 0.0f };
		frame.time_params = { time, time - delta, delta, 0.0f };
		frame.water_params = { water.enabled ? 1.0f : 0.0f, water.height, water.level(position.x, position.z), 0.0f };
		frame.water_extinction = water_extinction;
		frame.water_scatter = water_scatter;
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::submit(const structures::mesh_s* mesh, const structures::mat4_s& world_matrix, const structures::mat4_s& previous_matrix, std::float_t material_override, std::uint32_t flags, structures::vec4_s motion)
	{
		if (mesh && mesh->index_count)
		{
			draws.push_back({ mesh, world_matrix, previous_matrix, material_override, flags, motion });
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::submit_skinned(const structures::character_s* character, const structures::mat4_s& world_matrix, const structures::mat4_s& previous_matrix, const structures::mat4_s* palette, const structures::mat4_s* previous_palette, std::uint32_t flags, std::float_t pallor, std::float_t clearance)
	{
		const auto bone_count{ static_cast<std::uint32_t>(character ? character->bones.size() : 0u) };

		if (character && character->mesh.index_count && palette_rows.size() / 4u + bone_count * 2u <= maximum_palette_bones)
		{
			const auto offset{ static_cast<std::uint32_t>(palette_rows.size() / 4u) };

			append_palette(palette, bone_count);
			append_palette(previous_palette, bone_count);

			skinned_draws.push_back({ character, world_matrix, previous_matrix, offset, offset + bone_count, flags, pallor, clearance });
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::append_palette(const structures::mat4_s* palette, std::uint32_t count)
	{
		for (auto bone{ 0u }; bone < count; bone++)
		{
			for (auto row{ 0u }; row < 4u; row++)
			{
				palette_rows.push_back({ palette[bone].m[row][0], palette[bone].m[row][1], palette[bone].m[row][2], palette[bone].m[row][3] });
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::draw_skinned(const structures::vec4_s* planes, std::uint32_t plane_count, bool shadow_pass, bool viewmodel_pass)
	{
		const auto stride{ static_cast<UINT>(sizeof(structures::skinned_vertex_s)) };
		const auto offset{ 0u };

		ID3D11ShaderResourceView* unbound{ nullptr };

		gpu.context->VSSetShaderResources(bone_rows_slot, 1u, &palette_view);

		for (const auto& item : skinned_draws)
		{
			const auto overlay{ (item.flags & structures::draw_flag_viewmodel) != 0u };
			const auto center{ mathematics.transform_point((item.character->bounds_min + item.character->bounds_max) * 0.5f, item.world) };
			const auto extent{ mathematics.length(item.character->bounds_max - item.character->bounds_min) * 0.5f + 0.5f };
			const auto visible{ overlay || mathematics.box_visible(planes, plane_count, center - structures::vec3_s{ extent, extent, extent }, center + structures::vec3_s{ extent, extent, extent }) };

			if (visible && overlay == viewmodel_pass && (shadow_pass ? (item.flags & (structures::draw_flag_viewmodel | structures::draw_flag_no_shadow)) == 0u : (item.flags & structures::draw_flag_shadow_only) == 0u))
			{
				set_object(item.world, item.previous_world, -1.0f, item.flags, { static_cast<std::float_t>(item.palette_offset), static_cast<std::float_t>(item.previous_offset), item.pallor, item.clearance });

				gpu.context->IASetVertexBuffers(0u, 1u, &item.character->mesh.vertex_buffer, &stride, &offset);
				gpu.context->IASetIndexBuffer(item.character->mesh.index_buffer, DXGI_FORMAT_R32_UINT, 0u);

				gpu.context->DrawIndexed(item.character->alpha_first_index, 0u, 0);

				if (shadow_pass == false && item.character->mesh.index_count > item.character->alpha_first_index)
				{
					gpu.context->PSSetShader(gbuffer_alpha_ps, nullptr, 0u);
					gpu.context->RSSetState(gpu.raster_none);

					gpu.context->DrawIndexed(item.character->mesh.index_count - item.character->alpha_first_index, item.character->alpha_first_index, 0);

					gpu.context->PSSetShader(gbuffer_ps, nullptr, 0u);
					gpu.context->RSSetState(gpu.raster_back);
				}
			}
		}

		gpu.context->VSSetShaderResources(bone_rows_slot, 1u, &unbound);
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::render(ID3D11RenderTargetView* output)
	{
		frame.light_params.x = static_cast<std::float_t>(std::min(frame_lights.size(), static_cast<std::size_t>(maximum_lights)));

		terrain.camera = camera.position;

		if (frame_lights.size())
		{
			gpu.update_buffer(light_buffer, frame_lights.data(), static_cast<std::uint32_t>(std::min(frame_lights.size(), static_cast<std::size_t>(maximum_lights)) * sizeof(structures::light_gpu_s)));
		}

		gpu.update_buffer(frame_buffer, &frame, sizeof(frame));

		if (palette_rows.size())
		{
			gpu.update_buffer(palette_buffer, palette_rows.data(), static_cast<std::uint32_t>(palette_rows.size() * sizeof(structures::vec4_s)));
		}

		gpu.context->VSSetConstantBuffers(0u, 1u, &frame_buffer);
		gpu.context->PSSetConstantBuffers(0u, 1u, &frame_buffer);
		gpu.context->CSSetConstantBuffers(0u, 1u, &frame_buffer);

		profiler.begin();

		render_shadows();

		render_gbuffer();

		occlusion_view = ssao.compute(depth.srv, gbuffer[1].srv, settings.ambient_occlusion);

		profiler.mark(structures::profile_ssao);

		cloud_view = clouds.compute(settings.clouds, frame_index);

		profiler.mark(structures::profile_clouds);

		render_lighting();

		profiler.mark(structures::profile_lighting);

		water.render();

		particles.render();

		weather.render();

		if (settings.volumetrics > 0u)
		{
			render_shafts();
		}

		water.render_underwater();

		profiler.mark(structures::profile_effects);

		const auto resolved{ post_process.resolve(hdr.srv, gbuffer[4].srv, depth.srv, settings.anti_aliasing == 2u) };

		post_process.expose(resolved, frame_delta);

		render_post(output, resolved, settings.bloom ? post_process.bloom_chain(resolved, fullscreen_vs) : black.srv);

		profiler.mark(structures::profile_post);

		profiler.end();

		draws.clear();
		skinned_draws.clear();
		palette_rows.clear();

		frame_lights = static_lights;

		frame_index++;
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::render_shafts()
	{
		const auto facing{ mathematics.dot(camera.forward, sky.sun_direction) };

		structures::vec2_s sun{};

		if (facing > 0.1f && sky.sun_direction.y > -0.05f && mathematics.project(camera.position + sky.sun_direction * 1000.0f, camera.view_projection, { 1.0f, 1.0f }, sun))
		{
			post_process.light_shafts(hdr.rtv, depth.srv, cloud_view, fullscreen_vs, sun, shaft_strength * mathematics.saturate((facing - 0.1f) * 2.5f) * (1.0f - weather.cloud_now * 0.85f));
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::render_shadows()
	{
		if (settings.shadows > 0u && shadows.resource)
		{
			shadows.update(camera, sky.sun_direction);

			gpu.context->IASetInputLayout(shadows.layout);
			gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
			gpu.context->VSSetShader(shadows.vertex_shader, nullptr, 0u);
			gpu.context->PSSetShader(nullptr, nullptr, 0u);
			gpu.context->RSSetState(gpu.raster_shadow);
			gpu.context->OMSetDepthStencilState(gpu.depth_shadow, 0u);
			gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);

			for (auto cascade{ 0u }; cascade < shadows.cascades; cascade++)
			{
				shadows.begin_cascade(cascade);

				set_object(mathematics.identity(), mathematics.identity(), -1.0f, 0u);

				gpu.context->IASetInputLayout(shadows.alpha_layout);
				gpu.context->VSSetShader(shadows.alpha_vertex_shader, nullptr, 0u);
				gpu.context->PSSetShader(shadows.alpha_pixel_shader, nullptr, 0u);
				gpu.context->PSSetSamplers(0u, 1u, &gpu.sampler_anisotropic_wrap);

				materials.bind(0u);

				draw_world(shadows.planes[cascade], 4u, true);

				gpu.context->IASetInputLayout(shadows.layout);
				gpu.context->VSSetShader(shadows.vertex_shader, nullptr, 0u);
				gpu.context->PSSetShader(nullptr, nullptr, 0u);

				draw_world(shadows.planes[cascade], 4u, false);

				if (terrain.enabled)
				{
					terrain.select(shadows.planes[cascade], 4u);

					terrain.draw(true);

					gpu.context->IASetInputLayout(shadows.layout);
					gpu.context->VSSetShader(shadows.vertex_shader, nullptr, 0u);
				}

				profiler.mark(structures::profile_cascade_ground + cascade * 2u);

				if (foliage.instances.size())
				{
					foliage.select(camera.position, shadows.planes[cascade], 4u, true);

					foliage.draw(true);

					gpu.context->IASetInputLayout(shadows.layout);
					gpu.context->VSSetShader(shadows.vertex_shader, nullptr, 0u);
					gpu.context->PSSetShader(nullptr, nullptr, 0u);
				}

				for (const auto& item : draws)
				{
					if ((item.flags & (structures::draw_flag_viewmodel | structures::draw_flag_no_shadow)) == 0u)
					{
						draw_item(item, true);
					}
				}

				if (skinned_draws.size())
				{
					gpu.context->IASetInputLayout(shadows.skinned_layout);
					gpu.context->VSSetShader(shadows.skinned_vertex_shader, nullptr, 0u);

					draw_skinned(shadows.planes[cascade], 4u, true, false);

					gpu.context->IASetInputLayout(shadows.layout);
					gpu.context->VSSetShader(shadows.vertex_shader, nullptr, 0u);
				}

				profiler.mark(structures::profile_cascade_foliage + cascade * 2u);
			}

			gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);
		}

		for (auto cascade{ settings.shadows > 0u && shadows.resource ? shadows.cascades : 0u }; cascade < shadow_cascade_count; cascade++)
		{
			profiler.mark(structures::profile_cascade_ground + cascade * 2u);
			profiler.mark(structures::profile_cascade_foliage + cascade * 2u);
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::render_gbuffer()
	{
		ID3D11RenderTargetView* targets[gbuffer_count]{};

		const std::float_t zero[4] = { 0.0f, 0.0f, 0.0f, 0.0f };

		for (auto index{ 0u }; index < gbuffer_count; index++)
		{
			targets[index] = gbuffer[index].rtv;

			gpu.context->ClearRenderTargetView(targets[index], zero);
		}

		gpu.context->ClearDepthStencilView(depth.dsv, D3D11_CLEAR_DEPTH, 0.0f, 0u);

		const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(width), static_cast<std::float_t>(height), 0.0f, 1.0f };
		const D3D11_VIEWPORT viewmodel_viewport{ 0.0f, 0.0f, static_cast<std::float_t>(width), static_cast<std::float_t>(height), viewmodel_depth_min, 1.0f };

		gpu.context->OMSetRenderTargets(gbuffer_count, targets, depth.dsv);
		gpu.context->OMSetDepthStencilState(gpu.depth_write, 0u);
		gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);
		gpu.context->RSSetState(gpu.raster_back);
		gpu.context->RSSetViewports(1u, &viewport);
		gpu.context->IASetInputLayout(gbuffer_layout);
		gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
		gpu.context->VSSetShader(gbuffer_vs, nullptr, 0u);
		gpu.context->PSSetShader(gbuffer_ps, nullptr, 0u);
		gpu.context->PSSetSamplers(0u, 1u, &gpu.sampler_anisotropic_wrap);

		materials.bind(0u);

		set_object(mathematics.identity(), mathematics.identity(), -1.0f, 0u);

		draw_world(view_planes, 6u, false);

		gpu.context->PSSetShader(gbuffer_alpha_ps, nullptr, 0u);
		gpu.context->RSSetState(gpu.raster_none);

		draw_world(view_planes, 6u, true);

		gpu.context->PSSetShader(gbuffer_ps, nullptr, 0u);
		gpu.context->RSSetState(gpu.raster_back);

		profiler.mark(structures::profile_world);

		if (terrain.enabled)
		{
			terrain.select(view_planes, 6u);

			terrain.draw(false);

			gpu.context->IASetInputLayout(gbuffer_layout);
			gpu.context->VSSetShader(gbuffer_vs, nullptr, 0u);
			gpu.context->PSSetShader(gbuffer_ps, nullptr, 0u);
		}

		profiler.mark(structures::profile_terrain);

		if (foliage.instances.size())
		{
			foliage.select(camera.position, view_planes, 6u, false);

			foliage.draw(false);

			gpu.context->IASetInputLayout(gbuffer_layout);
			gpu.context->VSSetShader(gbuffer_vs, nullptr, 0u);
			gpu.context->PSSetShader(gbuffer_ps, nullptr, 0u);
			gpu.context->RSSetState(gpu.raster_back);
		}

		profiler.mark(structures::profile_foliage);

		if (grass.ready && terrain.enabled)
		{
			grass.draw();

			gpu.context->IASetInputLayout(gbuffer_layout);
			gpu.context->VSSetShader(gbuffer_vs, nullptr, 0u);
			gpu.context->PSSetShader(gbuffer_ps, nullptr, 0u);
			gpu.context->RSSetState(gpu.raster_back);
		}

		profiler.mark(structures::profile_grass);

		for (const auto& item : draws)
		{
			if ((item.flags & (structures::draw_flag_viewmodel | structures::draw_flag_shadow_only)) == 0u)
			{
				draw_item(item, false);
			}
		}

		if (skinned_draws.size())
		{
			gpu.context->IASetInputLayout(skinned_layout);
			gpu.context->VSSetShader(gbuffer_skinned_vs, nullptr, 0u);

			draw_skinned(view_planes, 6u, false, false);

			gpu.context->IASetInputLayout(gbuffer_layout);
			gpu.context->VSSetShader(gbuffer_vs, nullptr, 0u);
		}

		gpu.context->RSSetViewports(1u, &viewmodel_viewport);

		for (const auto& item : draws)
		{
			if (item.flags & structures::draw_flag_viewmodel)
			{
				set_object(item.world, item.previous_world, item.material_override, item.flags);

				draw_mesh(item.mesh);
			}
		}

		if (skinned_draws.size())
		{
			gpu.context->IASetInputLayout(skinned_layout);
			gpu.context->VSSetShader(gbuffer_skinned_vs, nullptr, 0u);

			draw_skinned(view_planes, 6u, false, true);

			gpu.context->IASetInputLayout(gbuffer_layout);
			gpu.context->VSSetShader(gbuffer_vs, nullptr, 0u);
		}

		gpu.context->RSSetViewports(1u, &viewport);

		gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);

		profiler.mark(structures::profile_models);

		if (settings.marks)
		{
			decals.render();
		}

		profiler.mark(structures::profile_decals);
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::render_lighting()
	{
		ID3D11ShaderResourceView* resources[20] = { gbuffer[0].srv, gbuffer[1].srv, gbuffer[2].srv, gbuffer[3].srv, depth.srv, shadows.resource ? shadows.resource : white.srv, sky.prefiltered, sky.lut, cloud_view && atmosphere.clear_view ? atmosphere.clear_view : sky.equirect, occlusion_view ? occlusion_view : white.srv, black.srv, light_view, probes.views[0], probes.views[1], probes.views[2], probes.views[3], water.normal_view ? water.normal_view : black.srv, weather.roof_view ? weather.roof_view : black.srv, cloud_view ? cloud_view : black.srv, clouds.shadow_map.srv ? clouds.shadow_map.srv : white.srv };
		ID3D11SamplerState* samplers[4] = { gpu.sampler_linear_clamp, gpu.sampler_shadow, gpu.sampler_linear_wrap, gpu.sampler_point_clamp };
		ID3D11ShaderResourceView* unbound[20]{};
		ID3D11UnorderedAccessView* none{ nullptr };

		shadows.bind(2u);

		clouds.bind();

		gpu.context->CSSetShader(lighting_cs, nullptr, 0u);
		gpu.context->CSSetShaderResources(0u, 20u, resources);
		gpu.context->CSSetSamplers(0u, 4u, samplers);
		gpu.context->CSSetUnorderedAccessViews(0u, 1u, &hdr.uav, nullptr);

		gpu.context->Dispatch((width + light_tile_size - 1u) / light_tile_size, (height + light_tile_size - 1u) / light_tile_size, 1u);

		gpu.context->CSSetUnorderedAccessViews(0u, 1u, &none, nullptr);
		gpu.context->CSSetShaderResources(0u, 20u, unbound);
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::render_post(ID3D11RenderTargetView* output, ID3D11ShaderResourceView* scene, ID3D11ShaderResourceView* bloom)
	{
		post.params = { exposure, settings.bloom ? bloom_mix : 0.0f, settings.motion_blur ? motion_blur_shutter : 0.0f, static_cast<std::float_t>(frame_index % 64u) };
		post.grade = { 1.1f, 1.06f, 1.0f / std::max(settings.brightness, 0.1f), settings.sharpening };
		post.effects = { settings.chromatic_aberration ? 0.0012f : 0.0f, settings.vignette ? 0.22f : 0.0f, settings.film_grain ? 0.25f : 0.0f, static_cast<std::float_t>(settings.colour_filter) };
		post.screen = { static_cast<std::float_t>(width), static_cast<std::float_t>(height), 1.0f / static_cast<std::float_t>(width), 1.0f / static_cast<std::float_t>(height) };

		gpu.update_buffer(post_buffer, &post, sizeof(post));

		const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(output_width), static_cast<std::float_t>(output_height), 0.0f, 1.0f };

		ID3D11ShaderResourceView* resources[5] = { scene, bloom, post_process.exposure_srv, gbuffer[4].srv, depth.srv };
		ID3D11ShaderResourceView* unbound[5]{};

		gpu.context->OMSetRenderTargets(1u, &output, nullptr);
		gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);
		gpu.context->OMSetDepthStencilState(gpu.depth_none, 0u);
		gpu.context->RSSetState(gpu.raster_none);
		gpu.context->RSSetViewports(1u, &viewport);
		gpu.context->IASetInputLayout(nullptr);
		gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
		gpu.context->VSSetShader(fullscreen_vs, nullptr, 0u);
		gpu.context->PSSetShader(tonemap_ps, nullptr, 0u);
		gpu.context->PSSetShaderResources(0u, 5u, resources);
		gpu.context->PSSetSamplers(0u, 1u, &gpu.sampler_linear_clamp);
		gpu.context->PSSetConstantBuffers(4u, 1u, &post_buffer);

		gpu.context->Draw(3u, 0u);

		gpu.context->PSSetShaderResources(0u, 5u, unbound);
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::set_object(const structures::mat4_s& world_matrix, const structures::mat4_s& previous_matrix, std::float_t material_override, std::uint32_t flags, structures::vec4_s skin, structures::vec4_s motion)
	{
		object.world = world_matrix;
		object.previous_world = previous_matrix;
		object.params = { material_override, (flags & structures::draw_flag_viewmodel) ? 1.0f : 0.0f, (flags & structures::draw_flag_character) ? 1.0f : 0.0f, 0.0f };
		object.skin = skin;
		object.motion = motion;

		gpu.update_buffer(object_buffer, &object, sizeof(object));

		gpu.context->VSSetConstantBuffers(1u, 1u, &object_buffer);
		gpu.context->PSSetConstantBuffers(1u, 1u, &object_buffer);
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::draw_world(const structures::vec4_s* planes, std::uint32_t plane_count, bool alpha)
	{
		if (world.vertex_buffer && world.index_buffer)
		{
			const auto stride{ static_cast<UINT>(sizeof(structures::vertex_s)) };
			const auto offset{ 0u };

			gpu.context->IASetVertexBuffers(0u, 1u, &world.vertex_buffer, &stride, &offset);
			gpu.context->IASetIndexBuffer(world.index_buffer, DXGI_FORMAT_R32_UINT, 0u);

			for (const auto& range : world_ranges)
			{
				if (range.alpha == alpha && mathematics.box_visible(planes, plane_count, range.bounds_min, range.bounds_max))
				{
					gpu.context->DrawIndexed(range.index_count, range.first_index, 0);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::draw_item(const structures::draw_item_s& item, bool shadow_pass)
	{
		const auto alpha{ (item.flags & structures::draw_flag_alpha) != 0u };

		set_object(item.world, item.previous_world, item.material_override, item.flags, {}, item.motion);

		if (alpha && shadow_pass)
		{
			gpu.context->IASetInputLayout(shadows.alpha_layout);
			gpu.context->VSSetShader(shadows.alpha_vertex_shader, nullptr, 0u);
			gpu.context->PSSetShader(shadows.alpha_pixel_shader, nullptr, 0u);
		}

		else if (alpha)
		{
			gpu.context->PSSetShader(gbuffer_alpha_ps, nullptr, 0u);
			gpu.context->RSSetState(gpu.raster_none);
		}

		draw_mesh(item.mesh);

		if (alpha && shadow_pass)
		{
			gpu.context->IASetInputLayout(shadows.layout);
			gpu.context->VSSetShader(shadows.vertex_shader, nullptr, 0u);
			gpu.context->PSSetShader(nullptr, nullptr, 0u);
		}

		else if (alpha)
		{
			gpu.context->PSSetShader(gbuffer_ps, nullptr, 0u);
			gpu.context->RSSetState(gpu.raster_back);
		}
	}
	/*
	//=====================================================================================
	*/
	void renderer_c::draw_mesh(const structures::mesh_s* mesh)
	{
		const auto stride{ static_cast<UINT>(sizeof(structures::vertex_s)) };
		const auto offset{ 0u };

		gpu.context->IASetVertexBuffers(0u, 1u, &mesh->vertex_buffer, &stride, &offset);
		gpu.context->IASetIndexBuffer(mesh->index_buffer, DXGI_FORMAT_R32_UINT, 0u);

		gpu.context->DrawIndexed(mesh->index_count, 0u, 0);
	}
}

//=====================================================================================
