
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_glyphs_c baker_glyphs;

	bool baker_glyphs_c::bake(const char* assets_directory)
	{
		atlas.assign(static_cast<std::size_t>(font_atlas_width) * font_atlas_height, 0u);

		auto baked{ 0u };

		WIN32_FIND_DATAA found{};

		if (auto handle{ FindFirstFileA((std::string(assets_directory) + "\\source\\fonts\\*.ttf").c_str(), &found) }; handle != INVALID_HANDLE_VALUE)
		{
			do
			{
				logger.write("baker: font file %s registered %d", found.cFileName, AddFontResourceExA((std::string(assets_directory) + "\\source\\fonts\\" + found.cFileName).c_str(), FR_PRIVATE, nullptr));
			}
			while (FindNextFileA(handle, &found));

			FindClose(handle);
		}

		if (auto dc{ CreateCompatibleDC(nullptr) }; dc)
		{
			for (auto index{ 0u }; index < structures::font_count; index++)
			{
				if (auto handle{ CreateFontW(-font_source_size * font_supersample, 0, 0, 0, font_faces[index].weight, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_TT_PRECIS, CLIP_DEFAULT_PRECIS, ANTIALIASED_QUALITY, DEFAULT_PITCH, font_faces[index].face) }; handle)
				{
					const auto previous{ SelectObject(dc, handle) };

					TEXTMETRICW text_metrics{};
					wchar_t face[64]{};

					GetTextMetricsW(dc, &text_metrics);
					GetTextFaceW(dc, 64, face);

					logger.write("baker: font %u wants %ls got %ls", index, font_faces[index].face, face);

					auto& metrics{ fonts[index] };

					metrics.ascent = static_cast<std::float_t>(text_metrics.tmAscent) / font_supersample;
					metrics.descent = static_cast<std::float_t>(text_metrics.tmDescent) / font_supersample;
					metrics.line_height = static_cast<std::float_t>(text_metrics.tmHeight + text_metrics.tmExternalLeading) / font_supersample;

					for (auto code{ font_first_glyph }; code <= font_last_glyph; code++)
					{
						bake_glyph(dc, metrics, code);
					}

					SelectObject(dc, previous);

					DeleteObject(handle);

					baked++;
				}
			}

			DeleteDC(dc);
		}

		logger.write("baker: fonts baked %u faces, atlas rows used %d of %u", baked, cursor_y + row_height, font_atlas_height);

		return baked == structures::font_count;
	}
	/*
	//=====================================================================================
	*/
	void baker_glyphs_c::bake_glyph(HDC dc, structures::font_metrics_s& metrics, std::uint32_t code)
	{
		const MAT2 identity{ { 0, 1 }, { 0, 0 }, { 0, 0 }, { 0, 1 } };

		GLYPHMETRICS glyph_metrics{};

		auto& target{ metrics.glyphs[code - font_first_glyph] };

		target = {};

		if (const auto size{ GetGlyphOutlineW(dc, code, GGO_GRAY8_BITMAP, &glyph_metrics, 0u, nullptr, &identity) }; size != GDI_ERROR)
		{
			target.advance = static_cast<std::float_t>(glyph_metrics.gmCellIncX) / font_supersample;

			if (size > 0u)
			{
				bitmap.assign(size, 0u);

				GetGlyphOutlineW(dc, code, GGO_GRAY8_BITMAP, &glyph_metrics, size, bitmap.data(), &identity);

				const auto spread{ font_sdf_spread * font_supersample };
				const auto box_width{ static_cast<std::int32_t>(glyph_metrics.gmBlackBoxX) };
				const auto box_height{ static_cast<std::int32_t>(glyph_metrics.gmBlackBoxY) };
				const auto pitch{ (box_width + 3) & ~3 };
				const auto high_width{ ((box_width + spread * 2 + font_supersample - 1) / font_supersample) * font_supersample };
				const auto high_height{ ((box_height + spread * 2 + font_supersample - 1) / font_supersample) * font_supersample };
				const auto cell_width{ high_width / font_supersample };
				const auto cell_height{ high_height / font_supersample };

				if (cursor_x + cell_width + font_padding > static_cast<std::int32_t>(font_atlas_width))
				{
					cursor_x = font_padding;

					cursor_y += row_height + font_padding;

					row_height = 0;
				}

				if (cursor_y + cell_height + font_padding <= static_cast<std::int32_t>(font_atlas_height))
				{
					field_outside.assign(static_cast<std::size_t>(high_width) * high_height, 1e20f);
					field_inside.assign(static_cast<std::size_t>(high_width) * high_height, 0.0f);

					for (auto y{ 0 }; y < box_height; y++)
					{
						for (auto x{ 0 }; x < box_width; x++)
						{
							if (bitmap[static_cast<std::size_t>(y) * pitch + x] >= 32u)
							{
								field_outside[static_cast<std::size_t>(y + spread) * high_width + x + spread] = 0.0f;
								field_inside[static_cast<std::size_t>(y + spread) * high_width + x + spread] = 1e20f;
							}
						}
					}

					distance_field(field_outside, high_width, high_height);
					distance_field(field_inside, high_width, high_height);

					for (auto y{ 0 }; y < cell_height; y++)
					{
						for (auto x{ 0 }; x < cell_width; x++)
						{
							auto sum{ 0.0f };

							for (auto sy{ 0 }; sy < font_supersample; sy++)
							{
								for (auto sx{ 0 }; sx < font_supersample; sx++)
								{
									const auto index{ static_cast<std::size_t>(y * font_supersample + sy) * high_width + x * font_supersample + sx };

									auto signed_distance{ std::sqrt(field_outside[index]) - std::sqrt(field_inside[index]) };

									signed_distance += (signed_distance > 0.0f) ? -0.5f : 0.5f;

									sum += signed_distance;
								}
							}

							const auto distance{ sum / static_cast<std::float_t>(font_supersample * font_supersample * font_supersample) };

							atlas[static_cast<std::size_t>(cursor_y + y) * font_atlas_width + cursor_x + x] = static_cast<std::uint8_t>(std::clamp(0.5f - distance / (2.0f * font_sdf_spread), 0.0f, 1.0f) * 255.0f + 0.5f);
						}
					}

					target.uv_min = { static_cast<std::float_t>(cursor_x) / font_atlas_width, static_cast<std::float_t>(cursor_y) / font_atlas_height };
					target.uv_max = { static_cast<std::float_t>(cursor_x + cell_width) / font_atlas_width, static_cast<std::float_t>(cursor_y + cell_height) / font_atlas_height };
					target.offset = { static_cast<std::float_t>(glyph_metrics.gmptGlyphOrigin.x - spread) / font_supersample, static_cast<std::float_t>(-(glyph_metrics.gmptGlyphOrigin.y + spread)) / font_supersample };
					target.size = { static_cast<std::float_t>(cell_width), static_cast<std::float_t>(cell_height) };
					target.visible = true;

					cursor_x += cell_width + font_padding;

					row_height = std::max(row_height, cell_height);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_glyphs_c::distance_field(std::vector<std::float_t>& grid, std::int32_t grid_width, std::int32_t grid_height)
	{
		const auto longest{ static_cast<std::size_t>(std::max(grid_width, grid_height)) };

		edt_f.resize(longest);
		edt_d.resize(longest);
		edt_z.resize(longest + 1u);
		edt_v.resize(longest);

		for (auto x{ 0 }; x < grid_width; x++)
		{
			for (auto y{ 0 }; y < grid_height; y++)
			{
				edt_f[y] = grid[static_cast<std::size_t>(y) * grid_width + x];
			}

			distance_line(grid_height);

			for (auto y{ 0 }; y < grid_height; y++)
			{
				grid[static_cast<std::size_t>(y) * grid_width + x] = edt_d[y];
			}
		}

		for (auto y{ 0 }; y < grid_height; y++)
		{
			for (auto x{ 0 }; x < grid_width; x++)
			{
				edt_f[x] = grid[static_cast<std::size_t>(y) * grid_width + x];
			}

			distance_line(grid_width);

			for (auto x{ 0 }; x < grid_width; x++)
			{
				grid[static_cast<std::size_t>(y) * grid_width + x] = edt_d[x];
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_glyphs_c::distance_line(std::int32_t count)
	{
		auto k{ 0 };

		edt_v[0] = 0;
		edt_z[0] = -1e20f;
		edt_z[1] = 1e20f;

		for (auto q{ 1 }; q < count; q++)
		{
			auto s{ ((edt_f[q] + static_cast<std::float_t>(q * q)) - (edt_f[edt_v[k]] + static_cast<std::float_t>(edt_v[k] * edt_v[k]))) / static_cast<std::float_t>(2 * q - 2 * edt_v[k]) };

			while (s <= edt_z[k] && k > 0)
			{
				k--;

				s = ((edt_f[q] + static_cast<std::float_t>(q * q)) - (edt_f[edt_v[k]] + static_cast<std::float_t>(edt_v[k] * edt_v[k]))) / static_cast<std::float_t>(2 * q - 2 * edt_v[k]);
			}

			k++;

			edt_v[k] = q;
			edt_z[k] = s;
			edt_z[k + 1] = 1e20f;
		}

		k = 0;

		for (auto q{ 0 }; q < count; q++)
		{
			while (edt_z[k + 1] < static_cast<std::float_t>(q))
			{
				k++;
			}

			edt_d[q] = static_cast<std::float_t>((q - edt_v[k]) * (q - edt_v[k])) + edt_f[edt_v[k]];
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_glyphs_c::append_items(std::vector<baker::pak_item_s>& items)
	{
		baker::pak_item_s texture{};

		std::snprintf(texture.entry.name, sizeof(texture.entry.name), "%s", "font_atlas");

		texture.entry.type = structures::pak_type_texture;
		texture.entry.format = static_cast<std::uint32_t>(DXGI_FORMAT_R8_UNORM);
		texture.entry.width = font_atlas_width;
		texture.entry.height = font_atlas_height;
		texture.entry.layers = 1u;
		texture.entry.mips = 1u;
		texture.data = atlas;

		items.push_back(std::move(texture));

		baker::pak_item_s table{};

		std::snprintf(table.entry.name, sizeof(table.entry.name), "%s", "font_metrics");

		table.entry.type = structures::pak_type_blob;
		table.entry.layers = structures::font_count;
		table.data.resize(sizeof(fonts));

		std::memcpy(table.data.data(), fonts, sizeof(fonts));

		items.push_back(std::move(table));
	}
}

//=====================================================================================
