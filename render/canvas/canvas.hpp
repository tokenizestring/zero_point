
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class canvas_c
	{
	public:

		ID3D11VertexShader* vertex_shader = nullptr;
		ID3D11PixelShader* pixel_shader = nullptr;
		ID3D11InputLayout* layout = nullptr;
		ID3D11Buffer* vertex_buffer = nullptr;
		ID3D11Buffer* index_buffer = nullptr;
		ID3D11Buffer* constant_buffer = nullptr;

		std::vector<structures::canvas_vertex_s> vertices;
		std::vector<structures::canvas_batch_s> batches;
		RECT scissor_stack[canvas_scissor_depth]{};
		std::uint32_t scissor_count = 0u;
		std::float_t screen_width = 0.0f;
		std::float_t screen_height = 0.0f;
		std::float_t scale = 1.0f;
		std::float_t zoom = 1.0f;
		std::float_t tracking = 0.0f;

		bool create();
		void destroy();
		void begin(std::float_t width, std::float_t height);
		void end(ID3D11RenderTargetView* target);

		void push(ID3D11ShaderResourceView* texture, const structures::canvas_vertex_s* quad);
		void rect(structures::rect_s area, std::uint32_t color);
		void gradient(structures::rect_s area, std::uint32_t top, std::uint32_t bottom);
		void gradient_horizontal(structures::rect_s area, std::uint32_t left, std::uint32_t right);
		void rounded(structures::rect_s area, std::float_t radius, std::uint32_t color);
		void rounded_outline(structures::rect_s area, std::float_t radius, std::float_t thickness, std::uint32_t color);
		void border(structures::rect_s area, std::float_t thickness, std::uint32_t color);
		void line(structures::vec2_s from, structures::vec2_s to, std::float_t thickness, std::uint32_t color);
		void circle(structures::vec2_s center, std::float_t radius, std::uint32_t color);
		void ring(structures::vec2_s center, std::float_t radius, std::float_t thickness, std::float_t start_angle, std::float_t end_angle, std::uint32_t color);
		void image(ID3D11ShaderResourceView* texture, structures::rect_s area, structures::vec2_s uv_min, structures::vec2_s uv_max, std::uint32_t color);
		std::float_t text(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* string, std::uint32_t align);
		std::float_t text_shadowed(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* string, std::uint32_t align);
		std::float_t text_styled(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* string, std::uint32_t align, std::float_t softness, std::float_t bias);
		std::float_t text_spaced(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* string, std::uint32_t align, std::float_t spacing);
		std::float_t measure(structures::font_e font_index, std::float_t size, const char* string);
		void push_scissor(structures::rect_s area);
		void pop_scissor();
	};

	extern canvas_c canvas;
}

//=====================================================================================
