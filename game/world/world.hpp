
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class world_c
	{
	public:

		std::vector<structures::plane_s> planes;
		std::vector<structures::brush_s> brushes;
		std::vector<std::vector<std::uint32_t>> cells;
		std::vector<structures::mover_s> movers;
		structures::vec3_s grid_min{};
		std::int32_t grid_x = 0;
		std::int32_t grid_y = 0;
		std::int32_t grid_z = 0;
		std::float_t kill_height = -30.0f;
		std::uint32_t ignored = UINT32_MAX;
		bool carrying = false;

		void clear();
		void set_mover(std::uint32_t index, const structures::mat4_s& placement, structures::vec3_s center, structures::vec3_s half, std::uint32_t surface, std::uint32_t owner);
		std::uint32_t add_brush(const structures::plane_s* brush_planes, std::uint32_t count, std::uint32_t surface, std::uint32_t contents);
		void add_box(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation, std::uint32_t surface, std::uint32_t contents);
		void add_ramp(structures::vec3_s center, structures::vec3_s size, std::float_t yaw, std::uint32_t surface, std::uint32_t contents);
		void build();
		void insert(std::uint32_t index);
		void gather(structures::vec3_s minimum, structures::vec3_s maximum, std::vector<std::uint32_t>& out);
		structures::trace_s trace(structures::vec3_s start, structures::vec3_s end, structures::vec3_s extents, std::uint32_t mask);
		structures::trace_s sweep(structures::vec3_s start, structures::vec3_s end, structures::vec3_s extents, std::uint32_t mask);
		void clip_planes(const structures::plane_s* brush_planes, std::uint32_t plane_count, std::int32_t index, std::uint32_t surface, structures::vec3_s start, structures::vec3_s end, structures::vec3_s extents, structures::trace_s& result);
		bool box_solid(structures::vec3_s center, structures::vec3_s extents, std::uint32_t mask);
	};

	extern world_c world;
}

//=====================================================================================
