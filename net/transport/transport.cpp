
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	transport_c transport;

	void transport_c::reset(structures::connection_s& connection, const structures::address_s& address, std::double_t now)
	{
		connection.address = address;
		connection.local_sequence = 0u;
		connection.remote_sequence = 0xFFFFu;
		connection.remote_bits = 0u;
		connection.next_outgoing = 0u;
		connection.next_incoming = 0u;
		connection.last_received = now;
		connection.last_sent = now;
		connection.rtt = 0.1f;

		connection.outgoing.clear();
		connection.incoming.clear();
		connection.sent.assign(net_sent_history, {});
	}
	/*
	//=====================================================================================
	*/
	bool transport_c::queue(structures::connection_s& connection, std::uint8_t type, const void* data, std::uint32_t size)
	{
		auto result{ false };

		if (connection.outgoing.size() < net_reliable_capacity && size <= net_reliable_bytes)
		{
			structures::reliable_s message{};

			message.id = connection.next_outgoing++;
			message.type = type;
			message.size = static_cast<std::uint16_t>(size);
			message.sent_time = -1000.0;

			std::memcpy(message.data, data, size);

			connection.outgoing.push_back(message);

			result = true;
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void transport_c::begin(structures::connection_s& connection, stream_writer_c& writer, std::double_t now)
	{
		const auto sequence{ connection.local_sequence++ };
		const auto resend{ static_cast<std::double_t>(std::max(0.1f, connection.rtt * 1.5f)) };

		auto& record{ connection.sent[sequence % net_sent_history] };

		record = { sequence, 0u, true, now, {} };

		writer.u32(net_protocol_id);
		writer.u8(structures::packet_data);
		writer.u16(sequence);
		writer.u16(connection.remote_sequence);
		writer.u32(connection.remote_bits);

		const auto count_at{ writer.size };

		writer.u8(0u);

		auto budget{ net_reliable_budget };

		for (auto& message : connection.outgoing)
		{
			if (record.count < net_reliable_per_packet && now - message.sent_time >= resend && message.size + 5u <= budget)
			{
				writer.u16(message.id);
				writer.u8(message.type);
				writer.u16(message.size);
				writer.bytes(message.data, message.size);

				message.sent_time = now;
				budget -= message.size + 5u;
				record.ids[record.count++] = message.id;
			}
		}

		if (writer.overflow == false)
		{
			writer.data[count_at] = record.count;
		}

		connection.last_sent = now;
	}
	/*
	//=====================================================================================
	*/
	bool transport_c::receive(structures::connection_s& connection, stream_reader_c& reader, std::vector<structures::reliable_s>& delivered, std::double_t now)
	{
		const auto sequence{ reader.u16() };
		const auto ack{ reader.u16() };
		const auto bits{ reader.u32() };
		const auto count{ reader.u8() };

		auto fresh{ false };

		if (reader.overflow == false)
		{
			connection.last_received = now;

			if (newer(sequence, connection.remote_sequence))
			{
				const auto shift{ static_cast<std::uint16_t>(sequence - connection.remote_sequence) };

				connection.remote_bits = shift < 32u ? (connection.remote_bits << shift) | (1u << (shift - 1u)) : 0u;
				connection.remote_sequence = sequence;

				fresh = true;
			}

			else
			{
				const auto behind{ static_cast<std::uint16_t>(connection.remote_sequence - sequence) };

				if (behind > 0u && behind <= 32u && (connection.remote_bits & (1u << (behind - 1u))) == 0u)
				{
					connection.remote_bits |= 1u << (behind - 1u);

					fresh = true;
				}
			}

			acknowledge(connection, ack, now);

			for (auto bit{ 0u }; bit < 32u; bit++)
			{
				if (bits & (1u << bit))
				{
					acknowledge(connection, static_cast<std::uint16_t>(ack - bit - 1u), now);
				}
			}

			for (auto index{ 0u }; index < count && reader.overflow == false; index++)
			{
				structures::reliable_s message{};

				message.id = reader.u16();
				message.type = reader.u8();
				message.size = reader.u16();

				if (message.size <= net_reliable_bytes)
				{
					reader.bytes(message.data, message.size);

					if (reader.overflow == false)
					{
						accept(connection, message, delivered);
					}
				}

				else
				{
					reader.overflow = true;
				}
			}
		}

		return fresh && reader.overflow == false;
	}
	/*
	//=====================================================================================
	*/
	void transport_c::acknowledge(structures::connection_s& connection, std::uint16_t sequence, std::double_t now)
	{
		if (auto& record{ connection.sent[sequence % net_sent_history] }; record.used && record.sequence == sequence)
		{
			for (auto index{ 0u }; index < record.count; index++)
			{
				const auto id{ record.ids[index] };

				connection.outgoing.erase(std::remove_if(connection.outgoing.begin(), connection.outgoing.end(), [id](const structures::reliable_s& message) { return message.id == id; }), connection.outgoing.end());
			}

			connection.rtt = mathematics.lerp(connection.rtt, static_cast<std::float_t>(std::max(now - record.time, 0.0)), 0.1f);

			record.used = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void transport_c::accept(structures::connection_s& connection, const structures::reliable_s& message, std::vector<structures::reliable_s>& delivered)
	{
		if (message.id == connection.next_incoming)
		{
			delivered.push_back(message);

			connection.next_incoming++;

			auto found{ true };

			while (found)
			{
				const auto next{ std::find_if(connection.incoming.begin(), connection.incoming.end(), [&](const structures::reliable_s& waiting) { return waiting.id == connection.next_incoming; }) };

				found = next != connection.incoming.end();

				if (found)
				{
					delivered.push_back(*next);

					connection.incoming.erase(next);
					connection.next_incoming++;
				}
			}
		}

		else if (newer(message.id, connection.next_incoming) && static_cast<std::uint16_t>(message.id - connection.next_incoming) < net_reliable_capacity && std::none_of(connection.incoming.begin(), connection.incoming.end(), [&](const structures::reliable_s& waiting) { return waiting.id == message.id; }))
		{
			connection.incoming.push_back(message);
		}
	}
	/*
	//=====================================================================================
	*/
	bool transport_c::newer(std::uint16_t a, std::uint16_t b)
	{
		return (a > b && a - b <= 32768u) || (a < b && b - a > 32768u);
	}
	/*
	//=====================================================================================
	*/
	std::uint16_t transport_c::encode_angle(std::float_t angle)
	{
		const auto turns{ angle / two_pi };

		return static_cast<std::uint16_t>(static_cast<std::int32_t>(std::floor((turns - std::floor(turns)) * 65536.0f + 0.5f)) & 0xFFFF);
	}
	/*
	//=====================================================================================
	*/
	std::float_t transport_c::decode_angle(std::uint16_t value)
	{
		return mathematics.wrap_angle(static_cast<std::float_t>(value) / 65536.0f * two_pi);
	}
	/*
	//=====================================================================================
	*/
	std::int16_t transport_c::encode_pitch(std::float_t angle)
	{
		return static_cast<std::int16_t>(std::clamp(angle / half_pi, -1.0f, 1.0f) * 32767.0f);
	}
	/*
	//=====================================================================================
	*/
	std::float_t transport_c::decode_pitch(std::int16_t value)
	{
		return static_cast<std::float_t>(value) / 32767.0f * half_pi;
	}
	/*
	//=====================================================================================
	*/
	std::double_t transport_c::quantize_time(std::double_t time)
	{
		return std::floor(std::max(time, 0.0) * net_time_scale) / net_time_scale;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t transport_c::encode_time(std::double_t time)
	{
		return static_cast<std::uint32_t>(static_cast<std::uint64_t>(std::max(time, 0.0) * net_time_scale + 0.5) & 0xFFFFFFFFu);
	}
	/*
	//=====================================================================================
	*/
	std::double_t transport_c::decode_time(std::uint32_t ticks, std::double_t reference)
	{
		const auto base{ static_cast<std::uint64_t>(std::max(reference, 0.0) * net_time_scale) };
		const auto offset{ static_cast<std::int32_t>(ticks - static_cast<std::uint32_t>(base & 0xFFFFFFFFu)) };

		return static_cast<std::double_t>(static_cast<std::int64_t>(base) + offset) / net_time_scale;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t transport_c::stamp(std::double_t time)
	{
		return static_cast<std::uint32_t>(static_cast<std::uint64_t>(std::max(time, 0.0) * 1000.0) & 0xFFFFFFFFu);
	}
}

//=====================================================================================
