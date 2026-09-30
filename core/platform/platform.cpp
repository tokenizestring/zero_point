
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	platform_c platform;

	bool platform_c::create(HINSTANCE module_instance, bool create_window)
	{
		instance = module_instance;

		headless = !create_window;

		std::memcpy(bindings, default_user_settings.bindings, sizeof(bindings));

		QueryPerformanceFrequency(&frequency);
		QueryPerformanceCounter(&start_counter);

		timeBeginPeriod(1u);

		frame_timer = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS);

		if (create_window)
		{
			SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);

			WNDCLASSEXW window_class{};

			window_class.cbSize = sizeof(window_class);
			window_class.style = CS_HREDRAW | CS_VREDRAW;
			window_class.lpfnWndProc = window_procedure;
			window_class.hInstance = instance;
			window_class.hCursor = LoadCursorA(nullptr, IDC_ARROW);
			window_class.hIcon = LoadIconW(instance, MAKEINTRESOURCEW(1));
			window_class.hIconSm = window_class.hIcon;
			window_class.lpszClassName = window_class_name;

			if (RegisterClassExW(&window_class))
			{
				const auto screen_width{ GetSystemMetrics(SM_CXSCREEN) };
				const auto screen_height{ GetSystemMetrics(SM_CYSCREEN) };

				windowed_rect = { (screen_width - default_window_width) / 2, (screen_height - default_window_height) / 2, (screen_width + default_window_width) / 2, (screen_height + default_window_height) / 2 };

				AdjustWindowRectEx(&windowed_rect, WS_OVERLAPPEDWINDOW, FALSE, 0u);

				window = CreateWindowExW(0u, window_class_name, game_title_wide, WS_OVERLAPPEDWINDOW, windowed_rect.left, windowed_rect.top, windowed_rect.right - windowed_rect.left, windowed_rect.bottom - windowed_rect.top, nullptr, nullptr, instance, nullptr);

				if (window)
				{
					RAWINPUTDEVICE device{};

					device.usUsagePage = 0x01u;
					device.usUsage = 0x02u;
					device.dwFlags = 0u;
					device.hwndTarget = window;

					RegisterRawInputDevices(&device, 1u, sizeof(device));

					ShowWindow(window, SW_SHOW);

					UpdateWindow(window);

					RECT inner{};

					GetClientRect(window, &inner);

					client_width = inner.right - inner.left;
					client_height = inner.bottom - inner.top;

					logger.write("platform: window created %dx%d", client_width, client_height);

					return true;
				}
			}

			logger.write("platform: window creation failed (%lu)", GetLastError());

			return false;
		}

		return true;
	}
	/*
	//=====================================================================================
	*/
	void platform_c::destroy()
	{
		set_mouse_captured(false);

		if (window)
		{
			DestroyWindow(window);

			window = nullptr;
		}

		UnregisterClassW(window_class_name, instance);

		if (frame_timer)
		{
			CloseHandle(frame_timer);

			frame_timer = nullptr;
		}

		timeEndPeriod(1u);
	}
	/*
	//=====================================================================================
	*/
	void platform_c::pump()
	{
		std::memset(input.pressed, 0, sizeof(input.pressed));
		std::memset(input.released, 0, sizeof(input.released));
		std::memset(input.repeated, 0, sizeof(input.repeated));

		input.mouse_delta = { 0.0f, 0.0f };
		input.wheel = 0.0f;
		input.text_length = 0u;
		input.text[0] = 0;

		resized = false;

		MSG message{};

		while (PeekMessageW(&message, nullptr, 0u, 0u, PM_REMOVE))
		{
			if (message.message == WM_QUIT)
			{
				quit_requested = true;
			}

			TranslateMessage(&message);

			DispatchMessageW(&message);
		}

		if (window)
		{
			POINT cursor{};

			GetCursorPos(&cursor);

			ScreenToClient(window, &cursor);

			input.mouse_position = { static_cast<std::float_t>(cursor.x), static_cast<std::float_t>(cursor.y) };
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::set_display_mode(structures::display_mode_e mode)
	{
		if (window)
		{
			if (display_mode == structures::display_mode_windowed && mode != structures::display_mode_windowed)
			{
				GetWindowRect(window, &windowed_rect);
			}

			display_mode = mode;

			if (mode == structures::display_mode_windowed)
			{
				SetWindowLongPtrW(window, GWL_STYLE, WS_OVERLAPPEDWINDOW | WS_VISIBLE);

				SetWindowPos(window, HWND_NOTOPMOST, windowed_rect.left, windowed_rect.top, windowed_rect.right - windowed_rect.left, windowed_rect.bottom - windowed_rect.top, SWP_FRAMECHANGED | SWP_NOACTIVATE);
			}

			else
			{
				MONITORINFO monitor{};

				monitor.cbSize = sizeof(monitor);

				GetMonitorInfoW(MonitorFromWindow(window, MONITOR_DEFAULTTONEAREST), &monitor);

				SetWindowLongPtrW(window, GWL_STYLE, WS_POPUP | WS_VISIBLE);

				SetWindowPos(window, HWND_TOP, monitor.rcMonitor.left, monitor.rcMonitor.top, monitor.rcMonitor.right - monitor.rcMonitor.left, monitor.rcMonitor.bottom - monitor.rcMonitor.top, SWP_FRAMECHANGED);
			}

			apply_cursor_clip();
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::set_mouse_captured(bool captured)
	{
		if (captured != mouse_captured)
		{
			mouse_captured = captured;

			if (captured)
			{
				while (ShowCursor(FALSE) >= 0)
				{
				}
			}

			else
			{
				while (ShowCursor(TRUE) < 0)
				{
				}
			}

			apply_cursor_clip();
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::apply_cursor_clip()
	{
		if (window && mouse_captured && focused)
		{
			RECT inner{};

			GetClientRect(window, &inner);

			POINT center{ (inner.left + inner.right) / 2, (inner.top + inner.bottom) / 2 };

			ClientToScreen(window, &center);

			RECT clip{ center.x, center.y, center.x + 1, center.y + 1 };

			ClipCursor(&clip);
		}

		else
		{
			ClipCursor(nullptr);
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::set_title(const char* text)
	{
		if (window)
		{
			SetWindowTextA(window, text);
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::release_all_keys()
	{
		for (auto key{ 0u }; key < key_count; key++)
		{
			if (input.down[key])
			{
				input.down[key] = false;

				input.released[key] = true;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	bool platform_c::held(std::uint32_t action)
	{
		return action < structures::bind_count && input.down[bindings[action]];
	}
	/*
	//=====================================================================================
	*/
	bool platform_c::tapped(std::uint32_t action)
	{
		return action < structures::bind_count && input.pressed[bindings[action]];
	}
	/*
	//=====================================================================================
	*/
	void platform_c::consume(std::uint32_t action)
	{
		if (action < structures::bind_count)
		{
			input.pressed[bindings[action]] = false;
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::simulate(std::uint32_t action, bool down)
	{
		if (action < structures::bind_count)
		{
			input.pressed[bindings[action]] = down && input.down[bindings[action]] == false;
			input.down[bindings[action]] = down;
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::sleep_until(std::double_t target_seconds)
	{
		if (const auto remaining{ target_seconds - time() }; remaining > 0.0015 && frame_timer)
		{
			LARGE_INTEGER due{};

			due.QuadPart = -static_cast<LONGLONG>((remaining - 0.001) * 10000000.0);

			if (SetWaitableTimerEx(frame_timer, &due, 0, nullptr, nullptr, nullptr, 0u))
			{
				WaitForSingleObject(frame_timer, INFINITE);
			}
		}

		while (time() < target_seconds)
		{
			YieldProcessor();
		}
	}
	/*
	//=====================================================================================
	*/
	std::double_t platform_c::time()
	{
		LARGE_INTEGER counter{};

		QueryPerformanceCounter(&counter);

		return static_cast<std::double_t>(counter.QuadPart - start_counter.QuadPart) / static_cast<std::double_t>(frequency.QuadPart);
	}
	/*
	//=====================================================================================
	*/
	bool platform_c::copy_to_clipboard(const char* text)
	{
		if (window && OpenClipboard(window))
		{
			EmptyClipboard();

			if (auto memory{ GlobalAlloc(GMEM_MOVEABLE, std::strlen(text) + 1u) }; memory)
			{
				std::memcpy(GlobalLock(memory), text, std::strlen(text) + 1u);

				GlobalUnlock(memory);

				SetClipboardData(CF_TEXT, memory);
			}

			CloseClipboard();

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool platform_c::paste_from_clipboard(char* out, std::uint32_t capacity)
	{
		auto result{ false };

		if (window && capacity && OpenClipboard(window))
		{
			if (auto memory{ GetClipboardData(CF_TEXT) }; memory)
			{
				if (auto text{ static_cast<const char*>(GlobalLock(memory)) }; text)
				{
					std::snprintf(out, capacity, "%s", text);

					GlobalUnlock(memory);

					result = true;
				}
			}

			CloseClipboard();
		}

		return result;
	}
	/*
	//=====================================================================================
	*/
	void platform_c::on_key(std::uint32_t key, bool down, bool repeat)
	{
		if (key < key_count)
		{
			if (down)
			{
				input.pressed[key] = input.pressed[key] || (!input.down[key] && !repeat);

				input.repeated[key] = true;

				input.down[key] = true;
			}

			else if (input.down[key])
			{
				input.down[key] = false;

				input.released[key] = true;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void platform_c::on_raw_input(LPARAM handle)
	{
		UINT size{ 0u };

		GetRawInputData(reinterpret_cast<HRAWINPUT>(handle), RID_INPUT, nullptr, &size, sizeof(RAWINPUTHEADER));

		if (size)
		{
			raw_buffer.resize(size);

			if (GetRawInputData(reinterpret_cast<HRAWINPUT>(handle), RID_INPUT, raw_buffer.data(), &size, sizeof(RAWINPUTHEADER)) == size)
			{
				if (const auto raw{ reinterpret_cast<RAWINPUT*>(raw_buffer.data()) }; raw->header.dwType == RIM_TYPEMOUSE && (raw->data.mouse.usFlags & MOUSE_MOVE_ABSOLUTE) == 0u)
				{
					input.mouse_delta.x += static_cast<std::float_t>(raw->data.mouse.lLastX);
					input.mouse_delta.y += static_cast<std::float_t>(raw->data.mouse.lLastY);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	LRESULT CALLBACK platform_c::window_procedure(HWND handle, UINT message, WPARAM wparam, LPARAM lparam)
	{
		switch (message)
		{
			case WM_CLOSE:
			{
				platform.quit_requested = true;

				return 0;
			}

			case WM_SIZE:
			{
				platform.client_width = LOWORD(lparam);
				platform.client_height = HIWORD(lparam);
				platform.minimized = (wparam == SIZE_MINIMIZED);
				platform.resized = true;

				platform.apply_cursor_clip();

				break;
			}

			case WM_ACTIVATEAPP:
			{
				platform.focused = (wparam != FALSE);

				platform.release_all_keys();

				platform.apply_cursor_clip();

				break;
			}

			case WM_GETMINMAXINFO:
			{
				reinterpret_cast<MINMAXINFO*>(lparam)->ptMinTrackSize = { minimum_window_width, minimum_window_height };

				return 0;
			}

			case WM_SETCURSOR:
			{
				if (LOWORD(lparam) == HTCLIENT && platform.mouse_captured)
				{
					SetCursor(nullptr);

					return TRUE;
				}

				break;
			}

			case WM_SYSCOMMAND:
			{
				if ((wparam & 0xFFF0u) == SC_KEYMENU)
				{
					return 0;
				}

				break;
			}

			case WM_ERASEBKGND:
			{
				return 1;
			}

			case WM_INPUT:
			{
				platform.on_raw_input(lparam);

				break;
			}

			case WM_KEYDOWN:
			case WM_SYSKEYDOWN:
			{
				platform.on_key(static_cast<std::uint32_t>(wparam), true, (lparam & (1 << 30)) != 0);

				if (wparam == VK_F4 && message == WM_SYSKEYDOWN)
				{
					platform.quit_requested = true;
				}

				return 0;
			}

			case WM_KEYUP:
			case WM_SYSKEYUP:
			{
				platform.on_key(static_cast<std::uint32_t>(wparam), false, false);

				return 0;
			}

			case WM_CHAR:
			{
				if (wparam >= 32u && wparam < 127u && platform.input.text_length + 1u < text_input_capacity)
				{
					platform.input.text[platform.input.text_length++] = static_cast<char>(wparam);

					platform.input.text[platform.input.text_length] = 0;
				}

				return 0;
			}

			case WM_LBUTTONDOWN:
			case WM_RBUTTONDOWN:
			case WM_MBUTTONDOWN:
			case WM_XBUTTONDOWN:
			{
				platform.on_key(message == WM_LBUTTONDOWN ? VK_LBUTTON : (message == WM_RBUTTONDOWN ? VK_RBUTTON : (message == WM_MBUTTONDOWN ? VK_MBUTTON : (GET_XBUTTON_WPARAM(wparam) == XBUTTON1 ? VK_XBUTTON1 : VK_XBUTTON2))), true, false);

				SetCapture(handle);

				return message == WM_XBUTTONDOWN ? TRUE : 0;
			}

			case WM_LBUTTONUP:
			case WM_RBUTTONUP:
			case WM_MBUTTONUP:
			case WM_XBUTTONUP:
			{
				platform.on_key(message == WM_LBUTTONUP ? VK_LBUTTON : (message == WM_RBUTTONUP ? VK_RBUTTON : (message == WM_MBUTTONUP ? VK_MBUTTON : (GET_XBUTTON_WPARAM(wparam) == XBUTTON1 ? VK_XBUTTON1 : VK_XBUTTON2))), false, false);

				ReleaseCapture();

				return message == WM_XBUTTONUP ? TRUE : 0;
			}

			case WM_MOUSEWHEEL:
			{
				platform.input.wheel += static_cast<std::float_t>(GET_WHEEL_DELTA_WPARAM(wparam)) / static_cast<std::float_t>(WHEEL_DELTA);

				return 0;
			}

			default:
			{
				break;
			}
		}

		return DefWindowProcW(handle, message, wparam, lparam);
	}
}

//=====================================================================================
