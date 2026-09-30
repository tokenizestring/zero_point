
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	namespace functions
	{
		std::uint32_t lerp_color(std::uint32_t a, std::uint32_t b, std::float_t t)
		{
			return rgba(static_cast<std::uint32_t>(mathematics.lerp(static_cast<std::float_t>(a & 0xFFu), static_cast<std::float_t>(b & 0xFFu), t)), static_cast<std::uint32_t>(mathematics.lerp(static_cast<std::float_t>((a >> 8u) & 0xFFu), static_cast<std::float_t>((b >> 8u) & 0xFFu), t)), static_cast<std::uint32_t>(mathematics.lerp(static_cast<std::float_t>((a >> 16u) & 0xFFu), static_cast<std::float_t>((b >> 16u) & 0xFFu), t)), static_cast<std::uint32_t>(mathematics.lerp(static_cast<std::float_t>(a >> 24u), static_cast<std::float_t>(b >> 24u), t)));
		}
		/*
		//=====================================================================================
		*/
		std::string executable_directory()
		{
			char path[MAX_PATH]{};

			GetModuleFileNameA(nullptr, path, MAX_PATH);

			if (auto slash{ std::strrchr(path, '\\') }; slash)
			{
				slash[1] = 0;
			}

			return path;
		}
		/*
		//=====================================================================================
		*/
		bool read_file(const char* path, std::vector<std::uint8_t>& out)
		{
			auto result{ false };

			if (auto file{ std::fopen(path, "rb") }; file)
			{
				std::fseek(file, 0, SEEK_END);

				out.resize(static_cast<std::size_t>(std::ftell(file)));

				std::fseek(file, 0, SEEK_SET);

				result = std::fread(out.data(), 1u, out.size(), file) == out.size();

				std::fclose(file);
			}

			return result;
		}
		/*
		//=====================================================================================
		*/
		bool write_file(const char* path, const void* data, std::size_t size)
		{
			auto result{ false };

			if (auto file{ std::fopen(path, "wb") }; file)
			{
				result = std::fwrite(data, 1u, size, file) == size;

				std::fclose(file);
			}

			return result;
		}
	}

	static_assert(sizeof(structures::vec2_s) == 8u);
	static_assert(sizeof(structures::vec3_s) == 12u);
	static_assert(sizeof(structures::vec4_s) == 16u);
	static_assert(sizeof(structures::quat_s) == 16u);
	static_assert(sizeof(structures::mat4_s) == 64u);
	static_assert(sizeof(structures::canvas_vertex_s) == 52u);
	static_assert(sizeof(structures::canvas_constants_s) == 16u);
}

//=====================================================================================
