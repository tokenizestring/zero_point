
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	marks_c marks;

	void marks_c::clear()
	{
		ring.assign(mark_capacity, {});
		heads.assign(static_cast<std::size_t>(mark_cells) * mark_cells, -1);
		fresh.clear();

		cursor = 0u;
		sweep = 0u;
		count = 0u;
	}
	/*
	//=====================================================================================
	*/
	std::double_t marks_c::now()
	{
		return server.running ? server.clock : (client.connected() ? client.server_clock : train.clock);
	}
	/*
	//=====================================================================================
	*/
	std::uint16_t marks_c::cell_of(structures::vec3_s position)
	{
		const auto limit{ static_cast<std::int32_t>(mark_cells) - 1 };
		const auto column{ std::clamp(static_cast<std::int32_t>(std::floor((position.x - terrain_origin) / mark_cell)), 0, limit) };
		const auto row{ std::clamp(static_cast<std::int32_t>(std::floor((position.z - terrain_origin) / mark_cell)), 0, limit) };

		return static_cast<std::uint16_t>(row * static_cast<std::int32_t>(mark_cells) + column);
	}
	/*
	//=====================================================================================
	*/
	std::uint16_t marks_c::pack(structures::vec3_s normal)
	{
		const auto sum{ std::max(std::fabs(normal.x) + std::fabs(normal.y) + std::fabs(normal.z), 0.0001f) };
		const auto u{ normal.x / sum };
		const auto v{ normal.z / sum };
		const auto folded_u{ normal.y >= 0.0f ? u : (1.0f - std::fabs(v)) * (u >= 0.0f ? 1.0f : -1.0f) };
		const auto folded_v{ normal.y >= 0.0f ? v : (1.0f - std::fabs(u)) * (v >= 0.0f ? 1.0f : -1.0f) };
		const auto first{ static_cast<std::uint32_t>(std::clamp(std::round(folded_u * 127.0f), -127.0f, 127.0f) + 127.0f) };
		const auto second{ static_cast<std::uint32_t>(std::clamp(std::round(folded_v * 127.0f), -127.0f, 127.0f) + 127.0f) };

		return static_cast<std::uint16_t>(first | (second << 8u));
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s marks_c::unpack(std::uint16_t packed)
	{
		const auto u{ (static_cast<std::float_t>(packed & 0xFFu) - 127.0f) / 127.0f };
		const auto v{ (static_cast<std::float_t>(packed >> 8u) - 127.0f) / 127.0f };
		const auto height{ 1.0f - std::fabs(u) - std::fabs(v) };
		const auto fold{ std::max(-height, 0.0f) };

		return mathematics.normalize({ u + (u >= 0.0f ? -fold : fold), height, v + (v >= 0.0f ? -fold : fold) });
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s marks_c::frame(structures::vec3_s normal, std::uint8_t spin)
	{
		const auto first{ mathematics.normalize(mathematics.cross(normal, std::fabs(normal.y) > 0.9f ? structures::vec3_s{ 1.0f, 0.0f, 0.0f } : structures::vec3_s{ 0.0f, 1.0f, 0.0f })) };
		const auto second{ mathematics.cross(normal, first) };
		const auto angle{ static_cast<std::float_t>(spin) / 256.0f * two_pi };

		return first * std::cos(angle) + second * std::sin(angle);
	}
	/*
	//=====================================================================================
	*/
	std::uint8_t marks_c::aim(structures::vec3_s normal, structures::vec3_s toward)
	{
		const auto first{ mathematics.normalize(mathematics.cross(normal, std::fabs(normal.y) > 0.9f ? structures::vec3_s{ 1.0f, 0.0f, 0.0f } : structures::vec3_s{ 0.0f, 1.0f, 0.0f })) };
		const auto second{ mathematics.cross(normal, first) };
		const auto flat{ toward - normal * mathematics.dot(toward, normal) };
		const auto axis{ mathematics.length(flat) > 0.05f ? mathematics.normalize(flat) * -1.0f : first };

		return static_cast<std::uint8_t>(static_cast<std::int32_t>(std::round(std::atan2(mathematics.dot(axis, second), mathematics.dot(axis, first)) / two_pi * 256.0f)) & 255);
	}
	/*
	//=====================================================================================
	*/
	std::int32_t marks_c::add(std::uint32_t kind, std::uint32_t variant, structures::vec3_s position, structures::vec3_s normal, std::uint8_t spin, std::uint8_t scale, std::double_t born, bool guessed)
	{
		auto result{ -1 };

		if (kind < structures::mark_count && ring.size())
		{
			const auto& definition{ mark_definitions[kind] };
			const auto slot{ static_cast<std::int32_t>(cursor) };

			cursor = (cursor + 1u) % static_cast<std::uint32_t>(ring.size());

			remove(slot);

			auto& mark{ ring[slot] };

			mark.position = position;
			mark.normal = normal;
			mark.axis = frame(normal, spin);
			mark.size = definition.size * (1.0f - definition.vary + 2.0f * definition.vary * static_cast<std::float_t>(scale) / 255.0f);
			mark.born = born;
			mark.cell = cell_of(position);
			mark.kind = static_cast<std::uint8_t>(kind);
			mark.variant = static_cast<std::uint8_t>(variant % std::max(definition.variants, 1u));
			mark.spin = spin;
			mark.scale = scale;
			mark.live = true;
			mark.guessed = guessed;
			mark.previous = -1;
			mark.next = heads[mark.cell];

			if (mark.next >= 0)
			{
				ring[mark.next].previous = slot;
			}

			heads[mark.cell] = slot;

			count++;

			if (server.running)
			{
				fresh.push_back(slot);
			}

			result = slot;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void marks_c::remove(std::int32_t index)
	{
		if (index >= 0 && index < static_cast<std::int32_t>(ring.size()) && ring[index].live)
		{
			auto& mark{ ring[index] };

			if (mark.previous >= 0)
			{
				ring[mark.previous].next = mark.next;
			}

			else
			{
				heads[mark.cell] = mark.next;
			}

			if (mark.next >= 0)
			{
				ring[mark.next].previous = mark.previous;
			}

			mark.live = false;

			count--;
		}
	}
	/*
	//=====================================================================================
	*/
	void marks_c::wipe(std::uint16_t cell)
	{
		auto index{ cell < heads.size() ? heads[cell] : -1 };

		while (index >= 0)
		{
			const auto following{ ring[index].next };

			if (ring[index].guessed == false)
			{
				remove(index);
			}

			index = following;
		}
	}
	/*
	//=====================================================================================
	*/
	void marks_c::expire()
	{
		const auto clock{ now() };

		for (auto step{ 0u }; step < mark_sweep && ring.size(); step++)
		{
			sweep = (sweep + 1u) % static_cast<std::uint32_t>(ring.size());

			if (const auto& mark{ ring[sweep] }; mark.live)
			{
				const auto age{ clock - mark.born };
				const auto life{ static_cast<std::double_t>(mark_definitions[mark.kind].life) };

				if ((life > 0.0 && age > life) || (mark.guessed && age > mark_guess_life))
				{
					remove(static_cast<std::int32_t>(sweep));
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void marks_c::impact(const structures::trace_s& hit, structures::vec3_s direction, std::float_t power, bool guessed)
	{
		if (hit.hit && hit.start_solid == false && hit.brush < mover_brush_base && hit.surface < structures::surface_count && surface_marks[hit.surface] < structures::mark_count)
		{
			const auto kind{ surface_marks[hit.surface] };
			const auto normal{ unpack(pack(hit.normal)) };
			const auto mixed{ mathematics.hash_u32(static_cast<std::uint32_t>(static_cast<std::int32_t>(hit.end.x * 97.0f)) * 73856093u ^ static_cast<std::uint32_t>(static_cast<std::int32_t>(hit.end.y * 97.0f)) * 19349663u ^ static_cast<std::uint32_t>(static_cast<std::int32_t>(hit.end.z * 97.0f)) * 83492791u) };
			const auto strength{ mathematics.saturate(power / mark_power_full) };
			const auto scale{ static_cast<std::uint8_t>(std::clamp(50.0f + 160.0f * strength + static_cast<std::float_t>((mixed >> 16u) & 63u) - 32.0f, 0.0f, 255.0f)) };
			const auto upright{ kind == structures::mark_wood && std::fabs(normal.y) < 0.7f };
			const auto spin{ upright ? static_cast<std::uint8_t>(aim(normal, { 0.0f, 1.0f, 0.0f }) + ((mixed >> 8u) & 7u) - 4u) : static_cast<std::uint8_t>((mixed >> 8u) & 255u) };

			add(kind, mixed & 7u, hit.end, normal, spin, scale, now(), guessed);
		}
	}
	/*
	//=====================================================================================
	*/
	void marks_c::bleed(structures::vec3_s point, structures::vec3_s direction)
	{
		const auto behind{ world.trace(point + direction * mark_blood_exit, point + direction * mark_blood_reach, { 0.01f, 0.01f, 0.01f }, structures::contents_solid) };

		if (behind.hit && behind.start_solid == false && behind.brush < mover_brush_base)
		{
			const auto normal{ unpack(pack(behind.normal)) };
			const auto slide{ direction - normal * mathematics.dot(direction, normal) };

			add(structures::mark_blood_spatter, roll(), behind.end, normal, aim(normal, mathematics.length(slide) > 0.35f ? slide : structures::vec3_s{ 0.0f, -1.0f, 0.0f }), roll(), now(), false);
		}

		for (auto drop{ 0u }; drop < 2u; drop++)
		{
			const auto from{ point + structures::vec3_s{ (random() - 0.5f) * 2.0f * mark_blood_scatter, 0.0f, (random() - 0.5f) * 2.0f * mark_blood_scatter } };
			const auto below{ world.trace(from, from - structures::vec3_s{ 0.0f, mark_blood_drop, 0.0f }, { 0.01f, 0.01f, 0.01f }, structures::contents_solid) };

			if (below.hit && below.start_solid == false && below.brush < mover_brush_base && (drop == 0u || random() < 0.5f))
			{
				add(structures::mark_blood_drip, roll(), below.end, unpack(pack(below.normal)), roll(), roll(), now(), false);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void marks_c::pool(structures::vec3_s position)
	{
		const auto below{ world.trace(position + structures::vec3_s{ 0.0f, 0.6f, 0.0f }, position - structures::vec3_s{ 0.0f, 1.5f, 0.0f }, { 0.01f, 0.01f, 0.01f }, structures::contents_solid) };

		if (below.hit && below.start_solid == false && below.brush < mover_brush_base)
		{
			add(structures::mark_blood_pool, roll(), below.end, unpack(pack(below.normal)), roll(), roll(), now(), false);
		}
	}
	/*
	//=====================================================================================
	*/
	void marks_c::tread(const structures::movement_state_s& state, structures::tread_s& tread)
	{
		const auto speed{ mathematics.length(structures::vec3_s{ state.velocity.x, 0.0f, state.velocity.z }) };

		tread.stride = std::min(tread.stride, state.stride);

		if ((state.flags & structures::movement_on_ground) && state.platform == 0u && speed > mark_tread_speed && state.stride - tread.stride >= step_length_base + step_length_scale * speed)
		{
			const auto left{ (tread.steps & 1u) != 0u };
			const auto layer{ state.ground < 0 && terrain.enabled ? std::min(terrain.ground(state.position.x, state.position.z), terrain_layer_count - 1u) : terrain_layer_count };
			const auto soft{ layer < terrain_layer_count ? layer_prints[layer] : static_cast<std::uint32_t>(structures::mark_count) };
			const auto hard{ state.ground_surface < structures::surface_count && surface_hard[state.ground_surface] };
			const auto wading{ state.water_depth > 0.03f };
			const auto kind{ wading ? static_cast<std::uint32_t>(structures::mark_count) : (soft < structures::mark_count ? soft : (tread.wet && hard ? static_cast<std::uint32_t>(structures::mark_print_wet) : static_cast<std::uint32_t>(structures::mark_count))) };

			tread.stride = state.stride;
			tread.steps++;
			tread.wet = wading || layer == structures::layer_marsh ? mark_wet_steps : (tread.wet ? tread.wet - 1u : 0u);

			if (kind < structures::mark_count && state.ground_normal.y > mark_tread_slope)
			{
				const auto turn{ mathematics.angle_difference(state.yaw, std::atan2(state.velocity.x, state.velocity.z)) };
				const auto lean{ std::fabs(turn) > half_pi ? turn - std::copysign(pi, turn) : turn };
				const auto heading{ mathematics.flat_forward(state.yaw + lean * mark_foot_follow) };
				const auto side{ structures::vec3_s{ heading.z, 0.0f, -heading.x } * (left ? -mark_foot_offset : mark_foot_offset) };
				const auto normal{ unpack(pack(state.ground_normal)) };
				const auto drop{ (state.ground_normal.x * side.x + state.ground_normal.z * side.z) / state.ground_normal.y };

				add(kind, left ? 0u : 1u, state.position + side - structures::vec3_s{ 0.0f, drop, 0.0f }, normal, aim(normal, heading), 128u, now(), false);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void marks_c::write(stream_writer_c& writer, const structures::mark_s& mark)
	{
		const auto x{ static_cast<std::uint32_t>(std::clamp((mark.position.x - terrain_origin) * mark_plane_scale, 0.0f, 16777215.0f)) };
		const auto z{ static_cast<std::uint32_t>(std::clamp((mark.position.z - terrain_origin) * mark_plane_scale, 0.0f, 16777215.0f)) };

		writer.u16(static_cast<std::uint16_t>(x & 0xFFFFu));
		writer.u8(static_cast<std::uint8_t>(x >> 16u));
		writer.u16(static_cast<std::uint16_t>(z & 0xFFFFu));
		writer.u8(static_cast<std::uint8_t>(z >> 16u));
		writer.u16(static_cast<std::uint16_t>(std::clamp((mark.position.y - mark_height_floor) * mark_height_scale, 0.0f, 65535.0f)));
		writer.u16(pack(mark.normal));
		writer.u8(static_cast<std::uint8_t>(mark.kind | (mark.variant << 5u)));
		writer.u8(mark.spin);
		writer.u8(mark.scale);
		writer.u8(static_cast<std::uint8_t>(std::clamp((now() - mark.born) / mark_age_step, 0.0, 255.0)));
	}
	/*
	//=====================================================================================
	*/
	void marks_c::receive(stream_reader_c& reader)
	{
		const auto flags{ reader.u8() };
		const auto cell{ reader.u16() };
		const auto total{ static_cast<std::uint32_t>(reader.u8()) };
		const auto clock{ now() };

		if (reader.overflow == false && (flags & 1u) != 0u)
		{
			wipe(cell);
		}

		for (auto entry{ 0u }; entry < total && reader.overflow == false && heads.size(); entry++)
		{
			const auto x_low{ static_cast<std::uint32_t>(reader.u16()) };
			const auto x{ x_low | (static_cast<std::uint32_t>(reader.u8()) << 16u) };
			const auto z_low{ static_cast<std::uint32_t>(reader.u16()) };
			const auto z{ z_low | (static_cast<std::uint32_t>(reader.u8()) << 16u) };
			const auto y{ reader.u16() };
			const auto normal{ unpack(reader.u16()) };
			const auto packed{ static_cast<std::uint32_t>(reader.u8()) };
			const auto spin{ reader.u8() };
			const auto scale{ reader.u8() };
			const auto age{ static_cast<std::double_t>(reader.u8()) * mark_age_step };
			const auto kind{ packed & 31u };
			const structures::vec3_s position{ terrain_origin + static_cast<std::float_t>(x) / mark_plane_scale, mark_height_floor + static_cast<std::float_t>(y) / mark_height_scale, terrain_origin + static_cast<std::float_t>(z) / mark_plane_scale };

			if (reader.overflow == false && kind < structures::mark_count)
			{
				auto twin{ -1 };

				for (auto other{ heads[cell_of(position)] }; other >= 0 && twin < 0; other = ring[other].next)
				{
					twin = ring[other].kind == kind && mathematics.distance(ring[other].position, position) < (ring[other].guessed ? mark_guess_reach : 0.004f) ? other : twin;
				}

				if (twin >= 0)
				{
					ring[twin].guessed = false;
				}

				else
				{
					add(kind, packed >> 5u, position, normal, spin, scale, clock - age, false);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint8_t marks_c::roll()
	{
		return static_cast<std::uint8_t>(random() * 255.0f);
	}
	/*
	//=====================================================================================
	*/
	std::float_t marks_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
