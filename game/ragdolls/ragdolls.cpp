
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	ragdolls_c ragdolls;

	void ragdolls_c::start(structures::actor_s& actor, structures::vec3_s push)
	{
		const auto& character{ *actor.character };

		auto& doll{ actor.ragdoll };

		doll.active = false;

		for (auto point{ 0u }; point < structures::ragdoll_point_count; point++)
		{
			doll.bones[point] = characters.bone(character, ragdoll_bones[point]);
		}

		if (std::all_of(std::begin(doll.bones), std::end(doll.bones), [](std::int32_t bone) { return bone >= 0; }))
		{
			const auto speed{ mathematics.length(actor.velocity) };
			const auto moving{ speed > ragdoll_top_speed ? actor.velocity * (ragdoll_top_speed / speed) : actor.velocity };

			for (auto point{ 0u }; point < structures::ragdoll_point_count; point++)
			{
				const auto& joint{ characters.globals[doll.bones[point]] };
				const auto local{ point == structures::ragdoll_head ? joint.row3(3u) + mathematics.normalize(joint.row3(0u)) * ragdoll_head_reach : joint.row3(3u) };

				doll.points[point] = mathematics.transform_point(local, actor.world);
				doll.previous[point] = doll.points[point] - (moving + push * ragdoll_push[point]) * ragdoll_step;
			}

			for (auto link{ 0u }; link < std::size(ragdoll_links); link++)
			{
				doll.lengths[link] = mathematics.distance(doll.points[ragdoll_links[link].from], doll.points[ragdoll_links[link].to]);
			}

			for (auto joint{ 0u }; joint < std::size(ragdoll_joints); joint++)
			{
				const auto& limb{ ragdoll_joints[joint] };

				doll.spans[joint] = (mathematics.distance(doll.points[limb.root], doll.points[limb.middle]) + mathematics.distance(doll.points[limb.middle], doll.points[limb.end])) * limb.fold;
			}

			doll.frame = actor.world;
			doll.carry = 0.0f;
			doll.clock = 0.0f;
			doll.calm = 0.0f;
			doll.asleep = false;
			doll.active = true;
		}
	}
	/*
	//=====================================================================================
	*/
	void ragdolls_c::step(structures::actor_s& actor, std::float_t delta)
	{
		auto& doll{ actor.ragdoll };

		doll.clock += delta;
		doll.carry = std::min(doll.carry + delta, ragdoll_step * static_cast<std::float_t>(ragdoll_substeps));

		if (doll.asleep == false)
		{
			auto fastest{ 0.0f };

			while (doll.carry >= ragdoll_step)
			{
				for (auto point{ 0u }; point < structures::ragdoll_point_count; point++)
				{
					const auto velocity{ (doll.points[point] - doll.previous[point]) * ragdoll_damping };

					starts[point] = doll.points[point];
					doll.previous[point] = doll.points[point];
					doll.points[point] += velocity + structures::vec3_s{ 0.0f, -ragdoll_gravity * ragdoll_step * ragdoll_step, 0.0f };
				}

				for (auto iteration{ 0u }; iteration < ragdoll_iterations; iteration++)
				{
					solve(doll);
				}

				const auto forward{ torso(doll.points).row3(2u) };

				for (auto joint{ 0u }; joint < std::size(ragdoll_joints); joint++)
				{
					bend(doll, ragdoll_joints[joint], joint, forward);
				}

				collide(doll);

				doll.carry -= ragdoll_step;
			}

			for (auto point{ 0u }; point < structures::ragdoll_point_count; point++)
			{
				fastest = std::max(fastest, mathematics.distance(doll.points[point], doll.previous[point]) / ragdoll_step);
			}

			doll.calm = fastest < ragdoll_rest_speed ? doll.calm + delta : 0.0f;
			doll.asleep = doll.calm > ragdoll_rest_time || doll.clock > ragdoll_lifetime;
		}
	}
	/*
	//=====================================================================================
	*/
	void ragdolls_c::solve(structures::ragdoll_s& doll)
	{
		for (auto link{ 0u }; link < std::size(ragdoll_links); link++)
		{
			const auto from{ ragdoll_links[link].from };
			const auto to{ ragdoll_links[link].to };
			const auto offset{ doll.points[to] - doll.points[from] };
			const auto length{ mathematics.length(offset) };

			if (length > 0.0001f)
			{
				const auto correction{ offset * ((length - doll.lengths[link]) / (length * (ragdoll_weights[from] + ragdoll_weights[to]))) };

				doll.points[from] += correction * ragdoll_weights[from];
				doll.points[to] -= correction * ragdoll_weights[to];
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void ragdolls_c::bend(structures::ragdoll_s& doll, const structures::ragdoll_joint_s& joint, std::uint32_t index, structures::vec3_s forward)
	{
		const auto reach{ doll.points[joint.end] - doll.points[joint.root] };
		const auto span{ mathematics.length(reach) };

		if (span > 0.0001f && span < doll.spans[index])
		{
			doll.points[joint.end] += reach * ((doll.spans[index] - span) / span);
		}

		const auto axis{ mathematics.normalize(doll.points[joint.end] - doll.points[joint.root]) };
		const auto side{ forward * joint.facing };
		const auto facing{ mathematics.normalize(side - axis * mathematics.dot(side, axis)) };
		const auto relative{ doll.points[joint.middle] - doll.points[joint.root] };
		const auto wrong{ mathematics.dot(relative - axis * mathematics.dot(relative, axis), facing) };

		if (wrong < 0.0f)
		{
			const auto fix{ facing * (-2.0f * wrong) };

			doll.points[joint.middle] += fix;
			doll.previous[joint.middle] += fix;
		}
	}
	/*
	//=====================================================================================
	*/
	void ragdolls_c::collide(structures::ragdoll_s& doll)
	{
		for (auto point{ 0u }; point < structures::ragdoll_point_count; point++)
		{
			if (const auto hit{ world.trace(starts[point], doll.points[point], { ragdoll_radius, ragdoll_radius, ragdoll_radius }, structures::contents_solid) }; hit.hit && hit.start_solid == false)
			{
				const auto motion{ hit.end - doll.previous[point] };
				const auto along{ motion - hit.normal * mathematics.dot(motion, hit.normal) };

				doll.points[point] = hit.end + hit.normal * 0.002f;
				doll.previous[point] = doll.points[point] - along * (1.0f - ragdoll_friction);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s ragdolls_c::torso(const structures::vec3_s* points)
	{
		const auto up{ mathematics.normalize(points[structures::ragdoll_chest] - points[structures::ragdoll_pelvis]) };
		const auto across{ points[structures::ragdoll_right_shoulder] + points[structures::ragdoll_right_hip] - points[structures::ragdoll_left_shoulder] - points[structures::ragdoll_left_hip] };
		const auto right{ mathematics.normalize(across - up * mathematics.dot(across, up)) };

		return mathematics.basis(right, up, mathematics.cross(right, up), {});
	}
	/*
	//=====================================================================================
	*/
	void ragdolls_c::pose(structures::actor_s& actor)
	{
		const auto& character{ *actor.character };
		const auto& doll{ actor.ragdoll };
		const auto inverse{ mathematics.inverse(doll.frame) };

		idle = idle < characters.clips.size() ? idle : characters.clip(clip_idle);

		characters.sample(character, idle, 0.0f, base);

		characters.compute_globals(character, base);

		for (auto point{ 0u }; point < structures::ragdoll_point_count; point++)
		{
			starts[point] = characters.globals[doll.bones[point]].row3(3u);
			locals[point] = mathematics.transform_point(doll.points[point], inverse);
		}

		const auto turn{ mathematics.multiply(mathematics.transpose(torso(starts)), torso(locals)) };
		const auto shift{ mathematics.multiply(mathematics.multiply(mathematics.translation(starts[structures::ragdoll_pelvis] * -1.0f), turn), mathematics.translation(locals[structures::ragdoll_pelvis])) };

		for (auto index{ 0u }; index < character.bones.size(); index++)
		{
			const auto& bone{ character.bones[index] };
			const auto local{ mathematics.compose(base.translations[index], base.rotations[index], bone.scale) };

			auto global{ bone.parent >= 0 ? mathematics.multiply(local, characters.globals[bone.parent]) : local };

			if (static_cast<std::int32_t>(index) == doll.bones[structures::ragdoll_pelvis])
			{
				global = mathematics.multiply(global, shift);
			}

			for (auto point{ 0u }; point < structures::ragdoll_point_count; point++)
			{
				if (doll.bones[point] == static_cast<std::int32_t>(index) && ragdoll_aims[point] < structures::ragdoll_point_count)
				{
					const auto origin{ global.row3(3u) };
					const auto aim{ mathematics.normalize(locals[ragdoll_aims[point]] - origin) };
					const auto hint{ global.row3(2u) };
					const auto side{ mathematics.normalize(hint - aim * mathematics.dot(hint, aim)) };

					global = mathematics.basis(aim * mathematics.length(global.row3(0u)), mathematics.cross(side, aim) * mathematics.length(global.row3(1u)), side * mathematics.length(hint), origin);
				}
			}

			characters.globals[index] = global;
			actor.palette[index] = mathematics.multiply(bone.inverse_bind, global);
		}
	}
}

//=====================================================================================
