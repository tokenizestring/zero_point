
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class tracer_c
	{
	public:

		std::vector<structures::ray_triangle_s> triangles;
		std::vector<structures::bvh_node_s> nodes;
		std::vector<structures::vec3_s> centroids;
		std::vector<structures::vec3_s> triangle_min;
		std::vector<structures::vec3_s> triangle_max;

		void build(const std::vector<structures::vertex_s>& vertices, const std::vector<std::uint32_t>& indices);
		void split(std::uint32_t node_index, std::vector<std::uint32_t>& pending);
		void swap_triangles(std::uint32_t a, std::uint32_t b);
		bool intersect(structures::vec3_s origin, structures::vec3_s direction, std::float_t maximum_distance, structures::ray_hit_s& hit);
		bool occluded(structures::vec3_s origin, structures::vec3_s direction, std::float_t maximum_distance);
		std::float_t box_entry(const structures::bvh_node_s& node, structures::vec3_s origin, structures::vec3_s inverse, std::float_t limit);
		std::float_t area(structures::vec3_s minimum, structures::vec3_s maximum);
	};

	extern tracer_c tracer;
}

//=====================================================================================
