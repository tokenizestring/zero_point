
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class survival_c;

	class fauna_c
	{
	public:

		std::vector<structures::animal_s> animals;
		std::vector<structures::herd_s> herds;
		std::vector<structures::watcher_s> watchers;
		std::vector<structures::vec3_s> bites;
		std::vector<std::pair<std::float_t, std::uint32_t>> nearby;
		const structures::character_s* bodies[structures::species_count]{};
		const structures::character_s* distant[structures::species_count]{};
		std::uint32_t clips[structures::species_count][structures::animal_clip_count]{};
		structures::pose_s current{};
		structures::pose_s previous{};
		structures::pose_s scratch{};
		std::double_t clock = 0.0;
		std::float_t struck = 0.0f;
		std::uint32_t seed = 0x51F15EEDu;
		std::uint16_t next_id = 1u;
		bool ready = false;

		void create();
		void clear();
		void populate();
		void spawn_herd(std::uint32_t kind, structures::vec3_s home);
		bool relocate(std::uint32_t index, structures::vec3_s near_point, std::float_t yaw);
		void place(std::uint32_t index, std::uint32_t species, std::uint32_t herd, structures::vec3_s home, bool leader);
		bool habitat(std::uint32_t kind, structures::vec3_s& home, bool far_from_watchers);
		void simulate(std::float_t delta);
		void live(structures::animal_s& animal, std::float_t delta);
		bool watched(structures::vec3_s position);
		void think(structures::animal_s& animal);
		void steer(structures::animal_s& animal, std::float_t delta);
		bool walkable(structures::vec3_s point);
		void alarm(structures::vec3_s origin, std::float_t loudness);
		std::int32_t ray(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance);
		bool damage(std::uint32_t index, std::float_t amount, structures::vec3_s origin);
		void die(structures::animal_s& animal);
		bool carve(survival_c& owner, std::uint32_t index);
		std::uint32_t melee(survival_c& owner, structures::vec3_s eye, structures::vec3_s forward, std::float_t reach, std::float_t strength, structures::vec3_s& point);
		std::int32_t carcass(structures::vec3_s eye, structures::vec3_s forward);
		std::float_t noise(const structures::movement_state_s& state);
		void write(stream_writer_c& writer, structures::vec3_s viewer);
		void read(stream_reader_c& reader, std::double_t time);
		std::int32_t find(std::uint16_t id);
		void update(std::float_t delta, std::double_t render_time, bool mirrored);
		void animate(structures::animal_s& animal, std::float_t delta);
		void sample(structures::animal_s& animal, const structures::character_s& character, std::uint32_t mode, std::float_t time, structures::pose_s& pose);
		void submit();
		std::float_t random();
	};

	extern fauna_c fauna;
}

//=====================================================================================
