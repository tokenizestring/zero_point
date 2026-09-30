
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	pak_c pak;

	bool pak_c::open(const char* path)
	{
		file = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_RANDOM_ACCESS, nullptr);

		if (file != INVALID_HANDLE_VALUE)
		{
			LARGE_INTEGER file_size{};

			GetFileSizeEx(file, &file_size);

			size = static_cast<std::uint64_t>(file_size.QuadPart);

			mapping = CreateFileMappingA(file, nullptr, PAGE_READONLY, 0u, 0u, nullptr);

			if (mapping)
			{
				base = static_cast<const std::uint8_t*>(MapViewOfFile(mapping, FILE_MAP_READ, 0u, 0u, 0u));

				if (base && size > sizeof(structures::pak_header_s))
				{
					header = reinterpret_cast<const structures::pak_header_s*>(base);

					if (header->magic == pak_magic && header->version == pak_version && header->table_offset + header->entry_count * sizeof(structures::pak_entry_s) <= size)
					{
						entries = reinterpret_cast<const structures::pak_entry_s*>(base + header->table_offset);

						logger.write("pak: %s mapped (%u entries, %llu MB)", path, header->entry_count, size / (1024ull * 1024ull));

						return true;
					}
				}
			}
		}

		logger.write("pak: failed to open %s", path);

		close();

		return false;
	}
	/*
	//=====================================================================================
	*/
	void pak_c::close()
	{
		if (base)
		{
			UnmapViewOfFile(base);

			base = nullptr;
		}

		if (mapping)
		{
			CloseHandle(mapping);

			mapping = nullptr;
		}

		if (file != INVALID_HANDLE_VALUE)
		{
			CloseHandle(file);

			file = INVALID_HANDLE_VALUE;
		}

		header = nullptr;
		entries = nullptr;
	}
	/*
	//=====================================================================================
	*/
	const structures::pak_entry_s* pak_c::find(const char* name)
	{
		if (entries)
		{
			for (auto index{ 0u }; index < header->entry_count; index++)
			{
				if (std::strcmp(entries[index].name, name) == 0)
				{
					return &entries[index];
				}
			}
		}

		logger.write("pak: missing entry %s", name);

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	const std::uint8_t* pak_c::data(const structures::pak_entry_s* entry)
	{
		if (entry && entry->offset + entry->size <= size)
		{
			return base + entry->offset;
		}

		return nullptr;
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t pak_c::row_pitch(DXGI_FORMAT format, std::uint32_t width)
	{
		switch (format)
		{
			case DXGI_FORMAT_BC1_UNORM:
			case DXGI_FORMAT_BC1_UNORM_SRGB:
			case DXGI_FORMAT_BC4_UNORM:
			{
				return std::max(1u, (width + 3u) / 4u) * 8u;
			}

			case DXGI_FORMAT_BC5_UNORM:
			case DXGI_FORMAT_BC7_UNORM:
			case DXGI_FORMAT_BC7_UNORM_SRGB:
			case DXGI_FORMAT_BC6H_UF16:
			{
				return std::max(1u, (width + 3u) / 4u) * 16u;
			}

			case DXGI_FORMAT_R8_UNORM:
			{
				return width;
			}

			case DXGI_FORMAT_R16G16B16A16_FLOAT:
			{
				return width * 8u;
			}

			default:
			{
				return width * 4u;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t pak_c::surface_size(DXGI_FORMAT format, std::uint32_t width, std::uint32_t height)
	{
		if (format == DXGI_FORMAT_BC1_UNORM || format == DXGI_FORMAT_BC1_UNORM_SRGB || format == DXGI_FORMAT_BC4_UNORM || format == DXGI_FORMAT_BC5_UNORM || format == DXGI_FORMAT_BC7_UNORM || format == DXGI_FORMAT_BC7_UNORM_SRGB || format == DXGI_FORMAT_BC6H_UF16)
		{
			return row_pitch(format, width) * std::max(1u, (height + 3u) / 4u);
		}

		return row_pitch(format, width) * height;
	}
	/*
	//=====================================================================================
	*/
	ID3D11ShaderResourceView* pak_c::create_texture(const char* name, std::uint32_t skip_mips, bool generate_mips, bool srgb_view)
	{
		ID3D11ShaderResourceView* view{ nullptr };

		if (const auto entry{ find(name) }; entry && data(entry) && gpu.device)
		{
			const auto format{ static_cast<DXGI_FORMAT>(entry->format) };
			const auto skip{ std::min(skip_mips, entry->mips > 1u ? entry->mips - 1u : 0u) };
			const auto layers{ std::max(1u, entry->layers) };
			const auto mips{ entry->mips - skip };

			std::vector<D3D11_SUBRESOURCE_DATA> initial(static_cast<std::size_t>(layers) * mips);

			auto cursor{ data(entry) };

			for (auto layer{ 0u }; layer < layers; layer++)
			{
				for (auto mip{ 0u }; mip < entry->mips; mip++)
				{
					const auto width{ std::max(1u, entry->width >> mip) };
					const auto height{ std::max(1u, entry->height >> mip) };

					if (mip >= skip)
					{
						initial[static_cast<std::size_t>(layer) * mips + (mip - skip)] = { cursor, row_pitch(format, width), surface_size(format, width, height) };
					}

					cursor += surface_size(format, width, height);
				}
			}

			D3D11_TEXTURE2D_DESC description{};

			description.Width = std::max(1u, entry->width >> skip);
			description.Height = std::max(1u, entry->height >> skip);
			description.MipLevels = generate_mips ? 0u : mips;
			description.ArraySize = layers;
			description.Format = format;
			description.SampleDesc.Count = 1u;
			description.Usage = generate_mips ? D3D11_USAGE_DEFAULT : D3D11_USAGE_IMMUTABLE;
			description.BindFlags = D3D11_BIND_SHADER_RESOURCE | (generate_mips ? D3D11_BIND_RENDER_TARGET : 0u);
			description.MiscFlags = generate_mips ? D3D11_RESOURCE_MISC_GENERATE_MIPS : 0u;

			ID3D11Texture2D* texture{ nullptr };

			if (SUCCEEDED(gpu.device->CreateTexture2D(&description, generate_mips ? nullptr : initial.data(), &texture)))
			{
				D3D11_SHADER_RESOURCE_VIEW_DESC resource{};

				resource.Format = (srgb_view && format == DXGI_FORMAT_R8G8B8A8_UNORM) ? DXGI_FORMAT_R8G8B8A8_UNORM_SRGB : format;

				if (entry->type == structures::pak_type_texture_array)
				{
					resource.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2DARRAY;
					resource.Texture2DArray.MipLevels = static_cast<UINT>(-1);
					resource.Texture2DArray.ArraySize = layers;
				}

				else
				{
					resource.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2D;
					resource.Texture2D.MipLevels = static_cast<UINT>(-1);
				}

				gpu.device->CreateShaderResourceView(texture, &resource, &view);

				if (generate_mips && view)
				{
					D3D11_TEXTURE2D_DESC created{};

					texture->GetDesc(&created);

					for (auto layer{ 0u }; layer < layers; layer++)
					{
						gpu.context->UpdateSubresource(texture, D3D11CalcSubresource(0u, layer, created.MipLevels), nullptr, initial[static_cast<std::size_t>(layer) * mips].pSysMem, initial[static_cast<std::size_t>(layer) * mips].SysMemPitch, 0u);
					}

					gpu.context->GenerateMips(view);
				}

				functions::release(texture);
			}

			else
			{
				logger.write("pak: texture creation failed for %s", name);
			}
		}

		return view;
	}
}

//=====================================================================================
