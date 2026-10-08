
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class viewmodel_c
	{
	public:

		structures::character_s arms{};
		structures::character_s arms_left{};
		structures::pose_s pose{};
		structures::mat4_s gun_frames[structures::weapon_count]{};
		structures::mat4_s gun_placement{};
		structures::mat4_s bolt_world{};
		structures::mat4_s previous_bolt_world{};
		structures::mat4_s magazine_world{};
		structures::mat4_s previous_magazine_world{};
		structures::mesh_s tools[structures::item_count]{};
		structures::mesh_s bolts[structures::weapon_count]{};
		structures::mesh_s magazines[structures::weapon_count]{};
		structures::mesh_s arrow_mesh{};
		structures::mesh_s string_mesh{};
		structures::vec3_s nock{};
		builder_c tool_builder;
		std::vector<structures::mat4_s> globals;
		std::vector<structures::mat4_s> palette;
		std::vector<structures::mat4_s> previous_palette;
		structures::mat4_s world{};
		structures::mat4_s tool_world{};
		structures::mat4_s previous_tool_world{};
		structures::vec3_s eye{};
		structures::vec3_s wrist{};
		structures::vec3_s angles{};
		structures::vec3_s hand_fingers{};
		structures::vec3_s hand_palm{};
		structures::vec3_s hand_wrist{};
		std::int32_t upper_arm = -1;
		std::int32_t forearm = -1;
		std::int32_t hand = -1;
		std::int32_t fingers[5][3]{};
		std::int32_t left_upper = -1;
		std::int32_t left_forearm = -1;
		std::int32_t left_hand = -1;
		std::int32_t left_fingers[5][3]{};
		std::int32_t twists[2]{ -1, -1 };
		std::float_t spreads[2][5]{};
		std::float_t grips[structures::item_count][5][3]{};
		std::float_t support_grips[structures::weapon_count][5][3]{};
		structures::mat4_s grip_frames[structures::item_count]{};
		structures::mat4_s support_frames[structures::weapon_count]{};
		structures::mat4_s palm_frame{};
		structures::mat4_s left_palm_frame{};
		structures::vec3_s thumb_axis{ 0.0f, 1.0f, 0.0f };
		std::float_t thumb_swings[structures::item_count]{};
		std::float_t fit_swing = 0.0f;
		bool fitted[structures::item_count]{};
		bool support_fitted[structures::weapon_count]{};
		std::vector<structures::vec3_s> fit_triangles;
		std::float_t left_palm = 1.0f;
		std::uint32_t rags = 0u;
		bool two_handed = false;
		std::uint32_t shown_item = 0u;
		std::float_t upper_length = 0.0f;
		std::float_t lower_length = 0.0f;
		std::float_t hinge_sign = 1.0f;
		std::float_t left_hinge_sign = 1.0f;
		std::float_t equip = 0.0f;
		std::float_t sway_x = 0.0f;
		std::float_t sway_y = 0.0f;
		std::float_t clock = 0.0f;
		std::float_t sprint_blend = 0.0f;
		std::float_t air_blend = 0.0f;
		std::float_t land_kick = 0.0f;
		std::float_t turn_lag = 0.0f;
		std::float_t pitch_lag = 0.0f;
		std::float_t swim_blend = 0.0f;
		std::float_t swim_phase = 0.0f;
		bool stowed = false;
		std::float_t magazine_hold = 0.0f;
		std::float_t reaching = 0.0f;
		std::float_t charge_grab = 0.0f;
		std::float_t charge_pull = 0.0f;
		std::float_t inspect = -1.0f;
		std::float_t inspect_blend = 0.0f;
		std::float_t inspect_yaw = 0.0f;
		std::float_t inspect_pitch = 0.0f;
		std::float_t inspect_idle = 0.0f;
		std::float_t inspect_zoom = 1.0f;
		bool inspecting = false;
		std::uint32_t punch_side = 0u;
		bool punching = false;
		bool grounded = true;
		bool ready = false;
		const char* arms_source = viewmodel_character;
		bool visible = false;
		bool history = false;

		bool create();
		void destroy();
		bool build_arm(const structures::character_s& source, std::int32_t root, structures::character_s& target);
		void add_twist(structures::character_s& target, std::int32_t lower_bone, std::int32_t hand_bone, std::int32_t twist_bone);
		std::uint32_t dominant(const structures::skinned_vertex_s& vertex);
		structures::mat4_s bone_frame(const structures::character_s& target, std::int32_t bone);
		void wrap(structures::character_s& target, std::int32_t bone, std::float_t start, std::float_t end, std::uint32_t bands, bool children);
		void subdivide(structures::character_s& target);
		void blend(const structures::skinned_vertex_s& first, const structures::skinned_vertex_s& second, structures::skinned_vertex_s& target);
		void build_tools();
		void build_gun(std::uint32_t weapon);
		void gather(const structures::mat4_s& to_hand);
		structures::vec2_s settle(const structures::mat4_s& frame);
		structures::mat4_s knuckles(std::int32_t owner, std::int32_t first_bone, std::int32_t last_bone);
		void measure();
		void fit(bool left, bool swinging, std::float_t (&out)[5][3]);
		std::uint32_t contacts(std::int32_t owner, const std::int32_t (&chain)[3], const std::float_t (&curls)[3], std::float_t sign, std::uint32_t finger);
		void fit_item(std::uint32_t item, bool seated);
		void fit_support(std::uint32_t weapon);
		void support(structures::vec3_s view_target, structures::vec3_s fingers_view, structures::vec3_s palm_view, std::uint32_t gun);
		structures::vec3_s to_model(structures::vec3_s view);
		void stick(std::uint32_t material, std::float_t radius, std::float_t bottom, std::float_t top);
		void stone(const structures::model_s& source, structures::vec3_s size, structures::vec3_s center, std::float_t yaw);
		void update(std::float_t delta);
		void place_gun(std::uint32_t gun, structures::quat_s rotation, structures::vec3_s position);
		void pose_tool(std::uint32_t item);
		void showcase(std::uint32_t item, std::float_t delta);
		structures::mat4_s blend_rigid(const structures::mat4_s& from, const structures::mat4_s& to, std::float_t t);
		void sample(std::float_t phase);
		void solve(structures::vec3_s target, structures::vec3_s fingers_direction, structures::vec3_s palm);
		void pose_fists(std::float_t delta);
		void solve_arm(std::uint32_t side, const structures::hand_frame_s& frame);
		void fist(std::uint32_t side, std::float_t clench);
		void twist(std::uint32_t side);
		structures::hand_frame_s tilt(const structures::hand_frame_s& frame, structures::vec3_s turn);
		structures::hand_frame_s swim_frame(std::uint32_t side, std::float_t phase);
		std::float_t wave(std::float_t time, std::float_t seed);
		void orient(std::int32_t bone, structures::vec3_s x_axis, structures::vec3_s z_hint);
		void curl(std::uint32_t item);
		void compute_globals();
		void submit();
		void submit_item();
	};

	extern viewmodel_c viewmodel;
}

//=====================================================================================
