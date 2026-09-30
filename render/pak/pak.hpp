
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class pak_c
	{
	public:

		HANDLE file = INVALID_HANDLE_VALUE;
		HANDLE mapping = nullptr;
		const std::uint8_t* base = nullptr;
		std::uint64_t size = 0u;
		const structures::pak_header_s* header = nullptr;
		const structures::pak_entry_s* entries = nullptr;

		bool open(const char* path);
		void close();
		const structures::pak_entry_s* find(const char* name);
		const std::uint8_t* data(const structures::pak_entry_s* entry);
		std::uint32_t row_pitch(DXGI_FORMAT format, std::uint32_t width);
		std::uint32_t surface_size(DXGI_FORMAT format, std::uint32_t width, std::uint32_t height);
		ID3D11ShaderResourceView* create_texture(const char* name, std::uint32_t skip_mips, bool generate_mips, bool srgb_view);
	};

	extern pak_c pak;
}

//=====================================================================================
