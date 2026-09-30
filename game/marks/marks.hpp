
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class marks_c
	{
	public:

		std::vector<structures::mark_s> ring;
		std::vector<std::int32_t> heads;
		std::vector<std::int32_t> fresh;
		std::uint32_t cursor = 0u;
		std::uint32_t sweep = 0u;
		std::uint32_t count = 0u;
		std::uint32_t seed = 0x51ED270Bu;

		void clear();
		std::double_t now();
		std::uint16_t cell_of(structures::vec3_s position);
		std::uint16_t pack(structures::vec3_s normal);
		structures::vec3_s unpack(std::uint16_t packed);
		structures::vec3_s frame(structures::vec3_s normal, std::uint8_t spin);
		std::uint8_t aim(structures::vec3_s normal, structures::vec3_s toward);
		std::int32_t add(std::uint32_t kind, std::uint32_t variant, structures::vec3_s position, structures::vec3_s normal, std::uint8_t spin, std::uint8_t scale, std::double_t born, bool guessed);
		void remove(std::int32_t index);
		void wipe(std::uint16_t cell);
		void expire();
		void impact(const structures::trace_s& hit, structures::vec3_s direction, std::float_t power, bool guessed);
		void bleed(structures::vec3_s point, structures::vec3_s direction);
		void pool(structures::vec3_s position);
		void tread(const structures::movement_state_s& state, structures::tread_s& tread);
		void write(stream_writer_c& writer, const structures::mark_s& mark);
		void receive(stream_reader_c& reader);
		std::uint8_t roll();
		std::float_t random();
	};

	extern marks_c marks;
}

//=====================================================================================
