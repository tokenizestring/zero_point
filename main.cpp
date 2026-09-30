
//=====================================================================================

#include "stdafx.hpp"

//=====================================================================================

extern "C"
{
	__declspec(dllexport) DWORD NvOptimusEnablement = 0x00000001u;
	__declspec(dllexport) std::int32_t AmdPowerXpressRequestHighPerformance = 1;
}

//=====================================================================================

std::int32_t WINAPI WinMain(HINSTANCE instance, HINSTANCE previous, LPSTR command_line, std::int32_t show)
{
	return zp::application.run(instance);
}

//=====================================================================================
