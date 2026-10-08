
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class ragdolls_c
	{
	public:

		structures::pose_s base{};
		structures::vec3_s starts[structures::ragdoll_point_count]{};
		structures::vec3_s locals[structures::ragdoll_point_count]{};
		std::uint32_t idle = UINT32_MAX;

		void start(structures::actor_s& actor, structures::vec3_s push);
		void step(structures::actor_s& actor, std::float_t delta);
		void solve(structures::ragdoll_s& doll);
		void bend(structures::ragdoll_s& doll, const structures::ragdoll_joint_s& joint, std::uint32_t index, structures::vec3_s forward);
		void collide(structures::ragdoll_s& doll);
		structures::mat4_s torso(const structures::vec3_s* points);
		void pose(structures::actor_s& actor);
	};

	extern ragdolls_c ragdolls;
}

//=====================================================================================
