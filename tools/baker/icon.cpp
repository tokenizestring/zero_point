
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_icon_c baker_icon;

	bool baker_icon_c::bake(const char* output_path)
	{
		const std::uint32_t sizes[] = { 256u, 64u, 48u, 32u, 16u };

		std::vector<std::vector<std::uint8_t>> encoded;

		for (const auto size : sizes)
		{
			std::vector<std::uint8_t> rgba;
			std::vector<std::uint8_t> png;

			render(size, rgba);

			if (baker_images.save_png(nullptr, rgba.data(), size, size, &png))
			{
				encoded.push_back(std::move(png));
			}
		}

		auto result{ false };

		if (encoded.size() == std::size(sizes))
		{
			if (auto file{ std::fopen(output_path, "wb") }; file)
			{
				const std::uint16_t header[3] = { 0u, 1u, static_cast<std::uint16_t>(encoded.size()) };

				std::fwrite(header, sizeof(header), 1u, file);

				auto offset{ static_cast<std::uint32_t>(6u + 16u * encoded.size()) };

				for (auto index{ 0u }; index < encoded.size(); index++)
				{
					const std::uint8_t dimensions[4] = { static_cast<std::uint8_t>(sizes[index] >= 256u ? 0u : sizes[index]), static_cast<std::uint8_t>(sizes[index] >= 256u ? 0u : sizes[index]), 0u, 0u };
					const std::uint16_t planes_bits[2] = { 1u, 32u };
					const std::uint32_t bytes_offset[2] = { static_cast<std::uint32_t>(encoded[index].size()), offset };

					std::fwrite(dimensions, sizeof(dimensions), 1u, file);
					std::fwrite(planes_bits, sizeof(planes_bits), 1u, file);
					std::fwrite(bytes_offset, sizeof(bytes_offset), 1u, file);

					offset += static_cast<std::uint32_t>(encoded[index].size());
				}

				for (const auto& png : encoded)
				{
					std::fwrite(png.data(), 1u, png.size(), file);
				}

				result = (std::ferror(file) == 0);

				std::fclose(file);
			}
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_icon_c::render(std::uint32_t size, std::vector<std::uint8_t>& rgba)
	{
		const auto samples{ 4u };

		rgba.assign(static_cast<std::size_t>(size) * size * 4u, 0u);

		for (auto y{ 0u }; y < size; y++)
		{
			for (auto x{ 0u }; x < size; x++)
			{
				structures::vec4_s accumulated{};

				for (auto sy{ 0u }; sy < samples; sy++)
				{
					for (auto sx{ 0u }; sx < samples; sx++)
					{
						const auto px{ ((static_cast<std::float_t>(x) + (static_cast<std::float_t>(sx) + 0.5f) / samples) / static_cast<std::float_t>(size)) * 2.0f - 1.0f };
						const auto py{ ((static_cast<std::float_t>(y) + (static_cast<std::float_t>(sy) + 0.5f) / samples) / static_cast<std::float_t>(size)) * 2.0f - 1.0f };

						const auto box{ std::max(std::fabs(px), std::fabs(py)) };
						const auto corner{ std::hypot(std::max(std::fabs(px) - 0.72f, 0.0f), std::max(std::fabs(py) - 0.72f, 0.0f)) };
						const auto inside_box{ (box < 0.96f && corner < 0.24f) ? 1.0f : 0.0f };
						const auto radius{ std::hypot(px * 1.0f, py * 0.82f) };
						const auto ring{ std::fabs(radius - 0.55f) < 0.1f ? 1.0f : 0.0f };
						const auto slash{ std::fabs(px * 0.8f + py * 0.6f) < 0.065f && radius < 0.66f ? 1.0f : 0.0f };
						const auto glow{ std::exp(-std::pow((radius - 0.55f) / 0.2f, 2.0f)) * 0.35f };

						structures::vec4_s color{ 0.035f + 0.02f * (1.0f - py), 0.05f + 0.03f * (1.0f - py), 0.075f + 0.04f * (1.0f - py), inside_box };

						if (inside_box > 0.0f)
						{
							color = color + structures::vec4_s{ 0.0f, 0.55f, 0.75f, 0.0f } * glow;

							if (ring > 0.0f || slash > 0.0f)
							{
								color = slash > 0.0f ? structures::vec4_s{ 1.0f, 0.42f, 0.0f, 1.0f } : structures::vec4_s{ 0.0f, 0.84f, 1.0f, 1.0f };
							}
						}

						accumulated += color * (1.0f / static_cast<std::float_t>(samples * samples));
					}
				}

				const auto target{ (static_cast<std::size_t>(y) * size + x) * 4u };

				rgba[target + 0u] = static_cast<std::uint8_t>(std::clamp(accumulated.x, 0.0f, 1.0f) * 255.0f);
				rgba[target + 1u] = static_cast<std::uint8_t>(std::clamp(accumulated.y, 0.0f, 1.0f) * 255.0f);
				rgba[target + 2u] = static_cast<std::uint8_t>(std::clamp(accumulated.z, 0.0f, 1.0f) * 255.0f);
				rgba[target + 3u] = static_cast<std::uint8_t>(std::clamp(accumulated.w, 0.0f, 1.0f) * 255.0f);
			}
		}
	}
}

//=====================================================================================
