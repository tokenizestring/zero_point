
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_towns_c baker_towns;

	void baker_towns_c::plan(std::vector<baker::course_s>& courses, const std::vector<structures::station_s>& stops, const std::string& preview_path)
	{
		plots.clear();

		for (const auto& profile : town_profiles)
		{
			for (const auto& site : world_sites)
			{
				if (site.landmark == profile.landmark)
				{
					lay_out(profile, site, courses, stops);

					preview(preview_path.substr(0u, preview_path.rfind('.')) + "_town_" + std::to_string(profile.landmark) + ".png", profile, site, courses);
				}
			}
		}

		logger.write("baker: towns laid out, %zu plots, %zu courses", plots.size(), courses.size());
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::lay_out(const structures::town_profile_s& profile, const structures::world_site_s& site, std::vector<baker::course_s>& courses, const std::vector<structures::station_s>& stops)
	{
		const auto first_course{ static_cast<std::uint32_t>(courses.size()) };
		const auto lane_rank{ profile.style == structures::town_style_capital ? 1u : 2u };

		first_plot = plots.size();
		state = profile.seed * 2654435761u + 7u;

		survey(profile, site, courses, stops);

		auto hub{ false };

		for (const auto index : members)
		{
			auto gap{ FLT_MAX };

			nearest(courses[index], site.position, gap);

			hub = hub || gap < baker::town_gate_reach * 0.5f;
		}

		const auto entries{ members };

		for (const auto index : entries)
		{
			for (auto end{ 0u }; end < 2u; end++)
			{
				const auto point{ end ? courses[index].path.back() : courses[index].path.front() };
				const auto width{ courses[index].width };

				auto dead{ mathematics.length(point - site.position) > baker::town_gate_reach && mathematics.length(point - site.position) < profile.radius };

				for (auto other{ 0u }; dead && other < courses.size(); other++)
				{
					auto gap{ FLT_MAX };

					if (other != index && courses[other].kind == structures::route_road)
					{
						nearest(courses[other], point, gap);

						dead = gap > baker::town_dead_end;
					}
				}

				std::vector<structures::vec2_s> route;

				if (dead && connect(cell_at(point), hub ? -1 : cell_at(site.position), index, UINT32_MAX, route))
				{
					const auto parent{ hub ? owner[cell_at(route.back())] : UINT32_MAX };

					route.front() = point;

					if (hub == false)
					{
						route.back() = site.position;
					}

					hub = lay_street(route, 0u, width, UINT32_MAX, parent, profile.landmark, courses) || hub;
				}
			}
		}

		std::vector<structures::vec2_s> targets;

		for (auto index{ 0u }; index < profile.streets; index++)
		{
			const auto ring{ profile.style == structures::town_style_capital ? baker::town_rings[index % std::size(baker::town_rings)] : 0.55f + 0.35f * random() };
			const auto angle{ (static_cast<std::float_t>(index) + 0.6f * random()) / static_cast<std::float_t>(profile.streets) * two_pi + static_cast<std::float_t>(profile.seed) };

			auto found{ false };

			for (auto attempt{ 0u }; attempt < 8u && found == false; attempt++)
			{
				const auto scale{ ring * (1.0f - 0.07f * static_cast<std::float_t>(attempt)) };
				const auto twist{ angle + (attempt % 2u ? 0.12f : -0.12f) * static_cast<std::float_t>(attempt) };
				const structures::vec2_s point{ site.position.x + std::sin(twist) * profile.radius * scale, site.position.y + std::cos(twist) * profile.radius * scale };

				if (const auto cell{ cell_at(point) }; cell >= 0 && blocked[cell] == 0u)
				{
					targets.push_back(point);

					found = true;
				}
			}
		}

		std::sort(targets.begin(), targets.end(), [&](const structures::vec2_s& a, const structures::vec2_s& b) { return mathematics.length(a - site.position) < mathematics.length(b - site.position); });

		for (const auto& target : targets)
		{
			std::vector<structures::vec2_s> route;

			if (const auto cell{ cell_at(target) }; reach[cell] > baker::town_crowd_reach * 0.7f && connect(cell, -1, UINT32_MAX, UINT32_MAX, route))
			{
				const auto parent{ owner[cell_at(route.back())] };
				const auto rank{ std::min(courses[parent].rank + 1u, lane_rank) };

				std::reverse(route.begin(), route.end());

				lay_street(route, rank, rank > 1u ? town_lane_width : town_street_width, parent, UINT32_MAX, profile.landmark, courses);
			}
		}

		const auto last_course{ static_cast<std::uint32_t>(courses.size()) };

		auto looped{ 0u };

		for (auto index{ first_course }; index < last_course && looped < profile.loops; index++)
		{
			std::vector<structures::vec2_s> route;

			if (courses[index].rank > 0u && connect(cell_at(courses[index].path.back()), -1, index, courses[index].parent, route) && route.size() * baker::town_cell < baker::town_loop_reach)
			{
				const auto parent{ owner[cell_at(route.back())] };
				const auto rank{ courses[index].rank };

				route.front() = courses[index].path.back();

				looped += lay_street(route, rank, rank > 1u ? town_lane_width : town_street_width, UINT32_MAX, parent, profile.landmark, courses) ? 1u : 0u;
			}
		}

		measure_room(courses, stops);

		parcel(profile, site, courses);

		logger.write("baker: %s planned with %zu streets (%zu new, %u loops), %zu plots", landmark_names[profile.landmark], members.size(), courses.size() - first_course, looped, plots.size() - first_plot);
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::survey(const structures::town_profile_s& profile, const structures::world_site_s& site, const std::vector<baker::course_s>& courses, const std::vector<structures::station_s>& stops)
	{
		const auto span{ (profile.radius + baker::town_margin) * 2.0f };

		cells = static_cast<std::uint32_t>(std::ceil(span / baker::town_cell));
		corner = { site.position.x - span * 0.5f, site.position.y - span * 0.5f };

		level.assign(static_cast<std::size_t>(cells) * cells, 0.0f);
		reach.assign(level.size(), FLT_MAX);
		owner.assign(level.size(), UINT32_MAX);
		blocked.assign(level.size(), 0u);
		members.clear();

		for (auto cell{ 0 }; cell < static_cast<std::int32_t>(level.size()); cell++)
		{
			const auto spot{ cell_center(cell) };

			level[cell] = baker_terrain.height_at(spot.x, spot.y);
			blocked[cell] = level[cell] < sea_level + baker::town_ground_floor || mathematics.length(spot - site.position) > profile.radius ? 1u : 0u;
		}

		for (auto index{ 0u }; index < courses.size(); index++)
		{
			const auto& course{ courses[index] };

			if (course.kind == structures::route_rail)
			{
				for (const auto& point : course.path)
				{
					block(point, course.width * 0.5f + baker::town_rail_clear);
				}

				for (const auto& stop : stops)
				{
					block(course.path[std::min<std::size_t>(stop.index, course.path.size() - 1u)], baker::town_station_clear);
				}
			}

			else if (std::any_of(course.path.begin(), course.path.end(), [&](const structures::vec2_s& point) { return inside(point, baker::town_crowd_reach); }))
			{
				stamp(course, index);

				if (std::any_of(course.path.begin(), course.path.end(), [&](const structures::vec2_s& point) { return mathematics.length(point - site.position) < profile.radius; }))
				{
					members.push_back(index);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::block(structures::vec2_s point, std::float_t radius)
	{
		const auto size{ static_cast<std::int32_t>(cells) };
		const auto first_column{ std::max(static_cast<std::int32_t>((point.x - radius - corner.x) / baker::town_cell), 0) };
		const auto last_column{ std::min(static_cast<std::int32_t>((point.x + radius - corner.x) / baker::town_cell) + 1, size - 1) };
		const auto first_row{ std::max(static_cast<std::int32_t>((point.y - radius - corner.y) / baker::town_cell), 0) };
		const auto last_row{ std::min(static_cast<std::int32_t>((point.y + radius - corner.y) / baker::town_cell) + 1, size - 1) };

		for (auto row{ first_row }; row <= last_row; row++)
		{
			for (auto column{ first_column }; column <= last_column; column++)
			{
				if (const auto cell{ row * size + column }; mathematics.length(cell_center(cell) - point) < radius)
				{
					blocked[cell] = 1u;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::stamp(const baker::course_s& course, std::uint32_t index)
	{
		const auto size{ static_cast<std::int32_t>(cells) };

		for (auto point{ 0u }; point + 1u < course.path.size(); point++)
		{
			const auto from{ course.path[point] };
			const auto to{ course.path[point + 1u] };
			const auto span{ to - from };
			const auto squared{ std::max(mathematics.dot(span, span), 0.0001f) };
			const auto first_column{ std::max(static_cast<std::int32_t>((std::min(from.x, to.x) - baker::town_crowd_reach - corner.x) / baker::town_cell), 0) };
			const auto last_column{ std::min(static_cast<std::int32_t>((std::max(from.x, to.x) + baker::town_crowd_reach - corner.x) / baker::town_cell) + 1, size - 1) };
			const auto first_row{ std::max(static_cast<std::int32_t>((std::min(from.y, to.y) - baker::town_crowd_reach - corner.y) / baker::town_cell), 0) };
			const auto last_row{ std::min(static_cast<std::int32_t>((std::max(from.y, to.y) + baker::town_crowd_reach - corner.y) / baker::town_cell) + 1, size - 1) };

			for (auto row{ first_row }; row <= last_row; row++)
			{
				for (auto column{ first_column }; column <= last_column; column++)
				{
					const auto cell{ row * size + column };
					const auto spot{ cell_center(cell) };
					const auto along{ mathematics.saturate(mathematics.dot(spot - from, span) / squared) };

					if (const auto distance{ mathematics.length(spot - (from + span * along)) }; distance < reach[cell])
					{
						reach[cell] = distance;
						owner[cell] = index;
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_towns_c::connect(std::int32_t start, std::int32_t goal, std::uint32_t avoid, std::uint32_t shun, std::vector<structures::vec2_s>& out)
	{
		const auto size{ static_cast<std::int32_t>(cells) };
		const std::int32_t steps[8][2] = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 }, { 1, 1 }, { 1, -1 }, { -1, 1 }, { -1, -1 } };
		const auto later = [](const std::pair<std::float_t, std::int32_t>& a, const std::pair<std::float_t, std::int32_t>& b)
			{
				return a.first > b.first;
			};

		std::vector<std::pair<std::float_t, std::int32_t>> frontier;

		auto found{ -1 };

		out.clear();
		spent.assign(level.size(), FLT_MAX);
		came.assign(level.size(), -1);

		if (start >= 0 && blocked[start] == 0u)
		{
			spent[start] = 0.0f;

			frontier.push_back({ 0.0f, start });
		}

		while (frontier.empty() == false && found < 0)
		{
			std::pop_heap(frontier.begin(), frontier.end(), later);

			const auto [cost, cell]{ frontier.back() };

			frontier.pop_back();

			if (cost <= spent[cell] && cell != start && (goal >= 0 ? cell == goal : reach[cell] <= baker::town_join_reach && owner[cell] != avoid && owner[cell] != shun && owner[cell] != UINT32_MAX))
			{
				found = cell;
			}

			else if (cost <= spent[cell])
			{
				for (const auto& step : steps)
				{
					const auto column{ cell % size + step[0] };
					const auto row{ cell / size + step[1] };
					const auto next{ row * size + column };

					if (column >= 0 && row >= 0 && column < size && row < size && blocked[next] == 0u)
					{
						const auto length{ baker::town_cell * (step[0] && step[1] ? 1.41421f : 1.0f) };
						const auto grade{ std::fabs(level[next] - level[cell]) / length };
						const auto band{ reach[next] > baker::town_join_reach && reach[next] < baker::town_crowd_reach && owner[next] != avoid ? baker::town_crowd_cost * (1.0f - (reach[next] - baker::town_join_reach) / (baker::town_crowd_reach - baker::town_join_reach)) : 0.0f };

						if (const auto total{ cost + length * (1.0f + baker::town_steep_cost * grade * grade + (grade > baker::town_grade_limit ? baker::town_steep_penalty : 0.0f) + band) }; total < spent[next])
						{
							spent[next] = total;
							came[next] = cell;

							frontier.push_back({ total, next });

							std::push_heap(frontier.begin(), frontier.end(), later);
						}
					}
				}
			}
		}

		for (auto cell{ found }; cell >= 0; cell = came[cell])
		{
			out.push_back(cell_center(cell));
		}

		std::reverse(out.begin(), out.end());

		return found >= 0 && out.size() > 1u;
	}
	/*
	//=====================================================================================
	*/
	bool baker_towns_c::lay_street(std::vector<structures::vec2_s> points, std::uint32_t rank, std::float_t width, std::uint32_t start_parent, std::uint32_t end_parent, std::uint32_t landmark, std::vector<baker::course_s>& courses)
	{
		smooth(points);

		if (start_parent != UINT32_MAX)
		{
			trim(points, courses[start_parent]);
		}

		if (end_parent != UINT32_MAX)
		{
			std::reverse(points.begin(), points.end());

			trim(points, courses[end_parent]);

			std::reverse(points.begin(), points.end());
		}

		auto length{ 0.0f };

		for (auto index{ 1u }; index < points.size(); index++)
		{
			length += mathematics.length(points[index] - points[index - 1u]);
		}

		if (points.size() > 2u && length > baker::town_street_minimum)
		{
			const auto lane{ rank > 1u };
			const auto walk{ lane ? 0.0f : (rank == 0u ? town_spine_walk : town_street_walk) };
			const auto index{ static_cast<std::uint32_t>(courses.size()) };

			baker::course_s street{};

			street.kind = structures::route_road;
			street.paving = lane ? structures::track_material_setts : structures::track_material_asphalt;
			street.rank = rank;
			street.landmark = landmark;
			street.parent = start_parent != UINT32_MAX ? start_parent : end_parent;
			street.width = width;
			street.grade = baker::town_street_grade;
			street.smoothing = baker::town_street_smoothing;
			street.slope = baker::town_street_slope;
			street.closed = false;
			street.path = std::move(points);
			street.walks.assign(street.path.size(), walk);
			street.flats.assign(street.path.size(), width * 0.5f + (lane ? town_lane_verge : walk));

			courses.push_back(std::move(street));

			members.push_back(index);

			stamp(courses[index], index);

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::smooth(std::vector<structures::vec2_s>& points)
	{
		std::vector<std::uint8_t> keep(points.size(), 0u);
		std::vector<structures::vec2_s> corners;

		keep.front() = 1u;
		keep.back() = 1u;

		simplify(points, 0u, points.size() - 1u, keep);

		for (auto index{ 0u }; index < points.size(); index++)
		{
			if (keep[index])
			{
				corners.push_back(points[index]);
			}
		}

		for (auto pass{ 0u }; pass < baker::town_smoothing && corners.size() > 2u; pass++)
		{
			std::vector<structures::vec2_s> rounded{ corners.front() };

			for (auto index{ 0u }; index + 1u < corners.size(); index++)
			{
				rounded.push_back(corners[index] * 0.75f + corners[index + 1u] * 0.25f);
				rounded.push_back(corners[index] * 0.25f + corners[index + 1u] * 0.75f);
			}

			rounded.push_back(corners.back());

			corners = std::move(rounded);
		}

		points.assign(1u, corners.front());

		auto carried{ 0.0f };

		for (auto index{ 1u }; index < corners.size(); index++)
		{
			const auto from{ corners[index - 1u] };
			const auto to{ corners[index] };
			const auto length{ mathematics.length(to - from) };

			auto position{ baker::route_spacing - carried };

			for (; position < length; position += baker::route_spacing)
			{
				points.push_back(from + (to - from) * (position / std::max(length, 0.0001f)));
			}

			carried = length - (position - baker::route_spacing);
		}

		if (mathematics.length(points.back() - corners.back()) > baker::route_spacing * 0.3f)
		{
			points.push_back(corners.back());
		}

		else
		{
			points.back() = corners.back();
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::simplify(const std::vector<structures::vec2_s>& points, std::size_t from, std::size_t to, std::vector<std::uint8_t>& keep)
	{
		const auto span{ points[to] - points[from] };
		const auto length{ std::max(mathematics.length(span), 0.0001f) };

		auto worst{ 0.0f };
		auto pick{ from };

		for (auto index{ from + 1u }; index < to; index++)
		{
			const auto offset{ points[index] - points[from] };

			if (const auto distance{ std::fabs(span.x * offset.y - span.y * offset.x) / length }; distance > worst)
			{
				worst = distance;
				pick = index;
			}
		}

		if (worst > baker::town_simplify)
		{
			keep[pick] = 1u;

			simplify(points, from, pick, keep);

			simplify(points, pick, to, keep);
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::trim(std::vector<structures::vec2_s>& points, const baker::course_s& parent)
	{
		const auto edge{ parent.width * 0.5f };

		auto gap{ 0.0f };
		auto index{ 0u };

		nearest(parent, points.front(), gap);

		while (index + 1u < points.size() && gap < edge)
		{
			index++;

			nearest(parent, points[index], gap);
		}

		if (index > 0u && gap >= edge)
		{
			auto inside{ points[index - 1u] };
			auto outside{ points[index] };

			for (auto step{ 0u }; step < 12u; step++)
			{
				const auto middle{ (inside + outside) * 0.5f };

				nearest(parent, middle, gap);

				if (gap < edge)
				{
					inside = middle;
				}

				else
				{
					outside = middle;
				}
			}

			points.erase(points.begin(), points.begin() + index);
			points.insert(points.begin(), outside);
		}
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s baker_towns_c::nearest(const baker::course_s& course, structures::vec2_s point, std::float_t& gap)
	{
		structures::vec2_s best{ course.path.front() };

		gap = mathematics.length(point - best);

		for (auto index{ 0u }; index + 1u < course.path.size(); index++)
		{
			const auto from{ course.path[index] };
			const auto span{ course.path[index + 1u] - from };
			const auto along{ mathematics.saturate(mathematics.dot(point - from, span) / std::max(mathematics.dot(span, span), 0.0001f)) };
			const auto spot{ from + span * along };

			if (const auto distance{ mathematics.length(point - spot) }; distance < gap)
			{
				gap = distance;
				best = spot;
			}
		}

		return best;
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::measure_room(const std::vector<baker::course_s>& courses, const std::vector<structures::station_s>& stops)
	{
		const auto size{ static_cast<std::int32_t>(std::ceil(static_cast<std::float_t>(cells) * baker::town_cell / baker::town_fine_cell)) };
		const auto band{ 14.0f };
		const structures::vec2_s far_corner{ corner.x + static_cast<std::float_t>(size) * baker::town_fine_cell, corner.y + static_cast<std::float_t>(size) * baker::town_fine_cell };

		fine = static_cast<std::uint32_t>(size);

		room.assign(static_cast<std::size_t>(fine) * fine, FLT_MAX);

		for (const auto& course : courses)
		{
			const auto rail{ course.kind == structures::route_rail };

			for (auto point{ 0u }; point + 1u < course.path.size(); point++)
			{
				const auto from{ course.path[point] };
				const auto to{ course.path[point + 1u] };
				const auto edge_from{ course.width * 0.5f + (rail ? baker::town_rail_clear : (course.walks[point] > 0.0f ? course.walks[point] : town_lane_verge)) };
				const auto edge_to{ course.width * 0.5f + (rail ? baker::town_rail_clear : (course.walks[point + 1u] > 0.0f ? course.walks[point + 1u] : town_lane_verge)) };
				const auto span{ to - from };
				const auto squared{ std::max(mathematics.dot(span, span), 0.0001f) };

				if (std::max(from.x, to.x) + band > corner.x && std::min(from.x, to.x) - band < far_corner.x && std::max(from.y, to.y) + band > corner.y && std::min(from.y, to.y) - band < far_corner.y)
				{
					const auto first_column{ std::max(static_cast<std::int32_t>((std::min(from.x, to.x) - band - corner.x) / baker::town_fine_cell), 0) };
					const auto last_column{ std::min(static_cast<std::int32_t>((std::max(from.x, to.x) + band - corner.x) / baker::town_fine_cell) + 1, size - 1) };
					const auto first_row{ std::max(static_cast<std::int32_t>((std::min(from.y, to.y) - band - corner.y) / baker::town_fine_cell), 0) };
					const auto last_row{ std::min(static_cast<std::int32_t>((std::max(from.y, to.y) + band - corner.y) / baker::town_fine_cell) + 1, size - 1) };

					for (auto row{ first_row }; row <= last_row; row++)
					{
						for (auto column{ first_column }; column <= last_column; column++)
						{
							const structures::vec2_s spot{ corner.x + (static_cast<std::float_t>(column) + 0.5f) * baker::town_fine_cell, corner.y + (static_cast<std::float_t>(row) + 0.5f) * baker::town_fine_cell };
							const auto along{ mathematics.saturate(mathematics.dot(spot - from, span) / squared) };
							const auto clearance{ mathematics.length(spot - (from + span * along)) - mathematics.lerp(edge_from, edge_to, along) };
							auto& value{ room[static_cast<std::size_t>(row) * fine + static_cast<std::size_t>(column)] };

							value = std::min(value, clearance);
						}
					}
				}
			}

			for (const auto& stop : stops)
			{
				const auto station{ course.path[std::min<std::size_t>(stop.index, course.path.size() - 1u)] };

				for (auto row{ 0 }; rail && row < size; row++)
				{
					for (auto column{ 0 }; column < size; column++)
					{
						const structures::vec2_s spot{ corner.x + (static_cast<std::float_t>(column) + 0.5f) * baker::town_fine_cell, corner.y + (static_cast<std::float_t>(row) + 0.5f) * baker::town_fine_cell };
						auto& value{ room[static_cast<std::size_t>(row) * fine + static_cast<std::size_t>(column)] };

						value = std::min(value, mathematics.length(spot - station) - baker::town_station_clear);
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::front(const std::vector<baker::course_s>& courses)
	{
		frontages.clear();

		for (const auto index : members)
		{
			const auto& course{ courses[index] };

			for (auto side{ -1.0f }; side < 2.0f; side += 2.0f)
			{
				baker::frontage_s frontage{};

				frontage.course = index;
				frontage.side = side;

				for (auto point{ 0u }; point < course.path.size(); point++)
				{
					const auto& previous{ course.path[point ? point - 1u : 0u] };
					const auto& next{ course.path[std::min<std::size_t>(point + 1u, course.path.size() - 1u)] };
					const auto tangent{ mathematics.normalize(next - previous) };
					const structures::vec2_s away{ -tangent.y * side, tangent.x * side };
					const auto setback{ course.width * 0.5f + town_plot_setback + (course.walks[point] > 0.0f ? course.walks[point] : town_lane_verge) };

					frontage.points.push_back(course.path[point] + away * setback);
					frontage.aways.push_back(away);
					frontage.arcs.push_back(point ? frontage.arcs.back() + mathematics.length(frontage.points[point] - frontage.points[point - 1u]) : 0.0f);
				}

				frontages.push_back(std::move(frontage));
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::parcel(const structures::town_profile_s& profile, const structures::world_site_s& site, const std::vector<baker::course_s>& courses)
	{
		std::vector<baker::opening_s> central;
		std::vector<baker::opening_s> outer;

		front(courses);

		for (auto index{ 0u }; index < frontages.size(); index++)
		{
			const auto& frontage{ frontages[index] };

			for (auto arc{ 0.0f }; courses[frontage.course].rank < 2u && arc < frontage.arcs.back(); arc += 2.0f)
			{
				const auto distance{ mathematics.length(along_at(frontage, arc) - site.position) };

				central.push_back({ distance, index, arc });
				outer.push_back({ std::fabs(distance - profile.radius * 0.8f), index, arc });
			}
		}

		std::sort(central.begin(), central.end(), [](const baker::opening_s& a, const baker::opening_s& b) { return a.distance < b.distance; });
		std::sort(outer.begin(), outer.end(), [](const baker::opening_s& a, const baker::opening_s& b) { return a.distance < b.distance; });

		for (const auto& special : town_specials)
		{
			for (auto count{ 0u }; special.style == profile.style && count < special.count; count++)
			{
				const auto& openings{ special.outskirts ? outer : central };

				auto placed{ false };

				for (auto index{ 0u }; index < openings.size() && placed == false; index++)
				{
					placed = place(frontages[openings[index].frontage], openings[index].arc, special.role, town_buildings[special.role].size, profile.landmark, site, profile.radius);
				}
			}
		}

		for (const auto& frontage : frontages)
		{
			const auto rank{ courses[frontage.course].rank };

			auto previous{ static_cast<std::uint32_t>(structures::town_building_count) };
			auto arc{ 0.0f };

			while (arc < frontage.arcs.back())
			{
				const auto distance{ mathematics.length(along_at(frontage, arc) - site.position) / profile.radius };
				const auto zone{ std::min((distance < profile.core ? 0u : (distance > 0.78f ? 2u : 1u)) + (rank > 1u ? 1u : 0u), 2u) };
				const auto attached{ previous == structures::town_terrace || previous == structures::town_shop };
				const auto role{ attached && zone < 2u && random() < baker::town_attached_chance ? previous : pick(profile.style, zone) };
				const auto garden{ role == structures::town_home || role == structures::town_cottage || role == structures::town_house };
				const auto rural{ role == structures::town_barn || role == structures::town_shed };
				const auto joined{ attached && role == previous };
				const structures::vec2_s size{ town_buildings[role].size.x + (garden ? random() * 3.0f : 0.0f), town_buildings[role].size.y + (garden ? 2.0f + random() * 6.0f : 0.0f) };
				const auto start{ arc + (joined ? 0.0f : baker::town_plot_gap + random() * (garden || rural ? 4.0f : 1.0f)) };

				if (place(frontage, start, role, size, profile.landmark, site, profile.radius))
				{
					arc = start + size.x;
					previous = role;
				}

				else
				{
					arc += baker::town_plot_step;
					previous = structures::town_building_count;
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_towns_c::place(const baker::frontage_s& frontage, std::float_t arc, std::uint32_t role, structures::vec2_s size, std::uint32_t landmark, const structures::world_site_s& site, std::float_t radius)
	{
		if (arc + size.x < frontage.arcs.back())
		{
			const auto from{ along_at(frontage, arc) };
			const auto to{ along_at(frontage, arc + size.x) };
			const auto along{ mathematics.normalize(to - from) };
			const structures::vec2_s away{ -along.y * frontage.side, along.x * frontage.side };

			auto bulge{ 0.0f };

			for (auto index{ 0u }; index < frontage.points.size(); index++)
			{
				if (frontage.arcs[index] > arc && frontage.arcs[index] < arc + size.x)
				{
					bulge = std::max(bulge, mathematics.dot(frontage.points[index] - from, away));
				}
			}

			const structures::town_plot_s plot{ (from + to) * 0.5f + away * bulge, size, std::atan2(away.x, away.y), 0.0f, role, landmark };

			if (fits(plot, site, radius))
			{
				plots.push_back(plot);

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool baker_towns_c::fits(const structures::town_plot_s& plot, const structures::world_site_s& site, std::float_t radius)
	{
		const structures::vec2_s away{ std::sin(plot.yaw), std::cos(plot.yaw) };
		const structures::vec2_s across{ away.y, -away.x };
		const auto columns{ std::max(2u, static_cast<std::uint32_t>(std::ceil(plot.size.x / 2.0f))) };
		const auto rows{ std::max(2u, static_cast<std::uint32_t>(std::ceil(plot.size.y / 2.0f))) };

		auto lowest{ FLT_MAX };
		auto highest{ -FLT_MAX };
		auto clear{ true };

		for (auto row{ 0u }; row <= rows && clear; row++)
		{
			for (auto column{ 0u }; column <= columns && clear; column++)
			{
				const auto spot{ plot.position + across * ((static_cast<std::float_t>(column) / static_cast<std::float_t>(columns) - 0.5f) * plot.size.x) + away * (static_cast<std::float_t>(row) / static_cast<std::float_t>(rows) * plot.size.y) };
				const auto ground{ baker_terrain.height_at(spot.x, spot.y) };

				lowest = std::min(lowest, ground);
				highest = std::max(highest, ground);

				clear = room_at(spot) > baker::town_plot_clearance && mathematics.length(spot - site.position) < radius + 4.0f;
			}
		}

		clear = clear && lowest > sea_level + baker::town_ground_floor && highest - lowest < baker::town_plot_relief;

		for (auto index{ first_plot }; index < plots.size() && clear; index++)
		{
			clear = overlaps(plot, plots[index]) == false;
		}

		return clear;
	}
	/*
	//=====================================================================================
	*/
	bool baker_towns_c::overlaps(const structures::town_plot_s& a, const structures::town_plot_s& b)
	{
		const structures::vec2_s away_a{ std::sin(a.yaw), std::cos(a.yaw) };
		const structures::vec2_s away_b{ std::sin(b.yaw), std::cos(b.yaw) };
		const structures::vec2_s across_a{ away_a.y, -away_a.x };
		const structures::vec2_s across_b{ away_b.y, -away_b.x };
		const auto offset{ (b.position + away_b * (b.size.y * 0.5f)) - (a.position + away_a * (a.size.y * 0.5f)) };
		const structures::vec2_s axes[4] = { away_a, across_a, away_b, across_b };

		auto touching{ true };

		for (const auto& axis : axes)
		{
			const auto extent_a{ a.size.x * 0.5f * std::fabs(mathematics.dot(across_a, axis)) + a.size.y * 0.5f * std::fabs(mathematics.dot(away_a, axis)) };
			const auto extent_b{ b.size.x * 0.5f * std::fabs(mathematics.dot(across_b, axis)) + b.size.y * 0.5f * std::fabs(mathematics.dot(away_b, axis)) };

			touching = touching && std::fabs(mathematics.dot(offset, axis)) < extent_a + extent_b + baker::town_plot_gap * 0.5f - 0.05f;
		}

		return touching;
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s baker_towns_c::along_at(const baker::frontage_s& frontage, std::float_t arc)
	{
		const auto upper{ static_cast<std::size_t>(std::upper_bound(frontage.arcs.begin(), frontage.arcs.end(), arc) - frontage.arcs.begin()) };
		const auto next{ std::clamp<std::size_t>(upper, 1u, frontage.arcs.size() - 1u) };
		const auto span{ std::max(frontage.arcs[next] - frontage.arcs[next - 1u], 0.0001f) };

		return frontage.points[next - 1u] + (frontage.points[next] - frontage.points[next - 1u]) * mathematics.saturate((arc - frontage.arcs[next - 1u]) / span);
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t baker_towns_c::pick(std::uint32_t style, std::uint32_t zone)
	{
		auto total{ 0.0f };

		for (const auto& mix : town_mixes)
		{
			total += mix.style == style && mix.zone == zone ? mix.weight : 0.0f;
		}

		auto left{ random() * total };

		for (const auto& mix : town_mixes)
		{
			if (mix.style == style && mix.zone == zone && left < mix.weight)
			{
				return mix.role;
			}

			left -= mix.style == style && mix.zone == zone ? mix.weight : 0.0f;
		}

		return structures::town_home;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_towns_c::room_at(structures::vec2_s point)
	{
		const auto fx{ (point.x - corner.x) / baker::town_fine_cell - 0.5f };
		const auto fz{ (point.y - corner.y) / baker::town_fine_cell - 0.5f };

		if (fx >= 0.0f && fz >= 0.0f && fx < static_cast<std::float_t>(fine) - 1.001f && fz < static_cast<std::float_t>(fine) - 1.001f)
		{
			const auto column{ static_cast<std::size_t>(fx) };
			const auto row{ static_cast<std::size_t>(fz) };
			const auto tx{ fx - static_cast<std::float_t>(column) };
			const auto tz{ fz - static_cast<std::float_t>(row) };
			const auto cell{ row * fine + column };

			return mathematics.lerp(mathematics.lerp(room[cell], room[cell + 1u], tx), mathematics.lerp(room[cell + fine], room[cell + fine + 1u], tx), tz);
		}

		return -1.0f;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_towns_c::walk_at(structures::vec2_s point)
	{
		for (const auto& profile : town_profiles)
		{
			for (const auto& site : world_sites)
			{
				if (site.landmark == profile.landmark && mathematics.length(point - site.position) < profile.radius - 6.0f)
				{
					return town_spine_walk;
				}
			}
		}

		return 0.0f;
	}
	/*
	//=====================================================================================
	*/
	bool baker_towns_c::planned(std::uint32_t landmark)
	{
		return std::any_of(std::begin(town_profiles), std::end(town_profiles), [&](const structures::town_profile_s& profile) { return profile.landmark == landmark; });
	}
	/*
	//=====================================================================================
	*/
	bool baker_towns_c::inside(structures::vec2_s point, std::float_t margin)
	{
		const auto span{ static_cast<std::float_t>(cells) * baker::town_cell };

		return point.x > corner.x - margin && point.y > corner.y - margin && point.x < corner.x + span + margin && point.y < corner.y + span + margin;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_towns_c::random()
	{
		state ^= state << 13u;
		state ^= state >> 17u;
		state ^= state << 5u;

		return static_cast<std::float_t>(state & 0xFFFFFFu) / 16777216.0f;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t baker_towns_c::cell_at(structures::vec2_s point)
	{
		const auto column{ static_cast<std::int32_t>(std::floor((point.x - corner.x) / baker::town_cell)) };
		const auto row{ static_cast<std::int32_t>(std::floor((point.y - corner.y) / baker::town_cell)) };

		return column >= 0 && row >= 0 && column < static_cast<std::int32_t>(cells) && row < static_cast<std::int32_t>(cells) ? row * static_cast<std::int32_t>(cells) + column : -1;
	}
	/*
	//=====================================================================================
	*/
	structures::vec2_s baker_towns_c::cell_center(std::int32_t cell)
	{
		return { corner.x + (static_cast<std::float_t>(cell % static_cast<std::int32_t>(cells)) + 0.5f) * baker::town_cell, corner.y + (static_cast<std::float_t>(cell / static_cast<std::int32_t>(cells)) + 0.5f) * baker::town_cell };
	}
	/*
	//=====================================================================================
	*/
	void baker_towns_c::preview(const std::string& path, const structures::town_profile_s& profile, const structures::world_site_s& site, const std::vector<baker::course_s>& courses)
	{
		const auto size{ static_cast<std::uint32_t>(static_cast<std::float_t>(cells) * baker::town_cell * baker::town_preview_scale) };
		const auto meter{ 1.0f / baker::town_preview_scale };

		std::vector<std::uint8_t> pixels(static_cast<std::size_t>(size) * size * 4u, 255u);

		const auto paint = [&](std::int32_t x, std::int32_t y, structures::vec3_s color)
			{
				if (x >= 0 && y >= 0 && x < static_cast<std::int32_t>(size) && y < static_cast<std::int32_t>(size))
				{
					const auto texel{ (static_cast<std::size_t>(size - 1u - static_cast<std::uint32_t>(y)) * size + static_cast<std::size_t>(x)) * 4u };

					pixels[texel + 0u] = static_cast<std::uint8_t>(std::clamp(color.x * 255.0f, 0.0f, 255.0f));
					pixels[texel + 1u] = static_cast<std::uint8_t>(std::clamp(color.y * 255.0f, 0.0f, 255.0f));
					pixels[texel + 2u] = static_cast<std::uint8_t>(std::clamp(color.z * 255.0f, 0.0f, 255.0f));
				}
			};

		const auto disc = [&](structures::vec2_s point, std::float_t radius, structures::vec3_s color)
			{
				const auto px{ static_cast<std::int32_t>((point.x - corner.x) * baker::town_preview_scale) };
				const auto py{ static_cast<std::int32_t>((point.y - corner.y) * baker::town_preview_scale) };
				const auto span{ static_cast<std::int32_t>(std::ceil(radius * baker::town_preview_scale)) };

				for (auto dy{ -span }; dy <= span; dy++)
				{
					for (auto dx{ -span }; dx <= span; dx++)
					{
						if (static_cast<std::float_t>(dx * dx + dy * dy) <= radius * radius * baker::town_preview_scale * baker::town_preview_scale)
						{
							paint(px + dx, py + dy, color);
						}
					}
				}
			};

		jobs.parallel_for(size, [&](std::uint32_t row)
			{
				for (auto column{ 0u }; column < size; column++)
				{
					const auto x{ corner.x + (static_cast<std::float_t>(column) + 0.5f) * meter };
					const auto z{ corner.y + (static_cast<std::float_t>(row) + 0.5f) * meter };
					const auto ground{ baker_terrain.height_at(x, z) };
					const auto light{ mathematics.saturate(0.62f + (baker_terrain.height_at(x - 1.0f, z) - baker_terrain.height_at(x + 1.0f, z) + baker_terrain.height_at(x, z - 1.0f) - baker_terrain.height_at(x, z + 1.0f)) * 0.35f) };
					const auto tone{ mathematics.saturate((ground + 10.0f) / 120.0f) };
					const auto color{ ground < sea_level ? structures::vec3_s{ 0.18f, 0.34f, 0.5f } : structures::vec3_s{ 0.42f + 0.3f * tone, 0.52f + 0.2f * tone, 0.32f + 0.2f * tone } * light };

					paint(static_cast<std::int32_t>(column), static_cast<std::int32_t>(row), color);
				}
			});

		for (const auto index : members)
		{
			const auto& course{ courses[index] };

			for (auto point{ 0u }; point < course.path.size(); point++)
			{
				disc(course.path[point], course.width * 0.5f + course.walks[point], { 0.78f, 0.77f, 0.74f });
			}
		}

		for (const auto index : members)
		{
			const auto& course{ courses[index] };

			for (const auto& point : course.path)
			{
				disc(point, course.width * 0.5f, course.paving == structures::track_material_setts ? structures::vec3_s{ 0.5f, 0.44f, 0.38f } : structures::vec3_s{ 0.22f, 0.22f, 0.24f });
			}
		}

		for (const auto& stop : baker_terrain.stops)
		{
			for (const auto& course : courses)
			{
				if (course.kind == structures::route_rail)
				{
					disc(course.path[std::min<std::size_t>(stop.index, course.path.size() - 1u)], 3.0f, { 0.9f, 0.1f, 0.1f });
				}
			}
		}

		for (const auto& course : courses)
		{
			for (auto point{ 0u }; course.kind == structures::route_rail && point < course.path.size(); point++)
			{
				disc(course.path[point], 1.6f, { 0.35f, 0.25f, 0.2f });
			}
		}

		for (auto index{ first_plot }; index < plots.size(); index++)
		{
			const auto& plot{ plots[index] };
			const structures::vec2_s away{ std::sin(plot.yaw), std::cos(plot.yaw) };
			const structures::vec2_s across{ away.y, -away.x };
			const auto color{ baker::town_role_colors[plot.role] };
			const auto reach_out{ std::max(plot.size.x, plot.size.y) + 2.0f };

			for (auto dy{ -reach_out }; dy <= reach_out; dy += meter)
			{
				for (auto dx{ -reach_out }; dx <= reach_out; dx += meter)
				{
					const structures::vec2_s spot{ plot.position.x + dx, plot.position.y + dy };
					const auto u{ mathematics.dot(spot - plot.position, across) };
					const auto v{ mathematics.dot(spot - plot.position, away) };

					if (std::fabs(u) <= plot.size.x * 0.5f && v >= 0.0f && v <= plot.size.y)
					{
						const auto rim{ std::fabs(u) > plot.size.x * 0.5f - meter * 1.5f || v < meter * 1.5f || v > plot.size.y - meter * 1.5f };
						const auto front_edge{ v < meter * 2.5f };

						paint(static_cast<std::int32_t>((spot.x - corner.x) * baker::town_preview_scale), static_cast<std::int32_t>((spot.y - corner.y) * baker::town_preview_scale), front_edge ? structures::vec3_s{ 0.1f, 0.1f, 0.1f } : (rim ? color * 0.55f : color));
					}
				}
			}
		}

		disc(site.position, 3.0f, { 1.0f, 0.1f, 0.1f });

		baker_images.save_png(path.c_str(), pixels.data(), size, size, nullptr);
	}
}

//=====================================================================================
