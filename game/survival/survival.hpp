
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class survival_c
	{
	public:

		structures::vitals_s vitals{};
		structures::climate_s climate{ climate_mean, 0.0f, 0.0f, 0.0f, climate_mean, 0.0f, false, false };
		structures::item_stack_s slots[total_slots]{};
		structures::craft_job_s queue[crafting_queue_size]{};
		structures::notification_s notifications[notification_count]{};
		std::uint32_t queue_count = 0u;
		std::uint32_t active_slot = 0u;
		std::int32_t open_container = -1;
		structures::item_stack_s scratch{};
		bool known[recipe_capacity]{};
		structures::vec3_s position{};
		std::uint32_t seed = 0x2545F491u;
		std::int32_t owner = -1;
		std::uint8_t harm = structures::death_starved;
		bool inventory_open = false;
		bool underwater = false;
		bool remote = false;

		void reset();
		void reset_knowledge();
		void give_kit();
		bool learn(std::uint32_t recipe);
		bool learn_random(std::uint32_t highest_tier);
		bool research(std::uint32_t recipe);
		std::uint32_t station();
		void update(std::float_t delta, std::float_t exertion);
		void acclimate(std::float_t delta);
		std::float_t ambient(std::float_t hours, std::float_t cloud, std::float_t rain, std::float_t storm);
		std::uint32_t give(std::uint32_t item, std::uint32_t amount, bool announce);
		std::uint32_t place(std::uint32_t item, std::uint32_t amount, std::uint32_t first, std::uint32_t last);
		std::uint32_t receive(const structures::item_stack_s& stack);
		std::uint32_t count(std::uint32_t item);
		bool take(std::uint32_t item, std::uint32_t amount);
		bool can_craft(std::uint32_t recipe);
		bool craft(std::uint32_t recipe);
		bool consume(std::uint32_t slot);
		void damage(std::float_t amount);
		void notify(const char* text, std::int32_t amount);
		void post(const char* text, std::int32_t amount);
		void cue(std::uint32_t sound, std::float_t volume, std::float_t pitch);
		std::uint64_t fingerprint();
		void swap(std::uint32_t from, std::uint32_t to);
		void transfer(std::uint32_t from);
		structures::item_stack_s& slot(std::uint32_t address);
		bool valid(std::uint32_t address);
		const structures::item_stack_s& held();
	};

	extern survival_c survival;
}

//=====================================================================================
