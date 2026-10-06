
//=====================================================================================

#pragma once

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <windowsx.h>
#include <shellapi.h>
#include <shlobj.h>
#include <mmsystem.h>
#include <wincodec.h>
#include <d3d11_1.h>
#include <dxgi1_6.h>
#include <xaudio2.h>
#include <xaudio2fx.h>
#include <x3daudio.h>
#include <xinput.h>

#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdarg>
#include <cmath>
#include <cfloat>
#include <array>
#include <vector>
#include <string>
#include <algorithm>
#include <atomic>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <memory>
#include <chrono>
#include <unordered_map>
#include <span>
#include <random>

#include "utils/logger/logger.hpp"
#include "utils/jobs/jobs.hpp"

#include "core/engine/engine.hpp"
#include "core/mathematics/mathematics.hpp"
#include "core/platform/platform.hpp"

#include "utils/stream/stream.hpp"
#include "utils/udp/udp.hpp"

#include "render/gpu/gpu.hpp"
#include "render/pak/pak.hpp"
#include "render/font/font.hpp"
#include "render/canvas/canvas.hpp"
#include "render/materials/materials.hpp"
#include "render/models/models.hpp"
#include "render/characters/characters.hpp"
#include "render/terrain/terrain.hpp"
#include "render/foliage/foliage.hpp"
#include "render/grass/grass.hpp"
#include "render/water/water.hpp"
#include "render/particles/particles.hpp"
#include "render/decals/decals.hpp"
#include "render/weather/weather.hpp"
#include "render/builder/builder.hpp"
#include "render/sky/sky.hpp"
#include "render/atmosphere/atmosphere.hpp"
#include "render/shadows/shadows.hpp"
#include "render/tracer/tracer.hpp"
#include "render/probes/probes.hpp"
#include "render/post/post.hpp"
#include "render/ssao/ssao.hpp"
#include "render/profiler/profiler.hpp"
#include "render/renderer/renderer.hpp"

#include "game/world/world.hpp"
#include "game/maps/maps.hpp"
#include "game/movement/movement.hpp"
#include "game/player/player.hpp"
#include "game/actors/actors.hpp"
#include "game/fauna/fauna.hpp"
#include "game/wildlife/wildlife.hpp"
#include "game/survival/survival.hpp"
#include "game/harvest/harvest.hpp"
#include "game/combat/combat.hpp"
#include "game/building/building.hpp"
#include "game/story/story.hpp"
#include "game/save/save.hpp"
#include "game/farming/farming.hpp"
#include "game/loot/loot.hpp"
#include "game/projectiles/projectiles.hpp"
#include "game/weapons/weapons.hpp"
#include "game/viewmodel/viewmodel.hpp"
#include "game/train/train.hpp"
#include "game/gates/gates.hpp"
#include "game/marks/marks.hpp"

#include "net/transport/transport.hpp"
#include "net/server/server.hpp"
#include "net/client/client.hpp"
#include "net/persist/persist.hpp"
#include "net/admin/admin.hpp"
#include "net/dedicated/dedicated.hpp"
#include "game/autotest/autotest.hpp"

#include "ui/chart/chart.hpp"
#include "ui/kit/kit.hpp"
#include "ui/hud/hud.hpp"
#include "ui/menu/menu.hpp"

#include "audio/mixer/mixer.hpp"

#include "core/application/application.hpp"

//=====================================================================================
