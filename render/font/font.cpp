
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	font_c font;

	bool font_c::create()
	{
		atlas = pak.create_texture("font_atlas", 0u, true, false);

		if (const auto entry{ pak.find("font_metrics") }; entry && entry->size == sizeof(fonts))
		{
			std::memcpy(fonts, pak.data(entry), sizeof(fonts));

			return atlas != nullptr;
		}

		logger.write("font: metrics missing from pak");

		return false;
	}
	/*
	//=====================================================================================
	*/
	void font_c::destroy()
	{
		functions::release(atlas);
	}
	/*
	//=====================================================================================
	*/
	const structures::glyph_s& font_c::glyph(structures::font_e font_index, std::uint8_t code)
	{
		if (code >= font_first_glyph)
		{
			return fonts[font_index].glyphs[code - font_first_glyph];
		}

		return fonts[font_index].glyphs[0];
	}
	/*
	//=====================================================================================
	*/
	std::float_t font_c::measure(structures::font_e font_index, std::float_t size, const char* text)
	{
		auto width{ 0.0f };

		for (; *text; text++)
		{
			width += glyph(font_index, static_cast<std::uint8_t>(*text)).advance;
		}

		return width * size / static_cast<std::float_t>(font_source_size);
	}
	/*
	//=====================================================================================
	*/
	std::float_t font_c::line_height(structures::font_e font_index, std::float_t size)
	{
		return fonts[font_index].line_height * size / static_cast<std::float_t>(font_source_size);
	}
}

//=====================================================================================
