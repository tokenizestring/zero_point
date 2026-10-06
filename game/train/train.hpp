
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class train_c
	{
	public:

		std::vector<std::float_t> reach;
		std::vector<structures::train_leg_s> legs;
		std::vector<structures::train_box_s> boxes[structures::train_vehicle_count];
		std::vector<structures::vec3_s> lamps[structures::train_vehicle_count];
		structures::mesh_s bodies[structures::train_vehicle_count]{};
		structures::mesh_s distant[structures::train_vehicle_count]{};
		structures::mesh_s wheel{};
		structures::mesh_s wheel_far{};
		structures::mat4_s placements[std::size(train_consist)]{};
		structures::mat4_s previous[std::size(train_consist)]{};
		structures::mat4_s posed[std::size(train_consist)]{};
		std::float_t offsets[std::size(train_consist)]{};
		std::uint32_t first_mover[std::size(train_consist)]{};
		builder_c shop;
		std::int32_t line = -1;
		std::float_t length = 0.0f;
		std::float_t extent = 0.0f;
		std::float_t cycle = 0.0f;
		std::double_t head = 0.0;
		std::double_t trailing = 0.0;
		std::float_t speed = 0.0f;
		std::float_t throttle = 0.0f;
		std::float_t phase = 0.0f;
		std::double_t clock = 0.0;
		std::double_t heard = 0.0;
		std::double_t placed = -1.0;
		std::int32_t joints[std::size(train_consist)][4]{};
		bool ready = false;
		bool history = false;
		bool squealed = false;
		bool halted = true;

		void create();
		void clear();
		void timetable();
		void shape(std::uint32_t vehicle);
		void build(std::uint32_t vehicle);
		void wheels();
		void mock(std::uint32_t vehicle);
		std::double_t travel(std::double_t time, std::float_t& rate);
		structures::vec3_s point(std::double_t along);
		structures::mat4_s pose(std::double_t time, std::uint32_t index);
		void place(std::double_t time);
		bool close(structures::vec3_s position, std::double_t time);
		structures::vec3_s velocity(std::uint32_t index, structures::vec3_s position, std::double_t time);
		std::uint32_t aboard(structures::vec3_s position, std::double_t time, structures::vec3_s& local);
		std::float_t strike(const structures::movement_state_s& state, std::double_t time, structures::vec3_s& shove);
		void advance(std::float_t delta);
		void update(std::float_t delta);
		void sounds(std::float_t delta);
		bool crossed(std::float_t moment, std::float_t from, std::float_t to);
		void submit();
		void glow(std::uint32_t index, std::float_t shine);
		std::float_t roll(std::double_t along);
	};

	extern train_c train;
}

//=====================================================================================
