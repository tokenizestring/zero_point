
//=====================================================================================

#pragma once

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	constexpr auto game_title = "Zero Point";
	constexpr auto game_title_wide = L"Zero Point";
	constexpr auto window_class_name = L"zero_point_window";
	constexpr auto log_file_name = "zero_point.log";
	constexpr auto pak_file_name = "zero_point.pak";

	constexpr auto pi = 3.14159265358979323846f;
	constexpr auto two_pi = 6.28318530717958647692f;
	constexpr auto half_pi = 1.57079632679489661923f;
	constexpr auto epsilon = 0.00001f;

	constexpr auto degrees_to_radians(std::float_t a) { return a * (pi / 180.0f); }
	constexpr auto radians_to_degrees(std::float_t a) { return a * (180.0f / pi); }

	constexpr auto default_window_width = 1600;
	constexpr auto default_window_height = 900;
	constexpr auto minimum_window_width = 640;
	constexpr auto minimum_window_height = 360;

	constexpr auto swapchain_buffer_count = 3u;
	constexpr auto swapchain_format = DXGI_FORMAT_R8G8B8A8_UNORM;

	constexpr auto key_count = 256u;
	constexpr auto text_input_capacity = 64u;

	constexpr auto canvas_max_quads = 32768u;
	constexpr auto canvas_max_vertices = canvas_max_quads * 4u;
	constexpr auto canvas_max_indices = canvas_max_quads * 6u;
	constexpr auto canvas_scissor_depth = 16u;

	constexpr auto font_atlas_width = 4096u;
	constexpr auto font_atlas_height = 2048u;
	constexpr auto font_source_size = 48;
	constexpr auto font_sdf_spread = 6;
	constexpr auto font_first_glyph = 32u;
	constexpr auto font_last_glyph = 255u;
	constexpr auto font_glyph_count = font_last_glyph - font_first_glyph + 1u;
	constexpr auto font_padding = 2;
	constexpr auto font_supersample = 4;

	constexpr auto pak_magic = 0x314B505Au;
	constexpr auto pak_version = 1u;
	constexpr auto pak_name_length = 48u;
	constexpr auto pak_alignment = 64u;
	constexpr auto material_name_length = 48u;
	constexpr auto model_part_name_length = 48u;
	constexpr auto material_texture_size = 1024u;
	constexpr auto sky_sh_coefficients = 9u;
	constexpr auto max_materials = 256u;
	constexpr auto terrain_size = 4608.0f;
	constexpr auto terrain_resolution = 4609u;
	constexpr auto terrain_texture_size = 4608u;
	constexpr auto terrain_origin = -2304.0f;
	constexpr auto terrain_layer_count = 16u;
	constexpr auto terrain_splat_count = 4u;
	constexpr auto biome_cell = 4.0f;
	constexpr auto biome_size = 1152u;
	constexpr auto ground_cell = 2.0f;
	constexpr auto ground_size = 2304u;
	constexpr auto field_spacing = 76.0f;
	constexpr auto field_bank = 1.7f;
	constexpr auto terrain_patch_cells = 36u;
	constexpr auto terrain_lod_levels = 8u;
	constexpr auto terrain_lod_base_range = 80.0f;
	constexpr auto terrain_morph_start = 0.7f;
	constexpr auto terrain_maximum_patches = 2048u;
	constexpr auto sea_level = 0.0f;
	constexpr auto maximum_models = 512u;
	constexpr auto inventory_slots = 24u;
	constexpr auto hotbar_slots = 6u;
	constexpr auto total_slots = inventory_slots + hotbar_slots;
	constexpr auto crafting_queue_size = 8u;
	constexpr auto notification_count = 6u;
	constexpr auto notification_time = 3.5f;
	constexpr auto maximum_health = 100.0f;
	constexpr auto maximum_calories = 500.0f;
	constexpr auto maximum_hydration = 250.0f;
	constexpr auto starting_calories = 140.0f;
	constexpr auto starting_hydration = 90.0f;
	constexpr auto calorie_burn = 0.085f;
	constexpr auto hydration_burn = 0.13f;
	constexpr auto maximum_crops = 256u;
	constexpr auto farm_reach = 3.2f;
	constexpr auto farm_spacing = 0.85f;
	constexpr auto farm_water_time = 540.0f;
	constexpr auto farm_wither_time = 240.0f;
	constexpr auto farm_rot_time = 360.0f;
	constexpr auto well_irrigation = 9.0f;
	constexpr auto well_drink = 45.0f;
	constexpr auto spring_drink = 30.0f;
	constexpr auto spring_spacing = 250.0f;
	constexpr auto sea_drink = 10.0f;
	constexpr auto sea_sickness = 6.0f;
	constexpr auto campfire_cook_time = 7.0f;
	constexpr auto campfire_fuel_time = 7.0f;
	constexpr auto starvation_damage = 0.35f;
	constexpr auto natural_regeneration = 0.12f;
	constexpr auto climate_interval = 0.5f;
	constexpr auto climate_mean = 15.0f;
	constexpr auto climate_swing = 7.0f;
	constexpr auto climate_peak_hour = 14.0f;
	constexpr auto climate_cloud_chill = 4.0f;
	constexpr auto climate_rain_chill = 5.0f;
	constexpr auto climate_storm_chill = 3.0f;
	constexpr auto climate_wet_chill = 8.0f;
	constexpr auto climate_sea = 13.0f;
	constexpr auto climate_campfire = 24.0f;
	constexpr auto climate_furnace = 16.0f;
	constexpr auto climate_torch = 5.0f;
	constexpr auto climate_fire_range = 5.0f;
	constexpr auto climate_roof_reach = 16.0f;
	constexpr auto climate_adapt = 1.5f;
	constexpr auto climate_soak = 0.03f;
	constexpr auto climate_dry = 0.006f;
	constexpr auto climate_fire_dry = 0.002f;
	constexpr auto climate_cold = 5.0f;
	constexpr auto climate_freezing = 0.0f;
	constexpr auto climate_hot = 38.0f;
	constexpr auto climate_cold_hunger = 0.06f;
	constexpr auto climate_freeze_damage = 0.02f;
	constexpr auto interact_range = 2.4f;
	constexpr auto container_restock = 420.0f;
	constexpr auto torch_flame_rate = 90.0f;
	constexpr auto container_slots = 12u;
	constexpr auto container_address = 100u;
	constexpr auto furnace_fuel_slot = 0u;
	constexpr auto furnace_first_input = 1u;
	constexpr auto furnace_last_input = 3u;
	constexpr auto furnace_first_output = 4u;
	constexpr auto furnace_smelt_time = 1.6f;
	constexpr auto furnace_fuel_time = 3.0f;
	constexpr auto building_cell = 3.0f;
	constexpr auto building_height = 3.0f;
	constexpr auto building_range = 5.5f;
	constexpr auto building_snap = 4.5f;
	constexpr auto maximum_structures = 1024u;
	constexpr auto hostile_structure_damage = 16.0f;
	constexpr auto audio_voices = 40u;
	constexpr auto audio_master_volume = 0.85f;
	constexpr auto audio_rolloff = 4.0f;
	constexpr auto audio_audible_range = 70.0f;
	constexpr auto audio_underwater_volume = 0.55f;
	constexpr auto audio_underwater_muffle = 0.09f;
	constexpr auto audio_underwater_duck = 0.12f;
	constexpr auto audio_shelter_muffle = 0.2f;
	constexpr auto audio_shelter_volume = 0.6f;
	constexpr auto audio_gun_voices = 48u;
	constexpr auto audio_gun_range = 1500.0f;
	constexpr auto audio_gun_reference = 14.0f;
	constexpr auto audio_speed_of_sound = 343.0f;
	constexpr auto audio_echo_rays = 16u;
	constexpr auto audio_echo_reach = 720.0f;
	constexpr auto audio_echo_step = 6.0f;
	constexpr auto audio_echo_wall_reach = 140.0f;
	constexpr auto audio_echo_count = 2u;
	constexpr auto audio_echo_strength = 0.55f;
	constexpr auto audio_echo_cutoff = 1400.0f;
	constexpr auto audio_echo_rise = 8.0f;
	constexpr auto audio_echo_cache = 0.6f;
	constexpr auto audio_reverb_send = 0.3f;
	constexpr auto audio_reverb_volume = 0.9f;
	constexpr auto audio_acoustic_interval = 0.5f;
	constexpr auto audio_occlusion_wall = 0.65f;
	constexpr auto audio_occlusion_loss = 0.5f;
	constexpr auto audio_occlusion_muffle = 0.22f;
	constexpr auto audio_occlusion_samples = 40u;
	constexpr auto audio_crack_radius = 9.0f;
	constexpr auto audio_crack_minimum = 18.0f;
	constexpr auto audio_whiz_radius = 2.6f;
	constexpr auto audio_bullet_speed = 760.0f;
	constexpr auto audio_impact_range = 28.0f;
	constexpr auto audio_event_near = 16.0f;
	constexpr auto audio_event_mid = 38.0f;
	constexpr auto audio_event_far = 70.0f;
	constexpr auto audio_rear_volume = 0.82f;
	constexpr auto audio_rear_muffle = 0.32f;
	constexpr auto audio_spatial_send = 0.2f;
	constexpr auto audio_drone_range = 1800.0f;
	constexpr auto audio_drone_floor = 0.002f;
	constexpr auto audio_listener_speed = 60.0f;
	constexpr auto audio_tail_voices = 12u;
	constexpr auto audio_tail_reference = 70.0f;
	constexpr auto audio_mechanism_range = 25.0f;
	constexpr auto audio_casing_range = 30.0f;
	constexpr auto audio_casing_delay = 0.38f;
	constexpr auto audio_deafen_range = 9.0f;
	constexpr auto audio_ring_threshold = 0.3f;
	constexpr auto audio_ring_decay = 0.045f;
	constexpr auto audio_ring_volume = 0.3f;
	constexpr auto audio_ring_muffle = 0.42f;
	constexpr auto audio_room_deafening = 2.2f;
	constexpr auto viewmodel_equip_time = 0.4f;
	constexpr auto viewmodel_grip_forward = 0.085f;
	constexpr auto viewmodel_grip_palm = 0.03f;
	constexpr auto viewmodel_sway = 0.00045f;
	constexpr auto viewmodel_arm_subdivisions = 0u;
	constexpr auto viewmodel_wrap_segments = 24u;
	constexpr auto chart_size = 2048u;
	constexpr auto chart_contour_interval = 10.0f;
	constexpr auto chart_margin = 1.14f;
	constexpr auto chart_forest_cell = 11;
	constexpr auto chart_grid_cells = 8u;
	constexpr auto chart_pin_count = 5u;
	constexpr auto chart_rail_step = 4u;
	constexpr auto chart_pin_reach = 16.0f;
	constexpr auto compass_span = 75.0f;
	constexpr auto compass_focus = 20.0f;
	constexpr auto compass_width = 560.0f;
	constexpr auto weapon_bolt_delay = 0.3f;
	constexpr auto weapon_cycle_time = 0.8f;
	constexpr auto weapon_scope_threshold = 0.9f;
	constexpr auto water_grid = 200u;
	constexpr auto water_extent = 6000.0f;
	constexpr auto water_warp = 2.6f;
	constexpr auto water_snap = 4.0f;
	constexpr auto water_steepness = 0.62f;
	constexpr auto water_normal_size = 512u;
	constexpr auto water_underwater_margin = 0.35f;
	constexpr auto grass_near_spacing = 0.42f;
	constexpr auto grass_near_radius = 30.0f;
	constexpr auto grass_far_spacing = 1.05f;
	constexpr auto grass_far_radius = 95.0f;
	constexpr auto grass_far_inner = 26.0f;
	constexpr auto grass_size = 0.9f;
	constexpr auto grass_push_radius = 1.1f;
	constexpr auto grass_card_rows = 4u;
	constexpr auto grass_cards = 4u;
	constexpr auto grass_card_offset = 0.12f;
	constexpr auto grass_sprite_count = 4u;
	constexpr auto grass_splat_slot = 22u;
	constexpr auto fir_variant_count = 6u;
	constexpr auto dead_tree_variant_count = 3u;
	constexpr auto foliage_cell_size = 64.0f;
	constexpr auto foliage_maximum_instances = 65536u;
	constexpr auto foliage_maximum_species = 192u;
	constexpr auto island_spawn_rays = 48u;
	constexpr auto route_cell = 4.0f;
	constexpr auto route_cells = 1152u;
	constexpr auto route_clear_margin = 4.0f;
	constexpr auto route_building_gap = 13.0f;
	constexpr auto route_prop_gap = 2.5f;
	constexpr auto hamlet_attempts = 12u;
	constexpr auto hamlet_turn = 0.4f;
	constexpr auto rail_gauge = 1.435f;
	constexpr auto rail_panel_near = 42.0f;
	constexpr auto rail_panel_far = 1400.0f;
	constexpr auto rail_panel_shadow = 70.0f;
	constexpr auto rail_panel_weeds = 0.22f;
	constexpr auto rail_panel_sway = -1.0f;
	constexpr auto rail_sleeper_spacing = 0.7f;
	constexpr auto rail_ballast_top = 0.26f;
	constexpr auto road_lift = 0.05f;
	constexpr auto road_lift_step = 0.003f;
	constexpr auto road_tile = 3.0f;
	constexpr auto road_skirt = 0.45f;
	constexpr auto road_skirt_drop = 0.16f;
	constexpr auto crossing_inset = 0.06f;
	constexpr auto crossing_reach = 1.2f;
	constexpr auto crossing_grade = 0.06f;
	constexpr auto crossing_search = 14.0f;
	constexpr auto crossing_overhang = 0.9f;
	constexpr auto crossing_board_width = 0.29f;
	constexpr auto crossing_board_depth = 0.14f;
	constexpr auto crossing_board_sink = 0.015f;
	constexpr auto junction_reach = 0.5f;
	constexpr std::float_t crossing_boards[6] = { -1.0f, -0.45f, -0.15f, 0.15f, 0.45f, 1.0f };
	constexpr auto crate_far_distance = 150.0f;
	constexpr auto crate_shadow_distance = 50.0f;
	constexpr auto building_near_distance = 95.0f;
	constexpr auto building_far_distance = 2600.0f;
	constexpr auto building_shadow_distance = 600.0f;
	constexpr auto foliage_fade_band = 8.0f;
	constexpr auto foliage_report_triangles = 150000ull;
	constexpr auto fir_impostor_distance = 110.0f;
	constexpr auto fir_near_distance = 45.0f;
	constexpr auto snag_near_distance = 50.0f;
	constexpr auto rock_near_distance = 40.0f;
	constexpr auto boulder_near_distance = 25.0f;
	constexpr auto shore_rock_near_distance = 70.0f;
	constexpr auto fir_shadow_distance = 170.0f;
	constexpr auto profiler_latency = 5u;
	constexpr auto profiler_warmup = 40u;
	constexpr auto bone_name_length = 48u;
	constexpr auto maximum_bones = 128u;
	constexpr auto maximum_palette_bones = 16384u;
	constexpr auto bone_rows_slot = 20u;
	constexpr auto terrain_height_slot = 21u;
	constexpr auto clip_frame_rate = 30.0f;
	constexpr auto character_facing_offset = pi;
	constexpr auto character_blend_sharpness = 10.0f;
	constexpr auto character_turn_threshold = 1.05f;
	constexpr auto character_turn_rate = 7.0f;
	constexpr auto character_strafe_limit = 1.3f;
	constexpr auto character_backpedal_angle = 1.95f;
	constexpr const char* character_twist_bones[] = { "Bip01 Spine", "Bip01 Spine1", "Bip01 Spine2", "Bip01 Neck", "Bip01 Head" };
	constexpr const char* character_sit_bones[] = { "Bip01 L Thigh", "Bip01 R Thigh", "Bip01 L Calf", "Bip01 R Calf", "Bip01 L UpperArm", "Bip01 R UpperArm", "Bip01 L Forearm", "Bip01 R Forearm" };
	constexpr std::float_t character_sit_angles[] = { 1.45f, 1.45f, -1.5f, -1.5f, 0.55f, 0.55f, 0.75f, 0.75f };
	constexpr std::float_t character_twist_shares[] = { 0.15f, 0.2f, 0.25f, 0.2f, 0.2f };
	constexpr std::float_t character_blade_shares[] = { 0.25f, 0.35f, 0.4f, 0.0f, -1.0f };
	constexpr const char* character_roster[] = { "military_male_01", "military_male_04", "police_male_02", "male_adult_05", "construction_male_01" };
	constexpr auto clip_idle = "m_idle_neutral_01";
	constexpr auto clip_walk = "m_walk_neutral_01";
	constexpr auto clip_run = "m_run_neutral";
	constexpr auto clip_sprint = "m_run_fast_01";
	constexpr auto clip_crouch = "m_crouch_idle";
	constexpr auto maximum_actors = 560u;
	constexpr auto actor_twist_yaw_limit = 1.4f;
	constexpr auto actor_twist_pitch_limit = 1.1f;
	constexpr auto actor_air_phase = 0.3f;
	constexpr auto actor_air_crouch = 0.35f;
	constexpr auto hostile_count = 40u;
	constexpr auto hostile_health = 100.0f;
	constexpr auto hostile_sight = 34.0f;
	constexpr auto hostile_hearing = 7.0f;
	constexpr auto hostile_forget = 70.0f;
	constexpr auto hostile_active_range = 170.0f;
	constexpr auto hostile_attack_range = 1.55f;
	constexpr auto hostile_attack_reach = 2.1f;
	constexpr auto hostile_attack_damage = 13.0f;
	constexpr auto hostile_attack_time = 0.85f;
	constexpr auto hostile_attack_cooldown = 1.5f;
	constexpr auto hostile_pallor = 0.72f;
	constexpr auto corpse_time = 120.0f;
	constexpr auto actor_radius = 0.34f;
	constexpr auto actor_height = 1.8f;
	constexpr std::float_t actor_avoid_angles[] = { 0.8f, -0.8f, 1.6f, -1.6f };
	constexpr const char* actor_rig_bones[] = { "Bip01 R UpperArm", "Bip01 R Forearm", "Bip01 R Hand", "Bip01 L UpperArm", "Bip01 L Forearm", "Bip01 L Hand" };
	constexpr const char* first_person_hidden_bones[] = { "Bip01 Head", "Bip01 R UpperArm", "Bip01 L UpperArm" };
	constexpr auto first_person_body_back = 0.12f;
	constexpr auto first_person_collapse = 0.001f;
	constexpr auto first_person_clearance = 0.32f;
	constexpr auto third_person_distance = 2.6f;
	constexpr auto third_person_side = 0.55f;
	constexpr auto third_person_height = 0.15f;

	constexpr auto camera_near = 0.04f;
	constexpr auto viewmodel_near = 0.01f;
	constexpr auto viewmodel_depth_min = 0.97f;
	constexpr auto shadow_cascade_count = 4u;
	constexpr auto shadow_reduced_resolution = 2048.0f;
	constexpr auto shadow_near_resolution = 2048.0f;
	constexpr auto shadow_depth_range = 400.0f;
	constexpr auto atmosphere_width = 1024u;
	constexpr auto atmosphere_height = 512u;
	constexpr auto atmosphere_strips = 8u;
	constexpr auto atmosphere_refresh = 1.0f;
	constexpr auto atmosphere_planet = 6360000.0f;
	constexpr auto atmosphere_top = 6420000.0f;
	constexpr auto sun_irradiance = 12.0f;
	constexpr auto moon_irradiance = 0.1f;
	constexpr auto atmosphere_bounce = 0.5f;
	constexpr auto atmosphere_coverage = 0.36f;
	constexpr auto cloud_shape_size = 128u;
	constexpr auto cloud_detail_size = 32u;
	constexpr auto cloud_weather_size = 512u;
	constexpr auto cloud_noise_group = 4u;
	constexpr auto cloud_shadow_size = 256u;
	constexpr auto cloud_shadow_extent = 12000.0f;
	constexpr auto cloud_bottom = 1400.0f;
	constexpr auto cloud_top = 3800.0f;
	constexpr auto cloud_storm_bottom = 850.0f;
	constexpr auto cloud_extinction = 0.035f;
	constexpr auto cloud_shadow_floor = 0.22f;
	constexpr auto cloud_evolve = 0.35f;
	constexpr auto cloud_light = 1.0f;
	constexpr auto cloud_ambient = 1.0f;
	constexpr auto cloud_wind_x = 9.0f;
	constexpr auto cloud_wind_z = 4.0f;
	constexpr std::float_t cloud_steps[5] = { 0.0f, 32.0f, 40.0f, 56.0f, 80.0f };
	constexpr auto sun_tilt = 0.55f;
	constexpr auto moon_tilt = 0.35f;
	constexpr auto day_length = 2400.0f;
	constexpr auto night_length = 720.0f;
	constexpr auto sunrise_hours = 6.0f;
	constexpr auto sunset_hours = 18.0f;
	constexpr auto sky_base_cube_size = 512u;
	constexpr auto sky_prefilter_size = 256u;
	constexpr auto sky_prefilter_mips = 7u;
	constexpr auto brdf_lut_size = 128u;
	constexpr auto compute_group_size = 8u;
	constexpr auto gbuffer_count = 5u;
	constexpr auto halton_length = 16u;
	constexpr auto bloom_levels = 6u;
	constexpr auto bloom_upsample_weight = 0.6f;
	constexpr auto bloom_mix = 0.04f;
	constexpr auto histogram_bins = 64u;
	constexpr auto exposure_key = -2.47f;
	constexpr auto exposure_minimum_log = -10.0f;
	constexpr auto exposure_lowest = -4.0f;
	constexpr auto exposure_highest = 3.2f;
	constexpr auto exposure_log_range = 18.0f;

	constexpr auto collision_epsilon = 0.002f;
	constexpr auto collision_cell_size = 4.0f;
	constexpr auto trace_piece = 8.0f;
	constexpr auto audio_occlusion_reach = 60.0f;
	constexpr auto audio_drone_recheck = 0.2f;
	constexpr auto terrain_clip_planes = 16u;
	constexpr auto trace_bumps = 4u;

	constexpr auto player_half_width = 0.34f;
	constexpr auto player_height = 1.82f;
	constexpr auto player_crouch_height = 1.24f;
	constexpr auto player_eye_height = 1.64f;
	constexpr auto player_crouch_eye_height = 1.08f;
	constexpr auto step_length_base = 0.62f;
	constexpr auto step_length_scale = 0.14f;
	constexpr auto move_speed_run = 4.6f;
	constexpr auto move_speed_sprint = 6.8f;
	constexpr auto move_speed_crouch = 2.1f;
	constexpr auto move_speed_aim = 0.56f;
	constexpr auto move_speed_walk = 0.5f;
	constexpr auto move_sprint_side = 0.33f;
	constexpr auto move_accelerate = 42.0f;
	constexpr auto move_decelerate = 30.0f;
	constexpr auto move_air_control = 2.4f;
	constexpr auto move_gravity = 19.0f;
	constexpr auto move_terminal_speed = 54.0f;
	constexpr auto move_jump_velocity = 6.4f;
	constexpr auto move_jump_cooldown = 0.45f;
	constexpr auto move_land_delay = 0.2f;
	constexpr auto move_land_slow = 0.45f;
	constexpr auto move_land_soft = 3.0f;
	constexpr auto move_land_hard = 7.0f;
	constexpr auto move_uphill_slow = 0.35f;
	constexpr auto move_step_height = 0.5f;
	constexpr auto move_walkable = 0.66f;
	constexpr auto move_ground_probe = 0.06f;
	constexpr auto move_ground_leave = 0.5f;
	constexpr auto move_ground_lift = 0.02f;
	constexpr auto move_stuck_distance = 0.01f;
	constexpr auto move_stuck_time = 0.25f;
	constexpr auto move_crouch_rate = 5.5f;
	constexpr auto move_step_smooth = 0.02f;
	constexpr auto move_clip_planes = 6u;
	constexpr auto move_overclip = 1.001f;
	constexpr auto water_wade_jump = 0.45f;
	constexpr auto water_wade_depth = 0.3f;
	constexpr auto water_swim_depth = 1.35f;
	constexpr auto water_swim_exit = 1.15f;
	constexpr auto water_wade_slow = 0.42f;
	constexpr auto water_float_eye = 0.12f;
	constexpr auto water_calm_depth = 9.0f;
	constexpr auto water_calm_floor = 0.12f;
	constexpr auto water_splash_speed = 2.5f;
	constexpr auto swim_speed = 2.2f;
	constexpr auto swim_speed_sprint = 3.3f;
	constexpr auto swim_accelerate = 5.5f;
	constexpr auto swim_drag = 2.4f;
	constexpr auto swim_buoyancy = 3.0f;
	constexpr auto swim_spring = 7.0f;
	constexpr auto swim_dive_pitch = 0.35f;
	constexpr auto swim_stroke_length = 1.6f;
	constexpr auto breath_seconds = 30.0f;
	constexpr auto breath_recover = 0.4f;
	constexpr auto drown_damage = 10.0f;
	constexpr auto fall_damage_start = 12.5f;
	constexpr auto fall_damage_lethal = 24.0f;
	constexpr auto probe_spacing = 1.0f;
	constexpr auto probe_rays = 256u;
	constexpr auto probe_bounces = 2u;
	constexpr auto probe_cache_version = 4u;
	constexpr auto bvh_leaf_size = 4u;
	constexpr auto bvh_bins = 12u;
	constexpr auto maximum_lights = 1024u;
	constexpr auto light_tile_size = 16u;
	constexpr auto maximum_tile_lights = 128u;
	constexpr auto headshot_multiplier = 2.0f;
	constexpr auto player_max_health = 200.0f;
	constexpr auto regen_delay = 5.0f;
	constexpr auto regen_rate = 20.0f;
	constexpr auto regen_cap = 100.0f;
	constexpr auto melee_damage = 125.0f;
	constexpr auto melee_range = 2.0f;
	constexpr auto melee_time = 0.65f;
	constexpr auto bullet_range = 500.0f;
	constexpr auto sprint_to_fire_time = 0.2f;
	constexpr auto maximum_particles = 4096u;
	constexpr auto maximum_decals = 1536u;
	constexpr auto decal_atlas_columns = 8u;
	constexpr auto decal_rough = 0.92f;
	constexpr auto decal_gloss = 0.16f;
	constexpr auto decal_distance_fade = 0.2f;
	constexpr auto mark_capacity = 32768u;
	constexpr auto mark_cell = 32.0f;
	constexpr auto mark_cells = 144u;
	constexpr auto mark_interest = 2;
	constexpr auto mark_bytes = 14u;
	constexpr auto marks_per_message = 36u;
	constexpr auto mark_queue_room = 96u;
	constexpr auto mark_cells_per_flush = 3u;
	constexpr auto mark_backlog = 1024u;
	constexpr auto mark_plane_scale = 16777216.0f / 4608.0f;
	constexpr auto mark_height_floor = -16.0f;
	constexpr auto mark_height_scale = 256.0f;
	constexpr auto mark_age_step = 8.0;
	constexpr auto mark_guess_life = 3.0;
	constexpr auto mark_guess_reach = 0.12f;
	constexpr auto mark_sweep = 512u;
	constexpr auto mark_lift = 0.01f;
	constexpr auto mark_power_full = 90.0f;
	constexpr auto mark_wet_steps = 14u;
	constexpr auto mark_foot_offset = 0.1f;
	constexpr auto mark_foot_follow = 0.5f;
	constexpr auto mark_tread_speed = 0.8f;
	constexpr auto mark_tread_slope = 0.72f;
	constexpr auto mark_blood_reach = 2.6f;
	constexpr auto mark_blood_exit = 0.35f;
	constexpr auto mark_blood_drop = 2.5f;
	constexpr auto mark_blood_scatter = 0.3f;
	constexpr auto mark_save_limit = 8192u;
	constexpr auto maximum_tracers = 256u;
	constexpr auto tick_rate = 60.0f;
	constexpr auto tick_interval = 1.0f / tick_rate;
	constexpr auto maximum_ticks_per_frame = 6u;
	constexpr auto default_mouse_sensitivity = 0.0021f;
	constexpr auto server_log_file_name = "zero_point_server.log";
	constexpr auto remote_character = "survivor_male";
	constexpr auto nude_character = "survivor_male_nude";
	constexpr auto server_executable_name = "zero_point_server.exe";
	constexpr auto net_protocol_id = 0x314E505Au;
	constexpr auto net_protocol_version = 10u;
	constexpr auto net_time_scale = 4096.0;
	constexpr auto net_time_window = 1.0;
	constexpr auto net_time_lead = 0.1;
	constexpr auto shader_time_wrap = 32768.0;
	constexpr auto net_default_port = 28015u;
	constexpr auto net_browse_ports = 4u;
	constexpr auto net_maximum_players = 500u;
	constexpr auto net_packet_bytes = 1400u;
	constexpr auto net_receive_bytes = 2048u;
	constexpr auto net_server_tick_rate = 30.0f;
	constexpr auto net_snapshot_rate = 20.0f;
	constexpr auto net_hibernate_step = 0.5f;
	constexpr auto net_delta_limit = 1.0f;
	constexpr auto net_input_redundancy = 6u;
	constexpr auto net_timeout = 12.0f;
	constexpr auto net_connect_interval = 0.5f;
	constexpr auto net_connect_attempts = 20u;
	constexpr auto net_query_interval = 1.5f;
	constexpr auto net_reliable_bytes = 512u;
	constexpr auto net_reliable_capacity = 256u;
	constexpr auto net_reliable_budget = 1100u;
	constexpr auto net_reliable_per_packet = 16u;
	constexpr auto net_sent_history = 256u;
	constexpr auto net_interest_radius = 420.0f;
	constexpr auto net_snapshot_players = 48u;
	constexpr auto net_interpolation_delay = 0.1f;
	constexpr auto net_remote_timeout = 2.5f;
	constexpr auto net_command_queue = 64u;
	constexpr auto net_commands_per_tick = 8u;
	constexpr auto net_command_budget = 0.5f;
	constexpr auto net_inventory_refresh = 2.0f;
	constexpr auto net_structures_per_message = 14u;
	constexpr auto net_crops_per_message = 24u;
	constexpr auto net_name_range = 40.0f;
	constexpr auto net_footstep_range = 45.0f;
	constexpr auto weather_drop_count = 18000u;
	constexpr auto weather_splash_grid = 32u;
	constexpr auto weather_bolt_segments = 40u;
	constexpr auto weather_bolt_life = 0.45f;
	constexpr auto weather_bolt_visible = 3600.0f;
	constexpr auto weather_bolt_brightness = 160.0f;
	constexpr auto shaft_decay = 0.965f;
	constexpr auto shaft_reach = 0.9f;
	constexpr auto shaft_focus = 6.0f;
	constexpr auto shaft_strength = 0.06f;
	constexpr auto weather_blend_rate = 0.012f;
	constexpr auto weather_wet_rate = 0.02f;
	constexpr auto weather_dry_rate = 0.004f;
	constexpr auto weather_exposure_cloud = 0.3f;
	constexpr auto weather_exposure_storm = 0.55f;
	constexpr auto roof_grid = 64u;
	constexpr auto roof_cell = 0.75f;
	constexpr auto roof_budget = 256u;
	constexpr auto roof_reach = 40.0f;
	constexpr auto roof_open = -100000.0f;
	constexpr auto net_bags_per_message = 9u;
	constexpr auto loot_bag_life = 600.0f;
	constexpr auto maximum_bags = 96u;
	constexpr auto net_crop_refresh = 2.0f;
	constexpr auto net_start_hours = 8.5f;
	constexpr auto world_save_interval = 60.0f;
	constexpr auto world_save_name = "zero_point_world.sav";
	constexpr std::uint32_t world_save_magic = 0x5A505744u;
	constexpr std::uint32_t world_save_version = 9u;
	constexpr std::uint32_t world_save_marks = 8u;
	constexpr std::uint32_t world_save_layout = 9u;
	constexpr std::uint32_t world_save_oldest = 7u;
	constexpr std::uint32_t world_save_tiers = 5u;
	constexpr std::uint32_t world_save_claims = 5u;
	constexpr std::uint32_t world_save_locks = 6u;
	constexpr auto lock_shock = 8.0f;
	constexpr auto lock_cooldown = 1.0f;
	constexpr auto net_rewind_samples = 32u;
	constexpr auto net_rewind_limit = 0.5f;
	constexpr auto net_shot_range = 900.0f;
	constexpr auto net_shot_bytes = 16u;
	constexpr auto net_snapshot_shots = 24u;
	constexpr auto net_tracer_range = 250.0f;
	constexpr auto player_hit_radius = 0.3f;
	constexpr auto player_head_zone = 0.3f;
	constexpr auto player_leg_zone = 0.85f;
	constexpr auto weapon_headshot_scale = 2.0f;
	constexpr auto weapon_leg_scale = 0.75f;
	constexpr auto weapon_punch_limit = 0.6f;
	constexpr auto weapon_punch_hold = 0.14f;
	constexpr auto weapon_punch_recover = 5.0f;
	constexpr auto weapon_punch_rise = 20.0f;
	constexpr auto weapon_aim_rate = 6.0f;
	constexpr auto weapon_equip_time = 0.4f;
	constexpr auto weapon_dry_delay = 0.3f;
	constexpr auto weapon_seed_salt = 0x7F4A7C15u;
	constexpr auto net_bot_respawn = 6.0f;
	constexpr auto net_player_respawn = 600.0f;
	constexpr auto net_history_size = 256u;
	constexpr auto net_grid_cell = 64.0f;
	constexpr auto net_grid_size = 80u;
	constexpr auto net_name_length = 32u;
	constexpr auto net_name_copies = 16u;
	constexpr auto net_password_length = 32u;
	constexpr auto net_server_name_length = 64u;
	constexpr auto net_chat_length = 120u;
	constexpr auto net_position_scale = 12.0f;
	constexpr auto net_velocity_scale = 10.0f;
	constexpr auto net_error_decay = 12.0f;
	constexpr auto net_snap_distance = 3.0f;
	constexpr auto net_status_interval = 60.0f;
	constexpr auto net_bot_think = 2.5f;
	constexpr auto net_spawn_spread = 14.0f;
	constexpr auto net_chat_lines = 8u;
	constexpr auto net_chat_time = 12.0f;
	constexpr auto net_input_rate = 60.0f;
	constexpr auto net_clock_snap = 0.25;
	constexpr auto net_clock_pull = 0.05;
	constexpr auto net_browse_interval = 3.0f;
	constexpr auto net_report_interval = 2.0f;
	constexpr auto net_priority_near = 12.0f;
	constexpr auto net_early_status_time = 35.0;
	constexpr auto net_player_bytes = 18u;
	constexpr auto socket_buffer_bytes = 4 * 1024 * 1024;
	constexpr DWORD socket_ignore_reset = 0x9800000Cu;

	namespace structures
	{
		struct vec2_s
		{
			std::float_t x, y;

			vec2_s operator+(const vec2_s& r) const { return { x + r.x, y + r.y }; }
			vec2_s operator-(const vec2_s& r) const { return { x - r.x, y - r.y }; }
			vec2_s operator*(const vec2_s& r) const { return { x * r.x, y * r.y }; }
			vec2_s operator/(const vec2_s& r) const { return { x / r.x, y / r.y }; }
			vec2_s operator*(std::float_t s) const { return { x * s, y * s }; }
			vec2_s operator/(std::float_t s) const { return { x / s, y / s }; }
			vec2_s operator-() const { return { -x, -y }; }
			void operator+=(const vec2_s& r) { x += r.x; y += r.y; }
			void operator-=(const vec2_s& r) { x -= r.x; y -= r.y; }
			void operator*=(std::float_t s) { x *= s; y *= s; }
		};
		/*
		//=====================================================================================
		*/
		struct vec3_s
		{
			std::float_t x, y, z;

			vec3_s operator+(const vec3_s& r) const { return { x + r.x, y + r.y, z + r.z }; }
			vec3_s operator-(const vec3_s& r) const { return { x - r.x, y - r.y, z - r.z }; }
			vec3_s operator*(const vec3_s& r) const { return { x * r.x, y * r.y, z * r.z }; }
			vec3_s operator/(const vec3_s& r) const { return { x / r.x, y / r.y, z / r.z }; }
			vec3_s operator*(std::float_t s) const { return { x * s, y * s, z * s }; }
			vec3_s operator/(std::float_t s) const { return { x / s, y / s, z / s }; }
			vec3_s operator-() const { return { -x, -y, -z }; }
			void operator+=(const vec3_s& r) { x += r.x; y += r.y; z += r.z; }
			void operator-=(const vec3_s& r) { x -= r.x; y -= r.y; z -= r.z; }
			void operator*=(const vec3_s& r) { x *= r.x; y *= r.y; z *= r.z; }
			void operator*=(std::float_t s) { x *= s; y *= s; z *= s; }
			void operator/=(std::float_t s) { x /= s; y /= s; z /= s; }
			std::float_t& operator[](std::uint32_t i) { return (&x)[i]; }
			std::float_t operator[](std::uint32_t i) const { return (&x)[i]; }
		};
		/*
		//=====================================================================================
		*/
		struct vec4_s
		{
			std::float_t x, y, z, w;

			vec4_s operator+(const vec4_s& r) const { return { x + r.x, y + r.y, z + r.z, w + r.w }; }
			vec4_s operator-(const vec4_s& r) const { return { x - r.x, y - r.y, z - r.z, w - r.w }; }
			vec4_s operator*(const vec4_s& r) const { return { x * r.x, y * r.y, z * r.z, w * r.w }; }
			vec4_s operator*(std::float_t s) const { return { x * s, y * s, z * s, w * s }; }
			vec4_s operator/(std::float_t s) const { return { x / s, y / s, z / s, w / s }; }
			void operator+=(const vec4_s& r) { x += r.x; y += r.y; z += r.z; w += r.w; }
			void operator*=(std::float_t s) { x *= s; y *= s; z *= s; w *= s; }
			vec3_s xyz() const { return { x, y, z }; }
			std::float_t& operator[](std::uint32_t i) { return (&x)[i]; }
			std::float_t operator[](std::uint32_t i) const { return (&x)[i]; }
		};
		/*
		//=====================================================================================
		*/
		struct quat_s
		{
			std::float_t x, y, z, w;
		};
		/*
		//=====================================================================================
		*/
		struct mat4_s
		{
			std::float_t m[4][4];

			vec3_s row3(std::uint32_t r) const { return { m[r][0], m[r][1], m[r][2] }; }
		};
		/*
		//=====================================================================================
		*/
		struct int2_s
		{
			std::int32_t x, y;
		};
		/*
		//=====================================================================================
		*/
		struct rect_s
		{
			std::float_t x, y, w, h;

			bool contains(vec2_s p) const { return p.x >= x && p.y >= y && p.x < x + w && p.y < y + h; }
			vec2_s center() const { return { x + w * 0.5f, y + h * 0.5f }; }
		};
		/*
		//=====================================================================================
		*/
		struct chart_pin_s
		{
			vec2_s position;
			std::uint32_t stamp;
		};
		/*
		//=====================================================================================
		*/
		enum display_mode_e : std::uint32_t
		{
			display_mode_windowed,
			display_mode_borderless,
			display_mode_fullscreen,
			display_mode_count
		};
		/*
		//=====================================================================================
		*/
		enum font_e : std::uint32_t
		{
			font_regular,
			font_bold,
			font_light,
			font_condensed,
			font_mono,
			font_hand,
			font_hand_bold,
			font_serif,
			font_serif_caps,
			font_display,
			font_count
		};
		/*
		//=====================================================================================
		*/
		enum align_e : std::uint32_t
		{
			align_left = 0u,
			align_center = 1u,
			align_right = 2u,
			align_top = 0u,
			align_middle = 4u,
			align_bottom = 8u
		};
		/*
		//=====================================================================================
		*/
		enum canvas_mode_e : std::uint32_t
		{
			canvas_mode_solid,
			canvas_mode_image,
			canvas_mode_text,
			canvas_mode_rounded,
			canvas_mode_ring
		};
		/*
		//=====================================================================================
		*/
		struct input_state_s
		{
			bool down[key_count];
			bool pressed[key_count];
			bool released[key_count];
			bool repeated[key_count];
			vec2_s mouse_position;
			vec2_s mouse_delta;
			std::float_t wheel;
			char text[text_input_capacity];
			std::uint32_t text_length;
		};
		/*
		//=====================================================================================
		*/
		struct canvas_vertex_s
		{
			vec2_s position;
			vec2_s uv;
			std::uint32_t color;
			vec4_s params;
			vec4_s extra;
		};
		/*
		//=====================================================================================
		*/
		struct canvas_constants_s
		{
			vec2_s screen_size;
			vec2_s inverse_screen_size;
		};
		/*
		//=====================================================================================
		*/
		struct canvas_batch_s
		{
			ID3D11ShaderResourceView* texture;
			RECT scissor;
			std::uint32_t first_index;
			std::uint32_t index_count;
		};
		/*
		//=====================================================================================
		*/
		struct glyph_s
		{
			vec2_s uv_min;
			vec2_s uv_max;
			vec2_s offset;
			vec2_s size;
			std::float_t advance;
			bool visible;
		};
		/*
		//=====================================================================================
		*/
		struct font_face_s
		{
			const wchar_t* face;
			std::int32_t weight;
		};
		/*
		//=====================================================================================
		*/
		struct font_metrics_s
		{
			std::float_t ascent;
			std::float_t descent;
			std::float_t line_height;
			glyph_s glyphs[font_glyph_count];
		};
		/*
		//=====================================================================================
		*/
		enum target_flags_e : std::uint32_t
		{
			target_rtv = 1u,
			target_srv = 2u,
			target_uav = 4u,
			target_mips = 8u
		};
		/*
		//=====================================================================================
		*/
		struct target_s
		{
			ID3D11Texture2D* texture;
			ID3D11RenderTargetView* rtv;
			ID3D11ShaderResourceView* srv;
			ID3D11UnorderedAccessView* uav;
			std::uint32_t width;
			std::uint32_t height;
			DXGI_FORMAT format;
		};
		/*
		//=====================================================================================
		*/
		struct depth_target_s
		{
			ID3D11Texture2D* texture;
			ID3D11DepthStencilView* dsv;
			ID3D11DepthStencilView* dsv_read_only;
			ID3D11ShaderResourceView* srv;
			std::uint32_t width;
			std::uint32_t height;
		};
		/*
		//=====================================================================================
		*/
		struct shader_blob_s
		{
			const void* data;
			std::size_t size;
		};
		/*
		//=====================================================================================
		*/
		enum pak_type_e : std::uint32_t
		{
			pak_type_texture,
			pak_type_texture_array,
			pak_type_blob,
			pak_type_sound
		};
		/*
		//=====================================================================================
		*/
		struct pak_header_s
		{
			std::uint32_t magic;
			std::uint32_t version;
			std::uint32_t entry_count;
			std::uint32_t reserved;
			std::uint64_t table_offset;
			std::uint64_t stamp;
		};
		/*
		//=====================================================================================
		*/
		struct pak_entry_s
		{
			char name[pak_name_length];
			std::uint32_t type;
			std::uint32_t format;
			std::uint32_t width;
			std::uint32_t height;
			std::uint32_t layers;
			std::uint32_t mips;
			std::uint64_t offset;
			std::uint64_t size;
		};
		/*
		//=====================================================================================
		*/
		struct material_record_s
		{
			char name[material_name_length];
			vec3_s average_albedo;
			std::float_t average_roughness;
			std::float_t average_metal;
			std::float_t height_scale;
			std::uint32_t procedural;
			std::float_t aspect;
		};
		/*
		//=====================================================================================
		*/
		struct sky_record_s
		{
			char name[material_name_length];
			vec3_s sun_direction;
			std::float_t sun_angular_radius;
			vec3_s sun_irradiance;
			std::float_t sky_scale;
			vec4_s sh[sky_sh_coefficients];
		};
		/*
		//=====================================================================================
		*/
		struct vertex_s
		{
			vec3_s position;
			vec3_s normal;
			vec4_s tangent;
			vec2_s uv;
			std::uint32_t material;
		};
		/*
		//=====================================================================================
		*/
		enum material_flags_e : std::uint32_t
		{
			material_flag_parallax = 1u,
			material_flag_triplanar = 2u,
			material_flag_two_sided = 4u,
			material_flag_glass = 8u,
			material_flag_unlit = 16u,
			material_flag_alpha_test = 32u,
			material_flag_emissive_map = 64u
		};
		/*
		//=====================================================================================
		*/
		struct model_header_s
		{
			std::uint32_t part_count;
			std::uint32_t vertex_count;
			std::uint32_t index_count;
			std::uint32_t material_count;
			vec3_s bounds_min;
			vec3_s bounds_max;
		};
		/*
		//=====================================================================================
		*/
		struct model_part_s
		{
			char name[model_part_name_length];
			std::uint32_t first_index;
			std::uint32_t index_count;
			vec3_s bounds_min;
			vec3_s bounds_max;
		};
		/*
		//=====================================================================================
		*/
		struct model_material_s
		{
			char set_name[material_name_length];
			std::uint32_t flags;
			vec3_s emissive;
			std::float_t roughness_scale;
			std::float_t metal_scale;
			std::float_t reserved[2];
		};
		/*
		//=====================================================================================
		*/
		struct material_gpu_s
		{
			vec4_s tint;
			std::uint32_t layer;
			std::float_t uv_scale;
			std::float_t normal_strength;
			std::float_t height_scale;
			std::float_t roughness_scale;
			std::float_t roughness_bias;
			std::float_t metal_scale;
			std::float_t metal_bias;
			vec3_s emissive;
			std::float_t aspect;
			std::uint32_t flags;
			std::float_t ao_strength;
			std::float_t specular;
			std::float_t reserved;
		};
		/*
		//=====================================================================================
		*/
		struct material_definition_s
		{
			const char* name;
			const char* texture_set;
			vec3_s tint;
			std::float_t uv_scale;
			std::float_t roughness_scale;
			std::float_t roughness_bias;
			std::float_t metal_scale;
			std::float_t metal_bias;
			std::float_t normal_strength;
			std::uint32_t flags;
			vec3_s emissive;
		};
		/*
		//=====================================================================================
		*/
		struct mesh_s
		{
			ID3D11Buffer* vertex_buffer;
			ID3D11Buffer* index_buffer;
			std::uint32_t vertex_count;
			std::uint32_t index_count;
			vec3_s bounds_min;
			vec3_s bounds_max;
		};
		/*
		//=====================================================================================
		*/
		struct draw_range_s
		{
			std::uint32_t first_index;
			std::uint32_t index_count;
			vec3_s bounds_min;
			vec3_s bounds_max;
			bool alpha;
		};
		/*
		//=====================================================================================
		*/
		struct model_s
		{
			char name[pak_name_length];
			std::vector<vertex_s> vertices;
			std::vector<std::uint32_t> indices;
			std::vector<model_part_s> parts;
			std::vector<std::uint32_t> materials;
			vec3_s bounds_min;
			vec3_s bounds_max;
			mesh_s mesh;
		};
		/*
		//=====================================================================================
		*/
		struct foliage_species_s
		{
			const model_s* near_model;
			const model_s* far_model;
			std::float_t near_distance;
			std::float_t far_distance;
			std::float_t shadow_distance;
			std::float_t sway;
			const model_s* impostor_model;
			std::float_t impostor_distance;
			const model_s* shadow_model;
		};
		/*
		//=====================================================================================
		*/
		struct foliage_instance_s
		{
			vec3_s position;
			std::float_t yaw;
			std::float_t scale;
			std::uint32_t species;
			std::float_t bend;
			std::float_t slope;
		};
		/*
		//=====================================================================================
		*/
		struct foliage_gpu_s
		{
			vec4_s placement;
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		struct foliage_cell_s
		{
			std::vector<std::uint32_t> instances;
			vec3_s bounds_min;
			vec3_s bounds_max;
		};
		/*
		//=====================================================================================
		*/
		struct foliage_bucket_s
		{
			const model_s* model;
			std::uint32_t first;
			std::uint32_t count;
			std::vector<foliage_gpu_s> items;
			bool impostor;
			bool fading;
		};
		/*
		//=====================================================================================
		*/
		enum profile_e : std::uint32_t
		{
			profile_cascade_ground,
			profile_cascade_foliage,
			profile_cascade1_ground,
			profile_cascade1_foliage,
			profile_cascade2_ground,
			profile_cascade2_foliage,
			profile_cascade3_ground,
			profile_cascade3_foliage,
			profile_world,
			profile_terrain,
			profile_foliage,
			profile_grass,
			profile_models,
			profile_decals,
			profile_ssao,
			profile_clouds,
			profile_lighting,
			profile_effects,
			profile_post,
			profile_count
		};
		/*
		//=====================================================================================
		*/
		enum item_e : std::uint32_t
		{
			item_none,
			item_wood,
			item_stone,
			item_metal_ore,
			item_sulfur_ore,
			item_metal_fragments,
			item_cloth,
			item_scrap,
			item_charcoal,
			item_rock,
			item_torch,
			item_stone_hatchet,
			item_stone_pickaxe,
			item_wooden_spear,
			item_hunting_bow,
			item_wooden_arrow,
			item_bandage,
			item_berries,
			item_canned_beans,
			item_water_bottle,
			item_campfire,
			item_sleeping_bag,
			item_wooden_door,
			item_building_plan,
			item_hammer,
			item_storage_box,
			item_furnace,
			item_sulfur,
			item_gunpowder,
			item_pistol_ammo,
			item_rifle_ammo,
			item_pistol,
			item_rifle,
			item_potato,
			item_baked_potato,
			item_corn,
			item_roasted_corn,
			item_pumpkin,
			item_roasted_pumpkin,
			item_hemp_seeds,
			item_well,
			item_assault_rifle,
			item_workbench_1,
			item_workbench_2,
			item_workbench_3,
			item_research_table,
			item_blueprint,
			item_radio_valve,
			item_radio_coil,
			item_radio_battery,
			item_cupboard,
			item_code_lock,
			item_raw_venison,
			item_cooked_venison,
			item_raw_pork,
			item_cooked_pork,
			item_raw_horse,
			item_cooked_horse,
			item_animal_fat,
			item_hide,
			item_bone,
			item_count
		};
		/*
		//=====================================================================================
		*/
		enum item_category_e : std::uint32_t
		{
			item_category_resource,
			item_category_tool,
			item_category_weapon,
			item_category_ammunition,
			item_category_medical,
			item_category_food,
			item_category_construction,
			item_category_farming,
			item_category_count
		};
		/*
		//=====================================================================================
		*/
		enum crop_e : std::uint32_t
		{
			crop_none,
			crop_potato,
			crop_corn,
			crop_hemp,
			crop_pumpkin,
			crop_count
		};
		/*
		//=====================================================================================
		*/
		enum container_kind_e : std::uint32_t
		{
			container_storage,
			container_furnace,
			container_campfire
		};
		/*
		//=====================================================================================
		*/
		enum weapon_e : std::uint32_t
		{
			weapon_none,
			weapon_pistol,
			weapon_rifle,
			weapon_bow,
			weapon_assault,
			weapon_count
		};
		/*
		//=====================================================================================
		*/
		struct item_definition_s
		{
			const char* name;
			const char* description;
			std::uint32_t category;
			std::uint32_t stack;
			std::float_t damage;
			std::float_t wood_yield;
			std::float_t stone_yield;
			std::float_t swing_time;
			std::float_t reach;
			std::float_t calories;
			std::float_t hydration;
			std::float_t healing;
			std::uint32_t weapon;
			std::uint32_t crop;
		};
		/*
		//=====================================================================================
		*/
		struct crop_definition_s
		{
			const char* name;
			const char* model;
			std::uint32_t yield;
			std::uint32_t minimum;
			std::uint32_t maximum;
			std::uint32_t bonus;
			std::uint32_t bonus_minimum;
			std::uint32_t bonus_maximum;
			std::float_t grow_time;
			std::float_t scale;
		};
		/*
		//=====================================================================================
		*/
		struct crop_s
		{
			vec3_s position;
			std::float_t yaw;
			std::float_t growth;
			std::float_t water;
			std::float_t health;
			std::float_t ripe_time;
			std::uint32_t kind;
			bool dead;
		};
		/*
		//=====================================================================================
		*/
		struct conversion_s
		{
			std::uint32_t input;
			std::uint32_t output;
		};
		/*
		//=====================================================================================
		*/
		struct item_stack_s
		{
			std::uint32_t item;
			std::uint32_t amount;
			std::float_t condition;
			std::uint32_t loaded;
		};
		/*
		//=====================================================================================
		*/
		struct loadout_entry_s
		{
			std::uint32_t slot;
			item_stack_s stack;
		};
		/*
		//=====================================================================================
		*/
		struct weapon_definition_s
		{
			std::uint32_t item;
			std::uint32_t ammo;
			std::uint32_t capacity;
			std::float_t interval;
			std::float_t reload;
			std::float_t spread;
			std::float_t aim_spread;
			std::float_t recoil;
			std::float_t range;
			std::float_t zoom;
			std::float_t noise;
			std::uint32_t shot_sound;
			std::uint32_t reload_sound;
			std::float_t scope;
			bool automatic;
			std::float_t jam_chance;
			std::float_t misfire_chance;
			std::float_t rate_jitter;
			std::float_t heat_per_shot;
			std::float_t bloom;
			std::float_t kick_jitter;
			std::float_t clear_time;
			std::uint32_t far_sound;
			std::float_t loudness;
		};
		/*
		//=====================================================================================
		*/
		struct ingredient_s
		{
			std::uint32_t item;
			std::uint32_t amount;
		};
		/*
		//=====================================================================================
		*/
		struct recipe_s
		{
			std::uint32_t result;
			std::uint32_t amount;
			std::float_t time;
			ingredient_s ingredients[3];
			std::uint32_t tier;
			bool starter;
		};
		/*
		//=====================================================================================
		*/
		struct craft_job_s
		{
			std::uint32_t recipe;
			std::float_t remaining;
		};
		/*
		//=====================================================================================
		*/
		struct notification_s
		{
			char text[64];
			std::float_t age;
			std::int32_t amount;
		};
		/*
		//=====================================================================================
		*/
		enum node_kind_e : std::uint32_t
		{
			node_tree,
			node_dead_tree,
			node_stone,
			node_metal,
			node_sulfur,
			node_hemp,
			node_berry,
			node_barrel,
			node_toolbox,
			node_box,
			node_military,
			node_medical,
			node_potato,
			node_corn,
			node_pumpkin,
			node_kind_count
		};
		/*
		//=====================================================================================
		*/
		struct resource_node_s
		{
			vec3_s position;
			std::float_t health;
			std::float_t radius;
			std::uint32_t kind;
			std::uint32_t instance;
			std::int32_t brush;
			bool depleted;
			std::float_t timer;
			std::float_t scale;
			std::uint32_t contents;
			std::float_t fall;
		};
		/*
		//=====================================================================================
		*/
		struct felled_s
		{
			const model_s* model;
			vec3_s position;
			std::float_t yaw;
			std::float_t scale;
			std::float_t fall;
			std::float_t angle;
			std::float_t speed;
			std::float_t height;
			std::float_t timer;
			bool landed;
			mat4_s previous;
		};
		/*
		//=====================================================================================
		*/
		struct loot_entry_s
		{
			std::uint32_t item;
			std::uint32_t minimum;
			std::uint32_t maximum;
			std::float_t chance;
		};
		/*
		//=====================================================================================
		*/
		struct loot_table_s
		{
			const loot_entry_s* entries;
			std::size_t count;
		};
		/*
		//=====================================================================================
		*/
		struct vitals_s
		{
			std::float_t health;
			std::float_t calories;
			std::float_t hydration;
			std::float_t damage_flash;
			std::float_t breath;
			bool dead;
		};
		/*
		//=====================================================================================
		*/
		struct climate_s
		{
			std::float_t air;
			std::float_t rain;
			std::float_t heat;
			std::float_t wetness;
			std::float_t temperature;
			std::float_t timer;
			bool sheltered;
			bool swimming;
		};
		/*
		//=====================================================================================
		*/
		struct viewmodel_key_s
		{
			std::float_t time;
			vec3_s wrist;
			vec3_s angles;
		};
		/*
		//=====================================================================================
		*/
		struct hand_frame_s
		{
			vec3_s wrist;
			vec3_s fingers;
			vec3_s palm;
		};
		/*
		//=====================================================================================
		*/
		enum action_e : std::uint32_t
		{
			action_slide,
			action_break,
			action_bolt,
			action_draw
		};
		/*
		//=====================================================================================
		*/
		enum landmark_e : std::uint32_t
		{
			landmark_town,
			landmark_outpost,
			landmark_yard,
			landmark_harbour,
			landmark_ouen,
			landmark_portelet,
			landmark_battery,
			landmark_institute,
			landmark_quarry,
			landmark_halt,
			landmark_rozel,
			landmark_landes,
			landmark_trinity,
			landmark_count
		};
		/*
		//=====================================================================================
		*/
		enum route_e : std::uint32_t
		{
			route_rail,
			route_road,
			route_count
		};
		/*
		//=====================================================================================
		*/
		enum track_material_e : std::uint32_t
		{
			track_material_asphalt,
			track_material_dirt,
			track_material_ballast,
			track_material_sleeper,
			track_material_rail,
			track_material_count
		};
		/*
		//=====================================================================================
		*/
		struct world_site_s
		{
			vec2_s position;
			std::float_t inner;
			std::float_t outer;
			std::float_t yaw;
			std::uint32_t landmark;
		};
		/*
		//=====================================================================================
		*/
		struct world_route_s
		{
			const vec2_s* points;
			std::uint32_t count;
			std::uint32_t kind;
			std::float_t width;
			std::float_t grade;
			std::float_t smoothing;
			std::float_t slope;
			bool closed;
		};
		/*
		//=====================================================================================
		*/
		enum town_building_e : std::uint32_t
		{
			town_terrace,
			town_shop,
			town_pub,
			town_church,
			town_police,
			town_clinic,
			town_garage,
			town_fuel,
			town_flats,
			town_school,
			town_hall,
			town_house,
			town_cottage,
			town_ruin,
			town_building_count
		};
		/*
		//=====================================================================================
		*/
		enum town_surface_e : std::uint32_t
		{
			town_road,
			town_lane,
			town_walk,
			town_square,
			town_yard,
			town_surface_count
		};
		/*
		//=====================================================================================
		*/
		struct town_building_s
		{
			const char* model;
			vec2_s size;
			std::uint32_t floors;
		};
		/*
		//=====================================================================================
		*/
		struct town_paving_s
		{
			std::uint32_t material;
			vec3_s tint;
			std::float_t top;
			std::float_t tile;
			bool raised;
		};
		/*
		//=====================================================================================
		*/
		struct town_patch_s
		{
			vec2_s minimum;
			vec2_s maximum;
			std::uint32_t paving;
		};
		/*
		//=====================================================================================
		*/
		struct town_row_s
		{
			vec2_s from;
			vec2_s to;
			std::float_t gap;
			std::uint32_t count;
			std::uint32_t buildings[10];
		};
		/*
		//=====================================================================================
		*/
		struct town_site_s
		{
			std::uint32_t building;
			vec2_s position;
			std::float_t yaw;
		};
		/*
		//=====================================================================================
		*/
		struct town_yard_s
		{
			vec2_s minimum;
			vec2_s maximum;
			std::uint32_t clutter;
		};
		/*
		//=====================================================================================
		*/
		struct town_prop_s
		{
			const char* model;
			vec2_s position;
			std::float_t yaw;
			std::uint32_t surface;
		};
		/*
		//=====================================================================================
		*/
		struct town_run_s
		{
			const char* model;
			vec2_s from;
			vec2_s to;
			std::float_t piece;
			std::uint32_t surface;
		};
		/*
		//=====================================================================================
		*/
		struct route_path_s
		{
			std::uint32_t kind;
			std::float_t width;
			bool closed;
			std::vector<vec3_s> points;
		};
		/*
		//=====================================================================================
		*/
		enum train_vehicle_e : std::uint32_t
		{
			train_vehicle_locomotive,
			train_vehicle_flat,
			train_vehicle_open,
			train_vehicle_box,
			train_vehicle_coach,
			train_vehicle_count
		};
		/*
		//=====================================================================================
		*/
		struct train_vehicle_s
		{
			const char* model;
			std::float_t length;
			std::float_t wheelbase;
			std::float_t height;
			std::float_t width;
			std::float_t deck;
			std::uint32_t material;
			std::uint32_t axles;
			std::float_t axle_offsets[4];
		};
		/*
		//=====================================================================================
		*/
		struct train_leg_s
		{
			std::float_t start_time;
			std::float_t start_distance;
			std::float_t length;
			std::float_t travel_time;
			std::float_t ramp_time;
			std::float_t ramp_length;
			std::float_t peak;
		};
		/*
		//=====================================================================================
		*/
		struct train_box_s
		{
			vec3_s center;
			vec3_s half;
			std::uint32_t surface;
		};
		/*
		//=====================================================================================
		*/
		enum vehicle_kind_e : std::uint32_t
		{
			vehicle_rover,
			vehicle_heli,
			vehicle_kind_count
		};
		/*
		//=====================================================================================
		*/
		struct vehicle_kind_s
		{
			const char* model;
			const char* name;
			std::float_t mass;
			vec3_s hull_center;
			vec3_s hull_half;
			vec3_s mass_center;
			std::uint32_t wheel_count;
			vec3_s wheels[4];
			std::float_t wheel_radius;
			std::float_t travel;
			std::float_t spring;
			std::float_t damper;
			std::float_t drive;
			std::float_t brake;
			std::float_t steer;
			std::float_t grip;
			std::float_t top_speed;
			std::float_t reverse_speed;
			std::float_t lift;
			std::float_t tilt;
			std::float_t turn;
			vec3_s rotor_hub;
			vec3_s tail_hub;
			std::float_t rotor_radius;
			std::uint32_t seat_count;
			vec3_s seats[2];
			vec3_s exits[2];
			vec3_s lights[2];
			vec3_s exhaust;
			std::float_t health;
		};
		/*
		//=====================================================================================
		*/
		struct vehicle_controls_s
		{
			std::float_t throttle;
			std::float_t steer;
			std::float_t lift;
			std::float_t pitch;
			std::float_t roll;
			std::float_t heading;
			bool brake;
			bool engine;
		};
		/*
		//=====================================================================================
		*/
		struct vehicle_s
		{
			vec3_s position;
			quat_s orientation;
			vec3_s velocity;
			vec3_s spin;
			std::float_t compression[4];
			std::float_t spun[4];
			std::float_t steer;
			std::float_t engine;
			std::float_t rotor;
			std::float_t rotor_speed;
			std::float_t health;
			std::float_t still;
			std::float_t scrape;
			std::float_t puff;
			std::float_t wreck_time;
			std::uint32_t home;
			std::uint32_t kind;
			std::uint32_t id;
			std::int32_t riders[2];
			bool asleep;
			bool predicted;
			vec3_s tick_position;
			quat_s tick_orientation;
			vec3_s from_position;
			vec3_s to_position;
			quat_s from_orientation;
			quat_s to_orientation;
			vec3_s shown_velocity;
			std::double_t from_time;
			std::double_t to_time;
			std::double_t seen;
			vec3_s shown_position;
			quat_s shown_orientation;
			vec3_s error;
			mat4_s world;
			mat4_s previous_world;
		};
		/*
		//=====================================================================================
		*/
		struct vehicle_spawn_s
		{
			std::uint32_t kind;
			vec2_s position;
			std::float_t yaw;
		};
		/*
		//=====================================================================================
		*/
		struct station_s
		{
			std::uint32_t landmark;
			std::uint32_t index;
			std::float_t side;
		};
		/*
		//=====================================================================================
		*/
		struct station_kit_s
		{
			std::uint32_t landmark;
			bool building;
			bool signal_box;
			bool water_tower;
		};
		/*
		//=====================================================================================
		*/
		struct crossing_s
		{
			vec3_s position;
			vec3_s rail;
			vec3_s road;
			std::float_t along;
			std::float_t width;
		};
		/*
		//=====================================================================================
		*/
		struct gate_s
		{
			vec3_s hinge;
			std::float_t open;
			std::float_t shut;
			std::float_t angle;
			std::float_t previous;
			std::float_t stretch;
			std::uint32_t crossing;
		};
		/*
		//=====================================================================================
		*/
		struct gate_lamp_s
		{
			vec3_s position;
			std::float_t phase;
			std::uint32_t crossing;
		};
		/*
		//=====================================================================================
		*/
		enum goal_kind_e : std::uint32_t
		{
			goal_have,
			goal_place,
			goal_research,
			goal_reach,
			goal_parts,
			goal_repair,
			goal_wait,
			goal_rescue,
			goal_free
		};
		/*
		//=====================================================================================
		*/
		struct goal_s
		{
			const char* title;
			const char* hint;
			std::uint32_t kind;
			std::uint32_t subject;
			std::uint32_t amount;
			std::uint32_t reward;
			std::uint32_t reward_amount;
		};
		/*
		//=====================================================================================
		*/
		enum app_state_e : std::uint32_t
		{
			app_loading,
			app_title,
			app_waking,
			app_playing
		};
		/*
		//=====================================================================================
		*/
		enum menu_page_e : std::uint32_t
		{
			page_main,
			page_settings,
			page_notes,
			page_servers,
			page_controls,
			page_credits
		};
		/*
		//=====================================================================================
		*/
		enum settings_tab_e : std::uint32_t
		{
			tab_display,
			tab_graphics,
			tab_audio,
			tab_controls,
			tab_keys,
			tab_gameplay,
			tab_interface,
			tab_accessibility,
			tab_count
		};
		/*
		//=====================================================================================
		*/
		enum setting_row_e : std::uint32_t
		{
			row_header,
			row_choice,
			row_slider,
			row_toggle,
			row_preset
		};
		/*
		//=====================================================================================
		*/
		enum dialog_e : std::uint32_t
		{
			dialog_none,
			dialog_display,
			dialog_leave,
			dialog_quit,
			dialog_defaults
		};
		/*
		//=====================================================================================
		*/
		enum menu_action_e : std::uint32_t
		{
			menu_none,
			menu_continue,
			menu_wake,
			menu_resume,
			menu_title,
			menu_settings,
			menu_notes,
			menu_quit,
			menu_play,
			menu_join,
			menu_host,
			menu_credits
		};
		/*
		//=====================================================================================
		*/
		struct menu_entry_s
		{
			const char* label;
			std::uint32_t action;
		};
		/*
		//=====================================================================================
		*/
		struct guide_key_s
		{
			std::int32_t bind;
			const char* key;
			const char* action;
		};
		/*
		//=====================================================================================
		*/
		enum bind_e : std::uint32_t
		{
			bind_forward,
			bind_back,
			bind_left,
			bind_right,
			bind_jump,
			bind_crouch,
			bind_sprint,
			bind_walk,
			bind_use,
			bind_reload,
			bind_rotate,
			bind_inventory,
			bind_map,
			bind_chat,
			bind_melee,
			bind_throw,
			bind_visor,
			bind_count
		};
		/*
		//=====================================================================================
		*/
		struct user_settings_s
		{
			std::uint32_t quality;
			std::float_t render_scale;
			std::float_t field_of_view;
			std::float_t brightness;
			std::float_t volume;
			std::float_t effects_volume;
			std::float_t ambience_volume;
			std::float_t sensitivity;
			bool film_grain;
			bool vignette;
			bool vsync;
			bool invert;
			std::uint8_t bindings[bind_count];
			std::uint32_t display;
			std::uint32_t window_size;
			std::uint32_t frame_limit;
			std::uint32_t anti_aliasing;
			std::uint32_t shadows;
			std::uint32_t ambient_occlusion;
			std::uint32_t reflections;
			std::uint32_t light_shafts;
			std::uint32_t texture_filter;
			std::uint32_t vegetation;
			std::uint32_t grass;
			std::uint32_t marks;
			bool bloom;
			bool motion_blur;
			bool chromatic_aberration;
			std::float_t sharpening;
			bool show_fps;
			std::float_t interface_volume;
			bool mute_unfocused;
			std::float_t aim_sensitivity;
			std::uint32_t crouch_mode;
			std::uint32_t aim_mode;
			std::uint32_t sprint_mode;
			std::uint32_t head_bob;
			std::uint32_t crosshair;
			bool hit_markers;
			bool compass;
			bool name_tags;
			std::uint32_t vitals;
			std::uint32_t hotbar;
			bool chat;
			bool hints;
			std::float_t interface_scale;
			std::uint32_t colour_filter;
			bool reduce_flashing;
			bool reverse_wheel;
			bool strafe_tilt;
			bool prompts;
			bool damage_direction;
			bool pickup_messages;
			bool calm_camera;
			bool ear_ringing;
			bool censor;
			std::uint32_t clouds;
		};
		/*
		//=====================================================================================
		*/
		struct setting_row_s
		{
			std::uint32_t tab;
			std::uint32_t kind;
			const char* key;
			const char* label;
			const char* description;
			std::uint32_t impact;
			std::uint32_t user_settings_s::* choice;
			std::float_t user_settings_s::* number;
			bool user_settings_s::* flag;
			const char* const* names;
			std::uint32_t count;
			std::float_t low;
			std::float_t high;
			std::float_t step;
			std::float_t display;
			const char* format;
			bool graphics;
		};
		/*
		//=====================================================================================
		*/
		struct title_shot_s
		{
			vec3_s from;
			vec3_s to;
			vec3_s focus;
			std::float_t orbit;
			std::float_t radius;
			bool orbiting;
		};
		/*
		//=====================================================================================
		*/
		struct landmark_s
		{
			vec2_s position;
			std::float_t radius;
			std::uint32_t kind;
		};
		/*
		//=====================================================================================
		*/
		struct road_s
		{
			vec2_s from;
			vec2_s to;
			std::float_t width;
		};
		/*
		//=====================================================================================
		*/
		struct footprint_s
		{
			vec2_s center;
			vec2_s half;
			std::float_t yaw;
		};
		/*
		//=====================================================================================
		*/
		struct gun_sound_s
		{
			std::uint32_t close;
			std::uint32_t own;
			std::uint32_t mechanism;
			std::uint32_t distant;
			std::uint32_t tail;
			std::float_t deafening;
			bool ejects;
		};
		/*
		//=====================================================================================
		*/
		struct gun_model_s
		{
			const char* model;
			const char* parts[6];
			const char* bolt[2];
			vec3_s grip;
			vec3_s muzzle;
			vec3_s support;
			vec3_s bolt_pivot;
			vec3_s bolt_knob;
			vec3_s bolt_axis;
			vec3_s support_fingers;
			vec3_s support_palm;
			std::float_t tilt;
			std::float_t bolt_throw;
			std::float_t bolt_lift;
			std::uint32_t action;
			const char* magazine;
			vec3_s magazine_grip;
		};
		/*
		//=====================================================================================
		*/
		struct arrow_s
		{
			vec3_s position;
			vec3_s velocity;
			vec3_s heading;
			std::float_t damage;
			std::float_t age;
			std::int32_t owner;
			bool flying;
		};
		/*
		//=====================================================================================
		*/
		enum piece_e : std::uint32_t
		{
			piece_foundation,
			piece_wall,
			piece_doorway,
			piece_window,
			piece_floor,
			piece_stairs,
			piece_roof,
			piece_door,
			piece_campfire,
			piece_sleeping_bag,
			piece_storage_box,
			piece_furnace,
			piece_well,
			piece_workbench_1,
			piece_workbench_2,
			piece_workbench_3,
			piece_research_table,
			piece_cupboard,
			piece_count
		};
		/*
		//=====================================================================================
		*/
		struct container_s
		{
			item_stack_s slots[container_slots];
			std::float_t smelt_timer;
			std::float_t fuel_timer;
			std::uint32_t structure;
			std::uint32_t kind;
			bool burning;
		};
		/*
		//=====================================================================================
		*/
		struct piece_definition_s
		{
			const char* name;
			std::uint32_t item;
			ingredient_s cost;
			std::float_t health;
		};
		/*
		//=====================================================================================
		*/
		struct structure_s
		{
			vec3_s position;
			std::float_t yaw;
			std::float_t health;
			std::float_t swing;
			std::float_t flicker;
			std::uint32_t piece;
			std::int32_t first_brush;
			std::uint32_t brush_count;
			std::int32_t anchor;
			std::int32_t container;
			std::uint32_t owner;
			std::uint32_t tier;
			bool open;
			bool destroyed;
		};
		/*
		//=====================================================================================
		*/
		struct tier_s
		{
			const char* name;
			std::uint32_t item;
			std::uint32_t cost;
			std::float_t health;
			std::float_t bullets;
			std::float_t blows;
			std::uint32_t surface;
			std::uint32_t sound;
		};
		/*
		//=====================================================================================
		*/
		struct placement_s
		{
			vec3_s position;
			std::float_t yaw;
			std::uint32_t piece;
			std::int32_t anchor;
			bool valid;
			bool active;
		};
		/*
		//=====================================================================================
		*/
		enum sound_e : std::uint32_t
		{
			sound_step_grass,
			sound_step_concrete,
			sound_step_wood,
			sound_step_soft,
			sound_step_gravel,
			sound_hit_wood,
			sound_hit_rock,
			sound_hit_metal,
			sound_hit_flesh,
			sound_hit_soft,
			sound_chop,
			sound_swing,
			sound_pickup,
			sound_container,
			sound_craft,
			sound_equip,
			sound_ui_click,
			sound_ui_open,
			sound_ui_close,
			sound_ui_error,
			sound_zombie_groan,
			sound_zombie_snarl,
			sound_ghost_moan,
			sound_player_hurt,
			sound_heartbeat,
			sound_fire,
			sound_amb_forest,
			sound_amb_crickets,
			sound_amb_drone,
			sound_amb_wind,
			sound_amb_ocean,
			sound_shot_pistol,
			sound_shot_rifle,
			sound_reload_pistol,
			sound_reload_rifle,
			sound_bolt,
			sound_shot_assault,
			sound_dry_fire,
			sound_jam,
			sound_splash,
			sound_wade,
			sound_swim,
			sound_underwater,
			sound_shot_pistol_far,
			sound_shot_rifle_far,
			sound_shot_assault_far,
			sound_amb_rain,
			sound_thunder,
			sound_tree_creak,
			sound_tree_fall,
			sound_bullet_crack,
			sound_bullet_whiz,
			sound_ricochet,
			sound_train_engine,
			sound_train_roll,
			sound_train_clack,
			sound_train_horn,
			sound_train_brake,
			sound_train_hiss,
			sound_gun_pistol_close,
			sound_gun_pistol_mech,
			sound_gun_pistol_far,
			sound_gun_pistol_tail_plain,
			sound_gun_pistol_tail_forest,
			sound_gun_pistol_tail_mountains,
			sound_gun_pistol_tail_city,
			sound_gun_pistol_tail_room,
			sound_gun_bolt_close,
			sound_gun_bolt_mech,
			sound_gun_bolt_far,
			sound_gun_bolt_tail_plain,
			sound_gun_bolt_tail_forest,
			sound_gun_bolt_tail_mountains,
			sound_gun_bolt_tail_city,
			sound_gun_bolt_tail_room,
			sound_gun_auto_close,
			sound_gun_auto_mech,
			sound_gun_auto_far,
			sound_gun_auto_tail_plain,
			sound_gun_auto_tail_forest,
			sound_gun_auto_tail_mountains,
			sound_gun_auto_tail_city,
			sound_gun_auto_tail_room,
			sound_casing_hard,
			sound_casing_wood,
			sound_casing_soft,
			sound_tinnitus,
			sound_gun_pistol_self,
			sound_gun_bolt_self,
			sound_gun_auto_self,
			sound_vehicle_engine,
			sound_vehicle_rotor,
			sound_count
		};
		/*
		//=====================================================================================
		*/
		enum drone_e : std::uint32_t
		{
			drone_engine,
			drone_roll,
			drone_horn,
			drone_brake,
			drone_vehicle_engine,
			drone_vehicle_rotor,
			drone_count
		};
		/*
		//=====================================================================================
		*/
		struct drone_s
		{
			vec3_s position;
			vec3_s velocity;
			std::float_t loudness;
			std::float_t pitch;
			std::float_t reference;
			std::float_t delay;
			std::float_t blocked;
			std::float_t recheck;
			std::uint32_t queued;
			bool fresh;
		};
		/*
		//=====================================================================================
		*/
		enum acoustic_e : std::uint32_t
		{
			acoustic_plain,
			acoustic_forest,
			acoustic_mountains,
			acoustic_city,
			acoustic_room,
			acoustic_underwater,
			acoustic_count
		};
		/*
		//=====================================================================================
		*/
		struct pending_sound_s
		{
			std::float_t time;
			std::uint32_t sound;
			vec3_s position;
			std::float_t volume;
			std::float_t pitch;
			std::float_t cutoff;
			std::float_t send;
			bool spatial;
		};
		/*
		//=====================================================================================
		*/
		struct echo_s
		{
			vec3_s position;
			std::float_t path;
			std::float_t strength;
		};
		/*
		//=====================================================================================
		*/
		enum ambience_e : std::uint32_t
		{
			ambience_forest,
			ambience_crickets,
			ambience_drone,
			ambience_wind,
			ambience_ocean,
			ambience_count
		};
		/*
		//=====================================================================================
		*/
		struct sound_clip_s
		{
			const std::uint8_t* data;
			std::uint32_t bytes;
			std::uint32_t frames;
			std::uint32_t channels;
			std::uint32_t rate;
		};
		/*
		//=====================================================================================
		*/
		struct sound_group_s
		{
			std::uint32_t first;
			std::uint32_t count;
		};
		/*
		//=====================================================================================
		*/
		enum particle_kind_e : std::uint32_t
		{
			particle_flame,
			particle_ember,
			particle_smoke,
			particle_dust,
			particle_chip,
			particle_blood,
			particle_spark,
			particle_fire,
			particle_kind_count
		};
		/*
		//=====================================================================================
		*/
		struct particle_kind_s
		{
			std::float_t life_minimum;
			std::float_t life_maximum;
			std::float_t size_minimum;
			std::float_t size_maximum;
			std::float_t growth;
			std::float_t gravity;
			std::float_t drag;
			std::float_t softness;
			vec4_s color;
		};
		/*
		//=====================================================================================
		*/
		struct particle_s
		{
			vec3_s position;
			vec3_s velocity;
			vec4_s color;
			std::float_t age;
			std::float_t life;
			std::float_t size;
			std::float_t rotation;
			std::float_t spin;
			std::float_t seed;
			std::uint32_t kind;
			bool view_space;
		};
		/*
		//=====================================================================================
		*/
		struct particle_vertex_s
		{
			vec3_s position;
			vec2_s uv;
			vec4_s color;
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		struct particle_constants_s
		{
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		struct rain_constants_s
		{
			vec4_s params;
			vec4_s wind;
			vec4_s ground;
		};
		/*
		//=====================================================================================
		*/
		struct bolt_constants_s
		{
			vec4_s points[weather_bolt_segments * 2u];
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		struct shaft_constants_s
		{
			vec4_s sun;
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		struct weather_phase_s
		{
			std::float_t cloud;
			std::float_t rain;
			std::float_t storm;
			std::float_t chance;
			std::float_t shortest;
			std::float_t longest;
		};
		/*
		//=====================================================================================
		*/
		struct water_constants_s
		{
			vec4_s waves[8];
			vec4_s params;
			vec4_s shallow;
			vec4_s deep;
			vec4_s absorption;
			vec4_s terrain;
		};
		/*
		//=====================================================================================
		*/
		struct grass_vertex_s
		{
			vec3_s position;
			vec3_s normal;
			vec2_s uv;
		};
		/*
		//=====================================================================================
		*/
		struct grass_constants_s
		{
			vec4_s rings[2];
			vec4_s sprites[grass_sprite_count];
			vec4_s terrain;
			vec4_s player;
			std::uint32_t materials[4];
		};
		/*
		//=====================================================================================
		*/
		struct terrain_constants_s
		{
			vec4_s params;
			vec4_s morph[8];
			std::uint32_t layers[terrain_layer_count];
			vec4_s camera;
		};
		/*
		//=====================================================================================
		*/
		enum terrain_layer_e : std::uint32_t
		{
			layer_grass,
			layer_dry,
			layer_litter,
			layer_dirt,
			layer_rock,
			layer_cliff,
			layer_sand,
			layer_gravel,
			layer_needles,
			layer_heath,
			layer_moor,
			layer_marsh,
			layer_dune,
			layer_shingle,
			layer_turf,
			layer_soil
		};
		/*
		//=====================================================================================
		*/
		enum biome_e : std::uint32_t
		{
			biome_sea,
			biome_beach,
			biome_shore,
			biome_dunes,
			biome_marsh,
			biome_meadow,
			biome_farmland,
			biome_woodland,
			biome_pinewood,
			biome_heath,
			biome_moor,
			biome_summit,
			biome_count
		};
		/*
		//=====================================================================================
		*/
		struct biome_flora_s
		{
			std::float_t trees;
			std::float_t snags;
			std::float_t rocks;
			std::float_t ores;
			std::float_t hemp;
			std::float_t berries;
			std::float_t crops;
			std::float_t plants;
			std::float_t debris;
			std::float_t gorse;
		};
		/*
		//=====================================================================================
		*/
		enum tree_kind_e : std::uint32_t
		{
			tree_fir,
			tree_pine,
			tree_birch,
			tree_oak,
			tree_hawthorn,
			tree_willow,
			tree_kind_count
		};
		/*
		//=====================================================================================
		*/
		struct tree_species_s
		{
			const char* prefix;
			std::uint32_t variants;
			std::float_t sway;
			std::float_t trunk;
			std::float_t height;
			std::float_t girth;
			std::float_t spread;
			std::float_t smallest;
			std::float_t largest;
		};
		/*
		//=====================================================================================
		*/
		enum field_kind_e : std::uint32_t
		{
			field_pasture,
			field_hay,
			field_ploughed,
			field_stubble,
			field_kind_count
		};
		/*
		//=====================================================================================
		*/
		struct terrain_header_s
		{
			std::uint32_t resolution;
			std::uint32_t texture_size;
			std::float_t world_size;
			std::float_t origin;
			std::float_t minimum_height;
			std::float_t maximum_height;
			std::float_t sea_level;
			std::uint32_t seed;
		};
		/*
		//=====================================================================================
		*/
		struct skinned_vertex_s
		{
			vec3_s position;
			vec3_s normal;
			vec4_s tangent;
			vec2_s uv;
			std::uint32_t material;
			std::uint32_t joints;
			std::uint32_t weights;
		};
		/*
		//=====================================================================================
		*/
		struct character_header_s
		{
			std::uint32_t bone_count;
			std::uint32_t vertex_count;
			std::uint32_t index_count;
			std::uint32_t material_count;
			std::uint32_t alpha_first_index;
			vec3_s bounds_min;
			vec3_s bounds_max;
		};
		/*
		//=====================================================================================
		*/
		struct character_bone_s
		{
			char name[bone_name_length];
			std::int32_t parent;
			vec3_s translation;
			quat_s rotation;
			vec3_s scale;
			mat4_s inverse_bind;
		};
		/*
		//=====================================================================================
		*/
		enum clip_track_flags_e : std::uint32_t
		{
			clip_track_translation = 1u
		};
		/*
		//=====================================================================================
		*/
		struct clip_header_s
		{
			std::uint32_t track_count;
			std::uint32_t frame_count;
			std::float_t frame_rate;
			std::float_t duration;
			vec3_s root_velocity;
			std::uint32_t root_track;
		};
		/*
		//=====================================================================================
		*/
		struct clip_track_s
		{
			char name[bone_name_length];
			std::uint32_t flags;
		};
		/*
		//=====================================================================================
		*/
		struct clip_key_s
		{
			quat_s rotation;
			vec3_s translation;
		};
		/*
		//=====================================================================================
		*/
		struct clip_s
		{
			char name[pak_name_length];
			clip_header_s header;
			std::vector<clip_track_s> tracks;
			const clip_key_s* keys;
		};
		/*
		//=====================================================================================
		*/
		struct character_s
		{
			char name[pak_name_length];
			std::vector<character_bone_s> bones;
			std::vector<skinned_vertex_s> vertices;
			std::vector<std::uint32_t> indices;
			std::vector<std::uint32_t> materials;
			std::vector<std::vector<std::int32_t>> clip_tracks;
			std::vector<std::float_t> twist_shares;
			std::vector<std::float_t> blade_shares;
			std::vector<std::float_t> sit_shares;
			std::uint32_t alpha_first_index;
			vec3_s bounds_min;
			vec3_s bounds_max;
			mesh_s mesh;
		};
		/*
		//=====================================================================================
		*/
		struct pose_s
		{
			quat_s rotations[maximum_bones];
			vec3_s translations[maximum_bones];
		};
		/*
		//=====================================================================================
		*/
		enum actor_behavior_e : std::uint32_t
		{
			actor_behavior_idle,
			actor_behavior_wander,
			actor_behavior_player,
			actor_behavior_hostile,
			actor_behavior_remote,
			actor_behavior_corpse
		};
		/*
		//=====================================================================================
		*/
		enum ragdoll_point_e : std::uint32_t
		{
			ragdoll_pelvis,
			ragdoll_chest,
			ragdoll_head,
			ragdoll_left_shoulder,
			ragdoll_left_elbow,
			ragdoll_left_wrist,
			ragdoll_right_shoulder,
			ragdoll_right_elbow,
			ragdoll_right_wrist,
			ragdoll_left_hip,
			ragdoll_left_knee,
			ragdoll_left_ankle,
			ragdoll_right_hip,
			ragdoll_right_knee,
			ragdoll_right_ankle,
			ragdoll_point_count
		};
		/*
		//=====================================================================================
		*/
		struct ragdoll_link_s
		{
			std::uint32_t from;
			std::uint32_t to;
		};
		/*
		//=====================================================================================
		*/
		struct ragdoll_joint_s
		{
			std::uint32_t root;
			std::uint32_t middle;
			std::uint32_t end;
			std::float_t facing;
			std::float_t fold;
		};
		/*
		//=====================================================================================
		*/
		struct ragdoll_s
		{
			vec3_s points[ragdoll_point_count];
			vec3_s previous[ragdoll_point_count];
			std::float_t lengths[26];
			std::float_t spans[4];
			std::int32_t bones[ragdoll_point_count];
			mat4_s frame;
			std::float_t carry;
			std::float_t clock;
			std::float_t calm;
			bool active;
			bool asleep;
		};
		/*
		//=====================================================================================
		*/
		enum actor_rig_e : std::uint32_t
		{
			actor_rig_right_upper,
			actor_rig_right_lower,
			actor_rig_right_hand,
			actor_rig_left_upper,
			actor_rig_left_lower,
			actor_rig_left_hand,
			actor_rig_count
		};
		/*
		//=====================================================================================
		*/
		struct actor_s
		{
			const character_s* character;
			vec3_s position;
			vec3_s velocity;
			vec3_s target;
			vec3_s home;
			std::float_t look_yaw;
			std::float_t look_pitch;
			std::float_t body_yaw;
			std::float_t phase;
			std::float_t idle_time;
			std::float_t speed;
			std::float_t desired_speed;
			std::float_t crouch;
			std::float_t air;
			std::float_t direction;
			std::float_t timer;
			std::uint32_t behavior;
			std::uint32_t seed;
			std::uint32_t frames;
			std::float_t health;
			std::float_t attack;
			std::float_t attack_timer;
			std::float_t hurt;
			std::float_t death;
			std::float_t sight_timer;
			std::float_t forget_timer;
			std::float_t pallor;
			std::float_t clock;
			std::float_t arms;
			std::float_t fall_roll;
			std::float_t voice_timer;
			std::int32_t blocker;
			std::int32_t rig[actor_rig_count];
			std::uint32_t held;
			std::int32_t held_bone;
			std::float_t blade;
			bool holding;
			bool seated;
			bool crouched;
			bool grounded;
			bool turning;
			bool hidden;
			bool alerted;
			bool dead;
			bool looted;
			bool dormant;
			bool struck;
			bool first_person;
			mat4_s world;
			mat4_s previous_world;
			mat4_s view_world;
			mat4_s previous_view_world;
			mat4_s held_offset;
			mat4_s held_world;
			mat4_s previous_held_world;
			std::vector<mat4_s> palette;
			std::vector<mat4_s> previous_palette;
			std::vector<mat4_s> view_palette;
			std::vector<mat4_s> previous_view_palette;
			std::vector<std::int32_t> collapse;
			ragdoll_s ragdoll;
			vec3_s shove;
		};
		/*
		//=====================================================================================
		*/
		enum hold_e : std::uint32_t
		{
			hold_none,
			hold_long,
			hold_pistol,
			hold_tool,
			hold_bow,
			hold_count
		};
		/*
		//=====================================================================================
		*/
		struct hold_pose_s
		{
			vec3_s anchor;
			vec3_s wrist;
			vec3_s support;
			std::float_t pitch;
			std::float_t blade;
			bool left;
		};
		/*
		//=====================================================================================
		*/
		enum species_e : std::uint32_t
		{
			species_stag,
			species_hind,
			species_boar,
			species_horse,
			species_count
		};
		/*
		//=====================================================================================
		*/
		enum animal_state_e : std::uint32_t
		{
			animal_graze,
			animal_idle,
			animal_rest,
			animal_walk,
			animal_alert,
			animal_flee,
			animal_charge,
			animal_dead
		};
		/*
		//=====================================================================================
		*/
		enum animal_clip_e : std::uint32_t
		{
			animal_clip_idle,
			animal_clip_look,
			animal_clip_graze,
			animal_clip_alert,
			animal_clip_walk,
			animal_clip_trot,
			animal_clip_run,
			animal_clip_hit,
			animal_clip_death,
			animal_clip_rest,
			animal_clip_attack,
			animal_clip_count
		};
		/*
		//=====================================================================================
		*/
		struct species_s
		{
			const char* name;
			const char* character;
			const char* lod;
			const char* clips[animal_clip_count];
			std::float_t health;
			std::float_t radius;
			std::float_t half;
			std::float_t center;
			std::float_t walk;
			std::float_t trot;
			std::float_t run;
			std::float_t sight;
			std::float_t hearing;
			std::float_t courage;
			std::uint32_t meat;
			std::uint32_t meat_amount;
			std::uint32_t hide_amount;
			std::uint32_t fat_amount;
			std::uint32_t bone_amount;
			std::float_t facing;
			std::float_t hoof;
			bool enabled;
		};
		/*
		//=====================================================================================
		*/
		struct herd_kind_s
		{
			std::uint32_t leader;
			std::uint32_t member;
			std::uint32_t minimum;
			std::uint32_t maximum;
			std::uint32_t count;
			std::uint32_t habitat;
		};
		/*
		//=====================================================================================
		*/
		struct herd_s
		{
			vec3_s home;
			vec3_s goal;
			std::float_t timer;
			std::float_t empty;
			std::uint32_t kind;
			std::uint32_t first;
			std::uint32_t count;
			std::float_t rest = 0.0f;
		};
		/*
		//=====================================================================================
		*/
		struct watcher_s
		{
			vec3_s position;
			std::float_t noise;
		};
		/*
		//=====================================================================================
		*/
		struct animal_s
		{
			vec3_s position;
			vec3_s velocity;
			vec3_s goal;
			vec3_s threat;
			vec3_s from;
			vec3_s to;
			vec3_s shown;
			std::float_t yaw;
			std::float_t heading;
			std::float_t from_yaw;
			std::float_t to_yaw;
			std::float_t shown_yaw;
			std::float_t health;
			std::float_t timer;
			std::float_t think;
			std::float_t fear;
			std::float_t speed;
			std::float_t shown_speed;
			std::float_t dead_time;
			std::float_t phase;
			std::float_t clip_time;
			std::float_t previous_time;
			std::float_t blend;
			std::float_t hurt;
			std::float_t bleed;
			std::float_t drip;
			std::double_t from_time;
			std::double_t to_time;
			std::double_t seen;
			std::uint32_t species;
			std::uint32_t state;
			std::uint32_t herd;
			std::uint32_t yields;
			std::uint32_t frames;
			std::uint32_t mode;
			std::uint32_t previous_mode;
			std::uint16_t id;
			bool alive;
			mat4_s world;
			mat4_s previous_world;
			std::vector<mat4_s> palette;
			std::vector<mat4_s> previous_palette;
		};
		/*
		//=====================================================================================
		*/
		enum creature_motion_e : std::uint32_t
		{
			creature_still,
			creature_flap,
			creature_swim
		};
		/*
		//=====================================================================================
		*/
		enum wildlife_kind_e : std::uint32_t
		{
			wildlife_gull,
			wildlife_crow,
			wildlife_mackerel,
			wildlife_bass,
			wildlife_kind_count
		};
		/*
		//=====================================================================================
		*/
		struct wildlife_kind_s
		{
			const char* model;
			std::uint32_t motion;
			std::float_t span;
			std::float_t amplitude;
			std::float_t beat;
			std::float_t speed;
			std::float_t radius;
			std::float_t height;
			std::float_t spread;
			std::uint32_t minimum;
			std::uint32_t maximum;
			std::uint32_t groups;
			std::float_t glide;
			std::uint32_t habitat;
			std::float_t roam;
			std::float_t floor_low;
			std::float_t floor_high;
		};
		/*
		//=====================================================================================
		*/
		struct flock_s
		{
			vec3_s home;
			vec3_s center;
			vec3_s heading;
			std::float_t drift;
			std::float_t startle;
			std::float_t lift;
			std::uint32_t kind;
			std::uint32_t first;
			std::uint32_t count;
		};
		/*
		//=====================================================================================
		*/
		struct creature_s
		{
			vec3_s position;
			vec3_s offset;
			vec3_s heading;
			std::float_t angle;
			std::float_t radius;
			std::float_t phase;
			std::float_t bob;
			std::float_t flap;
			std::float_t beat;
			std::float_t timer;
			std::float_t bank;
			std::float_t scare;
			std::float_t turn;
			mat4_s world;
			mat4_s previous_world;
			bool drawn;
		};
		/*
		//=====================================================================================
		*/
		struct skinned_draw_s
		{
			const character_s* character;
			mat4_s world;
			mat4_s previous_world;
			std::uint32_t palette_offset;
			std::uint32_t previous_offset;
			std::uint32_t flags;
			std::float_t pallor;
			std::float_t clearance;
		};
		/*
		//=====================================================================================
		*/
		enum prop_collision_e : std::uint32_t
		{
			prop_collision_none,
			prop_collision_bounds,
			prop_collision_parts,
			prop_collision_clip
		};
		/*
		//=====================================================================================
		*/
		enum draw_flags_e : std::uint32_t
		{
			draw_flag_viewmodel = 1u,
			draw_flag_character = 2u,
			draw_flag_no_shadow = 4u,
			draw_flag_alpha = 8u,
			draw_flag_shadow_only = 16u
		};
		/*
		//=====================================================================================
		*/
		struct draw_item_s
		{
			const mesh_s* mesh;
			mat4_s world;
			mat4_s previous_world;
			std::float_t material_override;
			std::uint32_t flags;
			vec4_s motion;
		};
		/*
		//=====================================================================================
		*/
		struct camera_s
		{
			vec3_s position;
			std::float_t yaw;
			std::float_t pitch;
			std::float_t roll;
			std::float_t vertical_fov;
			std::float_t viewmodel_fov;
			std::float_t aspect;
			vec2_s jitter;
			vec2_s previous_jitter;
			mat4_s view;
			mat4_s projection;
			mat4_s unjittered_projection;
			mat4_s view_projection;
			mat4_s unjittered_view_projection;
			mat4_s previous_view_projection;
			mat4_s viewmodel_projection;
			vec3_s forward;
			vec3_s right;
			vec3_s up;
		};
		/*
		//=====================================================================================
		*/
		struct frame_constants_s
		{
			mat4_s view;
			mat4_s projection;
			mat4_s view_projection;
			mat4_s inverse_view_projection;
			mat4_s previous_view_projection;
			mat4_s unjittered_view_projection;
			mat4_s inverse_view;
			mat4_s inverse_projection;
			mat4_s viewmodel_projection;
			mat4_s inverse_viewmodel_projection;
			vec4_s camera_position;
			vec4_s screen;
			vec4_s jitter;
			vec4_s sun_direction;
			vec4_s sun_color;
			vec4_s sky_params;
			vec4_s exposure_params;
			vec4_s fog_params;
			vec4_s quality_params;
			vec4_s viewmodel_params;
			vec4_s sky_sh[sky_sh_coefficients];
			vec4_s probe_origin;
			vec4_s probe_counts;
			vec4_s light_params;
			vec4_s time_params;
			vec4_s water_params;
			vec4_s water_extinction;
			vec4_s water_scatter;
			vec4_s weather_params;
		};
		/*
		//=====================================================================================
		*/
		struct light_gpu_s
		{
			vec3_s position;
			std::float_t radius;
			vec3_s color;
			std::float_t spot_outer;
			vec3_s direction;
			std::float_t spot_inner;
		};
		/*
		//=====================================================================================
		*/
		struct bvh_node_s
		{
			vec3_s minimum;
			std::uint32_t first;
			vec3_s maximum;
			std::uint32_t count;
		};
		/*
		//=====================================================================================
		*/
		struct ray_triangle_s
		{
			vec3_s v0;
			vec3_s edge1;
			vec3_s edge2;
			vec3_s normal;
			std::uint32_t material;
		};
		/*
		//=====================================================================================
		*/
		struct ray_hit_s
		{
			std::float_t distance;
			std::uint32_t triangle;
			bool backface;
		};
		/*
		//=====================================================================================
		*/
		struct probe_cache_header_s
		{
			std::uint32_t version;
			std::uint32_t count_x;
			std::uint32_t count_y;
			std::uint32_t count_z;
			std::uint64_t hash;
			vec3_s origin;
			std::float_t spacing;
		};
		/*
		//=====================================================================================
		*/
		struct shadow_constants_s
		{
			mat4_s cascade_matrices[shadow_cascade_count];
			vec4_s cascade_splits;
			vec4_s cascade_texel;
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		struct object_constants_s
		{
			mat4_s world;
			mat4_s previous_world;
			vec4_s params;
			vec4_s skin;
			vec4_s motion;
		};
		/*
		//=====================================================================================
		*/
		struct sky_constants_s
		{
			vec4_s params;
			vec4_s face;
		};
		/*
		//=====================================================================================
		*/
		struct atmosphere_constants_s
		{
			vec4_s sun;
			vec4_s moon;
			vec4_s size;
			vec4_s clouds;
			vec4_s zenith;
		};
		/*
		//=====================================================================================
		*/
		struct cloud_constants_s
		{
			vec4_s layer;
			vec4_s wind;
			vec4_s shade;
			vec4_s target;
			vec4_s state;
			vec4_s area;
		};
		/*
		//=====================================================================================
		*/
		struct post_constants_s
		{
			vec4_s params;
			vec4_s grade;
			vec4_s effects;
			vec4_s screen;
		};
		/*
		//=====================================================================================
		*/
		struct exposure_constants_s
		{
			vec4_s settings;
			vec4_s range;
			vec4_s limits;
		};
		/*
		//=====================================================================================
		*/
		struct single_constants_s
		{
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		struct double_constants_s
		{
			vec4_s params;
			vec4_s screen;
		};
		/*
		//=====================================================================================
		*/
		enum quality_e : std::uint32_t
		{
			quality_off,
			quality_low,
			quality_medium,
			quality_high,
			quality_ultra,
			quality_count
		};
		/*
		//=====================================================================================
		*/
		struct graphics_settings_s
		{
			std::uint32_t preset;
			std::float_t render_scale;
			std::uint32_t anti_aliasing;
			std::uint32_t shadows;
			std::uint32_t ambient_occlusion;
			std::uint32_t reflections;
			std::uint32_t volumetrics;
			std::uint32_t clouds;
			std::uint32_t textures;
			std::uint32_t anisotropy;
			std::uint32_t effects;
			bool motion_blur;
			bool depth_of_field;
			bool bloom;
			bool film_grain;
			bool chromatic_aberration;
			bool vignette;
			bool lens_flares;
			std::float_t sharpening;
			std::float_t brightness;
			std::float_t field_of_view;
			std::float_t viewmodel_field_of_view;
			bool vsync;
			std::uint32_t frame_cap;
			std::uint32_t colour_filter;
			std::float_t vegetation;
			std::float_t grass;
			bool marks;
			std::float_t flashes;
		};
		/*
		//=====================================================================================
		*/
		enum surface_e : std::uint32_t
		{
			surface_concrete,
			surface_metal,
			surface_grate,
			surface_wood,
			surface_glass,
			surface_fabric,
			surface_dirt,
			surface_flesh,
			surface_water,
			surface_grass,
			surface_sand,
			surface_rock,
			surface_gravel,
			surface_count
		};
		/*
		//=====================================================================================
		*/
		enum mark_e : std::uint32_t
		{
			mark_stone,
			mark_metal,
			mark_wood,
			mark_earth,
			mark_sand,
			mark_glass,
			mark_fabric,
			mark_print_mud,
			mark_print_sand,
			mark_print_wet,
			mark_blood_spatter,
			mark_blood_drip,
			mark_blood_pool,
			mark_scorch,
			mark_cut,
			mark_count
		};
		/*
		//=====================================================================================
		*/
		struct mark_definition_s
		{
			std::uint32_t cell;
			std::uint32_t variants;
			std::float_t size;
			std::float_t vary;
			std::float_t depth;
			std::float_t life;
			std::float_t fade;
			std::float_t reach;
			std::float_t dry;
			std::float_t grow;
			bool wet;
		};
		/*
		//=====================================================================================
		*/
		struct mark_s
		{
			vec3_s position;
			vec3_s normal;
			vec3_s axis;
			std::float_t size;
			std::double_t born;
			std::int32_t next;
			std::int32_t previous;
			std::uint16_t cell;
			std::uint8_t kind;
			std::uint8_t variant;
			std::uint8_t spin;
			std::uint8_t scale;
			bool live;
			bool guessed;
		};
		/*
		//=====================================================================================
		*/
		struct tread_s
		{
			std::float_t stride;
			std::uint32_t steps;
			std::uint32_t wet;
		};
		/*
		//=====================================================================================
		*/
		struct decal_gpu_s
		{
			vec4_s center;
			vec4_s normal;
			vec4_s axis;
			vec4_s tint;
		};
		/*
		//=====================================================================================
		*/
		struct decal_constants_s
		{
			vec4_s params;
		};
		/*
		//=====================================================================================
		*/
		enum contents_e : std::uint32_t
		{
			contents_solid = 1u,
			contents_player_clip = 2u,
			contents_bullet_clip = 4u,
			contents_glass = 8u,
			contents_water = 16u,
			contents_all = 0xFFFFFFFFu
		};
		/*
		//=====================================================================================
		*/
		struct plane_s
		{
			vec3_s normal;
			std::float_t distance;
		};
		/*
		//=====================================================================================
		*/
		struct brush_s
		{
			std::uint32_t first_plane;
			std::uint32_t plane_count;
			vec3_s bounds_min;
			vec3_s bounds_max;
			std::uint32_t surface;
			std::uint32_t contents;
		};
		/*
		//=====================================================================================
		*/
		struct mover_s
		{
			plane_s planes[12];
			vec3_s bounds_min;
			vec3_s bounds_max;
			std::uint32_t surface;
			std::uint32_t owner;
		};
		/*
		//=====================================================================================
		*/
		struct trace_s
		{
			std::float_t fraction;
			vec3_s end;
			vec3_s normal;
			std::int32_t brush;
			std::uint32_t surface;
			bool start_solid;
			bool all_solid;
			bool hit;
		};
		/*
		//=====================================================================================
		*/
		enum button_e : std::uint32_t
		{
			button_jump = 1u,
			button_crouch = 2u,
			button_sprint = 4u,
			button_fire = 8u,
			button_aim = 16u,
			button_reload = 32u,
			button_use = 64u,
			button_melee = 128u,
			button_visor = 256u,
			button_grenade = 512u,
			button_tactical = 1024u,
			button_walk = 2048u
		};
		/*
		//=====================================================================================
		*/
		struct usercmd_s
		{
			std::uint32_t sequence;
			std::float_t forward;
			std::float_t side;
			std::float_t yaw;
			std::float_t pitch;
			std::uint32_t buttons;
			std::uint32_t weapon;
			std::float_t delta;
			std::double_t time;
		};
		/*
		//=====================================================================================
		*/
		enum weapon_flag_e : std::uint32_t
		{
			weapon_flag_jammed = 1u,
			weapon_flag_cycled = 2u,
			weapon_flag_worked = 4u,
			weapon_flag_fire_held = 8u,
			weapon_flag_reload_held = 16u
		};
		/*
		//=====================================================================================
		*/
		enum weapon_event_e : std::uint32_t
		{
			weapon_event_fired = 1u,
			weapon_event_dry = 2u,
			weapon_event_misfire = 4u,
			weapon_event_dud = 8u,
			weapon_event_jam = 16u,
			weapon_event_reload = 32u,
			weapon_event_reloaded = 64u,
			weapon_event_bolt = 128u,
			weapon_event_cleared = 256u,
			weapon_event_clearing = 512u,
			weapon_event_loosed = 1024u,
			weapon_event_equip = 2048u,
			weapon_event_drawing = 4096u
		};
		/*
		//=====================================================================================
		*/
		enum autotest_e : std::uint32_t
		{
			autotest_walk,
			autotest_gather,
			autotest_build,
			autotest_pluck,
			autotest_plant,
			autotest_shoot,
			autotest_die,
			autotest_raid,
			autotest_ride,
			autotest_done
		};
		/*
		//=====================================================================================
		*/
		enum tool_flag_e : std::uint32_t
		{
			tool_flag_swinging = 1u,
			tool_flag_whoosh = 2u,
			tool_flag_struck = 4u,
			tool_flag_fire_held = 8u,
			tool_flag_use_held = 16u
		};
		/*
		//=====================================================================================
		*/
		enum tool_event_e : std::uint32_t
		{
			tool_event_swing = 1u,
			tool_event_whoosh = 2u,
			tool_event_strike = 4u,
			tool_event_eat = 8u,
			tool_event_use = 16u
		};
		/*
		//=====================================================================================
		*/
		struct tool_state_s
		{
			std::float_t timer;
			std::float_t length;
			std::uint32_t slot;
			std::uint32_t flags;
			std::uint32_t events;
		};
		/*
		//=====================================================================================
		*/
		struct weapon_state_s
		{
			std::uint32_t weapon;
			std::uint32_t slot;
			std::uint32_t seed;
			std::float_t cooldown;
			std::float_t reloading;
			std::float_t clearing;
			std::float_t hangfire;
			std::float_t cycle;
			std::float_t heat;
			std::float_t since_shot;
			std::float_t aim;
			std::float_t draw;
			std::float_t punch_pitch;
			std::float_t punch_yaw;
			std::float_t punch_rise;
			std::float_t power;
			std::uint32_t burst;
			std::uint32_t flags;
			std::uint32_t events;
			std::uint32_t rolls;
			vec3_s shot;
		};
		/*
		//=====================================================================================
		*/
		enum movement_flags_e : std::uint32_t
		{
			movement_on_ground = 1u,
			movement_crouched = 2u,
			movement_sprinting = 4u,
			movement_jump_held = 8u,
			movement_landed = 16u,
			movement_noclip = 32u,
			movement_swimming = 64u,
			movement_underwater = 128u,
			movement_wedged = 256u,
			movement_riding = 512u,
			movement_seated = 1024u
		};
		/*
		//=====================================================================================
		*/
		struct movement_state_s
		{
			vec3_s position;
			vec3_s velocity;
			std::float_t yaw;
			std::float_t pitch;
			std::float_t eye_height;
			std::float_t height;
			std::uint32_t flags;
			std::uint32_t ground_surface;
			std::float_t fall_peak;
			std::float_t landing_speed;
			std::float_t fall_distance;
			std::float_t stride;
			std::float_t speed_scale;
			std::float_t air_time;
			std::float_t water_surface;
			std::float_t water_depth;
			vec3_s ground_normal;
			std::float_t jump_timer;
			std::float_t stuck_time;
			std::float_t step;
			std::int32_t ground;
			std::uint32_t platform;
			vec3_s local;
			std::uint32_t vehicle;
			std::uint32_t seat;
		};
		/*
		//=====================================================================================
		*/
		enum packet_e : std::uint8_t
		{
			packet_query,
			packet_info,
			packet_connect,
			packet_accept,
			packet_reject,
			packet_data,
			packet_disconnect
		};
		/*
		//=====================================================================================
		*/
		enum reject_e : std::uint8_t
		{
			reject_full,
			reject_version,
			reject_closed,
			reject_banned,
			reject_whitelist,
			reject_password,
			reject_duplicate,
			reject_identity,
			reject_count
		};
		/*
		//=====================================================================================
		*/
		enum payload_e : std::uint8_t
		{
			payload_none,
			payload_input,
			payload_snapshot
		};
		/*
		//=====================================================================================
		*/
		enum message_e : std::uint8_t
		{
			message_join,
			message_leave,
			message_chat,
			message_shot,
			message_hit,
			message_death,
			message_respawn,
			message_time,
			message_inventory,
			message_notice,
			message_cue,
			message_request,
			message_node,
			message_nodes,
			message_build,
			message_structures,
			message_container,
			message_act,
			message_crops,
			message_hurt,
			message_bags,
			message_keypad,
			message_sound,
			message_marks
		};
		/*
		//=====================================================================================
		*/
		enum act_e : std::uint8_t
		{
			act_plant,
			act_water,
			act_reap,
			act_drink,
			act_arrow,
			act_loot
		};
		/*
		//=====================================================================================
		*/
		enum request_e : std::uint8_t
		{
			request_swap,
			request_transfer,
			request_craft,
			request_consume,
			request_research,
			request_door,
			request_open,
			request_close,
			request_light,
			request_authorize,
			request_upgrade,
			request_lock,
			request_code,
			request_rekey
		};
		/*
		//=====================================================================================
		*/
		enum death_e : std::uint8_t
		{
			death_fall,
			death_world,
			death_drowned,
			death_shot,
			death_starved,
			death_beaten,
			death_suicide,
			death_frozen,
			death_train,
			death_vehicle
		};
		/*
		//=====================================================================================
		*/
		enum link_state_e : std::uint32_t
		{
			link_idle,
			link_connecting,
			link_connected,
			link_failed
		};
		/*
		//=====================================================================================
		*/
		struct address_s
		{
			std::uint32_t ip;
			std::uint16_t port;

			bool operator==(const address_s& other) const { return ip == other.ip && port == other.port; }
		};
		/*
		//=====================================================================================
		*/
		struct reliable_s
		{
			std::uint16_t id;
			std::uint8_t type;
			std::uint16_t size;
			std::double_t sent_time;
			std::uint8_t data[net_reliable_bytes];
		};
		/*
		//=====================================================================================
		*/
		struct sent_packet_s
		{
			std::uint16_t sequence;
			std::uint8_t count;
			bool used;
			std::double_t time;
			std::uint16_t ids[net_reliable_per_packet];
		};
		/*
		//=====================================================================================
		*/
		struct connection_s
		{
			address_s address;
			std::uint16_t local_sequence;
			std::uint16_t remote_sequence;
			std::uint32_t remote_bits;
			std::uint16_t next_outgoing;
			std::uint16_t next_incoming;
			std::double_t last_received;
			std::double_t last_sent;
			std::float_t rtt;
			std::vector<reliable_s> outgoing;
			std::vector<reliable_s> incoming;
			std::vector<sent_packet_s> sent;
		};
		/*
		//=====================================================================================
		*/
		struct net_command_s
		{
			std::uint32_t sequence;
			std::int8_t forward;
			std::int8_t side;
			std::uint16_t yaw;
			std::int16_t pitch;
			std::uint16_t buttons;
			std::uint8_t slot;
			std::uint32_t time;
		};
		/*
		//=====================================================================================
		*/
		struct net_player_s
		{
			std::uint16_t id;
			std::int16_t position[3];
			std::int8_t velocity[3];
			std::uint16_t yaw;
			std::int8_t pitch;
			std::uint16_t flags;
			std::uint8_t health;
			std::uint8_t item;
		};
		/*
		//=====================================================================================
		*/
		struct trail_s
		{
			std::double_t time;
			vec3_s position;
			std::float_t height;
			bool alive;
		};
		/*
		//=====================================================================================
		*/
		struct shot_event_s
		{
			std::uint16_t shooter;
			std::uint8_t weapon;
			std::uint8_t result;
			vec3_s origin;
			vec3_s end;
		};
		/*
		//=====================================================================================
		*/
		struct server_client_s
		{
			connection_s connection;
			movement_state_s state;
			weapon_state_s weapon;
			tool_state_s tool;
			trail_s trail[net_rewind_samples];
			std::uint32_t trail_head;
			char name[net_name_length];
			std::vector<net_command_s> commands;
			std::uint32_t last_command;
			std::uint32_t item;
			std::uint64_t inventory_hash;
			std::double_t inventory_timer;
			std::float_t respawn_timer;
			std::float_t budget;
			std::float_t yaw;
			std::float_t pitch;
			std::float_t bot_timer;
			std::float_t bot_yaw;
			std::uint32_t echo_stamp;
			std::double_t echo_received;
			std::double_t keypad_clock;
			std::double_t command_time;
			std::double_t struck;
			std::int32_t cell;
			std::vector<std::float_t> priority;
			tread_s tread;
			std::int32_t mark_center;
			std::vector<std::uint16_t> mark_sync;
			std::vector<std::int32_t> mark_fresh;
			bool active;
			bool bot;
			bool alive;
		};
		/*
		//=====================================================================================
		*/
		struct remote_sample_s
		{
			std::double_t time;
			vec3_s position;
			vec3_s velocity;
			std::float_t yaw;
			std::float_t pitch;
			std::uint32_t flags;
			std::uint32_t platform;
			vec3_s local;
		};
		/*
		//=====================================================================================
		*/
		struct remote_player_s
		{
			std::uint16_t id;
			char name[net_name_length];
			std::int32_t actor;
			std::double_t last_seen;
			std::uint32_t item;
			std::float_t health;
			std::float_t stride;
			std::uint32_t count;
			remote_sample_s samples[8];
		};
		/*
		//=====================================================================================
		*/
		struct server_entry_s
		{
			address_s address;
			char name[net_server_name_length];
			char map[32];
			std::uint32_t players;
			std::uint32_t maximum;
			std::float_t ping;
			std::double_t queried;
			bool responded;
			std::uint32_t instance;
			bool locked;
		};
		/*
		//=====================================================================================
		*/
		struct predicted_s
		{
			usercmd_s command;
			bool usable;
			bool moving;
			bool used;
		};
		/*
		//=====================================================================================
		*/
		enum team_e : std::uint32_t
		{
			team_alpha,
			team_bravo,
			team_none,
			team_count = 2u
		};
		/*
		//=====================================================================================
		*/
		enum objective_kind_e : std::uint32_t
		{
			objective_domination,
			objective_flag,
			objective_hill,
			objective_bomb_site,
			objective_zombie_entry
		};
		/*
		//=====================================================================================
		*/
		struct spawn_point_s
		{
			vec3_s position;
			std::float_t yaw;
			std::uint32_t team;
			std::uint32_t flags;
		};
		/*
		//=====================================================================================
		*/
		struct depot_s
		{
			vec3_s position;
			vec3_s facing;
		};
		/*
		//=====================================================================================
		*/
		struct objective_s
		{
			vec3_s position;
			std::float_t radius;
			std::uint32_t kind;
			std::uint32_t team;
			char name[16];
		};
		/*
		//=====================================================================================
		*/
		struct light_s
		{
			vec3_s position;
			std::float_t radius;
			vec3_s color;
			std::float_t spot_cosine;
			vec3_s direction;
			std::uint32_t flags;
		};
		/*
		//=====================================================================================
		*/
		struct map_info_s
		{
			char name[32];
			char sky[64];
			std::float_t sky_rotation;
			std::float_t kill_height;
			vec3_s bounds_min;
			vec3_s bounds_max;
			vec3_s probe_min;
			vec3_s probe_max;
			vec4_s fog;
			std::float_t water_height;
			bool water;
			bool terrain;
			bool probes;
		};
		/*
		//=====================================================================================
		*/
		struct launch_options_s
		{
			bool dedicated;
			bool smoke;
			bool windowed;
			std::uint32_t frames;
			char capture[MAX_PATH];
			char map[64];
			char mode[32];
			char connect[64];
			char password[net_password_length];
			char player_name[net_name_length];
			std::uint32_t weather_test;
			char sky[64];
			std::float_t camera[5];
			bool camera_set;
			bool walk_test;
			bool walk_back;
			bool net_test;
			bool raid_test;
			bool third_person;
			bool camera_ground;
			std::int32_t quality;
			std::int32_t gather_kind;
			std::uint32_t test_item;
			bool test_inventory;
			bool fight_test;
			bool base_test;
			bool aim_test;
			bool fire_test;
			bool chart_test;
			bool farm_test;
			bool spring_test;
			bool fell_test;
			bool marks_test;
			bool keypad_test;
			bool dead_test;
			std::uint32_t ragdoll_test;
			bool title_test;
			bool wake_test;
			bool pause_test;
			bool loading_test;
			std::int32_t menu_page;
			std::uint32_t menu_tab;
			std::uint32_t menu_dialog;
			std::float_t start_hours;
			std::float_t inspect_hands;
			std::float_t showcase_angle;
			std::float_t jam_progress;
			std::float_t reload_progress;
			std::float_t spawn_turn;
			std::float_t spawn_advance;
			std::float_t spawn_pitch;
			std::uint32_t goal_step;
			bool dive_test;
			bool save_test;
			bool ride_test;
			bool impact_test;
			bool trace;
			std::double_t train_time;
			std::int32_t herd_view;
			std::int32_t hunt_herd;
			bool carve_test;
			std::float_t orbit;
			std::float_t orbit_distance;
			std::int32_t flock_view;
			std::int32_t drive_test;
		};
	}

	namespace structures
	{
		enum material_e : std::uint32_t
		{
			material_floor_hangar,
			material_floor_worn,
			material_floor_antislip,
			material_floor_painted,
			material_asphalt,
			material_metal_tread,
			material_floor_garage,
			material_tiles,
			material_wall_slab,
			material_wall_ribbed,
			material_wall_concrete,
			material_facade,
			material_concrete_rough,
			material_metal_blue,
			material_metal_green,
			material_metal_rust,
			material_corrugated,
			material_shutter,
			material_container_green,
			material_metal_sheet,
			material_plywood,
			material_burlap,
			material_polymer,
			material_anodized,
			material_steel,
			material_carbon,
			material_rubber,
			material_fabric_olive,
			material_fabric_dark,
			material_nylon,
			material_skin,
			material_flesh,
			material_panel_light,
			material_panel_dark,
			material_hexgrid,
			material_glass,
			material_knurled,
			material_paint_yellow,
			material_paint_white,
			material_paint_red,
			material_paint_gunmetal,
			material_paint_navy,
			material_light_white,
			material_light_warm,
			material_neon_cyan,
			material_neon_orange,
			material_screen,
			material_container_red,
			material_container_blue,
			material_water,
			material_deck,
			material_deck_line_yellow,
			material_deck_line_white,
			material_hull,
			material_tire,
			material_bulkhead,
			material_bulkhead_light,
			material_tread_plate,
			material_corrugated_steel,
			material_grating,
			material_rubber_mat,
			material_terrain_grass,
			material_terrain_grass_dry,
			material_terrain_forest,
			material_terrain_dirt,
			material_terrain_rock,
			material_terrain_cliff,
			material_terrain_sand,
			material_terrain_gravel,
			material_terrain_needles,
			material_terrain_heath,
			material_terrain_moor,
			material_terrain_marsh,
			material_terrain_dune,
			material_terrain_shingle,
			material_terrain_turf,
			material_terrain_soil,
			material_berry,
			material_pond,
			material_count
		};
	}

	constexpr structures::material_definition_s material_definitions[structures::material_count] =
	{
		{ "floor_hangar", "hangar_concrete_floor", { 2.8f, 2.8f, 2.8f }, 0.35f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "floor_worn", "concrete_floor_worn_001", { 1.0f, 1.0f, 1.0f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "floor_antislip", "anti_slip_concrete", { 0.85f, 0.85f, 0.85f }, 0.5f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "floor_painted", "painted_concrete_02", { 1.0f, 1.0f, 1.0f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "asphalt", "asphalt_03", { 1.0f, 1.0f, 1.0f }, 0.3f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "metal_tread", "metal_plate", { 1.0f, 1.0f, 1.0f }, 0.8f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "floor_garage", "garage_floor", { 0.8f, 0.8f, 0.8f }, 0.3f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "tiles", "interior_tiles", { 1.0f, 1.0f, 1.0f }, 0.8f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "wall_slab", "concrete_slab_wall_02", { 0.85f, 0.85f, 0.85f }, 0.3f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "wall_ribbed", "ribbed_concrete_wall", { 1.2f, 1.2f, 1.2f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "wall_concrete", "concrete_wall_006", { 1.1f, 1.1f, 1.1f }, 0.35f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "facade", "concrete_tile_facade", { 1.6f, 1.6f, 1.6f }, 0.35f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "concrete_rough", "rough_concrete", { 0.7f, 0.7f, 0.7f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "metal_blue", "blue_metal_plate", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "metal_green", "green_metal_rust", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "metal_rust", "rusty_metal_02", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "corrugated", "corrugated_iron_02", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 1.0f, 0.0f, 1.2f, structures::material_flag_parallax, {} },
		{ "shutter", "painted_metal_shutter", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "container_green", "container_side", { 1.0f, 1.0f, 1.0f }, 0.35f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "metal_sheet", "metal_plate_02", { 1.0f, 1.0f, 1.0f }, 0.6f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "plywood", "plywood", { 1.0f, 1.0f, 1.0f }, 0.8f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "burlap", "hessian_230", { 1.0f, 1.0f, 1.0f }, 2.5f, 1.0f, 0.1f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "polymer", "polymer", { 1.0f, 1.0f, 1.0f }, 6.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "anodized", "anodized", { 1.0f, 1.0f, 1.0f }, 4.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "steel", "steel", { 1.0f, 1.0f, 1.0f }, 3.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "carbon", "carbon", { 1.0f, 1.0f, 1.0f }, 8.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "rubber", "rubber", { 1.0f, 1.0f, 1.0f }, 8.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "fabric_olive", "fabric", { 0.55f, 0.55f, 0.42f }, 3.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "fabric_dark", "fabric", { 0.22f, 0.23f, 0.25f }, 3.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "nylon", "nylon", { 0.35f, 0.36f, 0.34f }, 4.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "skin", "skin", { 1.0f, 1.0f, 1.0f }, 1.5f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "flesh", "flesh", { 1.0f, 1.0f, 1.0f }, 2.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "panel_light", "panel", { 1.9f, 1.9f, 1.95f }, 0.5f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "panel_dark", "panel", { 0.45f, 0.47f, 0.5f }, 0.5f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "hexgrid", "hexgrid", { 1.0f, 1.0f, 1.0f }, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "glass", "glass", { 0.03f, 0.035f, 0.04f }, 0.5f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_glass, {} },
		{ "knurled", "knurled", { 1.0f, 1.0f, 1.0f }, 12.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "paint_yellow", "painted_steel", { 1.95f, 1.45f, 0.12f }, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "paint_white", "painted_steel", { 1.9f, 1.9f, 1.85f }, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "paint_red", "painted_steel", { 1.4f, 0.18f, 0.12f }, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "paint_gunmetal", "Metal027", { 4.0f, 4.0f, 4.2f }, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "paint_navy", "painted_steel", { 0.22f, 0.3f, 0.42f }, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "light_white", "glass", { 1.0f, 1.0f, 1.0f }, 1.0f, 0.0f, 0.3f, 0.0f, 0.0f, 0.0f, structures::material_flag_unlit, { 40.0f, 40.0f, 38.0f } },
		{ "light_warm", "glass", { 1.0f, 1.0f, 1.0f }, 1.0f, 0.0f, 0.3f, 0.0f, 0.0f, 0.0f, structures::material_flag_unlit, { 40.0f, 28.0f, 16.0f } },
		{ "neon_cyan", "glass", { 0.0f, 0.0f, 0.0f }, 1.0f, 0.0f, 0.3f, 0.0f, 0.0f, 0.0f, structures::material_flag_unlit, { 0.0f, 28.0f, 40.0f } },
		{ "neon_orange", "glass", { 0.0f, 0.0f, 0.0f }, 1.0f, 0.0f, 0.3f, 0.0f, 0.0f, 0.0f, structures::material_flag_unlit, { 40.0f, 14.0f, 0.0f } },
		{ "screen", "hexgrid", { 0.0f, 0.0f, 0.0f }, 6.0f, 0.3f, 0.05f, 0.0f, 0.0f, 0.2f, structures::material_flag_unlit, { 2.0f, 6.0f, 9.0f } },
		{ "container_red", "container_side", { 1.8f, 0.45f, 0.5f }, 0.35f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "container_blue", "container_side", { 0.3f, 0.6f, 2.2f }, 0.35f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "water", "glass", { 0.012f, 0.03f, 0.045f }, 0.05f, 0.0f, 0.04f, 0.0f, 0.0f, 0.0f, 0u, {} },
		{ "deck", "asphalt_03", { 1.0f, 1.45f, 2.05f }, 0.25f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "deck_line_yellow", "painted_concrete_02", { 2.6f, 2.0f, 0.3f }, 0.5f, 1.0f, 0.05f, 0.0f, 0.0f, 0.6f, 0u, {} },
		{ "deck_line_white", "painted_concrete_02", { 2.4f, 2.4f, 2.4f }, 0.5f, 1.0f, 0.05f, 0.0f, 0.0f, 0.6f, 0u, {} },
		{ "hull", "green_metal_rust_grey", { 2.9f, 3.05f, 3.3f }, 0.5f, 1.0f, 0.05f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "tire", "rubber", { 1.0f, 1.0f, 1.0f }, 2.0f, 1.0f, 0.05f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "bulkhead", "blue_metal_plate_grey", { 5.2f, 5.45f, 5.9f }, 0.4f, 1.0f, 0.05f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "bulkhead_light", "blue_metal_plate_grey", { 7.0f, 7.2f, 7.6f }, 0.4f, 1.0f, 0.05f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "tread_plate", "DiamondPlate008A", { 1.5f, 1.5f, 1.5f }, 1.2f, 1.0f, 0.1f, 1.0f, 0.0f, 1.0f, 0u, {} },
		{ "corrugated_steel", "CorrugatedSteel005", { 0.9f, 0.95f, 1.0f }, 0.6f, 1.0f, 0.1f, 1.0f, 0.0f, 1.0f, structures::material_flag_parallax, {} },
		{ "grating", "SheetMetal002", { 0.7f, 0.7f, 0.7f }, 1.5f, 1.0f, 0.2f, 1.0f, 0.0f, 1.0f, structures::material_flag_alpha_test, {} },
		{ "rubber_mat", "Rubber004", { 1.6f, 1.6f, 1.6f }, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_grass", "leafy_grass", { 0.29f, 0.5f, 0.36f }, 0.45f, 1.0f, 0.05f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_grass_dry", "withered_grass", { 0.5f, 0.56f, 0.5f }, 0.45f, 1.0f, 0.05f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_forest", "forest_leaves_02", { 0.45f, 0.52f, 0.8f }, 0.3f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_dirt", "brown_mud_02", { 1.15f, 1.12f, 1.1f }, 0.6f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_rock", "rocks_ground_05", { 0.85f, 0.87f, 0.9f }, 0.3f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_triplanar, {} },
		{ "terrain_cliff", "mossy_rock", { 0.95f, 0.97f, 1.05f }, 0.16f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, structures::material_flag_triplanar, {} },
		{ "terrain_sand", "gravelly_sand", { 1.0f, 1.55f, 2.45f }, 0.38f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_gravel", "ganges_river_pebbles", { 0.9f, 0.92f, 0.95f }, 0.42f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_needles", "ground_needles", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_heath", "ground_heath", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_moor", "ground_moor", { 1.0f, 1.0f, 1.0f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_marsh", "ground_marsh", { 1.0f, 1.0f, 1.0f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_dune", "ground_dune", { 0.62f, 0.62f, 0.62f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_shingle", "ground_shingle", { 1.0f, 1.0f, 1.0f }, 0.4f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_turf", "ground_turf", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_soil", "ground_soil", { 1.0f, 1.0f, 1.0f }, 0.5f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "berry", "painted_steel", { 0.9f, 0.04f, 0.08f }, 3.0f, 0.4f, 0.0f, 0.0f, 0.0f, 0.3f, 0u, {} },
		{ "pond", "brown_mud_02", { 0.05f, 0.06f, 0.055f }, 0.9f, 0.0f, 0.13f, 0.0f, 0.0f, 0.22f, 0u, {} }
	};

	constexpr structures::item_definition_s item_definitions[structures::item_count] =
	{
		{ "Nothing", "", structures::item_category_resource, 0u, 5.0f, 0.0f, 0.0f, 0.6f, 1.6f, 0.0f, 0.0f, 0.0f },
		{ "Wood", "Basic building and crafting material.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Stone", "Used for tools and stone construction.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Metal ore", "Smelt in a furnace to get metal fragments.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Sulfur ore", "Smelt in a furnace to get sulfur.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Metal fragments", "Refined metal for better tools.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Cloth", "Woven hemp fibre.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Scrap", "Salvaged parts from the old world.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Charcoal", "Burnt wood.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Rock", "A rock. Better than nothing.", structures::item_category_tool, 1u, 10.0f, 0.5f, 0.5f, 0.8f, 1.9f, 0.0f, 0.0f, 0.0f },
		{ "Torch", "Lights the way. Can be swung in a pinch.", structures::item_category_tool, 1u, 8.0f, 0.0f, 0.0f, 0.75f, 1.9f, 0.0f, 0.0f, 0.0f },
		{ "Stone hatchet", "Chops trees much faster than a rock.", structures::item_category_tool, 1u, 18.0f, 1.0f, 0.3f, 0.85f, 2.1f, 0.0f, 0.0f, 0.0f },
		{ "Stone pickaxe", "Breaks rock and ore nodes.", structures::item_category_tool, 1u, 16.0f, 0.3f, 1.0f, 0.95f, 2.1f, 0.0f, 0.0f, 0.0f },
		{ "Wooden spear", "Long reach, strong thrust.", structures::item_category_weapon, 1u, 35.0f, 0.1f, 0.05f, 1.0f, 2.8f, 0.0f, 0.0f, 0.0f },
		{ "Hunting bow", "Quiet, patient and deadly. Hold to draw, release to loose.", structures::item_category_weapon, 1u, 62.0f, 0.0f, 0.0f, 1.2f, 1.9f, 0.0f, 0.0f, 0.0f, structures::weapon_bow },
		{ "Wooden arrow", "Flint head, sinew and feathers.", structures::item_category_ammunition, 64u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Bandage", "Stops bleeding and restores a little health.", structures::item_category_medical, 3u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 15.0f },
		{ "Berries", "Wild berries. Mostly safe.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 35.0f, 12.0f, 1.0f },
		{ "Canned beans", "Old world food. Still good. Probably.", structures::item_category_food, 10u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 120.0f, 10.0f, 2.0f },
		{ "Water bottle", "Clean water.", structures::item_category_food, 5u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 90.0f, 0.0f },
		{ "Campfire", "Warmth, light and cooking.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Sleeping bag", "Respawn point.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Wooden door", "Keeps the dead out.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Building plan", "Plan foundations, walls and floors.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Hammer", "Upgrade and repair structures.", structures::item_category_tool, 1u, 8.0f, 0.0f, 0.0f, 0.7f, 1.9f, 0.0f, 0.0f, 0.0f },
		{ "Storage box", "Keeps your things safe.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Furnace", "Smelts ore with wood as fuel.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Sulfur", "Refined sulfur for gunpowder.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Gunpowder", "Charcoal and sulfur, ground fine.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Pipe shells", "Black powder and nails packed in scrap casings.", structures::item_category_ammunition, 64u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Rifle rounds", "Hand-poured lead in salvaged brass.", structures::item_category_ammunition, 64u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Pipe pistol", "Two pipes, a rubber band and a prayer.", structures::item_category_weapon, 1u, 48.0f, 0.0f, 0.0f, 0.0f, 1.6f, 0.0f, 0.0f, 0.0f, structures::weapon_pistol },
		{ "Scrap rifle", "Salvage, vine and patience.", structures::item_category_weapon, 1u, 85.0f, 0.0f, 0.0f, 0.0f, 1.6f, 0.0f, 0.0f, 0.0f, structures::weapon_rifle },
		{ "Potato", "Raw and starchy. Bake it, or bury it and grow more.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 35.0f, 6.0f, -1.0f, structures::weapon_none, structures::crop_potato },
		{ "Baked potato", "Hot, soft and filling.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 130.0f, 4.0f, 3.0f },
		{ "Corn", "Hard on the teeth raw. Plant the cob to grow a stalk.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 30.0f, 12.0f, 0.0f, structures::weapon_none, structures::crop_corn },
		{ "Roasted corn", "Charred and sweet.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 110.0f, 8.0f, 2.0f },
		{ "Pumpkin", "Heavy and watery. The seeds inside will grow.", structures::item_category_food, 5u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 50.0f, 35.0f, 0.0f, structures::weapon_none, structures::crop_pumpkin },
		{ "Roasted pumpkin", "Soft, sweet and warming.", structures::item_category_food, 5u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 160.0f, 30.0f, 5.0f },
		{ "Hemp seeds", "Push them into open soil to grow hemp.", structures::item_category_farming, 50u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, structures::weapon_none, structures::crop_hemp },
		{ "Well", "Dig down to fresh water. Crops around it stay watered.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Scrap AR", "Box tube, pipe and hope. Fully automatic, when it feels like it.", structures::item_category_weapon, 1u, 30.0f, 0.0f, 0.0f, 0.0f, 1.6f, 0.0f, 0.0f, 0.0f, structures::weapon_assault },
		{ "Workbench I", "A crude bench of planks and salvage. Tier I crafting within a few steps.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Workbench II", "Steel top, a vise and real tools. Tier II crafting within a few steps.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Workbench III", "A salvaged machine shop. Tier III crafting within a few steps.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Research table", "Tear scrap apart until it tells you how things are made.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Blueprint", "Someone's notes on how to make something. Learned when picked up.", structures::item_category_resource, 10u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Vacuum valve", "A glass valve from an old transmitter. Somehow not broken.", structures::item_category_resource, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Copper coil", "Hand-wound copper on a ceramic former. Radio parts.", structures::item_category_resource, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Battery", "A heavy lead battery that still holds a charge.", structures::item_category_resource, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Tool cupboard", "Claims the land around it. Only people you trust can build nearby or open your doors.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Code lock", "Four digits between your door and everyone else. Wrong guesses bite.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Raw venison", "Dark red deer meat. Cook it before you eat it.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 25.0f, 2.0f, -6.0f },
		{ "Cooked venison", "Lean, rich and filling.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 160.0f, 4.0f, 4.0f },
		{ "Raw pork", "Wild boar meat. Never eat it raw.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 20.0f, 2.0f, -9.0f },
		{ "Cooked pork", "Fatty, salty and very filling.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 190.0f, 2.0f, 3.0f },
		{ "Raw horse meat", "Tough, dark meat. Cook it first.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 25.0f, 2.0f, -6.0f },
		{ "Cooked horse meat", "Chewy, but it keeps you going.", structures::item_category_food, 20u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 150.0f, 4.0f, 3.0f },
		{ "Animal fat", "Rendered from a carcass. Burns slowly and keeps leather supple.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Hide", "A raw animal skin. Scrape it and it becomes leather.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ "Bone", "Hard and sharp when broken. Good for tools.", structures::item_category_resource, 1000u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f }
	};

	constexpr structures::crop_definition_s crop_definitions[structures::crop_count] =
	{
		{},
		{ "Potato plant", "potato_plant", structures::item_potato, 3u, 5u, structures::item_none, 0u, 0u, 540.0f, 1.0f },
		{ "Corn", "corn_stalk", structures::item_corn, 2u, 3u, structures::item_none, 0u, 0u, 720.0f, 1.0f },
		{ "Hemp", "hemp_plant", structures::item_cloth, 12u, 20u, structures::item_hemp_seeds, 1u, 3u, 480.0f, 1.0f },
		{ "Pumpkin vine", "pumpkin_patch", structures::item_pumpkin, 1u, 2u, structures::item_none, 0u, 0u, 840.0f, 1.0f }
	};

	constexpr structures::conversion_s smelt_conversions[] = { { structures::item_metal_ore, structures::item_metal_fragments }, { structures::item_sulfur_ore, structures::item_sulfur } };
	constexpr structures::conversion_s cook_conversions[] = { { structures::item_potato, structures::item_baked_potato }, { structures::item_corn, structures::item_roasted_corn }, { structures::item_pumpkin, structures::item_roasted_pumpkin }, { structures::item_raw_venison, structures::item_cooked_venison }, { structures::item_raw_pork, structures::item_cooked_pork }, { structures::item_raw_horse, structures::item_cooked_horse } };

	constexpr structures::recipe_s recipes[] =
	{
		{ structures::item_stone_hatchet, 1u, 12.0f, { { structures::item_wood, 200u }, { structures::item_stone, 100u }, {} }, 0u, true },
		{ structures::item_stone_pickaxe, 1u, 12.0f, { { structures::item_wood, 200u }, { structures::item_stone, 100u }, {} }, 0u, true },
		{ structures::item_wooden_spear, 1u, 8.0f, { { structures::item_wood, 300u }, {}, {} }, 0u, true },
		{ structures::item_hunting_bow, 1u, 20.0f, { { structures::item_wood, 200u }, { structures::item_cloth, 50u }, {} }, 0u, true },
		{ structures::item_wooden_arrow, 2u, 4.0f, { { structures::item_wood, 25u }, { structures::item_stone, 10u }, {} }, 0u, true },
		{ structures::item_torch, 1u, 3.0f, { { structures::item_wood, 30u }, { structures::item_cloth, 1u }, {} }, 0u, true },
		{ structures::item_bandage, 1u, 4.0f, { { structures::item_cloth, 4u }, {}, {} }, 0u, true },
		{ structures::item_campfire, 1u, 6.0f, { { structures::item_wood, 100u }, {}, {} }, 0u, true },
		{ structures::item_sleeping_bag, 1u, 10.0f, { { structures::item_cloth, 30u }, {}, {} }, 0u, true },
		{ structures::item_building_plan, 1u, 5.0f, { { structures::item_wood, 50u }, {}, {} }, 0u, true },
		{ structures::item_hammer, 1u, 5.0f, { { structures::item_wood, 100u }, {}, {} }, 0u, true },
		{ structures::item_wooden_door, 1u, 15.0f, { { structures::item_wood, 300u }, {}, {} }, 0u, true },
		{ structures::item_storage_box, 1u, 10.0f, { { structures::item_wood, 100u }, {}, {} }, 0u, true },
		{ structures::item_cupboard, 1u, 15.0f, { { structures::item_wood, 300u }, {}, {} }, 0u, true },
		{ structures::item_furnace, 1u, 20.0f, { { structures::item_stone, 250u }, { structures::item_wood, 100u }, {} }, 0u, true },
		{ structures::item_workbench_1, 1u, 25.0f, { { structures::item_wood, 300u }, { structures::item_metal_fragments, 60u }, { structures::item_scrap, 20u } }, 0u, true },
		{ structures::item_research_table, 1u, 20.0f, { { structures::item_metal_fragments, 150u }, { structures::item_wood, 100u }, { structures::item_scrap, 20u } }, 1u, true },
		{ structures::item_workbench_2, 1u, 40.0f, { { structures::item_metal_fragments, 400u }, { structures::item_scrap, 100u }, { structures::item_wood, 100u } }, 1u, true },
		{ structures::item_workbench_3, 1u, 60.0f, { { structures::item_metal_fragments, 800u }, { structures::item_scrap, 250u }, { structures::item_cloth, 50u } }, 2u, true },
		{ structures::item_well, 1u, 25.0f, { { structures::item_stone, 300u }, { structures::item_wood, 150u }, {} }, 1u, false },
		{ structures::item_gunpowder, 10u, 5.0f, { { structures::item_charcoal, 10u }, { structures::item_sulfur, 10u }, {} }, 1u, false },
		{ structures::item_pistol_ammo, 2u, 5.0f, { { structures::item_gunpowder, 8u }, { structures::item_metal_fragments, 6u }, { structures::item_scrap, 1u } }, 1u, false },
		{ structures::item_pistol, 1u, 30.0f, { { structures::item_metal_fragments, 60u }, { structures::item_wood, 80u }, { structures::item_scrap, 15u } }, 1u, false },
		{ structures::item_rifle_ammo, 2u, 6.0f, { { structures::item_gunpowder, 12u }, { structures::item_metal_fragments, 10u }, { structures::item_scrap, 1u } }, 2u, false },
		{ structures::item_rifle, 1u, 45.0f, { { structures::item_metal_fragments, 150u }, { structures::item_wood, 150u }, { structures::item_scrap, 40u } }, 2u, false },
		{ structures::item_assault_rifle, 1u, 60.0f, { { structures::item_metal_fragments, 250u }, { structures::item_wood, 60u }, { structures::item_scrap, 70u } }, 3u, false },
		{ structures::item_code_lock, 1u, 10.0f, { { structures::item_metal_fragments, 100u }, {}, {} }, 0u, true }
	};
	constexpr auto recipe_count = std::size(recipes);
	constexpr auto recipe_capacity = 64u;
	constexpr auto legacy_recipe_count = 26u;

	static_assert(recipe_count <= recipe_capacity);

	namespace structures
	{
		struct loot_bag_s
		{
			vec3_s position;
			std::float_t yaw;
			std::float_t timer;
			item_stack_s slots[total_slots];
			char name[net_name_length];
			std::int32_t actor;
			std::uint32_t items;
			std::uint32_t sleeper;
			std::float_t health;
			bool active;
		};
		/*
		//=====================================================================================
		*/
		struct player_record_s
		{
			char name[net_name_length];
			vec3_s position;
			std::float_t yaw;
			vitals_s vitals;
			item_stack_s slots[total_slots];
			craft_job_s queue[crafting_queue_size];
			std::uint32_t queue_count;
			bool known[recipe_capacity];
			bool alive;
		};
		/*
		//=====================================================================================
		*/
		struct legacy_record_s
		{
			char name[net_name_length];
			vec3_s position;
			std::float_t yaw;
			vitals_s vitals;
			item_stack_s slots[total_slots];
			craft_job_s queue[crafting_queue_size];
			std::uint32_t queue_count;
			bool known[legacy_recipe_count];
			bool alive;
		};
		/*
		//=====================================================================================
		*/
		struct lock_s
		{
			std::uint32_t owner;
			std::uint32_t code;
			bool coded;
			std::vector<std::uint32_t> authorized;
		};
	}

	constexpr std::uint32_t research_costs[4] = { 10u, 40u, 90u, 220u };
	constexpr const char* tier_names[4] = { "Hands", "Workbench I", "Workbench II", "Workbench III" };
	constexpr auto workbench_range = 4.0f;
	constexpr auto blueprint_scrap = 25u;

	constexpr structures::goal_s goals[] =
	{
		{ "Find your feet", "Punch or chop a tree until you have 100 wood.", structures::goal_have, structures::item_wood, 100u, structures::item_none, 0u },
		{ "Stone", "Hit rocks and boulders for 60 stone.", structures::goal_have, structures::item_stone, 60u, structures::item_none, 0u },
		{ "A proper tool", "Open your notes with Tab and craft a stone hatchet.", structures::goal_have, structures::item_stone_hatchet, 1u, structures::item_none, 0u },
		{ "A place to sleep", "Pick hemp for cloth, craft a sleeping bag and lay it down. You wake there if you die.", structures::goal_place, structures::piece_sleeping_bag, 1u, structures::item_none, 0u },
		{ "Fire", "Craft and place a campfire to cook and keep warm through the night.", structures::goal_place, structures::piece_campfire, 1u, structures::item_none, 0u },
		{ "Scavenger", "Break barrels and search the houses of Saint Aubin. Carry 40 scrap.", structures::goal_have, structures::item_scrap, 40u, structures::item_cloth, 20u },
		{ "Melt it down", "Build a furnace, feed it wood and metal ore, and make 80 metal fragments.", structures::goal_have, structures::item_metal_fragments, 80u, structures::item_none, 0u },
		{ "Workbench", "Craft and place Workbench I. Better things need a bench close by.", structures::goal_place, structures::piece_workbench_1, 1u, structures::item_blueprint, 1u },
		{ "Take it apart", "Build a research table and spend scrap to learn a recipe.", structures::goal_research, 0u, 1u, structures::item_none, 0u },
		{ "The Signal Post", "An antenna still stands at the Signal Post. Find it on your map (M).", structures::goal_reach, structures::landmark_outpost, 0u, structures::item_none, 0u },
		{ "Dead air", "The transmitter needs a valve, a coil and a battery. Search crates at Breaker's Yard, Saint Aubin and the Signal Post.", structures::goal_parts, 0u, 3u, structures::item_none, 0u },
		{ "Call for help", "Climb the Signal Post tower and repair the radio.", structures::goal_repair, 0u, 0u, structures::item_none, 0u },
		{ "Hold out", "A trawler heard you. It will come in three days. Stay alive.", structures::goal_wait, 0u, 3u, structures::item_none, 0u },
		{ "Morning Star", "At first light, go down to the shore and wave the boat in.", structures::goal_rescue, 0u, 0u, structures::item_none, 0u },
		{ "Rescued", "You made it off the island. It is still out there if you want it.", structures::goal_free, 0u, 0u, structures::item_none, 0u }
	};
	constexpr auto goal_count = std::size(goals);
	constexpr std::uint32_t radio_parts[3] = { structures::item_radio_coil, structures::item_radio_battery, structures::item_radio_valve };
	constexpr auto radio_part_chance = 0.4f;
	constexpr auto radio_part_pity = 3u;
	constexpr auto radio_reach = 2.6f;
	constexpr auto rescue_dawn = 5.5f;
	constexpr auto rescue_dusk = 9.5f;
	constexpr auto rescue_shore = 1.8f;
	constexpr auto dawn_hour = 6.0f;
	constexpr auto outpost_mast = 18.0f;

	constexpr auto fell_range = 180.0f;
	constexpr auto fell_rest = 1.47f;
	constexpr auto fell_linger = 7.0f;
	constexpr auto fell_sink = 3.0f;
	constexpr std::float_t node_respawn[structures::node_kind_count] = { 1500.0f, 1800.0f, 1200.0f, 1500.0f, 1500.0f, 600.0f, 600.0f, 900.0f, 420.0f, 420.0f, 420.0f, 420.0f, 720.0f, 720.0f, 720.0f };
	constexpr const char* node_names[structures::node_kind_count] = { "Tree", "Dead tree", "Stone", "Metal ore", "Sulfur ore", "Hemp", "Berry bush", "Barrel", "Tool chest", "Supply box", "Military crate", "Medical kit", "Wild potato", "Wild corn", "Wild pumpkin" };
	constexpr std::float_t node_health[structures::node_kind_count] = { 420.0f, 240.0f, 300.0f, 260.0f, 260.0f, 1.0f, 1.0f, 40.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f };
	constexpr const char* node_models[structures::node_kind_count] = { "", "", "", "", "", "", "", "", "metal_tool_chest", "cardboard_box_01", "old_military_crate", "medical_box", "", "", "" };

	constexpr structures::loot_entry_s loot_barrel[] = { { structures::item_scrap, 2u, 5u, 1.0f }, { structures::item_metal_fragments, 5u, 15u, 0.4f }, { structures::item_cloth, 5u, 10u, 0.3f }, { structures::item_canned_beans, 1u, 1u, 0.25f }, { structures::item_water_bottle, 1u, 1u, 0.25f }, { structures::item_bandage, 1u, 1u, 0.15f } };
	constexpr structures::loot_entry_s loot_toolbox[] = { { structures::item_scrap, 3u, 8u, 1.0f }, { structures::item_metal_fragments, 10u, 30u, 0.6f }, { structures::item_stone_hatchet, 1u, 1u, 0.12f }, { structures::item_stone_pickaxe, 1u, 1u, 0.12f }, { structures::item_hammer, 1u, 1u, 0.1f }, { structures::item_pistol_ammo, 4u, 10u, 0.1f }, { structures::item_gunpowder, 5u, 15u, 0.12f }, { structures::item_blueprint, 1u, 1u, 0.05f } };
	constexpr structures::loot_entry_s loot_box[] = { { structures::item_cloth, 4u, 12u, 0.7f }, { structures::item_canned_beans, 1u, 2u, 0.45f }, { structures::item_water_bottle, 1u, 1u, 0.45f }, { structures::item_berries, 2u, 5u, 0.3f }, { structures::item_scrap, 1u, 3u, 0.4f } };
	constexpr structures::loot_entry_s loot_military[] = { { structures::item_scrap, 6u, 14u, 1.0f }, { structures::item_metal_fragments, 25u, 60u, 0.7f }, { structures::item_pistol_ammo, 2u, 6u, 0.25f }, { structures::item_rifle_ammo, 2u, 4u, 0.12f }, { structures::item_gunpowder, 10u, 25u, 0.2f }, { structures::item_bandage, 1u, 3u, 0.5f }, { structures::item_blueprint, 1u, 1u, 0.18f } };
	constexpr structures::loot_entry_s loot_medical[] = { { structures::item_bandage, 2u, 4u, 1.0f }, { structures::item_water_bottle, 1u, 1u, 0.3f }, { structures::item_cloth, 3u, 6u, 0.3f } };
	constexpr structures::loot_entry_s loot_corpse[] = { { structures::item_cloth, 3u, 8u, 1.0f }, { structures::item_scrap, 1u, 3u, 0.55f }, { structures::item_berries, 2u, 4u, 0.3f }, { structures::item_bandage, 1u, 1u, 0.2f }, { structures::item_water_bottle, 1u, 1u, 0.12f }, { structures::item_canned_beans, 1u, 1u, 0.08f } };
	constexpr structures::loot_table_s corpse_loot{ loot_corpse, std::size(loot_corpse) };
	constexpr structures::loot_table_s node_loot[structures::node_kind_count] = { {}, {}, {}, {}, {}, {}, {}, { loot_barrel, std::size(loot_barrel) }, { loot_toolbox, std::size(loot_toolbox) }, { loot_box, std::size(loot_box) }, { loot_military, std::size(loot_military) }, { loot_medical, std::size(loot_medical) }, {}, {}, {} };

	constexpr const char* item_category_names[structures::item_category_count] = { "Resources", "Tools", "Weapons", "Ammunition", "Medical", "Food", "Construction", "Farming" };

	constexpr structures::viewmodel_key_s viewmodel_swing[] =
	{
		{ 0.0f, { 0.2f, -0.08f, 0.42f }, { 0.3f, -0.25f, 0.0f } },
		{ 0.26f, { 0.21f, -0.03f, 0.36f }, { -0.8f, 0.1f, -0.25f } },
		{ 0.4f, { 0.04f, -0.03f, 0.48f }, { 1.1f, -0.35f, 0.15f } },
		{ 0.56f, { 0.06f, -0.07f, 0.46f }, { 0.95f, -0.3f, 0.1f } },
		{ 1.0f, { 0.2f, -0.08f, 0.42f }, { 0.3f, -0.25f, 0.0f } }
	};

	constexpr structures::viewmodel_key_s viewmodel_holds[structures::item_count] =
	{
		{},
		{},
		{},
		{},
		{},
		{},
		{},
		{},
		{},
		{ 0.0f, { 0.0f, 0.02f, -0.02f }, { -0.1f, 0.0f, 0.0f } },
		{ 0.0f, { 0.0f, -0.02f, 0.0f }, { 0.25f, 0.0f, 0.35f } },
		{ 0.0f, { 0.0f, -0.03f, 0.02f }, { 0.45f, 0.05f, 0.45f } },
		{ 0.0f, { 0.0f, -0.03f, 0.02f }, { 0.45f, 0.05f, 0.45f } },
		{ 0.0f, { 0.02f, -0.03f, -0.04f }, { 1.05f, 0.1f, 0.0f } }
	};

	constexpr structures::piece_definition_s piece_definitions[structures::piece_count] =
	{
		{ "Foundation", structures::item_building_plan, { structures::item_wood, 50u }, 600.0f },
		{ "Wall", structures::item_building_plan, { structures::item_wood, 40u }, 450.0f },
		{ "Doorway", structures::item_building_plan, { structures::item_wood, 35u }, 400.0f },
		{ "Window", structures::item_building_plan, { structures::item_wood, 35u }, 400.0f },
		{ "Floor", structures::item_building_plan, { structures::item_wood, 25u }, 350.0f },
		{ "Stairs", structures::item_building_plan, { structures::item_wood, 40u }, 350.0f },
		{ "Roof", structures::item_building_plan, { structures::item_wood, 30u }, 350.0f },
		{ "Wooden door", structures::item_wooden_door, {}, 300.0f },
		{ "Campfire", structures::item_campfire, {}, 150.0f },
		{ "Sleeping bag", structures::item_sleeping_bag, {}, 80.0f },
		{ "Storage box", structures::item_storage_box, {}, 200.0f },
		{ "Furnace", structures::item_furnace, {}, 500.0f },
		{ "Well", structures::item_well, {}, 900.0f },
		{ "Workbench I", structures::item_workbench_1, {}, 400.0f },
		{ "Workbench II", structures::item_workbench_2, {}, 700.0f },
		{ "Workbench III", structures::item_workbench_3, {}, 1000.0f },
		{ "Research table", structures::item_research_table, {}, 350.0f },
		{ "Tool cupboard", structures::item_cupboard, {}, 500.0f }
	};
	constexpr auto deployable_kit = "deployables";
	constexpr auto structure_kit = "structures";
	constexpr auto roof_rise = 1.2f;
	constexpr const char* deployable_parts[structures::piece_count] = { nullptr, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr, "campfire", "sleeping_bag", "storage_box", "furnace", "well", "workbench_1", "workbench_2", "workbench_3", "research_table", nullptr };
	constexpr auto cupboard_range = 25.0f;
	constexpr auto building_tier_count = 4u;
	constexpr structures::tier_s building_tiers[building_tier_count] =
	{
		{ "Twig", structures::item_wood, 0u, 0.05f, 1.0f, 1.0f, structures::surface_wood, structures::sound_hit_wood },
		{ "Wood", structures::item_wood, 150u, 1.0f, 1.0f, 1.0f, structures::surface_wood, structures::sound_hit_wood },
		{ "Stone", structures::item_stone, 300u, 2.5f, 0.2f, 0.35f, structures::surface_rock, structures::sound_hit_rock },
		{ "Metal", structures::item_metal_fragments, 200u, 4.0f, 0.08f, 0.15f, structures::surface_metal, structures::sound_hit_metal }
	};
	constexpr std::float_t building_decay_hours[building_tier_count] = { 1.0f, 3.0f, 5.0f, 8.0f };
	constexpr const char* structure_parts[building_tier_count][structures::piece_door] =
	{
		{ "twig_foundation", "twig_wall", "twig_doorway", "twig_window", "twig_floor", "twig_stairs", "twig_roof" },
		{ "wood_foundation", "wood_wall", "wood_doorway", "wood_window", "wood_floor", "wood_stairs", "wood_roof" },
		{ "stone_foundation", "stone_wall", "stone_doorway", "stone_window", "stone_floor", "stone_stairs", "stone_roof" },
		{ "metal_foundation", "metal_wall", "metal_doorway", "metal_window", "metal_floor", "metal_stairs", "metal_roof" }
	};
	constexpr const char* weather_names[4] = { "clear", "overcast", "rainy", "stormy" };
	constexpr std::uint32_t impact_sounds[structures::surface_count] = { structures::sound_hit_rock, structures::sound_hit_metal, structures::sound_hit_metal, structures::sound_hit_wood, structures::sound_hit_metal, structures::sound_hit_soft, structures::sound_hit_soft, structures::sound_hit_flesh, structures::sound_splash, structures::sound_hit_soft, structures::sound_hit_soft, structures::sound_hit_rock, structures::sound_hit_soft };
	constexpr bool ricochet_surfaces[structures::surface_count] = { true, true, true, false, false, false, false, false, false, false, false, true, false };
	constexpr structures::mark_definition_s mark_definitions[structures::mark_count] =
	{
		{ 0u, 4u, 0.08f, 0.25f, 0.05f, 0.0f, 0.0f, 70.0f, 0.0f, 0.0f, false },
		{ 4u, 4u, 0.05f, 0.2f, 0.04f, 0.0f, 0.0f, 60.0f, 0.0f, 0.0f, false },
		{ 8u, 4u, 0.06f, 0.2f, 0.05f, 0.0f, 0.0f, 60.0f, 0.0f, 0.0f, false },
		{ 12u, 2u, 0.11f, 0.25f, 0.1f, 900.0f, 90.0f, 45.0f, 0.0f, 0.0f, false },
		{ 14u, 2u, 0.13f, 0.25f, 0.1f, 600.0f, 90.0f, 45.0f, 0.0f, 0.0f, false },
		{ 32u, 2u, 0.12f, 0.2f, 0.04f, 0.0f, 0.0f, 50.0f, 0.0f, 0.0f, false },
		{ 34u, 2u, 0.04f, 0.2f, 0.04f, 0.0f, 0.0f, 25.0f, 0.0f, 0.0f, false },
		{ 16u, 2u, 0.18f, 0.0f, 0.1f, 600.0f, 150.0f, 40.0f, 0.0f, 0.0f, false },
		{ 18u, 2u, 0.18f, 0.0f, 0.1f, 420.0f, 150.0f, 40.0f, 0.0f, 0.0f, false },
		{ 20u, 2u, 0.18f, 0.0f, 0.06f, 80.0f, 70.0f, 30.0f, 0.0f, 0.0f, true },
		{ 24u, 4u, 0.25f, 0.3f, 0.1f, 1800.0f, 300.0f, 55.0f, 240.0f, 0.0f, true },
		{ 28u, 2u, 0.1f, 0.3f, 0.08f, 1200.0f, 300.0f, 35.0f, 180.0f, 0.0f, true },
		{ 30u, 2u, 0.5f, 0.2f, 0.12f, 1800.0f, 300.0f, 60.0f, 420.0f, 25.0f, true },
		{ 36u, 2u, 0.4f, 0.3f, 0.15f, 0.0f, 0.0f, 80.0f, 0.0f, 0.0f, false },
		{ 38u, 2u, 0.12f, 0.15f, 0.05f, 0.0f, 0.0f, 40.0f, 0.0f, 0.0f, false }
	};
	constexpr std::uint32_t surface_marks[structures::surface_count] = { structures::mark_stone, structures::mark_metal, structures::mark_metal, structures::mark_wood, structures::mark_glass, structures::mark_fabric, structures::mark_earth, structures::mark_count, structures::mark_count, structures::mark_earth, structures::mark_sand, structures::mark_stone, structures::mark_earth };
	constexpr bool surface_hard[structures::surface_count] = { true, true, true, true, true, false, false, false, false, false, false, true, false };
	constexpr std::uint32_t layer_surfaces[terrain_layer_count] = { structures::surface_grass, structures::surface_grass, structures::surface_dirt, structures::surface_dirt, structures::surface_rock, structures::surface_rock, structures::surface_sand, structures::surface_gravel, structures::surface_dirt, structures::surface_grass, structures::surface_grass, structures::surface_dirt, structures::surface_sand, structures::surface_gravel, structures::surface_grass, structures::surface_dirt };
	constexpr std::uint32_t layer_prints[terrain_layer_count] = { structures::mark_count, structures::mark_count, structures::mark_count, structures::mark_print_mud, structures::mark_count, structures::mark_count, structures::mark_print_sand, structures::mark_count, structures::mark_count, structures::mark_count, structures::mark_count, structures::mark_print_mud, structures::mark_print_sand, structures::mark_count, structures::mark_count, structures::mark_print_mud };
	constexpr structures::vec3_s mark_blood_dried{ 0.42f, 0.3f, 0.3f };
	constexpr const char* reject_texts[structures::reject_count] = { "That server is full", "That server runs a different version", "That server is not accepting players", "You are banned from that server", "That server only lets in people on its whitelist", "Wrong server password", "Someone with your name is already playing there", "That name belongs to someone else on that server" };
	constexpr auto item_icon_size = 128u;
	constexpr auto item_icon_columns = 16u;
	constexpr auto item_icon_atlas = "item_icons";
	constexpr auto item_icon_table = "item_icon_table";
	constexpr auto admin_file_name = "zero_point_admin.cfg";
	constexpr auto identity_file_name = "identity.key";
	constexpr auto weather_forced_duration = 86400.0f;
	constexpr structures::weather_phase_s weather_phases[4] = { { 0.08f, 0.0f, 0.0f, 0.5f, 480.0f, 1320.0f }, { 0.62f, 0.0f, 0.0f, 0.25f, 360.0f, 960.0f }, { 0.88f, 0.65f, 0.0f, 0.15f, 300.0f, 840.0f }, { 1.0f, 1.0f, 1.0f, 0.1f, 240.0f, 600.0f } };
	constexpr auto building_decay_interval = 60.0f;
	constexpr auto hammer_repair = 60.0f;
	constexpr auto hammer_repair_wood = 10u;
	constexpr const char* tier_marks[4] = { "", "I", "II", "III" };

	constexpr const char* sound_names[structures::sound_count] = { "step_grass", "step_concrete", "step_wood", "step_soft", "step_gravel", "hit_wood", "hit_rock", "hit_metal", "hit_flesh", "hit_soft", "chop", "swing", "pickup", "container", "craft", "equip", "ui_click", "ui_open", "ui_close", "ui_error", "zombie_groan", "zombie_snarl", "ghost_moan", "player_hurt", "heartbeat", "fire", "amb_forest", "amb_crickets", "amb_drone", "amb_wind", "amb_ocean", "shot_pistol", "shot_rifle", "reload_pistol", "reload_rifle", "bolt", "shot_assault", "dry_fire", "jam", "splash", "wade", "swim", "underwater", "shot_pistol_far", "shot_rifle_far", "shot_assault_far", "amb_rain", "thunder", "tree_creak", "tree_fall", "bullet_crack", "bullet_whiz", "ricochet", "train_engine", "train_roll", "train_clack", "train_horn", "train_brake", "train_hiss", "gun_pistol_close", "gun_pistol_mech", "gun_pistol_far", "gun_pistol_tail_plain", "gun_pistol_tail_forest", "gun_pistol_tail_mountains", "gun_pistol_tail_city", "gun_pistol_tail_room", "gun_bolt_close", "gun_bolt_mech", "gun_bolt_far", "gun_bolt_tail_plain", "gun_bolt_tail_forest", "gun_bolt_tail_mountains", "gun_bolt_tail_city", "gun_bolt_tail_room", "gun_auto_close", "gun_auto_mech", "gun_auto_far", "gun_auto_tail_plain", "gun_auto_tail_forest", "gun_auto_tail_mountains", "gun_auto_tail_city", "gun_auto_tail_room", "casing_hard", "casing_wood", "casing_soft", "tinnitus", "gun_pistol_self", "gun_bolt_self", "gun_auto_self", "vehicle_engine", "vehicle_rotor" };

	constexpr std::uint32_t drone_sounds[structures::drone_count] = { structures::sound_train_engine, structures::sound_train_roll, structures::sound_count, structures::sound_count, structures::sound_vehicle_engine, structures::sound_vehicle_rotor };

	constexpr XAUDIO2FX_REVERB_I3DL2_PARAMETERS acoustic_presets[structures::acoustic_count] = { { 100.0f, -1000, -2600, 0.0f, 1.8f, 0.35f, -3000, 0.12f, -2400, 0.1f, 100.0f, 100.0f, 5000.0f }, XAUDIO2FX_I3DL2_PRESET_FOREST, XAUDIO2FX_I3DL2_PRESET_MOUNTAINS, XAUDIO2FX_I3DL2_PRESET_CITY, XAUDIO2FX_I3DL2_PRESET_ROOM, XAUDIO2FX_I3DL2_PRESET_UNDERWATER };

	constexpr structures::weapon_definition_s weapon_definitions[structures::weapon_count] =
	{
		{},
		{ structures::item_pistol, structures::item_pistol_ammo, 2u, 0.3f, 2.6f, 0.045f, 0.012f, 0.07f, 120.0f, 0.88f, 80.0f, structures::sound_shot_pistol, structures::sound_reload_pistol, 0.0f, false, 0.02f, 0.03f, 0.0f, 0.12f, 0.0f, 0.45f, 0.9f, structures::sound_shot_pistol_far, 0.75f },
		{ structures::item_rifle, structures::item_rifle_ammo, 5u, 1.2f, 3.4f, 0.04f, 0.002f, 0.12f, 600.0f, 0.8f, 120.0f, structures::sound_shot_rifle, structures::sound_reload_rifle, 0.3f, false, 0.015f, 0.02f, 0.0f, 0.1f, 0.0f, 0.38f, 1.2f, structures::sound_shot_rifle_far, 1.25f },
		{ structures::item_hunting_bow, structures::item_wooden_arrow, 1u, 0.2f, 0.55f, 0.03f, 0.005f, 0.0f, 120.0f, 0.86f, 6.0f, structures::sound_swing, structures::sound_pickup },
		{ structures::item_assault_rifle, structures::item_rifle_ammo, 30u, 0.095f, 2.9f, 0.05f, 0.011f, 0.022f, 350.0f, 0.82f, 110.0f, structures::sound_shot_assault, structures::sound_reload_rifle, 0.0f, true, 0.01f, 0.012f, 0.35f, 0.04f, 0.0035f, 0.95f, 1.3f, structures::sound_shot_assault_far, 1.0f }
	};
	constexpr structures::gun_sound_s gun_sounds[structures::weapon_count] =
	{
		{ structures::sound_count, structures::sound_count, structures::sound_count, structures::sound_count, structures::sound_count, 0.0f, false },
		{ structures::sound_gun_pistol_close, structures::sound_gun_pistol_self, structures::sound_gun_pistol_mech, structures::sound_gun_pistol_far, structures::sound_gun_pistol_tail_plain, 0.07f, false },
		{ structures::sound_gun_bolt_close, structures::sound_gun_bolt_self, structures::sound_gun_bolt_mech, structures::sound_gun_bolt_far, structures::sound_gun_bolt_tail_plain, 0.12f, false },
		{ structures::sound_count, structures::sound_count, structures::sound_count, structures::sound_count, structures::sound_count, 0.0f, false },
		{ structures::sound_gun_auto_close, structures::sound_gun_auto_self, structures::sound_gun_auto_mech, structures::sound_gun_auto_far, structures::sound_gun_auto_tail_plain, 0.08f, true }
	};
	constexpr std::float_t audio_tail_gains[structures::acoustic_count] = { 0.42f, 0.8f, 0.75f, 0.8f, 0.95f, 0.0f };

	constexpr auto fauna_maximum = 220u;
	constexpr auto fauna_think_interval = 0.1f;
	constexpr auto fauna_wake_range = 420.0f;
	constexpr auto fauna_dormant_step = 0.5f;
	constexpr auto fauna_sync_range = 280.0f;
	constexpr auto fauna_snapshot_animals = 40u;
	constexpr auto fauna_snapshot_reserve = 12u;
	constexpr auto fauna_animal_bytes = 13u;
	constexpr auto fauna_lod_distance = 45.0f;
	constexpr auto fauna_draw_distance = 300.0f;
	constexpr auto fauna_carcass_time = 900.0f;
	constexpr auto fauna_respawn_time = 300.0f;
	constexpr auto fauna_respawn_clearance = 200.0f;
	constexpr auto fauna_herd_spread = 8.0f;
	constexpr auto fauna_roam = 90.0f;
	constexpr auto fauna_turn_rate = 2.4f;
	constexpr auto fauna_acceleration = 3.5f;
	constexpr auto fauna_shore = 1.0f;
	constexpr auto fauna_steep = 0.74f;
	constexpr auto fauna_calm_rate = 0.08f;
	constexpr auto fauna_flee_time = 9.0f;
	constexpr auto fauna_charge_reach = 1.8f;
	constexpr auto fauna_charge_damage = 22.0f;
	constexpr auto fauna_carve_reach = 2.4f;
	constexpr auto fauna_carve_strikes = 5u;
	constexpr auto fauna_blend_speed = 4.0f;
	constexpr auto fauna_slope_follow = 0.75f;
	constexpr auto fauna_victim = 0xFFFEu;
	constexpr auto fauna_stale = 2.5;
	constexpr auto fauna_dead_center = 0.32f;
	constexpr auto fauna_fright = 1.3f;
	constexpr auto fauna_head_zone = 0.85f;
	constexpr auto fauna_heart_zone = 0.55f;
	constexpr auto fauna_gut_zone = 0.25f;
	constexpr std::float_t fauna_zone_damage[4] = { 3.0f, 2.4f, 1.0f, 0.8f };
	constexpr std::float_t fauna_zone_bleed[4] = { 0.0f, 0.06f, 0.04f, 0.02f };
	constexpr auto fauna_clot = 0.015f;
	constexpr auto fauna_drip = 1.2f;
	constexpr auto fauna_drip_threshold = 0.4f;
	constexpr auto fauna_hoof_range = 45.0f;
	constexpr auto fauna_hoof_volume = 0.07f;
	constexpr structures::species_s species_table[structures::species_count] =
	{
		{ "Red deer stag", "deer_stag", "deer_stag_lod", { "deer_idle", "deer_idle_look", "deer_graze", "deer_alert", "deer_walk", "deer_trot", "deer_run", "deer_hit", "deer_death", "deer_rest", "deer_attack" }, 180.0f, 0.24f, 0.4f, 0.93f, 1.3f, 3.5f, 11.0f, 70.0f, 170.0f, 0.0f, structures::item_raw_venison, 10u, 4u, 3u, 6u, pi, 0.85f, true },
		{ "Red deer hind", "deer_hind", "deer_hind_lod", { "deer_hind_idle", "deer_hind_idle_look", "deer_hind_graze", "deer_hind_alert", "deer_hind_walk", "deer_hind_trot", "deer_hind_run", "deer_hind_hit", "deer_hind_death", "deer_hind_rest", "deer_hind_attack" }, 120.0f, 0.21f, 0.35f, 0.81f, 1.216f, 3.272f, 10.285f, 75.0f, 180.0f, 0.0f, structures::item_raw_venison, 7u, 3u, 2u, 4u, pi, 0.95f, true },
		{ "Wild boar", "boar", "boar_lod", { "boar_idle", "boar_idle_look", "boar_root", "boar_alert", "boar_walk", "boar_trot", "boar_run", "boar_hit", "boar_death", "boar_rest", "boar_attack" }, 150.0f, 0.22f, 0.45f, 0.55f, 1.2f, 3.2f, 9.0f, 40.0f, 120.0f, 0.6f, structures::item_raw_pork, 8u, 2u, 6u, 4u, pi, 1.05f, true },
		{ "Horse", "horse", "horse_lod", { "horse_idle", "horse_idle_look", "horse_graze", "horse_alert", "horse_walk", "horse_trot", "horse_gallop", "horse_hit", "horse_death", "horse_idle", "horse_rear" }, 300.0f, 0.36f, 0.75f, 1.25f, 1.7f, 3.8f, 13.0f, 60.0f, 150.0f, 0.0f, structures::item_raw_horse, 16u, 6u, 4u, 8u, pi, 0.7f, true }
	};
	constexpr auto wildlife_maximum = 640u;
	constexpr auto wildlife_bird_range = 420.0f;
	constexpr auto wildlife_fish_range = 70.0f;
	constexpr auto wildlife_active_margin = 180.0f;
	constexpr auto wildlife_startle_time = 9.0f;
	constexpr auto wildlife_startle_range = 260.0f;
	constexpr auto wildlife_startle_lift = 22.0f;
	constexpr auto wildlife_fish_scare = 5.0f;
	constexpr auto wildlife_ground_clearance = 9.0f;
	constexpr auto wildlife_surface_clearance = 0.5f;
	constexpr auto wildlife_bed_clearance = 0.4f;
	constexpr structures::wildlife_kind_s wildlife_kinds[structures::wildlife_kind_count] =
	{
		{ "bird_gull", structures::creature_flap, 0.05f, 0.5f, 2.4f, 8.5f, 22.0f, 18.0f, 8.0f, 4u, 9u, 10u, 0.6f, (1u << structures::biome_beach) | (1u << structures::biome_shore) | (1u << structures::biome_dunes), 90.0f, 0.0f, 0.0f },
		{ "bird_crow", structures::creature_flap, 0.05f, 0.6f, 3.6f, 11.0f, 14.0f, 26.0f, 6.0f, 5u, 12u, 10u, 0.25f, (1u << structures::biome_farmland) | (1u << structures::biome_meadow) | (1u << structures::biome_woodland) | (1u << structures::biome_heath), 140.0f, 0.0f, 0.0f },
		{ "fish_mackerel", structures::creature_swim, 0.354f, 0.03f, 3.2f, 1.1f, 3.5f, 2.5f, 1.0f, 14u, 26u, 12u, 0.0f, 1u << structures::biome_sea, 14.0f, 3.5f, 14.0f },
		{ "fish_bass", structures::creature_swim, 0.603f, 0.045f, 1.6f, 0.7f, 2.5f, 4.5f, 0.8f, 3u, 6u, 10u, 0.0f, 1u << structures::biome_sea, 10.0f, 5.0f, 16.0f }
	};
	constexpr structures::herd_kind_s herd_kinds[] =
	{
		{ structures::species_stag, structures::species_hind, 3u, 7u, 16u, (1u << structures::biome_woodland) | (1u << structures::biome_pinewood) | (1u << structures::biome_heath) | (1u << structures::biome_meadow) | (1u << structures::biome_moor) },
		{ structures::species_boar, structures::species_boar, 2u, 5u, 9u, (1u << structures::biome_woodland) | (1u << structures::biome_pinewood) | (1u << structures::biome_marsh) },
		{ structures::species_horse, structures::species_horse, 3u, 7u, 6u, (1u << structures::biome_meadow) | (1u << structures::biome_farmland) | (1u << structures::biome_heath) | (1u << structures::biome_moor) | (1u << structures::biome_dunes) }
	};
	constexpr std::uint32_t ambience_sounds[structures::ambience_count] = { structures::sound_amb_forest, structures::sound_amb_crickets, structures::sound_amb_drone, structures::sound_amb_wind, structures::sound_amb_ocean };

	constexpr structures::particle_kind_s particle_kinds[structures::particle_kind_count] =
	{
		{ 0.28f, 0.5f, 0.018f, 0.032f, 0.5f, -0.25f, 1.4f, 0.05f, { 1.0f, 0.95f, 0.9f, 1.0f } },
		{ 0.6f, 1.4f, 0.004f, 0.008f, -0.5f, -0.6f, 0.8f, 0.02f, { 6.0f, 2.6f, 0.7f, 1.0f } },
		{ 2.0f, 3.6f, 0.08f, 0.16f, 2.2f, -0.35f, 0.6f, 0.4f, { 0.16f, 0.15f, 0.14f, 0.45f } },
		{ 0.6f, 1.2f, 0.08f, 0.16f, 2.4f, 0.4f, 3.5f, 0.3f, { 0.55f, 0.52f, 0.48f, 0.5f } },
		{ 0.6f, 1.1f, 0.008f, 0.016f, 0.0f, 9.8f, 0.5f, 0.02f, { 0.26f, 0.17f, 0.1f, 1.0f } },
		{ 0.35f, 0.7f, 0.05f, 0.1f, 1.6f, 4.0f, 3.0f, 0.1f, { 0.3f, 0.02f, 0.02f, 0.85f } },
		{ 0.25f, 0.5f, 0.005f, 0.01f, -0.5f, 9.8f, 0.4f, 0.02f, { 9.0f, 5.5f, 2.2f, 1.0f } },
		{ 0.45f, 0.8f, 0.07f, 0.13f, 0.3f, -0.4f, 1.3f, 0.12f, { 1.0f, 0.95f, 0.9f, 1.0f } }
	};

	constexpr structures::vec3_s atmosphere_rayleigh{ 5.802e-6f, 13.558e-6f, 33.1e-6f };
	constexpr structures::vec3_s atmosphere_ozone{ 0.65e-6f, 1.881e-6f, 0.085e-6f };
	constexpr structures::vec3_s moon_tint{ 0.62f, 0.72f, 1.0f };
	constexpr auto atmosphere_mie_scatter = 3.996e-6f;
	constexpr auto atmosphere_mie_absorb = 0.44e-6f;
	constexpr auto atmosphere_rayleigh_height = 8000.0f;
	constexpr auto atmosphere_mie_height = 1200.0f;

	constexpr structures::viewmodel_key_s weapon_holds[structures::weapon_count][2] =
	{
		{ {}, {} },
		{ { 0.0f, { 0.1f, -0.112f, 0.34f }, { 0.0f, -0.05f, 0.06f } }, { 0.0f, { 0.0f, -0.077f, 0.3f }, { 0.0f, 0.0f, 0.0f } } },
		{ { 0.0f, { 0.14f, -0.105f, 0.5f }, { 0.0f, -0.05f, 0.05f } }, { 0.0f, { 0.0f, -0.0785f, 0.31f }, { 0.0f, 0.0f, 0.0f } } },
		{ { 0.0f, { -0.17f, -0.15f, 0.54f }, { 0.04f, 0.1f, -0.32f } }, { 0.0f, { -0.01f, -0.095f, 0.55f }, { 0.0f, 0.0f, -0.22f } } },
		{ { 0.0f, { 0.12f, -0.1f, 0.47f }, { 0.0f, -0.05f, 0.05f } }, { 0.0f, { 0.0f, -0.072f, 0.255f }, { 0.0f, 0.0f, 0.0f } } }
	};

	constexpr structures::gun_model_s gun_models[structures::weapon_count] =
	{
		{},
		{ "pipe_pistol", { "pipe_pistol_frame", nullptr, nullptr, nullptr, nullptr, nullptr }, { "pipe_pistol_barrels", nullptr }, { -0.051f, -0.012f, 0.0f }, { 0.155f, 0.058f, 0.0f }, {}, { 0.051f, 0.0168f, 0.0f }, {}, { 0.0f, 0.0f, 1.0f }, {}, {}, 0.23f, 0.0f, -0.55f, structures::action_break },
		{ "scrap_rifle", { "scrap_rifle_body", nullptr, nullptr, nullptr, nullptr, nullptr }, { "scrap_rifle_bolt", nullptr }, { -0.3f, -0.002f, 0.0f }, { 0.576f, 0.036f, 0.0f }, { 0.012f, 0.026f, 0.0f }, { 0.0f, 0.036f, 0.0f }, { -0.2402f, 0.0183f, -0.0392f }, { 1.0f, 0.0f, 0.0f }, { 0.6f, 0.1f, -0.8f }, { 0.1f, 1.0f, 0.15f }, 0.7f, 0.075f, 1.2f, structures::action_bolt },
		{ "hunting_bow", { "hunting_bow_stave", nullptr, nullptr, nullptr, nullptr, nullptr }, { nullptr, nullptr }, {}, { 0.0f, 0.07f, 0.02f }, {}, { -0.129f, 0.68f, 0.0f }, { -0.129f, 0.07f, 0.0f }, {}, { 0.25f, 0.0f, -0.97f }, { 1.0f, 0.0f, 0.0f }, 0.0f, 0.3f, 0.0f, structures::action_draw },
		{ "scrap_ar", { "scrap_ar_body", nullptr, nullptr, nullptr, nullptr, nullptr }, { "scrap_ar_bolt", nullptr }, { -0.1106f, -0.0435f, 0.0f }, { 0.445f, 0.036f, 0.0f }, { 0.13f, 0.046f, 0.0f }, { 0.0f, 0.036f, 0.0f }, { -0.1f, 0.04f, 0.028f }, { 1.0f, 0.0f, 0.0f }, { 0.6f, 0.1f, -0.8f }, { 0.1f, 1.0f, 0.15f }, 0.31f, 0.045f, 0.0f, structures::action_slide, "scrap_ar_mag", { -0.0077f, -0.06f, 0.0f } }
	};
	constexpr structures::hold_pose_s hold_poses[structures::hold_count] =
	{
		{},
		{ { -0.12f, 1.3f, -0.26f }, { 0.0f, -0.03f, 0.07f }, { 0.0f, -0.03f, 0.06f }, -0.2f, 0.5f, false },
		{ { -0.06f, 1.22f, -0.42f }, { 0.0f, -0.03f, 0.06f }, { 0.06f, -0.06f, 0.06f }, -0.4f, 0.0f, false },
		{ { -0.25f, 0.95f, -0.12f }, { 0.0f, 0.06f, 0.03f }, {}, 0.5f, 0.0f, false },
		{ { 0.25f, 0.97f, -0.14f }, { 0.0f, 0.06f, 0.03f }, {}, -0.9f, 0.0f, true }
	};
	constexpr structures::vec3_s hold_right_pole{ -1.0f, -0.5f, 0.35f };
	constexpr structures::vec3_s hold_left_pole{ 1.0f, -0.5f, 0.35f };
	constexpr const char* ragdoll_bones[structures::ragdoll_point_count] = { "Bip01 Pelvis", "Bip01 Neck", "Bip01 Head", "Bip01 L UpperArm", "Bip01 L Forearm", "Bip01 L Hand", "Bip01 R UpperArm", "Bip01 R Forearm", "Bip01 R Hand", "Bip01 L Thigh", "Bip01 L Calf", "Bip01 L Foot", "Bip01 R Thigh", "Bip01 R Calf", "Bip01 R Foot" };
	constexpr std::uint32_t ragdoll_aims[structures::ragdoll_point_count] = { structures::ragdoll_point_count, structures::ragdoll_point_count, structures::ragdoll_head, structures::ragdoll_left_elbow, structures::ragdoll_left_wrist, structures::ragdoll_point_count, structures::ragdoll_right_elbow, structures::ragdoll_right_wrist, structures::ragdoll_point_count, structures::ragdoll_left_knee, structures::ragdoll_left_ankle, structures::ragdoll_point_count, structures::ragdoll_right_knee, structures::ragdoll_right_ankle, structures::ragdoll_point_count };
	constexpr std::float_t ragdoll_weights[structures::ragdoll_point_count] = { 0.55f, 0.65f, 1.1f, 0.8f, 1.0f, 1.3f, 0.8f, 1.0f, 1.3f, 0.7f, 0.9f, 1.2f, 0.7f, 0.9f, 1.2f };
	constexpr std::float_t ragdoll_push[structures::ragdoll_point_count] = { 0.45f, 1.0f, 1.1f, 0.9f, 0.8f, 0.7f, 0.9f, 0.8f, 0.7f, 0.3f, 0.12f, 0.04f, 0.3f, 0.12f, 0.04f };
	constexpr structures::ragdoll_link_s ragdoll_links[26] =
	{
		{ structures::ragdoll_pelvis, structures::ragdoll_chest },
		{ structures::ragdoll_pelvis, structures::ragdoll_left_shoulder },
		{ structures::ragdoll_pelvis, structures::ragdoll_right_shoulder },
		{ structures::ragdoll_pelvis, structures::ragdoll_left_hip },
		{ structures::ragdoll_pelvis, structures::ragdoll_right_hip },
		{ structures::ragdoll_chest, structures::ragdoll_left_shoulder },
		{ structures::ragdoll_chest, structures::ragdoll_right_shoulder },
		{ structures::ragdoll_chest, structures::ragdoll_left_hip },
		{ structures::ragdoll_chest, structures::ragdoll_right_hip },
		{ structures::ragdoll_left_shoulder, structures::ragdoll_right_shoulder },
		{ structures::ragdoll_left_shoulder, structures::ragdoll_left_hip },
		{ structures::ragdoll_left_shoulder, structures::ragdoll_right_hip },
		{ structures::ragdoll_right_shoulder, structures::ragdoll_left_hip },
		{ structures::ragdoll_right_shoulder, structures::ragdoll_right_hip },
		{ structures::ragdoll_left_hip, structures::ragdoll_right_hip },
		{ structures::ragdoll_chest, structures::ragdoll_head },
		{ structures::ragdoll_left_shoulder, structures::ragdoll_head },
		{ structures::ragdoll_right_shoulder, structures::ragdoll_head },
		{ structures::ragdoll_left_shoulder, structures::ragdoll_left_elbow },
		{ structures::ragdoll_left_elbow, structures::ragdoll_left_wrist },
		{ structures::ragdoll_right_shoulder, structures::ragdoll_right_elbow },
		{ structures::ragdoll_right_elbow, structures::ragdoll_right_wrist },
		{ structures::ragdoll_left_hip, structures::ragdoll_left_knee },
		{ structures::ragdoll_left_knee, structures::ragdoll_left_ankle },
		{ structures::ragdoll_right_hip, structures::ragdoll_right_knee },
		{ structures::ragdoll_right_knee, structures::ragdoll_right_ankle }
	};
	constexpr structures::ragdoll_joint_s ragdoll_joints[4] =
	{
		{ structures::ragdoll_left_shoulder, structures::ragdoll_left_elbow, structures::ragdoll_left_wrist, -1.0f, 0.42f },
		{ structures::ragdoll_right_shoulder, structures::ragdoll_right_elbow, structures::ragdoll_right_wrist, -1.0f, 0.42f },
		{ structures::ragdoll_left_hip, structures::ragdoll_left_knee, structures::ragdoll_left_ankle, 1.0f, 0.55f },
		{ structures::ragdoll_right_hip, structures::ragdoll_right_knee, structures::ragdoll_right_ankle, 1.0f, 0.55f }
	};
	constexpr auto ragdoll_step = 1.0f / 120.0f;
	constexpr auto ragdoll_substeps = 6u;
	constexpr auto ragdoll_iterations = 8u;
	constexpr auto ragdoll_damping = 0.996f;
	constexpr auto ragdoll_gravity = 9.81f;
	constexpr auto ragdoll_radius = 0.07f;
	constexpr auto ragdoll_friction = 0.6f;
	constexpr auto ragdoll_head_reach = 0.11f;
	constexpr auto ragdoll_rest_speed = 0.06f;
	constexpr auto ragdoll_rest_time = 0.8f;
	constexpr auto ragdoll_lifetime = 9.0f;
	constexpr auto ragdoll_shove = 1.4f;
	constexpr auto ragdoll_shot_shove = 2.6f;
	constexpr auto ragdoll_top_speed = 9.0f;
	constexpr auto ragdoll_test_frame = 150u;

	constexpr structures::viewmodel_key_s reload_poses[structures::weapon_count] =
	{
		{},
		{ 0.0f, { -0.02f, -0.08f, 0.0f }, { 0.45f, 0.0f, 0.55f } },
		{ 0.0f, { -0.02f, -0.08f, 0.0f }, { 0.45f, 0.0f, 0.55f } },
		{ 0.0f, { -0.02f, -0.08f, 0.0f }, { 0.45f, 0.0f, 0.55f } },
		{ 0.0f, { -0.07f, 0.035f, -0.02f }, { 0.04f, -0.15f, -0.42f } }
	};

	constexpr structures::vec3_s viewmodel_bow_anchor{ 0.012f, -0.11f, 0.08f };
	constexpr auto bow_draw_time = 0.85f;
	constexpr auto arrow_speed_minimum = 16.0f;
	constexpr auto arrow_speed_maximum = 58.0f;
	constexpr auto arrow_gravity = 9.81f;
	constexpr auto arrow_length = 0.72f;
	constexpr auto arrow_life = 90.0f;
	constexpr auto maximum_arrows = 64u;

	constexpr const char* landmark_names[structures::landmark_count] = { "Saint Aubin", "Signal Post", "Breaker's Yard", "Gorey Harbour", "Saint Ouen", "Portelet", "Noirmont Battery", "The Institute", "Le Pulec Quarry", "Saint Aubin Halt", "Rozel Farm", "Les Landes Farm", "Trinity Farm" };
	constexpr bool landmark_minor[structures::landmark_count] = { false, false, false, false, false, false, false, false, true, true, true, true, true };
	constexpr bool landmark_below[structures::landmark_count] = { false, false, false, false, false, false, false, false, false, true, false, false, false };
	constexpr structures::world_site_s world_sites[] =
	{
		{ { 460.0f, -420.0f }, 150.0f, 240.0f, 0.0f, structures::landmark_town },
		{ { 860.0f, -300.0f }, 60.0f, 110.0f, 0.0f, structures::landmark_halt },
		{ { 1180.0f, -330.0f }, 90.0f, 150.0f, 0.35f, structures::landmark_yard },
		{ { 1520.0f, 300.0f }, 90.0f, 150.0f, 0.0f, structures::landmark_harbour },
		{ { 300.0f, 1450.0f }, 110.0f, 180.0f, 0.0f, structures::landmark_ouen },
		{ { 1284.0f, 1232.0f }, 70.0f, 120.0f, 0.0f, structures::landmark_rozel },
		{ { 172.0f, -844.0f }, 70.0f, 120.0f, 0.0f, structures::landmark_landes },
		{ { -92.0f, -1300.0f }, 70.0f, 120.0f, 0.0f, structures::landmark_trinity },
		{ { -1100.0f, -1480.0f }, 80.0f, 140.0f, 0.0f, structures::landmark_portelet },
		{ { -1610.0f, 330.0f }, 70.0f, 120.0f, 0.0f, structures::landmark_battery },
		{ { 740.0f, 580.0f }, 90.0f, 150.0f, 0.0f, structures::landmark_institute },
		{ { 200.0f, 944.0f }, 35.0f, 70.0f, 0.0f, structures::landmark_outpost },
		{ { -900.0f, -600.0f }, 80.0f, 140.0f, 0.0f, structures::landmark_quarry }
	};
	constexpr structures::vec2_s railway_points[] = { { 1480.0f, 360.0f }, { 1560.0f, 700.0f }, { 1500.0f, 1000.0f }, { 1380.0f, 1300.0f }, { 1100.0f, 1520.0f }, { 700.0f, 1620.0f }, { 300.0f, 1520.0f }, { -60.0f, 1500.0f }, { -330.0f, 1330.0f }, { -560.0f, 1150.0f }, { -850.0f, 1030.0f }, { -1150.0f, 930.0f }, { -1380.0f, 740.0f }, { -1460.0f, 480.0f }, { -1520.0f, 150.0f }, { -1680.0f, -300.0f }, { -1620.0f, -700.0f }, { -1500.0f, -1050.0f }, { -1250.0f, -1350.0f }, { -1000.0f, -1480.0f }, { -640.0f, -1560.0f }, { -240.0f, -1470.0f }, { 150.0f, -1300.0f }, { 500.0f, -1000.0f }, { 800.0f, -650.0f }, { 880.0f, -300.0f }, { 1100.0f, -100.0f }, { 1350.0f, 150.0f } };
	constexpr structures::vec2_s south_road_points[] = { { 1180.0f, -330.0f }, { 1004.0f, -305.0f }, { 860.0f, -330.0f }, { 800.0f, -350.0f }, { 722.0f, -361.0f }, { 600.0f, -420.0f }, { 528.0f, -485.0f }, { 460.0f, -560.0f }, { 379.0f, -630.0f }, { 300.0f, -700.0f }, { 257.0f, -766.0f }, { 172.0f, -844.0f }, { 118.0f, -957.0f }, { 60.0f, -1029.0f }, { -26.0f, -1194.0f }, { -92.0f, -1300.0f }, { -256.0f, -1334.0f }, { -337.0f, -1459.0f }, { -418.0f, -1478.0f }, { -586.0f, -1514.0f }, { -649.0f, -1516.0f }, { -832.0f, -1500.0f }, { -947.0f, -1438.0f }, { -1022.0f, -1413.0f }, { -1100.0f, -1480.0f } };
	constexpr structures::vec2_s east_road_points[] = { { 800.0f, -350.0f }, { 849.0f, -277.0f }, { 932.0f, -146.0f }, { 975.0f, -91.0f }, { 1084.0f, -8.0f }, { 1120.0f, 19.0f }, { 1177.0f, 78.0f }, { 1250.0f, 158.0f }, { 1400.0f, 330.0f }, { 1419.0f, 416.0f }, { 1464.0f, 560.0f }, { 1485.0f, 742.0f }, { 1475.0f, 835.0f }, { 1422.0f, 953.0f }, { 1338.0f, 1174.0f }, { 1284.0f, 1232.0f }, { 1184.0f, 1326.0f }, { 1090.0f, 1379.0f }, { 950.0f, 1413.0f }, { 844.0f, 1410.0f }, { 741.0f, 1491.0f }, { 594.0f, 1479.0f }, { 533.0f, 1494.0f }, { 421.0f, 1479.0f }, { 300.0f, 1450.0f } };
	constexpr structures::vec2_s west_road_points[] = { { 300.0f, 1450.0f }, { 126.0f, 1418.0f }, { 35.0f, 1461.0f }, { -128.0f, 1430.0f }, { -195.0f, 1366.0f }, { -398.0f, 1200.0f }, { -452.0f, 1161.0f }, { -592.0f, 1080.0f }, { -719.0f, 1016.0f }, { -912.0f, 946.0f }, { -1030.0f, 913.0f }, { -1166.0f, 826.0f }, { -1209.0f, 760.0f }, { -1256.0f, 690.0f }, { -1399.0f, 556.0f }, { -1436.0f, 379.0f }, { -1425.0f, 300.0f }, { -1477.0f, 180.0f }, { -1451.0f, 80.0f }, { -1473.0f, 2.0f }, { -1540.0f, -139.0f }, { -1544.0f, -286.0f }, { -1581.0f, -378.0f }, { -1589.0f, -582.0f }, { -1572.0f, -734.0f }, { -1437.0f, -841.0f }, { -1436.0f, -978.0f }, { -1403.0f, -1073.0f }, { -1350.0f, -1188.0f }, { -1229.0f, -1272.0f }, { -1163.0f, -1321.0f }, { -1072.0f, -1370.0f }, { -1022.0f, -1413.0f } };
	constexpr structures::vec2_s valley_road_points[] = { { 460.0f, -300.0f }, { 500.0f, -52.0f }, { 553.0f, 21.0f }, { 666.0f, 112.0f }, { 770.0f, 176.0f }, { 783.0f, 297.0f }, { 856.0f, 370.0f }, { 857.0f, 506.0f }, { 850.0f, 565.0f }, { 810.0f, 590.0f }, { 740.0f, 580.0f } };
	constexpr structures::vec2_s quarry_road_points[] = { { 300.0f, -700.0f }, { 81.0f, -674.0f }, { -58.0f, -636.0f }, { -142.0f, -653.0f }, { -302.0f, -696.0f }, { -400.0f, -666.0f }, { -480.0f, -646.0f }, { -646.0f, -634.0f }, { -734.0f, -655.0f }, { -900.0f, -600.0f } };
	constexpr structures::vec2_s battery_road_points[] = { { -1425.0f, 300.0f }, { -1520.0f, 318.0f }, { -1610.0f, 330.0f } };
	constexpr structures::vec2_s harbour_road_points[] = { { 1400.0f, 330.0f }, { 1460.0f, 315.0f }, { 1520.0f, 300.0f } };
	constexpr structures::world_route_s world_routes[] =
	{
		{ railway_points, static_cast<std::uint32_t>(std::size(railway_points)), structures::route_rail, 5.2f, 0.025f, 100.0f, 0.65f, true },
		{ south_road_points, static_cast<std::uint32_t>(std::size(south_road_points)), structures::route_road, 6.4f, 0.1f, 20.0f, 0.5f, false },
		{ east_road_points, static_cast<std::uint32_t>(std::size(east_road_points)), structures::route_road, 6.4f, 0.1f, 20.0f, 0.5f, false },
		{ west_road_points, static_cast<std::uint32_t>(std::size(west_road_points)), structures::route_road, 6.4f, 0.1f, 20.0f, 0.5f, false },
		{ valley_road_points, static_cast<std::uint32_t>(std::size(valley_road_points)), structures::route_road, 5.6f, 0.1f, 20.0f, 0.5f, false },
		{ quarry_road_points, static_cast<std::uint32_t>(std::size(quarry_road_points)), structures::route_road, 5.6f, 0.1f, 20.0f, 0.5f, false },
		{ battery_road_points, static_cast<std::uint32_t>(std::size(battery_road_points)), structures::route_road, 5.6f, 0.1f, 20.0f, 0.5f, false },
		{ harbour_road_points, static_cast<std::uint32_t>(std::size(harbour_road_points)), structures::route_road, 6.4f, 0.1f, 20.0f, 0.5f, false }
	};
	constexpr structures::train_vehicle_s train_vehicles[structures::train_vehicle_count] =
	{
		{ "train_locomotive", 8.0f, 2.8f, 3.7f, 2.6f, 1.3f, structures::material_metal_green, 3u, { 1.4f, 0.0f, -1.4f, 0.0f } },
		{ "train_wagon_flat", 7.0f, 3.1f, 1.71f, 2.5f, 1.27f, structures::material_metal_rust, 2u, { 1.55f, -1.55f, 0.0f, 0.0f } },
		{ "train_wagon_open", 7.0f, 3.1f, 2.52f, 2.5f, 1.27f, structures::material_metal_rust, 2u, { 1.55f, -1.55f, 0.0f, 0.0f } },
		{ "train_wagon_box", 7.0f, 3.1f, 3.63f, 2.5f, 1.27f, structures::material_container_red, 2u, { 1.55f, -1.55f, 0.0f, 0.0f } },
		{ "train_coach", 12.0f, 6.0f, 3.64f, 2.6f, 1.27f, structures::material_container_blue, 4u, { 4.0f, 2.0f, -2.0f, -4.0f } }
	};
	constexpr std::uint32_t train_consist[] = { structures::train_vehicle_locomotive, structures::train_vehicle_flat, structures::train_vehicle_open, structures::train_vehicle_box, structures::train_vehicle_coach };
	constexpr std::uint32_t train_stops[] = { structures::landmark_halt, structures::landmark_harbour, structures::landmark_ouen, structures::landmark_battery, structures::landmark_portelet };
	constexpr structures::station_kit_s station_kits[] = { { structures::landmark_ouen, true, false, true }, { structures::landmark_harbour, true, true, false }, { structures::landmark_halt, false, false, false }, { structures::landmark_battery, false, false, false }, { structures::landmark_portelet, false, true, false } };
	constexpr auto vehicle_substep = 1.0f / 120.0f;
	constexpr auto vehicle_gravity = 9.81f;
	constexpr auto vehicle_mover_base = 128u;
	constexpr auto vehicle_owner_base = 64u;
	constexpr auto vehicle_enter_reach = 3.4f;
	constexpr auto vehicle_sleep_speed = 0.06f;
	constexpr auto vehicle_sleep_time = 1.5f;
	constexpr auto vehicle_linear_drag = 0.02f;
	constexpr auto vehicle_air_drag = 0.004f;
	constexpr auto vehicle_mover_stride = 24u;
	constexpr auto vehicle_ride_base = 0x10000u;
	constexpr auto vehicle_engine_reference = 14.0f;
	constexpr auto vehicle_rotor_reference = 40.0f;
	constexpr auto vehicle_angular_drag = 1.2f;
	constexpr auto vehicle_rolling = 0.018f;
	constexpr auto vehicle_restitution = 0.08f;
	constexpr auto vehicle_contact_friction = 0.55f;
	constexpr auto vehicle_grip_response = 0.5f;
	constexpr auto vehicle_steer_rate = 2.4f;
	constexpr auto vehicle_steer_fade = 0.55f;
	constexpr auto vehicle_spool_time = 6.0f;
	constexpr auto vehicle_rotor_turns = 7.0f;
	constexpr auto vehicle_tail_ratio = 4.6f;
	constexpr auto vehicle_climb_rate = 7.0f;
	constexpr auto vehicle_sink_rate = 5.0f;
	constexpr auto vehicle_hold = 2.6f;
	constexpr auto vehicle_crash_speed = 7.0f;
	constexpr auto vehicle_crash_damage = 7.0f;
	constexpr auto vehicle_bullet_scale = 0.35f;
	constexpr auto vehicle_wreck_damage = 45.0f;
	constexpr auto vehicle_bruise_scale = 2.5f;
	constexpr auto vehicle_bang_speed = 3.0f;
	constexpr auto vehicle_effect_range = 170.0f;
	constexpr auto vehicle_smoke_health = 0.35f;
	constexpr auto vehicle_dust_speed = 7.0f;
	constexpr auto vehicle_wash_height = 7.0f;
	constexpr auto vehicle_headlight_radius = 32.0f;
	constexpr auto vehicle_headlight_cosine = 0.8f;
	constexpr auto vehicle_headlight_tilt = 0.09f;
	constexpr structures::vec3_s vehicle_headlight_color = { 2.6f, 2.4f, 2.0f };
	constexpr auto vehicle_sync_range = 420.0f;
	constexpr auto vehicle_snapshot_count = 8u;
	constexpr auto vehicle_bytes = 35u;
	constexpr auto vehicle_detail_distance = 140.0f;
	constexpr auto vehicle_shadow_distance = 160.0f;
	constexpr auto vehicle_respawn_time = 600.0f;
	constexpr auto vehicle_stale_time = 3.0;
	constexpr structures::vehicle_kind_s vehicle_kinds[structures::vehicle_kind_count] =
	{
		{ "veh_rover", "Armoured rover", 1900.0f, { 0.0f, 1.15f, 0.0f }, { 0.98f, 0.72f, 2.25f }, { 0.0f, 0.75f, 0.1f }, 4u, { { -0.84f, 0.44f, 1.42f }, { 0.84f, 0.44f, 1.42f }, { -0.84f, 0.44f, -1.36f }, { 0.84f, 0.44f, -1.36f } }, 0.44f, 0.32f, 30000.0f, 3200.0f, 2900.0f, 5200.0f, 0.62f, 1.15f, 30.0f, 7.0f, 0.0f, 0.0f, 0.0f, {}, {}, 0.0f, 2u, { { -0.42f, 1.55f, 0.25f }, { 0.42f, 1.55f, 0.25f } }, { { -1.8f, 0.1f, 0.2f }, { 1.8f, 0.1f, 0.2f } }, { { -0.6f, 1.0f, 2.3f }, { 0.6f, 1.0f, 2.3f } }, { 0.8f, 2.3f, -0.6f }, 600.0f },
		{ "veh_heli", "Scrap helicopter", 950.0f, { 0.0f, 1.25f, 0.6f }, { 0.85f, 0.85f, 1.9f }, { 0.0f, 1.1f, 0.3f }, 0u, {}, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.65f, 0.42f, 1.3f, { 0.0f, 2.75f, 0.4f }, { 0.25f, 1.9f, -5.1f }, 4.1f, 2u, { { -0.35f, 1.7f, 1.2f }, { 0.35f, 1.7f, 1.2f } }, { { -1.6f, 0.1f, 0.8f }, { 1.6f, 0.1f, 0.8f } }, { { 0.0f, 0.9f, 2.4f }, { 0.0f, 0.9f, 2.4f } }, { 0.0f, 2.2f, -0.6f }, 400.0f }
	};
	constexpr structures::vehicle_spawn_s vehicle_spawns[] =
	{
		{ structures::vehicle_rover, { 506.0f, -421.5f }, half_pi },
		{ structures::vehicle_rover, { 461.8f, -332.0f }, pi },
		{ structures::vehicle_rover, { 1180.0f, -318.0f }, 0.35f },
		{ structures::vehicle_heli, { 413.0f, -450.0f }, 0.0f }
	};
	constexpr auto station_crossing_reach = 3.0f;
	constexpr auto station_crossing_search = 60.0f;
	constexpr auto station_crossing_clear = 16.0f;
	constexpr auto station_yard_ahead = 16.0f;
	constexpr auto station_yard_behind = 62.0f;
	constexpr auto station_yard_half = 12.0f;
	constexpr auto station_yard_blend = 24.0f;
	constexpr auto station_clearing = 15.0f;
	constexpr auto station_clearing_step = 10.0f;
	constexpr auto station_limit = 64u;
	constexpr auto platform_offset = 3.5f;
	constexpr auto platform_module = 12.0f;
	constexpr auto platform_modules = 4u;
	constexpr auto platform_ramp = 2.5f;
	constexpr auto platform_lead = 2.0f;
	constexpr auto station_offset = 8.0f;
	constexpr auto station_floor = 1.7f;
	constexpr auto signal_box_offset = 4.2f;
	constexpr auto signal_box_back = 20.0f;
	constexpr auto water_tower_offset = 3.6f;
	constexpr auto water_tower_back = 10.0f;
	constexpr auto signal_offset = 2.4f;
	constexpr auto signal_back = 110.0f;
	constexpr auto crossing_gate_model = "rail_crossing_gate";
	constexpr auto crossing_post_model = "rail_crossing_post";
	constexpr auto crossing_sign_model = "rail_crossing_sign";
	constexpr auto crossing_gate_clear = 3.3f;
	constexpr auto crossing_gate_margin = 0.45f;
	constexpr auto crossing_pivot_offset = 0.205f;
	constexpr auto crossing_slant_floor = 0.2f;
	constexpr auto crossing_sign_back = 8.0f;
	constexpr auto crossing_sign_margin = 0.9f;
	constexpr auto crossing_post_turn = 0.0f;
	constexpr auto crossing_sign_turn = 0.0f;
	constexpr auto crossing_close_ahead = 260.0f;
	constexpr auto crossing_open_behind = 15.0f;
	constexpr auto crossing_swing = 0.7f;
	constexpr auto crossing_stretch_low = 0.6f;
	constexpr auto crossing_stretch_high = 1.8f;
	constexpr auto crossing_view_distance = 260.0f;
	constexpr auto crossing_detail_distance = 60.0f;
	constexpr auto crossing_shadow_distance = 90.0f;
	constexpr auto crossing_lamp_radius = 8.0f;
	constexpr auto crossing_blink = 1.1f;
	constexpr structures::vec3_s crossing_lamp_color{ 4.0f, 0.25f, 0.12f };
	constexpr auto train_acceleration = 0.5f;
	constexpr auto train_cruise = 13.0f;
	constexpr auto train_dwell = 30.0f;
	constexpr auto train_coupling = 0.4f;
	constexpr auto train_wheel_radius = 0.48f;
	constexpr auto train_wheelset_model = "train_wheelset";
	constexpr auto train_view_distance = 1500.0f;
	constexpr auto train_detail_distance = 170.0f;
	constexpr auto train_shadow_distance = 230.0f;
	constexpr auto train_wheel_distance = 400.0f;
	constexpr auto train_light_distance = 700.0f;
	constexpr auto train_headlight_radius = 80.0f;
	constexpr auto train_headlight_cosine = 0.93f;
	constexpr auto train_headlight_tilt = 0.06f;
	constexpr structures::vec3_s train_headlight_color{ 120.0f, 108.0f, 88.0f };
	constexpr auto train_lamp_radius = 6.0f;
	constexpr structures::vec3_s train_lamp_color{ 1.8f, 1.3f, 0.7f };
	constexpr auto train_tail_radius = 9.0f;
	constexpr auto train_tail_height = 1.1f;
	constexpr structures::vec3_s train_tail_color{ 2.5f, 0.12f, 0.08f };
	constexpr auto train_lights_day = 0.1f;
	constexpr auto train_dusk_start = 0.25f;
	constexpr auto train_dusk_end = -0.05f;
	constexpr auto train_joint_spacing = 12.0f;
	constexpr auto train_clack_range = 45.0f;
	constexpr auto train_engine_reference = 16.0f;
	constexpr auto train_roll_reference = 9.0f;
	constexpr auto train_horn_reference = 70.0f;
	constexpr auto train_brake_reference = 12.0f;
	constexpr auto train_horn_lead = 2.5f;
	constexpr auto train_horn_approach = 24.0f;
	constexpr auto train_horn_crossing = 250.0f;
	constexpr auto train_horn_moving = 1.0f;
	constexpr auto train_brake_speed = 5.5f;
	constexpr auto train_hiss_speed = 0.15f;
	constexpr auto train_carry_limit = 3.0f;
	constexpr auto train_reach = 90.0f;
	constexpr auto train_tumble_scale = 1.35f;
	constexpr auto train_tumble_speed = 9.0f;
	constexpr auto train_strike_safe = 1.5f;
	constexpr auto train_strike_lethal = 7.0f;
	constexpr auto train_strike_reach = 1.1f;
	constexpr auto train_strike_cooldown = 0.5;
	constexpr auto train_ride_margin = 0.5f;
	constexpr auto train_ride_headroom = 2.6f;
	constexpr auto train_velocity_step = 0.05;
	constexpr auto mover_brush_base = 0x01000000;
	constexpr auto rail_head = 0.5f;
	constexpr structures::vec3_s chart_paper{ 0.86f, 0.8f, 0.66f };
	constexpr structures::vec3_s chart_ink{ 0.11f, 0.085f, 0.065f };
	constexpr structures::vec3_s chart_burn{ 0.42f, 0.3f, 0.18f };

	constexpr const char* viewmodel_left_fingers[5][3] = { { "Bip01 L Finger0", "Bip01 L Finger01", "Bip01 L Finger02" }, { "Bip01 L Finger1", "Bip01 L Finger11", "Bip01 L Finger12" }, { "Bip01 L Finger2", "Bip01 L Finger21", "Bip01 L Finger22" }, { "Bip01 L Finger3", "Bip01 L Finger31", "Bip01 L Finger32" }, { "Bip01 L Finger4", "Bip01 L Finger41", "Bip01 L Finger42" } };
	constexpr structures::vec3_s viewmodel_left_pole{ 0.6f, -1.0f, 0.3f };
	constexpr structures::vec3_s viewmodel_bolt_fingers{ 1.0f, 0.0f, 0.0f };
	constexpr structures::vec3_s viewmodel_bolt_palm{ 0.0f, 0.6f, 0.8f };

	constexpr auto viewmodel_character = "survivor";
	constexpr structures::loadout_entry_s test_kit[] = { { inventory_slots + 0u, { structures::item_pistol, 1u, 1.0f, 2u } }, { inventory_slots + 1u, { structures::item_rifle, 1u, 1.0f, 5u } }, { inventory_slots + 2u, { structures::item_assault_rifle, 1u, 1.0f, 30u } }, { inventory_slots + 3u, { structures::item_rock, 1u, 1.0f, 0u } }, { inventory_slots + 4u, { structures::item_building_plan, 1u, 1.0f, 0u } }, { 0u, { structures::item_pistol_ammo, 40u, 1.0f, 0u } }, { 1u, { structures::item_rifle_ammo, 64u, 1.0f, 0u } }, { 2u, { structures::item_rifle_ammo, 64u, 1.0f, 0u } }, { 3u, { structures::item_rifle_ammo, 64u, 1.0f, 0u } } };
	constexpr auto weapon_heat_decay = 0.16f;
	constexpr auto weapon_heat_spread = 1.6f;
	constexpr auto weapon_heat_jam = 4.0f;
	constexpr auto weapon_wear_jam = 3.0f;
	constexpr auto weapon_wear_per_shot = 0.0012f;
	constexpr auto weapon_burst_gap = 0.32f;
	constexpr auto weapon_bloom_shots = 12.0f;
	constexpr auto weapon_stutter_chance = 0.06f;
	constexpr auto weapon_stutter_time = 0.16f;
	constexpr auto weapon_jam_pull = 0.55f;
	constexpr auto weapon_misfire_wear = 2.0f;
	constexpr auto weapon_misfire_delay = 0.35f;
	constexpr auto weapon_hangfire_share = 0.35f;
	constexpr auto weapon_hangfire_minimum = 0.18f;
	constexpr auto weapon_hangfire_spread = 0.45f;
	constexpr auto weapon_smoke_heat = 0.45f;
	constexpr auto weapon_smoke_rate = 10.0f;
	constexpr auto weapon_smoke_rise = 0.3f;
	constexpr structures::vec3_s viewmodel_charge_fingers{ 1.0f, 0.0f, 0.0f };
	constexpr structures::vec3_s viewmodel_charge_palm{ 0.0f, 0.6f, -0.8f };
	constexpr structures::vec3_s viewmodel_magazine_fingers{ 0.0f, -0.4f, -0.9f };
	constexpr structures::vec3_s viewmodel_magazine_palm{ -1.0f, 0.2f, 0.0f };
	constexpr structures::vec3_s viewmodel_magazine_drop{ 0.03f, -0.24f, 0.05f };
	constexpr auto viewmodel_magazine_tilt = 0.45f;
	constexpr auto inspect_key = 'I';
	constexpr auto inspect_spin_rate = 0.5f;
	constexpr auto inspect_mouse_rate = 0.006f;
	constexpr auto inspect_idle_time = 1.2f;
	constexpr auto inspect_framing = 0.95f;
	constexpr auto inspect_zoom_rate = 0.12f;
	constexpr auto inspect_zoom_min = 0.3f;
	constexpr auto inspect_zoom_max = 1.4f;
	constexpr auto inspect_lift = 0.3f;
	constexpr auto inspect_light_radius = 4.0f;
	constexpr structures::vec3_s inspect_light_color{ 2.2f, 2.05f, 1.9f };

	constexpr structures::hand_frame_s guard_frames[2] =
	{
		{ { 0.13f, -0.145f, 0.3f }, { -0.22f, 0.62f, 0.75f }, { -0.8f, -0.45f, -0.25f } },
		{ { -0.145f, -0.125f, 0.37f }, { 0.2f, 0.58f, 0.79f }, { 0.8f, -0.45f, -0.25f } }
	};
	constexpr structures::hand_frame_s swim_frames[3] =
	{
		{ { 0.1f, -0.1f, 0.44f }, { 0.14f, 0.06f, 1.0f }, { 0.25f, -0.97f, 0.0f } },
		{ { 0.3f, -0.14f, 0.34f }, { 0.55f, -0.05f, 0.83f }, { 0.45f, -0.25f, -0.86f } },
		{ { 0.1f, -0.21f, 0.22f }, { -0.35f, 0.3f, 0.88f }, { -0.3f, -0.6f, -0.74f } }
	};
	constexpr std::float_t swim_frame_times[4] = { 0.0f, 0.45f, 0.75f, 1.0f };
	constexpr auto swim_stroke_rate = 0.35f;
	constexpr auto swim_stroke_speed_rate = 0.28f;
	constexpr auto swim_hand_clench = 0.12f;
	constexpr structures::hand_frame_s punch_frames[2] =
	{
		{ { 0.035f, -0.075f, 0.53f }, { -0.08f, 0.1f, 1.0f }, { -0.12f, -1.0f, 0.1f } },
		{ { -0.04f, -0.07f, 0.54f }, { 0.08f, 0.1f, 1.0f }, { 0.12f, -1.0f, 0.1f } }
	};
	constexpr auto viewmodel_wrist_freedom = 0.3f;
	constexpr std::float_t fist_curl[5][3] = { { 0.0f, 0.0f, 0.0f }, { 1.4f, 1.5f, 0.8f }, { 1.42f, 1.52f, 0.8f }, { 1.45f, 1.55f, 0.8f }, { 1.5f, 1.52f, 0.78f } };
	constexpr auto fist_gather = 0.85f;
	constexpr structures::vec2_s fist_thumb[3] = { { 0.55f, -0.35f }, { 0.45f, 0.0f }, { 0.55f, 0.0f } };
	constexpr auto hands_breath_rate = 0.23f;
	constexpr auto hands_drift = 0.0055f;
	constexpr auto hands_wobble = 0.035f;
	constexpr auto hands_step_dip = 0.012f;
	constexpr auto hands_step_swing = 0.016f;
	constexpr auto hands_sprint_pump = 0.07f;
	constexpr structures::vec3_s viewmodel_offset{ 0.02f, -0.02f, 0.14f };
	constexpr structures::vec3_s viewmodel_pole{ -0.45f, -1.0f, 0.25f };
	constexpr std::float_t viewmodel_curl[3] = { 1.2f, 1.45f, 1.0f };
	constexpr std::float_t support_curl[3] = { 1.15f, 1.35f, 0.9f };
	constexpr std::float_t viewmodel_thumb[3] = { 0.25f, 0.45f, 0.55f };
	constexpr std::float_t viewmodel_fit_limits[2][3] = { { 0.9f, 1.0f, 1.1f }, { 1.5f, 1.6f, 1.05f } };
	constexpr std::float_t viewmodel_fit_radius[5] = { 0.0105f, 0.0092f, 0.0095f, 0.0088f, 0.0078f };
	constexpr auto viewmodel_fit_reach = 0.2f;
	constexpr auto viewmodel_fit_step = 0.035f;
	constexpr auto viewmodel_fit_samples = 12u;
	constexpr auto viewmodel_fit_steps = 48u;
	constexpr auto viewmodel_fit_band = 0.022f;
	constexpr auto viewmodel_grip_lead = 0.002f;
	constexpr auto viewmodel_palm_gap = 0.011f;
	constexpr auto viewmodel_swing_step = 0.1f;
	constexpr auto viewmodel_swing_limit = 1.4f;
	constexpr structures::vec3_s viewmodel_study_wrist{ 0.0f, -0.14f, 0.34f };
	constexpr structures::vec3_s viewmodel_study_gun{ 0.0f, -0.1f, 0.36f };
	constexpr auto viewmodel_palm_center = 0.064f;
	constexpr auto viewmodel_palm_surface = 0.017f;
	constexpr structures::vec2_s viewmodel_fit_window{ 0.032f, 0.045f };
	constexpr const char* viewmodel_fingers[5][3] = { { "Bip01 R Finger0", "Bip01 R Finger01", "Bip01 R Finger02" }, { "Bip01 R Finger1", "Bip01 R Finger11", "Bip01 R Finger12" }, { "Bip01 R Finger2", "Bip01 R Finger21", "Bip01 R Finger22" }, { "Bip01 R Finger3", "Bip01 R Finger31", "Bip01 R Finger32" }, { "Bip01 R Finger4", "Bip01 R Finger41", "Bip01 R Finger42" } };

	constexpr structures::vec4_s water_extinction{ 0.36f, 0.1f, 0.085f, 0.0f };
	constexpr structures::vec4_s water_scatter{ 0.008f, 0.048f, 0.07f, 0.0f };
	constexpr structures::vec4_s water_shallow_tint{ 0.06f, 0.36f, 0.34f, 0.0f };
	constexpr structures::vec4_s water_foam{ 0.85f, 0.0f, 0.0f, 0.0f };
	constexpr structures::vec4_s water_waves[8] =
	{
		{ 0.8f, 0.6f, 72.0f, 0.5f },
		{ 0.56f, 0.83f, 43.0f, 0.34f },
		{ 0.99f, 0.14f, 29.0f, 0.24f },
		{ 0.21f, 0.98f, 17.0f, 0.13f },
		{ 0.96f, -0.28f, 11.0f, 0.08f },
		{ -0.05f, 1.0f, 7.0f, 0.05f },
		{ 0.9f, 0.43f, 4.3f, 0.028f },
		{ -0.44f, 0.9f, 2.7f, 0.016f }
	};

	constexpr const char* death_texts[10] = { "a bad fall", "the void", "drowning", "a gunshot", "starvation", "a beating", "giving up", "the cold", "the train", "a wreck" };
	constexpr const char* death_lines[10] = { "The fall broke you.", "The island swallowed you.", "The sea took your last breath.", "A bullet found you.", "Hunger finished what the island started.", "You were beaten into the dirt.", "You gave up.", "The cold got into your bones.", "The train did not stop for you.", "The wreck went up with you inside." };

	constexpr structures::vec3_s movement_unstick[14] =
	{
		{ 0.0f, 0.04f, 0.0f },
		{ 0.0f, 0.12f, 0.0f },
		{ 0.0f, 0.25f, 0.0f },
		{ 0.2f, 0.0f, 0.0f },
		{ -0.2f, 0.0f, 0.0f },
		{ 0.0f, 0.0f, 0.2f },
		{ 0.0f, 0.0f, -0.2f },
		{ 0.0f, 0.5f, 0.0f },
		{ 0.4f, 0.25f, 0.0f },
		{ -0.4f, 0.25f, 0.0f },
		{ 0.0f, 0.25f, 0.4f },
		{ 0.0f, 0.25f, -0.4f },
		{ 0.0f, 1.0f, 0.0f },
		{ 0.0f, 2.0f, 0.0f }
	};

	constexpr const char* profile_names[structures::profile_count] = { "c0 ground", "c0 foliage", "c1 ground", "c1 foliage", "c2 ground", "c2 foliage", "c3 ground", "c3 foliage", "world", "terrain", "foliage", "grass", "models", "decals", "ssao", "clouds", "lighting", "effects", "post" };

	constexpr structures::vec4_s grass_sprites[grass_sprite_count] =
	{
		{ 0.0f, 0.1992f, 0.4922f, 0.5f },
		{ 0.5176f, 0.0601f, 0.9829f, 0.5f },
		{ 0.0156f, 0.6694f, 0.4805f, 1.0f },
		{ 0.5254f, 0.8477f, 0.9624f, 1.0f }
	};

	constexpr structures::font_face_s font_faces[structures::font_count] =
	{
		{ L"Bahnschrift", FW_NORMAL },
		{ L"Bahnschrift SemiBold", FW_SEMIBOLD },
		{ L"Bahnschrift Light", FW_LIGHT },
		{ L"Bahnschrift SemiBold Condensed", FW_SEMIBOLD },
		{ L"Consolas", FW_NORMAL },
		{ L"Kalam", FW_NORMAL },
		{ L"Kalam", FW_BOLD },
		{ L"IM FELL English", FW_NORMAL },
		{ L"IM FELL English SC", FW_NORMAL },
		{ L"Bahnschrift Bold Condensed", FW_BOLD }
	};

	namespace functions
	{
		constexpr std::uint32_t rgba(std::uint32_t r, std::uint32_t g, std::uint32_t b, std::uint32_t a)
		{
			return (r & 0xFFu) | ((g & 0xFFu) << 8u) | ((b & 0xFFu) << 16u) | ((a & 0xFFu) << 24u);
		}

		constexpr std::uint32_t with_alpha(std::uint32_t color, std::float_t alpha)
		{
			return (color & 0x00FFFFFFu) | (static_cast<std::uint32_t>(static_cast<std::float_t>(color >> 24u) * (alpha < 0.0f ? 0.0f : (alpha > 1.0f ? 1.0f : alpha))) << 24u);
		}

		constexpr std::uint64_t hash(const char* text)
		{
			auto value{ 0xCBF29CE484222325ull };

			for (; *text; text++)
			{
				value = (value ^ static_cast<std::uint8_t>(*text)) * 0x100000001B3ull;
			}

			return value;
		}

		constexpr structures::setting_row_s header_row(std::uint32_t tab, const char* label)
		{
			return { tab, structures::row_header, "", label, "", 0u, nullptr, nullptr, nullptr, nullptr, 0u, 0.0f, 0.0f, 0.0f, 1.0f, "", false };
		}

		constexpr structures::setting_row_s choice_row(std::uint32_t tab, const char* key, const char* label, const char* description, std::uint32_t impact, std::uint32_t structures::user_settings_s::* member, const char* const* names, std::uint32_t count, bool graphics)
		{
			return { tab, structures::row_choice, key, label, description, impact, member, nullptr, nullptr, names, count, 0.0f, 0.0f, 0.0f, 1.0f, "", graphics };
		}

		constexpr structures::setting_row_s slider_row(std::uint32_t tab, const char* key, const char* label, const char* description, std::uint32_t impact, std::float_t structures::user_settings_s::* member, std::float_t low, std::float_t high, std::float_t step, std::float_t display, const char* format)
		{
			return { tab, structures::row_slider, key, label, description, impact, nullptr, member, nullptr, nullptr, 0u, low, high, step, display, format, false };
		}

		constexpr structures::setting_row_s toggle_row(std::uint32_t tab, const char* key, const char* label, const char* description, std::uint32_t impact, bool structures::user_settings_s::* member, bool graphics)
		{
			return { tab, structures::row_toggle, key, label, description, impact, nullptr, nullptr, member, nullptr, 0u, 0.0f, 0.0f, 0.0f, 1.0f, "", graphics };
		}

		constexpr structures::setting_row_s preset_row(std::uint32_t tab, const char* label, const char* description)
		{
			return { tab, structures::row_preset, "quality", label, description, 3u, nullptr, nullptr, nullptr, nullptr, 0u, 0.0f, 0.0f, 0.0f, 1.0f, "", false };
		}

		template <typename type_t> void release(type_t*& object)
		{
			if (object)
			{
				object->Release();

				object = nullptr;
			}
		}

		std::uint32_t lerp_color(std::uint32_t a, std::uint32_t b, std::float_t t);
		std::string executable_directory();
		bool read_file(const char* path, std::vector<std::uint8_t>& out);
		bool write_file(const char* path, const void* data, std::size_t size);
	}

	constexpr auto settings_file_name = "settings.ini";
	constexpr auto save_file_name = "island.sav";
	constexpr std::uint32_t save_magic = 0x3153505Au;
	constexpr std::uint32_t save_version = 6u;
	constexpr std::uint32_t save_oldest = 6u;
	constexpr std::uint32_t save_tiers = 4u;
	constexpr std::uint32_t save_recipes = 5u;
	constexpr auto save_interval = 90.0f;
	constexpr auto title_shot_time = 13.0f;
	constexpr auto title_fade_time = 1.4f;
	constexpr auto title_hours = 17.4f;
	constexpr auto wake_hours = 6.9f;
	constexpr auto wake_fade_time = 0.9f;
	constexpr auto wake_time = 4.6f;
	constexpr auto loading_tip_time = 6.5f;
	constexpr auto loading_minimum = 1.8f;
	constexpr auto loading_fade = 0.5f;
	constexpr auto loading_footprints = 16u;

	constexpr auto kit_text = functions::rgba(236u, 233u, 226u, 255u);
	constexpr auto kit_dim = functions::rgba(170u, 167u, 160u, 255u);
	constexpr auto kit_faint = functions::rgba(112u, 110u, 106u, 255u);
	constexpr auto kit_accent = functions::rgba(226u, 170u, 80u, 255u);
	constexpr auto kit_danger = functions::rgba(224u, 84u, 64u, 255u);
	constexpr auto kit_cool = functions::rgba(124u, 178u, 214u, 255u);
	constexpr auto kit_good = functions::rgba(132u, 190u, 120u, 255u);
	constexpr auto kit_panel = functions::rgba(9u, 10u, 12u, 218u);
	constexpr auto kit_raise = functions::rgba(255u, 255u, 255u, 14u);
	constexpr auto kit_line = functions::rgba(255u, 255u, 255u, 30u);
	constexpr auto kit_black = functions::rgba(0u, 0u, 0u, 255u);
	constexpr auto kit_caps = 0.14f;
	constexpr auto kit_wide = 0.24f;
	constexpr auto kit_title_spacing = 0.035f;
	constexpr auto kit_row = 50.0f;
	constexpr auto kit_slots = 512u;
	constexpr auto kit_hover_volume = 0.12f;
	constexpr auto kit_click_volume = 0.5f;
	constexpr auto kit_fade_speed = 12.0f;
	constexpr auto kit_dialog_seconds = 15.0f;
	constexpr auto kit_fps_window = 0.5f;
	constexpr auto reduced_flash_scale = 0.3f;
	constexpr auto motion_blur_shutter = 0.5f;

	constexpr auto hud_belt_hold = 2.4f;
	constexpr auto hud_vital_hold = 4.0f;
	constexpr auto hud_vital_low = 0.5f;
	constexpr auto hud_vital_step = 0.5f;
	constexpr auto hud_fade_speed = 7.0f;
	constexpr auto hud_belt_slot = 62.0f;
	constexpr auto hud_grid_slot = 84.0f;
	constexpr auto hud_slot_gap = 6.0f;
	constexpr auto hud_grid_columns = 6u;
	constexpr auto hud_box_columns = 4u;
	constexpr auto hud_recipe_row = 34.0f;
	constexpr auto hud_detail_height = 150.0f;
	constexpr auto hud_meter_width = 190.0f;
	constexpr auto hud_health = functions::rgba(230u, 226u, 218u, 255u);
	constexpr auto hud_breath = functions::rgba(170u, 214u, 236u, 255u);
	constexpr auto hud_blood = functions::rgba(206u, 58u, 44u, 255u);
	constexpr const char* hud_vital_labels[4] = { "Health", "Water", "Food", "Breath" };
	constexpr const char* keypad_labels[12] = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "Clear", "0", "OK" };

	constexpr auto preset_custom = static_cast<std::uint32_t>(structures::quality_count);
	constexpr const char* option_off_on[] = { "Off", "On" };
	constexpr const char* option_levels[] = { "Off", "Low", "Medium", "High", "Ultra" };
	constexpr const char* option_occlusion[] = { "Off", "Low", "Medium", "High" };
	constexpr std::uint32_t occlusion_levels[] = { 0u, 2u, 3u, 4u };
	constexpr const char* option_presets[] = { "Low", "Medium", "High", "Ultra", "Custom" };
	constexpr const char* option_display[] = { "Windowed", "Fullscreen" };
	constexpr const char* option_window_sizes[] = { "1280 x 720", "1600 x 900", "1920 x 1080", "2560 x 1440", "3840 x 2160" };
	constexpr std::uint32_t window_sizes[][2] = { { 1280u, 720u }, { 1600u, 900u }, { 1920u, 1080u }, { 2560u, 1440u }, { 3840u, 2160u } };
	constexpr const char* option_frame_limits[] = { "Unlimited", "30 fps", "60 fps", "90 fps", "120 fps", "144 fps", "165 fps", "240 fps" };
	constexpr std::float_t frame_limits[] = { 0.0f, 30.0f, 60.0f, 90.0f, 120.0f, 144.0f, 165.0f, 240.0f };
	constexpr const char* option_anti_aliasing[] = { "Off", "Temporal" };
	constexpr const char* option_filtering[] = { "2x", "4x", "8x", "16x" };
	constexpr const char* option_distances[] = { "Near", "Medium", "Far", "Very far" };
	constexpr std::float_t vegetation_scales[] = { 0.55f, 0.75f, 1.0f, 1.3f };
	constexpr const char* option_density[] = { "Low", "Medium", "High", "Ultra" };
	constexpr std::float_t grass_scales[] = { 0.6f, 0.8f, 1.0f, 1.2f };
	constexpr const char* option_hold[] = { "Hold", "Toggle" };
	constexpr const char* option_bob[] = { "Off", "Reduced", "Full" };
	constexpr std::float_t bob_scales[] = { 0.0f, 0.5f, 1.0f };
	constexpr const char* option_crosshair[] = { "Off", "Small dot", "Always on" };
	constexpr auto calm_camera_scale = 0.3f;
	constexpr const char* option_vitals[] = { "Always", "When needed" };
	constexpr const char* option_hotbar[] = { "When switching", "Always", "Hidden" };
	constexpr const char* option_colour[] = { "Off", "Protanopia", "Deuteranopia", "Tritanopia" };
	constexpr const char* settings_tab_names[structures::tab_count] = { "Display", "Graphics", "Audio", "Controls", "Key bindings", "Gameplay", "Interface", "Accessibility" };
	constexpr const char* impact_names[] = { "None", "Low", "Medium", "High" };
	constexpr structures::setting_row_s setting_rows[] =
	{
		functions::header_row(structures::tab_display, "Screen"),
		functions::choice_row(structures::tab_display, "display", "Display mode", "Fullscreen fills your monitor without a border and switches instantly. Windowed runs the game in a window you can move and resize.", 0u, &structures::user_settings_s::display, option_display, static_cast<std::uint32_t>(std::size(option_display)), false),
		functions::choice_row(structures::tab_display, "window_size", "Window size", "The size of the game window when it runs windowed. In fullscreen the game always uses your monitor's resolution.", 0u, &structures::user_settings_s::window_size, option_window_sizes, static_cast<std::uint32_t>(std::size(option_window_sizes)), false),
		functions::toggle_row(structures::tab_display, "vsync", "Vertical sync", "Locks the frame rate to your monitor's refresh rate so the image never tears. Adds a little input delay.", 0u, &structures::user_settings_s::vsync, false),
		functions::choice_row(structures::tab_display, "frame_limit", "Frame rate limit", "Caps how many frames the game draws each second. A limit keeps your graphics card cooler and quieter.", 0u, &structures::user_settings_s::frame_limit, option_frame_limits, static_cast<std::uint32_t>(std::size(option_frame_limits)), false),
		functions::header_row(structures::tab_display, "Image"),
		functions::slider_row(structures::tab_display, "render_scale", "Render scale", "Draws the world at a lower resolution and scales it up to your screen. Lower values run much faster but look softer.", 3u, &structures::user_settings_s::render_scale, 0.5f, 1.0f, 0.05f, 100.0f, "%.0f%%"),
		functions::slider_row(structures::tab_display, "field_of_view", "Field of view", "How wide you can see. A wider view shows more around you but makes distant things look smaller.", 1u, &structures::user_settings_s::field_of_view, 70.0f, 110.0f, 1.0f, 1.0f, "%.0f\xB0"),
		functions::slider_row(structures::tab_display, "brightness", "Brightness", "Raise it if nights are too dark on your screen, lower it if black looks grey.", 0u, &structures::user_settings_s::brightness, 0.7f, 1.3f, 0.01f, 100.0f, "%.0f%%"),
		functions::toggle_row(structures::tab_display, "show_fps", "Show frame rate", "Shows frames per second and the time each frame takes in the top right corner.", 0u, &structures::user_settings_s::show_fps, false),
		functions::preset_row(structures::tab_graphics, "Quality preset", "Sets every graphics option below at once. Changing any single option switches the preset to Custom."),
		functions::header_row(structures::tab_graphics, "Detail"),
		functions::choice_row(structures::tab_graphics, "shadows", "Shadows", "Quality and reach of the sun's shadows. Off removes shadows completely and is much faster.", 3u, &structures::user_settings_s::shadows, option_levels, static_cast<std::uint32_t>(std::size(option_levels)), true),
		functions::choice_row(structures::tab_graphics, "ambient_occlusion", "Ambient occlusion", "Darkens corners, creases and the ground under objects so everything sits in the world.", 2u, &structures::user_settings_s::ambient_occlusion, option_occlusion, static_cast<std::uint32_t>(std::size(option_occlusion)), true),
		functions::choice_row(structures::tab_graphics, "reflections", "Reflections", "Reflections of the shore, the sky and the sun on the sea.", 2u, &structures::user_settings_s::reflections, option_off_on, 2u, true),
		functions::choice_row(structures::tab_graphics, "light_shafts", "Light shafts", "Beams of sunlight breaking through trees, haze and fog.", 1u, &structures::user_settings_s::light_shafts, option_off_on, 2u, true),
		functions::choice_row(structures::tab_graphics, "clouds", "Volumetric clouds", "Real three-dimensional clouds that drift with the wind, glow at sunrise and sunset and cast moving shadows over the island. Off draws a flat cloud layer instead.", 2u, &structures::user_settings_s::clouds, option_off_on, 2u, true),
		functions::choice_row(structures::tab_graphics, "texture_filter", "Texture filtering", "Keeps the ground, roads and walls sharp when you look along them.", 1u, &structures::user_settings_s::texture_filter, option_filtering, static_cast<std::uint32_t>(std::size(option_filtering)), true),
		functions::choice_row(structures::tab_graphics, "vegetation", "Vegetation distance", "How far away trees and bushes keep their full detail before they swap to simpler versions.", 3u, &structures::user_settings_s::vegetation, option_distances, static_cast<std::uint32_t>(std::size(option_distances)), true),
		functions::choice_row(structures::tab_graphics, "grass", "Grass density", "How thick the grass grows and how far out it is drawn around you.", 3u, &structures::user_settings_s::grass, option_density, static_cast<std::uint32_t>(std::size(option_density)), true),
		functions::choice_row(structures::tab_graphics, "marks", "Bullet holes and footprints", "Marks left by bullets, blood and footsteps. Turning them off only hides them on your screen.", 1u, &structures::user_settings_s::marks, option_off_on, 2u, true),
		functions::header_row(structures::tab_graphics, "Post processing"),
		functions::choice_row(structures::tab_graphics, "anti_aliasing", "Anti-aliasing", "Smooths jagged edges. Temporal gives the cleanest image but can soften very fast motion slightly.", 1u, &structures::user_settings_s::anti_aliasing, option_anti_aliasing, static_cast<std::uint32_t>(std::size(option_anti_aliasing)), true),
		functions::slider_row(structures::tab_graphics, "sharpening", "Sharpening", "Brings back fine detail softened by anti-aliasing or a lower render scale.", 0u, &structures::user_settings_s::sharpening, 0.0f, 1.0f, 0.05f, 100.0f, "%.0f%%"),
		functions::toggle_row(structures::tab_graphics, "bloom", "Bloom", "The sun and bright lights glow softly into their surroundings.", 1u, &structures::user_settings_s::bloom, false),
		functions::toggle_row(structures::tab_graphics, "motion_blur", "Motion blur", "Blurs the image while you turn quickly or move fast, like a camera would.", 1u, &structures::user_settings_s::motion_blur, false),
		functions::toggle_row(structures::tab_graphics, "film_grain", "Film grain", "A fine moving grain over the image, like a film camera.", 0u, &structures::user_settings_s::film_grain, false),
		functions::toggle_row(structures::tab_graphics, "vignette", "Vignette", "Gently darkens the corners of the screen.", 0u, &structures::user_settings_s::vignette, false),
		functions::toggle_row(structures::tab_graphics, "chromatic_aberration", "Chromatic aberration", "Slight colour fringes towards the edges of the screen, like a real lens.", 0u, &structures::user_settings_s::chromatic_aberration, false),
		functions::header_row(structures::tab_audio, "Volume"),
		functions::slider_row(structures::tab_audio, "volume", "Master volume", "The overall loudness of the game.", 0u, &structures::user_settings_s::volume, 0.0f, 1.0f, 0.01f, 100.0f, "%.0f%%"),
		functions::slider_row(structures::tab_audio, "effects_volume", "Effects", "Gunshots, footsteps, tools, the train and everything else that happens in the world.", 0u, &structures::user_settings_s::effects_volume, 0.0f, 1.0f, 0.01f, 100.0f, "%.0f%%"),
		functions::slider_row(structures::tab_audio, "ambience_volume", "Ambience", "Wind, sea, birds, insects and rain.", 0u, &structures::user_settings_s::ambience_volume, 0.0f, 1.0f, 0.01f, 100.0f, "%.0f%%"),
		functions::slider_row(structures::tab_audio, "interface_volume", "Interface", "Menu clicks and inventory sounds.", 0u, &structures::user_settings_s::interface_volume, 0.0f, 1.0f, 0.01f, 100.0f, "%.0f%%"),
		functions::header_row(structures::tab_audio, "Behaviour"),
		functions::toggle_row(structures::tab_audio, "mute_unfocused", "Mute in the background", "Silences the game while another window is in front of it.", 0u, &structures::user_settings_s::mute_unfocused, false),
		functions::toggle_row(structures::tab_audio, "ear_ringing", "Ear ringing", "Gunfire right next to you leaves your ears ringing for a few seconds and dulls everything else, as it would without ear protection. Worst indoors.", 0u, &structures::user_settings_s::ear_ringing, false),
		functions::header_row(structures::tab_controls, "Mouse"),
		functions::slider_row(structures::tab_controls, "sensitivity", "Mouse sensitivity", "How far the view turns for each movement of your mouse.", 0u, &structures::user_settings_s::sensitivity, 0.3f, 3.0f, 0.05f, 1.0f, "%.2fx"),
		functions::slider_row(structures::tab_controls, "aim_sensitivity", "Aiming sensitivity", "Scales your sensitivity while aiming down the sights or through a scope.", 0u, &structures::user_settings_s::aim_sensitivity, 0.3f, 1.5f, 0.05f, 1.0f, "%.2fx"),
		functions::toggle_row(structures::tab_controls, "invert", "Invert vertical look", "Moving the mouse forward looks down instead of up.", 0u, &structures::user_settings_s::invert, false),
		functions::toggle_row(structures::tab_controls, "reverse_wheel", "Reverse belt scrolling", "Scrolling the wheel down picks the previous belt slot instead of the next one.", 0u, &structures::user_settings_s::reverse_wheel, false),
		functions::header_row(structures::tab_controls, "Actions"),
		functions::choice_row(structures::tab_controls, "crouch_mode", "Crouch", "Hold the key to stay crouched, or press it once to crouch and again to stand.", 0u, &structures::user_settings_s::crouch_mode, option_hold, 2u, false),
		functions::choice_row(structures::tab_controls, "aim_mode", "Aim down sights", "Hold the right mouse button to aim, or click once to raise the sights and again to lower them.", 0u, &structures::user_settings_s::aim_mode, option_hold, 2u, false),
		functions::choice_row(structures::tab_controls, "sprint_mode", "Sprint", "Hold the key to sprint, or press it once and keep running until you stop.", 0u, &structures::user_settings_s::sprint_mode, option_hold, 2u, false),
		functions::header_row(structures::tab_gameplay, "Camera"),
		functions::choice_row(structures::tab_gameplay, "head_bob", "Head bob", "How much the view moves with your footsteps. Turn it down if movement makes you feel unwell.", 0u, &structures::user_settings_s::head_bob, option_bob, static_cast<std::uint32_t>(std::size(option_bob)), false),
		functions::toggle_row(structures::tab_gameplay, "strafe_tilt", "Lean when strafing", "Tilts the view a little as you step sideways.", 0u, &structures::user_settings_s::strafe_tilt, false),
		functions::header_row(structures::tab_gameplay, "Help"),
		functions::toggle_row(structures::tab_gameplay, "hints", "Survival goals", "Shows your next survival goal in the corner of the screen when you play on your own.", 0u, &structures::user_settings_s::hints, false),
		functions::toggle_row(structures::tab_gameplay, "prompts", "Interaction prompts", "Shows what you can do with the thing in front of you, like opening a door or picking up a stone. Turn it off for an emptier screen.", 0u, &structures::user_settings_s::prompts, false),
		functions::header_row(structures::tab_gameplay, "Content"),
		functions::toggle_row(structures::tab_gameplay, "censor", "Censor nudity", "Survivors start with nothing, not even clothes. Turn this on and everyone you see, you included, wears underwear instead.", 0u, &structures::user_settings_s::censor, false),
		functions::header_row(structures::tab_interface, "Heads-up display"),
		functions::choice_row(structures::tab_interface, "crosshair", "Crosshair", "A small dot in the middle of the screen. It hides while you hold a gun or a bow, so you aim down the sights, unless you set it to always on.", 0u, &structures::user_settings_s::crosshair, option_crosshair, static_cast<std::uint32_t>(std::size(option_crosshair)), false),
		functions::toggle_row(structures::tab_interface, "hit_markers", "Hit markers", "A brief mark at the centre of the screen when your shot or swing lands.", 0u, &structures::user_settings_s::hit_markers, false),
		functions::toggle_row(structures::tab_interface, "damage_direction", "Damage direction", "A red arc around the middle of the screen points to where a hit came from.", 0u, &structures::user_settings_s::damage_direction, false),
		functions::toggle_row(structures::tab_interface, "compass", "Compass", "The bearing strip at the top of the screen, with your map pins on it.", 0u, &structures::user_settings_s::compass, false),
		functions::choice_row(structures::tab_interface, "vitals", "Health, water and food", "Always show your condition, or only while something is low or changing.", 0u, &structures::user_settings_s::vitals, option_vitals, static_cast<std::uint32_t>(std::size(option_vitals)), false),
		functions::choice_row(structures::tab_interface, "hotbar", "Belt", "Shows your belt for a moment after you change what you are holding, always, or never. Nothing ever tells you how many rounds are loaded.", 0u, &structures::user_settings_s::hotbar, option_hotbar, static_cast<std::uint32_t>(std::size(option_hotbar)), false),
		functions::toggle_row(structures::tab_interface, "name_tags", "Player names", "The names of other players you look at up close.", 0u, &structures::user_settings_s::name_tags, false),
		functions::toggle_row(structures::tab_interface, "chat", "Chat", "Shows the text chat in the lower left corner.", 0u, &structures::user_settings_s::chat, false),
		functions::toggle_row(structures::tab_interface, "pickup_messages", "Pickup messages", "Lists what you pick up and gather in the lower right corner.", 0u, &structures::user_settings_s::pickup_messages, false),
		functions::header_row(structures::tab_interface, "Layout"),
		functions::slider_row(structures::tab_interface, "interface_scale", "Interface size", "Makes every menu and the heads-up display bigger or smaller.", 0u, &structures::user_settings_s::interface_scale, 0.8f, 1.25f, 0.05f, 100.0f, "%.0f%%"),
		functions::header_row(structures::tab_accessibility, "Vision"),
		functions::choice_row(structures::tab_accessibility, "colour_filter", "Colour blind filter", "Shifts the colours of the whole image so they are easier to tell apart with the most common kinds of colour blindness.", 0u, &structures::user_settings_s::colour_filter, option_colour, static_cast<std::uint32_t>(std::size(option_colour)), false),
		functions::toggle_row(structures::tab_accessibility, "reduce_flashing", "Reduce flashing", "Softens lightning flashes and other sudden bright light.", 0u, &structures::user_settings_s::reduce_flashing, false),
		functions::header_row(structures::tab_accessibility, "Comfort"),
		functions::toggle_row(structures::tab_accessibility, "calm_camera", "Reduce camera motion", "Softens the dip when you land and the rise and fall of the waves while you swim.", 0u, &structures::user_settings_s::calm_camera, false)
	};

	constexpr const char* loading_stage_names[] = { "Gathering driftwood", "Weaving the rags", "Raising the sky", "Listening to the wind", "Shaping the island", "Inking the map", "Waiting for dawn" };
	constexpr const char* loading_tips[] =
	{
		"Sea water keeps you alive a little longer. It also kills you.",
		"Springs are marked on the map. Most people never find them.",
		"Chop one side of a trunk. The tree falls away from the notch.",
		"A well keeps every crop around it watered.",
		"Cook what you find. A raw potato barely counts as food.",
		"Crops left too long after they ripen will rot where they stand.",
		"Nothing here is new. Everything here can be made.",
		"The furnace eats wood and gives back charcoal. Keep both.",
		"Wrap your hands. Build a fire. Then worry about the rest.",
		"A sleeping bag is the only promise the island keeps.",
		"Stone first. Then fire. Then everything else."
	};

	constexpr structures::menu_entry_s title_entries[] = { { "Play", structures::menu_play }, { "Settings", structures::menu_settings }, { "Field guide", structures::menu_notes }, { "Credits", structures::menu_credits }, { "Quit", structures::menu_quit } };
	constexpr structures::menu_entry_s pause_entries[] = { { "Resume", structures::menu_resume }, { "Settings", structures::menu_settings }, { "Field guide", structures::menu_notes }, { "Leave server", structures::menu_title }, { "Quit to desktop", structures::menu_quit } };
	constexpr const char* title_details[] = { "Find an island and join it", "Display, graphics, sound and controls", "How to move and how to stay alive", "Who made what", "Back to the desktop" };
	constexpr const char* pause_details[] = { "Back to the island", "Display, graphics, sound and controls", "How to move and how to stay alive", "Return to the server list", "Close the game" };
	constexpr const char* credit_lines[][2] =
	{
		{ "Made by", "tokenizestring" },
		{ "Engine", "Written from scratch in C++20 on Direct3D 11" },
		{ "Ground and surface textures", "Poly Haven and ambientCG (CC0), plus our own generated sets" },
		{ "Characters", "Microsoft Rocketbox avatar library (MIT)" },
		{ "Sounds", "Kenney and OpenGameArt contributors (CC0), plus our own synthesised sounds" },
		{ "Buildings, trees, train, animals", "Modelled in Blender for this game" },
		{ "Fonts", "Kalam and IM Fell (SIL Open Font License), Bahnschrift" },
		{ "Status", "Early development. Expect bugs." }
	};
	constexpr const char* quality_names[] = { "Low", "Medium", "High", "Ultra" };

	constexpr std::int32_t guide_movement = -2;
	constexpr structures::guide_key_s guide_keys[] =
	{
		{ guide_movement, "", "Walk" },
		{ structures::bind_sprint, "", "Sprint" },
		{ structures::bind_jump, "", "Jump" },
		{ structures::bind_crouch, "", "Crouch" },
		{ -1, "Left mouse", "Swing, fire, plant, eat" },
		{ -1, "Right mouse", "Aim down the sights" },
		{ -1, "Hold left mouse", "Draw the bow" },
		{ structures::bind_reload, "", "Reload" },
		{ structures::bind_rotate, "", "Turn a building piece" },
		{ structures::bind_use, "", "Pick up, open, drink, harvest" },
		{ -1, "1 to 6, wheel", "Choose from the belt" },
		{ structures::bind_inventory, "", "Inventory and crafting" },
		{ structures::bind_map, "", "Unfold the map" },
		{ structures::bind_chat, "", "Chat" },
		{ -1, "Esc", "Pause" }
	};

	constexpr const char* notes_survival[] =
	{
		"Water runs out long before food does. Find a spring,",
		"or dig a well. The sea will only buy you a little time.",
		"",
		"Strike trees and stones with a rock until you can",
		"make a hatchet and a pickaxe. Everything starts there.",
		"",
		"Wild potatoes, corn and pumpkins grow in the grass.",
		"Eat one, or plant it. Crops near a well never go dry.",
		"",
		"A campfire cooks. A furnace smelts. Both need wood.",
		"",
		"Chop a tree from one side and keep chopping. When the",
		"notch runs deep enough it falls away from you. Stand clear.",
		"",
		"Lay down a sleeping bag before you die, not after."
	};

	constexpr structures::user_settings_s default_user_settings{ structures::quality_high, 1.0f, 95.0f, 1.0f, 0.85f, 1.0f, 1.0f, 1.0f, true, true, false, false, { 'W', 'S', 'A', 'D', VK_SPACE, VK_CONTROL, VK_SHIFT, VK_MENU, 'E', 'R', 'R', VK_TAB, 'M', 'T', 'F', 'G', 'V' }, 1u, 1u, 0u, 1u, 3u, 2u, 1u, 1u, 3u, 2u, 2u, 1u, true, false, true, 0.35f, false, 0.7f, false, 0.8f, 0u, 0u, 0u, 2u, 1u, true, true, true, 1u, 0u, true, true, 1.0f, 0u, false, false, true, true, true, true, false, true, false, 1u };
	constexpr const char* bind_names[structures::bind_count] = { "Move forward", "Move back", "Move left", "Move right", "Jump", "Crouch", "Sprint", "Walk", "Use", "Reload", "Rotate or next piece", "Inventory", "Map", "Chat", "Melee", "Throw", "Visor" };
	constexpr const char* compass_points[8] = { "N", "NE", "E", "SE", "S", "SW", "W", "NW" };
	constexpr const char* marker_prefixes[6] = { "col_", "ramp_", "loot_", "light_", "seat_", "exhaust" };
	constexpr const char* village_models[8] = { "bld_cottage", "bld_house", "bld_cottage", "bld_ruin", "bld_house", "bld_barn", "bld_cottage", "bld_shed" };
	constexpr const char* farm_models[3] = { "bld_house", "bld_barn", "bld_shed" };
	constexpr const char* hamlet_models[4] = { "bld_cottage", "bld_shed", "bld_ruin", "bld_cottage" };
	constexpr const char* outlier_models[2] = { "bld_shed", "bld_ruin" };
	constexpr auto town_clear_radius = 165.0f;
	constexpr auto town_grid = 2.0f;
	constexpr auto town_tile = 4.0f;
	constexpr auto town_footing = 0.3f;
	constexpr auto town_kerb_drop = 0.08f;
	constexpr auto town_route_margin = 2.0f;
	constexpr auto town_dash_length = 1.8f;
	constexpr auto town_dash_spacing = 5.0f;
	constexpr auto town_dash_width = 0.12f;
	constexpr auto town_dash_lift = 0.006f;
	constexpr auto town_dash_worn = 0.18f;
	constexpr auto town_dash_minimum = 30.0f;
	constexpr auto town_lamp_spacing = 26.0f;
	constexpr auto town_lamp_inset = 0.55f;
	constexpr auto town_prop_near = 140.0f;
	constexpr auto town_prop_far = 420.0f;
	constexpr auto town_prop_shadow = 90.0f;
	constexpr auto town_wrecks = 12u;
	constexpr auto town_junction_clear = 9.0f;
	constexpr const char* town_lamp_model = "street_lamp_01";
	constexpr const char* town_wreck_models[4] = { "covered_car", "prop_wreck_hatch", "prop_wreck_saloon", "prop_wreck_van" };
	constexpr auto town_loot_chance = 0.45f;
	constexpr const char* town_barrier_models[2] = { "concrete_road_barrier", "concrete_road_barrier_02" };
	constexpr structures::town_building_s town_buildings[structures::town_building_count] =
	{
		{ "bld_terrace", { 5.5f, 9.0f }, 2u },
		{ "bld_shop", { 7.0f, 10.0f }, 2u },
		{ "bld_pub", { 12.0f, 11.0f }, 2u },
		{ "bld_church", { 12.0f, 26.0f }, 1u },
		{ "bld_police", { 12.0f, 14.0f }, 2u },
		{ "bld_clinic", { 10.0f, 12.0f }, 1u },
		{ "bld_garage", { 14.0f, 12.0f }, 1u },
		{ "bld_fuel", { 20.0f, 14.0f }, 1u },
		{ "bld_flats", { 16.0f, 11.0f }, 3u },
		{ "bld_school", { 16.0f, 10.0f }, 1u },
		{ "bld_hall", { 14.0f, 20.0f }, 1u },
		{ "bld_house", { 9.0f, 8.0f }, 2u },
		{ "bld_cottage", { 8.0f, 7.0f }, 1u },
		{ "bld_ruin", { 8.0f, 7.0f }, 1u }
	};
	constexpr structures::town_paving_s town_pavings[structures::town_surface_count] =
	{
		{ structures::material_asphalt, { 0.52f, 0.5f, 0.48f }, 0.035f, 3.0f, false },
		{ structures::material_asphalt, { 0.64f, 0.62f, 0.58f }, 0.03f, 3.0f, false },
		{ structures::material_floor_worn, { 0.82f, 0.8f, 0.76f }, 0.15f, 2.0f, true },
		{ structures::material_floor_worn, { 0.92f, 0.88f, 0.82f }, 0.15f, 3.4f, true },
		{ structures::material_concrete_rough, { 0.78f, 0.77f, 0.75f }, 0.06f, 3.0f, false }
	};
	constexpr structures::town_patch_s town_patches[] =
	{
		{ { -3.5f, -145.0f }, { 3.5f, 125.0f }, structures::town_road },
		{ { -135.0f, -3.5f }, { -3.5f, 3.5f }, structures::town_road },
		{ { 3.5f, -3.5f }, { 140.0f, 3.5f }, structures::town_road },
		{ { -66.5f, 73.5f }, { -3.5f, 78.5f }, structures::town_lane },
		{ { 3.5f, 73.5f }, { 106.5f, 78.5f }, structures::town_lane },
		{ { -66.5f, -74.5f }, { -3.5f, -69.5f }, structures::town_lane },
		{ { 3.5f, -74.5f }, { 106.5f, -69.5f }, structures::town_lane },
		{ { -66.5f, 3.5f }, { -61.5f, 73.5f }, structures::town_lane },
		{ { -66.5f, -69.5f }, { -61.5f, -3.5f }, structures::town_lane },
		{ { 101.5f, 3.5f }, { 106.5f, 73.5f }, structures::town_lane },
		{ { 101.5f, -69.5f }, { 106.5f, -3.5f }, structures::town_lane },
		{ { 3.5f, 3.5f }, { 60.0f, 50.0f }, structures::town_square },
		{ { -6.0f, 3.5f }, { -3.5f, 73.5f }, structures::town_walk },
		{ { -61.5f, 3.5f }, { -6.0f, 6.0f }, structures::town_walk },
		{ { 3.5f, 50.0f }, { 6.0f, 73.5f }, structures::town_walk },
		{ { 60.0f, 3.5f }, { 101.5f, 6.0f }, structures::town_walk },
		{ { -6.0f, -69.5f }, { -3.5f, -3.5f }, structures::town_walk },
		{ { -61.5f, -6.0f }, { -6.0f, -3.5f }, structures::town_walk },
		{ { 3.5f, -69.5f }, { 6.0f, -3.5f }, structures::town_walk },
		{ { 6.0f, -6.0f }, { 101.5f, -3.5f }, structures::town_walk },
		{ { -6.0f, 78.5f }, { -3.5f, 120.0f }, structures::town_walk },
		{ { 3.5f, 78.5f }, { 6.0f, 120.0f }, structures::town_walk },
		{ { -6.0f, -140.0f }, { -3.5f, -74.5f }, structures::town_walk },
		{ { 3.5f, -115.0f }, { 6.0f, -74.5f }, structures::town_walk },
		{ { -130.0f, 3.5f }, { -66.5f, 6.0f }, structures::town_walk },
		{ { -130.0f, -6.0f }, { -66.5f, -3.5f }, structures::town_walk },
		{ { 106.5f, 3.5f }, { 128.0f, 6.0f }, structures::town_walk },
		{ { 106.5f, -6.0f }, { 114.0f, -3.5f }, structures::town_walk },
		{ { -58.0f, -42.0f }, { -36.0f, -18.0f }, structures::town_yard }
	};
	constexpr structures::town_row_s town_rows[] =
	{
		{ { -6.0f, 73.0f }, { -6.0f, 20.0f }, 1.0f, 8u, { structures::town_shop, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_shop } },
		{ { -6.0f, 6.0f }, { -61.0f, 6.0f }, 1.0f, 8u, { structures::town_shop, structures::town_shop, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_house } },
		{ { -60.0f, 20.0f }, { -60.0f, 72.0f }, 3.0f, 2u, { structures::town_flats, structures::town_flats } },
		{ { 58.0f, 51.0f }, { 21.0f, 51.0f }, 1.0f, 4u, { structures::town_pub, structures::town_shop, structures::town_shop, structures::town_terrace } },
		{ { 6.0f, 51.0f }, { 6.0f, 73.0f }, 1.0f, 4u, { structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace } },
		{ { 100.0f, 6.0f }, { 62.0f, 6.0f }, 1.0f, 3u, { structures::town_clinic, structures::town_shop, structures::town_shop } },
		{ { -6.0f, -22.0f }, { -6.0f, -69.0f }, 1.0f, 5u, { structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_police } },
		{ { -61.0f, -6.0f }, { -12.0f, -6.0f }, 1.0f, 6u, { structures::town_school, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_shop } },
		{ { 6.0f, -69.0f }, { 6.0f, -20.0f }, 1.0f, 7u, { structures::town_shop, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_shop } },
		{ { 6.0f, -6.0f }, { 60.0f, -6.0f }, 1.0f, 6u, { structures::town_shop, structures::town_shop, structures::town_terrace, structures::town_terrace, structures::town_terrace, structures::town_garage } },
		{ { -6.0f, 120.0f }, { -6.0f, 82.0f }, 3.0f, 3u, { structures::town_house, structures::town_cottage, structures::town_house } },
		{ { 6.0f, 82.0f }, { 6.0f, 120.0f }, 3.0f, 3u, { structures::town_cottage, structures::town_ruin, structures::town_cottage } },
		{ { -6.0f, -78.0f }, { -6.0f, -140.0f }, 3.0f, 4u, { structures::town_cottage, structures::town_house, structures::town_ruin, structures::town_cottage } },
		{ { 6.0f, -115.0f }, { 6.0f, -78.0f }, 3.0f, 2u, { structures::town_house, structures::town_cottage } },
		{ { -68.0f, 6.0f }, { -130.0f, 6.0f }, 3.0f, 4u, { structures::town_cottage, structures::town_house, structures::town_cottage, structures::town_ruin } },
		{ { -130.0f, -6.0f }, { -68.0f, -6.0f }, 3.0f, 4u, { structures::town_ruin, structures::town_cottage, structures::town_house, structures::town_cottage } }
	};
	constexpr structures::town_site_s town_sites[] =
	{
		{ structures::town_church, { 73.0f, 28.0f }, half_pi },
		{ structures::town_hall, { 80.0f, 61.0f }, half_pi },
		{ structures::town_fuel, { 80.0f, -38.0f }, -0.734f }
	};
	constexpr structures::town_yard_s town_yards[] =
	{
		{ { -47.0f, 18.0f }, { -18.0f, 71.0f }, 10u },
		{ { 18.0f, 63.0f }, { 56.0f, 71.0f }, 5u },
		{ { -44.0f, -66.0f }, { -18.0f, -20.0f }, 8u },
		{ { 18.0f, -66.0f }, { 58.0f, -20.0f }, 9u },
		{ { 62.0f, 38.0f }, { 98.0f, 48.0f }, 4u }
	};
	constexpr structures::vec2_s town_memorial = { 31.75f, 26.75f };
	constexpr const char* town_memorial_model = "prop_war_memorial";
	constexpr structures::town_run_s town_runs[] =
	{
		{ "prop_garden_wall", { 60.5f, 49.5f }, { 99.5f, 49.5f }, 4.0f, structures::surface_rock },
		{ "prop_garden_wall", { 99.5f, 49.5f }, { 99.5f, 19.0f }, 4.0f, structures::surface_rock },
		{ "prop_garden_wall", { 60.5f, 49.5f }, { 60.5f, 37.0f }, 4.0f, structures::surface_rock },
		{ "prop_garden_wall", { 60.5f, 19.0f }, { 60.5f, 9.0f }, 4.0f, structures::surface_rock },
		{ "prop_railing", { -3.8f, 6.5f }, { -3.8f, 15.5f }, 3.0f, structures::surface_metal },
		{ "prop_railing", { -15.5f, 3.8f }, { -6.5f, 3.8f }, 3.0f, structures::surface_metal },
		{ "prop_railing", { -3.8f, -15.5f }, { -3.8f, -6.5f }, 3.0f, structures::surface_metal },
		{ "prop_railing", { -6.5f, -3.8f }, { -15.5f, -3.8f }, 3.0f, structures::surface_metal },
		{ "prop_railing", { 3.8f, -6.5f }, { 3.8f, -9.5f }, 3.0f, structures::surface_metal },
		{ "prop_railing", { 15.5f, -3.8f }, { 6.5f, -3.8f }, 3.0f, structures::surface_metal },
		{ "prop_sandbags", { -6.0f, -88.0f }, { -3.0f, -88.0f }, 3.0f, structures::surface_fabric },
		{ "prop_sandbags", { 3.0f, -91.0f }, { 6.0f, -91.0f }, 3.0f, structures::surface_fabric },
		{ "prop_sandbags", { -3.0f, 93.0f }, { -6.0f, 93.0f }, 3.0f, structures::surface_fabric },
		{ "prop_sandbags", { -108.0f, 6.5f }, { -108.0f, 3.5f }, 3.0f, structures::surface_fabric },
		{ "prop_sandbags", { -108.0f, -3.5f }, { -108.0f, -6.5f }, 3.0f, structures::surface_fabric }
	};
	constexpr std::float_t town_memorial_steps[3] = { 5.4f, 4.2f, 3.0f };
	constexpr auto town_memorial_rise = 0.2f;
	constexpr auto town_memorial_plinth = 1.6f;
	constexpr auto town_memorial_needle = 4.6f;
	constexpr structures::vec2_s town_planters[4] = { { 14.0f, 14.0f }, { 50.0f, 14.0f }, { 14.0f, 40.0f }, { 50.0f, 40.0f } };
	constexpr structures::vec2_s town_trees[] = { { 64.0f, 13.0f }, { 66.0f, 45.0f }, { 90.0f, 46.0f }, { 97.0f, 30.0f }, { -30.0f, 60.0f }, { 30.0f, -45.0f }, { -25.0f, -50.0f }, { 40.0f, 67.0f } };
	constexpr auto town_planter_size = 2.8f;
	constexpr auto town_planter_rim = 0.2f;
	constexpr auto town_planter_height = 0.5f;
	constexpr auto town_planter_soil = 0.36f;
	constexpr auto town_bollard_spacing = 2.6f;
	constexpr auto town_bollard_inset = 0.45f;
	constexpr structures::town_prop_s town_props[] =
	{
		{ "prop_bench", { 31.75f, 32.75f }, 0.0f, structures::surface_wood },
		{ "prop_bench", { 31.75f, 20.75f }, pi, structures::surface_wood },
		{ "prop_bench", { 37.75f, 26.75f }, half_pi, structures::surface_wood },
		{ "prop_bench", { 25.75f, 26.75f }, -half_pi, structures::surface_wood },
		{ "prop_bench", { 20.0f, 47.0f }, 0.0f, structures::surface_wood },
		{ "prop_bench", { 44.0f, 47.0f }, 0.0f, structures::surface_wood },
		{ "prop_phone_box", { 8.0f, 8.5f }, half_pi, structures::surface_metal },
		{ "prop_post_box", { 4.6f, 53.0f }, half_pi, structures::surface_metal },
		{ "prop_post_box", { -4.7f, -40.0f }, -half_pi, structures::surface_metal },
		{ "prop_street_sign", { -5.2f, -6.8f }, 0.0f, structures::surface_metal },
		{ "prop_street_sign", { 4.8f, 82.0f }, 0.0f, structures::surface_metal },
		{ "prop_street_sign", { -4.8f, -78.0f }, pi, structures::surface_metal },
		{ "prop_market_stall_a", { 11.5f, 21.0f }, -half_pi, structures::surface_wood },
		{ "prop_market_stall_b", { 11.5f, 25.5f }, -half_pi, structures::surface_wood },
		{ "prop_market_stall_a", { 11.5f, 30.0f }, -half_pi, structures::surface_wood },
		{ "prop_market_stall_b", { 11.5f, 34.5f }, -half_pi, structures::surface_wood },
		{ "prop_horse_trough", { 5.4f, 44.0f }, half_pi, structures::surface_rock },
		{ "prop_litter_bin", { -4.8f, 30.0f }, -half_pi, structures::surface_metal },
		{ "prop_litter_bin", { 4.8f, 62.0f }, half_pi, structures::surface_metal },
		{ "prop_litter_bin", { -4.8f, -32.0f }, -half_pi, structures::surface_metal },
		{ "prop_litter_bin", { 4.8f, -52.0f }, half_pi, structures::surface_metal },
		{ "prop_litter_bin", { 28.0f, -4.8f }, pi, structures::surface_metal },
		{ "prop_litter_bin", { 82.0f, 4.8f }, 0.0f, structures::surface_metal },
		{ "prop_litter_bin", { -38.0f, 4.8f }, 0.0f, structures::surface_metal },
		{ "prop_litter_bin", { -40.0f, -4.8f }, pi, structures::surface_metal },
		{ "prop_litter_bin", { 7.5f, 46.0f }, 0.0f, structures::surface_metal },
		{ "prop_bus_shelter", { 5.0f, 96.0f }, half_pi, structures::surface_metal },
		{ "prop_bus_shelter", { -95.0f, -5.0f }, pi, structures::surface_metal },
		{ "prop_traffic_cone", { -2.6f, -93.4f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { -1.2f, -93.8f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { 0.4f, -94.0f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { 1.9f, -96.4f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { -2.8f, -101.0f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { 0.6f, 95.5f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { -0.6f, 104.5f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { 3.0f, 105.0f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { -110.0f, -0.4f }, 0.0f, structures::surface_fabric },
		{ "prop_traffic_cone", { -110.4f, 2.0f }, 0.0f, structures::surface_fabric },
		{ "prop_wreck_hatch", { 1.4f, -84.0f }, 0.25f, structures::surface_metal }
	};
	constexpr structures::vec3_s town_barriers[] = { { -2.4f, 98.0f, 0.25f }, { 2.6f, 101.5f, -0.3f }, { -1.0f, -96.0f, 0.15f }, { 2.8f, -99.0f, -0.4f }, { -112.0f, 1.6f, 1.75f }, { -115.0f, -2.2f, 1.3f } };
	constexpr const char* surface_names[structures::surface_count] = { "concrete", "metal", "grate", "wood", "glass", "fabric", "dirt", "flesh", "water", "grass", "sand", "rock", "gravel" };
	constexpr const char* biome_names[structures::biome_count] = { "sea", "beach", "rocky shore", "dunes", "marsh", "meadow", "farmland", "broadleaf woodland", "pinewood", "coastal heath", "moorland", "summit" };
	constexpr auto biome_scatter = 7.0f;
	constexpr structures::vec3_s biome_moods[structures::biome_count] = { { 0.0f, 0.0f, 0.1f }, { 0.25f, 0.3f, 0.12f }, { 0.15f, 0.2f, 0.18f }, { 0.35f, 0.5f, 0.16f }, { 0.8f, 1.3f, 0.0f }, { 0.85f, 1.0f, 0.04f }, { 0.8f, 0.9f, 0.04f }, { 1.35f, 0.9f, -0.06f }, { 1.1f, 0.7f, -0.04f }, { 0.45f, 0.6f, 0.2f }, { 0.25f, 0.4f, 0.3f }, { 0.08f, 0.15f, 0.45f } };
	constexpr structures::biome_flora_s biome_flora[structures::biome_count] =
	{
		{ 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 0.002f, 0.004f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.004f, 0.0f },
		{ 0.0f, 0.0f, 0.05f, 0.004f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.004f },
		{ 0.0f, 0.001f, 0.002f, 0.0f, 0.002f, 0.0f, 0.0f, 0.03f, 0.002f, 0.02f },
		{ 0.02f, 0.012f, 0.002f, 0.0f, 0.004f, 0.004f, 0.0f, 0.12f, 0.01f, 0.0f },
		{ 0.006f, 0.003f, 0.006f, 0.0012f, 0.012f, 0.004f, 0.0035f, 0.03f, 0.004f, 0.006f },
		{ 0.002f, 0.001f, 0.002f, 0.0f, 0.006f, 0.006f, 0.012f, 0.02f, 0.002f, 0.002f },
		{ 0.5f, 0.012f, 0.01f, 0.001f, 0.003f, 0.02f, 0.001f, 0.3f, 0.03f, 0.002f },
		{ 0.58f, 0.02f, 0.012f, 0.002f, 0.0f, 0.012f, 0.0f, 0.18f, 0.035f, 0.004f },
		{ 0.004f, 0.006f, 0.03f, 0.004f, 0.004f, 0.004f, 0.0f, 0.08f, 0.004f, 0.16f },
		{ 0.002f, 0.004f, 0.045f, 0.008f, 0.002f, 0.002f, 0.0f, 0.05f, 0.002f, 0.05f },
		{ 0.0f, 0.002f, 0.08f, 0.02f, 0.0f, 0.0f, 0.0f, 0.01f, 0.0f, 0.0f }
	};
	constexpr structures::tree_species_s tree_species[structures::tree_kind_count] =
	{
		{ "conifer_fir", 6u, 0.0004f, 0.45f, 6.0f, 0.3f, 2.0f, 0.7f, 1.3f },
		{ "flora_pine", 3u, 0.0004f, 0.5f, 7.0f, 0.32f, 3.0f, 0.8f, 1.15f },
		{ "flora_birch", 3u, 0.0007f, 0.32f, 6.0f, 0.2f, 2.2f, 0.75f, 1.15f },
		{ "flora_oak", 3u, 0.0003f, 0.9f, 4.0f, 0.5f, 5.0f, 0.8f, 1.1f },
		{ "flora_hawthorn", 3u, 0.0005f, 0.3f, 2.5f, 0.2f, 2.4f, 0.8f, 1.2f },
		{ "flora_willow", 3u, 0.0008f, 0.7f, 3.5f, 0.4f, 4.0f, 0.8f, 1.15f }
	};
	constexpr std::float_t biome_trees[structures::biome_count][structures::tree_kind_count] =
	{
		{ 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 0.0f, 0.3f, 0.0f, 0.1f, 0.6f },
		{ 0.05f, 0.0f, 0.25f, 0.35f, 0.35f, 0.0f },
		{ 0.0f, 0.0f, 0.1f, 0.45f, 0.45f, 0.0f },
		{ 0.12f, 0.03f, 0.3f, 0.4f, 0.12f, 0.03f },
		{ 0.55f, 0.38f, 0.07f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 0.4f, 0.3f, 0.0f, 0.3f, 0.0f },
		{ 0.0f, 0.2f, 0.4f, 0.0f, 0.4f, 0.0f },
		{ 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f }
	};
	constexpr auto gorse_variants = 3u;
	constexpr auto gorse_near_distance = 35.0f;
	constexpr auto gorse_far_distance = 260.0f;
	constexpr auto gorse_shadow_distance = 60.0f;
	constexpr auto gorse_sway = 0.05f;
	constexpr auto tree_far_distance = 1100.0f;
	constexpr auto tree_crowding = 0.8f;
	constexpr auto tree_stand_cell = 16.0f;
	constexpr auto hedge_step = 2.0f;
	constexpr auto hedge_band = 0.7f;
	constexpr auto hedge_keep = 0.9f;
	constexpr auto hedge_standard = 0.015f;
	constexpr auto hedge_smallest = 0.45f;
	constexpr auto hedge_largest = 0.65f;
	constexpr auto hedge_near_distance = 16.0f;
	constexpr auto hedge_shadow_distance = 90.0f;
	constexpr auto hedge_gorse_mask = 7u;
	constexpr auto hedge_gorse_scale = 1.6f;
	constexpr std::uint32_t hedge_salt = 0x2C1B3C6Du;
	constexpr std::uint32_t layer_sounds[terrain_layer_count] = { structures::sound_step_grass, structures::sound_step_grass, structures::sound_step_grass, structures::sound_step_gravel, structures::sound_step_concrete, structures::sound_step_concrete, structures::sound_step_soft, structures::sound_step_gravel, structures::sound_step_soft, structures::sound_step_grass, structures::sound_step_grass, structures::sound_step_soft, structures::sound_step_soft, structures::sound_step_gravel, structures::sound_step_grass, structures::sound_step_gravel };
	constexpr bool layer_barren[terrain_layer_count] = { false, false, false, false, true, true, true, true, false, false, false, false, true, true, false, false };
	constexpr std::uint32_t field_kinds[8] = { structures::field_pasture, structures::field_hay, structures::field_pasture, structures::field_ploughed, structures::field_stubble, structures::field_pasture, structures::field_hay, structures::field_pasture };
	constexpr const char* loot_marker_names[5] = { "toolbox", "box", "military", "medical", "food" };
	constexpr std::uint32_t loot_marker_nodes[5] = { structures::node_toolbox, structures::node_box, structures::node_military, structures::node_medical, structures::node_box };
}

//=====================================================================================
