
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_skies_c baker_skies;

	bool baker_skies_c::bake(const char* assets_directory)
	{
		for (const auto name : baker::sky_sources)
		{
			char path[MAX_PATH]{};

			std::snprintf(path, sizeof(path), "%s\\raw\\hdri\\%s_4k.hdr", assets_directory, name);

			baker::image_s image{};

			if (decode_hdr(path, image))
			{
				structures::sky_record_s record{};

				std::snprintf(record.name, sizeof(record.name), "%s", name);

				extract_sun(image, record);

				project_sh(image, record);

				baker::pak_item_s item{};

				std::snprintf(item.entry.name, sizeof(item.entry.name), "sky_%s", name);

				item.entry.type = structures::pak_type_texture;
				item.entry.format = static_cast<std::uint32_t>(DXGI_FORMAT_R9G9B9E5_SHAREDEXP);
				item.entry.width = image.width;
				item.entry.height = image.height;
				item.entry.layers = 1u;
				item.entry.mips = 1u;
				item.data.resize(static_cast<std::size_t>(image.width) * image.height * 4u);

				for (auto index{ 0u }; index < image.pixels.size(); index++)
				{
					const auto packed{ pack_rgb9e5(image.pixels[index].xyz()) };

					std::memcpy(&item.data[index * 4u], &packed, 4u);
				}

				items.push_back(std::move(item));

				records.push_back(record);

				logger.write("baker: sky %s %ux%u sun dir %.2f %.2f %.2f irradiance %.1f %.1f %.1f", name, image.width, image.height, record.sun_direction.x, record.sun_direction.y, record.sun_direction.z, record.sun_irradiance.x, record.sun_irradiance.y, record.sun_irradiance.z);
			}

			else
			{
				logger.write("baker: sky %s failed to decode", name);
			}
		}

		baker::pak_item_s table{};

		std::snprintf(table.entry.name, sizeof(table.entry.name), "%s", "sky_table");

		table.entry.type = structures::pak_type_blob;
		table.entry.layers = static_cast<std::uint32_t>(records.size());
		table.data.resize(records.size() * sizeof(structures::sky_record_s));

		std::memcpy(table.data.data(), records.data(), table.data.size());

		items.push_back(std::move(table));

		return records.size() > 0u;
	}
	/*
	//=====================================================================================
	*/
	bool baker_skies_c::decode_hdr(const char* path, baker::image_s& out)
	{
		std::vector<std::uint8_t> file;

		if (functions::read_file(path, file) && file.size() > 16u)
		{
			auto cursor{ 0u };

			const auto read_line = [&]()
				{
					std::string line;

					while (cursor < file.size() && file[cursor] != '\n')
					{
						line.push_back(static_cast<char>(file[cursor++]));
					}

					cursor++;

					return line;
				};

			for (auto line{ read_line() }; line.size() && cursor < file.size(); line = read_line())
			{
			}

			const auto resolution{ read_line() };

			std::int32_t height{ 0 }, width{ 0 };

			if (std::sscanf(resolution.c_str(), "-Y %d +X %d", &height, &width) == 2 && width > 0 && height > 0)
			{
				out.width = static_cast<std::uint32_t>(width);
				out.height = static_cast<std::uint32_t>(height);
				out.pixels.resize(static_cast<std::size_t>(width) * height);

				std::vector<std::uint8_t> scanline(static_cast<std::size_t>(width) * 4u);

				for (auto row{ 0 }; row < height && cursor + 4u <= file.size(); row++)
				{
					if (file[cursor] == 2u && file[cursor + 1u] == 2u && ((file[cursor + 2u] << 8u) | file[cursor + 3u]) == static_cast<std::uint32_t>(width))
					{
						cursor += 4u;

						for (auto channel{ 0 }; channel < 4; channel++)
						{
							for (auto column{ 0 }; column < width && cursor < file.size();)
							{
								if (auto run{ static_cast<std::int32_t>(file[cursor++]) }; run > 128)
								{
									run -= 128;

									const auto value{ file[cursor++] };

									for (; run > 0 && column < width; run--)
									{
										scanline[static_cast<std::size_t>(column++) * 4u + channel] = value;
									}
								}

								else
								{
									for (; run > 0 && column < width && cursor < file.size(); run--)
									{
										scanline[static_cast<std::size_t>(column++) * 4u + channel] = file[cursor++];
									}
								}
							}
						}
					}

					else
					{
						for (auto column{ 0 }; column < width && cursor + 4u <= file.size(); column++)
						{
							std::memcpy(&scanline[static_cast<std::size_t>(column) * 4u], &file[cursor], 4u);

							cursor += 4u;
						}
					}

					for (auto column{ 0 }; column < width; column++)
					{
						const auto exponent{ scanline[static_cast<std::size_t>(column) * 4u + 3u] };
						const auto scale{ exponent ? std::ldexp(1.0f, static_cast<std::int32_t>(exponent) - 136) : 0.0f };

						out.pixels[static_cast<std::size_t>(row) * width + column] = { scanline[static_cast<std::size_t>(column) * 4u] * scale, scanline[static_cast<std::size_t>(column) * 4u + 1u] * scale, scanline[static_cast<std::size_t>(column) * 4u + 2u] * scale, 1.0f };
					}
				}

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	structures::vec3_s baker_skies_c::direction(std::float_t u, std::float_t v)
	{
		const auto phi{ (u - 0.5f) * two_pi };
		const auto theta{ v * pi };

		return { std::sin(theta) * std::sin(phi), std::cos(theta), std::sin(theta) * std::cos(phi) };
	}
	/*
	//=====================================================================================
	*/
	void baker_skies_c::extract_sun(baker::image_s& image, structures::sky_record_s& record)
	{
		const auto luminance = [](const structures::vec4_s& p)
			{
				return p.x * 0.2126f + p.y * 0.7152f + p.z * 0.0722f;
			};

		auto brightest{ 0u };
		auto brightest_value{ 0.0f };
		auto average{ 0.0 };

		for (auto index{ 0u }; index < image.pixels.size(); index++)
		{
			const auto value{ luminance(image.pixels[index]) };

			average += value;

			if (value > brightest_value)
			{
				brightest_value = value;

				brightest = index;
			}
		}

		average /= static_cast<std::double_t>(image.pixels.size());

		const auto sun_u{ (static_cast<std::float_t>(brightest % image.width) + 0.5f) / static_cast<std::float_t>(image.width) };
		const auto sun_v{ (static_cast<std::float_t>(brightest / image.width) + 0.5f) / static_cast<std::float_t>(image.height) };
		const auto sun{ direction(sun_u, sun_v) };

		record.sun_direction = sun;
		record.sun_angular_radius = 0.0093f;
		record.sky_scale = 1.0f;

		if (brightest_value > static_cast<std::float_t>(average) * 60.0f)
		{
			const auto pixel_solid_angle{ (two_pi / static_cast<std::float_t>(image.width)) * (pi / static_cast<std::float_t>(image.height)) };
			const auto threshold{ brightest_value * baker::sun_threshold_fraction };
			const auto cos_inner{ std::cos(baker::sun_search_radius) };
			const auto cos_outer{ std::cos(baker::sun_search_radius * 2.0f) };

			structures::vec3_s ring_sum{};
			structures::vec3_s irradiance{};
			structures::vec3_s centroid{};

			auto ring_count{ 0.0f };

			for (auto y{ 0u }; y < image.height; y++)
			{
				const auto v{ (static_cast<std::float_t>(y) + 0.5f) / static_cast<std::float_t>(image.height) };
				const auto solid_angle{ pixel_solid_angle * std::sin(v * pi) };

				for (auto x{ 0u }; x < image.width; x++)
				{
					const auto u{ (static_cast<std::float_t>(x) + 0.5f) / static_cast<std::float_t>(image.width) };
					const auto cosine{ mathematics.dot(direction(u, v), sun) };

					if (cosine > cos_outer && cosine < cos_inner)
					{
						ring_sum += image.pixels[static_cast<std::size_t>(y) * image.width + x].xyz();

						ring_count += 1.0f;
					}

					else if (cosine >= cos_inner && luminance(image.pixels[static_cast<std::size_t>(y) * image.width + x]) > threshold)
					{
						irradiance += image.pixels[static_cast<std::size_t>(y) * image.width + x].xyz() * solid_angle;

						centroid += direction(u, v) * (luminance(image.pixels[static_cast<std::size_t>(y) * image.width + x]) * solid_angle);
					}
				}
			}

			const auto ring_average{ ring_count > 0.0f ? ring_sum / ring_count : structures::vec3_s{} };

			for (auto y{ 0u }; y < image.height; y++)
			{
				const auto v{ (static_cast<std::float_t>(y) + 0.5f) / static_cast<std::float_t>(image.height) };

				for (auto x{ 0u }; x < image.width; x++)
				{
					const auto u{ (static_cast<std::float_t>(x) + 0.5f) / static_cast<std::float_t>(image.width) };

					if (auto& pixel{ image.pixels[static_cast<std::size_t>(y) * image.width + x] }; mathematics.dot(direction(u, v), sun) >= cos_inner && luminance(pixel) > threshold)
					{
						pixel = { ring_average.x, ring_average.y, ring_average.z, 1.0f };
					}
				}
			}

			record.sun_direction = mathematics.normalize(centroid);
			record.sun_irradiance = irradiance;
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_skies_c::project_sh(const baker::image_s& image, structures::sky_record_s& record)
	{
		const auto pixel_solid_angle{ (two_pi / static_cast<std::float_t>(image.width)) * (pi / static_cast<std::float_t>(image.height)) };

		structures::vec3_s sums[sky_sh_coefficients]{};

		for (auto y{ 0u }; y < image.height; y += 2u)
		{
			const auto v{ (static_cast<std::float_t>(y) + 0.5f) / static_cast<std::float_t>(image.height) };
			const auto solid_angle{ pixel_solid_angle * std::sin(v * pi) * 4.0f };

			for (auto x{ 0u }; x < image.width; x += 2u)
			{
				const auto u{ (static_cast<std::float_t>(x) + 0.5f) / static_cast<std::float_t>(image.width) };
				const auto d{ direction(u, v) };
				const auto radiance{ image.pixels[static_cast<std::size_t>(y) * image.width + x].xyz() * solid_angle };

				const std::float_t basis[sky_sh_coefficients] = { 0.282095f, 0.488603f * d.y, 0.488603f * d.z, 0.488603f * d.x, 1.092548f * d.x * d.y, 1.092548f * d.y * d.z, 0.315392f * (3.0f * d.z * d.z - 1.0f), 1.092548f * d.x * d.z, 0.546274f * (d.x * d.x - d.y * d.y) };

				for (auto coefficient{ 0u }; coefficient < sky_sh_coefficients; coefficient++)
				{
					sums[coefficient] += radiance * basis[coefficient];
				}
			}
		}

		for (auto coefficient{ 0u }; coefficient < sky_sh_coefficients; coefficient++)
		{
			record.sh[coefficient] = { sums[coefficient].x, sums[coefficient].y, sums[coefficient].z, 0.0f };
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t baker_skies_c::pack_rgb9e5(structures::vec3_s color)
	{
		const auto limit{ 65408.0f };
		const auto r{ std::clamp(color.x, 0.0f, limit) };
		const auto g{ std::clamp(color.y, 0.0f, limit) };
		const auto b{ std::clamp(color.z, 0.0f, limit) };
		const auto largest{ std::max(r, std::max(g, b)) };

		if (largest > 1e-20f)
		{
			auto exponent{ std::max(-16, static_cast<std::int32_t>(std::floor(std::log2(largest)))) + 1 + 15 };
			auto denominator{ std::ldexp(1.0f, exponent - 15 - 9) };

			if (static_cast<std::int32_t>(std::floor(largest / denominator + 0.5f)) == 512)
			{
				denominator *= 2.0f;

				exponent++;
			}

			const auto rm{ static_cast<std::uint32_t>(std::floor(r / denominator + 0.5f)) };
			const auto gm{ static_cast<std::uint32_t>(std::floor(g / denominator + 0.5f)) };
			const auto bm{ static_cast<std::uint32_t>(std::floor(b / denominator + 0.5f)) };

			return (std::min(rm, 511u)) | (std::min(gm, 511u) << 9u) | (std::min(bm, 511u) << 18u) | (static_cast<std::uint32_t>(std::clamp(exponent, 0, 31)) << 27u);
		}

		return 0u;
	}
}

//=====================================================================================
