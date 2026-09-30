
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class persist_c
	{
	public:

		std::unordered_map<std::uint32_t, structures::player_record_s> records;
		std::unordered_map<std::uint32_t, std::uint64_t> identities;
		std::vector<std::uint8_t> buffer;
		std::size_t cursor = 0u;
		std::float_t timer = 0.0f;
		bool healthy = true;

		void tick(std::float_t delta);
		void remember(std::int32_t index);
		bool recall(std::int32_t index);
		bool write();
		bool claim(std::uint32_t name_hash, std::uint64_t identity);
		structures::player_record_s upgrade(const structures::legacy_record_s& legacy);
		bool read();
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

	extern persist_c persist;
}

//=====================================================================================
