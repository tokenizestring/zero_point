
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_audio_c baker_audio;

	bool baker_audio_c::bake(const char* assets_directory)
	{
		const auto directory{ std::string(assets_directory) + "\\raw\\audio" };

		WIN32_FIND_DATAA found{};

		auto total{ 0ull };

		if (auto handle{ FindFirstFileA((directory + "\\*.wav").c_str(), &found) }; handle != INVALID_HANDLE_VALUE)
		{
			do
			{
				auto name{ std::string(found.cFileName) };

				name = name.substr(0u, name.size() - 4u);

				if (read_wave(directory + "\\" + found.cFileName, name))
				{
					total += items.back().data.size();
				}

				else
				{
					logger.write("baker: sound %s could not be read", found.cFileName);
				}
			}
			while (FindNextFileA(handle, &found));

			FindClose(handle);
		}

		logger.write("baker: %zu sounds, %.1f MB pcm", items.size(), static_cast<std::double_t>(total) / 1048576.0);

		return true;
	}
	/*
	//=====================================================================================
	*/
	bool baker_audio_c::read_wave(const std::string& path, const std::string& name)
	{
		auto result{ false };

		if (auto file{ std::fopen(path.c_str(), "rb") }; file)
		{
			std::vector<std::uint8_t> bytes;

			std::fseek(file, 0, SEEK_END);

			bytes.resize(static_cast<std::size_t>(std::ftell(file)));

			std::fseek(file, 0, SEEK_SET);

			const auto read{ std::fread(bytes.data(), 1u, bytes.size(), file) == bytes.size() };

			std::fclose(file);

			std::uint16_t channels{ 0u };
			std::uint16_t bits{ 0u };
			std::uint32_t rate{ 0u };

			for (auto cursor{ 12u }; read && bytes.size() >= 12u && cursor + 8u <= bytes.size();)
			{
				std::uint32_t chunk_size{ 0u };

				std::memcpy(&chunk_size, bytes.data() + cursor + 4u, 4u);

				if (std::memcmp(bytes.data() + cursor, "fmt ", 4u) == 0 && chunk_size >= 16u)
				{
					std::memcpy(&channels, bytes.data() + cursor + 10u, 2u);
					std::memcpy(&rate, bytes.data() + cursor + 12u, 4u);
					std::memcpy(&bits, bytes.data() + cursor + 22u, 2u);
				}

				else if (std::memcmp(bytes.data() + cursor, "data", 4u) == 0 && bits == 16u && channels && cursor + 8u + chunk_size <= bytes.size())
				{
					baker::pak_item_s item{};

					std::snprintf(item.entry.name, sizeof(item.entry.name), "sound_%s", name.c_str());

					item.entry.type = structures::pak_type_sound;
					item.entry.format = channels;
					item.entry.width = rate;
					item.entry.height = chunk_size / (channels * 2u);
					item.data.assign(bytes.begin() + cursor + 8u, bytes.begin() + cursor + 8u + chunk_size);

					items.push_back(std::move(item));

					result = true;
				}

				cursor += 8u + chunk_size + (chunk_size & 1u);
			}
		}

		return result;
	}
}

//=====================================================================================
