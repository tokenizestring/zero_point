
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class actors_c
	{
	public:

		std::vector<structures::actor_s> list;
		structures::vec3_s focus{};
		bool passive = false;
		structures::pose_s locomotion{};
		structures::pose_s secondary{};
		structures::pose_s reference{};
		structures::pose_s crouching{};
		structures::pose_s airborne{};
		std::uint32_t clips[5]{ UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX };
		std::float_t speeds[4]{};
		const structures::character_s* clothed = nullptr;
		const structures::character_s* bare = nullptr;
		bool censored = false;

		bool create();
		void clear();
		const char* survivor() const;
		void dress(bool censor);
		structures::actor_s* spawn(const char* character_name, structures::vec3_s position, std::float_t yaw, std::uint32_t behavior);
		void mask(structures::actor_s& actor);
		void update(std::float_t delta);
		void think(structures::actor_s& actor, std::float_t delta);
		void hunt(structures::actor_s& actor, std::float_t delta);
		void strike(structures::actor_s& actor, std::float_t distance, std::float_t delta);
		bool sees_player(const structures::actor_s& actor);
		void damage(structures::actor_s& actor, std::float_t amount, structures::vec3_s direction);
		bool recycle(structures::actor_s& actor, structures::vec3_s origin, std::float_t minimum_distance, std::float_t maximum_distance);
		void animate(structures::actor_s& actor, std::float_t delta);
		void pose_arms(structures::actor_s& actor);
		bool hold(structures::actor_s& actor);
		void steer(structures::actor_s& actor, std::float_t delta);
		void submit();
		std::float_t random(structures::actor_s& actor);
	};

	extern actors_c actors;
}

//=====================================================================================
