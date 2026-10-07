
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class builder_c
	{
	public:

		std::vector<structures::vertex_s> vertices;
		std::vector<std::uint32_t> indices;
		std::uint32_t material = 0u;
		bool world_uv = true;
		structures::vec2_s uv_offset{};

		void clear();
		std::uint64_t strip();
		void set_material(std::uint32_t id);
		std::uint32_t add_vertex(structures::vec3_s position, structures::vec3_s normal, structures::vec2_s uv);
		void add_triangle(std::uint32_t a, std::uint32_t b, std::uint32_t c);
		structures::vec2_s project_uv(structures::vec3_s position, structures::vec3_s normal);
		void quad(structures::vec3_s p0, structures::vec3_s p1, structures::vec3_s p2, structures::vec3_s p3, structures::vec3_s normal);
		void box(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation);
		void box_faces(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation, std::uint32_t face_mask);
		void cylinder(structures::vec3_s base, structures::vec3_s axis, std::float_t radius, std::float_t length, std::uint32_t segments, bool caps);
		void cone(structures::vec3_s base, structures::vec3_s axis, std::float_t radius_base, std::float_t radius_top, std::float_t length, std::uint32_t segments, bool caps);
		void sphere(structures::vec3_s center, std::float_t radius, std::uint32_t segments, std::uint32_t rings);
		void ramp(structures::vec3_s center, structures::vec3_s size, std::float_t yaw);
		void prism(const structures::vec2_s* outline, std::uint32_t count, std::float_t length, const structures::mat4_s& placement);
		void append(const structures::model_s& model, std::uint32_t first_index, std::uint32_t index_count, const structures::mat4_s& placement);
		void compute_tangents(std::uint32_t first_vertex, std::uint32_t first_index);
		void transform(std::uint32_t first_vertex, const structures::mat4_s& matrix);
		void bounds(structures::vec3_s& minimum, structures::vec3_s& maximum);
		void build_clusters(std::float_t cell_size, std::vector<structures::draw_range_s>& ranges);
		bool upload(structures::mesh_s& mesh);
	};

	extern builder_c builder;
}

//=====================================================================================
