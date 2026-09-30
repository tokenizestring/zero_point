
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	particles_c particles;

	bool particles_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::particle_vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::particle_vertex_s, uv), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "COLOR", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 0u, offsetof(structures::particle_vertex_s, color), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 1u, DXGI_FORMAT_R32G32B32A32_FLOAT, 0u, offsetof(structures::particle_vertex_s, params), D3D11_INPUT_PER_VERTEX_DATA, 0u }
		};

		std::vector<std::uint32_t> indices;

		indices.reserve(static_cast<std::size_t>(maximum_particles) * 6u);

		for (auto index{ 0u }; index < maximum_particles; index++)
		{
			indices.insert(indices.end(), { index * 4u, index * 4u + 1u, index * 4u + 2u, index * 4u, index * 4u + 2u, index * 4u + 3u });
		}

		vertex_shader = gpu.create_vertex_shader("particles_vs", elements, 4u, &layout);
		pixel_shader = gpu.create_pixel_shader("particles_ps");
		vertex_buffer = gpu.create_buffer(maximum_particles * 4u * sizeof(structures::particle_vertex_s), D3D11_USAGE_DYNAMIC, D3D11_BIND_VERTEX_BUFFER, D3D11_CPU_ACCESS_WRITE, nullptr, 0u, 0u);
		index_buffer = gpu.create_buffer(static_cast<std::uint32_t>(indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, indices.data(), 0u, 0u);
		constant_buffer = gpu.create_constant_buffer(sizeof(structures::particle_constants_s));

		pool.reserve(maximum_particles);
		vertices.reserve(static_cast<std::size_t>(maximum_particles) * 4u);

		return vertex_shader && pixel_shader && layout && vertex_buffer && index_buffer && constant_buffer;
	}
	/*
	//=====================================================================================
	*/
	void particles_c::destroy()
	{
		functions::release(vertex_buffer);
		functions::release(index_buffer);
		functions::release(constant_buffer);
		functions::release(vertex_shader);
		functions::release(pixel_shader);
		functions::release(layout);

		clear();
	}
	/*
	//=====================================================================================
	*/
	void particles_c::clear()
	{
		pool.clear();
	}
	/*
	//=====================================================================================
	*/
	void particles_c::emit(std::uint32_t kind, structures::vec3_s position, structures::vec3_s velocity, std::float_t spread, std::uint32_t count, bool view_space)
	{
		const auto& definition{ particle_kinds[kind] };

		for (auto index{ 0u }; index < count && pool.size() < maximum_particles; index++)
		{
			structures::particle_s particle{};

			particle.position = position;
			particle.velocity = velocity + structures::vec3_s{ random() * 2.0f - 1.0f, random() * 2.0f - 1.0f, random() * 2.0f - 1.0f } * spread;
			particle.color = definition.color;
			particle.life = mathematics.lerp(definition.life_minimum, definition.life_maximum, random());
			particle.size = mathematics.lerp(definition.size_minimum, definition.size_maximum, random());
			particle.rotation = kind == structures::particle_flame || kind == structures::particle_fire ? 0.0f : random() * two_pi;
			particle.spin = kind == structures::particle_flame || kind == structures::particle_fire ? 0.0f : (random() - 0.5f) * 3.0f;
			particle.seed = random();
			particle.kind = kind;
			particle.view_space = view_space;

			pool.push_back(particle);
		}
	}
	/*
	//=====================================================================================
	*/
	void particles_c::torch(structures::vec3_s head, std::float_t delta)
	{
		const structures::vec3_s rise{ renderer.camera.right.y, renderer.camera.up.y, renderer.camera.forward.y };

		torch_budget += delta * torch_flame_rate;

		while (torch_budget >= 1.0f)
		{
			emit(structures::particle_flame, head + structures::vec3_s{ random() - 0.5f, random() * 0.5f, random() - 0.5f } * 0.03f, rise * 0.32f, 0.05f, 1u, true);

			if (random() < 0.07f)
			{
				emit(structures::particle_ember, head, rise * 0.55f, 0.22f, 1u, true);
			}

			torch_budget -= 1.0f;
		}
	}
	/*
	//=====================================================================================
	*/
	void particles_c::impact(std::uint32_t surface, structures::vec3_s position, structures::vec3_s normal)
	{
		const auto first{ pool.size() };
		const auto outward{ normal * 2.2f + structures::vec3_s{ 0.0f, 1.2f, 0.0f } };

		auto debris{ particle_kinds[structures::particle_chip].color };
		auto haze{ particle_kinds[structures::particle_dust].color };

		if (surface == structures::surface_wood)
		{
			emit(structures::particle_chip, position, outward, 1.4f, 7u, false);
			emit(structures::particle_dust, position, normal * 0.6f, 0.3f, 2u, false);

			haze = { 0.4f, 0.3f, 0.2f, 0.35f };
		}

		else if (surface == structures::surface_rock || surface == structures::surface_concrete)
		{
			emit(structures::particle_chip, position, outward, 1.6f, 6u, false);
			emit(structures::particle_dust, position, normal * 0.8f, 0.4f, 4u, false);

			debris = { 0.38f, 0.37f, 0.35f, 1.0f };
		}

		else if (surface == structures::surface_metal || surface == structures::surface_grate)
		{
			emit(structures::particle_spark, position, normal * 3.0f, 2.4f, 10u, false);
			emit(structures::particle_dust, position, normal * 0.4f, 0.15f, 1u, false);

			haze = { 0.3f, 0.3f, 0.3f, 0.3f };
		}

		else if (surface == structures::surface_flesh)
		{
			emit(structures::particle_blood, position, normal * 1.4f, 0.9f, 9u, false);
		}

		else if (surface == structures::surface_sand)
		{
			emit(structures::particle_dust, position, normal * 1.4f + structures::vec3_s{ 0.0f, 0.6f, 0.0f }, 0.7f, 7u, false);

			haze = { 0.78f, 0.7f, 0.52f, 0.55f };
		}

		else if (surface == structures::surface_dirt || surface == structures::surface_grass || surface == structures::surface_gravel)
		{
			emit(structures::particle_chip, position, outward * 0.8f, 1.3f, 5u, false);
			emit(structures::particle_dust, position, normal * 0.9f, 0.45f, 4u, false);

			debris = { 0.19f, 0.14f, 0.1f, 1.0f };
			haze = { 0.34f, 0.28f, 0.22f, 0.5f };
		}

		else
		{
			emit(structures::particle_dust, position, normal * 0.7f, 0.4f, 4u, false);
		}

		for (auto index{ first }; index < pool.size(); index++)
		{
			pool[index].color = pool[index].kind == structures::particle_chip ? debris : (pool[index].kind == structures::particle_dust ? haze : pool[index].color);
		}
	}
	/*
	//=====================================================================================
	*/
	void particles_c::update(std::float_t delta)
	{
		const structures::vec3_s rise{ renderer.camera.right.y, renderer.camera.up.y, renderer.camera.forward.y };

		clock += delta;

		for (auto index{ 0u }; index < pool.size();)
		{
			auto& particle{ pool[index] };

			particle.age += delta;

			if (particle.age >= particle.life)
			{
				particle = pool.back();

				pool.pop_back();
			}

			else
			{
				const auto& definition{ particle_kinds[particle.kind] };
				const auto up{ particle.view_space ? rise : structures::vec3_s{ 0.0f, 1.0f, 0.0f } };

				particle.velocity = particle.velocity * std::exp(-definition.drag * delta) - up * (definition.gravity * delta);
				particle.position += particle.velocity * delta;
				particle.rotation += particle.spin * delta;

				index++;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t particles_c::build(bool view_space)
	{
		const auto right{ view_space ? structures::vec3_s{ 1.0f, 0.0f, 0.0f } : renderer.camera.right };
		const auto up{ view_space ? structures::vec3_s{ 0.0f, 1.0f, 0.0f } : renderer.camera.up };

		order.clear();

		for (auto index{ 0u }; index < pool.size(); index++)
		{
			if (pool[index].view_space == view_space)
			{
				order.push_back({ view_space ? pool[index].position.z : mathematics.length_squared(pool[index].position - renderer.camera.position), index });
			}
		}

		std::sort(order.begin(), order.end(), [](const auto& a, const auto& b) { return a.first > b.first; });

		for (const auto& [distance, index] : order)
		{
			const auto& particle{ pool[index] };
			const auto& definition{ particle_kinds[particle.kind] };
			const auto progress{ particle.age / particle.life };
			const auto size{ particle.size * (1.0f + definition.growth * progress) };
			const auto cosine{ std::cos(particle.rotation) };
			const auto sine{ std::sin(particle.rotation) };
			const auto stretch{ particle.kind == structures::particle_flame || particle.kind == structures::particle_fire ? 1.5f : (particle.kind == structures::particle_chip ? 0.4f + particle.seed * 0.4f : 1.0f) };
			const auto axis_x{ (right * cosine + up * sine) * size };
			const auto axis_y{ (up * cosine - right * sine) * (size * stretch) };
			const structures::vec2_s corners[4] = { { 0.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f }, { 0.0f, 1.0f } };

			for (const auto& corner : corners)
			{
				vertices.push_back({ particle.position + axis_x * (corner.x * 2.0f - 1.0f) + axis_y * (1.0f - corner.y * 2.0f), corner, particle.color, { static_cast<std::float_t>(particle.kind), progress, definition.softness, particle.seed } });
			}
		}

		return static_cast<std::uint32_t>(order.size());
	}
	/*
	//=====================================================================================
	*/
	void particles_c::render()
	{
		if (pool.size() && vertex_buffer)
		{
			vertices.clear();

			const auto world_count{ build(false) };
			const auto view_count{ build(true) };
			const auto stride{ static_cast<UINT>(sizeof(structures::particle_vertex_s)) };
			const auto offset{ 0u };
			const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, static_cast<std::float_t>(renderer.width), static_cast<std::float_t>(renderer.height), 0.0f, 1.0f };
			const D3D11_VIEWPORT viewmodel_viewport{ 0.0f, 0.0f, static_cast<std::float_t>(renderer.width), static_cast<std::float_t>(renderer.height), viewmodel_depth_min, 1.0f };

			ID3D11ShaderResourceView* unbound{ nullptr };

			gpu.update_buffer(vertex_buffer, vertices.data(), static_cast<std::uint32_t>(vertices.size() * sizeof(structures::particle_vertex_s)));

			gpu.context->OMSetRenderTargets(1u, &renderer.hdr.rtv, renderer.depth.dsv_read_only);
			gpu.context->OMSetDepthStencilState(gpu.depth_read, 0u);
			gpu.context->OMSetBlendState(gpu.blend_premultiplied, nullptr, 0xFFFFFFFFu);
			gpu.context->RSSetState(gpu.raster_none);
			gpu.context->IASetInputLayout(layout);
			gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
			gpu.context->IASetVertexBuffers(0u, 1u, &vertex_buffer, &stride, &offset);
			gpu.context->IASetIndexBuffer(index_buffer, DXGI_FORMAT_R32_UINT, 0u);
			gpu.context->VSSetShader(vertex_shader, nullptr, 0u);
			gpu.context->PSSetShader(pixel_shader, nullptr, 0u);
			gpu.context->PSSetShaderResources(0u, 1u, &renderer.depth.srv);

			for (auto pass{ 0u }; pass < 2u; pass++)
			{
				const auto count{ pass ? view_count : world_count };
				const structures::particle_constants_s constants{ { static_cast<std::float_t>(pass), clock, camera_near, 0.0f } };

				if (count)
				{
					gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

					gpu.context->VSSetConstantBuffers(3u, 1u, &constant_buffer);
					gpu.context->PSSetConstantBuffers(3u, 1u, &constant_buffer);
					gpu.context->RSSetViewports(1u, pass ? &viewmodel_viewport : &viewport);

					gpu.context->DrawIndexed(count * 6u, pass ? world_count * 6u : 0u, 0);
				}
			}

			gpu.context->PSSetShaderResources(0u, 1u, &unbound);
			gpu.context->OMSetBlendState(gpu.blend_opaque, nullptr, 0xFFFFFFFFu);
			gpu.context->RSSetViewports(1u, &viewport);
			gpu.context->OMSetRenderTargets(0u, nullptr, nullptr);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t particles_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
