
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class vehicles_c
	{
	public:

		std::vector<structures::vehicle_s> list;
		std::vector<structures::train_box_s> boxes[structures::vehicle_kind_count];
		std::vector<structures::vec3_s> corners[structures::vehicle_kind_count];
		structures::mesh_s bodies[structures::vehicle_kind_count]{};
		structures::mesh_s distant[structures::vehicle_kind_count]{};
		structures::mesh_s wheels[structures::vehicle_kind_count][4]{};
		structures::mesh_s rotors[structures::vehicle_kind_count][2]{};
		structures::mesh_s steering[structures::vehicle_kind_count]{};
		structures::vec3_s pivots[structures::vehicle_kind_count][4]{};
		structures::vec3_s hubs[structures::vehicle_kind_count][2]{};
		structures::vec3_s wheel_hub[structures::vehicle_kind_count]{};
		structures::vec3_s inertia[structures::vehicle_kind_count]{};
		std::unordered_map<std::uint32_t, structures::animal_s> mounts;
		builder_c shop;
		std::uint32_t next_id = 1u;
		std::uint32_t seed = 0x6C8E9CF5u;
		std::uint32_t movers = 0u;
		std::uint32_t placed = 0u;
		std::uint32_t burnt = 0u;
		bool ready = false;

		void create();
		void shape(std::uint32_t kind);
		void build(std::uint32_t kind);
		void mock(std::uint32_t kind);
		structures::vec3_s turned(structures::vec3_s point);
		void clear();
		void populate();
		void spawn(std::uint32_t kind, structures::vec3_s position, std::float_t yaw);
		void reset(structures::vehicle_s& vehicle, structures::vec3_s position, std::float_t yaw);
		structures::vehicle_s* find(std::uint32_t id);
		std::int32_t index_of(std::uint32_t id);
		structures::vehicle_controls_s controls(const structures::vehicle_s& vehicle, const structures::usercmd_s& command);
		void pilot(structures::movement_state_s& state, const structures::usercmd_s& command);
		void advance(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t delta);
		void step(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt);
		void suspend(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt, structures::vec3_s& force, structures::vec3_s& torque);
		void hover(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt, structures::vec3_s& force, structures::vec3_s& torque);
		void stride(structures::vehicle_s& vehicle, const structures::vehicle_controls_s& controls, std::float_t dt);
		std::float_t footing(structures::vec3_s point, std::float_t fallback);
		void collide(structures::vehicle_s& vehicle, std::float_t dt);
		structures::vec3_s solve(const structures::vehicle_s& vehicle, structures::vec3_s torque);
		void simulate(std::float_t delta);
		void place(const structures::vehicle_s& vehicle, std::uint32_t slot);
		void update_movers();
		structures::mat4_s pose(structures::vec3_s position, structures::quat_s orientation);
		structures::vec3_s seat_point(const structures::vehicle_s& vehicle, std::uint32_t seat);
		structures::vec3_s exit_point(const structures::vehicle_s& vehicle, std::uint32_t seat);
		std::int32_t reach(structures::vec3_s eye, structures::vec3_s forward, std::uint32_t& seat);
		bool board(structures::movement_state_s& state, std::int32_t rider, structures::vec3_s eye, structures::vec3_s forward);
		bool tame(structures::movement_state_s& state, std::int32_t rider, structures::vec3_s eye, structures::vec3_s forward);
		void mount(structures::movement_state_s& state, std::int32_t rider, std::uint32_t index, std::uint32_t seat);
		void bury();
		void alight(structures::movement_state_s& state, std::int32_t rider);
		std::float_t damage(std::uint32_t index, std::float_t amount);
		std::int32_t ray(structures::vec3_s origin, structures::vec3_s direction, std::float_t range, std::float_t& distance);
		void write(stream_writer_c& writer, structures::vec3_s viewer, std::uint32_t driven);
		void read(stream_reader_c& reader, std::double_t time);
		void write_state(stream_writer_c& writer, const structures::vehicle_s& vehicle);
		void read_state(stream_reader_c& reader, structures::vehicle_s& vehicle);
		void adopt(structures::vehicle_s& vehicle, const structures::vehicle_s& source);
		void update(std::float_t delta, std::double_t render_time, bool mirrored);
		void present(structures::vehicle_s& vehicle, std::float_t delta);
		void gait(structures::vehicle_s& vehicle, std::float_t delta);
		void sounds(std::float_t delta);
		void submit();
		std::float_t random();
	};

	extern vehicles_c vehicles;
}

//=====================================================================================
