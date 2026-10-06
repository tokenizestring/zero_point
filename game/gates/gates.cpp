
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	gates_c gates;

	void gates_c::create()
	{
		clear();

		char far_name[64]{};

		std::snprintf(far_name, sizeof(far_name), "%s_far", crossing_gate_model);

		if (const auto model{ models.find(crossing_gate_model) }; model && gpu.device)
		{
			length = std::max(model->bounds_max.x, 0.5f);

			shop.clear();
			shop.append(*model, 0u, static_cast<std::uint32_t>(model->indices.size()), mathematics.identity());
			shop.upload(leaf);

			if (const auto far_model{ models.find(far_name) }; far_model)
			{
				shop.clear();
				shop.append(*far_model, 0u, static_cast<std::uint32_t>(far_model->indices.size()), mathematics.identity());
				shop.upload(leaf_far);
			}
		}

		closed.assign(maps.crossings.size(), 0u);

		for (auto index{ 0u }; index < maps.crossings.size(); index++)
		{
			hang(index);
		}

		logger.write("gates: %zu leaves and %zu lamps at %zu crossings", leaves.size(), lamps.size(), maps.crossings.size());
	}
	/*
	//=====================================================================================
	*/
	void gates_c::clear()
	{
		functions::release(leaf.vertex_buffer);
		functions::release(leaf.index_buffer);
		functions::release(leaf_far.vertex_buffer);
		functions::release(leaf_far.index_buffer);

		leaf = {};
		leaf_far = {};

		leaves.clear();
		lamps.clear();
		closed.clear();

		length = 1.0f;
		settled = false;
	}
	/*
	//=====================================================================================
	*/
	void gates_c::hang(std::uint32_t index)
	{
		const auto& crossing{ maps.crossings[index] };
		const auto post{ models.find(crossing_post_model) };

		for (auto side{ -1.0f }; side <= 1.0f; side += 2.0f)
		{
			const auto parked{ facing(maps.verge_away(crossing, side)) };
			const auto span{ maps.gate_hinge(crossing, side, 1.0f) - maps.gate_hinge(crossing, side, -1.0f) };
			const auto stretch{ std::clamp(mathematics.length(structures::vec3_s{ span.x, 0.0f, span.z }) * 0.5f / length, crossing_stretch_low, crossing_stretch_high) };

			for (auto edge{ -1.0f }; edge <= 1.0f; edge += 2.0f)
			{
				const auto placement{ mathematics.multiply(mathematics.rotation(mathematics.quat_axis_angle({ 0.0f, 1.0f, 0.0f }, maps.post_yaw(crossing, side, edge))), mathematics.translation(maps.post_spot(crossing, side, edge))) };

				leaves.push_back({ maps.gate_hinge(crossing, side, edge), parked, facing(maps.gate_toward(crossing, side, edge)), parked, parked, stretch, index });

				for (auto part{ 0u }; post && part < post->parts.size(); part++)
				{
					if (std::strncmp(post->parts[part].name, "light_", 6u) == 0)
					{
						lamps.push_back({ mathematics.transform_point((post->parts[part].bounds_min + post->parts[part].bounds_max) * 0.5f, placement), edge < 0.0f ? 0.0f : 0.5f, index });
					}
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void gates_c::update(std::float_t delta)
	{
		clock += static_cast<std::double_t>(delta);

		for (auto index{ 0u }; index < closed.size() && index < maps.crossings.size(); index++)
		{
			closed[index] = static_cast<std::uint8_t>(approaching(maps.crossings[index]) ? 1u : 0u);
		}

		for (auto& gate : leaves)
		{
			const auto target{ closed[gate.crossing] ? gate.shut : gate.open };
			const auto turn{ mathematics.angle_difference(gate.angle, target) };

			gate.previous = gate.angle;
			gate.angle = settled ? gate.angle + std::clamp(turn, -crossing_swing * delta, crossing_swing * delta) : target;
		}

		settled = true;
	}
	/*
	//=====================================================================================
	*/
	void gates_c::submit()
	{
		const auto blink{ std::fmod(clock * static_cast<std::double_t>(crossing_blink), 1.0) };

		for (const auto& gate : leaves)
		{
			const auto gap{ mathematics.distance(gate.hinge, renderer.camera.position) };
			const auto stretch{ mathematics.scaling({ gate.stretch, 1.0f, 1.0f }) };

			if (gap < crossing_view_distance && leaf.index_count)
			{
				renderer.submit(gap > crossing_detail_distance && leaf_far.index_count ? &leaf_far : &leaf, mathematics.multiply(mathematics.multiply(stretch, mathematics.rotation_y(gate.angle)), mathematics.translation(gate.hinge)), mathematics.multiply(mathematics.multiply(stretch, mathematics.rotation_y(gate.previous)), mathematics.translation(gate.hinge)), -1.0f, gap > crossing_shadow_distance ? static_cast<std::uint32_t>(structures::draw_flag_no_shadow) : 0u);
			}
		}

		for (const auto& lamp : lamps)
		{
			if (closed[lamp.crossing] && std::fmod(blink + static_cast<std::double_t>(lamp.phase), 1.0) < 0.5 && mathematics.distance(lamp.position, renderer.camera.position) < crossing_view_distance)
			{
				renderer.add_light(lamp.position, crossing_lamp_radius, crossing_lamp_color);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool gates_c::approaching(const structures::crossing_s& crossing)
	{
		if (train.ready && train.length > 1.0f)
		{
			const auto ahead{ std::fmod(crossing.along - static_cast<std::float_t>(train.head) + train.length * 2.0f, train.length) };

			return ahead < crossing_close_ahead || train.length - ahead < train.extent + crossing_open_behind;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	std::float_t gates_c::facing(structures::vec3_s direction)
	{
		return std::atan2(-direction.z, direction.x);
	}
}

//=====================================================================================
