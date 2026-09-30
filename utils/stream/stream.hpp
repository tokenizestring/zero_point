
//=====================================================================================

#pragma once

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	class stream_writer_c
	{
	public:

		std::uint8_t* data = nullptr;
		std::uint32_t capacity = 0u;
		std::uint32_t size = 0u;
		bool overflow = false;

		void reset(std::uint8_t* buffer, std::uint32_t buffer_capacity)
		{
			data = buffer;
			capacity = buffer_capacity;
			size = 0u;
			overflow = false;
		}

		void bytes(const void* source, std::uint32_t count)
		{
			if (overflow == false && size + count <= capacity)
			{
				std::memcpy(data + size, source, count);

				size += count;
			}

			else
			{
				overflow = true;
			}
		}

		void u8(std::uint8_t value)
		{
			bytes(&value, 1u);
		}

		void u16(std::uint16_t value)
		{
			bytes(&value, 2u);
		}

		void u32(std::uint32_t value)
		{
			bytes(&value, 4u);
		}

		void i8(std::int8_t value)
		{
			bytes(&value, 1u);
		}

		void i16(std::int16_t value)
		{
			bytes(&value, 2u);
		}

		void f32(std::float_t value)
		{
			bytes(&value, 4u);
		}

		void f64(std::double_t value)
		{
			bytes(&value, 8u);
		}

		void text(const char* value, std::uint32_t limit)
		{
			const auto length{ static_cast<std::uint32_t>(std::min<std::size_t>(std::strlen(value), std::min(limit, 255u))) };

			u8(static_cast<std::uint8_t>(length));

			bytes(value, length);
		}

		std::uint32_t remaining() const
		{
			return capacity - size;
		}
	};
	/*
	//=====================================================================================
	*/
	class stream_reader_c
	{
	public:

		const std::uint8_t* data = nullptr;
		std::uint32_t size = 0u;
		std::uint32_t cursor = 0u;
		bool overflow = false;

		void reset(const std::uint8_t* buffer, std::uint32_t buffer_size)
		{
			data = buffer;
			size = buffer_size;
			cursor = 0u;
			overflow = false;
		}

		void bytes(void* target, std::uint32_t count)
		{
			if (overflow == false && cursor + count <= size)
			{
				std::memcpy(target, data + cursor, count);

				cursor += count;
			}

			else
			{
				overflow = true;

				std::memset(target, 0, count);
			}
		}

		std::uint8_t u8()
		{
			std::uint8_t value{};

			bytes(&value, 1u);

			return value;
		}

		std::uint16_t u16()
		{
			std::uint16_t value{};

			bytes(&value, 2u);

			return value;
		}

		std::uint32_t u32()
		{
			std::uint32_t value{};

			bytes(&value, 4u);

			return value;
		}

		std::int8_t i8()
		{
			std::int8_t value{};

			bytes(&value, 1u);

			return value;
		}

		std::int16_t i16()
		{
			std::int16_t value{};

			bytes(&value, 2u);

			return value;
		}

		std::float_t f32()
		{
			std::float_t value{};

			bytes(&value, 4u);

			return std::isfinite(value) ? value : 0.0f;
		}

		std::double_t f64()
		{
			std::double_t value{};

			bytes(&value, 8u);

			return std::isfinite(value) ? value : 0.0;
		}

		void text(char* out, std::uint32_t capacity)
		{
			const auto length{ static_cast<std::uint32_t>(u8()) };
			const auto kept{ std::min(length, capacity - 1u) };

			bytes(out, kept);

			cursor += length - kept;
			overflow = overflow || cursor > size;
			out[kept] = 0;

			for (auto index{ 0u }; index < kept; index++)
			{
				out[index] = static_cast<std::uint8_t>(out[index]) < 32u ? ' ' : out[index];
			}
		}

		std::uint32_t remaining() const
		{
			return cursor < size ? size - cursor : 0u;
		}
	};
}

//=====================================================================================
