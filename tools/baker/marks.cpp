
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_marks_c baker_marks;

	bool baker_marks_c::bake(const char* assets_directory)
	{
		const char* names[2] = { "marks_color", "marks_shape" };

		for (auto index{ 0u }; index < 2u; index++)
		{
			const auto path{ std::string(assets_directory) + "\\raw\\marks\\" + names[index] + ".png" };

			baker::image_s image{};

			if (GetFileAttributesA(path.c_str()) != INVALID_FILE_ATTRIBUTES && baker_images.load(path.c_str(), image) && image.width == image.height && image.width >= 4u)
			{
				add(names[index], image, index == 0u);
			}
		}

		logger.write("baker: %zu of 2 mark textures", items.size());

		return true;
	}
	/*
	//=====================================================================================
	*/
	void baker_marks_c::add(const char* name, const baker::image_s& image, bool color)
	{
		baker::pak_item_s item{};

		std::snprintf(item.entry.name, sizeof(item.entry.name), "%s", name);

		item.entry.type = structures::pak_type_texture;
		item.entry.format = static_cast<std::uint32_t>(color ? DXGI_FORMAT_BC7_UNORM_SRGB : DXGI_FORMAT_BC7_UNORM);
		item.entry.width = image.width;
		item.entry.height = image.height;
		item.entry.layers = 1u;
		item.entry.mips = 0u;

		std::vector<structures::vec4_s> level{ image.pixels };

		for (auto& pixel : level)
		{
			pixel = color ? structures::vec4_s{ baker_images.srgb_to_linear(pixel.x), baker_images.srgb_to_linear(pixel.y), baker_images.srgb_to_linear(pixel.z), pixel.w } : pixel;
		}

		for (auto width{ image.width }; width >= 1u; width /= 2u)
		{
			const auto blocks{ std::max(1u, (width + 3u) / 4u) };

			std::vector<std::uint8_t> packed(static_cast<std::size_t>(blocks) * blocks * 16u);

			jobs.parallel_for(blocks, [&](std::uint32_t by)
				{
					std::uint8_t block[64]{};

					for (auto bx{ 0u }; bx < blocks; bx++)
					{
						for (auto texel{ 0u }; texel < 16u; texel++)
						{
							const auto px{ std::min(bx * 4u + (texel & 3u), width - 1u) };
							const auto py{ std::min(by * 4u + (texel >> 2u), width - 1u) };
							const auto& pixel{ level[static_cast<std::size_t>(py) * width + px] };

							block[texel * 4u + 0u] = static_cast<std::uint8_t>(std::clamp(color ? baker_images.linear_to_srgb(pixel.x) : pixel.x, 0.0f, 1.0f) * 255.0f + 0.5f);
							block[texel * 4u + 1u] = static_cast<std::uint8_t>(std::clamp(color ? baker_images.linear_to_srgb(pixel.y) : pixel.y, 0.0f, 1.0f) * 255.0f + 0.5f);
							block[texel * 4u + 2u] = static_cast<std::uint8_t>(std::clamp(color ? baker_images.linear_to_srgb(pixel.z) : pixel.z, 0.0f, 1.0f) * 255.0f + 0.5f);
							block[texel * 4u + 3u] = static_cast<std::uint8_t>(std::clamp(pixel.w, 0.0f, 1.0f) * 255.0f + 0.5f);
						}

						baker_compressor.bc7_block(block, &packed[(static_cast<std::size_t>(by) * blocks + bx) * 16u]);
					}
				});

			item.data.insert(item.data.end(), packed.begin(), packed.end());

			item.entry.mips++;

			if (width > 1u)
			{
				const auto half{ width / 2u };

				std::vector<structures::vec4_s> next(static_cast<std::size_t>(half) * half);

				for (auto row{ 0u }; row < half; row++)
				{
					for (auto column{ 0u }; column < half; column++)
					{
						structures::vec4_s plain{};
						structures::vec4_s weighted{};

						for (auto tap{ 0u }; tap < 4u; tap++)
						{
							const auto& pixel{ level[(static_cast<std::size_t>(row) * 2u + tap / 2u) * width + column * 2u + tap % 2u] };

							plain = { plain.x + pixel.x * 0.25f, plain.y + pixel.y * 0.25f, plain.z + pixel.z * 0.25f, plain.w + pixel.w * 0.25f };
							weighted = { weighted.x + pixel.x * pixel.w, weighted.y + pixel.y * pixel.w, weighted.z + pixel.z * pixel.w, weighted.w + pixel.w };
						}

						next[static_cast<std::size_t>(row) * half + column] = color && weighted.w > 0.0001f ? structures::vec4_s{ weighted.x / weighted.w, weighted.y / weighted.w, weighted.z / weighted.w, plain.w } : plain;
					}
				}

				level = std::move(next);
			}
		}

		items.push_back(std::move(item));
	}
}

//=====================================================================================
