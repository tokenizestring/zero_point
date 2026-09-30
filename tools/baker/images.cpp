
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_images_c baker_images;

	bool baker_images_c::initialize()
	{
		return SUCCEEDED(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&factory)));
	}
	/*
	//=====================================================================================
	*/
	void baker_images_c::shutdown()
	{
		functions::release(factory);
	}
	/*
	//=====================================================================================
	*/
	bool baker_images_c::load(const char* path, baker::image_s& out)
	{
		auto result{ false };

		CoInitializeEx(nullptr, COINIT_MULTITHREADED);

		IWICImagingFactory* local_factory{ nullptr };

		if (SUCCEEDED(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&local_factory))))
		{
			wchar_t wide_path[MAX_PATH]{};

			MultiByteToWideChar(CP_UTF8, 0u, path, -1, wide_path, MAX_PATH);

			IWICBitmapDecoder* decoder{ nullptr };
			IWICBitmapFrameDecode* frame{ nullptr };
			IWICFormatConverter* converter{ nullptr };

			if (SUCCEEDED(local_factory->CreateDecoderFromFilename(wide_path, nullptr, GENERIC_READ, WICDecodeMetadataCacheOnDemand, &decoder)) && SUCCEEDED(decoder->GetFrame(0u, &frame)) && SUCCEEDED(local_factory->CreateFormatConverter(&converter)) && SUCCEEDED(converter->Initialize(frame, GUID_WICPixelFormat32bppRGBA, WICBitmapDitherTypeNone, nullptr, 0.0, WICBitmapPaletteTypeCustom)))
			{
				UINT width{ 0u }, height{ 0u };

				frame->GetSize(&width, &height);

				std::vector<std::uint8_t> bytes(static_cast<std::size_t>(width) * height * 4u);

				if (SUCCEEDED(converter->CopyPixels(nullptr, width * 4u, static_cast<UINT>(bytes.size()), bytes.data())))
				{
					out.width = width;
					out.height = height;
					out.pixels.resize(static_cast<std::size_t>(width) * height);

					for (auto index{ 0u }; index < out.pixels.size(); index++)
					{
						out.pixels[index] = { bytes[index * 4u] / 255.0f, bytes[index * 4u + 1u] / 255.0f, bytes[index * 4u + 2u] / 255.0f, bytes[index * 4u + 3u] / 255.0f };
					}

					result = true;
				}
			}

			functions::release(converter);
			functions::release(frame);
			functions::release(decoder);
			functions::release(local_factory);
		}

		CoUninitialize();

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool baker_images_c::save_png(const char* path, const std::uint8_t* rgba, std::uint32_t width, std::uint32_t height, std::vector<std::uint8_t>* memory)
	{
		auto result{ false };

		IWICStream* stream{ nullptr };
		IStream* memory_stream{ nullptr };
		IWICBitmapEncoder* encoder{ nullptr };
		IWICBitmapFrameEncode* frame{ nullptr };

		if (SUCCEEDED(factory->CreateStream(&stream)))
		{
			wchar_t wide_path[MAX_PATH]{};

			if (path)
			{
				MultiByteToWideChar(CP_UTF8, 0u, path, -1, wide_path, MAX_PATH);
			}

			const auto opened{ path ? SUCCEEDED(stream->InitializeFromFilename(wide_path, GENERIC_WRITE)) : (SUCCEEDED(CreateStreamOnHGlobal(nullptr, TRUE, &memory_stream)) && SUCCEEDED(stream->InitializeFromIStream(memory_stream))) };

			if (opened && SUCCEEDED(factory->CreateEncoder(GUID_ContainerFormatPng, nullptr, &encoder)) && SUCCEEDED(encoder->Initialize(stream, WICBitmapEncoderNoCache)) && SUCCEEDED(encoder->CreateNewFrame(&frame, nullptr)) && SUCCEEDED(frame->Initialize(nullptr)))
			{
				WICPixelFormatGUID format{ GUID_WICPixelFormat32bppRGBA };

				frame->SetSize(width, height);

				frame->SetPixelFormat(&format);

				std::vector<std::uint8_t> pixels(rgba, rgba + static_cast<std::size_t>(width) * height * 4u);

				if (IsEqualGUID(format, GUID_WICPixelFormat32bppBGRA))
				{
					for (auto index{ 0u }; index < pixels.size(); index += 4u)
					{
						std::swap(pixels[index], pixels[index + 2u]);
					}
				}

				result = SUCCEEDED(frame->WritePixels(height, width * 4u, static_cast<UINT>(pixels.size()), pixels.data())) && SUCCEEDED(frame->Commit()) && SUCCEEDED(encoder->Commit());

				if (result && memory && memory_stream)
				{
					STATSTG statistics{};

					memory_stream->Stat(&statistics, STATFLAG_NONAME);

					memory->resize(static_cast<std::size_t>(statistics.cbSize.QuadPart));

					LARGE_INTEGER origin{};

					memory_stream->Seek(origin, STREAM_SEEK_SET, nullptr);

					ULONG read{ 0u };

					memory_stream->Read(memory->data(), static_cast<ULONG>(memory->size()), &read);
				}
			}
		}

		functions::release(frame);
		functions::release(encoder);
		functions::release(stream);
		functions::release(memory_stream);

		return result;
	}
	/*
	//=====================================================================================
	*/
	void baker_images_c::downsample(const baker::image_s& source, baker::image_s& out)
	{
		const auto width{ std::max(1u, source.width / 2u) };
		const auto height{ std::max(1u, source.height / 2u) };

		std::vector<structures::vec4_s> pixels(static_cast<std::size_t>(width) * height);

		for (auto y{ 0u }; y < height; y++)
		{
			for (auto x{ 0u }; x < width; x++)
			{
				const auto x0{ std::min(x * 2u, source.width - 1u) };
				const auto x1{ std::min(x * 2u + 1u, source.width - 1u) };
				const auto y0{ std::min(y * 2u, source.height - 1u) };
				const auto y1{ std::min(y * 2u + 1u, source.height - 1u) };

				pixels[static_cast<std::size_t>(y) * width + x] = (source.pixels[static_cast<std::size_t>(y0) * source.width + x0] + source.pixels[static_cast<std::size_t>(y0) * source.width + x1] + source.pixels[static_cast<std::size_t>(y1) * source.width + x0] + source.pixels[static_cast<std::size_t>(y1) * source.width + x1]) * 0.25f;
			}
		}

		out.width = width;
		out.height = height;
		out.pixels = std::move(pixels);
	}
	/*
	//=====================================================================================
	*/
	void baker_images_c::resample_axis(const baker::image_s& source, baker::image_s& out, std::uint32_t target, bool horizontal)
	{
		const auto source_length{ horizontal ? source.width : source.height };
		const auto other{ horizontal ? source.height : source.width };
		const auto scale{ static_cast<std::float_t>(source_length) / static_cast<std::float_t>(target) };

		baker::image_s result{ horizontal ? target : source.width, horizontal ? source.height : target, {} };

		result.pixels.resize(static_cast<std::size_t>(result.width) * result.height);

		const auto fetch = [&](std::uint32_t along, std::uint32_t line)
			{
				return horizontal ? source.pixels[static_cast<std::size_t>(line) * source.width + along % source_length] : source.pixels[static_cast<std::size_t>(along % source_length) * source.width + line];
			};

		for (auto line{ 0u }; line < other; line++)
		{
			for (auto index{ 0u }; index < target; index++)
			{
				structures::vec4_s value{};

				if (scale > 1.0f)
				{
					const auto start{ static_cast<std::float_t>(index) * scale };
					const auto end{ start + scale };

					for (auto sample{ static_cast<std::uint32_t>(std::floor(start)) }; static_cast<std::float_t>(sample) < end; sample++)
					{
						const auto overlap{ std::min(end, static_cast<std::float_t>(sample) + 1.0f) - std::max(start, static_cast<std::float_t>(sample)) };

						value += fetch(sample, line) * (overlap / scale);
					}
				}

				else
				{
					const auto position{ (static_cast<std::float_t>(index) + 0.5f) * scale - 0.5f + static_cast<std::float_t>(source_length) };
					const auto base{ static_cast<std::uint32_t>(std::floor(position)) };
					const auto t{ position - std::floor(position) };

					value = fetch(base, line) * (1.0f - t) + fetch(base + 1u, line) * t;
				}

				result.pixels[horizontal ? static_cast<std::size_t>(line) * result.width + index : static_cast<std::size_t>(index) * result.width + line] = value;
			}
		}

		out = std::move(result);
	}
	/*
	//=====================================================================================
	*/
	void baker_images_c::resize(baker::image_s& image, std::uint32_t width, std::uint32_t height)
	{
		if (image.width != width)
		{
			resample_axis(image, image, width, true);
		}

		if (image.height != height)
		{
			resample_axis(image, image, height, false);
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_images_c::srgb_to_linear(std::float_t v)
	{
		return v <= 0.04045f ? v / 12.92f : std::pow((v + 0.055f) / 1.055f, 2.4f);
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_images_c::linear_to_srgb(std::float_t v)
	{
		return v <= 0.0031308f ? v * 12.92f : 1.055f * std::pow(v, 1.0f / 2.4f) - 0.055f;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_images_c::hash(std::int32_t x, std::int32_t y, std::uint32_t seed)
	{
		return mathematics.hash_float(static_cast<std::uint32_t>(x) + mathematics.hash_u32(static_cast<std::uint32_t>(y) + mathematics.hash_u32(seed * 0x9E3779B9u)));
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_images_c::value_noise(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t seed)
	{
		const auto ix{ static_cast<std::int32_t>(std::floor(x)) };
		const auto iy{ static_cast<std::int32_t>(std::floor(y)) };
		const auto fx{ x - std::floor(x) };
		const auto fy{ y - std::floor(y) };
		const auto sx{ fx * fx * fx * (fx * (fx * 6.0f - 15.0f) + 10.0f) };
		const auto sy{ fy * fy * fy * (fy * (fy * 6.0f - 15.0f) + 10.0f) };
		const auto x0{ ((ix % period) + period) % period };
		const auto y0{ ((iy % period) + period) % period };
		const auto x1{ (x0 + 1) % period };
		const auto y1{ (y0 + 1) % period };

		return mathematics.lerp(mathematics.lerp(hash(x0, y0, seed), hash(x1, y0, seed), sx), mathematics.lerp(hash(x0, y1, seed), hash(x1, y1, seed), sx), sy);
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_images_c::gradient_noise(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t seed)
	{
		const auto ix{ static_cast<std::int32_t>(std::floor(x)) };
		const auto iy{ static_cast<std::int32_t>(std::floor(y)) };
		const auto fx{ x - std::floor(x) };
		const auto fy{ y - std::floor(y) };
		const auto sx{ fx * fx * fx * (fx * (fx * 6.0f - 15.0f) + 10.0f) };
		const auto sy{ fy * fy * fy * (fy * (fy * 6.0f - 15.0f) + 10.0f) };

		const auto corner = [&](std::int32_t cx, std::int32_t cy, std::float_t dx, std::float_t dy)
			{
				const auto angle{ hash(((cx % period) + period) % period, ((cy % period) + period) % period, seed) * two_pi };

				return std::cos(angle) * dx + std::sin(angle) * dy;
			};

		return mathematics.lerp(mathematics.lerp(corner(ix, iy, fx, fy), corner(ix + 1, iy, fx - 1.0f, fy), sx), mathematics.lerp(corner(ix, iy + 1, fx, fy - 1.0f), corner(ix + 1, iy + 1, fx - 1.0f, fy - 1.0f), sx), sy) * 1.41421356f;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_images_c::fbm(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t octaves, std::float_t gain, std::uint32_t seed)
	{
		auto sum{ 0.0f };
		auto amplitude{ 0.5f };
		auto normalizer{ 0.0f };
		auto frequency{ 1.0f };

		for (auto octave{ 0u }; octave < octaves; octave++)
		{
			sum += gradient_noise(x * frequency, y * frequency, period * static_cast<std::int32_t>(frequency), seed + octave * 131u) * amplitude;

			normalizer += amplitude;

			amplitude *= gain;

			frequency *= 2.0f;
		}

		return sum / normalizer;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_images_c::ridged(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t octaves, std::uint32_t seed)
	{
		auto sum{ 0.0f };
		auto amplitude{ 0.5f };
		auto normalizer{ 0.0f };
		auto frequency{ 1.0f };

		for (auto octave{ 0u }; octave < octaves; octave++)
		{
			const auto ridge{ 1.0f - std::fabs(gradient_noise(x * frequency, y * frequency, period * static_cast<std::int32_t>(frequency), seed + octave * 977u)) };

			sum += ridge * ridge * amplitude;

			normalizer += amplitude;

			amplitude *= 0.5f;

			frequency *= 2.0f;
		}

		return sum / normalizer;
	}
	/*
	//=====================================================================================
	*/
	baker::voronoi_s baker_images_c::voronoi(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t seed)
	{
		baker::voronoi_s result{ 1e9f, 1e9f, 0u };

		const auto ix{ static_cast<std::int32_t>(std::floor(x)) };
		const auto iy{ static_cast<std::int32_t>(std::floor(y)) };

		for (auto oy{ -1 }; oy <= 1; oy++)
		{
			for (auto ox{ -1 }; ox <= 1; ox++)
			{
				const auto cx{ (((ix + ox) % period) + period) % period };
				const auto cy{ (((iy + oy) % period) + period) % period };
				const auto px{ static_cast<std::float_t>(ix + ox) + hash(cx, cy, seed) };
				const auto py{ static_cast<std::float_t>(iy + oy) + hash(cx, cy, seed + 71u) };
				const auto distance{ std::sqrt((px - x) * (px - x) + (py - y) * (py - y)) };

				if (distance < result.f1)
				{
					result.f2 = result.f1;
					result.f1 = distance;
					result.cell = static_cast<std::uint32_t>(cy * period + cx);
				}

				else if (distance < result.f2)
				{
					result.f2 = distance;
				}
			}
		}

		return result;
	}
}

//=====================================================================================
