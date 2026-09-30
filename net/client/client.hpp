
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class client_c
	{
	public:

		udp_socket_c socket;
		structures::connection_s connection{};
		structures::address_s server{};
		structures::movement_state_s authority{};
		std::vector<structures::server_entry_s> servers;
		std::vector<structures::remote_player_s> remotes;
		std::vector<std::int32_t> free_actors;
		std::vector<structures::reliable_s> delivered;
		structures::predicted_s history[net_history_size]{};
		std::uint8_t buffer[net_receive_bytes]{};
		std::uint8_t packet[net_packet_bytes]{};
		std::uint8_t scratch[net_reliable_bytes]{};
		char name[net_name_length]{};
		char password[net_password_length]{};
		std::uint64_t identity = 0u;
		char server_name[net_server_name_length]{};
		char map_name[32]{};
		char status[128]{};
		char chat_lines[net_chat_lines][160]{};
		std::float_t chat_times[net_chat_lines]{};
		structures::vec3_s error{};
		std::double_t clock = 0.0;
		std::float_t attempt_timer = 0.0f;
		std::float_t input_timer = 0.0f;
		std::float_t report_timer = 0.0f;
		std::float_t latency = 0.0f;
		std::double_t server_clock = 0.0;
		std::double_t latest_snapshot = -1.0;
		std::float_t health = 100.0f;
		std::uint32_t state = structures::link_idle;
		std::uint32_t attempts = 0u;
		std::uint32_t salt = 0u;
		std::uint32_t nonce = 0u;
		std::uint32_t acknowledged = 0u;
		std::uint32_t maximum = 0u;
		std::uint32_t seed = 0x9E3779B9u;
		std::uint16_t id = 0u;
		std::double_t respawn_asked = -100.0;
		std::float_t worst_miss = 0.0f;
		std::uint32_t misses = 0u;
		std::uint32_t reconciles = 0u;
		std::uint32_t hits_confirmed = 0u;
		std::uint32_t damage_dealt = 0u;
		std::uint32_t shots_heard = 0u;
		std::uint8_t death_cause = 0u;
		char death_killer[net_name_length]{};
		bool alive = true;
		bool revived = false;
		bool synchronized = false;
		bool placed = false;
		bool opened = false;

		bool open();
		void close();
		void connect(const structures::address_s& address);
		void disconnect();
		void refresh();
		void update(std::float_t delta);
		void flush(std::float_t delta);
		void receive();
		void handle_info(const structures::address_s& address, stream_reader_c& reader);
		void handle_accept(stream_reader_c& reader);
		void handle_reject(stream_reader_c& reader);
		void handle_data(stream_reader_c& reader);
		void handle_message(const structures::reliable_s& message);
		void apply_snapshot(stream_reader_c& reader);
		void set_node(std::uint32_t index, bool depleted);
		void apply_structure(std::uint32_t index, const structures::structure_s& structure, bool burning);
		void hear_shot(std::uint16_t shooter, std::uint32_t weapon_id, std::uint32_t result, structures::vec3_s origin, structures::vec3_s end);
		void reconcile(std::uint32_t last);
		void record(const structures::usercmd_s& command, bool usable, bool moving);
		void replay_weapon(std::uint32_t last, const structures::weapon_state_s& authority_weapon);
		void send_input();
		void send_connect();
		void load_identity();
		void update_remotes(std::float_t delta);
		void say(const char* text);
		void request_respawn();
		void request(std::uint8_t type, std::uint16_t first, std::uint16_t second);
		void build(const structures::placement_s& placement);
		void act(std::uint8_t action, structures::vec3_s position);
		void add_chat(const char* text);
		void clear_remotes();
		bool connected();
		std::int32_t find_remote(std::uint16_t remote_id);
		std::int32_t take_actor(structures::vec3_s position, std::float_t yaw);
		std::float_t random();
	};

	extern client_c client;
}

//=====================================================================================
