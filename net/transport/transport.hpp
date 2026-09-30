
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class transport_c
	{
	public:

		void reset(structures::connection_s& connection, const structures::address_s& address, std::double_t now);
		bool queue(structures::connection_s& connection, std::uint8_t type, const void* data, std::uint32_t size);
		void begin(structures::connection_s& connection, stream_writer_c& writer, std::double_t now);
		bool receive(structures::connection_s& connection, stream_reader_c& reader, std::vector<structures::reliable_s>& delivered, std::double_t now);
		void acknowledge(structures::connection_s& connection, std::uint16_t sequence, std::double_t now);
		void accept(structures::connection_s& connection, const structures::reliable_s& message, std::vector<structures::reliable_s>& delivered);
		bool newer(std::uint16_t a, std::uint16_t b);
		std::uint16_t encode_angle(std::float_t angle);
		std::float_t decode_angle(std::uint16_t value);
		std::int16_t encode_pitch(std::float_t angle);
		std::float_t decode_pitch(std::int16_t value);
		std::double_t quantize_time(std::double_t time);
		std::uint32_t encode_time(std::double_t time);
		std::double_t decode_time(std::uint32_t ticks, std::double_t reference);
		std::uint32_t stamp(std::double_t time);
	};

	extern transport_c transport;
}

//=====================================================================================
