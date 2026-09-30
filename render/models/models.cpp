
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	models_c models;

	bool models_c::load()
	{
		models.clear();

		models.reserve(maximum_models);

		if (pak.entries)
		{
			for (auto index{ 0u }; index < pak.header->entry_count; index++)
			{
				const auto& entry{ pak.entries[index] };

				if (std::strncmp(entry.name, "model_", 6u) == 0 && entry.size >= sizeof(structures::model_header_s))
				{
					auto cursor{ pak.data(&entry) };

					structures::model_header_s header{};

					std::memcpy(&header, cursor, sizeof(header));

					cursor += sizeof(header);

					structures::model_s model{};

					std::snprintf(model.name, sizeof(model.name), "%s", entry.name + 6);

					model.parts.resize(header.part_count);
					model.vertices.resize(header.vertex_count);
					model.indices.resize(header.index_count);
					model.bounds_min = header.bounds_min;
					model.bounds_max = header.bounds_max;

					std::memcpy(model.parts.data(), cursor, model.parts.size() * sizeof(structures::model_part_s));

					cursor += model.parts.size() * sizeof(structures::model_part_s);

					for (auto material{ 0u }; material < header.material_count; material++)
					{
						structures::model_material_s record{};

						std::memcpy(&record, cursor, sizeof(record));

						cursor += sizeof(record);

						model.materials.push_back(materials.register_model_material(record));
					}

					std::memcpy(model.vertices.data(), cursor, model.vertices.size() * sizeof(structures::vertex_s));

					cursor += model.vertices.size() * sizeof(structures::vertex_s);

					std::memcpy(model.indices.data(), cursor, model.indices.size() * sizeof(std::uint32_t));

					for (auto& vertex : model.vertices)
					{
						vertex.material = vertex.material < model.materials.size() ? model.materials[vertex.material] : 0u;
					}

					models.push_back(std::move(model));
				}
			}
		}

		logger.write("models: %zu models loaded, %zu materials total", models.size(), materials.gpu_materials.size());

		return models.size() > 0u;
	}
	/*
	//=====================================================================================
	*/
	void models_c::destroy()
	{
		for (auto& model : models)
		{
			functions::release(model.mesh.vertex_buffer);
			functions::release(model.mesh.index_buffer);
		}

		models.clear();
	}
	/*
	//=====================================================================================
	*/
	structures::model_s* models_c::find(const char* name)
	{
		for (auto& model : models)
		{
			if (_stricmp(model.name, name) == 0)
			{
				return &model;
			}
		}

		logger.write("models: missing model %s", name);

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	const structures::model_part_s* models_c::part(const structures::model_s& model, const char* name)
	{
		for (const auto& entry : model.parts)
		{
			if (_stricmp(entry.name, name) == 0)
			{
				return &entry;
			}
		}

		logger.write("models: missing part %s in %s", name, model.name);

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	structures::model_s* models_c::clone(const char* source, const char* name, structures::vec3_s tint, std::float_t metal)
	{
		if (const auto present{ existing(name) }; present)
		{
			return present;
		}

		if (const auto original{ find(source) }; original && models.size() < maximum_models)
		{
			structures::model_s copy{ *original };

			std::snprintf(copy.name, sizeof(copy.name), "%s", name);

			copy.mesh = {};

			std::vector<std::pair<std::uint32_t, std::uint32_t>> remap;

			for (auto& vertex : copy.vertices)
			{
				auto found{ false };

				for (const auto& [from, to] : remap)
				{
					if (found == false && from == vertex.material)
					{
						vertex.material = to;

						found = true;
					}
				}

				if (found == false)
				{
					remap.push_back({ vertex.material, variant(vertex.material, tint, metal) });

					vertex.material = remap.back().second;
				}
			}

			models.push_back(std::move(copy));

			materials.upload();

			return &models.back();
		}

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	structures::model_s* models_c::create(const char* name)
	{
		if (models.size() < maximum_models)
		{
			models.push_back({});

			std::snprintf(models.back().name, sizeof(models.back().name), "%s", name);

			models.back().bounds_min = { FLT_MAX, FLT_MAX, FLT_MAX };
			models.back().bounds_max = { -FLT_MAX, -FLT_MAX, -FLT_MAX };

			return &models.back();
		}

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	structures::model_s* models_c::existing(const char* name)
	{
		for (auto& model : models)
		{
			if (_stricmp(model.name, name) == 0)
			{
				return &model;
			}
		}

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t models_c::variant(std::uint32_t material, structures::vec3_s tint, std::float_t metal)
	{
		auto copy{ materials.gpu_materials[std::min<std::size_t>(material, materials.gpu_materials.size() - 1u)] };

		copy.tint = { copy.tint.x * tint.x, copy.tint.y * tint.y, copy.tint.z * tint.z, 1.0f };
		copy.metal_bias += metal;
		copy.roughness_scale *= 1.0f - metal * 0.5f;

		materials.gpu_materials.push_back(copy);

		return static_cast<std::uint32_t>(materials.gpu_materials.size() - 1u);
	}
	/*
	//=====================================================================================
	*/
	void models_c::begin_part(structures::model_s& model, const char* name)
	{
		structures::model_part_s part{};

		std::snprintf(part.name, sizeof(part.name), "%s", name);

		part.first_index = static_cast<std::uint32_t>(model.indices.size());
		part.bounds_min = { FLT_MAX, FLT_MAX, FLT_MAX };
		part.bounds_max = { -FLT_MAX, -FLT_MAX, -FLT_MAX };

		model.parts.push_back(part);
	}
	/*
	//=====================================================================================
	*/
	void models_c::append(structures::model_s& model, const structures::model_s& source, const structures::model_part_s& part, const structures::mat4_s& placement, std::uint32_t material, std::float_t keep, std::uint32_t salt)
	{
		std::unordered_map<std::uint32_t, std::uint32_t> remap;
		std::vector<std::uint32_t> roots;

		auto& target{ model.parts.back() };

		const auto end{ std::min(part.first_index + part.index_count, static_cast<std::uint32_t>(source.indices.size())) };

		const auto root = [&](std::uint32_t value)
			{
				while (roots[value] != value)
				{
					roots[value] = roots[roots[value]];

					value = roots[value];
				}

				return value;
			};

		if (keep < 1.0f)
		{
			roots.resize(source.vertices.size());

			for (auto index{ 0u }; index < roots.size(); index++)
			{
				roots[index] = index;
			}

			for (auto index{ part.first_index }; index + 2u < end; index += 3u)
			{
				const auto a{ root(source.indices[index]) };

				roots[root(source.indices[index + 1u])] = a;
				roots[root(source.indices[index + 2u])] = a;
			}
		}

		for (auto index{ part.first_index }; index + 2u < end; index += 3u)
		{
			if (keep >= 1.0f || mathematics.hash_float(root(source.indices[index]) ^ salt) < keep)
			{
				for (auto corner{ 0u }; corner < 3u; corner++)
				{
					const auto original{ source.indices[index + corner] };

					if (remap.find(original) == remap.end())
					{
						const auto& vertex{ source.vertices[original] };
						const auto position{ mathematics.transform_point(vertex.position, placement) };
						const auto tangent{ mathematics.normalize(mathematics.transform_vector(vertex.tangent.xyz(), placement)) };

						model.vertices.push_back({ position, mathematics.normalize(mathematics.transform_vector(vertex.normal, placement)), { tangent.x, tangent.y, tangent.z, vertex.tangent.w }, vertex.uv, material == UINT32_MAX ? vertex.material : material });

						target.bounds_min = mathematics.minimum(target.bounds_min, position);
						target.bounds_max = mathematics.maximum(target.bounds_max, position);

						remap[original] = static_cast<std::uint32_t>(model.vertices.size() - 1u);
					}

					model.indices.push_back(remap[original]);
				}
			}
		}

		target.index_count = static_cast<std::uint32_t>(model.indices.size()) - target.first_index;
	}
	/*
	//=====================================================================================
	*/
	void models_c::sphere(structures::model_s& model, structures::vec3_s center, std::float_t radius, std::uint32_t material)
	{
		const auto first{ static_cast<std::uint32_t>(model.vertices.size()) };

		auto& target{ model.parts.back() };

		for (auto ring{ 0u }; ring <= 5u; ring++)
		{
			const auto theta{ static_cast<std::float_t>(ring) / 5.0f * pi };

			for (auto segment{ 0u }; segment <= 7u; segment++)
			{
				const auto phi{ static_cast<std::float_t>(segment) / 7.0f * two_pi };
				const structures::vec3_s normal{ std::sin(theta) * std::cos(phi), std::cos(theta), std::sin(theta) * std::sin(phi) };

				model.vertices.push_back({ center + normal * radius, normal, { -std::sin(phi), 0.0f, std::cos(phi), 1.0f }, { phi / two_pi, theta / pi }, material });
			}
		}

		for (auto ring{ 0u }; ring < 5u; ring++)
		{
			for (auto segment{ 0u }; segment < 7u; segment++)
			{
				const auto a{ first + ring * 8u + segment };
				const auto b{ a + 8u };

				model.indices.insert(model.indices.end(), { a, a + 1u, b, a + 1u, b + 1u, b });
			}
		}

		target.bounds_min = mathematics.minimum(target.bounds_min, center - structures::vec3_s{ radius, radius, radius });
		target.bounds_max = mathematics.maximum(target.bounds_max, center + structures::vec3_s{ radius, radius, radius });
		target.index_count = static_cast<std::uint32_t>(model.indices.size()) - target.first_index;
	}
	/*
	//=====================================================================================
	*/
	void models_c::seal(structures::model_s& model)
	{
		for (const auto& part : model.parts)
		{
			model.bounds_min = mathematics.minimum(model.bounds_min, part.bounds_min);
			model.bounds_max = mathematics.maximum(model.bounds_max, part.bounds_max);
		}

		materials.upload();

		logger.write("models: assembled %s, %zu tris, %zu parts, size %.2f %.2f %.2f", model.name, model.indices.size() / 3u, model.parts.size(), model.bounds_max.x - model.bounds_min.x, model.bounds_max.y - model.bounds_min.y, model.bounds_max.z - model.bounds_min.z);
	}
	/*
	//=====================================================================================
	*/
	bool models_c::upload(structures::model_s& model)
	{
		if (model.mesh.vertex_buffer == nullptr && model.vertices.size())
		{
			model.mesh.vertex_buffer = gpu.create_buffer(static_cast<std::uint32_t>(model.vertices.size() * sizeof(structures::vertex_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, model.vertices.data(), 0u, 0u);
			model.mesh.index_buffer = gpu.create_buffer(static_cast<std::uint32_t>(model.indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, model.indices.data(), 0u, 0u);
			model.mesh.vertex_count = static_cast<std::uint32_t>(model.vertices.size());
			model.mesh.index_count = static_cast<std::uint32_t>(model.indices.size());
			model.mesh.bounds_min = model.bounds_min;
			model.mesh.bounds_max = model.bounds_max;
		}

		return model.mesh.vertex_buffer != nullptr || gpu.device == nullptr;
	}
}

//=====================================================================================
