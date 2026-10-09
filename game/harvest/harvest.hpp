
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class harvest_c
	{
	public:

		std::vector<structures::resource_node_s> nodes;
		std::vector<std::uint32_t> changed;
		std::vector<std::uint32_t> waiting;
		std::vector<structures::felled_s> felled;
		std::unordered_map<std::int32_t, std::uint32_t> by_brush;
		structures::tool_state_s tool{};
		structures::vec3_s struck_point{};
		std::uint32_t struck_sound = structures::sound_count;
		std::float_t swing_timer = 0.0f;
		std::float_t swing_length = 1.0f;
		std::uint32_t seed = 0x51ED270Bu;
		bool swinging = false;

		void clear();
		void create_models();
		void create_hemp(const char* name, std::float_t keep);
		void create_berry_bush(const char* name, std::uint32_t branches, std::float_t keep);
		std::uint32_t add(std::uint32_t kind, structures::vec3_s position, std::float_t radius, std::uint32_t instance, std::int32_t brush);
		void update(std::float_t delta, bool input_enabled);
		void tick(const structures::usercmd_s& command, bool usable);
		void step(structures::tool_state_s& state, survival_c& owner, const structures::usercmd_s& command, bool usable);
		void respawn(std::float_t delta);
		std::int32_t strike(survival_c& owner, std::uint32_t slot, structures::vec3_s eye, structures::vec3_s forward, bool authoritative);
		std::int32_t interact(survival_c& owner, structures::vec3_s eye, structures::vec3_s forward, bool authoritative);
		std::int32_t pickup_target(structures::vec3_s eye, structures::vec3_s forward);
		bool lootable(std::uint32_t kind);
		bool plucked(std::uint32_t kind);
		void deplete(std::uint32_t index);
		void topple(std::uint32_t index);
		void fell(std::float_t delta);
		void submit();
		void restore(std::uint32_t index);
		void roll(survival_c& owner, const structures::loot_table_s& table);
		std::float_t random();
	};

	extern harvest_c harvest;
}

//=====================================================================================
