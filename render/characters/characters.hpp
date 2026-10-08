
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class characters_c
	{
	public:

		std::vector<structures::character_s> list;
		std::vector<structures::clip_s> clips;
		std::vector<structures::mat4_s> globals;

		bool load();
		bool upload();
		void destroy();
		const structures::character_s* find(const char* name);
		std::uint32_t clip(const char* name);
		std::int32_t bone(const structures::character_s& character, const char* name);
		void rest(const structures::character_s& character, structures::pose_s& pose);
		void sample(const structures::character_s& character, std::uint32_t clip_index, std::float_t time, structures::pose_s& pose);
		void blend(const structures::character_s& character, const structures::pose_s& from, const structures::pose_s& to, std::float_t weight, structures::pose_s& out);
		void add(const structures::character_s& character, const structures::pose_s& base, const structures::pose_s& reference, const structures::pose_s& target, std::float_t weight, structures::pose_s& out);
		void palette(const structures::character_s& character, const structures::pose_s& pose, std::float_t twist_yaw, std::float_t twist_pitch, structures::mat4_s* out, std::float_t blade = 0.0f, std::float_t sit = 0.0f, std::float_t straddle = 0.0f);
		void compute_globals(const structures::character_s& character, const structures::pose_s& pose);
		structures::mat4_s rest_global(const structures::character_s& character, std::int32_t bone);
		void reach(const structures::character_s& character, structures::pose_s& pose, std::int32_t upper, std::int32_t lower, std::int32_t end, structures::vec3_s target, structures::vec3_s pole, std::float_t weight);
		void orient(const structures::character_s& character, structures::pose_s& pose, std::int32_t bone, structures::vec3_s x_axis, structures::vec3_s z_hint);
	};

	extern characters_c characters;
}

//=====================================================================================
