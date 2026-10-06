
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	gpu_c gpu;

	bool gpu_c::create(HWND window, std::uint32_t initial_width, std::uint32_t initial_height)
	{
		if (SUCCEEDED(CreateDXGIFactory2(0u, IID_PPV_ARGS(&factory))))
		{
			if (SUCCEEDED(factory->EnumAdapterByGpuPreference(0u, DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE, IID_PPV_ARGS(&adapter))) || SUCCEEDED(factory->EnumAdapters1(0u, &adapter)))
			{
				DXGI_ADAPTER_DESC1 description{};

				adapter->GetDesc1(&description);

				WideCharToMultiByte(CP_UTF8, 0u, description.Description, -1, adapter_name, sizeof(adapter_name), nullptr, nullptr);

				adapter_memory = description.DedicatedVideoMemory;
			}

			BOOL allow_tearing{ FALSE };

			tearing = SUCCEEDED(factory->CheckFeatureSupport(DXGI_FEATURE_PRESENT_ALLOW_TEARING, &allow_tearing, sizeof(allow_tearing))) && allow_tearing;

			const D3D_FEATURE_LEVEL levels[] = { D3D_FEATURE_LEVEL_11_1, D3D_FEATURE_LEVEL_11_0 };

			ID3D11Device* base_device{ nullptr };
			ID3D11DeviceContext* base_context{ nullptr };

			auto flags{ 0u };

#ifdef ZP_DEBUG
			flags |= D3D11_CREATE_DEVICE_DEBUG;
#endif

			auto result{ D3D11CreateDevice(adapter, adapter ? D3D_DRIVER_TYPE_UNKNOWN : D3D_DRIVER_TYPE_HARDWARE, nullptr, flags, levels, 2u, D3D11_SDK_VERSION, &base_device, nullptr, &base_context) };

			if (FAILED(result) && flags)
			{
				result = D3D11CreateDevice(adapter, adapter ? D3D_DRIVER_TYPE_UNKNOWN : D3D_DRIVER_TYPE_HARDWARE, nullptr, 0u, levels, 2u, D3D11_SDK_VERSION, &base_device, nullptr, &base_context);
			}

			if (SUCCEEDED(result))
			{
				base_device->QueryInterface(IID_PPV_ARGS(&device));
				base_context->QueryInterface(IID_PPV_ARGS(&context));

				functions::release(base_device);
				functions::release(base_context);

				logger.write("gpu: %s (%llu MB), tearing %s", adapter_name, adapter_memory / (1024ull * 1024ull), tearing ? "yes" : "no");

				if (device && context && window)
				{
					DXGI_SWAP_CHAIN_DESC1 chain{};

					swapchain_flags = DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT | (tearing ? DXGI_SWAP_CHAIN_FLAG_ALLOW_TEARING : 0u);

					chain.Width = initial_width;
					chain.Height = initial_height;
					chain.Format = swapchain_format;
					chain.SampleDesc.Count = 1u;
					chain.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
					chain.BufferCount = swapchain_buffer_count;
					chain.Scaling = DXGI_SCALING_STRETCH;
					chain.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
					chain.AlphaMode = DXGI_ALPHA_MODE_IGNORE;
					chain.Flags = swapchain_flags;

					IDXGISwapChain1* base_swapchain{ nullptr };

					if (SUCCEEDED(factory->CreateSwapChainForHwnd(device, window, &chain, nullptr, nullptr, &base_swapchain)))
					{
						base_swapchain->QueryInterface(IID_PPV_ARGS(&swapchain));

						functions::release(base_swapchain);

						factory->MakeWindowAssociation(window, DXGI_MWA_NO_ALT_ENTER);

						if (swapchain)
						{
							swapchain->SetMaximumFrameLatency(1u);

							latency_waitable = swapchain->GetFrameLatencyWaitableObject();

							width = initial_width;
							height = initial_height;

							swapchain->GetBuffer(0u, IID_PPV_ARGS(&backbuffer));

							device->CreateRenderTargetView(backbuffer, nullptr, &backbuffer_rtv);

							return create_states(16u);
						}
					}

					logger.write("gpu: swapchain creation failed");

					return false;
				}

				return device && context && create_states(16u);
			}

			logger.write("gpu: device creation failed (0x%08X)", static_cast<std::uint32_t>(result));
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::destroy()
	{
		if (context)
		{
			context->ClearState();

			context->Flush();
		}

		destroy_states();

		functions::release(backbuffer_rtv);
		functions::release(backbuffer);

		if (latency_waitable)
		{
			CloseHandle(latency_waitable);

			latency_waitable = nullptr;
		}

		functions::release(swapchain);
		functions::release(context);
		functions::release(device);
		functions::release(adapter);
		functions::release(factory);
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::set_anisotropy(std::uint32_t anisotropy)
	{
		D3D11_SAMPLER_DESC sampler{};

		sampler.Filter = anisotropy > 1u ? D3D11_FILTER_ANISOTROPIC : D3D11_FILTER_MIN_MAG_MIP_LINEAR;
		sampler.AddressU = sampler.AddressV = sampler.AddressW = D3D11_TEXTURE_ADDRESS_WRAP;
		sampler.MaxAnisotropy = std::clamp(anisotropy, 1u, 16u);
		sampler.ComparisonFunc = D3D11_COMPARISON_NEVER;
		sampler.MaxLOD = D3D11_FLOAT32_MAX;

		if (ID3D11SamplerState* replacement{ nullptr }; SUCCEEDED(device->CreateSamplerState(&sampler, &replacement)))
		{
			functions::release(sampler_anisotropic_wrap);

			sampler_anisotropic_wrap = replacement;
		}
	}
	/*
	//=====================================================================================
	*/
	bool gpu_c::create_states(std::uint32_t anisotropy)
	{
		D3D11_SAMPLER_DESC sampler{};

		sampler.MaxLOD = D3D11_FLOAT32_MAX;
		sampler.MaxAnisotropy = 1u;
		sampler.ComparisonFunc = D3D11_COMPARISON_NEVER;

		sampler.Filter = D3D11_FILTER_MIN_MAG_MIP_POINT;
		sampler.AddressU = sampler.AddressV = sampler.AddressW = D3D11_TEXTURE_ADDRESS_CLAMP;
		device->CreateSamplerState(&sampler, &sampler_point_clamp);

		sampler.Filter = D3D11_FILTER_MIN_MAG_MIP_LINEAR;
		device->CreateSamplerState(&sampler, &sampler_linear_clamp);

		sampler.AddressU = sampler.AddressV = sampler.AddressW = D3D11_TEXTURE_ADDRESS_WRAP;
		device->CreateSamplerState(&sampler, &sampler_linear_wrap);

		sampler.Filter = anisotropy > 1u ? D3D11_FILTER_ANISOTROPIC : D3D11_FILTER_MIN_MAG_MIP_LINEAR;
		sampler.MaxAnisotropy = std::max(1u, anisotropy);
		device->CreateSamplerState(&sampler, &sampler_anisotropic_wrap);

		sampler.Filter = D3D11_FILTER_COMPARISON_MIN_MAG_LINEAR_MIP_POINT;
		sampler.MaxAnisotropy = 1u;
		sampler.AddressU = sampler.AddressV = sampler.AddressW = D3D11_TEXTURE_ADDRESS_BORDER;
		sampler.BorderColor[0] = sampler.BorderColor[1] = sampler.BorderColor[2] = sampler.BorderColor[3] = 1.0f;
		sampler.ComparisonFunc = D3D11_COMPARISON_LESS_EQUAL;
		device->CreateSamplerState(&sampler, &sampler_shadow);

		D3D11_BLEND_DESC blend{};

		blend.RenderTarget[0].RenderTargetWriteMask = D3D11_COLOR_WRITE_ENABLE_ALL;
		device->CreateBlendState(&blend, &blend_opaque);

		blend.RenderTarget[0].BlendEnable = TRUE;
		blend.RenderTarget[0].BlendOp = D3D11_BLEND_OP_ADD;
		blend.RenderTarget[0].BlendOpAlpha = D3D11_BLEND_OP_ADD;
		blend.RenderTarget[0].SrcBlend = D3D11_BLEND_SRC_ALPHA;
		blend.RenderTarget[0].DestBlend = D3D11_BLEND_INV_SRC_ALPHA;
		blend.RenderTarget[0].SrcBlendAlpha = D3D11_BLEND_ONE;
		blend.RenderTarget[0].DestBlendAlpha = D3D11_BLEND_INV_SRC_ALPHA;
		device->CreateBlendState(&blend, &blend_alpha);

		blend.RenderTarget[0].SrcBlend = D3D11_BLEND_ONE;
		blend.RenderTarget[0].DestBlend = D3D11_BLEND_ONE;
		blend.RenderTarget[0].SrcBlendAlpha = D3D11_BLEND_ONE;
		blend.RenderTarget[0].DestBlendAlpha = D3D11_BLEND_ONE;
		device->CreateBlendState(&blend, &blend_additive);

		blend.RenderTarget[0].SrcBlend = D3D11_BLEND_ONE;
		blend.RenderTarget[0].DestBlend = D3D11_BLEND_INV_SRC_ALPHA;
		blend.RenderTarget[0].SrcBlendAlpha = D3D11_BLEND_ZERO;
		blend.RenderTarget[0].DestBlendAlpha = D3D11_BLEND_ONE;
		device->CreateBlendState(&blend, &blend_premultiplied);

		blend.RenderTarget[0].SrcBlendAlpha = D3D11_BLEND_ONE;
		blend.RenderTarget[0].DestBlendAlpha = D3D11_BLEND_ONE;
		device->CreateBlendState(&blend, &blend_reactive);

		D3D11_RASTERIZER_DESC raster{};

		raster.FillMode = D3D11_FILL_SOLID;
		raster.CullMode = D3D11_CULL_BACK;
		raster.DepthClipEnable = TRUE;
		device->CreateRasterizerState(&raster, &raster_back);

		raster.CullMode = D3D11_CULL_NONE;
		device->CreateRasterizerState(&raster, &raster_none);

		raster.ScissorEnable = TRUE;
		device->CreateRasterizerState(&raster, &raster_scissor);

		raster.CullMode = D3D11_CULL_NONE;
		raster.DepthClipEnable = FALSE;
		raster.DepthBias = 64;
		raster.SlopeScaledDepthBias = 1.6f;
		raster.DepthBiasClamp = 0.01f;
		device->CreateRasterizerState(&raster, &raster_shadow);

		D3D11_DEPTH_STENCIL_DESC depth{};

		device->CreateDepthStencilState(&depth, &depth_none);

		depth.DepthEnable = TRUE;
		depth.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ZERO;
		depth.DepthFunc = D3D11_COMPARISON_GREATER_EQUAL;
		device->CreateDepthStencilState(&depth, &depth_read);

		depth.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL;
		depth.DepthFunc = D3D11_COMPARISON_GREATER;
		device->CreateDepthStencilState(&depth, &depth_write);

		depth.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ZERO;
		depth.DepthFunc = D3D11_COMPARISON_EQUAL;
		device->CreateDepthStencilState(&depth, &depth_equal);

		depth.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL;
		depth.DepthFunc = D3D11_COMPARISON_LESS;
		device->CreateDepthStencilState(&depth, &depth_shadow);

		return sampler_point_clamp && sampler_anisotropic_wrap && sampler_shadow && blend_alpha && raster_shadow && depth_shadow;
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::destroy_states()
	{
		functions::release(sampler_point_clamp);
		functions::release(sampler_linear_clamp);
		functions::release(sampler_linear_wrap);
		functions::release(sampler_anisotropic_wrap);
		functions::release(sampler_shadow);
		functions::release(blend_opaque);
		functions::release(blend_alpha);
		functions::release(blend_additive);
		functions::release(blend_premultiplied);
		functions::release(blend_reactive);
		functions::release(raster_back);
		functions::release(raster_none);
		functions::release(raster_scissor);
		functions::release(raster_shadow);
		functions::release(depth_none);
		functions::release(depth_read);
		functions::release(depth_write);
		functions::release(depth_equal);
		functions::release(depth_shadow);
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::resize(std::uint32_t new_width, std::uint32_t new_height)
	{
		if (swapchain && new_width && new_height && (new_width != width || new_height != height))
		{
			context->OMSetRenderTargets(0u, nullptr, nullptr);

			context->ClearState();

			context->Flush();

			functions::release(backbuffer_rtv);
			functions::release(backbuffer);

			if (SUCCEEDED(swapchain->ResizeBuffers(0u, new_width, new_height, DXGI_FORMAT_UNKNOWN, swapchain_flags)))
			{
				width = new_width;
				height = new_height;
			}

			swapchain->GetBuffer(0u, IID_PPV_ARGS(&backbuffer));

			device->CreateRenderTargetView(backbuffer, nullptr, &backbuffer_rtv);

			logger.write("gpu: resized to %ux%u", width, height);
		}
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::wait_for_frame()
	{
		if (latency_waitable)
		{
			WaitForSingleObjectEx(latency_waitable, 1000u, TRUE);
		}
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::present()
	{
		if (swapchain)
		{
			if (const auto result{ swapchain->Present(vsync ? 1u : 0u, (vsync || tearing == false) ? 0u : DXGI_PRESENT_ALLOW_TEARING) }; result == DXGI_ERROR_DEVICE_REMOVED || result == DXGI_ERROR_DEVICE_RESET)
			{
				logger.write("gpu: device lost (0x%08X, reason 0x%08X)", static_cast<std::uint32_t>(result), static_cast<std::uint32_t>(device->GetDeviceRemovedReason()));

				platform.quit_requested = true;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool gpu_c::capture(const char* path)
	{
		auto result{ false };

		D3D11_TEXTURE2D_DESC description{};

		backbuffer->GetDesc(&description);

		description.Usage = D3D11_USAGE_STAGING;
		description.BindFlags = 0u;
		description.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
		description.MiscFlags = 0u;

		ID3D11Texture2D* staging{ nullptr };

		if (SUCCEEDED(device->CreateTexture2D(&description, nullptr, &staging)))
		{
			context->CopyResource(staging, backbuffer);

			D3D11_MAPPED_SUBRESOURCE mapped{};

			if (SUCCEEDED(context->Map(staging, 0u, D3D11_MAP_READ, 0u, &mapped)))
			{
				std::vector<std::uint8_t> rows(static_cast<std::size_t>(description.Width) * description.Height * 4u);

				for (auto y{ 0u }; y < description.Height; y++)
				{
					std::memcpy(&rows[static_cast<std::size_t>(y) * description.Width * 4u], static_cast<const std::uint8_t*>(mapped.pData) + static_cast<std::size_t>(y) * mapped.RowPitch, description.Width * 4u);
				}

				context->Unmap(staging, 0u);

				for (auto index{ 3u }; index < rows.size(); index += 4u)
				{
					rows[index] = 255u;
				}

				IWICImagingFactory* imaging{ nullptr };

				if (SUCCEEDED(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&imaging))))
				{
					wchar_t wide_path[MAX_PATH]{};

					MultiByteToWideChar(CP_UTF8, 0u, path, -1, wide_path, MAX_PATH);

					IWICStream* stream{ nullptr };
					IWICBitmapEncoder* encoder{ nullptr };
					IWICBitmapFrameEncode* frame{ nullptr };

					if (SUCCEEDED(imaging->CreateStream(&stream)) && SUCCEEDED(stream->InitializeFromFilename(wide_path, GENERIC_WRITE)) && SUCCEEDED(imaging->CreateEncoder(GUID_ContainerFormatPng, nullptr, &encoder)) && SUCCEEDED(encoder->Initialize(stream, WICBitmapEncoderNoCache)) && SUCCEEDED(encoder->CreateNewFrame(&frame, nullptr)) && SUCCEEDED(frame->Initialize(nullptr)))
					{
						WICPixelFormatGUID format{ GUID_WICPixelFormat32bppRGBA };

						frame->SetSize(description.Width, description.Height);

						frame->SetPixelFormat(&format);

						if (IsEqualGUID(format, GUID_WICPixelFormat32bppBGRA))
						{
							for (auto index{ 0u }; index < rows.size(); index += 4u)
							{
								std::swap(rows[index], rows[index + 2u]);
							}
						}

						result = SUCCEEDED(frame->WritePixels(description.Height, description.Width * 4u, static_cast<UINT>(rows.size()), rows.data())) && SUCCEEDED(frame->Commit()) && SUCCEEDED(encoder->Commit());
					}

					functions::release(frame);
					functions::release(encoder);
					functions::release(stream);
					functions::release(imaging);
				}
			}

			functions::release(staging);
		}

		logger.write("gpu: capture %s -> %s", path, result ? "ok" : "failed");

		return result;
	}
	/*
	//=====================================================================================
	*/
	structures::shader_blob_s gpu_c::shader_bytes(const char* name)
	{
		if (auto resource{ FindResourceA(nullptr, name, MAKEINTRESOURCEA(10)) }; resource)
		{
			if (auto handle{ LoadResource(nullptr, resource) }; handle)
			{
				return { LockResource(handle), static_cast<std::size_t>(SizeofResource(nullptr, resource)) };
			}
		}

		logger.write("gpu: missing shader %s", name);

		return { nullptr, 0u };
	}
	/*
	//=====================================================================================
	*/
	ID3D11VertexShader* gpu_c::create_vertex_shader(const char* name, const D3D11_INPUT_ELEMENT_DESC* layout, std::uint32_t layout_count, ID3D11InputLayout** out_layout)
	{
		ID3D11VertexShader* shader{ nullptr };

		if (const auto blob{ device ? shader_bytes(name) : structures::shader_blob_s{ nullptr, 0u } }; blob.data)
		{
			device->CreateVertexShader(blob.data, blob.size, nullptr, &shader);

			if (layout && out_layout)
			{
				device->CreateInputLayout(layout, layout_count, blob.data, blob.size, out_layout);
			}
		}

		return shader;
	}
	/*
	//=====================================================================================
	*/
	ID3D11PixelShader* gpu_c::create_pixel_shader(const char* name)
	{
		ID3D11PixelShader* shader{ nullptr };

		if (const auto blob{ device ? shader_bytes(name) : structures::shader_blob_s{ nullptr, 0u } }; blob.data)
		{
			device->CreatePixelShader(blob.data, blob.size, nullptr, &shader);
		}

		return shader;
	}
	/*
	//=====================================================================================
	*/
	ID3D11ComputeShader* gpu_c::create_compute_shader(const char* name)
	{
		ID3D11ComputeShader* shader{ nullptr };

		if (const auto blob{ device ? shader_bytes(name) : structures::shader_blob_s{ nullptr, 0u } }; blob.data)
		{
			device->CreateComputeShader(blob.data, blob.size, nullptr, &shader);
		}

		return shader;
	}
	/*
	//=====================================================================================
	*/
	ID3D11Buffer* gpu_c::create_buffer(std::uint32_t size, D3D11_USAGE usage, std::uint32_t bind_flags, std::uint32_t cpu_flags, const void* data, std::uint32_t misc_flags, std::uint32_t stride)
	{
		D3D11_BUFFER_DESC description{};

		description.ByteWidth = size;
		description.Usage = usage;
		description.BindFlags = bind_flags;
		description.CPUAccessFlags = cpu_flags;
		description.MiscFlags = misc_flags;
		description.StructureByteStride = stride;

		D3D11_SUBRESOURCE_DATA initial{};

		initial.pSysMem = data;

		ID3D11Buffer* buffer{ nullptr };

		if (device)
		{
			device->CreateBuffer(&description, data ? &initial : nullptr, &buffer);
		}

		return buffer;
	}
	/*
	//=====================================================================================
	*/
	ID3D11Buffer* gpu_c::create_constant_buffer(std::uint32_t size)
	{
		return create_buffer((size + 15u) & ~15u, D3D11_USAGE_DYNAMIC, D3D11_BIND_CONSTANT_BUFFER, D3D11_CPU_ACCESS_WRITE, nullptr, 0u, 0u);
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::update_buffer(ID3D11Buffer* buffer, const void* data, std::uint32_t size)
	{
		D3D11_MAPPED_SUBRESOURCE mapped{};

		if (buffer && context && SUCCEEDED(context->Map(buffer, 0u, D3D11_MAP_WRITE_DISCARD, 0u, &mapped)))
		{
			std::memcpy(mapped.pData, data, size);

			context->Unmap(buffer, 0u);
		}
	}
	/*
	//=====================================================================================
	*/
	bool gpu_c::create_target(structures::target_s& target, std::uint32_t target_width, std::uint32_t target_height, DXGI_FORMAT format, std::uint32_t flags)
	{
		destroy_target(target);

		D3D11_TEXTURE2D_DESC description{};

		description.Width = std::max(1u, target_width);
		description.Height = std::max(1u, target_height);
		description.MipLevels = (flags & structures::target_mips) ? 0u : 1u;
		description.ArraySize = 1u;
		description.Format = format;
		description.SampleDesc.Count = 1u;
		description.Usage = D3D11_USAGE_DEFAULT;
		description.BindFlags = ((flags & structures::target_rtv) ? D3D11_BIND_RENDER_TARGET : 0u) | ((flags & structures::target_srv) ? D3D11_BIND_SHADER_RESOURCE : 0u) | ((flags & structures::target_uav) ? D3D11_BIND_UNORDERED_ACCESS : 0u);
		description.MiscFlags = (flags & structures::target_mips) ? D3D11_RESOURCE_MISC_GENERATE_MIPS : 0u;

		if (SUCCEEDED(device->CreateTexture2D(&description, nullptr, &target.texture)))
		{
			target.width = description.Width;
			target.height = description.Height;
			target.format = format;

			if (flags & structures::target_rtv)
			{
				device->CreateRenderTargetView(target.texture, nullptr, &target.rtv);
			}

			if (flags & structures::target_srv)
			{
				device->CreateShaderResourceView(target.texture, nullptr, &target.srv);
			}

			if (flags & structures::target_uav)
			{
				device->CreateUnorderedAccessView(target.texture, nullptr, &target.uav);
			}

			return true;
		}

		logger.write("gpu: target creation failed %ux%u format %u", target_width, target_height, static_cast<std::uint32_t>(format));

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool gpu_c::create_depth(structures::depth_target_s& target, std::uint32_t target_width, std::uint32_t target_height)
	{
		destroy_depth(target);

		D3D11_TEXTURE2D_DESC description{};

		description.Width = std::max(1u, target_width);
		description.Height = std::max(1u, target_height);
		description.MipLevels = 1u;
		description.ArraySize = 1u;
		description.Format = DXGI_FORMAT_R32_TYPELESS;
		description.SampleDesc.Count = 1u;
		description.Usage = D3D11_USAGE_DEFAULT;
		description.BindFlags = D3D11_BIND_DEPTH_STENCIL | D3D11_BIND_SHADER_RESOURCE;

		if (SUCCEEDED(device->CreateTexture2D(&description, nullptr, &target.texture)))
		{
			D3D11_DEPTH_STENCIL_VIEW_DESC view{};

			view.Format = DXGI_FORMAT_D32_FLOAT;
			view.ViewDimension = D3D11_DSV_DIMENSION_TEXTURE2D;

			device->CreateDepthStencilView(target.texture, &view, &target.dsv);

			view.Flags = D3D11_DSV_READ_ONLY_DEPTH;

			device->CreateDepthStencilView(target.texture, &view, &target.dsv_read_only);

			D3D11_SHADER_RESOURCE_VIEW_DESC resource{};

			resource.Format = DXGI_FORMAT_R32_FLOAT;
			resource.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2D;
			resource.Texture2D.MipLevels = 1u;

			device->CreateShaderResourceView(target.texture, &resource, &target.srv);

			target.width = description.Width;
			target.height = description.Height;

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::destroy_target(structures::target_s& target)
	{
		functions::release(target.uav);
		functions::release(target.srv);
		functions::release(target.rtv);
		functions::release(target.texture);
	}
	/*
	//=====================================================================================
	*/
	void gpu_c::destroy_depth(structures::depth_target_s& target)
	{
		functions::release(target.srv);
		functions::release(target.dsv_read_only);
		functions::release(target.dsv);
		functions::release(target.texture);
	}
}

//=====================================================================================
