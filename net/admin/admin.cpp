
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	admin_c admin;

	void admin_c::load()
	{
		std::vector<std::uint8_t> text;

		admins.clear();
		bans.clear();
		allowed.clear();
		password.clear();

		whitelist = false;

		if (functions::read_file(path().c_str(), text))
		{
			std::string line;

			text.push_back('\n');

			for (const auto letter : text)
			{
				if (letter == '\n')
				{
					const auto space{ line.find(' ') };
					const auto word{ line.substr(0u, space) };
					const auto rest{ space == std::string::npos ? std::string{} : line.substr(space + 1u) };

					if (word == "admin" && rest.size())
					{
						mark(admins, rest, true);
					}

					else if (word == "ban" && rest.size())
					{
						mark(bans, rest, true);
					}

					else if (word == "allow" && rest.size())
					{
						mark(allowed, rest, true);
					}

					else if (word == "whitelist")
					{
						whitelist = rest == "on";
					}

					else if (word == "password")
					{
						password = rest.substr(0u, net_password_length - 1u);
					}

					line.clear();
				}

				else if (letter != '\r')
				{
					line.push_back(static_cast<char>(letter));
				}
			}
		}

		logger.write("admin: %zu admins, %zu bans, whitelist %s (%zu allowed), password %s", admins.size(), bans.size(), whitelist ? "on" : "off", allowed.size(), password.size() ? "set" : "off");
	}
	/*
	//=====================================================================================
	*/
	void admin_c::save()
	{
		std::string text{ whitelist ? "whitelist on\n" : "whitelist off\n" };

		if (password.size())
		{
			text += "password " + password + "\n";
		}

		for (const auto& name : admins)
		{
			text += "admin " + name + "\n";
		}

		for (const auto& name : bans)
		{
			text += "ban " + name + "\n";
		}

		for (const auto& name : allowed)
		{
			text += "allow " + name + "\n";
		}

		functions::write_file(path().c_str(), text.data(), text.size());
	}
	/*
	//=====================================================================================
	*/
	std::string admin_c::path()
	{
		return functions::executable_directory() + admin_file_name;
	}
	/*
	//=====================================================================================
	*/
	std::string admin_c::folded(const std::string& name)
	{
		auto result{ name };

		std::transform(result.begin(), result.end(), result.begin(), [](char letter) { return static_cast<char>(std::tolower(static_cast<unsigned char>(letter))); });

		return result;
	}
	/*
	//=====================================================================================
	*/
	bool admin_c::listed(const std::vector<std::string>& list, const std::string& name)
	{
		return std::find(list.begin(), list.end(), folded(name)) != list.end();
	}
	/*
	//=====================================================================================
	*/
	void admin_c::mark(std::vector<std::string>& list, const std::string& name, bool present)
	{
		const auto key{ folded(name) };

		list.erase(std::remove(list.begin(), list.end(), key), list.end());

		if (present)
		{
			list.push_back(key);
		}
	}
	/*
	//=====================================================================================
	*/
	std::int32_t admin_c::screen(const char* name, const char* offered)
	{
		auto verdict{ -1 };

		if (listed(bans, name))
		{
			verdict = structures::reject_banned;
		}

		else if (whitelist && listed(allowed, name) == false && listed(admins, name) == false)
		{
			verdict = structures::reject_whitelist;
		}

		else if (password.size() && password != offered)
		{
			verdict = structures::reject_password;
		}

		return verdict;
	}
	/*
	//=====================================================================================
	*/
	std::int32_t admin_c::player(const std::string& target)
	{
		const auto wanted{ folded(target) };
		const auto numeric{ target.size() && std::all_of(target.begin(), target.end(), [](char letter) { return std::isdigit(static_cast<unsigned char>(letter)) != 0; }) };

		auto found{ -1 };

		for (auto index{ 0 }; index < static_cast<std::int32_t>(server.clients.size()) && found < 0; index++)
		{
			const auto& peer{ server.clients[index] };

			found = peer.active && peer.bot == false && (numeric ? std::atoi(target.c_str()) == index : folded(peer.name) == wanted) ? index : -1;
		}

		return found;
	}
	/*
	//=====================================================================================
	*/
	bool admin_c::command(const std::string& line, std::int32_t issuer)
	{
		const auto space{ line.find(' ') };
		const auto word{ line.substr(0u, space) };
		const auto rest{ space == std::string::npos ? std::string{} : line.substr(space + 1u) };
		const auto target{ player(rest) };
		const auto exact{ target >= 0 ? std::string{ server.clients[target].name } : rest };
		const auto phase{ std::find(std::begin(weather_names), std::end(weather_names), rest) - std::begin(weather_names) };

		char text[192]{};

		auto handled{ true };

		if (word == "kick" && target >= 0)
		{
			std::snprintf(text, sizeof(text), "Kicked %s", exact.c_str());

			server.drop(target, true);
		}

		else if (word == "ban" && exact.size())
		{
			mark(bans, exact, true);

			save();

			std::snprintf(text, sizeof(text), "Banned %s", exact.c_str());

			if (target >= 0)
			{
				server.drop(target, true);
			}
		}

		else if ((word == "unban" || word == "admin" || word == "unadmin" || word == "allow" || word == "disallow") && exact.size())
		{
			mark(word == "unban" ? bans : (word == "admin" || word == "unadmin" ? admins : allowed), exact, word == "admin" || word == "allow");

			save();

			std::snprintf(text, sizeof(text), "%s: %s", word.c_str(), exact.c_str());
		}

		else if (word == "whitelist" && (rest == "on" || rest == "off"))
		{
			whitelist = rest == "on";

			save();

			std::snprintf(text, sizeof(text), "Whitelist %s", rest.c_str());
		}

		else if (word == "password")
		{
			password = rest == "off" ? std::string{} : rest.substr(0u, net_password_length - 1u);

			save();

			std::snprintf(text, sizeof(text), "Password %s", password.size() ? "set" : "removed");
		}

		else if (word == "forget" && exact.size())
		{
			persist.identities.erase(mathematics.hash_text(exact.c_str()));

			std::snprintf(text, sizeof(text), "The name %s can be claimed again", exact.c_str());
		}

		else if (word == "bans")
		{
			std::string list;

			for (const auto& name : bans)
			{
				list += list.size() ? ", " + name : name;
			}

			std::snprintf(text, sizeof(text), "Banned: %s", list.size() ? list.c_str() : "nobody");
		}

		else if (word == "weather" && phase < static_cast<std::ptrdiff_t>(std::size(weather_names)))
		{
			server.set_weather(static_cast<std::uint32_t>(phase), weather_phases[phase].longest);

			std::snprintf(text, sizeof(text), "Weather set to %s", rest.c_str());
		}

		else if (word == "time" && rest.size())
		{
			server.hours = std::fmod(std::max(static_cast<std::float_t>(std::atof(rest.c_str())), 0.0f), 24.0f);

			std::snprintf(text, sizeof(text), "Time set to %.1f h", server.hours);
		}

		else if (word == "tp" && issuer >= 0 && target >= 0 && target != issuer)
		{
			server.clients[issuer].state.position = server.clients[target].state.position + structures::vec3_s{ 1.0f, 0.2f, 0.0f };
			server.clients[issuer].state.velocity = {};

			std::snprintf(text, sizeof(text), "Teleported to %s", exact.c_str());
		}

		else
		{
			handled = false;
		}

		if (text[0])
		{
			reply(issuer, text);
		}

		return handled;
	}
	/*
	//=====================================================================================
	*/
	void admin_c::reply(std::int32_t issuer, const char* text)
	{
		logger.write("admin: %s", text);

		if (issuer >= 0)
		{
			server.notify(issuer, text, 0);
		}
	}
}

//=====================================================================================
