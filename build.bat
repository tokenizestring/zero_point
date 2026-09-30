@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "root=%~dp0"
set "root_forward=%root:\=/%"

set "configuration=release"
if /i "%~1"=="debug" set "configuration=debug"

set "vswhere=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%vswhere%" (
	echo error: vswhere.exe not found
	exit /b 1
)

for /f "usebackq tokens=*" %%i in (`"%vswhere%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "vs_path=%%i"

if not defined vs_path (
	echo error: no visual studio c++ toolset found
	exit /b 1
)

call "%vs_path%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>nul

if not exist build\bin mkdir build\bin
if not exist build\obj\%configuration% mkdir build\obj\%configuration%
if not exist build\obj\shaders mkdir build\obj\shaders
if not exist build\obj\tools mkdir build\obj\tools

if /i "%~1"=="code" goto :compile

if exist tools\baker\baker.cpp (
	cl /nologo /std:c++20 /O2 /Oi /MT /EHsc /MP /W3 /DWIN32_LEAN_AND_MEAN /DNOMINMAX /D_CRT_SECURE_NO_WARNINGS /I. /Fo:build\obj\tools\ /Fe:build\obj\tools\baker.exe tools\baker\*.cpp core\engine\engine.cpp core\mathematics\mathematics.cpp /link /INCREMENTAL:NO windowscodecs.lib ole32.lib sapi.lib user32.lib gdi32.lib >build\obj\tools\baker.log
	if errorlevel 1 (
		type build\obj\tools\baker.log
		echo error: baker build failed
		exit /b 1
	)
	if /i "%~1"=="terrain" (
		build\obj\tools\baker.exe --terrain "%root%build\obj"
		exit /b !errorlevel!
	)
	build\obj\tools\baker.exe "%root%assets" "%root%build\bin\zero_point.pak" "%root%build\obj\zero_point.ico"
	if !errorlevel! neq 0 (
		echo error: asset bake failed
		exit /b 1
	)
)

:compile
set "shader_fail="
set "rc_file=build\obj\zero_point.rc"
type nul > "%rc_file%"
if exist build\obj\zero_point.ico >> "%rc_file%" echo 1 ICON "%root_forward%build/obj/zero_point.ico"

for /f "usebackq tokens=1-4" %%a in ("shaders\shaders.txt") do call :shader %%a %%b %%c %%d
if defined shader_fail exit /b 1

rc /nologo /fo build\obj\zero_point.res "%rc_file%"
if errorlevel 1 (
	echo error: resource compile failed
	exit /b 1
)

set "objects=build\obj\%configuration%"

> build\obj\sources.rsp (
	if exist core for /r core %%f in (*.cpp) do echo "%%f"
	if exist render for /r render %%f in (*.cpp) do echo "%%f"
	if exist audio for /r audio %%f in (*.cpp) do echo "%%f"
	if exist game for /r game %%f in (*.cpp) do echo "%%f"
	if exist net for /r net %%f in (*.cpp) do echo "%%f"
	if exist ui for /r ui %%f in (*.cpp) do echo "%%f"
	echo "%root%main.cpp"
	echo "%root%server_main.cpp"
)

> build\obj\shared.rsp (
	if exist core for /r core %%f in (*.cpp) do echo "%objects%\%%~nf.obj"
	if exist render for /r render %%f in (*.cpp) do echo "%objects%\%%~nf.obj"
	if exist audio for /r audio %%f in (*.cpp) do echo "%objects%\%%~nf.obj"
	if exist game for /r game %%f in (*.cpp) do echo "%objects%\%%~nf.obj"
	if exist net for /r net %%f in (*.cpp) do echo "%objects%\%%~nf.obj"
	if exist ui for /r ui %%f in (*.cpp) do echo "%objects%\%%~nf.obj"
)

set "common=/nologo /std:c++20 /W4 /wd4100 /wd4201 /wd4324 /wd4127 /EHsc /MP /Zi /DWIN32_LEAN_AND_MEAN /DNOMINMAX /D_CRT_SECURE_NO_WARNINGS /I. /Fo:%objects%\ /Fd:%objects%\vc.pdb"
set "libraries=d3d11.lib dxgi.lib dxguid.lib xaudio2.lib xinput.lib ws2_32.lib winmm.lib windowscodecs.lib ole32.lib user32.lib gdi32.lib shell32.lib advapi32.lib"

if "%configuration%"=="debug" (
	cl %common% /c /Od /MTd /RTC1 /DZP_DEBUG @build\obj\sources.rsp
) else (
	cl %common% /c /O2 /Oi /Ot /GL /Gy /GS- /fp:fast /MT /DNDEBUG @build\obj\sources.rsp
)

if errorlevel 1 (
	echo error: build failed
	exit /b 1
)

if "%configuration%"=="debug" (
	link /nologo /DEBUG /INCREMENTAL:NO /PDB:%objects%\zero_point.pdb /IMPLIB:%objects%\zero_point.lib /SUBSYSTEM:WINDOWS /OUT:build\bin\zero_point_debug.exe @build\obj\shared.rsp %objects%\main.obj build\obj\zero_point.res %libraries%
) else (
	link /nologo /LTCG /OPT:REF /OPT:ICF /DEBUG /INCREMENTAL:NO /PDB:%objects%\zero_point.pdb /IMPLIB:%objects%\zero_point.lib /SUBSYSTEM:WINDOWS /OUT:build\bin\zero_point.exe @build\obj\shared.rsp %objects%\main.obj build\obj\zero_point.res %libraries%
)

if errorlevel 1 (
	echo error: client link failed
	exit /b 1
)

if "%configuration%"=="debug" (
	link /nologo /DEBUG /INCREMENTAL:NO /PDB:%objects%\zero_point_server.pdb /IMPLIB:%objects%\zero_point_server.lib /SUBSYSTEM:CONSOLE /OUT:build\bin\zero_point_server_debug.exe @build\obj\shared.rsp %objects%\server_main.obj build\obj\zero_point.res %libraries%
) else (
	link /nologo /LTCG /OPT:REF /OPT:ICF /DEBUG /INCREMENTAL:NO /PDB:%objects%\zero_point_server.pdb /IMPLIB:%objects%\zero_point_server.lib /SUBSYSTEM:CONSOLE /OUT:build\bin\zero_point_server.exe @build\obj\shared.rsp %objects%\server_main.obj build\obj\zero_point.res %libraries%
)

if errorlevel 1 (
	echo error: server link failed
	exit /b 1
)

echo build ok: %configuration%
exit /b 0

:shader
fxc /nologo /T %3 /E %2 /O3 /Zpr /Fo build\obj\shaders\%4.cso shaders\%1.hlsl >build\obj\shaders\%4.log
if errorlevel 1 (
	type build\obj\shaders\%4.log
	echo error: shader compile failed: %1.hlsl %2
	set "shader_fail=1"
)
>> "%rc_file%" echo %4 RCDATA "%root_forward%build/obj/shaders/%4.cso"
exit /b 0
