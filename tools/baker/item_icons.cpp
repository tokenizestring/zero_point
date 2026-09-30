//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_item_icons_c baker_item_icons;

	bool baker_item_icons_c::bake(const char* assets_directory)
	{
		const auto atlas_size{ item_icon_size * item_icon_columns };

		auto found{ 0u };

		atlas.assign(static_cast<std::size_t>(atlas_size) * atlas_size * 4u, 0u);
		present.assign(structures::item_count, 0u);

		for (auto item{ 1u }; item < structures::item_count; item++)
		{
			const auto path{ std::string(assets_directory) + "\\raw\\icons\\" + key(item_definitions[item].name) + ".png" };

			baker::image_s image{};

			if (GetFileAttributesA(path.c_str()) != INVALID_FILE_ATTRIBUTES && baker_images.load(path.c_str(), image))
			{
				for (auto& pixel : image.pixels)
				{
					pixel = { pixel.x * pixel.w, pixel.y * pixel.w, pixel.z * pixel.w, pixel.w };
				}

				baker_images.resize(image, item_icon_size, item_icon_size);

				const auto cell_x{ (item % item_icon_columns) * item_icon_size };
				const auto cell_y{ (item / item_icon_columns) * item_icon_size };

				for (auto y{ 0u }; y < item_icon_size; y++)
				{
					for (auto x{ 0u }; x < item_icon_size; x++)
					{
						const auto& pixel{ image.pixels[static_cast<std::size_t>(y) * item_icon_size + x] };
						const auto alpha{ std::clamp(pixel.w, 0.0f, 1.0f) };
						const auto inverse{ alpha > 0.0001f ? 1.0f / alpha : 0.0f };
						const auto target{ ((static_cast<std::size_t>(cell_y) + y) * atlas_size + cell_x + x) * 4u };

						atlas[target + 0u] = static_cast<std::uint8_t>(std::clamp(pixel.x * inverse, 0.0f, 1.0f) * 255.0f + 0.5f);
						atlas[target + 1u] = static_cast<std::uint8_t>(std::clamp(pixel.y * inverse, 0.0f, 1.0f) * 255.0f + 0.5f);
						atlas[target + 2u] = static_cast<std::uint8_t>(std::clamp(pixel.z * inverse, 0.0f, 1.0f) * 255.0f + 0.5f);
						atlas[target + 3u] = static_cast<std::uint8_t>(alpha * 255.0f + 0.5f);
					}
				}

				present[item] = 1u;

				found++;
			}
		}

		logger.write("baker: %u of %u item icons", found, static_cast<std::uint32_t>(structures::item_count) - 1u);

		return true;
	}
	/*
	//=====================================================================================
	*/
	std::string baker_item_icons_c::key(const char* name)
	{
		std::string result;

		for (auto cursor{ name }; *cursor; cursor++)
		{
			const auto letter{ static_cast<unsigned char>(*cursor) };

			if (std::isalnum(letter))
			{
				result.push_back(static_cast<char>(std::tolower(letter)));
			}

			else if (letter == ' ' && result.size() && result.back() != '_')
			{
				result.push_back('_');
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_item_icons_c::append_items(std::vector<baker::pak_item_s>& items)
	{
		const auto atlas_size{ item_icon_size * item_icon_columns };

		baker::pak_item_s texture{};

		std::snprintf(texture.entry.name, sizeof(texture.entry.name), "%s", item_icon_atlas);

		texture.entry.type = structures::pak_type_texture;
		texture.entry.format = static_cast<std::uint32_t>(DXGI_FORMAT_R8G8B8A8_UNORM);
		texture.entry.width = atlas_size;
		texture.entry.height = atlas_size;
		texture.entry.layers = 1u;
		texture.entry.mips = 1u;
		texture.data = atlas;

		std::vector<std::uint8_t> level{ atlas };

		for (auto width{ atlas_size / 2u }; width >= item_icon_columns * 8u; width /= 2u)
		{
			std::vector<std::uint8_t> next(static_cast<std::size_t>(width) * width * 4u);

			for (auto row{ 0u }; row < width; row++)
			{
				for (auto column{ 0u }; column < width; column++)
				{
					auto weight{ 0.0f };
					auto red{ 0.0f };
					auto green{ 0.0f };
					auto blue{ 0.0f };

					for (auto tap{ 0u }; tap < 4u; tap++)
					{
						const auto source{ ((static_cast<std::size_t>(row) * 2u + tap / 2u) * width * 2u + column * 2u + tap % 2u) * 4u };
						const auto alpha{ static_cast<std::float_t>(level[source + 3u]) };

						red += level[source + 0u] * alpha;
						green += level[source + 1u] * alpha;
						blue += level[source + 2u] * alpha;
						weight += alpha;
					}

					const auto target{ (static_cast<std::size_t>(row) * width + column) * 4u };
					const auto scale{ weight > 0.0f ? 1.0f / weight : 0.0f };

					next[target + 0u] = static_cast<std::uint8_t>(red * scale + 0.5f);
					next[target + 1u] = static_cast<std::uint8_t>(green * scale + 0.5f);
					next[target + 2u] = static_cast<std::uint8_t>(blue * scale + 0.5f);
					next[target + 3u] = static_cast<std::uint8_t>(weight / 4.0f + 0.5f);
				}
			}

			texture.data.insert(texture.data.end(), next.begin(), next.end());
			texture.entry.mips++;

			level = std::move(next);
		}

		items.push_back(std::move(texture));

		baker::pak_item_s table{};

		std::snprintf(table.entry.name, sizeof(table.entry.name), "%s", item_icon_table);

		table.entry.type = structures::pak_type_blob;
		table.entry.layers = 1u;
		table.data = present;

		items.push_back(std::move(table));
	}
}

//=====================================================================================
