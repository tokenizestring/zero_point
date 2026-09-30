
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	canvas_c canvas;

	bool canvas_c::create()
	{
		const D3D11_INPUT_ELEMENT_DESC elements[] =
		{
			{ "POSITION", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::canvas_vertex_s, position), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 0u, DXGI_FORMAT_R32G32_FLOAT, 0u, offsetof(structures::canvas_vertex_s, uv), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "COLOR", 0u, DXGI_FORMAT_R8G8B8A8_UNORM, 0u, offsetof(structures::canvas_vertex_s, color), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 1u, DXGI_FORMAT_R32G32B32A32_FLOAT, 0u, offsetof(structures::canvas_vertex_s, params), D3D11_INPUT_PER_VERTEX_DATA, 0u },
			{ "TEXCOORD", 2u, DXGI_FORMAT_R32G32B32A32_FLOAT, 0u, offsetof(structures::canvas_vertex_s, extra), D3D11_INPUT_PER_VERTEX_DATA, 0u }
		};

		vertex_shader = gpu.create_vertex_shader("canvas_vs", elements, 5u, &layout);
		pixel_shader = gpu.create_pixel_shader("canvas_ps");

		vertex_buffer = gpu.create_buffer(canvas_max_vertices * sizeof(structures::canvas_vertex_s), D3D11_USAGE_DYNAMIC, D3D11_BIND_VERTEX_BUFFER, D3D11_CPU_ACCESS_WRITE, nullptr, 0u, 0u);

		std::vector<std::uint32_t> indices(canvas_max_indices);

		for (auto quad{ 0u }; quad < canvas_max_quads; quad++)
		{
			indices[quad * 6u + 0u] = quad * 4u + 0u;
			indices[quad * 6u + 1u] = quad * 4u + 1u;
			indices[quad * 6u + 2u] = quad * 4u + 2u;
			indices[quad * 6u + 3u] = quad * 4u + 0u;
			indices[quad * 6u + 4u] = quad * 4u + 2u;
			indices[quad * 6u + 5u] = quad * 4u + 3u;
		}

		index_buffer = gpu.create_buffer(canvas_max_indices * sizeof(std::uint32_t), D3D11_USAGE_IMMUTABLE, D3D11_BIND_INDEX_BUFFER, 0u, indices.data(), 0u, 0u);

		constant_buffer = gpu.create_constant_buffer(sizeof(structures::canvas_constants_s));

		vertices.reserve(canvas_max_vertices);

		batches.reserve(256u);

		return vertex_shader && pixel_shader && layout && vertex_buffer && index_buffer && constant_buffer;
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::destroy()
	{
		functions::release(constant_buffer);
		functions::release(index_buffer);
		functions::release(vertex_buffer);
		functions::release(layout);
		functions::release(pixel_shader);
		functions::release(vertex_shader);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::begin(std::float_t width, std::float_t height)
	{
		screen_width = width;
		screen_height = height;

		scale = height / 1080.0f;

		vertices.clear();
		batches.clear();

		scissor_count = 0u;
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::end(ID3D11RenderTargetView* target)
	{
		if (vertices.size() && target)
		{
			D3D11_MAPPED_SUBRESOURCE mapped{};

			if (SUCCEEDED(gpu.context->Map(vertex_buffer, 0u, D3D11_MAP_WRITE_DISCARD, 0u, &mapped)))
			{
				std::memcpy(mapped.pData, vertices.data(), vertices.size() * sizeof(structures::canvas_vertex_s));

				gpu.context->Unmap(vertex_buffer, 0u);
			}

			const structures::canvas_constants_s constants{ { screen_width, screen_height }, { 1.0f / screen_width, 1.0f / screen_height } };

			gpu.update_buffer(constant_buffer, &constants, sizeof(constants));

			const D3D11_VIEWPORT viewport{ 0.0f, 0.0f, screen_width, screen_height, 0.0f, 1.0f };

			const auto stride{ static_cast<UINT>(sizeof(structures::canvas_vertex_s)) };
			const auto offset{ 0u };

			gpu.context->OMSetRenderTargets(1u, &target, nullptr);
			gpu.context->OMSetBlendState(gpu.blend_alpha, nullptr, 0xFFFFFFFFu);
			gpu.context->OMSetDepthStencilState(gpu.depth_none, 0u);
			gpu.context->RSSetState(gpu.raster_scissor);
			gpu.context->RSSetViewports(1u, &viewport);
			gpu.context->IASetInputLayout(layout);
			gpu.context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
			gpu.context->IASetVertexBuffers(0u, 1u, &vertex_buffer, &stride, &offset);
			gpu.context->IASetIndexBuffer(index_buffer, DXGI_FORMAT_R32_UINT, 0u);
			gpu.context->VSSetShader(vertex_shader, nullptr, 0u);
			gpu.context->VSSetConstantBuffers(0u, 1u, &constant_buffer);
			gpu.context->PSSetShader(pixel_shader, nullptr, 0u);
			gpu.context->PSSetSamplers(0u, 1u, &gpu.sampler_linear_clamp);

			for (const auto& batch : batches)
			{
				gpu.context->RSSetScissorRects(1u, &batch.scissor);

				gpu.context->PSSetShaderResources(0u, 1u, &batch.texture);

				gpu.context->DrawIndexed(batch.index_count, batch.first_index, 0);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::push(ID3D11ShaderResourceView* texture, const structures::canvas_vertex_s* quad)
	{
		if (vertices.size() + 4u <= canvas_max_vertices)
		{
			const auto scissor{ scissor_count ? scissor_stack[scissor_count - 1u] : RECT{ 0, 0, static_cast<LONG>(screen_width), static_cast<LONG>(screen_height) } };

			if (batches.size() && batches.back().texture == texture && std::memcmp(&batches.back().scissor, &scissor, sizeof(RECT)) == 0)
			{
				batches.back().index_count += 6u;
			}

			else
			{
				batches.push_back({ texture, scissor, static_cast<std::uint32_t>(vertices.size() / 4u) * 6u, 6u });
			}

			vertices.insert(vertices.end(), quad, quad + 4);
		}
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::rect(structures::rect_s area, std::uint32_t color)
	{
		gradient(area, color, color);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::gradient(structures::rect_s area, std::uint32_t top, std::uint32_t bottom)
	{
		const structures::canvas_vertex_s quad[4] =
		{
			{ { area.x, area.y }, { 0.0f, 0.0f }, top, {}, {} },
			{ { area.x + area.w, area.y }, { 1.0f, 0.0f }, top, {}, {} },
			{ { area.x + area.w, area.y + area.h }, { 1.0f, 1.0f }, bottom, {}, {} },
			{ { area.x, area.y + area.h }, { 0.0f, 1.0f }, bottom, {}, {} }
		};

		push(nullptr, quad);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::gradient_horizontal(structures::rect_s area, std::uint32_t left, std::uint32_t right)
	{
		const structures::canvas_vertex_s quad[4] =
		{
			{ { area.x, area.y }, { 0.0f, 0.0f }, left, {}, {} },
			{ { area.x + area.w, area.y }, { 1.0f, 0.0f }, right, {}, {} },
			{ { area.x + area.w, area.y + area.h }, { 1.0f, 1.0f }, right, {}, {} },
			{ { area.x, area.y + area.h }, { 0.0f, 1.0f }, left, {}, {} }
		};

		push(nullptr, quad);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::rounded(structures::rect_s area, std::float_t radius, std::uint32_t color)
	{
		rounded_outline(area, radius, 0.0f, color);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::rounded_outline(structures::rect_s area, std::float_t radius, std::float_t thickness, std::uint32_t color)
	{
		const auto half_width{ area.w * 0.5f };
		const auto half_height{ area.h * 0.5f };
		const auto clamped{ std::min(radius, std::min(half_width, half_height)) };
		const structures::vec4_s params{ static_cast<std::float_t>(structures::canvas_mode_rounded), 1.0f, 0.0f, 0.0f };
		const structures::vec4_s extra{ half_width, half_height, clamped, thickness };

		const structures::canvas_vertex_s quad[4] =
		{
			{ { area.x - 1.0f, area.y - 1.0f }, { -half_width - 1.0f, -half_height - 1.0f }, color, params, extra },
			{ { area.x + area.w + 1.0f, area.y - 1.0f }, { half_width + 1.0f, -half_height - 1.0f }, color, params, extra },
			{ { area.x + area.w + 1.0f, area.y + area.h + 1.0f }, { half_width + 1.0f, half_height + 1.0f }, color, params, extra },
			{ { area.x - 1.0f, area.y + area.h + 1.0f }, { -half_width - 1.0f, half_height + 1.0f }, color, params, extra }
		};

		push(nullptr, quad);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::border(structures::rect_s area, std::float_t thickness, std::uint32_t color)
	{
		rect({ area.x, area.y, area.w, thickness }, color);
		rect({ area.x, area.y + area.h - thickness, area.w, thickness }, color);
		rect({ area.x, area.y + thickness, thickness, area.h - thickness * 2.0f }, color);
		rect({ area.x + area.w - thickness, area.y + thickness, thickness, area.h - thickness * 2.0f }, color);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::line(structures::vec2_s from, structures::vec2_s to, std::float_t thickness, std::uint32_t color)
	{
		const auto direction{ mathematics.normalize(to - from) };
		const auto normal{ structures::vec2_s{ -direction.y, direction.x } * (thickness * 0.5f) };

		const structures::canvas_vertex_s quad[4] =
		{
			{ from + normal, { 0.0f, 0.0f }, color, {}, {} },
			{ to + normal, { 1.0f, 0.0f }, color, {}, {} },
			{ to - normal, { 1.0f, 1.0f }, color, {}, {} },
			{ from - normal, { 0.0f, 1.0f }, color, {}, {} }
		};

		push(nullptr, quad);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::circle(structures::vec2_s center, std::float_t radius, std::uint32_t color)
	{
		rounded({ center.x - radius, center.y - radius, radius * 2.0f, radius * 2.0f }, radius, color);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::ring(structures::vec2_s center, std::float_t radius, std::float_t thickness, std::float_t start_angle, std::float_t end_angle, std::uint32_t color)
	{
		const structures::vec4_s params{ static_cast<std::float_t>(structures::canvas_mode_ring), 1.0f, 0.0f, 0.0f };
		const structures::vec4_s extra{ radius, thickness, start_angle, end_angle };
		const auto size{ radius + 1.0f };

		const structures::canvas_vertex_s quad[4] =
		{
			{ { center.x - size, center.y - size }, { -size, -size }, color, params, extra },
			{ { center.x + size, center.y - size }, { size, -size }, color, params, extra },
			{ { center.x + size, center.y + size }, { size, size }, color, params, extra },
			{ { center.x - size, center.y + size }, { -size, size }, color, params, extra }
		};

		push(nullptr, quad);
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::image(ID3D11ShaderResourceView* texture, structures::rect_s area, structures::vec2_s uv_min, structures::vec2_s uv_max, std::uint32_t color)
	{
		const structures::vec4_s params{ static_cast<std::float_t>(structures::canvas_mode_image), 0.0f, 0.0f, 0.0f };

		const structures::canvas_vertex_s quad[4] =
		{
			{ { area.x, area.y }, uv_min, color, params, {} },
			{ { area.x + area.w, area.y }, { uv_max.x, uv_min.y }, color, params, {} },
			{ { area.x + area.w, area.y + area.h }, uv_max, color, params, {} },
			{ { area.x, area.y + area.h }, { uv_min.x, uv_max.y }, color, params, {} }
		};

		push(texture, quad);
	}
	/*
	//=====================================================================================
	*/
	std::float_t canvas_c::text(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* string, std::uint32_t align)
	{
		return text_styled(font_index, position, size, color, string, align, 0.0f, 0.0f);
	}
	/*
	//=====================================================================================
	*/
	std::float_t canvas_c::text_shadowed(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* string, std::uint32_t align)
	{
		text_styled(font_index, position + structures::vec2_s{ size * 0.04f, size * 0.06f }, size, functions::with_alpha(0xFF000000u, static_cast<std::float_t>(color >> 24u) / 255.0f * 0.55f), string, align, 2.5f, 0.06f);

		return text_styled(font_index, position, size, color, string, align, 0.0f, 0.0f);
	}
	/*
	//=====================================================================================
	*/
	std::float_t canvas_c::text_styled(structures::font_e font_index, structures::vec2_s position, std::float_t size, std::uint32_t color, const char* string, std::uint32_t align, std::float_t softness, std::float_t bias)
	{
		const auto& metrics{ font.fonts[font_index] };
		const auto glyph_scale{ size / static_cast<std::float_t>(font_source_size) };
		const auto width{ font.measure(font_index, size, string) };
		const structures::vec4_s params{ static_cast<std::float_t>(structures::canvas_mode_text), softness, bias, 0.0f };

		auto pen{ position };

		if (align & structures::align_center)
		{
			pen.x -= width * 0.5f;
		}

		else if (align & structures::align_right)
		{
			pen.x -= width;
		}

		if (align & structures::align_middle)
		{
			pen.y -= (metrics.ascent + metrics.descent) * glyph_scale * 0.5f;
		}

		else if (align & structures::align_bottom)
		{
			pen.y -= (metrics.ascent + metrics.descent) * glyph_scale;
		}

		pen.y += metrics.ascent * glyph_scale;

		pen.x = std::floor(pen.x + 0.5f);
		pen.y = std::floor(pen.y + 0.5f);

		for (; *string; string++)
		{
			const auto& entry{ font.glyph(font_index, static_cast<std::uint8_t>(*string)) };

			if (entry.visible)
			{
				const auto origin{ pen + entry.offset * glyph_scale };
				const auto extent{ entry.size * glyph_scale };

				const structures::canvas_vertex_s quad[4] =
				{
					{ origin, entry.uv_min, color, params, {} },
					{ { origin.x + extent.x, origin.y }, { entry.uv_max.x, entry.uv_min.y }, color, params, {} },
					{ origin + extent, entry.uv_max, color, params, {} },
					{ { origin.x, origin.y + extent.y }, { entry.uv_min.x, entry.uv_max.y }, color, params, {} }
				};

				push(font.atlas, quad);
			}

			pen.x += entry.advance * glyph_scale;
		}

		return width;
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::push_scissor(structures::rect_s area)
	{
		if (scissor_count < canvas_scissor_depth)
		{
			RECT next{ static_cast<LONG>(area.x), static_cast<LONG>(area.y), static_cast<LONG>(area.x + area.w), static_cast<LONG>(area.y + area.h) };

			if (scissor_count)
			{
				const auto& parent{ scissor_stack[scissor_count - 1u] };

				next = { std::max(next.left, parent.left), std::max(next.top, parent.top), std::min(next.right, parent.right), std::min(next.bottom, parent.bottom) };
			}

			scissor_stack[scissor_count++] = next;
		}
	}
	/*
	//=====================================================================================
	*/
	void canvas_c::pop_scissor()
	{
		if (scissor_count)
		{
			scissor_count--;
		}
	}
}

//=====================================================================================
