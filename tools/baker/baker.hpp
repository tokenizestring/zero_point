
//=====================================================================================

#pragma once

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	namespace baker
	{
		constexpr auto procedural_size = material_texture_size;
		constexpr auto sun_search_radius = 0.045f;
		constexpr auto sun_threshold_fraction = 0.08f;
		constexpr auto simplify_error_fraction = 0.002f;
		constexpr auto simplify_minimum_error = 0.0012f;
		constexpr auto simplify_relaxed_error = 3.0f;
		constexpr auto simplify_budget_per_meter = 2500.0f;
		constexpr auto simplify_budget_minimum = 1500.0f;
		constexpr auto simplify_budget_maximum = 24000.0f;
		constexpr auto simplify_flip_limit = 0.3f;
		constexpr auto simplify_lod_error = 60.0;

		struct lod_model_s
		{
			const char* name;
			std::uint32_t near_budget;
			std::uint32_t far_budget;
		};

		constexpr lod_model_s lod_models[] =
		{
			{ "rock_moss_set_01", 12000u, 2500u },
			{ "rock_moss_set_02", 12000u, 2500u },
			{ "tree_dead_0", 8000u, 1200u },
			{ "tree_dead_1", 8000u, 1200u },
			{ "tree_dead_2", 8000u, 1200u }
		};
		constexpr auto terrain_seed = 20260928u;
		constexpr auto terrain_cache_version = 5u;
		constexpr auto bluff_guard = 210.0f;
		constexpr auto bluff_retreat = 170.0f;
		constexpr auto bluff_northern = 110.0f;
		constexpr auto bluff_face = 9.0f;
		constexpr auto terrain_erosion_size = 2305u;
		constexpr auto terrain_erosion_cell = 2.0f;
		constexpr auto terrain_erosion_droplets = 1920000u;
		constexpr auto terrain_erosion_steps = 64u;
		constexpr auto terrain_erosion_radius = 4;
		constexpr auto terrain_height_scale = 200.0f;
		constexpr auto terrain_sea_floor = -36.0f;
		constexpr auto terrain_ao_directions = 16u;
		constexpr auto terrain_ao_steps = 18u;

		constexpr auto route_spacing = 2.0f;
		constexpr auto route_passes = 6u;
		constexpr auto route_floor = 2.5f;
		constexpr auto route_shoulder = 30.0f;
		constexpr auto route_paint_band = 1.6f;
		constexpr auto biome_relief_radius = 12;
		constexpr auto biome_wind_steps = 20u;
		constexpr auto biome_wind_stride = 40.0f;
		constexpr auto biome_warp = 9.0f;
		constexpr auto biome_farm_reach = 460.0f;
		constexpr structures::vec2_s biome_upwind{ -0.94f, -0.34f };
		constexpr structures::vec3_s layer_colors[terrain_layer_count] = { { 0.28f, 0.42f, 0.16f }, { 0.52f, 0.5f, 0.28f }, { 0.24f, 0.2f, 0.12f }, { 0.4f, 0.3f, 0.2f }, { 0.45f, 0.44f, 0.42f }, { 0.36f, 0.35f, 0.34f }, { 0.86f, 0.78f, 0.58f }, { 0.55f, 0.52f, 0.48f }, { 0.3f, 0.19f, 0.11f }, { 0.36f, 0.24f, 0.34f }, { 0.55f, 0.47f, 0.24f }, { 0.16f, 0.2f, 0.13f }, { 0.92f, 0.86f, 0.68f }, { 0.62f, 0.58f, 0.56f }, { 0.34f, 0.5f, 0.2f }, { 0.3f, 0.21f, 0.15f } };
		constexpr structures::vec3_s biome_colors[structures::biome_count] = { { 0.05f, 0.18f, 0.3f }, { 0.9f, 0.84f, 0.62f }, { 0.45f, 0.45f, 0.48f }, { 0.95f, 0.9f, 0.45f }, { 0.1f, 0.45f, 0.5f }, { 0.45f, 0.75f, 0.25f }, { 0.85f, 0.65f, 0.2f }, { 0.1f, 0.5f, 0.12f }, { 0.02f, 0.28f, 0.2f }, { 0.65f, 0.3f, 0.65f }, { 0.6f, 0.45f, 0.25f }, { 0.85f, 0.85f, 0.9f } };
		constexpr std::uint32_t farm_sites[] = { structures::landmark_town, structures::landmark_ouen, structures::landmark_portelet, structures::landmark_rozel, structures::landmark_landes, structures::landmark_trinity, structures::landmark_halt };
		constexpr auto clip_offset_tolerance = 0.001f;
		constexpr const char* clip_retarget_prefixes[] = { "m_", "f_" };
		constexpr std::uint32_t bc7_weights[16] = { 0u, 4u, 9u, 13u, 17u, 21u, 26u, 30u, 34u, 38u, 43u, 47u, 51u, 55u, 60u, 64u };

		constexpr const char* scanned_sets[] =
		{
			"hangar_concrete_floor",
			"concrete_floor_worn_001",
			"anti_slip_concrete",
			"painted_concrete_02",
			"asphalt_03",
			"metal_plate",
			"garage_floor",
			"interior_tiles",
			"concrete_slab_wall_02",
			"ribbed_concrete_wall",
			"concrete_wall_006",
			"concrete_tile_facade",
			"rough_concrete",
			"blue_metal_plate",
			"green_metal_rust",
			"rusty_metal_02",
			"corrugated_iron_02",
			"painted_metal_shutter",
			"container_side",
			"metal_plate_02",
			"plywood",
			"hessian_230",
			"leafy_grass",
			"withered_grass",
			"forest_leaves_02",
			"brown_mud_02",
			"rocks_ground_05",
			"mossy_rock",
			"gravelly_sand",
			"ganges_river_pebbles"
		};

		constexpr const char* detailed_models[] =
		{
			"pipe_pistol",
			"scrap_rifle",
			"scrap_ar",
			"deployables",
			"structures"
		};

		constexpr const char* detailed_prefixes[] =
		{
			"conifer_",
			"grass_",
			"tree_dead_",
			"bld_",
			"rail_",
			"train_",
			"fauna_"
		};

		constexpr const char* neutralized_sets[] =
		{
			"blue_metal_plate",
			"green_metal_rust"
		};

		constexpr const char* ambientcg_sets[] =
		{
			"DiamondPlate008A",
			"CorrugatedSteel005",
			"Metal027",
			"Rubber004",
			"SheetMetal002"
		};

		constexpr const char* procedural_sets[] =
		{
			"polymer",
			"anodized",
			"steel",
			"carbon",
			"rubber",
			"fabric",
			"nylon",
			"skin",
			"flesh",
			"panel",
			"hexgrid",
			"glass",
			"knurled",
			"painted_steel"
		};

		constexpr const char* sky_sources[] =
		{
			"qwantani_late_afternoon_puresky",
			"table_mountain_2_puresky",
			"kloppenheim_07_puresky",
			"kloofendal_overcast_puresky"
		};

		struct image_s
		{
			std::uint32_t width;
			std::uint32_t height;
			std::vector<structures::vec4_s> pixels;
		};

		struct material_source_s
		{
			std::uint32_t size;
			std::float_t aspect;
			std::vector<std::float_t> alpha;
			std::vector<structures::vec3_s> albedo;
			std::vector<structures::vec3_s> normal;
			std::vector<std::float_t> roughness;
			std::vector<std::float_t> occlusion;
			std::vector<std::float_t> height;
			std::vector<std::float_t> metal;
		};

		enum material_origin_e : std::uint32_t
		{
			material_origin_scanned,
			material_origin_ambientcg,
			material_origin_procedural
		};

		struct material_job_s
		{
			std::string name;
			std::string source;
			std::uint32_t origin;
			bool neutralize;
		};

		struct material_output_s
		{
			structures::material_record_s record;
			std::vector<std::uint8_t> albedo;
			std::vector<std::uint8_t> normal;
			std::vector<std::uint8_t> rough_ao;
			std::vector<std::uint8_t> height_metal;
			bool valid;
		};

		struct pak_item_s
		{
			structures::pak_entry_s entry;
			std::vector<std::uint8_t> data;
		};

		struct voronoi_s
		{
			std::float_t f1;
			std::float_t f2;
			std::uint32_t cell;
		};

		enum json_type_e : std::uint32_t
		{
			json_null,
			json_boolean,
			json_number,
			json_string,
			json_array,
			json_object
		};

		struct json_s
		{
			std::uint32_t type;
			std::double_t number;
			std::string text;
			std::vector<json_s> items;
			std::vector<std::string> keys;

			const json_s& get(const char* key) const;
			const json_s& at(std::size_t index) const;
			std::double_t value(std::double_t fallback) const;
			bool has(const char* key) const;
		};

		struct model_texture_job_s
		{
			std::string set_name;
			std::string albedo;
			std::string normal;
			std::string rough_metal;
			std::string occlusion;
			std::string emissive;
			std::string alpha_mask;
			structures::vec4_s base_factor;
			std::float_t roughness_factor;
			std::float_t metal_factor;
			bool alpha;
		};

		struct model_vertex_s
		{
			structures::vec3_s position;
			structures::vec3_s normal;
			structures::vec2_s uv;
			std::uint32_t material;
		};

		struct clip_sampler_s
		{
			std::vector<std::float_t> times;
			std::vector<std::float_t> values;
			std::uint32_t components;
			bool cubic;
			bool step;
		};

		struct quadric_s
		{
			std::double_t xx;
			std::double_t xy;
			std::double_t xz;
			std::double_t xw;
			std::double_t yy;
			std::double_t yz;
			std::double_t yw;
			std::double_t zz;
			std::double_t zw;
			std::double_t ww;
			std::double_t area;
		};

		struct collapse_s
		{
			std::double_t cost;
			std::uint32_t from;
			std::uint32_t to;
			std::uint32_t stamp;
		};
	}

	class baker_simplifier_c
	{
	public:

		std::vector<baker::quadric_s> quadrics;
		std::vector<std::vector<std::uint32_t>> fans;
		std::vector<std::uint32_t> stamps;
		std::vector<std::uint8_t> locked;
		std::vector<std::uint8_t> alive;
		std::vector<std::double_t> limits;
		std::vector<std::uint32_t> triangles;
		std::vector<std::uint32_t> ring_from;
		std::vector<std::uint32_t> ring_to;
		std::vector<std::uint32_t> ring_update;
		std::vector<baker::collapse_s> heap;
		std::uint32_t alive_count = 0u;

		std::uint32_t simplify(std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts);
		std::uint32_t reduce(std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts, std::uint32_t budget);
		void setup(const std::vector<baker::model_vertex_s>& vertices, const std::vector<std::uint32_t>& indices, const std::vector<structures::model_part_s>& parts);
		void run(const std::vector<baker::model_vertex_s>& vertices, std::double_t limit_scale, std::uint32_t budget);
		bool best(const std::vector<baker::model_vertex_s>& vertices, std::uint32_t from, baker::collapse_s& out);
		bool valid(const std::vector<baker::model_vertex_s>& vertices, std::uint32_t from, std::uint32_t to);
		void collapse(std::uint32_t from, std::uint32_t to);
		void gather(std::uint32_t vertex, std::vector<std::uint32_t>& ring);
		void push(baker::collapse_s entry);
		baker::quadric_s combine(const baker::quadric_s& a, const baker::quadric_s& b);
		std::double_t evaluate(const baker::quadric_s& quadric, structures::vec3_s point);
		void rebuild(std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts);
	};

	class baker_json_c
	{
	public:

		const char* cursor = nullptr;
		const char* end = nullptr;

		bool parse(const std::string& text, baker::json_s& out);
		void skip();
		bool value(baker::json_s& out);
		bool string(std::string& out);
	};

	class baker_models_c
	{
	public:

		std::vector<baker::pak_item_s> items;
		std::vector<baker::model_texture_job_s> jobs_list;

		bool bake(const char* assets_directory);
		bool open(const std::string& directory, const std::string& file, baker::json_s& document, std::vector<std::vector<std::uint8_t>>& buffers);
		std::string decode_uri(const std::string& uri);
		void collect_materials(const baker::json_s& document, const std::string& directory, const std::string& name, std::vector<structures::model_material_s>& model_materials);
		void tangents(const std::vector<baker::model_vertex_s>& vertices, const std::vector<std::uint32_t>& indices, std::vector<structures::vec4_s>& out);
		void append(baker::pak_item_s& item, const void* data, std::size_t size);
		void write_model(const std::string& name, const std::vector<baker::model_vertex_s>& vertices, const std::vector<std::uint32_t>& indices, const std::vector<structures::model_part_s>& parts, const std::vector<structures::model_material_s>& model_materials);
		bool import(const std::string& directory, const std::string& file, const std::string& name);
		void visit(const baker::json_s& document, const std::vector<std::vector<std::uint8_t>>& buffers, std::uint32_t node_index, const std::array<std::double_t, 16>& parent, const std::string& name, std::vector<baker::model_vertex_s>& vertices, std::vector<std::uint32_t>& indices, std::vector<structures::model_part_s>& parts);
		std::string canonical(const std::string& path);
		const std::uint8_t* accessor(const baker::json_s& document, const std::vector<std::vector<std::uint8_t>>& buffers, std::uint32_t index, std::uint32_t& count, std::uint32_t& stride, std::uint32_t& component);
		void bake_materials(std::vector<baker::material_output_s>& outputs);
		bool load_channel(const std::string& path, baker::image_s& out);
	};

	class baker_characters_c
	{
	public:

		std::vector<baker::pak_item_s> items;

		bool bake(const char* assets_directory);
		bool import_character(const std::string& directory, const std::string& file, const std::string& name);
		bool import_clip(const std::string& directory, const std::string& file, const std::string& name);
		void node_transform(const baker::json_s& node, structures::vec3_s& translation, structures::quat_s& rotation, structures::vec3_s& scale);
		structures::mat4_s convert_matrix(const std::float_t* column_major);
		std::vector<std::float_t> read_floats(const baker::json_s& document, const std::vector<std::vector<std::uint8_t>>& buffers, std::uint32_t accessor_index, std::uint32_t& count, std::uint32_t& components);
		structures::vec4_s sample(const baker::clip_sampler_s& sampler, std::float_t time);
	};

	class baker_terrain_c
	{
	public:

		std::vector<std::float_t> coarse;
		std::vector<std::float_t> coarse_flow;
		std::vector<std::float_t> heights;
		std::vector<std::float_t> flow;
		std::vector<structures::vec3_s> normals;
		std::vector<std::float_t> occlusion;
		std::vector<std::float_t> route_near;
		std::vector<std::uint8_t> route_kind;
		std::vector<structures::route_path_s> routes;
		std::vector<std::uint8_t> biomes;
		std::vector<std::uint8_t> shading;
		std::vector<std::uint8_t> splats[terrain_splat_count];
		std::vector<std::uint8_t> ground;
		std::vector<std::uint8_t> control;
		std::vector<baker::pak_item_s> items;

		bool bake(const std::string& cache_path, const std::string& preview_path, bool use_cache);
		void classify();
		void blend(std::float_t x, std::float_t z, std::float_t* weights);
		void add_compressed(const char* name, std::uint32_t size, const std::vector<std::uint8_t>& base);
		void add_blob(const char* name, const std::vector<std::uint8_t>& bytes);
		void preview_biomes(const std::string& path);
		void grade();
		void route_path(const structures::world_route_s& route, std::vector<structures::vec2_s>& path);
		void write_routes();
		bool load_cache(const std::string& path);
		void save_cache(const std::string& path);
		void shape();
		std::float_t elevation(std::float_t x, std::float_t z);
		std::float_t clearance(std::float_t x, std::float_t z);
		void erode();
		void refine();
		void settle();
		void shade();
		void paint();
		void water_normals();
		void add_texture(const char* name, DXGI_FORMAT format, std::uint32_t size, const std::vector<std::uint8_t>& base, bool mips);
		void preview(const std::string& path);
		std::float_t height_at(std::float_t x, std::float_t z);
		std::float_t noise(std::float_t x, std::float_t z, std::uint32_t seed);
		std::float_t fbm(std::float_t x, std::float_t z, std::uint32_t octaves, std::uint32_t seed);
		std::float_t ridged(std::float_t x, std::float_t z, std::uint32_t octaves, std::uint32_t seed);
		std::float_t bilinear(const std::vector<std::float_t>& grid, std::uint32_t size, std::float_t x, std::float_t z);
		std::float_t bicubic(const std::vector<std::float_t>& grid, std::uint32_t size, std::float_t x, std::float_t z);
	};

	class baker_images_c
	{
	public:

		IWICImagingFactory* factory = nullptr;

		bool initialize();
		void shutdown();
		bool load(const char* path, baker::image_s& out);
		bool save_png(const char* path, const std::uint8_t* rgba, std::uint32_t width, std::uint32_t height, std::vector<std::uint8_t>* memory);
		void downsample(const baker::image_s& source, baker::image_s& out);
		void resample_axis(const baker::image_s& source, baker::image_s& out, std::uint32_t target, bool horizontal);
		void resize(baker::image_s& image, std::uint32_t width, std::uint32_t height);

		std::float_t srgb_to_linear(std::float_t v);
		std::float_t linear_to_srgb(std::float_t v);
		std::float_t hash(std::int32_t x, std::int32_t y, std::uint32_t seed);
		std::float_t value_noise(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t seed);
		std::float_t gradient_noise(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t seed);
		std::float_t fbm(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t octaves, std::float_t gain, std::uint32_t seed);
		std::float_t ridged(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t octaves, std::uint32_t seed);
		baker::voronoi_s voronoi(std::float_t x, std::float_t y, std::int32_t period, std::uint32_t seed);
	};

	class baker_compressor_c
	{
	public:

		void bc4_block(const std::uint8_t* values, std::uint32_t stride, std::uint8_t* out);
		void bc7_block(const std::uint8_t* rgba, std::uint8_t* out);
		std::uint32_t bc7_quantize(const std::float_t* endpoint, std::uint8_t* out);
		std::uint64_t bc7_indices(const std::uint8_t* rgba, const std::uint8_t* e0, const std::uint8_t* e1, std::uint8_t* indices);
		void bc7_pack(const std::uint8_t* e0, const std::uint8_t* e1, std::uint32_t p0, std::uint32_t p1, const std::uint8_t* indices, std::uint8_t* out);
		void compress_bc7(const std::uint8_t* rgba, std::uint32_t width, std::uint32_t height, std::vector<std::uint8_t>& out);
		void compress_bc5(const std::uint8_t* rg, std::uint32_t width, std::uint32_t height, std::vector<std::uint8_t>& out);
	};

	class baker_materials_c
	{
	public:

		std::vector<baker::material_output_s> outputs;

		bool bake(const char* assets_directory);
		bool load_scanned(const char* assets_directory, const char* name, baker::material_source_s& source);
		bool load_ambientcg(const char* assets_directory, const char* name, baker::material_source_s& source);
		void neutralize(baker::material_source_s& source);
		void generate(const char* name, baker::material_source_s& source);
		void normals_from_height(baker::material_source_s& source, std::float_t strength);
		void finish(const char* name, bool procedural, baker::material_source_s& source, baker::material_output_s& output);
		std::float_t coverage(const std::vector<std::float_t>& alpha, std::size_t count, std::float_t scale);
		void append_items(std::vector<baker::pak_item_s>& items);
	};

	class baker_skies_c
	{
	public:

		std::vector<baker::pak_item_s> items;
		std::vector<structures::sky_record_s> records;

		bool bake(const char* assets_directory);
		bool decode_hdr(const char* path, baker::image_s& out);
		structures::vec3_s direction(std::float_t u, std::float_t v);
		void extract_sun(baker::image_s& image, structures::sky_record_s& record);
		void project_sh(const baker::image_s& image, structures::sky_record_s& record);
		std::uint32_t pack_rgb9e5(structures::vec3_s color);
	};

	class baker_audio_c
	{
	public:

		std::vector<baker::pak_item_s> items;

		bool bake(const char* assets_directory);
		bool read_wave(const std::string& path, const std::string& name);
	};

	class baker_glyphs_c
	{
	public:

		structures::font_metrics_s fonts[structures::font_count]{};
		std::vector<std::uint8_t> atlas;
		std::vector<std::uint8_t> bitmap;
		std::vector<std::float_t> field_outside;
		std::vector<std::float_t> field_inside;
		std::vector<std::float_t> edt_f;
		std::vector<std::float_t> edt_d;
		std::vector<std::float_t> edt_z;
		std::vector<std::int32_t> edt_v;
		std::int32_t cursor_x = font_padding;
		std::int32_t cursor_y = font_padding;
		std::int32_t row_height = 0;

		bool bake(const char* assets_directory);
		void bake_glyph(HDC dc, structures::font_metrics_s& metrics, std::uint32_t code);
		void distance_field(std::vector<std::float_t>& grid, std::int32_t grid_width, std::int32_t grid_height);
		void distance_line(std::int32_t count);
		void append_items(std::vector<baker::pak_item_s>& items);
	};

	class baker_icon_c
	{
	public:

		bool bake(const char* output_path);
		void render(std::uint32_t size, std::vector<std::uint8_t>& rgba);
	};

	class baker_item_icons_c
	{
	public:

		std::vector<std::uint8_t> atlas;
		std::vector<std::uint8_t> present;

		bool bake(const char* assets_directory);
		std::string key(const char* name);
		void append_items(std::vector<baker::pak_item_s>& items);
	};

	class baker_c
	{
	public:

		std::vector<baker::pak_item_s> items;

		std::int32_t run(std::int32_t count, char** arguments);
		std::uint64_t stamp(const char* assets_directory);
		bool up_to_date(const char* pak_path, std::uint64_t expected);
		bool write(const char* pak_path, std::uint64_t pak_stamp);
	};

	extern baker_simplifier_c baker_simplifier;
	extern baker_characters_c baker_characters;
	extern baker_terrain_c baker_terrain;
	extern baker_models_c baker_models;
	extern baker_images_c baker_images;
	extern baker_compressor_c baker_compressor;
	extern baker_materials_c baker_materials;
	extern baker_skies_c baker_skies;
	extern baker_audio_c baker_audio;
	extern baker_glyphs_c baker_glyphs;
	extern baker_icon_c baker_icon;
	extern baker_item_icons_c baker_item_icons;
	extern baker_c baker_main;
}

//=====================================================================================
