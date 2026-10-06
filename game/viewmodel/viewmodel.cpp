
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	viewmodel_c viewmodel;

	bool viewmodel_c::create()
	{
		if (const auto source{ characters.find(viewmodel_character) }; source && source->bones.size())
		{
			upper_arm = characters.bone(*source, "Bip01 R UpperArm");
			forearm = characters.bone(*source, "Bip01 R Forearm");
			hand = characters.bone(*source, "Bip01 R Hand");
			left_upper = characters.bone(*source, "Bip01 L UpperArm");
			left_forearm = characters.bone(*source, "Bip01 L Forearm");
			left_hand = characters.bone(*source, "Bip01 L Hand");
			rags = models.variant(structures::material_burlap, { 0.4f, 0.33f, 0.24f }, 0.0f);

			for (auto finger{ 0u }; finger < 5u; finger++)
			{
				for (auto joint{ 0u }; joint < 3u; joint++)
				{
					fingers[finger][joint] = characters.bone(*source, viewmodel_fingers[finger][joint]);
					left_fingers[finger][joint] = characters.bone(*source, viewmodel_left_fingers[finger][joint]);
				}
			}

			if (upper_arm >= 0 && forearm >= 0 && hand >= 0 && build_arm(*source, upper_arm, arms))
			{
				build_arm(*source, left_upper, arms_left);

				globals.resize(arms.bones.size());
				palette.resize(arms.bones.size());
				previous_palette.resize(arms.bones.size());

				characters.rest(arms, pose);

				compute_globals();

				const auto shoulder{ globals[upper_arm].row3(3u) };
				const auto elbow{ globals[forearm].row3(3u) };
				const auto joint{ globals[hand].row3(3u) };
				const auto right_eye{ characters.bone(*source, "Bip01 REye") };
				const auto left_eye{ characters.bone(*source, "Bip01 LEye") };

				upper_length = mathematics.distance(shoulder, elbow);
				lower_length = mathematics.distance(elbow, joint);
				hinge_sign = mathematics.dot(mathematics.normalize(globals[upper_arm].row3(2u)), mathematics.cross(elbow - shoulder, joint - elbow)) >= 0.0f ? 1.0f : -1.0f;
				left_palm = left_hand >= 0 && mathematics.dot(mathematics.normalize(globals[left_hand].row3(1u)), { -1.0f, 0.0f, 0.0f }) < 0.0f ? -1.0f : 1.0f;
				eye = right_eye >= 0 && left_eye >= 0 ? (globals[right_eye].row3(3u) + globals[left_eye].row3(3u)) * 0.5f : globals[characters.bone(*source, "Bip01 Head")].row3(3u) + structures::vec3_s{ 0.0f, 0.1f, -0.09f };
				world = mathematics.multiply(mathematics.multiply(mathematics.translation(-eye), mathematics.rotation_y(pi)), mathematics.translation(viewmodel_offset));

				measure();

				build_tools();

				ready = arms.mesh.vertex_buffer && arms.mesh.index_buffer;

				logger.write("viewmodel: %zu + %zu arm tris, arm %.3f + %.3f m, eye %.3f %.3f %.3f, hinge %.0f, left palm %.0f", arms.indices.size() / 3u, arms_left.indices.size() / 3u, upper_length, lower_length, eye.x, eye.y, eye.z, hinge_sign, left_palm);

				if (left_upper >= 0 && left_forearm >= 0 && left_hand >= 0)
				{
					const auto left_shoulder{ globals[left_upper].row3(3u) };
					const auto left_elbow{ globals[left_forearm].row3(3u) };

					left_hinge_sign = mathematics.dot(mathematics.normalize(globals[left_upper].row3(2u)), mathematics.cross(left_elbow - left_shoulder, globals[left_hand].row3(3u) - left_elbow)) >= 0.0f ? 1.0f : -1.0f;
				}

				for (auto side{ 0u }; side < 2u; side++)
				{
					for (auto finger{ 1u }; finger < 5u; finger++)
					{
						if (const auto bone{ side ? left_fingers[finger][0] : fingers[finger][0] }; bone >= 0)
						{
							const auto direction{ mathematics.quat_rotate(arms.bones[bone].rotation, { 1.0f, 0.0f, 0.0f }) };

							spreads[side][finger] = std::atan2(direction.z, direction.x);
						}
					}
				}

				logger.write("viewmodel: %zu bones, twist bones %d %d, left hinge %.0f, spreads %.2f %.2f %.2f %.2f / %.2f %.2f %.2f %.2f", arms.bones.size(), twists[0], twists[1], left_hinge_sign, spreads[0][1], spreads[0][2], spreads[0][3], spreads[0][4], spreads[1][1], spreads[1][2], spreads[1][3], spreads[1][4]);
			}
		}

		return ready;
	}
	/*
	//=====================================================================================
	*/
	bool viewmodel_c::build_arm(const structures::character_s& source, std::int32_t root, structures::character_s& target)
	{
		if (root >= 0)
		{
			std::vector<std::uint8_t> arm(source.bones.size(), 0u);

			std::snprintf(target.name, sizeof(target.name), "%s_arm_%d", source.name, root);

			target.bones = source.bones;
			target.vertices = source.vertices;
			target.materials = source.materials;

			for (auto side{ 0u }; side < 2u; side++)
			{
				if (const auto lower_bone{ side ? left_forearm : forearm }; lower_bone >= 0)
				{
					auto twist_bone{ source.bones[lower_bone] };

					std::snprintf(twist_bone.name, sizeof(twist_bone.name), "Bip01 %c ForeTwist", side ? 'L' : 'R');

					twist_bone.parent = lower_bone;
					twist_bone.translation = {};
					twist_bone.rotation = mathematics.quat_identity();
					twist_bone.scale = { 1.0f, 1.0f, 1.0f };
					twists[side] = static_cast<std::int32_t>(target.bones.size());

					target.bones.push_back(twist_bone);
				}
			}

			target.twist_shares.assign(target.bones.size(), 0.0f);
			target.blade_shares.assign(target.bones.size(), 0.0f);
			target.bounds_min = source.bounds_min;
			target.bounds_max = source.bounds_max;
			target.alpha_first_index = UINT32_MAX;

			for (auto bone{ 0u }; bone < source.bones.size(); bone++)
			{
				for (auto walk{ static_cast<std::int32_t>(bone) }; walk >= 0 && arm[bone] == 0u; walk = source.bones[walk].parent)
				{
					arm[bone] = walk == root ? 1u : 0u;
				}
			}

			for (auto index{ 0u }; index + 2u < source.indices.size(); index += 3u)
			{
				if (index == source.alpha_first_index)
				{
					target.alpha_first_index = static_cast<std::uint32_t>(target.indices.size());
				}

				if (arm[dominant(source.vertices[source.indices[index]])] && arm[dominant(source.vertices[source.indices[index + 1u]])] && arm[dominant(source.vertices[source.indices[index + 2u]])])
				{
					target.indices.insert(target.indices.end(), { source.indices[index], source.indices[index + 1u], source.indices[index + 2u] });
				}
			}

			target.alpha_first_index = std::min(target.alpha_first_index, static_cast<std::uint32_t>(target.indices.size()));

			const auto palm_bone{ root == upper_arm ? hand : left_hand };
			const auto wrist_bone{ root == upper_arm ? forearm : left_forearm };

			if (palm_bone >= 0 && wrist_bone >= 0)
			{
				const auto reach_x{ mathematics.transform_point(bone_frame(target, palm_bone).row3(3u), mathematics.inverse(bone_frame(target, wrist_bone))).x };

				wrap(target, wrist_bone, reach_x - 0.07f, reach_x - 0.035f, 2u, true);

				add_twist(target, wrist_bone, palm_bone, twists[root == upper_arm ? 0u : 1u]);
			}

			for (auto level{ 0u }; level < viewmodel_arm_subdivisions; level++)
			{
				subdivide(target);
			}

			target.mesh.vertex_buffer = gpu.create_buffer(static_cast<std::uint32_t>(target.vertices.size() * sizeof(structures::skinned_vertex_s)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_VERTEX_BUFFER, 0u, target.vertices.data(), 0u, 0u);
			target.mesh.index_buffer = target.indices.size() ? gpu.create_buffer(static_cast<std::uint32_t>(target.indices.size() * sizeof(std::uint32_t)), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, target.indices.data(), 0u, 0u) : nullptr;
			target.mesh.vertex_count = static_cast<std::uint32_t>(target.vertices.size());
			target.mesh.index_count = static_cast<std::uint32_t>(target.indices.size());
			target.mesh.bounds_min = target.bounds_min;
			target.mesh.bounds_max = target.bounds_max;

			return target.mesh.vertex_buffer && target.mesh.index_buffer;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::add_twist(structures::character_s& target, std::int32_t lower_bone, std::int32_t hand_bone, std::int32_t twist_bone)
	{
		if (twist_bone >= 0)
		{
			const auto elbow{ bone_frame(target, lower_bone).row3(3u) };
			const auto span{ bone_frame(target, hand_bone).row3(3u) - elbow };

			for (auto& vertex : target.vertices)
			{
				const auto share{ mathematics.smoothstep(0.05f, 1.0f, mathematics.dot(vertex.position - elbow, span) / mathematics.dot(span, span)) };

				for (auto slot{ 0u }; slot < 4u; slot++)
				{
					const auto weight{ (vertex.weights >> (slot * 8u)) & 0xFFu };
					const auto moved{ static_cast<std::uint32_t>(std::lround(static_cast<std::float_t>(weight) * share)) };

					if (((vertex.joints >> (slot * 8u)) & 0xFFu) == static_cast<std::uint32_t>(lower_bone) && moved > 0u)
					{
						auto free_slot{ 4u };

						for (auto other{ 0u }; other < 4u; other++)
						{
							free_slot = free_slot == 4u && ((vertex.weights >> (other * 8u)) & 0xFFu) == 0u ? other : free_slot;
						}

						if (free_slot < 4u)
						{
							vertex.joints = (vertex.joints & ~(0xFFu << (free_slot * 8u))) | (static_cast<std::uint32_t>(twist_bone) << (free_slot * 8u));
							vertex.weights = (vertex.weights & ~(0xFFu << (free_slot * 8u)) & ~(0xFFu << (slot * 8u))) | (moved << (free_slot * 8u)) | ((weight - moved) << (slot * 8u));
						}

						else if (moved * 2u >= weight)
						{
							vertex.joints = (vertex.joints & ~(0xFFu << (slot * 8u))) | (static_cast<std::uint32_t>(twist_bone) << (slot * 8u));
						}
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t viewmodel_c::dominant(const structures::skinned_vertex_s& vertex)
	{
		auto best{ 0u };

		for (auto slot{ 1u }; slot < 4u; slot++)
		{
			best = ((vertex.weights >> (slot * 8u)) & 0xFFu) > ((vertex.weights >> (best * 8u)) & 0xFFu) ? slot : best;
		}

		return (vertex.joints >> (best * 8u)) & 0xFFu;
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s viewmodel_c::bone_frame(const structures::character_s& target, std::int32_t bone)
	{
		const auto bind{ mathematics.inverse(target.bones[bone].inverse_bind) };

		return mathematics.basis(mathematics.normalize(bind.row3(0u)), mathematics.normalize(bind.row3(1u)), mathematics.normalize(bind.row3(2u)), bind.row3(3u));
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::wrap(structures::character_s& target, std::int32_t bone, std::float_t start, std::float_t end, std::uint32_t bands, bool children)
	{
		const auto bind{ bone_frame(target, bone) };
		const auto inverse_bind{ mathematics.inverse(bind) };
		const auto parent{ target.bones[bone].parent };
		const auto joints{ static_cast<std::uint32_t>(bone) * 0x01010101u };
		const auto width{ (end - start) / static_cast<std::float_t>(bands) * 1.45f };

		std::vector<structures::vec3_s> nearby;
		std::vector<structures::skinned_vertex_s> added;
		std::vector<std::uint32_t> triangles;

		auto winding{ 0.0f };

		for (auto index{ 0u }; index + 2u < target.indices.size(); index += 3u)
		{
			const auto& a{ target.vertices[target.indices[index]] };
			const auto& b{ target.vertices[target.indices[index + 1u]] };
			const auto& c{ target.vertices[target.indices[index + 2u]] };

			winding += mathematics.dot(mathematics.cross(b.position - a.position, c.position - a.position), a.normal + b.normal + c.normal) > 0.0f ? 1.0f : -1.0f;

			const auto owner{ static_cast<std::int32_t>(dominant(a)) };

			if (owner == bone || owner == parent || (target.bones[owner].parent == bone && (children || std::strstr(target.bones[owner].name, "Twist"))))
			{
				nearby.insert(nearby.end(), { mathematics.transform_point(a.position, inverse_bind), mathematics.transform_point(b.position, inverse_bind), mathematics.transform_point(c.position, inverse_bind) });
			}
		}

		const auto support = [&](std::float_t x, std::float_t theta)
			{
				auto best{ 0.014f };

				for (auto index{ 0u }; index + 2u < nearby.size(); index += 3u)
				{
					for (auto corner{ 0u }; corner < 3u; corner++)
					{
						const auto& p{ nearby[index + corner] };
						const auto& q{ nearby[index + (corner + 1u) % 3u] };

						if ((p.x - x) * (q.x - x) <= 0.0f && std::fabs(q.x - p.x) > 1e-6f)
						{
							const auto crossing{ p + (q - p) * ((x - p.x) / (q.x - p.x)) };

							best = crossing.y * crossing.y + crossing.z * crossing.z < 0.0049f ? std::max(best, crossing.y * std::cos(theta) + crossing.z * std::sin(theta)) : best;
						}
					}
				}

				return best;
			};

		for (auto band{ 0u }; band < bands; band++)
		{
			const auto middle{ start + (end - start) * (static_cast<std::float_t>(band) + 0.5f) / static_cast<std::float_t>(bands) };
			const auto tilt{ (band % 2u ? 0.28f : -0.28f) * width };
			const auto first{ static_cast<std::uint32_t>(target.vertices.size() + added.size()) };

			for (auto edge{ 0u }; edge < 2u; edge++)
			{
				for (auto segment{ 0u }; segment <= viewmodel_wrap_segments; segment++)
				{
					const auto theta{ two_pi * static_cast<std::float_t>(segment) / static_cast<std::float_t>(viewmodel_wrap_segments) };
					const auto fray{ (mathematics.hash_float(segment % viewmodel_wrap_segments + band * 131u + edge * 977u + static_cast<std::uint32_t>(bone) * 7919u) - 0.5f) * 0.004f };
					const auto x{ middle + tilt * std::sin(theta + static_cast<std::float_t>(band)) + (edge ? 0.5f : -0.5f) * width + fray };
					const auto radius{ (support(x, theta - 0.13f) + support(x, theta) * 2.0f + support(x, theta + 0.13f)) * 0.25f + 0.0024f + 0.0008f * static_cast<std::float_t>(band) };
					const structures::vec3_s direction{ 0.0f, std::cos(theta), std::sin(theta) };

					structures::skinned_vertex_s vertex{};

					const auto around{ mathematics.normalize(mathematics.transform_vector({ 0.0f, -std::sin(theta), std::cos(theta) }, bind)) };

					vertex.position = mathematics.transform_point(structures::vec3_s{ x, 0.0f, 0.0f } + direction * radius, bind);
					vertex.normal = mathematics.normalize(mathematics.transform_vector(direction, bind));
					vertex.tangent = { around.x, around.y, around.z, 1.0f };
					vertex.uv = { theta * radius * 7.0f + static_cast<std::float_t>(band) * 0.37f, (edge ? width : 0.0f) * 7.0f };
					vertex.material = rags;
					vertex.joints = joints;
					vertex.weights = 255u;

					added.push_back(vertex);
				}
			}

			for (auto segment{ 0u }; segment < viewmodel_wrap_segments; segment++)
			{
				const auto row{ viewmodel_wrap_segments + 1u };
				const std::uint32_t quad[4] = { first + segment, first + segment + 1u, first + row + segment + 1u, first + row + segment };

				for (const auto& corners : { std::array<std::uint32_t, 3>{ quad[0], quad[1], quad[2] }, std::array<std::uint32_t, 3>{ quad[0], quad[2], quad[3] } })
				{
					const auto& a{ added[corners[0] - static_cast<std::uint32_t>(target.vertices.size())] };
					const auto& b{ added[corners[1] - static_cast<std::uint32_t>(target.vertices.size())] };
					const auto& c{ added[corners[2] - static_cast<std::uint32_t>(target.vertices.size())] };
					const auto facing{ mathematics.dot(mathematics.cross(b.position - a.position, c.position - a.position), a.normal) > 0.0f };

					triangles.insert(triangles.end(), { corners[0], facing == (winding > 0.0f) ? corners[1] : corners[2], facing == (winding > 0.0f) ? corners[2] : corners[1] });
				}
			}
		}

		target.vertices.insert(target.vertices.end(), added.begin(), added.end());
		target.indices.insert(target.indices.begin() + target.alpha_first_index, triangles.begin(), triangles.end());
		target.alpha_first_index += static_cast<std::uint32_t>(triangles.size());
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::subdivide(structures::character_s& target)
	{
		std::unordered_map<std::uint64_t, std::vector<std::uint32_t>> groups;
		std::unordered_map<std::uint64_t, std::uint32_t> midpoints;
		std::vector<structures::vec3_s> smooth(target.vertices.size());
		std::vector<std::uint8_t> creased(target.vertices.size(), 0u);
		std::vector<std::uint32_t> refined;

		const auto key = [](structures::vec3_s position)
			{
				const auto x{ static_cast<std::uint64_t>(std::llround(position.x * 10000.0) + 0x100000) & 0x1FFFFFull };
				const auto y{ static_cast<std::uint64_t>(std::llround(position.y * 10000.0) + 0x100000) & 0x1FFFFFull };
				const auto z{ static_cast<std::uint64_t>(std::llround(position.z * 10000.0) + 0x100000) & 0x1FFFFFull };

				return x | (y << 21u) | (z << 42u);
			};

		for (auto index{ 0u }; index < target.vertices.size(); index++)
		{
			groups[key(target.vertices[index].position)].push_back(index);
		}

		for (const auto& group : groups)
		{
			for (const auto member : group.second)
			{
				for (const auto other : group.second)
				{
					const auto agreement{ mathematics.dot(target.vertices[member].normal, target.vertices[other].normal) };

					smooth[member] = agreement > 0.5f ? smooth[member] + target.vertices[other].normal : smooth[member];
					creased[member] = agreement > 0.5f ? creased[member] : 1u;
				}

				smooth[member] = mathematics.normalize(smooth[member]);
			}
		}

		const auto split = [&](std::uint32_t first, std::uint32_t second)
			{
				const auto edge{ (static_cast<std::uint64_t>(std::min(first, second)) << 32u) | std::max(first, second) };

				if (const auto found{ midpoints.find(edge) }; found != midpoints.end())
				{
					return found->second;
				}

				const auto a{ target.vertices[first] };
				const auto b{ target.vertices[second] };
				const auto normal_a{ smooth[first] };
				const auto normal_b{ smooth[second] };
				const auto direction{ mathematics.normalize(structures::vec3_s{ a.tangent.x + b.tangent.x, a.tangent.y + b.tangent.y, a.tangent.z + b.tangent.z }) };
				const auto bulge{ creased[first] || creased[second] ? structures::vec3_s{} : (normal_a * mathematics.dot(b.position - a.position, normal_a) + normal_b * mathematics.dot(a.position - b.position, normal_b)) * 0.125f };
				const auto limit{ mathematics.distance(a.position, b.position) * 0.15f };

				structures::skinned_vertex_s vertex{ a };

				vertex.position = (a.position + b.position) * 0.5f - (mathematics.length(bulge) > limit ? mathematics.normalize(bulge) * limit : bulge);
				vertex.normal = mathematics.normalize(a.normal + b.normal);
				vertex.tangent = { direction.x, direction.y, direction.z, a.tangent.w };
				vertex.uv = (a.uv + b.uv) * 0.5f;

				blend(a, b, vertex);

				midpoints[edge] = static_cast<std::uint32_t>(target.vertices.size());
				target.vertices.push_back(vertex);

				return midpoints[edge];
			};

		refined.reserve(target.indices.size() * 4u);

		for (auto index{ 0u }; index + 2u < target.indices.size(); index += 3u)
		{
			const auto a{ target.indices[index] };
			const auto b{ target.indices[index + 1u] };
			const auto c{ target.indices[index + 2u] };
			const auto ab{ split(a, b) };
			const auto bc{ split(b, c) };
			const auto ca{ split(c, a) };

			refined.insert(refined.end(), { a, ab, ca, ab, b, bc, ca, bc, c, ab, bc, ca });
		}

		target.indices = refined;
		target.alpha_first_index *= 4u;
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::blend(const structures::skinned_vertex_s& first, const structures::skinned_vertex_s& second, structures::skinned_vertex_s& target)
	{
		std::uint32_t bones[8]{};
		std::float_t amounts[8]{};
		std::uint32_t picked[4]{};
		std::uint32_t shares[4]{};
		std::float_t kept[4]{};

		auto count{ 0u };
		auto total{ 0.0f };
		auto assigned{ 0u };

		for (const auto& source : { first, second })
		{
			for (auto slot{ 0u }; slot < 4u; slot++)
			{
				const auto bone{ (source.joints >> (slot * 8u)) & 0xFFu };
				const auto amount{ static_cast<std::float_t>((source.weights >> (slot * 8u)) & 0xFFu) };

				auto match{ 0u };

				while (match < count && bones[match] != bone)
				{
					match++;
				}

				if (amount > 0.0f)
				{
					bones[match] = bone;
					amounts[match] += amount;
					count = std::max(count, match + 1u);
				}
			}
		}

		for (auto slot{ 0u }; slot < 4u; slot++)
		{
			auto best{ 0u };

			for (auto index{ 1u }; index < count; index++)
			{
				best = amounts[index] > amounts[best] ? index : best;
			}

			picked[slot] = bones[best];
			kept[slot] = std::max(amounts[best], 0.0f);
			total += kept[slot];
			amounts[best] = -1.0f;
		}

		for (auto slot{ 0u }; slot < 4u; slot++)
		{
			shares[slot] = static_cast<std::uint32_t>(std::lround(kept[slot] / std::max(total, 1.0f) * 255.0f));
			assigned += shares[slot];
		}

		shares[0] = static_cast<std::uint32_t>(static_cast<std::int32_t>(shares[0]) + 255 - static_cast<std::int32_t>(assigned));
		target.joints = picked[0] | (picked[1] << 8u) | (picked[2] << 16u) | (picked[3] << 24u);
		target.weights = shares[0] | (shares[1] << 8u) | (shares[2] << 16u) | (shares[3] << 24u);
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::destroy()
	{
		functions::release(arms.mesh.vertex_buffer);
		functions::release(arms.mesh.index_buffer);
		functions::release(arms_left.mesh.vertex_buffer);
		functions::release(arms_left.mesh.index_buffer);

		for (auto& mesh : tools)
		{
			functions::release(mesh.vertex_buffer);
			functions::release(mesh.index_buffer);

			mesh = {};
		}

		for (auto& mesh : bolts)
		{
			functions::release(mesh.vertex_buffer);
			functions::release(mesh.index_buffer);

			mesh = {};
		}

		for (auto& mesh : magazines)
		{
			functions::release(mesh.vertex_buffer);
			functions::release(mesh.index_buffer);

			mesh = {};
		}

		for (auto mesh : { &arrow_mesh, &string_mesh })
		{
			functions::release(mesh->vertex_buffer);
			functions::release(mesh->index_buffer);

			*mesh = {};
		}

		ready = false;
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::build_tools()
	{
		const auto rock{ models.find("boulder_01") };
		const auto bark{ models.variant(structures::material_plywood, { 0.66f, 0.48f, 0.32f }, 0.0f) };
		const auto charred{ models.variant(structures::material_burlap, { 0.3f, 0.24f, 0.18f }, 0.0f) };

		materials.upload();

		if (rock)
		{
			tool_builder.clear();

			stone(*rock, { 0.085f, 0.07f, 0.11f }, { 0.0f, 0.0f, 0.01f }, 0.4f);

			fit_item(structures::item_rock, true);

			tool_builder.upload(tools[structures::item_rock]);

			tool_builder.clear();

			stick(bark, 0.016f, -0.13f, 0.38f);
			stick(structures::material_burlap, 0.021f, 0.27f, 0.33f);
			stone(*rock, { 0.15f, 0.075f, 0.05f }, { 0.05f, 0.3f, 0.0f }, half_pi);

			fit_item(structures::item_stone_hatchet, true);

			tool_builder.upload(tools[structures::item_stone_hatchet]);

			tool_builder.clear();

			stick(bark, 0.016f, -0.13f, 0.42f);
			stick(structures::material_burlap, 0.021f, 0.31f, 0.37f);
			stone(*rock, { 0.25f, 0.04f, 0.035f }, { 0.0f, 0.34f, 0.0f }, half_pi);

			fit_item(structures::item_stone_pickaxe, true);

			tool_builder.upload(tools[structures::item_stone_pickaxe]);
		}

		tool_builder.clear();

		stick(bark, 0.017f, -0.14f, 0.3f);
		stick(charred, 0.03f, 0.22f, 0.36f);

		fit_item(structures::item_torch, true);

		tool_builder.upload(tools[structures::item_torch]);

		tool_builder.clear();

		stick(bark, 0.015f, -0.85f, 0.62f);

		tool_builder.set_material(bark);
		tool_builder.cone({ 0.0f, 0.62f, 0.0f }, { 0.0f, 1.0f, 0.0f }, 0.015f, 0.0f, 0.16f, 8u, false);
		tool_builder.compute_tangents(0u, 0u);

		fit_item(structures::item_wooden_spear, true);

		tool_builder.upload(tools[structures::item_wooden_spear]);

		build_gun(structures::weapon_pistol);
		build_gun(structures::weapon_rifle);
		build_gun(structures::weapon_bow);
		build_gun(structures::weapon_assault);

		if (const auto arrow{ models.find("wooden_arrow") }; arrow)
		{
			tool_builder.clear();

			for (const auto& part : arrow->parts)
			{
				tool_builder.append(*arrow, part.first_index, part.index_count, mathematics.identity());
			}

			tool_builder.upload(arrow_mesh);
		}

		tool_builder.clear();
		tool_builder.set_material(models.variant(structures::material_burlap, { 0.42f, 0.36f, 0.28f }, 0.0f));
		tool_builder.cylinder({ 0.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f }, 0.0017f, 1.0f, 6u, false);
		tool_builder.compute_tangents(0u, 0u);
		tool_builder.upload(string_mesh);
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::build_gun(std::uint32_t weapon)
	{
		const auto& gun{ gun_models[weapon] };

		if (const auto model{ gun.model ? models.find(gun.model) : nullptr }; model)
		{
			gun_frames[weapon] = mathematics.multiply(mathematics.translation(-gun.grip), mathematics.rotation_z(gun.tilt));

			tool_builder.clear();

			for (const auto name : gun.parts)
			{
				if (const auto part{ name ? models.part(*model, name) : nullptr }; part)
				{
					tool_builder.append(*model, part->first_index, part->index_count, gun_frames[weapon]);
				}
			}

			if (gun.action != structures::action_draw)
			{
				fit_item(weapon_definitions[weapon].item, false);
			}

			if (weapon == structures::weapon_rifle || weapon == structures::weapon_bow || weapon == structures::weapon_assault)
			{
				fit_support(weapon);
			}

			tool_builder.upload(tools[weapon_definitions[weapon].item]);

			tool_builder.clear();

			for (const auto name : gun.bolt)
			{
				if (const auto part{ name ? models.part(*model, name) : nullptr }; part)
				{
					tool_builder.append(*model, part->first_index, part->index_count, mathematics.identity());
				}
			}

			if (tool_builder.indices.size())
			{
				tool_builder.upload(bolts[weapon]);
			}

			if (const auto part{ gun.magazine ? models.part(*model, gun.magazine) : nullptr }; part)
			{
				tool_builder.clear();
				tool_builder.append(*model, part->first_index, part->index_count, mathematics.identity());
				tool_builder.upload(magazines[weapon]);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::gather(const structures::mat4_s& to_hand)
	{
		fit_triangles.clear();

		for (auto index{ 0u }; index + 2u < tool_builder.indices.size(); index += 3u)
		{
			const auto a{ mathematics.transform_point(tool_builder.vertices[tool_builder.indices[index]].position, to_hand) };
			const auto b{ mathematics.transform_point(tool_builder.vertices[tool_builder.indices[index + 1u]].position, to_hand) };
			const auto c{ mathematics.transform_point(tool_builder.vertices[tool_builder.indices[index + 2u]].position, to_hand) };

			if (mathematics.length((a + b + c) / 3.0f) < viewmodel_fit_reach)
			{
				fit_triangles.push_back(a);
				fit_triangles.push_back(b);
				fit_triangles.push_back(c);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s viewmodel_c::settle(const structures::mat4_s& frame)
	{
		auto lowest{ FLT_MAX };
		auto front{ -FLT_MAX };

		const auto scan = [&](const auto& visit)
			{
				for (auto index{ 0u }; index + 2u < fit_triangles.size(); index += 3u)
				{
					const auto& a{ fit_triangles[index] };
					const auto& b{ fit_triangles[index + 1u] };
					const auto& c{ fit_triangles[index + 2u] };

					if (std::min({ a.x, b.x, c.x }) < 0.08f && std::max({ a.x, b.x, c.x }) > -0.08f && std::min({ a.z, b.z, c.z }) < viewmodel_fit_window.y && std::max({ a.z, b.z, c.z }) > -viewmodel_fit_window.y)
					{
						for (auto row{ 0u }; row <= viewmodel_fit_samples; row++)
						{
							for (auto column{ 0u }; column + row <= viewmodel_fit_samples; column++)
							{
								visit(a + (b - a) * (static_cast<std::float_t>(row) / static_cast<std::float_t>(viewmodel_fit_samples)) + (c - a) * (static_cast<std::float_t>(column) / static_cast<std::float_t>(viewmodel_fit_samples)));
							}
						}
					}
				}
			};

		scan([&](structures::vec3_s point)
			{
				lowest = std::fabs(point.x) < viewmodel_fit_window.x && std::fabs(point.z) < viewmodel_fit_window.y ? std::min(lowest, point.y) : lowest;
			});

		scan([&](structures::vec3_s point)
			{
				front = std::fabs(point.z) < viewmodel_fit_band && point.x < 0.075f && point.x > -0.06f && point.y < lowest + 0.07f ? std::max(front, point.x) : front;
			});

		const structures::vec2_s shift{ front > -FLT_MAX ? std::clamp(viewmodel_grip_lead - front, -0.07f, 0.0f) : -0.014f, viewmodel_palm_gap - (lowest < FLT_MAX ? lowest : -0.016f) };

		for (auto& point : fit_triangles)
		{
			point = mathematics.transform_point(point + structures::vec3_s{ shift.x, shift.y, 0.0f }, frame);
		}

		return shift;
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s viewmodel_c::knuckles(std::int32_t owner, std::int32_t first_bone, std::int32_t last_bone)
	{
		const auto origin{ globals[owner].row3(3u) };
		const auto x_axis{ mathematics.normalize(globals[owner].row3(0u)) };
		const auto y_axis{ mathematics.normalize(globals[owner].row3(1u)) };
		const auto z_axis{ mathematics.normalize(globals[owner].row3(2u)) };
		const auto first{ globals[first_bone].row3(3u) - origin };
		const auto last{ globals[last_bone].row3(3u) - origin };
		const structures::vec3_s start{ mathematics.dot(first, x_axis), mathematics.dot(first, y_axis), mathematics.dot(first, z_axis) };
		const structures::vec3_s finish{ mathematics.dot(last, x_axis), mathematics.dot(last, y_axis), mathematics.dot(last, z_axis) };
		const auto across{ mathematics.normalize(finish - start) };
		const auto lift{ mathematics.normalize(structures::vec3_s{ 0.0f, 1.0f, 0.0f } - across * across.y) };

		return mathematics.basis(mathematics.cross(lift, across), lift, across, (start + finish) * 0.5f);
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::measure()
	{
		characters.rest(arms, pose);

		compute_globals();

		const auto origin{ globals[hand].row3(3u) };
		const auto x_axis{ mathematics.normalize(globals[hand].row3(0u)) };
		const auto y_axis{ mathematics.normalize(globals[hand].row3(1u)) };
		const auto z_axis{ mathematics.normalize(globals[hand].row3(2u)) };

		const auto local = [&](structures::vec3_s point)
			{
				const auto offset{ point - origin };

				return structures::vec3_s{ mathematics.dot(offset, x_axis), mathematics.dot(offset, y_axis), mathematics.dot(offset, z_axis) };
			};

		for (auto& frame : grip_frames)
		{
			frame = mathematics.basis({ 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, { viewmodel_grip_forward, viewmodel_grip_palm, 0.0f });
		}

		for (auto& frame : support_frames)
		{
			frame = grip_frames[0];
		}

		palm_frame = mathematics.basis({ 1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f, 1.0f }, { 0.09f, 0.0f, 0.0f });
		left_palm_frame = palm_frame;

		if (fingers[1][0] >= 0 && fingers[4][0] >= 0 && fingers[0][0] >= 0 && fingers[0][2] >= 0)
		{
			const structures::vec3_s candidates[4] = { { 1.0f, 0.0f, 0.0f }, { -1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f }, { 0.0f, -1.0f, 0.0f } };

			auto highest{ -FLT_MAX };

			palm_frame = knuckles(hand, fingers[1][0], fingers[4][0]);

			for (const auto& candidate : candidates)
			{
				pose.rotations[fingers[0][0]] = mathematics.quat_multiply(arms.bones[fingers[0][0]].rotation, mathematics.quat_axis_angle(candidate, 0.5f));

				compute_globals();

				if (const auto height{ mathematics.dot(local(globals[fingers[0][2]].row3(3u)), palm_frame.row3(1u)) }; height > highest)
				{
					highest = height;
					thumb_axis = candidate;
				}
			}

			characters.rest(arms, pose);

			compute_globals();
		}

		if (left_hand >= 0 && left_fingers[1][0] >= 0 && left_fingers[4][0] >= 0)
		{
			left_palm_frame = knuckles(left_hand, left_fingers[4][0], left_fingers[1][0]);
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t viewmodel_c::contacts(std::int32_t owner, const std::int32_t (&chain)[3], const std::float_t (&curls)[3], std::float_t sign, std::uint32_t finger)
	{
		for (auto joint{ 0u }; joint < 3u; joint++)
		{
			if (chain[joint] >= 0)
			{
				pose.rotations[chain[joint]] = mathematics.quat_multiply(finger == 0u && joint == 0u && owner == hand ? mathematics.quat_multiply(arms.bones[chain[joint]].rotation, mathematics.quat_axis_angle(thumb_axis, fit_swing)) : arms.bones[chain[joint]].rotation, mathematics.quat_axis_angle({ 0.0f, 0.0f, 1.0f }, curls[joint] * sign));
			}
		}

		compute_globals();

		const auto origin{ globals[owner].row3(3u) };
		const auto x_axis{ mathematics.normalize(globals[owner].row3(0u)) };
		const auto y_axis{ mathematics.normalize(globals[owner].row3(1u)) };
		const auto z_axis{ mathematics.normalize(globals[owner].row3(2u)) };

		const auto local = [&](structures::vec3_s point)
			{
				const auto offset{ point - origin };

				return structures::vec3_s{ mathematics.dot(offset, x_axis), mathematics.dot(offset, y_axis), mathematics.dot(offset, z_axis) };
			};

		structures::vec3_s points[4]{};

		auto count{ 0u };

		for (auto joint{ 0u }; joint < 3u && chain[joint] >= 0; joint++)
		{
			points[count++] = local(globals[chain[joint]].row3(3u));
		}

		if (count >= 2u)
		{
			const auto last{ globals[chain[count - 1u]] };

			points[count] = local(last.row3(3u) + mathematics.normalize(last.row3(0u)) * (mathematics.distance(points[count - 1u], points[count - 2u]) * 0.85f));
			count++;
		}

		const auto radius{ viewmodel_fit_radius[finger] };

		auto mask{ 0u };

		for (auto segment{ 0u }; segment + 1u < count; segment++)
		{
			const auto low{ mathematics.minimum(points[segment], points[segment + 1u]) - structures::vec3_s{ radius, radius, radius } };
			const auto high{ mathematics.maximum(points[segment], points[segment + 1u]) + structures::vec3_s{ radius, radius, radius } };

			for (auto index{ 0u }; index + 2u < fit_triangles.size() && (mask & (1u << segment)) == 0u; index += 3u)
			{
				const auto& a{ fit_triangles[index] };
				const auto& b{ fit_triangles[index + 1u] };
				const auto& c{ fit_triangles[index + 2u] };
				const auto tri_low{ mathematics.minimum(mathematics.minimum(a, b), c) };
				const auto tri_high{ mathematics.maximum(mathematics.maximum(a, b), c) };

				if (tri_low.x <= high.x && tri_high.x >= low.x && tri_low.y <= high.y && tri_high.y >= low.y && tri_low.z <= high.z && tri_high.z >= low.z && mathematics.segment_triangle(points[segment], points[segment + 1u], a, b, c) < radius)
				{
					mask |= 1u << segment;
				}
			}
		}

		return mask;
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::fit(bool left, bool swinging, std::float_t (&out)[5][3])
	{
		const auto owner{ left ? left_hand : hand };
		const auto sign{ left ? left_palm : 1.0f };

		bool buried[5]{};

		characters.rest(arms, pose);

		fit_swing = 0.0f;

		for (auto finger{ 0u }; finger < 5u; finger++)
		{
			const auto& chain{ left ? left_fingers[finger] : fingers[finger] };
			const auto& limits{ viewmodel_fit_limits[finger ? 1u : 0u] };

			std::fill(std::begin(out[finger]), std::end(out[finger]), 0.0f);

			for (; finger == 0u && swinging && fit_swing < viewmodel_swing_limit && contacts(owner, chain, out[finger], sign, finger); fit_swing += viewmodel_swing_step)
			{
			}

			buried[finger] = contacts(owner, chain, out[finger], sign, finger) != 0u;

			std::float_t trial[3]{};

			bool frozen[3]{};

			for (auto step{ 1u }; step <= viewmodel_fit_steps && buried[finger] == false; step++)
			{
				for (auto joint{ 0u }; joint < 3u; joint++)
				{
					trial[joint] = frozen[joint] ? out[finger][joint] : limits[joint] * static_cast<std::float_t>(step) / static_cast<std::float_t>(viewmodel_fit_steps);
				}

				if (const auto mask{ contacts(owner, chain, trial, sign, finger) }; mask)
				{
					for (auto joint{ 0u }; joint <= (mask & 4u ? 2u : (mask & 2u ? 1u : 0u)); joint++)
					{
						frozen[joint] = true;
					}
				}

				else
				{
					std::copy(std::begin(trial), std::end(trial), std::begin(out[finger]));
				}
			}
		}

		for (auto finger{ 1u }; finger < 5u; finger++)
		{
			if (const auto donor{ finger == 4u ? 3u : (finger == 1u ? 2u : (buried[finger - 1u] ? finger + 1u : finger - 1u)) }; buried[finger])
			{
				std::copy(std::begin(out[donor]), std::end(out[donor]), std::begin(out[finger]));
			}
		}

		if (buried[0])
		{
			std::copy(std::begin(viewmodel_thumb), std::end(viewmodel_thumb), std::begin(out[0]));

			fit_swing = 0.0f;
		}

		characters.rest(arms, pose);

		compute_globals();
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::fit_item(std::uint32_t item, bool seated)
	{
		structures::vec2_s shift{};

		if (seated)
		{
			gather(mathematics.basis({ 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, {}));

			shift = settle(palm_frame);

			grip_frames[item] = mathematics.multiply(mathematics.basis({ 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, { shift.x, shift.y, 0.0f }), palm_frame);
		}

		else
		{
			gather(grip_frames[item]);
		}

		fitted[item] = fit_triangles.size() > 0u;

		if (fitted[item])
		{
			fit(false, seated, grips[item]);

			thumb_swings[item] = fit_swing;
		}

		logger.write("viewmodel: grip %s from %zu tris, shift %.3f %.3f, swing %.2f, thumb %.2f %.2f %.2f index %.2f %.2f %.2f middle %.2f %.2f %.2f ring %.2f %.2f %.2f pinky %.2f %.2f %.2f", item_definitions[item].name, fit_triangles.size() / 3u, shift.x, shift.y, thumb_swings[item], grips[item][0][0], grips[item][0][1], grips[item][0][2], grips[item][1][0], grips[item][1][1], grips[item][1][2], grips[item][2][0], grips[item][2][1], grips[item][2][2], grips[item][3][0], grips[item][3][1], grips[item][3][2], grips[item][4][0], grips[item][4][1], grips[item][4][2]);
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::fit_support(std::uint32_t weapon)
	{
		const auto& model{ gun_models[weapon] };
		const auto finger_axis{ mathematics.normalize(model.support_fingers) };
		const auto palm_axis{ mathematics.normalize(model.support_palm - finger_axis * mathematics.dot(model.support_palm, finger_axis)) };
		const auto anchor{ mathematics.basis(finger_axis, mathematics.cross(palm_axis, finger_axis), palm_axis, model.support) };

		gather(mathematics.multiply(mathematics.multiply(mathematics.inverse(gun_frames[weapon]), mathematics.inverse(anchor)), mathematics.basis({ 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, {})));

		const auto shift{ settle(left_palm_frame) };

		support_frames[weapon] = mathematics.multiply(mathematics.basis({ 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, { shift.x, shift.y, 0.0f }), left_palm_frame);
		support_fitted[weapon] = fit_triangles.size() > 0u && left_hand >= 0;

		if (support_fitted[weapon])
		{
			fit(true, false, support_grips[weapon]);
		}

		logger.write("viewmodel: support grip %s from %zu tris, shift %.3f %.3f, index %.2f %.2f %.2f middle %.2f %.2f %.2f thumb %.2f %.2f %.2f", item_definitions[weapon_definitions[weapon].item].name, fit_triangles.size() / 3u, shift.x, shift.y, support_grips[weapon][1][0], support_grips[weapon][1][1], support_grips[weapon][1][2], support_grips[weapon][2][0], support_grips[weapon][2][1], support_grips[weapon][2][2], support_grips[weapon][0][0], support_grips[weapon][0][1], support_grips[weapon][0][2]);
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::stick(std::uint32_t material, std::float_t radius, std::float_t bottom, std::float_t top)
	{
		const auto first_vertex{ static_cast<std::uint32_t>(tool_builder.vertices.size()) };
		const auto first_index{ static_cast<std::uint32_t>(tool_builder.indices.size()) };

		tool_builder.set_material(material);
		tool_builder.cylinder({ 0.0f, bottom, 0.0f }, { 0.0f, 1.0f, 0.0f }, radius, top - bottom, 12u, true);

		for (auto index{ first_vertex }; index < tool_builder.vertices.size(); index++)
		{
			tool_builder.vertices[index].uv = tool_builder.vertices[index].uv * 2.0f;
		}

		tool_builder.compute_tangents(first_vertex, first_index);
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::stone(const structures::model_s& source, structures::vec3_s size, structures::vec3_s center, std::float_t yaw)
	{
		const auto extent{ source.bounds_max - source.bounds_min };
		const auto middle{ (source.bounds_min + source.bounds_max) * 0.5f };
		const auto scale{ structures::vec3_s{ size.z / extent.x, size.y / extent.y, size.x / extent.z } };

		for (const auto& part : source.parts)
		{
			tool_builder.append(source, part.first_index, part.index_count, mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-middle), mathematics.scaling(scale)), mathematics.rotation_y(yaw)), mathematics.translation(center)));
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::update(std::float_t delta)
	{
		const auto item{ survival.held().item };

		visible = ready && (tools[item].index_count > 0u || item == structures::item_none) && survival.vitals.dead == false && weapons.scoped == false;

		if (item != shown_item)
		{
			shown_item = item;
			equip = 0.0f;
			inspecting = false;

			if (visible)
			{
				mixer.play_2d(structures::sound_equip, 0.45f, 0.95f + mixer.random() * 0.1f);
			}
		}

		swim_blend = mathematics.approach(swim_blend, (player.state.flags & structures::movement_swimming) ? 1.0f : 0.0f, delta * 2.5f);
		swim_phase = std::fmod(swim_phase + delta * (swim_stroke_rate + swim_stroke_speed_rate * mathematics.length(player.state.velocity)) * mathematics.smoothstep(0.5f, 1.0f, swim_blend), 1.0f);
		stowed = swim_blend > 0.5f;

		if (visible)
		{
			clock += delta;
			equip = std::min(1.0f, equip + delta / viewmodel_equip_time);
			sway_x = mathematics.clamp(mathematics.damp(sway_x, -platform.input.mouse_delta.x * viewmodel_sway, 9.0f, delta), -0.035f, 0.035f);
			sway_y = mathematics.clamp(mathematics.damp(sway_y, platform.input.mouse_delta.y * viewmodel_sway, 9.0f, delta), -0.035f, 0.035f);

			if (item == structures::item_none || stowed)
			{
				previous_palette = palette;
				previous_tool_world = tool_world;

				pose_fists(delta);

				two_handed = left_hand >= 0 && arms_left.mesh.index_count > 0u;
			}

			else
			{
				pose_tool(item);
			}

			showcase(item, delta);

			for (auto index{ 0u }; index < arms.bones.size(); index++)
			{
				palette[index] = mathematics.multiply(arms.bones[index].inverse_bind, globals[index]);
			}

			if (item == structures::item_torch && stowed == false)
			{
				particles.torch(mathematics.transform_point({ 0.0f, 0.37f, 0.0f }, tool_world), delta);
			}

			if (history == false)
			{
				previous_palette = palette;
				previous_tool_world = tool_world;
				previous_bolt_world = bolt_world;
				previous_magazine_world = magazine_world;
				history = true;
			}
		}

		else
		{
			history = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::pose_tool(std::uint32_t item)
	{
		const auto gun{ item_definitions[item].weapon };

		if (gun != structures::weapon_none)
		{
			const auto& hip{ weapon_holds[gun][0] };
			const auto& sight{ weapon_holds[gun][1] };
			const auto bolted{ gun_models[gun].action == structures::action_bolt };
			const auto clear{ weapons.clearing > 0.0f ? std::sin(mathematics.saturate(1.0f - weapons.clearing / weapon_definitions[gun].clear_time) * pi) : 0.0f };
			const auto dip{ std::max(weapons.reloading > 0.0f ? std::sin(mathematics.saturate(1.0f - weapons.reloading / weapon_definitions[gun].reload) * pi) : 0.0f, bolted ? 0.0f : clear * 0.4f) };
			const auto work{ std::max(weapons.cycled ? 0.0f : std::sin(mathematics.saturate(weapons.cycle / weapon_cycle_time) * pi), bolted ? clear : 0.0f) };
			const auto focus{ gun_models[gun].action == structures::action_draw ? mathematics.smoothstep(0.0f, 1.0f, std::max(weapons.aim * 0.6f, std::min(1.0f, weapons.draw * 1.6f))) : weapons.aim };
			const auto strain{ gun_models[gun].action == structures::action_draw ? mathematics.smoothstep(0.85f, 1.0f, weapons.draw) : 0.0f };

			wrist = mathematics.lerp(hip.wrist, sight.wrist, focus) + reload_poses[gun].wrist * dip + structures::vec3_s{ 0.015f * work + std::sin(clock * 23.0f) * 0.0012f * strain, 0.01f * weapons.kick - 0.035f * work + std::sin(clock * 29.0f + 1.0f) * 0.0012f * strain, -0.05f * weapons.kick + 0.03f * work };
			angles = mathematics.lerp(hip.angles, sight.angles, focus) + reload_poses[gun].angles * dip + structures::vec3_s{ -0.22f * weapons.kick + 0.1f * work, 0.0f, 0.45f * work };
		}

		else
		{
			sample(harvest.swinging ? harvest.swing_timer / std::max(harvest.swing_length, 0.01f) : 0.0f);
		}

		const auto& hold{ viewmodel_holds[gun != structures::weapon_none ? 0u : item] };
		const auto lowered{ std::max(1.0f - mathematics.ease_out_cubic(equip), std::min(swim_blend * 2.0f, 1.0f)) };
		const auto steady{ 1.0f - weapons.aim * 0.8f };
		const auto bob{ player.bob_weight * (harvest.swinging ? 0.3f : 1.0f) * steady };
		const structures::vec3_s motion{ std::sin(player.bob_phase * pi) * 0.011f * bob + sway_x * steady, -(0.5f - 0.5f * std::cos(player.bob_phase * two_pi)) * 0.013f * bob + std::sin(clock * 1.7f) * 0.003f * steady + sway_y * steady - lowered * 0.28f, 0.0f };
		const auto view_angles{ angles + hold.angles + structures::vec3_s{ lowered * (gun != structures::weapon_none ? 0.6f : -0.9f), 0.0f, 0.0f } };
		const auto rotation{ mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, view_angles.y), mathematics.quat_multiply(mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, view_angles.x), mathematics.quat_axis_angle({ 0.0f, 0.0f, 1.0f }, view_angles.z))) };

		previous_palette = palette;
		previous_tool_world = tool_world;
		previous_bolt_world = bolt_world;
		previous_magazine_world = magazine_world;
		const auto studied{ inspect >= 0.0f };
		const auto upright{ mathematics.normalize(structures::vec3_s{ 0.0f, 1.0f, 0.25f }) };
		const auto turned{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, degrees_to_radians(inspect)) };
		const auto pivot{ gun != structures::weapon_none ? (inspect >= 360.0f ? gun_models[gun].support : gun_models[gun].grip) : structures::vec3_s{} };

		hand_fingers = studied ? upright : mathematics.quat_rotate(rotation, { 0.0f, 0.0f, 1.0f });
		hand_palm = studied ? mathematics.quat_rotate(mathematics.quat_axis_angle(upright, degrees_to_radians(inspect)), { -1.0f, 0.0f, 0.0f }) : mathematics.quat_rotate(rotation, { -1.0f, 0.0f, 0.0f });
		hand_wrist = studied ? viewmodel_study_wrist : wrist + hold.wrist + motion;

		if (gun != structures::weapon_none)
		{
			place_gun(gun, studied ? turned : rotation, studied ? viewmodel_study_gun - mathematics.quat_rotate(turned, { 0.0f, 0.0f, 1.0f }) * pivot.x - mathematics.quat_rotate(turned, { 0.0f, 1.0f, 0.0f }) * pivot.y - mathematics.quat_rotate(turned, { -1.0f, 0.0f, 0.0f }) * pivot.z : wrist + motion);
		}

		solve(to_model(hand_wrist), { -hand_fingers.x, hand_fingers.y, -hand_fingers.z }, { -hand_palm.x, hand_palm.y, -hand_palm.z });

		curl(gun != structures::weapon_none && reaching > 0.5f ? structures::item_count : item);
		twist(0u);

		compute_globals();

		if (gun == structures::weapon_none)
		{
			const auto x_axis{ mathematics.normalize(globals[hand].row3(0u)) };
			const auto y_axis{ mathematics.normalize(globals[hand].row3(1u)) };
			const auto z_axis{ mathematics.normalize(globals[hand].row3(2u)) };

			tool_world = mathematics.multiply(mathematics.multiply(grip_frames[item], mathematics.basis(x_axis, y_axis, z_axis, globals[hand].row3(3u))), world);
		}

		two_handed = (gun == structures::weapon_rifle || gun == structures::weapon_bow || gun == structures::weapon_assault) && left_hand >= 0 && arms_left.mesh.index_count > 0u;

		if (two_handed)
		{
			const auto& model{ gun_models[gun] };
			const auto knob{ mathematics.transform_point(model.bolt_knob - structures::vec3_s{ charge_pull * model.bolt_throw, 0.0f, 0.0f }, gun_placement) };
			const auto grip{ mathematics.lerp(mathematics.transform_point(model.support, gun_placement), mathematics.transform_point(model.magazine_grip, magazine_world), magazine_hold) };
			const auto reach_fingers{ mathematics.lerp(mathematics.lerp(mathematics.transform_vector(model.support_fingers, gun_placement), mathematics.transform_vector(viewmodel_magazine_fingers, magazine_world), magazine_hold), mathematics.transform_vector(viewmodel_charge_fingers, gun_placement), charge_grab) };
			const auto reach_palm{ mathematics.lerp(mathematics.lerp(mathematics.transform_vector(model.support_palm, gun_placement), mathematics.transform_vector(viewmodel_magazine_palm, magazine_world), magazine_hold), mathematics.transform_vector(viewmodel_charge_palm, gun_placement), charge_grab) };

			support(mathematics.lerp(grip, knob, charge_grab), reach_fingers, reach_palm, gun);
			twist(1u);

			compute_globals();
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::showcase(std::uint32_t item, std::float_t delta)
	{
		const auto& mesh{ tools[item] };

		if (platform.input.pressed[inspect_key] && platform.mouse_captured && survival.inventory_open == false && stowed == false && mesh.index_count > 0u)
		{
			inspecting = inspecting == false;
			inspect_yaw = 0.0f;
			inspect_pitch = 0.0f;
			inspect_idle = 0.0f;
			inspect_zoom = 1.0f;
		}

		inspecting = inspecting && survival.inventory_open == false && stowed == false && mesh.index_count > 0u;
		inspect_blend = mathematics.damp(inspect_blend, inspecting ? 1.0f : 0.0f, 6.0f, delta);

		if (inspect_blend > 0.001f && mesh.index_count > 0u)
		{
			const auto gun{ item_definitions[item].weapon };
			const auto frames{ gun != structures::weapon_none ? gun_frames[gun] : mathematics.identity() };
			const auto unframe{ mathematics.inverse(frames) };

			auto low{ structures::vec3_s{ FLT_MAX, FLT_MAX, FLT_MAX } };
			auto high{ structures::vec3_s{ -FLT_MAX, -FLT_MAX, -FLT_MAX } };

			for (auto corner{ 0u }; corner < 8u; corner++)
			{
				const auto tool_corner{ mathematics.transform_point({ corner & 1u ? mesh.bounds_max.x : mesh.bounds_min.x, corner & 2u ? mesh.bounds_max.y : mesh.bounds_min.y, corner & 4u ? mesh.bounds_max.z : mesh.bounds_min.z }, unframe) };

				low = mathematics.minimum(low, tool_corner);
				high = mathematics.maximum(high, tool_corner);

				if (bolts[gun].index_count > 0u)
				{
					const structures::vec3_s bolt_corner{ corner & 1u ? bolts[gun].bounds_max.x : bolts[gun].bounds_min.x, corner & 2u ? bolts[gun].bounds_max.y : bolts[gun].bounds_min.y, corner & 4u ? bolts[gun].bounds_max.z : bolts[gun].bounds_min.z };

					low = mathematics.minimum(low, bolt_corner);
					high = mathematics.maximum(high, bolt_corner);
				}

				if (magazines[gun].index_count > 0u)
				{
					const structures::vec3_s magazine_corner{ corner & 1u ? magazines[gun].bounds_max.x : magazines[gun].bounds_min.x, corner & 2u ? magazines[gun].bounds_max.y : magazines[gun].bounds_min.y, corner & 4u ? magazines[gun].bounds_max.z : magazines[gun].bounds_min.z };

					low = mathematics.minimum(low, magazine_corner);
					high = mathematics.maximum(high, magazine_corner);
				}
			}

			if (inspecting)
			{
				char text[96]{};

				inspect_idle = std::fabs(platform.input.mouse_delta.x) + std::fabs(platform.input.mouse_delta.y) > 0.5f ? 0.0f : inspect_idle + delta;
				inspect_yaw += platform.input.mouse_delta.x * inspect_mouse_rate + (inspect_idle > inspect_idle_time ? delta * inspect_spin_rate : 0.0f);
				inspect_pitch = mathematics.clamp(inspect_pitch + platform.input.mouse_delta.y * inspect_mouse_rate, -1.2f, 1.2f);
				inspect_zoom = mathematics.clamp(inspect_zoom - platform.input.wheel * inspect_zoom_rate, inspect_zoom_min, inspect_zoom_max);

				std::snprintf(text, sizeof(text), "%s   drag to turn   wheel to zoom   [I] close", item_definitions[item].name);

				hud.set_prompt(text);
			}

			const auto radius{ mathematics.length(high - low) * 0.5f };
			const auto distance{ radius / std::tan(renderer.camera.viewmodel_fov * 0.5f) * inspect_framing * inspect_zoom };
			const auto turn{ mathematics.quat_multiply(mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, inspect_pitch), mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, pi + inspect_yaw)) };
			const auto placement{ mathematics.multiply(mathematics.multiply(mathematics.translation(-(low + high) * 0.5f), mathematics.rotation(turn)), mathematics.translation({ 0.0f, radius * inspect_lift, distance })) };

			tool_world = blend_rigid(tool_world, mathematics.multiply(unframe, placement), mathematics.smoothstep(0.0f, 1.0f, inspect_blend));

			if (gun != structures::weapon_none)
			{
				gun_placement = mathematics.multiply(frames, tool_world);
				bolt_world = gun_placement;
				magazine_world = gun_placement;
				nock = mathematics.transform_point(gun_models[gun].bolt_knob, gun_placement);
				weapons.muzzle = mathematics.transform_point(gun_models[gun].muzzle, gun_placement);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s viewmodel_c::blend_rigid(const structures::mat4_s& from, const structures::mat4_s& to, std::float_t t)
	{
		const auto start{ mathematics.quat_from_basis(mathematics.normalize(from.row3(0u)), mathematics.normalize(from.row3(1u)), mathematics.normalize(from.row3(2u))) };
		const auto end{ mathematics.quat_from_basis(mathematics.normalize(to.row3(0u)), mathematics.normalize(to.row3(1u)), mathematics.normalize(to.row3(2u))) };
		const auto rotation{ mathematics.quat_slerp(start, end, t) };

		return mathematics.basis(mathematics.quat_rotate(rotation, { 1.0f, 0.0f, 0.0f }), mathematics.quat_rotate(rotation, { 0.0f, 1.0f, 0.0f }), mathematics.quat_rotate(rotation, { 0.0f, 0.0f, 1.0f }), mathematics.lerp(from.row3(3u), to.row3(3u), t));
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::pose_fists(std::float_t delta)
	{
		const auto speed{ mathematics.length(structures::vec3_s{ player.state.velocity.x, 0.0f, player.state.velocity.z }) };
		const auto on_ground{ (player.state.flags & structures::movement_on_ground) != 0u };
		const auto sprinting{ (player.command.buttons & structures::button_sprint) != 0u && speed > move_speed_run * 0.85f && on_ground };
		const auto phase{ harvest.swinging ? mathematics.saturate(harvest.swing_timer / std::max(harvest.swing_length, 0.01f)) : 0.0f };
		const auto extend{ mathematics.smoothstep(0.06f, 0.34f, phase) * (1.0f - mathematics.smoothstep(0.46f, 0.95f, phase)) };
		const auto lowered{ std::max(1.0f - mathematics.ease_out_cubic(equip), stowed ? (1.0f - swim_blend) * 2.0f : 0.0f) };
		const auto stroke{ mathematics.smoothstep(0.5f, 1.0f, swim_blend) };
		const auto stride{ player.bob_phase * pi };
		const auto weight{ player.bob_weight };

		if (harvest.swinging && punching == false)
		{
			punch_side ^= 1u;
		}

		if (grounded == false && on_ground)
		{
			land_kick = std::min(1.0f, land_kick + 0.6f);
		}

		punching = harvest.swinging;
		grounded = on_ground;
		land_kick = mathematics.damp(land_kick, 0.0f, 6.0f, delta);
		sprint_blend = mathematics.damp(sprint_blend, sprinting ? 1.0f : 0.0f, 5.0f, delta);
		air_blend = mathematics.damp(air_blend, on_ground ? 0.0f : 1.0f, 7.0f, delta);
		turn_lag = mathematics.damp(turn_lag, mathematics.clamp(-platform.input.mouse_delta.x * 0.0011f, -0.12f, 0.12f), 7.0f, delta);
		pitch_lag = mathematics.damp(pitch_lag, mathematics.clamp(platform.input.mouse_delta.y * 0.0011f, -0.12f, 0.12f), 7.0f, delta);

		characters.rest(arms, pose);

		compute_globals();

		for (auto side{ 0u }; side < 2u; side++)
		{
			const auto sign{ side ? -1.0f : 1.0f };
			const auto seed{ side ? 7.31f : 1.13f };
			const auto breath{ std::sin(clock * two_pi * hands_breath_rate + (side ? 0.4f : 0.0f)) };
			const auto pump{ std::sin(stride + (side ? pi : 0.0f)) };
			const auto active{ harvest.swinging && side == punch_side ? extend : 0.0f };
			const auto guard_up{ harvest.swinging && side != punch_side ? extend : 0.0f };

			auto frame{ guard_frames[side] };

			frame.wrist = mathematics.lerp(frame.wrist, punch_frames[side].wrist, active);
			frame.fingers = mathematics.normalize(mathematics.lerp(frame.fingers, punch_frames[side].fingers, active));
			frame.palm = mathematics.normalize(mathematics.lerp(frame.palm, punch_frames[side].palm, active));

			frame.wrist = frame.wrist + structures::vec3_s{ -0.012f * sign * guard_up, 0.018f * guard_up, -0.03f * guard_up };
			frame.wrist = frame.wrist + structures::vec3_s{ wave(clock * 0.37f, seed), wave(clock * 0.29f, seed + 2.0f) + breath * 0.45f, wave(clock * 0.23f, seed + 4.0f) } * hands_drift;
			frame.wrist = frame.wrist + structures::vec3_s{ std::sin(stride) * hands_step_swing * 0.6f, -(0.5f - 0.5f * std::cos(stride * 2.0f)) * hands_step_dip, pump * hands_step_swing * sign * 0.5f } * weight * (1.0f - sprint_blend);
			frame.wrist = frame.wrist + structures::vec3_s{ -0.035f * sign, -0.075f + pump * hands_sprint_pump * 0.5f, -0.04f + pump * hands_sprint_pump } * sprint_blend;
			frame.wrist = frame.wrist + structures::vec3_s{ 0.0f, 0.03f * air_blend - 0.045f * land_kick, 0.0f };
			frame.wrist = frame.wrist + structures::vec3_s{ sway_x + turn_lag * 0.12f, sway_y - lowered * 0.3f, 0.0f };

			if (stroke > 0.001f)
			{
				const auto swimming_frame{ swim_frame(side, swim_phase) };

				frame.wrist = mathematics.lerp(frame.wrist, swimming_frame.wrist + structures::vec3_s{ sway_x, sway_y - lowered * 0.3f, 0.0f }, stroke);
				frame.fingers = mathematics.normalize(mathematics.lerp(frame.fingers, swimming_frame.fingers, stroke));
				frame.palm = mathematics.normalize(mathematics.lerp(frame.palm, swimming_frame.palm, stroke));
			}

			frame = tilt(frame, structures::vec3_s{ wave(clock * 0.31f, seed + 6.0f) * hands_wobble + breath * 0.01f + pitch_lag + pump * 0.25f * sprint_blend + lowered * 0.9f, wave(clock * 0.27f, seed + 8.0f) * hands_wobble + turn_lag, wave(clock * 0.35f, seed + 9.0f) * hands_wobble * 0.7f });

			if (inspect >= 0.0f)
			{
				frame = side ? structures::hand_frame_s{ { -0.3f, -0.5f, 0.1f }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 0.0f, 0.0f } } : structures::hand_frame_s{ { 0.0f, -0.11f, 0.2f }, mathematics.normalize(structures::vec3_s{ 0.0f, 1.0f, 0.25f }), mathematics.quat_rotate(mathematics.quat_axis_angle(structures::vec3_s{ 0.0f, 1.0f, 0.25f }, degrees_to_radians(inspect)), { -1.0f, 0.0f, 0.0f }) };
			}

			solve_arm(side, frame);
		}

		const auto clench{ mathematics.lerp(0.94f + 0.04f * std::sin(clock * two_pi * hands_breath_rate) + 0.06f * extend, swim_hand_clench, stroke) };

		fist(0u, clench);
		fist(1u, clench);
		twist(0u);
		twist(1u);

		compute_globals();
	}
	/*
	//=====================================================================================
	*/
	structures::hand_frame_s viewmodel_c::swim_frame(std::uint32_t side, std::float_t phase)
	{
		const auto sign{ side ? -1.0f : 1.0f };

		auto result{ swim_frames[0] };

		for (auto key{ 0u }; key < 3u; key++)
		{
			if (phase >= swim_frame_times[key] && phase <= swim_frame_times[key + 1u])
			{
				const auto& from{ swim_frames[key] };
				const auto& to{ swim_frames[(key + 1u) % 3u] };
				const auto t{ mathematics.smoothstep(0.0f, 1.0f, (phase - swim_frame_times[key]) / (swim_frame_times[key + 1u] - swim_frame_times[key])) };

				result = { mathematics.lerp(from.wrist, to.wrist, t), mathematics.normalize(mathematics.lerp(from.fingers, to.fingers, t)), mathematics.normalize(mathematics.lerp(from.palm, to.palm, t)) };
			}
		}

		result.wrist.x *= sign;
		result.fingers.x *= sign;
		result.palm.x *= sign;

		return result;
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::solve_arm(std::uint32_t side, const structures::hand_frame_s& frame)
	{
		const auto upper{ side ? left_upper : upper_arm };
		const auto lower{ side ? left_forearm : forearm };
		const auto hand_bone{ side ? left_hand : hand };

		if (upper >= 0 && lower >= 0 && hand_bone >= 0)
		{
			const auto target{ to_model(frame.wrist) };
			const structures::vec3_s fingers_model{ -frame.fingers.x, frame.fingers.y, -frame.fingers.z };
			const structures::vec3_s palm_model{ -frame.palm.x, frame.palm.y, -frame.palm.z };
			const auto pole{ side ? viewmodel_left_pole : viewmodel_pole };
			const auto sign{ side ? left_hinge_sign : hinge_sign };
			const auto shoulder{ globals[upper].row3(3u) };
			const auto offset{ target - shoulder };
			const auto reach{ std::clamp(mathematics.length(offset), 0.05f, (upper_length + lower_length) * 0.998f) };
			const auto along{ mathematics.normalize(offset) };
			const auto bend{ mathematics.normalize(pole - along * mathematics.dot(pole, along)) };
			const auto cosine{ std::clamp((upper_length * upper_length + reach * reach - lower_length * lower_length) / (2.0f * upper_length * reach), -1.0f, 1.0f) };
			const auto elbow{ shoulder + (along * cosine + bend * std::sqrt(1.0f - cosine * cosine)) * upper_length };
			const auto hinge{ mathematics.normalize(mathematics.cross(along, bend)) * -sign };
			const auto forearm_direction{ mathematics.normalize(shoulder + along * reach - elbow) };
			const auto fingers_direction{ mathematics.normalize(mathematics.lerp(forearm_direction, mathematics.normalize(fingers_model), inspect >= 0.0f ? 1.0f : viewmodel_wrist_freedom)) };
			const auto palm{ mathematics.normalize(palm_model - fingers_direction * mathematics.dot(palm_model, fingers_direction)) };

			orient(upper, mathematics.normalize(elbow - shoulder), hinge);
			orient(lower, forearm_direction, hinge);
			orient(hand_bone, fingers_direction, mathematics.cross(fingers_direction, palm * (side ? left_palm : 1.0f)));
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::fist(std::uint32_t side, std::float_t clench)
	{
		const auto& set{ side ? left_fingers : fingers };

		for (auto finger{ 0u }; finger < 5u; finger++)
		{
			for (auto joint{ 0u }; joint < 3u; joint++)
			{
				if (const auto bone{ set[finger][joint] }; bone >= 0)
				{
					const auto flex{ finger ? mathematics.quat_axis_angle({ 0.0f, 0.0f, 1.0f }, fist_curl[finger][joint] * clench) : mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 0.0f, 1.0f }, fist_thumb[joint].x * clench), mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, fist_thumb[joint].y * (side ? -1.0f : 1.0f) * clench)) };
					const auto gather{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, joint == 0u ? spreads[side][finger] * fist_gather * clench : 0.0f) };

					pose.rotations[bone] = mathematics.quat_multiply(gather, mathematics.quat_multiply(arms.bones[bone].rotation, flex));
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::twist(std::uint32_t side)
	{
		if (const auto hand_bone{ side ? left_hand : hand }; hand_bone >= 0 && twists[side] >= 0)
		{
			const auto relative{ mathematics.quat_multiply(mathematics.quat_conjugate(arms.bones[hand_bone].rotation), pose.rotations[hand_bone]) };

			pose.rotations[twists[side]] = mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, 2.0f * std::atan2(relative.w < 0.0f ? -relative.x : relative.x, std::fabs(relative.w)));
		}
	}
	/*
	//=====================================================================================
	*/
	structures::hand_frame_s viewmodel_c::tilt(const structures::hand_frame_s& frame, structures::vec3_s turn)
	{
		const auto rotation{ mathematics.quat_multiply(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, turn.y), mathematics.quat_multiply(mathematics.quat_axis_angle({ 1.0f, 0.0f, 0.0f }, turn.x), mathematics.quat_axis_angle({ 0.0f, 0.0f, 1.0f }, turn.z))) };

		return { frame.wrist, mathematics.normalize(mathematics.quat_rotate(rotation, frame.fingers)), mathematics.normalize(mathematics.quat_rotate(rotation, frame.palm)) };
	}
	/*
	//=====================================================================================
	*/
	std::float_t viewmodel_c::wave(std::float_t time, std::float_t seed)
	{
		return (std::sin(time * 6.2f + seed) * 0.6f + std::sin(time * 13.7f + seed * 2.3f) * 0.3f + std::sin(time * 29.3f + seed * 4.1f) * 0.1f);
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::place_gun(std::uint32_t gun, structures::quat_s rotation, structures::vec3_s position)
	{
		const auto& model{ gun_models[gun] };
		const auto bolted{ model.action == structures::action_bolt };
		const auto sliding{ model.action == structures::action_slide };
		const auto clear{ weapons.clearing > 0.0f ? 1.0f - weapons.clearing / weapon_definitions[gun].clear_time : 0.0f };
		const auto phase{ bolted && weapons.clearing > 0.0f ? clear : (weapons.cycled ? 1.0f : weapons.cycle / weapon_cycle_time) };
		const auto loading{ weapons.reloading > 0.0f ? 1.0f - weapons.reloading / weapon_definitions[gun].reload : (model.action == structures::action_break ? clear : 0.0f) };
		const auto opening{ mathematics.smoothstep(0.06f, 0.16f, loading) - mathematics.smoothstep(0.86f, 0.95f, loading) };
		const auto swapping{ magazines[gun].index_count > 0u && weapons.reloading > 0.0f };
		const auto emptied{ survival.held().loaded == 0u };
		const auto dropped{ swapping ? mathematics.smoothstep(0.1f, 0.35f, loading) - mathematics.smoothstep(0.5f, 0.72f, loading) : 0.0f };
		const auto lift{ bolted ? std::max(mathematics.smoothstep(0.3f, 0.42f, phase) - mathematics.smoothstep(0.68f, 0.8f, phase), opening) : (model.action == structures::action_break ? opening : 0.0f) };

		charge_pull = weapons.jammed ? mathematics.lerp(weapon_jam_pull, 1.0f, mathematics.smoothstep(0.3f, 0.45f, clear)) : 1.0f;
		charge_grab = sliding ? std::max(weapons.clearing > 0.0f ? mathematics.smoothstep(0.0f, 0.28f, clear) - mathematics.smoothstep(0.62f, 0.9f, clear) : 0.0f, swapping && emptied ? mathematics.smoothstep(0.74f, 0.8f, loading) - mathematics.smoothstep(0.9f, 0.98f, loading) : 0.0f) : 0.0f;
		magazine_hold = swapping ? mathematics.smoothstep(0.0f, 0.1f, loading) - mathematics.smoothstep(0.72f, 0.8f, loading) : 0.0f;

		const auto stuck{ weapons.jammed ? charge_pull * (1.0f - mathematics.smoothstep(0.55f, 0.62f, clear)) : 0.0f };
		const auto pull{ bolted ? std::max(mathematics.smoothstep(0.42f, 0.55f, phase) - mathematics.smoothstep(0.55f, 0.68f, phase), mathematics.smoothstep(0.16f, 0.26f, loading) - mathematics.smoothstep(0.76f, 0.86f, loading)) : (sliding ? std::max({ mathematics.smoothstep(0.55f, 0.9f, weapons.kick), emptied ? 1.0f - mathematics.smoothstep(0.86f, 0.92f, loading) : 0.0f, stuck }) : 0.0f) };
		const auto reach{ bolted ? std::max(mathematics.smoothstep(0.12f, 0.28f, phase) - mathematics.smoothstep(0.8f, 0.95f, phase), loading > 0.0f ? mathematics.smoothstep(0.0f, 0.06f, loading) - mathematics.smoothstep(0.28f, 0.36f, loading) + mathematics.smoothstep(0.64f, 0.72f, loading) - mathematics.smoothstep(0.94f, 1.0f, loading) : 0.0f) : 0.0f };

		reaching = reach;
		gun_placement = mathematics.basis(mathematics.quat_rotate(rotation, { 0.0f, 0.0f, 1.0f }), mathematics.quat_rotate(rotation, { 0.0f, 1.0f, 0.0f }), mathematics.quat_rotate(rotation, { -1.0f, 0.0f, 0.0f }), position);
		tool_world = mathematics.multiply(mathematics.inverse(gun_frames[gun]), gun_placement);
		bolt_world = mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-model.bolt_pivot), mathematics.rotation(mathematics.quat_axis_angle(model.bolt_axis, lift * model.bolt_lift))), mathematics.translation(model.bolt_pivot - structures::vec3_s{ pull * model.bolt_throw, 0.0f, 0.0f })), gun_placement);
		magazine_world = mathematics.multiply(mathematics.multiply(mathematics.multiply(mathematics.translation(-model.magazine_grip), mathematics.rotation_z(viewmodel_magazine_tilt * dropped)), mathematics.translation(model.magazine_grip + viewmodel_magazine_drop * dropped)), gun_placement);
		weapons.muzzle = mathematics.transform_point(model.muzzle, gun_placement);
		const auto held{ mathematics.multiply(mathematics.inverse(grip_frames[weapon_definitions[gun].item]), tool_world) };
		const auto knob_fingers{ mathematics.normalize(mathematics.transform_vector(viewmodel_bolt_fingers, bolt_world)) };
		const auto knob_palm{ mathematics.normalize(mathematics.transform_vector(viewmodel_bolt_palm, bolt_world)) };

		hand_fingers = mathematics.normalize(mathematics.lerp(mathematics.normalize(held.row3(0u)), knob_fingers, reach));
		hand_palm = mathematics.normalize(mathematics.lerp(mathematics.normalize(held.row3(1u)), knob_palm, reach));
		hand_wrist = mathematics.lerp(held.row3(3u), mathematics.transform_point(model.bolt_knob, bolt_world) - knob_fingers * viewmodel_grip_forward - knob_palm * viewmodel_grip_palm, reach);

		if (model.action == structures::action_draw)
		{
			nock = mathematics.lerp(mathematics.transform_point(model.bolt_knob, gun_placement), viewmodel_bow_anchor, mathematics.smoothstep(0.0f, 1.0f, weapons.draw));
			hand_fingers = mathematics.normalize(mathematics.transform_vector({ 1.0f, -0.25f, -0.2f }, gun_placement));
			hand_palm = mathematics.normalize(mathematics.transform_vector({ 0.0f, 0.15f, 1.0f }, gun_placement));
			hand_wrist = nock - hand_fingers * (viewmodel_grip_forward + 0.012f) - hand_palm * viewmodel_grip_palm;
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::sample(std::float_t phase)
	{
		wrist = viewmodel_swing[0].wrist;
		angles = viewmodel_swing[0].angles;

		for (auto index{ 1u }; index < std::size(viewmodel_swing); index++)
		{
			const auto& from{ viewmodel_swing[index - 1u] };
			const auto& to{ viewmodel_swing[index] };

			if (phase >= from.time && phase <= to.time)
			{
				const auto t{ mathematics.smoothstep(0.0f, 1.0f, (phase - from.time) / std::max(to.time - from.time, 0.001f)) };

				wrist = mathematics.lerp(from.wrist, to.wrist, t);
				angles = mathematics.lerp(from.angles, to.angles, t);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::solve(structures::vec3_s target, structures::vec3_s fingers_direction, structures::vec3_s palm)
	{
		characters.rest(arms, pose);

		compute_globals();

		const auto shoulder{ globals[upper_arm].row3(3u) };
		const auto offset{ target - shoulder };
		const auto reach{ std::clamp(mathematics.length(offset), 0.05f, (upper_length + lower_length) * 0.998f) };
		const auto along{ mathematics.normalize(offset) };
		const auto bend{ mathematics.normalize(viewmodel_pole - along * mathematics.dot(viewmodel_pole, along)) };
		const auto cosine{ std::clamp((upper_length * upper_length + reach * reach - lower_length * lower_length) / (2.0f * upper_length * reach), -1.0f, 1.0f) };
		const auto elbow{ shoulder + (along * cosine + bend * std::sqrt(1.0f - cosine * cosine)) * upper_length };
		const auto hinge{ mathematics.normalize(mathematics.cross(along, bend)) * -hinge_sign };

		orient(upper_arm, mathematics.normalize(elbow - shoulder), hinge);
		orient(forearm, mathematics.normalize(shoulder + along * reach - elbow), hinge);
		orient(hand, mathematics.normalize(fingers_direction), mathematics.cross(mathematics.normalize(fingers_direction), palm));
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::orient(std::int32_t bone, structures::vec3_s x_axis, structures::vec3_s z_hint)
	{
		const auto z_axis{ mathematics.normalize(z_hint - x_axis * mathematics.dot(z_hint, x_axis)) };
		const auto parent{ arms.bones[bone].parent };
		const auto parent_rotation{ parent >= 0 ? mathematics.quat_from_basis(mathematics.normalize(globals[parent].row3(0u)), mathematics.normalize(globals[parent].row3(1u)), mathematics.normalize(globals[parent].row3(2u))) : mathematics.quat_identity() };

		pose.rotations[bone] = mathematics.quat_normalize(mathematics.quat_multiply(mathematics.quat_conjugate(parent_rotation), mathematics.quat_from_basis(x_axis, mathematics.cross(z_axis, x_axis), z_axis)));

		compute_globals();
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::curl(std::uint32_t item)
	{
		for (auto finger{ 0u }; finger < 5u; finger++)
		{
			for (auto joint{ 0u }; joint < 3u; joint++)
			{
				if (const auto bone{ fingers[finger][joint] }; bone >= 0)
				{
					pose.rotations[bone] = mathematics.quat_multiply(finger == 0u && joint == 0u && item < structures::item_count && fitted[item] ? mathematics.quat_multiply(arms.bones[bone].rotation, mathematics.quat_axis_angle(thumb_axis, thumb_swings[item])) : arms.bones[bone].rotation, mathematics.quat_axis_angle({ 0.0f, 0.0f, 1.0f }, item < structures::item_count && fitted[item] ? grips[item][finger][joint] : (finger ? viewmodel_curl[joint] : viewmodel_thumb[joint])));
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::compute_globals()
	{
		for (auto index{ 0u }; index < arms.bones.size(); index++)
		{
			const auto local{ mathematics.compose(pose.translations[index], pose.rotations[index], arms.bones[index].scale) };

			globals[index] = arms.bones[index].parent >= 0 ? mathematics.multiply(local, globals[arms.bones[index].parent]) : local;
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::support(structures::vec3_s view_target, structures::vec3_s fingers_view, structures::vec3_s palm_view, std::uint32_t gun)
	{
		const auto finger_axis{ mathematics.normalize(fingers_view) };
		const auto palm_axis{ mathematics.normalize(palm_view - finger_axis * mathematics.dot(palm_view, finger_axis)) };
		const auto seated{ gun < structures::weapon_count && support_fitted[gun] && charge_grab < 0.5f && magazine_hold < 0.5f };
		const auto held{ mathematics.multiply(mathematics.inverse(seated ? support_frames[gun] : grip_frames[0]), mathematics.basis(finger_axis, mathematics.cross(palm_axis, finger_axis), palm_axis, view_target)) };
		const auto held_fingers{ mathematics.normalize(held.row3(0u)) };
		const auto held_palm{ mathematics.normalize(held.row3(1u)) };
		const structures::vec3_s fingers_model{ -held_fingers.x, held_fingers.y, -held_fingers.z };
		const auto palm_model{ structures::vec3_s{ -held_palm.x, held_palm.y, -held_palm.z } * left_palm };

		characters.reach(arms, pose, left_upper, left_forearm, left_hand, to_model(held.row3(3u)), viewmodel_left_pole, 1.0f);
		characters.orient(arms, pose, left_hand, fingers_model, mathematics.cross(fingers_model, palm_model));

		for (auto finger{ 0u }; finger < 5u; finger++)
		{
			for (auto joint{ 0u }; joint < 3u; joint++)
			{
				if (const auto bone{ left_fingers[finger][joint] }; bone >= 0)
				{
					pose.rotations[bone] = mathematics.quat_multiply(arms.bones[bone].rotation, mathematics.quat_axis_angle({ 0.0f, 0.0f, 1.0f }, (seated ? support_grips[gun][finger][joint] : (finger ? support_curl[joint] : viewmodel_thumb[joint])) * left_palm));
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s viewmodel_c::to_model(structures::vec3_s view)
	{
		return { eye.x - view.x + viewmodel_offset.x, eye.y + view.y - viewmodel_offset.y, eye.z - view.z + viewmodel_offset.z };
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::submit()
	{
		if (visible)
		{
			if (inspect_blend < 0.2f)
			{
				renderer.submit_skinned(&arms, world, world, palette.data(), previous_palette.data(), structures::draw_flag_viewmodel | structures::draw_flag_no_shadow, 0.0f);
			}

			if (two_handed && inspect_blend < 0.2f)
			{
				renderer.submit_skinned(&arms_left, world, world, palette.data(), previous_palette.data(), structures::draw_flag_viewmodel | structures::draw_flag_no_shadow, 0.0f);
			}

			if (stowed == false)
			{
				submit_item();
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void viewmodel_c::submit_item()
	{
		renderer.submit(&tools[shown_item], tool_world, previous_tool_world, -1.0f, structures::draw_flag_viewmodel);

		if (const auto gun{ item_definitions[shown_item].weapon }; bolts[gun].index_count > 0u)
		{
			renderer.submit(&bolts[gun], bolt_world, previous_bolt_world, -1.0f, structures::draw_flag_viewmodel);
		}

		if (const auto gun{ item_definitions[shown_item].weapon }; magazines[gun].index_count > 0u)
		{
			renderer.submit(&magazines[gun], magazine_world, previous_magazine_world, -1.0f, structures::draw_flag_viewmodel);
		}

		if (const auto gun{ item_definitions[shown_item].weapon }; gun != structures::weapon_none && gun_models[gun].action == structures::action_draw)
		{
			const auto& model{ gun_models[gun] };

			for (const auto tip : { model.bolt_pivot, structures::vec3_s{ model.bolt_pivot.x, -model.bolt_pivot.y, model.bolt_pivot.z } })
			{
				const auto start{ mathematics.transform_point(tip, gun_placement) };
				const auto span{ nock - start };
				const auto side{ mathematics.normalize(mathematics.cross(span, mathematics.transform_vector({ 0.0f, 0.0f, 1.0f }, gun_placement))) };
				const auto segment{ mathematics.basis(side, span, mathematics.normalize(mathematics.cross(side, span)), start) };

				renderer.submit(&string_mesh, segment, segment, -1.0f, structures::draw_flag_viewmodel);
			}

			if (survival.held().loaded > 0u && arrow_mesh.index_count > 0u)
			{
				const auto rest{ mathematics.transform_point(model.muzzle, gun_placement) };
				const auto heading{ mathematics.normalize(rest - nock) };
				const auto up{ mathematics.normalize(mathematics.transform_vector({ 0.0f, 1.0f, 0.0f }, gun_placement) - heading * mathematics.dot(mathematics.transform_vector({ 0.0f, 1.0f, 0.0f }, gun_placement), heading)) };
				const auto shaft{ mathematics.basis(heading, up, mathematics.cross(heading, up), nock + heading * arrow_length) };

				renderer.submit(&arrow_mesh, shaft, shaft, -1.0f, structures::draw_flag_viewmodel);
			}
		}

		if (inspect_blend > 0.01f)
		{
			renderer.add_light(renderer.camera.position + renderer.camera.right * -0.45f + renderer.camera.up * 0.35f + renderer.camera.forward * 0.05f, inspect_light_radius, inspect_light_color * inspect_blend);
		}

		if (shown_item == structures::item_torch)
		{
			const auto head{ mathematics.transform_point({ 0.0f, 0.38f, 0.0f }, tool_world) };
			const auto flicker{ 0.86f + 0.14f * std::sin(clock * 23.0f) * std::sin(clock * 7.3f + 1.3f) };

			renderer.add_light(renderer.camera.position + renderer.camera.right * head.x + renderer.camera.up * head.y + renderer.camera.forward * head.z, 11.0f, structures::vec3_s{ 3.4f, 1.8f, 0.65f } * flicker);
		}
	}
}

//=====================================================================================
