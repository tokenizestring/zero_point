
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class gpu_c
	{
	public:

		IDXGIFactory6* factory = nullptr;
		IDXGIAdapter1* adapter = nullptr;
		ID3D11Device1* device = nullptr;
		ID3D11DeviceContext1* context = nullptr;
		IDXGISwapChain2* swapchain = nullptr;
		HANDLE latency_waitable = nullptr;
		ID3D11Texture2D* backbuffer = nullptr;
		ID3D11RenderTargetView* backbuffer_rtv = nullptr;
		std::uint32_t width = 0u;
		std::uint32_t height = 0u;
		std::uint32_t swapchain_flags = 0u;
		bool tearing = false;
		bool vsync = true;
		char adapter_name[128] = {};
		std::uint64_t adapter_memory = 0u;

		ID3D11SamplerState* sampler_point_clamp = nullptr;
		ID3D11SamplerState* sampler_linear_clamp = nullptr;
		ID3D11SamplerState* sampler_linear_wrap = nullptr;
		ID3D11SamplerState* sampler_anisotropic_wrap = nullptr;
		ID3D11SamplerState* sampler_shadow = nullptr;

		ID3D11BlendState* blend_opaque = nullptr;
		ID3D11BlendState* blend_alpha = nullptr;
		ID3D11BlendState* blend_additive = nullptr;
		ID3D11BlendState* blend_premultiplied = nullptr;
		ID3D11BlendState* blend_reactive = nullptr;

		ID3D11RasterizerState* raster_back = nullptr;
		ID3D11RasterizerState* raster_none = nullptr;
		ID3D11RasterizerState* raster_scissor = nullptr;
		ID3D11RasterizerState* raster_shadow = nullptr;

		ID3D11DepthStencilState* depth_none = nullptr;
		ID3D11DepthStencilState* depth_read = nullptr;
		ID3D11DepthStencilState* depth_write = nullptr;
		ID3D11DepthStencilState* depth_equal = nullptr;
		ID3D11DepthStencilState* depth_shadow = nullptr;

		bool create(HWND window, std::uint32_t initial_width, std::uint32_t initial_height);
		void destroy();
		bool create_states(std::uint32_t anisotropy);
		void destroy_states();
		void resize(std::uint32_t new_width, std::uint32_t new_height);
		void wait_for_frame();
		void present();
		bool capture(const char* path);

		structures::shader_blob_s shader_bytes(const char* name);
		ID3D11VertexShader* create_vertex_shader(const char* name, const D3D11_INPUT_ELEMENT_DESC* layout, std::uint32_t layout_count, ID3D11InputLayout** out_layout);
		ID3D11PixelShader* create_pixel_shader(const char* name);
		ID3D11ComputeShader* create_compute_shader(const char* name);
		ID3D11Buffer* create_buffer(std::uint32_t size, D3D11_USAGE usage, std::uint32_t bind_flags, std::uint32_t cpu_flags, const void* data, std::uint32_t misc_flags, std::uint32_t stride);
		ID3D11Buffer* create_constant_buffer(std::uint32_t size);
		void update_buffer(ID3D11Buffer* buffer, const void* data, std::uint32_t size);

		bool create_target(structures::target_s& target, std::uint32_t target_width, std::uint32_t target_height, DXGI_FORMAT format, std::uint32_t flags);
		bool create_depth(structures::depth_target_s& target, std::uint32_t target_width, std::uint32_t target_height);
		void destroy_target(structures::target_s& target);
		void destroy_depth(structures::depth_target_s& target);
	};

	extern gpu_c gpu;
}

//=====================================================================================
