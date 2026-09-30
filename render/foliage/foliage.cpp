
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	foliage_c foliage;

	bool foliage_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "NORMAL", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, normal), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TANGENT", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 0u, offsetof(structures::vertex_s, tangent), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::vertex_s, uv), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "MATERIAL", 0u, DXGI_FORMAT_R32_UINT, 0u, offsetof(structures::vertex_s, material), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "INSTANCE", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::foliage_gpu_s, placement), D3D11_INPUT_PER_INSTANCE_DATA, 1u },
			{ "INSTANCE", 1u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::foliage_gpu_s, params), D3D11_INPUT_PER_INSTANCE_DATA, 1u }
		};

		const D3D11_INPUT_ELEMENT_DESC shadow_elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "INSTANCE", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::foliage_gpu_s, placement), D3D11_INPUT_PER_INSTANCE_DATA, 1u },
			{ "INSTANCE", 1u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::foliage_gpu_s, params), D3D11_INPUT_PER_INSTANCE_DATA, 1u }
		};

		const D3D11_INPUT_ELEMENT_DESC alpha_elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32B32_FLOAT, 0u, offsetof(structures::vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::vertex_s, uv), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "MATERIAL", 0u, DXGI_FORMAT_R32_UINT, 0u, offsetof(structures::vertex_s, material), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "INSTANCE", 0u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::foliage_gpu_s, placement), D3D11_INPUT_PER_INSTANCE_DATA, 1u },
			{ "INSTANCE", 1u, DXGI_FORMAT_R32G32B32A32_FLOAT, 1u, offsetof(structures::foliage_gpu_s, params), D3D11_INPUT_PER_INSTANCE_DATA, 1u }
		};

		vertex_shader = gpu.create_vertex_shader("gbuffer_instanced_vs", elements, 7u, &layout);
		impostor_vertex_shader = gpu.create_vertex_shader("gbuffer_impostor_vs", elements, 7u, &impostor_layout);
		impostor_pixel_shader = gpu.create_pixel_shader("gbuffer_impostor_ps");
		shadow_vertex_shader = gpu.create_vertex_shader("shadow_instanced_vs", shadow_elements, 3u, &shadow_layout);
		shadow_alpha_vertex_shader = gpu.create_vertex_shader("shadow_instanced_alpha_vs", alpha_elements, 5u, &shadow_alpha_layout);
		instance_buffer = gpu.create_buffer(foliage_maximum_instances * sizeof(structures::foliage_gpu_s), D3D11_USAGE_DYNAMIC, D3D11_BIND_VERTEX_BUFFER, D3D11_CPU_ACCESS_WRITE, nullptr, 0u, 0u);

		return vertex_shader && impostor_vertex_shader && impostor_pixel_shader && shadow_vertex_shader && shadow_alpha_vertex_shader && layout && impostor_layout && shadow_layout && shadow_alpha_layout && instance_buffer;
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::destroy()
	{
		report();

		clear();

		functions::release(instance_buffer);
		functions::release(layout);
		functions::release(impostor_layout);
		functions::release(shadow_layout);
		functions::release(shadow_alpha_layout);
		functions::release(vertex_shader);
		functions::release(impostor_vertex_shader);
		functions::release(impostor_pixel_shader);
		functions::release(shadow_vertex_shader);
		functions::release(shadow_alpha_vertex_shader);
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::clear()
	{
		species.clear();
		instances.clear();
		cells.clear();
		buckets.clear();
		bucket_alpha.clear();
		species_near.clear();
		species_far.clear();
		species_impostor.clear();
		species_shadow.clear();

		reach = 0.0f;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t foliage_c::add_species(const char* near_model, const char* far_model, std::float_t near_distance, std::float_t far_distance, std::float_t shadow_distance, std::float_t sway)
	{
		const auto near_entry{ models.find(near_model) };
		const auto far_entry{ far_model ? models.find(far_model) : nullptr };

		if (near_entry && species.size() < foliage_maximum_species && models.upload(*near_entry) && (far_entry == nullptr || models.upload(*far_entry)))
		{
			species.push_back({ near_entry, far_entry, near_distance, far_distance, shadow_distance, sway, nullptr, far_distance, nullptr });
			species_near.push_back(bucket(near_entry, false));
			species_far.push_back(far_entry ? bucket(far_entry, false) : species_near.back());
			species_impostor.push_back(UINT32_MAX);
			species_shadow.push_back(species_far.back());

			reach = std::max(reach, far_distance);

			return static_cast<std::uint32_t>(species.size() - 1u);
		}

		return UINT32_MAX;
	}
	/*
	//=====================================================================================
	*/
	bool foliage_c::add_impostor(std::uint32_t species_index, const char* model_name, std::float_t distance)
	{
		const auto entry{ models.find(model_name) };

		auto result{ false };

		if (entry && species_index < species.size() && models.upload(*entry))
		{
			species[species_index].impostor_model = entry;
			species[species_index].impostor_distance = distance;
			species_impostor[species_index] = bucket(entry, true);

			result = true;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool foliage_c::add_shadow(std::uint32_t species_index, const char* model_name)
	{
		const auto entry{ models.find(model_name) };

		auto result{ false };

		if (entry && species_index < species.size() && models.upload(*entry))
		{
			species[species_index].shadow_model = entry;
			species_shadow[species_index] = bucket(entry, false);

			result = true;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t foliage_c::bucket(const structures::model_s* model, bool impostor)
	{
		for (auto index{ 0u }; index < buckets.size(); index++)
		{
			if (buckets[index].model == model && buckets[index].impostor == impostor)
			{
				return index;
			}
		}

		std::vector<std::uint8_t> alpha;

		for (const auto& part : model->parts)
		{
			const auto material{ part.index_count ? model->vertices[model->indices[part.first_index]].material : 0u };

			alpha.push_back(material < materials.gpu_materials.size() && (materials.gpu_materials[material].flags & structures::material_flag_alpha_test) ? 1u : 0u);
		}

		buckets.push_back({ model, 0u, 0u, {}, impostor, false });
		bucket_alpha.push_back(std::move(alpha));

		return static_cast<std::uint32_t>(buckets.size() - 1u);
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::add(std::uint32_t species_index, structures::vec3_s position, std::float_t yaw, std::float_t scale)
	{
		if (species_index < species.size())
		{
			instances.push_back({ position, yaw, scale, species_index });
		}
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::build(structures::vec3_s minimum, structures::vec3_s maximum)
	{
		origin = minimum;
		cells_x = std::max(1u, static_cast<std::uint32_t>(std::ceil((maximum.x - minimum.x) / foliage_cell_size)));
		cells_z = std::max(1u, static_cast<std::uint32_t>(std::ceil((maximum.z - minimum.z) / foliage_cell_size)));

		cells.assign(static_cast<std::size_t>(cells_x) * cells_z, { {}, { FLT_MAX, FLT_MAX, FLT_MAX }, { -FLT_MAX, -FLT_MAX, -FLT_MAX } });

		for (auto index{ 0u }; index < instances.size(); index++)
		{
			const auto& instance{ instances[index] };
			const auto& model{ *species[instance.species].near_model };
			const auto cx{ std::min(static_cast<std::uint32_t>(std::max(0.0f, (instance.position.x - origin.x) / foliage_cell_size)), cells_x - 1u) };
			const auto cz{ std::min(static_cast<std::uint32_t>(std::max(0.0f, (instance.position.z - origin.z) / foliage_cell_size)), cells_z - 1u) };
			const auto radius{ std::max(std::max(std::fabs(model.bounds_min.x), std::fabs(model.bounds_max.x)), std::max(std::fabs(model.bounds_min.z), std::fabs(model.bounds_max.z))) * instance.scale };

			auto& cell{ cells[static_cast<std::size_t>(cz) * cells_x + cx] };

			cell.instances.push_back(index);
			cell.bounds_min = mathematics.minimum(cell.bounds_min, instance.position + structures::vec3_s{ -radius, model.bounds_min.y * instance.scale, -radius });
			cell.bounds_max = mathematics.maximum(cell.bounds_max, instance.position + structures::vec3_s{ radius, model.bounds_max.y * instance.scale, radius });
		}

		logger.write("foliage: %zu instances, %zu species, %zu models", instances.size(), species.size(), buckets.size());
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::select(structures::vec3_s camera, const structures::vec4_s* planes, std::uint32_t plane_count, bool shadow_pass)
	{
		for (auto& entry : buckets)
		{
			entry.items.clear();

			entry.fading = false;
		}

		for (const auto& cell : cells)
		{
			const auto gap{ mathematics.length(mathematics.maximum(mathematics.maximum(cell.bounds_min - camera, camera - cell.bounds_max), { 0.0f, 0.0f, 0.0f })) };

			if (cell.instances.size() && gap < reach && mathematics.box_visible(planes, plane_count, cell.bounds_min, cell.bounds_max))
			{
				for (const auto index : cell.instances)
				{
					const auto& instance{ instances[index] };
					const auto& kind{ species[instance.species] };
					const auto distance{ mathematics.distance(camera, instance.position) };

					if (instance.scale > 0.0f && distance < (shadow_pass ? kind.shadow_distance : kind.far_distance))
					{
						const auto first{ species_far[instance.species] != species_near[instance.species] && shadow_pass == false ? std::clamp((distance - kind.near_distance) / foliage_fade_band + 1.0f, 0.0f, 1.0f) : 1.0f };
						const auto second{ shadow_pass == false && species_impostor[instance.species] != UINT32_MAX ? std::clamp((distance - kind.impostor_distance) / foliage_fade_band + 1.0f, 0.0f, 1.0f) : 0.0f };

						if (first < 1.0f)
						{
							push(species_near[instance.species], index, first);
						}

						if (first > 0.0f && second < 1.0f)
						{
							push(shadow_pass ? species_shadow[instance.species] : species_far[instance.species], index, first < 1.0f ? -first : second);
						}

						if (second > 0.0f)
						{
							push(species_impostor[instance.species], index, second < 1.0f ? -second : 0.0f);
						}
					}
				}
			}
		}

		staging.clear();

		for (auto& entry : buckets)
		{
			const auto count{ std::min(entry.items.size(), static_cast<std::size_t>(foliage_maximum_instances) - staging.size()) };

			entry.first = static_cast<std::uint32_t>(staging.size());
			entry.count = static_cast<std::uint32_t>(count);

			staging.insert(staging.end(), entry.items.begin(), entry.items.begin() + static_cast<std::ptrdiff_t>(count));
		}

		if (staging.size())
		{
			gpu.update_buffer(instance_buffer, staging.data(), static_cast<std::uint32_t>(staging.size() * sizeof(structures::foliage_gpu_s)));
		}
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::report()
	{
		for (const auto& entry : buckets)
		{
			if (entry.count && static_cast<std::uint64_t>(entry.model->mesh.index_count / 3u) * entry.count > foliage_report_triangles)
			{
				logger.write("foliage: %s x%u = %.2f M tris", entry.model->name, entry.count, static_cast<std::double_t>(entry.model->mesh.index_count / 3u) * static_cast<std::double_t>(entry.count) / 1000000.0);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::push(std::uint32_t bucket_index, std::uint32_t index, std::float_t fade)
	{
		const auto& instance{ instances[index] };

		buckets[bucket_index].items.push_back({ { instance.position.x, instance.position.y, instance.position.z, instance.yaw }, { instance.scale, mathematics.hash_float(index) * two_pi, species[instance.species].sway, fade } });
		buckets[bucket_index].fading = buckets[bucket_index].fading || fade != 0.0f;
	}
	/*
	//=====================================================================================
	*/
	void foliage_c::draw(bool shadow_pass)
	{
		const UINT strides[2] = { sizeof(structures::vertex_s), sizeof(structures::foliage_gpu_s) };
		const UINT offsets[2] = { 0u, 0u };

		if (shadow_pass == false)
		{
			renderer.set_object(mathematics.identity(), mathematics.identity(), -1.0f, 0u);
		}

		for (auto index{ 0u }; index < buckets.size(); index++)
		{
			const auto& entry{ buckets[index] };

			if (entry.count && entry.model->mesh.vertex_buffer)
			{
				ID3D11Buffer* streams[2] = { entry.model->mesh.vertex_buffer, instance_buffer };

				gpu.context->IASetVertexBuffers(0u, 2u, streams, strides, offsets);
				gpu.context->IASetIndexBuffer(entry.model->mesh.index_buffer, DXGI_FORMAT_R32_UINT, 0u);

				for (auto part{ 0u }; part < entry.model->parts.size(); part++)
				{
					const auto alpha{ bucket_alpha[index][part] != 0u };

					if (entry.impostor)
					{
						gpu.context->IASetInputLayout(impostor_layout);
						gpu.context->VSSetShader(impostor_vertex_shader, nullptr, 0u);
						gpu.context->PSSetShader(impostor_pixel_shader, nullptr, 0u);
						gpu.context->RSSetState(gpu.raster_none);
					}

					else if (shadow_pass)
					{
						gpu.context->IASetInputLayout(alpha ? shadow_alpha_layout : shadow_layout);
						gpu.context->VSSetShader(alpha ? shadow_alpha_vertex_shader : shadow_vertex_shader, nullptr, 0u);
						gpu.context->PSSetShader(alpha ? shadows.alpha_pixel_shader : nullptr, nullptr, 0u);
					}

					else
					{
						gpu.context->IASetInputLayout(layout);
						gpu.context->VSSetShader(vertex_shader, nullptr, 0u);
						gpu.context->PSSetShader(alpha || entry.fading ? renderer.gbuffer_alpha_ps : renderer.gbuffer_ps, nullptr, 0u);
						gpu.context->RSSetState(alpha ? gpu.raster_none : gpu.raster_back);
					}

					gpu.context->DrawIndexedInstanced(entry.model->parts[part].index_count, entry.count, entry.model->parts[part].first_index, 0, entry.first);
				}
			}
		}
	}
}

//=====================================================================================
