
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_models_c baker_models;

	namespace baker
	{
		const json_s& json_s::get(const char* key) const
		{
			static const json_s empty{};

			for (auto index{ 0u }; index < keys.size(); index++)
			{
				if (keys[index] == key)
				{
					return items[index];
				}
			}

			return empty;
		}
		/*
		//=====================================================================================
		*/
		const json_s& json_s::at(std::size_t index) const
		{
			static const json_s empty{};

			if (index < items.size())
			{
				return items[index];
			}

			return empty;
		}
		/*
		//=====================================================================================
		*/
		std::double_t json_s::value(std::double_t fallback) const
		{
			if (type == json_number || type == json_boolean)
			{
				return number;
			}

			return fallback;
		}
		/*
		//=====================================================================================
		*/
		bool json_s::has(const char* key) const
		{
			return std::find(keys.begin(), keys.end(), std::string(key)) != keys.end();
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_json_c::parse(const std::string& text, baker::json_s& out)
	{
		cursor = text.data();
		end = cursor + text.size();

		return value(out);
	}
	/*
	//=====================================================================================
	*/
	void baker_json_c::skip()
	{
		while (cursor < end && (*cursor == ' ' || *cursor == '\n' || *cursor == '\r' || *cursor == '\t'))
		{
			cursor++;
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_json_c::string(std::string& out)
	{
		auto result{ false };

		out.clear();

		if (cursor < end && *cursor == '"')
		{
			cursor++;

			while (cursor < end && *cursor != '"')
			{
				if (*cursor == '\\' && cursor + 1 < end)
				{
					cursor++;

					const char escapes[][2] = { { 'n', '\n' }, { 't', '\t' }, { 'r', '\r' }, { 'b', '\b' }, { 'f', '\f' } };

					auto translated{ *cursor };

					for (const auto& escape : escapes)
					{
						if (*cursor == escape[0])
						{
							translated = escape[1];
						}
					}

					if (*cursor == 'u' && cursor + 4 < end)
					{
						translated = '?';

						cursor += 4;
					}

					out.push_back(translated);
				}

				else
				{
					out.push_back(*cursor);
				}

				cursor++;
			}

			if (cursor < end)
			{
				cursor++;

				result = true;
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool baker_json_c::value(baker::json_s& out)
	{
		auto result{ false };

		skip();

		out = {};

		if (cursor < end)
		{
			if (*cursor == '{')
			{
				out.type = baker::json_object;

				cursor++;

				skip();

				result = true;

				if (cursor < end && *cursor == '}')
				{
					cursor++;
				}

				else
				{
					auto open{ true };

					while (open && result)
					{
						std::string key;

						skip();

						baker::json_s member{};

						result = string(key);

						skip();

						result = result && cursor < end && *cursor == ':';

						if (result)
						{
							cursor++;

							result = value(member);

							out.keys.push_back(key);
							out.items.push_back(std::move(member));

							skip();

							if (cursor < end && *cursor == ',')
							{
								cursor++;
							}

							else if (cursor < end && *cursor == '}')
							{
								cursor++;

								open = false;
							}

							else
							{
								result = false;
							}
						}
					}
				}
			}

			else if (*cursor == '[')
			{
				out.type = baker::json_array;

				cursor++;

				skip();

				result = true;

				if (cursor < end && *cursor == ']')
				{
					cursor++;
				}

				else
				{
					auto open{ true };

					while (open && result)
					{
						baker::json_s element{};

						result = value(element);

						out.items.push_back(std::move(element));

						skip();

						if (cursor < end && *cursor == ',')
						{
							cursor++;
						}

						else if (cursor < end && *cursor == ']')
						{
							cursor++;

							open = false;
						}

						else
						{
							result = false;
						}
					}
				}
			}

			else if (*cursor == '"')
			{
				out.type = baker::json_string;

				result = string(out.text);
			}

			else if (end - cursor >= 4 && std::strncmp(cursor, "true", 4) == 0)
			{
				out.type = baker::json_boolean;
				out.number = 1.0;

				cursor += 4;

				result = true;
			}

			else if (end - cursor >= 5 && std::strncmp(cursor, "false", 5) == 0)
			{
				out.type = baker::json_boolean;
				out.number = 0.0;

				cursor += 5;

				result = true;
			}

			else if (end - cursor >= 4 && std::strncmp(cursor, "null", 4) == 0)
			{
				out.type = baker::json_null;

				cursor += 4;

				result = true;
			}

			else
			{
				char* number_end{ nullptr };

				out.type = baker::json_number;
				out.number = std::strtod(cursor, &number_end);

				result = number_end > cursor;

				cursor = number_end > cursor ? number_end : cursor;
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool baker_models_c::bake(const char* assets_directory)
	{
		const auto root{ std::string(assets_directory) + "\\raw\\models" };

		WIN32_FIND_DATAA found{};

		auto imported{ 0u };

		if (auto handle{ FindFirstFileA((root + "\\*").c_str(), &found) }; handle != INVALID_HANDLE_VALUE)
		{
			do
			{
				if ((found.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) && found.cFileName[0] != '.')
				{
					const auto directory{ root + "\\" + found.cFileName };

					WIN32_FIND_DATAA model_file{};

					if (auto model_handle{ FindFirstFileA((directory + "\\*.gltf").c_str(), &model_file) }; model_handle != INVALID_HANDLE_VALUE)
					{
						auto name{ std::string(found.cFileName) };

						std::transform(name.begin(), name.end(), name.begin(), [](char c) { return static_cast<char>(std::tolower(static_cast<unsigned char>(c))); });

						if (import(directory, directory + "\\" + model_file.cFileName, name))
						{
							imported++;
						}

						else
						{
							logger.write("baker: model %s failed to import", found.cFileName);
						}

						FindClose(model_handle);
					}
				}
			}
			while (FindNextFileA(handle, &found));

			FindClose(handle);
		}

		logger.write("baker: imported %u models, %zu material sets", imported, jobs_list.size());

		return true;
	}
	/*
	//=====================================================================================
	*/
	const std::uint8_t* baker_models_c::accessor(const baker::json_s& document, const std::vector<std::vector<std::uint8_t>>& buffers, std::uint32_t index, std::uint32_t& count, std::uint32_t& stride, std::uint32_t& component)
	{
		const auto& entry{ document.get("accessors").at(index) };
		const auto& view{ document.get("bufferViews").at(static_cast<std::size_t>(entry.get("bufferView").value(0.0))) };
		const auto buffer_index{ static_cast<std::size_t>(view.get("buffer").value(0.0)) };
		const auto offset{ static_cast<std::size_t>(view.get("byteOffset").value(0.0) + entry.get("byteOffset").value(0.0)) };
		const auto& kind{ entry.get("type").text };
		const auto components{ kind == "VEC2" ? 2u : (kind == "VEC3" ? 3u : (kind == "VEC4" ? 4u : 1u)) };

		component = static_cast<std::uint32_t>(entry.get("componentType").value(5126.0));
		count = static_cast<std::uint32_t>(entry.get("count").value(0.0));

		const auto component_size{ (component == 5126u || component == 5125u) ? 4u : (component == 5123u || component == 5122u ? 2u : 1u) };

		stride = static_cast<std::uint32_t>(view.get("byteStride").value(static_cast<std::double_t>(components * component_size)));

		if (buffer_index < buffers.size() && offset < buffers[buffer_index].size())
		{
			return buffers[buffer_index].data() + offset;
		}

		count = 0u;

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	void baker_models_c::visit(const baker::json_s& document, const std::vector<std::vector<std::uint8_t>>& buffers, std::uint32_t node_index, const std::array<std::double_t, 16>& parent, const std::string& name, std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts)
	{
		const auto& node{ document.get("nodes").at(node_index) };

		std::array<std::double_t, 16> local{ 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0 };

		if (node.has("matrix"))
		{
			for (auto index{ 0u }; index < 16u; index++)
			{
				local[index] = node.get("matrix").at(index).value(0.0);
			}
		}

		else
		{
			const auto& t{ node.get("translation") };
			const auto& r{ node.get("rotation") };
			const auto& s{ node.get("scale") };
			const auto qx{ r.at(0).value(0.0) }, qy{ r.at(1).value(0.0) }, qz{ r.at(2).value(0.0) }, qw{ r.at(3).value(1.0) };
			const auto sx{ s.at(0).value(1.0) }, sy{ s.at(1).value(1.0) }, sz{ s.at(2).value(1.0) };

			local = { (1.0 - 2.0 * (qy * qy + qz * qz)) * sx, (2.0 * (qx * qy + qz * qw)) * sx, (2.0 * (qx * qz - qy * qw)) * sx, 0.0, (2.0 * (qx * qy - qz * qw)) * sy, (1.0 - 2.0 * (qx * qx + qz * qz)) * sy, (2.0 * (qy * qz + qx * qw)) * sy, 0.0, (2.0 * (qx * qz + qy * qw)) * sz, (2.0 * (qy * qz - qx * qw)) * sz, (1.0 - 2.0 * (qx * qx + qy * qy)) * sz, 0.0, t.at(0).value(0.0), t.at(1).value(0.0), t.at(2).value(0.0), 1.0 };
		}

		std::array<std::double_t, 16> world{};

		for (auto column{ 0u }; column < 4u; column++)
		{
			for (auto row{ 0u }; row < 4u; row++)
			{
				world[column * 4u + row] = parent[0u * 4u + row] * local[column * 4u + 0u] + parent[1u * 4u + row] * local[column * 4u + 1u] + parent[2u * 4u + row] * local[column * 4u + 2u] + parent[3u * 4u + row] * local[column * 4u + 3u];
			}
		}

		if (node.has("mesh"))
		{
			const auto& mesh{ document.get("meshes").at(static_cast<std::size_t>(node.get("mesh").value(0.0))) };

			structures::model_part_s part{};

			std::snprintf(part.name, sizeof(part.name), "%s", node.has("name") ? node.get("name").text.c_str() : (name + "_" + std::to_string(parts.size())).c_str());

			const auto vertex_start{ vertices.size() };
			const auto marker{ std::any_of(std::begin(marker_prefixes), std::end(marker_prefixes), [&](const char* prefix) { return std::strncmp(part.name, prefix, std::strlen(prefix)) == 0; }) };

			part.first_index = static_cast<std::uint32_t>(indices.size());
			part.bounds_min = { FLT_MAX, FLT_MAX, FLT_MAX };
			part.bounds_max = { -FLT_MAX, -FLT_MAX, -FLT_MAX };

			for (const auto& primitive : mesh.get("primitives").items)
			{
				const auto& attributes{ primitive.get("attributes") };

				if (attributes.has("POSITION") && attributes.has("TEXCOORD_0"))
				{
					std::uint32_t position_count{ 0u }, position_stride{ 0u }, position_type{ 0u };
					std::uint32_t normal_count{ 0u }, normal_stride{ 0u }, normal_type{ 0u };
					std::uint32_t uv_count{ 0u }, uv_stride{ 0u }, uv_type{ 0u };

					const auto positions{ accessor(document, buffers, static_cast<std::uint32_t>(attributes.get("POSITION").value(0.0)), position_count, position_stride, position_type) };
					const auto normals{ attributes.has("NORMAL") ? accessor(document, buffers, static_cast<std::uint32_t>(attributes.get("NORMAL").value(0.0)), normal_count, normal_stride, normal_type) : nullptr };
					const auto uvs{ accessor(document, buffers, static_cast<std::uint32_t>(attributes.get("TEXCOORD_0").value(0.0)), uv_count, uv_stride, uv_type) };
					const auto material{ static_cast<std::uint32_t>(primitive.get("material").value(0.0)) };
					const auto base{ static_cast<std::uint32_t>(vertices.size()) };
					const auto& transform{ document.get("materials").at(material).get("pbrMetallicRoughness").get("baseColorTexture").get("extensions").get("KHR_texture_transform") };
					const auto uv_scale_x{ transform.get("scale").at(0).value(1.0) };
					const auto uv_scale_y{ transform.get("scale").at(1).value(1.0) };
					const auto uv_offset_x{ transform.get("offset").at(0).value(0.0) };
					const auto uv_offset_y{ transform.get("offset").at(1).value(0.0) };

					if (positions && uvs && position_type == 5126u && uv_type == 5126u)
					{
						for (auto vertex{ 0u }; vertex < position_count; vertex++)
						{
							const auto p{ reinterpret_cast<const std::float_t*>(positions + static_cast<std::size_t>(vertex) * position_stride) };
							const auto t{ reinterpret_cast<const std::float_t*>(uvs + static_cast<std::size_t>(vertex) * uv_stride) };

							structures::vec3_s normal{ 0.0f, 1.0f, 0.0f };

							if (normals && vertex < normal_count)
							{
								const auto n{ reinterpret_cast<const std::float_t*>(normals + static_cast<std::size_t>(vertex) * normal_stride) };

								normal = { static_cast<std::float_t>(world[0] * n[0] + world[4] * n[1] + world[8] * n[2]), static_cast<std::float_t>(world[1] * n[0] + world[5] * n[1] + world[9] * n[2]), static_cast<std::float_t>(world[2] * n[0] + world[6] * n[1] + world[10] * n[2]) };
							}

							const structures::vec3_s position{ static_cast<std::float_t>(world[0] * p[0] + world[4] * p[1] + world[8] * p[2] + world[12]), static_cast<std::float_t>(world[1] * p[0] + world[5] * p[1] + world[9] * p[2] + world[13]), static_cast<std::float_t>(world[2] * p[0] + world[6] * p[1] + world[10] * p[2] + world[14]) };
							const structures::vec3_s converted{ position.x, position.y, -position.z };
							const auto unit{ mathematics.normalize(normal) };

							vertices.push_back({ converted, { unit.x, unit.y, -unit.z }, { static_cast<std::float_t>(t[0] * uv_scale_x + uv_offset_x), static_cast<std::float_t>(t[1] * uv_scale_y + uv_offset_y) }, material });

							part.bounds_min = mathematics.minimum(part.bounds_min, converted);
							part.bounds_max = mathematics.maximum(part.bounds_max, converted);
						}

						if (primitive.has("indices"))
						{
							std::uint32_t index_count{ 0u }, index_stride{ 0u }, index_type{ 0u };

							const auto index_data{ accessor(document, buffers, static_cast<std::uint32_t>(primitive.get("indices").value(0.0)), index_count, index_stride, index_type) };

							for (auto triangle{ 0u }; index_data && triangle + 2u < index_count; triangle += 3u)
							{
								std::uint32_t corners[3]{};

								for (auto corner{ 0u }; corner < 3u; corner++)
								{
									const auto element{ index_data + static_cast<std::size_t>(triangle + corner) * index_stride };

									corners[corner] = index_type == 5125u ? *reinterpret_cast<const std::uint32_t*>(element) : (index_type == 5123u ? *reinterpret_cast<const std::uint16_t*>(element) : *element);
								}

								indices.push_back(base + corners[0]);
								indices.push_back(base + corners[2]);
								indices.push_back(base + corners[1]);
							}
						}

						else
						{
							for (auto triangle{ 0u }; triangle + 2u < position_count; triangle += 3u)
							{
								indices.push_back(base + triangle);
								indices.push_back(base + triangle + 2u);
								indices.push_back(base + triangle + 1u);
							}
						}
					}
				}
			}

			part.index_count = static_cast<std::uint32_t>(indices.size()) - part.first_index;

			if (marker && part.index_count)
			{
				indices.resize(part.first_index);
				vertices.resize(vertex_start);

				part.index_count = 0u;

				parts.push_back(part);
			}

			else if (part.index_count)
			{
				parts.push_back(part);
			}
		}

		for (const auto& child : node.get("children").items)
		{
			visit(document, buffers, static_cast<std::uint32_t>(child.value(0.0)), world, name, vertices, indices, parts);
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_models_c::open(const std::string& directory, const std::string& file, baker::json_s& document, std::vector<std::vector<std::uint8_t>>& buffers)
	{
		std::vector<std::uint8_t> bytes;

		auto result{ false };

		if (functions::read_file(file.c_str(), bytes))
		{
			baker_json_c parser{};

			if (parser.parse(std::string(bytes.begin(), bytes.end()), document))
			{
				for (const auto& buffer : document.get("buffers").items)
				{
					buffers.emplace_back();

					functions::read_file((directory + "\\" + decode_uri(buffer.get("uri").text)).c_str(), buffers.back());
				}

				result = true;
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::string baker_models_c::canonical(const std::string& path)
	{
		char full[MAX_PATH]{};

		return GetFullPathNameA(path.c_str(), MAX_PATH, full, nullptr) ? std::string{ full } : path;
	}
	/*
	//=====================================================================================
	*/
	std::string baker_models_c::decode_uri(const std::string& uri)
	{
		std::string decoded;

		for (auto index{ 0u }; index < uri.size(); index++)
		{
			if (uri[index] == '%' && index + 2u < uri.size())
			{
				decoded.push_back(static_cast<char>(std::strtol(uri.substr(index + 1u, 2u).c_str(), nullptr, 16)));

				index += 2u;
			}

			else
			{
				decoded.push_back(uri[index] == '/' ? '\\' : uri[index]);
			}
		}

		return decoded;
	}
	/*
	//=====================================================================================
	*/
	void baker_models_c::collect_materials(const baker::json_s& document, const std::string& directory, const std::string& name, std::vector<structures::model_material_s>& model_materials)
	{
		const auto image_path = [&](const baker::json_s& texture_reference)
			{
				std::string path;

				if (texture_reference.has("index"))
				{
					const auto& texture{ document.get("textures").at(static_cast<std::size_t>(texture_reference.get("index").value(0.0))) };
					const auto& image{ document.get("images").at(static_cast<std::size_t>(texture.get("source").value(0.0))) };

					path = canonical(directory + "\\" + decode_uri(image.get("uri").text));
				}

				return path;
			};

		const auto material_count{ std::max<std::size_t>(1u, document.get("materials").items.size()) };

		for (auto index{ 0u }; index < material_count; index++)
		{
			const auto& material{ document.get("materials").at(index) };
			const auto& pbr{ material.get("pbrMetallicRoughness") };
			const auto& base_factor{ pbr.get("baseColorFactor") };
			const auto alpha_mode{ material.get("alphaMode").text };
			const auto emissive_strength{ material.get("extensions").get("KHR_materials_emissive_strength").get("emissiveStrength").value(1.0) };
			const auto transmission{ material.get("extensions").has("KHR_materials_transmission") };
			const auto albedo_path{ image_path(pbr.get("baseColorTexture")) };

			baker::model_texture_job_s job{};

			job.set_name = name + "#" + std::to_string(index);
			job.albedo = albedo_path;
			job.normal = image_path(material.get("normalTexture"));
			job.rough_metal = image_path(pbr.get("metallicRoughnessTexture"));
			job.occlusion = image_path(material.get("occlusionTexture"));
			job.base_factor = { static_cast<std::float_t>(base_factor.at(0).value(1.0)), static_cast<std::float_t>(base_factor.at(1).value(1.0)), static_cast<std::float_t>(base_factor.at(2).value(1.0)), static_cast<std::float_t>(base_factor.at(3).value(1.0)) };
			job.roughness_factor = static_cast<std::float_t>(pbr.get("roughnessFactor").value(1.0));
			job.metal_factor = static_cast<std::float_t>(pbr.get("metallicFactor").value(1.0));
			job.alpha = (alpha_mode == "MASK" || alpha_mode == "BLEND") && albedo_path.size() && transmission == false;

			if (const auto marker{ albedo_path.rfind("_diff_") }; job.alpha && marker != std::string::npos)
			{
				const auto mask_path{ albedo_path.substr(0u, marker) + "_alpha_" + albedo_path.substr(marker + 6u) };

				job.alpha_mask = GetFileAttributesA(mask_path.c_str()) != INVALID_FILE_ATTRIBUTES ? mask_path : std::string{};
			}

			structures::model_material_s entry{};

			std::snprintf(entry.set_name, sizeof(entry.set_name), "%s", job.set_name.c_str());

			const auto& emissive{ material.get("emissiveFactor") };

			entry.emissive = { static_cast<std::float_t>(emissive.at(0).value(0.0) * emissive_strength), static_cast<std::float_t>(emissive.at(1).value(0.0) * emissive_strength), static_cast<std::float_t>(emissive.at(2).value(0.0) * emissive_strength) };
			entry.flags = (job.alpha ? structures::material_flag_alpha_test : 0u) | ((alpha_mode == "BLEND" && job.alpha == false) ? structures::material_flag_glass : 0u) | (mathematics.length(entry.emissive) > 0.01f ? structures::material_flag_unlit : 0u) | (material.get("doubleSided").value(0.0) > 0.5 ? structures::material_flag_two_sided : 0u);
			entry.roughness_scale = 1.0f;
			entry.metal_scale = 1.0f;

			const auto shared{ std::find_if(jobs_list.begin(), jobs_list.end(), [&](const baker::model_texture_job_s& other) { return job.albedo.size() && other.albedo == job.albedo && other.normal == job.normal && other.rough_metal == job.rough_metal && other.occlusion == job.occlusion && other.alpha == job.alpha && other.alpha_mask == job.alpha_mask && other.base_factor.x == job.base_factor.x && other.base_factor.y == job.base_factor.y && other.base_factor.z == job.base_factor.z && other.roughness_factor == job.roughness_factor && other.metal_factor == job.metal_factor; }) };

			if (shared != jobs_list.end())
			{
				std::snprintf(entry.set_name, sizeof(entry.set_name), "%s", shared->set_name.c_str());
			}

			else
			{
				jobs_list.push_back(job);
			}

			model_materials.push_back(entry);
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_models_c::tangents(const std::vector<baker::model_vertex_s>& vertices, const std::vector<std::uint32_t>& indices, std::vector<structures::vec4_s>& out)
	{
		std::vector<structures::vec3_s> tangent_sums(vertices.size());
		std::vector<structures::vec3_s> bitangent_sums(vertices.size());

		for (auto triangle{ 0u }; triangle + 2u < indices.size(); triangle += 3u)
		{
			const auto& v0{ vertices[indices[triangle]] };
			const auto& v1{ vertices[indices[triangle + 1u]] };
			const auto& v2{ vertices[indices[triangle + 2u]] };
			const auto edge1{ v1.position - v0.position };
			const auto edge2{ v2.position - v0.position };
			const auto du1{ v1.uv.x - v0.uv.x }, dv1{ v1.uv.y - v0.uv.y }, du2{ v2.uv.x - v0.uv.x }, dv2{ v2.uv.y - v0.uv.y };

			if (const auto determinant{ du1 * dv2 - du2 * dv1 }; std::fabs(determinant) > 1e-12f)
			{
				const auto tangent{ (edge1 * dv2 - edge2 * dv1) / determinant };
				const auto bitangent{ (edge2 * du1 - edge1 * du2) / determinant };

				for (auto corner{ 0u }; corner < 3u; corner++)
				{
					tangent_sums[indices[triangle + corner]] += tangent;
					bitangent_sums[indices[triangle + corner]] += bitangent;
				}
			}
		}

		out.resize(vertices.size());

		for (auto index{ 0u }; index < vertices.size(); index++)
		{
			const auto& source{ vertices[index] };

			auto tangent{ mathematics.normalize(tangent_sums[index] - source.normal * mathematics.dot(source.normal, tangent_sums[index])) };

			if (mathematics.length_squared(tangent) < 0.5f)
			{
				tangent = mathematics.any_perpendicular(source.normal);
			}

			out[index] = { tangent.x, tangent.y, tangent.z, mathematics.dot(mathematics.cross(source.normal, tangent), bitangent_sums[index]) < 0.0f ? -1.0f : 1.0f };
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_models_c::import(const std::string& directory, const std::string& file, const std::string& name)
	{
		baker::json_s document{};
		std::vector<std::vector<std::uint8_t>> buffers;

		auto result{ false };

		if (open(directory, file, document, buffers))
		{
			std::vector<structures::model_material_s> model_materials;

			collect_materials(document, directory, name, model_materials);

			std::vector<baker::model_vertex_s> vertices;
			std::vector<std::uint32_t> indices;
			std::vector<structures::model_part_s> parts;

			const std::array<std::double_t, 16> identity{ 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0 };
			const auto& scene{ document.get("scenes").at(static_cast<std::size_t>(document.get("scene").value(0.0))) };

			for (const auto& root : scene.get("nodes").items)
			{
				visit(document, buffers, static_cast<std::uint32_t>(root.value(0.0)), identity, name, vertices, indices, parts);
			}

			const auto original_triangles{ indices.size() / 3u };
			const auto lod{ std::find_if(std::begin(baker::lod_models), std::end(baker::lod_models), [&](const baker::lod_model_s& entry) { return name == entry.name; }) };

			if (vertices.size() && indices.size() && std::none_of(std::begin(baker::detailed_models), std::end(baker::detailed_models), [&](const char* detailed) { return name == detailed; }) && std::none_of(std::begin(baker::detailed_prefixes), std::end(baker::detailed_prefixes), [&](const char* prefix) { return name.rfind(prefix, 0u) == 0u; }))
			{
				baker_simplifier.simplify(vertices, indices, parts);
			}

			if (lod != std::end(baker::lod_models) && indices.size() / 3u > lod->near_budget)
			{
				baker_simplifier.reduce(vertices, indices, parts, lod->near_budget);
			}

			if (vertices.size() && indices.size())
			{
				write_model(name, vertices, indices, parts, model_materials);

				logger.write("baker:   simplified from %zu tris", original_triangles);

				if (lod != std::end(baker::lod_models))
				{
					auto far_vertices{ vertices };
					auto far_indices{ indices };
					auto far_parts{ parts };

					baker_simplifier.reduce(far_vertices, far_indices, far_parts, lod->far_budget);

					write_model(name + "_far", far_vertices, far_indices, far_parts, model_materials);
				}

				result = true;
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_models_c::write_model(const std::string& name, const std::vector<baker::model_vertex_s>& vertices, const std::vector<std::uint32_t>& indices, const std::vector<structures::model_part_s>& parts, const std::vector<structures::model_material_s>& model_materials)
	{
		std::vector<structures::vertex_s> finished(vertices.size());
		std::vector<structures::vec4_s> vertex_tangents;

		tangents(vertices, indices, vertex_tangents);

		structures::model_header_s header{ static_cast<std::uint32_t>(parts.size()), static_cast<std::uint32_t>(vertices.size()), static_cast<std::uint32_t>(indices.size()), static_cast<std::uint32_t>(model_materials.size()), { FLT_MAX, FLT_MAX, FLT_MAX }, { -FLT_MAX, -FLT_MAX, -FLT_MAX } };

		for (auto index{ 0u }; index < vertices.size(); index++)
		{
			const auto& source{ vertices[index] };

			finished[index] = { source.position, source.normal, vertex_tangents[index], source.uv, source.material };

			header.bounds_min = mathematics.minimum(header.bounds_min, source.position);
			header.bounds_max = mathematics.maximum(header.bounds_max, source.position);
		}

		baker::pak_item_s item{};

		std::snprintf(item.entry.name, sizeof(item.entry.name), "model_%s", name.c_str());

		item.entry.type = structures::pak_type_blob;
		item.entry.layers = static_cast<std::uint32_t>(parts.size());

		append(item, &header, sizeof(header));
		append(item, parts.data(), parts.size() * sizeof(structures::model_part_s));
		append(item, model_materials.data(), model_materials.size() * sizeof(structures::model_material_s));
		append(item, finished.data(), finished.size() * sizeof(structures::vertex_s));
		append(item, indices.data(), indices.size() * sizeof(std::uint32_t));

		items.push_back(std::move(item));

		logger.write("baker: model %-32s %6zu tris %3zu parts %zu materials size %.3f %.3f %.3f", name.c_str(), indices.size() / 3u, parts.size(), model_materials.size(), header.bounds_max.x - header.bounds_min.x, header.bounds_max.y - header.bounds_min.y, header.bounds_max.z - header.bounds_min.z);

		for (const auto& part : parts)
		{
			logger.write("baker:   part %-48s size %.3f %.3f %.3f min %.3f %.3f %.3f", part.name, part.bounds_max.x - part.bounds_min.x, part.bounds_max.y - part.bounds_min.y, part.bounds_max.z - part.bounds_min.z, part.bounds_min.x, part.bounds_min.y, part.bounds_min.z);
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_models_c::append(baker::pak_item_s& item, const void* data, std::size_t size)
	{
		item.data.insert(item.data.end(), static_cast<const std::uint8_t*>(data), static_cast<const std::uint8_t*>(data) + size);
	}
	/*
	//=====================================================================================
	*/
	bool baker_models_c::load_channel(const std::string& path, baker::image_s& out)
	{
		auto result{ false };

		if (path.size() && baker_images.load(path.c_str(), out))
		{
			baker_images.resize(out, material_texture_size, material_texture_size);

			result = true;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_models_c::bake_materials(std::vector<baker::material_output_s>& outputs)
	{
		const auto offset{ outputs.size() };

		outputs.resize(offset + jobs_list.size());

		jobs.parallel_for(static_cast<std::uint32_t>(jobs_list.size()), [&](std::uint32_t index)
			{
				const auto& job{ jobs_list[index] };
				const auto count{ static_cast<std::size_t>(material_texture_size) * material_texture_size };

				baker::image_s albedo{}, normal{}, rough_metal{}, occlusion{}, mask{};
				baker::material_source_s source{};

				const auto has_albedo{ load_channel(job.albedo, albedo) };
				const auto has_normal{ load_channel(job.normal, normal) };
				const auto has_rough_metal{ load_channel(job.rough_metal, rough_metal) };
				const auto has_occlusion{ load_channel(job.occlusion, occlusion) };
				const auto has_mask{ load_channel(job.alpha_mask, mask) };

				source.size = material_texture_size;
				source.aspect = 1.0f;
				source.albedo.resize(count);
				source.normal.resize(count);
				source.roughness.resize(count);
				source.occlusion.resize(count);
				source.height.assign(count, 0.5f);
				source.metal.resize(count);

				if (job.alpha)
				{
					source.alpha.resize(count);
				}

				for (auto pixel{ 0u }; pixel < count; pixel++)
				{
					const auto base{ has_albedo ? albedo.pixels[pixel] : structures::vec4_s{ 1.0f, 1.0f, 1.0f, 1.0f } };
					const auto encoded{ has_normal ? normal.pixels[pixel] : structures::vec4_s{ 0.5f, 0.5f, 1.0f, 1.0f } };
					const auto surface{ has_rough_metal ? rough_metal.pixels[pixel] : structures::vec4_s{ 1.0f, 1.0f, 1.0f, 1.0f } };

					source.albedo[pixel] = { baker_images.srgb_to_linear(base.x) * job.base_factor.x, baker_images.srgb_to_linear(base.y) * job.base_factor.y, baker_images.srgb_to_linear(base.z) * job.base_factor.z };
					source.normal[pixel] = mathematics.normalize({ encoded.x * 2.0f - 1.0f, 1.0f - encoded.y * 2.0f, encoded.z * 2.0f - 1.0f });
					source.roughness[pixel] = std::clamp(surface.y * job.roughness_factor, 0.0f, 1.0f);
					source.metal[pixel] = std::clamp(surface.z * job.metal_factor, 0.0f, 1.0f);
					source.occlusion[pixel] = has_occlusion ? occlusion.pixels[pixel].x : 1.0f;

					if (job.alpha)
					{
						source.alpha[pixel] = (has_mask ? mask.pixels[pixel].x : base.w) * job.base_factor.w;
					}
				}

				baker_materials.finish(job.set_name.c_str(), false, source, outputs[offset + index]);

				outputs[offset + index].record.height_scale = 0.0f;
			});
	}
}

//=====================================================================================
