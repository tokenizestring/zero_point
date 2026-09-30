
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class maps_c
	{
	public:

		structures::map_info_s info{};
		std::vector<structures::spawn_point_s> spawns;
		std::vector<structures::depot_s> depots;
		std::vector<structures::objective_s> objectives;
		std::vector<structures::light_s> lights;
		std::vector<structures::vec4_s> clearings;
		std::vector<structures::vec4_s> hotspots;
		std::vector<structures::landmark_s> landmarks;
		std::vector<structures::road_s> roads;
		std::vector<structures::footprint_s> footprints;
		std::unordered_map<std::string, std::uint32_t> building_species;
		std::vector<structures::route_path_s> paths;
		std::vector<std::uint8_t> corridor;
		std::uint32_t track_materials[structures::track_material_count]{};
		std::uint32_t crates[structures::node_kind_count]{};
		std::uint32_t barrels[3]{};
		std::uint32_t layout_seed = 0x1B873593u;
		structures::vec3_s radio{};
		bool radio_ready = false;

		void clear();
		bool load(const char* name);
		void finish();
		void build_test_scene();
		void build_island();
		void plant_island();
		void build_monuments();
		void build_town(structures::vec3_s center, std::float_t radius);
		void build_house(structures::vec3_s origin, std::float_t yaw, std::float_t width, std::float_t depth, std::uint32_t floors, std::float_t damage);
		void build_wall(structures::vec3_s start, std::float_t yaw, std::float_t length, std::float_t base, std::float_t height, const structures::vec4_s* holes, std::uint32_t hole_count, std::float_t damage, std::uint32_t material);
		void wall_piece(structures::vec3_s start, std::float_t yaw, std::float_t from, std::float_t to, std::float_t bottom, std::float_t top, std::uint32_t material);
		void build_outpost(structures::vec3_s center);
		void build_yard(structures::vec3_s center);
		void road(structures::vec3_s from, structures::vec3_s to, std::float_t width);
		void container_node(std::uint32_t kind, structures::vec3_s position, std::float_t yaw);
		void barrel_node(structures::vec3_s position);
		void ground_prop(const char* model_name, structures::vec3_s position, std::float_t yaw, std::float_t scale, std::uint32_t surface);
		bool place_building(const char* model_name, structures::vec3_s position, std::float_t yaw);
		void load_routes();
		void build_routes();
		void build_road(const structures::route_path_s& path);
		void build_rail(const structures::route_path_s& path);
		bool on_route(std::float_t x, std::float_t z);
		std::float_t route_gap(std::float_t x, std::float_t z);
		void build_hamlet(const structures::world_site_s& site);
		void raise(const char* model_name, structures::vec3_s position, std::float_t yaw, std::float_t width, std::float_t depth, std::uint32_t floors, std::float_t damage);
		std::uint32_t surface_named(const char* text);
		std::uint32_t loot_named(const char* text);
		bool cleared(std::float_t x, std::float_t z);
		std::float_t chance();
		void build_deck_zero();
		void build_hangar(std::float_t side);
		void build_corridor(std::float_t side);
		void build_tower();
		void build_flight_deck();
		void build_surroundings();

		void solid(structures::vec3_s center, structures::vec3_s size, std::uint32_t material, std::uint32_t surface);
		void solid_yaw(structures::vec3_s center, structures::vec3_s size, std::float_t yaw, std::uint32_t material, std::uint32_t surface);
		void detail(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation, std::uint32_t material);
		void clip(structures::vec3_s center, structures::vec3_s size);
		void slab(structures::vec3_s minimum, structures::vec3_s maximum, std::uint32_t material, std::uint32_t surface);
		void wall(structures::vec3_s minimum, structures::vec3_s maximum, std::uint32_t material);
		void stairs(structures::vec3_s bottom, std::float_t width, std::float_t rise, std::float_t run, std::float_t yaw, std::uint32_t material);
		void railing(structures::vec3_s from, structures::vec3_s to, std::uint32_t material);
		void column(structures::vec3_s base, std::float_t height, std::uint32_t material);
		void beam(structures::vec3_s from, structures::vec3_s to, std::float_t depth, std::uint32_t material);
		void grating(structures::vec3_s minimum, structures::vec3_s maximum);
		void container(structures::vec3_s base, std::float_t yaw, std::uint32_t material, bool long_container);
		void lamp(structures::vec3_s position, structures::vec3_s size, std::uint32_t material, structures::vec3_s color, std::float_t radius);
		void terminal(structures::vec3_s base, std::float_t yaw);
		void deck_line(structures::vec3_s from, structures::vec3_s to, std::float_t width, std::uint32_t material);
		void prop(const char* model_name, structures::vec3_s position, std::float_t yaw, std::float_t scale, std::uint32_t collision, std::uint32_t surface);
		void prop_rotated(const char* model_name, structures::vec3_s position, structures::quat_s rotation, std::float_t scale, std::uint32_t collision, std::uint32_t surface);
		void prop_part(const char* model_name, const char* part_name, structures::vec3_s position, structures::quat_s rotation, std::float_t scale, std::uint32_t collision, std::uint32_t surface);
		void place_collision(structures::vec3_s local_min, structures::vec3_s local_max, const structures::mat4_s& placement, structures::quat_s rotation, std::float_t scale, std::uint32_t collision, std::uint32_t surface);
		void spawn(structures::vec3_s position, std::float_t yaw, std::uint32_t team);
		void objective(structures::vec3_s position, std::float_t radius, std::uint32_t kind, std::uint32_t team, const char* name);
		structures::vec3_s rotate_yaw(structures::vec3_s offset, std::float_t yaw);
	};

	extern maps_c maps;
}

//=====================================================================================
