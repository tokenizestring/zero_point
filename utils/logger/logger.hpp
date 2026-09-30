
//=====================================================================================

#pragma once

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	class logger_c
	{
	public:

		char path[MAX_PATH] = {};
		char line[4096] = {};
		std::mutex mutex;
		std::uint64_t written = 0u;
		std::uint64_t cap = 8u * 1024u * 1024u;
		bool console = false;

		void initialize(const char* file_name, bool attach_console)
		{
			GetModuleFileNameA(nullptr, path, MAX_PATH);

			if (auto slash{ std::strrchr(path, '\\') }; slash)
			{
				std::snprintf(slash + 1, static_cast<std::size_t>(MAX_PATH - (slash + 1 - path)), "%s", file_name);
			}

			DeleteFileA(path);

			console = attach_console;
		}

		void write(const char* format, ...)
		{
			std::lock_guard<std::mutex> guard{ mutex };

			va_list arguments;

			va_start(arguments, format);

			std::vsnprintf(line, sizeof(line), format, arguments);

			va_end(arguments);

			if (auto file{ std::fopen(path, written > cap ? "wb" : "ab") }; file)
			{
				if (written > cap)
				{
					written = 0u;
				}

				written += static_cast<std::uint64_t>(std::fprintf(file, "%s\r\n", line));

				std::fclose(file);
			}

			OutputDebugStringA(line);
			OutputDebugStringA("\n");

			if (console)
			{
				std::printf("%s\n", line);

				std::fflush(stdout);
			}
		}
	};

	inline logger_c logger;
}

//=====================================================================================
