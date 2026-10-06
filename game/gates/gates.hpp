
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class gates_c
	{
	public:

		std::vector<structures::gate_s> leaves;
		std::vector<structures::gate_lamp_s> lamps;
		std::vector<std::uint8_t> closed;
		structures::mesh_s leaf{};
		structures::mesh_s leaf_far{};
		builder_c shop;
		std::float_t length = 1.0f;
		std::double_t clock = 0.0;
		bool settled = false;

		void create();
		void clear();
		void hang(std::uint32_t index);
		void update(std::float_t delta);
		void submit();
		bool approaching(const structures::crossing_s& crossing);
		std::float_t facing(structures::vec3_s direction);
	};

	extern gates_c gates;
}

//=====================================================================================
