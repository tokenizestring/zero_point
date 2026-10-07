
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class dedicated_c
	{
	public:

		std::mutex console_mutex;
		std::vector<std::string> console_lines;
		std::atomic<bool> running{ false };
		HANDLE timer = nullptr;
		HANDLE nudge = nullptr;
		bool precise = false;
		char name[net_server_name_length]{ "Zero Point" };
		char map[32]{ "island" };
		std::uint16_t port = static_cast<std::uint16_t>(net_default_port);
		std::uint32_t maximum = net_maximum_players;
		std::uint32_t bots = 0u;
		std::int32_t forced_weather = -1;
		std::uint32_t seed = 0x2545F491u;
		bool testing = false;

		std::int32_t run(std::int32_t count, char** arguments);
		void parse(std::int32_t count, char** arguments);
		bool load();
		void loop();
		void pause(std::float_t seconds);
		void read_console();
		void execute(const std::string& line);
		void status();
		void test_movement();
		void test_terrain();
		void test_bhop();
		void test_crouch();
		void test_slopes();
		void test_privilege();
		void test_climate();
		void test_train();
		bool find_ground(std::float_t flatness, structures::vec3_s& position);
		structures::usercmd_s test_command(std::float_t yaw, std::float_t forward, std::float_t side, std::uint32_t buttons);
		structures::usercmd_s timed_command(std::double_t time, std::float_t yaw, std::float_t forward, std::uint32_t buttons);
		std::float_t random();
		static BOOL WINAPI control(DWORD type);
	};

	extern dedicated_c dedicated;
}

//=====================================================================================
