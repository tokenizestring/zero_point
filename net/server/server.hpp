
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class server_c
	{
	public:

		udp_socket_c socket;
		std::vector<structures::server_client_s> clients;
		std::vector<survival_c> survivors;
		std::unordered_map<std::uint64_t, std::int32_t> lookup;
		std::vector<std::int32_t> cells;
		std::vector<std::int32_t> links;
		std::vector<structures::reliable_s> delivered;
		std::vector<std::pair<std::float_t, std::int32_t>> nearby;
		std::vector<structures::shot_event_s> shots;
		std::vector<std::uint32_t> heard;
		std::uint8_t buffer[net_receive_bytes]{};
		std::uint8_t packet[net_packet_bytes]{};
		std::uint8_t scratch[net_reliable_bytes]{};
		char name[net_server_name_length]{};
		char map[32]{};
		std::double_t clock = 0.0;
		std::float_t hours = net_start_hours;
		std::float_t crop_timer = 0.0f;
		std::float_t decay_timer = 0.0f;
		std::float_t weather_timer = 600.0f;
		std::uint32_t weather_phase = 0u;
		std::uint32_t crop_revision = 0u;
		std::uint32_t bag_revision = 0u;
		std::int32_t forced_spawn = -1;
		bool forced_ride = false;
		std::float_t tick_accumulator = 0.0f;
		std::float_t snapshot_accumulator = 0.0f;
		std::float_t status_timer = 0.0f;
		std::float_t tick_cost = 0.0f;
		std::uint32_t maximum = net_maximum_players;
		std::uint32_t instance = 0u;
		std::uint32_t player_count = 0u;
		std::uint32_t tick_count = 0u;
		std::uint32_t seed = 0x2545F491u;
		std::uint64_t bytes_sent = 0u;
		std::uint64_t bytes_received = 0u;
		bool running = false;

		bool start(std::uint16_t port, const char* server_name, const char* map_name, std::uint32_t maximum_players);
		void stop();
		void update(std::float_t delta);
		void set_weather(std::uint32_t phase, std::float_t duration);
		void receive();
		void handle_query(const structures::address_s& address, stream_reader_c& reader);
		void handle_connect(const structures::address_s& address, stream_reader_c& reader);
		void handle_data(std::int32_t index, stream_reader_c& reader);
		void handle_message(std::int32_t index, const structures::reliable_s& message);
		void read_input(std::int32_t index, stream_reader_c& reader);
		void simulate(std::float_t delta);
		void run_commands(std::int32_t index);
		void think_bot(std::int32_t index, std::float_t delta);
		void hurt(std::int32_t index, std::float_t amount, std::uint8_t cause, std::int32_t attacker);
		void kill(std::int32_t index, std::uint8_t cause, std::int32_t attacker);
		void shoot(std::int32_t index, const structures::usercmd_s& command);
		void use_tool(std::int32_t index, const structures::usercmd_s& command);
		void broadcast_nodes();
		void send_nodes(std::int32_t index);
		void handle_build(std::int32_t index, stream_reader_c& reader);
		void handle_act(std::int32_t index, stream_reader_c& reader);
		void send_crops(std::int32_t index);
		void send_bags(std::int32_t index);
		void write_structure(stream_writer_c& writer, std::uint32_t structure);
		void send_keypad(std::int32_t index, std::uint32_t door, bool setting);
		void broadcast_structures();
		void send_structures(std::int32_t index);
		void send_container(std::int32_t index, std::uint32_t container);
		void send_hit(std::int32_t shooter, std::int32_t victim, std::float_t damage, bool headshot, bool killed, structures::vec3_s point);
		void record_trails();
		structures::vec3_s present(const structures::movement_state_s& state);
		std::int32_t ray_player(std::int32_t shooter, structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::double_t when, std::float_t lead, std::float_t& distance, std::float_t& height, std::float_t& top);
		structures::trail_s rewound(std::int32_t index, std::double_t when);
		void handle_request(std::int32_t index, stream_reader_c& reader);
		void send_inventory(std::int32_t index);
		void notify(std::int32_t index, const char* text, std::int32_t amount);
		void cue(std::int32_t index, std::uint32_t sound, std::float_t volume, std::float_t pitch);
		void sound_at(std::int32_t source, std::uint32_t sound, structures::vec3_s position, std::float_t volume, std::float_t pitch, std::float_t range);
		void sound_events(std::int32_t index);
		void spawn(std::int32_t index);
		void send_snapshots();
		void share_marks();
		void send_marks(std::int32_t index);
		void build_grid();
		void gather(std::int32_t index);
		void write_player(stream_writer_c& writer, std::int32_t index);
		void send_accept(std::int32_t index, std::uint32_t salt);
		void send_reject(const structures::address_s& address, std::uint8_t reason);
		void broadcast(std::uint8_t type, const void* data, std::uint32_t size, std::int32_t except);
		void announce(std::int32_t index, std::int32_t target);
		void chat(std::int32_t index, const char* text);
		void drop(std::int32_t index, bool notify);
		void add_bots(std::uint32_t count);
		void send_raw(const structures::address_s& address, const std::uint8_t* data, std::uint32_t size);
		std::int32_t find(const structures::address_s& address);
		std::int32_t cell_of(structures::vec3_s position);
		std::uint64_t key(const structures::address_s& address);
		std::float_t random();
	};

	extern server_c server;
}

//=====================================================================================
