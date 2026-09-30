
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class font_c
	{
	public:

		structures::font_metrics_s fonts[structures::font_count]{};
		ID3D11ShaderResourceView* atlas = nullptr;

		bool create();
		void destroy();

		const structures::glyph_s& glyph(structures::font_e font, std::uint8_t code);
		std::float_t measure(structures::font_e font, std::float_t size, const char* text);
		std::float_t line_height(structures::font_e font, std::float_t size);
	};

	extern font_c font;
}

//=====================================================================================
