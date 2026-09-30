
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class building_c
	{
	public:

		std::vector<structures::structure_s> placed;
		std::vector<structures::container_s> containers;
		std::vector<std::uint32_t> dirty;
		std::vector<std::uint32_t> stirred;
		std::unordered_map<std::uint32_t, std::vector<std::uint32_t>> authorized;
		std::unordered_map<std::uint32_t, structures::lock_s> locks;
		structures::mesh_s keypad_mesh{};
		std::float_t tier_materials[building_tier_count]{ -1.0f, -1.0f, -1.0f, -1.0f };
		std::unordered_map<std::int32_t, std::uint32_t> by_brush;
		structures::mesh_s meshes[structures::piece_count]{};
		structures::mesh_s tier_meshes[building_tier_count][structures::piece_door]{};
		builder_c piece_builder;
		structures::placement_s preview{};
		std::uint32_t selected = structures::piece_foundation;
		std::uint32_t ghost_valid = 0u;
		std::uint32_t ghost_invalid = 0u;
		std::uint32_t wood = 0u;
		std::uint32_t bark = 0u;
		std::uint32_t seed = 0x7F4A7C15u;
		std::int32_t bag = -1;
		std::float_t turn = 0.0f;
		std::float_t clock = 0.0f;
		bool ready = false;

		bool create();
		void destroy();
		void clear();
		void build_meshes();
		void build_benches(std::uint32_t dark);
		void build_roof(std::uint32_t dark);
		void build_twigs();
		void stick(structures::vec3_s from, structures::vec3_s to, std::float_t radius);
		void lattice(std::float_t left, std::float_t right, std::float_t bottom, std::float_t top, std::float_t spacing);
		void load_kit();
		void migrate(structures::structure_s& structure);
		std::uint32_t workbench_tier(structures::vec3_s position);
		std::float_t warmth(structures::vec3_s position);
		bool research_nearby(structures::vec3_s position);
		void panel(std::uint32_t material, structures::vec3_s minimum, structures::vec3_s maximum);
		void update(std::float_t delta, bool input_enabled);
		std::uint32_t active_piece();
		void plan(std::uint32_t piece);
		bool snap_foundation(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out);
		bool snap_edge(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out);
		bool snap_cell(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out);
		bool snap_door(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out);
		bool snap_ground(structures::vec3_s origin, structures::vec3_s forward, structures::placement_s& out);
		bool occupied(structures::vec3_s position, std::uint32_t piece);
		bool affordable(std::uint32_t piece);
		bool place(const structures::placement_s& placement);
		bool permitted(const structures::placement_s& placement, structures::vec3_s eye);
		bool place(const structures::placement_s& placement, survival_c& payer, std::uint32_t slot, std::uint32_t owner);
		void attach(const structures::structure_s& structure);
		void refresh(std::uint32_t index, bool open, bool destroyed);
		void add_collision(std::uint32_t index);
		bool privileged(structures::vec3_s position, std::uint32_t identity);
		bool accessible(std::uint32_t index, std::uint32_t identity);
		bool attach_lock(std::uint32_t door, std::uint32_t identity);
		std::int32_t enter_code(std::uint32_t door, std::uint32_t identity, std::uint32_t code);
		void authorize(std::uint32_t index, std::uint32_t identity);
		std::int32_t cupboard_target(structures::vec3_s origin, structures::vec3_s forward);
		void box(std::uint32_t index, structures::vec3_s center, structures::vec3_s size, std::uint32_t surface);
		void ramp(std::uint32_t index, structures::vec3_s center, structures::vec3_s size, std::float_t spin, std::uint32_t surface);
		void toggle_door(std::uint32_t index);
		std::int32_t door_target(structures::vec3_s origin, structures::vec3_s forward);
		std::int32_t container_target(structures::vec3_s origin, structures::vec3_s forward);
		void smelt(std::float_t delta);
		bool deposit(structures::container_s& container, std::uint32_t item);
		bool damage(std::int32_t brush, std::float_t amount, bool bullet);
		bool upgrade(std::uint32_t index);
		void retier(std::uint32_t index, std::uint32_t tier);
		void decay(std::float_t elapsed);
		bool repair(std::uint32_t index, std::float_t amount);
		std::float_t durability(std::uint32_t index);
		std::int32_t structure_target(structures::vec3_s origin, structures::vec3_s forward, std::float_t reach);
		structures::mat4_s matrix(const structures::structure_s& piece);
		void effects(std::float_t delta);
		void submit();
		void test_base(structures::vec3_s origin, std::float_t yaw);
		std::float_t random();
	};

	extern building_c building;
}

//=====================================================================================
