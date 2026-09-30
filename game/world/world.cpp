
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	world_c world;

	void world_c::clear()
	{
		planes.clear();
		brushes.clear();
		cells.clear();
		movers.clear();

		grid_x = grid_y = grid_z = 0;
		carrying = false;
	}
	/*
	//=====================================================================================
	*/
	void world_c::set_mover(std::uint32_t index, const structures::mat4_s& placement, structures::vec3_s center, structures::vec3_s half, std::uint32_t surface, std::uint32_t owner)
	{
		if (index >= movers.size())
		{
			movers.resize(static_cast<std::size_t>(index) + 1u);
		}

		auto& mover{ movers[index] };

		const structures::vec3_s axes[3] = { placement.row3(0u), placement.row3(1u), placement.row3(2u) };
		const structures::vec3_s units[3] = { { 1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f, 1.0f } };
		const auto middle{ mathematics.transform_point(center, placement) };
		const auto extent{ mathematics.absolute(axes[0]) * half.x + mathematics.absolute(axes[1]) * half.y + mathematics.absolute(axes[2]) * half.z };

		for (auto axis{ 0u }; axis < 3u; axis++)
		{
			mover.planes[axis * 4u] = { axes[axis], mathematics.dot(axes[axis], middle) + half[axis] };
			mover.planes[axis * 4u + 1u] = { -axes[axis], -mathematics.dot(axes[axis], middle) + half[axis] };
			mover.planes[axis * 4u + 2u] = { units[axis], middle[axis] + extent[axis] };
			mover.planes[axis * 4u + 3u] = { -units[axis], -middle[axis] + extent[axis] };
		}

		mover.bounds_min = middle - extent;
		mover.bounds_max = middle + extent;
		mover.surface = surface;
		mover.owner = owner;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t world_c::add_brush(const structures::plane_s* brush_planes, std::uint32_t count, std::uint32_t surface, std::uint32_t contents)
	{
		structures::brush_s brush{ static_cast<std::uint32_t>(planes.size()), count, {}, {}, surface, contents };

		for (auto index{ 0u }; index < count; index++)
		{
			planes.push_back(brush_planes[index]);
		}

		brushes.push_back(brush);

		return static_cast<std::uint32_t>(brushes.size() - 1u);
	}
	/*
	//=====================================================================================
	*/
	void world_c::add_box(structures::vec3_s center, structures::vec3_s size, structures::quat_s rotation, std::uint32_t surface, std::uint32_t contents)
	{
		const structures::vec3_s axes[3] = { mathematics.quat_rotate(rotation, { 1.0f, 0.0f, 0.0f }), mathematics.quat_rotate(rotation, { 0.0f, 1.0f, 0.0f }), mathematics.quat_rotate(rotation, { 0.0f, 0.0f, 1.0f }) };
		const structures::vec3_s half{ size.x * 0.5f, size.y * 0.5f, size.z * 0.5f };

		structures::plane_s box_planes[12]{};

		auto count{ 0u };

		for (auto axis{ 0u }; axis < 3u; axis++)
		{
			box_planes[count++] = { axes[axis], mathematics.dot(axes[axis], center) + half[axis] };
			box_planes[count++] = { -axes[axis], -mathematics.dot(axes[axis], center) + half[axis] };
		}

		const auto extent{ mathematics.absolute(axes[0]) * half.x + mathematics.absolute(axes[1]) * half.y + mathematics.absolute(axes[2]) * half.z };

		if (std::fabs(axes[0].x) < 0.9999f || std::fabs(axes[1].y) < 0.9999f)
		{
			const structures::vec3_s units[3] = { { 1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f, 1.0f } };

			for (auto axis{ 0u }; axis < 3u; axis++)
			{
				box_planes[count++] = { units[axis], center[axis] + extent[axis] };
				box_planes[count++] = { -units[axis], -center[axis] + extent[axis] };
			}
		}

		const auto index{ add_brush(box_planes, count, surface, contents) };

		brushes[index].bounds_min = center - extent;
		brushes[index].bounds_max = center + extent;
	}
	/*
	//=====================================================================================
	*/
	void world_c::add_ramp(structures::vec3_s center, structures::vec3_s size, std::float_t yaw, std::uint32_t surface, std::uint32_t contents)
	{
		const auto rotation{ mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, yaw) };
		const auto right{ mathematics.quat_rotate(rotation, { 1.0f, 0.0f, 0.0f }) };
		const auto forward{ mathematics.quat_rotate(rotation, { 0.0f, 0.0f, 1.0f }) };
		const auto half{ size * 0.5f };
		const auto slope{ mathematics.normalize(mathematics.quat_rotate(rotation, { 0.0f, size.z, -size.y })) };
		const auto low_corner{ center + mathematics.quat_rotate(rotation, { 0.0f, -half.y, -half.z }) };
		const auto extent{ mathematics.absolute(right) * half.x + structures::vec3_s{ 0.0f, half.y, 0.0f } + mathematics.absolute(forward) * half.z };

		const structures::plane_s ramp_planes[11] =
		{
			{ { 0.0f, -1.0f, 0.0f }, -(center.y - half.y) },
			{ forward, mathematics.dot(forward, center) + half.z },
			{ right, mathematics.dot(right, center) + half.x },
			{ -right, -mathematics.dot(right, center) + half.x },
			{ slope, mathematics.dot(slope, low_corner) },
			{ { 1.0f, 0.0f, 0.0f }, center.x + extent.x },
			{ { -1.0f, 0.0f, 0.0f }, -center.x + extent.x },
			{ { 0.0f, 1.0f, 0.0f }, center.y + extent.y },
			{ { 0.0f, 0.0f, 1.0f }, center.z + extent.z },
			{ { 0.0f, 0.0f, -1.0f }, -center.z + extent.z },
			{ -forward, -mathematics.dot(forward, center) + half.z }
		};

		const auto index{ add_brush(ramp_planes, 11u, surface, contents) };

		brushes[index].bounds_min = center - extent;
		brushes[index].bounds_max = center + extent;
	}
	/*
	//=====================================================================================
	*/
	void world_c::build()
	{
		structures::vec3_s minimum{ FLT_MAX, FLT_MAX, FLT_MAX };
		structures::vec3_s maximum{ -FLT_MAX, -FLT_MAX, -FLT_MAX };

		for (const auto& brush : brushes)
		{
			minimum = mathematics.minimum(minimum, brush.bounds_min);
			maximum = mathematics.maximum(maximum, brush.bounds_max);
		}

		grid_min = minimum - structures::vec3_s{ 1.0f, 1.0f, 1.0f };

		grid_x = static_cast<std::int32_t>(std::ceil((maximum.x - grid_min.x + 1.0f) / collision_cell_size));
		grid_y = 1;
		grid_z = static_cast<std::int32_t>(std::ceil((maximum.z - grid_min.z + 1.0f) / collision_cell_size));

		cells.assign(static_cast<std::size_t>(grid_x) * grid_y * grid_z, {});

		for (auto index{ 0u }; index < brushes.size(); index++)
		{
			const auto& brush{ brushes[index] };
			const auto x0{ std::clamp(static_cast<std::int32_t>((brush.bounds_min.x - grid_min.x) / collision_cell_size), 0, grid_x - 1) };
			const auto y0{ std::clamp(static_cast<std::int32_t>((brush.bounds_min.y - grid_min.y) / collision_cell_size), 0, grid_y - 1) };
			const auto z0{ std::clamp(static_cast<std::int32_t>((brush.bounds_min.z - grid_min.z) / collision_cell_size), 0, grid_z - 1) };
			const auto x1{ std::clamp(static_cast<std::int32_t>((brush.bounds_max.x - grid_min.x) / collision_cell_size), 0, grid_x - 1) };
			const auto y1{ std::clamp(static_cast<std::int32_t>((brush.bounds_max.y - grid_min.y) / collision_cell_size), 0, grid_y - 1) };
			const auto z1{ std::clamp(static_cast<std::int32_t>((brush.bounds_max.z - grid_min.z) / collision_cell_size), 0, grid_z - 1) };

			for (auto z{ z0 }; z <= z1; z++)
			{
				for (auto y{ y0 }; y <= y1; y++)
				{
					for (auto x{ x0 }; x <= x1; x++)
					{
						cells[(static_cast<std::size_t>(z) * grid_y + y) * grid_x + x].push_back(index);
					}
				}
			}
		}

		logger.write("world: %zu brushes, %zu planes, grid %dx%dx%d", brushes.size(), planes.size(), grid_x, grid_y, grid_z);
	}
	/*
	//=====================================================================================
	*/
	void world_c::insert(std::uint32_t index)
	{
		if (index < brushes.size() && cells.size())
		{
			const auto& brush{ brushes[index] };
			const auto x0{ std::clamp(static_cast<std::int32_t>((brush.bounds_min.x - grid_min.x) / collision_cell_size), 0, grid_x - 1) };
			const auto z0{ std::clamp(static_cast<std::int32_t>((brush.bounds_min.z - grid_min.z) / collision_cell_size), 0, grid_z - 1) };
			const auto x1{ std::clamp(static_cast<std::int32_t>((brush.bounds_max.x - grid_min.x) / collision_cell_size), 0, grid_x - 1) };
			const auto z1{ std::clamp(static_cast<std::int32_t>((brush.bounds_max.z - grid_min.z) / collision_cell_size), 0, grid_z - 1) };

			for (auto z{ z0 }; z <= z1; z++)
			{
				for (auto x{ x0 }; x <= x1; x++)
				{
					cells[static_cast<std::size_t>(z) * grid_x + x].push_back(index);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void world_c::gather(structures::vec3_s minimum, structures::vec3_s maximum, std::vector<std::uint32_t>& out)
	{
		out.clear();

		if (grid_x > 0)
		{
			const auto x0{ std::clamp(static_cast<std::int32_t>((minimum.x - grid_min.x) / collision_cell_size), 0, grid_x - 1) };
			const auto y0{ std::clamp(static_cast<std::int32_t>((minimum.y - grid_min.y) / collision_cell_size), 0, grid_y - 1) };
			const auto z0{ std::clamp(static_cast<std::int32_t>((minimum.z - grid_min.z) / collision_cell_size), 0, grid_z - 1) };
			const auto x1{ std::clamp(static_cast<std::int32_t>((maximum.x - grid_min.x) / collision_cell_size), 0, grid_x - 1) };
			const auto y1{ std::clamp(static_cast<std::int32_t>((maximum.y - grid_min.y) / collision_cell_size), 0, grid_y - 1) };
			const auto z1{ std::clamp(static_cast<std::int32_t>((maximum.z - grid_min.z) / collision_cell_size), 0, grid_z - 1) };

			for (auto z{ z0 }; z <= z1; z++)
			{
				for (auto y{ y0 }; y <= y1; y++)
				{
					for (auto x{ x0 }; x <= x1; x++)
					{
						const auto& cell{ cells[(static_cast<std::size_t>(z) * grid_y + y) * grid_x + x] };

						out.insert(out.end(), cell.begin(), cell.end());
					}
				}
			}

			std::sort(out.begin(), out.end());

			out.erase(std::unique(out.begin(), out.end()), out.end());
		}
	}
	/*
	//=====================================================================================
	*/
	structures::trace_s world_c::trace(structures::vec3_s start, structures::vec3_s end, structures::vec3_s extents, std::uint32_t mask)
	{
		thread_local std::vector<std::uint32_t> candidates;

		structures::trace_s result{ 1.0f, end, { 0.0f, 0.0f, 0.0f }, -1, structures::surface_concrete, false, false, false };

		gather(mathematics.minimum(start, end) - extents - structures::vec3_s{ 0.01f, 0.01f, 0.01f }, mathematics.maximum(start, end) + extents + structures::vec3_s{ 0.01f, 0.01f, 0.01f }, candidates);

		const auto swept_min{ mathematics.minimum(start, end) - extents };
		const auto swept_max{ mathematics.maximum(start, end) + extents };

		for (const auto index : candidates)
		{
			const auto& brush{ brushes[index] };

			if ((brush.contents & mask) && brush.bounds_min.x <= swept_max.x && brush.bounds_max.x >= swept_min.x && brush.bounds_min.y <= swept_max.y && brush.bounds_max.y >= swept_min.y && brush.bounds_min.z <= swept_max.z && brush.bounds_max.z >= swept_min.z)
			{
				clip_planes(&planes[brush.first_plane], brush.plane_count, static_cast<std::int32_t>(index), brush.surface, start, end, extents, result);
			}
		}

		for (auto index{ 0u }; index < movers.size() && carrying == false && (mask & structures::contents_solid); index++)
		{
			if (const auto& mover{ movers[index] }; mover.bounds_min.x <= swept_max.x && mover.bounds_max.x >= swept_min.x && mover.bounds_min.y <= swept_max.y && mover.bounds_max.y >= swept_min.y && mover.bounds_min.z <= swept_max.z && mover.bounds_max.z >= swept_min.z)
			{
				clip_planes(mover.planes, 12u, mover_brush_base + static_cast<std::int32_t>(index), mover.surface, start, end, extents, result);
			}
		}

		if (terrain.enabled && (mask & structures::contents_solid))
		{
			terrain.clip(start, end, extents, result);
		}

		result.hit = result.fraction < 1.0f || result.start_solid;
		result.end = start + (end - start) * result.fraction;

		return result;
	}
	/*
	//=====================================================================================
	*/
	void world_c::clip_planes(const structures::plane_s* brush_planes, std::uint32_t plane_count, std::int32_t index, std::uint32_t surface, structures::vec3_s start, structures::vec3_s end, structures::vec3_s extents, structures::trace_s& result)
	{
		auto enter{ -1.0f };
		auto leave{ 1.0f };
		auto starts_out{ false };
		auto gets_out{ false };
		auto relevant{ true };

		const structures::plane_s* clip_plane{ nullptr };

		for (auto plane_index{ 0u }; plane_index < plane_count && relevant; plane_index++)
		{
			const auto& plane{ brush_planes[plane_index] };
			const auto distance{ plane.distance + mathematics.dot(mathematics.absolute(plane.normal), extents) };
			const auto d1{ mathematics.dot(start, plane.normal) - distance };
			const auto d2{ mathematics.dot(end, plane.normal) - distance };

			gets_out = gets_out || d2 > 0.0f;
			starts_out = starts_out || d1 > 0.0f;

			if (d1 > 0.0f && (d2 >= collision_epsilon || d2 >= d1))
			{
				relevant = false;
			}

			else if (d1 > 0.0f || d2 > 0.0f)
			{
				if (d1 > d2)
				{
					if (const auto fraction{ std::max((d1 - collision_epsilon) / (d1 - d2), 0.0f) }; fraction > enter)
					{
						enter = fraction;

						clip_plane = &plane;
					}
				}

				else
				{
					leave = std::min(leave, std::min((d1 + collision_epsilon) / (d1 - d2), 1.0f));
				}
			}
		}

		if (relevant)
		{
			if (starts_out)
			{
				if (enter < leave && enter > -1.0f && enter < result.fraction && clip_plane)
				{
					result.fraction = std::max(enter, 0.0f);
					result.normal = clip_plane->normal;
					result.brush = index;
					result.surface = surface;
				}
			}

			else
			{
				result.start_solid = true;
				result.all_solid = result.all_solid || gets_out == false;
				result.brush = index;
				result.surface = surface;

				if (result.all_solid)
				{
					result.fraction = 0.0f;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool world_c::box_solid(structures::vec3_s center, structures::vec3_s extents, std::uint32_t mask)
	{
		return trace(center, center, extents, mask).start_solid;
	}
}

//=====================================================================================
