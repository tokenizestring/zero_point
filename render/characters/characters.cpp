
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	characters_c characters;

	bool characters_c::load()
	{
		list.clear();
		clips.clear();

		for (auto index{ 0u }; pak.entries && index < pak.header->entry_count; index++)
		{
			const auto& entry{ pak.entries[index] };

			if (std::strncmp(entry.name, "clip_", 5u) == 0 && entry.size >= sizeof(structures::clip_header_s))
			{
				auto cursor{ pak.data(&entry) };

				structures::clip_s clip{};

				std::snprintf(clip.name, sizeof(clip.name), "%s", entry.name + 5);
				std::memcpy(&clip.header, cursor, sizeof(clip.header));

				cursor += sizeof(clip.header);

				clip.tracks.resize(clip.header.track_count);

				std::memcpy(clip.tracks.data(), cursor, clip.tracks.size() * sizeof(structures::clip_track_s));

				cursor += clip.tracks.size() * sizeof(structures::clip_track_s);

				clip.keys = reinterpret_cast<const structures::clip_key_s*>(cursor);

				clips.push_back(std::move(clip));
			}

			else if (std::strncmp(entry.name, "character_", 10u) == 0 && entry.size >= sizeof(structures::character_header_s))
			{
				auto cursor{ pak.data(&entry) };

				structures::character_header_s header{};

				std::memcpy(&header, cursor, sizeof(header));

				cursor += sizeof(header);

				structures::character_s character{};

				std::snprintf(character.name, sizeof(character.name), "%s", entry.name + 10);

				character.bones.resize(std::min(header.bone_count, maximum_bones));
				character.vertices.resize(header.vertex_count);
				character.indices.resize(header.index_count);
				character.alpha_first_index = header.alpha_first_index;
				character.bounds_min = header.bounds_min;
				character.bounds_max = header.bounds_max;

				std::memcpy(character.bones.data(), cursor, character.bones.size() * sizeof(structures::character_bone_s));

				cursor += static_cast<std::size_t>(header.bone_count) * sizeof(structures::character_bone_s);

				for (auto material{ 0u }; material < header.material_count; material++)
				{
					structures::model_material_s record{};

					std::memcpy(&record, cursor, sizeof(record));

					cursor += sizeof(record);

					character.materials.push_back(materials.register_model_material(record));
				}

				std::memcpy(character.vertices.data(), cursor, character.vertices.size() * sizeof(structures::skinned_vertex_s));

				cursor += character.vertices.size() * sizeof(structures::skinned_vertex_s);

				std::memcpy(character.indices.data(), cursor, character.indices.size() * sizeof(std::uint32_t));

				for (auto& vertex : character.vertices)
				{
					vertex.material = vertex.material < character.materials.size() ? character.materials[vertex.material] : 0u;
				}

				character.twist_shares.assign(character.bones.size(), 0.0f);
				character.blade_shares.assign(character.bones.size(), 0.0f);
				character.sit_shares.assign(character.bones.size(), 0.0f);

				for (auto twist{ 0u }; twist < std::size(character_twist_bones); twist++)
				{
					if (const auto found{ bone(character, character_twist_bones[twist]) }; found >= 0)
					{
						character.twist_shares[found] = character_twist_shares[twist];
						character.blade_shares[found] = character_blade_shares[twist];
					}
				}

				for (auto limb{ 0u }; limb < std::size(character_sit_bones); limb++)
				{
					if (const auto found{ bone(character, character_sit_bones[limb]) }; found >= 0)
					{
						character.sit_shares[found] = character_sit_angles[limb];
					}
				}

				list.push_back(std::move(character));
			}
		}

		for (auto& character : list)
		{
			character.clip_tracks.assign(clips.size(), std::vector<std::int32_t>(character.bones.size(), -1));

			for (auto clip_index{ 0u }; clip_index < clips.size(); clip_index++)
			{
				for (auto bone_index{ 0u }; bone_index < character.bones.size(); bone_index++)
				{
					for (auto track{ 0u }; track < clips[clip_index].tracks.size(); track++)
					{
						if (std::strcmp(clips[clip_index].tracks[track].name, character.bones[bone_index].name) == 0)
						{
							character.clip_tracks[clip_index][bone_index] = static_cast<std::int32_t>(track);
						}
					}
				}
			}
		}

		globals.resize(maximum_bones);

		logger.write("characters: %zu characters, %zu clips, %zu materials total", list.size(), clips.size(), materials.gpu_materials.size());

		return true;
	}
	/*
	//=====================================================================================
	*/
	bool characters_c::upload()
	{
		auto result{ true };

		for (auto& character : list)
		{
			character.mesh.vertex_buffer = gpu.create_buffer(static_cast<std::uint32_t>(character.vertices.size() * sizeof(structures::skinned_vertex_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, character.vertices.data(), 0u, 0u);
			character.mesh.index_buffer = gpu.create_buffer(static_cast<std::uint32_t>(character.indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, character.indices.data(), 0u, 0u);
			character.mesh.vertex_count = static_cast<std::uint32_t>(character.vertices.size());
			character.mesh.index_count = static_cast<std::uint32_t>(character.indices.size());
			character.mesh.bounds_min = character.bounds_min;
			character.mesh.bounds_max = character.bounds_max;

			result = result && character.mesh.vertex_buffer && character.mesh.index_buffer;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void characters_c::destroy()
	{
		for (auto& character : list)
		{
			functions::release(character.mesh.vertex_buffer);
			functions::release(character.mesh.index_buffer);
		}

		list.clear();
		clips.clear();
	}
	/*
	//=====================================================================================
	*/
	const structures::character_s* characters_c::find(const char* name)
	{
		for (const auto& character : list)
		{
			if (_stricmp(character.name, name) == 0)
			{
				return &character;
			}
		}

		logger.write("characters: missing character %s", name);

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t characters_c::clip(const char* name)
	{
		for (auto index{ 0u }; index < clips.size(); index++)
		{
			if (_stricmp(clips[index].name, name) == 0)
			{
				return index;
			}
		}

		logger.write("characters: missing clip %s", name);

		return UINT32_MAX;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t characters_c::bone(const structures::character_s& character, const char* name)
	{
		for (auto index{ 0u }; index < character.bones.size(); index++)
		{
			if (std::strcmp(character.bones[index].name, name) == 0)
			{
				return static_cast<std::int32_t>(index);
			}
		}

		return -1;
	}
	/*
	//=====================================================================================
	*/
	void characters_c::rest(const structures::character_s& character, structures::pose_s& pose)
	{
		for (auto index{ 0u }; index < character.bones.size(); index++)
		{
			pose.rotations[index] = character.bones[index].rotation;
			pose.translations[index] = character.bones[index].translation;
		}
	}
	/*
	//=====================================================================================
	*/
	void characters_c::sample(const structures::character_s& character, std::uint32_t clip_index, std::float_t time, structures::pose_s& pose)
	{
		rest(character, pose);

		if (clip_index < clips.size())
		{
			const auto& clip{ clips[clip_index] };
			const auto& tracks{ character.clip_tracks[clip_index] };
			const auto position{ std::clamp(time, 0.0f, clip.header.duration) * clip.header.frame_rate };
			const auto frame{ std::min(static_cast<std::uint32_t>(position), clip.header.frame_count - 2u) };
			const auto fraction{ std::clamp(position - static_cast<std::float_t>(frame), 0.0f, 1.0f) };

			for (auto index{ 0u }; index < character.bones.size(); index++)
			{
				if (const auto track{ tracks[index] }; track >= 0)
				{
					const auto& a{ clip.keys[static_cast<std::size_t>(frame) * clip.header.track_count + track] };
					const auto& b{ clip.keys[static_cast<std::size_t>(frame + 1u) * clip.header.track_count + track] };

					pose.rotations[index] = mathematics.quat_nlerp(a.rotation, b.rotation, fraction);

					if (clip.tracks[track].flags & structures::clip_track_translation)
					{
						pose.translations[index] = mathematics.lerp(a.translation, b.translation, fraction);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void characters_c::blend(const structures::character_s& character, const structures::pose_s& from, const structures::pose_s& to, std::float_t weight, structures::pose_s& out)
	{
		for (auto index{ 0u }; index < character.bones.size(); index++)
		{
			out.rotations[index] = mathematics.quat_nlerp(from.rotations[index], to.rotations[index], weight);
			out.translations[index] = mathematics.lerp(from.translations[index], to.translations[index], weight);
		}
	}
	/*
	//=====================================================================================
	*/
	void characters_c::add(const structures::character_s& character, const structures::pose_s& base, const structures::pose_s& reference, const structures::pose_s& target, std::float_t weight, structures::pose_s& out)
	{
		for (auto index{ 0u }; index < character.bones.size(); index++)
		{
			const auto delta{ mathematics.quat_multiply(mathematics.quat_conjugate(reference.rotations[index]), target.rotations[index]) };

			out.rotations[index] = mathematics.quat_nlerp(base.rotations[index], mathematics.quat_multiply(base.rotations[index], delta), weight);
			out.translations[index] = base.translations[index] + (target.translations[index] - reference.translations[index]) * weight;
		}
	}
	/*
	//=====================================================================================
	*/
	void characters_c::palette(const structures::character_s& character, const structures::pose_s& pose, std::float_t twist_yaw, std::float_t twist_pitch, structures::mat4_s* out, std::float_t blade, std::float_t sit)
	{
		for (auto index{ 0u }; index < character.bones.size(); index++)
		{
			const auto& bone_data{ character.bones[index] };
			const auto local{ mathematics.compose(pose.translations[index], pose.rotations[index], bone_data.scale) };

			globals[index] = bone_data.parent >= 0 ? mathematics.multiply(local, globals[bone_data.parent]) : local;

			if (sit > 0.0f && index < character.sit_shares.size() && character.sit_shares[index] != 0.0f)
			{
				const auto joint{ globals[index].row3(3u) };

				globals[index] = mathematics.multiply(mathematics.multiply(mathematics.multiply(globals[index], mathematics.translation(-joint)), mathematics.rotation(mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, character.sit_shares[index] * sit))), mathematics.translation(joint));
			}

			if (character.twist_shares[index] > 0.0f)
			{
				const auto origin{ globals[index].row3(3u) };
				const auto twist{ mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, twist_yaw * character.twist_shares[index] + blade * character.blade_shares[index]), mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, twist_pitch * character.twist_shares[index])) };

				globals[index] = mathematics.multiply(mathematics.multiply(mathematics.multiply(globals[index], mathematics.translation(-origin)), mathematics.rotation(twist)), mathematics.translation(origin));
			}

			out[index] = mathematics.multiply(bone_data.inverse_bind, globals[index]);
		}
	}
	/*
	//=====================================================================================
	*/
	void characters_c::compute_globals(const structures::character_s& character, const structures::pose_s& pose)
	{
		for (auto index{ 0u }; index < character.bones.size(); index++)
		{
			const auto local{ mathematics.compose(pose.translations[index], pose.rotations[index], character.bones[index].scale) };

			globals[index] = character.bones[index].parent >= 0 ? mathematics.multiply(local, globals[character.bones[index].parent]) : local;
		}
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s characters_c::rest_global(const structures::character_s& character, std::int32_t bone)
	{
		auto result{ mathematics.identity() };

		for (auto walk{ bone }; walk >= 0; walk = character.bones[walk].parent)
		{
			result = mathematics.multiply(result, mathematics.compose(character.bones[walk].translation, character.bones[walk].rotation, character.bones[walk].scale));
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void characters_c::reach(const structures::character_s& character, structures::pose_s& pose, std::int32_t upper, std::int32_t lower, std::int32_t end, structures::vec3_s target, structures::vec3_s pole, std::float_t weight)
	{
		if (upper >= 0 && lower >= 0 && end >= 0 && weight > 0.001f)
		{
			compute_globals(character, pose);

			const auto shoulder{ globals[upper].row3(3u) };
			const auto upper_length{ mathematics.distance(shoulder, globals[lower].row3(3u)) };
			const auto lower_length{ mathematics.distance(globals[lower].row3(3u), globals[end].row3(3u)) };
			const auto rest_upper{ rest_global(character, upper) };
			const auto rest_lower{ rest_global(character, lower) };
			const auto rest_end{ rest_global(character, end) };
			const auto hinge_sign{ mathematics.dot(mathematics.normalize(rest_upper.row3(2u)), mathematics.cross(rest_lower.row3(3u) - rest_upper.row3(3u), rest_end.row3(3u) - rest_lower.row3(3u))) >= 0.0f ? 1.0f : -1.0f };
			const auto offset{ target - shoulder };
			const auto distance{ std::clamp(mathematics.length(offset), 0.05f, (upper_length + lower_length) * 0.998f) };
			const auto along{ mathematics.normalize(offset) };
			const auto bend{ mathematics.normalize(pole - along * mathematics.dot(pole, along)) };
			const auto cosine{ std::clamp((upper_length * upper_length + distance * distance - lower_length * lower_length) / (2.0f * upper_length * distance), -1.0f, 1.0f) };
			const auto elbow{ shoulder + (along * cosine + bend * std::sqrt(1.0f - cosine * cosine)) * upper_length };
			const auto hinge{ mathematics.normalize(mathematics.cross(along, bend)) * -hinge_sign };
			const auto upper_original{ pose.rotations[upper] };
			const auto lower_original{ pose.rotations[lower] };

			orient(character, pose, upper, mathematics.normalize(elbow - shoulder), hinge);
			orient(character, pose, lower, mathematics.normalize(shoulder + along * distance - elbow), hinge);

			pose.rotations[upper] = mathematics.quat_slerp(upper_original, pose.rotations[upper], weight);
			pose.rotations[lower] = mathematics.quat_slerp(lower_original, pose.rotations[lower], weight);
		}
	}
	/*
	//=====================================================================================
	*/
	void characters_c::orient(const structures::character_s& character, structures::pose_s& pose, std::int32_t bone, structures::vec3_s x_axis, structures::vec3_s z_hint)
	{
		const auto z_axis{ mathematics.normalize(z_hint - x_axis * mathematics.dot(z_hint, x_axis)) };
		const auto parent{ character.bones[bone].parent };
		const auto parent_rotation{ parent >= 0 ? mathematics.quat_from_basis(mathematics.normalize(globals[parent].row3(0u)), mathematics.normalize(globals[parent].row3(1u)), mathematics.normalize(globals[parent].row3(2u))) : mathematics.quat_identity() };

		pose.rotations[bone] = mathematics.quat_normalize(mathematics.quat_multiply(mathematics.quat_conjugate(parent_rotation), mathematics.quat_from_basis(x_axis, mathematics.cross(z_axis, x_axis), z_axis)));

		const auto local{ mathematics.compose(pose.translations[bone], pose.rotations[bone], character.bones[bone].scale) };

		globals[bone] = parent >= 0 ? mathematics.multiply(local, globals[parent]) : local;
	}
}

//=====================================================================================
