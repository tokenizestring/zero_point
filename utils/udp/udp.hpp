
//=====================================================================================

#pragma once

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	class udp_socket_c
	{
	public:

		SOCKET handle = INVALID_SOCKET;
		WSAEVENT signal = WSA_INVALID_EVENT;
		std::uint16_t port = 0u;
		bool started = false;

		bool open(std::uint16_t bind_port, bool broadcast)
		{
			WSADATA data{};

			started = WSAStartup(MAKEWORD(2, 2), &data) == 0;
			handle = started ? socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP) : INVALID_SOCKET;

			if (handle != INVALID_SOCKET)
			{
				sockaddr_in local{};
				u_long nonblocking{ 1u };
				BOOL enable{ broadcast ? TRUE : FALSE };
				BOOL ignore{ FALSE };
				DWORD returned{ 0u };
				std::int32_t buffer{ socket_buffer_bytes };

				local.sin_family = AF_INET;
				local.sin_port = htons(bind_port);
				local.sin_addr.s_addr = htonl(INADDR_ANY);

				setsockopt(handle, SOL_SOCKET, SO_BROADCAST, reinterpret_cast<const char*>(&enable), sizeof(enable));
				setsockopt(handle, SOL_SOCKET, SO_RCVBUF, reinterpret_cast<const char*>(&buffer), sizeof(buffer));
				setsockopt(handle, SOL_SOCKET, SO_SNDBUF, reinterpret_cast<const char*>(&buffer), sizeof(buffer));

				WSAIoctl(handle, socket_ignore_reset, &ignore, sizeof(ignore), nullptr, 0u, &returned, nullptr, nullptr);

				if (bind(handle, reinterpret_cast<const sockaddr*>(&local), sizeof(local)) == 0 && ioctlsocket(handle, FIONBIO, &nonblocking) == 0)
				{
					sockaddr_in bound{};
					std::int32_t length{ sizeof(bound) };

					getsockname(handle, reinterpret_cast<sockaddr*>(&bound), &length);

					port = ntohs(bound.sin_port);
				}

				else
				{
					closesocket(handle);

					handle = INVALID_SOCKET;
				}
			}

			return handle != INVALID_SOCKET;
		}

		bool watch()
		{
			signal = handle != INVALID_SOCKET ? WSACreateEvent() : WSA_INVALID_EVENT;

			if (signal != WSA_INVALID_EVENT && WSAEventSelect(handle, signal, FD_READ) != 0)
			{
				WSACloseEvent(signal);

				signal = WSA_INVALID_EVENT;
			}

			return signal != WSA_INVALID_EVENT;
		}

		void close()
		{
			if (handle != INVALID_SOCKET)
			{
				closesocket(handle);

				handle = INVALID_SOCKET;
			}

			if (signal != WSA_INVALID_EVENT)
			{
				WSACloseEvent(signal);

				signal = WSA_INVALID_EVENT;
			}

			if (started)
			{
				WSACleanup();

				started = false;
			}
		}

		bool send(const structures::address_s& address, const void* data, std::uint32_t size)
		{
			sockaddr_in target{};

			target.sin_family = AF_INET;
			target.sin_port = htons(address.port);
			target.sin_addr.s_addr = address.ip;

			return handle != INVALID_SOCKET && sendto(handle, static_cast<const char*>(data), static_cast<std::int32_t>(size), 0, reinterpret_cast<const sockaddr*>(&target), sizeof(target)) == static_cast<std::int32_t>(size);
		}

		std::int32_t receive(structures::address_s& address, void* data, std::uint32_t capacity)
		{
			sockaddr_in source{};
			std::int32_t length{ sizeof(source) };

			const auto received{ handle != INVALID_SOCKET ? recvfrom(handle, static_cast<char*>(data), static_cast<std::int32_t>(capacity), 0, reinterpret_cast<sockaddr*>(&source), &length) : SOCKET_ERROR };

			address = { source.sin_addr.s_addr, ntohs(source.sin_port) };

			return received;
		}

		static bool parse(const char* text, std::uint16_t default_port, structures::address_s& out)
		{
			char host[128]{};

			auto port_value{ static_cast<std::uint32_t>(default_port) };
			auto result{ false };

			std::snprintf(host, sizeof(host), "%s", text);

			if (auto colon{ std::strrchr(host, ':') }; colon)
			{
				port_value = static_cast<std::uint32_t>(std::strtoul(colon + 1, nullptr, 10));

				*colon = 0;
			}

			WSADATA data{};
			addrinfo hints{};
			addrinfo* found{ nullptr };

			hints.ai_family = AF_INET;
			hints.ai_socktype = SOCK_DGRAM;

			const auto started_here{ WSAStartup(MAKEWORD(2, 2), &data) == 0 };

			if (host[0] && port_value > 0u && port_value < 65536u && getaddrinfo(host, nullptr, &hints, &found) == 0 && found)
			{
				out = { reinterpret_cast<const sockaddr_in*>(found->ai_addr)->sin_addr.s_addr, static_cast<std::uint16_t>(port_value) };

				result = true;
			}

			if (found)
			{
				freeaddrinfo(found);
			}

			if (started_here)
			{
				WSACleanup();
			}

			return result;
		}

		static void format(const structures::address_s& address, char* out, std::uint32_t capacity)
		{
			const auto bytes{ reinterpret_cast<const std::uint8_t*>(&address.ip) };

			std::snprintf(out, capacity, "%u.%u.%u.%u:%u", bytes[0], bytes[1], bytes[2], bytes[3], address.port);
		}
	};
}

//=====================================================================================
