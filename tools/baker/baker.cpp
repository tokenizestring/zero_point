
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_c baker_main;

	std::int32_t baker_c::run(std::int32_t count, char** arguments)
	{
		auto result{ 1 };

		if (count == 3 && std::strcmp(arguments[1], "--terrain") == 0)
		{
			logger.initialize("baker.log", true);

			CoInitializeEx(nullptr, COINIT_MULTITHREADED);

			jobs.start();

			if (baker_images.initialize() && baker_terrain.bake(std::string(arguments[2]) + "\\terrain_cache.bin", std::string(arguments[2]) + "\\terrain_preview.png", false))
			{
				result = 0;
			}

			baker_images.shutdown();

			jobs.stop();

			CoUninitialize();
		}

		else if (count >= 4)
		{
			logger.initialize("baker.log", true);

			CoInitializeEx(nullptr, COINIT_MULTITHREADED);

			jobs.start();

			const auto pak_stamp{ stamp(arguments[1]) };

			logger.write("baker: input stamp %016llx", pak_stamp);

			if (up_to_date(arguments[2], pak_stamp) && GetFileAttributesA(arguments[3]) != INVALID_FILE_ATTRIBUTES)
			{
				logger.write("baker: assets up to date");

				result = 0;
			}

			else if (baker_images.initialize())
			{
				const auto start{ GetTickCount64() };

				const auto output_directory{ std::string(arguments[3]).substr(0u, std::string(arguments[3]).find_last_of("\\/")) };

				if (baker_materials.bake(arguments[1]) && baker_models.bake(arguments[1]) && baker_characters.bake(arguments[1]) && baker_terrain.bake(output_directory + "\\terrain_cache.bin", output_directory + "\\terrain_preview.png", true) && baker_skies.bake(arguments[1]) && baker_audio.bake(arguments[1]) && baker_glyphs.bake(arguments[1]) && baker_item_icons.bake(arguments[1]) && baker_marks.bake(arguments[1]) && baker_icon.bake(arguments[3]))
				{
					baker_models.bake_materials(baker_materials.outputs);

					baker_materials.append_items(items);

					for (auto& item : baker_models.items)
					{
						items.push_back(std::move(item));
					}

					for (auto& item : baker_characters.items)
					{
						items.push_back(std::move(item));
					}

					for (auto& item : baker_terrain.items)
					{
						items.push_back(std::move(item));
					}

					for (auto& item : baker_skies.items)
					{
						items.push_back(std::move(item));
					}

					for (auto& item : baker_audio.items)
					{
						items.push_back(std::move(item));
					}

					baker_glyphs.append_items(items);

					baker_item_icons.append_items(items);

					for (auto& item : baker_marks.items)
					{
						items.push_back(std::move(item));
					}

					if (write(arguments[2], pak_stamp))
					{
						logger.write("baker: wrote %s (%zu entries) in %.1f s", arguments[2], items.size(), static_cast<std::double_t>(GetTickCount64() - start) / 1000.0);

						result = 0;
					}
				}

				baker_images.shutdown();
			}

			jobs.stop();

			CoUninitialize();
		}

		else
		{
			std::printf("usage: baker <assets directory> <pak path> <icon path>\n");
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	std::uint64_t baker_c::stamp(const char* assets_directory)
	{
		auto value{ functions::hash("zero_point_baker_revision_5") ^ pak_version };

		const auto mix = [&](const void* data, std::size_t size)
			{
				for (auto index{ 0u }; index < size; index++)
				{
					value = (value ^ static_cast<const std::uint8_t*>(data)[index]) * 0x100000001B3ull;
				}
			};

		char module_path[MAX_PATH]{};

		GetModuleFileNameA(nullptr, module_path, MAX_PATH);

		WIN32_FILE_ATTRIBUTE_DATA attributes{};

		if (GetFileAttributesExA(module_path, GetFileExInfoStandard, &attributes))
		{
			mix(&attributes.ftLastWriteTime, sizeof(attributes.ftLastWriteTime));
			mix(&attributes.nFileSizeLow, sizeof(attributes.nFileSizeLow));
		}

		std::vector<std::string> pending{ std::string(assets_directory) };

		while (pending.size())
		{
			const auto directory{ pending.back() };

			pending.pop_back();

			WIN32_FIND_DATAA found{};

			if (auto handle{ FindFirstFileA((directory + "\\*").c_str(), &found) }; handle != INVALID_HANDLE_VALUE)
			{
				do
				{
					if (found.cFileName[0] != '.')
					{
						if (found.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)
						{
							pending.push_back(directory + "\\" + found.cFileName);
						}

						else
						{
							mix(found.cFileName, std::strlen(found.cFileName));
							mix(&found.nFileSizeLow, sizeof(found.nFileSizeLow));
							mix(&found.ftLastWriteTime, sizeof(found.ftLastWriteTime));
						}
					}
				}
				while (FindNextFileA(handle, &found));

				FindClose(handle);
			}
		}

		return value;
	}
	/*
	//=====================================================================================
	*/
	bool baker_c::up_to_date(const char* pak_path, std::uint64_t expected)
	{
		auto result{ false };

		if (auto file{ std::fopen(pak_path, "rb") }; file)
		{
			structures::pak_header_s header{};

			if (std::fread(&header, sizeof(header), 1u, file) == 1u)
			{
				result = (header.magic == pak_magic && header.version == pak_version && header.stamp == expected);
			}

			std::fclose(file);
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool baker_c::write(const char* pak_path, std::uint64_t pak_stamp)
	{
		auto result{ false };

		const auto temporary{ std::string(pak_path) + ".tmp" };

		if (auto file{ std::fopen(temporary.c_str(), "wb") }; file)
		{
			structures::pak_header_s header{ pak_magic, pak_version, static_cast<std::uint32_t>(items.size()), 0u, 0u, pak_stamp };

			std::fwrite(&header, sizeof(header), 1u, file);

			const std::uint8_t padding[pak_alignment]{};

			std::vector<structures::pak_entry_s> table;

			for (auto& item : items)
			{
				const auto position{ static_cast<std::uint64_t>(_ftelli64(file)) };
				const auto aligned{ (position + pak_alignment - 1u) & ~static_cast<std::uint64_t>(pak_alignment - 1u) };

				std::fwrite(padding, 1u, static_cast<std::size_t>(aligned - position), file);

				item.entry.offset = aligned;
				item.entry.size = item.data.size();

				std::fwrite(item.data.data(), 1u, item.data.size(), file);

				table.push_back(item.entry);
			}

			header.table_offset = static_cast<std::uint64_t>(_ftelli64(file));

			std::fwrite(table.data(), sizeof(structures::pak_entry_s), table.size(), file);

			std::fseek(file, 0, SEEK_SET);

			std::fwrite(&header, sizeof(header), 1u, file);

			result = (std::ferror(file) == 0);

			std::fclose(file);

			for (auto attempt{ 0u }; result && attempt < 40u; attempt++)
			{
				if (MoveFileExA(temporary.c_str(), pak_path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
				{
					return true;
				}

				Sleep(250u);
			}

			logger.write("baker: could not replace %s (error %lu)", pak_path, GetLastError());

			result = false;
		}

		return result;
	}
}

//=====================================================================================

std::int32_t main(std::int32_t count, char** arguments)
{
	return zp::baker_main.run(count, arguments);
}

//=====================================================================================
