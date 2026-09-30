
//=====================================================================================

#pragma once

#include "../engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class mathematics_c
	{
	public:

		std::float_t dot(structures::vec3_s a, structures::vec3_s b);
		std::float_t dot(structures::vec2_s a, structures::vec2_s b);
		std::float_t length(structures::vec3_s v);
		std::float_t length(structures::vec2_s v);
		std::float_t length_squared(structures::vec3_s v);
		std::float_t distance(structures::vec3_s a, structures::vec3_s b);
		structures::vec3_s cross(structures::vec3_s a, structures::vec3_s b);
		structures::vec3_s normalize(structures::vec3_s v);
		structures::vec2_s normalize(structures::vec2_s v);
		structures::vec3_s lerp(structures::vec3_s a, structures::vec3_s b, std::float_t t);
		structures::vec3_s minimum(structures::vec3_s a, structures::vec3_s b);
		structures::vec3_s maximum(structures::vec3_s a, structures::vec3_s b);
		structures::vec3_s absolute(structures::vec3_s v);
		structures::vec3_s reflect(structures::vec3_s v, structures::vec3_s n);
		structures::vec3_s project_on_plane(structures::vec3_s v, structures::vec3_s n);
		structures::vec3_s any_perpendicular(structures::vec3_s v);

		std::float_t lerp(std::float_t a, std::float_t b, std::float_t t);
		std::float_t clamp(std::float_t v, std::float_t low, std::float_t high);
		std::float_t saturate(std::float_t v);
		std::float_t smoothstep(std::float_t edge0, std::float_t edge1, std::float_t v);
		std::float_t sign(std::float_t v);
		std::float_t wrap_angle(std::float_t radians);
		std::float_t angle_difference(std::float_t from, std::float_t to);
		std::float_t approach(std::float_t current, std::float_t target, std::float_t step);
		structures::vec3_s approach(structures::vec3_s current, structures::vec3_s target, std::float_t step);
		std::float_t damp(std::float_t current, std::float_t target, std::float_t sharpness, std::float_t dt);
		structures::vec3_s damp(structures::vec3_s current, structures::vec3_s target, std::float_t sharpness, std::float_t dt);
		std::float_t ease_out_cubic(std::float_t t);
		std::float_t ease_in_out_cubic(std::float_t t);
		std::float_t ease_out_back(std::float_t t);

		structures::vec3_s forward_from_angles(std::float_t yaw, std::float_t pitch);
		structures::vec3_s right_from_yaw(std::float_t yaw);
		structures::vec3_s flat_forward(std::float_t yaw);

		structures::mat4_s identity();
		structures::mat4_s multiply(const structures::mat4_s& a, const structures::mat4_s& b);
		structures::mat4_s transpose(const structures::mat4_s& a);
		structures::mat4_s inverse(const structures::mat4_s& a);
		structures::mat4_s translation(structures::vec3_s t);
		structures::mat4_s scaling(structures::vec3_s s);
		structures::mat4_s rotation_x(std::float_t radians);
		structures::mat4_s rotation_y(std::float_t radians);
		structures::mat4_s rotation_z(std::float_t radians);
		structures::mat4_s rotation(structures::quat_s q);
		structures::mat4_s compose(structures::vec3_s position, structures::quat_s orientation, structures::vec3_s scale);
		structures::mat4_s basis(structures::vec3_s right, structures::vec3_s up, structures::vec3_s forward, structures::vec3_s position);
		structures::mat4_s look_to(structures::vec3_s eye, structures::vec3_s forward, structures::vec3_s up);
		structures::mat4_s perspective(std::float_t vertical_fov, std::float_t aspect, std::float_t near_plane, structures::vec2_s jitter);
		structures::mat4_s perspective_finite(std::float_t vertical_fov, std::float_t aspect, std::float_t near_plane, std::float_t far_plane);
		structures::mat4_s orthographic(std::float_t left, std::float_t right, std::float_t bottom, std::float_t top, std::float_t near_plane, std::float_t far_plane);
		structures::vec3_s transform_point(structures::vec3_s p, const structures::mat4_s& m);
		bool project(structures::vec3_s p, const structures::mat4_s& m, structures::vec2_s size, structures::vec2_s& out);
		structures::vec3_s transform_vector(structures::vec3_s v, const structures::mat4_s& m);
		structures::vec4_s transform(structures::vec4_s v, const structures::mat4_s& m);

		structures::quat_s quat_identity();
		structures::quat_s quat_axis_angle(structures::vec3_s axis, std::float_t radians);
		structures::quat_s quat_euler(std::float_t yaw, std::float_t pitch, std::float_t roll);
		structures::quat_s quat_multiply(structures::quat_s a, structures::quat_s b);
		structures::quat_s quat_normalize(structures::quat_s q);
		structures::quat_s quat_conjugate(structures::quat_s q);
		structures::quat_s quat_slerp(structures::quat_s a, structures::quat_s b, std::float_t t);
		structures::quat_s quat_nlerp(structures::quat_s a, structures::quat_s b, std::float_t t);
		std::float_t quat_dot(structures::quat_s a, structures::quat_s b);
		structures::quat_s quat_from_basis(structures::vec3_s right, structures::vec3_s up, structures::vec3_s forward);
		structures::quat_s quat_between(structures::vec3_s from, structures::vec3_s to);
		structures::vec3_s quat_rotate(structures::quat_s q, structures::vec3_s v);

		structures::vec3_s closest_on_triangle(structures::vec3_s p, structures::vec3_s a, structures::vec3_s b, structures::vec3_s c);
		std::float_t segment_distance(structures::vec3_s p1, structures::vec3_s q1, structures::vec3_s p2, structures::vec3_s q2);
		std::float_t segment_triangle(structures::vec3_s p, structures::vec3_s q, structures::vec3_s a, structures::vec3_s b, structures::vec3_s c);

		void frustum(const structures::mat4_s& m, structures::vec4_s* planes);
		bool box_visible(const structures::vec4_s* planes, std::uint32_t count, structures::vec3_s minimum, structures::vec3_s maximum);

		std::uint32_t hash_u32(std::uint32_t v);
		std::uint32_t hash_text(const char* text);
		std::float_t hash_float(std::uint32_t v);
		std::float_t halton(std::uint32_t index, std::uint32_t base);
		std::uint32_t field(std::float_t x, std::float_t z, std::float_t spacing, std::float_t& border);
	};

	extern mathematics_c mathematics;
}

//=====================================================================================
