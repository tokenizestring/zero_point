
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class renderer_c
	{
	public:

		structures::graphics_settings_s settings{};
		structures::camera_s camera{};
		structures::frame_constants_s frame{};
		structures::post_constants_s post{};
		structures::object_constants_s object{};
		structures::vec4_s view_planes[6]{};
		structures::vec4_s fog{};

		ID3D11Buffer* frame_buffer = nullptr;
		ID3D11Buffer* object_buffer = nullptr;
		ID3D11Buffer* post_buffer = nullptr;

		std::uint32_t output_width = 0u;
		std::uint32_t output_height = 0u;
		std::uint32_t width = 0u;
		std::uint32_t height = 0u;

		structures::target_s gbuffer[gbuffer_count]{};
		structures::depth_target_s depth{};
		structures::target_s hdr{};
		structures::target_s white{};
		structures::target_s black{};

		ID3D11VertexShader* gbuffer_vs = nullptr;
		ID3D11PixelShader* gbuffer_ps = nullptr;
		ID3D11PixelShader* gbuffer_alpha_ps = nullptr;
		ID3D11InputLayout* gbuffer_layout = nullptr;
		ID3D11VertexShader* gbuffer_skinned_vs = nullptr;
		ID3D11InputLayout* skinned_layout = nullptr;
		ID3D11Buffer* palette_buffer = nullptr;
		ID3D11ShaderResourceView* palette_view = nullptr;
		ID3D11ComputeShader* lighting_cs = nullptr;
		ID3D11VertexShader* fullscreen_vs = nullptr;
		ID3D11PixelShader* tonemap_ps = nullptr;

		structures::mesh_s world{};
		std::vector<structures::draw_range_s> world_ranges;
		std::vector<structures::draw_item_s> draws;
		std::vector<structures::skinned_draw_s> skinned_draws;
		std::vector<structures::vec4_s> palette_rows;
		std::vector<structures::light_gpu_s> static_lights;
		std::vector<structures::light_gpu_s> frame_lights;
		ID3D11Buffer* light_buffer = nullptr;
		ID3D11ShaderResourceView* light_view = nullptr;
		ID3D11ShaderResourceView* occlusion_view = nullptr;
		ID3D11ShaderResourceView* cloud_view = nullptr;

		std::uint64_t frame_index = 0u;
		std::float_t exposure = 1.0f;
		std::float_t zoom = 1.0f;
		std::float_t frame_delta = 0.016f;
		std::uint32_t debug_view = 0u;
		std::float_t time = 0.0f;
		bool camera_valid = false;

		bool create();
		void destroy();
		void default_settings(std::uint32_t preset);
		void apply_settings();
		bool resize(std::uint32_t new_width, std::uint32_t new_height);
		void destroy_targets();
		void set_world();
		void set_lights(const std::vector<structures::light_s>& lights);
		void add_light(structures::vec3_s position, std::float_t radius, structures::vec3_s color);
		void add_spot(structures::vec3_s position, std::float_t radius, structures::vec3_s color, structures::vec3_s direction, std::float_t cosine);
		structures::light_gpu_s convert_light(const structures::light_s& light);
		void begin_frame(structures::vec3_s position, std::float_t yaw, std::float_t pitch, std::float_t roll, std::float_t delta);
		void submit(const structures::mesh_s* mesh, const structures::mat4_s& world_matrix, const structures::mat4_s& previous_matrix, std::float_t material_override, std::uint32_t flags, structures::vec4_s motion = {});
		void submit_skinned(const structures::character_s* character, const structures::mat4_s& world_matrix, const structures::mat4_s& previous_matrix, const structures::mat4_s* palette, const structures::mat4_s* previous_palette, std::uint32_t flags, std::float_t pallor, std::float_t clearance = 0.0f);
		void append_palette(const structures::mat4_s* palette, std::uint32_t count);
		void draw_skinned(const structures::vec4_s* planes, std::uint32_t plane_count, bool shadow_pass, bool viewmodel_pass);
		void render(ID3D11RenderTargetView* output);
		void render_shadows();
		void render_shafts();
		void render_gbuffer();
		void render_lighting();
		void render_post(ID3D11RenderTargetView* output, ID3D11ShaderResourceView* scene, ID3D11ShaderResourceView* bloom);
		void set_object(const structures::mat4_s& world_matrix, const structures::mat4_s& previous_matrix, std::float_t material_override, std::uint32_t flags, structures::vec4_s skin = {}, structures::vec4_s motion = {});
		void draw_world(const structures::vec4_s* planes, std::uint32_t plane_count, bool alpha);
		void draw_mesh(const structures::mesh_s* mesh);
		void draw_item(const structures::draw_item_s& item, bool shadow_pass);
	};

	extern renderer_c renderer;
}

//=====================================================================================
