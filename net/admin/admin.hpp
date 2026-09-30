
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class admin_c
	{
	public:

		std::vector<std::string> admins;
		std::vector<std::string> bans;
		std::vector<std::string> allowed;
		std::string password;
		bool whitelist = false;

		void load();
		void save();
		std::string path();
		std::string folded(const std::string& name);
		bool listed(const std::vector<std::string>& list, const std::string& name);
		void mark(std::vector<std::string>& list, const std::string& name, bool present);
		std::int32_t screen(const char* name, const char* offered);
		std::int32_t player(const std::string& target);
		bool command(const std::string& line, std::int32_t issuer);
		void reply(std::int32_t issuer, const char* text);
	};

	extern admin_c admin;
}

//=====================================================================================
