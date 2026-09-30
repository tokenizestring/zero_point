
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_characters_c baker_characters;

	bool baker_characters_c::bake(const char* assets_directory)
	{
		const auto character_root{ std::string(assets_directory) + "\\raw\\characters" };
		const auto clip_root{ std::string(assets_directory) + "\\raw\\animations" };

		WIN32_FIND_DATAA found{};

		if (auto handle{ FindFirstFileA((character_root + "\\*").c_str(), &found) }; handle != INVALID_HANDLE_VALUE)
		{
			do
			{
				if ((found.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) && found.cFileName[0] != '.')
				{
					const auto directory{ character_root + "\\" + found.cFileName };

					import_character(directory, directory + "\\" + found.cFileName + ".gltf", found.cFileName);
				}
			}
			while (FindNextFileA(handle, &found));

			FindClose(handle);
		}

		if (auto handle{ FindFirstFileA((clip_root + "\\*.gltf").c_str(), &found) }; handle != INVALID_HANDLE_VALUE)
		{
			do
			{
				const auto name{ std::string(found.cFileName) };

				import_clip(clip_root, clip_root + "\\" + name, name.substr(0u, name.size() - 5u));
			}
			while (FindNextFileA(handle, &found));

			FindClose(handle);
		}

		logger.write("baker: %zu character and clip entries", items.size());

		return true;
	}
	/*
	//=====================================================================================
	*/
	bool baker_characters_c::import_character(const std::string& directory, const std::string& file, const std::string& name)
	{
		baker::json_s document{};
		std::vector<std::vector<std::uint8_t>> buffers;

		auto result{ false };

		if (baker_models.open(directory, file, document, buffers) && document.get("skins").items.size())
		{
			std::vector<structures::model_material_s> model_materials;

			baker_models.collect_materials(document, directory, "character_" + name, model_materials);

			const auto& nodes{ document.get("nodes").items };
			const auto& skin{ document.get("skins").at(0) };

			std::vector<std::int32_t> node_parent(nodes.size(), -1);
			std::vector<std::uint8_t> needed(nodes.size(), 0u);
			std::vector<std::int32_t> bone_of_node(nodes.size(), -1);
			std::vector<std::uint32_t> order;

			for (auto node{ 0u }; node < nodes.size(); node++)
			{
				for (const auto& child : nodes[node].get("children").items)
				{
					node_parent[static_cast<std::size_t>(child.value(0.0))] = static_cast<std::int32_t>(node);
				}
			}

			for (const auto& joint : skin.get("joints").items)
			{
				for (auto walk{ static_cast<std::int32_t>(joint.value(0.0)) }; walk >= 0; walk = node_parent[walk])
				{
					needed[walk] = 1u;
				}
			}

			std::vector<std::uint32_t> stack;

			for (const auto& root : document.get("scenes").at(static_cast<std::size_t>(document.get("scene").value(0.0))).get("nodes").items)
			{
				stack.push_back(static_cast<std::uint32_t>(root.value(0.0)));
			}

			while (stack.size())
			{
				const auto node{ stack.back() };

				stack.pop_back();

				if (needed[node])
				{
					bone_of_node[node] = static_cast<std::int32_t>(order.size());

					order.push_back(node);
				}

				for (const auto& child : nodes[node].get("children").items)
				{
					stack.push_back(static_cast<std::uint32_t>(child.value(0.0)));
				}
			}

			std::vector<structures::character_bone_s> bones(order.size());

			for (auto bone{ 0u }; bone < order.size(); bone++)
			{
				const auto& node{ nodes[order[bone]] };

				std::snprintf(bones[bone].name, sizeof(bones[bone].name), "%s", node.get("name").text.c_str());

				bones[bone].parent = node_parent[order[bone]] >= 0 ? bone_of_node[node_parent[order[bone]]] : -1;
				bones[bone].inverse_bind = mathematics.identity();

				node_transform(node, bones[bone].translation, bones[bone].rotation, bones[bone].scale);
			}

			std::uint32_t matrix_count{ 0u }, matrix_components{ 0u };

			const auto matrices{ read_floats(document, buffers, static_cast<std::uint32_t>(skin.get("inverseBindMatrices").value(0.0)), matrix_count, matrix_components) };

			for (auto joint{ 0u }; joint < skin.get("joints").items.size() && joint < matrix_count; joint++)
			{
				if (const auto bone{ bone_of_node[static_cast<std::size_t>(skin.get("joints").at(joint).value(0.0))] }; bone >= 0)
				{
					bones[bone].inverse_bind = convert_matrix(&matrices[static_cast<std::size_t>(joint) * 16u]);
				}
			}

			std::vector<baker::model_vertex_s> vertices;
			std::vector<std::uint32_t> joints;
			std::vector<std::uint32_t> weights;
			std::vector<std::uint32_t> opaque;
			std::vector<std::uint32_t> alpha;

			for (const auto& node : nodes)
			{
				if (node.has("mesh") && node.has("skin"))
				{
					for (const auto& primitive : document.get("meshes").at(static_cast<std::size_t>(node.get("mesh").value(0.0))).get("primitives").items)
					{
						const auto& attributes{ primitive.get("attributes") };
						const auto material{ static_cast<std::uint32_t>(primitive.get("material").value(0.0)) };
						const auto base{ static_cast<std::uint32_t>(vertices.size()) };

						std::uint32_t count{ 0u }, components{ 0u }, normal_count{ 0u }, normal_components{ 0u }, uv_count{ 0u }, uv_components{ 0u }, joint_count{ 0u }, joint_components{ 0u }, weight_count{ 0u }, weight_components{ 0u }, index_count{ 0u }, index_components{ 0u };

						const auto positions{ read_floats(document, buffers, static_cast<std::uint32_t>(attributes.get("POSITION").value(0.0)), count, components) };
						const auto normals{ read_floats(document, buffers, static_cast<std::uint32_t>(attributes.get("NORMAL").value(0.0)), normal_count, normal_components) };
						const auto uvs{ read_floats(document, buffers, static_cast<std::uint32_t>(attributes.get("TEXCOORD_0").value(0.0)), uv_count, uv_components) };
						const auto joint_values{ read_floats(document, buffers, static_cast<std::uint32_t>(attributes.get("JOINTS_0").value(0.0)), joint_count, joint_components) };
						const auto weight_values{ read_floats(document, buffers, static_cast<std::uint32_t>(attributes.get("WEIGHTS_0").value(0.0)), weight_count, weight_components) };
						const auto index_values{ read_floats(document, buffers, static_cast<std::uint32_t>(primitive.get("indices").value(0.0)), index_count, index_components) };

						if (count && normal_count == count && uv_count == count && joint_count == count && weight_count == count)
						{
							for (auto vertex{ 0u }; vertex < count; vertex++)
							{
								const auto p{ &positions[static_cast<std::size_t>(vertex) * 3u] };
								const auto n{ &normals[static_cast<std::size_t>(vertex) * 3u] };
								const auto t{ &uvs[static_cast<std::size_t>(vertex) * 2u] };

								vertices.push_back({ { p[0], p[1], -p[2] }, mathematics.normalize({ n[0], n[1], -n[2] }), { t[0], t[1] }, material });

								std::uint32_t packed_joints{ 0u };
								std::float_t influence[4]{};
								std::float_t total{ 0.0f };

								for (auto slot{ 0u }; slot < 4u; slot++)
								{
									const auto joint{ static_cast<std::size_t>(joint_values[static_cast<std::size_t>(vertex) * 4u + slot]) };
									const auto bone{ joint < skin.get("joints").items.size() ? bone_of_node[static_cast<std::size_t>(skin.get("joints").at(joint).value(0.0))] : 0 };

									packed_joints |= static_cast<std::uint32_t>(std::max(bone, 0)) << (slot * 8u);

									influence[slot] = std::max(0.0f, weight_values[static_cast<std::size_t>(vertex) * 4u + slot]);

									total += influence[slot];
								}

								std::uint32_t quantized[4]{};
								std::uint32_t sum{ 0u };
								std::uint32_t heaviest{ 0u };

								for (auto slot{ 0u }; slot < 4u; slot++)
								{
									quantized[slot] = static_cast<std::uint32_t>(std::round(influence[slot] / std::max(total, 1e-6f) * 255.0f));

									sum += quantized[slot];

									heaviest = influence[slot] > influence[heaviest] ? slot : heaviest;
								}

								quantized[heaviest] = static_cast<std::uint32_t>(std::clamp(static_cast<std::int32_t>(quantized[heaviest]) + 255 - static_cast<std::int32_t>(sum), 0, 255));

								joints.push_back(packed_joints);
								weights.push_back(quantized[0] | (quantized[1] << 8u) | (quantized[2] << 16u) | (quantized[3] << 24u));
							}

							auto& target{ material < model_materials.size() && (model_materials[material].flags & structures::material_flag_alpha_test) ? alpha : opaque };

							for (auto triangle{ 0u }; triangle + 2u < index_count; triangle += 3u)
							{
								target.push_back(base + static_cast<std::uint32_t>(index_values[triangle]));
								target.push_back(base + static_cast<std::uint32_t>(index_values[triangle + 2u]));
								target.push_back(base + static_cast<std::uint32_t>(index_values[triangle + 1u]));
							}
						}
					}
				}
			}

			if (vertices.size() && opaque.size() + alpha.size())
			{
				std::vector<std::uint32_t> indices{ opaque };

				indices.insert(indices.end(), alpha.begin(), alpha.end());

				std::vector<structures::vec4_s> vertex_tangents;

				baker_models.tangents(vertices, indices, vertex_tangents);

				std::vector<structures::skinned_vertex_s> finished(vertices.size());

				structures::character_header_s header{ static_cast<std::uint32_t>(bones.size()), static_cast<std::uint32_t>(vertices.size()), static_cast<std::uint32_t>(indices.size()), static_cast<std::uint32_t>(model_materials.size()), static_cast<std::uint32_t>(opaque.size()), { FLT_MAX, FLT_MAX, FLT_MAX }, { -FLT_MAX, -FLT_MAX, -FLT_MAX } };

				for (auto index{ 0u }; index < vertices.size(); index++)
				{
					finished[index] = { vertices[index].position, vertices[index].normal, vertex_tangents[index], vertices[index].uv, vertices[index].material, joints[index], weights[index] };

					header.bounds_min = mathematics.minimum(header.bounds_min, vertices[index].position);
					header.bounds_max = mathematics.maximum(header.bounds_max, vertices[index].position);
				}

				baker::pak_item_s item{};

				std::snprintf(item.entry.name, sizeof(item.entry.name), "character_%s", name.c_str());

				item.entry.type = structures::pak_type_blob;

				baker_models.append(item, &header, sizeof(header));
				baker_models.append(item, bones.data(), bones.size() * sizeof(structures::character_bone_s));
				baker_models.append(item, model_materials.data(), model_materials.size() * sizeof(structures::model_material_s));
				baker_models.append(item, finished.data(), finished.size() * sizeof(structures::skinned_vertex_s));
				baker_models.append(item, indices.data(), indices.size() * sizeof(std::uint32_t));

				items.push_back(std::move(item));

				logger.write("baker: character %-24s %zu bones %zu vertices %zu tris (%zu alpha) %zu materials height %.2f%s", name.c_str(), bones.size(), vertices.size(), indices.size() / 3u, alpha.size() / 3u, model_materials.size(), header.bounds_max.y - header.bounds_min.y, bones.size() > maximum_bones ? ", over the bone limit" : "");

				result = true;
			}
		}

		if (result == false)
		{
			logger.write("baker: character %s was not imported", name.c_str());
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool baker_characters_c::import_clip(const std::string& directory, const std::string& file, const std::string& name)
	{
		baker::json_s document{};
		std::vector<std::vector<std::uint8_t>> buffers;

		auto result{ false };

		if (baker_models.open(directory, file, document, buffers) && document.get("animations").items.size())
		{
			const auto& nodes{ document.get("nodes").items };
			const auto& animation{ document.get("animations").at(0) };

			std::vector<std::int32_t> node_parent(nodes.size(), -1);
			std::vector<std::int32_t> translation_sampler(nodes.size(), -1);
			std::vector<std::int32_t> rotation_sampler(nodes.size(), -1);
			std::vector<std::uint32_t> track_nodes;

			for (auto node{ 0u }; node < nodes.size(); node++)
			{
				for (const auto& child : nodes[node].get("children").items)
				{
					node_parent[static_cast<std::size_t>(child.value(0.0))] = static_cast<std::int32_t>(node);
				}
			}

			for (const auto& channel : animation.get("channels").items)
			{
				const auto node{ static_cast<std::size_t>(channel.get("target").get("node").value(0.0)) };
				const auto& path{ channel.get("target").get("path").text };

				if (path == "translation")
				{
					translation_sampler[node] = static_cast<std::int32_t>(channel.get("sampler").value(0.0));
				}

				else if (path == "rotation")
				{
					rotation_sampler[node] = static_cast<std::int32_t>(channel.get("sampler").value(0.0));
				}
			}

			auto start{ FLT_MAX };
			auto end{ -FLT_MAX };

			for (auto node{ 0u }; node < nodes.size(); node++)
			{
				if (translation_sampler[node] >= 0 || rotation_sampler[node] >= 0)
				{
					track_nodes.push_back(node);
				}
			}

			std::vector<baker::clip_sampler_s> samplers(animation.get("samplers").items.size());

			for (auto index{ 0u }; index < samplers.size(); index++)
			{
				const auto& sampler{ animation.get("samplers").at(index) };

				std::uint32_t count{ 0u }, components{ 0u };

				samplers[index].times = read_floats(document, buffers, static_cast<std::uint32_t>(sampler.get("input").value(0.0)), count, components);
				samplers[index].values = read_floats(document, buffers, static_cast<std::uint32_t>(sampler.get("output").value(0.0)), count, samplers[index].components);
				samplers[index].cubic = sampler.get("interpolation").text == "CUBICSPLINE";
				samplers[index].step = sampler.get("interpolation").text == "STEP";

				if (samplers[index].times.size())
				{
					start = std::min(start, samplers[index].times.front());
					end = std::max(end, samplers[index].times.back());
				}
			}

			if (track_nodes.size() && end >= start)
			{
				const auto frame_count{ std::max(2u, static_cast<std::uint32_t>(std::round((end - start) * clip_frame_rate)) + 1u) };

				structures::clip_header_s header{ static_cast<std::uint32_t>(track_nodes.size()), frame_count, clip_frame_rate, static_cast<std::float_t>(frame_count - 1u) / clip_frame_rate, {}, UINT32_MAX };

				std::vector<structures::clip_track_s> tracks(track_nodes.size());
				std::vector<structures::clip_key_s> keys(static_cast<std::size_t>(frame_count) * track_nodes.size());
				std::vector<structures::vec3_s> rests(track_nodes.size());

				const auto retargeted{ std::any_of(std::begin(baker::clip_retarget_prefixes), std::end(baker::clip_retarget_prefixes), [&name](const char* prefix) { return name.rfind(prefix, 0u) == 0u; }) };

				auto moving{ 0u };
				auto offset{ 0u };

				for (auto track{ 0u }; track < track_nodes.size(); track++)
				{
					const auto& node{ nodes[track_nodes[track]] };

					std::snprintf(tracks[track].name, sizeof(tracks[track].name), "%s", node.get("name").text.c_str());

					structures::vec3_s rest_translation{}, rest_scale{};
					structures::quat_s rest_rotation{};

					node_transform(node, rest_translation, rest_rotation, rest_scale);

					rests[track] = rest_translation;

					header.root_track = node_parent[track_nodes[track]] < 0 ? track : header.root_track;

					for (auto frame{ 0u }; frame < frame_count; frame++)
					{
						const auto time{ start + static_cast<std::float_t>(frame) / clip_frame_rate };

						auto& key{ keys[static_cast<std::size_t>(frame) * track_nodes.size() + track] };

						key.translation = rest_translation;
						key.rotation = rest_rotation;

						if (translation_sampler[track_nodes[track]] >= 0)
						{
							const auto value{ sample(samplers[translation_sampler[track_nodes[track]]], time) };

							key.translation = { value.x, value.y, -value.z };
						}

						if (rotation_sampler[track_nodes[track]] >= 0)
						{
							const auto value{ sample(samplers[rotation_sampler[track_nodes[track]]], time) };

							key.rotation = mathematics.quat_normalize({ -value.x, -value.y, value.z, value.w });
						}

						if (frame && mathematics.quat_dot(key.rotation, keys[static_cast<std::size_t>(frame - 1u) * track_nodes.size() + track].rotation) < 0.0f)
						{
							key.rotation = { -key.rotation.x, -key.rotation.y, -key.rotation.z, -key.rotation.w };
						}
					}
				}

				if (header.root_track < track_nodes.size())
				{
					const auto first{ keys[header.root_track].translation };
					const auto last{ keys[static_cast<std::size_t>(frame_count - 1u) * track_nodes.size() + header.root_track].translation };

					header.root_velocity = structures::vec3_s{ last.x - first.x, 0.0f, last.z - first.z } / std::max(header.duration, 0.001f);

					for (auto frame{ 0u }; frame < frame_count; frame++)
					{
						auto& key{ keys[static_cast<std::size_t>(frame) * track_nodes.size() + header.root_track] };

						key.translation.x = first.x;
						key.translation.z = first.z;
					}
				}

				for (auto track{ 0u }; track < track_nodes.size(); track++)
				{
					const auto shifted{ track != header.root_track && translation_sampler[track_nodes[track]] >= 0 && mathematics.length(keys[track].translation - rests[track]) > baker::clip_offset_tolerance };

					for (auto frame{ 1u }; frame < frame_count; frame++)
					{
						if (mathematics.length(keys[static_cast<std::size_t>(frame) * track_nodes.size() + track].translation - keys[track].translation) > 0.001f)
						{
							tracks[track].flags |= structures::clip_track_translation;
						}
					}

					moving += (tracks[track].flags & structures::clip_track_translation) ? 1u : 0u;
					offset += shifted && (tracks[track].flags & structures::clip_track_translation) == 0u ? 1u : 0u;

					if (shifted && retargeted == false)
					{
						tracks[track].flags |= structures::clip_track_translation;
					}
				}

				baker::pak_item_s item{};

				std::snprintf(item.entry.name, sizeof(item.entry.name), "clip_%s", name.c_str());

				item.entry.type = structures::pak_type_blob;

				baker_models.append(item, &header, sizeof(header));
				baker_models.append(item, tracks.data(), tracks.size() * sizeof(structures::clip_track_s));
				baker_models.append(item, keys.data(), keys.size() * sizeof(structures::clip_key_s));

				items.push_back(std::move(item));

				logger.write("baker: clip %-24s %u tracks %u frames %.2f s root speed %.2f m/s, %u moving %u offset%s", name.c_str(), header.track_count, header.frame_count, header.duration, mathematics.length(header.root_velocity), moving, offset, retargeted ? " (retargeted)" : "");

				result = true;
			}
		}

		if (result == false)
		{
			logger.write("baker: clip %s was not imported", name.c_str());
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_characters_c::node_transform(const baker::json_s& node, structures::vec3_s& translation, structures::quat_s& rotation, structures::vec3_s& scale)
	{
		const auto& t{ node.get("translation") };
		const auto& r{ node.get("rotation") };
		const auto& s{ node.get("scale") };

		translation = { static_cast<std::float_t>(t.at(0).value(0.0)), static_cast<std::float_t>(t.at(1).value(0.0)), -static_cast<std::float_t>(t.at(2).value(0.0)) };
		rotation = mathematics.quat_normalize({ -static_cast<std::float_t>(r.at(0).value(0.0)), -static_cast<std::float_t>(r.at(1).value(0.0)), static_cast<std::float_t>(r.at(2).value(0.0)), static_cast<std::float_t>(r.at(3).value(1.0)) });
		scale = { static_cast<std::float_t>(s.at(0).value(1.0)), static_cast<std::float_t>(s.at(1).value(1.0)), static_cast<std::float_t>(s.at(2).value(1.0)) };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s baker_characters_c::convert_matrix(const std::float_t* column_major)
	{
		const std::float_t signs[4] = { 1.0f, 1.0f, -1.0f, 1.0f };

		structures::mat4_s result{};

		for (auto row{ 0u }; row < 4u; row++)
		{
			for (auto column{ 0u }; column < 4u; column++)
			{
				result.m[row][column] = column_major[row * 4u + column] * signs[row] * signs[column];
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::vector<std::float_t> baker_characters_c::read_floats(const baker::json_s& document, const std::vector<std::vector<std::uint8_t>>& buffers, std::uint32_t accessor_index, std::uint32_t& count, std::uint32_t& components)
	{
		std::vector<std::float_t> values;

		std::uint32_t stride{ 0u }, component{ 0u };

		const auto& entry{ document.get("accessors").at(accessor_index) };
		const auto& kind{ entry.get("type").text };
		const auto normalized{ entry.get("normalized").type == baker::json_boolean && entry.get("normalized").number > 0.5 };

		components = kind == "SCALAR" ? 1u : (kind == "VEC2" ? 2u : (kind == "VEC3" ? 3u : (kind == "VEC4" ? 4u : (kind == "MAT4" ? 16u : 1u))));

		if (const auto data{ baker_models.accessor(document, buffers, accessor_index, count, stride, component) }; data)
		{
			const auto size{ component == 5126u || component == 5125u ? 4u : (component == 5123u || component == 5122u ? 2u : 1u) };

			stride = std::max(stride, components * size);

			values.resize(static_cast<std::size_t>(count) * components);

			for (auto element{ 0u }; element < count; element++)
			{
				for (auto channel{ 0u }; channel < components; channel++)
				{
					const auto source{ data + static_cast<std::size_t>(element) * stride + static_cast<std::size_t>(channel) * size };

					auto value{ 0.0f };

					if (component == 5126u)
					{
						std::memcpy(&value, source, 4u);
					}

					else if (component == 5125u)
					{
						value = static_cast<std::float_t>(*reinterpret_cast<const std::uint32_t*>(source));
					}

					else if (component == 5123u)
					{
						value = static_cast<std::float_t>(*reinterpret_cast<const std::uint16_t*>(source)) / (normalized ? 65535.0f : 1.0f);
					}

					else
					{
						value = static_cast<std::float_t>(*source) / (normalized ? 255.0f : 1.0f);
					}

					values[static_cast<std::size_t>(element) * components + channel] = value;
				}
			}
		}

		return values;
	}
	/*
	//=====================================================================================
	*/
	structures::vec4_s baker_characters_c::sample(const baker::clip_sampler_s& sampler, std::float_t time)
	{
		structures::vec4_s a{ 0.0f, 0.0f, 0.0f, 1.0f };
		structures::vec4_s b{ 0.0f, 0.0f, 0.0f, 1.0f };

		if (const auto count{ sampler.times.size() }; count)
		{
			const auto stride{ sampler.cubic ? sampler.components * 3u : sampler.components };
			const auto offset{ sampler.cubic ? sampler.components : 0u };
			const auto upper{ static_cast<std::size_t>(std::upper_bound(sampler.times.begin(), sampler.times.end(), time) - sampler.times.begin()) };
			const auto next{ std::min(upper, count - 1u) };
			const auto previous{ upper ? upper - 1u : 0u };
			const auto span{ sampler.times[next] - sampler.times[previous] };
			const auto fraction{ span > 1e-6f && sampler.step == false ? std::clamp((time - sampler.times[previous]) / span, 0.0f, 1.0f) : 0.0f };

			for (auto channel{ 0u }; channel < std::min(sampler.components, 4u); channel++)
			{
				a[channel] = sampler.values[previous * stride + offset + channel];
				b[channel] = sampler.values[next * stride + offset + channel];
			}

			if (sampler.components == 4u && a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w < 0.0f)
			{
				b = b * -1.0f;
			}

			return a + (b - a) * fraction;
		}

		return a;
	}
}

//=====================================================================================
