
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	mathematics_c mathematics;

	std::float_t mathematics_c::dot(structures::vec3_s a, structures::vec3_s b)
	{
		return a.x * b.x + a.y * b.y + a.z * b.z;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::dot(structures::vec2_s a, structures::vec2_s b)
	{
		return a.x * b.x + a.y * b.y;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::length(structures::vec3_s v)
	{
		return std::sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::length(structures::vec2_s v)
	{
		return std::sqrt(v.x * v.x + v.y * v.y);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::length_squared(structures::vec3_s v)
	{
		return v.x * v.x + v.y * v.y + v.z * v.z;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::distance(structures::vec3_s a, structures::vec3_s b)
	{
		return length(a - b);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::cross(structures::vec3_s a, structures::vec3_s b)
	{
		return { a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::normalize(structures::vec3_s v)
	{
		if (const auto size{ length(v) }; size > epsilon)
		{
			return v / size;
		}

		return { 0.0f, 0.0f, 0.0f };
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s mathematics_c::normalize(structures::vec2_s v)
	{
		if (const auto size{ length(v) }; size > epsilon)
		{
			return v / size;
		}

		return { 0.0f, 0.0f };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::lerp(structures::vec3_s a, structures::vec3_s b, std::float_t t)
	{
		return a + (b - a) * t;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::minimum(structures::vec3_s a, structures::vec3_s b)
	{
		return { std::min(a.x, b.x), std::min(a.y, b.y), std::min(a.z, b.z) };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::maximum(structures::vec3_s a, structures::vec3_s b)
	{
		return { std::max(a.x, b.x), std::max(a.y, b.y), std::max(a.z, b.z) };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::absolute(structures::vec3_s v)
	{
		return { std::fabs(v.x), std::fabs(v.y), std::fabs(v.z) };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::reflect(structures::vec3_s v, structures::vec3_s n)
	{
		return v - n * (2.0f * dot(v, n));
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::project_on_plane(structures::vec3_s v, structures::vec3_s n)
	{
		return v - n * dot(v, n);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::any_perpendicular(structures::vec3_s v)
	{
		if (std::fabs(v.y) < 0.9f)
		{
			return normalize(cross(v, { 0.0f, 1.0f, 0.0f }));
		}

		return normalize(cross(v, { 1.0f, 0.0f, 0.0f }));
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::lerp(std::float_t a, std::float_t b, std::float_t t)
	{
		return a + (b - a) * t;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::clamp(std::float_t v, std::float_t low, std::float_t high)
	{
		return v < low ? low : (v > high ? high : v);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::saturate(std::float_t v)
	{
		return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::smoothstep(std::float_t edge0, std::float_t edge1, std::float_t v)
	{
		const auto t{ saturate((v - edge0) / (edge1 - edge0)) };

		return t * t * (3.0f - 2.0f * t);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::sign(std::float_t v)
	{
		return v > 0.0f ? 1.0f : (v < 0.0f ? -1.0f : 0.0f);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::wrap_angle(std::float_t radians)
	{
		return radians - two_pi * std::floor((radians + pi) / two_pi);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::angle_difference(std::float_t from, std::float_t to)
	{
		return wrap_angle(to - from);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::approach(std::float_t current, std::float_t target, std::float_t step)
	{
		if (current < target)
		{
			return std::min(current + step, target);
		}

		return std::max(current - step, target);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::approach(structures::vec3_s current, structures::vec3_s target, std::float_t step)
	{
		const auto difference{ target - current };

		if (const auto size{ length(difference) }; size > step)
		{
			return current + difference * (step / size);
		}

		return target;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::damp(std::float_t current, std::float_t target, std::float_t sharpness, std::float_t dt)
	{
		return lerp(current, target, 1.0f - std::exp(-sharpness * dt));
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::damp(structures::vec3_s current, structures::vec3_s target, std::float_t sharpness, std::float_t dt)
	{
		return lerp(current, target, 1.0f - std::exp(-sharpness * dt));
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::ease_out_cubic(std::float_t t)
	{
		return 1.0f - (1.0f - t) * (1.0f - t) * (1.0f - t);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::ease_in_out_cubic(std::float_t t)
	{
		return t < 0.5f ? 4.0f * t * t * t : 1.0f - (-2.0f * t + 2.0f) * (-2.0f * t + 2.0f) * (-2.0f * t + 2.0f) * 0.5f;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::ease_out_back(std::float_t t)
	{
		return 1.0f + 2.70158f * (t - 1.0f) * (t - 1.0f) * (t - 1.0f) + 1.70158f * (t - 1.0f) * (t - 1.0f);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::forward_from_angles(std::float_t yaw, std::float_t pitch)
	{
		return { std::sin(yaw) * std::cos(pitch), std::sin(pitch), std::cos(yaw) * std::cos(pitch) };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::right_from_yaw(std::float_t yaw)
	{
		return { std::cos(yaw), 0.0f, -std::sin(yaw) };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::flat_forward(std::float_t yaw)
	{
		return { std::sin(yaw), 0.0f, std::cos(yaw) };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::identity()
	{
		return { { { 1.0f, 0.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f, 0.0f, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::multiply(const structures::mat4_s& a, const structures::mat4_s& b)
	{
		structures::mat4_s result{};

		for (auto row{ 0u }; row < 4u; row++)
		{
			for (auto column{ 0u }; column < 4u; column++)
			{
				result.m[row][column] = a.m[row][0] * b.m[0][column] + a.m[row][1] * b.m[1][column] + a.m[row][2] * b.m[2][column] + a.m[row][3] * b.m[3][column];
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::transpose(const structures::mat4_s& a)
	{
		structures::mat4_s result{};

		for (auto row{ 0u }; row < 4u; row++)
		{
			for (auto column{ 0u }; column < 4u; column++)
			{
				result.m[row][column] = a.m[column][row];
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::inverse(const structures::mat4_s& a)
	{
		const auto m{ &a.m[0][0] };

		structures::mat4_s result{};

		const auto r{ &result.m[0][0] };

		r[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
		r[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
		r[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
		r[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
		r[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
		r[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
		r[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
		r[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
		r[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
		r[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
		r[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
		r[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
		r[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
		r[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
		r[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
		r[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];

		if (const auto determinant{ m[0] * r[0] + m[1] * r[4] + m[2] * r[8] + m[3] * r[12] }; std::fabs(determinant) > 1e-12f)
		{
			for (auto index{ 0u }; index < 16u; index++)
			{
				r[index] /= determinant;
			}

			return result;
		}

		return identity();
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::translation(structures::vec3_s t)
	{
		return { { { 1.0f, 0.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, 1.0f, 0.0f }, { t.x, t.y, t.z, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::scaling(structures::vec3_s s)
	{
		return { { { s.x, 0.0f, 0.0f, 0.0f }, { 0.0f, s.y, 0.0f, 0.0f }, { 0.0f, 0.0f, s.z, 0.0f }, { 0.0f, 0.0f, 0.0f, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::rotation_x(std::float_t radians)
	{
		return { { { 1.0f, 0.0f, 0.0f, 0.0f }, { 0.0f, std::cos(radians), std::sin(radians), 0.0f }, { 0.0f, -std::sin(radians), std::cos(radians), 0.0f }, { 0.0f, 0.0f, 0.0f, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::rotation_y(std::float_t radians)
	{
		return { { { std::cos(radians), 0.0f, -std::sin(radians), 0.0f }, { 0.0f, 1.0f, 0.0f, 0.0f }, { std::sin(radians), 0.0f, std::cos(radians), 0.0f }, { 0.0f, 0.0f, 0.0f, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::rotation_z(std::float_t radians)
	{
		return { { { std::cos(radians), std::sin(radians), 0.0f, 0.0f }, { -std::sin(radians), std::cos(radians), 0.0f, 0.0f }, { 0.0f, 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f, 0.0f, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::rotation(structures::quat_s q)
	{
		const auto xx{ q.x * q.x }, yy{ q.y * q.y }, zz{ q.z * q.z };
		const auto xy{ q.x * q.y }, xz{ q.x * q.z }, yz{ q.y * q.z };
		const auto wx{ q.w * q.x }, wy{ q.w * q.y }, wz{ q.w * q.z };

		return { { { 1.0f - 2.0f * (yy + zz), 2.0f * (xy + wz), 2.0f * (xz - wy), 0.0f }, { 2.0f * (xy - wz), 1.0f - 2.0f * (xx + zz), 2.0f * (yz + wx), 0.0f }, { 2.0f * (xz + wy), 2.0f * (yz - wx), 1.0f - 2.0f * (xx + yy), 0.0f }, { 0.0f, 0.0f, 0.0f, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::compose(structures::vec3_s position, structures::quat_s orientation, structures::vec3_s scale)
	{
		return basis(quat_rotate(orientation, { scale.x, 0.0f, 0.0f }), quat_rotate(orientation, { 0.0f, scale.y, 0.0f }), quat_rotate(orientation, { 0.0f, 0.0f, scale.z }), position);
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::basis(structures::vec3_s right, structures::vec3_s up, structures::vec3_s forward, structures::vec3_s position)
	{
		return { { { right.x, right.y, right.z, 0.0f }, { up.x, up.y, up.z, 0.0f }, { forward.x, forward.y, forward.z, 0.0f }, { position.x, position.y, position.z, 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::look_to(structures::vec3_s eye, structures::vec3_s forward, structures::vec3_s up)
	{
		const auto z_axis{ normalize(forward) };
		const auto x_axis{ normalize(cross(up, z_axis)) };
		const auto y_axis{ cross(z_axis, x_axis) };

		return { { { x_axis.x, y_axis.x, z_axis.x, 0.0f }, { x_axis.y, y_axis.y, z_axis.y, 0.0f }, { x_axis.z, y_axis.z, z_axis.z, 0.0f }, { -dot(x_axis, eye), -dot(y_axis, eye), -dot(z_axis, eye), 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::perspective(std::float_t vertical_fov, std::float_t aspect, std::float_t near_plane, structures::vec2_s jitter)
	{
		const auto y_scale{ 1.0f / std::tan(vertical_fov * 0.5f) };

		return { { { y_scale / aspect, 0.0f, 0.0f, 0.0f }, { 0.0f, y_scale, 0.0f, 0.0f }, { jitter.x, jitter.y, 0.0f, 1.0f }, { 0.0f, 0.0f, near_plane, 0.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::perspective_finite(std::float_t vertical_fov, std::float_t aspect, std::float_t near_plane, std::float_t far_plane)
	{
		const auto y_scale{ 1.0f / std::tan(vertical_fov * 0.5f) };

		return { { { y_scale / aspect, 0.0f, 0.0f, 0.0f }, { 0.0f, y_scale, 0.0f, 0.0f }, { 0.0f, 0.0f, near_plane / (near_plane - far_plane), 1.0f }, { 0.0f, 0.0f, near_plane * far_plane / (far_plane - near_plane), 0.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::mat4_s mathematics_c::orthographic(std::float_t left, std::float_t right, std::float_t bottom, std::float_t top, std::float_t near_plane, std::float_t far_plane)
	{
		return { { { 2.0f / (right - left), 0.0f, 0.0f, 0.0f }, { 0.0f, 2.0f / (top - bottom), 0.0f, 0.0f }, { 0.0f, 0.0f, 1.0f / (far_plane - near_plane), 0.0f }, { (left + right) / (left - right), (top + bottom) / (bottom - top), near_plane / (near_plane - far_plane), 1.0f } } };
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::transform_point(structures::vec3_s p, const structures::mat4_s& m)
	{
		return { p.x * m.m[0][0] + p.y * m.m[1][0] + p.z * m.m[2][0] + m.m[3][0], p.x * m.m[0][1] + p.y * m.m[1][1] + p.z * m.m[2][1] + m.m[3][1], p.x * m.m[0][2] + p.y * m.m[1][2] + p.z * m.m[2][2] + m.m[3][2] };
	}
	/*
	//=====================================================================================
	*/
	bool mathematics_c::project(structures::vec3_s p, const structures::mat4_s& m, structures::vec2_s size, structures::vec2_s& out)
	{
		const auto x{ p.x * m.m[0][0] + p.y * m.m[1][0] + p.z * m.m[2][0] + m.m[3][0] };
		const auto y{ p.x * m.m[0][1] + p.y * m.m[1][1] + p.z * m.m[2][1] + m.m[3][1] };
		const auto w{ p.x * m.m[0][3] + p.y * m.m[1][3] + p.z * m.m[2][3] + m.m[3][3] };

		if (w > 0.01f)
		{
			out = { (x / w * 0.5f + 0.5f) * size.x, (0.5f - y / w * 0.5f) * size.y };

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::transform_vector(structures::vec3_s v, const structures::mat4_s& m)
	{
		return { v.x * m.m[0][0] + v.y * m.m[1][0] + v.z * m.m[2][0], v.x * m.m[0][1] + v.y * m.m[1][1] + v.z * m.m[2][1], v.x * m.m[0][2] + v.y * m.m[1][2] + v.z * m.m[2][2] };
	}
	/*
	//=====================================================================================
	*/
	structures::vec4_s mathematics_c::transform(structures::vec4_s v, const structures::mat4_s& m)
	{
		return { v.x * m.m[0][0] + v.y * m.m[1][0] + v.z * m.m[2][0] + v.w * m.m[3][0], v.x * m.m[0][1] + v.y * m.m[1][1] + v.z * m.m[2][1] + v.w * m.m[3][1], v.x * m.m[0][2] + v.y * m.m[1][2] + v.z * m.m[2][2] + v.w * m.m[3][2], v.x * m.m[0][3] + v.y * m.m[1][3] + v.z * m.m[2][3] + v.w * m.m[3][3] };
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_identity()
	{
		return { 0.0f, 0.0f, 0.0f, 1.0f };
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_axis_angle(structures::vec3_s axis, std::float_t radians)
	{
		const auto unit{ normalize(axis) * std::sin(radians * 0.5f) };

		return { unit.x, unit.y, unit.z, std::cos(radians * 0.5f) };
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_euler(std::float_t yaw, std::float_t pitch, std::float_t roll)
	{
		return quat_multiply(quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw), quat_multiply(quat_axis_angle({ 1.0f, 0.0f, 0.0f }, -pitch), quat_axis_angle({ 0.0f, 0.0f, 1.0f }, roll)));
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_multiply(structures::quat_s a, structures::quat_s b)
	{
		return { a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y, a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x, a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w, a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z };
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_normalize(structures::quat_s q)
	{
		if (const auto size{ std::sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w) }; size > epsilon)
		{
			return { q.x / size, q.y / size, q.z / size, q.w / size };
		}

		return quat_identity();
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_conjugate(structures::quat_s q)
	{
		return { -q.x, -q.y, -q.z, q.w };
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_slerp(structures::quat_s a, structures::quat_s b, std::float_t t)
	{
		auto cosine{ a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w };

		if (cosine < 0.0f)
		{
			b = { -b.x, -b.y, -b.z, -b.w };

			cosine = -cosine;
		}

		if (cosine > 0.9995f)
		{
			return quat_normalize({ a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t, a.w + (b.w - a.w) * t });
		}

		const auto angle{ std::acos(cosine) };
		const auto inverse_sine{ 1.0f / std::sin(angle) };
		const auto weight_a{ std::sin((1.0f - t) * angle) * inverse_sine };
		const auto weight_b{ std::sin(t * angle) * inverse_sine };

		return { a.x * weight_a + b.x * weight_b, a.y * weight_a + b.y * weight_b, a.z * weight_a + b.z * weight_b, a.w * weight_a + b.w * weight_b };
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_nlerp(structures::quat_s a, structures::quat_s b, std::float_t t)
	{
		const auto side{ quat_dot(a, b) < 0.0f ? -1.0f : 1.0f };

		return quat_normalize({ a.x + (b.x * side - a.x) * t, a.y + (b.y * side - a.y) * t, a.z + (b.z * side - a.z) * t, a.w + (b.w * side - a.w) * t });
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::quat_dot(structures::quat_s a, structures::quat_s b)
	{
		return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_from_basis(structures::vec3_s right, structures::vec3_s up, structures::vec3_s forward)
	{
		if (const auto trace{ right.x + up.y + forward.z }; trace > 0.0f)
		{
			const auto s{ std::sqrt(trace + 1.0f) * 2.0f };

			return quat_normalize({ (up.z - forward.y) / s, (forward.x - right.z) / s, (right.y - up.x) / s, 0.25f * s });
		}

		else if (right.x > up.y && right.x > forward.z)
		{
			const auto s{ std::sqrt(1.0f + right.x - up.y - forward.z) * 2.0f };

			return quat_normalize({ 0.25f * s, (up.x + right.y) / s, (forward.x + right.z) / s, (up.z - forward.y) / s });
		}

		else if (up.y > forward.z)
		{
			const auto s{ std::sqrt(1.0f + up.y - right.x - forward.z) * 2.0f };

			return quat_normalize({ (up.x + right.y) / s, 0.25f * s, (forward.y + up.z) / s, (forward.x - right.z) / s });
		}

		const auto s{ std::sqrt(1.0f + forward.z - right.x - up.y) * 2.0f };

		return quat_normalize({ (forward.x + right.z) / s, (forward.y + up.z) / s, 0.25f * s, (right.y - up.x) / s });
	}
	/*
	//=====================================================================================
	*/
	structures::quat_s mathematics_c::quat_between(structures::vec3_s from, structures::vec3_s to)
	{
		const auto a{ normalize(from) };
		const auto b{ normalize(to) };

		if (const auto cosine{ dot(a, b) }; cosine > -0.99999f)
		{
			const auto axis{ cross(a, b) };

			return quat_normalize({ axis.x, axis.y, axis.z, 1.0f + cosine });
		}

		return quat_axis_angle(any_perpendicular(a), pi);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::quat_rotate(structures::quat_s q, structures::vec3_s v)
	{
		const auto axis{ structures::vec3_s{ q.x, q.y, q.z } };
		const auto t{ cross(axis, v) * 2.0f };

		return v + t * q.w + cross(axis, t);
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s mathematics_c::closest_on_triangle(structures::vec3_s p, structures::vec3_s a, structures::vec3_s b, structures::vec3_s c)
	{
		const auto ab{ b - a };
		const auto ac{ c - a };
		const auto ap{ p - a };
		const auto d1{ dot(ab, ap) };
		const auto d2{ dot(ac, ap) };
		const auto bp{ p - b };
		const auto d3{ dot(ab, bp) };
		const auto d4{ dot(ac, bp) };
		const auto cp{ p - c };
		const auto d5{ dot(ab, cp) };
		const auto d6{ dot(ac, cp) };
		const auto vc{ d1 * d4 - d3 * d2 };
		const auto vb{ d5 * d2 - d1 * d6 };
		const auto va{ d3 * d6 - d5 * d4 };

		if (d1 <= 0.0f && d2 <= 0.0f)
		{
			return a;
		}

		if (d3 >= 0.0f && d4 <= d3)
		{
			return b;
		}

		if (vc <= 0.0f && d1 >= 0.0f && d3 <= 0.0f)
		{
			return a + ab * (d1 / (d1 - d3));
		}

		if (d6 >= 0.0f && d5 <= d6)
		{
			return c;
		}

		if (vb <= 0.0f && d2 >= 0.0f && d6 <= 0.0f)
		{
			return a + ac * (d2 / (d2 - d6));
		}

		if (va <= 0.0f && d4 - d3 >= 0.0f && d5 - d6 >= 0.0f)
		{
			return b + (c - b) * ((d4 - d3) / ((d4 - d3) + (d5 - d6)));
		}

		const auto denominator{ 1.0f / (va + vb + vc) };

		return a + ab * (vb * denominator) + ac * (vc * denominator);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::segment_distance(structures::vec3_s p1, structures::vec3_s q1, structures::vec3_s p2, structures::vec3_s q2)
	{
		const auto d1{ q1 - p1 };
		const auto d2{ q2 - p2 };
		const auto r{ p1 - p2 };
		const auto a{ dot(d1, d1) };
		const auto e{ dot(d2, d2) };
		const auto f{ dot(d2, r) };
		const auto c{ dot(d1, r) };
		const auto b{ dot(d1, d2) };
		const auto denominator{ a * e - b * b };

		auto s{ a > 1e-12f && e > 1e-12f && denominator > 1e-12f ? saturate((b * f - c * e) / denominator) : 0.0f };
		auto t{ e > 1e-12f ? (b * s + f) / e : 0.0f };

		if (t < 0.0f)
		{
			t = 0.0f;
			s = a > 1e-12f ? saturate(-c / a) : 0.0f;
		}

		else if (t > 1.0f)
		{
			t = 1.0f;
			s = a > 1e-12f ? saturate((b - c) / a) : 0.0f;
		}

		return distance(p1 + d1 * s, p2 + d2 * t);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::segment_triangle(structures::vec3_s p, structures::vec3_s q, structures::vec3_s a, structures::vec3_s b, structures::vec3_s c)
	{
		const auto normal{ cross(b - a, c - a) };
		const auto side_p{ dot(normal, p - a) };
		const auto side_q{ dot(normal, q - a) };

		if ((side_p > 0.0f) != (side_q > 0.0f) && std::fabs(side_p - side_q) > 1e-12f)
		{
			const auto hit{ p + (q - p) * (side_p / (side_p - side_q)) };

			if (distance(closest_on_triangle(hit, a, b, c), hit) < 1e-5f)
			{
				return 0.0f;
			}
		}

		return std::min({ distance(closest_on_triangle(p, a, b, c), p), distance(closest_on_triangle(q, a, b, c), q), segment_distance(p, q, a, b), segment_distance(p, q, b, c), segment_distance(p, q, c, a) });
	}
	/*
	//=====================================================================================
	*/
	void mathematics_c::frustum(const structures::mat4_s& m, structures::vec4_s* planes)
	{
		const auto column = [&](std::uint32_t j)
			{
				return structures::vec4_s{ m.m[0][j], m.m[1][j], m.m[2][j], m.m[3][j] };
			};

		planes[0] = column(3u) + column(0u);
		planes[1] = column(3u) - column(0u);
		planes[2] = column(3u) + column(1u);
		planes[3] = column(3u) - column(1u);
		planes[4] = column(2u);
		planes[5] = column(3u) - column(2u);
	}
	/*
	//=====================================================================================
	*/
	bool mathematics_c::box_visible(const structures::vec4_s* planes, std::uint32_t count, structures::vec3_s minimum, structures::vec3_s maximum)
	{
		auto visible{ true };

		for (auto index{ 0u }; index < count; index++)
		{
			const auto& plane{ planes[index] };

			if (visible && plane.x * (plane.x > 0.0f ? maximum.x : minimum.x) + plane.y * (plane.y > 0.0f ? maximum.y : minimum.y) + plane.z * (plane.z > 0.0f ? maximum.z : minimum.z) + plane.w < 0.0f)
			{
				visible = false;
			}
		}

		return visible;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::halton(std::uint32_t index, std::uint32_t base)
	{
		auto result{ 0.0f };
		auto fraction{ 1.0f };

		for (; index > 0u; index /= base)
		{
			fraction /= static_cast<std::float_t>(base);

			result += fraction * static_cast<std::float_t>(index % base);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t mathematics_c::hash_text(const char* text)
	{
		auto hash{ 2166136261u };

		for (auto cursor{ text }; cursor && *cursor; cursor++)
		{
			hash = (hash ^ static_cast<std::uint8_t>(*cursor)) * 16777619u;
		}

		return hash;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t mathematics_c::hash_u32(std::uint32_t v)
	{
		v ^= v >> 16u;
		v *= 0x7FEB352Du;
		v ^= v >> 15u;
		v *= 0x846CA68Bu;
		v ^= v >> 16u;

		return v;
	}
	/*
	//=====================================================================================
	*/
	std::float_t mathematics_c::hash_float(std::uint32_t v)
	{
		return static_cast<std::float_t>(hash_u32(v) >> 8u) * (1.0f / 16777216.0f);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t mathematics_c::field(std::float_t x, std::float_t z, std::float_t spacing, std::float_t& border)
	{
		const auto column{ static_cast<std::int32_t>(std::floor(x / spacing)) };
		const auto row{ static_cast<std::int32_t>(std::floor(z / spacing)) };

		structures::vec2_s first{};
		structures::vec2_s runner{};

		auto nearest{ FLT_MAX };
		auto second{ FLT_MAX };
		auto result{ 0u };

		for (auto dz{ -1 }; dz <= 1; dz++)
		{
			for (auto dx{ -1 }; dx <= 1; dx++)
			{
				const auto hash{ hash_u32(static_cast<std::uint32_t>(column + dx) * 73856093u ^ static_cast<std::uint32_t>(row + dz) * 19349663u ^ 0x5F3759DFu) };
				const structures::vec2_s seed{ (static_cast<std::float_t>(column + dx) + 0.5f + (hash_float(hash) - 0.5f) * 0.72f) * spacing, (static_cast<std::float_t>(row + dz) + 0.5f + (hash_float(hash ^ 0x9E3779B9u) - 0.5f) * 0.72f) * spacing };
				const auto gap{ length(structures::vec2_s{ x - seed.x, z - seed.y }) };

				if (gap < nearest)
				{
					second = nearest;
					runner = first;
					nearest = gap;
					first = seed;
					result = hash;
				}

				else if (gap < second)
				{
					second = gap;
					runner = seed;
				}
			}
		}

		border = (second * second - nearest * nearest) / std::max(2.0f * length(runner - first), 0.001f);

		return result;
	}
}

//=====================================================================================
