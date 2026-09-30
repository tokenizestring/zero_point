
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
	constexpr auto audio_echo_count = 5u;
	constexpr auto audio_echo_strength = 0.6f;
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
	constexpr auto rail_sleeper_spacing = 0.7f;
	constexpr auto rail_ballast_top = 0.26f;
	constexpr auto road_lift = 0.05f;
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
	constexpr std::float_t character_twist_shares[] = { 0.15f, 0.2f, 0.25f, 0.2f, 0.2f };
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
	constexpr auto maximum_decals = 512u;
	constexpr auto maximum_tracers = 256u;
	constexpr auto tick_rate = 60.0f;
	constexpr auto tick_interval = 1.0f / tick_rate;
	constexpr auto maximum_ticks_per_frame = 6u;
	constexpr auto default_mouse_sensitivity = 0.0021f;
	constexpr auto server_log_file_name = "zero_point_server.log";
	constexpr auto remote_character = "survivor";
	constexpr auto server_executable_name = "zero_point_server.exe";
	constexpr auto net_protocol_id = 0x314E505Au;
	constexpr auto net_protocol_version = 4u;
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
	constexpr std::uint32_t world_save_version = 7u;
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
	constexpr auto net_early_status_ticks = 1000u;
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
			profile_ssao,
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
			page_controls
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
			menu_host
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
			bool crouched;
			bool grounded;
			bool turning;
			bool hidden;
			bool alerted;
			bool dead;
			bool looted;
			bool dormant;
			bool struck;
			mat4_s world;
			mat4_s previous_world;
			std::vector<mat4_s> palette;
			std::vector<mat4_s> previous_palette;
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
			draw_flag_alpha = 8u
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
			movement_riding = 512u
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
			message_sound
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
			death_train
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
			bool title_test;
			bool wake_test;
			bool pause_test;
			bool loading_test;
			std::int32_t menu_page;
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
		{ "terrain_needles", "forest_leaves_02", { 0.62f, 0.4f, 0.42f }, 0.34f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_heath", "withered_grass", { 0.3f, 0.27f, 0.34f }, 0.5f, 1.0f, 0.05f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_moor", "withered_grass", { 0.62f, 0.56f, 0.34f }, 0.4f, 1.0f, 0.05f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_marsh", "brown_mud_02", { 0.5f, 0.56f, 0.46f }, 0.5f, 0.55f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_dune", "gravelly_sand", { 1.25f, 1.8f, 2.6f }, 0.6f, 1.0f, 0.0f, 0.0f, 0.0f, 0.5f, 0u, {} },
		{ "terrain_shingle", "ganges_river_pebbles", { 1.0f, 0.96f, 0.95f }, 0.3f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
		{ "terrain_turf", "leafy_grass", { 0.33f, 0.52f, 0.34f }, 0.62f, 1.0f, 0.05f, 0.0f, 0.0f, 0.7f, 0u, {} },
		{ "terrain_soil", "brown_mud_02", { 0.8f, 0.72f, 0.66f }, 0.75f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0u, {} },
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
		{ "Code lock", "Four digits between your door and everyone else. Wrong guesses bite.", structures::item_category_construction, 1u, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f }
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
	constexpr structures::conversion_s cook_conversions[] = { { structures::item_potato, structures::item_baked_potato }, { structures::item_corn, structures::item_roasted_corn }, { structures::item_pumpkin, structures::item_roasted_pumpkin } };

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

	constexpr const char* sound_names[structures::sound_count] = { "step_grass", "step_concrete", "step_wood", "step_soft", "step_gravel", "hit_wood", "hit_rock", "hit_metal", "hit_flesh", "hit_soft", "chop", "swing", "pickup", "container", "craft", "equip", "ui_click", "ui_open", "ui_close", "ui_error", "zombie_groan", "zombie_snarl", "ghost_moan", "player_hurt", "heartbeat", "fire", "amb_forest", "amb_crickets", "amb_drone", "amb_wind", "amb_ocean", "shot_pistol", "shot_rifle", "reload_pistol", "reload_rifle", "bolt", "shot_assault", "dry_fire", "jam", "splash", "wade", "swim", "underwater", "shot_pistol_far", "shot_rifle_far", "shot_assault_far", "amb_rain", "thunder", "tree_creak", "tree_fall", "bullet_crack", "bullet_whiz", "ricochet", "train_engine", "train_roll", "train_clack", "train_horn", "train_brake", "train_hiss" };

	constexpr std::uint32_t drone_sounds[structures::drone_count] = { structures::sound_train_engine, structures::sound_train_roll, structures::sound_count, structures::sound_count };

	constexpr XAUDIO2FX_REVERB_I3DL2_PARAMETERS acoustic_presets[structures::acoustic_count] = { XAUDIO2FX_I3DL2_PRESET_PLAIN, XAUDIO2FX_I3DL2_PRESET_FOREST, XAUDIO2FX_I3DL2_PRESET_MOUNTAINS, XAUDIO2FX_I3DL2_PRESET_CITY, XAUDIO2FX_I3DL2_PRESET_ROOM, XAUDIO2FX_I3DL2_PRESET_UNDERWATER };

	constexpr structures::weapon_definition_s weapon_definitions[structures::weapon_count] =
	{
		{},
		{ structures::item_pistol, structures::item_pistol_ammo, 2u, 0.3f, 2.6f, 0.045f, 0.012f, 0.07f, 120.0f, 0.88f, 80.0f, structures::sound_shot_pistol, structures::sound_reload_pistol, 0.0f, false, 0.02f, 0.03f, 0.0f, 0.12f, 0.0f, 0.45f, 0.9f, structures::sound_shot_pistol_far, 0.75f },
		{ structures::item_rifle, structures::item_rifle_ammo, 5u, 1.2f, 3.4f, 0.04f, 0.002f, 0.12f, 600.0f, 0.8f, 120.0f, structures::sound_shot_rifle, structures::sound_reload_rifle, 0.3f, false, 0.015f, 0.02f, 0.0f, 0.1f, 0.0f, 0.38f, 1.2f, structures::sound_shot_rifle_far, 1.25f },
		{ structures::item_hunting_bow, structures::item_wooden_arrow, 1u, 0.2f, 0.55f, 0.03f, 0.005f, 0.0f, 120.0f, 0.86f, 6.0f, structures::sound_swing, structures::sound_pickup },
		{ structures::item_assault_rifle, structures::item_rifle_ammo, 30u, 0.095f, 2.9f, 0.05f, 0.011f, 0.022f, 350.0f, 0.82f, 110.0f, structures::sound_shot_assault, structures::sound_reload_rifle, 0.0f, true, 0.01f, 0.012f, 0.35f, 0.04f, 0.0035f, 0.95f, 1.3f, structures::sound_shot_assault_far, 1.0f }
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
	constexpr structures::vec2_s south_road_points[] = { { 1180.0f, -330.0f }, { 860.0f, -330.0f }, { 600.0f, -420.0f }, { 460.0f, -560.0f }, { 300.0f, -700.0f }, { 172.0f, -844.0f }, { 60.0f, -1080.0f }, { -92.0f, -1300.0f }, { -420.0f, -1470.0f }, { -760.0f, -1500.0f }, { -1100.0f, -1480.0f } };
	constexpr structures::vec2_s east_road_points[] = { { 860.0f, -330.0f }, { 1000.0f, -150.0f }, { 1250.0f, 50.0f }, { 1440.0f, 250.0f }, { 1520.0f, 520.0f }, { 1450.0f, 860.0f }, { 1380.0f, 1120.0f }, { 1284.0f, 1232.0f }, { 1000.0f, 1420.0f }, { 650.0f, 1500.0f }, { 300.0f, 1450.0f } };
	constexpr structures::vec2_s west_road_points[] = { { 300.0f, 1450.0f }, { -100.0f, 1420.0f }, { -420.0f, 1190.0f }, { -780.0f, 1040.0f }, { -1120.0f, 950.0f }, { -1340.0f, 780.0f }, { -1470.0f, 450.0f }, { -1610.0f, 330.0f }, { -1580.0f, 0.0f }, { -1600.0f, -400.0f }, { -1520.0f, -800.0f }, { -1380.0f, -1150.0f }, { -1100.0f, -1480.0f } };
	constexpr structures::vec2_s valley_road_points[] = { { 460.0f, -300.0f }, { 520.0f, -60.0f }, { 600.0f, 200.0f }, { 740.0f, 480.0f }, { 740.0f, 580.0f } };
	constexpr structures::vec2_s quarry_road_points[] = { { 300.0f, -700.0f }, { 0.0f, -650.0f }, { -350.0f, -620.0f }, { -650.0f, -600.0f }, { -900.0f, -600.0f } };
	constexpr structures::world_route_s world_routes[] =
	{
		{ railway_points, static_cast<std::uint32_t>(std::size(railway_points)), structures::route_rail, 5.2f, 0.025f, 100.0f, 0.65f, true },
		{ south_road_points, static_cast<std::uint32_t>(std::size(south_road_points)), structures::route_road, 6.4f, 0.1f, 20.0f, 0.5f, false },
		{ east_road_points, static_cast<std::uint32_t>(std::size(east_road_points)), structures::route_road, 6.4f, 0.1f, 20.0f, 0.5f, false },
		{ west_road_points, static_cast<std::uint32_t>(std::size(west_road_points)), structures::route_road, 6.4f, 0.1f, 20.0f, 0.5f, false },
		{ valley_road_points, static_cast<std::uint32_t>(std::size(valley_road_points)), structures::route_road, 5.6f, 0.1f, 20.0f, 0.5f, false },
		{ quarry_road_points, static_cast<std::uint32_t>(std::size(quarry_road_points)), structures::route_road, 5.6f, 0.1f, 20.0f, 0.5f, false }
	};
	constexpr structures::train_vehicle_s train_vehicles[structures::train_vehicle_count] =
	{
		{ "train_locomotive", 8.0f, 3.2f, 3.5f, 2.5f, 1.25f, structures::material_metal_green },
		{ "train_wagon_flat", 6.5f, 3.6f, 1.35f, 2.4f, 1.2f, structures::material_metal_rust },
		{ "train_wagon_open", 6.5f, 3.6f, 2.3f, 2.4f, 1.2f, structures::material_metal_rust },
		{ "train_wagon_box", 6.5f, 3.6f, 3.4f, 2.5f, 1.2f, structures::material_container_red },
		{ "train_coach", 12.0f, 8.0f, 3.5f, 2.6f, 1.2f, structures::material_container_blue }
	};
	constexpr std::uint32_t train_consist[] = { structures::train_vehicle_locomotive, structures::train_vehicle_flat, structures::train_vehicle_open, structures::train_vehicle_box, structures::train_vehicle_coach };
	constexpr std::uint32_t train_stops[] = { structures::landmark_halt, structures::landmark_harbour, structures::landmark_ouen, structures::landmark_battery, structures::landmark_portelet };
	constexpr auto train_acceleration = 0.5f;
	constexpr auto train_cruise = 13.0f;
	constexpr auto train_dwell = 30.0f;
	constexpr auto train_coupling = 0.4f;
	constexpr auto train_wheel_radius = 0.48f;
	constexpr auto train_view_distance = 1500.0f;
	constexpr auto train_detail_distance = 170.0f;
	constexpr auto train_shadow_distance = 230.0f;
	constexpr auto train_joint_spacing = 18.0f;
	constexpr auto train_axle_spacing = 1.8f;
	constexpr auto train_clack_range = 45.0f;
	constexpr auto train_engine_reference = 16.0f;
	constexpr auto train_roll_reference = 9.0f;
	constexpr auto train_horn_reference = 70.0f;
	constexpr auto train_brake_reference = 12.0f;
	constexpr auto train_horn_lead = 2.5f;
	constexpr auto train_horn_approach = 24.0f;
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

	constexpr const char* death_texts[9] = { "a bad fall", "the void", "drowning", "a gunshot", "starvation", "a beating", "giving up", "the cold", "the train" };
	constexpr const char* death_lines[9] = { "The fall broke you.", "The island swallowed you.", "The sea took your last breath.", "A bullet found you.", "Hunger finished what the island started.", "You were beaten into the dirt.", "You gave up.", "The cold got into your bones.", "The train did not stop for you." };

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

	constexpr const char* profile_names[structures::profile_count] = { "c0 ground", "c0 foliage", "c1 ground", "c1 foliage", "c2 ground", "c2 foliage", "c3 ground", "c3 foliage", "world", "terrain", "foliage", "grass", "models", "ssao", "lighting", "effects", "post" };

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
		{ L"IM FELL English SC", FW_NORMAL }
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

	constexpr auto paper_size = 512u;
	constexpr auto ui_ink = functions::rgba(36u, 27u, 20u, 238u);
	constexpr auto ui_faded = functions::rgba(36u, 27u, 20u, 150u);
	constexpr auto ui_red = functions::rgba(138u, 30u, 18u, 240u);
	constexpr auto ui_blue = functions::rgba(34u, 68u, 100u, 235u);
	constexpr auto ui_ochre = functions::rgba(146u, 98u, 26u, 238u);
	constexpr auto ui_cream = functions::rgba(238u, 228u, 206u, 240u);
	constexpr auto ui_paper = functions::rgba(255u, 255u, 255u, 244u);
	constexpr const char* ui_vital_labels[4] = { "Health", "Water", "Food", "Breath" };

	constexpr auto page_width = 1280u;
	constexpr auto page_height = 900u;
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
	constexpr auto ui_cream_bright = functions::rgba(250u, 243u, 226u, 255u);
	constexpr auto ui_shade = functions::rgba(10u, 8u, 6u, 215u);

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

	constexpr structures::menu_entry_s title_entries[] = { { "Play", structures::menu_play }, { "Field notes", structures::menu_notes }, { "Settings", structures::menu_settings }, { "Leave the island", structures::menu_quit } };
	constexpr structures::menu_entry_s pause_entries[] = { { "Resume", structures::menu_resume }, { "Field notes", structures::menu_notes }, { "Settings", structures::menu_settings }, { "Leave the server", structures::menu_title }, { "Leave the island", structures::menu_quit } };
	constexpr const char* quality_names[] = { "Low", "Medium", "High", "Ultra" };

	constexpr const char* notes_controls[][2] =
	{
		{ "W A S D", "walk" },
		{ "Shift", "run" },
		{ "Space", "jump" },
		{ "Ctrl or C", "crouch" },
		{ "Left mouse", "swing, fire, plant, eat" },
		{ "Right mouse", "aim down the sights" },
		{ "Hold left mouse", "draw the bow" },
		{ "R", "reload, turn a piece" },
		{ "E", "pick up, open, drink, harvest" },
		{ "1 to 6, wheel", "choose from the belt" },
		{ "Tab", "open the journal" },
		{ "M", "unfold the map" },
		{ "Esc", "pause" }
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

	constexpr structures::user_settings_s default_user_settings{ structures::quality_high, 1.0f, 95.0f, 1.0f, 0.85f, 1.0f, 1.0f, 1.0f, true, true, false, false, { 'W', 'S', 'A', 'D', VK_SPACE, VK_CONTROL, VK_SHIFT, VK_MENU, 'E', 'R', 'R', VK_TAB, 'M', 'T', 'F', 'G', 'V' } };
	constexpr const char* bind_names[structures::bind_count] = { "Move forward", "Move back", "Move left", "Move right", "Jump", "Crouch", "Sprint", "Walk", "Use", "Reload", "Rotate or next piece", "Inventory", "Map", "Chat", "Melee", "Throw", "Visor" };
	constexpr const char* compass_points[8] = { "N", "NE", "E", "SE", "S", "SW", "W", "NW" };
	constexpr const char* marker_prefixes[4] = { "col_", "ramp_", "loot_", "light_" };
	constexpr const char* village_models[8] = { "bld_cottage", "bld_house", "bld_cottage", "bld_ruin", "bld_house", "bld_barn", "bld_cottage", "bld_shed" };
	constexpr const char* farm_models[3] = { "bld_house", "bld_barn", "bld_shed" };
	constexpr const char* hamlet_models[4] = { "bld_cottage", "bld_shed", "bld_ruin", "bld_cottage" };
	constexpr const char* outlier_models[2] = { "bld_shed", "bld_ruin" };
	constexpr const char* surface_names[structures::surface_count] = { "concrete", "metal", "grate", "wood", "glass", "fabric", "dirt", "flesh", "water", "grass", "sand", "rock", "gravel" };
	constexpr const char* biome_names[structures::biome_count] = { "sea", "beach", "rocky shore", "dunes", "marsh", "meadow", "farmland", "broadleaf woodland", "pinewood", "coastal heath", "moorland", "summit" };
	constexpr auto biome_scatter = 7.0f;
	constexpr structures::biome_flora_s biome_flora[structures::biome_count] =
	{
		{ 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 0.002f, 0.004f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.004f },
		{ 0.0f, 0.0f, 0.05f, 0.004f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f },
		{ 0.0f, 0.001f, 0.002f, 0.0f, 0.002f, 0.0f, 0.0f, 0.03f, 0.002f },
		{ 0.02f, 0.012f, 0.002f, 0.0f, 0.004f, 0.004f, 0.0f, 0.12f, 0.01f },
		{ 0.006f, 0.003f, 0.006f, 0.0012f, 0.012f, 0.004f, 0.0035f, 0.03f, 0.004f },
		{ 0.002f, 0.001f, 0.002f, 0.0f, 0.006f, 0.006f, 0.012f, 0.02f, 0.002f },
		{ 0.5f, 0.012f, 0.01f, 0.001f, 0.003f, 0.02f, 0.001f, 0.3f, 0.03f },
		{ 0.58f, 0.02f, 0.012f, 0.002f, 0.0f, 0.012f, 0.0f, 0.18f, 0.035f },
		{ 0.004f, 0.006f, 0.03f, 0.004f, 0.004f, 0.004f, 0.0f, 0.08f, 0.004f },
		{ 0.002f, 0.004f, 0.045f, 0.008f, 0.002f, 0.002f, 0.0f, 0.05f, 0.002f },
		{ 0.0f, 0.002f, 0.08f, 0.02f, 0.0f, 0.0f, 0.0f, 0.01f, 0.0f }
	};
	constexpr std::uint32_t layer_sounds[terrain_layer_count] = { structures::sound_step_grass, structures::sound_step_grass, structures::sound_step_grass, structures::sound_step_gravel, structures::sound_step_concrete, structures::sound_step_concrete, structures::sound_step_soft, structures::sound_step_gravel, structures::sound_step_soft, structures::sound_step_grass, structures::sound_step_grass, structures::sound_step_soft, structures::sound_step_soft, structures::sound_step_gravel, structures::sound_step_grass, structures::sound_step_gravel };
	constexpr bool layer_barren[terrain_layer_count] = { false, false, false, false, true, true, true, true, false, false, false, false, true, true, false, false };
	constexpr std::uint32_t field_kinds[8] = { structures::field_pasture, structures::field_hay, structures::field_pasture, structures::field_ploughed, structures::field_stubble, structures::field_pasture, structures::field_hay, structures::field_pasture };
	constexpr const char* loot_marker_names[5] = { "toolbox", "box", "military", "medical", "food" };
	constexpr std::uint32_t loot_marker_nodes[5] = { structures::node_toolbox, structures::node_box, structures::node_military, structures::node_medical, structures::node_box };
}

//=====================================================================================
