
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_compressor_c baker_compressor;

	void baker_compressor_c::bc4_block(const std::uint8_t* values, std::uint32_t stride, std::uint8_t* out)
	{
		auto low{ 255u };
		auto high{ 0u };

		for (auto index{ 0u }; index < 16u; index++)
		{
			low = std::min(low, static_cast<std::uint32_t>(values[index * stride]));
			high = std::max(high, static_cast<std::uint32_t>(values[index * stride]));
		}

		std::memset(out, 0, 8u);

		out[0] = static_cast<std::uint8_t>(high);
		out[1] = static_cast<std::uint8_t>(low);

		if (high > low)
		{
			std::uint32_t palette[8] = { high, low, 0u, 0u, 0u, 0u, 0u, 0u };

			for (auto entry{ 2u }; entry < 8u; entry++)
			{
				palette[entry] = ((8u - entry) * high + (entry - 1u) * low + 3u) / 7u;
			}

			auto bits{ 0ull };

			for (auto index{ 0u }; index < 16u; index++)
			{
				auto best{ 0u };
				auto best_error{ 1000000 };

				for (auto entry{ 0u }; entry < 8u; entry++)
				{
					if (const auto error{ std::abs(static_cast<std::int32_t>(palette[entry]) - static_cast<std::int32_t>(values[index * stride])) }; error < best_error)
					{
						best_error = error;

						best = entry;
					}
				}

				bits |= static_cast<std::uint64_t>(best) << (index * 3u);
			}

			for (auto byte{ 0u }; byte < 6u; byte++)
			{
				out[2u + byte] = static_cast<std::uint8_t>(bits >> (byte * 8u));
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t baker_compressor_c::bc7_quantize(const std::float_t* endpoint, std::uint8_t* out)
	{
		auto best_bit{ 0u };
		auto best_error{ 1e30f };

		for (auto bit{ 0u }; bit < 2u; bit++)
		{
			auto error{ 0.0f };

			for (auto channel{ 0u }; channel < 4u; channel++)
			{
				const auto quantized{ std::clamp(static_cast<std::int32_t>(std::floor((endpoint[channel] - static_cast<std::float_t>(bit)) * 0.5f + 0.5f)), 0, 127) };
				const auto rebuilt{ static_cast<std::float_t>(quantized * 2 + static_cast<std::int32_t>(bit)) };

				error += (rebuilt - endpoint[channel]) * (rebuilt - endpoint[channel]);
			}

			if (error < best_error)
			{
				best_error = error;

				best_bit = bit;
			}
		}

		for (auto channel{ 0u }; channel < 4u; channel++)
		{
			out[channel] = static_cast<std::uint8_t>(std::clamp(static_cast<std::int32_t>(std::floor((endpoint[channel] - static_cast<std::float_t>(best_bit)) * 0.5f + 0.5f)), 0, 127) * 2 + static_cast<std::int32_t>(best_bit));
		}

		return best_bit;
	}
	/*
	//=====================================================================================
	*/
	std::uint64_t baker_compressor_c::bc7_indices(const std::uint8_t* rgba, const std::uint8_t* e0, const std::uint8_t* e1, std::uint8_t* indices)
	{
		std::int32_t palette[16][4]{};

		for (auto entry{ 0u }; entry < 16u; entry++)
		{
			for (auto channel{ 0u }; channel < 4u; channel++)
			{
				palette[entry][channel] = static_cast<std::int32_t>(((64u - baker::bc7_weights[entry]) * e0[channel] + baker::bc7_weights[entry] * e1[channel] + 32u) >> 6u);
			}
		}

		auto total{ 0ull };

		for (auto pixel{ 0u }; pixel < 16u; pixel++)
		{
			auto best{ 0u };
			auto best_error{ 0x7FFFFFFF };

			for (auto entry{ 0u }; entry < 16u; entry++)
			{
				auto error{ 0 };

				for (auto channel{ 0u }; channel < 4u; channel++)
				{
					const auto difference{ palette[entry][channel] - static_cast<std::int32_t>(rgba[pixel * 4u + channel]) };

					error += difference * difference;
				}

				if (error < best_error)
				{
					best_error = error;

					best = entry;
				}
			}

			indices[pixel] = static_cast<std::uint8_t>(best);

			total += static_cast<std::uint64_t>(best_error);
		}

		return total;
	}
	/*
	//=====================================================================================
	*/
	void baker_compressor_c::bc7_pack(const std::uint8_t* e0, const std::uint8_t* e1, std::uint32_t p0, std::uint32_t p1, const std::uint8_t* indices, std::uint8_t* out)
	{
		std::memset(out, 0, 16u);

		auto position{ 0u };

		const auto put = [&](std::uint32_t value, std::uint32_t count)
			{
				for (auto bit{ 0u }; bit < count; bit++)
				{
					if ((value >> bit) & 1u)
					{
						out[(position + bit) >> 3u] |= static_cast<std::uint8_t>(1u << ((position + bit) & 7u));
					}
				}

				position += count;
			};

		put(1u << 6u, 7u);

		for (auto channel{ 0u }; channel < 4u; channel++)
		{
			put(static_cast<std::uint32_t>(e0[channel] >> 1u), 7u);
			put(static_cast<std::uint32_t>(e1[channel] >> 1u), 7u);
		}

		put(p0, 1u);
		put(p1, 1u);

		put(indices[0], 3u);

		for (auto pixel{ 1u }; pixel < 16u; pixel++)
		{
			put(indices[pixel], 4u);
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_compressor_c::bc7_block(const std::uint8_t* rgba, std::uint8_t* out)
	{
		std::float_t mean[4]{};

		for (auto pixel{ 0u }; pixel < 16u; pixel++)
		{
			for (auto channel{ 0u }; channel < 4u; channel++)
			{
				mean[channel] += static_cast<std::float_t>(rgba[pixel * 4u + channel]) / 16.0f;
			}
		}

		std::float_t covariance[4][4]{};

		for (auto pixel{ 0u }; pixel < 16u; pixel++)
		{
			for (auto a{ 0u }; a < 4u; a++)
			{
				for (auto b{ 0u }; b < 4u; b++)
				{
					covariance[a][b] += (static_cast<std::float_t>(rgba[pixel * 4u + a]) - mean[a]) * (static_cast<std::float_t>(rgba[pixel * 4u + b]) - mean[b]);
				}
			}
		}

		std::float_t axis[4] = { covariance[0][0] + 0.001f, covariance[1][1] + 0.002f, covariance[2][2] + 0.003f, covariance[3][3] };

		for (auto iteration{ 0u }; iteration < 8u; iteration++)
		{
			std::float_t next[4]{};

			for (auto a{ 0u }; a < 4u; a++)
			{
				next[a] = covariance[a][0] * axis[0] + covariance[a][1] * axis[1] + covariance[a][2] * axis[2] + covariance[a][3] * axis[3];
			}

			if (const auto size{ std::sqrt(next[0] * next[0] + next[1] * next[1] + next[2] * next[2] + next[3] * next[3]) }; size > 1e-6f)
			{
				for (auto a{ 0u }; a < 4u; a++)
				{
					axis[a] = next[a] / size;
				}
			}
		}

		auto low{ 1e30f };
		auto high{ -1e30f };

		for (auto pixel{ 0u }; pixel < 16u; pixel++)
		{
			auto projection{ 0.0f };

			for (auto channel{ 0u }; channel < 4u; channel++)
			{
				projection += (static_cast<std::float_t>(rgba[pixel * 4u + channel]) - mean[channel]) * axis[channel];
			}

			low = std::min(low, projection);
			high = std::max(high, projection);
		}

		std::float_t endpoint0[4]{};
		std::float_t endpoint1[4]{};

		for (auto channel{ 0u }; channel < 4u; channel++)
		{
			endpoint0[channel] = std::clamp(mean[channel] + axis[channel] * low, 0.0f, 255.0f);
			endpoint1[channel] = std::clamp(mean[channel] + axis[channel] * high, 0.0f, 255.0f);
		}

		std::uint8_t e0[4]{};
		std::uint8_t e1[4]{};
		std::uint8_t indices[16]{};

		auto p0{ bc7_quantize(endpoint0, e0) };
		auto p1{ bc7_quantize(endpoint1, e1) };
		auto error{ bc7_indices(rgba, e0, e1, indices) };

		for (auto iteration{ 0u }; iteration < 3u && error > 0u; iteration++)
		{
			std::float_t aa{ 0.0f }, ab{ 0.0f }, bb{ 0.0f };
			std::float_t ax[4]{};
			std::float_t bx[4]{};

			for (auto pixel{ 0u }; pixel < 16u; pixel++)
			{
				const auto weight{ static_cast<std::float_t>(baker::bc7_weights[indices[pixel]]) / 64.0f };

				aa += (1.0f - weight) * (1.0f - weight);
				ab += (1.0f - weight) * weight;
				bb += weight * weight;

				for (auto channel{ 0u }; channel < 4u; channel++)
				{
					ax[channel] += (1.0f - weight) * static_cast<std::float_t>(rgba[pixel * 4u + channel]);
					bx[channel] += weight * static_cast<std::float_t>(rgba[pixel * 4u + channel]);
				}
			}

			if (const auto determinant{ aa * bb - ab * ab }; std::fabs(determinant) > 1e-6f)
			{
				std::float_t refined0[4]{};
				std::float_t refined1[4]{};

				for (auto channel{ 0u }; channel < 4u; channel++)
				{
					refined0[channel] = std::clamp((ax[channel] * bb - bx[channel] * ab) / determinant, 0.0f, 255.0f);
					refined1[channel] = std::clamp((bx[channel] * aa - ax[channel] * ab) / determinant, 0.0f, 255.0f);
				}

				std::uint8_t candidate0[4]{};
				std::uint8_t candidate1[4]{};
				std::uint8_t candidate_indices[16]{};

				const auto candidate_p0{ bc7_quantize(refined0, candidate0) };
				const auto candidate_p1{ bc7_quantize(refined1, candidate1) };

				if (const auto candidate_error{ bc7_indices(rgba, candidate0, candidate1, candidate_indices) }; candidate_error < error)
				{
					error = candidate_error;

					std::memcpy(e0, candidate0, 4u);
					std::memcpy(e1, candidate1, 4u);
					std::memcpy(indices, candidate_indices, 16u);

					p0 = candidate_p0;
					p1 = candidate_p1;
				}
			}
		}

		if (indices[0] & 8u)
		{
			std::swap(e0, e1);
			std::swap(p0, p1);

			for (auto pixel{ 0u }; pixel < 16u; pixel++)
			{
				indices[pixel] = static_cast<std::uint8_t>(15u - indices[pixel]);
			}
		}

		bc7_pack(e0, e1, p0, p1, indices, out);
	}
	/*
	//=====================================================================================
	*/
	void baker_compressor_c::compress_bc7(const std::uint8_t* rgba, std::uint32_t width, std::uint32_t height, std::vector<std::uint8_t>& out)
	{
		const auto blocks_wide{ std::max(1u, (width + 3u) / 4u) };
		const auto blocks_high{ std::max(1u, (height + 3u) / 4u) };

		std::uint8_t block[64]{};
		std::uint8_t encoded[16]{};

		for (auto by{ 0u }; by < blocks_high; by++)
		{
			for (auto bx{ 0u }; bx < blocks_wide; bx++)
			{
				for (auto pixel{ 0u }; pixel < 16u; pixel++)
				{
					const auto x{ std::min(bx * 4u + (pixel & 3u), width - 1u) };
					const auto y{ std::min(by * 4u + (pixel >> 2u), height - 1u) };

					std::memcpy(&block[pixel * 4u], &rgba[(static_cast<std::size_t>(y) * width + x) * 4u], 4u);
				}

				bc7_block(block, encoded);

				out.insert(out.end(), encoded, encoded + 16);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_compressor_c::compress_bc5(const std::uint8_t* rg, std::uint32_t width, std::uint32_t height, std::vector<std::uint8_t>& out)
	{
		const auto blocks_wide{ std::max(1u, (width + 3u) / 4u) };
		const auto blocks_high{ std::max(1u, (height + 3u) / 4u) };

		std::uint8_t block[32]{};
		std::uint8_t encoded[16]{};

		for (auto by{ 0u }; by < blocks_high; by++)
		{
			for (auto bx{ 0u }; bx < blocks_wide; bx++)
			{
				for (auto pixel{ 0u }; pixel < 16u; pixel++)
				{
					const auto x{ std::min(bx * 4u + (pixel & 3u), width - 1u) };
					const auto y{ std::min(by * 4u + (pixel >> 2u), height - 1u) };

					block[pixel * 2u + 0u] = rg[(static_cast<std::size_t>(y) * width + x) * 2u + 0u];
					block[pixel * 2u + 1u] = rg[(static_cast<std::size_t>(y) * width + x) * 2u + 1u];
				}

				bc4_block(&block[0], 2u, &encoded[0]);
				bc4_block(&block[1], 2u, &encoded[8]);

				out.insert(out.end(), encoded, encoded + 16);
			}
		}
	}
}

//=====================================================================================
