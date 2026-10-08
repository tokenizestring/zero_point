
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class post_c
	{
	public:

		structures::target_s history[2]{};
		structures::target_s bloom[bloom_levels]{};
		structures::target_s shafts[2]{};
		std::uint32_t history_index = 0u;
		bool history_valid = false;
		std::uint32_t width = 0u;
		std::uint32_t height = 0u;

		ID3D11Buffer* histogram_buffer = nullptr;
		ID3D11UnorderedAccessView* histogram_uav = nullptr;
		ID3D11Buffer* exposure_buffer = nullptr;
		ID3D11UnorderedAccessView* exposure_uav = nullptr;
		ID3D11ShaderResourceView* exposure_srv = nullptr;

		ID3D11ComputeShader* taa_cs = nullptr;
		ID3D11ComputeShader* histogram_cs = nullptr;
		ID3D11ComputeShader* average_cs = nullptr;
		ID3D11PixelShader* bloom_down_ps = nullptr;
		ID3D11PixelShader* bloom_up_ps = nullptr;
		ID3D11PixelShader* shaft_mask_ps = nullptr;
		ID3D11PixelShader* shaft_blur_ps = nullptr;
		ID3D11PixelShader* shaft_apply_ps = nullptr;

		ID3D11Buffer* taa_buffer = nullptr;
		ID3D11Buffer* exposure_constants = nullptr;
		ID3D11Buffer* bloom_buffer = nullptr;
		ID3D11Buffer* shaft_buffer = nullptr;

		std::float_t compensation = 0.0f;

		bool create();
		void destroy();
		bool resize(std::uint32_t new_width, std::uint32_t new_height);
		void destroy_targets();
		ID3D11ShaderResourceView* resolve(ID3D11ShaderResourceView* current, ID3D11ShaderResourceView* motion, ID3D11ShaderResourceView* depth_view, bool enabled);
		void expose(ID3D11ShaderResourceView* scene, std::float_t delta);
		ID3D11ShaderResourceView* bloom_chain(ID3D11ShaderResourceView* scene, ID3D11VertexShader* fullscreen);
		void light_shafts(ID3D11RenderTargetView* scene, ID3D11ShaderResourceView* depth_view, ID3D11ShaderResourceView* cloud_view, ID3D11VertexShader* fullscreen, structures::vec2_s sun, std::float_t strength);
		void fullscreen_pass(ID3D11RenderTargetView* target, std::uint32_t target_width, std::uint32_t target_height, ID3D11ShaderResourceView* source, ID3D11PixelShader* shader, ID3D11BlendState* blend);
	};

	extern post_c post_process;
}

//=====================================================================================
