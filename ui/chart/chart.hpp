
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class chart_c
	{
	public:

		std::vector<std::float_t> heights;
		std::vector<std::float_t> coverage;
		std::vector<std::uint32_t> pixels;
		ID3D11ShaderResourceView* view = nullptr;
		structures::vec2_s origin{};
		structures::chart_pin_s pins[chart_pin_count]{};
		structures::vec2_s grave{};
		std::float_t meters = 1.0f;
		std::uint32_t pin_clock = 0u;
		bool open = false;
		bool ready = false;
		bool grave_marked = false;
		bool was_dead = false;

		bool create();
		void destroy();
		void forget();
		void update(bool input_enabled);
		void pin(structures::vec2_s point);
		structures::rect_s frame();
		void draw(std::float_t s);
		void survey();
		void relief();
		void forests();
		void works();
		void furniture();
		void compose();
		bool upload();
		structures::vec2_s project(std::float_t x, std::float_t z);
		void stroke(structures::vec2_s from, structures::vec2_s to, std::float_t width, std::float_t alpha);
		void polygon(const structures::vec2_s* corners, std::uint32_t count, std::float_t alpha);
		void dab(structures::vec2_s center, std::float_t radius, std::float_t alpha);
		void circle(structures::vec2_s center, std::float_t radius, std::float_t width, std::float_t alpha);
		void deposit(std::int32_t x, std::int32_t y, std::float_t alpha);
		std::float_t noise(std::float_t x, std::float_t y, std::uint32_t seed);
		std::float_t fractal(std::float_t x, std::float_t y, std::uint32_t octaves, std::uint32_t seed);
		void triangle(structures::vec2_s a, structures::vec2_s b, structures::vec2_s c, std::uint32_t color);
	};

	extern chart_c chart;
}

//=====================================================================================
