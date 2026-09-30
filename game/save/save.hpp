
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class save_c
	{
	public:

		std::vector<std::uint8_t> buffer;
		std::size_t cursor = 0u;
		std::float_t timer = 0.0f;
		bool healthy = true;

		bool exists();
		bool write();
		bool read();
		void tick(std::float_t delta);
		void apply_structures(std::uint32_t first);
		std::string path();
		void put(const void* data, std::size_t size);
		void get(void* data, std::size_t size);

		template <typename value_t>
		void put_value(const value_t& value)
		{
			put(&value, sizeof(value));
		}

		template <typename value_t>
		value_t get_value()
		{
			value_t value{};

			get(&value, sizeof(value));

			return value;
		}
	};

	extern save_c save;
}

//=====================================================================================
